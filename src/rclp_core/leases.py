from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from rclp_core.crypto import DemoKeyPair, verify_with_public_key_b64
from rclp_core.models import (
    CapabilityConstraintRequirement,
    CapabilityConstraintBounds,
    CapabilityLease,
    CapabilityRequest,
    ED25519_SIGNATURE_ALGORITHM,
    LeaseConstraints,
    SUPPORTED_PROTOCOL_VERSION,
    signature_algorithm_violation,
)


ED25519_SIGNATURE_BYTES = 64
ED25519_SIGNATURE_B64_MAX_TEXT_BYTES = 4 * ((ED25519_SIGNATURE_BYTES + 2) // 3)
MAX_SIGNED_TEXT_FIELD_BYTES = 1_024
MAX_SIGNED_TEXT_TOTAL_BYTES = 16_384


class _SignedTextBudget:
    def __init__(self) -> None:
        self.total_bytes = 0

    def exceeded(self, value: object | None) -> bool:
        if value is None:
            return False
        size = len(str(value).encode("utf-8"))
        self.total_bytes += size
        return size > MAX_SIGNED_TEXT_FIELD_BYTES or self.total_bytes > MAX_SIGNED_TEXT_TOTAL_BYTES


def _timestamp_is_naive(value: datetime) -> bool:
    return value.tzinfo is None or value.utcoffset() is None


def issue_lease(
    request: CapabilityRequest,
    constraints: LeaseConstraints,
    issuer_id: str,
    issuer_key: DemoKeyPair,
    ttl_seconds: int,
    *,
    policy_id: str,
    policy_digest: str,
) -> CapabilityLease:
    if ttl_seconds <= 0:
        raise ValueError("lease ttl must be positive")
    if ttl_seconds > request.requested_duration_seconds:
        raise ValueError("lease ttl cannot exceed requested duration")
    if not policy_id.strip() or not policy_digest.strip():
        raise ValueError("lease policy provenance is required")

    now = datetime.now(timezone.utc)
    lease = CapabilityLease(
        protocol_version=SUPPORTED_PROTOCOL_VERSION,
        message_id=f"msg_{uuid4().hex}",
        correlation_id=request.correlation_id,
        created_at=now,
        message_type="capability_lease",
        issuer_id=issuer_id,
        agent_id=request.requesting_agent_id,
        edge_agent_id=request.edge_agent_id,
        robot_id=request.robot_id,
        mission_id=request.mission_id,
        capability=request.capability,
        constraints=constraints,
        issued_at=now,
        expires_at=now + timedelta(seconds=ttl_seconds),
        nonce=f"lease_nonce_{uuid4().hex}",
        policy_id=policy_id,
        policy_digest=policy_digest,
        signature_alg=ED25519_SIGNATURE_ALGORITHM,
    )
    lease.signature = issuer_key.sign(lease)
    return lease


def is_expired(lease: CapabilityLease, at: datetime | None = None) -> bool:
    at = at or datetime.now(timezone.utc)
    return at >= lease.expires_at


def is_not_yet_valid(lease: CapabilityLease, at: datetime | None = None) -> bool:
    at = at or datetime.now(timezone.utc)
    return at < lease.issued_at


def lease_time_violation(
    lease: CapabilityLease,
    *,
    at: datetime,
    max_lease_age_seconds: int,
    max_lease_ttl_seconds: int,
    clock_skew_seconds: int,
) -> str | None:
    if (
        _timestamp_is_naive(at)
        or _timestamp_is_naive(lease.issued_at)
        or _timestamp_is_naive(lease.expires_at)
    ):
        return "LEASE_TIMESTAMP_INVALID"
    skew = timedelta(seconds=clock_skew_seconds)
    try:
        latest_accepted_issued_at = at + skew
    except OverflowError:
        return "LEASE_TIMESTAMP_INVALID"
    if lease.issued_at > latest_accepted_issued_at:
        return "LEASE_NOT_YET_VALID"
    if at >= lease.expires_at:
        return "LEASE_EXPIRED"
    if lease.expires_at <= lease.issued_at:
        return "LEASE_TIME_WINDOW_INVALID"
    lease_ttl = lease.expires_at - lease.issued_at
    if lease_ttl > timedelta(seconds=max_lease_ttl_seconds):
        return "LEASE_TTL_TOO_LONG"
    lease_age = at - lease.issued_at
    if lease_age > timedelta(seconds=max_lease_age_seconds) + skew:
        return "LEASE_STALE"
    return None


def verify_lease_signature(lease: CapabilityLease, issuer_public_key_b64: str) -> bool:
    if not lease.signature:
        return False
    return verify_with_public_key_b64(lease, lease.signature, issuer_public_key_b64)


def lease_signature_algorithm_violation(lease: CapabilityLease) -> str | None:
    return signature_algorithm_violation(
        lease,
        missing_reason="LEASE_SIGNATURE_ALGORITHM_MISSING",
        unsupported_reason="LEASE_SIGNATURE_ALGORITHM_UNSUPPORTED",
    )


def lease_signature_material_too_large(lease: CapabilityLease) -> bool:
    if lease.signature is None:
        return False
    return len(lease.signature.encode("utf-8")) > ED25519_SIGNATURE_B64_MAX_TEXT_BYTES


def lease_signed_material_too_large(lease: CapabilityLease) -> bool:
    if lease_signature_material_too_large(lease):
        return True

    text_budget = _SignedTextBudget()
    constraints = lease.constraints
    for value in (
        lease.protocol_version,
        lease.message_id,
        lease.correlation_id,
        lease.created_at.isoformat(),
        lease.message_type,
        lease.lease_id,
        lease.issuer_id,
        lease.agent_id,
        lease.edge_agent_id,
        lease.robot_id,
        lease.mission_id,
        lease.capability,
        constraints.geofence_id,
        constraints.max_latency_ms_p95,
        constraints.max_packet_loss_pct,
        constraints.min_uplink_mbps,
        constraints.fallback_on_degrade,
        constraints.max_speed_mps,
        lease.issued_at.isoformat(),
        lease.expires_at.isoformat(),
        lease.nonce,
        lease.policy_id,
        lease.policy_digest,
        lease.signature_alg,
        lease.signature,
    ):
        if text_budget.exceeded(value):
            return True
    return False


def lease_matches_context(
    lease: CapabilityLease,
    *,
    agent_id: str,
    edge_agent_id: str,
    robot_id: str,
    mission_id: str,
    capability: str,
) -> bool:
    return (
        lease.agent_id == agent_id
        and lease.edge_agent_id == edge_agent_id
        and lease.robot_id == robot_id
        and lease.mission_id == mission_id
        and str(lease.capability) == str(capability)
    )


def capability_constraint_requirement_violation(
    lease: CapabilityLease,
    capability_constraint_requirements: Mapping[str, CapabilityConstraintRequirement] | None,
) -> str | None:
    if capability_constraint_requirements is None:
        return "CAPABILITY_CONSTRAINT_REQUIREMENTS_REQUIRED"
    requirement = capability_constraint_requirements.get(str(lease.capability))
    if requirement is None or str(requirement.capability) != str(lease.capability):
        return "CAPABILITY_CONSTRAINT_REQUIREMENTS_REQUIRED"
    if capability_constraints_missing(lease.constraints, requirement):
        return "LEASE_CONSTRAINTS_MISSING"
    return None


def capability_constraint_bound_violation(
    lease: CapabilityLease,
    capability_constraint_bounds: Mapping[str, CapabilityConstraintBounds] | None,
) -> str | None:
    if capability_constraint_bounds is None:
        return "CAPABILITY_CONSTRAINT_BOUNDS_REQUIRED"
    bounds = capability_constraint_bounds.get(str(lease.capability))
    if bounds is None or str(bounds.capability) != str(lease.capability):
        return "CAPABILITY_CONSTRAINT_BOUNDS_REQUIRED"
    if capability_constraints_exceed_bounds(lease.constraints, bounds):
        return "LEASE_CONSTRAINTS_EXCEED_POLICY"
    return None


def required_constraints_missing(
    lease: CapabilityLease,
    capability_constraint_requirements: Mapping[str, CapabilityConstraintRequirement] | None,
) -> bool:
    return (
        capability_constraint_requirement_violation(
            lease,
            capability_constraint_requirements,
        )
        == "LEASE_CONSTRAINTS_MISSING"
    )


def capability_constraints_missing(
    constraints: LeaseConstraints,
    requirement: CapabilityConstraintRequirement,
) -> bool:
    return (
        (requirement.require_geofence_id and constraints.geofence_id is None)
        or (
            requirement.require_network_thresholds
            and (
                constraints.max_latency_ms_p95 is None
                or constraints.max_packet_loss_pct is None
                or constraints.min_uplink_mbps is None
            )
        )
        or (
            requirement.require_fallback_on_degrade
            and (
                "fallback_on_degrade" not in constraints.model_fields_set
                or not str(constraints.fallback_on_degrade).strip()
            )
        )
        or (requirement.require_max_speed_mps and constraints.max_speed_mps is None)
    )


def capability_constraints_exceed_bounds(
    constraints: LeaseConstraints,
    bounds: CapabilityConstraintBounds,
) -> bool:
    if bounds.geofence_id is not None and constraints.geofence_id != bounds.geofence_id:
        return True
    return (
        _max_field_exceeds_policy(
            constraints.max_latency_ms_p95,
            bounds.max_latency_ms_p95,
        )
        or _max_field_exceeds_policy(
            constraints.max_packet_loss_pct,
            bounds.max_packet_loss_pct,
        )
        or _min_field_exceeds_policy(
            constraints.min_uplink_mbps,
            bounds.min_uplink_mbps,
        )
        or _max_field_exceeds_policy(
            constraints.max_speed_mps,
            bounds.max_speed_mps,
        )
        or _fallback_exceeds_policy(constraints, bounds)
    )


def _max_field_exceeds_policy(value: float | None, bound: float | None) -> bool:
    if value is None:
        return False
    return bound is None or value > bound


def _min_field_exceeds_policy(value: float | None, bound: float | None) -> bool:
    if value is None:
        return False
    return bound is None or value < bound


def _fallback_exceeds_policy(
    constraints: LeaseConstraints,
    bounds: CapabilityConstraintBounds,
) -> bool:
    if bounds.fallback_on_degrade is None:
        return "fallback_on_degrade" in constraints.model_fields_set
    return constraints.fallback_on_degrade != bounds.fallback_on_degrade
