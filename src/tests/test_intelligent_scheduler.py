"""
单元测试：智能并行调度器 - Story 10.2

测试覆盖：
- 节点分析和特征提取
- 相似度计算和聚类算法
- 任务分组和依赖分析
- 调度计划生成
- 执行引擎集成
"""

import asyncio
import json

# 导入要测试的模块
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).parent.parent))

from canvas_utils import COLOR_YELLOW, IntelligentParallelScheduler, NodeAnalysisResult, TaskGroup


class TestNodeAnalysisResult:
    """测试节点分析结果数据类"""

    def test_node_analysis_result_creation(self):
        """测试创建节点分析结果"""
        node_id = "node-123"
        content = "这是一个测试内容"
        position = (100, 200)
        recommendations = ["clarification-path", "oral-explanation"]
        quality_scores = {"accuracy": 0.8, "imagery": 0.7}

        result = NodeAnalysisResult(
            node_id=node_id,
            content=content,
            position=position,
            agent_recommendations=recommendations,
            quality_scores=quality_scores
        )

        assert result.node_id == node_id
        assert result.content == content
        assert result.position == position
        assert result.agent_recommendations == recommendations
        assert result.quality_scores == quality_scores

    def test_feature_extraction(self):
        """测试特征提取"""
        result = NodeAnalysisResult(
            node_id="node-123",
            content="测试内容长度超过100字符的测试内容用于验证hash功能正常工作" * 2,
            position=(100, 200),
            agent_recommendations=["clarification-path", "oral-explanation"],
            quality_scores={"accuracy": 0.8, "imagery": 0.7}
        )

        features = result.features
        assert features["content_length"] > 0
        assert features["position_x"] == 100
        assert features["position_y"] == 200
        assert features["primary_agent"] == "clarification-path"
        assert features["agent_count"] == 2
        assert features["avg_quality"] == 0.75


class TestTaskGroup:
    """测试任务组数据类"""

    def test_task_group_creation(self):
        """测试创建任务组"""
        group_id = "group-abc123"
        agent_type = "clarification-path"
        nodes = ["node-1", "node-2", "node-3"]

        group = TaskGroup(
            group_id=group_id,
            agent_type=agent_type,
            nodes=nodes
        )

        assert group.group_id == group_id
        assert group.agent_type == agent_type
        assert group.nodes == nodes
        assert group.dependencies == []
        assert group.priority_score == 0.0
        assert group.resource_requirements["concurrent_slots"] == 3
        assert group.resource_requirements["memory_estimate"] == 150
        assert group.resource_requirements["api_calls_estimate"] == 9


class TestIntelligentParallelScheduler:
    """测试智能并行调度器"""

    @pytest.fixture
    def scheduler(self):
        """创建调度器实例"""
        return IntelligentParallelScheduler(max_concurrent=8)

    @pytest.fixture
    def sample_canvas_data(self):
        """创建示例Canvas数据"""
        return {
            "nodes": [
                {
                    "id": "node-1",
                    "type": "text",
                    "text": "什么是逆否命题？",
                    "x": 100,
                    "y": 100,
                    "width": 400,
                    "height": 150,
                    "color": COLOR_YELLOW
                },
                {
                    "id": "node-2",
                    "type": "text",
                    "text": "理解命题逻辑的基本概念",
                    "x": 100,
                    "y": 300,
                    "width": 400,
                    "height": 150,
                    "color": COLOR_YELLOW
                },
                {
                    "id": "node-3",
                    "type": "text",
                    "text": "逆否命题的应用场景",
                    "x": 600,
                    "y": 100,
                    "width": 400,
                    "height": 150,
                    "color": COLOR_YELLOW
                },
                {
                    "id": "node-4",
                    "type": "text",
                    "text": "布尔代数基础",
                    "x": 600,
                    "y": 300,
                    "width": 400,
                    "height": 150,
                    "color": COLOR_YELLOW
                }
            ],
            "edges": []
        }

    @pytest.fixture
    def temp_canvas_file(self, sample_canvas_data):
        """创建临时Canvas文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False, encoding='utf-8') as f:
            json.dump(sample_canvas_data, f, ensure_ascii=False, indent=2)
            return f.name

    def test_scheduler_initialization(self):
        """测试调度器初始化"""
        scheduler = IntelligentParallelScheduler(max_concurrent=10)

        assert scheduler.max_concurrent == 10
        assert scheduler.task_decomposer is not None
        assert scheduler.agent_selector is not None
        assert scheduler.resource_monitor is not None
        assert scheduler.execution_engine is not None
        assert scheduler.config is not None
        assert scheduler.scheduling_history == []

    def test_load_config(self, scheduler):
        """测试配置加载"""
        config = scheduler._load_config()

        assert "analysis" in config
        assert "scheduling" in config
        assert "resources" in config
        assert "user_experience" in config

        # 检查默认值
        assert config["analysis"]["similarity_threshold"] == 0.75
        assert config["scheduling"]["default_max_concurrent"] == 12

    def test_extract_yellow_nodes(self, scheduler, sample_canvas_data):
        """测试提取黄色节点"""
        yellow_nodes = scheduler._extract_yellow_nodes(sample_canvas_data)

        assert len(yellow_nodes) == 4
        assert all(node.get("color") == COLOR_YELLOW for node in yellow_nodes)

        # 测试指定节点ID
        specific_nodes = scheduler._extract_yellow_nodes(
            sample_canvas_data,
            node_ids=["node-1", "node-3"]
        )
        assert len(specific_nodes) == 2

    @pytest.mark.asyncio
    async def test_analyze_nodes(self, scheduler):
        """测试节点分析"""
        yellow_nodes = [
            {"id": "node-1", "text": "测试内容1", "x": 100, "y": 100},
            {"id": "node-2", "text": "测试内容2", "x": 200, "y": 200}
        ]

        results = await scheduler._analyze_nodes(yellow_nodes)

        assert len(results) == 2
        assert all(isinstance(r, NodeAnalysisResult) for r in results)
        assert all(r.agent_recommendations for r in results)

    def test_calculate_content_similarity(self, scheduler):
        """测试内容相似度计算"""
        # 完全相同
        sim1 = scheduler._calculate_content_similarity("hello world", "hello world")
        assert sim1 == 1.0

        # 部分相同
        sim2 = scheduler._calculate_content_similarity("hello world", "hello there")
        assert 0 < sim2 < 1

        # 完全不同
        sim3 = scheduler._calculate_content_similarity("hello", "world")
        assert sim3 == 0.0

        # 空字符串
        sim4 = scheduler._calculate_content_similarity("", "")
        assert sim4 == 1.0

    def test_calculate_quality_similarity(self, scheduler):
        """测试质量评分相似度"""
        scores1 = {"accuracy": 0.8, "imagery": 0.7, "completeness": 0.9}
        scores2 = {"accuracy": 0.8, "imagery": 0.7, "completeness": 0.9}

        # 完全相同
        sim1 = scheduler._calculate_quality_similarity(scores1, scores2)
        assert sim1 > 0.9

        # 部分不同
        scores3 = {"accuracy": 0.6, "imagery": 0.8, "completeness": 0.7}
        sim2 = scheduler._calculate_quality_similarity(scores1, scores3)
        assert 0 < sim2 < 1

    def test_calculate_position_similarity(self, scheduler):
        """测试位置相似度计算"""
        # 相同位置
        sim1 = scheduler._calculate_position_similarity((100, 100), (100, 100))
        assert sim1 == 1.0

        # 接近位置
        sim2 = scheduler._calculate_position_similarity((100, 100), (150, 150))
        assert 0.5 < sim2 < 1.0

        # 远距离
        sim3 = scheduler._calculate_position_similarity((0, 0), (1000, 1000))
        assert sim3 < 0.1

    def test_calculate_agent_similarity(self, scheduler):
        """测试Agent推荐相似度"""
        # 完全相同
        sim1 = scheduler._calculate_agent_similarity(
            ["clarification-path", "oral-explanation"],
            ["clarification-path", "oral-explanation"]
        )
        assert sim1 == 1.0

        # 部分相同
        sim2 = scheduler._calculate_agent_similarity(
            ["clarification-path", "oral-explanation"],
            ["clarification-path", "comparison-table"]
        )
        assert 0 < sim2 < 1

        # 完全不同
        sim3 = scheduler._calculate_agent_similarity(
            ["clarification-path"],
            ["comparison-table"]
        )
        assert sim3 == 0.0

    def test_calculate_node_similarity(self, scheduler):
        """测试节点相似度计算"""
        node1 = NodeAnalysisResult(
            node_id="node-1",
            content="hello world test",
            position=(100, 100),
            agent_recommendations=["clarification-path"],
            quality_scores={"accuracy": 0.8}
        )

        node2 = NodeAnalysisResult(
            node_id="node-2",
            content="hello there test",
            position=(150, 150),
            agent_recommendations=["clarification-path"],
            quality_scores={"accuracy": 0.8}
        )

        similarity = scheduler._calculate_node_similarity(
            node1, node2, 0.4, 0.25, 0.15, 0.2
        )

        assert 0 < similarity < 1

    def test_hierarchical_clustering(self, scheduler):
        """测试层次聚类算法"""
        # 创建测试数据
        results = [
            NodeAnalysisResult("node-1", "content1", (0, 0), ["agent1"], {}),
            NodeAnalysisResult("node-2", "content2", (0, 0), ["agent1"], {}),
            NodeAnalysisResult("node-3", "content3", (1000, 1000), ["agent2"], {})
        ]

        # 创建相似度矩阵（前两个相似，第三个不同）
        similarity_matrix = [
            [0.0, 0.8, 0.1],
            [0.8, 0.0, 0.1],
            [0.1, 0.1, 0.0]
        ]

        clusters = scheduler._hierarchical_clustering(
            results, similarity_matrix, 0.5, 5, 2
        )

        assert len(clusters) >= 2
        # 前两个应该在一个簇中
        cluster1_nodes = [r.node_id for r in clusters[0]]
        assert "node-1" in cluster1_nodes and "node-2" in cluster1_nodes

    def test_cluster_nodes(self, scheduler):
        """测试节点聚类"""
        results = [
            NodeAnalysisResult(
                node_id="node-1",
                content="数学概念解释",
                position=(100, 100),
                agent_recommendations=["clarification-path", "oral-explanation"],
                quality_scores={"accuracy": 0.6}
            ),
            NodeAnalysisResult(
                node_id="node-2",
                content="数学概念详解",
                position=(150, 150),
                agent_recommendations=["clarification-path", "oral-explanation"],
                quality_scores={"accuracy": 0.5}
            ),
            NodeAnalysisResult(
                node_id="node-3",
                content="物理公式推导",
                position=(500, 500),
                agent_recommendations=["comparison-table"],
                quality_scores={"accuracy": 0.7}
            )
        ]

        task_groups = scheduler._cluster_nodes(results)

        assert len(task_groups) >= 1
        assert all(isinstance(g, TaskGroup) for g in task_groups)
        # 节点应该被成功分组（可能在同一组或不同组）
        total_nodes = sum(len(g.nodes) for g in task_groups)
        assert total_nodes == 3

    def test_analyze_dependencies(self, scheduler, sample_canvas_data):
        """测试依赖关系分析"""
        # 创建测试任务组
        groups = [
            TaskGroup("group-1", "clarification-path", ["node-1", "node-2"]),
            TaskGroup("group-2", "oral-explanation", ["node-3"]),
            TaskGroup("group-3", "comparison-table", ["node-4"])
        ]

        groups_with_deps = scheduler._analyze_dependencies(groups, sample_canvas_data)

        assert len(groups_with_deps) == 3
        # 可能会有依赖关系（基于位置）
        for group in groups_with_deps:
            assert isinstance(group.dependencies, list)

    def test_optimize_execution_order(self, scheduler):
        """测试执行顺序优化"""
        # 创建有依赖关系的任务组
        group1 = TaskGroup("group-1", "agent1", ["node-1"])
        group2 = TaskGroup("group-2", "agent2", ["node-2"])
        group3 = TaskGroup("group-3", "agent3", ["node-3"])

        # 设置依赖：group2 依赖 group1
        group2.dependencies = ["group-1"]
        # 设置依赖：group3 依赖 group2
        group3.dependencies = ["group-2"]

        # 设置优先级
        group1.priority_score = 0.5
        group2.priority_score = 0.8
        group3.priority_score = 0.3

        groups = [group3, group1, group2]  # 乱序输入
        optimized = scheduler._optimize_execution_order(groups)

        # 验证顺序：group1 应该在 group2 前面，group2 在 group3 前面
        assert optimized[0].group_id == "group-1"
        assert optimized[1].group_id == "group-2"
        assert optimized[2].group_id == "group-3"

    def test_create_scheduling_plan(self, scheduler):
        """测试创建调度计划"""
        analysis_results = [
            NodeAnalysisResult("node-1", "content1", (0, 0), ["agent1"], {}),
            NodeAnalysisResult("node-2", "content2", (0, 0), ["agent1"], {})
        ]

        task_groups = [
            TaskGroup("group-1", "agent1", ["node-1", "node-2"])
        ]

        plan = scheduler._create_scheduling_plan(
            "test.canvas", analysis_results, task_groups
        )

        assert "plan_id" in plan
        assert plan["canvas_path"] == "test.canvas"
        assert "analysis_timestamp" in plan
        assert plan["node_analysis"]["total_nodes"] == 2
        assert len(plan["task_groups"]) == 1
        assert plan["task_groups"][0]["agent_type"] == "agent1"
        assert "execution_strategy" in plan

    def test_preview_execution_plan(self, scheduler):
        """测试执行计划预览"""
        plan = {
            "plan_id": "schedule-123",
            "canvas_path": "/path/to/test.canvas",
            "analysis_timestamp": "2025-01-27T10:00:00",
            "node_analysis": {
                "total_nodes": 5,
                "grouped_nodes": 5,
                "skipped_nodes": 0
            },
            "task_groups": [
                {
                    "group_id": "group-1",
                    "agent_type": "clarification-path",
                    "nodes": ["node-1", "node-2"],
                    "estimated_duration": "45-60秒",
                    "priority_score": 0.85,
                    "dependencies": [],
                    "resource_requirements": {
                        "concurrent_slots": 2
                    }
                }
            ],
            "execution_strategy": {
                "max_concurrent_groups": 2,
                "total_estimated_duration": "90-120秒",
                "optimization_strategy": "dependency_aware"
            },
            "user_confirmation_required": True
        }

        preview = scheduler.preview_execution_plan(plan)

        assert "智能并行调度执行计划预览" in preview
        assert "schedule-123" in preview
        assert "5" in preview  # 总节点数
        assert "clarification-path" in preview
        assert "45-60秒" in preview
        assert "确认执行?" in preview

    @pytest.mark.asyncio
    async def test_analyze_and_schedule_nodes(self, scheduler, temp_canvas_file):
        """测试完整的分析和调度流程"""
        result = await scheduler.analyze_and_schedule_nodes(
            canvas_path=temp_canvas_file,
            node_ids=None,  # 分析所有黄色节点
            auto_execute=False
        )

        assert result["success"] is True
        assert "scheduling_plan" in result
        assert result["scheduling_plan"] is not None
        assert result["analysis_time"] > 0
        assert result["scheduling_plan"]["node_analysis"]["total_nodes"] > 0

    @pytest.mark.asyncio
    async def test_analyze_and_schedule_nodes_no_yellow(self, scheduler, temp_canvas_file):
        """测试没有黄色节点的情况"""
        # 修改Canvas文件，移除黄色节点
        with open(temp_canvas_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for node in data["nodes"]:
            node["color"] = "2"  # 改为绿色

        with open(temp_canvas_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)

        result = await scheduler.analyze_and_schedule_nodes(temp_canvas_file)

        assert result["success"] is False
        assert "未找到需要处理的黄色节点" in result["error"]
        assert result["scheduling_plan"] is None

    def test_update_metrics(self, scheduler):
        """测试性能指标更新"""
        analysis_results = [
            NodeAnalysisResult("node-1", "content1", (0, 0), ["agent1"], {})
        ]
        task_groups = [
            TaskGroup("group-1", "agent1", ["node-1"])
        ]

        initial_metrics = scheduler.performance_metrics.copy()

        scheduler._update_metrics(analysis_results, task_groups, 1.5)

        assert scheduler.performance_metrics["total_nodes_processed"] > initial_metrics["total_nodes_processed"]
        assert scheduler.performance_metrics["total_groups_created"] > initial_metrics["total_groups_created"]

    def test_get_performance_metrics(self, scheduler):
        """测试获取性能指标"""
        metrics = scheduler.get_performance_metrics()

        assert "scheduling_metrics" in metrics
        assert "recent_plans" in metrics
        assert isinstance(metrics["scheduling_metrics"], dict)
        assert isinstance(metrics["recent_plans"], list)

    @pytest.mark.asyncio
    async def test_execute_scheduling_plan_no_confirmation(self, scheduler):
        """测试需要确认但未确认的执行"""
        plan = {
            "plan_id": "test-plan",
            "canvas_path": "test.canvas",
            "user_confirmation_required": True,
            "task_groups": []
        }

        result = await scheduler.execute_scheduling_plan(plan, user_confirmed=False)

        assert result["success"] is False
        assert "需要用户确认才能执行计划" in result["error"]
        assert result["execution_id"] is None

    def test_estimate_total_duration(self, scheduler):
        """测试执行时间估算"""
        groups = [
            TaskGroup("group-1", "clarification-path", ["node-1", "node-2"]),
            TaskGroup("group-2", "scoring-agent", ["node-3"])
        ]

        duration = scheduler._estimate_total_duration(groups)

        assert duration > 0
        assert groups[0].estimated_duration > 0
        assert groups[1].estimated_duration > 0


class TestLargeScalePerformance:
    """大规模性能测试"""

    @pytest.mark.asyncio
    async def test_large_number_of_nodes(self):
        """测试大量节点的处理性能"""
        # 创建100个节点的测试数据
        nodes = []
        for i in range(100):
            nodes.append({
                "id": f"node-{i}",
                "type": "text",
                "text": f"测试节点内容 {i}",
                "x": (i % 10) * 450,
                "y": (i // 10) * 200,
                "width": 400,
                "height": 150,
                "color": COLOR_YELLOW
            })

        canvas_data = {"nodes": nodes, "edges": []}

        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False, encoding='utf-8') as f:
            json.dump(canvas_data, f, ensure_ascii=False)
            temp_file = f.name

        try:
            scheduler = IntelligentParallelScheduler(max_concurrent=12)

            # 测试分析性能
            start_time = asyncio.get_event_loop().time()
            result = await scheduler.analyze_and_schedule_nodes(temp_file)
            end_time = asyncio.get_event_loop().time()

            analysis_time = end_time - start_time

            # 验证结果
            assert result["success"] is True
            assert result["analysis_time"] < 5.0  # 应该在5秒内完成
            assert analysis_time < 5.0
            assert result["scheduling_plan"]["node_analysis"]["total_nodes"] == 100

            # 验证分组效果
            task_groups = result["scheduling_plan"]["task_groups"]
            assert len(task_groups) > 0
            # 对于100个相似度低的节点，分组效果可能不明显，但至少应该成功处理
            assert len(task_groups) <= 100

        finally:
            # 清理临时文件
            import os
            os.unlink(temp_file)


class TestErrorHandling:
    """错误处理测试"""

    @pytest.mark.asyncio
    async def test_invalid_canvas_path(self):
        """测试无效的Canvas路径"""
        scheduler = IntelligentParallelScheduler()

        result = await scheduler.analyze_and_schedule_nodes("/nonexistent/path.canvas")

        assert result["success"] is False
        assert "error" in result

    def test_invalid_config(self):
        """测试无效配置的处理"""
        # 创建无效的配置文件
        invalid_config = "invalid: yaml: content: ["

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_config)
            config_path = f.name

        # 临时修改配置路径
        scheduler = IntelligentParallelScheduler()
        original_load = scheduler._load_config

        def mock_load_config():
            try:
                with open(config_path, 'r') as f:
                    import yaml
                    return yaml.safe_load(f)
            except:
                return scheduler._get_default_config()

        scheduler._load_config = mock_load_config

        try:
            config = scheduler._load_config()
            # 应该返回默认配置
            assert "analysis" in config
        finally:
            scheduler._load_config = original_load
            import os
            os.unlink(config_path)


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
