# Architecture

```text
Central fleet agent
  ├── requests capabilities
  ├── explains intent
  └── consumes decisions/audit
        │
        ▼
RCLP policy + lease layer
  ├── identity registry
  ├── policy evaluator
  ├── lease issuer
  ├── revocation service
  ├── audit sink
  └── conformance checks
        │
        ▼
Edge agent / robot-local daemon
  ├── verifies leases locally
  ├── observes network/geofence/robot state
  ├── gates command paths
  ├── emits fallback events
  └── buffers audit events
        │
        ▼
Robot autonomy + safety stack
  ├── perception
  ├── planning
  ├── controls
  ├── obstacle avoidance
  └── certified/local safety mechanisms
```

## Key boundary

The central agent requests authority. The edge agent enforces authority. The local robot safety stack handles physical safety constraints.

## MVP runtime components

- `rclp_core`: protocol models, policy evaluation, lease signing/verification, audit.
- `rclp_agents`: central and edge reference agents.
- `rclp_ros2`: command-gate scaffold for ROS 2 integration.
- `isaac_sim`: POC plan for simulated robot authority gating.
