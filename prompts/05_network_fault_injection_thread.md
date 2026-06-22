# Codex Prompt — T5 Network Fault Injection

You are implementing deterministic network-state simulation. Read `docs/TEST_STRATEGY.md` and `docs/LAMBDA_ISAAC_SIM_SETUP.md`.

Goal: make network state a policy input and a demo lever.

Tasks:

1. Add deterministic network profiles: `normal`, `degraded_teleop`, `uplink_bad`, `partition`.
2. Ensure policy evaluation can deny/degrade based on latency, packet loss, and uplink estimate.
3. Add optional documentation for Linux `tc netem` scripts, but do not make tests require root or system network changes.
4. Add tests proving degraded state affects authority.

Acceptance criteria:

- Unit tests are deterministic.
- Demo can switch profile and show policy effect.
