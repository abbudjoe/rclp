import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VECTOR_DIR = ROOT / "tests" / "vectors" / "edge_verifier"

EXPECTED_VECTOR_NAMES = {
    "command_authenticated_agent_missing_rejected",
    "command_invalid_signature_rejected",
    "command_missing_signature_rejected",
    "command_not_yet_valid_rejected",
    "command_stale_rejected",
    "command_untrusted_agent_rejected",
    "expired_lease_rejected",
    "geofence_violation_rejected",
    "malformed_signature_rejected",
    "max_speed_too_high_rejected",
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
    "stale_local_state_rejected",
    "ttl_too_long_rejected",
    "unsigned_local_state_rejected",
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
    "DENY_STALE_STATE",
    "DENY_STATE_AUTHENTICATED_EDGE_MISSING",
    "DENY_STATE_AUTHENTICATED_EDGE_MISMATCH",
    "DENY_STATE_KEY_NOT_TRUSTED",
    "DENY_STATE_SIGNATURE_MISSING",
    "DENY_INVALID_STATE_SIGNATURE",
    "DENY_COMMAND_AUTHENTICATED_AGENT_MISSING",
    "DENY_COMMAND_AUTHENTICATED_AGENT_MISMATCH",
    "DENY_COMMAND_AGENT_KEY_NOT_TRUSTED",
    "DENY_COMMAND_SIGNATURE_MISSING",
    "DENY_INVALID_COMMAND_SIGNATURE",
    "DENY_COMMAND_NOT_YET_VALID",
    "DENY_STALE_COMMAND",
    "DENY_REPLAYED_COMMAND",
    "DENY_COMMAND_CONSTRAINT",
    "DENY_LEASE_CONSTRAINTS_EXCEED_POLICY",
    "DENY_POLICY_DIGEST_REQUIRED",
    "DENY_POLICY_DIGEST_NOT_ACCEPTED",
    "DENY_TTL_TOO_LONG",
    "DENY_UNKNOWN_ALGORITHM",
    "DENY_UNKNOWN_ISSUER",
    "DEGRADE_NETWORK_POLICY",
}

REQUIRED_CLAIM_FIELDS = {
    "protocol_version",
    "message_id",
    "correlation_id",
    "created_at_unix_ms",
    "message_type",
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
    "policy_id",
    "policy_digest",
}

REQUIRED_COMMAND_FIELDS = {
    "protocol_version",
    "message_id",
    "correlation_id",
    "message_type",
    "command_id",
    "agent_id",
    "authenticated_agent_id",
    "edge_agent_id",
    "robot_id",
    "mission_id",
    "capability",
    "command_nonce",
    "created_at_unix_ms",
    "payload",
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
            "policy_id",
            "policy_digest",
            "audit_chain_head",
            "accepted_policies",
            "trusted_issuer_ids",
            "accepted_capabilities",
            "issuer_capability_scopes",
            "capability_constraint_requirements",
            "capability_constraint_bounds",
            "trusted_command_agent_ids",
            "command_hmac_secret",
            "dev_hmac_secret",
            "trusted_state_edge_ids",
            "state_hmac_secret",
            "now_unix_ms",
            "revocations",
            "max_lease_ttl_ms",
            "max_lease_age_ms",
            "max_state_age_ms",
            "max_command_age_ms",
        }
        assert vector["trusted_context"]["policy_id"] == "remote-assist-authority-v0"
        assert (
            vector["trusted_context"]["policy_digest"]
            == "sha256:remote-assist-authority-v0-test-digest"
        )
        assert (
            vector["trusted_context"]["audit_chain_head"] == "sha256:trusted-dev-audit-chain-head"
        )
        assert vector["trusted_context"]["accepted_policies"] == [
            {
                "policy_id": "remote-assist-authority-v0",
                "policy_digest": "sha256:remote-assist-authority-v0-test-digest",
            }
        ]
        assert vector["trusted_context"]["trusted_issuer_ids"] == ["issuer"]
        assert vector["trusted_context"]["accepted_capabilities"] == ["remote_assist"]
        assert vector["trusted_context"]["issuer_capability_scopes"] == [
            {"issuer_id": "issuer", "capabilities": ["remote_assist"]}
        ]
        assert vector["trusted_context"]["capability_constraint_requirements"] == [
            {
                "capability": "remote_assist",
                "require_geofence_id": True,
                "require_network_thresholds": True,
                "require_fallback_on_degrade": True,
                "require_max_speed_mps": False,
            }
        ]
        bounds = vector["trusted_context"]["capability_constraint_bounds"]
        assert len(bounds) == 1
        assert bounds[0]["capability"] == "remote_assist"
        assert bounds[0]["geofence_id"] == "test-zone-a"
        assert bounds[0]["max_latency_ms_p95"] == 80.0
        assert bounds[0]["max_packet_loss_pct"] == 1.0
        assert bounds[0]["min_uplink_mbps"] == 3.0
        assert bounds[0]["fallback_on_degrade"] == "crawl_to_safe_zone"
        assert set(bounds[0]) <= {
            "capability",
            "geofence_id",
            "max_latency_ms_p95",
            "max_packet_loss_pct",
            "min_uplink_mbps",
            "fallback_on_degrade",
            "max_speed_mps",
            "network_violation_action",
        }
        assert vector["trusted_context"]["trusted_command_agent_ids"] == ["fleet-agent:v0.1"]
        assert vector["trusted_context"]["command_hmac_secret"] == "command-dev-test-secret"
        assert vector["trusted_context"]["dev_hmac_secret"] == "dev-test-secret"
        assert vector["trusted_context"]["trusted_state_edge_ids"] == ["edge-agent:rover-001"]
        assert vector["trusted_context"]["state_hmac_secret"] == "state-dev-test-secret"
        assert vector["trusted_context"]["now_unix_ms"] == vector["now_unix_ms"]
        assert isinstance(vector["trusted_context"]["revocations"], list)
        assert isinstance(vector["trusted_context"]["max_lease_ttl_ms"], int)
        assert isinstance(vector["trusted_context"]["max_lease_age_ms"], int)
        assert isinstance(vector["trusted_context"]["max_state_age_ms"], int)
        assert isinstance(vector["trusted_context"]["max_command_age_ms"], int)
        assert isinstance(vector["seen_nonces"], list)
        assert set(vector["input"]) == {"lease", "command", "local_context"}
        assert vector["expected"]["decision"] in {"allow", "deny", "degrade"}
        assert vector["expected"]["reason_code"] in EXPECTED_REASON_CODES

        lease = vector["input"]["lease"]
        assert set(lease) == {"alg", "claims", "signature"}
        assert isinstance(lease["claims"], dict)
        if name != "missing_required_field_rejected":
            assert REQUIRED_CLAIM_FIELDS.issubset(lease["claims"])
        command = vector["input"]["command"]
        assert REQUIRED_COMMAND_FIELDS.issubset(command)
        if name != "command_authenticated_agent_missing_rejected":
            assert command["authenticated_agent_id"] == command["agent_id"]
        assert isinstance(command["created_at_unix_ms"], int)
        assert isinstance(command["payload"], dict)
        assert "max_speed_mps" not in command
        if name != "command_missing_signature_rejected":
            assert isinstance(command["signature"], str)
        assert "command_hmac_secret" not in command
        assert "trusted_issuer_ids" not in vector["input"]["local_context"]
        assert "dev_hmac_secret" not in vector["input"]["local_context"]
        assert "state_hmac_secret" not in vector["input"]["local_context"]
        assert (
            vector["input"]["local_context"].get("authenticated_edge_agent_id")
            == vector["input"]["local_context"]["edge_agent_id"]
        )
        if name != "unsigned_local_state_rejected":
            assert isinstance(vector["input"]["local_context"]["signature"], str)
        assert isinstance(vector["input"]["local_context"]["observed_at_unix_ms"], int)
        assert isinstance(
            vector["input"]["local_context"]["network_state"]["observed_at_unix_ms"],
            int,
        )
        assert isinstance(
            vector["input"]["local_context"]["geofence_state"]["verified_at_unix_ms"],
            int,
        )


def test_rust_edge_vectors_use_dev_hmac_profile_only_where_expected():
    for vector in load_vectors():
        alg = vector["input"]["lease"]["alg"]
        expected_reason = vector["expected"]["reason_code"]
        if expected_reason == "DENY_UNKNOWN_ALGORITHM":
            assert alg != "RCLP-DEV-HMAC-SHA256"
        else:
            assert alg == "RCLP-DEV-HMAC-SHA256"
