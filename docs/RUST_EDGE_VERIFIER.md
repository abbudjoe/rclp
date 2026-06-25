# Rust Edge Verifier

The Rust edge verifier is a small spike for the future hardened RCLP trust
boundary. Python remains the reference implementation for protocol iteration,
policy behavior, and Isaac Sim demos. The Rust crate exists to prove the
edge-side primitive can be expressed as deterministic, dependency-light library
code.

## Trust Boundary

The verifier sits at the robot-local command gate. A caller supplies untrusted
message material (`CapabilityLeaseEnvelope`, versioned `EdgeCommand`, and
signed observed local robot context) separately from trusted verifier context:
issuer trust roots, the dev lease HMAC secret, edge-state trust roots, the dev
state HMAC secret, accepted policy references, accepted capabilities,
issuer-to-capability scopes, local revocation state, explicit verifier time,
and local lease/state TTL/age policy limits. The caller also supplies a
durable/shared replay cache. The verifier
returns `allow`, `deny`, or `degrade` with a machine-readable reason code and an
audit event.

`local_context` is observed robot-local state: robot identity, edge identity,
authenticated edge identity, mission identity, network state, geofence state,
and a dev-profile state signature. `TrustedVerifierContext` contains trust
roots, the dev lease and state HMAC secrets, revocations, explicit verifier
time, accepted capabilities, issuer-to-capability scopes, and local lease/state
TTL/age limits used by this spike. The split keeps trusted verifier
configuration out of the command/observation payload while still making all
verification inputs explicit.

The core verifier does not read files, call the system clock, open network
connections, launch ROS 2 nodes, or talk to Isaac Sim.
Audit identity generation is the only exception to deterministic input-only
behavior: each emitted audit event binds a per-event sequence and identity
nonce so repeated malformed or authority decisions cannot collide on
`audit_id`/`message_id`.

## Current Checks

The crate verifies:

- lease claims and commands carry the expected protocol version and message type
- signature algorithm is known
- dev HMAC signature matches canonical lease claims, including signed
  `policy_id` and `policy_digest`
- the lease's signed policy reference matches the current trusted policy
  reference and is included in accepted policies
- issuer is trusted by `TrustedVerifierContext`
- requested capability is locally accepted and included in the trusted issuer's
  explicit capability scope
- local context is signed by a trusted authenticated edge identity before its
  network or geofence values can affect authority
- lease is not before-valid, expired, stale, revoked, or over the local TTL
  limit
- lease nonce can be consumed by the replay cache for an allow or degrade
  decision
- command, lease, and local context agree on robot, edge agent, central agent,
  mission, and capability
- required `remote_assist` constraints exist
- local robot, network, and geofence timestamps are fresh
- geofence state satisfies the lease constraint
- network state satisfies lease constraints, or explicitly degrades only when a
  fallback hook is present
- command HMAC covers the command protocol envelope and `payload`
- signed command material is bounded before HMAC canonicalization can run on
  untrusted input, including scalar command fields, signature text, and the
  command `payload` size, node count, and nesting depth
- command payload speed satisfies `max_speed_mps` when the lease includes that
  constraint
- the supplied replay cache reports durable/shared semantics before any
  authority decision can consume command or lease nonce state
- authority-relevant audit events carry authority context; malformed pre-parse
  inputs produce diagnostic non-authority audit records
- command-authentication failures produce diagnostic non-authority audit records
  with claimed subject values labeled as untrusted payload context

All failures return deny/degrade decisions rather than panicking.

## What It Does Not Do

This spike does not implement ROS 2, Isaac Sim, PyO3 bindings, a production
replay service, policy issuance, fleet management, teleop media, a dashboard,
hosted services, carrier integration, or low-level robot safety controls.

It is a safety-adjacent authority verifier, not a certified safety system.

## Relationship To Python

The Python implementation remains the MVP reference. The Rust verifier mirrors
the edge command-gate semantics: short-lived scoped leases, explicit local
context, trusted issuers, local revocation state, replay rejection,
geofence/network checks, speed constraints, command actor authentication,
command freshness/replay rejection, local-state freshness, and auditable
fail-closed decisions.

Python and Rust now share the MVP replay decision that an accepted lease nonce
is single-use in the edge verifier replay window. Python reports
`LEASE_NONCE_REPLAYED`; Rust reports `DENY_REPLAYED_NONCE`.

The shared vectors live in `tests/vectors/edge_verifier/`. Each vector keeps
untrusted verification input under `input`, trusted local verifier state under
`trusted_context`, and test replay-cache seed state under `seen_nonces`.
`trusted_context` includes the accepted policy id/digest, issuer and command
trust roots, accepted capability scopes, and per-capability constraint
requirements. Rust tests execute the vectors. Python tests validate vector shape
so pytest does not depend on Cargo. The crate also exposes a thin CLI bridge:

```bash
cargo run -p rclp-edge-verifier --bin rclp-edge-verify -- \
  tests/vectors/edge_verifier/valid_remote_assist_lease.json
```

The CLI runs the same `verify_json_value` library path and writes a JSON
decision with `decision`, `reason_code`, and `audit_event`.

Run the combined Python/Rust parity gate with:

```bash
python scripts/run_cross_language_conformance.py
```

The runner executes Python evals and Rust vector tests when Cargo is available,
then writes `tests/evals/reports/cross_language_latest.json`. It compares shared
decision semantics while preserving each implementation's native reason codes.

`ReplayCache::consume_nonce()` is intentionally a single check-and-mark
operation from the verifier's perspective. `ReplayCache::durability()` must
report durable/shared semantics or the verifier denies before authority
evaluation. The crate exports `FileReplayCache` as a small reference
implementation whose nonce consumption uses atomic per-nonce file creation, so
tests and local adapters can prove replay state survives verifier recreation.
Production edge deployments may replace it with a stronger shared durable store
that preserves the same atomic consume contract across verifier instances and
restarts.

## MVP Crypto Status

The current Rust vector profile is `RCLP-DEV-HMAC-SHA256`.

Rules:

- HMAC-SHA256 is computed over canonical JSON lease claims.
- Separate dev HMACs are computed over canonical JSON command envelope,
  identity fields, nonce, timestamp, and `payload`, and over local context
  fields, excluding their respective `signature` fields.
- Canonical JSON uses sorted object keys and no insignificant whitespace.
- The signed payload excludes the signature field.
- Unknown algorithms are rejected.

This profile is test-only. Production edge deployments should replace or
supplement it with an asymmetric signature profile such as Ed25519, key IDs,
rotation, revoked-key handling, and a normative canonicalization spec. The
Python demo uses the explicit non-production
`signature_alg="RCLP-DEV-ED25519"` profile; the Rust HMAC profile is only to
keep shared vectors deterministic and offline during this spike.

The normative development-profile details for both Python and Rust live in
`docs/CRYPTO_PROFILES.md`.

## Running Tests

From the repository root:

```bash
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
python -m compileall src tests
python -m pytest
```

Use the repo virtualenv if the system Python does not have pytest installed:

```bash
.venv/bin/python -m pytest
```

## Production Gaps

- Stable versioned schemas are still needed for cross-language implementers.
- The Rust crate does not yet verify Python Ed25519 demo leases.
- The crate provides `FileReplayCache` as a local durable reference cache, not
  a production replay service for clustered edge deployments.
- Production issuer key rotation is not modeled in the Rust spike.
- The Rust spike consumes a local revocation set; it does not verify
  `LeaseRevocation` message signatures. The Python command gate verifies signed
  revocation messages in the MVP reference path.
- Fallback declaration signature verification is implemented in the Python MVP
  reference path, but not in the Rust spike.
- `ControlPlaneReachabilityAssertion` and `AuditBatchCommit` are Python MVP
  reference paths in this pass. Rust parity is limited to the edge verifier's
  command/lease/local-context vectors.
- Clock trust and monotonic time handling are still assumptions.
- Audit persistence and hash-chain integration remain in the Python reference.
