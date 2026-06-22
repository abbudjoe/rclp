# rclp-edge-verifier

Minimal Rust spike for the robot-local RCLP lease verifier.

The crate is pure library code. It does not call the system clock, open files,
perform network I/O, or integrate with ROS 2. Callers supply the command,
signed lease, and local observed context separately from trusted verifier
context, which carries issuer trust roots, the dev HMAC secret, revocation
state, current verifier time, and local lease TTL/age policy limits.

The current vector crypto profile is `RCLP-DEV-HMAC-SHA256`, a deterministic
test-only HMAC over canonical lease claims. It exists so shared JSON vectors can
run offline. It is not a production signature profile.

Run from the repository root:

```bash
cargo test --workspace
```
