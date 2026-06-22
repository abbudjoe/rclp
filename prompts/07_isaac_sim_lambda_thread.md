# Codex Prompt — T7 Isaac Sim on Lambda

You are the simulation POC engineer. Read `docs/LAMBDA_ISAAC_SIM_SETUP.md`, `docs/ARCHITECTURE.md`, and `isaac_sim/README.md`.

Goal: prepare, then implement, the first Isaac Sim proof on Lambda.ai.

Tasks:

1. Convert the plan into a step-by-step checklist with commands where safe.
2. Add a minimal ROS 2 integration plan for gating a simulated command path.
3. Create a `isaac_sim/scenarios/remote_assist_gate.md` scenario file.
4. Add placeholders for scripts that launch local RCLP demo next to Isaac/ROS 2.
5. Do not hardcode Lambda credentials or account-specific details.

Acceptance criteria:

- A fresh engineer can follow the checklist on a Lambda instance.
- The first Isaac milestone gates simulated commands; it does not require real cellular or full autonomy.
