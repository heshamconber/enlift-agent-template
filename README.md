# Enlift Agent Template

**The standard scaffold for every Claude Code agent built at Enlift.**

This template is **mandatory**. Every Enlift agent must start from this repo and conform to its structure. Deviations require team approval.

---

## Why this template exists

We build agents that touch client data, support tickets, and internal documentation. If every agent is built differently — different naming, different verification, different permission posture — we cannot maintain them, audit them, or hand them off.

This template enforces five non-negotiable components every Enlift agent must have:

1. **Standard CLAUDE.md** — opinionated project memory
2. **Locked-down permissions baseline** — `.claude/settings.json` denies dangerous tools by default
3. **PII masking + audit log** — every model call is sanitised; every run is logged
4. **Self-verification step** — the agent reviews its own output before returning it
5. **Success criteria + eval cases** — written *before* coding, gated *before* shipping

If your agent does not have all five, it is not production-ready. See `docs/DEFINITION_OF_DONE.md`.

---

## Quick start

```bash
# 1. Clone this template
git clone <enlift-agent-template-url> my-new-agent
cd my-new-agent
rm -rf .git && git init

# 2. Fill out the spec BEFORE writing any code
$EDITOR docs/SPEC.md

# 3. Define what "done" looks like
$EDITOR docs/SUCCESS_CRITERIA.md
$EDITOR tests/eval_cases.md

# 4. Customise CLAUDE.md for this specific agent
$EDITOR CLAUDE.md

# 5. Launch Claude Code
claude
```

---

## What's in this repo

| Path | What it is | Editable? |
|---|---|---|
| `CLAUDE.md` | Project memory loaded at every session start | Yes — fill it in |
| `.claude/settings.json` | Permissions baseline (deny-by-default) | **No** — use `.claude/settings.local.json` for personal overrides |
| `.claude/commands/` | Standard slash commands shared across all Enlift agents | Yes — add your own |
| `.claude/skills/mask-pii/` | Mandatory PII masking skill | **No** — required, do not remove |
| `.claude/skills/audit-log/` | Mandatory audit logging skill | **No** — required, do not remove |
| `.claude/skills/verify-output/` | Mandatory self-verification skill | **No** — required, do not remove |
| `docs/SPEC.md` | What this agent does — fill in *before* coding | Yes — required |
| `docs/SUCCESS_CRITERIA.md` | How we know it works | Yes — required |
| `docs/RUNBOOK.md` | How to operate this agent in production | Yes — required |
| `docs/DEFINITION_OF_DONE.md` | The gate — every agent must pass | **No** — read it, conform to it |
| `tests/eval_cases.md` | Scenarios this agent must pass | Yes — minimum 5 cases |
| `.env.example` | Template for secrets — never commit real `.env` | Yes |
| `.gitignore` | Pre-configured to keep secrets and local state out of git | Yes — extend, don't shrink |

---

## Naming conventions

| Thing | Pattern | Example |
|---|---|---|
| Agent repo name | `enlift-<domain>-<verb>` | `enlift-ops-handbook-creator` |
| Skill name | `kebab-case`, verb-first | `mask-pii`, `lookup-jira` |
| Slash command (shared) | `/enlift-<action>` | `/enlift-verify` |
| Slash command (personal) | `/<action>` | `/refactor` |
| File names | lowercase, hyphenated, no spaces | `client-isolation.md` |

---

## Before you ship

Run through `docs/DEFINITION_OF_DONE.md`. Every box must be checked. No exceptions.

---

*Maintained by the Enlift AI team. Questions: ask in #ai-agents Slack channel.*
