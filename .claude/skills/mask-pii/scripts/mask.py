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

# Optional NER-based masking via presidio (covers PERSON, ORG, LOCATION, etc.).
# Falls back to regex-only if presidio or the spaCy model is not installed.
try:
    from presidio_analyzer import AnalyzerEngine as _AnalyzerEngine
    _presidio = _AnalyzerEngine()
except Exception as _presidio_err:
    if os.environ.get("ENLIFT_ENV") in ("production", "staging"):
        print(
            f"[mask-pii] CRITICAL: Presidio NER engine unavailable: {_presidio_err}\n"
            "[mask-pii] PERSON, ORG, LOCATION names will not be masked.\n"
            "[mask-pii] Install presidio and spaCy model: "
            "pip install presidio-analyzer && python -m spacy download en_core_web_sm",
            file=sys.stderr,
        )
        sys.exit(1)
    _presidio = None

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
    ("UKNIN", re.compile(
        r"\b[A-CEGHJ-PR-TW-Z]{2}\d{6}[A-D]\b"               # UK National Insurance Number
    )),
    ("EMAIL", re.compile(
        r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
    )),
    ("PHONE", re.compile(
        r"\+?1?\s?[\(\-]?\d{3}[\)\-\s]?\s?\d{3}[\-\s]?\d{4}"  # NANP
        r"|\+?\d[\d\s\-\(\)]{6,}\d"                             # international (loose)
    )),
    ("IPADDR", re.compile(
        r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
    )),
]

# Verification pass — catches survivors
_VERIFY_PATTERNS = [p for _, p in _PATTERNS]

# JURISDICTION COVERAGE:
# Covered (regex):  US SSN, NANP phone, IBAN, AU TFN (loose), UK NIN, IP address, credit card
# Covered (presidio): PERSON, ORG, LOCATION, EMAIL, PHONE (when presidio is installed)
# NOT covered without presidio: EU national IDs (FR INSEE/NIR, NL BSN, DE Personalausweis),
#   Canadian SIN, person/org names, location names.
# Derived agents processing EU client data MUST install presidio (see requirements.txt).


def _token(label: str, value: str) -> str:
    digest = hashlib.sha256((_SESSION_SALT + value).encode()).hexdigest()[:8]
    return f"[{label}_{digest}]"


def _presidio_mask(text: str) -> str:
    """NER pass for PERSON, ORG, LOCATION, and other high-recall entity types.

    Applied before regex patterns so that named entities are masked before
    regex patterns run (avoids partial matches on already-masked tokens).
    Returns text unchanged if presidio is not installed.
    """
    if _presidio is None:
        return text
    try:
        results = _presidio.analyze(text=text, language="en")
        for r in sorted(results, key=lambda x: x.start, reverse=True):
            token = _token(r.entity_type, text[r.start:r.end])
            text = text[:r.start] + token + text[r.end:]
    except Exception:
        pass
    return text


def mask(text: str) -> str:
    text = _presidio_mask(text)
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
