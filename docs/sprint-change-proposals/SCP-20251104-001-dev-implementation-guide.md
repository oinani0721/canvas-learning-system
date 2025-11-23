# Dev Agent 实现指南：修复 /intelligent-parallel Canvas集成

**关联提案**: SCP-20251104-001
**分配给**: Dev Agent
**预计工作量**: 4-6小时开发 + 2-3小时测试
**优先级**: 🔴 高
**截止日期**: 2025-11-05

---

## 📋 任务概览

修复 `/intelligent-parallel` 命令中缺失的Agent调用和Canvas集成功能。

**核心问题**:
- `ConcurrentAgentProcessor._execute_with_semaphore()` 只返回模拟结果
- Agent从未被真正调用
- Canvas集成协调器已实现但未被使用

**目标**:
- 实现真实的Sub-agent调用
- 将生成的内容集成到Canvas中
- 创建蓝色解释节点和黄色总结节点

---

## 🎯 实现任务清单

### 任务1: 实现 `_call_subagent()` 方法
**文件**: `canvas_utils.py`
**位置**: `ConcurrentAgentProcessor` 类中（约第1629行后）
**预计时间**: 2小时

#### 1.1 方法签名
```python
async def _call_subagent(
    self,
    agent_name: str,
    node_content: str,
    canvas_path: str,
    node_id: str = None
) -> Dict[str, Any]:
    """调用Sub-agent生成内容

    Args:
        agent_name: Agent类型名称（如 'clarification-path'）
        node_content: 黄色节点的文本内容
        canvas_path: Canvas文件路径
        node_id: 节点ID

    Returns:
        Dict: Agent生成结果
        {
            "agent_name": str,
            "content": str,  # 生成的解释内容
            "node_id": str,
            "metadata": {
                "timestamp": str,
                "model": str,
                "word_count": int
            }
        }
    """
```

#### 1.2 实现细节

**步骤1: 构建Agent调用语句**
```python
# 使用现有的Sub-agent调用协议
call_statement = f"""
Use the {agent_name} subagent to generate explanation for the following content.

Content to analyze:
{node_content}

Canvas context:
- File: {canvas_path}
- Node ID: {node_id}

Expected output: Generate detailed explanation according to the {agent_name} agent's specification.

⚠️ IMPORTANT: Return ONLY the raw content. Do NOT wrap it in JSON or markdown code blocks.
"""
```

**步骤2: 执行Agent调用**
```python
try:
    # 使用Task工具调用Sub-agent
    from anthropic import Anthropic

    # 初始化客户端（如果尚未初始化）
    if not hasattr(self, '_anthropic_client'):
        self._anthropic_client = Anthropic()

    # 调用Agent
    response = self._anthropic_client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4000,
        messages=[{
            "role": "user",
            "content": call_statement
        }]
    )

    # 提取内容
    generated_content = response.content[0].text

    return {
        "agent_name": agent_name,
        "content": generated_content,
        "node_id": node_id,
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "model": response.model,
            "word_count": len(generated_content.split())
        },
        "success": True
    }

except Exception as e:
    logger.error(f"Sub-agent调用失败: {agent_name}, 错误: {e}")
    return {
        "agent_name": agent_name,
        "content": None,
        "node_id": node_id,
        "error": str(e),
        "success": False
    }
```

**注意事项**:
- 使用现有的Sub-agent调用协议（参考 `canvas_utils.py` 中的 CanvasOrchestrator）
- 处理超时和错误
- 记录日志

---

### 任务2: 修复 `_execute_with_semaphore()` 方法
**文件**: `canvas_utils.py`
**位置**: 第1841-1891行
**预计时间**: 1小时

#### 2.1 当前代码（需要替换）
```python
async def _execute_with_semaphore(
    self,
    task_info: Dict[str, Any],
    canvas_path: str,
    execution_id: str
) -> Dict[str, Any]:
    async with self.semaphore:
        start_time = time.time()

        try:
            # ❌ 当前：模拟执行
            agent_name = task_info.get("agent_name")
            node_id = task_info.get("node_id")
            node_text = task_info.get("node_text", "")

            await asyncio.sleep(0.5)  # 模拟执行时间

            execution_time = time.time() - start_time

            return {
                "agent_name": agent_name,
                "node_id": node_id,
                "execution_time": round(execution_time, 2),
                "status": "success",
                "output": f"Agent {agent_name} 执行成功",
                "execution_id": execution_id
            }
        except Exception as e:
            # ... 错误处理
```

#### 2.2 修复后的代码
```python
async def _execute_with_semaphore(
    self,
    task_info: Dict[str, Any],
    canvas_path: str,
    execution_id: str
) -> Dict[str, Any]:
    async with self.semaphore:
        start_time = time.time()

        try:
            # ✅ 修复：实际调用Sub-agent
            agent_name = task_info.get("agent_name")
            node_id = task_info.get("node_id")
            node_text = task_info.get("node_text", "")

            # 调用实际的Sub-agent
            agent_result = await self._call_subagent(
                agent_name=agent_name,
                node_content=node_text,
                canvas_path=canvas_path,
                node_id=node_id
            )

            execution_time = time.time() - start_time

            # 返回包含Agent生成内容的结果
            return {
                "agent_name": agent_name,
                "node_id": node_id,
                "agent_result": agent_result,  # 新增：Agent生成的内容
                "execution_time": round(execution_time, 2),
                "status": "success" if agent_result.get("success") else "error",
                "execution_id": execution_id,
                "success": agent_result.get("success", False)
            }

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"执行任务失败: {str(e)}")

            return {
                "agent_name": task_info.get("agent_name", "unknown"),
                "node_id": task_info.get("node_id"),
                "execution_time": round(execution_time, 2),
                "status": "error",
                "error": str(e),
                "execution_id": execution_id,
                "success": False
            }
```

---

### 任务3: 集成Canvas协调器
**文件**: `canvas_utils.py`
**位置**: `execute_parallel()` 方法，第1762行之前
**预计时间**: 1.5小时

#### 3.1 找到插入位置
在 `execute_parallel()` 方法中，找到这段代码：
```python
# 处理结果
successful_results = []
failed_results = []

for i, result in enumerate(results):
    task_info = agent_tasks[i]
    if isinstance(result, Exception):
        failed_results.append({...})
    else:
        successful_results.append(result)
```

#### 3.2 在循环后添加Canvas集成
```python
# 处理结果
successful_results = []
failed_results = []

for i, result in enumerate(results):
    task_info = agent_tasks[i]
    if isinstance(result, Exception):
        failed_results.append({
            "agent_name": task_info.get("agent_name", "unknown"),
            "task_info": task_info,
            "error": str(result),
            "success": False
        })
    else:
        successful_results.append(result)

# ✅ 新增：Canvas集成
if self.canvas_coordinator and canvas_path:
    logger.info(f"开始集成{len(successful_results)}个Agent结果到Canvas")

    for result in successful_results:
        # 只集成成功的Agent结果
        if not result.get("success"):
            continue

        agent_result = result.get("agent_result")
        if not agent_result or not agent_result.get("success"):
            continue

        try:
            # 调用Canvas集成协调器
            integration_result = self.canvas_coordinator.integrate_agent_result(
                agent_result=agent_result,
                canvas_path=canvas_path,
                source_node_id=result.get("node_id")
            )

            # 将集成结果附加到原结果
            result["canvas_integration"] = {
                "success": integration_result.success,
                "explanation_node_id": integration_result.explanation_node_id,
                "summary_node_id": integration_result.summary_node_id,
                "edges_created": integration_result.edges_created,
                "error": integration_result.error
            }

            if integration_result.success:
                logger.info(f"成功集成Agent结果到Canvas: {result.get('agent_name')}")
            else:
                logger.warning(f"Canvas集成失败: {integration_result.error}")

        except Exception as e:
            logger.error(f"Canvas集成异常: {e}")
            result["canvas_integration"] = {
                "success": False,
                "error": str(e)
            }
            # 不中断执行，继续处理其他结果
```

---

### 任务4: 更新返回结果
**文件**: `canvas_utils.py`
**位置**: `execute_parallel()` 方法的返回语句
**预计时间**: 30分钟

#### 4.1 修改返回数据结构
```python
return {
    "success": True,
    "execution_id": execution_id,
    "execution_time": execution_time,
    "total_tasks": len(agent_tasks),
    "successful_tasks": len(successful_results),
    "failed_tasks": len(failed_results),
    "results": result,
    "performance_metrics": result.get("performance_metrics", {}),
    # ✅ 新增：Canvas集成统计
    "canvas_integration_summary": {
        "attempted": sum(1 for r in successful_results if "canvas_integration" in r),
        "successful": sum(1 for r in successful_results
                         if r.get("canvas_integration", {}).get("success")),
        "failed": sum(1 for r in successful_results
                     if not r.get("canvas_integration", {}).get("success")),
        "nodes_created": sum(2 for r in successful_results
                            if r.get("canvas_integration", {}).get("success"))
    }
}
```

---

## 🧪 测试要求

### 单元测试
**文件**: `tests/test_concurrent_agent_processor.py`

#### 测试1: `test_call_subagent_success`
```python
async def test_call_subagent_success():
    """测试Sub-agent成功调用"""
    processor = ConcurrentAgentProcessor(max_concurrent=2)

    result = await processor._call_subagent(
        agent_name="clarification-path",
        node_content="测试内容：什么是切平面？",
        canvas_path="test.canvas",
        node_id="test-node-1"
    )

    assert result["success"] is True
    assert result["agent_name"] == "clarification-path"
    assert result["content"] is not None
    assert len(result["content"]) > 0
    assert "metadata" in result
```

#### 测试2: `test_execute_with_semaphore_real_agent`
```python
async def test_execute_with_semaphore_real_agent():
    """测试实际Agent调用（非模拟）"""
    processor = ConcurrentAgentProcessor(max_concurrent=2)

    task_info = {
        "agent_name": "oral-explanation",
        "node_id": "test-node-2",
        "node_text": "解释线性代数中的特征值"
    }

    result = await processor._execute_with_semaphore(
        task_info=task_info,
        canvas_path="test.canvas",
        execution_id="test-exec-1"
    )

    assert result["success"] is True
    assert "agent_result" in result
    assert result["agent_result"]["content"] is not None
```

#### 测试3: `test_canvas_integration_in_execute_parallel`
```python
async def test_canvas_integration_in_execute_parallel():
    """测试Canvas集成"""
    processor = ConcurrentAgentProcessor(max_concurrent=2)

    # 创建测试Canvas文件
    canvas_path = "test_canvas_integration.canvas"
    # ... 创建测试数据

    agent_tasks = [{
        "agent_name": "clarification-path",
        "node_id": "yellow-node-1",
        "node_text": "测试内容"
    }]

    result = await processor.execute_parallel(
        agent_tasks=agent_tasks,
        canvas_path=canvas_path,
        timeout=60
    )

    assert result["success"] is True
    assert result["canvas_integration_summary"]["successful"] > 0

    # 验证Canvas文件
    canvas_data = CanvasJSONOperator.read_canvas(canvas_path)
    blue_nodes = [n for n in canvas_data["nodes"] if n.get("color") == "5"]
    assert len(blue_nodes) > 0
```

### 集成测试
**文件**: `tests/test_intelligent_parallel_e2e.py` (新建)

```python
"""End-to-end测试：完整的智能并行处理流程"""

import pytest
from canvas_utils import (
    IntelligentParallelScheduler,
    CanvasJSONOperator
)

@pytest.mark.asyncio
async def test_full_intelligent_parallel_workflow():
    """测试完整工作流：分析 → 调度 → 执行 → 集成"""

    # 1. 准备测试Canvas
    canvas_path = "tests/fixtures/test_lecture5.canvas"

    # 2. 初始化调度器
    scheduler = IntelligentParallelScheduler(max_concurrent=4)

    # 3. 分析和调度
    result = await scheduler.analyze_and_schedule_nodes(
        canvas_path=canvas_path,
        auto_execute=True
    )

    # 4. 验证结果
    assert result["success"] is True
    assert result["execution_result"] is not None

    # 5. 验证Canvas文件
    canvas_data = CanvasJSONOperator.read_canvas(canvas_path)

    # 应该有蓝色解释节点
    blue_nodes = [n for n in canvas_data["nodes"] if n.get("color") == "5"]
    assert len(blue_nodes) > 0

    # 应该有新的黄色总结节点
    yellow_nodes = [n for n in canvas_data["nodes"] if n.get("color") == "6"]
    assert len(yellow_nodes) > 0

    # 验证连接边
    edges = canvas_data.get("edges", [])
    assert len(edges) > 0

@pytest.mark.asyncio
async def test_canvas_nodes_visible_in_obsidian():
    """验证生成的节点在Obsidian中可见"""
    # 这个测试需要手动在Obsidian中验证
    # 生成测试报告供用户检查
    pass
```

---

## 📝 实现检查清单

在提交代码前，确保完成以下检查：

### 代码实现
- [ ] `_call_subagent()` 方法已实现
- [ ] `_execute_with_semaphore()` 已修复（移除模拟代码）
- [ ] Canvas集成代码已添加到 `execute_parallel()`
- [ ] 返回结果包含Canvas集成统计
- [ ] 所有新代码有类型注解
- [ ] 所有新代码有docstring

### 错误处理
- [ ] Agent调用失败时有适当的错误处理
- [ ] Canvas集成失败不会中断整个流程
- [ ] 所有异常都被捕获和记录
- [ ] 用户会收到明确的错误信息

### 日志记录
- [ ] 关键步骤有INFO级别日志
- [ ] 错误有ERROR级别日志
- [ ] 使用Loguru格式化日志

### 测试
- [ ] 所有单元测试通过
- [ ] 集成测试通过
- [ ] 测试覆盖率 ≥ 95%
- [ ] 无测试警告

### 性能
- [ ] 单个Agent调用时间合理（< 30秒）
- [ ] Canvas写入时间 < 2秒
- [ ] 内存使用无泄漏

### 向后兼容
- [ ] 不破坏现有功能
- [ ] 无canvas_path时正常降级
- [ ] 现有测试全部通过

---

## 🐛 常见问题与解决方案

### 问题1: Agent调用超时
**解决**: 添加超时参数，默认30秒
```python
result = await asyncio.wait_for(
    self._call_subagent(...),
    timeout=30
)
```

### 问题2: Canvas文件写入冲突
**解决**: CanvasIntegrationCoordinator已实现文件锁，无需额外处理

### 问题3: 生成的内容格式不正确
**解决**: 使用 `_format_explanation_text()` 格式化内容

### 问题4: 测试中Mock Agent调用
**解决**: 使用pytest的monkeypatch或unittest.mock
```python
@pytest.fixture
def mock_agent_call(monkeypatch):
    async def mock_call(*args, **kwargs):
        return {"success": True, "content": "模拟内容"}

    monkeypatch.setattr(
        "canvas_utils.ConcurrentAgentProcessor._call_subagent",
        mock_call
    )
```

---

## 📦 交付物清单

完成后，请提交以下文件：

1. **修改的代码**:
   - `canvas_utils.py` (修改3个方法)

2. **新建的测试**:
   - `tests/test_concurrent_agent_processor.py` (更新)
   - `tests/test_intelligent_parallel_e2e.py` (新建)

3. **测试报告**:
   - 测试覆盖率报告
   - 所有测试通过截图

4. **实现文档**:
   - 简短的实现说明（200字以内）
   - 遇到的问题和解决方案

---

## ✅ 完成标准

代码可以合并当满足：
- ✅ 所有单元测试通过（≥95%覆盖率）
- ✅ 集成测试通过
- ✅ 代码审查通过（无严重问题）
- ✅ Story 10.7的所有AC满足

---

## 🔗 相关资源

- **Sprint Change Proposal**: `docs/sprint-change-proposals/SCP-20251104-001-intelligent-parallel-fix.md`
- **Story 10.7**: `docs/stories/10.7.canvas-integration-coordinator.story.md`
- **Canvas Integration API**: `canvas_utils/canvas_integration_coordinator.py`
- **现有Sub-agent调用示例**: `canvas_utils.py` CanvasOrchestrator类

---

**分配时间**: 2025-11-04 22:30
**预计完成**: 2025-11-05 18:00
**当前状态**: ⏳ 等待Dev Agent开始

如有任何问题，请查阅Sprint Change Proposal或联系PM Agent。
