"""
Canvas并行处理集成引擎 - Story 10.4实现

本模块实现Canvas学习系统的并行处理功能，包括：
- 并行任务分发和管理
- 结果聚合和Canvas更新
- 处理进度监控
- 事务性文件操作

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-24
Story: 10.4 - Canvas并行处理集成引擎
"""

import asyncio
import json
import os
import re
import tempfile
import shutil
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import threading
import time

# 导入Canvas 3层架构
from canvas_utils import CanvasJSONOperator, CanvasBusinessLogic, CanvasOrchestrator

# 导入并行处理组件（Epic 10）
try:
    from agent_instance_pool import GLMInstancePool, AgentTask
    from glm_rate_limiter import GLMRateLimiter
    PARALLEL_COMPONENTS_AVAILABLE = True
except ImportError:
    PARALLEL_COMPONENTS_AVAILABLE = False

# 导入事务管理器
from transaction_manager import FileTransactionManager, transaction_manager

# 尝试导入loguru日志
try:
    from loguru import logger
    LOGURU_ENABLED = True
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    LOGURU_ENABLED = False


# ========== 数据模型定义 ==========

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NodeComplexity(Enum):
    """节点复杂度枚举"""
    LOW = "low"       # 简单节点，<100字符
    MEDIUM = "medium" # 中等节点，100-500字符
    HIGH = "high"     # 复杂节点，>500字符


class LoadBalanceStrategy(Enum):
    """负载均衡策略枚举"""
    ROUND_ROBIN = "round_robin"
    COMPLEXITY_BASED = "complexity_based"
    PERFORMANCE_BASED = "performance_based"


@dataclass
class ProcessingTask:
    """并行处理任务数据模型"""
    task_id: str
    node_id: str
    agent_type: str
    node_data: Dict
    complexity: NodeComplexity
    estimated_time: float  # 预估处理时间(秒)
    assigned_instance: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict] = None
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0


@dataclass
class ProcessingSession:
    """并行处理会话数据模型"""
    session_id: str
    canvas_path: str
    tasks: List[ProcessingTask] = field(default_factory=list)
    total_nodes: int = 0
    completed_nodes: int = 0
    failed_nodes: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING

    @property
    def progress_percentage(self) -> float:
        """计算进度百分比"""
        if self.total_nodes == 0:
            return 0.0
        return (self.completed_nodes / self.total_nodes) * 100

    @property
    def estimated_completion_time(self) -> Optional[datetime]:
        """估算完成时间"""
        if self.completed_nodes == 0:
            return None
        elapsed = (datetime.now() - self.start_time).total_seconds()
        avg_time_per_node = elapsed / self.completed_nodes
        remaining_nodes = self.total_nodes - self.completed_nodes
        eta_seconds = avg_time_per_node * remaining_nodes
        return datetime.now() + timedelta(seconds=eta_seconds)


@dataclass
class CanvasUpdateResult:
    """Canvas更新结果数据模型"""
    update_id: str
    session_id: str
    nodes_updated: int
    nodes_created: int
    edges_updated: int
    update_time: datetime = field(default_factory=datetime.now)
    conflicts_resolved: int = 0
    backup_path: Optional[str] = None
    success: bool = True
    error_details: List[str] = field(default_factory=list)


@dataclass
class TaskDistributionConfig:
    """任务分发配置"""
    enable_complexity_analysis: bool = True
    load_balance_strategy: LoadBalanceStrategy = LoadBalanceStrategy.ROUND_ROBIN
    max_tasks_per_instance: int = 10
    task_timeout: int = 300  # 5分钟
    retry_failed_tasks: bool = True
    max_retries: int = 3
    enable_progress_monitoring: bool = True
    concurrent_limit: int = 5  # 最大并发数


@dataclass
class NodeComplexityMetrics:
    """节点复杂度评估指标"""
    node_id: str
    text_length: int
    has_math_formulas: bool
    has_code_blocks: bool
    has_images: bool
    connection_count: int  # 连接边数量
    depth_level: int  # 在Canvas中的层级深度
    complexity_score: float  # 0-100的综合复杂度分数

    def calculate_complexity(self) -> NodeComplexity:
        """计算节点复杂度等级"""
        if self.complexity_score < 30:
            return NodeComplexity.LOW
        elif self.complexity_score < 70:
            return NodeComplexity.MEDIUM
        else:
            return NodeComplexity.HIGH


# ========== 核心类定义 ==========

class ParallelCanvasProcessor:
    """Canvas并行处理集成引擎核心类

    负责协调并行处理的各个组件，包括任务分发、结果聚合、
    Canvas更新和进度监控等功能。
    """

    def __init__(self,
                 canvas_utils: CanvasOrchestrator,
                 instance_pool: Optional['GLMInstancePool'] = None,
                 rate_limiter: Optional['GLMRateLimiter'] = None,
                 config: Optional[TaskDistributionConfig] = None):
        """初始化Canvas并行处理器

        Args:
            canvas_utils: Canvas操作工具（Layer 3）
            instance_pool: GLM实例池（可选）
            rate_limiter: 速率限制器（可选）
            config: 任务分发配置（可选）
        """
        self.canvas_utils = canvas_utils
        self.instance_pool = instance_pool
        self.rate_limiter = rate_limiter
        self.config = config or TaskDistributionConfig()

        # 内部状态
        self.active_sessions: Dict[str, ProcessingSession] = {}
        self.session_history: List[ProcessingSession] = []
        self._file_lock = threading.Lock()

        # 初始化子组件
        self.task_distributor = TaskDistributor(self.config)
        self.result_aggregator = ResultAggregator(canvas_utils)
        self.progress_monitor = ProgressMonitor()
        self.transaction_manager = transaction_manager

        # Canvas 3层架构集成
        self.layer1_operator = CanvasJSONOperator  # Layer 1: 底层JSON操作
        self.layer2_business = CanvasBusinessLogic  # Layer 2: 业务逻辑
        self.layer3_orchestrator = canvas_utils    # Layer 3: 高级接口

        logger.info(f"ParallelCanvasProcessor initialized with strategy: {self.config.load_balance_strategy.value}")

    async def analyze_canvas_complexity(self, canvas_path: str) -> List[NodeComplexityMetrics]:
        """分析Canvas中节点的复杂度

        Args:
            canvas_path: Canvas文件路径

        Returns:
            List[NodeComplexityMetrics]: 节点复杂度指标列表
        """
        logger.info(f"Analyzing canvas complexity: {canvas_path}")

        # 读取Canvas文件
        canvas_data = self.canvas_utils.logic.canvas_data.read_canvas(canvas_path)
        nodes = canvas_data.get('nodes', [])

        metrics = []

        for node in nodes:
            # 分析节点特征
            text_length = len(node.get('text', ''))
            text = node.get('text', '')

            # 检测特殊内容
            has_math_formulas = bool(re.search(r'\$\$.*?\$\$|\\[a-zA-Z]+\{', text))
            has_code_blocks = '```' in text or '`' in text
            has_images = node.get('type') == 'file' and node.get('file', '').endswith(('.png', '.jpg', '.jpeg', '.gif'))

            # 计算连接数（需要遍历edges）
            connection_count = 0
            node_id = node.get('id')
            for edge in canvas_data.get('edges', []):
                if edge.get('fromNode') == node_id or edge.get('toNode') == node_id:
                    connection_count += 1

            # 估算深度层级（基于y坐标）
            depth_level = max(1, int(node.get('y', 0) / 400))

            # 计算复杂度分数
            complexity_score = self._calculate_complexity_score(
                text_length, has_math_formulas, has_code_blocks,
                has_images, connection_count, depth_level
            )

            metric = NodeComplexityMetrics(
                node_id=node_id,
                text_length=text_length,
                has_math_formulas=has_math_formulas,
                has_code_blocks=has_code_blocks,
                has_images=has_images,
                connection_count=connection_count,
                depth_level=depth_level,
                complexity_score=complexity_score
            )

            metrics.append(metric)

        logger.info(f"Analyzed {len(metrics)} nodes for complexity")
        return metrics

    def _calculate_complexity_score(self,
                                  text_length: int,
                                  has_math_formulas: bool,
                                  has_code_blocks: bool,
                                  has_images: bool,
                                  connection_count: int,
                                  depth_level: int) -> float:
        """计算节点复杂度分数（0-100）"""
        score = 0.0

        # 文本长度贡献（0-30分）
        if text_length < 100:
            score += text_length * 0.3
        elif text_length < 500:
            score += 30 + (text_length - 100) * 0.05
        else:
            score += 50 + min(20, (text_length - 500) * 0.02)

        # 特殊内容贡献（0-30分）
        if has_math_formulas:
            score += 15
        if has_code_blocks:
            score += 10
        if has_images:
            score += 5

        # 连接数贡献（0-20分）
        score += min(20, connection_count * 4)

        # 深度贡献（0-20分）
        score += min(20, depth_level * 4)

        return min(100.0, score)

    async def create_processing_session(self,
                                      canvas_path: str,
                                      agent_type: str,
                                      target_nodes: List[str],
                                      session_config: Optional[Dict] = None) -> ProcessingSession:
        """创建并行处理会话

        Args:
            canvas_path: Canvas文件路径
            agent_type: 要使用的Agent类型
            target_nodes: 目标节点ID列表
            session_config: 会话配置（可选）

        Returns:
            ProcessingSession: 创建的处理会话
        """
        session_id = str(uuid.uuid4())
        logger.info(f"Creating processing session {session_id} for {len(target_nodes)} nodes")

        # 创建会话
        session = ProcessingSession(
            session_id=session_id,
            canvas_path=canvas_path,
            total_nodes=len(target_nodes)
        )

        # 读取Canvas数据
        canvas_data = self.canvas_utils.logic.canvas_data.read_canvas(canvas_path)
        nodes_map = {node['id']: node for node in canvas_data.get('nodes', [])}

        # 分析节点复杂度
        complexity_metrics = await self.analyze_canvas_complexity(canvas_path)
        metrics_map = {m.node_id: m for m in complexity_metrics}

        # 创建处理任务
        tasks = []
        for node_id in target_nodes:
            if node_id not in nodes_map:
                logger.warning(f"Node {node_id} not found in canvas")
                continue

            node_data = nodes_map[node_id]
            metrics = metrics_map.get(node_id)

            if metrics:
                complexity = metrics.calculate_complexity()
                estimated_time = self._estimate_processing_time(complexity, agent_type)
            else:
                complexity = NodeComplexity.MEDIUM
                estimated_time = 30.0  # 默认30秒

            task = ProcessingTask(
                task_id=str(uuid.uuid4()),
                node_id=node_id,
                agent_type=agent_type,
                node_data=node_data,
                complexity=complexity,
                estimated_time=estimated_time
            )

            tasks.append(task)

        session.tasks = tasks
        session.total_nodes = len(tasks)

        # 保存会话
        self.active_sessions[session_id] = session

        logger.info(f"Created session {session_id} with {len(tasks)} tasks")
        return session

    def _estimate_processing_time(self, complexity: NodeComplexity, agent_type: str) -> float:
        """估算处理时间"""
        base_times = {
            'basic-decomposition': 10.0,
            'deep-decomposition': 20.0,
            'oral-explanation': 30.0,
            'clarification-path': 40.0,
            'comparison-table': 25.0,
            'memory-anchor': 20.0,
            'four-level-explanation': 35.0,
            'example-teaching': 30.0,
            'scoring-agent': 10.0,
            'verification-question-agent': 15.0
        }

        base_time = base_times.get(agent_type, 30.0)

        # 根据复杂度调整
        multipliers = {
            NodeComplexity.LOW: 0.5,
            NodeComplexity.MEDIUM: 1.0,
            NodeComplexity.HIGH: 2.0
        }

        return base_time * multipliers[complexity]

    async def distribute_tasks(self,
                              session: ProcessingSession,
                              available_instances: List[str]) -> Dict[str, List[ProcessingTask]]:
        """智能分发任务到可用实例

        Args:
            session: 处理会话
            available_instances: 可用实例ID列表

        Returns:
            Dict[str, List[ProcessingTask]]: 实例到任务列表的映射
        """
        logger.info(f"Distributing {len(session.tasks)} tasks to {len(available_instances)} instances")

        if not available_instances:
            logger.warning("No available instances for task distribution")
            return {}

        # 使用任务分发器进行分发
        distribution = await self.task_distributor.distribute_tasks_to_instances(
            session.tasks,
            available_instances,
            self.config.load_balance_strategy.value
        )

        # 更新任务的分配信息
        for instance_id, tasks in distribution.items():
            for task in tasks:
                task.assigned_instance = instance_id

        logger.info(f"Task distribution completed: {len(distribution)} instances assigned")
        return distribution

    async def execute_parallel_processing(self, session: ProcessingSession) -> ProcessingSession:
        """执行并行处理

        Args:
            session: 处理会话

        Returns:
            ProcessingSession: 更新后的会话
        """
        logger.info(f"Starting parallel processing for session {session.session_id}")
        session.status = TaskStatus.PROCESSING
        session.start_time = datetime.now()

        # 获取可用实例
        if self.instance_pool:
            available_instances = await self.instance_pool.get_available_instances()
        else:
            # 如果没有实例池，使用模拟实例
            available_instances = [f"instance-{i}" for i in range(self.config.concurrent_limit)]

        # 分发任务
        task_distribution = await self.distribute_tasks(session, available_instances)

        # 创建并发任务
        async_tasks = []
        semaphore = asyncio.Semaphore(self.config.concurrent_limit)

        for instance_id, tasks in task_distribution.items():
            for task in tasks:
                async_task = self._process_task_with_semaphore(semaphore, task, instance_id)
                async_tasks.append(async_task)

        # 等待所有任务完成
        await asyncio.gather(*async_tasks, return_exceptions=True)

        # 更新会话状态
        session.status = TaskStatus.COMPLETED
        session.end_time = datetime.now()

        logger.info(f"Parallel processing completed for session {session.session_id}")
        return session

    async def _process_task_with_semaphore(self,
                                         semaphore: asyncio.Semaphore,
                                         task: ProcessingTask,
                                         instance_id: str) -> None:
        """使用信号量控制并发的任务处理"""
        async with semaphore:
            await self._process_single_task(task, instance_id)

    async def _process_single_task(self, task: ProcessingTask, instance_id: str) -> None:
        """处理单个任务"""
        task.status = TaskStatus.PROCESSING
        task.started_at = datetime.now()

        try:
            # 这里应该调用实际的Agent进行处理
            # 暂时使用模拟处理
            logger.info(f"Processing task {task.task_id} on instance {instance_id}")

            # 模拟处理时间
            await asyncio.sleep(task.estimated_time / 10)  # 加速模拟

            # 模拟结果
            task.result = {
                "node_id": task.node_id,
                "agent_type": task.agent_type,
                "processed_content": f"Processed by {task.agent_type}",
                "timestamp": datetime.now().isoformat()
            }

            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()

        except Exception as e:
            logger.error(f"Task {task.task_id} failed: {e}")
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.now()

    async def aggregate_results(self, session: ProcessingSession) -> CanvasUpdateResult:
        """聚合处理结果并更新Canvas

        Args:
            session: 处理会话

        Returns:
            CanvasUpdateResult: Canvas更新结果
        """
        logger.info(f"Aggregating results for session {session.session_id}")

        # 使用结果聚合器进行聚合
        update_result = await self.result_aggregator.aggregate_and_apply_updates(session)

        # 更新会话历史
        self.session_history.append(session)
        if session.session_id in self.active_sessions:
            del self.active_sessions[session.session_id]

        logger.info(f"Results aggregated successfully: {update_result.nodes_updated} nodes updated")
        return update_result

    async def monitor_progress(self, session_id: str) -> Dict:
        """监控处理进度

        Args:
            session_id: 会话ID

        Returns:
            Dict: 进度信息
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}

        progress_info = {
            "session_id": session_id,
            "status": session.status.value,
            "total_nodes": session.total_nodes,
            "completed_nodes": session.completed_nodes,
            "failed_nodes": session.failed_nodes,
            "progress_percentage": session.progress_percentage,
            "start_time": session.start_time.isoformat() if session.start_time else None,
            "estimated_completion": session.estimated_completion_time.isoformat() if session.estimated_completion_time else None
        }

        # 添加任务状态详情
        task_status_counts = {}
        for task in session.tasks:
            status = task.status.value
            task_status_counts[status] = task_status_counts.get(status, 0) + 1

        progress_info["task_status_counts"] = task_status_counts

        return progress_info

    async def cancel_session(self, session_id: str) -> bool:
        """取消处理会话

        Args:
            session_id: 会话ID

        Returns:
            bool: 是否成功取消
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return False

        logger.info(f"Cancelling session {session_id}")

        # 更新任务状态
        for task in session.tasks:
            if task.status in [TaskStatus.PENDING, TaskStatus.PROCESSING]:
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.now()

        # 更新会话状态
        session.status = TaskStatus.CANCELLED
        session.end_time = datetime.now()

        # 移动到历史记录
        self.session_history.append(session)
        del self.active_sessions[session_id]

        return True

    async def get_session_history(self, canvas_path: str) -> List[ProcessingSession]:
        """获取处理会话历史

        Args:
            canvas_path: Canvas文件路径

        Returns:
            List[ProcessingSession]: 历史会话列表
        """
        history = [
            session for session in self.session_history
            if session.canvas_path == canvas_path
        ]

        # 按时间倒序排列
        history.sort(key=lambda s: s.start_time, reverse=True)

        return history


# ========== 辅助组件类 ==========

class TaskDistributor:
    """智能任务分发器"""

    def __init__(self, config: TaskDistributionConfig):
        self.config = config

    async def distribute_tasks_to_instances(self,
                                          tasks: List[ProcessingTask],
                                          instances: List[str],
                                          strategy: str = "round_robin") -> Dict[str, List[ProcessingTask]]:
        """将任务分发到实例"""
        distribution = {instance_id: [] for instance_id in instances}

        if strategy == "round_robin":
            self._distribute_round_robin(tasks, instances, distribution)
        elif strategy == "complexity_based":
            await self._distribute_complexity_based(tasks, instances, distribution)
        elif strategy == "performance_based":
            await self._distribute_performance_based(tasks, instances, distribution)
        else:
            # 默认使用轮询
            self._distribute_round_robin(tasks, instances, distribution)

        return distribution

    def _distribute_round_robin(self,
                               tasks: List[ProcessingTask],
                               instances: List[str],
                               distribution: Dict[str, List[ProcessingTask]]) -> None:
        """轮询分发策略"""
        for i, task in enumerate(tasks):
            instance_id = instances[i % len(instances)]
            distribution[instance_id].append(task)

    async def _distribute_complexity_based(self,
                                          tasks: List[ProcessingTask],
                                          instances: List[str],
                                          distribution: Dict[str, List[ProcessingTask]]) -> None:
        """基于复杂度的分发策略"""
        # 按复杂度排序
        sorted_tasks = sorted(tasks, key=lambda t: t.complexity.value, reverse=True)

        # 为每个实例维护复杂度总和
        instance_complexity = {instance_id: 0 for instance_id in instances}

        for task in sorted_tasks:
            # 选择当前复杂度最低的实例
            min_instance = min(instances, key=lambda i: instance_complexity[i])

            distribution[min_instance].append(task)
            instance_complexity[min_instance] += task.complexity.value

    async def _distribute_performance_based(self,
                                           tasks: List[ProcessingTask],
                                           instances: List[str],
                                           distribution: Dict[str, List[ProcessingTask]]) -> None:
        """基于性能的分发策略（暂时使用轮询）"""
        self._distribute_round_robin(tasks, instances, distribution)


class ResultAggregator:
    """结果聚合器"""

    def __init__(self, canvas_utils: CanvasOrchestrator):
        self.canvas_utils = canvas_utils
        self.transaction_manager = transaction_manager

    async def aggregate_and_apply_updates(self, session: ProcessingSession) -> CanvasUpdateResult:
        """聚合结果并应用到Canvas"""
        update_id = str(uuid.uuid4())

        try:
            # 创建备份
            backup_path = self.transaction_manager.create_backup(session.canvas_path)

            # 收集所有成功的结果
            successful_results = []
            failed_count = 0

            for task in session.tasks:
                if task.status == TaskStatus.COMPLETED and task.result:
                    successful_results.append(task.result)
                elif task.status == TaskStatus.FAILED:
                    failed_count += 1

            # 使用事务管理器更新Canvas
            def update_canvas_data(current_data: Dict) -> Dict:
                """更新Canvas数据 - 添加AI生成的解释节点

                为每个成功的AI处理结果创建蓝色解释节点，并连接到原始黄色节点。

                颜色规范:
                - 蓝色(5): AI生成的解释内容
                - 不使用红色(1)/紫色(3): 仅用于问题节点
                - 不使用黄色(6): 仅用于个人理解输出

                Args:
                    current_data: Canvas JSON数据

                Returns:
                    Dict: 更新后的Canvas数据，包含统计信息
                """
                updated_data = current_data.copy()

                # 统计信息
                nodes_created_count = 0
                edges_created_count = 0
                color_errors = []

                # 为每个成功的结果创建蓝色节点和边
                for task in session.tasks:
                    if task.status != TaskStatus.COMPLETED or not task.result:
                        continue

                    try:
                        # 1. 提取任务信息
                        yellow_node_id = task.node_id
                        agent_type = task.agent_type
                        result = task.result

                        # 2. 获取生成的.md文件路径
                        output_file = result.get('output_file') or result.get('file_path')
                        if not output_file:
                            logger.warning(f"Task {task.task_id} missing output_file")
                            continue

                        # 3. 查找黄色节点以确定位置
                        yellow_node = CanvasJSONOperator.find_node_by_id(
                            updated_data,
                            yellow_node_id
                        )

                        if not yellow_node:
                            logger.warning(f"Yellow node {yellow_node_id} not found")
                            continue

                        # 4. 计算蓝色节点位置（黄色节点右侧200px）
                        yellow_x = yellow_node.get('x', 0)
                        yellow_y = yellow_node.get('y', 0)
                        blue_x = yellow_x + 200
                        blue_y = yellow_y

                        # 5. 创建蓝色解释节点（file类型，链接到.md文件）
                        blue_node_id = CanvasJSONOperator.create_node(
                            updated_data,
                            node_type="file",
                            x=blue_x,
                            y=blue_y,
                            width=250,
                            height=150,
                            color="5",  # 蓝色 = AI生成内容
                            file=output_file
                        )
                        nodes_created_count += 1

                        # 6. 创建边: yellow -> blue
                        edge_id = CanvasJSONOperator.create_edge(
                            updated_data,
                            from_node=yellow_node_id,
                            to_node=blue_node_id,
                            label="AI解释"
                        )
                        edges_created_count += 1

                        logger.info(
                            f"Created blue node {blue_node_id} "
                            f"for agent {agent_type}, file: {output_file}"
                        )

                    except Exception as e:
                        logger.error(f"Failed to process task {task.task_id}: {e}")
                        color_errors.append(str(e))
                        continue

                # 7. 验证颜色合规性
                all_nodes = updated_data.get('nodes', [])
                new_nodes = all_nodes[-nodes_created_count:] if nodes_created_count > 0 else []

                for node in new_nodes:
                    node_color = node.get('color')
                    if node_color and node_color != '5':
                        error_msg = f"ERROR: Node {node['id']} has wrong color {node_color}, expected '5' (blue)"
                        logger.error(error_msg)
                        color_errors.append(error_msg)

                # 8. 添加统计信息到返回数据
                updated_data['_processing_stats'] = {
                    'nodes_created': nodes_created_count,
                    'edges_created': edges_created_count,
                    'color_errors': color_errors,
                    'timestamp': datetime.now().isoformat()
                }

                logger.info(
                    f"Canvas update complete: "
                    f"{nodes_created_count} nodes, "
                    f"{edges_created_count} edges, "
                    f"{len(color_errors)} errors"
                )

                return updated_data

            # 原子性更新Canvas文件
            self.transaction_manager.atomic_update_json(
                session.canvas_path,
                update_canvas_data
            )

            # 验证文件完整性
            if not self.transaction_manager.verify_file_integrity(session.canvas_path):
                raise Exception("Canvas file integrity check failed after update")

            nodes_updated = len(successful_results)
            nodes_created = 0  # 根据实际更新逻辑计算
            edges_updated = 0  # 根据实际更新逻辑计算

            update_result = CanvasUpdateResult(
                update_id=update_id,
                session_id=session.session_id,
                nodes_updated=nodes_updated,
                nodes_created=nodes_created,
                edges_updated=edges_updated,
                backup_path=backup_path,
                success=True
            )

            return update_result

        except Exception as e:
            logger.error(f"Failed to aggregate results: {e}")
            # 尝试从备份恢复
            try:
                self.transaction_manager.restore_from_backup(session.canvas_path, backup_path)
                logger.info(f"Restored {session.canvas_path} from backup after failure")
            except:
                logger.error("Failed to restore from backup")

            return CanvasUpdateResult(
                update_id=update_id,
                session_id=session.session_id,
                nodes_updated=0,
                nodes_created=0,
                edges_updated=0,
                success=False,
                error_details=[str(e)]
            )


class ProgressMonitor:
    """进度监控器"""

    def __init__(self):
        self.progress_callbacks = []

    def register_callback(self, callback):
        """注册进度回调函数"""
        self.progress_callbacks.append(callback)

    async def notify_progress(self, session_id: str, progress_info: Dict):
        """通知进度更新"""
        for callback in self.progress_callbacks:
            try:
                await callback(session_id, progress_info)
            except Exception as e:
                logger.error(f"Progress callback error: {e}")