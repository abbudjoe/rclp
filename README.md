# RCLP

RCLP is an open protocol MVP for short-lived, locally enforced capability
leases: central software actors request selected robot capabilities, a
robot-local authority service evaluates policy, and a robot-local authority
gate enforces the result near the command path.

In this repo, "agent" means a software actor. It may be a remote-assist
service, operator-session controller, fleet service, autonomy module, or other
software actor. It does not imply an LLM, chatbot, or fully autonomous fleet
manager.

The Robot Capability Lease Protocol focuses on a narrow authority gap:
existing robot, fleet, network, and agent protocols move commands, state,
tools, or missions, while RCLP asks whether authority may pass from a central
software actor to a robot-local authority service and gate for a physical
capability under current conditions.

This repository is the open reference implementation for that primitive. It is
not the future hosted commercial platform.

## What This MVP Demonstrates

- capability authority requests from central software actors such as
  remote-assist services, operator-session controllers, fleet services, and
  autonomy modules
- robot-local authority service policy and lease verification
- signed short-lived leases
- explicit MVP signature algorithm metadata
- allow, deny, degrade, and revoke decisions
- network-state-conditioned authority
- optional control-plane-reachability-conditioned authority
- geofence-conditioned authority
- robot-local authority gate command enforcement before a robot-facing command
  path
- audit JSONL and replay of the authority chain
- signed local audit batches for validation evidence
- audit conformance schema for the MVP authority chain
- Python reference implementation
- Rust edge verifier spike

The local proof uses deterministic fixtures and local non-production keys. The
main flow is:

```text
central software actor requests authority
-> robot-local authority service verifies local context and policy
-> lease is granted, denied, degraded, or revoked
-> robot-local authority gate enforces the lease locally
-> audit replay reconstructs the event chain
```

## Example Gated Capabilities

- `remote_assist`: allow a remote operator or central service to influence robot behavior
- `operator_velocity_control`: allow a remote-assist service or operator-session controller to send bounded velocity commands
- `recovery_behavior`: allow a robot to execute a bounded recovery maneuver after getting stuck
- `autonomy_escalation`: allow a software actor to move from advisory mode to command-producing mode
- `temporary_speed_envelope`: allow a higher speed limit for a bounded mission segment under local constraints
- `geofence_sensitive_maneuver`: allow a robot to perform an action that is valid only inside a specific zone
- `crossing_assist`: allow bounded assistance for a crossing or right-of-way-sensitive maneuver
- `dock_recovery`: allow bounded recovery behavior around docking or undocking

## What This MVP Does Not Demonstrate

- formal safety certification
- production robot safety
- real cellular behavior
- carrier API behavior
- production cryptographic trust infrastructure
- customer willingness to deploy
- full robot hardware integration
- ROS 2 runtime delivery or Isaac Sim execution
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
python -m pytest
python tests/evals/eval_runner.py
python scripts/run_cross_language_conformance.py
python -m rclp_agents.demo_remote_assist
```

If your shell does not expose venv console scripts or you prefer not to rely on
activation, use the venv-qualified equivalents:

```bash
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest
.venv/bin/python tests/evals/eval_runner.py
.venv/bin/python -m rclp_agents.demo_remote_assist
```

`pytest` is also valid after the venv is activated; `python -m pytest` is the
more shell-independent form.

For the packaged validation path:

Run the editable dev install above first; `run_validation_checks.sh` treats
Ruff as part of the local validation gate.

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

The Rust crate is an edge-verifier spike with offline vectors and test-only
`RCLP-DEV-HMAC-SHA256`, not production cryptographic infrastructure. The ROS 2
and Isaac Sim surfaces in this repo are scaffolds and proof plans; the local
validation path does not require ROS 2, Isaac Sim, cloud credentials, or paid
compute.

## Validation Release

`v0.1-validation` is the controlled technical validation package for the MVP.
It is intended for robotics/platform/fleet-operator calls, not production robot
deployments.

## External Validation Path

For controlled technical validation, start here:

- `docs/START_HERE_FOR_VALIDATION.md`

Related validation docs:

- `docs/CONTROLLED_REVIEW_PACKET.md`
- `docs/VALIDATION_RELEASE_NOTES.md`
- `docs/CUSTOMER_CALL_PACKET.md`
- `docs/STACK_PLACEMENT.md`
- `docs/DEPLOYMENT_SHAPES.md`
- `docs/INTEGRATION_SKETCH_REMOTE_ASSIST.md`
- `docs/OBSERVE_ONLY_SAMPLE_REPORT.md` (illustrative sample; not generated
  from field data)
- `docs/POLICY_OWNERSHIP.md`
- `docs/DEMO_WALKTHROUGH.md`
- `docs/EVALS.md`
- `docs/SAFETY_BOUNDARY.md`
- `docs/WHY_NOT_ROS_VDA5050_MCP_A2A.md`
- `docs/WHY_NOT_EXISTING_PROTOCOLS.md`

Run:

```bash
./scripts/run_validation_checks.sh
./scripts/run_validation_demo.sh
```

Artifact map for validation:

- Python reference implementation: protocol behavior, policy, leases, command
  gate, demo, eval harness, and audit replay.
- Rust edge verifier spike: deterministic edge-verifier shape with offline
  vectors; not a replacement for the Python reference.
- ROS 2 command-gate scaffold: adapter direction for robot middleware.
- Eval runner: deterministic local evidence for allow, deny, degrade, revoke,
  and audit paths.
- Future commercial platform: out of this repo.

## Demo Path

`python -m rclp_agents.demo_remote_assist` runs a complete local
`remote_assist` authority negotiation:

1. Creates local central software actor, authority service, robot-local
   authority gate, robot, mission, geofence, policy, and non-production key
   fixtures.
2. Signs a `CapabilityRequest`.
3. Allows a short-lived lease under the normal deterministic network profile.
4. Accepts a matching command through the command gate.
5. Rejects a command with no lease.
6. Applies an impaired network profile and returns degrade or deny.
7. Revokes the previous lease and rejects later command use.
8. Prints `audit_jsonl` and `incident_replay_summary`.

The important result is not robot motion; it is local rejection, revocation,
and auditability of selected robot authority.

Expected stable markers include `POLICY_SATISFIED`, `NO_LEASE`,
`NETWORK_LATENCY_DEGRADED` for the default impaired profile,
`NETWORK_UPLINK_TOO_LOW` for `--network-profile uplink_bad`,
`NETWORK_PROFILE_REVOKE`, `LEASE_REVOKED`, `audit_jsonl`, and
`incident_replay_summary`.

For a live review, point at these demo sections and markers:

| Demo section | What it proves | Expected marker |
|---|---|---|
| `normal_network_decision` | normal local context allows a scoped lease | `POLICY_SATISFIED` |
| `command_gate_with_valid_lease` | command gate accepts only a matching valid lease | `LEASE_VALID` |
| `command_without_valid_lease` | high-authority command without a lease fails closed | `NO_LEASE` |
| `impaired_network_decision` | network-state-aware authorization degrades or denies | `NETWORK_LATENCY_DEGRADED` or `NETWORK_UPLINK_TOO_LOW` |
| `lease_revocation` | degraded local context can revoke prior authority | `NETWORK_PROFILE_REVOKE` |
| `command_gate_after_network_revocation` | revoked authority cannot be reused | `LEASE_REVOKED` |
| `audit_jsonl` | authority-changing events are emitted as audit commits | `audit_jsonl` |
| `incident_replay_summary` | audit replay reconstructs the authority chain | `incident_replay_summary` |

Five-minute validation script: `docs/DEMO_SCRIPT.md`.

Detailed walkthrough: `docs/DEMO_WALKTHROUGH.md`.

Customer call packet: `docs/CUSTOMER_CALL_PACKET.md`.

Adapter enforcement contract: `docs/ADAPTER_ENFORCEMENT_CONTRACT.md`.

Audit conformance schema: `manifests/rclp_audit_conformance_schema.json`.

Development crypto profiles: `docs/CRYPTO_PROFILES.md`.

Deployment-shape mapping: `docs/DEPLOYMENT_SHAPES.md`.

Observe-only illustrative sample, not generated from field data:
`docs/OBSERVE_ONLY_SAMPLE_REPORT.md`.

Policy ownership guidance: `docs/POLICY_OWNERSHIP.md`.

## Repository Layout

```text
AGENTS.md                         Project-level agent guidance
docs/                             Protocol, doctrine, threat, readiness docs
src/rclp_core/                    Protocol models, policy, leases, crypto, audit
src/rclp_agents/                  Central actor and robot-local authority MVP mocks/demo
src/rclp_ros2/                    ROS 2 command-gate adapter scaffold
crates/rclp-edge-verifier/        Rust edge lease verifier spike
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

Reviewer boundary checklist for future docs and examples:

- Rust edge verifier status stays a spike with offline vectors and test-only
  `RCLP-DEV-HMAC-SHA256`, not production cryptographic infrastructure.
- ROS 2 and Isaac Sim content stays scaffold/proof-plan language unless a
  runnable integration and matching tests are added.
- Hosted trust roots, managed policy UI, enterprise accounts, carrier/MVNO
  integrations, and SLAs stay out of this open protocol repo.
- Claims stay scoped to controlled technical validation, local deterministic
  proof, and safety-adjacent authority behavior.

Release readiness notes: `docs/RELEASE_READINESS.md`.

Controlled review packet: `docs/CONTROLLED_REVIEW_PACKET.md`.

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

Validation-facing adjacent protocol table:
`docs/WHY_NOT_ROS_VDA5050_MCP_A2A.md`.

Next thread map: `docs/NEXT_THREAD_MAP.md`.
