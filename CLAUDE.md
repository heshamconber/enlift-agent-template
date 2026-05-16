# CLAUDE.md

> **This file is loaded automatically at every Claude Code session start.**
> Fill in the placeholders. Keep this file lean — under 200 lines is the target.
> Remember: Claude already knows a lot. Only tell it what's specific to *this* agent.

---

## What this agent is

**Name**: `<agent-name>` (must match `enlift-<domain>-<verb>` pattern)

**Purpose**: <one sentence — what does this agent do for the business?>

**Replaces**: <what manual work or older system this is replacing>

**Out of scope**: <what this agent will explicitly NOT do — be concrete>

---

## How to work on this project

**Stack**: <languages, frameworks, runtimes>

**Project structure**:
```
src/        — your agent's scripts and helpers (add scripts here, then allow them in settings.json)
docs/       — runbook (one file — fill this in before building)
tests/      — eval cases (minimum 5)
.claude/    — skills, commands, permissions (don't edit unless adding a new skill or tool)
```

**Commands you'll need**:
- Run tests: `<command>`
- Run lint: `<command>`
- Run a single eval case: `<command>`
- Run the full eval suite: `<command>`

---

## Which rules apply to your agent?

| Rule | Client-facing agent | Internal-only agent |
|------|--------------------|--------------------|
| PII masking | **Required** | Only if inputs contain personal data |
| Audit logging | **Required** | Recommended but can be lightweight |
| Multi-tenant isolation | **Required** | Not applicable — skip this rule |
| Self-verification | **Required** | **Required** |
| Deny-by-default permissions | **Required** | **Required** |

**Client-facing** = agent reads tickets, emails, documents, or any data that belongs to a client.
**Internal-only** = agent works purely with your own team's data (Jira backlog, internal reports, code).

---

## Enlift-mandated rules (non-negotiable)

### 1. PII handling

- **Always** invoke the `mask-pii` skill before sending external content (tickets, emails, documents) to the model.
- Never log raw PII. The audit log records hashes/redacted versions only.
- If you see actual names, emails, phone numbers, or IDs in your context, stop and call `/enlift-mask`.
- For client-facing agents processing external content, wire an LLM injection classifier at startup via `set_llm_injection_classifier()` in `src/preflight.py` — regex-only mode is not sufficient for production client-facing use.

### 2. Multi-tenant isolation *(client-facing agents only)*

- This agent works on data from **one client at a time**. Never mix.
- Client identity is established at session start. Verify before any action.
- If you cannot determine which client a piece of data belongs to, **stop and ask the operator**.
- *Internal-only agents: skip this rule — delete this section when you fill in CLAUDE.md.*

### 3. Self-verification before output

- Before returning any final output, invoke the `verify-output` skill.
- Verification checks: factual grounding, no hallucinated references, success criteria met, no PII leaked.
- If verification fails, revise. If it fails twice, escalate to the operator.

### 4. Audit logging

- Every run is logged via the `audit-log` skill.
- Log entries include: timestamp, operator, client context, tools invoked, success/failure.
- The audit log is append-only. Never modify or delete entries.
- Pass `tokens_used=llm_client._tokens_used` to `require_audit_then_return()` so token consumption is recorded — never leave it at the default 0.

### 5. Permissions

- This agent runs under the deny-by-default permissions baseline in `.claude/settings.json`.
- **Never run with `--dangerously-skip-permissions`.**
- New tool requirements must be added to `settings.json` and reviewed in PR.

---

## Forbidden actions

These commands are **denied** by `.claude/settings.json` and must never be enabled:

- `Bash(rm -rf *)` — destructive deletion
- `Bash(sudo *)` — privilege escalation
- `Bash(curl *)` / `Bash(wget *)` — arbitrary network fetch (exfiltration risk)
- `Read(./.env*)` — secrets
- `Read(~/.ssh/*)` — host credentials
- `Read(~/.aws/*)` — cloud credentials

---

## Coding discipline

These four rules reduce the most common LLM coding mistakes (sourced from Andrej Karpathy's guidelines):

### 1. Think before coding
Surface assumptions and confusion **before** writing any code. If the request is ambiguous, ask a focused clarifying question rather than guessing and building on a wrong foundation.

### 2. Simplicity first
Write only the minimum code needed to satisfy the request. No extra features, no speculative abstractions, no "nice to have" additions unless explicitly asked. Three similar lines beat a premature abstraction.

### 3. Surgical changes
Every changed line must trace directly back to the user's request. Do not reformat surrounding code, rename unrelated variables, or clean up adjacent logic unless that is the task.

### 4. Goal-driven execution
Before starting, convert vague requests into a concrete, verifiable success criterion. Example: "add validation" → "the function returns an error when the input is not a positive integer." Code to that target, then verify it.

---

## How to verify your work

Every change must:
1. Pass the eval suite in `tests/eval_cases.md` (target: pass^5 ≥ 80% — agent succeeds on all 5 attempts in ≥80% of trials)
2. Update `docs/RUNBOOK.md` if behaviour or operational steps change
3. Pass the ship checklist in `docs/RUNBOOK.md` before shipping

---

## Tone and output style

- Plain English. No jargon for jargon's sake.
- Cite sources for every factual claim from external content (tickets, docs).
- When uncertain, say so — never fabricate references or fill gaps with plausible-sounding fiction.
- Output should be skimmable: short paragraphs, clear headers, no walls of text.

---

*Last updated: <date>. Maintained by: <team-or-name>.*
