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


# ════════════════════════════════════════════════════════════════════
# Story 2.1 P1.1 — RetrievalTrace 结构化追踪
# ════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_enrich_returns_trace_with_graph_version():
    """P1.1 — 正常路径下 trace 含 graph_version + included list"""
    mock_service = MagicMock()
    mock_service.is_built = True
    mock_service.build_timestamp = "2026-05-03T10:00:00+00:00"
    mock_service.get_neighbors.return_value = [
        _make_neighbor("X", hop=1, type="concept"),
        _make_neighbor("Y", hop=2, type="concept"),
    ]

    result = await enrich_from_wikilink_graph(
        "节点/Eigenvalues.md", max_hops=2, graph_service=mock_service
    )

    assert result.trace is not None
    assert result.trace.seed == "节点/Eigenvalues.md"
    assert result.trace.max_hops == 2
    assert result.trace.graph_version == "2026-05-03T10:00:00+00:00"
    assert len(result.trace.included) == 2
    assert result.trace.omitted == []
    assert result.trace.degradations == []
    # 每个 included 应有 reason 标记
    for item in result.trace.included:
        assert item.reason in ("frontmatter_link", "wikilink_outgoing")


@pytest.mark.asyncio
async def test_enrich_trace_marks_frontmatter_link_reason():
    """P1.1 — frontmatter relationships[] 显式声明的关系标记 reason='frontmatter_link'"""
    mock_service = MagicMock()
    mock_service.is_built = True
    mock_service.build_timestamp = "2026-05-03T10:00:00+00:00"
    mock_service.get_neighbors.return_value = [
        _make_neighbor(
            "Linear-Independence",
            hop=1,
            relationships=[
                {"type": "prerequisite", "target": "[[Eigenvalues]]"}
            ],
        ),
        _make_neighbor("PlainNeighbor", hop=1, type="concept"),
    ]

    result = await enrich_from_wikilink_graph(
        "节点/Eigenvalues.md", graph_service=mock_service
    )

    by_path = {item.path: item for item in result.trace.included}
    assert by_path["节点/Linear-Independence.md"].reason == "frontmatter_link"
    assert by_path["节点/Linear-Independence.md"].relationship_type == "prerequisite"
    assert by_path["节点/PlainNeighbor.md"].reason == "wikilink_outgoing"
    assert by_path["节点/PlainNeighbor.md"].relationship_type is None


@pytest.mark.asyncio
async def test_enrich_trace_records_degradation_when_graph_unbuilt():
    """P1.1 — graph 未构建时 trace.degradations 列出降级原因"""
    mock_service = MagicMock()
    mock_service.is_built = False
    mock_service.build_timestamp = None

    result = await enrich_from_wikilink_graph(
        "节点/X.md", graph_service=mock_service
    )

    assert result.trace is not None
    assert "wikilink_graph_not_built" in result.trace.degradations
    assert result.trace.included == []
    assert result.trace.graph_version == "unbuilt"


@pytest.mark.asyncio
async def test_enrich_trace_records_degradation_on_unexpected_error():
    """P1.1 — 异常时 trace.degradations 记录 unexpected_error:<ExceptionType>"""
    mock_service = MagicMock()
    mock_service.is_built = True
    mock_service.build_timestamp = "2026-05-03T10:00:00+00:00"
    mock_service.get_neighbors.side_effect = RuntimeError("boom")

    result = await enrich_from_wikilink_graph(
        "节点/X.md", graph_service=mock_service
    )

    assert result.trace is not None
    assert any(
        "RuntimeError" in d for d in result.trace.degradations
    ), result.trace.degradations


# ════════════════════════════════════════════════════════════════════
# Phase 1.7+ Regression — ChatGPT 对抗审查 P0 fixes (2026-05-03)
# ════════════════════════════════════════════════════════════════════


def test_extract_user_callouts_adjacent_callouts_do_not_merge():
    """P0#5 — 相邻 callout 不能被吞进上一个 body."""
    from app.services.wikilink_context_service import _extract_user_callouts

    md = "> [!tip]+ First\n> A\n> [!error]+ Second\n> B\n"
    out = _extract_user_callouts(md)
    assert out == [
        {"kind": "tip", "title": "First", "content": "A"},
        {"kind": "error", "title": "Second", "content": "B"},
    ], out


def test_extract_user_callouts_with_blank_quote_line():
    """P0#5 边界 — 中间空 quote 行不应阻止下一个 callout 识别."""
    from app.services.wikilink_context_service import _extract_user_callouts

    md = "> [!tip]+ First\n> A\n>\n> [!error]+ Second\n> B\n"
    out = _extract_user_callouts(md)
    assert len(out) == 2, out
    assert out[0]["kind"] == "tip"
    assert out[1]["kind"] == "error"
    assert "[!error]" not in out[0]["content"]


def test_extract_user_callouts_three_adjacent():
    """P0#5 边界 — 3 个连续 callout 全部识别."""
    from app.services.wikilink_context_service import _extract_user_callouts

    md = (
        "> [!tip]+ A\n> aa\n"
        "> [!error]+ B\n> bb\n"
        "> [!question]+ C\n> cc\n"
    )
    out = _extract_user_callouts(md)
    assert len(out) == 3, out
    assert [c["kind"] for c in out] == ["tip", "error", "question"]


def test_extract_user_callouts_code_fence_skipped():
    """code fence 内的伪 callout 不应被识别为真 callout."""
    from app.services.wikilink_context_service import _extract_user_callouts

    md = (
        "```md\n"
        "> [!tip]+ fake-in-code\n"
        "> not real\n"
        "```\n"
        "> [!tip]+ real\n"
        "> body\n"
    )
    out = _extract_user_callouts(md)
    assert len(out) == 1, out
    assert out[0]["title"] == "real"


def test_extract_user_callouts_filters_relation_namespace():
    """relation/* callout (Canvas ai-linked-doc 自动派生) 应被过滤."""
    from app.services.wikilink_context_service import _extract_user_callouts

    md = (
        "> [!relation/extends]+ noise\n> ignore\n"
        "> [!tip]+ real\n> keep\n"
    )
    out = _extract_user_callouts(md)
    assert len(out) == 1, out
    assert out[0]["kind"] == "tip"


def test_resolve_vault_md_path_rejects_outside_vault(tmp_path):
    """P0-A — absolute path 在 vault 外应拒绝 (path traversal sandbox)."""
    from app.services.wikilink_context_service import _resolve_vault_md_path

    vault = tmp_path / "vault"
    vault.mkdir()
    inside = vault / "节点"
    inside.mkdir()
    inside_file = inside / "ok.md"
    inside_file.write_text("# OK", encoding="utf-8")

    outside = tmp_path / "outside.md"
    outside.write_text("# secret", encoding="utf-8")

    assert _resolve_vault_md_path(str(inside_file), str(vault)) == inside_file.resolve()
    assert _resolve_vault_md_path(str(outside), str(vault)) is None


def test_resolve_vault_md_path_rejects_dotdot_escape(tmp_path):
    """P0-A — `../../etc/passwd` 风格相对路径应拒绝."""
    from app.services.wikilink_context_service import _resolve_vault_md_path

    vault = tmp_path / "vault"
    vault.mkdir()
    target = tmp_path / "secret.md"
    target.write_text("secret", encoding="utf-8")

    # 即使相对路径用 .. 逃逸到 vault 外, resolve + relative_to 必须拒绝
    assert _resolve_vault_md_path("../secret.md", str(vault)) is None


def test_resolve_vault_md_path_rejects_non_md(tmp_path):
    """P0-A — 非 .md 后缀应拒绝 (即使在 vault 内)."""
    from app.services.wikilink_context_service import _resolve_vault_md_path

    vault = tmp_path / "vault"
    vault.mkdir()
    yaml_file = vault / "config.yaml"
    yaml_file.write_text("password: secret", encoding="utf-8")

    assert _resolve_vault_md_path(str(yaml_file), str(vault)) is None


def test_resolve_vault_md_path_rejects_oversized(tmp_path):
    """P0-A — 超过 1MB 的 .md 应拒绝 (防 DoS)."""
    from app.services.wikilink_context_service import (
        _MAX_NEIGHBOR_MD_BYTES,
        _resolve_vault_md_path,
    )

    vault = tmp_path / "vault"
    vault.mkdir()
    big = vault / "huge.md"
    big.write_text("a" * (_MAX_NEIGHBOR_MD_BYTES + 100), encoding="utf-8")

    assert _resolve_vault_md_path(str(big), str(vault)) is None
