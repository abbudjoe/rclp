# Demo Walkthrough

Use this as a five-minute live-call script for `v0.1-validation`.

The local demo proves the `remote_assist` authority primitive with deterministic
fixtures. It uses local non-production Ed25519 keys, in-process network
profiles, a policy YAML file, a signed request, a signed lease, a robot-local
command gate, fallback declarations, audit JSONL, and replay summary.

No ROS 2, Isaac Sim, root privileges, cloud account, external network calls, or
robot hardware are required.

## Setup Command

From a fresh checkout with Python 3.11 or newer:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

If Rust is installed, the validation script also exercises the Rust verifier
workspace.

## Validation Command

Run the package validation command:

```bash
./scripts/run_validation_checks.sh
```

Expected result:

- Python compile succeeds.
- `pytest` passes.
- deterministic eval runner reports all scenarios passing.
- Ruff passes when dev dependencies are installed.
- Rust fmt, clippy, and tests pass when Cargo is available.

The command does not require network, ROS 2, Isaac Sim, cloud credentials, or
robot hardware.

## Demo Command

Run:

```bash
./scripts/run_validation_demo.sh
```

The script runs:

```bash
python -m rclp_agents.demo_remote_assist
```

You can also run a hard-deny profile:

```bash
./scripts/run_validation_demo.sh --network-profile uplink_bad
```

## Expected Story

Tell the story in this order:

1. The remote-assist service, operator-session controller, fleet service,
   autonomy module, or other central software actor requests `remote_assist`
   authority.
2. The robot-local authority service evaluates identity, mission, robot,
   geofence, observed network state used as an authorization input, replay,
   revocation, lease scope, and fallback policy.
3. Normal local state grants a short-lived scoped lease.
4. The command gate allows one matching command with the valid lease.
5. A command without a valid lease is rejected.
6. Network degradation causes degradation or revocation.
7. Later use of revoked authority is rejected.
8. Audit replay reconstructs the causal chain.

Keep the framing narrow: RCLP governs authority, not low-level robot safety.

## Expected Output Highlights

The exact IDs, signatures, timestamps, and hashes will change. These section
headers and reason codes should be stable:

```text
RCLP remote_assist local protocol demonstration
Safety note: RCLP is a safety-adjacent authority layer, not a certified safety system.

### setup
"policy_id": "remote-assist-authority-v0"
"deterministic_network_profiles": ["normal", "degraded_teleop", "uplink_bad", "partition"]

### capability_request
"message_type": "capability_request"
"capability": "remote_assist"
"requesting_agent_id": "fleet-agent:v0.1"

### normal_network_decision
"decision": "allow"
"reason_code": "POLICY_SATISFIED"
"policy_id": "remote-assist-authority-v0"
"lease": {"capability": "remote_assist", ...}

### command_gate_with_valid_lease
"allowed": true
"reason_code": "LEASE_VALID"

### command_without_valid_lease
"decision": "deny"
"reason_code": "NO_LEASE"
"safe_alternatives": ["local_autonomy_only"]

### impaired_network_decision
"decision": "degrade"
"reason_code": "NETWORK_LATENCY_DEGRADED"
"safe_alternatives": ["crawl_to_safe_zone"]

### lease_revocation
"message_type": "lease_revocation"
"reason_code": "NETWORK_PROFILE_REVOKE"

### command_gate_after_network_revocation
"decision": "deny"
"reason_code": "LEASE_REVOKED"

### audit_jsonl
{"message_type":"audit_commit", ...}

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

## How To Explain The Allow Path

Point at `normal_network_decision` and `command_gate_with_valid_lease`.

The important claim is not that the robot moved safely. The claim is that
authority was explicitly requested, evaluated against local state and policy,
scoped to robot/mission/capability/agent/time, signed, and then enforced by a
robot-local gate.

The important result is not robot motion; it is local rejection, revocation,
and auditability of selected robot authority.

Use these phrases:

- "short-lived scoped authority"
- "robot-local edge verification"
- "command gate before robot-facing execution"

## How To Explain Deny, Revoke, And Degrade

Point at `command_without_valid_lease`, `impaired_network_decision`,
`lease_revocation`, and `command_gate_after_network_revocation`.

The important moment is the rejection or revocation of authority under degraded
conditions. RCLP is useful because it makes failure states legible and
auditable:

- no lease -> `NO_LEASE`
- degraded latency -> `NETWORK_LATENCY_DEGRADED`
- hard uplink failure -> `NETWORK_UPLINK_TOO_LOW`
- partition -> `NETWORK_DETACHED`
- revoked lease reuse -> `LEASE_REVOKED`

Fallbacks are hooks and audit declarations, not certified safety behavior.

## How To Explain Audit Replay

Point at `audit_jsonl` and `incident_replay_summary`.

The replay should reconstruct request, state, decision, enforcement,
revocation, and fallback events for the same correlation ID. The demo is meant
to make the authority chain explainable after an incident or near miss.

## How To Explain Evals

After the demo, point to:

- `docs/EVALS.md`
- `tests/evals/scenarios/`
- `tests/evals/reports/latest.json`

The deterministic eval suite checks fail-closed behavior across missing,
stale, malformed, mismatched, replayed, revoked, geofence-violating, and
network-impaired authority paths. It is local technical validation evidence for
the authority primitive, not production safety evidence.

Run directly:

```bash
python tests/evals/eval_runner.py
```

## How To Explain Limitations

Say these plainly:

- This is a safety-adjacent authority layer, not a certified safety system.
- This is a local deterministic proof, not field safety evidence.
- This does not prove real cellular behavior or carrier API behavior.
- This does not include production key management or hardware roots of trust.
- This does not include a hosted commercial control plane.
- ROS 2 and Isaac Sim are integration scaffolds, not validation prerequisites.
- The current ask is controlled technical validation of the primitive.

## Closing Question

End with:

> Where would this authority boundary live in your stack, and what local
> conditions would have to gate remote assist or autonomy escalation before you
> would trust it even in observe-only mode?
