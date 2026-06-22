# Demo Script

This is a 5-minute technical validation flow for a robotics/platform engineer.
Use it to show what the MVP proves and where the boundary is.

## Setup

From a fresh checkout:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

## Flow

1. Explain central-agent <-> edge-agent authority negotiation.

   RCLP does not send raw high-authority commands directly from a central
   actor to a robot-local command path. The central actor requests a physical
   capability, and the edge evaluates local policy and context before authority
   passes.

2. Run tests.

   ```bash
   python -m compileall src tests
   pytest
   ```

   If Rust is installed:

   ```bash
   cargo test --workspace
   ```

3. Run the local demo.

   ```bash
   python -m rclp_agents.demo_remote_assist
   ```

4. Show the allow path.

   Point to `normal_network_decision` and `command_gate_with_valid_lease`.
   Expected reason codes: `POLICY_SATISFIED` and `LEASE_VALID`.

5. Show deny, revoke, and degrade paths.

   Point to `command_without_valid_lease`, `impaired_network_decision`,
   `lease_revocation`, and `command_gate_after_network_revocation`.
   Expected reason codes include `NO_LEASE`, `NETWORK_LATENCY_DEGRADED`,
   `NETWORK_PROFILE_REVOKE`, and `LEASE_REVOKED`.

   Run a hard-deny profile:

   ```bash
   python -m rclp_agents.demo_remote_assist --network-profile uplink_bad
   ```

   Expected impaired reason code: `NETWORK_UPLINK_TOO_LOW`.

6. Show audit replay.

   Point to `audit_jsonl` and `incident_replay_summary`. The replay should
   reconstruct request, state, decision, enforcement, revocation, and fallback
   events for the same correlation ID.

7. Explain Python reference and Rust verifier spike.

   The Python implementation is the MVP reference for policy, leases, demo,
   command gate, and audit. The Rust crate is a deterministic edge verifier
   spike with offline vectors and test-only HMAC crypto. See
   `docs/RUST_EDGE_VERIFIER.md`.

8. Explain what remains unproven.

   This MVP does not prove formal safety certification, production robot
   safety, real cellular behavior, carrier APIs, production cryptographic trust
   infrastructure, customer willingness to deploy, full robot hardware
   integration, or hosted commercial-platform behavior.

## Closing Statement

RCLP is a safety-adjacent authority layer for scoped, short-lived physical
capability leases. It is ready for controlled technical validation of the
authority primitive, not production deployment.
