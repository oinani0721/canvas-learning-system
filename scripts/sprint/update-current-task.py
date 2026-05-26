#!/usr/bin/env python3
"""update-current-task.py — Sprint v3 CURRENT_TASK.md 自动同步

Plan: EPIC1-BMAD-DEV-ASSESS-2026-04-17

Stop hook 自动触发. 读 sprint-status.yaml + git log, 重写 CURRENT_TASK.md
frontmatter 关键字段, 保 body 完整. fail-open (hook 出错不阻断 session).

字段更新:
  - next_story_id            (找 sprint_v3 段下一个 ready-for-dev, 依赖全 done)
  - next_story_title         (entry.title)
  - last_commit_hash         (git log -1 --format=%h)
  - sprint_progress          (done/total 计数)
  - last_updated             (UTC ISO 8601)
"""
import os
import re
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timezone

try:
    import yaml
except ImportError:
    print("[update-current-task] PyYAML missing, skip (fail-open)", file=sys.stderr)
    sys.exit(0)


def _worktree_dir() -> Path:
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        return Path(env)
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / ".claude" / "settings.json").exists():
            return parent
    return Path.cwd()


WORKTREE = _worktree_dir()
SPRINT_STATUS = WORKTREE / "_bmad-output/implementation-artifacts/sprint-status.yaml"
CURRENT_TASK = WORKTREE / "_decisions/CURRENT_TASK.md"


def load_sprint_v3() -> dict:
    if not SPRINT_STATUS.exists():
        return {}
    try:
        with SPRINT_STATUS.open() as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print(f"[update-current-task] yaml load error: {e}", file=sys.stderr)
        return {}
    return data.get("development_status", {}).get("sprint_v3_obsidian_hybrid", {}) or {}


def find_next_ready_story(sprint_v3: dict):
    """找下一个 ready-for-dev story (按 day 升序, estimate 升序). 依赖全 done 才算可执行."""
    candidates = []
    for story_id, entry in sprint_v3.items():
        if not isinstance(entry, dict):
            continue
        if entry.get("status") != "ready-for-dev":
            continue
        deps = entry.get("depends_on", []) or []
        all_done = all(
            isinstance(sprint_v3.get(d), dict) and sprint_v3[d].get("status") == "done"
            for d in deps
        )
        if not deps or all_done:
            candidates.append((story_id, entry))
    if not candidates:
        return None, None
    candidates.sort(key=lambda x: (x[1].get("day", 99), x[1].get("estimate_hours", 99)))
    return candidates[0]


def get_git_latest_commit() -> tuple[str, str]:
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%h %s"],
            cwd=str(WORKTREE),
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        line = result.stdout.strip()
        if " " in line:
            sha, msg = line.split(" ", 1)
            return sha, msg
        return line, ""
    except Exception as e:
        return "", f"git error: {e}"


def count_progress(sprint_v3: dict) -> tuple[int, int]:
    done = 0
    total = 0
    skip_keys = {"sprint_label", "total_estimate_hours", "total_stories",
                 "active_plan", "plan_doc", "deferred"}
    for story_id, entry in sprint_v3.items():
        if story_id in skip_keys:
            continue
        if not isinstance(entry, dict) or "status" not in entry:
            continue
        total += 1
        if entry.get("status") == "done":
            done += 1
    return done, total


def _replace_field(text: str, field: str, value: str) -> str:
    """Replace `field: "..."` (with optional trailing comment) line in frontmatter."""
    pattern = rf'^({re.escape(field)}: )"[^"]*"(.*)$'
    replacement = rf'\1"{value}"\2'
    new, count = re.subn(pattern, replacement, text, flags=re.MULTILINE)
    if count == 0:
        return text
    return new


def update_current_task() -> int:
    sprint_v3 = load_sprint_v3()
    if not sprint_v3:
        print("[update-current-task] sprint_v3_obsidian_hybrid not found, skip")
        return 0

    next_id, next_entry = find_next_ready_story(sprint_v3)
    git_sha, git_msg = get_git_latest_commit()
    done_count, total_count = count_progress(sprint_v3)
    progress_pct = round(done_count / total_count * 100, 1) if total_count else 0.0

    if not CURRENT_TASK.exists():
        print(f"[update-current-task] {CURRENT_TASK} not found, skip")
        return 0

    content = CURRENT_TASK.read_text()
    m = re.match(r"^(---\n.*?\n---\n)(.*)", content, re.DOTALL)
    if not m:
        print("[update-current-task] frontmatter not found, skip")
        return 0

    frontmatter = m.group(1)
    body = m.group(2)

    if next_id and isinstance(next_entry, dict):
        frontmatter = _replace_field(frontmatter, "next_story_id", next_id)
        title = (next_entry.get("title", "") or "").replace('"', "'")[:120]
        frontmatter = _replace_field(frontmatter, "next_story_title", title)

    frontmatter = _replace_field(
        frontmatter,
        "sprint_progress",
        f"{done_count}/{total_count} done ({progress_pct}%) — auto-synced",
    )

    if git_sha:
        # last_commit_hash 行可能含注释, 单独 handle
        new_line = f'last_commit_hash: "{git_sha}"  # auto-synced; msg: {git_msg[:60].replace(chr(10), " ")}'
        frontmatter = re.sub(
            r"^last_commit_hash:.*$",
            new_line,
            frontmatter,
            count=1,
            flags=re.MULTILINE,
        )

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    frontmatter = _replace_field(frontmatter, "last_updated", now)

    CURRENT_TASK.write_text(frontmatter + body)
    print(
        f"[update-current-task] ✓ next={next_id} progress={done_count}/{total_count} "
        f"commit={git_sha[:7] if git_sha else 'na'}"
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(update_current_task())
    except Exception as e:
        print(f"[update-current-task] ERROR (fail-open): {e}", file=sys.stderr)
        sys.exit(0)
