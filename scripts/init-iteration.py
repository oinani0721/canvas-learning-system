#!/usr/bin/env python3
"""
Initialize Planning Phase Iteration
在开始新的correct course迭代前的准备工作
"""

import sys
import io
import shutil
from pathlib import Path
from datetime import datetime

# Fix Windows GBK encoding issue
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent / "lib"))

from planning_utils import (
    get_project_root,
    get_next_iteration_number,
    get_planning_iterations_dir,
    is_git_clean,
    get_git_sha,
    scan_planning_files,
    print_status,
    confirm_action,
    write_file,
    save_snapshot,  # Bug fix: 添加 save_snapshot 导入
)


def backup_openapi_specs():
    """备份当前OpenAPI specs到versions/目录"""
    root = get_project_root()
    api_dir = root / "specs" / "api"
    versions_dir = api_dir / "versions"

    if not api_dir.exists():
        print_status("No API specs directory found", "warning")
        return

    # 获取所有OpenAPI文件（排除versions目录）
    spec_files = []
    for ext in ["*.yml", "*.yaml"]:
        spec_files.extend(api_dir.glob(ext))

    spec_files = [f for f in spec_files if "versions" not in str(f)]

    if not spec_files:
        print_status("No OpenAPI specs found to backup", "warning")
        return

    print_status(f"Backing up {len(spec_files)} OpenAPI spec(s)...", "progress")

    for spec_file in spec_files:
        # 读取版本号（如果有）
        try:
            import yaml

            with open(spec_file, "r", encoding="utf-8") as f:
                spec = yaml.safe_load(f)
                version = spec.get("info", {}).get("version", "1.0.0")
        except Exception:
            version = "1.0.0"

        # 创建备份
        backup_name = f"{spec_file.stem}.v{version}{spec_file.suffix}"
        backup_path = versions_dir / backup_name

        if not backup_path.exists():
            shutil.copy2(spec_file, backup_path)
            print_status(f"  Backed up: {backup_name}", "success")
        else:
            print_status(f"  Already exists: {backup_name}", "info")


def create_pre_checklist(iteration_num: int):
    """创建pre-correct-course checklist实例"""
    checklist_path = get_project_root() / f"pre-correct-course-iteration-{iteration_num:03d}.md"

    # 读取模板
    template_path = get_project_root() / ".bmad-core" / "checklists" / "pre-correct-course.md"
    template = Path(template_path).read_text(encoding="utf-8")

    # 填充当前信息
    content = template.replace("v_____", "TODO: Fill in current version")
    content += f"\n\n**Generated for Iteration {iteration_num}**\n"
    content += f"**Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

    write_file(checklist_path, content)
    print_status(f"Pre-checklist created: {checklist_path}", "success")

    return checklist_path


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Initialize a new Planning Phase iteration")
    parser.add_argument("--iteration", type=int, help="Iteration number (default: auto-increment)")
    parser.add_argument("--force", action="store_true", help="Skip Git clean check")

    args = parser.parse_args()

    print("=" * 60)
    print("🚀 Initialize Planning Phase Iteration")
    print("=" * 60)

    # 检查Git状态
    if not is_git_clean() and not args.force:
        print_status("Git working directory is not clean!", "error")
        print_status("Please commit or stash changes before starting a new iteration", "info")
        print_status("Or use --force to skip this check", "info")
        return 1

    # 获取迭代编号
    if args.iteration:
        iteration_num = args.iteration
    else:
        iteration_num = get_next_iteration_number()
    print_status(f"Iteration number: {iteration_num}", "info")

    # 创建snapshot
    # Bug fix: 使用当前 iteration_num 创建快照，并保存到文件
    print_status("Creating current state snapshot...", "progress")
    from snapshot_planning import create_snapshot

    snapshot = create_snapshot(iteration_num)

    # Bug fix: 调用 save_snapshot 保存到文件
    snapshot_path = save_snapshot(snapshot, iteration_num)
    print_status(f"Snapshot saved: {snapshot_path}", "success")

    # 备份OpenAPI specs
    print_status("Backing up OpenAPI specs...", "progress")
    backup_openapi_specs()

    # 创建pre-checklist
    print_status("Creating pre-correct-course checklist...", "progress")
    checklist_path = create_pre_checklist(iteration_num)

    # 打印下一步指引
    print("\n" + "=" * 60)
    print("✅ Iteration Initialized Successfully!")
    print("=" * 60)
    print(f"\n   └─ Iteration: {iteration_num}")
    print(f"   └─ Git Commit: {get_git_sha()[:8]}")
    print(f"   └─ Snapshot: {snapshot_path}")  # Bug fix: 使用实际保存路径
    print(f"   └─ Branch: planning-iteration-{iteration_num}")
    print(f"\n📋 Ready for Planning changes")
    print(f"\n**Next Steps**:")
    print(f"1. Review the checklist: {checklist_path}")
    print(f"2. Run: /pm → *correct-course")
    print(f"3. Run: /planning → *validate")
    print(f"4. Run: /planning → *finalize")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
