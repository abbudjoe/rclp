# Customer Call Packet

## One-Liner

RCLP is an open protocol MVP for short-lived capability leases between
central software actors and robot-local edge authority services that mediate
selected robot capabilities.

In this repo, "agent" means a software actor. It may be a fleet service,
autonomy module, remote-assist service, operator-session controller, or AI
agent. It does not imply an LLM, chatbot, or fully autonomous fleet manager.

## Problem Statement

As robot fleets add central AI agents, edge AI, remote assist, and autonomy
escalation, teams need a way to decide and prove when authority is permitted to
pass from a central actor to a robot-local runtime under explicit policy and
local conditions.

Many stacks already move missions, telemetry, commands, tools, and operator
media. RCLP focuses on a narrower authority question:

> Is this actor currently allowed to exercise this physical capability on this
> robot, for this mission, under the current local conditions?

## What The MVP Proves

- capability authority request from a fleet service, autonomy module,
  remote-assist service, operator-session controller, or other central
  software actor
- robot-local edge authority-service verification
- signed/scoped/expiring lease semantics
- denial/revocation on stale, unauthorized, unsuitable, or context-mismatched authority
- decisions that use observed network state and geofence state as inputs
- local command-gating semantics
- audit replay
- adversarial eval coverage

The demo is deterministic and local. It uses non-production demo keys and
simulated network profiles.

## What It Does Not Prove

- production safety
- formal certification
- real robot deployment
- real cellular network behavior
- carrier API behavior
- customer willingness to adopt

It also does not provide a hosted control plane, fleet manager, teleoperation
system, billing system, customer account system, or certified safety
controller.

## Five-Minute Call Flow

1. Run `./scripts/run_validation_checks.sh` or show the latest passing output.
2. Run `./scripts/run_validation_demo.sh`.
3. Point to the allow path: `POLICY_SATISFIED` then `LEASE_VALID`.
4. Point to fail-closed behavior: `NO_LEASE`, degraded network, revocation, and
   `LEASE_REVOKED`.
5. Show `audit_jsonl` and `incident_replay_summary`.
6. Ask where this authority boundary would live in the stakeholder's stack.

Detailed speaker notes are in `docs/DEMO_WALKTHROUGH.md`.

## Feedback Sought

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

Example capabilities to test against: `remote_assist`,
`operator_velocity_control`, `recovery_behavior`, `autonomy_escalation`,
`temporary_speed_envelope`, `geofence_sensitive_maneuver`, `crossing_assist`,
and `dock_recovery`.

## Suggested Close

The ask is technical validation, not adoption. We want to know whether this
authority primitive is real, where it would fit, which assumptions are wrong,
and what evidence an operator or platform team would need next.
