#!/usr/bin/env python3
"""
Planning Phase Iteration Validator
验证两次Planning迭代间的一致性，检测Breaking Changes
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

# 添加lib目录到path
sys.path.insert(0, str(Path(__file__).parent / "lib"))

from planning_utils import (
    init_utf8_encoding,
    load_snapshot,
    load_validation_rules,
    generate_markdown_report,
    compare_versions,
    print_status,
    get_project_root
)

# ========================================
# 验证结果类
# ========================================

class ValidationResult:
    """验证结果"""
    def __init__(self):
        self.breaking_changes: List[Dict] = []
        self.warnings: List[Dict] = []
        self.info: List[Dict] = []

    def add_breaking_change(self, type: str, details: Any, recommendation: str):
        self.breaking_changes.append({
            "type": type,
            "details": details,
            "severity": "HIGH",
            "recommendation": recommendation
        })

    def add_warning(self, type: str, details: Any, recommendation: str = ""):
        self.warnings.append({
            "type": type,
            "details": details,
            "severity": "MEDIUM",
            "recommendation": recommendation
        })

    def add_info(self, type: str, details: Any):
        self.info.append({
            "type": type,
            "details": details,
            "severity": "LOW"
        })

    def has_breaking_changes(self) -> bool:
        return len(self.breaking_changes) > 0

    def has_warnings(self) -> bool:
        return len(self.warnings) > 0

# ========================================
# PRD验证逻辑
# ========================================

def validate_prd_changes(prev: Dict, curr: Dict, rules: Dict) -> ValidationResult:
    """验证PRD文件的变更"""
    result = ValidationResult()

    prev_files = {f['path']: f for f in prev.get("files", {}).get("prd", [])}
    curr_files = {f['path']: f for f in curr.get("files", {}).get("prd", [])}

    # 检查文件删除
    deleted_files = set(prev_files.keys()) - set(curr_files.keys())
    if deleted_files and not rules.get("prd_validation", {}).get("can_delete", True):
        result.add_breaking_change(
            "PRD File Deletion",
            list(deleted_files),
            "恢复被删除的PRD文件或明确标记为deprecated"
        )

    # 检查版本号递增
    for path in curr_files:
        if path in prev_files:
            prev_version = prev_files[path].get("version", "unknown")
            curr_version = curr_files[path].get("version", "unknown")

            if prev_version != "unknown" and curr_version != "unknown":
                if compare_versions(curr_version, prev_version) <= 0:
                    if rules.get("prd_validation", {}).get("version_must_increment", True):
                        result.add_warning(
                            "PRD Version Not Incremented",
                            f"{path}: {prev_version} → {curr_version}",
                            "递增版本号以反映变更"
                        )

            # 检查hash变化
            if prev_files[path]["hash"] != curr_files[path]["hash"]:
                result.add_info(
                    "PRD File Modified",
                    f"{path}: Version {curr_version}"
                )

    # 检查新增文件
    added_files = set(curr_files.keys()) - set(prev_files.keys())
    for path in added_files:
        result.add_info(
            "New PRD File Added",
            path
        )

    return result

# ========================================
# Architecture验证逻辑
# ========================================

def validate_architecture_changes(prev: Dict, curr: Dict, rules: Dict) -> ValidationResult:
    """验证Architecture文件的变更"""
    result = ValidationResult()

    prev_files = {f['path']: f for f in prev.get("files", {}).get("architecture", [])}
    curr_files = {f['path']: f for f in curr.get("files", {}).get("architecture", [])}

    # 检查文件删除
    deleted_files = set(prev_files.keys()) - set(curr_files.keys())
    if deleted_files:
        result.add_breaking_change(
            "Architecture File Deletion",
            list(deleted_files),
            "Architecture文件不能删除，只能标记为deprecated"
        )

    # 检查版本号递增
    for path in curr_files:
        if path in prev_files:
            prev_version = prev_files[path].get("version", "unknown")
            curr_version = curr_files[path].get("version", "unknown")

            if prev_version != "unknown" and curr_version != "unknown":
                if compare_versions(curr_version, prev_version) <= 0:
                    result.add_warning(
                        "Architecture Version Not Incremented",
                        f"{path}: {prev_version} → {curr_version}",
                        "递增版本号以反映变更"
                    )

            # 检查hash变化
            if prev_files[path]["hash"] != curr_files[path]["hash"]:
                result.add_info(
                    "Architecture File Modified",
                    f"{path}: Version {curr_version}"
                )

    return result

# ========================================
# OpenAPI验证逻辑
# ========================================

def validate_openapi_changes(prev: Dict, curr: Dict, rules: Dict) -> ValidationResult:
    """验证OpenAPI Spec的变更"""
    result = ValidationResult()

    prev_specs = {f['path']: f for f in prev.get("files", {}).get("api_specs", [])}
    curr_specs = {f['path']: f for f in curr.get("files", {}).get("api_specs", [])}

    # 检查OpenAPI spec删除
    deleted_specs = set(prev_specs.keys()) - set(curr_specs.keys())
    if deleted_specs:
        result.add_breaking_change(
            "OpenAPI Spec File Deleted",
            list(deleted_specs),
            "不能删除OpenAPI spec文件"
        )

    # 检查版本和hash变化
    for path in curr_specs:
        if path in prev_specs:
            prev_version = prev_specs[path].get("version", "unknown")
            curr_version = curr_specs[path].get("version", "unknown")
            prev_hash = prev_specs[path]["hash"]
            curr_hash = curr_specs[path]["hash"]

            # Hash变化但版本未变
            if prev_hash != curr_hash:
                if prev_version == curr_version:
                    result.add_warning(
                        "OpenAPI Spec Modified Without Version Change",
                        f"{path}: Content changed but version unchanged ({curr_version})",
                        "更新OpenAPI spec的version字段"
                    )
                else:
                    result.add_info(
                        "OpenAPI Spec Modified",
                        f"{path}: {prev_version} → {curr_version}"
                    )

    return result

# ========================================
# Epic验证逻辑
# ========================================

def validate_epic_changes(prev: Dict, curr: Dict, rules: Dict) -> ValidationResult:
    """验证Epic文件的变更"""
    result = ValidationResult()

    prev_epics = {f['path']: f for f in prev.get("files", {}).get("epics", [])}
    curr_epics = {f['path']: f for f in curr.get("files", {}).get("epics", [])}

    # 检查Epic删除
    deleted_epics = set(prev_epics.keys()) - set(curr_epics.keys())
    if deleted_epics and not rules.get("prd_validation", {}).get("epics", {}).get("can_delete", False):
        result.add_breaking_change(
            "Epic Deleted",
            list(deleted_epics),
            "Epic不能删除，如需合并请明确记录"
        )

    # 检查Epic数量减少
    prev_count = len(prev_epics)
    curr_count = len(curr_epics)
    if curr_count < prev_count:
        result.add_warning(
            "Epic Count Decreased",
            f"从{prev_count}减少到{curr_count}",
            "确认Epic合并或删除是有意的"
        )

    # 检查新增Epic
    added_epics = set(curr_epics.keys()) - set(prev_epics.keys())
    for path in added_epics:
        result.add_info(
            "New Epic Added",
            path
        )

    return result

# ========================================
# 虚拟数据检测
# ========================================

def detect_mock_data(prev: Dict, curr: Dict, rules: Dict) -> ValidationResult:
    """检测虚拟数据引入"""
    result = ValidationResult()

    custom_rules = rules.get("custom_rules", {})
    mock_detection = custom_rules.get("detect_mock_data_introduction", {})

    if not mock_detection.get("enabled", False):
        return result

    patterns = mock_detection.get("patterns", [])

    # 检查所有新增或修改的文件
    all_curr_files = []
    for category in curr.get("files", {}).values():
        all_curr_files.extend(category)

    all_prev_files = {f['path']: f for files in prev.get("files", {}).values() for f in files}

    for file in all_curr_files:
        path = file['path']
        curr_hash = file['hash']

        # 新增或修改的文件
        if path not in all_prev_files or all_prev_files[path]['hash'] != curr_hash:
            # 检查是否包含mock data patterns
            # 注意：这里简化处理，实际需要读取文件内容检查
            for pattern in patterns:
                if pattern.lower() in path.lower():
                    result.add_warning(
                        "Potential Mock Data Detected",
                        f"{path} contains pattern '{pattern}'",
                        "确认这是真实数据而非虚拟数据"
                    )
                    break

    return result

# ========================================
# 主验证逻辑
# ========================================

def validate_iterations(prev_iteration: int, curr_iteration: int, rules: Dict) -> ValidationResult:
    """验证两次迭代间的一致性"""
    print_status(f"Loading snapshots...", "progress")

    prev_snapshot = load_snapshot(prev_iteration)
    curr_snapshot = load_snapshot(curr_iteration)

    if prev_snapshot is None:
        raise FileNotFoundError(f"Previous snapshot not found: iteration-{prev_iteration:03d}.json")

    if curr_snapshot is None:
        raise FileNotFoundError(f"Current snapshot not found: iteration-{curr_iteration:03d}.json")

    print_status(f"Validating Iteration {prev_iteration} → {curr_iteration}...", "progress")

    combined_result = ValidationResult()

    # PRD验证
    print_status("  Validating PRD changes...", "progress")
    prd_result = validate_prd_changes(prev_snapshot, curr_snapshot, rules)
    combined_result.breaking_changes.extend(prd_result.breaking_changes)
    combined_result.warnings.extend(prd_result.warnings)
    combined_result.info.extend(prd_result.info)

    # Architecture验证
    print_status("  Validating Architecture changes...", "progress")
    arch_result = validate_architecture_changes(prev_snapshot, curr_snapshot, rules)
    combined_result.breaking_changes.extend(arch_result.breaking_changes)
    combined_result.warnings.extend(arch_result.warnings)
    combined_result.info.extend(arch_result.info)

    # OpenAPI验证
    print_status("  Validating OpenAPI Spec changes...", "progress")
    api_result = validate_openapi_changes(prev_snapshot, curr_snapshot, rules)
    combined_result.breaking_changes.extend(api_result.breaking_changes)
    combined_result.warnings.extend(api_result.warnings)
    combined_result.info.extend(api_result.info)

    # Epic验证
    print_status("  Validating Epic changes...", "progress")
    epic_result = validate_epic_changes(prev_snapshot, curr_snapshot, rules)
    combined_result.breaking_changes.extend(epic_result.breaking_changes)
    combined_result.warnings.extend(epic_result.warnings)
    combined_result.info.extend(epic_result.info)

    # 虚拟数据检测
    print_status("  Detecting mock data introduction...", "progress")
    mock_result = detect_mock_data(prev_snapshot, curr_snapshot, rules)
    combined_result.breaking_changes.extend(mock_result.breaking_changes)
    combined_result.warnings.extend(mock_result.warnings)
    combined_result.info.extend(mock_result.info)

    return combined_result, prev_snapshot, curr_snapshot

# ========================================
# 报告生成
# ========================================

def generate_validation_report(
    result: ValidationResult,
    prev_snapshot: Dict,
    curr_snapshot: Dict,
    output_path: Path
):
    """生成验证报告"""
    sections = []

    # Summary
    summary_content = f"""
**Previous Iteration**: {prev_snapshot['iteration']}
**Current Iteration**: {curr_snapshot['iteration']}
**Previous Git Commit**: `{prev_snapshot['git_commit'][:8]}...`
**Current Git Commit**: `{curr_snapshot['git_commit'][:8]}...`

**Validation Results**:
- 🔴 Breaking Changes: {len(result.breaking_changes)}
- 🟡 Warnings: {len(result.warnings)}
- 🟢 Info: {len(result.info)}
"""
    sections.append({"title": "Summary", "content": summary_content})

    # Breaking Changes
    if result.breaking_changes:
        bc_content = ""
        for i, change in enumerate(result.breaking_changes, 1):
            bc_content += f"### {i}. ❌ {change['type']}\n\n"
            bc_content += f"**Details**: {change['details']}\n\n"
            bc_content += f"**Severity**: {change['severity']}\n\n"
            bc_content += f"**Recommendation**: {change['recommendation']}\n\n"
            bc_content += "---\n\n"
        sections.append({"title": "🔴 Breaking Changes", "content": bc_content})

    # Warnings
    if result.warnings:
        warn_content = ""
        for i, warning in enumerate(result.warnings, 1):
            warn_content += f"### {i}. ⚠️ {warning['type']}\n\n"
            warn_content += f"**Details**: {warning['details']}\n\n"
            warn_content += f"**Recommendation**: {warning.get('recommendation', 'Review manually')}\n\n"
            warn_content += "---\n\n"
        sections.append({"title": "🟡 Warnings", "content": warn_content})

    # Info
    if result.info:
        info_content = ""
        for i, info in enumerate(result.info, 1):
            info_content += f"{i}. ✅ **{info['type']}**: {info['details']}\n\n"
        sections.append({"title": "🟢 Info", "content": info_content})

    # Version Matrix
    version_matrix = f"""
| Category | Previous | Current | Change |
|----------|----------|---------|--------|
| PRD Files | {prev_snapshot['statistics']['prd_count']} | {curr_snapshot['statistics']['prd_count']} | {curr_snapshot['statistics']['prd_count'] - prev_snapshot['statistics']['prd_count']:+d} |
| Architecture Files | {prev_snapshot['statistics']['architecture_count']} | {curr_snapshot['statistics']['architecture_count']} | {curr_snapshot['statistics']['architecture_count'] - prev_snapshot['statistics']['architecture_count']:+d} |
| Epic Files | {prev_snapshot['statistics']['epic_count']} | {curr_snapshot['statistics']['epic_count']} | {curr_snapshot['statistics']['epic_count'] - prev_snapshot['statistics']['epic_count']:+d} |
| API Specs | {prev_snapshot['statistics']['api_spec_count']} | {curr_snapshot['statistics']['api_spec_count']} | {curr_snapshot['statistics']['api_spec_count'] - prev_snapshot['statistics']['api_spec_count']:+d} |
"""
    sections.append({"title": "Version Matrix", "content": version_matrix})

    # Recommendations
    if result.has_breaking_changes():
        rec_content = """
🔴 **Critical**: This iteration contains Breaking Changes.

**Required Actions**:
1. Review all Breaking Changes listed above
2. For each Breaking Change, decide:
   - **Accept**: Update OpenAPI spec version (Major increment) and document in CHANGELOG
   - **Reject**: Revert changes to avoid breaking change
   - **Modify**: Adjust implementation to avoid breaking change
3. DO NOT proceed until all Breaking Changes are resolved
4. Run validation again after fixes

**How to Fix**:
```bash
# If accepting breaking changes
python scripts/finalize-iteration.py --breaking

# If reverting
git checkout docs/prd.md  # Example: revert specific file
python scripts/validate-iteration.py  # Re-validate
```
"""
        sections.append({"title": "Recommendations", "content": rec_content})
    elif result.has_warnings():
        rec_content = """
🟡 **Warnings Found**: Review recommended, but not blocking.

**Suggested Actions**:
1. Review all warnings
2. Address concerns or document reasons for ignoring
3. Proceed with caution

**You can proceed with**:
```bash
python scripts/finalize-iteration.py
```
"""
        sections.append({"title": "Recommendations", "content": rec_content})
    else:
        rec_content = """
✅ **All Checks Passed**: No issues detected.

**Next Steps**:
```bash
python scripts/finalize-iteration.py
git commit -m "Planning Iteration {curr_snapshot['iteration']} Complete"
```
"""
        sections.append({"title": "Recommendations", "content": rec_content})

    # 生成报告
    report = generate_markdown_report(
        f"Planning Iteration {curr_snapshot['iteration']} Validation Report",
        sections
    )

    # 保存报告
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print_status(f"Validation report saved: {output_path}", "success")

# ========================================
# CLI接口
# ========================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate consistency between Planning Phase iterations"
    )
    parser.add_argument(
        '--iteration',
        type=int,
        required=True,
        help='Current iteration number to validate'
    )
    parser.add_argument(
        '--final',
        action='store_true',
        help='Run final validation before finalize (stricter checks)'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output report path (default: iteration-{iteration}-validation-report.md)'
    )

    args = parser.parse_args()

    # Auto-detect previous iteration
    previous_iteration = args.iteration - 1 if args.iteration > 1 else 1
    current_iteration = args.iteration

    # Initialize UTF-8 encoding for Windows
    init_utf8_encoding()

    # 加载验证规则
    try:
        rules = load_validation_rules()
    except FileNotFoundError as e:
        print_status(f"Error: {e}", "error")
        return 1

    # 执行验证
    try:
        result, prev_snapshot, curr_snapshot = validate_iterations(
            previous_iteration,
            current_iteration,
            rules
        )
    except FileNotFoundError as e:
        print_status(f"Error: {e}", "error")
        return 1

    # 生成报告
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = get_project_root() / f"iteration-{current_iteration:03d}-validation-report.md"

    # Final validation stricter mode
    if args.final:
        print_status("Running FINAL validation (stricter checks)...", "warning")

    generate_validation_report(result, prev_snapshot, curr_snapshot, output_path)

    # 打印摘要
    print("\n" + "="*60)
    print("📊 Validation Summary")
    print("="*60)
    print(f"🔴 Breaking Changes: {len(result.breaking_changes)}")
    print(f"🟡 Warnings: {len(result.warnings)}")
    print(f"🟢 Info: {len(result.info)}")
    print("="*60)

    if result.has_breaking_changes():
        print("\n❌ VALIDATION FAILED: Breaking changes detected!")
        print(f"Review the report: {output_path}")
        return 1
    elif result.has_warnings():
        print("\n⚠️ VALIDATION PASSED WITH WARNINGS")
        print(f"Review the report: {output_path}")
        return 0
    else:
        print("\n✅ VALIDATION PASSED: No issues detected!")
        return 0

if __name__ == "__main__":
    sys.exit(main())
