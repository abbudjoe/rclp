# S4 — Open-source / Commercial-boundary Review

## Verdict

GREEN

The repository is suitable for controlled external technical validation when
reviewers are given the same narrow framing used in the README and validation
notes: protocol MVP, local deterministic evidence, no production deployment,
and no certified safety claim. I did not find sensitive commercial leakage
such as pricing, named customers, carrier contracts, proprietary integration
plans, local absolute paths in tracked files, or obvious committed production
credentials.

The prior yellow release-hygiene items have been remediated for controlled
validation: Rust and Python package metadata now align on Apache-2.0,
`SECURITY.md` no longer contains a placeholder reporting contact, and
`docs/CONTROLLED_REVIEW_PACKET.md` defines the external review surface and
excludes planning docs unless deliberately included. This fresh review pass
found no new controlled-validation blockers.

## Open-source posture

- The README clearly says this repo is an open protocol MVP and reference
  implementation, not the future hosted commercial platform.
- `docs/GOVERNANCE.md` keeps the protocol narrow, emphasizes
  interoperability, and states that the open protocol should not require a
  commercial hosted service.
- `CONTRIBUTING.md`, `SECURITY.md`, `docs/SAFETY_BOUNDARY.md`, and
  `docs/VALIDATION_RELEASE_NOTES.md` consistently describe controlled
  validation rather than public standardization or production readiness.
- License posture is clear enough for controlled validation: `LICENSE`,
  `pyproject.toml`, and `crates/rclp-edge-verifier/Cargo.toml` all declare
  Apache-2.0.
- `SECURITY.md` now directs controlled reviewers to the named project owner or
  private review channel that distributed the packet, avoids public disclosure
  of sensitive vulnerability details, and leaves monitored public security
  intake as a public-launch requirement.
- `docs/CONTROLLED_REVIEW_PACKET.md`, `docs/VALIDATION_RELEASE_NOTES.md`, demo
  docs, eval docs, and the technical FAQ invite concrete technical feedback on
  the protocol primitive without packaging the full planning backlog.

## Commercial-boundary assessment

- The protocol/commercial split is explicit in README and
  `docs/COMMERCIAL_BOUNDARY.md`. Hosted trust roots, customer accounts, billing,
  managed policy UI, fleet-scale audit backends, carrier/MVNO integrations,
  managed connectivity, enterprise IAM/SSO, commercial SLAs, and proprietary
  workflows are all out of scope for this repo.
- The repo does not include pricing, named customer lists, account-specific
  workflows, or named carrier strategy from the requested search targets.
- Some docs are more go-to-market-adjacent than protocol-adjacent:
  `docs/FIRST_CALL_TARGET_PROFILE.md`, `docs/PMF_RESEARCH_GUARDRAILS.md`,
  `docs/ADOPTION_LADDER.md`, `docs/FIELD_NOTES_TEMPLATE.md`, and parts of
  `docs/NEXT_THREAD_MAP.md`. `docs/CONTROLLED_REVIEW_PACKET.md` now excludes
  those files from the recommended external review packet unless a reviewer
  explicitly needs planning context.
- The commercial roadmap content is high-level and does not reveal carrier
  contracts, pricing, a customer list, or a proprietary integration plan.
- The repo invites useful technical review of the authority primitive, demo,
  conformance tests, threat model, and safety boundary while excluding planning
  and discovery aids from the default external packet.

## Safety/security wording risks

- Safety claims are conservative. The docs repeatedly use
  "safety-adjacent authority layer" and explicitly reject production safety,
  formal certification, field safety, real cellular behavior, and carrier API
  claims.
- Search hits for phrases such as "certified safety" and "production ready"
  were overwhelmingly negative statements, checklist reminders, or FAQ
  disclaimers. I did not find "certified safe", "guaranteed safe",
  "secure by default", "carrier-grade", "real-time guaranteed", or "formal
  safety system" used as positive claims.
- Terms like `safe_alternatives` and `crawl_to_safe_zone` remain in protocol
  examples and test fixtures. Existing docs already explain that these are
  fallback hooks or API labels, not certified safety behavior. Keep that
  explanation close to customer-facing demos.
- Security posture is honest about non-production demo keys, test-only HMAC
  vectors, missing production key management, clock-trust assumptions, and
  hardened-profile gaps.

## Sensitive references or local paths

- Tracked-source and review-packet scans found no local absolute paths.
  Non-`.git` scans were run with repository ignore rules, so ignored generated
  artifacts such as virtualenvs, build outputs, caches, and bytecode are not
  part of the review-packet evidence. Clean or exclude generated artifacts
  before packaging a local checkout.
- No obvious real secrets, API keys, bearer tokens, SSH private keys, cloud
  account IDs, or private keys were found in tracked files by targeted pattern
  search.
- The Rust edge verifier test vectors include deterministic dev HMAC fixture
  values under `tests/vectors/edge_verifier/`. They are documented as
  non-production test secrets and are expected for offline conformance vectors.
  Do not reuse them outside tests.
- Lambda and Isaac Sim docs use environment-variable placeholders for API keys,
  SSH keys, regions, images, and filesystem names. I did not find committed
  account-specific values.
- Requested company/carrier target search did not find sensitive named-company,
  customer-list, or pricing content except checklist statements saying such
  references must not be present.
- Evidence basis included tracked-file scans with `git ls-files -z | xargs -0
  rg` for the requested terms, a targeted secret-pattern scan, a tracked
  local-absolute-path scan, and source/review-packet scans with repository
  ignore rules for local paths, named-company references, and secret-shaped
  patterns.

## Blocking issues

- None for controlled external technical validation.
- Public launch still needs an intentionally monitored public security intake
  and any counsel review the owner wants for the Apache-2.0 release posture.
- Standards-facing or broad public releases should continue excluding planning
  and discovery docs unless they are explicitly reviewed for that audience.

## Recommended fixes

- No remaining repository implementation fixes are required before controlled
  external technical validation.
- `docs/CONTROLLED_REVIEW_PACKET.md` is the source of truth for external
  technical-review bundles and now carries the distribution checks for this
  review posture.
- The private security-reporting contact is a pre-distribution human gate:
  before any packet is sent, the sender must name the project owner or private
  review channel. `SECURITY.md` and `docs/CONTROLLED_REVIEW_PACKET.md` both
  state that external review should not begin until this channel exists.
- Continue to keep all safety language anchored to "safety-adjacent authority
  layer", "fallback hook", "network-state-aware authorization", and
  "sim proof".
- Continue to use deterministic local fixtures and labeled non-production keys
  for validation demos; do not add real customer logs, cloud identifiers,
  account names, pricing, carrier details, or proprietary workflows to this
  repo.
- Before assembling a packet from a local checkout, clean or exclude ignored
  generated artifacts such as virtualenvs, build outputs, caches, and bytecode.
