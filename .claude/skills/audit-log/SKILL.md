---
name: audit-log
description: Appends a structured entry to the agent's append-only audit log. Use at the start of every agent run, at every tool invocation that touches client data, and at every final output. Mandatory for all Enlift agents.
allowed-tools: Read, Bash(date *), Bash(echo *)
---

# Audit Log — Enlift mandatory skill

## When to invoke

- **At session start**: log the operator, client context, and intended task
- **At every tool call** that reads client data or writes any output
- **At every final output**: log the success/failure and the verification result
- **At every escalation**: log what was escalated and why

## Log format

Entries are JSON Lines (one JSON object per line) appended to `audit/<YYYY-MM-DD>.jsonl`:

```json
{
  "timestamp": "2026-04-22T14:32:11Z",
  "agent": "enlift-ops-handbook-creator",
  "operator": "hesham@enlift.com",
  "client_context": "client_a4f3b8",
  "event_type": "tool_invocation",
  "tool": "Read",
  "target": "[REDACTED_PATH]",
  "outcome": "success",
  "verification_passed": null,
  "notes": ""
}
```

## What MUST be logged

| Event | When |
|---|---|
| `session_start` | Every Claude Code session for this agent |
| `tool_invocation` | Every Read/Write/Bash/MCP call that touches client data |
| `pii_mask_invoked` | Every time the mask-pii skill runs |
| `pii_mask_failure` | If PII masking fails |
| `verification_result` | After every verify-output skill run |
| `final_output` | When the agent returns a final result to the operator |
| `escalation` | When the agent escalates instead of acting |
| `permission_denied` | When a tool call is blocked by permissions |

## What MUST NOT appear in the log

- Raw PII (use the mask-pii skill first; log the masked version or hashes only)
- Secrets, tokens, API keys
- Full document contents (log a content hash + length instead)
- Anything you would not be comfortable showing to a regulator

## Operational rules

1. **Append-only.** Never modify or delete past entries. If a logged event is wrong, append a correction event referencing it.
2. **Daily rotation.** New file each day, old files are immutable.
3. **No log = no run.** If the audit log cannot be written (disk full, permission denied), the agent must halt and escalate. Continuing to operate without an audit trail is a breach of the framework.

## How to use

```bash
.claude/skills/audit-log/scripts/log.py \
  --event-type tool_invocation \
  --tool Read \
  --target "$file" \
  --outcome success
```

## Why this is mandatory

When you leave or hand off this agent, the audit log is the *only* record of what it did, for whom, and whether it worked. Without it: no accountability, no debugging, no compliance story. Treat this skill as part of the agent's contract with the business, not as overhead.

---

*Maintained by Enlift. Do not disable.*
