# S3 — Robotics Platform / Customer-legibility Review

## Verdict

GREEN for controlled technical validation with robotics platform, autonomy
infrastructure, remote-assist, or fleet reliability teams.

YELLOW for broader outreach. The repository is now legible enough to ask a
high-context robotics team for technical feedback, but it is not ready to be
read as a pilot offer, operator-facing product, safety system, or production
integration package.

## One-sentence interpretation

- RCLP is an open protocol MVP for short-lived, locally enforced capability
  leases that let central software actors request selected robot capabilities
  while a robot-local authority gate allows, denies, degrades, revokes, and
  audits that authority under local context.

## What is clear

- The authority gap is understandable: existing robot stacks already move
  missions, commands, telemetry, media, tasks, and tools, while RCLP asks
  whether a specific actor is currently allowed to exercise a specific
  physical capability on a specific robot.
- The repository mostly sounds like a protocol and reference implementation,
  not a fleet manager, teleop system, SaaS product, certified safety system,
  or robot controller.
- The customer-facing docs now define "agent" as a software actor early
  enough that a technical reviewer is less likely to assume "LLM chatbot
  drives robot."
- The distinction from ROS 2, SROS2, VDA5050, Open-RMF, MCP, A2A, fleet
  managers, teleop systems, robot-local safety controllers, and connectivity
  platforms is clear enough for a controlled validation call.
- The demo maps to a recognizable remote-assist workflow: a fleet or
  remote-assist service requests `remote_assist`, local context can allow,
  deny, degrade, or revoke authority, and the audit chain reconstructs the
  decision path.
- `docs/STACK_PLACEMENT.md` and `docs/DEPLOYMENT_SHAPES.md` now give a robot
  fleet team a reasonable first answer to "where would this sit in my stack?"
  across ROS 2, proprietary gateways, teleop services, fleet managers, and
  autonomy modules.
- The validation-call ask is explicit: the repo wants feedback on whether this
  authority boundary exists, where it would live, which capabilities need
  scoped authority, whether observe-only mode is useful, and what evidence
  would justify a pilot.
- The safety and commercial boundaries are appropriately conservative: the
  repo does not claim certified safety, real cellular behavior, production key
  management, customer willingness to deploy, hosted control-plane behavior, or
  fleet management.

## What is confusing

- The customer docs use clearer language, but the normative protocol still
  uses "central agent" and "edge agent." That is probably acceptable for the
  spec, but reviewers who jump between README, spec, and package names may
  still need the "agent means software actor" caveat repeated.
- "Robot-local edge authority service" and "robot-local edge authority gate"
  are both used. The difference between the policy/lease service and the
  command-path gate should be crisp before less technical outreach.
- The deployment-shape mapping is useful but still illustrative. It does not
  map example capabilities to actual ROS 2 actions/topics, gateway API calls,
  teleop session transitions, or fleet-manager command objects.
- The observe-only sample report helps, but it is synthetic. A fleet
  reliability lead will ask for a real shadow-mode trace against recorded
  command streams before treating the audit story as evidence.
- Network state is correctly framed as an authorization input, but the source
  of truth remains open: who measures it, how it is authenticated, how it is
  debounced, and how conflicting robot-local observations are resolved.
- Policy ownership is now named, but the production lifecycle is still only a
  validation discussion: review gates, emergency narrowing, rollout, rollback,
  incident review, and policy version ownership are not operationally
  specified.
- The Python reference implementation, Rust verifier spike, ROS 2 scaffold,
  eval runner, Isaac Sim scaffold, and future commercial platform are separated
  in prose, but a skimming reviewer may still need a short "which artifact is
  authoritative for what?" table.
- The demo is a good authority-flow proof, but it is not yet a robot workflow
  proof. It does not show timing, operator UX, robot command latency, ROS 2
  delivery, gateway deployment, or degraded real-network behavior.

## Likely customer objections

- "We already enforce this in our fleet manager, teleop service, IAM layer,
  ROS permissions, gateway, or operations process. What failure mode does RCLP
  catch that we do not?"
- "A gate near the command path can add latency, false denials, integration
  fragility, and new incident modes during remote assist."
- "Who owns these policies, and what safety, reliability, security, and
  operations review is required before enforcement?"
- "Where does observed network state come from, and why should the authority
  layer trust it?"
- "How do leases, revocations, and replay caches behave across partitions,
  robot restarts, multiple edge processes, and clock skew?"
- "How does this compose with our existing e-stop, braking, safety PLC,
  autonomy fallback, and certified safety stack?"
- "Can it run observe-only against our current command stream without touching
  robot behavior, and what would the first useful report look like?"
- "What evidence distinguishes this from adding better permission checks and
  audit logging to our existing teleop or gateway stack?"
- "Is a vendor-neutral protocol premature before there is field evidence that
  multiple fleets share this exact authority boundary?"

## Where this fits in a robot stack

- Between central software actors and selected robot-facing command paths.
- Near a robot gateway, edge runtime, ROS 2 bridge, DDS boundary, custom
  command router, remote-assist command ingress point, or autonomy escalation
  boundary.
- Beside fleet managers and teleop systems: those systems may request leases,
  but RCLP decides whether selected capabilities are currently authorized under
  local context.
- Above robot-local autonomy and safety controls: RCLP can deny, degrade, or
  revoke software authority, but the local autonomy and safety stack remains
  responsible for physical behavior.
- In observe-only audit first, where it mirrors selected command intents and
  records would-allow, would-deny, would-degrade, and would-revoke decisions
  without blocking robot behavior.
- In incident review, where the value is reconstructing who requested
  authority, for which robot and mission, under what local state, and why the
  authority decision changed.

## Where this does not fit

- It does not belong in low-level control loops, braking, obstacle avoidance,
  e-stop, safety PLC logic, perception, planning, or certified safety
  functions.
- It does not replace ROS 2, DDS, SROS2, VDA5050, Open-RMF, MCP, A2A, fleet
  managers, teleop session managers, carrier platforms, or network operations
  tooling.
- It is not the hosted commercial platform, managed trust root, policy UI,
  fleet-scale audit backend, enterprise IAM integration, billing system, or
  carrier integration.
- It is not production key management, hardware-backed trust, attestation,
  policy lifecycle management, or a field-proven safety case.
- It is not evidence that customers will deploy, buy, or accept hard command
  gating.

## Blocking issues before technical validation calls

- No blocker for tightly scoped technical validation calls with robotics
  platform, autonomy infrastructure, remote-assist, or fleet reliability teams.
  The repo is now clear enough to ask whether the authority primitive is real
  and where it would fit.
- Do not broaden the audience yet. Operator-facing, sales, pilot, or
  production-readiness outreach would still overrun the evidence.
- The main pre-call caveat is that the observe-only report is illustrative, not
  generated from customer telemetry. Say that plainly before a reviewer has to
  discover it.
- The second pre-call caveat is integration specificity: be ready to ask the
  customer for one concrete command path to map, because the repo does not yet
  provide ROS 2 topic/action, gateway API, or teleop-session adapter details.
- The third pre-call caveat is policy lifecycle: the repo identifies likely
  policy owners, but it does not yet define an operational policy change and
  approval process.

## Recommended wording changes

- Prefer "robot-local authority gate" or "robot-local edge authority gate" in
  customer-facing docs; reserve "edge agent" for protocol-spec contexts that
  immediately define the term.
- Use one consistent distinction: "authority service" for policy/lease
  decisioning and "authority gate" for command-path enforcement.
- In outreach, lead with `remote_assist`, `operator_velocity_control`, and
  `recovery_behavior`; move `AI agent` and broader autonomy language later so
  operators do not read this as an LLM-control product.
- Add a short artifact map near the validation entry path: Python reference =
  protocol behavior, Rust verifier = edge-verifier spike, ROS 2 scaffold =
  adapter direction, eval runner = deterministic local evidence, future
  commercial platform = out of repo.
- Label the observe-only sample as "illustrative, not generated from field
  data" anywhere it is linked from a customer packet.
- Keep using "observed network state used as an authorization input"; avoid
  wording that sounds like connectivity assurance, QoS assurance, or carrier
  behavior.
- Fix small wording friction such as "local robot-local edge authority gate" in
  safety docs before sending the packet externally.
