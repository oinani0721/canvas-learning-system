"""Story 2.5 Task 4 — 错误双写单元测试.

覆盖:
- AC #4: frontmatter `errors[]` 追加 (双标签 D 方案)
- Task 4.5: 原子写入 (临时文件 + os.replace)
- AC #6: Graphiti 失败重试 + frontmatter 仍成功 (本地优先)
- write_error_dual fire-and-forget
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
import yaml

from app.graphiti.entity_types import (
    ErrorType,
    PedagogyErrorType,
    RemedyStrategy,
)
from app.services.error_classifier import ClassifiedError
from app.services.error_writer import (
    GRAPHITI_MAX_RETRIES,
    write_error_dual,
    write_error_to_frontmatter,
    write_error_to_graphiti,
)


def _make_error(**overrides) -> ClassifiedError:
    """构造测试用 ClassifiedError."""
    base = {
        "legacy_type": ErrorType.KNOWLEDGE_GAP,
        "pedagogy_type": PedagogyErrorType.CONCEPTUAL_CONFUSION,
        "description": "学生混淆了 X 和 Y",
        "context": "对话第 2 轮",
        "confidence": 0.85,
        "legacy_remedy": RemedyStrategy.BACKTRACK_DEFINITION,
        "pedagogy_remedies": [RemedyStrategy.DISCRIMINATION_COMPARISON],
        "sub_tags": ["synonym_confusion"],
    }
    base.update(overrides)
    return ClassifiedError(**base)


# ════════════════════════════════════════════════════════════════════
# write_error_to_frontmatter (Task 4.1, 4.5)
# ════════════════════════════════════════════════════════════════════


def test_frontmatter_appends_to_existing_errors_list(tmp_path):
    """已有 errors[] → 追加新条."""
    f = tmp_path / "node.md"
    f.write_text(
        "---\n"
        "type: concept\n"
        "errors:\n"
        "  - type: careless_slip\n"
        "    description: 旧错误\n"
        "    corrected_at: null\n"
        "---\n"
        "# Body\n",
        encoding="utf-8",
    )

    error = _make_error()
    ok, error_id = write_error_to_frontmatter(f, error)
    assert ok is True
    assert error_id is not None  # Story 2.5 HIGH#10 fix — id 必须返回

    new_text = f.read_text(encoding="utf-8")
    fm_dict = yaml.safe_load(new_text.split("---")[1])
    assert len(fm_dict["errors"]) == 2
    assert fm_dict["errors"][0]["description"] == "旧错误"
    assert fm_dict["errors"][1]["type"] == "conceptual_confusion"
    assert fm_dict["errors"][1]["legacy_type"] == "knowledge_gap"
    assert fm_dict["errors"][1]["confidence"] == 0.85
    assert "discrimination_comparison" in fm_dict["errors"][1]["remedy_strategies"]
    assert fm_dict["errors"][1]["id"] == error_id  # HIGH#10 fix — id 写入


def test_frontmatter_creates_errors_list_when_missing(tmp_path):
    """无 errors[] 字段 → 新建并追加."""
    f = tmp_path / "node.md"
    f.write_text(
        "---\ntype: concept\n---\n# Body\n",
        encoding="utf-8",
    )

    error = _make_error()
    ok, error_id = write_error_to_frontmatter(f, error)
    assert ok is True
    assert error_id is not None

    new_text = f.read_text(encoding="utf-8")
    fm_dict = yaml.safe_load(new_text.split("---")[1])
    assert isinstance(fm_dict["errors"], list)
    assert len(fm_dict["errors"]) == 1
    assert fm_dict["errors"][0]["type"] == "conceptual_confusion"
    assert fm_dict["errors"][0]["id"] == error_id


def test_frontmatter_preserves_body_unchanged(tmp_path):
    """frontmatter 写入不破坏 body."""
    f = tmp_path / "node.md"
    body = "# Heading\n\nSome body content with `code` and **bold**.\n\n## H2\n"
    f.write_text(f"---\ntype: concept\n---\n{body}", encoding="utf-8")

    write_error_to_frontmatter(f, _make_error())
    new_text = f.read_text(encoding="utf-8")
    assert body in new_text


def test_frontmatter_file_not_found_returns_false(tmp_path):
    """文件不存在 → (False, None) (不抛异常)."""
    f = tmp_path / "missing.md"
    ok, error_id = write_error_to_frontmatter(f, _make_error())
    assert ok is False
    assert error_id is None


def test_frontmatter_atomic_no_temp_left_on_success(tmp_path):
    """原子写入: 成功后无临时文件残留."""
    f = tmp_path / "node.md"
    f.write_text("---\ntype: concept\n---\n# Body\n", encoding="utf-8")

    write_error_to_frontmatter(f, _make_error())

    leftover = list(tmp_path.glob(".node.md.tmp*"))
    assert leftover == [], f"原子写入失败留下临时文件: {leftover}"


def test_frontmatter_double_label_fields_present(tmp_path):
    """D 方案: 双标签 (legacy_type + pedagogy_type) 都写入."""
    f = tmp_path / "node.md"
    f.write_text("---\ntype: concept\n---\n# Body\n", encoding="utf-8")

    error = _make_error(
        legacy_type=ErrorType.SUPERFICIAL,
        pedagogy_type=PedagogyErrorType.METACOGNITIVE_ERROR,
        legacy_remedy=RemedyStrategy.DISCRIMINATION_TRANSFER,
        pedagogy_remedies=[RemedyStrategy.TRANSFER_SELF_EXPLANATION],
        sub_tags=["transfer_failure"],
    )
    write_error_to_frontmatter(f, error)

    fm_dict = yaml.safe_load(f.read_text().split("---")[1])
    err_record = fm_dict["errors"][0]
    assert err_record["type"] == "metacognitive_error"  # PRD pedagogy
    assert err_record["legacy_type"] == "superficial"  # Story 3.6 兼容
    assert err_record["tags"] == ["transfer_failure"]
    assert err_record["remedy_strategies"] == ["transfer_self_explanation"]


# ════════════════════════════════════════════════════════════════════
# write_error_to_graphiti (Task 4.2, 4.3, 4.4)
# ════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_graphiti_success_first_attempt():
    """memory_service 第一次调用成功 → 返回 True."""
    error = _make_error()

    mock_memory_svc = AsyncMock()
    mock_memory_svc.record_knowledge_entity = AsyncMock(return_value=None)

    with patch(
        "app.services.memory_service.get_memory_service",
        new=AsyncMock(return_value=mock_memory_svc),
    ):
        ok = await write_error_to_graphiti(error, node_id="节点/X.md")

    assert ok is True
    mock_memory_svc.record_knowledge_entity.assert_called_once()


@pytest.mark.asyncio
async def test_graphiti_returns_false_on_memory_service_unavailable():
    """memory_service import / instantiate 失败 → False (Graceful)."""
    error = _make_error()

    with patch(
        "app.services.memory_service.get_memory_service",
        new=AsyncMock(side_effect=ImportError("graphiti not installed")),
    ):
        ok = await write_error_to_graphiti(error, node_id="x")

    assert ok is False


@pytest.mark.asyncio
async def test_graphiti_retries_3_times_then_returns_false():
    """所有重试都失败 → 返回 False, 调用 3 次 (AC #6)."""
    error = _make_error()

    mock_memory_svc = AsyncMock()
    mock_memory_svc.record_knowledge_entity = AsyncMock(
        side_effect=RuntimeError("Neo4j down")
    )

    with patch(
        "app.services.memory_service.get_memory_service",
        new=AsyncMock(return_value=mock_memory_svc),
    ), patch("app.services.error_writer.GRAPHITI_RETRY_INTERVAL_S", 0.001):
        ok = await write_error_to_graphiti(error, node_id="x")

    assert ok is False
    assert mock_memory_svc.record_knowledge_entity.call_count == GRAPHITI_MAX_RETRIES


@pytest.mark.asyncio
async def test_graphiti_succeeds_after_retry():
    """前 N-1 次失败, 最后一次成功 → True (重试机制有效)."""
    error = _make_error()

    call_count = [0]

    async def _mock_call(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] < 2:
            raise RuntimeError("transient")
        return None

    mock_memory_svc = AsyncMock()
    mock_memory_svc.record_knowledge_entity = AsyncMock(side_effect=_mock_call)

    with patch(
        "app.services.memory_service.get_memory_service",
        new=AsyncMock(return_value=mock_memory_svc),
    ), patch("app.services.error_writer.GRAPHITI_RETRY_INTERVAL_S", 0.001):
        ok = await write_error_to_graphiti(error, node_id="x")

    assert ok is True
    assert call_count[0] == 2


# ════════════════════════════════════════════════════════════════════
# write_error_dual (双写入口)
# ════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_dual_write_frontmatter_success_graphiti_scheduled(tmp_path):
    """frontmatter 成功 + fire-and-forget Graphiti task scheduled."""
    f = tmp_path / "node.md"
    f.write_text("---\ntype: concept\n---\n# Body\n", encoding="utf-8")

    mock_memory_svc = AsyncMock()
    mock_memory_svc.record_knowledge_entity = AsyncMock(return_value=None)

    with patch(
        "app.services.memory_service.get_memory_service",
        new=AsyncMock(return_value=mock_memory_svc),
    ):
        result = await write_error_dual(
            f, _make_error(), node_id="x", session_id="s1",
            mode="write_confirmed",
        )

    assert result["frontmatter"] is True
    assert result["graphiti"] == "queued"  # HIGH#5 fix: scheduled → queued
    assert result["error_id"] is not None  # HIGH#10 fix


@pytest.mark.asyncio
async def test_dual_write_skips_graphiti_when_frontmatter_fails(tmp_path):
    """frontmatter 失败 (文件不存在) → Graphiti skipped."""
    missing = tmp_path / "missing.md"

    mock_memory_svc = AsyncMock()
    mock_memory_svc.record_knowledge_entity = AsyncMock()

    with patch(
        "app.services.memory_service.get_memory_service",
        new=AsyncMock(return_value=mock_memory_svc),
    ):
        result = await write_error_dual(
            missing, _make_error(), node_id="x",
            mode="write_confirmed",
        )

    assert result["frontmatter"] is False
    assert result["graphiti"] == "skipped_frontmatter_failed"
    mock_memory_svc.record_knowledge_entity.assert_not_called()


@pytest.mark.asyncio
async def test_dual_write_sync_mode_returns_graphiti_status(tmp_path):
    """同步模式 (fire_and_forget=False) 返回 graphiti ok/failed."""
    f = tmp_path / "node.md"
    f.write_text("---\ntype: concept\n---\n# Body\n", encoding="utf-8")

    mock_memory_svc = AsyncMock()
    mock_memory_svc.record_knowledge_entity = AsyncMock(return_value=None)

    with patch(
        "app.services.memory_service.get_memory_service",
        new=AsyncMock(return_value=mock_memory_svc),
    ):
        result = await write_error_dual(
            f,
            _make_error(),
            node_id="x",
            fire_and_forget_graphiti=False,
            mode="write_confirmed",
        )

    assert result["frontmatter"] is True
    assert result["graphiti"] == "ok"


# ════════════════════════════════════════════════════════════════════
# Story 2.5 ChatGPT 二轮审查 P0/HIGH regression (2026-05-04)
# ════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_concurrent_writes_no_data_loss(tmp_path):
    """P0#3 — per-file lock 防 read-modify-write 竞态丢数据.

    并发 N 个 record_error 写同一文件, errors[] 应有 N 条 (无丢失).
    """
    import asyncio as _asyncio

    from app.services.error_writer import write_error_dual

    f = tmp_path / "concurrent.md"
    f.write_text("---\ntype: concept\n---\n# Body\n", encoding="utf-8")

    mock_memory_svc = AsyncMock()
    mock_memory_svc.record_knowledge_entity = AsyncMock(return_value=None)

    errors = [
        _make_error(description=f"错误 {i}", confidence=0.7 + i * 0.01)
        for i in range(10)
    ]

    with patch(
        "app.services.memory_service.get_memory_service",
        new=AsyncMock(return_value=mock_memory_svc),
    ):
        # 10 个并发 write
        results = await _asyncio.gather(
            *[
                write_error_dual(
                    f, err, node_id=f"node-{i}", session_id="s",
                    fire_and_forget_graphiti=True,
                    mode="write_confirmed",
                )
                for i, err in enumerate(errors)
            ]
        )

    # 所有 frontmatter 都成功
    assert all(r["frontmatter"] for r in results)
    # 所有 error_id 唯一
    error_ids = [r["error_id"] for r in results]
    assert len(set(error_ids)) == 10, f"id 重复: {error_ids}"

    # frontmatter errors[] 应有 10 条
    fm_dict = yaml.safe_load(f.read_text().split("---")[1])
    assert len(fm_dict["errors"]) == 10, (
        f"并发写丢数据: 期望 10, 实际 {len(fm_dict['errors'])}"
    )


def test_frontmatter_dedupe_same_error_updates_seen_count(tmp_path):
    """HIGH#11 — 同 (pedagogy_type, description, node_id) 错误重复时更新 seen_count."""
    f = tmp_path / "dedupe.md"
    f.write_text("---\ntype: concept\n---\n# Body\n", encoding="utf-8")

    error = _make_error()

    # 写 3 次同样的错误
    ok1, id1 = write_error_to_frontmatter(f, error, node_id_for_dedupe="x")
    ok2, id2 = write_error_to_frontmatter(f, error, node_id_for_dedupe="x")
    ok3, id3 = write_error_to_frontmatter(f, error, node_id_for_dedupe="x")

    assert ok1 and ok2 and ok3
    # 同错误返回同 id
    assert id1 == id2 == id3

    fm_dict = yaml.safe_load(f.read_text().split("---")[1])
    # errors[] 应只有 1 条 (无限增长被防住)
    assert len(fm_dict["errors"]) == 1
    assert fm_dict["errors"][0]["seen_count"] == 3
    assert fm_dict["errors"][0]["id"] == id1


def test_frontmatter_legacy_remedy_field_present(tmp_path):
    """MEDIUM#13 — frontmatter 同时写 legacy_remedy + pedagogy_remedies."""
    f = tmp_path / "node.md"
    f.write_text("---\ntype: concept\n---\n# Body\n", encoding="utf-8")

    error = _make_error()  # KNOWLEDGE_GAP (legacy) → CONCEPTUAL_CONFUSION (pedagogy)

    write_error_to_frontmatter(f, error)
    fm_dict = yaml.safe_load(f.read_text().split("---")[1])
    rec = fm_dict["errors"][0]

    # MEDIUM#13: legacy_remedy 不丢
    assert rec["legacy_remedy"] == "backtrack_definition"
    # pedagogy_remedies 也存在
    assert "discrimination_comparison" in rec["remedy_strategies"]


@pytest.mark.asyncio
async def test_dual_write_sync_mode_graphiti_failed(tmp_path):
    """同步模式 + Graphiti 失败 → graphiti=failed (frontmatter 仍 True)."""
    f = tmp_path / "node.md"
    f.write_text("---\ntype: concept\n---\n# Body\n", encoding="utf-8")

    with patch(
        "app.services.memory_service.get_memory_service",
        new=AsyncMock(side_effect=ImportError("graphiti unavailable")),
    ):
        result = await write_error_dual(
            f,
            _make_error(),
            node_id="x",
            fire_and_forget_graphiti=False,
            mode="write_confirmed",
        )

    assert result["frontmatter"] is True  # AC #6: 本地优先
    assert result["graphiti"] == "failed"
