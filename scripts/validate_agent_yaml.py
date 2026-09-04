#!/usr/bin/env python3
"""
Validate Agent YAML
验证Claude Code Agent文件中的YAML frontmatter格式
"""

import sys
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional

try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False

sys.path.insert(0, str(Path(__file__).parent / "lib"))

from planning_utils import print_status


def extract_yaml_frontmatter(content: str) -> Tuple[Optional[str], int, int]:
    """
    提取YAML frontmatter

    Returns:
        (yaml_content, start_line, end_line) or (None, 0, 0)
    """
    lines = content.split("\n")

    # 查找开始的 ---
    start_idx = -1
    for i, line in enumerate(lines):
        if line.strip() == "---":
            start_idx = i
            break

    if start_idx == -1:
        return None, 0, 0

    # 查找结束的 ---
    end_idx = -1
    for i in range(start_idx + 1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break

    if end_idx == -1:
        return None, start_idx + 1, 0

    # 提取YAML内容
    yaml_content = "\n".join(lines[start_idx + 1 : end_idx])
    return yaml_content, start_idx + 1, end_idx + 1


def validate_yaml_syntax(yaml_content: str) -> List[str]:
    """验证YAML语法"""
    errors = []

    if not HAS_YAML:
        # 基本检查
        if yaml_content.count(":") == 0:
            errors.append("No key-value pairs found")
        return errors

    try:
        data = yaml.safe_load(yaml_content)
        if data is None:
            errors.append("Empty YAML content")
        elif not isinstance(data, dict):
            errors.append("YAML must be a dictionary/mapping")
    except yaml.YAMLError as e:
        errors.append(f"YAML syntax error: {e}")

    return errors


def validate_agent_schema(yaml_content: str) -> List[str]:
    """验证Agent YAML schema"""
    warnings = []

    if not HAS_YAML:
        return warnings

    try:
        data = yaml.safe_load(yaml_content)
        if not data:
            return warnings

        # 检查必需字段
        required_fields = ["name", "description"]
        for field in required_fields:
            if field not in data:
                warnings.append(f"Missing recommended field: {field}")

        # 检查常见字段类型
        if "tools" in data and not isinstance(data["tools"], list):
            warnings.append("'tools' should be a list")

        if "commands" in data and not isinstance(data["commands"], (list, dict)):
            warnings.append("'commands' should be a list or dict")

    except yaml.YAMLError:
        pass  # 语法错误已在别处报告

    return warnings


def validate_markdown_structure(content: str) -> List[str]:
    """验证Markdown结构"""
    warnings = []

    # 检查必需section
    required_sections = ["Purpose", "Instructions"]
    for section in required_sections:
        if f"# {section}" not in content and f"## {section}" not in content:
            warnings.append(f"Missing section: {section}")

    # 检查代码块闭合
    code_blocks = content.count("```")
    if code_blocks % 2 != 0:
        warnings.append("Unclosed code block (odd number of ```)")

    return warnings


def validate_agent_file(file_path: Path) -> Dict:
    """验证Agent文件"""
    result = {"file": str(file_path), "valid": True, "errors": [], "warnings": []}

    if not file_path.exists():
        result["valid"] = False
        result["errors"].append(f"File not found: {file_path}")
        return result

    content = file_path.read_text(encoding="utf-8")

    # 提取YAML frontmatter
    yaml_content, start_line, end_line = extract_yaml_frontmatter(content)

    if yaml_content is None:
        result["warnings"].append("No YAML frontmatter found")
    else:
        # 验证YAML语法
        yaml_errors = validate_yaml_syntax(yaml_content)
        if yaml_errors:
            result["valid"] = False
            result["errors"].extend([f"Line {start_line}: {e}" for e in yaml_errors])
        else:
            # 验证schema
            schema_warnings = validate_agent_schema(yaml_content)
            result["warnings"].extend(schema_warnings)

    # 验证Markdown结构
    md_warnings = validate_markdown_structure(content)
    result["warnings"].extend(md_warnings)

    return result


def main():
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Validate Claude Code Agent YAML frontmatter")
    parser.add_argument("files", nargs="+", help="Agent markdown files to validate")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")

    args = parser.parse_args()

    print("=" * 60)
    print("🔍 Agent YAML Validation")
    print("=" * 60)

    results = []
    all_valid = True

    for file_path in args.files:
        path = Path(file_path)
        result = validate_agent_file(path)
        results.append(result)

        if not result["valid"]:
            all_valid = False
        if args.strict and result["warnings"]:
            all_valid = False
            result["valid"] = False

    if args.json:
        print(json.dumps(results, indent=2))
        return 0 if all_valid else 1

    # 输出结果
    for result in results:
        print(f"\n📄 {result['file']}")

        if result["errors"]:
            print("  Errors:")
            for error in result["errors"]:
                print(f"    ❌ {error}")

        if result["warnings"]:
            print("  Warnings:")
            for warning in result["warnings"]:
                print(f"    ⚠️ {warning}")

        if result["valid"] and not result["warnings"]:
            print("  ✅ Valid")

    print("\n" + "=" * 60)

    if all_valid:
        print("✅ All files valid!")
        return 0
    else:
        print("❌ Validation failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
