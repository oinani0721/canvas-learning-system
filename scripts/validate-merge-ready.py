#!/usr/bin/env python3
"""
Validate Merge Ready
检查Story worktree是否可以合并
"""

import sys
import subprocess
from pathlib import Path
from typing import Dict, Optional

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

sys.path.insert(0, str(Path(__file__).parent / "lib"))

from planning_utils import (
    get_project_root,
    print_status
)

def get_worktree_path(story_id: str) -> Path:
    """获取worktree路径"""
    root = get_project_root()
    # worktree在项目根目录的同级
    parent = root.parent
    return parent / f"Canvas-develop-{story_id}"

def load_worktree_status(worktree_path: Path) -> Optional[Dict]:
    """加载worktree状态文件"""
    status_file = worktree_path / ".worktree-status.yaml"

    if not status_file.exists():
        return None

    if not HAS_YAML:
        # 简单解析
        content = status_file.read_text(encoding='utf-8')
        status = {}
        for line in content.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                value = value.strip().strip('"').strip("'")
                if value.lower() == 'true':
                    value = True
                elif value.lower() == 'false':
                    value = False
                elif value.lower() == 'null':
                    value = None
                status[key.strip()] = value
        return status

    with open(status_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def check_tests_pass(worktree_path: Path) -> bool:
    """检查测试是否通过"""
    # 检查状态文件
    status = load_worktree_status(worktree_path)
    if status:
        return status.get('tests_passed', False)

    # 或者实际运行测试
    return False

def check_qa_reviewed(worktree_path: Path) -> bool:
    """检查QA是否审查通过"""
    status = load_worktree_status(worktree_path)
    if status:
        return status.get('qa_reviewed', False)
    return False

def check_qa_gate(worktree_path: Path) -> str:
    """获取QA门禁状态"""
    status = load_worktree_status(worktree_path)
    if status:
        return status.get('qa_gate', 'unknown')
    return 'unknown'

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

def validate_merge_ready(story_id: str) -> Dict:
    """验证Story是否可以合并"""
    worktree_path = get_worktree_path(story_id)

    result = {
        "story_id": story_id,
        "worktree_exists": worktree_path.exists(),
        "checks": {},
        "ready_to_merge": False
    }

    if not worktree_path.exists():
        result["error"] = f"Worktree not found: {worktree_path}"
        return result

    # 执行检查
    status = load_worktree_status(worktree_path)

    # 状态检查
    current_status = status.get('status', 'unknown') if status else 'unknown'
    result["checks"]["status_ready"] = current_status == "ready-to-merge"
    result["checks"]["current_status"] = current_status

    # 测试检查
    result["checks"]["tests_passed"] = check_tests_pass(worktree_path)

    # QA检查
    result["checks"]["qa_reviewed"] = check_qa_reviewed(worktree_path)
    result["checks"]["qa_gate"] = check_qa_gate(worktree_path)

    # 未提交更改检查
    result["checks"]["no_uncommitted"] = check_no_uncommitted(worktree_path)

    # 综合判断
    qa_gate = result["checks"]["qa_gate"]
    result["ready_to_merge"] = (
        result["checks"]["status_ready"] and
        result["checks"]["tests_passed"] and
        result["checks"]["qa_reviewed"] and
        qa_gate in ['PASS', 'WAIVED'] and
        result["checks"]["no_uncommitted"]
    )

    return result

def main():
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Validate Story worktree is ready to merge"
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
    print("🔍 Merge Ready Validation")
    print("="*60)

    result = validate_merge_ready(args.story)

    if args.json:
        print(json.dumps(result, indent=2))
        return 0 if result["ready_to_merge"] else 1

    # 输出结果
    print(f"\nStory: {args.story}")
    print(f"Worktree: {'✅ Found' if result['worktree_exists'] else '❌ Not found'}")

    if "error" in result:
        print_status(result["error"], "error")
        return 1

    checks = result["checks"]
    print("\n📋 Checks:")
    print(f"  Status: {checks['current_status']} {'✅' if checks['status_ready'] else '❌'}")
    print(f"  Tests Passed: {'✅' if checks['tests_passed'] else '❌'}")
    print(f"  QA Reviewed: {'✅' if checks['qa_reviewed'] else '❌'}")
    print(f"  QA Gate: {checks['qa_gate']} {'✅' if checks['qa_gate'] in ['PASS', 'WAIVED'] else '❌'}")
    print(f"  No Uncommitted: {'✅' if checks['no_uncommitted'] else '❌'}")

    print("\n" + "="*60)

    if result["ready_to_merge"]:
        print("✅ Ready to Merge!")
        print("\nNext step: Run `*merge {args.story}`")
        return 0
    else:
        print("❌ Not Ready to Merge")
        print("\nFix the failing checks above before merging.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
