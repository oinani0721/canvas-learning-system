#!/usr/bin/env python3
"""
Canvas Learning System - OpenAPI Specification Export Script

自动从 FastAPI 应用导出 OpenAPI 规范，并进行版本控制友好的格式化。

Usage:
    python scripts/spec-tools/export-openapi.py [--output OUTPUT] [--format FORMAT]

Examples:
    python scripts/spec-tools/export-openapi.py
    python scripts/spec-tools/export-openapi.py --output specs/api/openapi.json
    python scripts/spec-tools/export-openapi.py --format yaml --output openapi.yaml
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))


def export_openapi(output_path: str = "openapi.json", format_type: str = "json") -> dict:
    """
    Export OpenAPI specification from FastAPI application.

    Args:
        output_path: Path to save the specification
        format_type: Output format (json or yaml)

    Returns:
        dict: The OpenAPI specification
    """
    from app.main import app

    # Get OpenAPI schema
    schema = app.openapi()

    # Add metadata
    schema["info"]["x-generated-at"] = datetime.now(timezone.utc).isoformat()
    schema["info"]["x-generator"] = "Canvas Learning System OpenAPI Exporter"

    # Ensure output directory exists
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    if format_type == "yaml":
        try:
            import yaml
            with open(output, "w", encoding="utf-8") as f:
                yaml.dump(schema, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        except ImportError:
            print("Warning: PyYAML not installed. Falling back to JSON.")
            format_type = "json"

    if format_type == "json":
        with open(output, "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)

    return schema


def analyze_spec(schema: dict) -> dict:
    """
    Analyze the OpenAPI specification and return statistics.

    Args:
        schema: OpenAPI specification dict

    Returns:
        dict: Statistics about the specification
    """
    paths = schema.get("paths", {})
    components = schema.get("components", {})
    schemas = components.get("schemas", {})

    # Count operations by method
    methods = {}
    tags = set()
    for path, operations in paths.items():
        for method, operation in operations.items():
            if method in ["get", "post", "put", "patch", "delete"]:
                methods[method] = methods.get(method, 0) + 1
                if "tags" in operation:
                    tags.update(operation["tags"])

    return {
        "version": schema.get("openapi", "unknown"),
        "title": schema.get("info", {}).get("title", "unknown"),
        "api_version": schema.get("info", {}).get("version", "unknown"),
        "paths_count": len(paths),
        "schemas_count": len(schemas),
        "operations": methods,
        "total_operations": sum(methods.values()),
        "tags": sorted(tags),
    }


def compare_specs(old_path: str, new_schema: dict) -> dict:
    """
    Compare old and new specifications.

    Args:
        old_path: Path to old specification
        new_schema: New specification dict

    Returns:
        dict: Comparison results
    """
    old_path = Path(old_path)
    if not old_path.exists():
        return {"status": "new", "message": "No existing specification found"}

    with open(old_path, "r", encoding="utf-8") as f:
        old_schema = json.load(f)

    old_paths = set(old_schema.get("paths", {}).keys())
    new_paths = set(new_schema.get("paths", {}).keys())

    old_schemas = set(old_schema.get("components", {}).get("schemas", {}).keys())
    new_schemas = set(new_schema.get("components", {}).get("schemas", {}).keys())

    return {
        "status": "changed" if old_paths != new_paths or old_schemas != new_schemas else "unchanged",
        "paths": {
            "added": sorted(new_paths - old_paths),
            "removed": sorted(old_paths - new_paths),
            "unchanged": len(old_paths & new_paths),
        },
        "schemas": {
            "added": sorted(new_schemas - old_schemas),
            "removed": sorted(old_schemas - new_schemas),
            "unchanged": len(old_schemas & new_schemas),
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description="Export OpenAPI specification from Canvas Learning System"
    )
    parser.add_argument(
        "--output", "-o",
        default="openapi.json",
        help="Output file path (default: openapi.json)"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["json", "yaml"],
        default="json",
        help="Output format (default: json)"
    )
    parser.add_argument(
        "--compare", "-c",
        action="store_true",
        help="Compare with existing specification"
    )
    parser.add_argument(
        "--stats", "-s",
        action="store_true",
        help="Print specification statistics"
    )

    args = parser.parse_args()

    print(f"Exporting OpenAPI specification to {args.output}...")

    try:
        schema = export_openapi(args.output, args.format)
        print(f"Successfully exported to {args.output}")

        if args.stats:
            stats = analyze_spec(schema)
            print("\n=== Specification Statistics ===")
            print(f"  OpenAPI Version: {stats['version']}")
            print(f"  API Title: {stats['title']}")
            print(f"  API Version: {stats['api_version']}")
            print(f"  Paths: {stats['paths_count']}")
            print(f"  Schemas: {stats['schemas_count']}")
            print(f"  Total Operations: {stats['total_operations']}")
            print(f"  Operations by method:")
            for method, count in stats['operations'].items():
                print(f"    - {method.upper()}: {count}")
            print(f"  Tags: {', '.join(stats['tags'])}")

        if args.compare:
            comparison = compare_specs(args.output, schema)
            print(f"\n=== Comparison with Existing Spec ===")
            print(f"  Status: {comparison['status']}")
            if comparison['status'] == "changed":
                if comparison['paths']['added']:
                    print(f"  New paths: {', '.join(comparison['paths']['added'])}")
                if comparison['paths']['removed']:
                    print(f"  Removed paths: {', '.join(comparison['paths']['removed'])}")
                if comparison['schemas']['added']:
                    print(f"  New schemas: {', '.join(comparison['schemas']['added'])}")
                if comparison['schemas']['removed']:
                    print(f"  Removed schemas: {', '.join(comparison['schemas']['removed'])}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
