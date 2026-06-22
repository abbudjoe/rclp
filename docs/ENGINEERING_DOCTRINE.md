# Engineering Doctrine

## Build the smallest proof of the missing primitive

The primitive is not robot fleet dispatch. It is not a simulator. It is not a cloud dashboard. It is **bounded authority negotiation** between a central actor and an edge actor operating near a robot.

## Biases

- Protocol core before UI.
- Deterministic tests before demos.
- Local simulation before cloud/GPU complexity.
- Narrow spec before broad standard.
- Explicit non-goals before feature expansion.
- Open reference implementation before commercial platform.

## Core invariants

1. A high-authority command without a valid lease is rejected.
2. A lease is scoped to agent, edge agent, robot, mission, capability, and time window.
3. A lease can be invalidated by policy-relevant state changes.
4. Edge enforcement does not require cloud availability for already-cached policy decisions.
5. Every authority decision emits an audit event.
6. Fallback behavior is explicitly declared; it is not implied.
7. The protocol must compose with existing robot ecosystems.

## Design pressure

If a feature does not help answer “who is allowed to make this robot do this physical thing, right now, and under what conditions?” it is probably out of scope.
