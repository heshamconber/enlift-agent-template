"""Preflight utilities: PII masking and simple injection-detection.

Call `preflight(text)` before passing untrusted text to any LLM client.
This module calls the existing mask script at `.claude/skills/mask-pii/scripts/mask.py`.
"""
from __future__ import annotations

import hmac
import os
import subprocess
import sys
import re
from dataclasses import dataclass, field
from typing import Callable, Optional, Tuple

# Optional hook: derived agents may set this to a callable that takes a
# pre-masked string and returns True if an LLM classifier suspects injection.
# When None, the secondary LLM pre-pass is skipped (regex-only mode).
# Example wiring:
#   from src.preflight import set_llm_injection_classifier
#   set_llm_injection_classifier(my_client.classify_injection)
_llm_injection_classifier: Optional[Callable[[str], bool]] = None


def set_llm_injection_classifier(fn: Callable[[str], bool]) -> None:
    """Register a callable for secondary LLM-based injection detection.

    The callable receives the pre-masked text and must return True if it
    suspects injection, False otherwise. It should use a separate, cheap
    model invocation with a dedicated token budget.
    """
    global _llm_injection_classifier
    _llm_injection_classifier = fn

MAX_INPUT_BYTES = 1_000_000  # 1 MB hard limit — reject anything larger

INJECTION_PATTERNS = [
    re.compile(r"ignore (?:your )?(?:previous|prior|all) instructions", re.I),
    re.compile(r"disregard (?:previous|prior|all) instructions", re.I),
    re.compile(r"(?i)please execute the following commands?"),
    re.compile(r"(?i)you are now(?: a)?"),
    re.compile(r"(?i)act as(?: a| an)?"),
    re.compile(r"(?i)new (?:system )?persona"),
    re.compile(r"(?i)jailbreak"),
    re.compile(r"(?i)developer mode"),
    re.compile(r"(?i)repeat (?:the )?(?:above|following|this) (?:text|prompt|instructions?)?"),
    re.compile(r"(?i)print (?:the )?(?:above|system prompt|instructions?)"),
    re.compile(r"(?i)what (?:are|were) your instructions"),
    re.compile(r"<\s*script", re.I),
]


class PreflightError(RuntimeError):
    pass


# Per-process secret — never logged or persisted. LLMClient validates against this.
_PROOF_SECRET: bytes = os.urandom(32)


@dataclass(frozen=True)
class PreflightResult:
    masked: str
    pii_count: int
    proof: bytes = field(default=b"", repr=False)


def _run_mask(text: str) -> Tuple[int, str, str]:
    """Run the mask script as a subprocess; return (rc, stdout, stderr)."""
    proc = subprocess.Popen(
        [sys.executable, ".claude/skills/mask-pii/scripts/mask.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
    )
    out, err = proc.communicate(text)
    return proc.returncode, out, err


def _injection_detect(text: str) -> bool:
    for p in INJECTION_PATTERNS:
        if p.search(text):
            return True
    return False


def preflight(text: str) -> PreflightResult:
    """Mask PII and run a lightweight injection check.

    Returns a PreflightResult(masked, pii_count) on success.
    Raises `PreflightError` on failure.
    """
    if len(text.encode("utf-8")) > MAX_INPUT_BYTES:
        raise PreflightError(
            f"Input exceeds maximum allowed size ({MAX_INPUT_BYTES} bytes). "
            "Split the input or reject it."
        )

    rc, masked, err = _run_mask(text)
    if rc != 0:
        raise PreflightError(f"PII masking failed: {err.strip()}")

    # Count masked tokens produced by mask.py (format: [LABEL_xxxxxxxx])
    pii_count = len(re.findall(r'\[[A-Z]+_[0-9a-f]{8}\]', masked))

    if _injection_detect(masked):
        raise PreflightError("Injection pattern detected in input — escalate and do not call model")

    if _llm_injection_classifier is not None:
        try:
            if _llm_injection_classifier(masked):
                raise PreflightError(
                    "LLM classifier detected injection — escalate and do not call model"
                )
        except PreflightError:
            raise
        except Exception as exc:
            raise PreflightError(f"LLM injection classifier failed: {exc}") from exc

    proof = hmac.new(_PROOF_SECRET, masked.encode(), "sha256").digest()
    return PreflightResult(masked=masked, pii_count=pii_count, proof=proof)


__all__ = ["preflight", "PreflightError", "PreflightResult", "MAX_INPUT_BYTES", "_PROOF_SECRET"]
