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
- soft degraded network degrades authority
- hard network failure denied
- no lease rejected
- invalid request signature rejected
- authenticated request actor mismatch rejected
- expired lease rejected
- stale request rejected
- stale but not-yet-expired lease rejected
- unsigned or stale robot state assertion rejected before policy allow
- policy issuance without replay protection rejected
- missing, unsigned, or stale current edge state rejected at command gate
- missing, unsigned, stale, replayed, or actor-mismatched edge commands
  rejected at command gate before lease validation can allow
- command payload exceeding `max_speed_mps` or carrying conflicting speed
  aliases rejected
- wrong robot rejected
- wrong agent rejected
- revoked lease rejected
- invalid signature rejected
- unknown requesting agent rejected
- unknown lease issuer rejected
- unknown revocation actor rejected
- unsigned, invalid-signature, stale, and context-conflicting revocation
  rejected
- replayed context rejected
- replayed request nonce rejected
- policy authority-scope downgrade rejected
- permissive policy digest downgrade rejected
- audit event created for allow
- audit event created for deny
- audit event created for fallback
- audit replay rejects top-level context tampering

## Commands

```bash
python -m compileall src tests
python -m pytest
```
