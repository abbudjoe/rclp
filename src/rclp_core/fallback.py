from __future__ import annotations

from collections.abc import Mapping

from rclp_core.crypto import DemoKeyPair, verify_with_public_key_b64
from rclp_core.models import (
    ED25519_SIGNATURE_ALGORITHM,
    FallbackDeclaration,
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


def sign_fallback_declaration(
    declaration: FallbackDeclaration,
    signer: DemoKeyPair,
    *,
    authenticated_declared_by: str | None = None,
) -> FallbackDeclaration:
    declaration.authenticated_declared_by = authenticated_declared_by or declaration.declared_by
    declaration.signature_alg = ED25519_SIGNATURE_ALGORITHM
    declaration.signature = None
    declaration.signature = signer.sign(declaration)
    return declaration


def fallback_declaration_auth_violation(
    declaration: FallbackDeclaration,
    edge_public_keys_by_id: Mapping[str, str],
) -> str | None:
    if alg_reason := signature_algorithm_violation(
        declaration,
        missing_reason="FALLBACK_SIGNATURE_ALGORITHM_MISSING",
        unsupported_reason="FALLBACK_SIGNATURE_ALGORITHM_UNSUPPORTED",
    ):
        return alg_reason
    if declaration.authenticated_declared_by is None:
        return "FALLBACK_AUTHENTICATED_DECLARED_BY_MISSING"
    if declaration.authenticated_declared_by != declaration.declared_by:
        return "FALLBACK_AUTHENTICATED_DECLARED_BY_MISMATCH"
    if declaration.signature is None:
        return "FALLBACK_SIGNATURE_MISSING"
    public_key = edge_public_keys_by_id.get(declaration.authenticated_declared_by)
    if public_key is None:
        return "FALLBACK_DECLARER_KEY_NOT_TRUSTED"
    if fallback_declaration_signed_material_too_large(declaration):
        return "FALLBACK_SIGNED_MATERIAL_TOO_LARGE"
    if not verify_with_public_key_b64(declaration, declaration.signature, public_key):
        return "FALLBACK_SIGNATURE_INVALID"
    return None


def fallback_declaration_signed_material_too_large(
    declaration: FallbackDeclaration,
) -> bool:
    if (
        declaration.signature is not None
        and len(declaration.signature.encode("utf-8")) > ED25519_SIGNATURE_B64_MAX_TEXT_BYTES
    ):
        return True
    text_budget = _SignedTextBudget()
    for value in (
        declaration.protocol_version,
        declaration.message_id,
        declaration.correlation_id,
        declaration.created_at.isoformat(),
        declaration.message_type,
        declaration.robot_id,
        declaration.edge_agent_id,
        declaration.mission_id,
        declaration.trigger,
        declaration.fallback_action,
        declaration.declared_by,
        declaration.authenticated_declared_by,
        declaration.lease_id,
        declaration.decision_id,
        declaration.revocation_id,
        declaration.signature_alg,
        declaration.signature,
    ):
        if text_budget.exceeded(value):
            return True
    return False
