"""Wikilink graph service — Story 1.2.

Parses vault .md files with obsidiantools, builds bidirectional NetworkX graph,
supports N-hop neighbor queries and hot updates via asyncio.Lock.
"""

from __future__ import annotations

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
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


class WikilinkGraphService:
    """Bidirectional wikilink graph built from vault .md files."""

    def __init__(self) -> None:
        self._vault_path: Optional[str] = None
        self._vault = None  # obsidiantools.Vault
        self._graph = None  # NetworkX graph
        self._lock = asyncio.Lock()
        self._node_count = 0
        self._edge_count = 0

    @property
    def is_built(self) -> bool:
        return self._graph is not None

    @property
    def node_count(self) -> int:
        return self._node_count

    @property
    def edge_count(self) -> int:
        return self._edge_count

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

    def get_neighbors(self, note_path: str, hop: int = 2) -> list[NeighborNote]:
        """BFS N-hop neighbor traversal (AC #2, #3, #5)."""
        if self._graph is None:
            return []

        # Normalize: strip .md extension for obsidiantools key matching
        key = note_path
        if key.endswith(".md"):
            key = key[:-3]

        if key not in self._graph:
            logger.debug("wikilink.note_not_found", note_path=note_path)
            return []

        start = time.monotonic()
        neighbors: list[NeighborNote] = []
        visited: set[str] = {key}
        queue: deque[tuple[str, int]] = deque([(key, 0)])

        while queue:
            current, depth = queue.popleft()
            if depth >= hop:
                continue
            for adj in self._graph.neighbors(current):
                if adj in visited:
                    continue
                visited.add(adj)

                fm = self._get_frontmatter(adj)
                neighbors.append(
                    NeighborNote(
                        title=adj,
                        path=self._resolve_path(adj),
                        hop_distance=depth + 1,
                        frontmatter=fm,
                    )
                )
                queue.append((adj, depth + 1))

        duration_ms = (time.monotonic() - start) * 1000
        logger.debug(
            "wikilink.get_neighbors",
            note_path=note_path,
            hop=hop,
            neighbor_count=len(neighbors),
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
        }

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
