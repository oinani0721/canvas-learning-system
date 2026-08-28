# CARD-G4-2 (BATCH-2026-08-28-第五批) — 统一四态值域契约.
"""service_status 四态值域契约测试.

锁三件事:
1. ``ServiceStatus`` 枚举值域与 ``SERVICE_STATUS_VALUES`` 权威元组一致;
2. ``CanvasRAGState.retrieval_status`` 的 Literal 镜像与枚举值域逐值一致
   (防两侧漂移 — Literal 加值/枚举加值必须同步, 否则本测试红);
3. ``StatusedResult`` 构造校验: unavailable/degraded 必须带 reason,
   ok/empty 禁止带 reason (故障必须可诊断, 非故障不得伪装故障).
"""

from __future__ import annotations

import pytest

from app.models.service_status import (
    SERVICE_STATUS_VALUES,
    ServiceStatus,
    StatusedResult,
    fold_overall_status,
    max_severity,
)


class TestEnumValueDomain:
    def test_enum_matches_authority_tuple(self):
        assert tuple(s.value for s in ServiceStatus) == SERVICE_STATUS_VALUES

    def test_four_states_exact(self):
        assert SERVICE_STATUS_VALUES == ("ok", "empty", "degraded", "unavailable")

    def test_canvas_rag_state_literal_mirrors_enum(self):
        """CanvasRAGState.retrieval_status 的 Literal 值域 == 枚举值域。"""
        import typing

        from agentic_rag.state import CanvasRAGState

        hints = typing.get_type_hints(CanvasRAGState, include_extras=True)
        assert "retrieval_status" in hints, (
            "CanvasRAGState 缺 retrieval_status 字段 (G4-2 加性字段)"
        )
        annotated = hints["retrieval_status"]
        # Annotated[Optional[Literal[...]], desc] → 剥到 Literal args
        inner = typing.get_args(annotated)[0]  # Optional[Literal[...]]
        literal = next(
            a for a in typing.get_args(inner) if typing.get_origin(a) is typing.Literal
        )
        assert set(typing.get_args(literal)) == set(SERVICE_STATUS_VALUES), (
            f"Literal 镜像漂移: {typing.get_args(literal)} != {SERVICE_STATUS_VALUES}"
        )


class TestStatusedResultContract:
    def test_unavailable_requires_reason(self):
        with pytest.raises(ValueError):
            StatusedResult(status=ServiceStatus.UNAVAILABLE)

    def test_degraded_requires_reason(self):
        with pytest.raises(ValueError):
            StatusedResult(status=ServiceStatus.DEGRADED, items=[1])

    def test_empty_rejects_reason(self):
        with pytest.raises(ValueError):
            StatusedResult(status=ServiceStatus.EMPTY, reason="should not be here")

    def test_ok_rejects_reason(self):
        with pytest.raises(ValueError):
            StatusedResult(status=ServiceStatus.OK, items=[1], reason="nope")

    def test_blank_reason_rejected_for_unavailable(self):
        with pytest.raises(ValueError):
            StatusedResult(status=ServiceStatus.UNAVAILABLE, reason="   ")

    def test_from_items_ok_vs_empty(self):
        assert StatusedResult.from_items([1]).status is ServiceStatus.OK
        empty = StatusedResult.from_items([])
        assert empty.status is ServiceStatus.EMPTY
        assert empty.reason is None

    def test_from_items_rejects_none(self):
        """Codex round-1 MEDIUM-12: None 通常是「调用失败」而非「空结果」,
        当成可信 EMPTY 正是本卡要消灭的伪装 (原测试把它锁成了 EMPTY)。"""
        with pytest.raises(ValueError):
            StatusedResult.from_items(None)

    def test_ok_requires_non_empty_payload(self):
        with pytest.raises(ValueError):
            StatusedResult(status=ServiceStatus.OK, items=[])

    def test_empty_rejects_payload(self):
        with pytest.raises(ValueError):
            StatusedResult(status=ServiceStatus.EMPTY, items=[1])

    def test_unavailable_rejects_payload(self):
        """unavailable 不得夹带部分结果 — 那是 degraded 的语义."""
        with pytest.raises(ValueError):
            StatusedResult(status=ServiceStatus.UNAVAILABLE, items=[1], reason="x")

    def test_non_list_payload_rejected(self):
        with pytest.raises(TypeError):
            StatusedResult(status=ServiceStatus.OK, items="not a list")

    def test_non_str_reason_rejected(self):
        with pytest.raises(ValueError):
            StatusedResult(status=ServiceStatus.UNAVAILABLE, reason=object())

    def test_payload_is_copied_not_aliased(self):
        """frozen=True 挡不住 items.append() — 构造时复制隔断外部引用."""
        src = [1]
        result = StatusedResult.from_items(src)
        src.append(2)
        assert result.items == [1]

    def test_unavailable_items_always_empty(self):
        r = StatusedResult.unavailable("neo4j down")
        assert r.items == []
        assert r.reason == "neo4j down"
        assert not r.is_trustworthy

    def test_degraded_keeps_partial_items(self):
        r = StatusedResult.degraded([1, 2], "graphiti timeout, fulltext only")
        assert r.status is ServiceStatus.DEGRADED
        assert r.items == [1, 2]
        assert r.is_trustworthy

    def test_bare_str_status_coerced(self):
        r = StatusedResult(status="ok", items=[1])
        assert r.status is ServiceStatus.OK

    def test_to_dict_omits_reason_when_none(self):
        assert "reason" not in StatusedResult.from_items([1]).to_dict()
        assert StatusedResult.unavailable("x").to_dict()["reason"] == "x"


class TestMaxSeverity:
    """组件级严重度排序 (MEDIUM-15 更名: 它**不是**整体结果折算)."""

    def test_bare_str_input_returns_enum(self):
        """裸 str 输入不得让返回类型漂移成 str."""
        result = max_severity("ok", "degraded")
        assert result is ServiceStatus.DEGRADED

    def test_empty_input_rejected(self):
        with pytest.raises(ValueError):
            max_severity()

    def test_severity_order(self):
        assert (
            max_severity(ServiceStatus.OK, ServiceStatus.EMPTY)
            is ServiceStatus.EMPTY
        )
        assert (
            max_severity(ServiceStatus.EMPTY, ServiceStatus.DEGRADED)
            is ServiceStatus.DEGRADED
        )
        assert (
            max_severity(
                ServiceStatus.OK, ServiceStatus.UNAVAILABLE, ServiceStatus.DEGRADED
            )
            is ServiceStatus.UNAVAILABLE
        )


class TestFoldOverallStatus:
    """整体四态折算 — 与 memory_service / fuse_results 手写口径同源。

    Codex round-1 MEDIUM-15: `max_severity` 只排严重度, 用它做整体折算
    会把「一个源挂了但另一个源健康地返回了结果」说成 unavailable。
    """

    def test_failure_with_results_is_degraded(self):
        assert (
            fold_overall_status(has_results=True, failed_sources=1, healthy_sources=0)
            is ServiceStatus.DEGRADED
        )

    def test_failure_without_results_but_healthy_source_is_degraded(self):
        """另一个源健康地查到 0 条 —— 检索系统没挂, 只是这一路缺了。"""
        assert (
            fold_overall_status(has_results=False, failed_sources=1, healthy_sources=1)
            is ServiceStatus.DEGRADED
        )

    def test_all_sources_failed_no_results_is_unavailable(self):
        assert (
            fold_overall_status(has_results=False, failed_sources=2, healthy_sources=0)
            is ServiceStatus.UNAVAILABLE
        )

    def test_clean_with_results_is_ok(self):
        assert (
            fold_overall_status(has_results=True, failed_sources=0, healthy_sources=2)
            is ServiceStatus.OK
        )

    def test_clean_without_results_is_empty(self):
        assert (
            fold_overall_status(has_results=False, failed_sources=0, healthy_sources=2)
            is ServiceStatus.EMPTY
        )
