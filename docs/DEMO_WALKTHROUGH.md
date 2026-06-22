# Demo Walkthrough

The local demo proves the `remote_assist` authority primitive with deterministic
fixtures. It uses local non-production Ed25519 keys, in-process network
profiles, a policy YAML file, a signed request, a signed lease, an edge command
gate, fallback declarations, audit JSONL, and replay summary.

## Run

From a fresh checkout with Python 3.11 or newer:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest
python -m rclp_agents.demo_remote_assist
```

Run a hard-deny network profile:

```bash
python -m rclp_agents.demo_remote_assist --network-profile uplink_bad
```

No ROS 2, Isaac Sim, root privileges, cloud account, or external network calls
are required for the local demo.

## Expected Sections

The exact IDs, signatures, timestamps, and hashes will change. These section
headers and reason codes should be stable:

```text
RCLP remote_assist local protocol demonstration
Safety note: RCLP is a safety-adjacent authority layer, not a certified safety system.

### setup
...
"policy_id": "remote-assist-authority-v0"
"deterministic_network_profiles": ["normal", "degraded_teleop", "uplink_bad", "partition"]

### capability_request
...
"message_type": "capability_request"
"capability": "remote_assist"
"requesting_agent_id": "fleet-agent:v0.1"
"signature": "<non-production demo signature>"

### normal_network_decision
...
"message_type": "capability_decision"
"decision": "allow"
"reason_code": "POLICY_SATISFIED"
"deciding_actor_id": "rclp-demo-issuer"
"policy_id": "remote-assist-authority-v0"
"lease": {"capability": "remote_assist", "signature": "..."}

### command_gate_with_valid_lease
...
"allowed": true
"reason_code": "LEASE_VALID"

### command_without_valid_lease
...
"decision": "deny"
"reason_code": "NO_LEASE"
"safe_alternatives": ["local_autonomy_only"]

### impaired_network_decision
...
"decision": "degrade"
"reason_code": "NETWORK_LATENCY_DEGRADED"
"safe_alternatives": ["crawl_to_safe_zone"]

### lease_revocation
...
"message_type": "lease_revocation"
"reason_code": "NETWORK_PROFILE_REVOKE"

### command_gate_after_network_revocation
...
"decision": "deny"
"reason_code": "LEASE_REVOKED"

### audit_jsonl
{"message_type":"audit_commit", ... "event_type":"capability_requested", ...}
{"message_type":"audit_commit", ... "event_type":"capability_allowed", ...}
{"message_type":"audit_commit", ... "event_type":"command_rejected", ...}

### incident_replay_summary
Correlation corr_demo_remote_assist:
  requests:
  states:
  decisions:
  enforcement:
  revocations:
  fallbacks:
```

With `--network-profile uplink_bad`, the impaired decision should be:

```text
"decision": "deny"
"reason_code": "NETWORK_UPLINK_TOO_LOW"
```

With `--network-profile partition`, the impaired decision should be:

```text
"decision": "deny"
"reason_code": "NETWORK_DETACHED"
```

## What To Notice

- The central agent requests a capability; it does not send a raw privileged
  robot command directly to the edge.
- Normal network state allows a short-lived lease.
- The command gate accepts a command only with a valid, matching, unexpired
  lease.
- A command without a lease is rejected and produces a fallback declaration.
- Network degradation changes authority and causes revocation or rejection.
- Audit replay reconstructs request, state, decision, enforcement, revocation,
  and fallback.

This is a sim/local proof of a safety-adjacent authority layer, not field-proven
safety and not a certified safety system.
