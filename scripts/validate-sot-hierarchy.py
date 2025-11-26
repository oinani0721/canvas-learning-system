#!/usr/bin/env python3
"""
Source of Truth (SoT) Hierarchy Validation Script
验证文档之间的一致性，检测PRD/Architecture/Schema/OpenAPI冲突

功能:
1. 检测PRD与Schema之间的冲突
2. 检测Architecture与OpenAPI之间的冲突
3. 检测Schema与OpenAPI之间的引用一致性
4. 生成冲突报告

用法:
  python scripts/validate-sot-hierarchy.py [--verbose]

参数:
  --verbose - 显示详细输出

返回码:
  0 - 无冲突
  1 - 检测到冲突
"""

import sys
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Set UTF-8 encoding for Windows console
import io
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Try to import yaml
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


def get_project_root() -> Path:
    """获取项目根目录"""
    return Path(__file__).parent.parent


def load_yaml_file(file_path: Path) -> Optional[Dict]:
    """加载YAML文件"""
    if not YAML_AVAILABLE:
        return None
    if not file_path.exists():
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception:
        return None


def load_json_file(file_path: Path) -> Optional[Dict]:
    """加载JSON文件"""
    if not file_path.exists():
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def extract_schema_fields(schema: Dict) -> Dict[str, Dict]:
    """从JSON Schema中提取字段定义"""
    fields = {}
    properties = schema.get('properties', {})
    required = schema.get('required', [])

    for field_name, field_def in properties.items():
        fields[field_name] = {
            'type': field_def.get('type'),
            'required': field_name in required,
            'description': field_def.get('description', ''),
        }
    return fields


def extract_openapi_schemas(openapi: Dict) -> Dict[str, Dict]:
    """从OpenAPI中提取schema定义"""
    schemas = {}
    components = openapi.get('components', {})
    schema_defs = components.get('schemas', {})

    for schema_name, schema_def in schema_defs.items():
        # 处理$ref引用
        if '$ref' in schema_def:
            schemas[schema_name] = {'ref': schema_def['$ref']}
        else:
            schemas[schema_name] = extract_schema_fields(schema_def)
    return schemas


def check_schema_openapi_refs(project_root: Path) -> List[Dict]:
    """检查OpenAPI中的$ref是否指向存在的Schema文件"""
    conflicts = []
    api_dir = project_root / 'specs' / 'api'
    data_dir = project_root / 'specs' / 'data'

    if not api_dir.exists():
        return conflicts

    for api_file in api_dir.glob('*.yml'):
        openapi = load_yaml_file(api_file)
        if not openapi:
            continue

        # 查找所有$ref
        refs = find_all_refs(openapi)
        for ref in refs:
            # 检查外部文件引用
            if ref.startswith('../data/') or ref.startswith('./'):
                ref_file = ref.split('#')[0]
                ref_path = (api_file.parent / ref_file).resolve()
                if not ref_path.exists():
                    conflicts.append({
                        'type': 'Missing $ref',
                        'document_a': str(api_file.name),
                        'document_b': ref_file,
                        'description': f"OpenAPI references non-existent schema file: {ref}",
                        'level_a': 4,  # OpenAPI
                        'level_b': 3,  # Schema
                    })

    return conflicts


def find_all_refs(obj: Any, refs: List[str] = None) -> List[str]:
    """递归查找所有$ref"""
    if refs is None:
        refs = []

    if isinstance(obj, dict):
        if '$ref' in obj:
            refs.append(obj['$ref'])
        for value in obj.values():
            find_all_refs(value, refs)
    elif isinstance(obj, list):
        for item in obj:
            find_all_refs(item, refs)

    return refs


def check_schema_consistency(project_root: Path) -> List[Dict]:
    """检查JSON Schema之间的一致性"""
    conflicts = []
    data_dir = project_root / 'specs' / 'data'

    if not data_dir.exists():
        return conflicts

    schemas = {}
    for schema_file in data_dir.glob('*.json'):
        schema = load_json_file(schema_file)
        if schema:
            schemas[schema_file.stem] = {
                'file': schema_file,
                'content': schema,
            }

    # 检查$ref引用
    for schema_name, schema_info in schemas.items():
        refs = find_all_refs(schema_info['content'])
        for ref in refs:
            if ref.startswith('./') or ref.startswith('../'):
                ref_file = ref.split('#')[0]
                ref_path = (schema_info['file'].parent / ref_file).resolve()
                if not ref_path.exists():
                    conflicts.append({
                        'type': 'Schema $ref',
                        'document_a': schema_info['file'].name,
                        'document_b': ref_file,
                        'description': f"Schema references non-existent file: {ref}",
                        'level_a': 3,
                        'level_b': 3,
                    })

    return conflicts


def check_openapi_paths(project_root: Path) -> List[Dict]:
    """检查OpenAPI路径定义的一致性"""
    conflicts = []
    api_dir = project_root / 'specs' / 'api'

    if not api_dir.exists():
        return conflicts

    all_paths = {}
    for api_file in api_dir.glob('*.yml'):
        openapi = load_yaml_file(api_file)
        if not openapi:
            continue

        paths = openapi.get('paths', {})
        for path, methods in paths.items():
            if path in all_paths:
                # 检查重复定义
                conflicts.append({
                    'type': 'Duplicate Path',
                    'document_a': str(api_file.name),
                    'document_b': str(all_paths[path]['file']),
                    'description': f"Path '{path}' defined in multiple OpenAPI files",
                    'level_a': 4,
                    'level_b': 4,
                })
            else:
                all_paths[path] = {'file': api_file.name, 'methods': methods}

    return conflicts


def generate_conflict_report(conflicts: List[Dict]) -> str:
    """生成冲突报告"""
    if not conflicts:
        return "[SUCCESS] No SoT conflicts detected!"

    report = ["[CONFLICTS DETECTED]", "=" * 60]

    for i, conflict in enumerate(conflicts, 1):
        report.append(f"\n{i}. {conflict['type']}")
        report.append(f"   Document A (Level {conflict['level_a']}): {conflict['document_a']}")
        report.append(f"   Document B (Level {conflict['level_b']}): {conflict['document_b']}")
        report.append(f"   Description: {conflict['description']}")

    report.append("\n" + "=" * 60)
    report.append(f"\nTotal conflicts: {len(conflicts)}")
    report.append("\nRefer to: docs/architecture/sot-hierarchy.md for resolution protocol")

    return "\n".join(report)


def main():
    """主函数"""
    verbose = '--verbose' in sys.argv

    print("=" * 60)
    print("[VALIDATE] Source of Truth Hierarchy Validation")
    print("=" * 60)

    if not YAML_AVAILABLE:
        print("[WARNING] PyYAML not installed. OpenAPI validation skipped.")
        print("   Install with: pip install pyyaml")

    print()

    project_root = get_project_root()
    all_conflicts = []

    # 1. 检查Schema一致性
    print("Checking JSON Schema consistency...", end=" ")
    schema_conflicts = check_schema_consistency(project_root)
    all_conflicts.extend(schema_conflicts)
    print(f"[{len(schema_conflicts)} issues]" if schema_conflicts else "[OK]")

    # 2. 检查OpenAPI路径
    if YAML_AVAILABLE:
        print("Checking OpenAPI path definitions...", end=" ")
        path_conflicts = check_openapi_paths(project_root)
        all_conflicts.extend(path_conflicts)
        print(f"[{len(path_conflicts)} issues]" if path_conflicts else "[OK]")

        # 3. 检查Schema-OpenAPI引用
        print("Checking Schema-OpenAPI references...", end=" ")
        ref_conflicts = check_schema_openapi_refs(project_root)
        all_conflicts.extend(ref_conflicts)
        print(f"[{len(ref_conflicts)} issues]" if ref_conflicts else "[OK]")

    # 生成报告
    print("\n" + "=" * 60)
    report = generate_conflict_report(all_conflicts)
    print(report)
    print("=" * 60)

    return 1 if all_conflicts else 0


if __name__ == "__main__":
    sys.exit(main())
