# Adapter Enforcement Contract

Status: MVP contract for future ROS 2, VDA5050, Open-RMF, MCP, and A2A
adapters.

RCLP adapters MUST NOT forward robot-facing commands directly from a central
agent, fleet manager, tool call, or transport callback to robot topics,
services, actions, order streams, or local execution hooks.

Every adapter path that can cause a physical capability to execute MUST call the
local `CommandGate` first and MUST use the resulting `GateResult` as the only
authority decision for that command.

Minimum adapter requirements:

- The adapter MUST preserve the command's authenticated actor, robot, mission,
  edge agent, capability, command id, command nonce, and payload through the
  gate call.
- The adapter MUST pass the presented `CapabilityLease` and fresh local
  `RobotStateAssertion` when the capability requires state-constrained
  authorization.
- The adapter MUST deny locally when `CommandGate` returns `allowed=false`.
- The adapter MUST NOT emit fallback hooks on command-authentication failures;
  fallback declarations are selected only by command-gate policy.
- The adapter MUST NOT create a parallel allowlist, topic allow rule, action
  bypass, or central-agent override that can execute a robot-facing command
  without a gate decision.
- The adapter MUST preserve or emit the gate audit id so enforcement can be
  causally linked to the command, lease, state, revocation, and fallback chain.

Current MVP coverage:

- `src/rclp_agents/edge_agent_daemon.py` is intentionally a narrow delegate to
  `CommandGate.evaluate`.
- `tests/test_protocol_flow.py` and `tests/test_security_negative_paths.py`
  cover daemon/gate mismatch and unauthenticated command rejection paths.

Future adapter PRs MUST add adapter-level negative tests proving that no
robot-facing route can bypass `CommandGate`.
