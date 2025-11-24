# ADR-006: 实时通信方案 - SSE + HTTP

## 状态

**已接受** | 2025-11-23

## 背景

Canvas Learning System 需要实时通信能力，用于以下核心场景：

### 业务需求

| Epic | 场景 | 通信需求 |
|------|------|----------|
| Epic 10 | 并行处理进度 | 实时推送进度百分比、当前处理节点 |
| Epic 13 | Agent 执行状态 | 实时推送执行步骤、当前 Agent |
| Epic 13 | 批量评分结果 | 逐个推送评分完成的节点 |
| Epic 17 | 性能监控 | 定期推送系统指标 |

### 技术约束

1. **Obsidian 插件环境**
   - 基于 Electron，支持现代 Web API
   - 插件 UI 使用 TypeScript/React
   - 不需要考虑老浏览器兼容

2. **本地通信**
   - 后端运行在 localhost:8000
   - 网络延迟 <1ms
   - 不存在网络不稳定问题

3. **单用户场景**
   - 无需房间/广播机制
   - 无需多租户隔离

### 可选方案

| 方案 | 描述 |
|------|------|
| 原生 WebSocket | 全双工通信，需手动实现重连/心跳 |
| Socket.IO | 功能完整，自动重连/降级，但包体积大 |
| **SSE + HTTP** | SSE 单向推送 + HTTP POST 操作 |

## 决策

**采用 SSE (Server-Sent Events) + HTTP 混合方案**

- **SSE**: 服务端 → 客户端的实时推送
- **HTTP POST**: 客户端 → 服务端的操作请求（如取消）

## 理由

### 1. 通信模式匹配

**95% 的实时通信是单向推送**：

```
服务端 ──────────────────────────> 客户端
        进度更新、状态变化、评分结果
```

SSE 天然适合这种模式，无需维护双向连接的复杂性。

### 2. 浏览器原生支持

```typescript
// SSE 使用极其简单
const eventSource = new EventSource('/events/task-123');

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    updateUI(data);
};

// 浏览器自动处理：
// ✅ 断线重连
// ✅ 保持连接
// ✅ 事件解析
```

相比之下，WebSocket 需要手动实现重连逻辑。

### 3. 取消操作分析

经过场景分析，**取消操作是低频功能**：

| 场景 | 耗时 | 取消概率 | 原因 |
|------|------|----------|------|
| 单节点分析 | 5-15秒 | 极低 | 太快，来不及取消 |
| 批量评分 | 20-40秒 | 低 | 沉没成本心理 |
| 并行处理 | 30-60秒 | 中 | 可能选错文件 |

**95% 的任务不会被取消**，因此：
- 不值得为此引入 WebSocket 的复杂性
- HTTP POST 完全满足偶发的取消需求

### 4. 实现简单

**SSE 后端实现**（FastAPI 内置支持）：
```python
from sse_starlette.sse import EventSourceResponse

@app.get("/events/{task_id}")
async def event_stream(task_id: str):
    async def generate():
        while not task_completed(task_id):
            yield {"event": "progress", "data": json.dumps(get_progress(task_id))}
            await asyncio.sleep(0.5)
    return EventSourceResponse(generate())
```

**HTTP 取消接口**：
```python
@app.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    tasks[task_id]["cancel_requested"] = True
    return {"success": True}
```

### 5. Obsidian 兼容性

- SSE 是标准 Web API，Electron 完全支持
- 无需引入 Socket.IO 等第三方库
- 减少插件包体积

### 6. 调试友好

- 浏览器 DevTools 可直接查看 SSE 事件流
- HTTP 请求可用 curl 单独测试
- 日志清晰，问题易定位

## 实现细节

### 架构图

```
┌─────────────────────────────────────────────────────────┐
│ Obsidian 插件                                           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────┐      ┌──────────────────┐        │
│  │ EventSource      │      │ fetch()          │        │
│  │ (SSE 连接)       │      │ (HTTP 请求)      │        │
│  └────────┬─────────┘      └────────┬─────────┘        │
│           │                         │                   │
│           │ 接收进度推送            │ 发送操作请求       │
│           ▼                         ▼                   │
└───────────────────────────┬─────────────────────────────┘
                            │
                   localhost:8000
                            │
┌───────────────────────────┴─────────────────────────────┐
│ FastAPI 后端                                            │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  GET /events/{task_id}     POST /tasks/{task_id}/cancel │
│  GET /events/metrics       POST /tasks                  │
│                                                         │
│  ┌──────────────────────────────────────────┐          │
│  │ 任务状态存储 (tasks dict)                 │          │
│  │ - status: running/completed/cancelled    │          │
│  │ - progress: {completed, total}           │          │
│  │ - cancel_requested: bool                 │          │
│  └──────────────────────────────────────────┘          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### SSE 事件类型定义

```typescript
// 进度更新事件
interface ProgressEvent {
    type: 'progress';
    task_id: string;
    completed: number;
    total: number;
    current_step: string;
    groups?: GroupProgress[];  // 并行处理时
}

// 任务完成事件
interface CompletedEvent {
    type: 'completed';
    task_id: string;
    result: TaskResult;
    duration_ms: number;
}

// 任务取消事件
interface CancelledEvent {
    type: 'cancelled';
    task_id: string;
    completed_before_cancel: number;
}

// 错误事件
interface ErrorEvent {
    type: 'error';
    task_id: string;
    error_code: string;
    message: string;
}

// 性能指标事件
interface MetricsEvent {
    type: 'metrics';
    timestamp: string;
    api_latency_ms: number;
    agent_calls_per_minute: number;
    memory_mb: number;
}
```

### 后端完整实现

```python
# app/api/events.py
from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse
import asyncio
import json

router = APIRouter(prefix="/events", tags=["Events"])

# 任务状态存储（生产环境应使用 Redis）
tasks: dict[str, dict] = {}

@router.get("/{task_id}")
async def task_event_stream(task_id: str, request: Request):
    """
    SSE 端点：推送任务执行进度

    Events:
    - progress: 进度更新
    - completed: 任务完成
    - cancelled: 任务取消
    - error: 错误发生
    """

    async def generate():
        while True:
            # 检查客户端是否断开
            if await request.is_disconnected():
                break

            task = tasks.get(task_id)
            if not task:
                yield {
                    "event": "error",
                    "data": json.dumps({
                        "error_code": "TASK_NOT_FOUND",
                        "message": f"Task {task_id} not found"
                    })
                }
                break

            # 任务取消
            if task.get("cancel_requested") and task["status"] == "cancelled":
                yield {
                    "event": "cancelled",
                    "data": json.dumps({
                        "task_id": task_id,
                        "completed_before_cancel": task["completed"]
                    })
                }
                break

            # 任务完成
            if task["status"] == "completed":
                yield {
                    "event": "completed",
                    "data": json.dumps({
                        "task_id": task_id,
                        "result": task.get("result", {}),
                        "duration_ms": task.get("duration_ms", 0)
                    })
                }
                break

            # 任务失败
            if task["status"] == "failed":
                yield {
                    "event": "error",
                    "data": json.dumps({
                        "error_code": task.get("error_code", "UNKNOWN"),
                        "message": task.get("error_message", "Unknown error")
                    })
                }
                break

            # 推送进度
            yield {
                "event": "progress",
                "data": json.dumps({
                    "task_id": task_id,
                    "completed": task["completed"],
                    "total": task["total"],
                    "current_step": task.get("current_step", ""),
                    "groups": task.get("groups", [])
                })
            }

            await asyncio.sleep(0.5)  # 500ms 推送间隔

    return EventSourceResponse(generate())


@router.get("/metrics/stream")
async def metrics_event_stream(request: Request):
    """
    SSE 端点：推送系统性能指标

    Events:
    - metrics: 性能指标更新（每 5 秒）
    """

    async def generate():
        while True:
            if await request.is_disconnected():
                break

            metrics = await collect_system_metrics()
            yield {
                "event": "metrics",
                "data": json.dumps(metrics)
            }

            await asyncio.sleep(5)  # 5 秒推送间隔

    return EventSourceResponse(generate())
```

```python
# app/api/tasks.py
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
import uuid

router = APIRouter(prefix="/tasks", tags=["Tasks"])

class CancelResponse(BaseModel):
    success: bool
    message: str

@router.post("/{task_id}/cancel", response_model=CancelResponse)
async def cancel_task(task_id: str):
    """
    取消正在执行的任务

    注意：取消请求会被标记，但任务可能需要等待当前 LLM 调用完成
    """

    task = tasks.get(task_id)

    if not task:
        return CancelResponse(
            success=False,
            message=f"Task {task_id} not found"
        )

    if task["status"] in ["completed", "failed", "cancelled"]:
        return CancelResponse(
            success=False,
            message=f"Task already {task['status']}"
        )

    # 设置取消标志
    task["cancel_requested"] = True

    return CancelResponse(
        success=True,
        message="Cancel request sent. Task will stop after current operation."
    )
```

### 前端完整实现

```typescript
// src/services/EventService.ts

export interface TaskProgress {
    task_id: string;
    completed: number;
    total: number;
    current_step: string;
    groups?: GroupProgress[];
}

export interface GroupProgress {
    name: string;
    total: number;
    completed: number;
    status: 'pending' | 'running' | 'done' | 'failed';
}

export class TaskEventService {
    private eventSource: EventSource | null = null;
    private taskId: string | null = null;
    private baseUrl: string;

    constructor(baseUrl: string = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }

    /**
     * 连接到任务事件流
     */
    connect(
        taskId: string,
        callbacks: {
            onProgress: (data: TaskProgress) => void;
            onCompleted: (result: any) => void;
            onCancelled: (data: any) => void;
            onError: (error: any) => void;
        }
    ): void {
        this.taskId = taskId;
        this.eventSource = new EventSource(`${this.baseUrl}/events/${taskId}`);

        // 进度更新
        this.eventSource.addEventListener('progress', (event) => {
            const data = JSON.parse(event.data) as TaskProgress;
            callbacks.onProgress(data);
        });

        // 任务完成
        this.eventSource.addEventListener('completed', (event) => {
            const data = JSON.parse(event.data);
            callbacks.onCompleted(data);
            this.disconnect();
        });

        // 任务取消
        this.eventSource.addEventListener('cancelled', (event) => {
            const data = JSON.parse(event.data);
            callbacks.onCancelled(data);
            this.disconnect();
        });

        // 错误处理
        this.eventSource.addEventListener('error', (event) => {
            // SSE 连接错误会触发这个
            if (this.eventSource?.readyState === EventSource.CLOSED) {
                callbacks.onError({ message: 'Connection closed' });
                this.disconnect();
            }
        });

        // 自定义错误事件
        this.eventSource.addEventListener('error', (event: any) => {
            if (event.data) {
                const data = JSON.parse(event.data);
                callbacks.onError(data);
                this.disconnect();
            }
        });
    }

    /**
     * 发送取消请求
     */
    async cancel(): Promise<{ success: boolean; message: string }> {
        if (!this.taskId) {
            return { success: false, message: 'No active task' };
        }

        const response = await fetch(`${this.baseUrl}/tasks/${this.taskId}/cancel`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        return response.json();
    }

    /**
     * 断开连接
     */
    disconnect(): void {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
        this.taskId = null;
    }

    /**
     * 获取连接状态
     */
    isConnected(): boolean {
        return this.eventSource?.readyState === EventSource.OPEN;
    }
}
```

```typescript
// src/views/ParallelAnalysisView.ts
import { ItemView, WorkspaceLeaf } from 'obsidian';
import { TaskEventService } from '../services/EventService';

export class ParallelAnalysisView extends ItemView {
    private eventService: TaskEventService;
    private progressBar: HTMLElement;
    private statusText: HTMLElement;
    private cancelButton: HTMLButtonElement;

    constructor(leaf: WorkspaceLeaf) {
        super(leaf);
        this.eventService = new TaskEventService();
    }

    async startAnalysis(canvasPath: string, nodes: string[]): Promise<void> {
        // 1. 启动任务
        const response = await fetch('http://localhost:8000/tasks/parallel-analysis', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ canvas_path: canvasPath, node_ids: nodes })
        });

        const { task_id } = await response.json();

        // 2. 连接事件流
        this.eventService.connect(task_id, {
            onProgress: (data) => this.updateProgress(data),
            onCompleted: (result) => this.showCompleted(result),
            onCancelled: (data) => this.showCancelled(data),
            onError: (error) => this.showError(error)
        });

        // 3. 启用取消按钮
        this.cancelButton.disabled = false;
        this.cancelButton.onclick = () => this.handleCancel();
    }

    private updateProgress(data: TaskProgress): void {
        const percent = (data.completed / data.total) * 100;
        this.progressBar.style.width = `${percent}%`;
        this.statusText.textContent = `${data.completed}/${data.total} - ${data.current_step}`;
    }

    private async handleCancel(): Promise<void> {
        this.cancelButton.disabled = true;
        this.cancelButton.textContent = '取消中...';

        const result = await this.eventService.cancel();

        if (!result.success) {
            new Notice(`取消失败: ${result.message}`);
            this.cancelButton.disabled = false;
            this.cancelButton.textContent = '取消';
        }
        // 成功的话，等待 SSE 的 cancelled 事件
    }

    private showCompleted(result: any): void {
        this.progressBar.style.width = '100%';
        this.statusText.textContent = '分析完成!';
        new Notice(`成功分析 ${result.total} 个节点`);
    }

    private showCancelled(data: any): void {
        this.statusText.textContent = `已取消 (完成 ${data.completed_before_cancel} 个)`;
        new Notice('任务已取消');
    }

    private showError(error: any): void {
        this.statusText.textContent = `错误: ${error.message}`;
        new Notice(`任务失败: ${error.message}`, 5000);
    }

    onunload(): void {
        this.eventService.disconnect();
    }
}
```

### API 端点总结

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/events/{task_id}` | SSE - 任务进度流 |
| GET | `/events/metrics/stream` | SSE - 性能指标流 |
| POST | `/tasks/parallel-analysis` | 启动并行分析 |
| POST | `/tasks/single-analysis` | 启动单节点分析 |
| POST | `/tasks/batch-scoring` | 启动批量评分 |
| POST | `/tasks/{task_id}/cancel` | 取消任务 |
| GET | `/tasks/{task_id}` | 获取任务状态 |

## 影响

### 正面影响

1. **实现简单** - SSE 是最轻量的实时方案
2. **调试容易** - 标准 HTTP，工具支持好
3. **无额外依赖** - 不需要 Socket.IO
4. **Obsidian 兼容** - 原生 API，稳定可靠

### 负面影响

1. **单向限制** - 客户端→服务端需要单独 HTTP 请求
2. **连接数** - 每个任务一个 SSE 连接
3. **无二进制支持** - SSE 只能传输文本

### 缓解措施

1. **连接复用** - 多个任务可共享一个 SSE 连接（通过 task_id 区分）
2. **连接管理** - 插件卸载时确保断开所有连接
3. **数据压缩** - JSON 数据保持精简

## 未来扩展

### 如果需要升级到 WebSocket

以下场景可能需要考虑 WebSocket：

1. **协作学习** - 多用户实时同步
2. **双向高频通信** - 如实时协作编辑
3. **二进制传输** - 如图片流

**迁移路径**：
- 保持相同的事件类型定义
- 后端添加 WebSocket 端点
- 前端抽象通信层，支持 SSE/WS 切换

### 连接复用优化

```python
# 未来可以实现连接复用
@router.get("/stream")
async def unified_event_stream(request: Request):
    """统一事件流，支持订阅多个任务"""

    async def generate():
        subscribed_tasks = set()

        while True:
            # 接收订阅请求（通过 query param 或其他机制）
            # 推送所有订阅任务的事件
            pass

    return EventSourceResponse(generate())
```

## 替代方案记录

### 方案A: 原生 WebSocket

**未选择原因**：
- 需要手动实现重连/心跳
- 对于单向推送场景过于复杂
- 开发成本高于收益

### 方案B: Socket.IO

**未选择原因**：
- 引入 ~40KB 额外依赖
- 功能过剩（房间、命名空间等不需要）
- 可能与 Obsidian 的打包机制冲突

### 方案C: 轮询

**未选择原因**：
- 延迟高（取决于轮询间隔）
- 服务器压力大
- 用户体验差

## 实现计划

| 阶段 | 内容 | Story |
|------|------|-------|
| Phase 1 | SSE 基础设施 + 任务进度推送 | Story 11.x |
| Phase 2 | 取消操作支持 | Story 11.x |
| Phase 3 | 性能指标流 | Story 17.x |
| Phase 4 | 前端 EventService 封装 | Story 13.x |

## 参考资料

- [MDN: Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [FastAPI SSE](https://github.com/sysid/sse-starlette)
- [Obsidian Plugin API](https://docs.obsidian.md/Plugins/Getting+started/Build+a+plugin)

---

**作者**: Winston (Architect Agent)
**审核**: 待定
**批准**: 待定
