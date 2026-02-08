#!/usr/bin/env python3
"""
Canvas Learning System - Specification Sync Verification Script

验证规范文档与代码的同步状态。

功能:
1. 检测 OpenAPI 规范是否过时
2. 比较规范定义与实际代码
3. 生成同步状态报告

使用方法:
    python scripts/spec-tools/verify-sync.py [--fix] [--report]
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

# 颜色输出
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def color(text: str, c: str) -> str:
    """添加颜色"""
    if os.environ.get('NO_COLOR'):
        return text
    return f"{c}{text}{Colors.END}"


def load_openapi_spec(spec_path: Path) -> dict:
    """加载 OpenAPI 规范"""
    if not spec_path.exists():
        return {}

    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_routes_from_code(api_dir: Path) -> Dict[str, List[str]]:
    """从代码中提取路由定义"""
    routes = {}

    for py_file in api_dir.glob("**/*.py"):
        if py_file.name.startswith("_"):
            continue

        content = py_file.read_text(encoding='utf-8')

        # 匹配 FastAPI 路由装饰器
        patterns = [
            r'@router\.(get|post|put|patch|delete)\s*\(\s*["\']([^"\']+)["\']',
            r'@app\.(get|post|put|patch|delete)\s*\(\s*["\']([^"\']+)["\']',
        ]

        file_routes = []
        for pattern in patterns:
            matches = re.findall(pattern, content)
            for method, path in matches:
                file_routes.append((method.upper(), path))

        if file_routes:
            routes[str(py_file.relative_to(api_dir))] = file_routes

    return routes


def extract_routes_from_spec(spec: dict) -> List[Tuple[str, str]]:
    """从 OpenAPI 规范中提取路由"""
    routes = []

    for path, methods in spec.get('paths', {}).items():
        for method in methods:
            if method in ['get', 'post', 'put', 'patch', 'delete']:
                routes.append((method.upper(), path))

    return routes


def compare_routes(code_routes: Dict[str, List[Tuple[str, str]]],
                   spec_routes: List[Tuple[str, str]]) -> dict:
    """比较代码路由和规范路由"""
    # 扁平化代码路由
    all_code_routes = set()
    for file_routes in code_routes.values():
        for route in file_routes:
            all_code_routes.add(route)

    spec_routes_set = set(spec_routes)

    # 计算差异
    in_code_not_spec = all_code_routes - spec_routes_set
    in_spec_not_code = spec_routes_set - all_code_routes
    in_both = all_code_routes & spec_routes_set

    return {
        'in_code_not_spec': sorted(in_code_not_spec),
        'in_spec_not_code': sorted(in_spec_not_code),
        'in_both': sorted(in_both),
        'code_count': len(all_code_routes),
        'spec_count': len(spec_routes),
        'sync_rate': len(in_both) / max(len(all_code_routes), 1) * 100,
    }


def check_spec_age(spec_path: Path) -> dict:
    """检查规范文件的年龄"""
    if not spec_path.exists():
        return {'exists': False, 'age_days': None}

    mtime = datetime.fromtimestamp(spec_path.stat().st_mtime, tz=timezone.utc)
    now = datetime.now(timezone.utc)
    age = now - mtime

    return {
        'exists': True,
        'last_modified': mtime.isoformat(),
        'age_days': age.days,
        'age_hours': age.total_seconds() / 3600,
    }


def generate_report(comparison: dict, spec_age: dict) -> str:
    """生成同步状态报告"""
    lines = []
    lines.append("=" * 60)
    lines.append("Canvas Learning System - Specification Sync Report")
    lines.append("=" * 60)
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    lines.append("")

    # 规范年龄
    lines.append("## OpenAPI Specification Age")
    if spec_age['exists']:
        age_days = spec_age['age_days']
        if age_days > 30:
            status = color("STALE", Colors.RED)
        elif age_days > 7:
            status = color("AGING", Colors.YELLOW)
        else:
            status = color("FRESH", Colors.GREEN)

        lines.append(f"  Status: {status}")
        lines.append(f"  Last Modified: {spec_age['last_modified']}")
        lines.append(f"  Age: {age_days} days ({spec_age['age_hours']:.1f} hours)")
    else:
        lines.append(f"  Status: {color('NOT FOUND', Colors.RED)}")
    lines.append("")

    # 路由同步
    lines.append("## Route Synchronization")
    lines.append(f"  Code Routes: {comparison['code_count']}")
    lines.append(f"  Spec Routes: {comparison['spec_count']}")

    sync_rate = comparison['sync_rate']
    if sync_rate >= 95:
        sync_status = color(f"{sync_rate:.1f}%", Colors.GREEN)
    elif sync_rate >= 80:
        sync_status = color(f"{sync_rate:.1f}%", Colors.YELLOW)
    else:
        sync_status = color(f"{sync_rate:.1f}%", Colors.RED)
    lines.append(f"  Sync Rate: {sync_status}")
    lines.append("")

    # 差异详情
    if comparison['in_code_not_spec']:
        lines.append("## Routes in Code but NOT in Spec (Missing from docs)")
        for method, path in comparison['in_code_not_spec']:
            lines.append(f"  {color('!', Colors.YELLOW)} {method} {path}")
        lines.append("")

    if comparison['in_spec_not_code']:
        lines.append("## Routes in Spec but NOT in Code (Orphaned docs)")
        for method, path in comparison['in_spec_not_code']:
            lines.append(f"  {color('!', Colors.RED)} {method} {path}")
        lines.append("")

    # 建议
    lines.append("## Recommendations")
    recommendations = []

    if not spec_age['exists']:
        recommendations.append("- Generate OpenAPI spec: python scripts/spec-tools/export-openapi.py")
    elif spec_age['age_days'] > 7:
        recommendations.append("- Regenerate OpenAPI spec: python scripts/spec-tools/export-openapi.py")

    if comparison['in_code_not_spec']:
        recommendations.append(f"- Add {len(comparison['in_code_not_spec'])} missing routes to OpenAPI spec")

    if comparison['in_spec_not_code']:
        recommendations.append(f"- Remove {len(comparison['in_spec_not_code'])} orphaned routes from OpenAPI spec")

    if not recommendations:
        recommendations.append("- All looks good! Keep up the good work.")

    for rec in recommendations:
        lines.append(f"  {rec}")

    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Verify specification sync with code"
    )
    parser.add_argument(
        "--fix", "-f",
        action="store_true",
        help="Automatically regenerate OpenAPI spec if stale"
    )
    parser.add_argument(
        "--report", "-r",
        action="store_true",
        help="Save report to file"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args()

    # 路径
    project_root = Path(__file__).parent.parent.parent
    spec_path = project_root / "openapi.json"
    api_dir = project_root / "backend" / "app" / "api"

    # 加载规范
    spec = load_openapi_spec(spec_path)

    # 提取路由
    code_routes = extract_routes_from_code(api_dir)
    spec_routes = extract_routes_from_spec(spec)

    # 比较
    comparison = compare_routes(code_routes, spec_routes)
    spec_age = check_spec_age(spec_path)

    if args.json:
        result = {
            'comparison': comparison,
            'spec_age': spec_age,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }
        print(json.dumps(result, indent=2))
    else:
        report = generate_report(comparison, spec_age)
        print(report)

        if args.report:
            report_path = project_root / "spec-sync-report.txt"
            with open(report_path, 'w', encoding='utf-8') as f:
                # 移除颜色代码
                clean_report = re.sub(r'\033\[[0-9;]+m', '', report)
                f.write(clean_report)
            print(f"\nReport saved to: {report_path}")

    # 自动修复
    if args.fix and (not spec_age['exists'] or spec_age['age_days'] > 7):
        print("\nRegenerating OpenAPI spec...")
        os.system(f"python {project_root / 'scripts' / 'spec-tools' / 'export-openapi.py'}")

    # 返回码
    if comparison['sync_rate'] < 80 or spec_age.get('age_days', 0) > 30:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
