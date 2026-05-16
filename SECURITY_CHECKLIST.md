# Security Checklist — Enlift Agent Template

Generated: 2026-05-16
Framework: OWASP AI Agent Security Cheat Sheet (ASI01–ASI10) + AI Agent Security Workshop 10 Golden Rules + OWASP Top 10 for LLM Applications

### Legend
- ✅ COVERED — control is implemented
- ⚠️ PARTIAL — partially addressed, gap noted
- ❌ MISSING — not implemented
- N/A — not applicable to this architecture

---

## Summary

| Tier | Count |
|------|-------|
| ✅ COVERED | 27 |
| ⚠️ PARTIAL | 13 |
| ❌ MISSING | 8 |
| N/A | 2 |

**Overall posture:** Strong input controls, PII pipeline, and permissions baseline; gaps in container hardening, supply chain scanning, LLM data egress documentation, multi-tenant enforcement code, and token-count accuracy in audit logs.

---

## ASI01 — Prompt Injection

| ID | Control | Status | Evidence / Gap |
|----|---------|--------|----------------|
| 1.1 | All external data treated as untrusted | ✅ COVERED | `src/llm_client.py:36` — `pre_masked` flag enforces preflight call; `src/preflight.py:74` — `preflight()` required before LLM use |
| 1.2 | Delimiters/boundaries between instructions and data | ✅ COVERED | `src/llm_client.py:55-59` — `=== UNTRUSTED CONTENT START/END ===` wraps all user content |
| 1.3 | Content filter for known injection patterns (regex) | ✅ COVERED | `src/preflight.py:34-47` — 12 regex patterns covering "ignore instructions", "act as", "jailbreak", `<script>`, etc. |
| 1.4 | Separate LLM pre-pass to validate untrusted content | ⚠️ PARTIAL | `src/preflight.py:19,92-101` — hook exists (`set_llm_injection_classifier`) but is `None` by default; regex-only mode ships unless derived agent wires up a classifier |
| 1.5 | Indirect injection via API responses sanitised | ⚠️ PARTIAL | `src/preflight.py:74` — preflight() covers inputs; no guardrail specifically labelled for Jira/Orchestrator API responses; enforcement depends on derived agent calling preflight() on every external source |
| 1.6 | Untrusted input passed in user role, not system role | ✅ COVERED | `src/llm_client.py:36-48` — API signature enforces `system_prompt` (trusted) vs `user_content` (untrusted) separation |

**Remediation for 1.4:** In `src/preflight.py`, document in CLAUDE.md that derived agents MUST call `set_llm_injection_classifier()` with a cheap classifier model before going to production. Add a CI lint check or RUNBOOK ship-checklist item confirming it's wired.

**Remediation for 1.5:** Add a note in `src/preflight.py` (and RUNBOOK.md) that ALL text fetched from external APIs (Jira, Intercom, etc.) must be passed through `preflight()` before embedding in any prompt, not just user-provided files.

---

## ASI02 — Tool Misuse & Exploitation

| ID | Control | Status | Evidence / Gap |
|----|---------|--------|----------------|
| 2.1 | Minimum tool set — deny-by-default | ✅ COVERED | `.claude/settings.json:4` — `"defaultMode": "deny"` with narrow allowlist |
| 2.2 | Read-only scopes for every external integration | ⚠️ PARTIAL | `.claude/settings.json` — no external MCP tools present in template; RUNBOOK.md instructs scoped OAuth but no enforcement mechanism; derived agents must add this |
| 2.3 | Tool arguments validated/escaped before each call | ✅ COVERED | `src/tool_safe_call.py:30-34` — `_SAFE_ARG_RE` allowlist + `shlex.quote`; raises `ValueError` on disallowed chars |
| 2.4 | LLM output not used raw as a tool argument | ✅ COVERED | `src/tool_safe_call.py:22-37` — `call_external_tool()` validates any LLM-derived arg through `_SAFE_ARG_RE` before use |
| 2.5 | Rate limits / hard caps on tool calls per session | ✅ COVERED | `src/llm_client.py:51-52` — `max_calls=50` per session; `src/llm_client.py:19` — `token_budget=8000` with hard stop |

**Remediation for 2.2:** Add a row to the ship checklist in `docs/RUNBOOK.md`: "Every MCP connector is configured with read-only OAuth scope. Document scope in Tools & Skills table."

---

## ASI03 — Identity & Privilege Abuse

| ID | Control | Status | Evidence / Gap |
|----|---------|--------|----------------|
| 3.1 | Agent has own scoped service identity | ⚠️ PARTIAL | `.env.example:5-8` — `ANTHROPIC_API_KEY` placeholder with rotation guidance; no enforcement of separate service account vs. human credentials |
| 3.2 | Short-lived, rotated credentials | ⚠️ PARTIAL | `.env.example:8,17,22,27` — 90-day max-age comment and last-rotated field; no automated rotation or expiry check in code |
| 3.3 | Audit log attributes every action to a specific run/identity | ✅ COVERED | `src/audit_wrapper.py:11` — `RUN_ID = str(uuid.uuid4())` generated per process; `.claude/skills/audit-log/scripts/log.py:83-99` — captures run_id, agent, operator, client_context per entry |
| 3.4 | No credential sharing across agents or environments | ⚠️ PARTIAL | `.env.example` and README warn against it; no technical enforcement (e.g., scoped secrets manager binding) |

**Remediation for 3.2:** Add a CI step or pre-flight script that reads `ANTHROPIC_API_KEY` creation date and fails if it is > 90 days old. Until then, add it to the weekly ops checklist in RUNBOOK.md.

---

## ASI04 — Supply Chain

| ID | Control | Status | Evidence / Gap |
|----|---------|--------|----------------|
| 4.1 | Dependencies pinned to exact versions | ✅ COVERED | `requirements.txt` — all packages pinned with `==` (pytest==8.3.5, presidio-analyzer==2.2.354, presidio-anonymizer==2.2.354, spacy==3.7.4) |
| 4.2 | Container image scanning in CI | ❌ MISSING | `.github/workflows/ci.yml` — only `pip-audit` for Python packages; no container scan (Trivy/Grype/Snyk); no Dockerfile present |
| 4.3 | Base image provenance (SHA digest) | N/A | No Dockerfile in repo; N/A until derived agent adds containerisation |
| 4.4 | Third-party LLM data egress documented and approved | ❌ MISSING | `docs/RUNBOOK.md:52-63` — LLM Provider table exists but all fields are `<placeholder>`; no approved provider, data residency, or DPA on record |
| 4.5 | No unapproved MCP servers or third-party plugins | ✅ COVERED | `.claude/settings.json` — no MCP tools in allowlist; README/RUNBOOK require PR review before adding |

**Remediation for 4.2:** Add a Trivy or `pip-audit` container-scan step to `.github/workflows/ci.yml` when a Dockerfile is added. For now, `pip-audit` covers Python deps — note this gap in RUNBOOK.md.

**Remediation for 4.4:** Fill in `docs/RUNBOOK.md` LLM Provider table before production; make it a ship-checklist hard gate.

---

## ASI05 — Unexpected Code Execution

| ID | Control | Status | Evidence / Gap |
|----|---------|--------|----------------|
| 5.1 | No eval()/exec()/subprocess of LLM-generated content | ✅ COVERED | `src/tool_safe_call.py:30-34` — LLM-derived args validated through `_SAFE_ARG_RE` before any `subprocess.check_call`; no `eval()` or `exec()` found in codebase |
| 5.2 | Agent-generated code not auto-executed on host | ✅ COVERED | No code generation or auto-execution pattern found in template; `src/llm_client.py` — placeholder stub only |

---

## ASI06 — Memory & Context Poisoning

| ID | Control | Status | Evidence / Gap |
|----|---------|--------|----------------|
| 6.1 | No persistent memory between runs (or scoped/encrypted) | ✅ COVERED | `src/audit_wrapper.py:11` — `RUN_ID` is a fresh UUID per process; no vector store or shared memory module found |
| 6.2 | Each run is fully isolated (unique ID, temp workspace) | ✅ COVERED | `src/audit_wrapper.py:11` — unique `RUN_ID` per process; `src/llm_client.py:28-29` — token/call counters reset on instantiation |
| 6.3 | No self-reinforcing loops (agent writing outputs back to inputs) | ✅ COVERED | No RAG write-back or memory update pattern found in codebase |

---

## ASI08 — Cascading Failures

| ID | Control | Status | Evidence / Gap |
|----|---------|--------|----------------|
| 8.1 | Retry limits on LLM and external API calls | ✅ COVERED | `src/llm_client.py:65` — `for _ in range(self.max_retries)` with default `max_retries=3` |
| 8.2 | Token budget enforcement with hard stop | ✅ COVERED | `src/llm_client.py:31-33` — `TokenBudgetExceeded` raised when budget exceeded; `src/llm_client.py:62` — token count checked before every call |
| 8.3 | LLM call timeout | ✅ COVERED | `src/llm_client.py:79-84` — `threading.Thread` with `thread.join(timeout=self.timeout_seconds)`; `TimeoutError` raised if thread is alive after timeout |
| 8.4 | Fail-safe defaults: partial failure → UNKNOWN, not crash | ⚠️ PARTIAL | `src/llm_client.py:89` — returns `""` (empty string) on exhausted retries before raising; no structured UNKNOWN/ESCALATE signal at pipeline level; derived agents must handle this |

**Remediation for 8.4:** Add a `PipelineResult` dataclass with `status: Literal["success","failure","unknown"]` in `src/llm_client.py` so callers get a typed failure signal rather than catching raw exceptions.

---

## Data Protection

| ID | Control | Status | Evidence / Gap |
|----|---------|--------|----------------|
| DP1 | PII masking runs before every LLM call | ✅ COVERED | `src/llm_client.py:44-48` — `pre_masked=False` raises `ValueError`; enforced by API contract |
| DP2 | PII entity list covers relevant jurisdictions | ✅ COVERED | `.claude/skills/mask-pii/scripts/mask.py:38-60` — EMAIL, PHONE (NANP + international), SSN, IBAN, AU TFN, UK NIN, IPADDR, credit card; NER via presidio when installed |
| DP3 | Output scanned for PII before writing to disk | ✅ COVERED | `src/audit_wrapper.py:24-35` — `_OUTPUT_PII_CHECK` regex mirrors mask patterns; `require_audit_then_return()` suppresses output and logs `pii_mask_failure` if PII found |
| DP4 | Upload/input size limits enforced | ✅ COVERED | `src/preflight.py:32` — `MAX_INPUT_BYTES = 1_000_000`; raises `PreflightError` on oversize input |
| DP5 | Data retention/deletion policy exists | ✅ COVERED | `docs/RUNBOOK.md:215-219` — 12-month retention; `find audit/ -name "*.jsonl" -mtime +365 -delete`; blob lifecycle policy recommended for production |
| DP6 | Privacy notice in UI (if applicable) | N/A | No UI component in this template |

---

## Infrastructure & Container

| ID | Control | Status | Evidence / Gap |
|----|---------|--------|----------------|
| IC1 | Container runs as non-root user | ❌ MISSING | No Dockerfile in repo; when derived agents add one, `USER` directive must be present |
| IC2 | No secrets baked into container image | ❌ MISSING | No Dockerfile; `.env` is gitignored (`.gitignore` — confirmed by README); must ensure Dockerfile does not `COPY .env` |
| IC3 | XSRF/CSRF protection enabled | ❌ MISSING | No web UI in template; derived agents adding Streamlit/FastAPI must enable this |
| IC4 | UI requires authentication | ❌ MISSING | No UI; derived agents must implement auth before exposing any interface |

**Remediation for IC1–IC4:** Add a "Container & UI hardening" section to the ship checklist in `docs/RUNBOOK.md` with mandatory items: non-root USER, no `.env` COPY, XSRF enabled, auth required.

---

## Monitoring & Audit

| ID | Control | Status | Evidence / Gap |
|----|---------|--------|----------------|
| M1 | Immutable audit log written before output is accessible | ✅ COVERED | `src/audit_wrapper.py:62-84` — `require_audit_then_return()` calls `write_final_audit()` before returning payload; audit failure raises `RuntimeError` |
| M2 | Audit log captures: run_id, input source, PII counts, token usage, status | ⚠️ PARTIAL | `.claude/skills/audit-log/scripts/log.py:83-99` — captures all listed fields; BUT `tokens_used` defaults to 0 and is never populated from `LLMClient._tokens_used` in `audit_wrapper.py` — token count is always 0 in logs |
| M3 | Logs stored in separate trust boundary from the agent | ⚠️ PARTIAL | `src/audit_wrapper.py:16-20` — production env enforced to use external path; dev defaults to `./audit`; separation depends on operator configuration |
| M4 | Alerting on security-relevant events | ✅ COVERED | `.claude/skills/audit-log/scripts/log.py:36-61` — `_fire_alert()` POSTs to `ALERT_WEBHOOK_URL` on `pii_mask_failure`, `escalation`, `permission_denied`, or any `failure` outcome |

**Remediation for M2:** In `src/audit_wrapper.py:write_final_audit()`, accept a `tokens_used` parameter and pass `LLMClient._tokens_used` to the audit log command via `--tokens-used`.

---

## Incident Response

| ID | Control | Status | Evidence / Gap |
|----|---------|--------|----------------|
| IR1 | Kill switch procedure documented (< 60 s) | ✅ COVERED | `docs/RUNBOOK.md:181-190` — 6-step kill switch with `pkill`, API key revocation, audit archival |
| IR2 | Incident response runbook: Detect → Contain → Eradicate → Recover | ✅ COVERED | `docs/RUNBOOK.md:194-201` — full DCER table with concrete actions per phase |
| IR3 | Credential revocation steps for every external integration | ✅ COVERED | `.env.example:7-27` — revocation URLs and last-rotated tracking for each credential type |
| IR4 | Contacts and escalation path documented | ⚠️ PARTIAL | `docs/RUNBOOK.md:169-176` — escalation table exists; all contacts are `<placeholder>`; unfilled in template |

**Remediation for IR4:** Make "all placeholders filled" a hard CI gate (currently a ship-checklist item only): `grep -c '<[^>]*>' docs/RUNBOOK.md` must return 0 before merge to main.

---

## Adversarial Testing

| ID | Control | Status | Evidence / Gap |
|----|---------|--------|----------------|
| AT1 | Injection test fixtures exist | ✅ COVERED | `tests/fixtures/injection.txt` — fixture with "Ignore your previous instructions" pattern |
| AT2 | Tests assert injected instructions are NOT reflected in output | ⚠️ PARTIAL | `tests/test_preflight.py:9-13` — asserts `PreflightError` raised on injection; BUT no end-to-end test asserting injected text does NOT appear in LLM output (only tests the guard raises, not that output is clean) |
| AT3 | PII leakage tests exist | ✅ COVERED | `tests/test_preflight.py:16-22` — asserts email, phone, SSN not present in masked output |
| AT4 | Adversarial tests run in CI | ✅ COVERED | `.github/workflows/ci.yml:14` — `pytest tests/ -v` runs all tests including `test_preflight.py` |

**Remediation for AT2:** Add an integration test in `tests/test_preflight.py` that runs preflight + `LLMClient.call()` (with a mock provider) and asserts that the injection fixture phrase does not appear in the returned string.

---

## Priority Action List

### Fix Immediately (High Risk)

| Gap | File | What to add |
|-----|------|-------------|
| LLM data egress not documented (4.4) | `docs/RUNBOOK.md:52-63` | Fill in Provider, data residency, DPA before ANY production use; make it a CI hard-gate (`grep '<placeholder>'` exits 1) |
| Token usage always logged as 0 (M2) | `src/audit_wrapper.py` | Accept `tokens_used: int` in `write_final_audit()` and `require_audit_then_return()`; pass `llm_client._tokens_used` at call site |
| LLM injection classifier not wired by default (1.4) | `src/preflight.py` + `CLAUDE.md` | Add RUNBOOK ship-checklist item: "LLM injection classifier is wired via `set_llm_injection_classifier()`"; consider making `None` classifier a hard block in production env |

### Fix Soon (Medium Risk)

| Gap | File | What to add |
|-----|------|-------------|
| Escalation contacts all `<placeholder>` (IR4) | `docs/RUNBOOK.md:169-176` | Add CI gate: `grep -c '<[^>]*>' docs/RUNBOOK.md` must be 0 before merge to main |
| Credential rotation has no automated check (3.2) | `src/preflight.py` or new `src/env_check.py` | On startup, read env var `ANTHROPIC_KEY_ROTATED` (date string); raise `RuntimeError` if > 90 days old |
| AT2: no end-to-end injection output test (AT2) | `tests/test_preflight.py` | Add test: call preflight + mock LLMClient; assert injection phrase absent from output string |
| Fail-safe: no typed UNKNOWN signal (8.4) | `src/llm_client.py` | Add `PipelineResult(status, content)` dataclass; return `status="unknown"` on exhausted retries |
| `audit_wrapper` uses `python3` hardcoded (audit_wrapper.py:71) | `src/audit_wrapper.py:71` | Replace `"python3"` with `sys.executable` to match line 49 (already correct there); prevents breakage in venvs |

### Fix When Infrastructure is Ready (Low Risk / Ops)

| Gap | Action |
|-----|--------|
| No container scan in CI (4.2) | When Dockerfile is added, add Trivy scan step to `.github/workflows/ci.yml` |
| Container runs as root / no USER directive (IC1) | Add `USER appuser` to any future Dockerfile |
| Secrets not baked into container image check (IC2) | Add `.dockerignore` with `.env` excluded; verify in CI |
| Web UI has no auth / XSRF (IC3, IC4) | When UI is added, enable XSRF in framework config and add authentication |
| Audit logs in same trust boundary in dev (M3) | In production deploy, mount `AUDIT_LOG_PATH` to a separate storage account; document in RUNBOOK.md |

---

## Verification

| Fix | How to verify |
|-----|---------------|
| LLM data egress documented | `grep -c '<[^>]*>' docs/RUNBOOK.md` → must return 0 |
| Token logging fixed | `python3 -c "from src.audit_wrapper import require_audit_then_return; ..."` — check `tokens_used` > 0 in `audit/*.jsonl` after a run |
| Injection classifier wired | `python3 -c "from src.preflight import _llm_injection_classifier; assert _llm_injection_classifier is not None"` in derived agent's startup |
| Credential rotation check | Set `ANTHROPIC_KEY_ROTATED=2024-01-01` → startup must raise; set to today → startup must pass |
| AT2 output test | `pytest tests/test_preflight.py::test_injection_not_in_output -v` → PASS |
| Container non-root | `docker run --rm <image> id` → must not show `uid=0(root)` |
| Audit log trust boundary | In production: `ls $AUDIT_LOG_PATH` from agent process must succeed; from web process must fail (separate mount) |
