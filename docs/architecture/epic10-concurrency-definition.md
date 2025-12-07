---
document_type: "Architecture"
version: "1.0.0"
last_modified: "2025-11-19"
status: "approved"
iteration: 1

authors:
  - name: "Architect Agent"
    role: "Solution Architect"

reviewers:
  - name: "PO Agent"
    role: "Product Owner"
    approved: true

compatible_with:
  prd: "v1.0"
  api_spec: "v1.0"

api_spec_hash: "0dc1d3610d28bf99"

changes_from_previous:
  - "Initial Architecture with frontmatter metadata"

git:
  commit_sha: ""
  tag: ""

metadata:
  components_count: 0
  external_services: []
  technology_stack:
    frontend: []
    backend: ["Python 3.11", "asyncio"]
    database: []
    infrastructure: []
---

# Epic 10 并发层次定义和限制

## 概述

Epic 10智能并行处理系统采用三级并发模型，通过在不同层级实施精细化的并发控制，实现系统性能和资源利用的最优化。

## 三级并发模型

### 第一级：Agent级别并发

**定义**: 单个节点的多个Agent并行处理

**场景**: 一个黄色理解节点需要多个Agent同时处理以提供全面支持

**技术实现**:
```python
# Story 10.1 - ReviewBoardAgentSelector
async def process_multiple_agents(
    self,
    node_id: str,
    agent_recommendations: List[str]
) -> Dict:
    """并行处理单个节点的多个推荐Agent"""
    semaphore = asyncio.Semaphore(100)  # 最多100个Agent并发
    tasks = []

    for agent_name in agent_recommendations:
        task = self._execute_agent_with_semaphore(
            semaphore, node_id, agent_name
        )
        tasks.append(task)

    results = await asyncio.gather(*tasks)
    return aggregate_results(results)
```

**并发限制**: **最大100个Agent**
- 基于系统资源限制（内存、CPU）
- 典型使用场景：5-10个Agent并发
- 深度分析场景：可达30-50个Agent
- 极限场景（充足资源）：可达100个Agent

**使用示例**:
```yaml
单节点多Agent处理场景:
  - 轻量运行: [clarification-path, comparison-table, memory-anchor] (3个)
  - 深度分析: [oral-explanation, four-level-explanation,
                clarification-path, example-teaching] (4个)
  - 全面支持: 最多100个不同类型的Agent
  - 典型场景: 5-10个Agent，充分利用多核CPU
```

---

### 第二级：节点级别并发

**定义**: 多个节点的批处理并发

**场景**: 多个黄色节点分组后并行处理不同的Agent任务

**技术实现**:
```python
# Story 10.2 - IntelligentParallelScheduler
async def execute_node_groups_parallel(
    self,
    task_groups: List[Dict]
) -> Dict:
    """并行执行多个节点组"""
    semaphore = asyncio.Semaphore(50)  # 最多50个组并发
    active_tasks = {}
    completed_groups = []

    # 智能任务调度
    for group in task_groups:
        if len(active_tasks) >= 50:
            # 等待某个任务完成
            done, pending = await asyncio.wait(
                active_tasks.values(),
                return_when=asyncio.FIRST_COMPLETED
            )
            completed_groups.extend(done)

            # 清理完成的任务
            for task in done:
                group_id = self._get_group_id_from_task(task)
                del active_tasks[group_id]

        # 启动新任务
        task = self._execute_group_with_semaphore(
            semaphore, group
        )
        active_tasks[group["group_id"]] = task

    # 等待所有任务完成
    if active_tasks:
        remaining = await asyncio.gather(*active_tasks.values())
        completed_groups.extend(remaining)

    return self._aggregate_group_results(completed_groups)
```

**并发限制**: **最多50个节点组**
- 基于系统资源（内存、CPU）和用户体验平衡
- 每个组内部可能包含多个Agent（但受第一级限制）
- 默认值，可通过--max参数调整（1-100）
- 资源充足时可动态提升到50个组

**资源分配**:
```yaml
典型节点级并发配置:
  default_concurrent_groups: 50
  max_concurrent_groups: 100
  memory_per_group: 200MB
  typical_agents_per_group: 3-5
```

---

### 第三级：任务级别并发

**定义**: 任务组的调度并发

**场景**: 有依赖关系的任务组按最优顺序执行

**技术实现**:
```python
# Story 10.2 - IntelligentParallelScheduler (优化版)
async def execute_with_dependency_awareness(
    self,
    task_groups: List[Dict],
    dependencies: Dict
) -> Dict:
    """基于依赖关系的智能并发执行"""
    # 使用拓扑排序确定执行顺序
    execution_order = self._topological_sort(
        task_groups, dependencies
    )

    # 创建执行队列
    ready_queue = asyncio.Queue()
    running_tasks = {}
    max_concurrent_tasks = 20  # 任务级并发限制

    # 初始化队列
    for group in execution_order:
        if not dependencies.get(group["group_id"]):
            await ready_queue.put(group)

    # 执行循环
    results = {}
    while not ready_queue.empty() or running_tasks:
        # 启动新任务（如果未达到并发限制）
        while (
            len(running_tasks) < max_concurrent_tasks
            and not ready_queue.empty()
        ):
            group = await ready_queue.get()
            task = self._execute_task_group(group)
            running_tasks[group["group_id"]] = (task, group)

        # 等待至少一个任务完成
        if running_tasks:
            done, pending = await asyncio.wait(
                [task for task, _ in running_tasks.values()],
                return_when=asyncio.FIRST_COMPLETED
            )

            # 处理完成的任务
            for task in done:
                group_id = self._get_group_id_from_task(task)
                result = await task
                results[group_id] = result

                # 从运行列表中移除
                _, group = running_tasks.pop(group_id)

                # 检查并释放依赖此任务的其他任务
                dependent_groups = self._find_dependent_groups(
                    group_id, task_groups, dependencies
                )
                for dep_group in dependent_groups:
                    if self._all_dependencies_met(
                        dep_group, results, dependencies
                    ):
                        await ready_queue.put(dep_group)

    return results
```

**并发限制**: **最多20个任务组**
- 考虑任务间的依赖关系
- 确保关键路径优先执行
- 基于依赖关系复杂度动态调整
- 充分利用系统并发能力

---

## 并发限制矩阵

| 并发层级 | 限制值 | 控制对象 | 典型场景 | 配置方式 |
|---------|--------|----------|----------|----------|
| **Agent级** | 100 | 单节点的Agent数量 | 深度学习、全面支持 | 系统资源限制 |
| **节点级** | 50 | 并行处理的节点组 | 批量处理、效率提升 | --max参数 |
| **任务级** | 20 | 有依赖的任务组 | 复杂工作流、有序执行 | 调度器内置 |
| **系统最大** | 500 | 总并发Agent实例 | 系统极限场景 | ResourceAwareScheduler |

### 并发计算示例

```python
# 场景1：单节点深度分析
node_1 = {
    "agents": 5,  # 5个Agent并发
    "groups": 1,  # 1个节点组
    "tasks": 1     # 1个任务
}
# 总并发：5个Agent

# 场景2：多节点批处理（迁移后）
nodes = [
    {"agents": 5, "groups": 1},  # 5个Agent
    {"agents": 3, "groups": 1},  # 3个Agent
    {"agents": 8, "groups": 1},  # 8个Agent
    # ... 共50个节点组
]
# 总并发：50个组 × 平均5个Agent = 250个Agent

# 场景3：复杂工作流（迁移后）
workflow = {
    "groups": 20,          # 20个任务组并行
    "agents_per_group": 10, # 每组10个Agent
    "nodes_per_group": 5    # 每组5个节点
}
# 总并发：20 × 10 = 200个Agent（受系统资源限制）
```

## 动态并发调整

### 自适应并发控制

```python
class AdaptiveConcurrencyController:
    """自适应并发控制器"""

    def __init__(self, initial_limits: Dict):
        self.limits = initial_limits
        self.performance_metrics = PerformanceMonitor()
        self.adjustment_factor = 1.2  # 调整因子

    async def adjust_concurrency(self):
        """基于性能指标动态调整并发限制"""
        current_metrics = await self.performance_metrics.get_metrics()

        # CPU使用率过高
        if current_metrics.cpu_usage > 80:
            self._reduce_concurrency("cpu")

        # 内存使用率过高
        if current_metrics.memory_usage > 80:
            self._reduce_concurrency("memory")

        # 响应时间过长（移除API限制检查）
        if current_metrics.avg_response_time > 5:
            self._reduce_concurrency("response_time")

        # 系统空闲，可以提升并发
        if (
            current_metrics.cpu_usage < 50
            and current_metrics.memory_usage < 50
        ):
            self._increase_concurrency()

    def _reduce_concurrency(self, reason: str):
        """减少并发限制"""
        if reason == "cpu" or reason == "memory":
            # 减少节点级并发
            self.limits["node_level"] = max(
                10,
                self.limits["node_level"] // self.adjustment_factor
            )
            # 减少Agent级并发
            self.limits["agent_level"] = max(
                10,
                self.limits["agent_level"] // self.adjustment_factor
            )

    def _increase_concurrency(self):
        """增加并发限制"""
        self.limits["node_level"] = min(
            100,
            int(self.limits["node_level"] * self.adjustment_factor)
        )
        self.limits["agent_level"] = min(
            100,
            int(self.limits["agent_level"] * self.adjustment_factor)
        )
```

### 优先级调度

```python
class PriorityAwareScheduler:
    """优先级感知调度器"""

    PRIORITY_LEVELS = {
        "urgent": 4,
        "high": 3,
        "normal": 2,
        "low": 1
    }

    async def schedule_with_priority(
        self,
        tasks: List[Dict],
        concurrency_limits: Dict
    ) -> Dict:
        """基于优先级的任务调度"""
        # 按优先级排序
        sorted_tasks = sorted(
            tasks,
            key=lambda x: self.PRIORITY_LEVELS.get(
                x.get("priority", "normal"),
                2
            ),
            reverse=True
        )

        # 优先级队列
        priority_queues = {
            level: asyncio.Queue()
            for level in self.PRIORITY_LEVELS
        }

        # 任务入队
        for task in sorted_tasks:
            priority = task.get("priority", "normal")
            await priority_queues[priority].put(task)

        # 按优先级执行
        results = {}
        for priority in ["urgent", "high", "normal", "low"]:
            while not priority_queues[priority].empty():
                task = await priority_queues[priority].get()

                # 调整并发限制（高优先级任务可以占用更多资源）
                if priority in ["urgent", "high"]:
                    boosted_limits = self._boost_limits(concurrency_limits)
                else:
                    boosted_limits = concurrency_limits

                result = await self._execute_with_limits(
                    task, boosted_limits
                )
                results[task["id"]] = result

        return results
```

## 监控和告警

### 关键指标

```yaml
监控指标:
  agent_level:
    - concurrent_agents_count
    - agent_execution_time
    - agent_success_rate
    - memory_per_agent

  node_level:
    - active_node_groups
    - group_processing_time
    - group_success_rate
    - memory_per_group

  task_level:
    - pending_tasks_count
    - dependency_resolution_time
    - task_throughput
    - system_utilization

  system_level:
    - total_memory_usage
    - cpu_usage_percent
    - concurrent_agent_instances
```

### 告警阈值

```python
ALERT_THRESHOLDS = {
    "agent_level": {
        "max_concurrent_reached": 100,     # 达到Agent级最大并发
        "agent_failure_rate": 0.1,        # Agent失败率>10%
        "memory_per_agent": 300            # 单Agent内存>300MB
    },
    "node_level": {
        "max_groups_reached": 50,         # 达到节点级最大并发
        "group_processing_time": 300,      # 组处理时间>5分钟
        "memory_per_group": 500            # 组内存>500MB
    },
    "task_level": {
        "pending_tasks_queue": 100,        # 待处理任务>100
        "dependency_cycle": True,          # 检测到依赖循环
        "system_cpu_usage": 0.9            # CPU使用率>90%
    },
    "system_level": {
        "total_memory_usage": 0.85,        # 系统内存使用>85%
        "total_agent_instances": 500       # 总Agent实例>500
    }
}
```

## 最佳实践

### 1. 并发配置建议

```yaml
# 轻量级使用（1-10个节点）
lightweight:
  agent_concurrency: 10
  node_concurrency: 10
  task_concurrency: 5

# 标准使用（10-50个节点）
standard:
  agent_concurrency: 30
  node_concurrency: 20
  task_concurrency: 10

# 重度使用（50-100个节点）
heavy:
  agent_concurrency: 60
  node_concurrency: 40
  task_concurrency: 15

# 极限使用（100+个节点，资源充足）
extreme:
  agent_concurrency: 100
  node_concurrency: 50
  task_concurrency: 20
```

### 2. 资源优化建议

- **CPU密集型任务**: 减少并发数，增加批处理大小
- **IO密集型任务**: 增加并发数，减少批处理大小
- **混合型任务**: 动态调整，基于实时性能指标

### 3. 错误处理策略

```python
async def execute_with_fallback(
    task: Dict,
    fallback_strategy: str = "sequential"
) -> Dict:
    """带回退策略的任务执行"""
    try:
        # 尝试并行执行
        return await execute_parallel(task)
    except ConcurrencyLimitExceeded:
        # 并发超限，回退到顺序执行
        if fallback_strategy == "sequential":
            return await execute_sequential(task)
        elif fallback_strategy == "reduced_concurrency":
            return await execute_with_reduced_concurrency(task)
    except ResourceExhausted:
        # 资源耗尽，等待后重试
        await asyncio.sleep(5)
        return await execute_with_fallback(
            task,
            fallback_strategy="reduced_concurrency"
        )
```

## ResourceAwareScheduler - 资源感知调度器（迁移后新增）

### 设计背景

迁移到LangGraph后，API并发限制被移除，系统并发能力不再受限于GLM-4.6 Max的API限制。为了充分利用这一优势，同时防止系统资源过载，引入**ResourceAwareScheduler**作为新的资源管理层。

### 核心职责

```python
class ResourceAwareScheduler:
    """
    资源感知调度器

    职责:
    1. 实时监控系统资源（内存、CPU）
    2. 动态调整并发限制
    3. 防止资源过载
    4. 优化资源利用率
    """

    def __init__(
        self,
        max_memory_percent: float = 80.0,
        max_cpu_percent: float = 80.0,
        initial_agent_concurrency: int = 100,
        initial_node_concurrency: int = 50,
        initial_task_concurrency: int = 20,
        min_concurrency: int = 10,
        adjustment_interval: float = 1.0
    ):
        """
        参数:
            max_memory_percent: 最大内存使用百分比（默认80%）
            max_cpu_percent: 最大CPU使用百分比（默认80%）
            initial_agent_concurrency: 初始Agent并发数（默认100）
            initial_node_concurrency: 初始节点并发数（默认50）
            initial_task_concurrency: 初始任务并发数（默认20）
            min_concurrency: 最小并发数（默认10）
            adjustment_interval: 调整间隔秒数（默认1.0秒）
        """
        self.max_memory_percent = max_memory_percent
        self.max_cpu_percent = max_cpu_percent

        # 并发限制（动态调整）
        self.agent_concurrency = initial_agent_concurrency
        self.node_concurrency = initial_node_concurrency
        self.task_concurrency = initial_task_concurrency

        # 边界值
        self.min_concurrency = min_concurrency
        self.max_agent_concurrency = 100
        self.max_node_concurrency = 100
        self.max_task_concurrency = 20

        # 调整参数
        self.adjustment_interval = adjustment_interval
        self.monitoring_task = None

    async def start_monitoring(self):
        """启动资源监控循环"""
        self.monitoring_task = asyncio.create_task(self._monitor_loop())

    async def stop_monitoring(self):
        """停止资源监控"""
        if self.monitoring_task:
            self.monitoring_task.cancel()

    async def _monitor_loop(self):
        """监控循环"""
        while True:
            try:
                await asyncio.sleep(self.adjustment_interval)
                await self._adjust_concurrency_by_resources()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Resource monitoring error: {e}")

    async def _adjust_concurrency_by_resources(self):
        """基于实时资源动态调整并发数"""
        import psutil

        memory_percent = psutil.virtual_memory().percent
        cpu_percent = psutil.cpu_percent(interval=0.1)

        # 资源压力过高（>90%），紧急降低并发
        if memory_percent > 90 or cpu_percent > 90:
            self.agent_concurrency = self.min_concurrency
            self.node_concurrency = self.min_concurrency
            self.task_concurrency = max(5, self.min_concurrency // 2)
            logging.warning(
                f"Emergency concurrency reduction: "
                f"Memory={memory_percent}%, CPU={cpu_percent}%"
            )

        # 资源压力较高（80-90%），降低并发
        elif memory_percent > 80 or cpu_percent > 80:
            self.agent_concurrency = max(
                self.min_concurrency,
                int(self.agent_concurrency * 0.7)
            )
            self.node_concurrency = max(
                self.min_concurrency,
                int(self.node_concurrency * 0.7)
            )
            self.task_concurrency = max(
                5,
                int(self.task_concurrency * 0.7)
            )
            logging.info(
                f"Concurrency reduction: "
                f"Memory={memory_percent}%, CPU={cpu_percent}%"
            )

        # 资源充足（<50%），提升并发
        elif memory_percent < 50 and cpu_percent < 60:
            self.agent_concurrency = min(
                self.max_agent_concurrency,
                int(self.agent_concurrency * 1.3)
            )
            self.node_concurrency = min(
                self.max_node_concurrency,
                int(self.node_concurrency * 1.3)
            )
            self.task_concurrency = min(
                self.max_task_concurrency,
                int(self.task_concurrency * 1.2)
            )
            logging.debug(
                f"Concurrency increase: "
                f"Memory={memory_percent}%, CPU={cpu_percent}%"
            )

    def get_current_limits(self) -> Dict[str, int]:
        """获取当前并发限制"""
        return {
            "agent_concurrency": self.agent_concurrency,
            "node_concurrency": self.node_concurrency,
            "task_concurrency": self.task_concurrency
        }
```

### 集成示例

```python
# Story 10.1 - ReviewBoardAgentSelector集成
class ReviewBoardAgentSelector:
    def __init__(self, resource_scheduler: ResourceAwareScheduler):
        self.resource_scheduler = resource_scheduler

    async def process_multiple_agents(
        self,
        node_id: str,
        agent_recommendations: List[str]
    ) -> Dict:
        """使用动态并发限制处理Agent"""
        # 获取当前并发限制
        limits = self.resource_scheduler.get_current_limits()
        current_limit = limits["agent_concurrency"]

        # 创建动态Semaphore
        semaphore = asyncio.Semaphore(current_limit)

        # ... 执行任务
```

### 性能优势

| 场景 | 旧限制（API限制） | 新限制（资源感知） | 性能提升 |
|------|-----------------|-------------------|---------|
| 轻量任务（CPU<30%） | 20 agents | 100 agents | **5倍** |
| 标准任务（CPU 50-70%） | 20 agents | 60 agents | **3倍** |
| 重度任务（CPU>80%） | 20 agents | 10-20 agents | **持平（保护）** |
| 100节点批处理 | 12组 × 3agent = 36并发 | 50组 × 5agent = 250并发 | **7倍** |

### 监控指标

```yaml
resource_scheduler_metrics:
  current_limits:
    - agent_concurrency_current
    - node_concurrency_current
    - task_concurrency_current

  system_resources:
    - memory_percent
    - cpu_percent
    - available_memory_gb

  adjustment_events:
    - concurrency_increase_count
    - concurrency_decrease_count
    - emergency_reduction_count
```

---

## 总结

Epic 10的三级并发模型（迁移后版本）提供了精细化的并发控制能力：

1. **Agent级**: 单节点深度并行，最多100个Agent（基于系统资源）
2. **节点级**: 多节点批处理，默认50个组，可调至100个
3. **任务级**: 有序工作流执行，最多20个并发任务
4. **ResourceAwareScheduler**: 实时资源监控和动态并发调整

**关键变化**（相比迁移前）:
- ✅ 移除API并发限制（GLM-4.6 Max限制移除）
- ✅ 并发值大幅提升（Agent: 20→100, Node: 12→50, Task: 5→20）
- ✅ 引入ResourceAwareScheduler资源感知调度器
- ✅ 性能提升3-7倍（不同场景）

通过动态调整、优先级调度、资源感知监控和告警，系统能够在各种场景下保持最优性能和资源利用效率，同时充分利用LangGraph迁移带来的并发能力提升。
