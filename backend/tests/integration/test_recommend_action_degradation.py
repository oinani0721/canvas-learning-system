"""
Story 31.A.9: 推荐降级 UI 指示器后端集成测试 — recommend-action 端点降级

验证 POST /api/v1/agents/recommend-action 端点在 memory_service 不可用时
仍然能正确返回基于分数的推荐结果（优雅降级）。

可追溯性映射 (支撑 Story 31.10 — 推荐降级模式 UI 指示器):
- AC-31.10.1 (降级标签触发条件) → test_recommend_action_graceful_on_memory_failure
  当 memory_service 失败时，端点仍返回 200 且 action 有效 → 前端判定为正常推荐
- AC-31.10.2 (正常推荐) → test_recommend_action_success_format
  正常情况下端点返回完整推荐 → 前端正常渲染
- AC-31.10.5 (回退逻辑不变) → test_recommend_action_response_matches_schema
  无论是否降级，响应格式完全一致 → 前端无需特殊处理

前端测试 (已存在, 13 个测试):
- canvas-progress-tracker/obsidian-plugin/tests/ScoringResultPanel.test.ts
  覆盖 AC-31.10.1~8 前端渲染逻辑

[Source: docs/stories/31.A.9.story.md]
[Source: docs/stories/31.10.story.md]
[Source: docs/stories/31.3.story.md - recommend-action 原始实现]
"""

import logging
from unittest.mock import AsyncMock

import pytest
from app.config import Settings, get_settings
from app.main import app
from app.services.memory_service import get_memory_service
from fastapi.testclient import TestClient

logger = logging.getLogger(__name__)


# ============================================================================
# Test Settings & DI Overrides
# ============================================================================


def _test_settings() -> Settings:
    """Override settings for testing."""
    return Settings(
        canvas_base_path=".",
        GEMINI_API_KEY="",
        NEO4J_URI="",
    )


def _make_mock_memory_service(*, fail_history: bool = False):
    """Create a mock MemoryService with configurable behavior.

    Args:
        fail_history: If True, get_learning_history raises RuntimeError.
    """
    mock = AsyncMock()
    if fail_history:
        mock.get_learning_history = AsyncMock(
            side_effect=RuntimeError("Memory service unavailable (test)")
        )
    else:
        mock.get_learning_history = AsyncMock(
            return_value={
                "items": [
                    {"score": 70, "timestamp": "2026-02-10T10:00:00Z"},
                    {"score": 65, "timestamp": "2026-02-10T09:00:00Z"},
                    {"score": 80, "timestamp": "2026-02-10T08:00:00Z"},
                ],
                "total": 3,
            }
        )
    return mock


# ============================================================================
# AC-31.A.9.3: recommend-action 端点降级测试
# ============================================================================


class TestRecommendActionDegradation:
    """Story 31.A.9 AC-3: 验证 recommend-action 端点在 Agent/Memory 不可用时的行为。

    支撑 Story 31.10 AC-31.10.1 (降级标签触发条件)。

    recommend-action 端点降级链:
      POST /api/v1/agents/recommend-action
        → request.include_history=True
        → memory_service.get_learning_history() 失败
        → except: history_context = None (优雅降级)
        → 基于纯 score 的推荐 (无历史参考)
        → 返回 200 + 有效推荐
    """

    def test_recommend_action_graceful_on_memory_failure(self):
        """Memory 不可用时端点优雅降级 — 仍返回基于分数的有效推荐.

        端点代码 (agents.py:1870-1873):
          except Exception as e:
              logger.warning(f"Failed to get learning history: {e}")
              history_context = None
        """
        mock_memory = _make_mock_memory_service(fail_history=True)

        app.dependency_overrides[get_settings] = _test_settings
        app.dependency_overrides[get_memory_service] = lambda: mock_memory
        try:
            with TestClient(app) as client:
                response = client.post(
                    "/api/v1/agents/recommend-action",
                    json={
                        "score": 75,
                        "node_id": "test_node_1",
                        "canvas_name": "test_canvas",
                        "include_history": True,
                    },
                )
            assert response.status_code == 200
            data = response.json()
            # 即使 memory 失败，也返回有效推荐
            assert "action" in data
            assert data["action"] in ("decompose", "explain", "next")
            assert "reason" in data
            assert len(data["reason"]) > 0
            # history_context 应为 None (降级)
            assert data.get("history_context") is None
        finally:
            app.dependency_overrides.pop(get_settings, None)
            app.dependency_overrides.pop(get_memory_service, None)

    def test_recommend_action_success_format(self):
        """Memory 正常时端点返回完整推荐 + history_context.

        score=75 → action="explain" (60-79 range per AC-31.3.3)
        """
        mock_memory = _make_mock_memory_service(fail_history=False)

        app.dependency_overrides[get_settings] = _test_settings
        app.dependency_overrides[get_memory_service] = lambda: mock_memory
        try:
            with TestClient(app) as client:
                response = client.post(
                    "/api/v1/agents/recommend-action",
                    json={
                        "score": 75,
                        "node_id": "test_node_2",
                        "canvas_name": "test_canvas",
                        "include_history": True,
                    },
                )
            assert response.status_code == 200
            data = response.json()
            assert data["action"] == "explain"  # 60-79 → explain
            assert "reason" in data
            assert data["priority"] in (1, 2, 3, 4, 5)
        finally:
            app.dependency_overrides.pop(get_settings, None)
            app.dependency_overrides.pop(get_memory_service, None)

    def test_recommend_action_response_matches_schema(self):
        """无论降级与否，响应格式与 RecommendActionResponse schema 一致.

        验证所有 schema 必需字段存在且类型正确。
        """
        mock_memory = _make_mock_memory_service(fail_history=False)

        app.dependency_overrides[get_settings] = _test_settings
        app.dependency_overrides[get_memory_service] = lambda: mock_memory
        try:
            with TestClient(app) as client:
                response = client.post(
                    "/api/v1/agents/recommend-action",
                    json={
                        "score": 45,
                        "node_id": "test_node_3",
                        "canvas_name": "test_canvas",
                        "include_history": False,
                    },
                )
            assert response.status_code == 200
            data = response.json()

            # RecommendActionResponse schema 必需字段
            assert "action" in data
            assert "agent" in data or data.get("action") == "next"  # agent=null for "next"
            assert "reason" in data
            assert "priority" in data
            assert "review_suggested" in data
            assert "alternative_agents" in data

            # 类型验证
            assert isinstance(data["action"], str)
            assert isinstance(data["reason"], str)
            assert isinstance(data["priority"], int)
            assert isinstance(data["review_suggested"], bool)
            assert isinstance(data["alternative_agents"], list)
            # agent is Optional[str] — null for "next", string for others
            if data.get("agent") is not None:
                assert isinstance(data["agent"], str)

            # action 枚举值验证
            assert data["action"] in ("decompose", "explain", "next")

            # score < 60 → decompose
            assert data["action"] == "decompose"
        finally:
            app.dependency_overrides.pop(get_settings, None)
            app.dependency_overrides.pop(get_memory_service, None)

    def test_recommend_action_score_thresholds(self):
        """验证三个分数阈值对应的推荐 action.

        AC-31.3.3 score-based recommendation:
        - score < 60 → decompose
        - score 60-79 → explain
        - score >= 80 → next
        """
        mock_memory = _make_mock_memory_service(fail_history=False)

        app.dependency_overrides[get_settings] = _test_settings
        app.dependency_overrides[get_memory_service] = lambda: mock_memory
        try:
            with TestClient(app) as client:
                # Low score → decompose
                resp_low = client.post(
                    "/api/v1/agents/recommend-action",
                    json={
                        "score": 30,
                        "node_id": "node_low",
                        "canvas_name": "test",
                        "include_history": False,
                    },
                )
                assert resp_low.json()["action"] == "decompose"

                # Medium score → explain
                resp_mid = client.post(
                    "/api/v1/agents/recommend-action",
                    json={
                        "score": 65,
                        "node_id": "node_mid",
                        "canvas_name": "test",
                        "include_history": False,
                    },
                )
                assert resp_mid.json()["action"] == "explain"

                # High score → next
                resp_high = client.post(
                    "/api/v1/agents/recommend-action",
                    json={
                        "score": 90,
                        "node_id": "node_high",
                        "canvas_name": "test",
                        "include_history": False,
                    },
                )
                assert resp_high.json()["action"] == "next"
        finally:
            app.dependency_overrides.pop(get_settings, None)
            app.dependency_overrides.pop(get_memory_service, None)
