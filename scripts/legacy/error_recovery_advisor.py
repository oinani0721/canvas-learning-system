"""
Canvas学习系统 - 错误恢复建议器
Story 8.11: 集成Canvas专用错误日志系统

本模块提供智能错误诊断和恢复建议，包括：
- 常见错误的解决方案库
- 智能错误诊断
- 预防措施建议
- 错误恢复步骤指导

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-22
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import re


class ErrorRecoveryAdvisor:
    """错误恢复建议器"""

    def __init__(self):
        """初始化错误恢复建议器"""
        self.recovery_database = self._load_recovery_database()
        self.pattern_matchers = self._initialize_pattern_matchers()

    def _load_recovery_database(self) -> Dict:
        """加载恢复建议数据库"""
        return {
            "file_operations": {
                "FileNotFoundError": {
                    "description": "Canvas文件不存在",
                    "common_causes": [
                        "文件路径输入错误",
                        "文件被删除或移动",
                        "文件名拼写错误",
                        "工作目录不正确"
                    ],
                    "recovery_steps": [
                        {
                            "step": 1,
                            "action": "验证文件路径",
                            "description": "检查文件路径是否正确，包括目录和文件名",
                            "command": "ls -la /path/to/canvas/file.canvas"
                        },
                        {
                            "step": 2,
                            "action": "检查工作目录",
                            "description": "确认当前工作目录是否正确",
                            "command": "pwd"
                        },
                        {
                            "step": 3,
                            "action": "搜索相似文件",
                            "description": "在当前目录及子目录中搜索可能的Canvas文件",
                            "command": "find . -name '*.canvas' -type f"
                        },
                        {
                            "step": 4,
                            "action": "检查文件权限",
                            "description": "确认是否有读取文件的权限",
                            "command": "ls -lh /path/to/canvas/file.canvas"
                        }
                    ],
                    "prevention_measures": [
                        "使用绝对路径而非相对路径",
                        "在操作前检查文件是否存在",
                        "实现文件路径验证机制",
                        "提供文件选择界面而非手动输入"
                    ],
                    "related_errors": ["PermissionError", "IsADirectoryError"]
                },

                "PermissionError": {
                    "description": "文件权限不足",
                    "common_causes": [
                        "文件只读属性",
                        "目录权限限制",
                        "用户权限不足",
                        "文件被其他程序占用"
                    ],
                    "recovery_steps": [
                        {
                            "step": 1,
                            "action": "检查文件权限",
                            "description": "查看文件当前的权限设置",
                            "command": "ls -la /path/to/file"
                        },
                        {
                            "step": 2,
                            "action": "修改文件权限",
                            "description": "如果安全，尝试修改文件权限",
                            "command": "chmod 644 /path/to/file"
                        },
                        {
                            "step": 3,
                            "action": "检查文件占用",
                            "description": "确认文件是否被其他程序占用",
                            "command": "lsof /path/to/file"
                        },
                        {
                            "step": 4,
                            "action": "以管理员身份运行",
                            "description": "如果必要，尝试以管理员权限运行程序"
                        }
                    ],
                    "prevention_measures": [
                        "确保运行环境有足够权限",
                        "在程序启动时检查权限",
                        "提供权限不足的友好提示",
                        "实现权限申请机制"
                    ],
                    "related_errors": ["FileNotFoundError", "OSError"]
                },

                "json.JSONDecodeError": {
                    "description": "Canvas文件格式错误",
                    "common_causes": [
                        "文件内容不是有效的JSON格式",
                        "JSON语法错误",
                        "文件编码问题",
                        "文件被截断或损坏"
                    ],
                    "recovery_steps": [
                        {
                            "step": 1,
                            "action": "验证JSON格式",
                            "description": "使用JSON验证工具检查文件格式",
                            "command": "python -m json.tool /path/to/file.canvas"
                        },
                        {
                            "step": 2,
                            "action": "检查文件编码",
                            "description": "确认文件编码是否为UTF-8",
                            "command": "file -i /path/to/file.canvas"
                        },
                        {
                            "step": 3,
                            "action": "备份并修复",
                            "description": "备份原文件并尝试修复JSON格式",
                            "command": "cp /path/to/file.canvas /path/to/file.backup"
                        },
                        {
                            "step": 4,
                            "action": "重新创建文件",
                            "description": "如果无法修复，使用标准模板重新创建Canvas文件"
                        }
                    ],
                    "prevention_measures": [
                        "在写入前验证JSON格式",
                        "实现原子写入操作",
                        "添加文件完整性检查",
                        "使用标准Canvas模板"
                    ],
                    "related_errors": ["UnicodeDecodeError", "ValueError"]
                }
            },

            "agent_operations": {
                "TimeoutError": {
                    "description": "Agent执行超时",
                    "common_causes": [
                        "AI服务响应缓慢",
                        "网络连接问题",
                        "输入数据过大",
                        "系统资源不足"
                    ],
                    "recovery_steps": [
                        {
                            "step": 1,
                            "action": "检查网络连接",
                            "description": "验证网络连接是否正常",
                            "command": "ping -c 4 api.anthropic.com"
                        },
                        {
                            "step": 2,
                            "action": "增加超时时间",
                            "description": "适当增加Agent调用的超时时间设置",
                            "command": "export AGENT_TIMEOUT=60"
                        },
                        {
                            "step": 3,
                            "action": "简化输入数据",
                            "description": "减少或简化输入给Agent的数据量"
                        },
                        {
                            "step": 4,
                            "action": "检查系统资源",
                            "description": "确认系统有足够的内存和CPU资源",
                            "command": "free -h && top -bn1"
                        }
                    ],
                    "prevention_measures": [
                        "实现超时重试机制",
                        "添加输入数据大小限制",
                        "监控网络状态",
                        "提供进度反馈"
                    ],
                    "related_errors": ["ConnectionError", "HTTPError"]
                },

                "ValueError": {
                    "description": "Agent输入数据无效",
                    "common_causes": [
                        "输入数据格式不正确",
                        "参数值超出有效范围",
                        "必需参数缺失",
                        "数据类型不匹配"
                    ],
                    "recovery_steps": [
                        {
                            "step": 1,
                            "action": "验证输入格式",
                            "description": "检查输入数据的格式是否符合要求"
                        },
                        {
                            "step": 2,
                            "action": "检查参数范围",
                            "description": "确认所有参数都在有效范围内"
                        },
                        {
                            "step": 3,
                            "action": "补充缺失参数",
                            "description": "添加缺失的必需参数"
                        },
                        {
                            "step": 4,
                            "action": "类型转换",
                            "description": "对数据进行适当的类型转换"
                        }
                    ],
                    "prevention_measures": [
                        "实现输入验证机制",
                        "提供清晰的输入格式说明",
                        "添加参数校验函数",
                        "使用默认值处理"
                    ],
                    "related_errors": ["TypeError", "KeyError"]
                }
            },

            "node_operations": {
                "KeyError": {
                    "description": "节点ID不存在",
                    "common_causes": [
                        "节点ID输入错误",
                        "节点已被删除",
                        "Canvas文件结构变化",
                        "节点ID格式不正确"
                    ],
                    "recovery_steps": [
                        {
                            "step": 1,
                            "action": "列出所有节点ID",
                            "description": "获取Canvas中所有节点的ID列表",
                            "command": "python -c \"import json; data=json.load(open('file.canvas')); print([n['id'] for n in data['nodes']])\""
                        },
                        {
                            "step": 2,
                            "action": "搜索相似ID",
                            "description": "查找与输入ID相似的节点ID"
                        },
                        {
                            "step": 3,
                            "action": "验证ID格式",
                            "description": "确认节点ID格式是否符合规范"
                        },
                        {
                            "step": 4,
                            "action": "创建新节点",
                            "description": "如果节点确实不存在，创建新的节点"
                        }
                    ],
                    "prevention_measures": [
                        "实现节点ID验证",
                        "提供节点选择界面",
                        "维护节点ID缓存",
                        "添加模糊搜索功能"
                    ],
                    "related_errors": ["IndexError", "TypeError"]
                },

                "IndexError": {
                    "description": "节点索引超出范围",
                    "common_causes": [
                        "索引值超出节点列表范围",
                        "节点列表为空",
                        "索引计算错误",
                        "节点位置变化"
                    ],
                    "recovery_steps": [
                        {
                            "step": 1,
                            "action": "检查节点数量",
                            "description": "确认Canvas中的节点总数",
                            "command": "python -c \"import json; data=json.load(open('file.canvas')); print(len(data['nodes']))\""
                        },
                        {
                            "step": 2,
                            "action": "验证索引值",
                            "description": "确认索引值在有效范围内"
                        },
                        {
                            "step": 3,
                            "action": "使用节点ID",
                            "description": "改用节点ID而非索引来访问节点"
                        },
                        {
                            "step": 4,
                            "action": "重新计算索引",
                            "description": "基于当前节点列表重新计算正确的索引"
                        }
                    ],
                    "prevention_measures": [
                        "优先使用节点ID",
                        "实现索引边界检查",
                        "添加空列表检查",
                        "提供索引验证函数"
                    ],
                    "related_errors": ["KeyError", "TypeError"]
                }
            },

            "system_errors": {
                "MemoryError": {
                    "description": "系统内存不足",
                    "common_causes": [
                        "处理大型Canvas文件",
                        "内存泄漏",
                        "同时运行多个程序",
                        "系统内存不足"
                    ],
                    "recovery_steps": [
                        {
                            "step": 1,
                            "action": "检查内存使用",
                            "description": "查看当前内存使用情况",
                            "command": "free -h"
                        },
                        {
                            "step": 2,
                            "action": "释放内存",
                            "description": "关闭不必要的程序释放内存"
                        },
                        {
                            "step": 3,
                            "action": "分批处理",
                            "description": "将大文件分批处理而非一次性加载"
                        },
                        {
                            "step": 4,
                            "action": "重启程序",
                            "description": "重启程序清理内存碎片"
                        }
                    ],
                    "prevention_measures": [
                        "实现内存监控",
                        "优化数据结构",
                        "添加内存限制",
                        "实现流式处理"
                    ],
                    "related_errors": ["OSError", "ResourceWarning"]
                },

                "ConnectionError": {
                    "description": "网络连接错误",
                    "common_causes": [
                        "网络连接中断",
                        "服务器不可达",
                        "DNS解析失败",
                        "防火墙阻拦"
                    ],
                    "recovery_steps": [
                        {
                            "step": 1,
                            "action": "检查网络连接",
                            "description": "测试基本网络连通性",
                            "command": "ping -c 4 8.8.8.8"
                        },
                        {
                            "step": 2,
                            "action": "检查DNS解析",
                            "description": "验证DNS解析是否正常",
                            "command": "nslookup api.anthropic.com"
                        },
                        {
                            "step": 3,
                            "action": "检查防火墙",
                            "description": "确认防火墙没有阻拦相关端口"
                        },
                        {
                            "step": 4,
                            "action": "使用代理",
                            "description": "如果需要，配置网络代理"
                        }
                    ],
                    "prevention_measures": [
                        "实现网络检测",
                        "添加重试机制",
                        "提供离线模式",
                        "缓存重要数据"
                    ],
                    "related_errors": ["TimeoutError", "HTTPError"]
                }
            }
        }

    def _initialize_pattern_matchers(self) -> Dict:
        """初始化错误模式匹配器"""
        return {
            "file_path_errors": [
                re.compile(r"No such file or directory"),
                re.compile(r"File not found"),
                re.compile(r"cannot access"),
                re.compile(r"does not exist")
            ],
            "permission_errors": [
                re.compile(r"Permission denied"),
                re.compile(r"Access denied"),
                re.compile(r"Operation not permitted"),
                re.compile(r"Read-only file system")
            ],
            "json_errors": [
                re.compile(r"Expecting"),
                re.compile(r"Unterminated string"),
                re.compile(r"Extra data"),
                re.compile(r"Invalid control character")
            ],
            "network_errors": [
                re.compile(r"Connection refused"),
                re.compile(r"Name or service not known"),
                re.compile(r"Network is unreachable"),
                re.compile(r"Connection timed out")
            ],
            "memory_errors": [
                re.compile(r"MemoryError"),
                re.compile(r"Unable to allocate"),
                re.compile(r"Out of memory"),
                re.compile(r"Cannot allocate memory")
            ]
        }

    def get_recovery_advice(self, error: Exception, context: Dict = None) -> Dict:
        """获取错误恢复建议

        Args:
            error: 异常对象
            context: 错误上下文信息

        Returns:
            Dict: 恢复建议信息
        """
        error_type = type(error).__name__
        error_message = str(error)

        # 确定错误类别
        category = self._classify_error(error_type, error_message, context)

        # 获取基础恢复信息
        base_recovery = self._get_base_recovery(category, error_type)

        # 生成个性化建议
        personalized_advice = self._generate_personalized_advice(error, context, base_recovery)

        return {
            "error_info": {
                "type": error_type,
                "message": error_message,
                "category": category
            },
            "recovery_plan": personalized_advice,
            "prevention_guide": base_recovery.get("prevention_measures", []),
            "related_resources": self._get_related_resources(category, error_type),
            "escalation_triggers": self._get_escalation_triggers(category, error_type)
        }

    def _classify_error(self, error_type: str, error_message: str, context: Dict = None) -> str:
        """分类错误"""
        # 首先基于异常类型分类
        type_mapping = {
            "FileNotFoundError": "file_operations",
            "PermissionError": "file_operations",
            "JSONDecodeError": "file_operations",
            "TimeoutError": "agent_operations",
            "ValueError": "agent_operations",
            "KeyError": "node_operations",
            "IndexError": "node_operations",
            "MemoryError": "system_errors",
            "ConnectionError": "system_errors"
        }

        if error_type in type_mapping:
            return type_mapping[error_type]

        # 基于错误消息模式匹配
        for category, patterns in self.pattern_matchers.items():
            for pattern in patterns:
                if pattern.search(error_message):
                    return category.replace("_errors", "")

        # 基于上下文分类
        if context:
            if "agent_name" in context:
                return "agent_operations"
            elif "node_id" in context or "edge_id" in context:
                return "node_operations"
            elif "canvas_path" in context:
                return "file_operations"

        return "system_errors"

    def _get_base_recovery(self, category: str, error_type: str) -> Dict:
        """获取基础恢复信息"""
        return self.recovery_database.get(category, {}).get(error_type, {
            "description": f"未知错误类型: {error_type}",
            "common_causes": ["未知原因"],
            "recovery_steps": [
                {
                    "step": 1,
                    "action": "查看详细错误信息",
                    "description": "仔细阅读错误消息和堆栈跟踪"
                },
                {
                    "step": 2,
                    "action": "搜索解决方案",
                    "description": "在文档或网上搜索相关解决方案"
                },
                {
                            "step": 3,
                    "action": "联系技术支持",
                    "description": "如果问题持续，联系技术支持团队"
                }
            ],
            "prevention_measures": ["添加更多错误检查"],
            "related_errors": []
        })

    def _generate_personalized_advice(self, error: Exception, context: Dict, base_recovery: Dict) -> Dict:
        """生成个性化恢复建议"""
        advice = {
            "immediate_actions": [],
            "detailed_steps": base_recovery.get("recovery_steps", []),
            "context_specific_tips": [],
            "estimated_difficulty": "medium",
            "estimated_time": "5-10 minutes"
        }

        # 基于上下文添加个性化建议
        if context:
            if "canvas_path" in context:
                canvas_path = context["canvas_path"]
                advice["immediate_actions"].append(f"检查Canvas文件: {canvas_path}")
                advice["context_specific_tips"].append("确保Canvas文件格式正确且可读")

            if "agent_name" in context:
                agent_name = context["agent_name"]
                advice["immediate_actions"].append(f"检查Agent配置: {agent_name}")
                advice["context_specific_tips"].append("验证Agent输入参数格式")

            if "node_id" in context:
                node_id = context["node_id"]
                advice["immediate_actions"].append(f"验证节点ID: {node_id}")
                advice["context_specific_tips"].append("确认节点在Canvas中存在")

        # 根据错误类型调整难度和时间估算
        error_type = type(error).__name__
        if error_type in ["FileNotFoundError", "PermissionError"]:
            advice["estimated_difficulty"] = "easy"
            advice["estimated_time"] = "2-5 minutes"
        elif error_type in ["MemoryError", "ConnectionError"]:
            advice["estimated_difficulty"] = "hard"
            advice["estimated_time"] = "10-30 minutes"

        return advice

    def _get_related_resources(self, category: str, error_type: str) -> List[Dict]:
        """获取相关资源"""
        resources = []

        # 通用资源
        general_resources = [
            {
                "title": "Canvas学习系统文档",
                "url": "docs/",
                "type": "documentation"
            },
            {
                "title": "故障排除指南",
                "url": "docs/troubleshooting.md",
                "type": "guide"
            }
        ]

        # 特定类型资源
        if category == "file_operations":
            resources.extend([
                {
                    "title": "Canvas文件格式规范",
                    "url": "docs/canvas-format.md",
                    "type": "specification"
                },
                {
                    "title": "文件操作最佳实践",
                    "url": "docs/file-operations.md",
                    "type": "guide"
                }
            ])
        elif category == "agent_operations":
            resources.extend([
                {
                    "title": "Agent配置指南",
                    "url": "docs/agent-configuration.md",
                    "type": "guide"
                },
                {
                    "title": "Agent调用示例",
                    "url": "docs/agent-examples.md",
                    "type": "examples"
                }
            ])

        return general_resources + resources

    def _get_escalation_triggers(self, category: str, error_type: str) -> List[str]:
        """获取升级触发条件"""
        triggers = [
            "错误在多次尝试后持续出现",
            "系统功能受到严重影响",
            "无法确定错误原因",
            "建议的解决方案无效"
        ]

        # 特定类型的升级条件
        if category == "system_errors":
            triggers.append("系统资源持续不足")
            triggers.append("网络连接长时间中断")
        elif category == "file_operations":
            triggers.append("重要Canvas文件损坏")
            triggers.append("权限问题无法解决")

        return triggers

    def diagnose_error_pattern(self, error_logs: List[Dict]) -> Dict:
        """诊断错误模式

        Args:
            error_logs: 错误日志列表

        Returns:
            Dict: 错误模式分析结果
        """
        if not error_logs:
            return {
                "pattern_detected": False,
                "analysis": "没有足够的错误数据进行分析"
            }

        # 统计错误类型
        error_types = {}
        error_categories = {}
        error_timeline = []

        for log in error_logs:
            error_info = log.get("error_information", {})
            error_type = error_info.get("error_type", "Unknown")
            category = log.get("category", "unknown")
            timestamp = log.get("timestamp", "")

            error_types[error_type] = error_types.get(error_type, 0) + 1
            error_categories[category] = error_categories.get(category, 0) + 1
            error_timeline.append(timestamp)

        # 分析模式
        total_errors = len(error_logs)
        most_common_type = max(error_types.items(), key=lambda x: x[1])
        most_common_category = max(error_categories.items(), key=lambda x: x[1])

        # 时间模式分析
        time_pattern = self._analyze_time_pattern(error_timeline)

        # 生成诊断结果
        diagnosis = {
            "pattern_detected": True,
            "total_errors": total_errors,
            "most_frequent_error": {
                "type": most_common_type[0],
                "count": most_common_type[1],
                "percentage": round((most_common_type[1] / total_errors) * 100, 1)
            },
            "most_affected_category": {
                "name": most_common_category[0],
                "count": most_common_category[1],
                "percentage": round((most_common_category[1] / total_errors) * 100, 1)
            },
            "time_pattern": time_pattern,
            "recommendations": self._generate_pattern_recommendations(error_types, error_categories),
            "needs_attention": most_common_type[1] > total_errors * 0.5  # 超过50%的错误是同一类型
        }

        return diagnosis

    def _analyze_time_pattern(self, timestamps: List[str]) -> Dict:
        """分析时间模式"""
        if not timestamps:
            return {"pattern": "no_data"}

        try:
            # 转换时间戳
            times = [datetime.fromisoformat(ts.replace('Z', '+00:00')) for ts in timestamps if ts]

            if len(times) < 2:
                return {"pattern": "insufficient_data"}

            # 计算时间间隔
            intervals = []
            for i in range(1, len(times)):
                interval = (times[i] - times[i-1]).total_seconds()
                intervals.append(interval)

            avg_interval = sum(intervals) / len(intervals)

            # 判断模式
            if avg_interval < 60:  # 小于1分钟
                pattern = "burst"
                description = "错误集中爆发，可能存在系统性问题"
            elif avg_interval < 3600:  # 小于1小时
                pattern = "frequent"
                description = "错误频繁发生，需要关注"
            else:
                pattern = "sporadic"
                description = "错误零星发生，可能是偶发问题"

            return {
                "pattern": pattern,
                "description": description,
                "average_interval_seconds": round(avg_interval, 1),
                "total_timespan_hours": round((times[-1] - times[0]).total_seconds() / 3600, 1)
            }

        except Exception:
            return {"pattern": "analysis_failed", "description": "时间分析失败"}

    def _generate_pattern_recommendations(self, error_types: Dict, error_categories: Dict) -> List[str]:
        """基于模式生成建议"""
        recommendations = []

        # 基于错误类型的建议
        if error_types.get("FileNotFoundError", 0) > 0:
            recommendations.append("建议检查文件路径管理机制")

        if error_types.get("TimeoutError", 0) > 0:
            recommendations.append("建议优化网络连接和超时设置")

        if error_types.get("MemoryError", 0) > 0:
            recommendations.append("建议检查内存使用和优化数据结构")

        # 基于错误类别的建议
        if error_categories.get("file_operations", 0) > len(error_types) * 0.5:
            recommendations.append("文件操作问题较多，建议审查文件处理逻辑")

        if error_categories.get("agent_operations", 0) > len(error_types) * 0.5:
            recommendations.append("Agent调用问题较多，建议检查AI服务配置")

        return recommendations


# 全局错误恢复建议器实例
_global_advisor = None

def get_error_recovery_advisor() -> ErrorRecoveryAdvisor:
    """获取全局错误恢复建议器实例"""
    global _global_advisor
    if _global_advisor is None:
        _global_advisor = ErrorRecoveryAdvisor()
    return _global_advisor

def get_recovery_advice(error: Exception, context: Dict = None) -> Dict:
    """获取错误恢复建议（便捷函数）"""
    advisor = get_error_recovery_advisor()
    return advisor.get_recovery_advice(error, context)

def diagnose_error_pattern(error_logs: List[Dict]) -> Dict:
    """诊断错误模式（便捷函数）"""
    advisor = get_error_recovery_advisor()
    return advisor.diagnose_error_pattern(error_logs)