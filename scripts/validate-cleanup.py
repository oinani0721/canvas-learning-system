#!/usr/bin/env python3
"""
Validate Cleanup
检查是否可以安全删除worktree
"""

import sys
import subprocess
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).parent / "lib"))

from planning_utils import (
    get_project_root,
    print_status
)

def get_worktree_path(story_id: str) -> Path:
    """获取worktree路径"""
    root = get_project_root()
    parent = root.parent
    return parent / f"Canvas-develop-{story_id}"

def check_branch_merged(story_id: str) -> bool:
    """检查分支是否已合并到main"""
    branch_name = f"develop-story-{story_id}"
    root = get_project_root()

    try:
        # 获取已合并的分支列表
        result = subprocess.run(
            ['git', 'branch', '--merged', 'main'],
            capture_output=True,
            text=True,
            cwd=root
        )

        merged_branches = [b.strip().lstrip('* ') for b in result.stdout.split('\n')]
        return branch_name in merged_branches
    except Exception:
        return False

def check_no_uncommitted(worktree_path: Path) -> bool:
    """检查无未提交更改"""
    try:
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True,
            cwd=worktree_path
        )
        return len(result.stdout.strip()) == 0
    except Exception:
        return False

def check_no_stashed(worktree_path: Path) -> bool:
    """检查无stash"""
    try:
        result = subprocess.run(
            ['git', 'stash', 'list'],
            capture_output=True,
            text=True,
            cwd=worktree_path
        )
        return len(result.stdout.strip()) == 0
    except Exception:
        return True  # 默认通过

def validate_cleanup(story_id: str) -> Dict:
    """验证是否可以安全删除worktree"""
    worktree_path = get_worktree_path(story_id)

    result = {
        "story_id": story_id,
        "worktree_exists": worktree_path.exists(),
        "checks": {},
        "safe_to_cleanup": False
    }

    if not worktree_path.exists():
        result["error"] = f"Worktree not found: {worktree_path}"
        result["safe_to_cleanup"] = True  # 不存在则无需清理
        return result

    # 执行检查
    result["checks"]["branch_merged"] = check_branch_merged(story_id)
    result["checks"]["no_uncommitted"] = check_no_uncommitted(worktree_path)
    result["checks"]["no_stashed"] = check_no_stashed(worktree_path)

    # 综合判断
    result["safe_to_cleanup"] = (
        result["checks"]["branch_merged"] and
        result["checks"]["no_uncommitted"] and
        result["checks"]["no_stashed"]
    )

    return result

def main():
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Validate worktree is safe to cleanup"
    )
    parser.add_argument(
        '--story',
        type=str,
        required=True,
        help='Story ID to validate'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON'
    )

    args = parser.parse_args()

    print("="*60)
    print("🔍 Cleanup Validation")
    print("="*60)

    result = validate_cleanup(args.story)

    if args.json:
        print(json.dumps(result, indent=2))
        return 0 if result["safe_to_cleanup"] else 1

    # 输出结果
    print(f"\nStory: {args.story}")
    print(f"Worktree: {'✅ Found' if result['worktree_exists'] else '❌ Not found'}")

    if "error" in result and not result["safe_to_cleanup"]:
        print_status(result["error"], "error")
        return 1

    if not result["worktree_exists"]:
        print_status("Worktree already removed", "info")
        return 0

    checks = result["checks"]
    print("\n📋 Checks:")
    print(f"  Branch Merged: {'✅' if checks['branch_merged'] else '❌'}")
    print(f"  No Uncommitted: {'✅' if checks['no_uncommitted'] else '❌'}")
    print(f"  No Stashed: {'✅' if checks['no_stashed'] else '❌'}")

    print("\n" + "="*60)

    if result["safe_to_cleanup"]:
        print("✅ Safe to Cleanup!")
        worktree_path = get_worktree_path(args.story)
        print(f"\nRun: git worktree remove {worktree_path}")
        return 0
    else:
        print("❌ Not Safe to Cleanup")
        if not checks["branch_merged"]:
            print("\n⚠️ Branch not merged! Merge first or use --force to lose changes.")
        if not checks["no_uncommitted"]:
            print("\n⚠️ Uncommitted changes! Commit or stash first.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
