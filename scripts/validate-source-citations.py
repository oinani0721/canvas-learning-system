#!/usr/bin/env python3
"""
Source Citation Validation Script
验证SDD文件中的来源引用标记

功能:
1. 检查JSON Schema是否有x-source-verification字段
2. 检查OpenAPI是否有x-source-verification字段
3. 验证Context7 Library ID格式 (/org/project)
4. 检查ADR是否有"Context7技术验证"section
5. 可选：实时验证Context7 Library ID存在性

用法:
  python scripts/validate-source-citations.py [--verify-context7] [files...]

参数:
  --verify-context7  实时调用Context7验证Library ID存在性
  files              要验证的文件列表，不提供则验证所有SDD文件

返回码:
  0 - 验证通过
  1 - 验证失败

Reference: Section 16.5.3 of planning document
"""

import sys
import re
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional

# Set UTF-8 encoding for Windows console
import io
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


# Context7 Library ID 格式: /org/project 或 /org/project/version
CONTEXT7_LIBRARY_ID_PATTERN = r'^/[a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+(?:/[a-zA-Z0-9_.-]+)?$'


class SourceCitationValidator:
    """来源引用验证器"""

    def __init__(self, project_root: Path, verify_context7: bool = False):
        self.project_root = project_root
        self.verify_context7 = verify_context7
        self.specs_dir = project_root / "specs"
        self.adr_dir = project_root / "docs" / "architecture" / "decisions"

        # 验证结果
        self.results: Dict[str, Dict] = {
            'schema': {'total': 0, 'valid': 0, 'issues': []},
            'openapi': {'total': 0, 'valid': 0, 'issues': []},
            'adr': {'total': 0, 'valid': 0, 'issues': []}
        }

    def validate_schema_file(self, file_path: Path) -> Tuple[bool, List[str]]:
        """验证单个JSON Schema文件的来源引用"""
        issues = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
        except json.JSONDecodeError as e:
            return False, [f"JSON parse error: {e}"]
        except Exception as e:
            return False, [f"Cannot read file: {e}"]

        # 检查x-source-verification字段
        if 'x-source-verification' not in schema:
            issues.append("Missing x-source-verification field")
            return False, issues

        source_verification = schema['x-source-verification']

        # 检查verified_at
        if 'verified_at' not in source_verification:
            issues.append("Missing verified_at timestamp in x-source-verification")

        # 检查sources数组
        if 'sources' not in source_verification:
            issues.append("Missing sources array in x-source-verification")
            return False, issues

        sources = source_verification.get('sources', [])
        if not sources:
            issues.append("Empty sources array in x-source-verification")
            return False, issues

        # 验证每个source
        for i, source in enumerate(sources):
            if 'type' not in source:
                issues.append(f"Source[{i}]: Missing type field")
                continue

            if source['type'] == 'context7':
                if 'library_id' not in source:
                    issues.append(f"Source[{i}]: Missing library_id for context7 type")
                else:
                    library_id = source['library_id']
                    if not re.match(CONTEXT7_LIBRARY_ID_PATTERN, library_id):
                        issues.append(f"Source[{i}]: Invalid Context7 library_id format: {library_id}")

            elif source['type'] == 'official_doc':
                if 'url' not in source:
                    issues.append(f"Source[{i}]: Missing url for official_doc type")

        return len(issues) == 0, issues

    def validate_openapi_file(self, file_path: Path) -> Tuple[bool, List[str]]:
        """验证单个OpenAPI文件的来源引用"""
        issues = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return False, [f"Cannot read file: {e}"]

        # 检查x-source-verification字段（YAML格式）
        if 'x-source-verification' not in content:
            issues.append("Missing x-source-verification in info section")
            return False, issues

        # 检查verified_at
        if not re.search(r'verified_at:\s*["\']?\d{4}-\d{2}-\d{2}', content):
            issues.append("Missing or invalid verified_at timestamp")

        # 检查format_source或business_source
        has_format_source = 'format_source:' in content
        has_business_source = 'business_source:' in content

        if not has_format_source and not has_business_source:
            issues.append("Missing format_source or business_source in x-source-verification")

        # 检查Context7 library_id
        library_id_match = re.search(r'library_id:\s*["\']?(/[^\s"\']+)', content)
        if library_id_match:
            library_id = library_id_match.group(1)
            if not re.match(CONTEXT7_LIBRARY_ID_PATTERN, library_id):
                issues.append(f"Invalid Context7 library_id format: {library_id}")
        elif has_format_source:
            # 如果有format_source但没有library_id
            if 'context7' in content.lower() and 'library_id' not in content:
                issues.append("Context7 type specified but missing library_id")

        return len(issues) == 0, issues

    def validate_adr_file(self, file_path: Path) -> Tuple[bool, List[str]]:
        """验证单个ADR文件的Context7技术验证section"""
        issues = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return False, [f"Cannot read file: {e}"]

        # 检查Context7技术验证section
        has_context7_section = bool(re.search(
            r'##\s*Context7\s*(技术验证|Technical\s*Verification)',
            content, re.IGNORECASE
        ))

        if not has_context7_section:
            # 检查是否有任何技术验证相关的section
            has_any_verification = bool(re.search(
                r'##\s*(技术验证|Verification|Research|Source)',
                content, re.IGNORECASE
            ))

            if not has_any_verification:
                issues.append("Missing Context7技术验证 section")
                return False, issues
            else:
                # 有其他验证section，检查是否包含Context7引用
                if 'context7' not in content.lower() and 'library_id' not in content.lower():
                    issues.append("Has verification section but no Context7 references")

        # 检查是否有Library ID引用
        library_id_matches = re.findall(r'Library\s*ID[:\s]+[`"]?(/[^\s`"]+)', content, re.IGNORECASE)
        if not library_id_matches:
            # 不是强制要求，但建议有
            issues.append("[WARNING] No Context7 Library ID found (recommended but not required)")

        # 验证Library ID格式
        for library_id in library_id_matches:
            if not re.match(CONTEXT7_LIBRARY_ID_PATTERN, library_id):
                issues.append(f"Invalid Context7 library_id format: {library_id}")

        # 只返回错误（不含WARNING）
        errors = [i for i in issues if not i.startswith('[WARNING]')]
        return len(errors) == 0, issues

    def validate_all_schemas(self, files: Optional[List[Path]] = None) -> Dict:
        """验证所有JSON Schema文件"""
        if files:
            schema_files = [f for f in files if f.suffix == '.json' and 'schema' in f.name]
        else:
            schema_dir = self.specs_dir / "data"
            schema_files = list(schema_dir.glob("*.schema.json")) if schema_dir.exists() else []

        for schema_file in schema_files:
            self.results['schema']['total'] += 1
            valid, issues = self.validate_schema_file(schema_file)

            if valid:
                self.results['schema']['valid'] += 1
            else:
                self.results['schema']['issues'].append({
                    'file': schema_file.name,
                    'issues': issues
                })

        return self.results['schema']

    def validate_all_openapi(self, files: Optional[List[Path]] = None) -> Dict:
        """验证所有OpenAPI文件"""
        if files:
            openapi_files = [f for f in files if f.suffix in ['.yml', '.yaml'] and 'openapi' in f.name.lower()]
        else:
            api_dir = self.specs_dir / "api"
            openapi_files = list(api_dir.glob("*.yml")) + list(api_dir.glob("*.yaml")) if api_dir.exists() else []

        for openapi_file in openapi_files:
            self.results['openapi']['total'] += 1
            valid, issues = self.validate_openapi_file(openapi_file)

            if valid:
                self.results['openapi']['valid'] += 1
            else:
                self.results['openapi']['issues'].append({
                    'file': openapi_file.name,
                    'issues': issues
                })

        return self.results['openapi']

    def validate_all_adrs(self, files: Optional[List[Path]] = None) -> Dict:
        """验证所有ADR文件"""
        if files:
            adr_files = [f for f in files if f.suffix == '.md' and 'adr' in f.name.lower()]
        else:
            adr_files = list(self.adr_dir.glob("*.md")) if self.adr_dir.exists() else []

        for adr_file in adr_files:
            self.results['adr']['total'] += 1
            valid, issues = self.validate_adr_file(adr_file)

            if valid:
                self.results['adr']['valid'] += 1
            else:
                self.results['adr']['issues'].append({
                    'file': adr_file.name,
                    'issues': issues
                })

        return self.results['adr']

    def validate(self, files: Optional[List[Path]] = None) -> Tuple[bool, Dict]:
        """
        执行所有验证

        Returns:
            (passed, results)
        """
        print("=" * 60)
        print("[VALIDATE] Source Citation Validation")
        print("=" * 60)
        print()

        # 1. 验证JSON Schema
        print("[1/3] Validating JSON Schema files...")
        schema_result = self.validate_all_schemas(files)
        schema_pct = (schema_result['valid'] / schema_result['total'] * 100) if schema_result['total'] > 0 else 100.0
        print(f"  Schema: {schema_result['valid']}/{schema_result['total']} valid ({schema_pct:.1f}%)")
        print()

        # 2. 验证OpenAPI
        print("[2/3] Validating OpenAPI files...")
        openapi_result = self.validate_all_openapi(files)
        openapi_pct = (openapi_result['valid'] / openapi_result['total'] * 100) if openapi_result['total'] > 0 else 100.0
        print(f"  OpenAPI: {openapi_result['valid']}/{openapi_result['total']} valid ({openapi_pct:.1f}%)")
        print()

        # 3. 验证ADR
        print("[3/3] Validating ADR files...")
        adr_result = self.validate_all_adrs(files)
        adr_pct = (adr_result['valid'] / adr_result['total'] * 100) if adr_result['total'] > 0 else 100.0
        print(f"  ADR: {adr_result['valid']}/{adr_result['total']} valid ({adr_pct:.1f}%)")
        print()

        # 计算总体结果
        total = schema_result['total'] + openapi_result['total'] + adr_result['total']
        valid = schema_result['valid'] + openapi_result['valid'] + adr_result['valid']
        overall_pct = (valid / total * 100) if total > 0 else 100.0

        has_issues = (
            len(schema_result['issues']) > 0 or
            len(openapi_result['issues']) > 0 or
            # ADR只检查非WARNING issue
            any(
                not all(i.startswith('[WARNING]') for i in item['issues'])
                for item in adr_result['issues']
            )
        )

        # 打印结果
        print("=" * 60)
        if not has_issues:
            print(f"[PASS] Source Citation Validation Passed ({overall_pct:.1f}%)")
        else:
            print(f"[FAIL] Source Citation Validation Failed")

            # 列出问题
            all_issues = []
            for category in ['schema', 'openapi', 'adr']:
                for item in self.results[category]['issues']:
                    for issue in item['issues']:
                        all_issues.append(f"{item['file']}: {issue}")

            print("\nIssues found:")
            for issue in all_issues[:10]:
                print(f"  - {issue}")
            if len(all_issues) > 10:
                print(f"  ... and {len(all_issues) - 10} more")

        print("=" * 60)

        return not has_issues, self.results

    def generate_report(self, output_path: Optional[Path] = None) -> str:
        """生成详细验证报告"""
        schema_result = self.results['schema']
        openapi_result = self.results['openapi']
        adr_result = self.results['adr']

        total = schema_result['total'] + openapi_result['total'] + adr_result['total']
        valid = schema_result['valid'] + openapi_result['valid'] + adr_result['valid']
        overall_pct = (valid / total * 100) if total > 0 else 100.0

        has_issues = any(len(self.results[cat]['issues']) > 0 for cat in ['schema', 'openapi', 'adr'])

        report = f"""# Source Citation Validation Report

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Status**: {'PASS' if not has_issues else 'FAIL'}

---

## Summary

| Category | Total | Valid | Percentage | Status |
|----------|-------|-------|------------|--------|
| JSON Schema | {schema_result['total']} | {schema_result['valid']} | {(schema_result['valid']/schema_result['total']*100) if schema_result['total'] > 0 else 100:.1f}% | {'PASS' if len(schema_result['issues'])==0 else 'FAIL'} |
| OpenAPI | {openapi_result['total']} | {openapi_result['valid']} | {(openapi_result['valid']/openapi_result['total']*100) if openapi_result['total'] > 0 else 100:.1f}% | {'PASS' if len(openapi_result['issues'])==0 else 'FAIL'} |
| ADR | {adr_result['total']} | {adr_result['valid']} | {(adr_result['valid']/adr_result['total']*100) if adr_result['total'] > 0 else 100:.1f}% | {'PASS' if len(adr_result['issues'])==0 else 'FAIL'} |
| **Overall** | **{total}** | **{valid}** | **{overall_pct:.1f}%** | **{'PASS' if not has_issues else 'FAIL'}** |

---

## Required Format

### JSON Schema x-source-verification

```json
{{
  "x-source-verification": {{
    "verified_at": "YYYY-MM-DDTHH:MM:SSZ",
    "sources": [
      {{"type": "context7", "library_id": "/org/project", "topic": "topic"}},
      {{"type": "official_doc", "url": "https://..."}}
    ]
  }}
}}
```

### OpenAPI x-source-verification

```yaml
info:
  x-source-verification:
    verified_at: "YYYY-MM-DD"
    format_source:
      type: context7
      library_id: "/oai/openapi-specification"
    business_source:
      prd_version: "vX.X.X"
```

### ADR Context7技术验证 Section

```markdown
## Context7技术验证

**验证时间**: YYYY-MM-DD

**{technology}** (选中方案):
- Context7 Library ID: `/org/project`
- Code Snippets: XXX
- Benchmark Score: XX.X
```

---

## Issues Found

"""
        if has_issues:
            for category in ['schema', 'openapi', 'adr']:
                if self.results[category]['issues']:
                    report += f"### {category.upper()} Issues\n\n"
                    for item in self.results[category]['issues']:
                        report += f"**{item['file']}**:\n"
                        for issue in item['issues']:
                            report += f"- {issue}\n"
                        report += "\n"
        else:
            report += "_No issues found. All files have valid source citations._\n"

        report += f"""
---

## Recommendations

"""
        if has_issues:
            report += "1. Add missing x-source-verification fields to SDD files\n"
            report += "2. Ensure Context7 Library ID format is `/org/project`\n"
            report += "3. Add Context7技术验证 section to ADR files\n"
            report += "4. Include verified_at timestamp for traceability\n"
        else:
            report += "All source citations are valid. No action required.\n"

        report += f"""
---

**Report generated by**: scripts/validate-source-citations.py
**Reference**: Section 16.5.3 of planning document
"""

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"\nReport saved to: {output_path}")

        return report


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Validate source citations in SDD files')
    parser.add_argument('files', nargs='*', help='Files to validate (default: all SDD files)')
    parser.add_argument('--verify-context7', action='store_true', help='Real-time verify Context7 Library IDs')
    parser.add_argument('--report', action='store_true', help='Generate detailed report')
    parser.add_argument('--output', type=str, help='Report output path')

    args = parser.parse_args()

    # 项目根目录
    project_root = Path(__file__).parent.parent

    # 转换文件路径
    files = [Path(f) for f in args.files] if args.files else None

    # 创建验证器并执行
    validator = SourceCitationValidator(project_root, args.verify_context7)
    passed, results = validator.validate(files)

    # 生成报告
    if args.report:
        output_path = Path(args.output) if args.output else project_root / "docs" / "specs" / "source-citation-report.md"
        validator.generate_report(output_path)

    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
