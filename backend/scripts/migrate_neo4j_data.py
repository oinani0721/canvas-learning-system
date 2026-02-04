#!/usr/bin/env python3
"""
Neo4j数据迁移脚本 - 清理Unicode乱码
Story 30.1 - AC 3

Usage:
    python migrate_neo4j_data.py --dry-run   # 预览变更
    python migrate_neo4j_data.py             # 执行迁移
    python migrate_neo4j_data.py --force     # 跳过确认

[Source: docs/stories/30.1.story.md - Task 3]
"""

import json
import shutil
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Tuple

# Try to import ftfy for better Unicode fixing
try:
    import ftfy
    HAS_FTFY = True
except ImportError:
    HAS_FTFY = False
    print("Warning: ftfy not installed. Using basic Unicode cleaning.")
    print("Install with: pip install ftfy>=6.0.0")

# Default paths
SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR.parent
DEFAULT_SOURCE = BACKEND_DIR / "data" / "neo4j_memory.json"


def fix_unicode_garbage(text: str) -> str:
    """
    修复Unicode乱码.

    Args:
        text: 可能包含乱码的文本

    Returns:
        修复后的文本
    """
    if not isinstance(text, str):
        return text

    if HAS_FTFY:
        # ftfy provides comprehensive Unicode fixing
        return ftfy.fix_text(text)

    # Fallback: Basic cleaning - remove invalid characters
    try:
        # Try to encode and decode to remove invalid sequences
        return text.encode('utf-8', errors='ignore').decode('utf-8')
    except Exception:
        return text


def _fix_recursive(obj: Any) -> Any:
    """
    递归修复所有字符串值.

    Args:
        obj: 任意JSON对象（dict, list, str, number, bool, None）

    Returns:
        修复后的对象
    """
    if isinstance(obj, str):
        return fix_unicode_garbage(obj)
    elif isinstance(obj, dict):
        return {k: _fix_recursive(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_fix_recursive(item) for item in obj]
    return obj


def analyze_unicode_issues(data: Any, path: str = "") -> List[Tuple[str, str, str]]:
    """
    分析数据中的Unicode问题.

    Args:
        data: 要分析的数据
        path: 当前JSON路径

    Returns:
        List of (path, original, fixed) tuples for changed values
    """
    issues = []

    if isinstance(data, str):
        fixed = fix_unicode_garbage(data)
        if fixed != data:
            issues.append((path, data[:100], fixed[:100]))
    elif isinstance(data, dict):
        for k, v in data.items():
            issues.extend(analyze_unicode_issues(v, f"{path}.{k}" if path else k))
    elif isinstance(data, list):
        for i, item in enumerate(data):
            issues.extend(analyze_unicode_issues(item, f"{path}[{i}]"))

    return issues


def migrate_json_data(source: Path, dry_run: bool = False, force: bool = False) -> Dict:
    """
    执行JSON数据迁移.

    Args:
        source: 源JSON文件路径
        dry_run: 是否为预览模式
        force: 是否跳过确认

    Returns:
        修复后的数据
    """
    print(f"\n{'=' * 60}")
    print(f"Neo4j Data Migration Script (Story 30.1)")
    print(f"{'=' * 60}")
    print(f"Source file: {source}")
    print(f"Mode: {'DRY RUN (preview only)' if dry_run else 'MIGRATION'}")
    print(f"ftfy installed: {'Yes' if HAS_FTFY else 'No (using basic cleaning)'}")
    print(f"{'=' * 60}\n")

    # Check if source exists
    if not source.exists():
        print(f"Error: Source file not found: {source}")
        sys.exit(1)

    # Read source file
    print(f"Reading source file...")
    with open(source, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in source file: {e}")
            sys.exit(1)

    # Analyze Unicode issues
    print(f"Analyzing Unicode issues...")
    issues = analyze_unicode_issues(data)

    print(f"\nFound {len(issues)} potential Unicode issues:")
    if issues:
        for i, (path, original, fixed) in enumerate(issues[:10]):  # Show first 10
            print(f"  [{i+1}] {path}")
            print(f"      Original: {repr(original)}")
            print(f"      Fixed:    {repr(fixed)}")
        if len(issues) > 10:
            print(f"  ... and {len(issues) - 10} more issues")
    else:
        print("  No Unicode issues found. Data appears clean.")

    # Fix the data
    print(f"\nApplying Unicode fixes...")
    fixed_data = _fix_recursive(data)

    if dry_run:
        print(f"\n[DRY RUN] No changes written to disk.")
        print(f"Run without --dry-run to apply changes.")
        return fixed_data

    # Confirm migration
    if not force and issues:
        response = input(f"\nProceed with migration? (y/N): ")
        if response.lower() != 'y':
            print("Migration cancelled.")
            sys.exit(0)

    # Backup original file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = source.with_suffix(f'.json.bak.{timestamp}')
    print(f"\nBacking up original file to: {backup_path}")
    shutil.copy2(source, backup_path)

    # Also create a simple .bak file (overwrites previous)
    simple_backup = source.with_suffix('.json.bak')
    shutil.copy2(source, simple_backup)
    print(f"Also backed up to: {simple_backup}")

    # Write fixed data
    print(f"\nWriting fixed data to: {source}")
    with open(source, 'w', encoding='utf-8') as f:
        json.dump(fixed_data, f, ensure_ascii=False, indent=2)

    # Verify the written file
    print(f"\nVerifying written file...")
    with open(source, 'r', encoding='utf-8') as f:
        verify_data = json.load(f)

    if verify_data == fixed_data:
        print(f"Verification: SUCCESS")
    else:
        print(f"Verification: FAILED - Data mismatch!")
        print(f"Restoring from backup...")
        shutil.copy2(backup_path, source)
        sys.exit(1)

    print(f"\n{'=' * 60}")
    print(f"Migration complete!")
    print(f"  - Original backup: {backup_path}")
    print(f"  - Fixed issues: {len(issues)}")
    print(f"{'=' * 60}\n")

    return fixed_data


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Migrate Neo4j JSON data - clean Unicode garbage (Story 30.1)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python migrate_neo4j_data.py --dry-run        Preview changes without modifying
  python migrate_neo4j_data.py                  Run migration with confirmation
  python migrate_neo4j_data.py --force          Run without confirmation prompt
  python migrate_neo4j_data.py --source custom.json   Migrate a custom file
        """
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing to disk"
    )

    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help=f"Source JSON file (default: {DEFAULT_SOURCE})"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt"
    )

    args = parser.parse_args()

    migrate_json_data(
        source=args.source,
        dry_run=args.dry_run,
        force=args.force
    )


if __name__ == "__main__":
    main()
