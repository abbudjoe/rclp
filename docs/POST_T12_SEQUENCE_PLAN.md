# Post-T12 Sequence Plan

This plan is the post-T12 control plane for moving RCLP from a working local
protocol/eval MVP into controlled technical validation calls and then a visual
Isaac Sim POC. It is planning guidance only. Do not add broad new protocol
features before the first validation calls.

## 1. Current State

The post-T12 handoff state is expected to include:

- Python reference implementation for capability requests, policy evaluation,
  signed short-lived leases, command gating, revocation, fallback declarations,
  audit JSONL, and incident replay.
- Rust edge verifier spike that proves the edge-side verifier primitive can be
  expressed as deterministic, dependency-light code.
- Deterministic adversarial eval harness with 33 YAML scenarios and JSON
  reporting.
- Local demo flow for `remote_assist` authority negotiation.
- Safety and commercial boundary docs that keep the repo narrow and honest.

Current checkout note: after fast-forwarding to `origin/main`, the T12 eval
artifacts are present under `docs/EVALS.md` and `tests/evals/`, with 33 YAML
scenarios and a local eval runner.

## 2. What The Repo Currently Proves

The repo currently proves protocol semantics under deterministic local tests:

- valid lease allow path
- deny on stale, missing, malformed, revoked, or replayed authority
- network-state-aware authorization and geofence-conditioned decisions
- local command-gating semantics
- audit completeness checks and replayable authority chains

This is local safety-adjacent evidence. It is not production safety evidence.

## 3. What The Repo Does Not Prove

The repo does not prove:

- production safety
- real robot behavior
- real cellular or network behavior
- Isaac Sim visual behavior, unless and until T14 evidence is produced
- customer willingness to adopt
- carrier API behavior
- formal certification
- production cryptographic trust infrastructure
- hosted commercial-platform behavior

## 4. Recommended Next Sequence

Step 1: Human final review and clean merge.

- Review the current repo state, especially README, release readiness, safety
  boundary, commercial boundary, eval coverage, and local setup.
- Resolve broken doc references, missing eval artifacts, or unclear release
  claims before packaging.

Step 2: Run the full validation suite from a fresh clone.

- Run Python compile and pytest.
- Run the deterministic eval runner.
- Run Rust fmt, clippy, and tests if the Rust workspace is present.
- Confirm the demo runs without cloud, ROS 2, Isaac Sim, external network
  calls, or secrets.

Step 3: Run T13 Demo + Validation Release Package.

- Use the supplied T13 prompt as the source contract.
- Package the MVP for controlled technical validation calls.
- Create validation release notes, customer-call packet, technical FAQ, demo
  walkthrough, comparison doc, first-call target profile, and local validation
  scripts.
- Do not add new protocol features unless required to fix a broken demo or
  broken test.

Step 4: Create the suggested `v0.1-validation` tag.

- Tag only after the T13 package passes local validation.
- Suggested command:

```bash
git tag -a v0.1-validation -m "RCLP v0.1 validation release"
```

Step 5: Begin 5-8 controlled technical validation calls.

- Use the customer-call packet, demo walkthrough, release notes, and field-notes
  template.
- Keep the ask narrow: validate whether RCLP maps to a real central software
  actor to robot-local authority gate gap.
- Record feedback as issues or field notes; do not expand protocol scope during
  calls.

Step 6: Run T14 Isaac Sim Visual POC on Lambda.ai.

- Use the supplied T14 prompt as the source contract.
- Reuse the existing RCLP protocol implementation and eval semantics.
- Keep the first visual demo to one simulated robot, one central-software-actor
  mock, one robot-local authority process, one command gate, one deterministic
  network impairment trigger, one fallback hook, and one audit replay.
- Do not claim real robot safety, real cellular behavior, or production
  readiness.

Step 7: Synthesize customer feedback.

- Consolidate validation notes after the first calls.
- Separate protocol-boundary findings from commercial-platform requests.
- Identify whether customers would run observe-only mode before enforcement.

Step 8: Decide the next branch.

A. Rust parity / hardened edge verifier

B. Observe-only customer pilot

C. Isaac Sim / public demo polish

D. Protocol boundary revision

E. Commercial platform planning in a separate future repo

## 5. Build Freeze Guidance

Before initial validation calls, do not add broad new protocol features. Only
fix:

- broken setup
- broken tests
- broken eval runner
- confusing docs
- demo regressions
- security overclaims
- local path leaks
- secret leaks
- release-readiness contradictions

Commercial platform work, customer accounts, billing, managed policy UI,
carrier/MVNO integration, real QoS integration, production robot runtime, and
formal safety certification evidence must not start in this repo.

## 6. Customer-Call Gate

Ready for controlled technical validation calls when:

- fresh clone works
- README is legible
- local demo runs
- `python -m compileall src tests` passes
- `pytest` passes
- eval runner passes
- Rust fmt, clippy, and tests pass if Rust is present
- no secrets or committed private keys are present
- no absolute local paths leak into public docs
- no named-company/internal references are present
- safety boundary is explicit
- commercial boundary is explicit
- validation memo or customer-call packet exists
- demo script or walkthrough exists
- known gaps are stated as non-claims, not hidden caveats

Controlled calls are allowed to be narrow and candid. They should test whether
the primitive matters, not whether the repo is production software.

## 7. Public Release Gate

Controlled validation calls can happen with:

- `v0.1-validation`

Public launch requires more:

- license confirmed
- governance note reviewed
- security contact confirmed
- polished Isaac Sim demo or clear visual artifact
- issue templates
- contributor guidance
- stronger spec stability note
- eval documentation present and easy to run
- no local path leaks or placeholder operational contacts

Do not treat controlled technical validation as public launch.

## 8. Decision Criteria After First Calls

Strong signal:

- customer has a central-software-actor to robot-local authority gap
- remote assist or autonomy escalation depends on network, geofence, or mission
  state
- current audit is fragmented
- scoped per-capability revocation is weak
- they would run observe-only mode
- they introduce the teleop, fleet reliability, robotics platform, or
  safety/compliance owner
- they can name where an edge daemon or authority sidecar would live

Weak signal:

- "cool protocol" but no pain
- "we already built this"
- "belongs in our fleet manager"
- unwilling to run an edge component
- no budget owner
- no remote assist or autonomy escalation workflow
- only interested in hosted SaaS before validating the open protocol primitive
