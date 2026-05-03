---
name: audit-log
description: Appends a structured entry to the append-only audit log. Invoke at session start, at every tool call touching client data, and at every final output. Mandatory for all Enlift agents.
allowed-tools: Read, Bash(date *), Bash(python3 .claude/skills/audit-log/scripts/log.py *)
---

# Audit Log

## How to use

```bash
python3 .claude/skills/audit-log/scripts/log.py \
  --event-type <type> \
  --tool <tool-name> \
  --target "<masked-path-or-id>" \
  --outcome success|failure|partial
```

Valid event types: `session_start`, `tool_invocation`, `pii_mask_invoked`, `pii_mask_failure`, `verification_result`, `final_output`, `escalation`, `permission_denied`

## Rules

- Log at session start, at every client data access, and at final output.
- Never log raw PII — only masked tokens or hashes.
- If the log cannot be written, **halt and escalate**. No audit = not allowed to run.
- Entries are append-only. Never delete or overwrite past entries.
