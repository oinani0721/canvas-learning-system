#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Canvas学习系统错误日志记录系统

该系统记录所有Canvas操作错误，提供最佳实践建议，并确保Agent能够读取错误报告。
结合Context7验证的MCP记忆服务技术。

使用方法:
    python canvas_error_system.py --log error_type error_message context
    python canvas_error_system.py --query "相关问题"
    python canvas_error_system.py --report canvas_file

Author: Canvas Learning System Team
Version: 2.0
Created: 2025-10-20
"""

import json
import asyncio
import argparse
import datetime
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# 尝试导入MCP记忆服务
try:
    from mcp_graphiti_memory import add_memory, search_memories
    MEMORY_SERVICE_AVAILABLE = True
except ImportError:
    print("[INFO] MCP记忆服务不可用，使用本地存储")
    MEMORY_SERVICE_AVAILABLE = False

class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    INFO = "info"

class ErrorCategory(Enum):
    """错误类别"""
    CANVAS_OPERATION = "canvas_operation"
    AGENT_EXECUTION = "agent_execution"
    LAYOUT_GENERATION = "layout_generation"
    MEMORY_SYSTEM = "memory_system"
    VALIDATION = "validation"
    PERFORMANCE = "performance"
    USER_INPUT = "user_input"
    SYSTEM = "system"

@dataclass
class CanvasError:
    """Canvas错误记录"""
    error_id: str
    timestamp: datetime.datetime
    category: ErrorCategory
    severity: ErrorSeverity
    error_type: str
    error_message: str
    context: Dict[str, Any]
    stack_trace: Optional[str] = None
    canvas_file: Optional[str] = None
    agent_name: Optional[str] = None
    user_action: Optional[str] = None
    resolution: Optional[str] = None
    prevention_tip: Optional[str] = None
    related_errors: List[str] = None

    def __post_init__(self):
        if self.related_errors is None:
            self.related_errors = []

@dataclass
class BestPractice:
    """最佳实践建议"""
    practice_id: str
    category: ErrorCategory
    title: str
    description: str
    prevention_steps: List[str]
    applicable_scenarios: List[str]
    confidence_score: float
    created_at: datetime.datetime
    usage_count: int = 0

class CanvasErrorSystem:
    """Canvas错误日志系统"""

    def __init__(self):
        """初始化错误系统"""
        self.errors: List[CanvasError] = []
        self.best_practices: List[BestPractice] = []
        self.memory_available = MEMORY_SERVICE_AVAILABLE

        # 初始化基础最佳实践
        self._initialize_best_practices()

        # 加载历史错误
        self._load_historical_errors()

    def _initialize_best_practices(self):
        """初始化基础最佳实践"""
        practices = [
            BestPractice(
                practice_id="canvas_file_validation",
                category=ErrorCategory.CANVAS_OPERATION,
                title="Canvas文件验证最佳实践",
                description="在操作Canvas文件前进行完整性验证",
                prevention_steps=[
                    "检查Canvas文件是否存在",
                    "验证JSON格式是否正确",
                    "确认必需字段(nodes, edges)存在",
                    "检查节点ID的唯一性",
                    "验证边的节点引用有效性"
                ],
                applicable_scenarios=["读取Canvas", "写入Canvas", "修改Canvas"],
                confidence_score=0.95,
                created_at=datetime.datetime.now()
            ),
            BestPractice(
                practice_id="color_system_compliance",
                category=ErrorCategory.VALIDATION,
                title="颜色系统合规性检查",
                description="确保节点颜色符合Canvas学习系统标准",
                prevention_steps=[
                    "验证颜色代码有效性(1=红, 2=绿, 3=紫, 5=蓝, 6=黄)",
                    "检查颜色与节点类型的匹配性",
                    "确保每个问题节点都有对应的黄色理解节点",
                    "验证颜色流转逻辑的正确性",
                    "记录颜色选择的判断依据"
                ],
                applicable_scenarios=["节点创建", "颜色修改", "Agent评分"],
                confidence_score=0.98,
                created_at=datetime.datetime.now()
            ),
            BestPractice(
                practice_id="agent_call_protocol",
                category=ErrorCategory.AGENT_EXECUTION,
                title="Agent调用协议最佳实践",
                description="标准化Agent调用流程，确保结果可靠性",
                prevention_steps=[
                    "验证Agent输入数据的完整性",
                    "使用标准化的调用格式",
                    "设置合理的超时时间",
                    "验证返回结果的数据格式",
                    "记录Agent调用的详细日志"
                ],
                applicable_scenarios=["所有Agent调用"],
                confidence_score=0.92,
                created_at=datetime.datetime.now()
            ),
            BestPractice(
                practice_id="layout_optimization",
                category=ErrorCategory.LAYOUT_GENERATION,
                title="Canvas布局优化最佳实践",
                description="生成清晰、易读的Canvas布局",
                prevention_steps=[
                    "分析节点间的逻辑关系",
                    "选择合适的布局模式(层次/径向/流程)",
                    "确保节点间有足够的间距",
                    "避免边线和节点重叠",
                    "保持布局的一致性和美观性"
                ],
                applicable_scenarios=["布局生成", "节点添加", "结构调整"],
                confidence_score=0.88,
                created_at=datetime.datetime.now()
            ),
            BestPractice(
                practice_id="memory_system_integrity",
                category=ErrorCategory.MEMORY_SYSTEM,
                title="记忆系统数据完整性",
                description="确保学习记忆数据的准确性和一致性",
                prevention_steps=[
                    "验证记忆数据的格式正确性",
                    "检查时间戳的一致性",
                    "确保学习进度数据的逻辑性",
                    "定期备份重要记忆数据",
                    "验证记忆检索的准确性"
                ],
                applicable_scenarios=["记忆存储", "记忆检索", "进度追踪"],
                confidence_score=0.94,
                created_at=datetime.datetime.now()
            )
        ]

        self.best_practices = practices

    def _load_historical_errors(self):
        """加载历史错误记录"""
        try:
            error_log_file = Path.cwd() / "canvas_error_history.json"
            if error_log_file.exists():
                with open(error_log_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for error_data in data.get('errors', []):
                    error = self._deserialize_error(error_data)
                    self.errors.append(error)

                print(f"[INFO] 已加载 {len(self.errors)} 条历史错误记录")

        except Exception as e:
            print(f"[WARN] 加载历史错误失败: {e}")

    async def log_error(
        self,
        category: ErrorCategory,
        severity: ErrorSeverity,
        error_type: str,
        error_message: str,
        context: Dict[str, Any],
        canvas_file: Optional[str] = None,
        agent_name: Optional[str] = None,
        user_action: Optional[str] = None,
        stack_trace: Optional[str] = None
    ) -> str:
        """记录错误"""
        try:
            error_id = f"error_{datetime.datetime.now().timestamp()}"

            # 查找相关的最佳实践
            relevant_practices = self._find_relevant_practices(category, error_type)
            prevention_tip = relevant_practices[0].prevention_steps[0] if relevant_practices else None

            error = CanvasError(
                error_id=error_id,
                timestamp=datetime.datetime.now(),
                category=category,
                severity=severity,
                error_type=error_type,
                error_message=error_message,
                context=context,
                stack_trace=stack_trace,
                canvas_file=canvas_file,
                agent_name=agent_name,
                user_action=user_action,
                prevention_tip=prevention_tip
            )

            self.errors.append(error)

            # 存储到记忆系统
            if self.memory_available:
                memory_content = f"""
Canvas错误记录:
ID: {error_id}
时间: {error.timestamp.isoformat()}
类别: {category.value}
严重程度: {severity.value}
类型: {error_type}
消息: {error_message}
Canvas文件: {canvas_file}
Agent: {agent_name}
用户操作: {user_action}

上下文信息:
{json.dumps(context, indent=2, ensure_ascii=False)}

预防建议:
{prevention_tip or '暂无建议'}

相关最佳实践:
{chr(10).join(f"- {p.title}: {p.description}" for p in relevant_practices[:3])}
"""

                await add_memory(
                    key=f"canvas_error_{error_id}",
                    content=memory_content,
                    metadata={
                        "error_id": error_id,
                        "category": category.value,
                        "severity": severity.value,
                        "error_type": error_type,
                        "canvas_file": canvas_file,
                        "agent_name": agent_name,
                        "timestamp": error.timestamp.isoformat(),
                        "prevention_tip": prevention_tip
                    }
                )

            # 保存到本地文件
            await self._save_errors_to_file()

            print(f"[ERROR] 错误已记录: {error_id} - {error_type}")
            return error_id

        except Exception as e:
            print(f"[CRITICAL] 记录错误失败: {e}")
            return f"log_error_failed_{datetime.datetime.now().timestamp()}"

    def _find_relevant_practices(self, category: ErrorCategory, error_type: str) -> List[BestPractice]:
        """查找相关的最佳实践"""
        relevant = []
        for practice in self.best_practices:
            if practice.category == category:
                # 简单的关键词匹配
                if any(keyword in error_type.lower() for keyword in practice.title.lower().split()):
                    relevant.append(practice)
                    practice.usage_count += 1

        # 如果没有找到完全匹配的，返回同类别的实践
        if not relevant:
            relevant = [p for p in self.best_practices if p.category == category]
            for p in relevant:
                p.usage_count += 1

        return sorted(relevant, key=lambda x: x.confidence_score, reverse=True)

    async def query_errors(
        self,
        query: str,
        category: Optional[ErrorCategory] = None,
        severity: Optional[ErrorSeverity] = None,
        canvas_file: Optional[str] = None,
        limit: int = 10
    ) -> List[CanvasError]:
        """查询错误记录"""
        try:
            filtered_errors = self.errors

            # 应用过滤条件
            if category:
                filtered_errors = [e for e in filtered_errors if e.category == category]

            if severity:
                filtered_errors = [e for e in filtered_errors if e.severity == severity]

            if canvas_file:
                filtered_errors = [e for e in filtered_errors if e.canvas_file == canvas_file]

            # 关键词搜索
            if query:
                query_lower = query.lower()
                filtered_errors = [
                    e for e in filtered_errors
                    if (query_lower in e.error_type.lower() or
                        query_lower in e.error_message.lower() or
                        any(query_lower in str(v).lower() for v in e.context.values()))
                ]

            # 按时间排序并限制结果
            filtered_errors.sort(key=lambda x: x.timestamp, reverse=True)
            return filtered_errors[:limit]

        except Exception as e:
            print(f"[ERROR] 查询错误失败: {e}")
            return []

    async def generate_error_report(self, canvas_file: Optional[str] = None) -> Dict[str, Any]:
        """生成错误报告"""
        try:
            # 统计错误
            total_errors = len(self.errors)
            if canvas_file:
                file_errors = [e for e in self.errors if e.canvas_file == canvas_file]
            else:
                file_errors = self.errors

            # 按类别统计
            category_stats = {}
            severity_stats = {}
            recent_errors = []

            for error in file_errors:
                # 类别统计
                cat = error.category.value
                category_stats[cat] = category_stats.get(cat, 0) + 1

                # 严重程度统计
                sev = error.severity.value
                severity_stats[sev] = severity_stats.get(sev, 0) + 1

                # 最近错误
                if (datetime.datetime.now() - error.timestamp).days <= 7:
                    recent_errors.append(error)

            # 生成建议
            recommendations = self._generate_recommendations(file_errors)

            report = {
                "generated_at": datetime.datetime.now().isoformat(),
                "canvas_file": canvas_file,
                "total_errors": len(file_errors),
                "category_distribution": category_stats,
                "severity_distribution": severity_stats,
                "recent_errors_count": len(recent_errors),
                "most_common_errors": self._get_most_common_errors(file_errors, 5),
                "recommendations": recommendations,
                "best_practices_usage": {p.practice_id: p.usage_count for p in self.best_practices},
                "system_health_score": self._calculate_health_score(file_errors)
            }

            return report

        except Exception as e:
            print(f"[ERROR] 生成错误报告失败: {e}")
            return {}

    def _generate_recommendations(self, errors: List[CanvasError]) -> List[str]:
        """生成改进建议"""
        recommendations = []

        if not errors:
            recommendations.append("系统运行良好，继续保持！")
            return recommendations

        # 分析错误模式
        error_categories = [e.category for e in errors]
        category_counts = {}
        for cat in error_categories:
            category_counts[cat] = category_counts.get(cat, 0) + 1

        # 基于最频繁的错误类别生成建议
        most_common_category = max(category_counts.items(), key=lambda x: x[1])[0]

        if most_common_category == ErrorCategory.CANVAS_OPERATION:
            recommendations.append("建议加强Canvas文件验证，确保文件格式和内容的正确性")
        elif most_common_category == ErrorCategory.AGENT_EXECUTION:
            recommendations.append("建议优化Agent调用协议，增加错误处理和重试机制")
        elif most_common_category == ErrorCategory.VALIDATION:
            recommendations.append("建议完善数据验证流程，特别是颜色系统和节点关系验证")
        elif most_common_category == ErrorCategory.LAYOUT_GENERATION:
            recommendations.append("建议改进布局算法，考虑更多用户偏好和使用场景")
        elif most_common_category == ErrorCategory.MEMORY_SYSTEM:
            recommendations.append("建议增强记忆系统的稳定性和数据完整性检查")

        # 检查是否有严重错误
        critical_errors = [e for e in errors if e.severity == ErrorSeverity.CRITICAL]
        if critical_errors:
            recommendations.append("发现严重错误，建议立即处理并加强系统监控")

        return recommendations

    def _get_most_common_errors(self, errors: List[CanvasError], limit: int = 5) -> List[Dict[str, Any]]:
        """获取最常见的错误"""
        error_counts = {}
        for error in errors:
            error_type = error.error_type
            error_counts[error_type] = error_counts.get(error_type, 0) + 1

        # 排序并返回前N个
        sorted_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)
        return [
            {
                "error_type": error_type,
                "count": count,
                "latest_occurrence": max(e.timestamp for e in errors if e.error_type == error_type).isoformat()
            }
            for error_type, count in sorted_errors[:limit]
        ]

    def _calculate_health_score(self, errors: List[CanvasError]) -> float:
        """计算系统健康分数"""
        if not errors:
            return 100.0

        # 基础分数
        base_score = 100.0

        # 根据错误数量扣分
        error_penalty = min(len(errors) * 2, 50)  # 最多扣50分

        # 根据严重程度扣分
        severity_penalty = 0
        for error in errors:
            if error.severity == ErrorSeverity.CRITICAL:
                severity_penalty += 10
            elif error.severity == ErrorSeverity.HIGH:
                severity_penalty += 5
            elif error.severity == ErrorSeverity.MEDIUM:
                severity_penalty += 2
            elif error.severity == ErrorSeverity.LOW:
                severity_penalty += 1

        severity_penalty = min(severity_penalty, 30)  # 最多扣30分

        # 最近错误的额外扣分
        recent_penalty = 0
        recent_cutoff = datetime.datetime.now() - datetime.timedelta(days=7)
        recent_errors = [e for e in errors if e.timestamp > recent_cutoff]
        recent_penalty = min(len(recent_errors), 20)  # 最多扣20分

        final_score = max(0, base_score - error_penalty - severity_penalty - recent_penalty)
        return round(final_score, 1)

    async def get_agent_guidance(self, current_task: str, canvas_file: Optional[str] = None) -> Dict[str, Any]:
        """为Agent提供错误预防指导"""
        try:
            # 查找相关错误
            relevant_errors = await self.query_errors(current_task, canvas_file=canvas_file, limit=5)

            # 查找相关最佳实践
            task_lower = current_task.lower()
            relevant_practices = []

            for practice in self.best_practices:
                if any(scenario.lower() in task_lower for scenario in practice.applicable_scenarios):
                    relevant_practices.append(practice)

            # 生成指导建议
            guidance = {
                "task": current_task,
                "canvas_file": canvas_file,
                "relevant_errors": [
                    {
                        "error_type": e.error_type,
                        "prevention_tip": e.prevention_tip,
                        "severity": e.severity.value
                    }
                    for e in relevant_errors[:3]
                ],
                "best_practices": [
                    {
                        "title": p.title,
                        "description": p.description,
                        "prevention_steps": p.prevention_steps,
                        "confidence": p.confidence_score
                    }
                    for p in relevant_practices[:3]
                ],
                "recommendations": self._generate_task_recommendations(current_task, relevant_errors, relevant_practices),
                "health_warning": len([e for e in relevant_errors if e.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]]) > 0
            }

            return guidance

        except Exception as e:
            print(f"[ERROR] 生成Agent指导失败: {e}")
            return {"error": str(e)}

    def _generate_task_recommendations(
        self,
        task: str,
        errors: List[CanvasError],
        practices: List[BestPractice]
    ) -> List[str]:
        """为特定任务生成建议"""
        recommendations = []

        # 基于历史错误生成建议
        if errors:
            recommendations.append("基于历史错误，建议特别注意数据验证和错误处理")

        # 基于最佳实践生成建议
        if practices:
            top_practice = max(practices, key=lambda x: x.confidence_score)
            recommendations.append(f"推荐遵循: {top_practice.title}")

        # 任务特定建议
        task_lower = task.lower()
        if "canvas" in task_lower:
            recommendations.append("操作Canvas前请验证文件完整性和格式正确性")
        elif "agent" in task_lower:
            recommendations.append("确保Agent输入数据完整，使用标准调用格式")
        elif "layout" in task_lower:
            recommendations.append("考虑节点关系和用户偏好，选择合适的布局模式")

        return recommendations[:3]  # 最多返回3个建议

    async def _save_errors_to_file(self):
        """保存错误到文件"""
        try:
            error_data = {
                "last_updated": datetime.datetime.now().isoformat(),
                "total_errors": len(self.errors),
                "errors": [self._serialize_error(error) for error in self.errors]
            }

            error_log_file = Path.cwd() / "canvas_error_history.json"
            with open(error_log_file, 'w', encoding='utf-8') as f:
                json.dump(error_data, f, indent=2, ensure_ascii=False, default=str)

        except Exception as e:
            print(f"[ERROR] 保存错误文件失败: {e}")

    def _serialize_error(self, error: CanvasError) -> Dict[str, Any]:
        """序列化错误对象"""
        data = asdict(error)
        # 转换枚举和日期时间
        data['category'] = error.category.value
        data['severity'] = error.severity.value
        data['timestamp'] = error.timestamp.isoformat()
        return data

    def _deserialize_error(self, data: Dict[str, Any]) -> CanvasError:
        """反序列化错误对象"""
        # 转换枚举和日期时间
        data['category'] = ErrorCategory(data['category'])
        data['severity'] = ErrorSeverity(data['severity'])
        data['timestamp'] = datetime.datetime.fromisoformat(data['timestamp'])

        return CanvasError(**data)

# 全局错误系统实例
error_system = CanvasErrorSystem()

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Canvas错误日志系统')
    parser.add_argument('--log', nargs=4, metavar=('category', 'severity', 'type', 'message'),
                       help='记录错误')
    parser.add_argument('--query', metavar='query_string', help='查询错误')
    parser.add_argument('--report', metavar='canvas_file', nargs='?', const=None,
                       help='生成错误报告')
    parser.add_argument('--guidance', nargs=2, metavar=('task', 'canvas_file'),
                       help='获取Agent指导')

    args = parser.parse_args()

    try:
        if args.log:
            category, severity, error_type, error_message = args.log

            # 记录错误
            error_id = await error_system.log_error(
                category=ErrorCategory(category),
                severity=ErrorSeverity(severity),
                error_type=error_type,
                error_message=error_message,
                context={"command_line_args": True}
            )
            print(f"错误已记录: {error_id}")

        elif args.query:
            query_string = args.query

            # 查询错误
            results = await error_system.query_errors(query_string)
            print(f"找到 {len(results)} 个相关错误:")
            for error in results:
                print(f"  - {error.error_type}: {error.error_message}")

        elif args.report is not None:
            canvas_file = args.report

            # 生成报告
            report = await error_system.generate_error_report(canvas_file)
            print("错误报告:")
            print(json.dumps(report, indent=2, ensure_ascii=False, default=str))

        elif args.guidance:
            task, canvas_file = args.guidance

            # 获取指导
            guidance = await error_system.get_agent_guidance(task, canvas_file)
            print("Agent指导:")
            print(json.dumps(guidance, indent=2, ensure_ascii=False, default=str))

        else:
            print("请指定操作模式: --log, --query, --report, 或 --guidance")
            print("使用 --help 查看详细帮助")

    except Exception as e:
        print(f"[ERROR] 执行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())