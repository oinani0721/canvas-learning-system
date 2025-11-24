#!/usr/bin/env python3
"""
Finalize Planning Phase Iteration
完成一次Planning迭代：创建snapshot、验证、更新日志、创建Git tag
"""

import sys
import io
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding for emoji support
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent / "lib"))

from planning_utils import (
    get_project_root,
    get_next_iteration_number,
    get_planning_iterations_dir,
    get_git_sha,
    create_git_tag,
    print_status,
    confirm_action,
    read_file,
    write_file
)
import subprocess


def git_commit_changes(iteration_num: int, goal: str = None) -> bool:
    """执行git add和commit，触发pre-commit hooks"""
    try:
        # Stage所有Planning相关文件
        print_status("Staging changes...", "progress")

        # Stage specific directories to avoid committing unrelated files
        paths_to_stage = [
            "docs/prd/",
            "docs/architecture/",
            "docs/epics/",
            "specs/",
            ".bmad-core/planning-iterations/",
            "CHANGELOG.md"
        ]

        for path in paths_to_stage:
            full_path = get_project_root() / path
            if full_path.exists():
                subprocess.run(
                    ["git", "add", str(full_path)],
                    cwd=get_project_root(),
                    capture_output=True
                )

        # Also stage iteration snapshot
        subprocess.run(
            ["git", "add", f".bmad-core/planning-iterations/iteration-{iteration_num:03d}.json"],
            cwd=get_project_root(),
            capture_output=True
        )

        # Check if there are staged changes
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=get_project_root(),
            capture_output=True
        )

        if result.returncode == 0:
            print_status("No changes to commit", "warning")
            return True

        # Create commit message
        commit_msg = f"Planning: Iteration {iteration_num}"
        if goal:
            commit_msg += f" - {goal}"

        commit_msg += "\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>"

        # Execute commit (this triggers pre-commit hooks)
        print_status("Committing changes (pre-commit hooks will run)...", "progress")
        result = subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=get_project_root(),
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            # Check if pre-commit hooks failed
            if "pre-commit" in result.stderr.lower() or "hook" in result.stderr.lower():
                print_status("Pre-commit hooks failed! Fix issues and retry.", "error")
                print(result.stderr)
            else:
                print_status(f"Commit failed: {result.stderr}", "error")
            return False

        print_status("Changes committed successfully!", "success")
        return True

    except Exception as e:
        print_status(f"Git commit error: {e}", "error")
        return False

def update_iteration_log(iteration_num: int, snapshot: dict, validation_passed: bool):
    """更新iteration-log.md"""
    log_path = get_planning_iterations_dir() / "iteration-log.md"

    # 读取现有日志
    if log_path.exists():
        log_content = read_file(log_path)
    else:
        log_content = "# Planning Phase Iteration Log\n\n"

    # 创建新条目
    entry = f"""
### Iteration {iteration_num:03d} - {datetime.now().strftime('%Y-%m-%d')}

**Git Commit**: `{snapshot['git_commit']}`
**Timestamp**: {snapshot['timestamp']}
**Validation**: {"✅ Passed" if validation_passed else "⚠️ Warnings"}

**Files Modified**:
- PRD: {snapshot['statistics']['prd_count']} file(s)
- Architecture: {snapshot['statistics']['architecture_count']} file(s)
- Epics: {snapshot['statistics']['epic_count']} file(s)
- API Specs: {snapshot['statistics']['api_spec_count']} file(s)

**Total Files**: {snapshot['statistics']['total_files']}

---

"""

    # 在"## Iteration History"后面插入
    if "## Iteration History" in log_content:
        parts = log_content.split("## Iteration History", 1)
        log_content = parts[0] + "## Iteration History\n\n" + entry + parts[1].split("\n\n", 2)[-1]
    else:
        log_content += "\n## Iteration History\n\n" + entry

    write_file(log_path, log_content)
    print_status(f"Updated iteration log: {log_path}", "success")

def create_post_checklist(iteration_num: int):
    """创建post-correct-course checklist实例"""
    checklist_path = get_project_root() / f"post-correct-course-iteration-{iteration_num:03d}.md"

    # 读取模板
    template_path = get_project_root() / ".bmad-core" / "checklists" / "post-correct-course.md"
    template = read_file(template_path)

    # 填充当前信息
    content = template + f"\n\n**Generated for Iteration {iteration_num}**\n"
    content += f"**Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

    write_file(checklist_path, content)
    print_status(f"Post-checklist created: {checklist_path}", "success")

    return checklist_path

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Finalize a Planning Phase iteration"
    )
    parser.add_argument(
        '--breaking',
        action='store_true',
        help='Accept breaking changes (use with caution)'
    )
    parser.add_argument(
        '--skip-validation',
        action='store_true',
        help='Skip validation step'
    )
    parser.add_argument(
        '--no-tag',
        action='store_true',
        help='Do not create Git tag'
    )
    parser.add_argument(
        '--no-commit',
        action='store_true',
        help='Do not auto-commit changes (manual commit required)'
    )
    parser.add_argument(
        '--goal',
        type=str,
        help='Iteration goal for commit message'
    )
    parser.add_argument(
        '-y', '--yes',
        action='store_true',
        help='Auto-confirm all prompts (non-interactive mode)'
    )

    args = parser.parse_args()

    print("="*60)
    print("🏁 Finalize Planning Phase Iteration")
    print("="*60)

    # 获取当前迭代编号
    iteration_num = get_next_iteration_number() - 1

    if iteration_num < 1:
        print_status("No iterations found. Run init-iteration.py first.", "error")
        return 1

    print_status(f"Finalizing Iteration {iteration_num}...", "progress")

    # 创建最终snapshot
    print_status("Creating final snapshot...", "progress")
    from snapshot_planning import create_snapshot
    snapshot = create_snapshot(iteration_num)

    # 运行验证（如果没有跳过）
    validation_passed = True
    if not args.skip_validation and iteration_num > 1:
        print_status(f"Validating against Iteration {iteration_num - 1}...", "progress")

        try:
            from validate_iteration import validate_iterations, load_validation_rules

            rules = load_validation_rules()
            result, prev_snapshot, curr_snapshot = validate_iterations(
                iteration_num - 1,
                iteration_num,
                rules
            )

            if result.has_breaking_changes() and not args.breaking:
                print_status("Breaking changes detected!", "error")
                print_status("Review validation report and fix issues, or use --breaking to accept", "info")
                return 1
            elif result.has_warnings():
                print_status("Warnings detected. Review recommended.", "warning")
                validation_passed = False
            else:
                print_status("Validation passed!", "success")

        except Exception as e:
            print_status(f"Validation error: {e}", "error")
            if not args.yes and not confirm_action("Continue anyway?"):
                return 1
            validation_passed = False

    # 更新iteration log
    print_status("Updating iteration log...", "progress")
    update_iteration_log(iteration_num, snapshot, validation_passed)

    # 创建post-checklist
    print_status("Creating post-correct-course checklist...", "progress")
    checklist_path = create_post_checklist(iteration_num)

    # Git commit（如果需要）
    commit_success = True
    if not args.no_commit:
        if args.yes or confirm_action("Commit all Planning changes?"):
            commit_success = git_commit_changes(iteration_num, args.goal)
            if not commit_success:
                print_status("Commit failed. Fix issues and run: git add . && git commit", "error")
                return 1
    else:
        print_status("Skipping auto-commit (--no-commit specified)", "info")

    # 创建Git tag（如果需要）
    if not args.no_tag and commit_success:
        tag_name = f"planning-v{iteration_num}"
        tag_message = f"Planning Phase Iteration {iteration_num}"
        if args.goal:
            tag_message += f": {args.goal}"

        if args.yes or confirm_action(f"Create Git tag '{tag_name}'?"):
            create_git_tag(tag_name, tag_message)

    # 打印完成信息
    print("\n" + "="*60)
    print("🎉 Iteration Finalized Successfully!")
    print("="*60)
    print(f"\n**Iteration**: {iteration_num}")
    print(f"**Snapshot**: iteration-{iteration_num:03d}.json")
    print(f"**Git Commit**: {snapshot['git_commit'][:8]}...")
    print(f"**Validation**: {"✅ Passed" if validation_passed else "⚠️ Warnings"}")
    print(f"**Auto-Committed**: {"✅ Yes" if (not args.no_commit and commit_success) else "❌ No"}")

    print(f"\n**Next Steps**:")
    print(f"1. Review post-checklist: {checklist_path}")
    if args.no_commit:
        print(f"2. Commit changes manually:")
        print(f"   git add .")
        print(f"   git commit -m \"Planning Iteration {iteration_num} Complete\"")
        print(f"3. Push to remote (if ready):")
        print(f"   git push origin main --tags")
    else:
        print(f"2. Push to remote (if ready):")
        print(f"   git push origin main --tags")
    print("="*60)

    return 0

if __name__ == "__main__":
    sys.exit(main())
