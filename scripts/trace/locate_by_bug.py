#!/usr/bin/env python3
"""
Bug → Decision → Story → Code locator.

Given a BugID (BUG-XXXXXXXX), traces through:
  1. bug_log.jsonl → bug record (endpoint, error, request_id)
  2. decision_log.jsonl → related decisions by request_id
  3. Story file → BMAD native File List + UAT Script

Reads the same File List section as BMAD code-review Step 1.

Usage:
  python scripts/trace/locate_by_bug.py BUG-12AB34CD
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.trace._story_reader import extract_section, find_story_file, read_file_list
BUG_LOG = PROJECT_ROOT / "backend" / "data" / "bug_log.jsonl"
DECISION_LOG = PROJECT_ROOT / "backend" / "data" / "decision_log.jsonl"
STORY_DIR = PROJECT_ROOT / "_bmad-output" / "implementation-artifacts"


def get_bug_by_id(bug_id: str) -> dict | None:
    if not BUG_LOG.exists():
        return None
    for line in BUG_LOG.read_text(encoding="utf-8").strip().split("\n"):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
            if record.get("bug_id") == bug_id:
                return record
        except json.JSONDecodeError:
            continue
    return None


def find_related_decisions(request_id: str) -> list[dict]:
    if not request_id or not DECISION_LOG.exists():
        return []
    results = []
    for line in DECISION_LOG.read_text(encoding="utf-8").strip().split("\n"):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
            if record.get("request_id") == request_id:
                results.append(record)
        except json.JSONDecodeError:
            continue
    return results


def infer_story_from_endpoint(endpoint: str) -> str | None:
    """Best-effort inference — returns None if ambiguous."""
    return None


def locate(bug_id: str) -> dict:
    bug = get_bug_by_id(bug_id)
    if not bug:
        return {"error": f"Bug {bug_id} not found in {BUG_LOG.relative_to(PROJECT_ROOT)}"}

    request_id = bug.get("request_id", "")
    decisions = find_related_decisions(request_id)

    story_id = bug.get("story_id") or infer_story_from_endpoint(bug.get("endpoint", ""))
    story_file = find_story_file(story_id, STORY_DIR) if story_id else None

    file_list: list[str] = []
    uat_script = ""
    if story_file and story_file.exists():
        file_list = read_file_list(story_file)
        uat_script = extract_section(story_file, "UAT Script")

    return {
        "bug": {
            "bug_id": bug.get("bug_id"),
            "timestamp": bug.get("timestamp"),
            "endpoint": bug.get("endpoint"),
            "error_type": bug.get("error_type"),
            "error_message": bug.get("error_message"),
            "request_id": request_id,
            "story_id": story_id,
        },
        "decisions": [
            {
                "decision_id": d.get("decision_id"),
                "function_name": d.get("function_name"),
                "reason": d.get("reason"),
                "timestamp": d.get("timestamp"),
            }
            for d in decisions
        ],
        "story_file": str(story_file.relative_to(PROJECT_ROOT)) if story_file else None,
        "file_list": file_list,
        "uat_script": uat_script,
    }


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: locate_by_bug.py BUG-XXXXXXXX", file=sys.stderr)
        sys.exit(1)

    bug_id = sys.argv[1]
    result = locate(bug_id)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
