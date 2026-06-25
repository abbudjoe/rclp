# Protocol Evals

Status: deterministic local MVP eval harness. This is technical validation
evidence for the safety-adjacent authority layer, not a production safety or
field-network claim.

## What The Suite Tests

The eval suite asks:

```text
Does RCLP fail closed when authority is missing, stale, revoked, replayed,
malformed, mismatched, or unsafe under local context?
```

The scenarios under `tests/evals/scenarios/` cover the T12 minimum set plus
post-review security regressions:

- valid remote-assist authority
- missing, expired, not-yet-valid, revoked, replayed, malformed, and
  bad-signature authority
- wrong central agent, edge agent, robot, mission, and capability
- geofence violation, high latency, high packet loss, and partitioned network
- stale command after expiry and conflicting local state
- missing or stale current edge state
- unsigned or stale policy state assertions
- over-speed command payloads under `max_speed_mps`
- unsigned revocation rejection
- audit completeness for allow and deny paths
- multi-step network-degradation revocation
- multi-step cloud partition and lease-expiry behavior

Expected outcomes are `allow`, `deny`, or `degrade`. Negative and ambiguous
high-risk paths are expected to deny or degrade with an explicit reason code.

## What It Does Not Test

The eval harness does not test certified safety behavior, robot motion,
real cellular behavior, carrier APIs, Isaac Sim, ROS 2 runtime delivery,
production key management, hardware trust roots, hosted services, fleet
management, teleoperation media, or a commercial dashboard.

It runs only local deterministic Python reference behavior.

## Run Command

From the repo root:

```bash
python tests/evals/eval_runner.py
```

The full local validation path is:

```bash
python -m compileall src tests
pytest
python tests/evals/eval_runner.py
```

Expected successful eval summary:

```text
RCLP evals: 33 passed, 0 failed, 33 total
PASS valid_remote_assist: allow LEASE_VALID
PASS no_lease_denied: deny NO_LEASE
PASS scenario_network_degrade_revokes: deny LEASE_REVOKED
PASS scenario_cloud_partition_expiry: deny LEASE_EXPIRED
Wrote JSON report: tests/evals/reports/latest.json
```

The exact path in the final line is absolute when run locally. A passing eval
summary is evidence for deterministic local reference behavior only; it is not
evidence of production safety, real cellular behavior, ROS 2 runtime delivery,
Isaac Sim execution, or hosted-platform readiness.

If Rust is installed:

```bash
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
```

## Report Interpretation

The runner prints a concise pass/fail summary and writes:

```text
tests/evals/reports/latest.json
```

The JSON report includes scenario name, kind, expected decision, actual
decision, expected reason code, actual reason code, audit event types, missing
audit fields, errors, and notes. The report timestamp is generation metadata;
scenario decision inputs use `now_unix_ms` from each YAML file.

A passing report means the local reference implementation satisfied the eval
expectations. It does not mean production safety, real network guarantees, or
field readiness.

## Audit Completeness

Audit checks use an eval-level view derived from `AuditCommit` records and
their audited payloads. The runner does not satisfy required audit fields from
in-memory request, command, lease, or state objects that were not themselves
recorded in the audit chain.

The current MVP mappings include:

- `event_id` maps to `audit_id`
- `timestamp` maps to `created_at`
- `central_agent_id` maps to request or command agent identity
- `requested_capability` maps to request, command, or lease capability
- `network_state` and `geofence_state` map to decision payloads or current
  local state snapshots captured inside audit records

The allow and deny audit evals require enough mapped fields to reconstruct the
authority decision. Missing fields are report failures.

## Python And Rust Conformance

Python remains the reference implementation for policy behavior, command-gate
audit behavior, and the T12 eval harness.

The Rust verifier spike continues to consume shared vectors under
`tests/vectors/edge_verifier/` through `cargo test --workspace`. The Python
eval runner does not invoke Cargo so pytest and CI stay deterministic for
Python-only environments.

There is no Rust CLI yet for direct Python-vs-Rust eval comparison. Until one
exists, parity is checked by:

- Python evals over the reference policy and command gate
- Python vector-shape tests for the shared Rust vectors
- Rust workspace tests over the shared edge-verifier vectors

## Why Fail-Closed Matters

RCLP governs authority over physical capabilities. A high-authority command
whose lease is missing, invalid, stale, revoked, mismatched, or unsafe under
local context MUST NOT pass through the edge gate. Fail-closed behavior keeps
authority bounded to explicit identity, mission, robot, capability, time,
network, geofence, revocation, and fallback inputs.
Policy issuance also fails closed when signed state or replay protection is
missing; command enforcement fails closed when a state-scoped lease lacks fresh
local state.

## Known Gaps

- The Python MVP signature profile does not expose a first-class signature
  algorithm field. The Python eval for an unknown signature profile fails
  closed as `INVALID_SIGNATURE`; the Rust vectors cover `UNKNOWN_ALGORITHM`
  explicitly.
- Cloud connectivity is not a separate protocol field in the Python MVP.
  Partition behavior is represented through deterministic network state. The
  current command gate denies partitioned `remote_assist` commands before lease
  expiry because the lease's network constraints are violated.
- Audit completeness is checked through an eval mapping rather than a finalized
  v0.1 conformance schema.
- The runner writes a local report artifact but does not publish or persist
  evidence to an external audit backend.
- Production key rotation, hardware-backed trust, durable replay storage, and
  signed fallback envelopes remain future hardening work.
