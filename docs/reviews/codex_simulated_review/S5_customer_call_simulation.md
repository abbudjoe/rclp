# S5 — Customer-call Simulation Panel

## Overall read

- RCLP is most credible when framed as an authority primitive around remote assist, autonomy escalation, revocation, and incident replay. It is least credible when it sounds like a new fleet manager, safety system, teleoperation stack, or commercial control plane.
- The strongest simulated signal comes from operators with outdoor or campus fleets that already have remote assist, network uncertainty, geofences, and painful post-incident reconstruction. They can imagine observe-only mode quickly because it does not threaten the live command path.
- The hardest objection is not "does this work technically?" It is "why is this not just one more feature in our existing fleet platform?" Mature teams often already have role-based permissions, command validators, network health gates, and logs. RCLP must prove it adds a clearer contract across central agents, edge agents, policy, and audit.
- Enforcement mode is a later conversation. A credible first ask is shadowing past or live events, producing authority timelines, and comparing RCLP decisions against existing operator decisions without blocking commands.
- The MVP proof is useful but narrow. It proves deterministic fail-closed authority behavior under simulated profiles; it does not prove field safety, real cellular behavior, production key management, low false-denial rates, or willingness to deploy.
- Budget ownership is fragmented. Operations feels the pain, platform engineering owns the integration, safety/compliance can block enforcement, and a VP-level sponsor is usually needed if this moves beyond observe-only validation.

## Persona 1 — Sidewalk/campus delivery robot operations

- What do they already have?
  - A central fleet manager, operator console, remote assist or teleop queue, geofencing, mission state, robot-local autonomy and safety controllers, cellular/Wi-Fi monitoring, role-based operator permissions, and incident logs.
  - Some command gating probably already exists, but it is likely embedded in proprietary fleet logic rather than expressed as a reusable lease contract.
- What pain might resonate?
  - Remote assist under degraded connectivity, operator handoff after autonomy stalls, proving who or what had authority during curb crossings or campus interactions, and revoking central authority when geofence or network state changes.
  - The phrase that will land: "Can you reconstruct why this robot accepted or rejected remote assist under the exact network and mission conditions?"
- What would they object to?
  - "We already gate commands in our fleet stack."
  - "A new edge gate could block an operator during the one moment we need intervention."
  - "Network thresholds are not stable enough to make hard authorization decisions."
  - "Open protocol is nice, but our problem is uptime and incident load this quarter."
  - "Who maintains the policy when operations changes procedures?"
- Which part of RCLP is valuable?
  - Observe-only audit replay, scoped short-lived leases for remote assist, local rejection of stale or mismatched authority, network-state-aware authorization, and revocation tied to local conditions.
- Which part sounds unnecessary?
  - Broad agent-protocol framing, future MCP/A2A adapters, any hosted platform discussion, and generic lease theory if not tied to the remote-assist queue.
- Would they run observe-only mode?
  - Yes, if it can ingest fleet events without touching the command path and produce useful incident timelines within days.
- Would they allow enforcement mode later?
  - Possibly. Start with soft gating on non-critical capabilities or a subset of remote-assist actions. Hard gating would require shadow-mode evidence, override semantics, and an operational runbook for false denials.
- Who would own the budget?
  - Robot operations or fleet reliability would sponsor. Platform engineering would own integration. Safety/legal may approve the boundary. Final budget likely sits with VP Operations, Head of Autonomy, or a platform infrastructure owner.
- What proof would they require?
  - Replay of several real or sanitized incidents, false allow/false deny analysis in shadow mode, latency overhead at the edge gate, integration path into their operator console and robot-local runtime, and evidence that revocation survives process restart.
- Signal strength: strong

First 15 minutes of a call:

- Founder opening
  - "RCLP is an open protocol MVP for short-lived capability leases between a central fleet actor and a robot-local edge actor. We are not replacing your fleet manager or safety stack. We are testing whether the authority boundary around remote assist, network state, geofence state, revocation, and audit should be explicit."
- Customer reaction
  - "The audit and revocation angle is interesting. We already have a lot of this in our stack, but it is spread across operator permissions, fleet state, and robot code."
- Customer questions
  - "Where exactly does the edge gate sit?"
  - "Does it block remote assist if LTE gets bad?"
  - "Can operators override it?"
  - "How does this avoid creating a new source of mission failures?"
  - "Can it ingest our existing logs first?"
- Founder clarifying questions
  - "Which remote-assist actions are high-authority enough that they should require local authorization?"
  - "When network state degrades today, do you revoke operator authority, downgrade capability, or rely on operator judgment?"
  - "After an incident, can you reconstruct operator identity, robot state, mission, geofence, network, policy, and command decision in one chain?"
  - "Where would a robot-local verifier naturally live in your stack?"
- Likely objections
  - They will resist any first-step enforcement. They will also push back on network gating if it sounds like RCLP is claiming network guarantees.
  - They may see RCLP as useful only if it reduces incident-review labor or prevents a known class of bad remote-assist events.
- Best follow-up ask
  - Ask for one sanitized remote-assist incident timeline and one normal remote-assist session. Offer to map both into observe-only RCLP decisions and identify where the authority contract is missing or already solved.

## Persona 2 — Outdoor inspection robot teleoperation/fleet reliability

- What do they already have?
  - Teleoperation stack, video/control links, health monitoring, watchdogs, mission supervisor, field connectivity profiles, autonomy fallback procedures, field logs, and operator escalation workflows.
  - They may already have link-quality gates, but those gates are often operational heuristics rather than signed capability leases with replayable authority state.
- What pain might resonate?
  - Lossy outdoor networks, remote operator takeover during inspection anomalies, disagreement between autonomy state and operator console state, and incident review after commands were sent near link-quality limits.
  - RCLP can resonate if positioned as "prove the robot-local runtime had enough fresh authority to accept this command," not as a replacement for teleop media or robot safety.
- What would they object to?
  - "We already know whether the link is good enough from our teleop system."
  - "Video quality, latency spikes, and operator control quality are richer than your simple network model."
  - "A signed lease does not help if the robot is in mud, rain, or RF shadow."
  - "Do not add latency or another daemon that can fail in the field."
  - "Our field team will not debug a protocol during an inspection job."
- Which part of RCLP is valuable?
  - Network-state-aware authorization, local lease validation without cloud availability, command rejection on stale or revoked authority, fallback hook declarations, and audit replay that ties request, state, decision, enforcement, and revocation together.
- Which part sounds unnecessary?
  - Hosted-platform boundary discussion, standards-language before a working adapter, and any focus on low-level robot safety.
- Would they run observe-only mode?
  - Yes, especially if it can shadow teleop sessions and flag where their existing system would have allowed remote assist under stale, degraded, or contradictory state.
- Would they allow enforcement mode later?
  - Yes, but narrowly. They might allow hard gating for selected remote-assist actions only after weeks of shadow-mode comparison and a field-runbook for denial reason codes.
- Who would own the budget?
  - Fleet reliability or teleoperation leadership would own pain and pilot budget. Platform infrastructure owns implementation. Operations signs off if the tool reduces incident load or failed missions.
- What proof would they require?
  - Network fault-injection results against their thresholds, edge-gate latency under field hardware constraints, no dependency on cloud reachability for cached policy decisions, signed-state handling, replay across process restart, and useful incident timelines from real logs.
- Signal strength: strong

First 15 minutes of a call:

- Founder opening
  - "We are testing a narrow primitive: before a remote operator or central agent can exercise a physical capability, the robot-local edge path verifies a short-lived lease against current mission, robot, network, geofence, and fallback policy. The MVP is deterministic and local; it is not a teleop stack."
- Customer reaction
  - "The network-conditioned authority part is relevant. We already have link metrics, but they are not cleanly tied to permissioning and post-incident replay."
- Customer questions
  - "Can you consume our link-quality metrics instead of defining new ones?"
  - "How does it behave during a partition?"
  - "What happens when the operator is already in control and the link degrades?"
  - "Can denial reason codes show up in our operator console?"
  - "What hardware footprint does the edge verifier need?"
- Founder clarifying questions
  - "Which remote-assist commands should fail closed when state is unknown?"
  - "Do you distinguish degrade from deny today, or is that handled manually?"
  - "How do you revoke a takeover session when local state changes?"
  - "What incident evidence is missing from your current logs?"
- Likely objections
  - They will challenge whether the MVP's deterministic network profiles are too simple for field behavior.
  - They will worry that enforcement could strand robots or prevent recovery commands.
  - They may reject any integration that does not fit their existing teleop and logging stack.
- Best follow-up ask
  - Ask them to provide their existing remote-assist link thresholds and a few anonymized session logs. Offer a shadow-mode comparison that classifies allow, degrade, deny, and revoke decisions without touching live control.

## Persona 3 — Construction/surveying robotics platform engineer

- What do they already have?
  - ROS 2 or proprietary robot runtime, mission planner, survey task model, jobsite maps, geofences or exclusion zones, operator tablet or cloud console, autonomy modules, logs, and integration glue for customer workflows.
  - They likely have robot-local safety controls and may have simple command authorization, but less formal authority leasing across central agents, edge runtime, and audit.
- What pain might resonate?
  - Jobsite boundaries change, survey missions are scoped, subcontractors or customer operators may have limited authority, connectivity is intermittent, and post-job audit matters when a robot crossed into the wrong area or executed the wrong mission segment.
  - RCLP may help express "this actor can run this capability for this mission and geofence, for this short time, under local state."
- What would they object to?
  - "Our fleet is small enough that this is overkill."
  - "Construction sites expect intermittent connectivity; network denial could be too conservative."
  - "The hard part is maps, mission semantics, and customer workflow, not generic leases."
  - "A ROS 2 scaffold is not enough. Show me where this sits in actions, topics, and lifecycle nodes."
  - "Policy ownership will become another configuration problem."
- Which part of RCLP is valuable?
  - Scoped mission/capability leases, geofence-conditioned authority, edge-local command gating, explicit policy digest, and audit replay for customer or insurer questions.
- Which part sounds unnecessary?
  - Remote-assist-centered network examples if their primary pain is mission or geofence scope; commercial-platform exclusions; broad AI-agent language.
- Would they run observe-only mode?
  - Yes, if it can map to ROS 2 or their proprietary command path with little disruption and show jobsite authority timelines.
- Would they allow enforcement mode later?
  - Maybe. More likely for selected capabilities such as remote assist, mission start, restricted-zone entry, high-speed traversal, or payload operation than for the entire command path.
- Who would own the budget?
  - Platform engineering or autonomy infrastructure if it reduces integration risk. Product or customer success may sponsor if enterprise customers ask for auditability. Operations alone probably will not buy it.
- What proof would they require?
  - ROS 2 adapter demonstration, geofence and mission-state mapping, configurable policy bounds, low-latency local validation, no cloud dependency, and a customer-readable audit report from a simulated or real jobsite run.
- Signal strength: medium

First 15 minutes of a call:

- Founder opening
  - "RCLP is not a construction robot workflow system. It is a small authority layer for asking whether a software actor may exercise one physical capability on one robot for one mission under current local conditions."
- Customer reaction
  - "I can see it around restricted operations, but the generic protocol may not understand our mission semantics."
- Customer questions
  - "How do capabilities map to ROS 2 actions or services?"
  - "Can leases include jobsite zones and customer-specific policy?"
  - "Does the edge verifier need to understand our maps?"
  - "How do policy digests get updated between jobs?"
  - "Can this be a library instead of a daemon?"
- Founder clarifying questions
  - "Which commands would you never want a central service to send without robot-local confirmation?"
  - "Do you currently bind operator or module identity to mission, geofence, and time?"
  - "Who reviews incident logs when a robot does something unexpected on site?"
  - "Would a shadow audit of mission start, restricted-zone entry, and remote assist be useful?"
- Likely objections
  - They will say the value depends on domain-specific policy schemas that the MVP does not yet have.
  - They may prefer adding signed command checks inside their existing ROS 2/proprietary runtime.
  - They will not tolerate a protocol that expands into fleet scheduling or jobsite management.
- Best follow-up ask
  - Ask for one high-authority construction/survey capability and its current preconditions. Offer to encode only that authority decision as a lease profile and produce a minimal observe-only audit trace.

## Persona 4 — Hospital/enterprise service robot safety/compliance

- What do they already have?
  - Vendor fleet manager, enterprise IAM or operator roles, change-control process, incident reporting, facility approvals, indoor Wi-Fi monitoring, robot-local safety controllers, and vendor-provided logs.
  - They may have procurement and compliance requirements that make edge-runtime changes slow or impossible without vendor sponsorship.
- What pain might resonate?
  - Auditability, least privilege for remote support, proving local rejection of stale or unauthorized commands, and clearer incident timelines when a robot operates near staff, patients, visitors, elevators, or restricted areas.
  - The compliance-friendly part is explicit authority and audit, not safety claims.
- What would they object to?
  - "If it is not certified safety behavior, do not sell it as safety."
  - "We cannot insert unvalidated open-source code into a vendor robot control path."
  - "Our risks are facility workflow, privacy, uptime, and vendor accountability."
  - "Network-state-aware authorization is less compelling on managed indoor Wi-Fi."
  - "We need procurement, cybersecurity, and vendor support before any enforcement discussion."
- Which part of RCLP is valuable?
  - Audit replay, least-privilege authority, short-lived support leases, local rejection of unauthorized commands, and explicit fallback hook declarations for incident records.
- Which part sounds unnecessary?
  - Outdoor network-degradation emphasis, AI-agent framing, low-level protocol details during a compliance-first call, and any suggestion that RCLP replaces a vendor safety case.
- Would they run observe-only mode?
  - Possibly, if it is log-only, vendor-approved, and helps incident review without collecting sensitive operational data beyond what is necessary.
- Would they allow enforcement mode later?
  - Unlikely in the near term unless the robot vendor integrates it and it passes cybersecurity, validation, and change-control review.
- Who would own the budget?
  - Safety/compliance can sponsor evaluation, but IT/security, facilities operations, procurement, and the robot vendor control adoption. Budget may sit under facilities automation, enterprise robotics, or vendor support rather than a protocol line item.
- What proof would they require?
  - Vendor integration path, cyber risk assessment, data-minimization story, audit retention controls, hazard-analysis alignment, fail-closed behavior for high-authority actions, and clear evidence that RCLP is a safety-adjacent authority layer rather than a certified safety system.
- Signal strength: weak

First 15 minutes of a call:

- Founder opening
  - "RCLP is a safety-adjacent authority layer. It does not replace certified robot safety systems. The question we are validating is whether short-lived, auditable authority leases help govern remote support, autonomy escalation, or other high-authority software actions."
- Customer reaction
  - "The distinction helps, but our first concern is vendor responsibility and compliance. We cannot add anything to the control path casually."
- Customer questions
  - "Is this certified?"
  - "Does it collect patient, staff, or facility data?"
  - "Which vendor robots support it?"
  - "Can it run only as an audit layer?"
  - "Who signs off when RCLP denies a support action?"
- Founder clarifying questions
  - "Where do remote-support permissions live today?"
  - "What evidence is missing after a robot-related incident?"
  - "Do you need to prove that commands were locally rejected when support authority was stale or unauthorized?"
  - "Would a vendor-run observe-only pilot be acceptable?"
- Likely objections
  - They will reject enforcement without vendor backing and formal validation.
  - They may view the project as too early because the MVP excludes production key management, enterprise IAM, hosted audit retention, and commercial SLAs.
  - They will punish any wording that implies certified safety.
- Best follow-up ask
  - Ask for a compliance-oriented review of the safety boundary and audit model, not a deployment. The best near-term validation is whether their incident-review process recognizes the authority chain as useful.

## Persona 5 — Mature robot fleet platform engineer

- What do they already have?
  - A mature fleet platform with central services, edge agents, role-based permissions, command validators, policy engines, signed or authenticated command channels, telemetry, audit logs, deployment infrastructure, simulator coverage, customer accounts, and support tooling.
  - They likely think in terms of internal platform primitives, not standalone protocols.
- What pain might resonate?
  - Third-party agents and customer integrations are increasing the number of software actors that can request physical actions. A common lease/audit vocabulary could reduce bespoke integrations and make external authority review easier.
  - They may value RCLP as a conformance profile or interoperability spec more than as a product.
- What would they object to?
  - "This is a feature in our fleet manager."
  - "Your MVP does not capture our operational nuance, deployment model, or customer-specific policies."
  - "We already have signed commands, edge policy, and audit."
  - "A protocol without ecosystem adoption is more maintenance surface."
  - "An open protocol could commoditize a platform capability we already sell."
- Which part of RCLP is valuable?
  - The explicit authority question, conformance tests, fail-closed negative cases, audit-chain language, edge verifier spike, and potential standard vocabulary for third-party agent access.
- Which part sounds unnecessary?
  - Basic remote-assist demo, commercial platform roadmap, and any sales framing that implies they need a new control plane.
- Would they run observe-only mode?
  - Maybe, but more as a standards evaluation or internal comparison than a deployment pilot.
- Would they allow enforcement mode later?
  - Unlikely unless major customers demand RCLP compatibility, regulators/auditors recognize the pattern, or RCLP becomes a useful adapter boundary for third-party agents.
- Who would own the budget?
  - Platform architecture, security architecture, standards/partnerships, or product strategy. It may have no clear budget unless tied to customer integration revenue or risk reduction.
- What proof would they require?
  - Formalized spec stability, conformance suite quality, adapters for ROS 2/VDA5050/Open-RMF or their proprietary equivalent, security review, multiple external adopters, and evidence that RCLP adds something beyond their existing permission and audit model.
- Signal strength: weak

First 15 minutes of a call:

- Founder opening
  - "We expect mature platforms may already have pieces of this. The validation question is whether an explicit central-agent to edge-agent capability lease protocol is useful as an external contract, conformance target, or third-party integration boundary."
- Customer reaction
  - "Conceptually reasonable, but this looks like part of a fleet platform. We would need to see why it should be a protocol rather than our internal policy API."
- Customer questions
  - "What does RCLP do that signed commands plus policy engine plus audit do not?"
  - "Who else is adopting it?"
  - "How stable is the schema?"
  - "Can we map it to our existing command validators?"
  - "Does it handle multi-robot missions and customer tenancy?"
- Founder clarifying questions
  - "Where do third-party software actors request physical authority in your stack?"
  - "Do customers ask for a portable audit chain across agent, fleet, edge, policy, and robot state?"
  - "Which part of this would you reject as too platform-specific?"
  - "Would conformance tests for fail-closed edge authority be useful even if you never run our reference implementation?"
- Likely objections
  - They will see RCLP as technically obvious but commercially weak without ecosystem pull.
  - They may resist anything that looks like a competing platform or a lowest-common-denominator standard.
  - They will challenge the lack of production trust infrastructure and multi-tenant policy management.
- Best follow-up ask
  - Ask for a gap review, not a pilot: have them mark which RCLP fields and negative tests are redundant, missing, or incompatible with their internal authority model.

## Strongest customer segment

- Outdoor inspection and sidewalk/campus delivery fleets are the strongest targets. They combine remote assist, local edge runtime, degraded network conditions, geofence/mission context, operator escalation, and incident-review pain.
- The best first calls should be with teams that can provide real session logs or incident timelines. A call that ends with "we can give you logs to shadow" is much stronger than "interesting standard."
- The strongest wedge is observe-only authority replay for remote assist. It is easy to understand, does not require trust in enforcement, and can reveal whether the missing primitive is real.

## Weakest customer segment

- Hospital/enterprise service robots are weak for near-term MVP validation because compliance, vendor control, procurement, and safety-boundary sensitivity slow everything down.
- Mature fleet platform vendors are weak as buyers because they can build or already have much of this. They are still valuable as skeptical reviewers of the protocol contract and conformance tests.
- Any customer with no remote assist, no edge runtime, no high-authority command boundary, or no incident-reconstruction pain is likely a poor first target.

## Best validation questions

- "Where does authority currently live between central fleet software, operators, autonomy modules, and robot-local execution?"
- "Which physical capabilities would you never want a central actor to exercise without local verification?"
- "Do you condition remote assist or autonomy escalation on network, geofence, mission, or robot-local state today?"
- "When context changes mid-session, how do you revoke authority?"
- "After an incident, can you reconstruct actor identity, command, robot state, mission, geofence, network state, policy, decision, revocation, and fallback hook in one causal chain?"
- "Would observe-only RCLP decisions over your existing logs produce useful disagreement cases?"
- "What false-deny rate would make enforcement unacceptable?"
- "Which denial reason codes would operators need to see?"
- "Who owns policy definitions, fallback hooks, and incident replay in your organization?"
- "What exact proof would make this worth a second technical session?"

## Questions to avoid

- "Would you buy this?" Too early and too easy to answer politely.
- "Do you care about robot safety?" This invites vague agreement and risks overstating the safety boundary.
- "Should this be a standard?" Most customers cannot answer until the integration pain is concrete.
- "Would you replace your fleet manager with this?" RCLP should not be framed as a fleet manager.
- "Do you want a hosted platform?" That jumps past the open MVP and muddies the commercial boundary.
- "Is network quality important?" Everyone says yes. Ask how network state changes authority instead.
- "Would hard enforcement be useful?" Ask first about observe-only disagreement, false denials, and selected capabilities.
- "Can we deploy on a robot?" Too soon for most calls. Ask for logs, thresholds, or a simulator path first.

## Recommended call framing

- Open with the narrow authority question: "Who is allowed to make this robot do this physical thing, right now, under current local conditions?"
- Say explicitly that RCLP is not a fleet manager, teleoperation system, certified safety system, low-level safety controller, or production trust infrastructure.
- Show the demo only as a deterministic sim proof of the authority contract: allow, no lease, degraded network, revocation, command rejection, and audit replay.
- Ask for disconfirmation early: "Where is this already solved in your stack, and what would make this protocol unnecessary?"
- Lead with observe-only mode. The first validation target is shadow audit over existing sessions, not command-path enforcement.
- Treat enforcement as a later gated step for selected capabilities only, after shadow evidence, false-denial analysis, operator UX, and policy ownership are clear.
- For strong-fit operators, ask for sanitized logs, network thresholds, or one high-authority workflow to encode. For mature platforms, ask for a gap review of the protocol and negative tests.
- The strongest follow-up artifact is a customer-specific authority map: actors, capabilities, local state inputs, revocation triggers, fallback hooks, audit gaps, and where RCLP would be redundant.
