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
| Request replay | reused request nonce | request replay cache rejects duplicate agent/nonce pairs |
| Lease replay | old or context-shifted lease reused | nonce, expiry, staleness, signature, issuer allow-list, context binding |
| Stale command | command arrives after network partition | request age, lease age, expiry, and local state checks |
| Wrong robot | lease for robot A used on robot B | robot_id binding in lease |
| Wrong mission or capability | lease for mission/capability A used for B | mission_id and capability binding in lease |
| Policy downgrade | permissive policy pushed mid-mission | accepted policy digest pin; future: signed policy bundles |
| Empty-scope policy downgrade | allow-list removed from policy | explicit authority scopes fail closed |
| Unknown issuer or revoker | untrusted actor issues lease or revokes authority | trusted issuer and revoker sets at edge gate |
| Compromised central agent | known agent requests unsupported or excessive authority | deny and audit; future: escalation and rate limits |
| Missing audit | decision cannot be reconstructed | audit required for every decision path |

## Out-of-scope for MVP, not out-of-scope forever

- Hardware roots of trust
- Secure boot
- TPM/TEE-backed key storage
- Formal verification
- Certified safety control
- Production key rotation
- Fleet-scale revocation propagation
