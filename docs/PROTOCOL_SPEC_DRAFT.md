# RCLP Protocol Spec Draft

Status: MVP draft. Normative keywords in this draft describe intended v0.1
behavior but are not a standards claim until a v0.1 tag exists.

## Purpose

RCLP defines a safety-adjacent authority layer for central agents and edge
agents operating near robots. It answers one narrow question:

> Who is allowed to make this robot do this physical thing, right now, and
> under what conditions?

RCLP specifies how software actors request, grant, deny, degrade, revoke, and
audit short-lived physical capability leases. It does not replace the robot's
local safety system, autonomy stack, fleet scheduler, or network transport.

## Non-goals

RCLP does not define:

- robot navigation
- robot mission planning
- map formats
- teleoperation media transport
- low-level motor control
- certified safety behavior
- carrier network APIs
- fleet scheduling
- hosted control-plane or SaaS requirements

## Actors

- **Human owner / organization:** legal and operational authority source.
- **Central agent:** fleet-level software actor that can request capabilities.
- **Edge agent:** robot-local software actor that verifies local state and
  enforces leases.
- **Robot:** physical endpoint with autonomy/safety stack.
- **Policy engine:** deterministic evaluator that grants, denies, degrades, or
  revokes authority from explicit inputs.
- **Audit sink:** append-only record of protocol events.

## Common Message Requirements

Every top-level protocol message defined in this section MUST carry:

- `protocol_version`
- `message_id`
- `correlation_id`
- `created_at`
- `message_type`

Unless a message defines a more specific identifier, the message's
`message_id` is its stable protocol identifier. Fields such as `request_id`,
`decision_id`, and `revocation_id` reference the target message's `message_id`.
Embedded objects MAY inherit `correlation_id` from the containing top-level
message, but standalone transmission MUST include the common envelope.

Messages that cross a trust boundary MUST be authenticated and integrity
protected. The MVP reference implementation may use clearly labeled
non-production keys, but the protocol contract assumes verifiable message
origin and payload integrity.

Receivers MUST reject malformed messages, unsupported `protocol_version`
values, duplicate `message_id` values in a replay-sensitive context, and
messages whose authenticated identity does not match their claimed actor field.

Authority-changing messages MUST produce or reference an audit record.

## Message Types

The v0.0.1 reference implementation exposes the following Pydantic protocol
messages in `src/rclp_core/models.py` and the ROS-agnostic command gate.
`AuditEvent` and `AgentIdentity` remain compatibility aliases, but the protocol
message names are `AuditCommit` and `AgentAttestation`.

| Protocol message | Reference model | Wire `message_type` |
|---|---|---|
| `AgentAttestation` | `AgentAttestation` | `agent_attestation` |
| `RobotStateAssertion` | `RobotStateAssertion` | `robot_state_assertion` |
| `NetworkStateAssertion` | `NetworkStateAssertion` | `network_state_assertion` |
| `CapabilityRequest` | `CapabilityRequest` | `capability_request` |
| `CapabilityDecision` | `CapabilityDecision` | `capability_decision` |
| `CapabilityLease` | `CapabilityLease` | `capability_lease` |
| `EdgeCommand` | `rclp_ros2.command_gate.EdgeCommand` | `edge_command` |
| `LeaseRevocation` | `LeaseRevocation` | `lease_revocation` |
| `FallbackDeclaration` | `FallbackDeclaration` | `fallback_declaration` |
| `AuditCommit` | `AuditCommit` | `audit_commit` |

The local v0.0.1 implementation enforces signed `CapabilityRequest`, signed
edge-local `RobotStateAssertion`, signed `CapabilityLease`, and signed
`LeaseRevocation` paths. Standalone `NetworkStateAssertion`,
`CapabilityDecision`, and `FallbackDeclaration` trust-boundary signature
verification remain v0.1 release blockers, so those messages MUST be treated as
local/in-process demo messages unless a downstream implementation adds
authenticated envelopes and negative tests.

### AgentAttestation

Purpose: proves the identity and version of a central or edge agent.

Required fields:

- `agent_id`
- `kind`
- `manifest_digest`
- `public_key_id`
- `trust_tier`
- `created_at`
- `authenticated_agent_id`
- `signature` or equivalent authenticated envelope

Optional fields:

- `revoked`

Rejection conditions:

- missing or unsupported `kind`
- missing `manifest_digest`, `public_key_id`, or trust tier
- signed material exceeds the active per-field or total attestation budget
  before signature verification or canonicalization
- attestation is stale for the active profile
- manifest digest does not match the referenced implementation manifest
- authenticated identity does not match `agent_id`
- signature is missing, malformed, or invalid
- authenticated identity key is not trusted for the active profile
- agent is revoked or outside the accepted trust tier

Audit impact:

- Accepted attestations SHOULD be linked to future request, decision, and audit
  chains by `agent_id` and `public_key_id`.
- Rejected attestations SHOULD be auditable when authenticated enough to inspect.

### RobotStateAssertion

Purpose: reports robot-local state relevant to authority decisions.

Required fields:

- `robot_id`
- `edge_agent_id`
- `authenticated_edge_agent_id`
- `mission_id`
- `safety_state`
- `geofence_state`
- `network_state`
- `network_state.attached`
- `observed_at`
- `signature` or equivalent authenticated envelope

Optional fields:

- `human_operator_available`

Rejection conditions:

- robot, edge agent, or mission does not match the request or lease context
- state is stale for the policy profile in use
- safety, geofence, network, or mission state is missing or unsupported
- nested authority inputs required by policy, including `network_state.attached`,
  are missing from the signed wire object
- network profile is unknown or internally contradictory, including
  `profile=partition` with `attached=true`
- authenticated identity does not match `edge_agent_id`
- signature is missing, malformed, or invalid
- nested network/geofence observation timestamps are stale or in the future
- fresher local state conflicts with the assertion

Audit impact:

- Decisions that depend on robot, geofence, mission, human-operator, or network
  state MUST reference the assertion `message_id`, payload hash, or equivalent
  state snapshot.

### CapabilityRequest

Purpose: a central agent asks an edge agent or policy engine for authority to
exercise one physical capability for one robot in one mission.

Required fields:

- `requesting_agent_id`
- `authenticated_agent_id`
- `edge_agent_id`
- `robot_id`
- `mission_id`
- `capability`
- `reason`
- `requested_duration_seconds`
- `request_nonce`
- `created_at`
- `signature` or equivalent authenticated envelope

Optional fields:

- `requested_constraints`
- `human_operator_id`
- `state_assertion_refs`

Normative behavior:

- A request MUST name exactly one `capability`, `robot_id`, `edge_agent_id`,
  and `mission_id`.
- `requested_duration_seconds` MUST be positive and MUST NOT exceed the
  maximum lease TTL allowed by policy for the capability.
- `reason` SHOULD be human-legible enough for audit replay, but MUST NOT be the
  only authorization input.
- `request_nonce` MUST be unique per requesting agent for the replay window
  enforced by the receiver.
- Requested constraints MAY narrow authority. They MUST NOT expand authority
  beyond policy or robot-local state.
- Unknown top-level request fields or unknown nested `requested_constraints`
  fields MUST be rejected at trust boundaries before signature acceptance.

Rejection conditions:

- unknown, revoked, or unauthenticated requesting agent
- unknown edge agent or robot
- request authenticated as a different actor than `requesting_agent_id`
- mission mismatch or mission not allowed by policy
- unsupported capability or capability not covered by policy
- missing delegation from the human owner or organization
- requested duration exceeds policy limit
- requested constraints conflict with policy or local state
- invalid signature or malformed authenticated envelope
- replayed `request_nonce` or duplicate request in the active replay window
- stale `created_at` outside the receiver's accepted clock-skew window

Audit impact:

- Every accepted, denied, or malformed-but-authenticated request MUST be linked
  to an audit event using `correlation_id` or an equivalent causal reference.

### CapabilityDecision

Purpose: the policy engine or edge agent records the result of evaluating a
`CapabilityRequest`.

Required fields:

- `request_id`
- `decision`
- `reason_code`
- `audit_id`
- `created_at`
- `deciding_actor_id`
- `policy_id` and/or `policy_digest`
- `signature` or equivalent authenticated envelope
- `lease` when `decision` is `allow`
- `safe_alternatives` when `decision` is `deny` or `degrade`

Normative behavior:

- `decision` MUST be one of `allow`, `deny`, or `degrade`.
- An `allow` decision MUST include a `CapabilityLease`.
- A `deny` or `degrade` decision MUST include at least one useful
  `safe_alternatives` value.
- `reason_code` MUST be stable enough for conformance tests and audit replay.
- The decision MUST be causally linked to exactly one request.
- The decision MUST identify the policy input used for the decision by
  `policy_id`, `policy_digest`, or another stable policy reference.
- Lease invalidation MUST be represented by `LeaseRevocation`, not by a
  `CapabilityDecision`.

Rejection conditions:

- decision is not linked to a known request
- request fields do not match the embedded or referenced lease
- `allow` decision has no lease
- `allow` decision includes an expired, overbroad, unsigned, or malformed lease
- `deny` or `degrade` decision lacks a reason code or safe alternative
- `decision` value is unknown to the receiver
- `decision` attempts to revoke authority instead of using `LeaseRevocation`
- deciding actor is not authorized to decide for the edge agent, robot,
  mission, and capability
- policy reference is missing, revoked, or not accepted by the edge agent
- invalid signature or authenticated identity mismatch

Audit impact:

- Every decision MUST create or reference an `AuditCommit`.
- Allow, deny, and degrade paths MUST be auditable with the request, state
  inputs, policy reference, and reason code needed for replay.

### CapabilityLease

Purpose: a signed, short-lived grant of authority for one agent to exercise one
capability against one robot through one edge agent in one mission.

Required fields:

- common protocol envelope fields: `protocol_version`, `message_id`,
  `correlation_id`, `created_at`, `message_type`
- `lease_id`
- `issuer_id`
- `agent_id`
- `edge_agent_id`
- `robot_id`
- `mission_id`
- `capability`
- `constraints`
- `issued_at`
- `expires_at`
- `nonce`
- `policy_id`
- `policy_digest`
- `signature`

Required constraint semantics:

- A lease MUST bind authority to the named `agent_id`, `edge_agent_id`,
  `robot_id`, `mission_id`, and `capability`.
- A lease MUST include a finite time window.
- A lease MUST carry enough constraints for local edge rejection, such as
  geofence, network-state thresholds, mission state, maximum speed, or fallback
  hooks when those inputs are policy-relevant.
- A lease MUST be verifiable by the edge agent without contacting a cloud
  service during command enforcement.
- The signed lease material MUST bind `policy_id` and `policy_digest`; edge
  verifier profiles MUST reject leases whose signed policy reference is missing
  or not accepted.
- Edge verifier profiles MUST compare signed lease constraints to an explicit
  local policy-bound constraint contract for the lease capability. Signed
  constraints MAY narrow authority, but MUST NOT claim broader authority than
  the accepted local policy bounds.
- When geofence membership is policy-relevant, the policy-bound constraint
  contract MUST include the specific `geofence_id`; a signed lease geofence
  constraint for any other geofence MUST be rejected locally.
- When a local policy bound specifies `fallback_on_degrade`, verifiers MUST
  compare the lease's effective fallback value to that bound even if the lease
  omitted the field and the model default supplied the effective value.

Rejection conditions:

- unsupported `protocol_version`, missing `message_type`, or unknown top-level
  lease fields at a trust boundary
- unknown nested lease constraint fields at a trust boundary
- missing, unaccepted, or mismatched signed `policy_id`/`policy_digest` in a
  verifier profile that pins policy provenance
- signature is invalid or missing
- `issuer_id` is unknown, revoked, or not authorized for the capability
- current time is before `issued_at` or after `expires_at`, allowing only the
  receiver's explicit clock-skew tolerance
- lease is not bound to the requesting command's agent, edge agent, robot,
  mission, or capability
- lease constraints are violated by current local state
- signed lease constraints exceed the accepted local policy-bound constraint
  contract for the capability
- a state-constrained capability lacks fresh edge-local current state
- a `max_speed_mps` constraint is present and the command payload omits,
  malforms, or exceeds the requested speed
- lease was superseded or revoked by a known `LeaseRevocation`
- `nonce` or `lease_id` is replayed in a conflicting context
- required constraint fields for the capability are missing
- lease TTL exceeds policy maximum

Audit impact:

- Lease issuance MUST be auditable as part of the corresponding
  `CapabilityDecision`.
- Lease validation failures that block a physical command MUST be auditable.

### EdgeCommand

Purpose: a central-agent command presented to an edge agent for local
authorization under a matching capability lease.

Required fields:

- common protocol envelope fields: `protocol_version`, `message_id`,
  `correlation_id`, `created_at`, and `message_type`
- `command_id`
- `agent_id`
- `authenticated_agent_id`
- `edge_agent_id`
- `robot_id`
- `mission_id`
- `capability`
- `command_nonce`
- `payload`
- `signature`

Rejection conditions:

- protocol version is unsupported
- `authenticated_agent_id` is missing or does not match `agent_id`
- command signature is missing, invalid, or signed by an untrusted command key
- command `payload` is missing or was changed after signing
- command `payload` contains members outside the accepted capability's typed
  payload schema; in the MVP speed-constrained profile, executable speed
  intent MUST be represented only by top-level `max_speed_mps` and/or
  `speed_mps`
- signed command material exceeds the verifier profile's pre-auth scalar,
  payload-size, node-count, or nesting-depth budget
- command is stale or not yet valid outside the receiver's explicit clock-skew
  tolerance
- a matching capability lease is absent
- `command_id` or `command_nonce` has already been accepted in the replay
  window
- command agent, edge agent, robot, mission, capability, or payload does not
  match the presented lease and local state constraints

Audit impact:

- Accepted and rejected commands MUST create or reference an `AuditCommit`.
- Command-authentication failures MUST NOT emit fallback declarations or call
  fallback hooks.
- Command-authentication failure audits MUST NOT treat claimed command robot,
  mission, edge, or actor fields as trusted authority subject fields; if
  recorded, they MUST be labeled as claimed/untrusted diagnostic context.
- Command-authentication failure diagnostics MUST bound untrusted claimed text
  fields before audit storage, either by truncating, hashing, or recording
  lengths instead of copying oversized attacker-controlled values.
- A command rejected only because the matching lease is absent MUST NOT consume
  command replay state or emit a fallback declaration.
- Lease authentication, provenance, freshness, scope, policy, constraint, and
  payload-validation denials MUST NOT emit a fallback declaration or invoke
  fallback hooks merely because a non-`None` lease was presented.
- Rejections after command authentication MAY emit a `FallbackDeclaration`
  chosen by local fallback policy only for local state fail-closed reasons or
  authenticated revocation-backed denials that provide enough authority context
  for the fallback hook.
- Command rejection audit MUST include the command identity, authenticated
  command actor, lease reference when present, reason code, and policy-relevant
  state references.

### LeaseRevocation

Purpose: invalidates a lease before its natural expiry when policy-relevant
state changes, authority is withdrawn, or compromise is suspected.

Required fields:

- `lease_id`
- `revoked_by`
- `edge_agent_id`
- `reason_code`
- `revoked_at`
- `created_at`
- `fallback_action`
- `signature` or equivalent authenticated envelope for trust-boundary use

Optional fields:

- `robot_id`
- `mission_id`
- `capability`
- `superseding_lease_id`

Normative behavior:

- A revocation MUST be authenticated by an actor authorized to revoke the
  referenced lease for the referenced `edge_agent_id`.
- An edge agent that knows a valid revocation MUST reject future use of the
  revoked lease.
- Accepted revocations MUST be recorded in durable edge-local authority state
  for the lease freshness window so command-gate restart cannot make the lease
  usable again.
- Replayed signed revocation messages MUST be idempotent: they MAY be audited
  as replayed or duplicate revocations, but MUST NOT re-emit fallback hooks.
- A revocation SHOULD include enough context for an edge agent to reject wrong
  robot, wrong mission, or wrong capability propagation mistakes.
- `edge_agent_id` MUST match the referenced lease. If `robot_id`,
  `mission_id`, or `capability` are present, they MUST also match the
  referenced lease. The local reference profile rejects conflicting context.
- A revocation MAY be generated locally by an edge agent when local policy
  inputs invalidate the lease.
- Lease invalidation MUST NOT depend on whether a fallback hook is present,
  supported, or accepted.
- `fallback_action` MAY help the edge agent select a fallback hook, but it is
  not authority to execute that hook. The actual selected fallback MUST be
  recorded separately as `FallbackDeclaration`.

Rejection conditions:

- invalid signature or authenticated identity mismatch
- signed revocation material exceeds the receiver's pre-auth text budget before
  signature decoding or verification
- missing signature or untrusted revoker key
- `revoked_by` is not authorized to revoke leases for the referenced
  `edge_agent_id`
- referenced lease is known and context fields conflict with it
- `edge_agent_id`, optional `robot_id`, optional `mission_id`, or optional
  `capability` fields conflict with the referenced lease
- `revoked_at` is implausibly stale or in the future outside the accepted
  clock-skew window
- `reason_code` is missing or unknown for the profile in use

Audit impact:

- Every accepted revocation MUST create or reference an `AuditCommit`.
- A rejected revocation SHOULD be auditable when it was authenticated but not
  accepted, because that may indicate misconfiguration or attack.
- If revocation triggers fallback, the fallback MUST be recorded separately as
  a `FallbackDeclaration`.

### NetworkStateAssertion

Purpose: reports network conditions used as policy inputs for capabilities that
depend on connectivity, such as remote assist.

Required fields:

- `edge_agent_id`
- `robot_id`
- `mission_id`
- `profile`
- `attached`
- `latency_ms_p95`
- `packet_loss_pct`
- `uplink_mbps`
- `observed_at`
- `measurement_window_seconds`
- `source`
- `signature` or equivalent authenticated envelope

Normative behavior:

- Network state is an authorization input, not a network guarantee.
- The assertion MUST identify the edge agent and robot whose authority decision
  may use it.
- Measurements MUST be bounded to an explicit observation time and measurement
  window.
- Policy thresholds SHOULD include hysteresis or minimum-window semantics to
  avoid rapid grant/revoke oscillation.
- A receiver MAY use a coarser local network profile when exact measurements
  are unavailable, but it MUST treat unknown state conservatively for
  high-authority capabilities.
- `attached` MUST be present explicitly on the signed wire object; a receiver
  MUST NOT authorize from a default-filled attachment value.
- `profile=partition` MUST be treated as detached for authority decisions even
  if `attached=true` and measurements appear healthy.
Rejection conditions:

- assertion is stale for the policy profile in use
- edge agent, robot, or mission does not match the request or lease context
- measurement fields are missing, negative, non-finite, or physically
  implausible
- `measurement_window_seconds` is missing, zero, or too small for the policy
  profile
- `source` is not trusted for the edge agent or capability
- invalid signature or authenticated identity mismatch
- assertion conflicts with fresher local state

Audit impact:

- A decision that depends on network state MUST reference the assertion
  `message_id`, payload hash, or equivalent state snapshot.
- Network-triggered denial, degradation, fallback, or revocation MUST be
  auditable with the relevant thresholds and observed values.

### FallbackDeclaration

Purpose: declares the fallback hook selected after denial, expiry, degradation,
or revocation.

Required fields:

- `robot_id`
- `edge_agent_id`
- `mission_id`
- `trigger`
- `fallback_action`
- `declared_by`
- `created_at`
- `signature` or equivalent authenticated envelope

Optional fields:

- `lease_id`
- `decision_id`
- `revocation_id`

Normative behavior:

- A fallback declaration MUST describe a fallback hook, not certified safety
  behavior.
- `fallback_action` MUST be selected from the local fallback policy for the
  mission, robot, and capability.
- An edge agent MAY emit a fallback declaration locally without cloud
  connectivity when a lease expires, is revoked, or violates local constraints.
- Local robot safety systems remain authoritative for low-level safety.

Rejection conditions:

- declaring actor is not authorized for the robot or edge agent
- fallback action is unsupported or disallowed by local policy
- trigger is missing or unrelated to a known denial, expiry, degradation,
  constraint violation, or revocation
- robot, edge agent, or mission fields conflict with the related lease or
  decision
- invalid signature or authenticated identity mismatch
- declaration is stale, duplicated, or superseded by fresher local state

Audit impact:

- Every fallback declaration MUST be auditable.
- The audit record MUST preserve the trigger and any related decision,
  revocation, or lease reference needed to reconstruct the authority chain.

### AuditCommit

Purpose: records an append-only event in the causal authority chain.

Required fields:

- `audit_id`
- `correlation_id`
- `event_type`
- `actor_id`
- `robot_id`
- `mission_id`
- `summary`
- `payload`
- `payload_hash`
- `created_at`

Required for authority-changing events:

- `authority_relevant`
- `integrity_profile`
- `integrity_proof`

Optional fields:

- `previous_audit_hash`
- `policy_id`
- `policy_digest`
- `state_refs`
- `related_message_ids`

Stable `event_type` values for the MVP audit profile:

- `capability_requested`: a central agent requested a capability.
- `network_state_asserted`: robot-local or edge-local state used by policy was observed.
- `capability_allowed`: policy allowed a requested capability.
- `capability_denied`: policy denied a requested capability.
- `capability_degraded`: policy selected degraded authority or safe alternatives.
- `command_allowed`: the edge command gate accepted a command under a valid lease.
- `command_rejected`: the edge command gate or edge daemon rejected a command.
- `lease_revoked`: an accepted revocation invalidated a lease.
- `revocation_rejected`: a revocation was authenticated enough to inspect but rejected.
- `fallback_declared`: an edge agent declared a fallback hook.
- `diagnostic`: non-authority diagnostic event allowed by the local profile.
- `demo_setup`: non-authority demo setup event allowed by the local profile.

Normative behavior:

- Every authority decision path MUST emit an audit commit, including allow,
  deny, degrade, revoke, fallback, and command rejection paths.
- Audit commits for `capability_allowed`, `capability_denied`,
  `capability_degraded`, `command_allowed`, `command_rejected`,
  `lease_revoked`, `revocation_rejected`, and `fallback_declared` MUST set
  `authority_relevant` to `true`.
- `payload_hash` MUST commit to the protocol payload or canonical summary used
  for replay.
- `integrity_proof` MUST also commit to replay-critical top-level audit
  context, including event identity, actor, robot, mission, summary, policy
  reference, state refs, related message IDs, authority relevance, and previous
  hash-chain value.
- `related_message_ids` SHOULD include the request, state assertion, command,
  revocation, lease, or fallback declaration identifiers needed to reconstruct
  the causal chain.
- `state_refs` MUST identify policy-relevant state assertions when a decision
  depends on robot, geofence, mission, or network state.
- `summary` SHOULD be useful to operators, but replay MUST NOT depend on prose
  alone.
- Audit commits for authority-changing events MUST include an integrity proof
  sufficient for the active conformance profile, such as hash chaining, signed
  batches, or append-only storage with signed commit digests.
- `integrity_profile` MUST identify how `integrity_proof` should be verified.
- Non-authority diagnostic audit events MAY use weaker integrity guarantees
  when the profile explicitly allows it.

Rejection conditions:

- missing or duplicate `audit_id`
- missing common protocol envelope fields
- missing causal `correlation_id`
- `payload_hash` does not match the referenced payload
- integrity proof is missing or invalid for an authority-changing event
- event type is unknown to the audit profile in use
- unknown top-level audit fields are present outside the integrity proof
- actor identity is missing, revoked, or inconsistent with the referenced
  message
- required robot, mission, policy, state, or related-message references are
  missing for an authority-changing event
- `created_at` is outside accepted ordering or clock-skew tolerance for the
  audit sink

Audit impact:

- `AuditCommit` is the audit impact. Rejected audit commits MUST be surfaced as
  operationally significant because missing audit can make an authority chain
  unreconstructable.

## Lease Validation Rules

An edge agent MUST reject a physical command if:

- the command actor identity is missing, unauthenticated, mismatched with the
  command agent, signed by an untrusted command key, stale, not yet valid, or
  replayed by command id or nonce
- no lease is present for the capability
- the lease issuer is unknown, revoked, or not accepted by local policy
- the lease signature is invalid
- the lease is expired
- the lease is stale or has a TTL beyond the accepted policy maximum
- the lease agent, edge agent, robot, mission, or capability does not match
- the lease nonce has been used in an invalid context
- a revocation for the lease is known
- the capability requires current local state and no fresh local state is
  available
- current local state is unauthenticated or signed by an untrusted edge key
- local state violates hard constraints
- command payload constraints such as `max_speed_mps` are missing, malformed,
  exceeded, carried in conflicting aliases, or carried outside the accepted
  typed payload schema
- signed command material exceeds the verifier profile's pre-auth scalar,
  payload-size, node-count, or nesting-depth budget before command
  authentication can canonicalize untrusted input
- required audit behavior cannot be satisfied for an authority-changing path

## Network-State Policy

Network-state-aware authorization MAY be used for capabilities that depend on
connectivity. RCLP does not guarantee network quality. It only defines how
observed network state can influence authority decisions.

For high-authority capabilities, unknown, stale, or untrusted network state
SHOULD cause denial, degradation, or locally declared fallback according to
policy.

## Fallback Semantics

Fallback actions are declarations to the local robot runtime. RCLP does not
certify that a fallback is physically safe. The robot's local safety system
remains authoritative for low-level safety.

## Relationship to Adjacent Protocols

RCLP is intended to compose with existing robot and agent ecosystems. These
systems are substrates or adjacent protocols, not replacements for RCLP's
authority lease semantics.

- **ROS 2 security:** provides identity, encryption, and access-control
  mechanisms for ROS 2 graphs. RCLP can use those mechanisms as transport or
  runtime substrate, but ROS 2 security does not by itself define short-lived
  physical capability leases tied to mission, robot, network state, fallback,
  and audit causality.
- **VDA5050:** defines AGV/fleet-manager interoperability messages for orders,
  state, and actions. RCLP may authorize whether an actor can cause a robot to
  exercise a capability exposed through such a workflow, but it does not replace
  VDA5050 order/state semantics.
- **Open-RMF:** coordinates fleets, tasks, traffic, and shared facility
  resources. RCLP does not schedule fleets or allocate work. It can be used as
  an authority layer around specific physical capabilities invoked by or near an
  Open-RMF deployment.
- **MCP/A2A:** define agent-tool or agent-agent interaction patterns. RCLP may
  bind physical capability authority to requests originating through those
  channels, but generic agent communication does not answer whether this actor
  may make this robot do this physical thing right now under current policy and
  local state.

## MVP Assumptions

- Demo keys are non-production.
- Edge enforcement can evaluate cached policy and current local state without
  cloud availability.
- Network impairment used in MVP tests is simulated.
- Sim proof is not field-proven safety.
- Policy schemas and conformance tests will evolve before v0.1.

## Open Questions

- What canonical serialization and signature profile should v0.1 require?
- What clock-skew tolerance should conformance tests assume?
- Should `policy_id`, `policy_digest`, or both be mandatory on all decisions
  and leases?
- How should revocation propagation behave during long network partitions?
- What network measurement windows and hysteresis profiles are sufficient for
  the MVP remote-assist profile?
- Which audit integrity proof should the v0.1 conformance profile require:
  hash chaining, signed batches, append-only storage with signed commit
  digests, or another narrow mechanism?
- Which fields should be mandatory in the ROS 2, VDA5050, Open-RMF, MCP, and
  A2A adapter profiles?
- What is the smallest conformance schema that proves the authority contract
  without turning RCLP into a fleet manager?
