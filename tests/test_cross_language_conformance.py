import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts/run_cross_language_conformance.py"


def load_runner():
    spec = importlib.util.spec_from_file_location(
        "run_cross_language_conformance",
        RUNNER_PATH,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_cross_language_report_passes_when_shared_decisions_match():
    runner = load_runner()
    python_report = {
        "results": [
            {
                "name": case.python_name,
                "status": "passed",
                "actual_decision": "allow" if case.python_name == "valid_remote_assist" else "deny",
                "actual_reason_code": sorted(case.python_reason_codes)[0],
            }
            for case in runner.PARITY_CASES
        ]
    }
    rust_vectors = {
        case.rust_name: {
            "name": case.rust_name,
            "expected": {
                "decision": "allow" if case.python_name == "valid_remote_assist" else "deny",
                "reason_code": sorted(case.rust_reason_codes)[0],
            },
        }
        for case in runner.PARITY_CASES
    }

    report = runner.build_cross_language_report(python_report, rust_vectors)

    assert report["summary"]["failed"] == 0
    assert report["summary"]["passed"] == len(runner.PARITY_CASES)


def test_cross_language_report_fails_on_decision_divergence():
    runner = load_runner()
    python_report = {
        "results": [
            {
                "name": case.python_name,
                "status": "passed",
                "actual_decision": "deny",
                "actual_reason_code": sorted(case.python_reason_codes)[0],
            }
            for case in runner.PARITY_CASES
        ]
    }
    rust_vectors = {
        case.rust_name: {
            "name": case.rust_name,
            "expected": {
                "decision": "deny",
                "reason_code": sorted(case.rust_reason_codes)[0],
            },
        }
        for case in runner.PARITY_CASES
    }
    rust_vectors["valid_remote_assist_lease"]["expected"]["decision"] = "allow"

    report = runner.build_cross_language_report(python_report, rust_vectors)

    assert report["summary"]["failed"] == 1
    failed_case = next(case for case in report["cases"] if case["status"] == "failed")
    assert failed_case["python_scenario"] == "valid_remote_assist"
    assert "decision mismatch" in failed_case["errors"][0]


def test_cross_language_report_fails_on_reason_family_divergence():
    runner = load_runner()
    python_report = {
        "results": [
            {
                "name": case.python_name,
                "status": "passed",
                "actual_decision": "allow" if case.python_name == "valid_remote_assist" else "deny",
                "actual_reason_code": sorted(case.python_reason_codes)[0],
            }
            for case in runner.PARITY_CASES
        ]
    }
    rust_vectors = {
        case.rust_name: {
            "name": case.rust_name,
            "expected": {
                "decision": "allow" if case.python_name == "valid_remote_assist" else "deny",
                "reason_code": sorted(case.rust_reason_codes)[0],
            },
        }
        for case in runner.PARITY_CASES
    }
    python_report["results"][0]["actual_reason_code"] = "WRONG_ALLOW_REASON"

    report = runner.build_cross_language_report(python_report, rust_vectors)

    assert report["summary"]["failed"] == 1
    failed_case = next(case for case in report["cases"] if case["status"] == "failed")
    assert failed_case["python_scenario"] == "valid_remote_assist"
    assert "Python reason mismatch" in failed_case["errors"][0]
