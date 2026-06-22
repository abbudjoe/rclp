# Codex Prompt — T8 Security Red Team

You are the security reviewer. Read `docs/SECURITY_DOCTRINE.md`, `docs/THREAT_MODEL.md`, and all tests.

Goal: break the protocol MVP before customers do.

Tasks:

1. Add negative tests for replay, stale lease, wrong robot, wrong mission, wrong capability, expired lease, revoked lease, invalid signature, unknown agent, and policy downgrade.
2. Review for unsafe wording in docs.
3. Add a `docs/SECURITY_REVIEW_NOTES.md` file with MVP blockers and future hardening.
4. Do not introduce heavy dependencies without justification.

Acceptance criteria:

- Security tests pass.
- New issues are explicit and prioritized.
- No production-safety overclaims remain.
