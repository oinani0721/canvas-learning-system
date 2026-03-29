# Canvas Learning System - Subject Configuration
# Story 1.9: Multi-Subject Knowledge Graph Isolation
"""
Subject-specific configuration for the memory system.

Activated by Story 1.9. Provides:
- Dynamic subject list (user-managed via Neo4j :Subject nodes)
- Subject path inference from Canvas file paths
- Group ID construction for Graphiti/Neo4j isolation
- Request-context subject resolution

[Source: _bmad-output/implementation-artifacts/1-9-multi-subject-kg-isolation.md#Task 5]
"""

import logging
from contextvars import ContextVar
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from neo4j import AsyncDriver

logger = logging.getLogger(__name__)

# Default subject identifier (used when no subject is specified)
DEFAULT_SUBJECT_ID = "general"

# ContextVar for per-request subject_id propagation
# Set by API middleware/dependency, read by services that need the current subject.
_current_subject_id: ContextVar[str] = ContextVar("current_subject_id", default=DEFAULT_SUBJECT_ID)


def get_database_for_subject(subject_id: str) -> str:
    """
    Get Neo4j database name for a subject.
    All subjects use the same Neo4j database with subjectId property filtering.
    """
    return "neo4j"


def get_current_subject_id() -> str:
    """
    Get the current subject ID from the request context.

    The subject_id is set per-request via ``set_current_subject_id`` (called
    from the API dependency layer).  Falls back to DEFAULT_SUBJECT_ID when
    no request context is active (e.g. background tasks, CLI).
    """
    return _current_subject_id.get()


def set_current_subject_id(subject_id: str) -> None:
    """
    Set the subject_id for the current request context.

    Called by the FastAPI dependency ``resolve_subject_id`` so that any
    downstream service can retrieve it via ``get_current_subject_id()``.
    """
    _current_subject_id.set(subject_id if subject_id else DEFAULT_SUBJECT_ID)


async def list_subjects_from_neo4j(neo4j_driver: "AsyncDriver") -> List[dict]:
    """
    Fetch the dynamic list of user-created subjects from Neo4j.

    Each subject is stored as a ``:Subject`` node with properties:
        id (str), name (str), createdAt (str), color (str|null).

    Args:
        neo4j_driver: An async Neo4j driver instance.

    Returns:
        List of subject dicts with keys: id, name, createdAt, color.
    """
    query = """
    MATCH (s:Subject)
    RETURN s.id AS id, s.name AS name,
           s.createdAt AS createdAt, s.color AS color
    ORDER BY s.createdAt ASC
    """
    subjects: List[dict] = []
    try:
        async with neo4j_driver.session() as session:
            result = await session.run(query)
            records = await result.data()
            for rec in records:
                subjects.append({
                    "id": rec.get("id", ""),
                    "name": rec.get("name", ""),
                    "created_at": rec.get("createdAt", ""),
                    "color": rec.get("color"),
                })
    except (OSError, RuntimeError, ValueError) as e:
        logger.warning(f"Failed to list subjects from Neo4j: {e}")
    return subjects


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


def build_neo4j_subject_filter(
    subject_id: Optional[str],
    node_alias: str = "n",
) -> tuple:
    """
    Build a Cypher WHERE clause fragment for subject-scoped queries.

    Returns a ``(clause, params)`` tuple.  When *subject_id* is ``None`` or
    ``"general"`` (the default bucket), the clause is empty so that the query
    returns results across all subjects.

    Args:
        subject_id: The subject to filter by (may be None).
        node_alias: Cypher variable name of the node to filter.

    Returns:
        (cypher_fragment, param_dict) -- e.g.
        ``("AND n.subjectId = $subject_id", {"subject_id": "math"})``
        or ``("", {})``.
    """
    if not subject_id or subject_id == DEFAULT_SUBJECT_ID:
        return ("", {})
    return (
        f"AND {node_alias}.subjectId = $subject_id",
        {"subject_id": subject_id},
    )
