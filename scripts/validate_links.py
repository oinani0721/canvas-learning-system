#!/usr/bin/env python3
"""
Pre-commit link validator — ensures wikilinks are Obsidian-resolvable.

Checks:
  1. Every story file has aliases containing its story_id
  2. All [[target]] in ## Relations sections resolve to a file stem or alias

Exit 0 = all OK. Exit 1 = broken links found (blocks commit).

Usage:
  python scripts/validate_links.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STORY_DIR = PROJECT_ROOT / "_bmad-output" / "implementation-artifacts"
EPIC_DIR = PROJECT_ROOT / "_bmad-output" / "planning-artifacts"


def extract_frontmatter(content: str) -> dict | None:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not match:
        return None
    try:
        return yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return None


def main() -> int:
    resolvable: set[str] = set()

    scan_dirs = [d for d in [STORY_DIR, EPIC_DIR] if d.exists()]
    all_files: list[Path] = []
    for d in scan_dirs:
        all_files.extend(sorted(d.glob("*.md")))

    for f in all_files:
        resolvable.add(f.stem)
        content = f.read_text(encoding="utf-8")
        fm = extract_frontmatter(content)
        if fm:
            for alias in fm.get("aliases", []) or []:
                resolvable.add(str(alias))

    errors: list[str] = []

    # Check 1: Every story has aliases containing story_id
    for f in sorted(STORY_DIR.glob("*.md")) if STORY_DIR.exists() else []:
        content = f.read_text(encoding="utf-8")
        fm = extract_frontmatter(content)
        if not fm or fm.get("doc_type") != "story":
            continue
        sid = fm.get("story_id", "")
        aliases = [str(a) for a in (fm.get("aliases", []) or [])]
        if sid and sid not in aliases:
            errors.append(f"MISSING_ALIAS: {f.name} story_id={sid} not in aliases")

    # Check 2: All [[target]] in Relations sections are resolvable
    for f in all_files:
        content = f.read_text(encoding="utf-8")
        idx = content.find("## Relations")
        if idx == -1:
            continue
        relations = content[idx:]
        for target in re.findall(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]", relations):
            if target not in resolvable:
                errors.append(f"BROKEN_LINK: [[{target}]] in {f.name}")

    if errors:
        print(f"Link validation failed ({len(errors)} errors):")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"Link validation OK ({len(resolvable)} resolvable targets)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
