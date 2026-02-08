#!/usr/bin/env python3
"""
Canvas Learning System - Pydantic → JSON Schema Exporter

代码优先原则：从 Pydantic 模型自动生成 JSON Schema。
"代码是唯一的事实来源（Single Source of Truth）！！！！"

Usage:
    python scripts/spec-tools/export-json-schemas.py [--output-dir DIR] [--compare] [--stats]

Examples:
    python scripts/spec-tools/export-json-schemas.py                    # 导出到 specs/data/generated/
    python scripts/spec-tools/export-json-schemas.py --compare          # 与现有 Schema 比较
    python scripts/spec-tools/export-json-schemas.py --output-dir ./out # 导出到指定目录
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

# Add backend to path for imports
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
    """Add color to text"""
    if os.environ.get('NO_COLOR'):
        return text
    return f"{c}{text}{Colors.END}"


def print_header(title: str):
    """Print section header"""
    print()
    print(color("=" * 70, Colors.CYAN))
    print(color(f"  {title}", Colors.CYAN))
    print(color("=" * 70, Colors.CYAN))


def discover_pydantic_models() -> Dict[str, List[Tuple[str, Type]]]:
    """
    Discover all Pydantic models from backend/app/models/.

    Returns:
        Dict mapping module name to list of (class_name, class) tuples
    """
    from pydantic import BaseModel

    models_dir = BACKEND_DIR / "app" / "models"
    discovered = {}

    model_files = [
        "schemas",
        "memory_schemas",
        "review_models",
        "session_models",
        "metadata_models",
        "multimodal_schemas",
        "rollback",
        "common",
        "enums",
        "canvas_events",
        "agent_routing_models",
        "intelligent_parallel_models",
        "merge_strategy_models",
    ]

    for module_name in model_files:
        try:
            module = importlib.import_module(f"app.models.{module_name}")
            models = []

            for name, obj in inspect.getmembers(module, inspect.isclass):
                # Only include classes defined in this module
                if obj.__module__ == f"app.models.{module_name}":
                    # Check if it's a Pydantic model (but not Enum)
                    if issubclass(obj, BaseModel) and obj is not BaseModel:
                        models.append((name, obj))

            if models:
                discovered[module_name] = models

        except Exception as e:
            print(f"  {color('!', Colors.YELLOW)} Could not import {module_name}: {e}")

    return discovered


def model_to_schema_name(class_name: str) -> str:
    """
    Convert PydanticClassName to schema-file-name.

    Examples:
        HealthCheckResponse -> health-check-response
        LearningEpisodeCreate -> learning-episode-create
    """
    import re
    # Insert hyphen before uppercase letters
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', class_name)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1)
    return s2.lower()


def generate_json_schema(model_class: Type) -> Dict[str, Any]:
    """
    Generate JSON Schema from Pydantic model.

    Uses Pydantic's built-in model_json_schema() method.
    """
    try:
        schema = model_class.model_json_schema()

        # Add metadata
        schema['$id'] = f"https://canvas-learning.local/schemas/{model_to_schema_name(model_class.__name__)}.json"
        schema['$schema'] = "https://json-schema.org/draft/2020-12/schema"

        # Add generation metadata
        schema['x-generated'] = {
            'from': f"app.models.{model_class.__module__.split('.')[-1]}.{model_class.__name__}",
            'at': datetime.now(timezone.utc).isoformat(),
            'tool': 'export-json-schemas.py'
        }

        return schema
    except Exception as e:
        return {'error': str(e), 'model': model_class.__name__}


def export_schemas(output_dir: Path) -> Tuple[int, int, List[Dict]]:
    """
    Export all Pydantic models to JSON Schema files.

    Returns:
        Tuple of (success_count, error_count, results)
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    discovered = discover_pydantic_models()
    success = 0
    errors = 0
    results = []

    for module_name, models in discovered.items():
        print(f"\n  Module: {color(module_name, Colors.BLUE)}")

        for class_name, model_class in models:
            schema = generate_json_schema(model_class)
            schema_name = model_to_schema_name(class_name)
            output_path = output_dir / f"{schema_name}.schema.json"

            if 'error' in schema:
                print(f"    {color('[X]', Colors.RED)} {class_name}: {schema['error']}")
                errors += 1
                results.append({
                    'model': class_name,
                    'status': 'error',
                    'error': schema['error']
                })
            else:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(schema, f, indent=2, ensure_ascii=False)

                print(f"    {color('[OK]', Colors.GREEN)} {class_name} -> {schema_name}.schema.json")
                success += 1
                results.append({
                    'model': class_name,
                    'status': 'success',
                    'schema_file': str(output_path.name),
                    'properties': len(schema.get('properties', {}))
                })

    return success, errors, results


def compare_schemas(generated_dir: Path, existing_dir: Path) -> Dict[str, Any]:
    """
    Compare generated schemas with existing specs/data/ schemas.

    Returns comparison report.
    """
    generated_files = {f.stem.replace('.schema', ''): f for f in generated_dir.glob('*.schema.json')}
    existing_files = {f.stem.replace('.schema', ''): f for f in existing_dir.glob('*.schema.json')}

    generated_names = set(generated_files.keys())
    existing_names = set(existing_files.keys())

    # Find differences
    only_in_generated = generated_names - existing_names
    only_in_existing = existing_names - generated_names
    in_both = generated_names & existing_names

    # Compare schemas that exist in both
    differences = []
    matches = []

    for name in in_both:
        with open(generated_files[name], 'r', encoding='utf-8') as f:
            gen_schema = json.load(f)
        with open(existing_files[name], 'r', encoding='utf-8') as f:
            exist_schema = json.load(f)

        # Remove metadata for comparison
        gen_props = set(gen_schema.get('properties', {}).keys())
        exist_props = set(exist_schema.get('properties', {}).keys())

        if gen_props != exist_props:
            only_in_gen = gen_props - exist_props
            only_in_exist = exist_props - gen_props
            differences.append({
                'schema': name,
                'generated_props': list(gen_props),
                'existing_props': list(exist_props),
                'only_in_generated': list(only_in_gen),
                'only_in_existing': list(only_in_exist),
                'issue': 'property_mismatch'
            })
        else:
            matches.append(name)

    return {
        'generated_count': len(generated_names),
        'existing_count': len(existing_names),
        'only_in_generated': list(only_in_generated),
        'only_in_existing': list(only_in_existing),
        'property_mismatches': differences,
        'matches': matches,
        'sync_rate': len(matches) / len(in_both) * 100 if in_both else 0
    }


def print_comparison_report(comparison: Dict[str, Any]):
    """Print human-readable comparison report"""
    print_header("Schema Comparison Report (Generated vs Existing)")

    print(f"\n  Generated schemas: {comparison['generated_count']}")
    print(f"  Existing schemas: {comparison['existing_count']}")
    print(f"  Sync rate: {comparison['sync_rate']:.1f}%")

    # Schemas only in generated (new in code, missing in specs)
    if comparison['only_in_generated']:
        print(f"\n  {color('New schemas (in code, not in specs):', Colors.GREEN)}")
        for name in comparison['only_in_generated'][:10]:
            print(f"    + {name}")
        if len(comparison['only_in_generated']) > 10:
            print(f"    ... and {len(comparison['only_in_generated']) - 10} more")

    # Schemas only in existing (orphaned specs, no code)
    if comparison['only_in_existing']:
        print(f"\n  {color('Orphaned schemas (in specs, not in code):', Colors.YELLOW)}")
        for name in comparison['only_in_existing'][:10]:
            print(f"    ? {name}")
        if len(comparison['only_in_existing']) > 10:
            print(f"    ... and {len(comparison['only_in_existing']) - 10} more")

    # Property mismatches
    if comparison['property_mismatches']:
        print(f"\n  {color('Property mismatches:', Colors.RED)}")
        for diff in comparison['property_mismatches'][:5]:
            print(f"    {color('!', Colors.RED)} {diff['schema']}")
            if diff['only_in_generated']:
                print(f"      Code has: {diff['only_in_generated']}")
            if diff['only_in_existing']:
                print(f"      Schema has (not in code!): {diff['only_in_existing']}")
        if len(comparison['property_mismatches']) > 5:
            print(f"    ... and {len(comparison['property_mismatches']) - 5} more mismatches")


def print_stats(results: List[Dict], success: int, errors: int):
    """Print export statistics"""
    print_header("Export Statistics")

    print(f"\n  Total models: {success + errors}")
    print(f"  {color(f'Success: {success}', Colors.GREEN)}")
    if errors:
        print(f"  {color(f'Errors: {errors}', Colors.RED)}")

    # Properties per model
    props_list = [r['properties'] for r in results if r['status'] == 'success']
    if props_list:
        print(f"\n  Properties per model:")
        print(f"    Min: {min(props_list)}")
        print(f"    Max: {max(props_list)}")
        print(f"    Avg: {sum(props_list) / len(props_list):.1f}")


def main():
    parser = argparse.ArgumentParser(
        description="Export Pydantic models to JSON Schema (Code-First)"
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=Path,
        default=PROJECT_ROOT / "specs" / "data" / "generated",
        help="Output directory for generated schemas"
    )
    parser.add_argument(
        "--compare", "-c",
        action="store_true",
        help="Compare with existing specs/data/ schemas"
    )
    parser.add_argument(
        "--stats", "-s",
        action="store_true",
        help="Show detailed statistics"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args()

    print_header("Pydantic → JSON Schema Exporter")
    print(f"  Output: {args.output_dir}")
    print(f"  Code-First Principle: 代码是唯一的事实来源！")

    # Export schemas
    print("\n  Discovering Pydantic models...")
    success, errors, results = export_schemas(args.output_dir)

    # Stats
    if args.stats:
        print_stats(results, success, errors)

    # Compare with existing
    if args.compare:
        existing_dir = PROJECT_ROOT / "specs" / "data"
        if existing_dir.exists():
            comparison = compare_schemas(args.output_dir, existing_dir)

            if args.json:
                print(json.dumps(comparison, indent=2))
            else:
                print_comparison_report(comparison)
        else:
            print(f"\n  {color('Warning:', Colors.YELLOW)} specs/data/ not found, skipping comparison")

    # JSON output
    if args.json:
        output = {
            'success': success,
            'errors': errors,
            'results': results,
            'output_dir': str(args.output_dir),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"\n  {color('[OK]', Colors.GREEN)} Exported {success} schemas to {args.output_dir}")
        if errors:
            print(f"  {color('!', Colors.YELLOW)} {errors} models failed to export")

    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
