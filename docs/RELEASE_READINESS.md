# Release Readiness

Status: ready for controlled technical validation after the local validation
commands pass in the current checkout. This is not a production readiness
claim.

## Current MVP Status

RCLP currently demonstrates a local reference profile for the `remote_assist`
authority primitive:

```text
central agent requests authority
-> edge agent evaluates policy and local state
-> a signed short-lived lease is issued, denied, degraded, or revoked
-> command gate enforces locally
-> audit replay reconstructs the event chain
```

The repo is intentionally protocol-oriented. It is suitable for technical
review, controlled demos, and customer-discovery conversations about the
authority primitive.

## Implemented

- Pydantic protocol models for the MVP message surface.
- Signed local `CapabilityRequest` and `CapabilityLease` paths using
  non-production demo keys.
- Policy evaluation over identity, mission, geofence, human-operator
  availability, network state, accepted policy digest, request age, and replay
  cache.
- Deterministic network profiles: `normal`, `degraded_teleop`, `uplink_bad`,
  and `partition`.
- Edge command gate that rejects missing, invalid, expired, stale, revoked,
  mismatched, overlong, or constraint-violating leases.
- Fallback declarations as events and hooks, not certified safety behavior.
- Audit JSONL, payload hashes, local hash-chain integrity proof, and replay
  summary.
- Python demo: `python -m rclp_agents.demo_remote_assist`.
- Rust edge verifier spike with offline JSON vectors and test-only HMAC crypto.
- CI workflows for Python and Rust validation.

## Stubbed Or Scaffolded

- ROS 2 integration is a command-gate scaffold, not a full ROS 2 adapter.
- Isaac Sim work is a POC plan and script scaffold; the repo does not contain a
  full simulator implementation.
- Rust verifier is a spike, not a replacement for the Python reference and not
  production cryptographic infrastructure.
- Carrier/MVNO, real QoS, real cellular impairment, and managed connectivity
  integrations are out of scope.
- Hosted trust root, managed policy UI, accounts, billing, and fleet-scale
  audit backend are out of scope for this repo.

## Run Tests

Python:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m compileall src tests
pytest
```

Rust, when the Rust toolchain is installed:

```bash
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
```

Optional formatting/linting if installed:

```bash
ruff check .
ruff format . --check
```

## Run Demo

Default local proof:

```bash
python -m rclp_agents.demo_remote_assist
```

Hard-deny impaired profile:

```bash
python -m rclp_agents.demo_remote_assist --network-profile uplink_bad
```

Expected visible evidence:

- `capability_request`
- `normal_network_decision` with `POLICY_SATISFIED`
- `command_gate_with_valid_lease` with `LEASE_VALID`
- `command_without_valid_lease` with `NO_LEASE`
- `impaired_network_decision` with degrade or deny reason codes
- `lease_revocation`
- `command_gate_after_network_revocation` with `LEASE_REVOKED`
- `audit_jsonl`
- `incident_replay_summary`

## Known Gaps

- Production key management, key rotation, attestation, and hardware-backed
  trust are not implemented.
- Revocation and some standalone messages still need authenticated trust-boundary
  envelopes for a hardened profile.
- Replay windows are in-memory in the Python reference.
- Clock trust and monotonic-time handling remain MVP assumptions.
- Rust verifier uses `RCLP-DEV-HMAC-SHA256` vectors for deterministic offline
  tests and does not verify Python demo Ed25519 leases.
- ROS 2 and Isaac Sim integration remain scaffolded.
- Real cellular behavior, carrier APIs, field safety, and customer willingness
  are not proven.
- `LICENSE` should be reviewed by project counsel before public launch even
  when using Apache-2.0 text.

## Before-Customer-Call Checklist

- Run Python and Rust validation commands in a clean checkout.
- Run the default demo and one impaired profile.
- Skim `docs/SAFETY_BOUNDARY.md` and avoid production safety claims.
- Skim `docs/COMMERCIAL_BOUNDARY.md` and keep hosted platform discussion
  separate from the open repo.
- Open `docs/RUST_EDGE_VERIFIER.md` before discussing the Rust spike.
- Prepare to show the tests under `tests/`, especially negative security and
  conformance tests.
- Use `docs/CUSTOMER_VALIDATION_MEMO.md` to keep feedback focused on the
  authority primitive.
- Record customer feedback as issues or field notes; do not expand protocol
  scope during the call.
