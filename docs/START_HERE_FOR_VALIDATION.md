# Start Here for RCLP Validation

## One-sentence definition

RCLP is an open protocol MVP for short-lived, locally enforced capability
leases between central software actors and robot-local edge authority services.

In this repo, "agent" means a software actor. It may be a fleet service,
autonomy module, remote-assist service, operator-session controller, or AI
agent. It does not imply an LLM, chatbot, or fully autonomous fleet manager.

## What RCLP is trying to validate

RCLP is testing whether robot fleets need a vendor-neutral authority layer for
selected high-authority robot capabilities such as remote assist, autonomy
escalation, recovery behavior, temporary speed-envelope changes, crossing
assist, dock recovery, operator velocity control, or geofence-sensitive
maneuvers.

The protocol asks whether a capability authority request from a central
software actor should be allowed, denied, degraded, revoked, and audited by a
robot-local edge authority service using identity, mission, geofence, observed
network state, lease, and fallback constraints.

## Recommended read order

1. `README.md` - overview and quickstart
2. `docs/CUSTOMER_CALL_PACKET.md` - validation framing
3. `docs/STACK_PLACEMENT.md` - where RCLP fits in a robot stack
4. `docs/INTEGRATION_SKETCH_REMOTE_ASSIST.md` - concrete `remote_assist` workflow
5. `docs/DEMO_SCRIPT.md` - 5-minute technical demo
6. `docs/SAFETY_BOUNDARY.md` - what RCLP does and does not claim
7. `docs/WHY_NOT_ROS_VDA5050_MCP_A2A.md` - adjacent protocol comparison
8. `docs/EVALS.md` - adversarial eval coverage
9. `docs/COMMERCIAL_BOUNDARY.md` - open protocol vs future commercial platform

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

## What feedback we are not seeking yet

- pricing feedback
- procurement feedback
- production safety certification review
- carrier integration feedback
- full commercial-platform requirements
