# Customer Call Readiness Checklist

Use this checklist before starting controlled technical validation calls. It is
not a public launch checklist and not a production readiness claim.

## Repo Hygiene

- [ ] Fresh clone quickstart tested.
- [ ] README is legible in under one minute.
- [ ] No absolute local paths in public docs or scripts.
- [ ] No secrets, tokens, API keys, Lambda credentials, private keys, or account
  IDs committed.
- [ ] No named-company/internal references.
- [ ] LICENSE is present and acceptable for controlled validation.
- [ ] `SECURITY.md` does not overpromise response process or production
  hardening.
- [ ] A named project owner or private review channel exists for controlled
  security reports before the packet is shared.
- [ ] Known gaps are documented, not hidden.

## Demo Readiness

- [ ] Demo script is accurate.
- [ ] Demo walkthrough exists and is usable during a live call.
- [ ] Default local demo runs without ROS 2, Isaac Sim, cloud credentials,
  external services, root privileges, or host network mutation.
- [ ] Impaired network profile shows deny, degrade, or revoke behavior.
- [ ] Audit replay reconstructs the request, state, decision, enforcement,
  revocation, and fallback chain.

## Eval Readiness

- [ ] `python -m compileall src tests` passes.
- [ ] `pytest` passes.
- [ ] Eval runner passes.
- [ ] Eval docs exist and explain the adversarial scenarios.
- [ ] Rust `cargo fmt --all -- --check` passes if Rust is present.
- [ ] Rust `cargo clippy --workspace --all-targets -- -D warnings` passes if
  Rust is present.
- [ ] Rust `cargo test --workspace` passes if Rust is present.
- [ ] Ruff check and format check pass if Ruff is installed.

## Security And Safety Caveats

- [ ] README does not overclaim production readiness.
- [ ] Safety boundary is explicit.
- [ ] Commercial boundary is explicit.
- [ ] Demo keys are labeled non-production.
- [ ] RCLP is described as a safety-adjacent authority layer, not a certified
  safety system.
- [ ] Fallback behavior is described as a fallback hook, not guaranteed safe
  behavior.
- [ ] Network state is described as an authorization input, not a promise about
  connectivity quality.

## Customer-Call Packet

- [ ] Customer validation memo or customer-call packet exists.
- [ ] Controlled review packet exists and excludes planning docs unless needed.
- [ ] One-liner is clear.
- [ ] Problem statement is centered on the central software actor to
  robot-local authority gate boundary.
- [ ] What the MVP proves is listed.
- [ ] What the MVP does not prove is listed.
- [ ] Feedback questions ask where the primitive would live in the customer
  stack.
- [ ] Call owner has a concise 5-minute demo flow.

## Legal And IP Hygiene

- [ ] License reviewed for controlled validation.
- [ ] Rust and Python package license declarations match the root license.
- [ ] Third-party protocol names are used descriptively and carefully.
- [ ] No proprietary customer workflows are included.
- [ ] No customer data or field logs are committed.
- [ ] No cloud credentials or Lambda account details are committed.

## Open-Source Posture

- [ ] Controlled-call framing is clear: `v0.1-validation`, not public launch.
- [ ] Governance note exists or is listed as a public launch blocker.
- [ ] Controlled-review security reporting channel is confirmed; public
  security intake remains a public-launch blocker.
- [ ] Contributor guidance is either present or listed as a public launch
  blocker.
- [ ] Issue templates are either present or listed as a public launch blocker.

## Post-Call Notes

- [ ] Field notes template exists.
- [ ] Strong and weak signal criteria are visible.
- [ ] Feedback is recorded as issues or field notes.
- [ ] Requests for SaaS, billing, carrier integration, or managed trust roots
  are captured as future commercial-platform inputs, not added to this repo.
- [ ] Protocol feedback is separated from demo polish and commercial feedback.
