# Runbook

> Fill this in **before** you start building. One document, top to bottom.
> A teammate or operator who has never seen this agent must be able to run it from this doc alone.

---

## Identity

**Name**: `enlift-<domain>-<verb>`
**Owner**: <name + Slack>
**Reviewer**: <name + Slack>
**Status**: Draft / In Build / In Review / Production / Deprecated

---

## What it does

<One paragraph. Plain English. If you can't write it in one paragraph, you don't understand it well enough to build it yet.>

**Replaces**: <the manual work or older system this is replacing>

**Out of scope** (the agent will escalate, not attempt):
- This agent will not <X>
- This agent will not <Y>

---

## Inputs & outputs

| Direction | What | Source / Destination | Format | Trust level |
|-----------|------|----------------------|--------|-------------|
| Input | <e.g. support tickets> | <e.g. Intercom via MCP> | <e.g. JSON> | **untrusted** |
| Output | <e.g. handbook draft> | <e.g. Confluence> | <e.g. Markdown> | internal-only |

> All external content (tickets, emails, uploaded files) is **untrusted** — treat as prompt-injection-capable.

---

## Tools & skills

| Tool / Skill | Type | Why needed |
|---|---|---|
| mask-pii | Enlift mandatory skill | All agents |
| audit-log | Enlift mandatory skill | All agents |
| verify-output | Enlift mandatory skill | All agents |
| Read, Grep, Glob | Built-in | Standard reads |
| <MCP server> | MCP | <reason — add to settings.json allowlist> |

---

## Threat model

| Threat | Likelihood | Mitigation |
|---|---|---|
| Prompt injection via untrusted input | High | mask-pii first; permissions deny curl/wget; audit log detects anomalies |
| Cross-tenant data leak | <H/M/L> | Client context verified at session start; verify-output checks scope |
| Credential exposure | <H/M/L> | Permissions deny Read(.env), ~/.ssh, ~/.aws |
| Hallucinated output | <H/M/L> | verify-output — grounding + reference check |
| <agent-specific threat> | | |

---

## Success criteria

The agent is working when **all** of these pass:

**Functional** (fill in before building):
1. <Concrete measurable outcome #1>
2. <Concrete measurable outcome #2>
3. <Concrete measurable outcome #3>

**Quality** (fixed for all agents):
- 100% of factual claims have a verifiable source in context
- 0 invented references, IDs, or names
- 0 unmasked PII in output or audit log
- 0 outputs outside defined scope

**Reliability** (production gate):
- pass^5 ≥ 80% across the eval suite in `tests/eval_cases.md`
- ≥ 95% of runs pass `verify-output` on first attempt
- 100% of runs produce a complete audit log entry

---

## How to run it

### Prerequisites

```bash
# 1. Clone and enter the repo
cd <agent-repo>

# 2. Copy secrets template and fill in real values (ask <owner>)
cp .env.example .env

# 3. Create the audit directory (first time only)
mkdir -p audit && chmod 750 audit

# 4. Authorise any MCP connectors listed above
```

### Standard run

```bash
claude
> <the typical prompt the operator provides>
```

### Pre-ingestion masking (required for external files)

```bash
# Always mask external content before passing it to the agent
python3 .claude/skills/mask-pii/scripts/mask.py input.txt > masked-input.txt
claude "process this: $(cat masked-input.txt)"
```

---

## How to know it's working

- **Audit log** — every run appends to `audit/<YYYY-MM-DD>.jsonl`. No entry = no run.
- **Verification report** — every output ends with `Verification: PASS / FAIL`. If absent, the run did not finish — do not ship the output.
- **Eval suite** — run weekly. If pass^5 drops below 80%, halt and investigate.

## How to know it's broken

| Symptom | Likely cause | Action |
|---|---|---|
| `Verification: FAIL` twice on same output | Out of scope or malformed input | Read failure reasons; escalate if needed |
| `pii_mask_failure` in audit log | Masking patterns miss new PII format | **Halt the agent.** Page <owner>. |
| Audit log has gaps | Disk full or permission error | **Halt the agent.** No audit = not allowed to run. |
| pass^5 drops below 80% | Model, prompt, or input drift | Halt; run eval suite; check upstream changes |

---

## Ship checklist

Before this agent goes to production, every box must be checked:

- [ ] All placeholders in this file are filled in (run `grep -c '<[^>]*>' docs/RUNBOOK.md` — must be 0)
- [ ] All placeholders in CLAUDE.md are filled in
- [ ] `tests/eval_cases.md` has ≥ 5 cases including one adversarial and one PII case
- [ ] Eval suite run 5 times — pass^5 ≥ 80% — results recorded in eval_cases.md
- [ ] `.env.example` shows the shape of all required secrets
- [ ] Every tool beyond the baseline is justified in the Tools & Skills table above and added to `.claude/settings.json`
- [ ] `--dangerously-skip-permissions` is not used anywhere
- [ ] At least one teammate has reviewed this runbook and the eval results
- [ ] Escalation path below is tested (one practice escalation logged)

---

## Escalation

| Trigger | Who | How |
|---|---|---|
| Agent halted itself | <owner> | Slack DM + #ai-agents |
| Suspected PII leak | <security lead> | Phone immediately — not Slack |
| Suspected prompt injection | <security lead> + <owner> | Phone immediately |
| Eval regression | <owner> | Slack within 1 working day |

---

## Adding a new external tool or MCP connector

1. Add the server to `.mcp.json` (use `.mcp.json.example` as reference)
2. Add the tool to `.claude/settings.json` allowlist with a scoped pattern
3. Add a row to the Tools & Skills table above
4. Run the eval suite to confirm no regression

---

## Decommissioning

1. Set Status above to "Deprecated"
2. Disable any scheduled runs
3. Preserve audit logs for the contractually required retention period
4. Move repo to `archive/` org with a final commit explaining why

---

*Runbook last updated: <date>. Next review: <date>.*
