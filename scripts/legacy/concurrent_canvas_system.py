"""
Canvas学习系统 v2.0 - 多Agent并发分析系统核心实现

本文件实现了多Agent并发分析系统的核心组件，包括：
- Task Coordinator: 任务协调器
- Process Pool Manager: 进程池管理器
- Result Merger: 结果融合器
- Content Validator: 内容验证器
- Optimized Canvas Writer: 优化的Canvas写入器

Author: Claude (Dev Agent)
Version: 2.0
Created: 2025-10-18
"""

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import hashlib
import os
import sys

# 添加现有canvas_utils到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from canvas_utils import CanvasJSONOperator, CanvasBusinessLogic

# 尝试导入aiomultiprocess（如果可用）
try:
    import aiomultiprocess
    AIOMULTIPROCESS_AVAILABLE = True
except ImportError:
    AIOMULTIPROCESS_AVAILABLE = False
    print("警告: aiomultiprocess未安装，将使用asyncio模拟并发")

# 尝试导入psutil（用于性能监控）
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("警告: psutil未安装，性能监控功能受限")


# ========== 数据结构定义 ==========

@dataclass
class AgentTask:
    """Agent任务定义"""
    task_id: str
    agent_name: str
    input_data: Dict[str, Any]
    target_node_id: str
    priority: int = 1
    estimated_duration: float = 5.0
    dependencies: List[str] = field(default_factory=list)
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3

@dataclass
class TaskResult:
    """任务执行结果"""
    task_id: str
    agent_name: str
    target_node_id: str
    status: str  # "success", "failed", "timeout"
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    content_length: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ValidationResult:
    """内容验证结果"""
    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    confidence_score: float = 1.0

    def add_error(self, error: str):
        self.errors.append(error)
        self.is_valid = False
        self.confidence_score = max(0.0, self.confidence_score - 0.2)

    def add_warning(self, warning: str):
        self.warnings.append(warning)
        self.confidence_score = max(0.0, self.confidence_score - 0.1)

    def merge(self, other: 'ValidationResult'):
        self.is_valid = self.is_valid and other.is_valid
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.confidence_score = min(self.confidence_score, other.confidence_score)

@dataclass
class ErrorHandlingResult:
    """错误处理结果"""
    should_retry: bool = False
    retry_delay: float = 0.0
    modifications: Dict[str, Any] = field(default_factory=dict)
    message: str = ""


# ========== 异常类定义 ==========

class ConcurrentAnalysisError(Exception):
    """并发分析异常"""
    pass

class CanvasWriteError(Exception):
    """Canvas写入异常"""
    pass

class ConnectionPoolError(Exception):
    """连接池异常"""
    pass


# ========== 核心组件实现 ==========

class AgentClassifier:
    """Agent分类器"""

    AGENT_CATEGORIES = {
        "computation_intensive": {
            "agents": ["oral-explanation", "clarification-path", "four-level-explanation"],
            "executor": "process_pool",
            "max_concurrent": 2,
            "timeout": 30.0,
            "memory_mb": 300
        },
        "io_intensive": {
            "agents": ["comparison-table", "memory-anchor", "basic-decomposition", "deep-decomposition"],
            "executor": "async_pool",
            "max_concurrent": 4,
            "timeout": 15.0,
            "memory_mb": 150
        },
        "lightweight": {
            "agents": ["scoring-agent", "verification-question-agent", "example-teaching"],
            "executor": "direct",
            "max_concurrent": 6,
            "timeout": 10.0,
            "memory_mb": 100
        }
    }

    @classmethod
    def classify_agent(cls, agent_name: str) -> Dict[str, Any]:
        """分类Agent并返回执行配置"""
        for category, config in cls.AGENT_CATEGORIES.items():
            if agent_name in config["agents"]:
                return config.copy()

        # 默认分类为轻量级
        return cls.AGENT_CATEGORIES["lightweight"].copy()


class ProcessPoolManager:
    """进程池管理器"""

    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or min(4, os.cpu_count() or 2)
        self.process_pool = None
        self.async_pool = None
        self.initialized = False

    async def initialize(self):
        """初始化进程池"""
        if self.initialized:
            return

        if AIOMULTIPROCESS_AVAILABLE:
            # 使用aiomultiprocess实现真正的并行
            self.async_pool = aiomultiprocess.Pool(processes=self.max_workers)
            print(f"✅ aiomultiprocess池初始化成功，进程数: {self.max_workers}")
        else:
            # 降级到asyncio
            print("⚠️  使用asyncio模拟并发（性能受限）")

        self.initialized = True

    async def execute_task(self, task: AgentTask) -> TaskResult:
        """执行Agent任务"""
        if not self.initialized:
            await self.initialize()

        start_time = time.time()
        task_id = task.task_id

        try:
            # 获取Agent分类配置
            config = AgentClassifier.classify_agent(task.agent_name)
            timeout = config["timeout"]

            if AIOMULTIPROCESS_AVAILABLE and config["executor"] == "process_pool":
                # 真正的并行执行
                result = await self._execute_with_aiomultiprocess(task, timeout)
            else:
                # 异步执行
                result = await self._execute_with_asyncio(task, timeout)

            result.execution_time = time.time() - start_time
            return result

        except asyncio.TimeoutError:
            return TaskResult(
                task_id=task_id,
                agent_name=task.agent_name,
                target_node_id=task.target_node_id,
                status="timeout",
                execution_time=time.time() - start_time,
                error_message=f"任务超时 ({config['timeout']}秒)"
            )
        except Exception as e:
            return TaskResult(
                task_id=task_id,
                agent_name=task.agent_name,
                target_node_id=task.target_node_id,
                status="failed",
                execution_time=time.time() - start_time,
                error_message=str(e)
            )

    async def _execute_with_aiomultiprocess(
        self,
        task: AgentTask,
        timeout: float
    ) -> TaskResult:
        """使用aiomultiprocess执行任务"""

        async def agent_worker():
            """Agent工作进程"""
            return await self._call_agent_simulation(task)

        try:
            # 使用aiomultiprocess执行
            result_data = await asyncio.wait_for(
                self.async_pool.apply(agent_worker),
                timeout=timeout
            )

            return TaskResult(
                task_id=task.task_id,
                agent_name=task.agent_name,
                target_node_id=task.target_node_id,
                status="success",
                result_data=result_data,
                content_length=len(str(result_data))
            )

        except asyncio.TimeoutError:
            raise

    async def _execute_with_asyncio(
        self,
        task: AgentTask,
        timeout: float
    ) -> TaskResult:
        """使用asyncio执行任务"""

        try:
            result_data = await asyncio.wait_for(
                self._call_agent_simulation(task),
                timeout=timeout
            )

            return TaskResult(
                task_id=task.task_id,
                agent_name=task.agent_name,
                target_node_id=task.target_node_id,
                status="success",
                result_data=result_data,
                content_length=len(str(result_data))
            )

        except asyncio.TimeoutError:
            raise

    async def _call_agent_simulation(self, task: AgentTask) -> Dict[str, Any]:
        """模拟Agent调用（实际实现中会调用真实的Claude Code Agent）"""

        # 模拟Agent处理时间
        config = AgentClassifier.classify_agent(task.agent_name)
        processing_time = config.get("timeout", 5.0) * 0.6  # 60%的超时时间
        await asyncio.sleep(processing_time)

        # 模拟不同Agent的输出
        user_understanding = task.input_data.get("user_understanding", "")
        question_text = task.input_data.get("question_text", "")

        if task.agent_name == "oral-explanation":
            content = f"""🗣️ 教授式讲解：{question_text}

{user_understanding}

这是一个关于"{question_text}"的详细口语化解释，包含了背景铺垫、核心概念讲解、生动举例和常见误区分析。

## 背景铺垫
{question_text}是学习过程中的重要概念，理解它对于掌握整个知识体系至关重要。

## 核心解释
基于您的理解"{user_understanding[:100]}..."，我们可以进一步深化...

## 生动举例
举个简单的例子...

## 常见误区
学习{question_text}时容易犯的错误包括...

*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        elif task.agent_name == "clarification-path":
            content = f"""🔍 深度澄清路径：{question_text}

## 1. 问题澄清
我们要解决的核心问题是"{question_text}"。

## 2. 概念拆解
基于您的理解"{user_understanding[:100]}..."，我们可以将这个概念拆解为以下几个关键部分...

## 3. 深度解释
每个部分的详细解释...

## 4. 验证总结
通过以上分析，我们可以得出结论...

*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        elif task.agent_name == "comparison-table":
            content = f"""📊 概念对比表

| 维度 | 概念A | 概念B |
|------|-------|-------|
| 定义 | 定义A | 定义B |
| 特征 | 特征A | 特征B |
| 使用场景 | 场景A | 场景B |
| 示例 | 示例A | 示例B |

基于您的理解：{user_understanding[:100]}...

*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        else:
            # 默认内容
            content = f"""🤖 {task.agent_name} 分析结果

基于您对"{question_text}"的理解：{user_understanding}

这是{task.agent_name}生成的分析内容。

*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

        return {
            "content": content,
            "agent_name": task.agent_name,
            "target_node_id": task.target_node_id,
            "processing_time": processing_time
        }

    async def shutdown(self):
        """关闭进程池"""
        if self.async_pool:
            await self.async_pool.close()
        print("✅ 进程池已关闭")


class TaskCoordinator:
    """任务协调器"""

    def __init__(self, max_workers: int = 4, max_concurrent_agents: int = 3):
        self.max_workers = max_workers
        self.max_concurrent_agents = max_concurrent_agents
        self.process_manager = ProcessPoolManager(max_workers)
        self.active_tasks: Dict[str, AgentTask] = {}
        self.completed_results: List[TaskResult] = []

    async def initialize(self):
        """初始化任务协调器"""
        await self.process_manager.initialize()

    async def coordinate_concurrent_analysis(
        self,
        canvas_path: str,
        yellow_nodes: List[Dict],
        selected_agents: List[str],
        analysis_mode: str = "parallel"
    ) -> Dict[str, Any]:
        """协调多Agent并发分析"""

        print(f"🚀 开始并发分析：{len(yellow_nodes)}个节点，{len(selected_agents)}个Agent")
        start_time = time.time()

        try:
            # 1. 生成任务
            tasks = await self._generate_tasks(yellow_nodes, selected_agents)
            print(f"📋 生成了{len(tasks)}个任务")

            # 2. 执行并发任务
            if analysis_mode == "parallel":
                results = await self._execute_parallel(tasks)
            elif analysis_mode == "sequential":
                results = await self._execute_sequential(tasks)
            else:
                results = await self._execute_hybrid(tasks)

            # 3. 统计结果
            successful = sum(1 for r in results if r.status == "success")
            failed = sum(1 for r in results if r.status == "failed")
            timeout = sum(1 for r in results if r.status == "timeout")

            total_time = time.time() - start_time
            performance_improvement = len(tasks) * 5.0 / total_time  # 假设串行每个任务5秒

            print(f"✅ 并发分析完成：{successful}成功，{failed}失败，{timeout}超时")
            print(f"⏱️  总耗时：{total_time:.2f}秒，性能提升：{performance_improvement:.1f}倍")

            return {
                "status": "completed",
                "total_time": total_time,
                "performance_improvement": performance_improvement,
                "results": results,
                "statistics": {
                    "total_tasks": len(tasks),
                    "successful": successful,
                    "failed": failed,
                    "timeout": timeout
                }
            }

        except Exception as e:
            print(f"❌ 并发分析失败：{str(e)}")
            raise ConcurrentAnalysisError(f"并发分析失败: {str(e)}")

    async def _generate_tasks(
        self,
        yellow_nodes: List[Dict],
        selected_agents: List[str]
    ) -> List[AgentTask]:
        """生成并发任务列表"""

        tasks = []

        for node in yellow_nodes:
            node_id = node.get("id", "")
            node_text = node.get("text", "")

            for agent_name in selected_agents:
                task = AgentTask(
                    task_id=f"{node_id}_{agent_name}_{uuid.uuid4().hex[:8]}",
                    agent_name=agent_name,
                    input_data={
                        "question_text": node.get("question_text", ""),
                        "user_understanding": node_text,
                        "reference_material": node.get("reference_material", "")
                    },
                    target_node_id=node_id,
                    estimated_duration=5.0
                )
                tasks.append(task)

        return tasks

    async def _execute_parallel(self, tasks: List[AgentTask]) -> List[TaskResult]:
        """并行执行所有任务"""

        semaphore = asyncio.Semaphore(self.max_concurrent_agents)

        async def execute_with_semaphore(task: AgentTask):
            async with semaphore:
                return await self.process_manager.execute_task(task)

        # 并发执行所有任务
        results = await asyncio.gather(
            *[execute_with_semaphore(task) for task in tasks],
            return_exceptions=True
        )

        # 处理异常结果
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append(TaskResult(
                    task_id="unknown",
                    agent_name="unknown",
                    target_node_id="unknown",
                    status="failed",
                    error_message=str(result)
                ))
            else:
                processed_results.append(result)

        return processed_results

    async def _execute_sequential(self, tasks: List[AgentTask]) -> List[TaskResult]:
        """顺序执行任务（用于测试）"""
        results = []
        for task in tasks:
            result = await self.process_manager.execute_task(task)
            results.append(result)
        return results

    async def _execute_hybrid(self, tasks: List[AgentTask]) -> List[TaskResult]:
        """混合执行：按Agent类型分组并行"""

        # 按Agent类型分组
        grouped_tasks = {}
        for task in tasks:
            category = AgentClassifier.classify_agent(task.agent_name)["executor"]
            if category not in grouped_tasks:
                grouped_tasks[category] = []
            grouped_tasks[category].append(task)

        # 逐组执行
        all_results = []
        for category, category_tasks in grouped_tasks.items():
            if category == "process_pool" and len(category_tasks) > 1:
                # 并行执行计算密集型任务
                results = await self._execute_parallel(category_tasks)
            else:
                # 其他类型顺序执行
                results = await self._execute_sequential(category_tasks)
            all_results.extend(results)

        return all_results

    async def shutdown(self):
        """关闭任务协调器"""
        await self.process_manager.shutdown()


class ContentValidator:
    """内容验证器"""

    def __init__(self):
        self.validation_rules = {
            "length_check": self._validate_content_length,
            "encoding_check": self._validate_encoding,
            "structure_check": self._validate_structure,
            "completeness_check": self._validate_completeness
        }

    async def validate_content(
        self,
        content: str,
        source_agent: str
    ) -> ValidationResult:
        """验证内容完整性"""

        result = ValidationResult()

        # 执行各项验证
        for rule_name, rule_func in self.validation_rules.items():
            try:
                validation_result = await rule_func(content, source_agent)
                result.merge(validation_result)
            except Exception as e:
                result.add_error(f"{rule_name}: {str(e)}")

        return result

    async def _validate_content_length(
        self,
        content: str,
        source_agent: str
    ) -> ValidationResult:
        """验证内容长度"""

        result = ValidationResult()

        # 检查是否被截断
        ellipsis_count = content.count("...")
        if ellipsis_count > 3:
            result.add_warning(f"检测到{ellipsis_count}个省略号，可能存在截断")

        # 检查预期长度
        expected_lengths = {
            "oral-explanation": (800, 1200),
            "clarification-path": (1500, 2500),
            "four-level-explanation": (1200, 1600)
        }

        if source_agent in expected_lengths:
            min_len, max_len = expected_lengths[source_agent]
            actual_len = len(content)

            if actual_len < min_len * 0.5:
                result.add_error(f"内容过短: {actual_len}字符 (预期: {min_len}-{max_len})")
            elif actual_len < min_len * 0.8:
                result.add_warning(f"内容较短: {actual_len}字符 (预期: {min_len}-{max_len})")

        return result

    async def _validate_encoding(self, content: str, source_agent: str) -> ValidationResult:
        """验证字符编码"""

        result = ValidationResult()

        try:
            # 测试UTF-8编码/解码
            encoded = content.encode('utf-8')
            decoded = encoded.decode('utf-8')

            if decoded != content:
                result.add_error("UTF-8编码验证失败")

        except UnicodeEncodeError as e:
            result.add_error(f"编码错误: {str(e)}")

        # 检查特殊字符
        problematic_chars = ['�', '\ufffd', '\x00']
        for char in problematic_chars:
            if char in content:
                result.add_error(f"检测到问题字符: {repr(char)}")

        return result

    async def _validate_structure(self, content: str, source_agent: str) -> ValidationResult:
        """验证内容结构"""

        result = ValidationResult()

        # 检查基本结构
        if not content.strip():
            result.add_error("内容为空")
            return result

        # 检查是否包含预期的结构元素
        if source_agent == "oral-explanation":
            required_elements = ["背景", "核心", "举例", "误区"]
            for element in required_elements:
                if element not in content:
                    result.add_warning(f"缺少{element}部分")

        elif source_agent == "clarification-path":
            required_elements = ["澄清", "拆解", "解释", "总结"]
            for element in required_elements:
                if element not in content:
                    result.add_warning(f"缺少{element}部分")

        return result

    async def _validate_completeness(self, content: str, source_agent: str) -> ValidationResult:
        """验证内容完整性"""

        result = ValidationResult()

        # 检查生成时间戳
        if "生成时间:" not in content:
            result.add_warning("缺少生成时间戳")

        # 检查Agent标识
        if source_agent not in content:
            result.add_warning("缺少Agent标识")

        return result


class ResultMerger:
    """结果融合器"""

    def __init__(self):
        self.content_validator = ContentValidator()

    async def merge_results(
        self,
        results: List[TaskResult],
        fusion_strategy: str = "complementary"
    ) -> Dict[str, Any]:
        """融合多个Agent的执行结果"""

        print(f"🔗 开始融合{len(results)}个Agent结果")

        # 1. 过滤成功的结果
        successful_results = [r for r in results if r.status == "success"]
        if not successful_results:
            raise ValueError("没有成功的Agent结果可以融合")

        # 2. 验证结果完整性
        validated_results = []
        for result in successful_results:
            content = result.result_data.get("content", "")
            validation = await self.content_validator.validate_content(
                content, result.agent_name
            )

            if validation.is_valid:
                validated_results.append(result)
            else:
                print(f"⚠️  {result.agent_name}结果验证失败: {validation.errors}")

        if not validated_results:
            raise ValueError("所有结果都未通过验证")

        # 3. 执行融合
        if fusion_strategy == "complementary":
            merged_content = await self._merge_complementary(validated_results)
        elif fusion_strategy == "supplementary":
            merged_content = await self._merge_supplementary(validated_results)
        else:
            merged_content = await self._merge_complementary(validated_results)

        # 4. 添加元数据
        merged_content["metadata"] = {
            "fusion_strategy": fusion_strategy,
            "agent_count": len(validated_results),
            "fusion_time": datetime.now().isoformat(),
            "source_agents": [r.agent_name for r in validated_results]
        }

        print(f"✅ 结果融合完成，使用了{len(validated_results)}个Agent的结果")
        return merged_content

    async def _merge_complementary(self, results: List[TaskResult]) -> Dict[str, Any]:
        """互补融合策略"""

        merged_content = {
            "sections": [],
            "cross_references": [],
            "summary_points": []
        }

        # 按Agent类型分组
        results_by_type = {}
        for result in results:
            agent_name = result.agent_name
            results_by_type[agent_name] = result.result_data

        # 构建互补内容结构
        section_order = [
            "oral-explanation",
            "clarification-path",
            "comparison-table",
            "memory-anchor",
            "four-level-explanation",
            "example-teaching"
        ]

        for agent_name in section_order:
            if agent_name in results_by_type:
                result = results_by_type[agent_name]
                content = result.get("content", "")

                # 确定标题
                titles = {
                    "oral-explanation": "🗣️ 教授式讲解",
                    "clarification-path": "🔍 深度澄清路径",
                    "comparison-table": "📊 概念对比表",
                    "memory-anchor": "⚓ 记忆锚点",
                    "four-level-explanation": "🎯 四层次解释",
                    "example-teaching": "📝 例题教学"
                }

                merged_content["sections"].append({
                    "type": agent_name,
                    "title": titles.get(agent_name, f"🤖 {agent_name}"),
                    "content": content
                })

        # 生成交叉引用
        merged_content["cross_references"] = self._generate_cross_references(
            merged_content["sections"]
        )

        # 生成要点总结
        merged_content["summary_points"] = self._extract_summary_points(
            merged_content["sections"]
        )

        return merged_content

    async def _merge_supplementary(self, results: List[TaskResult]) -> Dict[str, Any]:
        """补充融合策略"""
        # 实现略...
        return await self._merge_complementary(results)

    def _generate_cross_references(self, sections: List[Dict]) -> List[str]:
        """生成交叉引用"""

        references = []

        if len(sections) > 1:
            references.append("📖 以上分析从不同角度深入解释了相关概念")

            # 根据sections生成具体引用
            for i, section in enumerate(sections):
                if i < len(sections) - 1:
                    next_section = sections[i + 1]
                    references.append(
                        f"➡️  参见「{section['title']}」与「{next_section['title']}」的关联分析"
                    )

        return references

    def _extract_summary_points(self, sections: List[Dict]) -> List[str]:
        """提取要点总结"""

        summary_points = []

        # 从每个section中提取要点
        for section in sections:
            content = section.get("content", "")

            # 简单的要点提取逻辑
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('#') or line.startswith('*') or line.startswith('-'):
                    # 清理格式
                    point = line.lstrip('#*- ').strip()
                    if len(point) > 10 and len(point) < 200:
                        summary_points.append(point)

        # 去重并限制数量
        unique_points = []
        for point in summary_points:
            if point not in unique_points:
                unique_points.append(point)

        return unique_points[:10]  # 最多10个要点


class OptimizedCanvasWriter:
    """优化的Canvas写入器"""

    def __init__(self, canvas_path: str):
        self.canvas_path = canvas_path
        self.operator = CanvasJSONOperator
        self.backup_dir = Path(canvas_path).parent / ".backups"
        self.backup_dir.mkdir(exist_ok=True)

    async def write_merged_content(
        self,
        yellow_node_id: str,
        merged_content: Dict[str, Any],
        backup_enabled: bool = True
    ) -> bool:
        """写入融合后的内容到黄色节点"""

        print(f"✍️  开始写入节点 {yellow_node_id}")

        try:
            # 1. 创建备份
            if backup_enabled:
                await self._create_backup()

            # 2. 读取Canvas数据
            canvas_data = self.operator.read_canvas(self.canvas_path)

            # 3. 格式化内容
            formatted_content = await self._format_content_for_canvas(merged_content)

            # 4. 找到并更新黄色节点
            success = self._update_yellow_node(canvas_data, yellow_node_id, formatted_content)

            if not success:
                raise ValueError(f"黄色节点 {yellow_node_id} 不存在")

            # 5. 保存Canvas文件
            self.operator.write_canvas(self.canvas_path, canvas_data)

            # 6. 验证写入结果
            verification_success = await self._verify_write_result(
                yellow_node_id, formatted_content
            )

            if verification_success:
                print(f"✅ 节点 {yellow_node_id} 写入成功")
                return True
            else:
                print(f"⚠️  节点 {yellow_node_id} 写入验证失败")
                return False

        except Exception as e:
            print(f"❌ 节点 {yellow_node_id} 写入失败: {str(e)}")
            if backup_enabled:
                await self._restore_from_backup()
            raise CanvasWriteError(f"写入失败: {str(e)}")

    async def _create_backup(self):
        """创建Canvas文件备份"""

        canvas_file = Path(self.canvas_path)
        if not canvas_file.exists():
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"{canvas_file.stem}_{timestamp}{canvas_file.suffix}"

        try:
            import shutil
            shutil.copy2(canvas_file, backup_file)
            print(f"💾 备份已创建: {backup_file}")
        except Exception as e:
            print(f"⚠️  备份创建失败: {str(e)}")

    async def _format_content_for_canvas(self, merged_content: Dict[str, Any]) -> str:
        """为Canvas格式化内容"""

        formatted_parts = []

        # 添加标题
        formatted_parts.append("# 🤖 多Agent智能分析结果\n")

        # 添加各个section
        for section in merged_content.get("sections", []):
            formatted_parts.append(f"## {section['title']}\n")
            formatted_parts.append(f"{section['content']}\n\n")

        # 添加交叉引用
        if merged_content.get("cross_references"):
            formatted_parts.append("## 🔗 关联参考\n")
            for ref in merged_content["cross_references"]:
                formatted_parts.append(f"- {ref}\n")
            formatted_parts.append("\n")

        # 添加要点总结
        if merged_content.get("summary_points"):
            formatted_parts.append("## 💡 核心要点\n")
            for point in merged_content["summary_points"]:
                formatted_parts.append(f"- {point}\n")
            formatted_parts.append("\n")

        # 添加元数据
        metadata = merged_content.get("metadata", {})
        formatted_parts.append("---\n")
        formatted_parts.append(f"**融合策略**: {metadata.get('fusion_strategy', 'unknown')}\n")
        formatted_parts.append(f"**参与Agent数**: {metadata.get('agent_count', 0)}\n")
        formatted_parts.append(f"**生成时间**: {metadata.get('fusion_time', 'unknown')}\n")
        formatted_parts.append("**处理方式**: 多Agent并发分析 + 智能融合\n")

        return "".join(formatted_parts)

    def _update_yellow_node(
        self,
        canvas_data: Dict,
        node_id: str,
        content: str
    ) -> bool:
        """更新黄色节点内容"""

        for node in canvas_data.get("nodes", []):
            if node.get("id") == node_id:
                # 验证节点颜色
                if node.get("color") != "6":  # 黄色
                    print(f"⚠️  警告: 节点 {node_id} 不是黄色节点")

                node["text"] = content
                return True

        return False

    async def _verify_write_result(
        self,
        node_id: str,
        expected_content: str
    ) -> bool:
        """验证写入结果"""

        try:
            # 重新读取Canvas
            canvas_data = self.operator.read_canvas(self.canvas_path)

            # 找到节点并验证内容
            for node in canvas_data.get("nodes", []):
                if node.get("id") == node_id:
                    actual_content = node.get("text", "")

                    # 检查内容长度
                    if len(actual_content) < len(expected_content) * 0.9:
                        print(f"⚠️  内容长度检查失败: {len(actual_content)} vs {len(expected_content)}")
                        return False

                    # 检查关键字段
                    if "多Agent智能分析结果" not in actual_content:
                        print("⚠️  关键字段检查失败: 缺少分析结果标识")
                        return False

                    return True

            print(f"⚠️  验证失败: 节点 {node_id} 不存在")
            return False

        except Exception as e:
            print(f"⚠️  验证过程出错: {str(e)}")
            return False

    async def _restore_from_backup(self):
        """从备份恢复"""
        # 实现略...
        print("🔄 尝试从备份恢复...")


# ========== 主要接口类 ==========

class ConcurrentCanvasOrchestrator:
    """并发Canvas操作器 - 主要接口类"""

    def __init__(self, canvas_path: str, concurrent_enabled: bool = True):
        self.canvas_path = canvas_path
        self.concurrent_enabled = concurrent_enabled

        if concurrent_enabled:
            self.task_coordinator = TaskCoordinator()
            self.result_merger = ResultMerger()
            self.canvas_writer = OptimizedCanvasWriter(canvas_path)
            self.logic = CanvasBusinessLogic(canvas_path)

    async def initialize(self):
        """初始化并发系统"""
        if self.concurrent_enabled:
            await self.task_coordinator.initialize()

    async def concurrent_analyze_yellow_nodes(
        self,
        yellow_node_ids: List[str],
        selected_agents: List[str],
        analysis_mode: str = "parallel"
    ) -> Dict[str, Any]:
        """并发分析多个黄色节点

        Args:
            yellow_node_ids: 黄色节点ID列表
            selected_agents: 选择的Agent列表
            analysis_mode: 分析模式 ("parallel", "sequential", "hybrid")

        Returns:
            Dict: 分析结果报告
        """

        print(f"🎯 开始并发分析: {len(yellow_node_ids)}个节点, {len(selected_agents)}个Agent")
        session_id = str(uuid.uuid4())[:8]

        try:
            # 1. 读取黄色节点内容
            yellow_nodes = await self._extract_yellow_nodes(yellow_node_ids)

            if not yellow_nodes:
                raise ValueError("未找到有效的黄色节点")

            # 2. 执行并发分析
            analysis_results = await self.task_coordinator.coordinate_concurrent_analysis(
                self.canvas_path,
                yellow_nodes,
                selected_agents,
                analysis_mode
            )

            # 3. 融合结果并写入Canvas
            merged_results = {}
            successful_nodes = 0

            for node_id in yellow_node_ids:
                # 获取该节点的所有结果
                node_results = [
                    result for result in analysis_results["results"]
                    if result.target_node_id == node_id and result.status == "success"
                ]

                if node_results:
                    try:
                        # 融合结果
                        merged_content = await self.result_merger.merge_results(node_results)

                        # 写入Canvas
                        success = await self.canvas_writer.write_merged_content(
                            node_id, merged_content
                        )

                        merged_results[node_id] = {
                            "success": success,
                            "agent_count": len(node_results),
                            "content_length": len(str(merged_content))
                        }

                        if success:
                            successful_nodes += 1

                    except Exception as e:
                        print(f"❌ 节点 {node_id} 处理失败: {str(e)}")
                        merged_results[node_id] = {
                            "success": False,
                            "error": str(e),
                            "agent_count": len(node_results)
                        }
                else:
                    merged_results[node_id] = {
                        "success": False,
                        "error": "没有成功的Agent结果",
                        "agent_count": 0
                    }

            # 4. 生成最终报告
            total_time = analysis_results["total_time"]
            performance_improvement = analysis_results["performance_improvement"]

            report = {
                "session_id": session_id,
                "status": "completed",
                "total_nodes": len(yellow_node_ids),
                "successful_nodes": successful_nodes,
                "failed_nodes": len(yellow_node_ids) - successful_nodes,
                "total_time": total_time,
                "performance_improvement": performance_improvement,
                "node_results": merged_results,
                "analysis_statistics": analysis_results["statistics"],
                "selected_agents": selected_agents,
                "analysis_mode": analysis_mode
            }

            print(f"🎉 并发分析会话 {session_id} 完成!")
            print(f"   成功节点: {successful_nodes}/{len(yellow_node_ids)}")
            print(f"   总耗时: {total_time:.2f}秒")
            print(f"   性能提升: {performance_improvement:.1f}倍")

            return report

        except Exception as e:
            print(f"❌ 并发分析会话 {session_id} 失败: {str(e)}")
            raise ConcurrentAnalysisError(f"并发分析失败: {str(e)}")

    async def _extract_yellow_nodes(self, yellow_node_ids: List[str]) -> List[Dict]:
        """提取黄色节点数据"""

        canvas_data = self.operator.read_canvas(self.canvas_path)
        yellow_nodes = []

        for node_id in yellow_node_ids:
            for node in canvas_data.get("nodes", []):
                if node.get("id") == node_id and node.get("color") == "6":  # 黄色
                    # 查找关联的问题节点
                    question_node = self._find_related_question_node(
                        canvas_data, node_id
                    )

                    yellow_nodes.append({
                        "id": node_id,
                        "text": node.get("text", ""),
                        "question_text": question_node.get("text", "") if question_node else "",
                        "reference_material": ""
                    })
                    break

        return yellow_nodes

    def _find_related_question_node(self, canvas_data: Dict, yellow_node_id: str) -> Optional[Dict]:
        """查找与黄色节点关联的问题节点"""

        # 查找连接到黄色节点的边
        for edge in canvas_data.get("edges", []):
            if edge.get("to") == yellow_node_id:
                from_node_id = edge.get("from")

                # 找到来源节点
                for node in canvas_data.get("nodes", []):
                    if node.get("id") == from_node_id:
                        # 检查是否为问题节点（红色或紫色）
                        if node.get("color") in ["1", "3", "4"]:  # 红色、紫色
                            return node

        return None

    async def shutdown(self):
        """关闭并发系统"""
        if self.concurrent_enabled:
            await self.task_coordinator.shutdown()


# ========== 使用示例 ==========

async def example_usage():
    """使用示例"""

    # 配置
    canvas_path = "笔记库/离散数学/离散数学.canvas"
    yellow_node_ids = ["yellow-001", "yellow-002", "yellow-003"]  # 实际的黄色节点ID
    selected_agents = [
        "oral-explanation",
        "clarification-path",
        "comparison-table",
        "memory-anchor"
    ]

    # 创建并发操作器
    orchestrator = ConcurrentCanvasOrchestrator(
        canvas_path=canvas_path,
        concurrent_enabled=True
    )

    try:
        # 初始化
        await orchestrator.initialize()

        # 执行并发分析
        result = await orchestrator.concurrent_analyze_yellow_nodes(
            yellow_node_ids=yellow_node_ids,
            selected_agents=selected_agents,
            analysis_mode="parallel"  # 可选: "parallel", "sequential", "hybrid"
        )

        # 打印结果
        print("\n" + "="*50)
        print("并发分析结果报告")
        print("="*50)
        print(f"会话ID: {result['session_id']}")
        print(f"总节点数: {result['total_nodes']}")
        print(f"成功节点: {result['successful_nodes']}")
        print(f"失败节点: {result['failed_nodes']}")
        print(f"总耗时: {result['total_time']:.2f}秒")
        print(f"性能提升: {result['performance_improvement']:.1f}倍")
        print(f"分析模式: {result['analysis_mode']}")

        print("\n节点详情:")
        for node_id, node_result in result['node_results'].items():
            status = "✅ 成功" if node_result['success'] else "❌ 失败"
            agent_count = node_result.get('agent_count', 0)
            print(f"  {node_id}: {status} (Agent数: {agent_count})")
            if not node_result['success'] and 'error' in node_result:
                print(f"    错误: {node_result['error']}")

    except Exception as e:
        print(f"示例执行失败: {str(e)}")

    finally:
        # 清理资源
        await orchestrator.shutdown()


if __name__ == "__main__":
    """直接运行时的示例"""
    print("🚀 Canvas学习系统 v2.0 - 多Agent并发分析系统")
    print("=" * 60)

    # 检查依赖
    if not AIOMULTIPROCESS_AVAILABLE:
        print("⚠️  建议安装 aiomultiprocess 以获得最佳性能:")
        print("   pip install aiomultiprocess")

    if not PSUTIL_AVAILABLE:
        print("⚠️  建议安装 psutil 以启用性能监控:")
        print("   pip install psutil")

    print("\n📖 使用方法:")
    print("1. 导入: from concurrent_canvas_system import ConcurrentCanvasOrchestrator")
    print("2. 创建: orchestrator = ConcurrentCanvasOrchestrator(canvas_path)")
    print("3. 初始化: await orchestrator.initialize()")
    print("4. 分析: await orchestrator.concurrent_analyze_yellow_nodes(...)")

    # 运行示例（如果需要）
    run_example = input("\n是否运行示例? (y/N): ").lower().strip()
    if run_example == 'y':
        asyncio.run(example_usage())

    print("\n✅ 系统就绪!")