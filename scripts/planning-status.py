#!/usr/bin/env python3
"""
Planning Phase Status
显示当前Planning迭代状态和历史
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent / "lib"))

from planning_utils import (
    get_project_root,
    get_planning_iterations_dir,
    load_snapshot,
    is_git_clean,
    get_git_sha,
    print_status,
    generate_markdown_report
)

def get_all_iterations() -> List[Dict]:
    """获取所有迭代信息"""
    iterations_dir = get_planning_iterations_dir()

    if not iterations_dir.exists():
        return []

    iterations = []
    for snapshot_file in sorted(iterations_dir.glob("iteration-*.json")):
        try:
            snapshot = load_snapshot(snapshot_file)
            num = int(snapshot_file.stem.split('-')[1])
            iterations.append({
                "number": num,
                "timestamp": snapshot.get('timestamp', 'unknown'),
                "git_sha": snapshot.get('git_sha', 'unknown')[:8],
                "goal": snapshot.get('goal', ''),
                "status": "Finalized" if snapshot.get('finalized') else "In Progress"
            })
        except Exception as e:
            print_status(f"Error loading {snapshot_file}: {e}", "warning")

    return sorted(iterations, key=lambda x: x['number'], reverse=True)

def get_current_branch() -> str:
    """获取当前Git分支"""
    try:
        result = subprocess.run(
            ['git', 'branch', '--show-current'],
            capture_output=True,
            text=True,
            cwd=get_project_root()
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"

def get_uncommitted_changes() -> List[str]:
    """获取未提交的更改"""
    try:
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True,
            cwd=get_project_root()
        )

        changes = []
        for line in result.stdout.strip().split('\n'):
            if line:
                # 只显示Planning相关文件
                if any(p in line for p in ['docs/prd', 'docs/architecture', 'specs/', 'CLAUDE.md']):
                    status = line[:2].strip()
                    path = line[3:]
                    changes.append(f"{path} ({status})")

        return changes
    except Exception:
        return []

def get_spec_versions() -> List[Dict]:
    """获取SDD规范版本"""
    root = get_project_root()
    specs = []

    # OpenAPI specs
    api_dir = root / "specs" / "api"
    if api_dir.exists():
        for spec_file in api_dir.glob("*.yml"):
            if 'versions' not in str(spec_file):
                try:
                    import yaml
                    with open(spec_file, 'r', encoding='utf-8') as f:
                        spec = yaml.safe_load(f)
                        version = spec.get('info', {}).get('version', 'unknown')
                        specs.append({
                            "name": spec_file.name,
                            "type": "OpenAPI",
                            "version": version
                        })
                except Exception:
                    specs.append({
                        "name": spec_file.name,
                        "type": "OpenAPI",
                        "version": "parse error"
                    })

    # JSON schemas
    data_dir = root / "specs" / "data"
    if data_dir.exists():
        for schema_file in data_dir.glob("*.json"):
            try:
                with open(schema_file, 'r', encoding='utf-8') as f:
                    schema = json.load(f)
                    version = schema.get('version', schema.get('$id', 'unknown'))
                    if '/' in str(version):
                        version = version.split('/')[-1]
                    specs.append({
                        "name": schema_file.name,
                        "type": "JSON Schema",
                        "version": version
                    })
            except Exception:
                specs.append({
                    "name": schema_file.name,
                    "type": "JSON Schema",
                    "version": "parse error"
                })

    return specs

def generate_status_report() -> str:
    """生成状态报告"""
    iterations = get_all_iterations()
    current_branch = get_current_branch()
    uncommitted = get_uncommitted_changes()
    spec_versions = get_spec_versions()

    sections = []

    # 当前状态
    if iterations:
        latest = iterations[0]
        current_content = f"""
- **Active Iteration**: {latest['number']}
- **Status**: {latest['status']}
- **Branch**: {current_branch}
- **Started**: {latest['timestamp']}
- **Goal**: {latest.get('goal', 'N/A')}
"""
    else:
        current_content = """
- **Active Iteration**: None
- **Status**: No iterations found

Run `*init` to start your first iteration.
"""

    sections.append({
        "title": "Current State",
        "content": current_content
    })

    # 未提交更改
    if uncommitted:
        changes_content = "\n".join([f"- {c}" for c in uncommitted])
    else:
        changes_content = "No uncommitted Planning changes ✅"

    sections.append({
        "title": "Uncommitted Changes",
        "content": changes_content
    })

    # 迭代历史
    if iterations:
        history_content = "| Iteration | Status | Date | Goal |\n"
        history_content += "|-----------|--------|------|------|\n"

        for it in iterations[:10]:  # 显示最近10个
            goal = it.get('goal', '')[:30] + ('...' if len(it.get('goal', '')) > 30 else '')
            date = it['timestamp'][:10] if len(it['timestamp']) >= 10 else it['timestamp']
            history_content += f"| {it['number']} | {it['status']} | {date} | {goal} |\n"

        if len(iterations) > 10:
            history_content += f"\n*...and {len(iterations) - 10} more iterations*"
    else:
        history_content = "No iteration history"

    sections.append({
        "title": "Iteration History",
        "content": history_content
    })

    # SDD规范版本
    if spec_versions:
        specs_content = "| Spec | Type | Version |\n"
        specs_content += "|------|------|------|\n"

        for spec in spec_versions:
            specs_content += f"| {spec['name']} | {spec['type']} | {spec['version']} |\n"
    else:
        specs_content = "No SDD specs found"

    sections.append({
        "title": "SDD Spec Versions",
        "content": specs_content
    })

    # 可用命令
    commands_content = """
- `*validate` - Check current changes for breaking changes
- `*finalize` - Complete this iteration
- `*rollback` - Restore previous state
- `*compare {N}` - Compare to iteration N
"""

    sections.append({
        "title": "Available Commands",
        "content": commands_content
    })

    return generate_markdown_report("Planning Iteration Status", sections)

def generate_json_status() -> Dict:
    """生成JSON格式状态"""
    iterations = get_all_iterations()

    return {
        "current_iteration": iterations[0] if iterations else None,
        "branch": get_current_branch(),
        "uncommitted_changes": get_uncommitted_changes(),
        "iteration_history": iterations,
        "spec_versions": get_spec_versions(),
        "timestamp": datetime.now().isoformat()
    }

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Show current Planning iteration state and history"
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON for scripting'
    )
    parser.add_argument(
        '--history-only',
        action='store_true',
        help='Show only iteration history'
    )

    args = parser.parse_args()

    if args.json:
        status = generate_json_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))
    elif args.history_only:
        iterations = get_all_iterations()
        if iterations:
            print("\n📋 Iteration History\n")
            print("| Iteration | Status | Date | Goal |")
            print("|-----------|--------|------|------|")
            for it in iterations:
                goal = it.get('goal', '')[:40]
                date = it['timestamp'][:10] if len(it['timestamp']) >= 10 else it['timestamp']
                print(f"| {it['number']} | {it['status']} | {date} | {goal} |")
        else:
            print_status("No iterations found. Run *init to start", "warning")
    else:
        print("="*60)
        print("📊 Planning Iteration Status")
        print("="*60)
        print(generate_status_report())

    return 0

if __name__ == "__main__":
    sys.exit(main())
