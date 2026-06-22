from __future__ import annotations

from datetime import datetime, timedelta, timezone

from rclp_core.leases import (
    is_expired,
    is_not_yet_valid,
    lease_matches_context,
    required_constraints_missing,
    verify_lease_signature,
)
from rclp_core.models import CapabilityLease, NetworkProfile, RobotStateAssertion


DEFAULT_LEASE_MAX_AGE_SECONDS = 600
DEFAULT_LEASE_MAX_TTL_SECONDS = 600
LEASE_CLOCK_SKEW_SECONDS = 30


def validate_lease_for_command(
    lease: CapabilityLease | None,
    *,
    issuer_public_key_b64: str,
    trusted_issuer_ids: set[str],
    agent_id: str,
    edge_agent_id: str,
    robot_id: str,
    mission_id: str,
    capability: str,
    current_state: RobotStateAssertion | None = None,
    revoked_lease_ids: set[str] | None = None,
    max_lease_age_seconds: int = DEFAULT_LEASE_MAX_AGE_SECONDS,
    max_lease_ttl_seconds: int = DEFAULT_LEASE_MAX_TTL_SECONDS,
    now: datetime | None = None,
) -> tuple[bool, str]:
    revoked_lease_ids = revoked_lease_ids or set()
    if lease is None:
        return False, "NO_LEASE"
    if lease.lease_id in revoked_lease_ids:
        return False, "LEASE_REVOKED"
    if lease.issuer_id not in trusted_issuer_ids:
        return False, "ISSUER_NOT_TRUSTED"
    if not verify_lease_signature(lease, issuer_public_key_b64):
        return False, "INVALID_SIGNATURE"
    now = now or datetime.now(timezone.utc)
    if is_not_yet_valid(lease, now):
        return False, "LEASE_NOT_YET_VALID"
    if is_expired(lease, now):
        return False, "LEASE_EXPIRED"
    lease_ttl = lease.expires_at - lease.issued_at
    if lease_ttl > timedelta(seconds=max_lease_ttl_seconds + LEASE_CLOCK_SKEW_SECONDS):
        return False, "LEASE_TTL_TOO_LONG"
    lease_age = now - lease.issued_at
    if lease_age > timedelta(seconds=max_lease_age_seconds + LEASE_CLOCK_SKEW_SECONDS):
        return False, "LEASE_STALE"
    if required_constraints_missing(lease):
        return False, "LEASE_CONSTRAINTS_MISSING"
    if not lease_matches_context(
        lease,
        agent_id=agent_id,
        edge_agent_id=edge_agent_id,
        robot_id=robot_id,
        mission_id=mission_id,
        capability=capability,
    ):
        return False, "LEASE_CONTEXT_MISMATCH"
    if current_state is not None:
        return validate_lease_against_state(lease, current_state)
    return True, "LEASE_VALID"


def validate_lease_against_state(
    lease: CapabilityLease,
    state: RobotStateAssertion,
) -> tuple[bool, str]:
    if (
        state.robot_id != lease.robot_id
        or state.edge_agent_id != lease.edge_agent_id
        or state.mission_id != lease.mission_id
    ):
        return False, "LEASE_STATE_MISMATCH"

    constraints = lease.constraints
    if constraints.geofence_id is not None:
        if not state.geofence_state.inside:
            return False, "GEOFENCE_CONSTRAINT_VIOLATED"
        if state.geofence_state.geofence_id != constraints.geofence_id:
            return False, "GEOFENCE_CONSTRAINT_VIOLATED"

    network = state.network_state
    if network.profile == NetworkProfile.UNKNOWN:
        return False, "NETWORK_STATE_UNKNOWN"
    if not network.attached:
        return False, "NETWORK_DETACHED"
    if (
        constraints.max_latency_ms_p95 is not None
        and network.latency_ms_p95 > constraints.max_latency_ms_p95
    ):
        return False, "NETWORK_LATENCY_TOO_HIGH"
    if (
        constraints.max_packet_loss_pct is not None
        and network.packet_loss_pct > constraints.max_packet_loss_pct
    ):
        return False, "NETWORK_PACKET_LOSS_TOO_HIGH"
    if (
        constraints.min_uplink_mbps is not None
        and network.uplink_mbps < constraints.min_uplink_mbps
    ):
        return False, "NETWORK_UPLINK_TOO_LOW"

    return True, "LEASE_VALID"
