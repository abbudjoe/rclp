# S3 — Robotics Platform / Customer-legibility Review

## Verdict

GREEN for controlled technical validation with high-context robotics platform,
remote-assist, edge autonomy, or fleet reliability teams.

YELLOW for broader outreach. The repository is understandable enough for a
skeptical technical validation call, but it is not ready to be treated as a
pilot offer, operator-facing product, production integration package, fleet
manager, or safety system.

## One-sentence interpretation

- RCLP is an open protocol MVP for short-lived capability leases: central
  software actors request authority for selected robot capabilities, a
  robot-local authority service evaluates policy and local context, and a
  robot-local authority gate enforces and audits the result near the command
  path.

## What is clear

- The authority gap is now legible: existing robot stacks already move
  missions, commands, telemetry, media, tasks, and tools, while RCLP asks
  whether this actor is currently allowed to exercise this physical capability
  on this robot, in this mission, under current local conditions.
- The repository reads primarily as a protocol and reference implementation.
  It does not read like a fleet manager, teleop product, certified safety
  system, hosted SaaS, carrier platform, or robot controller.
- The authority-service / authority-gate split is clear enough for technical
  reviewers: the service evaluates policy and lease decisions; the gate
  enforces near selected robot-facing command paths.
- The comparison to ROS 2, SROS2, VDA5050, Open-RMF, MCP, A2A, teleop
  systems, fleet managers, robot-local safety controllers, and connectivity
  platforms is much clearer than the baseline. RCLP is positioned as an
  authority layer that composes with those systems rather than replacing them.
- The demo maps to a recognizable remote-assist authority workflow: a central
  service requests `remote_assist`, local context can allow, deny, degrade, or
  revoke authority, and audit replay reconstructs the decision path.
- The validation docs give a robot fleet team a plausible first answer to
  where RCLP would fit: beside a ROS 2 graph, inside or beside a proprietary
  gateway, before a teleop command path, adjacent to a fleet manager, or at an
  autonomy escalation boundary.
- The validation ask is concrete: determine whether the authority boundary
  exists, where the gate would live, which capabilities need scoped authority,
  whether observe-only mode is useful, and what evidence would justify a
  pilot.
- The safety and commercial boundaries are appropriately conservative: no
  certified safety claim, no production robot safety claim, no real cellular
  behavior claim, no production key-management claim, no customer willingness
  claim, and no hosted commercial-platform claim.

## What is confusing

- Customer-facing docs mostly avoid overloaded "agent" language, but the
  normative protocol still uses `central agent` and `edge agent`. The
  terminology note helps, but a reviewer moving quickly between README,
  protocol spec, package names, and code may still have to translate between
  customer-facing and protocol-facing vocabulary.
- The deployment-shape docs explain where RCLP could sit, but they do not yet
  map example capabilities to concrete ROS 2 actions/topics, gateway API
  calls, teleop session transitions, or fleet-manager command objects.
- The observe-only report is clearly labeled illustrative and not generated
  from field data. That is honest, but it also means the audit story is still
  a proposed evidence format rather than evidence from a real command stream.
- Network state is framed correctly as an authorization input, not a network
  guarantee. A fleet reliability lead will still ask who measures it, how it
  is authenticated, how it is debounced, how stale/conflicting observations
  are handled, and which system owns the source of truth.
- Policy ownership is named, but operational lifecycle is still thin:
  approval gates, emergency narrowing, rollout, rollback, incident review,
  policy version ownership, and production change control are not specified.
- The artifact map helps, but the repo still has a lot of surfaces for a
  first-time customer reviewer: Python reference implementation, Rust verifier
  spike, ROS 2 scaffold, eval runner, Isaac Sim scaffold, observe-only report,
  and future commercial-platform boundary.
- The demo is an authority-flow proof, not a robot workflow proof. It does not
  show operator UX, robot timing, command latency, ROS 2 runtime delivery,
  gateway packaging, degraded real-network behavior, or hard-gate operational
  acceptability.

## Likely customer objections

- "We already enforce this in our fleet manager, gateway, IAM layer, teleop
  service, ROS permissions, or operations process. What failure mode does RCLP
  catch that our current controls miss?"
- "A robot-local gate near the command path can add latency, false denials,
  operational fragility, and new incident modes during remote assist."
- "Who owns and approves these policies, and what safety, reliability,
  security, and operations review is required before enforcement?"
- "Where does observed network state come from, and why should this authority
  layer trust it?"
- "How do leases, revocations, replay caches, and policy pins behave across
  partitions, robot restarts, multiple edge processes, and clock skew?"
- "How does this compose with e-stop, braking, safety PLCs, certified safety
  functions, local autonomy fallback, and existing incident procedures?"
- "Can this run observe-only against our current command stream without
  touching robot behavior, and what would the first useful report look like?"
- "What evidence distinguishes this from adding better permission checks and
  audit logging to our existing teleop, gateway, or fleet stack?"
- "Why should this become a vendor-neutral protocol before there is field
  evidence that multiple fleets share the same authority boundary?"

## Where this fits in a robot stack

- Between central software actors and selected high-authority robot-facing
  command paths.
- Near a robot gateway, edge runtime, ROS 2 bridge, DDS boundary, custom
  command router, remote-assist command ingress point, or autonomy escalation
  boundary.
- Beside fleet managers and teleop systems: those systems may request leases,
  but RCLP decides whether selected capabilities are currently authorized
  under local context.
- Above local autonomy and safety controls: RCLP can deny, degrade, revoke, or
  audit software authority, but local autonomy and safety systems remain
  responsible for physical behavior.
- First as observe-only audit, where it mirrors selected command intents and
  records would-allow, would-deny, would-degrade, and would-revoke decisions
  without blocking robot behavior.
- In incident review, where the value is reconstructing who requested
  authority, for which robot and mission, under which local state, and why the
  authority decision changed.

## Where this does not fit

- It does not belong in low-level controls, braking, obstacle avoidance,
  e-stop, safety PLC logic, perception, planning, or certified safety
  functions.
- It does not replace ROS 2, DDS, SROS2, VDA5050, Open-RMF, MCP, A2A, fleet
  managers, teleop systems, carrier platforms, or network operations tooling.
- It is not the hosted commercial platform, managed trust root, managed policy
  UI, fleet-scale audit backend, enterprise IAM integration, billing system,
  managed connectivity layer, or carrier integration.
- It is not production key management, hardware-backed trust, attestation,
  operational policy lifecycle management, or a safety case.
- It is not evidence that customers will deploy, buy, or accept hard command
  gating.

## Blocking issues before technical validation calls

- No blocker for tightly scoped technical validation calls with high-context
  robotics platform, remote-assist, edge autonomy, or fleet reliability teams.
- Do not broaden the audience yet. Operator-facing, sales, pilot,
  procurement, or production-readiness outreach would still outrun the
  evidence.
- State plainly before calls that observe-only evidence is illustrative and
  not generated from real customer command streams.
- For any serious follow-up, pick one concrete customer command path and map
  it to actual ROS 2 actions/topics, gateway API calls, teleop session
  transitions, or fleet-manager commands. The repo does not yet provide that
  adapter-level mapping.
- Be ready to discuss policy lifecycle. The repo identifies likely policy
  owners, but it does not define the operational approval/change process a
  fleet would need before enforcement.
- Be ready to explain the source and trust model for network-state inputs.
  That is likely to come up immediately for remote-assist teams.

## Recommended wording changes

- No blocking wording change is required before controlled technical
  validation calls.
- Keep using "authority service" for policy/lease decisioning and "authority
  gate" for command-path enforcement in customer-facing docs.
- Keep defining "agent" as a software actor before any customer-facing use of
  agent terminology; avoid leading with AI-agent or autonomous-agent framing.
- Keep labeling the observe-only report as illustrative and not generated from
  field data wherever it is linked from the validation path.
- Keep leading outreach language with concrete robotics capabilities such as
  `remote_assist`, `operator_velocity_control`, and `recovery_behavior`; leave
  broader autonomy and AI-agent examples secondary.
- Keep the protocol-spec terminology note near the actor section so reviewers
  understand why the spec still says `central agent` and `edge agent`.
