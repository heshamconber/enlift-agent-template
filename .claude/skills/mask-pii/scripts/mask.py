#!/usr/bin/env python3
"""
Enlift PII masking script.

Usage:
    python3 mask.py <file>        # mask a file, print to stdout
    python3 mask.py               # read from stdin
    echo "text" | python3 mask.py

A per-session random salt is generated at startup and kept in memory only.
The same value in two different sessions produces different tokens, preventing
cross-session and cross-client correlation of masked identifiers.

Exit codes:
    0  — masking succeeded, no PII survived
    1  — PII survived the mask pass (masking failure)
    2  — I/O error
"""

import hashlib
import os
import re
import secrets
import sys

# Per-session salt — in memory only, never logged or persisted
_SESSION_SALT = secrets.token_hex(16)

# PII patterns — ordered from most specific to least specific
_PATTERNS = [
    ("FINANCIAL", re.compile(
        r"\b[A-Z]{2}\d{2}[A-Z0-9]{4,32}\b"                 # IBAN
        r"|\b(?:\d[ -]?){13,16}\b"                           # credit card (basic Luhn-range)
    )),
    ("GOVID", re.compile(
        r"\b\d{3}-\d{2}-\d{4}\b"                             # US SSN
        r"|\b\d{2}/\d{6}/\d\b"                               # AU TFN (loose)
    )),
    ("EMAIL", re.compile(
        r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
    )),
    ("PHONE", re.compile(
        r"\+?1?\s?[\(\-]?\d{3}[\)\-\s]?\s?\d{3}[\-\s]?\d{4}"  # NANP
        r"|\+?\d[\d\s\-\(\)]{6,}\d"                             # international (loose)
    )),
]

# Verification pass — catches survivors
_VERIFY_PATTERNS = [p for _, p in _PATTERNS]


def _token(label: str, value: str) -> str:
    digest = hashlib.sha256((_SESSION_SALT + value).encode()).hexdigest()[:8]
    return f"[{label}_{digest}]"


def mask(text: str) -> str:
    for label, pattern in _PATTERNS:
        text = pattern.sub(lambda m: _token(label, m.group()), text)
    return text


def _has_survivors(text: str) -> bool:
    return any(p.search(text) for p in _VERIFY_PATTERNS)


def main() -> int:
    try:
        if len(sys.argv) > 1:
            with open(sys.argv[1], encoding="utf-8", errors="replace") as fh:
                raw = fh.read()
        else:
            raw = sys.stdin.read()
    except OSError as exc:
        print(f"[mask-pii] I/O error: {exc}", file=sys.stderr)
        return 2

    masked = mask(raw)

    if _has_survivors(masked):
        print("[mask-pii] FAILURE: PII survived masking pass.", file=sys.stderr)
        print("[mask-pii] Do not proceed. Log pii_mask_failure and escalate.", file=sys.stderr)
        sys.stdout.write(masked)
        return 1

    sys.stdout.write(masked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
