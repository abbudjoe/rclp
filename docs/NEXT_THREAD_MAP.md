# Next Thread Map

This map defines the next Codex threads after T12. Run one thread at a time
through its own source contract and definition of done. Do not combine
validation packaging, customer synthesis, and simulator work into one broad
thread.

## T13 - Demo + Validation Release Package

Goal:

- Turn the working RCLP MVP into a clean validation package for controlled
  technical validation calls with robotics, platform, and fleet operators.

Inputs:

- Supplied T13 prompt: `T13 - Demo + Validation Release Package`.
- `docs/POST_T12_SEQUENCE_PLAN.md`.
- `docs/CUSTOMER_CALL_READINESS_CHECKLIST.md`.
- `README.md`, `docs/RELEASE_READINESS.md`, `docs/SAFETY_BOUNDARY.md`,
  `docs/COMMERCIAL_BOUNDARY.md`, `docs/RUST_EDGE_VERIFIER.md`, existing demo
  docs, tests, examples, manifests, agents, and Rust crate.

Non-goals:

- Hosted commercial platform.
- Customer accounts or billing.
- Carrier/MVNO/eSIM integration.
- Real QoS or carrier API integration.
- Isaac Sim visual POC.
- New protocol features except fixes for broken demo or broken tests.
- Production crypto overhaul.
- Formal safety certification evidence.
- Full robot hardware integration.
- Dashboard.

Definition of done:

- Validation release notes exist for `v0.1-validation`.
- Customer call packet exists.
- Technical FAQ exists.
- Demo walkthrough is accurate for a live 5-minute call.
- Comparison doc explains why RCLP sits alongside ROS 2, VDA5050, Open-RMF,
  MCP, A2A, fleet managers, teleop systems, and IoT connectivity platforms.
- First-call target profile exists.
- Local validation check script exists and works.
- Local validation demo script exists and works.
- README links to validation docs.
- Tests and evals pass, or missing T12 eval artifacts are explicitly blocking.
- Final readiness assessment says whether the repo is ready for controlled
  technical validation calls.

When to run:

- Run immediately after human final review and a fresh-clone validation pass.
- Run before broad outreach and before creating `v0.1-validation`.

## T14 - Isaac Sim Visual POC On Lambda.ai

Goal:

- Build a visual proof-of-concept plan and scaffold that shows the RCLP flow
  inside or alongside Isaac Sim on Lambda.ai.

Inputs:

- Supplied T14 prompt: `T14 - Isaac Sim Visual POC on Lambda.ai`.
- T13 validation release package.
- Existing `isaac_sim/` scaffolding, local demo, eval semantics, protocol
  implementation, safety boundary, and release notes.

Non-goals:

- Full robot autonomy stack.
- Full ROS 2 production integration.
- Production safety layer.
- Hosted commercial control plane.
- Carrier/MVNO/eSIM integration.
- Real cellular QoS.
- Complex multi-robot simulation.
- Photorealistic environment.
- Advanced navigation stack unless already trivial.
- Full NVIDIA Isaac Mission Dispatch integration.
- Full VDA5050 implementation.
- Dashboard.
- Anything requiring secrets or paid services beyond explicitly authorized
  Lambda compute access.

Definition of done:

- Isaac Sim POC architecture is documented.
- Lambda.ai setup doc exists.
- Scenario docs exist for remote assist authority gating and network-degrade
  revocation.
- Visual demo script exists.
- Safe setup and run scripts exist.
- Python integration scaffold exists and reuses RCLP logic instead of forking
  the protocol.
- Non-Isaac tests cover the scaffold and do not require GPU, ROS 2, Lambda, or
  Isaac Sim.
- Existing tests and evals still pass.
- README links to Isaac POC docs.
- Final response states what was validated locally and what remains to run on
  Lambda.ai.

When to run:

- Run after T13 creates the validation release package, or in parallel only if
  the owner explicitly wants simulator polish while T13 stays the customer-call
  gate.
- Do not run paid Lambda compute without current-turn authorization for the
  specific mutation.

## T15 - First Customer Feedback Synthesis

Goal:

- Synthesize the first 5-8 controlled technical validation calls into protocol,
  demo, commercial, and adoption findings.

Inputs:

- Field notes from controlled calls.
- Customer call packet.
- Demo walkthrough.
- Strong and weak signal criteria from the post-T12 sequence plan.

Non-goals:

- Building requested features during synthesis.
- Starting SaaS implementation.
- Treating a single enthusiastic call as product-market fit.
- Turning customer-specific workflows into protocol requirements without
  repeat evidence.

Definition of done:

- Calls are summarized by persona, fleet type, authority gap, current stack,
  requested integration point, observe-only appetite, audit needs, and blockers.
- Strong, weak, and ambiguous signals are separated.
- Protocol-boundary changes are listed separately from simulator polish and
  commercial-platform requests.
- Recommended next branch is selected or explicitly deferred.

When to run:

- Run after at least 5 controlled calls, or earlier only if a blocker repeats
  across multiple high-fit conversations.

## T16 - Rust/Python Parity Adapter

Goal:

- Decide whether to deepen Rust parity with the Python reference and, if so,
  close the most important edge-verifier semantic gaps.

Inputs:

- Rust verifier docs and vectors.
- Python reference implementation.
- Customer feedback requiring hardened edge-side enforcement.
- T13/T15 findings.

Non-goals:

- Replacing the Python reference.
- Production crypto promises without a signed spec and key lifecycle plan.
- ROS 2, Isaac Sim, hosted service, or dashboard work.

Definition of done:

- Parity gaps are enumerated.
- Any implemented parity change has shared vectors and negative tests.
- Python tests do not require Cargo unless intentionally changed.
- Rust docs still describe spike versus hardened profile honestly.

When to run:

- Run only if customer feedback or validation evidence shows edge-verifier
  hardening matters more than observe-only integration or visual demo polish.

## T17 - Observe-Only Integration Spike

Goal:

- Explore a low-risk observe-only integration path that records authority
  decisions without initially enforcing robot command gating.

Inputs:

- Customer feedback that names a real stack location for RCLP.
- Safety and commercial boundaries.
- Existing audit/replay implementation.
- Protocol spec and conformance checklist.

Non-goals:

- Production deployment.
- Customer-specific proprietary integration.
- Full fleet manager, teleop system, carrier integration, or hosted platform.
- Enforcement claims before observe-only evidence.

Definition of done:

- Observe-only event contract is documented.
- Required customer-side integration points are listed without secrets or
  proprietary details.
- Audit output can explain what would have allowed, denied, degraded, or
  revoked authority.
- Follow-on enforcement work is explicitly gated by customer feedback and
  safety review.

When to run:

- Run after customer calls show a strong need and a realistic edge or sidecar
  insertion point.

