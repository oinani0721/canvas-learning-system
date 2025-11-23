#!/usr/bin/env python3
"""
Check status of all parallel development worktrees.

Usage:
    python check-worktree-status.py
    python check-worktree-status.py --json
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml


def get_worktrees() -> List[Dict[str, str]]:
    """Get list of Git worktrees."""
    result = subprocess.run(
        ['git', 'worktree', 'list', '--porcelain'],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return []

    worktrees = []
    current = {}

    for line in result.stdout.split('\n'):
        if line.startswith('worktree '):
            if current:
                worktrees.append(current)
            current = {'path': line[9:]}
        elif line.startswith('HEAD '):
            current['head'] = line[5:]
        elif line.startswith('branch '):
            current['branch'] = line[7:]
        elif line == 'detached':
            current['detached'] = True

    if current:
        worktrees.append(current)

    return worktrees


def read_worktree_status(worktree_path: Path) -> Optional[Dict]:
    """Read .worktree-status.yaml from a worktree."""
    status_file = worktree_path / '.worktree-status.yaml'

    if not status_file.exists():
        return None

    try:
        with open(status_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Warning: Could not read {status_file}: {e}", file=sys.stderr)
        return None


def get_worktree_activity(worktree_path: Path) -> str:
    """Get last activity time for a worktree."""
    try:
        result = subprocess.run(
            ['git', '-C', str(worktree_path), 'log', '-1', '--format=%cr'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "unknown"


def get_commit_count(worktree_path: Path, base_branch: str = 'main') -> int:
    """Get number of commits ahead of base branch."""
    try:
        result = subprocess.run(
            ['git', '-C', str(worktree_path), 'rev-list', '--count', f'{base_branch}..HEAD'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return int(result.stdout.strip())
    except Exception:
        pass
    return 0


def main():
    parser = argparse.ArgumentParser(description='Check worktree status')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--base-path', help='Base path for worktrees')
    args = parser.parse_args()

    # Get all worktrees
    worktrees = get_worktrees()

    # Filter to development worktrees
    dev_worktrees = []
    for wt in worktrees:
        path = Path(wt['path'])
        branch = wt.get('branch', '')

        # Check if it's a development worktree
        if 'develop-' in str(path) or 'develop-story-' in branch:
            status = read_worktree_status(path)

            dev_worktrees.append({
                'path': str(path),
                'name': path.name,
                'branch': branch,
                'story_id': status.get('story_id', 'unknown') if status else 'unknown',
                'status': status.get('status', 'unknown') if status else 'unknown',
                'tests_passed': status.get('tests_passed', False) if status else False,
                'qa_reviewed': status.get('qa_reviewed', False) if status else False,
                'qa_gate': status.get('qa_gate', None) if status else None,
                'last_activity': get_worktree_activity(path),
                'commits': get_commit_count(path),
            })

    if args.json:
        print(json.dumps(dev_worktrees, indent=2))
    else:
        if not dev_worktrees:
            print("No active parallel development worktrees found.")
            return

        print("## Parallel Development Status\n")
        print("### Active Worktrees\n")
        print("| Worktree | Story | Status | Tests | QA Gate | Ready |")
        print("|----------|-------|--------|-------|---------|-------|")

        ready_to_merge = 0
        dev_complete = 0
        qa_reviewing = 0
        in_progress = 0

        for wt in dev_worktrees:
            status_icon = "✅" if wt['status'] == 'ready-to-merge' else "🔄"
            tests_icon = "Passed" if wt['tests_passed'] else "Not Run"
            qa_gate = wt['qa_gate'] if wt['qa_gate'] else "-"
            ready = "✅" if wt['status'] == 'ready-to-merge' else "❌"

            if wt['status'] == 'ready-to-merge':
                ready_to_merge += 1
            elif wt['status'] == 'qa-reviewing':
                qa_reviewing += 1
            elif wt['status'] == 'dev-complete':
                dev_complete += 1
            else:
                in_progress += 1

            print(f"| {wt['name']} | {wt['story_id']} | {status_icon} {wt['status']} | {tests_icon} | {qa_gate} | {ready} |")

        print(f"\n### Summary")
        print(f"- **Total**: {len(dev_worktrees)} worktrees")
        print(f"- **Ready to Merge**: {ready_to_merge}")
        print(f"- **QA Reviewing**: {qa_reviewing}")
        print(f"- **Dev Complete**: {dev_complete}")
        print(f"- **In Progress**: {in_progress}")


if __name__ == '__main__':
    main()
