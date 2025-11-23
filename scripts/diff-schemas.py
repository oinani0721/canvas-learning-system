#!/usr/bin/env python3
"""
JSON Schema Diff Tool
比较两个JSON Schema版本，识别breaking vs non-breaking changes
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Set, Any

sys.path.insert(0, str(Path(__file__).parent / "lib"))

from planning_utils import (
    print_status,
    generate_markdown_report
)

class SchemaDiff:
    """JSON Schema差异分析器"""

    def __init__(self, schema1: Dict, schema2: Dict):
        self.schema1 = schema1
        self.schema2 = schema2
        self.breaking_changes: List[Dict] = []
        self.non_breaking_changes: List[Dict] = []
        self.info_changes: List[Dict] = []

    def add_breaking(self, message: str, details: Any = None):
        self.breaking_changes.append({"message": message, "details": details})

    def add_non_breaking(self, message: str, details: Any = None):
        self.non_breaking_changes.append({"message": message, "details": details})

    def add_info(self, message: str, details: Any = None):
        self.info_changes.append({"message": message, "details": details})

    def has_breaking_changes(self) -> bool:
        return len(self.breaking_changes) > 0

def compare_properties(diff: SchemaDiff, props1: Dict, props2: Dict, required1: Set, required2: Set, context: str = ""):
    """比较schema properties"""
    keys1 = set(props1.keys())
    keys2 = set(props2.keys())

    # 删除的字段
    removed = keys1 - keys2
    for field in removed:
        diff.add_breaking(f"Field removed: {context}{field}")

    # 新增的字段
    added = keys2 - keys1
    for field in added:
        if field in required2:
            diff.add_breaking(f"Required field added: {context}{field}")
        else:
            diff.add_non_breaking(f"Optional field added: {context}{field}")

    # 必填变更
    newly_required = required2 - required1
    for field in newly_required:
        if field in keys1:  # 已存在的字段变为必填
            diff.add_breaking(f"Field now required: {context}{field}")

    no_longer_required = required1 - required2
    for field in no_longer_required:
        if field in keys2:  # 仍存在但不再必填
            diff.add_non_breaking(f"Field no longer required: {context}{field}")

    # 类型变更
    common = keys1 & keys2
    for field in common:
        type1 = props1[field].get('type')
        type2 = props2[field].get('type')

        if type1 != type2:
            diff.add_breaking(f"Type changed: {context}{field} ({type1} → {type2})")

def diff_schemas(schema1: Dict, schema2: Dict) -> SchemaDiff:
    """比较两个JSON Schema"""
    diff = SchemaDiff(schema1, schema2)

    # 比较基本信息
    id1 = schema1.get('$id', schema1.get('id', ''))
    id2 = schema2.get('$id', schema2.get('id', ''))
    if id1 != id2:
        diff.add_info(f"Schema ID changed: {id1} → {id2}")

    # 比较properties
    props1 = schema1.get('properties', {})
    props2 = schema2.get('properties', {})
    required1 = set(schema1.get('required', []))
    required2 = set(schema2.get('required', []))

    compare_properties(diff, props1, props2, required1, required2)

    # 比较definitions/components
    defs1 = schema1.get('definitions', schema1.get('$defs', {}))
    defs2 = schema2.get('definitions', schema2.get('$defs', {}))

    for def_name in set(defs1.keys()) | set(defs2.keys()):
        if def_name in defs1 and def_name not in defs2:
            diff.add_info(f"Definition removed: {def_name}")
        elif def_name not in defs1 and def_name in defs2:
            diff.add_info(f"Definition added: {def_name}")

    return diff

def generate_diff_report(diff: SchemaDiff, schema1_path: Path, schema2_path: Path) -> str:
    """生成Markdown格式报告"""
    sections = []

    summary = f"""
**Schema 1**: `{schema1_path.name}`
**Schema 2**: `{schema2_path.name}`

**Breaking Changes**: {len(diff.breaking_changes)}
**Non-Breaking Changes**: {len(diff.non_breaking_changes)}
**Info Changes**: {len(diff.info_changes)}
"""
    sections.append({"title": "Summary", "content": summary})

    if diff.breaking_changes:
        content = "\n".join([f"❌ {c['message']}" for c in diff.breaking_changes])
        sections.append({"title": "⚠️ Breaking Changes", "content": content})

    if diff.non_breaking_changes:
        content = "\n".join([f"✅ {c['message']}" for c in diff.non_breaking_changes])
        sections.append({"title": "Non-Breaking Changes", "content": content})

    if diff.info_changes:
        content = "\n".join([f"ℹ️ {c['message']}" for c in diff.info_changes])
        sections.append({"title": "ℹ️ Informational Changes", "content": content})

    return generate_markdown_report("JSON Schema Diff Report", sections)

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Compare JSON Schemas and detect breaking changes"
    )
    parser.add_argument(
        '--base',
        type=str,
        help='Path to baseline snapshot JSON or schema file'
    )
    parser.add_argument(
        '--current',
        type=str,
        help='Path to current schemas directory or file'
    )
    parser.add_argument(
        'schema1',
        nargs='?',
        help='First schema file (legacy mode)'
    )
    parser.add_argument(
        'schema2',
        nargs='?',
        help='Second schema file (legacy mode)'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output file path'
    )
    parser.add_argument(
        '--fail-on-breaking',
        action='store_true',
        help='Exit with code 1 if breaking changes detected'
    )

    args = parser.parse_args()

    print("="*60)
    print("🔍 JSON Schema Diff")
    print("="*60)

    # 确定模式
    if args.base and args.current:
        base_path = Path(args.base)
        current_path = Path(args.current)

        if current_path.is_dir():
            current_schemas = list(current_path.glob("*.json"))
            if not current_schemas:
                print_status("No JSON schemas found in current directory", "error")
                return 1
            schema2_path = current_schemas[0]
        else:
            schema2_path = current_path

        # 从base确定对应的schema
        if base_path.suffix == '.json' and 'iteration' not in base_path.stem:
            schema1_path = base_path
        else:
            # 从snapshot加载
            with open(base_path, 'r', encoding='utf-8') as f:
                snapshot = json.load(f)
            schema_files = snapshot.get('files', {}).get('schemas', [])
            if not schema_files:
                print_status("No schemas in baseline", "warning")
                return 0
            schema1_path = Path(schema_files[0].get('path', ''))

    elif args.schema1 and args.schema2:
        schema1_path = Path(args.schema1)
        schema2_path = Path(args.schema2)
    else:
        parser.error("Provide --base and --current, or schema1 and schema2")

    # 加载schemas
    if not schema1_path.exists():
        print_status(f"Schema 1 not found: {schema1_path}", "error")
        return 1
    if not schema2_path.exists():
        print_status(f"Schema 2 not found: {schema2_path}", "error")
        return 1

    with open(schema1_path, 'r', encoding='utf-8') as f:
        schema1 = json.load(f)
    with open(schema2_path, 'r', encoding='utf-8') as f:
        schema2 = json.load(f)

    # 比较
    diff = diff_schemas(schema1, schema2)
    report = generate_diff_report(diff, schema1_path, schema2_path)

    if args.output:
        Path(args.output).write_text(report, encoding='utf-8')
        print_status(f"Report saved: {args.output}", "success")
    else:
        print("\n" + report)

    if diff.has_breaking_changes() and args.fail_on_breaking:
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
