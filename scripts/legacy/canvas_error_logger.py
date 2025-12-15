"""
Canvas学习系统 - 专用错误日志记录器
Story 8.11: 集成Canvas专用错误日志系统

本模块实现Canvas专用的结构化错误日志系统，提供：
- Canvas操作错误日志记录
- Agent调用上下文收集
- JSON格式结构化日志输出
- 自动文件轮转和管理
- 错误分类和统计分析
- 智能恢复建议

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-22
"""

import json
import os
import sys
import traceback
import uuid
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import time
import threading
import yaml


class ErrorSeverity(Enum):
    """错误严重性枚举"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class ErrorCategory(Enum):
    """错误分类枚举"""
    FILE_OPERATION = "file_operation"
    AGENT_CALL = "agent_call"
    NODE_OPERATION = "node_operation"
    SYSTEM_ERROR = "system_error"


class CanvasErrorLogger:
    """Canvas专用错误日志记录器"""

    def __init__(self, log_config_path: str = "config/error_logging.yaml"):
        """初始化错误日志记录器

        Args:
            log_config_path: 日志配置文件路径
        """
        self.config = self._load_config(log_config_path)
        self.session_id = str(uuid.uuid4())[:16]
        self.user_id = "default"
        self.operation_sequence = 0
        self.recent_operations = []
        self._lock = threading.Lock()

        # 确保日志目录存在
        log_dir = Path(self.config["file_logging"]["log_file_path"]).parent
        log_dir.mkdir(exist_ok=True)

        # 错误代码映射
        self.error_codes = self.config.get("error_codes", {})

    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f).get("error_logging", {})
        except FileNotFoundError:
            # 返回默认配置
            return {
                "enabled": True,
                "log_level": "INFO",
                "file_logging": {
                    "enabled": True,
                    "log_file_path": "./logs/canvas_errors.log",
                    "max_file_size_mb": 10,
                    "backup_count": 5
                },
                "format": {
                    "use_json": True,
                    "include_stack_trace": True,
                    "include_context": True
                },
                "error_codes": {}
            }

    def _get_error_code(self, category: str, error_type: str) -> str:
        """获取错误代码"""
        return self.error_codes.get(category, {}).get(error_type, f"UNKNOWN_{category}_{error_type}")

    def _assess_severity(self, error: Exception, category: str) -> ErrorSeverity:
        """评估错误严重性"""
        if isinstance(error, (FileNotFoundError, PermissionError)):
            return ErrorSeverity.HIGH
        elif isinstance(error, (ValueError, KeyError)):
            return ErrorSeverity.MEDIUM
        elif isinstance(error, TimeoutError):
            return ErrorSeverity.HIGH
        elif category == "system_error":
            return ErrorSeverity.CRITICAL
        else:
            return ErrorSeverity.LOW

    def _collect_system_context(self) -> Dict:
        """收集系统上下文信息"""
        if not self.config.get("context_collection", {}).get("collect_system_info", True):
            return {}

        base_info = {
            "python_version": sys.version,
            "platform": sys.platform,
            "working_directory": os.getcwd()
        }

        try:
            import psutil
            base_info.update({
                "available_memory_mb": psutil.virtual_memory().available // (1024 * 1024),
                "cpu_usage_percent": psutil.cpu_percent()
            })

            # Windows路径处理
            try:
                disk_path = os.getcwd()
                if isinstance(disk_path, str):
                    # 确保路径格式正确
                    disk_path = os.path.abspath(disk_path)
                    disk_usage = psutil.disk_usage(disk_path)
                    base_info["disk_space_available_gb"] = disk_usage.free // (1024 * 1024 * 1024)
            except (OSError, ValueError, psutil.AccessDenied):
                # 如果获取磁盘信息失败，使用默认值
                base_info["disk_space_available_gb"] = 0

        except ImportError:
            pass
        except Exception:
            # psutil调用失败时忽略，不影响核心功能
            pass

        return base_info

    def _collect_canvas_context(self, canvas_path: str, **kwargs) -> Dict:
        """收集Canvas上下文信息"""
        context = {
            "canvas_file_path": canvas_path
        }

        try:
            if os.path.exists(canvas_path):
                stat = os.stat(canvas_path)
                context.update({
                    "canvas_file_size_bytes": stat.st_size,
                    "canvas_last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })

                # 尝试读取Canvas文件获取节点数量
                try:
                    with open(canvas_path, 'r', encoding='utf-8') as f:
                        canvas_data = json.load(f)
                    context.update({
                        "canvas_node_count": len(canvas_data.get('nodes', [])),
                        "canvas_edge_count": len(canvas_data.get('edges', []))
                    })
                except:
                    pass

            # 添加操作目标信息
            if 'node_id' in kwargs:
                context["operation_target"] = {
                    "node_id": kwargs['node_id'],
                    "node_type": kwargs.get('node_type', 'unknown'),
                    "node_content_preview": kwargs.get('node_content', '')[:100] + "..." if len(kwargs.get('node_content', '')) > 100 else kwargs.get('node_content', '')
                }

        except Exception:
            pass

        return context

    def _collect_agent_context(self, agent_name: str, **kwargs) -> Dict:
        """收集Agent上下文信息"""
        return {
            "agent_name": agent_name,
            "agent_call_id": kwargs.get('call_id', str(uuid.uuid4())[:16]),
            "agent_input_summary": kwargs.get('input_summary', ''),
            "agent_execution_time_ms": kwargs.get('execution_time_ms', 0),
            "agent_error_phase": kwargs.get('error_phase', 'unknown')
        }

    def _collect_performance_metrics(self, start_time: float) -> Dict:
        """收集性能指标"""
        duration_ms = (time.time() - start_time) * 1000

        base_metrics = {
            "operation_duration_ms": round(duration_ms, 2),
            "file_io_bytes": 0,
            "network_requests_count": 0
        }

        try:
            import psutil
            process = psutil.Process()
            base_metrics.update({
                "memory_usage_delta_mb": round(process.memory_info().rss / (1024 * 1024), 2),
                "cpu_usage_delta_percent": process.cpu_percent()
            })
        except (ImportError, psutil.AccessDenied, psutil.NoSuchProcess):
            # psutil不可用或权限不足时使用默认值
            pass
        except Exception:
            # 其他psutil错误时忽略
            pass

        return base_metrics

    def _create_log_entry(self, operation: str, canvas_path: str, context: Dict,
                         status: str = "success", error: Exception = None,
                         start_time: float = None) -> Dict:
        """创建日志条目"""

        # 输入验证和安全检查
        if not isinstance(operation, str) or len(operation) > 100:
            operation = "unknown_operation"

        if not isinstance(canvas_path, str) or len(canvas_path) > 500:
            canvas_path = "unknown_path"

        if not isinstance(context, dict):
            context = {}

        if status not in ["success", "error", "warning", "info"]:
            status = "unknown"

        # 更新操作序列
        with self._lock:
            self.operation_sequence += 1
            seq = self.operation_sequence

        # 记录操作到历史
        operation_record = {
            "operation": operation,
            "timestamp": datetime.now().isoformat(),
            "status": status
        }
        self.recent_operations.append(operation_record)
        if len(self.recent_operations) > 10:
            self.recent_operations.pop(0)

        # 基础日志结构
        log_entry = {
            "canvas_error_log": {
                "log_id": f"log-{str(uuid.uuid4())[:16]}",
                "timestamp": datetime.now().isoformat(),
                "level": status.upper() if status != "success" else "INFO",
                "category": self._get_operation_category(operation),
                "operation_type": operation,
                "status": status,

                # 错误信息
                "error_information": self._create_error_info(error) if error else {},

                # 上下文信息
                "canvas_context": self._collect_canvas_context(canvas_path, **context),
                "agent_context": self._collect_agent_context(context.get('agent_name', ''), **{k: v for k, v in context.items() if k != 'agent_name'}),
                "system_context": self._collect_system_context(),
                "user_context": {
                    "user_id": self.user_id,
                    "session_id": self.session_id,
                    "operation_sequence": seq,
                    "recent_operations": self.recent_operations[-5:]  # 最近5个操作
                },

                # 性能指标
                "performance_metrics": self._collect_performance_metrics(start_time) if start_time else {},

                # 解决信息
                "resolution_info": self._create_resolution_info(error) if error else {}
            }
        }

        return log_entry

    def _get_operation_category(self, operation: str) -> str:
        """获取操作分类"""
        if 'canvas' in operation and ('read' in operation or 'write' in operation):
            return ErrorCategory.FILE_OPERATION.value
        elif 'agent' in operation:
            return ErrorCategory.AGENT_CALL.value
        elif 'node' in operation or 'edge' in operation:
            return ErrorCategory.NODE_OPERATION.value
        elif 'file_operation' in operation:
            return ErrorCategory.FILE_OPERATION.value
        elif 'agent_operation' in operation:
            return ErrorCategory.AGENT_CALL.value
        elif 'system_error' in operation:
            return ErrorCategory.SYSTEM_ERROR.value
        else:
            return ErrorCategory.SYSTEM_ERROR.value

    def _create_error_info(self, error: Exception) -> Dict:
        """创建错误信息"""
        error_type = type(error).__name__
        category = self._get_operation_category('unknown')

        return {
            "error_type": error_type,
            "error_message": str(error),
            "stack_trace": traceback.format_exc() if self.config.get("format", {}).get("include_stack_trace", True) else "",
            "error_code": self._get_error_code(category, error_type.lower()),
            "recovery_suggested": True,
            "recovery_actions": self._get_recovery_actions(error)
        }

    def _get_recovery_actions(self, error: Exception) -> List[str]:
        """获取恢复建议"""
        actions = []
        error_type = type(error).__name__

        if isinstance(error, FileNotFoundError):
            actions = [
                "检查文件路径是否正确",
                "验证文件权限设置",
                "确认文件格式为有效的Canvas格式"
            ]
        elif isinstance(error, PermissionError):
            actions = [
                "检查文件和目录权限",
                "确保有读写权限",
                "尝试以管理员身份运行"
            ]
        elif isinstance(error, json.JSONDecodeError):
            actions = [
                "检查Canvas文件格式是否正确",
                "验证JSON语法",
                "尝试备份文件并重新创建"
            ]
        elif isinstance(error, ValueError):
            actions = [
                "检查输入数据格式",
                "验证参数值的有效性",
                "参考API文档确认正确用法"
            ]
        elif isinstance(error, TimeoutError):
            actions = [
                "增加超时时间设置",
                "检查网络连接",
                "重试操作"
            ]
        else:
            actions = [
                "查看详细错误信息",
                "联系技术支持",
                "记录错误上下文以便调试"
            ]

        return actions

    def _create_resolution_info(self, error: Exception) -> Dict:
        """创建解决信息"""
        return {
            "resolved": False,
            "resolution_timestamp": None,
            "resolution_method": None,
            "prevention_measures": [
                "添加预检查机制",
                "改进错误处理逻辑",
                "增加用户友好的错误提示"
            ]
        }

    def _write_log(self, log_entry: Dict):
        """写入日志文件"""
        if not self.config.get("file_logging", {}).get("enabled", True):
            return

        log_file = self.config["file_logging"]["log_file_path"]

        # 检查文件大小并轮转
        self._check_and_rotate_log()

        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                if self.config.get("format", {}).get("use_json", True):
                    json.dump(log_entry, f, ensure_ascii=False, separators=(',', ':'))
                    f.write('\n')
                else:
                    # 简化格式输出
                    f.write(f"{datetime.now().isoformat()} - {log_entry['canvas_error_log']['level']} - {log_entry['canvas_error_log']['operation_type']}\n")

        except Exception as e:
            # 日志写入失败时的备用方案 - 使用标准logging避免安全风险
            import logging
            logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
            logger = logging.getLogger(__name__)
            logger.error(f"日志写入失败: {e}")
            logger.debug(f"原始日志: {json.dumps(log_entry, ensure_ascii=False, indent=2)}")

    def _check_and_rotate_log(self):
        """检查并轮转日志文件"""
        log_file = self.config["file_logging"]["log_file_path"]
        max_size_mb = self.config["file_logging"].get("max_file_size_mb", 10)
        backup_count = self.config["file_logging"].get("backup_count", 5)

        try:
            if os.path.exists(log_file):
                file_size_mb = os.path.getsize(log_file) / (1024 * 1024)
                if file_size_mb >= max_size_mb:
                    # 轮转日志文件
                    for i in range(backup_count - 1, 0, -1):
                        old_file = f"{log_file}.{i}"
                        new_file = f"{log_file}.{i + 1}"
                        if os.path.exists(old_file):
                            if os.path.exists(new_file):
                                os.remove(new_file)
                            os.rename(old_file, new_file)

                    # 移动当前日志文件
                    backup_file = f"{log_file}.1"
                    if os.path.exists(backup_file):
                        os.remove(backup_file)
                    os.rename(log_file, backup_file)

        except Exception as e:
            # 日志轮转失败时使用标准logging避免安全风险
            import logging
            logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
            logger = logging.getLogger(__name__)
            logger.error(f"日志轮转失败: {e}")

    def log_canvas_operation(self, operation: str, canvas_path: str,
                           context: Dict, status: str = "success",
                           error: Exception = None) -> str:
        """记录Canvas操作日志

        Args:
            operation: 操作类型
            canvas_path: Canvas文件路径
            context: 操作上下文信息
            status: 操作状态 ("success", "error", "warning")
            error: 异常对象(如果有)

        Returns:
            str: 日志记录ID
        """
        if not self.config.get("enabled", True):
            return ""

        # 输入验证必须在访问context属性之前进行
        if not isinstance(context, dict):
            context = {}

        start_time = context.get('start_time')
        log_entry = self._create_log_entry(operation, canvas_path, context, status, error, start_time)

        self._write_log(log_entry)

        return log_entry["canvas_error_log"]["log_id"]

    def log_agent_call(self, agent_name: str, call_id: str,
                      input_data: Dict, execution_time_ms: int,
                      status: str = "success", error: Exception = None) -> str:
        """记录Agent调用日志

        Args:
            agent_name: Agent名称
            call_id: 调用ID
            input_data: 输入数据
            execution_time_ms: 执行时间(毫秒)
            status: 调用状态
            error: 异常对象(如果有)

        Returns:
            str: 日志记录ID
        """
        if not self.config.get("enabled", True):
            return ""

        # 输入验证
        if not isinstance(input_data, dict):
            input_data = {}

        context = {
            "agent_name": agent_name,
            "call_id": call_id,
            "input_summary": str(input_data)[:200] + "..." if len(str(input_data)) > 200 else str(input_data),
            "execution_time_ms": execution_time_ms,
            "error_phase": "response_parsing" if error else "completed"
        }

        operation = f"agent_call_{agent_name}"
        canvas_path = input_data.get('canvas_path', 'unknown')

        return self.log_canvas_operation(operation, canvas_path, context, status, error)

    def get_recent_errors(self, limit: int = 10, severity: str = None) -> List[Dict]:
        """获取最近的错误记录

        Args:
            limit: 返回记录数量限制
            severity: 严重性过滤 (None表示所有级别)

        Returns:
            List[Dict]: 错误记录列表
        """
        log_file = self.config["file_logging"]["log_file_path"]
        errors = []

        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in reversed(f.readlines()):
                    if len(errors) >= limit:
                        break

                    try:
                        log_entry = json.loads(line.strip())
                        log_data = log_entry.get("canvas_error_log", {})

                        # 过滤成功记录
                        if log_data.get("status") == "success":
                            continue

                        # 过滤严重性
                        if severity and log_data.get("severity") != severity:
                            continue

                        errors.append(log_data)

                    except json.JSONDecodeError:
                        continue

        except FileNotFoundError:
            pass

        return errors

    def generate_error_summary(self, period_hours: int = 24) -> Dict:
        """生成错误统计摘要

        Args:
            period_hours: 统计时间范围(小时)

        Returns:
            Dict: 错误摘要报告
        """
        log_file = self.config["file_logging"]["log_file_path"]
        cutoff_time = datetime.now() - timedelta(hours=period_hours)

        summary = {
            "error_summary_report": {
                "report_period": {
                    "start_date": cutoff_time.isoformat(),
                    "end_date": datetime.now().isoformat(),
                    "total_logs_analyzed": 0
                },
                "error_overview": {
                    "total_errors": 0,
                    "total_warnings": 0,
                    "total_info_logs": 0,
                    "error_rate_percentage": 0.0,
                    "most_recent_error": None
                },
                "error_category_breakdown": {},
                "severity_distribution": {},
                "top_error_patterns": [],
                "performance_impact": {
                    "average_error_resolution_time_minutes": 0.0,
                    "total_downtime_minutes": 0.0,
                    "user_experience_impact": "minimal",
                    "system_stability_score": 100.0
                }
            }
        }

        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                total_logs = 0
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        log_data = log_entry.get("canvas_error_log", {})

                        # 检查时间范围
                        log_time = datetime.fromisoformat(log_data.get("timestamp", ""))
                        if log_time < cutoff_time:
                            continue

                        total_logs += 1
                        status = log_data.get("status", "success")
                        severity = log_data.get("severity", "INFO")
                        category = log_data.get("category", "unknown")

                        # 更新总体统计
                        if status == "error":
                            summary["error_summary_report"]["error_overview"]["total_errors"] += 1
                        elif status == "warning":
                            summary["error_summary_report"]["error_overview"]["total_warnings"] += 1
                        else:
                            summary["error_summary_report"]["error_overview"]["total_info_logs"] += 1

                        # 更新分类统计
                        if category not in summary["error_summary_report"]["error_category_breakdown"]:
                            summary["error_summary_report"]["error_category_breakdown"][category] = {
                                "count": 0,
                                "percentage": 0.0,
                                "most_common_error": "",
                                "trend": "stable"
                            }
                        summary["error_summary_report"]["error_category_breakdown"][category]["count"] += 1

                        # 更新严重性分布
                        if severity not in summary["error_summary_report"]["severity_distribution"]:
                            summary["error_summary_report"]["severity_distribution"][severity] = 0
                        summary["error_summary_report"]["severity_distribution"][severity] += 1

                        # 记录最近错误
                        if status == "error" and not summary["error_summary_report"]["error_overview"]["most_recent_error"]:
                            summary["error_summary_report"]["error_overview"]["most_recent_error"] = log_time.isoformat()

                    except json.JSONDecodeError:
                        continue

                summary["error_summary_report"]["report_period"]["total_logs_analyzed"] = total_logs

                # 计算百分比和趋势
                total_operations = total_logs
                if total_operations > 0:
                    total_errors = summary["error_summary_report"]["error_overview"]["total_errors"]
                    summary["error_summary_report"]["error_overview"]["error_rate_percentage"] = round((total_errors / total_operations) * 100, 2)

                    # 计算分类百分比
                    for category, data in summary["error_summary_report"]["error_category_breakdown"].items():
                        data["percentage"] = round((data["count"] / total_errors) * 100, 2) if total_errors > 0 else 0.0

                    # 计算系统稳定性分数
                    stability_score = max(0, 100 - (total_errors / total_operations * 100))
                    summary["error_summary_report"]["performance_impact"]["system_stability_score"] = round(stability_score, 1)

        except FileNotFoundError:
            pass

        return summary

    def search_error_logs(self, query: str, start_time: datetime = None,
                         end_time: datetime = None) -> List[Dict]:
        """搜索错误日志

        Args:
            query: 搜索关键词
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            List[Dict]: 匹配的日志记录
        """
        log_file = self.config["file_logging"]["log_file_path"]
        matches = []

        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        log_data = log_entry.get("canvas_error_log", {})

                        # 时间过滤
                        if start_time or end_time:
                            log_time = datetime.fromisoformat(log_data.get("timestamp", ""))
                            if start_time and log_time < start_time:
                                continue
                            if end_time and log_time > end_time:
                                continue

                        # 关键词搜索
                        log_text = json.dumps(log_data, ensure_ascii=False).lower()
                        if query.lower() in log_text:
                            matches.append(log_data)

                    except json.JSONDecodeError:
                        continue

        except FileNotFoundError:
            pass

        return matches


# 全局错误日志记录器实例
_global_logger = None

def get_canvas_error_logger() -> CanvasErrorLogger:
    """获取全局Canvas错误日志记录器实例"""
    global _global_logger
    if _global_logger is None:
        _global_logger = CanvasErrorLogger()
    return _global_logger

def log_canvas_operation(operation: str, canvas_path: str, context: Dict,
                        status: str = "success", error: Exception = None) -> str:
    """记录Canvas操作日志（便捷函数）"""
    logger = get_canvas_error_logger()
    return logger.log_canvas_operation(operation, canvas_path, context, status, error)

def log_agent_call(agent_name: str, call_id: str, input_data: Dict,
                  execution_time_ms: int, status: str = "success",
                  error: Exception = None) -> str:
    """记录Agent调用日志（便捷函数）"""
    logger = get_canvas_error_logger()
    return logger.log_agent_call(agent_name, call_id, input_data, execution_time_ms, status, error)