#!/usr/bin/env python3
"""
Canvas Learning System - API Reality Dashboard

实时显示代码中实际存在的API端点，与规范文档对比。
"代码是唯一的事实来源（Single Source of Truth）！！！！"

Usage:
    python scripts/spec-tools/api-reality-dashboard.py [--export] [--compare EPIC_FILE]

Examples:
    python scripts/spec-tools/api-reality-dashboard.py                 # 显示所有API
    python scripts/spec-tools/api-reality-dashboard.py --export        # 导出Markdown
    python scripts/spec-tools/api-reality-dashboard.py --compare docs/epics/EPIC-30-*.md
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Set

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"


class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    END = '\033[0m'


def color(text: str, c: str) -> str:
    if os.environ.get('NO_COLOR'):
        return text
    return f"{c}{text}{Colors.END}"


def print_header(title: str):
    print()
    print(color("=" * 70, Colors.CYAN))
    print(color(f"  {title}", Colors.CYAN))
    print(color("=" * 70, Colors.CYAN))


def load_or_generate_openapi() -> Dict:
    """Load OpenAPI spec, generate if not exists."""
    spec_path = BACKEND_DIR / "openapi.json"

    if not spec_path.exists():
        print(f"  {color('Generating OpenAPI from code...', Colors.YELLOW)}")
        os.system(f'cd "{BACKEND_DIR}" && python ../scripts/spec-tools/export-openapi.py')

    if spec_path.exists():
        with open(spec_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def categorize_endpoints(spec: Dict) -> Dict[str, List[Dict]]:
    """Categorize endpoints by their prefix."""
    categories = {}

    for path, ops in spec.get('paths', {}).items():
        # Extract category from path
        parts = path.split('/')
        if len(parts) >= 4:  # /api/v1/category/...
            category = parts[3]
        else:
            category = 'root'

        if category not in categories:
            categories[category] = []

        for method, details in ops.items():
            if method.lower() == 'options':
                continue
            categories[category].append({
                'method': method.upper(),
                'path': path,
                'summary': details.get('summary', ''),
                'tags': details.get('tags', [])
            })

    return categories


def print_dashboard(spec: Dict):
    """Print the API reality dashboard."""
    print_header("API Reality Dashboard")
    print(f"  Generated at: {datetime.now(timezone.utc).isoformat()}")
    print(f"  OpenAPI Version: {spec.get('openapi', 'N/A')}")
    print(f"  API Title: {spec.get('info', {}).get('title', 'N/A')}")

    categories = categorize_endpoints(spec)
    total_endpoints = sum(len(eps) for eps in categories.values())
    print(f"  {color(f'Total Endpoints: {total_endpoints}', Colors.GREEN)}")

    # Print by category
    for category in sorted(categories.keys()):
        endpoints = categories[category]
        print(f"\n  {color(f'📁 {category.upper()}', Colors.BLUE)} ({len(endpoints)} endpoints)")

        for ep in sorted(endpoints, key=lambda x: x['path']):
            method_color = {
                'GET': Colors.GREEN,
                'POST': Colors.BLUE,
                'PUT': Colors.YELLOW,
                'DELETE': Colors.RED,
                'PATCH': Colors.MAGENTA
            }.get(ep['method'], Colors.END)

            print(f"    {color(f'{ep[\"method\"]:6}', method_color)} {ep['path']}")


def export_markdown(spec: Dict) -> str:
    """Export API dashboard as Markdown."""
    categories = categorize_endpoints(spec)
    total = sum(len(eps) for eps in categories.values())

    lines = [
        "# Canvas Learning System - API Reality Dashboard",
        "",
        f"> 代码是唯一的事实来源（Single Source of Truth）！",
        f"> 生成时间: {datetime.now(timezone.utc).isoformat()}",
        "",
        f"## 总览",
        "",
        f"- **总端点数**: {total}",
        f"- **OpenAPI版本**: {spec.get('openapi', 'N/A')}",
        "",
        "## 端点清单",
        ""
    ]

    for category in sorted(categories.keys()):
        endpoints = categories[category]
        lines.append(f"### {category.upper()} ({len(endpoints)} endpoints)")
        lines.append("")
        lines.append("| Method | Path | Summary |")
        lines.append("|--------|------|---------|")

        for ep in sorted(endpoints, key=lambda x: x['path']):
            lines.append(f"| {ep['method']} | `{ep['path']}` | {ep['summary']} |")

        lines.append("")

    return "\n".join(lines)


def compare_with_epic(spec: Dict, epic_path: str):
    """Compare actual API with EPIC claims."""
    import re

    epic_file = Path(epic_path)
    if not epic_file.exists():
        # Try glob
        matches = list(PROJECT_ROOT.glob(epic_path))
        if not matches:
            print(f"  {color(f'EPIC file not found: {epic_path}', Colors.RED)}")
            return
        epic_file = matches[0]

    content = epic_file.read_text(encoding='utf-8')

    # Extract claimed endpoints from EPIC
    endpoint_pattern = r'(GET|POST|PUT|DELETE|PATCH)\s+(/api/v[0-9]/[a-zA-Z0-9_/\-\{\}]+)'
    claimed = set(re.findall(endpoint_pattern, content))
    claimed_endpoints = {f"{m[0]} {m[1]}" for m in claimed}

    # Get actual endpoints
    actual_endpoints = set()
    for path, ops in spec.get('paths', {}).items():
        for method in ops.keys():
            if method.lower() != 'options':
                actual_endpoints.add(f"{method.upper()} {path}")

    # Compare
    print_header(f"EPIC vs Reality: {epic_file.name}")

    # In EPIC but not in code (hallucination!)
    hallucinated = claimed_endpoints - actual_endpoints
    if hallucinated:
        print(f"\n  {color('🔴 HALLUCINATED (in EPIC but NOT in code):', Colors.RED)}")
        for ep in sorted(hallucinated):
            print(f"    ❌ {ep}")

    # In code but not in EPIC (missing documentation)
    # Normalize for comparison
    def normalize(ep: str) -> str:
        return re.sub(r'\{[^}]+\}', '{id}', ep)

    claimed_normalized = {normalize(ep) for ep in claimed_endpoints}
    actual_normalized = {normalize(ep) for ep in actual_endpoints}

    # Find endpoints that might be undocumented
    # (This is a simplified check)

    # Verified endpoints
    verified = claimed_endpoints & actual_endpoints
    print(f"\n  {color(f'✅ VERIFIED ({len(verified)} endpoints match):', Colors.GREEN)}")
    for ep in sorted(verified)[:10]:
        print(f"    ✓ {ep}")
    if len(verified) > 10:
        print(f"    ... and {len(verified) - 10} more")

    # Summary
    print(f"\n  {color('Summary:', Colors.CYAN)}")
    print(f"    EPIC claims: {len(claimed_endpoints)} endpoints")
    print(f"    Code reality: {len(actual_endpoints)} endpoints")
    print(f"    Hallucinated: {len(hallucinated)}")
    print(f"    Verified: {len(verified)}")

    if hallucinated:
        print(f"\n  {color('⚠️ EPIC needs update! Hallucinated endpoints found.', Colors.YELLOW)}")


def main():
    parser = argparse.ArgumentParser(
        description="API Reality Dashboard - Show actual endpoints from code"
    )
    parser.add_argument(
        "--export", "-e",
        action="store_true",
        help="Export as Markdown file"
    )
    parser.add_argument(
        "--compare", "-c",
        type=str,
        help="Compare with EPIC file"
    )

    args = parser.parse_args()

    # Load or generate OpenAPI
    spec = load_or_generate_openapi()
    if not spec:
        print(f"  {color('Failed to load OpenAPI spec', Colors.RED)}")
        return 1

    if args.compare:
        compare_with_epic(spec, args.compare)
    elif args.export:
        md_content = export_markdown(spec)
        output_path = PROJECT_ROOT / "docs" / "api" / "API-REALITY-DASHBOARD.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(md_content, encoding='utf-8')
        print(f"  {color(f'Exported to {output_path}', Colors.GREEN)}")
    else:
        print_dashboard(spec)

    return 0


if __name__ == "__main__":
    sys.exit(main())
