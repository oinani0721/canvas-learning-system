"""
5-ge-1 单元测试: CanvasGraphEpisodeV1 统一 schema + narrative + sanitize。

覆盖 AC#7:
  - 7 event_type × 各 1 用例 (schema 合法性)
  - narrative 字段必填 (空 → ValidationError)
  - event_id 确定性 (同输入 → 同 id)
  - sanitize_group_id_for_graphiti 真用 (vault:cs_61b:recursion → vault__cs_61b__recursion)
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.graphiti.canvas_episode import (
    CANVAS_EDGE_TYPE_MAP,
    CANVAS_GRAPH_EDGE_TYPES,
    CalloutPayload,
    CanvasGraphEpisodeV1,
    ContextPayload,
    EventType,
)
from app.graphiti.group_id_compat import sanitize_group_id_for_graphiti
from app.graphiti.narrative_builder import build_narrative

OCCURRED = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def _base(**overrides):
    base = dict(
        occurred_at=OCCURRED,
        vault_id="cs_61b",
        group_id="vault:cs_61b:recursion",
        canvas_path="原白板/递归白板.md",
        node_id="recursion-base-case",
        belief_key="callout:recursion-base-case:abc123",
        context=ContextPayload(
            source_board="递归白板",
            path_trace=["概览", "base case"],
            out_links=["回溯"],
            in_links=["递归总览"],
        ),
        narrative="用户在递归白板对 base case 写下 tip。",
    )
    base.update(overrides)
    return base


# ═══════════════════════════════════════════════════════════════════════════════
# AC#1 — 7 event types
# ═══════════════════════════════════════════════════════════════════════════════


def test_event_type_enum_has_7_values():
    assert {e.value for e in EventType} == {
        "wikilink_added",
        "wikilink_removed",
        "callout_added",
        "callout_updated",
        "callout_removed",
        "calibration_vote",
        "error_marked",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# AC#7 — 7 event_type 各 1 schema 合法性用例 (+ narrative 渲染无异常)
# ═══════════════════════════════════════════════════════════════════════════════


def test_callout_added_valid():
    ep = CanvasGraphEpisodeV1(
        **_base(
            event_type=EventType.CALLOUT_ADDED,
            callout=CalloutPayload(callout_type="tip", text="先想 base case"),
        )
    )
    assert ep.schema_version == "CanvasGraphEpisodeV1"
    assert "[[recursion-base-case]]" in build_narrative(ep)


def test_callout_updated_valid():
    ep = CanvasGraphEpisodeV1(
        **_base(
            event_type=EventType.CALLOUT_UPDATED,
            belief_key="callout:recursion-base-case:abc123",
            callout=CalloutPayload(callout_type="tip", text="改成: base case 要返回值"),
        )
    )
    assert ep.event_type is EventType.CALLOUT_UPDATED
    assert "修改" in build_narrative(ep)


def test_callout_removed_valid():
    ep = CanvasGraphEpisodeV1(
        **_base(
            event_type=EventType.CALLOUT_REMOVED,
            callout=CalloutPayload(callout_type="tip", text="删除的内容"),
        )
    )
    assert "删除" in build_narrative(ep)


def test_wikilink_added_valid():
    ep = CanvasGraphEpisodeV1(
        **_base(
            event_type=EventType.WIKILINK_ADDED,
            source_node_id="recursion",
            target_node_id="base-case",
            relation_type="prerequisite",
            belief_key="edge:recursion:prerequisite:base-case",
        )
    )
    text = build_narrative(ep)
    assert "[[recursion]]" in text and "[[base-case]]" in text and "新增" in text


def test_wikilink_removed_valid():
    ep = CanvasGraphEpisodeV1(
        **_base(
            event_type=EventType.WIKILINK_REMOVED,
            source_node_id="recursion",
            target_node_id="dfs",
            relation_type="related_to",
            belief_key="edge:recursion:related_to:dfs",
        )
    )
    assert "删除" in build_narrative(ep)


def test_calibration_vote_valid():
    ep = CanvasGraphEpisodeV1(
        **_base(
            event_type=EventType.CALIBRATION_VOTE,
            belief_key="calib:q-42:vote-7",
            callout=CalloutPayload(callout_type="note", text="掌握"),
        )
    )
    assert "校准投票" in build_narrative(ep)


def test_error_marked_valid():
    ep = CanvasGraphEpisodeV1(
        **_base(
            event_type=EventType.ERROR_MARKED,
            belief_key="error:recursion-base-case:knowledge_gap",
            callout=CalloutPayload(callout_type="error", text="忘了写 base case"),
        )
    )
    assert "标记了错误" in build_narrative(ep)


# ═══════════════════════════════════════════════════════════════════════════════
# AC#6/#7 — narrative 必填
# ═══════════════════════════════════════════════════════════════════════════════


def test_narrative_empty_string_raises():
    with pytest.raises(ValidationError):
        CanvasGraphEpisodeV1(**_base(event_type=EventType.CALLOUT_ADDED, narrative=""))


def test_narrative_whitespace_only_raises():
    with pytest.raises(ValidationError):
        CanvasGraphEpisodeV1(
            **_base(event_type=EventType.CALLOUT_ADDED, narrative="   ")
        )


def test_narrative_missing_raises():
    args = _base(event_type=EventType.CALLOUT_ADDED)
    del args["narrative"]
    with pytest.raises(ValidationError):
        CanvasGraphEpisodeV1(**args)


# ═══════════════════════════════════════════════════════════════════════════════
# AC#2/#7 — event_id 确定性
# ═══════════════════════════════════════════════════════════════════════════════


def test_event_id_deterministic_same_inputs():
    ep1 = CanvasGraphEpisodeV1(**_base(event_type=EventType.CALLOUT_ADDED))
    ep2 = CanvasGraphEpisodeV1(**_base(event_type=EventType.CALLOUT_ADDED))
    assert ep1.event_id == ep2.event_id
    assert len(ep1.event_id) == 64  # sha256 hex


def test_event_id_differs_on_different_timestamp():
    ep1 = CanvasGraphEpisodeV1(**_base(event_type=EventType.CALLOUT_ADDED))
    ep2 = CanvasGraphEpisodeV1(
        **_base(
            event_type=EventType.CALLOUT_ADDED,
            occurred_at=datetime(2026, 6, 2, tzinfo=timezone.utc),
        )
    )
    assert ep1.event_id != ep2.event_id


def test_compute_event_id_pure_function():
    a = CanvasGraphEpisodeV1.compute_event_id("v", "c.md", "anchor", OCCURRED)
    b = CanvasGraphEpisodeV1.compute_event_id("v", "c.md", "anchor", OCCURRED)
    assert a == b and len(a) == 64


def test_explicit_event_id_preserved():
    ep = CanvasGraphEpisodeV1(
        **_base(event_type=EventType.CALLOUT_ADDED, event_id="my-fixed-id")
    )
    assert ep.event_id == "my-fixed-id"


# ═══════════════════════════════════════════════════════════════════════════════
# AC#7 — sanitize_group_id_for_graphiti 真用
# ═══════════════════════════════════════════════════════════════════════════════


def test_sanitize_group_id_colon_to_double_underscore():
    assert (
        sanitize_group_id_for_graphiti("vault:cs_61b:recursion")
        == "vault__cs_61b__recursion"
    )


def test_sanitize_group_id_single_level():
    assert sanitize_group_id_for_graphiti("vault:cs_61b") == "vault__cs_61b"


# ═══════════════════════════════════════════════════════════════════════════════
# AC#3 — edge type 本体 (新名, 不碰 entity_types.py 同名常量)
# ═══════════════════════════════════════════════════════════════════════════════


def test_canvas_graph_edge_types_has_10():
    # 7 关系型 + 3 自环型
    assert len(CANVAS_GRAPH_EDGE_TYPES) == 10
    assert "Prerequisite" in CANVAS_GRAPH_EDGE_TYPES
    assert "SelfAnnotation" in CANVAS_GRAPH_EDGE_TYPES


def test_canvas_edge_type_map_canvasnode_pair():
    assert ("CanvasNode", "CanvasNode") in CANVAS_EDGE_TYPE_MAP
    assert "Prerequisite" in CANVAS_EDGE_TYPE_MAP[("CanvasNode", "CanvasNode")]
