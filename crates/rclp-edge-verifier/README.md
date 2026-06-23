# rclp-edge-verifier

Minimal Rust spike for the robot-local RCLP lease verifier.

The crate is pure library code. It does not call the system clock, open files,
perform network I/O, or integrate with ROS 2. Callers supply the command,
signed lease, and signed local observed context separately from trusted
verifier context, which carries issuer trust roots, dev lease/command/state
HMAC secrets, command-agent and state-edge trust roots, accepted policy
id/digest pins, accepted capabilities, issuer-to-capability scopes,
per-capability constraint requirements, revocation state, current verifier
time, and local lease/command/state TTL/age policy limits.

The verifier consumes lease nonces through `ReplayCache::consume_nonce()`, a
single check-and-mark operation. The crate does not export a default in-memory
cache; callers must provide replay storage, and production callers should use
durable shared storage with the same atomic contract.

The current vector crypto profile is `RCLP-DEV-HMAC-SHA256`, a deterministic
test-only HMAC over canonical lease claims plus separate HMACs over canonical
command and local context fields. It exists so shared JSON vectors can run
offline. It is not a production signature profile.

Run from the repository root:

```bash
cargo test --workspace
```
