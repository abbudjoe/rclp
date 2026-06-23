# Assembly Ledger

## Post-Scan 4-Finding Security Remediation - 2026-06-23T2

Status: successful

Source contract:

- User request: resolve all four Codex Security findings using `assembly`.
- Completed fresh Codex Security scan `0aab2b4e-d69b-4eb4-830f-edcde6bbf656`.
- Scan report:
  `/private/var/folders/5s/5dk3z2k93lgfqmsn0l28_lbm0000gn/T/codex-security-scans-XVS5WG/rclp/4ad0fe8e14eeb0d47e9f051f24ef5eee4ba76273_20260623T165856Z_r90lo99j/report.md`
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
  `/private/var/folders/5s/5dk3z2k93lgfqmsn0l28_lbm0000gn/T/codex-security-scans-XVS5WG/rclp/4ad0fe8e14eeb0d47e9f051f24ef5eee4ba76273_20260623T141934Z_j9b_oj7r/report.md`
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
- Codex Security scan `eb7bed48-4cd6-41db-b868-66d4fa26f023` report at `/private/var/folders/5s/5dk3z2k93lgfqmsn0l28_lbm0000gn/T/codex-security-scans-XVS5WG/rclp/4ad0fe8e14eeb0d47e9f051f24ef5eee4ba76273_20260623T030156Z_69_emnx1/report.md`.
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
  `/private/var/folders/5s/5dk3z2k93lgfqmsn0l28_lbm0000gn/T/codex-security-scans-f4cVft/rclp/4ad0fe8e14eeb0d47e9f051f24ef5eee4ba76273_20260623T014350Z_7yfom2zj/report.md`
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
  `/private/var/folders/5s/5dk3z2k93lgfqmsn0l28_lbm0000gn/T/codex-security-scans-f4cVft/rclp/4ad0fe8e14eeb0d47e9f051f24ef5eee4ba76273_20260623T004740Z_17myo_fj/report.md`
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
  Boost/internal references and fallback hooks remains.

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
