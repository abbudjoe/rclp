# Assembly Ledger

## T12 Protocol Evals / Adversarial Test Harness - 2026-06-22

Status: successful

Source contract:

- User attachment: `T12 - Protocol Evals / Adversarial Test Harness`
- User instruction: use `assembly`
- `AGENTS.md`
- `DIRECTION.md`
- `docs/ENGINEERING_DOCTRINE.md`
- `docs/SECURITY_DOCTRINE.md`
- `docs/DESIGN_TASTE.md`
- `docs/PROTOCOL_SPEC_DRAFT.md`
- `docs/THREAT_MODEL.md`
- `docs/TEST_STRATEGY.md`
- `README.md`
- `docs/RELEASE_READINESS.md`
- `docs/SAFETY_BOUNDARY.md`
- `docs/RUST_EDGE_VERIFIER.md`
- Existing Python reference code, Rust verifier vectors, tests, examples, and CI

Target contract:

Add a local deterministic adversarial eval harness that answers whether RCLP
fails closed when authority is missing, stale, revoked, replayed, malformed,
mismatched, or unsafe under local context, while producing human-readable and
machine-readable evidence without broad protocol redesign.

Success criterion:

`python tests/evals/eval_runner.py` discovers all required scenarios, executes
them deterministically against the Python reference behavior, validates expected
decision/reason and audit completeness, writes a JSON report, returns nonzero on
failure, and the repo validation gates still pass. Rust parity remains covered
by the existing Rust vector tests and documented relationship unless a Rust CLI
already exists.

Definition of done:

| Item | Status | Evidence |
|---|---|---|
| Eval scenarios exist for the required minimum 24 T12 cases, each with an expected `allow`, `deny`, or `degrade` outcome. | met | `tests/evals/scenarios/` contains 24 YAML scenarios matching the T12 minimum set; `.venv/bin/python tests/evals/eval_runner.py` passed with 24 passed / 0 failed. |
| A deterministic eval runner exists and discovers scenario files without external services, random timestamps, or wall-clock decision inputs. | met | `tests/evals/eval_runner.py` discovers YAML scenarios, uses `now_unix_ms`, validates the required scenario registry and unique names, requires explicit expected decision/reason, and has no network/service dependencies. `src/rclp_core/conformance.py` and `src/rclp_ros2/command_gate.py` now accept an optional explicit `now` for deterministic lease validation while preserving default caller behavior. |
| Runner prints a concise human-readable pass/fail summary. | met | Runner output reports `RCLP evals: 24 passed, 0 failed, 24 total` and one PASS/FAIL line per scenario with decision/reason. |
| Runner writes a machine-readable JSON report. | met | Runner writes `tests/evals/reports/latest.json`; generated JSON reports are ignored by `.gitignore`, while `tests/evals/reports/.gitkeep` preserves the directory. |
| Audit completeness is checked for allow and deny paths, with MVP gaps documented rather than hidden. | met | `audit_allow_complete` and `audit_deny_complete` require mapped audit fields. The runner derives required fields only from `AuditCommit` records and audited payloads, not runner-only objects. `docs/EVALS.md` documents the mapping and known gaps. |
| Multi-step scenario evals exist for network degradation and cloud partition/lease expiry authority transitions. | met | `scenario_network_degrade_revokes.yaml` covers grant, command allow, network degrade, revocation, command rejection, fallback, and audit chain. `scenario_cloud_partition_expiry.yaml` covers grant, pre-partition command allow, partition denial of new authority, partitioned pre-expiry command fail-closed behavior, late post-expiry denial, fallback, and audit chain. |
| Cross-language conformance relationship is documented without making Python evals depend brittly on Cargo. | met | `docs/EVALS.md` explains Python evals as the reference harness and Rust parity through existing shared vectors plus `cargo test --workspace`; Python evals do not invoke Cargo. |
| Existing Python tests still pass. | met | `.venv/bin/python -m pytest` passed with 88 tests after T12 changes; `.venv/bin/python -m compileall src tests` passed. |
| Rust tests still pass if the Rust workspace/toolchain is available. | met | Rust toolchain was available; `cargo fmt --all -- --check`, `cargo clippy --workspace --all-targets -- -D warnings`, and `cargo test --workspace` passed. |
| Eval docs explain purpose, non-goals, run command, report interpretation, fail-closed behavior, Python/Rust relationship, and known gaps. | met | `docs/EVALS.md` documents eval purpose, non-goals, commands, report interpretation, audit completeness, fail-closed rationale, Python/Rust relationship, and known gaps. `tests/evals/README.md` gives developer instructions and scenario kinds. |
| Root README links to eval docs and command with minimal churn. | met | `README.md` quickstart now includes `python tests/evals/eval_runner.py` and links `docs/EVALS.md`. |
| Existing Python CI runs the deterministic eval command. | met | `.github/workflows/ci.yml` now runs `python tests/evals/eval_runner.py` after compile and pytest. |
| Assembly spec-conformance review is clean, with post-review smoke rerun and final ledger update. | met | Initial subagent review found Scenario B partial coverage, missing scenario registry validation, overly synthetic audit completeness, and ledger drift. Fixes addressed each item. Re-review found implementation/docs/tests clean and only this final ledger update missing. Post-review smoke and full gates passed; this ledger entry records final met status and evidence. |

Review status:

- Initial subagent review found four issues: Scenario B did not explicitly
  evaluate partitioned pre-expiry command behavior, the runner could pass with
  missing/zero scenarios or missing expected outcomes, audit completeness could
  be satisfied from runner-only objects, and the ledger was stale.
- Fixes added a required scenario registry and expected-outcome validation,
  derived audit completeness only from audit records and audited payloads,
  expanded Scenario B to include explicit partitioned pre-expiry fail-closed
  behavior, documented the MVP partition semantics, added regression tests, and
  updated the ledger.
- Subagent re-review classified DoD items 1-12 as met and found only this
  final ledger drift remaining. This update closes that finding.

Evidence:

- Preflight `python -m compileall src tests` passed before edits.
- Bare `pytest` and `python -m pytest` failed before edits because the active
  Python environment had no pytest installed.
- `.venv/bin/python -m pip install -e '.[dev]'` passed to create local
  validation environment.
- `.venv/bin/python tests/evals/eval_runner.py` passed: 24 evals passed,
  0 failed, report written to `tests/evals/reports/latest.json`.
- `.venv/bin/python -m pytest tests/test_protocol_evals.py` passed: 4 tests.
- `.venv/bin/python -m compileall src tests` passed after implementation.
- `.venv/bin/python -m pytest` passed: 88 tests.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format . --check` passed: 22 files already formatted.
- `cargo fmt --all -- --check` passed.
- `cargo clippy --workspace --all-targets -- -D warnings` passed.
- `cargo test --workspace` passed: 1 library test, 2 vector tests, 0 doc tests.
- No cloud jobs or paid compute are required for T12, and none will be
  launched, stopped, resized, deleted, or otherwise mutated.

## T11 Release Readiness / Repo Audit - 2026-06-22

Status: successful

Source contract:

- User attachment: `T11 - Release Readiness / Repo Audit`
- User instruction: use `assembly`
- `AGENTS.md`
- `DIRECTION.md`
- all docs under `docs/`
- repository surfaces under `src/`, `tests/`, `examples/`, `manifests/`,
  `agents/`, `isaac_sim/`, `crates/`, and `.github/workflows/`

Target contract:

Make the open protocol MVP externally legible and runnable for a skeptical
robotics/platform engineer without expanding scope beyond repo readiness,
documentation correctness, safety/commercial boundaries, and command evidence.

Success criterion:

A fresh evaluator can understand RCLP in under one minute, run the local demo
and tests, inspect Python and Rust verifier evidence, understand what the MVP
does and does not prove, and see that the repo is ready for controlled
technical validation calls, not production deployment.

Definition of done:

| Item | Status | Evidence |
|---|---|---|
| Root README is externally legible with one-sentence definition, authority-gap problem, MVP demonstrations, explicit non-proofs, quickstart, demo path, repo layout, protocol boundary, commercial boundary, and safety boundary. | met | `README.md` now defines RCLP in one sentence, explains the authority gap, lists what the MVP demonstrates and does not demonstrate, gives Python and Rust quickstarts, documents expected demo markers, maps the repo, and states safety/commercial/protocol boundaries. |
| Quickstart commands are accurate for a fresh local clone, including Python setup, tests, demo, and Rust workspace command when present. | met | `.venv/bin/python -m pytest` passed with 84 tests after editable install; demo commands passed for default and `uplink_bad`; Rust workspace commands passed. Bare `pytest` is not on PATH in this shell, but it resolves after activating `.venv`. |
| Demo flow is documented in `docs/DEMO_SCRIPT.md` with a 5-minute technical validation flow, expected allow/deny/degrade/revoke/audit path, and Rust spike note. | met | `docs/DEMO_SCRIPT.md` covers setup, tests, demo, allow path, deny/revoke/degrade path, audit replay, Python reference vs Rust spike, and unproven boundaries. |
| Safety boundary is explicit in `docs/SAFETY_BOUNDARY.md` and README, using safety-adjacent authority-layer language and no certified-safety claim. | met | `docs/SAFETY_BOUNDARY.md` and `README.md` state that RCLP gates software/agent authority and does not replace certified robot safety systems, obstacle avoidance, braking, emergency stop, or formal safety cases. |
| Commercial boundary is explicit in `docs/COMMERCIAL_BOUNDARY.md` and README, keeping hosted SaaS, carrier/MVNO, customer accounts, billing, and managed platform code out of this repo. | met | `docs/COMMERCIAL_BOUNDARY.md` and `README.md` exclude hosted trust root, customer accounts, billing, managed policy UI, fleet-scale audit backend, carrier/MVNO integrations, managed connectivity, enterprise SSO/IAM, commercial SLAs, and proprietary customer workflows. |
| Rust edge verifier spike is documented accurately as a deterministic spike, not production crypto or a Python replacement. | met | `README.md`, `docs/RELEASE_READINESS.md`, and existing `docs/RUST_EDGE_VERIFIER.md` describe the Rust crate as a deterministic edge verifier spike with offline vectors and test-only HMAC crypto. `cargo test --workspace` passed. |
| Repo does not overclaim production readiness, certified safety, carrier behavior, real cellular behavior, or customer willingness. | met | Wording scan found only explicit non-claims or doctrine examples for safety/production/cellular/customer terms. `docs/SECURITY_REVIEW_NOTES.md` heading was narrowed to blockers before customer pilots / production-profile use so controlled technical validation is not contradicted. |
| Customer validation memo exists and asks for specific technical/customer feedback while stating non-claims. | met | `docs/CUSTOMER_VALIDATION_MEMO.md` includes one-liner, problem statement, MVP proof points, feedback sought, explicit non-claims, and 12 validation questions. |
| Release readiness doc exists with current status, implemented/stubbed surfaces, test/demo commands, known gaps, and before-customer-call checklist. | met | `docs/RELEASE_READINESS.md` includes current MVP status, implemented items, stubbed/scaffolded items, test commands, demo commands, expected evidence, known gaps, and before-customer-call checklist. |
| GitHub/release hygiene is checked: `.gitignore`, `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`, workflows, and community-file scope. | met | `.gitignore` now ignores Rust/build/coverage/artifact outputs; `LICENSE` contains full Apache-2.0 text; `CONTRIBUTING.md` includes Python and Rust validation; `SECURITY.md` exists with MVP limitations and placeholder contact; `.github/workflows/ci.yml` and `rust.yml` already cover Python/Rust gates; no `CODE_OF_CONDUCT.md` was added. |
| Tests and validation commands are run and results reported. | met | Validation evidence is recorded below. Bare `pytest` and bare `ruff` are not on PATH in this shell; repo `.venv` runners passed. |

Review status:

- Subagent spec-conformance review initially found two issues: T11 ledger still
  `in-progress`/`not-started`, and `docs/SECURITY_REVIEW_NOTES.md` used
  "MVP Blockers Before Customer-Facing Use", which could conflict with T11's
  controlled technical-validation target.
- Fixes updated this ledger with final DoD status/evidence and renamed the
  security heading to "Blockers Before Customer Pilots / Production-Profile
  Use" with an explicit controlled-validation carveout.
- Focused re-review returned no remaining findings and classified all 11 T11
  DoD items as met. The review subagent was closed after the clean result.

Evidence:

- `python -m compileall src tests` passed.
- Bare `pytest` failed with `zsh:1: command not found: pytest`; after
  activating/installing the repo virtualenv, `.venv/bin/python -m pytest`
  passed with 84 tests.
- `cargo fmt --all -- --check` passed.
- `cargo clippy --workspace --all-targets -- -D warnings` passed.
- `cargo test --workspace` passed: 1 library test, 2 vector tests, 0 doc tests.
- Bare `ruff check .` failed with `zsh:1: command not found: ruff`; repo
  virtualenv runner `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format . --check` passed: 20 files already formatted.
- `.venv/bin/python -m rclp_agents.demo_remote_assist` passed and showed
  `POLICY_SATISFIED`, `NO_LEASE`, `NETWORK_LATENCY_DEGRADED`,
  `NETWORK_PROFILE_REVOKE`, `LEASE_REVOKED`, `audit_jsonl`, and
  `incident_replay_summary`.
- `.venv/bin/python -m rclp_agents.demo_remote_assist --network-profile uplink_bad`
  passed and showed `NETWORK_UPLINK_TOO_LOW`.
- Overclaim scan found only explicit non-claims or doctrine examples for
  production/safety/cellular/customer terms.
- Secret scan found documented placeholders, deterministic `dev-test-secret`
  vectors, and docs warnings. A local `.env` file exists and is ignored, but
  was not opened.
- `.github/workflows/ci.yml` and `.github/workflows/rust.yml` already run the
  expected Python and Rust gates.
- `/Users/joseph/rclp` is not a Git checkout, so `git status` and `git diff`
  are unavailable in this workspace.

Cloud/job status:

- No cloud jobs or paid compute are required for T11.
- Repository cloud mutation rule reviewed; no launch, stop, delete, resize, or
  other paid-compute mutation will be performed.

## T10 Rust Edge Verifier Spike - 2026-06-22

Status: successful

Source contract:

- User prompt: T10 Rust Edge Verifier Spike
- `AGENTS.md`
- `DIRECTION.md`
- `docs/ENGINEERING_DOCTRINE.md`
- `docs/SECURITY_DOCTRINE.md`
- `docs/DESIGN_TASTE.md`
- `docs/PROTOCOL_SPEC_DRAFT.md`
- `docs/THREAT_MODEL.md`
- `docs/TEST_STRATEGY.md`
- `docs/CONFORMANCE_CHECKLIST.md`
- `docs/API_STYLE.md`
- `docs/ARCHITECTURE.md`
- `docs/NETWORK_FAULT_INJECTION.md`
- `src/rclp_core/models.py`
- `src/rclp_core/leases.py`
- `src/rclp_core/conformance.py`
- `src/rclp_ros2/command_gate.py`
- Existing Python security and protocol tests under `tests/`

Definition of done:

| Item | Status | Evidence |
|---|---|---|
| Rust workspace and `crates/rclp-edge-verifier` library exist with `#![forbid(unsafe_code)]`, minimal dependencies, no async/runtime/network/ROS code, and no filesystem dependency in core verifier logic. | met | Root `Cargo.toml`, `crates/rclp-edge-verifier/Cargo.toml`, and `src/lib.rs` define the Rust workspace/crate; `lib.rs` uses `#![forbid(unsafe_code)]`; core modules avoid filesystem, network, ROS, async runtime, and wall-clock calls. `cargo clippy --workspace --all-targets -- -D warnings` and `cargo test --workspace` passed. |
| Public Rust API exposes a small deterministic edge verifier: `VerificationInput`, `VerificationDecision`, `Decision`, `verify(...)`, `ReplayCache`, and `InMemoryReplayCache`. | met | `crates/rclp-edge-verifier/src/lib.rs` exports `VerificationInput`, `VerificationDecision`, `Decision`, `verify`, `verify_json_value`, `ReplayCache`, `InMemoryReplayCache`, and `TrustedVerifierContext`; vector tests exercise the API. |
| Verifier fails closed for required edge checks: signature/algorithm, expiry/not-yet-valid, revoked lease, replayed nonce, robot/edge/central/mission/capability mismatch, geofence violation, network policy, and malformed input. | met | `verifier.rs` rejects malformed input, unknown algorithm, unknown issuer, invalid signature, not-yet-valid, expired, TTL-too-long, stale, revoked, replayed nonce, robot/agent/mission/capability mismatch, geofence violation, network violations, and missing fallback on network violation; it marks nonces only after allow/degrade. |
| Shared deterministic JSON vectors exist for allow, expiry, revocation, wrong robot, wrong agent, wrong capability, network degradation, geofence violation, replay, malformed signature, and any additional algorithm/time edge cases needed by the verifier. | met | `tests/vectors/edge_verifier/` contains 22 offline JSON vectors covering allow, expiry, revocation, replay, wrong robot/agent/edge/mission/capability, geofence, network degrade, network partition, missing network fallback, malformed signature/input/numeric, unknown algorithm, unknown issuer, stale, and TTL-too-long cases. |
| Rust tests load every shared vector offline and assert expected decision and reason code. | met | `crates/rclp-edge-verifier/tests/vector_tests.rs` loads every vector, checks expected decision, reason code, and audit reason, and has a first-use/second-use replay regression. `cargo test --workspace` passed. |
| Python compatibility hook is lightweight and does not make pytest depend on cargo. | met | `tests/test_rust_edge_vectors.py` validates vector directory shape, expected vector names/reasons, trust-context boundaries, and dev HMAC profile usage using Python JSON only; it does not invoke Cargo. |
| Rust verifier documentation explains purpose, trust boundary, Python-reference relationship, test commands, MVP crypto status, non-goals, and production gaps without claiming production readiness. | met | `docs/RUST_EDGE_VERIFIER.md` and `crates/rclp-edge-verifier/README.md` document the trust boundary, Python reference relationship, explicit trusted-context split, test commands, dev HMAC status, non-goals, and production gaps without production-readiness claims. |
| Required validation and assembly spec review are clean or any environment limitations are explicitly recorded. | met | Post-review gates passed: `cargo fmt --all -- --check`, `cargo clippy --workspace --all-targets -- -D warnings`, `cargo test --workspace`, `python -m compileall src tests`, `.venv/bin/python -m pytest` (84 passed), `.venv/bin/ruff check .`, and `.venv/bin/ruff format . --check`. Bare `python -m pytest` failed because the system Python lacks `pytest`; the repo venv was used for pytest evidence. |

Review status:

- Preflight found T9 conformance docs already present; T10 stayed isolated to the Rust verifier crate, Rust-focused vectors, lightweight Python vector-shape hook, and Rust verifier docs.
- The Rust API uses `TrustedVerifierContext` for trust roots, dev HMAC secret, revocations, explicit verifier time, and local TTL/age limits, keeping observed `local_context` limited to robot/network/geofence state.
- Python reference uses demo Ed25519 helpers; the Rust spike uses the prompt's provisional `RCLP-DEV-HMAC-SHA256` vector signature profile only for deterministic shared vectors and documents the production crypto gap.
- Subagent spec review initially found replay-source parity risk, hard network states able to degrade, missing stale/mission/edge/hard-network vectors, and a trust-boundary/API risk from deserializing trusted verifier material with untrusted input.
- Replay behavior was kept intentionally because the T10 source contract requires first valid nonce use to allow and second use to deny; docs now call this a spike delta from the Python command gate and a v0.1 protocol decision gap.
- Fixes preserved hard denial for partition/detached/unknown profiles, added stale/mission/edge/hard-network and malformed numeric vectors, added a first-use/second-use replay regression, split trust roots/secret/revocations/time/TTL-age policy into `TrustedVerifierContext`, and kept `VerificationInput` to lease/command/observed local state.
- Final review found only a Rust formatting drift; `cargo fmt --all` fixed it, and the reviewer confirmed DoD items 1-8 met with no remaining findings.
- No cloud jobs or paid compute were launched, stopped, resized, deleted, or otherwise mutated.
- `/Users/joseph/rclp` is not a Git checkout, so scoped git staging/status could not be performed in this workspace.

Evidence:

- `cargo fmt --all -- --check` passed.
- `cargo clippy --workspace --all-targets -- -D warnings` passed.
- `cargo test --workspace` passed: 1 library test, 2 vector tests, 0 doc tests.
- `python -m compileall src tests` passed.
- `.venv/bin/python -m pytest` passed: 84 tests.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format . --check` passed: 20 files already formatted.
- Bare `python -m pytest` failed with `No module named pytest`; repo `.venv` runner was used for test evidence.

## T9 Docs + Conformance - 2026-06-22

Status: successful

Source contract:

- `prompts/09_docs_conformance_thread.md`
- `DIRECTION.md` Phase 9 completion criteria
- `AGENTS.md`
- `docs/ENGINEERING_DOCTRINE.md`
- `docs/SECURITY_DOCTRINE.md`
- `docs/DESIGN_TASTE.md`
- `docs/PROTOCOL_SPEC_DRAFT.md`
- `docs/THREAT_MODEL.md`
- `docs/TEST_STRATEGY.md`
- User prompt: T9 Docs + Conformance

Definition of done:

| Item | Status | Evidence |
|---|---|---|
| README quickstart is accurate and enough for a developer to run the local demo in 15 minutes. | met | `README.md` now uses venv setup, `python -m pip install -e '.[dev]'`, `python -m compileall src tests`, `python -m pytest`, default demo, and `--network-profile uplink_bad`; editable install and both demo profiles passed locally. |
| Protocol implementer conformance checklist exists and documents the minimum local conformance profile. | met | `docs/CONFORMANCE_CHECKLIST.md` defines the v0.0.1 local reference profile, required message surface, authority checks, edge enforcement checks, local evidence, and explicit non-proofs. |
| Demo walkthrough exists with expected output and remains honest about local demo scope. | met | `docs/DEMO_WALKTHROUGH.md` documents setup commands, expected stable section markers, expected reason codes for `degraded_teleop`, `uplink_bad`, and `partition`, and local/sim proof safety-adjacent scope. |
| Spec, manifest, examples, and code agree on message names and required fields for the MVP implementation surface. | met | `docs/PROTOCOL_SPEC_DRAFT.md`, `manifests/rclp_protocol_manifest.yaml`, `src/rclp_core/models.py`, `examples/audit/sample_replay.json`, and `examples/scenarios/network_degrade.yaml` now align on `AgentAttestation`, `NetworkStateAssertion`, `AuditCommit`, `audit_commit`, signature field presence, current network-profile behavior, and full audit commit fields; `tests/test_conformance_contract.py` checks manifest/model fields, spec field mentions, audit sample hash-chain validity, stable event types, and scenario policy behavior. |
| Release checklist exists for v0.0.1 and v0.1.0. | met | `docs/RELEASE_CHECKLIST.md` defines v0.0.1 local protocol proof gates and v0.1.0 public protocol seed gates; README, roadmap, and governance docs link to it. |
| Repo remains narrow and honest: no hosted SaaS, MVNO, fleet manager, teleop media, or certified-safety claims. | met | New docs explicitly scope out hosted SaaS, carrier/MVNO, fleet management, teleop media, field safety, real cellular behavior, and certified safety; spec and checklist call trust-boundary signature verification gaps v0.1 hardening items. |
| Required validation and spec-conformance review are clean. | met | Initial subagent review found signature/profile, example, ledger, and conformance-test depth gaps; fixes closed all findings. Final re-review classified DoD items 1-6 as met and item 7 as partial only pending this ledger update. Post-fix local gates passed: compileall, full pytest, ruff check, ruff format check, conformance tests, and both demo profiles. |

Review status:

- Initial subagent review found four issues: missing signature/profile clarity for `NetworkStateAssertion` and `FallbackDeclaration`, abridged examples that contradicted full required fields, stale ledger status, and shallow conformance tests.
- Fixes added `FallbackDeclaration.signature`, completed signature fields in the manifest, clarified v0.0.1 local trust-boundary limits, expanded API examples to include common envelopes, replaced the audit sample with full `AuditCommit` fixtures, and strengthened conformance tests.
- Subagent re-review found the signature/profile, example, and conformance-test issues resolved; only this final ledger update remained.

Evidence:

- `.venv/bin/python -m pip install -e '.[dev]'` passed.
- `python -m compileall src tests` passed.
- Bare `python -m pytest` failed because the system Python lacks `pytest`; repo `.venv` runner was used for test evidence after editable install.
- `.venv/bin/python -m pytest tests/test_conformance_contract.py` passed: 5 tests.
- `.venv/bin/python -m pytest` passed: 82 tests.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format . --check` passed: 19 files already formatted.
- `.venv/bin/python -m rclp_agents.demo_remote_assist` passed and showed `POLICY_SATISFIED`, `NO_LEASE`, `NETWORK_LATENCY_DEGRADED`, `NETWORK_PROFILE_REVOKE`, `LEASE_REVOKED`, `audit_jsonl`, and `incident_replay_summary`.
- `.venv/bin/python -m rclp_agents.demo_remote_assist --network-profile uplink_bad` passed and showed `NETWORK_UPLINK_TOO_LOW`.
- Workspace is not a Git checkout, so `git status` and `git diff` were unavailable.
- No cloud jobs or paid compute were launched, stopped, resized, deleted, or otherwise mutated for T9.

## T8 Security Red Team - 2026-06-22

Status: successful

Source contract:

- `prompts/08_security_redteam_thread.md`
- `DIRECTION.md` Phase 8 completion criteria
- `AGENTS.md`
- `docs/SECURITY_DOCTRINE.md`
- `docs/THREAT_MODEL.md`
- `docs/TEST_STRATEGY.md`
- `docs/PROTOCOL_SPEC_DRAFT.md`
- User prompt: T8 Security Red Team

Definition of done:

| Item | Status | Evidence |
|---|---|---|
| Negative tests cover replay, stale request/lease, wrong agent, wrong robot, wrong mission, wrong capability, expired lease, revoked lease, invalid signature, unknown agent/issuer/revoker, compromised central-agent escalation, and policy downgrade. | met | `tests/test_security_negative_paths.py` covers replayed request nonce, invalid request signature, authenticated-agent mismatch, stale request, stale lease, wrong agent/robot/mission/capability lease replay, expired lease, revoked lease, invalid lease signature, unknown requesting agent, unknown issuer, unknown revoker, compromised known central-agent escalation with audit, empty-scope policy downgrade, and permissive policy digest downgrade. |
| Threat model and security doctrine reflect the new negative cases. | met | `docs/THREAT_MODEL.md`, `docs/SECURITY_DOCTRINE.md`, `docs/TEST_STRATEGY.md`, and `docs/PROTOCOL_SPEC_DRAFT.md` now describe request auth, replay, staleness, wrong agent/context, trusted issuer/revoker, accepted policy digests, and remaining signed-bundle/signature hardening. |
| Unsafe docs wording is reviewed and production-safety overclaims are removed. | met | Policy id changed to `remote-assist-authority-v0`; docs examples use network suitability and fallback-hook language; wording scan found only conservative non-claim language such as `Sim proof is not field-proven safety`. |
| Security review notes separate MVP blockers from future hardening. | met | `docs/SECURITY_REVIEW_NOTES.md` lists fixed T8 controls, P0/P1 blockers, and future hardening. |
| No heavy dependencies are introduced. | met | `pyproject.toml` dependency set remains Pydantic, PyYAML, and cryptography; implementation uses existing stdlib/Pydantic/cryptography paths. No Git diff was available because this workspace is not a Git checkout. |

Review status:

- Initial subagent review found missing authenticated request handling, incomplete permissive policy downgrade coverage, missing wrong-agent/compromised-central tests, and stale ledger evidence.
- Fixes added signed `CapabilityRequest` verification, accepted policy digest checks, wrong-agent and compromised-central tests, and updated security docs.
- Re-review classified all T8 DoD items as met, with two remaining findings: stale `central_agent_mock` unsigned request helper and stale T8 ledger.
- Final fixes made `request_remote_assist()` require a `DemoKeyPair` and emit signed requests, added a regression proving the mock satisfies the policy contract, and updated this ledger.

Evidence:

- `python -m compileall src tests` passed.
- `.venv/bin/python -m pytest` passed: 77 tests.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format .` reported 18 files unchanged after final fixes.
- Bare `pytest`, `ruff check .`, and `ruff format .` are not on PATH in this shell; repo `.venv` runners were used for test/lint evidence.
- No cloud jobs or paid compute were launched, stopped, resized, deleted, or otherwise mutated.

## T7 Isaac Sim on Lambda - 2026-06-22

Status: successful

Source contract:

- `prompts/07_isaac_sim_lambda_thread.md`
- `DIRECTION.md` Phase 7 completion criteria
- `docs/LAMBDA_ISAAC_SIM_SETUP.md`
- `docs/ARCHITECTURE.md`
- `isaac_sim/README.md`
- `AGENTS.md`
- `docs/ENGINEERING_DOCTRINE.md`
- `docs/SECURITY_DOCTRINE.md`
- `docs/DESIGN_TASTE.md`
- `docs/PROTOCOL_SPEC_DRAFT.md`
- `docs/THREAT_MODEL.md`
- `docs/TEST_STRATEGY.md`
- User prompt: T7 Isaac Sim on Lambda

Definition of done:

| Item | Status | Evidence |
|---|---|---|
| Lambda setup checklist is explicit enough for a fresh engineer and includes safe commands. | met | `docs/LAMBDA_ISAAC_SIM_SETUP.md` now includes local preflight, optional `.env` sourcing, read-only Lambda API smoke, explicit paid-compute launch template with operator-action warning, instance bootstrap, Isaac source decision tree, verification commands, ROS 2 checks, bridge guidance, launch templates, evidence capture, and cleanup notes. |
| Isaac Sim ROS 2 bridge approach is documented. | met | `docs/LAMBDA_ISAAC_SIM_SETUP.md` documents ROS 2 as transport around `src/rclp_ros2/command_gate.py`; `isaac_sim/scenarios/remote_assist_gate.md` names candidate, accepted, fallback, and audit topics. |
| Minimal simulated robot scenario plan exists. | met | `isaac_sim/scenarios/remote_assist_gate.md` defines objective, authority contract, topology, preconditions, minimal scene, steps, expected results, evidence, and rejection conditions. |
| First Isaac milestone gates simulated commands and avoids full autonomy, real cellular, or certified safety claims. | met | Lambda checklist, Isaac README, and scenario all constrain the milestone to simulated `remote_assist` command gating with deterministic network profiles and explicitly reject full autonomy, real cellular validation, certified safety claims, fleet dispatch, and hosted SaaS scope. |
| Script placeholders launch or prepare local RCLP demo next to Isaac/ROS 2 without credentials or account-specific values. | met | `setup_lambda_instance.sh` runs a credential-free prerequisite check; `run_local_protocol_demo.sh` runs the local proof with configurable deterministic profile; `run_ros2_gate_demo.sh` prints the ROS 2 adapter contract and runs the local proof next to the ROS 2/Isaac shell context. |
| No Lambda credentials, account IDs, SSH keys, private keys, or account-specific details are hardcoded. | met | Touched docs/scripts use environment-variable placeholders only; targeted secret-pattern scan found no explicit Lambda API key assignments, literal bearer tokens, SSH keys, private key headers, or account ID strings. |

Review status:

- Initial subagent review found the Isaac install/launch path too vague, `.env` sourcing too brittle, and the ledger not updated.
- Fixes added optional `.env` sourcing, a credential-free Isaac source decision tree, `ISAAC_SIM_ROOT` verification, ROS 2 doctor checks, bridge extension/version guidance, launch command templates, and official reference links.
- Subagent re-review classified all six T7 DoD items as met; the only remaining finding was ledger drift, fixed in this final ledger update.

Evidence:

- `bash -n isaac_sim/scripts/*.sh` passed.
- `python -m compileall src tests` passed.
- `.venv/bin/python -m pytest` passed: 52 tests.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format .` reported 17 files unchanged.
- `isaac_sim/scripts/setup_lambda_instance.sh` passed locally and did not read Lambda credentials.
- `isaac_sim/scripts/run_local_protocol_demo.sh` passed and printed `command_allowed`, `NO_LEASE` rejection, degraded decision, revocation, `LEASE_REVOKED` rejection, `audit_jsonl`, and `incident_replay_summary`.
- `isaac_sim/scripts/run_ros2_gate_demo.sh` passed locally, printed the ROS 2 adapter placeholder contract, noted ROS 2 was not on PATH in this local shell, and ran the local RCLP proof.
- Targeted secret-pattern scan over touched docs/scripts found no matches.
- No Lambda instance was launched, stopped, resized, deleted, or otherwise mutated during this work.

Live Lambda/Isaac evidence, 2026-06-22:

- User requested the proof be run on Isaac Sim in Lambda; existing active Lambda instance `real2sim-b1-live-stream-r2` was reused rather than launching new paid compute.
- Cloud run ledger updated at `~/.codex/cloud_runs/ledger.jsonl` under run id `rclp-t7-isaac-remote-assist-gate-r1`.
- Runner: Lambda `gpu_1x_a10` in `us-east-1`, NVIDIA A10 visible through `nvidia-smi`; Isaac stream container `real2sim-isaac-stream-r2` stayed healthy.
- Isaac environment: container image `nvcr.io/nvidia/isaac-sim:6.0.0`; `/isaac-sim/VERSION` reported `6.0.0-rc.59+release.41464.5f2772bc.gl`; `/isaac-sim/python.sh` reported Python 3.12.13; ROS 2 bridge extension present at `/isaac-sim/exts/isaacsim.ros2.bridge`; `ros2` CLI was not on PATH.
- Proof was run inside the Isaac Sim container with `PYTHONPATH=src` and `PYTHON_BIN=/isaac-sim/python.sh`.
- Container `python -m compileall src tests` passed after fixing staging issues by excluding macOS AppleDouble files and chowning the staged repo.
- `isaac_sim/scripts/setup_lambda_instance.sh` passed inside the container and captured GPU/Isaac environment evidence.
- `isaac_sim/scripts/run_local_protocol_demo.sh` passed inside the container and produced `command_gate_with_valid_lease`, `command_without_valid_lease`, `impaired_network_decision`, `lease_revocation`, `command_gate_after_network_revocation`, `audit_jsonl`, and `incident_replay_summary`.
- `isaac_sim/scripts/run_ros2_gate_demo.sh` passed inside the container; it noted `ros2` was not on PATH and then ran the local RCLP proof next to the Isaac shell context.
- Proof markers were all `True`: valid lease allow, `NO_LEASE` rejection, `NETWORK_LATENCY_DEGRADED`, revocation, `LEASE_REVOKED` rejection, `audit_jsonl`, and `incident_replay_summary`.
- Artifacts copied to `artifacts/lambda_t7_remote_assist_gate_r1/`: `environment.txt`, `compileall.txt`, `setup_lambda_instance.txt`, `run_local_protocol_demo.txt`, `run_ros2_gate_demo.txt`, `proof_markers.txt`, `remote_postrun_status.txt`, and `SHA256SUMS.txt`.
- No Lambda credentials, account-specific values, or private keys were copied into the staged repo or artifacts.
- The preexisting Lambda instance was left running because it belonged to an existing live Isaac stream run; no instance launch or termination was performed for this proof.

## T6 Audit + Incident Replay - 2026-06-22

Status: successful

Source contract:

- `prompts/06_audit_replay_thread.md`
- `DIRECTION.md` Phase 6 completion criteria
- `docs/API_STYLE.md`
- `docs/THREAT_MODEL.md`
- `src/rclp_core/audit.py`
- `AGENTS.md`
- `docs/ENGINEERING_DOCTRINE.md`
- `docs/SECURITY_DOCTRINE.md`
- `docs/DESIGN_TASTE.md`
- `docs/PROTOCOL_SPEC_DRAFT.md`
- `docs/TEST_STRATEGY.md`
- User prompt: T6 Audit + Incident Replay

Definition of done:

| Item | Status | Evidence |
|---|---|---|
| Stable audit event types are defined for request, state, allow, deny, degrade, revoke, fallback, command allow, command rejection, and diagnostics. | met | `AuditEventType` in `src/rclp_core/models.py` defines stable event names; `test_audit_event_type_is_stable_enum` rejects freeform event strings. |
| Audit log supports JSONL export and load. | met | `AuditLog.to_jsonl()`, `write_jsonl()`, and `load_jsonl()` support round trip and validate required fields, payload hashes, duplicate audit IDs, and hash-chain integrity; tests cover round trip, missing `payload_hash`, tampered hash, tampered chain, and duplicates. |
| Replay summarizer groups events by correlation ID and summarizes request -> state -> decision -> enforcement -> revocation -> fallback. | met | `AuditLog.replay()` returns typed per-correlation buckets; `replay_summary()` prints request, state, decision, enforcement, revocation, fallback, and diagnostic groups; demo output shows the full chain. |
| Allow, deny, revoke, fallback, and command rejection paths emit audit events. | met | Public `evaluate_policy()` requires an `AuditLog`; `CommandGate` emits `command_allowed`, `command_rejected`, `lease_revoked`, `revocation_rejected`, and `fallback_declared`; `EdgeAgentDaemon` audits edge-agent mismatch rejection. |
| Demo prints replay summary. | met | `.venv/bin/python -m rclp_agents.demo_remote_assist` prints `audit_jsonl` and structured `incident_replay_summary`; `tests/test_demo_remote_assist.py` asserts replay sections and reason codes. |
| Audit event schema is documented. | met | `docs/PROTOCOL_SPEC_DRAFT.md` documents `AuditCommit` required fields, stable event types, authority relevance, related IDs, state refs, payload hash, and integrity proof requirements. |
| No silent security-relevant decisions. | met | `test_public_policy_evaluation_requires_audit_log`, policy causal tests, command allow/reject/revoke/fallback tests, revocation rejection tests, and edge mismatch test cover authority paths; authority event types cannot be demoted out of audit context. |

Review status:

- Initial subagent review classified JSONL validation, structured replay, policy audit enforcement, state refs, and raw revocation context as partial.
- Fixes implemented in `src/rclp_core/audit.py`, `src/rclp_core/policy.py`, `src/rclp_ros2/command_gate.py`, `src/rclp_agents/edge_agent_daemon.py`, `src/rclp_agents/demo_remote_assist.py`, protocol docs, and tests.
- Second subagent review found two remaining issues: `revocation_rejected` could be demoted via `authority_relevant=False`, and JSONL load could repair missing `payload_hash`.
- Final fixes enforced authority event relevance, moved no-context revocation rejection to `diagnostic`, and validated required raw JSONL fields before Pydantic defaults.
- Final subagent re-review returned no remaining actionable findings and classified all T6 DoD items as met.

Evidence:

- Bare `python -m compileall src tests` passed.
- Bare `pytest` is not installed on PATH in this shell (`zsh: command not found: pytest`); repo `.venv` runner was used for test evidence.
- `.venv/bin/python -m compileall src tests` passed.
- `.venv/bin/python -m pytest` passed: 52 tests.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format .` reported 17 files unchanged after final fixes.
- `.venv/bin/python -m rclp_agents.demo_remote_assist` passed and printed structured `incident_replay_summary` with requests, states, decisions, enforcement, revocations, fallbacks, and diagnostics.

## T5 Network Fault Injection - 2026-06-22

Status: successful

Source contract:

- `prompts/05_network_fault_injection_thread.md`
- `DIRECTION.md` Phase 5 completion criteria
- `docs/TEST_STRATEGY.md`
- `docs/LAMBDA_ISAAC_SIM_SETUP.md`
- `AGENTS.md`
- `docs/ENGINEERING_DOCTRINE.md`
- `docs/SECURITY_DOCTRINE.md`
- `docs/DESIGN_TASTE.md`
- `docs/PROTOCOL_SPEC_DRAFT.md`
- `docs/THREAT_MODEL.md`
- User prompt: T5 Network Fault Injection

Definition of done:

| Item | Status | Evidence |
|---|---|---|
| Deterministic network profiles exist for `normal`, `degraded_teleop`, `uplink_bad`, and `partition`. | met | `NetworkProfile` and deterministic `PROFILES` live in `src/rclp_core/models.py` and `src/rclp_core/network.py`; `test_deterministic_network_profiles_are_typed_and_stable` proves typed lookup, copy isolation, and profile values. |
| Policy evaluation can allow, degrade, or deny from explicit latency, packet loss, uplink, attachment, and unknown-state inputs. | met | `NetworkRequirements` now has allow and hard-deny thresholds; tests cover normal allow, soft latency/loss/uplink degradation, `uplink_bad` denial, `partition` denial, and `NETWORK_STATE_UNKNOWN` denial. |
| Edge command enforcement can reject a previously valid lease when current network state violates lease constraints. | met | `validate_lease_against_state()` rejects unknown, detached, high latency, high packet loss, and low uplink current state; tests cover degraded, `uplink_bad`, `partition`, and unknown current state. |
| Linux `tc netem` usage is documented as optional and not required by tests. | met | `docs/NETWORK_FAULT_INJECTION.md` documents optional manual `tc netem` examples and states automated tests MUST NOT require root, external network calls, or host network changes; `docs/LAMBDA_ISAAC_SIM_SETUP.md` links to it. |
| Demo can switch network profile and show policy effect. | met | `python -m rclp_agents.demo_remote_assist --network-profile <profile>` supports impaired profile selection; tests assert default `degraded_teleop` returns `degrade` and `uplink_bad` returns `deny`; manual evidence covered `partition`. |

Review status:

- Initial subagent review found unknown network state was not conservative, T5 ledger was still in-progress, and `docs/TEST_STRATEGY.md` wording drifted from soft-degrade behavior.
- Fixes implemented in `src/rclp_core/policy.py`, `src/rclp_core/conformance.py`, `tests/test_protocol_flow.py`, and `docs/TEST_STRATEGY.md`.
- Final subagent re-review returned no remaining findings and classified all T5 DoD items as met.

Evidence:

- `.venv/bin/python -m compileall src tests` passed after review fixes.
- `.venv/bin/python -m pytest tests/test_demo_remote_assist.py tests/test_protocol_flow.py` passed: 39 tests after review fixes.
- `.venv/bin/python -m pytest` passed: 40 tests after review fixes.
- `.venv/bin/ruff check .` passed after review fixes.
- `.venv/bin/ruff format .` reported 17 files unchanged after review fixes.
- `.venv/bin/python -m rclp_agents.demo_remote_assist --network-profile partition` passed and showed `NETWORK_DETACHED` with `local_autonomy_only` through decision, revocation, fallback declaration, and final command rejection.

## T4 Central Agent + Demo Flow - 2026-06-22

Status: successful

Source contract:

- `README.md`
- `docs/API_STYLE.md`
- `DIRECTION.md` Phase 4 completion criteria
- `AGENTS.md`
- `docs/ENGINEERING_DOCTRINE.md`
- `docs/SECURITY_DOCTRINE.md`
- `docs/DESIGN_TASTE.md`
- `docs/PROTOCOL_SPEC_DRAFT.md`
- `docs/THREAT_MODEL.md`
- `docs/TEST_STRATEGY.md`
- User prompt: T4 Central Agent + Demo Flow

Definition of done:

| Item | Status | Evidence |
|---|---|---|
| Demo creates central and edge agent identities. | met | `demo_remote_assist` prints structured `central_agent` and `edge_agent` identity objects; `tests/test_demo_remote_assist.py` asserts both IDs. |
| Demo creates a robot, mission, geofence, and policy. | met | Demo setup output includes `RobotIdentity`, `MissionContext`, `GeofenceState`, policy id/path, and network thresholds; regression test asserts each. |
| Demo requests `remote_assist` under normal network conditions and shows an allowed lease. | met | Demo prints `capability_request` and `normal_network_decision` with `decision: allow`, `POLICY_SATISFIED`, signed `remote_assist` lease; regression test asserts lease and signature. |
| Demo degrades network conditions and shows denial or revocation. | met | Demo prints `degraded_network_decision` with stable network reason and safe alternative, then structured `lease_revocation`; regression test asserts both. |
| Demo attempts a command without a valid lease and shows rejection. | met | Demo prints API-style `command_without_valid_lease` denial envelope with `NO_LEASE`, audit id, safe alternative, retry semantics, and gate result; regression test asserts rejection. |
| Demo emits audit JSONL or structured console output. | met | Demo emits structured JSON sections and an `audit_jsonl` block; regression test parses every audit line and asserts the causal event order and correlation id. |
| Demo prints a concise incident replay summary. | met | Demo prints `incident_replay_summary` from `AuditLog.replay_summary()`; regression test asserts request, allow, missing-lease rejection, degraded denial, and revocation rejection appear. |
| Demo runs with no external services and avoids formal safety certification claims. | met | `.venv/bin/python -m rclp_agents.demo_remote_assist` runs locally; output explicitly says RCLP is a safety-adjacent authority layer, not a certified safety system. |

Review status:

- Initial subagent review found ledger status drift, incomplete API-style command rejection output, and fallback correlation-id drift.
- Fixes implemented in `src/rclp_agents/demo_remote_assist.py`, `src/rclp_ros2/command_gate.py`, `tests/test_demo_remote_assist.py`, and `tests/test_protocol_flow.py`.
- Final subagent re-review returned no remaining findings and classified all T4 DoD items as met.

Evidence:

- `.venv/bin/python -m pytest tests/test_demo_remote_assist.py tests/test_protocol_flow.py tests/test_audit.py` passed: 27 tests before review fixes.
- `.venv/bin/python -m pytest` passed: 29 tests after review fixes.
- `.venv/bin/python -m compileall src tests` passed after review fixes.
- `.venv/bin/ruff check .` passed after review fixes.
- `.venv/bin/ruff format .` reported 17 files unchanged after review fixes.
- `.venv/bin/python -m rclp_agents.demo_remote_assist` passed and produced structured setup, request, decision, gate, revocation, audit JSONL, and replay sections.
- Bare `python -m compileall src tests` passed.
- Bare Homebrew `python -m rclp_agents.demo_remote_assist` is not runnable in this shell until the package and dependencies are installed for that interpreter; README quickstart uses editable install first, and the repo `.venv` runner passes.

## T3 Edge Agent + Command Gate - 2026-06-22

Status: successful

Source contract:

- `prompts/03_edge_agent_command_gate_thread.md`
- `AGENTS.md`
- `docs/ARCHITECTURE.md`
- `docs/SECURITY_DOCTRINE.md`
- `docs/PROTOCOL_SPEC_DRAFT.md`
- `docs/TEST_STRATEGY.md`

Definition of done:

| Item | Status | Evidence |
|---|---|---|
| Command gate accepts only a valid, unexpired lease matching robot, mission, agent, edge agent, and capability. | met | `CommandGate.evaluate()` delegates to `validate_lease_for_command`; valid lease test passes and allow results do not emit fallback declarations. |
| Command gate rejects commands with no valid lease. | met | Tests cover no lease, expired lease, revoked lease, wrong robot, wrong mission, wrong capability, invalid signature, missing constraints, degraded state, and wrong geofence. |
| Revocation handling invalidates future command use of a lease. | met | `CommandGate.revoke()` records revocations, accepts `LeaseRevocation`, rejects mismatched revocation/lease context, and causes future use to return `LEASE_REVOKED`. |
| Deny, revoke, and degrade paths emit fallback declarations as events, not certified safety controls. | met | Deny/degrade/revoke tests assert emitted `FallbackDeclaration` objects through `GateResult`, in-memory `fallback_events`, and optional `fallback_sink`. Invalid leases cannot choose fallback action from untrusted constraints. |
| ROS 2 integration remains a scaffold and unit tests do not require ROS 2. | met | `src/rclp_ros2/command_gate.py` remains dependency-light and ROS-agnostic; tests run with plain Python/Pydantic and no ROS 2 imports. |

Evidence:

- `python -m compileall src tests` passed.
- Bare `pytest` is not installed on PATH in this checkout.
- `.venv/bin/python -m pytest` passed: 26 tests.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format .` completed with 16 files unchanged.
- Subagent spec review was not spawned because the available multi-agent tool requires an explicit user request for subagents; main-agent spec conformance was checked against the T3 prompt and repo doctrine.

## T1 Protocol Spec - 2026-06-22

Status: successful

Source contract:

- `prompts/01_protocol_spec_thread.md`
- `AGENTS.md`
- `docs/PROTOCOL_SPEC_DRAFT.md`
- `docs/THREAT_MODEL.md`
- `docs/GOVERNANCE.md`

Definition of done:

| Item | Status | Evidence |
|---|---|---|
| Refine definitions for CapabilityRequest, CapabilityDecision, CapabilityLease, LeaseRevocation, NetworkStateAssertion, FallbackDeclaration, and AuditCommit. | met | `docs/PROTOCOL_SPEC_DRAFT.md` defines purpose, required fields, normative behavior, rejection conditions, and audit impact for all seven messages. |
| Add useful normative MUST/SHOULD/MAY language while keeping the spec narrow. | met | Spec is scoped to the authority question and avoids fleet dispatch, low-level safety, and hosted platform requirements. |
| Add rejection conditions for each named message. | met | Mechanical doc audit confirmed rejection sections for all seven messages. |
| Add comparison section for ROS 2 security, VDA5050, Open-RMF, and MCP/A2A as substrates or adjacent protocols, not replacements. | met | `Relationship to Adjacent Protocols` section added. |
| Add open questions and avoid overclaiming. | met | `MVP Assumptions` and `Open Questions` sections added; safety language remains safety-adjacent and conservative. |
| Keep commercial hosted platform features out of required spec behavior. | met | Only hosted/SaaS mention is a non-goal. |
| Run required validation commands. | met | `.venv/bin/python -m compileall src tests` passed; `.venv/bin/python -m pytest` passed with 8 tests. Bare `pytest` is not installed on PATH, so the repo `.venv` runner was used. |
| Complete spec-conformance review. | met | Subagent review findings were fixed; final reviewer confirmation classified T1 DoD as met. |

Evidence:

- `python -m compileall src tests` passed with the active system Python.
- `.venv/bin/python -m compileall src tests` passed.
- `.venv/bin/python -m pytest` passed: 8 tests.
- `.venv/bin/ruff check .` passed.
- Mechanical doc audit confirmed all seven named messages include required fields, rejection conditions, audit impact, and normative language.
- Subagent review fixed revocation/fallback coupling, common envelope strength, safe-alternative consistency, revocation message separation, and audit integrity proof requirements.
- Final subagent confirmation: no blocker; T1 DoD met.
