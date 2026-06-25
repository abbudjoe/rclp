# S1 — Fresh-clone Reproducibility Review

## Verdict

GREEN

## Summary

- A skeptical robotics/platform engineer can clone the repo, understand the RCLP primitive quickly, install the declared dev dependencies, run the Python tests, run the deterministic evals, run the demo, and run the Rust verifier checks.
- The README explains the project in under one minute: it states the authority primitive, the MVP proof, the non-goals, quickstart commands, demo markers, safety boundary, and commercial boundary.
- The MVP claim is supported for controlled technical validation: short-lived, locally enforced capability leases conditioned on identity, mission, geofence, network state, and fallback policy.
- The repo does not overclaim production safety, real cellular behavior, field validation, ROS 2 runtime integration, Isaac Sim execution, or hosted commercial-platform readiness.
- I would be comfortable sending this repo to a technical reviewer for controlled validation calls after running the packaged validation script in the target checkout.

## Commands run

- `python -m venv .venv` — passed.
- `.venv/bin/python -m pip install -e '.[dev]'` — passed; installed declared Python/dev dependencies.
- `.venv/bin/python -m compileall src tests` — passed.
- `.venv/bin/python -m pytest` — passed: 246 tests.
- `.venv/bin/python tests/evals/eval_runner.py` — passed: 33 eval scenarios, 0 failed; wrote `tests/evals/reports/latest.json`.
- `.venv/bin/python -m rclp_agents.demo_remote_assist` — passed; showed allow, no-lease deny, degraded-network decision, revocation, post-revocation deny, audit JSONL, and incident replay summary.
- `cargo fmt --all -- --check` — passed.
- `cargo clippy --workspace --all-targets -- -D warnings` — passed.
- `cargo test --workspace` — passed: 3 Rust unit tests and 47 vector tests.
- `./scripts/run_validation_checks.sh` — passed end to end, including compileall, pytest, evals, Ruff, Rust fmt, Rust clippy, and Rust tests.
- `./scripts/run_validation_demo.sh --network-profile uplink_bad` — passed; hard-deny path showed `NETWORK_UPLINK_TOO_LOW`, revocation, `LEASE_REVOKED`, fallback declarations, audit JSONL, and replay summary.
- `git status --short` — clean before adding this review report; ignored generated artifacts did not appear.
- `git ls-files --others --exclude-standard` — no untracked required files before adding this review report.
- `rg -n "/Users/|/home/|AWS_|SECRET|TOKEN|PRIVATE KEY|BEGIN .*KEY|lambda|Lambda|TODO|FIXME" .` — inspected local-path/secret/setup-risk patterns; findings were documented Lambda/Isaac guidance, clearly labeled test secrets, and the `SECURITY.md` contact TODO, not committed production credentials.

## What worked

- Quickstart is complete and accurate for a local Python 3.11+ environment. I used Python 3.14.4 in a fresh `.venv`, and the documented install/test/demo commands worked.
- `scripts/run_validation_checks.sh` is a good reviewer-facing command because it exercises Python compile, pytest, deterministic evals, Ruff, and Rust checks when Cargo is installed.
- The demo actually demonstrates the intended flow: signed request, `POLICY_SATISFIED` allow, `LEASE_VALID` command gate allow, `NO_LEASE` deny, `NETWORK_LATENCY_DEGRADED` or `NETWORK_UPLINK_TOO_LOW`, `NETWORK_PROFILE_REVOKE`, `LEASE_REVOKED`, fallback hook declaration, `audit_jsonl`, and `incident_replay_summary`.
- The eval suite is deterministic and local. It discovered 33 YAML scenarios and explicitly covers missing, stale, expired, revoked, replayed, malformed, mismatched, geofence, network, current-state, speed, revocation, audit, degradation, and partition/expiry paths.
- Rust verifier checks are present and deterministic. The workspace consumes shared vectors under `tests/vectors/edge_verifier/` and clearly labels its HMAC profile as test-only.
- CI workflows exist for both Python and Rust and cover the core Python/Rust validation checks. Ruff and demo execution are covered by the local packaged validation/demo scripts rather than the current CI workflows.
- No untracked required files were present before adding this report. Generated artifacts are ignored: `.venv/`, `target/`, egg-info, pytest/Ruff caches, and `tests/evals/reports/latest.json`.
- Secret/path scan did not find committed production secrets. The visible HMAC strings are in test vectors and documented as non-production. Lambda/Isaac docs use operator placeholders and warnings rather than committed credentials.

## What failed or was confusing

- No validation command failed in this environment.
- The packaged validation script fails if dev dependencies have not been installed, because Ruff is treated as required. It prints a helpful install command, so this is acceptable but worth calling out in demos.
- `compileall src tests` lists ignored `src/rclp.egg-info` after editable install. This is harmless, but a fresh reviewer may notice it.
- The demo output is intentionally verbose. It proves the audit chain well, but for a live call the speaker should know which markers to point at rather than scrolling through all JSON.
- `SECURITY.md` still contains a TODO for a public security contact. That is not a blocker for controlled technical validation, but it should be fixed before public launch.
- Isaac Sim and ROS 2 are clearly scoped as scaffold/POC surfaces, not runnable proof paths. That is documented correctly, but the reviewer should not infer simulator or robot integration from the local proof.

## Blocking issues before customer calls

- None for controlled technical validation calls, assuming the presenter runs `./scripts/run_validation_checks.sh` in the checkout that will be shown.

## Non-blocking improvements

- Add a short "what to point at in demo output" block to the README or demo script with the exact section names and reason codes.
- Consider adding a one-line note that `./scripts/run_validation_checks.sh` expects `python -m pip install -e '.[dev]'` to have been run first.
- Consider adding a concise sample eval summary to `docs/EVALS.md` so reviewers know what success looks like before running it.
- Replace the `SECURITY.md` contact TODO before public distribution.
- Keep repeating that Rust is a verifier spike with test-only HMAC vectors and that Isaac Sim/ROS 2 remain scaffolded.

## Recommended fixes

- No blocking code or command fixes are required.
- For reviewer polish, add a compact demo-marker checklist near the README demo command:
  `POLICY_SATISFIED`, `LEASE_VALID`, `NO_LEASE`, `NETWORK_LATENCY_DEGRADED`, `NETWORK_UPLINK_TOO_LOW`, `NETWORK_PROFILE_REVOKE`, `LEASE_REVOKED`, `audit_jsonl`, and `incident_replay_summary`.
- Before any broader public release, replace the security-contact TODO and rerun the full validation script from a clean clone.
