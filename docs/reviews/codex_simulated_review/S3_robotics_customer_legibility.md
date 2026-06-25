# S3 — Robotics Platform / Customer-legibility Review

## Verdict

GREEN for controlled technical validation with robotics platform,
remote-assist, autonomy infrastructure, or fleet reliability teams.

YELLOW for broader outreach. The repository is understandable enough for a
high-context technical validation call, but it is not ready to be treated as a
pilot offer, operator-facing product, production integration package, fleet
manager, or safety system.

## One-sentence interpretation

- RCLP is an open protocol MVP for short-lived capability leases: a central
  software actor requests authority for a selected robot capability, a
  robot-local authority service evaluates policy and local context, and a
  robot-local authority gate enforces and audits the result near the command
  path.

## What is clear

- The authority gap is now legible: robot stacks already move commands,
  missions, media, telemetry, tasks, and tools, while RCLP asks whether this
  actor is currently allowed to exercise this physical capability on this
  robot, in this mission, under current local conditions.
- The repo reads mostly as a protocol plus reference implementation. It does
  not read like a fleet manager, teleop product, certified safety system,
  hosted SaaS, carrier platform, or robot controller.
- The service/gate split is much clearer than before: the authority service
  evaluates policy and leases; the authority gate enforces near the
  robot-facing command path.
- The distinction from ROS 2, SROS2, VDA5050, Open-RMF, MCP, A2A, teleop
  systems, fleet managers, robot-local safety controllers, and connectivity
  platforms is clear enough for technical reviewers.
- The demo maps to a recognizable remote-assist authority workflow: a service
  requests `remote_assist`, local context can allow, deny, degrade, or revoke,
  and audit replay reconstructs the decision path.
- The validation docs explain where this could sit in ROS 2 robots,
  proprietary robot gateways, teleop services, fleet managers, and autonomy
  modules.
- The validation ask is concrete: determine whether the authority boundary
  exists, where the gate would live, which capabilities need scoped authority,
  whether observe-only mode is useful, and what evidence would justify a
  pilot.
- The repo is appropriately conservative about non-claims: no certified
  safety, no production robot safety, no real cellular behavior, no production
  key management, no customer willingness, and no hosted commercial platform.

## What is confusing

- The current customer-facing language is mostly clear, but the protocol spec
  still uses `central agent` and `edge agent`. That is acceptable as an
  internal protocol model, but a reviewer jumping from README to spec still
  has to hold two vocabularies in their head.
- The docs explain deployment shapes, but they do not yet map capabilities to
  concrete ROS 2 actions/topics, gateway API calls, teleop session transitions,
  or fleet-manager command objects.
- The observe-only sample is correctly labeled illustrative and not generated
  from field data. That also means it is not yet evidence from a real command
  stream.
- Network state is framed correctly as an authorization input, but a fleet
  reliability team will still ask who measures it, how it is authenticated,
  how it is debounced, and how conflicting local observations are resolved.
- Policy ownership is named, but the actual policy lifecycle remains thin:
  approval gates, emergency narrowing, rollout, rollback, incident review, and
  policy version ownership are not operationally specified.
- The artifact map helps, but the Rust verifier, Python reference, ROS 2
  scaffold, eval runner, Isaac Sim scaffold, and future platform still form a
  lot of surface area for a first-time reviewer.
- The demo is an authority-flow proof, not a robot workflow proof. It does not
  show operator UX, robot timing, command latency, ROS 2 runtime delivery,
  gateway packaging, or degraded real-network behavior.

## Likely customer objections

- "We already enforce this in our fleet manager, gateway, IAM layer, teleop
  service, ROS permissions, or operations process. What failure mode does RCLP
  catch that our current controls miss?"
- "A gate near the command path can add latency, false denials, operational
  fragility, and new failure modes during remote assist."
- "Who owns and approves these policies, and what safety, reliability,
  security, and operations review is required before enforcement?"
- "Where does observed network state come from, and why should this authority
  layer trust it?"
- "How do leases, revocations, replay caches, and policy pins behave across
  partitions, robot restarts, multiple edge processes, and clock skew?"
- "How does this compose with e-stop, braking, safety PLCs, certified safety
  functions, local autonomy fallback, and existing incident procedures?"
- "Can it run observe-only against our current command stream without touching
  robot behavior, and what would the first useful report look like?"
- "What evidence distinguishes this from adding better permission checks and
  audit logging to our existing teleop or gateway stack?"
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
- Above local autonomy and safety controls: RCLP can deny, degrade, or revoke
  software authority, but local autonomy and safety systems remain responsible
  for physical behavior.
- First as observe-only audit, where it mirrors selected command intents and
  records would-allow, would-deny, would-degrade, and would-revoke decisions
  without blocking robot behavior.
- In incident review, where the value is reconstructing who requested
  authority, for which robot and mission, under which local state, and why the
  decision changed.

## Where this does not fit

- It does not belong in low-level controls, braking, obstacle avoidance,
  e-stop, safety PLC logic, perception, planning, or certified safety
  functions.
- It does not replace ROS 2, DDS, SROS2, VDA5050, Open-RMF, MCP, A2A, fleet
  managers, teleop systems, carrier platforms, or network operations tooling.
- It is not the hosted commercial platform, managed trust root, managed policy
  UI, fleet-scale audit backend, enterprise IAM integration, billing system,
  or carrier integration.
- It is not production key management, hardware-backed trust, attestation,
  operational policy lifecycle management, or a safety case.
- It is not evidence that customers will deploy, buy, or accept hard command
  gating.

## Blocking issues before technical validation calls

- No blocker for tightly scoped technical validation calls with high-context
  robotics platform, remote-assist, autonomy infrastructure, or fleet
  reliability teams.
- Do not broaden the audience yet. Operator-facing, sales, pilot, or
  production-readiness outreach would still outrun the evidence.
- The main caveat before calls is that observe-only evidence is illustrative,
  not generated from real customer command streams.
- The second caveat is integration specificity: before a serious follow-up,
  pick one concrete command path and map it to actual ROS 2 actions/topics,
  gateway API calls, teleop session transitions, or fleet-manager commands.
- The third caveat is policy lifecycle: the repo identifies likely policy
  owners, but it does not define the operational approval/change process a
  fleet would need before enforcement.

## Recommended wording changes

- No blocking wording change is required before controlled technical
  validation calls.
- Keep using "authority service" for policy/lease decisioning and "authority
  gate" for command-path enforcement in customer-facing docs.
- Keep labeling the observe-only report as illustrative and not generated from
  field data wherever it is linked from the validation path.
- Keep leading outreach language centered on `remote_assist`,
  `operator_velocity_control`, and `recovery_behavior`; keep AI-agent and
  broader autonomy framing secondary.
- Keep the protocol-spec terminology note near the actor section so reviewers
  understand why the spec still says `central agent` and `edge agent`.
