#!/usr/bin/env python3
"""
Story Status YAML Sync Validator
Part of BMad Issue #1015 Fix - Phase 3.2

Validates that when Story files are committed, the canvas-project-status.yaml
story_statuses section is also updated to match.

Usage:
    python scripts/validate-story-status-yaml-sync.py

Exit codes:
    0 - Validation passed
    1 - Validation failed (warnings only, does not block)
"""

import re
import sys
import subprocess
from pathlib import Path
from typing import Optional, Dict

# Configuration
YAML_PATH = Path(".bmad-core/data/canvas-project-status.yaml")
STORY_PATH = Path("docs/stories")

# Status mapping from various formats to kebab-case
STATUS_MAP = {
    'done': 'done',
    'complete': 'done',
    'completed': 'done',
    '✅ done': 'done',
    '✅ complete': 'done',
    '**complete**': 'done',
    'draft': 'draft',
    'approved': 'approved',
    '**approved**': 'approved',
    'ready': 'ready-for-dev',
    'ready for development': 'ready-for-dev',
    'ready for dev': 'ready-for-dev',
    'in progress': 'in-progress',
    'in development': 'in-progress',
    '🔄 in development': 'in-progress',
    'review': 'ready-for-review',
    'ready for review': 'ready-for-review',
    'in review': 'in-review',
    'blocked': 'blocked',
}


def get_staged_files() -> list:
    """Get list of staged files from git."""
    try:
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only'],
            capture_output=True,
            text=True,
            check=True
        )
        return [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
    except subprocess.CalledProcessError:
        return []


def extract_story_id(filename: str) -> Optional[str]:
    """Extract story ID from filename (e.g., '30.4' from '30.4.story.md')."""
    match = re.search(r'(\d+\.\d+)', filename)
    if match:
        return match.group(1)
    return None


def extract_status_from_story(filepath: Path) -> Optional[str]:
    """Extract status from Story file content."""
    if not filepath.exists():
        return None

    content = filepath.read_text(encoding='utf-8')

    # Pattern 1: status: value (kebab-case format)
    match = re.search(r'^status:\s*(.+)$', content, re.MULTILINE)
    if match:
        return match.group(1).strip().lower()

    # Pattern 2: ## Status section with value on next line
    match = re.search(r'## Status\s*\n+([^\n#]+)', content, re.DOTALL)
    if match:
        status_line = match.group(1).strip()
        # Clean up common patterns
        status_line = re.sub(r'^\*\*Status\*\*:\s*', '', status_line)
        status_line = re.sub(r'^Status:\s*', '', status_line)
        status_line = re.sub(r'\s*\(.*\)$', '', status_line)  # Remove parenthetical notes
        return status_line.strip().lower()

    # Pattern 3: Status: value in any format
    match = re.search(r'^\*?\*?Status\*?\*?:\s*(.+)$', content, re.MULTILINE)
    if match:
        status_line = match.group(1).strip()
        status_line = re.sub(r'\s*\(.*\)$', '', status_line)
        return status_line.strip().lower()

    return None


def normalize_status(status: Optional[str]) -> Optional[str]:
    """Normalize status to kebab-case."""
    if not status:
        return None

    status_lower = status.lower().strip()

    # Direct lookup
    if status_lower in STATUS_MAP:
        return STATUS_MAP[status_lower]

    # If already kebab-case, return as-is
    if re.match(r'^[a-z][a-z0-9-]*$', status_lower):
        return status_lower

    # Convert to kebab-case
    result = re.sub(r'[^\w\s-]', '', status_lower)
    result = re.sub(r'\s+', '-', result)
    return result


def get_yaml_statuses() -> Dict[str, str]:
    """Extract story statuses from YAML file."""
    statuses = {}

    if not YAML_PATH.exists():
        return statuses

    content = YAML_PATH.read_text(encoding='utf-8')

    # Simple pattern matching for story_statuses section
    in_story_statuses = False
    current_story_id = None

    for line in content.split('\n'):
        if line.strip() == 'story_statuses:':
            in_story_statuses = True
            continue

        if in_story_statuses:
            # End of section
            if line and not line.startswith(' ') and not line.startswith('#'):
                break

            # Story ID line
            story_match = re.match(r'\s+"?(\d+\.\d+)"?:\s*$', line)
            if story_match:
                current_story_id = story_match.group(1)
                continue

            # Status line
            if current_story_id:
                status_match = re.match(r'\s+status:\s*(\S+)', line)
                if status_match:
                    statuses[current_story_id] = status_match.group(1)
                    current_story_id = None

    return statuses


def main():
    print("🔍 Story Status YAML Sync Validator (BMad Issue #1015 Fix)")
    print("=" * 60)

    # Get staged files
    staged_files = get_staged_files()

    # Filter story files
    story_files = [f for f in staged_files if f.startswith('docs/stories/') and f.endswith('.md')]
    yaml_staged = YAML_PATH.as_posix() in staged_files

    if not story_files:
        print("✅ No story files in commit, skipping validation")
        return 0

    print(f"\n📝 Story files being committed: {len(story_files)}")
    for f in story_files:
        print(f"   - {f}")

    # Check if YAML is also staged
    if not yaml_staged:
        print("\n⚠️  WARNING: Story files changed but canvas-project-status.yaml not staged")
        print("\n   Story status should be synced to YAML when Story files change.")
        print("   Consider running: scripts/validate-story-status-sync.ps1")
        print("\n   To include YAML in this commit:")
        print(f"   git add {YAML_PATH}")
        print("\n   To skip this check: git commit --no-verify")
        # Warning only, don't block
        return 0

    print("\n✅ Both story files and YAML are staged - checking consistency...")

    # Load YAML statuses
    yaml_statuses = get_yaml_statuses()

    # Check each story file
    mismatches = []
    for story_file in story_files:
        story_id = extract_story_id(story_file)
        if not story_id:
            continue

        filepath = Path(story_file)
        file_status = normalize_status(extract_status_from_story(filepath))
        yaml_status = yaml_statuses.get(story_id)

        if file_status and yaml_status and file_status != yaml_status:
            mismatches.append({
                'story_id': story_id,
                'file_status': file_status,
                'yaml_status': yaml_status
            })
        elif file_status and not yaml_status:
            print(f"   ⚠️  {story_id}: Not in YAML story_statuses (file: {file_status})")

    if mismatches:
        print("\n❌ Status mismatches found:")
        for m in mismatches:
            print(f"   {m['story_id']}: file='{m['file_status']}' vs yaml='{m['yaml_status']}'")
        print("\n   Please ensure Story file and YAML statuses match.")
        # Warning only, don't block
        return 0

    print("\n✅ Validation passed - statuses are consistent")
    return 0


if __name__ == '__main__':
    sys.exit(main())
