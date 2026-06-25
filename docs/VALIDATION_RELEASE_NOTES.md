# RCLP v0.1-validation Release Notes

This release is intended for controlled technical validation calls, not
production robot deployments.

## Purpose

`v0.1-validation` packages the RCLP MVP for 5-8 controlled calls with
robotics, platform, fleet operations, teleoperation, and safety/compliance
stakeholders. The goal is to validate whether the central-agent to edge-agent
authority primitive maps to real robot-fleet workflows.

This is not a broad public launch and not a production-readiness claim.

## Implemented Components

- Python reference implementation for capability requests, policy evaluation,
  signed short-lived leases, command gating, revocation, fallback declarations,
  audit JSONL, and incident replay.
- Local deterministic network profiles for `normal`, `degraded_teleop`,
  `uplink_bad`, and `partition`.
- Remote-assist demo with local non-production keys and deterministic fixtures.
- Adversarial eval harness under `tests/evals/`.
- Rust edge verifier spike with deterministic offline vectors and test-only
  HMAC crypto.
- Safety, commercial, threat-model, conformance, and release-readiness docs.
- Validation scripts:
  - `./scripts/run_validation_checks.sh`
  - `./scripts/run_validation_demo.sh`

## Demo Flow

The five-minute local flow shows:

1. A central/fleet agent requests `remote_assist` authority.
2. The edge-side policy path checks identity, mission, robot, geofence, network
   state, replay state, lease scope, revocation, and fallback policy.
3. A valid scoped lease allows a gated command.
4. A command without a valid lease fails closed.
5. Network degradation causes degradation or revocation.
6. Later use of revoked authority is rejected.
7. Audit replay reconstructs the request, state, decision, enforcement,
   revocation, and fallback chain.

Run it with:

```bash
./scripts/run_validation_demo.sh
```

Detailed call notes live in `docs/DEMO_WALKTHROUGH.md`.

## Eval Coverage

The current deterministic eval suite has 33 scenarios. It covers:

- valid remote-assist authority
- no lease, expired lease, not-yet-valid lease, revoked lease, and replayed
  request nonce paths
- malformed input and invalid signature paths
- wrong central agent, edge agent, robot, mission, and capability
- geofence violation
- degraded latency, packet loss, uplink failure, and partitioned network state
- stale command and stale current edge state
- unsigned current state, unsigned policy state, and unsigned revocation paths
- over-speed and malformed command payload paths
- audit completeness for allow and deny paths
- multi-step network-degradation revocation
- multi-step cloud-partition/lease-expiry behavior

Run the evals with:

```bash
python tests/evals/eval_runner.py
```

The runner writes `tests/evals/reports/latest.json`.

## Rust Verifier Status

The Rust crate under `crates/rclp-edge-verifier/` is an edge verifier spike. It
proves that core edge-side checks can be expressed as deterministic,
dependency-light Rust code with offline vectors. It is not a replacement for
the Python reference implementation and does not yet verify the Python demo's
Ed25519 leases.

The Rust profile uses `RCLP-DEV-HMAC-SHA256` for deterministic tests only.
Production deployments need a hardened asymmetric signature profile, key
rotation, hardware-backed trust where appropriate, and operational replay and
revocation services.

## Known Hardening Gaps

- Production key management, key rotation, attestation, and hardware-backed
  trust are not implemented.
- Clock trust, monotonic-time behavior, retention, compaction, backup, and
  recovery policy remain MVP assumptions.
- Fallback declarations are hooks and audit signals, not certified safety
  behavior.
- ROS 2 and Isaac Sim integration remain scaffolded.
- Real cellular behavior, carrier APIs, field safety, and customer willingness
  are not proven.
- Hosted trust roots, customer accounts, managed policy UI, billing, and
  commercial SLAs belong in a future separate platform repo.

## Non-Claims

This release does not claim:

- production robot safety
- formal safety certification
- field-proven safety
- real cellular or carrier API behavior
- production cryptographic trust infrastructure
- real robot deployment readiness
- customer adoption or willingness to buy
- hosted commercial-platform readiness

Use "safety-adjacent authority layer" and "fallback hook" when describing the
MVP.

## Intended Audience

Best-fit reviewers are skeptical technical stakeholders who operate or build
robot fleets with remote assist, autonomy escalation, central orchestration,
edge runtimes, and incident/audit needs:

- robotics platform engineers
- fleet reliability leads
- heads of robot operations or teleoperation
- autonomy infrastructure leads
- safety/compliance leads

## Validation Commands

From a checkout with dev dependencies installed:

```bash
./scripts/run_validation_checks.sh
./scripts/run_validation_demo.sh
```

These commands do not require network access, ROS 2, Isaac Sim, cloud
credentials, or robot hardware.

## Suggested Tag

Do not create the tag until the project owner has reviewed the package and the
validation script passes in the intended checkout.

Suggested command:

```bash
git tag -a v0.1-validation -m "RCLP v0.1 validation release"
```

## Next Validation Steps

1. Run `./scripts/run_validation_checks.sh` from a clean checkout.
2. Run `./scripts/run_validation_demo.sh` and keep
   `docs/DEMO_WALKTHROUGH.md` open during the call.
3. Send `docs/CUSTOMER_CALL_PACKET.md` before or after the call.
4. Use `docs/FIRST_CALL_TARGET_PROFILE.md` to prioritize the first 5-8 calls.
5. Record feedback as issues or field notes without expanding protocol scope
   during calls.
6. After the first calls, decide whether to prioritize Rust parity,
   observe-only pilot design, Isaac Sim polish, protocol-boundary revision, or
   separate commercial platform planning.
