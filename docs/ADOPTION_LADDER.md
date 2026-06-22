# Adoption Ladder

Customers will not immediately let a new protocol sit in a hard control path. Support staged adoption.

## Level 0 — Observe-only

Ingest events and produce audit timelines. No gating.

## Level 1 — Advisory

Recommend allow/deny/degrade decisions. Customer system remains authoritative.

## Level 2 — Soft gate

Edge agent rejects non-critical commands without valid leases.

## Level 3 — Hard gate for selected capabilities

Remote assist or autonomy escalation requires valid lease.

## Level 4 — Production integration

Policy, audit, lease enforcement, and revocation integrated into fleet ops and incident review.

## Level 5 — Qualified Safety-Engineering Integration

Future work with qualified safety engineers. This is not part of the MVP and
is not a safety certification claim by this repository.
