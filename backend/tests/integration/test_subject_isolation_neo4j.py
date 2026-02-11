# Canvas Learning System - Story 30.15 Tests
# 多学科隔离 + DI 完整性测试
"""
Story 30.15 - Subject Isolation and DI Integrity Tests

Task 1: group_id query isolation (Neo4j mock)
Task 2: DI chain end-to-end verification
Task 3: DI parameter completeness automation

[Source: docs/stories/30.15.test-isolation-di-integrity.story.md]
"""

import inspect
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ============================================================================
# Task 1: Multi-Subject Isolation Tests
# ============================================================================

class TestGroupIdQueryIsolation:
    """AC-30.15.1: group_id query isolation."""

    @pytest.fixture
    def mock_neo4j(self):
        neo4j = MagicMock()
        neo4j.initialize = AsyncMock()
        neo4j.stats = {"initialized": True, "connected": True}
        neo4j.create_learning_relationship = AsyncMock()
        # Simulate different results for different group_ids
        neo4j.get_learning_history = AsyncMock(return_value=[])
        return neo4j

    @pytest.fixture
    def mock_learning_memory(self):
        client = MagicMock()
        client._initialized = False
        client.initialize = AsyncMock(return_value=True)
        client.search_memories = AsyncMock(return_value=[])
        client.add_learning_episode = AsyncMock(return_value=True)
        return client

    @pytest.fixture
    async def memory_service(self, mock_neo4j, mock_learning_memory):
        from app.services.memory_service import MemoryService
        service = MemoryService(
            neo4j_client=mock_neo4j,
            learning_memory_client=mock_learning_memory,
        )
        await service.initialize()
        return service

    @pytest.mark.asyncio
    async def test_math_data_not_in_physics_query(self, memory_service):
        """Math data should not appear in Physics query."""
        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = False

            # Write Math event
            await memory_service.record_learning_event(
                user_id="user1", canvas_path="math/algebra.canvas",
                node_id="n1", concept="二次方程", agent_type="scoring-agent",
                subject="数学"
            )
            # Write Physics event
            await memory_service.record_learning_event(
                user_id="user1", canvas_path="physics/mechanics.canvas",
                node_id="n2", concept="牛顿定律", agent_type="scoring-agent",
                subject="物理"
            )

        # Patch load_failed_scores to avoid file access
        with patch.object(memory_service, "load_failed_scores", return_value=[]):
            with patch.object(memory_service, "_episodes_recovered", True):
                result = await memory_service.get_learning_history(
                    user_id="user1", subject="数学"
                )

        # Only Math data
        concepts = [item.get("concept") for item in result["items"]]
        assert "二次方程" in concepts
        assert "牛顿定律" not in concepts

    @pytest.mark.asyncio
    async def test_physics_data_not_in_math_query(self, memory_service):
        """Physics data should not appear in Math query."""
        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = False

            await memory_service.record_learning_event(
                user_id="user1", canvas_path="math/algebra.canvas",
                node_id="n1", concept="二次方程", agent_type="scoring-agent",
                subject="数学"
            )
            await memory_service.record_learning_event(
                user_id="user1", canvas_path="physics/mechanics.canvas",
                node_id="n2", concept="牛顿定律", agent_type="scoring-agent",
                subject="物理"
            )

        with patch.object(memory_service, "load_failed_scores", return_value=[]):
            with patch.object(memory_service, "_episodes_recovered", True):
                result = await memory_service.get_learning_history(
                    user_id="user1", subject="物理"
                )

        concepts = [item.get("concept") for item in result["items"]]
        assert "牛顿定律" in concepts
        assert "二次方程" not in concepts

    @pytest.mark.asyncio
    async def test_no_subject_returns_all(self, memory_service):
        """No subject filter should return all data."""
        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = False

            await memory_service.record_learning_event(
                user_id="user1", canvas_path="math/algebra.canvas",
                node_id="n1", concept="二次方程", agent_type="scoring-agent",
                subject="数学"
            )
            await memory_service.record_learning_event(
                user_id="user1", canvas_path="physics/mechanics.canvas",
                node_id="n2", concept="牛顿定律", agent_type="scoring-agent",
                subject="物理"
            )

        with patch.object(memory_service, "load_failed_scores", return_value=[]):
            with patch.object(memory_service, "_episodes_recovered", True):
                result = await memory_service.get_learning_history(
                    user_id="user1"  # No subject filter
                )

        concepts = [item.get("concept") for item in result["items"]]
        assert "二次方程" in concepts
        assert "牛顿定律" in concepts

    @pytest.mark.asyncio
    async def test_group_id_in_batch_writes(self, memory_service):
        """Batch writes should include group_id from event metadata."""
        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = False

            await memory_service.record_learning_event(
                user_id="user1", canvas_path="math/algebra.canvas",
                node_id="n1", concept="概念", agent_type="agent",
                subject="数学"
            )

        # Check group_id is stored in _episodes
        ep = memory_service._episodes[0]
        assert ep.get("group_id") is not None
        assert "数学" in ep.get("group_id", "").lower() or "math" in ep.get("group_id", "").lower()


# ============================================================================
# AC-30.15.2: Neo4j WHERE clause verification
# ============================================================================

class TestNeo4jGroupIdFiltering:
    """AC-30.15.2: Verify queries pass group_id to Neo4j."""

    @pytest.fixture
    def mock_neo4j(self):
        neo4j = MagicMock()
        neo4j.initialize = AsyncMock()
        neo4j.stats = {"initialized": True, "connected": True}
        neo4j.get_learning_history = AsyncMock(return_value=[])
        neo4j.get_review_suggestions = AsyncMock(return_value=[])
        return neo4j

    @pytest.fixture
    def mock_learning_memory(self):
        client = MagicMock()
        client._initialized = False
        client.initialize = AsyncMock(return_value=True)
        return client

    @pytest.fixture
    async def memory_service(self, mock_neo4j, mock_learning_memory):
        from app.services.memory_service import MemoryService
        service = MemoryService(
            neo4j_client=mock_neo4j,
            learning_memory_client=mock_learning_memory,
        )
        await service.initialize()
        return service

    @pytest.mark.asyncio
    async def test_get_learning_history_passes_group_id(self, memory_service, mock_neo4j):
        """get_learning_history passes group_id to Neo4j when subject provided."""
        with patch.object(memory_service, "load_failed_scores", return_value=[]):
            with patch.object(memory_service, "_episodes_recovered", True):
                await memory_service.get_learning_history(
                    user_id="user1", subject="数学"
                )

        mock_neo4j.get_learning_history.assert_called_once()
        call_kwargs = mock_neo4j.get_learning_history.call_args[1]
        assert call_kwargs.get("group_id") is not None

    @pytest.mark.asyncio
    async def test_get_learning_history_no_group_id_without_subject(self, memory_service, mock_neo4j):
        """get_learning_history passes group_id=None when no subject."""
        with patch.object(memory_service, "load_failed_scores", return_value=[]):
            with patch.object(memory_service, "_episodes_recovered", True):
                await memory_service.get_learning_history(
                    user_id="user1"  # No subject
                )

        mock_neo4j.get_learning_history.assert_called_once()
        call_kwargs = mock_neo4j.get_learning_history.call_args[1]
        assert call_kwargs.get("group_id") is None


# ============================================================================
# Task 2: DI Chain E2E Tests
# ============================================================================

class TestDIChainIntegrity:
    """AC-30.15.3: DI chain end-to-end verification."""

    def test_verification_service_canvas_service_injected(self):
        """P0 regression: VerificationService gets canvas_service from DI."""
        from app.dependencies import get_verification_service

        sig = inspect.signature(get_verification_service)
        param_names = list(sig.parameters.keys())
        assert "canvas_service" in param_names, (
            "P0: get_verification_service must accept canvas_service parameter"
        )

    def test_canvas_service_memory_client_code_path(self):
        """P0 regression: get_canvas_service injects memory_client."""
        source_file = Path(__file__).parent.parent.parent / "app" / "dependencies.py"
        code = source_file.read_text(encoding="utf-8")

        # Find get_canvas_service and check it injects memory_client
        start = code.find("async def get_canvas_service")
        end = code.find("\nasync def ", start + 1)
        if end == -1:
            end = code.find("\ndef ", start + 1)
        func_code = code[start:end]

        assert "memory_client" in func_code, (
            "P0: get_canvas_service must inject memory_client into CanvasService"
        )

    def test_context_enrichment_graphiti_injected(self):
        """P1 regression: get_context_enrichment_service injects graphiti_service."""
        source_file = Path(__file__).parent.parent.parent / "app" / "dependencies.py"
        code = source_file.read_text(encoding="utf-8")

        start = code.find("async def get_context_enrichment_service")
        end = code.find("\nasync def ", start + 1)
        if end == -1:
            end = code.find("\ndef ", start + 1)
        func_code = code[start:end]

        assert "graphiti_service" in func_code, (
            "P1: get_context_enrichment_service must inject graphiti_service"
        )

    def test_verification_service_accepts_all_required_deps(self):
        """VerificationService __init__ params vs dependencies.py actual params."""
        from app.services.verification_service import VerificationService

        init_sig = inspect.signature(VerificationService.__init__)
        init_params = set(init_sig.parameters.keys()) - {"self"}

        # These are the critical dependencies that MUST be injected
        critical_deps = {"agent_service", "canvas_service", "memory_service"}
        for dep in critical_deps:
            assert dep in init_params, (
                f"VerificationService.__init__ must accept {dep}"
            )


# ============================================================================
# Task 3: DI Parameter Completeness
# ============================================================================

class TestDIParameterCompleteness:
    """AC-30.15.4: DI parameter completeness automation."""

    def test_verification_service_di_passes_all_critical_deps(self):
        """dependencies.py passes all critical deps to VerificationService."""
        source_file = Path(__file__).parent.parent.parent / "app" / "dependencies.py"
        code = source_file.read_text(encoding="utf-8")

        # Extract get_verification_service body
        start = code.find("async def get_verification_service")
        end = code.find("\n\n# Type alias for VerificationService", start)
        func_code = code[start:end]

        # Must pass these to VerificationService()
        assert "canvas_service=canvas_service" in func_code, "Missing canvas_service injection"
        assert "memory_service=memory_service" in func_code, "Missing memory_service injection"
        assert "agent_service=agent_service" in func_code, "Missing agent_service injection"

    def test_canvas_service_di_passes_memory_client(self):
        """dependencies.py passes memory_client to CanvasService."""
        source_file = Path(__file__).parent.parent.parent / "app" / "dependencies.py"
        code = source_file.read_text(encoding="utf-8")

        start = code.find("async def get_canvas_service")
        end = code.find("\n\n# Type alias for CanvasService", start)
        func_code = code[start:end]

        assert "memory_client=memory_client" in func_code, "Missing memory_client injection"

    def test_context_enrichment_di_passes_graphiti(self):
        """dependencies.py passes graphiti_service to ContextEnrichmentService."""
        source_file = Path(__file__).parent.parent.parent / "app" / "dependencies.py"
        code = source_file.read_text(encoding="utf-8")

        start = code.find("async def get_context_enrichment_service")
        end = code.find("\n\n# Type alias for ContextEnrichmentService", start)
        func_code = code[start:end]

        assert "graphiti_service=graphiti_service" in func_code, "Missing graphiti_service injection"

    def test_subject_mapping_yaml_exists(self):
        """AC-30.15.5: subject_mapping.yaml exists and is not corrupted."""
        from app.core.subject_config import extract_subject_from_canvas_path

        # Should not crash on valid input
        result = extract_subject_from_canvas_path("math/algebra.canvas")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_build_group_id_deterministic(self):
        """group_id is deterministic for same subject."""
        from app.core.subject_config import build_group_id

        gid1 = build_group_id("数学")
        gid2 = build_group_id("数学")
        assert gid1 == gid2

    def test_build_group_id_different_subjects(self):
        """Different subjects produce different group_ids."""
        from app.core.subject_config import build_group_id

        gid_math = build_group_id("数学")
        gid_physics = build_group_id("物理")
        assert gid_math != gid_physics
