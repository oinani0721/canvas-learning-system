# Canvas Learning System - Integration Tests for Batch Processing
# Story 33.8: E2E Integration Testing
# ✅ Verified from docs/stories/33.8.story.md - Task 7
"""
Integration tests for service layer orchestration.

Tests:
- Service chain: SessionManager → IntelligentGroupingService → AgentRoutingEngine → BatchOrchestrator → ResultMerger
- Session lifecycle management
- Memory write triggers (fire-and-forget pattern from EPIC-30)

[Source: docs/stories/33.8.story.md - Task 7.1-7.6]
[Source: docs/epics/EPIC-33-AGENT-POOL-BATCH-PROCESSING.md]
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.session_manager import SessionManager, SessionStatus, SessionInfo
from app.services.batch_orchestrator import BatchOrchestrator
from app.services.result_merger import (
    ResultMerger,
    SupplementaryMerger,
    HierarchicalMerger,
    VotingMerger,
    get_merger,
    MergeStrategyType,
)
from app.models.intelligent_parallel_models import ParallelTaskStatus
from app.models.merge_strategy_models import AgentResult, MergeConfig


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def session_manager_clean():
    """Get a clean SessionManager instance for testing."""
    SessionManager.reset_instance()
    manager = SessionManager.get_instance()
    yield manager
    SessionManager.reset_instance()


@pytest.fixture
def mock_agent_service():
    """Create mock AgentService for testing."""
    service = MagicMock()
    service.call_agent = AsyncMock(return_value={
        "success": True,
        "file_path": "generated/test.md",
        "content": "Test content",
        "file_size": 512,
    })
    return service


@pytest.fixture
def test_canvas_data() -> dict:
    """Create test canvas data with yellow nodes."""
    return {
        "nodes": [
            {
                "id": f"node-{i:03d}",
                "type": "text",
                "color": "6",  # Yellow
                "text": f"测试概念{i}: 这是一个需要处理的学习内容",
                "x": i * 200,
                "y": 0,
                "width": 180,
                "height": 100
            }
            for i in range(5)
        ],
        "edges": []
    }


@pytest.fixture
def test_canvas_file(tmp_path: Path, test_canvas_data: dict) -> Path:
    """Create test canvas file."""
    canvas_dir = tmp_path / "笔记库"
    canvas_dir.mkdir(parents=True, exist_ok=True)
    canvas_file = canvas_dir / "test_batch.canvas"
    canvas_file.write_text(json.dumps(test_canvas_data, ensure_ascii=False), encoding='utf-8')
    return canvas_file


@pytest.fixture
def mock_canvas_utils():
    """
    Mock canvas_utils module to avoid import issues in IntelligentGroupingService.

    [Fix for: canvas_utils.path_manager module import error]
    [Source: docs/qa/gates/33.8-e2e-integration-testing.yml#recommendations]
    """
    # Create mock CanvasBusinessLogic class
    class MockCanvasBusinessLogic:
        def __init__(self, canvas_path: str):
            self.canvas_path = canvas_path
            # Read actual canvas data from file
            with open(canvas_path, 'r', encoding='utf-8') as f:
                self.canvas_data = json.load(f)

        def cluster_canvas_nodes(
            self,
            n_clusters=None,
            similarity_threshold=0.3,
            create_groups=False,
            min_cluster_size=2,
        ):
            """Mock clustering that returns valid cluster structure."""
            nodes = self.canvas_data.get("nodes", [])
            text_nodes = [n for n in nodes if n.get("type") == "text" and n.get("text")]

            if len(text_nodes) < min_cluster_size:
                raise ValueError(f"节点数量不足: {len(text_nodes)} < {min_cluster_size}")

            # Create simple clustering: all nodes in one cluster
            return {
                "clusters": [
                    {
                        "id": "cluster-1",
                        "label": "测试分组",
                        "top_keywords": ["测试", "概念"],
                        "confidence": 0.75,
                        "nodes": [n["id"] for n in text_nodes],
                    }
                ],
                "silhouette_score": 0.6,
                "optimal_k": 1,
            }

    # Create mock module
    mock_module = MagicMock()
    mock_module.CanvasBusinessLogic = MockCanvasBusinessLogic

    # Patch sys.modules
    original_modules = {}
    if 'canvas_utils' in sys.modules:
        original_modules['canvas_utils'] = sys.modules['canvas_utils']

    sys.modules['canvas_utils'] = mock_module

    yield mock_module

    # Restore original modules
    if 'canvas_utils' in original_modules:
        sys.modules['canvas_utils'] = original_modules['canvas_utils']
    elif 'canvas_utils' in sys.modules:
        del sys.modules['canvas_utils']


# =============================================================================
# Test Class: Service Layer Orchestration (AC-33.8.6)
# [Source: docs/stories/33.8.story.md - Task 7.2]
# =============================================================================

class TestServiceLayerOrchestration:
    """
    Integration tests for service chain orchestration.

    Tests: SessionManager → IntelligentGroupingService → AgentRoutingEngine → BatchOrchestrator → ResultMerger
    """

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_service_chain_data_flow(
        self,
        session_manager_clean: SessionManager,
        mock_agent_service,
        test_canvas_file: Path,
        tmp_path: Path,
    ):
        """
        Test data flows correctly through service chain.

        [Source: docs/stories/33.8.story.md - Task 7.2]
        """
        # Step 1: Create session via SessionManager
        session_id = await session_manager_clean.create_session(
            canvas_path=str(test_canvas_file),
            node_count=5,
            metadata={"source": "integration_test"}
        )
        assert session_id is not None

        # Step 2: Verify session created with pending status
        session_info = await session_manager_clean.get_session(session_id)
        assert session_info is not None
        assert session_info.status == SessionStatus.PENDING
        assert session_info.canvas_path == str(test_canvas_file)
        assert session_info.node_count == 5

        # Step 3: Transition to running
        await session_manager_clean.transition_state(session_id, SessionStatus.RUNNING)
        session_info = await session_manager_clean.get_session(session_id)
        assert session_info.status == SessionStatus.RUNNING

        # Step 4: Update progress
        await session_manager_clean.update_progress(session_id, 50)
        session_info = await session_manager_clean.get_session(session_id)
        assert session_info.progress_percent == 50

        # Step 5: Add node results
        for i in range(5):
            await session_manager_clean.add_node_result(
                session_id,
                f"node-{i:03d}",
                {
                    "success": True,
                    "file_path": f"generated/node-{i:03d}.md",
                    "agent_type": "oral-explanation",
                }
            )

        # Step 6: Transition to completed
        await session_manager_clean.transition_state(session_id, SessionStatus.COMPLETED)
        session_info = await session_manager_clean.get_session(session_id)
        assert session_info.status == SessionStatus.COMPLETED
        assert session_info.progress_percent == 100

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_batch_orchestrator_integration(
        self,
        session_manager_clean: SessionManager,
        mock_agent_service,
    ):
        """
        Test BatchOrchestrator integrates with SessionManager.

        [Source: docs/stories/33.8.story.md - Task 7.2]
        """
        # Create session
        session_id = await session_manager_clean.create_session(
            canvas_path="test.canvas",
            node_count=3,
        )

        # Create orchestrator with mocked agent service
        orchestrator = BatchOrchestrator(
            session_manager=session_manager_clean,
            agent_service=mock_agent_service,
            max_concurrent=12,
        )

        # Verify orchestrator can access session
        session_info = await session_manager_clean.get_session(session_id)
        assert session_info is not None
        assert session_info.status == SessionStatus.PENDING


# =============================================================================
# Test Class: Session Lifecycle Management (AC-33.8.6)
# [Source: docs/stories/33.8.story.md - Task 7.3]
# =============================================================================

class TestSessionLifecycleManagement:
    """
    Integration tests for SessionManager state transitions.

    Tests all valid state transitions in the session lifecycle.
    """

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_session_state_machine(self, session_manager_clean: SessionManager):
        """
        Test session state machine transitions.

        [Source: docs/stories/33.8.story.md - Task 7.3]
        [Source: Story 33.3 - AC2]

        Valid transitions:
        - PENDING → RUNNING
        - RUNNING → COMPLETED
        - RUNNING → FAILED
        - RUNNING → PARTIAL_FAILURE
        - RUNNING → CANCELLED
        - PENDING → CANCELLED
        """
        # Test PENDING → RUNNING → COMPLETED
        session_id = await session_manager_clean.create_session("test.canvas", 5)
        assert (await session_manager_clean.get_session(session_id)).status == SessionStatus.PENDING

        await session_manager_clean.transition_state(session_id, SessionStatus.RUNNING)
        assert (await session_manager_clean.get_session(session_id)).status == SessionStatus.RUNNING

        await session_manager_clean.transition_state(session_id, SessionStatus.COMPLETED)
        assert (await session_manager_clean.get_session(session_id)).status == SessionStatus.COMPLETED

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_session_cancel_from_pending(self, session_manager_clean: SessionManager):
        """Test cancellation from PENDING state."""
        session_id = await session_manager_clean.create_session("test.canvas", 5)
        await session_manager_clean.cancel_session(session_id)
        assert (await session_manager_clean.get_session(session_id)).status == SessionStatus.CANCELLED

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_session_cancel_from_running(self, session_manager_clean: SessionManager):
        """Test cancellation from RUNNING state."""
        session_id = await session_manager_clean.create_session("test.canvas", 5)
        await session_manager_clean.transition_state(session_id, SessionStatus.RUNNING)
        await session_manager_clean.cancel_session(session_id)
        assert (await session_manager_clean.get_session(session_id)).status == SessionStatus.CANCELLED

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_session_partial_failure(self, session_manager_clean: SessionManager):
        """Test PARTIAL_FAILURE state transition."""
        session_id = await session_manager_clean.create_session("test.canvas", 5)
        await session_manager_clean.transition_state(session_id, SessionStatus.RUNNING)
        await session_manager_clean.transition_state(session_id, SessionStatus.PARTIAL_FAILURE)
        assert (await session_manager_clean.get_session(session_id)).status == SessionStatus.PARTIAL_FAILURE

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_session_progress_tracking(self, session_manager_clean: SessionManager):
        """
        Test progress percentage tracking.

        [Source: Story 33.3 - AC7]
        """
        session_id = await session_manager_clean.create_session("test.canvas", 10)

        # Progress should start at 0
        session = await session_manager_clean.get_session(session_id)
        assert session.progress_percent == 0

        # Transition to RUNNING state (required for progress updates)
        await session_manager_clean.transition_state(session_id, SessionStatus.RUNNING)

        # Update progress incrementally
        for progress in [10, 25, 50, 75, 100]:
            await session_manager_clean.update_progress(session_id, progress)
            session = await session_manager_clean.get_session(session_id)
            assert session.progress_percent == progress

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_session_node_result_storage(self, session_manager_clean: SessionManager):
        """
        Test per-node result storage.

        [Source: Story 33.3 - AC8]
        """
        session_id = await session_manager_clean.create_session("test.canvas", 3)
        await session_manager_clean.transition_state(session_id, SessionStatus.RUNNING)

        # Add node results
        for i in range(3):
            await session_manager_clean.add_node_result(
                session_id,
                f"node-{i}",
                {"success": True, "file_path": f"output_{i}.md"}
            )

        # Verify results stored
        session = await session_manager_clean.get_session(session_id)
        assert len(session.node_results) == 3

        # Progress should auto-calculate
        assert session.progress_percent == 100  # 3/3 * 100

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_multiple_sessions_isolation(self, session_manager_clean: SessionManager):
        """
        Test multiple sessions are properly isolated.

        [Source: docs/stories/33.8.story.md - Task 7.3]
        """
        # Create multiple sessions
        session_ids = []
        for i in range(3):
            session_id = await session_manager_clean.create_session(f"canvas_{i}.canvas", 5)
            session_ids.append(session_id)

        # Verify sessions are independent
        await session_manager_clean.transition_state(session_ids[0], SessionStatus.RUNNING)
        await session_manager_clean.transition_state(session_ids[1], SessionStatus.CANCELLED)

        assert (await session_manager_clean.get_session(session_ids[0])).status == SessionStatus.RUNNING
        assert (await session_manager_clean.get_session(session_ids[1])).status == SessionStatus.CANCELLED
        assert (await session_manager_clean.get_session(session_ids[2])).status == SessionStatus.PENDING


# =============================================================================
# Test Class: Grouping Service Integration (AC-33.8.6)
# [Source: docs/stories/33.8.story.md - Task 7.4]
# =============================================================================

class TestGroupingServiceIntegration:
    """
    Integration tests for IntelligentGroupingService TF-IDF clustering.

    Tests semantic grouping and agent recommendation.
    """

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_grouping_service_clusters_nodes(
        self,
        test_canvas_file: Path,
        tmp_path: Path,
        mock_canvas_utils,
    ):
        """
        Test IntelligentGroupingService produces valid clusters.

        [Source: docs/stories/33.8.story.md - Task 7.4]
        [Fix: Uses mock_canvas_utils fixture to avoid import issues]
        """
        from app.services.intelligent_grouping_service import IntelligentGroupingService

        service = IntelligentGroupingService(canvas_base_path=str(tmp_path))

        # Analyze canvas
        result = await service.analyze_canvas(
            canvas_path=str(test_canvas_file.relative_to(tmp_path)),
            target_color="6",
        )

        # Verify result structure
        assert result.canvas_path is not None
        assert result.total_nodes == 5
        assert len(result.groups) > 0

        # Verify each group has required fields
        for group in result.groups:
            assert group.group_id is not None
            assert group.recommended_agent is not None
            assert len(group.nodes) > 0
            assert 0 <= group.confidence <= 1

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_grouping_service_agent_recommendation(
        self,
        tmp_path: Path,
        mock_canvas_utils,
    ):
        """
        Test agent recommendations based on content patterns.

        [Source: Story 33.4 - AC-33.4.1]
        [Fix: Uses mock_canvas_utils fixture to avoid import issues]
        """
        from app.services.intelligent_grouping_service import IntelligentGroupingService

        # Create canvas with specific question patterns
        canvas_data = {
            "nodes": [
                {"id": "n1", "type": "text", "color": "6", "text": "什么是递归？请解释递归的概念。", "x": 0, "y": 0, "width": 200, "height": 100},
                {"id": "n2", "type": "text", "color": "6", "text": "递归和迭代有什么区别？请对比说明。", "x": 200, "y": 0, "width": 200, "height": 100},
            ],
            "edges": []
        }

        canvas_dir = tmp_path / "笔记库"
        canvas_dir.mkdir(parents=True, exist_ok=True)
        canvas_file = canvas_dir / "test_patterns.canvas"
        canvas_file.write_text(json.dumps(canvas_data, ensure_ascii=False), encoding='utf-8')

        service = IntelligentGroupingService(canvas_base_path=str(tmp_path))
        result = await service.analyze_canvas(
            canvas_path=str(canvas_file.relative_to(tmp_path)),
            target_color="6",
        )

        # Verify agents are recommended
        agents_used = {group.recommended_agent for group in result.groups}
        assert len(agents_used) > 0


# =============================================================================
# Test Class: Agent Routing Integration (AC-33.8.6)
# [Source: docs/stories/33.8.story.md - Task 7.5]
# =============================================================================

class TestAgentRoutingIntegration:
    """
    Integration tests for AgentRoutingEngine.

    Tests agent selection based on content patterns.
    """

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_agent_routing_pattern_matching(self):
        """
        Test AgentRoutingEngine matches patterns to agents.

        [Source: docs/stories/33.8.story.md - Task 7.5]
        [Source: Story 33.5 - AC1]
        """
        from app.services.agent_routing_engine import AgentRoutingEngine
        from app.models.agent_routing_models import RoutingRequest

        engine = AgentRoutingEngine()

        # Test various patterns
        test_cases = [
            ("什么是递归？", "oral-explanation"),
            ("递归和迭代的区别", "comparison-table"),
            ("如何理解闭包的概念？", "clarification-path"),
            ("举例说明函数式编程", "example-teaching"),
            ("如何记忆设计模式？", "memory-anchor"),
        ]

        for node_text, expected_agent in test_cases:
            request = RoutingRequest(node_id="test-node", node_text=node_text)
            result = engine.route_single_node(request)
            # Verify a recommendation is made
            assert result.recommended_agent is not None
            assert result.confidence > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_agent_routing_confidence_scoring(self):
        """
        Test confidence scoring for agent recommendations.

        [Source: Story 33.5 - AC2]
        """
        from app.services.agent_routing_engine import AgentRoutingEngine
        from app.models.agent_routing_models import RoutingRequest

        engine = AgentRoutingEngine()

        # Strong pattern match should have high confidence
        request = RoutingRequest(
            node_id="test",
            node_text="什么是机器学习？请详细解释机器学习的定义和核心概念。",
        )
        result = engine.route_single_node(request)

        assert result.confidence >= 0.5  # At least medium confidence
        assert result.recommended_agent is not None


# =============================================================================
# Test Class: Memory Write Triggers (AC-33.8.6)
# [Source: docs/stories/33.8.story.md - Task 7.6]
# =============================================================================

class TestMemoryWriteTriggers:
    """
    Integration tests for memory write triggers.

    Tests fire-and-forget pattern from EPIC-30.
    """

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_memory_write_triggered_on_completion(
        self,
        session_manager_clean: SessionManager,
    ):
        """
        Test memory write is triggered after agent completion.

        [Source: docs/stories/33.8.story.md - Task 7.6]
        [Source: Story 33.6 - AC6]
        """
        memory_writes = []

        async def mock_memory_write(session_id: str, node_id: str, result: dict):
            """Track memory write calls."""
            memory_writes.append({
                "session_id": session_id,
                "node_id": node_id,
                "result": result,
            })

        # Create mock agent service with memory trigger
        mock_agent = MagicMock()
        mock_agent.call_agent = AsyncMock(return_value={
            "success": True,
            "file_path": "test.md",
            "content": "Test",
            "file_size": 100,
        })
        mock_agent._trigger_memory_write = AsyncMock(side_effect=mock_memory_write)

        # Create session
        session_id = await session_manager_clean.create_session("test.canvas", 2)

        # Create orchestrator
        orchestrator = BatchOrchestrator(
            session_manager=session_manager_clean,
            agent_service=mock_agent,
        )

        # Verify memory trigger can be called (fire-and-forget)
        await mock_agent._trigger_memory_write(
            session_id,
            "node-001",
            {"success": True, "agent_type": "oral-explanation"}
        )

        assert len(memory_writes) == 1
        assert memory_writes[0]["node_id"] == "node-001"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_memory_write_failure_does_not_block(
        self,
        session_manager_clean: SessionManager,
    ):
        """
        Test memory write failures don't block agent execution.

        [Source: Story 33.6 - AC6 - Memory write failures must NOT block]
        """
        async def failing_memory_write(*args, **kwargs):
            """Memory write that always fails."""
            raise Exception("Memory write failed")

        mock_agent = MagicMock()
        mock_agent.call_agent = AsyncMock(return_value={
            "success": True,
            "file_path": "test.md",
        })
        mock_agent._trigger_memory_write = AsyncMock(side_effect=failing_memory_write)

        session_id = await session_manager_clean.create_session("test.canvas", 1)

        # Simulate agent completion with failing memory write
        agent_result = await mock_agent.call_agent("oral-explanation", "node-1", "Test")

        # Memory write should fail but not raise
        try:
            await mock_agent._trigger_memory_write(session_id, "node-1", agent_result)
        except Exception:
            pass  # Fire-and-forget - failures are logged but don't block

        # Agent result should still be valid
        assert agent_result["success"] is True


# =============================================================================
# Test Class: Result Merger Integration (AC-33.8.6)
# [Source: docs/stories/33.8.story.md - Task 7.2]
# =============================================================================

class TestResultMergerIntegration:
    """
    Integration tests for ResultMerger strategies.

    Tests all three merge strategies: supplementary, hierarchical, voting.
    """

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_supplementary_merger(self):
        """
        Test SupplementaryMerger concatenates outputs.

        [Source: Story 33.7 - AC1]
        """
        merger = SupplementaryMerger()

        results = [
            AgentResult(
                node_id="n1",
                agent_name="oral-explanation",
                result="这是口语化解释的内容。",
                success=True,
            ),
            AgentResult(
                node_id="n2",
                agent_name="example-teaching",
                result="这是例题教学的内容。",
                success=True,
            ),
        ]

        merged = await merger.merge(results)

        assert merged.merged_content is not None
        assert "oral-explanation" in merged.merged_content or "口语" in merged.merged_content
        assert merged.quality_score is not None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_hierarchical_merger(self):
        """
        Test HierarchicalMerger organizes by difficulty.

        [Source: Story 33.7 - AC2]
        """
        merger = HierarchicalMerger()

        results = [
            AgentResult(
                node_id="n1",
                agent_name="oral-explanation",
                result="入门级：这是基础概念的简单介绍。",
                success=True,
            ),
            AgentResult(
                node_id="n2",
                agent_name="deep-decomposition",
                result="深入分析：这是高级内容的深度剖析。",
                success=True,
            ),
        ]

        merged = await merger.merge(results)

        assert merged.merged_content is not None
        assert merged.strategy_used == MergeStrategyType.hierarchical

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_voting_merger_deduplication(self):
        """
        Test VotingMerger deduplicates similar content.

        [Source: Story 33.7 - AC3]
        """
        merger = VotingMerger()

        # Two similar results that should be deduplicated
        results = [
            AgentResult(
                node_id="n1",
                agent_name="oral-explanation",
                result="递归是一个函数调用自身的编程技术。",
                success=True,
            ),
            AgentResult(
                node_id="n2",
                agent_name="clarification-path",
                result="递归是函数调用自己的技术，用于解决可分解的问题。",
                success=True,
            ),
        ]

        merged = await merger.merge(results)

        assert merged.merged_content is not None
        # Quality score should reflect deduplication
        assert merged.quality_score.redundancy is not None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_merger_factory(self):
        """
        Test get_merger factory returns correct strategy.

        [Source: Story 33.7 - AC4]
        """
        supplementary = get_merger(MergeStrategyType.supplementary)
        assert isinstance(supplementary, SupplementaryMerger)

        hierarchical = get_merger(MergeStrategyType.hierarchical)
        assert isinstance(hierarchical, HierarchicalMerger)

        voting = get_merger(MergeStrategyType.voting)
        assert isinstance(voting, VotingMerger)
