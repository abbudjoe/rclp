# Policy Ownership

RCLP does not decide organizational policy ownership. It defines protocol
messages, lease constraints, local enforcement, and audit semantics for policy
that a fleet organization has already approved.

In a production program, policy ownership would likely sit with the team that
already owns robot operational risk: safety/reliability/autonomy/platform, not
with the protocol itself.

## Suggested ownership model for validation

| Policy activity | Likely owner | Validation question |
|---|---|---|
| Define high-authority capabilities | Robotics platform, autonomy, safety, and fleet reliability leads | Which robot capabilities require scoped authority instead of ordinary command permissions? |
| Define local state requirements | Robotics platform and robot safety/reliability teams | Which mission, geofence, observed network state, and fallback inputs must be checked locally? |
| Approve policy before enforcement | Safety/reliability review group, autonomy lead, and operations owner | What review evidence is required before moving beyond observe-only mode? |
| Deploy policy to edge gates | Platform or edge-runtime team | How is the accepted policy digest pinned, rolled out, and rolled back? |
| Monitor denials and degradations | Fleet reliability, operations, and incident response | Which reason codes should page humans, create tickets, or stay audit-only? |
| Review incidents | Safety, reliability, operations, and security | Does the audit chain reconstruct who requested authority, under what context, and why authority changed? |
| Change policy during operations | Same group that owns operational risk, with change-control support | What emergency-change process avoids silent authority expansion? |

## What RCLP owns

- A typed authority request, decision, lease, command-gate, revocation,
  fallback, and audit shape.
- Local rejection of missing, stale, invalid, revoked, mismatched, or
  overbroad authority.
- Auditability of allow, deny, degrade, revoke, fallback, and command
  enforcement paths.

## What RCLP does not own

- Whether a robot motion is physically safe.
- Which business role is allowed to approve a capability policy.
- Fleet-specific hazard analysis, safety case, policy lifecycle UI, or
  production key-management process.
- The final decision to move from observe-only audit to advisory decisions,
  soft gating, or hard command gating.

## Open validation questions

- Which team already owns the closest equivalent authority boundary?
- Who can approve new gated capabilities?
- Who can emergency-revoke or narrow a capability policy?
- Who consumes audit output after an incident or near miss?
- What evidence would justify hard gating for a selected capability?
