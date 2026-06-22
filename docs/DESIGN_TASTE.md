# Design Taste

## Product taste

- Make authority visible.
- Make denial useful.
- Make failure states legible.
- Prefer small, composable primitives.
- Treat “agent” as a software actor, not just an LLM.
- Avoid hype vocabulary in normative docs.

## API taste

Good response:

```json
{
  "decision": "deny",
  "reason_code": "NETWORK_UNSUITABLE_FOR_REMOTE_ASSIST",
  "safe_alternatives": ["local_autonomy_only", "crawl_to_safe_zone", "escalate_to_human"],
  "retry_after_seconds": 30
}
```

Bad response:

```json
{"error": "not allowed"}
```

## Documentation taste

- Explain what this replaces and what it does not replace.
- Keep the open spec narrow.
- Mark assumptions as assumptions.
- Use diagrams only when they clarify authority flow.

## Demo taste

The demo should look like infrastructure, not a toy robot demo. The important moment is the rejection or revocation of authority under degraded conditions.
