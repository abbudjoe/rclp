# Why Not Existing Protocols?

RCLP is not replacing ROS 2, VDA5050, Open-RMF, MassRobotics AMR Interop, MCP,
A2A, fleet managers, teleop systems, or IoT connectivity platforms. It targets
a narrower central-agent to edge-agent authority negotiation gap.

Existing systems move state, missions, tools, messages, or commands. RCLP asks
whether a specific actor has bounded, current authority to exercise a specific
physical capability under current local conditions.

## ROS 2 / DDS Security

ROS 2 provides robot middleware for topics, services, actions, nodes, and
message transport. DDS Security can authenticate and protect communication at
the middleware layer.

RCLP sits above or beside that transport layer. It asks whether a central actor
should have authority to exercise a capability such as `remote_assist` for a
specific robot and mission under current network, geofence, lease, replay, and
revocation state.

## VDA5050

VDA5050 standardizes communication between AGV/AMR fleets and a master control
system, especially around orders, state, and interoperability.

RCLP is not an order schema or fleet-control protocol. It can complement a
mission/order protocol by gating whether a software actor has current authority
to issue or escalate a physical capability at the edge.

## Open-RMF

Open-RMF coordinates fleets, facilities, schedules, traffic, doors, lifts, and
multi-robot interoperability.

RCLP does not coordinate traffic or facilities. It focuses on local authority
enforcement and auditability for specific capabilities.

## MassRobotics AMR Interop

MassRobotics AMR Interop focuses on reporting AMR state and interoperability
signals across systems.

RCLP is not a fleet-state reporting format. It could consume local state as an
authorization input, but its core primitive is scoped authority leasing and
edge-side command gating.

## MCP

MCP helps applications expose tools and context to AI systems.

RCLP is not a tool-calling protocol. If an AI agent uses tools that can affect
physical robot behavior, RCLP can help decide whether that actor has current
authority to exercise the robot-facing capability.

## A2A

A2A-style agent protocols coordinate communication between software agents.

RCLP is narrower: it gates physical capability authority between a central or
fleet actor and a robot-local edge runtime. It does not try to become a general
agent messaging layer.

## Fleet Managers

Fleet managers handle scheduling, allocation, routing, state, policies,
operator workflows, and operational dashboards.

RCLP does not replace those systems. A fleet manager or agent may request a
lease, but the edge agent still enforces whether the requested authority is
valid under local conditions.

## Teleop Systems

Teleop systems handle operator sessions, video, controls, network paths,
latency management, and human-machine interaction.

RCLP does not carry teleop media or controls. It can gate whether a teleop or
remote-assist capability should be allowed, degraded, revoked, or denied.

## IoT Connectivity Platforms

IoT connectivity platforms manage devices, connectivity, telemetry,
certificates, SIMs/eSIMs, carrier integrations, and network operations.

RCLP does not manage connectivity. It treats network state as an authorization
input and can fail closed when network conditions are unsuitable for a
capability.

## Core Distinction

RCLP is a safety-adjacent authority layer. It composes with existing robot,
fleet, connectivity, and agent ecosystems by adding one explicit question:

> Does this actor have a short-lived, scoped, locally enforceable lease for
> this physical capability, on this robot, in this mission, under current local
> conditions?

That gap is narrower than fleet management, teleoperation, middleware,
interoperability, or general agent communication, and the MVP should be judged
against that narrower claim.
