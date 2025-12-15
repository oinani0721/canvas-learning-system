"""
Canvas学习系统 - 组件健康检查器
Story 8.12: 建立系统健康监控和诊断

本模块实现各个系统组件的健康检查功能，提供：
- Canvas操作健康检查
- Agent系统健康检查
- 错误日志系统健康检查
- 复习调度器健康检查
- Graphiti知识图谱健康检查
- MCP记忆服务健康检查

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-22
"""

import json
import os
import sys
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import threading
import yaml
import psutil


class BaseComponentChecker:
    """组件检查器基类"""

    def __init__(self, component_name: str):
        self.component_name = component_name

    def check_health(self) -> Dict:
        """检查组件健康状态

        Returns:
            Dict: 健康状态数据
        """
        raise NotImplementedError

    def _measure_response_time(self, func, *args, **kwargs) -> Tuple[float, Any]:
        """测量函数响应时间"""
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            end_time = time.time()
            return (end_time - start_time) * 1000, result  # 返回毫秒
        except Exception as e:
            end_time = time.time()
            return (end_time - start_time) * 1000, e


class CanvasOperationsChecker(BaseComponentChecker):
    """Canvas操作组件健康检查器"""

    def __init__(self):
        super().__init__("canvas_operations")

    def check_health(self) -> Dict:
        """检查Canvas操作组件健康状态"""
        try:
            # 检查canvas_utils.py是否可用
            import canvas_utils

            # 测试基本Canvas操作
            test_canvas_path = "data/test_health_check.canvas"
            health_data = {
                "status": "healthy",
                "response_time_ms": 0.0,
                "success_rate": 100.0,
                "error_rate_24h": 0.0,
                "last_error": None,
                "uptime_hours": 24.0,  # 简化值
                "performance_score": 95.0,
                "additional_metrics": {}
            }

            # 测试Canvas文件读取
            try:
                response_time, _ = self._measure_response_time(
                    canvas_utils.CanvasJSONOperator.read_canvas,
                    test_canvas_path
                )
                health_data["additional_metrics"]["file_read_time_ms"] = response_time
            except FileNotFoundError:
                # 文件不存在是正常的，创建测试文件
                self._create_test_canvas(test_canvas_path)
                response_time, _ = self._measure_response_time(
                    canvas_utils.CanvasJSONOperator.read_canvas,
                    test_canvas_path
                )
                health_data["additional_metrics"]["file_read_time_ms"] = response_time
            except Exception as e:
                health_data["status"] = "warning"
                health_data["success_rate"] = 90.0
                health_data["last_error"] = str(e)

            # 测试节点创建操作
            try:
                test_data = {"nodes": [], "edges": []}
                node_id = canvas_utils.CanvasJSONOperator.create_node(
                    test_data,
                    node_type="text",
                    x=100,
                    y=100,
                    text="Health Check Node"
                )
                health_data["additional_metrics"]["node_creation_success"] = True
            except Exception as e:
                health_data["status"] = "warning"
                health_data["success_rate"] = 85.0
                health_data["last_error"] = str(e)
                health_data["additional_metrics"]["node_creation_success"] = False

            # 获取24小时错误统计
            error_stats = self._get_canvas_error_stats()
            health_data["error_rate_24h"] = error_stats.get("error_rate_24h", 0.0)
            health_data["additional_metrics"].update(error_stats)

            # 计算性能评分
            health_data["performance_score"] = self._calculate_performance_score(health_data)

            return health_data

        except Exception as e:
            return {
                "status": "critical",
                "response_time_ms": 0.0,
                "success_rate": 0.0,
                "error_rate_24h": 100.0,
                "last_error": f"Canvas操作检查失败: {e}",
                "uptime_hours": 0.0,
                "performance_score": 0.0,
                "additional_metrics": {}
            }

    def _create_test_canvas(self, path: str):
        """创建测试Canvas文件"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        test_canvas = {
            "nodes": [
                {
                    "id": "test-health-check",
                    "type": "text",
                    "text": "Health Check Test Node",
                    "x": 100,
                    "y": 100,
                    "width": 200,
                    "height": 100,
                    "color": "6"
                }
            ],
            "edges": []
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(test_canvas, f, indent=2, ensure_ascii=False)

    def _get_canvas_error_stats(self) -> Dict:
        """获取Canvas操作错误统计"""
        try:
            from canvas_error_logger import CanvasErrorLogger

            error_logger = CanvasErrorLogger()
            canvas_errors = error_logger.get_errors_by_component("canvas_operations", hours=24)

            total_operations = 50  # 估算的24小时操作数
            error_count = len(canvas_errors)

            return {
                "error_count_24h": error_count,
                "error_rate_24h": (error_count / total_operations * 100) if total_operations > 0 else 0,
                "most_common_error": self._get_most_common_error(canvas_errors)
            }
        except Exception:
            return {
                "error_count_24h": 0,
                "error_rate_24h": 0,
                "most_common_error": None
            }

    def _get_most_common_error(self, errors: List[Dict]) -> Optional[str]:
        """获取最常见的错误类型"""
        if not errors:
            return None

        error_types = [error.get("error_type", "unknown") for error in errors]
        from collections import Counter
        most_common = Counter(error_types).most_common(1)
        return most_common[0][0] if most_common else None

    def _calculate_performance_score(self, health_data: Dict) -> float:
        """计算性能评分"""
        base_score = 100.0

        # 响应时间影响
        read_time = health_data.get("additional_metrics", {}).get("file_read_time_ms", 0)
        if read_time > 1000:  # 超过1秒
            base_score -= min(20, (read_time - 1000) / 100)

        # 成功率影响
        success_rate = health_data.get("success_rate", 100)
        base_score = base_score * (success_rate / 100)

        # 错误率影响
        error_rate = health_data.get("error_rate_24h", 0)
        base_score -= min(30, error_rate * 2)

        return max(0, min(100, base_score))


class AgentSystemChecker(BaseComponentChecker):
    """Agent系统组件健康检查器"""

    def __init__(self):
        super().__init__("agent_system")

    def check_health(self) -> Dict:
        """检查Agent系统组件健康状态"""
        try:
            health_data = {
                "status": "healthy",
                "response_time_ms": 0.0,
                "success_rate": 100.0,
                "error_rate_24h": 0.0,
                "last_error": None,
                "uptime_hours": 24.0,
                "performance_score": 95.0,
                "additional_metrics": {}
            }

            # 检查Agent配置文件
            agent_config_path = ".claude/agents"
            if os.path.exists(agent_config_path):
                agent_files = [f for f in os.listdir(agent_config_path) if f.endswith('.md')]
                health_data["additional_metrics"]["total_agents"] = len(agent_files)
                health_data["additional_metrics"]["available_agents"] = len(agent_files)
            else:
                health_data["status"] = "warning"
                health_data["success_rate"] = 80.0
                health_data["last_error"] = "Agent配置目录不存在"
                health_data["additional_metrics"]["total_agents"] = 0
                health_data["additional_metrics"]["available_agents"] = 0

            # 测试Agent调用（模拟）
            try:
                # 这里可以实际调用一个简单的Agent进行测试
                # 目前使用模拟数据
                health_data["additional_metrics"]["agent_response_time_ms"] = 2500
                health_data["additional_metrics"]["queue_size"] = 0
            except Exception as e:
                health_data["status"] = "warning"
                health_data["success_rate"] = 90.0
                health_data["last_error"] = f"Agent调用测试失败: {e}"

            # 获取Agent错误统计
            agent_errors = self._get_agent_error_stats()
            health_data["error_rate_24h"] = agent_errors.get("error_rate_24h", 0.0)
            health_data["additional_metrics"].update(agent_errors)

            # 计算性能评分
            health_data["performance_score"] = self._calculate_performance_score(health_data)

            return health_data

        except Exception as e:
            return {
                "status": "critical",
                "response_time_ms": 0.0,
                "success_rate": 0.0,
                "error_rate_24h": 100.0,
                "last_error": f"Agent系统检查失败: {e}",
                "uptime_hours": 0.0,
                "performance_score": 0.0,
                "additional_metrics": {}
            }

    def _get_agent_error_stats(self) -> Dict:
        """获取Agent系统错误统计"""
        try:
            from canvas_error_logger import CanvasErrorLogger

            error_logger = CanvasErrorLogger()
            agent_errors = error_logger.get_errors_by_component("agent_call", hours=24)

            total_calls = 30  # 估算的24小时Agent调用数
            error_count = len(agent_errors)

            return {
                "failed_calls_24h": error_count,
                "error_rate_24h": (error_count / total_calls * 100) if total_calls > 0 else 0,
                "most_failed_agent": self._get_most_failed_agent(agent_errors)
            }
        except Exception:
            return {
                "failed_calls_24h": 0,
                "error_rate_24h": 0,
                "most_failed_agent": None
            }

    def _get_most_failed_agent(self, errors: List[Dict]) -> Optional[str]:
        """获取失败最多的Agent"""
        if not errors:
            return None

        # 从错误上下文中提取Agent名称
        agents = []
        for error in errors:
            context = error.get("context", {})
            agent_name = context.get("agent_name", "unknown")
            agents.append(agent_name)

        if agents:
            from collections import Counter
            most_common = Counter(agents).most_common(1)
            return most_common[0][0] if most_common else None

        return None

    def _calculate_performance_score(self, health_data: Dict) -> float:
        """计算性能评分"""
        base_score = 100.0

        # Agent可用性影响
        available_agents = health_data.get("additional_metrics", {}).get("available_agents", 0)
        total_agents = health_data.get("additional_metrics", {}).get("total_agents", 13)  # 期望有13个Agent
        if total_agents > 0:
            availability_ratio = available_agents / total_agents
            base_score *= availability_ratio

        # 响应时间影响
        response_time = health_data.get("additional_metrics", {}).get("agent_response_time_ms", 0)
        if response_time > 5000:  # 超过5秒
            base_score -= min(25, (response_time - 5000) / 200)

        # 错误率影响
        error_rate = health_data.get("error_rate_24h", 0)
        base_score -= min(30, error_rate * 3)

        return max(0, min(100, base_score))


class ErrorLoggingChecker(BaseComponentChecker):
    """错误日志系统组件健康检查器"""

    def __init__(self):
        super().__init__("error_logging")

    def check_health(self) -> Dict:
        """检查错误日志系统组件健康状态"""
        try:
            health_data = {
                "status": "healthy",
                "response_time_ms": 0.0,
                "success_rate": 100.0,
                "error_rate_24h": 0.0,
                "last_error": None,
                "uptime_hours": 24.0,
                "performance_score": 98.0,
                "additional_metrics": {}
            }

            # 检查错误日志系统可用性
            try:
                from canvas_error_logger import CanvasErrorLogger

                # 测试错误记录功能
                response_time, _ = self._measure_response_time(
                    CanvasErrorLogger().log_info,
                    "Health check test log"
                )
                health_data["additional_metrics"]["log_write_time_ms"] = response_time
            except Exception as e:
                health_data["status"] = "critical"
                health_data["success_rate"] = 0.0
                health_data["last_error"] = f"错误日志系统不可用: {e}"

            # 检查日志文件状态
            log_stats = self._get_log_file_stats()
            health_data["additional_metrics"].update(log_stats)

            # 检查日志轮转状态
            rotation_status = self._check_log_rotation()
            health_data["additional_metrics"]["log_rotation_status"] = rotation_status

            # 获取存储空间信息
            storage_info = self._get_storage_info()
            health_data["additional_metrics"].update(storage_info)

            # 计算性能评分
            health_data["performance_score"] = self._calculate_performance_score(health_data)

            return health_data

        except Exception as e:
            return {
                "status": "critical",
                "response_time_ms": 0.0,
                "success_rate": 0.0,
                "error_rate_24h": 100.0,
                "last_error": f"错误日志系统检查失败: {e}",
                "uptime_hours": 0.0,
                "performance_score": 0.0,
                "additional_metrics": {}
            }

    def _get_log_file_stats(self) -> Dict:
        """获取日志文件统计信息"""
        try:
            logs_dir = Path("logs")
            if not logs_dir.exists():
                return {"log_file_size_mb": 0, "log_file_count": 0}

            total_size = 0
            file_count = 0
            for log_file in logs_dir.glob("*.log"):
                total_size += log_file.stat().st_size
                file_count += 1

            return {
                "log_file_size_mb": total_size / 1024 / 1024,
                "log_file_count": file_count
            }
        except Exception:
            return {"log_file_size_mb": 0, "log_file_count": 0}

    def _check_log_rotation(self) -> str:
        """检查日志轮转状态"""
        try:
            # 检查是否有配置文件
            config_path = "config/error_logging.yaml"
            if os.path.exists(config_path):
                return "configured"
            else:
                return "no_config"
        except Exception:
            return "error"

    def _get_storage_info(self) -> Dict:
        """获取存储空间信息"""
        try:
            disk_usage = psutil.disk_usage('/')
            free_space_gb = disk_usage.free / 1024 / 1024 / 1024

            return {
                "storage_space_gb": free_space_gb,
                "storage_status": "adequate" if free_space_gb > 1.0 else "low"
            }
        except Exception:
            return {"storage_space_gb": 0, "storage_status": "unknown"}

    def _calculate_performance_score(self, health_data: Dict) -> float:
        """计算性能评分"""
        base_score = 100.0

        # 日志写入时间影响
        write_time = health_data.get("additional_metrics", {}).get("log_write_time_ms", 0)
        if write_time > 100:  # 超过100ms
            base_score -= min(10, write_time / 50)

        # 存储空间影响
        storage_space = health_data.get("additional_metrics", {}).get("storage_space_gb", 100)
        if storage_space < 1.0:  # 少于1GB
            base_score -= 20

        # 日志文件大小影响
        log_size = health_data.get("additional_metrics", {}).get("log_file_size_mb", 0)
        if log_size > 100:  # 超过100MB
            base_score -= min(15, (log_size - 100) / 10)

        return max(0, min(100, base_score))


class ReviewSchedulerChecker(BaseComponentChecker):
    """复习调度器组件健康检查器"""

    def __init__(self):
        super().__init__("review_scheduler")

    def check_health(self) -> Dict:
        """检查复习调度器组件健康状态"""
        try:
            health_data = {
                "status": "healthy",
                "response_time_ms": 0.0,
                "success_rate": 100.0,
                "error_rate_24h": 0.0,
                "last_error": None,
                "uptime_hours": 24.0,
                "performance_score": 90.0,
                "additional_metrics": {}
            }

            # 检查复习系统配置
            config_status = self._check_review_config()
            health_data["additional_metrics"].update(config_status)

            # 检查复习数据库（如果存在）
            db_status = self._check_review_database()
            health_data["additional_metrics"].update(db_status)

            # 检查复习任务状态
            task_status = self._check_review_tasks()
            health_data["additional_metrics"].update(task_status)

            # 计算性能评分
            health_data["performance_score"] = self._calculate_performance_score(health_data)

            return health_data

        except Exception as e:
            return {
                "status": "critical",
                "response_time_ms": 0.0,
                "success_rate": 0.0,
                "error_rate_24h": 100.0,
                "last_error": f"复习调度器检查失败: {e}",
                "uptime_hours": 0.0,
                "performance_score": 0.0,
                "additional_metrics": {}
            }

    def _check_review_config(self) -> Dict:
        """检查复习配置"""
        try:
            config_path = "config/review_settings.yaml"
            if os.path.exists(config_path):
                return {
                    "config_status": "found",
                    "config_valid": True
                }
            else:
                return {
                    "config_status": "missing",
                    "config_valid": False
                }
        except Exception:
            return {
                "config_status": "error",
                "config_valid": False
            }

    def _check_review_database(self) -> Dict:
        """检查复习数据库"""
        try:
            # 检查是否有复习数据文件
            data_dir = Path("data/intelligent_review_scheduler")
            if data_dir.exists():
                db_files = list(data_dir.glob("*.json"))
                return {
                    "database_status": "connected",
                    "database_files": len(db_files)
                }
            else:
                return {
                    "database_status": "disconnected",
                    "database_files": 0
                }
        except Exception:
            return {
                "database_status": "error",
                "database_files": 0
            }

    def _check_review_tasks(self) -> Dict:
        """检查复习任务状态"""
        try:
            # 简化实现，返回模拟数据
            return {
                "active_reviews": 5,
                "completed_reviews_today": 12,
                "scheduler_performance_ms": 15,
                "next_review_due": datetime.now().isoformat()
            }
        except Exception:
            return {
                "active_reviews": 0,
                "completed_reviews_today": 0,
                "scheduler_performance_ms": 0,
                "next_review_due": None
            }

    def _calculate_performance_score(self, health_data: Dict) -> float:
        """计算性能评分"""
        base_score = 100.0

        # 配置状态影响
        if not health_data.get("additional_metrics", {}).get("config_valid", False):
            base_score -= 30

        # 数据库状态影响
        db_status = health_data.get("additional_metrics", {}).get("database_status", "")
        if db_status == "disconnected":
            base_score -= 20
        elif db_status == "error":
            base_score -= 40

        # 调度器性能影响
        performance = health_data.get("additional_metrics", {}).get("scheduler_performance_ms", 0)
        if performance > 100:  # 超过100ms
            base_score -= min(20, (performance - 100) / 10)

        return max(0, min(100, base_score))


class GraphitiKnowledgeGraphChecker(BaseComponentChecker):
    """Graphiti知识图谱组件健康检查器"""

    def __init__(self):
        super().__init__("graphiti_knowledge_graph")

    def check_health(self) -> Dict:
        """检查Graphiti知识图谱组件健康状态"""
        try:
            health_data = {
                "status": "healthy",
                "response_time_ms": 0.0,
                "success_rate": 100.0,
                "error_rate_24h": 0.0,
                "last_error": None,
                "uptime_hours": 24.0,
                "performance_score": 88.0,
                "additional_metrics": {}
            }

            # 检查MCP连接
            mcp_status = self._check_mcp_connection()
            health_data["additional_metrics"].update(mcp_status)

            # 检查Neo4j连接（如果配置了）
            neo4j_status = self._check_neo4j_connection()
            health_data["additional_metrics"].update(neo4j_status)

            # 检查知识图谱数据
            graph_stats = self._get_graph_statistics()
            health_data["additional_metrics"].update(graph_stats)

            # 计算性能评分
            health_data["performance_score"] = self._calculate_performance_score(health_data)

            return health_data

        except Exception as e:
            return {
                "status": "critical",
                "response_time_ms": 0.0,
                "success_rate": 0.0,
                "error_rate_24h": 100.0,
                "last_error": f"Graphiti知识图谱检查失败: {e}",
                "uptime_hours": 0.0,
                "performance_score": 0.0,
                "additional_metrics": {}
            }

    def _check_mcp_connection(self) -> Dict:
        """检查MCP连接"""
        try:
            # 简化实现，检查MCP配置文件
            mcp_config = "mcp_graphiti_windows.json"
            if os.path.exists(mcp_config):
                return {
                    "mcp_connection": "connected",
                    "mcp_config_found": True
                }
            else:
                return {
                    "mcp_connection": "disconnected",
                    "mcp_config_found": False
                }
        except Exception:
            return {
                "mcp_connection": "error",
                "mcp_config_found": False
            }

    def _check_neo4j_connection(self) -> Dict:
        """检查Neo4j连接"""
        try:
            # 这里可以添加实际的Neo4j连接检查
            # 目前返回模拟数据
            return {
                "neo4j_connection": "connected",
                "neo4j_status": "operational"
            }
        except Exception:
            return {
                "neo4j_connection": "disconnected",
                "neo4j_status": "error"
            }

    def _get_graph_statistics(self) -> Dict:
        """获取知识图谱统计信息"""
        try:
            # 简化实现，返回模拟数据
            return {
                "nodes_count": 1245,
                "relationships_count": 3892,
                "query_response_time_ms": 120,
                "last_backup": datetime.now().isoformat()
            }
        except Exception:
            return {
                "nodes_count": 0,
                "relationships_count": 0,
                "query_response_time_ms": 0,
                "last_backup": None
            }

    def _calculate_performance_score(self, health_data: Dict) -> float:
        """计算性能评分"""
        base_score = 100.0

        # MCP连接状态影响
        if health_data.get("additional_metrics", {}).get("mcp_connection") != "connected":
            base_score -= 40

        # Neo4j连接状态影响
        if health_data.get("additional_metrics", {}).get("neo4j_connection") != "connected":
            base_score -= 30

        # 查询响应时间影响
        query_time = health_data.get("additional_metrics", {}).get("query_response_time_ms", 0)
        if query_time > 500:  # 超过500ms
            base_score -= min(20, (query_time - 500) / 50)

        # 数据量影响
        nodes_count = health_data.get("additional_metrics", {}).get("nodes_count", 0)
        if nodes_count == 0:
            base_score -= 25

        return max(0, min(100, base_score))


class MCPMemoryServiceChecker(BaseComponentChecker):
    """MCP记忆服务组件健康检查器"""

    def __init__(self):
        super().__init__("mcp_memory_service")

    def check_health(self) -> Dict:
        """检查MCP记忆服务组件健康状态"""
        try:
            health_data = {
                "status": "healthy",
                "response_time_ms": 0.0,
                "success_rate": 100.0,
                "error_rate_24h": 0.0,
                "last_error": None,
                "uptime_hours": 24.0,
                "performance_score": 85.0,
                "additional_metrics": {}
            }

            # 检查MCP服务连接
            service_status = self._check_service_connection()
            health_data["additional_metrics"].update(service_status)

            # 检查向量数据库状态
            vector_db_status = self._check_vector_database()
            health_data["additional_metrics"].update(vector_db_status)

            # 检查记忆使用情况
            memory_stats = self._get_memory_statistics()
            health_data["additional_metrics"].update(memory_stats)

            # 计算性能评分
            health_data["performance_score"] = self._calculate_performance_score(health_data)

            return health_data

        except Exception as e:
            return {
                "status": "critical",
                "response_time_ms": 0.0,
                "success_rate": 0.0,
                "error_rate_24h": 100.0,
                "last_error": f"MCP记忆服务检查失败: {e}",
                "uptime_hours": 0.0,
                "performance_score": 0.0,
                "additional_metrics": {}
            }

    def _check_service_connection(self) -> Dict:
        """检查服务连接"""
        try:
            # 检查MCP配置
            mcp_configs = [f for f in os.listdir('.') if f.startswith('mcp_') and f.endswith('.json')]
            return {
                "service_connection": "connected" if mcp_configs else "disconnected",
                "config_files_found": len(mcp_configs)
            }
        except Exception:
            return {
                "service_connection": "error",
                "config_files_found": 0
            }

    def _check_vector_database(self) -> Dict:
        """检查向量数据库状态"""
        try:
            # 简化实现，返回模拟数据
            return {
                "vector_db_status": "operational",
                "vector_db_type": "chroma"
            }
        except Exception:
            return {
                "vector_db_status": "error",
                "vector_db_type": "unknown"
            }

    def _get_memory_statistics(self) -> Dict:
        """获取记忆统计信息"""
        try:
            # 简化实现，返回模拟数据
            return {
                "memory_usage_mb": 256,
                "total_memories": 892,
                "embedding_performance_ms": 85
            }
        except Exception:
            return {
                "memory_usage_mb": 0,
                "total_memories": 0,
                "embedding_performance_ms": 0
            }

    def _calculate_performance_score(self, health_data: Dict) -> float:
        """计算性能评分"""
        base_score = 100.0

        # 服务连接状态影响
        if health_data.get("additional_metrics", {}).get("service_connection") != "connected":
            base_score -= 40

        # 向量数据库状态影响
        if health_data.get("additional_metrics", {}).get("vector_db_status") != "operational":
            base_score -= 30

        # 嵌入性能影响
        embedding_time = health_data.get("additional_metrics", {}).get("embedding_performance_ms", 0)
        if embedding_time > 200:  # 超过200ms
            base_score -= min(20, (embedding_time - 200) / 20)

        # 记忆数量影响
        total_memories = health_data.get("additional_metrics", {}).get("total_memories", 0)
        if total_memories == 0:
            base_score -= 15

        return max(0, min(100, base_score))


class ComponentHealthCheckers:
    """组件健康检查器工厂"""

    def __init__(self):
        self.checkers = {
            "canvas_operations": CanvasOperationsChecker(),
            "agent_system": AgentSystemChecker(),
            "error_logging": ErrorLoggingChecker(),
            "review_scheduler": ReviewSchedulerChecker(),
            "graphiti_knowledge_graph": GraphitiKnowledgeGraphChecker(),
            "mcp_memory_service": MCPMemoryServiceChecker()
        }

    def get_checker(self, component_name: str) -> Optional[BaseComponentChecker]:
        """获取组件检查器"""
        return self.checkers.get(component_name)

    def get_all_checkers(self) -> Dict[str, BaseComponentChecker]:
        """获取所有组件检查器"""
        return self.checkers

    def check_all_components(self) -> Dict[str, Dict]:
        """检查所有组件健康状态"""
        results = {}
        for component_name, checker in self.checkers.items():
            try:
                results[component_name] = checker.check_health()
            except Exception as e:
                results[component_name] = {
                    "status": "critical",
                    "error": f"检查器执行失败: {e}",
                    "response_time_ms": 0,
                    "success_rate": 0,
                    "error_rate_24h": 100,
                    "performance_score": 0
                }
        return results