"""Story 2.1 — Wikilink graph 上下文服务（独立模块）

提供:
- enrich_from_wikilink_graph: 调 Story 1.2 wikilink_graph_service 获取 N-hop 邻居
- 可配置 max_hops（默认 2）+ 超时保护（200ms NFR-PERF）
- AC #5: 图服务不可用 / 超时 / 异常 时降级（空邻居 + 降级标记）
- AC #2: 从 frontmatter relationships[] 提取关系类型

设计偏离 spec 的 Dev Notes：
- spec 建议"扩展 context_enrichment_service.py"，但该文件已 1161 行（Canvas JSON 时代逻辑），
  新增独立模块更符合 SOLID 单一职责。后续 Story 2.2 / 2.3 可复用本模块。
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

import structlog

from app.services.wikilink_graph_service import (
    NeighborNote,
    WikilinkGraphService,
    get_wikilink_graph_service,
)

logger = structlog.get_logger(__name__)

DEFAULT_MAX_HOPS = 2
DEFAULT_TIMEOUT_MS = 200


@dataclass
class WikilinkNeighborContext:
    """Story 2.1 AC #1 — wikilink graph 邻居上下文（区别于 Canvas JSON AdjacentNode）。"""

    slug: str
    path: str
    hop_distance: int
    relationship_type: str | None = None
    frontmatter: dict[str, Any] = field(default_factory=dict)
    content_summary: str | None = None


@dataclass
class EnrichmentResult:
    """Story 2.1 AC #5 — 含降级标记的结果包装。"""

    neighbors: list[WikilinkNeighborContext] = field(default_factory=list)
    degraded: bool = False
    degraded_reason: str | None = None
    elapsed_ms: float = 0.0


def _extract_relationship_type(
    fm: dict[str, Any], target_slug: str
) -> str | None:
    """从 frontmatter relationships[] 提取与 target_slug 关联的关系类型。

    relationships 期望格式：
        [{"type": "prerequisite", "target": "[[Fundamentals]]", ...}, ...]
    """
    relationships = fm.get("relationships")
    if not isinstance(relationships, list):
        return None
    for rel in relationships:
        if not isinstance(rel, dict):
            continue
        target = rel.get("target", "")
        if isinstance(target, str) and target_slug in target:
            rel_type = rel.get("type")
            if isinstance(rel_type, str) and rel_type:
                return rel_type
    return None


def _normalize_target_slug(node_path: str) -> str:
    """从 node_path 提取 basename（去 .md 后缀）作为 target_slug。"""
    basename = node_path.rsplit("/", 1)[-1]
    if basename.endswith(".md"):
        basename = basename[:-3]
    return basename


async def enrich_from_wikilink_graph(
    node_path: str,
    max_hops: int = DEFAULT_MAX_HOPS,
    timeout_ms: int = DEFAULT_TIMEOUT_MS,
    graph_service: WikilinkGraphService | None = None,
) -> EnrichmentResult:
    """Story 2.1 Task 1.1 — Wikilink graph N-hop 遍历邻居上下文。

    AC #1: 调 wikilink_graph_service.get_neighbors 获取 N-hop 邻居 + frontmatter
    AC #5: 图服务不可用 / 超时 / 异常 → degraded=True + 空 neighbors（不抛异常）
    NFR-PERF: 单次遍历 < 200ms（超时返回 degraded=True）

    Args:
        node_path: 节点 vault 相对路径（如 "节点/Eigenvalues.md"）
        max_hops: 遍历最大跳数（默认 2）
        timeout_ms: 单次遍历超时（默认 200ms 对齐 NFR-PERF）
        graph_service: 可注入测试 service（默认 singleton）

    Returns:
        EnrichmentResult，degraded 字段标识降级状态
    """
    start = time.monotonic()
    service = graph_service or get_wikilink_graph_service()

    if not service.is_built:
        elapsed = (time.monotonic() - start) * 1000
        logger.warning(
            "wikilink_context.graph_not_built",
            node_path=node_path,
            elapsed_ms=round(elapsed, 2),
        )
        return EnrichmentResult(
            neighbors=[],
            degraded=True,
            degraded_reason="wikilink_graph_not_built",
            elapsed_ms=elapsed,
        )

    try:
        loop = asyncio.get_event_loop()
        future = loop.run_in_executor(
            None, service.get_neighbors, node_path, max_hops
        )
        try:
            raw_neighbors: list[NeighborNote] = await asyncio.wait_for(
                future, timeout=timeout_ms / 1000.0
            )
        except asyncio.TimeoutError:
            elapsed = (time.monotonic() - start) * 1000
            logger.warning(
                "wikilink_context.timeout",
                node_path=node_path,
                timeout_ms=timeout_ms,
                elapsed_ms=round(elapsed, 2),
            )
            return EnrichmentResult(
                neighbors=[],
                degraded=True,
                degraded_reason="traversal_timeout",
                elapsed_ms=elapsed,
            )
    except Exception as e:
        elapsed = (time.monotonic() - start) * 1000
        logger.exception(
            "wikilink_context.unexpected_error",
            node_path=node_path,
            error=str(e),
        )
        return EnrichmentResult(
            neighbors=[],
            degraded=True,
            degraded_reason=f"unexpected_error: {type(e).__name__}",
            elapsed_ms=elapsed,
        )

    target_slug = _normalize_target_slug(node_path)
    contexts: list[WikilinkNeighborContext] = []
    for n in raw_neighbors:
        rel_type = _extract_relationship_type(n.frontmatter, target_slug)
        contexts.append(
            WikilinkNeighborContext(
                slug=n.title,
                path=n.path,
                hop_distance=n.hop_distance,
                relationship_type=rel_type,
                frontmatter=n.frontmatter,
                content_summary=None,
            )
        )

    contexts.sort(key=lambda c: (c.hop_distance, c.slug))

    elapsed = (time.monotonic() - start) * 1000
    logger.info(
        "wikilink_context.enriched",
        node_path=node_path,
        max_hops=max_hops,
        neighbor_count=len(contexts),
        elapsed_ms=round(elapsed, 2),
    )
    return EnrichmentResult(
        neighbors=contexts,
        degraded=False,
        elapsed_ms=elapsed,
    )
