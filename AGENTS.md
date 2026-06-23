# AGENTS.md — RCLP Open Protocol MVP

## Mission

Build a minimal, testable, open reference implementation for a central-agent ↔ edge-agent physical capability lease protocol. Keep the repo narrow and protocol-oriented.

## Required reading before making changes

- `docs/ENGINEERING_DOCTRINE.md`
- `docs/SECURITY_DOCTRINE.md`
- `docs/DESIGN_TASTE.md`
- `docs/PROTOCOL_SPEC_DRAFT.md`
- `docs/THREAT_MODEL.md`
- `docs/TEST_STRATEGY.md`

## Architectural constraints

- RCLP governs **authority**, not low-level robot safety.
- The edge agent must be able to reject unsafe, stale, invalid, or unauthorized requests locally.
- Leases must be short-lived, scoped, signed, and auditable.
- Network state, geofence state, mission state, and fallback policy are policy inputs.
- Use existing ecosystems where possible: ROS 2, Isaac Sim, VDA5050, MCP/A2A adapters later.
- Do not turn this repo into a full fleet manager, teleop system, carrier integration, or hosted SaaS.

## Coding rules

- Prefer small, typed Python modules.
- Keep protocol models pure and dependency-light.
- Write tests for every behavior change.
- All security-relevant code needs a negative test.
- Never introduce external network calls in tests.
- Never commit secrets, tokens, API keys, Lambda credentials, or private keys.
- Generated demo keys are allowed only if clearly labeled non-production.
- Avoid framework lock-in in `rclp_core/`.

## Validation commands

Run before considering work complete:

```bash
python -m compileall src tests
pytest
```

If formatting/lint tooling is installed:

```bash
ruff check .
ruff format .
```

## Documentation rules

- Keep protocol docs normative where possible: MUST, SHOULD, MAY.
- Separate MVP assumptions from future commercial-platform ideas.
- Mark open questions explicitly.
- Every new protocol message must include: purpose, required fields, rejection conditions, audit impact.

## Safety language

Use precise wording:

- Say “safety-adjacent authority layer,” not “certified safety system.”
- Say “fallback hook,” not “guaranteed safe behavior.”
- Say “network-state-aware authorization,” not “network guarantees.”
- Say “sim proof,” not “field-proven safety.”

## Repository boundary

Commercial platform code belongs in a future separate repo. This repo may include commercial boundary notes but not managed SaaS implementation.
