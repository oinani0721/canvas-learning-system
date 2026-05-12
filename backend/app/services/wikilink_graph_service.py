"""Wikilink graph service — Story 1.2.

Parses vault .md files with obsidiantools, builds bidirectional NetworkX graph,
supports N-hop neighbor queries and hot updates via asyncio.Lock.
"""

from __future__ import annotations

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class NeighborNote:
    title: str
    path: str
    hop_distance: int
    frontmatter: dict[str, Any] = field(default_factory=dict)
    # Story 2.2+2.9 T2 (2026-05-11) — 4 精度 wikilink + backlink 支持
    is_backlink: bool = (
        False  # True: 通过反向边 (predecessor) 到达; False: 出边 (outgoing)
    )
    # Story 2.2+2.9 T4 (path_trace, 2026-05-11) — BFS 路径 (含 seed → ... → self)
    path_trace: list[str] = field(default_factory=list)


class WikilinkGraphService:
    """Bidirectional wikilink graph built from vault .md files."""

    def __init__(self) -> None:
        self._vault_path: Optional[str] = None
        self._vault = None  # obsidiantools.Vault
        self._graph = None  # NetworkX graph
        self._lock = asyncio.Lock()
        self._node_count = 0
        self._edge_count = 0
        self._build_timestamp: Optional[str] = None

    @property
    def is_built(self) -> bool:
        return self._graph is not None

    @property
    def node_count(self) -> int:
        return self._node_count

    @property
    def edge_count(self) -> int:
        return self._edge_count

    @property
    def build_timestamp(self) -> Optional[str]:
        """Story 2.1 P1.1 — ISO-8601 时间戳（UTC，秒精度），作为 RetrievalTrace.graph_version。"""
        return self._build_timestamp

    async def build(self, vault_path: str) -> dict[str, Any]:
        """Build the full wikilink graph from vault (AC #1)."""
        start = time.monotonic()

        def _build_sync():
            from obsidiantools.api import Vault

            v = Vault(Path(vault_path)).connect()
            return v

        loop = asyncio.get_event_loop()
        vault = await loop.run_in_executor(None, _build_sync)

        async with self._lock:
            self._vault_path = vault_path
            self._vault = vault
            self._graph = vault.graph
            self._node_count = self._graph.number_of_nodes()
            self._edge_count = self._graph.number_of_edges()
            self._build_timestamp = datetime.now(timezone.utc).isoformat(
                timespec="seconds"
            )

        duration_ms = (time.monotonic() - start) * 1000
        logger.info(
            "wikilink.graph_built",
            vault_path=vault_path,
            total_nodes=self._node_count,
            total_edges=self._edge_count,
            graph_build_time_ms=round(duration_ms, 1),
        )

        return {
            "total_nodes": self._node_count,
            "total_edges": self._edge_count,
            "build_time_ms": round(duration_ms, 1),
        }

    def get_neighbors(
        self,
        note_path: str,
        hop: int = 2,
        include_backlinks: bool = True,
    ) -> list[NeighborNote]:
        """BFS N-hop neighbor traversal (AC #2, #3, #5).

        Story 2.1 Phase 1 hotfix（2026-05-03）：
        plugin 端传 vault 相对路径（如 ``节点/Eigenvalues.md``），
        但 obsidiantools graph 的 node key 是 **basename only**（如 ``Eigenvalues``）。
        本方法对 full path → basename 做 fallback 匹配，避免邻居总是 0 的隐性 bug。

        Story 2.2+2.9 T2 (2026-05-11) — backlinks + path_trace:
            ``include_backlinks=True``: 同时遍历出边 (successors) 和入边
            (predecessors)，NeighborNote 标 ``is_backlink``。反向边对应
            "节点 Y 在正文里 ``[[X]]`` 引用 seed=X" 场景，与 outgoing 等价
            但来源不同。``path_trace``: BFS 时记录路径 [seed, ..., self]。
        """
        if self._graph is None:
            return []

        key = note_path
        if key.endswith(".md"):
            key = key[:-3]

        def _node_adj(node: str) -> list[str]:
            """取节点的"出边 + 入边"邻居（去重，outgoing 优先排序）"""
            if node not in self._graph:
                return []
            if hasattr(self._graph, "successors"):
                out = list(self._graph.successors(node))
            else:
                out = list(self._graph.neighbors(node))
            if include_backlinks and hasattr(self._graph, "predecessors"):
                seen = set(out)
                for b in self._graph.predecessors(node):
                    if b not in seen:
                        out.append(b)
                        seen.add(b)
            return out

        def _is_backlink_edge(src: str, dst: str) -> bool:
            """判断 dst 是 src 的 backlink（入边）而非 outgoing（出边）"""
            if not hasattr(self._graph, "successors"):
                return False
            return dst not in list(self._graph.successors(src))

        # Story 2.1 Phase 1 hotfix（2026-05-03）：obsidiantools 行为：
        # 同一物理文件有"两个图节点"——vault 相对路径 key（孤立，0 邻居）
        # 和 wikilink 文本 key（如 basename，有真实邻居关系）。
        # plugin 端传 vault 路径会命中孤立节点 → 总是 0 邻居。
        # 修复策略：路径 key 找到但 0 邻居时，回退到 basename。
        primary_in_graph = key in self._graph
        primary_adj = _node_adj(key) if primary_in_graph else []

        if not primary_in_graph or len(primary_adj) == 0:
            basename = key.rsplit("/", 1)[-1]
            if basename and basename != key and basename in self._graph:
                basename_adj = _node_adj(basename)
                if len(basename_adj) > 0:
                    logger.info(
                        "wikilink.path_normalized_to_basename",
                        note_path=note_path,
                        primary_key=key,
                        primary_adj_count=len(primary_adj),
                        basename_key=basename,
                        basename_adj_count=len(basename_adj),
                    )
                    key = basename
                else:
                    # 路径和 basename 都是孤立节点 → 真正无邻居
                    return []
            else:
                if not primary_in_graph:
                    return []
                # primary 在图里但 0 邻居（真正孤立节点）
                return []

        start = time.monotonic()
        neighbors: list[NeighborNote] = []
        visited: set[str] = {key}
        # BFS 队列含 path_trace (从 seed 起的累积路径)
        queue: deque[tuple[str, int, list[str]]] = deque([(key, 0, [key])])

        while queue:
            current, depth, current_path = queue.popleft()
            if depth >= hop:
                continue
            for adj in _node_adj(current):
                if adj in visited:
                    continue
                visited.add(adj)

                fm = self._get_frontmatter(adj)
                is_back = _is_backlink_edge(current, adj)
                neighbor_path = current_path + [adj]
                neighbors.append(
                    NeighborNote(
                        title=adj,
                        path=self._resolve_path(adj),
                        hop_distance=depth + 1,
                        frontmatter=fm,
                        is_backlink=is_back,
                        path_trace=neighbor_path,
                    )
                )
                queue.append((adj, depth + 1, neighbor_path))

        duration_ms = (time.monotonic() - start) * 1000
        backlink_count = sum(1 for n in neighbors if n.is_backlink)
        logger.debug(
            "wikilink.get_neighbors",
            note_path=note_path,
            hop=hop,
            neighbor_count=len(neighbors),
            backlink_count=backlink_count,
            include_backlinks=include_backlinks,
            traversal_time_ms=round(duration_ms, 2),
        )
        return neighbors

    async def refresh(self, changed_files: list[str] | None = None) -> dict[str, Any]:
        """Hot update the graph (AC #4). Full rebuild for v1."""
        if self._vault_path is None:
            return {"error": "Graph not built yet"}
        return await self.build(self._vault_path)

    def get_stats(self) -> dict[str, Any]:
        return {
            "vault_path": self._vault_path,
            "is_built": self.is_built,
            "total_nodes": self._node_count,
            "total_edges": self._edge_count,
            "build_timestamp": self._build_timestamp,
        }

    def get_degree_stats(self) -> dict[str, float]:
        """Story 2.2+2.9 T3.5 — degree percentile snapshot for hub penalty.

        Story 2.9 AC #2: hub_penalty = log(degree / median + 1) 用此 dict 的
        `median` 字段做归一化基线，防 MOC/Index 类高 degree 节点垄断邻居列表。

        Returns:
            dict with keys:
            - median (== p50): float, robust 基线
            - p95: float, hub threshold 参考
            - max: float, sanity check
            - count: int, 节点总数
            Empty graph / None → 全 0。
        """
        if self._graph is None or self._node_count == 0:
            return {"median": 0.0, "p50": 0.0, "p95": 0.0, "max": 0.0, "count": 0}

        # NetworkX DiGraph.degree(n) = in_degree + out_degree (total)
        degrees = sorted(int(self._graph.degree(n)) for n in self._graph.nodes())
        n = len(degrees)
        if n == 0:
            return {"median": 0.0, "p50": 0.0, "p95": 0.0, "max": 0.0, "count": 0}

        median = float(degrees[n // 2])
        p95_idx = min(int(n * 0.95), n - 1)
        p95 = float(degrees[p95_idx])
        max_deg = float(degrees[-1])
        return {
            "median": median,
            "p50": median,
            "p95": p95,
            "max": max_deg,
            "count": n,
        }

    def get_degree(self, note_key: str) -> int:
        """Story 2.2+2.9 T3.5 — single-node degree lookup for hub penalty.

        Mirrors get_neighbors() basename fallback logic so hub_penalty 用的
        degree 与 BFS 找到的同一节点对齐 (避免路径 vs basename 不一致导致
        penalty 被错误归零).
        """
        if self._graph is None or not note_key:
            return 0

        key = note_key
        if key.endswith(".md"):
            key = key[:-3]

        if key in self._graph:
            return int(self._graph.degree(key))

        basename = key.rsplit("/", 1)[-1]
        if basename and basename != key and basename in self._graph:
            return int(self._graph.degree(basename))

        return 0

    def _get_frontmatter(self, note_key: str) -> dict[str, Any]:
        if self._vault is None:
            return {}
        try:
            fm = self._vault.get_front_matter(note_key)
            return fm if isinstance(fm, dict) else {}
        except Exception:
            return {}

    def _resolve_path(self, note_key: str) -> str:
        if self._vault is None:
            return f"{note_key}.md"
        try:
            source = self._vault.get_source_path(note_key)
            return str(source) if source else f"{note_key}.md"
        except Exception:
            return f"{note_key}.md"


# Singleton
_wikilink_graph_service: Optional[WikilinkGraphService] = None


def get_wikilink_graph_service() -> WikilinkGraphService:
    global _wikilink_graph_service
    if _wikilink_graph_service is None:
        _wikilink_graph_service = WikilinkGraphService()
    return _wikilink_graph_service
