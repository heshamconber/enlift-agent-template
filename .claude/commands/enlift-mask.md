---
description: Mask PII in the provided text or file using the Enlift mandatory masking skill before any external content enters the model context.
allowed-tools: Read, Grep
---

Invoke the mask-pii skill on the content the operator just referenced or pasted.

Mask all of the following before proceeding with the task:
- Email addresses
- Phone numbers
- Person names paired with role/title context
- Government IDs (SSN, national ID, passport)
- Financial identifiers (credit card, IBAN)
- Internal client IDs

After masking, scan once more for survivors. If any PII survives, do not proceed — log a `pii_mask_failure` event via the audit-log skill and escalate to the operator.

Return the masked content for the operator to confirm before continuing.
