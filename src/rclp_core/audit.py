from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from rclp_core.models import AuditCommit, AuditEventType, stable_json_hash


AUTHORITY_EVENT_TYPES = {
    AuditEventType.CAPABILITY_REQUESTED,
    AuditEventType.NETWORK_STATE_ASSERTED,
    AuditEventType.CAPABILITY_ALLOWED,
    AuditEventType.CAPABILITY_DENIED,
    AuditEventType.CAPABILITY_DEGRADED,
    AuditEventType.COMMAND_ALLOWED,
    AuditEventType.COMMAND_REJECTED,
    AuditEventType.LEASE_REVOKED,
    AuditEventType.REVOCATION_REJECTED,
    AuditEventType.FALLBACK_DECLARED,
}

LOAD_REQUIRED_FIELDS = {
    "protocol_version",
    "message_id",
    "audit_id",
    "correlation_id",
    "created_at",
    "message_type",
    "event_type",
    "actor_id",
    "summary",
    "payload",
    "payload_hash",
    "authority_relevant",
    "integrity_profile",
    "integrity_proof",
}


class ReplayItem(BaseModel):
    audit_id: str
    event_type: AuditEventType
    actor_id: str
    reason_code: str | None = None
    command_id: str | None = None
    lease_id: str | None = None
    request_id: str | None = None
    state_id: str | None = None
    declaration_id: str | None = None
    fallback_action: str | None = None
    state_refs: list[str] = Field(default_factory=list)
    related_message_ids: list[str] = Field(default_factory=list)


class CorrelationReplay(BaseModel):
    correlation_id: str
    requests: list[ReplayItem] = Field(default_factory=list)
    states: list[ReplayItem] = Field(default_factory=list)
    decisions: list[ReplayItem] = Field(default_factory=list)
    enforcement: list[ReplayItem] = Field(default_factory=list)
    revocations: list[ReplayItem] = Field(default_factory=list)
    fallbacks: list[ReplayItem] = Field(default_factory=list)
    diagnostics: list[ReplayItem] = Field(default_factory=list)


class AuditLog:
    def __init__(self) -> None:
        self.events: list[AuditCommit] = []
        self._audit_ids: set[str] = set()

    def append(self, event: AuditCommit) -> AuditCommit:
        if event.audit_id in self._audit_ids:
            raise ValueError(f"duplicate audit_id: {event.audit_id}")
        previous_hash = self.events[-1].integrity_proof if self.events else None
        self._validate_context(event)
        self._validate_payload_hash(event)
        expected_proof = self._integrity_proof(event, previous_hash)
        if event.previous_audit_hash not in {None, previous_hash}:
            raise ValueError("previous_audit_hash does not match audit chain")
        if event.integrity_proof is not None and event.integrity_proof != expected_proof:
            raise ValueError("integrity_proof does not match audit event")
        committed = event.model_copy(
            update={
                "previous_audit_hash": event.previous_audit_hash or previous_hash,
                "integrity_proof": expected_proof,
            }
        )
        self.events.append(committed)
        self._audit_ids.add(committed.audit_id)
        return committed

    def record(
        self,
        *,
        event_type: AuditEventType | str,
        actor_id: str,
        summary: str,
        correlation_id: str,
        robot_id: str | None = None,
        mission_id: str | None = None,
        payload: dict[str, Any] | None = None,
        authority_relevant: bool = True,
        policy_id: str | None = None,
        policy_digest: str | None = None,
        state_refs: list[str] | None = None,
        related_message_ids: list[str] | None = None,
    ) -> AuditCommit:
        return self.append(
            AuditCommit(
                correlation_id=correlation_id,
                event_type=event_type,
                actor_id=actor_id,
                robot_id=robot_id,
                mission_id=mission_id,
                summary=summary,
                payload=payload or {},
                authority_relevant=authority_relevant,
                policy_id=policy_id,
                policy_digest=policy_digest,
                state_refs=state_refs or [],
                related_message_ids=related_message_ids or [],
            )
        )

    def to_jsonl(self) -> str:
        return "\n".join(event.model_dump_json() for event in self.events)

    def write_jsonl(self, path: str | Path) -> None:
        text = self.to_jsonl()
        Path(path).write_text(text + ("\n" if text else ""), encoding="utf-8")

    @property
    def chain_head(self) -> str | None:
        return self.events[-1].integrity_proof if self.events else None

    def by_correlation_id(self) -> dict[str, list[AuditCommit]]:
        groups: dict[str, list[AuditCommit]] = defaultdict(list)
        for event in self.events:
            groups[event.correlation_id].append(event)
        return dict(groups)

    def replay(self) -> dict[str, CorrelationReplay]:
        groups: dict[str, CorrelationReplay] = {}
        for correlation_id, events in self.by_correlation_id().items():
            group = CorrelationReplay(correlation_id=correlation_id)
            for event in events:
                item = _replay_item(event)
                if event.event_type == AuditEventType.CAPABILITY_REQUESTED:
                    group.requests.append(item)
                elif event.event_type == AuditEventType.NETWORK_STATE_ASSERTED:
                    group.states.append(item)
                elif event.event_type in {
                    AuditEventType.CAPABILITY_ALLOWED,
                    AuditEventType.CAPABILITY_DENIED,
                    AuditEventType.CAPABILITY_DEGRADED,
                }:
                    group.decisions.append(item)
                elif event.event_type in {
                    AuditEventType.COMMAND_ALLOWED,
                    AuditEventType.COMMAND_REJECTED,
                }:
                    group.enforcement.append(item)
                elif event.event_type in {
                    AuditEventType.LEASE_REVOKED,
                    AuditEventType.REVOCATION_REJECTED,
                }:
                    group.revocations.append(item)
                elif event.event_type == AuditEventType.FALLBACK_DECLARED:
                    group.fallbacks.append(item)
                else:
                    group.diagnostics.append(item)
            groups[correlation_id] = group
        return groups

    def replay_summary(self) -> str:
        lines: list[str] = []
        for correlation_id, replay in self.replay().items():
            lines.append(f"Correlation {correlation_id}:")
            for label, items in [
                ("requests", replay.requests),
                ("states", replay.states),
                ("decisions", replay.decisions),
                ("enforcement", replay.enforcement),
                ("revocations", replay.revocations),
                ("fallbacks", replay.fallbacks),
                ("diagnostics", replay.diagnostics),
            ]:
                if not items:
                    continue
                lines.append(f"  {label}:")
                for item in items:
                    details = _replay_details(item)
                    lines.append(f"    - {item.event_type} audit={item.audit_id}{details}")
        return "\n".join(lines)

    def _validate_context(self, event: AuditCommit) -> None:
        if event.event_type in AUTHORITY_EVENT_TYPES:
            if not event.authority_relevant:
                raise ValueError("authority event type must be authority_relevant")
            if event.robot_id is None or event.mission_id is None:
                raise ValueError("authority-relevant audit event requires robot_id and mission_id")

    def _validate_payload_hash(self, event: AuditCommit) -> None:
        expected_payload_hash = stable_json_hash(event.payload)
        if event.payload_hash != expected_payload_hash:
            raise ValueError("payload_hash does not match audit payload")

    def _integrity_proof(self, event: AuditCommit, previous_hash: str | None) -> str:
        return stable_json_hash(
            {
                "audit_id": event.audit_id,
                "message_id": event.message_id,
                "message_type": event.message_type,
                "protocol_version": event.protocol_version,
                "correlation_id": event.correlation_id,
                "created_at": event.created_at,
                "event_type": event.event_type,
                "actor_id": event.actor_id,
                "robot_id": event.robot_id,
                "mission_id": event.mission_id,
                "summary": event.summary,
                "payload_hash": event.payload_hash,
                "authority_relevant": event.authority_relevant,
                "integrity_profile": event.integrity_profile,
                "policy_id": event.policy_id,
                "policy_digest": event.policy_digest,
                "state_refs": event.state_refs,
                "related_message_ids": event.related_message_ids,
                "previous_audit_hash": previous_hash,
            }
        )


AuditImportProfile = Literal["authority_chain", "diagnostic_only"]


def load_jsonl(
    path: str | Path,
    *,
    trusted_chain_head: str | None = None,
    import_profile: AuditImportProfile = "authority_chain",
) -> list[AuditCommit]:
    if import_profile not in {"authority_chain", "diagnostic_only"}:
        raise ValueError(f"unsupported audit import profile: {import_profile}")
    events: list[AuditCommit] = []
    audit_ids: set[str] = set()
    previous_hash: str | None = None
    validator = AuditLog()
    authority_events = False
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            raw_event = json.loads(line)
            missing_fields = LOAD_REQUIRED_FIELDS - raw_event.keys()
            if missing_fields:
                missing = ", ".join(sorted(missing_fields))
                raise ValueError(f"audit event missing required fields: {missing}")
            null_fields = {field for field in LOAD_REQUIRED_FIELDS if raw_event.get(field) is None}
            if null_fields:
                null = ", ".join(sorted(null_fields))
                raise ValueError(f"audit event required fields cannot be null: {null}")
            event = AuditCommit.model_validate(raw_event)
            if event.audit_id in audit_ids:
                raise ValueError(f"duplicate audit_id: {event.audit_id}")
            validator._validate_context(event)
            validator._validate_payload_hash(event)
            if event.previous_audit_hash != previous_hash:
                raise ValueError("previous_audit_hash does not match audit chain")
            if event.integrity_proof != validator._integrity_proof(event, previous_hash):
                raise ValueError("integrity_proof does not match audit event")
            if event.authority_relevant or event.event_type in AUTHORITY_EVENT_TYPES:
                authority_events = True
            audit_ids.add(event.audit_id)
            events.append(event)
            previous_hash = event.integrity_proof
    if import_profile == "diagnostic_only":
        if authority_events:
            raise ValueError("diagnostic-only audit import cannot include authority events")
        return events
    if events:
        if trusted_chain_head is None:
            raise ValueError("trusted audit chain head required for audit import")
        if trusted_chain_head != previous_hash:
            raise ValueError("trusted audit chain head does not match audit chain")
    return events


def _replay_item(event: AuditCommit) -> ReplayItem:
    payload = event.payload
    request_id = payload.get("request_id")
    state_id = payload.get("state_assertion_id")
    declaration_id = None
    if event.event_type == AuditEventType.CAPABILITY_REQUESTED:
        request_id = payload.get("message_id")
    if event.event_type == AuditEventType.NETWORK_STATE_ASSERTED:
        state_id = payload.get("message_id")
    if event.event_type == AuditEventType.FALLBACK_DECLARED:
        declaration_id = payload.get("message_id")
    return ReplayItem(
        audit_id=event.audit_id,
        event_type=event.event_type,
        actor_id=event.actor_id,
        reason_code=payload.get("reason_code") or payload.get("trigger"),
        command_id=payload.get("command_id"),
        lease_id=payload.get("lease_id"),
        request_id=request_id,
        state_id=state_id,
        declaration_id=declaration_id,
        fallback_action=payload.get("fallback_action"),
        state_refs=event.state_refs,
        related_message_ids=event.related_message_ids,
    )


def _replay_details(item: ReplayItem) -> str:
    parts: list[str] = []
    for label, value in [
        ("reason", item.reason_code),
        ("command", item.command_id),
        ("lease", item.lease_id),
        ("request", item.request_id),
        ("state", item.state_id),
        ("declaration", item.declaration_id),
        ("fallback", item.fallback_action),
    ]:
        if value is not None:
            parts.append(f"{label}={value}")
    if item.state_refs:
        parts.append(f"state_refs={','.join(item.state_refs)}")
    if item.related_message_ids:
        parts.append(f"related={','.join(item.related_message_ids)}")
    return " " + " ".join(parts) if parts else ""
