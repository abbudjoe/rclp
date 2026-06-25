# Why Not ROS, VDA5050, MCP, Or A2A?

These systems move commands, state, missions, tools, media, or coordination
data. RCLP adds a narrow capability-authority layer that decides whether a
selected high-authority robot capability is currently authorized under
identity, mission, local state, observed network state used as an authorization
input, geofence, lease, and fallback constraints.

For more background, see `docs/WHY_NOT_EXISTING_PROTOCOLS.md`.

| System | What it does | What RCLP does not replace | What RCLP adds |
|---|---|---|---|
| ROS 2 / DDS | Provides robot middleware for topics, services, actions, nodes, and message transport. | Middleware, ROS graph design, node permissions, message schemas, or robot runtime delivery. | A capability-authority decision before selected robot-facing actions pass through a robot-local authority gate. |
| ROS 2 Security / SROS2 | Adds identity, encryption, access control, and policy enforcement for ROS 2 communication. | ROS 2 authentication, encryption, access-control files, or secure transport configuration. | Short-lived capability leases tied to actor, robot, mission, capability, local state, observed network state used as an authorization input, fallback policy, and audit causality. |
| VDA5050 | Standardizes AGV/AMR order and state communication with a master control system. | Order semantics, state reports, action definitions, or fleet interoperability messages. | A local authority check for whether a central software actor may exercise a selected capability inside or adjacent to an order flow. |
| Open-RMF | Coordinates fleets, tasks, traffic, doors, lifts, and shared facility resources. | Fleet scheduling, traffic negotiation, facility integration, or task allocation. | A bounded robot-local authority gate for high-authority robot capabilities invoked by or near a coordinated fleet workflow. |
| MCP | Lets applications expose tools and context to AI systems. | Tool discovery, tool invocation, context sharing, or application-agent integration. | A physical capability lease check when a tool or software actor can affect robot behavior. |
| A2A | Coordinates communication and task handoff between software agents. | General agent messaging, negotiation, task routing, or agent collaboration. | A narrow central-software-actor to robot-local authority contract for selected physical capabilities. |
| Fleet managers | Dispatch, observe, coordinate, route, and operate robots across a fleet. | Dispatch, routing, scheduling, dashboards, operator workflows, or fleet policy UI. | A lease request and edge enforcement layer that can sit beside a fleet manager for selected high-authority actions. |
| Teleoperation systems | Manage operator sessions, video/media transport, controls, latency, and HMI. | Operator UI, media transport, joystick/control protocol, session management, or network path optimization. | A decision about whether `remote_assist` or operator velocity authority is allowed, degraded, revoked, denied, and audited. |
| Robot-local safety controllers | Enforce low-level safety behavior such as e-stop, braking, obstacle avoidance, and certified safety responses. | Certified safety functions, controls, braking, obstacle avoidance, hazard analysis, or formal safety cases. | A safety-adjacent authority layer above those systems; local safety remains authoritative for physical safety. |
| IoT/cellular connectivity platforms | Manage devices, telemetry, certificates, SIMs/eSIMs, carrier integrations, and network operations. | Connectivity management, carrier APIs, SIM lifecycle, network service operations, device telemetry, or network operations. | Use observed network state as an authorization input; RCLP does not guarantee connectivity. |

## Core distinction

RCLP is not a fleet manager, teleop system, middleware, carrier platform, or
certified safety controller. It asks a narrower question:

> Should this central software actor have a short-lived, locally enforceable
> lease for this selected robot capability, in this mission, under the current
> local conditions?
