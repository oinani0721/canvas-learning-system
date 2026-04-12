#!/usr/bin/env python3
"""
Bidirectional Link Synchronizer — 4-dimension wikilink generator.

Scans Story and Epic files, builds reverse indices, validates references,
and idempotently upserts a `## Relations` section at the end of each file.

Dimensions:
  1. Story → Epic (upward: epic_id field)
  2. Epic → Story list (downward: auto-fill child_stories)
  3. Story ↔ Story (horizontal: depends_on / blocks)
  4. Story ↔ PRD / Decision / Bug (cross-cutting: prd_id, trace.decisions, trace.bugs)

Usage:
  python scripts/sync_links.py              # full sync
  python scripts/sync_links.py --validate   # validate only, no writes
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STORY_DIR = PROJECT_ROOT / "_bmad-output" / "implementation-artifacts"
EPIC_DIR_CANDIDATES = [
    PROJECT_ROOT / "_bmad-output" / "planning-artifacts",
    PROJECT_ROOT / "docs" / "epics",
]
PRD_DIR = PROJECT_ROOT / "_bmad-output" / "planning-artifacts"
META_DIR = PROJECT_ROOT / "docs" / "_meta"
LINK_ERRORS_FILE = META_DIR / "link-errors.md"
SYNC_REPORT_FILE = META_DIR / "sync-report.md"

RELATIONS_HEADER = "## Relations"


def extract_frontmatter(content: str) -> dict | None:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not match:
        return None
    try:
        return yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return None


def find_files(directory: Path, pattern: str = "*.md") -> list[Path]:
    if not directory.exists():
        return []
    return sorted(directory.glob(pattern))


def build_story_index() -> dict[str, dict]:
    index: dict[str, dict] = {}
    for story_file in find_files(STORY_DIR):
        content = story_file.read_text(encoding="utf-8")
        fm = extract_frontmatter(content)
        if not fm or fm.get("doc_type") != "story":
            continue
        sid = fm.get("story_id", "")
        if sid:
            index[sid] = {
                "path": story_file,
                "epic_id": fm.get("epic_id", ""),
                "prd_id": fm.get("prd_id", ""),
                "depends_on": fm.get("depends_on", []) or [],
                "blocks": fm.get("blocks", []) or [],
                "decisions": (fm.get("trace", {}) or {}).get("decisions", []) or [],
                "bugs": (fm.get("trace", {}) or {}).get("bugs", []) or [],
            }
    return index


def build_epic_index() -> dict[str, Path]:
    index: dict[str, Path] = {}
    for epic_dir in EPIC_DIR_CANDIDATES:
        for epic_file in find_files(epic_dir):
            content = epic_file.read_text(encoding="utf-8")
            fm = extract_frontmatter(content)
            if fm and fm.get("doc_type") == "epic":
                eid = fm.get("epic_id", "")
                if eid:
                    index[eid] = epic_file
            elif "EPIC-" in epic_file.name.upper() or "epic" in epic_file.name.lower():
                match = re.search(r"EPIC[_-]?(\d+)", epic_file.name, re.IGNORECASE)
                if match:
                    eid = f"EPIC-{match.group(1)}"
                    index[eid] = epic_file
    return index


def build_reverse_index(story_index: dict) -> dict[str, list[str]]:
    """epic_id → [story_ids]"""
    rev: dict[str, list[str]] = defaultdict(list)
    for sid, data in story_index.items():
        eid = data.get("epic_id", "")
        if eid:
            rev[eid].append(sid)
    for k in rev:
        rev[k].sort()
    return dict(rev)


def validate(
    story_index: dict,
    epic_index: dict[str, Path],
) -> list[str]:
    errors: list[str] = []

    for sid, data in story_index.items():
        eid = data.get("epic_id", "")
        if eid and eid not in epic_index:
            errors.append(f"ORPHAN: Story {sid} references {eid} but no Epic file found")

        for dep in data.get("depends_on", []):
            if str(dep) not in story_index:
                errors.append(f"BROKEN_DEP: Story {sid} depends_on {dep} which doesn't exist")

        for blk in data.get("blocks", []):
            if str(blk) not in story_index:
                errors.append(f"BROKEN_BLOCK: Story {sid} blocks {blk} which doesn't exist")

    dep_graph: dict[str, set[str]] = {}
    for sid, data in story_index.items():
        dep_graph[sid] = {str(d) for d in data.get("depends_on", [])}

    for sid in dep_graph:
        visited: set[str] = set()
        stack = [sid]
        while stack:
            current = stack.pop()
            if current in visited:
                if current == sid:
                    errors.append(f"CIRCULAR: Story {sid} has circular dependency")
                    break
                continue
            visited.add(current)
            stack.extend(dep_graph.get(current, set()))

    return errors


def generate_relations_section(sid: str, data: dict) -> str:
    lines = [RELATIONS_HEADER, ""]

    eid = data.get("epic_id", "")
    if eid:
        lines.append(f"- EPIC: [[{eid}]]")

    prd_id = data.get("prd_id", "")
    if prd_id:
        lines.append(f"- PRD: [[{prd_id}]]")

    deps = data.get("depends_on", [])
    if deps:
        dep_links = ", ".join(f"[[{d}]]" for d in deps)
        lines.append(f"- Depends on: {dep_links}")

    blocks = data.get("blocks", [])
    if blocks:
        blk_links = ", ".join(f"[[{b}]]" for b in blocks)
        lines.append(f"- Blocks: {blk_links}")

    decisions = data.get("decisions", [])
    if decisions:
        dec_links = ", ".join(f"[[{d}]]" for d in decisions)
        lines.append(f"- Decisions: {dec_links}")

    bugs = data.get("bugs", [])
    if bugs:
        bug_links = ", ".join(f"[[{b}]]" for b in bugs)
        lines.append(f"- Bugs: {bug_links}")

    return "\n".join(lines) + "\n"


def upsert_relations(file_path: Path, new_section: str) -> bool:
    content = file_path.read_text(encoding="utf-8")
    idx = content.find(RELATIONS_HEADER)
    if idx != -1:
        next_h2 = content.find("\n## ", idx + len(RELATIONS_HEADER))
        if next_h2 == -1:
            old_section = content[idx:]
        else:
            old_section = content[idx:next_h2]
        if old_section.strip() == new_section.strip():
            return False
        updated = content[:idx] + new_section + (content[next_h2:] if next_h2 != -1 else "")
    else:
        if not content.endswith("\n"):
            content += "\n"
        updated = content + "\n" + new_section

    file_path.write_text(updated, encoding="utf-8")
    return True


def sync(story_index: dict, epic_index: dict, reverse_index: dict) -> dict:
    stats = {"stories_synced": 0, "epics_synced": 0, "skipped": 0}

    for sid, data in story_index.items():
        section = generate_relations_section(sid, data)
        if upsert_relations(data["path"], section):
            stats["stories_synced"] += 1
        else:
            stats["skipped"] += 1

    for eid, epic_path in epic_index.items():
        child_stories = reverse_index.get(eid, [])
        lines = [RELATIONS_HEADER, ""]
        if child_stories:
            lines.append("- Stories:")
            for s in child_stories:
                lines.append(f"  - [[{s}]]")
        section = "\n".join(lines) + "\n"
        if upsert_relations(epic_path, section):
            stats["epics_synced"] += 1

    return stats


def write_errors(errors: list[str]) -> None:
    META_DIR.mkdir(parents=True, exist_ok=True)
    content = "# Link Validation Errors\n\n"
    if not errors:
        content += "No errors found.\n"
    else:
        for e in errors:
            content += f"- {e}\n"
    LINK_ERRORS_FILE.write_text(content, encoding="utf-8")


def write_report(stats: dict, error_count: int) -> None:
    META_DIR.mkdir(parents=True, exist_ok=True)
    content = "# Sync Report\n\n"
    content += f"- Stories synced: {stats.get('stories_synced', 0)}\n"
    content += f"- Epics synced: {stats.get('epics_synced', 0)}\n"
    content += f"- Skipped (unchanged): {stats.get('skipped', 0)}\n"
    content += f"- Validation errors: {error_count}\n"
    SYNC_REPORT_FILE.write_text(content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Bidirectional Link Synchronizer")
    parser.add_argument("--validate", action="store_true", help="Validate only, no writes")
    args = parser.parse_args()

    story_index = build_story_index()
    epic_index = build_epic_index()
    reverse_index = build_reverse_index(story_index)

    errors = validate(story_index, epic_index)
    write_errors(errors)

    if args.validate:
        if errors:
            print(f"Found {len(errors)} validation errors — see docs/_meta/link-errors.md")
            sys.exit(1)
        print(f"Validated {len(story_index)} stories, {len(epic_index)} epics. No errors.")
        return

    stats = sync(story_index, epic_index, reverse_index)
    write_report(stats, len(errors))

    total = stats["stories_synced"] + stats["epics_synced"]
    print(
        f"Synced {total} files ({stats['stories_synced']} stories, "
        f"{stats['epics_synced']} epics). {len(errors)} errors."
    )


if __name__ == "__main__":
    main()
