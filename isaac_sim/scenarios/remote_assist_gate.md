# Scenario - Remote Assist Gate

## Objective

Demonstrate that a simulated robot command path accepts `remote_assist`
commands only while a valid RCLP capability lease exists.

This is a sim proof of the authority layer. It is not certified safety
validation, real cellular validation, full autonomy, fleet dispatch, or a
hosted control plane.

## Authority Contract

- The central agent MAY request `remote_assist`.
- The edge agent MUST verify a lease locally before a simulated command is
  forwarded.
- Commands without a lease, with a mismatched lease, or after revocation MUST
  be rejected.
- Allow, reject, revoke, and fallback paths MUST be auditable.
- Network state is a policy input. The first milestone uses deterministic
  network profiles rather than real cellular impairment.

## Simulated Topology

```text
central-agent demo
  -> CapabilityRequest(remote_assist)
  -> policy decision + short-lived lease
  -> ROS 2 adapter candidate command
  -> RCLP CommandGate
  -> accepted simulator command topic
  -> Isaac Sim robot
```

The ROS 2 adapter is intentionally thin. It should translate ROS 2 messages
into the existing `rclp_ros2.command_gate.Command` model, call
`CommandGate.evaluate(...)`, and forward only allowed commands.

## Preconditions

- Lambda instance has GPU visibility (`nvidia-smi` succeeds).
- Repository dependencies are installed with `python -m pip install -e '.[dev]'`.
- `python -m rclp_agents.demo_remote_assist --network-profile degraded_teleop`
  succeeds locally on the instance.
- Isaac Sim is installed or mounted by an operator-approved workflow.
- ROS 2 Humble or Jazzy is available when testing the bridge.
- No Lambda credentials, SSH keys, or account identifiers are stored in this
  repository.

## Minimal Scene

Use the smallest mobile-robot scene that can expose a simulator-only command
path. The robot does not need full navigation or autonomy. It only needs enough
visible behavior to prove whether a command was forwarded or blocked.

Suggested simulator command payload:

```json
{
  "intent": "start_remote_assist",
  "max_speed_mps": 0.6
}
```

Suggested ROS 2 topic names for the first adapter:

| Topic | Direction | Purpose |
|---|---|---|
| `/rclp/remote_assist/request` | central/adapter -> gate | Candidate simulated command before authorization. |
| `/sim/remote_assist/accepted` | gate -> Isaac Sim | Forwarded command only after `CommandGate` allows it. |
| `/rclp/fallback` | gate -> observer | Fallback declaration after denial, expiry, or revocation. |
| `/rclp/audit` | gate -> observer | Audit event stream or pointer to JSONL audit output. |

## Steps

1. Launch Isaac Sim with a simple mobile robot scene and ROS 2 bridge enabled.
2. Source ROS 2 in the shell that runs the adapter.
3. Start the RCLP local protocol proof:

   ```bash
   isaac_sim/scripts/run_local_protocol_demo.sh
   ```

4. Start the ROS 2 gate placeholder or adapter:

   ```bash
   isaac_sim/scripts/run_ros2_gate_demo.sh
   ```

5. Under the deterministic `normal` profile, central-agent demo requests
   `remote_assist`.
6. Policy returns `allow` and issues a short-lived `CapabilityLease`.
7. The gate receives a candidate simulated command with matching
   `agent_id`, `edge_agent_id`, `robot_id`, `mission_id`, and `capability`.
8. `CommandGate.evaluate(...)` returns `allowed=True`.
9. The adapter forwards the command to the simulator-only accepted command
   topic.
10. Send a command without a lease. The gate rejects it and emits audit plus a
   fallback declaration.
11. Change deterministic network state to `degraded_teleop`, `uplink_bad`, or
   `partition`.
12. Policy denies, degrades, or revokes authority according to the profile and
   configured thresholds.
13. Attempt another `remote_assist` command with the old lease.
14. The gate rejects the command and does not forward it to Isaac Sim.
15. Confirm audit replay reconstructs request, state, decision, enforcement,
   revocation, and fallback.

## Expected Results

| Check | Expected result |
|---|---|
| Valid lease under normal deterministic network state | Command is forwarded to the simulator-only accepted topic. |
| Missing lease | Command is rejected with `NO_LEASE`. |
| Impaired profile after lease issuance | Decision degrades/denies or lease is revoked. |
| Command after revocation or violated constraints | Command is rejected and not forwarded. |
| Audit replay | Authority chain is visible in `incident_replay_summary`. |

## Evidence to collect

- Lambda instance type, region, image, and Isaac Sim version with no account
  identifiers.
- Exact Isaac Sim launch command.
- `run_local_protocol_demo.sh` output.
- ROS 2 topic list or adapter placeholder output.
- `audit_jsonl`.
- `incident_replay_summary`.
- Screenshot or recording from Isaac Sim if GUI or streaming is available.

## Rejection Conditions To Prove

- no lease;
- expired lease, if the adapter can force one during the run;
- wrong robot or wrong mission, if the adapter supports a malformed command
  fixture;
- revoked lease after deterministic network impairment;
- missing audit event for an authority-changing path.

The first required rejection is no lease. The first required impairment proof
is deterministic network-state-aware authorization; real cellular is out of
scope for this milestone.
