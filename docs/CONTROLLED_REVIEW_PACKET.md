# Controlled Review Packet

This packet is the recommended external-review surface for controlled technical
validation of the RCLP protocol MVP. It is not a public launch bundle, standards
submission, production-readiness claim, or commercial-platform plan.

## Include

- `README.md`
- `LICENSE`
- `SECURITY.md`
- `CONTRIBUTING.md`
- `docs/VALIDATION_RELEASE_NOTES.md`
- `docs/SAFETY_BOUNDARY.md`
- `docs/COMMERCIAL_BOUNDARY.md`
- `docs/GOVERNANCE.md`
- `docs/PROTOCOL_SPEC_DRAFT.md`
- `docs/THREAT_MODEL.md`
- `docs/EVALS.md`
- `docs/DEMO_WALKTHROUGH.md`
- `docs/DEMO_SCRIPT.md`
- `docs/TECHNICAL_FAQ.md`
- `docs/WHY_NOT_EXISTING_PROTOCOLS.md`
- `docs/RUST_EDGE_VERIFIER.md`
- `src/`, `tests/`, `examples/`, `manifests/`, `scripts/`, and
  `crates/rclp-edge-verifier/`

## Exclude Unless The Reviewer Needs Planning Context

- `docs/FIRST_CALL_TARGET_PROFILE.md`
- `docs/PMF_RESEARCH_GUARDRAILS.md`
- `docs/ADOPTION_LADDER.md`
- `docs/FIELD_NOTES_TEMPLATE.md`
- `docs/NEXT_THREAD_MAP.md`
- `docs/POST_T12_SEQUENCE_PLAN.md`
- `docs/ASSEMBLY_LEDGER.md`

These files are not secret, but they are planning and discovery aids rather
than protocol-review artifacts. Keep them out of a standards-facing or broad
public packet unless intentionally reviewed first.

## Distribution Checks

- Do not send the packet until the project owner or private review channel for
  security reports is named.
- Confirm the packet is framed as controlled technical validation, not
  deployment approval.
- Keep hosted commercial platform, billing, customer accounts, carrier/MVNO
  integration, managed connectivity, and proprietary customer workflows out of
  the packet.
- Do not include real customer data, field logs, account identifiers, cloud
  credentials, private keys, API tokens, pricing, or carrier-contract details.
- Keep safety language anchored to "safety-adjacent authority layer",
  "fallback hook", "network-state-aware authorization", and "sim proof".

## Recommended Opening Note

RCLP is an open protocol MVP for short-lived capability leases between
central/fleet agents and robot-local edge agents. The goal of this packet is
technical validation of the authority primitive. It does not claim production
robot safety, formal certification, real cellular behavior, customer adoption,
or hosted commercial-platform readiness.
