"""
测试并行Canvas处理器 - Story 10.4

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-24
"""

import json
import os
import tempfile
from unittest.mock import Mock

import pytest
import pytest_asyncio

# 导入被测试的模块
from parallel_canvas_processor import (
    LoadBalanceStrategy,
    NodeComplexity,
    ParallelCanvasProcessor,
    ProcessingTask,
    TaskDistributionConfig,
    TaskStatus,
)

from canvas_utils import CanvasBusinessLogic, CanvasJSONOperator, CanvasOrchestrator


@pytest_asyncio.fixture
async def temp_canvas():
    """创建临时Canvas文件"""
    canvas_data = {
        "nodes": [
            {
                "id": "node-001",
                "type": "text",
                "text": "这是一个简单节点",
                "x": 100,
                "y": 100,
                "width": 400,
                "height": 300,
                "color": "1"
            },
            {
                "id": "node-002",
                "type": "text",
                "text": "这是一个包含数学公式的复杂节点：$E = mc^2$，还有代码块：\n```python\ndef hello():\n    print('Hello')\n```",
                "x": 600,
                "y": 100,
                "width": 400,
                "height": 300,
                "color": "3"
            },
            {
                "id": "node-003",
                "type": "text",
                "text": "中等复杂度的节点文本，长度适中，没有特殊内容。",
                "x": 100,
                "y": 500,
                "width": 400,
                "height": 300,
                "color": "1"
            }
        ],
        "edges": [
            {
                "id": "edge-001",
                "fromNode": "node-001",
                "toNode": "node-002",
                "fromSide": "right",
                "toSide": "left"
            }
        ]
    }

    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False) as f:
        json.dump(canvas_data, f, ensure_ascii=False, indent=2)
        temp_path = f.name

    yield temp_path

    # 清理
    os.unlink(temp_path)


@pytest.fixture
def mock_canvas_orchestrator():
    """模拟CanvasOrchestrator"""
    mock = Mock(spec=CanvasOrchestrator)
    # 模拟必要的属性
    mock.canvas_path = "test_canvas.canvas"
    mock.logic = Mock(spec=CanvasBusinessLogic)
    mock.logic.canvas_data = Mock(spec=CanvasJSONOperator)
    return mock


@pytest.fixture
def mock_instance_pool():
    """模拟GLM实例池"""
    mock = Mock()
    mock.get_available_instances.return_value = ["instance-1", "instance-2", "instance-3"]
    mock.allocate_instance.return_value = "instance-1"
    mock.release_instance.return_value = True
    return mock


@pytest.fixture
def mock_rate_limiter():
    """模拟GLM速率限制器"""
    mock = Mock()
    mock.can_process.return_value = True
    mock.record_request.return_value = None
    return mock


@pytest.fixture
def processor_config():
    """处理器配置"""
    return TaskDistributionConfig(
        enable_complexity_analysis=True,
        load_balance_strategy=LoadBalanceStrategy.ROUND_ROBIN,
        max_tasks_per_instance=5,
        task_timeout=60,
        enable_progress_monitoring=True,
        concurrent_limit=3
    )


class TestParallelCanvasProcessor:
    """测试ParallelCanvasProcessor"""

    @pytest.mark.asyncio
    async def test_initialization(self, mock_canvas_orchestrator, processor_config):
        """测试初始化"""
        processor = ParallelCanvasProcessor(
            canvas_utils=mock_canvas_orchestrator,
            config=processor_config
        )

        assert processor.canvas_utils == mock_canvas_orchestrator
        assert processor.config == processor_config
        assert len(processor.active_sessions) == 0
        assert len(processor.session_history) == 0
        assert processor.task_distributor is not None
        assert processor.result_aggregator is not None
        assert processor.progress_monitor is not None

    @pytest.mark.asyncio
    async def test_analyze_canvas_complexity(self, mock_canvas_orchestrator):
        """测试Canvas复杂度分析"""
        # 模拟Canvas数据
        mock_canvas_orchestrator.logic.canvas_data.read_canvas.return_value = {
            "nodes": [
                {
                    "id": "node-001",
                    "type": "text",
                    "text": "这是一个简单节点",
                    "x": 100,
                    "y": 100,
                    "width": 400,
                    "height": 300,
                    "color": "1"
                },
                {
                    "id": "node-002",
                    "type": "text",
                    "text": "这是一个包含数学公式的复杂节点：$E = mc^2$，还有代码块：\n```python\ndef hello():\n    print('Hello')\n```",
                    "x": 600,
                    "y": 100,
                    "width": 400,
                    "height": 300,
                    "color": "3"
                },
                {
                    "id": "node-003",
                    "type": "text",
                    "text": "中等复杂度的节点文本，长度适中，没有特殊内容。",
                    "x": 100,
                    "y": 500,
                    "width": 400,
                    "height": 300,
                    "color": "1"
                }
            ],
            "edges": [
                {
                    "id": "edge-001",
                    "fromNode": "node-001",
                    "toNode": "node-002",
                    "fromSide": "right",
                    "toSide": "left"
                }
            ]
        }

        processor = ParallelCanvasProcessor(mock_canvas_orchestrator)

        # 分析复杂度
        metrics = await processor.analyze_canvas_complexity("test_canvas.canvas")

        assert len(metrics) == 3

        # 检查第一个节点（简单）
        simple_node = next(m for m in metrics if m.node_id == "node-001")
        assert simple_node.text_length < 100
        assert simple_node.has_math_formulas == False
        assert simple_node.has_code_blocks == False
        assert simple_node.connection_count == 1
        assert simple_node.calculate_complexity() == NodeComplexity.LOW

        # 检查第二个节点（复杂）
        complex_node = next(m for m in metrics if m.node_id == "node-002")
        assert complex_node.text_length > 100
        assert complex_node.has_math_formulas == True
        assert complex_node.has_code_blocks == True
        assert complex_node.calculate_complexity() == NodeComplexity.HIGH

        # 检查第三个节点（中等）
        medium_node = next(m for m in metrics if m.node_id == "node-003")
        assert medium_node.calculate_complexity() == NodeComplexity.MEDIUM

    @pytest.mark.asyncio
    async def test_create_processing_session(self, mock_canvas_orchestrator, processor_config):
        """测试创建处理会话"""
        # 模拟Canvas数据
        mock_canvas_orchestrator.logic.canvas_data.read_canvas.return_value = {
            "nodes": [
                {"id": "node-001", "type": "text", "text": "简单节点", "color": "1"},
                {"id": "node-002", "type": "text", "text": "复杂节点", "color": "3"},
                {"id": "node-003", "type": "text", "text": "中等节点", "color": "1"}
            ]
        }

        processor = ParallelCanvasProcessor(mock_canvas_orchestrator, config=processor_config)

        # 创建会话
        session = await processor.create_processing_session(
            canvas_path="test_canvas.canvas",
            agent_type="basic-decomposition",
            target_nodes=["node-001", "node-002", "node-003"]
        )

        assert session.session_id is not None
        assert session.canvas_path == "test_canvas.canvas"
        assert session.total_nodes == 3
        assert len(session.tasks) == 3
        assert session.status == TaskStatus.PENDING

        # 检查任务
        for task in session.tasks:
            assert task.task_id is not None
            assert task.agent_type == "basic-decomposition"
            assert task.status == TaskStatus.PENDING
            assert task.estimated_time > 0

        # 检查会话是否保存
        assert session.session_id in processor.active_sessions

    @pytest.mark.asyncio
    async def test_distribute_tasks(self, temp_canvas, processor_config):
        """测试任务分发"""
        orchestrator = CanvasOrchestrator(temp_canvas)
        processor = ParallelCanvasProcessor(orchestrator, config=processor_config)

        # 创建会话
        session = await processor.create_processing_session(
            canvas_path=temp_canvas,
            agent_type="basic-decomposition",
            target_nodes=["node-001", "node-002", "node-003"]
        )

        # 分发任务
        available_instances = ["instance-1", "instance-2", "instance-3"]
        distribution = await processor.distribute_tasks(session, available_instances)

        assert len(distribution) == 3
        total_tasks = sum(len(tasks) for tasks in distribution.values())
        assert total_tasks == 3

        # 检查任务分配
        for instance_id, tasks in distribution.items():
            for task in tasks:
                assert task.assigned_instance == instance_id

    @pytest.mark.asyncio
    async def test_execute_parallel_processing(self, temp_canvas, processor_config):
        """测试并行处理执行"""
        orchestrator = CanvasOrchestrator(temp_canvas)
        processor = ParallelCanvasProcessor(orchestrator, config=processor_config)

        # 创建会话
        session = await processor.create_processing_session(
            canvas_path=temp_canvas,
            agent_type="basic-decomposition",
            target_nodes=["node-001", "node-002"]
        )

        # 执行并行处理
        processed_session = await processor.execute_parallel_processing(session)

        assert processed_session.status == TaskStatus.COMPLETED
        assert processed_session.start_time is not None
        assert processed_session.end_time is not None

        # 检查任务状态
        completed_tasks = [t for t in processed_session.tasks if t.status == TaskStatus.COMPLETED]
        assert len(completed_tasks) == 2

    @pytest.mark.asyncio
    async def test_monitor_progress(self, temp_canvas, processor_config):
        """测试进度监控"""
        orchestrator = CanvasOrchestrator(temp_canvas)
        processor = ParallelCanvasProcessor(orchestrator, config=processor_config)

        # 创建会话
        session = await processor.create_processing_session(
            canvas_path=temp_canvas,
            agent_type="basic-decomposition",
            target_nodes=["node-001", "node-002"]
        )

        # 监控进度
        progress = await processor.monitor_progress(session.session_id)

        assert progress["session_id"] == session.session_id
        assert progress["status"] == "pending"
        assert progress["total_nodes"] == 2
        assert progress["progress_percentage"] == 0.0

    @pytest.mark.asyncio
    async def test_cancel_session(self, temp_canvas, processor_config):
        """测试取消会话"""
        orchestrator = CanvasOrchestrator(temp_canvas)
        processor = ParallelCanvasProcessor(orchestrator, config=processor_config)

        # 创建会话
        session = await processor.create_processing_session(
            canvas_path=temp_canvas,
            agent_type="basic-decomposition",
            target_nodes=["node-001"]
        )

        # 取消会话
        success = await processor.cancel_session(session.session_id)
        assert success is True

        # 检查会话状态
        assert session.session_id not in processor.active_sessions
        assert session.status == TaskStatus.CANCELLED
        assert session in processor.session_history

    @pytest.mark.asyncio
    async def test_get_session_history(self, temp_canvas, processor_config):
        """测试获取会话历史"""
        orchestrator = CanvasOrchestrator(temp_canvas)
        processor = ParallelCanvasProcessor(orchestrator, config=processor_config)

        # 创建并完成一个会话
        session = await processor.create_processing_session(
            canvas_path=temp_canvas,
            agent_type="basic-decomposition",
            target_nodes=["node-001"]
        )
        await processor.execute_parallel_processing(session)
        await processor.aggregate_results(session)

        # 获取历史
        history = await processor.get_session_history(temp_canvas)
        assert len(history) == 1
        assert history[0].session_id == session.session_id

    @pytest.mark.asyncio
    async def test_aggregate_results(self, temp_canvas, processor_config):
        """测试结果聚合"""
        orchestrator = CanvasOrchestrator(temp_canvas)
        processor = ParallelCanvasProcessor(orchestrator, config=processor_config)

        # 创建并执行会话
        session = await processor.create_processing_session(
            canvas_path=temp_canvas,
            agent_type="basic-decomposition",
            target_nodes=["node-001"]
        )
        await processor.execute_parallel_processing(session)

        # 聚合结果
        update_result = await processor.aggregate_results(session)

        assert update_result.success is True
        assert update_result.session_id == session.session_id
        assert update_result.nodes_updated >= 0
        assert update_result.backup_path is not None


class TestTaskDistribution:
    """测试任务分发"""

    @pytest.mark.asyncio
    async def test_round_robin_distribution(self):
        """测试轮询分发"""
        from task_distributor import AdvancedTaskDistributor

        config = TaskDistributionConfig(load_balance_strategy=LoadBalanceStrategy.ROUND_ROBIN)
        distributor = AdvancedTaskDistributor(config)

        # 创建测试任务
        tasks = [
            ProcessingTask(
                task_id=f"task-{i}",
                node_id=f"node-{i}",
                agent_type="basic-decomposition",
                node_data={},
                complexity=NodeComplexity.MEDIUM,
                estimated_time=10.0
            )
            for i in range(5)
        ]

        # 分发任务
        instances = ["instance-1", "instance-2"]
        distribution = await distributor.distribute_tasks(tasks, instances)

        assert len(distribution) == 2
        assert len(distribution["instance-1"]) == 3
        assert len(distribution["instance-2"]) == 2

    @pytest.mark.asyncio
    async def test_complexity_based_distribution(self):
        """测试基于复杂度的分发"""
        from task_distributor import AdvancedTaskDistributor

        config = TaskDistributionConfig(load_balance_strategy=LoadBalanceStrategy.COMPLEXITY_BASED)
        distributor = AdvancedTaskDistributor(config)

        # 创建不同复杂度的任务
        tasks = [
            ProcessingTask(
                task_id="task-simple",
                node_id="node-1",
                agent_type="basic-decomposition",
                node_data={},
                complexity=NodeComplexity.LOW,
                estimated_time=5.0
            ),
            ProcessingTask(
                task_id="task-complex",
                node_id="node-2",
                agent_type="basic-decomposition",
                node_data={},
                complexity=NodeComplexity.HIGH,
                estimated_time=30.0
            )
        ]

        # 分发任务
        instances = ["instance-1", "instance-2"]
        distribution = await distributor.distribute_tasks(tasks, instances)

        # 复杂任务应该分配到负载较低的实例
        assert len(distribution["instance-1"]) + len(distribution["instance-2"]) == 2


class TestTransactionManager:
    """测试事务管理器"""

    def test_atomic_write(self):
        """测试原子性写入"""
        from transaction_manager import FileTransactionManager

        manager = FileTransactionManager()
        test_data = {"test": "data", "number": 123}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            # 原子性写入
            with manager.atomic_write(temp_path, 'w', encoding='utf-8') as f:
                json.dump(test_data, f)

            # 验证文件内容
            with open(temp_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)

            assert loaded_data == test_data

        finally:
            os.unlink(temp_path)

    def test_backup_and_restore(self):
        """测试备份和恢复"""
        from transaction_manager import FileTransactionManager

        manager = FileTransactionManager()
        original_data = {"original": "data"}
        modified_data = {"modified": "data"}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
            json.dump(original_data, f)

        try:
            # 创建备份
            backup_path = manager.create_backup(temp_path)
            assert os.path.exists(backup_path)

            # 修改文件
            with manager.atomic_write(temp_path, 'w', encoding='utf-8') as f:
                json.dump(modified_data, f)

            # 验证修改
            with open(temp_path, 'r') as f:
                data = json.load(f)
            assert data == modified_data

            # 恢复备份
            success = manager.restore_from_backup(temp_path, backup_path)
            assert success is True

            # 验证恢复
            with open(temp_path, 'r') as f:
                data = json.load(f)
            assert data == original_data

            # 清理备份
            os.unlink(backup_path)

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


@pytest.mark.asyncio
async def test_integration_workflow(temp_canvas):
    """测试完整工作流程"""
    # 创建处理器
    orchestrator = CanvasOrchestrator(temp_canvas)
    config = TaskDistributionConfig(
        load_balance_strategy=LoadBalanceStrategy.COMPLEXITY_BASED,
        concurrent_limit=2
    )
    processor = ParallelCanvasProcessor(orchestrator, config=config)

    # 1. 分析复杂度
    metrics = await processor.analyze_canvas_complexity(temp_canvas)
    assert len(metrics) == 3

    # 2. 创建处理会话
    session = await processor.create_processing_session(
        canvas_path=temp_canvas,
        agent_type="basic-decomposition",
        target_nodes=["node-001", "node-002", "node-003"]
    )
    assert session.total_nodes == 3

    # 3. 执行并行处理
    processed_session = await processor.execute_parallel_processing(session)
    assert processed_session.status == TaskStatus.COMPLETED

    # 4. 聚合结果
    update_result = await processor.aggregate_results(processed_session)
    assert update_result.success is True

    # 5. 获取性能报告
    report = await processor.monitor_progress(session.session_id)
    assert report["session_id"] == session.session_id


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
