---
name: mask-pii
description: Masks personally identifiable information (PII) in text before it is sent to the model or written to logs. Use when processing tickets, emails, documents, or any external content that may contain names, email addresses, phone numbers, government IDs, or financial account numbers. Mandatory for all Enlift agents.
allowed-tools: Read, Grep
---

# PII Masking — Enlift mandatory skill

## When to invoke

Invoke this skill **before** any of the following:

- Sending ticket content, email content, or document content to the model
- Writing content to the audit log
- Returning output that includes content from external sources

If you are unsure whether content contains PII, invoke this skill anyway. False positives are cheap; leaks are not.

## What gets masked

| Category | Pattern | Replacement |
|---|---|---|
| Email addresses | `name@domain.tld` | `[EMAIL_<hash>]` |
| Phone numbers | international + local formats | `[PHONE_<hash>]` |
| Person names | when paired with role/title context | `[NAME_<hash>]` |
| Government IDs | SSN, national ID, passport patterns | `[GOVID_<hash>]` |
| Credit card / IBAN | Luhn-valid sequences, IBAN format | `[FINANCIAL_<hash>]` |
| Internal client IDs | configurable per-project (see `client-patterns.md`) | `[CLIENT_<hash>]` |

The hash is a stable SHA-256-truncated-to-8 of the original value. This means the same email always masks to the same token within a session, so the model can still reason about "the same person mentioned three times" without seeing the actual identity.

## How to use

```bash
# Mask a file before reading it into context
.claude/skills/mask-pii/scripts/mask.py <input-file> > masked-content.txt

# Mask a string inline
echo "$content" | .claude/skills/mask-pii/scripts/mask.py
```

## What to do if masking fails

1. **Do not proceed with the unmasked content.**
2. Log the failure to the audit log with `[PII_MASK_FAILURE]`.
3. Escalate to the operator — do not attempt to "best-effort" mask manually.

## Verification

After masking, scan the output one more time for:
- Anything that looks like an email (`@` followed by a domain)
- Anything that looks like a phone number (sequences of 7+ digits with separators)
- Proper nouns that don't appear in your project's known entity list

If any of these survive, masking has failed.

## Why this is mandatory

Enlift agents process client data including support tickets and internal documents. A single leak of unmasked PII into a model log, an audit trail, or — worst case — another client's context, is a contractual breach and a regulatory issue. This skill is the first line of defence.

---

*Maintained by Enlift. Do not modify masking patterns without security review.*
