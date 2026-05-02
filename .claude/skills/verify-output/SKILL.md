---
name: verify-output
description: Runs a structured self-verification check on the agent's output before returning it to the operator. Use as the final step before any final answer, generated document, or completed task. Mandatory for all Enlift agents.
allowed-tools: Read, Grep
---

# Verify Output — Enlift mandatory skill

## When to invoke

**Always invoke this skill before returning a final result to the operator.**

This is not optional. The agent does not "look ready" — it must pass verification, in writing, every time.

## The verification checklist

The skill walks through these checks. **All must pass.**

### 1. Grounding check
For every factual claim in the output:
- Does the source exist in the agent's accessible context (a file, a tool result, a verified document)?
- Can you point to the exact line / chunk / tool response that supports it?
- If no, **the claim must be removed or rewritten as uncertain**.

### 2. Hallucinated reference check
For every cited source, link, file path, person, ticket number, or system name:
- Does it actually exist?
- If you cannot verify it exists, **remove it** — never leave a plausible-looking but unverified reference.

### 3. Success criteria check
- Open `docs/SUCCESS_CRITERIA.md`.
- Walk through each criterion.
- For each: does the current output satisfy it? Yes / No / N/A.
- If any "No", **revise the output**.

### 4. PII leakage check
- Scan the output for unmasked emails, phone numbers, names paired with PII context, financial identifiers.
- If any survive, the mask-pii skill failed earlier — escalate, do not "patch" by manually redacting.

### 5. Scope check
- Open `docs/SPEC.md`, section "Out of scope".
- Does the output stay within scope, or has the agent drifted?
- If drift, **trim the output** to scope and note what was excluded.

## Output of this skill

A short verification report appended to the response, **or** a clear failure with revision instructions.

Example pass:

```
Verification: PASS
- Grounding: 12 claims, all sourced
- References: 4 cited, all verified
- Success criteria: 5/5 met
- PII: clean
- Scope: within bounds
```

Example fail:

```
Verification: FAIL
- Grounding: 1 unsupported claim ("the customer signed in 2023") — remove or source
- References: 1 unverified ticket ID (TICK-9912) — remove
Action: revise and re-run verify-output before returning
```

## Two-strike rule

If verification fails twice on the same output, **stop revising and escalate to the operator**. Do not enter an infinite revision loop. Two failures is a signal that the underlying task needs human re-scoping.

## Why this is mandatory

Anthropic's guidance on agent evaluation distinguishes `pass@k` (succeeded at least once) from `pass^k` (succeeded every time). Demos use `pass@k`. Production needs `pass^k`. Self-verification is what closes the gap. Without it, the agent ships output that "looks right" — which is exactly the failure mode that loses client trust.

This skill is your contract with the business: every output has been checked, against criteria written down before the work started, before it left the agent.

---

*Maintained by Enlift. Do not weaken the checklist.*
