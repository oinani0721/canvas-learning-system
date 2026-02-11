"""
Story 36.13: Tests for asyncio.sleep audit + TTLCache configuration.

Tests:
1. Deleted simulate-work sleep in review_service (AC-1)
2. Memory retry delay from Settings (AC-2)
3. AgentService TTLCache from Settings (AC-3)
4. MemoryService TTLCache from Settings (AC-4)
5. ContextEnrichmentService TTLCache from Settings (AC-5)
6. Default values backward compatible (AC-7)
7. Extreme values no crash (AC-7)
"""

import asyncio
import inspect
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# AC-1: Deleted simulate-work sleep
# ---------------------------------------------------------------------------

class TestDeleteSimulateWorkSleep:
    """AC-36.13.1: The asyncio.sleep(0.2) 'Simulate work' is removed."""

    def test_no_simulate_work_sleep_in_generate(self):
        """Verify _generate closure no longer contains asyncio.sleep."""
        from app.services.review_service import ReviewService

        # Read the source of the generate_verification_canvas method
        source = inspect.getsource(ReviewService.generate_verification_canvas)
        assert "Simulate work" not in source
        # The specific sleep(0.2) pattern should be gone
        assert "sleep(0.2)" not in source


# ---------------------------------------------------------------------------
# AC-2: Memory retry delay from Settings
# ---------------------------------------------------------------------------

class TestMemoryRetryDelayFromSettings:
    """AC-36.13.2: memory_service retry delays use Settings config."""

    def test_retry_delay_reads_settings(self):
        """MemoryService uses configurable retry delays."""
        with patch("app.services.memory_service.get_neo4j_client") as mock_neo4j, \
             patch("app.services.memory_service.get_learning_memory_client") as mock_lmc, \
             patch("app.config.get_settings") as mock_settings:
            mock_neo4j.return_value = MagicMock()
            mock_lmc.return_value = MagicMock()
            s = MagicMock()
            s.MEMORY_RETRY_BASE_DELAY = 2.5
            s.MEMORY_RETRY_MAX_DELAY = 15.0
            s.SCORE_HISTORY_CACHE_MAXSIZE = 500
            mock_settings.return_value = s

            from app.services.memory_service import MemoryService
            svc = MemoryService()

            assert svc._retry_base_delay == 2.5
            assert svc._retry_max_delay == 15.0

    def test_retry_delay_defaults_match_original(self):
        """Default retry delays preserve backward compatibility."""
        from app.config import Settings
        s = Settings(
            AI_API_KEY="test",
            NEO4J_PASSWORD="test",
        )
        assert s.MEMORY_RETRY_BASE_DELAY == 1.0
        assert s.MEMORY_RETRY_MAX_DELAY == 10.0


# ---------------------------------------------------------------------------
# AC-3: AgentService TTLCache from Settings
# ---------------------------------------------------------------------------

class TestAgentServiceCacheFromSettings:
    """AC-36.13.3: AgentService TTLCache uses Settings config."""

    def test_cache_uses_custom_maxsize_and_ttl(self):
        """AgentService TTLCache respects injected maxsize and ttl."""
        from app.services.agent_service import AgentService
        svc = AgentService(
            memory_cache_maxsize=50,
            memory_cache_ttl=10,
        )
        assert svc._memory_cache.maxsize == 50
        assert svc._memory_cache.ttl == 10  # Verify actual TTL value

    def test_cache_default_values(self):
        """AgentService defaults match original hardcoded values."""
        from app.services.agent_service import AgentService
        svc = AgentService()
        assert svc._memory_cache.maxsize == 1000


# ---------------------------------------------------------------------------
# AC-4: MemoryService TTLCache from Settings
# ---------------------------------------------------------------------------

class TestMemoryServiceCacheFromSettings:
    """AC-36.13.4: MemoryService score_history_cache uses Settings config."""

    def test_cache_uses_custom_maxsize(self):
        """MemoryService score_history_cache respects Settings maxsize."""
        with patch("app.services.memory_service.get_neo4j_client") as mock_neo4j, \
             patch("app.services.memory_service.get_learning_memory_client") as mock_lmc, \
             patch("app.config.get_settings") as mock_settings:
            mock_neo4j.return_value = MagicMock()
            mock_lmc.return_value = MagicMock()
            s = MagicMock()
            s.MEMORY_RETRY_BASE_DELAY = 1.0
            s.MEMORY_RETRY_MAX_DELAY = 10.0
            s.SCORE_HISTORY_CACHE_MAXSIZE = 200
            mock_settings.return_value = s

            from app.services.memory_service import MemoryService
            svc = MemoryService()
            assert svc._score_history_cache.maxsize == 200


# ---------------------------------------------------------------------------
# AC-5: ContextEnrichmentService TTLCache from Settings
# ---------------------------------------------------------------------------

class TestEnrichmentCacheFromSettings:
    """AC-36.13.5: ContextEnrichmentService cache uses Settings config."""

    def test_cache_uses_custom_maxsize(self):
        """ContextEnrichmentService cache respects injected maxsize."""
        from app.services.context_enrichment_service import ContextEnrichmentService
        mock_canvas = MagicMock()
        svc = ContextEnrichmentService(
            canvas_service=mock_canvas,
            association_cache_maxsize=300,
        )
        assert svc._association_cache.maxsize == 300

    def test_cache_default_maxsize(self):
        """ContextEnrichmentService default maxsize = 1000."""
        from app.services.context_enrichment_service import ContextEnrichmentService
        mock_canvas = MagicMock()
        svc = ContextEnrichmentService(canvas_service=mock_canvas)
        assert svc._association_cache.maxsize == 1000


# ---------------------------------------------------------------------------
# AC-7: Default values backward compatible + extreme values
# ---------------------------------------------------------------------------

class TestDefaultValuesBackwardCompatible:
    """AC-36.13.7: D4 — defaults unchanged, extreme values safe."""

    def test_settings_defaults_match_original(self):
        """All new Settings fields have defaults matching original hardcoded values."""
        from app.config import Settings
        s = Settings(
            AI_API_KEY="test",
            NEO4J_PASSWORD="test",
        )
        assert s.MEMORY_RETRY_BASE_DELAY == 1.0
        assert s.MEMORY_RETRY_MAX_DELAY == 10.0
        assert s.AGENT_MEMORY_CACHE_MAXSIZE == 1000
        assert s.AGENT_MEMORY_CACHE_TTL == 30
        assert s.SCORE_HISTORY_CACHE_MAXSIZE == 1000
        assert s.ENRICHMENT_CACHE_MAXSIZE == 1000

    def test_extreme_maxsize_1_no_crash(self):
        """maxsize=1 does not crash — cache simply evicts aggressively."""
        from app.services.agent_service import AgentService
        svc = AgentService(memory_cache_maxsize=1, memory_cache_ttl=0)
        # Should be able to set and get from cache without crash
        svc._memory_cache["key1"] = "val1"
        svc._memory_cache["key2"] = "val2"
        # With maxsize=1, only 1 entry survives
        assert len(svc._memory_cache) <= 1

    def test_extreme_ttl_0_no_crash(self):
        """ttl=0 does not crash — entries expire immediately."""
        from cachetools import TTLCache
        from app.services.agent_service import AgentService
        svc = AgentService(memory_cache_maxsize=100, memory_cache_ttl=0)
        svc._memory_cache["key1"] = "val1"
        # ttl=0 means entries expire on next access
        # Just verify no crash and it's still a TTLCache
        assert isinstance(svc._memory_cache, TTLCache)

    def test_enrichment_extreme_maxsize_1(self):
        """ContextEnrichmentService with maxsize=1 does not crash."""
        from app.services.context_enrichment_service import ContextEnrichmentService
        mock_canvas = MagicMock()
        svc = ContextEnrichmentService(
            canvas_service=mock_canvas,
            association_cache_maxsize=1,
        )
        svc._association_cache["k1"] = "v1"
        svc._association_cache["k2"] = "v2"
        assert len(svc._association_cache) <= 1


# ---------------------------------------------------------------------------
# M3 Fix: DI path propagation — verify dependencies.py passes Settings values
# ---------------------------------------------------------------------------

class TestDIPathPropagation:
    """Verify dependencies.py actually passes Settings config to services."""

    def test_agent_service_di_passes_cache_config(self):
        """dependencies.py reads Settings and passes to AgentService constructor."""
        from app.dependencies import get_agent_service
        source = inspect.getsource(get_agent_service)
        assert "AGENT_MEMORY_CACHE_MAXSIZE" in source, \
            "dependencies.py must pass AGENT_MEMORY_CACHE_MAXSIZE to AgentService"
        assert "AGENT_MEMORY_CACHE_TTL" in source, \
            "dependencies.py must pass AGENT_MEMORY_CACHE_TTL to AgentService"

    def test_enrichment_service_di_passes_cache_config(self):
        """dependencies.py reads Settings and passes to ContextEnrichmentService."""
        from app.dependencies import get_context_enrichment_service
        source = inspect.getsource(get_context_enrichment_service)
        assert "ENRICHMENT_CACHE_MAXSIZE" in source, \
            "dependencies.py must pass ENRICHMENT_CACHE_MAXSIZE to ContextEnrichmentService"

    def test_env_example_documents_all_new_settings(self):
        """AC-6: .env.example contains all Story 36.13 config items."""
        from pathlib import Path
        env_example = Path(__file__).parent.parent.parent / ".env.example"
        content = env_example.read_text(encoding="utf-8")
        required_keys = [
            "MEMORY_RETRY_BASE_DELAY",
            "MEMORY_RETRY_MAX_DELAY",
            "AGENT_MEMORY_CACHE_MAXSIZE",
            "AGENT_MEMORY_CACHE_TTL",
            "SCORE_HISTORY_CACHE_MAXSIZE",
            "ENRICHMENT_CACHE_MAXSIZE",
        ]
        for key in required_keys:
            assert key in content, f".env.example missing documentation for {key}"
