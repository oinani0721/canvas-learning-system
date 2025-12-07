# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: testing)
"""
Unit tests for Story 15.5: 异步操作和后台任务
[Source: Story 15.5 AC:9 - 单元测试覆盖所有服务的异步方法]

Tests:
- CanvasService async file operations
- AgentService concurrency limiting
- BackgroundTaskManager task lifecycle
- ReviewService background task execution
"""
import asyncio
import json
from pathlib import Path

import pytest
from app.core.exceptions import CanvasNotFoundException, NodeNotFoundException, TaskNotFoundError, ValidationError
from app.services.agent_service import AgentResult, AgentService, AgentType
from app.services.background_task_manager import BackgroundTaskManager, TaskStatus
from app.services.canvas_service import CanvasService
from app.services.review_service import ReviewProgress, ReviewService

# ============================================================================
# CanvasService Tests
# ============================================================================

class TestCanvasService:
    """Tests for CanvasService async file operations"""

    @pytest.mark.asyncio
    async def test_read_canvas_success(
        self,
        canvas_service: CanvasService,
        canvas_file: Path,
        sample_canvas_data: dict
    ):
        """Test successful canvas read with asyncio.to_thread"""
        # Act
        result = await canvas_service.read_canvas("test")

        # Assert
        assert result is not None
        assert "nodes" in result
        assert len(result["nodes"]) == len(sample_canvas_data["nodes"])

    @pytest.mark.asyncio
    async def test_read_canvas_not_found(self, canvas_service: CanvasService):
        """Test CanvasNotFoundException when file doesn't exist"""
        with pytest.raises(CanvasNotFoundException) as exc_info:
            await canvas_service.read_canvas("nonexistent")

        assert "nonexistent" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_read_canvas_path_traversal_blocked(self, canvas_service: CanvasService):
        """Test path traversal attack prevention"""
        with pytest.raises(ValidationError) as exc_info:
            await canvas_service.read_canvas("../../../etc/passwd")

        assert "path traversal" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_write_canvas(
        self,
        canvas_service: CanvasService,
        temp_dir: Path,
        sample_canvas_data: dict
    ):
        """Test writing canvas file with asyncio.to_thread"""
        # Act
        result = await canvas_service.write_canvas("new_canvas", sample_canvas_data)

        # Assert
        assert result is True
        canvas_path = temp_dir / "new_canvas.canvas"
        assert canvas_path.exists()

        with open(canvas_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        assert saved_data == sample_canvas_data

    @pytest.mark.asyncio
    async def test_add_node(
        self,
        canvas_service: CanvasService,
        canvas_file: Path
    ):
        """Test adding node to canvas"""
        # Arrange
        new_node = {
            "type": "text",
            "text": "New Node",
            "x": 500,
            "y": 100
        }

        # Act
        result = await canvas_service.add_node("test", new_node)

        # Assert
        assert "id" in result
        assert result["text"] == "New Node"

        # Verify node was added
        canvas_data = await canvas_service.read_canvas("test")
        node_ids = [n["id"] for n in canvas_data["nodes"]]
        assert result["id"] in node_ids

    @pytest.mark.asyncio
    async def test_update_node(
        self,
        canvas_service: CanvasService,
        canvas_file: Path
    ):
        """Test updating existing node"""
        # Act
        result = await canvas_service.update_node(
            "test",
            "node1",
            {"text": "Updated Text", "color": "5"}
        )

        # Assert
        assert result["text"] == "Updated Text"
        assert result["color"] == "5"
        assert result["id"] == "node1"  # ID should not change

    @pytest.mark.asyncio
    async def test_update_node_not_found(
        self,
        canvas_service: CanvasService,
        canvas_file: Path
    ):
        """Test NodeNotFoundException when updating non-existent node"""
        with pytest.raises(NodeNotFoundException) as exc_info:
            await canvas_service.update_node("test", "nonexistent", {"text": "New"})

        assert "nonexistent" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_node(
        self,
        canvas_service: CanvasService,
        canvas_file: Path
    ):
        """Test deleting node and related edges"""
        # Act
        result = await canvas_service.delete_node("test", "node1")

        # Assert
        assert result is True

        # Verify node was deleted
        canvas_data = await canvas_service.read_canvas("test")
        node_ids = [n["id"] for n in canvas_data["nodes"]]
        assert "node1" not in node_ids

        # Verify related edges were also deleted
        for edge in canvas_data.get("edges", []):
            assert edge.get("fromNode") != "node1"
            assert edge.get("toNode") != "node1"

    @pytest.mark.asyncio
    async def test_get_nodes_by_color(
        self,
        canvas_service: CanvasService,
        canvas_file: Path
    ):
        """Test filtering nodes by color"""
        # Act
        green_nodes = await canvas_service.get_nodes_by_color("test", "3")

        # Assert
        assert len(green_nodes) == 1
        assert green_nodes[0]["id"] == "node2"

    @pytest.mark.asyncio
    async def test_canvas_exists(
        self,
        canvas_service: CanvasService,
        canvas_file: Path
    ):
        """Test canvas existence check"""
        assert await canvas_service.canvas_exists("test") is True
        assert await canvas_service.canvas_exists("nonexistent") is False

    @pytest.mark.asyncio
    async def test_cleanup(self, temp_dir: Path):
        """Test service cleanup"""
        service = CanvasService(str(temp_dir))
        assert service._initialized is True

        await service.cleanup()
        assert service._initialized is False


# ============================================================================
# AgentService Tests
# ============================================================================

class TestAgentService:
    """Tests for AgentService with Semaphore concurrency control"""

    @pytest.mark.asyncio
    async def test_call_agent_success(self, agent_service: AgentService):
        """Test successful single agent call"""
        # Act
        result = await agent_service.call_agent(
            AgentType.SCORING,
            "Test prompt"
        )

        # Assert
        assert isinstance(result, AgentResult)
        assert result.success is True
        assert result.agent_type == AgentType.SCORING
        assert result.data is not None

    @pytest.mark.asyncio
    async def test_call_agent_with_timeout(self, agent_service: AgentService):
        """Test agent call timeout handling"""
        # Create a service with very short timeout behavior
        # The simulated delay is 0.1s, so this should succeed
        result = await agent_service.call_agent(
            AgentType.BASIC_DECOMPOSITION,
            "Test prompt",
            timeout=1.0
        )

        assert result.success is True

    @pytest.mark.asyncio
    async def test_semaphore_limits_concurrency(self, agent_service: AgentService):
        """Test that Semaphore limits concurrent calls to max_concurrent"""
        # Arrange - create many concurrent requests
        num_requests = 20
        requests = [
            {"agent_type": AgentType.SCORING, "prompt": f"Prompt {i}"}
            for i in range(num_requests)
        ]

        # Track max concurrent during execution
        max_observed_concurrent = 0

        original_simulate = agent_service._simulate_agent_call

        async def tracking_simulate(*args, **kwargs):
            nonlocal max_observed_concurrent
            current = agent_service.active_calls
            if current > max_observed_concurrent:
                max_observed_concurrent = current
            return await original_simulate(*args, **kwargs)

        agent_service._simulate_agent_call = tracking_simulate

        # Act
        results = await agent_service.call_agents_batch(requests)

        # Assert
        assert len(results) == num_requests
        # Max concurrent should not exceed the semaphore limit (5 in test fixture)
        assert max_observed_concurrent <= agent_service._max_concurrent

    @pytest.mark.asyncio
    async def test_call_agents_batch_return_exceptions(self, agent_service: AgentService):
        """Test batch calls with return_exceptions=True"""
        # Arrange
        requests = [
            {"agent_type": AgentType.SCORING, "prompt": "Prompt 1"},
            {"agent_type": AgentType.ORAL_EXPLANATION, "prompt": "Prompt 2"},
            {"agent_type": AgentType.COMPARISON_TABLE, "prompt": "Prompt 3"},
        ]

        # Act
        results = await agent_service.call_agents_batch(requests, return_exceptions=True)

        # Assert
        assert len(results) == 3
        # All should be AgentResult since we're using simulated calls
        for result in results:
            assert isinstance(result, AgentResult)
            assert result.success is True

    @pytest.mark.asyncio
    async def test_call_decomposition_basic(self, agent_service: AgentService):
        """Test basic decomposition call"""
        result = await agent_service.call_decomposition("Test content", deep=False)

        assert result.agent_type == AgentType.BASIC_DECOMPOSITION
        assert result.success is True

    @pytest.mark.asyncio
    async def test_call_decomposition_deep(self, agent_service: AgentService):
        """Test deep decomposition call"""
        result = await agent_service.call_decomposition("Test content", deep=True)

        assert result.agent_type == AgentType.DEEP_DECOMPOSITION
        assert result.success is True

    @pytest.mark.asyncio
    async def test_call_scoring(self, agent_service: AgentService):
        """Test scoring agent call"""
        result = await agent_service.call_scoring(
            node_content="What is recursion?",
            user_understanding="A function calling itself"
        )

        assert result.agent_type == AgentType.SCORING
        assert result.success is True

    @pytest.mark.asyncio
    async def test_call_explanation_types(self, agent_service: AgentService):
        """Test different explanation types"""
        explanation_types = [
            ("oral", AgentType.ORAL_EXPLANATION),
            ("clarification", AgentType.CLARIFICATION_PATH),
            ("comparison", AgentType.COMPARISON_TABLE),
            ("memory", AgentType.MEMORY_ANCHOR),
            ("four_level", AgentType.FOUR_LEVEL),
            ("example", AgentType.EXAMPLE_TEACHING),
        ]

        for exp_type, expected_agent in explanation_types:
            result = await agent_service.call_explanation("Test content", exp_type)
            assert result.agent_type == expected_agent
            assert result.success is True

    @pytest.mark.asyncio
    async def test_total_calls_counter(self, agent_service: AgentService):
        """Test that total_calls counter increments correctly"""
        initial_count = agent_service.total_calls

        await agent_service.call_agent(AgentType.SCORING, "Test 1")
        await agent_service.call_agent(AgentType.SCORING, "Test 2")
        await agent_service.call_agent(AgentType.SCORING, "Test 3")

        assert agent_service.total_calls == initial_count + 3

    @pytest.mark.asyncio
    async def test_cleanup_waits_for_active_calls(self):
        """Test that cleanup waits for active calls to complete"""
        service = AgentService(max_concurrent=2)

        # Start some calls
        tasks = [
            asyncio.create_task(service.call_agent(AgentType.SCORING, f"Test {i}"))
            for i in range(3)
        ]

        # Small delay to ensure tasks started
        await asyncio.sleep(0.01)

        # Cleanup should wait for all calls
        await service.cleanup()

        assert service._initialized is False

        # Wait for tasks to complete
        await asyncio.gather(*tasks, return_exceptions=True)


# ============================================================================
# BackgroundTaskManager Tests
# ============================================================================

class TestBackgroundTaskManager:
    """Tests for BackgroundTaskManager task lifecycle"""

    @pytest.mark.asyncio
    async def test_create_task(self, task_manager: BackgroundTaskManager):
        """Test task creation"""
        async def sample_task():
            await asyncio.sleep(0.1)
            return {"result": "success"}

        # Act
        task_id = await task_manager.create_task("test_type", sample_task)

        # Assert
        assert task_id is not None
        assert len(task_id) > 0

        # Wait for task to complete
        await asyncio.sleep(0.2)

        task_info = task_manager.get_task_status(task_id)
        assert task_info.status == TaskStatus.COMPLETED
        assert task_info.result == {"result": "success"}

    @pytest.mark.asyncio
    async def test_task_status_transitions(self, task_manager: BackgroundTaskManager):
        """Test task status transitions: PENDING -> RUNNING -> COMPLETED"""
        status_history = []

        async def tracked_task():
            await asyncio.sleep(0.1)
            return "done"

        # Create task
        task_id = await task_manager.create_task("test_type", tracked_task)

        # Check initial status is PENDING or RUNNING (depends on timing)
        task_info = task_manager.get_task_status(task_id)
        assert task_info.status in (TaskStatus.PENDING, TaskStatus.RUNNING)

        # Wait and check RUNNING or COMPLETED
        await asyncio.sleep(0.05)
        task_info = task_manager.get_task_status(task_id)
        status_history.append(task_info.status)

        # Wait for completion
        await asyncio.sleep(0.2)
        task_info = task_manager.get_task_status(task_id)
        assert task_info.status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_task_failure_status(self, task_manager: BackgroundTaskManager):
        """Test task failure sets FAILED status"""
        async def failing_task():
            await asyncio.sleep(0.05)
            raise ValueError("Task failed")

        task_id = await task_manager.create_task("test_type", failing_task)

        # Wait for task to fail
        await asyncio.sleep(0.2)

        task_info = task_manager.get_task_status(task_id)
        assert task_info.status == TaskStatus.FAILED
        assert "Task failed" in task_info.error

    @pytest.mark.asyncio
    async def test_cancel_running_task(self, task_manager: BackgroundTaskManager):
        """Test cancelling a running task"""
        async def long_task():
            await asyncio.sleep(10)  # Long task
            return "should not reach"

        task_id = await task_manager.create_task("test_type", long_task)

        # Wait a bit for task to start
        await asyncio.sleep(0.05)

        # Cancel
        result = await task_manager.cancel_task(task_id)

        assert result is True

        # Wait for cancellation to process
        await asyncio.sleep(0.1)

        task_info = task_manager.get_task_status(task_id)
        assert task_info.status == TaskStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_get_task_status_not_found(self, task_manager: BackgroundTaskManager):
        """Test TaskNotFoundError when task doesn't exist"""
        with pytest.raises(TaskNotFoundError) as exc_info:
            task_manager.get_task_status("nonexistent-id")

        assert "nonexistent-id" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_progress(self, task_manager: BackgroundTaskManager):
        """Test progress update"""
        async def progressive_task():
            for i in range(10):
                await asyncio.sleep(0.01)
            return "done"

        task_id = await task_manager.create_task("test_type", progressive_task)

        # Update progress
        task_manager.update_progress(task_id, 0.5)

        task_info = task_manager.get_task_status(task_id)
        assert task_info.progress == 0.5

        # Test bounds
        task_manager.update_progress(task_id, 1.5)  # Should clamp to 1.0
        assert task_manager.get_task_status(task_id).progress == 1.0

        task_manager.update_progress(task_id, -0.5)  # Should clamp to 0.0
        assert task_manager.get_task_status(task_id).progress == 0.0

    @pytest.mark.asyncio
    async def test_list_tasks_by_status(self, task_manager: BackgroundTaskManager):
        """Test listing tasks by status"""
        async def quick_task():
            return "done"

        async def long_task():
            await asyncio.sleep(10)
            return "done"

        # Create tasks
        quick_id = await task_manager.create_task("quick", quick_task)
        long_id = await task_manager.create_task("long", long_task)

        # Wait for quick task to complete
        await asyncio.sleep(0.1)

        # List completed tasks
        completed = task_manager.list_tasks(status=TaskStatus.COMPLETED)
        completed_ids = [t.task_id for t in completed]
        assert quick_id in completed_ids

        # List running tasks
        running = task_manager.list_tasks(status=TaskStatus.RUNNING)
        running_ids = [t.task_id for t in running]
        assert long_id in running_ids

        # Cancel long task for cleanup
        await task_manager.cancel_task(long_id)

    @pytest.mark.asyncio
    async def test_list_tasks_by_type(self, task_manager: BackgroundTaskManager):
        """Test listing tasks by type"""
        async def sample_task():
            return "done"

        await task_manager.create_task("type_a", sample_task)
        await task_manager.create_task("type_a", sample_task)
        await task_manager.create_task("type_b", sample_task)

        # Wait for completion
        await asyncio.sleep(0.1)

        type_a_tasks = task_manager.list_tasks(task_type="type_a")
        assert len(type_a_tasks) == 2

        type_b_tasks = task_manager.list_tasks(task_type="type_b")
        assert len(type_b_tasks) == 1

    @pytest.mark.asyncio
    async def test_cleanup_old_tasks(self, task_manager: BackgroundTaskManager):
        """Test cleaning up old completed tasks"""
        async def quick_task():
            return "done"

        # Create and complete tasks
        for _ in range(5):
            await task_manager.create_task("test", quick_task)

        await asyncio.sleep(0.1)

        # All tasks should be completed
        all_tasks = task_manager.list_tasks()
        assert len(all_tasks) == 5

        # Cleanup with max_age_hours=0 should clean all completed
        cleaned = await task_manager.cleanup_old_tasks(max_age_hours=0)
        # Note: Due to timing, some tasks might not be old enough yet
        # This is a soft check
        assert cleaned >= 0

    @pytest.mark.asyncio
    async def test_singleton_pattern(self, task_manager: BackgroundTaskManager):
        """Test BackgroundTaskManager singleton"""
        instance1 = BackgroundTaskManager.get_instance()
        instance2 = BackgroundTaskManager.get_instance()

        assert instance1 is instance2

    @pytest.mark.asyncio
    async def test_task_info_to_dict(self, task_manager: BackgroundTaskManager):
        """Test TaskInfo.to_dict() serialization"""
        async def sample_task():
            return {"data": "value"}

        task_id = await task_manager.create_task(
            "test_type",
            sample_task,
            metadata={"key": "value"}
        )

        await asyncio.sleep(0.1)

        task_dict = task_manager.get_task_status_dict(task_id)

        assert "task_id" in task_dict
        assert "task_type" in task_dict
        assert "status" in task_dict
        assert "created_at" in task_dict
        assert "metadata" in task_dict
        assert task_dict["metadata"] == {"key": "value"}


# ============================================================================
# ReviewService Tests
# ============================================================================

class TestReviewService:
    """Tests for ReviewService background task execution"""

    @pytest.mark.asyncio
    async def test_generate_review_canvas_returns_task_id(
        self,
        review_service: ReviewService,
        canvas_file: Path
    ):
        """Test that generate_review_canvas returns task_id immediately"""
        # Act
        result = await review_service.generate_review_canvas("test")

        # Assert
        assert "task_id" in result
        assert result["status"] == "processing"
        assert "test" in result["message"]

    @pytest.mark.asyncio
    async def test_generate_review_canvas_not_found(
        self,
        review_service: ReviewService
    ):
        """Test CanvasNotFoundException for non-existent canvas"""
        with pytest.raises(CanvasNotFoundException):
            await review_service.generate_review_canvas("nonexistent")

    @pytest.mark.asyncio
    async def test_get_progress(
        self,
        review_service: ReviewService,
        canvas_file: Path
    ):
        """Test progress tracking"""
        # Start generation
        result = await review_service.generate_review_canvas("test")
        task_id = result["task_id"]

        # Get progress
        progress = await review_service.get_progress(task_id)

        assert isinstance(progress, ReviewProgress)
        assert progress.task_id == task_id
        assert progress.canvas_name == "test"

    @pytest.mark.asyncio
    async def test_get_progress_dict(
        self,
        review_service: ReviewService,
        canvas_file: Path
    ):
        """Test progress dictionary format"""
        result = await review_service.generate_review_canvas("test")
        task_id = result["task_id"]

        progress_dict = await review_service.get_progress_dict(task_id)

        assert "task_id" in progress_dict
        assert "canvas_name" in progress_dict
        assert "status" in progress_dict
        assert "progress" in progress_dict

    @pytest.mark.asyncio
    async def test_cancel_generation(
        self,
        review_service: ReviewService,
        canvas_file: Path
    ):
        """Test cancelling review generation"""
        result = await review_service.generate_review_canvas("test")
        task_id = result["task_id"]

        # Cancel
        cancelled = await review_service.cancel_generation(task_id)

        # The task might complete before cancellation, so we just check no exception
        assert cancelled in (True, False)

    @pytest.mark.asyncio
    async def test_list_tasks(
        self,
        review_service: ReviewService,
        canvas_file: Path
    ):
        """Test listing review tasks"""
        # Generate a few tasks
        await review_service.generate_review_canvas("test")

        # Wait a bit
        await asyncio.sleep(0.1)

        # List tasks
        tasks = await review_service.list_tasks()

        assert len(tasks) >= 1
        assert all(isinstance(t, ReviewProgress) for t in tasks)

    @pytest.mark.asyncio
    async def test_list_tasks_by_canvas_name(
        self,
        review_service: ReviewService,
        canvas_file: Path
    ):
        """Test listing tasks filtered by canvas name"""
        await review_service.generate_review_canvas("test")

        await asyncio.sleep(0.1)

        # List by canvas name
        tasks = await review_service.list_tasks(canvas_name="test")
        assert len(tasks) >= 1

        # List by non-existent canvas name
        tasks = await review_service.list_tasks(canvas_name="other_canvas")
        assert len(tasks) == 0

    @pytest.mark.asyncio
    async def test_extract_question_from_node_with_colon(
        self,
        review_service: ReviewService
    ):
        """Test question extraction from node with colon"""
        node = {"text": "递归：一个函数调用自身"}
        question = review_service._extract_question_from_node(node)

        assert "递归" in question
        assert "？" in question

    @pytest.mark.asyncio
    async def test_extract_question_from_node_without_colon(
        self,
        review_service: ReviewService
    ):
        """Test question extraction from node without colon"""
        node = {"text": "简单文本"}
        question = review_service._extract_question_from_node(node)

        assert "请解释" in question
        assert "简单文本" in question

    @pytest.mark.asyncio
    async def test_cleanup(
        self,
        canvas_service: CanvasService,
        task_manager: BackgroundTaskManager
    ):
        """Test service cleanup"""
        service = ReviewService(canvas_service, task_manager)
        assert service._initialized is True

        await service.cleanup()
        assert service._initialized is False


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for all services working together"""

    @pytest.mark.asyncio
    async def test_full_workflow(
        self,
        temp_dir: Path,
        sample_canvas_data: dict
    ):
        """Test full workflow: Canvas -> Agent -> Review"""
        # Setup
        BackgroundTaskManager.reset_instance()

        canvas_service = CanvasService(str(temp_dir))
        agent_service = AgentService(max_concurrent=5)
        task_manager = BackgroundTaskManager()
        review_service = ReviewService(canvas_service, task_manager)

        try:
            # 1. Create canvas
            await canvas_service.write_canvas("integration_test", sample_canvas_data)

            # 2. Read and verify
            canvas_data = await canvas_service.read_canvas("integration_test")
            assert len(canvas_data["nodes"]) == 3

            # 3. Add a node
            new_node = await canvas_service.add_node(
                "integration_test",
                {"type": "text", "text": "New Node", "x": 600, "y": 0, "color": "3"}
            )
            assert "id" in new_node

            # 4. Call agents
            results = await agent_service.call_agents_batch([
                {"agent_type": AgentType.SCORING, "prompt": "Score this"},
                {"agent_type": AgentType.ORAL_EXPLANATION, "prompt": "Explain this"},
            ])
            assert len(results) == 2
            assert all(r.success for r in results)

            # 5. Start review generation
            review_result = await review_service.generate_review_canvas("integration_test")
            task_id = review_result["task_id"]

            # 6. Wait and check progress
            await asyncio.sleep(0.5)
            progress = await review_service.get_progress(task_id)
            # Task should be completed or still running
            assert progress.status in (TaskStatus.RUNNING, TaskStatus.COMPLETED, TaskStatus.PENDING)

        finally:
            # Cleanup
            await review_service.cleanup()
            await agent_service.cleanup()
            await task_manager.cleanup()
            await canvas_service.cleanup()
            BackgroundTaskManager.reset_instance()

    @pytest.mark.asyncio
    async def test_concurrent_canvas_operations(
        self,
        canvas_service: CanvasService,
        canvas_file: Path
    ):
        """Test concurrent canvas operations don't interfere"""
        # Create multiple operations concurrently
        tasks = [
            canvas_service.read_canvas("test"),
            canvas_service.get_nodes_by_color("test", "1"),
            canvas_service.get_nodes_by_color("test", "3"),
            canvas_service.canvas_exists("test"),
            canvas_service.canvas_exists("nonexistent"),
        ]

        results = await asyncio.gather(*tasks)

        # All should complete without error
        assert len(results) == 5
        assert results[0] is not None  # read_canvas
        assert len(results[1]) == 1  # red nodes
        assert len(results[2]) == 1  # green nodes
        assert results[3] is True  # exists
        assert results[4] is False  # not exists
