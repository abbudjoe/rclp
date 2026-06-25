# S2 — Protocol/Security Red-team Review

## Verdict

GREEN for controlled technical validation calls.

This does not prove production safety, production security, real robot safety,
real cellular behavior, or a hardened production trust infrastructure. It does
support the narrower MVP claim that RCLP demonstrates a safety-adjacent
authority layer with scoped, expiring, locally enforced, revocable,
network/geofence-conditioned, and auditable authority.

Evidence run:

- `python -m compileall src tests` passed.
- `uv run --extra dev pytest` passed: 246 tests.
- `uv run python tests/evals/eval_runner.py` passed: 33 scenarios, 0 failures.
- `cargo test --workspace` passed: 3 unit tests and 47 vector tests.
- `cargo fmt --all -- --check` passed.
- `cargo clippy --workspace --all-targets -- -D warnings` passed.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed.

The system Python lacked `pytest`, `PyYAML`, and `ruff`; I used `uv` against the
project metadata to run the Python evidence without changing tracked source.

## Hardening claim assessment

- Scoped: credible. Python lease validation checks issuer trust, accepted
  capabilities, issuer capability scope, policy provenance, agent, edge agent,
  robot, mission, capability, constraints, revocation state, current signed
  local state, and command payload constraints in `src/rclp_core/conformance.py`.
- Expiring: credible. Python and Rust both reject expired, future, stale, and
  over-TTL leases; tests and evals cover `LEASE_EXPIRED`, `LEASE_NOT_YET_VALID`,
  stale lease, and TTL-too-long paths.
- Locally enforced: credible for the MVP. `CommandGate` requires local trusted
  config, durable replay cache, durable revocation store, local policy
  provenance, local state keys, and local constraint bounds before accepting a
  command. `EdgeAgentDaemon.handle_command()` delegates directly to the gate.
- Revocable: credible. Revocation requires a signed `LeaseRevocation`, trusted
  revoker identity, edge scope, context match, freshness, durable storage, and
  replay-idempotent fallback behavior.
- Network/geofence-conditioned: credible. Network and geofence are signed local
  state inputs; unknown/partition/detached network state denies, threshold
  violations deny/degrade, and geofence mismatch or outside state denies.
- Auditable: credible for local MVP evidence. Audit events hash payloads, bind
  replay-critical top-level context into integrity proof, require robot/mission
  context for authority events, and support replay summaries. The eval suite
  requires audit fields for allow/deny and multi-step revocation/partition
  scenarios.

## Attack paths reviewed

- no lease accepted: rejected as `NO_LEASE`; missing-lease denial does not
  consume command replay state or emit fallback.
- expired lease accepted: rejected as `LEASE_EXPIRED` / `DENY_EXPIRED_LEASE`.
- revoked lease accepted: rejected as `LEASE_REVOKED` /
  `DENY_REVOKED_LEASE`; durable revocation survives gate restart.
- replayed nonce accepted: request replay is rejected by a durable SQLite cache;
  command replay is rejected; Rust also rejects replayed lease nonce.
- wrong robot accepted: rejected as context/robot mismatch.
- wrong mission accepted: rejected as context/mission mismatch.
- wrong capability accepted: rejected as context mismatch or capability not
  granted.
- unknown signature algorithm accepted: Rust rejects with
  `DENY_UNKNOWN_ALGORITHM`; Python has no first-class algorithm field and fails
  the scenario closed as `INVALID_SIGNATURE`.
- malformed signature accepted: rejected for request, lease, command,
  revocation, state, and attestation paths; oversized signed material is
  bounded before verification.
- missing required field silently defaults to unsafe value: mostly rejected.
  Strict Pydantic/Rust schemas, explicit `model_fields_set` checks, and
  `deny_unknown_fields` prevent unsafe defaults for authority fields such as
  request duration, state safety, human operator availability, and
  `network_state.attached`.
- network degradation only logged but not enforced: not observed. Policy
  degrades/denies, command gate rejects current-state network violations, and
  the eval suite covers network degradation revoking a prior lease.
- geofence violation ignored: rejected at policy and command-gate layers.
- central agent bypasses command gate: not present in the MVP scaffold.
  `EdgeAgentDaemon` delegates to `CommandGate`; real ROS 2 adapter miswiring is
  not yet proven impossible because the ROS 2 integration remains a scaffold.
- audit trail does not prove causality: not observed for local MVP. The audit
  chain binds payload hash, event identity, actor, robot, mission, policy refs,
  state refs, related messages, authority relevance, and previous hash.
- edge verifier relies on cloud availability in unsafe way: not observed. Rust
  verifier has explicit trusted context, explicit time, durable replay cache,
  no network calls, and no system-clock dependency in core verification.
- fallback behavior is underspecified: acceptable for MVP, not production.
  Fallback hooks are local declarations and audit signals, not certified safety
  behavior; signed fallback envelopes remain a future hardening item.
- Python and Rust semantics diverge: present but documented. Python is the MVP
  reference; Rust is a verifier spike with explicit algorithm envelopes and
  single-use lease nonce semantics. Both fail closed on reviewed cases.

## Fail-closed behavior

The core fail-closed story is strong for a reference MVP:

- Schema boundaries reject unknown fields and unsupported protocol versions.
- Request issuance requires signed agent identity, signed fresh state,
  accepted policy digest, durable request replay storage, explicit allow lists,
  geofence satisfaction, and network satisfaction.
- Command enforcement authenticates the command first, rejects nonlocal edge
  context before lease validation, does not consume replay state for `NO_LEASE`,
  validates signed lease provenance and constraints, requires current signed
  state for remote assist, and only emits fallback for authenticated local-state
  or authenticated revocation-backed denial classes.
- Durable command replay and durable revocation stores are constructor
  requirements for `CommandGate`.
- Rust rejects malformed input, non-durable replay caches, unknown algorithms,
  command-auth failures, policy digest mismatch, stale state, network/geofence
  failures, and replayed command or lease nonces.

The main fail-closed limitation is integration scope: this proves local library
and scaffold behavior, not that every future ROS 2, VDA5050, MCP, A2A, or robot
runtime path is physically wired through the gate.

## Audit credibility

Audit credibility is good for local deterministic validation:

- `AuditLog.append()` rejects duplicate audit IDs, validates authority context,
  validates payload hash, and computes a chained integrity proof.
- Import requires required fields, rejects null required fields, validates
  chain order, rejects proof mismatch, and requires a trusted chain head for
  authority-chain import.
- Command-authentication failures are diagnostic/non-authority and label
  claimed subject values as untrusted.
- Eval scenarios require audit fields for allow, deny, network degrade/revoke,
  and cloud partition/expiry flows.
- Rust audit events bind payload hash, reason, decision, identity nonce,
  previous chain head, policy refs, state refs, and related messages.

Remaining audit caveats: the Python eval mapping is not a final v0.1
conformance schema, audit persistence is local only, and there is no external
append-only backend or production key infrastructure in this repo.

## Python/Rust parity risks

- Python has no first-class signature algorithm envelope; Rust does. Python
  still fails unknown-alg fixtures closed as invalid signature, but the reason
  semantics differ.
- Rust consumes lease nonce on allow/degrade and rejects second use; Python does
  not persistently consume lease nonces at the command gate. This is documented
  as a hardening experiment, but it needs a v0.1 protocol decision.
- Rust uses deterministic test-only HMAC vectors; Python demo paths use
  non-production Ed25519 helpers. There is no Rust CLI or Python-vs-Rust eval
  bridge that executes the same full scenario suite end to end.
- Rust consumes local revocation sets but does not verify signed
  `LeaseRevocation` messages; Python verifies signed revocations in the MVP
  reference path.

None of these parity risks invalidate the current MVP hardening claim because
both sides fail closed for the reviewed attack cases, but they do block a
stronger cross-language conformance claim.

## Overclaims or unsafe wording

The repo is generally careful. `README.md`, `docs/SAFETY_BOUNDARY.md`,
`docs/EVALS.md`, and `docs/RUST_EDGE_VERIFIER.md` repeatedly state that this is
a safety-adjacent authority layer, not a certified safety system, production
robot safety proof, real cellular proof, or production trust infrastructure.

One wording risk remains: "hardening" should keep being scoped to local MVP
authority validation. Avoid implying production security until key rotation,
hardware-backed trust, production audit persistence, real adapter enforcement,
and cross-language conformance are complete.

## Blocking issues

No blocking issues for controlled technical validation calls.

Do not use this report as evidence of production safety, production security,
field-proven robot behavior, real cellular behavior, or production-ready trust
operations.

## Recommended fixes

- Decide v0.1 lease nonce semantics and align Python/Rust behavior.
- Add a first-class Python signature algorithm envelope or explicitly document
  Python's current Ed25519-only profile as the reference behavior.
- Add a Rust CLI or shared eval bridge so Python eval scenarios and Rust vector
  semantics can be compared by one command.
- Finalize an audit conformance schema beyond the current eval mapping.
- Sign and verify `FallbackDeclaration` envelopes for trust-boundary use, while
  keeping fallback hooks explicitly non-certified.
- Document or model cloud/control-plane reachability separately if future
  claims need to distinguish cloud partition from local network degradation.
- Add adapter-level tests when ROS 2/VDA5050/MCP/A2A paths are implemented so
  no robot-facing command route can bypass `CommandGate`.
