#!/usr/bin/env python3
"""
OpenAPI Specification Diff Tool
比较两个OpenAPI spec版本，识别breaking vs non-breaking changes
"""

import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any

sys.path.insert(0, str(Path(__file__).parent / "lib"))

from planning_utils import (
    read_openapi_spec,
    get_openapi_version,
    print_status,
    generate_markdown_report
)

# ========================================
# OpenAPI Diff类定义
# ========================================

class OpenAPIDiff:
    """OpenAPI规格差异分析器"""

    def __init__(self, spec1: Dict, spec2: Dict):
        self.spec1 = spec1
        self.spec2 = spec2
        self.breaking_changes: List[Dict] = []
        self.non_breaking_changes: List[Dict] = []
        self.info_changes: List[Dict] = []

    def add_breaking(self, category: str, message: str, details: Any = None):
        """添加breaking change"""
        self.breaking_changes.append({
            "category": category,
            "message": message,
            "details": details
        })

    def add_non_breaking(self, category: str, message: str, details: Any = None):
        """添加non-breaking change"""
        self.non_breaking_changes.append({
            "category": category,
            "message": message,
            "details": details
        })

    def add_info(self, category: str, message: str, details: Any = None):
        """添加info change"""
        self.info_changes.append({
            "category": category,
            "message": message,
            "details": details
        })

    def has_breaking_changes(self) -> bool:
        return len(self.breaking_changes) > 0

# ========================================
# 差异检测函数
# ========================================

def compare_endpoints(diff: OpenAPIDiff, paths1: Dict, paths2: Dict):
    """比较API endpoints"""
    endpoints1 = set(paths1.keys())
    endpoints2 = set(paths2.keys())

    # 删除的endpoints (BREAKING)
    removed_endpoints = endpoints1 - endpoints2
    for endpoint in removed_endpoints:
        methods = list(paths1[endpoint].keys())
        diff.add_breaking(
            "Endpoint Deletion",
            f"Endpoint removed: {endpoint}",
            {"methods": methods}
        )

    # 新增的endpoints (NON-BREAKING)
    added_endpoints = endpoints2 - endpoints1
    for endpoint in added_endpoints:
        methods = list(paths2[endpoint].keys())
        diff.add_non_breaking(
            "Endpoint Addition",
            f"New endpoint added: {endpoint}",
            {"methods": methods}
        )

    # 修改的endpoints
    common_endpoints = endpoints1 & endpoints2
    for endpoint in common_endpoints:
        compare_endpoint_methods(diff, endpoint, paths1[endpoint], paths2[endpoint])

def compare_endpoint_methods(diff: OpenAPIDiff, endpoint: str, methods1: Dict, methods2: Dict):
    """比较单个endpoint的HTTP methods"""
    http_methods1 = set(k for k in methods1.keys() if k in ['get', 'post', 'put', 'patch', 'delete'])
    http_methods2 = set(k for k in methods2.keys() if k in ['get', 'post', 'put', 'patch', 'delete'])

    # 删除的methods (BREAKING)
    removed_methods = http_methods1 - http_methods2
    for method in removed_methods:
        diff.add_breaking(
            "Method Deletion",
            f"Method removed: {method.upper()} {endpoint}",
            None
        )

    # 新增的methods (NON-BREAKING)
    added_methods = http_methods2 - http_methods1
    for method in added_methods:
        diff.add_non_breaking(
            "Method Addition",
            f"New method added: {method.upper()} {endpoint}",
            None
        )

    # 比较共同methods的请求/响应schema
    common_methods = http_methods1 & http_methods2
    for method in common_methods:
        compare_operation(diff, endpoint, method, methods1[method], methods2[method])

def compare_operation(diff: OpenAPIDiff, endpoint: str, method: str, op1: Dict, op2: Dict):
    """比较单个operation的变更"""
    operation_id = f"{method.upper()} {endpoint}"

    # 比较requestBody
    req1 = op1.get('requestBody', {})
    req2 = op2.get('requestBody', {})

    if req1 and not req2:
        diff.add_breaking(
            "Request Body Removal",
            f"Request body removed: {operation_id}",
            None
        )
    elif not req1 and req2:
        diff.add_breaking(
            "Request Body Addition",
            f"Request body now required: {operation_id}",
            None
        )
    elif req1 and req2:
        compare_request_body(diff, operation_id, req1, req2)

    # 比较responses
    responses1 = op1.get('responses', {})
    responses2 = op2.get('responses', {})
    compare_responses(diff, operation_id, responses1, responses2)

    # 比较parameters
    params1 = op1.get('parameters', [])
    params2 = op2.get('parameters', [])
    compare_parameters(diff, operation_id, params1, params2)

def compare_request_body(diff: OpenAPIDiff, operation_id: str, req1: Dict, req2: Dict):
    """比较requestBody schema"""
    # 检查required字段变更
    required1 = req1.get('required', False)
    required2 = req2.get('required', False)

    if not required1 and required2:
        diff.add_breaking(
            "Request Body Required",
            f"Request body now required: {operation_id}",
            None
        )
    elif required1 and not required2:
        diff.add_non_breaking(
            "Request Body Optional",
            f"Request body now optional: {operation_id}",
            None
        )

    # 比较content schema
    content1 = req1.get('content', {}).get('application/json', {}).get('schema', {})
    content2 = req2.get('content', {}).get('application/json', {}).get('schema', {})

    if content1 and content2:
        compare_schemas(diff, f"{operation_id} [Request]", content1, content2)

def compare_responses(diff: OpenAPIDiff, operation_id: str, responses1: Dict, responses2: Dict):
    """比较response schemas"""
    status_codes1 = set(responses1.keys())
    status_codes2 = set(responses2.keys())

    # 删除的响应码 (BREAKING)
    removed_codes = status_codes1 - status_codes2
    for code in removed_codes:
        diff.add_breaking(
            "Response Code Removal",
            f"Response {code} removed: {operation_id}",
            None
        )

    # 新增的响应码 (NON-BREAKING)
    added_codes = status_codes2 - status_codes1
    for code in added_codes:
        diff.add_non_breaking(
            "Response Code Addition",
            f"Response {code} added: {operation_id}",
            None
        )

    # 比较共同响应码的schema
    common_codes = status_codes1 & status_codes2
    for code in common_codes:
        schema1 = responses1[code].get('content', {}).get('application/json', {}).get('schema', {})
        schema2 = responses2[code].get('content', {}).get('application/json', {}).get('schema', {})

        if schema1 and schema2:
            compare_schemas(diff, f"{operation_id} [Response {code}]", schema1, schema2)

def compare_parameters(diff: OpenAPIDiff, operation_id: str, params1: List, params2: List):
    """比较parameters"""
    # 按name和in组成的key分组
    params1_map = {(p.get('name'), p.get('in')): p for p in params1}
    params2_map = {(p.get('name'), p.get('in')): p for p in params2}

    keys1 = set(params1_map.keys())
    keys2 = set(params2_map.keys())

    # 删除的参数
    removed_params = keys1 - keys2
    for key in removed_params:
        param = params1_map[key]
        if param.get('required', False):
            diff.add_breaking(
                "Required Parameter Removal",
                f"Required parameter removed: {key[0]} ({key[1]})",
                {"operation": operation_id}
            )
        else:
            diff.add_non_breaking(
                "Optional Parameter Removal",
                f"Optional parameter removed: {key[0]} ({key[1]})",
                {"operation": operation_id}
            )

    # 新增的参数
    added_params = keys2 - keys1
    for key in added_params:
        param = params2_map[key]
        if param.get('required', False):
            diff.add_breaking(
                "Required Parameter Addition",
                f"New required parameter added: {key[0]} ({key[1]})",
                {"operation": operation_id}
            )
        else:
            diff.add_non_breaking(
                "Optional Parameter Addition",
                f"New optional parameter added: {key[0]} ({key[1]})",
                {"operation": operation_id}
            )

    # 参数required属性变更
    common_params = keys1 & keys2
    for key in common_params:
        param1 = params1_map[key]
        param2 = params2_map[key]

        required1 = param1.get('required', False)
        required2 = param2.get('required', False)

        if not required1 and required2:
            diff.add_breaking(
                "Parameter Now Required",
                f"Parameter now required: {key[0]} ({key[1]})",
                {"operation": operation_id}
            )
        elif required1 and not required2:
            diff.add_non_breaking(
                "Parameter Now Optional",
                f"Parameter now optional: {key[0]} ({key[1]})",
                {"operation": operation_id}
            )

def compare_schemas(diff: OpenAPIDiff, context: str, schema1: Dict, schema2: Dict):
    """比较JSON schema定义"""
    # 处理$ref引用（简化处理）
    if '$ref' in schema1 or '$ref' in schema2:
        if schema1.get('$ref') != schema2.get('$ref'):
            diff.add_info(
                "Schema Reference Change",
                f"Schema reference changed: {context}",
                {"from": schema1.get('$ref'), "to": schema2.get('$ref')}
            )
        return

    # 比较required字段
    required1 = set(schema1.get('required', []))
    required2 = set(schema2.get('required', []))

    newly_required = required2 - required1
    if newly_required:
        diff.add_breaking(
            "Required Fields Addition",
            f"New required fields: {context}",
            {"fields": list(newly_required)}
        )

    no_longer_required = required1 - required2
    if no_longer_required:
        diff.add_non_breaking(
            "Required Fields Removal",
            f"Fields no longer required: {context}",
            {"fields": list(no_longer_required)}
        )

    # 比较properties
    props1 = schema1.get('properties', {})
    props2 = schema2.get('properties', {})

    fields1 = set(props1.keys())
    fields2 = set(props2.keys())

    # 删除的字段 (BREAKING if in response)
    removed_fields = fields1 - fields2
    if removed_fields:
        if 'Response' in context:
            diff.add_breaking(
                "Response Field Removal",
                f"Response fields removed: {context}",
                {"fields": list(removed_fields)}
            )
        else:
            diff.add_non_breaking(
                "Request Field Removal",
                f"Request fields removed: {context}",
                {"fields": list(removed_fields)}
            )

    # 新增的字段 (NON-BREAKING if not required)
    added_fields = fields2 - fields1
    if added_fields:
        new_required = added_fields & required2
        if new_required:
            diff.add_breaking(
                "Required Field Addition",
                f"New required fields added: {context}",
                {"fields": list(new_required)}
            )

        new_optional = added_fields - required2
        if new_optional:
            diff.add_non_breaking(
                "Optional Field Addition",
                f"New optional fields added: {context}",
                {"fields": list(new_optional)}
            )

def compare_components(diff: OpenAPIDiff, components1: Dict, components2: Dict):
    """比较components/schemas定义"""
    schemas1 = components1.get('schemas', {})
    schemas2 = components2.get('schemas', {})

    schema_names1 = set(schemas1.keys())
    schema_names2 = set(schemas2.keys())

    # 删除的schemas (可能是BREAKING)
    removed_schemas = schema_names1 - schema_names2
    if removed_schemas:
        diff.add_info(
            "Schema Removal",
            f"Schemas removed from components",
            {"schemas": list(removed_schemas)}
        )

    # 新增的schemas (NON-BREAKING)
    added_schemas = schema_names2 - schema_names1
    if added_schemas:
        diff.add_info(
            "Schema Addition",
            f"New schemas added to components",
            {"schemas": list(added_schemas)}
        )

def compare_info(diff: OpenAPIDiff, info1: Dict, info2: Dict):
    """比较基本信息"""
    version1 = info1.get('version', 'unknown')
    version2 = info2.get('version', 'unknown')

    if version1 != version2:
        diff.add_info(
            "Version Change",
            f"Version updated: {version1} → {version2}",
            None
        )

    title1 = info1.get('title', '')
    title2 = info2.get('title', '')

    if title1 != title2:
        diff.add_info(
            "Title Change",
            f"API title changed: {title1} → {title2}",
            None
        )

# ========================================
# 主diff函数
# ========================================

def diff_openapi_specs(spec1: Dict, spec2: Dict) -> OpenAPIDiff:
    """
    比较两个OpenAPI规格

    Args:
        spec1: 旧版本OpenAPI规格
        spec2: 新版本OpenAPI规格

    Returns:
        OpenAPIDiff对象
    """
    diff = OpenAPIDiff(spec1, spec2)

    # 比较info
    compare_info(diff, spec1.get('info', {}), spec2.get('info', {}))

    # 比较endpoints
    compare_endpoints(diff, spec1.get('paths', {}), spec2.get('paths', {}))

    # 比较components
    compare_components(diff, spec1.get('components', {}), spec2.get('components', {}))

    return diff

# ========================================
# 报告生成
# ========================================

def generate_diff_report(diff: OpenAPIDiff, spec1_path: Path, spec2_path: Path) -> str:
    """生成Markdown格式的diff报告"""

    sections = []

    # 概要
    summary_content = f"""
**Spec 1**: `{spec1_path.name}`
**Spec 2**: `{spec2_path.name}`

**Breaking Changes**: {len(diff.breaking_changes)}
**Non-Breaking Changes**: {len(diff.non_breaking_changes)}
**Info Changes**: {len(diff.info_changes)}
"""
    sections.append({"title": "Summary", "content": summary_content})

    # Breaking Changes
    if diff.breaking_changes:
        breaking_content = ""
        for change in diff.breaking_changes:
            breaking_content += f"### {change['category']}\n\n"
            breaking_content += f"❌ **{change['message']}**\n\n"
            if change['details']:
                breaking_content += f"```\n{change['details']}\n```\n\n"

        sections.append({"title": "⚠️ Breaking Changes", "content": breaking_content})

    # Non-Breaking Changes
    if diff.non_breaking_changes:
        non_breaking_content = ""
        for change in diff.non_breaking_changes:
            non_breaking_content += f"### {change['category']}\n\n"
            non_breaking_content += f"✅ **{change['message']}**\n\n"
            if change['details']:
                non_breaking_content += f"```\n{change['details']}\n```\n\n"

        sections.append({"title": "Non-Breaking Changes", "content": non_breaking_content})

    # Info Changes
    if diff.info_changes:
        info_content = ""
        for change in diff.info_changes:
            info_content += f"### {change['category']}\n\n"
            info_content += f"ℹ️ **{change['message']}**\n\n"
            if change['details']:
                info_content += f"```\n{change['details']}\n```\n\n"

        sections.append({"title": "ℹ️ Informational Changes", "content": info_content})

    # 迁移建议
    if diff.breaking_changes:
        migration_content = """
Breaking changes detected! Please take the following actions:

1. **Review all breaking changes** listed above
2. **Update API consumers** to handle removed endpoints/fields
3. **Increment major version** (e.g., 1.x.x → 2.0.0)
4. **Document migration path** in CHANGELOG.md
5. **Notify all stakeholders** before deploying

**Recommended Version Increment**: MAJOR (X.0.0)
"""
    elif diff.non_breaking_changes:
        migration_content = """
No breaking changes detected. Safe to deploy with minor version increment.

**Recommended Version Increment**: MINOR (x.Y.0)
"""
    else:
        migration_content = """
No changes detected or only informational changes.

**Recommended Version Increment**: PATCH (x.y.Z) or no change
"""

    sections.append({"title": "Migration Guide", "content": migration_content})

    return generate_markdown_report("OpenAPI Specification Diff Report", sections)

# ========================================
# CLI接口
# ========================================

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Compare two OpenAPI specifications and detect breaking changes"
    )

    # 新参数接口 (匹配 Task 文件)
    parser.add_argument(
        '--base',
        type=str,
        help='Path to baseline snapshot JSON file (iterations/iteration-N.json)'
    )
    parser.add_argument(
        '--current',
        type=str,
        help='Path to current specs directory (specs/api/)'
    )

    # 保留旧参数接口以保持兼容性
    parser.add_argument(
        'spec1',
        nargs='?',
        type=str,
        help='Path to first OpenAPI spec (older version) - legacy mode'
    )
    parser.add_argument(
        'spec2',
        nargs='?',
        type=str,
        help='Path to second OpenAPI spec (newer version) - legacy mode'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output file path for diff report (default: print to stdout)'
    )
    parser.add_argument(
        '--fail-on-breaking',
        action='store_true',
        help='Exit with code 1 if breaking changes detected'
    )

    args = parser.parse_args()

    # 确定使用哪种模式
    if args.base and args.current:
        # 新模式: 从snapshot和目录加载
        import json

        base_path = Path(args.base)
        current_dir = Path(args.current)

        if not base_path.exists():
            print_status(f"Baseline snapshot not found: {base_path}", "error")
            return 1

        if not current_dir.exists():
            print_status(f"Current specs directory not found: {current_dir}", "error")
            return 1

        # 从snapshot加载旧版本spec信息
        with open(base_path, 'r', encoding='utf-8') as f:
            snapshot = json.load(f)

        # 获取snapshot中的OpenAPI spec
        openapi_files = snapshot.get('files', {}).get('openapi', [])
        if not openapi_files:
            print_status("No OpenAPI specs found in baseline snapshot", "warning")
            return 0

        # 找到当前目录中对应的spec文件
        current_specs = list(current_dir.glob('*.yml')) + list(current_dir.glob('*.yaml'))
        if not current_specs:
            print_status(f"No OpenAPI specs found in: {current_dir}", "error")
            return 1

        # 使用第一个找到的spec进行比较
        spec1_path = Path(openapi_files[0].get('path', ''))
        spec2_path = current_specs[0]

        if not spec1_path.exists():
            # 如果旧spec文件不存在，尝试从snapshot数据重建或跳过
            print_status(f"Baseline spec file not found: {spec1_path}", "warning")
            print_status("Comparing against empty baseline", "info")
            spec1_path = None
    elif args.spec1 and args.spec2:
        # 旧模式: 直接指定两个spec文件
        spec1_path = Path(args.spec1)
        spec2_path = Path(args.spec2)
    else:
        parser.error("Either use --base and --current, or provide spec1 and spec2 arguments")

    # 验证文件存在（新模式中spec1_path可能为None）
    if spec1_path is not None and not spec1_path.exists():
        print_status(f"Spec 1 not found: {spec1_path}", "error")
        return 1

    if not spec2_path.exists():
        print_status(f"Spec 2 not found: {spec2_path}", "error")
        return 1

    print("="*60)
    print("🔍 OpenAPI Specification Diff")
    print("="*60)

    print_status(f"Loading specs...", "progress")
    try:
        if spec1_path is None:
            # 空baseline：创建空spec用于比较
            spec1 = {"openapi": "3.0.0", "info": {"title": "Empty", "version": "0.0.0"}, "paths": {}}
        else:
            spec1 = read_openapi_spec(spec1_path)
        spec2 = read_openapi_spec(spec2_path)
    except Exception as e:
        print_status(f"Failed to load specs: {e}", "error")
        return 1

    print_status(f"Comparing specs...", "progress")
    diff = diff_openapi_specs(spec1, spec2)

    # 生成报告
    report_spec1_path = spec1_path if spec1_path else Path("(empty baseline)")
    report = generate_diff_report(diff, report_spec1_path, spec2_path)

    # 输出报告
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print_status(f"Report saved to: {output_path}", "success")
    else:
        print("\n" + report)

    # 打印摘要
    print("\n" + "="*60)
    print("📊 Diff Summary")
    print("="*60)
    print(f"Breaking Changes: {len(diff.breaking_changes)}")
    print(f"Non-Breaking Changes: {len(diff.non_breaking_changes)}")
    print(f"Info Changes: {len(diff.info_changes)}")

    if diff.has_breaking_changes():
        print("\n⚠️ Breaking changes detected!")
        print_status("Review the report carefully before deploying", "warning")

        if args.fail_on_breaking:
            return 1
    else:
        print("\n✅ No breaking changes detected!")

    return 0

if __name__ == "__main__":
    sys.exit(main())
