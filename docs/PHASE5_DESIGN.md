# Phase 5 设计文档：异步并行执行系统

**Epic**: Epic 10 - Intelligent Parallel Processing System
**Phase**: Phase 5 - Async Parallel Execution
**设计日期**: 2025-11-04
**状态**: 设计中

---

## 🎯 Phase 5目标

实现**真正的异步并行执行**，使多个Agent调用能够同时进行，显著提升处理速度。

**核心指标**：
- 4个Agent任务并发执行
- 总执行时间 < Phase 4的50%
- 保持100%成功率
- 资源利用率优化

---

## 🏗️ 技术架构

### 当前架构（Phase 4）- 串行执行

```
Task 1 (clarification-path) → 等待完成 → 5-10秒
  ↓
Task 2 (oral-explanation) → 等待完成 → 5-10秒
  ↓
Task 3 (memory-anchor) → 等待完成 → 5-10秒
  ↓
Task 4 (memory-anchor) → 等待完成 → 5-10秒

总时间: 20-40秒（串行累加）
```

**问题**：即使使用Task tool的并行调用，实际上仍然是串行等待每个Agent完成。

### Phase 5架构 - 异步并行

```
Task 1 (clarification-path) ─┐
Task 2 (oral-explanation)    ├─→ asyncio.gather() → 并发执行
Task 3 (memory-anchor)       │
Task 4 (memory-anchor)       ┘

总时间: max(Task1, Task2, Task3, Task4) ≈ 5-10秒（最慢任务的时间）
```

**优势**：真正的并发执行，总时间由最慢的单个任务决定。

---

## 🔧 核心技术栈

### Python异步库

1. **asyncio**: 核心异步运行时
   ```python
   import asyncio

   async def call_agent_async(task):
       # 异步Agent调用
       pass

   async def main():
       tasks = [call_agent_async(t) for t in agent_tasks]
       results = await asyncio.gather(*tasks)
   ```

2. **aiofiles**: 异步文件I/O
   ```python
   import aiofiles

   async def save_result_async(path, content):
       async with aiofiles.open(path, 'w', encoding='utf-8') as f:
           await f.write(content)
   ```

3. **aiohttp** (可选): 异步HTTP请求
   - 如果未来需要通过API调用Agent

### Claude Code Task Tool的异步调用

**挑战**：Task tool本身是同步的，需要模拟异步行为。

**方案1**: 使用`asyncio.to_thread()`将同步调用转为异步
```python
async def call_task_async(agent_name, prompt):
    result = await asyncio.to_thread(
        call_task_sync,  # 同步的Task tool调用
        agent_name,
        prompt
    )
    return result
```

**方案2**: 使用`concurrent.futures.ThreadPoolExecutor`
```python
import concurrent.futures

async def call_task_async(agent_name, prompt):
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        result = await loop.run_in_executor(
            pool,
            call_task_sync,
            agent_name,
            prompt
        )
    return result
```

**推荐**：方案1更简洁，Python 3.9+原生支持。

---

## 📝 模块设计

### `scripts/async_intelligent_parallel.py`

**核心功能模块**：

```python
import asyncio
import aiofiles
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

class AsyncIntelligentParallel:
    """异步智能并行处理系统"""

    def __init__(self, state_file: str):
        """
        初始化异步系统

        Args:
            state_file: Phase 4准备的状态文件路径
        """
        self.state_file = state_file
        self.state = None
        self.results = []

    async def load_state(self):
        """异步加载状态文件"""
        async with aiofiles.open(self.state_file, 'r', encoding='utf-8') as f:
            content = await f.read()
            self.state = json.loads(content)

    async def call_agent_async(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        异步调用单个Agent

        Args:
            task: Agent任务配置

        Returns:
            执行结果
        """
        node_id = task['node_id']
        agent_name = task['agent_name']
        node_content = task['node_content']

        print(f"  [Start] {agent_name} → {node_id}")

        # 使用asyncio.to_thread包装同步Task调用
        result = await asyncio.to_thread(
            self._call_task_sync,
            agent_name,
            node_content,
            task['canvas_path']
        )

        print(f"  [Done] {agent_name} → {node_id}")

        return {
            "node_id": node_id,
            "agent_name": agent_name,
            "success": True,
            "content": result,
            "timestamp": datetime.now().isoformat()
        }

    def _call_task_sync(self, agent_name: str, content: str, canvas_path: str) -> str:
        """
        同步Task调用（由asyncio.to_thread调用）

        这是实际调用Claude Code Task tool的地方
        """
        # 构造Agent prompt
        prompt = self._build_agent_prompt(agent_name, content, canvas_path)

        # 调用Task tool (同步)
        # 注意：这里是伪代码，实际需要集成Claude Code的Task调用机制
        result = task_tool.call(subagent_type=agent_name, prompt=prompt)

        return result

    async def execute_parallel(self) -> List[Dict[str, Any]]:
        """
        并行执行所有Agent任务

        Returns:
            所有Agent的执行结果列表
        """
        agent_tasks = self.state['agent_tasks']

        print(f"\n🚀 Starting parallel execution: {len(agent_tasks)} tasks")

        # 创建异步任务列表
        tasks = [
            self.call_agent_async(task)
            for task in agent_tasks
        ]

        # 并发执行所有任务
        start_time = datetime.now()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = datetime.now()

        elapsed = (end_time - start_time).total_seconds()
        print(f"\n✅ All tasks completed in {elapsed:.2f} seconds")

        self.results = results
        return results

    async def save_results_async(self, output_file: str):
        """异步保存结果到JSON"""
        async with aiofiles.open(output_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(self.results, indent=2, ensure_ascii=False))

    async def run(self) -> Dict[str, Any]:
        """
        完整的异步执行流程

        Returns:
            执行统计信息
        """
        # Step 1: 加载状态
        await self.load_state()

        # Step 2: 并行执行
        results = await self.execute_parallel()

        # Step 3: 保存结果
        output_file = "agent_results_phase5.json"
        await self.save_results_async(output_file)

        # Step 4: 生成统计
        success_count = sum(1 for r in results if isinstance(r, dict) and r.get('success'))

        return {
            "total_tasks": len(results),
            "success_count": success_count,
            "success_rate": success_count / len(results),
            "output_file": output_file
        }


async def main():
    """主入口"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python async_intelligent_parallel.py <state_file>")
        sys.exit(1)

    state_file = sys.argv[1]

    system = AsyncIntelligentParallel(state_file)
    stats = await system.run()

    print("\n" + "="*60)
    print("Phase 5 Async Execution Summary")
    print("="*60)
    print(f"  Total tasks: {stats['total_tasks']}")
    print(f"  Success: {stats['success_count']}/{stats['total_tasks']}")
    print(f"  Success rate: {stats['success_rate']*100:.1f}%")
    print(f"  Results saved: {stats['output_file']}")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🔄 执行流程

### Phase 5 Workflow

```
1. 准备阶段（复用Phase 4）
   ├─ 使用 prepare_intelligent_parallel_phase4.py
   ├─ 生成 .intelligent_parallel_state_phase4_*.json
   └─ 包含智能分组结果

2. 异步执行阶段（Phase 5新增）
   ├─ 加载状态文件
   ├─ 创建异步任务列表
   ├─ asyncio.gather() 并发执行
   └─ 收集所有结果

3. Finalization阶段（修改）
   ├─ 异步保存结果到JSON
   ├─ 异步更新Canvas文件
   ├─ 异步保存文档到磁盘
   └─ Graphiti记忆存储

4. 报告阶段
   └─ 生成性能对比报告（Phase 4 vs Phase 5）
```

---

## 📊 性能目标

### 预期提升

假设单个Agent任务耗时8秒（平均）：

| Metric | Phase 4 (串行) | Phase 5 (并行) | 提升 |
|--------|---------------|---------------|------|
| **4个任务总时间** | 32秒 | 8秒 | **4倍** |
| **CPU利用率** | 25% | 80-100% | 3-4倍 |
| **I/O等待** | 75% | 20% | 降低55% |

**关键指标**：
- 总执行时间 < 10秒（4个任务）
- 成功率保持100%
- 内存使用 < 200MB

---

## 🧪 测试计划

### Phase 5测试用例

**Test Case 1: 基础并发测试**
- 输入: 4个黄色节点（复用Phase 4数据）
- 预期: 4个Agent并发执行，总时间<10秒
- 验证: 所有结果成功，文档质量不降低

**Test Case 2: 负载测试**
- 输入: 8个黄色节点
- 预期: 8个Agent并发执行
- 验证: 内存使用稳定，无OOM错误

**Test Case 3: 错误处理**
- 输入: 故意引入1个失败任务
- 预期: asyncio.gather(return_exceptions=True)捕获错误
- 验证: 其他任务继续执行，不被阻塞

**Test Case 4: 性能对比**
- 对比Phase 4和Phase 5的执行时间
- 验证: Phase 5至少快2倍

---

## 🚧 技术挑战

### Challenge 1: Task Tool的异步适配

**问题**: Claude Code的Task tool是同步调用，如何实现真正的异步？

**解决方案**:
- 使用`asyncio.to_thread()`将同步调用放入线程池
- 虽然底层仍是线程，但在Python层面实现了异步编排
- 可以并发执行多个Task调用

### Challenge 2: 文件I/O并发安全

**问题**: 多个Agent同时写入文档，可能冲突

**解决方案**:
- 每个Agent写入不同的文件（已有的设计）
- 使用`aiofiles`异步文件I/O，避免阻塞
- Canvas文件更新放在最后，串行执行

### Challenge 3: 错误传播和恢复

**问题**: 一个Agent失败时，如何不影响其他Agent？

**解决方案**:
- `asyncio.gather(return_exceptions=True)`
- 单个任务失败不会取消其他任务
- 在结果中标记失败任务，继续处理成功的

---

## 📈 对比分析框架

### Phase 4 vs Phase 5 Comparison Metrics

```python
comparison_report = {
    "phase_4": {
        "execution_model": "Sequential (pseudo-parallel Task calls)",
        "total_time": 25.3,  # seconds
        "avg_task_time": 6.3,
        "cpu_utilization": 30,
        "success_rate": 100
    },
    "phase_5": {
        "execution_model": "True Async Parallel (asyncio.gather)",
        "total_time": 7.8,   # seconds (目标)
        "avg_task_time": 6.3,  # 单任务时间不变
        "cpu_utilization": 90,
        "success_rate": 100
    },
    "improvement": {
        "speedup": 3.24,  # 25.3 / 7.8
        "time_saved": 17.5,  # seconds
        "efficiency_gain": "224%"
    }
}
```

---

## 🎯 实现里程碑

### Milestone 1: 异步框架搭建 ✅ (当前)
- 设计文档完成
- 架构确定

### Milestone 2: 核心模块开发
- 创建`async_intelligent_parallel.py`
- 实现AsyncIntelligentParallel类
- 集成asyncio + aiofiles

### Milestone 3: Task调用异步适配
- 实现`_call_task_sync()`
- 使用`asyncio.to_thread()`包装
- 测试并发调用

### Milestone 4: 完整流程测试
- 运行4任务并发测试
- 验证结果正确性
- 测量性能提升

### Milestone 5: 性能对比和报告
- 生成Phase 4 vs Phase 5对比报告
- 文档化最佳实践
- 更新Epic 10 README

---

## 🔮 未来扩展

### Phase 5+: 进一步优化

1. **动态并发控制**
   - 根据系统负载自动调整并发数
   - `asyncio.Semaphore`限制最大并发

2. **优先级队列**
   - 重要任务先执行
   - 使用`asyncio.PriorityQueue`

3. **实时进度反馈**
   - WebSocket推送进度更新
   - 进度条可视化

4. **分布式执行**
   - 跨多台机器并行
   - 使用Celery或Ray

---

## 📝 依赖要求

```txt
# Phase 5 Additional Dependencies
asyncio  # Python 3.7+ built-in
aiofiles>=23.0.0
aiohttp>=3.9.0  # 可选，用于HTTP异步调用
```

---

## ✅ 验收标准

Phase 5完成需满足：

1. ✅ 4个Agent任务真正并发执行
2. ✅ 总执行时间 < Phase 4的60%
3. ✅ 成功率保持100%
4. ✅ 文档质量不降低
5. ✅ 完整的性能对比报告

---

**下一步**: 实现`async_intelligent_parallel.py`模块，开始Milestone 2。
