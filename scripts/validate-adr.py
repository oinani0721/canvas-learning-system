#!/usr/bin/env python3
"""
ADR (Architecture Decision Record) Validator
验证ADR文件的完整性、编号连续性和引用有效性
"""

import sys
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any

# 添加lib目录到path
sys.path.insert(0, str(Path(__file__).parent / "lib"))

from planning_utils import init_utf8_encoding, print_status, generate_markdown_report, get_project_root

# ========================================
# ADR验证结果类
# ========================================


class ADRValidationResult:
    """ADR验证结果"""

    def __init__(self):
        self.errors: List[Dict] = []
        self.warnings: List[Dict] = []
        self.info: List[Dict] = []

    def add_error(self, adr: str, issue: str, recommendation: str):
        self.errors.append({"adr": adr, "issue": issue, "recommendation": recommendation})

    def add_warning(self, adr: str, issue: str, recommendation: str = ""):
        self.warnings.append({"adr": adr, "issue": issue, "recommendation": recommendation})

    def add_info(self, adr: str, detail: str):
        self.info.append({"adr": adr, "detail": detail})

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


# ========================================
# ADR解析函数
# ========================================


def parse_adr_number(filename: str) -> int:
    """从文件名解析ADR编号"""
    match = re.match(r"^(\d+)-", filename)
    if match:
        return int(match.group(1))
    return -1


def parse_adr_content(filepath: Path) -> Dict:
    """解析ADR文件内容"""
    content = filepath.read_text(encoding="utf-8")

    result = {
        "path": str(filepath),
        "filename": filepath.name,
        "number": parse_adr_number(filepath.name),
        "has_status": False,
        "has_context": False,
        "has_decision": False,
        "has_consequences": False,
        "status": None,
        "references": [],
    }

    # 检查必需章节
    if re.search(r"^##\s*Status", content, re.MULTILINE):
        result["has_status"] = True
        # 提取状态值
        status_match = re.search(r"^##\s*Status\s*\n+\s*(\w+)", content, re.MULTILINE)
        if status_match:
            result["status"] = status_match.group(1)

    if re.search(r"^##\s*Context", content, re.MULTILINE):
        result["has_context"] = True

    if re.search(r"^##\s*Decision", content, re.MULTILINE):
        result["has_decision"] = True

    if re.search(r"^##\s*Consequences", content, re.MULTILINE):
        result["has_consequences"] = True

    # 提取引用
    ref_section = re.search(r"^##\s*References\s*\n(.*?)(?=^##|\Z)", content, re.MULTILINE | re.DOTALL)
    if ref_section:
        refs = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", ref_section.group(1))
        result["references"] = refs

    return result


# ========================================
# 验证函数
# ========================================


def validate_numbering(adrs: List[Dict], result: ADRValidationResult):
    """验证ADR编号连续性"""
    numbers = sorted([adr["number"] for adr in adrs if adr["number"] > 0])

    if not numbers:
        return

    # 检查是否从1开始（或合理的起始数字）
    if numbers[0] != 1:
        result.add_warning(f"ADR-{numbers[0]:04d}", f"编号不从1开始，首个编号为{numbers[0]}", "如果是有意为之可以忽略")

    # 检查连续性
    for i in range(1, len(numbers)):
        if numbers[i] != numbers[i - 1] + 1:
            result.add_warning(
                f"ADR-{numbers[i]:04d}",
                f"编号不连续: 缺少ADR-{numbers[i - 1] + 1:04d}到ADR-{numbers[i] - 1:04d}",
                "检查是否有ADR被删除或遗漏",
            )


def validate_required_sections(adr: Dict, result: ADRValidationResult):
    """验证ADR必需章节"""
    adr_name = f"ADR-{adr['number']:04d}"

    if not adr["has_status"]:
        result.add_error(
            adr_name, "缺少Status章节", "添加## Status章节并设置状态（Proposed/Accepted/Deprecated/Superseded）"
        )

    if not adr["has_context"]:
        result.add_error(adr_name, "缺少Context章节", "添加## Context章节描述问题背景")

    if not adr["has_decision"]:
        result.add_error(adr_name, "缺少Decision章节", "添加## Decision章节记录最终决策")

    if not adr["has_consequences"]:
        result.add_warning(adr_name, "缺少Consequences章节", "建议添加## Consequences章节说明决策影响")


def validate_status(adr: Dict, result: ADRValidationResult):
    """验证ADR状态"""
    adr_name = f"ADR-{adr['number']:04d}"
    valid_statuses = ["Proposed", "Accepted", "Deprecated", "Superseded"]

    if adr["status"] and adr["status"] not in valid_statuses:
        result.add_warning(adr_name, f"非标准状态: {adr['status']}", f"建议使用标准状态: {', '.join(valid_statuses)}")


def validate_references(adr: Dict, result: ADRValidationResult):
    """验证ADR引用的文件是否存在"""
    adr_name = f"ADR-{adr['number']:04d}"
    project_root = get_project_root()

    for ref_name, ref_path in adr["references"]:
        # 跳过外部链接
        if ref_path.startswith("http"):
            continue

        # 检查本地文件引用
        full_path = project_root / ref_path
        if not full_path.exists():
            result.add_warning(adr_name, f"引用的文件不存在: {ref_path}", "检查文件路径是否正确或文件是否已被移动")


# ========================================
# 主验证逻辑
# ========================================


def validate_all_adrs(adr_dir: Path) -> Tuple[ADRValidationResult, List[Dict]]:
    """验证所有ADR文件"""
    result = ADRValidationResult()

    # 获取所有ADR文件
    adr_files = sorted(adr_dir.glob("*.md"))

    if not adr_files:
        result.add_warning("N/A", f"未找到ADR文件: {adr_dir}", "使用/architect *create-adr创建ADR")
        return result, []

    # 解析所有ADR
    adrs = []
    for adr_file in adr_files:
        try:
            adr_data = parse_adr_content(adr_file)
            adrs.append(adr_data)
            result.add_info(f"ADR-{adr_data['number']:04d}", f"Status: {adr_data['status'] or 'Unknown'}")
        except Exception as e:
            result.add_error(adr_file.name, f"解析失败: {str(e)}", "检查文件编码和格式")

    # 验证编号连续性
    print_status("  检查编号连续性...", "progress")
    validate_numbering(adrs, result)

    # 验证每个ADR
    for adr in adrs:
        print_status(f"  验证ADR-{adr['number']:04d}...", "progress")
        validate_required_sections(adr, result)
        validate_status(adr, result)
        validate_references(adr, result)

    return result, adrs


# ========================================
# 报告生成
# ========================================


def generate_validation_report(result: ADRValidationResult, adrs: List[Dict], output_path: Path):
    """生成验证报告"""
    sections = []

    # Summary
    summary_content = f"""
**Total ADRs**: {len(adrs)}
**Errors**: {len(result.errors)}
**Warnings**: {len(result.warnings)}

**Status Distribution**:
"""
    status_counts = {}
    for adr in adrs:
        status = adr.get("status", "Unknown")
        status_counts[status] = status_counts.get(status, 0) + 1

    for status, count in sorted(status_counts.items()):
        summary_content += f"- {status}: {count}\n"

    sections.append({"title": "Summary", "content": summary_content})

    # Errors
    if result.errors:
        error_content = ""
        for error in result.errors:
            error_content += f"### ❌ {error['adr']}\n\n"
            error_content += f"**Issue**: {error['issue']}\n\n"
            error_content += f"**Fix**: {error['recommendation']}\n\n"
            error_content += "---\n\n"
        sections.append({"title": "Errors", "content": error_content})

    # Warnings
    if result.warnings:
        warn_content = ""
        for warning in result.warnings:
            warn_content += f"### ⚠️ {warning['adr']}\n\n"
            warn_content += f"**Issue**: {warning['issue']}\n\n"
            if warning["recommendation"]:
                warn_content += f"**Suggestion**: {warning['recommendation']}\n\n"
            warn_content += "---\n\n"
        sections.append({"title": "Warnings", "content": warn_content})

    # ADR List
    if adrs:
        list_content = "| # | Status | File |\n|---|--------|------|\n"
        for adr in sorted(adrs, key=lambda x: x["number"]):
            list_content += f"| {adr['number']:04d} | {adr.get('status', 'Unknown')} | {adr['filename']} |\n"
        sections.append({"title": "ADR List", "content": list_content})

    # Generate report
    report = generate_markdown_report("ADR Validation Report", sections)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print_status(f"Report saved: {output_path}", "success")


# ========================================
# CLI接口
# ========================================


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Validate Architecture Decision Records (ADRs)")
    parser.add_argument(
        "--adr-dir",
        type=str,
        default="docs/architecture/decisions",
        help="Directory containing ADR files (default: docs/architecture/decisions)",
    )
    parser.add_argument("--output", type=str, help="Output report path (default: adr-validation-report.md)")
    parser.add_argument("--fail-on-error", action="store_true", help="Exit with code 1 if errors detected")

    args = parser.parse_args()

    # Initialize UTF-8 encoding for Windows
    init_utf8_encoding()

    project_root = get_project_root()
    adr_dir = project_root / args.adr_dir

    print("=" * 60)
    print("🔍 ADR Validation")
    print("=" * 60)

    if not adr_dir.exists():
        print_status(f"ADR directory not found: {adr_dir}", "error")
        return 1

    print_status(f"Scanning: {adr_dir}", "progress")

    # Run validation
    result, adrs = validate_all_adrs(adr_dir)

    # Generate report
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = project_root / "adr-validation-report.md"

    generate_validation_report(result, adrs, output_path)

    # Print summary
    print("\n" + "=" * 60)
    print("📊 Validation Summary")
    print("=" * 60)
    print(f"Total ADRs: {len(adrs)}")
    print(f"❌ Errors: {len(result.errors)}")
    print(f"⚠️ Warnings: {len(result.warnings)}")
    print(f"ℹ️ Info: {len(result.info)}")
    print("=" * 60)

    if result.has_errors():
        print("\n❌ VALIDATION FAILED: Errors detected!")
        print(f"Review the report: {output_path}")
        if args.fail_on_error:
            return 1
    elif result.has_warnings():
        print("\n⚠️ VALIDATION PASSED WITH WARNINGS")
        print(f"Review the report: {output_path}")
    else:
        print("\n✅ VALIDATION PASSED: All ADRs are valid!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
