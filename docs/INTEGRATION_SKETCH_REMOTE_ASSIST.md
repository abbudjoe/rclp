# Integration Sketch: remote_assist

## Existing robot fleet components

- fleet manager
- remote-assist service
- robot-local gateway or edge runtime
- ROS 2 or equivalent robot command path
- local autonomy and safety controller
- telemetry/audit sink

## RCLP insertion point

RCLP sits before selected high-authority robot-facing commands. It evaluates a
capability authority request from a central software actor and gives a
robot-local edge authority gate enough signed, scoped context to allow, deny,
degrade, revoke, and audit command authority locally.

RCLP does not replace teleop media transport, operator UI, local autonomy, or
safety controllers.

The MVP proves the authority primitive; it does not yet prescribe whether the
edge gate is packaged as a ROS 2 node, gateway plugin, sidecar process, or
embedded library.

In observe-only mode, RCLP would record allow/deny/degrade decisions without
blocking commands.

## Example flow

1. Robot reports uncertainty, blockage, low confidence, or failed recovery.
2. Fleet service or remote-assist service requests `remote_assist` authority.
3. RCLP evaluates:
   - central software actor identity
   - robot identity
   - mission ID
   - requested capability
   - lease time window
   - local/geofence state
   - observed network state used as an authorization input
   - fallback policy
4. RCLP grants, denies, or degrades.
5. Robot-local edge authority gate accepts selected commands only while a valid lease exists.
6. If lease, network, geofence, or mission state becomes invalid, the gate rejects further high-authority commands and emits fallback/audit events.

## Example gated commands

- enabling joystick assist
- enabling operator velocity commands
- allowing a bounded recovery behavior
- raising a speed envelope temporarily
- authorizing an autonomy escalation
- allowing a geofence-sensitive maneuver

## Commands not gated by RCLP

- emergency stop
- local obstacle avoidance
- braking
- certified safety controller behavior
- low-level perception/planning internals

## What is audited

- requesting actor
- robot
- mission
- requested capability
- lease ID
- local/geofence state
- observed network state used as an authorization input
- allow/deny/degrade reason
- fallback declaration
- revocation or expiry event, if applicable
