"""
Story 31.A.9: 推荐降级 UI 指示器后端集成测试 — 降级标志传播

验证 VerificationService.process_answer() 在不同降级场景下
正确设置 degraded 标志并返回完整响应格式。

可追溯性映射 (支撑 Story 31.10 — 推荐降级模式 UI 指示器):
- AC-31.10.1 (降级标签) → test_degraded_true_when_agent_unavailable
- AC-31.10.2 (正常标签) → test_degraded_false_when_agent_succeeds
- AC-31.10.3 (重试能力) → test_degraded_true_when_agent_timeout
- AC-31.10.4 (样式一致性) → N/A (前端 Jest 测试覆盖: ScoringResultPanel.test.ts)
- AC-31.10.5 (回退逻辑不变) → test_degraded_response_has_required_fields

前端测试 (已存在, 13 个测试):
- canvas-progress-tracker/obsidian-plugin/tests/ScoringResultPanel.test.ts
  覆盖 AC-31.10.1~8 前端渲染逻辑

[Source: docs/stories/31.A.9.story.md]
[Source: docs/stories/31.10.story.md]
"""

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.verification_service import VerificationService


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def temp_canvas_dir(tmp_path: Path) -> Path:
    """Create a temp directory with a valid .canvas file containing red/purple nodes."""
    canvas_data = {
        "nodes": [
            {
                "id": "node_red_1",
                "type": "text",
                "text": "微积分基本定理",
                "color": "4",
                "x": 0,
                "y": 0,
                "width": 200,
                "height": 100,
            },
            {
                "id": "node_purple_1",
                "type": "text",
                "text": "极限的定义",
                "color": "3",
                "x": 250,
                "y": 0,
                "width": 200,
                "height": 100,
            },
            {
                "id": "node_green_1",
                "type": "text",
                "text": "加法运算",
                "color": "2",
                "x": 500,
                "y": 0,
                "width": 200,
                "height": 100,
            },
        ],
        "edges": [],
    }
    canvas_file = tmp_path / "test.canvas"
    canvas_file.write_text(json.dumps(canvas_data, ensure_ascii=False), encoding="utf-8")
    return tmp_path


@pytest.fixture
def verification_service_no_agent(temp_canvas_dir: Path) -> VerificationService:
    """VerificationService with agent_service=None → forces degradation path."""
    return VerificationService(
        agent_service=None,
        canvas_base_path=str(temp_canvas_dir),
    )


@pytest.fixture
def verification_service_with_agent(temp_canvas_dir: Path) -> VerificationService:
    """VerificationService with a mock agent_service that returns success."""
    mock_agent = MagicMock()
    mock_agent.call_scoring = AsyncMock(
        return_value=MagicMock(
            success=True,
            data={"total_score": 75.0},
        )
    )
    return VerificationService(
        agent_service=mock_agent,
        canvas_base_path=str(temp_canvas_dir),
    )


@pytest.fixture
def verification_service_timeout(temp_canvas_dir: Path) -> VerificationService:
    """VerificationService with agent that always times out."""
    mock_agent = MagicMock()
    mock_agent.call_scoring = AsyncMock(side_effect=asyncio.TimeoutError)
    return VerificationService(
        agent_service=mock_agent,
        canvas_base_path=str(temp_canvas_dir),
    )


# ============================================================================
# AC-31.A.9.1: process_answer 降级标志测试
# ============================================================================


class TestDegradedFlagPropagation:
    """Story 31.A.9 AC-1: 验证 degraded 标志在 process_answer 中正确设置和传播。

    支撑 Story 31.10 AC-31.10.1 (降级标签) 的后端前置条件。

    降级触发链:
      process_answer() → _evaluate_answer_with_scoring_agent()
        → agent 不可用 → _mock_evaluate_answer() → degraded=True
    """

    @pytest.mark.asyncio
    async def test_degraded_true_when_agent_unavailable(
        self, verification_service_no_agent: VerificationService
    ):
        """AC-31.10.1 后端前置: Agent 不可用时 degraded=True.

        触发路径: _do_scoring_agent_call() → self._agent_service is None
          → fallback → _mock_evaluate_answer() → (quality, score, True, "agent_unavailable")
        """
        session = await verification_service_no_agent.start_session(
            canvas_name="test",
        )
        result = await verification_service_no_agent.process_answer(
            session["session_id"], "这是一个关于微积分基本定理的详细回答" * 5
        )
        assert result["degraded"] is True

    @pytest.mark.asyncio
    async def test_degraded_false_when_agent_succeeds(
        self, verification_service_with_agent: VerificationService
    ):
        """AC-31.10.2 后端前置: Agent 正常时 degraded=False.

        触发路径: _do_scoring_agent_call() → call_scoring() returns success
          → (quality, raw_score, False, None)
        """
        session = await verification_service_with_agent.start_session(
            canvas_name="test",
        )
        result = await verification_service_with_agent.process_answer(
            session["session_id"], "这是一个关于微积分基本定理的详细回答" * 5
        )
        assert result["degraded"] is False

    @pytest.mark.asyncio
    async def test_degraded_true_when_agent_timeout(
        self, verification_service_timeout: VerificationService
    ):
        """AC-31.10.3 后端前置: Agent 超时时 degraded=True.

        触发路径: _evaluate_answer_with_scoring_agent()
          → asyncio.wait_for() raises TimeoutError
          → _mock_evaluate_answer() → (quality, score, True)
        """
        session = await verification_service_timeout.start_session(
            canvas_name="test",
        )
        result = await verification_service_timeout.process_answer(
            session["session_id"], "这是一个关于微积分基本定理的详细回答" * 5
        )
        assert result["degraded"] is True


# ============================================================================
# AC-31.A.9.2: process_answer 降级响应格式完整性
# ============================================================================


class TestDegradedResponseFormat:
    """Story 31.A.9 AC-2: 验证降级响应包含前端 ScoringResultPanel 需要的所有字段。

    支撑 Story 31.10 AC-31.10.5 (回退逻辑不变): 确保降级响应格式与正常响应一致，
    前端 ScoringResultPanel 无需特殊处理不同格式。
    """

    @pytest.mark.asyncio
    async def test_degraded_response_has_required_fields(
        self, verification_service_no_agent: VerificationService
    ):
        """降级响应包含前端 ScoringResultPanel 需要的 score, degraded, action 字段."""
        session = await verification_service_no_agent.start_session(
            canvas_name="test",
        )
        result = await verification_service_no_agent.process_answer(
            session["session_id"], "这是一个关于微积分基本定理的详细回答" * 5
        )
        # 前端 ScoringResultPanel 依赖这些字段
        assert "score" in result
        assert "degraded" in result
        assert "action" in result
        assert "quality" in result
        assert "progress" in result
        assert isinstance(result["score"], (int, float))
        assert 0 <= result["score"] <= 100

    @pytest.mark.asyncio
    async def test_degraded_score_is_reasonable(
        self, verification_service_no_agent: VerificationService
    ):
        """Mock 评分的基本合理性: 短答案分数 < 长答案分数.

        _mock_evaluate_answer 基于字符长度:
        - < 20 chars → 20.0 (wrong)
        - 20-50 chars → 50.0 (partial)
        - 50-100 chars → 70.0 (good)
        - > 100 chars → 90.0 (excellent)
        """
        # 短答案 (< 20 chars)
        session_short = await verification_service_no_agent.start_session(
            canvas_name="test",
        )
        result_short = await verification_service_no_agent.process_answer(
            session_short["session_id"], "短"
        )

        # 长答案 (> 100 chars)
        session_long = await verification_service_no_agent.start_session(
            canvas_name="test",
        )
        result_long = await verification_service_no_agent.process_answer(
            session_long["session_id"], "这是一个非常详细和完整的回答，涵盖了微积分基本定理的所有核心要素和推导过程，包括连续性条件和极限定义" * 3
        )

        assert result_short["degraded"] is True
        assert result_long["degraded"] is True
        assert result_short["score"] < result_long["score"]
