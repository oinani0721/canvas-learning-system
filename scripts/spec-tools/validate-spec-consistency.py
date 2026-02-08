#!/usr/bin/env python3
"""
Canvas Learning System - Specification Consistency Validator

交叉验证 OpenAPI、Pydantic 模型和 JSON Schema 的一致性。
"代码是唯一的事实来源（Single Source of Truth）！！！！"

验证链:
    Pydantic Models (SSOT) ←→ OpenAPI Spec ←→ JSON Schema

Usage:
    python scripts/spec-tools/validate-spec-consistency.py [--fix] [--json]

Examples:
    python scripts/spec-tools/validate-spec-consistency.py          # 验证一致性
    python scripts/spec-tools/validate-spec-consistency.py --fix    # 自动修复
"""

import argparse
import importlib
import inspect
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Type

# Add backend to path
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))


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


class ConsistencyIssue:
    """Represents a consistency issue between specs"""

    def __init__(
        self,
        severity: str,  # 'critical', 'warning', 'info'
        source: str,
        target: str,
        issue_type: str,
        description: str,
        details: Optional[Dict] = None
    ):
        self.severity = severity
        self.source = source
        self.target = target
        self.issue_type = issue_type
        self.description = description
        self.details = details or {}

    def to_dict(self) -> Dict:
        return {
            'severity': self.severity,
            'source': self.source,
            'target': self.target,
            'issue_type': self.issue_type,
            'description': self.description,
            'details': self.details
        }


def load_openapi_spec() -> Optional[Dict]:
    """Load OpenAPI specification"""
    spec_path = PROJECT_ROOT / "openapi.json"
    if not spec_path.exists():
        return None
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_openapi_schemas(spec: Dict) -> Dict[str, Dict]:
    """Extract component schemas from OpenAPI spec"""
    return spec.get('components', {}).get('schemas', {})


def load_json_schemas() -> Dict[str, Dict]:
    """Load all JSON schemas from specs/data/"""
    schemas = {}
    schema_dir = PROJECT_ROOT / "specs" / "data"
    if not schema_dir.exists():
        return schemas

    for f in schema_dir.glob("*.schema.json"):
        try:
            with open(f, 'r', encoding='utf-8') as fp:
                schema = json.load(fp)
                # Use filename without .schema.json as key
                name = f.stem.replace('.schema', '')
                schemas[name] = schema
        except Exception:
            pass

    return schemas


def discover_pydantic_schemas() -> Dict[str, Dict]:
    """
    Discover Pydantic models and extract their JSON schemas.
    """
    from pydantic import BaseModel

    models_dir = BACKEND_DIR / "app" / "models"
    schemas = {}

    model_files = [
        "schemas",
        "memory_schemas",
        "review_models",
        "session_models",
        "metadata_models",
        "multimodal_schemas",
        "rollback",
        "common",
        "canvas_events",
    ]

    for module_name in model_files:
        try:
            module = importlib.import_module(f"app.models.{module_name}")

            for name, obj in inspect.getmembers(module, inspect.isclass):
                if obj.__module__ == f"app.models.{module_name}":
                    if issubclass(obj, BaseModel) and obj is not BaseModel:
                        try:
                            schema = obj.model_json_schema()
                            schemas[name] = {
                                'schema': schema,
                                'module': module_name,
                                'properties': set(schema.get('properties', {}).keys()),
                                'required': set(schema.get('required', []))
                            }
                        except Exception:
                            pass
        except Exception:
            pass

    return schemas


def validate_openapi_vs_pydantic(
    openapi_schemas: Dict[str, Dict],
    pydantic_schemas: Dict[str, Dict]
) -> List[ConsistencyIssue]:
    """
    Validate OpenAPI schemas against Pydantic models.
    Pydantic is the source of truth.
    """
    issues = []

    openapi_names = set(openapi_schemas.keys())
    pydantic_names = set(pydantic_schemas.keys())

    # Schemas in OpenAPI but not in Pydantic (orphaned)
    for name in openapi_names - pydantic_names:
        issues.append(ConsistencyIssue(
            severity='warning',
            source='OpenAPI',
            target='Pydantic',
            issue_type='orphaned_schema',
            description=f"Schema '{name}' in OpenAPI but no Pydantic model found",
            details={'schema': name}
        ))

    # Schemas in both - compare properties
    for name in openapi_names & pydantic_names:
        openapi_props = set(openapi_schemas[name].get('properties', {}).keys())
        pydantic_props = pydantic_schemas[name]['properties']

        # Properties in OpenAPI but not in Pydantic (OpenAPI幻觉!)
        extra_in_openapi = openapi_props - pydantic_props
        if extra_in_openapi:
            issues.append(ConsistencyIssue(
                severity='critical',
                source='OpenAPI',
                target='Pydantic',
                issue_type='schema_hallucination',
                description=f"OpenAPI has properties not in Pydantic model (幻觉!): {extra_in_openapi}",
                details={
                    'schema': name,
                    'hallucinated_properties': list(extra_in_openapi),
                    'code_file': pydantic_schemas[name]['module']
                }
            ))

        # Properties in Pydantic but not in OpenAPI (outdated OpenAPI)
        missing_in_openapi = pydantic_props - openapi_props
        if missing_in_openapi:
            issues.append(ConsistencyIssue(
                severity='warning',
                source='Pydantic',
                target='OpenAPI',
                issue_type='outdated_openapi',
                description=f"Pydantic has properties missing in OpenAPI: {missing_in_openapi}",
                details={
                    'schema': name,
                    'missing_properties': list(missing_in_openapi)
                }
            ))

    return issues


def validate_json_schema_vs_pydantic(
    json_schemas: Dict[str, Dict],
    pydantic_schemas: Dict[str, Dict]
) -> List[ConsistencyIssue]:
    """
    Validate JSON Schemas against Pydantic models.
    """
    issues = []

    # Convert pydantic names to kebab-case for matching
    def to_kebab(name: str) -> str:
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1).lower()

    pydantic_kebab = {to_kebab(k): v for k, v in pydantic_schemas.items()}

    json_names = set(json_schemas.keys())
    pydantic_names = set(pydantic_kebab.keys())

    # Schemas in JSON but not in Pydantic (orphaned)
    for name in json_names - pydantic_names:
        issues.append(ConsistencyIssue(
            severity='warning',
            source='JSON Schema',
            target='Pydantic',
            issue_type='orphaned_json_schema',
            description=f"JSON Schema '{name}' has no corresponding Pydantic model",
            details={'schema': name}
        ))

    # Compare properties for matching schemas
    for name in json_names & pydantic_names:
        json_props = set(json_schemas[name].get('properties', {}).keys())
        pydantic_props = pydantic_kebab[name]['properties']

        extra_in_json = json_props - pydantic_props
        if extra_in_json:
            issues.append(ConsistencyIssue(
                severity='critical',
                source='JSON Schema',
                target='Pydantic',
                issue_type='json_schema_hallucination',
                description=f"JSON Schema has properties not in code: {extra_in_json}",
                details={
                    'schema': name,
                    'hallucinated_properties': list(extra_in_json)
                }
            ))

    return issues


def check_enum_consistency(pydantic_schemas: Dict[str, Dict]) -> List[ConsistencyIssue]:
    """Check enum value consistency between specs"""
    issues = []

    # Known enum files to check
    enum_checks = [
        {
            'schema_file': 'fsrs-card',
            'property': 'state',
            'expected_values': [0, 1, 2, 3],  # From code
        }
    ]

    json_schemas = load_json_schemas()

    for check in enum_checks:
        if check['schema_file'] in json_schemas:
            schema = json_schemas[check['schema_file']]
            props = schema.get('properties', {})

            if check['property'] in props:
                prop_def = props[check['property']]
                schema_values = prop_def.get('enum', [])

                if set(schema_values) != set(check['expected_values']):
                    issues.append(ConsistencyIssue(
                        severity='critical',
                        source='JSON Schema',
                        target='Code',
                        issue_type='enum_mismatch',
                        description=f"Enum values mismatch for {check['schema_file']}.{check['property']}",
                        details={
                            'schema_values': schema_values,
                            'code_values': check['expected_values']
                        }
                    ))

    return issues


def generate_report(issues: List[ConsistencyIssue]) -> Dict:
    """Generate validation report"""
    critical = [i for i in issues if i.severity == 'critical']
    warnings = [i for i in issues if i.severity == 'warning']
    info = [i for i in issues if i.severity == 'info']

    return {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'summary': {
            'total_issues': len(issues),
            'critical': len(critical),
            'warnings': len(warnings),
            'info': len(info),
            'is_valid': len(critical) == 0
        },
        'issues': {
            'critical': [i.to_dict() for i in critical],
            'warnings': [i.to_dict() for i in warnings],
            'info': [i.to_dict() for i in info]
        }
    }


def print_report(report: Dict):
    """Print human-readable report"""
    print_header("Specification Consistency Report")

    summary = report['summary']
    print(f"\n  Total issues: {summary['total_issues']}")
    critical_count = summary['critical']
    critical_color = Colors.RED if critical_count else Colors.GREEN
    print(f"  {color(f'Critical: {critical_count}', critical_color)}")
    print(f"  Warnings: {summary['warnings']}")

    if summary['is_valid']:
        print(f"\n  {color('[OK] Specifications are consistent!', Colors.GREEN)}")
    else:
        print(f"\n  {color('[FAIL] Specifications have inconsistencies!', Colors.RED)}")

    # Print critical issues
    critical_issues = report['issues']['critical']
    if critical_issues:
        print(f"\n  {color('CRITICAL ISSUES (must fix):', Colors.RED)}")
        for issue in critical_issues[:10]:
            print(f"\n    {color('!', Colors.RED)} [{issue['issue_type']}]")
            print(f"      {issue['description']}")
            if issue['details']:
                if 'hallucinated_properties' in issue['details']:
                    print(f"      幻觉属性: {issue['details']['hallucinated_properties']}")
                if 'code_file' in issue['details']:
                    print(f"      代码位置: app/models/{issue['details']['code_file']}.py")

    # Print warnings
    warning_issues = report['issues']['warnings']
    if warning_issues:
        print(f"\n  {color('WARNINGS:', Colors.YELLOW)}")
        for issue in warning_issues[:5]:
            print(f"    {color('?', Colors.YELLOW)} {issue['description']}")


def main():
    parser = argparse.ArgumentParser(
        description="Validate specification consistency (Code-First)"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output as JSON"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Attempt to fix issues (regenerate specs from code)"
    )

    args = parser.parse_args()

    print_header("Specification Consistency Validator")
    print(f"  SSOT Principle: 代码是唯一的事实来源！")

    # Load all specs
    print("\n  Loading specifications...")

    openapi_spec = load_openapi_spec()
    if openapi_spec:
        openapi_schemas = extract_openapi_schemas(openapi_spec)
        print(f"    OpenAPI schemas: {len(openapi_schemas)}")
    else:
        openapi_schemas = {}
        print(f"    {color('OpenAPI: not found', Colors.YELLOW)}")

    json_schemas = load_json_schemas()
    print(f"    JSON schemas: {len(json_schemas)}")

    print("  Loading Pydantic models (source of truth)...")
    pydantic_schemas = discover_pydantic_schemas()
    print(f"    Pydantic models: {len(pydantic_schemas)}")

    # Run validations
    print("\n  Running validations...")
    all_issues = []

    # OpenAPI vs Pydantic
    if openapi_schemas:
        issues = validate_openapi_vs_pydantic(openapi_schemas, pydantic_schemas)
        all_issues.extend(issues)
        print(f"    OpenAPI vs Pydantic: {len(issues)} issues")

    # JSON Schema vs Pydantic
    issues = validate_json_schema_vs_pydantic(json_schemas, pydantic_schemas)
    all_issues.extend(issues)
    print(f"    JSON Schema vs Pydantic: {len(issues)} issues")

    # Enum consistency
    issues = check_enum_consistency(pydantic_schemas)
    all_issues.extend(issues)
    print(f"    Enum consistency: {len(issues)} issues")

    # Generate report
    report = generate_report(all_issues)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)

    # Fix if requested
    if args.fix and not report['summary']['is_valid']:
        print(f"\n  {color('Attempting auto-fix...', Colors.YELLOW)}")
        print("  Running: python scripts/spec-tools/export-openapi.py")
        os.system(f"cd {BACKEND_DIR} && python ../scripts/spec-tools/export-openapi.py")
        print("  Running: python scripts/spec-tools/export-json-schemas.py")
        os.system(f"python {SCRIPT_DIR}/export-json-schemas.py")
        print(f"  {color('Re-run validation to verify fixes', Colors.YELLOW)}")

    return 0 if report['summary']['is_valid'] else 1


if __name__ == "__main__":
    sys.exit(main())
