from __future__ import annotations

from collections.abc import Collection, Mapping
from datetime import datetime, timedelta, timezone

from rclp_core.crypto import verify_with_public_key_b64
from rclp_core.models import (
    ControlPlaneReachabilityAssertion,
    NetworkProfile,
    NetworkState,
    RobotStateAssertion,
    signature_algorithm_violation,
)


DEFAULT_STATE_MAX_AGE_SECONDS = 30
STATE_CLOCK_SKEW_SECONDS = 30
ROBOT_STATE_REQUIRED_WIRE_FIELDS = frozenset({"safety_state"})
NETWORK_STATE_REQUIRED_WIRE_FIELDS = frozenset({"attached"})
CONTROL_PLANE_REACHABILITY_REQUIRED_WIRE_FIELDS = frozenset({"reachable"})
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


def robot_state_signed_material_too_large(state: RobotStateAssertion) -> bool:
    text_budget = _SignedTextBudget()
    network_state = state.network_state
    geofence_state = state.geofence_state
    for value in (
        state.protocol_version,
        state.message_id,
        state.correlation_id,
        state.created_at.isoformat(),
        state.message_type,
        state.robot_id,
        state.edge_agent_id,
        state.authenticated_edge_agent_id,
        state.mission_id,
        state.safety_state,
        network_state.profile,
        network_state.attached,
        network_state.latency_ms_p95,
        network_state.packet_loss_pct,
        network_state.uplink_mbps,
        network_state.observed_at.isoformat(),
        geofence_state.geofence_id,
        geofence_state.inside,
        geofence_state.verified_at.isoformat(),
        state.observed_at.isoformat(),
        state.human_operator_available,
        state.signature_alg,
        state.signature,
    ):
        if text_budget.exceeded(value):
            return True
    return False


def control_plane_reachability_signed_material_too_large(
    assertion: ControlPlaneReachabilityAssertion,
) -> bool:
    text_budget = _SignedTextBudget()
    for value in (
        assertion.protocol_version,
        assertion.message_id,
        assertion.correlation_id,
        assertion.created_at.isoformat(),
        assertion.message_type,
        assertion.edge_agent_id,
        assertion.authenticated_edge_agent_id,
        assertion.robot_id,
        assertion.mission_id,
        assertion.reachability,
        assertion.reachable,
        assertion.observed_at.isoformat(),
        assertion.measurement_window_seconds,
        assertion.source,
        assertion.signature_alg,
        assertion.signature,
    ):
        if text_budget.exceeded(value):
            return True
    return False


def network_state_required_fields_missing(network: NetworkState) -> bool:
    return not NETWORK_STATE_REQUIRED_WIRE_FIELDS.issubset(network.model_fields_set)


def network_state_authority_violation(network: NetworkState) -> str | None:
    if network.profile == NetworkProfile.UNKNOWN:
        return "NETWORK_STATE_UNKNOWN"
    if network.profile == NetworkProfile.PARTITION:
        return "NETWORK_DETACHED"
    if not network.attached:
        return "NETWORK_DETACHED"
    return None


def state_time_violation(
    state: RobotStateAssertion,
    *,
    now: datetime | None = None,
    max_age_seconds: int = DEFAULT_STATE_MAX_AGE_SECONDS,
) -> str | None:
    """Return a fail-closed reason when a state assertion is stale or from the future."""

    now = now or datetime.now(timezone.utc)
    for timestamp in [
        state.created_at,
        state.observed_at,
        state.network_state.observed_at,
        state.geofence_state.verified_at,
    ]:
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            return "STATE_TIMESTAMP_INVALID"
        if timestamp > now + timedelta(seconds=STATE_CLOCK_SKEW_SECONDS):
            return "STATE_NOT_YET_VALID"
        if now - timestamp > timedelta(seconds=max_age_seconds + STATE_CLOCK_SKEW_SECONDS):
            return "STATE_STALE"
    return None


def control_plane_reachability_time_violation(
    assertion: ControlPlaneReachabilityAssertion,
    *,
    now: datetime | None = None,
    max_age_seconds: int = DEFAULT_STATE_MAX_AGE_SECONDS,
) -> str | None:
    now = now or datetime.now(timezone.utc)
    for timestamp in [
        assertion.created_at,
        assertion.observed_at,
    ]:
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            return "CONTROL_PLANE_TIMESTAMP_INVALID"
        if timestamp > now + timedelta(seconds=STATE_CLOCK_SKEW_SECONDS):
            return "CONTROL_PLANE_NOT_YET_VALID"
        if now - timestamp > timedelta(seconds=max_age_seconds + STATE_CLOCK_SKEW_SECONDS):
            return "CONTROL_PLANE_STATE_STALE"
    return None


def state_auth_violation(
    state: RobotStateAssertion,
    edge_public_keys_by_id: Mapping[str, str],
    *,
    required_wire_fields: Collection[str] = ROBOT_STATE_REQUIRED_WIRE_FIELDS,
) -> str | None:
    if not set(required_wire_fields).issubset(state.model_fields_set):
        return "STATE_REQUIRED_FIELD_MISSING"
    if network_state_required_fields_missing(state.network_state):
        return "STATE_REQUIRED_FIELD_MISSING"
    if alg_reason := signature_algorithm_violation(
        state,
        missing_reason="STATE_SIGNATURE_ALGORITHM_MISSING",
        unsupported_reason="STATE_SIGNATURE_ALGORITHM_UNSUPPORTED",
    ):
        return alg_reason
    if state.authenticated_edge_agent_id is None:
        return "STATE_AUTHENTICATED_EDGE_MISSING"
    if state.authenticated_edge_agent_id != state.edge_agent_id:
        return "STATE_AUTHENTICATED_EDGE_MISMATCH"
    if state.signature is None:
        return "STATE_SIGNATURE_MISSING"
    public_key = edge_public_keys_by_id.get(state.authenticated_edge_agent_id)
    if public_key is None:
        return "EDGE_STATE_KEY_NOT_TRUSTED"
    if robot_state_signed_material_too_large(state):
        return "STATE_SIGNED_MATERIAL_TOO_LARGE"
    if not verify_with_public_key_b64(state, state.signature, public_key):
        return "STATE_SIGNATURE_INVALID"
    return None


def control_plane_reachability_auth_violation(
    assertion: ControlPlaneReachabilityAssertion,
    edge_public_keys_by_id: Mapping[str, str],
    *,
    required_wire_fields: Collection[str] = CONTROL_PLANE_REACHABILITY_REQUIRED_WIRE_FIELDS,
) -> str | None:
    if not set(required_wire_fields).issubset(assertion.model_fields_set):
        return "CONTROL_PLANE_REQUIRED_FIELD_MISSING"
    if alg_reason := signature_algorithm_violation(
        assertion,
        missing_reason="CONTROL_PLANE_SIGNATURE_ALGORITHM_MISSING",
        unsupported_reason="CONTROL_PLANE_SIGNATURE_ALGORITHM_UNSUPPORTED",
    ):
        return alg_reason
    if assertion.authenticated_edge_agent_id is None:
        return "CONTROL_PLANE_AUTHENTICATED_EDGE_MISSING"
    if assertion.authenticated_edge_agent_id != assertion.edge_agent_id:
        return "CONTROL_PLANE_AUTHENTICATED_EDGE_MISMATCH"
    if assertion.signature is None:
        return "CONTROL_PLANE_SIGNATURE_MISSING"
    public_key = edge_public_keys_by_id.get(assertion.authenticated_edge_agent_id)
    if public_key is None:
        return "CONTROL_PLANE_KEY_NOT_TRUSTED"
    if control_plane_reachability_signed_material_too_large(assertion):
        return "CONTROL_PLANE_SIGNED_MATERIAL_TOO_LARGE"
    if not verify_with_public_key_b64(assertion, assertion.signature, public_key):
        return "CONTROL_PLANE_SIGNATURE_INVALID"
    return None
