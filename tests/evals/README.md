# RCLP Protocol Evals

Run the local adversarial eval harness from the repository root:

```bash
python tests/evals/eval_runner.py
```

The runner discovers `scenarios/*.yaml`, executes each scenario deterministically
against the Python reference policy and command gate, prints a pass/fail
summary, and writes `reports/latest.json`.

Scenario kinds:

- `policy_decision`: evaluates a capability request against policy and local
  state.
- `command_gate`: evaluates a robot-facing command against a lease and optional
  current local state.
- `malformed_input`: verifies malformed protocol input is denied without
  crashing the runner.
- `network_degrade_revokes`: exercises grant, degradation, revocation,
  rejection, fallback, and audit chain.
- `cloud_partition_expiry`: exercises cached lease use, partition denial of new
  authority, expiry rejection, fallback, and audit chain.

Keep new scenarios deterministic: set `now_unix_ms`, avoid external services,
and use expected decisions of `allow`, `deny`, or `degrade`. The runner
enforces the required T12 scenario registry and unique scenario names, so a
missing required scenario is a report failure.
