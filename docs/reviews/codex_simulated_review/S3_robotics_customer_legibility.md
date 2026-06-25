# S3 — Robotics Platform / Customer-legibility Review

## Verdict

GREEN for controlled technical validation with robotics platform, autonomy
infrastructure, remote-assist, or fleet reliability teams.

Not green for broad fleet-operator outreach, pilot sales, or production
deployment framing.

## One-sentence interpretation

- RCLP is an open protocol MVP for short-lived, locally enforced authority
  leases that let a central software actor request selected robot capabilities
  while a robot-local edge authority gate allows, denies, degrades, revokes,
  and audits that authority under local context.

## What is clear

- The authority gap is now understandable: many robot stacks already move
  commands, telemetry, missions, media, and tasks, but they do not always make
  the authority boundary explicit for high-authority capabilities.
- The repo mostly sounds like a protocol/reference implementation, not a fleet
  manager, teleop product, safety controller, or hosted platform.
- The README and validation docs now define "agent" as a software actor early,
  which reduces the risk that a reviewer reads it as "LLM chatbot controls a
  robot."
- The distinction from ROS 2, SROS2, VDA5050, Open-RMF, MCP, A2A, fleet
  managers, teleop systems, robot-local safety controllers, and connectivity
  platforms is clear enough for a technical reviewer.
- `docs/STACK_PLACEMENT.md` and
  `docs/INTEGRATION_SKETCH_REMOTE_ASSIST.md` make the stack insertion point
  concrete: RCLP sits before selected high-authority robot-facing commands,
  with local enforcement near the robot gateway or middleware path.
- The demo maps to a recognizable remote-assist workflow: robot uncertainty or
  failed recovery leads to a `remote_assist` authority request; local context
  can allow, degrade, deny, revoke, and audit.
- The validation ask is clear: this is not a buying conversation; it is a call
  to test whether the authority boundary exists, where it would live, which
  capabilities need scoped authority, and what evidence would justify a pilot.

## What is confusing

- The phrase "edge authority service" is clearer than "edge agent," but the
  exact deployable shape is still underspecified. Is it a sidecar, ROS 2 node,
  gateway plugin, fleet-agent component, or library embedded in a robot
  gateway?
- The repo explains what RCLP does not replace, but less clearly explains who
  owns policy in a real organization: fleet ops, safety engineering, autonomy,
  security, site ops, or a customer-specific authority board.
- The demo uses deterministic network profiles, which is acceptable, but a
  fleet reliability lead will immediately ask how observed network state is
  sourced, trusted, debounced, and reconciled against stale robot-local state.
- The "capability" examples are useful, but some are still conceptual. A
  customer will want a precise mapping from each capability to actual command
  topics/actions/API calls in their stack.
- The protocol/reference split is mostly clear, but the Python reference,
  Rust verifier spike, ROS scaffold, and future commercial platform could still
  blur for reviewers who skim quickly.
- The audit story is promising but high level. The repo does not yet show how
  an operator, incident reviewer, or reliability engineer would consume audit
  output inside existing logging/SIEM/incident tooling.
- "Observe-only" is the right adoption path, but the repo does not yet show an
  observe-only integration artifact or sample report from a shadow-mode run.

## Likely customer objections

- "We already enforce authority in our fleet manager, teleop service, IAM, ROS
  permissions, or robot gateway. Why add another gate?"
- "A robot-local gate in the command path could add latency, operational
  fragility, or false denials during incidents."
- "Who writes and owns these policies, and how do they pass safety/security
  review?"
- "How do leases and revocations propagate across intermittent connectivity,
  multiple edge processes, and robot restarts?"
- "What is the source of truth for observed network state, geofence state, and
  mission state?"
- "How does this compose with our existing emergency stop, safety PLC,
  braking, autonomy fallback, and certified safety stack?"
- "Can this run observe-only against our current command stream without
  changing robot behavior?"
- "What evidence distinguishes this from a well-designed teleop permission
  check plus audit logging?"
- "How do we avoid creating a new vendor-neutral standard before proving that
  enough teams share the same authority boundary?"

## Where this fits in a robot stack

- Between central software actors and selected robot-facing command paths.
- Near a robot gateway, edge runtime, ROS 2 bridge, DDS boundary, custom
  command router, or remote-assist command ingress point.
- Beside fleet managers and teleop systems: those systems may request leases,
  but RCLP would decide whether selected capabilities are currently
  authorized.
- Above robot-local autonomy and safety controls: RCLP can deny or revoke
  authority, but local autonomy and safety systems remain responsible for
  physical behavior.
- In audit and incident-review workflows, where the value is reconstructing
  who requested authority, under what context, what was allowed or denied, and
  why authority changed.

## Where this does not fit

- It does not belong in low-level control loops, braking, obstacle avoidance,
  e-stop, safety PLC behavior, perception, or certified safety functions.
- It does not replace ROS 2, DDS, VDA5050, Open-RMF, MCP, A2A, fleet managers,
  teleop session managers, carrier platforms, or network operations tooling.
- It is not a hosted SaaS control plane in this repo.
- It is not a production key-management, attestation, policy lifecycle, or
  fleet-scale audit backend.
- It is not evidence of real cellular behavior, field safety, customer
  willingness to deploy, or production readiness.

## Blocking issues before technical validation calls

- No blocking issue for controlled technical validation calls with friendly or
  high-context robotics platform teams, provided the call is framed narrowly
  around authority-boundary validation.
- For broader outreach, the main blocker is still lack of a one-page
  "show me my stack" mapping for common deployment shapes: ROS 2 robot,
  proprietary robot gateway, teleop service, fleet manager, and autonomy
  module.
- The second blocker for broader outreach is missing observe-only evidence:
  a sample shadow-mode report showing what RCLP would have allowed, denied,
  degraded, and audited without touching robot behavior.
- A third blocker is policy ownership. Before outreach beyond technical
  validators, the docs should say who is expected to define, approve, deploy,
  and review capability policies in a real fleet organization.

## Recommended wording changes

- Prefer: "robot-local edge authority gate" over "edge agent" in customer
  docs unless the sentence immediately defines "agent."
- Prefer: "capability authority request from a fleet service, autonomy module,
  remote-assist service, or operator-session controller" over "central-agent
  request."
- Add a repeated sentence near stack/integration docs: "In observe-only mode,
  RCLP would record allow/deny/degrade decisions without blocking commands."
- Add a concrete policy-ownership sentence: "In a production program, policy
  ownership would likely sit with the team that already owns robot operational
  risk: safety/reliability/autonomy/platform, not with the protocol itself."
- Add a deployment-shape caveat: "The MVP proves the authority primitive; it
  does not yet prescribe whether the edge gate is packaged as a ROS 2 node,
  gateway plugin, sidecar process, or embedded library."
- When describing network inputs, prefer: "observed network state used as an
  authorization input" rather than any phrase that sounds like connectivity or
  QoS assurance.
- For outreach, lead with `remote_assist`, `operator_velocity_control`, and
  `recovery_behavior`; leave `AI agent` and broader autonomy language later so
  operators do not assume this is an LLM control product.
