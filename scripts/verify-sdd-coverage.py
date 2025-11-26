#!/usr/bin/env python3
"""
SDD Coverage Verification Script
验证PRD需求到SDD规范的覆盖率

功能:
1. 提取PRD中定义的API端点和数据模型
2. 检查OpenAPI规范覆盖率
3. 检查JSON Schema覆盖率
4. 计算总覆盖率并与80%门禁比较
5. 生成覆盖率报告

用法:
  python scripts/verify-sdd-coverage.py [--report] [--threshold 80]

参数:
  --report    生成详细报告到docs/specs/sdd-coverage-report.md
  --threshold 覆盖率门禁值 (默认80)

返回码:
  0 - 覆盖率达标 (≥ threshold)
  1 - 覆盖率不达标

Reference: Section 16.5.1 of planning document
"""

import sys
import re
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional

# Set UTF-8 encoding for Windows console
import io
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


class SDDCoverageVerifier:
    """SDD覆盖率验证器"""

    def __init__(self, project_root: Path, threshold: int = 80):
        self.project_root = project_root
        self.threshold = threshold
        self.prd_dir = project_root / "docs" / "prd"
        self.specs_dir = project_root / "specs"
        self.arch_dir = project_root / "docs" / "architecture"

        # 收集的需求
        self.api_endpoints: List[Dict] = []
        self.data_models: List[Dict] = []

        # 覆盖率结果
        self.coverage_results: Dict = {
            'api': {'total': 0, 'covered': 0, 'missing': []},
            'schema': {'total': 0, 'covered': 0, 'missing': []},
            'overall': {'total': 0, 'covered': 0, 'percentage': 0.0}
        }

    def extract_api_endpoints_from_prd(self) -> List[Dict]:
        """从PRD/Epic文件中提取API端点定义"""
        endpoints = []

        # 检查多个可能的Epic文件位置
        epic_locations = [
            self.prd_dir / "epics" / "EPIC-15-FastAPI.md",
            self.prd_dir / "EPIC-15-FastAPI.md",
            self.prd_dir / "epics" / "EPIC-11-FastAPI.md",
            self.prd_dir / "EPIC-11-FASTAPI-BACKEND-DETAILED.md",
        ]

        for epic_file in epic_locations:
            if epic_file.exists():
                endpoints.extend(self._extract_endpoints_from_file(epic_file))

        return endpoints

    def _extract_endpoints_from_file(self, epic_file: Path) -> List[Dict]:
        """从单个Epic文件提取端点"""
        endpoints = []

        try:
            with open(epic_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception as e:
            print(f"Warning: Cannot read {epic_file}: {e}")
            return []

        in_api_section = False
        current_category = "Uncategorized"

        for line_num, line in enumerate(lines, 1):
            # 检测API章节开始
            if re.search(r'##\s*API\s*(Endpoints?|端点)', line, re.IGNORECASE):
                in_api_section = True
                continue

            # 检测章节结束 (二级标题，不含API)
            if in_api_section and line.startswith('## ') and 'API' not in line.upper():
                in_api_section = False
                continue

            if in_api_section:
                # 检测分类
                category_match = re.search(r'###\s+(.+?)(?:\s+\(\d+|$)', line)
                if category_match:
                    current_category = category_match.group(1).strip()
                    continue

                # 提取端点定义 - 多种格式
                # 格式1: - `METHOD /path` - 描述
                # 格式2: | METHOD | /path | 描述 |
                # 格式3: `METHOD /path`
                patterns = [
                    r'-\s+`(GET|POST|PUT|DELETE|PATCH)\s+([^`]+)`\s*[-:]?\s*(.+)?',
                    r'\|\s*(GET|POST|PUT|DELETE|PATCH)\s*\|\s*([^\|]+)\s*\|\s*([^\|]+)\s*\|',
                    r'`(GET|POST|PUT|DELETE|PATCH)\s+([^`]+)`',
                ]

                for pattern in patterns:
                    endpoint_match = re.search(pattern, line, re.IGNORECASE)
                    if endpoint_match:
                        method = endpoint_match.group(1).upper()
                        path = endpoint_match.group(2).strip()
                        description = endpoint_match.group(3).strip() if len(endpoint_match.groups()) > 2 and endpoint_match.group(3) else ""

                        endpoints.append({
                            'method': method,
                            'path': path,
                            'description': description,
                            'category': current_category,
                            'source_file': epic_file.name,
                            'source_line': line_num
                        })
                        break

        return endpoints

    def extract_data_models_from_prd(self) -> List[Dict]:
        """从PRD/Epic文件中提取数据模型定义"""
        models = []

        # 检查多个可能的Epic文件位置
        epic_locations = [
            self.prd_dir / "epics" / "EPIC-15-FastAPI.md",
            self.prd_dir / "EPIC-15-FastAPI.md",
            self.prd_dir / "epics" / "EPIC-11-FastAPI.md",
            self.arch_dir / "EPIC-11-DATA-MODELS.md",
        ]

        for epic_file in epic_locations:
            if epic_file.exists():
                models.extend(self._extract_models_from_file(epic_file))

        return models

    def _extract_models_from_file(self, file_path: Path) -> List[Dict]:
        """从单个文件提取数据模型"""
        models = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception as e:
            print(f"Warning: Cannot read {file_path}: {e}")
            return []

        in_model_section = False
        current_category = "Uncategorized"

        for line_num, line in enumerate(lines, 1):
            # 检测数据模型章节
            if re.search(r'##\s*(数据模型|Data\s*Models?)', line, re.IGNORECASE):
                in_model_section = True
                continue

            # 检测章节结束
            if in_model_section and line.startswith('## ') and '模型' not in line and 'Model' not in line:
                in_model_section = False
                continue

            if in_model_section:
                # 检测分类
                category_match = re.search(r'###?\s+\d*\.?\s*\**(.+?模型|.+?Models?)\**', line, re.IGNORECASE)
                if category_match:
                    current_category = category_match.group(1).strip()

                # 提取模型名称 (PascalCase格式)
                model_names = re.findall(r'`([A-Z][a-zA-Z0-9]+)`', line)
                for model_name in model_names:
                    # 过滤常见非模型名称
                    if model_name not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HTTP', 'JSON', 'UUID']:
                        models.append({
                            'name': model_name,
                            'category': current_category,
                            'source_file': file_path.name,
                            'source_line': line_num
                        })

        return models

    def check_openapi_coverage(self) -> Dict:
        """检查OpenAPI规范覆盖率"""
        openapi_files = list((self.specs_dir / "api").glob("*.yml")) + \
                        list((self.specs_dir / "api").glob("*.yaml"))

        if not openapi_files:
            return {'total': len(self.api_endpoints), 'covered': 0, 'missing': self.api_endpoints}

        # 读取所有OpenAPI内容
        openapi_content = ""
        for openapi_file in openapi_files:
            try:
                with open(openapi_file, 'r', encoding='utf-8') as f:
                    openapi_content += f.read() + "\n"
            except Exception as e:
                print(f"Warning: Cannot read {openapi_file}: {e}")

        covered = []
        missing = []

        for endpoint in self.api_endpoints:
            path = endpoint['path']
            method = endpoint['method'].lower()

            # 标准化路径 (处理参数占位符)
            normalized_path = re.sub(r'\{[^}]+\}', '{.*}', path)
            path_pattern = re.escape(path).replace(r'\{.*\}', r'\{[^}]+\}')

            # 检查路径是否存在
            if re.search(path_pattern, openapi_content) or path in openapi_content:
                # 检查方法是否定义
                path_idx = openapi_content.find(path) if path in openapi_content else -1
                if path_idx != -1:
                    section = openapi_content[path_idx:path_idx + 500]
                    if re.search(rf'^\s*{method}:', section, re.MULTILINE):
                        covered.append(endpoint)
                        continue

            missing.append(endpoint)

        return {
            'total': len(self.api_endpoints),
            'covered': len(covered),
            'missing': missing
        }

    def check_schema_coverage(self) -> Dict:
        """检查JSON Schema覆盖率"""
        schema_dir = self.specs_dir / "data"
        if not schema_dir.exists():
            return {'total': len(self.data_models), 'covered': 0, 'missing': self.data_models}

        schema_files = list(schema_dir.glob("*.schema.json"))
        schema_names = [f.stem.replace('.schema', '').lower().replace('-', '') for f in schema_files]

        covered = []
        missing = []

        for model in self.data_models:
            model_name = model['name']
            # 转换PascalCase到小写无分隔符
            normalized_name = re.sub(r'(?<!^)(?=[A-Z])', '', model_name).lower()

            if normalized_name in schema_names or model_name.lower() in schema_names:
                covered.append(model)
            else:
                # 也检查部分匹配
                partial_match = any(normalized_name in name or name in normalized_name for name in schema_names)
                if partial_match:
                    covered.append(model)
                else:
                    missing.append(model)

        return {
            'total': len(self.data_models),
            'covered': len(covered),
            'missing': missing
        }

    def calculate_overall_coverage(self) -> float:
        """计算总体覆盖率"""
        total = self.coverage_results['api']['total'] + self.coverage_results['schema']['total']
        covered = self.coverage_results['api']['covered'] + self.coverage_results['schema']['covered']

        if total == 0:
            return 100.0  # 无需求视为100%覆盖

        percentage = (covered / total) * 100
        self.coverage_results['overall'] = {
            'total': total,
            'covered': covered,
            'percentage': percentage
        }
        return percentage

    def verify(self) -> Tuple[bool, float]:
        """
        执行覆盖率验证

        Returns:
            (passed, coverage_percentage)
        """
        print("=" * 60)
        print("[VERIFY] SDD Coverage Verification")
        print("=" * 60)
        print(f"  Threshold: {self.threshold}%")
        print()

        # 1. 提取PRD需求
        print("[1/4] Extracting PRD requirements...")
        self.api_endpoints = self.extract_api_endpoints_from_prd()
        self.data_models = self.extract_data_models_from_prd()
        print(f"  Found {len(self.api_endpoints)} API endpoints")
        print(f"  Found {len(self.data_models)} data models")
        print()

        # 2. 检查OpenAPI覆盖率
        print("[2/4] Checking OpenAPI coverage...")
        self.coverage_results['api'] = self.check_openapi_coverage()
        api_pct = (self.coverage_results['api']['covered'] / self.coverage_results['api']['total'] * 100) \
            if self.coverage_results['api']['total'] > 0 else 100.0
        print(f"  OpenAPI: {self.coverage_results['api']['covered']}/{self.coverage_results['api']['total']} ({api_pct:.1f}%)")
        print()

        # 3. 检查Schema覆盖率
        print("[3/4] Checking JSON Schema coverage...")
        self.coverage_results['schema'] = self.check_schema_coverage()
        schema_pct = (self.coverage_results['schema']['covered'] / self.coverage_results['schema']['total'] * 100) \
            if self.coverage_results['schema']['total'] > 0 else 100.0
        print(f"  Schema: {self.coverage_results['schema']['covered']}/{self.coverage_results['schema']['total']} ({schema_pct:.1f}%)")
        print()

        # 4. 计算总体覆盖率
        print("[4/4] Calculating overall coverage...")
        overall_pct = self.calculate_overall_coverage()
        print(f"  Overall: {self.coverage_results['overall']['covered']}/{self.coverage_results['overall']['total']} ({overall_pct:.1f}%)")
        print()

        # 判断是否通过
        passed = overall_pct >= self.threshold

        # 打印结果
        print("=" * 60)
        if passed:
            print(f"[PASS] Coverage {overall_pct:.1f}% >= {self.threshold}% threshold")
        else:
            print(f"[FAIL] Coverage {overall_pct:.1f}% < {self.threshold}% threshold")

            # 列出缺失项
            if self.coverage_results['api']['missing']:
                print("\nMissing OpenAPI endpoints:")
                for ep in self.coverage_results['api']['missing'][:5]:
                    print(f"  - {ep['method']} {ep['path']}")
                if len(self.coverage_results['api']['missing']) > 5:
                    print(f"  ... and {len(self.coverage_results['api']['missing']) - 5} more")

            if self.coverage_results['schema']['missing']:
                print("\nMissing JSON Schemas:")
                for model in self.coverage_results['schema']['missing'][:5]:
                    print(f"  - {model['name']}")
                if len(self.coverage_results['schema']['missing']) > 5:
                    print(f"  ... and {len(self.coverage_results['schema']['missing']) - 5} more")

        print("=" * 60)

        return passed, overall_pct

    def generate_report(self, output_path: Optional[Path] = None) -> str:
        """生成详细覆盖率报告"""
        api_pct = (self.coverage_results['api']['covered'] / self.coverage_results['api']['total'] * 100) \
            if self.coverage_results['api']['total'] > 0 else 100.0
        schema_pct = (self.coverage_results['schema']['covered'] / self.coverage_results['schema']['total'] * 100) \
            if self.coverage_results['schema']['total'] > 0 else 100.0
        overall_pct = self.coverage_results['overall']['percentage']

        report = f"""# SDD Coverage Report

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Threshold**: {self.threshold}%
**Status**: {'PASS' if overall_pct >= self.threshold else 'FAIL'}

---

## Coverage Summary

| Category | Total | Covered | Percentage | Status |
|----------|-------|---------|------------|--------|
| API Endpoints | {self.coverage_results['api']['total']} | {self.coverage_results['api']['covered']} | {api_pct:.1f}% | {'PASS' if api_pct >= self.threshold else 'FAIL'} |
| Data Models | {self.coverage_results['schema']['total']} | {self.coverage_results['schema']['covered']} | {schema_pct:.1f}% | {'PASS' if schema_pct >= self.threshold else 'FAIL'} |
| **Overall** | **{self.coverage_results['overall']['total']}** | **{self.coverage_results['overall']['covered']}** | **{overall_pct:.1f}%** | **{'PASS' if overall_pct >= self.threshold else 'FAIL'}** |

---

## Missing API Endpoints ({len(self.coverage_results['api']['missing'])})

"""
        if self.coverage_results['api']['missing']:
            report += "| Method | Path | Description | Source |\n"
            report += "|--------|------|-------------|--------|\n"
            for ep in self.coverage_results['api']['missing']:
                report += f"| `{ep['method']}` | `{ep['path']}` | {ep.get('description', '-')} | {ep['source_file']}:L{ep['source_line']} |\n"
        else:
            report += "_All API endpoints are covered._\n"

        report += f"""
---

## Missing JSON Schemas ({len(self.coverage_results['schema']['missing'])})

"""
        if self.coverage_results['schema']['missing']:
            report += "| Model Name | Category | Source |\n"
            report += "|------------|----------|--------|\n"
            for model in self.coverage_results['schema']['missing']:
                kebab_name = re.sub(r'(?<!^)(?=[A-Z])', '-', model['name']).lower()
                report += f"| `{model['name']}` | {model['category']} | {model['source_file']}:L{model['source_line']} |\n"
        else:
            report += "_All data models have corresponding schemas._\n"

        report += """
---

## Recommendations

"""
        if overall_pct < self.threshold:
            report += f"Coverage is below the {self.threshold}% threshold. To improve:\n\n"

            if self.coverage_results['api']['missing']:
                report += "### OpenAPI Gaps\n\n"
                report += "Run the following to create missing endpoints:\n"
                report += "```bash\n"
                report += "@architect *create-openapi\n"
                report += "```\n\n"

            if self.coverage_results['schema']['missing']:
                report += "### JSON Schema Gaps\n\n"
                report += "Run the following to create missing schemas:\n"
                report += "```bash\n"
                report += "@architect *create-schemas\n"
                report += "```\n\n"
        else:
            report += "Coverage meets the threshold. No action required.\n"

        report += f"""
---

**Report generated by**: scripts/verify-sdd-coverage.py
**Reference**: Section 16.5.1 of planning document
"""

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"\nReport saved to: {output_path}")

        return report


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Verify SDD coverage against PRD requirements')
    parser.add_argument('--report', action='store_true', help='Generate detailed report')
    parser.add_argument('--threshold', type=int, default=80, help='Coverage threshold percentage (default: 80)')
    parser.add_argument('--output', type=str, help='Report output path (default: docs/specs/sdd-coverage-report.md)')

    args = parser.parse_args()

    # 项目根目录
    project_root = Path(__file__).parent.parent

    # 创建验证器并执行
    verifier = SDDCoverageVerifier(project_root, args.threshold)
    passed, coverage = verifier.verify()

    # 生成报告
    if args.report:
        output_path = Path(args.output) if args.output else project_root / "docs" / "specs" / "sdd-coverage-report.md"
        verifier.generate_report(output_path)

    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
