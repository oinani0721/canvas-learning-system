#!/usr/bin/env python3
"""
Batch add Obsidian `aliases` field to story frontmatter.

Ensures every Story file has `aliases: ["N.M"]` matching its `story_id`,
so that wikilinks like [[1.1]] resolve via Obsidian's alias lookup.

Usage:
  python scripts/batch_add_aliases.py --dry-run   # preview changes
  python scripts/batch_add_aliases.py              # apply changes
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STORY_DIR = PROJECT_ROOT / "_bmad-output" / "implementation-artifacts"


def process_file(story_file: Path, dry_run: bool) -> str | None:
    """Add aliases to a single story file. Returns story_id if modified, None if skipped."""
    content = story_file.read_text(encoding="utf-8")

    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not fm_match:
        return None

    fm_text = fm_match.group(1)
    try:
        fm = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError:
        return None

    if fm.get("doc_type") != "story":
        return None

    sid = fm.get("story_id", "")
    if not sid:
        return None

    aliases = fm.get("aliases", []) or []
    if str(sid) in [str(a) for a in aliases]:
        return None  # already has correct alias

    # Insert aliases line after story_id line (preserves field order)
    sid_line = re.search(r'^(story_id:\s*".*")\s*$', fm_text, re.MULTILINE)
    if not sid_line:
        return None

    pos = sid_line.end()
    new_fm = fm_text[:pos] + f'\naliases: ["{sid}"]' + fm_text[pos:]
    new_content = f"---\n{new_fm}\n---\n" + content[fm_match.end():]

    if not dry_run:
        story_file.write_text(new_content, encoding="utf-8")

    return str(sid)


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch add aliases to story frontmatter")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()

    if not STORY_DIR.exists():
        print(f"Story directory not found: {STORY_DIR}")
        sys.exit(1)

    modified: list[str] = []
    skipped = 0

    for story_file in sorted(STORY_DIR.glob("*.md")):
        result = process_file(story_file, args.dry_run)
        if result:
            modified.append(result)
            action = "would add" if args.dry_run else "added"
            print(f"  {action} aliases: [\"{result}\"] → {story_file.name}")
        else:
            skipped += 1

    mode = "[DRY RUN] " if args.dry_run else ""
    print(f"\n{mode}Modified: {len(modified)}, Skipped: {skipped}")


if __name__ == "__main__":
    main()
