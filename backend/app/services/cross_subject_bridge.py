# Canvas Learning System - Cross-Subject Bridge Service
# Story 1.9: Tag Jaccard bridging for cross-subject retrieval (AC-5)
"""
Computes Tag Jaccard similarity between subjects to determine
which subjects should be included in cross-subject search.

Jaccard(A, B) = |A intersection B| / |A union B|
Tags source: node keywords, frontmatter tags.

P0-SYNC-ISO-2026-08-17 R10 (外部审查 P1-06) — vault 隔离口径:
本服务是 **vault 内跨 subject** 桥, 不是跨 vault 桥。「跨 subject」指同一
vault 里不同学科之间的 Tag Jaccard 扩展 (Story 1.9 AC-5 的设计意图即
单用户单库多学科)。因此两条 Neo4j 读查询都必须按 vault 前缀过滤
(group_id = vault 根 OR STARTS WITH vault 根 + "__"), 否则:
- 候选 subject 列表混入其他 vault 的学科;
- 同名 subjectId (如两个 vault 都有 "math") 的 tag 集互相污染,
  Jaccard 在脏集合上计算 → 检索面跨 vault 泄漏。

[Source: _bmad-output/implementation-artifacts/1-9-multi-subject-kg-isolation.md#Task 7]
"""

import asyncio
import logging
from typing import Dict, List, Set, Tuple

import structlog

logger = structlog.get_logger(__name__)


def _physical_vault_scope(group_id: str = "") -> Tuple[str, str]:
    """P0-SYNC-ISO-2026-08-17 R10: 读侧 vault 隔离范围 (物理格式).

    Args:
        group_id: 逻辑 D16 group_id (``vault:x[:sub]``); 空则兜底读
            ``get_current_subject_id()`` ContextVar (命名是历史误导 —
            实际存的是 endpoint 层 resolve_vault_group_id 注入的 group_id)。

    Returns:
        (vault_group, vault_prefix) 二元组:
          vault_group  — 物理 vault 根组 (如 ``vault__cs_61b``), ``=`` 匹配
          vault_prefix — ``vault_group + "__"``, ``STARTS WITH`` 匹配二级子组

    绑定 Neo4j 前必过 ``to_physical_group_id`` (T1 契约: 物理存储是
    ``vault__`` 双下划线, 逻辑冒号格式直接绑定 = 假过滤)。跨 subject 桥按
    vault 根 (前两段) 过滤而非全量 group — 全量精确匹配会把本 vault 其他
    subject 的二级子组也挡掉, 违背本服务的跨 subject 设计意图。
    ``=`` 与 ``STARTS WITH prefix+"__"`` 并用防前缀撞名
    (``vault__a`` 不得命中 ``vault__a2``)。
    """
    from app.core.subject_config import get_current_subject_id
    from app.graphiti.group_id_compat import to_physical_group_id

    logical = group_id if group_id and group_id.strip() else get_current_subject_id()
    physical = to_physical_group_id(logical)
    segments = physical.split("__")
    vault_group = "__".join(segments[:2]) if len(segments) >= 2 else physical
    return vault_group, vault_group + "__"


def compute_tag_jaccard(tags_a: Set[str], tags_b: Set[str]) -> float:
    """
    Compute Jaccard similarity between two tag sets.

    Args:
        tags_a: Tag set for subject A.
        tags_b: Tag set for subject B.

    Returns:
        Jaccard coefficient (0.0 to 1.0).
    """
    if not tags_a and not tags_b:
        return 0.0
    intersection = tags_a & tags_b
    union = tags_a | tags_b
    if len(union) == 0:
        return 0.0
    return len(intersection) / len(union)


async def find_related_subjects(
    current_subject_id: str,
    all_subject_tags: Dict[str, Set[str]],
    threshold: float = 0.3,
) -> List[str]:
    """
    Find subjects related to the current one by Tag Jaccard similarity.

    Args:
        current_subject_id: The active subject.
        all_subject_tags: Mapping of subject_id -> set of tags.
        threshold: Minimum Jaccard coefficient to consider related (default 0.3).

    Returns:
        List of subject_ids that exceed the threshold.
    """
    current_tags = all_subject_tags.get(current_subject_id, set())
    if not current_tags:
        # No tags for current subject => no similarity can be computed
        empty: List[str] = []
        return empty

    related: List[str] = []  # ruff C408: use literal
    for subject_id, tags in all_subject_tags.items():
        if subject_id == current_subject_id:
            continue
        similarity = compute_tag_jaccard(current_tags, tags)
        if similarity >= threshold:
            related.append(subject_id)
            logger.debug(
                f"Cross-subject bridge: {current_subject_id} <-> {subject_id} "
                f"Jaccard={similarity:.3f} (threshold={threshold})"
            )

    return related


async def expand_search_subjects(
    current_subject_id: str,
    neo4j_driver: object,
    threshold: float = 0.3,
    group_id: str = "",
) -> List[str]:
    """
    Expand the search scope to include related subjects via Tag Jaccard.

    Called when ``cross_subject=True`` in a RAG query.  Fetches tags for
    all subjects **within the current vault** from Neo4j, computes Jaccard
    similarity against the current subject, and returns a list that
    includes the current subject plus any related subjects exceeding the
    threshold.

    Args:
        current_subject_id: The subject the user is currently working in.
        neo4j_driver: Async Neo4j driver for tag extraction.
        threshold: Minimum Jaccard coefficient to include a subject.
        group_id: Optional logical D16 group_id (``vault:x[:sub]``) pinning
            the vault scope; empty falls back to the request ContextVar
            (see ``_physical_vault_scope``).

    Returns:
        List of subject_ids to search (always includes *current_subject_id*).
    """
    vault_group, vault_prefix = _physical_vault_scope(group_id)

    # 1. Fetch candidate subjects present in THIS vault.
    #
    # P0-SYNC-ISO R10: 旧实现 `MATCH (s:Subject) RETURN s.id` 列的是全局
    # Subject 注册表 — :Subject 节点没有 group_id 属性, 无法在其上注入
    # vault 过滤 (cypher_helpers.py wave-6 backlog 把本站点标为 VAULT-SCOPED
    # P1)。改从 CanvasNode 投影推导: 本 vault 内实际有节点的 subjectId 才是
    # 有效扩展候选 — 语义更准 (无节点的 subject tag 集恒空, 永远过不了
    # Jaccard 阈值), 同时消灭跨 vault 候选泄漏与对外 vault subject 的 N+1
    # tag 查询浪费。
    all_subject_ids: List[str] = []
    subjects_query = """
    MATCH (n:CanvasNode)
    WHERE (n.group_id = $vault_group OR n.group_id STARTS WITH $vault_prefix)
      AND n.subjectId IS NOT NULL AND n.subjectId <> ''
    RETURN DISTINCT n.subjectId AS id
    """
    try:
        async with neo4j_driver.session() as session:
            result = await session.run(
                subjects_query,
                vault_group=vault_group,
                vault_prefix=vault_prefix,
            )
            records = await result.data()
            all_subject_ids = [r["id"] for r in records if r.get("id")]
    except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
        logger.warning(f"expand_search_subjects: failed to list subjects: {e}")
        return [current_subject_id]

    if not all_subject_ids:
        return [current_subject_id]

    # 2. Fetch tags for each subject (vault-scoped, same group_id pin)
    all_tags: Dict[str, Set[str]] = {}
    for sid in all_subject_ids:
        all_tags[sid] = await get_subject_tags_from_neo4j(neo4j_driver, sid, group_id=group_id)

    # 3. Find related subjects
    related = await find_related_subjects(current_subject_id, all_tags, threshold=threshold)

    # 4. Always include the current subject first
    result_subjects = [current_subject_id]
    for sid in related:
        if sid != current_subject_id:
            result_subjects.append(sid)

    logger.info(f"expand_search_subjects: {current_subject_id} -> {result_subjects} (threshold={threshold})")
    return result_subjects


async def get_subject_tags_from_neo4j(
    neo4j_driver: object,
    subject_id: str,
    group_id: str = "",
) -> Set[str]:
    """
    Extract tags for a subject from Neo4j node keywords and content.

    P0-SYNC-ISO R10: 按 vault 前缀过滤 — 两个 vault 可能有同名 subjectId
    (如都叫 "math"), 不过滤则 tag 集跨 vault 混合, Jaccard 在脏集合上计算。

    Args:
        neo4j_driver: Neo4j async driver.
        subject_id: Subject identifier.
        group_id: Optional logical D16 group_id pinning the vault scope;
            empty falls back to the request ContextVar.

    Returns:
        Set of tags extracted from nodes in this subject (current vault only).
    """
    vault_group, vault_prefix = _physical_vault_scope(group_id)
    tags: Set[str] = set()
    query = """
    MATCH (n:CanvasNode {subjectId: $subject_id})
    WHERE n.title IS NOT NULL
      AND (n.group_id = $vault_group OR n.group_id STARTS WITH $vault_prefix)
    RETURN n.title AS title, n.ocrConcepts AS concepts
    """
    try:
        async with neo4j_driver.session() as session:
            result = await session.run(
                query,
                subject_id=subject_id,
                vault_group=vault_group,
                vault_prefix=vault_prefix,
            )
            records = await result.data()
            for rec in records:
                # Add title words as tags
                title = rec.get("title", "")
                if title:
                    for word in title.lower().split():
                        if len(word) > 1:
                            tags.add(word)
                # Add OCR concepts if present
                concepts = rec.get("concepts")
                if concepts and isinstance(concepts, list):
                    for concept in concepts:
                        tags.add(concept.lower().strip())
    except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
        logger.warning(f"Failed to get tags for subject {subject_id}: {e}")

    return tags
