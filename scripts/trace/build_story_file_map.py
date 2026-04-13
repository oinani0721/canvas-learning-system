#!/usr/bin/env python3
"""
Build Story ↔ File external index.

Scans all Story files for BMAD native '### File List' sections and
aggregates with git log Story: trailers to produce a YAML index at
docs/_meta/indices/story-file-map.yaml.

This is a READ-ONLY external index — it never writes back to Story files.
Used by Dataview dashboards and /bmad-lb for reverse lookups.

Usage:
  python scripts/trace/build_story_file_map.py         # incremental
  python scripts/trace/build_story_file_map.py --all    # full rebuild
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.trace._story_reader import read_file_list
STORY_DIR = PROJECT_ROOT / "_bmad-output" / "implementation-artifacts"
INDEX_DIR = PROJECT_ROOT / "docs" / "_meta" / "indices"
INDEX_FILE = INDEX_DIR / "story-file-map.yaml"


def extract_story_id_from_filename(filename: str) -> str | None:
    match = re.match(r"(\d+\.\d+)", filename)
    return match.group(1) if match else None


def scan_story_files() -> dict[str, list[str]]:
    """Read File List from all Story .md files."""
    mapping: dict[str, list[str]] = {}
    if not STORY_DIR.exists():
        return mapping

    for story_file in sorted(STORY_DIR.glob("*.md")):
        story_id = extract_story_id_from_filename(story_file.name)
        if not story_id:
            continue
        file_list = read_file_list(story_file)
        if file_list:
            mapping[story_id] = file_list
    return mapping


def scan_git_trailers() -> dict[str, set[str]]:
    """Extract Story: trailers from git log and map to changed files."""
    mapping: dict[str, set[str]] = {}
    try:
        log_output = subprocess.check_output(
            [
                "git", "log", "--all", "--format=%H %B",
                "--diff-filter=ACMR", "--name-only",
            ],
            cwd=str(PROJECT_ROOT),
            text=True,
            timeout=10,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return mapping

    current_story_ids: list[str] = []
    current_files: list[str] = []

    for line in log_output.split("\n"):
        trailer_match = re.match(r"^Story:\s*(\d+\.\d+)", line)
        if trailer_match:
            current_story_ids.append(trailer_match.group(1))
        elif line.startswith(("backend/", "frontend/")):
            current_files.append(line.strip())
        elif not line.strip():
            for sid in current_story_ids:
                mapping.setdefault(sid, set()).update(current_files)
            current_story_ids = []
            current_files = []

    return mapping


def build_index() -> dict:
    file_list_map = scan_story_files()
    git_map = scan_git_trailers()

    all_ids = sorted(set(file_list_map.keys()) | set(git_map.keys()))
    index: dict[str, dict] = {}

    for sid in all_ids:
        from_file_list = file_list_map.get(sid, [])
        from_git = sorted(git_map.get(sid, set()))
        all_files = sorted(set(from_file_list) | set(from_git))

        index[sid] = {
            "files": all_files,
            "source_file_list": len(from_file_list),
            "source_git_trailer": len(from_git),
        }

    return index


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="Full rebuild")
    parser.parse_args()

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    index = build_index()

    INDEX_FILE.write_text(
        yaml.dump(
            {"generated": "build_story_file_map.py", "stories": index},
            allow_unicode=True,
            default_flow_style=False,
        ),
        encoding="utf-8",
    )
    print(f"Index written: {len(index)} stories → {INDEX_FILE.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
