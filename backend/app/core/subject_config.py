# Canvas Learning System - Subject Configuration
# Story 1.9: Multi-Subject Knowledge Graph Isolation
"""
Subject-specific configuration for the memory system.

Activated by Story 1.9. Provides:
- Dynamic subject list (user-managed via Settings UI)
- Subject path inference from Canvas file paths
- Group ID construction for Graphiti/Neo4j isolation

[Source: _bmad-output/implementation-artifacts/1-9-multi-subject-kg-isolation.md#Task 5]
"""

from typing import Optional


# Default subject identifier (used when no subject is specified)
DEFAULT_SUBJECT_ID = "general"


def get_database_for_subject(subject_id: str) -> str:
    """
    Get Neo4j database name for a subject.
    All subjects use the same Neo4j database with subjectId property filtering.
    """
    return "neo4j"


def get_current_subject_id() -> str:
    """
    Get the default subject ID.
    The actual current subject comes from the API request context (subject_id parameter).
    This function provides the fallback default.
    """
    return DEFAULT_SUBJECT_ID


# Directories to skip when scanning for subjects
SKIP_DIRECTORIES_LOWER = {
    ".obsidian",
    ".git",
    ".trash",
    "__pycache__",
    "node_modules",
    ".canvas-learning",
    "笔记库",
    "vault",
    "notes",
    "obsidian",
}


def extract_subject_from_canvas_path(canvas_path: str) -> str:
    """
    Extract subject name from Canvas file path.

    Rules:
    1. Use the first non-skip directory in the path as subject
    2. If only a filename, use the filename (without extension)
    3. Handle Chinese and Unicode paths

    Examples:
    - "数学/离散数学.canvas" -> "数学"
    - "托福/听力/托福听力.canvas" -> "托福"
    - "离散数学.canvas" -> "离散数学"
    - "笔记库/物理/力学.canvas" -> "物理" (skips 笔记库)

    Args:
        canvas_path: Canvas file path

    Returns:
        Extracted subject name

    [Source: Story 1.9 AC-2 path inference]
    """
    from pathlib import Path

    if not canvas_path:
        return DEFAULT_SUBJECT_ID

    path = Path(canvas_path)
    parts = list(path.parts)

    # Skip common root directories
    for part in parts:
        part_lower = part.lower()
        if part_lower not in SKIP_DIRECTORIES_LOWER and not part.endswith('.canvas'):
            return part

    # Fallback: use filename without extension
    return path.stem or DEFAULT_SUBJECT_ID


def build_group_id(subject: str, canvas_name: Optional[str] = None) -> str:
    """
    Build a group_id for Neo4j/Graphiti memory isolation.

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
        Sanitized name

    Examples:
        - "数学" -> "数学"
        - "Math 101" -> "math_101"
        - "计算机科学" -> "计算机科学"
        - "托福/听力" -> "托福_听力"
    """
    import re

    if not name:
        return "default"

    normalized = name.casefold()
    sanitized = re.sub(r'[^\w]', '_', normalized, flags=re.UNICODE)
    sanitized = re.sub(r'_+', '_', sanitized)
    return sanitized.strip('_') or "default"
