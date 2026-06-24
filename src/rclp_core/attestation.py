from __future__ import annotations

from collections.abc import Collection, Mapping
from datetime import datetime, timedelta, timezone

from rclp_core.crypto import verify_with_public_key_b64
from rclp_core.models import AgentAttestation


DEFAULT_ATTESTATION_MAX_AGE_SECONDS = 300
ATTESTATION_CLOCK_SKEW_SECONDS = 30


def attestation_auth_violation(
    attestation: AgentAttestation,
    agent_public_keys_by_id: Mapping[str, str],
) -> str | None:
    """Return an authentication-only rejection reason for an attestation."""
    if attestation.authenticated_agent_id is None:
        return "ATTESTATION_AUTHENTICATED_AGENT_MISSING"
    if attestation.authenticated_agent_id != attestation.agent_id:
        return "ATTESTATION_AUTHENTICATED_AGENT_MISMATCH"
    if attestation.signature is None:
        return "ATTESTATION_SIGNATURE_MISSING"
    public_key = agent_public_keys_by_id.get(attestation.authenticated_agent_id)
    if public_key is None:
        return "ATTESTATION_AGENT_KEY_NOT_TRUSTED"
    if not verify_with_public_key_b64(attestation, attestation.signature, public_key):
        return "ATTESTATION_SIGNATURE_INVALID"
    return None


def attestation_trust_violation(
    attestation: AgentAttestation,
    agent_public_keys_by_id: Mapping[str, str],
    *,
    public_key_ids_by_agent_id: Mapping[str, str] | None = None,
    accepted_trust_tiers: Collection[str] | None = None,
    manifest_digests_by_agent_id: Mapping[str, str] | None = None,
    now: datetime | None = None,
    max_attestation_age_seconds: int = DEFAULT_ATTESTATION_MAX_AGE_SECONDS,
) -> str | None:
    """Return the first trust-boundary rejection reason for an attestation."""
    if reason := attestation_auth_violation(attestation, agent_public_keys_by_id):
        return reason
    if time_reason := _attestation_time_violation(
        attestation,
        now=now,
        max_age_seconds=max_attestation_age_seconds,
    ):
        return time_reason
    if not attestation.manifest_digest.strip():
        return "ATTESTATION_MANIFEST_DIGEST_MISSING"
    if not attestation.public_key_id.strip():
        return "ATTESTATION_PUBLIC_KEY_ID_MISSING"
    public_key_ids_by_agent_id = public_key_ids_by_agent_id or {}
    expected_public_key_id = public_key_ids_by_agent_id.get(attestation.agent_id)
    if expected_public_key_id is None or not expected_public_key_id.strip():
        return "ATTESTATION_PUBLIC_KEY_ID_NOT_TRUSTED"
    if attestation.public_key_id != expected_public_key_id:
        return "ATTESTATION_PUBLIC_KEY_ID_MISMATCH"
    if attestation.revoked:
        return "ATTESTATION_AGENT_REVOKED"
    if accepted_trust_tiers is not None and attestation.trust_tier not in accepted_trust_tiers:
        return "ATTESTATION_TRUST_TIER_NOT_ACCEPTED"
    if manifest_digests_by_agent_id is not None:
        expected_manifest_digest = manifest_digests_by_agent_id.get(attestation.agent_id)
        if expected_manifest_digest is None or not expected_manifest_digest.strip():
            return "ATTESTATION_MANIFEST_DIGEST_NOT_TRUSTED"
        if attestation.manifest_digest != expected_manifest_digest:
            return "ATTESTATION_MANIFEST_DIGEST_MISMATCH"
    return None


def _attestation_time_violation(
    attestation: AgentAttestation,
    *,
    now: datetime | None,
    max_age_seconds: int,
) -> str | None:
    now = now or datetime.now(timezone.utc)
    if attestation.created_at.tzinfo is None or attestation.created_at.utcoffset() is None:
        return "ATTESTATION_TIMESTAMP_INVALID"
    if attestation.created_at > now + timedelta(seconds=ATTESTATION_CLOCK_SKEW_SECONDS):
        return "ATTESTATION_NOT_YET_VALID"
    if now - attestation.created_at > timedelta(
        seconds=max_age_seconds + ATTESTATION_CLOCK_SKEW_SECONDS
    ):
        return "ATTESTATION_STALE"
    return None
