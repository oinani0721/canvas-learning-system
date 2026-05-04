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
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
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
    """Story 2.1 AC #1 — wikilink graph 邻居上下文（区别于 Canvas JSON AdjacentNode）。

    Phase 1.7（2026-05-03）: 加 `callouts` 字段装载邻居 .md body 里的 Obsidian
    callout（[!tip]+/[!error]+/[!question]+ 等），让 Claude 看到用户批注事实存档，
    而非仅 frontmatter 元数据。content_summary 装去 frontmatter+callout 后的 prose excerpt。
    """

    slug: str
    path: str
    hop_distance: int
    relationship_type: str | None = None
    frontmatter: dict[str, Any] = field(default_factory=dict)
    content_summary: str | None = None
    callouts: list[dict[str, str]] = field(default_factory=list)


@dataclass
class TraceItem:
    """Story 2.1 P1.1 — RetrievalTrace 单条入选项。"""

    path: str
    hop: int
    relationship_type: str | None
    reason: str  # "wikilink_outgoing" | "wikilink_backlink" | "frontmatter_link" | ...
    tokens: int = 0  # 占位，Phase 2 接入 query-aware rerank 后由 assembler 回填


@dataclass
class RetrievalTrace:
    """Story 2.1 P1.1 — 检索过程结构化追踪（让 Claude / 调试者看见 RAG 边界）。

    included: 入选邻居 + 来源 reason
    omitted:  被丢弃邻居 + 原因（hub_penalty_*, token_budget, stale_summary, ...）
    degradations: 全局降级原因（wikilink_graph_not_built, traversal_timeout, ...）
    graph_version: WikilinkGraphService.build_timestamp（同一构建的所有查询共享）
    """

    seed: str
    max_hops: int
    graph_version: str
    elapsed_ms: float = 0.0
    included: list[TraceItem] = field(default_factory=list)
    omitted: list[dict[str, Any]] = field(default_factory=list)
    degradations: list[str] = field(default_factory=list)


@dataclass
class EnrichmentResult:
    """Story 2.1 AC #5 — 含降级标记的结果包装。"""

    neighbors: list[WikilinkNeighborContext] = field(default_factory=list)
    degraded: bool = False
    degraded_reason: str | None = None
    elapsed_ms: float = 0.0
    trace: RetrievalTrace | None = None


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


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1.7 — Body callout extraction (Story 2.1, 2026-05-03)
# 4 路并行 deep explore 共识：邻居装载从 frontmatter-only 升级到 frontmatter +
# body excerpt + callout 提取（参考 EcphoryRAG / GraphRAG hybrid neighbor strategy）。
# 实现选 regex 而非 obsidian-callouts pip 包：零新依赖、Canvas 7 callout 类型固定、
# 节点规模 ≤30 性能不敏感。社区先例：Quartz 4 + Dataview 都用 regex 提取 callout。
# ─────────────────────────────────────────────────────────────────────────────

# Obsidian callout 起始行：`> [!kind]+/-? title?`
# kind 可含 `/`（如 Canvas 自定义 `relation/extends`）
_CALLOUT_PATTERN = re.compile(
    r"^[ ]{0,3}>[ ]?\[!(?P<kind>[\w/-]+)\][+-]?[ \t]*(?P<title>[^\n]*)\n"
    r"(?P<body>(?:^[ ]{0,3}>.*\n?)*)",
    re.MULTILINE,
)
_FRONTMATTER_PATTERN = re.compile(r"^---\n.*?\n---\n", re.DOTALL)
_QUOTE_LINE_PATTERN = re.compile(r"^[ ]{0,3}>.*\n?", re.MULTILINE)

# Canvas Story 1.16 锁定 7 类（question/tip/error/hint/note/warning/info）。
# Canvas ai-linked-doc skill 自动派生的 `relation/extends` 是噪音，过滤掉。
_USER_ANNOTATION_KINDS = {
    "question", "tip", "error", "hint", "note", "warning", "info",
}
_NOISE_CALLOUT_KIND_PREFIXES = ("relation/", "relation-")
_BODY_EXCERPT_MAX_CHARS = 400
_CALLOUT_TITLE_MAX = 80
_CALLOUT_CONTENT_MAX = 200
_MAX_CALLOUTS_PER_NEIGHBOR = 8


def _strip_quote_prefix(line: str) -> str:
    return re.sub(r"^[ ]{0,3}>[ ]?", "", line).rstrip()


def _extract_user_callouts(text: str) -> list[dict[str, str]]:
    """从 markdown 提取用户批注 callout（仅 Canvas 7 类，过滤 relation/* 噪音）。

    Returns: [{"kind": "tip", "title": "...", "content": "..."}, ...]
    """
    if not text:
        return []
    out: list[dict[str, str]] = []
    for match in _CALLOUT_PATTERN.finditer(text):
        kind_raw = (match.group("kind") or "").lower().strip()
        if not kind_raw:
            continue
        # 过滤 Canvas 自动派生的 relation/* callout
        if any(kind_raw.startswith(p) for p in _NOISE_CALLOUT_KIND_PREFIXES):
            continue
        if kind_raw not in _USER_ANNOTATION_KINDS:
            continue
        title = (match.group("title") or "").strip()[:_CALLOUT_TITLE_MAX]
        body_block = match.group("body") or ""
        content_lines = [
            _strip_quote_prefix(ln)
            for ln in body_block.split("\n")
            if ln.strip().startswith(">")
        ]
        content = "\n".join(content_lines).strip()[:_CALLOUT_CONTENT_MAX]
        if title or content:
            out.append({"kind": kind_raw, "title": title, "content": content})
        if len(out) >= _MAX_CALLOUTS_PER_NEIGHBOR:
            break
    return out


def _extract_body_excerpt(text: str, max_chars: int = _BODY_EXCERPT_MAX_CHARS) -> str:
    """去 frontmatter + 全部 callout / quote 行后的 prose excerpt。"""
    if not text:
        return ""
    no_fm = _FRONTMATTER_PATTERN.sub("", text, count=1)
    no_callouts = _CALLOUT_PATTERN.sub("", no_fm)
    no_quotes = _QUOTE_LINE_PATTERN.sub("", no_callouts)
    cleaned = re.sub(r"\n{3,}", "\n\n", no_quotes).strip()
    return cleaned[:max_chars]


def _read_neighbor_md(neighbor_path: str, vault_path: str | None) -> str | None:
    """读邻居 .md 文件内容（兼容 absolute 与 vault-relative 两种 path 形式）。"""
    if not neighbor_path:
        return None
    p = Path(neighbor_path)
    if not p.is_absolute() and vault_path:
        p = Path(vault_path) / p
    try:
        return p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        logger.debug(
            "wikilink_context.neighbor_read_failed", path=str(p), error=str(e)
        )
        return None


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
    graph_version = getattr(service, "build_timestamp", None) or "unbuilt"

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
            trace=RetrievalTrace(
                seed=node_path,
                max_hops=max_hops,
                graph_version=graph_version,
                elapsed_ms=elapsed,
                degradations=["wikilink_graph_not_built"],
            ),
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
                trace=RetrievalTrace(
                    seed=node_path,
                    max_hops=max_hops,
                    graph_version=graph_version,
                    elapsed_ms=elapsed,
                    degradations=["traversal_timeout"],
                ),
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
            trace=RetrievalTrace(
                seed=node_path,
                max_hops=max_hops,
                graph_version=graph_version,
                elapsed_ms=elapsed,
                degradations=[f"unexpected_error:{type(e).__name__}"],
            ),
        )

    target_slug = _normalize_target_slug(node_path)
    vault_root = getattr(service, "_vault_path", None)
    contexts: list[WikilinkNeighborContext] = []
    trace_items: list[TraceItem] = []
    for n in raw_neighbors:
        rel_type = _extract_relationship_type(n.frontmatter, target_slug)
        # Phase 1.7 — 读邻居 .md body 提取 callout + prose excerpt
        n_text = _read_neighbor_md(n.path, vault_root)
        callouts = _extract_user_callouts(n_text) if n_text else []
        excerpt = _extract_body_excerpt(n_text) if n_text else None
        # Phase 1.7 — slug 规范化为 basename（obsidiantools graph key 在某些
        # 版本带路径前缀如 "节点/X"，验收单步骤 3 要求纯 basename "X"）。
        # 同时 [[X]] 形式更符合 Obsidian wikilink 简写惯例（Skill 默认引用方式）。
        slug_basename = _normalize_target_slug(n.title)
        contexts.append(
            WikilinkNeighborContext(
                slug=slug_basename,
                path=n.path,
                hop_distance=n.hop_distance,
                relationship_type=rel_type,
                frontmatter=n.frontmatter,
                content_summary=excerpt,
                callouts=callouts,
            )
        )
        # Phase 1 仅区分 frontmatter 显式声明 vs BFS 默认推断；
        # Phase 2 区分 outgoing / backlink，Phase 3 加 alias / heading
        reason = "frontmatter_link" if rel_type is not None else "wikilink_outgoing"
        trace_items.append(
            TraceItem(
                path=n.path,
                hop=n.hop_distance,
                relationship_type=rel_type,
                reason=reason,
                tokens=0,
            )
        )

    contexts.sort(key=lambda c: (c.hop_distance, c.slug))
    trace_items.sort(key=lambda t: (t.hop, t.path))

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
        trace=RetrievalTrace(
            seed=node_path,
            max_hops=max_hops,
            graph_version=graph_version,
            elapsed_ms=elapsed,
            included=trace_items,
            omitted=[],
            degradations=[],
        ),
    )
