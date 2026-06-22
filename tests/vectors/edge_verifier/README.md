# Edge Verifier Vectors

These JSON fixtures are shared conformance inputs for edge-side RCLP lease
verification. They are deterministic and require no ROS 2, Isaac Sim, network
access, filesystem access from core verifier logic, or wall-clock time.

The current spike uses `RCLP-DEV-HMAC-SHA256`: HMAC-SHA256 over canonical JSON
lease claims using sorted keys and no insignificant whitespace. The signature
covers `input.lease.claims` only and excludes `input.lease.signature`.

Each vector keeps untrusted lease, command, and local observed state under
`input`. Trusted local verifier state is under `trusted_context`; replay-cache
seed state is under `seen_nonces`.

The shared test secret is `dev-test-secret` and is carried in each vector's
`trusted_context`. It is not a production key.
