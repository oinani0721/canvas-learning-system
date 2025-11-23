#!/usr/bin/env python3
"""
Planning Phase Snapshot Tool
捕获当前Planning Phase状态的完整快照，用于迭代一致性验证
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# 添加lib目录到path
sys.path.insert(0, str(Path(__file__).parent / "lib"))

from planning_utils import (
    init_utf8_encoding,
    get_project_root,
    get_next_iteration_number,
    save_snapshot,
    read_file,
    compute_file_hash,
    extract_frontmatter,
    get_openapi_version,
    get_git_sha,
    scan_planning_files,
    print_status
)

# ========================================
# Snapshot文件信息提取
# ========================================

def extract_file_info(file_path: Path) -> Dict:
    """
    提取单个文件的详细信息

    Returns:
        {
            "path": str,
            "hash": str,
            "size": int,
            "last_modified": str,
            "version": str (if exists),
            "metadata": dict (if exists)
        }
    """
    if not file_path.exists():
        return None

    info = {
        "path": str(file_path.relative_to(get_project_root())),
        "hash": compute_file_hash(file_path),
        "size": file_path.stat().st_size,
        "last_modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
    }

    # 尝试提取frontmatter信息
    if file_path.suffix == '.md':
        try:
            content = read_file(file_path)
            frontmatter, _ = extract_frontmatter(content)

            if frontmatter:
                info["version"] = frontmatter.get("version", "unknown")
                info["metadata"] = {
                    "document_type": frontmatter.get("document_type"),
                    "status": frontmatter.get("status"),
                    "iteration": frontmatter.get("iteration"),
                    "compatible_with": frontmatter.get("compatible_with"),
                    "changes_from_previous": frontmatter.get("changes_from_previous")
                }
            else:
                info["version"] = "no_frontmatter"
                info["metadata"] = {}
        except Exception as e:
            print_status(f"Warning: Failed to extract frontmatter from {file_path.name}: {e}", "warning")
            info["version"] = "error"
            info["metadata"] = {}

    # 如果是OpenAPI spec文件
    elif file_path.suffix in ['.yml', '.yaml'] and 'api' in str(file_path):
        version = get_openapi_version(file_path)
        info["version"] = version or "unknown"
        info["metadata"] = {"type": "openapi"}

    return info

# ========================================
# 主Snapshot生成逻辑
# ========================================

def create_snapshot(iteration_num: int = None) -> Dict:
    """
    创建Planning Phase的完整snapshot

    Args:
        iteration_num: 迭代编号，如果为None则自动生成

    Returns:
        Snapshot字典
    """
    print_status("Starting snapshot creation...", "progress")

    if iteration_num is None:
        iteration_num = get_next_iteration_number()

    # 扫描所有Planning文件
    files_by_category = scan_planning_files()

    snapshot = {
        "iteration": iteration_num,
        "timestamp": datetime.now().isoformat(),
        "git_commit": get_git_sha(),
        "files": {}
    }

    # 处理PRD文件
    print_status("Scanning PRD files...", "progress")
    snapshot["files"]["prd"] = []
    for file in files_by_category['prd']:
        file_info = extract_file_info(file)
        if file_info:
            snapshot["files"]["prd"].append(file_info)

    print_status(f"  Found {len(snapshot['files']['prd'])} PRD file(s)", "info")

    # 处理Architecture文件
    print_status("Scanning Architecture files...", "progress")
    snapshot["files"]["architecture"] = []
    for file in files_by_category['architecture']:
        file_info = extract_file_info(file)
        if file_info:
            snapshot["files"]["architecture"].append(file_info)

    print_status(f"  Found {len(snapshot['files']['architecture'])} Architecture file(s)", "info")

    # 处理Epic文件
    print_status("Scanning Epic files...", "progress")
    snapshot["files"]["epics"] = []
    for file in files_by_category['epics']:
        file_info = extract_file_info(file)
        if file_info:
            snapshot["files"]["epics"].append(file_info)

    print_status(f"  Found {len(snapshot['files']['epics'])} Epic file(s)", "info")

    # 处理API Specs
    print_status("Scanning API Specification files...", "progress")
    snapshot["files"]["api_specs"] = []
    for file in files_by_category['api_specs']:
        # 排除versions/目录中的文件
        if 'versions' not in str(file):
            file_info = extract_file_info(file)
            if file_info:
                snapshot["files"]["api_specs"].append(file_info)

    print_status(f"  Found {len(snapshot['files']['api_specs'])} API Spec file(s)", "info")

    # 处理Data Schemas
    print_status("Scanning Data Schema files...", "progress")
    snapshot["files"]["data_schemas"] = []
    for file in files_by_category['data_schemas']:
        file_info = extract_file_info(file)
        if file_info:
            snapshot["files"]["data_schemas"].append(file_info)

    print_status(f"  Found {len(snapshot['files']['data_schemas'])} Data Schema file(s)", "info")

    # 处理Behavior Specs
    print_status("Scanning Behavior Specification files...", "progress")
    snapshot["files"]["behavior_specs"] = []
    for file in files_by_category['behavior_specs']:
        file_info = extract_file_info(file)
        if file_info:
            snapshot["files"]["behavior_specs"].append(file_info)

    print_status(f"  Found {len(snapshot['files']['behavior_specs'])} Behavior Spec file(s)", "info")

    # 添加统计信息
    snapshot["statistics"] = {
        "total_files": sum(len(files) for files in snapshot["files"].values()),
        "prd_count": len(snapshot["files"]["prd"]),
        "architecture_count": len(snapshot["files"]["architecture"]),
        "epic_count": len(snapshot["files"]["epics"]),
        "api_spec_count": len(snapshot["files"]["api_specs"]),
        "data_schema_count": len(snapshot["files"]["data_schemas"]),
        "behavior_spec_count": len(snapshot["files"]["behavior_specs"])
    }

    return snapshot

# ========================================
# CLI接口
# ========================================

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Create a snapshot of the Planning Phase state"
    )
    parser.add_argument(
        '--iteration',
        type=int,
        help='Iteration number (default: auto-increment)'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output file path (default: .bmad-core/planning-iterations/snapshots/iteration-NNN.json)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print detailed information'
    )

    args = parser.parse_args()

    # Initialize UTF-8 encoding for Windows
    init_utf8_encoding()

    # 创建snapshot
    snapshot = create_snapshot(iteration_num=args.iteration)

    # 保存snapshot
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(snapshot, f, indent=2, ensure_ascii=False)
        print_status(f"Snapshot saved to: {output_path}", "success")
    else:
        save_snapshot(snapshot, snapshot["iteration"])

    # 打印摘要
    print("\n" + "="*60)
    print("📸 Snapshot Summary")
    print("="*60)
    print(f"Iteration Number: {snapshot['iteration']}")
    print(f"Timestamp: {snapshot['timestamp']}")
    print(f"Git Commit: {snapshot['git_commit'][:8]}...")
    print(f"\nFiles Captured:")
    print(f"  - PRD: {snapshot['statistics']['prd_count']}")
    print(f"  - Architecture: {snapshot['statistics']['architecture_count']}")
    print(f"  - Epics: {snapshot['statistics']['epic_count']}")
    print(f"  - API Specs: {snapshot['statistics']['api_spec_count']}")
    print(f"  - Data Schemas: {snapshot['statistics']['data_schema_count']}")
    print(f"  - Behavior Specs: {snapshot['statistics']['behavior_spec_count']}")
    print(f"\nTotal Files: {snapshot['statistics']['total_files']}")
    print("="*60)

    # 详细输出（如果指定了--verbose）
    if args.verbose:
        print("\n📄 Detailed File List:")
        print("-"*60)

        for category, files in snapshot["files"].items():
            if files:
                print(f"\n{category.upper()}:")
                for file_info in files:
                    print(f"  • {file_info['path']}")
                    print(f"    Version: {file_info.get('version', 'N/A')}")
                    print(f"    Hash: {file_info['hash'][:16]}...")
                    print(f"    Size: {file_info['size']} bytes")

    print("\n✅ Snapshot created successfully!")

    return 0

if __name__ == "__main__":
    sys.exit(main())
