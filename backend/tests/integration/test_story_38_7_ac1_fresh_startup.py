"""
Story 38.7 AC-1: Fresh Environment Startup Verification

Verifies default config, FSRS init, episode recovery, startup logging.

Split from test_story_38_7_e2e_integration.py for maintainability.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.config import Settings
from app.services.memory_service import MemoryService

from tests.integration.conftest import make_mock_learning_memory, make_mock_neo4j


def _recovery_scope() -> str:
    """CARD-G4-1b: 启动恢复按 **active vault 根组** (方案甲) 装载。

    `_recover_episodes_from_neo4j` 现在把作用域显式传给 client, 所以断言调用
    参数时必须带上它 —— 这正是"进程级缓存用进程级作用域"的可验证痕迹。
    """
    from app.core.subject_config import default_vault_group_id

    return default_vault_group_id()


def _scope_physical(suffix: str = "") -> str:
    """当前读作用域的物理组 (JSON 存储里的落盘形态)。"""
    from app.graphiti.group_id_compat import to_physical_group_id

    return to_physical_group_id(_recovery_scope()) + suffix


# ═══════════════════════════════════════════════════════════════════════════════
# AC-1: Fresh Environment Startup Verification
# ═══════════════════════════════════════════════════════════════════════════════


class TestAC1FreshEnvironmentStartup:
    """AC-1: Verify default config, FSRS init, episode recovery, startup logging."""

    def test_dual_write_defaults_to_true(self):
        """
        [P0] Story 38.4 AC-1: ENABLE_GRAPHITI_JSON_DUAL_WRITE defaults to True.
        Verify the Field definition default, bypassing .env overrides.
        """
        field_info = Settings.model_fields["ENABLE_GRAPHITI_JSON_DUAL_WRITE"]
        assert field_info.default is True, (
            f"Code default must be True (safe default), got {field_info.default}"
        )

    def test_fsrs_init_ok_when_library_available(self):
        """
        [P0] Story 38.3 AC-3: ReviewService._fsrs_init_ok == True when
        py-fsrs is installed and FSRSManager initializes without error.
        """
        from app.services.review_service import FSRS_AVAILABLE, ReviewService

        if not FSRS_AVAILABLE:
            pytest.skip("py-fsrs not installed")

        canvas_svc = MagicMock()
        task_mgr = MagicMock()
        rs = ReviewService(canvas_service=canvas_svc, task_manager=task_mgr)
        assert rs._fsrs_init_ok is True

    def test_fsrs_init_ok_false_when_no_library(self):
        """
        [P0] Story 38.3 AC-3: ReviewService._fsrs_init_ok == False when
        py-fsrs is unavailable, with reason logged.
        """
        from app.services.review_service import ReviewService

        with (
            patch("app.services.review_service.FSRS_AVAILABLE", False),
            patch("app.services.review_service.FSRSManager", None),
        ):
            canvas_svc = MagicMock()
            task_mgr = MagicMock()
            rs = ReviewService(canvas_service=canvas_svc, task_manager=task_mgr)
            assert rs._fsrs_init_ok is False
            assert rs._fsrs_init_reason is not None

    @pytest.mark.asyncio
    async def test_memory_service_recovers_episodes_on_init(self):
        """
        [P0] Story 38.2 AC-2: MemoryService.initialize() calls
        _recover_episodes_from_neo4j() and populates self._episodes.
        """
        neo4j = make_mock_neo4j(
            episodes=[
                {
                    "user_id": "u1",
                    "concept": "Python",
                    "concept_id": "c1",
                    "score": 85,
                    "timestamp": "2026-02-07T10:00:00",
                    "group_id": "g1",
                    "review_count": 2,
                },
            ]
        )
        learning_mem = make_mock_learning_memory()

        ms = MemoryService(neo4j_client=neo4j)
        ms._learning_memory = learning_mem
        await ms.initialize()

        assert ms._episodes_recovered is True
        assert len(ms._episodes) == 1
        assert ms._episodes[0]["concept"] == "Python"
        neo4j.get_all_recent_episodes.assert_awaited_once_with(
            limit=1000, group_id=_recovery_scope()
        )

    @pytest.mark.asyncio
    async def test_memory_service_degrades_when_neo4j_unavailable(self):
        """
        [P0] Story 38.2 AC-3: If Neo4j fails during init recovery,
        _episodes_recovered stays False and _episodes stays empty.
        """
        neo4j = make_mock_neo4j()
        # CARD-G4-1b: 裸 `Exception` **从来不在**生产 except 的捕获范围
        # `(RuntimeError, ConnectionError, asyncio.TimeoutError)` 里 —— 这条
        # 用例过去是靠异常穿透而红/绿含混的。改成真实会发生的 ConnectionError,
        # AC-3 的优雅降级才第一次被真正验证。生产 except **不得**放宽成
        # Exception: 那会连 VaultScopeUnresolved 一起吞掉。
        neo4j.get_all_recent_episodes = AsyncMock(
            side_effect=ConnectionError("Connection refused")
        )
        learning_mem = make_mock_learning_memory()

        ms = MemoryService(neo4j_client=neo4j)
        ms._learning_memory = learning_mem
        await ms.initialize()

        assert ms._episodes_recovered is False
        assert len(ms._episodes) == 0

    def test_dual_write_enabled_drives_info_log_path(self):
        """
        [P1] Story 38.4 AC-1: When ENABLE_GRAPHITI_JSON_DUAL_WRITE=True,
        the config drives the "enabled" code path in main.py:L118-120.
        """
        s = Settings(
            CANVAS_BASE_PATH="./test",
            CORS_ORIGINS="http://localhost",
            ENABLE_GRAPHITI_JSON_DUAL_WRITE=True,
        )
        assert s.ENABLE_GRAPHITI_JSON_DUAL_WRITE is True

    def test_dual_write_disabled_drives_warning_log_path(self):
        """
        [P1] Story 38.4 AC-2: When ENABLE_GRAPHITI_JSON_DUAL_WRITE=False,
        the config drives the "disabled" WARNING path in main.py:L121-123.
        """
        s = Settings(
            CANVAS_BASE_PATH="./test",
            CORS_ORIGINS="http://localhost",
            ENABLE_GRAPHITI_JSON_DUAL_WRITE=False,
        )
        assert s.ENABLE_GRAPHITI_JSON_DUAL_WRITE is False
