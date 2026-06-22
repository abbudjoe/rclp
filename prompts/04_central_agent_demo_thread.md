# Codex Prompt — T4 Central Agent + Demo Flow

You are implementing the demo flow. Read `README.md`, `docs/API_STYLE.md`, and existing tests.

Goal: make `python -m rclp_agents.demo_remote_assist` a compelling local protocol demonstration.

Demo requirements:

1. Create a central agent and edge agent identity.
2. Create a robot, mission, geofence, and policy.
3. Request `remote_assist` under normal network conditions and show an allowed lease.
4. Degrade network conditions and show denial or revocation.
5. Attempt a command without a valid lease and show rejection.
6. Emit audit JSONL or structured console output.
7. Print a concise incident replay summary.

Acceptance criteria:

- Demo runs with no external services.
- Output is understandable by a robotics platform engineer.
- Demo does not imply formal safety certification.
