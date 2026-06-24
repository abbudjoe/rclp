from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from rclp_core.crypto import DemoKeyPair, verify_with_public_key_b64
from rclp_core.models import (
    CapabilityConstraintRequirement,
    CapabilityLease,
    CapabilityRequest,
    LeaseConstraints,
    SUPPORTED_PROTOCOL_VERSION,
)


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
        policy_id=policy_id,
        policy_digest=policy_digest,
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
    if lease_ttl > timedelta(seconds=max_lease_ttl_seconds) + skew:
        return "LEASE_TTL_TOO_LONG"
    lease_age = at - lease.issued_at
    if lease_age > timedelta(seconds=max_lease_age_seconds) + skew:
        return "LEASE_STALE"
    return None


def verify_lease_signature(lease: CapabilityLease, issuer_public_key_b64: str) -> bool:
    if not lease.signature:
        return False
    return verify_with_public_key_b64(lease, lease.signature, issuer_public_key_b64)


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
