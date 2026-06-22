import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VECTOR_DIR = ROOT / "tests" / "vectors" / "edge_verifier"

EXPECTED_VECTOR_NAMES = {
    "expired_lease_rejected",
    "geofence_violation_rejected",
    "malformed_signature_rejected",
    "malformed_numeric_rejected",
    "missing_required_field_rejected",
    "network_degrade_denies_or_revokes",
    "network_missing_fallback_rejected",
    "network_partition_rejected",
    "network_partition_degrade_action_rejected",
    "not_yet_valid_rejected",
    "replay_nonce_rejected",
    "revoked_lease_rejected",
    "stale_lease_rejected",
    "ttl_too_long_rejected",
    "unknown_algorithm_rejected",
    "unknown_issuer_rejected",
    "valid_remote_assist_lease",
    "wrong_agent_rejected",
    "wrong_capability_rejected",
    "wrong_edge_agent_rejected",
    "wrong_mission_rejected",
    "wrong_robot_rejected",
}

EXPECTED_REASON_CODES = {
    "ALLOW",
    "DENY_CAPABILITY_NOT_GRANTED",
    "DENY_EXPIRED_LEASE",
    "DENY_GEOFENCE_VIOLATION",
    "DENY_INVALID_SIGNATURE",
    "DENY_MALFORMED_INPUT",
    "DENY_NETWORK_POLICY",
    "DENY_NOT_YET_VALID",
    "DENY_REPLAYED_NONCE",
    "DENY_REVOKED_LEASE",
    "DENY_ROBOT_MISMATCH",
    "DENY_AGENT_MISMATCH",
    "DENY_MISSION_MISMATCH",
    "DENY_STALE_LEASE",
    "DENY_TTL_TOO_LONG",
    "DENY_UNKNOWN_ALGORITHM",
    "DENY_UNKNOWN_ISSUER",
    "DEGRADE_NETWORK_POLICY",
}

REQUIRED_CLAIM_FIELDS = {
    "lease_id",
    "issuer_id",
    "agent_id",
    "edge_agent_id",
    "robot_id",
    "mission_id",
    "capability",
    "constraints",
    "issued_at",
    "expires_at",
    "nonce",
}


def load_vectors() -> list[dict]:
    return [
        json.loads(path.read_text(encoding="utf-8")) for path in sorted(VECTOR_DIR.glob("*.json"))
    ]


def test_rust_edge_vector_directory_is_well_formed():
    assert VECTOR_DIR.is_dir()
    names = {path.stem for path in VECTOR_DIR.glob("*.json")}
    assert EXPECTED_VECTOR_NAMES.issubset(names)

    for vector in load_vectors():
        name = vector["name"]
        assert (VECTOR_DIR / f"{name}.json").exists()
        assert vector["description"].strip()
        assert isinstance(vector["now_unix_ms"], int)
        assert set(vector["trusted_context"]) == {
            "trusted_issuer_ids",
            "dev_hmac_secret",
            "now_unix_ms",
            "revocations",
            "max_lease_ttl_ms",
            "max_lease_age_ms",
        }
        assert vector["trusted_context"]["trusted_issuer_ids"] == ["issuer"]
        assert vector["trusted_context"]["dev_hmac_secret"] == "dev-test-secret"
        assert vector["trusted_context"]["now_unix_ms"] == vector["now_unix_ms"]
        assert isinstance(vector["trusted_context"]["revocations"], list)
        assert isinstance(vector["trusted_context"]["max_lease_ttl_ms"], int)
        assert isinstance(vector["trusted_context"]["max_lease_age_ms"], int)
        assert isinstance(vector["seen_nonces"], list)
        assert set(vector["input"]) == {"lease", "command", "local_context"}
        assert vector["expected"]["decision"] in {"allow", "deny", "degrade"}
        assert vector["expected"]["reason_code"] in EXPECTED_REASON_CODES

        lease = vector["input"]["lease"]
        assert set(lease) == {"alg", "claims", "signature"}
        assert isinstance(lease["claims"], dict)
        if name != "missing_required_field_rejected":
            assert REQUIRED_CLAIM_FIELDS.issubset(lease["claims"])
        assert "trusted_issuer_ids" not in vector["input"]["local_context"]
        assert "dev_hmac_secret" not in vector["input"]["local_context"]


def test_rust_edge_vectors_use_dev_hmac_profile_only_where_expected():
    for vector in load_vectors():
        alg = vector["input"]["lease"]["alg"]
        expected_reason = vector["expected"]["reason_code"]
        if expected_reason == "DENY_UNKNOWN_ALGORITHM":
            assert alg != "RCLP-DEV-HMAC-SHA256"
        else:
            assert alg == "RCLP-DEV-HMAC-SHA256"
