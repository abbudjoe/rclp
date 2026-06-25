# Deployment Shapes for Validation

The MVP proves the authority primitive; it does not yet prescribe whether the
authority gate is packaged as a ROS 2 node, gateway plugin, sidecar process,
or embedded library.

Use this page during validation calls when a reviewer asks, "Where would this
fit in my stack?"

| Existing stack shape | Where RCLP would sit | Capability authority requester | Selected path it could gate | Observe-only starting point | What RCLP does not replace |
|---|---|---|---|---|---|
| ROS 2 robot | Beside the ROS 2 graph or as a robot-local authority gate before selected actions, services, or command topics. | Remote-assist service, operator-session controller, fleet service, or autonomy module. | `remote_assist`, operator velocity commands, bounded recovery actions, or temporary speed-envelope changes. | Subscribe to or mirror selected command intents, evaluate allow/deny/degrade, and write audit records without blocking ROS 2 traffic. | ROS 2, DDS, SROS2, node graph design, action semantics, or robot safety controllers. |
| Proprietary robot gateway | Inside or beside the robot gateway that already translates cloud/fleet commands into robot-local commands. | Gateway-facing fleet service, remote-assist service, or autonomy module. | Gateway command routes that can affect motion authority, recovery behavior, or geofence-sensitive actions. | Evaluate a shadow copy of gateway command requests and emit audit decisions while the existing gateway remains authoritative. | Gateway transport, command translation, hardware abstraction, or local controls. |
| Teleop or remote-assist service | Before remote-assist commands cross from the operator/session service into the robot-local command path. | Teleop session manager, operator-session controller, or remote-assist orchestration service. | Enabling joystick assist, operator velocity commands, bounded recovery, or escalation from advisory to command-producing mode. | Record whether each operator-control session would have been allowed, denied, degraded, or revoked under RCLP policy. | Operator UI, media transport, session management, joystick/control protocol, or HMI. |
| Fleet manager | Beside the fleet manager as an authority check for selected high-authority requests, not as the scheduler itself. | Fleet manager, fleet ops service, task orchestrator, or autonomy supervisor. | Recovery behavior, autonomy escalation, temporary speed envelope, crossing assist, or dock recovery. | Evaluate selected fleet-manager requests in advisory mode and report whether scoped authority would have been granted. | Dispatch, routing, scheduling, task assignment, dashboard, or fleet policy UI. |
| Autonomy module | At the boundary where an autonomy module moves from advisory output into robot-facing command authority. | Autonomy module, supervisor, or fleet autonomy service. | Autonomy escalation, bounded recovery behavior, speed-envelope changes, or geofence-sensitive maneuvers. | Log when autonomy would have required scoped authority before producing robot-facing commands. | Perception, planning, behavior trees, controls, low-level safety, or model inference. |

## Validation questions for each shape

- Which component already decides that this actor may influence robot behavior?
- Where could a robot-local authority gate observe selected command intent
  without blocking commands on day one?
- Which command paths are high-authority enough to require a short-lived lease?
- Which local state source would provide mission, geofence, and observed network
  state used as an authorization input?
- Which team would own policy approval and incident review?
- What false-denial, latency, or operational risk would make hard gating
  unacceptable?
