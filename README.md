# RCLP

RCLP is an open protocol MVP for short-lived capability leases between
central/fleet agents and robot-local edge agents operating robots.

The Robot Capability Lease Protocol focuses on a narrow authority gap:
existing robot, fleet, network, and agent protocols move commands, state,
tools, or missions, while RCLP asks whether authority may pass from a central
actor to an edge actor for a physical capability under current conditions.

This repository is the open reference implementation for that primitive. It is
not the future hosted commercial platform.

## What This MVP Demonstrates

- central-agent capability requests
- edge-agent local verification
- signed short-lived leases
- explicit MVP signature algorithm metadata
- allow, deny, degrade, and revoke decisions
- network-state-conditioned authority
- geofence-conditioned authority
- command gating before a robot-facing command path
- audit JSONL and replay of the authority chain
- audit conformance schema for the MVP authority chain
- Python reference implementation
- Rust edge verifier spike

The local proof uses deterministic fixtures and local non-production keys. The
main flow is:

```text
central agent requests authority
-> edge agent verifies local context and policy
-> lease is granted, denied, degraded, or revoked
-> command gate enforces locally
-> audit replay reconstructs the event chain
```

## What This MVP Does Not Demonstrate

- formal safety certification
- production robot safety
- real cellular behavior
- carrier API behavior
- production cryptographic trust infrastructure
- customer willingness to deploy
- full robot hardware integration
- hosted commercial platform
- fleet management, teleoperation media, or mission scheduling

## Quickstart

Requires Python 3.11 or newer. The local demo does not require ROS 2, Isaac
Sim, root privileges, cloud credentials, external services, or host network
mutation.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m compileall src tests
pytest
python tests/evals/eval_runner.py
python -m rclp_agents.demo_remote_assist
```

For the packaged validation path:

```bash
./scripts/run_validation_checks.sh
./scripts/run_validation_demo.sh
```

Run a hard-deny deterministic network profile:

```bash
python -m rclp_agents.demo_remote_assist --network-profile uplink_bad
```

If Rust is installed, run the edge verifier spike:

```bash
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
cargo run -p rclp-edge-verifier --bin rclp-edge-verify -- \
  tests/vectors/edge_verifier/valid_remote_assist_lease.json
```

Rust prerequisites are the standard stable Rust toolchain with `cargo`,
`rustfmt`, and `clippy`.

## Validation Release

`v0.1-validation` is the controlled technical validation package for the MVP.
It is intended for robotics/platform/fleet-operator calls, not production robot
deployments.

Start here:

- `docs/VALIDATION_RELEASE_NOTES.md`
- `docs/CUSTOMER_CALL_PACKET.md`
- `docs/DEMO_WALKTHROUGH.md`
- `docs/EVALS.md`
- `docs/WHY_NOT_EXISTING_PROTOCOLS.md`

Run:

```bash
./scripts/run_validation_checks.sh
./scripts/run_validation_demo.sh
```

## Demo Path

`python -m rclp_agents.demo_remote_assist` runs a complete local
`remote_assist` authority negotiation:

1. Creates local central-agent, edge-agent, robot, mission, geofence, policy,
   and non-production key fixtures.
2. Signs a `CapabilityRequest`.
3. Allows a short-lived lease under the normal deterministic network profile.
4. Accepts a matching command through the command gate.
5. Rejects a command with no lease.
6. Applies an impaired network profile and returns degrade or deny.
7. Revokes the previous lease and rejects later command use.
8. Prints `audit_jsonl` and `incident_replay_summary`.

Expected stable markers include `POLICY_SATISFIED`, `NO_LEASE`,
`NETWORK_LATENCY_DEGRADED` for the default impaired profile,
`NETWORK_UPLINK_TOO_LOW` for `--network-profile uplink_bad`,
`NETWORK_PROFILE_REVOKE`, `LEASE_REVOKED`, `audit_jsonl`, and
`incident_replay_summary`.

Five-minute validation script: `docs/DEMO_SCRIPT.md`.

Detailed walkthrough: `docs/DEMO_WALKTHROUGH.md`.

Customer call packet: `docs/CUSTOMER_CALL_PACKET.md`.

Adapter enforcement contract: `docs/ADAPTER_ENFORCEMENT_CONTRACT.md`.

Audit conformance schema: `manifests/rclp_audit_conformance_schema.json`.

## Repository Layout

```text
AGENTS.md                         Project-level agent guidance
docs/                             Protocol, doctrine, threat, readiness docs
src/rclp_core/                    Protocol models, policy, leases, crypto, audit
src/rclp_agents/                  Central-agent and edge-agent MVP mocks/demo
src/rclp_ros2/                    ROS 2 command-gate adapter scaffold
crates/rclp-edge-verifier/        Rust edge-side lease verifier spike
examples/                         Policies, scenarios, manifests, audit examples
tests/                            Conformance, behavior, and negative tests
isaac_sim/                        Lambda.ai + Isaac Sim POC plan and scaffold
manifests/                        Protocol manifest and agent manifest examples
agents/                           Local workstream role notes
```

## Protocol Boundary

RCLP is a safety-adjacent authority layer. It is meant to compose with robot
and agent ecosystems, not replace them. RCLP does not replace:

- ROS 2
- VDA5050
- Open-RMF
- MCP
- A2A
- robot fleet managers
- teleoperation systems
- local robot safety controllers

RCLP gates software/agent authority. It does not replace certified robot safety
systems, low-level obstacle avoidance, braking, emergency stop, or formal safety
cases.

## Commercial Boundary

This open repo contains the protocol MVP, reference implementation, tests,
docs, and simulator-oriented proof scaffolding. It excludes hosted trust roots,
customer accounts, billing, managed policy UI, fleet-scale audit backends,
carrier/MVNO integrations, managed connectivity, enterprise SSO/IAM, commercial
SLAs, and proprietary customer workflows.

See `docs/COMMERCIAL_BOUNDARY.md`.

## Readiness

The target state for this repository is controlled technical validation calls:
a skeptical robotics/platform engineer should be able to clone it, understand
the primitive in under one minute, run the demo, inspect the tests, understand
the safety boundary, and see exactly what this MVP does and does not prove.

Release readiness notes: `docs/RELEASE_READINESS.md`.

Validation release notes: `docs/VALIDATION_RELEASE_NOTES.md`.

Conformance checklist: `docs/CONFORMANCE_CHECKLIST.md`.

Rust verifier notes: `docs/RUST_EDGE_VERIFIER.md`.

Protocol evals: `docs/EVALS.md`.

Post-T12 sequence plan: `docs/POST_T12_SEQUENCE_PLAN.md`.

Customer-call readiness checklist:
`docs/CUSTOMER_CALL_READINESS_CHECKLIST.md`.

Technical FAQ: `docs/TECHNICAL_FAQ.md`.

First-call target profile: `docs/FIRST_CALL_TARGET_PROFILE.md`.

Comparison with adjacent protocols: `docs/WHY_NOT_EXISTING_PROTOCOLS.md`.

Next thread map: `docs/NEXT_THREAD_MAP.md`.
