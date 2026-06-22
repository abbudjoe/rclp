# Codex Prompt — T3 Edge Agent + Command Gate

You are building the edge-side enforcement proof. Read `AGENTS.md`, `docs/ARCHITECTURE.md`, `docs/SECURITY_DOCTRINE.md`, and `src/rclp_ros2/command_gate.py`.

Goal: prove that the edge agent rejects commands without valid authority.

Tasks:

1. Implement or refine a command gate that accepts a command only with a valid, unexpired lease matching robot, mission, agent, and capability.
2. Add revocation handling.
3. Add fallback event emission on deny/revoke/degrade.
4. Keep ROS 2 integration as a scaffold; do not require ROS 2 in unit tests.
5. Add tests for no lease, expired lease, revoked lease, wrong robot, wrong capability, and valid lease.

Acceptance criteria:

- Tests pass without ROS 2 installed.
- Edge enforcement semantics are clear enough to later wire to ROS 2 topics/services/actions.
