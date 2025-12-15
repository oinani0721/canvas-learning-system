"""
Canvas Learning System v2.0 - Canvas记忆系统集成

扩展现有Canvas操作类，集成统一记忆接口。
保持向后兼容性的同时添加新的记忆功能。

Author: Canvas Learning System Team
Version: 2.0
Created: 2025-10-23
"""

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import sys

# 导入现有Canvas操作
from canvas_utils import CanvasJSONOperator, CanvasBusinessLogic, CanvasOrchestrator

# 导入统一记忆系统
from memory_system import (
    UnifiedMemoryInterface,
    TemporalMemoryManager,
    SemanticMemoryManager,
    MemoryConsistencyValidator,
    GracefulDegradationManager,
    UnifiedMemoryEntry,
    MemoryLink,
    MemoryType,
    MemoryLinkType,
    LearningState,
    InteractionType
)

# 导入配置
try:
    import yaml
    CONFIG_LOADED = True
except ImportError:
    CONFIG_LOADED = False
    import json as config_module


class CanvasMemoryIntegration:
    """Canvas记忆系统集成类

    为现有Canvas操作添加统一记忆功能：
    - 保持向后兼容性
    - 自动记录学习历程
    - 语义理解与关联
    - 一致性验证和降级处理
    """

    def __init__(self, config_path: Optional[str] = None):
        """初始化Canvas记忆系统集成"""
        self.config = self._load_config(config_path)

        # 初始化统一记忆系统组件
        self.unified_memory = None
        self.temporal_manager = None
        self.semantic_manager = None
        self.consistency_validator = None
        self.degradation_manager = None

        # 配置参数
        self.memory_enabled = self.config.get('memory_enabled', True)
        self.auto_record_learning = self.config.get('auto_record_learning', True)
        self.semantic_analysis_enabled = self.config.get('semantic_analysis_enabled', True)
        self.consistency_check_enabled = self.config.get('consistency_check_enabled', True)

        # 初始化组件
        self._initialize_memory_system()

        # 现有Canvas操作类的包装器
        self.canvas_operator = None
        self.canvas_business = None
        self.canvas_orchestrator = None

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """加载配置文件"""
        default_config = {
            "memory_enabled": True,
            "auto_record_learning": True,
            "semantic_analysis_enabled": True,
            "consistency_check_enabled": True,
            "unified_memory": {
                "auto_link_enabled": True,
                "sync_enabled": True,
                "consistency_check_enabled": True
            },
            "temporal_memory": {
                "neo4j_uri": "bolt://localhost:7687",
                "neo4j_username": "neo4j",
                "neo4j_password": "password",
                "session_timeout": 1800
            },
            "semantic_memory": {
                "endpoint": "local",
                "timeout": 30,
                "max_text_length": 512,
                "similarity_threshold": 0.7
            },
            "consistency_validation": {
                "auto_repair_enabled": True,
                "validation_strategies": [
                    "cross_reference_check",
                    "data_integrity_check",
                    "timestamp_consistency",
                    "relationship_validation"
                ]
            },
            "graceful_degradation": {
                "enabled": True,
                "health_check_interval": 60,
                "health_check_timeout": 10,
                "failure_threshold": 3
            }
        }

        if not config_path or not CONFIG_LOADED:
            return default_config

        try:
            config_file = Path(config_path)
            if not config_file.exists():
                # 尝试默认配置路径
                default_paths = [
                    "config/canvas_v2_config.yaml",
                    "config/memory_system_config.yaml",
                    "canvas_v2_config.yaml"
                ]
                for path in default_paths:
                    if Path(path).exists():
                        config_file = Path(path)
                        break

            if config_file.exists():
                if config_file.suffix.lower() in ['.yaml', '.yml']:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        loaded_config = yaml.safe_load(f)
                else:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        loaded_config = json.load(f)

                # 合并默认配置和加载的配置
                return {**default_config, **loaded_config}
            else:
                print(f"配置文件不存在: {config_path}，使用默认配置")
                return default_config

        except Exception as e:
            print(f"配置文件加载失败: {e}，使用默认配置")
            return default_config

    def _initialize_memory_system(self):
        """初始化记忆系统组件"""
        if not self.memory_enabled:
            return

        try:
            # 初始化统一记忆接口
            unified_config = self.config.get('unified_memory', {})
            self.unified_memory = UnifiedMemoryInterface(unified_config)

            # 初始化时序记忆管理器
            temporal_config = self.config.get('temporal_memory', {})
            self.temporal_manager = TemporalMemoryManager(temporal_config)

            # 初始化语义记忆管理器
            semantic_config = self.config.get('semantic_memory', {})
            self.semantic_manager = SemanticMemoryManager(semantic_config)

            # 初始化一致性验证器
            consistency_config = self.config.get('consistency_validation', {})
            self.consistency_validator = MemoryConsistencyValidator(consistency_config)

            # 初始化优雅降级管理器
            degradation_config = self.config.get('graceful_degradation', {})
            self.degradation_manager = GracefulDegradationManager(degradation_config)

            # 注册组件到降级管理器
            self.degradation_manager.register_components(
                temporal_manager=self.temporal_manager,
                semantic_manager=self.semantic_manager,
                unified_interface=self.unified_memory
            )

            # 启动健康监控
            if self.degradation_manager:
                self.degradation_manager.start_monitoring()

            print("Canvas记忆系统集成初始化成功")

        except Exception as e:
            print(f"记忆系统初始化失败: {e}")
            self.memory_enabled = False

    def create_enhanced_canvas_orchestrator(self, canvas_path: str) -> 'EnhancedCanvasOrchestrator':
        """创建增强的Canvas编排器"""
        return EnhancedCanvasOrchestrator(
            canvas_path=canvas_path,
            memory_integration=self
        )

    def record_canvas_interaction(self,
                                 canvas_path: str,
                                 node_id: str,
                                 interaction_type: str,
                                 content: str,
                                 learning_state: str = "unknown",
                                 confidence_score: float = 0.0,
                                 metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """记录Canvas交互到记忆系统"""
        if not self.memory_enabled or not self.unified_memory:
            return None

        try:
            # 提取Canvas ID
            canvas_id = Path(canvas_path).stem

            # 构建元数据
            interaction_metadata = {
                "interaction_type": interaction_type,
                "canvas_path": canvas_path,
                "timestamp": datetime.now().isoformat(),
                **(metadata or {})
            }

            # 推断学习状态
            if learning_state == "unknown":
                learning_state = self._infer_learning_state(interaction_type, confidence_score)

            # 存储完整学习记忆
            memory_id = self.unified_memory.store_complete_learning_memory(
                canvas_id=canvas_id,
                node_id=node_id,
                content=content,
                learning_state=learning_state,
                confidence_score=confidence_score,
                metadata=interaction_metadata
            )

            # 语义分析
            if self.semantic_analysis_enabled and self.semantic_manager:
                try:
                    semantic_context = self.semantic_manager.understand_semantic_context(
                        content=content,
                        context=interaction_metadata
                    )
                    # 将语义分析结果添加到元数据
                    interaction_metadata["semantic_analysis"] = semantic_context
                except Exception as e:
                    print(f"语义分析失败: {e}")

            return memory_id

        except Exception as e:
            print(f"记录Canvas交互失败: {e}")
            return None

    def _infer_learning_state(self, interaction_type: str, confidence_score: float) -> str:
        """根据交互类型和置信度推断学习状态"""
        if confidence_score >= 0.8:
            return "green"
        elif confidence_score >= 0.7:
            return "purple"
        elif confidence_score >= 0.5:
            return "yellow"
        else:
            return "red"

    def get_memory_context_for_canvas(self,
                                    canvas_path: str,
                                    node_id: Optional[str] = None,
                                    limit: int = 10) -> List[Dict[str, Any]]:
        """获取Canvas相关的记忆上下文"""
        if not self.memory_enabled or not self.unified_memory:
            return []

        try:
            canvas_id = Path(canvas_path).stem
            memories = self.unified_memory.retrieve_contextual_memory(
                canvas_id=canvas_id,
                node_id=node_id,
                limit=limit
            )
            return [memory.to_dict() for memory in memories]
        except Exception as e:
            print(f"获取记忆上下文失败: {e}")
            return []

    def search_canvas_memories(self,
                              canvas_path: str,
                              query: str,
                              search_type: str = "all",
                              limit: int = 10) -> List[Dict[str, Any]]:
        """搜索Canvas相关的记忆"""
        if not self.memory_enabled or not self.unified_memory:
            return []

        try:
            canvas_id = Path(canvas_path).stem
            # 限定搜索范围为特定Canvas
            context_filter = {"canvas_id": canvas_id}

            results = self.unified_memory.search_memories(
                query=query,
                search_type=search_type,
                limit=limit
            )

            # 过滤结果
            filtered_results = []
            for result in results:
                if "canvas_id" in str(result.get("memory", {})):
                    if canvas_id in str(result["memory"]):
                        filtered_results.append(result)

            return filtered_results
        except Exception as e:
            print(f"搜索Canvas记忆失败: {e}")
            return []

    def run_consistency_check(self) -> Optional[Dict[str, Any]]:
        """运行一致性检查"""
        if not self.memory_enabled or not self.consistency_validator or not self.unified_memory:
            return None

        try:
            report = self.consistency_validator.validate_memory_consistency(
                memory_entries=self.unified_memory.memory_entries,
                memory_links=self.unified_memory.memory_links
            )
            return report.to_dict()
        except Exception as e:
            print(f"一致性检查失败: {e}")
            return None

    def get_memory_system_status(self) -> Dict[str, Any]:
        """获取记忆系统状态"""
        status = {
            "memory_enabled": self.memory_enabled,
            "components": {}
        }

        if self.unified_memory:
            status["components"]["unified_memory"] = self.unified_memory.get_status()

        if self.temporal_manager:
            status["components"]["temporal_manager"] = self.temporal_manager.get_status()

        if self.semantic_manager:
            status["components"]["semantic_manager"] = self.semantic_manager.get_status()

        if self.degradation_manager:
            status["components"]["degradation_manager"] = self.degradation_manager.get_system_status()

        return status

    def cleanup(self):
        """清理资源"""
        try:
            if self.degradation_manager:
                self.degradation_manager.stop_monitoring()

            if self.unified_memory:
                self.unified_memory.cleanup()

            if self.temporal_manager:
                self.temporal_manager.cleanup()

            if self.semantic_manager:
                self.semantic_manager.cleanup()

            print("Canvas记忆系统集成资源清理完成")

        except Exception as e:
            print(f"资源清理失败: {e}")


class EnhancedCanvasOrchestrator(CanvasOrchestrator):
    """增强的Canvas编排器

    扩展现有CanvasOrchestrator，添加记忆系统集成功能。
    """

    def __init__(self, canvas_path: str, memory_integration: CanvasMemoryIntegration):
        """初始化增强的Canvas编排器"""
        super().__init__(canvas_path)
        self.memory_integration = memory_integration
        self.canvas_id = Path(canvas_path).stem

    def add_node_with_memory(self,
                           node_type: str,
                           content: str,
                           node_color: str = "1",
                           metadata: Optional[Dict[str, Any]] = None,
                           record_interaction: bool = True) -> str:
        """添加节点并记录到记忆系统"""
        # 调用原始方法添加节点
        node_id = self.add_node(node_type, content, node_color, metadata)

        # 记录到记忆系统
        if record_interaction and self.memory_integration.memory_enabled:
            self.memory_integration.record_canvas_interaction(
                canvas_path=self.canvas_path,
                node_id=node_id,
                interaction_type="node_creation",
                content=content,
                learning_state="yellow",  # 新创建的节点默认为需要学习状态
                confidence_score=0.3,
                metadata={
                    "node_type": node_type,
                    "node_color": node_color,
                    **(metadata or {})
                }
            )

        return node_id

    def edit_node_with_memory(self,
                            node_id: str,
                            new_content: str,
                            metadata: Optional[Dict[str, Any]] = None,
                            record_interaction: bool = True) -> bool:
        """编辑节点并记录到记忆系统"""
        # 获取当前节点内容
        current_node = self.find_node_by_id(node_id)
        old_content = current_node.get("content", "") if current_node else ""

        # 调用原始方法编辑节点
        success = self.edit_node(node_id, new_content, metadata)

        # 记录到记忆系统
        if record_interaction and success and self.memory_integration.memory_enabled:
            self.memory_integration.record_canvas_interaction(
                canvas_path=self.canvas_path,
                node_id=node_id,
                interaction_type="node_edit",
                content=new_content,
                learning_state="yellow",  # 编辑后的节点需要重新学习
                confidence_score=0.5,
                metadata={
                    "old_content": old_content,
                    "new_content": new_content,
                    **(metadata or {})
                }
            )

        return success

    def score_node_with_memory(self,
                             node_id: str,
                             score: float,
                             feedback: str = "",
                             record_interaction: bool = True) -> bool:
        """评分节点并记录到记忆系统"""
        # 调用原始方法评分节点
        success = self.score_node(node_id, score, feedback)

        # 记录到记忆系统
        if record_interaction and success and self.memory_integration.memory_enabled:
            # 获取节点内容
            node = self.find_node_by_id(node_id)
            content = node.get("content", "") if node else ""

            # 根据分数推断学习状态
            if score >= 80:
                learning_state = "green"
            elif score >= 60:
                learning_state = "purple"
            elif score >= 40:
                learning_state = "yellow"
            else:
                learning_state = "red"

            self.memory_integration.record_canvas_interaction(
                canvas_path=self.canvas_path,
                node_id=node_id,
                interaction_type="node_scoring",
                content=content,
                learning_state=learning_state,
                confidence_score=score / 100.0,
                metadata={
                    "score": score,
                    "feedback": feedback
                }
            )

        return success

    def get_memory_context_for_node(self, node_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """获取节点相关的记忆上下文"""
        if not self.memory_integration.memory_enabled:
            return []

        return self.memory_integration.get_memory_context_for_canvas(
            canvas_path=self.canvas_path,
            node_id=node_id,
            limit=limit
        )

    def search_related_memories(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """搜索相关记忆"""
        if not self.memory_integration.memory_enabled:
            return []

        return self.memory_integration.search_canvas_memories(
            canvas_path=self.canvas_path,
            query=query,
            limit=limit
        )

    def get_memory_enhanced_node_summary(self, node_id: str) -> Dict[str, Any]:
        """获取记忆增强的节点摘要"""
        # 获取基本节点信息
        node = self.find_node_by_id(node_id)
        if not node:
            return {"error": "Node not found"}

        summary = {
            "node_id": node_id,
            "content": node.get("content", ""),
            "color": node.get("color", ""),
            "type": node.get("type", ""),
            "memory_context": [],
            "related_memories": []
        }

        # 添加记忆上下文
        if self.memory_integration.memory_enabled:
            summary["memory_context"] = self.get_memory_context_for_node(node_id)
            summary["related_memories"] = self.search_related_memories(
                node.get("content", "")[:100],  # 使用前100个字符作为查询
                limit=5
            )

        return summary


# 便捷函数
def create_canvas_memory_integration(config_path: Optional[str] = None) -> CanvasMemoryIntegration:
    """创建Canvas记忆系统集成的便捷函数"""
    return CanvasMemoryIntegration(config_path)


def create_enhanced_canvas_orchestrator(canvas_path: str,
                                       config_path: Optional[str] = None) -> EnhancedCanvasOrchestrator:
    """创建增强Canvas编排器的便捷函数"""
    memory_integration = create_canvas_memory_integration(config_path)
    return memory_integration.create_enhanced_canvas_orchestrator(canvas_path)


# 向后兼容性包装器
class BackwardCompatibleCanvas:
    """向后兼容的Canvas包装器

    为现有代码提供向后兼容性，同时添加新的记忆功能。
    """

    def __init__(self, canvas_path: str, enable_memory: bool = True, config_path: Optional[str] = None):
        """初始化向后兼容Canvas"""
        self.canvas_path = canvas_path
        self.enable_memory = enable_memory

        # 初始化传统Canvas操作
        self.orchestrator = CanvasOrchestrator(canvas_path)

        # 初始化记忆系统（如果启用）
        self.memory_integration = None
        self.enhanced_orchestrator = None

        if enable_memory:
            self.memory_integration = create_canvas_memory_integration(config_path)
            self.enhanced_orchestrator = self.memory_integration.create_enhanced_canvas_orchestrator(canvas_path)

    def add_node(self, node_type: str, content: str, node_color: str = "1", metadata: Optional[Dict[str, Any]] = None) -> str:
        """添加节点（带记忆功能）"""
        if self.enhanced_orchestrator:
            return self.enhanced_orchestrator.add_node_with_memory(
                node_type, content, node_color, metadata
            )
        else:
            return self.orchestrator.add_node(node_type, content, node_color, metadata)

    def edit_node(self, node_id: str, new_content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """编辑节点（带记忆功能）"""
        if self.enhanced_orchestrator:
            return self.enhanced_orchestrator.edit_node_with_memory(
                node_id, new_content, metadata
            )
        else:
            return self.orchestrator.edit_node(node_id, new_content, metadata)

    def score_node(self, node_id: str, score: float, feedback: str = "") -> bool:
        """评分节点（带记忆功能）"""
        if self.enhanced_orchestrator:
            return self.enhanced_orchestrator.score_node_with_memory(
                node_id, score, feedback
            )
        else:
            return self.orchestrator.score_node(node_id, score, feedback)

    def get_memory_context(self, node_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """获取记忆上下文（新功能）"""
        if self.enhanced_orchestrator:
            return self.enhanced_orchestrator.get_memory_context_for_node(node_id, limit)
        return []

    def search_memories(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """搜索记忆（新功能）"""
        if self.enhanced_orchestrator:
            return self.enhanced_orchestrator.search_related_memories(query, limit)
        return []

    def get_memory_status(self) -> Dict[str, Any]:
        """获取记忆系统状态（新功能）"""
        if self.memory_integration:
            return self.memory_integration.get_memory_system_status()
        return {"memory_enabled": False}

    # 代理所有其他方法到原始orchestrator
    def __getattr__(self, name):
        """代理其他方法到原始orchestrator"""
        return getattr(self.orchestrator, name)


# 测试用例
if __name__ == "__main__":
    # 测试Canvas记忆系统集成
    try:
        # 创建集成实例
        integration = create_canvas_memory_integration()

        # 创建增强的Canvas编排器
        enhanced_orchestrator = create_enhanced_canvas_orchestrator("test_canvas.canvas")

        # 测试添加节点（带记忆记录）
        node_id = enhanced_orchestrator.add_node_with_memory(
            node_type="text",
            content="这是一个测试节点，用于验证记忆系统集成。",
            node_color="1"
        )
        print(f"添加节点: {node_id}")

        # 测试获取记忆上下文
        context = enhanced_orchestrator.get_memory_context_for_node(node_id)
        print(f"记忆上下文: {len(context)} 条记录")

        # 测试搜索相关记忆
        memories = enhanced_orchestrator.search_related_memories("测试")
        print(f"搜索到 {len(memories)} 条相关记忆")

        # 测试向后兼容包装器
        compatible_canvas = BackwardCompatibleCanvas("test_canvas.canvas")
        node_id2 = compatible_canvas.add_node("text", "向后兼容测试")
        print(f"兼容模式添加节点: {node_id2}")

        # 清理资源
        integration.cleanup()

    except Exception as e:
        print(f"Canvas记忆系统集成测试失败: {e}")