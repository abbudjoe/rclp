# Test Strategy

## Test levels

1. Unit tests for models, policy, lease expiry, signature validation.
2. Conformance tests for protocol behavior.
3. Scenario tests for full request → decision → enforcement → audit flows.
4. Fault-injection tests for network/geofence degradation.
5. Isaac Sim integration tests later.

The implementer checklist lives in `docs/CONFORMANCE_CHECKLIST.md`. The
protocol manifest in `manifests/rclp_protocol_manifest.yaml` is the field-name
contract that conformance tests should check against the Pydantic models.

## Minimum conformance cases

- valid remote-assist request allowed
- missing, invalid-signature, untrusted-key, or actor-mismatched
  `AgentAttestation` rejected before trust-boundary identity bootstrap
- soft degraded network degrades authority
- hard network failure denied
- no lease rejected
- invalid request signature rejected
- authenticated request actor mismatch rejected
- expired lease rejected
- stale request rejected
- stale but not-yet-expired lease rejected
- unsupported or future-field `CapabilityLease` rejected before authority allow
- unsigned or stale robot state assertion rejected before policy allow
- policy issuance without replay protection rejected
- missing, unsigned, or stale current edge state rejected at command gate
- missing, unsigned, stale, replayed, or actor-mismatched edge commands
  rejected at command gate before lease validation can allow
- unauthenticated command denials audited without fallback declarations or
  fallback sink calls
- command payload exceeding `max_speed_mps`, carrying conflicting speed aliases,
  or carrying speed-constrained motion intent outside the accepted typed
  payload schema rejected
- wrong robot rejected
- wrong agent rejected
- revoked lease rejected
- accepted revocation remains enforced after command-gate restart
- invalid signature rejected
- unknown requesting agent rejected
- unknown lease issuer rejected
- unknown revocation actor rejected
- unsigned, over-budget-signature, invalid-signature, stale, and
  context-conflicting revocation rejected
- replayed context rejected
- replayed request nonce rejected
- policy input with unknown top-level or nested future authority fields rejected
  before policy digest acceptance
- temporary request replay, command replay, and revocation stores rejected as
  non-durable at authority boundaries
- policy authority-scope downgrade rejected
- permissive policy digest downgrade rejected
- signed lease policy id/digest mismatch rejected by the Rust verifier
- Python command gate rejects signed leases whose policy id/digest is missing
  or not accepted by the local policy pin
- Python command gate and Rust verifier reject signed lease constraints that
  exceed accepted local policy-bound constraint values, including wrong
  geofence identity and effective fallback defaults
- Rust verifier rejects non-durable replay caches before authority decisions
  and preserves replay state across verifier restart when using a shared store
- Rust verifier rejects oversized signed command scalar fields and oversized or
  deeply nested command payloads before command HMAC canonicalization
- Rust verifier bounds oversized untrusted command-auth diagnostic fields before
  audit storage
- Python command gate labels pre-auth command diagnostic subject identifiers as
  claimed data and does not expose unprefixed trusted-looking subject keys
- Python command gate rejects oversized command and revocation signatures before
  base64 decode or signature verification
- audit event created for allow
- audit event created for deny
- audit event created for fallback
- audit replay rejects top-level context tampering
- audit JSONL import rejects appended unknown context outside the integrity
  proof
- replayed signed revocation does not re-emit fallback hooks, including after a
  command-gate restart
- Rust verifier malformed pre-parse audit records are diagnostic/non-authority
  and repeated malformed decisions have unique audit identities

## Commands

```bash
python -m compileall src tests
python -m pytest
```
