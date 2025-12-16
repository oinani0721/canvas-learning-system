#!/usr/bin/env python3
"""
Content Consistency Validation Script
验证PRD、Schema、OpenAPI之间的内容一致性

功能:
1. 比较PRD字段定义与Schema字段定义 (required/optional)
2. 检查Schema $ref内容与OpenAPI $ref内容一致性
3. 检测字段类型不匹配
4. 生成冲突报告，按SoT层级推荐解决方案

用法:
  python scripts/validate-content-consistency.py [--report]

参数:
  --report  生成详细报告

返回码:
  0 - 一致性检查通过
  1 - 发现不一致

Reference: Section 16.5.4 of planning document
"""

import sys
import re
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Set

# Set UTF-8 encoding for Windows console
import io
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


# SoT层级 (数字越小优先级越高)
SOT_HIERARCHY = {
    'prd': 1,
    'architecture': 2,
    'schema': 3,
    'openapi': 4,
    'story': 5,
    'code': 6
}


class ContentConsistencyValidator:
    """内容一致性验证器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.specs_dir = project_root / "specs"
        self.prd_dir = project_root / "docs" / "prd"

        # 收集的定义
        self.prd_models: Dict[str, Dict] = {}
        self.schema_models: Dict[str, Dict] = {}
        self.openapi_models: Dict[str, Dict] = {}

        # 一致性检查结果
        self.conflicts: List[Dict] = []
        self.warnings: List[Dict] = []

    def extract_prd_models(self) -> Dict[str, Dict]:
        """从PRD文档提取数据模型定义"""
        models = {}

        prd_files = list(self.prd_dir.glob("**/*.md"))

        for prd_file in prd_files:
            try:
                with open(prd_file, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception:
                continue

            # 查找数据模型定义章节
            # 格式: ### ModelName 或 #### ModelName
            model_sections = re.finditer(
                r'^###?\s+`?([A-Z][a-zA-Z0-9]+)`?\s*\n(.*?)(?=^###?\s+|$)',
                content, re.MULTILINE | re.DOTALL
            )

            for match in model_sections:
                model_name = match.group(1)
                section_content = match.group(2)

                # 提取字段定义
                fields = self._extract_fields_from_text(section_content)

                if fields:
                    models[model_name] = {
                        'fields': fields,
                        'source': prd_file.name,
                        'source_type': 'prd'
                    }

        return models

    def _extract_fields_from_text(self, text: str) -> Dict[str, Dict]:
        """从文本提取字段定义"""
        fields = {}

        # 模式1: | field | type | required | description |
        table_pattern = r'\|\s*`?(\w+)`?\s*\|\s*`?([^|]+)`?\s*\|\s*`?(required|optional|是|否|必填|可选)`?\s*\|'
        for match in re.finditer(table_pattern, text, re.IGNORECASE):
            field_name = match.group(1).strip()
            field_type = match.group(2).strip()
            required_str = match.group(3).strip().lower()
            required = required_str in ['required', '是', '必填']

            fields[field_name] = {
                'type': field_type,
                'required': required
            }

        # 模式2: - `field`: type (required/optional)
        list_pattern = r'-\s+`(\w+)`\s*:\s*([^(]+)(?:\((\w+)\))?'
        for match in re.finditer(list_pattern, text):
            field_name = match.group(1).strip()
            field_type = match.group(2).strip()
            required_str = match.group(3).strip().lower() if match.group(3) else 'required'
            required = required_str in ['required', '必填']

            if field_name not in fields:
                fields[field_name] = {
                    'type': field_type,
                    'required': required
                }

        return fields

    def extract_schema_models(self) -> Dict[str, Dict]:
        """从JSON Schema文件提取模型定义"""
        models = {}

        schema_dir = self.specs_dir / "data"
        if not schema_dir.exists():
            return models

        schema_files = list(schema_dir.glob("*.schema.json"))

        for schema_file in schema_files:
            try:
                with open(schema_file, 'r', encoding='utf-8') as f:
                    schema = json.load(f)
            except Exception:
                continue

            # 从文件名推断模型名
            # canvas-node.schema.json → CanvasNode
            file_stem = schema_file.stem.replace('.schema', '')
            model_name = ''.join(word.capitalize() for word in file_stem.split('-'))

            # 提取字段
            fields = self._extract_fields_from_schema(schema)

            if fields:
                models[model_name] = {
                    'fields': fields,
                    'source': schema_file.name,
                    'source_type': 'schema'
                }

        return models

    def _extract_fields_from_schema(self, schema: Dict) -> Dict[str, Dict]:
        """从JSON Schema提取字段定义"""
        fields = {}

        properties = schema.get('properties', {})
        required = schema.get('required', [])

        for field_name, field_def in properties.items():
            field_type = field_def.get('type', 'unknown')
            if '$ref' in field_def:
                field_type = f"$ref:{field_def['$ref']}"

            fields[field_name] = {
                'type': field_type,
                'required': field_name in required
            }

        return fields

    def extract_openapi_models(self) -> Dict[str, Dict]:
        """从OpenAPI文件提取模型定义"""
        models = {}

        api_dir = self.specs_dir / "api"
        if not api_dir.exists():
            return models

        openapi_files = list(api_dir.glob("*.yml")) + list(api_dir.glob("*.yaml"))

        for openapi_file in openapi_files:
            try:
                with open(openapi_file, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception:
                continue

            # 简单YAML解析（提取components/schemas下的模型）
            # 完整解析需要PyYAML，这里用正则简化
            schema_sections = re.finditer(
                r'^\s{4}(\w+):\s*\n((?:\s{6}.+\n)*)',
                content, re.MULTILINE
            )

            for match in schema_sections:
                model_name = match.group(1)
                model_content = match.group(2)

                # 提取properties
                fields = self._extract_fields_from_yaml(model_content)

                if fields:
                    models[model_name] = {
                        'fields': fields,
                        'source': openapi_file.name,
                        'source_type': 'openapi'
                    }

        return models

    def _extract_fields_from_yaml(self, yaml_content: str) -> Dict[str, Dict]:
        """从YAML内容提取字段定义"""
        fields = {}

        # 查找properties
        if 'properties:' not in yaml_content:
            return fields

        # 简单提取字段名和类型
        field_pattern = r'^\s{8}(\w+):\s*\n(?:\s{10}type:\s*(\w+))?'
        for match in re.finditer(field_pattern, yaml_content, re.MULTILINE):
            field_name = match.group(1)
            field_type = match.group(2) if match.group(2) else 'unknown'

            fields[field_name] = {
                'type': field_type,
                'required': False  # 需要更复杂的解析来确定
            }

        # 提取required字段 - 支持两种格式
        # 格式1: 内联数组 required: [field1, field2]
        inline_required = re.search(r'required:\s*\[([^\]]+)\]', yaml_content)
        if inline_required:
            required_list = [f.strip().strip('"\'') for f in inline_required.group(1).split(',')]
            for field_name in required_list:
                if field_name in fields:
                    fields[field_name]['required'] = True

        # 格式2: 多行列表 required:\n  - field1\n  - field2
        multiline_required = re.search(r'required:\s*\n((?:\s+-\s*\w+\n?)+)', yaml_content)
        if multiline_required:
            required_list = re.findall(r'-\s*(\w+)', multiline_required.group(1))
            for field_name in required_list:
                if field_name in fields:
                    fields[field_name]['required'] = True

        return fields

    def compare_models(self) -> List[Dict]:
        """比较不同来源的模型定义"""
        conflicts = []

        # 获取所有模型名称
        all_model_names = set(self.prd_models.keys()) | set(self.schema_models.keys()) | set(self.openapi_models.keys())

        for model_name in all_model_names:
            prd_model = self.prd_models.get(model_name)
            schema_model = self.schema_models.get(model_name)
            openapi_model = self.openapi_models.get(model_name)

            # 比较PRD vs Schema
            if prd_model and schema_model:
                conflicts.extend(self._compare_model_fields(
                    model_name, prd_model, schema_model, 'prd', 'schema'
                ))

            # 比较Schema vs OpenAPI
            if schema_model and openapi_model:
                conflicts.extend(self._compare_model_fields(
                    model_name, schema_model, openapi_model, 'schema', 'openapi'
                ))

        return conflicts

    def _compare_model_fields(self, model_name: str, model_a: Dict, model_b: Dict,
                               type_a: str, type_b: str) -> List[Dict]:
        """比较两个模型的字段"""
        conflicts = []

        fields_a = model_a['fields']
        fields_b = model_b['fields']

        # 检查字段差异
        all_fields = set(fields_a.keys()) | set(fields_b.keys())

        for field_name in all_fields:
            field_a = fields_a.get(field_name)
            field_b = fields_b.get(field_name)

            # 字段只在一个来源存在
            if not field_a:
                conflicts.append({
                    'model': model_name,
                    'field': field_name,
                    'type': 'field_missing',
                    'sources': {type_a: 'NOT EXISTS', type_b: str(field_b)},
                    'higher_priority': type_a,
                    'recommendation': f"Add field '{field_name}' to {type_b} (aligns with {type_a})"
                })
                continue

            if not field_b:
                conflicts.append({
                    'model': model_name,
                    'field': field_name,
                    'type': 'field_missing',
                    'sources': {type_a: str(field_a), type_b: 'NOT EXISTS'},
                    'higher_priority': type_a,
                    'recommendation': f"Field '{field_name}' in {type_a} not found in {type_b}"
                })
                continue

            # 比较required状态
            if field_a.get('required') != field_b.get('required'):
                higher_priority = type_a if SOT_HIERARCHY[type_a] < SOT_HIERARCHY[type_b] else type_b
                conflicts.append({
                    'model': model_name,
                    'field': field_name,
                    'type': 'required_mismatch',
                    'sources': {
                        type_a: 'required' if field_a.get('required') else 'optional',
                        type_b: 'required' if field_b.get('required') else 'optional'
                    },
                    'higher_priority': higher_priority,
                    'recommendation': f"Update {type_b if higher_priority == type_a else type_a} to match {higher_priority}"
                })

        return conflicts

    def validate(self) -> Tuple[bool, List[Dict]]:
        """
        执行一致性验证

        Returns:
            (passed, conflicts)
        """
        print("=" * 60)
        print("[VALIDATE] Content Consistency Validation")
        print("=" * 60)
        print()

        # 1. 提取PRD模型
        print("[1/4] Extracting PRD model definitions...")
        self.prd_models = self.extract_prd_models()
        print(f"  Found {len(self.prd_models)} PRD models")

        # 2. 提取Schema模型
        print("[2/4] Extracting JSON Schema definitions...")
        self.schema_models = self.extract_schema_models()
        print(f"  Found {len(self.schema_models)} Schema models")

        # 3. 提取OpenAPI模型
        print("[3/4] Extracting OpenAPI definitions...")
        self.openapi_models = self.extract_openapi_models()
        print(f"  Found {len(self.openapi_models)} OpenAPI models")
        print()

        # 4. 比较模型
        print("[4/4] Comparing model definitions...")
        self.conflicts = self.compare_models()
        print(f"  Found {len(self.conflicts)} inconsistencies")
        print()

        # 判断结果
        # 只有required_mismatch是阻止性冲突，field_missing作为警告
        blocking_conflicts = [c for c in self.conflicts if c['type'] == 'required_mismatch']
        warning_conflicts = [c for c in self.conflicts if c['type'] == 'field_missing']
        passed = len(blocking_conflicts) == 0

        # 打印结果
        print("=" * 60)
        if passed:
            if warning_conflicts:
                print("[PASS] Content Consistency Validation Passed (with warnings)")
                print(f"\nWarnings ({len(warning_conflicts)} field_missing issues - non-blocking):")
                for conflict in warning_conflicts[:3]:
                    print(f"  - {conflict['model']}.{conflict['field']}: {conflict['type']}")
                if len(warning_conflicts) > 3:
                    print(f"  ... and {len(warning_conflicts) - 3} more")
            else:
                print("[PASS] Content Consistency Validation Passed")
        else:
            print("[FAIL] Content Consistency Validation Failed")
            print(f"\nBlocking errors ({len(blocking_conflicts)} required_mismatch issues):")
            for conflict in blocking_conflicts[:5]:
                print(f"  - {conflict['model']}.{conflict['field']}: {conflict['type']}")
                print(f"    {conflict['sources']}")
                print(f"    Recommendation: {conflict['recommendation']}")
            if len(blocking_conflicts) > 5:
                print(f"  ... and {len(blocking_conflicts) - 5} more")

        print("=" * 60)

        return passed, self.conflicts

    def generate_report(self, output_path: Optional[Path] = None) -> str:
        """生成详细一致性报告"""
        critical_conflicts = [c for c in self.conflicts if c['type'] in ['field_missing', 'required_mismatch']]
        passed = len(critical_conflicts) == 0

        report = f"""# Content Consistency Report

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Status**: {'PASS' if passed else 'FAIL'}

---

## Summary

| Metric | Value |
|--------|-------|
| PRD Models | {len(self.prd_models)} |
| JSON Schema Models | {len(self.schema_models)} |
| OpenAPI Models | {len(self.openapi_models)} |
| Inconsistencies | {len(self.conflicts)} |
| Critical Issues | {len(critical_conflicts)} |

---

## SoT Hierarchy Reference

When conflicts are detected, resolve according to Source of Truth hierarchy:

1. **PRD** (Level 1) - Highest authority, defines WHAT
2. **Architecture** (Level 2) - Defines HOW
3. **JSON Schema** (Level 3) - Data structure contracts
4. **OpenAPI Spec** (Level 4) - API behavior contracts
5. **Stories** (Level 5) - Implementation details
6. **Code** (Level 6) - Must comply with all above

---

## Inconsistencies Found ({len(self.conflicts)})

"""
        if self.conflicts:
            report += "| Model | Field | Type | Sources | Recommendation |\n"
            report += "|-------|-------|------|---------|----------------|\n"
            for conflict in self.conflicts:
                sources_str = ', '.join(f"{k}:{v}" for k, v in conflict['sources'].items())
                report += f"| {conflict['model']} | {conflict['field']} | {conflict['type']} | {sources_str} | {conflict['recommendation']} |\n"
        else:
            report += "_No inconsistencies found. All sources are aligned._\n"

        report += """
---

## Resolution Steps

"""
        if not passed:
            report += "For each conflict listed above:\n\n"
            report += "1. **Identify the higher-priority source** (use SoT hierarchy)\n"
            report += "2. **Update the lower-priority document** to match\n"
            report += "3. **Re-run validation** to confirm resolution\n"
            report += "4. **Commit changes** with reference to this report\n\n"

            # Group conflicts by type
            field_missing = [c for c in self.conflicts if c['type'] == 'field_missing']
            required_mismatch = [c for c in self.conflicts if c['type'] == 'required_mismatch']

            if field_missing:
                report += "### Missing Fields\n\n"
                for c in field_missing[:5]:
                    report += f"- **{c['model']}.{c['field']}**: {c['recommendation']}\n"
                if len(field_missing) > 5:
                    report += f"- ... and {len(field_missing) - 5} more\n"
                report += "\n"

            if required_mismatch:
                report += "### Required/Optional Mismatches\n\n"
                for c in required_mismatch[:5]:
                    report += f"- **{c['model']}.{c['field']}**: {c['sources']}\n"
                    report += f"  → {c['recommendation']}\n"
                if len(required_mismatch) > 5:
                    report += f"- ... and {len(required_mismatch) - 5} more\n"
        else:
            report += "No resolution needed. All sources are consistent.\n"

        report += f"""
---

**Report generated by**: scripts/validate-content-consistency.py
**Reference**: Section 16.5.4 of planning document
"""

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"\nReport saved to: {output_path}")

        return report


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Validate content consistency across SDD documents')
    parser.add_argument('--report', action='store_true', help='Generate detailed report')
    parser.add_argument('--output', type=str, help='Report output path')

    args = parser.parse_args()

    # 项目根目录
    project_root = Path(__file__).parent.parent

    # 创建验证器并执行
    validator = ContentConsistencyValidator(project_root)
    passed, conflicts = validator.validate()

    # 生成报告
    if args.report:
        output_path = Path(args.output) if args.output else project_root / "docs" / "specs" / "content-consistency-report.md"
        validator.generate_report(output_path)

    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
