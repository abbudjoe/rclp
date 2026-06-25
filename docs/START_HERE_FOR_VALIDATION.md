# Start Here for RCLP Validation

## One-sentence definition

RCLP is an open protocol MVP for short-lived, locally enforced capability
leases: central software actors request selected robot capabilities, a
robot-local authority service evaluates policy, and a robot-local authority
gate enforces the result near the command path.

In this repo, "agent" means a software actor. It may be a remote-assist
service, operator-session controller, fleet service, autonomy module, or other
software actor. It does not imply an LLM, chatbot, or fully autonomous fleet
manager.

## What RCLP is trying to validate

RCLP is testing whether robot fleets need a vendor-neutral authority layer for
selected high-authority robot capabilities such as remote assist, operator
velocity control, recovery behavior, temporary speed-envelope
changes, crossing assist, dock recovery, autonomy escalation, or
geofence-sensitive maneuvers.

The protocol asks whether a capability authority request from a central
software actor should be allowed, denied, degraded, revoked, and audited by a
robot-local authority service and enforced by a robot-local authority gate
using identity, mission, geofence, observed network state used as an
authorization input, lease, and fallback constraints.

## Recommended read order

1. `README.md` - overview and quickstart
2. `docs/CUSTOMER_CALL_PACKET.md` - validation framing
3. `docs/STACK_PLACEMENT.md` - where RCLP fits in a robot stack
4. `docs/DEPLOYMENT_SHAPES.md` - common "where does this fit?" mappings
5. `docs/INTEGRATION_SKETCH_REMOTE_ASSIST.md` - concrete `remote_assist` workflow
6. `docs/OBSERVE_ONLY_SAMPLE_REPORT.md` - illustrative shadow-mode evidence format, not generated from field data
7. `docs/POLICY_OWNERSHIP.md` - who defines, approves, deploys, and reviews policy
8. `docs/DEMO_SCRIPT.md` - 5-minute technical demo
9. `docs/SAFETY_BOUNDARY.md` - what RCLP does and does not claim
10. `docs/WHY_NOT_ROS_VDA5050_MCP_A2A.md` - adjacent protocol comparison
11. `docs/EVALS.md` - adversarial eval coverage
12. `docs/COMMERCIAL_BOUNDARY.md` - open protocol vs future commercial platform

## Validation artifact map

- Python reference implementation: protocol behavior, policy, leases, command
  gate, demo, eval harness, and audit replay.
- Rust edge verifier spike: deterministic edge-verifier shape with offline
  vectors; not a replacement for the Python reference.
- ROS 2 command-gate scaffold: adapter direction for robot middleware.
- Eval runner: deterministic local evidence for allow, deny, degrade, revoke,
  and audit paths.
- Future commercial platform: out of this repo.

## What feedback we want

We are not asking whether you would buy this today.

We are asking:

- whether this authority boundary exists in your robot stack
- where this gate would live
- which capabilities would require scoped authority
- whether observe-only mode would be useful
- what evidence would make this worth a pilot
- what existing system this would conflict with or complement

The first validation target is not production enforcement. It is whether an
observe-only or advisory authority layer would produce useful audit, denial,
degradation, or integration evidence in real robot operations.

In observe-only mode, RCLP would record allow/deny/degrade decisions without
blocking commands.

## What feedback we are not seeking yet

- pricing feedback
- procurement feedback
- production safety certification review
- carrier integration feedback
- full commercial-platform requirements
