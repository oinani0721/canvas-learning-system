"""Story 2.1 Task 5.1 — wikilink_context_service 单元测试。

覆盖 AC #1（N-hop 遍历）+ AC #2（关系类型提取）+ AC #5（降级处理）。
"""

from unittest.mock import MagicMock

import pytest

from app.services.wikilink_context_service import (
    DEFAULT_MAX_HOPS,
    DEFAULT_TIMEOUT_MS,
    EnrichmentResult,
    WikilinkNeighborContext,
    _extract_relationship_type,
    _normalize_target_slug,
    enrich_from_wikilink_graph,
)
from app.services.wikilink_graph_service import NeighborNote


def _make_neighbor(
    title: str = "Eigenvalues", hop: int = 1, **fm
) -> NeighborNote:
    return NeighborNote(
        title=title,
        path=f"节点/{title}.md",
        hop_distance=hop,
        frontmatter=fm,
    )


# ════════════════════════════════════════════════════════════════════
# _normalize_target_slug
# ════════════════════════════════════════════════════════════════════


def test_normalize_target_slug_with_md_suffix():
    assert _normalize_target_slug("节点/Eigenvalues.md") == "Eigenvalues"


def test_normalize_target_slug_no_md_suffix():
    assert _normalize_target_slug("节点/Eigenvalues") == "Eigenvalues"


def test_normalize_target_slug_no_path():
    assert _normalize_target_slug("Eigenvalues.md") == "Eigenvalues"


def test_normalize_target_slug_chinese():
    assert _normalize_target_slug("节点/特征值.md") == "特征值"


# ════════════════════════════════════════════════════════════════════
# _extract_relationship_type
# ════════════════════════════════════════════════════════════════════


def test_extract_relationship_type_match():
    fm = {
        "relationships": [
            {"type": "refines", "target": "[[Fundamentals]]"},
        ]
    }
    assert _extract_relationship_type(fm, "Fundamentals") == "refines"


def test_extract_relationship_type_multiple_only_first_match():
    fm = {
        "relationships": [
            {"type": "prerequisite", "target": "[[Fundamentals]]"},
            {"type": "refines", "target": "[[Other]]"},
        ]
    }
    assert _extract_relationship_type(fm, "Fundamentals") == "prerequisite"


def test_extract_relationship_type_no_match():
    fm = {
        "relationships": [
            {"type": "refines", "target": "[[OtherNote]]"},
        ]
    }
    assert _extract_relationship_type(fm, "Fundamentals") is None


def test_extract_relationship_type_no_relationships_field():
    fm = {"type": "concept", "mastery_score": 0.5}
    assert _extract_relationship_type(fm, "Fundamentals") is None


def test_extract_relationship_type_malformed_not_list():
    fm = {"relationships": "not a list"}
    assert _extract_relationship_type(fm, "Fundamentals") is None


def test_extract_relationship_type_malformed_item_not_dict():
    fm = {"relationships": ["not a dict", 42, None]}
    assert _extract_relationship_type(fm, "Fundamentals") is None


def test_extract_relationship_type_missing_type_field():
    fm = {"relationships": [{"target": "[[Fundamentals]]"}]}
    assert _extract_relationship_type(fm, "Fundamentals") is None


# ════════════════════════════════════════════════════════════════════
# enrich_from_wikilink_graph — 正常 + 降级路径
# ════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_enrich_normal_2hop():
    """AC #1 — 正常 2-hop 遍历返回邻居列表"""
    mock_service = MagicMock()
    mock_service.is_built = True
    mock_service.get_neighbors.return_value = [
        _make_neighbor("Linear-Independence", hop=1, type="concept"),
        _make_neighbor("Determinant", hop=1, type="concept"),
        _make_neighbor("Matrix-Rank", hop=2, type="concept"),
    ]

    result = await enrich_from_wikilink_graph(
        "节点/Eigenvalues.md", max_hops=2, graph_service=mock_service
    )

    assert isinstance(result, EnrichmentResult)
    assert result.degraded is False
    assert result.degraded_reason is None
    assert len(result.neighbors) == 3
    # 排序后 1-hop 在前（按 hop + slug 排序）
    assert result.neighbors[0].hop_distance == 1
    assert result.neighbors[2].hop_distance == 2
    assert result.elapsed_ms > 0


@pytest.mark.asyncio
async def test_enrich_returns_wikilink_context_dataclass():
    mock_service = MagicMock()
    mock_service.is_built = True
    mock_service.get_neighbors.return_value = [
        _make_neighbor("X", hop=1, type="concept", mastery_score=0.5),
    ]

    result = await enrich_from_wikilink_graph(
        "节点/Y.md", graph_service=mock_service
    )
    n = result.neighbors[0]
    assert isinstance(n, WikilinkNeighborContext)
    assert n.slug == "X"
    assert n.path == "节点/X.md"
    assert n.hop_distance == 1
    assert n.frontmatter == {"type": "concept", "mastery_score": 0.5}
    assert n.content_summary is None


@pytest.mark.asyncio
async def test_enrich_relationship_type_extracted():
    """AC #2 — relationship_type 从 frontmatter relationships[] 提取"""
    mock_service = MagicMock()
    mock_service.is_built = True
    mock_service.get_neighbors.return_value = [
        _make_neighbor(
            "Linear-Independence",
            hop=1,
            relationships=[
                {"type": "prerequisite", "target": "[[Eigenvalues]]"}
            ],
        ),
    ]

    result = await enrich_from_wikilink_graph(
        "节点/Eigenvalues.md", graph_service=mock_service
    )

    assert result.neighbors[0].relationship_type == "prerequisite"


@pytest.mark.asyncio
async def test_enrich_graph_not_built_degraded():
    """AC #5 — 图未构建 → degraded"""
    mock_service = MagicMock()
    mock_service.is_built = False

    result = await enrich_from_wikilink_graph(
        "节点/X.md", graph_service=mock_service
    )

    assert result.degraded is True
    assert result.degraded_reason == "wikilink_graph_not_built"
    assert result.neighbors == []


@pytest.mark.asyncio
async def test_enrich_empty_neighbors_not_degraded():
    """孤立节点（无邻居）不算降级"""
    mock_service = MagicMock()
    mock_service.is_built = True
    mock_service.get_neighbors.return_value = []

    result = await enrich_from_wikilink_graph(
        "节点/Isolated.md", graph_service=mock_service
    )

    assert result.degraded is False
    assert result.neighbors == []


@pytest.mark.asyncio
async def test_enrich_unexpected_error_degraded():
    """AC #5 — 异常 → degraded + 不抛"""
    mock_service = MagicMock()
    mock_service.is_built = True
    mock_service.get_neighbors.side_effect = RuntimeError("graph corruption")

    result = await enrich_from_wikilink_graph(
        "节点/X.md", graph_service=mock_service
    )

    assert result.degraded is True
    assert result.degraded_reason is not None
    assert "unexpected_error" in result.degraded_reason
    assert "RuntimeError" in result.degraded_reason
    assert result.neighbors == []


@pytest.mark.asyncio
async def test_enrich_default_params():
    """默认 max_hops + timeout_ms 常量"""
    assert DEFAULT_MAX_HOPS == 2
    assert DEFAULT_TIMEOUT_MS == 200


@pytest.mark.asyncio
async def test_enrich_neighbors_sorted_by_hop_then_slug():
    """邻居按 (hop_distance, slug) 升序"""
    mock_service = MagicMock()
    mock_service.is_built = True
    mock_service.get_neighbors.return_value = [
        _make_neighbor("Zebra", hop=2),
        _make_neighbor("Apple", hop=1),
        _make_neighbor("Mango", hop=1),
    ]

    result = await enrich_from_wikilink_graph(
        "节点/X.md", graph_service=mock_service
    )

    slugs = [n.slug for n in result.neighbors]
    assert slugs == ["Apple", "Mango", "Zebra"]
