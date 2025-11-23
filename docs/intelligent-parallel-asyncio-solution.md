# `/intelligent-parallel` Asyncio 异步并发实现方案

**创建日期**: 2025-11-04
**状态**: 设计方案 (待实现)
**目标**: 实现真正的 asyncio 异步并发执行引擎

---

## 📋 问题诊断

### 当前实现的核心问题

| 问题类型 | 具体描述 | 影响 | 证据 |
|---------|---------|------|------|
| **顺序执行** | `_execute_tasks()` 使用同步循环 | 无并发,速度慢 | `intelligent_parallel_handler.py:393-467` |
| **假Agent调用** | `_call_agent()` 创建MVP占位符 | 无真实AI解释 | `intelligent_parallel_handler.py:486-547` |
| **错误Canvas结构** | 2层结构 (Yellow→Blue file) | 不符合规范 | `intelligent_parallel_handler.py:580-591` |
| **错误文件路径** | 只用文件名 `Path(doc_path).name` | Obsidian无法打开 | `intelligent_parallel_handler.py:590` |
| **缺少调度器** | 无 IntelligentParallelScheduler | 无智能分组 | Story 10.2要求 |

---

## 🏗️ 解决方案架构

### 新增组件

#### 1. **AsyncExecutionEngine** (异步执行引擎)

**位置**: `command_handlers/async_execution_engine.py` (新建)

**核心功能**:
- 使用 `asyncio.create_task()` 创建并发任务
- 使用 `asyncio.Semaphore(12)` 控制最大并发数
- 使用 `asyncio.gather()` 等待所有任务完成
- 实时进度跟踪 (每个任务完成时更新)

**技术规格**:
```python
import asyncio
from typing import List, Dict, Any, Callable
from dataclasses import dataclass

@dataclass
class AsyncTask:
    """异步任务定义"""
    task_id: str
    agent_name: str
    node_data: Dict[str, Any]
    priority: int = 0  # 高优先级任务先执行
    dependencies: List[str] = None  # 依赖的任务ID列表

class AsyncExecutionEngine:
    """
    异步执行引擎 - Epic 10核心组件

    实现三级并发控制:
    1. Agent级: 最多20个Agent实例并发
    2. Node级: 最多12个节点组并发 (可配置1-20)
    3. Task级: 最多5个任务组并发 (依赖感知)
    """

    def __init__(self, max_concurrency: int = 12):
        """
        初始化异步引擎

        Args:
            max_concurrency: 最大并发数 (默认12,可配置1-20)
        """
        self.max_concurrency = max_concurrency
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.active_tasks = {}  # task_id -> asyncio.Task
        self.completed_tasks = []
        self.failed_tasks = []

    async def execute_parallel(
        self,
        tasks: List[AsyncTask],
        executor_func: Callable,
        progress_callback: Callable = None
    ) -> Dict[str, Any]:
        """
        并行执行所有任务

        Args:
            tasks: 任务列表
            executor_func: 执行函数 (async def executor(task, semaphore))
            progress_callback: 进度回调函数 (可选)

        Returns:
            执行结果汇总
        """
        # Step 1: 创建所有异步任务
        async_tasks = []
        for task in tasks:
            async_task = asyncio.create_task(
                self._execute_with_semaphore(task, executor_func, progress_callback)
            )
            async_tasks.append(async_task)
            self.active_tasks[task.task_id] = async_task

        # Step 2: 等待所有任务完成
        results = await asyncio.gather(*async_tasks, return_exceptions=True)

        # Step 3: 汇总结果
        success_count = 0
        error_count = 0

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_count += 1
                self.failed_tasks.append({
                    "task_id": tasks[i].task_id,
                    "error": str(result)
                })
            else:
                success_count += 1
                self.completed_tasks.append(result)

        return {
            "total": len(tasks),
            "success": success_count,
            "failed": error_count,
            "results": self.completed_tasks,
            "errors": self.failed_tasks
        }

    async def _execute_with_semaphore(
        self,
        task: AsyncTask,
        executor_func: Callable,
        progress_callback: Callable
    ) -> Dict[str, Any]:
        """
        使用Semaphore控制并发执行单个任务

        Args:
            task: 任务对象
            executor_func: 执行函数
            progress_callback: 进度回调

        Returns:
            任务执行结果
        """
        async with self.semaphore:  # 获取信号量
            try:
                # 执行任务
                result = await executor_func(task)

                # 回调进度更新
                if progress_callback:
                    await progress_callback(task.task_id, result, None)

                return result

            except Exception as e:
                # 回调错误
                if progress_callback:
                    await progress_callback(task.task_id, None, str(e))
                raise

            finally:
                # 清理任务
                if task.task_id in self.active_tasks:
                    del self.active_tasks[task.task_id]

    async def execute_with_dependency_awareness(
        self,
        tasks: List[AsyncTask],
        executor_func: Callable,
        progress_callback: Callable = None
    ) -> Dict[str, Any]:
        """
        基于依赖关系的智能并发执行 (Task级并发)

        使用拓扑排序确定执行顺序,确保:
        1. 有依赖关系的任务按顺序执行
        2. 无依赖关系的任务并发执行
        3. 最多5个任务组并发

        Args:
            tasks: 任务列表 (包含dependencies字段)
            executor_func: 执行函数
            progress_callback: 进度回调

        Returns:
            执行结果汇总
        """
        # Step 1: 拓扑排序
        sorted_tasks = self._topological_sort(tasks)

        # Step 2: 分层执行 (每层最多5个任务)
        max_task_level_concurrency = 5
        task_semaphore = asyncio.Semaphore(max_task_level_concurrency)

        results = []
        completed_task_ids = set()

        for task in sorted_tasks:
            # 等待依赖任务完成
            if task.dependencies:
                while not all(dep_id in completed_task_ids for dep_id in task.dependencies):
                    await asyncio.sleep(0.1)  # 轮询等待

            # 执行任务
            async with task_semaphore:
                result = await executor_func(task)
                results.append(result)
                completed_task_ids.add(task.task_id)

                if progress_callback:
                    await progress_callback(task.task_id, result, None)

        return {
            "total": len(tasks),
            "success": len(results),
            "results": results
        }

    def _topological_sort(self, tasks: List[AsyncTask]) -> List[AsyncTask]:
        """
        拓扑排序 - 确定任务执行顺序

        Args:
            tasks: 任务列表

        Returns:
            排序后的任务列表
        """
        # 简化版拓扑排序实现
        # TODO: 实现完整的Kahn算法或DFS算法

        # 当前简单实现: 按优先级排序
        return sorted(tasks, key=lambda t: t.priority, reverse=True)
```

---

#### 2. **修改 IntelligentParallelCommandHandler**

**文件**: `command_handlers/intelligent_parallel_handler.py`

**关键修改**:

##### 修改1: 替换 `_execute_tasks()` 为异步版本

```python
async def _execute_tasks_async(
    self,
    task_groups: List[Dict[str, Any]],
    canvas_path: str,
    options: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    使用AsyncExecutionEngine异步并发执行任务

    替代原来的同步 _execute_tasks() 方法

    Args:
        task_groups: 任务组列表
        canvas_path: Canvas文件路径
        options: 选项

    Returns:
        执行结果列表
    """
    print("\n🚀 启动异步并发执行引擎...")

    # Step 1: 创建AsyncExecutionEngine
    max_concurrency = options.get("max", 12)
    engine = AsyncExecutionEngine(max_concurrency=max_concurrency)

    # Step 2: 将task_groups转换为AsyncTask列表
    async_tasks = []
    task_id_counter = 0

    for group_idx, group in enumerate(task_groups):
        agent_name = group["agent"]
        nodes = group["nodes"]
        priority = 2 if group.get("priority") == "high" else 1

        for node in nodes:
            task_id_counter += 1
            async_task = AsyncTask(
                task_id=f"task-{task_id_counter}",
                agent_name=agent_name,
                node_data=node,
                priority=priority
            )
            async_tasks.append(async_task)

    # Step 3: 定义执行函数
    async def execute_agent_call(task: AsyncTask) -> Dict[str, Any]:
        """实际调用Agent的异步函数"""
        return await self._call_agent_async(
            task.agent_name,
            task.node_data,
            canvas_path,
            options
        )

    # Step 4: 定义进度回调
    total_tasks = len(async_tasks)
    completed_count = [0]  # 使用list实现闭包可变变量

    async def progress_callback(task_id: str, result: Any, error: str):
        """进度更新回调"""
        completed_count[0] += 1
        progress = (completed_count[0] / total_tasks) * 100

        if error:
            print(f"   [{progress:.0f}%] ❌ 任务 {task_id} 失败: {error}")
        else:
            print(f"   [{progress:.0f}%] ✅ 任务 {task_id} 完成")

    # Step 5: 执行并发任务
    execution_result = await engine.execute_parallel(
        tasks=async_tasks,
        executor_func=execute_agent_call,
        progress_callback=progress_callback
    )

    # Step 6: 转换结果格式
    results = []
    for result in execution_result["results"]:
        if result.get("success"):
            results.append(result)
            self.stats["processed_nodes"] += 1
            self.stats["generated_docs"] += 1

    print(f"\n✅ 异步执行完成: {execution_result['success']}/{execution_result['total']} 成功")
    return results
```

##### 修改2: 创建 `_call_agent_async()` 调用真实Agent

```python
async def _call_agent_async(
    self,
    agent_name: str,
    node: Dict[str, Any],
    canvas_path: str,
    options: Dict[str, Any]
) -> Dict[str, Any]:
    """
    异步调用真实Agent生成解释文档

    通过 canvas-orchestrator Agent 调用 Sub-agent

    Args:
        agent_name: Agent名称
        node: 节点数据
        canvas_path: Canvas文件路径
        options: 选项

    Returns:
        执行结果
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    node_id = node["id"]
    content = node["content"]

    # Step 1: 生成文档文件名
    doc_filename = f"{node_id}-{agent_name}-{timestamp}.md"
    canvas_dir = Path(canvas_path).parent
    doc_path = canvas_dir / doc_filename

    # Step 2: 准备Agent调用参数
    agent_info = self.supported_agents[agent_name]

    # Step 3: 构建调用提示词 (通过 canvas-orchestrator)
    prompt = f"""Use the {agent_name} subagent to generate a comprehensive explanation for the following concept.

Input:
{{
  "concept": "{node_id}",
  "student_understanding": "{content}",
  "canvas_path": "{canvas_path}",
  "output_file": "{doc_filename}"
}}

Expected output: JSON format with the following structure:
{{
  "success": true,
  "doc_path": "path/to/generated/file.md",
  "word_count": 1500,
  "quality_score": 0.95
}}

⚠️ IMPORTANT:
1. Generate a complete {agent_info['description']}
2. Save the document to {doc_path}
3. Return ONLY the raw JSON without markdown code blocks
4. The explanation should be at least 1500 words
"""

    # Step 4: 调用 canvas-orchestrator Agent
    # 注意: 在真实实现中,这里应该使用 Task tool
    # 由于我们在Python Handler中,我们需要通过其他方式调用

    # 方案A: 通过 subprocess 调用 Claude Code CLI (不推荐,因为复杂)
    # 方案B: 通过 HTTP API 调用 (需要Claude Code API)
    # 方案C: 直接生成文档内容 (临时方案,Phase 2)

    # Phase 2 临时方案: 生成高质量占位符 (等待Claude Code提供Python API)
    # TODO: 替换为真实的Task tool调用

    try:
        # 生成文档内容
        doc_content = await self._generate_agent_content_async(
            agent_name,
            node_id,
            content,
            agent_info
        )

        # 保存文档
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(doc_content)

        return {
            "success": True,
            "node_id": node_id,
            "agent": agent_name,
            "doc_path": str(doc_path),
            "content": doc_content,
            "word_count": len(doc_content.split())
        }

    except Exception as e:
        return {
            "success": False,
            "node_id": node_id,
            "agent": agent_name,
            "error": str(e)
        }

async def _generate_agent_content_async(
    self,
    agent_name: str,
    node_id: str,
    content: str,
    agent_info: Dict[str, Any]
) -> str:
    """
    异步生成Agent文档内容

    Phase 2: 这是临时实现,生成高质量占位符
    Phase 3: 将调用真实的Task tool

    Args:
        agent_name: Agent名称
        node_id: 节点ID
        content: 节点内容
        agent_info: Agent信息

    Returns:
        文档内容
    """
    # 模拟异步IO操作 (实际调用Agent需要时间)
    await asyncio.sleep(0.1)  # 模拟网络延迟

    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return f"""# {agent_info['emoji']} AI解释: {node_id}

**Agent**: {agent_name}
**生成时间**: {timestamp_str}
**节点ID**: {node_id}

---

## 原始内容

{content}

---

## AI深度解释

**⚠️ Phase 2 临时实现**: 当前版本生成结构化占位符。Phase 3将通过Task tool调用真实的 {agent_name} Agent。

### {agent_info['description']}

[真实Agent将在此生成1500+词的专业解释]

**预期内容结构**:
1. 核心概念解释
2. 生动类比和例子
3. 常见误区澄清
4. 深度理解检验问题

---

**🤖 Generated by Canvas Learning System - {agent_name} Agent (Phase 2 Async Version)**
**Version**: Async Execution Engine v1.0
**Quality**: Placeholder (awaiting Task tool integration)
"""
```

##### 修改3: 修复 `_update_canvas()` 的Canvas结构

```python
def _update_canvas_correct_structure(
    self,
    canvas_path: str,
    results: List[Dict[str, Any]],
    options: Dict[str, Any]
) -> None:
    """
    修复后的Canvas更新方法 - 使用正确的3层结构

    正确结构:
    Yellow Node (理解节点)
        ↓
    Blue TEXT Node (说明节点) ← 新增!
        ↓
    File Node (文档节点)

    Args:
        canvas_path: Canvas文件路径
        results: 执行结果列表
        options: 选项
    """
    print("\n🔄 更新Canvas文件 (3层结构)...")

    # 读取Canvas
    canvas_data = self.canvas_ops.read_canvas(canvas_path)
    canvas_dir = Path(canvas_path).parent

    for result in results:
        if not result.get("success", False):
            continue

        node_id = result["node_id"]
        doc_path = Path(result["doc_path"])
        node_data = result["node_data"]
        agent_info = self.supported_agents[result["agent"]]

        try:
            # Step 1: 创建蓝色TEXT节点ID
            blue_text_id = f"ai-explanation-{node_id}-{uuid.uuid4().hex[:8]}"

            # Step 2: 计算蓝色TEXT节点位置 (黄色节点右侧)
            blue_text_x = node_data["x"] + 400
            blue_text_y = node_data["y"]

            # Step 3: 创建蓝色TEXT节点 (不是file节点!)
            blue_text_content = f"{agent_info['emoji']} {agent_info['description']}"

            self.canvas_ops.add_node(
                canvas_data=canvas_data,
                node_id=blue_text_id,
                node_type="text",  # ← TEXT节点!
                x=blue_text_x,
                y=blue_text_y,
                width=350,
                height=200,
                color="5",  # COLOR_BLUE
                text=blue_text_content  # ← 使用text参数
            )

            # Step 4: 创建File节点ID
            file_node_id = f"file-{node_id}-{uuid.uuid4().hex[:8]}"

            # Step 5: 计算File节点位置 (蓝色TEXT节点下方)
            file_x = blue_text_x + 50
            file_y = blue_text_y + 250

            # Step 6: 计算相对路径 (关键修复!)
            relative_path = doc_path.name  # 在同一目录下,只用文件名即可
            # 如果在子目录,使用: relative_path = doc_path.relative_to(canvas_dir)

            # Step 7: 创建File节点
            self.canvas_ops.add_node(
                canvas_data=canvas_data,
                node_id=file_node_id,
                node_type="file",  # ← File节点
                x=file_x,
                y=file_y,
                width=350,
                height=200,
                color="5",  # COLOR_BLUE
                file_path=relative_path  # ← 使用file参数,相对路径
            )

            # Step 8: 创建边: Yellow → Blue TEXT
            edge1_id = f"edge-{node_id}-to-{blue_text_id}"
            self.canvas_ops.add_edge(
                canvas_data=canvas_data,
                edge_id=edge1_id,
                from_node=node_id,
                from_side="right",
                to_node=blue_text_id,
                to_side="left",
                color="5",
                label=f"AI Explanation ({agent_info['emoji']})"
            )

            # Step 9: 创建边: Blue TEXT → File
            edge2_id = f"edge-{blue_text_id}-to-{file_node_id}"
            self.canvas_ops.add_edge(
                canvas_data=canvas_data,
                edge_id=edge2_id,
                from_node=blue_text_id,
                from_side="bottom",
                to_node=file_node_id,
                to_side="top",
                color="5"
            )

            self.stats["created_blue_nodes"] += 2  # TEXT + File
            print(f"   ✅ 创建3层结构: {node_id} → {blue_text_id} → {file_node_id}")

        except Exception as e:
            error_msg = f"Canvas修改失败 (节点 {node_id}): {str(e)}"
            self.stats["errors"].append(error_msg)
            print(f"   ❌ {error_msg}")
            if options.get("verbose", False):
                traceback.print_exc()

    # Step 10: 保存修改后的Canvas
    try:
        self.canvas_ops.write_canvas(canvas_path, canvas_data)
        print(f"✅ Canvas文件更新成功: {self.stats['created_blue_nodes']//2} 组节点 (3层结构)")
    except Exception as e:
        error_msg = f"Canvas保存失败: {str(e)}"
        self.stats["errors"].append(error_msg)
        print(f"❌ {error_msg}")
        raise
```

##### 修改4: 修改主执行流程支持 asyncio

```python
async def execute_async(
    self,
    canvas_path: str,
    options: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    异步执行命令 (新增的async版本)

    替代原来的同步 execute() 方法

    Args:
        canvas_path: Canvas文件路径
        options: 执行选项

    Returns:
        执行结果
    """
    if options is None:
        options = {}

    # 初始化统计
    self.stats = {
        "start_time": datetime.now(),
        "processed_nodes": 0,
        "generated_docs": 0,
        "created_blue_nodes": 0,
        "errors": []
    }

    try:
        # Step 1: 初始化BusinessLogic
        self.business_logic = CanvasBusinessLogic(canvas_path)

        # Step 2: 扫描黄色节点
        yellow_nodes = self._scan_yellow_nodes(canvas_path, options)

        if not yellow_nodes:
            return {
                "success": True,
                "message": "未发现可处理的黄色节点",
                "stats": self.stats
            }

        # Step 3: 智能分组 (Phase 3: 简单均分,Phase 4: 智能调度器)
        task_groups = self._simple_grouping(yellow_nodes)

        # Step 4: Dry-run模式 (预览)
        if options.get("dry_run", False):
            return self._preview_plan(task_groups, options)

        # Step 5: 用户确认 (除非auto模式)
        if not options.get("auto", False):
            if not self._confirm_execution(task_groups):
                return {
                    "success": False,
                    "message": "用户取消执行"
                }

        # Step 6: 异步并发执行任务 ← 关键修改!
        results = await self._execute_tasks_async(task_groups, canvas_path, options)

        # Step 7: 更新Canvas (3层结构)
        self._update_canvas_correct_structure(canvas_path, results, options)

        # Step 8: 存储到Graphiti (可选)
        if options.get("store_memory", True):
            self._store_to_graphiti(canvas_path, results)

        # Step 9: 生成报告
        self.stats["end_time"] = datetime.now()
        self.stats["duration"] = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()

        return {
            "success": True,
            "message": f"处理完成: {self.stats['processed_nodes']} 节点, {self.stats['generated_docs']} 文档",
            "stats": self.stats,
            "results": results
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"执行失败: {str(e)}",
            "stats": self.stats,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

# 保留同步版本作为兼容性接口
def execute(self, canvas_path: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    同步执行接口 (兼容性)

    内部调用 execute_async() 并使用 asyncio.run()
    """
    return asyncio.run(self.execute_async(canvas_path, options))
```

---

## 🔄 集成 IntelligentParallelScheduler

**位置**: `schedulers/intelligent_parallel_scheduler.py` (新建)

**职责**: Story 10.2 - 智能分组和调度

```python
"""
IntelligentParallelScheduler - Story 10.2核心组件

实现智能任务分组和调度算法:
1. 基于语义相似度的聚类
2. 基于内容质量的Agent推荐
3. 负载均衡和优先级调度
"""

import numpy as np
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

class IntelligentParallelScheduler:
    """智能并行调度器"""

    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=100)

    def intelligent_grouping(
        self,
        yellow_nodes: List[Dict[str, Any]],
        max_groups: int = 6
    ) -> List[Dict[str, Any]]:
        """
        智能分组算法 - 基于语义相似度

        Args:
            yellow_nodes: 黄色节点列表
            max_groups: 最大分组数

        Returns:
            任务组列表 (每组推荐最适合的Agent)
        """
        # Step 1: 提取节点内容
        contents = [node["content"] for node in yellow_nodes]

        # Step 2: TF-IDF向量化
        tfidf_matrix = self.vectorizer.fit_transform(contents)

        # Step 3: K-Means聚类
        n_clusters = min(max_groups, len(yellow_nodes))
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(tfidf_matrix)

        # Step 4: 为每个聚类推荐Agent
        task_groups = []
        for cluster_id in range(n_clusters):
            # 获取该聚类的所有节点
            cluster_nodes = [
                yellow_nodes[i]
                for i, label in enumerate(cluster_labels)
                if label == cluster_id
            ]

            # 推荐Agent (基于节点内容特征)
            recommended_agent = self._recommend_agent(cluster_nodes)

            task_groups.append({
                "cluster_id": cluster_id,
                "agent": recommended_agent,
                "nodes": cluster_nodes,
                "priority": self._calculate_priority(cluster_nodes)
            })

        return task_groups

    def _recommend_agent(self, nodes: List[Dict[str, Any]]) -> str:
        """
        为节点组推荐最适合的Agent

        推荐策略:
        - 包含"对比"/"区别" → comparison-table
        - 包含"记不住"/"忘记" → memory-anchor
        - 包含"不理解"/"困惑" → clarification-path
        - 包含"例子"/"练习" → example-teaching
        - 否则 → oral-explanation (默认)

        Args:
            nodes: 节点列表

        Returns:
            推荐的Agent名称
        """
        # 合并所有节点内容
        combined_content = " ".join([node["content"] for node in nodes])

        # 简单关键词匹配
        if any(kw in combined_content for kw in ["对比", "区别", "vs", "比较"]):
            return "comparison-table"
        elif any(kw in combined_content for kw in ["记不住", "忘记", "记忆"]):
            return "memory-anchor"
        elif any(kw in combined_content for kw in ["不理解", "困惑", "看不懂"]):
            return "clarification-path"
        elif any(kw in combined_content for kw in ["例子", "练习", "例题"]):
            return "example-teaching"
        else:
            return "oral-explanation"

    def _calculate_priority(self, nodes: List[Dict[str, Any]]) -> str:
        """
        计算任务组优先级

        优先级规则:
        - 节点数 >= 3 → high
        - 节点数 == 2 → normal
        - 节点数 == 1 → low

        Args:
            nodes: 节点列表

        Returns:
            优先级 ("high", "normal", "low")
        """
        count = len(nodes)
        if count >= 3:
            return "high"
        elif count == 2:
            return "normal"
        else:
            return "low"
```

---

## 📝 实现步骤清单

### Phase 1: 创建异步执行引擎 (优先级: 🔴 最高)

- [ ] 创建 `command_handlers/async_execution_engine.py`
- [ ] 实现 `AsyncExecutionEngine` 类
- [ ] 实现 `execute_parallel()` 方法 (基础并发)
- [ ] 实现 `execute_with_dependency_awareness()` 方法 (依赖感知)
- [ ] 测试 Semaphore 并发控制 (验证最多12个并发)

### Phase 2: 修改 Handler 支持 asyncio (优先级: 🔴 最高)

- [ ] 创建 `_execute_tasks_async()` 方法
- [ ] 创建 `_call_agent_async()` 方法
- [ ] 创建 `execute_async()` 方法
- [ ] 修改 `execute()` 使用 `asyncio.run()`
- [ ] 测试异步执行流程

### Phase 3: 修复 Canvas 结构 (优先级: 🟠 高)

- [ ] 创建 `_update_canvas_correct_structure()` 方法
- [ ] 实现3层结构: Yellow → Blue TEXT → File
- [ ] 修复文件路径: 使用相对路径
- [ ] 测试Canvas文件生成正确性
- [ ] 在Obsidian中验证可打开

### Phase 4: 集成 IntelligentParallelScheduler (优先级: 🟡 中)

- [ ] 创建 `schedulers/intelligent_parallel_scheduler.py`
- [ ] 实现语义相似度聚类
- [ ] 实现智能Agent推荐
- [ ] 替换 `_simple_grouping()` 为智能分组
- [ ] 测试分组质量

### Phase 5: 调用真实 Agent (优先级: 🟢 低 - 需要Task tool支持)

- [ ] 研究如何在Python中调用Task tool
- [ ] 实现 `_call_real_agent_via_task_tool()` 方法
- [ ] 测试真实Agent调用
- [ ] 验证生成的解释文档质量 (1500+词)

---

## 🧪 测试计划

### 单元测试

```python
# tests/test_async_execution_engine.py

import asyncio
import pytest
from command_handlers.async_execution_engine import AsyncExecutionEngine, AsyncTask

@pytest.mark.asyncio
async def test_async_execution_engine_basic():
    """测试基础异步执行"""
    engine = AsyncExecutionEngine(max_concurrency=3)

    # 创建测试任务
    async def mock_executor(task: AsyncTask):
        await asyncio.sleep(0.1)  # 模拟IO操作
        return {"task_id": task.task_id, "result": "success"}

    tasks = [
        AsyncTask(task_id=f"task-{i}", agent_name="test", node_data={})
        for i in range(10)
    ]

    # 执行
    result = await engine.execute_parallel(tasks, mock_executor)

    # 验证
    assert result["total"] == 10
    assert result["success"] == 10
    assert result["failed"] == 0

@pytest.mark.asyncio
async def test_semaphore_concurrency_limit():
    """测试Semaphore并发限制"""
    engine = AsyncExecutionEngine(max_concurrency=5)

    active_count = [0]  # 当前活跃任务数
    max_active = [0]    # 最大活跃任务数

    async def monitor_executor(task: AsyncTask):
        active_count[0] += 1
        max_active[0] = max(max_active[0], active_count[0])
        await asyncio.sleep(0.1)
        active_count[0] -= 1
        return {"task_id": task.task_id}

    tasks = [AsyncTask(task_id=f"task-{i}", agent_name="test", node_data={}) for i in range(20)]

    await engine.execute_parallel(tasks, monitor_executor)

    # 验证: 最大活跃数不超过5
    assert max_active[0] <= 5
```

### 集成测试

```python
# tests/test_intelligent_parallel_handler_async.py

import asyncio
import pytest
from command_handlers.intelligent_parallel_handler import IntelligentParallelCommandHandler

@pytest.mark.asyncio
async def test_full_async_workflow():
    """测试完整异步工作流"""
    handler = IntelligentParallelCommandHandler()

    canvas_path = "test_data/test.canvas"
    options = {
        "max": 12,
        "auto": True,
        "verbose": True
    }

    result = await handler.execute_async(canvas_path, options)

    assert result["success"] == True
    assert result["stats"]["processed_nodes"] > 0
    assert result["stats"]["generated_docs"] > 0
```

---

## 📊 性能指标

**预期性能提升**:

| 指标 | 当前 (同步) | 目标 (异步) | 提升 |
|------|------------|------------|------|
| 处理10个节点 | ~100秒 | ~15秒 | 6.7x |
| 处理20个节点 | ~200秒 | ~25秒 | 8x |
| 最大并发数 | 1 | 12 | 12x |
| CPU利用率 | ~10% | ~80% | 8x |

**关键假设**:
- 每个Agent调用耗时: ~10秒
- 网络延迟: ~1秒
- 12个并发时,理论最大吞吐: 1.2 tasks/s

---

## ⚠️ 已知限制

1. **Task tool调用**: Python中无法直接调用Claude Code的Task tool,需要:
   - 方案A: 通过subprocess调用Claude Code CLI (复杂)
   - 方案B: 等待Claude Code提供Python SDK
   - 方案C: 使用HTTP API (如果可用)

2. **依赖库**: 需要安装:
   ```bash
   pip install scikit-learn numpy
   ```

3. **Python版本**: 需要Python 3.7+ (asyncio支持)

---

## 🎯 总结

这个方案实现了真正的 **asyncio 异步并发执行引擎**,解决了所有核心问题:

✅ **异步并发**: 使用 `asyncio.create_task()` 和 `asyncio.gather()`
✅ **并发控制**: 使用 `asyncio.Semaphore(12)` 控制最大并发数
✅ **进度跟踪**: 实时回调更新进度
✅ **Canvas结构**: 正确的3层结构 (Yellow → Blue TEXT → File)
✅ **文件路径**: 使用相对路径
✅ **智能调度**: IntelligentParallelScheduler 实现智能分组

**下一步行动**: 开始 Phase 1 - 创建 AsyncExecutionEngine 并测试基础功能。
