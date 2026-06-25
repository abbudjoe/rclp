# Conformance Checklist

Status: v0.0.1 local reference profile.

This checklist is for implementers who want to prove the RCLP primitive without
turning the repo into a fleet manager, teleop system, carrier integration, or
hosted control plane.

## Primitive

An implementation conforms to the MVP primitive when it can answer:

> Who is allowed to make this robot do this physical thing, right now, and
> under what conditions?

For the reference profile, the physical capability is `remote_assist`, the
authority object is a short-lived `CapabilityLease`, and the edge-side command
gate must reject commands that lack valid authority.

## Message Surface

Implementers MUST support the message names and fields listed in
`manifests/rclp_protocol_manifest.yaml`. The reference implementation exports
the same surface from `src/rclp_core/models.py`.

Minimum v0.0.1 message checklist:

- `AgentAttestation` identifies central and edge software actors, binds the
  claimed `agent_id` to `authenticated_agent_id`, and carries signature material
  plus explicit `signature_alg` metadata for trust-boundary verification.
- `RobotStateAssertion` binds robot, edge agent, authenticated edge identity,
  mission, safety state, geofence state, network state, observation time, and
  explicit signature metadata.
- `NetworkStateAssertion` is available for standalone network-state profiles;
  the local demo embeds network state in `RobotStateAssertion`. Trust-boundary
  use requires an authenticated envelope; the v0.0.1 local demo does not verify
  standalone network assertion signatures.
- `CapabilityRequest` is signed and includes requesting agent, edge agent,
  robot, mission, capability, reason, requested duration, and request nonce.
- `CapabilityDecision` records allow, deny, or degrade with reason code,
  deciding actor, policy reference, audit id, lease when allowed, and fallback
  alternatives when denied or degraded.
- `CapabilityLease` carries the common protocol envelope and `capability_lease`
  message type, is signed, short-lived, scoped to agent/edge/robot/mission/
  capability, binds signed policy provenance, rejects unsupported versions or
  unknown future fields at trust boundaries, and carries local rejection
  constraints.
- `LeaseRevocation` identifies the lease, signed revoker, edge agent, reason,
  revocation time, optional robot/mission/capability context, and advisory
  fallback hook. Accepted revocations persist in durable edge-local authority
  state and replayed signed revocation messages do not re-emit fallback hooks.
  Cross-edge revokers are denied by default; broader revokers require explicit
  `revoker_edge_scopes_by_id` configuration, and the selected fallback remains
  a local-policy decision.
- `FallbackDeclaration` records the selected fallback hook; it is not a
  certified safety behavior. Trust-boundary use requires `signature_alg`,
  `authenticated_declared_by`, and a valid signature by an authorized edge
  declarer. Local in-process fallback declarations may remain unsigned records.
- `AuditCommit` records every authority-relevant request, decision, command
  allow/reject, revocation, and fallback path. The MVP schema lives at
  `manifests/rclp_audit_conformance_schema.json`.

## Authority Evaluation

The policy path MUST:

- fail closed for unknown agents, edge agents, robots, missions, capabilities,
  empty authority scopes, stale requests, replayed request nonces, invalid
  request signatures, missing replay protection, unauthenticated or stale state,
  unknown future policy fields, and unaccepted policy digests;
- treat network state as an authorization input, not a network guarantee;
- allow `remote_assist` only when identity, mission, geofence, human-operator,
  network, policy-digest, and request-signature checks pass;
- degrade or deny when deterministic network profiles cross configured
  thresholds;
- produce a stable reason code and an audit commit for allow, deny, and degrade.

## Edge Enforcement

The edge command gate MUST reject:

- missing lease;
- unknown issuer;
- unsupported lease protocol version or unknown future lease fields at the
  trust boundary;
- missing or unaccepted signed lease policy provenance in verifier profiles that
  pin accepted policy digests;
- invalid lease signature;
- expired, stale, or too-long lease;
- lease context mismatch for agent, edge agent, robot, mission, or capability;
- accepted lease nonce replay, including after command-gate restart;
- missing required constraints for `remote_assist`;
- known revoked lease, including after command-gate restart;
- missing, unsigned, or stale current local state for state-constrained
  capabilities;
- current local state that violates lease constraints;
- command payloads that omit, malform, exceed, or conflict on `max_speed_mps`
  when present;
- command payload members outside the accepted capability's typed payload
  schema, including nested speed or motion fields in the MVP speed-constrained
  profile;
- missing or unsupported signature algorithm metadata for signed
  trust-boundary messages;
- signed command material that exceeds the verifier profile's pre-auth scalar,
  payload-size, node-count, or nesting-depth budget.
- signed revocation material that exceeds the receiver's pre-auth text budget
  before signature decoding or verification.

Each command allow or rejection MUST be auditable. Rejections after command
authentication SHOULD emit a `FallbackDeclaration` chosen from local fallback
policy. Command-authentication failures MUST NOT emit fallback side effects.
Unauthenticated command failure audits MUST NOT trust claimed command subject
fields as authority context.

## Required Local Evidence

Run these before claiming v0.0.1 local conformance:

```bash
python -m compileall src tests
python -m pytest
python -m rclp_agents.demo_remote_assist
python -m rclp_agents.demo_remote_assist --network-profile uplink_bad
```

If installed, also run:

```bash
ruff check .
ruff format .
```

## What v0.0.1 Does Not Prove

The local profile does not prove field safety, real cellular behavior,
production key management, signed policy bundle distribution, standalone
network-state assertion signature verification, signed decision verification
across a trust boundary, production fallback execution semantics, fleet-scale
revocation propagation, or hosted SaaS behavior. Those are v0.1+ hardening
items.
