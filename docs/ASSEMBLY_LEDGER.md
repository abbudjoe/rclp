# Assembly Ledger

## S4 Fresh Open-source / Commercial-boundary Review - 2026-06-25

Status: successful

Source contract:

- User request: perform the S4 open-source / commercial-boundary review and
  write `docs/reviews/codex_simulated_review/S4_open_source_commercial_boundary.md`
  using `assembly`.
- Target state: controlled external technical validation, not public
  standardization or production deployment.
- `AGENTS.md`
- `README.md`
- `LICENSE`
- `SECURITY.md`
- `CONTRIBUTING.md`
- `docs/COMMERCIAL_BOUNDARY.md`
- `docs/GOVERNANCE.md`
- `docs/SAFETY_BOUNDARY.md`
- `docs/CUSTOMER_VALIDATION_MEMO.md`
- `docs/VALIDATION_RELEASE_NOTES.md`
- `docs/ENGINEERING_DOCTRINE.md`
- `docs/SECURITY_DOCTRINE.md`
- `docs/DESIGN_TASTE.md`
- `docs/PROTOCOL_SPEC_DRAFT.md`
- `docs/THREAT_MODEL.md`
- `docs/TEST_STRATEGY.md`

Preflight note:

- No cloud jobs, GPU jobs, Lambda instances, or paid compute mutations are
  required for this review. None will be launched, stopped, resized, deleted,
  or otherwise mutated.

Target contract:

Evaluate whether the RCLP open protocol MVP is safe to share with controlled
external technical reviewers without leaking commercial strategy, overclaiming
safety, or creating avoidable confusion. Keep changes narrow: update the S4
review report and ledger only unless an obvious sensitive-content cleanup is
required.

Definition of done:

| Item | Status | Evidence |
|---|---|---|
| Required S4 and repo doctrine documents are read before report update. | met | Read `README.md`, `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`, `docs/COMMERCIAL_BOUNDARY.md`, `docs/GOVERNANCE.md`, `docs/SAFETY_BOUNDARY.md`, `docs/CUSTOMER_VALIDATION_MEMO.md`, `docs/VALIDATION_RELEASE_NOTES.md`, `AGENTS.md`, and the required doctrine docs before editing the report. |
| Requested search targets and sensitive-content scans are run without exposing possible secrets. | met | Ran tracked-file searches for the requested terms, targeted local-path scans, named-company scans, license posture checks, security-contact checks, source/review-packet scans with repository ignore rules, and secret-shaped pattern scans. The report now states that ignored generated artifacts such as virtualenvs, build outputs, caches, and bytecode must be cleaned or excluded before packaging. No possible secret values are quoted in the report. |
| S4 report is written at the requested path with the requested structure and answers all six evaluation questions. | met | Updated `docs/reviews/codex_simulated_review/S4_open_source_commercial_boundary.md` with the required sections, GREEN verdict, current scan evidence, commercial-boundary assessment, safety/security wording risks, sensitive-reference assessment, blocking issues, and recommended fixes. |
| Verdict is appropriate for controlled external technical validation and avoids public-launch or production-deployment overclaiming. | met | The report says suitable for controlled external technical validation, not public standardization or production deployment, and keeps public security intake/counsel review as public-launch cautions rather than controlled-validation blockers. |
| Changes remain narrow and do not introduce secrets, local paths, private references, unsafe wording, or commercial strategy. | met | Edits are limited to the S4 report and this assembly ledger entry; tracked-source and review-packet scans found no local absolute paths, named-company target hits, or secret-shaped pattern matches. |
| Validation/evidence gates and subagent spec-conformance review complete. | met | `git diff --check`, `.venv/bin/python -m compileall src tests`, `.venv/bin/python -m pytest -q` (246 passed), `.venv/bin/ruff check .`, `.venv/bin/ruff format . --check`, `cargo fmt --all -- --check`, `cargo clippy --workspace --all-targets -- -D warnings`, `cargo test --workspace` (3 unit tests and 47 vector tests), and `.venv/bin/python tests/evals/eval_runner.py` (33 passed) passed. McClintock's initial review found one evidence-scope wording issue and the pending ledger row; both were resolved, and the re-review found no remaining blocking, partial, or evidence risks. |

Changed files:

- `docs/reviews/codex_simulated_review/S4_open_source_commercial_boundary.md`
- `docs/ASSEMBLY_LEDGER.md`

Review notes:

- McClintock confirmed the report structure and GREEN verdict satisfy the S4
  contract for controlled external technical validation.
- The valid review finding about overbroad local-path evidence wording was
  fixed by scoping the report to tracked-source and review-packet scans and by
  adding a generated-artifact cleanup/exclusion guard before packaging.
- McClintock's re-review classified all DoD items as met and found no remaining
  blocking, partial, or evidence risks.

## S4 Recommended-fix Closure Follow-up - 2026-06-25

Status: successful

Source contract:

- User request: resolve all blocking issues and implement the recommended fixes
  from `docs/reviews/codex_simulated_review/S4_open_source_commercial_boundary.md`
  using `assembly`.
- `AGENTS.md`
- `docs/ENGINEERING_DOCTRINE.md`
- `docs/SECURITY_DOCTRINE.md`
- `docs/DESIGN_TASTE.md`
- `docs/PROTOCOL_SPEC_DRAFT.md`
- `docs/THREAT_MODEL.md`
- `docs/TEST_STRATEGY.md`
- `docs/COMMERCIAL_BOUNDARY.md`
- `docs/GOVERNANCE.md`
- `docs/SAFETY_BOUNDARY.md`
- `docs/CONTROLLED_REVIEW_PACKET.md`
- `SECURITY.md`

Preflight note:

- No cloud jobs, GPU jobs, Lambda instances, or paid compute mutations are
  required for this item. None will be launched, stopped, resized, deleted, or
  otherwise mutated.

Target contract:

Close the current S4 follow-up by ensuring the review report has no unresolved
controlled-validation blockers and that each recommended fix is either already
implemented in repository docs or explicitly represented as a pre-distribution
human gate. Keep the repo suitable for controlled external technical
validation, not public standardization or production deployment.

Definition of done:

| Item | Status | Evidence |
|---|---|---|
| No controlled-validation blocking issues remain in the S4 report. | met | `docs/reviews/codex_simulated_review/S4_open_source_commercial_boundary.md` keeps the verdict GREEN and states there are no blocking issues for controlled external technical validation. |
| Recommended fixes are represented as implemented repo controls or explicit pre-distribution gates. | met | The S4 report now states no remaining repository implementation fixes are required for controlled validation, names `docs/CONTROLLED_REVIEW_PACKET.md` as the technical-review source of truth, and treats the private security-reporting contact as a pre-distribution human gate. `docs/CONTROLLED_REVIEW_PACKET.md` now says not to send the packet until the project owner or private review channel for security reports is named. |
| Safety, security, and commercial-boundary language remains conservative. | met | The changed docs preserve controlled technical validation framing and use the existing non-production, safety-adjacent, fallback-hook, network-state-aware authorization, and sim-proof wording without public standardization, production deployment, carrier behavior, or certified-safety claims. |
| No secrets, local paths, pricing, named customer lists, carrier-contract details, or sensitive company references are introduced. | met | Targeted tracked-file scans found no local absolute paths and no secret-pattern matches; the broader requested-term scan showed expected non-claim, doctrine, checklist, environment-placeholder, and deterministic dev-HMAC fixture hits only. The changed files add no credentials, local paths, account identifiers, pricing, customer names, carrier contracts, or proprietary workflows. |
| Validation gates and subagent review complete. | met | `.venv/bin/python -m compileall src tests`, `.venv/bin/python -m pytest -q` (246 passed), `.venv/bin/ruff check .`, `.venv/bin/ruff format . --check`, `cargo fmt --all -- --check`, `cargo clippy --workspace --all-targets -- -D warnings`, `cargo test --workspace` (3 unit tests and 47 vector tests), `.venv/bin/python tests/evals/eval_runner.py` (33 passed), and `git diff --check` passed. Pasteur's independent review classified the report and packet changes as met and found only this ledger-closure gap, which this update resolves. |

Changed files:

- `docs/reviews/codex_simulated_review/S4_open_source_commercial_boundary.md`
- `docs/CONTROLLED_REVIEW_PACKET.md`
- `docs/ASSEMBLY_LEDGER.md`

Review notes:

- Pasteur reviewed the S4 follow-up and found no additional governance,
  safety-wording, provenance, or data-leakage blockers. The only valid finding
  was that this ledger entry still said `in-progress` and had pending DoD rows;
  this ledger update resolves that finding.
- Pasteur re-reviewed after the ledger correction and found no remaining
  blocking, partial, or evidence risks; all five DoD items were classified as
  met.

## S4 Open-source / Commercial-boundary Fixes - 2026-06-25

Status: successful

Source contract:

- User request: resolve all blocking issues and implement recommended fixes
  from `docs/reviews/codex_simulated_review/S4_open_source_commercial_boundary.md`
  using `assembly`.
- `AGENTS.md`
- `docs/ENGINEERING_DOCTRINE.md`
- `docs/SECURITY_DOCTRINE.md`
- `docs/DESIGN_TASTE.md`
- `docs/PROTOCOL_SPEC_DRAFT.md`
- `docs/THREAT_MODEL.md`
- `docs/TEST_STRATEGY.md`
- `docs/COMMERCIAL_BOUNDARY.md`
- `docs/GOVERNANCE.md`
- `docs/SAFETY_BOUNDARY.md`

Preflight note:

- No cloud jobs, GPU jobs, Lambda instances, or paid compute mutations are
  required for this item. None were launched, stopped, resized, deleted, or
  otherwise mutated.

Target contract:

Resolve the S4 yellow/blocking hygiene items without broad code changes:
controlled external technical reviewers should see a clean license posture,
non-placeholder controlled security reporting instructions, a focused external
review packet boundary, conservative safety/security language, and no added
commercial strategy or sensitive data.

Definition of done:

| Item | Status | Evidence |
|---|---|---|
| Rust and Python package license declarations align with the root license. | met | `crates/rclp-edge-verifier/Cargo.toml` now declares `Apache-2.0`, matching `LICENSE` and `pyproject.toml`. |
| `SECURITY.md` no longer contains a placeholder reporting contact. | met | `SECURITY.md` now directs controlled reviewers to the named project owner or private review channel that provided the packet and keeps monitored public intake as a public-launch requirement. |
| A controlled external review packet boundary exists and excludes planning docs unless needed. | met | Added `docs/CONTROLLED_REVIEW_PACKET.md` with include/exclude lists, distribution checks, and opening-note language; README, validation notes, release readiness, FAQ, and customer-call checklist link or reference it. |
| S4 report reflects the remediated current state without overclaiming public-release readiness. | met | `docs/reviews/codex_simulated_review/S4_open_source_commercial_boundary.md` now reports GREEN for controlled validation, no controlled-validation blockers, and remaining public-release cautions. |
| Safety/security wording remains conservative. | met | New and edited docs use controlled validation, safety-adjacent authority layer, fallback hook, network-state-aware authorization, and sim proof framing without production safety claims. |
| No secrets, local paths, pricing, named customer lists, or carrier-contract details are added. | met | Edits add only docs/package metadata and no credentials, account identifiers, local paths, pricing, customer names, or carrier details. |
| Validation gates and subagent review complete. | met | `.venv/bin/python -m compileall src tests`, `.venv/bin/python -m pytest` (246 passed), `.venv/bin/ruff check .`, `.venv/bin/ruff format . --check`, `cargo fmt --all -- --check`, `cargo clippy --workspace --all-targets -- -D warnings`, and `cargo test --workspace` passed. Targeted scans found no local absolute paths, no stale placeholder security-contact text, no old dual-license string, and no named company/carrier target terms; broader secret-pattern hits were code/test HMAC names or environment-variable placeholders. Subagent review findings were addressed. |

## T13 Demo + Validation Release Package - 2026-06-25

Status: successful

Source contract:

- User request: proceed with T13 using `assembly`.
- User-supplied T13 prompt: `T13 - Demo + Validation Release Package`.
- `AGENTS.md`
- Required repo doctrine under `docs/`
- `docs/POST_T12_SEQUENCE_PLAN.md`
- `docs/RELEASE_READINESS.md`
- `docs/SAFETY_BOUNDARY.md`
- `docs/COMMERCIAL_BOUNDARY.md`
- `docs/EVALS.md`
- `docs/RUST_EDGE_VERIFIER.md`

Preflight note:

- No cloud jobs, AWS Lambda functions, GPU jobs, or paid compute are required
  for T13, and none will be launched, stopped, resized, deleted, or otherwise
  mutated.
- `DIRECTION.md` is not present in the current checkout.
- Baseline validation passed before edits: `.venv/bin/python -m compileall src
  tests`, `.venv/bin/python -m pytest -q`, `.venv/bin/python
  tests/evals/eval_runner.py`, `cargo fmt --all -- --check`, `cargo clippy
  --workspace --all-targets -- -D warnings`, and `cargo test --workspace`.

Target contract:

Package the working RCLP MVP for 5-8 controlled technical validation calls by
creating externally legible release notes, customer-call material, FAQ,
walkthrough, comparison, target-profile docs, and local validation/demo scripts
without adding protocol features or production-readiness claims.

Success criterion:

The validation package is complete, scripts work without network, ROS 2, Isaac
Sim, or cloud resources, README points to the package, tests/evals pass, a
spec-conformance review is clean, and the final readiness assessment is limited
to controlled technical validation calls.

Definition of done:

| Item | Status | Evidence |
|---|---|---|
| D1: `docs/VALIDATION_RELEASE_NOTES.md` exists for `v0.1-validation`. | met | Release notes include purpose, implemented components, demo flow, 33-scenario eval coverage, Rust verifier status, known hardening gaps, non-claims, intended audience, next validation steps, exact controlled-call/non-production sentence, and suggested tag guidance. |
| D2: `docs/CUSTOMER_CALL_PACKET.md` exists. | met | Customer packet includes the required one-liner, problem statement, MVP proves/does-not-prove lists, feedback sought, five-minute flow, and conservative authority wording after review. |
| D3: `docs/TECHNICAL_FAQ.md` exists. | met | FAQ covers robot fleet manager, teleoperation, safety controller, ROS 2/VDA5050/Open-RMF/MCP/A2A replacement, short-lived leases, local enforcement, network state, cloud partition, Rust/Python relationship, production readiness, and future commercial platform. |
| D4: `docs/DEMO_WALKTHROUGH.md` exists and supports a five-minute live call. | met | Walkthrough now includes setup, validation, demo commands, expected story, stable output highlights, allow/deny/revoke/degrade/audit/eval explanations, limitations, and a closing validation question. |
| D5: `docs/WHY_NOT_EXISTING_PROTOCOLS.md` exists. | met | Comparison doc covers ROS 2/DDS Security, VDA5050, Open-RMF, MassRobotics AMR Interop, MCP, A2A, fleet managers, teleop systems, and IoT connectivity platforms while stating RCLP is a narrow adjacent authority layer. |
| D6: `docs/FIRST_CALL_TARGET_PROFILE.md` exists. | met | Target profile lists best-fit customers, personas, strong-fit traits, bad-fit traits, discovery priorities, and recommended first ask. |
| D7: `scripts/run_validation_checks.sh` exists and works. | met | Script uses strict Bash mode, runs compileall, pytest, eval runner, Ruff, and Rust fmt/clippy/test when Cargo is available; `./scripts/run_validation_checks.sh` passed after review fixes. |
| D8: `scripts/run_validation_demo.sh` exists and works. | met | Script prints concise demo framing, points to `docs/DEMO_WALKTHROUGH.md`, and runs `python -m rclp_agents.demo_remote_assist`; default and `--network-profile uplink_bad` runs passed. |
| D9: `README.md` links to the validation package and commands. | met | README now links release notes, customer packet, demo walkthrough, evals, comparison doc, technical FAQ, target profile, and validation/demo commands. |
| D10: Tests/evals pass. | met | Baseline and post-review validation passed: 246 pytest tests, 33/33 evals, Ruff, Rust fmt/clippy, and Rust unit/vector tests. |
| D11: Final response states controlled-call readiness without production claims. | met | Final response for this assembly item will state controlled technical validation readiness only and will not claim production readiness. |

Changed files:

- `README.md`
- `docs/ASSEMBLY_LEDGER.md`
- `docs/CUSTOMER_CALL_PACKET.md`
- `docs/CUSTOMER_VALIDATION_MEMO.md`
- `docs/DEMO_SCRIPT.md`
- `docs/DEMO_WALKTHROUGH.md`
- `docs/FIRST_CALL_TARGET_PROFILE.md`
- `docs/TECHNICAL_FAQ.md`
- `docs/VALIDATION_RELEASE_NOTES.md`
- `docs/WHY_NOT_EXISTING_PROTOCOLS.md`
- `scripts/run_validation_checks.sh`
- `scripts/run_validation_demo.sh`

Review notes:

- Avicenna reviewed T13 spec conformance and classified D1-D8 and D10 as met,
  D9 as partial only because README initially omitted
  `docs/WHY_NOT_EXISTING_PROTOCOLS.md`.
- Valid review findings were fixed: ledger provenance was updated, pre-existing
  local absolute paths in this public ledger were redacted, README now links
  the comparison doc, and customer-packet wording avoids "safely pass" and
  "unsafe authority" overclaims.
- Avicenna re-review returned no blocking findings and classified D1-D10 as
  met for controlled technical validation readiness. The reviewer was closed
  after completion, and no cloud changes were made.

Evidence:

- Baseline before edits passed:
  `.venv/bin/python -m compileall src tests`;
  `.venv/bin/python -m pytest -q` (246 passed);
  `.venv/bin/python tests/evals/eval_runner.py` (33 passed);
  `cargo fmt --all -- --check`;
  `cargo clippy --workspace --all-targets -- -D warnings`;
  `cargo test --workspace` (3 unit tests and 47 vector tests).
- Initial smoke after edits passed:
  `bash -n scripts/run_validation_checks.sh scripts/run_validation_demo.sh`;
  `./scripts/run_validation_demo.sh --network-profile uplink_bad` produced
  `NETWORK_UPLINK_TOO_LOW`, `audit_jsonl`, and `incident_replay_summary`.
- Full validation package command passed:
  `./scripts/run_validation_checks.sh` (246 pytest tests, 33/33 evals, Ruff,
  Rust fmt/clippy, 3 Rust unit tests, and 47 Rust vector tests).
- Default demo command passed:
  `./scripts/run_validation_demo.sh` produced `POLICY_SATISFIED`,
  `LEASE_VALID`, `NO_LEASE`, `NETWORK_LATENCY_DEGRADED`,
  `NETWORK_PROFILE_REVOKE`, `LEASE_REVOKED`, `audit_jsonl`, and
  `incident_replay_summary`.
- Post-review hygiene and validation passed:
  local absolute-path scan over public docs, scripts, guidance, examples,
  manifests, agents, and workflows returned no matches;
  `git diff --check` passed;
  `bash -n scripts/run_validation_checks.sh scripts/run_validation_demo.sh`
  passed;
  `./scripts/run_validation_checks.sh` passed;
  default and `uplink_bad` demo runs passed.

## Post-Scan 2-Finding Security Remediation - 2026-06-25 (scan ff73e22a)

Status: successful

Source contract:

- User request: resolve the two findings from Codex Security scan
  `ff73e22a-43d8-4ebe-8c31-14d9e44dcd9b` using `assembly`.
- Scan report:
  `local Codex Security report artifact redacted`
- Findings:
  `csf_b88c842c54b2e57b23544d31` and
  `csf_bac2df8348c750866b4e43d0`.
- `AGENTS.md`
- Required repo doctrine under `docs/`
- `docs/PROTOCOL_SPEC_DRAFT.md`
- `docs/THREAT_MODEL.md`
- `docs/TEST_STRATEGY.md`

Preflight note:

- The working tree already contained uncommitted remediation changes before
  this pass began; this entry records the additional work for scan `ff73e22a`.
- No cloud jobs, AWS Lambda functions, GPU jobs, or paid compute are required
  for this remediation, and none will be launched, stopped, resized, deleted,
  or otherwise mutated.

Target contract:

Close the two validated findings at their root authority contracts: Rust edge
verifier command payload constraints must be enforced before any non-deny
degrade authority result, and Python signed lease duration must be compared to
the exact local max TTL policy without widening by wall-clock skew.

Success criterion:

The original vulnerable paths no longer reproduce, focused negative
regressions prove each invariant and legitimate behavior, assembly
spec-conformance review is clean, post-review validation passes, and this
ledger is updated with final evidence.

Definition of done:

| Item | Status | Evidence |
|---|---|---|
| D1: Rust verifier denies an overspeed signed command under soft network degradation with `DENY_COMMAND_CONSTRAINT` before `Decision::Degrade`. | met | `verify()` now runs `command_constraint_violation()` inside the `DegradeNetworkPolicy` branch before returning `Decision::Degrade`; regression `network_degrade_overspeed_command_denies_before_degrade` mutates the degrade vector with coherent max-speed bounds and an overspeed payload and passed. |
| D2: Python lease duration rejects `max_lease_ttl_seconds + 1` even when the overage is inside `LEASE_CLOCK_SKEW_SECONDS`, while exact max TTL still passes. | met | `lease_time_violation()` now compares signed lease duration to the exact `max_lease_ttl_seconds` policy; regressions `test_lease_ttl_exact_max_passes_but_max_plus_one_rejects_within_skew` and `test_command_gate_rejects_lease_ttl_max_plus_one_even_within_skew` passed. |
| D3: Focused and full validation gates pass after assembly review. | met | Focused Python and Rust smokes passed before review; Cicero subagent review found only this ledger status gap, then reported compileall, full pytest, Rust workspace, Ruff, cargo fmt/clippy, and `git diff --check` passing. Post-review focused smokes and `git diff --check` passed after the ledger update. |

Changed files:

- `crates/rclp-edge-verifier/src/verifier.rs`
- `crates/rclp-edge-verifier/tests/vector_tests.rs`
- `src/rclp_core/leases.py`
- `tests/test_security_negative_paths.py`
- `docs/ASSEMBLY_LEDGER.md`

Review notes:

- Cicero reviewed spec conformance and DoD satisfaction. D1 and D2 were
  classified `met`; D3 was initially `partial` only because this ledger entry
  still said `in-progress`/`not-started`.
- No code-level contract, source-parity, runtime, safety, or provenance
  blockers remained after this ledger update.
- The review subagent was closed after completion.

Evidence:

- Focused Python regression gate passed:
  `.venv/bin/python -m pytest -q tests/test_security_negative_paths.py::test_lease_ttl_exact_max_passes_but_max_plus_one_rejects_within_skew tests/test_security_negative_paths.py::test_command_gate_rejects_lease_ttl_max_plus_one_even_within_skew`
  (2 passed).
- Focused Rust regression gate passed:
  `cargo test -p rclp-edge-verifier --test vector_tests network_degrade_overspeed_command_denies_before_degrade`
  (1 passed).
- Broad touched-suite gates passed:
  `.venv/bin/python -m pytest -q tests/test_security_negative_paths.py`
  (175 passed) and
  `cargo test -p rclp-edge-verifier --test vector_tests`
  (47 passed).
- Cicero review validation passed:
  `.venv/bin/python -m compileall src tests`;
  `.venv/bin/python -m pytest -q` (246 passed);
  `cargo test --workspace` (3 unit tests and 47 vector tests);
  `.venv/bin/ruff check .`;
  `.venv/bin/ruff format --check .`;
  `cargo fmt --all -- --check`;
  `cargo clippy --workspace --all-targets -- -D warnings`;
  `git diff --check`.
- Final local full-gate rerun passed after review and ledger correction:
  `.venv/bin/python -m compileall src tests`;
  `.venv/bin/python -m pytest -q` (246 passed);
  `.venv/bin/ruff check .`;
  `.venv/bin/ruff format --check .`;
  `cargo fmt --all -- --check`;
  `cargo test --workspace` (3 unit tests and 47 vector tests);
  `cargo clippy --workspace --all-targets -- -D warnings`.

## Post-Scan 4-Finding Security Remediation - 2026-06-25 (scan 6eba756f)

Status: successful

Source contract:

- User request: resolve all four findings from Codex Security scan
  `6eba756f-be06-4876-adbc-336f3a3a7271` using `assembly`.
- Scan report:
  `local Codex Security report artifact redacted`
- Findings:
  `csf_64d842e5a53d7e92519cdf9a`,
  `csf_22c57b9b68fc8ec1228f5edb`,
  `csf_19fb9d50b5523232aef924f3`, and
  `csf_b5fd272221dd38e06f71514d`.
- `AGENTS.md`
- Required repo doctrine under `docs/`
- `docs/PROTOCOL_SPEC_DRAFT.md`
- `docs/THREAT_MODEL.md`
- `docs/TEST_STRATEGY.md`

Preflight note:

- The working tree already contained uncommitted remediation changes before
  this pass began; this entry records only the additional work for scan
  `6eba756f`.
- No cloud jobs, AWS Lambda functions, GPU jobs, or paid compute are required
  for this remediation, and none will be launched, stopped, resized, deleted,
  or otherwise mutated.

Target contract:

Close the four validated findings at their root authority contracts: signed
network state must not authorize from defaulted or contradictory attachment
state; attestation trust must require explicit `trust_tier`; attestation signed
material must be size-budgeted before signature verification/canonicalization;
and command-gate lease-validation failures must not emit fallback hooks unless
the denial is tied to locally authenticated revocation or already-valid local
state context.

Success criterion:

The original vulnerable paths no longer reproduce, focused negative
regressions prove each invariant and legitimate behavior, assembly
spec-conformance review is clean, post-review validation passes, and this
ledger is updated with final evidence.

Definition of done:

| Item | Status | Evidence |
|---|---|---|
| D1: Signed robot state missing nested `network_state.attached` is rejected before policy or command-gate allow. | met | `NetworkState.attached` is now structurally required, `state_auth_violation()` also checks nested `model_fields_set`, and `test_robot_state_missing_network_attached_is_rejected_before_policy_allow` proves raw signed state without the nested field cannot reach policy or gate allow. |
| D2: Contradictory `NetworkProfile.PARTITION` with `attached=True` and healthy metrics is fail-closed by policy and command-gate state conformance. | met | Shared helper `network_state_authority_violation()` treats partition as detached and is used by policy issuance and lease/state conformance. Regression `test_partition_profile_with_attached_state_denies_policy_and_command_gate` proves both paths deny with `NETWORK_DETACHED`. |
| D3: Attestation signed material is bounded before signature verification/canonical JSON for both valid and invalid signatures. | met | `attestation_auth_violation()` calls `attestation_signed_material_too_large()` before `verify_with_public_key_b64()`. Regressions `test_oversized_attestation_material_rejects_before_signature_verification` and `test_oversized_invalid_attestation_material_rejects_before_signature_verification` monkeypatch verification and prove it is not reached. |
| D4: Missing attestation `trust_tier` cannot default to `development` through trust-boundary validation. | met | `AgentAttestation.trust_tier` no longer has a default, the protocol manifest no longer treats it as runtime-defaulted, demo attestations set it explicitly, and `test_agent_attestation_missing_trust_tier_is_rejected_at_boundary` proves omission fails at the model boundary. |
| D5: Invalid non-`None` lease validation denials do not emit fallback declarations or fallback-sink calls; revocation-backed denials still can. | met | `CommandGate._denial_can_emit_fallback()` allowlists state fail-closed reasons and authenticated `LEASE_REVOKED` denials. Invalid signature, policy-provenance, policy-digest, forged-revocation, expired-lease, context, payload, and constraint regressions now assert no fallback; `test_replayed_post_auth_denial_does_not_reemit_fallback` preserves authenticated revocation fallback behavior. |
| D6: Focused and full validation gates pass after assembly review. | met | Focused and broad pytest suites, compileall, full pytest, eval runner, Rust workspace test, Ruff, cargo fmt/clippy, and `git diff --check` passed after local assembly review. |

Changed files:

- `src/rclp_core/models.py`
- `src/rclp_core/network.py`
- `src/rclp_core/state.py`
- `src/rclp_core/policy.py`
- `src/rclp_core/conformance.py`
- `src/rclp_core/attestation.py`
- `src/rclp_ros2/command_gate.py`
- `src/rclp_agents/demo_remote_assist.py`
- `manifests/rclp_protocol_manifest.yaml`
- `docs/PROTOCOL_SPEC_DRAFT.md`
- `docs/TEST_STRATEGY.md`
- `tests/test_security_negative_paths.py`
- `tests/test_protocol_flow.py`

Review notes:

- Assembly spec-conformance review checked the patched authority boundaries
  against the four scan findings: no unsafe model defaults remain for
  `network_state.attached` or attestation `trust_tier`; policy and command
  conformance share the partition/detached helper; attestation size checks run
  before verification; and fallback emission is explicit by denial class.
- Multi-agent tooling is available, but its active rule forbids spawning
  subagents unless the user explicitly asks for subagents/delegation. Assembly
  spec-conformance review was therefore completed locally.
- The worktree already contained uncommitted remediation changes before this
  pass began; those files were preserved and validated rather than reverted.

Evidence:

- Focused regression gate passed:
  `.venv/bin/python -m pytest -q tests/test_security_negative_paths.py::test_oversized_attestation_material_rejects_before_signature_verification tests/test_security_negative_paths.py::test_oversized_invalid_attestation_material_rejects_before_signature_verification tests/test_security_negative_paths.py::test_agent_attestation_missing_trust_tier_is_rejected_at_boundary tests/test_security_negative_paths.py::test_partition_profile_with_attached_state_denies_policy_and_command_gate tests/test_security_negative_paths.py::test_command_gate_rejects_signed_lease_missing_policy_provenance tests/test_security_negative_paths.py::test_command_gate_rejects_signed_lease_policy_digest_mismatch tests/test_security_negative_paths.py::test_forged_revoked_lease_id_cannot_select_revocation_fallback`
  (7 passed).
- Broad touched-suite gate passed:
  `.venv/bin/python -m pytest -q tests/test_security_negative_paths.py tests/test_protocol_flow.py tests/test_demo_remote_assist.py`
  (216 passed).
- Manifest conformance gate passed:
  `.venv/bin/python -m pytest -q tests/test_conformance_contract.py::test_protocol_manifest_matches_exported_message_models`
  (1 passed).
- `.venv/bin/python -m compileall src tests` passed.
- `.venv/bin/python -m pytest -q` passed: 244 tests.
- `.venv/bin/python tests/evals/eval_runner.py` passed: 33/33 evals.
- `cargo test --workspace` passed: 3 unit tests and 46 vector tests.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format --check .` passed.
- `cargo fmt --all -- --check` passed.
- `cargo clippy --workspace --all-targets -- -D warnings` passed.
- `git diff --check` passed.

## Post-Scan 5-Finding Security Remediation - 2026-06-25 (scan a6759ec9)

Status: successful

Source contract:

- User request: resolve all five findings from Codex Security scan
  `a6759ec9-0b09-4053-a71c-338d081bdaf2` using `assembly`.
- Scan report:
  `local Codex Security report artifact redacted`
- Findings:
  `csf_fcf962ab89e1a38173c7e2cc`,
  `csf_bf47df01065ce7ffecface5e`,
  `csf_3672d8e61ae65b2e9ba4da74`,
  `csf_17c586c247ad83ec4d574053`, and
  `csf_c05aa5124fe6dcd69dd2f54b`.
- `AGENTS.md`
- Required repo doctrine under `docs/`
- `docs/PROTOCOL_SPEC_DRAFT.md`
- `docs/THREAT_MODEL.md`
- `docs/TEST_STRATEGY.md`

Preflight note:

- Working tree was clean before this remediation began.
- No cloud jobs, AWS Lambda functions, GPU jobs, or paid compute are required
  for this remediation, and none will be launched, stopped, resized, deleted,
  or otherwise mutated.

Target contract:

Close the five validated findings at their root authority/audit contracts:
missing-lease command denials must not consume replay state or emit fallback;
robot state assertions must be size-budgeted before signature decode or
canonicalization; Python pre-auth command/revocation diagnostics must bound
claimed untrusted fields before audit construction; Rust malformed-input
diagnostics must bound parser summaries before audit storage; and attestation
trust must fail closed unless manifest and trust-tier policies are explicit.

Success criterion:

The original vulnerable paths no longer reproduce, focused negative
regressions prove each invariant and legitimate behavior, assembly
spec-conformance review is clean, post-review gates pass, and this ledger is
updated with final evidence.

Definition of done:

| Item | Status | Evidence |
|---|---|---|
| D1: Signed commands presented with `lease=None` do not consume command replay state or emit fallback declarations. | met | `CommandGate.evaluate()` now rejects `lease=None` before replay consumption and with `emit_fallback=False`. Regression `test_missing_lease_denial_does_not_consume_command_replay_or_emit_fallback` proves the later command-plus-lease use is accepted and no fallback is emitted. |
| D2: `RobotStateAssertion` signed material is budgeted before base64 decode, canonical JSON, or signature verification. | met | `state_auth_violation()` now calls `robot_state_signed_material_too_large()` before `verify_with_public_key_b64()`. Regression `test_oversized_robot_state_material_rejects_before_signature_verification` monkeypatches verification and proves over-budget state returns `STATE_SIGNED_MATERIAL_TOO_LARGE` first. |
| D3: Python command and revocation pre-auth diagnostics bound claimed untrusted text before audit construction. | met | `CommandGate` now records oversized claimed diagnostic text as byte length, SHA-256, and truncation metadata; pre-auth command diagnostics no longer include untrusted command IDs in summaries or irrelevant state snapshots. Regressions `test_command_auth_diagnostic_bounds_oversized_claimed_fields` and `test_revocation_diagnostic_bounds_oversized_claimed_revoker` passed. |
| D4: Rust malformed pre-parse diagnostics bound parser summaries before audit construction. | met | `malformed_decision()` now stores `bounded_diagnostic_text(&summary)`. Regression `malformed_input_diagnostic_summary_bounds_oversized_parse_errors` passed and asserts the oversized unknown key is absent from the audit payload. |
| D5: Attestation trust requires explicit accepted trust tiers and manifest digest policy before returning trusted. | met | `attestation_trust_violation()` now returns `ATTESTATION_TRUST_TIER_POLICY_REQUIRED` or `ATTESTATION_MANIFEST_DIGEST_POLICY_REQUIRED` when those policy surfaces are omitted. Regressions `test_agent_attestation_requires_explicit_trust_tier_policy` and `test_agent_attestation_requires_explicit_manifest_policy` passed. |
| Focused and full validation gates pass after assembly review. | met | Focused gates passed: `.venv/bin/python -m pytest -q tests/test_security_negative_paths.py -k 'attestation_requires_explicit or oversized_robot_state or diagnostic_bounds or missing_lease_denial or replayed_post_auth'` (7 passed), `.venv/bin/python -m pytest -q tests/test_protocol_flow.py::test_no_lease_rejected tests/test_protocol_flow.py::test_fallback_declaration_uses_command_correlation_id tests/test_demo_remote_assist.py::test_demo_remote_assist_outputs_full_local_authority_flow` (3 passed), and `cargo test -p rclp-edge-verifier --test vector_tests malformed_input_diagnostic_summary_bounds_oversized_parse_errors` (1 passed). Post-review full gates passed: compileall, full pytest, eval runner, cargo test, Ruff check/format check, cargo fmt check, Clippy, and `git diff --check`. |

Changed files:

- `src/rclp_ros2/command_gate.py`
- `src/rclp_core/state.py`
- `src/rclp_core/attestation.py`
- `crates/rclp-edge-verifier/src/verifier.rs`
- `tests/test_security_negative_paths.py`
- `tests/test_protocol_flow.py`
- `tests/test_demo_remote_assist.py`
- `tests/evals/scenarios/audit_deny_complete.yaml`
- `crates/rclp-edge-verifier/tests/vector_tests.rs`
- `docs/PROTOCOL_SPEC_DRAFT.md`
- `docs/TEST_STRATEGY.md`
- `docs/ASSEMBLY_LEDGER.md`

Review notes:

- Assembly spec-conformance review found the five remediation contracts met and
  added one sibling hardening fix: pre-auth command diagnostics no longer attach
  irrelevant `current_state` snapshots.
- Multi-agent tooling is available, but its active rule forbids spawning
  subagents unless the user explicitly asks for subagents/delegation. Assembly
  spec-conformance review was therefore completed locally.

Evidence:

- `.venv/bin/python -m compileall src tests` passed.
- `.venv/bin/python -m pytest -q` passed: 239 tests.
- `.venv/bin/python tests/evals/eval_runner.py` passed: 33/33 evals.
- `cargo test --workspace` passed: 3 unit tests and 46 vector tests.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format --check .` passed.
- `cargo fmt --all -- --check` passed.
- `cargo clippy --workspace --all-targets -- -D warnings` passed.
- `git diff --check` passed.

## Post-Scan 4-Finding Security Remediation - 2026-06-24 (scan 72e1cd1f)

Status: successful

Source contract:

- User request: commit/push the current checkpoint, then fix all four findings
  from Codex Security scan `72e1cd1f-641c-4e46-9792-2c2739931ca5`
  using `assembly`.
- Scan report:
  `local Codex Security report artifact redacted`
- Findings:
  `RCLP-SHARD-72E1CD1F-GEOFENCE-BOUNDS-001`,
  `72e1cd1f-conformance-fallback-bound-001`,
  `RCLP-EDGE-VERIFIER-AUDIT-DOS-002`, and
  `RCLP-PY-COMMAND-DIAGNOSTIC-LABEL-001`.
- `AGENTS.md`
- Required repo doctrine under `docs/`
- `docs/PROTOCOL_SPEC_DRAFT.md`
- `docs/THREAT_MODEL.md`
- `docs/TEST_STRATEGY.md`

Preflight note:

- The checkpoint commit `37e7f74 Harden RCLP authority verification` was
  pushed to `origin/main` before this remediation began.
- No cloud jobs, AWS Lambda functions, GPU jobs, or paid compute are required
  for this remediation, and none will be launched, stopped, resized, deleted,
  or otherwise mutated.

Target contract:

Close the four validated findings at their root authority/audit contracts:
policy-derived capability bounds must include explicit geofence identity when
geofence policy is required; effective lease fallback defaults must still be
bounded by local policy; unauthenticated command diagnostics must label subject
fields as claimed data; and Rust pre-auth audit diagnostics must bound
over-budget claimed text before storing it.

Success criterion:

The original vulnerable paths no longer reproduce, focused regressions prove
each invariant and legitimate behavior, assembly spec-conformance review is
clean, and full repository validation passes.

Definition of done:

| Item | Status | Evidence |
|---|---|---|
| `RCLP-SHARD-72E1CD1F-GEOFENCE-BOUNDS-001`: policy-derived bounds carry explicit geofence identity and wrong-zone signed leases are rejected locally. | met | `PolicyRequirements.geofence_id` is required when geofence enforcement is enabled, `policy_constraint_bounds()` derives it into `CapabilityConstraintBounds`, Rust vectors now include the explicit local geofence bound, and regressions `test_policy_derived_bounds_include_required_geofence_identity`, `test_policy_required_geofence_identity_must_be_explicit`, and `test_signed_lease_cannot_expand_policy_geofence_identity` passed. |
| `72e1cd1f-conformance-fallback-bound-001`: effective fallback defaults cannot bypass local fallback bounds. | met | Python `capability_constraints_exceed_bounds()` compares the effective fallback value even when the field was omitted; Rust `option_field_exceeds_policy()` now rejects omitted values when a local fallback bound exists. Regressions `test_implicit_fallback_default_cannot_bypass_policy_bounds` and `omitted_fallback_cannot_bypass_local_fallback_bound` passed. |
| `RCLP-EDGE-VERIFIER-AUDIT-DOS-002`: Rust pre-auth denials bound claimed diagnostic text before audit storage. | met | Rust `deny_untrusted_command()` now passes claimed text through `bounded_diagnostic_text()`, storing hash/length metadata for oversized values. Regression `oversized_signed_command_field_is_rejected_before_hmac_canonicalization` asserts bounded payload length and no copied oversized value. |
| `RCLP-PY-COMMAND-DIAGNOSTIC-LABEL-001`: Python command-auth diagnostics expose subject values only as claimed/untrusted fields. | met | `CommandGate._reject_command()` now emits unprefixed subject payload fields only for authority-relevant denials; non-authoritative command-auth diagnostics use `claimed_*` fields. Regression `test_command_auth_denials_do_not_emit_fallback_side_effects` asserts no trusted-looking subject keys are present. |
| Focused and full validation gates pass after review. | met | Focused gates passed: `.venv/bin/python -m pytest tests/test_security_negative_paths.py -q -k 'geofence_identity or fallback_default or command_auth_denials'`, `.venv/bin/python -m pytest tests/test_security_negative_paths.py tests/test_rust_edge_vectors.py -q`, and `cargo test -p rclp-edge-verifier --test vector_tests`. Full gates passed: `.venv/bin/python -m compileall src tests`, `.venv/bin/python -m pytest -q` (234 tests), `.venv/bin/python tests/evals/eval_runner.py` (33/33), `cargo test --workspace` (3 unit tests and 45 vector tests), `.venv/bin/ruff check .`, `.venv/bin/ruff format --check .`, `cargo fmt --all -- --check`, `cargo clippy --workspace --all-targets -- -D warnings`, and `git diff --check`. |

Changed files:

- `src/rclp_core/policy.py`
- `src/rclp_core/leases.py`
- `src/rclp_ros2/command_gate.py`
- `crates/rclp-edge-verifier/src/verifier.rs`
- `examples/policies/remote_assist_policy.yaml`
- `docs/PROTOCOL_SPEC_DRAFT.md`
- `docs/THREAT_MODEL.md`
- `docs/TEST_STRATEGY.md`
- `tests/test_security_negative_paths.py`
- `tests/test_rust_edge_vectors.py`
- `crates/rclp-edge-verifier/tests/vector_tests.rs`
- `tests/vectors/edge_verifier/*.json`

Review notes:

- Local assembly spec-conformance review found the four remediation contracts
  satisfied and added one sibling hardening fix so Rust fallback bounds cannot
  be bypassed by omitted fallback values.
- Multi-agent tooling was available, but its active rule forbids spawning
  subagents unless the user explicitly asks for subagents/delegation. Assembly
  spec-conformance review was therefore performed locally and this limitation
  is recorded here.
- No cloud jobs, AWS Lambda functions, GPU jobs, or paid compute were launched,
  stopped, resized, deleted, or otherwise mutated.

## CAND-0006-001 Policy-Bound Constraint Remediation - 2026-06-24

Status: successful

Source contract:

- User request: commit/push the previous checkpoint, then fix the current
  Codex Security finding using `assembly`.
- Finding `CAND-0006-001`: Edge verification trusts signed lease constraints
  without policy-bound value checks.
- Scan report:
  `local Codex Security report artifact redacted`
- `AGENTS.md`
- Required repo doctrine under `docs/`
- `docs/PROTOCOL_SPEC_DRAFT.md`
- `docs/THREAT_MODEL.md`
- `docs/TEST_STRATEGY.md`

Preflight note:

- The checkpoint commit `fdcee45 Harden RCLP authority controls` was pushed to
  `origin/main` before this remediation began.
- No cloud jobs, AWS Lambda functions, GPU jobs, or paid compute were required
  or mutated.
- Multi-agent tooling was discovered, but its active rule forbids spawning
  subagents unless the user explicitly asks for subagents/delegation. Assembly
  spec-conformance review was therefore performed locally and this limitation
  is recorded here.

Target contract:

Signed lease constraints are not authority by themselves. The edge verifier
must compare every signed constraint value to an explicit local, typed,
per-capability policy-bound contract. A lease may narrow authority, but it must
not add a speed ceiling, relax network thresholds, or choose fallback/network
actions that the accepted local policy bounds do not grant.

Success criterion:

The original PoC overbroad signed lease no longer authorizes, Python
`CommandGate` and the Rust edge verifier both enforce policy-bound constraints,
legitimate narrowed speed-limited leases still exercise command-payload
validation, evals remain green, and repository validation passes.

Definition of done:

| Item | Status | Evidence |
|---|---|---|
| Reproduce `CAND-0006-001` before changes. | met | Pre-fix PoC output showed `overbroad_result.allowed: true` with `reason_code: LEASE_VALID` for a signed `max_speed_mps: 100.0` lease under a policy with no speed grant. |
| Add a typed policy-bound constraint contract visible to edge verifiers. | met | `CapabilityConstraintBounds` was added to Python models and Rust trusted verifier context; `policy_constraint_bounds()` derives bounds from accepted policy; all Rust vectors now include `trusted_context.capability_constraint_bounds`. |
| Python command gate rejects signed lease constraints broader than accepted policy bounds. | met | `validate_lease_for_command()` now calls `capability_constraint_bound_violation()` after malformed checks. Regressions cover absent speed grants and relaxed network thresholds returning `LEASE_CONSTRAINTS_EXCEED_POLICY`; legitimate policy-owned speed limits still pass payload validation. |
| Rust edge verifier rejects the same overbroad signed constraint pattern. | met | Rust `lease_constraints_exceed_policy()` denies signed constraints exceeding `CapabilityConstraintBounds`. Regression `signed_lease_constraints_cannot_expand_absent_policy_speed_bound` returns `DENY_LEASE_CONSTRAINTS_EXCEED_POLICY`. |
| Positive/narrowed behavior remains valid. | met | Existing and updated speed tests verify policy-owned `max_speed_mps: 0.5` leases still allow valid speed aliases and reject too-high, malformed, or conflicting command speeds with command-specific reasons. Eval scenarios now declare their policy speed bounds explicitly. |
| Normative docs and conformance contract describe the invariant. | met | `docs/PROTOCOL_SPEC_DRAFT.md`, `docs/THREAT_MODEL.md`, and `docs/TEST_STRATEGY.md` now state that signed lease constraints must not exceed local policy-bound constraint values. |
| Required validation commands and focused evidence pass. | met | `python -m compileall src tests` passed; `.venv/bin/python -m compileall src tests` passed; `.venv/bin/python -m pytest` passed, 230 tests; `.venv/bin/python tests/evals/eval_runner.py` passed, 33 evals; `cargo fmt --manifest-path crates/rclp-edge-verifier/Cargo.toml --check` passed; `cargo test --manifest-path crates/rclp-edge-verifier/Cargo.toml` passed, 3 unit tests and 44 vector tests; `.venv/bin/ruff format --check .` passed; `.venv/bin/ruff check .` passed; `git diff --check` passed. |
| Original issue no longer reproduces. | met | Post-fix original PoC reports `overbroad_result.allowed: false` with `reason_code: LEASE_CONSTRAINTS_EXCEED_POLICY`; baseline no-speed command remains denied with `COMMAND_PAYLOAD_SCHEMA_VIOLATION`. |

Review notes:

- Local spec-conformance review checked the changed Python/Rust verifier
  boundary against the source contract and confirmed the new invariant is
  enforced at the command-gate/verifier layer rather than only at policy
  issuance.
- Bare `python tests/evals/eval_runner.py` still fails in this shell because
  the system interpreter lacks `yaml`; the repository `.venv` runner passes.

## Post-Scan 4-Finding Security Remediation - 2026-06-24 (scan 52c0d522)

Status: successful

Source contract:

- User request: resolve all four findings from Codex Security scan
  `52c0d522-150d-4a46-a0ca-b2bfd6630212` using `assembly`.
- Scan report:
  `local Codex Security report artifact redacted`
- `AGENTS.md`
- Required repo doctrine under `docs/`
- `docs/PROTOCOL_SPEC_DRAFT.md`
- `docs/THREAT_MODEL.md`
- `docs/TEST_STRATEGY.md`

Preflight note:

- No cloud jobs, GPU jobs, AWS Lambda functions, or paid compute are required
  for this remediation, and none will be launched, stopped, resized, deleted,
  or otherwise mutated.
- Assembly review used an available spec-conformance reviewer after focused
  implementation smoke passed.

Target contract:

Close the four validated findings at their root authority/audit contracts:
Rust command payload schema validation must run independently of speed
constraints; policy-required human-operator state must be explicit in signed
wire state before allow; geofence-required Rust leases and local state must
carry non-empty geofence identifiers; and audit JSONL import must reject null
required integrity fields before model normalization.

Success criterion:

The original vulnerable paths no longer reproduce, focused regressions prove
each invariant and legitimate behavior, local validation gates pass, assembly
spec-conformance review is clean, post-review gates pass, and this ledger is
updated with final evidence.

Definition of done:

| Item | Status | Evidence |
|---|---|---|
| RCLP-52C0-001: Rust verifier validates command payload schema for no-speed leases; nonempty no-speed payloads are denied and empty payloads remain allowed. | met | `command_constraint_violation()` now validates payload schema before checking whether the lease has `max_speed_mps`. Regressions: `no_speed_payload_allows_empty_payload` and `no_speed_payload_rejects_nonempty_uninterpreted_fields`; focused `cargo test -p rclp-edge-verifier no_speed_payload --test vector_tests` passed, 2 tests. |
| RCLP-52C0-002: Policy-required `human_operator_available` must be explicitly present in signed `RobotStateAssertion` before policy allow; explicit true remains allowed and explicit false remains denied. | met | `state_auth_violation()` now accepts policy-dependent required wire fields, and policy evaluation requires explicit `human_operator_available` when policy does. Regressions: `test_policy_required_human_operator_state_must_be_explicit_before_policy_allow` and `test_explicit_human_operator_available_state_still_allows_policy`; focused pytest passed. Existing explicit-false denial remains covered in `tests/test_protocol_flow.py`. |
| RCLP-52C0-003: Rust geofence-required authority rejects empty or whitespace signed geofence identifiers in lease constraints and local state, while valid matching geofences remain allowed. | met | Required Rust lease geofence constraints are trim-checked, and blank signed local geofence state is treated as a geofence violation. Regressions: `blank_geofence_ids_do_not_satisfy_required_geofence_constraint` and `blank_local_geofence_state_rejects_valid_geofence_constraint`; focused `cargo test` filters passed. |
| RCLP-52C0-004: Audit JSONL import rejects `null` for required integrity fields, especially `payload_hash`, before `AuditCommit` normalization; valid anchored imports remain accepted. | met | `load_jsonl()` rejects null values for required load fields before `AuditCommit.model_validate()` can recompute fields. Regression: `test_load_jsonl_rejects_null_required_integrity_field_before_model_repair` passed for `payload_hash` and `integrity_proof`; valid anchored import remains covered by round-trip and full audit tests. |
| Security-relevant tests cover every changed behavior and legitimate behavior remains covered. | met | Focused gates passed, then `.venv/bin/python -m pytest tests/test_security_negative_paths.py tests/test_audit.py tests/test_protocol_flow.py tests/test_conformance_contract.py tests/test_demo_remote_assist.py -q` passed, 222 tests; `cargo test -p rclp-edge-verifier --test vector_tests` passed, 43 tests; `.venv/bin/python -m compileall src tests` passed. |
| Assembly spec-conformance review is clean and post-review gates pass. | met | Subagent review found no code-level correctness, authority, robotics safety-adjacent, provenance, or audit-integrity blocker; it only requested this final ledger update. Full gates passed: `.venv/bin/python -m pytest -q` passed, 228 tests; `.venv/bin/python tests/evals/eval_runner.py` passed, 33 evals; `cargo test --workspace` passed, 3 unit tests and 43 vector tests; `.venv/bin/ruff check .` passed; `.venv/bin/ruff format --check .` passed; `cargo fmt --all -- --check` passed; `cargo clippy --workspace --all-targets -- -D warnings` passed; `git diff --check` passed. |

Changed files:

- `src/rclp_core/state.py`
- `src/rclp_core/policy.py`
- `src/rclp_core/audit.py`
- `src/rclp_agents/demo_remote_assist.py`
- `crates/rclp-edge-verifier/src/verifier.rs`
- `tests/test_security_negative_paths.py`
- `tests/test_audit.py`
- `tests/test_protocol_flow.py`
- `tests/test_conformance_contract.py`
- `crates/rclp-edge-verifier/tests/vector_tests.rs`

Review notes:

- Assembly reviewer classified the four remediation contracts as met and found
  no code-level correctness, authority, robotics safety-adjacent, provenance,
  or audit-integrity blocker. The only review finding was that this ledger
  still carried planned evidence; this section now records final evidence.
- No cloud jobs, AWS Lambda functions, GPU jobs, or paid compute were launched,
  stopped, resized, deleted, or otherwise mutated.

## Post-Scan 6-Finding Security Remediation - 2026-06-24 (scan ccd6c9e8)

Status: successful

Source contract:

- User request: resolve all six findings from Codex Security scan
  `ccd6c9e8-b196-443b-8587-f6b28540312a` using `assembly` and lambda.
- Scan report:
  `local Codex Security report artifact redacted`
- `AGENTS.md`
- Required repo doctrine under `docs/`
- `docs/PROTOCOL_SPEC_DRAFT.md`
- `docs/THREAT_MODEL.md`
- `docs/TEST_STRATEGY.md`

Preflight note:

- No cloud jobs, GPU jobs, or paid compute are required for this remediation.
  The user said "lambda", but there is no repo/tool Lambda smoke contract for
  these findings; no AWS Lambda or paid compute will be launched, stopped,
  resized, deleted, or otherwise mutated without explicit current-turn
  authorization for that exact action.
- Assembly review used the available multi-agent reviewer after focused
  implementation smoke passed.

Target contract:

Close the six validated findings at their root authority contracts: signed
authority fields required by the manifest must be explicit before verification
or policy use; request signed material must be size-bounded before decode,
canonicalization, or verification; attestation trust must bind freshness and key
identity; side-effecting post-auth command denials must be replay-idempotent;
pre-auth revocation rejections must not attribute authenticated actors from
unverified claims; and Rust file replay stores must durably install fresh store
directories before advertising durable shared replay state.

Success criterion:

The original vulnerable paths no longer reproduce, focused regressions prove
each invariant and legitimate behavior, local validation gates pass, assembly
spec-conformance review is clean, post-review gates pass, and this ledger is
updated with final evidence.

Definition of done:

| Item | Status | Evidence |
|---|---|---|
| RCLP-CCD6-001: manifest-required `CapabilityRequest.requested_duration_seconds` and `RobotStateAssertion.safety_state` are rejected when absent from the signed wire model before policy allow. | met | `CapabilityRequest` auth now checks `model_fields_set` for explicit `requested_duration_seconds`; `RobotStateAssertion` auth checks explicit `safety_state`. Regressions: `test_capability_request_missing_explicit_duration_is_denied_before_policy_allow` and `test_robot_state_missing_explicit_safety_state_is_denied_before_policy_allow`. |
| RCLP-CCD6-002: invalid oversized signed `CapabilityRequest` material is rejected before base64 decode, canonical JSON, or signature verification. | met | Request signature text and signed request fields are budgeted before `verify_with_public_key_b64()`. Regressions monkeypatch verify/canonicalization: `test_oversized_request_signature_rejects_before_decode_or_verify` and `test_oversized_request_signed_field_rejects_before_canonical_json`. |
| RCLP-CCD6-003: `AgentAttestation` trust requires bounded freshness and `public_key_id` binding to the trusted key record. | met | `attestation_trust_violation()` now enforces freshness, rejects future/stale timestamps, and requires the attested `public_key_id` to match trusted key-id state. Regressions: `test_agent_attestation_rejects_stale_trust_material`, `test_agent_attestation_rejects_unbound_public_key_id`, and the signed happy path with explicit key-id trust. |
| RCLP-CCD6-004: `CommandGate` consumes authenticated side-effecting denials so repeated post-auth denials do not re-emit fallback hooks. | met | After command auth and local-edge checks, lease-validation denials now record command replay state before emitting fallback. Regressions: `test_missing_lease_denial_consumes_command_replay_state_before_fallback_side_effect` and `test_replayed_post_auth_denial_does_not_reemit_fallback`. |
| RCLP-CCD6-005: pre-auth revocation rejections use a local unauthenticated audit actor and keep claimed revoker identity only as untrusted payload context. | met | Pre-signature and untrusted revocation rejection paths now audit as `local_command_gate` and store the claimed actor only as `claimed_revoked_by`; authenticated post-signature rejections keep authenticated actor attribution. Regressions cover unsigned and tampered revocations. |
| RCLP-CCD6-006: Rust `FileReplayCache` fsyncs newly created replay-store directory entries before reporting durable shared replay state. | met | `FileReplayCache::new()` computes the missing directory chain, creates it, fsyncs every created parent entry including `.` for first-level relative stores, then fsyncs the created directory. Regressions: `file_replay_cache_creates_nested_fresh_store_as_durable_shared`, `first_level_relative_store_syncs_current_directory_parent`, and `nested_relative_store_syncs_named_parent`. |
| Security-relevant tests cover every changed behavior and legitimate behavior remains covered. | met | Focused Python and Rust regressions passed, followed by final `compileall`, full `pytest`, eval runner, Rust workspace tests, Rust clippy, Ruff check, Ruff format check, Rust format check, and whitespace checks. |
| Assembly spec-conformance review is clean and post-review gates pass. | met | Lambda-style reviewer initially found the relative replay-store fsync gap. The Rust helper was fixed, focused regressions passed, and re-review returned PASS for RCLP-CCD6-006. Post-review gates passed. |

Changed files:

- `src/rclp_core/policy.py`
- `src/rclp_core/state.py`
- `src/rclp_core/attestation.py`
- `src/rclp_ros2/command_gate.py`
- `crates/rclp-edge-verifier/src/replay.rs`
- `tests/test_security_negative_paths.py`
- `crates/rclp-edge-verifier/tests/vector_tests.rs`
- `src/rclp_agents/central_agent_mock.py`
- `src/rclp_agents/demo_remote_assist.py`
- `tests/test_protocol_flow.py`
- `tests/test_conformance_contract.py`
- `tests/evals/eval_runner.py`

Validation evidence:

- `.venv/bin/python -m pytest tests/test_security_negative_paths.py -q` passed, 155 tests.
- `.venv/bin/python -m pytest tests/test_protocol_flow.py tests/test_conformance_contract.py tests/test_demo_remote_assist.py tests/test_protocol_evals.py -q` passed, 53 tests.
- `.venv/bin/python -m compileall src tests` passed.
- `.venv/bin/python -m pytest -q` passed, 224 tests.
- `.venv/bin/python tests/evals/eval_runner.py` passed, 33 evals.
- `cargo test --workspace` passed, including 3 Rust unit tests and 39 vector tests.
- `cargo clippy --workspace --all-targets -- -D warnings` passed.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format --check .` passed.
- `cargo fmt --all -- --check` passed.
- `git diff --check` passed.

Review notes:

- Lambda-style assembly review initially classified RCLP-CCD6-006 as partial
  because first-level relative fresh replay-store paths skipped fsyncing the
  current directory entry. `directory_parent_to_sync()` now maps that case to
  `.` and has direct regression coverage. Re-review returned PASS.
- No cloud jobs, AWS Lambda functions, GPU jobs, or paid compute were launched,
  stopped, resized, deleted, or otherwise mutated.

## Post-Scan 4-Finding Security Remediation - 2026-06-24

Status: successful

Source contract:

- User request: fix all four findings from the completed Codex Security scan
  using `assembly`.
- Completed Codex Security scan `fe1e1ee8-6dc6-4ec4-8f30-5d91d883afc0`.
- Scan report:
  `local Codex Security report artifact redacted`
- `AGENTS.md`
- Required repo doctrine under `docs/`
- `docs/PROTOCOL_SPEC_DRAFT.md`
- `docs/THREAT_MODEL.md`
- `docs/TEST_STRATEGY.md`

Preflight note:

- No cloud jobs, GPU jobs, or paid compute are required for this remediation,
  and none will be launched, stopped, resized, deleted, or otherwise mutated.
- Assembly review will use the available multi-agent reviewer after focused
  implementation smoke passes.

Target contract:

Close the four validated findings at their root authority/audit contracts:
Rust command replay state must not be consumed until all non-replay authority
checks have passed; Python lease verification must reject over-budget signed
lease material before canonicalization or signature verification; protocol
models must reject stringly booleans and numerics at trust boundaries; and
audit JSONL import must not let mutable imported authority classification opt
out of trusted chain anchoring.

Success criterion:

The original reproductions no longer succeed, focused regressions prove each
invariant and legitimate behavior, focused and full local gates pass, assembly
spec-conformance review is clean, and post-review gates pass.

Definition of done:

| Item | Status | Evidence |
|---|---|---|
| RCLP-RUST-REPLAY-FINALIZE-001: Rust verifier defers command replay key consumption until lease signature, context, local state, network policy, and command constraints have passed; invalid lease presentation must not poison a later valid command. | met | Command authentication is now side-effect free. Final allow/degrade replay state is committed in one batch for command id, command nonce, and lease nonce. Regressions: `invalid_lease_after_command_auth_does_not_poison_command_replay_state` and `replayed_lease_nonce_does_not_poison_fresh_command_replay_state`. |
| RCLP-PY-LEASE-MATERIAL-BUDGET-001: Python lease validation rejects over-budget signed lease fields before canonical JSON or signature verification. | met | `lease_signed_material_too_large()` now applies per-field and aggregate budgets to all signed lease text fields before `verify_lease_signature()`. Regression `test_oversized_lease_signed_field_rejects_before_canonical_json_or_verify` monkeypatches verification to prove it is not reached. |
| RCLP-PY-STRICT-SCALARS-001: Authority-relevant protocol models reject string booleans, string numerics, and other scalar coercions at trust boundaries while preserving valid numeric and datetime behavior. | met | Protocol and policy models now use pre-validation for authority bool/int/number fields. Regressions cover core message models, audit `authority_relevant`, policy TTL, policy booleans, policy max speed, and policy network thresholds; integer JSON numbers still validate for float fields. |
| RCLP-PY-AUDIT-IMPORT-ANCHOR-001: Audit JSONL import requires explicit trusted-chain anchoring by default and diagnostic-only import is an explicit caller-selected mode, not inferred from mutable imported rows. | met | `load_jsonl()` defaults to `authority_chain` import and requires a trusted head for any non-empty authority import after structural integrity validation. Diagnostic import is only available through explicit `import_profile="diagnostic_only"`. Regression covers recomputed demoted diagnostic-looking import. |
| Security-relevant tests cover every changed behavior and legitimate behavior remains covered. | met | Focused Rust and Python regressions passed, followed by full local validation, Rust workspace tests, eval runner, Ruff, format, and whitespace checks. |
| Assembly spec-conformance review is clean and post-review gates pass. | met | Assembly reviewer initially found partial replay poisoning on replayed lease nonce and policy scalar coercion. Both were fixed, the focused reruns passed, and follow-up review reported PASS with no remaining findings. |

Validation evidence:

- `cargo test -p rclp-edge-verifier replayed_lease_nonce_does_not_poison_fresh_command_replay_state` passed.
- `.venv/bin/python -m pytest tests/test_security_negative_paths.py::test_oversized_lease_signed_field_rejects_before_canonical_json_or_verify tests/test_security_negative_paths.py::test_authority_models_reject_string_numeric_and_boolean_scalars_at_boundary tests/test_security_negative_paths.py::test_json_integer_network_metrics_remain_valid_numbers tests/test_audit.py::test_load_jsonl_rejects_demoted_authority_event_without_explicit_diagnostic_import -q` passed, 4 tests.
- `.venv/bin/python -m pytest tests/test_security_negative_paths.py::test_policy_rejects_string_numeric_and_boolean_scalars_before_digest_pin tests/test_security_negative_paths.py::test_authority_models_reject_string_numeric_and_boolean_scalars_at_boundary -q` passed, 2 tests.
- `.venv/bin/python -m compileall src tests` passed.
- `.venv/bin/python -m pytest` passed, 203 tests.
- `cargo test --workspace` passed, 38 Rust vector tests plus unit/doc tests.
- `cargo fmt --all -- --check` passed.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format --check .` passed.
- `git diff --check` passed.
- `.venv/bin/python tests/evals/eval_runner.py` passed, 33 evals.

Review notes:

- Initial assembly review found two residual blockers: command replay keys were still consumed before lease nonce replay rejection, and policy models still coerced scalar authority values before digesting. Both were corrected before final gates.
- The Rust replay cache now reports the rejected batch index so the verifier can keep precise denial reasons without committing partial replay state.
- No cloud jobs, GPU jobs, or paid compute were launched, stopped, resized, deleted, or otherwise mutated.

## Post-Scan 6-Finding Security Remediation - 2026-06-24

Status: successful

Source contract:

- User request: resolve all six findings from the completed Codex Security scan
  using `assembly`.
- Completed Codex Security scan `e2918d26-8d2f-4eb1-81e1-6a26c2f36bdd`.
- Scan report:
  `local Codex Security report artifact redacted`
- `AGENTS.md`
- Required repo doctrine under `docs/`
- `docs/PROTOCOL_SPEC_DRAFT.md`
- `docs/THREAT_MODEL.md`
- `docs/TEST_STRATEGY.md`

Changed files:

- `src/rclp_core/policy.py`
- `src/rclp_core/conformance.py`
- `src/rclp_core/leases.py`
- `src/rclp_ros2/command_gate.py`
- `src/rclp_agents/demo_remote_assist.py`
- `tests/test_security_negative_paths.py`
- `tests/test_demo_remote_assist.py`
- `tests/evals/eval_runner.py`

Preflight note:

- No cloud jobs, GPU jobs, or paid compute are required for this remediation,
  and none will be launched, stopped, resized, deleted, or otherwise mutated.
- Assembly review will use the available multi-agent reviewer after focused
  implementation smoke passes.

Target contract:

Close the six validated findings at their root authority contracts: requester
constraints must only narrow policy-owned authority; command payload schema
validation must not disappear for no-speed leases; lease and revocation signed
material must be bounded before decode, canonicalization, or signature
verification; revocation acceptance must be bound to the receiving local edge;
and demo lease issuance must be committed into the chained audit trail.

Success criterion:

The original vulnerable paths no longer reproduce, focused regressions prove
each invariant and legitimate behavior, full local validation gates pass,
assembly spec-conformance review is clean, and post-review gates pass.

Definition of done:

| Item | Status | Evidence |
|---|---|---|
| RCLP-W06-001: `max_speed_mps` can only be accepted as a narrowing of an explicit policy-owned speed ceiling. | met | `PolicyRequirements.max_speed_mps` is now the policy-owned ceiling copied into base lease constraints. Requested speed constraints are denied when policy omits speed authority or when the request exceeds the policy ceiling. Regressions: `test_requested_speed_constraint_cannot_create_policy_authority` and `test_requested_speed_constraint_can_narrow_policy_owned_ceiling`. |
| RCLP-W07-001: command payload schema validation runs for no-speed leases and rejects unknown executable payload fields. | met | `validate_command_payload_against_constraints()` now requires a payload object, rejects unknown top-level executable fields before speed handling, accepts `{}` for no-speed leases, and rejects nonempty no-speed payloads with `COMMAND_PAYLOAD_SCHEMA_VIOLATION`. Regressions cover empty allowed and nonempty no-speed denial cases; eval defaults were updated to `{}` so speed scenarios stay explicit. |
| CS-RCLP-W04-001: demo allow decisions commit issued lease identity and digest into the hash-chained audit log. | met | The demo normal allow path now records one authoritative `capability_allowed` event after lease issuance. That event includes lease id, lease message id, nonce, signature, digest, policy context, constraints, network state, geofence state, and causal related message ids. Regression asserts there is exactly one allow event and every allow audit includes lease identity and digest. |
| RCLP-W05-001: oversized lease signatures are rejected before base64 decode, canonicalization, or public-key verification. | met | Lease signature text is bounded to the Ed25519 base64 size before `verify_lease_signature()` can decode or verify. Regression `test_oversized_lease_signature_rejects_before_decode_or_verify` monkeypatches public-key verification to prove it is not reached. |
| RCLP-W07-002: revocations for nonlocal lease or revocation edge ids are rejected before durable state mutation or fallback side effects. | met | `CommandGate.revoke()` now rejects revocations whose lease edge or revocation edge does not match the configured local edge before storing revocation state or emitting fallback. Regressions cover mismatched revocation edge and nonlocal lease edge without fallback side effects. |
| RCLP-W07-003: revocation signed material is bounded across all signed text fields before canonicalization or signature verification. | met | Revocation signed text now uses the same field-budget primitive across protocol, ids, actor ids, reason, fallback, robot, mission, capability, and signature before canonicalization or verify. Regression `test_oversized_revocation_signed_field_rejects_before_canonical_json` proves canonical JSON and signature verification are not reached. |
| Security-relevant tests cover every changed behavior and legitimate behavior remains covered. | met | Passed focused security/demo/eval tests, `compileall`, full pytest, standalone eval runner, Ruff check, Ruff format check, and `git diff --check`. |
| Assembly spec-conformance review is clean and post-review gates pass. | met | Multi-agent reviewer initially found the duplicate incomplete demo allow audit and formatting drift. The demo audit was changed to emit one lease-bearing allow event, touched files were formatted, and reviewer re-check reported no remaining security blockers. Post-review validation gates passed. |

Validation evidence:

- `.venv/bin/python -m pytest tests/test_demo_remote_assist.py tests/test_protocol_evals.py::test_eval_runner_executes_required_scenario_set -q` passed, 3 tests.
- `.venv/bin/python -m pytest tests/test_security_negative_paths.py -q` passed, 130 tests.
- `.venv/bin/python -m compileall src tests` passed.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format --check .` passed.
- `git diff --check` passed.
- `.venv/bin/python -m pytest` passed, 198 tests.
- `.venv/bin/python tests/evals/eval_runner.py` passed, 33 evals.

Review notes:

- The normal demo allow path uses a private policy-evaluation log, then appends
  the single lease-bearing authority event to the replayable audit chain after
  issuance. Degrade and deny paths still use the core policy audit directly
  because they do not mint lease authority.
- Command payload defaults in the eval runner are now `{}`. Speed-related evals
  remain explicit through scenario payloads and lease constraints.
- No cloud jobs, GPU jobs, or paid compute were launched, stopped, resized,
  deleted, or otherwise mutated.

## Post-Scan 3-Finding Security Remediation - 2026-06-24 (payload/edge/signature)

Status: successful

Source contract:

- User request: fix all three findings from the completed Codex Security scan
  using `assembly`.
- Completed Codex Security scan `b62a8bb7-0f0e-48fb-bad2-b0a390b989f1`.
- Scan report:
  `local Codex Security report artifact redacted`
- `AGENTS.md`
- Required repo doctrine under `docs/`
- `docs/PROTOCOL_SPEC_DRAFT.md`
- `docs/THREAT_MODEL.md`
- `docs/TEST_STRATEGY.md`

Preflight note:

- No cloud jobs, GPU jobs, or paid compute are required for this remediation,
  and none will be launched, stopped, resized, deleted, or otherwise mutated.
- The active tool policy does not allow spawning subagents unless the user
  explicitly asks for subagents or delegation, so the assembly review gate will
  be completed in-thread unless explicit delegation is later requested.

Target contract:

Close the three validated scan findings at their root authority contracts:
the Rust verifier must enforce a typed payload contract for speed-constrained
commands; Python `CommandGate` must own and enforce the configured local edge
identity even when called directly; and command/revocation signature text must
be cheaply bounded before base64 decode or signature verification.

Success criterion:

Nested or unknown executable payload fields cannot bypass Rust
`max_speed_mps` enforcement; direct `CommandGate.evaluate()` rejects commands
or leases for non-local edges before lease validation can allow; oversized
command and revocation signatures are rejected before `unb64()` or
`verify_with_public_key_b64()` can process them; focused regressions, full
local gates, assembly spec-conformance review, and post-review gates pass.

Definition of done:

| Item | Status | Evidence |
|---|---|---|
| RCLP-RUST-PAYLOAD-SCHEMA-001: Rust verifier enforces a typed payload contract for speed-constrained commands and rejects nested or unknown payload members that are outside the local constraint decision. | met | `crates/rclp-edge-verifier/src/verifier.rs` now treats speed-constrained payloads as a typed schema with only top-level `max_speed_mps` and `speed_mps`; unknown top-level members, including nested `motion`, `trajectory`, and vendor motion fields, reject with `DENY_COMMAND_CONSTRAINT`. Rust regressions `speed_limited_payload_accepts_supported_speed_aliases` and `speed_limited_payload_rejects_unknown_motion_fields` passed. Python conformance now mirrors the same schema with `COMMAND_PAYLOAD_SCHEMA_VIOLATION` for speed-constrained unknown members. |
| RCLP-WRONG-LOCAL-EDGE-DIRECT-GATE-001: Python `CommandGate` binds direct evaluation to a configured local edge identity and rejects command or lease edge mismatches before lease validation can authorize. | met | `CommandGate` now requires `local_edge_agent_id`, rejects non-local command/lease edge context with `EDGE_AGENT_MISMATCH`, and `EdgeAgentDaemon` validates that it wraps a gate for the same local edge. Regressions `test_direct_command_gate_rejects_nonlocal_edge_context_before_lease_validation` and `test_nonlocal_edge_rejection_does_not_consume_command_replay_nonce` passed, and existing daemon mismatch tests stayed green. |
| RCLP-PY-SIGNATURE-PREAUTH-BOUNDS-001: Python command and revocation paths reject over-budget signature text before base64 decode, canonical re-encode, or signature verification. | met | `_command_auth_violation()` checks signed command material before `unb64()`, and `revoke()` rejects oversized revocation signatures with `REVOCATION_SIGNED_MATERIAL_TOO_LARGE` before `verify_with_public_key_b64()`. Monkeypatched regressions `test_oversized_command_signature_rejects_before_decode_or_verify` and `test_oversized_revocation_signature_rejects_before_decode_or_verify` prove decode/verify are not reached. |
| Security-relevant tests cover every changed behavior and legitimate behavior remains covered. | met | Passed: focused payload tests (`cargo test -p rclp-edge-verifier --test vector_tests speed_limited_payload`, `.venv/bin/python -m pytest tests/test_security_negative_paths.py::test_max_speed_constraint_is_enforced_against_command_payload -q`); focused local-edge/replay tests; focused signature-ordering tests; `.venv/bin/python -m compileall src tests`; `.venv/bin/python -m pytest` (190 passed); `.venv/bin/python tests/evals/eval_runner.py` (33 passed, 0 failed); `cargo test --workspace`; `cargo clippy --workspace --all-targets -- -D warnings`; `cargo fmt --all -- --check`; `.venv/bin/ruff check .`; `.venv/bin/ruff format --check .`; `git diff --check`. |
| Assembly spec-conformance review is clean and post-review gates pass. | met | In-thread assembly review found one valid ordering issue: non-local edge rejection was happening after command replay consumption inside command authentication. The fix moved replay consumption after local-edge checks and added `test_nonlocal_edge_rejection_does_not_consume_command_replay_nonce`. Post-review full Python, eval, Rust, lint, format, and whitespace gates passed. |

Review notes:

- The payload remediation is intentionally fail-closed for the MVP
  speed-constrained profile: payload members outside the typed top-level speed
  schema are rejected instead of inferred as non-executable.
- `CommandGate` now owns the local edge identity contract directly. The daemon
  remains a wrapper and refuses to wrap a gate for a different local edge.
- Command replay consumption now happens after command authentication and local
  edge binding, so a valid command addressed to another edge cannot poison the
  local replay cache.
- Subagent review was not spawned because the active tool policy only permits
  subagents when the user explicitly asks for subagents or delegation; the
  assembly review gate was completed in-thread.

## Post-Scan 3-Finding Security Remediation - 2026-06-24

Status: successful

Source contract:

- User request: fix all three findings from the completed Codex Security scan
  using `assembly`.
- Completed Codex Security scan `c3b45b5d-eeef-4363-b1f6-52e2b36a6539`.
- Scan report:
  `local Codex Security report artifact redacted`
- `AGENTS.md`
- Required repo doctrine under `docs/`
- `docs/PROTOCOL_SPEC_DRAFT.md`
- `docs/THREAT_MODEL.md`
- `docs/TEST_STRATEGY.md`

Preflight note:

- `DIRECTION.md` is listed as required reading in `AGENTS.md`, but is absent
  in the current checkout after prior user-directed cleanup. The remaining
  required doctrine files and scan artifacts are the active implementation
  contract.
- No cloud jobs, GPU jobs, or paid compute are required for this remediation,
  and none will be launched, stopped, resized, deleted, or otherwise mutated.

Target contract:

Close the three validated findings at their root authority contracts: Rust
lease TTL duration must not be inflated by clock-skew tolerance; Rust
`FileReplayCache` must acknowledge consumed replay markers only after a durable
commit protocol; and Python `CommandGate` must reject oversized signed command
material before signature verification canonicalizes attacker-controlled input.

Success criterion:

Rust verifier denies leases whose signed duration exceeds the exact local
`max_lease_ttl_ms`; `FileReplayCache::consume_nonce()` performs a durable file
and directory commit before returning success; Python command auth rejects
oversized scalar, payload, node-count, and nesting-depth material before
`canonical_json()` runs; focused regressions, full local gates, assembly
spec-conformance review, and post-review gates pass.

Definition of done:

| Item | Status | Evidence |
|---|---|---|
| RCLP-RUST-TTL-STRICT-001: Rust verifier enforces signed lease duration against the exact local policy maximum, with clock skew only for instant/freshness comparisons. | met | `crates/rclp-edge-verifier/src/verifier.rs` now compares signed lease duration directly to `trusted_context.max_lease_ttl_ms`; clock skew remains only on age/freshness checks. Rust regressions `lease_ttl_exact_policy_maximum_is_allowed` and `lease_ttl_max_plus_one_is_rejected` cover exact max allow and `max + 1` denial. |
| RCLP-RUST-REPLAY-DURABLE-COMMIT-001: `FileReplayCache` only returns successful nonce consumption after durable marker commit and parent directory sync, failing closed on durability errors. | met | `FileReplayCache::consume_nonce()` now creates the marker with `create_new`, writes the nonce, `sync_all()`s the file, `sync_all()`s the parent directory, and returns `false` on commit errors. Regression `file_replay_cache_writes_marker_and_rejects_duplicate_nonce` proves an accepted nonce has an observable marker and is not accepted again. |
| RCLP-PY-COMMAND-SIGNED-MATERIAL-BOUNDS-001: Python `CommandGate` bounds signed command material before invalid-signature verification can canonicalize untrusted input. | met | `src/rclp_ros2/command_gate.py` now checks signed command scalar, total text, payload estimated size, payload node count, and payload depth before `verify_with_public_key_b64()` can canonicalize the command. Python regressions prove oversized scalar, payload, and nesting reject with `COMMAND_SIGNED_MATERIAL_TOO_LARGE` while `canonical_json()` is not called, and malformed signature behavior remains `COMMAND_SIGNATURE_INVALID` without canonicalization. |
| Security-relevant tests cover every changed behavior and legitimate behavior remains covered. | met | Passed: `cargo test -p rclp-edge-verifier --test vector_tests lease_ttl`; `cargo test -p rclp-edge-verifier --test vector_tests file_replay_cache_writes_marker_and_rejects_duplicate_nonce`; `cargo test -p rclp-edge-verifier --test vector_tests` (34 passed); `cargo test --workspace` (1 lib test, 34 vector tests, doc-tests); `cargo clippy --workspace --all-targets -- -D warnings`; `cargo fmt --all -- --check`; `.venv/bin/python -m compileall src tests`; `.venv/bin/python -m pytest tests/test_security_negative_paths.py` (113 passed); `.venv/bin/python -m pytest` (181 passed); `.venv/bin/python tests/evals/eval_runner.py` (33 passed, 0 failed); `.venv/bin/ruff check .`; `.venv/bin/ruff format --check .`; `git diff --check`. |
| Assembly spec-conformance review is clean and post-review gates pass. | met | Review pass checked the changed Rust/Python authority boundaries against this DoD and found no remaining code-level issues. A delegated subagent was not spawned because the active tool policy permits subagents only when the user explicitly asks for delegation; the assembly review discipline was still completed in-thread. Post-review targeted Python tests, Ruff lint/format, Rust fmt, Clippy, and whitespace checks passed. |

Review notes:

- The TTL remediation is intentionally narrow: it removes skew tolerance from
  duration enforcement while preserving skew on time-window freshness checks.
- The replay remediation is fail-closed: if marker write, file sync, or parent
  directory sync fails, nonce consumption is not reported as successful.
- The Python remediation keeps missing and malformed signatures on their
  existing command-auth paths, while oversized syntactically valid but invalid
  signed command material is rejected before command canonicalization.
- The active tool policy requires explicit user delegation before spawning
  subagents, so this assembly run used an in-thread spec-conformance review
  instead of a delegated reviewer.

## Post-Scan 3-Finding Security Remediation - 2026-06-23

Status: successful

Source contract:

- User request: resolve all three Codex Security findings using `assembly`.
- Completed Codex Security scan `0babed54-469b-4f62-b7b5-201359a5bc02`.
- Scan report:
  `local Codex Security report artifact redacted`
- `AGENTS.md`
- Required repo doctrine under `docs/`
- `docs/PROTOCOL_SPEC_DRAFT.md`
- `docs/THREAT_MODEL.md`
- `docs/TEST_STRATEGY.md`

Preflight note:

- `DIRECTION.md` is listed as required reading in `AGENTS.md`, but is absent
  in the current checkout after prior user-directed cleanup. The remaining
  required doctrine files and scan artifacts are the active implementation
  contract.
- No cloud jobs, GPU jobs, or paid compute are required for this remediation,
  and none will be launched, stopped, resized, deleted, or otherwise mutated.

Target contract:

Close the three validated scan findings at their root authority contracts:
Python command-gate authorization must require a signed lease policy reference
that matches an accepted local policy pin; the Rust verifier must fail closed
unless replay state is explicitly durable/shared for production verification;
and Rust command authentication must bound attacker-controlled signed command
material before invalid signatures can consume unbounded canonicalization
resources.

Success criterion:

Missing or mismatched Python lease policy provenance is denied before
`LEASE_VALID`; Rust verifier calls reject non-durable replay caches and preserve
nonce consumption across verifier restart when backed by a shared store; Rust
verifier rejects oversized signed command fields and oversized or overly deep
command payloads before HMAC canonicalization; focused regressions, full local
gates, subagent spec-conformance review, and post-review gates pass.

Definition of done:

| Item | Status | Evidence |
|---|---|---|
| RCLP-PY-LEASE-POLICY-PROVENANCE-001: Python command-gate lease validation requires accepted policy id/digest inputs and rejects signed leases whose policy provenance is missing or mismatched. | met | `CapabilityLease` and `issue_lease()` require nonblank `policy_id` and `policy_digest`; `CommandGate` requires accepted policy pins; `validate_lease_for_command()` rejects missing or mismatched signed provenance. Focused regressions cover matching, missing, and digest-mismatch signed lease provenance. |
| RCLP-RUST-REPLAY-DURABILITY-001: Rust verifier API rejects non-durable replay stores for production verification and keeps command/lease replay state durable across verifier restart. | met | `ReplayCacheDurability` makes durability explicit, `verify_json_value()` and `verify()` deny non-durable replay caches before authority decisions, and `FileReplayCache` provides a local durable/shared reference implementation. Rust regressions cover non-durable rejection, signed command replay after cache recreation, and lease nonce replay after cache recreation with a fresh signed command. |
| RCLP-RUST-PREAUTH-PAYLOAD-BOUNDS-001: Rust verifier bounds signed command material before command HMAC canonicalization on untrusted inputs. | met | The verifier checks a signed-material budget before command HMAC verification, covering command scalar fields, signature text, lease/local signed text, and command payload size, node count, and nesting depth. Over-budget material returns `DENY_COMMAND_SIGNED_MATERIAL_TOO_LARGE` through a diagnostic/non-authority denial. Focused Rust regressions cover oversized scalar command fields and oversized/deep payloads before HMAC canonicalization. |
| Security-relevant tests cover every changed behavior and legitimate behavior remains covered. | met | Passed after review fixes: `.venv/bin/python -m compileall src tests`; `.venv/bin/python -m pytest` (177 passed); `.venv/bin/python tests/evals/eval_runner.py` (33 passed, 0 failed); `cargo test --workspace` (1 lib test plus 31 vector tests); `cargo test -p rclp-edge-verifier --test vector_tests` (31 passed); `cargo clippy --workspace --all-targets -- -D warnings`; `cargo fmt --all -- --check`; `.venv/bin/ruff check .`; `.venv/bin/ruff format . --check`; `git diff --check`. |
| Assembly spec-conformance review is clean and post-review gates pass. | met | Reviewer `019ef67d-d89b-7163-970d-f4006e2c00c8` ("Nash") found valid follow-ups for non-payload command-field bounds, lease-nonce restart evidence, and stale docs/ledger evidence. Code and docs were fixed, Nash re-reviewed the code/security paths as met with no remaining code-level findings, and this ledger entry is now closed with post-review gate evidence. |

Review notes:

- Initial reviewer `019ef67d-d89b-7163-970d-f4006e2c00c8` ("Nash")
  found one valid P2 gap: the original pre-auth Rust budget only covered
  `command.payload`, while command HMAC canonicalization also signs scalar
  command fields. The fix broadened the gate to signed command material before
  HMAC canonicalization and added
  `oversized_signed_command_field_is_rejected_before_hmac_canonicalization`.
- The same reviewer found a replay evidence gap: command replay after cache
  recreation did not independently prove lease nonce durability. The fix added
  `file_replay_cache_preserves_lease_nonce_after_verifier_recreation`, which
  resigns a fresh command while reusing the lease nonce and expects
  `DENY_REPLAYED_NONCE`.
- The Rust verifier exports `FileReplayCache` as a local durable reference
  cache for tests and adapters. Production clustered edge deployments still
  need a production replay service that preserves the same atomic consume
  contract across verifier instances and restarts.
- Final re-review status: clean for the code/security remediation paths. The
  only remaining reviewer note was this ledger entry being stale; the entry was
  updated after that re-review and the clean post-review gates above.

## Post-Scan 9-Finding Security Remediation - 2026-06-23

Status: successful

Source contract:

- User request: resolve all Codex Security findings using `assembly`.
- Completed Codex Security scan `d43b49d8-a432-4000-a90b-0e1c8fcf74cf`.
- Scan report:
  `local Codex Security report artifact redacted`
- `AGENTS.md`
- Required repo doctrine under `docs/`
- `docs/PROTOCOL_SPEC_DRAFT.md`
- `docs/THREAT_MODEL.md`
- `docs/TEST_STRATEGY.md`

Preflight note:

- No cloud jobs or paid compute are required for this remediation, and none
  will be launched, stopped, resized, deleted, or otherwise mutated.
- `DIRECTION.md` was listed in repo instructions but is absent in the current
  checkout; the remaining doctrine files and scan report are the active
  implementation contract.

Target contract:

Close the nine validated findings at their root authority contracts: policy and
message trust boundaries must reject unknown future authority fields,
temporary stores must not satisfy durable-store requirements, revocation
messages must be idempotent across replay and restart, Rust lease and command
verification must bind the protocol envelope, command payload, and signed
policy provenance, unauthenticated Rust command denials must not trust claimed
command provenance, and repo docs must not preserve live Lambda identifiers.

Definition of done:

| Item | Status | Evidence |
|---|---|---|
| Policy digest pinning hashes only strict, known policy fields and rejects unknown top-level or nested policy input. | met | `Policy`, `PolicyRequirements`, `NetworkRequirements`, and `FallbackPolicy` now forbid extras; `test_policy_rejects_unknown_top_level_field_before_digest_pin` and `test_policy_rejects_unknown_nested_field_before_digest_pin` prove hidden fields fail before digest acceptance. |
| Temporary request replay, command replay, and revocation stores are explicitly non-durable and fail closed at issuance/gate boundaries. | met | `RequestReplayCache.temporary()`, `CommandReplayCache.temporary()`, and `RevocationStore.temporary()` set `durable=False`; policy/gate constructors reject them. `test_policy_rejects_ephemeral_temporary_replay_store_for_authority_issuance` and `test_command_gate_rejects_ephemeral_temporary_stores` cover the original path. |
| Rust verifier requires versioned protocol envelope and payload binding for signed leases and commands. | met | Rust `CapabilityLeaseClaims` and `EdgeCommand` now require protocol envelope fields; command HMAC includes the envelope and `payload`; vectors were regenerated. `command_payload_tamper_invalidates_command_signature`, `command_without_payload_is_malformed`, `command_envelope_tamper_invalidates_command_signature`, and `lease_envelope_tamper_invalidates_lease_signature_after_command_auth` cover the path. |
| Signed Python request, state, command, revocation, fallback, and audit messages reject unknown future authority fields before signature/audit acceptance. | met | `BaseMessage` uses `extra="forbid"` and nested authority models use strict models. Focused tests cover request, state, lease, nested lease constraints, policy input, and audit import unknown fields. |
| Signed revocation replay is idempotent and does not re-emit fallback side effects, including after command-gate restart. | met | `RevocationStore` tracks unique `revocation_id` values in durable SQLite before authority mutation; duplicate accepted revocations produce `REVOCATION_REPLAYED` and no fallback. `test_replayed_signed_revocation_after_restart_does_not_reemit_fallback` covers restart replay. |
| Rust verifier binds lease policy provenance to the signed lease and accepted trusted policy reference. | met | Rust lease claims require signed `policy_id` and `policy_digest`, and `policy_digest_violation()` compares them with `TrustedVerifierContext` accepted policy state. `signed_lease_policy_digest_mismatch_is_rejected` covers a signed mismatch. |
| Assembly ledger no longer records live Lambda identifiers or cloud-specific deployment IDs. | met | T7 live evidence was redacted to operator-managed generic labels; targeted search found no `real2sim-b1`, `rclp-t7-isaac`, `real2sim-isaac`, `gpu_1x_a10`, or `us-east-1` strings under `docs/`, `tests/`, `src/`, `crates/`, or `manifests/`. |
| Rust command-auth failure audits are diagnostic/non-authority and do not trust unauthenticated command subject fields. | met | All verifier denials before command authentication now route through `deny_untrusted_command()`, producing diagnostic/non-authority audit events with claimed subject values only in payload. `authenticated_command_actor_mismatch_is_rejected_before_lease_checks` and `pre_command_auth_policy_failure_is_diagnostic_non_authority` cover direct and mixed pre-auth failures. |
| Audit JSONL import rejects appended unknown context outside the integrity proof. | met | `AuditCommit` inherits strict `BaseMessage` parsing; `test_load_jsonl_rejects_unknown_context_outside_integrity_proof` proves appended top-level context is rejected. |
| Security-relevant tests cover every changed behavior and legitimate behavior remains covered. | met | Passed: `.venv/bin/python -m compileall src tests`; `.venv/bin/python -m pytest` (174 passed); `.venv/bin/python tests/evals/eval_runner.py` (33 passed, 0 failed); `cargo test --workspace` (25 Rust vector tests plus unit tests); `cargo clippy --workspace --all-targets -- -D warnings`; `cargo fmt --all -- --check`; `.venv/bin/ruff check .`; `.venv/bin/ruff format . --check`. |
| Assembly spec-conformance review is clean and post-review validation gates pass. | met | Reviewer `019ef636-ee95-72f3-afaf-a3abd7bb1cf7` initially found the Rust pre-command-auth audit gap and stale ledger status; the Rust gap was fixed, the reviewer rechecked it cleanly, and post-fix gates passed: `cargo test --workspace`, `cargo clippy --workspace --all-targets -- -D warnings`, `cargo fmt --all -- --check`, `.venv/bin/python -m pytest tests/test_rust_edge_vectors.py tests/test_audit.py tests/test_security_negative_paths.py`, and `.venv/bin/ruff check .`. |

Review notes:

- Reviewer `019ef636-ee95-72f3-afaf-a3abd7bb1cf7` ("Halley") found one
  valid P1 issue: Rust pre-command-auth denials for earlier lease/policy
  failures could still emit authority-relevant audit records with claimed
  command subjects. The fix routes every pre-command-auth typed denial through
  diagnostic/non-authority audit construction and adds focused Rust regressions.
- The same review noted this ledger entry was not yet closed; this entry is
  now closed after code fix, clean re-review, and post-review validation.
- Final re-review status: clean for the Rust pre-command-auth audit issue. The
  reviewer confirmed pre-command-auth typed denials now route through
  diagnostic/non-authority audit construction, and that the focused Rust
  regressions cover the mixed pre-auth failure path.

## Post-Scan 5-Finding Security Remediation - 2026-06-23

Status: successful

Source contract:

- User request: resolve all five Codex Security findings using `assembly`.
- Completed Codex Security scan `7539de62-1d6d-4a01-9b30-426f39d6717c`.
- Scan report:
  `local Codex Security report artifact redacted`
- `AGENTS.md`
- Required repo doctrine under `docs/`
- `docs/PROTOCOL_SPEC_DRAFT.md`
- `docs/THREAT_MODEL.md`
- `docs/TEST_STRATEGY.md`

Preflight note:

- No cloud jobs or paid compute are required for this remediation, and none
  will be launched, stopped, resized, deleted, or otherwise mutated.

Target contract:

Close the five validated findings at their root authority contracts:
revocation state must survive command-gate restart, unauthenticated command
denials must not trigger fallback side effects, leases must fail closed on
unsupported protocol versions, Rust audit identities must not collide across
distinct decisions, and malformed pre-parse Rust audit records must not be
authority-relevant events without authority context.

Success criterion:

The reproduced attack paths deny safely after restart or malformed input, do
not emit attacker-triggered fallback declarations, produce unique audit event
IDs, reject unsupported lease protocol versions, and pass focused regressions,
repo gates, and spec-conformance review.

Definition of done:

| Item | Status | Evidence |
|---|---|---|
| RCLP-REVOCATION-DURABLE-001: Python command-gate revocation enforcement uses an explicit durable/shared store and fails closed without one. | met | `RevocationStore` is SQLite-backed, `CommandGate` requires a durable injected store, accepted revocations are persisted before in-memory mutation, and `test_revoked_lease_is_rejected_after_gate_restart` proves a recreated gate with the same store rejects the original restart PoC. |
| RCLP-AUTH-FAIL-NO-FALLBACK-001: Unauthenticated or command-authentication denials do not emit `FallbackDeclaration` side effects. | met | Command-authentication failures call `_reject_command(..., emit_fallback=False)`, return no fallback action/declaration, do not call the fallback sink, and now record diagnostic/non-authority audit events using local actor identity. `test_command_auth_denials_do_not_emit_fallback_side_effects` covers missing actor, missing signature, invalid signature, and untrusted key. |
| RCLP-LEASE-VERSION-001: Capability leases carry and enforce the supported protocol version so unsupported/future raw leases cannot authorize commands. | met | `CapabilityLease` requires the common envelope (`protocol_version`, `message_id`, `correlation_id`, `created_at`, `message_type`) at parse time, forbids unknown top-level fields, and `LeaseConstraints` forbids unknown nested authority fields. Focused tests cover unsupported lease versions, missing common envelope fields, top-level future fields, and nested future constraint fields. |
| RCLP-RUST-AUDIT-ID-001: Rust verifier audit events have unique identities across distinct authority decisions, even under identical trusted timestamps and malformed input. | met | Rust `AuditEvent` identity now binds `event_sequence`, `identity_nonce`, and payload hash into `audit_id`, `message_id`, and `integrity_proof`; `malformed_json_audit_events_have_unique_identities` proves repeated malformed decisions do not collide. |
| RCLP-RUST-MALFORMED-AUDIT-001: Rust malformed pre-parse audit events are diagnostic/non-authority unless authority context is available. | met | Rust `AuditSubject` carries `authority_relevant`; malformed pre-parse decisions emit `event_type=diagnostic`, `authority_relevant=false`, and no lease/command context, while parsed authority decisions remain authority-relevant. |
| Security-relevant tests cover every changed behavior and legitimate behavior remains covered. | met | Added Python regressions for durable revocation restart, durable store constructor failure, strict lease protocol parsing, nested lease constraint future fields, and no fallback/auth diagnostic behavior; added Rust vector regressions for audit uniqueness and malformed diagnostic classification. |
| Validation gates pass. | met | Passed after review fixes: `.venv/bin/python -m compileall src tests`; `.venv/bin/python -m pytest` (162 passed); `.venv/bin/python tests/evals/eval_runner.py` (33 passed, 0 failed); `cargo test --workspace`; `cargo clippy --workspace --all-targets -- -D warnings`; `cargo fmt --all -- --check`; `.venv/bin/ruff check .`; `.venv/bin/ruff format . --check`. |
| Assembly spec-conformance review is clean and post-review gates pass. | met | Initial subagent reviewer `019ef5ba-16ac-70e1-99d5-99345217b51c` found strict lease parsing, unauthenticated audit provenance, and stale ledger findings; first re-review found the remaining missing `message_type` envelope gap. All valid findings were fixed, post-review gates passed, and final re-review returned clean with every DoD item met. |

Review notes:

- Reviewer: `019ef5ba-16ac-70e1-99d5-99345217b51c` ("Parfit").
- Initial review status: three valid findings. P1 strict lease parsing and P2
  unauthenticated audit provenance were fixed in code and tests; P3 stale
  ledger evidence was updated in this entry.
- First re-review status: one remaining valid finding for missing
  `message_type` acceptance on raw leases. The fix was expanded to require the
  full common `CapabilityLease` envelope at parse time, with focused tests.
- Final re-review status: clean. The reviewer classified all DoD items as met
  and made no code or cloud changes.
- No cloud jobs or paid compute were required or mutated.

## Post-Scan 4-Finding Security Remediation - 2026-06-23T2

Status: successful

Source contract:

- User request: resolve all four Codex Security findings using `assembly`.
- Completed fresh Codex Security scan `0aab2b4e-d69b-4eb4-830f-edcde6bbf656`.
- Scan report:
  `local Codex Security report artifact redacted`
- `AGENTS.md`
- Required repo doctrine under `docs/`
- `docs/PROTOCOL_SPEC_DRAFT.md`
- `docs/THREAT_MODEL.md`
- `docs/TEST_STRATEGY.md`

Preflight note:

- `DIRECTION.md` is intentionally removed from the current worktree by prior
  user request. The current `AGENTS.md` no longer lists it as required reading.
- No cloud jobs or paid compute are required for this remediation, and none
  will be launched, stopped, resized, deleted, or otherwise mutated.

Target contract:

Close the four validated scan findings at their root authority contracts:
command replay state must be durable/shared rather than process-local, every
accepted Python capability must have an explicit constraint requirement profile,
Rust trusted verifier secrets must not leak through debug or serialization, and
Rust verifier audit events must be chained to a caller-provided audit head.

Success criterion:

The Python command gate rejects the original restart replay PoC, accepted
non-remote capabilities fail closed without their declared constraints, Rust
debug/JSON output redacts HMAC secrets, Rust audit events bind a non-empty prior
audit chain head, focused regressions pass, and the required local gates pass.

Definition of done:

| Item | Status | Evidence |
|---|---|---|
| RCLP-CMD-REPLAY-DURABLE-001: Python command replay protection uses an explicit durable/shared store for command id and nonce replay, and `CommandGate` fails closed without one. | met | `CommandReplayCache` now supports SQLite-backed atomic command-id and nonce inserts, `CommandGate` requires a durable injected cache, and `test_replayed_signed_command_is_rejected_after_gate_restart` proves a recreated gate with the same store rejects the original replay PoC. |
| RCLP-PY-CAP-CONSTRAINT-001: Python lease validation enforces typed per-capability required constraints for every accepted capability, not only `remote_assist`. | met | `CapabilityConstraintRequirement` now defines the Python profile, `CommandGate` requires every accepted capability to have a requirement, and tests cover non-remote empty-constraint denial, legitimate constrained `mission_continue` allow, and explicit fallback-field enforcement. |
| RCLP-RUST-SECRET-REDACT-001: Rust `TrustedVerifierContext` does not print or serialize HMAC secrets by default. | met | Rust `TrustedVerifierContext` now uses custom redacted `Debug` and `skip_serializing` on HMAC secrets; `trusted_verifier_context_redacts_hmac_secrets` verifies debug output and JSON serialization do not expose the secrets. |
| RCLP-RUST-AUDIT-ANCHOR-001: Rust verifier audit events bind a caller-provided previous audit hash / chain head instead of always emitting `previous_audit_hash: None`. | met | Rust trusted context now requires `audit_chain_head`, serde rejects malformed chain heads, `verify_json_value()` preflights the chain head before parse-error audits, and vector tests prove non-empty previous hash binding plus proof sensitivity to chain-head tampering. |
| Security-relevant tests cover every changed behavior and legitimate behavior remains covered. | met | Added Python regressions for durable command replay, non-remote constraints, and explicit fallback requirements; added Rust regressions for secret redaction, malformed audit-chain context, malformed JSON audit binding, and previous-hash proof tamper sensitivity. |
| Validation gates pass. | met | Passed: `.venv/bin/python -m compileall src tests`; `.venv/bin/python -m pytest` (147 passed); `.venv/bin/python tests/evals/eval_runner.py` (33 passed, 0 failed); `cargo test --workspace`; `cargo test -p rclp-edge-verifier --test vector_tests` (17 passed); `cargo fmt --all -- --check`; `cargo clippy --workspace --all-targets -- -D warnings`; `.venv/bin/ruff check .`; `.venv/bin/ruff format . --check`. |
| Assembly spec-conformance review is clean and post-review gates pass. | met | Subagent reviewer `019ef587-c2ab-7562-8cd7-5d24fb55c773` first found fallback explicitness and malformed-input audit-chain gaps; both were fixed, focused and broad gates reran, and re-review returned clean with all DoD items met. |

Review notes:

- Reviewer: `019ef587-c2ab-7562-8cd7-5d24fb55c773` ("Descartes").
- Initial review status: two valid code findings and one ledger update item.
- Final review status: clean. The reviewer classified all remediation DoD
  items as met and made no code or cloud changes.
- No cloud jobs or paid compute were required or mutated.

## Post-Scan 6-Finding Security Remediation - 2026-06-23

Status: successful

Source contract:

- User request: resolve all six Codex Security findings using `assembly`.
- Completed Codex Security scan `c3c5a16a-9f5b-4d0e-9805-99314da56f24`.
- Scan report:
  `local Codex Security report artifact redacted`
- `AGENTS.md`
- Required repo doctrine under `docs/`
- `docs/PROTOCOL_SPEC_DRAFT.md`
- `docs/THREAT_MODEL.md`
- `docs/TEST_STRATEGY.md`

Preflight note:

- `DIRECTION.md` is listed as required reading in `AGENTS.md`, but it is
  currently removed from the worktree by prior user request. The remaining
  required doctrine files were read before implementation.
- No cloud jobs or paid compute are required for this remediation, and none
  will be launched, stopped, resized, deleted, or otherwise mutated.

Target contract:

Close the six validated scan findings at their root authority contracts:
audit import authenticity, per-capability constraint schemas, Rust audit proof
field binding, durable request replay storage, command authentication before
authority audit, and Rust policy digest pinning.

Success criterion:

The Python reference implementation and Rust edge verifier reject all six
reproduced attack paths with focused negative tests, preserve legitimate
behavior, and pass local validation gates.

Definition of done:

| Item | Status | Evidence |
|---|---|---|
| RCLP-AUDIT-AUTH-001: Python audit JSONL import rejects authority events whose integrity profile is only locally recomputable unless a trusted anchor validates the chain. | met | `load_jsonl()` now requires a matching `trusted_chain_head` when authority events are imported. Tests cover anchored positive load, unanchored authority rejection, and recomputed tamper rejection against the original trusted chain head. |
| RCLP-CAP-CONSTRAINT-001: Rust verifier enforces typed per-capability required constraints, so accepted non-`remote_assist` capabilities cannot authorize with empty constraints. | met | `TrustedVerifierContext` now carries `capability_constraint_requirements`, and `required_constraints_missing()` enforces the schema for every accepted capability. Rust regression `accepted_non_remote_capability_requires_declared_constraints` denies a signed accepted `mission_continue` lease with empty constraints. |
| RCLP-RUST-AUDIT-BIND-001: Rust audit `integrity_proof` binds every replay-critical top-level authority field. | met | Rust `AuditEvent` proof payload now includes `decision`, `reason_code`, `lease_id`, `command_id`, and `observed_at_unix_ms`. `authority_decisions_carry_audit_commit_integrity_fields` recomputes the proof and verifies tampering changes the proof. |
| RCLP-REQUEST-REPLAY-DURABLE-001: Python capability request replay protection is durable and atomic for the request freshness window, and policy issuance fails closed without durable replay storage. | met | `RequestReplayCache` now uses durable SQLite-backed atomic insert semantics for policy issuance; `_evaluate_policy_inputs()` consumes a fresh authenticated nonce before policy/state/network/geofence outcomes. Tests cover missing cache, non-durable store denial, replay across recreated cache instances, and authenticated denial followed by replayed allow attempt. |
| RCLP-EDGE-PREAUTH-AUDIT-001: Edge daemon does not write authority-relevant command audit events before command authentication succeeds or fails through the command gate. | met | `EdgeAgentDaemon.handle_command()` delegates unauthenticated mismatch commands to `CommandGate.evaluate()`. Negative test verifies an unsigned mismatched command produces `COMMAND_AUTHENTICATED_AGENT_MISSING`, not a pre-auth `EDGE_AGENT_MISMATCH` authority audit. |
| RCLP-RUST-POLICY-DIGEST-001: Rust verifier authorization is pinned to an accepted policy id/digest and emitted audit events carry that policy reference. | met | Rust `TrustedVerifierContext` now uses accepted `{policy_id, policy_digest}` references. `policy_digest_violation()` requires the pair before authorization, audit events include both fields, and regressions cover downgraded digest plus accepted digest with mismatched policy id. |
| Security-relevant tests cover every changed behavior and legitimate behavior remains covered. | met | Focused regressions were added in `tests/test_audit.py`, `tests/test_security_negative_paths.py`, `tests/test_rust_edge_vectors.py`, and `crates/rclp-edge-verifier/tests/vector_tests.rs`; shared Rust vectors were migrated to the policy-reference and constraint-schema contract. |
| Validation gates pass. | met | Final gates passed: `.venv/bin/python -m compileall src tests`; `.venv/bin/python -m pytest` (142 passed); `PYTHONPATH=src .venv/bin/python tests/evals/eval_runner.py` (33 passed, 0 failed); `cargo test --workspace` (1 lib test and 14 vector tests); `cargo clippy --workspace --all-targets -- -D warnings`; `.venv/bin/ruff check .`; `.venv/bin/ruff format . --check`; `cargo fmt --all -- --check`. |
| Assembly spec-conformance review is clean and post-review gates pass. | met | Subagent reviewer Feynman first found authenticated-deny replay consumption and Rust policy id/digest pair gaps; both were fixed and re-reviewed cleanly with no remaining code findings. Post-review full gates reran successfully. |

Review notes:

- Reviewer: `019ef560-853f-7702-a659-881898bc5819` ("Feynman").
- Initial review status: two valid code findings and one ledger update item.
- Post-review status: no remaining code blocker. The reviewer classified all
  six remediation DoD items as met and noted ledger closure was the remaining
  administrative step.
- No cloud jobs or paid compute were required or mutated.

## Post-Scan 4-Finding Security Remediation - 2026-06-23

Status: successful

Source contract:
- Codex Security scan `eb7bed48-4cd6-41db-b868-66d4fa26f023` report at `local Codex Security report artifact redacted`.
- AGENTS-required doctrine read before edits. `DIRECTION.md` is intentionally deleted in the working tree per user request; historical `HEAD:DIRECTION.md` was used as non-authoritative context only.
- No cloud job mutation authorized or performed.

Definition of done:

| ID | Requirement | Status | Evidence |
| --- | --- | --- | --- |
| RCLP-CG-SCOPE-001 | Python `CommandGate` / `validate_lease_for_command` enforce edge-local accepted capabilities and issuer capability scopes; trusted issuers cannot sign capabilities outside local scope. | met | `CommandGate` now requires `accepted_capabilities` and `issuer_capability_scopes`, and `validate_lease_for_command()` rejects locally unsupported or issuer-unscoped capabilities with `CAPABILITY_NOT_GRANTED`. Negative coverage includes trusted issuer `autonomy_escalation` denial. |
| RCLP-CG-CMD-AUTH-001 | Python commands crossing the edge/ROS gate require authenticated actor identity, signature verification, freshness, and replay protection before lease validation can allow. | met | `EdgeCommand` is a signed `BaseMessage`; `CommandGate.evaluate()` checks authenticated actor, trusted command key, signature, freshness, and command id/nonce replay before lease validation. Negative coverage covers missing auth actor, missing signature, actor mismatch, untrusted key, invalid signature, stale/future command, and replay. |
| RCLP-RUST-CMD-ACTOR-001 | Rust verifier treats command actor as authenticated envelope state, rejects authenticated actor mismatch, and does not authorize using a spoofable claimed agent field. | met | Rust `EdgeCommand` now carries authenticated actor, command nonce/time, and signature; `TrustedVerifierContext` carries command-agent trust roots and command HMAC secret. Vectors cover missing auth actor, actor mismatch, untrusted agent, invalid/missing signature, stale/future command, and signed command replay. |
| RCLP-RUST-AUDIT-001 | Rust verifier authority decisions carry AuditCommit-equivalent integrity fields including payload hash and integrity proof. | met | Rust `AuditEvent` now emits `audit_commit` envelope fields, `created_at`, `payload_hash`, `integrity_profile`, `integrity_proof`, policy reference slots, state refs, and related IDs. Rust tests recompute payload hash and integrity proof and verify top-level tamper changes the proof. |
| RCLP-TESTS-001 | Changed behavior has focused negative tests / vectors; Python and Rust fixtures are updated. | met | Python negative tests and Rust shared vectors updated; `EdgeCommand` added to protocol docs and manifest. |
| RCLP-GATES-001 | Focused smoke plus required local gates pass where feasible. | met | Passed: `.venv/bin/python -m compileall src tests`; `.venv/bin/python -m pytest` (136 passed); `.venv/bin/python tests/evals/eval_runner.py` (33 passed); `cargo fmt --all -- --check`; `cargo clippy --workspace --all-targets -- -D warnings`; `cargo test --workspace`; `.venv/bin/ruff check .`; `.venv/bin/ruff format --check .`. |
| RCLP-REVIEW-001 | Spec-conformance review is performed and post-review smoke reruns cleanly. | met | Subagent spec review found audit-proof, command-auth coverage, and `edge_command` protocol-surface gaps; all were resolved, rechecked cleanly, and the full verification gates reran successfully. |

## Post-Scan 3-Finding Security Remediation - 2026-06-23

Status: successful

Source contract:

- User request: resolve the three Codex Security findings using `assembly`.
- Completed Codex Security scan `1a82e261-a7ff-4db1-868e-bae9c5a42599`.
- Scan report:
  `local Codex Security report artifact redacted`
- `AGENTS.md`
- Required repo doctrine under `docs/`
- `docs/PROTOCOL_SPEC_DRAFT.md`
- `docs/THREAT_MODEL.md`
- `docs/TEST_STRATEGY.md`

Preflight note:

- No cloud jobs or paid compute are required for this remediation, and none
  will be launched, stopped, resized, deleted, or otherwise mutated.

Target contract:

Close the three validated findings at their root authority contracts:
Rust verifier capability authorization must be explicit and local, Rust replay
nonce consumption must be atomic from the verifier contract's perspective, and
signed revocations must be scoped to the referenced lease edge context unless
an explicit broader role exists.

Success criterion:

The Rust edge verifier rejects HMAC-valid unsupported capabilities and consumes
lease nonces through a single atomic operation; the Python command gate rejects
cross-edge revocations from otherwise trusted revokers; focused negative tests
and local validation gates pass.

Definition of done:

| Item | Status | Evidence |
|---|---|---|
| RCLP-RUST-EDGE-001: Rust verifier enforces explicit local accepted capability and issuer-to-capability scope before allow/degrade. | met | `TrustedVerifierContext` now carries `accepted_capabilities` and `issuer_capability_scopes`; `verify()` rejects signed capabilities that are not locally accepted or issuer-scoped with `DENY_CAPABILITY_NOT_GRANTED`. Rust regressions cover an HMAC-valid unsupported capability and issuer scope mismatch. Shared vectors and Python vector-shape tests include the new trusted context contract. |
| RCLP-RUST-EDGE-002: Rust replay cache contract exposes atomic nonce consumption and no verifier path uses split check/mark. | met | `ReplayCache` now exposes only `consume_nonce()`, and `verify()` consumes the nonce immediately before `allow` or `degrade`. The public `InMemoryReplayCache` export was removed so the crate does not present process-local replay storage as a production default. Rust regressions cover same-cache replay rejection after both allow and degrade. |
| RCLP-CG-REVOCATION-CTX-001: revocation signer authority is bound to the referenced lease edge context or an explicit scope. | met | `LeaseRevocation` now requires `edge_agent_id`. `CommandGate` verifies signed revocations, requires revocation edge context to match the lease, rejects cross-edge revokers by default, and permits broader revokers only through explicit `revoker_edge_scopes_by_id`. Python tests cover cross-edge denial, explicit scoped revoker allow, and revocation edge mismatch denial. |
| Security-relevant tests cover every changed behavior. | met | Added Rust vector tests for unsupported signed capability, issuer-capability scope mismatch, allow replay consumption, and degrade replay consumption. Added Python negative/positive revocation tests for cross-edge revoker denial, explicit scoped revoker allow, and revocation edge context mismatch. |
| Validation gates pass. | met | Focused smoke passed: `cargo test -p rclp-edge-verifier --test vector_tests` (8 passed) and `.venv/bin/python -m pytest tests/test_security_negative_paths.py tests/test_protocol_flow.py tests/test_rust_edge_vectors.py tests/test_conformance_contract.py` (111 passed). Broader gates passed: `.venv/bin/python -m compileall src tests`; `.venv/bin/python -m pytest` (127 passed); `PYTHONPATH=src .venv/bin/python tests/evals/eval_runner.py` (33 passed, 0 failed); `cargo test --workspace`; `cargo fmt --all -- --check`; `cargo clippy --workspace --all-targets -- -D warnings`; `.venv/bin/ruff check .`; `.venv/bin/ruff format . --check`. |
| Assembly spec-conformance review is clean and post-review gates pass. | met | Subagent review classified code-level remediation as sound and found only ledger/docs parity nits. Those docs were updated, and post-review gates were rerun successfully. |

Cloud/job status:

- No cloud jobs or paid compute are required for this remediation.
- Repository cloud mutation rule reviewed; no launch, stop, delete, resize, or
  other paid-compute mutation will be performed.

Review notes:

- Subagent reviewer: `019ef25b-c45e-7322-bf27-ff39aa71d782` ("Franklin").
- Initial review status: no code-level security blocker; docs/ledger parity
  updates requested for this section, `docs/THREAT_MODEL.md`, and
  `docs/CONFORMANCE_CHECKLIST.md`.
- Post-review action: updated ledger evidence and clarified revocation edge
  scoping and advisory fallback wording in summary docs.

## Post-Scan 10-Finding Security Remediation - 2026-06-23

Status: successful

Source contract:

- User request: fix all 10 Codex Security findings using `assembly`.
- Completed Codex Security scan `2b19d816-a775-4733-9e1f-6319bc54e547`.
- Scan report:
  `local Codex Security report artifact redacted`
- `AGENTS.md`
- Required repo doctrine under `docs/`
- `docs/PROTOCOL_SPEC_DRAFT.md`
- `docs/THREAT_MODEL.md`
- `docs/TEST_STRATEGY.md`

Preflight note:

- `DIRECTION.md` is listed as required reading in `AGENTS.md`, but it is
  currently removed from the worktree by prior user request. The remaining
  required doctrine files were read before implementation.
- No cloud jobs or paid compute are required for this remediation, and none
  will be launched, stopped, resized, deleted, or otherwise mutated.

Target contract:

Close the 10 scan findings at their root authority/control-plane contracts:
finite signed numerics, supported protocol versions, Rust freshness overflow,
fallback policy selection, explicit state-key trust, fail-closed lease
timestamps, strict signature encoding, manifest/model requiredness parity, and
single-principal scoping for the Rust dev HMAC profile.

Success criterion:

The Python reference implementation, ROS-adjacent command gate, manifest
conformance tests, eval scenarios, and Rust verifier reject all 10 reproduced
attack paths with focused negative tests and local validation gates.

Definition of done:

| Item | Status | Evidence |
|---|---|---|
| CS-RCLP-001: malformed signature encodings are rejected before Ed25519 verification. | met | `rclp_core.crypto.unb64()` now uses strict validating URL-safe base64 and canonical re-encoding. Negative tests cover malformed request and lease signatures returning `REQUEST_SIGNATURE_INVALID` / `INVALID_SIGNATURE`. |
| CS-RCLP-002: all authority-critical numeric fields reject non-finite values before policy or command comparisons. | met | Pydantic fields now set `allow_inf_nan=False`; policy and command conformance add runtime finite checks for copied/signed objects. Negative tests cover model rejection, signed non-finite network state, and non-finite lease constraints. |
| CS-RCLP-003: malformed or naive lease timestamps fail closed with auditable denial/fallback instead of exceptions. | met | `lease_time_violation()` centralizes timezone/window/age/TTL checks before datetime arithmetic. Negative coverage verifies naive lease timestamps return `LEASE_TIMESTAMP_INVALID` with local fallback instead of crashing. |
| CS-RCLP-004: unsupported `protocol_version` values are rejected before signed authority semantics are interpreted. | met | `SUPPORTED_PROTOCOL_VERSION` and runtime `protocol_version_violation()` are enforced at the start of policy evaluation and in revocation handling before mutation. Post-review tests cover unsupported request/state versions even with semantic conflicts, plus unsupported revocation versions. |
| CS-RCLP-006: expired, stale, revoked, malformed, or otherwise invalid leases cannot select command-gate fallback actions. | met | `CommandGate` now selects fallback from local reason-code policy, not lease constraints. Negative coverage verifies expired leases with attacker-chosen lease fallback still emit `LOCAL_AUTONOMY_ONLY`. |
| CS-RCLP-007: revocation `fallback_action` is advisory and local fallback policy selects the emitted fallback. | met | Revocation audit payload preserves `requested_fallback_action`, while emitted fallback is selected by local policy. Negative coverage verifies a `HOLD_POSITION` revocation request cannot force fallback for an unrecognized local reason. |
| CS-RCLP-008: command-gate state signing keys are explicit and cannot silently alias to revocation keys. | met | `CommandGate` no longer defaults `state_public_keys_by_edge_id` from revoker keys; callers/tests pass state keys explicitly. Negative coverage verifies revoker-only keys produce `EDGE_STATE_KEY_NOT_TRUSTED`. |
| CS-RCLP-009: Rust state freshness arithmetic overflow fails closed. | met | Rust state freshness arithmetic now returns `DENY_MALFORMED_INPUT` on checked-add overflow. Rust regression `overflowing_state_freshness_window_fails_closed` covers the overflow case. |
| CS-RCLP-010: Rust dev HMAC profile cannot silently authorize multiple issuers or state-edge principals with one shared secret. | met | The dev HMAC verifier now rejects trust contexts with more than one issuer or state edge id. Rust regression `dev_hmac_profile_rejects_multi_principal_trust_sets` covers both sets. |
| CS-RCLP-011: manifest-required trust-boundary fields match model requiredness or an explicit runtime-required contract enforced by tests. | met | `manifests/rclp_protocol_manifest.yaml` now declares `runtime_required_fields`; conformance tests require every manifest required field to be either model-required or explicitly runtime-required. |
| Security-relevant tests cover every changed behavior. | met | Added Python negative tests for the scan findings in `tests/test_security_negative_paths.py`, conformance manifest checks in `tests/test_conformance_contract.py`, and Rust verifier regressions in `crates/rclp-edge-verifier/tests/vector_tests.rs`. |
| Validation gates pass. | met | Final local gates passed: compileall, full pytest, eval runner, Ruff check/format check, Cargo fmt check, Cargo clippy, and Cargo test. |
| Assembly spec-conformance review is clean and post-review gates pass. | met | Subagent reviewer `019ef21e-d9ce-76a2-b054-a1165fbee052` first found a CS-RCLP-004 ordering blocker; after the fix, targeted re-review reported no remaining blocker and confirmed unsupported request/state/revocation versions fail before semantic handling or mutation. |

Review status:

- Clean after post-review fix. Independent reviewer Popper confirmed the
  CS-RCLP-004 ordering blocker is closed, probed the prior semantic-conflict
  cases, and reported no remaining blocker.

Evidence:

- `.venv/bin/python -m pytest tests/test_security_negative_paths.py tests/test_protocol_flow.py tests/test_conformance_contract.py` passed: 106 tests.
- `.venv/bin/python -m compileall src tests` passed.
- `.venv/bin/python tests/evals/eval_runner.py` passed: 33 evals passed, 0 failed.
- `.venv/bin/python -m pytest` passed: 124 tests.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format . --check` passed.
- `cargo test -p rclp-edge-verifier` passed: 1 library test, 5 vector tests, 0 doc tests.
- `cargo fmt --all -- --check` passed.
- `cargo clippy --workspace --all-targets -- -D warnings` passed.

## Post-Scan Security Finding Remediation - 2026-06-23

Status: successful

Source contract:

- User request: fix the four Codex Security findings using `assembly`.
- Completed Codex Security scan `e02479b0-82f5-4d68-9748-e2bfc4efa38b`.
- `AGENTS.md`
- Required repo doctrine under `docs/`
- `docs/PROTOCOL_SPEC_DRAFT.md`
- `docs/THREAT_MODEL.md`
- `docs/TEST_STRATEGY.md`

Preflight note:

- `DIRECTION.md` is listed as required reading in `AGENTS.md`, but it is
  currently removed from the worktree by prior user request. The remaining
  required doctrine files were read before implementation.
- No cloud jobs or paid compute are required for this remediation, and none
  will be launched, stopped, resized, deleted, or otherwise mutated.

Target contract:

Close the four post-scan security findings at their root control-plane
contracts: authenticated Rust local state, issuer-id-to-key binding, authenticated
revocation fallback binding, and audited fail-closed malformed request
timestamps.

Success criterion:

The Python reference command gate and policy path, plus the Rust verifier spike,
reject the four reproduced attack paths with focused negative tests and local
validation gates.

Definition of done:

| Item | Status | Evidence |
|---|---|---|
| Rust verifier authenticates local network/geofence state before using it for authority. | met | `LocalContext` now carries `authenticated_edge_agent_id`, local state timestamps, and a dev-profile state signature. `TrustedVerifierContext` now carries trusted state edge ids and a state HMAC secret. The verifier rejects missing/mismatched/untrusted/unsigned/invalid state before geofence or network policy checks. Shared vectors were regenerated with signed local state, and `unsigned_local_state_rejected.json` plus the Rust mutation regression prove unsigned or forged local state cannot authorize a command. |
| Lease issuer identity is bound to the public key used for verification. | met | `validate_lease_for_command()` now builds an issuer-key registry and verifies a lease only with the key mapped to `lease.issuer_id`; multi-issuer `CommandGate` construction requires an explicit issuer-key registry. Negative coverage includes a trusted low-privilege key signing a lease claiming a different trusted issuer and receiving `INVALID_SIGNATURE`. |
| Revocation fallback is selected only for an authenticated, context-bound revoked lease. | met | Revoked-lease id handling now occurs after signature, lease time, required constraints, and command-context checks. Stored revocation records include the authenticated lease authority tuple, and fallback declarations only use revocation fallback/correlation/revocation ids when the current authenticated lease and command context match that tuple. Negative coverage proves a fake unsigned/context-shifted lease reusing a revoked id gets `INVALID_SIGNATURE` and `LOCAL_AUTONOMY_ONLY` with no revocation id. |
| Naive `CapabilityRequest.created_at` is rejected as an audited denial, not an exception. | met | `_request_time_violation()` rejects naive request timestamps as `REQUEST_TIMESTAMP_INVALID` before datetime comparison. Negative coverage verifies policy evaluation returns `Decision.DENY`, records `capability_denied`, and includes the reason in the audit payload. |
| Security-relevant tests cover every changed behavior. | met | Added focused Python negative tests for naive request timestamps, forged revoked-id fallback, issuer/key mismatch, and multi-issuer key-registry enforcement. Rust vectors and tests cover signed local state, unsigned local state, forged local context mutation, and replay. Python vector shape tests assert the new state trust-root and signature contract. |
| Validation gates pass. | met | Full gates passed after formatting: compileall, full pytest, eval runner, Ruff check, Ruff format check, Cargo fmt check, Cargo clippy, and Cargo test. |
| Assembly spec-conformance review is clean and post-review gates pass. | met | Subagent reviewer `019ef1ec-d70f-7810-ad45-28bc2334e555` returned no actionable findings and noted only documented production gaps. The review thread was closed, then post-review pytest/Rust/eval smoke passed. |

Review status:

- Clean. Subagent reviewer Maxwell reviewed the four finding contracts,
  changed files, extracted DoD, and evidence in read-only mode. The reviewer
  reported no actionable findings and confirmed the four contracts appear
  covered. Residual risks are intentionally out of scope and documented: the
  Rust spike still uses the test-only HMAC profile and consumes a local
  revocation set rather than verifying revocation messages itself.

Evidence:

- `.venv/bin/python -m pytest tests/test_security_negative_paths.py tests/test_protocol_flow.py tests/test_rust_edge_vectors.py` passed: 89 tests.
- `cargo test -p rclp-edge-verifier --test vector_tests` passed: 3 tests.
- `.venv/bin/python -m compileall src tests` passed.
- `.venv/bin/python -m pytest` passed: 110 tests.
- `PYTHONPATH=src .venv/bin/python tests/evals/eval_runner.py` passed: 33
  evals passed, 0 failed.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format . --check` passed after formatting one touched Python
  test file.
- `cargo fmt --all -- --check` passed after formatting touched Rust files.
- `cargo clippy --workspace --all-targets -- -D warnings` passed.
- `cargo test --workspace` passed: 1 library test, 3 vector tests, 0 doc
  tests.
- Post-review smoke passed:
  `.venv/bin/python -m pytest tests/test_security_negative_paths.py tests/test_rust_edge_vectors.py`
  with 47 tests passed.
- Post-review smoke passed:
  `cargo test -p rclp-edge-verifier --test vector_tests` with 3 tests passed.
- Post-review smoke passed:
  `PYTHONPATH=src .venv/bin/python tests/evals/eval_runner.py` with 33 evals
  passed, 0 failed.

Artifacts:

- Python issuer-key and state/fallback policy contracts:
  `src/rclp_core/conformance.py`, `src/rclp_core/policy.py`, and
  `src/rclp_ros2/command_gate.py`.
- Python regression tests: `tests/test_security_negative_paths.py`.
- Rust local-state authentication: `crates/rclp-edge-verifier/src/types.rs`,
  `crates/rclp-edge-verifier/src/crypto.rs`, and
  `crates/rclp-edge-verifier/src/verifier.rs`.
- Rust/vector regressions:
  `crates/rclp-edge-verifier/tests/vector_tests.rs`,
  `tests/test_rust_edge_vectors.py`, and
  `tests/vectors/edge_verifier/`.
- Documentation:
  `docs/RUST_EDGE_VERIFIER.md`,
  `tests/vectors/edge_verifier/README.md`, and
  `crates/rclp-edge-verifier/README.md`.

Cloud/job status:

- No cloud jobs or paid compute were required.
- Repository cloud mutation rule reviewed; no launch, stop, delete, resize, or
  other paid-compute mutation was performed.

## Security Review Remediation - 2026-06-22

Status: successful

Source contract:

- User request: resolve all security/code-review findings using `assembly`.
- Human reviewer findings from the RCLP MVP security pass.
- `AGENTS.md`
- Required repo doctrine under `docs/`

Target contract:

Close the security review findings at their protocol/control-plane roots so RCLP
fails closed for stale or unauthenticated state, unsigned revocation, replayed
authority requests, unenforced command constraints, and tampered audit context.

Success criterion:

The Python reference, command gate, eval harness, and Rust verifier all enforce
the same authority contracts; negative tests cover every changed
security-relevant behavior; full local validation gates pass.

Definition of done:

| Item | Status | Evidence |
|---|---|---|
| Edge command validation fails closed when required local state is missing or stale. | met | `validate_lease_for_command()` now requires current state for state-scoped `remote_assist` leases, authenticates signed edge-local state, and rejects stale state. Negative coverage includes missing, unsigned, and stale current-state command-gate cases in `tests/test_security_negative_paths.py` and eval scenarios `missing_current_state_denied`, `unsigned_current_state_denied`, and `stale_current_state_denied`. |
| Policy issuance requires authenticated edge-local state and bounded freshness. | met | `RobotStateAssertion` now carries `authenticated_edge_agent_id` and `signature`; policy validation uses trusted edge keys and shared state freshness checks. Negative coverage includes unsigned and stale state policy tests/evals. |
| Policy issuance requires replay protection instead of allowing a no-cache authority path. | met | `_evaluate_policy_inputs()` and `evaluate_policy()` require a `RequestReplayCache` and deny `REQUEST_REPLAY_CACHE_REQUIRED` when absent. Replay-negative tests still cover duplicate nonce denial. |
| Lease revocation acceptance requires a signed trusted revoker, freshness bounds, and matching lease context. | met | `CommandGate.revoke()` now requires a trusted revoker key, valid signature, fresh `created_at`/`revoked_at`, matching lease id, and non-conflicting optional robot/mission/capability context. Negative tests cover unsigned, invalid, stale, unknown, lease-mismatched, and context-conflicting revocations. |
| `max_speed_mps` lease constraints are enforced against command payloads and fail closed on missing or malformed command data. | met | Command payloads are passed into conformance; speed-limited leases reject missing, malformed, non-finite, conflicting-alias, and too-high speed data. Negative tests and evals cover `COMMAND_SPEED_MISSING`, `COMMAND_SPEED_MALFORMED`, `COMMAND_SPEED_CONFLICT`, and `COMMAND_SPEED_TOO_HIGH`. |
| Audit integrity proofs bind replay-critical top-level `AuditCommit` context. | met | Audit proofs now bind common envelope fields, actor/context fields, summary, authority relevance, policy id/digest, state refs, related message ids, payload hash, and previous hash. JSONL import requires common envelope fields. Negative tests cover top-level context tamper and missing common envelope field rejection. |
| Rust verifier parity covers state freshness and speed constraint enforcement. | met | Rust verifier types/checks now include local context timestamps, `max_state_age_ms`, and command `max_speed_mps`; shared vectors include stale local state and over-speed command rejection. Cargo vector tests pass. |
| Security-relevant negative tests and evals cover every changed behavior. | met | `.venv/bin/python -m pytest` passed 106 tests; `PYTHONPATH=src .venv/bin/python tests/evals/eval_runner.py` passed 33/33 scenarios including missing/unsigned/stale state, unsigned revocation, over-speed, conflicting speed alias, and non-finite speed. |
| Validation gates pass. | met | Full gates passed: compileall, pytest, eval runner, Ruff check, Ruff format check, Cargo fmt check, Cargo clippy, and Cargo test. |
| Assembly spec-conformance review is clean and post-review gates pass. | met | Initial subagent review found unsigned current-state, speed alias, audit envelope, revocation context, and stale ledger issues; fixes addressed each. Focused re-review found a remaining NaN speed blocker; fix added finite-speed validation and a non-finite speed eval. Final focused re-review found no concrete blockers. Post-review gates passed. |

Review status:

- First assembly reviewer found five valid issues: command-gate current state
  was not authenticated, conflicting speed aliases could bypass
  `max_speed_mps`, audit import accepted missing common envelope fields,
  revocation context was only lease-id deep, and this ledger was stale.
- Fixes added shared state authentication, command-gate trusted state keys,
  conflicting-speed rejection, common-envelope audit import requirements,
  `message_type` / `policy_digest` audit proof binding, optional revocation
  robot/mission/capability context, and negative tests/evals for each gap.
- Focused re-review found one remaining blocker: non-finite Python speeds
  such as `NaN` could pass comparisons. Fix added an explicit finite check and
  the `nonfinite_speed_denied` eval scenario.
- Final focused re-review returned no concrete blockers and classified D1-D9
  as met, with D10 pending only this ledger update.

Evidence:

- `.venv/bin/python -m compileall src tests` passed.
- `.venv/bin/python -m pytest` passed: 106 tests.
- `PYTHONPATH=src .venv/bin/python tests/evals/eval_runner.py` passed: 33
  evals passed, 0 failed.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format . --check` passed: 23 files already formatted.
- `cargo fmt --all -- --check` passed.
- `cargo clippy --workspace --all-targets -- -D warnings` passed.
- `cargo test --workspace` passed: 1 library test, 2 vector tests, 0 doc
  tests.
- Final reviewer smoke passed:
  `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -p no:cacheprovider tests/test_security_negative_paths.py::test_max_speed_constraint_is_enforced_against_command_payload tests/test_protocol_evals.py::test_eval_runner_executes_required_scenario_set`
  with 7 tests passed.

Cloud/job status:

- No cloud jobs or paid compute are required for this remediation.
- Repository cloud mutation rule reviewed; no launch, stop, delete, resize, or
  other paid-compute mutation will be performed.

## Post-T12 Validation Sequence Plan - 2026-06-22

Status: successful

Source contract:

- User attachment: `Sequence Plan - Post-T12 Validation Sequence`
- User-provided T13 prompt: `T13 - Demo + Validation Release Package`
- User-provided T14 prompt: `T14 - Isaac Sim Visual POC on Lambda.ai`
- User instruction: use `assembly`
- `AGENTS.md`
- `DIRECTION.md` at the time of the Post-T12 sequence work; this file was
  later removed by user request.
- Required repo doctrine under `docs/`

Target contract:

Create a planning/documentation handoff that tells the project owner exactly
what to do after T12, which Codex threads to run next, what must be true before
controlled technical validation calls, and what not to build yet. The work must
not add new protocol features.

Success criterion:

The repo contains a clear post-T12 sequence plan, customer-call readiness gate,
and next-thread map that recommend T13 before broad outreach, T14 as a visual
Isaac Sim POC, controlled calls before public launch, and no commercial
platform work yet.

Definition of done:

| Item | Status | Evidence |
|---|---|---|
| `docs/POST_T12_SEQUENCE_PLAN.md` exists. | met | Created `docs/POST_T12_SEQUENCE_PLAN.md` with current state, proof/non-proof boundaries, recommended sequence, build freeze guidance, customer-call gate, public release gate, and post-call decision criteria. After the fast-forward merge from `origin/main`, the plan now references the present T12 eval artifacts instead of treating them as absent. |
| `docs/CUSTOMER_CALL_READINESS_CHECKLIST.md` exists. | met | Created `docs/CUSTOMER_CALL_READINESS_CHECKLIST.md` with repo hygiene, demo readiness, eval readiness, safety/security caveats, customer-call packet, legal/IP hygiene, open-source posture, and post-call notes sections. |
| `docs/NEXT_THREAD_MAP.md` exists. | met | Created `docs/NEXT_THREAD_MAP.md` with T13, T14, T15, T16, and T17 goals, inputs, non-goals, definitions of done, and timing. The supplied T13/T14 prompts are mapped as thread inputs without executing them. |
| `DIRECTION.md` is updated if appropriate. | met | Appended a concise Post-T12 sequence section to `DIRECTION.md` during the Post-T12 sequence work. The file was later removed by user request, and current live references now point to the replacement sequence docs. |
| The sequence clearly recommends T13 before broad outreach and T14 for visual POC. | met | `docs/POST_T12_SEQUENCE_PLAN.md` recommends T13 before `v0.1-validation` and 5-8 controlled calls, then T14 for the Isaac Sim visual POC; `docs/NEXT_THREAD_MAP.md` says T13 runs before broad outreach and T14 runs after T13 unless explicitly parallelized. |
| The plan distinguishes controlled technical validation calls from public launch. | met | `docs/POST_T12_SEQUENCE_PLAN.md` separates the customer-call gate from the public release gate; `docs/CUSTOMER_CALL_READINESS_CHECKLIST.md` states controlled-call framing is `v0.1-validation`, not public launch. |
| The plan makes clear that no commercial platform work should start yet. | met | `docs/POST_T12_SEQUENCE_PLAN.md` and `docs/NEXT_THREAD_MAP.md` explicitly block hosted commercial platform, customer accounts, billing, carrier/MVNO integration, real QoS integration, and managed SaaS work in this repo. |
| Tests are run and reported where possible. | met | Local gates were run and are recorded below. After fast-forwarding to `origin/main`, `.venv/bin/python tests/evals/eval_runner.py` passed 24/24 evals. |

Review status:

- Subagent spec-conformance review found two valid issues: this ledger still
  recorded the item as `in-progress`, and older ledger entries contained
  absolute local workspace paths that contradicted the new readiness gate.
- The first fix recorded actual evidence, classified every mapped DoD item, and
  removed the old absolute local workspace path references.
- Focused subagent re-review returned no findings and classified the prior P1
  ledger-status issue and P2 local-path issue as resolved.
- Post-review smoke reran `python -m compileall src tests` and
  `.venv/bin/python -m pytest`; both passed.
- After the user authorized the fast-forward merge from `origin/main`, the T12
  eval artifacts were brought into the local checkout and the eval runner was
  rerun successfully under the repo virtualenv.

Evidence:

- Fast-forward merge from `origin/main` succeeded after stashing and reapplying
  local Post-T12 documentation edits.
- `python -m compileall src tests` passed.
- `.venv/bin/python -m pytest` passed: 84 tests before the T12 merge.
- `python tests/evals/eval_runner.py` under the system Python failed because
  that interpreter did not have `PyYAML` installed.
- `.venv/bin/python tests/evals/eval_runner.py` passed after the T12 merge: 24
  evals passed, 0 failed.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format . --check` passed: 20 files already formatted before
  the T12 merge.
- `cargo fmt --all -- --check` passed.
- `cargo clippy --workspace --all-targets -- -D warnings` passed.
- `cargo test --workspace` passed: 1 library test, 2 vector tests, 0 doc tests.
- Content scan found no absolute local-user paths in the changed public
  sequence docs or `README.md`; intended checklist wording about
  named-company/internal references and fallback hooks remains.

Cloud/job status:

- No cloud jobs or paid compute are required for this planning/documentation
  work.
- Repository cloud mutation rule reviewed; no launch, stop, delete, resize, or
  other paid-compute mutation will be performed.

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
| GitHub/release hygiene is checked: `.gitignore`, `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`, workflows, and community-file scope. | met | `.gitignore` now ignores Rust/build/coverage/artifact outputs; `LICENSE` contains full Apache-2.0 text; `CONTRIBUTING.md` includes Python and Rust validation; `SECURITY.md` exists with MVP limitations and controlled-review reporting guidance; `.github/workflows/ci.yml` and `rust.yml` already cover Python/Rust gates; no `CODE_OF_CONDUCT.md` was added. |
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
- `local workspace` is not a Git checkout, so `git status` and `git diff`
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
- `local workspace` is not a Git checkout, so scoped git staging/status could not be performed in this workspace.

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

External Lambda/Isaac evidence, 2026-06-22:

- User requested the proof be run on Isaac Sim in Lambda; an existing
  operator-managed Lambda instance was reused rather than launching new paid
  compute.
- Cloud run evidence was recorded in the local cloud-run ledger under a
  redacted operator-approved run label.
- Runner evidence confirmed a Lambda GPU host with NVIDIA A10 visible through
  `nvidia-smi`; the operator-managed Isaac stream container stayed healthy.
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

## 2026-06-24 Security Scan Remediation: Replay Ordering, Attestation Auth, Rust Audit Classification

Status: successful

Source contract:

- User request: resolve all three Codex Security findings using `assembly`.
- Completed Codex Security scan `98d14d20-a22b-4635-91c1-b33d4e5a48ab`.
- `docs/ENGINEERING_DOCTRINE.md`
- `docs/SECURITY_DOCTRINE.md`
- `docs/DESIGN_TASTE.md`
- `docs/PROTOCOL_SPEC_DRAFT.md`
- `docs/THREAT_MODEL.md`
- `docs/TEST_STRATEGY.md`
- `docs/CONFORMANCE_CHECKLIST.md`

Cloud/job rule:

- No cloud jobs or paid compute are required for this remediation, and none
  are authorized or planned.

Target contract:

Close the three validated scan findings at their root authority contracts:
Python command replay state must not be durably consumed before lease
authorization succeeds; `AgentAttestation` must be able to carry verifiable
authenticated identity and signature material at the protocol contract surface;
and authenticated Rust verifier policy-downgrade command attempts must be
audited as authority-relevant command rejections while malformed/pre-auth
diagnostics remain non-authority.

Definition of done:

| Item | Status | Evidence |
|---|---|---|
| Command replay state mutates only after command authentication and lease/current-state authorization succeed. | met | `CommandReplayCache.contains()` checks replay state without mutation; `CommandGate.evaluate()` calls `remember()` only after `validate_lease_for_command()` succeeds. `test_missing_lease_denial_does_not_consume_command_replay_state` proves a no-lease denial does not poison the later valid command. Signed replay now audits as authority-relevant `command_rejected` with no fallback side effect. |
| `AgentAttestation` manifest/model can represent authenticated identity and signature material, with canonical signed material handled by existing signing helpers. | met | `AgentAttestation` now carries `authenticated_agent_id` and `signature`; protocol manifest/spec/checklist/test strategy and demo setup were aligned. `attestation_auth_violation()` verifies identity/signature, and `attestation_trust_violation()` adds manifest, trust-tier, and revocation checks. Negative tests cover missing signature, invalid signature, authenticated identity mismatch, untrusted key, blank manifest/key id, revoked agent, unaccepted trust tier, and manifest mismatch. |
| Rust verifier emits authority-relevant command rejection audit for authenticated policy id/digest mismatch, while malformed or unauthenticated pre-auth failures stay diagnostic/non-authority. | met | `verifier.rs` now delays policy mismatch rejection until after command authentication when the command is authenticated; authenticated mismatch produces `command_rejected`/`authority_relevant=true`, while pre-auth policy failure remains diagnostic. Audit payloads include accepted and presented policy id/digest for downgrade forensics. |
| Security-relevant tests cover each changed behavior. | met | Focused Python attestation/replay tests passed (`16 passed, 132 deselected`); focused Rust policy-digest tests passed (`3 passed`). Full Python, Rust, compile, style, and diff checks passed after review fixes. |
| Assembly spec-conformance review is clean and post-review gates pass. | met | Subagent reviewer `019efa4f-3195-7302-8265-28af1bdd41d9` first found four gaps; fixes were applied. The same reviewer completed a clean re-review and noted only future residual key-rotation scope: `public_key_id` is presence-checked but not yet a separate key-registry selector. |

Review status:

- Initial subagent review found: incomplete ledger evidence, replay rejections
  incorrectly audited as diagnostics, missing presented/accepted Rust policy
  provenance, and an attestation helper that was auth-only.
- Review fixes applied:
  - decoupled command fallback emission from audit authority classification;
  - added replay audit assertions for `COMMAND_REPLAYED`;
  - added accepted/presented policy provenance to Rust authority audit payloads;
  - added `attestation_trust_violation()` and negative trust-boundary tests.
- Re-review by `019efa4f-3195-7302-8265-28af1bdd41d9`: clean, no remaining
  findings for D1-D4. Residual future scope is explicit key rotation keyed by
  `public_key_id`.

Evidence:

- `.venv/bin/python -m pytest tests/test_security_negative_paths.py -k "agent_attestation or replayed_signed_command_is_rejected_before_second_authorization or missing_lease_denial_does_not_consume_command_replay_state or replayed_signed_command_is_rejected_after_gate_restart" -q` -> `16 passed, 132 deselected`.
- `cargo test -p rclp-edge-verifier policy_digest -- --nocapture` -> `3 passed`.
- `.venv/bin/python -m compileall src tests` -> passed.
- `.venv/bin/python -m pytest` -> `217 passed`.
- `cargo test --workspace` -> passed after correcting one test-only policy provenance assertion; final result `38 passed` for vector tests, Rust unit test passed, doc tests passed.
- `.venv/bin/ruff check .` -> passed.
- `.venv/bin/ruff format --check .` -> `24 files already formatted`.
- `cargo fmt --all -- --check` -> passed.
- `git diff --check` -> passed.
- No cloud jobs, paid compute, or remote state were mutated.

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
