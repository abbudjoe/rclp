#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_EVAL_REPORT = REPO_ROOT / "tests/evals/reports/latest.json"
RUST_VECTOR_DIR = REPO_ROOT / "tests/vectors/edge_verifier"
DEFAULT_REPORT_PATH = REPO_ROOT / "tests/evals/reports/cross_language_latest.json"


@dataclass(frozen=True)
class ParityCase:
    python_name: str
    rust_name: str
    python_reason_codes: frozenset[str]
    rust_reason_codes: frozenset[str]


PARITY_CASES: tuple[ParityCase, ...] = (
    ParityCase(
        "valid_remote_assist",
        "valid_remote_assist_lease",
        frozenset({"LEASE_VALID"}),
        frozenset({"ALLOW"}),
    ),
    ParityCase(
        "expired_lease_denied",
        "expired_lease_rejected",
        frozenset({"LEASE_EXPIRED"}),
        frozenset({"DENY_EXPIRED_LEASE"}),
    ),
    ParityCase(
        "revoked_lease_denied",
        "revoked_lease_rejected",
        frozenset({"LEASE_REVOKED"}),
        frozenset({"DENY_REVOKED_LEASE"}),
    ),
    ParityCase(
        "replay_nonce_denied",
        "replay_nonce_rejected",
        frozenset({"REQUEST_REPLAYED"}),
        frozenset({"DENY_REPLAYED_NONCE"}),
    ),
    ParityCase(
        "wrong_central_agent_denied",
        "wrong_agent_rejected",
        frozenset({"COMMAND_AGENT_KEY_NOT_TRUSTED"}),
        frozenset({"DENY_AGENT_MISMATCH"}),
    ),
    ParityCase(
        "wrong_edge_agent_denied",
        "wrong_edge_agent_rejected",
        frozenset({"EDGE_AGENT_MISMATCH"}),
        frozenset({"DENY_AGENT_MISMATCH"}),
    ),
    ParityCase(
        "wrong_robot_denied",
        "wrong_robot_rejected",
        frozenset({"LEASE_CONTEXT_MISMATCH"}),
        frozenset({"DENY_ROBOT_MISMATCH"}),
    ),
    ParityCase(
        "wrong_mission_denied",
        "wrong_mission_rejected",
        frozenset({"LEASE_CONTEXT_MISMATCH"}),
        frozenset({"DENY_MISSION_MISMATCH"}),
    ),
    ParityCase(
        "capability_not_granted_denied",
        "wrong_capability_rejected",
        frozenset({"LEASE_CONTEXT_MISMATCH"}),
        frozenset({"DENY_CAPABILITY_NOT_GRANTED"}),
    ),
    ParityCase(
        "unknown_alg_denied",
        "unknown_algorithm_rejected",
        frozenset({"LEASE_SIGNATURE_ALGORITHM_UNSUPPORTED"}),
        frozenset({"DENY_UNKNOWN_ALGORITHM"}),
    ),
    ParityCase(
        "malformed_signature_denied",
        "malformed_signature_rejected",
        frozenset({"INVALID_SIGNATURE"}),
        frozenset({"DENY_INVALID_SIGNATURE"}),
    ),
    ParityCase(
        "geofence_violation_denied",
        "geofence_violation_rejected",
        frozenset({"GEOFENCE_CONSTRAINT_VIOLATED"}),
        frozenset({"DENY_GEOFENCE_VIOLATION"}),
    ),
    ParityCase(
        "cloud_partition_no_new_authority",
        "network_partition_rejected",
        frozenset({"NETWORK_DETACHED"}),
        frozenset({"DENY_NETWORK_POLICY"}),
    ),
    ParityCase(
        "stale_current_state_denied",
        "stale_local_state_rejected",
        frozenset({"STATE_STALE"}),
        frozenset({"DENY_STALE_STATE"}),
    ),
    ParityCase(
        "max_speed_too_high_denied",
        "max_speed_too_high_rejected",
        frozenset({"COMMAND_SPEED_TOO_HIGH"}),
        frozenset({"DENY_COMMAND_CONSTRAINT"}),
    ),
)


def run_command(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_rust_vectors(vector_dir: Path = RUST_VECTOR_DIR) -> dict[str, dict[str, Any]]:
    vectors: dict[str, dict[str, Any]] = {}
    for path in sorted(vector_dir.glob("*.json")):
        vector = load_json(path)
        vectors[vector["name"]] = vector
    return vectors


def build_cross_language_report(
    python_report: dict[str, Any],
    rust_vectors: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    python_results = {result["name"]: result for result in python_report.get("results", [])}
    cases: list[dict[str, Any]] = []

    for parity_case in PARITY_CASES:
        python_result = python_results.get(parity_case.python_name)
        rust_vector = rust_vectors.get(parity_case.rust_name)
        errors: list[str] = []

        if python_result is None:
            errors.append(f"missing Python eval scenario: {parity_case.python_name}")
            python_decision = None
            python_reason = None
            python_status = "missing"
        else:
            python_decision = _normalize_decision(python_result.get("actual_decision"))
            python_reason = python_result.get("actual_reason_code")
            python_status = python_result.get("status")
            if python_status != "passed":
                errors.append(f"Python eval did not pass: {parity_case.python_name}")

        if rust_vector is None:
            errors.append(f"missing Rust vector: {parity_case.rust_name}")
            rust_decision = None
            rust_reason = None
        else:
            expected = rust_vector.get("expected", {})
            rust_decision = _normalize_decision(expected.get("decision"))
            rust_reason = expected.get("reason_code")

        if python_decision != rust_decision:
            errors.append(f"decision mismatch: python={python_decision!r} rust={rust_decision!r}")
        if python_result is not None and python_reason not in parity_case.python_reason_codes:
            errors.append(
                "Python reason mismatch: "
                f"got {python_reason!r}, expected one of "
                f"{sorted(parity_case.python_reason_codes)}"
            )
        if rust_vector is not None and rust_reason not in parity_case.rust_reason_codes:
            errors.append(
                "Rust reason mismatch: "
                f"got {rust_reason!r}, expected one of "
                f"{sorted(parity_case.rust_reason_codes)}"
            )

        cases.append(
            {
                "python_scenario": parity_case.python_name,
                "rust_vector": parity_case.rust_name,
                "status": "passed" if not errors else "failed",
                "python_status": python_status,
                "python_decision": python_decision,
                "python_reason_code": python_reason,
                "rust_decision": rust_decision,
                "rust_reason_code": rust_reason,
                "errors": errors,
            }
        )

    failed = sum(1 for case in cases if case["status"] != "passed")
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total": len(cases),
            "passed": len(cases) - failed,
            "failed": failed,
        },
        "cases": cases,
    }


def _normalize_decision(value: object) -> str | None:
    if value is None:
        return None
    return str(value).lower()


def write_report(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def print_summary(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    print(
        "RCLP cross-language conformance: "
        f"{summary['passed']} passed, {summary['failed']} failed, {summary['total']} total"
    )
    for case in report["cases"]:
        status = "PASS" if case["status"] == "passed" else "FAIL"
        print(
            f"{status} {case['python_scenario']} <-> {case['rust_vector']}: "
            f"{case['python_decision']} / {case['rust_decision']}"
        )
        for error in case["errors"]:
            print(f"  - {error}")
    print(f"Wrote JSON report: {path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run Python evals, Rust verifier vectors, and compare shared decisions."
    )
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--require-rust", action="store_true")
    parser.add_argument("--skip-commands", action="store_true")
    args = parser.parse_args(argv)

    command_results: list[dict[str, Any]] = []
    if not args.skip_commands:
        command_results.append(
            run_command(
                [
                    sys.executable,
                    "tests/evals/eval_runner.py",
                    "--report",
                    str(PYTHON_EVAL_REPORT),
                ]
            )
        )
        if shutil.which("cargo") is not None:
            command_results.append(
                run_command(["cargo", "test", "-p", "rclp-edge-verifier", "--test", "vector_tests"])
            )
        else:
            command_results.append(
                {
                    "command": [
                        "cargo",
                        "test",
                        "-p",
                        "rclp-edge-verifier",
                        "--test",
                        "vector_tests",
                    ],
                    "returncode": None,
                    "stdout": "",
                    "stderr": "cargo not found; Rust vector execution skipped",
                }
            )

    report = build_cross_language_report(load_json(PYTHON_EVAL_REPORT), load_rust_vectors())
    report["commands"] = command_results
    write_report(report, args.report)
    print_summary(report, args.report)

    command_failed = any(result["returncode"] not in {0, None} for result in command_results)
    rust_skipped = any(result["returncode"] is None for result in command_results)
    if report["summary"]["failed"] or command_failed or (args.require_rust and rust_skipped):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
