# Network Fault Injection

RCLP treats network state as a policy input, not a network guarantee. The
reference implementation uses deterministic in-process profiles for tests and
demos:

| Profile | Intent | Authority effect for `remote_assist` |
|---|---|---|
| `normal` | Healthy link for remote assist. | Policy allows a short-lived lease. |
| `degraded_teleop` | Latency, packet loss, and uplink are outside the allow window but inside hard-deny thresholds. | Policy returns `degrade` with a fallback hook. |
| `uplink_bad` | Uplink estimate is too low for remote assist. | Policy denies authority. |
| `partition` | Edge is detached from the control path. | Policy denies authority and uses disconnect fallback. |

Run the local demo with a selected impaired profile:

```bash
python -m rclp_agents.demo_remote_assist --network-profile degraded_teleop
python -m rclp_agents.demo_remote_assist --network-profile uplink_bad
python -m rclp_agents.demo_remote_assist --network-profile partition
```

The deterministic profiles live in `src/rclp_core/network.py`. Unit tests MUST
use those profiles or explicit `NetworkState` fixtures. Tests MUST NOT require
root, Linux traffic control, external network calls, or host network changes.

## Optional Linux `tc netem`

Linux `tc netem` can be useful for manual integration demos after the local
policy path is passing. These commands mutate host networking and normally
require root, so they are intentionally not part of the automated test suite.

Example shapes:

```bash
# Degraded teleop-like profile.
sudo tc qdisc add dev eth0 root netem delay 180ms loss 3.5% rate 1mbit

# Uplink-constrained profile.
sudo tc qdisc add dev eth0 root netem delay 70ms loss 0.5% rate 600kbit

# Partition-like local impairment.
sudo tc qdisc add dev eth0 root netem loss 100%

# Always clean up after a manual run.
sudo tc qdisc del dev eth0 root
```

Replace `eth0` with the interface under test. Prefer a disposable VM, container
namespace, or isolated Lambda/Isaac test host for manual netem work.
