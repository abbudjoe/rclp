# Isaac Sim POC Scaffold

This folder contains the first Lambda.ai + Isaac Sim proof plan for RCLP. Keep
it lightweight and protocol-oriented: the milestone gates simulated commands
with a local RCLP lease check. It does not attempt full autonomy, real cellular
validation, certified safety behavior, fleet dispatch, or hosted SaaS behavior.

## First Isaac Proof

Use Isaac Sim to show that a central-agent request cannot reach a simulated
robot command path unless the edge agent verifies a valid RCLP capability
lease. The important moment is the edge-side command gate rejecting a simulated
remote-assist command when the lease is missing, stale, revoked, or violates
current deterministic network state.

## Runbook

- Lambda checklist: `../docs/LAMBDA_ISAAC_SIM_SETUP.md`
- Scenario: `scenarios/remote_assist_gate.md`
- Local protocol proof:

  ```bash
  scripts/run_local_protocol_demo.sh
  ```

- ROS 2 gate placeholder:

  ```bash
  scripts/run_ros2_gate_demo.sh
  ```

## Scripts

- `scripts/setup_lambda_instance.sh` checks local runtime prerequisites on a
  Lambda instance. It does not read credentials or install paid resources.
- `scripts/run_local_protocol_demo.sh` runs
  `python -m rclp_agents.demo_remote_assist` with a configurable deterministic
  impaired profile.
- `scripts/run_ros2_gate_demo.sh` is the placeholder entry point for a future
  ROS 2 adapter that calls `rclp_ros2.command_gate.CommandGate` before
  forwarding simulator commands.

All scripts must remain credential-free. Pass local paths and runtime choices
through environment variables such as `ISAAC_SIM_ROOT`, `ROS_DISTRO`,
`ROS_DOMAIN_ID`, `PYTHON_BIN`, and `RCLP_NETWORK_PROFILE`.
