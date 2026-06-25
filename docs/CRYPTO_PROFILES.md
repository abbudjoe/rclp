# RCLP Crypto Profiles

Status: v0.0.1 development profiles for local technical validation. These
profiles are not production key-management, hardware-root, rotation, or
certification guidance.

## Canonical JSON

Signed MVP payloads use deterministic JSON before signature or HMAC verification.
The canonical form MUST:

- serialize the protocol model as JSON-compatible values;
- exclude the `signature` field from signed material;
- include the explicit signature algorithm field, either `signature_alg` for
  Python protocol messages or `alg` for Rust lease envelopes;
- sort object keys lexicographically;
- use UTF-8 encoded JSON text;
- use compact separators with no insignificant whitespace;
- reject unknown top-level or nested authority fields at trust boundaries before
  accepting authority.

Python implements this profile in `src/rclp_core/crypto.py` with
`canonical_json()`. Rust implements the matching deterministic JSON helper in
`crates/rclp-edge-verifier/src/canonical_json.rs` for vector verification.

## RCLP-DEV-ED25519

`RCLP-DEV-ED25519` is the Python MVP asymmetric development profile.

Rules:

- Signed trust-boundary messages MUST carry
  `signature_alg="RCLP-DEV-ED25519"` as signed material.
- Receivers MUST reject missing or unsupported `signature_alg` before signature
  decoding or verification.
- Signatures are URL-safe base64 Ed25519 signatures over canonical JSON.
- The canonical JSON excludes the `signature` field and includes all other signed
  fields, including protocol envelope, actor identity, context, timestamps, and
  signature algorithm metadata.
- Receivers MUST reject malformed base64, non-canonical base64 encodings,
  invalid signatures, and authenticated identity mismatches.
- Receivers SHOULD enforce pre-auth text and payload budgets before
  canonicalizing untrusted material.

This profile is used for Python `CapabilityRequest`, `RobotStateAssertion`,
`CapabilityLease`, `LeaseRevocation`, trust-boundary `FallbackDeclaration`,
`ControlPlaneReachabilityAssertion`, and `AuditBatchCommit` paths in the local
reference implementation.

## RCLP-DEV-HMAC-SHA256

`RCLP-DEV-HMAC-SHA256` is the Rust edge-verifier deterministic vector profile.

Rules:

- Lease envelopes MUST carry `alg="RCLP-DEV-HMAC-SHA256"`.
- Receivers MUST reject unknown algorithms before accepting authority.
- HMAC-SHA256 is computed over canonical JSON claims or command/context payloads
  excluding their `signature` fields.
- Separate development HMAC secrets are used for lease, command, and local-state
  vector material.
- The profile is test-only and exists so Rust vectors can run offline without
  production key distribution.

Rust currently verifies local edge command-gate vectors, not Python Ed25519
leases or signed Python revocation messages.

## Cross-Language Evidence

Run the local parity gate from the repository root:

```bash
python scripts/run_cross_language_conformance.py
```

The runner executes Python eval scenarios and Rust verifier vector tests when
Cargo is available, then writes
`tests/evals/reports/cross_language_latest.json`. It compares shared decision
semantics across mapped Python scenarios and Rust JSON vectors while preserving
each implementation's native reason codes in the report.

## Production Boundary

Before production security claims, RCLP needs a versioned production crypto
profile covering key identifiers, key rotation, revocation, hardware-backed or
managed trust roots, signed policy bundles, production canonicalization
stability, and cross-language asymmetric verification.
