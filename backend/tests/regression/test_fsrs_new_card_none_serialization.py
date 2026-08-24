# CARD-A1 回归锁定 (BATCH-2026-08-24-复习闭环)
# [Source: _bmad-output/implementation-artifacts/goal-cards/2026-08-24-第一批小goal卡-复习闭环.md#CARD-A1]
"""fsrs 6.3.1 新卡 None 序列化回归测试。

fsrs 6.x 语义: Card() 新卡的 stability/difficulty == None（从未复习、无记忆参数）。
旧代码用 hasattr() 守卫——属性存在但值为 None，守卫失效，float(None) → TypeError。

锁定 4 个崩溃点（全部真实 fsrs 6.3.1 对象，禁 mock）:
  1. fsrs_manager.serialize_card(新卡) 无异常，None 序列化为 JSON null 并可 roundtrip；
  2. fsrs_manager.card_to_state(新卡) 无异常，None 不被写死 0.0；
  3. review_service.schedule_review(新卡) algorithm=="fsrs-4.5"，
     不因 f-string 格式化 None 崩溃而静默降级 Ebbinghaus；
  4. review_service.get_fsrs_state(新概念) found=True（Story 38.3 AC-4 自动建卡）。

None 语义分层（设计要点）:
  - 持久化层 (card_data / card_state JSON): None ↔ null 严格 roundtrip，
    禁止写死 0.0（scheduler 会把 stability=0.0 当成已学卡）；
  - API 展示层 (get_fsrs_state 返回 dict 的 stability/difficulty 字段):
    None → 展示默认值（FSRSStateResponse schema 要求 float 且 difficulty>=1）。
"""

import asyncio
import json
import sys
import uuid
from pathlib import Path

import pytest

# Add backend/lib to path for imports (同 tests/unit/test_fsrs_manager.py 约定)
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from memory.temporal.fsrs_manager import FSRS_AVAILABLE, FSRSManager  # noqa: E402

pytestmark = pytest.mark.skipif(
    not FSRS_AVAILABLE, reason="需要真实 py-fsrs 库（本回归禁 mock/fallback）"
)


@pytest.fixture
def fsrs_manager():
    """真实 FSRSManager（内部持有真实 fsrs.Scheduler）。"""
    return FSRSManager()


@pytest.fixture
def review_service(tmp_path, monkeypatch):
    """真实依赖组装的 ReviewService。

    不 mock 任何行为——CanvasService/BackgroundTaskManager/FSRSManager 全部真实实例；
    仅将卡片状态持久化文件重定向到 tmp_path（测试卫生，真实文件 I/O 仍然发生）。
    """
    import app.services.review_service as rs_module

    monkeypatch.setattr(
        rs_module, "_CARD_STATES_FILE", tmp_path / "fsrs_card_states.json"
    )

    from app.services.background_task_manager import BackgroundTaskManager
    from app.services.canvas_service import CanvasService

    return rs_module.ReviewService(
        canvas_service=CanvasService(canvas_base_path=str(tmp_path)),
        task_manager=BackgroundTaskManager(),
    )


def test_new_card_semantics_precondition():
    """前置锁定: fsrs 6.3.1 新卡 stability/difficulty 就是 None（不是 0.0）。

    如果未来升级 fsrs 后此断言失败，说明库语义又变了，
    本文件其余断言的前提需要重新评估。
    """
    from fsrs import Card

    card = Card()
    assert card.stability is None
    assert card.difficulty is None
    assert card.last_review is None


def test_serialize_card_new_card_roundtrip(fsrs_manager):
    """崩溃点 1: serialize_card(新卡) 无异常; None → JSON null → roundtrip 还原 None。"""
    card = fsrs_manager.create_card()

    card_json = fsrs_manager.serialize_card(card)  # 旧代码此处 float(None) TypeError

    payload = json.loads(card_json)
    assert payload["stability"] is None, "新卡 stability 必须序列化为 null, 不许写死 0.0"
    assert payload["difficulty"] is None, "新卡 difficulty 必须序列化为 null, 不许写死 0.0"

    restored = fsrs_manager.deserialize_card(card_json)
    assert restored.stability is None, "roundtrip 后 None 必须还原, 否则新卡被当成已学卡"
    assert restored.difficulty is None
    assert restored.due == card.due
    assert int(restored.state) == int(card.state)
    # fsrs 6.x Card 无 reps/lapses 属性 (hasattr 兜底 0), 只锁序列化字段
    assert payload["reps"] == 0
    assert payload["lapses"] == 0
    assert restored.last_review is None


def test_serialize_card_reviewed_card_keeps_real_values(fsrs_manager):
    """守护既有行为: 已复习卡的真实数值不受 None 修复影响。"""
    card = fsrs_manager.create_card()
    card, _log = fsrs_manager.review_card(card, 3)  # Rating.Good
    assert card.stability is not None

    restored = fsrs_manager.deserialize_card(fsrs_manager.serialize_card(card))
    assert abs(restored.stability - card.stability) < 1e-9
    assert abs(restored.difficulty - card.difficulty) < 1e-9


def test_card_to_state_new_card_no_exception(fsrs_manager):
    """崩溃点 2: card_to_state(新卡) 无异常; CardState 保留 None 而非写死 0.0。"""
    card = fsrs_manager.create_card()

    state = fsrs_manager.card_to_state(  # 旧代码此处 float(None) TypeError
        card, concept="card-a1-concept", canvas_file="card-a1.canvas"
    )

    assert state.stability is None, "CardState.stability 不许把新卡写死成 0.0"
    assert state.difficulty is None
    assert state.card_data is not None

    # to_dict/from_dict/state_to_card 全链 roundtrip 仍保 None
    restored_state = type(state).from_dict(state.to_dict())
    assert restored_state.stability is None
    restored_card = fsrs_manager.state_to_card(restored_state)
    assert restored_card.stability is None
    assert restored_card.difficulty is None


@pytest.mark.asyncio
async def test_schedule_review_new_card_uses_fsrs_not_ebbinghaus(review_service):
    """崩溃点 3: 新卡走 FSRS 主路径, 不因日志格式化 None 崩溃而静默降级。"""
    concept_id = f"card-a1-schedule-{uuid.uuid4().hex}"

    result = await review_service.schedule_review(
        "card-a1-canvas", concept_id=concept_id
    )

    assert result["algorithm"] == "fsrs-4.5", (
        "新卡必须走 FSRS-4.5; algorithm==ebbinghaus-fallback 说明 "
        "f-string 格式化 None 的 TypeError 又被 except 吞掉静默降级了"
    )
    # 返回的 card_data 保持新卡 null 语义
    payload = json.loads(result["card_data"])
    assert payload["stability"] is None
    assert payload["difficulty"] is None


@pytest.mark.asyncio
async def test_get_fsrs_state_new_concept_found_true(review_service):
    """崩溃点 4: 新概念自动建卡成功 (Story 38.3 AC-4), found=True 非 error 兜底。"""
    concept_id = f"card-a1-state-{uuid.uuid4().hex}"

    tasks_before = set(asyncio.all_tasks())
    result = await review_service.get_fsrs_state(concept_id)
    # 事件循环卫生: 立即取消 get_fsrs_state 派生的 fire-and-forget Graphiti
    # 持久化任务, 防止测试写真实图库 (create_task 后无 await 点, 任务尚未起步)
    for task in asyncio.all_tasks() - tasks_before:
        if not task.done():
            task.cancel()

    assert result["found"] is True, (
        "新概念必须自动建卡 found=True; found=False 说明 serialize_card(新卡) "
        "的 TypeError 又被 except 吞掉走了 error 兜底"
    )
    assert "error" not in result.get("reason", ""), f"不应走 error 兜底: {result}"

    # 持久化层: card_state JSON 保留 null (roundtrip 权威数据)
    card_payload = json.loads(result["card_state"])
    assert card_payload["stability"] is None
    assert card_payload["difficulty"] is None

    # API 展示层: schema 兼容 float (FSRSStateResponse 要求 difficulty>=1)
    assert isinstance(result["stability"], float)
    assert isinstance(result["difficulty"], float)
    assert result["difficulty"] >= 1

    # 自动建卡已入内存缓存: 二次查询命中同一张卡
    tasks_before = set(asyncio.all_tasks())
    second = await review_service.get_fsrs_state(concept_id)
    for task in asyncio.all_tasks() - tasks_before:
        if not task.done():
            task.cancel()
    assert second["found"] is True
    assert second["card_state"] == result["card_state"]
