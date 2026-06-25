# S2 — Protocol/Security Red-team Review

## Verdict

GREEN for controlled technical validation calls.

This review does not prove production safety, production security, real robot
safety, real cellular behavior, or production trust operations. It supports the
narrower MVP claim that RCLP demonstrates a safety-adjacent authority layer with
scoped, expiring, locally enforced, revocable, network/geofence-conditioned, and
auditable authority in deterministic local validation.

Fresh evidence run for this review:

- Bare `pytest` is not installed on this shell path (`zsh: command not found:
  pytest`), so the supported repository virtualenv command was used.
- `.venv/bin/python -m compileall src tests` passed.
- `.venv/bin/python -m pytest` passed: 267 tests.
- `.venv/bin/python tests/evals/eval_runner.py` passed: 33 scenarios, 0
  failures.
- `cargo test --workspace` passed: 3 unit tests, 48 vector/integration tests,
  0 doc tests.
- `cargo fmt --all -- --check` passed.
- `cargo clippy --workspace --all-targets -- -D warnings` passed.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format --check .` passed.
- `.venv/bin/python scripts/run_cross_language_conformance.py --require-rust`
  passed: 15 mapped Python/Rust parity cases, 0 failures.

## Hardening claim assessment

- Scoped: credible for the MVP. Leases bind issuer, central agent, edge agent,
  robot, mission, capability, policy id/digest, constraints, and current signed
  local state. Python and Rust both reject wrong actor, robot, mission,
  capability, issuer scope, policy provenance, and constraint-bound cases.
- Expiring: credible. Lease expiry, not-yet-valid windows, stale-but-not-expired
  leases, and TTL overages are checked locally and covered by tests/evals.
- Locally enforced: credible. `CommandGate` rejects before a robot-facing
  command is allowed; the Rust verifier takes explicit trusted context and does
  not depend on cloud calls, files outside caller-supplied replay storage, or
  the system clock for authority decisions.
- Revocable: credible. Signed revocations require trusted revoker identity,
  edge scope, context match, freshness, and durable storage. Replays are
  idempotent and do not re-emit fallback side effects.
- Network/geofence-conditioned: credible. Fresh signed local state is required
  for remote assist. Unknown, detached, partitioned, or threshold-violating
  network state denies or degrades according to policy; geofence mismatch or
  outside state denies. Control-plane reachability is now a distinct optional
  signed protocol input that denies new authority when a policy explicitly
  requires it and the assertion is missing, stale, untrusted, partitioned,
  unknown, or unreachable.
- Auditable: credible for local MVP evidence. Authority events are written as
  `AuditCommit` records with payload hashes, hash-chain integrity proofs,
  state refs, related message ids, policy refs, and replay support. Signed audit
  batches now validate duplicate ids, payload hashes, previous-hash continuity,
  and recomputed integrity proofs before signing or verification.

## Attack paths reviewed

- no lease accepted: denied as `NO_LEASE`; the command replay cache is not
  consumed and fallback is not emitted.
- expired lease accepted: denied as `LEASE_EXPIRED` / `DENY_EXPIRED_LEASE`.
- revoked lease accepted: denied as `LEASE_REVOKED` /
  `DENY_REVOKED_LEASE`; revocation state survives command-gate restart.
- replayed nonce accepted: request nonce replay, command id/nonce replay, and
  accepted lease nonce replay are rejected; Python and Rust both cover restart
  persistence.
- wrong robot accepted: denied by lease/state/context binding.
- wrong mission accepted: denied by lease/state/context binding.
- wrong capability accepted: denied by lease context or capability scope.
- unknown signature algorithm accepted: denied before signature acceptance for
  Python request, state, lease, command, revocation, attestation, and fallback
  declaration profiles; Rust rejects unknown lease algorithms.
- malformed signature accepted: denied for request, lease, command,
  revocation, state, and attestation paths; oversized signed material is
  bounded before decode/canonicalization/verification where tested.
- missing required field silently defaults to unsafe value: not observed for
  reviewed authority fields. Strict schemas plus explicit `model_fields_set`
  checks reject missing `signature_alg`, request duration, state safety,
  human-operator state when policy requires it, `network_state.attached`, common
  lease envelope fields, and required constraints.
- network degradation only logged but not enforced: not observed. Network
  degradation and partition affect policy and command decisions; multi-step
  evals cover network-triggered revocation and partition/expiry behavior.
- geofence violation ignored: denied at policy and command-gate layers.
- central agent bypasses command gate: no bypass observed in the MVP scaffold.
  `EdgeAgentDaemon` routes commands through `CommandGate`, with a recording-gate
  delegation regression test; future real ROS 2, VDA5050, MCP, or A2A adapters
  still need adapter-level gate tests.
- audit trail does not prove causality: not observed for local MVP evidence.
  Audit commits bind payload, replay-critical top-level context, state refs,
  related message ids, policy refs, and previous chain value. Signed audit batch
  helpers reject tampered, duplicate, out-of-order, mixed, or non-contiguous
  event chains before signing or verification.
- edge verifier relies on cloud availability in unsafe way: not observed. The
  Rust core verifier is local and caller-supplied; Python command enforcement
  uses cached local policy/trust state and current local state.
- fallback behavior is underspecified: acceptable for this MVP boundary.
  Fallback is a declared hook and audit signal, not certified safety behavior;
  Python can sign and verify fallback declarations across a trust boundary.
- Python and Rust semantics diverge: no blocking divergence for the reviewed
  claim. Both enforce scoped, expiring, revocable, replay-resistant,
  network/geofence-conditioned edge authority. Residual differences are listed
  below.

## Fail-closed behavior

- Schema boundaries reject unknown fields and unsupported protocol versions.
- Policy issuance requires signed central request, durable request replay
  storage, accepted policy digest, explicit allow lists, signed fresh state,
  geofence satisfaction, network suitability, and bounded requested constraints.
- Command enforcement authenticates the command before lease validation,
  rejects nonlocal edge context before authority evaluation, requires durable
  command replay and revocation stores, pins policy provenance, verifies signed
  leases, requires fresh signed current state for `remote_assist`, checks
  network/geofence/speed constraints, and records accepted command plus lease
  nonce use atomically.
- Auth failures and malformed-input paths do not emit fallback side effects.
  Fallback is emitted only for authenticated local-state or authenticated
  revocation-backed denial classes.
- Rust rejects non-durable replay caches before authority decisions and emits
  diagnostic, non-authority audit records for malformed/pre-auth failures.

## Audit credibility

- `AuditLog.append()` rejects duplicate audit ids, validates authority context,
  validates payload hashes, and computes a local hash-chain proof.
- JSONL import requires common/integrity fields, rejects null required fields,
  validates chain order and integrity proof, rejects unknown context outside the
  proof, and requires a trusted chain head for authority-chain import.
- `AuditBatchCommit` is a local signed evidence artifact over committed audit
  events. Batch creation and verification recompute event payload hashes,
  rolling previous hashes, and integrity proofs, and reject duplicate,
  out-of-order, mixed-log, tampered, or non-contiguous chains.
- Command-authentication failures are diagnostic/non-authority and label
  claimed subject values as untrusted diagnostic context.
- Eval scenarios require audit completeness for allow, deny, network
  degrade/revoke, and partition/expiry flows.
- Rust audit events include decision, reason, payload hash, previous chain
  head, policy refs, state refs, related ids, and per-event identity entropy.

Remaining audit caveat: this is local tamper-evidence, signed-batch evidence,
and replay credibility, not a production append-only audit backend or production
key-management system.

## Python/Rust parity risks

- Rust uses deterministic `RCLP-DEV-HMAC-SHA256` vectors; Python uses the
  explicit non-production `RCLP-DEV-ED25519` profile. The development
  canonicalization and signature profiles are now documented in
  `docs/CRYPTO_PROFILES.md`. Production v0.1 still needs one production-grade
  cross-language signature/canonicalization profile.
- Python remains the reference for policy issuance, signed revocation
  verification, fallback declarations, and hash-chain audit import. Rust is an
  edge-verifier spike and does not yet verify Python Ed25519 demo leases,
  signed `LeaseRevocation` messages, or fallback declarations.
- Reason-code names are not identical between Python and Rust
  (`LEASE_NONCE_REPLAYED` vs `DENY_REPLAYED_NONCE`, for example), though the
  security outcomes align. The cross-language runner now checks mapped decision
  outcomes and accepted Python/Rust reason-code sets so wrong-deny regressions
  do not pass merely because both sides denied.
- `python scripts/run_cross_language_conformance.py --require-rust` now runs
  Python evals plus Rust vector tests from one command and writes a local parity
  report.

## Overclaims or unsafe wording

- The reviewed docs generally use the right boundary language: "safety-adjacent
  authority layer," "network-state-aware authorization," "fallback hook," and
  "sim proof" rather than production safety/security claims.
- `README.md`, `docs/SAFETY_BOUNDARY.md`, `docs/EVALS.md`,
  `docs/RUST_EDGE_VERIFIER.md`, and `docs/DEMO_SCRIPT.md` all state that this
  is not production robot safety, formal certification, real cellular proof, or
  production trust infrastructure.
- Continue scoping "hardening" to deterministic local MVP authority validation
  until production keys, trust roots, production audit persistence, and real
  adapters are done.

## Blocking issues

None for controlled technical validation calls.

Do not present this as proof of production safety, production security,
field-proven robot behavior, real cellular behavior, or production trust
operations.

## Recommended fixes

No blocking fixes are required before controlled technical validation calls.
Recommended future fixes before production or broader v0.1 claims:

- Define and implement a production-grade cross-language crypto profile with key
  ids, rotation, revocation, and production canonicalization stability.
- Extend Rust beyond the verifier spike if Rust is meant to validate Python
  Ed25519 leases, signed revocations, fallback declarations, control-plane
  assertions, or audit imports.
- Add adapter-level tests as real ROS 2, VDA5050, Open-RMF, MCP, or A2A paths
  arrive so robot-facing command routes cannot bypass `CommandGate`.
- Replace local JSONL/hash-chain/signed-batch evidence with a production
  append-only or otherwise tamper-evident backend before making production audit
  claims.
