"""
Agent性能优化模块

提供Agent执行的性能优化功能，包括：
- 并行处理
- 上下文管理
- 缓存机制
- 资源池管理

Author: Canvas Learning System Team
Version: 2.0
Created: 2025-01-22
"""

import asyncio
import time
import threading
import queue
from typing import Dict, List, Optional, Any, Callable
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from dataclasses import dataclass
import weakref
import functools


@dataclass
class AgentTask:
    """Agent任务数据类"""
    priority: int
    task_id: str
    agent_type: str
    input_data: Dict[str, Any]
    timeout: float = 30.0
    retry_count: int = 0
    max_retries: int = 2
    created_at: float = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()

    def __lt__(self, other):
        """定义小于比较，仅基于priority进行排序"""
        if not isinstance(other, AgentTask):
            return NotImplemented
        return self.priority < other.priority


@dataclass
class AgentResult:
    """Agent执行结果数据类"""
    task_id: str
    agent_type: str
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    started_at: float = 0.0
    completed_at: float = 0.0


class AgentPerformanceOptimizer:
    """Agent性能优化器"""

    def __init__(self,
                 max_workers: int = 5,
                 enable_caching: bool = True,
                 cache_size: int = 100,
                 enable_context_pooling: bool = True):
        self.max_workers = max_workers
        self.enable_caching = enable_caching
        self.cache_size = cache_size
        self.enable_context_pooling = enable_context_pooling

        # 执行器池
        self._thread_executor = ThreadPoolExecutor(max_workers=max_workers)
        self._process_executor = ProcessPoolExecutor(max_workers=max(2, max_workers // 2))

        # 任务队列
        self._task_queue = queue.PriorityQueue()
        self._running_tasks: Dict[str, AgentTask] = {}

        # 结果缓存
        self._result_cache: Dict[str, AgentResult] = {}
        self._cache_timestamps: Dict[str, float] = {}
        self._cache_lock = threading.RLock()

        # 上下文池
        self._context_pool: Dict[str, Any] = {}
        self._context_lock = threading.RLock()

        # 性能统计
        self._performance_stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "parallel_executions": 0,
            "total_execution_time": 0.0,
            "average_execution_time": 0.0
        }

        # 启动后台工作线程
        self._workers_running = True
        self._worker_threads = []
        for i in range(max_workers):
            worker = threading.Thread(target=self._worker_loop, daemon=True)
            worker.start()
            self._worker_threads.append(worker)

    def _worker_loop(self):
        """工作线程主循环"""
        while self._workers_running:
            try:
                # 获取任务（带超时）
                task = self._task_queue.get(timeout=1.0)
                self._execute_task(task)
                self._task_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"工作线程异常: {e}")

    def _execute_task(self, task: AgentTask):
        """执行单个Agent任务"""
        start_time = time.time()

        try:
            # 记录任务开始
            self._running_tasks[task.task_id] = task

            # 检查缓存
            if self.enable_caching:
                cached_result = self._get_cached_result(task)
                if cached_result:
                    self._performance_stats["cache_hits"] += 1
                    self._performance_stats["completed_tasks"] += 1
                    return cached_result
                else:
                    self._performance_stats["cache_misses"] += 1

            # 获取Agent执行函数
            agent_func = self._get_agent_function(task.agent_type)
            if not agent_func:
                raise ValueError(f"未知的Agent类型: {task.agent_type}")

            # 准备执行上下文
            context = self._prepare_context(task.agent_type)

            # 执行Agent
            if asyncio.iscoroutinefunction(agent_func):
                # 异步Agent
                result_data = asyncio.run(agent_func(task.input_data))
            else:
                # 同步Agent
                result_data = agent_func(task.input_data)

            # 创建成功结果
            result = AgentResult(
                task_id=task.task_id,
                agent_type=task.agent_type,
                success=True,
                result=result_data,
                execution_time=time.time() - start_time,
                started_at=start_time,
                completed_at=time.time()
            )

            # 缓存结果或临时存储
            if self.enable_caching:
                self._cache_result(task, result)
            else:
                # 当缓存禁用时，将结果临时存储用于wait_for_task查找
                with self._cache_lock:
                    self._result_cache[self._get_cache_key(task)] = result
                    self._cache_timestamps[self._get_cache_key(task)] = time.time()
                    # 限制非缓存模式的结果数量
                    if len(self._result_cache) > 50:  # 最多保存50个最近结果
                        oldest_key = min(self._cache_timestamps.items(), key=lambda item: item[1])[0]
                        del self._result_cache[oldest_key]
                        del self._cache_timestamps[oldest_key]

            # 清理上下文
            if self.enable_context_pooling:
                self._cleanup_context(task.agent_type, context)

            # 更新统计
            self._performance_stats["completed_tasks"] += 1
            self._performance_stats["total_execution_time"] += result.execution_time
            self._performance_stats["average_execution_time"] = (
                self._performance_stats["total_execution_time"] /
                self._performance_stats["completed_tasks"]
            )

        except Exception as e:
            # 创建失败结果
            result = AgentResult(
                task_id=task.task_id,
                agent_type=task.agent_type,
                success=False,
                error=str(e),
                execution_time=time.time() - start_time,
                started_at=start_time,
                completed_at=time.time()
            )

            # 重试逻辑
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                # 重新排队（降低优先级）
                task.priority += 1  # 更新优先级
                self._task_queue.put(task)
                print(f"任务 {task.task_id} 失败，准备重试 ({task.retry_count}/{task.max_retries})")
            else:
                self._performance_stats["failed_tasks"] += 1
                print(f"任务 {task.task_id} 最终失败: {e}")

        finally:
            # 清理运行任务记录
            self._running_tasks.pop(task.task_id, None)

    def _get_agent_function(self, agent_type: str) -> Optional[Callable]:
        """获取Agent执行函数"""
        # 这里应该根据agent_type返回对应的执行函数
        # 由于我们是在测试环境，返回模拟函数
        agent_functions = {
            "basic-decomposition": self._mock_basic_decomposition,
            "deep-decomposition": self._mock_deep_decomposition,
            "scoring-agent": self._mock_scoring_agent,
            "oral-explanation": self._mock_oral_explanation,
            "clarification-path": self._mock_clarification_path,
            "comparison-table": self._mock_comparison_table,
            "memory-anchor": self._mock_memory_anchor,
            "four-level-explanation": self._mock_four_level_explanation,
            "example-teaching": self._mock_example_teaching,
            "verification-question": self._mock_verification_question
        }

        return agent_functions.get(agent_type)

    def _prepare_context(self, agent_type: str) -> Any:
        """准备Agent执行上下文"""
        if not self.enable_context_pooling:
            return None

        with self._context_lock:
            if agent_type not in self._context_pool:
                # 创建新的上下文
                context = {
                    "agent_type": agent_type,
                    "created_at": time.time(),
                    "usage_count": 0
                }
                self._context_pool[agent_type] = context
            else:
                context = self._context_pool[agent_type]
                context["usage_count"] += 1

            return context

    def _cleanup_context(self, agent_type: str, context: Any):
        """清理Agent执行上下文"""
        # 这里可以添加上下文清理逻辑
        pass

    def _get_cache_key(self, task: AgentTask) -> str:
        """生成缓存键"""
        # 基于Agent类型和输入数据生成哈希键
        import hashlib
        import json

        input_str = json.dumps(task.input_data, sort_keys=True)
        hash_key = hashlib.md5(f"{task.agent_type}:{input_str}".encode()).hexdigest()
        return f"{task.agent_type}:{hash_key}"

    def _get_cached_result(self, task: AgentTask) -> Optional[AgentResult]:
        """获取缓存结果"""
        if not self.enable_caching:
            return None

        cache_key = self._get_cache_key(task)

        with self._cache_lock:
            if cache_key in self._result_cache:
                cached_result = self._result_cache[cache_key]
                # 检查缓存是否过期（1小时）
                if time.time() - cached_result.completed_at < 3600:
                    return cached_result
                else:
                    # 移除过期缓存
                    del self._result_cache[cache_key]
                    del self._cache_timestamps[cache_key]

        return None

    def _cache_result(self, task: AgentTask, result: AgentResult):
        """缓存结果"""
        if not self.enable_caching or not result.success:
            return

        cache_key = self._get_cache_key(task)

        with self._cache_lock:
            # 检查缓存大小限制
            if len(self._result_cache) >= self.cache_size:
                # 移除最旧的缓存项 - 简化实现避免比较问题
                oldest_items = sorted(self._cache_timestamps.items(), key=lambda item: item[1])
                if oldest_items:
                    oldest_key = oldest_items[0][0]
                    del self._result_cache[oldest_key]
                    del self._cache_timestamps[oldest_key]

            # 添加新缓存
            self._result_cache[cache_key] = result
            self._cache_timestamps[cache_key] = time.time()

    def submit_task(self, agent_type: str, input_data: Dict[str, Any],
                   priority: int = 0, timeout: float = 30.0) -> str:
        """提交Agent任务"""
        task_id = f"task-{int(time.time() * 1000)}-{len(self._running_tasks)}"

        task = AgentTask(
            priority=priority,  # 优先级作为第一个字段
            task_id=task_id,
            agent_type=agent_type,
            input_data=input_data,
            timeout=timeout
        )

        # 添加到队列
        self._task_queue.put(task)

        self._performance_stats["total_tasks"] += 1
        return task_id

    def submit_tasks_batch(self, tasks: List[Dict[str, Any]]) -> List[str]:
        """批量提交任务"""
        task_ids = []
        for task_data in tasks:
            task_id = self.submit_task(
                agent_type=task_data["agent_type"],
                input_data=task_data["input_data"],
                priority=task_data.get("priority", 0),
                timeout=task_data.get("timeout", 30.0)
            )
            task_ids.append(task_id)

        return task_ids

    def execute_parallel(self, tasks: List[Dict[str, Any]]) -> List[AgentResult]:
        """并行执行多个任务"""
        self._performance_stats["parallel_executions"] += 1

        # 提交所有任务
        task_ids = self.submit_tasks_batch(tasks)

        # 等待所有任务完成
        results = []
        for task_id in task_ids:
            result = self.wait_for_task(task_id)
            results.append(result)

        return results

    def wait_for_task(self, task_id: str, timeout: float = 60.0) -> AgentResult:
        """等待任务完成"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            # 检查缓存中的结果
            with self._cache_lock:
                for cached_result in self._result_cache.values():
                    if cached_result.task_id == task_id:
                        return cached_result

            # 检查运行中的任务是否已完成
            if task_id not in self._running_tasks:
                # 任务可能已完成，从缓存中查找
                for cached_result in self._result_cache.values():
                    if cached_result.task_id == task_id:
                        return cached_result

            time.sleep(0.1)  # 短暂等待

        raise TimeoutError(f"任务 {task_id} 在 {timeout} 秒内未完成")

    def get_task_status(self, task_id: str) -> str:
        """获取任务状态"""
        if task_id in self._running_tasks:
            return "running"

        # 检查缓存中是否有结果
        for cached_result in self._result_cache.values():
            if cached_result.task_id == task_id:
                return "completed" if cached_result.success else "failed"

        return "unknown"

    def cancel_task(self, task_id: str) -> bool:
        """取消任务（仅对排队中的任务有效）"""
        # 这是一个简化的实现
        # 在实际场景中，需要更复杂的队列管理
        return task_id not in self._running_tasks

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        stats = self._performance_stats.copy()
        stats.update({
            "queue_size": self._task_queue.qsize(),
            "running_tasks": len(self._running_tasks),
            "cache_size": len(self._result_cache),
            "context_pool_size": len(self._context_pool),
            "worker_threads": len(self._worker_threads),
            "success_rate": (
                stats["completed_tasks"] / max(1, stats["total_tasks"]) * 100
            )
        })
        return stats

    def clear_cache(self):
        """清空缓存"""
        with self._cache_lock:
            self._result_cache.clear()
            self._cache_timestamps.clear()

    def shutdown(self):
        """关闭优化器"""
        self._workers_running = False

        # 等待所有工作线程结束
        for worker in self._worker_threads:
            worker.join(timeout=5.0)

        # 关闭执行器
        self._thread_executor.shutdown(wait=True)
        self._process_executor.shutdown(wait=True)

    # Mock Agent functions for testing
    def _mock_basic_decomposition(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """模拟基础拆解Agent"""
        time.sleep(0.1)  # 模拟处理时间
        return {
            "sub_questions": [
                {"text": f"什么是{input_data.get('concept', '概念')}的基本定义？", "type": "定义型"},
                {"text": f"{input_data.get('concept', '概念')}的核心特征是什么？", "type": "特征型"}
            ],
            "total_count": 2
        }

    def _mock_deep_decomposition(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """模拟深度拆解Agent"""
        time.sleep(0.2)  # 模拟处理时间
        return {
            "deep_questions": [
                {"text": f"你理解的{input_data.get('concept', '概念')}和标准定义有何差异？", "type": "对比型"},
                {"text": f"如何验证你对{input_data.get('concept', '概念')}的理解？", "type": "验证型"}
            ],
            "total_count": 2
        }

    def _mock_scoring_agent(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """模拟评分Agent"""
        time.sleep(0.05)  # 模拟处理时间
        return {
            "accuracy_score": 20,
            "imagery_score": 18,
            "completeness_score": 22,
            "originality_score": 19,
            "total_score": 79,
            "color_transition": "purple"
        }

    def _mock_oral_explanation(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """模拟口语化解释Agent"""
        time.sleep(0.15)  # 模拟处理时间
        return {
            "explanation_type": "oral",
            "content": f"想象一下，{input_data.get('concept', '概念')}就像...",
            "style": "教授式讲解"
        }

    def _mock_clarification_path(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """模拟澄清路径Agent"""
        time.sleep(0.25)  # 模拟处理时间
        return {
            "clarification_type": "systematic",
            "steps": ["问题澄清", "概念拆解", "深度解释", "验证总结"]
        }

    def _mock_comparison_table(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """模拟对比表Agent"""
        time.sleep(0.1)  # 模拟处理时间
        return {
            "comparison_type": "table",
            "dimensions": ["定义", "特征", "应用场景"],
            "concepts": input_data.get("concepts", ["概念1", "概念2"])
        }

    def _mock_memory_anchor(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """模拟记忆锚点Agent"""
        time.sleep(0.08)  # 模拟处理时间
        return {
            "anchor_type": "mnemonic",
            "techniques": [
                f"生动类比：{input_data.get('concept', '概念')}就像...",
                f"记忆口诀：..."
            ]
        }

    def _mock_four_level_explanation(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """模拟四层次解释Agent"""
        time.sleep(0.3)  # 模拟处理时间
        return {
            "explanation_type": "four_level",
            "levels": {
                "新手": f"{input_data.get('concept', '概念')}的基本介绍",
                "进阶": f"{input_data.get('concept', '概念')}的深入理解",
                "专家": f"{input_data.get('concept', '概念')}的专业应用",
                "创新": f"{input_data.get('concept', '概念')}的前沿发展"
            }
        }

    def _mock_example_teaching(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """模拟例题教学Agent"""
        time.sleep(0.2)  # 模拟处理时间
        return {
            "teaching_type": "example_based",
            "sections": ["题目", "思路分析", "分步求解", "易错点提醒"],
            "concept": input_data.get("concept", "概念")
        }

    def _mock_verification_question(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """模拟检验问题生成Agent"""
        time.sleep(0.12)  # 模拟处理时间
        return {
            "question_type": "verification",
            "questions": [
                f"请解释{input_data.get('concept', '概念')}的核心原理",
                f"{input_data.get('concept', '概念')}在什么情况下不适用？"
            ]
        }


# 全局Agent性能优化器实例
_global_agent_optimizer: Optional[AgentPerformanceOptimizer] = None


def get_agent_optimizer() -> AgentPerformanceOptimizer:
    """获取全局Agent性能优化器实例"""
    global _global_agent_optimizer
    if _global_agent_optimizer is None:
        _global_agent_optimizer = AgentPerformanceOptimizer()
    return _global_agent_optimizer


def submit_agent_task(agent_type: str, input_data: Dict[str, Any]) -> str:
    """提交Agent任务（便捷函数）"""
    return get_agent_optimizer().submit_task(agent_type, input_data)


def execute_agents_parallel(tasks: List[Dict[str, Any]]) -> List[AgentResult]:
    """并行执行多个Agent任务（便捷函数）"""
    return get_agent_optimizer().execute_parallel(tasks)