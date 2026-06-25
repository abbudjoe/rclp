# Customer Validation Memo

For the concise sendable packet, use `docs/CUSTOMER_CALL_PACKET.md`. This memo
keeps the longer validation questions and framing.

## One-Liner

RCLP is an open protocol MVP for short-lived capability leases between
central/fleet agents and robot-local edge agents operating robots.

## Problem Statement

Robotics teams often have mature systems for missions, commands, telemetry,
fleet coordination, and local robot safety. The gap RCLP explores is authority:
who or what is allowed to make this robot exercise this physical capability
right now, under current mission, geofence, network, and fallback conditions.

## What The MVP Proves

- A central agent can request a scoped physical capability instead of sending a
  raw high-authority command.
- A robot-local edge path can evaluate local context and policy before issuing
  authority.
- A short-lived signed lease can gate command execution.
- Degraded or unsuitable network state can deny, degrade, or revoke authority.
- Missing, stale, invalid, mismatched, expired, or revoked leases are rejected.
- Audit replay can reconstruct the authority chain.

## Feedback Being Sought

We are seeking technical validation of whether this authority primitive maps to
real robotics workflows, especially remote assist, autonomy escalation,
incident reconstruction, and software-agent permissioning.

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
   local lease or gate?
3. Do you already condition remote assist or autonomy escalation on network
   state?
4. What robot-local state must be checked before authority can pass?
5. How do you revoke authority today when context changes mid-mission?
6. What audit chain would you need after an incident involving remote assist or
   an autonomy module?
7. Would an observe-only or advisory mode be useful before command gating?
8. Which existing systems would RCLP need to compose with first: ROS 2,
   VDA5050, Open-RMF, MCP, A2A, or a proprietary stack?
9. What would make an edge-side command gate unacceptable operationally?
10. What production hardening would be mandatory before a pilot?
11. What evidence would convince your platform or safety engineering team that
    the authority primitive is worth deeper evaluation?
12. Who would own policy, fallback definitions, and incident replay inside your
    organization?
