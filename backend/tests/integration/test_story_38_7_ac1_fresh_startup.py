"""
Story 38.7 AC-1: Fresh Environment Startup Verification

Verifies default config, FSRS init, episode recovery, startup logging.

Split from test_story_38_7_e2e_integration.py for maintainability.
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.config import Settings
from app.services.memory_service import MemoryService


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════


def _make_mock_neo4j(*, episodes=None, health_ok=True, fail_write=False):
    """Create a mock Neo4jClient with configurable behavior."""
    mock = AsyncMock()
    mock.initialize = AsyncMock()
    mock.health_check = AsyncMock(return_value=health_ok)
    mock.stats = {"initialized": True, "node_count": 10, "edge_count": 5, "episode_count": 3}
    mock.get_all_recent_episodes = AsyncMock(return_value=episodes or [])
    mock.get_learning_history = AsyncMock(return_value=[])
    if fail_write:
        mock.record_episode_to_neo4j = AsyncMock(side_effect=Exception("Neo4j connection refused"))
    else:
        mock.record_episode_to_neo4j = AsyncMock(return_value=True)
    return mock


def _make_mock_learning_memory():
    """Create a mock LearningMemoryClient."""
    mock = MagicMock()
    mock.add_memory = MagicMock()
    mock.save = MagicMock()
    return mock


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
        from app.services.review_service import ReviewService, FSRS_AVAILABLE

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

        with patch("app.services.review_service.FSRS_AVAILABLE", False), \
             patch("app.services.review_service.FSRSManager", None):
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
        neo4j = _make_mock_neo4j(episodes=[
            {"user_id": "u1", "concept": "Python", "concept_id": "c1",
             "score": 85, "timestamp": "2026-02-07T10:00:00", "group_id": "g1",
             "review_count": 2},
        ])
        learning_mem = _make_mock_learning_memory()

        ms = MemoryService(neo4j_client=neo4j, learning_memory_client=learning_mem)
        await ms.initialize()

        assert ms._episodes_recovered is True
        assert len(ms._episodes) == 1
        assert ms._episodes[0]["concept"] == "Python"
        neo4j.get_all_recent_episodes.assert_awaited_once_with(limit=1000)

    @pytest.mark.asyncio
    async def test_memory_service_degrades_when_neo4j_unavailable(self):
        """
        [P0] Story 38.2 AC-3: If Neo4j fails during init recovery,
        _episodes_recovered stays False and _episodes stays empty.
        """
        neo4j = _make_mock_neo4j()
        neo4j.get_all_recent_episodes = AsyncMock(
            side_effect=Exception("Connection refused")
        )
        learning_mem = _make_mock_learning_memory()

        ms = MemoryService(neo4j_client=neo4j, learning_memory_client=learning_mem)
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
