# Technical FAQ

## Q: Is this a robot fleet manager?

No. RCLP does not schedule missions, allocate robots, optimize routes, manage
maps, or provide fleet dashboards. It is a narrow authority/lease layer that can
sit beside a fleet manager.

## Q: Is this a teleoperation system?

No. RCLP does not carry video, joystick input, operator sessions, or teleop
media. It can gate whether a central actor currently has authority to exercise
a capability such as `remote_assist`.

## Q: Is this a safety controller?

No. RCLP is a safety-adjacent authority layer, not a certified safety system.
It can reject unauthorized or stale authority and declare fallback hooks, but
the robot's local safety controller remains responsible for physical safety.

## Q: Is this a replacement for ROS 2, VDA5050, Open-RMF, MCP, or A2A?

No. Those systems move robot messages, missions, interoperability state, tools,
or agent-to-agent communication. RCLP asks whether a specific actor has bounded
current authority to exercise a specific physical capability under current
local conditions.

## Q: Why do leases need to be short-lived?

Short lease lifetimes limit the blast radius of stale state, compromised
central actors, network changes, mission changes, and policy mistakes. A stale
lease should expire quickly instead of remaining a broad standing permission.

## Q: Why does enforcement need to be local?

The robot-local authority gate must be able to reject unsafe, stale, invalid,
unauthorized, or context-mismatched requests even when cloud connectivity is
unavailable. RCLP's command gate is designed so high-authority actions fail
closed near the robot when required inputs are missing or invalid.

## Q: Why does network state matter?

Remote assist and autonomy escalation can depend on latency, packet loss,
uplink quality, and partition state. RCLP treats network state as an explicit
authorization input so authority can degrade, deny, or revoke when the current
network profile no longer satisfies policy.

## Q: What happens during cloud partition?

The MVP models partition as deterministic local network state. New authority is
denied when the network is detached, and command-gate enforcement uses local
state and cached policy/lease data to fail closed. The MVP does not claim real
cellular, cloud connectivity, or QoS behavior.

## Q: How does Rust relate to Python?

Python is the MVP reference implementation for protocol iteration, policy
behavior, the demo, the eval harness, and audit replay. The Rust crate is an
edge verifier spike that exercises deterministic offline vectors and explores a
hardened robot-local verifier shape.

## Q: Is this production ready?

No. `v0.1-validation` is suitable for controlled technical validation calls,
not production robot deployments. Production work would require hardened key
management, operational replay/revocation storage, field integration,
monitoring, safety analysis, and organization-specific policy governance.

## Q: What would a commercial platform add later?

A separate commercial platform could add managed trust roots, policy lifecycle
management, customer accounts, billing, hosted audit/replay, fleet-scale
storage, enterprise IAM/SSO, integrations, SLAs, and managed network/carrier
adapters. Those are intentionally outside this open protocol MVP repo.

## Q: Does RCLP require Isaac Sim, ROS 2, cloud, or robot hardware?

No. The validation release is locally runnable with Python, and optionally
Rust. Isaac Sim and ROS 2 are later integration paths, not prerequisites for
the validation package.

## Q: What should reviewers inspect first?

Start with `README.md`, `docs/VALIDATION_RELEASE_NOTES.md`,
`docs/DEMO_WALKTHROUGH.md`, `docs/EVALS.md`, `docs/SAFETY_BOUNDARY.md`, and
`docs/COMMERCIAL_BOUNDARY.md`. Then run `./scripts/run_validation_checks.sh`
and `./scripts/run_validation_demo.sh`.
