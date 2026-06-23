from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta, timezone

from rclp_core.crypto import verify_with_public_key_b64
from rclp_core.models import RobotStateAssertion


DEFAULT_STATE_MAX_AGE_SECONDS = 30
STATE_CLOCK_SKEW_SECONDS = 30


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


def state_auth_violation(
    state: RobotStateAssertion,
    edge_public_keys_by_id: Mapping[str, str],
) -> str | None:
    if state.authenticated_edge_agent_id is None:
        return "STATE_AUTHENTICATED_EDGE_MISSING"
    if state.authenticated_edge_agent_id != state.edge_agent_id:
        return "STATE_AUTHENTICATED_EDGE_MISMATCH"
    if state.signature is None:
        return "STATE_SIGNATURE_MISSING"
    public_key = edge_public_keys_by_id.get(state.authenticated_edge_agent_id)
    if public_key is None:
        return "EDGE_STATE_KEY_NOT_TRUSTED"
    if not verify_with_public_key_b64(state, state.signature, public_key):
        return "STATE_SIGNATURE_INVALID"
    return None
