#!/usr/bin/env python3
"""
Canvas Learning System - OpenAPI Diff Tool

比较两个 OpenAPI 规范文件，检测破坏性变更。

Usage:
    python scripts/spec-tools/diff-openapi.py <old_spec> <new_spec> [--format FORMAT]

Examples:
    python scripts/spec-tools/diff-openapi.py openapi-main.json openapi.json
    python scripts/spec-tools/diff-openapi.py openapi-main.json openapi.json --format json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple


class BreakingChangeType:
    """破坏性变更类型"""
    REMOVED_PATH = "removed_path"
    REMOVED_OPERATION = "removed_operation"
    REMOVED_REQUIRED_PARAM = "removed_required_param"
    ADDED_REQUIRED_PARAM = "added_required_param"
    CHANGED_PARAM_TYPE = "changed_param_type"
    REMOVED_RESPONSE = "removed_response"
    CHANGED_RESPONSE_SCHEMA = "changed_response_schema"
    REMOVED_SCHEMA = "removed_schema"
    REMOVED_SCHEMA_PROPERTY = "removed_schema_property"
    CHANGED_PROPERTY_TYPE = "changed_property_type"


class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


def color(text: str, c: str) -> str:
    """Add color to text"""
    import os
    if os.environ.get('NO_COLOR'):
        return text
    return f"{c}{text}{Colors.END}"


def load_spec(path: str) -> dict:
    """Load OpenAPI spec from file"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_paths(spec: dict) -> Dict[str, Dict[str, Any]]:
    """Extract paths with their operations"""
    return spec.get('paths', {})


def extract_schemas(spec: dict) -> Dict[str, Any]:
    """Extract component schemas"""
    return spec.get('components', {}).get('schemas', {})


def diff_paths(old_paths: dict, new_paths: dict) -> Tuple[List[dict], List[dict], List[dict]]:
    """Compare paths between specs"""
    breaking = []
    additions = []
    modifications = []

    old_path_set = set(old_paths.keys())
    new_path_set = set(new_paths.keys())

    # Removed paths (breaking)
    for path in old_path_set - new_path_set:
        breaking.append({
            'type': BreakingChangeType.REMOVED_PATH,
            'path': path,
            'message': f"Path '{path}' was removed"
        })

    # Added paths (non-breaking)
    for path in new_path_set - old_path_set:
        additions.append({
            'path': path,
            'message': f"Path '{path}' was added"
        })

    # Compare operations on existing paths
    for path in old_path_set & new_path_set:
        old_ops = old_paths[path]
        new_ops = new_paths[path]

        old_methods = set(old_ops.keys()) - {'parameters', 'servers', 'summary', 'description'}
        new_methods = set(new_ops.keys()) - {'parameters', 'servers', 'summary', 'description'}

        # Removed operations (breaking)
        for method in old_methods - new_methods:
            breaking.append({
                'type': BreakingChangeType.REMOVED_OPERATION,
                'path': path,
                'method': method.upper(),
                'message': f"{method.upper()} {path} was removed"
            })

        # Added operations (non-breaking)
        for method in new_methods - old_methods:
            additions.append({
                'path': path,
                'method': method.upper(),
                'message': f"{method.upper()} {path} was added"
            })

        # Compare existing operations
        for method in old_methods & new_methods:
            old_op = old_ops[method]
            new_op = new_ops[method]

            # Compare parameters
            param_changes = diff_parameters(
                old_op.get('parameters', []),
                new_op.get('parameters', []),
                path,
                method.upper()
            )
            breaking.extend(param_changes['breaking'])
            modifications.extend(param_changes['modifications'])

            # Compare responses
            response_changes = diff_responses(
                old_op.get('responses', {}),
                new_op.get('responses', {}),
                path,
                method.upper()
            )
            breaking.extend(response_changes['breaking'])
            modifications.extend(response_changes['modifications'])

    return breaking, additions, modifications


def diff_parameters(old_params: list, new_params: list, path: str, method: str) -> dict:
    """Compare operation parameters"""
    breaking = []
    modifications = []

    # Create param lookup by (name, in)
    old_param_map = {(p['name'], p.get('in', 'query')): p for p in old_params}
    new_param_map = {(p['name'], p.get('in', 'query')): p for p in new_params}

    old_keys = set(old_param_map.keys())
    new_keys = set(new_param_map.keys())

    # Required params that were removed (breaking)
    for key in old_keys - new_keys:
        param = old_param_map[key]
        if param.get('required', False):
            breaking.append({
                'type': BreakingChangeType.REMOVED_REQUIRED_PARAM,
                'path': path,
                'method': method,
                'param': key[0],
                'message': f"Required parameter '{key[0]}' was removed from {method} {path}"
            })

    # New required params (breaking)
    for key in new_keys - old_keys:
        param = new_param_map[key]
        if param.get('required', False):
            breaking.append({
                'type': BreakingChangeType.ADDED_REQUIRED_PARAM,
                'path': path,
                'method': method,
                'param': key[0],
                'message': f"New required parameter '{key[0]}' was added to {method} {path}"
            })

    return {'breaking': breaking, 'modifications': modifications}


def diff_responses(old_responses: dict, new_responses: dict, path: str, method: str) -> dict:
    """Compare operation responses"""
    breaking = []
    modifications = []

    old_codes = set(old_responses.keys())
    new_codes = set(new_responses.keys())

    # Removed success responses (breaking)
    for code in old_codes - new_codes:
        if code.startswith('2'):  # Success responses
            breaking.append({
                'type': BreakingChangeType.REMOVED_RESPONSE,
                'path': path,
                'method': method,
                'status': code,
                'message': f"Response {code} was removed from {method} {path}"
            })

    return {'breaking': breaking, 'modifications': modifications}


def diff_schemas(old_schemas: dict, new_schemas: dict) -> Tuple[List[dict], List[dict], List[dict]]:
    """Compare component schemas"""
    breaking = []
    additions = []
    modifications = []

    old_schema_set = set(old_schemas.keys())
    new_schema_set = set(new_schemas.keys())

    # Removed schemas (potentially breaking)
    for schema in old_schema_set - new_schema_set:
        breaking.append({
            'type': BreakingChangeType.REMOVED_SCHEMA,
            'schema': schema,
            'message': f"Schema '{schema}' was removed"
        })

    # Added schemas (non-breaking)
    for schema in new_schema_set - old_schema_set:
        additions.append({
            'schema': schema,
            'message': f"Schema '{schema}' was added"
        })

    # Compare existing schemas
    for schema in old_schema_set & new_schema_set:
        old_props = old_schemas[schema].get('properties', {})
        new_props = new_schemas[schema].get('properties', {})

        old_prop_set = set(old_props.keys())
        new_prop_set = set(new_props.keys())

        # Removed properties
        for prop in old_prop_set - new_prop_set:
            old_required = old_schemas[schema].get('required', [])
            if prop in old_required:
                breaking.append({
                    'type': BreakingChangeType.REMOVED_SCHEMA_PROPERTY,
                    'schema': schema,
                    'property': prop,
                    'message': f"Required property '{prop}' was removed from schema '{schema}'"
                })
            else:
                modifications.append({
                    'schema': schema,
                    'property': prop,
                    'message': f"Optional property '{prop}' was removed from schema '{schema}'"
                })

        # Check type changes
        for prop in old_prop_set & new_prop_set:
            old_type = old_props[prop].get('type')
            new_type = new_props[prop].get('type')
            if old_type != new_type:
                breaking.append({
                    'type': BreakingChangeType.CHANGED_PROPERTY_TYPE,
                    'schema': schema,
                    'property': prop,
                    'old_type': old_type,
                    'new_type': new_type,
                    'message': f"Property '{prop}' in schema '{schema}' changed type from '{old_type}' to '{new_type}'"
                })

    return breaking, additions, modifications


def generate_report(
    path_breaking: list,
    path_additions: list,
    path_modifications: list,
    schema_breaking: list,
    schema_additions: list,
    schema_modifications: list
) -> str:
    """Generate human-readable diff report"""
    lines = []
    lines.append("=" * 70)
    lines.append("OpenAPI Specification Diff Report")
    lines.append("=" * 70)

    # Breaking changes
    all_breaking = path_breaking + schema_breaking
    if all_breaking:
        lines.append("")
        lines.append(color("## BREAKING CHANGES", Colors.RED))
        for item in all_breaking:
            lines.append(f"  {color('!', Colors.RED)} {item['message']}")
    else:
        lines.append("")
        lines.append(color("## No breaking changes detected", Colors.GREEN))

    # Additions
    all_additions = path_additions + schema_additions
    if all_additions:
        lines.append("")
        lines.append(color("## Additions", Colors.GREEN))
        for item in all_additions:
            lines.append(f"  {color('+', Colors.GREEN)} {item['message']}")

    # Modifications
    all_modifications = path_modifications + schema_modifications
    if all_modifications:
        lines.append("")
        lines.append(color("## Modifications", Colors.YELLOW))
        for item in all_modifications:
            lines.append(f"  {color('~', Colors.YELLOW)} {item['message']}")

    # Summary
    lines.append("")
    lines.append("=" * 70)
    lines.append("Summary:")
    lines.append(f"  Breaking changes: {len(all_breaking)}")
    lines.append(f"  Additions: {len(all_additions)}")
    lines.append(f"  Modifications: {len(all_modifications)}")

    if all_breaking:
        lines.append("")
        lines.append(color("WARNING: This change contains breaking changes!", Colors.RED))
        lines.append("Consider whether this is intentional and update clients accordingly.")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Compare two OpenAPI specifications and detect breaking changes"
    )
    parser.add_argument(
        "old_spec",
        help="Path to the old (baseline) OpenAPI specification"
    )
    parser.add_argument(
        "new_spec",
        help="Path to the new OpenAPI specification"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)"
    )
    parser.add_argument(
        "--fail-on-breaking",
        action="store_true",
        help="Exit with code 1 if breaking changes are detected"
    )

    args = parser.parse_args()

    # Load specs
    try:
        old_spec = load_spec(args.old_spec)
        new_spec = load_spec(args.new_spec)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}", file=sys.stderr)
        sys.exit(1)

    # Compare
    old_paths = extract_paths(old_spec)
    new_paths = extract_paths(new_spec)
    old_schemas = extract_schemas(old_spec)
    new_schemas = extract_schemas(new_spec)

    path_breaking, path_additions, path_modifications = diff_paths(old_paths, new_paths)
    schema_breaking, schema_additions, schema_modifications = diff_schemas(old_schemas, new_schemas)

    if args.format == "json":
        result = {
            'breaking_changes': path_breaking + schema_breaking,
            'additions': path_additions + schema_additions,
            'modifications': path_modifications + schema_modifications,
            'has_breaking_changes': len(path_breaking + schema_breaking) > 0,
            'summary': {
                'breaking': len(path_breaking + schema_breaking),
                'additions': len(path_additions + schema_additions),
                'modifications': len(path_modifications + schema_modifications),
            }
        }
        print(json.dumps(result, indent=2))
    else:
        report = generate_report(
            path_breaking, path_additions, path_modifications,
            schema_breaking, schema_additions, schema_modifications
        )
        print(report)

    # Exit code
    if args.fail_on_breaking and (path_breaking or schema_breaking):
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
