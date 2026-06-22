# Direction File — How to Run Codex Threads

Use this file as the operating plan. The goal is to build a narrow, public, credible open-protocol MVP before broad customer outreach.

## Thread naming convention

Use one Codex thread per workstream. Keep each thread scoped. Do not ask one thread to do everything.

Recommended thread names:

1. `T0 Repo Steward`
2. `T1 Protocol Spec`
3. `T2 Core Library`
4. `T3 Edge Agent + Command Gate`
5. `T4 Central Agent + Demo Flow`
6. `T5 Network Fault Injection`
7. `T6 Audit + Incident Replay`
8. `T7 Isaac Sim on Lambda`
9. `T8 Security Red Team`
10. `T9 Docs + Conformance`
11. `GTM Research Lead` in the separate GTM repo/package

## Phase 0 — Bootstrap and guardrails

Start with `T0 Repo Steward`.

Prompt file:

```text
prompts/00_repo_steward_bootstrap.md
```

Completion criteria:

- `pytest` passes.
- Repo structure is intact.
- `README.md`, `AGENTS.md`, and `docs/` are coherent.
- `docs/COMMERCIAL_BOUNDARY.md` clearly keeps SaaS/MVNO work out of this repo.

## Phase 1 — Protocol semantics

Start `T1 Protocol Spec` after T0 reports the repo is valid.

Prompt file:

```text
prompts/01_protocol_spec_thread.md
```

Completion criteria:

- `docs/PROTOCOL_SPEC_DRAFT.md` defines message types and normative behavior.
- Each message includes required fields and rejection conditions.
- The protocol is explicitly positioned as an authority layer, not fleet dispatch.

## Phase 2 — Core library and conformance

Start `T2 Core Library` after T1 has defined the message model.

Prompt file:

```text
prompts/02_core_library_thread.md
```

Completion criteria:

- Pydantic models cover required messages.
- Policy evaluator handles identity, mission, geofence, network thresholds, and fallback.
- Signed lease issue/verify/reject path works.
- Negative tests exist for invalid/expired/replayed lease paths.

## Phase 3 — Edge enforcement

Start `T3 Edge Agent + Command Gate` after T2 has passing lease tests.

Prompt file:

```text
prompts/03_edge_agent_command_gate_thread.md
```

Completion criteria:

- Edge agent can verify a lease locally.
- Command gate rejects commands with no valid lease.
- Fallback actions are emitted as events, not treated as certified safety controls.
- Tests cover allow, deny, expire, revoke, and degraded network.

## Phase 4 — Central-agent demo

Start `T4 Central Agent + Demo Flow` after T3 passes.

Prompt file:

```text
prompts/04_central_agent_demo_thread.md
```

Completion criteria:

- `python -m rclp_agents.demo_remote_assist` shows a full authority negotiation flow.
- Demo includes normal network, degraded network, and audit output.
- Demo output is easy to paste into a technical memo.

## Phase 5 — Network fault injection

Start `T5 Network Fault Injection` after the demo works without real network impairment.

Prompt file:

```text
prompts/05_network_fault_injection_thread.md
```

Completion criteria:

- Local deterministic impairment profiles exist.
- Optional Linux `tc netem` scripts are documented but not required for tests.
- Tests show network changes can degrade or revoke authority.

## Phase 6 — Audit and incident replay

Start `T6 Audit + Incident Replay` after demo flow is stable.

Prompt file:

```text
prompts/06_audit_replay_thread.md
```

Completion criteria:

- Audit events have a stable schema.
- Demo can emit JSONL audit logs.
- Replay tool summarizes request → decision → enforcement → fallback.

## Phase 7 — Isaac Sim POC on Lambda.ai

Start `T7 Isaac Sim on Lambda` only after the local demo is stable.

Prompt file:

```text
prompts/07_isaac_sim_lambda_thread.md
```

Completion criteria:

- Lambda setup checklist is explicit.
- Isaac Sim ROS 2 bridge approach is documented.
- A minimal simulated robot scenario plan exists.
- The first Isaac milestone only gates simulated commands; it does not attempt full autonomy.

## Phase 8 — Security red team

Start `T8 Security Red Team` after T2 and T3 are stable.

Prompt file:

```text
prompts/08_security_redteam_thread.md
```

Completion criteria:

- Threat model is updated.
- Attack test cases exist for replay, stale commands, wrong agent, wrong robot, policy downgrade, and compromised central agent.
- Security TODOs are separated into MVP blockers vs future hardening.

## Phase 9 — Docs and conformance

Start `T9 Docs + Conformance` once Phase 4 demo passes.

Prompt file:

```text
prompts/09_docs_conformance_thread.md
```

Completion criteria:

- The repo has a clear demo script.
- Conformance tests are documented.
- The open spec has a governance note and versioning plan.
- The public README is credible but does not overclaim.

## Parallel GTM thread

Use the separate package `rclp-gtm-thread/`.

Start GTM after Phase 0, but do not send broad outbound until Phase 4 produces a working demo.

Primary prompt:

```text
rclp-gtm-thread/prompts/00_gtm_research_lead.md
```

GTM output should feed back into this repo as issues, not undocumented scope creep.
