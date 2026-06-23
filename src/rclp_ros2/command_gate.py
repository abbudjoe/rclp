from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from rclp_core.audit import AuditLog
from rclp_core.conformance import validate_lease_for_command
from rclp_core.crypto import verify_with_public_key_b64
from rclp_core.leases import lease_matches_context
from rclp_core.models import (
    AuditEventType,
    BaseMessage,
    CapabilityConstraintRequirement,
    CapabilityLease,
    FallbackAction,
    FallbackDeclaration,
    LeaseRevocation,
    RobotStateAssertion,
    protocol_version_violation,
)
from rclp_core.state import DEFAULT_STATE_MAX_AGE_SECONDS


DEFAULT_REVOCATION_MAX_AGE_SECONDS = 300
REVOCATION_CLOCK_SKEW_SECONDS = 30
DEFAULT_COMMAND_MAX_AGE_SECONDS = 30
COMMAND_CLOCK_SKEW_SECONDS = 30

DEFAULT_LOCAL_FALLBACK_ACTIONS_BY_REASON: dict[str, FallbackAction] = {
    "NETWORK_LATENCY_TOO_HIGH": FallbackAction.CRAWL_TO_SAFE_ZONE,
    "NETWORK_PACKET_LOSS_TOO_HIGH": FallbackAction.CRAWL_TO_SAFE_ZONE,
    "NETWORK_UPLINK_TOO_LOW": FallbackAction.CRAWL_TO_SAFE_ZONE,
    "NETWORK_DETACHED": FallbackAction.CRAWL_TO_SAFE_ZONE,
    "NETWORK_STATE_UNKNOWN": FallbackAction.CRAWL_TO_SAFE_ZONE,
    "NETWORK_PROFILE_REVOKE": FallbackAction.CRAWL_TO_SAFE_ZONE,
    "NETWORK_DEGRADED_REVOKE": FallbackAction.CRAWL_TO_SAFE_ZONE,
    "GEOFENCE_CONSTRAINT_VIOLATED": FallbackAction.HOLD_POSITION,
}


class EdgeCommand(BaseMessage):
    message_type: Literal["edge_command"] = "edge_command"
    command_id: str
    agent_id: str
    authenticated_agent_id: str | None = None
    edge_agent_id: str
    robot_id: str
    mission_id: str
    capability: str
    command_nonce: str = Field(default_factory=lambda: f"cmd_nonce_{uuid4().hex}")
    payload: dict
    signature: str | None = None


Command = EdgeCommand


class GateResult(BaseModel):
    allowed: bool
    reason_code: str
    audit_id: str | None = None
    fallback_action: FallbackAction | None = None
    fallback_declaration: FallbackDeclaration | None = None


class RevokedLease(BaseModel):
    lease_id: str
    issuer_id: str
    agent_id: str
    edge_agent_id: str
    robot_id: str
    mission_id: str
    capability: str
    reason_code: str = "LEASE_REVOKED"
    fallback_action: FallbackAction | None = None
    revocation_id: str | None = None
    correlation_id: str | None = None


class CommandReplayCache:
    """Durable replay window for signed edge commands.

    A cache without a store path is intentionally non-durable and cannot be used
    by `CommandGate`; it remains useful only for construction-level tests.
    """

    def __init__(self, store_path: str | Path | None = None) -> None:
        self._store_path = Path(store_path) if store_path is not None else None
        self._tempdir: TemporaryDirectory[str] | None = None
        self._seen_command_ids: set[tuple[str, str]] = set()
        self._seen_nonces: set[tuple[str, str]] = set()
        if self._store_path is not None:
            self._store_path.parent.mkdir(parents=True, exist_ok=True)
            with self._connect() as connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS command_replay_entries (
                        authenticated_agent_id TEXT NOT NULL,
                        replay_kind TEXT NOT NULL,
                        replay_value TEXT NOT NULL,
                        command_id TEXT NOT NULL,
                        command_nonce TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        consumed_at TEXT NOT NULL,
                        PRIMARY KEY (
                            authenticated_agent_id,
                            replay_kind,
                            replay_value
                        )
                    )
                    """
                )

    @classmethod
    def temporary(cls) -> "CommandReplayCache":
        tempdir = TemporaryDirectory(prefix="rclp-command-replay-")
        cache = cls(Path(tempdir.name) / "command_replay.sqlite3")
        cache._tempdir = tempdir
        return cache

    @property
    def durable(self) -> bool:
        return self._store_path is not None

    @property
    def store_path(self) -> Path | None:
        return self._store_path

    def _connect(self) -> sqlite3.Connection:
        if self._store_path is None:
            raise ValueError("command replay cache has no durable store")
        return sqlite3.connect(self._store_path, timeout=30, isolation_level="IMMEDIATE")

    def remember(self, command: Command) -> bool:
        if command.authenticated_agent_id is None:
            return False
        command_id_key = (command.authenticated_agent_id, command.command_id)
        nonce_key = (command.authenticated_agent_id, command.command_nonce)
        if self._store_path is not None:
            consumed_at = datetime.now(timezone.utc).isoformat()
            try:
                with self._connect() as connection:
                    connection.execute(
                        """
                        INSERT INTO command_replay_entries (
                            authenticated_agent_id,
                            replay_kind,
                            replay_value,
                            command_id,
                            command_nonce,
                            created_at,
                            consumed_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            command.authenticated_agent_id,
                            "command_id",
                            command.command_id,
                            command.command_id,
                            command.command_nonce,
                            command.created_at.isoformat(),
                            consumed_at,
                        ),
                    )
                    connection.execute(
                        """
                        INSERT INTO command_replay_entries (
                            authenticated_agent_id,
                            replay_kind,
                            replay_value,
                            command_id,
                            command_nonce,
                            created_at,
                            consumed_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            command.authenticated_agent_id,
                            "command_nonce",
                            command.command_nonce,
                            command.command_id,
                            command.command_nonce,
                            command.created_at.isoformat(),
                            consumed_at,
                        ),
                    )
            except sqlite3.IntegrityError:
                return False
            return True
        if command_id_key in self._seen_command_ids or nonce_key in self._seen_nonces:
            return False
        self._seen_command_ids.add(command_id_key)
        self._seen_nonces.add(nonce_key)
        return True


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
        accepted_capabilities: set[str] | None = None,
        issuer_capability_scopes: Mapping[str, set[str]] | None = None,
        capability_constraint_requirements: (
            Mapping[str, CapabilityConstraintRequirement] | None
        ) = None,
        agent_public_keys_by_id: Mapping[str, str] | None = None,
        issuer_public_keys_by_id: Mapping[str, str] | None = None,
        revoker_public_keys_by_id: Mapping[str, str] | None = None,
        revoker_edge_scopes_by_id: Mapping[str, set[str]] | None = None,
        state_public_keys_by_edge_id: Mapping[str, str] | None = None,
        command_replay_cache: CommandReplayCache | None = None,
        fallback_sink: Callable[[FallbackDeclaration], None] | None = None,
        audit_log: AuditLog | None = None,
        fallback_actions_by_reason: Mapping[str, FallbackAction] | None = None,
        max_lease_age_seconds: int = 600,
        max_lease_ttl_seconds: int = 600,
        max_state_age_seconds: int = DEFAULT_STATE_MAX_AGE_SECONDS,
        max_command_age_seconds: int = DEFAULT_COMMAND_MAX_AGE_SECONDS,
        max_revocation_age_seconds: int = DEFAULT_REVOCATION_MAX_AGE_SECONDS,
    ) -> None:
        if not trusted_issuer_ids:
            raise ValueError("trusted_issuer_ids must name at least one lease issuer")
        if not trusted_revoker_ids:
            raise ValueError("trusted_revoker_ids must name at least one revocation actor")
        if not accepted_capabilities:
            raise ValueError("accepted_capabilities must name at least one local capability")
        if issuer_capability_scopes is None:
            raise ValueError("issuer_capability_scopes is required")
        if capability_constraint_requirements is None:
            raise ValueError("capability_constraint_requirements is required")
        if not agent_public_keys_by_id:
            raise ValueError("agent_public_keys_by_id must name at least one command agent key")
        if command_replay_cache is None or not command_replay_cache.durable:
            raise ValueError("durable command_replay_cache is required")
        if issuer_public_keys_by_id is None and len(trusted_issuer_ids) != 1:
            raise ValueError("issuer_public_keys_by_id is required for multiple lease issuers")
        self.issuer_public_key_b64 = issuer_public_key_b64
        self.trusted_issuer_ids = set(trusted_issuer_ids)
        self.accepted_capabilities = set(accepted_capabilities)
        self.issuer_capability_scopes = {
            issuer_id: set(capabilities)
            for issuer_id, capabilities in issuer_capability_scopes.items()
        }
        self.capability_constraint_requirements = dict(capability_constraint_requirements)
        for issuer_id in self.trusted_issuer_ids:
            if not self.issuer_capability_scopes.get(issuer_id):
                raise ValueError("issuer_capability_scopes must scope every trusted issuer")
        for capability in self.accepted_capabilities:
            requirement = self.capability_constraint_requirements.get(capability)
            if requirement is None or str(requirement.capability) != capability:
                raise ValueError(
                    "capability_constraint_requirements must cover every accepted capability"
                )
        self.agent_public_keys_by_id = dict(agent_public_keys_by_id)
        self.issuer_public_keys_by_id = dict(
            issuer_public_keys_by_id or {next(iter(trusted_issuer_ids)): issuer_public_key_b64}
        )
        self.trusted_revoker_ids = set(trusted_revoker_ids)
        self.revoker_public_keys_by_id = dict(revoker_public_keys_by_id or {})
        configured_revoker_scopes = {
            revoker_id: set(edge_ids)
            for revoker_id, edge_ids in (revoker_edge_scopes_by_id or {}).items()
        }
        self.revoker_edge_scopes_by_id = {
            revoker_id: configured_revoker_scopes.get(revoker_id, {revoker_id})
            for revoker_id in self.trusted_revoker_ids
        }
        self.state_public_keys_by_edge_id = dict(state_public_keys_by_edge_id or {})
        self.fallback_actions_by_reason = {
            **DEFAULT_LOCAL_FALLBACK_ACTIONS_BY_REASON,
            **dict(fallback_actions_by_reason or {}),
        }
        self.max_lease_age_seconds = max_lease_age_seconds
        self.max_lease_ttl_seconds = max_lease_ttl_seconds
        self.max_state_age_seconds = max_state_age_seconds
        self.max_command_age_seconds = max_command_age_seconds
        self.max_revocation_age_seconds = max_revocation_age_seconds
        self.command_replay_cache = command_replay_cache
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
        now: datetime | None = None,
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
            issuer_id=lease.issuer_id if lease else "",
            agent_id=lease.agent_id if lease else "",
            edge_agent_id=lease.edge_agent_id if lease else "",
            robot_id=lease.robot_id if lease else "",
            mission_id=lease.mission_id if lease else "",
            capability=str(lease.capability) if lease else "",
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

        if version_reason := protocol_version_violation(revocation):
            self._record_revocation_rejected(
                revocation=revocation,
                lease=lease,
                reason_code=version_reason,
                summary="revocation rejected because protocol version is unsupported",
            )
            raise ValueError("revocation protocol version is unsupported")

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

        if revocation.signature is None:
            self._record_revocation_rejected(
                revocation=revocation,
                lease=lease,
                reason_code="REVOCATION_SIGNATURE_MISSING",
                summary="revocation rejected because signature is missing",
            )
            raise ValueError("revocation signature is missing")

        revoker_public_key = self.revoker_public_keys_by_id.get(revoked_by)
        if revoker_public_key is None:
            self._record_revocation_rejected(
                revocation=revocation,
                lease=lease,
                reason_code="REVOCATION_KEY_NOT_TRUSTED",
                summary="revocation rejected because revoker key is not trusted",
            )
            raise ValueError("revocation key is not trusted")
        if not verify_with_public_key_b64(revocation, revocation.signature, revoker_public_key):
            self._record_revocation_rejected(
                revocation=revocation,
                lease=lease,
                reason_code="REVOCATION_SIGNATURE_INVALID",
                summary="revocation rejected because signature is invalid",
            )
            raise ValueError("revocation signature is invalid")

        if lease.edge_agent_id not in self.revoker_edge_scopes_by_id.get(revoked_by, set()):
            self.audit_log.record(
                event_type=AuditEventType.REVOCATION_REJECTED,
                actor_id=revoked_by,
                robot_id=lease.robot_id,
                mission_id=lease.mission_id,
                correlation_id=record.correlation_id or record.lease_id,
                summary="revocation rejected because actor is not scoped to lease edge",
                payload={
                    "lease_id": record.lease_id,
                    "revocation_id": record.revocation_id,
                    "revoked_by": revoked_by,
                    "revoker_edge_scope": sorted(
                        self.revoker_edge_scopes_by_id.get(revoked_by, set())
                    ),
                    "revocation_edge_agent_id": revocation.edge_agent_id,
                    "lease_edge_agent_id": lease.edge_agent_id,
                    "reason_code": "REVOCATION_ACTOR_SCOPE_MISMATCH",
                },
                related_message_ids=[record.revocation_id] if record.revocation_id else [],
            )
            raise ValueError("revocation actor is not authorized for lease edge")

        if time_reason := self._revocation_time_violation(revocation, now=now):
            self._record_revocation_rejected(
                revocation=revocation,
                lease=lease,
                reason_code=time_reason,
                summary=f"revocation rejected because it is not fresh: {time_reason}",
            )
            raise ValueError("revocation is not fresh")

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
        if self._revocation_context_conflicts(revocation, lease):
            self.audit_log.record(
                event_type=AuditEventType.REVOCATION_REJECTED,
                actor_id=revoked_by,
                robot_id=lease.robot_id,
                mission_id=lease.mission_id,
                correlation_id=record.correlation_id or lease.lease_id,
                summary="revocation rejected because context does not match lease",
                payload={
                    "revocation_lease_id": record.lease_id,
                    "lease_id": lease.lease_id,
                    "revocation_edge_agent_id": revocation.edge_agent_id,
                    "lease_edge_agent_id": lease.edge_agent_id,
                    "revocation_robot_id": revocation.robot_id,
                    "lease_robot_id": lease.robot_id,
                    "revocation_mission_id": revocation.mission_id,
                    "lease_mission_id": lease.mission_id,
                    "revocation_capability": revocation.capability,
                    "lease_capability": lease.capability,
                    "reason_code": "REVOCATION_CONTEXT_MISMATCH",
                },
                related_message_ids=[record.revocation_id] if record.revocation_id else [],
            )
            raise ValueError("revocation context does not match lease")
        self.revocations[record.lease_id] = record
        fallback_action = self._local_fallback_action(record.reason_code)
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
                "requested_fallback_action": record.fallback_action,
                "fallback_action": fallback_action,
                "revocation_id": record.revocation_id,
            },
            related_message_ids=[record.revocation_id] if record.revocation_id else [],
        )
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
        now: datetime | None = None,
    ) -> GateResult:
        if auth_reason := self._command_auth_violation(command, now=now):
            return self._reject_command(
                command=command,
                lease=lease,
                current_state=current_state,
                reason=auth_reason,
            )
        ok, reason = validate_lease_for_command(
            lease,
            issuer_public_key_b64=self.issuer_public_key_b64,
            issuer_public_keys_by_id=self.issuer_public_keys_by_id,
            trusted_issuer_ids=self.trusted_issuer_ids,
            accepted_capabilities=self.accepted_capabilities,
            issuer_capability_scopes=self.issuer_capability_scopes,
            capability_constraint_requirements=self.capability_constraint_requirements,
            agent_id=command.agent_id,
            edge_agent_id=command.edge_agent_id,
            robot_id=command.robot_id,
            mission_id=command.mission_id,
            capability=command.capability,
            current_state=current_state,
            state_public_keys_by_edge_id=self.state_public_keys_by_edge_id,
            revoked_lease_ids=set(self.revocations),
            max_lease_age_seconds=self.max_lease_age_seconds,
            max_lease_ttl_seconds=self.max_lease_ttl_seconds,
            max_state_age_seconds=self.max_state_age_seconds,
            command_payload=command.payload,
            now=now,
        )
        if ok:
            payload = {
                "command_id": command.command_id,
                "command_message_id": command.message_id,
                "agent_id": command.agent_id,
                "authenticated_agent_id": command.authenticated_agent_id,
                "edge_agent_id": command.edge_agent_id,
                "robot_id": command.robot_id,
                "mission_id": command.mission_id,
                "capability": command.capability,
                "command_nonce": command.command_nonce,
                "lease_id": lease.lease_id if lease else None,
                "reason_code": reason,
            }
            state_refs: list[str] = []
            related_message_ids = [command.message_id]
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
        return self._reject_command(
            command=command,
            lease=lease,
            current_state=current_state,
            reason=reason,
        )

    def _reject_command(
        self,
        *,
        command: Command,
        lease: CapabilityLease | None,
        current_state: RobotStateAssertion | None,
        reason: str,
    ) -> GateResult:
        revocation = self._matching_authenticated_revocation(command, lease, reason)
        fallback = self._fallback_action_for_denial(command, lease, reason, revocation)
        command_correlation_id = self._command_correlation_id(command, lease, revocation)
        declaration = FallbackDeclaration(
            correlation_id=command_correlation_id,
            robot_id=command.robot_id,
            edge_agent_id=command.edge_agent_id,
            mission_id=command.mission_id,
            trigger=reason,
            fallback_action=fallback,
            declared_by=command.edge_agent_id,
            lease_id=lease.lease_id if lease else None,
            revocation_id=revocation.revocation_id if revocation else None,
        )
        payload = {
            "command_id": command.command_id,
            "command_message_id": command.message_id,
            "agent_id": command.agent_id,
            "authenticated_agent_id": command.authenticated_agent_id,
            "edge_agent_id": command.edge_agent_id,
            "robot_id": command.robot_id,
            "mission_id": command.mission_id,
            "capability": command.capability,
            "command_nonce": command.command_nonce,
            "lease_id": lease.lease_id if lease else None,
            "reason_code": reason,
            "fallback_action": fallback,
        }
        state_refs = []
        related_message_ids = [command.message_id]
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

    def _command_auth_violation(
        self,
        command: Command,
        *,
        now: datetime | None = None,
    ) -> str | None:
        if version_reason := protocol_version_violation(command):
            return version_reason
        if not command.command_id.strip():
            return "COMMAND_ID_MISSING"
        if not command.command_nonce.strip():
            return "COMMAND_NONCE_MISSING"
        if command.authenticated_agent_id is None:
            return "COMMAND_AUTHENTICATED_AGENT_MISSING"
        if command.authenticated_agent_id != command.agent_id:
            return "COMMAND_AUTHENTICATED_AGENT_MISMATCH"
        public_key = self.agent_public_keys_by_id.get(command.authenticated_agent_id)
        if public_key is None:
            return "COMMAND_AGENT_KEY_NOT_TRUSTED"
        if command.signature is None:
            return "COMMAND_SIGNATURE_MISSING"
        if not verify_with_public_key_b64(command, command.signature, public_key):
            return "COMMAND_SIGNATURE_INVALID"
        if time_reason := self._command_time_violation(command, now=now):
            return time_reason
        if not self.command_replay_cache.remember(command):
            return "COMMAND_REPLAYED"
        return None

    def _command_time_violation(
        self,
        command: Command,
        *,
        now: datetime | None = None,
    ) -> str | None:
        now = now or datetime.now(timezone.utc)
        if command.created_at.tzinfo is None or command.created_at.utcoffset() is None:
            return "COMMAND_TIMESTAMP_INVALID"
        if command.created_at > now + timedelta(seconds=COMMAND_CLOCK_SKEW_SECONDS):
            return "COMMAND_NOT_YET_VALID"
        if now - command.created_at > timedelta(
            seconds=self.max_command_age_seconds + COMMAND_CLOCK_SKEW_SECONDS
        ):
            return "COMMAND_STALE"
        return None

    def _fallback_action_for_denial(
        self,
        command: Command,
        lease: CapabilityLease | None,
        reason: str,
        revocation: RevokedLease | None,
    ) -> FallbackAction:
        if reason == "LEASE_REVOKED" and revocation is not None:
            return self._local_fallback_action(revocation.reason_code)
        return self._local_fallback_action(reason)

    def _local_fallback_action(self, reason: str) -> FallbackAction:
        return self.fallback_actions_by_reason.get(reason, FallbackAction.LOCAL_AUTONOMY_ONLY)

    def _revocation_time_violation(
        self,
        revocation: LeaseRevocation,
        *,
        now: datetime | None = None,
    ) -> str | None:
        now = now or datetime.now(timezone.utc)
        for timestamp in [revocation.created_at, revocation.revoked_at]:
            if timestamp.tzinfo is None or timestamp.utcoffset() is None:
                return "REVOCATION_TIMESTAMP_INVALID"
            if timestamp > now + timedelta(seconds=REVOCATION_CLOCK_SKEW_SECONDS):
                return "REVOCATION_NOT_YET_VALID"
            if now - timestamp > timedelta(
                seconds=self.max_revocation_age_seconds + REVOCATION_CLOCK_SKEW_SECONDS
            ):
                return "REVOCATION_STALE"
        if revocation.revoked_at < revocation.created_at - timedelta(
            seconds=REVOCATION_CLOCK_SKEW_SECONDS
        ):
            return "REVOCATION_TIME_INCONSISTENT"
        return None

    def _record_revocation_rejected(
        self,
        *,
        revocation: LeaseRevocation,
        lease: CapabilityLease,
        reason_code: str,
        summary: str,
    ) -> None:
        self.audit_log.record(
            event_type=AuditEventType.REVOCATION_REJECTED,
            actor_id=revocation.revoked_by,
            robot_id=lease.robot_id,
            mission_id=lease.mission_id,
            correlation_id=revocation.correlation_id or lease.lease_id,
            summary=summary,
            payload={
                "lease_id": revocation.lease_id,
                "revocation_id": revocation.message_id,
                "revoked_by": revocation.revoked_by,
                "reason_code": reason_code,
            },
            related_message_ids=[revocation.message_id],
        )

    def _revocation_context_conflicts(
        self,
        revocation: LeaseRevocation,
        lease: CapabilityLease,
    ) -> bool:
        if revocation.edge_agent_id != lease.edge_agent_id:
            return True
        if revocation.robot_id is not None and revocation.robot_id != lease.robot_id:
            return True
        if revocation.mission_id is not None and revocation.mission_id != lease.mission_id:
            return True
        return revocation.capability is not None and revocation.capability != lease.capability

    def _matching_authenticated_revocation(
        self,
        command: Command,
        lease: CapabilityLease | None,
        reason: str,
    ) -> RevokedLease | None:
        if reason != "LEASE_REVOKED" or lease is None:
            return None
        revocation = self.revocations.get(lease.lease_id)
        if revocation is None:
            return None
        if (
            revocation.issuer_id != lease.issuer_id
            or revocation.agent_id != lease.agent_id
            or revocation.edge_agent_id != lease.edge_agent_id
            or revocation.robot_id != lease.robot_id
            or revocation.mission_id != lease.mission_id
            or revocation.capability != str(lease.capability)
        ):
            return None
        if not lease_matches_context(
            lease,
            agent_id=command.agent_id,
            edge_agent_id=command.edge_agent_id,
            robot_id=command.robot_id,
            mission_id=command.mission_id,
            capability=command.capability,
        ):
            return None
        return revocation

    def _command_correlation_id(
        self,
        command: Command,
        lease: CapabilityLease | None,
        revocation: RevokedLease | None = None,
    ) -> str:
        if revocation is not None and revocation.correlation_id is not None:
            return revocation.correlation_id
        if command.correlation_id is not None:
            return command.correlation_id
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
