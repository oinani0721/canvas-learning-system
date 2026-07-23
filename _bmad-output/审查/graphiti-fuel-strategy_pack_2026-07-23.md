This file is a merged representation of a subset of the codebase, containing specifically included files and files not matching ignore patterns, combined into a single document by Repomix.

# File Summary

## Purpose
This file contains a packed representation of a subset of the repository's contents that is considered the most important context.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.

## File Format
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Repository files (if enabled)
5. Multiple file entries, each consisting of:
  a. A header with the file path (## File: path/to/file)
  b. The full contents of the file in a code block

## Usage Guidelines
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.

## Notes
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Only files matching these patterns are included: backend/app/services/memory_service.py, backend/app/services/episode_worker.py, backend/app/services/conversation_distiller.py, backend/app/services/learning_event_log.py, backend/app/services/error_writer.py, backend/app/services/graphiti_structured_writer.py, backend/app/services/canvas_projection_sync.py, backend/app/services/targeting_material_service.py, backend/app/api/v1/endpoints/tips.py, backend/app/api/v1/endpoints/memory.py, backend/app/mcp/tools/memory_tools.py, backend/app/graphiti/group_id_compat.py, backend/app/core/subject_config.py, backend/app/core/term_aliases.py, canvas-vault/.claude/hooks/session-end-archive.py, frontend/obsidian-plugin/src/frontmatter-tips-sync.ts, frontend/obsidian-plugin/src/node-derivation.ts, _bmad-output/研究/2026-07-22-记忆检索效果对抗审查.md, _bmad-output/研究/2026-07-23-ChatGPT审查对账-计划v2修订.md, _bmad-output/研究/2026-07-22-下一步开发计划-稳定记忆与越老越准.md, _decisions/CURRENT_TASK.md
- Files matching these patterns are excluded: .env, .env*, **/.env*, **/*.pem, **/*.p12, **/*.pfx, **/id_rsa*, **/credentials*.json, **/service-account*.json, **/.npmrc, **/.aws/**, **/.git-credentials, **/*.tfvars, **/kubeconfig, **/.pypirc, **/*.key, **/*secret*, **/openclaw.json*, **/*.bak*, logs/**, state/**
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Files are sorted by Git change count (files with more changes are at the bottom)

# Directory Structure
````
backend/
  app/
    api/
      v1/
        endpoints/
          memory.py
          tips.py
    core/
      subject_config.py
      term_aliases.py
    graphiti/
      group_id_compat.py
    mcp/
      tools/
        memory_tools.py
    services/
      canvas_projection_sync.py
      conversation_distiller.py
      episode_worker.py
      error_writer.py
      graphiti_structured_writer.py
      learning_event_log.py
      memory_service.py
      targeting_material_service.py
canvas-vault/
  .claude/
    hooks/
      session-end-archive.py
frontend/
  obsidian-plugin/
    src/
      frontmatter-tips-sync.ts
      node-derivation.ts
````

# Files

## File: backend/app/core/subject_config.py
````python
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


def default_vault_group_id() -> str:
    """轨道 B P15 (2026-07-20): MCP 工具缺省 group 推导。

    写侧 (SessionEnd 归档等) 落 vault:<active_vault>, 而 MCP 读写工具
    缺省曾回落 DEFAULT_GROUP_ID (vault:default) — 两侧异组, 不带
    group_id 的召回必空手 (UAT D2 实测踩空根因)。统一走已在
    main.py/tips.py/canvas_projection_sync 生产使用的推导链。
    """
    from app.config import get_current_vault_id

    return build_vault_group_id(get_current_vault_id())
````

## File: backend/app/core/term_aliases.py
````python
"""批次4' 检索束 — 术语双语别名表 (MEM-FLYWHEEL-2026-07-22, 对账采纳)。

中英混合检索的稳态修法: 与其换 embedding 模型, 不如把 query 扩成「检索束」
(原文 + 命中术语的另一语言 + 别名) — 对「代理/agent」「极小极大/minimax」
这类短词多义与跨语场景, 束比单条 query 稳 (ChatGPT 对账裁决: 优先于任何
换模型动作)。

实现: 最小拼接式 — 命中表内术语时把对侧语言术语拼进 query, 单次查询
(BM25 多词 OR 天然支持, dense embedding 对拼接 query 稳健), 不做多路
多次检索 (延迟 ×N 不值)。

表按 vault 主题维护 (CS188 + 线代), 新学科加条目即可。
"""

from __future__ import annotations

#: 中文 → 英文术语束 (含常用别名, 空格分隔)
ZH_TO_EN: dict[str, str] = {
    "特征值": "eigenvalue",
    "特征向量": "eigenvector",
    "协方差": "covariance",
    "零空间": "null space kernel",
    "主成分": "principal component PCA",
    "矩阵": "matrix",
    "行列式": "determinant",
    "线性变换": "linear transformation",
    "极小极大": "minimax",
    "剪枝": "pruning alpha-beta",
    "值迭代": "value iteration",
    "策略迭代": "policy iteration",
    "启发函数": "heuristic",
    "启发式": "heuristic",
    "可采纳": "admissible admissibility",
    "一致性": "consistency consistent",
    "弧一致": "arc consistency AC-3",
    "约束满足": "constraint satisfaction CSP",
    "回溯": "backtracking",
    "深度优先": "depth-first DFS",
    "广度优先": "breadth-first BFS",
    "理性代理": "rational agent",
    "代理": "agent",
    "零和": "zero-sum",
    "误解": "misconception",
    "递归": "recursion",
}

#: 英文 → 中文术语束 (跨语反向: 英文 query 召回中文三元组)
EN_TO_ZH: dict[str, str] = {
    "eigenvalue": "特征值",
    "eigenvector": "特征向量",
    "covariance": "协方差",
    "null space": "零空间",
    "minimax": "极小极大",
    "pruning": "剪枝",
    "value iteration": "值迭代",
    "heuristic": "启发函数",
    "admissible": "可采纳",
    "admissibility": "可采纳",
    "consistency": "一致性",
    "arc consistency": "弧一致",
    "backtracking": "回溯",
    "agent": "代理",
    "zero-sum": "零和",
    "misconception": "误解",
    "recursion": "递归",
}


def expand_query(query: str) -> str:
    """query 命中术语表 → 拼接对侧语言术语束; 无命中原样返回。

    长词优先匹配 (「理性代理」先于「代理」), 已在 query 中的术语不重复拼。
    """
    if not query:
        return query
    additions: list[str] = []
    q_lower = query.lower()
    matched_spans: list[str] = []

    for zh, en in sorted(ZH_TO_EN.items(), key=[REDACTED:env-cred] kv: -len(kv[0])):
        if zh in query and not any(zh in s for s in matched_spans):
            matched_spans.append(zh)
            for term in en.split():
                if term.lower() not in q_lower and term not in additions:
                    additions.append(term)

    for en, zh in sorted(EN_TO_ZH.items(), key=[REDACTED:env-cred] kv: -len(kv[0])):
        if en in q_lower and zh not in query and zh not in additions:
            additions.append(zh)

    if not additions:
        return query
    return query + " " + " ".join(additions)
````

## File: backend/app/services/error_writer.py
````python
# Story 2.5 Task 4 — 错误双写 (frontmatter + Graphiti)
#
# AC #4: errors[] 数组追加到 frontmatter (双标签 D 方案: pedagogy + legacy)
#        + memory_service.record_knowledge_entity 写 Graphiti
# AC #6: Graphiti 失败 → frontmatter 仍成功 (本地优先) + structlog warning
#        + 自动重试 (3 次, 间隔 1s)
#
# [Source: _bmad-output/implementation-artifacts/epic-2/2-5-error-extraction-classification.md#Task 4]

from __future__ import annotations

import asyncio
import contextvars
import hashlib
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import structlog
import yaml

from app.services.error_classifier import ClassifiedError

# Story 2.5.X (D15 = C+) — write_error_dual mode 选项
WriteMode = Literal["candidate_only", "write_confirmed"]
CANDIDATE_INITIAL_STATUS = "pending"
CANDIDATE_SOURCE_AI = "ai_suggested"

logger = structlog.get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# 配置常量 (PRD AC #4 + #6)
# ═══════════════════════════════════════════════════════════════════════════════

GRAPHITI_TIMEOUT_S = 0.5  # 单次 record_knowledge_entity 超时 (Task 4.3)
GRAPHITI_MAX_RETRIES = 3  # 重试上限 (Task 4.4)
GRAPHITI_RETRY_INTERVAL_S = 1.0  # 重试间隔

# Story 2.5 P0 fix (ChatGPT 二轮审查 2026-05-04):
# per-file async lock 防并发 read-modify-write 丢数据.
# 多个 record_error 并发写同一个 .md 时 errors[] 不丢条.
_FILE_LOCKS: dict[str, asyncio.Lock] = {}


def _get_file_lock(file_path: str | Path) -> asyncio.Lock:
    """Per-file async lock (Story 2.5 P0 fix concurrency)."""
    key = [REDACTED:env-cred]
    if key not in _FILE_LOCKS:
        _FILE_LOCKS[key] = asyncio.Lock()
    return _FILE_LOCKS[key]


def _make_dedupe_hash(error: ClassifiedError, node_id: str) -> str:
    """Story 2.5 HIGH#11 fix — error 去重 hash (ChatGPT 二轮审查).

    同 (pedagogy_type, description, node_id) 视为同一错误, 避免无限增长.
    """
    raw = f"{error.pedagogy_type.value}|{error.description}|{node_id}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


# ═══════════════════════════════════════════════════════════════════════════════
# Story 2.5.X Task 1 — Candidate writer (C+ 渐进式确认)
# ═══════════════════════════════════════════════════════════════════════════════


def _make_candidate_record(
    error: ClassifiedError,
    *,
    node_id: str,
    session_id: str,
    group_id: str,
    candidate_id: str,
    dedupe_hash: str,
    now_iso: str,
    ai_reason: str | None = None,
    evidence_turns: list[int] | None = None,
    raw_dialog_excerpt: str | None = None,
    provenance: str = "distilled",
) -> dict[str, Any]:
    """Story 2.5.X AC #1 — 构造 candidate dict (含 6 状态机初始值 pending).

    方案 A 硬要求 (2026-07-20 裁决): provenance 区分 seeded (测试种子) /
    distilled (真实蒸馏); description 拆 misconception/correction 双字段
    (出题侧只读前者防泄题, P5), description 保留兼容旧读侧。
    """
    from app.services.candidate_callout import split_description

    misconception, correction = split_description(error.description)
    return {
        "id": candidate_id,
        "status": CANDIDATE_INITIAL_STATUS,
        "source": CANDIDATE_SOURCE_AI,
        "provenance": provenance,
        "misconception": misconception,
        "correction": correction,
        "node_id": node_id,
        "session_id": session_id,
        "group_id": group_id,
        "candidate_dedupe_hash": dedupe_hash,
        "pedagogy_type": error.pedagogy_type.value,
        "legacy_type": error.legacy_type.value,
        "description": error.description,
        "context": error.context,
        "ai_reason": ai_reason,  # Task 5 LLM 升级后填
        "evidence_turns": evidence_turns or [],  # Task 5 LLM 升级后填
        "raw_dialog_excerpt": raw_dialog_excerpt,  # Task 5 透传后填
        "confidence": round(error.confidence, 3),
        "confidence_source": "llm",  # 当前 ErrorClassifier 已输出 confidence
        "sub_tags": list(error.sub_tags),
        "suggested_remedy_strategies": [r.value for r in error.pedagogy_remedies],
        "legacy_remedy": error.legacy_remedy.value,
        "created_at": now_iso,
        "last_seen_at": now_iso,
        "seen_count": 1,
        "seen_sessions": [session_id] if session_id else [],
        "status_changed_at": None,  # 状态变更时填 (AC #2)
        "status_changed_by": None,
    }


def write_candidate_to_frontmatter(
    file_path: str | Path,
    error: ClassifiedError,
    *,
    node_id: str,
    session_id: str = "",
    group_id: str = "",
    candidate_id: str | None = None,
    ai_reason: str | None = None,
    evidence_turns: list[int] | None = None,
    raw_dialog_excerpt: str | None = None,
) -> tuple[bool, str | None]:
    """Story 2.5.X Task 1 — 追加候选错误到 frontmatter `error_candidates[]` (原子写入).

    与 `write_error_to_frontmatter` 区别：
    - 写 `error_candidates[]` 而非 `errors[]` (双数组并存)
    - candidate.status = "pending" (6 状态机初始值, AC #2)
    - 不写 Graphiti (AC #1: candidate 阶段不进知识图谱)
    - 复用同一 dedupe_hash 算法 (不含 session_id, AC #3)
    - 重复同错误时更新 last_seen_at / seen_count / seen_sessions (不 append)

    Args:
        file_path: 节点 .md 路径
        error: ClassifiedError 双标签错误
        node_id: Canvas 节点 ID (用于 dedupe + metadata)
        session_id: 当前对话 session ID (Round-2 修正: 加 frontmatter 但不进 dedupe)
        group_id: vault namespace (Story 2.5.Y 前期占位, 当前可为 "")
        candidate_id: 可选 UUID, None 时自动生成
        ai_reason: AI 判错理由 (Task 5 升级 LLM 后传)
        evidence_turns: 触发轮次 (Task 5 升级 LLM 后传)
        raw_dialog_excerpt: 原始对话摘录 (Task 5 透传后传)

    Returns:
        (success, candidate_id) — 重复错误算成功 (返回 existing id).
    """
    p = Path(file_path)
    if not p.exists():
        logger.warning("candidate_writer.file_not_found", path=str(p))
        return False, None

    try:
        text = p.read_text(encoding="utf-8")
        fm_str, body = _split_frontmatter(text)

        fm_dict = yaml.safe_load(fm_str) if fm_str else {}
        if not isinstance(fm_dict, dict):
            fm_dict = {}

        candidates_list = fm_dict.get("error_candidates", [])
        if not isinstance(candidates_list, list):
            candidates_list = []

        # AC #3: dedupe hash 复用 errors[] 算法 (不含 session_id, 跨 session 同错应 update 不 append)
        dedupe_hash = _make_dedupe_hash(error, node_id)
        now_iso = datetime.now(timezone.utc).isoformat()

        existing_idx: int | None = None
        for i, rec in enumerate(candidates_list):
            if (
                isinstance(rec, dict)
                and rec.get("candidate_dedupe_hash") == dedupe_hash
                and rec.get("status") == CANDIDATE_INITIAL_STATUS  # 仅 pending 算重复
            ):
                existing_idx = i
                break

        if existing_idx is not None:
            # AC #3: 同错误重复 → 更新 last_seen_at / seen_count / seen_sessions / max(confidence)
            existing = candidates_list[existing_idx]
            existing["last_seen_at"] = now_iso
            existing["seen_count"] = int(existing.get("seen_count", 1)) + 1

            existing_sessions = existing.get("seen_sessions") or []
            if not isinstance(existing_sessions, list):
                existing_sessions = []
            if session_id and session_id not in existing_sessions:
                existing_sessions.append(session_id)
            existing["seen_sessions"] = existing_sessions

            # 取最大 confidence (Round-2 修正建议)
            existing_conf = float(existing.get("confidence", 0.0))
            new_conf = round(error.confidence, 3)
            if new_conf > existing_conf:
                existing["confidence"] = new_conf

            existing_id = existing.get("id") or candidate_id or str(uuid.uuid4())
            existing["id"] = existing_id

            logger.info(
                "candidate_writer.frontmatter_duplicate_updated",
                path=str(p),
                candidate_id=existing_id,
                seen_count=existing["seen_count"],
                seen_sessions=len(existing_sessions),
            )
            candidate_id = existing_id
        else:
            # 新候选: append 完整 record
            if candidate_id is None:
                candidate_id = str(uuid.uuid4())
            new_record = _make_candidate_record(
                error,
                node_id=node_id,
                session_id=session_id,
                group_id=group_id,
                candidate_id=candidate_id,
                dedupe_hash=dedupe_hash,
                now_iso=now_iso,
                ai_reason=ai_reason,
                evidence_turns=evidence_turns,
                raw_dialog_excerpt=raw_dialog_excerpt,
            )
            candidates_list.append(new_record)

            # 方案 A 双写回显 (轨道 B 2026-07-20): 新候选生成时同步在正文
            # 追加 🔴 待复盘卡片 (锚点 %%cand:<id>%%, accept/dispute 时原地
            # 变态)。生产写侧当前断裂 (P14, 轨道③接通), 此处先就绪。
            from app.services.candidate_callout import (
                render_candidate_callout,
                upsert_candidate_callout,
            )

            body, _ = upsert_candidate_callout(
                body,
                candidate_id,
                render_candidate_callout(new_record, "pending"),
                append_if_missing=True,
            )

        fm_dict["error_candidates"] = candidates_list

        new_fm = yaml.safe_dump(fm_dict, allow_unicode=True, sort_keys=False)
        new_text = f"---\n{new_fm}---\n{body}"

        # 复用 errors[] 的原子写入模式 (AC #4 Task 4.5 from Story 2.5 v1.0)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            delete=False,
            dir=p.parent,
            prefix=f".{p.name}.tmp",
        ) as tmp:
            tmp.write(new_text)
            tmp_path = tmp.name
        os.replace(tmp_path, p)

        logger.info(
            "candidate_writer.frontmatter_written",
            path=str(p),
            pedagogy_type=error.pedagogy_type.value,
            confidence=error.confidence,
            candidate_id=candidate_id,
            duplicate=existing_idx is not None,
        )
        return True, candidate_id
    except Exception as e:
        logger.warning(
            "candidate_writer.frontmatter_failed",
            path=str(file_path),
            error=str(e),
            error_type=type(e).__name__,
        )
        return False, None


async def write_candidate_to_frontmatter_async(
    file_path: str | Path,
    error: ClassifiedError,
    *,
    node_id: str,
    session_id: str = "",
    group_id: str = "",
    candidate_id: str | None = None,
    ai_reason: str | None = None,
    evidence_turns: list[int] | None = None,
    raw_dialog_excerpt: str | None = None,
) -> tuple[bool, str | None]:
    """Story 2.5.X — Async wrapper 复用 per-file lock 防并发数据丢失.

    多个 candidate write 并发写同一 .md 时, error_candidates[] 不丢条.
    """
    lock = _get_file_lock(file_path)
    async with lock:
        return await asyncio.to_thread(
            write_candidate_to_frontmatter,
            file_path,
            error,
            node_id=node_id,
            session_id=session_id,
            group_id=group_id,
            candidate_id=candidate_id,
            ai_reason=ai_reason,
            evidence_turns=evidence_turns,
            raw_dialog_excerpt=raw_dialog_excerpt,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Frontmatter 写入 (Task 4.1, 4.5)
# ═══════════════════════════════════════════════════════════════════════════════


def write_error_to_frontmatter(
    file_path: str | Path,
    error: ClassifiedError,
    error_id: str | None = None,
    node_id_for_dedupe: str = "",
) -> tuple[bool, str | None]:
    """Story 2.5 Task 4.1 — 追加错误到 .md frontmatter `errors[]` (原子写入).

    Story 2.5 ChatGPT 二轮审查 fix (2026-05-04):
    - HIGH#10: error_id 写入 frontmatter, 与 Graphiti misconception_id 一致
    - HIGH#11: dedupe_hash 检测同错误重复 → update last_seen_at + count 不 append
    - 注意: 并发安全由 write_error_to_frontmatter_async() 提供 per-file lock

    PRD §3.2 schema (扩展含 D 方案双标签 + dedupe):
    ```yaml
    errors:
      - id: <uuid>                          # 与 Graphiti misconception_id 一致
        dedupe_hash: <16 chars sha256>      # 同错误检测 key
        type: conceptual_confusion           # PRD pedagogy 标签
        legacy_type: knowledge_gap           # Story 3.6 兼容
        legacy_remedy: backtrack_definition  # Story 3.6 单一策略 (MEDIUM#13)
        description: "..."
        corrected_at: null
        last_seen_at: "2026-05-04T..."       # 重复错误更新
        seen_count: 1                        # 重复次数
        tags: [synonym_confusion]
        remedy_strategies: [discrimination_comparison]
        confidence: 0.85
        confidence_source: llm | heuristic   # MEDIUM (二轮审查建议)
        created_at: "2026-05-04T..."
    ```

    Args:
        file_path: 节点 .md 路径.
        error: ClassifiedError 双标签错误.
        error_id: 可选 UUID, 与 Graphiti misconception_id 关联.
        node_id_for_dedupe: 用于生成 dedupe_hash 的 node_id.

    Returns:
        (success, error_id) — 成功时返回 (True, error_id used);
        失败时返回 (False, None). 重复错误算成功 (返回 existing id).
    """
    p = Path(file_path)
    if not p.exists():
        logger.warning("error_writer.file_not_found", path=str(p))
        return False, None

    try:
        text = p.read_text(encoding="utf-8")
        fm_str, body = _split_frontmatter(text)

        fm_dict = yaml.safe_load(fm_str) if fm_str else {}
        if not isinstance(fm_dict, dict):
            fm_dict = {}

        errors_list = fm_dict.get("errors", [])
        if not isinstance(errors_list, list):
            errors_list = []

        # Story 2.5 HIGH#11 fix — dedupe 检测
        dedupe_hash = _make_dedupe_hash(error, node_id_for_dedupe)
        now_iso = datetime.now(timezone.utc).isoformat()

        existing_idx: int | None = None
        for i, rec in enumerate(errors_list):
            if (
                isinstance(rec, dict)
                and rec.get("dedupe_hash") == dedupe_hash
                and rec.get("corrected_at") is None  # 已纠正的不算重复
            ):
                existing_idx = i
                break

        if existing_idx is not None:
            # 同错误重复: 更新 last_seen_at + seen_count, 不 append
            existing = errors_list[existing_idx]
            existing["last_seen_at"] = now_iso
            existing["seen_count"] = int(existing.get("seen_count", 1)) + 1
            existing_id = existing.get("id") or error_id or str(uuid.uuid4())
            existing["id"] = existing_id
            logger.info(
                "error_writer.frontmatter_duplicate_updated",
                path=str(p),
                error_id=existing_id,
                seen_count=existing["seen_count"],
            )
            error_id = existing_id
        else:
            # 新错误: append 完整 record
            if error_id is None:
                error_id = str(uuid.uuid4())
            new_record = {
                "id": error_id,
                "dedupe_hash": dedupe_hash,
                "type": error.pedagogy_type.value,
                "legacy_type": error.legacy_type.value,
                "legacy_remedy": error.legacy_remedy.value,  # MEDIUM#13 fix
                "description": error.description,
                "corrected_at": None,
                "last_seen_at": now_iso,
                "seen_count": 1,
                "tags": list(error.sub_tags),
                "remedy_strategies": [r.value for r in error.pedagogy_remedies],
                "confidence": round(error.confidence, 3),
                "created_at": now_iso,
            }
            errors_list.append(new_record)

        fm_dict["errors"] = errors_list

        new_fm = yaml.safe_dump(fm_dict, allow_unicode=True, sort_keys=False)
        new_text = f"---\n{new_fm}---\n{body}"

        # AC #4 Task 4.5: 原子写入 (临时文件 + os.replace)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            delete=False,
            dir=p.parent,
            prefix=f".{p.name}.tmp",
        ) as tmp:
            tmp.write(new_text)
            tmp_path = tmp.name
        os.replace(tmp_path, p)

        logger.info(
            "error_writer.frontmatter_written",
            path=str(p),
            pedagogy_type=error.pedagogy_type.value,
            legacy_type=error.legacy_type.value,
            confidence=error.confidence,
            error_id=error_id,
            duplicate=existing_idx is not None,
        )
        return True, error_id
    except Exception as e:
        logger.warning(
            "error_writer.frontmatter_failed",
            path=str(file_path),
            error=str(e),
            error_type=type(e).__name__,
        )
        return False, None


async def write_error_to_frontmatter_async(
    file_path: str | Path,
    error: ClassifiedError,
    error_id: str | None = None,
    node_id_for_dedupe: str = "",
) -> tuple[bool, str | None]:
    """Story 2.5 P0 fix — Async wrapper with per-file lock 防并发数据丢失.

    多个 record_error 并发写同一 .md 时, errors[] 不丢条.
    """
    lock = _get_file_lock(file_path)
    async with lock:
        return await asyncio.to_thread(
            write_error_to_frontmatter,
            file_path,
            error,
            error_id,
            node_id_for_dedupe,
        )


def _split_frontmatter(text: str) -> tuple[str, str]:
    """切分 markdown frontmatter (--- ... ---) 与 body.

    支持兼容: BOM (\ufeff) + CRLF (\r\n).
    返回: (frontmatter_yaml_str, body_str). 无 frontmatter 时 fm_yaml_str = "".
    """
    s = text.lstrip("\ufeff")
    if not s.startswith("---"):
        return "", text  # 保留原 text (含 BOM)
    parts = s.split("---", 2)
    if len(parts) < 3:
        return "", text
    return parts[1].lstrip("\r\n"), parts[2].lstrip("\r\n")


# ═══════════════════════════════════════════════════════════════════════════════
# Graphiti 写入 (Task 4.2, 4.3, 4.4) — 通过 memory_service.record_knowledge_entity
# ═══════════════════════════════════════════════════════════════════════════════


async def write_error_to_graphiti(
    error: ClassifiedError,
    node_id: str,
    session_id: str = "",
    error_id: str | None = None,
    *,
    group_id: str | None = None,
) -> bool:
    """Story 2.5 Task 4.2 + Story 2.5.Y AC #3 — 通过 memory_service.record_knowledge_entity 写 Graphiti.

    Story 2.5.Y AC #3 (2026-05-05): 移除 DEFAULT_GROUP_ID 硬编码.
    - group_id 改为优先 ContextVar (get_current_subject_id) → 否则参数 group_id → 否则 fallback DEFAULT_GROUP_ID + warning
    - 新代码应通过 endpoint 注入 ContextVar (build_vault_group_id), 不应依赖 DEFAULT_GROUP_ID 兜底

    AC #6: 失败 → structlog warning + 3 次重试 (间隔 1s) + 最终返回 False.

    Args:
        error: ClassifiedError 双标签.
        node_id: Canvas 节点 ID.
        session_id: 对话 session ID.
        error_id: misconception_id 与 frontmatter 一致.
        group_id: 显式传入的 group_id (优先级 < ContextVar). 通常由 ContextVar 注入, 此参数仅用于无 ContextVar 上下文 (如 cron / CLI).

    Returns:
        True 写入成功, False 重试耗尽仍失败.
    """
    try:
        from app.core.subject_config import get_current_subject_id
        from app.services.memory_service import get_memory_service

        # Story 2.5.Y AC #3 — group_id 解析优先级:
        # 1. 显式 group_id 参数 (cron/CLI 场景)
        # 2. ContextVar (endpoint 注入)
        # 3. fallback DEFAULT_GROUP_ID + warning (deprecated 兜底)
        if group_id:
            effective_group_id = group_id
        else:
            ctx_group_id = get_current_subject_id()
            if ctx_group_id and ctx_group_id != "general":  # DEFAULT_SUBJECT_ID
                effective_group_id = ctx_group_id
            else:
                # Story 2.5.Y deprecated fallback (Task 6 迁移后应移除)
                from app.config import DEFAULT_GROUP_ID

                effective_group_id = DEFAULT_GROUP_ID
                logger.warning(
                    "error_writer.group_id_fallback_to_default",
                    fallback=DEFAULT_GROUP_ID,
                    node_id=node_id,
                    hint="Story 2.5.Y AC #3: 调用方应通过 ContextVar 或参数传入 group_id",
                )

        memory_svc = await get_memory_service()
    except (ImportError, AttributeError, RuntimeError) as e:
        logger.warning(
            "error_writer.memory_service_unavailable",
            error=str(e),
            error_type=type(e).__name__,
            node_id=node_id,
        )
        return False

    metadata: dict[str, Any] = {
        "misconception_id": error_id,  # Story 2.5 HIGH#10 fix — 与 frontmatter id 关联
        "pedagogy_type": error.pedagogy_type.value,
        "legacy_type": error.legacy_type.value,
        "description": error.description,
        "context": error.context,
        "remedy_strategies": [r.value for r in error.pedagogy_remedies],
        "legacy_remedy": error.legacy_remedy.value,
        "sub_tags": list(error.sub_tags),
        "confidence": round(error.confidence, 3),
        "node_id": node_id,
        "session_id": session_id,
    }
    content = (
        f"Error ({error.pedagogy_type.value} / {error.legacy_type.value}): "
        f"{error.description}"
    )

    for attempt in range(1, GRAPHITI_MAX_RETRIES + 1):
        try:
            await asyncio.wait_for(
                memory_svc.record_knowledge_entity(
                    event_type="misconception",
                    content=content,
                    metadata=metadata,
                    group_id=effective_group_id,  # Story 2.5.Y AC #3: 不再硬编码 DEFAULT_GROUP_ID
                ),
                timeout=GRAPHITI_TIMEOUT_S,
            )
            logger.info(
                "error_writer.graphiti_written",
                node_id=node_id,
                attempt=attempt,
                pedagogy_type=error.pedagogy_type.value,
            )
            return True
        except asyncio.TimeoutError:
            logger.warning(
                "error_writer.graphiti_timeout",
                attempt=attempt,
                timeout_s=GRAPHITI_TIMEOUT_S,
                node_id=node_id,
            )
        except Exception as e:
            logger.warning(
                "error_writer.graphiti_attempt_failed",
                attempt=attempt,
                error=str(e),
                error_type=type(e).__name__,
                node_id=node_id,
            )
        if attempt < GRAPHITI_MAX_RETRIES:
            await asyncio.sleep(GRAPHITI_RETRY_INTERVAL_S)

    logger.warning(
        "error_writer.graphiti_max_retries_exceeded",
        node_id=node_id,
        max_retries=GRAPHITI_MAX_RETRIES,
    )
    return False


# ═══════════════════════════════════════════════════════════════════════════════
# 双写入口 (Task 4 综合)
# ═══════════════════════════════════════════════════════════════════════════════


async def write_error_dual(
    file_path: str | Path,
    error: ClassifiedError,
    node_id: str,
    session_id: str = "",
    fire_and_forget_graphiti: bool = True,
    *,
    mode: WriteMode = "candidate_only",
    group_id: str = "",
    ai_reason: str | None = None,
    evidence_turns: list[int] | None = None,
    raw_dialog_excerpt: str | None = None,
) -> dict[str, Any]:
    """Story 2.5 Task 4 + Story 2.5.X Task 1 — 双写入口 (含 C+ 渐进式确认 mode).

    Story 2.5.X (D15 = C+) 修正 (2026-05-04):
    - 加 `mode` 参数 (默认 "candidate_only" — AI 不直接写 errors[], 写候选区)
    - mode="candidate_only" → 调 write_candidate_to_frontmatter_async, 跳过 Graphiti (AC #1)
    - mode="write_confirmed" → 现有 v1.0 行为 (用户 accept_candidate 时使用)

    Story 2.5 v1.0 ChatGPT 二轮审查 fix (commit 0d05ad8):
    - P0#3 fix: 使用 write_error_to_frontmatter_async + per-file lock 防并发
    - HIGH#5 fix: graphiti_status "queued" 表示异步任务已调度
    - HIGH#10 fix: error_id 在 frontmatter + Graphiti metadata 一致
    - HIGH#11 fix: dedupe 同错误重复时返回相同 error_id, 不 append

    Args:
        file_path: .md 路径.
        error: ClassifiedError.
        node_id: Canvas 节点 ID.
        session_id: 对话 session ID.
        fire_and_forget_graphiti: True → 后台 task; False → 同步等待 (仅 write_confirmed 模式生效).
        mode: "candidate_only" (默认 Story 2.5.X) → 写 error_candidates[] / "write_confirmed" → 写 errors[] + Graphiti.
        group_id: vault namespace (Story 2.5.Y 前期占位).
        ai_reason / evidence_turns / raw_dialog_excerpt: candidate 模式的辅助元数据 (Task 5 升级 LLM 后使用).

    Returns:
        candidate_only mode:
        {
          "mode": "candidate_only",
          "frontmatter": bool,
          "graphiti": "skipped_candidate_mode" | "skipped_frontmatter_failed",
          "candidate_id": str | None,
        }
        write_confirmed mode:
        {
          "mode": "write_confirmed",
          "frontmatter": bool,
          "graphiti": "queued" | "ok" | "failed" | "skipped_frontmatter_failed",
          "error_id": str | None,
        }
    """
    # Story 2.5.X Task 1: candidate_only 模式 (默认) — 写 error_candidates[], 不写 Graphiti
    if mode == "candidate_only":
        fm_ok, candidate_id = await write_candidate_to_frontmatter_async(
            file_path,
            error,
            node_id=node_id,
            session_id=session_id,
            group_id=group_id,
            ai_reason=ai_reason,
            evidence_turns=evidence_turns,
            raw_dialog_excerpt=raw_dialog_excerpt,
        )
        if not fm_ok:
            return {
                "mode": "candidate_only",
                "frontmatter": False,
                "graphiti": "skipped_frontmatter_failed",
                "candidate_id": None,
            }
        return {
            "mode": "candidate_only",
            "frontmatter": True,
            "graphiti": "skipped_candidate_mode",  # AC #1: candidate 阶段不进 Graphiti
            "candidate_id": candidate_id,
        }

    # mode == "write_confirmed" — Story 2.5 v1.0 原行为 (accept_candidate 触发)
    fm_ok, error_id = await write_error_to_frontmatter_async(
        file_path, error, error_id=None, node_id_for_dedupe=node_id
    )

    if not fm_ok:
        return {
            "mode": "write_confirmed",
            "frontmatter": False,
            "graphiti": "skipped_frontmatter_failed",
            "error_id": None,
        }

    if fire_and_forget_graphiti:
        # wave-5 Stage B P0 (2026-05-11): snapshot ContextVar so background
        # Graphiti write inherits the vault/subject_id of the originating
        # request — prevents cross-vault leak after parent request returns.
        ctx = contextvars.copy_context()
        asyncio.create_task(
            write_error_to_graphiti(error, node_id, session_id, error_id=error_id),
            context=ctx,
        )
        return {
            "mode": "write_confirmed",
            "frontmatter": True,
            "graphiti": "queued",
            "error_id": error_id,
        }

    graphiti_ok = await write_error_to_graphiti(
        error, node_id, session_id, error_id=error_id
    )
    return {
        "mode": "write_confirmed",
        "frontmatter": True,
        "graphiti": "ok" if graphiti_ok else "failed",
        "error_id": error_id,
    }
````

## File: backend/app/services/learning_event_log.py
````python
"""批次3' 2-4 — 统一学习事件日志 (MEM-FLYWHEEL-2026-07-22, 对账 schema 四要素)。

`<vault>/learning_events.jsonl` append-only: frontmatter 仍是真相源 (不改架构),
日志提供「过程可回放、图可重建」兜底 — 会话记忆层从「丢图即永失」变为可重放。

Schema 四要素 (ChatGPT 对账采纳):
  - event_id: 幂等键 (调用方构造稳定值, 重放/重试不双写)
  - event_version: schema 版本 (当前 1)
  - recorded_at / effective_at: 双时间戳 (记录时刻 vs 业务生效时刻,
    补录历史事件时两者分离)
  - event_type: 限 8 类核心动作 (EVENT_TYPES), 未知类型拒绝 — 防事件膨胀

写点 (批次3' 接入 4 个, node_derived 留批次4' 拆分补强):
  backend: candidate_created (蒸馏) / candidate_accepted / candidate_disputed
           (= dispute 三件套第三件「可追溯」suppression log) / session_archived
  vault:   answer_scored / answer_abandoned (quiz-answer) / exam_created
           (start-exam-board) — SKILL 静态 python 直接 append 同一文件
"""

from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

EVENT_VERSION = 1

#: 8 类核心动作 — 新增类型必须走对账评审, 不得随手扩
EVENT_TYPES = frozenset(
    {
        "node_derived",
        "exam_created",
        "answer_scored",
        "answer_abandoned",
        "candidate_created",
        "candidate_accepted",
        "candidate_disputed",
        "session_archived",
    }
)

_write_lock = threading.Lock()


def _log_path() -> Path:
    from app.config import settings

    canvas_base = getattr(settings, "CANVAS_BASE_PATH", None) or "/vaults/canvas-vault"
    return Path(canvas_base) / "learning_events.jsonl"


def append_event(
    event_type: str,
    event_id: str,
    node_id: str = "",
    payload: Optional[dict[str, Any]] = None,
    effective_at: Optional[str] = None,
) -> bool:
    """append-only 落一条学习事件; event_id 已存在 → 幂等跳过。

    永不抛异常 (记录失败不得影响主链) — 返回 False 表示未写入
    (幂等跳过或 IO 失败, 区别见日志)。
    """
    try:
        if event_type not in EVENT_TYPES:
            logger.warning(
                "[learning-events] 拒绝未知 event_type=%r (8 类白名单)", event_type
            )
            return False
        if not event_id:
            logger.warning("[learning-events] 拒绝空 event_id (幂等键必填)")
            return False

        path = _log_path()
        path.parent.mkdir(parents=True, exist_ok=True)

        with _write_lock:
            # 幂等: 文件内已有该 event_id → 跳过 (日志量级小, 全文扫描可接受;
            # 大文件时可换尾部 N 行 + 索引)
            if path.exists():
                needle = json.dumps(event_id, ensure_ascii=False)
                with open(path, encoding="utf-8") as f:
                    if any(needle in line for line in f):
                        return False
            now = datetime.now(timezone.utc).isoformat()
            record = {
                "event_id": event_id,
                "event_version": EVENT_VERSION,
                "event_type": event_type,
                "node_id": node_id,
                "recorded_at": now,
                "effective_at": effective_at or now,
                "payload": payload or {},
            }
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return True
    except Exception as e:  # noqa: BLE001 — 日志兜底, 不炸主链
        logger.warning("[learning-events] append 失败 (主链不受影响): %s", e)
        return False
````

## File: frontend/obsidian-plugin/src/frontmatter-tips-sync.ts
````typescript
/**
 * FrontmatterTipsSync — Story 2.4 Plan A (2026-05-14)
 *
 * 监听 metadataCache 文件元数据变化，解析 callout → 写入 frontmatter tips[]
 * 数组。Obsidian 官方 app.fileManager.processFrontMatter API 原子写入。
 *
 * 核心设计（按 Story 2.4 spec + ChatGPT 5-14 对抗审查盲点修复）：
 *   1. metadataCache.on('changed') 而非 vault.on('modify') — Obsidian 内部
 *      已 throttle + 不会跟我们写 frontmatter 形成无限循环
 *   2. 完全覆盖 tips[] — 不 append, 不 dedupe — 自然支持删除（spec AC#5）
 *   3. 比对新旧内容相同则跳过 — 防止 frontmatter 写入触发新一轮 changed
 *   4. added_at 保留 — 匹配的旧 tip 沿用其 added_at, 新 tip 写当前时间
 *   5. parser 兼容 [!tip]+/- 单复数 — Story 2.4 spec AC#3 + #1 协议要求
 *
 * 与 Plan B（DEPRECATED）的区别：
 *   - 不调 backend POST — 完全本地
 *   - 不依赖 Graphiti / Gemini / Neo4j
 *   - 真相源 = file frontmatter（非 Graphiti EpisodicNode）
 *   - 离线 100% 安全（文件本身就是数据）
 *   - 删除天然支持
 *
 * 见 _bmad-output/research/2026-05-14-plan-b-postmortem.md
 */
import type { TFile } from "obsidian";
import { parseCalloutsFromContent, type ParsedCallout } from "./callout";
import type CanvasLearningPlugin from "./main";

const ALLOWED_PATH_PREFIXES = ["节点/", "原白板/"];

interface FrontmatterTip {
  id: string; // P0 (A+-prime): 稳定批注身份 cb-xxx, 空=历史批注(回退内容匹配)
  text: string;
  tag: string;
  understanding: string;
  added_at: string;
  source: string;
}

export class FrontmatterTipsSync {
  constructor(private plugin: CanvasLearningPlugin) {}

  /** Called from metadataCache.on('changed') */
  async syncFile(file: TFile): Promise<void> {
    if (!this.shouldHandle(file)) return;

    try {
      const content = await this.plugin.app.vault.read(file);
      const callouts = await parseCalloutsFromContent(
        content,
        file.basename,
      );

      await this.plugin.app.fileManager.processFrontMatter(
        file,
        (fm: Record<string, unknown>) => {
          const oldTips = (fm.tips as FrontmatterTip[]) || [];
          const newTips = this.buildNewTips(callouts, oldTips);

          // 防无限循环 + 不必要写入：相同内容跳过
          if (this.tipsEqual(oldTips, newTips)) return;

          // spec AC#5: 完全覆盖 — 旧 tip 被删的 callout 自然消失
          if (newTips.length === 0) {
            // 用户删光了所有 callout — 移除 tips 字段
            delete fm.tips;
          } else {
            fm.tips = newTips;
          }
        },
      );
    } catch {
      // 静默 — frontmatter 写入失败不应打扰用户（文件本身仍有 callout）
    }
  }

  private shouldHandle(file: TFile): boolean {
    if (file.extension !== "md") return false;
    return ALLOWED_PATH_PREFIXES.some((p) => file.path.startsWith(p));
  }

  /**
   * 用新 callouts 构建 tips[], 保留旧 tip 的 added_at（基于 text+tag+understanding 匹配）。
   * 这样用户编辑 callout 内容不会破坏 added_at 时序记录。
   */
  private buildNewTips(
    callouts: ParsedCallout[],
    oldTips: FrontmatterTip[],
  ): FrontmatterTip[] {
    const now = new Date().toISOString();
    return callouts.map((c) => {
      // P0: 有稳定 id 时按 id 匹配旧 tip(改正文不丢 added_at); 否则回退内容匹配
      const matched = c.annotationId
        ? oldTips.find((t) => t.id === c.annotationId)
        : oldTips.find(
            (t) =>
              t.text === c.content &&
              t.tag === c.tag &&
              t.understanding === c.understanding,
          );
      return {
        id: c.annotationId,
        text: c.content,
        tag: c.tag,
        understanding: c.understanding,
        added_at: matched?.added_at || now,
        source: "callout_parse",
      };
    });
  }

  private tipsEqual(a: FrontmatterTip[], b: FrontmatterTip[]): boolean {
    if (a.length !== b.length) return false;
    return a.every(
      (t, i) =>
        t.id === b[i].id &&
        t.text === b[i].text &&
        t.tag === b[i].tag &&
        t.understanding === b[i].understanding,
    );
  }
}
````

## File: backend/app/services/conversation_distiller.py
````python
# Canvas Learning System - Conversation Distiller
# Story 3.8: Structured Extraction from Conversations (AC-2)
#
# LLM-based extraction of structured data from conversation history:
#   - Error records (4-type classification, reusing Story 3.6 classifier)
#   - Tips (key knowledge points)
#   - Key Q&A highlights (valuable Q&A pairs, clustered by topic)
#   - Conversation summary (1-3 sentences)
#
# Uses Flash/lite model via LiteLLM for cost efficiency.
#
# [Source: _bmad-output/implementation-artifacts/3-8-dialog-archive-async-generation.md#Task 2]

import json
import logging
import os

import structlog
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Extraction Result Models
# ═══════════════════════════════════════════════════════════════════════════════


class ExtractedTip(BaseModel):
    """A tip extracted from conversation distillation."""

    content: str
    title: str
    tags: List[str] = Field(default_factory=list)


class ExtractedError(BaseModel):
    """An error extracted from conversation distillation."""

    description: str
    error_type: str = ""  # Will be classified by ErrorClassifier


class ExtractedQA(BaseModel):
    """A key Q&A pair extracted from conversation."""

    question: str
    answer: str
    topic: str = ""


class DistillationResult(BaseModel):
    """Complete distillation result from a conversation."""

    summary: str = Field(default="", description="1-3 sentence conversation summary")
    tips: List[ExtractedTip] = Field(default_factory=list)
    errors: List[ExtractedError] = Field(default_factory=list)
    qa_highlights: List[ExtractedQA] = Field(default_factory=list)
    distilled_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Distillation Prompt
# ═══════════════════════════════════════════════════════════════════════════════

DISTILLATION_PROMPT = """You are a learning analytics expert. Extract structured data from the following conversation between a student and a tutor AI.

Conversation:
{conversation_text}

Extract the following (return ONLY a JSON object):
{{
  "summary": "<1-3 sentence summary of the conversation topic and learning outcome>",
  "tips": [
    {{"content": "<key knowledge point text>", "title": "<short title>", "tags": ["important"|"review"]}}
  ],
  "errors": [
    {{"description": "<description of student error/misconception>"}}
  ],
  "qa_highlights": [
    {{"question": "<valuable question>", "answer": "<key answer>", "topic": "<topic label>"}}
  ]
}}

Rules:
- tips: Extract 0-5 most important knowledge points
- errors: Extract 0-3 student errors/misconceptions (if any)
- qa_highlights: Extract 0-5 most valuable Q&A exchanges
- summary: Brief, focus on what was learned
- If no errors found, return empty array
- Return valid JSON only"""


# ═══════════════════════════════════════════════════════════════════════════════
# Conversation Distiller
# ═══════════════════════════════════════════════════════════════════════════════


class ConversationDistiller:
    """
    Extracts structured learning data from conversation history.

    Story 3.8 AC-2: LLM-based distillation for the dialogue
    distillation channel.

    [Source: _bmad-output/implementation-artifacts/3-8-dialog-archive-async-generation.md#Task 2.2]
    """

    async def distill(
        self,
        messages: List[Dict[str, str]],
        node_id: str,
    ) -> DistillationResult:
        """
        Distill a conversation into structured data.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            node_id: The canvas node ID for context.

        Returns:
            DistillationResult with summary, tips, errors, and Q&A highlights.
        """
        if not messages:
            return DistillationResult()

        # Format conversation text
        conversation_text = self._format_messages(messages)

        # Story 3-8 FIX H3: Check for prompt injection in conversation text
        from app.middleware.prompt_injection_guard import check_input

        injection_check = check_input(conversation_text)
        if injection_check.is_blocked:
            logger.warning(
                "[Story 3.8] Distillation input blocked: risk_score=%.2f, patterns=%s, node_id=%s",
                injection_check.risk_score,
                injection_check.matched_patterns,
                node_id,
            )
            return DistillationResult(
                summary=f"Conversation with {len(messages)} messages (input safety check failed)"
            )

        # Truncate to avoid token limits (keep last ~8000 chars)
        if len(conversation_text) > 8000:
            conversation_text = (
                "...(earlier messages truncated)...\n\n" + conversation_text[-8000:]
            )

        try:
            return await self._llm_distill(conversation_text)
        except Exception as e:
            logger.warning(f"[Story 3.8] Distillation failed: {e}")
            # Return empty result on failure (non-blocking)
            return DistillationResult(
                summary=f"Conversation with {len(messages)} messages (distillation failed)"
            )

    async def distill_and_persist(
        self,
        messages: List[Dict[str, str]],
        node_id: str,
        group_id: str,
    ) -> DistillationResult:
        """
        Distill a conversation and persist results.

        Args:
            messages: List of message dicts.
            node_id: Canvas node ID.
            group_id: group_id for memory isolation.

        Returns:
            DistillationResult.
        """
        result = await self.distill(messages, node_id)

        # Persist distillation results
        await self._persist_distillation(result, node_id, group_id)

        return result

    async def _llm_distill(self, conversation_text: str) -> DistillationResult:
        """
        Use LLM to extract structured data from conversation.

        Uses a cost-efficient model (Flash) via LiteLLM.

        Args:
            conversation_text: Formatted conversation text.

        Returns:
            DistillationResult parsed from LLM response.
        """
        import litellm

        from app.config import settings
        from app.core.litellm_config import (
            format_litellm_model,
            get_runtime_model_config,
        )

        # F9 Distillation model cascade (3 tiers):
        # Tier 1: Ollama Qwen3 local (free, Chinese-native, no encoding issues)
        # Tier 2: CLIProxyAPI Claude Haiku (subscription, English-only due to encoding bug)
        # Tier 3: Configured LiteLLM provider (API key fallback)
        ollama_base = os.environ.get(
            "OLLAMA_API_BASE", "http://canvas-learning-system-ollama:11434"
        )
        ollama_model = os.environ.get("DISTILL_OLLAMA_MODEL", "ollama/qwen3:8b")
        cli_proxy_base = os.environ.get(
            "CLI_PROXY_API_BASE", "http://cli-proxy-api:8317/v1"
        )
        cli_proxy_key = [REDACTED:env-cred]"CLI_PROXY_API_KEY", "dummy")
        cli_proxy_model = os.environ.get(
            "CLI_PROXY_MODEL", "openai/claude-haiku-4-5-20251001"
        )

        prompt = DISTILLATION_PROMPT.format(conversation_text=conversation_text)
        response = None

        # M3 Tier 0 (2026-07-13): 宿主 llama-server Qwen3.5-35B — canary 已放行
        # (50/50 零失败, 见 scripts/graphiti_schema_canary.py)。GRAPHITI_LLM_PROVIDER
        # =local 时蒸馏与 Graphiti 语义抽取共用同一运行时, 归档链全本地。
        # 失败静默降级到原有 Tier1-3 (Iron Rule 5: Tier2 cli-proxy 保持休眠)。
        if (os.environ.get("GRAPHITI_LLM_PROVIDER") or "").strip().lower() == "local":
            local_base = os.environ.get(
                "GRAPHITI_LLM_BASE_URL", "http://host.docker.internal:12341/v1"
            )
            local_model = (
                os.environ.get("GRAPHITI_LLM_MODEL") or "qwen3.5-35b-a3b-q4_k_s"
            )
            try:
                response = await litellm.acompletion(
                    model=f"openai/{local_model}",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1500,
                    temperature=0.2,
                    api_key=[REDACTED:env-cred]"GRAPHITI_LLM_API_KEY") or "local",
                    api_base=local_base,
                    timeout=45,
                )
                logger.info("[M3] Distillation via local llama-server succeeded")
            except Exception as local_err:
                logger.warning(
                    "[M3] local llama-server Tier0 failed: %s (type=%s)",
                    str(local_err)[:200],
                    type(local_err).__name__,
                )
                response = None

        # Tier 1: Ollama Qwen3 (best for Chinese content)
        if response is None:
            try:
                response = await litellm.acompletion(
                    model=ollama_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1500,
                    temperature=0.2,
                    api_base=ollama_base,
                    timeout=30,  # V7: reduced from 120s; 30s covers Ollama cold start + inference
                )
                logger.info("[F9] Distillation via Ollama Qwen3 succeeded")
            except Exception as ollama_err:
                logger.warning(
                    "[F9] Ollama Tier1 failed: %s (type=%s)",
                    str(ollama_err)[:200],
                    type(ollama_err).__name__,
                )

                # Tier 2: CLIProxyAPI (Claude subscription, English content only)
                try:
                    response = await litellm.acompletion(
                        model=cli_proxy_model,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=1500,
                        temperature=0.2,
                        api_key=[REDACTED:env-cred]
                        api_base=cli_proxy_base,
                        timeout=60,
                    )
                    logger.info("[F9] Distillation via CLIProxyAPI succeeded")
                except Exception as proxy_err:
                    logger.warning(
                        "[F9] CLIProxyAPI failed (%s), trying configured provider",
                        str(proxy_err)[:100],
                    )

                    # Tier 3: Configured LiteLLM provider (requires API key)
                    runtime_cfg = get_runtime_model_config()
                    api_key = [REDACTED:env-cred]
                        runtime_cfg.get_scoring_api_key() or settings.AI_API_KEY or None
                    )
                    provider = settings.AI_PROVIDER
                    model_name = settings.AI_MODEL_NAME
                    model = format_litellm_model(provider, model_name)
                    response = await litellm.acompletion(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=1500,
                        temperature=0.2,
                        api_key=[REDACTED:env-cred]
                    )

        content = response.choices[0].message.content.strip()

        # Strip markdown code fences if present (LLMs often wrap JSON)
        if content.startswith("```"):
            # Remove opening fence (e.g. ```json or ```)
            first_newline = content.index("\n") if "\n" in content else 3
            content = content[first_newline + 1 :]
            # Remove closing fence
            if content.endswith("```"):
                content = content[:-3].strip()

        # Parse JSON response
        parsed = json.loads(content)

        tips = [
            ExtractedTip(
                content=t.get("content", ""),
                title=t.get("title", "Untitled"),
                tags=t.get("tags", []),
            )
            for t in parsed.get("tips", [])
            if t.get("content")
        ]

        errors = [
            ExtractedError(description=e.get("description", ""))
            for e in parsed.get("errors", [])
            if e.get("description")
        ]

        qa_highlights = [
            ExtractedQA(
                question=qa.get("question", ""),
                answer=qa.get("answer", ""),
                topic=qa.get("topic", ""),
            )
            for qa in parsed.get("qa_highlights", [])
            if qa.get("question") and qa.get("answer")
        ]

        return DistillationResult(
            summary=parsed.get("summary", ""),
            tips=tips,
            errors=errors,
            qa_highlights=qa_highlights,
        )

    async def _persist_distillation(
        self,
        result: DistillationResult,
        node_id: str,
        group_id: str,
    ) -> None:
        """
        Persist distillation results.

        Args:
            result: The distillation result to persist.
            node_id: Canvas node ID.
            group_id: group_id for memory isolation.
        """
        try:
            from app.services.memory_service import get_memory_service

            memory_svc = await get_memory_service()

            # Persist summary
            if result.summary:
                await memory_svc.record_knowledge_entity(
                    event_type="conversation_distillation",
                    content=f"Distilled summary for node {node_id}: {result.summary}",
                    metadata={
                        "node_id": node_id,
                        "distilled_at": result.distilled_at,
                        "tip_count": len(result.tips),
                        "error_count": len(result.errors),
                        "qa_count": len(result.qa_highlights),
                    },
                    group_id=group_id,
                )

            # Persist tips
            for tip in result.tips:
                await memory_svc.record_knowledge_entity(
                    event_type="learning_tip",
                    content=f"Tip: {tip.title} | Content: {tip.content}",
                    metadata={
                        "tip_id": str(uuid.uuid4()),
                        "title": tip.title,
                        "content": tip.content,
                        "tags": tip.tags,
                        "node_id": node_id,
                        "source": "distillation",
                    },
                    group_id=group_id,
                )

            # Persist errors via error classifier
            # 批次3' P14a (MEM-FLYWHEEL): 旧代码 classify() 返回值直接丢弃 —
            # 蒸馏错误从未落 error_candidates[], SessionEnd 自动生产错误候选
            # 的管道在此断裂 (测试种子耗尽即枯死的根因)。改为 classify_with_pedagogy
            # → write_error_dual(candidate_only) 落节点候选区, 等用户复盘 accept。
            if result.errors:
                from app.services.error_classifier import get_error_classifier
                from app.services.error_writer import write_error_dual
                from app.services.frontmatter_signals import _node_md_path
                from app.services.learning_event_log import append_event

                classifier = get_error_classifier()
                node_path = _node_md_path(node_id) if node_id else None
                for error in result.errors:
                    try:
                        classified = await classifier.classify_with_pedagogy(
                            error_description=error.description,
                            node_id=node_id,
                            context="(extracted from conversation distillation)",
                        )
                        if node_path is None:
                            logger.warning(
                                f"[P14a] 节点 md 不存在, 蒸馏候选无处落: node={node_id}"
                            )
                            continue
                        dual = await write_error_dual(
                            file_path=node_path,
                            error=classified,
                            node_id=node_id,
                            session_id="distillation",
                            mode="candidate_only",
                            group_id=group_id or "",
                            ai_reason="conversation distillation (SessionEnd)",
                        )
                        cand_id = dual.get("candidate_id")
                        if cand_id:
                            append_event(
                                "candidate_created",
                                event_id=f"cand:{cand_id}",
                                node_id=node_id,
                                payload={
                                    "source": "distillation",
                                    "description": error.description[:200],
                                },
                            )
                    except Exception as e:
                        logger.warning(
                            f"[Story 3.8] Error classification failed during distillation: {e}"
                        )

            # Persist Q&A highlights
            for qa in result.qa_highlights:
                await memory_svc.record_knowledge_entity(
                    event_type="qa_highlight",
                    content=f"Q: {qa.question} | A: {qa.answer}",
                    metadata={
                        "question": qa.question,
                        "answer": qa.answer,
                        "topic": qa.topic,
                        "node_id": node_id,
                        "source": "distillation",
                    },
                    group_id=group_id,
                )

            logger.info(
                f"[Story 3.8] Distillation persisted: node={node_id} "
                f"tips={len(result.tips)} errors={len(result.errors)} "
                f"qa={len(result.qa_highlights)}"
            )

        except Exception as e:
            logger.warning(f"[Story 3.8] Failed to persist distillation results: {e}")

    def _format_messages(self, messages: List[Dict[str, str]]) -> str:
        """Format message list into readable conversation text."""
        lines = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            prefix = "Student" if role == "user" else "Tutor"
            lines.append(f"{prefix}: {content}")
        return "\n\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════════════════════════════════════

_distiller_instance: Optional[ConversationDistiller] = None


def get_conversation_distiller() -> ConversationDistiller:
    """Get or create the singleton ConversationDistiller instance."""
    global _distiller_instance
    if _distiller_instance is None:
        _distiller_instance = ConversationDistiller()
    return _distiller_instance
````

## File: frontend/obsidian-plugin/src/node-derivation.ts
````typescript
/**
 * Story 1.17 v4.0 — 100% plugin 脚本派生（零 LLM 调用）
 *
 * 用户决策（2026-05-01）："派生 = 单独拉出来放在一个全新的文档来进行讨论"。
 * 不再 AI 生成正文，节点正文 = 选中文本 quote + 三段空白模板让用户自己写。
 *
 * 全部 7 步 deterministic（<200ms 完成）：
 *   1. 启发式提取概念名（无 LLM）
 *   2. 重名处理（_2 / _3 / ...）
 *   3. 构造 frontmatter（用 processFrontMatter API 保 YAML 安全）
 *   4. 生成节点正文（选中文本 quote + 三段空白模板）— **终态**，不等 AI
 *   5. wikilink + 关系 callout 模板（替换源笔记选中文本）
 *   6. 白板 ## Concepts append 行（无 ai_pending status）
 *   7. Notice 提示 — 不切 Claudian / 不写剪贴板
 *
 * 旧 v3 hybrid 阶段 2（buildPhase2SkillPrompt / AI_BODY_PLACEHOLDER）已删除 —
 *   Skill ai-linked-doc-fill v5.0 也一起删除。
 */

const ILLEGAL_FILENAME_CHARS = /[\\/:*?"<>|#^[\]]/g;
const WHITESPACE_RUN = /\s+/g;

/**
 * 启发式从选中文本提取概念名作为文件名。
 *
 * 中文：取前 2-10 个汉字（按句号 / 标点 / 换行截断）
 * 英文：取前 3-6 个 kebab-case 单词
 * 混合：保留字母数字汉字，连接符 -
 *
 * 全失败时 fallback 到 `derived-<6 位 timestamp>`。
 */
export function deriveConceptStub(selected: string): string {
  if (!selected) return fallbackStub();
  let head = selected.split(/[\n。.！!？?；;]/u)[0] ?? selected;
  head = head.trim();
  if (!head) return fallbackStub();

  const cleaned = head
    .replace(ILLEGAL_FILENAME_CHARS, "")
    .replace(WHITESPACE_RUN, "-")
    .replace(/^-+|-+$/g, "");

  if (!cleaned) return fallbackStub();

  const truncated = truncateUnicodeAware(cleaned, 40);
  if (!truncated) return fallbackStub();

  return truncated;
}

function fallbackStub(): string {
  const ts = new Date()
    .toISOString()
    .replace(/[-:T.Z]/g, "")
    .slice(8, 14);
  return `derived-${ts}`;
}

function truncateUnicodeAware(s: string, maxLen: number): string {
  const chars = Array.from(s);
  if (chars.length <= maxLen) return s;
  const cut = chars.slice(0, maxLen).join("");
  // P4 (轨道 B 2026-07-20): 硬砍会产生句中截断文件名
  // (Eigenvalues-are-special-vectors-that-sat)。回退到最近的 - 词边界;
  // 边界太靠前 (< maxLen/2, 如无连字符的中文) 则保留硬砍。
  const lastDash = cut.lastIndexOf("-");
  if (lastDash >= Math.floor(maxLen / 2)) {
    return cut.slice(0, lastDash);
  }
  return cut;
}

/**
 * 重名处理：节点池里同名 → 加 _2 / _3 / ... / _9。9+ 重名抛错。
 */
export function resolveUniqueNodeName(
  desiredStub: string,
  existsCheck: (path: string) => boolean,
): string {
  const baseName = `节点/${desiredStub}.md`;
  if (!existsCheck(baseName)) return desiredStub;
  for (let n = 2; n <= 9; n++) {
    const candidate = `节点/${desiredStub}_${n}.md`;
    if (!existsCheck(candidate)) return `${desiredStub}_${n}`;
  }
  throw new Error(
    `节点池 9+ 重名（${desiredStub}），请考虑概念拆分或手动改名`,
  );
}

const RELATION_CN_LABEL: Record<string, string> = {
  prerequisite: "先修",
  depends_on: "依赖",
  refines: "细化",
  extends: "扩展",
  example_of: "例子",
  contradicts: "反驳",
  related_to: "相关",
};

export function getRelationCnLabel(key: [REDACTED:env-cred] string {
  return RELATION_CN_LABEL[key] ?? key;
}

/**
 * 构造源笔记替换块（v4.1 保留原文）。
 *
 * 用户决策（2026-05-01）："虽然从原文拉出来作为新节点单独讨论，但是不要把原文删除了"。
 * 改成：原文逐字保留 + 下方紧跟 callout 标记派生关系 + wikilink。
 *
 * 输出格式（4 行 / 5 行）：
 *   <原选中文本，逐字不动>
 *   <空行>
 *   > [!relation/<key>]+ 已派生为 [[节点/<concept>]] · <中文标签>
 *   > 这段文本已被派生为独立讨论节点（保留原文供你后续阅读 + 派生节点供你深度展开）。
 *   > 你的派生意图: <description>     ← 仅当 description 非空
 *
 * PKM 共识对齐（Roam block-ref / Andy Matuschak transclude / Zettelkasten 非破坏性原则）：
 *   派生 ≠ 删除原文。原文作为"原始上下文"保留，派生节点作为"独立讨论容器"新建。
 */
export function buildSourceReplacement(
  conceptName: string,
  relationKey: [REDACTED:env-cred]
  description: string,
  selected: string,
): string {
  const cnLabel = getRelationCnLabel(relationKey);
  const trimmedSelected = selected.trim();
  const lines = [
    trimmedSelected,
    "",
    `> [!relation/${relationKey}]+ 已派生为 [[节点/${conceptName}]] · ${cnLabel}`,
    `> 这段文本已被派生为独立讨论节点（保留原文供你后续阅读 + 派生节点供你深度展开）。`,
  ];
  const trimmedDesc = description.trim();
  if (trimmedDesc) {
    lines.push(`> 你的派生意图: ${trimmedDesc}`);
  }
  return lines.join("\n");
}

/**
 * 构造新节点 frontmatter 数据对象（供 processFrontMatter 回调注入）。
 *
 * ⛔ 不要返回字符串拼接的 YAML — agent 1 验证：含 wikilink "[[原白板/X]]" 的字符串
 *   纯拼接会被 YAML 引擎误解析。必须用 processFrontMatter callback 让 Obsidian 处理转义。
 */
export interface NodeFrontmatter {
  type: "concept";
  mastery_score: number;
  created_at: string;
  source_note: string;
  source_board: string;
  created_from: "ai_linked_doc";
  up: string;
  "derived-from": string;
  relationships: Array<{
    type: string;
    target: string;
    description?: string;
    // 批次4' 3-1/3-2 (MEM-FLYWHEEL): 派生时刻理解快照 — 投影 sync 透传入
    // CANVAS_EDGE 永久留档,「当时为什么困惑」事后可重建
    derived_at?: string;
    source_mastery_at_derivation?: number;
    confusion?: string;
  }>;
}

export function buildNodeFrontmatter(args: {
  sourceNoteStem: string;
  activeBoard: string;
  relationKey: [REDACTED:env-cred]
  description: string;
  createdAt: string;
  sourceMastery?: number | null;
  confusion?: string | null;
}): NodeFrontmatter {
  const sourceWikilink = `[[${args.sourceNoteStem}]]`;
  const rel: NodeFrontmatter["relationships"][0] = {
    type: args.relationKey,
    target: sourceWikilink,
    derived_at: args.createdAt,
  };
  const trimmedDesc = args.description.trim();
  if (trimmedDesc) rel.description = trimmedDesc;
  if (typeof args.sourceMastery === "number") {
    rel.source_mastery_at_derivation = args.sourceMastery;
  }
  const trimmedConfusion = (args.confusion ?? "").trim();
  if (trimmedConfusion) rel.confusion = trimmedConfusion.slice(0, 300);
  return {
    type: "concept",
    mastery_score: 0.3,
    created_at: args.createdAt,
    source_note: sourceWikilink,
    source_board: `[[原白板/${args.activeBoard}]]`,
    created_from: "ai_linked_doc",
    up: sourceWikilink,
    "derived-from": sourceWikilink,
    relationships: [rel],
  };
}

/**
 * 批次4' 3-1 (MEM-FLYWHEEL): 选中文本附近（前后 10 行）最近一条
 * [!question]/[!error] 批注 → 派生时刻困惑快照。找不到返回 null。
 */
export function extractNearbyConfusion(
  sourceContent: string,
  selected: string,
): string | null {
  const firstSelLine = selected.trim().split("\n")[0] ?? "";
  if (!firstSelLine) return null;
  const idx = sourceContent.indexOf(firstSelLine);
  if (idx < 0) return null;
  const lines = sourceContent.split("\n");
  let cum = 0;
  let selLine = 0;
  for (let i = 0; i < lines.length; i++) {
    cum += lines[i].length + 1;
    if (cum > idx) {
      selLine = i;
      break;
    }
  }
  const lo = Math.max(0, selLine - 10);
  const hi = Math.min(lines.length - 1, selLine + 10);
  let best: string | null = null;
  let bestDist = Infinity;
  for (let i = lo; i <= hi; i++) {
    const m = lines[i].match(/^>\s*\[!(question|error)\]\+?\s*(.*)$/i);
    if (!m) continue;
    const dist = Math.abs(i - selLine);
    if (dist >= bestDist) continue;
    const inline = (m[2] ?? "").trim();
    const nextLine = (lines[i + 1] ?? "").replace(/^>\s*/, "").trim();
    const text = inline || nextLine;
    if (text) {
      bestDist = dist;
      best = text;
    }
  }
  return best;
}

/**
 * 批次3'/4' (MEM-FLYWHEEL): node_derived 学习事件行 (learning_events.jsonl
 * append-only, 幂等键 = derive:<节点名>, schema 与 backend
 * learning_event_log.py 对齐)。
 */
export function buildNodeDerivedEventLine(
  conceptName: string,
  createdAt: string,
): { eventId: string; line: string } {
  const eventId = `derive:${conceptName}`;
  const record = {
    event_id: eventId,
    event_version: 1,
    event_type: "node_derived",
    node_id: conceptName,
    recorded_at: createdAt,
    effective_at: createdAt,
    payload: {},
  };
  return { eventId, line: JSON.stringify(record) + "\n" };
}

/**
 * 节点正文模板（v4.0 终态，无 AI 生成）。
 *
 * 用户决策："派生 = 拉出来放新文档讨论"。正文 = 选中文本 quote + 三段空白让用户自己写。
 * 用户后续可在节点 md 内打开 Claudian sidebar 围绕这个概念展开讨论。
 *
 * Quote 块用 [!quote]+ callout 友好显示原文；三段（核心概念 / 关键点 / 关联概念）
 * 提供"思考起点"模板（PKM Evergreen Notes 共识：用户必须自己写以触发深度思考）。
 */
export function buildNodeBody(
  conceptName: string,
  selected: string,
  sourceNoteStem: string,
): string {
  const trimmedSelected = selected.trim();
  return [
    `# ${conceptName}`,
    "",
    `> [!quote]+ 派生起点（来自 [[${sourceNoteStem}]] 选中文本）`,
    `> ${trimmedSelected.replace(/\n/g, "\n> ")}`,
    "",
    "## 核心概念",
    "",
    "（你的 1-2 句精准定义。这个概念 *是什么* / *为什么重要*？）",
    "",
    "## 关键点",
    "",
    "- ",
    "",
    "## 关联概念",
    "",
    `- [[${sourceNoteStem}]] — extracted from this note`,
    "",
    "---",
    "",
    "> [!tip] 💬 围绕这个概念讨论",
    "> 这个节点是**讨论容器**，不是 AI 写好的内容。你可以：",
    "> - 在上面三段空白处写下你的理解（最有学习价值）",
    "> - 在 Claude Code 里围绕本节点和 Claude 自由对话（节点级 AI 对话）",
    "> - `Cmd+Shift+D` 选中本节点正文继续派生子节点",
    "> - `Cmd+Shift+A` 选中文字加 Tips/疑问/错误标注",
    "",
  ].join("\n");
}

/**
 * 白板 ## Concepts append 行（v4.0：无 ai_pending status，因为不再有 AI 阶段）。
 */
export function buildBoardConceptsLine(
  conceptName: string,
  relationKey: [REDACTED:env-cred]
): string {
  return `- [[节点/${conceptName}]] — ${relationKey}, weak (0.30)`;
}

export function buildBoardActivityLine(
  conceptName: string,
  sourceNoteStem: string,
  relationKey: [REDACTED:env-cred]
  isoTimestamp: string,
): string {
  return `- ${isoTimestamp}: Extracted [[节点/${conceptName}]] via canvas:ai-linked-doc from [[${sourceNoteStem}]]（关系: ${relationKey}）`;
}
````

## File: backend/app/api/v1/endpoints/memory.py
````python
# Canvas Learning System - Memory API Endpoints
# Story 22.4: 学习历史存储与查询API
# Story 30.8: 多学科隔离与group_id支持
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: APIRouter, Depends)
"""
Memory API Endpoints - Learning history storage and query.

NOTE: All endpoints delegate to MemoryService which requires a live Neo4j
connection. When Neo4j is unavailable, endpoints will return 500 errors.
Endpoint logic is real (not stubbed), but depends on MemoryService health.

Story 22.4 Implementation:
- POST /episodes: Record learning events (AC-22.4.1)
- GET /episodes: Query learning history (AC-22.4.2)
- GET /concepts/{id}/history: Query concept history (AC-22.4.3)
- GET /review-suggestions: Get review suggestions (AC-22.4.4)

Story 30.8 Implementation:
- GET /episodes: Added subject query parameter (AC-30.8.3)
- GET /review-suggestions: Added subject query parameter (AC-30.8.3)

[Source: docs/prd/EPIC-22-MEMORY-SYSTEM-NEO4J-GRAPHITI.md#Story-22.4]
[Source: docs/stories/22.4.story.md#API端点实现]
[Source: docs/stories/30.8.story.md#Task-3.2]
"""

import logging
from datetime import datetime
from typing import Annotated, List, Optional

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: APIRouter)
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.models.memory_schemas import (
    BatchEpisodesRequest,
    BatchEpisodesResponse,
    BatchErrorItem,
    ConceptHistoryResponse,
    LearningEpisodeCreate,
    LearningEpisodeResponse,
    LearningHistoryItem,
    LearningHistoryResponse,
    MemoryHealthResponse,
    ReviewSuggestionResponse,
)
from app.security import require_internal_api_key
from app.services.memory_service import (
    MemoryService,
    get_memory_service,
)

logger = logging.getLogger(__name__)

# ChatGPT-DR-2026-05-13 P0-3: Memory API 统一鉴权 — 6 个 non-extract endpoint
# endpoint-level 加 Depends(require_internal_api_key), 防匿名 LAN/external 访问.
# /extract-conversation 保留 _require_observer_token 单独鉴权 (sidecar 兼容).
memory_router = APIRouter()


# Wave-5 Stage B (2026-05-12) — Multi-vault ContextVar 注入辅助.
# 3 memory endpoints 此前无 vault_id 隔离 → 跨 vault 学习历史串库 (P0).
def _resolve_vault_group_id(
    vault_id: Optional[str],
    subject_id: Optional[str] = None,
    canvas_path: Optional[str] = None,
    legacy_group_id: Optional[str] = None,
) -> str:
    """Wave-5 Stage B — vault_id → ContextVar 注入 + 派生 group_id."""
    from app.config import sanitize_vault_id
    from app.core.subject_config import (
        build_vault_group_id,
        canonical_group_id,
        set_current_subject_id,
    )

    if vault_id and vault_id.strip():
        sanitized = sanitize_vault_id(vault_id)
        derived = build_vault_group_id(
            sanitized,
            subject_id=subject_id,
            canvas_path=canvas_path,
        )
    elif legacy_group_id and legacy_group_id.strip():
        logger.warning(
            "Wave-5 Stage B: memory endpoint vault_id missing, "
            "falling back to deprecated group_id=%s",
            legacy_group_id,
        )
        derived = canonical_group_id(legacy_group_id)
    else:
        # 批次1'① (MEM-FLYWHEEL): 双缺失不再落 DEFAULT_GROUP_ID (vault:default
        # 污染桶) — 推导当前 vault 组, 与 P15 MCP 工具模式一致。缺失回落
        # default 桶只准存在于离线迁移工具, 不在线上主路径。
        from app.core.subject_config import default_vault_group_id

        logger.warning(
            "Wave-5 Stage B: memory endpoint both vault_id and group_id missing, "
            "deriving current vault group (fail-closed, no DEFAULT_GROUP_ID)"
        )
        derived = default_vault_group_id()

    set_current_subject_id(derived)
    return derived


# =============================================================================
# Dependency Injection - Singleton Pattern for Neo4j Connection Pooling
# Singleton lives in app.services.memory_service (single source of truth).
# This module re-exports for FastAPI Depends() usage.
# =============================================================================

# Type alias for MemoryService dependency — delegates to service-layer singleton
MemoryServiceDep = Annotated[MemoryService, Depends(get_memory_service)]


# =============================================================================
# POST /episodes - Record learning event (AC-22.4.1)
# ✅ Verified from docs/stories/22.4.story.md#API端点实现
# =============================================================================


@memory_router.post(
    "/episodes",
    response_model=LearningEpisodeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="记录学习事件",
    description="记录用户的学习事件，存储到Neo4j和Graphiti",
    dependencies=[Depends(require_internal_api_key)],  # P0-3
)
async def create_learning_episode(
    episode: LearningEpisodeCreate, memory_service: MemoryServiceDep
) -> LearningEpisodeResponse:
    """
    记录学习事件

    ✅ Verified from docs/stories/22.4.story.md#create_learning_episode:
    - 调用 memory_service.record_learning_event()
    - 返回 episode_id 和 status

    Wave-5 Stage B (2026-05-12) — Multi-vault P0-2:
    - episode.vault_id 必填, 注入 ContextVar 防跨 vault 学习记录串库.

    [Source: docs/stories/22.4.story.md#API端点实现]
    """
    # Wave-5 Stage B — vault_id ContextVar 注入
    _resolve_vault_group_id(
        episode.vault_id,
        subject_id=episode.subject_id,
        canvas_path=episode.canvas_path,
    )

    try:
        episode_id = await memory_service.record_learning_event(
            user_id=episode.user_id,
            canvas_path=episode.canvas_path,
            node_id=episode.node_id,
            concept=episode.concept,
            agent_type=episode.agent_type,
            score=episode.score,
            duration_seconds=episode.duration_seconds,
        )

        logger.info(f"Created learning episode: {episode_id}")
        return LearningEpisodeResponse(episode_id=episode_id, status="created")

    except Exception as e:
        logger.error(f"Failed to create learning episode: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record learning event: {str(e)}",
        )


# =============================================================================
# GET /episodes - Query learning history (AC-22.4.2, AC-22.4.5)
# ✅ Verified from docs/stories/22.4.story.md#API端点实现
# =============================================================================


@memory_router.get(
    "/episodes",
    response_model=LearningHistoryResponse,
    summary="查询学习历史",
    dependencies=[Depends(require_internal_api_key)],  # P0-3
    description="查询用户的学习历史，支持分页和过滤",
)
async def get_learning_history(
    memory_service: MemoryServiceDep,
    user_id: str = Query(..., description="用户ID"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    concept: Optional[str] = Query(None, description="概念过滤"),
    subject: Optional[str] = Query(None, description="学科过滤 (AC-30.8.3)"),
    canvas_path: Optional[str] = Query(
        None, description="Canvas路径 (Epic 6: canvas-scoped filtering)"
    ),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页大小"),
    vault_id: Optional[str] = Query(
        default=None,
        min_length=1,
        description=(
            "Multi-vault P0-2 (Wave-5 Stage B) — 推荐必填. 注入 ContextVar 防跨 vault 历史串库. "
            "Plugin 端 inferVaultId(app.vault.getName()) 取."
        ),
    ),
    subject_id: Optional[str] = Query(default=None),
    group_id: Optional[str] = Query(
        default=None,
        deprecated=True,
        description="Deprecated — 改用 vault_id.",
    ),
) -> LearningHistoryResponse:
    """
    查询学习历史

    ✅ Verified from docs/stories/22.4.story.md#get_learning_history:
    - 支持 start_date 和 end_date 过滤
    - 支持 concept 过滤
    - 支持分页 (page, page_size)

    ✅ Verified from docs/stories/30.8.story.md#AC-30.8.3:
    - 支持 subject 查询参数过滤

    ✅ Epic 6: 支持 canvas_path 查询参数进行 canvas 级别过滤

    Wave-5 Stage B (2026-05-12) — Multi-vault P0-2:
    - vault_id 推荐必填, 注入 ContextVar 防跨 vault 历史串库.

    [Source: docs/stories/22.4.story.md#API端点实现]
    [Source: docs/stories/30.8.story.md#Task-3.2]
    """
    # Wave-5 Stage B — vault_id ContextVar 注入
    _resolve_vault_group_id(
        vault_id,
        subject_id=subject_id,
        canvas_path=canvas_path,
        legacy_group_id=group_id,
    )

    try:
        result = await memory_service.get_learning_history(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            concept=concept,
            subject=subject,
            canvas_path=canvas_path,
            page=page,
            page_size=page_size,
        )

        # Convert items to LearningHistoryItem models
        # Note: Use `or ""` instead of default param to handle None values
        # from legacy data where agent_type may be stored as null
        items = [
            LearningHistoryItem(
                episode_id=item.get("episode_id") or "",
                user_id=item.get("user_id") or "",
                canvas_path=item.get("canvas_path") or "",
                node_id=item.get("node_id") or "",
                concept=item.get("concept") or "",
                agent_type=item.get("agent_type") or "unknown",
                score=item.get("score"),
                duration_seconds=item.get("duration_seconds"),
                timestamp=item.get("timestamp") or "",
            )
            for item in result.get("items", [])
        ]

        return LearningHistoryResponse(
            items=items,
            total=result.get("total", 0),
            page=result.get("page", 1),
            page_size=result.get("page_size", 50),
            pages=result.get("pages", 0),
        )

    except Exception as e:
        logger.error(f"Failed to get learning history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query learning history: {str(e)}",
        )


# =============================================================================
# GET /concepts/{id}/history - Query concept history (AC-22.4.3)
# ✅ Verified from AC-22.4.3
# =============================================================================


@memory_router.get(
    "/concepts/{concept_id}/history",
    response_model=ConceptHistoryResponse,
    summary="查询概念学习历史",
    description="查询特定概念的学习历史，包含时间线和得分变化",
    dependencies=[Depends(require_internal_api_key)],  # P0-3
)
async def get_concept_history(
    concept_id: str,
    memory_service: MemoryServiceDep,
    user_id: Optional[str] = Query(None, description="用户ID (optional)"),
    limit: int = Query(50, ge=1, le=200, description="最大返回数量"),
) -> ConceptHistoryResponse:
    """
    查询概念学习历史

    ✅ Verified from AC-22.4.3:
    - 按概念ID查询学习历史
    - 返回时间线数据
    - 包含得分变化

    [Source: docs/stories/22.4.story.md#Dev-Notes]
    """
    try:
        result = await memory_service.get_concept_history(
            concept_id=concept_id, user_id=user_id, limit=limit
        )

        return ConceptHistoryResponse(**result)

    except Exception as e:
        logger.error(f"Failed to get concept history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query concept history: {str(e)}",
        )


# =============================================================================
# GET /review-suggestions - Get review suggestions (AC-22.4.4)
# ✅ Verified from docs/stories/22.4.story.md#API端点实现
# =============================================================================


@memory_router.get(
    "/review-suggestions",
    response_model=List[ReviewSuggestionResponse],
    summary="获取复习建议",
    description="获取基于艾宾浩斯遗忘曲线的复习建议",
    dependencies=[Depends(require_internal_api_key)],  # P0-3
)
async def get_review_suggestions(
    memory_service: MemoryServiceDep,
    user_id: str = Query(..., description="用户ID"),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    subject: Optional[str] = Query(None, description="学科过滤 (AC-30.8.3)"),
    canvas_path: Optional[str] = Query(
        None, description="Canvas路径 (Epic 6: canvas-scoped filtering)"
    ),
    vault_id: Optional[str] = Query(
        default=None,
        min_length=1,
        description="Multi-vault P0-2 — 推荐必填. 注入 ContextVar 防跨 vault 复习建议串库.",
    ),
    subject_id: Optional[str] = Query(default=None),
    group_id: Optional[str] = Query(
        default=None, deprecated=True, description="Deprecated — 改用 vault_id."
    ),
) -> List[ReviewSuggestionResponse]:
    """
    获取复习建议

    ✅ Verified from docs/stories/22.4.story.md#get_review_suggestions:
    - 基于艾宾浩斯遗忘曲线
    - 返回需要复习的概念
    - 包含优先级排序

    ✅ Verified from docs/stories/30.8.story.md#AC-30.8.3:
    - 支持 subject 查询参数过滤

    ✅ Epic 6: 支持 canvas_path 查询参数进行 canvas 级别过滤

    Wave-5 Stage B (2026-05-12) — Multi-vault P0-2:
    - vault_id 推荐必填, 注入 ContextVar 防跨 vault 复习建议串库.

    [Source: docs/stories/22.4.story.md#API端点实现]
    [Source: docs/stories/30.8.story.md#Task-3.2]
    """
    # Wave-5 Stage B — vault_id ContextVar 注入
    _resolve_vault_group_id(
        vault_id,
        subject_id=subject_id,
        canvas_path=canvas_path,
        legacy_group_id=group_id,
    )

    try:
        suggestions = await memory_service.get_review_suggestions(
            user_id=user_id, limit=limit, subject=subject, canvas_path=canvas_path
        )

        return [
            ReviewSuggestionResponse(
                concept=s.get("concept", ""),
                concept_id=s.get("concept_id", ""),
                last_score=s.get("last_score"),
                review_count=s.get("review_count", 0),
                due_date=s.get("due_date", ""),
                priority=s.get("priority", "medium"),
            )
            for s in suggestions
        ]

    except Exception as e:
        logger.error(f"Failed to get review suggestions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get review suggestions: {str(e)}",
        )


# =============================================================================
# GET /health - Memory system health check (AC-30.3.5)
# ✅ Verified from Story 30.3
# =============================================================================


@memory_router.get(
    "/health",
    response_model=MemoryHealthResponse,
    summary="Memory系统健康检查",
    description="获取3层记忆系统的健康状态",
    dependencies=[Depends(require_internal_api_key)],  # P0-3
)
async def get_memory_health(memory_service: MemoryServiceDep) -> MemoryHealthResponse:
    """
    获取Memory系统健康状态

    ✅ Verified from Story 30.3 AC-30.3.5:
    - 返回 Temporal (FSRS/SQLite) 层状态
    - 返回 Graphiti (Neo4j) 层状态
    - 返回 Semantic (LanceDB) 层状态
    - 整体状态: healthy/degraded/unhealthy

    [Source: docs/stories/30.3.memory-api-health-endpoints.story.md#AC-30.3.5]
    """
    try:
        health_status = await memory_service.get_health_status()
        return MemoryHealthResponse(**health_status)

    except Exception as e:
        logger.error(f"Failed to get memory health status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get memory health status: {str(e)}",
        )


# =============================================================================
# POST /episodes/batch - Batch record learning events (AC-30.3.10)
# ✅ Verified from Story 30.3
# =============================================================================


@memory_router.post(
    "/episodes/batch",
    response_model=BatchEpisodesResponse,
    status_code=status.HTTP_200_OK,
    summary="批量记录学习事件",
    description="批量记录Canvas节点颜色变化等学习事件(最多50个)",
    dependencies=[Depends(require_internal_api_key)],  # P0-3
)
async def create_batch_episodes(
    request: BatchEpisodesRequest, memory_service: MemoryServiceDep
) -> BatchEpisodesResponse:
    """
    批量记录学习事件

    ✅ Verified from Story 30.3 AC-30.3.10:
    - 支持最多50个事件批量提交
    - 返回 processed, failed 计数
    - 错误详情包含失败的事件索引和错误信息

    [Source: docs/stories/30.3.memory-api-health-endpoints.story.md#AC-30.3.10]
    """
    try:
        # Convert Pydantic models to dicts for service
        events_data = [
            {
                "event_type": event.event_type,
                "timestamp": event.timestamp,
                "canvas_path": event.canvas_path,
                "node_id": event.node_id,
                "metadata": event.metadata.model_dump() if event.metadata else {},
            }
            for event in request.events
        ]

        result = await memory_service.record_batch_learning_events(events_data)

        return BatchEpisodesResponse(
            success=result["success"],
            processed=result["processed"],
            failed=result["failed"],
            errors=[BatchErrorItem(**err) for err in result["errors"]],
            timestamp=result["timestamp"],
        )

    except Exception as e:
        logger.error(f"Failed to process batch episodes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process batch episodes: {str(e)}",
        )


# =============================================================================
# POST /extract-conversation - Sidecar fallback learning extraction
# =============================================================================

import os
from typing import Optional

from fastapi import Header
from pydantic import BaseModel, Field


def _require_observer_token(
    request: Request,
    x_canvas_observer_token: [REDACTED:env-cred][str] = Header(default=None),
) -> None:
    """
    audit-2026-04-07/p0-2 + ChatGPT-DR-2026-05-13 P0-1 (Wave-6 hardening):
    Gate /extract-conversation behind a shared token. **Default fail-closed**.

    Threat model rationale (ChatGPT Deep Research 2026-05-13):
        Previous default-open behavior allowed any reachable client to POST
        misconceptions into Graphiti when SIDECAR_OBSERVER_TOKEN was unset.
        This is a memory poisoning attack vector — attackers could weaponize
        the personal memory pipeline by injecting bogus misconceptions, which
        would later drive AI exam questions based on attacker-controlled
        misunderstandings ("the personal memory weaponization scenario").

    Auth decision matrix:
        - SIDECAR_OBSERVER_TOKEN set + header matches              → allow
        - SIDECAR_OBSERVER_TOKEN set + header mismatch             → 401
        - SIDECAR_OBSERVER_TOKEN unset + ALLOW_LOCAL_OBSERVER_BYPASS=true
          AND client.host ∈ {127.0.0.1, ::1}                       → allow + warning log
        - SIDECAR_OBSERVER_TOKEN unset + (not loopback OR bypass disabled) → 503

    Local dev bypass requires BOTH (a) explicit env opt-in AND (b) loopback
    client.host check — neither alone is sufficient. Pairs with sidecar
    header set in frontend/sidecar/sidecar.js (CANVAS_OBSERVER_TOKEN).
    """
    expected = (os.environ.get("SIDECAR_OBSERVER_TOKEN") or "").strip()
    provided = (x_canvas_observer_token or "").strip()

    if expected:
        # Production path — token configured, must match
        if provided != expected:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing X-Canvas-Observer-Token",
            )
        return

    # Token unset — fail-closed unless explicit local bypass
    bypass_env = (os.environ.get("ALLOW_LOCAL_OBSERVER_BYPASS") or "").lower() == "true"
    client_host = request.client.host if request.client else None
    is_loopback = client_host in {"127.0.0.1", "::1"}

    if bypass_env and is_loopback:
        logger.warning(
            "observer_token_bypass_local: client=%s reason=ALLOW_LOCAL_OBSERVER_BYPASS=true "
            "on loopback. Configure SIDECAR_OBSERVER_TOKEN for production.",
            client_host,
        )
        return

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=(
            "Observer auth not configured. Set SIDECAR_OBSERVER_TOKEN env "
            "for production, or ALLOW_LOCAL_OBSERVER_BYPASS=true for loopback dev."
        ),
    )


class ExtractConversationRequest(BaseModel):
    """Request for sidecar fallback conversation extraction."""

    node_id: str = Field(..., description="Canvas node identifier")
    session_id: str = Field("", description="Dialogue session identifier")
    messages: List[dict] = Field(
        ..., description="List of {role, content} message dicts"
    )
    # audit-2026-04-07/p0-2: callers may now scope the extraction to a real
    # canvas/subject instead of falling back to the global DEFAULT_GROUP_ID.
    group_id: Optional[str] = Field(
        default=None,
        description="Explicit Graphiti group_id. Overrides canvas_path inference.",
    )
    canvas_path: Optional[str] = Field(
        default=None,
        description=(
            "Canvas file path (e.g. '数学/微积分.canvas'). Used to derive "
            "group_id via subject_config helpers when group_id is not set."
        ),
    )


class ExtractConversationResponse(BaseModel):
    """Response from fallback extraction."""

    extracted: bool = False
    extracted_count: int = 0
    status: str = "ok"
    message: str = ""
    group_id: Optional[str] = None


@memory_router.post(
    "/extract-conversation",
    response_model=ExtractConversationResponse,
    summary="Extract learning events from conversation (sidecar fallback)",
    description=(
        "Called by sidecar when a conversation turn completes without "
        "record_learning_memory being invoked. Uses ConversationDistiller "
        "(Ollama Tier1) to extract structured learning data and write to Graphiti."
    ),
    dependencies=[Depends(_require_observer_token)],
)
async def extract_conversation_learning(
    request: ExtractConversationRequest,
    memory_service: MemoryServiceDep,
) -> ExtractConversationResponse:
    try:
        from app.services.conversation_distiller import ConversationDistiller
        from app.core.subject_config import (
            build_group_id,
            default_vault_group_id,
            extract_canvas_name,
            extract_subject_from_canvas_path,
        )

        # audit-2026-04-07/p0-2 → 批次1'① (MEM-FLYWHEEL): resolve target group_id.
        # Priority:
        #   1. explicit request.group_id (caller knows best)
        #   2. derived from canvas_path (subject + canvas filename)
        #   3. 当前 vault 组推导 (不再落 DEFAULT_GROUP_ID 污染桶 — 蒸馏产物
        #      是写侧, 落错桶即永久污染)
        if request.group_id:
            resolved_group_id = request.group_id
        elif request.canvas_path:
            subject = extract_subject_from_canvas_path(request.canvas_path)
            canvas_name = extract_canvas_name(request.canvas_path)
            resolved_group_id = build_group_id(subject, canvas_name)
        else:
            resolved_group_id = default_vault_group_id()

        distiller = ConversationDistiller()
        result = await distiller.distill(
            messages=request.messages,
            node_id=request.node_id,
        )

        extracted_count = 0

        for tip in result.tips:
            await memory_service.record_knowledge_entity(
                event_type="learning_tip",
                content=f"[Tip] {tip.title}: {tip.content}",
                metadata={
                    "node_id": request.node_id,
                    "source": "sidecar_fallback",
                    "tags": tip.tags,
                },
                group_id=resolved_group_id,
            )
            extracted_count += 1

        for error in result.errors:
            await memory_service.record_knowledge_entity(
                event_type="misconception",
                content=f"[Error] {error.description}",
                metadata={
                    "node_id": request.node_id,
                    "source": "sidecar_fallback",
                    "error_type": error.error_type,
                },
                group_id=resolved_group_id,
            )
            extracted_count += 1

        logger.info(
            f"[Observer-Fallback] Extracted {extracted_count} items "
            f"for node {request.node_id} into group {resolved_group_id}"
        )

        return ExtractConversationResponse(
            extracted=extracted_count > 0,
            extracted_count=extracted_count,
            status="ok",
            message=f"Extracted {extracted_count} learning items",
            group_id=resolved_group_id,
        )

    except Exception as e:
        logger.error(f"[Observer-Fallback] extract-conversation error: {e}")
        return ExtractConversationResponse(
            extracted=False,
            status="error",
            message=str(e)[:200],
        )


# =============================================================================
# POST /archive/session — M3 SessionEnd 归档管道 (2026-07-13, 路线图 v2)
#
# Claude Code SessionEnd hook (vault .claude/hooks/session-end-archive.py)
# 解析 transcript 后调用本端点。双通道落库:
#   1. 蒸馏 (distill_and_persist): tips/errors/qa → 结构化主链 (主图)
#   2. 对话全文 episode → worker LLM 抽取 → __semantic 影子图 (M2 隔离)
# 鉴权同 /episodes (X-CLS-Internal-Key, hook 读 .obsidian/cls-internal-key.txt)。
# =============================================================================


class SessionArchiveRequest(BaseModel):
    """Request from the SessionEnd hook."""

    session_id: str = Field(..., description="Claude Code session identifier")
    vault_id: str = Field(..., description="Vault folder name (backend sanitizes)")
    messages: List[dict] = Field(
        ..., description="List of {role, content} dicts parsed from transcript"
    )
    canvas_path: Optional[str] = Field(
        default=None, description="Optional canvas path for group derivation"
    )
    subject_id: Optional[str] = Field(default=None)
    group_id: Optional[str] = Field(
        default=None, description="Explicit group_id override (D16 format)"
    )


class SessionArchiveResponse(BaseModel):
    """Response for the SessionEnd archive pipeline."""

    archived: bool = False
    distilled_tips: int = 0
    distilled_errors: int = 0
    episode_enqueued: bool = False
    group_id: Optional[str] = None
    status: str = "ok"
    message: str = ""


@memory_router.post(
    "/archive/session",
    response_model=SessionArchiveResponse,
    summary="SessionEnd 会话归档（蒸馏 → 主链结构化 + 全文 → 语义影子图）",
    dependencies=[Depends(require_internal_api_key)],
)
async def archive_session(
    request: SessionArchiveRequest,
    memory_service: MemoryServiceDep,
) -> SessionArchiveResponse:
    # hook 侧已做 <4 条过滤, 服务端复核 (直连调用方不一定守约)
    if len(request.messages) < 4:
        return SessionArchiveResponse(
            archived=False,
            status="skipped_trivial",
            message=f"only {len(request.messages)} messages, below archive threshold",
        )

    try:
        resolved_group_id = request.group_id or _resolve_vault_group_id(
            request.vault_id,
            subject_id=request.subject_id,
            canvas_path=request.canvas_path,
        )

        from app.services.conversation_distiller import get_conversation_distiller

        distiller = get_conversation_distiller()
        node_id = f"session:{request.session_id[:16]}"

        # 通道 1: 蒸馏 → 结构化主链 (summary/tips/errors/qa 经
        # record_knowledge_entity / error_classifier 走 structured writer)
        result = await distiller.distill_and_persist(
            messages=request.messages,
            node_id=node_id,
            group_id=resolved_group_id,
        )

        # 通道 2: 对话全文 → 语义影子图 (worker 单点重定向 __semantic)。
        # 截断对齐 distiller (尾部 8000 字符, 近因优先)。
        conversation_text = "\n\n".join(
            f"{'Student' if m.get('role') == 'user' else 'Tutor'}: {m.get('content', '')}"
            for m in request.messages
        )
        if len(conversation_text) > 8000:
            conversation_text = (
                "...(earlier messages truncated)...\n\n" + conversation_text[-8000:]
            )
        enqueued = memory_service.enqueue_conversation_archive(
            session_id=request.session_id,
            conversation_text=conversation_text,
            group_id=resolved_group_id,
        )

        logger.info(
            "[M3] Session archived: session=%s group=%s tips=%d errors=%d "
            "episode_enqueued=%s",
            request.session_id[:16],
            resolved_group_id,
            len(result.tips),
            len(result.errors),
            enqueued,
        )
        # 批次3' 2-4 (MEM-FLYWHEEL): 会话归档落事件日志 — 图可重建的兜底
        from app.services.learning_event_log import append_event

        append_event(
            "session_archived",
            event_id=f"archive:{request.session_id}",
            node_id=node_id,
            payload={
                "tips": len(result.tips),
                "errors": len(result.errors),
                "group_id": resolved_group_id,
            },
        )
        return SessionArchiveResponse(
            archived=True,
            distilled_tips=len(result.tips),
            distilled_errors=len(result.errors),
            episode_enqueued=enqueued,
            group_id=resolved_group_id,
            status="ok",
            message=result.summary[:200] if result.summary else "",
        )

    except Exception as e:
        logger.error(f"[M3] archive-session error: {e}")
        return SessionArchiveResponse(
            archived=False,
            status="error",
            message=str(e)[:200],
        )
````

## File: backend/app/graphiti/group_id_compat.py
````python
"""
Graphiti group_id compatibility shim.

Background:
    Canvas D16 group_id 规约 (Story 2.5.Y AC #2, locked 2026-05-05) uses
    colon-separated format: `vault:<vault_id>` / `vault:<vault_id>:<subject>`.

    Graphiti's upstream validation rejects any group_id containing characters
    outside `[A-Za-z0-9_-]`, which means **all Canvas group_ids fail Graphiti
    add_episode / search calls** with `GroupIdValidationError`.

    This compatibility shim sanitizes Canvas group_ids at the Graphiti API
    boundary (and only at the boundary). All Canvas business logic (Cypher
    queries, subject_config, memory_service writers/readers) continues to use
    the Canvas D16 format internally.

    Boundary locations (must call sanitize before passing to graphiti_core):
    - `episode_worker._process_task` → graphiti.add_episode(group_id=...)
    - `memory_service._search_graphiti` → graphiti.search_(group_ids=[...])
    - `memory_service._search_graphiti_legacy` → graphiti.search(group_ids=[...])

    Reverse direction: not currently needed — Canvas readers query
    Neo4j's EpisodicNode.source_description / node_id, not its group_id
    field (which is owned by Graphiti and stored in sanitized form).

Source:
    P0-5 (2026-05-14) — discovered after P0 三件套 + P0-4 schema fixes
    finally let GraphitiEpisodeWorker run to add_episode and hit the
    upstream group_id validator.
"""

import re

_GRAPHITI_SEPARATOR = "__"

#: M1-E2E 修复 (2026-07-13): graphiti_core validator 只收 [A-Za-z0-9_-],
#: 而 S27 决策"group_id 按白板名"使 canvas 段天然含中文 (特征值与特征向量)。
#: 结构化主链直写 Cypher 绕过 validator 从未暴露; 语义通道 add_episode
#: 一触即拒 (3 重试全挂)。修复采用 IDNA 同款方案 (RFC 3492): 非法段
#: punycode 编码 + xn-- 前缀 — 确定性、可逆、输出字母表恒合规。
#: 前提: 段由上游 sanitizer (NFKC + Unicode \w 折叠) 产出, 只含词字符;
#: 已编码段 (xn--*) 本身合规, sanitize 幂等。
_VALID_SEGMENT_RE = re.compile(r"^[A-Za-z0-9_-]*$")
_PUNY_PREFIX = "xn--"


def _encode_segment(segment: str) -> str:
    """非法段 → xn--<punycode>; 合规段 (含已编码段) 原样返回。"""
    if _VALID_SEGMENT_RE.match(segment):
        return segment
    return _PUNY_PREFIX + segment.encode("punycode").decode("ascii")


def _decode_segment(segment: str) -> str:
    """xn-- 段 → 原文; 解码失败 (罕见: 真名恰为 xn--*) 原样返回。"""
    if not segment.startswith(_PUNY_PREFIX):
        return segment
    try:
        return segment[len(_PUNY_PREFIX) :].encode("ascii").decode("punycode")
    except (UnicodeError, ValueError):
        return segment


def sanitize_group_id_for_graphiti(canvas_group_id: str) -> str:
    """Convert Canvas D16 group_id to Graphiti-safe form.

    Examples:
        vault:cs_61b              → vault__cs_61b
        vault:cs_61b:algorithms   → vault__cs_61b__algorithms
        vault:cv:特征值与特征向量  → vault__cv__xn--<punycode> (可逆)
        vault:default             → vault__default
        cs188 (legacy, no colon)  → cs188 (unchanged)

    幂等: 已物理化/已编码输入再过一遍输出不变 (分隔符自适应 : 或 __)。

    Args:
        canvas_group_id: Canvas-side group_id in D16 format.

    Returns:
        Graphiti-safe equivalent (only [A-Za-z0-9_-] characters).
    """
    if not canvas_group_id:
        return canvas_group_id
    sep = ":" if ":" in canvas_group_id else _GRAPHITI_SEPARATOR
    return _GRAPHITI_SEPARATOR.join(
        _encode_segment(seg) for seg in canvas_group_id.split(sep)
    )


def desanitize_group_id_from_graphiti(graphiti_group_id: str) -> str:
    """Convert Graphiti-stored group_id back to Canvas D16 format.

    Inverse of `sanitize_group_id_for_graphiti` (含 xn-- 段 punycode 解码,
    中文白板名往返无损)。Useful when surfacing Graphiti's group_id back
    to Canvas-side code that expects D16 colons.

    Caveat: this splits on "__", which is unambiguous only if no Canvas
    group_id segment legitimately contains "__". D16 segments are
    vault_id / subject_id which use single underscores (cs_61b, not
    cs__61b), so this is safe under the current spec.
    """
    if not graphiti_group_id:
        return graphiti_group_id
    return ":".join(
        _decode_segment(seg) for seg in graphiti_group_id.split(_GRAPHITI_SEPARATOR)
    )


#: M2 双图隔离 (2026-07-13, 路线图 v2 / R3-Q1 对抗审查): 语义影子图后缀。
#: LLM 抽取产物绝不与结构化主图共享 group — graphiti 的 dedupe/invalidation
#: 以 group_id 为搜索边界, 隔离后跨路径污染在机制上不可能 (LLM 抽取实体
#: 不会被 resolve 到主图 uuid5 节点上, 也不会 invalidate 主图边)。
_SEMANTIC_SUFFIX = "semantic"


def semantic_group_id(group_id: str) -> str:
    """主图 group_id → 语义影子图 sibling group_id (逻辑 D16 形态)。

    任何经 LLM 抽取的内容 (add_episode 语义通道) 必须写入本函数返回的
    影子分组; 分组由服务端代码固定, 不暴露给任何调用方 (含 MCP 工具与
    hook 端点) — 即使提示词被污染也没有通路碰到主图。

    Examples:
        vault:canvas_vault   → vault:canvas_vault:semantic
        vault__canvas_vault  → vault__canvas_vault__semantic (物理形态输入)
        cs188 (legacy 裸值)  → cs188__semantic (无冒号即视为物理形态,
                               冒号后缀会被 graphiti validator 拒绝)
        已带 :semantic 后缀  → 原样返回 (幂等)
    """
    if not group_id:
        return group_id
    if group_id.endswith(f":{_SEMANTIC_SUFFIX}") or group_id.endswith(
        f"{_GRAPHITI_SEPARATOR}{_SEMANTIC_SUFFIX}"
    ):
        return group_id
    sep = ":" if ":" in group_id else _GRAPHITI_SEPARATOR
    return f"{group_id}{sep}{_SEMANTIC_SUFFIX}"


def to_physical_group_id(group_id: str) -> str:
    """任意来源 group_id → Neo4j 物理存储格式 (T1 统一, 2026-07-10 交接任务书).

    这是**唯一物理边界入口**: 一切直接读写 Neo4j group_id 属性的 Cypher
    (MERGE/SET/WHERE), 参数绑定前必须过本函数。物理规范 = 双下划线形态
    (`vault__cs_61b`), 因为 graphiti_core 上游 validator 拒绝冒号, 全图
    只能向 `__` 统一; D16 冒号格式仍是业务层/API 的逻辑规约不变。

    组合链: canonical_group_id (逻辑归一, deprecated 值映射 + WARNING)
    → sanitize_group_id_for_graphiti (冒号 → __)。

    幂等防御: canonical_group_id 会把已物理化的 `vault__x` 误判为未规范
    输入回旋成 `vault:vault__x` (再 sanitize = `vault__vault__x` 数据损坏),
    故检测到 `vault__` 前缀直接原样返回, 双重调用安全。

    Examples:
        vault:cs_61b        → vault__cs_61b
        vault__cs_61b       → vault__cs_61b   (幂等)
        cs188 (deprecated)  → vault__default  (canonical WARNING)
        CS 61B              → vault__cs_61b
    """
    if not group_id:
        return group_id
    if group_id.startswith(f"vault{_GRAPHITI_SEPARATOR}"):
        # M1-E2E (2026-07-13): 早退也过 sanitize — ASCII 输入幂等不变,
        # 中文物理历史形态 (vault__x__中文, 结构化直写产物) 收敛到 punycode。
        return sanitize_group_id_for_graphiti(group_id)
    # MEDIUM-1 防御 (T1 对抗审查 2026-07-10): canonical_group_id 对 vault:
    # 前缀输入直通、不做段级 sanitize — 若段内含 __ (如 .env 手写
    # vault:my__vault), sanitize 后 desanitize 会层级错乱 (vault:my:vault)。
    # 标准管线 (sanitize_vault_id / sanitize_subject_name 均折叠 _+) 不会
    # 产出这种值, 检测到即告警提示修配置。
    if group_id.startswith("vault:") and _GRAPHITI_SEPARATOR in group_id:
        import logging

        logging.getLogger(__name__).warning(
            "group_id %r contains '__' inside a vault: segment — "
            "desanitize roundtrip will be lossy; fix the source config "
            "(expected single underscores, e.g. from sanitize_vault_id)",
            group_id,
        )
    # Lazy import: core 层不反向依赖 graphiti 层, 无循环, 但保持与
    # config.py 相同的延迟加载姿势避免 Settings 初始化顺序问题。
    from app.core.subject_config import canonical_group_id

    return sanitize_group_id_for_graphiti(canonical_group_id(group_id))
````

## File: backend/app/mcp/tools/memory_tools.py
````python
# Canvas Learning System - MCP Memory Tools
# Story 3.2: MCP Tool Exposure (AC-2)
#
# Tools: search_memories, record_calibration, record_learning_memory
# These tools provide Agent access to the Graphiti learning memory system.
#
# [Source: _bmad-output/implementation-artifacts/3-2-mcp-tool-exposure-backend-api.md#Task 2.4]

import asyncio
import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.audit.guardian import get_audit_guardian

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Pydantic Models
# ═══════════════════════════════════════════════════════════════════════════════


class SearchMemoriesInput(BaseModel):
    """Input schema for search_memories tool."""

    query: str = Field(..., description="Natural language search query.")
    node_id: Optional[str] = Field(
        None, description="Filter by canvas node ID (optional)."
    )
    group_id: Optional[str] = Field(
        None, description="Graphiti group_id for memory isolation (optional)."
    )
    max_results: int = Field(
        10, ge=1, le=50, description="Maximum number of results to return."
    )


class MemoryItem(BaseModel):
    """A single memory search result."""

    fact: str = Field(..., description="The memory fact content")
    source: Optional[str] = Field(None, description="Source of the memory")
    timestamp: Optional[str] = Field(None, description="When the memory was created")
    relevance_score: Optional[float] = Field(None, description="Search relevance score")


class SearchMemoriesOutput(BaseModel):
    """Output schema for search_memories tool."""

    query: str
    results: List[MemoryItem] = Field(default_factory=list)
    total_count: int = 0
    status: str = "ok"
    message: str = ""


class RecordCalibrationInput(BaseModel):
    """Input schema for record_calibration tool."""

    node_id: str = Field(..., description="The canvas node identifier.")
    session_id: str = Field(..., description="The dialogue session identifier.")
    predicted_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="The predicted/expected score before answering.",
    )
    actual_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="The actual score after answering.",
    )
    question_type: Optional[str] = Field(
        None, description="Type of question that was asked."
    )
    difficulty: Optional[str] = Field(
        None, description="Difficulty level of the question."
    )


class RecordCalibrationOutput(BaseModel):
    """Output schema for record_calibration tool."""

    node_id: str
    recorded: bool
    calibration_gap: float = Field(
        ..., description="Absolute gap between predicted and actual score"
    )
    status: str = "ok"
    message: str = ""


class RecordLearningMemoryInput(BaseModel):
    """Input schema for record_learning_memory tool.

    Agent calls this when it detects a student learning event during dialogue.
    """

    node_id: str = Field(
        ..., description="Canvas node ID where the learning event occurred."
    )
    entity_type: str = Field(
        ...,
        description=(
            "Type of learning event: "
            "Misconception (知识点误解), "
            "ProblemTrap (做题思维陷阱), "
            "LogicalFallacy (逻辑推理谬误), "
            "GuidedThinking (引导思考记录)."
        ),
    )
    concept: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Specific concept name (e.g. 'A* admissibility').",
    )
    topic: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Broader topic (e.g. 'Search', 'MDPs').",
    )
    details: str = Field(
        ..., description="What the student got wrong and what is correct. Be specific."
    )
    severity: Optional[str] = Field(
        None,
        description="'critical' | 'moderate' | 'minor'. Judge by depth of misunderstanding.",
    )
    source_session_id: Optional[str] = Field(
        None, description="Session ID where this learning event was detected."
    )
    source_canvas_id: Optional[str] = Field(
        None, description="Canvas/board ID where the event occurred."
    )
    group_id: Optional[str] = Field(
        None,
        description=(
            "Graphiti group_id for memory isolation (D16 format, e.g. "
            "'vault:canvas_vault'). Falls back to the global default when omitted."
        ),
    )


class RecordLearningMemoryOutput(BaseModel):
    """Output schema for record_learning_memory tool."""

    node_id: str
    recorded: bool
    entity_type: str = ""
    status: str = "ok"
    message: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# Tool Implementation Functions
# ═══════════════════════════════════════════════════════════════════════════════


async def search_memories(
    query: str,
    node_id: Optional[str] = None,
    group_id: Optional[str] = None,
    max_results: int = 10,
) -> Dict[str, Any]:
    """
    Search the Graphiti learning memory knowledge graph.

    Returns relevant learning memories (facts, events, associations)
    matching the natural language query.

    This tool does not require a pipeline token.

    Args:
        query: Natural language search query.
        node_id: Optional filter by canvas node ID.
        group_id: Optional Graphiti group_id for memory isolation.
        max_results: Maximum number of results to return.

    Returns:
        Dict with search results.
    """
    guardian = get_audit_guardian()
    asyncio.create_task(guardian.record_tool_call("search_memories", "", node_id or ""))

    try:
        from app.services.memory_service import get_memory_service

        memory_svc = await get_memory_service()

        # P15 (轨道 B 2026-07-20): 缺省推导当前 vault 组 (vault:canvas_vault),
        # 不再回落 DEFAULT_GROUP_ID 空桶 — 归档写侧与读侧同组, 召回不踩空
        if group_id is None:
            from app.core.subject_config import default_vault_group_id

            group_id = default_vault_group_id()

        # Search memories via the memory service
        # 批次1'⑤ (MEM-FLYWHEEL): cross_encoder 接线 — 18012 bge-reranker
        # 此前在主记忆检索被调用 0 次 (恒走默认 RRF, 审查「已付钱零收益」
        # 之一)。worker 的 Graphiti 实例已配本地 CrossEncoderClient, 指定
        # recipe 即上岗 (社区标尺: hybrid 之上接精排可再消 1/3 残余失败)。
        search_result = await memory_svc.search_memories(
            query=query,
            group_id=group_id,
            max_results=max_results,
            search_config="combined_cross_encoder",
        )

        # Convert results to MemoryItem format
        items: List[MemoryItem] = []
        raw_results = search_result if isinstance(search_result, list) else []

        for item in raw_results[:max_results]:
            if isinstance(item, dict):
                items.append(
                    MemoryItem(
                        fact=item.get("fact", item.get("content", str(item))),
                        source=item.get("source"),
                        timestamp=item.get("timestamp", item.get("created_at")),
                        relevance_score=item.get("score", item.get("relevance_score")),
                    )
                )
            else:
                # Handle Graphiti entity objects
                items.append(
                    MemoryItem(
                        fact=getattr(item, "fact", str(item)),
                        source=getattr(item, "source", None),
                        timestamp=str(getattr(item, "created_at", "")),
                        relevance_score=getattr(item, "score", None),
                    )
                )

        return SearchMemoriesOutput(
            query=query,
            results=items,
            total_count=len(items),
            status="ok",
        ).model_dump()

    except ImportError as e:
        logger.warning(f"[Story 3.2] search_memories: service not available: {e}")
        return SearchMemoriesOutput(
            query=query,
            status="service_unavailable",
            message=str(e),
        ).model_dump()
    except Exception as e:
        logger.error(f"[Story 3.2] search_memories error: {e}")
        return SearchMemoriesOutput(
            query=query,
            status="error",
            message=str(e),
        ).model_dump()


async def record_calibration(
    node_id: str,
    session_id: str,
    predicted_score: float,
    actual_score: float,
    question_type: Optional[str] = None,
    difficulty: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Record a calibration data point for metacognitive tracking.

    Captures the gap between a student's predicted performance and actual
    performance, which is used to track self-assessment accuracy over time.

    This tool does not require a pipeline token.

    Args:
        node_id: The canvas node identifier.
        session_id: The dialogue session identifier.
        predicted_score: The predicted/expected score before answering.
        actual_score: The actual score after answering.
        question_type: Type of question (optional).
        difficulty: Difficulty level (optional).

    Returns:
        Dict with recording status and calibration gap.
    """
    guardian = get_audit_guardian()
    asyncio.create_task(
        guardian.record_tool_call("record_calibration", session_id, node_id)
    )

    calibration_gap = abs(predicted_score - actual_score)

    try:
        from app.services.memory_service import get_memory_service

        memory_svc = await get_memory_service()

        # Record calibration as a learning event
        calibration_data = {
            "event_type": "calibration",
            "node_id": node_id,
            "session_id": session_id,
            "predicted_score": predicted_score,
            "actual_score": actual_score,
            "calibration_gap": calibration_gap,
        }
        if question_type:
            calibration_data["question_type"] = question_type
        if difficulty:
            calibration_data["difficulty"] = difficulty

        await memory_svc.record_knowledge_entity(
            event_type="calibration",
            content=f"Calibration: predicted={predicted_score:.2f} actual={actual_score:.2f} gap={calibration_gap:.2f}",
            metadata=calibration_data,
            # P15: 校准记录落当前 vault 组
            group_id=default_vault_group_id(),
        )

        return RecordCalibrationOutput(
            node_id=node_id,
            recorded=True,
            calibration_gap=calibration_gap,
            status="ok",
            message=f"Calibration recorded: gap={calibration_gap:.2f}",
        ).model_dump()

    except ImportError as e:
        logger.warning(f"[Story 3.2] record_calibration: service not available: {e}")
        return RecordCalibrationOutput(
            node_id=node_id,
            recorded=False,
            calibration_gap=calibration_gap,
            status="service_unavailable",
            message=str(e),
        ).model_dump()
    except Exception as e:
        logger.error(f"[Story 3.2] record_calibration error: {e}")
        return RecordCalibrationOutput(
            node_id=node_id,
            recorded=False,
            calibration_gap=calibration_gap,
            status="error",
            message=str(e),
        ).model_dump()


async def record_learning_memory(
    node_id: str,
    entity_type: str,
    concept: str,
    topic: str,
    details: str,
    severity: Optional[str] = None,
    source_session_id: Optional[str] = None,
    source_canvas_id: Optional[str] = None,
    group_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Record a learning event (misconception, problem trap, logical fallacy,
    or guided thinking) to the Graphiti knowledge graph.

    Call this tool when you detect that the student has:
    - A misconception: states something factually wrong about a concept
    - A problem-solving trap: applies wrong procedure or falls for a common trap
    - A logical fallacy: reasoning contains an invalid step
    - A guided thinking event: completed a teaching exchange worth recording

    When NOT to call:
    - Simple typos or language errors (not conceptual)
    - Student merely asks a question (asking != misunderstanding)
    - You are unsure — ask a follow-up first
    - Same misconception already recorded this session

    Rate limit: maximum 2 calls per conversation turn.

    Args:
        node_id: Canvas node identifier.
        entity_type: Misconception | ProblemTrap | LogicalFallacy | GuidedThinking
        concept: Specific concept name (e.g. 'A* admissibility').
        topic: Broader topic (e.g. 'Search', 'MDPs').
        details: What the student got wrong and what is correct.
        severity: Optional 'critical' | 'moderate' | 'minor'.

    Returns:
        Dict with recording status.
    """
    guardian = get_audit_guardian()
    asyncio.create_task(
        guardian.record_tool_call("record_learning_memory", "", node_id)
    )

    valid_types = {"Misconception", "ProblemTrap", "LogicalFallacy", "GuidedThinking"}
    if entity_type not in valid_types:
        return RecordLearningMemoryOutput(
            node_id=node_id,
            recorded=False,
            entity_type=entity_type,
            status="validation_error",
            message=f"Invalid entity_type: {entity_type}. Must be one of {valid_types}",
        ).model_dump()

    try:
        from app.core.memory_format import build_entity_name, build_episode_body
        from app.services.memory_service import get_memory_service

        memory_svc = await get_memory_service()

        # M3 (2026-07-13) + P15 (2026-07-20): 调用方可传 D16 group_id,
        # 缺省推导当前 vault 组 (不再落 vault:default 空桶)。
        resolved_group_id = group_id or default_vault_group_id()

        name = build_entity_name(entity_type, concept)
        body = build_episode_body(entity_type, topic=topic, error=details, correct="")
        content = f"{body}"
        if severity:
            content += f" | Severity: {severity}"

        await memory_svc.record_knowledge_entity(
            event_type=entity_type.lower(),
            content=content,
            metadata={
                "entity_type": entity_type,
                "concept": concept,
                "topic": topic,
                "details": details,
                "severity": severity,
                "node_id": node_id,
                "source": "observer_agent",
                "name": name,
                "source_session_id": source_session_id,
                "source_canvas_id": source_canvas_id,
            },
            group_id=resolved_group_id,
        )

        logger.info(
            f"[LearningMemory] Recorded {entity_type}: {concept} node={node_id}"
        )

        return RecordLearningMemoryOutput(
            node_id=node_id,
            recorded=True,
            entity_type=entity_type,
            status="ok",
            message=f"Recorded {entity_type}: {concept}",
        ).model_dump()

    except ImportError as e:
        logger.warning(f"[LearningMemory] service not available: {e}")
        return RecordLearningMemoryOutput(
            node_id=node_id,
            recorded=False,
            entity_type=entity_type,
            status="service_unavailable",
            message=str(e),
        ).model_dump()
    except Exception as e:
        logger.error(f"[LearningMemory] error: {e}")
        return RecordLearningMemoryOutput(
            node_id=node_id,
            recorded=False,
            entity_type=entity_type,
            status="error",
            message=str(e),
        ).model_dump()
````

## File: backend/app/services/canvas_projection_sync.py
````python
"""Fix-E1 (2026-06-10): 节点增殖原因边同步 — markdown frontmatter → Neo4j CANVAS_EDGE。

GAP-E: 用户拉新节点标的"相关原因"写在新节点 md frontmatter `relationships[]`
(node-derivation.ts: {type, target: [[源笔记]], description?})。但降级到 markdown 后:
  - 旧 `sync_all_edges_to_neo4j` 读 .canvas JSON (vault 里已 0 个 .canvas)
  - 后端无任何代码读 frontmatter relationships → CANVAS_EDGE
→ CANVAS_EDGE = 0, question_generator._get_edge_reasons (读 CANVAS_EDGE.label) 永远空。

本服务扫 vault md frontmatter relationships[] → MERGE CANVAS_EDGE{label=原因}, 让检验白板
能在针对性考察时拿到"用户为什么把这两个概念连起来"的原因 (用户 Q2: 出题时给 LLM 当上下文)。

触发: main.py 启动时搭车 Story 2.1 wikilink eager-build 之后 (与之同源扫 vault markdown)。
对齐架构方向: backend 从 .canvas 迁到 markdown 图遍历 (project_context_enrichment_gap)。

读侧契约 (question_generator.py:966-984 _get_edge_reasons):
  MATCH (n:CanvasNode {id: $node_id})-[r:CANVAS_EDGE]->(m) WHERE r.label IS NOT NULL
  RETURN r.label
→ 边方向: 持有 frontmatter 的节点(派生节点) -[CANVAS_EDGE{label}]-> target(源节点)。
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Optional

import frontmatter

logger = logging.getLogger(__name__)

_WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


def _resolve_node_id(raw: Any) -> str:
    """'[[节点/base-case]]' / '[[源笔记|别名]]' / 'base-case' → 'base-case' (basename, 去别名)。"""
    text = str(raw or "")
    m = _WIKILINK_RE.search(text)
    inner = m.group(1) if m else text
    inner = inner.split("|", 1)[0]  # 去 [[target|alias]] 别名
    return inner.split("/")[-1].strip().removesuffix(".md")


class CanvasProjectionSync:
    """扫 vault md frontmatter relationships[] → Neo4j CANVAS_EDGE (原因边)。"""

    def __init__(self) -> None:
        self._neo4j = None

    def _client(self):
        if self._neo4j is None:
            from app.clients.neo4j_client import get_neo4j_client

            self._neo4j = get_neo4j_client()
        return self._neo4j

    async def sync(self, vault_path: str, group_id: str = "") -> dict[str, int]:
        """扫描 vault, 把节点 frontmatter relationships 同步成 CANVAS_EDGE。

        Args:
            vault_path: vault 根目录。
            group_id: 逻辑 D16 group_id (如 vault:canvas_vault), 由调用方
                (main.py 启动流程) 经 build_vault_group_id 构造。T2 (2026-07-10):
                MERGE 的 CanvasNode / CANVAS_EDGE 均落此 group (物理 __ 格式),
                多 vault 不串。空值时回退当前 vault 推导。

        Returns: {nodes_with_relationships, edges_synced, failed}。
        """
        base = Path(vault_path)
        if not base.exists():
            logger.warning("[Fix-E1] vault path 不存在, 跳过原因边同步: %s", vault_path)
            return {"nodes_with_relationships": 0, "edges_synced": 0, "failed": 0}

        # T2 (2026-07-10): group 缺省回退当前 vault (与 vault_backfill 同源)
        if not group_id:
            from app.config import get_current_vault_id
            from app.core.subject_config import build_vault_group_id

            group_id = build_vault_group_id(get_current_vault_id())
        from app.graphiti.group_id_compat import to_physical_group_id

        physical_gid = to_physical_group_id(group_id)

        client = self._client()
        nodes_with_rel = 0
        edges_synced = 0
        failed = 0
        alive_edge_ids: list[str] = []

        for md in base.rglob("*.md"):
            rels = self._read_relationships(md)
            if not rels:
                continue
            source_id = md.stem  # node_id = 文件 basename (扁平节点池约定)
            nodes_with_rel += 1
            for rel in rels:
                target_id = _resolve_node_id(rel.get("target"))
                rel_type = str(rel.get("type") or "related_to")
                description = str(rel.get("description") or "").strip()
                # 原因优先; 无原因时退到关系类型, 保证 label 非空 (否则 _get_edge_reasons 过滤掉)
                label = description or rel_type
                if not target_id or target_id == source_id:
                    continue
                try:
                    edge_id = await self._merge_edge(
                        client,
                        source_id,
                        target_id,
                        rel_type,
                        label,
                        physical_gid,
                        rel=rel,
                    )
                    alive_edge_ids.append(edge_id)
                    edges_synced += 1
                except Exception as e:  # noqa: BLE001 — 单边失败不阻断批量
                    failed += 1
                    logger.debug(
                        "[Fix-E1] edge sync failed %s->%s: %s", source_id, target_id, e
                    )

        # 批次4' 3-3 幽灵边对账 (MEM-FLYWHEEL): frontmatter 里已删/改名的
        # relationship, 旧 CANVAS_EDGE 此前永远留在图里 (MERGE 只增不删,
        # 拆分时间线越老越脏)。软失效不物理删 — 时间线可追溯, 查询侧过滤。
        invalidated = 0
        try:
            records = await client.run_query(
                """
                MATCH ()-[e:CANVAS_EDGE]-()
                WHERE e.group_id = $group_id AND e.synced_from = 'frontmatter'
                  AND NOT e.id IN $alive_ids AND e.invalidated_at IS NULL
                SET e.invalidated_at = datetime(), e.active = false
                RETURN count(DISTINCT e) AS c
                """,
                group_id=physical_gid,
                alive_ids=alive_edge_ids,
            )
            if records:
                data = records[0] if isinstance(records[0], dict) else records[0].data()
                invalidated = int(data.get("c") or 0)
        except Exception as e:  # noqa: BLE001 — 对账失败不阻断同步
            logger.warning("[3-3] 幽灵边对账失败 (本轮跳过): %s", e)

        logger.info(
            "[Fix-E1] 原因边同步: %d 节点有 relationships, %d 边写入, %d 失败, %d 幽灵边失效",
            nodes_with_rel,
            edges_synced,
            failed,
            invalidated,
        )
        return {
            "nodes_with_relationships": nodes_with_rel,
            "edges_synced": edges_synced,
            "failed": failed,
            "edges_invalidated": invalidated,
        }

    @staticmethod
    def _read_relationships(md_path: Path) -> Optional[list[dict[str, Any]]]:
        """读单个 md 的 frontmatter relationships[] (非 list 或解析失败 → None)。"""
        try:
            post = frontmatter.load(str(md_path))
        except Exception as e:  # noqa: BLE001 — 损坏 frontmatter 不阻断扫描
            logger.debug("[Fix-E1] frontmatter 解析失败 %s: %s", md_path.name, e)
            return None
        rels = post.metadata.get("relationships")
        if not isinstance(rels, list):
            return None
        return [r for r in rels if isinstance(r, dict)]

    async def _merge_edge(
        self,
        client: Any,
        source_id: str,
        target_id: str,
        rel_type: str,
        label: str,
        physical_gid: str,
        rel: Optional[dict[str, Any]] = None,
    ) -> str:
        """MERGE (source)-[CANVAS_EDGE{label=原因}]->(target) (确定性 edge id 幂等)。

        T2 (2026-07-10): 节点/边均 SET group_id (物理 __ 格式); edge_id 纳入
        group 前缀 — 跨 vault 同名节点对的边不再共享 id 互相覆盖 label。
        MERGE 键保持 {id} 不加 group, 对齐 SyncService / exam_service_ext 的
        CanvasNode 写契约 (键结构分叉会造重复节点)。

        批次4' (MEM-FLYWHEEL): 3-2 ON CREATE 打 created_at (首建时序, 幂等重跑
        不覆盖) + relationships[] 的 derived_at 透传; 3-1 派生时刻理解快照
        (source_mastery_at_derivation / confusion) 随边留档; 3-3 复活清除失效
        标记 (md 里边回来了 → 幽灵标记撤销)。边身份 = source→type→target
        (reason 变更走 SET label 属性更新, 不并排新增)。
        """
        rel = rel or {}
        edge_id = f"rel-{physical_gid}-{source_id}-{rel_type}-{target_id}"
        await client.run_query(
            """
            MERGE (s:CanvasNode {id: $source_id})
            SET s.group_id = coalesce(s.group_id, $group_id)
            MERGE (t:CanvasNode {id: $target_id})
            SET t.group_id = coalesce(t.group_id, $group_id)
            MERGE (s)-[e:CANVAS_EDGE {id: $edge_id}]->(t)
            ON CREATE SET e.created_at = datetime()
            SET e.label = $label,
                e.relation_type = $rel_type,
                e.group_id = $group_id,
                e.synced_from = 'frontmatter',
                e.active = true,
                e.derived_at = coalesce($derived_at, e.derived_at),
                e.source_mastery_at_derivation =
                    coalesce($source_mastery, e.source_mastery_at_derivation),
                e.confusion_at_derivation =
                    coalesce($confusion, e.confusion_at_derivation)
            REMOVE e.invalidated_at
            """,
            source_id=source_id,
            target_id=target_id,
            edge_id=edge_id,
            label=label,
            rel_type=rel_type,
            group_id=physical_gid,
            derived_at=str(rel.get("derived_at")) if rel.get("derived_at") else None,
            source_mastery=(
                float(rel["source_mastery_at_derivation"])
                if rel.get("source_mastery_at_derivation") is not None
                else None
            ),
            confusion=(
                str(rel.get("confusion"))[:300] if rel.get("confusion") else None
            ),
        )
        return edge_id


_canvas_projection_sync: Optional[CanvasProjectionSync] = None


def get_canvas_projection_sync() -> CanvasProjectionSync:
    """Singleton accessor。"""
    global _canvas_projection_sync
    if _canvas_projection_sync is None:
        _canvas_projection_sync = CanvasProjectionSync()
    return _canvas_projection_sync
````

## File: canvas-vault/.claude/hooks/session-end-archive.py
````python
#!/usr/bin/env python3
"""M3 SessionEnd 归档 hook (2026-07-13, 路线图 v2) — Claude Code 原生环境。

SessionEnd 触发 (原生 CLI 可靠; Claudian 会在 3s 后杀子进程, 故 D-1 切换
是本管道的前置条件)。流程: stdin 读 SessionEnd payload → 解析 transcript
jsonl → 提取 user/assistant 文本轮次 → POST /api/v1/memory/archive/session。

批次0 0-4 (MEM-FLYWHEEL-2026-07-22): 后端不可达时归档请求落本地待发队列
(pending_archives.jsonl, session_id 幂等), 下次 hook 运行时自动补发 —
停机窗口结束的学习会话不再永久丢失。全程 best-effort: 任何失败静默
退出 0, 绝不阻塞 session 关闭。
"""

import json
import os
import pathlib
import sys
import time
import urllib.request

BACKEND_URL = "http://localhost:8011/api/v1/memory/archive/session"
MIN_MESSAGES = 4  # 少于 4 条 = trivial session, 不归档
MIN_USER_MESSAGES = 2  # 归档计数修正 (轨道 B 2026-07-20, UAT D2 ⑥):
# assistant 在工具调用间产生多个 text 片段、各算一条 — 带工具的单轮问答
# 也能凑满 4 条总数 ("1 轮不归档"假设不成立, 召回测试 session 被误归档)。
# 加真实用户轮下限: user 角色 < 2 条不归档。
MAX_MESSAGES = 40  # 只送尾部 40 轮 (近因优先, 与后端 8000 字符截断对齐)
PER_MESSAGE_CHARS = 4000
TIMEOUT_S = 8

# ── 0-4 本地待发队列 ──
QUEUE_FILE = pathlib.Path(__file__).resolve().parent / "pending_archives.jsonl"
DEAD_FILE = pathlib.Path(__file__).resolve().parent / "pending_archives.dead.jsonl"
MAX_DRAIN_PER_RUN = 5  # 单次 hook 最多补发条数, 控制关停耗时
MAX_ATTEMPTS = 30  # 补发上限, 超过转 dead 文件留证


def parse_transcript(path: pathlib.Path) -> list:
    messages = []
    for line in path.read_text(errors="replace").splitlines():
        try:
            entry = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        if entry.get("isMeta"):
            continue
        etype = entry.get("type")
        if etype not in ("user", "assistant"):
            continue
        msg = entry.get("message") or {}
        content = msg.get("content")
        if isinstance(content, str):
            text = content
        elif isinstance(content, list):
            # 只取 text block — tool_use/tool_result 不进归档
            text = "\n".join(
                b.get("text", "")
                for b in content
                if isinstance(b, dict) and b.get("type") == "text"
            )
        else:
            continue
        text = text.strip()
        # 过滤 hook/命令注入轮次 (<system-reminder>/<command-name> 等包裹)
        if not text or text.startswith("<"):
            continue
        messages.append(
            {"role": msg.get("role") or etype, "content": text[:PER_MESSAGE_CHARS]}
        )
    return messages


def _post(record: dict, internal_key: [REDACTED:env-cred] -> bool:
    """POST 归档 payload。成功 True; 任何网络/HTTP 失败 False。"""
    request = urllib.request.Request(
        BACKEND_URL,
        data=json.dumps(record).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-CLS-Internal-Key": internal_key,
        },
        method="POST",
    )
    try:
        urllib.request.urlopen(request, timeout=TIMEOUT_S)
        return True
    except Exception:
        return False


def _load_queue() -> list:
    if not QUEUE_FILE.is_file():
        return []
    entries = []
    for line in QUEUE_FILE.read_text(errors="replace").splitlines():
        try:
            entries.append(json.loads(line))
        except (json.JSONDecodeError, ValueError):
            continue
    return entries


def _save_queue(entries: list) -> None:
    if not entries:
        QUEUE_FILE.unlink(missing_ok=True)
        return
    QUEUE_FILE.write_text(
        "".join(json.dumps(e, ensure_ascii=False) + "\n" for e in entries)
    )


def _enqueue(record: dict) -> None:
    """幂等入队: 同 session_id 已在队则跳过。"""
    entries = _load_queue()
    sid = record.get("session_id")
    if any(e.get("record", {}).get("session_id") == sid for e in entries):
        return
    entries.append({"queued_at": time.time(), "attempts": 0, "record": record})
    _save_queue(entries)


def _drain(internal_key: [REDACTED:env-cred] -> None:
    """补发积压归档: 成功移除, 失败保留 (attempts+1), 超上限转 dead。"""
    entries = _load_queue()
    if not entries:
        return
    remaining, drained = [], 0
    for entry in entries:
        if drained >= MAX_DRAIN_PER_RUN:
            remaining.append(entry)
            continue
        drained += 1
        if _post(entry.get("record", {}), internal_key):
            continue  # 成功: 不保留
        entry["attempts"] = int(entry.get("attempts", 0)) + 1
        if entry["attempts"] >= MAX_ATTEMPTS:
            with DEAD_FILE.open("a") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        else:
            remaining.append(entry)
    _save_queue(remaining)


def main() -> None:
    payload = json.load(sys.stdin)
    transcript_path = payload.get("transcript_path") or ""
    session_id = payload.get("session_id") or "unknown"
    vault_root = pathlib.Path(
        os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or "."
    )

    key_file = vault_root / ".obsidian" / "cls-internal-key.txt"
    internal_key = [REDACTED:env-cred] if key_file.is_file() else ""

    # 先补发历史积压 (即使本次 session 不够归档门槛也要补)
    try:
        _drain(internal_key)
    except Exception:
        pass

    transcript = pathlib.Path(transcript_path).expanduser()
    if not transcript.is_file():
        return
    messages = parse_transcript(transcript)
    user_turns = sum(1 for m in messages if m.get("role") == "user")
    if len(messages) < MIN_MESSAGES or user_turns < MIN_USER_MESSAGES:
        return
    messages = messages[-MAX_MESSAGES:]

    record = {
        "session_id": session_id,
        "vault_id": vault_root.name,
        "messages": messages,
    }
    if not _post(record, internal_key):
        # 0-4: 后端不可达 → 落本地队列, 下次 hook 运行补发
        _enqueue(record)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # best-effort: 归档失败绝不阻塞 session 关闭
    sys.exit(0)
````

## File: backend/app/api/v1/endpoints/tips.py
````python
# Canvas Learning System - Tips API Endpoint
# Story 3.6: Tips Writing to Graphiti (AC-2)
#
# POST /api/v1/tips - Save a user-annotated tip to Graphiti
#
# The tip contains selected text from dialogue, a user-provided title,
# and classification tags. It is written to Graphiti via the
# Agent self-report channel for future context injection (Story 3.4).
#
# [Source: _bmad-output/implementation-artifacts/3-6-tips-annotation-error-archiving.md#Task 2.4]

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

tips_router = APIRouter()


def _resolve_tips_group_id(vault_id: str | None = None) -> str:
    """B2 修复 (2026-07-12 对抗审查): tips 写读统一落当前 vault 桶。

    旧契约 5 处全用 DEFAULT_GROUP_ID (vault:default) —— 实时批注落错桶,
    要等下次重启 vault_backfill 重放 frontmatter 才进正确 vault 桶,
    多 vault 并存时必串库。显式 vault_id (插件传) 优先; 缺省回退当前
    激活 vault (与 vault_backfill / canvas_projection_sync 同源)。
    写读两侧 (save/search/find_episode) 全部走本函数保持成对。
    """
    from app.config import get_current_vault_id, sanitize_vault_id
    from app.core.subject_config import build_vault_group_id

    if vault_id and vault_id.strip():
        return build_vault_group_id(sanitize_vault_id(vault_id))
    return build_vault_group_id(get_current_vault_id())


# ═══════════════════════════════════════════════════════════════════════════════
# Request / Response Models
# ═══════════════════════════════════════════════════════════════════════════════


class SaveTipRequest(BaseModel):
    """Request body for saving a tip annotation."""

    vault_id: str = Field(
        default="",
        description=(
            "B2 (2026-07-12): vault 身份。插件端 inferVaultId(app.vault.getName()) 传; "
            "空 = 回退后端当前激活 vault。tips 写读统一落 vault 桶, 不再用 vault:default。"
        ),
    )

    content: str = Field(..., min_length=1, description="The selected text content")
    title: str = Field(..., min_length=1, description="User-provided title for the tip")
    tags: List[str] = Field(
        default_factory=list,
        description="Classification tags: important, confused, inspiration, review",
    )
    node_id: str = Field(..., description="Source canvas node ID")
    annotation_id: str = Field(
        default="",
        description=(
            "P0 (A+-prime): 稳定批注身份 cb-xxx (前端 wrapSelection 生成)。"
            "后端 write_callout 用它做 identity, 空则回退首行。"
        ),
    )
    source_timestamp: str = Field(
        ..., description="ISO timestamp of the source dialogue message"
    )
    event_type: str = Field(
        default="learning_tip",
        description=(
            "Entity type for memory_format canonical schema. "
            "Use 'learning_tip' for sidebar dialogue tips (Story 3.6) or "
            "'callout_annotation' for whiteboard Cmd+Shift+A callout (Story 1.16, P0-1)."
        ),
    )


class SaveTipResponse(BaseModel):
    """Response after saving a tip."""

    tip_id: str
    saved: bool
    status: str = "ok"
    message: str = ""


class SaveRelationRequest(BaseModel):
    """P4 (A+-prime): 派生关系原因实时上报 (Cmd+Shift+D 拉新节点)。

    走 Graphiti-native write_relation_reason (经 record_knowledge_entity), 不走
    sync.py 的 CANVAS_EDGE 投影。让'写下为什么拉出 → 立即读回'不必等重启回填。
    """

    vault_id: str = Field(
        default="",
        description=(
            "B2 (2026-07-12): vault 身份。插件端 inferVaultId(app.vault.getName()) 传; "
            "空 = 回退后端当前激活 vault。tips 写读统一落 vault 桶, 不再用 vault:default。"
        ),
    )

    source_node_id: str = Field(
        ..., description="持有 relationship 的派生节点 basename"
    )
    target_node_id: str = Field(..., description="源节点 basename")
    relation_type: str = Field(
        default="related_to", description="prerequisite/refines/extends/..."
    )
    reason: str = Field(default="", description="用户写的'为什么拉出/连接'")
    source_timestamp: str = Field(default="", description="ISO 用户操作时刻")


class SaveRelationResponse(BaseModel):
    saved: bool
    status: str = "written"
    message: str = ""


# ─── Story 2.4 Plan B Phase 2 (2026-05-14): Batch sync schema ───
# 用户在 callout 内继续输入"我的理解"后，plugin debounce 500ms 触发 batch sync。
# Backend 用 content_hash 做幂等去重 — 同 hash 跳过，不同 hash 创建 v2 EpisodicNode。


class CalloutBatchItem(BaseModel):
    """Single callout entry in batch sync."""

    tag: str = Field(..., description="tips | error | question | keypoint")
    tag_label: str = Field(default="", description="Display label e.g. '💡 Tips'")
    understanding: str = Field(
        default="",
        description="understood | fuzzy | not-understood | '' (无 checkbox)",
    )
    content: str = Field(..., min_length=1, description="Callout body content")
    content_hash: str = Field(
        ..., min_length=64, max_length=64, description="SHA256 hex"
    )
    annotation_id: str = Field(
        default="",
        description="P0 (A+-prime): 稳定批注身份 cb-xxx, 空=历史批注(回退首行)",
    )


class BatchSyncRequest(BaseModel):
    """Plugin debounce 触发的整文件 callout batch 同步。"""

    vault_id: str = Field(
        default="",
        description=(
            "B2 (2026-07-12): vault 身份。插件端 inferVaultId(app.vault.getName()) 传; "
            "空 = 回退后端当前激活 vault。tips 写读统一落 vault 桶, 不再用 vault:default。"
        ),
    )

    node_id: str = Field(..., description="Source canvas node basename (no ext)")
    callouts: List[CalloutBatchItem] = Field(
        ..., description="All callouts parsed from the file"
    )
    source_timestamp: str = Field(..., description="ISO timestamp")


class BatchSyncResponse(BaseModel):
    """Aggregate result of batch sync."""

    total_received: int
    new_synced: int  # 新创建 episode 数
    skipped_duplicate: int  # content_hash 已存在跳过
    failed: int
    status: str = "ok"


# ═══════════════════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════════════════


class TipItem(BaseModel):
    """A single tip in the GET response."""

    tip_id: str
    content: str
    title: str
    tags: List[str] = Field(default_factory=list)
    node_id: str
    created_at: str = ""


class GetTipsResponse(BaseModel):
    """Response from GET /tips endpoint."""

    tips: List[TipItem]
    total: int


@tips_router.get(
    "",
    response_model=GetTipsResponse,
    summary="Get tips for a node from Graphiti",
    description="Retrieve all tip annotations for a given canvas node.",
)
async def get_tips(
    node_id: str,
    vault_id: str = "",
) -> Dict[str, Any]:
    """
    Retrieve tips for a canvas node from Graphiti memory.

    Story 3.6: GET endpoint for frontend to read saved tips.

    Args:
        node_id: The canvas node ID to fetch tips for.

    Returns:
        GetTipsResponse with list of tips and total count.
    """
    try:
        from app.services.memory_service import get_memory_service

        memory_svc = await get_memory_service()

        # Search for tips related to this node
        # B2 (2026-07-12): 读侧与写侧成对 — 同走 _resolve_tips_group_id
        results = await memory_svc.search_memories(
            query=f"learning_tip node_id:{node_id}",
            group_id=_resolve_tips_group_id(vault_id),
            limit=50,
        )

        tips: List[Dict[str, Any]] = []
        seen_tip_ids: set = set()
        for item in results:
            metadata = item.get("metadata", {})
            tip_id = metadata.get("tip_id")
            if metadata.get("node_id") == node_id and tip_id:
                # Deduplicate by tip_id to avoid repeated content
                if tip_id in seen_tip_ids:
                    continue
                seen_tip_ids.add(tip_id)
                tips.append(
                    TipItem(
                        tip_id=tip_id,
                        content=metadata.get("content", ""),
                        title=metadata.get("title", "Untitled"),
                        tags=metadata.get("tags", []),
                        node_id=node_id,
                        created_at=metadata.get("created_at", ""),
                    ).model_dump()
                )

        return GetTipsResponse(
            tips=tips,
            total=len(tips),
        ).model_dump()

    except Exception as e:
        logger.warning(f"[Story 3.6] Failed to get tips for node {node_id}: {e}")
        return GetTipsResponse(tips=[], total=0).model_dump()


@tips_router.post(
    "",
    response_model=SaveTipResponse,
    summary="Save a tip annotation to Graphiti",
    description="Save a user-annotated tip (selected dialogue text) to the "
    "Graphiti learning memory. The tip becomes available for future "
    "context injection (Story 3.4).",
)
async def save_tip(request: SaveTipRequest) -> Dict[str, Any]:
    """
    Save a tip annotation to Graphiti.

    Story 3.6 AC-2: User clicks "Write Tips" -> tip saved to Graphiti.
    The tip data includes: content (selected text), title (user input),
    tags, source node ID, and source dialogue timestamp.

    Args:
        request: The tip data to save.

    Returns:
        SaveTipResponse with tip_id and status.
    """
    tip_id = str(uuid.uuid4())

    try:
        from app.services.memory_service import get_memory_service

        memory_svc = await get_memory_service()

        # Build tip content for Graphiti
        tags_str = ", ".join(request.tags) if request.tags else "none"

        # P0-1 (2026-05-13): event_type 由 client 决定 — callout 走 callout_annotation,
        # 侧栏 tip 走 learning_tip。两者都通过 memory_format.py canonical schema 映射。
        # Whitelist 防止任意 event_type 注入（只允许已知的 2 种）。
        allowed_event_types = {"learning_tip", "callout_annotation"}
        effective_event_type = (
            request.event_type
            if request.event_type in allowed_event_types
            else "learning_tip"
        )

        result = await memory_svc.record_knowledge_entity(
            event_type=effective_event_type,
            content=(
                f"Tip: {request.title} | Content: {request.content} | Tags: {tags_str}"
            ),
            metadata={
                "tip_id": tip_id,
                "title": request.title,
                "content": request.content,
                "tags": request.tags,
                "node_id": request.node_id,
                "annotation_id": request.annotation_id,
                "source_timestamp": request.source_timestamp,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            group_id=_resolve_tips_group_id(request.vault_id),
        )

        # A7 (P2): 诚实反映持久化结果 — 不再无条件 saved=True。
        write_status = (
            result.get("status", "written") if isinstance(result, dict) else "written"
        )
        degraded = write_status == "degraded"
        logger.info(
            f"[Story 3.6] Tip saved: id={tip_id} node={request.node_id} "
            f"title={request.title[:50]} status={write_status}"
        )

        return SaveTipResponse(
            tip_id=tip_id,
            saved=not degraded,
            status=write_status,
            message=(
                "记忆服务未就绪，批注已暂存，将在服务就绪后自动入图"
                if degraded
                else "Tips saved successfully"
            ),
        ).model_dump()

    except Exception as e:
        logger.error(f"[Story 3.6] Failed to save tip: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save tip: {str(e)}",
        ) from e


@tips_router.post(
    "/relation",
    response_model=SaveRelationResponse,
    summary="Save a derivation relation reason to Graphiti (P4)",
    description="派生节点时实时上报'为什么拉出'的关系原因 → Graphiti-native "
    "write_relation_reason。修 X1: 不必等启动回填即可读回。",
)
async def save_relation(request: SaveRelationRequest) -> Dict[str, Any]:
    """P4 (A+-prime): 派生关系原因实时入图。"""
    from app.services.memory_service import get_memory_service

    try:
        memory_svc = await get_memory_service()
        result = await memory_svc.record_knowledge_entity(
            event_type="node_derived",
            content=(
                request.reason
                or f"{request.source_node_id} -> {request.target_node_id}"
            ),
            metadata={
                "node_id": request.source_node_id,
                "target_node_id": request.target_node_id,
                "relation_type": request.relation_type,
                "reason": request.reason,
                "source_timestamp": request.source_timestamp,
            },
            group_id=_resolve_tips_group_id(request.vault_id),
        )
        write_status = (
            result.get("status", "written") if isinstance(result, dict) else "written"
        )
        degraded = write_status == "degraded"
        logger.info(
            f"[P4] Relation saved: {request.source_node_id} -> "
            f"{request.target_node_id} ({request.relation_type}) status={write_status}"
        )
        return SaveRelationResponse(
            saved=not degraded,
            status=write_status,
            message=(
                "记忆服务未就绪，关系已暂存，将在服务就绪后自动入图"
                if degraded
                else "Relation saved"
            ),
        ).model_dump()
    except Exception as e:
        logger.error(f"[P4] Failed to save relation: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to save relation: {str(e)}"
        ) from e


# ═══════════════════════════════════════════════════════════════════════════════
# Story 2.4 Plan B Phase 2 (2026-05-14): Batch sync endpoint
# ═══════════════════════════════════════════════════════════════════════════════

# P0-8 (2026-05-14): in-memory cache for hash dedup race condition.
# Graphiti add_episode 是异步（~20-30s LLM extraction），Neo4j 查询可能 lag。
# In-memory cache 同步检查，杜绝同一 batch 处理窗口内重复 enqueue。
# 简单 LRU：> 1000 条时保留最新 800 条。多进程部署会丢一致性，但开发期单进程 OK。
_BATCH_HASH_CACHE: set[str] = set()
_BATCH_HASH_CACHE_MAX = 1000
_BATCH_HASH_CACHE_KEEP = 800


def _hash_cache_check_or_add(hash_marker: str) -> bool:
    """Return True if hash already seen (skip), False if new (proceed + add)."""
    if hash_marker in _BATCH_HASH_CACHE:
        return True
    _BATCH_HASH_CACHE.add(hash_marker)
    if len(_BATCH_HASH_CACHE) > _BATCH_HASH_CACHE_MAX:
        # Simple eviction: keep most recently added (rough — set has no order
        # but for in-process dedup this is acceptable)
        keep = list(_BATCH_HASH_CACHE)[-_BATCH_HASH_CACHE_KEEP:]
        _BATCH_HASH_CACHE.clear()
        _BATCH_HASH_CACHE.update(keep)
    return False


@tips_router.post(
    "/batch",
    response_model=BatchSyncResponse,
    summary="批注 debounce 批量同步 (RE-ENABLED 2026-06-11)",
    description=(
        "曾于 2026-05-14 废弃 (plan-b postmortem) — 该决策前提是'后端管道 "
        "G-FAKE 断裂, 写了也进不了记忆'。2026-06-10 后端重构为 Graphiti-native "
        "(record_knowledge_entity 结构化路由 → :Entity/RELATES_TO, 图级确定性 "
        "uuid MERGE 真幂等), 前提失效, 复活。调用方: 插件 CalloutSyncDebouncer "
        "(3s debounce, 静默), 收录用户在 callout 内续写的'我的理解'全文。"
    ),
)
async def batch_sync_callouts(request: BatchSyncRequest) -> Dict[str, Any]:
    """Batch sync callouts using SHA256 content_hash for idempotency.

    Story 2.4 Plan B Phase 2 (2026-05-14), re-enabled 2026-06-11.
    """
    try:
        from app.services.memory_service import get_memory_service

        memory_svc = await get_memory_service()

        new_synced = 0
        skipped = 0
        failed = 0

        for callout in request.callouts:
            try:
                # 双层幂等：(1) in-memory cache 杜绝异步 race，(2) Neo4j 持久去重
                hash_marker_for_cache = f"{request.node_id}|{callout.content_hash}"
                if _hash_cache_check_or_add(hash_marker_for_cache):
                    skipped += 1
                    continue
                already_exists = await memory_svc.find_episode_by_content_hash(
                    node_id=request.node_id,
                    content_hash=callout.content_hash,
                    group_id=_resolve_tips_group_id(request.vault_id),
                )
                if already_exists:
                    skipped += 1
                    continue

                # 创建新 episode（Graphiti 自动生成 valid_at 作时序版本标记）
                # P0-7 (2026-05-14): content_hash 必须内嵌到 content 字段才能持久化
                # 查询 — Graphiti 不存 metadata 到 EpisodicNode。`[hash:xxx]` 后缀
                # 让 find_episode_by_content_hash 能用 CONTAINS 匹配。
                tip_id = str(uuid.uuid4())
                tags_repr = (
                    f"tag:{callout.tag},understanding:{callout.understanding or 'none'}"
                )
                hash_marker = f"[hash:{callout.content_hash[:16]}]"
                batch_result = await memory_svc.record_knowledge_entity(
                    event_type="callout_annotation",
                    content=(
                        f"Callout [{callout.tag_label}]: {callout.content} | "
                        f"Tags: {tags_repr} | {hash_marker}"
                    ),
                    metadata={
                        "tip_id": tip_id,
                        "title": f"{callout.tag_label} · {request.node_id}",
                        "content": callout.content,
                        "tag": callout.tag,
                        "understanding": callout.understanding,
                        "node_id": request.node_id,
                        "annotation_id": callout.annotation_id,
                        "content_hash": callout.content_hash,
                        "source_timestamp": request.source_timestamp,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "batch_sync": True,
                    },
                    group_id=_resolve_tips_group_id(request.vault_id),
                )
                # A7 (P2): degraded 未入图, 不计入 synced
                if (
                    isinstance(batch_result, dict)
                    and batch_result.get("status") == "degraded"
                ):
                    failed += 1
                else:
                    new_synced += 1
            except Exception as inner_e:
                logger.warning(
                    f"[Story 2.4 batch] Failed one callout (hash={callout.content_hash[:8]}): {inner_e}"
                )
                failed += 1

        logger.info(
            f"[Story 2.4 batch] node={request.node_id} "
            f"received={len(request.callouts)} new={new_synced} "
            f"skipped={skipped} failed={failed}"
        )

        return BatchSyncResponse(
            total_received=len(request.callouts),
            new_synced=new_synced,
            skipped_duplicate=skipped,
            failed=failed,
            status="ok",
        ).model_dump()

    except Exception as e:
        logger.error(f"[Story 2.4 batch] Batch sync failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Batch sync failed: {str(e)}",
        ) from e
````

## File: backend/app/services/graphiti_structured_writer.py
````python
"""D2 结构化 Graphiti 写入适配器: 用户显式标注确定性写 :Entity/RELATES_TO (零 LLM)。

Phase 1 (GRAPHITI-NATIVE-MEMORY-2026-06-10)。

为什么不走 add_triplet: 实读 graphiti.py:1450-1568 (0.28.2) — add_triplet 跑
3×embedding + 2×hybrid search + resolve_extracted_edge(llm_client), 对"每打一条
批注/每拉一个节点"的高频显式事件成本/延迟不可接受, 且显式事件不需要 LLM 猜矛盾。
为什么不是裸 Cypher: 写的是 Graphiti canonical :Entity-[RELATES_TO]->:Entity
(经 EntityEdge.save, edges.py:330-367 官方持久化路径), 不伪造 :EpisodicNode/
:CanvasNode 冒充 Graphiti (G-FAKE 教训)。

建模约定 (读侧 graphiti_memory_reader 按 attributes 过滤):
- callout/error/conversation → 自环边 (src==tgt), attributes.source 区分
- relation 原因 → 真实 src→tgt 边, fact=用户写的"为什么"
- 全部带 attributes.node_id (持有方) + valid_at; D8 显式 embedding
- belief 版本链: D10 统一入口在此, 内部委托 graphiti_belief_service
  (不重写其旧边 supersede / as_of 版本语义)

[Source: _bmad-output/研究/2026-06-10-graphiti-native-记忆重构-落地计划.md §Phase 1]
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime
from typing import Any, Optional
from uuid import NAMESPACE_DNS, uuid5

from graphiti_core.edges import EntityEdge
from graphiti_core.errors import EdgeNotFoundError

from app.graphiti.group_id_compat import sanitize_group_id_for_graphiti
from app.graphiti.identity_registry import IdentityRegistry

logger = logging.getLogger(__name__)


async def _preserved_times(
    driver: Any, edge_uuid: str, occurred_at: datetime
) -> tuple[datetime, datetime]:
    """create-or-preserve (P3/A4 2026-06-26): 边已存在则保留其 (created_at, valid_at),
    否则用 occurred_at。

    根治时序污染: EntityEdge.save 用 `SET e=$edge_data` 全量覆写。启动回填用回填
    时刻 save 同 uuid 边时, 若不保留, 会把实时写入的真实事件时间冲成回填时刻
    (实测: 图里所有边 created_at 全=容器启动时刻)。保留原始时间后, 回填只补缺边、
    不篡改已有边的时间线。新边 (EdgeNotFoundError) 用 occurred_at (= 调用方传的
    真实源事件时间)。
    """
    try:
        existing = await EntityEdge.get_by_uuid(driver, edge_uuid)
        return (existing.created_at or occurred_at, existing.valid_at or occurred_at)
    except EdgeNotFoundError:
        return occurred_at, occurred_at
    except Exception as e:  # noqa: BLE001 — 查询失败退新建语义, 不阻断写入
        logger.debug("[A4] preserve-times 查询失败, 用 occurred_at: %s", e)
        return occurred_at, occurred_at


def _deterministic_edge_uuid(kind: str, node_key: [REDACTED:env-cred] gid: str, fact: str) -> str:
    """同 (类型, 节点, group, 内容) → 同 uuid → save 的 MERGE 语义幂等。

    重跑回填 / 重存同文件不重复建边; 内容变了 = 新边 (累积模型)。
    """
    fact_hash = hashlib.sha256(fact.encode("utf-8")).hexdigest()[:16]
    return str(uuid5(NAMESPACE_DNS, f"{kind}:{node_key}:{gid}:{fact_hash}"))


def canonical_callout_fact(
    callout_type: str, understanding: Optional[str], body: str
) -> str:
    """三通道统一的批注存储格式 (去重修复 2026-06-13)。

    此前即时上报/停笔同步/启动回填各自包装 ("Tip:…|Content:…" /
    "Callout […]: … | [hash:…]" / "💡 Tips - [x] …") → 同一批注三个指纹
    三条边。writer 持有唯一格式, 调用方一律传裸文本。
    """
    head = f"[{callout_type}·{understanding}]" if understanding else f"[{callout_type}]"
    return f"{head} {body}"


def _identity_first_line(text: str) -> str:
    """批注的逻辑身份 = 首个非空行 (= 用户选中的文本, 三通道天然一致)。

    同一批注的不同版本 (即时上报的'仅选中' → 停笔同步的'含我的理解全文')
    → 同身份 → 同 uuid → MERGE 原地升级为最新最全, 不并排存多条。
    新批注 (不同选中文本) → 新身份 → 累积模型不受影响。
    """
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return text


async def _save_edge_with_embedding(
    edge: EntityEdge, driver: Any, embedder: Optional[Any]
) -> EntityEdge:
    """D8: save() 纯持久化不自动 embed, 必须在此显式生成 fact_embedding。"""
    if embedder is not None:
        await edge.generate_embedding(embedder)
    await edge.save(driver)
    return edge


async def _self_loop_edge(
    driver: Any,
    embedder: Optional[Any],
    *,
    node_id: str,
    group_id: str,
    name: str,
    fact: str,
    occurred_at: datetime,
    attributes: dict[str, Any],
    identity_text: Optional[str] = None,
) -> EntityEdge:
    """callout/error/conversation 的自环建模: 节点对自身的陈述。

    identity_text 给定时, uuid 按逻辑身份 (节点+批注首行) 而非全文指纹 —
    同一批注的版本演进 (选中→续写全文) MERGE 原地升级, 不并排存多条。
    """
    gid = sanitize_group_id_for_graphiti(group_id)  # C-3 边界 sanitize
    node_uuid = await IdentityRegistry.ensure_entity_node(
        driver, node_id, gid, embedder=embedder
    )
    edge_uuid = _deterministic_edge_uuid(name, node_id, gid, identity_text or fact)
    # P3 (A4): 边已存在则保留原始时间, 防回填覆写真实事件时间
    created_at, valid_at = await _preserved_times(driver, edge_uuid, occurred_at)
    edge = EntityEdge(
        uuid=edge_uuid,
        group_id=gid,
        source_node_uuid=node_uuid,
        target_node_uuid=node_uuid,
        created_at=created_at,
        valid_at=valid_at,
        invalid_at=None,
        name=name,
        fact=fact,
        attributes={**attributes, "node_id": node_id},
    )
    return await _save_edge_with_embedding(edge, driver, embedder)


async def write_callout(
    driver: Any,
    embedder: Optional[Any],
    *,
    node_id: str,
    group_id: str,
    callout_type: str,
    text: str,
    occurred_at: datetime,
    understanding: Optional[str] = None,
    annotation_id: Optional[str] = None,
) -> EntityEdge:
    """用户批注 → 自环 SelfAnnotation 边。

    text 必须是裸批注正文 (选中文本 + 续写, 无通道包装) — 存储格式由
    canonical_callout_fact 统一。

    P0 (A+-prime 2026-06-26): 身份优先用稳定 annotation_id (cb-xxx, 前端
    wrapSelection 生成嵌入 callout 标题)。改批注正文不再换身份(防孤儿)，
    同节点同一句原文的两条不同批注不再因首行相同碰撞合并。无 id 的历史批注
    回退首行身份 (向后兼容)。
    """
    return await _self_loop_edge(
        driver,
        embedder,
        node_id=node_id,
        group_id=group_id,
        name="SelfAnnotation",
        fact=canonical_callout_fact(callout_type, understanding, text),
        occurred_at=occurred_at,
        attributes={
            "source": "callout",
            "event_type": "callout_added",
            "callout_type": callout_type,
            "understanding": understanding,
            "annotation_id": annotation_id or None,
        },
        identity_text=annotation_id or _identity_first_line(text),
    )


async def write_error(
    driver: Any,
    embedder: Optional[Any],
    *,
    node_id: str,
    group_id: str,
    error_type: str,
    description: str,
    occurred_at: datetime,
) -> EntityEdge:
    """错误标记 → 自环 SelfMisconception 边 (fact=错误描述)。"""
    return await _self_loop_edge(
        driver,
        embedder,
        node_id=node_id,
        group_id=group_id,
        name="SelfMisconception",
        fact=description,
        occurred_at=occurred_at,
        attributes={
            "source": "error",
            "event_type": "error_marked",
            "error_type": error_type,
        },
    )


async def write_conversation_summary(
    driver: Any,
    embedder: Optional[Any],
    *,
    node_id: str,
    group_id: str,
    summary: str,
    occurred_at: datetime,
) -> EntityEdge:
    """对话归档摘要 → 自环 ConversationSummary 边 (fact=AI 生成的对话摘要)。

    用户拍板 (2026-06-10): 归档时写摘要边供检验白板精确读;
    对话全文仍走 add_episode 非结构化通道做语义抽取。
    """
    return await _self_loop_edge(
        driver,
        embedder,
        node_id=node_id,
        group_id=group_id,
        name="ConversationSummary",
        fact=summary,
        occurred_at=occurred_at,
        attributes={
            "source": "conversation",
            "event_type": "conversation_archived",
        },
    )


async def write_relation_reason(
    driver: Any,
    embedder: Optional[Any],
    *,
    source_node_id: str,
    target_node_id: str,
    group_id: str,
    relation_type: Optional[str],
    reason: str,
    occurred_at: datetime,
) -> EntityEdge:
    """节点增殖原因 → 真实 src→tgt 边 (fact=用户写的"为什么拉出/连接")。"""
    gid = sanitize_group_id_for_graphiti(group_id)
    su = await IdentityRegistry.ensure_entity_node(
        driver, source_node_id, gid, embedder=embedder
    )
    tu = await IdentityRegistry.ensure_entity_node(
        driver, target_node_id, gid, embedder=embedder
    )
    edge_uuid = _deterministic_edge_uuid(
        relation_type or "RelatedTo",
        f"{source_node_id}->{target_node_id}",
        gid,
        reason,
    )  # 幂等
    # P3 (A4): 边已存在则保留原始时间, 防回填覆写真实事件时间
    created_at, valid_at = await _preserved_times(driver, edge_uuid, occurred_at)
    edge = EntityEdge(
        uuid=edge_uuid,
        group_id=gid,
        source_node_uuid=su,
        target_node_uuid=tu,
        created_at=created_at,
        valid_at=valid_at,
        invalid_at=None,
        name=relation_type or "RelatedTo",
        fact=reason,
        attributes={
            "node_id": source_node_id,  # 读侧按持有方 node 精确查
            "source": "relation",
            "event_type": "wikilink_added",
            "relation_type": relation_type,
        },
    )
    return await _save_edge_with_embedding(edge, driver, embedder)


async def write_belief_version(graphiti: Any, **kwargs: Any) -> Any:
    """D10: belief 版本链统一入口 — 内部委托 graphiti_belief_service。

    版本语义 (旧 active 边 supersede + 新 active 边 + as_of 回溯) 留在
    belief 服务, 不在此抽薄 (ChatGPT 计划审查)。
    """
    from app.services.graphiti_belief_service import update_belief_version_chain

    return await update_belief_version_chain(graphiti, **kwargs)


async def invalidate_missing_callouts(
    driver: Any,
    embedder: Optional[Any],
    *,
    node_id: str,
    group_id: str,
    keep_annotation_ids: set[str],
    occurred_at: datetime,
) -> int:
    """P5 (A2 删除失效 2026-06-26): 删除对账 — 节点当前已无的批注边置 invalid_at。

    frontmatter/markdown 当前 callout 集合 keep_annotation_ids 之外的 active callout
    自环边 → invalid_at + status=deleted (用户删了该 callout)。仅作用于带
    annotation_id 的 P0+ 边; 无 id 的历史边不动 (无法可靠对账)。

    注: P1 已让 ACP 当前态读 frontmatter, 删除立即不参与出题。此对账是图整洁/时光机
    一致的最终一致性补充 (回填时跑), 非阻断出题的实时硬需求。
    复用 belief 的 invalidate+embedding 模式 (读回边 fact_embedding 默认空, save 前补)。
    返回失效条数。
    """
    from app.services.graphiti_memory_reader import _node_uuid_and_active_edges

    _uuid, edges = await _node_uuid_and_active_edges(driver, node_id, group_id)
    invalidated = 0
    for edge in edges:
        attrs = edge.attributes or {}
        if attrs.get("source") != "callout":
            continue
        aid = attrs.get("annotation_id")
        if not aid or aid in keep_annotation_ids:
            continue
        # 用户已删此批注 → tombstone
        edge.invalid_at = occurred_at
        edge.attributes = {**attrs, "status": "deleted"}
        if edge.fact_embedding is None:
            try:
                await edge.load_fact_embedding(driver)
            except Exception:  # noqa: BLE001 — 读回无 embedding 退生成
                pass
        if edge.fact_embedding is None and embedder is not None:
            await edge.generate_embedding(embedder)
        await edge.save(driver)
        invalidated += 1
    return invalidated
````

## File: backend/app/services/targeting_material_service.py
````python
"""T4 方案 A (2026-07-10, 用户拍板) — 针对性考察素材服务。

给定节点, 沿增殖投影图 (CanvasNode-[CANVAS_EDGE{label=原因}]-CanvasNode,
T2 起带 group_id) 找 1-hop 邻居, 读每个邻居的**当前态错误**作为跨节点
出题素材: "你之前在 A 犯过 X 错, 现在考你 B 里同源的概念"。

素材来源 (P1 A+-prime 裁决: 当前态读 frontmatter, Graphiti 是历史流):
- 邻居发现: Neo4j 投影 (1 条 cypher, 双向 1-hop + 边 label 原因, group 过滤)
- 邻居错误: frontmatter `errors[]` (Story 2.5.X 用户 accept 确认的正式错误,
  优先) + `tips[] tag==error` (用户手标) — 两者都是学生自己的错误记录,
  不是定义正文, 信息隔离 (d=1.50) 不破。

降级契约: Neo4j 不可用 / 无邻居 / 邻居无错误 → materials=[] + degraded
标记, 调用方 (start-exam-board skill 经 API) 静默退回仅本节点素材。
"""

from __future__ import annotations

import logging
from typing import Any

import frontmatter

from app.graphiti.group_id_compat import to_physical_group_id
from app.services.frontmatter_signals import _node_md_path

logger = logging.getLogger(__name__)

#: 单邻居最多贡献的错误条数 (防单点噪音淹没 prompt)
_MAX_ERRORS_PER_NEIGHBOR = 3


def _read_neighbor_errors(node_id: str, group_id: str = "") -> list[str]:
    """读邻居节点当前态错误描述 (正式 errors[] 优先 + tips tag=error)。

    轨道 B P2 (2026-07-20): 两道新防线 —
    ① vault 归属校验: 邻居 md 的 errors[].group_id 与请求 group 不一致
       一律拒收 (UAT-2.5.X-test 的 CS188 素材曾混入线代 vault 出题链);
    ② 泄题防御 (P5/硬要求③): 优先读 misconception 字段 (误解半句),
       缺失才回退 description — 更正半句永不进出题素材。
    """
    # 纵深防御: neighbor_id 来自图内受控数据 (sync 写入 md.stem), 但
    # _node_md_path 本身无穿越防护 — 含路径分隔/父目录引用一律拒绝
    if "/" in node_id or "\\" in node_id or ".." in node_id:
        logger.warning("[T4] 拒绝可疑 neighbor_id: %r", node_id)
        return []
    path = _node_md_path(node_id)
    if path is None:
        return []
    try:
        post = frontmatter.load(str(path))
    except (OSError, ValueError, UnicodeDecodeError) as e:
        logger.debug("[T4] frontmatter 读取失败 %s: %s", node_id, e)
        return []
    fm = post.metadata or {}
    out: list[str] = []
    # 批次3' dispute 三件套第二件「出题排除」(MEM-FLYWHEEL): 用户 dispute 过的
    # 候选文本不得再进出题素材 — 不再拿你否认过的点考你。disputed 候选留在
    # error_candidates[] (终态, 状态机保证不入 errors[]), 此处按文本匹配拦截
    # errors[]/tips[] 中与 disputed 内容相同的素材 (早年直写/重复提名场景)。
    disputed_texts: set[str] = set()
    for cand in fm.get("error_candidates") or []:
        if isinstance(cand, dict) and cand.get("status") == "disputed":
            for key in ("misconception", "description"):
                t = str(cand.get(key) or "").strip()
                if t:
                    disputed_texts.add(t)
    # 正式 errors[] — 2.5.X accept/edited 移入, 用户主权确认过的错误
    for err in fm.get("errors") or []:
        if isinstance(err, dict):
            # 批次1'② (MEM-FLYWHEEL): fail-closed — 缺 group_id 一律拒收。
            # 「缺失放行」曾是 C1 泄漏通道 (UAT-2.5.X 测试种子 errors[] 无
            # group_id 混入线代出题链, 2026-07-22 对抗审查实锤); 缺失兼容
            # 只准存在于离线迁移工具, 不在线上主路径 (ChatGPT R1 三层防线)。
            err_group = str(err.get("group_id") or "").strip()
            if group_id and err_group != group_id:
                logger.info(
                    "[T4-P2] 拒收邻居素材 (fail-closed): node=%s err_group=%r req_group=%s",
                    node_id,
                    err_group,
                    group_id,
                )
                continue
            desc = str(err.get("misconception") or err.get("description") or "").strip()
            if desc and desc in disputed_texts:
                logger.info("[T4-dispute] 排除已 dispute 素材: node=%s", node_id)
                continue
            if desc:
                out.append(desc)
    # tips[] 中用户手标的 error
    for tip in fm.get("tips") or []:
        if isinstance(tip, dict) and tip.get("tag") == "error":
            text = str(tip.get("text") or "").strip()
            if text and text in disputed_texts:
                logger.info("[T4-dispute] 排除已 dispute tips 素材: node=%s", node_id)
                continue
            if text:
                out.append(text)
    return out[:_MAX_ERRORS_PER_NEIGHBOR]


async def collect_targeting_material(
    node_id: str,
    group_id: str,
    budget_chars: int = 1200,
) -> dict[str, Any]:
    """收集节点的跨节点针对性考察素材。

    Args:
        node_id: 被考察节点 id (文件 basename, 扁平节点池约定)。
        group_id: 逻辑 D16 group_id (vault:x) — 内部物理化后过滤投影图。
        budget_chars: 素材总字符预算 (超出截断, 邻居顺序 = 图返回顺序)。

    Returns:
        {materials: [{source_node, relation_reason, kind, text}],
         degraded: bool, degraded_reason: str | None}
    """
    result: dict[str, Any] = {
        "materials": [],
        "degraded": False,
        "degraded_reason": None,
    }
    try:
        from app.clients.neo4j_client import get_neo4j_client

        client = get_neo4j_client()
        # T1/T2: 投影图物理 __ 格式; 双向 1-hop, 边 label = 用户增殖原因
        # 批次1'② (MEM-FLYWHEEL): 三处收紧 —
        # ① n/e/m 三侧 group 谓词严格相等 (IS NULL 放行是 C1 同源洞, 移除);
        # ② OPTIONAL MATCH 区分 node_not_found / no_neighbors 两态;
        # ③ ORDER BY neighbor_id 确定性排序 (原纯存储顺序=随机;
        #    批次4' 投影边补 created_at 后改按时间)。
        # 批次4' 3-3: e.invalidated_at IS NULL 过滤幽灵边 (已删/改名的旧关系
        # 不再进出题素材); 3-2: ORDER BY 升级为派生时间倒序 (created_at 已补,
        # 最近拆分的关系优先), neighbor_id 兜底保确定性
        records = await client.run_query(
            """
            MATCH (n:CanvasNode {id: $node_id})
            WHERE n.group_id = $group_id
            OPTIONAL MATCH (n)-[e:CANVAS_EDGE]-(m:CanvasNode)
            WHERE e.group_id = $group_id AND m.id <> $node_id
              AND m.group_id = $group_id AND e.invalidated_at IS NULL
            RETURN DISTINCT m.id AS neighbor_id, e.label AS reason,
                   e.created_at AS edge_created_at
            ORDER BY edge_created_at DESC, neighbor_id
            LIMIT 10
            """,
            node_id=node_id,
            group_id=to_physical_group_id(group_id),
        )
    except Exception as e:  # noqa: BLE001 — 读侧降级, 不炸出题
        logger.debug("[T4] 邻居查询失败 (降级仅本节点): %s", e)
        result["degraded"] = True
        result["degraded_reason"] = f"neo4j_unavailable: {type(e).__name__}"
        return result

    if not records:
        result["degraded"] = True
        result["degraded_reason"] = "node_not_found"
        return result
    neighbor_rows = [
        data
        for rec in records
        if (data := rec if isinstance(rec, dict) else rec.data()).get("neighbor_id")
    ]
    if not neighbor_rows:
        result["degraded"] = True
        result["degraded_reason"] = "no_neighbors"
        return result

    used = 0
    for data in neighbor_rows:
        neighbor_id = str(data.get("neighbor_id") or "")
        reason = str(data.get("reason") or "").strip()
        for err_text in _read_neighbor_errors(neighbor_id, group_id=group_id):
            if used + len(err_text) > budget_chars:
                logger.debug("[T4] 素材达字符预算 %d, 截断", budget_chars)
                return result
            result["materials"].append(
                {
                    "source_node": neighbor_id,
                    "relation_reason": reason,
                    "kind": "error",
                    "text": err_text,
                }
            )
            used += len(err_text)
    if not result["materials"]:
        # 有邻居但全部无可用错误素材 — 与「无邻居」区分, 调用方可选不同兜底话术
        result["degraded"] = True
        result["degraded_reason"] = "no_neighbor_errors"
    return result
````

## File: backend/app/services/episode_worker.py
````python
"""
GraphitiEpisodeWorker - Async queue-based background worker for graphiti add_episode.

Production-ready implementation with:
- asyncio.Queue for sequential episode processing
- Exponential backoff retry with full jitter
- Dead-letter store for exhausted retries
- Graceful shutdown with drain timeout
- Observable metrics (queue depth, latency, failure rate)

References:
- graphiti-core docstring: "each episode is added sequentially and awaited"
- getzep/graphiti mcp_server/src/services/queue_service.py (official pattern)
- Python 3.13+ asyncio.Queue.shutdown() for graceful termination

Author: Canvas Learning System
"""

import asyncio
import hashlib
import json
import logging
import os
import re

import structlog
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from graphiti_core import Graphiti

logger = structlog.get_logger(__name__)


# ── Py<3.13 兼容层 (2026-07-22 批次0) ──────────────────────────────────────
# asyncio.QueueShutDown / Queue.shutdown() 是 Python 3.13+ API, 生产容器为
# python:3.11-slim — except 子句在异常匹配时才求值, 属性缺失会以
# AttributeError 掩盖原始异常并中断关停排空。导入期解析一次。
class _QueueShutDownFallback(Exception):
    """Py<3.13 占位 — 永不被抛出, 仅使 except 子句可安全求值。"""


_QUEUE_SHUTDOWN: type[BaseException] = getattr(
    asyncio, "QueueShutDown", _QueueShutDownFallback
)

#: Py<3.13 无 Queue.shutdown() 时用于优雅停机的队列哨兵。
_STOP_SENTINEL: Any = object()

try:
    from graphiti_core.errors import (
        EntityTypeValidationError,
        GroupIdValidationError,
    )

    #: 确定性校验错误 — 重试必然同样失败 (如 group_id 含非法字符),
    #: 直接死信留证, 不空转重试队列。
    _PERMANENT_EPISODE_ERRORS: tuple[type[Exception], ...] = (
        GroupIdValidationError,
        EntityTypeValidationError,
    )
except ImportError:  # pragma: no cover — graphiti_core 版本无此错误类
    _PERMANENT_EPISODE_ERRORS = ()


# ═══════════════════════════════════════════════════════════════════════════════
# Data Models
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class EpisodeTask:
    """A unit of work for the episode processing queue."""

    name: str
    episode_body: str
    group_id: str
    source_description: str
    reference_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    entity_types: dict[str, Any] | None = field(default=None)
    edge_types: dict[str, Any] | None = field(default=None)
    request_id: str | None = field(default=None)

    @property
    def can_retry(self) -> bool:
        return self.retry_count < self.max_retries

    @property
    def backoff_seconds(self) -> float:
        """Exponential backoff with full jitter. Cap at 60s."""
        base = 2**self.retry_count
        cap = min(base, 60)
        return random.uniform(0, cap)

    def to_dict(self) -> dict[str, Any]:
        result = {
            "name": self.name,
            "episode_body": self.episode_body[:200],  # truncate for logging
            "group_id": self.group_id,
            "source_description": self.source_description,
            "reference_time": self.reference_time.isoformat(),
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat(),
        }
        if self.request_id is not None:
            result["request_id"] = self.request_id
        # Log type names only (type references are not JSON-serializable)
        if self.entity_types:
            result["entity_type_names"] = list(self.entity_types.keys())
        if self.edge_types:
            result["edge_type_names"] = list(self.edge_types.keys())
        return result


@dataclass
class WorkerMetrics:
    """Observable metrics for the episode worker."""

    episodes_enqueued: int = 0
    episodes_processed: int = 0
    episodes_failed: int = 0
    episodes_dead_lettered: int = 0
    episodes_dropped_queue_full: int = 0
    queue_depth: int = 0
    worker_running: bool = False
    _processing_times: list[float] = field(default_factory=list)

    def record_processing_time(self, seconds: float) -> None:
        self._processing_times.append(seconds)
        if len(self._processing_times) > 100:
            self._processing_times = self._processing_times[-100:]

    @property
    def avg_processing_time_ms(self) -> float:
        if not self._processing_times:
            return 0.0
        return (sum(self._processing_times) / len(self._processing_times)) * 1000

    @property
    def max_processing_time_ms(self) -> float:
        if not self._processing_times:
            return 0.0
        return max(self._processing_times) * 1000

    def to_dict(self) -> dict[str, Any]:
        total = self.episodes_processed + self.episodes_failed
        return {
            "episodes_enqueued": self.episodes_enqueued,
            "episodes_processed": self.episodes_processed,
            "episodes_failed": self.episodes_failed,
            "episodes_dead_lettered": self.episodes_dead_lettered,
            "episodes_dropped_queue_full": self.episodes_dropped_queue_full,
            "queue_depth": self.queue_depth,
            "worker_running": self.worker_running,
            "avg_processing_time_ms": round(self.avg_processing_time_ms, 1),
            "max_processing_time_ms": round(self.max_processing_time_ms, 1),
            "success_rate": round(self.episodes_processed / max(total, 1), 3),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Dead Letter Store
# ═══════════════════════════════════════════════════════════════════════════════


# audit-2026-04-07/p1-1: secret patterns we redact from any string before
# it lands on disk. Defense in depth — even if upstream callers think they're
# sending sanitized data, the dead-letter file is the last stop and a common
# place for forensic exfiltration. CWE-532 (Insertion of Sensitive Information
# into Log File). Patterns mirror common LLM/cloud key formats.
_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),  # OpenAI/Anthropic
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),  # Google
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),  # GitHub
    re.compile(r"Bearer\s+[A-Za-z0-9._-]{20,}", re.IGNORECASE),
    re.compile(r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}"),  # JWT
)


def _redact(text: str) -> str:
    """Replace secret-looking substrings with ***REDACTED***. No-op for non-strings."""
    if not isinstance(text, str):
        return text
    result = text
    for pat in _SECRET_PATTERNS:
        result = pat.sub("***REDACTED***", result)
    return result


class DeadLetterStore:
    """Persists failed episodes to JSONL for manual inspection and replay.

    audit-2026-04-07/p1-1: privacy-by-default rewrite.

    Previously this stored the full ``episode_body`` plaintext on every failure,
    which means all content the LLM saw — including potentially PII, student
    answers, system prompts containing instructions, and the rare leaked
    credential — was permanently archived in ``data/dead_letter_episodes.jsonl``.
    Combined with the file being committed to git in some failure modes, this
    is a CWE-532 vector.

    New default behavior:
      - Always store ``episode_body_sha256`` (16-byte hex prefix) so replays can
        verify content matches without revealing it.
      - Only store ``episode_body_full`` when env ``DEAD_LETTER_STORE_FULL_BODY``
        is set to ``true`` / ``1`` / ``yes`` (opt-in for debugging).
      - When stored, the full body is run through ``_redact`` to scrub obvious
        secret patterns (OpenAI/Google/GitHub/Bearer/JWT).
      - Error messages are truncated to 200 chars and redacted.
      - Logger.error no longer interpolates the raw error string — only the
        type name — so accidentally-leaked secrets in exception messages don't
        end up in the structured log stream either.
    """

    def __init__(self, file_path: str = "data/dead_letter_episodes.jsonl") -> None:
        self._file_path = Path(file_path)
        self._file_path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _store_full_body_enabled() -> bool:
        flag = (os.environ.get("DEAD_LETTER_STORE_FULL_BODY") or "").strip().lower()
        return flag in ("1", "true", "yes", "on")

    def store(
        self, task: EpisodeTask, error: Exception, *, request_id: str | None = None
    ) -> None:
        """Append failed task to JSONL file synchronously (tiny payload, acceptable).

        Privacy: episode_body_full is omitted unless DEAD_LETTER_STORE_FULL_BODY=true.
        """
        # Always: hash + minimal metadata (safe to keep forever)
        body_bytes = task.episode_body.encode("utf-8", errors="replace")
        body_hash = hashlib.sha256(body_bytes).hexdigest()

        record = {
            **task.to_dict(),
            "episode_body_sha256": body_hash,
            "episode_body_length": len(task.episode_body),
            "error": _redact(str(error))[:200],
            "error_type": type(error).__name__,
            "failed_at": datetime.now(timezone.utc).isoformat(),
        }

        # Opt-in: full body (still redacted for known secret patterns)
        if self._store_full_body_enabled():
            record["episode_body_full"] = _redact(task.episode_body)

        if request_id is not None:
            record["request_id"] = request_id

        with open(self._file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        # audit-2026-04-07/p1-1: scrub error from logger interpolation. Type
        # name only — full message is in the JSONL record (already redacted).
        logger.error(
            f"Dead-lettered episode: name={task.name}, "
            f"retries={task.retry_count}/{task.max_retries}, "
            f"error_type={type(error).__name__}, "
            f"sha256={body_hash[:16]}"
        )

    def count(self) -> int:
        if not self._file_path.exists():
            return 0
        with open(self._file_path, "r", encoding="utf-8") as f:
            return sum(1 for _ in f)


# ═══════════════════════════════════════════════════════════════════════════════
# GraphitiEpisodeWorker
# ═══════════════════════════════════════════════════════════════════════════════


class GraphitiEpisodeWorker:
    """
    Async background worker for sequential graphiti add_episode processing.

    Architecture:
        API handler --put_nowait--> asyncio.Queue --get--> Worker --await--> graphiti.add_episode()
                                     (maxsize=100)       (single task)      (sequential, 5-30s each)

    Usage in FastAPI lifespan:
        worker = GraphitiEpisodeWorker()
        await worker.initialize_graphiti(neo4j_uri, neo4j_user, neo4j_password, google_api_key)
        await worker.start()
        app.state.episode_worker = worker
        ...
        await worker.stop(timeout=30.0)

    Usage in API handler:
        worker = request.app.state.episode_worker
        worker.enqueue(EpisodeTask(name=..., episode_body=..., group_id=...))
    """

    def __init__(
        self,
        maxsize: int = 100,
        dead_letter_path: str = "data/dead_letter_episodes.jsonl",
    ) -> None:
        self._graphiti: Optional[Graphiti] = None
        self._queue: asyncio.Queue[EpisodeTask] = asyncio.Queue(maxsize=maxsize)
        self._worker_task: Optional[asyncio.Task[None]] = None
        self._dead_letter = DeadLetterStore(dead_letter_path)
        self._metrics = WorkerMetrics()
        self._started = False

    # ── Initialization ──

    async def initialize_graphiti(
        self,
        neo4j_uri: str,
        neo4j_user: str,
        neo4j_password: [REDACTED:env-cred]
        google_api_key: [REDACTED:env-cred]
        llm_model: str = "gemini-2.5-flash",
    ) -> bool:
        """
        Create Graphiti instance with GeminiClient + GeminiEmbedder and build indices.

        Sets os.environ GOOGLE_API_KEY so the Gemini SDK can find it.
        Returns True on success, False if degraded (worker runs but skips episodes).

        ⚠️ CRITICAL: Pre-flight Neo4j connectivity probe MUST run BEFORE Graphiti(...)
        instantiation. graphiti-core v0.28.2's Neo4jDriver.__init__ contains a
        fire-and-forget asyncio task that triggers an unawaited
        build_indices_and_constraints() coroutine on construction:

            # graphiti_core/driver/neo4j_driver.py:91-101
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.build_indices_and_constraints())  # L98 - LEAKED
            except RuntimeError:
                pass

        The created task reference is never stored, no done-callback is attached,
        and no exception handler wraps it. If Neo4j is unreachable, the task raises
        ServiceUnavailable inside the loop and Python emits
        "Task exception was never retrieved" warnings. We cannot patch graphiti-core
        (pinned 0.28.2). The only safe approach is: probe connectivity with a bare
        neo4j AsyncDriver first, and only instantiate Graphiti(...) after the probe
        succeeds. If the probe fails we never construct Graphiti, so the leaked task
        never starts.
        """
        # Pre-flight: bare-driver Neo4j reachability probe (no graphiti-core involved).
        # ✅ Verified pattern: neo4j-python-driver verify_connectivity() probe.
        # Reference: graphiti_core/driver/neo4j_driver.py:98 (fire-and-forget bug)
        from neo4j import (
            AsyncGraphDatabase,
        )  # local import: avoid module-load side effects
        from neo4j.exceptions import AuthError, ServiceUnavailable

        temp_driver = None
        try:
            temp_driver = AsyncGraphDatabase.driver(
                uri=neo4j_uri,
                auth=(neo4j_user or "", neo4j_password or ""),
            )
            await asyncio.wait_for(temp_driver.verify_connectivity(), timeout=5.0)
            logger.info(
                "GraphitiEpisodeWorker: Neo4j pre-flight ok "
                f"(uri={neo4j_uri}, db=neo4j)"
            )
        except (ServiceUnavailable, AuthError, asyncio.TimeoutError, OSError) as e:
            logger.error(
                "GraphitiEpisodeWorker: Neo4j pre-flight failed "
                f"({type(e).__name__}: {e}). "
                "Skipping Graphiti instantiation to avoid graphiti-core "
                "fire-and-forget task leak (neo4j_driver.py:98). "
                "Worker will run in degraded mode."
            )
            self._graphiti = None
            return False
        finally:
            if temp_driver is not None:
                try:
                    await temp_driver.close()
                except Exception as close_err:  # noqa: BLE001
                    logger.debug(f"temp_driver.close() best-effort: {close_err}")

        # Pre-flight passed → safe to instantiate Graphiti (existing logic below)
        try:
            # Make API key available to Gemini SDK
            os.environ.setdefault("GOOGLE_API_KEY", google_api_key)
            # M2 修复 (2026-07-13, 路线图 v2): graphiti_core.helpers 在 **import
            # 时** 绑定 SEMAPHORE_LIMIT (对抗审查实证: 此处运行时赋值对已 import
            # 的模块无效)。真正生效的注入点是 docker-compose 的 SEMAPHORE_LIMIT
            # env (进程启动前)。此处仅作未设置时的兜底 setdefault, 不再硬覆盖 —
            # 本地 35B 模型场景 compose 侧设 1, 云模型默认 3。
            os.environ.setdefault("SEMAPHORE_LIMIT", "3")

            from app.graphiti.embedder_factory import build_embedder
            from app.graphiti.llm_factory import (
                build_cross_encoder,
                build_llm_client,
                get_graphiti_max_coroutines,
            )

            # M2 (2026-07-13, 路线图 v2): LLM/reranker 从硬编码 Gemini 改为
            # 工厂注入 (GRAPHITI_LLM_PROVIDER / GRAPHITI_RERANKER_PROVIDER =
            # gemini|local)。local 分支 fail-closed 契约: 上线前必过
            # scripts/graphiti_schema_canary.py。embedder 沿用既有工厂。
            llm_client = build_llm_client(google_api_key, llm_model)
            embedder = build_embedder(google_api_key)
            cross_encoder = build_cross_encoder(google_api_key, llm_model)

            # Safe: pre-flight passed, Neo4j is reachable. graphiti-core's L98
            # leaked task will still fire, but build_indices_and_constraints will
            # succeed instead of raising, so no "Task exception never retrieved".
            self._graphiti = Graphiti(
                uri=neo4j_uri,
                user=neo4j_user,
                password=[REDACTED:env-cred]
                llm_client=llm_client,
                embedder=embedder,
                cross_encoder=cross_encoder,
                # local 35B 默认 1 (与 compose SEMAPHORE_LIMIT 配对), 云默认 3
                max_coroutines=get_graphiti_max_coroutines(),
            )

            await self._graphiti.build_indices_and_constraints()
            logger.info(
                f"GraphitiEpisodeWorker: Graphiti initialized "
                f"(neo4j={neo4j_uri}, model={llm_model})"
            )
            return True

        except Exception as e:
            logger.error(
                f"GraphitiEpisodeWorker: Failed to initialize Graphiti client: {e}. "
                f"Worker will run in degraded mode (episodes will be dead-lettered)."
            )
            self._graphiti = None
            return False

    # ── Public API ──

    def set_graphiti_client(self, client: Graphiti) -> None:
        """Set or replace the graphiti client (useful for lazy initialization)."""
        self._graphiti = client

    async def start(self) -> None:
        """Start the background worker task."""
        if self._started:
            logger.warning("GraphitiEpisodeWorker already started")
            return

        self._worker_task = asyncio.create_task(
            self._run(), name="graphiti-episode-worker"
        )
        self._started = True
        self._metrics.worker_running = True
        logger.info(f"GraphitiEpisodeWorker started (maxsize={self._queue.maxsize})")

    async def stop(self, timeout: float = 30.0) -> None:
        """
        Graceful shutdown: drain remaining events, then stop.

        Uses Python 3.13+ Queue.shutdown() for clean termination.
        """
        if not self._started:
            return

        pending = self._queue.qsize()
        logger.info(f"Stopping GraphitiEpisodeWorker, {pending} events pending...")

        # Step 1: Signal queue shutdown (no more puts, gets continue until empty)
        queue_shutdown = getattr(self._queue, "shutdown", None)
        if queue_shutdown is not None:
            queue_shutdown(immediate=False)
        else:
            # Py<3.13 无 Queue.shutdown(): 哨兵入队, worker 排空存量后自然退出
            try:
                self._queue.put_nowait(_STOP_SENTINEL)
            except asyncio.QueueFull:
                pass  # 队列满: 依赖下方 drain 超时 + cancel 兜底

        # Step 2: Wait for worker to drain and exit naturally
        if self._worker_task is not None:
            try:
                await asyncio.wait_for(self._worker_task, timeout=timeout)
                logger.info("GraphitiEpisodeWorker drained and stopped cleanly")
            except asyncio.TimeoutError:
                remaining = self._queue.qsize()
                logger.warning(
                    f"Worker drain timed out ({timeout}s), "
                    f"{remaining} events will be lost. Force cancelling..."
                )
                self._worker_task.cancel()
                try:
                    await self._worker_task
                except asyncio.CancelledError:
                    pass

        self._started = False
        self._metrics.worker_running = False

    def enqueue(self, task: EpisodeTask) -> bool:
        """
        Enqueue an episode for background processing.

        Non-blocking. Returns False if queue is full or shut down (event dropped).
        Caller should handle the False return (e.g., log, fallback).
        """
        try:
            self._queue.put_nowait(task)
            self._metrics.episodes_enqueued += 1
            self._metrics.queue_depth = self._queue.qsize()
            logger.debug(
                f"Enqueued episode: name={task.name[:50]}, "
                f"queue_depth={self._queue.qsize()}"
            )
            return True
        except asyncio.QueueFull:
            self._metrics.episodes_dropped_queue_full += 1
            logger.warning(
                f"Episode queue full (maxsize={self._queue.maxsize}), "
                f"dropping: {task.name[:50]}"
            )
            return False
        except _QUEUE_SHUTDOWN:
            logger.warning(f"Episode queue shut down, cannot enqueue: {task.name[:50]}")
            return False

    @property
    def metrics(self) -> WorkerMetrics:
        """Current worker metrics (read-only snapshot with updated queue_depth)."""
        self._metrics.queue_depth = self._queue.qsize()
        return self._metrics

    @property
    def is_ready(self) -> bool:
        """True if worker is started AND graphiti client is initialized."""
        return self._started and self._graphiti is not None

    # ── Internal ──

    async def _run(self) -> None:
        """Worker main loop: sequential episode processing."""
        logger.info("Worker loop started")

        while True:
            try:
                task = await self._queue.get()
            except _QUEUE_SHUTDOWN:
                logger.info("Queue shut down signal received, worker exiting")
                break
            if task is _STOP_SENTINEL:
                logger.info("Stop sentinel received, worker exiting")
                break

            start = time.perf_counter()
            try:
                await self._process_episode(task)
                elapsed = time.perf_counter() - start
                self._metrics.episodes_processed += 1
                self._metrics.record_processing_time(elapsed)
                logger.info(
                    f"Episode processed: name={task.name[:50]}, "
                    f"took={elapsed * 1000:.0f}ms"
                )
            except Exception as e:
                elapsed = time.perf_counter() - start
                self._metrics.episodes_failed += 1
                self._metrics.record_processing_time(elapsed)
                await self._handle_failure(task, e)
            finally:
                self._queue.task_done()
                self._metrics.queue_depth = self._queue.qsize()

        logger.info("Worker loop exited")

    async def _process_episode(self, task: EpisodeTask) -> None:
        """Call graphiti add_episode for a single task."""
        if self._graphiti is None:
            raise RuntimeError("Graphiti client not initialized")

        # GRAPHITI-NATIVE Phase 4 (D6): add_episode 语义队列收窄为非结构化材料
        # (对话归档全文/自由文本日志/历史回灌)。结构化事件 (批注/错误/对话摘要)
        # 主路径已在 memory_service 路由到 graphiti_structured_writer; 它们出现
        # 在此队列 = fallback (graphiti 未就绪/写失败), 合法但需可观测。
        _STRUCTURED_SOURCE_DESCS = {
            "learning-tip-record",
            "callout-annotation-record",
            "misconception-record",
            "problem-trap-record",
            "logical-fallacy-record",
            "guided-thinking-record",
        }
        if task.source_description in _STRUCTURED_SOURCE_DESCS:
            logger.info(
                f"[Graphiti-native D6] structured event in semantic queue "
                f"(fallback path): {task.name}"
            )

        # P0-5 (2026-05-14): Canvas D16 group_id 用冒号分隔 (vault:cs_61b:subj),
        # 但 Graphiti 上游 validator 拒绝冒号。在 Graphiti 边界 sanitize 为
        # 双下划线分隔形式 (vault__cs_61b__subj)，Canvas 业务逻辑保持 D16 不变。
        #
        # M2 双图隔离 (2026-07-13): add_episode 是 LLM 抽取通道, 产物一律落
        # 语义影子分组 (…__semantic) — graphiti 的 dedupe/invalidation 以
        # group 为边界, 影子分组使 LLM 实体既不会 resolve 到主图 uuid5 节点
        # 也不会 invalidate 主图边。分组在此单点固定, 不暴露给任何 enqueue
        # 调用方; 主图只由 graphiti_structured_writer 直写。读侧已同构:
        # search_memories 主图+影子图同查。
        from app.graphiti.group_id_compat import (
            sanitize_group_id_for_graphiti,
            semantic_group_id,
        )

        kwargs: dict[str, Any] = {
            "name": task.name,
            "episode_body": task.episode_body,
            "group_id": semantic_group_id(
                sanitize_group_id_for_graphiti(task.group_id)
            ),
            "source_description": task.source_description,
            "reference_time": task.reference_time,
        }
        if task.entity_types is not None:
            kwargs["entity_types"] = task.entity_types
        if task.edge_types is not None:
            kwargs["edge_types"] = task.edge_types

        await self._graphiti.add_episode(**kwargs)

        # 5-ge-2 Phase B: 演化型事件 (callout 改写/删除、wikilink 删除、error、calibration)
        # 在 add_episode 成功后旁路维护 belief 时序版本链 (旧版 invalid_at + 新版 active)。
        # 双层解耦: belief 旁路失败非致命, 不回滚主 episode 写入; belief 业务不泄漏进 worker。
        from app.graphiti.canvas_episode import EVOLUTION_EVENT_TYPES

        if task.metadata.get("event_type") in EVOLUTION_EVENT_TYPES:
            try:
                from app.services.graphiti_belief_service import (
                    maybe_update_belief_from_task,
                )

                await maybe_update_belief_from_task(self._graphiti, task)
            except Exception as e:  # noqa: BLE001 — belief 旁路失败不阻断主写入
                # 审查 M4: 带 belief_key/event_type 便于后续对账补偿 (旁路无重试)
                logger.warning(
                    "belief chain update skipped (non-fatal): "
                    f"event_type={task.metadata.get('event_type')} "
                    f"belief_key=[REDACTED:env-cred]'belief_key')} err={e}"
                )

    async def _handle_failure(self, task: EpisodeTask, error: Exception) -> None:
        """Handle a failed episode: retry with backoff or dead-letter."""
        if isinstance(error, _PERMANENT_EPISODE_ERRORS):
            # 确定性校验错误重试必然复现 — 直接死信留证 (2026-07-22 批次0)
            logger.error(
                f"Episode permanently failed (deterministic validation, "
                f"skip retry): {error}"
            )
            self._metrics.episodes_dead_lettered += 1
            self._dead_letter.store(task, error)
            return
        if task.can_retry:
            task.retry_count += 1
            backoff = task.backoff_seconds
            logger.warning(
                f"Episode failed (attempt {task.retry_count}/{task.max_retries}), "
                f"retrying in {backoff:.1f}s: {error}"
            )
            await asyncio.sleep(backoff)
            try:
                self._queue.put_nowait(task)
            except (asyncio.QueueFull, _QUEUE_SHUTDOWN):
                # Cannot re-queue: dead-letter it
                self._metrics.episodes_dead_lettered += 1
                self._dead_letter.store(task, error)
        else:
            self._metrics.episodes_dead_lettered += 1
            self._dead_letter.store(task, error)


# ═══════════════════════════════════════════════════════════════════════════════
# Singleton accessor (consistent with project pattern)
# ═══════════════════════════════════════════════════════════════════════════════

_worker_instance: Optional[GraphitiEpisodeWorker] = None


def get_episode_worker() -> GraphitiEpisodeWorker:
    """Get or create the singleton GraphitiEpisodeWorker instance."""
    global _worker_instance
    if _worker_instance is None:
        _worker_instance = GraphitiEpisodeWorker()
    return _worker_instance


async def cleanup_episode_worker() -> None:
    """Cleanup the singleton worker instance (for shutdown)."""
    global _worker_instance
    if _worker_instance is not None:
        await _worker_instance.stop(timeout=30.0)
        _worker_instance = None
````

## File: backend/app/services/memory_service.py
````python
# Canvas Learning System - Memory Service
# Story 22.4: 学习历史存储与查询API
# Story 30.8: 多学科隔离与group_id支持
# Story 36.9: 学习记忆双写（Neo4j + Graphiti JSON存储）
# ✅ Verified from docs/stories/22.4.story.md#Dev-Notes
# ✅ Verified from docs/stories/30.8.story.md#Task-1.1
# ✅ Verified from docs/stories/36.9.story.md#AC-36.9.1
"""
Memory Service - Learning history storage and query.

Story 22.4 Implementation:
- AC-22.4.1: POST /api/v1/memory/episodes - Record learning events
- AC-22.4.2: GET /api/v1/memory/episodes - Query learning history
- AC-22.4.3: GET /api/v1/memory/concepts/{id}/history - Query concept history
- AC-22.4.4: GET /api/v1/memory/review-suggestions - Get review suggestions
- AC-22.4.5: Pagination and filtering support

Story 30.8 Implementation:
- AC-30.8.1: Each discipline uses independent `group_id` namespace
- AC-30.8.2: Auto-infer discipline from Canvas path
- AC-30.8.3: API supports `?subject=数学` query parameter filtering

Story 36.9 Implementation:
- AC-36.9.1: 学习事件写入Neo4j成功后自动尝试写入LearningMemoryClient
- AC-36.9.2: JSON写入使用fire-and-forget模式，不阻塞主流程
- AC-36.9.3: JSON写入失败时静默降级，记录警告日志但不抛出异常
- AC-36.9.4: JSON写入超时保护（500ms），超时后放弃写入
- AC-36.9.5: 可通过环境变量ENABLE_GRAPHITI_JSON_DUAL_WRITE开关双写功能

[Source: docs/prd/EPIC-22-MEMORY-SYSTEM-NEO4J-GRAPHITI.md#Story-22.4]
[Source: docs/stories/22.4.story.md#MemoryService实现]
[Source: docs/stories/30.8.story.md#学科推断规则]
[Source: docs/stories/36.9.story.md#Dev-Notes]
"""

import asyncio
import hashlib
import json
import logging
import time
import unicodedata
import uuid

import structlog
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from cachetools import TTLCache

from app.clients.neo4j_client import Neo4jClient, get_neo4j_client
from app.config import DEFAULT_GROUP_ID, settings
from app.core.decision_tracker import log_decision
from app.core.failed_writes_constants import FAILED_WRITES_FILE, failed_writes_lock
from app.core.subject_config import (
    build_vault_group_id,
    extract_canvas_name,
    extract_subject_from_canvas_path,
)
from app.services.episode_worker import EpisodeTask, get_episode_worker
from app.graphiti.entity_types import CANVAS_ENTITY_TYPES, CANVAS_EDGE_TYPES

logger = structlog.get_logger(__name__)


def _vault_scoped_group_id(subject=None, canvas_name=None) -> str:
    """G-DEFAULT 根治 (2026-07-10, D16/C-3): 写侧统一 vault:<vault_id>[:<二级>] 前缀.

    取代本模块此前直接调 Story 1.9 legacy build_group_id(subject[, canvas])——
    legacy 格式让所有 vault 的记忆塌进同一 subject 桶(2026-07-10 cypher 实测:
    图中 88 节点 group_id 全为 default/cs188/test fallback, 零真实 vault 身份)。
    二级优先 canvas_name(D16 vault:<id>:<canvas> 规约), 无 canvas 时用 subject。
    """
    from app.config import get_current_vault_id

    vault_id = get_current_vault_id()
    if canvas_name:
        return build_vault_group_id(vault_id, canvas_path=canvas_name)
    if subject:
        return build_vault_group_id(vault_id, subject_id=subject)
    return build_vault_group_id(vault_id)


# Story 31.5: Cache TTL for score history queries (30 seconds)
SCORE_HISTORY_CACHE_TTL = 30

# Story 38.6: FAILED_WRITES_FILE and failed_writes_lock imported from
# app.core.failed_writes_constants (shared with agent_service.py)


# Story 30.10 AC-30.10.1: Deterministic episode ID generation
def _generate_deterministic_episode_id(
    user_id: str, canvas_path: str, node_id: str, concept: str
) -> str:
    """
    Generate a deterministic episode ID based on content hash.

    Same learning event (same user, canvas, node, concept) always produces
    the same episode_id, enabling idempotent writes.

    [Source: docs/stories/30.10.idempotency-fix.story.md#AC-30.10.1]
    """
    content = f"{user_id}:{canvas_path}:{node_id}:{concept}"
    hash_hex = hashlib.sha256(content.encode("utf-8")).hexdigest()[:32]
    return f"episode-{hash_hex}"


# Story 30.10 AC-30.10.4: Deterministic batch episode ID generation
def _generate_batch_episode_id(
    canvas_path: str, node_id: str, event_type: str, timestamp: str
) -> str:
    """
    Generate a deterministic batch episode ID based on event content.

    Same batch event always produces the same episode_id.

    [Source: docs/stories/30.10.idempotency-fix.story.md#AC-30.10.4]
    """
    content = f"{canvas_path}:{node_id}:{event_type}:{timestamp}"
    hash_hex = hashlib.sha256(content.encode("utf-8")).hexdigest()[:32]
    return f"batch-{hash_hex}"


@dataclass
class ScoreHistoryResponse:
    """
    Score history response data.

    Story 31.5 AC-31.5.1: Response format for score history query.

    Attributes:
        scores: List of historical scores (0-100, oldest to newest)
        timestamps: List of corresponding timestamps
        average: Average score
        sample_size: Number of records

    [Source: specs/data/score-history-response.schema.json]
    """

    concept_id: str
    canvas_name: str
    scores: List[int]
    timestamps: List[str]
    average: float
    sample_size: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "concept_id": self.concept_id,
            "canvas_name": self.canvas_name,
            "scores": self.scores,
            "timestamps": self.timestamps,
            "average": self.average,
            "sample_size": self.sample_size,
        }


class MemoryService:
    """
    学习记忆服务

    ✅ Verified from docs/stories/22.4.story.md#MemoryService实现:
    - record_learning_event(): 记录学习事件到Neo4j和Graphiti
    - get_learning_history(): 获取学习历史(分页)
    - get_review_suggestions(): 获取复习建议(基于艾宾浩斯遗忘曲线)

    [Source: docs/stories/22.4.story.md#Dev-Notes]
    """

    MAX_EPISODE_CACHE = 2000  # Story 38.2: Upper bound on in-memory episode cache

    def __init__(
        self,
        neo4j_client: Optional[Neo4jClient] = None,
    ):
        """
        Initialize MemoryService.

        Args:
            neo4j_client: Neo4j client instance (optional, uses singleton if not provided)

        [Source: docs/stories/22.4.story.md#MemoryService实现]
        """
        self.neo4j = neo4j_client or get_neo4j_client()
        self._initialized = False
        self._episodes: List[Dict[str, Any]] = []  # In-memory episode store
        # Story 38.2 AC-2: Track whether episodes have been recovered from Neo4j
        self._episodes_recovered: bool = False
        # Story 38.2: Lock to prevent concurrent recovery attempts
        self._recovery_lock = asyncio.Lock()
        # Fix C5: Lock to prevent concurrent _episodes mutations
        self._episodes_lock = asyncio.Lock()

        # Story 36.13 AC-4: Read configurable values from Settings
        try:
            from app.config import get_settings

            _settings = get_settings()
            _score_cache_maxsize = _settings.SCORE_HISTORY_CACHE_MAXSIZE
        except (ImportError, RuntimeError, AttributeError) as e:
            logger.warning(f"Settings unavailable, using default cache config: {e}")
            _score_cache_maxsize = 1000

        # Story 31.5: Cache for score history queries (30s TTL)
        # NFR-P0: Bounded TTLCache replaces bare dict to prevent unbounded memory growth
        # Story 36.13 AC-4: maxsize configurable via Settings
        self._score_history_cache: TTLCache = TTLCache(
            maxsize=_score_cache_maxsize, ttl=SCORE_HISTORY_CACHE_TTL
        )
        # NFR-P0: Lock for cache stampede protection (double-check locking)
        self._score_cache_lock = asyncio.Lock()
        # Story 30.24 AC-30.24.4: Track batch write failures for shutdown safety
        self._pending_failed_writes: List[Dict[str, Any]] = []
        logger.debug("MemoryService initialized")

    async def initialize(self) -> bool:
        """Initialize the service and underlying clients."""
        if self._initialized:
            return True

        await self.neo4j.initialize()
        self._initialized = True

        # Story 38.2 AC-2: Recover episodes from Neo4j on startup
        await self._recover_episodes_from_neo4j()

        logger.info("MemoryService initialized successfully")
        return True

    async def ensure_fulltext_index(self) -> None:
        """
        Create the episode_content fulltext index in Neo4j if it doesn't exist.

        Epic 4 Feature 4.1: Auto-create Neo4j fulltext index on startup.
        Uses IF NOT EXISTS for idempotency — safe to call multiple times.

        Gracefully handles:
        - Neo4j not initialized / unavailable
        - Index already exists
        - Permission errors or connection failures
        """
        if not self.neo4j.stats.get("initialized", False):
            logger.info(
                "[Epic 4] Skipping fulltext index creation: Neo4j not initialized"
            )
            return

        # 批次4' R4 (MEM-FLYWHEEL): CJK analyzer — 中文 BM25 分词 (standard 单字
        # 切分致中文精度 -26pt)。IF NOT EXISTS 语义: 已有 cjk 版索引时跳过;
        # 全新库启动时直接建成 cjk 版 (与 scripts/rebuild_fulltext_cjk.cypher 一致)
        cypher = (
            "CREATE FULLTEXT INDEX episode_content IF NOT EXISTS "
            "FOR (n:EpisodicNode) ON EACH [n.content] "
            "OPTIONS {indexConfig: {`fulltext.analyzer`: 'cjk'}}"
        )
        try:
            await self.neo4j.run_query(cypher)
            logger.info(
                "[Epic 4] Fulltext index 'episode_content' ensured on EpisodicNode.content"
            )
        except (RuntimeError, ConnectionError, Exception) as e:
            logger.warning(f"[Epic 4] Fulltext index creation failed (non-fatal): {e}")

    async def _recover_episodes_from_neo4j(self) -> None:
        """
        Recover episodes from Neo4j on startup.

        Story 38.2 AC-1/AC-2: Populate self._episodes from Neo4j so the
        in-memory cache survives restarts.

        Story 38.2 AC-3: If Neo4j is unavailable, graceful degradation —
        _episodes remains empty, _episodes_recovered stays False, and
        recovery is re-attempted lazily on first query.

        Uses _recovery_lock to prevent concurrent recovery from multiple
        simultaneous get_learning_history() calls.

        [Source: docs/stories/38.2.story.md#Task-2]
        """
        async with self._recovery_lock:
            # Double-check after acquiring lock (another coroutine may have completed recovery)
            if self._episodes_recovered:
                return
            try:
                records = await self.neo4j.get_all_recent_episodes(limit=1000)
                added = 0
                if records:
                    # Build set of existing episode keys to avoid duplicates
                    # Key includes timestamp so same user+concept at different times are kept
                    existing_keys = {
                        (
                            e.get("user_id"),
                            e.get("concept"),
                            str(e.get("timestamp") or ""),
                        )
                        for e in self._episodes
                    }
                    for idx, record in enumerate(records):
                        user_id = record.get("user_id")
                        concept = record.get("concept")
                        timestamp = str(record.get("timestamp") or "")
                        # Skip if already in cache (from degraded-mode recording)
                        if (user_id, concept, timestamp) in existing_keys:
                            continue
                        # T1 统一 (2026-07-10): Neo4j 物理层存 `__` 格式, 恢复进
                        # 内存 cache 前转回 D16 冒号 — 否则 Tier 3 cache 过滤
                        # (冒号比较) 对 recovered episodes 恒不匹配。
                        from app.graphiti.group_id_compat import (
                            desanitize_group_id_from_graphiti,
                        )

                        episode = {
                            "episode_id": f"recovered-{idx}-{user_id or 'unknown'}-{record.get('concept_id') or 'unknown'}",
                            "user_id": user_id,
                            "concept": concept,
                            "concept_id": record.get("concept_id"),
                            "score": record.get("score"),
                            "timestamp": timestamp,
                            "group_id": desanitize_group_id_from_graphiti(
                                record.get("group_id") or ""
                            ),
                            "review_count": record.get("review_count") or 0,
                            "episode_type": "recovered",
                        }
                        self._episodes.append(episode)
                        existing_keys.add((user_id, concept, timestamp))
                        added += 1
                    # Cap episode cache to prevent unbounded growth
                    if len(self._episodes) > self.MAX_EPISODE_CACHE:
                        self._episodes = self._episodes[-self.MAX_EPISODE_CACHE :]
                self._episodes_recovered = True
                logger.info(
                    f"MemoryService: recovered {added} episodes from Neo4j ({len(records)} returned, {len(records) - added} deduped)"
                )
            except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
                # AC-3: Graceful degradation — start with empty history
                self._episodes_recovered = False
                logger.warning(
                    f"MemoryService: Neo4j unavailable, starting with empty history ({e})"
                )

    def _enqueue_episode(
        self,
        name: str,
        episode_body: str,
        group_id: str,
        source_description: str = "canvas_learning_system",
        entity_types: Optional[Dict[str, Any]] = None,
        edge_types: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Enqueue a learning episode for Graphiti processing.

        Phase 2: Replaces fire-and-forget JSON dual-write and bridge calls.
        Non-blocking. Worker processes sequentially via graphiti add_episode.

        Returns True if enqueued, False if queue full or worker unavailable.
        """
        worker = get_episode_worker()
        if not worker.is_ready:
            logger.debug("Episode worker not ready, skipping enqueue")
            return False

        # Capture request_id from structlog contextvars at enqueue time,
        # since the worker processes tasks in a separate coroutine context.
        _ctx = structlog.contextvars.get_contextvars()
        task = EpisodeTask(
            name=name,
            episode_body=episode_body,
            group_id=group_id,
            source_description=source_description,
            entity_types=entity_types,
            edge_types=edge_types,
            request_id=_ctx.get("request_id"),
        )
        return worker.enqueue(task)

    def enqueue_conversation_archive(
        self,
        *,
        session_id: str,
        conversation_text: str,
        group_id: str,
    ) -> bool:
        """M3 (2026-07-13): SessionEnd 会话归档 → 语义通道 (D6 非结构化材料)。

        对话全文经 worker add_episode 做 LLM 实体抽取; worker 在
        _process_episode 单点把 group 重定向到 __semantic 影子分组
        (M2 双图隔离), 本方法与调用方均无法指定主图 — 提示词被污染
        也没有通路碰到结构化主链。返回 True=已入队 (异步, 非已写入)。
        """
        return self._enqueue_episode(
            name=f"session-archive:{session_id[:16]}",
            episode_body=conversation_text,
            group_id=group_id,
            source_description="conversation-archive",
        )

    def _record_structured_outbox(self, entry: Dict[str, Any]) -> bool:
        """A7 (P2): 结构化写入彻底失败时立即落盘 outbox, 不静默丢数据。

        立即写 FAILED_WRITES_FILE (非等 shutdown flush) 抗进程崩溃。条目带
        kind='knowledge_entity' 判别符, recover_failed_writes 据此重放
        (重新走 record_knowledge_entity 的结构化写入, 此时 worker 通常已就绪)。

        注: callout/relation 的主要持久化是 frontmatter + 启动回填 (vault md 是
        真相源, backfill_vault 重建边), outbox 是非结构化材料/边界场景的兜底。
        返回 True=已落盘, False=连兜底也失败(真数据丢失风险, 已 error 日志)。
        """
        try:
            FAILED_WRITES_FILE.parent.mkdir(parents=True, exist_ok=True)
            with failed_writes_lock:
                with open(FAILED_WRITES_FILE, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            return True
        except OSError as e:
            logger.error("[A7] outbox 落盘失败 (数据可能丢失): %s", e)
            return False

    async def record_learning_event(
        self,
        user_id: str,
        canvas_path: str,
        node_id: str,
        concept: str,
        agent_type: str,
        score: Optional[int] = None,
        duration_seconds: Optional[int] = None,
        subject: Optional[str] = None,
    ) -> str:
        """
        记录学习事件

        同时存储到Neo4j知识图谱和Graphiti时序数据库

        ✅ Verified from docs/stories/22.4.story.md#record_learning_event:
        - 存储到Neo4j - 创建学习关系
        - 存储到Graphiti - 添加Episode
        - 返回episode_id

        ✅ Verified from docs/stories/30.8.story.md#AC-30.8.1:
        - 自动从canvas_path提取学科 (AC-30.8.2)
        - 使用group_id进行命名空间隔离 (AC-30.8.1)

        Args:
            user_id: 用户ID
            canvas_path: Canvas文件路径
            node_id: Canvas节点ID
            concept: 学习概念
            agent_type: 使用的Agent类型
            score: 得分 (0-100, optional)
            duration_seconds: 学习时长 (optional)
            subject: 学科名称 (可选，如不提供则自动推断)

        Returns:
            str: Episode ID

        [Source: docs/stories/22.4.story.md#record_learning_event]
        [Source: docs/stories/30.8.story.md#Task-3.1]
        """
        if not self._initialized:
            await self.initialize()

        # Story 30.10 AC-30.10.1: Deterministic episode ID (replaces uuid4)
        episode_id = _generate_deterministic_episode_id(
            user_id, canvas_path, node_id, concept
        )

        # ✅ AC-30.8.2: Auto-infer subject from canvas_path if not provided
        inferred_subject = subject or extract_subject_from_canvas_path(canvas_path)

        # ✅ AC-30.8.1: Build group_id for namespace isolation (Epic 6: canvas-scoped)
        canvas_name = extract_canvas_name(canvas_path)
        group_id = _vault_scoped_group_id(inferred_subject, canvas_name=canvas_name)

        try:
            # ✅ Verified: Store to Neo4j - Create learning relationship
            await self._create_neo4j_learning_relationship(
                user_id=user_id, concept=concept, score=score, group_id=group_id
            )

            # ✅ Verified: Store episode (simulating Graphiti add_learning_episode)
            content = f"User {user_id} learned '{concept}' using {agent_type}"
            if score is not None:
                content += f" with score {score}"

            episode = {
                "episode_id": episode_id,
                "content": content,
                "episode_type": "learning",
                "user_id": user_id,
                "canvas_path": canvas_path,
                "node_id": node_id,
                "concept": concept,
                "agent_type": agent_type,
                "score": score,
                "duration_seconds": duration_seconds,
                "timestamp": datetime.now().isoformat(),
                # ✅ Story 30.8: Subject isolation fields
                "subject": inferred_subject,
                "group_id": group_id,
            }
            # Story 30.10 AC-30.10.3: Dedup _episodes - skip if exists to preserve score history
            # Fix C4: changed from overwrite to skip-if-exists to not destroy FSRS score history
            existing_idx = next(
                (
                    i
                    for i, ep in enumerate(self._episodes)
                    if ep.get("episode_id") == episode_id
                ),
                None,
            )
            if existing_idx is not None:
                log_decision(
                    function="MemoryService.record_learning_event",
                    input_summary={"concept": concept, "episode_id": episode_id},
                    output="skipped_duplicate",
                    reason=f"episode already exists at idx={existing_idx}, preserving FSRS history",
                )
            else:
                self._episodes.append(episode)
                # Fix C5: Enforce MAX_EPISODE_CACHE to prevent unbounded memory growth
                if len(self._episodes) > self.MAX_EPISODE_CACHE:
                    self._episodes = self._episodes[-self.MAX_EPISODE_CACHE :]
                log_decision(
                    function="MemoryService.record_learning_event",
                    input_summary={
                        "concept": concept,
                        "agent": agent_type,
                        "canvas": canvas_name,
                    },
                    output=episode_id,
                    reason=f"new episode recorded, subject={inferred_subject}, group_id={group_id}",
                )

            # Phase 2: Enqueue to GraphitiEpisodeWorker for real add_episode
            score_text = f" (score: {score}/100)" if score is not None else ""
            self._enqueue_episode(
                name=f"learning:{concept[:80]}",
                episode_body=(
                    f"Student learned '{concept}' using {agent_type} agent on canvas "
                    f"'{canvas_path}'{score_text}. Node: {node_id}."
                ),
                group_id=group_id,
                source_description=f"canvas_learning:{inferred_subject}",
                entity_types=CANVAS_ENTITY_TYPES,
                edge_types=CANVAS_EDGE_TYPES,
            )

            return episode_id

        except Exception as e:
            logger.error(f"Failed to record learning event: {e}")
            raise

    async def get_learning_history(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        concept: Optional[str] = None,
        subject: Optional[str] = None,
        canvas_path: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """
        获取学习历史 (分页)

        ✅ Story 31.A.2 AC-31.A.2.1: 从Neo4j读取学习历史（替代只读内存）
        ✅ Verified from docs/stories/22.4.story.md#get_learning_history:
        - 从Neo4j查询时序数据
        - 应用concept过滤
        - 分页返回

        ✅ Verified from docs/stories/30.8.story.md#AC-30.8.3:
        - 支持`?subject=数学`查询参数过滤

        Args:
            user_id: 用户ID
            start_date: 开始日期 (optional)
            end_date: 结束日期 (optional)
            concept: 概念过滤 (optional)
            subject: 学科过滤 (optional) - AC-30.8.3
            canvas_path: Canvas file path for canvas-scoped filtering (Epic 6)
            page: 页码 (default: 1)
            page_size: 每页大小 (default: 50)

        Returns:
            Dict with items, total, page, page_size, pages

        [Source: docs/stories/31.A.2.story.md#AC-31.A.2.1]
        [Source: docs/stories/22.4.story.md#get_learning_history]
        [Source: docs/stories/30.8.story.md#Task-3.1]
        """
        if not self._initialized:
            await self.initialize()

        # ✅ Epic 6: Build canvas-scoped group_id when canvas_path is available
        if canvas_path:
            inferred_subject = subject or extract_subject_from_canvas_path(canvas_path)
            c_name = extract_canvas_name(canvas_path)
            group_id = _vault_scoped_group_id(inferred_subject, canvas_name=c_name)
        elif subject:
            group_id = _vault_scoped_group_id(subject)
        else:
            group_id = None

        # ✅ Story 31.A.2 AC-31.A.2.1: Query from Neo4j first (replaces memory-only read)
        episodes = []
        try:
            neo4j_results = await self.neo4j.get_learning_history(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                concept=concept,
                group_id=group_id,
                limit=page_size * page,  # Get enough data for pagination
            )
            episodes = neo4j_results or []
            logger.debug(
                f"Retrieved {len(episodes)} episodes from Neo4j for user {user_id}"
            )
        except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
            # ✅ Story 31.A.2: Fallback to memory if Neo4j fails
            logger.warning(f"Neo4j query failed, falling back to memory: {e}")

        # [Code Review C2 fix]: Always supplement Neo4j results with in-memory episodes.
        # Neo4j MERGE only keeps 1 LEARNED relationship per user+concept, so it returns
        # at most 1 record per concept. In-memory _episodes stores every score event via
        # append(), enabling consecutive_low tracking (which requires ≥3 scores).
        if not self._episodes_recovered:
            await self._recover_episodes_from_neo4j()

        memory_episodes = [e for e in self._episodes if e.get("user_id") == user_id]

        # FR-KG-04 fix: Apply group_id filter to in-memory episodes for canvas-scoped
        # isolation (Story 30.8 AC-30.8.1). Without this, when Neo4j is unavailable
        # and we fall back to in-memory _episodes, queries with canvas_path would
        # leak data from other canvases that share the same user_id.
        if group_id:
            memory_episodes = [
                e for e in memory_episodes if e.get("group_id", "") == group_id
            ]

        # Apply date filters to in-memory episodes
        # S34 Bug fix #3: Normalize both sides to str for consistent comparison
        # (Neo4j returns offset-aware DateTime, in-memory uses ISO strings)
        if start_date:
            start_str = (
                str(start_date.isoformat())
                if hasattr(start_date, "isoformat")
                else str(start_date)
            )
            memory_episodes = [
                e for e in memory_episodes if str(e.get("timestamp", "")) >= start_str
            ]
        if end_date:
            end_str = (
                str(end_date.isoformat())
                if hasattr(end_date, "isoformat")
                else str(end_date)
            )
            memory_episodes = [
                e for e in memory_episodes if str(e.get("timestamp", "")) <= end_str
            ]

        # Apply concept filter
        if concept:
            concept_lower = concept.lower()
            memory_episodes = [
                e
                for e in memory_episodes
                if concept_lower in e.get("concept", "").lower()
            ]

        # Apply subject filter
        if subject:
            subject_lower = subject.lower()
            memory_episodes = [
                e
                for e in memory_episodes
                if subject_lower in e.get("subject", "").lower()
            ]

        # Merge: deduplicate by (node_id, timestamp), prefer Neo4j (persistent)
        if memory_episodes:
            existing_keys = {
                (e.get("node_id", ""), e.get("timestamp", "")) for e in episodes
            }
            for me in memory_episodes:
                key = [REDACTED:env-cred]"node_id", ""), me.get("timestamp", ""))
                if key not in existing_keys:
                    episodes.append(me)
                    existing_keys.add(key)

        # Sort by timestamp (newest first)
        # Neo4j returns neo4j.time.DateTime objects, in-memory uses ISO strings;
        # str() normalizes both to sortable strings.
        if episodes:
            episodes.sort(key=[REDACTED:env-cred] x: str(x.get("timestamp", "")), reverse=True)

        # Story 38.6 AC-4: Merge failed scores from fallback so user never sees gaps
        # S34 Bug fix #1+#2: Filter by user_id and date range before merge
        failed_scores = await asyncio.to_thread(self.load_failed_scores)
        if failed_scores:
            # Bug fix #1: Filter by user_id (prevent cross-user data leakage)
            if user_id:
                failed_scores = [
                    fs for fs in failed_scores if fs.get("user_id", "") == user_id
                ]
            # Bug fix #2: Apply same date filters as memory_episodes
            if start_date:
                s_str = (
                    str(start_date.isoformat())
                    if hasattr(start_date, "isoformat")
                    else str(start_date)
                )
                failed_scores = [
                    fs for fs in failed_scores if str(fs.get("timestamp", "")) >= s_str
                ]
            if end_date:
                e_str = (
                    str(end_date.isoformat())
                    if hasattr(end_date, "isoformat")
                    else str(end_date)
                )
                failed_scores = [
                    fs for fs in failed_scores if str(fs.get("timestamp", "")) <= e_str
                ]
            # FR-KG-04 fix: Apply group_id filter to fallback failed_scores for
            # canvas-scoped isolation (Story 30.8 AC-30.8.1). Derive group_id from
            # canvas_name + inferred subject — failed_writes.jsonl historical entries
            # don't carry group_id directly, so we reconstruct it the same way the
            # write path does.
            if group_id:

                def _derive_group_id(fs: Dict[str, Any]) -> str:
                    canvas_name_field = fs.get("canvas_name", "") or ""
                    if not canvas_name_field:
                        return ""
                    inferred_subj = subject or extract_subject_from_canvas_path(
                        canvas_name_field
                    )
                    cn_only = extract_canvas_name(canvas_name_field)
                    return _vault_scoped_group_id(inferred_subj, canvas_name=cn_only)

                failed_scores = [
                    fs for fs in failed_scores if _derive_group_id(fs) == group_id
                ]
            # Deduplicate: only include fallback entries not already in episodes
            existing_keys = {
                (e.get("node_id", ""), e.get("timestamp", "")) for e in episodes
            }
            for fs in failed_scores:
                key = [REDACTED:env-cred]"node_id", ""), fs.get("timestamp", ""))
                if key not in existing_keys:
                    episodes.append(fs)
            # Re-sort after merge (str() normalizes DateTime vs string)
            episodes.sort(key=[REDACTED:env-cred] x: str(x.get("timestamp", "")), reverse=True)

        # Pagination
        total = len(episodes)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated = episodes[start_idx:end_idx]

        return {
            "items": paginated,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size if total > 0 else 0,
        }

    async def get_concept_history(
        self, concept_id: str, user_id: Optional[str] = None, limit: int = 50
    ) -> Dict[str, Any]:
        """
        查询概念学习历史

        ✅ Verified from AC-22.4.3: GET /api/v1/memory/concepts/{id}/history

        Args:
            concept_id: 概念ID
            user_id: 用户ID (optional)
            limit: 最大返回数量

        Returns:
            Dict with timeline data and score changes

        [Source: docs/stories/22.4.story.md#Dev-Notes]
        """
        if not self._initialized:
            await self.initialize()

        # Get history from Neo4j
        history = await self.neo4j.get_concept_history(
            concept_id=concept_id, user_id=user_id, limit=limit
        )

        # Format as timeline
        timeline = []
        for record in history:
            timeline.append(
                {
                    "timestamp": record.get("timestamp"),
                    "score": record.get("score"),
                    "user_id": record.get("user_id"),
                    "concept": record.get("concept"),
                    "review_count": record.get("review_count", 0),
                }
            )

        # Calculate score trend
        scores = [r.get("score") for r in timeline if r.get("score") is not None]
        score_trend = {
            "first": scores[-1] if scores else None,
            "last": scores[0] if scores else None,
            "average": sum(scores) / len(scores) if scores else None,
            "improvement": (scores[0] - scores[-1]) if len(scores) >= 2 else None,
        }

        return {
            "concept_id": concept_id,
            "timeline": timeline,
            "score_trend": score_trend,
            "total_reviews": len(timeline),
        }

    async def get_concept_score_history(
        self, concept_id: str, canvas_name: str, limit: int = 5
    ) -> ScoreHistoryResponse:
        """
        查询概念的历史得分 (最近N次)

        Story 31.5 AC-31.5.1: Query recent score records for difficulty adaptation.

        ✅ Task 2.1: get_concept_score_history(concept_id, canvas_name, limit=5)
        ✅ Task 2.2: Query Neo4j for recent N score records
        ✅ Task 2.3: Return format: {scores: int[], timestamps: datetime[], average: float}
        ✅ Task 2.4: Cache with 30 second TTL

        Args:
            concept_id: 概念/节点ID
            canvas_name: Canvas文件名
            limit: 返回的历史记录数量上限 (default: 5)

        Returns:
            ScoreHistoryResponse with scores, timestamps, average, sample_size

        [Source: docs/stories/31.5.story.md#Task-2]
        [Source: specs/data/score-history-response.schema.json]
        """
        if not self._initialized:
            await self.initialize()

        # Build cache key
        cache_key = [REDACTED:env-cred]"{concept_id}:{canvas_name}:{limit}"

        # NFR-P0: Check cache (TTLCache auto-evicts expired entries)
        cached_result = self._score_history_cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Score history cache hit for {concept_id}")
            return cached_result

        # NFR-P0: Double-check locking for cache stampede protection
        async with self._score_cache_lock:
            # Re-check after acquiring lock (another coroutine may have populated)
            cached_result = self._score_history_cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Score history cache hit (after lock) for {concept_id}")
                return cached_result

        # Query Neo4j for score history
        try:
            records = await self.neo4j.get_concept_score_history(
                concept_id=concept_id, canvas_name=canvas_name, limit=limit
            )

            # Extract scores and timestamps
            scores: List[int] = []
            timestamps: List[str] = []

            for record in records:
                score = record.get("score")
                ts = record.get("timestamp")
                if score is not None:
                    scores.append(int(score))
                    timestamps.append(str(ts) if ts else "")

            # Calculate average
            average = sum(scores) / len(scores) if scores else 0.0

            result = ScoreHistoryResponse(
                concept_id=concept_id,
                canvas_name=canvas_name,
                scores=scores,
                timestamps=timestamps,
                average=round(average, 2),
                sample_size=len(scores),
            )

            # Store in cache (TTLCache handles expiration automatically)
            self._score_history_cache[cache_key] = result

            logger.debug(
                f"Score history for {concept_id}: "
                f"{len(scores)} records, avg={average:.2f}"
            )

            return result

        except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
            logger.error(f"Failed to get score history for {concept_id}: {e}")
            # Return empty result on error (graceful degradation per ADR-009)
            return ScoreHistoryResponse(
                concept_id=concept_id,
                canvas_name=canvas_name,
                scores=[],
                timestamps=[],
                average=0.0,
                sample_size=0,
            )

    async def get_review_suggestions(
        self,
        user_id: str,
        limit: int = 10,
        subject: Optional[str] = None,
        canvas_path: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取复习建议 (基于艾宾浩斯遗忘曲线)

        查询Neo4j中next_review时间已过的概念

        ✅ Verified from docs/stories/22.4.story.md#get_review_suggestions:
        - 查询next_review < datetime()的概念
        - 添加优先级 (high if review_count < 3 else medium)
        - ORDER BY next_review

        ✅ Verified from docs/stories/30.8.story.md#AC-30.8.3:
        - 支持`?subject=数学`查询参数过滤

        Args:
            user_id: 用户ID
            limit: 返回数量 (default: 10)
            subject: 学科过滤 (optional) - AC-30.8.3
            canvas_path: Canvas file path for canvas-scoped filtering (Epic 6)

        Returns:
            List of review suggestions with priority

        [Source: docs/stories/22.4.story.md#get_review_suggestions]
        [Source: docs/stories/30.8.story.md#Task-3.1]
        """
        if not self._initialized:
            await self.initialize()

        # ✅ Epic 6: Build canvas-scoped group_id when canvas_path is available
        if canvas_path:
            inferred_subject = subject or extract_subject_from_canvas_path(canvas_path)
            c_name = extract_canvas_name(canvas_path)
            group_id = _vault_scoped_group_id(inferred_subject, canvas_name=c_name)
        elif subject:
            group_id = _vault_scoped_group_id(subject)
        else:
            group_id = None

        suggestions = await self.neo4j.get_review_suggestions(
            user_id=user_id, limit=limit, group_id=group_id
        )

        logger.debug(
            f"Retrieved {len(suggestions)} review suggestions for user {user_id} (subject={subject})"
        )
        return suggestions

    async def _create_neo4j_learning_relationship(
        self,
        user_id: str,
        concept: str,
        score: Optional[int] = None,
        group_id: Optional[str] = None,
    ) -> None:
        """
        在Neo4j中创建学习关系

        ✅ Verified from docs/stories/22.4.story.md#_create_neo4j_learning_relationship:
        - MERGE (u:User {id: $userId})
        - MERGE (c:Concept {name: $concept})
        - MERGE (u)-[r:LEARNED]->(c)
        - SET r.timestamp, r.score, r.next_review, r.group_id

        Args:
            user_id: 用户ID
            concept: 概念名称
            score: 得分 (optional)
            group_id: 科目隔离 group_id (optional, Story 30.8)

        [Source: docs/stories/22.4.story.md#_create_neo4j_learning_relationship]
        """
        await self.neo4j.create_learning_relationship(
            user_id=user_id, concept=concept, score=score, group_id=group_id
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        return {
            "initialized": self._initialized,
            "total_episodes": len(self._episodes),
            "neo4j_stats": self.neo4j.stats,
        }

    async def get_health_status(self) -> Dict[str, Any]:
        """
        获取3层记忆系统健康状态

        ✅ Verified from Story 30.3 AC-30.3.5:
        - 返回 Temporal (FSRS/SQLite) 层状态
        - 返回 Graphiti (Neo4j) 层状态
        - 返回 Semantic (LanceDB) 层状态
        - 整体状态: healthy/degraded/unhealthy

        Returns:
            Dict with status, layers, timestamp

        [Source: docs/stories/30.3.memory-api-health-endpoints.story.md#Task-1.2]
        """
        if not self._initialized:
            await self.initialize()

        layers = {
            "temporal": {"status": "ok", "backend": "sqlite"},
            "graphiti": {"status": "ok", "backend": "neo4j"},
            "semantic": {"status": "ok", "backend": "lancedb"},
        }

        # Check Graphiti/Neo4j layer
        # ✅ Story 30.3 Fix: Use correct stats fields (initialized, health_status)
        try:
            neo4j_stats = self.neo4j.stats
            is_connected = (
                neo4j_stats.get("initialized", False)
                and neo4j_stats.get("mode") == "NEO4J"
                and neo4j_stats.get("health_status", False)
            )
            if is_connected:
                layers["graphiti"]["node_count"] = neo4j_stats.get("node_count", 0)
            elif neo4j_stats.get("mode") == "JSON_FALLBACK":
                # JSON fallback mode - still considered operational
                layers["graphiti"]["status"] = "ok"
                layers["graphiti"]["backend"] = "json_fallback"
            else:
                layers["graphiti"]["status"] = "error"
                layers["graphiti"]["error"] = "Neo4j not connected"
        except (RuntimeError, AttributeError, KeyError) as e:
            layers["graphiti"]["status"] = "error"
            layers["graphiti"]["error"] = str(e)

        # Temporal layer (in-memory/SQLite simulation) - always ok for now
        layers["temporal"]["status"] = "ok"

        # Semantic layer (LanceDB) - check if available
        try:
            # For now, assume LanceDB is available if we can import it
            layers["semantic"]["status"] = "ok"
            layers["semantic"]["vector_count"] = 0  # Placeholder
        except (ImportError, RuntimeError) as e:
            layers["semantic"]["status"] = "error"
            layers["semantic"]["error"] = str(e)

        # Determine overall status
        error_count = sum(
            1 for layer in layers.values() if layer.get("status") == "error"
        )

        if error_count == 0:
            overall_status = "healthy"
        elif error_count < len(layers):
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"

        return {
            "status": overall_status,
            "layers": layers,
            "timestamp": datetime.now().isoformat(),
        }

    async def record_batch_learning_events(
        self, events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        批量记录学习事件 (真并行版)

        Story 30.10: 确定性 episode_id + 幂等去重
        Story 30.11: asyncio.gather 并行化 Neo4j 写入
        - AC-30.11.1: asyncio.gather + Semaphore 并行
        - AC-30.11.2: return_exceptions=True 部分失败隔离
        - AC-30.11.3: BATCH_NEO4J_CONCURRENCY 配置并发数
        - AC-30.11.4: 兼容 Story 30.10 幂等键
        - AC-30.11.5: 记录 batch_avg_latency_ms

        Args:
            events: List of event dictionaries

        Returns:
            Dict with success, processed, failed, errors, episode_ids, batch_avg_latency_ms, timestamp

        [Source: docs/stories/30.11.batch-true-parallel.story.md]
        """
        if not self._initialized:
            await self.initialize()

        batch_start = time.monotonic()

        # ── Phase 1: 预处理（同步，保护 _episodes 列表无竞态） ──
        processed = 0
        failed = 0
        errors: List[Dict[str, Any]] = []
        valid_records: List[Dict[str, Any]] = []
        episode_ids: List[str] = []

        for idx, event in enumerate(events):
            try:
                required_fields = ["event_type", "timestamp", "canvas_path", "node_id"]
                missing = [f for f in required_fields if f not in event]
                if missing:
                    raise ValueError(f"Missing required fields: {missing}")

                # Story 30.10 AC-30.10.4: Deterministic batch episode ID
                episode_id = _generate_batch_episode_id(
                    canvas_path=event["canvas_path"],
                    node_id=event["node_id"],
                    event_type=event["event_type"],
                    timestamp=event["timestamp"],
                )
                episode_record = {
                    "episode_id": episode_id,
                    "event_type": event["event_type"],
                    "timestamp": event["timestamp"],
                    "canvas_path": event["canvas_path"],
                    "node_id": event["node_id"],
                    "metadata": event.get("metadata", {}),
                }

                # Story 30.10 AC-30.10.3: Dedup batch episodes
                # Fix C4: skip-if-exists to preserve score history
                existing_idx = next(
                    (
                        i
                        for i, ep in enumerate(self._episodes)
                        if ep.get("episode_id") == episode_id
                    ),
                    None,
                )
                if existing_idx is not None:
                    logger.debug(f"Skipped duplicate batch episode: {episode_id}")
                else:
                    self._episodes.append(episode_record)
                    # Fix C5: Enforce MAX_EPISODE_CACHE
                    if len(self._episodes) > self.MAX_EPISODE_CACHE:
                        self._episodes = self._episodes[-self.MAX_EPISODE_CACHE :]

                neo4j_payload = {
                    "episode_id": episode_id,
                    "user_id": "batch_user",
                    "canvas_path": event["canvas_path"],
                    "node_id": event["node_id"],
                    "concept": event.get("metadata", {}).get(
                        "concept", event.get("metadata", {}).get("node_text", "unknown")
                    ),
                    "agent_type": event["event_type"],
                    "timestamp": event["timestamp"],
                }
                valid_records.append({"idx": idx, "payload": neo4j_payload})
                episode_ids.append(episode_id)
                processed += 1

            except (ValueError, KeyError, TypeError) as e:
                failed += 1
                errors.append({"index": idx, "error": str(e)})

        # ── Phase 2: 并行 Neo4j 写入 (Story 30.11 AC-30.11.1) ──
        neo4j_available = self.neo4j.stats.get("initialized", False)

        if neo4j_available and valid_records:
            concurrency = getattr(settings, "BATCH_NEO4J_CONCURRENCY", 10)
            semaphore = asyncio.Semaphore(concurrency)

            async def _write_single(record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
                async with semaphore:
                    try:
                        await self.neo4j.record_episode(record["payload"])
                        return None
                    except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
                        return {"index": record["idx"], "error": str(e)}

            results = await asyncio.gather(
                *[_write_single(r) for r in valid_records],
                return_exceptions=True,
            )

            neo4j_errors = []
            for r in results:
                if isinstance(r, Exception):
                    neo4j_errors.append({"error": str(r)})
                elif r is not None:
                    neo4j_errors.append(r)

            if neo4j_errors:
                logger.warning(
                    f"Batch Neo4j write: {len(neo4j_errors)} errors (non-blocking)"
                )
                # Fix C3: Surface Neo4j errors in response so caller knows about partial failures
                errors.extend(neo4j_errors)
                failed += len(neo4j_errors)
                # Story 30.24 AC-30.24.4: Track failed writes for shutdown safety
                for i, err in enumerate(neo4j_errors):
                    err_index = err.get("index")
                    if err_index is not None and err_index < len(episode_ids):
                        eid = episode_ids[err_index]
                    else:
                        eid = f"unknown_{i}"
                    self._pending_failed_writes.append(
                        {
                            "episode_id": eid,
                            "timestamp": datetime.now().isoformat(),
                            "reason": err.get("error", "unknown"),
                        }
                    )

        # ── Phase 2: Enqueue batch events to GraphitiEpisodeWorker ──
        for record in valid_records:
            p = record["payload"]
            concept = p.get("concept", "unknown")
            inferred_subject = extract_subject_from_canvas_path(p["canvas_path"])
            c_name = extract_canvas_name(p["canvas_path"])
            self._enqueue_episode(
                name=f"batch_learning:{concept[:80]}",
                episode_body=(
                    f"Student learned '{concept}' using {p.get('agent_type', 'unknown')} agent "
                    f"on canvas '{p['canvas_path']}'. Node: {p['node_id']}."
                ),
                group_id=_vault_scoped_group_id(inferred_subject, canvas_name=c_name),
                source_description=f"canvas_batch:{inferred_subject}",
            )

        # ── Phase 3: 性能指标 (Story 30.11 AC-30.11.5) ──
        elapsed_ms = (time.monotonic() - batch_start) * 1000
        avg_latency = elapsed_ms / len(events) if events else 0.0

        if not hasattr(self, "_batch_stats"):
            self._batch_stats = {}
        self._batch_stats["batch_avg_latency_ms"] = round(avg_latency, 2)
        self._batch_stats["last_batch_total_ms"] = round(elapsed_ms, 2)
        self._batch_stats["last_batch_size"] = len(events)

        logger.debug(
            f"Batch processed {processed} events in {elapsed_ms:.0f}ms "
            f"(parallel, concurrency={getattr(settings, 'BATCH_NEO4J_CONCURRENCY', 10)})"
        )

        return {
            "success": failed == 0,
            "processed": processed,
            "failed": failed,
            "errors": errors,
            "episode_ids": episode_ids,
            "batch_avg_latency_ms": round(avg_latency, 2),
            "timestamp": datetime.now().isoformat(),
        }

    async def record_knowledge_entity(
        self,
        event_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        group_id: Optional[str] = None,
        _from_recovery: bool = False,
    ) -> Dict[str, Any]:
        """
        Record a knowledge entity (tip or misconception) as an episode.

        Story 3.6: Tips annotation and error archiving.
        - Tips (event_type="learning_tip"): user-selected dialogue text
        - Misconceptions (event_type="misconception"): agent-detected errors

        Written to in-memory episode cache and Neo4j if connected.
        Uses the Graphiti bridge for Claude Code compatibility.

        Args:
            event_type: Entity type ("learning_tip" or "misconception").
            content: Human-readable summary of the entity.
            metadata: Structured data (tip_id/misconception_id, tags, etc.).
            group_id: Namespace group for subject isolation.

        Returns:
            dict: {"entity_id": str, "status": "written"|"enqueued"|"degraded"}.
            A7 (P2): status 诚实反映持久化结果 — written=结构化写入图,
            enqueued=进语义队列, degraded=worker 未就绪已落 outbox 待重放
            (调用方据此报告, 不再无条件 saved=True)。

            _from_recovery=True 时不重落 outbox (recover 重放路径, 避免重复堆积)。
        """
        if not self._initialized:
            await self.initialize()

        entity_id = f"{event_type}-{uuid.uuid4().hex[:16]}"
        resolved_group_id = group_id or DEFAULT_GROUP_ID
        meta = metadata or {}

        episode = {
            "episode_id": entity_id,
            "content": content,
            "episode_type": event_type,
            "node_id": meta.get("node_id", ""),
            "timestamp": datetime.now().isoformat(),
            "group_id": resolved_group_id,
            "metadata": meta,
        }

        self._episodes.append(episode)
        if len(self._episodes) > self.MAX_EPISODE_CACHE:
            self._episodes = self._episodes[-self.MAX_EPISODE_CACHE :]

        # ═══ GRAPHITI-NATIVE Phase 2 (2026-06-10) ═══════════════════════════
        # ① 删除 neo4j.record_episode 双写: 该路径实为 MERGE User-LEARNED-Concept,
        #    丢弃 tip 内容且污染 review 调度 (ChatGPT 对抗审查: G-FAKE 假写)。
        #    record_episode 方法本身保留 — batch_record_events/record_temporal_event
        #    等真实学习事件调用方仍用它。
        # ② 结构化 event (批注/错误/对话摘要) → graphiti_structured_writer 确定性写
        #    :Entity/RELATES_TO (主路径, 零 LLM, 检验白板可按 node_id 精确读)。
        #    非结构化 / graphiti 未就绪 / 缺 node_id / 写失败 → 原 add_episode
        #    队列 (语义通道 fallback, 数据不丢)。
        structured_written = False
        node_id_for_exam = meta.get("node_id", "")
        if node_id_for_exam:
            worker = get_episode_worker()
            graphiti = getattr(worker, "_graphiti", None)
            if graphiti is not None:
                from app.services.graphiti_structured_writer import (
                    write_callout,
                    write_conversation_summary,
                    write_error,
                    write_relation_reason,
                )

                # P3 (A4): valid_at = 真实源事件时间(客户端 source_timestamp =
                # 用户操作时刻), 非 now(=系统入图时间)。解析失败退 now。
                occurred = datetime.now(timezone.utc)
                _src_ts = meta.get("source_timestamp")
                if _src_ts:
                    try:
                        occurred = datetime.fromisoformat(
                            str(_src_ts).replace("Z", "+00:00")
                        )
                    except (ValueError, TypeError):
                        pass
                try:
                    if event_type in ("learning_tip", "callout_annotation"):
                        # 去重修复 (2026-06-13): 优先 meta['content'] (裸正文,
                        # 三通道一致) — content 参数可能带通道包装 ("Tip:…|" 等),
                        # 包装差异曾让同一批注三个指纹三条边。understanding 从
                        # meta 直取或解析 tags 列表 ("understanding:fuzzy")。
                        understanding = meta.get("understanding")
                        callout_type = meta.get("tag")
                        for t in meta.get("tags") or []:  # modal 把两者编进 tags 列表
                            s = str(t)
                            if not understanding and s.startswith("understanding:"):
                                understanding = s.split(":", 1)[1]
                            elif not callout_type and s.startswith("tag:"):
                                callout_type = s.split(":", 1)[1]
                        await write_callout(
                            graphiti.driver,
                            graphiti.embedder,
                            node_id=node_id_for_exam,
                            group_id=resolved_group_id,
                            callout_type=callout_type
                            or ("tip" if event_type == "learning_tip" else "note"),
                            text=meta.get("content") or content,
                            occurred_at=occurred,
                            understanding=understanding or None,
                            # P0 (A+-prime): 稳定身份, 即时上报与停笔回填同 id
                            annotation_id=meta.get("annotation_id") or None,
                        )
                        structured_written = True
                    elif event_type in (
                        "misconception",
                        "problem_trap",
                        "logical_fallacy",
                        "guided_thinking",
                    ):
                        await write_error(
                            graphiti.driver,
                            graphiti.embedder,
                            node_id=node_id_for_exam,
                            group_id=resolved_group_id,
                            error_type=meta.get("error_type", event_type),
                            description=content,
                            occurred_at=occurred,
                        )
                        structured_written = True
                    elif event_type == "conversation_archive":
                        await write_conversation_summary(
                            graphiti.driver,
                            graphiti.embedder,
                            node_id=node_id_for_exam,
                            group_id=resolved_group_id,
                            summary=meta.get("summary") or content,
                            occurred_at=occurred,
                        )
                        structured_written = True
                    elif event_type in ("node_derived", "wikilink_added"):
                        # P4 (X1): 派生关系原因实时入图 (非启动回填)。node_id_for_exam =
                        # 持有 frontmatter relationships 的派生节点(出边源), target = 源节点。
                        # 走 Graphiti-native write_relation_reason, 不走 CANVAS_EDGE 投影。
                        target = meta.get("target_node_id", "")
                        if target:
                            await write_relation_reason(
                                graphiti.driver,
                                graphiti.embedder,
                                source_node_id=node_id_for_exam,
                                target_node_id=target,
                                group_id=resolved_group_id,
                                relation_type=meta.get("relation_type"),
                                reason=meta.get("reason") or content,
                                occurred_at=occurred,
                            )
                            structured_written = True
                except Exception as e:  # noqa: BLE001 — 结构化失败退语义队列保数据
                    logger.warning(
                        f"[Graphiti-native] structured write failed for "
                        f"{event_type} (fallback to episode queue): {e}"
                    )
                    structured_written = False

        status = "written"
        if not structured_written:
            # 语义通道 (add_episode): 非结构化材料 / fallback。
            # P0-2a (2026-05-13): source_description 对齐 memory_format.py canonical。
            from app.core.memory_format import (
                entity_type_from_event,
                get_source_description,
            )

            canonical_entity_type = entity_type_from_event(event_type)
            canonical_source_desc = (
                get_source_description(canonical_entity_type)
                if canonical_entity_type
                else f"canvas_learning:{event_type}"
            )
            enqueued = self._enqueue_episode(
                name=f"{event_type}:{meta.get('title', content[:40])}",
                episode_body=content,
                group_id=resolved_group_id,
                source_description=canonical_source_desc,
                entity_types=CANVAS_ENTITY_TYPES,
                edge_types=CANVAS_EDGE_TYPES,
            )
            if enqueued:
                status = "enqueued"
            else:
                # A7 (P2): worker 未就绪 → 既不入图也未入队。诚实标 degraded +
                # 落 outbox 待重放, 不再静默返回成功。
                status = "degraded"
                if not _from_recovery:
                    self._record_structured_outbox(
                        {
                            "kind": "knowledge_entity",
                            "event_type": event_type,
                            "content": content,
                            "metadata": meta,
                            "group_id": resolved_group_id,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                    logger.warning(
                        "[A7] %s 未入图(worker未就绪), 已落 outbox 待重放: "
                        "id=%s node=%s",
                        event_type,
                        entity_id,
                        meta.get("node_id", ""),
                    )

        logger.info(
            f"[Story 3.6] Recorded {event_type}: id={entity_id} "
            f"group={resolved_group_id} status={status}"
        )
        return {"entity_id": entity_id, "status": status}

    async def find_episode_by_content_hash(
        self,
        node_id: str,
        content_hash: str,
        group_id: Optional[str] = None,
    ) -> bool:
        """Story 2.4 Plan B Phase 3 (2026-05-14): 幂等查询。

        Check if a callout with given content_hash already exists in Neo4j for
        the given node_id. Used by /api/v1/tips/batch to skip duplicates and
        avoid creating redundant Graphiti episodes when user re-saves the
        same file without changing callouts.

        Args:
            node_id: Canvas node id (file basename).
            content_hash: SHA256 hex of node_id|tag|understanding|content.
            group_id: Optional namespace filter.

        Returns:
            True if an EpisodicNode with this content_hash exists (skip),
            False if not (proceed to create new episode).
        """
        if not self._initialized:
            await self.initialize()

        try:
            from app.clients.neo4j_client import get_neo4j_client
            from app.graphiti.group_id_compat import to_physical_group_id

            client = get_neo4j_client()
            # T1 统一 (2026-07-10): 物理层单一 `__` 格式, 双格式 OR 查询退役
            physical_group_id = to_physical_group_id(group_id or DEFAULT_GROUP_ID)

            # P0-7 (2026-05-14): Graphiti 不持久化 metadata 到 EpisodicNode。
            # tips.py batch_sync 把 content_hash 内嵌为 [hash:abc123] 后缀写到
            # content 字段，这里用 CONTAINS 匹配前 16 hex chars。
            hash_marker = f"[hash:{content_hash[:16]}]"
            query = """
            MATCH (e:Episodic)
            WHERE e.group_id = $group_id
              AND e.source_description = 'callout-annotation-record'
              AND e.content CONTAINS $hash_marker
            RETURN count(e) AS cnt
            LIMIT 1
            """
            records = await client.run_query(
                query,
                group_id=physical_group_id,
                hash_marker=hash_marker,
            )
            for record in records or []:
                data = record if isinstance(record, dict) else record.data()
                cnt = data.get("cnt", 0)
                if cnt > 0:
                    return True
            return False
        except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
            logger.debug(
                f"[Story 2.4 batch] find_episode_by_content_hash failed (non-fatal): {e}"
            )
            # 失败时 fail-open — 允许 batch 继续（重复同步比丢失数据更可接受）
            return False

    # Search config recipe mapping: string name → SearchConfig object
    _SEARCH_RECIPES: Dict[
        str, Any
    ] = {}  # populated lazily to avoid import-time side effects

    @classmethod
    def _get_search_recipes(cls) -> Dict[str, Any]:
        """Lazily load search config recipes from graphiti_core."""
        if not cls._SEARCH_RECIPES:
            try:
                from graphiti_core.search.search_config_recipes import (
                    COMBINED_HYBRID_SEARCH_RRF,
                    COMBINED_HYBRID_SEARCH_CROSS_ENCODER,
                    EDGE_HYBRID_SEARCH_CROSS_ENCODER,
                    EDGE_HYBRID_SEARCH_RRF,
                    NODE_HYBRID_SEARCH_RRF,
                )

                # 批次1'④ (MEM-FLYWHEEL): MMR 配方注册 — Graphiti 白送的
                # 去重配方此前闲置 (审查「三个已付钱零收益」之三)
                from graphiti_core.search.search_config_recipes import (
                    COMBINED_HYBRID_SEARCH_MMR,
                    EDGE_HYBRID_SEARCH_MMR,
                    NODE_HYBRID_SEARCH_MMR,
                )

                cls._SEARCH_RECIPES = {
                    "combined_rrf": COMBINED_HYBRID_SEARCH_RRF,
                    "combined_cross_encoder": COMBINED_HYBRID_SEARCH_CROSS_ENCODER,
                    "combined_mmr": COMBINED_HYBRID_SEARCH_MMR,
                    "edge_cross_encoder": EDGE_HYBRID_SEARCH_CROSS_ENCODER,
                    "edge_rrf": EDGE_HYBRID_SEARCH_RRF,
                    "edge_mmr": EDGE_HYBRID_SEARCH_MMR,
                    "node_rrf": NODE_HYBRID_SEARCH_RRF,
                    "node_mmr": NODE_HYBRID_SEARCH_MMR,
                }
            except ImportError:
                logger.warning("graphiti_core search recipes not available")
        return cls._SEARCH_RECIPES

    async def _search_graphiti(
        self,
        query: str,
        group_id: Optional[str] = None,
        limit: int = 20,
        search_config: str = "combined_rrf",
        search_filter: Optional[Any] = None,
    ) -> List[Dict[str, Any]]:
        """Tier 1: Search via graphiti-core search_() with advanced recipes.

        Args:
            query: Search query string
            group_id: Optional group namespace for filtering
            limit: Max results to return
            search_config: Recipe name — one of 'combined_rrf', 'combined_cross_encoder',
                          'edge_cross_encoder', 'edge_rrf', 'node_rrf'
            search_filter: Optional SearchFilters instance for date/label/type filtering

        Returns:
            List of result dicts with 'relevance_score' from reranker scores.
        """
        worker = get_episode_worker()
        if not worker.is_ready or worker._graphiti is None:
            return list()  # worker not initialized yet

        # Resolve search config recipe
        recipes = self._get_search_recipes()
        config_obj = recipes.get(search_config)
        if config_obj is None:
            logger.warning(
                f"Unknown search config '{search_config}', falling back to combined_rrf"
            )
            config_obj = recipes.get("combined_rrf")

        # If recipes are unavailable (import failed), fall back to old search()
        if config_obj is None:
            return await self._search_graphiti_legacy(query, group_id, limit)

        try:
            # Override the limit in config
            from graphiti_core.search.search_config import SearchConfig

            # Create a copy with updated limit
            config_with_limit = config_obj.model_copy(update={"limit": limit})

            # P0-5 (2026-05-14): sanitize group_id at Graphiti boundary
            # M2 双图检索 (2026-07-13, 路线图 v2): 主图 + 语义影子图同查 —
            # 影子图只由 LLM 抽取通道写入 (semantic_group_id 服务端固定),
            # 读侧扩展让对话上下文能召回蒸馏产物的隐式关系 fact。
            from app.graphiti.group_id_compat import (
                sanitize_group_id_for_graphiti,
                semantic_group_id,
            )

            _gid_phys = sanitize_group_id_for_graphiti(group_id) if group_id else None
            # 批次1'④ (MEM-FLYWHEEL): punycode 白板级子组并入检索 — 中文白板名
            # 转码组 (vault__x__xn--*) 曾不在搜索范围, 组内 fact 逐字查不到
            # (审查实锤: q1 完美中文答案搁浅在 punycode 组)
            _search_groups = None
            if _gid_phys:
                _search_groups = [_gid_phys, semantic_group_id(_gid_phys)]
                _search_groups += await self._expand_vault_subgroups(_gid_phys)
            search_kwargs: Dict[str, Any] = {
                "query": query,
                "config": config_with_limit,
                "group_ids": _search_groups,
            }
            if search_filter is not None:
                search_kwargs["search_filter"] = search_filter

            results = await asyncio.wait_for(
                worker._graphiti.search_(**search_kwargs),
                timeout=3.0,
            )

            episodes: List[Dict[str, Any]] = []

            # Parse edges with reranker scores
            edges = getattr(results, "edges", []) or []
            edge_scores = getattr(results, "edge_reranker_scores", []) or []
            for i, edge in enumerate(edges):
                score = edge_scores[i] if i < len(edge_scores) else 0.0
                episodes.append(
                    {
                        "episode_id": getattr(edge, "uuid", ""),
                        "content": getattr(edge, "fact", ""),
                        "name": getattr(edge, "name", ""),
                        "episode_type": "graphiti_search",
                        "timestamp": (
                            getattr(edge, "created_at", datetime.now()).isoformat()
                            if hasattr(edge, "created_at")
                            else datetime.now().isoformat()
                        ),
                        "group_id": group_id or "",
                        "source": "graphiti",
                        "result_type": "edge",
                        "relevance_score": float(score),
                    }
                )

            # Parse nodes with reranker scores
            nodes = getattr(results, "nodes", []) or []
            node_scores = getattr(results, "node_reranker_scores", []) or []
            for i, node in enumerate(nodes):
                score = node_scores[i] if i < len(node_scores) else 0.0
                episodes.append(
                    {
                        "episode_id": getattr(node, "uuid", ""),
                        "content": getattr(node, "summary", "")
                        or getattr(node, "name", ""),
                        "name": getattr(node, "name", ""),
                        "episode_type": "graphiti_search",
                        "timestamp": (
                            getattr(node, "created_at", datetime.now()).isoformat()
                            if hasattr(node, "created_at")
                            else datetime.now().isoformat()
                        ),
                        "group_id": group_id or "",
                        "source": "graphiti",
                        "result_type": "node",
                        "relevance_score": float(score),
                    }
                )

            return episodes
        except (RuntimeError, asyncio.TimeoutError, AttributeError, TypeError) as e:
            logger.warning(f"Graphiti search_() failed or timed out: {e}")
            return list()

    async def _search_graphiti_legacy(
        self, query: str, group_id: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Legacy fallback: search via graphiti.search() when recipes unavailable."""
        worker = get_episode_worker()
        if not worker.is_ready or worker._graphiti is None:
            return list()
        try:
            # P0-5 (2026-05-14): sanitize group_id at Graphiti boundary
            # M2 双图检索 (2026-07-13): legacy 路径与 Tier1 保持同构 — 主图+影子图
            from app.graphiti.group_id_compat import (
                sanitize_group_id_for_graphiti,
                semantic_group_id,
            )

            _gid_phys = sanitize_group_id_for_graphiti(group_id) if group_id else None
            results = await asyncio.wait_for(
                worker._graphiti.search(
                    query=query,
                    group_ids=(
                        [_gid_phys, semantic_group_id(_gid_phys)] if _gid_phys else None
                    ),
                    num_results=limit,
                ),
                timeout=2.0,
            )
            episodes = []
            for r in results:
                episodes.append(
                    {
                        "episode_id": getattr(r, "uuid", ""),
                        "content": getattr(r, "fact", ""),
                        "name": getattr(r, "name", ""),
                        "episode_type": "graphiti_search",
                        "timestamp": (
                            getattr(r, "created_at", datetime.now()).isoformat()
                            if hasattr(r, "created_at")
                            else datetime.now().isoformat()
                        ),
                        "group_id": group_id or "",
                        "source": "graphiti",
                        "relevance_score": 0.5,  # default score for legacy results
                    }
                )
            return episodes
        except (RuntimeError, asyncio.TimeoutError, AttributeError) as e:
            logger.warning(f"Graphiti legacy search failed or timed out: {e}")
            return list()

    #: 批次1'④: 白板级子组枚举缓存 {前缀: (过期时间戳, 组列表)}
    _subgroup_cache: Dict[str, Any] = {}

    async def _expand_vault_subgroups(self, gid_phys: str) -> List[str]:
        """枚举 vault 物理组前缀下的白板级子组 (批次1'④, MEM-FLYWHEEL)。

        中文白板名经 punycode 转码后落在 vault__x__xn--* 子组; 此前搜索只查
        [vault 组, semantic 影子组], punycode 组内 fact 逐字查不到 (2026-07-22
        对抗审查实锤)。5 分钟 TTL 缓存; Neo4j 不可用时静默返回空 — 只影响
        扩展面, 不炸主检索。
        """
        import time as _time

        prefix = gid_phys + "__"
        cached = self._subgroup_cache.get(prefix)
        if cached and cached[0] > _time.time():
            return cached[1]
        groups: List[str] = []
        try:
            records = await self.neo4j.run_query(
                "MATCH (n) WHERE n.group_id STARTS WITH $prefix "
                "RETURN DISTINCT n.group_id AS gid LIMIT 50",
                prefix=prefix,
            )
            for rec in records or []:
                data = rec if isinstance(rec, dict) else rec.data()
                gid = str(data.get("gid") or "")
                if gid:
                    groups.append(gid)
        except Exception as e:  # noqa: BLE001 — 读侧扩展, 降级不炸
            logger.debug("[批次1'④] 子组枚举失败 (跳过扩展): %s", e)
        self._subgroup_cache[prefix] = (_time.time() + 300, groups)
        return groups

    @staticmethod
    def _dedupe_by_text(
        results: List[Dict[str, Any]], ratio: float = 0.92
    ) -> List[Dict[str, Any]]:
        """文本级近重去重 (批次1'④, MEM-FLYWHEEL): 保留分数最高条。

        dedup 只按 episode_id 收不掉不同 uuid 的近重边 (审查实测近重复率
        27%、5 对逐字节相同同屏)。入参须已按 relevance_score 降序 — 顺序
        遍历时后到的近重条即低分条, 直接丢弃。
        """
        import difflib

        kept: List[Dict[str, Any]] = []
        seen_norm: List[str] = []
        for r in results:
            text = "".join(
                unicodedata.normalize(
                    "NFKC", str(r.get("content") or r.get("name") or "")
                )
                .casefold()
                .split()
            )
            if text and any(
                difflib.SequenceMatcher(None, text, s).ratio() >= ratio
                for s in seen_norm
            ):
                continue
            if text:
                seen_norm.append(text)
            kept.append(r)
        return kept

    @staticmethod
    def _compute_unified_score(episode: Dict[str, Any], tier: int) -> float:
        """Compute a normalized relevance score for a search result.

        Normalizes scores across 3 search tiers to a 0.0-1.0 range so results
        can be sorted consistently regardless of source.

        Args:
            episode: Search result dict (may already have 'relevance_score' or 'score')
            tier: 1=graphiti (reranker score), 2=neo4j fulltext, 3=in-memory

        Returns:
            Normalized score in [0.0, 1.0]
        """
        if tier == 1:
            # Graphiti: reranker score is already 0.0-1.0
            return float(episode.get("relevance_score", 0.0))
        elif tier == 2:
            # Neo4j fulltext: raw Lucene score varies; normalize by capping at 10.0
            raw_score = float(episode.get("score", 0.0))
            return min(raw_score / 10.0, 1.0)
        else:
            # In-memory substring match: fixed baseline score
            return 0.1

    def _inject_fsrs_r_values(self, results: List[Dict[str, Any]]) -> None:
        """Inject FSRS retrievability values into search results as a reranking signal.

        For each result that has a 'concept' or 'name' field, attempts to look up
        the concept's FSRS R-value. Low R-value concepts (about to be forgotten)
        get up to 50% score boost to prioritize review-worthy material.

        Boost formula: final_score = relevance_score * (1.0 + (1.0 - r_value) * 0.5)

        Modifies results in-place. Graceful degradation: if MasteryEngine is
        unavailable or concept not found, the result is left unchanged.
        """
        try:
            from app.services.mastery_engine import get_mastery_engine

            engine = get_mastery_engine()
        except (ImportError, RuntimeError, Exception) as e:
            logger.debug(f"MasteryEngine unavailable for FSRS injection: {e}")
            return

        for result in results:
            concept_name = result.get("concept") or result.get("name")
            if not concept_name:
                continue
            try:
                # Build a minimal ConceptState for retrievability lookup.
                # MasteryEngine.get_retrievability needs a ConceptState with fsrs_card_data.
                # Without persisted card data, we skip — no crash.
                from app.models.mastery_state import ConceptState

                # Attempt to find existing concept state via engine's known concepts
                # This is best-effort — engine may not have this concept loaded
                concept_state = None
                if hasattr(engine, "_concept_cache") and isinstance(
                    engine._concept_cache, dict
                ):
                    concept_state = engine._concept_cache.get(concept_name)

                if concept_state is not None:
                    r_value = engine.get_retrievability(concept_state)
                    r_value = max(0.0, min(1.0, r_value))  # clamp to [0, 1]
                    result["fsrs_r_value"] = round(r_value, 4)

                    # Boost: low R-value concepts get higher final score
                    base_score = result.get("relevance_score", 0.0)
                    result["relevance_score"] = base_score * (
                        1.0 + (1.0 - r_value) * 0.5
                    )
            except (AttributeError, TypeError, ValueError, RuntimeError) as e:
                logger.debug(f"FSRS R-value lookup failed for '{concept_name}': {e}")
                continue

    async def _search_neo4j_fulltext(
        self, query: str, group_id: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Tier 2: Search via Neo4j fulltext index for keyword matches."""
        if not self.neo4j.stats.get("initialized", False):
            return list()  # Neo4j not connected

        try:
            cypher = """
            CALL db.index.fulltext.queryNodes('episode_content', $search_term)
            YIELD node, score
            WHERE ($group_id IS NULL OR node.group_id = $group_id)
            RETURN node, score
            ORDER BY score DESC
            LIMIT $limit
            """
            # MVP-α fix (2026-05-15): escape Lucene 特殊字符防 ParseException
            # 节点名含 ( ) [ ] 等会让 Lucene parser 抛 ClientError, 之前吞掉下游 fallback.
            import re

            safe_query = re.sub(r'([+\-!(){}\[\]^"~*?:\\/])', r"\\\1", query or "")
            safe_query = safe_query.replace("&&", r"\&\&").replace("||", r"\|\|")

            # T1 统一 (2026-07-10): episode 节点物理存 `__` 格式 — 冒号格式
            # 直查恒空 (Tier 2 断了两个月, Tier 1 降级时整条 search 静默空)。
            from app.graphiti.group_id_compat import to_physical_group_id

            records = await self.neo4j.run_query(
                cypher,
                search_term=safe_query,
                group_id=to_physical_group_id(group_id) if group_id else None,
                limit=limit,
            )
            from app.graphiti.group_id_compat import (
                desanitize_group_id_from_graphiti,
            )

            episodes = []
            for r in records if records else list():
                node = r["node"]
                episodes.append(
                    {
                        "episode_id": node.get("episode_id", ""),
                        "content": node.get("content", ""),
                        "episode_type": node.get("episode_type", ""),
                        "score": r.get("score", 0.0),
                        "timestamp": node.get("timestamp", ""),
                        # T1: 物理 `__` → 对外 D16 冒号 (与 Tier 1/3 输出一致)
                        "group_id": desanitize_group_id_from_graphiti(
                            node.get("group_id", "")
                        ),
                        "node_id": node.get("node_id", ""),
                        "source": "neo4j_fulltext",
                    }
                )
            return episodes
        except (
            RuntimeError,
            ConnectionError,
            asyncio.TimeoutError,
            neo4j.exceptions.ClientError,  # MVP-α fix: Lucene ParseException
            neo4j.exceptions.Neo4jError,
        ) as e:
            logger.debug(f"Neo4j fulltext search failed (non-fatal): {e}")
            return list()  # fulltext index may not exist yet

    async def search_memories(
        self,
        query: str,
        group_id: Optional[str] = None,
        max_results: int = 50,
        limit: Optional[int] = None,
        search_config: str = "combined_rrf",
        search_filter: Optional[Any] = None,
        # 批次1'④ 地板取 0.05: bge-reranker 跨语弱相关落在 0.05-0.2 区间
        # (0.2 实测误杀 mem-05/15/24, recall@5 -9pt); 假阳性防护主要靠
        # cross_encoder 区分度, 地板只砍趋零噪音
        min_relevance: float = 0.05,
    ) -> List[Dict[str, Any]]:
        """
        Search learning memories using 3-tier layered search with unified scoring.

        Phase 2: Upgraded with search_() recipes, unified relevance scoring,
        and FSRS R-value injection for reranking.

        Tier 1: Graphiti search_() with configurable recipes (reranker scores)
        Tier 2: Neo4j fulltext index (Lucene scores normalized to 0-1)
        Tier 3: In-memory cache (fixed 0.1 baseline score)

        Results merged, deduplicated, scored uniformly, boosted by FSRS R-value,
        and sorted by relevance_score descending.

        Args:
            query: Search query string
            group_id: Optional group namespace for filtering
            max_results: Maximum results to return (default 50)
            limit: Override for max_results (backward compat)
            search_config: Recipe name for Graphiti search_ ('combined_rrf', etc.)
            search_filter: Optional SearchFilters for date/label filtering

        Signature backward-compatible — existing callers unaffected.
        """
        if not self._initialized:
            await self.initialize()

        # 批次4' 检索束 (MEM-FLYWHEEL): query 命中双语术语表 → 拼接对侧语言
        # 术语束再检索 — 跨语/短词多义场景 (「极小极大」→ minimax) 召回稳态化
        from app.core.term_aliases import expand_query

        query = expand_query(query)

        effective_limit = limit if limit is not None else max_results
        seen_ids: set = set()
        merged: List[Dict[str, Any]] = []

        # Tier 1: Graphiti semantic search via search_()
        graphiti_hits = await self._search_graphiti(
            query,
            group_id,
            effective_limit,
            search_config=search_config,
            search_filter=search_filter,
        )
        for ep in graphiti_hits:
            ep_id = ep.get("episode_id", "")
            if ep_id and ep_id not in seen_ids:
                seen_ids.add(ep_id)
                # Tier 1 results already have relevance_score from reranker
                ep["relevance_score"] = self._compute_unified_score(ep, tier=1)
                merged.append(ep)

        # Tier 2: Neo4j fulltext search
        neo4j_hits = await self._search_neo4j_fulltext(query, group_id, effective_limit)
        for ep in neo4j_hits:
            ep_id = ep.get("episode_id", "")
            if ep_id and ep_id not in seen_ids:
                seen_ids.add(ep_id)
                ep["relevance_score"] = self._compute_unified_score(ep, tier=2)
                merged.append(ep)

        # Tier 3: In-memory cache (always available fallback)
        tier3_count = 0
        query_lower = query.lower()
        for episode in reversed(self._episodes):
            if len(merged) >= effective_limit:
                break
            if group_id and episode.get("group_id", "") != group_id:
                continue
            ep_id = episode.get("episode_id", "")
            if ep_id in seen_ids:
                continue
            searchable = " ".join(
                str(episode.get(field, ""))
                for field in ("content", "episode_type", "node_id", "concept")
            ).lower()
            if query_lower in searchable:
                seen_ids.add(ep_id)
                episode_with_source = {**episode, "source": "in_memory"}
                episode_with_source["relevance_score"] = self._compute_unified_score(
                    episode_with_source, tier=3
                )
                merged.append(episode_with_source)
                tier3_count += 1

        # FSRS R-value injection: boost low-retrievability concepts
        self._inject_fsrs_r_values(merged)

        # Sort by relevance_score descending (unified across all tiers)
        merged.sort(key=[REDACTED:env-cred] x: x.get("relevance_score", 0.0), reverse=True)

        # 批次1'④ (MEM-FLYWHEEL): 文本级近重去重 (跨 Tier, 收不同 uuid 近重边)
        pre_dedupe = len(merged)
        merged = self._dedupe_by_text(merged)

        # 批次1'④ (MEM-FLYWHEEL): 相关度地板 — 低于阈值宁可空 (假阳性满编
        # 止血一阶手段)。Tier1/2 全空的降级场景跳过地板, 保留 Tier3 内存兜底。
        if min_relevance > 0 and (graphiti_hits or neo4j_hits):
            merged = [
                r for r in merged if r.get("relevance_score", 0.0) >= min_relevance
            ]

        # Epic 4 Feature 4.2: Log which tier(s) produced results
        logger.info(
            f"[search_memories] Tier 1: {len(graphiti_hits)} results, "
            f"Tier 2: {len(neo4j_hits)} results, "
            f"Tier 3: {tier3_count} results "
            f"(deduped {pre_dedupe - len(merged) if pre_dedupe > len(merged) else 0}, "
            f"floor={min_relevance}, returned {len(merged[:effective_limit])})"
        )

        return merged[:effective_limit]

    async def search_error_memories(
        self,
        node_id: str,
        group_id: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """检索节点的历史误解/错误记录 (Story 2.3 消费方契约, 批次2' 线3 补齐)。

        chat.py /enrich-context 与 chat_context_assembler 自 2026-05-13 起调用
        此方法, 但方法本体从未实现 — 现网 500 (BUG-32DB6194, G-PIPE 实例)。
        实现: search_memories 三层融合定向查询 + 错误信号过滤, 映射为
        assembler._format_historical_errors 消费的 error_record schema
        (error_type / description / corrected_at / tags / source_session)。
        """
        hits = await self.search_memories(
            query=f"{node_id} 错误 误解 mistake misconception",
            group_id=group_id,
            max_results=max(limit * 4, 20),
        )
        markers = (
            "error",
            "mistake",
            "misconception",
            "错误",
            "误解",
            "混淆",
            "纠正",
        )
        records: List[Dict[str, Any]] = []
        for h in hits:
            text = " ".join(
                str(h.get(k, "")) for k in ("content", "name", "episode_type")
            ).lower()
            if not any(m in text for m in markers):
                continue
            records.append(
                {
                    "error_type": h.get("episode_type") or "learning_error",
                    "description": str(h.get("content") or "")[:500],
                    "corrected_at": str(h.get("timestamp") or ""),
                    "tags": [],
                    "source_session": str(h.get("group_id") or ""),
                    "_episode_id": str(h.get("episode_id") or ""),
                    "_node_id": node_id,
                }
            )
            if len(records) >= limit:
                break
        return records

    async def record_temporal_event(
        self,
        event_type: str,
        session_id: str,
        canvas_path: str,
        node_id: Optional[str] = None,
        edge_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        记录时序事件到Neo4j Temporal Memory

        Story 30.5: Canvas CRUD Operations Memory Trigger
        - AC-30.5.1: node_created 事件
        - AC-30.5.2: edge_created 事件
        - AC-30.5.3: node_updated 事件

        Args:
            event_type: 事件类型 (node_created, node_updated, edge_created)
            session_id: 会话ID
            canvas_path: Canvas文件路径
            node_id: 节点ID (可选)
            edge_id: 边ID (可选)
            metadata: 事件元数据 (可选)

        Returns:
            str: Episode ID

        [Source: specs/data/temporal-event.schema.json]
        [Source: docs/stories/30.5.story.md#AC-30.5.1]
        """
        if not self._initialized:
            await self.initialize()

        import uuid

        event_id = f"event-{uuid.uuid4().hex[:16]}"

        # Build episode record following temporal-event.schema.json
        episode_record = {
            "event_id": event_id,
            "session_id": session_id,
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "canvas_path": canvas_path,
            "node_id": node_id,
            "edge_id": edge_id,
            "metadata": metadata or {},
        }

        # Store in memory
        self._episodes.append(episode_record)
        # Fix C5: Enforce MAX_EPISODE_CACHE
        if len(self._episodes) > self.MAX_EPISODE_CACHE:
            self._episodes = self._episodes[-self.MAX_EPISODE_CACHE :]

        # Try to store in Neo4j if connected
        if self.neo4j.stats.get("initialized", False):
            try:
                await self.neo4j.record_episode(
                    {
                        "episode_id": event_id,
                        "user_id": session_id,
                        "canvas_path": canvas_path,
                        "node_id": node_id or "",
                        "concept": metadata.get("node_text", "") if metadata else "",
                        "agent_type": event_type,
                        "timestamp": episode_record["timestamp"],
                    }
                )

                # Story 30.5 AC-30.5.4: Create Canvas-Concept relationship graph
                if event_type in ("node_created", "node_updated") and node_id:
                    await self.neo4j.create_canvas_node_relationship(
                        canvas_path=canvas_path,
                        node_id=node_id,
                        node_text=metadata.get("node_text") if metadata else None,
                    )
                elif event_type == "edge_created" and edge_id:
                    from_node = metadata.get("from_node") if metadata else None
                    to_node = metadata.get("to_node") if metadata else None
                    if from_node and to_node:
                        await self.neo4j.create_edge_relationship(
                            canvas_path=canvas_path,
                            edge_id=edge_id,
                            from_node_id=from_node,
                            to_node_id=to_node,
                            edge_label=metadata.get("edge_label") if metadata else None,
                        )

            except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
                # Silent degradation - log but don't raise
                logger.warning(f"Neo4j write failed for temporal event: {e}")

        logger.debug(f"Recorded temporal event: {event_type} for {canvas_path}")

        # Phase 2: Enqueue temporal event to GraphitiEpisodeWorker
        concept = ""
        if metadata:
            concept = metadata.get("node_text", "") or metadata.get("concept", "")
        if not concept:
            concept = f"{event_type}:{node_id or edge_id or 'unknown'}"
        inferred_subject = extract_subject_from_canvas_path(canvas_path)
        c_name = extract_canvas_name(canvas_path)
        self._enqueue_episode(
            name=f"temporal:{event_type}:{concept[:60]}",
            episode_body=(
                f"Canvas event '{event_type}' on path '{canvas_path}'. "
                f"Node: {node_id or edge_id or 'unknown'}. Concept: {concept}."
            ),
            group_id=_vault_scoped_group_id(inferred_subject, canvas_name=c_name),
            source_description=f"canvas_temporal:{event_type}",
        )

        return event_id

    # ═══════════════════════════════════════════════════════════════════════════════
    # Story 38.6: Failed Write Recovery & Merged View
    # ═══════════════════════════════════════════════════════════════════════════════

    async def recover_failed_writes(self) -> Dict[str, int]:
        """
        .. deprecated:: Story 38.8
            Replaced by ``FallbackSyncService.sync_all_fallbacks()`` which handles
            all three fallback files with checkpoint support and conflict resolution.
            This method is retained for backward compatibility but is no longer
            called from the startup lifespan. See ``fallback_sync_service.py``.

        Story 38.6 AC-3: Replay failed writes from data/failed_writes.jsonl on startup.

        Reads each entry, attempts to re-record it. Successfully replayed entries
        are removed; still-failing entries remain in the file.

        Uses failed_writes_lock to avoid racing with _record_failed_write.

        Returns:
            dict with 'recovered' and 'pending' counts
        """
        if not FAILED_WRITES_FILE.exists():
            return {"recovered": 0, "pending": 0}

        # Acquire shared lock to prevent _record_failed_write from appending
        # while we read + rewrite the file (fixes #1 race condition).
        with failed_writes_lock:
            try:
                lines = (
                    FAILED_WRITES_FILE.read_text(encoding="utf-8").strip().splitlines()
                )
            except (OSError, UnicodeDecodeError) as e:
                logger.warning(f"[Story 38.6] Failed to read fallback file: {e}")
                return {"recovered": 0, "pending": 0}

        if not lines:
            return {"recovered": 0, "pending": 0}

        recovered = 0
        still_pending = []

        for line in lines:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                logger.warning("[Story 38.6] Skipping malformed fallback entry")
                still_pending.append(
                    line
                )  # preserve malformed lines to avoid data loss
                continue

            try:
                # A7 (P2): 结构化条目 (callout/error/relation/对话) → 重走
                # record_knowledge_entity 的结构化写入 (启动时 worker 通常已就绪)。
                # _from_recovery=True 防止再次失败时重复落 outbox。
                if entry.get("kind") == "knowledge_entity":
                    result = await self.record_knowledge_entity(
                        event_type=entry.get("event_type", ""),
                        content=entry.get("content", ""),
                        metadata=entry.get("metadata"),
                        group_id=entry.get("group_id"),
                        _from_recovery=True,
                    )
                    if result.get("status") in ("written", "enqueued"):
                        recovered += 1
                    else:
                        still_pending.append(line)
                    continue

                # Phase 2: Enqueue recovered entry to GraphitiEpisodeWorker
                concept = entry.get("concept", "") or entry.get("concept_id", "unknown")
                entry_canvas = entry.get("canvas_name", "")
                inferred_subject = extract_subject_from_canvas_path(entry_canvas)
                c_name = extract_canvas_name(entry_canvas)
                enqueued = self._enqueue_episode(
                    name=f"recovery:{concept[:80]}",
                    episode_body=(
                        f"Recovered learning event for concept '{concept}' "
                        f"on canvas '{entry_canvas}'."
                    ),
                    group_id=_vault_scoped_group_id(
                        inferred_subject, canvas_name=c_name
                    ),
                    source_description="canvas_recovery",
                )
                if enqueued:
                    recovered += 1
                else:
                    still_pending.append(line)
            except (RuntimeError, asyncio.TimeoutError):
                still_pending.append(line)

        # Rewrite file with only still-pending entries under lock
        with failed_writes_lock:
            try:
                if still_pending:
                    tmp_file = FAILED_WRITES_FILE.with_suffix(".tmp")
                    tmp_file.write_text(
                        "\n".join(still_pending) + "\n", encoding="utf-8"
                    )
                    # Windows-safe replace: retry on PermissionError (#2)
                    for attempt in range(3):
                        try:
                            tmp_file.replace(FAILED_WRITES_FILE)
                            break
                        except PermissionError:
                            if attempt < 2:
                                import time as _time

                                _time.sleep(0.1)
                            else:
                                raise
                else:
                    FAILED_WRITES_FILE.unlink(missing_ok=True)
            except (OSError, PermissionError) as e:
                logger.warning(f"[Story 38.6] Failed to update fallback file: {e}")

        logger.info(
            f"[Story 38.6] Recovered {recovered} failed writes, {len(still_pending)} still pending"
        )
        return {"recovered": recovered, "pending": len(still_pending)}

    def load_failed_scores(self) -> List[Dict[str, Any]]:
        """
        Story 38.6 AC-4: Load scoring entries from failed_writes.jsonl for merged view.

        Returns list of dicts that can be merged into learning history results,
        so the user never sees a "missing score" gap.

        Uses failed_writes_lock to avoid reading a partially-written line.
        """
        if not FAILED_WRITES_FILE.exists():
            return []

        results = []
        try:
            with failed_writes_lock:
                lines = (
                    FAILED_WRITES_FILE.read_text(encoding="utf-8").strip().splitlines()
                )
            for line in lines:
                try:
                    entry = json.loads(line)
                    results.append(
                        {
                            "timestamp": entry.get("timestamp", ""),
                            "canvas_name": entry.get("canvas_name", ""),
                            "node_id": entry.get("concept_id", ""),
                            "concept": entry.get("concept", "")
                            or entry.get("concept_id", ""),
                            "score": entry.get("score"),
                            "user_id": entry.get(
                                "user_id", ""
                            ),  # S34 fix: include for filtering
                            "source": "fallback",
                            "error_reason": entry.get("error_reason", ""),
                        }
                    )
                except json.JSONDecodeError:
                    continue
        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"[Story 38.6] Failed to load failed scores: {e}")

        return results

    async def cleanup(self) -> None:
        """
        Cleanup local MemoryService state.

        IMPORTANT: Does NOT cleanup the shared Neo4j driver, because Neo4jClient
        is a shared singleton used by multiple services. Neo4j cleanup is handled
        separately at application shutdown via cleanup_memory_service().

        Story 30.24 AC-30.24.4: Flushes pending failed writes to
        failed_writes.jsonl before clearing state, so no data is silently lost.

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#依赖注入设计]
        """
        # Story 30.24 AC-30.24.4: Flush pending failed writes before cleanup
        if self._pending_failed_writes:
            self._flush_pending_failed_writes()

        self._initialized = False
        self._episodes.clear()
        self._score_history_cache.clear()
        self._episodes_recovered = False
        logger.debug("MemoryService local state cleanup completed")

    def _flush_pending_failed_writes(self) -> None:
        """
        Story 30.24 AC-30.24.4: Persist pending batch write failures to
        data/failed_writes.jsonl so they survive shutdown.

        Thread-safe via failed_writes_lock (shared with agent_service).

        Note: This is a synchronous method called from async cleanup().
        Safe in single-threaded asyncio (no await between iteration and clear).
        If cleanup() is ever called from a signal handler thread, consider
        wrapping _pending_failed_writes access with an asyncio.Lock.
        """
        if not self._pending_failed_writes:
            return

        try:
            FAILED_WRITES_FILE.parent.mkdir(parents=True, exist_ok=True)
            with failed_writes_lock:
                with open(FAILED_WRITES_FILE, "a", encoding="utf-8") as f:
                    for entry in self._pending_failed_writes:
                        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            logger.warning(
                f"[Story 30.24] Flushed {len(self._pending_failed_writes)} "
                f"pending failed writes to {FAILED_WRITES_FILE}"
            )
        except (OSError, TypeError, ValueError) as e:
            logger.error(f"[Story 30.24] Failed to flush pending writes: {e}")
        finally:
            self._pending_failed_writes.clear()


# Singleton instance — the ONLY MemoryService singleton entry point for the entire project.
# All modules (endpoints, dependencies, main) MUST import from here.
_memory_service_instance: Optional[MemoryService] = None
_memory_service_lock: asyncio.Lock = asyncio.Lock()


async def get_memory_service() -> MemoryService:
    """
    Get or create MemoryService singleton (async, auto-initializes).

    This is the single canonical entry point for MemoryService across the
    entire application. All modules (memory endpoints, agent endpoints,
    dependencies, main) MUST use this function.

    Uses asyncio.Lock to prevent race conditions when multiple coroutines
    call this concurrently during startup.

    Returns:
        MemoryService: Initialized singleton instance
    """
    global _memory_service_instance

    # Fast path: already initialized
    if _memory_service_instance is not None and _memory_service_instance._initialized:
        return _memory_service_instance

    # Slow path: acquire lock for safe initialization
    async with _memory_service_lock:
        # Double-check after acquiring lock
        if (
            _memory_service_instance is not None
            and _memory_service_instance._initialized
        ):
            return _memory_service_instance

        if _memory_service_instance is None:
            logger.info("Creating MemoryService singleton instance")
            _memory_service_instance = MemoryService()

        if not _memory_service_instance._initialized:
            await _memory_service_instance.initialize()
            logger.info("MemoryService singleton initialized")

    return _memory_service_instance


async def cleanup_memory_service() -> None:
    """
    Cleanup MemoryService singleton — called on application shutdown.

    This is the ONLY place that cleans up the shared Neo4j driver,
    since MemoryService.cleanup() only clears local state.
    """
    global _memory_service_instance
    if _memory_service_instance is not None:
        # First cleanup local MemoryService state
        await _memory_service_instance.cleanup()
        # Then cleanup the shared Neo4j driver (only at app shutdown)
        try:
            await _memory_service_instance.neo4j.cleanup()
            logger.info("Neo4j driver cleaned up during shutdown")
        except (RuntimeError, ConnectionError, OSError) as e:
            logger.warning(f"Neo4j driver cleanup failed: {e}")
        _memory_service_instance = None
        logger.info("MemoryService singleton cleaned up")


def reset_memory_service() -> None:
    """Reset singleton instance (for testing only)."""
    global _memory_service_instance
    _memory_service_instance = None
````
