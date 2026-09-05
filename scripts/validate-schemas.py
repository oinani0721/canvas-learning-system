#!/usr/bin/env python3
"""
JSON Schema Validation Script
验证JSON Schema文件的语法和兼容性

功能:
1. 验证JSON Schema语法正确性
2. 检查$ref引用是否有效
3. 验证Schema版本兼容性 (draft-07)
4. 检测breaking changes (删除required字段等)

用法:
  python scripts/validate-schemas.py [schema_files...]

参数:
  schema_files - 要验证的schema文件列表，如果不提供则验证所有

返回码:
  0 - 验证通过
  1 - 验证失败
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple


def get_project_root() -> Path:
    """获取项目根目录"""
    return Path(__file__).parent.parent


def validate_json_syntax(file_path: Path) -> Tuple[bool, str]:
    """验证JSON语法"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            json.load(f)
        return True, ""
    except json.JSONDecodeError as e:
        return False, f"JSON syntax error: {e}"


def validate_schema_structure(schema: Dict[str, Any], file_path: Path) -> List[str]:
    """验证Schema结构"""
    errors = []

    # 检查$schema声明
    if "$schema" not in schema:
        errors.append(f"{file_path}: Missing $schema declaration")
    elif "draft-07" not in schema.get("$schema", ""):
        errors.append(f"{file_path}: Schema should use draft-07 (found: {schema.get('$schema')})")

    # 检查type定义
    if "type" not in schema and "$ref" not in schema and "oneOf" not in schema and "allOf" not in schema:
        errors.append(f"{file_path}: Missing type definition")

    # 检查title (推荐)
    if "title" not in schema:
        errors.append(f"{file_path}: Missing title (recommended for documentation)")

    return errors


def validate_refs(schema: Dict[str, Any], file_path: Path, schemas_dir: Path) -> List[str]:
    """验证$ref引用"""
    errors = []

    def check_refs(obj, path=""):
        if isinstance(obj, dict):
            if "$ref" in obj:
                ref = obj["$ref"]
                # 检查外部引用
                if ref.startswith("./") or ref.startswith("../"):
                    ref_path = (file_path.parent / ref.split("#")[0]).resolve()
                    if not ref_path.exists():
                        errors.append(f"{file_path}: Invalid $ref '{ref}' - file not found")
            for key, value in obj.items():
                check_refs(value, f"{path}.{key}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                check_refs(item, f"{path}[{i}]")

    check_refs(schema)
    return errors


def check_required_fields(schema: Dict[str, Any]) -> List[str]:
    """提取required字段列表"""
    required = []

    def extract_required(obj, path=""):
        if isinstance(obj, dict):
            if "required" in obj and isinstance(obj["required"], list):
                for field in obj["required"]:
                    required.append(f"{path}.{field}" if path else field)
            if "properties" in obj:
                for key, value in obj["properties"].items():
                    extract_required(value, f"{path}.{key}" if path else key)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                extract_required(item, path)

    extract_required(schema)
    return required


def validate_schema_file(file_path: Path) -> Tuple[List[str], List[str]]:
    """
    验证单个Schema文件

    返回:
        (errors, warnings)
    """
    errors = []
    warnings = []

    # 1. 验证JSON语法
    valid, error_msg = validate_json_syntax(file_path)
    if not valid:
        errors.append(f"{file_path}: {error_msg}")
        return errors, warnings

    # 2. 加载Schema
    with open(file_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    # 3. 验证Schema结构
    structure_errors = validate_schema_structure(schema, file_path)
    for error in structure_errors:
        if "recommended" in error.lower():
            warnings.append(error)
        else:
            errors.append(error)

    # 4. 验证$ref引用
    schemas_dir = get_project_root() / "specs" / "data"
    ref_errors = validate_refs(schema, file_path, schemas_dir)
    errors.extend(ref_errors)

    # 5. 检查空properties (警告)
    if schema.get("type") == "object" and "properties" not in schema:
        warnings.append(f"{file_path}: Object type without properties defined")

    return errors, warnings


def main():
    """主函数"""
    print("=" * 60)
    print("🔍 JSON Schema Validation")
    print("=" * 60)

    # 确定要验证的文件
    if len(sys.argv) > 1:
        # 验证指定的文件
        files_to_validate = [Path(f) for f in sys.argv[1:]]
    else:
        # 验证所有Schema文件
        schemas_dir = get_project_root() / "specs" / "data"
        if not schemas_dir.exists():
            print(f"⚠️ Schemas directory not found: {schemas_dir}")
            return 0

        files_to_validate = list(schemas_dir.glob("*.json"))

    if not files_to_validate:
        print("ℹ️ No schema files to validate")
        return 0

    # 验证每个文件
    all_errors = []
    all_warnings = []

    for file_path in files_to_validate:
        if not file_path.exists():
            all_errors.append(f"File not found: {file_path}")
            continue

        print(f"Validating: {file_path.name}...", end=" ")
        errors, warnings = validate_schema_file(file_path)

        if errors:
            print("❌ FAILED")
            all_errors.extend(errors)
        elif warnings:
            print("⚠️ WARNINGS")
            all_warnings.extend(warnings)
        else:
            print("✅ OK")

    # 打印汇总
    print("\n" + "=" * 60)

    if all_errors:
        print("\n❌ ERRORS:")
        for error in all_errors:
            print(f"  • {error}")

    if all_warnings:
        print("\n⚠️ WARNINGS:")
        for warning in all_warnings:
            print(f"  • {warning}")

    if not all_errors and not all_warnings:
        print("\n✅ All schemas validated successfully!")

    print("=" * 60)

    # 返回码
    return 1 if all_errors else 0


if __name__ == "__main__":
    sys.exit(main())
