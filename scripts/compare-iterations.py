#!/usr/bin/env python3
"""
Compare Planning Phase Iterations
比较两个迭代版本或当前状态与指定迭代的差异
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

sys.path.insert(0, str(Path(__file__).parent / "lib"))

from planning_utils import (
    get_project_root,
    get_planning_iterations_dir,
    load_snapshot,
    scan_planning_files,
    print_status,
    generate_markdown_report,
)


def get_iteration_snapshot(iteration_num: int) -> Optional[Dict]:
    """获取指定迭代的snapshot"""
    iterations_dir = get_planning_iterations_dir()
    snapshot_path = iterations_dir / f"iteration-{iteration_num:03d}.json"

    if not snapshot_path.exists():
        return None

    return load_snapshot(snapshot_path)


def get_current_state() -> Dict:
    """获取当前Planning文件状态"""
    return scan_planning_files()


def compare_file_sets(files1: List[Dict], files2: List[Dict], file_type: str) -> Dict:
    """比较两组文件"""
    result = {"added": [], "removed": [], "modified": []}

    paths1 = {f["path"]: f for f in files1}
    paths2 = {f["path"]: f for f in files2}

    # 新增文件
    for path in paths2:
        if path not in paths1:
            result["added"].append(paths2[path])

    # 删除文件
    for path in paths1:
        if path not in paths2:
            result["removed"].append(paths1[path])

    # 修改文件
    for path in paths1:
        if path in paths2:
            f1 = paths1[path]
            f2 = paths2[path]

            # 比较hash或version
            if f1.get("hash") != f2.get("hash") or f1.get("version") != f2.get("version"):
                result["modified"].append(
                    {
                        "path": path,
                        "from_version": f1.get("version", "unknown"),
                        "to_version": f2.get("version", "unknown"),
                        "from_hash": f1.get("hash", "")[:8],
                        "to_hash": f2.get("hash", "")[:8],
                    }
                )

    return result


def compare_iterations(from_iter: int, to_iter: Optional[int] = None) -> Dict:
    """
    比较两个迭代

    Args:
        from_iter: 起始迭代号
        to_iter: 目标迭代号，None表示当前状态
    """
    # 加载起始迭代
    from_snapshot = get_iteration_snapshot(from_iter)
    if not from_snapshot:
        raise ValueError(f"Iteration {from_iter} not found")

    # 加载目标状态
    if to_iter is not None:
        to_snapshot = get_iteration_snapshot(to_iter)
        if not to_snapshot:
            raise ValueError(f"Iteration {to_iter} not found")
        to_label = f"Iteration {to_iter}"
    else:
        to_snapshot = get_current_state()
        to_label = "Current State"

    # 比较各类文件
    comparison = {
        "from_iteration": from_iter,
        "to_iteration": to_iter,
        "to_label": to_label,
        "timestamp": datetime.now().isoformat(),
        "changes": {},
    }

    file_types = ["prd", "architecture", "openapi", "schemas"]

    for file_type in file_types:
        from_files = from_snapshot.get("files", {}).get(file_type, [])
        to_files = to_snapshot.get("files", {}).get(file_type, [])

        changes = compare_file_sets(from_files, to_files, file_type)
        if changes["added"] or changes["removed"] or changes["modified"]:
            comparison["changes"][file_type] = changes

    return comparison


def generate_comparison_report(comparison: Dict) -> str:
    """生成比较报告"""
    from_iter = comparison["from_iteration"]
    to_iter = comparison.get("to_iteration")
    to_label = comparison["to_label"]

    sections = []

    # 标题
    if to_iter:
        title = f"Iteration Comparison: {from_iter} → {to_iter}"
    else:
        title = f"Iteration Comparison: {from_iter} → Current"

    # 摘要
    summary_lines = []
    changes = comparison["changes"]

    for file_type, type_changes in changes.items():
        added = len(type_changes.get("added", []))
        removed = len(type_changes.get("removed", []))
        modified = len(type_changes.get("modified", []))

        if added or removed or modified:
            parts = []
            if added:
                parts.append(f"{added} added")
            if modified:
                parts.append(f"{modified} modified")
            if removed:
                parts.append(f"{removed} removed")
            summary_lines.append(f"- **{file_type.upper()}**: {', '.join(parts)}")

    if not summary_lines:
        summary_lines.append("No changes detected")

    sections.append({"title": "Summary", "content": "\n".join(summary_lines)})

    # 详细变更
    type_labels = {
        "prd": "PRD Changes",
        "architecture": "Architecture Changes",
        "openapi": "API Changes (OpenAPI)",
        "schemas": "Schema Changes (JSON Schema)",
    }

    for file_type, type_changes in changes.items():
        content_parts = []

        # 新增文件
        for f in type_changes.get("added", []):
            content_parts.append(f"**+ Added**: `{f.get('path', 'unknown')}`")

        # 删除文件
        for f in type_changes.get("removed", []):
            content_parts.append(f"**- Removed**: `{f.get('path', 'unknown')}`")

        # 修改文件
        for f in type_changes.get("modified", []):
            content_parts.append(
                f"**~ Modified**: `{f['path']}`\n"
                f"  - Version: {f['from_version']} → {f['to_version']}\n"
                f"  - Hash: {f['from_hash']} → {f['to_hash']}"
            )

        if content_parts:
            sections.append({"title": type_labels.get(file_type, file_type), "content": "\n\n".join(content_parts)})

    # Breaking Changes检查
    breaking_changes = []

    # 检查删除的文件
    for file_type, type_changes in changes.items():
        for f in type_changes.get("removed", []):
            breaking_changes.append(f"- File removed: `{f.get('path', 'unknown')}`")

    if breaking_changes:
        sections.append(
            {
                "title": "Breaking Changes",
                "content": "⚠️ **Potential breaking changes detected:**\n\n" + "\n".join(breaking_changes),
            }
        )
    else:
        sections.append({"title": "Breaking Changes", "content": "✅ None detected"})

    return generate_markdown_report(title, sections)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Compare changes between Planning Phase iterations")
    parser.add_argument("--from", dest="from_iter", type=int, required=True, help="Starting iteration number")
    parser.add_argument(
        "--to",
        dest="to_iter",
        type=str,
        default="current",
        help='Target iteration number or "current" (default: current)',
    )
    parser.add_argument(
        "--format", choices=["markdown", "json"], default="markdown", help="Output format (default: markdown)"
    )
    parser.add_argument("--output", type=str, help="Save to file instead of displaying")

    args = parser.parse_args()

    print("=" * 60)
    print("📊 Planning Iteration Comparison")
    print("=" * 60)

    # 解析目标迭代
    to_iter = None if args.to_iter == "current" else int(args.to_iter)

    try:
        print_status(f"Comparing iterations...", "progress")
        comparison = compare_iterations(args.from_iter, to_iter)

        # 生成输出
        if args.format == "json":
            output = json.dumps(comparison, indent=2, ensure_ascii=False)
        else:
            output = generate_comparison_report(comparison)

        # 输出结果
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(output)
            print_status(f"Report saved to: {output_path}", "success")
        else:
            print("\n" + output)

        # 打印摘要
        total_changes = sum(
            len(c.get("added", [])) + len(c.get("removed", [])) + len(c.get("modified", []))
            for c in comparison["changes"].values()
        )

        print("\n" + "=" * 60)
        print_status(f"Total changes: {total_changes}", "info")

        return 0

    except ValueError as e:
        print_status(str(e), "error")
        return 1
    except Exception as e:
        print_status(f"Comparison failed: {e}", "error")
        return 1


if __name__ == "__main__":
    sys.exit(main())
