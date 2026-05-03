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

---

## Quick start

```bash
# 1. Clone this template
git clone <enlift-agent-template-url> my-new-agent
cd my-new-agent
rm -rf .git && git init

# 2. Fill out the runbook BEFORE writing any code
$EDITOR docs/RUNBOOK.md

# 3. Fill in your eval cases
$EDITOR tests/eval_cases.md

# 4. Customise CLAUDE.md for this specific agent
$EDITOR CLAUDE.md

# 5. Set up secrets and the audit directory
cp .env.example .env && $EDITOR .env
mkdir -p audit && chmod 750 audit

# 6. Launch Claude Code
claude
```

---

## What's in this repo

| Path | What it is |
|---|---|
| `CLAUDE.md` | Project memory — fill in before building |
| `src/` | Your agent's scripts and helpers — put custom code here |
| `docs/RUNBOOK.md` | Everything in one place: spec, success criteria, how to run, ship checklist |
| `tests/eval_cases.md` | Scenarios the agent must pass — minimum 5 |
| `.claude/settings.json` | Deny-by-default permissions baseline — extend, don't weaken |
| `.claude/skills/mask-pii/` | Mandatory PII masking (includes `scripts/mask.py`) |
| `.claude/skills/audit-log/` | Mandatory audit logging (includes `scripts/log.py`) |
| `.claude/skills/verify-output/` | Mandatory self-verification |
| `.claude/commands/` | Shared slash commands |
| `.env.example` | Secrets template — copy to `.env`, never commit `.env` |
| `.mcp.json.example` | MCP server config template |
| `.gitignore` | Pre-configured — extend, don't shrink |

---

## Naming conventions

| Thing | Pattern | Example |
|---|---|---|
| Agent repo name | `enlift-<domain>-<verb>` | `enlift-ops-handbook-creator` |
| Skill name | `kebab-case`, verb-first | `mask-pii`, `lookup-jira` |
| Slash command (shared) | `/enlift-<action>` | `/enlift-verify` |

---

## Adding external tools

Each derived agent adds the specific tools it needs. To add an MCP server or CLI tool:

1. Add to `.mcp.json` (use `.mcp.json.example` as reference)
2. Add the scoped allow rule to `.claude/settings.json`
3. Document in `docs/RUNBOOK.md` — Tools & Skills table
4. Review in PR before merging

---

*Maintained by the Enlift AI team. Questions: #ai-agents Slack channel.*
