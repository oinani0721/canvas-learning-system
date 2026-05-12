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


class TestMultiVaultIsolation:
    """P0-1 hotfix (2026-05-11) — per-vault singleton isolation.

    回归 Story 2.5.Y 留下的串库风险:旧 module-level Optional 单例在
    多 vault 并发场景下,第一个 vault build 后的 graph 被永久 cache,
    其余 vault 全用错的 graph.新实现按 sanitized vault key 分桶.
    """

    @pytest.fixture(autouse=True)
    def _clear_caches(self):
        from app.services.wikilink_graph_service import clear_all_caches

        clear_all_caches()
        yield
        clear_all_caches()

    @pytest.fixture
    def vault_a(self, tmp_path):
        vault = tmp_path / "vault_a"
        vault.mkdir()
        (vault / "Alpha.md").write_text("# Alpha\nLinks to [[Beta]]\n")
        (vault / "Beta.md").write_text("# Beta\n")
        return vault

    @pytest.fixture
    def vault_b(self, tmp_path):
        vault = tmp_path / "vault_b"
        vault.mkdir()
        (vault / "Gamma.md").write_text("# Gamma\nLinks to [[Delta]] and [[Epsilon]]\n")
        (vault / "Delta.md").write_text("# Delta\nLinks to [[Epsilon]]\n")
        (vault / "Epsilon.md").write_text("# Epsilon\n")
        return vault

    @pytest.mark.asyncio
    async def test_per_vault_isolation(self, vault_a, vault_b):
        """set ContextVar vault_A → build graph A → ContextVar vault_B → build
        graph B → 两个 service instance 不同,各自 node_count 独立."""
        from app.core.subject_config import (
            _current_subject_id,
            set_current_subject_id,
        )
        from app.services.wikilink_graph_service import (
            get_cache_stats,
            get_wikilink_graph_service,
        )

        # Vault A 上下文
        token_a = _current_subject_id.set("vault_A_test")
        try:
            svc_a = get_wikilink_graph_service()
            await svc_a.build(str(vault_a))
            assert svc_a.is_built
            nodes_a = svc_a.node_count
            assert nodes_a >= 2
        finally:
            _current_subject_id.reset(token_a)

        # Vault B 上下文 — 必须拿到不同 instance
        token_b = _current_subject_id.set("vault_B_test")
        try:
            svc_b = get_wikilink_graph_service()
            assert svc_b is not svc_a, (
                "P0-1 violation: 两个 vault 拿到同一 WikilinkGraphService instance"
            )
            await svc_b.build(str(vault_b))
            assert svc_b.is_built
            nodes_b = svc_b.node_count
            assert nodes_b >= 3
            # 两个 vault 的 node_count 独立(B 比 A 多)
            assert nodes_b > nodes_a
        finally:
            _current_subject_id.reset(token_b)

        # 回到 Vault A 上下文 — 应拿回原 instance, A 的 graph 未被 B 覆盖
        token_c = _current_subject_id.set("vault_A_test")
        try:
            svc_a_again = get_wikilink_graph_service()
            assert svc_a_again is svc_a, "vault_A 第二次 lookup 应返回同一 instance"
            assert svc_a_again.node_count == nodes_a, (
                "vault_A 的 node_count 被 vault_B build 污染了"
            )
        finally:
            _current_subject_id.reset(token_c)

        # cache_stats 应记录两个 vault
        stats = get_cache_stats()
        assert stats["total_vaults"] >= 2
        assert "vault_a_test" in stats["vaults"]
        assert "vault_b_test" in stats["vaults"]

    @pytest.mark.asyncio
    async def test_no_contextvar_uses_default_key(self, vault_a):
        """ContextVar 未设(或为 DEFAULT_SUBJECT_ID)→ 落 __default__ slot,正常工作."""
        from app.core.subject_config import (
            DEFAULT_SUBJECT_ID,
            _current_subject_id,
        )
        from app.services.wikilink_graph_service import (
            get_cache_stats,
            get_wikilink_graph_service,
        )

        # 显式 reset 到 DEFAULT_SUBJECT_ID(模拟无请求上下文)
        token = _current_subject_id.set(DEFAULT_SUBJECT_ID)
        try:
            svc = get_wikilink_graph_service()
            await svc.build(str(vault_a))
            assert svc.is_built
            assert svc.node_count >= 2

            # default 桶第二次 lookup 应返回同一 instance
            svc_again = get_wikilink_graph_service()
            assert svc_again is svc

            stats = get_cache_stats()
            # DEFAULT_SUBJECT_ID = "general", sanitize 后 = "general"(非 __default__)
            # 但因 ContextVar default 也是 "general", 落在 "general" 桶
            assert any(k in stats["vaults"] for k in ("general", "__default__")), (
                f"既不在 'general' 也不在 '__default__': {list(stats['vaults'].keys())}"
            )
        finally:
            _current_subject_id.reset(token)

    @pytest.mark.asyncio
    async def test_clear_cache_for_vault(self, vault_a):
        """clear_cache_for_vault 可清掉指定 vault 的 instance,后续 lookup 会重建."""
        from app.core.subject_config import _current_subject_id
        from app.services.wikilink_graph_service import (
            clear_cache_for_vault,
            get_wikilink_graph_service,
        )

        token = _current_subject_id.set("vault_clear_test")
        try:
            svc1 = get_wikilink_graph_service()
            await svc1.build(str(vault_a))

            removed = clear_cache_for_vault("vault_clear_test")
            assert removed is True

            # 不存在的 key 返 False
            assert clear_cache_for_vault("vault_clear_test") is False

            # 重新 lookup 应拿到新 instance
            svc2 = get_wikilink_graph_service()
            assert svc2 is not svc1
            assert not svc2.is_built  # 新 instance 还没 build
        finally:
            _current_subject_id.reset(token)
