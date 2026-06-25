# Observe-only Shadow-mode Sample Report

This is an illustrative report format for validation calls. It is not generated
from field data, it is not field evidence, and it does not claim production
readiness.

In observe-only mode, RCLP would record allow/deny/degrade decisions without
blocking commands.

## Sample scope

- Mode: observe-only audit
- Robot: `rover-001`
- Mission: `mission-001`
- Capability focus: `remote_assist`
- Existing command path: unchanged
- RCLP action: evaluate mirrored authority requests and command intents, then
  write audit decisions
- Robot behavior: not changed by this sample

## Sample summary

| Outcome | Count | Meaning in observe-only mode |
|---|---:|---|
| Would allow | 7 | Existing command intent had matching scoped authority under current local context. |
| Would deny | 3 | Existing command intent lacked valid authority or conflicted with local context. |
| Would degrade | 2 | Existing context suggested safe alternatives rather than full authority. |
| Would revoke | 1 | Previously valid authority would have been invalidated by changed local context. |

## Sample event excerpts

| Time | Actor | Capability | Existing command intent | RCLP shadow decision | Reason code | Audit impact |
|---|---|---|---|---|---|---|
| 10:14:08 | `remote-assist-service` | `remote_assist` | enable joystick assist | would allow | `POLICY_SATISFIED` | request, state, lease, and command intent recorded |
| 10:16:42 | `operator-session-controller` | `operator_velocity_control` | send bounded velocity command | would deny | `NO_LEASE` | missing authority event recorded; command not blocked in observe-only mode |
| 10:18:03 | `remote-assist-service` | `remote_assist` | continue operator assist | would degrade | `NETWORK_LATENCY_DEGRADED` | observed network state used as an authorization input; safe alternative recorded |
| 10:19:11 | `fleet-service` | `recovery_behavior` | bounded recovery maneuver | would deny | `GEOFENCE_CONSTRAINT_VIOLATED` | local geofence state and denial reason recorded |
| 10:20:29 | `robot-local-authority-gate` | `remote_assist` | continued use of prior lease | would revoke | `NETWORK_PROFILE_REVOKE` | revocation and fallback hook declaration recorded |

## Sample findings for a validation call

- A shadow gate would have produced useful denial evidence for missing scoped
  authority without interrupting the existing remote-assist session.
- Observed network state used as an authorization input would have triggered
  degradation before the operator-facing workflow saw a hard failure.
- Audit records would help incident review connect the requesting actor,
  mission, robot, local state, decision, and fallback hook.
- The customer still needs to validate whether each reason code maps to their
  operational language and escalation process.

## What this sample does not prove

- It does not prove robot safety, real cellular behavior, production security,
  customer willingness to deploy, or hard-gate operational acceptability.
- It does not replace a real shadow-mode run against customer telemetry and
  command streams.
