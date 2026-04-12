#!/usr/bin/env python3
"""
BMAD Process Awareness Check (SessionStart pre-filter)

Reads CURRENT_TASK.md frontmatter to determine if the current session
is in a BMAD workflow. Only when plan_kind starts with "bmad" does it
invoke scan_feedback.py for pending annotation summary.

Non-BMAD workflows get zero injection (exit 0, empty stdout).
Compact source always skips (Anthropic issue #15174).

Usage (called by context-inject.js):
  echo '{"cwd": "...", "source": "startup"}' | python scripts/bmad/bmad_check.py
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import yaml


def main() -> None:
    try:
        stdin_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    cwd = Path(stdin_data.get("cwd", "."))
    source = stdin_data.get("source", "startup")

    if source == "compact":
        sys.exit(0)

    task_file = cwd / "_decisions" / "CURRENT_TASK.md"
    if not task_file.exists():
        sys.exit(0)

    content = task_file.read_text(encoding="utf-8")
    if not content.startswith("---"):
        sys.exit(0)

    fm_end = content.find("---", 3)
    if fm_end == -1:
        sys.exit(0)

    try:
        fm = yaml.safe_load(content[3:fm_end])
    except yaml.YAMLError:
        sys.exit(0)

    if not isinstance(fm, dict):
        sys.exit(0)

    plan_kind = fm.get("plan_kind", "")
    if not isinstance(plan_kind, str) or not plan_kind.startswith("bmad"):
        sys.exit(0)

    try:
        summary = subprocess.check_output(
            [sys.executable, "scripts/bmad/scan_feedback.py", "--mode=pending-summary"],
            cwd=str(cwd),
            text=True,
            timeout=2,
        ).strip()
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        sys.exit(0)

    if not summary or summary == "0":
        sys.exit(0)

    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": f"[BMAD-ANNO] {summary}",
        }
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
