from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from math import isfinite
from numbers import Real

from rclp_core.leases import (
    capability_constraint_bound_violation,
    capability_constraint_requirement_violation,
    lease_matches_context,
    lease_signed_material_too_large,
    lease_time_violation,
    verify_lease_signature,
)
from rclp_core.models import (
    Capability,
    CapabilityConstraintBounds,
    CapabilityConstraintRequirement,
    CapabilityLease,
    NetworkProfile,
    RobotStateAssertion,
    protocol_version_violation,
)
from rclp_core.state import (
    DEFAULT_STATE_MAX_AGE_SECONDS,
    state_auth_violation,
    state_time_violation,
)


DEFAULT_LEASE_MAX_AGE_SECONDS = 600
DEFAULT_LEASE_MAX_TTL_SECONDS = 600
LEASE_CLOCK_SKEW_SECONDS = 30
SUPPORTED_SPEED_PAYLOAD_FIELDS = frozenset({"max_speed_mps", "speed_mps"})


def validate_lease_for_command(
    lease: CapabilityLease | None,
    *,
    issuer_public_key_b64: str | None = None,
    issuer_public_keys_by_id: Mapping[str, str] | None = None,
    trusted_issuer_ids: set[str],
    accepted_capabilities: set[str] | None = None,
    accepted_policy_id: str | None = None,
    accepted_policy_digests: set[str] | None = None,
    issuer_capability_scopes: Mapping[str, set[str]] | None = None,
    capability_constraint_requirements: (
        Mapping[str, CapabilityConstraintRequirement] | None
    ) = None,
    capability_constraint_bounds: Mapping[str, CapabilityConstraintBounds] | None = None,
    agent_id: str,
    edge_agent_id: str,
    robot_id: str,
    mission_id: str,
    capability: str,
    current_state: RobotStateAssertion | None = None,
    state_public_keys_by_edge_id: Mapping[str, str] | None = None,
    command_payload: Mapping[str, object] | None = None,
    revoked_lease_ids: set[str] | None = None,
    max_lease_age_seconds: int = DEFAULT_LEASE_MAX_AGE_SECONDS,
    max_lease_ttl_seconds: int = DEFAULT_LEASE_MAX_TTL_SECONDS,
    max_state_age_seconds: int = DEFAULT_STATE_MAX_AGE_SECONDS,
    now: datetime | None = None,
) -> tuple[bool, str]:
    revoked_lease_ids = revoked_lease_ids or set()
    if lease is None:
        return False, "NO_LEASE"
    if version_reason := protocol_version_violation(lease):
        return False, version_reason
    if lease.issuer_id not in trusted_issuer_ids:
        return False, "ISSUER_NOT_TRUSTED"

    issuer_public_keys = issuer_key_registry(
        trusted_issuer_ids=trusted_issuer_ids,
        issuer_public_key_b64=issuer_public_key_b64,
        issuer_public_keys_by_id=issuer_public_keys_by_id,
    )
    issuer_public_key = issuer_public_keys.get(lease.issuer_id)
    if issuer_public_key is None:
        return False, "ISSUER_KEY_NOT_TRUSTED"
    if lease_signed_material_too_large(lease):
        return False, "LEASE_SIGNED_MATERIAL_TOO_LARGE"
    if not verify_lease_signature(lease, issuer_public_key):
        return False, "INVALID_SIGNATURE"
    if policy_reason := lease_policy_provenance_violation(
        lease,
        accepted_policy_id=accepted_policy_id,
        accepted_policy_digests=accepted_policy_digests,
    ):
        return False, policy_reason
    if scope_reason := capability_scope_violation(
        lease,
        accepted_capabilities=accepted_capabilities,
        issuer_capability_scopes=issuer_capability_scopes,
    ):
        return False, scope_reason

    now = now or datetime.now(timezone.utc)
    if time_reason := lease_time_violation(
        lease,
        at=now,
        max_lease_age_seconds=max_lease_age_seconds,
        max_lease_ttl_seconds=max_lease_ttl_seconds,
        clock_skew_seconds=LEASE_CLOCK_SKEW_SECONDS,
    ):
        return False, time_reason
    if constraint_reason := capability_constraint_requirement_violation(
        lease,
        capability_constraint_requirements,
    ):
        return False, constraint_reason
    if lease_constraints_malformed(lease):
        return False, "LEASE_CONSTRAINT_MALFORMED"
    if constraint_bound_reason := capability_constraint_bound_violation(
        lease,
        capability_constraint_bounds,
    ):
        return False, constraint_bound_reason
    if not lease_matches_context(
        lease,
        agent_id=agent_id,
        edge_agent_id=edge_agent_id,
        robot_id=robot_id,
        mission_id=mission_id,
        capability=capability,
    ):
        return False, "LEASE_CONTEXT_MISMATCH"
    if lease.lease_id in revoked_lease_ids:
        return False, "LEASE_REVOKED"
    if current_state is None:
        if lease_requires_current_state(lease):
            return False, "CURRENT_STATE_REQUIRED"
    else:
        if state_public_keys_by_edge_id is None:
            return False, "STATE_AUTH_REQUIRED"
        if state_auth_reason := state_auth_violation(
            current_state,
            state_public_keys_by_edge_id,
        ):
            return False, state_auth_reason
        if version_reason := protocol_version_violation(current_state):
            return False, version_reason
        if state_reason := state_time_violation(
            current_state,
            now=now,
            max_age_seconds=max_state_age_seconds,
        ):
            return False, state_reason
        ok, reason = validate_lease_against_state(lease, current_state)
        if not ok:
            return ok, reason
    return validate_command_payload_against_constraints(lease, command_payload)


def issuer_key_registry(
    *,
    trusted_issuer_ids: set[str],
    issuer_public_key_b64: str | None,
    issuer_public_keys_by_id: Mapping[str, str] | None,
) -> dict[str, str]:
    if issuer_public_keys_by_id is not None:
        return dict(issuer_public_keys_by_id)
    if issuer_public_key_b64 is not None and len(trusted_issuer_ids) == 1:
        issuer_id = next(iter(trusted_issuer_ids))
        return {issuer_id: issuer_public_key_b64}
    return {}


def capability_scope_violation(
    lease: CapabilityLease,
    *,
    accepted_capabilities: set[str] | None,
    issuer_capability_scopes: Mapping[str, set[str]] | None,
) -> str | None:
    if not accepted_capabilities or issuer_capability_scopes is None:
        return "CAPABILITY_SCOPE_REQUIRED"
    capability = str(lease.capability)
    if capability not in accepted_capabilities:
        return "CAPABILITY_NOT_GRANTED"
    issuer_scope = issuer_capability_scopes.get(lease.issuer_id, set())
    if capability not in issuer_scope:
        return "CAPABILITY_NOT_GRANTED"
    return None


def lease_policy_provenance_violation(
    lease: CapabilityLease,
    *,
    accepted_policy_id: str | None,
    accepted_policy_digests: set[str] | None,
) -> str | None:
    if not accepted_policy_id or not accepted_policy_id.strip() or not accepted_policy_digests:
        return "POLICY_PROVENANCE_REQUIRED"
    normalized_digests = {digest for digest in accepted_policy_digests if digest.strip()}
    if len(normalized_digests) != len(accepted_policy_digests):
        return "POLICY_PROVENANCE_REQUIRED"
    if not lease.policy_id or not lease.policy_id.strip():
        return "LEASE_POLICY_PROVENANCE_REQUIRED"
    if not lease.policy_digest or not lease.policy_digest.strip():
        return "LEASE_POLICY_PROVENANCE_REQUIRED"
    if lease.policy_id != accepted_policy_id or lease.policy_digest not in normalized_digests:
        return "LEASE_POLICY_NOT_ACCEPTED"
    return None


def lease_requires_current_state(lease: CapabilityLease) -> bool:
    if lease.capability == Capability.REMOTE_ASSIST:
        return True
    constraints = lease.constraints
    return any(
        value is not None
        for value in [
            constraints.geofence_id,
            constraints.max_latency_ms_p95,
            constraints.max_packet_loss_pct,
            constraints.min_uplink_mbps,
        ]
    )


def _finite_nonnegative_number(value: object, *, max_value: float | None = None) -> bool:
    if isinstance(value, bool) or not isinstance(value, Real):
        return False
    numeric = float(value)
    if not isfinite(numeric) or numeric < 0:
        return False
    return max_value is None or numeric <= max_value


def lease_constraints_malformed(lease: CapabilityLease) -> bool:
    constraints = lease.constraints
    return not (
        (
            constraints.max_latency_ms_p95 is None
            or _finite_nonnegative_number(constraints.max_latency_ms_p95)
        )
        and (
            constraints.max_packet_loss_pct is None
            or _finite_nonnegative_number(constraints.max_packet_loss_pct, max_value=100)
        )
        and (
            constraints.min_uplink_mbps is None
            or _finite_nonnegative_number(constraints.min_uplink_mbps)
        )
        and (
            constraints.max_speed_mps is None
            or _finite_nonnegative_number(constraints.max_speed_mps)
        )
    )


def network_state_malformed(state: RobotStateAssertion) -> bool:
    network = state.network_state
    return not (
        _finite_nonnegative_number(network.latency_ms_p95)
        and _finite_nonnegative_number(network.packet_loss_pct, max_value=100)
        and _finite_nonnegative_number(network.uplink_mbps)
    )


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
    if network_state_malformed(state):
        return False, "NETWORK_STATE_MALFORMED"
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


def validate_command_payload_against_constraints(
    lease: CapabilityLease,
    command_payload: Mapping[str, object] | None,
) -> tuple[bool, str]:
    if command_payload is None:
        return False, "COMMAND_PAYLOAD_SCHEMA_VIOLATION"
    if set(command_payload) - SUPPORTED_SPEED_PAYLOAD_FIELDS:
        return False, "COMMAND_PAYLOAD_SCHEMA_VIOLATION"
    max_speed_mps = lease.constraints.max_speed_mps
    if max_speed_mps is None:
        if command_payload:
            return False, "COMMAND_PAYLOAD_SCHEMA_VIOLATION"
        return True, "LEASE_VALID"
    if not _finite_nonnegative_number(max_speed_mps):
        return False, "LEASE_CONSTRAINT_MALFORMED"
    has_max_speed = "max_speed_mps" in command_payload
    has_speed = "speed_mps" in command_payload
    if has_max_speed and has_speed:
        max_speed_raw = command_payload["max_speed_mps"]
        speed_raw = command_payload["speed_mps"]
        if max_speed_raw != speed_raw:
            return False, "COMMAND_SPEED_CONFLICT"
    raw_speed = command_payload.get("max_speed_mps", command_payload.get("speed_mps"))
    if raw_speed is None:
        return False, "COMMAND_SPEED_MISSING"
    if isinstance(raw_speed, bool) or not isinstance(raw_speed, Real):
        return False, "COMMAND_SPEED_MALFORMED"
    speed_mps = float(raw_speed)
    if not isfinite(speed_mps) or speed_mps < 0:
        return False, "COMMAND_SPEED_MALFORMED"
    if speed_mps > max_speed_mps:
        return False, "COMMAND_SPEED_TOO_HIGH"
    return True, "LEASE_VALID"
