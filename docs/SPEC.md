# Agent Spec

> **Fill this in BEFORE writing any code or starting Claude Code.**
> An agent without a spec is a hobby project, not an Enlift agent.

---

## Identity

**Name**: `enlift-<domain>-<verb>`

**Owner**: <who maintains this — name + Slack>

**Reviewer**: <who signs off on changes — name + Slack>

**Status**: Draft / In Build / In Review / Production / Deprecated

---

## What it does

<One paragraph. Plain English. If you cannot write it in one paragraph, you do not understand it well enough to build it yet.>

---

## Why it exists

**Problem it solves**: <the manual work, the bottleneck, the mistake category>

**Cost of not having it**: <hours/week, error rate, customer impact>

**Why an agent vs a workflow vs a script**: <justify the autonomy level — see Anthropic's "Building Effective Agents">

---

## Inputs

| Input | Source | Format | Trust level |
|---|---|---|---|
| <e.g. support tickets> | <e.g. Intercom> | <e.g. JSON via MCP> | **untrusted** (treat as prompt-injection-capable) |

> Mark every input as **trusted** or **untrusted**. External content (tickets, emails, web pages, user-uploaded files) is **always untrusted** even if it comes from a known source.

---

## Outputs

| Output | Destination | Format | Sensitivity |
|---|---|---|---|
| <e.g. handbook draft> | <e.g. Confluence> | <e.g. Markdown> | <e.g. internal-only> |

---

## Tools required

| Tool | Built-in / MCP / Custom | Why this agent needs it |
|---|---|---|
| Read | Built-in | <reason> |
| Grep | Built-in | <reason> |
| <MCP server> | MCP | <reason> |

> Every tool must be justified. Every tool must be added to `.claude/settings.json` allowlist with explicit scope. Default-deny everything else.

---

## Skills required

| Skill | Source | Why this agent needs it |
|---|---|---|
| mask-pii | Enlift mandatory | All Enlift agents |
| audit-log | Enlift mandatory | All Enlift agents |
| verify-output | Enlift mandatory | All Enlift agents |
| <custom skill> | Custom | <reason> |

---

## Threat model

| Threat | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Prompt injection via untrusted input | **High** (any agent reading external content) | Could cause unintended tool calls / data exfiltration | Input goes through mask-pii first; permissions deny `curl`/`wget`; audit log catches anomalies |
| Cross-tenant data leak | <H/M/L> | Contractual breach | Client context verified at session start; verify-output checks scope |
| Credential exposure | <H/M/L> | <impact> | Permissions deny `Read(./.env*)` and `~/.ssh`, `~/.aws` |
| Hallucinated output | <H/M/L> | Wrong information shipped | verify-output skill — grounding + reference check |
| <add agent-specific threats> | | | |

---

## Out of scope

<List things this agent **explicitly will not do**. Be concrete. Drift is the enemy.>

- This agent will not <X>
- This agent will not <Y>
- If asked to do <X>, the agent escalates to the operator

---

## Operator interaction

**Who runs this**: <a specific human role, not "the team">

**How they invoke it**: <command, schedule, trigger>

**What they review**: <what the operator must confirm before output ships>

**Escalation path**: <when the agent halts, who gets pinged>

---

## Open questions

<List anything you do not know yet. Better here than discovered mid-build.>

---

*Spec last updated: <date>. Next review: <date>.*
