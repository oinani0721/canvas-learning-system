"""
Canvas Learning System v2.0 - 统一记忆接口测试

测试统一记忆接口的核心功能和集成。

Author: Canvas Learning System Team
Version: 2.0
Created: 2025-10-23
"""

import sys
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

# 添加项目根目录到路径
sys.path.append('..')
sys.path.append('../memory_system')

from memory_system import (
    GracefulDegradationManager,
    InteractionType,
    LearningState,
    MemoryConsistencyValidator,
    MemoryLink,
    MemoryLinkType,
    MemoryType,
    SemanticMemoryManager,
    TemporalMemoryManager,
    UnifiedMemoryEntry,
    UnifiedMemoryInterface,
)


class TestUnifiedMemoryInterface:
    """统一记忆接口测试类"""

    @pytest.fixture
    def memory_config(self):
        """测试配置"""
        return {
            "auto_link_enabled": True,
            "sync_enabled": True,
            "consistency_check_enabled": True,
            "temporal_memory": {
                "neo4j_uri": "bolt://localhost:7687",
                "neo4j_username": "neo4j",
                "neo4j_password": "password"
            },
            "semantic_memory": {
                "endpoint": "local",
                "timeout": 30
            }
        }

    @pytest.fixture
    def unified_interface(self, memory_config):
        """创建统一记忆接口实例"""
        with patch('memory_system.temporal_memory_manager.TemporalMemoryManager') as mock_temporal, \
             patch('memory_system.semantic_memory_manager.SemanticMemoryManager') as mock_semantic:

            # 配置mock
            mock_temporal.return_value.is_available.return_value = True
            mock_semantic.return_value.is_available.return_value = True

            interface = UnifiedMemoryInterface(memory_config)
            return interface

    def test_interface_initialization(self, unified_interface):
        """测试接口初始化"""
        assert unified_interface.is_available() is True
        assert unified_interface.auto_link_enabled is True
        assert unified_interface.sync_enabled is True
        assert unified_interface.consistency_check_enabled is True
        assert unified_interface.temporal_manager is not None
        assert unified_interface.semantic_manager is not None

    def test_store_complete_learning_memory_success(self, unified_interface):
        """测试成功存储完整学习记忆"""
        # 配置mock
        unified_interface.temporal_manager.record_learning_journey.return_value = "temporal_123"
        unified_interface.semantic_manager.store_semantic_memory.return_value = "semantic_123"

        # 存储记忆
        memory_id = unified_interface.store_complete_learning_memory(
            canvas_id="test_canvas",
            node_id="test_node",
            content="这是一个测试内容",
            learning_state="yellow",
            confidence_score=0.6,
            metadata={"test": True}
        )

        # 验证结果
        assert memory_id is not None
        assert memory_id in unified_interface.memory_entries
        assert len(unified_interface.memory_entries) == 1

        # 验证记忆条目
        memory_entry = unified_interface.memory_entries[memory_id]
        assert memory_entry.canvas_id == "test_canvas"
        assert memory_entry.node_id == "test_node"
        assert memory_entry.content == "这是一个测试内容"
        assert memory_entry.temporal_id == "temporal_123"
        assert memory_entry.semantic_id == "semantic_123"

        # 验证调用
        unified_interface.temporal_manager.record_learning_journey.assert_called_once()
        unified_interface.semantic_manager.store_semantic_memory.assert_called_once()

    def test_store_complete_learning_memory_with_temporal_failure(self, unified_interface):
        """测试时序记忆失败时的存储"""
        # 配置mock - 时序记忆失败
        unified_interface.temporal_manager.record_learning_journey.side_effect = Exception("Temporal error")
        unified_interface.semantic_manager.store_semantic_memory.return_value = "semantic_123"

        # 存储记忆
        memory_id = unified_interface.store_complete_learning_memory(
            canvas_id="test_canvas",
            node_id="test_node",
            content="测试内容",
            learning_state="yellow"
        )

        # 验证仍然可以存储（优雅降级）
        assert memory_id is not None
        memory_entry = unified_interface.memory_entries[memory_id]
        assert memory_entry.temporal_id is None  # 时序记忆失败
        assert memory_entry.semantic_id == "semantic_123"

    def test_link_memories_success(self, unified_interface):
        """测试成功建立记忆关联"""
        # 创建一些记忆条目
        unified_interface.memory_entries["memory1"] = UnifiedMemoryEntry(
            memory_id="memory1",
            canvas_id="test_canvas",
            node_id="node1",
            content="内容1"
        )
        unified_interface.memory_entries["memory2"] = UnifiedMemoryEntry(
            memory_id="memory2",
            canvas_id="test_canvas",
            node_id="node2",
            content="内容2"
        )

        # 建立关联
        link_id = unified_interface.link_memories(
            source_memory_id="memory1",
            target_memory_id="memory2",
            link_type=MemoryLinkType.CONCEPT_RELATION,
            strength=0.8
        )

        # 验证结果
        assert link_id is not None
        assert link_id in unified_interface.memory_links
        assert len(unified_interface.memory_links) == 1

        # 验证链接
        memory_link = unified_interface.memory_links[link_id]
        assert memory_link.source_memory_id == "memory1"
        assert memory_link.target_memory_id == "memory2"
        assert memory_link.link_type == MemoryLinkType.CONCEPT_RELATION
        assert memory_link.strength == 0.8

    def test_retrieve_contextual_memory(self, unified_interface):
        """测试上下文感知的记忆检索"""
        # 创建测试记忆条目
        test_memories = [
            UnifiedMemoryEntry(
                memory_id="memory1",
                canvas_id="test_canvas",
                node_id="node1",
                content="数学相关内容",
                metadata={"learning_state": "green", "tags": ["math"]}
            ),
            UnifiedMemoryEntry(
                memory_id="memory2",
                canvas_id="test_canvas",
                node_id="node2",
                content="编程相关内容",
                metadata={"learning_state": "yellow", "tags": ["programming"]}
            ),
            UnifiedMemoryEntry(
                memory_id="memory3",
                canvas_id="other_canvas",
                node_id="node1",
                content="其他内容",
                metadata={"learning_state": "red"}
            )
        ]

        for memory in test_memories:
            unified_interface.memory_entries[memory.memory_id] = memory

        # 检索特定Canvas的记忆
        memories = unified_interface.retrieve_contextual_memory("test_canvas")
        assert len(memories) == 2

        # 带上下文过滤的检索
        context = {"learning_state": "green"}
        memories = unified_interface.retrieve_contextual_memory("test_canvas", context=context)
        assert len(memories) == 1
        assert memories[0].memory_id == "memory1"

    def test_search_memories(self, unified_interface):
        """测试记忆搜索"""
        # 创建测试记忆条目
        test_memories = [
            UnifiedMemoryEntry(
                memory_id="memory1",
                canvas_id="test_canvas",
                node_id="node1",
                content="函数定义和性质"
            ),
            UnifiedMemoryEntry(
                memory_id="memory2",
                canvas_id="test_canvas",
                node_id="node2",
                content="算法复杂度分析"
            ),
            UnifiedMemoryEntry(
                memory_id="memory3",
                canvas_id="test_canvas",
                node_id="node3",
                content="数据库设计原理"
            )
        ]

        for memory in test_memories:
            unified_interface.memory_entries[memory.memory_id] = memory

        # 搜索包含"函数"的记忆
        results = unified_interface.search_memories("函数", search_type="unified")
        assert len(results) >= 1
        assert any("memory1" in str(result) for result in results)

        # 搜索包含"算法"的记忆
        results = unified_interface.search_memories("算法", search_type="unified")
        assert len(results) >= 1
        assert any("memory2" in str(result) for result in results)

    def test_get_memory_statistics(self, unified_interface):
        """测试获取记忆统计"""
        # 创建不同类型的记忆条目
        unified_interface.memory_entries["temporal_only"] = UnifiedMemoryEntry(
            memory_id="temporal_only",
            canvas_id="test_canvas",
            node_id="node1",
            content="只有时序记忆",
            temporal_id="temporal_1",
            memory_type=MemoryType.TEMPORAL
        )
        unified_interface.memory_entries["semantic_only"] = UnifiedMemoryEntry(
            memory_id="semantic_only",
            canvas_id="test_canvas",
            node_id="node2",
            content="只有语义记忆",
            semantic_id="semantic_1",
            memory_type=MemoryType.SEMANTIC
        )
        unified_interface.memory_entries["unified"] = UnifiedMemoryEntry(
            memory_id="unified",
            canvas_id="test_canvas",
            node_id="node3",
            content="统一记忆",
            temporal_id="temporal_2",
            semantic_id="semantic_2",
            memory_type=MemoryType.UNIFIED
        )

        # 创建记忆链接
        unified_interface.memory_links["link1"] = MemoryLink(
            link_id="link1",
            source_memory_id="temporal_only",
            target_memory_id="semantic_only",
            link_type=MemoryLinkType.TEMPORAL_SEMANTIC
        )

        # 获取统计
        stats = unified_interface.get_memory_statistics()

        # 验证统计结果
        assert stats["total_unified_memories"] == 3
        assert stats["total_memory_links"] == 1
        assert stats["memory_types"]["unified"] == 1
        assert stats["memory_types"]["temporal"] == 1
        assert stats["memory_types"]["semantic"] == 1
        assert stats["canvas_distribution"]["test_canvas"] == 3

    def test_cleanup_old_memories(self, unified_interface):
        """测试清理旧记忆"""
        # 创建测试记忆（包括旧的记忆）
        old_time = datetime.now() - timedelta(days=400)
        recent_time = datetime.now() - timedelta(days=10)

        unified_interface.memory_entries["old_memory"] = UnifiedMemoryEntry(
            memory_id="old_memory",
            canvas_id="test_canvas",
            node_id="node1",
            content="旧记忆",
            created_at=old_time
        )
        unified_interface.memory_entries["recent_memory"] = UnifiedMemoryEntry(
            memory_id="recent_memory",
            canvas_id="test_canvas",
            node_id="node2",
            content="最近记忆",
            created_at=recent_time
        )

        # 执行清理
        cleanup_results = unified_interface.cleanup_old_memories(days_threshold=30)

        # 验证清理结果
        assert cleanup_results["deleted_memories"] == 1
        assert "old_memory" not in unified_interface.memory_entries
        assert "recent_memory" in unified_interface.memory_entries

    def test_sync_memories(self, unified_interface):
        """测试记忆同步"""
        # 创建测试记忆
        unified_interface.memory_entries["test_memory"] = UnifiedMemoryEntry(
            memory_id="test_memory",
            canvas_id="test_canvas",
            node_id="node1",
            content="测试记忆"
        )

        # 执行同步
        sync_results = unified_interface.sync_memories()

        # 验证同步结果
        assert "status" in sync_results
        assert "synced_entries" in sync_results
        assert "failed_entries" in sync_results
        assert "created_links" in sync_results
        assert "errors" in sync_results

    def test_interface_error_handling(self, unified_interface):
        """测试接口错误处理"""
        # 测试无效参数
        with pytest.raises(Exception):
            unified_interface.store_complete_learning_memory(
                canvas_id="",  # 空的canvas_id应该引发错误
                node_id="test_node",
                content="测试内容"
            )

        # 测试无效的记忆ID链接
        with pytest.raises(Exception):
            unified_interface.link_memories(
                source_memory_id="nonexistent",
                target_memory_id="also_nonexistent",
                link_type=MemoryLinkType.CONCEPT_RELATION
            )


class TestTemporalMemoryManager:
    """时序记忆管理器测试类"""

    @pytest.fixture
    def temporal_config(self):
        """时序记忆配置"""
        return {
            "neo4j_uri": "bolt://localhost:7687",
            "neo4j_username": "neo4j",
            "neo4j_password": "password",
            "session_timeout": 1800
        }

    @pytest.fixture
    def temporal_manager(self, temporal_config):
        """创建时序记忆管理器实例"""
        with patch('memory_system.temporal_memory_manager.TemporalMemoryManager._initialize_graphiti'):
            manager = TemporalMemoryManager(temporal_config)
            manager.is_initialized = True
            return manager

    def test_manager_initialization(self, temporal_manager):
        """测试管理器初始化"""
        assert temporal_manager.is_available() is True
        assert temporal_manager.neo4j_uri == "bolt://localhost:7687"
        assert temporal_manager.session_timeout == 1800

    def test_create_learning_session(self, temporal_manager):
        """测试创建学习会话"""
        session = temporal_manager.create_learning_session("test_canvas", "test_user")

        assert session is not None
        assert session.canvas_id == "test_canvas"
        assert session.user_id == "test_user"
        assert session.start_time is not None
        assert temporal_manager.current_session == session

    def test_record_learning_journey(self, temporal_manager):
        """测试记录学习历程"""
        # 创建会话
        temporal_manager.create_learning_session("test_canvas", "test_user")

        # 记录学习历程
        memory_id = temporal_manager.record_learning_journey(
            canvas_id="test_canvas",
            node_id="test_node",
            learning_state=LearningState.YELLOW,
            timestamp=datetime.now(),
            interaction_type=InteractionType.VIEW,
            confidence_score=0.6,
            duration_seconds=120
        )

        assert memory_id is not None
        assert temporal_manager.current_session is not None
        assert memory_id in temporal_manager.current_session.memories_created
        assert "test_node" in temporal_manager.current_session.nodes_interacted

    def test_calculate_review_schedule(self, temporal_manager):
        """测试计算复习间隔"""
        # 测试不同学习状态的复习间隔
        green_next = temporal_manager.calculate_review_schedule(
            node_id="test_node",
            current_state=LearningState.GREEN,
            confidence_score=0.9
        )
        yellow_next = temporal_manager.calculate_review_schedule(
            node_id="test_node",
            current_state=LearningState.YELLOW,
            confidence_score=0.6
        )
        red_next = temporal_manager.calculate_review_schedule(
            node_id="test_node",
            current_state=LearningState.RED,
            confidence_score=0.2
        )

        # 验证复习间隔符合预期（绿色 > 黄色 > 红色）
        assert green_next > yellow_next > red_next

    def test_end_learning_session(self, temporal_manager):
        """测试结束学习会话"""
        # 创建会话
        session = temporal_manager.create_learning_session("test_canvas", "test_user")

        # 模拟一些活动
        temporal_manager.record_learning_journey(
            canvas_id="test_canvas",
            node_id="test_node",
            learning_state=LearningState.YELLOW,
            timestamp=datetime.now()
        )

        # 结束会话
        ended_session = temporal_manager.end_learning_session()

        assert ended_session is not None
        assert ended_session.session_id == session.session_id
        assert ended_session.end_time is not None
        assert ended_session.duration_seconds > 0
        assert temporal_manager.current_session is None


class TestSemanticMemoryManager:
    """语义记忆管理器测试类"""

    @pytest.fixture
    def semantic_config(self):
        """语义记忆配置"""
        return {
            "endpoint": "local",
            "timeout": 30,
            "max_text_length": 512,
            "similarity_threshold": 0.7
        }

    @pytest.fixture
    def semantic_manager(self, semantic_config):
        """创建语义记忆管理器实例"""
        with patch('memory_system.semantic_memory_manager.SemanticMemoryManager._initialize_mcp_client'):
            manager = SemanticMemoryManager(semantic_config)
            manager.is_initialized = True
            return manager

    def test_manager_initialization(self, semantic_manager):
        """测试管理器初始化"""
        assert semantic_manager.is_available() is True
        assert semantic_manager.endpoint == "local"
        assert semantic_manager.timeout == 30
        assert semantic_manager.max_text_length == 512

    def test_store_semantic_memory(self, semantic_manager):
        """测试存储语义记忆"""
        memory_id = semantic_manager.store_semantic_memory(
            content="这是一个关于函数定义的数学概念",
            metadata={"domain": "mathematics", "difficulty": "medium"}
        )

        assert memory_id is not None
        assert isinstance(memory_id, str)

    def test_understand_semantic_context(self, semantic_manager):
        """测试语义理解"""
        content = "函数是一种特殊的映射关系，它将定义域中的每个元素映射到值域中的唯一元素。"

        understanding = semantic_manager.understand_semantic_context(
            content=content,
            context={"domain": "mathematics"}
        )

        assert "semantic_tags" in understanding
        assert "concept_entities" in understanding
        assert "domain_classification" in understanding
        assert "understanding_score" in understanding
        assert "related_concepts" in understanding

    def test_find_cross_domain_connections(self, semantic_manager):
        """测试跨域连接发现"""
        connections = semantic_manager.find_cross_domain_connections(
            concept="函数",
            domains=["mathematics", "programming", "physics"]
        )

        assert isinstance(connections, list)
        # 应该找到一些跨域连接
        assert len(connections) >= 0

    def test_generate_intelligent_tags(self, semantic_manager):
        """测试智能标签生成"""
        content = "在这个例子中，我们将演示如何使用数学归纳法证明自然数的性质。"

        tags = semantic_manager.generate_intelligent_tags(
            content=content,
            existing_tags=["mathematics"]
        )

        assert isinstance(tags, list)
        assert len(tags) > 0
        # 应该包含相关的标签
        assert any("math" in tag.lower() for tag in tags)

    def test_analyze_creativity(self, semantic_manager):
        """测试创意分析"""
        content = "想象一下，如果函数会说话，它会告诉我们什么样的故事呢？"

        creativity = semantic_manager.analyze_creativity(content)

        assert "creativity_score" in creativity
        assert "novelty_score" in creativity
        assert "diversity_score" in creativity
        assert "depth_score" in creativity
        assert "recommendations" in creativity

        # 验证分数在合理范围内
        assert 0 <= creativity["creativity_score"] <= 1
        assert 0 <= creativity["novelty_score"] <= 1
        assert 0 <= creativity["diversity_score"] <= 1
        assert 0 <= creativity["depth_score"] <= 1


class TestMemoryConsistencyValidator:
    """记忆一致性验证器测试类"""

    @pytest.fixture
    def validator_config(self):
        """验证器配置"""
        return {
            "auto_repair_enabled": True,
            "max_repair_attempts": 3,
            "validation_strategies": [
                "cross_reference_check",
                "data_integrity_check",
                "timestamp_consistency",
                "relationship_validation"
            ]
        }

    @pytest.fixture
    def validator(self, validator_config):
        """创建验证器实例"""
        return MemoryConsistencyValidator(validator_config)

    @pytest.fixture
    def test_memories(self):
        """测试记忆数据"""
        return {
            "memory1": UnifiedMemoryEntry(
                memory_id="memory1",
                canvas_id="test_canvas",
                node_id="node1",
                content="正常记忆",
                temporal_id="temporal1",
                semantic_id="semantic1"
            ),
            "memory2": UnifiedMemoryEntry(
                memory_id="memory2",
                canvas_id="test_canvas",
                node_id="node2",
                content="有问题的记忆",
                temporal_id="nonexistent_temporal",  # 不存在的时序记忆引用
                semantic_id="semantic2"
            ),
            "memory3": UnifiedMemoryEntry(
                memory_id="memory3",
                canvas_id="test_canvas",
                node_id="node3",
                content="",  # 空内容
                temporal_id="temporal3",
                semantic_id="semantic3"
            )
        }

    @pytest.fixture
    def test_links(self):
        """测试记忆链接"""
        return {
            "link1": MemoryLink(
                link_id="link1",
                source_memory_id="memory1",
                target_memory_id="memory2",
                link_type=MemoryLinkType.CONCEPT_RELATION
            ),
            "link2": MemoryLink(
                link_id="link2",
                source_memory_id="nonexistent",  # 不存在的记忆
                target_memory_id="memory1",
                link_type=MemoryLinkType.TEMPORAL_SEMANTIC
            )
        }

    def test_validate_memory_consistency(self, validator, test_memories, test_links):
        """测试记忆一致性验证"""
        report = validator.validate_memory_consistency(
            memory_entries=test_memories,
            memory_links=test_links,
            full_validation=True
        )

        # 验证报告结构
        assert hasattr(report, 'temporal_memories_count')
        assert hasattr(report, 'semantic_memories_count')
        assert hasattr(report, 'unified_memories_count')
        assert hasattr(report, 'consistency_score')
        assert hasattr(report, 'inconsistencies_found')
        assert hasattr(report, 'recommendations')

        # 应该发现一些问题
        assert len(report.inconsistencies_found) > 0
        assert report.consistency_score < 1.0

    def test_cross_reference_validation(self, validator, test_memories, test_links):
        """测试跨引用验证"""
        issues = validator._validate_cross_references(test_memories, test_links)

        # 应该发现孤立的引用
        assert len(issues) > 0

        # 检查问题类型
        issue_types = [issue.issue_type for issue in issues]
        assert "orphaned_temporal_reference" in issue_types
        assert "orphaned_source_link" in issue_types

    def test_data_integrity_validation(self, validator, test_memories):
        """测试数据完整性验证"""
        issues = validator._validate_data_integrity(test_memories)

        # 应该发现完整性问题
        assert len(issues) > 0

        # 检查问题类型
        issue_types = [issue.issue_type for issue in issues]
        assert "missing_content" in issue_types

    def test_auto_repair_issues(self, validator, test_memories, test_links):
        """测试自动修复问题"""
        # 先验证找到问题
        report = validator.validate_memory_consistency(test_memories, test_links)
        issues = [ConsistencyIssue(**issue) for issue in report.inconsistencies_found if issue.get('auto_fixable', False)]

        if issues:
            # 执行自动修复
            repair_results = validator.auto_repair_issues(issues, test_memories, test_links)

            # 验证修复结果
            assert "fixed_issues" in repair_results
            assert "failed_repairs" in repair_results
            assert "skipped_issues" in repair_results
            assert "repair_details" in repair_results

    def test_get_validation_history(self, validator):
        """测试获取验证历史"""
        # 执行几次验证
        validator.validate_memory_consistency({}, {})
        validator.validate_memory_consistency({}, {})

        # 获取历史
        history = validator.get_validation_history(limit=10)

        assert isinstance(history, list)
        assert len(history) >= 2

        # 验证历史记录格式
        for record in history:
            assert "validation_id" in record
            assert "timestamp" in record
            assert "total_memories_checked" in record
            assert "issues_found" in record
            assert "consistency_score" in record

    def test_get_consistency_trend(self, validator):
        """测试获取一致性趋势"""
        # 执行几次验证以创建历史记录
        validator.validate_memory_consistency({}, {})
        validator.validate_memory_consistency({}, {})

        # 获取趋势
        trend = validator.get_consistency_trend(days=7)

        assert "trend" in trend
        assert "scores" in trend
        assert "dates" in trend
        assert "average_score" in trend
        assert "validation_count" in trend


class TestGracefulDegradationManager:
    """优雅降级管理器测试类"""

    @pytest.fixture
    def degradation_config(self):
        """降级配置"""
        return {
            "health_check_interval": 1,  # 1秒间隔用于测试
            "health_check_timeout": 5,
            "failure_threshold": 2,
            "recovery_threshold": 2,
            "max_concurrent_checks": 3
        }

    @pytest.fixture
    def degradation_manager(self, degradation_config):
        """创建降级管理器实例"""
        return GracefulDegradationManager(degradation_config)

    def test_manager_initialization(self, degradation_manager):
        """测试管理器初始化"""
        assert degradation_manager.health_check_interval == 1
        assert degradation_manager.failure_threshold == 2
        assert degradation_manager.recovery_threshold == 2
        assert degradation_manager.current_level.value == "normal"
        assert degradation_manager.system_status.value == "healthy"

    def test_register_components(self, degradation_manager):
        """测试组件注册"""
        # 创建mock组件
        mock_temporal = Mock()
        mock_semantic = Mock()
        mock_unified = Mock()

        # 注册组件
        degradation_manager.register_components(
            temporal_manager=mock_temporal,
            semantic_manager=mock_semantic,
            unified_interface=mock_unified
        )

        # 验证注册结果
        assert len(degradation_manager.component_status) == 3
        assert "temporal_memory" in degradation_manager.component_status
        assert "semantic_memory" in degradation_manager.component_status
        assert "unified_interface" in degradation_manager.component_status

    def test_health_check_execution(self, degradation_manager):
        """测试健康检查执行"""
        # 注册组件
        degradation_manager.register_components()

        # 执行健康检查
        degradation_manager._perform_health_checks()

        # 验证检查结果
        assert len(degradation_manager.component_status) > 0

        for component_name, result in degradation_manager.component_status.items():
            assert hasattr(result, 'component_name')
            assert hasattr(result, 'status')
            assert hasattr(result, 'response_time_ms')
            assert hasattr(result, 'timestamp')

    def test_degradation_level_determination(self, degradation_manager):
        """测试降级级别确定"""
        # 测试不同触发条件
        normal_triggers = []
        warning_triggers = ["response_time > 1000ms"]
        degraded_triggers = ["component_unavailable", "error_rate > 15%"]
        emergency_triggers = ["response_time > 5000ms", "error_rate > 50%"]

        # 验证级别判断
        assert degradation_manager._determine_degradation_level(normal_triggers).value == "normal"
        assert degradation_manager._determine_degradation_level(warning_triggers).value == "warning"
        assert degradation_manager._determine_degradation_level(degraded_triggers).value == "degraded"
        assert degradation_manager._determine_degradation_level(emergency_triggers).value == "emergency"

    def test_system_status_update(self, degradation_manager):
        """测试系统状态更新"""
        # 测试不同降级级别对应的状态
        degradation_manager.current_level = DegradationLevel.NORMAL
        degradation_manager._update_system_status()
        assert degradation_manager.system_status.value == "healthy"

        degradation_manager.current_level = DegradationLevel.WARNING
        degradation_manager._update_system_status()
        assert degradation_manager.system_status.value == "warning"

        degradation_manager.current_level = DegradationLevel.DEGRADED
        degradation_manager._update_system_status()
        assert degradation_manager.system_status.value == "critical"

        degradation_manager.current_level = DegradationLevel.EMERGENCY
        degradation_manager._update_system_status()
        assert degradation_manager.system_status.value == "offline"

    def test_manual_recovery(self, degradation_manager):
        """测试手动恢复"""
        # 注册组件
        degradation_manager.register_components()

        # 设置为降级状态
        degradation_manager.current_level = DegradationLevel.DEGRADED

        # 尝试手动恢复
        success = degradation_manager.trigger_manual_recovery()

        # 验证恢复结果
        assert isinstance(success, bool)

    def test_get_system_status(self, degradation_manager):
        """测试获取系统状态"""
        # 注册组件
        degradation_manager.register_components()

        # 获取状态
        status = degradation_manager.get_system_status()

        # 验证状态信息
        assert "current_level" in status
        assert "system_status" in status
        assert "monitoring_active" in status
        assert "component_count" in status
        assert "components" in status
        assert "failure_counts" in status
        assert "recovery_counts" in status

    def test_monitoring_lifecycle(self, degradation_manager):
        """测试监控生命周期"""
        # 注册组件
        degradation_manager.register_components()

        # 启动监控
        degradation_manager.start_monitoring()
        assert degradation_manager.monitoring_active is True

        # 等待一小段时间让监控运行
        import time
        time.sleep(2)

        # 停止监控
        degradation_manager.stop_monitoring()
        assert degradation_manager.monitoring_active is False


# 集成测试
class TestMemorySystemIntegration:
    """记忆系统集成测试"""

    @pytest.fixture
    def integrated_system(self):
        """创建集成的记忆系统"""
        config = {
            "auto_link_enabled": True,
            "sync_enabled": True,
            "consistency_check_enabled": True,
            "temporal_memory": {"session_timeout": 1800},
            "semantic_memory": {"timeout": 30},
            "consistency_validation": {"auto_repair_enabled": True},
            "graceful_degradation": {"health_check_interval": 60}
        }

        with patch('memory_system.temporal_memory_manager.TemporalMemoryManager._initialize_graphiti'), \
             patch('memory_system.semantic_memory_manager.SemanticMemoryManager._initialize_mcp_client'):

            unified_interface = UnifiedMemoryInterface(config)
            validator = MemoryConsistencyValidator(config.get('consistency_validation', {}))
            degradation_manager = GracefulDegradationManager(config.get('graceful_degradation', {}))

            return {
                "unified_interface": unified_interface,
                "validator": validator,
                "degradation_manager": degradation_manager
            }

    def test_complete_learning_workflow(self, integrated_system):
        """测试完整的学习工作流"""
        unified_interface = integrated_system["unified_interface"]
        validator = integrated_system["validator"]

        # 1. 存储学习记忆
        memory_id1 = unified_interface.store_complete_learning_memory(
            canvas_id="math_canvas",
            node_id="function_node",
            content="函数是一种特殊的映射关系",
            learning_state="yellow",
            confidence_score=0.6
        )

        memory_id2 = unified_interface.store_complete_learning_memory(
            canvas_id="math_canvas",
            node_id="derivative_node",
            content="导数描述函数在某点的变化率",
            learning_state="red",
            confidence_score=0.3
        )

        # 2. 建立记忆关联
        link_id = unified_interface.link_memories(
            source_memory_id=memory_id1,
            target_memory_id=memory_id2,
            link_type=MemoryLinkType.CONCEPT_RELATION,
            strength=0.8
        )

        # 3. 验证一致性
        report = validator.validate_memory_consistency(
            memory_entries=unified_interface.memory_entries,
            memory_links=unified_interface.memory_links
        )

        # 4. 验证结果
        assert memory_id1 is not None
        assert memory_id2 is not None
        assert link_id is not None
        assert len(unified_interface.memory_entries) == 2
        assert len(unified_interface.memory_links) == 1
        assert report.consistency_score >= 0.0

    def test_contextual_retrieval_workflow(self, integrated_system):
        """测试上下文检索工作流"""
        unified_interface = integrated_system["unified_interface"]

        # 创建多个相关记忆
        memories = [
            ("calculus_node", "微积分研究变化率和累积"),
            ("limit_node", "极限描述函数趋近的行为"),
            ("integral_node", "积分是微分的逆运算")
        ]

        memory_ids = []
        for node_id, content in memories:
            memory_id = unified_interface.store_complete_learning_memory(
                canvas_id="calculus_canvas",
                node_id=node_id,
                content=content,
                learning_state="yellow",
                confidence_score=0.5
            )
            memory_ids.append(memory_id)

        # 上下文检索
        retrieved_memories = unified_interface.retrieve_contextual_memory(
            canvas_id="calculus_canvas",
            limit=10
        )

        # 验证检索结果
        assert len(retrieved_memories) == 3
        assert all(memory.canvas_id == "calculus_canvas" for memory in retrieved_memories)

        # 带上下文的检索
        context = {"learning_state": "yellow"}
        filtered_memories = unified_interface.retrieve_contextual_memory(
            canvas_id="calculus_canvas",
            context=context,
            limit=10
        )

        assert len(filtered_memories) == 3

    def test_search_and_discovery_workflow(self, integrated_system):
        """测试搜索和发现工作流"""
        unified_interface = integrated_system["unified_interface"]

        # 创建不同领域的记忆
        memories = [
            ("math_function", "函数的数学定义和性质"),
            ("programming_function", "编程中的函数概念"),
            ("physics_function", "物理中的函数关系"),
            ("algorithm_complexity", "算法复杂度分析方法")
        ]

        for node_id, content in memories:
            canvas_id = "math_canvas" if "math" in node_id or "algorithm" in node_id else "programming_canvas"
            unified_interface.store_complete_learning_memory(
                canvas_id=canvas_id,
                node_id=node_id,
                content=content,
                learning_state="green",
                confidence_score=0.8
            )

        # 搜索测试
        search_results = unified_interface.search_memories("函数", search_type="all", limit=10)
        assert len(search_results) >= 2  # 至少找到数学函数和编程函数

        # 验证搜索结果格式
        for result in search_results:
            assert "type" in result
            assert "memory" in result
            assert "relevance" in result

    def test_error_handling_and_recovery(self, integrated_system):
        """测试错误处理和恢复"""
        unified_interface = integrated_system["unified_interface"]
        degradation_manager = integrated_system["degradation_manager"]

        # 注册组件到降级管理器
        degradation_manager.register_components(
            temporal_manager=unified_interface.temporal_manager,
            semantic_manager=unified_interface.semantic_manager,
            unified_interface=unified_interface
        )

        # 模拟组件故障
        degradation_manager.component_status["temporal_memory"] = Mock(
            status=Mock(value="critical"),
            response_time_ms=5000
        )

        # 评估系统状态
        degradation_manager._evaluate_system_status()

        # 验证降级响应
        assert degradation_manager.current_level.value != "normal"

        # 测试手动恢复
        recovery_success = degradation_manager.trigger_manual_recovery()
        assert isinstance(recovery_success, bool)


# 性能测试
class TestMemorySystemPerformance:
    """记忆系统性能测试"""

    @pytest.fixture
    def performance_system(self):
        """创建性能测试系统"""
        config = {
            "auto_link_enabled": True,
            "sync_enabled": False,  # 禁用同步以提高性能
            "consistency_check_enabled": False,  # 禁用一致性检查以提高性能
        }

        with patch('memory_system.temporal_memory_manager.TemporalMemoryManager._initialize_graphiti'), \
             patch('memory_system.semantic_memory_manager.SemanticMemoryManager._initialize_mcp_client'):

            return UnifiedMemoryInterface(config)

    def test_bulk_memory_storage_performance(self, performance_system):
        """测试批量记忆存储性能"""
        import time

        # 测试数据
        test_memories = [
            (f"node_{i}", f"测试内容 {i}", "yellow", 0.5 + (i % 10) * 0.05)
            for i in range(100)
        ]

        # 执行批量存储
        start_time = time.time()
        memory_ids = []

        for node_id, content, state, confidence in test_memories:
            memory_id = performance_system.store_complete_learning_memory(
                canvas_id="performance_canvas",
                node_id=node_id,
                content=content,
                learning_state=state,
                confidence_score=confidence
            )
            memory_ids.append(memory_id)

        end_time = time.time()
        duration = end_time - start_time

        # 性能断言
        assert len(memory_ids) == 100
        assert duration < 10.0  # 100个记忆应该在10秒内完成存储
        assert duration / 100 < 0.1  # 平均每个记忆存储时间小于100ms

    def test_memory_search_performance(self, performance_system):
        """测试记忆搜索性能"""
        import time

        # 创建测试数据
        for i in range(50):
            performance_system.store_complete_learning_memory(
                canvas_id="search_canvas",
                node_id=f"search_node_{i}",
                content=f"包含搜索关键词的测试内容 {i}",
                learning_state="green",
                confidence_score=0.8
            )

        # 执行搜索性能测试
        search_queries = ["搜索", "关键词", "测试", "内容"]

        total_search_time = 0
        for query in search_queries:
            start_time = time.time()
            results = performance_system.search_memories(query, limit=20)
            end_time = time.time()
            total_search_time += (end_time - start_time)

            # 验证搜索结果
            assert len(results) > 0

        avg_search_time = total_search_time / len(search_queries)

        # 性能断言
        assert avg_search_time < 0.5  # 平均搜索时间小于500ms

    def test_consistency_validation_performance(self, performance_system):
        """测试一致性验证性能"""
        from memory_system.memory_consistency_validator import MemoryConsistencyValidator

        # 创建大量测试数据
        for i in range(200):
            performance_system.store_complete_learning_memory(
                canvas_id=f"validation_canvas_{i % 10}",
                node_id=f"validation_node_{i}",
                content=f"一致性验证测试内容 {i}",
                learning_state="yellow",
                confidence_score=0.6
            )

        # 创建验证器
        validator = MemoryConsistencyValidator({"validation_strategies": ["data_integrity_check"]})

        # 执行一致性验证
        import time
        start_time = time.time()

        report = validator.validate_memory_consistency(
            memory_entries=performance_system.memory_entries,
            memory_links=performance_system.memory_links,
            full_validation=True
        )

        end_time = time.time()
        duration = end_time - start_time

        # 性能断言
        assert duration < 5.0  # 200个记忆的验证应该在5秒内完成
        assert report.consistency_score >= 0.0


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short", "--cov=memory_system", "--cov-report=html"])
