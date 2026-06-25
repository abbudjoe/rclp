# S1 — Fresh-clone Reproducibility Review

## Verdict

GREEN

## Summary

- A skeptical robotics/platform engineer can clone the repo, understand the RCLP primitive quickly, install the declared dev dependencies, run tests, run evals, run the demo, and understand what the MVP proves.
- The README explains the project in under one minute: it states the authority-layer claim, the non-goals, quickstart, demo markers, validation package, safety boundary, and commercial boundary.
- The supported local proof matches the intended MVP claim for controlled technical validation: short-lived, locally enforced capability leases conditioned on identity, mission, geofence, network state, and fallback policy.
- The repo does not claim production safety, field validation, real carrier/network behavior, runnable ROS 2 integration, Isaac Sim execution, or hosted commercial-platform readiness.
- I would be comfortable sending this repo to a technical reviewer for controlled validation calls, with the caveat that reviewers should follow the documented venv/install step or use the packaged scripts rather than bare system Python.

## Commands run

- `python -m venv .venv` — passed; rerun against the existing ignored local venv.
- `.venv/bin/python -m pip install -e '.[dev]'` — passed; rebuilt the editable package and found declared runtime/dev dependencies already satisfied.
- `python -m compileall src tests` — passed.
- `pytest` — failed outside an activated environment: `zsh:1: command not found: pytest`.
- `.venv/bin/python -m pytest` — passed: 246 tests.
- `python tests/evals/eval_runner.py` — failed outside the venv: `ModuleNotFoundError: No module named 'yaml'`.
- `.venv/bin/python tests/evals/eval_runner.py` — passed: 33 eval scenarios, 0 failed; wrote the ignored generated report under `tests/evals/reports/`.
- `python -m rclp_agents.demo_remote_assist` — failed outside the venv: `ModuleNotFoundError: No module named 'rclp_agents'`.
- `.venv/bin/python -m rclp_agents.demo_remote_assist` — passed; showed allow, no-lease deny, degraded-network decision, revocation, post-revocation deny, audit JSONL, and incident replay summary.
- `cargo fmt --all -- --check` — passed.
- `cargo clippy --workspace --all-targets -- -D warnings` — passed.
- `cargo test --workspace` — passed: 3 Rust unit tests and 47 vector tests.
- `./scripts/run_validation_checks.sh` — passed end to end, including compileall, pytest, evals, Ruff, Rust fmt, Rust clippy, and Rust tests.
- `./scripts/run_validation_demo.sh --network-profile uplink_bad` — passed; hard-deny path showed `NETWORK_UPLINK_TOO_LOW`, `NETWORK_PROFILE_REVOKE`, `LEASE_REVOKED`, fallback declarations, audit JSONL, and replay summary.
- `git status --short` — clean before this report/ledger update.
- `git ls-files --others --exclude-standard` — no untracked required files before this report/ledger update.
- Targeted local-path/credential/TODO scan over reviewer-facing docs, source, tests, crates, scripts, manifests, examples, and workflows — no committed production credentials or hidden required files found. Current non-production HMAC/test keys are explicitly labeled.

## What worked

- Quickstart is complete and accurate for a local Python 3.11+ environment when the documented venv and editable dev install are used.
- `scripts/run_validation_checks.sh` is a good reviewer-facing command because it exercises Python compile, pytest, deterministic evals, Ruff, and Rust checks when Cargo is installed.
- The demo actually demonstrates the intended flow: signed request, `POLICY_SATISFIED` allow, `LEASE_VALID` command gate allow, `NO_LEASE` deny, `NETWORK_LATENCY_DEGRADED` or `NETWORK_UPLINK_TOO_LOW`, `NETWORK_PROFILE_REVOKE`, `LEASE_REVOKED`, fallback hook declaration, `audit_jsonl`, and `incident_replay_summary`.
- The eval suite is deterministic and local. It discovered 33 YAML scenarios and explicitly covers missing, stale, expired, revoked, replayed, malformed, mismatched, geofence, network, current-state, speed, revocation, audit, degradation, and partition/expiry paths.
- Rust verifier checks are present and deterministic. The workspace consumes shared vectors under `tests/vectors/edge_verifier/` and clearly labels its HMAC profile as test-only.
- CI workflows exist for both Python and Rust. Python CI covers compileall, `python -m pytest`, deterministic evals, and the demo marker smoke; Rust CI covers Rust fmt, clippy, and tests. Ruff remains covered by the local packaged validation script.
- No untracked required files were present before this report update. Generated artifacts are ignored: `.venv/`, `target/`, egg-info, pytest/Ruff caches, and `tests/evals/reports/latest.json`.
- Secret/path scan did not find committed production secrets. The visible HMAC strings are in test vectors and documented as non-production. Lambda/Isaac docs use operator placeholders and warnings rather than committed credentials.

## What failed or was confusing

- The bare prompt commands `pytest`, `python tests/evals/eval_runner.py`, and `python -m rclp_agents.demo_remote_assist` failed in this shell because the system Python was not using the repo venv or editable install. This is not a repo blocker because the README documents the venv/install path and the packaged scripts select `.venv/bin/python` when present.
- The packaged validation script requires dev dependencies because Ruff is part of the local gate. It prints the install command if dependencies are missing.
- `compileall src tests` can list ignored generated directories such as egg-info and eval reports after local setup. This is harmless, but fresh reviewers may notice it.
- The demo output is intentionally verbose. The README and demo script now include marker tables, which makes it practical to narrate live without scrolling through every JSON field.
- `SECURITY.md` now provides controlled-validation private-channel reporting guidance. Before a public launch, the project should still publish a monitored security address or enable private vulnerability reporting.
- Isaac Sim and ROS 2 are clearly scoped as scaffold/POC surfaces, not runnable proof paths. That is documented correctly, but the reviewer should not infer simulator or robot integration from the local proof.

## Blocking issues before customer calls

- None for controlled technical validation calls, assuming the presenter runs `./scripts/run_validation_checks.sh` in the checkout that will be shown.

## Non-blocking improvements

- Implemented in follow-up: `SECURITY.md` now names GitHub private vulnerability reporting for `abbudjoe/rclp` as the public-launch reporting path and requires a monitored email if repository-hosted private reporting is unavailable.
- Implemented in follow-up: `README.md` now uses `python -m pytest` in quickstart and includes `.venv/bin/python ...` equivalents beside the local commands.
- Implemented in follow-up: `.github/workflows/ci.yml` now runs the remote-assist demo with the hard-deny network profile and greps the expected allow, deny, revoke, audit, and replay markers.
- Implemented in follow-up: `README.md` now includes a reviewer boundary checklist for Rust verifier status, ROS 2/Isaac Sim scope, hosted-platform exclusions, and controlled-validation wording.

## Recommended fixes

- No protocol behavior fixes are required before controlled technical validation calls.
- Before any broader public release, enable the documented GitHub private vulnerability reporting path or publish the monitored security email, then rerun `./scripts/run_validation_checks.sh` from a clean clone.
- If reviewer friction appears around setup, keep the README quickstart and CI command forms aligned with `python -m pytest` and the venv-qualified variants.
