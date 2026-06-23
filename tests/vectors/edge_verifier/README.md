# Edge Verifier Vectors

These JSON fixtures are shared conformance inputs for edge-side RCLP lease
verification. They are deterministic and require no ROS 2, Isaac Sim, network
access, filesystem access from core verifier logic, or wall-clock time.

The current spike uses `RCLP-DEV-HMAC-SHA256`: HMAC-SHA256 over canonical JSON
lease claims using sorted keys and no insignificant whitespace. Separate dev
HMAC domains cover signed commands and signed local context fields so command
actor identity, network state, and geofence state cannot be treated as authority
inputs unless they are bound to authenticated local identities. The lease
signature excludes `input.lease.signature`; the command signature excludes
`input.command.signature`; the local context signature excludes
`input.local_context.signature`.

Each vector keeps untrusted lease, command, and local observed state under
`input`. Trusted local verifier state is under `trusted_context`, including
the accepted policy id/digest, local accepted capabilities,
issuer-to-capability scopes, per-capability constraint requirements, trusted
command agents, and dev HMAC secrets; replay-cache seed state is under
`seen_nonces`.

The shared lease test secret is `dev-test-secret`, the shared command test
secret is `command-dev-test-secret`, and the shared local-state test secret is
`state-dev-test-secret`. All are carried in each vector's `trusted_context`.
They are not production keys.
