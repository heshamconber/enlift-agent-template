---
description: Run the Enlift mandatory verification checklist on the current draft output before returning it to the operator.
allowed-tools: Read, Grep
---

Run the verify-output skill against the current draft.

Walk through the full checklist:
1. Grounding check — every factual claim sourced
2. Hallucinated reference check — every cited entity verified
3. Success criteria check — match against docs/SUCCESS_CRITERIA.md
4. PII leakage check — scan for unmasked PII
5. Scope check — match against docs/SPEC.md "Out of scope"

Report PASS or FAIL with specifics. If FAIL, list each issue with a concrete revision action.

Two-strike rule: if this is the second failure on the same output, escalate to the operator instead of revising again.
