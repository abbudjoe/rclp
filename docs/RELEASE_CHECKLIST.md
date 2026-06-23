# Release Checklist

Use this checklist before tagging public releases. Keep release claims tied to
evidence in this repository.

## v0.0.1 - Local Protocol Proof

Scope: a local, dependency-light reference implementation for the
central-agent to edge-agent `remote_assist` lease primitive.

- README quickstart runs from a fresh checkout with Python 3.11 or newer.
- `docs/DEMO_WALKTHROUGH.md` matches current demo output.
- `docs/CONFORMANCE_CHECKLIST.md` matches `manifests/rclp_protocol_manifest.yaml`
  and `src/rclp_core/models.py`.
- Protocol spec, manifest, examples, and tests agree on message names and field
  names.
- Demo prints signed request, allowed lease, missing-lease rejection, impaired
  network decision, revocation, audit JSONL, and incident replay summary.
- Negative tests cover replay, stale request/state/lease, wrong context,
  invalid signatures, unknown actors, signed revocation, command constraints,
  and policy downgrade.
- Validation passes:

  ```bash
  python -m compileall src tests
  python -m pytest
  ruff check .
  ruff format .
  ```

- Public docs avoid certified-safety, field-proven, fleet-manager, teleop
  media, carrier/MVNO, and hosted SaaS claims.
- `LICENSE` contains the approved full license text before public release.
- No secrets, private keys, credentials, account IDs, or cloud-specific customer
  data are present.

## v0.1.0 - Public Protocol Seed

Scope: a first public protocol seed with a stabilized MVP conformance profile.

- Versioned schemas exist for all v0.1 protocol messages.
- Canonical serialization and signature profile are specified and tested.
- Signed `CapabilityDecision` verification is implemented or explicitly
  excluded from the v0.1 profile with a narrow local-only rationale.
- Signed `LeaseRevocation` verification has a versioned key-id and rotation
  profile, building on the local MVP signature check.
- Standalone `NetworkStateAssertion` and `FallbackDeclaration` authenticated
  envelope verification is implemented or explicitly scoped out of v0.1.
- Policy authenticity uses signed bundles or an authenticated policy manifest,
  not only local digest pinning.
- Issuer and revoker key registries support key IDs, rotation, and revoked-key
  negative tests.
- Clock-skew and request/lease staleness profile is normative and tested.
- Audit integrity profile is normative and tested for export/import/replay.
- Conformance tests can be run by third-party implementers without external
  services or host network mutation.
- Governance and versioning notes explain how fields, profiles, and adapters
  evolve without requiring a commercial hosted service.
- Security review notes separate v0.1 blockers from future hardening.
- Demo recording or transcript is regenerated from the tagged code.
- Public release notes state that RCLP is a safety-adjacent authority layer, not
  a certified safety system.
