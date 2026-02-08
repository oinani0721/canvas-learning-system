#!/usr/bin/env python3
"""
Canvas Learning System - EPIC Reality Check

在创建/修改EPIC之前，自动检查代码现实。
"代码是唯一的事实来源（Single Source of Truth）！！！！"

Usage:
    python scripts/spec-tools/epic-reality-check.py [--epic EPIC_FILE] [--json]

Examples:
    python scripts/spec-tools/epic-reality-check.py                           # 全量检查
    python scripts/spec-tools/epic-reality-check.py --epic docs/epics/EPIC-30-*.md  # 检查特定EPIC
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"


class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
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


def load_openapi() -> Optional[Dict]:
    """Load OpenAPI spec from code-generated file."""
    spec_path = BACKEND_DIR / "openapi.json"
    if not spec_path.exists():
        return None
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_actual_endpoints(spec: Dict) -> Set[str]:
    """Extract actual API endpoints from OpenAPI spec."""
    endpoints = set()
    for path, ops in spec.get('paths', {}).items():
        for method in ops.keys():
            if method.lower() != 'options':
                endpoints.add(f"{method.upper()} {path}")
    return endpoints


def get_actual_files() -> Dict[str, Path]:
    """Get actual code files in the project."""
    files = {}

    # Backend Python files
    for py_file in BACKEND_DIR.rglob("*.py"):
        rel_path = py_file.relative_to(PROJECT_ROOT)
        files[str(rel_path).replace("\\", "/")] = py_file

    # Frontend TypeScript files
    src_dir = PROJECT_ROOT / "src"
    if src_dir.exists():
        for ts_file in src_dir.rglob("*.ts"):
            rel_path = ts_file.relative_to(PROJECT_ROOT)
            files[str(rel_path).replace("\\", "/")] = ts_file
        for tsx_file in src_dir.rglob("*.tsx"):
            rel_path = tsx_file.relative_to(PROJECT_ROOT)
            files[str(rel_path).replace("\\", "/")] = tsx_file

    return files


def extract_epic_claims(epic_content: str) -> Dict[str, List[str]]:
    """Extract claims from EPIC content."""
    claims = {
        'files': [],      # Files mentioned in EPIC
        'endpoints': [],  # API endpoints mentioned
        'classes': [],    # Classes/Services mentioned
    }

    # Extract file paths (e.g., `backend/app/services/xxx.py`)
    file_patterns = [
        r'`([a-zA-Z0-9_/\-\.]+\.py)`',
        r'`([a-zA-Z0-9_/\-\.]+\.ts)`',
        r'`([a-zA-Z0-9_/\-\.]+\.tsx)`',
    ]
    for pattern in file_patterns:
        matches = re.findall(pattern, epic_content)
        claims['files'].extend(matches)

    # Extract API endpoints (e.g., POST /api/v1/xxx)
    endpoint_pattern = r'(GET|POST|PUT|DELETE|PATCH)\s+(/api/v[0-9]/[a-zA-Z0-9_/\-\{\}]+)'
    matches = re.findall(endpoint_pattern, epic_content)
    claims['endpoints'].extend([f"{m[0]} {m[1]}" for m in matches])

    # Extract service/class names
    class_pattern = r'`?([A-Z][a-zA-Z]+(?:Service|Client|Controller|Handler))`?'
    matches = re.findall(class_pattern, epic_content)
    claims['classes'].extend(matches)

    return claims


def verify_claims(
    claims: Dict[str, List[str]],
    actual_endpoints: Set[str],
    actual_files: Dict[str, Path]
) -> Dict[str, Any]:
    """Verify EPIC claims against code reality."""
    results = {
        'files': {'verified': [], 'hallucinated': []},
        'endpoints': {'verified': [], 'hallucinated': []},
        'classes': {'verified': [], 'hallucinated': []},
    }

    # Verify files
    for file_path in set(claims['files']):
        # Normalize path
        normalized = file_path.replace("\\", "/")
        if normalized in actual_files:
            results['files']['verified'].append(file_path)
        else:
            # Check partial match
            found = False
            for actual_path in actual_files.keys():
                if normalized in actual_path or actual_path.endswith(normalized):
                    results['files']['verified'].append(f"{file_path} → {actual_path}")
                    found = True
                    break
            if not found:
                results['files']['hallucinated'].append(file_path)

    # Verify endpoints
    for endpoint in set(claims['endpoints']):
        # Normalize endpoint (handle path parameters)
        normalized = re.sub(r'\{[^}]+\}', '{id}', endpoint)
        found = False
        for actual in actual_endpoints:
            actual_normalized = re.sub(r'\{[^}]+\}', '{id}', actual)
            if normalized == actual_normalized:
                results['endpoints']['verified'].append(endpoint)
                found = True
                break
        if not found:
            results['endpoints']['hallucinated'].append(endpoint)

    # Verify classes (search in code)
    for class_name in set(claims['classes']):
        found = False
        for file_path, full_path in actual_files.items():
            if file_path.endswith('.py'):
                try:
                    content = full_path.read_text(encoding='utf-8')
                    if f"class {class_name}" in content:
                        results['classes']['verified'].append(f"{class_name} in {file_path}")
                        found = True
                        break
                except:
                    pass
        if not found:
            results['classes']['hallucinated'].append(class_name)

    return results


def check_epic(epic_path: Path, actual_endpoints: Set[str], actual_files: Dict[str, Path]) -> Dict:
    """Check a single EPIC file."""
    content = epic_path.read_text(encoding='utf-8')
    claims = extract_epic_claims(content)
    verification = verify_claims(claims, actual_endpoints, actual_files)

    # Calculate hallucination score
    total_claims = sum(len(claims[k]) for k in claims)
    hallucinated = sum(len(verification[k]['hallucinated']) for k in verification)

    return {
        'epic': epic_path.name,
        'claims': claims,
        'verification': verification,
        'total_claims': total_claims,
        'hallucinated_count': hallucinated,
        'hallucination_rate': hallucinated / total_claims * 100 if total_claims > 0 else 0
    }


def print_report(result: Dict):
    """Print human-readable report for an EPIC."""
    print(f"\n  {color('EPIC:', Colors.BLUE)} {result['epic']}")
    print(f"  Claims: {result['total_claims']}, Hallucinated: {result['hallucinated_count']}")

    rate = result['hallucination_rate']
    if rate == 0:
        print(f"  {color('✅ 0% hallucination - EPIC matches code reality!', Colors.GREEN)}")
    elif rate < 20:
        print(f"  {color(f'🟡 {rate:.1f}% hallucination - Minor issues', Colors.YELLOW)}")
    else:
        print(f"  {color(f'🔴 {rate:.1f}% hallucination - EPIC has major discrepancies!', Colors.RED)}")

    # Print hallucinated items
    v = result['verification']
    if v['files']['hallucinated']:
        print(f"\n  {color('Hallucinated files:', Colors.RED)}")
        for f in v['files']['hallucinated'][:5]:
            print(f"    ❌ {f}")

    if v['endpoints']['hallucinated']:
        print(f"\n  {color('Hallucinated endpoints:', Colors.RED)}")
        for e in v['endpoints']['hallucinated'][:5]:
            print(f"    ❌ {e}")

    if v['classes']['hallucinated']:
        print(f"\n  {color('Hallucinated classes:', Colors.RED)}")
        for c in v['classes']['hallucinated'][:5]:
            print(f"    ❌ {c}")


def main():
    parser = argparse.ArgumentParser(
        description="Check EPIC claims against code reality"
    )
    parser.add_argument(
        "--epic", "-e",
        type=str,
        help="Specific EPIC file to check (glob pattern)"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args()

    print_header("EPIC Reality Check")
    print(f"  Principle: 代码是唯一的事实来源！")

    # Load OpenAPI
    print("\n  Loading code reality...")
    openapi = load_openapi()
    if openapi:
        actual_endpoints = get_actual_endpoints(openapi)
        print(f"    API endpoints: {len(actual_endpoints)}")
    else:
        print(f"  {color('Warning: OpenAPI not found. Run export-openapi.py first.', Colors.YELLOW)}")
        actual_endpoints = set()

    actual_files = get_actual_files()
    print(f"    Code files: {len(actual_files)}")

    # Find EPIC files
    epics_dir = PROJECT_ROOT / "docs" / "epics"
    if args.epic:
        epic_files = list(epics_dir.glob(args.epic))
    else:
        epic_files = list(epics_dir.glob("*.md"))

    print(f"    EPICs to check: {len(epic_files)}")

    # Check each EPIC
    results = []
    for epic_path in sorted(epic_files):
        result = check_epic(epic_path, actual_endpoints, actual_files)
        results.append(result)
        if not args.json:
            print_report(result)

    # Summary
    if not args.json:
        print_header("Summary")
        total_epics = len(results)
        clean_epics = sum(1 for r in results if r['hallucination_rate'] == 0)
        problematic = [r for r in results if r['hallucination_rate'] >= 20]

        print(f"\n  Total EPICs: {total_epics}")
        print(f"  {color(f'Clean (0% hallucination): {clean_epics}', Colors.GREEN)}")
        print(f"  {color(f'Problematic (≥20% hallucination): {len(problematic)}', Colors.RED)}")

        if problematic:
            print(f"\n  {color('EPICs needing immediate fix:', Colors.RED)}")
            for p in problematic:
                print(f"    - {p['epic']} ({p['hallucination_rate']:.1f}%)")
    else:
        output = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'actual_endpoints_count': len(actual_endpoints),
            'actual_files_count': len(actual_files),
            'epics': results
        }
        print(json.dumps(output, indent=2))

    # Return exit code based on hallucination
    max_hallucination = max(r['hallucination_rate'] for r in results) if results else 0
    return 1 if max_hallucination >= 20 else 0


if __name__ == "__main__":
    sys.exit(main())
