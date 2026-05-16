"""Audit wrapper to ensure final_output is logged before outputs are exposed."""
from __future__ import annotations

import os
import re
import subprocess
import sys
import uuid

# Generated once per process — correlates all audit events from a single run
RUN_ID = str(uuid.uuid4())

# Prevent accidental use of the local ./audit path in production environments.
_AUDIT_PATH = os.environ.get("AUDIT_LOG_PATH", "./audit")
_ENV = os.environ.get("ENLIFT_ENV", "dev")
if _ENV == "production" and _AUDIT_PATH in ("./audit", "audit", ".\\audit"):
    raise RuntimeError(
        "AUDIT_LOG_PATH must point to a separate trust boundary in production. "
        "Set AUDIT_LOG_PATH to an Azure Blob mount, S3 path, or network share."
    )

# Quick PII survivor check on LLM output before it leaves the pipeline.
# Pattern set mirrors mask.py _PATTERNS to ensure output coverage == input coverage.
_OUTPUT_PII_CHECK = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"       # email
    r"|\b\d{3}-\d{2}-\d{4}\b"                                    # SSN
    r"|\+?1?\s?[\(\-]?\d{3}[\)\-\s]?\s?\d{3}[\-\s]?\d{4}"      # NANP phone
    r"|\+?\d[\d\s\-\(\)]{6,}\d"                                   # international phone
    r"|\b[A-Z]{2}\d{2}[A-Z0-9]{4,32}\b"                          # IBAN
    r"|\b\d{2}/\d{6}/\d\b"                                        # AU TFN
    r"|\b[A-CEGHJ-PR-TW-Z]{2}\d{6}[A-D]\b"                      # UK NIN
    r"|\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"                         # IP address
    r"|\b(?:\d[ -]?){13,16}\b"                                    # credit card
)


def _output_has_pii(text: str) -> bool:
    return bool(_OUTPUT_PII_CHECK.search(text))


def write_final_audit(
    agent: str = "<unknown>",
    operator: str = "<unknown>",
    client_context: str = "<unknown>",
    outcome: str = "success",
    tokens_used: int = 0,
) -> None:
    cmd = [
        sys.executable,
        ".claude/skills/audit-log/scripts/log.py",
        "--event-type", "final_output",
        "--agent", agent,
        "--operator", operator,
        "--client-context", client_context,
        "--outcome", outcome,
        "--run-id", RUN_ID,
        "--tokens-used", str(tokens_used),
    ]
    # If audit write fails, raise to prevent leaking output without a record
    subprocess.check_call(cmd)


def require_audit_then_return(
    payload: str,
    *,
    agent: str = "<unknown>",
    operator: str = "<unknown>",
    client_context: str = "<unknown>",
    tokens_used: int = 0,
) -> str:
    if _output_has_pii(payload):
        subprocess.call([
            sys.executable, ".claude/skills/audit-log/scripts/log.py",
            "--event-type", "pii_mask_failure",
            "--outcome", "failure",
            "--notes", "PII detected in LLM output — output suppressed",
            "--agent", agent,
            "--operator", operator,
            "--client-context", client_context,
            "--run-id", RUN_ID,
        ])
        raise RuntimeError(
            "PII detected in output — suppressed. Log pii_mask_failure and escalate."
        )
    write_final_audit(
        agent=agent,
        operator=operator,
        client_context=client_context,
        outcome="success",
        tokens_used=tokens_used,
    )
    return payload


__all__ = ["write_final_audit", "require_audit_then_return", "RUN_ID"]
