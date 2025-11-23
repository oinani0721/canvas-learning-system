#!/usr/bin/env python3
"""
Git Hooks Setup Script
安装和配置Planning Phase迭代管理的Git hooks
"""

import sys
import os
import shutil
import stat
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "lib"))

from planning_utils import (
    get_project_root,
    print_status
)

def make_executable(file_path: Path):
    """使文件可执行（Unix-like系统）"""
    if os.name != 'nt':  # 非Windows系统
        st = os.stat(file_path)
        os.chmod(file_path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

def setup_pre_commit_hook():
    """设置pre-commit hook"""
    root = get_project_root()
    hooks_dir = root / ".git" / "hooks"

    if not hooks_dir.exists():
        print_status("Not a Git repository. Cannot install hooks.", "error")
        return False

    # pre-commit hook路径
    hook_file = hooks_dir / "pre-commit"

    if hook_file.exists():
        # 备份现有hook
        backup_file = hooks_dir / "pre-commit.backup"
        shutil.copy2(hook_file, backup_file)
        print_status(f"Existing hook backed up to: {backup_file.name}", "info")

    # 读取hook模板
    template_file = root / "scripts" / "templates" / "pre-commit.sh"

    if not template_file.exists():
        # 如果模板不存在，直接检查.git/hooks/pre-commit是否已存在
        if hook_file.exists():
            print_status("Pre-commit hook already exists.", "success")
            make_executable(hook_file)
            return True
        else:
            print_status("Hook template not found and no existing hook.", "error")
            return False

    # 复制hook
    shutil.copy2(template_file, hook_file)
    print_status(f"Pre-commit hook installed: {hook_file}", "success")

    # 使其可执行
    make_executable(hook_file)
    print_status("Hook made executable", "success")

    return True

def test_hook():
    """测试hook是否正常工作"""
    root = get_project_root()
    hook_file = root / ".git" / "hooks" / "pre-commit"

    if not hook_file.exists():
        print_status("Hook not found. Cannot test.", "error")
        return False

    print_status("Testing hook...", "progress")

    # 检查Python是否可用
    try:
        import subprocess
        result = subprocess.run(
            ['python3', '--version'],
            capture_output=True,
            text=True,
            check=True
        )
        print_status(f"Python found: {result.stdout.strip()}", "success")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_status("Python3 not found. Hook may not work properly.", "warning")
        return False

    # 检查验证脚本
    validate_script = root / "scripts" / "validate-iteration.py"
    if not validate_script.exists():
        print_status("Validation script not found. Hook will skip validation.", "warning")
        return False

    print_status("Hook setup verified successfully!", "success")
    return True

def main():
    """主函数"""
    # Windows编码处理
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    print("="*60)
    print("🔧 Git Hooks Setup for Planning Phase")
    print("="*60)
    print()

    # 设置pre-commit hook
    print_status("Setting up pre-commit hook...", "progress")
    if setup_pre_commit_hook():
        print_status("Pre-commit hook installed successfully!", "success")
    else:
        print_status("Failed to install pre-commit hook.", "error")
        return 1

    print()

    # 测试hook
    print_status("Testing hook configuration...", "progress")
    if test_hook():
        print_status("All tests passed!", "success")
    else:
        print_status("Some tests failed. Hook may not work as expected.", "warning")

    print()
    print("="*60)
    print("✅ Git Hooks Setup Complete!")
    print("="*60)
    print()
    print("The pre-commit hook will now automatically:")
    print("  1. Detect Planning Phase file changes")
    print("  2. Create temporary snapshot")
    print("  3. Run validation against previous iteration")
    print("  4. Block commit if breaking changes detected")
    print()
    print("To bypass the hook (NOT RECOMMENDED):")
    print("  git commit -n -m \"message\"")
    print()
    print("To accept breaking changes:")
    print("  python scripts/finalize-iteration.py --breaking")
    print("="*60)

    return 0

if __name__ == "__main__":
    sys.exit(main())
