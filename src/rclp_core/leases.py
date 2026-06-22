from __future__ import annotations

from datetime import datetime, timedelta, timezone

from rclp_core.crypto import DemoKeyPair, verify_with_public_key_b64
from rclp_core.models import Capability, CapabilityLease, CapabilityRequest, LeaseConstraints


def issue_lease(
    request: CapabilityRequest,
    constraints: LeaseConstraints,
    issuer_id: str,
    issuer_key: DemoKeyPair,
    ttl_seconds: int,
) -> CapabilityLease:
    if ttl_seconds <= 0:
        raise ValueError("lease ttl must be positive")
    if ttl_seconds > request.requested_duration_seconds:
        raise ValueError("lease ttl cannot exceed requested duration")

    now = datetime.now(timezone.utc)
    lease = CapabilityLease(
        issuer_id=issuer_id,
        agent_id=request.requesting_agent_id,
        edge_agent_id=request.edge_agent_id,
        robot_id=request.robot_id,
        mission_id=request.mission_id,
        capability=request.capability,
        constraints=constraints,
        issued_at=now,
        expires_at=now + timedelta(seconds=ttl_seconds),
    )
    lease.signature = issuer_key.sign(lease)
    return lease


def is_expired(lease: CapabilityLease, at: datetime | None = None) -> bool:
    at = at or datetime.now(timezone.utc)
    return at >= lease.expires_at


def is_not_yet_valid(lease: CapabilityLease, at: datetime | None = None) -> bool:
    at = at or datetime.now(timezone.utc)
    return at < lease.issued_at


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


def required_constraints_missing(lease: CapabilityLease) -> bool:
    if lease.capability != Capability.REMOTE_ASSIST:
        return False

    constraints = lease.constraints
    return (
        constraints.geofence_id is None
        or constraints.max_latency_ms_p95 is None
        or constraints.max_packet_loss_pct is None
        or constraints.min_uplink_mbps is None
    )
