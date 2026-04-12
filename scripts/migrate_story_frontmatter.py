#!/usr/bin/env python3
"""
Story Frontmatter Migration — converts bold-field stories to YAML frontmatter.

Scans _bmad-output/implementation-artifacts/*.md for stories that use the
old-style bold fields (e.g., **Story ID:** 30.23) and converts them to
YAML frontmatter format.

Epic 28+ stories are enforced (exit 1 if any lack frontmatter).
Legacy epics only warn.

Usage:
  python scripts/migrate_story_frontmatter.py              # dry-run
  python scripts/migrate_story_frontmatter.py --apply      # write changes
  python scripts/migrate_story_frontmatter.py --enforce 28  # fail if Epic 28+ lacks FM
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STORY_DIR = PROJECT_ROOT / "_bmad-output" / "implementation-artifacts"

BOLD_PATTERNS = {
    "story_id": re.compile(r"\*\*Story\s*ID[:\s]*\*\*\s*(\S+)", re.IGNORECASE),
    "epic_id": re.compile(r"\*\*Epic[:\s]*\*\*\s*(\S+)", re.IGNORECASE),
    "status": re.compile(r"\*\*Status[:\s]*\*\*\s*(.+)", re.IGNORECASE),
    "priority": re.compile(r"\*\*Priority[:\s]*\*\*\s*(\S+)", re.IGNORECASE),
    "estimate_hours": re.compile(r"\*\*Estimate[:\s]*\*\*\s*(\d+)", re.IGNORECASE),
}


def has_yaml_frontmatter(content: str) -> bool:
    return content.startswith("---\n")


def extract_bold_fields(content: str) -> dict:
    fields: dict = {}
    for key, pattern in BOLD_PATTERNS.items():
        match = pattern.search(content[:500])
        if match:
            val = match.group(1).strip()
            if key == "estimate_hours":
                fields[key] = int(val)
            else:
                fields[key] = val
    return fields


def extract_epic_num(filename: str) -> int | None:
    match = re.match(r"(\d+)\.", filename)
    return int(match.group(1)) if match else None


def inject_frontmatter(content: str, fields: dict) -> str:
    fm = {
        "doc_type": "story",
        **fields,
        "depends_on": [],
        "blocks": [],
        "trace": {"decisions": [], "bugs": []},
    }
    fm_str = yaml.dump(fm, allow_unicode=True, default_flow_style=False).strip()
    return f"---\n{fm_str}\n---\n\n{content}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--enforce", type=int, default=28)
    args = parser.parse_args()

    if not STORY_DIR.exists():
        print(f"Story dir not found: {STORY_DIR}")
        sys.exit(1)

    migrated = 0
    warnings = 0
    enforced_failures = 0

    for story_file in sorted(STORY_DIR.glob("*.md")):
        content = story_file.read_text(encoding="utf-8")
        if has_yaml_frontmatter(content):
            continue

        epic_num = extract_epic_num(story_file.name)
        fields = extract_bold_fields(content)

        if not fields.get("story_id"):
            sid_match = re.match(r"(\d+\.\d+)", story_file.name)
            if sid_match:
                fields["story_id"] = sid_match.group(1)

        if not fields.get("epic_id") and epic_num is not None:
            fields["epic_id"] = f"EPIC-{epic_num}"

        is_enforced = epic_num is not None and epic_num >= args.enforce

        if is_enforced:
            if args.apply:
                new_content = inject_frontmatter(content, fields)
                story_file.write_text(new_content, encoding="utf-8")
                migrated += 1
                print(f"MIGRATED: {story_file.name}")
            else:
                enforced_failures += 1
                print(f"ENFORCE: {story_file.name} (Epic {epic_num} >= {args.enforce}, needs frontmatter)")
        else:
            warnings += 1
            if not args.apply:
                print(f"WARNING: {story_file.name} (legacy Epic {epic_num}, skip)")

    print(f"\nSummary: {migrated} migrated, {enforced_failures} need migration, {warnings} legacy warnings")
    if enforced_failures > 0 and not args.apply:
        sys.exit(1)


if __name__ == "__main__":
    main()
