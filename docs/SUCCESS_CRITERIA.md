# Success Criteria

> **Fill this in BEFORE coding.** Anthropic's eval guidance is clear: criteria that are written *before* the work always make better tests than criteria invented *after*.

---

## What "done" means for this agent

The agent is considered to be working when **all** of these are true:

### Functional criteria

1. <Concrete, measurable thing #1 — e.g. "Generates a handbook draft for any client following the Enlift handbook structure">
2. <Concrete, measurable thing #2>
3. <Concrete, measurable thing #3>

### Quality criteria

4. **Grounding**: 100% of factual claims in output have a verifiable source in the agent's input context
5. **No hallucinations**: 0 invented references, ticket IDs, person names, or system names
6. **PII**: 0 unmasked PII in output or audit log
7. **Scope**: 0 outputs that drift outside the agent's defined scope

### Reliability criteria

8. **pass^5 ≥ 80%**: across 5 independent runs of the same eval case, the agent succeeds in at least 4. *(This is the production bar — `pass@5` "succeeded at least once" is a demo bar, not a production bar.)*
9. **Verification rate**: ≥ 95% of runs pass `verify-output` on first attempt; remaining runs revise once and pass
10. **Audit completeness**: 100% of runs produce a complete audit log entry

---

## What "done" does NOT mean

- It does **not** mean every possible task succeeds
- It does **not** mean the agent never escalates — escalation when uncertain is correct behaviour
- It does **not** mean the agent works on inputs outside the spec — inputs outside the spec should produce a graceful "out of scope" response

---

## How we measure each criterion

| Criterion | Measurement | Owner |
|---|---|---|
| Functional 1–3 | Eval cases in `tests/eval_cases.md` | <build owner> |
| Grounding | verify-output skill report | Automated |
| No hallucinations | verify-output skill report | Automated |
| PII | mask-pii + verify-output | Automated |
| Scope | verify-output, scope check | Automated |
| pass^5 ≥ 80% | Run eval suite 5 times, count full passes | <reviewer> |

---

## When to revisit

Re-read this document:
- Before starting any new feature
- After any failure in production
- At every quarterly review

If reality has drifted from these criteria, **update the criteria first**, then update the agent. Never the other way around.

---

*Criteria last updated: <date>.*
