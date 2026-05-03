---
name: verify-output
description: Runs a self-verification check on the agent's output before returning it to the operator. Always invoke as the final step before any answer or completed task. Mandatory for all Enlift agents.
allowed-tools: Read, Grep
---

# Verify Output

Always invoke before returning a final result. Walk through all five checks — all must pass.

## Checklist

1. **Grounding** — every factual claim has a verifiable source in context. If not, remove or mark as uncertain.
2. **References** — every cited file, ticket, person, or system actually exists. If unverifiable, remove it.
3. **Success criteria** — open `docs/RUNBOOK.md` → "Success criteria". Each criterion: pass / fail / N/A. Revise if any fail.
4. **PII** — scan output for unmasked emails, phones, names, IDs. If any found, escalate — do not manually redact.
5. **Scope** — check `docs/RUNBOOK.md` → "Out of scope". Trim anything outside scope.

## Output format

```
Verification: PASS
- Grounding: X claims, all sourced
- References: X cited, all verified
- Success criteria: X/X met
- PII: clean
- Scope: within bounds
```

## Two-strike rule

If verification fails twice on the same output, stop and escalate to the operator. Do not loop a third time.
