# First-Call Target Profile

Use this profile to prioritize the first 5-8 controlled technical validation
calls. The goal is not broad market coverage; it is to find operators and
platform teams with a concrete central-agent to edge-agent authority gap.

## Best-Fit Customers

- outdoor mobile robot fleets
- sidewalk/campus delivery robots
- field inspection robots
- construction/surveying robots
- agriculture robots
- security patrol robots
- teleop/remote-assist-heavy fleets

## Personas

- Head of Robot Operations
- Head of Teleoperation
- Fleet Reliability Lead
- Robotics Platform Engineer
- Autonomy Infrastructure Lead
- Safety/Compliance Lead

## Strong-Fit Traits

- uses remote assist or teleop
- has edge runtime or robot-side daemon
- has central fleet orchestration
- cares about network/geofence/mission state
- has fragmented incident audit
- expects more AI-assisted operations

Additional strong signals:

- can name a high-authority capability that should be gated
- has autonomy escalation or degraded-network procedures
- already runs robot-local policy or safety-adjacent software
- wants observe-only evidence before enforcement
- has painful post-incident reconstruction workflows

## Bad-Fit Traits

- no remote assist/autonomy escalation
- purely indoor predictable Wi-Fi AMR workflow
- no willingness to run edge component
- no operational pain around authority/audit

Additional weak signals:

- only wants a hosted SaaS before validating the open primitive
- treats all command authority as already solved inside a fleet manager
- cannot identify a policy owner for capability authority
- has no stakeholder who owns incident replay or remote-assist risk

## Discovery Priorities

In the first calls, optimize for learning:

- whether the authority primitive maps to a real workflow
- which actor would request a lease
- where an edge-side verifier could live
- which local conditions should gate authority
- what fallback declarations would mean operationally
- what audit chain is needed after an incident
- whether observe-only mode would be a credible first step

## Recommended First Ask

Ask for a technical validation conversation with a platform or operations owner:

> We have an open MVP for short-lived robot capability leases between central
> agents and robot-local edge runtimes. We are not asking you to deploy it. We
> want to validate whether this authority boundary exists in your stack and
> what evidence would make it worth deeper evaluation.
