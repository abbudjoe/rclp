# Security Policy

RCLP is an experimental open protocol MVP and reference implementation. Do not
use this repository as a production robot safety system.

## Reporting Security Issues

Security reporting contact:

```text
For controlled validation, report security issues to the project maintainer
through the same private channel that provided access to this repository.
```

Do not disclose sensitive vulnerability details in public issues. Before any
public repository launch, publish a monitored project security address or
enable private vulnerability reporting in the repository host.

## Current Known Security Limitations

- Demo keys are non-production and generated for local reference flows.
- Production key management, rotation, hardware-backed storage, attestation,
  and certificate chains are not implemented.
- Revocation and some standalone messages still need authenticated
  trust-boundary envelopes for a hardened profile.
- Python replay windows are in-memory.
- Clock trust and monotonic-time handling remain MVP assumptions.
- The Rust edge verifier uses deterministic test vectors with
  `RCLP-DEV-HMAC-SHA256`; this is not a production signature profile.
- This repo does not provide production robot safety, formal certification,
  carrier integrations, hosted trust roots, managed policy UI, or commercial
  SLAs.

## Scope

In scope for review:

- protocol models
- policy evaluation
- lease signing and verification
- command gate behavior
- audit replay/integrity behavior
- Rust edge verifier spike
- documentation claims that could mislead implementers

Out of scope for this repo:

- hosted commercial platform security
- customer account security
- carrier/MVNO integrations
- robot hardware safety certification
