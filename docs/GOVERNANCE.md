# Open Protocol Governance Draft

## Principles

- Keep the protocol narrow.
- Optimize for interoperability and inspection.
- Do not require use of a commercial hosted service.
- Publish conformance tests.
- Treat safety claims conservatively.
- Support profiles/adapters rather than monolithic scope expansion.

## Versioning

Use semantic versioning once v0.1.0 is tagged.

- Patch: documentation clarifications, non-breaking test additions.
- Minor: backward-compatible message fields and profiles.
- Major: breaking message/schema/semantic changes.

Release gates are tracked in `docs/RELEASE_CHECKLIST.md`. A release MUST NOT
claim more than the checklist evidence supports.

## Future profiles

- ROS 2 profile
- VDA5050 authorization profile
- MCP tool profile
- A2A agent-agent profile
- Network-state profile
- Audit export profile
