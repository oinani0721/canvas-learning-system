#!/usr/bin/env python3
"""
Analyze Story dependencies to identify file conflicts for parallel development.

Usage:
    python analyze-story-conflicts.py --stories "13.1,13.2,13.3,13.4"
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


def parse_story_files(story_id: str, stories_dir: Path) -> Set[str]:
    """Extract files to modify from a Story file."""
    story_file = stories_dir / f"story-{story_id}.md"

    if not story_file.exists():
        print(f"Warning: Story file not found: {story_file}", file=sys.stderr)
        return set()

    content = story_file.read_text(encoding='utf-8')
    files = set()

    # Look for "Files to Modify" or similar sections
    patterns = [
        r'##.*Files.*to.*Modify.*\n((?:[-*]\s+`?[\w/._-]+`?\n?)+)',
        r'##.*Technical.*Notes.*\n.*?(?:files?|modify).*?:((?:\s*[-*]\s+`?[\w/._-]+`?\n?)+)',
        r'`(src/[\w/._-]+\.py)`',
        r'`(tests/[\w/._-]+\.py)`',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            if isinstance(match, str):
                # Extract individual file paths
                file_matches = re.findall(r'`?([\w/._-]+\.py)`?', match)
                files.update(file_matches)

    return files


def find_conflicts(story_files: Dict[str, Set[str]]) -> List[Tuple[str, str, Set[str]]]:
    """Find file conflicts between Stories."""
    conflicts = []
    story_ids = list(story_files.keys())

    for i, story_a in enumerate(story_ids):
        for story_b in story_ids[i+1:]:
            common_files = story_files[story_a] & story_files[story_b]
            if common_files:
                conflicts.append((story_a, story_b, common_files))

    return conflicts


def recommend_parallel_groups(
    story_ids: List[str],
    conflicts: List[Tuple[str, str, Set[str]]]
) -> List[List[str]]:
    """Recommend parallel groups avoiding conflicts."""
    # Build conflict graph
    conflict_pairs = {(a, b) for a, b, _ in conflicts}
    conflict_pairs.update((b, a) for a, b, _ in conflicts)

    # Greedy grouping
    groups = []
    remaining = set(story_ids)

    while remaining:
        group = []
        for story in list(remaining):
            # Check if story conflicts with any in current group
            conflicts_with_group = any(
                (story, g) in conflict_pairs or (g, story) in conflict_pairs
                for g in group
            )
            if not conflicts_with_group:
                group.append(story)
                remaining.remove(story)

        if group:
            groups.append(group)
        else:
            # Shouldn't happen, but prevent infinite loop
            break

    return groups


def main():
    parser = argparse.ArgumentParser(description='Analyze Story conflicts')
    parser.add_argument('--stories', required=True, help='Comma-separated Story IDs')
    parser.add_argument('--stories-dir', default='docs/stories', help='Stories directory')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    args = parser.parse_args()

    # Parse arguments
    story_ids = [s.strip() for s in args.stories.split(',')]
    stories_dir = Path(args.stories_dir)

    if not stories_dir.exists():
        print(f"Error: Stories directory not found: {stories_dir}", file=sys.stderr)
        sys.exit(1)

    # Analyze each Story
    story_files = {}
    for story_id in story_ids:
        files = parse_story_files(story_id, stories_dir)
        story_files[story_id] = files

    # Find conflicts
    conflicts = find_conflicts(story_files)

    # Get recommendations
    groups = recommend_parallel_groups(story_ids, conflicts)

    if args.json:
        result = {
            'story_files': {k: list(v) for k, v in story_files.items()},
            'conflicts': [(a, b, list(f)) for a, b, f in conflicts],
            'recommended_groups': groups,
        }
        print(json.dumps(result, indent=2))
    else:
        # Print report
        print("## Story Dependency Analysis\n")

        print("### File Modification Map\n")
        print("| Story | Files to Modify |")
        print("|-------|-----------------|")
        for story_id, files in story_files.items():
            files_str = ", ".join(sorted(files)) if files else "(none detected)"
            print(f"| {story_id} | {files_str} |")

        print("\n### Conflicts\n")
        if conflicts:
            for story_a, story_b, common in conflicts:
                print(f"❌ {story_a} ↔ {story_b}: {', '.join(common)}")
        else:
            print("✅ No conflicts detected")

        print("\n### Recommended Parallel Groups\n")
        for i, group in enumerate(groups, 1):
            print(f"Group {i}: {', '.join(group)}")


if __name__ == '__main__':
    main()
