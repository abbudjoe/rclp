# Threat Model

## Protected assets

- Robot authority decisions
- Capability leases
- Agent identity keys
- Robot/edge identity keys
- Policy definitions
- Audit trail integrity
- Local fallback behavior

## Trust assumptions for MVP

- Demo keys are local and non-production.
- Central and edge agents run in controlled test environments.
- Network impairment is simulated.
- Isaac Sim is used for concept proof, not safety validation.

## High-priority threats

| Threat | Example | MVP mitigation |
|---|---|---|
| Overbroad central authority | central agent sends direct command | command gate requires valid lease |
| Request replay | reused request nonce or ephemeral replay cache after restart | mandatory durable request replay cache rejects duplicate agent/nonce pairs |
| Lease replay or version/policy downgrade | old, context-shifted, unsupported-version, or wrong-policy lease reused | explicit `CapabilityLease` protocol envelope, signed policy reference, nonce, expiry, staleness, signature, issuer allow-list, context binding |
| Stale or forged state | stale or unsigned robot-local state used for authority | policy requires signed edge-local state with bounded freshness |
| Stale command | command arrives after network partition | request age, lease age, expiry, and fresh local state checks |
| Unauthenticated command triggers fallback | unsigned or invalid command is sent only to force local fallback hooks | command authentication failures are audited without emitting `FallbackDeclaration` side effects |
| Command exceeds lease constraints | speed-limited lease used for faster command | command gate enforces `max_speed_mps` from command payload |
| Signed lease exceeds local policy bounds | compromised issuer signs `max_speed_mps`, relaxed network thresholds, the wrong geofence, or fallback behavior not granted by accepted policy | edge verifier compares signed lease constraints and effective defaults to typed local constraint bounds and rejects overbroad leases |
| Wrong robot | lease for robot A used on robot B | robot_id binding in lease |
| Wrong mission or capability | lease for mission/capability A used for B | mission_id and capability binding in lease |
| Policy downgrade | permissive policy pushed mid-mission or unknown policy fields hidden before digesting | strict policy schema plus accepted policy digest pin; future: signed policy bundles |
| Empty-scope policy downgrade | allow-list removed from policy | explicit authority scopes fail closed |
| Unknown, cross-edge, or replayed issuer/revoker | untrusted actor issues lease, revokes another edge's authority, or replays a signed revocation for fallback side effects | trusted issuer and revoker sets, signed revocation checks, durable revocation store with revocation-message replay detection, required revocation `edge_agent_id`, and default denial for revokers not scoped to the lease edge |
| Compromised central agent | known agent requests unsupported or excessive authority | deny and audit; future: escalation and rate limits |
| Audit context tamper or collision | audit payload unchanged but robot/mission/state refs changed, unknown context is appended outside the proof, or repeated malformed inputs collide on audit identity | strict audit import plus proof binding of replay-critical top-level context; Rust audit events bind a per-event identity nonce and classify pre-parse malformed records as diagnostic |
| Missing audit | decision cannot be reconstructed | audit required for every decision path |

## Out-of-scope for MVP, not out-of-scope forever

- Hardware roots of trust
- Secure boot
- TPM/TEE-backed key storage
- Formal verification
- Certified safety control
- Production key rotation
- Fleet-scale revocation propagation
