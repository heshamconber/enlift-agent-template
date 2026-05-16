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
    AUDIT_LOG_PATH          — override audit directory (default: ./audit)

Exit codes:
    0  — entry written successfully
    1  — could not write to audit log (agent must halt)
"""

import argparse
import json
import os
import stat
import sys
import urllib.request
from datetime import datetime, timezone

# Env-var override lets production agents write to a separate trust boundary
_default_audit_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "audit")
AUDIT_DIR = os.path.normpath(os.environ.get("AUDIT_LOG_PATH", _default_audit_dir))

_ALERT_WEBHOOK_URL = os.environ.get("ALERT_WEBHOOK_URL", "")
_ALERT_EVENTS = {"pii_mask_failure", "escalation", "permission_denied"}


def _fire_alert(entry: dict) -> None:
    """POST a JSON alert to the configured webhook.

    Fails silently — alerting must never block or mask the audit write.
    """
    if not _ALERT_WEBHOOK_URL:
        return
    try:
        payload = json.dumps({
            "text": (
                f"[{entry['agent']}] Security event: {entry['event_type']} "
                f"| run_id={entry['run_id']} | outcome={entry['outcome']}"
            )
        }).encode()
        req = urllib.request.Request(
            _ALERT_WEBHOOK_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass


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
        "run_id": args.run_id or "",
        "agent": args.agent or os.environ.get("ENLIFT_AGENT_NAME", "<unknown>"),
        "operator": args.operator or os.environ.get("ENLIFT_OPERATOR", "<unknown>"),
        "client_context": args.client_context or os.environ.get("ENLIFT_CLIENT_CONTEXT", "<unknown>"),
        "event_type": args.event_type,
        "tool": args.tool or "",
        "target": args.target or "",
        "outcome": args.outcome,
        "verification_passed": args.verification_passed,
        "pii_count": args.pii_count,
        "tokens_used": args.tokens_used,
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
    parser.add_argument("--run-id", default="", help="UUID correlating all events in one run")
    parser.add_argument("--pii-count", type=int, default=0, help="Number of PII entities masked")
    parser.add_argument("--tokens-used", type=int, default=0, help="LLM tokens consumed")
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

    if args.event_type in _ALERT_EVENTS or args.outcome == "failure":
        _fire_alert(entry)

    return 0


if __name__ == "__main__":
    sys.exit(main())
