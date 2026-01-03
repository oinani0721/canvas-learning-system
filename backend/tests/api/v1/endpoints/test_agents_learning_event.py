# Canvas Learning System - Story 12.A.5 Tests
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: testing BackgroundTasks)
"""
Story 12.A.5 - Learning Event Auto-Recording Tests

Tests for automatic learning event recording after Agent calls:
- AC1: Auto-recording on successful Agent calls
- AC2: Record includes concept, canvas_path, node_id, timestamp
- AC3: Recording doesn't block Agent response (BackgroundTasks)
- AC4: Silent failure handling (graceful degradation)
- AC5: Events stored to learning_memories.json
- AC6: Subsequent calls can retrieve new events

[Source: docs/stories/story-12.A.5-learning-event-recording.md#Testing]
[Source: docs/architecture/coding-standards.md#测试规范]
"""

from unittest.mock import AsyncMock, patch

import pytest
from app.api.v1.endpoints.agents import (
    _record_learning_event,
    get_memory_service_for_agents,
)
from fastapi import BackgroundTasks


class MockMemoryService:
    """Mock MemoryService for testing Story 12.A.5."""

    def __init__(self, should_fail: bool = False):
        """
        Initialize mock service.

        Args:
            should_fail: If True, record_learning_event raises exception
        """
        self.should_fail = should_fail
        self.call_count = 0
        self.last_call_args = None

    async def initialize(self):
        """Mock initialize."""
        pass

    async def cleanup(self):
        """Mock cleanup."""
        pass

    async def record_learning_event(
        self,
        user_id: str,
        canvas_path: str,
        node_id: str,
        concept: str,
        agent_type: str,
        score: int | None = None,
        duration_seconds: int | None = None
    ) -> str:
        """Mock record_learning_event."""
        self.call_count += 1
        self.last_call_args = {
            "user_id": user_id,
            "canvas_path": canvas_path,
            "node_id": node_id,
            "concept": concept,
            "agent_type": agent_type,
            "score": score,
            "duration_seconds": duration_seconds,
        }

        if self.should_fail:
            raise Exception("Mock DB Error")

        return f"episode-mock-{self.call_count}"


class MockEnrichedContext:
    """Mock enriched context result."""

    def __init__(self):
        self.target_content = "逆否命题的定义和性质"
        self.enriched_context = "相关上下文：充分必要条件"
        self.x = 100
        self.y = 200
        self.width = 400
        self.height = 200
        self.color = "3"  # Purple (Obsidian Canvas: "3"=purple, "4"=red)
        self.has_textbook_refs = False


class MockRAGService:
    """Mock RAG service for testing."""

    def __init__(self):
        self.is_available = False
        self.import_error = "RAG not available in tests"


class TestRecordLearningEvent:
    """Tests for _record_learning_event helper function."""

    @pytest.mark.asyncio
    async def test_record_learning_event_success(self):
        """AC-1: Successfully records learning event after Agent call."""
        # Given: A mock memory service
        mock_service = MockMemoryService()

        # When: Recording a learning event
        await _record_learning_event(
            memory_service=mock_service,
            agent_type="decompose_basic",
            canvas_path="Math53.canvas",
            node_id="node_abc123",
            concept="逆否命题的定义"
        )

        # Then: Service was called exactly once
        assert mock_service.call_count == 1

    @pytest.mark.asyncio
    async def test_record_learning_event_includes_required_fields(self):
        """AC-2: Record includes concept, canvas_path, node_id, agent_type."""
        # Given: A mock memory service
        mock_service = MockMemoryService()

        # When: Recording a learning event
        await _record_learning_event(
            memory_service=mock_service,
            agent_type="decompose_deep",
            canvas_path="Math53.canvas",
            node_id="node_xyz789",
            concept="逆否命题"
        )

        # Then: All required fields are present
        args = mock_service.last_call_args
        assert args["user_id"] == "default"
        assert args["canvas_path"] == "Math53.canvas"
        assert args["node_id"] == "node_xyz789"
        assert args["concept"] == "逆否命题"
        assert args["agent_type"] == "decompose_deep"

    @pytest.mark.asyncio
    async def test_record_learning_event_with_score(self):
        """AC-2: Score recording for scoring Agent."""
        # Given: A mock memory service
        mock_service = MockMemoryService()

        # When: Recording a learning event with score
        await _record_learning_event(
            memory_service=mock_service,
            agent_type="score",
            canvas_path="Math53.canvas",
            node_id="node_score1",
            concept="用户对逆否命题的理解",
            score=85
        )

        # Then: Score is included
        args = mock_service.last_call_args
        assert args["score"] == 85
        assert args["agent_type"] == "score"

    @pytest.mark.asyncio
    async def test_record_learning_event_failure_silent(self):
        """AC-4: Recording failure does not raise exception (silent handling)."""
        # Given: A failing memory service
        mock_service = MockMemoryService(should_fail=True)

        # When: Recording fails
        # Then: No exception propagates (silent handling)
        try:
            await _record_learning_event(
                memory_service=mock_service,
                agent_type="decompose_basic",
                canvas_path="Math53.canvas",
                node_id="node_fail1",
                concept="测试概念"
            )
        except Exception as e:
            pytest.fail(f"Exception should not propagate: {e}")

        # Service was still called
        assert mock_service.call_count == 1

    @pytest.mark.asyncio
    async def test_record_learning_event_different_agent_types(self):
        """AC-2: Different agent types are recorded correctly."""
        mock_service = MockMemoryService()

        # Test decompose_basic
        await _record_learning_event(
            memory_service=mock_service,
            agent_type="decompose_basic",
            canvas_path="Canvas1.canvas",
            node_id="node1",
            concept="概念1"
        )
        assert mock_service.last_call_args["agent_type"] == "decompose_basic"

        # Test explain_oral
        await _record_learning_event(
            memory_service=mock_service,
            agent_type="explain_oral",
            canvas_path="Canvas2.canvas",
            node_id="node2",
            concept="概念2"
        )
        assert mock_service.last_call_args["agent_type"] == "explain_oral"

        # Test explain_clarification
        await _record_learning_event(
            memory_service=mock_service,
            agent_type="explain_clarification",
            canvas_path="Canvas3.canvas",
            node_id="node3",
            concept="概念3"
        )
        assert mock_service.last_call_args["agent_type"] == "explain_clarification"

        # Total calls
        assert mock_service.call_count == 3


class TestBackgroundTaskIntegration:
    """Tests for BackgroundTasks integration (AC-3)."""

    @pytest.mark.asyncio
    async def test_background_task_non_blocking(self):
        """AC-3: Recording doesn't block Agent response."""
        # Given: A BackgroundTasks instance and mock service
        background_tasks = BackgroundTasks()
        mock_service = MockMemoryService()

        # When: Adding recording task to background
        background_tasks.add_task(
            _record_learning_event,
            memory_service=mock_service,
            agent_type="decompose_basic",
            canvas_path="Math53.canvas",
            node_id="node_bg1",
            concept="后台任务测试"
        )

        # Then: Task is queued (not yet executed)
        assert mock_service.call_count == 0

        # When: Running background tasks
        await background_tasks()

        # Then: Task was executed
        assert mock_service.call_count == 1

    @pytest.mark.asyncio
    async def test_background_task_failure_graceful(self):
        """AC-3 + AC-4: Background task failure is graceful."""
        # Given: A failing service and BackgroundTasks
        background_tasks = BackgroundTasks()
        mock_service = MockMemoryService(should_fail=True)

        # When: Adding failing task
        background_tasks.add_task(
            _record_learning_event,
            memory_service=mock_service,
            agent_type="decompose_basic",
            canvas_path="Math53.canvas",
            node_id="node_fail_bg",
            concept="失败任务测试"
        )

        # Then: Executing doesn't raise (graceful degradation)
        try:
            await background_tasks()
        except Exception as e:
            pytest.fail(f"Background task failure should not propagate: {e}")


class TestMemoryServiceDependency:
    """Tests for get_memory_service_for_agents dependency."""

    @pytest.mark.asyncio
    async def test_memory_service_lifecycle(self):
        """Test MemoryService initialize/cleanup lifecycle."""
        # Given: Mocked MemoryService class
        with patch('app.api.v1.endpoints.agents.MemoryService') as MockClass:
            mock_instance = AsyncMock()
            mock_instance.initialize = AsyncMock()
            mock_instance.cleanup = AsyncMock()
            MockClass.return_value = mock_instance

            # When: Using the dependency generator
            gen = get_memory_service_for_agents()
            service = await gen.__anext__()

            # Then: Initialize was called and service is the mock instance
            mock_instance.initialize.assert_called_once()
            assert service is mock_instance

            # When: Finishing the generator
            try:
                await gen.__anext__()
            except StopAsyncIteration:
                pass

            # Then: Cleanup was called
            mock_instance.cleanup.assert_called_once()


class TestEndpointIntegration:
    """Integration tests for Agent endpoints with learning event recording."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for endpoint testing."""
        return {
            "agent_service": AsyncMock(),
            "context_service": AsyncMock(),
            "rag_service": MockRAGService(),
            "memory_service": MockMemoryService(),
        }

    @pytest.mark.asyncio
    async def test_decompose_basic_triggers_recording(self, mock_dependencies):
        """AC-1: decompose_basic endpoint triggers learning event recording."""
        # Given: Mock dependencies
        mock_dependencies["context_service"].enrich_with_adjacent_nodes = AsyncMock(
            return_value=MockEnrichedContext()
        )
        mock_dependencies["agent_service"].decompose_basic = AsyncMock(
            return_value={"questions": [], "created_nodes": []}
        )

        # When: Calling endpoint (simulated via direct function call)
        from app.api.v1.endpoints.agents import decompose_basic
        from app.models import DecomposeRequest

        background_tasks = BackgroundTasks()
        request = DecomposeRequest(
            canvas_name="Math53.canvas",
            node_id="node_test1"
        )

        await decompose_basic(
            request=request,
            background_tasks=background_tasks,
            agent_service=mock_dependencies["agent_service"],
            context_service=mock_dependencies["context_service"],
            rag_service=mock_dependencies["rag_service"],
            memory_service=mock_dependencies["memory_service"],
        )

        # Then: Background task was added
        # Execute background tasks
        await background_tasks()

        # Then: Learning event was recorded
        assert mock_dependencies["memory_service"].call_count == 1
        args = mock_dependencies["memory_service"].last_call_args
        assert args["agent_type"] == "decompose_basic"
        assert args["canvas_path"] == "Math53.canvas"

    @pytest.mark.asyncio
    async def test_decompose_deep_triggers_recording(self, mock_dependencies):
        """AC-1: decompose_deep endpoint triggers learning event recording."""
        # Given: Mock dependencies
        mock_dependencies["context_service"].enrich_with_adjacent_nodes = AsyncMock(
            return_value=MockEnrichedContext()
        )
        mock_dependencies["agent_service"].decompose_deep = AsyncMock(
            return_value={"questions": [], "created_nodes": []}
        )

        # When: Calling endpoint
        from app.api.v1.endpoints.agents import decompose_deep
        from app.models import DecomposeRequest

        background_tasks = BackgroundTasks()
        request = DecomposeRequest(
            canvas_name="Math53.canvas",
            node_id="node_deep1"
        )

        await decompose_deep(
            request=request,
            background_tasks=background_tasks,
            agent_service=mock_dependencies["agent_service"],
            context_service=mock_dependencies["context_service"],
            rag_service=mock_dependencies["rag_service"],
            memory_service=mock_dependencies["memory_service"],
        )

        await background_tasks()

        # Then: Learning event was recorded with correct agent_type
        assert mock_dependencies["memory_service"].call_count == 1
        args = mock_dependencies["memory_service"].last_call_args
        assert args["agent_type"] == "decompose_deep"

    @pytest.mark.asyncio
    async def test_score_understanding_triggers_recording(self, mock_dependencies):
        """AC-1: score_understanding endpoint triggers learning event recording."""
        # Given: Mock dependencies
        # Note: NodeScore validates: each sub-score 0-10, total 0-40
        mock_dependencies["agent_service"].score_node = AsyncMock(
            return_value={
                "scores": [{
                    "node_id": "node_score1",
                    "accuracy": 8.0,
                    "imagery": 7.0,
                    "completeness": 9.0,
                    "originality": 6.0,
                    "total": 30.0,  # Valid: 0-40 range
                    "new_color": "2",  # Green (>=32 is green, but 30 would be yellow)
                    "concept": "逆否命题理解"
                }]
            }
        )

        # When: Calling endpoint
        from app.api.v1.endpoints.agents import score_understanding
        from app.models import ScoreRequest

        # Need to mock canvas_service for score endpoint
        mock_canvas_service = AsyncMock()

        background_tasks = BackgroundTasks()
        request = ScoreRequest(
            canvas_name="Math53.canvas",
            node_ids=["node_score1"]
        )

        await score_understanding(
            request=request,
            background_tasks=background_tasks,
            agent_service=mock_dependencies["agent_service"],
            canvas_service=mock_canvas_service,
            rag_service=mock_dependencies["rag_service"],
            memory_service=mock_dependencies["memory_service"],
        )

        await background_tasks()

        # Then: Learning event was recorded with score
        assert mock_dependencies["memory_service"].call_count == 1
        args = mock_dependencies["memory_service"].last_call_args
        assert args["agent_type"] == "score"
        assert args["score"] == 30  # Total score from mock (0-40 range)

    @pytest.mark.asyncio
    async def test_explain_oral_triggers_recording(self, mock_dependencies):
        """AC-1: explain_oral endpoint triggers learning event recording."""
        # Given: Mock dependencies
        mock_dependencies["context_service"].enrich_with_adjacent_nodes = AsyncMock(
            return_value=MockEnrichedContext()
        )
        mock_dependencies["agent_service"].generate_explanation = AsyncMock(
            return_value={"explanation": "口语化解释内容", "created_node_id": "new1"}
        )

        # When: Calling endpoint
        from app.api.v1.endpoints.agents import explain_oral
        from app.models import ExplainRequest

        background_tasks = BackgroundTasks()
        request = ExplainRequest(
            canvas_name="Math53.canvas",
            node_id="node_oral1"
        )

        await explain_oral(
            request=request,
            background_tasks=background_tasks,
            agent_service=mock_dependencies["agent_service"],
            context_service=mock_dependencies["context_service"],
            rag_service=mock_dependencies["rag_service"],
            memory_service=mock_dependencies["memory_service"],
        )

        await background_tasks()

        # Then: Learning event was recorded
        assert mock_dependencies["memory_service"].call_count == 1
        args = mock_dependencies["memory_service"].last_call_args
        assert args["agent_type"] == "explain_oral"

    @pytest.mark.asyncio
    async def test_learning_event_failure_does_not_block_response(self, mock_dependencies):
        """AC-4: Learning event failure does not block Agent response."""
        # Given: A failing memory service
        failing_memory_service = MockMemoryService(should_fail=True)

        mock_dependencies["context_service"].enrich_with_adjacent_nodes = AsyncMock(
            return_value=MockEnrichedContext()
        )
        mock_dependencies["agent_service"].decompose_basic = AsyncMock(
            return_value={"questions": ["问题1"], "created_nodes": []}
        )

        # When: Calling endpoint with failing memory service
        from app.api.v1.endpoints.agents import decompose_basic
        from app.models import DecomposeRequest

        background_tasks = BackgroundTasks()
        request = DecomposeRequest(
            canvas_name="Math53.canvas",
            node_id="node_fail"
        )

        # Then: Response is successful
        response = await decompose_basic(
            request=request,
            background_tasks=background_tasks,
            agent_service=mock_dependencies["agent_service"],
            context_service=mock_dependencies["context_service"],
            rag_service=mock_dependencies["rag_service"],
            memory_service=failing_memory_service,
        )

        # Response should be valid
        assert response.questions == ["问题1"]

        # Background task execution should not raise
        try:
            await background_tasks()
        except Exception as e:
            pytest.fail(f"Background task failure should not propagate: {e}")


class TestAllExplainEndpointsRecording:
    """Test all 6 explain endpoints record learning events."""

    @pytest.fixture
    def mock_deps(self):
        """Create mock dependencies for all explain endpoints."""
        context_service = AsyncMock()
        context_service.enrich_with_adjacent_nodes = AsyncMock(
            return_value=MockEnrichedContext()
        )

        agent_service = AsyncMock()
        agent_service.generate_explanation = AsyncMock(
            return_value={"explanation": "解释内容", "created_node_id": "new1"}
        )

        return {
            "agent_service": agent_service,
            "context_service": context_service,
            "rag_service": MockRAGService(),
        }

    @pytest.mark.asyncio
    @pytest.mark.parametrize("endpoint_func,agent_type", [
        ("explain_oral", "explain_oral"),
        ("explain_clarification", "explain_clarification"),
        ("explain_comparison", "explain_comparison"),
        ("explain_memory", "explain_memory"),
        ("explain_four_level", "explain_four-level"),
        ("explain_example", "explain_example"),
    ])
    async def test_explain_endpoint_records_event(
        self, mock_deps, endpoint_func, agent_type
    ):
        """AC-1: All explain endpoints trigger learning event recording."""
        from app.api.v1.endpoints import agents
        from app.models import ExplainRequest

        memory_service = MockMemoryService()
        background_tasks = BackgroundTasks()
        request = ExplainRequest(
            canvas_name="Math53.canvas",
            node_id=f"node_{endpoint_func}"
        )

        # Get the endpoint function
        endpoint = getattr(agents, endpoint_func)

        await endpoint(
            request=request,
            background_tasks=background_tasks,
            agent_service=mock_deps["agent_service"],
            context_service=mock_deps["context_service"],
            rag_service=mock_deps["rag_service"],
            memory_service=memory_service,
        )

        await background_tasks()

        # Verify recording
        assert memory_service.call_count == 1
        args = memory_service.last_call_args
        assert args["agent_type"] == agent_type
        assert args["canvas_path"] == "Math53.canvas"
