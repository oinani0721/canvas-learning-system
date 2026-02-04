# Canvas Learning System - Subject Configuration
# Story 30.x: Multi-Subject Memory System (STUB)
"""
Subject-specific configuration for the memory system.

STUB: Full implementation in Story 30.x

TODO: Will implement:
- Subject-specific memory configuration
- Subject isolation for multi-subject learning
"""

from enum import Enum
from typing import Dict, Optional


class SubjectType(str, Enum):
    """Types of subjects in Canvas Learning System."""
    MATH = "math"
    PHYSICS = "physics"
    COMPUTER_SCIENCE = "computer_science"
    LANGUAGE = "language"
    GENERAL = "general"


# Default subject configuration
DEFAULT_SUBJECT = SubjectType.GENERAL

# Subject to Neo4j database mapping (STUB)
SUBJECT_DATABASE_MAPPING: Dict[SubjectType, str] = {
    SubjectType.MATH: "neo4j",
    SubjectType.PHYSICS: "neo4j",
    SubjectType.COMPUTER_SCIENCE: "neo4j",
    SubjectType.LANGUAGE: "neo4j",
    SubjectType.GENERAL: "neo4j",
}


def get_database_for_subject(subject: SubjectType) -> str:
    """Get Neo4j database name for a subject."""
    return SUBJECT_DATABASE_MAPPING.get(subject, "neo4j")


def get_current_subject() -> SubjectType:
    """Get the current active subject (STUB)."""
    return DEFAULT_SUBJECT


# Directories to skip when scanning for subjects
# ✅ Verified from docs/stories/30.8.story.md#学科推断规则
SKIP_DIRECTORIES_LOWER = {
    ".obsidian",
    ".git",
    ".trash",
    "__pycache__",
    "node_modules",
    ".canvas-learning",
    # Chinese common root directories (AC-30.8.2)
    "笔记库",
    "vault",
    "notes",
    "obsidian",
}


def extract_subject_from_canvas_path(canvas_path: str) -> str:
    """
    从Canvas路径提取学科名称

    ✅ Verified from docs/stories/30.8.story.md#AC-30.8.2:
    规则:
    1. 使用路径的第一级目录作为学科
    2. 如果只有文件名，使用文件名（去除扩展名）
    3. 处理中文和Unicode路径

    示例:
    - "数学/离散数学.canvas" → "数学"
    - "托福/听力/托福听力.canvas" → "托福"
    - "离散数学.canvas" → "离散数学"
    - "笔记库/物理/力学.canvas" → "物理" (跳过笔记库)

    Args:
        canvas_path: Canvas文件路径

    Returns:
        Extracted subject name

    [Source: docs/stories/30.8.story.md#学科推断规则]
    """
    from pathlib import Path

    if not canvas_path:
        return DEFAULT_SUBJECT.value

    path = Path(canvas_path)
    parts = list(path.parts)

    # Skip common root directories
    for part in parts:
        part_lower = part.lower()
        if part_lower not in SKIP_DIRECTORIES_LOWER and not part.endswith('.canvas'):
            return part

    # Fallback: use filename without extension
    return path.stem or DEFAULT_SUBJECT.value


def build_group_id(subject: str, canvas_name: Optional[str] = None) -> str:
    """
    Build a group_id for Neo4j memory isolation.

    Args:
        subject: Subject name (e.g., "math", "physics")
        canvas_name: Optional canvas name for further isolation

    Returns:
        Group ID string for memory isolation
    """
    sanitized = sanitize_subject_name(subject)
    if canvas_name:
        return f"{sanitized}:{sanitize_subject_name(canvas_name)}"
    return sanitized


def sanitize_subject_name(name: str) -> str:
    """
    Sanitize a subject name for use as group_id.

    Preserves Unicode characters (Chinese, Japanese, etc.) while normalizing
    ASCII characters to lowercase and replacing special characters with underscores.

    Args:
        name: Raw subject name

    Returns:
        Sanitized name (preserves Unicode letters, lowercase ASCII, underscores for separators)

    Examples:
        - "数学" → "数学"
        - "Math 101" → "math_101"
        - "计算机科学" → "计算机科学"
        - "托福/听力" → "托福_听力"
        - "C++" → "c"

    [Source: docs/stories/30.8.story.md - QA Review Fix for Unicode handling]
    """
    import re

    if not name:
        return "default"

    # Normalize: casefold() provides better Unicode lowercasing than lower()
    # Chinese characters are unaffected (no case), ASCII becomes lowercase
    normalized = name.casefold()

    # Replace non-word characters with underscore
    # \w matches [a-zA-Z0-9_] plus Unicode letters and digits (Chinese, etc.)
    # This preserves Chinese characters while replacing spaces, punctuation, etc.
    sanitized = re.sub(r'[^\w]', '_', normalized, flags=re.UNICODE)

    # Remove consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)

    # Remove leading/trailing underscores
    return sanitized.strip('_') or "default"
