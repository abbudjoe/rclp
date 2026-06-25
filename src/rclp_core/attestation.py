from __future__ import annotations

from collections.abc import Collection, Mapping
from datetime import datetime, timedelta, timezone

from rclp_core.crypto import verify_with_public_key_b64
from rclp_core.models import AgentAttestation, signature_algorithm_violation


DEFAULT_ATTESTATION_MAX_AGE_SECONDS = 300
ATTESTATION_CLOCK_SKEW_SECONDS = 30
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


def attestation_signed_material_too_large(attestation: AgentAttestation) -> bool:
    text_budget = _SignedTextBudget()
    for value in (
        attestation.protocol_version,
        attestation.message_id,
        attestation.correlation_id,
        attestation.created_at.isoformat(),
        attestation.message_type,
        attestation.agent_id,
        attestation.authenticated_agent_id,
        attestation.kind,
        attestation.manifest_digest,
        attestation.public_key_id,
        attestation.trust_tier,
        attestation.revoked,
        attestation.signature_alg,
        attestation.signature,
    ):
        if text_budget.exceeded(value):
            return True
    return False


def attestation_auth_violation(
    attestation: AgentAttestation,
    agent_public_keys_by_id: Mapping[str, str],
) -> str | None:
    """Return an authentication-only rejection reason for an attestation."""
    if alg_reason := signature_algorithm_violation(
        attestation,
        missing_reason="ATTESTATION_SIGNATURE_ALGORITHM_MISSING",
        unsupported_reason="ATTESTATION_SIGNATURE_ALGORITHM_UNSUPPORTED",
    ):
        return alg_reason
    if attestation.authenticated_agent_id is None:
        return "ATTESTATION_AUTHENTICATED_AGENT_MISSING"
    if attestation.authenticated_agent_id != attestation.agent_id:
        return "ATTESTATION_AUTHENTICATED_AGENT_MISMATCH"
    if attestation.signature is None:
        return "ATTESTATION_SIGNATURE_MISSING"
    public_key = agent_public_keys_by_id.get(attestation.authenticated_agent_id)
    if public_key is None:
        return "ATTESTATION_AGENT_KEY_NOT_TRUSTED"
    if attestation_signed_material_too_large(attestation):
        return "ATTESTATION_SIGNED_MATERIAL_TOO_LARGE"
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
    if not accepted_trust_tiers:
        return "ATTESTATION_TRUST_TIER_POLICY_REQUIRED"
    normalized_trust_tiers = {tier for tier in accepted_trust_tiers if tier.strip()}
    if len(normalized_trust_tiers) != len(accepted_trust_tiers):
        return "ATTESTATION_TRUST_TIER_POLICY_REQUIRED"
    if "trust_tier" not in attestation.model_fields_set:
        return "ATTESTATION_TRUST_TIER_MISSING"
    if attestation.trust_tier not in normalized_trust_tiers:
        return "ATTESTATION_TRUST_TIER_NOT_ACCEPTED"
    if manifest_digests_by_agent_id is None:
        return "ATTESTATION_MANIFEST_DIGEST_POLICY_REQUIRED"
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
