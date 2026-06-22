# Lambda.ai + Isaac Sim POC Checklist

This checklist prepares the first RCLP Isaac Sim proof on a Lambda Cloud GPU
instance. It is intentionally narrow: the milestone demonstrates a
safety-adjacent authority layer gating simulated remote-assist commands. It
does not prove certified safety, real cellular behavior, full autonomy, fleet
dispatch, or hosted SaaS behavior.

## Source Contract

- `DIRECTION.md` Phase 7: explicit Lambda checklist, Isaac Sim ROS 2 bridge
  approach, minimal simulated robot scenario, and no full autonomy.
- `docs/PROTOCOL_SPEC_DRAFT.md`: edge enforcement MUST reject a physical
  command without a valid lease and MUST audit allow/reject paths.
- `isaac_sim/scenarios/remote_assist_gate.md`: first scenario to execute.

## Local Preflight

Run these on the machine where this repository is checked out before creating
or using a Lambda instance.

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
python -m compileall src tests
python -m pytest
python -m rclp_agents.demo_remote_assist --network-profile degraded_teleop
```

Expected local result:

- the demo grants `remote_assist` under the normal deterministic network
  profile;
- the command gate rejects a command without a lease;
- the impaired profile triggers denial/degrade/revocation behavior;
- `audit_jsonl` and `incident_replay_summary` are printed.

## Lambda Preflight

Do not commit `.env`, API keys, SSH private keys, account IDs, or Lambda
account-specific values. Keep credentials in local environment variables or in
the operator's Lambda account configuration.

Safe credential sanity check:

```bash
if [[ -f .env ]]; then
  set -a
  . ./.env
  set +a
fi
: "${LAMBDA_API_KEY:?set LAMBDA_API_KEY in .env or the shell}"
```

Safe read-only API smoke:

```bash
curl https://cloud.lambda.ai/api/v1/instances \
  -H "Authorization: Bearer ${LAMBDA_API_KEY}"
```

Before creating paid compute, choose and record:

- instance type with enough VRAM for the Isaac Sim version being used;
- region;
- SSH key name already registered in Lambda;
- persistent filesystem name or mount plan for Isaac assets and repository
  state;
- expected cleanup owner and stop/delete policy after the proof.

Operator action, paid compute:

```bash
export LAMBDA_REGION="<region>"
export LAMBDA_INSTANCE_TYPE="<gpu-instance-type>"
export LAMBDA_SSH_KEY_NAMES='["<registered-ssh-key-name>"]'
export LAMBDA_FILESYSTEM_NAMES='["<persistent-filesystem-name>"]'

curl -X POST https://cloud.lambda.ai/api/v1/instance-operations/launch \
  -H "Authorization: Bearer ${LAMBDA_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{
    \"region_name\": \"${LAMBDA_REGION}\",
    \"instance_type_name\": \"${LAMBDA_INSTANCE_TYPE}\",
    \"ssh_key_names\": ${LAMBDA_SSH_KEY_NAMES},
    \"file_system_names\": ${LAMBDA_FILESYSTEM_NAMES}
  }"
```

The launch command is a mutation. Run it only after the operator intentionally
chooses the region, instance type, SSH key, filesystem, and cleanup policy.

After launch, inspect instance status until an IP address is available:

```bash
curl https://cloud.lambda.ai/api/v1/instances \
  -H "Authorization: Bearer ${LAMBDA_API_KEY}"
```

## Instance Bootstrap

SSH into the Lambda instance, then clone or update this repository.

```bash
git clone <repo-url> rclp
cd rclp
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
python -m compileall src tests
python -m pytest
```

Run the credential-free environment check:

```bash
isaac_sim/scripts/setup_lambda_instance.sh
```

This script is a safe placeholder. It checks Python, GPU visibility, optional
ROS 2 availability, and whether an Isaac Sim root path has been provided. It
does not install Isaac Sim and does not read Lambda credentials.

## Isaac Sim And ROS 2 Bridge

Pick one Isaac Sim source and record it before running the proof:

| Option | Use when | Credential-free checks |
|---|---|---|
| Preinstalled image | The selected Lambda image already includes Isaac Sim or an Isaac Sim container. | `find / -maxdepth 4 -name 'isaac-sim.sh' 2>/dev/null | head` |
| Persistent filesystem | Isaac Sim assets or install state are already mounted from Lambda storage. | `mount | grep -i lambda || true`; `find /mnt -maxdepth 5 -name 'isaac-sim.sh' 2>/dev/null | head` |
| Container | The operator has approved a container image and license flow for the selected Isaac Sim version. | `docker --version`; `nvidia-smi`; record the image tag outside this repo. |

Do not store NVIDIA credentials, license tokens, Lambda API keys, SSH private
keys, or account-specific image names in this repository.

Set the Isaac root path if the scripts need it:

```bash
export ISAAC_SIM_ROOT="<directory-containing-isaac-sim.sh>"
export ROS_DISTRO="${ROS_DISTRO:-humble}"
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-42}"
```

Verify the Isaac root:

```bash
test -x "${ISAAC_SIM_ROOT}/isaac-sim.sh"
"${ISAAC_SIM_ROOT}/isaac-sim.sh" --help | head -n 40
```

ROS 2 setup depends on the Isaac Sim version and Python ABI. Current NVIDIA
Isaac Sim documentation notes that Isaac Sim 5.1 uses Python 3.11, dynamically
loads the ROS 2 backend from `ROS_DISTRO`, and can use internal ROS 2 libraries
when a compatible system ROS 2 environment is not sourced. Use the installed
Isaac Sim version's documentation as the final source of truth.

Source ROS 2 only in shells that need it and verify the distribution:

```bash
if [[ -f "/opt/ros/${ROS_DISTRO}/setup.bash" ]]; then
  source "/opt/ros/${ROS_DISTRO}/setup.bash"
fi
echo "ROS_DISTRO=${ROS_DISTRO:-unset}"
echo "ROS_DOMAIN_ID=${ROS_DOMAIN_ID}"
ros2 doctor --report
```

Enable the ROS 2 bridge extension for the installed Isaac Sim version. For
older Isaac Sim 4.x documentation, the ROS 2 bridge extension is named
`omni.isaac.ros2_bridge` and cannot be enabled at the same time as the ROS 1
bridge. Newer Isaac Sim versions may expose updated extension identifiers or
startup options; record the exact installed-version command used.

Headless launch template:

```bash
export RCLP_ISAAC_LAUNCH_COMMAND='${ISAAC_SIM_ROOT}/isaac-sim.sh --headless'
eval "${RCLP_ISAAC_LAUNCH_COMMAND}"
```

Remote/streaming launch template:

```bash
export RCLP_ISAAC_LAUNCH_COMMAND='${ISAAC_SIM_ROOT}/isaac-sim.sh'
eval "${RCLP_ISAAC_LAUNCH_COMMAND}"
```

After the first successful run, record:

```bash
printf 'Isaac launch command: %s\n' "${RCLP_ISAAC_LAUNCH_COMMAND}"
printf 'ISAAC_SIM_ROOT=%s\n' "${ISAAC_SIM_ROOT}"
printf 'ROS_DISTRO=%s ROS_DOMAIN_ID=%s\n' "${ROS_DISTRO:-unset}" "${ROS_DOMAIN_ID}"
```

Reference docs used for this checklist:

- NVIDIA Isaac Sim ROS 2 installation guide:
  <https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html>
- NVIDIA Isaac Sim 4.2 ROS/ROS 2 bridge extension guide:
  <https://docs.isaacsim.omniverse.nvidia.com/4.2.0/features/external_communication/ext_omni_isaac_ros_bridge.html>
- Lambda Cloud instance management docs:
  <https://docs.lambda.ai/public-cloud/on-demand/creating-managing-instances/>

## Minimal ROS 2 Command-Gate Plan

The first integration keeps ROS 2 as transport around the existing
ROS-agnostic `CommandGate` in `src/rclp_ros2/command_gate.py`.

1. Isaac Sim publishes simulated robot state, clock, and a simple command
   target through the ROS 2 bridge.
2. A thin ROS 2 adapter subscribes to a candidate remote-assist command topic,
   such as `/rclp/remote_assist/request`.
3. The adapter converts each ROS 2 message into a `Command` with explicit
   `agent_id`, `edge_agent_id`, `robot_id`, `mission_id`, and `capability`.
4. The adapter calls `CommandGate.evaluate(command, lease, current_state)`
   before forwarding to the simulated robot command topic.
5. On `allowed=True`, the adapter republishes the command to a simulator-only
   topic, such as `/sim/remote_assist/accepted`.
6. On `allowed=False`, the adapter does not forward the command. It emits a
   fallback declaration and audit event through the existing RCLP audit path.
7. The first impairment source is deterministic RCLP network state
   (`normal`, `degraded_teleop`, `uplink_bad`, `partition`), not real cellular.
8. Optional Linux `tc netem` can be used later for manual host impairment, but
   it is not required for the milestone and MUST NOT be required by tests.

The milestone is satisfied when one simulated command is accepted under a valid
lease, a no-lease command is rejected, and a later command is rejected after an
impaired profile causes denial, degradation, or revocation.

## First Scenario Runbook

Terminal A, Isaac Sim:

```bash
export ISAAC_SIM_ROOT="<path-to-isaac-sim-install>"
export ROS_DISTRO="${ROS_DISTRO:-humble}"
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-42}"
# Launch Isaac Sim with ROS 2 bridge enabled using the installed Isaac command.
```

Terminal B, RCLP local proof:

```bash
cd rclp
. .venv/bin/activate
isaac_sim/scripts/run_local_protocol_demo.sh
```

Terminal C, ROS 2 gate placeholder:

```bash
cd rclp
. .venv/bin/activate
isaac_sim/scripts/run_ros2_gate_demo.sh
```

Evidence to capture:

- exact Lambda instance type, region, image, and Isaac Sim version, without
  account identifiers;
- exact Isaac Sim launch command;
- `python -m rclp_agents.demo_remote_assist --network-profile degraded_teleop`
  output;
- ROS 2 topic list or adapter placeholder output;
- `audit_jsonl` and `incident_replay_summary`;
- screenshot or short recording showing the simulator scene, if GUI or stream
  access is available.

## Cleanup

Before stopping or deleting a paid instance, copy useful non-secret artifacts
out of the instance and record their location in the assembly ledger. Then use
the operator-approved Lambda cleanup action for the instance and filesystem.

Never store Lambda API keys, SSH private keys, generated private keys, or
account-specific instance identifiers in this repository.
