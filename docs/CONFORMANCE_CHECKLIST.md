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

- `AgentAttestation` identifies central and edge software actors.
- `RobotStateAssertion` binds robot, edge agent, mission, safety state,
  geofence state, network state, and observation time.
- `NetworkStateAssertion` is available for standalone network-state profiles;
  the local demo embeds network state in `RobotStateAssertion`. Trust-boundary
  use requires an authenticated envelope; the v0.0.1 local demo does not verify
  standalone network assertion signatures.
- `CapabilityRequest` is signed and includes requesting agent, edge agent,
  robot, mission, capability, reason, requested duration, and request nonce.
- `CapabilityDecision` records allow, deny, or degrade with reason code,
  deciding actor, policy reference, audit id, lease when allowed, and fallback
  alternatives when denied or degraded.
- `CapabilityLease` is signed, short-lived, scoped to agent/edge/robot/mission/
  capability, and carries local rejection constraints.
- `LeaseRevocation` identifies the lease, revoker, reason, revocation time, and
  fallback hook to declare if accepted.
- `FallbackDeclaration` records the selected fallback hook; it is not a
  certified safety behavior. Trust-boundary use requires an authenticated
  envelope; the v0.0.1 local demo emits local fallback declarations without
  verifying fallback declaration signatures.
- `AuditCommit` records every authority-relevant request, decision, command
  allow/reject, revocation, and fallback path.

## Authority Evaluation

The policy path MUST:

- fail closed for unknown agents, edge agents, robots, missions, capabilities,
  empty authority scopes, stale requests, replayed request nonces, invalid
  request signatures, and unaccepted policy digests;
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
- invalid lease signature;
- expired, stale, or too-long lease;
- lease context mismatch for agent, edge agent, robot, mission, or capability;
- missing required constraints for `remote_assist`;
- known revoked lease;
- current local state that violates lease constraints.

Each command allow or rejection MUST be auditable. Rejections SHOULD emit a
`FallbackDeclaration` chosen from local fallback policy.

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
across a trust boundary, signed revocation verification across a trust boundary,
fallback declaration signature verification across a trust boundary,
fleet-scale revocation propagation, or hosted SaaS behavior. Those are v0.1+
hardening items.
