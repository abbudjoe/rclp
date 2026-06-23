# Security Review Notes

Date: 2026-06-22

Scope: T8 security red-team pass over the local protocol MVP, security doctrine,
threat model, and test suite.

## Fixed In T8

- Added explicit negative tests for replayed request nonces, stale requests,
  stale leases, wrong agent, wrong robot, wrong mission, wrong capability,
  expired leases, revoked leases, invalid signatures, unknown requesting
  agents, unknown lease issuers, unknown revocation actors, and policy-scope
  downgrade.
- Added a durable `RequestReplayCache` contract for duplicate
  `(requesting_agent_id, request_nonce)` rejection in the policy path.
- Added signed `CapabilityRequest` authentication with authenticated actor
  matching and negative tests for invalid signatures and actor mismatch.
- Added request age rejection and lease age/TTL rejection.
- Changed policy scope checks to fail closed when authority allow-lists are
  removed or empty.
- Added accepted policy digest checks so permissive policy edits are rejected
  unless the edge accepts the exact active policy digest.
- Made the command gate require explicit trusted lease issuer and revoker sets.
- Added signed `RobotStateAssertion` verification and freshness checks before
  policy issuance.
- Made request replay protection mandatory for policy issuance.
- Added signed `LeaseRevocation` verification with trusted revoker keys,
  revocation freshness checks, and negative tests for missing, invalid, and
  stale revocation signatures, plus optional robot/mission/capability context
  conflict rejection.
- Made state-scoped command enforcement require fresh current local state and
  trusted edge state signatures, and enforce `max_speed_mps` command payload
  constraints including conflicting speed aliases.
- Expanded audit integrity proofs to bind replay-critical top-level audit
  context and require common envelope fields on JSONL import, not only payload
  hashes.
- Renamed the demo policy id from a safety-suggestive name to
  `remote-assist-authority-v0`.
- Replaced docs examples that implied network safety with
  network-suitability / fallback-hook language.

## Blockers Before Customer Pilots / Production-Profile Use

Controlled technical validation calls may proceed with the local MVP when the
non-claims are explicit: this is a protocol/reference implementation review,
not a customer pilot, production safety deployment, or hardened trust profile.

| Priority | Issue | Impact | Required fix |
|---|---|---|---|
| P0 | Policy authenticity is digest-pinned locally but not carried in signed policy bundles. | A deployment can reject unaccepted policy objects, but the repo does not yet define distribution, rotation, or signer authorization for policy manifests. | Require signed policy bundles or an authenticated policy manifest before customer pilots. |
| P1 | CapabilityDecision is not represented as a verified signed envelope at the edge. | The local demo issues leases directly after policy evaluation, but cross-boundary decisions still need origin and payload verification. | Add signed decision verification or constrain the MVP profile so only locally evaluated decisions can issue command-gate leases. |
| P1 | Replay tracking now uses a durable local store but lacks retention and compaction policy. | Operators need bounded storage and an explicit replay-window lifecycle. | Define nonce-retention windows, compaction, backup, and recovery behavior for production profiles. |
| P1 | The demo uses one public key input for lease verification. | Key rotation, multiple issuers, and issuer key id matching are not represented. | Add a small issuer registry keyed by `issuer_id` / `public_key_id`, with revoked-key tests. |
| P1 | Clock trust is assumed. | Request and lease staleness checks depend on local clock integrity. | Define clock-skew profile, monotonic-clock handling, and degraded behavior for clock uncertainty. |

## Future Hardening

- Hardware-backed keys, key rotation, certificate chains, secure boot, and
  attestation.
- Signed audit batches or append-only storage beyond the local hash-chain
  profile.
- Fleet-scale revocation propagation semantics during partitions.
- Rate limits and escalation paths for compromised but known central agents.
- Property tests or fuzz tests for malformed envelopes and boundary timestamps.
- Canonical serialization profile for all signed protocol messages.
- Adapter-specific conformance profiles for ROS 2, VDA5050, Open-RMF, MCP, and
  A2A.

## Wording Review

No production-safety claim is intentionally made by the current docs. The repo
continues to describe RCLP as a safety-adjacent authority layer, not a
certified safety system. Remaining terms such as `safe_alternatives` and
`crawl_to_safe_zone` are protocol/API labels for fallback-oriented outputs, not
claims that RCLP certifies physical safety.
