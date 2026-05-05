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
_current_subject_id: ContextVar[str] = ContextVar(
    "current_subject_id", default=DEFAULT_SUBJECT_ID
)


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
                subjects.append(
                    {
                        "id": rec.get("id", ""),
                        "name": rec.get("name", ""),
                        "created_at": rec.get("createdAt", ""),
                        "color": rec.get("color"),
                    }
                )
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
        if part_lower not in SKIP_DIRECTORIES_LOWER and not part.endswith(".canvas"):
            return part

    # Fallback: use filename without extension
    return path.stem or DEFAULT_SUBJECT_ID


def extract_canvas_name(canvas_path: str) -> str:
    """
    Extract canvas filename without .canvas extension.

    Used to derive the canvas-level component of group_id for
    per-canvas memory namespace isolation (Epic 6 Feature 6.1).

    Examples:
        - "数学/离散数学.canvas" -> "离散数学"
        - "Math 54/chapter1/calc.canvas" -> "calc"
        - "random" -> "random"
        - "" -> "untitled"

    Args:
        canvas_path: Canvas file path (may include directories)

    Returns:
        Canvas filename stem, or "untitled" if empty/missing.

    [Source: Phase 3 PRD Epic 6 - group_id Dynamic Binding]
    """
    from pathlib import PurePosixPath

    if not canvas_path:
        return "untitled"

    # Use PurePosixPath to handle forward-slash paths consistently
    name = PurePosixPath(canvas_path).stem

    # PurePosixPath(".canvas").stem returns ".canvas" (hidden file with no real name)
    if not name or name.startswith("."):
        return "untitled"
    return name


def build_group_id(subject: str, canvas_name: Optional[str] = None) -> str:
    """
    Build a group_id for Neo4j/Graphiti memory isolation (Story 1.9 legacy).

    ⚠️ Story 2.5.Y 推荐使用 build_vault_group_id() 实现统一 vault: 前缀命名.
    本函数保留是为 Story 1.9 backward compatibility (production data 已用此格式).

    Args:
        subject: Subject name (e.g., "math", "physics")
        canvas_name: Optional canvas name for further isolation

    Returns:
        Group ID string for memory isolation (e.g., "math" / "math:calc")
    """
    sanitized = sanitize_subject_name(subject)
    if canvas_name:
        return f"{sanitized}:{sanitize_subject_name(canvas_name)}"
    return sanitized


def build_vault_group_id(
    vault_id: str,
    subject_id: Optional[str] = None,
    canvas_path: Optional[str] = None,
) -> str:
    """Story 2.5.Y Task 1 + AC #2 — vault: 前缀命名统一 group_id 构造.

    新统一格式: ``vault:<vault_id>[:<subject_or_canvas>]``

    与旧 build_group_id 区别:
    - 强制 ``vault:`` 前缀 (区分新旧数据 + Story 2.5.Y 迁移识别)
    - vault_id 是必填主参数 (Story 1.9 的 subject 作为可选二级)
    - subject_id 与 canvas_path 互斥 (优先 subject_id)

    Args:
        vault_id: Vault stable identifier (必填), 如 "cs_61b" / "数学"
        subject_id: 可选学科二级隔离 (优先级 > canvas_path)
        canvas_path: 可选 canvas/board 名 (subject_id 为空时使用)

    Returns:
        统一格式 group_id

    Examples:
        >>> build_vault_group_id("cs_61b")
        'vault:cs_61b'
        >>> build_vault_group_id("cs_61b", subject_id="algorithms")
        'vault:cs_61b:algorithms'
        >>> build_vault_group_id("cs_61b", canvas_path="admissibility")
        'vault:cs_61b:admissibility'
        >>> build_vault_group_id("数学")
        'vault:数学'

    Raises:
        ValueError: vault_id 为空 (Story 2.5.Y AC #2 强制要求)
    """
    if not vault_id or not vault_id.strip():
        raise ValueError(
            "vault_id is required for Story 2.5.Y vault: prefix isolation"
        )

    sanitized_vault = sanitize_subject_name(vault_id)
    base = f"vault:{sanitized_vault}"

    # subject_id 优先于 canvas_path (互斥)
    if subject_id:
        return f"{base}:{sanitize_subject_name(subject_id)}"
    if canvas_path:
        # canvas_path 可能是完整路径, 提取 stem
        canvas_name = extract_canvas_name(canvas_path)
        if canvas_name and canvas_name != "untitled":
            return f"{base}:{sanitize_subject_name(canvas_name)}"
    return base


def is_vault_group_id(group_id: str) -> bool:
    """Story 2.5.Y Task 6 — 检测 group_id 是否已是 vault: 前缀格式 (用于迁移脚本)."""
    return isinstance(group_id, str) and group_id.startswith("vault:")


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
    sanitized = re.sub(r"[^\w]", "_", normalized, flags=re.UNICODE)
    sanitized = re.sub(r"_+", "_", sanitized)
    return sanitized.strip("_") or "default"


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
