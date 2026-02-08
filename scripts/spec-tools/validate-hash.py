#!/usr/bin/env python3
"""
Canvas Learning System - API Spec Hash Validator

验证 ADR 文档中引用的 api_spec_hash 与当前 OpenAPI 规范的哈希值一致。
用于检测规范变更后 ADR 是否需要更新。

Usage:
    python scripts/spec-tools/validate-hash.py [--update]

Examples:
    python scripts/spec-tools/validate-hash.py          # 检查一致性
    python scripts/spec-tools/validate-hash.py --update # 更新 ADR 中的哈希
"""

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


def color(text: str, c: str) -> str:
    """Add color to text"""
    if os.environ.get('NO_COLOR'):
        return text
    return f"{c}{text}{Colors.END}"


def compute_spec_hash(spec_path: Path) -> str:
    """Compute SHA256 hash of OpenAPI spec (normalized)"""
    if not spec_path.exists():
        return ""

    with open(spec_path, 'r', encoding='utf-8') as f:
        spec = json.load(f)

    # Remove volatile fields for stable hashing
    if 'info' in spec:
        spec['info'].pop('x-generated-at', None)

    # Normalize and hash
    normalized = json.dumps(spec, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:16]


def find_adr_files(docs_dir: Path) -> List[Path]:
    """Find all ADR markdown files"""
    adr_patterns = [
        docs_dir / "architecture" / "decisions" / "*.md",
        docs_dir / "adr" / "*.md",
        docs_dir / "ADR*.md",
    ]

    files = []
    for pattern in adr_patterns:
        files.extend(pattern.parent.glob(pattern.name) if pattern.parent.exists() else [])

    return files


def extract_spec_hash_from_adr(adr_path: Path) -> Optional[str]:
    """Extract api_spec_hash from ADR file"""
    content = adr_path.read_text(encoding='utf-8')

    # Look for various patterns
    patterns = [
        r'api_spec_hash:\s*["\']?([a-f0-9]+)["\']?',
        r'spec_hash:\s*["\']?([a-f0-9]+)["\']?',
        r'openapi_hash:\s*["\']?([a-f0-9]+)["\']?',
        r'\[api_spec_hash\]:\s*([a-f0-9]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group(1)

    return None


def update_adr_hash(adr_path: Path, old_hash: str, new_hash: str) -> bool:
    """Update the hash in an ADR file"""
    content = adr_path.read_text(encoding='utf-8')

    # Replace old hash with new
    patterns = [
        (r'(api_spec_hash:\s*["\']?)' + old_hash + r'(["\']?)',
         r'\g<1>' + new_hash + r'\g<2>'),
        (r'(spec_hash:\s*["\']?)' + old_hash + r'(["\']?)',
         r'\g<1>' + new_hash + r'\g<2>'),
        (r'(openapi_hash:\s*["\']?)' + old_hash + r'(["\']?)',
         r'\g<1>' + new_hash + r'\g<2>'),
    ]

    updated = False
    for pattern, replacement in patterns:
        new_content, count = re.subn(pattern, replacement, content, flags=re.IGNORECASE)
        if count > 0:
            content = new_content
            updated = True

    if updated:
        adr_path.write_text(content, encoding='utf-8')

    return updated


def validate_spec_hashes(project_root: Path, update: bool = False) -> Tuple[bool, List[dict]]:
    """
    Validate all ADR spec hashes against current OpenAPI spec.

    Returns:
        Tuple of (all_valid, list of validation results)
    """
    spec_path = project_root / "openapi.json"
    docs_dir = project_root / "docs"

    current_hash = compute_spec_hash(spec_path)
    if not current_hash:
        return False, [{
            'file': str(spec_path),
            'status': 'error',
            'message': 'OpenAPI spec not found'
        }]

    results = []
    all_valid = True
    adr_files = find_adr_files(docs_dir)

    for adr_path in adr_files:
        adr_hash = extract_spec_hash_from_adr(adr_path)

        if adr_hash is None:
            # No hash in this ADR, skip
            continue

        relative_path = adr_path.relative_to(project_root)

        if adr_hash == current_hash:
            results.append({
                'file': str(relative_path),
                'status': 'valid',
                'hash': adr_hash,
                'message': 'Hash matches current spec'
            })
        else:
            all_valid = False
            if update:
                if update_adr_hash(adr_path, adr_hash, current_hash):
                    results.append({
                        'file': str(relative_path),
                        'status': 'updated',
                        'old_hash': adr_hash,
                        'new_hash': current_hash,
                        'message': 'Hash updated to match current spec'
                    })
                else:
                    results.append({
                        'file': str(relative_path),
                        'status': 'error',
                        'hash': adr_hash,
                        'expected': current_hash,
                        'message': 'Failed to update hash'
                    })
            else:
                results.append({
                    'file': str(relative_path),
                    'status': 'mismatch',
                    'hash': adr_hash,
                    'expected': current_hash,
                    'message': f'Hash mismatch: ADR has {adr_hash}, spec has {current_hash}'
                })

    return all_valid, results


def generate_report(current_hash: str, results: List[dict]) -> str:
    """Generate validation report"""
    lines = []
    lines.append("=" * 60)
    lines.append("API Spec Hash Validation Report")
    lines.append("=" * 60)
    lines.append(f"Current OpenAPI Spec Hash: {color(current_hash, Colors.BLUE)}")
    lines.append("")

    valid_count = sum(1 for r in results if r['status'] == 'valid')
    mismatch_count = sum(1 for r in results if r['status'] == 'mismatch')
    updated_count = sum(1 for r in results if r['status'] == 'updated')
    error_count = sum(1 for r in results if r['status'] == 'error')

    if results:
        lines.append("## ADR Hash Validations")
        for result in results:
            status = result['status']
            if status == 'valid':
                icon = color('✓', Colors.GREEN)
            elif status == 'updated':
                icon = color('↑', Colors.YELLOW)
            elif status == 'mismatch':
                icon = color('✗', Colors.RED)
            else:
                icon = color('!', Colors.RED)

            lines.append(f"  {icon} {result['file']}")
            lines.append(f"      {result['message']}")
    else:
        lines.append("No ADR files with api_spec_hash found.")

    lines.append("")
    lines.append("=" * 60)
    lines.append("Summary:")
    lines.append(f"  Valid: {valid_count}")
    lines.append(f"  Mismatched: {mismatch_count}")
    lines.append(f"  Updated: {updated_count}")
    lines.append(f"  Errors: {error_count}")

    if mismatch_count > 0:
        lines.append("")
        lines.append(color("WARNING: Some ADR files reference outdated API specs!", Colors.RED))
        lines.append("Run with --update to fix, or manually review the ADRs.")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Validate API spec hashes in ADR documents"
    )
    parser.add_argument(
        "--update", "-u",
        action="store_true",
        help="Update mismatched hashes in ADR files"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent.parent
    spec_path = project_root / "openapi.json"

    current_hash = compute_spec_hash(spec_path)
    all_valid, results = validate_spec_hashes(project_root, update=args.update)

    if args.json:
        output = {
            'current_spec_hash': current_hash,
            'all_valid': all_valid,
            'results': results,
        }
        print(json.dumps(output, indent=2))
    else:
        report = generate_report(current_hash, results)
        print(report)

    sys.exit(0 if all_valid else 1)


if __name__ == "__main__":
    main()
