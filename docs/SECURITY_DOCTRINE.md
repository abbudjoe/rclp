# Security Doctrine

RCLP sits near a physical authority boundary. Treat mistakes as potentially safety-relevant even though this MVP is not a certified safety system.

## Security goals

- Least privilege for software actors.
- Explicit delegated authority.
- Short-lived capabilities.
- Local verification and enforcement.
- Replay resistance.
- Tamper-evident audit trail.
- Fail-closed for high-authority actions.
- Fail-operational only for predeclared local fallback modes.

## Threats to test in MVP

- Central agent sends command without a lease.
- Central agent sends unauthenticated, unsigned, invalid-signature, or replayed
  commands that attempt to trigger fallback side effects.
- Central agent reuses a request nonce inside the replay window.
- Central agent sends a stale capability request.
- Central agent sends an invalid request signature or actor-mismatched request.
- Central agent or operator supplies policy or request data with unknown future
  authority fields that would be dropped before digest or signature checks.
- Central agent reuses an expired lease.
- Central agent reuses a stale but not-yet-expired lease.
- Central agent presents a lease with an unsupported `protocol_version` or
  unknown future authority fields.
- Central agent presents a lease whose signed policy id/digest does not match
  the accepted policy reference.
- Lease is replayed on another robot.
- Lease is replayed by another agent.
- Lease is replayed for another mission.
- Agent requests capability outside scope.
- Unknown lease issuer or revocation actor attempts to affect authority.
- A previously accepted revocation is forgotten after command-gate restart.
- A replayed signed revocation attempts to trigger fallback side effects again.
- Temporary process-local stores are accidentally accepted as durable authority
  stores for replay or revocation state.
- Network degrades below policy threshold.
- Geofence check fails.
- Cloud/control plane becomes unreachable.
- Policy is downgraded or loses explicit authority scopes while a mission is
  active.
- Audit events are missing or causally incomplete.
- Audit JSONL contains appended unknown context outside the integrity proof.
- Diagnostic malformed-input audit events are confused with authority-relevant
  command decisions, or distinct audit events collide on `audit_id`.

## Non-production crypto note

The reference implementation may use local generated Ed25519 keys for demonstration. Production systems need hardware-backed keys, key rotation, revocation, certificate chains, secure boot/attestation, and incident response workflows.

## Required negative-test principle

Every allow path must have a corresponding deny/reject test.
