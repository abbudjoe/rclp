# Codex Prompt — T6 Audit + Incident Replay

You are implementing incident-grade audit scaffolding. Read `docs/API_STYLE.md`, `docs/THREAT_MODEL.md`, and `src/rclp_core/audit.py`.

Goal: every authority decision should be reconstructable.

Tasks:

1. Define stable audit event types.
2. Add JSONL export.
3. Add a replay summarizer that groups events by correlation ID.
4. Ensure allow, deny, revoke, fallback, and command rejection paths emit audit events.
5. Add tests for causal completeness.

Acceptance criteria:

- Demo prints replay summary.
- Audit event schema is documented.
- No silent security-relevant decisions.
