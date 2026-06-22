from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Capability(StrEnum):
    REMOTE_ASSIST = "remote_assist"
    MISSION_CONTINUE = "mission_continue"
    AUTONOMY_ESCALATION = "autonomy_escalation"


class Decision(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    DEGRADE = "degrade"


class FallbackAction(StrEnum):
    LOCAL_AUTONOMY_ONLY = "local_autonomy_only"
    CRAWL_TO_SAFE_ZONE = "crawl_to_safe_zone"
    HOLD_POSITION = "hold_position"
    REVOKE_REMOTE_ASSIST = "revoke_remote_assist"
    ESCALATE_TO_HUMAN = "escalate_to_human"


class AuditEventType(StrEnum):
    DEMO_SETUP = "demo_setup"
    CAPABILITY_REQUESTED = "capability_requested"
    NETWORK_STATE_ASSERTED = "network_state_asserted"
    CAPABILITY_ALLOWED = "capability_allowed"
    CAPABILITY_DENIED = "capability_denied"
    CAPABILITY_DEGRADED = "capability_degraded"
    COMMAND_ALLOWED = "command_allowed"
    COMMAND_REJECTED = "command_rejected"
    LEASE_REVOKED = "lease_revoked"
    REVOCATION_REJECTED = "revocation_rejected"
    FALLBACK_DECLARED = "fallback_declared"
    DIAGNOSTIC = "diagnostic"


class SafetyState(StrEnum):
    NOMINAL = "nominal"
    DEGRADED = "degraded"
    EMERGENCY = "emergency"


class NetworkProfile(StrEnum):
    UNKNOWN = "unknown"
    NORMAL = "normal"
    DEGRADED_TELEOP = "degraded_teleop"
    UPLINK_BAD = "uplink_bad"
    PARTITION = "partition"


class BaseMessage(BaseModel):
    protocol_version: str = "0.0.1-draft"
    message_id: str = Field(default_factory=lambda: f"msg_{uuid4().hex}")
    correlation_id: str = Field(default_factory=lambda: f"corr_{uuid4().hex}")
    created_at: datetime = Field(default_factory=utc_now)


class AgentAttestation(BaseMessage):
    message_type: Literal["agent_attestation"] = "agent_attestation"
    agent_id: str
    kind: Literal["central_agent", "edge_agent", "human_operator", "service"]
    manifest_digest: str
    public_key_id: str
    trust_tier: Literal["development", "staging", "production"] = "development"
    revoked: bool = False


AgentIdentity = AgentAttestation


class RobotIdentity(BaseModel):
    robot_id: str
    hardware_id: str
    edge_agent_id: str


class MissionContext(BaseModel):
    mission_id: str
    mission_type: str = "demo"
    human_operator_available: bool = False


class NetworkState(BaseModel):
    profile: NetworkProfile = NetworkProfile.UNKNOWN
    attached: bool = True
    latency_ms_p95: float = Field(ge=0)
    packet_loss_pct: float = Field(ge=0, le=100)
    uplink_mbps: float = Field(ge=0)
    observed_at: datetime = Field(default_factory=utc_now)


class GeofenceState(BaseModel):
    geofence_id: str
    inside: bool
    verified_at: datetime = Field(default_factory=utc_now)


class RobotStateAssertion(BaseMessage):
    message_type: Literal["robot_state_assertion"] = "robot_state_assertion"
    robot_id: str
    edge_agent_id: str
    mission_id: str
    safety_state: SafetyState = SafetyState.NOMINAL
    network_state: NetworkState
    geofence_state: GeofenceState
    observed_at: datetime = Field(default_factory=utc_now)
    human_operator_available: bool = True


class NetworkStateAssertion(BaseMessage):
    message_type: Literal["network_state_assertion"] = "network_state_assertion"
    edge_agent_id: str
    robot_id: str
    mission_id: str
    profile: NetworkProfile
    attached: bool
    latency_ms_p95: float = Field(ge=0)
    packet_loss_pct: float = Field(ge=0, le=100)
    uplink_mbps: float = Field(ge=0)
    observed_at: datetime = Field(default_factory=utc_now)
    measurement_window_seconds: int = Field(gt=0)
    source: str
    signature: str | None = None


class CapabilityRequest(BaseMessage):
    message_type: Literal["capability_request"] = "capability_request"
    requesting_agent_id: str
    authenticated_agent_id: str | None = None
    edge_agent_id: str
    robot_id: str
    mission_id: str
    capability: Capability
    reason: str
    requested_duration_seconds: int = Field(default=600, gt=0)
    request_nonce: str = Field(default_factory=lambda: f"nonce_{uuid4().hex}")
    signature: str | None = None


class LeaseConstraints(BaseModel):
    geofence_id: str | None = None
    max_latency_ms_p95: float | None = Field(default=None, ge=0)
    max_packet_loss_pct: float | None = Field(default=None, ge=0, le=100)
    min_uplink_mbps: float | None = Field(default=None, ge=0)
    fallback_on_degrade: FallbackAction = FallbackAction.LOCAL_AUTONOMY_ONLY
    max_speed_mps: float | None = Field(default=None, ge=0)


class CapabilityLease(BaseModel):
    lease_id: str = Field(default_factory=lambda: f"lease_{uuid4().hex}")
    issuer_id: str
    agent_id: str
    edge_agent_id: str
    robot_id: str
    mission_id: str
    capability: Capability
    constraints: LeaseConstraints
    issued_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime
    nonce: str = Field(default_factory=lambda: f"lease_nonce_{uuid4().hex}")
    signature: str | None = None


class CapabilityDecision(BaseMessage):
    message_type: Literal["capability_decision"] = "capability_decision"
    request_id: str
    decision: Decision
    reason_code: str
    deciding_actor_id: str
    policy_id: str | None = None
    policy_digest: str | None = None
    lease: CapabilityLease | None = None
    safe_alternatives: list[FallbackAction] = Field(default_factory=list)
    audit_id: str
    signature: str | None = None


class LeaseRevocation(BaseMessage):
    message_type: Literal["lease_revocation"] = "lease_revocation"
    lease_id: str
    revoked_by: str
    reason_code: str
    revoked_at: datetime = Field(default_factory=utc_now)
    fallback_action: FallbackAction
    signature: str | None = None


class FallbackDeclaration(BaseMessage):
    message_type: Literal["fallback_declaration"] = "fallback_declaration"
    robot_id: str
    edge_agent_id: str
    mission_id: str
    trigger: str
    fallback_action: FallbackAction
    declared_by: str
    lease_id: str | None = None
    decision_id: str | None = None
    revocation_id: str | None = None
    signature: str | None = None


def stable_json_hash(payload: Any) -> str:
    canonical = json.dumps(
        payload,
        default=str,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class AuditCommit(BaseMessage):
    message_type: Literal["audit_commit"] = "audit_commit"
    audit_id: str = Field(default_factory=lambda: f"audit_{uuid4().hex}")
    event_type: AuditEventType
    actor_id: str
    robot_id: str | None = None
    mission_id: str | None = None
    summary: str
    payload: dict[str, Any] = Field(default_factory=dict)
    payload_hash: str | None = None
    authority_relevant: bool = True
    integrity_profile: str = "local_hash_chain_v0"
    integrity_proof: str | None = None
    previous_audit_hash: str | None = None
    policy_id: str | None = None
    state_refs: list[str] = Field(default_factory=list)
    related_message_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def commit_payload_hash(self) -> "AuditCommit":
        if self.payload_hash is None:
            self.payload_hash = stable_json_hash(self.payload)
        return self


AuditEvent = AuditCommit
