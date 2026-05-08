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
        raise ValueError("vault_id is required for Story 2.5.Y vault: prefix isolation")

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


# ═══════════════════════════════════════════════════════════════════════════════
# Round-23 Story 7.2 · Patch 2 — canonical_group_id 唯一入口
# [Source: _bmad-output/research/round-23-chatgpt-dr-result-and-synthesis-2026-05-08.md]
# ═══════════════════════════════════════════════════════════════════════════════

import logging as _canon_logging
from functools import lru_cache as _canon_lru_cache

_canon_logger = _canon_logging.getLogger(__name__)


# Round-23 Patch 2: 本地 deprecated mapping 副本 (避免循环依赖 services 层)
# 与 app.services.group_id_migration_service.LEGACY_TO_VAULT_MAPPING 内容必须保持同步.
# core 层是配置基石, 不依赖 services 层. services 层的 mapping 用于一次性迁移脚本.
_DEPRECATED_GROUP_ID_MAPPING = {
    "cs188": "vault:default",
    "canvas-dev": "vault:default",
    "general": "vault:default",
    "main": "vault:default",
}


@_canon_lru_cache(maxsize=128)
def canonical_group_id(value: str) -> str:
    """Round-23 Patch 2: group_id 唯一归一化入口.

    所有 group_id 输入路径必须经此函数, 杜绝以下泄漏:
    - 旧硬编码 (cs188 / canvas-dev / cs_61b:main) 直接进 Neo4j
    - 不同来源大小写/连字符差异 (CS-61B vs cs_61b)
    - 用户输入未 sanitize 直接写库

    deprecated 字符串触发 WARNING (但仍归一化, 不破坏现有数据读取).

    归一化 4 条规则 (与 services.group_id_migration_service.map_legacy_group_id 一致):
    1. 空/None/非 str → 'vault:default'
    2. 已 vault: 前缀 → 幂等返回
    3. 命中 _DEPRECATED_GROUP_ID_MAPPING → 映射 + WARNING
    4. 含冒号 (Story 1.9 subject:canvas 格式) → vault:<sanitize(subject)>:<sanitize(canvas)>
    5. 其他 → vault:<sanitize(value)>

    Args:
        value: 原始 group_id (可能是 deprecated / 已规范 / 任意字符串)

    Returns:
        归一化后的 vault: 前缀 group_id

    Examples:
        >>> canonical_group_id("vault:cs_61b")
        'vault:cs_61b'
        >>> canonical_group_id("cs188")  # 触发 WARNING
        'vault:default'
        >>> canonical_group_id("CS 61B")
        'vault:cs_61b'

    Notes:
        - lru_cache 避免每次 import 重算
        - core 层不依赖 services 层 (避免循环依赖)
    """
    if not isinstance(value, str) or not value.strip():
        _canon_logger.warning(
            "canonical_group_id received empty/non-str input, defaulting to 'vault:default'"
        )
        return "vault:default"

    if is_vault_group_id(value):
        return value

    if value in _DEPRECATED_GROUP_ID_MAPPING:
        new_value = _DEPRECATED_GROUP_ID_MAPPING[value]
        _canon_logger.warning(
            "Deprecated group_id '%s' detected — auto-canonicalized to '%s'. "
            "Update callers to use vault: prefix directly.",
            value,
            new_value,
        )
        return new_value

    if ":" in value:
        parts = value.split(":", 1)
        subject = sanitize_subject_name(parts[0])
        rest = sanitize_subject_name(parts[1]) if len(parts) > 1 else ""
        if rest:
            return f"vault:{subject}:{rest}"
        return f"vault:{subject}"

    return f"vault:{sanitize_subject_name(value)}"


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
