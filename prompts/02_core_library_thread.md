# Codex Prompt — T2 Core Library

You are the core library engineer. Read `AGENTS.md`, `docs/PROTOCOL_SPEC_DRAFT.md`, `docs/SECURITY_DOCTRINE.md`, and tests.

Goal: implement the protocol core in dependency-light Python.

Tasks:

1. Review `src/rclp_core/` models, policy, crypto, leases, audit, and network modules.
2. Ensure protocol objects are typed and serializable.
3. Implement/strengthen lease signing and verification.
4. Implement policy checks for capability, geofence, network thresholds, mission, robot, and agent identity.
5. Add tests for allow, deny, expired lease, wrong robot, wrong mission, invalid signature, and degraded network.
6. Keep all tests local and deterministic.

Acceptance criteria:

- `pytest` passes.
- Every allow path has at least one negative test.
- No external network calls.
