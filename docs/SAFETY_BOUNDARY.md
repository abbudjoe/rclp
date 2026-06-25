# Safety Boundary

RCLP is a safety-adjacent authority layer. It gates whether a software actor may
exercise a physical capability under explicit policy and local context.

RCLP gates software/agent authority. It does not replace certified robot safety
systems, low-level obstacle avoidance, braking, emergency stop, or formal safety
cases.

## What RCLP Does

- Requires a scoped, short-lived lease before selected high-authority commands
  can pass through the command gate.
- Lets the robot-local authority gate reject unsafe, stale, invalid,
  unauthorized, or context-mismatched requests locally.
- Treats network state, geofence state, mission state, and fallback policy as
  authorization inputs.
- Records authority-changing paths in audit events so the chain can be replayed.
- Provides fallback hooks as declarations to the local robot runtime.

## What RCLP Does Not Do

- It does not certify that a robot motion or fallback action is physically safe.
- It does not replace the robot's certified or local safety mechanisms.
- It does not implement braking, obstacle avoidance, emergency stop, motor
  control, perception, planning, or formal safety cases.
- It does not prove field safety or real cellular behavior.

## Robot-local Enforcement

For high-risk authority, edge enforcement should fail closed when required
inputs are missing, stale, invalid, unauthorized, or inconsistent. The
robot-local authority gate must be able to reject a command without calling a
cloud service.

Examples of fail-closed behavior in this MVP:

- no lease -> reject
- invalid signature -> reject
- unknown issuer -> reject
- expired or stale lease -> reject
- wrong robot, mission, software actor, authority gate, or capability -> reject
- network or geofence constraints violated -> reject
- known revocation -> reject

## Fallback Hooks

Fallback behavior must be defined by the robot operator and local robot runtime.
RCLP can declare fallback hooks such as `local_autonomy_only`,
`crawl_to_safe_zone`, or `hold_position`, but those declarations are not
certified safety behavior.

The fallback hook is an authorization and audit signal. The robot's local safety
controller remains responsible for physical safety.

## Certification Scope

Formal certification is out of scope for the MVP. Future safety-engineering
work would need qualified safety analysis, system-specific hazard analysis,
hardware/runtime evidence, and certification planning outside this reference
repo.
