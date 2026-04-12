"""
Shared Story file reader — single source for File List parsing.

Used by:
  - scripts/trace/locate_by_bug.py  (Phase 6: /bmad-lb)
  - scripts/trace/build_story_file_map.py  (Phase 4: external index)

Reads the BMAD native "### File List" section from Story .md files.
This is the same data source that BMAD dev-story Step 1 and code-review
Step 1 consume, ensuring zero divergence.
"""
from __future__ import annotations

import re
from pathlib import Path


def read_file_list(story_path: Path) -> list[str]:
    """Extract file paths from the BMAD native '### File List' section."""
    text = story_path.read_text(encoding="utf-8")
    return _extract_file_list(text)


def _extract_file_list(text: str) -> list[str]:
    pattern = r"###\s+File\s+List\s*\n(.*?)(?:\n##|\n---|\Z)"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if not match:
        return []

    section = match.group(1)
    files = []
    for line in section.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        cleaned = re.sub(r"^[-*]\s*", "", line).strip()
        cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)
        if cleaned and not cleaned.startswith("#") and not cleaned.startswith("<!--"):
            files.append(cleaned)
    return files


def extract_section(story_path: Path, section_name: str) -> str:
    """Extract the body of any H2/H3 section by name."""
    text = story_path.read_text(encoding="utf-8")
    return _extract_section(text, section_name)


def _extract_section(text: str, section_name: str) -> str:
    escaped = re.escape(section_name)
    pattern = rf"^(#{2,3})\s+{escaped}\s*$"
    match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
    if not match:
        return ""

    level = len(match.group(1))
    start = match.end()

    next_header = re.compile(rf"^#{{{1},{level}}}\s+", re.MULTILINE)
    next_match = next_header.search(text, start)
    if next_match:
        return text[start : next_match.start()].strip()
    return text[start:].strip()


def find_story_file(
    story_id: str,
    story_dir: Path | None = None,
) -> Path | None:
    """Find a Story file by its ID (e.g., '30.23')."""
    if story_dir is None:
        from scripts.lib.planning_utils import get_project_root
        story_dir = get_project_root() / "_bmad-output" / "implementation-artifacts"

    candidates = list(story_dir.glob(f"*{story_id}*"))
    md_files = [c for c in candidates if c.suffix == ".md"]
    if md_files:
        return md_files[0]
    return candidates[0] if candidates else None
