# Definition of Done

> **This is the gate. Every Enlift agent must pass every box before it is considered production-ready.**
> Strictness: **Mandatory.** No exceptions without explicit team approval, documented in the agent's PR.

---

## The Five Mandatory Components

Before this agent ships, each of these must be **true and verifiable**:

### 1. Standard CLAUDE.md ✅
- [ ] `CLAUDE.md` exists at repo root
- [ ] All template placeholders are filled in (no `<placeholders>` left)
- [ ] File is under 200 lines (instruction-following degrades with length)
- [ ] All five Enlift-mandated rules are present and customised: PII, multi-tenant, self-verification, audit logging, permissions
- [ ] Forbidden actions section is intact

### 2. Locked-down permissions baseline ✅
- [ ] `.claude/settings.json` is the unmodified Enlift baseline (or any deviations are documented in PR)
- [ ] `--dangerously-skip-permissions` is **not** used anywhere in scripts, docs, or CI
- [ ] `.gitignore` excludes `.claude/settings.local.json` (personal overrides stay local)
- [ ] Every allowed tool beyond the baseline is justified in `docs/SPEC.md`

### 3. PII masking + audit log ✅
- [ ] `mask-pii` skill is present in `.claude/skills/`
- [ ] `audit-log` skill is present in `.claude/skills/`
- [ ] Spec confirms: every external input is masked before reaching the model
- [ ] Spec confirms: every run produces a complete audit log entry
- [ ] Audit logs go to a directory listed in `.gitignore` (logs are never committed)
- [ ] At least one test case verifies that PII does not survive into output

### 4. Self-verification step ✅
- [ ] `verify-output` skill is present in `.claude/skills/`
- [ ] CLAUDE.md instructs the agent to invoke verification before every final output
- [ ] Two-strike rule is enforced (no infinite revision loops)
- [ ] At least one test case verifies that a deliberately bad input fails verification

### 5. Success criteria + eval cases ✅
- [ ] `docs/SUCCESS_CRITERIA.md` is filled in
- [ ] Criteria were written **before** the agent was built (check git history)
- [ ] `tests/eval_cases.md` has **at least 5** scenarios
- [ ] At least one eval case is an adversarial input (prompt injection attempt, malformed data, out-of-scope request)
- [ ] Eval suite has been run 5 times — **pass^5 ≥ 80%**
- [ ] Eval results are recorded with date and version

---

## Operational readiness

- [ ] `docs/RUNBOOK.md` is filled in — a non-builder can operate this agent from it
- [ ] Owner and reviewer are named in `docs/SPEC.md`
- [ ] Escalation path is defined and tested (one practice escalation logged)
- [ ] Secrets live in `.env` (gitignored), with `.env.example` showing the shape

---

## Review

- [ ] At least one teammate has reviewed the spec, success criteria, and CLAUDE.md
- [ ] Reviewer has run the eval suite themselves
- [ ] PR contains: spec, success criteria, runbook, eval results, threat model

---

## When NOT to ship

Even if every box is checked, **do not ship if any of these are true**:

- Eval pass^5 is between 60–80% — agent is "demo-ready" but not production-ready
- Verification fails on more than 1 in 5 runs — the agent does not yet know when it is wrong
- Threat model has high-impact threats with no mitigation
- Owner is "the team" rather than a named individual

In those cases: ship to a limited pilot, not to production. Track results. Re-run this checklist before broad rollout.

---

## When to re-run this checklist

- Before initial production launch
- After any change to CLAUDE.md, permissions, or skills
- After any security incident
- Quarterly, regardless of changes

---

*This document is the contract every Enlift agent honours. If you find yourself wanting to skip a box, that is the signal to slow down — not to ship.*
