"""
PRD Story Extractor - 从PRD markdown文件中自动提取Story IDs

Author: Claude (Epic 20 补全计划 - Phase 0)
Date: 2025-12-12

Purpose:
    解决*epic-develop命令的Story遗漏问题。
    之前用户需要手动指定--stories参数，容易遗漏。
    现在系统可以自动从PRD文件中提取所有Story IDs。
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


def _version_sort_key(story_id: str) -> Tuple[int, int]:
    """
    版本号排序key - 使用tuple避免float精度问题

    float("23.10") = 23.1 = float("23.1"), 导致排序错误
    使用tuple: ("23.10") -> (23, 10), ("23.1") -> (23, 1)

    Args:
        story_id: Story ID (如 "20.1", "23.10")

    Returns:
        排序用的tuple (epic_id, story_number)
    """
    parts = story_id.split(".")
    return (int(parts[0]), int(parts[1]) if len(parts) > 1 else 0)


def extract_stories_from_prd(prd_file: Path) -> List[str]:
    """
    从PRD markdown文件中提取所有Story IDs

    支持的格式:
    1. ### Story 20.1: xxx
    2. ### Story-20.1: xxx
    3. **Story ID**: Story-20.1
    4. **Story ID**: Story 20.1

    Args:
        prd_file: PRD markdown文件路径

    Returns:
        排序后的Story ID列表，如 ["20.1", "20.2", "20.3", "20.4"]
        如果文件不存在或解析失败，返回空列表

    Example:
        >>> extract_stories_from_prd(Path("docs/prd/EPIC-20-XXX.md"))
        ['20.1', '20.2', '20.3', '20.4']
    """
    if not prd_file.exists():
        print(f"[PRD Parser] WARNING: PRD file not found: {prd_file}")
        return []

    try:
        content = prd_file.read_text(encoding='utf-8')
    except Exception as e:
        print(f"[PRD Parser] WARNING: Failed to read PRD file: {e}")
        return []

    # 多种匹配模式，覆盖不同的PRD格式
    patterns = [
        # Pattern 1: ### Story 20.1: xxx 或 ### Story-20.1: xxx
        r'###\s*Story[- ]?(\d+\.\d+)[:\s]',

        # Pattern 2: **Story ID**: Story-20.1 或 **Story ID**: Story 20.1
        r'\*\*Story ID\*\*:\s*Story[- ]?(\d+\.\d+)',

        # Pattern 3: Story ID: Story-20.1 (无bold)
        r'Story ID:\s*Story[- ]?(\d+\.\d+)',

        # Pattern 4: | Story 20.1 | 或 | 20.1 | (表格格式，但需要更谨慎)
        # 这个pattern可能匹配到版本号等，所以要求前面有Story关键词
        r'\|\s*Story[- ]?(\d+\.\d+)\s*\|',
    ]

    story_ids: Set[str] = set()

    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
        story_ids.update(matches)

    if not story_ids:
        print(f"[PRD Parser] WARNING: No stories found in PRD file: {prd_file.name}")
        return []

    # 按版本号排序 (20.1, 20.2, ..., 20.10) - 使用_version_sort_key
    sorted_ids = sorted(story_ids, key=_version_sort_key)

    print(f"[PRD Parser] OK: Extracted {len(sorted_ids)} stories from {prd_file.name}: {sorted_ids}")
    return sorted_ids


def validate_story_coverage(
    prd_file: Path,
    requested_stories: List[str]
) -> Dict[str, any]:
    """
    验证请求的Stories是否覆盖PRD中的所有Stories

    Args:
        prd_file: PRD markdown文件路径
        requested_stories: 用户请求处理的Story ID列表

    Returns:
        覆盖率报告字典:
        {
            "prd_stories": ["20.1", "20.2", "20.3", "20.4"],  # PRD中定义的所有Stories
            "requested_stories": ["20.1"],                    # 用户请求的Stories
            "missing_stories": ["20.2", "20.3", "20.4"],     # 遗漏的Stories
            "extra_stories": [],                              # 请求了但PRD中没有的Stories
            "is_complete": False                              # 是否完全覆盖
        }

    Example:
        >>> coverage = validate_story_coverage(
        ...     Path("docs/prd/EPIC-20-XXX.md"),
        ...     ["20.1"]
        ... )
        >>> print(coverage["missing_stories"])
        ['20.2', '20.3', '20.4']
    """
    prd_stories = set(extract_stories_from_prd(prd_file))
    requested = set(requested_stories) if requested_stories else set()

    missing = prd_stories - requested
    extra = requested - prd_stories

    coverage = {
        "prd_stories": sorted(prd_stories, key=_version_sort_key),
        "requested_stories": sorted(requested, key=_version_sort_key) if requested else [],
        "missing_stories": sorted(missing, key=_version_sort_key) if missing else [],
        "extra_stories": sorted(extra, key=_version_sort_key) if extra else [],
        "is_complete": prd_stories == requested and len(prd_stories) > 0
    }

    # 打印覆盖率报告
    if coverage["is_complete"]:
        print(f"[PRD Parser] OK: Complete coverage: all {len(prd_stories)} stories included")
    else:
        if coverage["missing_stories"]:
            print(f"[PRD Parser] WARNING: Missing {len(coverage['missing_stories'])} stories: {coverage['missing_stories']}")
        if coverage["extra_stories"]:
            print(f"[PRD Parser] WARNING: Extra stories not in PRD: {coverage['extra_stories']}")

    return coverage


def find_epic_prd_file(base_path: Path, epic_id: int) -> Optional[Path]:
    """
    根据Epic ID查找对应的PRD文件

    查找模式:
    1. docs/prd/EPIC-{epic_id}-*.md
    2. docs/prd/epic-{epic_id}-*.md
    3. docs/prd/Epic-{epic_id}-*.md

    Args:
        base_path: 项目根目录
        epic_id: Epic编号 (如 20)

    Returns:
        PRD文件路径，如果未找到返回None

    Example:
        >>> find_epic_prd_file(Path("."), 20)
        PosixPath('docs/prd/EPIC-20-BACKEND-STABILITY-MULTI-PROVIDER.md')
    """
    prd_dir = base_path / "docs" / "prd"

    if not prd_dir.exists():
        print(f"[PRD Parser] WARNING: PRD directory not found: {prd_dir}")
        return None

    # 尝试不同的命名模式
    patterns = [
        f"EPIC-{epic_id}-*.md",
        f"epic-{epic_id}-*.md",
        f"Epic-{epic_id}-*.md",
    ]

    for pattern in patterns:
        matches = list(prd_dir.glob(pattern))
        if matches:
            # 如果有多个匹配，选择最新的
            matches.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            print(f"[PRD Parser] OK: Found PRD file: {matches[0]}")
            return matches[0]

    print(f"[PRD Parser] WARNING: No PRD file found for Epic {epic_id} in {prd_dir}")
    return None


def get_epic_id_from_story(story_id: str) -> Optional[int]:
    """
    从Story ID中提取Epic ID

    Args:
        story_id: Story ID (如 "20.1", "20.2")

    Returns:
        Epic ID (如 20)，如果解析失败返回None

    Example:
        >>> get_epic_id_from_story("20.3")
        20
    """
    try:
        epic_part = story_id.split(".")[0]
        return int(epic_part)
    except (ValueError, IndexError):
        return None


# CLI utility for testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python prd_parser.py <epic_id> [base_path]")
        print("Example: python prd_parser.py 20")
        sys.exit(1)

    epic_id = int(sys.argv[1])
    base_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(".")

    prd_file = find_epic_prd_file(base_path, epic_id)
    if prd_file:
        stories = extract_stories_from_prd(prd_file)
        print(f"\nEpic {epic_id} Stories: {stories}")
