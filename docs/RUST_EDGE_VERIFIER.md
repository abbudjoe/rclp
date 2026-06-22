# Rust Edge Verifier

The Rust edge verifier is a small spike for the future hardened RCLP trust
boundary. Python remains the reference implementation for protocol iteration,
policy behavior, and Isaac Sim demos. The Rust crate exists to prove the
edge-side primitive can be expressed as deterministic, dependency-light library
code.

## Trust Boundary

The verifier sits at the robot-local command gate. A caller supplies untrusted
message material (`CapabilityLeaseEnvelope`, `EdgeCommand`, and observed local
robot context) separately from trusted verifier context: issuer trust roots, the
dev HMAC secret, local revocation state, explicit verifier time, and local
lease TTL/age policy limits. The caller also supplies a replay cache. The
verifier returns `allow`, `deny`, or `degrade` with a machine-readable reason
code and an audit event.

`local_context` is observed robot-local state: robot identity, edge identity,
mission identity, network state, and geofence state. `TrustedVerifierContext`
contains trust roots, the dev HMAC secret, revocations, explicit verifier time,
and local TTL/age limits used by this spike. The split keeps trusted verifier
configuration out of the command/observation payload while still making all
verification inputs explicit.

The core verifier does not read files, call the system clock, open network
connections, launch ROS 2 nodes, or talk to Isaac Sim.

## Current Checks

The crate verifies:

- signature algorithm is known
- dev HMAC signature matches canonical lease claims
- issuer is trusted by `TrustedVerifierContext`
- lease is not before-valid, expired, stale, revoked, or over the local TTL
  limit
- lease nonce has not already been seen
- command, lease, and local context agree on robot, edge agent, central agent,
  mission, and capability
- required `remote_assist` constraints exist
- geofence state satisfies the lease constraint
- network state satisfies lease constraints, or explicitly degrades only when a
  fallback hook is present

All failures return deny/degrade decisions rather than panicking.

## What It Does Not Do

This spike does not implement ROS 2, Isaac Sim, PyO3 bindings, persistent replay
storage, policy issuance, fleet management, teleop media, a dashboard, hosted
services, carrier integration, or low-level robot safety controls.

It is a safety-adjacent authority verifier, not a certified safety system.

## Relationship To Python

The Python implementation remains the MVP reference. The Rust verifier mirrors
the edge command-gate semantics: short-lived scoped leases, explicit local
context, trusted issuers, revocation, replay rejection, geofence/network checks,
and auditable fail-closed decisions.

One intentional spike delta is replay handling: the current Python command gate
does not persistently consume lease nonces, while T10 requires the Rust verifier
to mark a valid lease nonce on first successful use and reject a second use with
`DENY_REPLAYED_NONCE`. Treat that as a hardening experiment, not a finalized
protocol decision.

The shared vectors live in `tests/vectors/edge_verifier/`. Each vector keeps
untrusted verification input under `input`, trusted local verifier state under
`trusted_context`, and test replay-cache seed state under `seen_nonces`. Rust
tests execute the vectors. Python tests only validate vector shape so pytest
does not depend on Cargo.

## MVP Crypto Status

The current Rust vector profile is `RCLP-DEV-HMAC-SHA256`.

Rules:

- HMAC-SHA256 is computed over canonical JSON lease claims.
- Canonical JSON uses sorted object keys and no insignificant whitespace.
- The signed payload excludes the signature field.
- Unknown algorithms are rejected.

This profile is test-only. Production edge deployments should replace or
supplement it with an asymmetric signature profile such as Ed25519, key IDs,
rotation, revoked-key handling, and a normative canonicalization spec. The
Python demo already uses non-production Ed25519 helpers; the Rust HMAC profile
is only to keep shared vectors deterministic and offline during this spike.

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
- Replay protection is in-memory only.
- Whether lease nonces are single-use or command/session-scoped needs v0.1
  protocol resolution.
- Trust roots and issuer key rotation are not modeled.
- Revocation and fallback declaration signatures remain v0.1 hardening items.
- Clock trust and monotonic time handling are still assumptions.
- Audit persistence and hash-chain integration remain in the Python reference.
