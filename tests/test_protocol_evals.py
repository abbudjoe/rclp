import importlib.util
import sys
from pathlib import Path


EVAL_RUNNER_PATH = Path(__file__).parent / "evals" / "eval_runner.py"


def load_eval_runner():
    spec = importlib.util.spec_from_file_location("rclp_eval_runner", EVAL_RUNNER_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_eval_runner_executes_required_scenario_set(tmp_path):
    runner = load_eval_runner()

    report = runner.run_all(runner.scenario_dir(), tmp_path / "latest.json")

    assert report["summary"] == {"total": 33, "passed": 33, "failed": 0}
    names = {result["name"] for result in report["results"]}
    assert {
        "valid_remote_assist",
        "no_lease_denied",
        "expired_lease_denied",
        "not_yet_valid_denied",
        "revoked_lease_denied",
        "replay_nonce_denied",
        "wrong_central_agent_denied",
        "wrong_edge_agent_denied",
        "wrong_robot_denied",
        "wrong_mission_denied",
        "capability_not_granted_denied",
        "unknown_alg_denied",
        "malformed_signature_denied",
        "malformed_input_denied",
        "geofence_violation_denied",
        "high_latency_degraded_or_denied",
        "high_packet_loss_degraded_or_denied",
        "cloud_partition_no_new_authority",
        "stale_command_after_expiry_denied",
        "conflicting_state_denied",
        "audit_allow_complete",
        "audit_deny_complete",
        "scenario_network_degrade_revokes",
        "scenario_cloud_partition_expiry",
        "missing_current_state_denied",
        "stale_current_state_denied",
        "unsigned_state_policy_denied",
        "stale_state_policy_denied",
        "max_speed_too_high_denied",
        "unsigned_revocation_denied",
        "unsigned_current_state_denied",
        "conflicting_speed_alias_denied",
        "nonfinite_speed_denied",
    } == names


def test_malformed_eval_input_denies_without_crashing():
    runner = load_eval_runner()
    result = runner.evaluate_scenario(
        {
            "name": "missing_robot_id",
            "kind": "malformed_input",
            "input": {
                "raw_request": {
                    "requesting_agent_id": "fleet-agent:v0.1",
                    "edge_agent_id": "edge-agent:rover-001",
                    "mission_id": "mission-001",
                    "capability": "remote_assist",
                    "reason": "missing robot_id",
                }
            },
            "expected": {"decision": "deny", "reason_code": "MALFORMED_INPUT"},
        }
    )

    assert result.passed is True
    assert result.actual_decision == "deny"
    assert result.actual_reason_code == "MALFORMED_INPUT"


def test_eval_runner_fails_when_required_registry_is_missing(tmp_path):
    runner = load_eval_runner()

    report = runner.run_all(tmp_path, tmp_path / "latest.json")

    assert report["summary"]["failed"] > 0
    assert any(
        "missing required eval scenario" in error
        for result in report["results"]
        for error in result["errors"]
    )


def test_eval_runner_requires_expected_decision_and_reason():
    runner = load_eval_runner()
    result = runner.evaluate_scenario(
        {
            "name": "missing_expectations",
            "kind": "malformed_input",
            "input": {"raw_request": {}},
            "expected": {},
        }
    )

    assert result.passed is False
    assert "expected.decision" in "\n".join(result.errors)
    assert "expected.reason_code" in "\n".join(result.errors)
