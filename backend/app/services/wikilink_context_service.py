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

    Story 2.2+2.9 T2 (2026-05-11) — wikilink 4 精度 + backlink 字段:
        backlink: True 表示邻居通过反向边 (predecessor) 到达（节点 Y 在正文里
                  ``[[X]]`` 引用 seed=X 场景）。False 表示出边 (outgoing)。
        heading_anchor: 当 seed 的正文用 ``[[X#Heading]]`` 引用此邻居时填入,
                       下游可只装载该 heading 段落而非整文件。
        alias: 当 seed 用 ``[[X|Y]]`` 引用时填入 Y, prompt 渲染时用 alias 替代 slug。
        block_id: 当 seed 用 ``[[X#^block_id]]`` 引用时填入 block_id。
        path_trace: BFS 路径 [seed, ..., self], 长度 = hop_distance + 1.

    Story 2.2+2.9 T5 (2026-05-11) — Relationship Evidence (AC #6):
        evidence: 当 frontmatter relationships[] 含 `evidence: "..."` 字段时填入,
                 Claude 看到引证可作为外部书目/公式锚点 (e.g. "see eq. 3.2 in Strang")
    """

    slug: str
    path: str
    hop_distance: int
    relationship_type: str | None = None
    frontmatter: dict[str, Any] = field(default_factory=dict)
    content_summary: str | None = None
    callouts: list[dict[str, str]] = field(default_factory=list)
    backlink: bool = False
    heading_anchor: str | None = None
    alias: str | None = None
    block_id: str | None = None
    path_trace: list[str] = field(default_factory=list)
    evidence: str | None = None


@dataclass
class TraceItem:
    """Story 2.1 P1.1 — RetrievalTrace 单条入选项。

    Story 2.2+2.9 T2 (2026-05-11) — path_trace + backlink:
        path_trace: BFS 路径 [seed, ..., self], 让 Claude 看到"通过哪个中间节点到达"。
        reason 现已用 "wikilink_backlink" 区分反向边。

    Story 2.2+2.9 T5 (2026-05-11) — Relationship Evidence (AC #6):
        evidence: 外部书目/公式锚点 (frontmatter relationships[].evidence). 让
                 trace 上能看到"为什么这条邻居被引入"的人工标注理由 (vs 纯 graph 邻接)。

    Story 2.2+2.9 Global-Search (2026-05-12) — Multi-seed BFS 诊断字段:
        seed_origin: 该 trace item 是通过哪个 seed 到达的 (single-seed 模式下为 None,
                    multi-seed 模式下记录原始 seed node_path, 便于"节点 X 解题遇到
                    外来概念 Y"场景下区分 X 邻居 vs Y 邻居)。
    """

    path: str
    hop: int
    relationship_type: str | None
    reason: str  # "wikilink_outgoing" | "wikilink_backlink" | "frontmatter_link" | ...
    tokens: int = 0  # 占位，Phase 2 接入 query-aware rerank 后由 assembler 回填
    path_trace: list[str] = field(default_factory=list)
    evidence: str | None = None
    seed_origin: str | None = None


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


def _extract_relationship_type(fm: dict[str, Any], target_slug: str) -> str | None:
    """Backward-compat shim — 单返回 type. 新代码用 _extract_relationship_info."""
    info = _extract_relationship_info(fm, target_slug)
    return info[0] if info else None


def _extract_relationship_info(
    fm: dict[str, Any], target_slug: str
) -> tuple[str | None, str | None]:
    """Story 2.2+2.9 T5.2 — 从 frontmatter relationships[] 提取关系 type + evidence.

    relationships 期望格式：
        [{"type": "prerequisite", "target": "[[Fundamentals]]",
          "evidence": "see eq. 3.2 in Strang"}, ...]

    Returns:
        (type, evidence) tuple. 任一字段缺失返回 None。
        无匹配 entry → (None, None)。
    """
    relationships = fm.get("relationships")
    if not isinstance(relationships, list):
        return (None, None)
    for rel in relationships:
        if not isinstance(rel, dict):
            continue
        target = rel.get("target", "")
        if isinstance(target, str) and target_slug in target:
            rel_type = rel.get("type")
            evidence = rel.get("evidence")
            return (
                rel_type if isinstance(rel_type, str) and rel_type else None,
                evidence if isinstance(evidence, str) and evidence else None,
            )
    return (None, None)


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

# Phase 1.7+ (2026-05-03 ChatGPT 对抗审查 P0#5 fix):
# 旧 regex `(?P<body>(?:^[ ]{0,3}>.*\n?)*)` 贪婪匹配下一个 callout header,
# 把相邻 callout 吞进上一个的 body. 改用 line scanner (O(n), 无 backtracking).
_CALLOUT_HEADER_PATTERN = re.compile(
    r"^[ ]{0,3}>[ ]?\[!(?P<kind>[\w/-]+)\][+-]?[ \t]*(?P<title>.*)$"
)
_QUOTE_PREFIX_PATTERN = re.compile(r"^[ ]{0,3}>")
_FRONTMATTER_PATTERN = re.compile(r"^\ufeff?---\r?\n.*?\r?\n---\r?\n", re.DOTALL)

# Canvas Story 1.16 锁定 7 类（question/tip/error/hint/note/warning/info）.
# Canvas ai-linked-doc skill 自动派生的 `relation/extends` 是噪音, 过滤掉.
_USER_ANNOTATION_KINDS = {
    "question",
    "tip",
    "error",
    "hint",
    "note",
    "warning",
    "info",
}
_NOISE_CALLOUT_KIND_PREFIXES = ("relation/", "relation-")
_BODY_EXCERPT_MAX_CHARS = 400
_CALLOUT_TITLE_MAX = 80
_CALLOUT_CONTENT_MAX = 200
_MAX_CALLOUTS_PER_NEIGHBOR = 8

# Phase 1.7+ (2026-05-03 ChatGPT P0-A fix): 防 path traversal / DoS
_MAX_NEIGHBOR_MD_BYTES = 1_000_000  # 1MB cap


def _strip_quote_prefix(line: str) -> str:
    return re.sub(r"^[ ]{0,3}>[ ]?", "", line).rstrip()


def _extract_user_callouts(text: str) -> list[dict[str, str]]:
    """从 markdown 提取用户批注 callout (仅 Canvas 7 类, 过滤 relation/* 噪音).

    Phase 1.7+ (2026-05-03): 改 line scanner. 正确处理:
    - 相邻 callout (P0#5 fix): 遇到下一个 header 就 flush 上一个
    - 嵌套 code fence: ``` 内跳过避免误识别
    - 非 quote 行 break: 退出当前 callout 而非吞并
    - Filtered kind: 不阻断后续 callout (relation/* 跳过, 但下一条还能识别)

    Returns: [{"kind": "tip", "title": "...", "content": "..."}, ...]
    """
    if not text:
        return []
    callouts: list[dict] = []
    current: dict | None = None
    in_code_fence = False
    for line in text.split("\n"):
        stripped = line.strip()
        # Code fence toggle (``` 或 ~~~)
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_fence = not in_code_fence
            if current is not None:
                callouts.append(current)
                current = None
            continue
        if in_code_fence:
            continue
        # Callout header
        m = _CALLOUT_HEADER_PATTERN.match(line)
        if m:
            if current is not None:
                callouts.append(current)
                current = None
            kind_raw = (m.group("kind") or "").lower().strip()
            if not kind_raw:
                continue
            if any(kind_raw.startswith(p) for p in _NOISE_CALLOUT_KIND_PREFIXES):
                continue
            if kind_raw not in _USER_ANNOTATION_KINDS:
                continue
            title = (m.group("title") or "").strip()[:_CALLOUT_TITLE_MAX]
            current = {"kind": kind_raw, "title": title, "_lines": []}
            continue
        # Quote line (> ...) — 只装入当前 callout
        if _QUOTE_PREFIX_PATTERN.match(line):
            if current is not None:
                stripped_q = _strip_quote_prefix(line)
                if stripped_q or current["_lines"]:
                    current["_lines"].append(stripped_q)
            continue
        # 非 quote 行 break 当前 callout
        if current is not None:
            callouts.append(current)
            current = None
    if current is not None:
        callouts.append(current)

    out: list[dict[str, str]] = []
    for c in callouts:
        content = "\n".join(c["_lines"]).strip()[:_CALLOUT_CONTENT_MAX]
        if c["title"] or content:
            out.append({"kind": c["kind"], "title": c["title"], "content": content})
        if len(out) >= _MAX_CALLOUTS_PER_NEIGHBOR:
            break
    return out


def _extract_body_excerpt(text: str, max_chars: int = _BODY_EXCERPT_MAX_CHARS) -> str:
    """去 frontmatter + callout block 后的 prose excerpt.

    Phase 1.7+ (2026-05-03): 不再用 regex 跨块吞并 (P0#5 同根因).
    保留普通 blockquote (如教材引文); 只抠掉已识别的 callout 块.
    """
    if not text:
        return ""
    # 去 frontmatter (兼容 BOM + CRLF)
    no_fm = _FRONTMATTER_PATTERN.sub("", text, count=1)
    # line scanner: 跳过 callout block (header + 后续 quote 行直到非 quote)
    out_lines: list[str] = []
    skipping_callout = False
    in_code_fence = False
    for line in no_fm.split("\n"):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_fence = not in_code_fence
            skipping_callout = False
            out_lines.append(line)
            continue
        if in_code_fence:
            out_lines.append(line)
            continue
        if _CALLOUT_HEADER_PATTERN.match(line):
            skipping_callout = True
            continue
        if skipping_callout:
            if _QUOTE_PREFIX_PATTERN.match(line):
                continue
            skipping_callout = False
        out_lines.append(line)
    cleaned = re.sub(r"\n{3,}", "\n\n", "\n".join(out_lines)).strip()
    return cleaned[:max_chars]


def _resolve_vault_md_path(neighbor_path: str, vault_path: str | None) -> Path | None:
    """安全解析邻居 .md 路径 (Phase 1.7+ ChatGPT P0-A path traversal fix).

    必须 1) 落在 vault_path resolve 后的根内, 2) 后缀 .md, 3) size <= 1MB.
    防御 absolute path attack / symlink escape / DoS.
    """
    if not neighbor_path or not vault_path:
        return None
    try:
        root = Path(vault_path).resolve(strict=True)
        raw = Path(neighbor_path)
        candidate = (raw if raw.is_absolute() else root / raw).resolve(strict=True)
        # 边界检查: 必须在 vault root 下 (含 symlink resolve)
        candidate.relative_to(root)
        if candidate.suffix.lower() != ".md":
            return None
        if candidate.stat().st_size > _MAX_NEIGHBOR_MD_BYTES:
            logger.debug(
                "wikilink_context.neighbor_too_large",
                path=str(candidate),
                size=candidate.stat().st_size,
            )
            return None
        return candidate
    except (OSError, ValueError) as e:
        logger.debug(
            "wikilink_context.neighbor_resolve_failed",
            path=neighbor_path,
            vault_path=vault_path,
            error=str(e),
        )
        return None


def _read_neighbor_md(neighbor_path: str, vault_path: str | None) -> str | None:
    """读邻居 .md 文件内容 (sandbox: 必须在 vault_path 内 + 1MB size cap)."""
    candidate = _resolve_vault_md_path(neighbor_path, vault_path)
    if candidate is None:
        return None
    try:
        return candidate.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        logger.debug(
            "wikilink_context.neighbor_read_failed",
            path=str(candidate),
            error=str(e),
        )
        return None


async def enrich_from_wikilink_graph(
    node_path: str,
    max_hops: int = DEFAULT_MAX_HOPS,
    timeout_ms: int = DEFAULT_TIMEOUT_MS,
    graph_service: WikilinkGraphService | None = None,
    additional_seeds: list[str] | None = None,
) -> EnrichmentResult:
    """Story 2.1 Task 1.1 — Wikilink graph N-hop 遍历邻居上下文。

    AC #1: 调 wikilink_graph_service.get_neighbors 获取 N-hop 邻居 + frontmatter
    AC #5: 图服务不可用 / 超时 / 异常 → degraded=True + 空 neighbors（不抛异常）
    NFR-PERF: 单次遍历 < 200ms（超时返回 degraded=True）

    Story 2.2+2.9 Global-Search (2026-05-12) — Multi-seed BFS:
        当 `additional_seeds` 提供时, 每个 seed 各跑一遍 BFS, merge 结果按 slug
        去重保留 min(hop_distance), 用于"节点 X 解题遇到外来概念 Y, 装 Y 邻居"场景。
        TraceItem.seed_origin 记录"通过哪个 seed 到达", 便于诊断。
        additional_seeds=None 时保持单 seed 行为完全不变 (backward compat)。

    Args:
        node_path: 主 seed 节点 vault 相对路径（如 "节点/Eigenvalues.md"）
        max_hops: 遍历最大跳数（默认 2）
        timeout_ms: 单次遍历超时（默认 200ms 对齐 NFR-PERF）
        graph_service: 可注入测试 service（默认 singleton）
        additional_seeds: 额外 seed 列表 (None / []: 纯 single-seed 模式)

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
        future = loop.run_in_executor(None, service.get_neighbors, node_path, max_hops)
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
    seen_slugs: set[str] = set()
    # Story 2.2+2.9 Global-Search (2026-05-12) — multi-seed 模式标记 seed_origin
    # additional_seeds 提供时,主 seed 仍记录 seed_origin=node_path (诊断对称)
    is_multi_seed = bool(additional_seeds)
    primary_seed_origin: str | None = node_path if is_multi_seed else None
    for n in raw_neighbors:
        # Phase 1.7+ (2026-05-03 用户 UAT P1 fix): 过滤 seed 自循环 + 同 slug 去重.
        # 根因: obsidiantools graph 同一文件可能有 path-prefixed key (节点/X) 与
        # basename key (X) 双 node, BFS visited set 用 path-prefixed 时 basename
        # 在 2-hop 处会被误识别为新邻居, seed 自己出现在 2-hop 里 (用户实测发现).
        slug_basename = _normalize_target_slug(n.title)
        if slug_basename == target_slug:
            continue  # 跳过 seed 自循环
        if slug_basename in seen_slugs:
            continue  # 跳过同 slug 重复 (path/basename 双 node 同时出现)
        seen_slugs.add(slug_basename)

        # Story 2.2+2.9 T5.2 (2026-05-11) — 同时取 type + evidence (单次扫 fm)
        rel_type, evidence = _extract_relationship_info(n.frontmatter, target_slug)
        # Phase 1.7 — 读邻居 .md body 提取 callout + prose excerpt
        n_text = _read_neighbor_md(n.path, vault_root)
        callouts = _extract_user_callouts(n_text) if n_text else []
        excerpt = _extract_body_excerpt(n_text) if n_text else None
        # Story 2.2+2.9 T2 (2026-05-11) — backlink + path_trace 字段透传
        is_backlink = getattr(n, "is_backlink", False)
        path_trace = list(getattr(n, "path_trace", []))
        contexts.append(
            WikilinkNeighborContext(
                slug=slug_basename,
                path=n.path,
                hop_distance=n.hop_distance,
                relationship_type=rel_type,
                frontmatter=n.frontmatter,
                content_summary=excerpt,
                callouts=callouts,
                backlink=is_backlink,
                path_trace=path_trace,
                evidence=evidence,
            )
        )
        # Story 2.2+2.9 T2 (2026-05-11) — reason 区分 outgoing vs backlink
        # frontmatter_link 优先（用户显式声明），其次按边方向（outgoing/backlink）
        if rel_type is not None:
            reason = "frontmatter_link"
        elif is_backlink:
            reason = "wikilink_backlink"
        else:
            reason = "wikilink_outgoing"
        trace_items.append(
            TraceItem(
                path=n.path,
                hop=n.hop_distance,
                relationship_type=rel_type,
                reason=reason,
                tokens=0,
                path_trace=path_trace,
                evidence=evidence,
                seed_origin=primary_seed_origin,
            )
        )

    # Story 2.2+2.9 Global-Search (2026-05-12) — Multi-seed BFS merge.
    # 对每个 additional_seed 单独跑 BFS, merge 邻居/trace 到主结果:
    # - 按 slug 去重保留 min(hop_distance)
    # - TraceItem.seed_origin 记录"通过哪个 seed 到达"
    # - 任一 sub-seed 触发 degraded → 不影响主结果 (best-effort, 不阻断)
    # - target_slug 自循环过滤扩展到所有 seed 的 slug 集合
    if additional_seeds:
        all_seed_slugs = {target_slug}
        for s in additional_seeds:
            all_seed_slugs.add(_normalize_target_slug(s))
        # 主结果里把跨 seed 自循环也过滤掉 (e.g. seed=[X, Y], Y 出现在 X 的邻居里
        # 应保留 — Y 是另一个 seed, 不是 X 邻居 noise; 但 if X 邻居含 Y, 视为
        # "通过 X 到达 Y", path_trace 已记录, 不重复添加 — 留给 sub-seed 自己跑)
        # 实现选择: 保留主 seed 邻居 (含其他 seed 节点本身 - 因为它确实是 1-hop 邻居)
        # sub-seed 跑时再处理自循环过滤

        for seed in additional_seeds:
            if not seed or not seed.strip():
                continue
            try:
                # 复用整个函数 (含 timeout / degraded handling), 但 additional_seeds=None
                # 避免递归无限. timeout/graph_service/max_hops 沿用主调用参数.
                sub_result = await enrich_from_wikilink_graph(
                    node_path=seed,
                    max_hops=max_hops,
                    timeout_ms=timeout_ms,
                    graph_service=graph_service,
                    additional_seeds=None,
                )
            except Exception as e:
                logger.warning(
                    "wikilink_context.additional_seed_failed",
                    seed=seed,
                    error=str(e)[:120],
                )
                continue
            if sub_result.degraded:
                logger.debug(
                    "wikilink_context.additional_seed_degraded",
                    seed=seed,
                    reason=sub_result.degraded_reason,
                )
                # 不阻断主结果, 跳过该 seed 邻居
                continue
            for sub_n in sub_result.neighbors:
                if sub_n.slug in seen_slugs:
                    # 已在主 seed 或前一 additional seed 中, 检查是否需要更新 min hop
                    # 简化: 保留先到 (主 seed 优先), 不替换 (FIFO 语义符合"主 seed 是
                    # 中心, additional 是补充" prompt 语义)
                    continue
                if (
                    sub_n.slug in all_seed_slugs
                    and sub_n.slug != _normalize_target_slug(seed)
                ):
                    # 跨 seed 自循环: e.g. sub_seed=Y 跑到主 seed X
                    # 跳过 (主 seed 已是分析中心, 不当成 Y 的邻居装入)
                    continue
                seen_slugs.add(sub_n.slug)
                contexts.append(sub_n)
            # merge sub_result.trace.included 时标 seed_origin=seed
            if sub_result.trace is not None:
                sub_paths_in_main = {t.path for t in trace_items}
                for sub_item in sub_result.trace.included:
                    if sub_item.path in sub_paths_in_main:
                        continue
                    trace_items.append(
                        TraceItem(
                            path=sub_item.path,
                            hop=sub_item.hop,
                            relationship_type=sub_item.relationship_type,
                            reason=sub_item.reason,
                            tokens=sub_item.tokens,
                            path_trace=sub_item.path_trace,
                            evidence=sub_item.evidence,
                            seed_origin=seed,
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
