from __future__ import annotations

from collections.abc import Callable

from pydantic import BaseModel

from rclp_core.audit import AuditLog
from rclp_core.conformance import validate_lease_for_command
from rclp_core.leases import lease_matches_context, verify_lease_signature
from rclp_core.models import (
    AuditEventType,
    CapabilityLease,
    FallbackAction,
    FallbackDeclaration,
    LeaseRevocation,
    RobotStateAssertion,
)


class Command(BaseModel):
    correlation_id: str | None = None
    command_id: str
    agent_id: str
    edge_agent_id: str
    robot_id: str
    mission_id: str
    capability: str
    payload: dict


class GateResult(BaseModel):
    allowed: bool
    reason_code: str
    audit_id: str | None = None
    fallback_action: FallbackAction | None = None
    fallback_declaration: FallbackDeclaration | None = None


class RevokedLease(BaseModel):
    lease_id: str
    reason_code: str = "LEASE_REVOKED"
    fallback_action: FallbackAction | None = None
    revocation_id: str | None = None
    correlation_id: str | None = None


class CommandGate:
    """ROS-agnostic command gate.

    Future ROS 2 adapters should call this before forwarding commands to topics/services/actions.
    """

    def __init__(
        self,
        issuer_public_key_b64: str,
        *,
        trusted_issuer_ids: set[str],
        trusted_revoker_ids: set[str],
        fallback_sink: Callable[[FallbackDeclaration], None] | None = None,
        audit_log: AuditLog | None = None,
        max_lease_age_seconds: int = 600,
        max_lease_ttl_seconds: int = 600,
    ) -> None:
        if not trusted_issuer_ids:
            raise ValueError("trusted_issuer_ids must name at least one lease issuer")
        if not trusted_revoker_ids:
            raise ValueError("trusted_revoker_ids must name at least one revocation actor")
        self.issuer_public_key_b64 = issuer_public_key_b64
        self.trusted_issuer_ids = set(trusted_issuer_ids)
        self.trusted_revoker_ids = set(trusted_revoker_ids)
        self.max_lease_age_seconds = max_lease_age_seconds
        self.max_lease_ttl_seconds = max_lease_ttl_seconds
        self.revocations: dict[str, RevokedLease] = {}
        self.fallback_events: list[FallbackDeclaration] = []
        self._fallback_sink = fallback_sink
        self.audit_log = audit_log or AuditLog()

    @property
    def revoked_lease_ids(self) -> set[str]:
        return set(self.revocations)

    def revoke(
        self,
        revocation: LeaseRevocation | str,
        lease: CapabilityLease | None = None,
    ) -> FallbackDeclaration | None:
        if not isinstance(revocation, LeaseRevocation):
            if lease is not None:
                self.audit_log.record(
                    event_type=AuditEventType.REVOCATION_REJECTED,
                    actor_id="local_command_gate",
                    robot_id=lease.robot_id,
                    mission_id=lease.mission_id,
                    correlation_id=lease.lease_id,
                    summary="raw lease-id revocation rejected because protocol context is required",
                    payload={
                        "lease_id": revocation,
                        "reason_code": "REVOCATION_CONTEXT_REQUIRED",
                    },
                    related_message_ids=[revocation],
                )
            raise ValueError("revocation requires a LeaseRevocation message")

        record = RevokedLease(
            lease_id=revocation.lease_id,
            reason_code=revocation.reason_code,
            fallback_action=revocation.fallback_action,
            revocation_id=revocation.message_id,
            correlation_id=revocation.correlation_id,
        )
        revoked_by = revocation.revoked_by
        if lease is None:
            self.audit_log.record(
                event_type=AuditEventType.DIAGNOSTIC,
                actor_id=revoked_by,
                correlation_id=record.correlation_id or record.lease_id,
                summary="revocation rejected because lease context is required",
                payload={
                    "lease_id": record.lease_id,
                    "reason_code": "REVOCATION_CONTEXT_REQUIRED",
                    "revocation_id": record.revocation_id,
                },
                authority_relevant=False,
                related_message_ids=[record.revocation_id] if record.revocation_id else [],
            )
            raise ValueError("revocation requires lease context")

        if revoked_by not in self.trusted_revoker_ids:
            self.audit_log.record(
                event_type=AuditEventType.REVOCATION_REJECTED,
                actor_id=revoked_by,
                robot_id=lease.robot_id,
                mission_id=lease.mission_id,
                correlation_id=record.correlation_id or record.lease_id,
                summary="revocation rejected because actor is not trusted",
                payload={
                    "lease_id": record.lease_id,
                    "revocation_id": record.revocation_id,
                    "revoked_by": revoked_by,
                    "reason_code": "REVOCATION_ACTOR_NOT_TRUSTED",
                },
                related_message_ids=[record.revocation_id] if record.revocation_id else [],
            )
            raise ValueError("revocation actor is not trusted")

        if lease.lease_id != record.lease_id:
            self.audit_log.record(
                event_type=AuditEventType.REVOCATION_REJECTED,
                actor_id=revoked_by,
                robot_id=lease.robot_id,
                mission_id=lease.mission_id,
                correlation_id=record.correlation_id or lease.lease_id,
                summary="revocation rejected because lease_id does not match lease",
                payload={
                    "revocation_lease_id": record.lease_id,
                    "lease_id": lease.lease_id,
                    "reason_code": "REVOCATION_LEASE_MISMATCH",
                },
                related_message_ids=[record.revocation_id] if record.revocation_id else [],
            )
            raise ValueError("revocation lease_id does not match lease")
        self.revocations[record.lease_id] = record
        self.audit_log.record(
            event_type=AuditEventType.LEASE_REVOKED,
            actor_id=revoked_by,
            robot_id=lease.robot_id,
            mission_id=lease.mission_id,
            correlation_id=record.correlation_id or lease.lease_id,
            summary=f"lease {record.lease_id} revoked: {record.reason_code}",
            payload={
                "lease_id": record.lease_id,
                "reason_code": record.reason_code,
                "fallback_action": record.fallback_action,
                "revocation_id": record.revocation_id,
            },
            related_message_ids=[record.revocation_id] if record.revocation_id else [],
        )
        fallback_action = record.fallback_action or self._trusted_lease_fallback_action(lease)
        declaration = FallbackDeclaration(
            correlation_id=record.correlation_id or lease.lease_id,
            robot_id=lease.robot_id,
            edge_agent_id=lease.edge_agent_id,
            mission_id=lease.mission_id,
            trigger=record.reason_code,
            fallback_action=fallback_action,
            declared_by=lease.edge_agent_id,
            lease_id=lease.lease_id,
            revocation_id=record.revocation_id,
        )
        self._emit_fallback(declaration)
        return declaration

    def evaluate(
        self,
        command: Command,
        lease: CapabilityLease | None,
        current_state: RobotStateAssertion | None = None,
    ) -> GateResult:
        ok, reason = validate_lease_for_command(
            lease,
            issuer_public_key_b64=self.issuer_public_key_b64,
            trusted_issuer_ids=self.trusted_issuer_ids,
            agent_id=command.agent_id,
            edge_agent_id=command.edge_agent_id,
            robot_id=command.robot_id,
            mission_id=command.mission_id,
            capability=command.capability,
            current_state=current_state,
            revoked_lease_ids=set(self.revocations),
            max_lease_age_seconds=self.max_lease_age_seconds,
            max_lease_ttl_seconds=self.max_lease_ttl_seconds,
        )
        if ok:
            payload = {
                "command_id": command.command_id,
                "agent_id": command.agent_id,
                "edge_agent_id": command.edge_agent_id,
                "robot_id": command.robot_id,
                "mission_id": command.mission_id,
                "capability": command.capability,
                "lease_id": lease.lease_id if lease else None,
                "reason_code": reason,
            }
            state_refs: list[str] = []
            related_message_ids = [command.command_id]
            if current_state is not None:
                state_refs.append(current_state.message_id)
                related_message_ids.append(current_state.message_id)
                payload["current_state"] = current_state.model_dump(mode="json")
            event = self.audit_log.record(
                event_type=AuditEventType.COMMAND_ALLOWED,
                actor_id=command.edge_agent_id,
                robot_id=command.robot_id,
                mission_id=command.mission_id,
                correlation_id=self._command_correlation_id(command, lease),
                summary=f"command {command.command_id} allowed: {reason}",
                payload=payload,
                state_refs=state_refs,
                related_message_ids=related_message_ids,
            )
            return GateResult(allowed=True, reason_code=reason, audit_id=event.audit_id)
        fallback = self._fallback_action_for_denial(command, lease, reason)
        command_correlation_id = self._command_correlation_id(command, lease)
        declaration = FallbackDeclaration(
            correlation_id=command_correlation_id,
            robot_id=command.robot_id,
            edge_agent_id=command.edge_agent_id,
            mission_id=command.mission_id,
            trigger=reason,
            fallback_action=fallback,
            declared_by=command.edge_agent_id,
            lease_id=lease.lease_id if lease else None,
            revocation_id=self.revocations[lease.lease_id].revocation_id
            if lease and lease.lease_id in self.revocations
            else None,
        )
        payload = {
            "command_id": command.command_id,
            "agent_id": command.agent_id,
            "edge_agent_id": command.edge_agent_id,
            "robot_id": command.robot_id,
            "mission_id": command.mission_id,
            "capability": command.capability,
            "lease_id": lease.lease_id if lease else None,
            "reason_code": reason,
            "fallback_action": fallback,
        }
        state_refs = []
        related_message_ids = [command.command_id]
        if current_state is not None:
            state_refs.append(current_state.message_id)
            related_message_ids.append(current_state.message_id)
            payload["current_state"] = current_state.model_dump(mode="json")
        event = self.audit_log.record(
            event_type=AuditEventType.COMMAND_REJECTED,
            actor_id=command.edge_agent_id,
            robot_id=command.robot_id,
            mission_id=command.mission_id,
            correlation_id=command_correlation_id,
            summary=f"command {command.command_id} rejected: {reason}",
            payload=payload,
            state_refs=state_refs,
            related_message_ids=related_message_ids,
        )
        self._emit_fallback(declaration)
        return GateResult(
            allowed=False,
            reason_code=reason,
            audit_id=event.audit_id,
            fallback_action=fallback,
            fallback_declaration=declaration,
        )

    def _fallback_action_for_denial(
        self,
        command: Command,
        lease: CapabilityLease | None,
        reason: str,
    ) -> FallbackAction:
        if lease is None:
            return FallbackAction.LOCAL_AUTONOMY_ONLY
        if reason == "LEASE_REVOKED":
            revocation = self.revocations.get(lease.lease_id)
            if revocation and revocation.fallback_action is not None:
                return revocation.fallback_action
        if self._lease_can_select_fallback(lease, command):
            return lease.constraints.fallback_on_degrade
        return FallbackAction.LOCAL_AUTONOMY_ONLY

    def _lease_can_select_fallback(self, lease: CapabilityLease, command: Command) -> bool:
        if lease.issuer_id not in self.trusted_issuer_ids:
            return False
        if not verify_lease_signature(lease, self.issuer_public_key_b64):
            return False
        return lease_matches_context(
            lease,
            agent_id=command.agent_id,
            edge_agent_id=command.edge_agent_id,
            robot_id=command.robot_id,
            mission_id=command.mission_id,
            capability=command.capability,
        )

    def _trusted_lease_fallback_action(self, lease: CapabilityLease) -> FallbackAction:
        if lease.issuer_id not in self.trusted_issuer_ids:
            return FallbackAction.LOCAL_AUTONOMY_ONLY
        if verify_lease_signature(lease, self.issuer_public_key_b64):
            return lease.constraints.fallback_on_degrade
        return FallbackAction.LOCAL_AUTONOMY_ONLY

    def _fallback_correlation_id(
        self,
        command: Command,
        lease: CapabilityLease | None,
    ) -> str | None:
        if command.correlation_id is not None:
            return command.correlation_id
        if lease is not None and lease.lease_id in self.revocations:
            return self.revocations[lease.lease_id].correlation_id
        return None

    def _command_correlation_id(self, command: Command, lease: CapabilityLease | None) -> str:
        fallback_correlation_id = self._fallback_correlation_id(command, lease)
        if fallback_correlation_id is not None:
            return fallback_correlation_id
        if lease is not None:
            return lease.lease_id
        return command.command_id

    def _emit_fallback(self, declaration: FallbackDeclaration) -> None:
        self.fallback_events.append(declaration)
        self.audit_log.record(
            event_type=AuditEventType.FALLBACK_DECLARED,
            actor_id=declaration.declared_by,
            robot_id=declaration.robot_id,
            mission_id=declaration.mission_id,
            correlation_id=declaration.correlation_id,
            summary=(
                f"fallback {declaration.fallback_action.value} declared after {declaration.trigger}"
            ),
            payload=declaration.model_dump(mode="json"),
            related_message_ids=[
                message_id
                for message_id in [
                    declaration.lease_id,
                    declaration.decision_id,
                    declaration.revocation_id,
                ]
                if message_id is not None
            ],
        )
        if self._fallback_sink is not None:
            self._fallback_sink(declaration)
