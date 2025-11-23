#!/usr/bin/env python3
"""
Story SDD Contract Validator
Phase 4 验证工具：检查Story是否符合SDD规范（OpenAPI、JSON Schema、ADR）

Usage:
    python scripts/validate-story-sdd.py --story docs/stories/12.1.story.md
    python scripts/validate-story-sdd.py --story docs/stories/12.1.story.md --strict
"""

import sys
import re
import json
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime

# 添加lib目录到path
sys.path.insert(0, str(Path(__file__).parent / "lib"))

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')


# ========================================
# 验证结果类
# ========================================

class SDDValidationResult:
    """SDD验证结果"""
    def __init__(self):
        self.errors: List[Dict] = []
        self.warnings: List[Dict] = []
        self.info: List[Dict] = []
        self.passed_checks: List[str] = []

    def add_error(self, check: str, details: str, recommendation: str):
        self.errors.append({
            "check": check,
            "details": details,
            "severity": "ERROR",
            "recommendation": recommendation
        })

    def add_warning(self, check: str, details: str, recommendation: str = ""):
        self.warnings.append({
            "check": check,
            "details": details,
            "severity": "WARNING",
            "recommendation": recommendation
        })

    def add_info(self, check: str, details: str):
        self.info.append({
            "check": check,
            "details": details,
            "severity": "INFO"
        })

    def add_passed(self, check: str):
        self.passed_checks.append(check)

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


# ========================================
# 辅助函数
# ========================================

def get_project_root() -> Path:
    """获取项目根目录"""
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "CLAUDE.md").exists():
            return current
        current = current.parent
    return Path(__file__).parent.parent


def print_status(message: str, status_type: str = "info"):
    """打印状态消息"""
    icons = {
        "success": "✅",
        "error": "❌",
        "warning": "⚠️",
        "progress": "⏳",
        "info": "ℹ️"
    }
    icon = icons.get(status_type, "•")
    print(f"{icon} {message}")


def load_story_file(story_path: Path) -> str:
    """加载Story文件内容"""
    if not story_path.exists():
        raise FileNotFoundError(f"Story file not found: {story_path}")
    return story_path.read_text(encoding='utf-8')


def load_openapi_spec(spec_path: Path) -> Dict:
    """加载OpenAPI规范"""
    if not spec_path.exists():
        return {}

    # Try multiple encodings
    for encoding in ['utf-8', 'utf-8-sig', 'gbk', 'latin-1']:
        try:
            content = spec_path.read_text(encoding=encoding)
            if spec_path.suffix in ['.yml', '.yaml']:
                return yaml.safe_load(content) or {}
            elif spec_path.suffix == '.json':
                return json.loads(content)
            return {}
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            print(f"⚠️ Warning: Could not load {spec_path}: {e}")
            return {}
    return {}


def load_json_schema(schema_path: Path) -> Dict:
    """加载JSON Schema"""
    if not schema_path.exists():
        return {}
    for encoding in ['utf-8', 'utf-8-sig', 'gbk', 'latin-1']:
        try:
            return json.loads(schema_path.read_text(encoding=encoding))
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            print(f"⚠️ Warning: Could not load {schema_path}: {e}")
            return {}
    return {}


# ========================================
# 提取Story中的SDD引用
# ========================================

def extract_api_endpoints(story_content: str) -> List[Dict]:
    """从Story内容中提取API端点引用"""
    endpoints = []

    # 匹配模式: POST /api/xxx, GET /api/xxx 等
    endpoint_pattern = r'(GET|POST|PUT|DELETE|PATCH)\s+(/api/[^\s\]]+)'
    matches = re.findall(endpoint_pattern, story_content)

    for method, path in matches:
        endpoints.append({
            "method": method,
            "path": path.rstrip(',').rstrip(')')
        })

    return endpoints


def extract_schema_references(story_content: str) -> List[str]:
    """从Story内容中提取Schema引用"""
    schemas = []

    # 匹配模式: CanvasNode, AgentResponse 等（首字母大写的标识符）
    # 从specs/data/引用中提取
    schema_pattern = r'specs/data/([a-z-]+)\.schema\.json'
    matches = re.findall(schema_pattern, story_content)
    schemas.extend(matches)

    # 也匹配直接的Schema名称引用
    name_pattern = r'Schema[:\s]+(\w+)'
    matches = re.findall(name_pattern, story_content)
    schemas.extend(matches)

    return list(set(schemas))


def extract_adr_references(story_content: str) -> List[str]:
    """从Story内容中提取ADR引用"""
    adrs = []

    # 匹配模式: ADR-001, ADR-002 等
    adr_pattern = r'ADR-(\d{3,4})'
    matches = re.findall(adr_pattern, story_content)

    return list(set(matches))


def check_sdd_section_exists(story_content: str) -> Tuple[bool, bool]:
    """检查SDD规范参考和ADR决策关联section是否存在"""
    has_sdd = "SDD规范参考" in story_content or "SDD Spec Reference" in story_content
    has_adr = "ADR决策关联" in story_content or "ADR Decisions" in story_content
    return has_sdd, has_adr


# ========================================
# 验证逻辑
# ========================================

def validate_api_endpoints(
    endpoints: List[Dict],
    openapi_specs: Dict[str, Dict],
    result: SDDValidationResult
):
    """验证API端点是否在OpenAPI spec中定义"""
    if not endpoints:
        result.add_warning(
            "API Endpoint Check",
            "No API endpoints found in Story",
            "If this Story involves API calls, add endpoint references"
        )
        return

    for endpoint in endpoints:
        method = endpoint["method"].lower()
        path = endpoint["path"]
        found = False

        # 在所有OpenAPI specs中查找
        for spec_name, spec in openapi_specs.items():
            paths = spec.get("paths", {})

            # 直接匹配
            if path in paths:
                if method in paths[path]:
                    found = True
                    result.add_info(
                        "API Endpoint Validated",
                        f"{endpoint['method']} {path} found in {spec_name}"
                    )
                    break

            # 路径参数匹配 (例如 /api/canvas/{id})
            for spec_path in paths:
                # 将路径参数转换为正则
                regex_path = re.sub(r'\{[^}]+\}', r'[^/]+', spec_path)
                if re.match(f"^{regex_path}$", path):
                    if method in paths[spec_path]:
                        found = True
                        result.add_info(
                            "API Endpoint Validated",
                            f"{endpoint['method']} {path} matches {spec_path} in {spec_name}"
                        )
                        break

            if found:
                break

        if not found:
            result.add_error(
                "API Endpoint Not Defined",
                f"{endpoint['method']} {path} not found in any OpenAPI spec",
                f"Add this endpoint to specs/api/*.openapi.yml or verify the path is correct"
            )


def validate_schema_references(
    schemas: List[str],
    json_schemas: Dict[str, Dict],
    result: SDDValidationResult
):
    """验证Schema引用是否存在"""
    if not schemas:
        result.add_info(
            "Schema Check",
            "No explicit schema references found in Story"
        )
        return

    for schema_name in schemas:
        # 转换为文件名格式
        file_name = schema_name.lower().replace('_', '-')

        if file_name in json_schemas or schema_name in json_schemas:
            result.add_info(
                "Schema Validated",
                f"Schema '{schema_name}' found in specs/data/"
            )
        else:
            result.add_warning(
                "Schema Not Found",
                f"Schema '{schema_name}' not found in specs/data/",
                f"Add {file_name}.schema.json to specs/data/ or verify the name"
            )


def validate_adr_references(
    adrs: List[str],
    adr_dir: Path,
    result: SDDValidationResult
):
    """验证ADR引用是否存在"""
    if not adrs:
        result.add_warning(
            "ADR Check",
            "No ADR references found in Story",
            "If this Story involves architecture decisions, add ADR references"
        )
        return

    for adr_num in adrs:
        # 查找ADR文件
        adr_pattern = f"{adr_num}-*.md"
        matching_files = list(adr_dir.glob(adr_pattern))

        if matching_files:
            result.add_info(
                "ADR Validated",
                f"ADR-{adr_num} found: {matching_files[0].name}"
            )
        else:
            result.add_error(
                "ADR Not Found",
                f"ADR-{adr_num} not found in {adr_dir}",
                f"Create this ADR using /architect → *create-adr command"
            )


def validate_required_sections(
    story_content: str,
    result: SDDValidationResult
):
    """验证必填Section是否存在且非空"""
    has_sdd, has_adr = check_sdd_section_exists(story_content)

    if has_sdd:
        # 检查SDD section是否有内容
        sdd_match = re.search(
            r'(?:SDD规范参考|SDD Spec Reference)[^\n]*\n(.*?)(?=\n##|\n### [A-Z]|\Z)',
            story_content,
            re.DOTALL
        )
        if sdd_match:
            content = sdd_match.group(1).strip()
            if len(content) < 50:  # 内容太少
                result.add_warning(
                    "SDD Section Empty",
                    "SDD规范参考 section exists but has minimal content",
                    "Add API endpoint and Schema references from specs/ directory"
                )
            else:
                result.add_passed("SDD规范参考 section present and has content")
        else:
            result.add_passed("SDD规范参考 section present")
    else:
        result.add_error(
            "Missing Required Section",
            "SDD规范参考 section not found in Story",
            "Add SDD规范参考 section with OpenAPI and Schema references"
        )

    if has_adr:
        # 检查ADR section是否有内容
        adr_match = re.search(
            r'(?:ADR决策关联|ADR Decisions)[^\n]*\n(.*?)(?=\n##|\n### [A-Z]|\Z)',
            story_content,
            re.DOTALL
        )
        if adr_match:
            content = adr_match.group(1).strip()
            if len(content) < 30:
                result.add_warning(
                    "ADR Section Empty",
                    "ADR决策关联 section exists but has minimal content",
                    "Add relevant ADR references from docs/architecture/decisions/"
                )
            else:
                result.add_passed("ADR决策关联 section present and has content")
        else:
            result.add_passed("ADR决策关联 section present")
    else:
        result.add_error(
            "Missing Required Section",
            "ADR决策关联 section not found in Story",
            "Add ADR决策关联 section with architecture decision references"
        )


# ========================================
# 主验证函数
# ========================================

def validate_story_sdd(story_path: Path, strict: bool = False) -> SDDValidationResult:
    """执行完整的SDD验证"""
    result = SDDValidationResult()
    project_root = get_project_root()

    print_status(f"Validating Story: {story_path}", "progress")

    # 加载Story
    try:
        story_content = load_story_file(story_path)
    except FileNotFoundError as e:
        result.add_error("File Not Found", str(e), "Check the story path")
        return result

    # 加载OpenAPI specs
    print_status("Loading OpenAPI specifications...", "progress")
    specs_dir = project_root / "specs" / "api"
    openapi_specs = {}

    if specs_dir.exists():
        for spec_file in specs_dir.glob("*.openapi.yml"):
            spec_name = spec_file.stem
            openapi_specs[spec_name] = load_openapi_spec(spec_file)
        for spec_file in specs_dir.glob("*.openapi.yaml"):
            spec_name = spec_file.stem
            openapi_specs[spec_name] = load_openapi_spec(spec_file)

    if not openapi_specs:
        result.add_warning(
            "No OpenAPI Specs",
            f"No OpenAPI specs found in {specs_dir}",
            "Create OpenAPI specs in Phase 3 using Architect agent"
        )

    # 加载JSON Schemas
    print_status("Loading JSON Schemas...", "progress")
    schemas_dir = project_root / "specs" / "data"
    json_schemas = {}

    if schemas_dir.exists():
        for schema_file in schemas_dir.glob("*.schema.json"):
            schema_name = schema_file.stem.replace('.schema', '')
            json_schemas[schema_name] = load_json_schema(schema_file)

    # 加载ADR目录
    adr_dir = project_root / "docs" / "architecture" / "decisions"

    # 提取Story中的引用
    print_status("Extracting SDD references from Story...", "progress")
    endpoints = extract_api_endpoints(story_content)
    schemas = extract_schema_references(story_content)
    adrs = extract_adr_references(story_content)

    print_status(f"Found: {len(endpoints)} endpoints, {len(schemas)} schemas, {len(adrs)} ADRs", "info")

    # 执行验证
    print_status("Validating required sections...", "progress")
    validate_required_sections(story_content, result)

    print_status("Validating API endpoints...", "progress")
    validate_api_endpoints(endpoints, openapi_specs, result)

    print_status("Validating schema references...", "progress")
    validate_schema_references(schemas, json_schemas, result)

    print_status("Validating ADR references...", "progress")
    validate_adr_references(adrs, adr_dir, result)

    # Strict模式：将warnings也视为errors
    if strict and result.has_warnings():
        for warning in result.warnings:
            result.add_error(
                f"[Strict] {warning['check']}",
                warning['details'],
                warning['recommendation']
            )

    return result


# ========================================
# 报告生成
# ========================================

def generate_validation_report(
    result: SDDValidationResult,
    story_path: Path,
    output_path: Optional[Path] = None
) -> str:
    """生成验证报告"""
    report_lines = [
        f"# Story SDD Validation Report",
        f"",
        f"**Story**: `{story_path}`",
        f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"",
        f"## Summary",
        f"",
        f"- ❌ Errors: {len(result.errors)}",
        f"- ⚠️ Warnings: {len(result.warnings)}",
        f"- ✅ Passed: {len(result.passed_checks)}",
        f"- ℹ️ Info: {len(result.info)}",
        f""
    ]

    # Errors
    if result.errors:
        report_lines.extend([
            f"## ❌ Errors (Must Fix)",
            f""
        ])
        for i, error in enumerate(result.errors, 1):
            report_lines.extend([
                f"### {i}. {error['check']}",
                f"",
                f"**Details**: {error['details']}",
                f"",
                f"**Recommendation**: {error['recommendation']}",
                f"",
                f"---",
                f""
            ])

    # Warnings
    if result.warnings:
        report_lines.extend([
            f"## ⚠️ Warnings (Should Fix)",
            f""
        ])
        for i, warning in enumerate(result.warnings, 1):
            report_lines.extend([
                f"### {i}. {warning['check']}",
                f"",
                f"**Details**: {warning['details']}",
                f"",
                f"**Recommendation**: {warning.get('recommendation', 'Review manually')}",
                f"",
                f"---",
                f""
            ])

    # Passed
    if result.passed_checks:
        report_lines.extend([
            f"## ✅ Passed Checks",
            f""
        ])
        for check in result.passed_checks:
            report_lines.append(f"- ✅ {check}")
        report_lines.append("")

    # Info
    if result.info:
        report_lines.extend([
            f"## ℹ️ Information",
            f""
        ])
        for info in result.info:
            report_lines.append(f"- {info['check']}: {info['details']}")
        report_lines.append("")

    # Next Steps
    if result.has_errors():
        report_lines.extend([
            f"## 🔴 Next Steps",
            f"",
            f"1. Fix all errors listed above",
            f"2. Re-run validation: `python scripts/validate-story-sdd.py --story {story_path}`",
            f"3. Story cannot proceed to development until all errors are fixed",
            f""
        ])
    elif result.has_warnings():
        report_lines.extend([
            f"## 🟡 Next Steps",
            f"",
            f"1. Review warnings and fix if possible",
            f"2. Story can proceed but may have quality issues",
            f"3. Consider running in strict mode: `--strict`",
            f""
        ])
    else:
        report_lines.extend([
            f"## 🟢 Next Steps",
            f"",
            f"1. Story passes SDD validation",
            f"2. Ready for development: `/dev` → `*develop-story`",
            f""
        ])

    report = "\n".join(report_lines)

    # 保存报告
    if output_path:
        output_path.write_text(report, encoding='utf-8')
        print_status(f"Report saved: {output_path}", "success")

    return report


# ========================================
# CLI入口
# ========================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate Story against SDD specifications (OpenAPI, JSON Schema, ADR)"
    )
    parser.add_argument(
        '--story',
        type=str,
        required=True,
        help='Path to Story file (e.g., docs/stories/12.1.story.md)'
    )
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Strict mode: treat warnings as errors'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output report path (default: story-sdd-validation-report.md)'
    )

    args = parser.parse_args()

    # 解析路径
    project_root = get_project_root()
    story_path = Path(args.story)
    if not story_path.is_absolute():
        story_path = project_root / story_path

    # 执行验证
    result = validate_story_sdd(story_path, strict=args.strict)

    # 生成报告
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = project_root / "story-sdd-validation-report.md"

    report = generate_validation_report(result, story_path, output_path)

    # 打印摘要
    print("\n" + "=" * 60)
    print("📊 SDD Validation Summary")
    print("=" * 60)
    print(f"❌ Errors: {len(result.errors)}")
    print(f"⚠️ Warnings: {len(result.warnings)}")
    print(f"✅ Passed: {len(result.passed_checks)}")
    print("=" * 60)

    if result.has_errors():
        print("\n❌ VALIDATION FAILED: Fix errors before development")
        return 1
    elif result.has_warnings():
        print("\n⚠️ VALIDATION PASSED WITH WARNINGS")
        return 0
    else:
        print("\n✅ VALIDATION PASSED: Story ready for development")
        return 0


if __name__ == "__main__":
    sys.exit(main())
