# Stack Placement

## Where RCLP runs

RCLP runs between central software actors and a robot-local authority gate. A
robot-local authority service handles policy and lease decisioning; the
authority gate enforces the result near the robot-facing command path.

The MVP proves the authority primitive; it does not yet prescribe whether the
authority gate is packaged as a ROS 2 node, gateway plugin, sidecar process, or
embedded library. See `docs/DEPLOYMENT_SHAPES.md` for common validation-call
deployment shapes.

## What calls it

A remote-assist service, operator-session controller, fleet service, autonomy
module, or other central software actor can submit a capability authority
request. In this repo, "agent" means that kind of software actor; it does not
imply an LLM, chatbot, or fully autonomous fleet manager. A future caller could
be an AI agent, but RCLP is not an LLM-control product.

## What it gates

RCLP gates selected high-authority robot capabilities, for example:

- `remote_assist`: allow a remote operator or central service to influence robot behavior
- `operator_velocity_control`: allow a remote-assist service or operator-session controller to send bounded velocity commands
- `recovery_behavior`: allow a robot to execute a bounded recovery maneuver after getting stuck
- `autonomy_escalation`: allow a software actor to move from advisory mode to command-producing mode
- `temporary_speed_envelope`: allow a higher speed limit for a bounded mission segment under local constraints
- `geofence_sensitive_maneuver`: allow a robot to perform an action that is valid only inside a specific zone
- `crossing_assist`: allow bounded assistance for a crossing or right-of-way-sensitive maneuver
- `dock_recovery`: allow bounded recovery behavior around docking or undocking

## What it does not touch

RCLP does not carry teleoperation media, replace mission planning, schedule
fleets, manage carrier connectivity, implement robot controls, or decide that a
motion is physically safe.

## What remains owned by the robot safety stack

Local robot autonomy and safety systems remain responsible for planning,
controls, braking, emergency stop, obstacle avoidance, and certified or
site-specific safety behavior. RCLP is a safety-adjacent authority layer, not a
certified safety system.

| Layer | Example systems | Role | RCLP relationship |
|---|---|---|---|
| Fleet manager | Viam, Formant, custom fleet ops | Dispatch, observe, coordinate | May request leases; not replaced |
| Remote-assist service | Teleop session manager, operator UI | Human/operator intervention | May request `remote_assist` authority |
| Central software actor | Remote-assist service, operator-session controller, fleet service, autonomy module | Requests capability authority | RCLP caller |
| Authority service | RCLP reference implementation | Issues allow/deny/degrade decisions | Core protocol |
| Robot-local authority gate | Robot-local verifier / command gate | Enforces lease locally | Core enforcement point |
| Robot middleware | ROS 2, custom C++, DDS | Carries commands/actions | Selected commands may be gated |
| Robot autonomy/safety | planning, controls, e-stop, braking | Local robot behavior and safety | Not replaced |
| Audit sink | logs, SIEM, incident review | Records decisions | Receives RCLP audit events |

```text
Remote-assist service / operator-session controller / fleet service / autonomy module
        |
        | capability authority request
        v
Robot-local authority service / lease issuer
        |
        | signed short-lived lease
        v
Robot-local authority gate
        |
        | gated command path
        v
ROS 2 / robot middleware / robot gateway
        |
        v
Robot autonomy + local safety systems
```

## RCLP can start observe-only

RCLP does not have to block robot commands on day one.

In observe-only mode, RCLP would record allow/deny/degrade decisions without
blocking commands.

Adoption path:

1. observe-only audit
2. advisory allow/deny/degrade decisions
3. soft gating for non-critical capabilities
4. hard gating for selected high-authority capabilities
5. production-hardened edge enforcement after customer-specific safety review

## Policy ownership

In a production program, policy ownership would likely sit with the team that
already owns robot operational risk: safety/reliability/autonomy/platform, not
with the protocol itself.

Use `docs/POLICY_OWNERSHIP.md` to discuss who defines, approves, deploys,
monitors, and reviews capability policies.
