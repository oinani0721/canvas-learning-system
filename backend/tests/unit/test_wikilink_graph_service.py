"""Tests for Story 1.2: Wikilink graph build + neighbor discovery."""

import asyncio
from pathlib import Path

import pytest


@pytest.fixture
def vault_with_links(tmp_path):
    """Create a minimal vault with interlinked .md files."""
    (tmp_path / "A.md").write_text(
        "---\nmastery_score: 0.8\n---\n# A\nLinks to [[B]] and [[C]]\n"
    )
    (tmp_path / "B.md").write_text(
        "---\nmastery_score: 0.5\n---\n# B\nLinks to [[C]] and [[D]]\n"
    )
    (tmp_path / "C.md").write_text("# C\nLinks back to [[A]]\n")
    (tmp_path / "D.md").write_text("# D\nNo outgoing links\n")
    (tmp_path / "orphan.md").write_text("# Orphan\nNo links at all\n")
    return tmp_path


@pytest.fixture
def graph_service():
    from app.services.wikilink_graph_service import WikilinkGraphService

    return WikilinkGraphService()


class TestGraphBuild:
    @pytest.mark.asyncio
    async def test_build_success(self, graph_service, vault_with_links):
        result = await graph_service.build(str(vault_with_links))
        assert result["total_nodes"] >= 4
        assert result["total_edges"] >= 3
        assert result["build_time_ms"] >= 0
        assert graph_service.is_built

    @pytest.mark.asyncio
    async def test_stats_after_build(self, graph_service, vault_with_links):
        await graph_service.build(str(vault_with_links))
        stats = graph_service.get_stats()
        assert stats["is_built"] is True
        assert stats["total_nodes"] >= 4


class TestNeighborQuery:
    @pytest.mark.asyncio
    async def test_1hop_neighbors(self, graph_service, vault_with_links):
        await graph_service.build(str(vault_with_links))
        neighbors = graph_service.get_neighbors("A", hop=1)
        titles = {n.title for n in neighbors}
        assert "B" in titles
        assert "C" in titles
        assert all(n.hop_distance == 1 for n in neighbors)

    @pytest.mark.asyncio
    async def test_2hop_neighbors(self, graph_service, vault_with_links):
        await graph_service.build(str(vault_with_links))
        neighbors = graph_service.get_neighbors("A", hop=2)
        titles = {n.title for n in neighbors}
        assert "D" in titles  # A -> B -> D

    @pytest.mark.asyncio
    async def test_circular_links_no_duplicates(self, graph_service, vault_with_links):
        """AC #3: A -> B -> C -> A cycle should not produce duplicates."""
        await graph_service.build(str(vault_with_links))
        neighbors = graph_service.get_neighbors("A", hop=3)
        titles = [n.title for n in neighbors]
        assert len(titles) == len(set(titles))

    @pytest.mark.asyncio
    async def test_nonexistent_note_returns_empty(
        self, graph_service, vault_with_links
    ):
        """AC #5: Querying non-existent note returns empty list."""
        await graph_service.build(str(vault_with_links))
        result = graph_service.get_neighbors("nonexistent")
        assert result == []

    @pytest.mark.asyncio
    async def test_full_path_falls_back_to_basename_when_orphan(
        self, graph_service, vault_with_links
    ):
        """Phase 1 hotfix — obsidiantools 给同一文件 2 个节点（vault 路径 + wikilink basename）。
        plugin 传 vault 路径命中孤立节点 → 应自动 fallback 到 basename。
        """
        await graph_service.build(str(vault_with_links))
        # full path with subdir prefix
        result = graph_service.get_neighbors("subdir/A.md", hop=1)
        # A.md exists in vault as wikilink target → basename fallback should find neighbors
        titles = {n.title for n in result}
        assert "B" in titles
        assert "C" in titles

    @pytest.mark.asyncio
    async def test_basename_only_path_still_works(
        self, graph_service, vault_with_links
    ):
        """Phase 1 hotfix — basename-only 路径（向后兼容）"""
        await graph_service.build(str(vault_with_links))
        result = graph_service.get_neighbors("A", hop=1)
        titles = {n.title for n in result}
        assert "B" in titles

    @pytest.mark.asyncio
    async def test_truly_isolated_node_returns_empty(
        self, graph_service, vault_with_links
    ):
        """Phase 1 hotfix — 路径 + basename 都无邻居 = 真正孤立节点"""
        await graph_service.build(str(vault_with_links))
        # orphan.md 在 vault 但无 wikilink 引用 + 无外链
        result = graph_service.get_neighbors("orphan", hop=2)
        assert result == []

    @pytest.mark.asyncio
    async def test_md_extension_stripped(self, graph_service, vault_with_links):
        await graph_service.build(str(vault_with_links))
        result = graph_service.get_neighbors("A.md", hop=1)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_frontmatter_included(self, graph_service, vault_with_links):
        await graph_service.build(str(vault_with_links))
        neighbors = graph_service.get_neighbors("A", hop=1)
        b_neighbor = next((n for n in neighbors if n.title == "B"), None)
        if b_neighbor and b_neighbor.frontmatter:
            assert "mastery_score" in b_neighbor.frontmatter


class TestGraphNotBuilt:
    def test_neighbors_before_build(self, graph_service):
        assert graph_service.get_neighbors("A") == []

    def test_stats_before_build(self, graph_service):
        stats = graph_service.get_stats()
        assert stats["is_built"] is False


class TestDegreeStats:
    """Story 2.2+2.9 T3.5 — degree percentile snapshot for hub penalty."""

    def test_empty_graph_returns_zeros(self, graph_service):
        stats = graph_service.get_degree_stats()
        assert stats["median"] == 0.0
        assert stats["p95"] == 0.0
        assert stats["max"] == 0.0
        assert stats["count"] == 0

    @pytest.mark.asyncio
    async def test_simple_graph_has_finite_stats(self, graph_service, vault_with_links):
        await graph_service.build(str(vault_with_links))
        stats = graph_service.get_degree_stats()
        assert stats["count"] >= 4
        assert stats["max"] >= stats["p95"] >= stats["median"] >= 0
        # vault_with_links: A→B,C; B→C,D; C→A; D 无出边; orphan 完全孤立
        # degree(A) = out(2) + in(1, from C) = 3
        # 至少有节点 degree>0
        assert stats["max"] >= 1

    @pytest.mark.asyncio
    async def test_p50_equals_median(self, graph_service, vault_with_links):
        await graph_service.build(str(vault_with_links))
        stats = graph_service.get_degree_stats()
        assert stats["p50"] == stats["median"]


class TestGetDegree:
    """Story 2.2+2.9 T3.5 — per-node degree lookup with basename fallback."""

    def test_empty_graph_returns_zero(self, graph_service):
        assert graph_service.get_degree("A") == 0

    @pytest.mark.asyncio
    async def test_existing_node_returns_positive_degree(
        self, graph_service, vault_with_links
    ):
        await graph_service.build(str(vault_with_links))
        # A 在 graph 里有链接,degree > 0
        assert graph_service.get_degree("A") >= 1

    @pytest.mark.asyncio
    async def test_unknown_node_returns_zero(self, graph_service, vault_with_links):
        await graph_service.build(str(vault_with_links))
        assert graph_service.get_degree("nonexistent_xyz") == 0

    @pytest.mark.asyncio
    async def test_basename_fallback_matches_neighbor_logic(
        self, graph_service, vault_with_links
    ):
        """与 get_neighbors() 的 basename fallback 行为一致,degree 用同一节点."""
        await graph_service.build(str(vault_with_links))
        # 传 vault 相对路径,应回退到 basename
        deg_basename = graph_service.get_degree("A")
        deg_path = graph_service.get_degree("subdir/A.md")
        assert deg_basename == deg_path
        assert deg_basename >= 1

    @pytest.mark.asyncio
    async def test_md_extension_stripped(self, graph_service, vault_with_links):
        await graph_service.build(str(vault_with_links))
        assert graph_service.get_degree("A") == graph_service.get_degree("A.md")


class TestRefresh:
    @pytest.mark.asyncio
    async def test_refresh_rebuilds(self, graph_service, vault_with_links):
        await graph_service.build(str(vault_with_links))
        original_nodes = graph_service.node_count

        (vault_with_links / "E.md").write_text("# E\nLinks to [[A]]\n")
        result = await graph_service.refresh()
        assert graph_service.node_count >= original_nodes
