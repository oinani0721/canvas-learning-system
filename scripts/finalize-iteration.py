#!/usr/bin/env python3
"""
Finalize Planning Phase Iteration
完成一次Planning迭代：创建snapshot、验证、更新日志、创建Git tag
"""

import sys
from pathlib import Path
from datetime import datetime

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
            if not confirm_action("Continue anyway?"):
                return 1
            validation_passed = False

    # 更新iteration log
    print_status("Updating iteration log...", "progress")
    update_iteration_log(iteration_num, snapshot, validation_passed)

    # 创建post-checklist
    print_status("Creating post-correct-course checklist...", "progress")
    checklist_path = create_post_checklist(iteration_num)

    # 创建Git tag（如果需要）
    if not args.no_tag:
        tag_name = f"planning-v{iteration_num}"
        tag_message = f"Planning Phase Iteration {iteration_num}"

        if confirm_action(f"Create Git tag '{tag_name}'?"):
            create_git_tag(tag_name, tag_message)

    # 打印完成信息
    print("\n" + "="*60)
    print("✅ Iteration Finalized Successfully!")
    print("="*60)
    print(f"\n**Iteration**: {iteration_num}")
    print(f"**Snapshot**: iteration-{iteration_num:03d}.json")
    print(f"**Git Commit**: {snapshot['git_commit'][:8]}...")
    print(f"**Validation**: {"✅ Passed" if validation_passed else "⚠️ Warnings"}")

    print(f"\n**Next Steps**:")
    print(f"1. Review post-checklist: {checklist_path}")
    print(f"2. Commit all changes:")
    print(f"   git add .")
    print(f"   git commit -m \"Planning Iteration {iteration_num} Complete\"")
    print(f"3. Push to remote (if ready):")
    print(f"   git push origin main --tags")
    print("="*60)

    return 0

if __name__ == "__main__":
    sys.exit(main())
