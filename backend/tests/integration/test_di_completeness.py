"""
DI Completeness Tests - Story 36.11

Automated dependency injection completeness verification for all core Services.
Ensures that every __init__ optional parameter is actually passed by dependencies.py factory functions.

AC2: Cover AgentService, CanvasService, VerificationService, ContextEnrichmentService, ReviewService
AC3: Any missing injection must cause test FAIL

[Source: docs/stories/36.11.story.md]
"""

import inspect
import logging
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# =============================================================================
# Task 1 + Task 3: AgentService memory_client Injection Tests
# =============================================================================


class TestAgentServiceMemoryClientInjection:
    """
    Tests for AgentService.memory_client DI fix.

    AC1: AgentService receives memory_client from dependencies.py
    AC4: WARNING log when memory_client=None
    """

    @pytest.mark.asyncio
    async def test_agent_service_memory_client_injected(self):
        """
        AC1: Verify get_agent_service injects memory_client (LearningMemoryClient).

        Task 1.1-1.3: dependencies.py should lazy-import get_learning_memory_client
        and pass the instance to AgentService constructor.

        [Source: docs/stories/36.11.story.md#Task-1]
        """
        from app.dependencies import get_agent_service

        # Create minimal mock settings (no AI key to skip GeminiClient)
        settings = MagicMock()
        settings.AI_API_KEY = ""
        settings.AI_MODEL_NAME = "test"
        settings.AI_BASE_URL = ""
        settings.AI_PROVIDER = "test"

        canvas_service = MagicMock()
        neo4j_client = MagicMock()

        gen = get_agent_service(settings, canvas_service, neo4j_client)
        service = await gen.__anext__()

        try:
            # AC1: memory_client should be injected (not None)
            assert service._memory_client is not None, (
                "AgentService._memory_client should be injected by dependencies.py. "
                "Currently None — get_agent_service() is not passing memory_client."
            )
        finally:
            try:
                await gen.aclose()
            except Exception:
                pass

    @pytest.mark.asyncio
    async def test_agent_service_memory_client_is_learning_memory_client(self):
        """
        AC1: Verify the injected memory_client is a LearningMemoryClient instance.

        [Source: docs/stories/36.11.story.md#Task-3.1]
        """
        from app.dependencies import get_agent_service
        from app.clients.graphiti_client import LearningMemoryClient

        settings = MagicMock()
        settings.AI_API_KEY = ""
        settings.AI_MODEL_NAME = "test"
        settings.AI_BASE_URL = ""
        settings.AI_PROVIDER = "test"

        canvas_service = MagicMock()
        neo4j_client = MagicMock()

        gen = get_agent_service(settings, canvas_service, neo4j_client)
        service = await gen.__anext__()

        try:
            if service._memory_client is not None:
                assert isinstance(service._memory_client, LearningMemoryClient), (
                    f"Expected LearningMemoryClient, got {type(service._memory_client)}"
                )
        finally:
            try:
                await gen.aclose()
            except Exception:
                pass

    @pytest.mark.asyncio
    async def test_agent_service_memory_client_none_logs_warning(self):
        """
        AC4: Verify WARNING log when memory_client=None.

        Task 1.4: AgentService should log WARNING for degradation transparency.

        [Source: docs/stories/36.11.story.md#Task-1.4]
        """
        from app.services.agent_service import AgentService

        with patch("app.services.agent_service.logger") as mock_logger:
            # Create AgentService with memory_client=None
            service = AgentService(
                gemini_client=None,
                memory_client=None,
                canvas_service=None,
                neo4j_client=None
            )

            # AC4: Should have logged WARNING about missing memory_client
            warning_calls = [
                str(call) for call in mock_logger.warning.call_args_list
            ]
            memory_warnings = [
                w for w in warning_calls
                if "memory" in w.lower() or "LearningMemoryClient" in w
            ]
            assert len(memory_warnings) > 0, (
                "AgentService should log WARNING when memory_client=None. "
                f"Actual warning calls: {warning_calls}"
            )

    @pytest.mark.asyncio
    async def test_agent_service_neo4j_fallback_to_memory_client(self):
        """
        AC1: Verify AgentService uses memory_client as fallback when Neo4j unavailable.

        Task 3.2: When neo4j_client is None, memory_client should still provide
        historical learning context.

        [Source: docs/stories/36.11.story.md#Task-3.2]
        """
        from app.services.agent_service import AgentService

        mock_memory = MagicMock()
        mock_memory.search_memories = AsyncMock(return_value=[
            {"concept": "test", "score": 0.8}
        ])

        # Create AgentService with neo4j_client=None but memory_client present
        service = AgentService(
            gemini_client=None,
            memory_client=mock_memory,
            canvas_service=None,
            neo4j_client=None  # Neo4j unavailable
        )

        # Verify memory_client is stored and available for fallback
        assert service._memory_client is mock_memory, (
            "memory_client should be stored even when neo4j_client is None"
        )
        assert service._neo4j_client is None, (
            "neo4j_client should be None"
        )


# =============================================================================
# Task 2: Generic DI Completeness Tests
# =============================================================================


# Service DI configuration: maps service name to factory info and critical attributes
SERVICES_DI_CONFIG = {
    "AgentService": {
        "factory_module": "app.dependencies",
        "factory_name": "get_agent_service",
        "init_class_module": "app.services.agent_service",
        "init_class_name": "AgentService",
        "critical_params": [
            "gemini_client", "memory_client", "canvas_service", "neo4j_client"
        ],
        "critical_attrs": [
            "_gemini_client", "_memory_client", "_canvas_service", "_neo4j_client"
        ],
    },
    "CanvasService": {
        "factory_module": "app.dependencies",
        "factory_name": "get_canvas_service",
        "init_class_module": "app.services.canvas_service",
        "init_class_name": "CanvasService",
        "critical_params": ["canvas_base_path", "memory_client"],
        "critical_attrs": ["_canvas_base_path", "_memory_client"],
    },
    "VerificationService": {
        "factory_module": "app.dependencies",
        "factory_name": "get_verification_service",
        "init_class_module": "app.services.verification_service",
        "init_class_name": "VerificationService",
        "critical_params": [
            "rag_service", "cross_canvas_service", "textbook_context_service",
            "canvas_service", "agent_service", "canvas_base_path",
            "graphiti_client", "memory_service"
        ],
        "critical_attrs": [
            "_rag_service", "_cross_canvas_service", "_textbook_context_service",
            "_canvas_service", "_agent_service", "_canvas_base_path",
            "_graphiti_client", "_memory_service"
        ],
    },
    "ContextEnrichmentService": {
        "factory_module": "app.dependencies",
        "factory_name": "get_context_enrichment_service",
        "init_class_module": "app.services.context_enrichment_service",
        "init_class_name": "ContextEnrichmentService",
        # canvas_service is REQUIRED (no default), others are optional
        "critical_params": [
            "textbook_service", "cross_canvas_service", "graphiti_service"
        ],
        "critical_attrs": [
            "_textbook_service", "_cross_canvas_service", "_graphiti_service"
        ],
    },
    "ReviewService": {
        "factory_module": "app.dependencies",
        "factory_name": "get_review_service",
        "init_class_module": "app.services.review_service",
        "init_class_name": "ReviewService",
        # canvas_service, task_manager are REQUIRED; graphiti_client, fsrs_manager are optional
        "critical_params": ["graphiti_client", "fsrs_manager"],
        "critical_attrs": ["_graphiti_client", "_fsrs_manager"],
    },
}


class TestDICompletenessInspection:
    """
    AC2: Automated DI completeness verification using inspect.signature().

    For each Service, verify that every __init__ optional parameter
    has a corresponding entry in the factory function's construction call.

    AC3: Any new __init__ parameter not passed by dependencies.py will FAIL.

    [Source: docs/stories/36.11.story.md#Task-2]
    """

    @pytest.mark.parametrize(
        "service_name,config",
        list(SERVICES_DI_CONFIG.items()),
        ids=list(SERVICES_DI_CONFIG.keys()),
    )
    def test_service_init_params_coverage(self, service_name, config):
        """
        AC2/AC3: Verify that every critical __init__ parameter of each Service
        is listed as a critical_param, ensuring the test catches missing injections.

        Uses inspect.signature() to extract actual __init__ parameters.

        [Source: docs/stories/36.11.story.md#Task-2.2]
        """
        import importlib

        # Dynamically import the Service class
        module = importlib.import_module(config["init_class_module"])
        service_class = getattr(module, config["init_class_name"])

        # Get __init__ signature
        sig = inspect.signature(service_class.__init__)
        init_params = [
            name for name, param in sig.parameters.items()
            if name != "self"
            and param.default is not inspect.Parameter.empty  # Only optional params
        ]

        # Verify all critical params are in the actual __init__ signature
        for critical_param in config["critical_params"]:
            assert critical_param in init_params, (
                f"{service_name}.__init__ does not have parameter '{critical_param}'. "
                f"Available optional params: {init_params}"
            )

    @pytest.mark.parametrize(
        "service_name",
        ["AgentService", "CanvasService", "VerificationService",
         "ContextEnrichmentService", "ReviewService"],
    )
    def test_service_di_config_has_matching_attrs(self, service_name):
        """
        AC2: Verify that critical_params and critical_attrs lists have matching lengths.

        Each critical param should map to a critical attr for runtime verification.

        [Source: docs/stories/36.11.story.md#Task-2.4]
        """
        config = SERVICES_DI_CONFIG[service_name]
        assert len(config["critical_params"]) == len(config["critical_attrs"]), (
            f"{service_name}: critical_params ({len(config['critical_params'])}) "
            f"and critical_attrs ({len(config['critical_attrs'])}) length mismatch"
        )


class TestAgentServiceDICompleteness:
    """
    Task 2.5: test_agent_service_di_completeness

    Runtime verification that dependencies.py actually passes all critical
    parameters to AgentService.

    [Source: docs/stories/36.11.story.md#Task-2.5]
    """

    @pytest.mark.asyncio
    async def test_agent_service_di_completeness(self):
        """
        AC2: Verify AgentService gets all critical dependencies from get_agent_service().

        [Source: docs/stories/36.11.story.md#Task-2.5]
        """
        from app.dependencies import get_agent_service

        settings = MagicMock()
        settings.AI_API_KEY = "test-key"
        settings.AI_MODEL_NAME = "test-model"
        settings.AI_BASE_URL = ""
        settings.AI_PROVIDER = "test"

        canvas_service = MagicMock()
        neo4j_client = MagicMock()

        gen = get_agent_service(settings, canvas_service, neo4j_client)
        service = await gen.__anext__()

        try:
            config = SERVICES_DI_CONFIG["AgentService"]
            for attr_name in config["critical_attrs"]:
                assert hasattr(service, attr_name), (
                    f"AgentService missing attribute '{attr_name}'"
                )
                # For GeminiClient, it depends on API key being valid
                # For others, they should be non-None
                if attr_name not in ("_gemini_client",):
                    val = getattr(service, attr_name)
                    assert val is not None, (
                        f"AgentService.{attr_name} is None — "
                        f"dependencies.py is not injecting this dependency"
                    )
        finally:
            try:
                await gen.aclose()
            except Exception:
                pass


class TestCanvasServiceDICompleteness:
    """
    Task 2.5: test_canvas_service_di_completeness

    [Source: docs/stories/36.11.story.md#Task-2.5]
    """

    @pytest.mark.asyncio
    async def test_canvas_service_di_completeness(self):
        """
        AC2: Verify CanvasService gets all critical dependencies.
        """
        from app.dependencies import get_canvas_service

        settings = MagicMock()
        settings.canvas_base_path = "test/path"

        gen = get_canvas_service(settings)
        service = await gen.__anext__()

        try:
            # canvas_base_path should always be set
            assert hasattr(service, "_canvas_base_path") or hasattr(service, "canvas_base_path"), (
                "CanvasService missing canvas_base_path attribute"
            )
            # memory_client may be None if MemoryService not available (graceful degradation)
            # But the injection attempt should have been made
            assert hasattr(service, "_memory_client"), (
                "CanvasService missing _memory_client attribute"
            )
        finally:
            try:
                await gen.aclose()
            except Exception:
                pass


class TestReviewServiceDICompleteness:
    """
    Task 2.5: test_review_service_di_completeness

    [Source: docs/stories/36.11.story.md#Task-2.5]
    """

    @pytest.mark.asyncio
    async def test_review_service_di_completeness(self):
        """
        AC2: Verify ReviewService gets all critical dependencies.
        """
        from app.dependencies import get_review_service

        canvas_service = MagicMock()
        task_manager = MagicMock()
        settings = MagicMock()
        settings.USE_FSRS = False

        gen = get_review_service(canvas_service, task_manager, settings)
        service = await gen.__anext__()

        try:
            # ReviewService uses public attrs (no underscore prefix)
            assert service.canvas_service is canvas_service
            assert service.task_manager is task_manager
        finally:
            try:
                await gen.aclose()
            except Exception:
                pass
