# Customer Call Packet

## One-Liner

RCLP is an open protocol MVP for short-lived capability leases between
central/fleet agents and robot-local edge agents operating robots.

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

- central-agent capability request
- edge-side local verification
- signed/scoped/expiring lease semantics
- denial/revocation on stale, unauthorized, unsuitable, or context-mismatched authority
- network/geofence-conditioned decision
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

- Does this map to a real authority gap in your robot fleet?
- Where would this live in your stack?
- Which actor would request leases today?
- Would you first run this observe-only?
- What conditions should gate remote assist/autonomy escalation?
- What audit trail do you need after an incident?

Additional useful questions:

- Which current systems would RCLP need to compose with first?
- Which capabilities would be high-authority enough to gate?
- Who would own policy, fallback definitions, and audit replay?
- What evidence would make this worth a deeper pilot conversation?

## Suggested Close

The ask is technical validation, not adoption. We want to know whether this
authority primitive is real, where it would fit, which assumptions are wrong,
and what evidence an operator or platform team would need next.
