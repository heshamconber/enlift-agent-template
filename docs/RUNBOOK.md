# Runbook

> **For the human who has to operate this agent — possibly months from now, possibly not the person who built it.**
> Write this assuming the reader does not have the builder's context.

---

## What this agent does (one paragraph)

<Plain language. No jargon. The "elevator pitch" version of SPEC.md.>

---

## How to run it

### Prerequisites

- Claude Code installed (see `https://code.claude.com`)
- Repo cloned locally
- `.env` populated from `.env.example` (ask <owner> for the values — they are NOT in this repo)
- Required MCP connectors authorised: <list>

### Standard run

```bash
cd <agent-repo>
claude
> <the typical prompt the operator provides>
```

### Scheduled run (if applicable)

<How the agent is run on a schedule, by whom, where logs go.>

---

## How to know it's working

- **Audit log**: every run appends an entry to `audit/<YYYY-MM-DD>.jsonl`. No entry = no run.
- **Verification report**: every output ends with a `Verification: PASS / FAIL` block from the `verify-output` skill. If you do not see one, the agent did not finish properly — do not ship the output.
- **Eval suite**: run `<command>` weekly. If pass^5 drops below 80%, halt the agent and investigate.

---

## How to know it's broken

| Symptom | What it likely means | What to do |
|---|---|---|
| `Verification: FAIL` twice on same output | Task is out of scope or input is malformed | Read the failure reasons, escalate if needed — do not force a third try |
| Repeated `pii_mask_failure` in audit log | Masking patterns no longer match real input | **Halt the agent**. Page <owner>. |
| Agent silently drops output | Permission denial or model error | Check the audit log for the last `permission_denied` or error event |
| Audit log has gaps | Disk full or permission misconfig | **Halt the agent.** No audit = not allowed to run. |
| pass^5 below 80% | Regression — model, prompt, or input drift | Halt, run the eval suite, check for upstream changes |

---

## Common operator tasks

### Adding a new MCP connector
1. Add the connector definition to `.mcp.json`
2. Add the new tool to `.claude/settings.json` allowlist
3. Update `docs/SPEC.md` "Tools required"
4. Run the eval suite to confirm no regression

### Updating CLAUDE.md
1. Edit `CLAUDE.md`
2. Keep it under 200 lines (instruction-following degrades as instruction count rises)
3. Run the eval suite — verify behaviour did not drift unintentionally

### Rotating secrets
1. Update the secret at the source (vault, provider console)
2. Update operator's local `.env` — **never** the committed `.env.example`
3. Run a smoke test (single eval case)

---

## Escalation

| Trigger | Who | How |
|---|---|---|
| Agent halted itself | <owner> | Slack DM + #ai-agents channel |
| Suspected PII leak | <security lead> | Immediately — phone, not Slack |
| Suspected prompt injection success | <security lead> + <owner> | Immediately |
| Eval suite regression | <owner> | Slack within 1 working day |
| Operator question | <owner> | #ai-agents channel |

---

## Decommissioning

When this agent is retired:
1. Mark `docs/SPEC.md` status = "Deprecated"
2. Disable any scheduled runs
3. **Preserve the audit logs** for the contractually required retention period
4. Move repo to the `archive/` org with a final commit explaining why

---

*Runbook last updated: <date>. Next review: <date>.*
