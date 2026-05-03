#!/usr/bin/env python3
"""
Enlift audit logging script.

Appends a JSON-Lines entry to audit/YYYY-MM-DD.jsonl.
Creates the audit/ directory (chmod 750) if it does not exist.

Usage:
    python3 log.py --event-type session_start --outcome success
    python3 log.py --event-type tool_invocation --tool Read --target "[REDACTED]" --outcome success
    python3 log.py --event-type pii_mask_failure --outcome failure --notes "Email survived"

Environment variables (used as fallback when flags are omitted):
    ENLIFT_AGENT_NAME       — agent identifier
    ENLIFT_CLIENT_CONTEXT   — hashed/anonymised client identifier
    ENLIFT_OPERATOR         — operator email (pre-masked)

Exit codes:
    0  — entry written successfully
    1  — could not write to audit log (agent must halt)
"""

import argparse
import json
import os
import stat
import sys
from datetime import datetime, timezone

AUDIT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "audit")
AUDIT_DIR = os.path.normpath(AUDIT_DIR)

VALID_EVENT_TYPES = {
    "session_start",
    "tool_invocation",
    "pii_mask_invoked",
    "pii_mask_failure",
    "verification_result",
    "final_output",
    "escalation",
    "permission_denied",
}


def ensure_audit_dir(path: str) -> None:
    if not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)
        # chmod 750: owner rwx, group r-x, other ---
        os.chmod(path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP)


def build_entry(args: argparse.Namespace) -> dict:
    now = datetime.now(timezone.utc)
    return {
        "timestamp": now.isoformat(),
        "agent": args.agent or os.environ.get("ENLIFT_AGENT_NAME", "<unknown>"),
        "operator": args.operator or os.environ.get("ENLIFT_OPERATOR", "<unknown>"),
        "client_context": args.client_context or os.environ.get("ENLIFT_CLIENT_CONTEXT", "<unknown>"),
        "event_type": args.event_type,
        "tool": args.tool or "",
        "target": args.target or "",
        "outcome": args.outcome,
        "verification_passed": args.verification_passed,
        "notes": args.notes or "",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Enlift audit log writer")
    parser.add_argument("--event-type", required=True, choices=VALID_EVENT_TYPES)
    parser.add_argument("--tool", default="")
    parser.add_argument("--target", default="", help="Pre-masked path or identifier only")
    parser.add_argument("--outcome", required=True, choices=["success", "failure", "partial"])
    parser.add_argument("--operator", default="")
    parser.add_argument("--client-context", default="")
    parser.add_argument("--agent", default="")
    parser.add_argument("--notes", default="")
    parser.add_argument("--verification-passed", type=lambda v: v.lower() == "true", default=None)
    args = parser.parse_args()

    try:
        ensure_audit_dir(AUDIT_DIR)
    except OSError as exc:
        print(f"[audit-log] CRITICAL: cannot create audit directory: {exc}", file=sys.stderr)
        print("[audit-log] Agent must halt. No audit = not allowed to run.", file=sys.stderr)
        return 1

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log_file = os.path.join(AUDIT_DIR, f"{today}.jsonl")

    entry = build_entry(args)
    line = json.dumps(entry, ensure_ascii=False)

    try:
        with open(log_file, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError as exc:
        print(f"[audit-log] CRITICAL: cannot write to {log_file}: {exc}", file=sys.stderr)
        print("[audit-log] Agent must halt. No audit = not allowed to run.", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
