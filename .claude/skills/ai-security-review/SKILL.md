# Skill: AI Agent Security Review

## Purpose
Perform a comprehensive security gap analysis of an AI agent project against:
- OWASP AI Agent Security Cheat Sheet (ASI01–ASI10)
- AI Agent Security Workshop — 10 Golden Rules
- OWASP Top 10 for LLM Applications

Produces `SECURITY_CHECKLIST.md` in the project root with every control
rated ✅ COVERED / ⚠️ PARTIAL / ❌ MISSING, evidence drawn from the actual
codebase, and concrete remediation steps for every gap.

This skill is read-only. It never modifies source code. It writes only
`SECURITY_CHECKLIST.md` (and `SECURITY_FIXES_TODO.md` if gaps are found).

---

## Phase 1 — Understand the project architecture

Read the following in order (stop when you have enough context):
1. `CLAUDE.md` or `README.md` — identity, stack, pipeline steps, guardrails
2. Entry point files: `run_pipeline.py`, `app.py`, `main.py`, or similar
3. `modules/` or `src/` directory listing
4. Any file named `config.py`, `settings.py`, or `.env.example`
5. `requirements.txt`, `pyproject.toml`, or `package.json`
6. `Dockerfile` or `docker-compose.yml`
7. `.github/workflows/` — CI/CD pipelines
8. `tests/` directory structure

Build a mental model of:
- What external systems the agent calls (LLM providers, APIs, databases)
- How documents/inputs enter the system
- How outputs leave the system
- What credentials are used and how they are stored
- Whether the pipeline is stateless or maintains memory between runs

---

## Phase 2 — Control-by-control evidence collection

For each control below, search the codebase for evidence. Use Grep and Read
to find actual implementations — do not assume a control is present without
seeing the code. Rate each control:

  ✅ COVERED   — control is demonstrably implemented in code
  ⚠️ PARTIAL   — partially addressed; note the specific gap
  ❌ MISSING   — no implementation found

### ASI01 — Prompt Injection

Search for:
- Patterns like `_check_injection`, injection filter, content filter, guardrail
  scan before LLM calls
- Delimiters wrapping untrusted content in prompts (e.g. `=== DOC ===`,
  `<document>`, `[USER INPUT]`)
- Whether untrusted content (uploaded files, API responses) enters the LLM
  system prompt vs. user message role
- Whether Jira/Orchestrator/external API text is sanitised before embedding
  in prompts

Controls to rate:
| ID | Control |
|----|---------|
| 1.1 | All external data treated as untrusted |
| 1.2 | Delimiters/boundaries between instructions and data |
| 1.3 | Content filter for known injection patterns (regex or classifier) |
| 1.4 | Separate LLM pre-pass to validate untrusted content |
| 1.5 | Indirect injection via API responses (Jira, Orchestrator, DB) sanitised |
| 1.6 | Untrusted input passed in user role, not system role |

### ASI02 — Tool Misuse & Exploitation

Search for:
- JQL/SQL/OData parameter escaping before embedding user input in queries
- Whether the agent can write/delete, or only read, external systems
- OAuth scopes / API token permissions (look in config, README, CLAUDE.md)
- Rate limiting or call caps per pipeline run
- Whether LLM output is used directly as a tool argument (high risk)

Controls to rate:
| ID | Control |
|----|---------|
| 2.1 | Minimum tool set — agent cannot reach systems it doesn't need |
| 2.2 | Read-only scopes for every external integration |
| 2.3 | Tool arguments validated/escaped before each call |
| 2.4 | LLM output is never used raw as a tool argument |
| 2.5 | Rate limits / hard caps on tool calls per session |

### ASI03 — Identity & Privilege Abuse

Search for:
- Whether the agent uses a dedicated service identity (not a human user)
- Credential storage: `.env`, secrets vault, environment injection
- Short-lived vs. long-lived credentials (OAuth client_credentials vs. API tokens)
- Audit logs that distinguish agent actions from human actions

Controls to rate:
| ID | Control |
|----|---------|
| 3.1 | Agent has own scoped service identity — no shared human credentials |
| 3.2 | Short-lived, rotated credentials where possible |
| 3.3 | Audit log attributes every action to a specific run/identity |
| 3.4 | No credential sharing across agents or environments |

### ASI04 — Supply Chain

Search for:
- `requirements.txt` / `package.json`: are versions pinned (`==` or `~=`) or
  loose (`>=`)?
- `Dockerfile`: is the base image SHA-pinned or just a tag?
- CI/CD workflow: is there a container scan step (Trivy, Grype, Snyk)?
- Whether third-party LLM providers send data outside the organisation's
  cloud tenant (Groq, OpenAI public API, Gemini — vs. Azure AI Foundry,
  on-premise)
- Whether MCP servers or third-party plugins are used (supply chain risk)

Controls to rate:
| ID | Control |
|----|---------|
| 4.1 | Dependencies pinned to exact or compatible-release versions |
| 4.2 | Container image scanning in CI |
| 4.3 | Base image provenance (SHA digest or official image) |
| 4.4 | Third-party LLM data egress documented and approved |
| 4.5 | No unapproved MCP servers or third-party plugins |

### ASI05 — Unexpected Code Execution

Search for:
- Any `eval()`, `exec()`, `subprocess`, `os.system` calls
- Whether the LLM is asked to produce code that is then executed
- Whether agent-generated content is rendered in a browser (XSS risk)

Controls to rate:
| ID | Control |
|----|---------|
| 5.1 | No eval() / exec() / subprocess of LLM-generated content |
| 5.2 | Agent-generated code is not auto-executed on the host |

### ASI06 — Memory & Context Poisoning

Search for:
- Vector stores, RAG databases, persistent memory modules
- Whether one run's output can influence the next run's inputs
- Run isolation: unique run IDs, temp directories, no state bleed

Controls to rate:
| ID | Control |
|----|---------|
| 6.1 | No persistent memory between runs (or memory is scoped and encrypted) |
| 6.2 | Each run is fully isolated (unique ID, temp workspace) |
| 6.3 | No self-reinforcing loops (agent writing its outputs back to its inputs) |

### ASI08 — Cascading Failures

Search for:
- Retry limits on LLM calls, external API calls
- Token budget enforcement (RED threshold halts pipeline)
- Timeout on LLM calls (prevent indefinite hangs)
- Whether one step's failure propagates and destroys later steps' data

Controls to rate:
| ID | Control |
|----|---------|
| 8.1 | Retry limits on LLM and external API calls |
| 8.2 | Token budget enforcement with hard stop |
| 8.3 | LLM call timeout (thread-based or async) |
| 8.4 | Fail-safe defaults: partial failure → UNKNOWN, not crash |

### Data Protection

Search for:
- PII masking before LLM calls: Presidio, spaCy, regex patterns
- Entity types detected: PERSON, EMAIL, PHONE_NUMBER, national IDs
- Whether LLM output (generated text) is scanned for PII before writing to disk
- Upload size limits
- Whether outputs are encrypted at rest
- Data retention policy for generated files and audit logs

Controls to rate:
| ID | Control |
|----|---------|
| DP1 | PII masking runs before every LLM call (G5 equivalent) |
| DP2 | PII entity list covers relevant jurisdiction (phone, national ID, etc.) |
| DP3 | Output (LLM-generated text) scanned for PII before writing to disk |
| DP4 | Upload / input size limits enforced |
| DP5 | Data retention / deletion policy exists for outputs and audit logs |
| DP6 | Privacy notice in UI (if applicable) |

### Infrastructure & Container

Search for:
- `Dockerfile`: presence of `USER` directive (non-root)
- `.streamlit/config.toml` or equivalent: XSRF, upload size, auth
- Whether UI has authentication (OAuth, SSO, API key) or is open
- Secrets baked into image (check for `.env` COPY without removal)

Controls to rate:
| ID | Control |
|----|---------|
| IC1 | Container runs as non-root user |
| IC2 | No secrets baked into container image |
| IC3 | XSRF / CSRF protection enabled |
| IC4 | UI requires authentication (or is explicitly internal-only) |

### Monitoring & Audit

Search for:
- Audit logger module — what fields are captured per run
- Whether audit logs are immutable (blob storage, append-only)
- Azure Monitor / OpenTelemetry / structured logging
- Alerting rules for anomalous behaviour (token spikes, repeated failures)

Controls to rate:
| ID | Control |
|----|---------|
| M1 | Immutable audit log written before output is accessible |
| M2 | Audit log captures: run ID, input source, PII counts, token usage, status |
| M3 | Logs stored in separate trust boundary from the agent |
| M4 | Alerting on security-relevant events (failures, token spikes, unknown fields) |

### Incident Response

Search for:
- `docs/INCIDENT_RESPONSE.md` or similar
- Kill switch procedure documented
- Credential revocation steps documented
- Contact list for incidents

Controls to rate:
| ID | Control |
|----|---------|
| IR1 | Kill switch procedure documented (agent offline in < 60s) |
| IR2 | Incident response runbook: Detect → Contain → Eradicate → Recover |
| IR3 | Credential revocation steps for every external integration |
| IR4 | Contacts and escalation path documented |

### Adversarial Testing

Search for:
- Test fixtures for injection attacks (e.g. `pdd_with_injection.txt`)
- Tests that assert injected content does NOT appear in output
- PII leakage tests
- Whether eval/guardrail tests run in CI or are excluded

Controls to rate:
| ID | Control |
|----|---------|
| AT1 | Injection test fixtures exist |
| AT2 | Tests assert injected instructions are NOT reflected in output |
| AT3 | PII leakage tests exist |
| AT4 | Adversarial tests run in CI (not excluded) |

---

## Phase 3 — Produce SECURITY_CHECKLIST.md

Write `SECURITY_CHECKLIST.md` to the project root with this exact structure:

```markdown
# Security Checklist — [Project Name]

Generated: [date]
Framework: OWASP AI Agent Security Cheat Sheet + AI Agent Security Workshop

### Legend
- ✅ COVERED — control is implemented
- ⚠️ PARTIAL — partially addressed, gap noted
- ❌ MISSING — not implemented
- N/A — not applicable to this architecture

---

## Summary

| Tier | Count |
|------|-------|
| ✅ COVERED | N |
| ⚠️ PARTIAL | N |
| ❌ MISSING | N |
| N/A | N |

**Overall posture:** [one sentence — e.g. "Strong input controls, gaps in output scanning and container hardening"]

---

## [Each ASI section from Phase 2]

[Table of controls with status + evidence/gap column]

[Remediation block for every PARTIAL or MISSING control — specific file, function, and what to add]

---

## Priority Action List

### Fix Immediately (High Risk)
| Gap | File | What to add |
|-----|------|-------------|

### Fix Soon (Medium Risk)
| Gap | File | What to add |
|-----|------|-------------|

### Fix When Infrastructure is Ready (Low Risk / Ops)
| Gap | Action |
|-----|--------|

---

## Verification

[How to verify each fix — test commands, docker commands, manual checks]
```

Evidence column must cite the actual file path and function name (or "not found") — never say "appears to be" or "seems like". If you can't find the code, rate it MISSING.

---

## Phase 4 — Produce SECURITY_FIXES_TODO.md (if any gaps found)

If there are any PARTIAL or MISSING controls, also write `SECURITY_FIXES_TODO.md`
with the same "Fix Immediately / Fix Soon / Fix When Ready" structure.

For each fix, provide:
- The exact file path
- The exact code change or snippet to add
- Where in the file to place it (before/after which function or line)

This file is the implementation queue — specific enough that a developer can
work through it without needing to re-run the assessment.

---

## Guardrails for this skill

- Do NOT modify any source files — read only.
- Do NOT skip controls because the project "seems" secure. Check the code.
- Do NOT rate a control COVERED based on documentation alone — find the code.
- Do NOT produce generic advice — every finding must cite a specific file.
- If the project has no CLAUDE.md or README, ask the user to describe the
  architecture before proceeding.
- Evidence column: always `file.py:line_number` or `"not found in codebase"`.
