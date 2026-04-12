#!/usr/bin/env python3
"""
BMAD-ANNO Feedback Scanner

Scans active Story files and PRD register files for unprocessed
Obsidian Callout annotations ([!BMAD-ANNO]).

Three modes:
  pending-summary  — count only (for SessionStart hook)
  interactive      — list details (for /bmad-sf slash command)
  batch-silent     — dump to docs/_meta/annotations/ (for Stop hook)

Usage:
  python scripts/bmad/scan_feedback.py --mode=pending-summary
  python scripts/bmad/scan_feedback.py --mode=interactive --story=30.23
  python scripts/bmad/scan_feedback.py --mode=batch-silent --sprint-status path/to/sprint-status.yaml
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STORY_DIR = PROJECT_ROOT / "_bmad-output" / "implementation-artifacts"
PRD_REGISTER = PROJECT_ROOT / "_prd-register"
ANNOTATIONS_DIR = PROJECT_ROOT / "docs" / "_meta" / "annotations"
DEFAULT_SPRINT_STATUS = STORY_DIR / "sprint-status.yaml"

ACTIVE_STATUSES = {"ready-for-dev", "in-progress", "review"}

CALLOUT_RE = re.compile(
    r"^>\s*\[!BMAD-ANNO\]\s*(\S+)\s*\n((?:>\s*.*\n)*)",
    re.MULTILINE,
)


def load_story_status_map(sprint_status_path: Path | None) -> dict[str, str]:
    if not sprint_status_path or not sprint_status_path.exists():
        return {}
    data = yaml.safe_load(sprint_status_path.read_text(encoding="utf-8"))
    dev_status = data.get("development_status", {})
    result: dict[str, str] = {}
    for story_key, status in dev_status.items():
        if isinstance(status, str):
            result[str(story_key)] = status
        elif isinstance(status, dict):
            result[str(story_key)] = status.get("status", "unknown")
    return result


def find_story_files(
    sprint_status_path: Path | None = None,
    story_filter: str | None = None,
) -> list[Path]:
    if story_filter:
        pattern = f"*{story_filter}*"
        return sorted(STORY_DIR.glob(pattern))

    active_ids: set[str] = set()
    if sprint_status_path and sprint_status_path.exists():
        status_map = load_story_status_map(sprint_status_path)
        for story_key, status in status_map.items():
            if status in ACTIVE_STATUSES:
                active_ids.add(story_key)

    if active_ids:
        files = []
        for sid in active_ids:
            files.extend(STORY_DIR.glob(f"*{sid}*"))
        return sorted(set(files))

    return sorted(STORY_DIR.glob("*.md"))


def find_prd_register_files() -> list[Path]:
    if not PRD_REGISTER.exists():
        return []
    return sorted(PRD_REGISTER.glob("PRD14-S*.md"))


def extract_feedback_section(text: str) -> str:
    for header in ("## User Feedback & Changes", "## 用户批注区"):
        idx = text.find(header)
        if idx != -1:
            section_start = idx + len(header)
            next_h2 = text.find("\n## ", section_start)
            if next_h2 == -1:
                return text[section_start:]
            return text[section_start:next_h2]
    return ""


def parse_callouts(section: str) -> list[dict]:
    results = []
    for match in CALLOUT_RE.finditer(section):
        anno_id = match.group(1)
        raw_body = match.group(2)
        body_lines = []
        for line in raw_body.split("\n"):
            stripped = re.sub(r"^>\s?", "", line)
            body_lines.append(stripped)
        body_text = "\n".join(body_lines).strip()
        try:
            data = yaml.safe_load(body_text) or {}
        except yaml.YAMLError:
            data = {"_parse_error": True, "_raw": body_text}
        data["id"] = anno_id
        results.append(data)
    return results


def is_processed(anno: dict) -> bool:
    if anno.get("processed"):
        return True
    anno_id = anno['id']
    fname = anno_id if anno_id.startswith("ANNO-") else f"ANNO-{anno_id}"
    anno_file = ANNOTATIONS_DIR / f"{fname}.yaml"
    return anno_file.exists()


def _resolve_story_status(fpath: Path, status_map: dict[str, str]) -> str:
    stem = fpath.stem
    for key in status_map:
        if key in stem or stem.startswith(key):
            return status_map[key]
    return "unknown"


def scan(
    sprint_status_path: Path | None = None,
    story_filter: str | None = None,
) -> list[dict]:
    results = []
    status_map = load_story_status_map(sprint_status_path)

    story_files = find_story_files(sprint_status_path, story_filter)
    prd_files = find_prd_register_files()

    for fpath in story_files + prd_files:
        if not fpath.exists() or not fpath.suffix == ".md":
            continue
        text = fpath.read_text(encoding="utf-8")
        section = extract_feedback_section(text)
        if not section:
            continue
        is_prd = fpath.parent == PRD_REGISTER
        story_status = "n/a" if is_prd else _resolve_story_status(fpath, status_map)
        callouts = parse_callouts(section)
        for c in callouts:
            if not is_processed(c):
                results.append({
                    "source_file": str(fpath.relative_to(PROJECT_ROOT)),
                    "story_status": story_status,
                    **c,
                })
    return results


def mode_pending_summary(results: list[dict]) -> None:
    if not results:
        return
    by_intent = Counter(r.get("intent", "unknown") for r in results)
    parts = [f"{v} {k}" for k, v in sorted(by_intent.items())]
    print(f"你有 {len(results)} 条未处理批注: {' / '.join(parts)}")


def mode_interactive(results: list[dict]) -> None:
    if not results:
        print("没有未处理的批注。")
        return
    by_intent = Counter(r.get("intent", "unknown") for r in results)
    parts = [f"{v} {k}" for k, v in sorted(by_intent.items())]
    print(f"共 {len(results)} 条未处理批注: {' / '.join(parts)}")
    print()
    for i, r in enumerate(results, 1):
        print(f"[{i}] {r.get('id', '?')}")
        print(f"    Source: {r.get('source_file', '?')}")
        status = r.get("story_status", "?")
        print(f"    Status: {status} | Intent: {r.get('intent', '?')} | Action: {r.get('action', '?')}")
        print(f"    Reason: {r.get('reason', '-')}")
        if r.get("target"):
            print(f"    Target: {r['target']}")
        print()


def mode_batch_silent(results: list[dict]) -> None:
    if not results:
        return
    ANNOTATIONS_DIR.mkdir(parents=True, exist_ok=True)
    failed_dir = ANNOTATIONS_DIR / "_failed"

    for r in results:
        anno_id = r.get("id", "unknown")
        fname = anno_id if anno_id.startswith("ANNO-") else f"ANNO-{anno_id}"
        out_file = ANNOTATIONS_DIR / f"{fname}.yaml"
        try:
            payload = {
                **r,
                "scan_timestamp": datetime.now(timezone.utc).isoformat(),
            }
            out_file.write_text(
                yaml.dump(payload, allow_unicode=True, default_flow_style=False),
                encoding="utf-8",
            )
        except Exception as exc:
            failed_dir.mkdir(parents=True, exist_ok=True)
            err_file = failed_dir / f"{fname}.yaml"
            err_file.write_text(
                yaml.dump(
                    {"id": anno_id, "error": str(exc), "_raw": r},
                    allow_unicode=True,
                ),
                encoding="utf-8",
            )
            print(f"[WARN] Failed to write {anno_id}: {exc}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description="BMAD-ANNO Feedback Scanner")
    parser.add_argument(
        "--mode",
        choices=["pending-summary", "interactive", "batch-silent"],
        default="interactive",
    )
    parser.add_argument("--sprint-status", type=Path, default=None)
    parser.add_argument("--story", type=str, default=None)
    args = parser.parse_args()

    sprint_path = args.sprint_status or DEFAULT_SPRINT_STATUS
    results = scan(sprint_path if sprint_path.exists() else None, args.story)

    if args.mode == "pending-summary":
        mode_pending_summary(results)
    elif args.mode == "interactive":
        mode_interactive(results)
    elif args.mode == "batch-silent":
        mode_batch_silent(results)


if __name__ == "__main__":
    main()
