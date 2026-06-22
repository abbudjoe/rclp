# Codex Prompt — T1 Protocol Spec

You are the protocol specification lead. Read `AGENTS.md`, `docs/PROTOCOL_SPEC_DRAFT.md`, `docs/THREAT_MODEL.md`, and `docs/GOVERNANCE.md`.

Goal: tighten the RCLP spec without making it too broad.

Tasks:

1. Refine message definitions for `CapabilityRequest`, `CapabilityDecision`, `CapabilityLease`, `LeaseRevocation`, `NetworkStateAssertion`, `FallbackDeclaration`, and `AuditCommit`.
2. Add normative MUST/SHOULD/MAY language where useful.
3. Add rejection conditions for each message.
4. Add an explicit comparison section: ROS 2 security, VDA5050, Open-RMF, MCP/A2A are substrates or adjacent protocols, not replacements.
5. Add open questions and avoid overclaiming.

Acceptance criteria:

- Spec remains narrow.
- It answers: “Who is allowed to make this robot do this physical thing, right now, and under what conditions?”
- No commercial hosted platform features are specified as required.
