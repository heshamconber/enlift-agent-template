---
name: mask-pii
description: Masks PII in text before it is sent to the model or written to logs. Use whenever processing tickets, emails, documents, or any external content. Mandatory for all Enlift agents.
allowed-tools: Read, Grep, Bash(python3 .claude/skills/mask-pii/scripts/mask.py *)
---

# PII Masking

Invoke **before** sending any external content to the model or writing to logs. If unsure, invoke anyway.

## How to use

```bash
# Mask a file
python3 .claude/skills/mask-pii/scripts/mask.py input.txt > masked.txt

# Mask from stdin
echo "$content" | python3 .claude/skills/mask-pii/scripts/mask.py
```

Masks: emails → `[EMAIL_xxxx]`, phones → `[PHONE_xxxx]`, government IDs → `[GOVID_xxxx]`, financial IDs → `[FINANCIAL_xxxx]`. Tokens are stable within a session so the model can reason about the same person appearing multiple times.

## If masking fails (non-zero exit code)

1. Do not proceed with the unmasked content.
2. Log a `pii_mask_failure` event via the audit-log skill.
3. Escalate to the operator.
