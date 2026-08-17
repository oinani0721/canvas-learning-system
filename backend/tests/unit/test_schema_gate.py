"""R10 复审 P2-02 — canvas schema gate 三态行为测试."""

from __future__ import annotations

from typing import Any

import pytest

from app.services.schema_gate import (
    REQUIRED_CANVAS_CONSTRAINTS,
    CanvasSchemaGate,
)


class _FakeResult:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    async def data(self) -> list[dict[str, Any]]:
        return self._rows


class _FakeSession:
    def __init__(self, rows: list[dict[str, Any]], fail: bool = False) -> None:
        self._rows = rows
        self._fail = fail

    async def run(self, query: str, **params: Any) -> _FakeResult:
        if self._fail:
            raise ConnectionError("neo4j down")
        return _FakeResult(self._rows)

    async def __aenter__(self) -> "_FakeSession":
        return self

    async def __aexit__(self, *args: Any) -> None:
        return None


class _FakeDriver:
    def __init__(self, rows: list[dict[str, Any]], fail: bool = False) -> None:
        self.rows = rows
        self.fail = fail

    def session(self, database: str | None = None) -> _FakeSession:
        return _FakeSession(self.rows, fail=self.fail)


def _gate_with(rows: list[dict[str, Any]], fail: bool = False) -> CanvasSchemaGate:
    gate = CanvasSchemaGate()
    gate._driver = _FakeDriver(rows, fail=fail)  # type: ignore[assignment]
    return gate


_ALL_PRESENT = [{"name": n} for n in REQUIRED_CANVAS_CONSTRAINTS]


class TestSchemaGate:
    @pytest.mark.asyncio
    async def test_all_present_passes(self) -> None:
        gate = _gate_with(_ALL_PRESENT)
        assert await gate.verify() is True
        assert await gate.block_reason() is None

    @pytest.mark.asyncio
    async def test_missing_constraint_blocks_with_name(self) -> None:
        """确认缺失 → 拦, 且文案指明缺哪条 + 修法."""
        rows = [{"name": "canvasnode_group_id_unique"}]  # 只有 1/3
        gate = _gate_with(rows)
        assert await gate.verify() is False
        reason = await gate.block_reason()
        assert reason is not None
        assert "canvasboard_group_id_unique" in reason
        assert "migrate_canvas_group_isolation" in reason  # 给出修法

    @pytest.mark.asyncio
    async def test_db_unreachable_is_unknown_not_blocking(self) -> None:
        """未知态不拦 — DB 不可达时写入自身就会 503, gate 只拦「连上了
        且确认缺约束」这一 gate 独有信息."""
        gate = _gate_with([], fail=True)
        assert await gate.verify() is None
        assert await gate.block_reason() is None

    @pytest.mark.asyncio
    async def test_unknown_state_retries_and_recovers(self) -> None:
        """启动时 DB 没起 → 未知; 之后 DB 起来 → block_reason 重验并按
        实际约束态裁决 (覆盖重建 volume 零约束窗口)."""
        gate = _gate_with([], fail=True)
        assert await gate.verify() is None
        # DB 恢复, 但 volume 是新的 (零约束)
        gate._driver = _FakeDriver([])  # type: ignore[assignment]
        reason = await gate.block_reason()
        assert reason is not None  # 重验后确认缺失 → 拦
        # 补齐约束后恢复放行
        gate._driver = _FakeDriver(_ALL_PRESENT)  # type: ignore[assignment]
        assert await gate.verify() is True
        assert await gate.block_reason() is None
