#!/usr/bin/env python3
"""
Rollback Planning Phase Iteration
恢复Planning文件到之前的迭代状态
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

sys.path.insert(0, str(Path(__file__).parent / "lib"))

from planning_utils import (
    get_project_root,
    get_planning_iterations_dir,
    load_snapshot,
    is_git_clean,
    get_git_sha,
    print_status,
    confirm_action,
)


def get_current_iteration() -> int:
    """获取当前迭代号"""
    iterations_dir = get_planning_iterations_dir()

    if not iterations_dir.exists():
        return 0

    iterations = list(iterations_dir.glob("iteration-*.json"))
    if not iterations:
        return 0

    # 提取最大迭代号
    max_iter = 0
    for f in iterations:
        try:
            num = int(f.stem.split("-")[1])
            max_iter = max(max_iter, num)
        except (IndexError, ValueError):
            continue

    return max_iter


def get_iteration_snapshot(iteration_num: int) -> Optional[Dict]:
    """获取指定迭代的snapshot"""
    iterations_dir = get_planning_iterations_dir()
    snapshot_path = iterations_dir / f"iteration-{iteration_num:03d}.json"

    if not snapshot_path.exists():
        return None

    return load_snapshot(snapshot_path)


def run_git_command(cmd: list, check: bool = True) -> subprocess.CompletedProcess:
    """执行Git命令"""
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=get_project_root())

    if check and result.returncode != 0:
        raise RuntimeError(f"Git command failed: {' '.join(cmd)}\n{result.stderr}")

    return result


def stash_changes(message: str) -> bool:
    """Stash当前更改"""
    try:
        result = run_git_command(["git", "stash", "push", "-m", message])
        return "Saved working directory" in result.stdout or result.returncode == 0
    except Exception as e:
        print_status(f"Stash failed: {e}", "warning")
        return False


def checkout_tag(tag_name: str) -> bool:
    """Checkout到指定tag"""
    try:
        run_git_command(["git", "checkout", tag_name])
        return True
    except Exception as e:
        print_status(f"Checkout failed: {e}", "error")
        return False


def create_recovery_branch(iteration_num: int) -> str:
    """创建恢复分支"""
    branch_name = f"planning-recovery-from-{iteration_num}"
    try:
        run_git_command(["git", "checkout", "-b", branch_name])
        return branch_name
    except Exception as e:
        # 分支可能已存在
        print_status(f"Could not create branch {branch_name}: {e}", "warning")
        return ""


def rollback_to_iteration(target_iter: int, force: bool = False, no_stash: bool = False) -> bool:
    """
    回滚到指定迭代

    Args:
        target_iter: 目标迭代号
        force: 跳过确认
        no_stash: 不stash当前更改

    Returns:
        是否成功
    """
    root = get_project_root()
    current_iter = get_current_iteration()

    # 验证目标迭代存在
    snapshot = get_iteration_snapshot(target_iter)
    if not snapshot:
        print_status(f"Iteration {target_iter} not found", "error")
        return False

    # 检查Git状态
    if not is_git_clean():
        if no_stash:
            if not force:
                print_status("Uncommitted changes will be lost! Use --force to confirm", "error")
                return False
        else:
            # Stash更改
            print_status("Stashing current changes...", "progress")
            stash_msg = f"Pre-rollback stash from iteration {current_iter}"
            if stash_changes(stash_msg):
                print_status(f"Changes stashed: {stash_msg}", "success")

    # 确认回滚
    if not force:
        print("\n" + "=" * 60)
        print("⚠️  Rollback Warning")
        print("=" * 60)
        print(f"\nCurrent iteration: {current_iter}")
        print(f"Target iteration: {target_iter}")
        print(f"\nThis will:")
        print(f"  - Restore PRD files to iteration {target_iter} state")
        print(f"  - Restore Architecture files to iteration {target_iter} state")
        print(f"  - Restore Specs to iteration {target_iter} state")
        print(f"  - Discard all changes since iteration {target_iter}")

        if not confirm_action("\nProceed with rollback?"):
            print_status("Rollback cancelled", "info")
            return False

    # 执行回滚
    tag_name = f"planning-v{target_iter}"

    print_status(f"Checking out tag {tag_name}...", "progress")

    # 检查tag是否存在
    result = run_git_command(["git", "tag", "-l", tag_name], check=False)
    if tag_name not in result.stdout:
        print_status(f"Tag {tag_name} not found", "error")
        print_status("Available tags:", "info")
        result = run_git_command(["git", "tag", "-l", "planning-v*"], check=False)
        print(result.stdout)
        return False

    # Checkout tag
    if not checkout_tag(tag_name):
        return False

    # 创建恢复分支
    branch_name = create_recovery_branch(target_iter)

    return True


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Rollback Planning files to a previous iteration state")
    parser.add_argument("--target", type=int, required=True, help="Target iteration number to rollback to")
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompt")
    parser.add_argument("--no-stash", action="store_true", help="Discard current changes without stashing")

    args = parser.parse_args()

    print("=" * 60)
    print("⏪ Planning Iteration Rollback")
    print("=" * 60)

    current_iter = get_current_iteration()
    print_status(f"Current iteration: {current_iter}", "info")
    print_status(f"Target iteration: {args.target}", "info")

    if args.target >= current_iter:
        print_status(f"Target iteration must be less than current ({current_iter})", "error")
        return 1

    success = rollback_to_iteration(args.target, force=args.force, no_stash=args.no_stash)

    if success:
        print("\n" + "=" * 60)
        print("✅ Rollback Complete")
        print("=" * 60)
        print(f"   └─ Restored to: Iteration {args.target}")
        print(f"   └─ Branch: planning-recovery-from-{args.target}")
        print(f"\n📋 You can now:")
        print(f"   - Start new iteration: *init")
        print(f"   - View restored state: *status")
        print(f"   - Recover stash: git stash pop")
        return 0
    else:
        print_status("Rollback failed", "error")
        return 1


if __name__ == "__main__":
    sys.exit(main())
