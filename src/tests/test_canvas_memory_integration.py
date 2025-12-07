"""
Canvas Learning System v2.0 - Canvas记忆系统集成测试

测试Canvas记忆系统集成的功能和向后兼容性。

Author: Canvas Learning System Team
Version: 2.0
Created: 2025-10-23
"""

import json
import os
import shutil
import sys
import tempfile
from unittest.mock import Mock, patch

import pytest

# 添加项目根目录到路径
sys.path.append('..')
sys.path.append('../memory_system')

from canvas_memory_integration import (
    BackwardCompatibleCanvas,
    CanvasMemoryIntegration,
    EnhancedCanvasOrchestrator,
    create_canvas_memory_integration,
    create_enhanced_canvas_orchestrator,
)


class TestCanvasMemoryIntegration:
    """Canvas记忆系统集成测试类"""

    @pytest.fixture
    def temp_canvas_file(self):
        """创建临时Canvas文件"""
        temp_dir = tempfile.mkdtemp()
        canvas_path = os.path.join(temp_dir, "test_canvas.canvas")

        # 创建基本的Canvas结构
        canvas_data = {
            "nodes": [
                {
                    "id": "root",
                    "type": "text",
                    "content": "测试Canvas",
                    "color": "1",
                    "x": 100,
                    "y": 100,
                    "width": 200,
                    "height": 100
                }
            ],
            "edges": []
        }

        with open(canvas_path, 'w', encoding='utf-8') as f:
            json.dump(canvas_data, f, ensure_ascii=False, indent=2)

        yield canvas_path

        # 清理
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_config(self):
        """模拟配置"""
        return {
            "memory_enabled": True,
            "auto_record_learning": True,
            "semantic_analysis_enabled": True,
            "consistency_check_enabled": True,
            "unified_memory": {
                "auto_link_enabled": True,
                "sync_enabled": True
            }
        }

    @pytest.fixture
    def memory_integration(self, mock_config):
        """创建Canvas记忆系统集成实例"""
        with patch('canvas_memory_integration.UnifiedMemoryInterface'), \
             patch('canvas_memory_integration.TemporalMemoryManager'), \
             patch('canvas_memory_integration.SemanticMemoryManager'), \
             patch('canvas_memory_integration.MemoryConsistencyValidator'), \
             patch('canvas_memory_integration.GracefulDegradationManager'):

            integration = CanvasMemoryIntegration()
            integration.memory_enabled = True
            return integration

    def test_load_default_config(self):
        """测试加载默认配置"""
        integration = CanvasMemoryIntegration()

        assert integration.config["memory_enabled"] is True
        assert integration.config["auto_record_learning"] is True
        assert integration.config["semantic_analysis_enabled"] is True
        assert integration.config["consistency_check_enabled"] is True

    def test_load_config_from_file(self, temp_canvas_file):
        """测试从文件加载配置"""
        # 创建配置文件
        config_dir = os.path.dirname(temp_canvas_file)
        config_path = os.path.join(config_dir, "test_config.yaml")

        config_data = {
            "memory_enabled": False,
            "auto_record_learning": False,
            "custom_setting": "test_value"
        }

        try:
            import yaml
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f)

            # 加载配置
            integration = CanvasMemoryIntegration(config_path)

            assert integration.config["memory_enabled"] is False
            assert integration.config["auto_record_learning"] is False
            assert integration.config["custom_setting"] == "test_value"

        except ImportError:
            # 如果yaml不可用，跳过此测试
            pytest.skip("YAML not available")
        finally:
            if os.path.exists(config_path):
                os.remove(config_path)

    def test_initialize_memory_system_success(self, memory_integration):
        """测试成功初始化记忆系统"""
        # 验证组件已初始化
        assert memory_integration.unified_memory is not None
        assert memory_integration.temporal_manager is not None
        assert memory_integration.semantic_manager is not None
        assert memory_integration.consistency_validator is not None
        assert memory_integration.degradation_manager is not None

    def test_initialize_memory_system_disabled(self):
        """测试禁用记忆系统时的初始化"""
        config = {"memory_enabled": False}
        integration = CanvasMemoryIntegration(config)

        assert integration.memory_enabled is False
        assert integration.unified_memory is None
        assert integration.temporal_manager is None
        assert integration.semantic_manager is None

    def test_record_canvas_interaction_success(self, memory_integration, temp_canvas_file):
        """测试成功记录Canvas交互"""
        # 配置mock
        memory_integration.unified_memory.store_complete_learning_memory.return_value = "memory_123"

        # 记录交互
        memory_id = memory_integration.record_canvas_interaction(
            canvas_path=temp_canvas_file,
            node_id="test_node",
            interaction_type="node_creation",
            content="测试内容",
            learning_state="yellow",
            confidence_score=0.6,
            metadata={"test": True}
        )

        # 验证结果
        assert memory_id == "memory_123"

        # 验证调用
        memory_integration.unified_memory.store_complete_learning_memory.assert_called_once()
        call_args = memory_integration.unified_memory.store_complete_learning_memory.call_args

        assert call_args[1]["canvas_id"] == "test_canvas"  # 从文件路径提取
        assert call_args[1]["node_id"] == "test_node"
        assert call_args[1]["content"] == "测试内容"
        assert call_args[1]["learning_state"] == "yellow"
        assert call_args[1]["confidence_score"] == 0.6

    def test_record_canvas_interaction_disabled(self, memory_integration, temp_canvas_file):
        """测试禁用记忆时的交互记录"""
        memory_integration.memory_enabled = False

        memory_id = memory_integration.record_canvas_interaction(
            canvas_path=temp_canvas_file,
            node_id="test_node",
            interaction_type="node_creation",
            content="测试内容"
        )

        assert memory_id is None

    def test_record_canvas_interaction_with_semantic_analysis(self, memory_integration, temp_canvas_file):
        """测试带语义分析的交互记录"""
        # 配置mock
        memory_integration.unified_memory.store_complete_learning_memory.return_value = "memory_123"
        memory_integration.semantic_manager.understand_semantic_context.return_value = {
            "semantic_tags": ["math", "function"],
            "understanding_score": 0.8
        }

        # 记录交互
        memory_id = memory_integration.record_canvas_interaction(
            canvas_path=temp_canvas_file,
            node_id="test_node",
            interaction_type="node_edit",
            content="函数是一种特殊的映射关系"
        )

        # 验证语义分析被调用
        memory_integration.semantic_manager.understand_semantic_context.assert_called_once()

    def test_get_memory_context_for_canvas(self, memory_integration, temp_canvas_file):
        """测试获取Canvas相关的记忆上下文"""
        # 配置mock
        mock_memories = [
            Mock(to_dict=lambda: {"memory_id": "mem1", "content": "内容1"}),
            Mock(to_dict=lambda: {"memory_id": "mem2", "content": "内容2"})
        ]
        memory_integration.unified_memory.retrieve_contextual_memory.return_value = mock_memories

        # 获取记忆上下文
        context = memory_integration.get_memory_context_for_canvas(temp_canvas_file)

        # 验证结果
        assert len(context) == 2
        assert context[0]["memory_id"] == "mem1"
        assert context[1]["memory_id"] == "mem2"

        # 验证调用参数
        memory_integration.unified_memory.retrieve_contextual_memory.assert_called_once_with(
            canvas_id="test_canvas",
            node_id=None,
            limit=10
        )

    def test_search_canvas_memories(self, memory_integration, temp_canvas_file):
        """测试搜索Canvas相关的记忆"""
        # 配置mock
        mock_results = [
            {"memory": {"canvas_id": "test_canvas", "content": "函数定义"}, "type": "unified"},
            {"memory": {"canvas_id": "test_canvas", "content": "数学公式"}, "type": "unified"}
        ]
        memory_integration.unified_memory.search_memories.return_value = mock_results

        # 搜索记忆
        results = memory_integration.search_canvas_memories(
            canvas_path=temp_canvas_file,
            query="函数",
            search_type="unified",
            limit=10
        )

        # 验证结果
        assert len(results) == 2
        assert results[0]["memory"]["canvas_id"] == "test_canvas"

    def test_run_consistency_check(self, memory_integration):
        """测试运行一致性检查"""
        # 配置mock
        mock_report = Mock(to_dict=lambda: {
            "consistency_score": 0.95,
            "inconsistencies_found": [],
            "recommendations": []
        })
        memory_integration.consistency_validator.validate_memory_consistency.return_value = mock_report

        # 运行一致性检查
        report = memory_integration.run_consistency_check()

        # 验证结果
        assert report is not None
        assert report["consistency_score"] == 0.95
        assert len(report["inconsistencies_found"]) == 0

    def test_get_memory_system_status(self, memory_integration):
        """测试获取记忆系统状态"""
        # 配置mock
        memory_integration.unified_memory.get_status.return_value = {
            "initialized": True,
            "memory_count": 10
        }
        memory_integration.temporal_manager.get_status.return_value = {
            "initialized": True,
            "current_session": "session_123"
        }
        memory_integration.semantic_manager.get_status.return_value = {
            "initialized": True,
            "mcp_available": True
        }
        memory_integration.degradation_manager.get_system_status.return_value = {
            "current_level": "normal",
            "system_status": "healthy"
        }

        # 获取状态
        status = memory_integration.get_memory_system_status()

        # 验证结果
        assert status["memory_enabled"] is True
        assert "unified_memory" in status["components"]
        assert "temporal_manager" in status["components"]
        assert "semantic_manager" in status["components"]
        assert "degradation_manager" in status["components"]

    def test_cleanup(self, memory_integration):
        """测试资源清理"""
        # 配置mock
        memory_integration.degradation_manager.stop_monitoring = Mock()
        memory_integration.unified_memory.cleanup = Mock()
        memory_integration.temporal_manager.cleanup = Mock()
        memory_integration.semantic_manager.cleanup = Mock()

        # 执行清理
        memory_integration.cleanup()

        # 验证清理调用
        memory_integration.degradation_manager.stop_monitoring.assert_called_once()
        memory_integration.unified_memory.cleanup.assert_called_once()
        memory_integration.temporal_manager.cleanup.assert_called_once()
        memory_integration.semantic_manager.cleanup.assert_called_once()


class TestEnhancedCanvasOrchestrator:
    """增强Canvas编排器测试类"""

    @pytest.fixture
    def mock_memory_integration(self):
        """创建模拟的记忆集成"""
        mock_integration = Mock()
        mock_integration.memory_enabled = True
        mock_integration.record_canvas_interaction.return_value = "memory_123"
        return mock_integration

    @pytest.fixture
    def enhanced_orchestrator(self, temp_canvas_file, mock_memory_integration):
        """创建增强的Canvas编排器"""
        with patch('canvas_memory_integration.CanvasOrchestrator'):
            orchestrator = EnhancedCanvasOrchestrator(temp_canvas_file, mock_memory_integration)
            # 模拟父类方法
            orchestrator.add_node = Mock(return_value="node_123")
            orchestrator.edit_node = Mock(return_value=True)
            orchestrator.score_node = Mock(return_value=True)
            orchestrator.find_node_by_id = Mock(return_value={
                "id": "node_123",
                "content": "原始内容",
                "color": "1"
            })
            return orchestrator

    def test_add_node_with_memory(self, enhanced_orchestrator, mock_memory_integration):
        """测试带记忆记录的添加节点"""
        # 添加节点
        node_id = enhanced_orchestrator.add_node_with_memory(
            node_type="text",
            content="测试节点内容",
            node_color="1",
            metadata={"custom": True}
        )

        # 验证结果
        assert node_id == "node_123"

        # 验证父类方法被调用
        enhanced_orchestrator.add_node.assert_called_once_with(
            "text", "测试节点内容", "1", {"custom": True}
        )

        # 验证记忆记录被调用
        mock_memory_integration.record_canvas_interaction.assert_called_once()
        call_args = mock_memory_integration.record_canvas_interaction.call_args

        assert call_args[1]["canvas_path"] == enhanced_orchestrator.canvas_path
        assert call_args[1]["node_id"] == "node_123"
        assert call_args[1]["interaction_type"] == "node_creation"
        assert call_args[1]["content"] == "测试节点内容"
        assert call_args[1]["learning_state"] == "yellow"
        assert call_args[1]["confidence_score"] == 0.3

    def test_edit_node_with_memory(self, enhanced_orchestrator, mock_memory_integration):
        """测试带记忆记录的编辑节点"""
        # 编辑节点
        success = enhanced_orchestrator.edit_node_with_memory(
            node_id="node_123",
            new_content="更新后的内容",
            metadata={"edited": True}
        )

        # 验证结果
        assert success is True

        # 验证父类方法被调用
        enhanced_orchestrator.edit_node.assert_called_once_with(
            "node_123", "更新后的内容", {"edited": True}
        )

        # 验证记忆记录被调用
        mock_memory_integration.record_canvas_interaction.assert_called_once()
        call_args = mock_memory_integration.record_canvas_interaction.call_args

        assert call_args[1]["node_id"] == "node_123"
        assert call_args[1]["interaction_type"] == "node_edit"
        assert call_args[1]["content"] == "更新后的内容"
        assert call_args[1]["old_content"] == "原始内容"

    def test_score_node_with_memory(self, enhanced_orchestrator, mock_memory_integration):
        """测试带记忆记录的评分节点"""
        # 评分节点
        success = enhanced_orchestrator.score_node_with_memory(
            node_id="node_123",
            score=85,
            feedback="很好的理解"
        )

        # 验证结果
        assert success is True

        # 验证父类方法被调用
        enhanced_orchestrator.score_node.assert_called_once_with("node_123", 85, "很好的理解")

        # 验证记忆记录被调用
        mock_memory_integration.record_canvas_interaction.assert_called_once()
        call_args = mock_memory_integration.record_canvas_interaction.call_args

        assert call_args[1]["node_id"] == "node_123"
        assert call_args[1]["interaction_type"] == "node_scoring"
        assert call_args[1]["learning_state"] == "green"  # 85分对应green状态
        assert call_args[1]["confidence_score"] == 0.85

    def test_score_node_learning_state_inference(self, enhanced_orchestrator, mock_memory_integration):
        """测试评分节点时的学习状态推断"""
        test_cases = [
            (95, "green"),
            (75, "purple"),
            (45, "yellow"),
            (25, "red")
        ]

        for score, expected_state in test_cases:
            # 重置mock
            mock_memory_integration.reset_mock()

            # 评分节点
            enhanced_orchestrator.score_node_with_memory(node_id="node_123", score=score)

            # 验证学习状态推断
            call_args = mock_memory_integration.record_canvas_interaction.call_args
            assert call_args[1]["learning_state"] == expected_state
            assert call_args[1]["confidence_score"] == score / 100.0

    def test_get_memory_context_for_node(self, enhanced_orchestrator, mock_memory_integration):
        """测试获取节点相关的记忆上下文"""
        # 配置mock
        mock_context = [{"memory_id": "mem1", "content": "相关内容"}]
        mock_memory_integration.get_memory_context_for_canvas.return_value = mock_context

        # 获取记忆上下文
        context = enhanced_orchestrator.get_memory_context_for_node("node_123", limit=5)

        # 验证结果
        assert len(context) == 1
        assert context[0]["memory_id"] == "mem1"

        # 验证调用参数
        mock_memory_integration.get_memory_context_for_canvas.assert_called_once_with(
            canvas_path=enhanced_orchestrator.canvas_path,
            node_id="node_123",
            limit=5
        )

    def test_search_related_memories(self, enhanced_orchestrator, mock_memory_integration):
        """测试搜索相关记忆"""
        # 配置mock
        mock_memories = [{"memory_id": "mem1", "content": "函数相关"}]
        mock_memory_integration.search_canvas_memories.return_value = mock_memories

        # 搜索记忆
        memories = enhanced_orchestrator.search_related_memories("函数定义", limit=10)

        # 验证结果
        assert len(memories) == 1
        assert memories[0]["memory_id"] == "mem1"

        # 验证调用参数
        mock_memory_integration.search_canvas_memories.assert_called_once_with(
            canvas_path=enhanced_orchestrator.canvas_path,
            query="函数定义",
            limit=10
        )

    def test_get_memory_enhanced_node_summary(self, enhanced_orchestrator, mock_memory_integration):
        """测试获取记忆增强的节点摘要"""
        # 配置mock
        mock_context = [{"memory_id": "mem1", "content": "相关记忆"}]
        mock_memories = [{"memory_id": "mem2", "content": "相关记忆2"}]

        mock_memory_integration.get_memory_context_for_canvas.return_value = mock_context
        mock_memory_integration.search_canvas_memories.return_value = mock_memories

        # 获取节点摘要
        summary = enhanced_orchestrator.get_memory_enhanced_node_summary("node_123")

        # 验证结果结构
        assert "node_id" in summary
        assert "content" in summary
        assert "color" in summary
        assert "type" in summary
        assert "memory_context" in summary
        assert "related_memories" in summary

        # 验证具体内容
        assert summary["node_id"] == "node_123"
        assert summary["content"] == "原始内容"
        assert len(summary["memory_context"]) == 1
        assert len(summary["related_memories"]) == 1


class TestBackwardCompatibleCanvas:
    """向后兼容Canvas测试类"""

    @pytest.fixture
    def temp_canvas_file(self):
        """创建临时Canvas文件"""
        temp_dir = tempfile.mkdtemp()
        canvas_path = os.path.join(temp_dir, "compatible_canvas.canvas")

        canvas_data = {"nodes": [], "edges": []}
        with open(canvas_path, 'w', encoding='utf-8') as f:
            json.dump(canvas_data, f)

        yield canvas_path
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def compatible_canvas(self, temp_canvas_file):
        """创建向后兼容Canvas实例"""
        with patch('canvas_memory_integration.CanvasOrchestrator') as mock_orchestrator_class:
            mock_orchestrator = Mock()
            mock_orchestrator.add_node.return_value = "node_123"
            mock_orchestrator.edit_node.return_value = True
            mock_orchestrator.score_node.return_value = True
            mock_orchestrator.find_node_by_id.return_value = {
                "id": "node_123",
                "content": "测试内容"
            }
            mock_orchestrator_class.return_value = mock_orchestrator

            canvas = BackwardCompatibleCanvas(temp_canvas_file)
            canvas.orchestrator = mock_orchestrator
            return canvas

    def test_initialization_with_memory_enabled(self, temp_canvas_file):
        """测试启用记忆时的初始化"""
        with patch('canvas_memory_integration.create_canvas_memory_integration') as mock_create:
            mock_integration = Mock()
            mock_integration.create_enhanced_canvas_orchestrator.return_value = Mock()
            mock_create.return_value = mock_integration

            canvas = BackwardCompatibleCanvas(temp_canvas_file, enable_memory=True)

            assert canvas.enable_memory is True
            assert canvas.memory_integration is not None
            assert canvas.enhanced_orchestrator is not None

    def test_initialization_with_memory_disabled(self, temp_canvas_file):
        """测试禁用记忆时的初始化"""
        canvas = BackwardCompatibleCanvas(temp_canvas_file, enable_memory=False)

        assert canvas.enable_memory is False
        assert canvas.memory_integration is None
        assert canvas.enhanced_orchestrator is None

    def test_add_node_with_memory_enabled(self, compatible_canvas):
        """测试启用记忆时添加节点"""
        # 配置增强编排器
        compatible_canvas.enhanced_orchestrator = Mock()
        compatible_canvas.enhanced_orchestrator.add_node_with_memory.return_value = "enhanced_node_123"

        # 添加节点
        node_id = compatible_canvas.add_node("text", "测试内容", "1")

        # 验证使用了增强编排器
        compatible_canvas.enhanced_orchestrator.add_node_with_memory.assert_called_once_with(
            "text", "测试内容", "1", None
        )

    def test_add_node_with_memory_disabled(self, compatible_canvas):
        """测试禁用记忆时添加节点"""
        compatible_canvas.enable_memory = False
        compatible_canvas.enhanced_orchestrator = None

        # 添加节点
        node_id = compatible_canvas.add_node("text", "测试内容", "1")

        # 验证使用了原始编排器
        compatible_canvas.orchestrator.add_node.assert_called_once_with(
            "text", "测试内容", "1", None
        )

    def test_edit_node_delegation(self, compatible_canvas):
        """测试编辑节点代理"""
        # 编辑节点
        success = compatible_canvas.edit_node("node_123", "新内容")

        # 验证代理调用
        compatible_canvas.orchestrator.edit_node.assert_called_once_with("node_123", "新内容", None)

    def test_score_node_delegation(self, compatible_canvas):
        """测试评分节点代理"""
        # 评分节点
        success = compatible_canvas.score_node("node_123", 85, "很好")

        # 验证代理调用
        compatible_canvas.orchestrator.score_node.assert_called_once_with("node_123", 85, "很好")

    def test_get_memory_context_new_feature(self, compatible_canvas):
        """测试获取记忆上下文新功能"""
        # 配置增强编排器
        compatible_canvas.enhanced_orchestrator = Mock()
        compatible_canvas.enhanced_orchestrator.get_memory_context_for_node.return_value = [
            {"memory_id": "mem1", "content": "相关内容"}
        ]

        # 获取记忆上下文
        context = compatible_canvas.get_memory_context("node_123", limit=5)

        # 验证调用
        compatible_canvas.enhanced_orchestrator.get_memory_context_for_node.assert_called_once_with(
            "node_123", 5
        )
        assert len(context) == 1

    def test_search_memories_new_feature(self, compatible_canvas):
        """测试搜索记忆新功能"""
        # 配置增强编排器
        compatible_canvas.enhanced_orchestrator = Mock()
        compatible_canvas.enhanced_orchestrator.search_related_memories.return_value = [
            {"memory_id": "mem1", "content": "搜索结果"}
        ]

        # 搜索记忆
        memories = compatible_canvas.search_memories("函数", limit=10)

        # 验证调用
        compatible_canvas.enhanced_orchestrator.search_related_memories.assert_called_once_with(
            "函数", 10
        )
        assert len(memories) == 1

    def test_get_memory_status_new_feature(self, compatible_canvas):
        """测试获取记忆状态新功能"""
        # 配置记忆集成
        compatible_canvas.memory_integration = Mock()
        compatible_canvas.memory_integration.get_memory_system_status.return_value = {
            "memory_enabled": True,
            "components": {}
        }

        # 获取状态
        status = compatible_canvas.get_memory_status()

        # 验证结果
        assert status["memory_enabled"] is True
        assert "components" in status

    def test_get_memory_status_without_memory(self, compatible_canvas):
        """测试无记忆时的状态获取"""
        compatible_canvas.memory_integration = None

        # 获取状态
        status = compatible_canvas.get_memory_status()

        # 验证结果
        assert status["memory_enabled"] is False

    def test_attribute_proxy_to_original_orchestrator(self, compatible_canvas):
        """测试属性代理到原始编排器"""
        # 测试访问不存在的属性应该代理到原始编排器
        with patch.object(compatible_canvas.orchestrator, 'custom_method', return_value="custom_result"):
            result = compatible_canvas.custom_method("arg1", "arg2")

            assert result == "custom_result"
            compatible_canvas.orchestrator.custom_method.assert_called_once_with("arg1", "arg2")


class TestConvenienceFunctions:
    """便捷函数测试类"""

    def test_create_canvas_memory_integration(self):
        """测试创建Canvas记忆系统集成"""
        with patch('canvas_memory_integration.CanvasMemoryIntegration') as mock_class:
            mock_instance = Mock()
            mock_class.return_value = mock_instance

            result = create_canvas_memory_integration("test_config.yaml")

            mock_class.assert_called_once_with("test_config.yaml")
            assert result == mock_instance

    def test_create_enhanced_canvas_orchestrator(self):
        """测试创建增强Canvas编排器"""
        with patch('canvas_memory_integration.create_canvas_memory_integration') as mock_create, \
             patch('canvas_memory_integration.CanvasMemoryIntegration') as mock_class:

            mock_integration = Mock()
            mock_orchestrator = Mock()
            mock_create.return_value = mock_integration
            mock_integration.create_enhanced_canvas_orchestrator.return_value = mock_orchestrator

            result = create_enhanced_canvas_orchestrator("test_canvas.canvas", "test_config.yaml")

            mock_create.assert_called_once_with("test_config.yaml")
            mock_integration.create_enhanced_canvas_orchestrator.assert_called_once_with("test_canvas.canvas")
            assert result == mock_orchestrator


class TestIntegrationWorkflows:
    """集成工作流测试类"""

    @pytest.fixture
    def temp_canvas_file(self):
        """创建临时Canvas文件"""
        temp_dir = tempfile.mkdtemp()
        canvas_path = os.path.join(temp_dir, "workflow_canvas.canvas")

        canvas_data = {"nodes": [], "edges": []}
        with open(canvas_path, 'w', encoding='utf-8') as f:
            json.dump(canvas_data, f)

        yield canvas_path
        shutil.rmtree(temp_dir)

    def test_complete_learning_workflow_with_memory(self, temp_canvas_file):
        """测试带记忆的完整学习工作流"""
        with patch('canvas_memory_integration.CanvasMemoryIntegration') as mock_integration_class, \
             patch('canvas_memory_integration.CanvasOrchestrator'):

            # 配置mock
            mock_integration = Mock()
            mock_integration.memory_enabled = True
            mock_integration.record_canvas_interaction.return_value = "memory_123"
            mock_integration.create_enhanced_canvas_orchestrator.return_value = Mock()
            mock_integration_class.return_value = mock_integration

            mock_orchestrator = Mock()
            mock_orchestrator.add_node.return_value = "node_123"
            mock_orchestrator.edit_node.return_value = True
            mock_orchestrator.score_node.return_value = True
            mock_orchestrator.find_node_by_id.return_value = {
                "id": "node_123",
                "content": "原始内容"
            }

            # 创建增强编排器
            orchestrator = create_enhanced_canvas_orchestrator(temp_canvas_file)
            orchestrator.add_node = mock_orchestrator.add_node
            orchestrator.edit_node = mock_orchestrator.edit_node
            orchestrator.score_node = mock_orchestrator.score_node
            orchestrator.find_node_by_id = mock_orchestrator.find_node_by_id

            # 执行学习工作流
            # 1. 添加节点
            node_id = orchestrator.add_node_with_memory(
                node_type="text",
                content="函数是一种特殊的映射关系",
                node_color="1"
            )

            # 2. 编辑节点
            success = orchestrator.edit_node_with_memory(
                node_id=node_id,
                new_content="函数是一种特殊的映射关系，它将定义域中的每个元素映射到值域中的唯一元素。"
            )

            # 3. 评分节点
            success = orchestrator.score_node_with_memory(
                node_id=node_id,
                score=85,
                feedback="对函数概念理解正确"
            )

            # 4. 获取记忆上下文
            context = orchestrator.get_memory_context_for_node(node_id)

            # 5. 搜索相关记忆
            related_memories = orchestrator.search_related_memories("映射关系")

            # 验证工作流结果
            assert node_id == "node_123"
            assert success is True
            assert mock_integration.record_canvas_interaction.call_count == 3  # 添加、编辑、评分

    def test_backward_compatibility_workflow(self, temp_canvas_file):
        """测试向后兼容工作流"""
        with patch('canvas_memory_integration.CanvasOrchestrator') as mock_orchestrator_class:
            # 配置mock
            mock_orchestrator = Mock()
            mock_orchestrator.add_node.return_value = "node_123"
            mock_orchestrator.edit_node.return_value = True
            mock_orchestrator.score_node.return_value = True
            mock_orchestrator_class.return_value = mock_orchestrator

            # 创建兼容Canvas
            canvas = BackwardCompatibleCanvas(temp_canvas_file, enable_memory=False)

            # 执行传统工作流
            node_id = canvas.add_node("text", "传统节点内容", "1")
            success = canvas.edit_node(node_id, "编辑后的内容")
            score_success = canvas.score_node(node_id, 75, "理解良好")

            # 验证结果
            assert node_id == "node_123"
            assert success is True
            assert score_success is True

            # 验证调用原始方法
            mock_orchestrator.add_node.assert_called_once_with("text", "传统节点内容", "1", None)
            mock_orchestrator.edit_node.assert_called_once_with("node_123", "编辑后的内容", None)
            mock_orchestrator.score_node.assert_called_once_with("node_123", 75, "理解良好")

    def test_mixed_mode_workflow(self, temp_canvas_file):
        """测试混合模式工作流（部分启用记忆）"""
        with patch('canvas_memory_integration.CanvasMemoryIntegration') as mock_integration_class, \
             patch('canvas_memory_integration.CanvasOrchestrator') as mock_orchestrator_class:

            # 配置mock
            mock_integration = Mock()
            mock_integration.memory_enabled = True
            mock_integration.record_canvas_interaction.return_value = "memory_123"
            mock_integration.create_enhanced_canvas_orchestrator.return_value = Mock()
            mock_integration_class.return_value = mock_integration

            mock_orchestrator = Mock()
            mock_orchestrator.add_node.return_value = "node_123"
            mock_orchestrator.edit_node.return_value = True
            mock_orchestrator.score_node.return_value = True
            mock_orchestrator.find_node_by_id.return_value = {
                "id": "node_123",
                "content": "测试内容"
            }

            # 创建Canvas（启用记忆）
            canvas = BackwardCompatibleCanvas(temp_canvas_file, enable_memory=True)
            canvas.orchestrator = mock_orchestrator
            canvas.enhanced_orchestrator = Mock()
            canvas.enhanced_orchestrator.add_node_with_memory.return_value = "node_123"
            canvas.enhanced_orchestrator.edit_node_with_memory.return_value = True
            canvas.enhanced_orchestrator.score_node_with_memory.return_value = True

            # 混合使用新旧功能
            # 使用新功能（带记忆）
            node_id1 = canvas.add_node("text", "带记忆的节点", "1")

            # 使用新功能（带记忆）
            success1 = canvas.edit_node(node_id1, "编辑带记忆的节点")

            # 使用新功能（带记忆）
            success2 = canvas.score_node(node_id1, 90, "优秀")

            # 使用新功能（获取记忆上下文）
            context = canvas.get_memory_context(node_id1)

            # 使用新功能（搜索记忆）
            memories = canvas.search_memories("节点")

            # 使用传统功能
            canvas_status = canvas.get_canvas_status() if hasattr(canvas, 'get_canvas_status') else "traditional"

            # 验证混合工作流
            assert node_id1 == "node_123"
            assert success1 is True
            assert success2 is True
            assert isinstance(context, list)
            assert isinstance(memories, list)


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
