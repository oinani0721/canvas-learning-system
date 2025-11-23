#!/usr/bin/env python3
"""
Validate Parallel Stories
检查Stories是否可以安全地并行开发（无文件冲突）
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple

sys.path.insert(0, str(Path(__file__).parent / "lib"))

from planning_utils import (
    get_project_root,
    print_status
)

def get_story_path(story_id: str) -> Path:
    """获取Story文件路径"""
    root = get_project_root()
    # 尝试不同的命名格式
    patterns = [
        f"docs/stories/story-{story_id}.md",
        f"docs/stories/{story_id}.md",
        f"docs/stories/story_{story_id.replace('.', '_')}.md"
    ]

    for pattern in patterns:
        path = root / pattern
        if path.exists():
            return path

    return root / f"docs/stories/story-{story_id}.md"

def extract_affected_files(story_path: Path) -> Set[str]:
    """从Story文件提取受影响的文件列表"""
    affected = set()

    if not story_path.exists():
        return affected

    content = story_path.read_text(encoding='utf-8')

    # 查找 "Affected Files" 或 "Files to Modify" 等section
    in_files_section = False
    for line in content.split('\n'):
        line_lower = line.lower()

        if any(keyword in line_lower for keyword in ['affected files', 'files to modify', 'related files']):
            in_files_section = True
            continue

        if in_files_section:
            if line.startswith('#'):  # 新section开始
                in_files_section = False
                continue

            # 提取文件路径
            if line.strip().startswith('-') or line.strip().startswith('*'):
                file_path = line.strip().lstrip('-*').strip()
                # 清理markdown格式
                file_path = file_path.strip('`').split('(')[0].strip()
                if file_path and '.' in file_path:
                    affected.add(file_path)

    # 如果没找到显式列表，尝试从Dev Notes提取
    if not affected:
        # 查找代码块中的文件引用
        import re
        file_patterns = re.findall(r'`(src/[^`]+\.py)`|`(tests/[^`]+\.py)`', content)
        for matches in file_patterns:
            for match in matches:
                if match:
                    affected.add(match)

    return affected

def find_conflicts(stories: List[str]) -> List[Tuple[str, str, str]]:
    """
    查找Stories之间的文件冲突

    Returns:
        List of (story1, story2, conflicting_file) tuples
    """
    conflicts = []

    # 收集每个Story的受影响文件
    story_files: Dict[str, Set[str]] = {}

    for story_id in stories:
        story_path = get_story_path(story_id)
        story_files[story_id] = extract_affected_files(story_path)

    # 两两比较
    story_list = list(stories)
    for i in range(len(story_list)):
        for j in range(i + 1, len(story_list)):
            story1 = story_list[i]
            story2 = story_list[j]

            common_files = story_files[story1] & story_files[story2]
            for file in common_files:
                conflicts.append((story1, story2, file))

    return conflicts

def validate_stories_exist(stories: List[str]) -> List[str]:
    """验证Story文件存在"""
    missing = []
    for story_id in stories:
        story_path = get_story_path(story_id)
        if not story_path.exists():
            missing.append(story_id)
    return missing

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate Stories can be developed in parallel"
    )
    parser.add_argument(
        '--stories',
        type=str,
        required=True,
        help='Comma-separated list of Story IDs (e.g., "13.1,13.2,13.4")'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON'
    )

    args = parser.parse_args()

    # 解析Story列表
    stories = [s.strip() for s in args.stories.split(',')]

    print("="*60)
    print("🔍 Parallel Stories Validation")
    print("="*60)

    print_status(f"Checking {len(stories)} stories: {', '.join(stories)}", "info")

    # 检查Story文件存在
    missing = validate_stories_exist(stories)
    if missing:
        print_status(f"Stories not found: {', '.join(missing)}", "warning")

    # 查找冲突
    conflicts = find_conflicts(stories)

    result = {
        "stories": stories,
        "conflicts": [
            {"story1": c[0], "story2": c[1], "file": c[2]}
            for c in conflicts
        ],
        "safe_to_parallelize": len(conflicts) == 0
    }

    if args.json:
        print(json.dumps(result, indent=2))
        return 0 if result["safe_to_parallelize"] else 1

    # 输出结果
    print("\n" + "="*60)

    if conflicts:
        print("⚠️ Conflicts Detected!")
        print("="*60)

        for story1, story2, file in conflicts:
            print(f"\n❌ {story1} ↔ {story2}")
            print(f"   Conflict on: {file}")

        # 建议安全的分组
        safe_stories = set(stories)
        for c in conflicts:
            # 简单策略：移除第二个冲突的Story
            if c[1] in safe_stories:
                safe_stories.discard(c[1])

        print(f"\n📋 Suggested safe set: {', '.join(sorted(safe_stories))}")
        return 1
    else:
        print("✅ Safe to Parallelize!")
        print("="*60)
        print(f"\nAll {len(stories)} stories can be developed in parallel.")
        print("\nNext step: Run `*init \"{args.stories}\"`")
        return 0

if __name__ == "__main__":
    sys.exit(main())
