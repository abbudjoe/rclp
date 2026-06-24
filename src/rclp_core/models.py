from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from enum import StrEnum
from numbers import Real
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


SUPPORTED_PROTOCOL_VERSION = "0.0.1-draft"
STRICT_MODEL_CONFIG = ConfigDict(extra="forbid")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _reject_coerced_bool(value: Any) -> Any:
    if not isinstance(value, bool):
        raise ValueError("authority boolean fields must be JSON booleans")
    return value


def _reject_coerced_int(value: Any) -> Any:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("authority integer fields must be JSON integers")
    return value


def _reject_coerced_number(value: Any) -> Any:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError("authority numeric fields must be JSON numbers")
    return value


def _reject_coerced_optional_number(value: Any) -> Any:
    if value is None:
        return value
    return _reject_coerced_number(value)


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


class StrictModel(BaseModel):
    model_config = STRICT_MODEL_CONFIG


class BaseMessage(BaseModel):
    model_config = STRICT_MODEL_CONFIG

    protocol_version: str = SUPPORTED_PROTOCOL_VERSION
    message_id: str = Field(default_factory=lambda: f"msg_{uuid4().hex}")
    correlation_id: str = Field(default_factory=lambda: f"corr_{uuid4().hex}")
    created_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def validate_protocol_version(self) -> "BaseMessage":
        if self.protocol_version != SUPPORTED_PROTOCOL_VERSION:
            raise ValueError(f"unsupported protocol_version: {self.protocol_version}")
        return self


def protocol_version_violation(*messages: BaseMessage) -> str | None:
    for message in messages:
        if message.protocol_version != SUPPORTED_PROTOCOL_VERSION:
            return "PROTOCOL_VERSION_UNSUPPORTED"
    return None


class AgentAttestation(BaseMessage):
    message_type: Literal["agent_attestation"] = "agent_attestation"
    agent_id: str
    authenticated_agent_id: str | None = None
    kind: Literal["central_agent", "edge_agent", "human_operator", "service"]
    manifest_digest: str
    public_key_id: str
    trust_tier: Literal["development", "staging", "production"] = "development"
    revoked: bool = False
    signature: str | None = None

    _validate_revoked_bool = field_validator("revoked", mode="before")(_reject_coerced_bool)


AgentIdentity = AgentAttestation


class RobotIdentity(StrictModel):
    robot_id: str
    hardware_id: str
    edge_agent_id: str


class MissionContext(StrictModel):
    mission_id: str
    mission_type: str = "demo"
    human_operator_available: bool = False

    _validate_human_operator_available_bool = field_validator(
        "human_operator_available",
        mode="before",
    )(_reject_coerced_bool)


class NetworkState(StrictModel):
    profile: NetworkProfile = NetworkProfile.UNKNOWN
    attached: bool = True
    latency_ms_p95: float = Field(ge=0, allow_inf_nan=False)
    packet_loss_pct: float = Field(ge=0, le=100, allow_inf_nan=False)
    uplink_mbps: float = Field(ge=0, allow_inf_nan=False)
    observed_at: datetime = Field(default_factory=utc_now)

    _validate_attached_bool = field_validator("attached", mode="before")(_reject_coerced_bool)
    _validate_network_numbers = field_validator(
        "latency_ms_p95",
        "packet_loss_pct",
        "uplink_mbps",
        mode="before",
    )(_reject_coerced_number)


class GeofenceState(StrictModel):
    geofence_id: str
    inside: bool
    verified_at: datetime = Field(default_factory=utc_now)

    _validate_inside_bool = field_validator("inside", mode="before")(_reject_coerced_bool)


class RobotStateAssertion(BaseMessage):
    message_type: Literal["robot_state_assertion"] = "robot_state_assertion"
    robot_id: str
    edge_agent_id: str
    authenticated_edge_agent_id: str | None = None
    mission_id: str
    safety_state: SafetyState = SafetyState.NOMINAL
    network_state: NetworkState
    geofence_state: GeofenceState
    observed_at: datetime = Field(default_factory=utc_now)
    human_operator_available: bool = True
    signature: str | None = None

    _validate_human_operator_available_bool = field_validator(
        "human_operator_available",
        mode="before",
    )(_reject_coerced_bool)


class NetworkStateAssertion(BaseMessage):
    message_type: Literal["network_state_assertion"] = "network_state_assertion"
    edge_agent_id: str
    robot_id: str
    mission_id: str
    profile: NetworkProfile
    attached: bool
    latency_ms_p95: float = Field(ge=0, allow_inf_nan=False)
    packet_loss_pct: float = Field(ge=0, le=100, allow_inf_nan=False)
    uplink_mbps: float = Field(ge=0, allow_inf_nan=False)
    observed_at: datetime = Field(default_factory=utc_now)
    measurement_window_seconds: int = Field(gt=0)
    source: str
    signature: str | None = None

    _validate_attached_bool = field_validator("attached", mode="before")(_reject_coerced_bool)
    _validate_network_numbers = field_validator(
        "latency_ms_p95",
        "packet_loss_pct",
        "uplink_mbps",
        mode="before",
    )(_reject_coerced_number)
    _validate_measurement_window_seconds_int = field_validator(
        "measurement_window_seconds",
        mode="before",
    )(_reject_coerced_int)


class LeaseConstraints(StrictModel):
    geofence_id: str | None = None
    max_latency_ms_p95: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    max_packet_loss_pct: float | None = Field(default=None, ge=0, le=100, allow_inf_nan=False)
    min_uplink_mbps: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    fallback_on_degrade: FallbackAction = FallbackAction.LOCAL_AUTONOMY_ONLY
    max_speed_mps: float | None = Field(default=None, ge=0, allow_inf_nan=False)

    _validate_constraint_numbers = field_validator(
        "max_latency_ms_p95",
        "max_packet_loss_pct",
        "min_uplink_mbps",
        "max_speed_mps",
        mode="before",
    )(_reject_coerced_optional_number)


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
    requested_constraints: LeaseConstraints | None = None
    request_nonce: str = Field(default_factory=lambda: f"nonce_{uuid4().hex}")
    signature: str | None = None

    _validate_requested_duration_seconds_int = field_validator(
        "requested_duration_seconds",
        mode="before",
    )(_reject_coerced_int)


class CapabilityConstraintRequirement(StrictModel):
    capability: Capability
    require_geofence_id: bool = False
    require_network_thresholds: bool = False
    require_fallback_on_degrade: bool = False
    require_max_speed_mps: bool = False

    _validate_requirement_bools = field_validator(
        "require_geofence_id",
        "require_network_thresholds",
        "require_fallback_on_degrade",
        "require_max_speed_mps",
        mode="before",
    )(_reject_coerced_bool)


class CapabilityConstraintBounds(StrictModel):
    capability: Capability
    geofence_id: str | None = None
    max_latency_ms_p95: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    max_packet_loss_pct: float | None = Field(default=None, ge=0, le=100, allow_inf_nan=False)
    min_uplink_mbps: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    fallback_on_degrade: FallbackAction | None = None
    max_speed_mps: float | None = Field(default=None, ge=0, allow_inf_nan=False)

    _validate_bound_numbers = field_validator(
        "max_latency_ms_p95",
        "max_packet_loss_pct",
        "min_uplink_mbps",
        "max_speed_mps",
        mode="before",
    )(_reject_coerced_optional_number)


class CapabilityLease(BaseMessage):
    protocol_version: str
    message_id: str
    correlation_id: str
    created_at: datetime
    message_type: Literal["capability_lease"]
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
    policy_id: str
    policy_digest: str
    signature: str | None = None

    @model_validator(mode="after")
    def validate_time_window(self) -> "CapabilityLease":
        if not self.policy_id.strip() or not self.policy_digest.strip():
            raise ValueError("lease policy provenance must be non-empty")
        for value in (self.issued_at, self.expires_at):
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError("lease timestamps must be timezone-aware")
        if self.expires_at <= self.issued_at:
            raise ValueError("lease expires_at must be after issued_at")
        return self


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
    edge_agent_id: str
    reason_code: str
    revoked_at: datetime = Field(default_factory=utc_now)
    fallback_action: FallbackAction
    robot_id: str | None = None
    mission_id: str | None = None
    capability: Capability | None = None
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
    policy_digest: str | None = None
    state_refs: list[str] = Field(default_factory=list)
    related_message_ids: list[str] = Field(default_factory=list)

    _validate_authority_relevant_bool = field_validator(
        "authority_relevant",
        mode="before",
    )(_reject_coerced_bool)

    @model_validator(mode="after")
    def commit_payload_hash(self) -> "AuditCommit":
        if self.payload_hash is None:
            self.payload_hash = stable_json_hash(self.payload)
        return self


AuditEvent = AuditCommit
