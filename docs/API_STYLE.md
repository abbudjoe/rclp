# API Style

## Capability request shape

Agents request capabilities, not raw robot commands.

```json
{
  "protocol_version": "0.0.1-draft",
  "message_id": "msg_...",
  "correlation_id": "corr_...",
  "created_at": "2026-06-22T00:00:00Z",
  "message_type": "capability_request",
  "requesting_agent_id": "fleet-agent:v0.1",
  "authenticated_agent_id": "fleet-agent:v0.1",
  "edge_agent_id": "edge-agent:rover-001",
  "robot_id": "rover-001",
  "mission_id": "mission-001",
  "capability": "remote_assist",
  "reason": "low-confidence obstacle negotiation",
  "requested_duration_seconds": 600,
  "request_nonce": "nonce_...",
  "signature": "..."
}
```

## Decision shape

Decisions should be structured enough for machines and humans.

```json
{
  "protocol_version": "0.0.1-draft",
  "message_id": "msg_...",
  "correlation_id": "corr_...",
  "created_at": "2026-06-22T00:00:01Z",
  "message_type": "capability_decision",
  "request_id": "msg_...",
  "decision": "deny",
  "reason_code": "NETWORK_UNSUITABLE_FOR_REMOTE_ASSIST",
  "deciding_actor_id": "rclp-demo-issuer",
  "policy_id": "remote-assist-authority-v0",
  "policy_digest": "sha256:...",
  "safe_alternatives": ["local_autonomy_only", "crawl_to_safe_zone"],
  "audit_id": "audit_...",
  "signature": "..."
}
```

## Error style

Every denial or error should include:

- stable reason code
- human-readable summary
- fallback-oriented alternatives when available
- retry semantics when appropriate
- audit id when the event is security/authority-relevant
