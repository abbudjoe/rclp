# Customer Validation Memo

For the concise sendable packet, use `docs/CUSTOMER_CALL_PACKET.md`. This memo
keeps the longer validation questions and framing.

## One-Liner

RCLP is an open protocol MVP for short-lived capability leases between
central software actors and robot-local edge authority services that mediate
selected robot capabilities.

In this repo, "agent" means a software actor. It may be a fleet service,
autonomy module, remote-assist service, operator-session controller, or AI
agent. It does not imply an LLM, chatbot, or fully autonomous fleet manager.

## Problem Statement

Robotics teams often have mature systems for missions, commands, telemetry,
fleet coordination, and local robot safety. The gap RCLP explores is authority:
who or what is allowed to make this robot exercise this physical capability
right now, under current mission, geofence, network, and fallback conditions.

## What The MVP Proves

- A fleet service, autonomy module, remote-assist service,
  operator-session controller, or other central software actor can request
  scoped authority instead of sending a raw high-authority command.
- A robot-local edge authority service can evaluate local context and policy
  before issuing authority.
- A short-lived signed lease can gate command execution.
- Degraded or unsuitable observed network state used as an authorization input
  can deny, degrade, or revoke authority.
- Missing, stale, invalid, mismatched, expired, or revoked leases are rejected.
- Audit replay can reconstruct the authority chain.

## Feedback Being Sought

We are not asking whether you would buy this today.

We are asking:

- whether this authority boundary exists in your stack
- where it would live
- which capabilities would require scoped authority
- whether observe-only mode would be useful
- what evidence would make this worth a pilot
- what existing systems this would conflict with or complement

The first validation target is not production enforcement. It is whether an
observe-only or advisory authority layer would produce useful audit, denial,
degradation, or integration evidence in real robot operations.

In observe-only mode, RCLP would record allow/deny/degrade decisions without
blocking commands.

In a production program, policy ownership would likely sit with the team that
already owns robot operational risk: safety/reliability/autonomy/platform, not
with the protocol itself.

## Explicit Non-Claims

- This is not a certified safety system.
- This is not production robot safety.
- This does not prove real cellular behavior or carrier API behavior.
- This does not include production key management or hardware roots of trust.
- This does not include a hosted control plane, customer accounts, billing, or
  managed policy UI.
- This does not prove willingness to deploy or buy.

## Validation Questions

1. Where does authority currently live between your fleet/control systems and
   robot-local execution?
2. Which capabilities would you consider high-authority enough to require a
   local lease or gate, such as `remote_assist`,
   `operator_velocity_control`, `recovery_behavior`,
   `autonomy_escalation`, `temporary_speed_envelope`,
   `geofence_sensitive_maneuver`, `crossing_assist`, or `dock_recovery`?
3. Do you already condition remote assist or autonomy escalation on network
   state?
4. What robot-local state must be checked before authority can pass?
5. How do you revoke authority today when context changes mid-mission?
6. What audit chain would you need after an incident involving remote assist or
   an autonomy module?
7. Would an observe-only or advisory mode be useful before command gating?
8. Which existing systems would RCLP need to compose with first: ROS 2,
   VDA5050, Open-RMF, MCP, A2A, or a proprietary stack?
9. What would make a robot-local command gate unacceptable operationally?
10. What production hardening would be mandatory before a pilot?
11. What evidence would convince your platform or safety engineering team that
    the authority primitive is worth deeper evaluation?
12. Who would own policy, fallback definitions, and incident replay inside your
    organization?
