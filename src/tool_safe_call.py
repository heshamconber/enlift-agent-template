"""Helpers to safely pass LLM-derived strings to external tools or shell.

Prefer parameterised APIs over shelling out; these helpers are a minimal
defensive layer to avoid naive `shell=True` usage.
"""
from __future__ import annotations

import re
import shlex
import subprocess
from typing import Sequence

# Allowlist for LLM-derived arguments: word chars, hyphens, dots, @, /, :.
# Blocks flag injection (--exec=, --format=%) that shlex.quote cannot prevent.
_SAFE_ARG_RE = re.compile(r'^[\w\-\.@/:]+$')


def safe_shell_arg(s: str) -> str:
    return shlex.quote(s)


def call_external_tool(cmd_base: Sequence[str], llm_arg: str) -> None:
    """Call an external tool with a single LLM-derived argument safely.

    `cmd_base` should be a list of program and parameters (no shell). The
    LLM-derived argument will be validated against a character allowlist,
    quoted, and appended; prefer libraries with parameterised calls over
    this helper.
    """
    if not _SAFE_ARG_RE.fullmatch(llm_arg):
        raise ValueError(
            f"LLM-derived argument contains disallowed characters: {llm_arg!r}. "
            "Only word chars, hyphens, dots, @, /, and : are permitted."
        )
    safe_arg = safe_shell_arg(llm_arg)
    cmd = list(cmd_base) + [safe_arg]
    subprocess.check_call(cmd)


__all__ = ["safe_shell_arg", "call_external_tool"]
