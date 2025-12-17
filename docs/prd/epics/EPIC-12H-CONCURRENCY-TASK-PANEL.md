# Epic 12.H: Canvas 并发控制 + 任务管理面板 - 棕地增强

**创建日期**: 2025-12-17
**状态**: Ready for Implementation
**优先级**: P0 (Critical)
**类型**: Bug Fix + Feature Enhancement

---

## Epic 目标

解决 **"点击一次生成多份解释文档"** 的根本问题，并提供用户可见的任务管理面板，让用户能够查看、管理和取消正在进行的 Agent 请求。

---

## Epic 描述

### 现有系统上下文

- **当前功能**: 14个学习 Agent 通过 Obsidian 右键菜单调用后端 API
- **技术栈**:
  - 前端: TypeScript + Obsidian Plugin API
  - 后端: FastAPI + GeminiClient + AgentService
- **集成点**:
  - 前端: `canvas-progress-tracker/obsidian-plugin/main.ts`
  - 后端: `backend/app/services/canvas_service.py`
  - API: `backend/app/api/v1/endpoints/agents.py`

### 问题根源诊断 (UltraThink 深度调研结果)

| # | 根本原因 | 概率 | 位置 | 验证状态 |
|---|---------|------|------|---------|
| **1** | **Canvas Service 无并发锁** | 95% | `canvas_service.py` | ✅ 代码确认 |
| **2** | **不同Agent可并发执行** | 85% | `main.ts` lockKey设计 | ✅ 用户确认 |
| **3** | 后端无二级防重复 | 60% | `agents.py` | ✅ 代码确认 |
| **4** | 多条write路径 | 30% | `agent_service.py` | ✅ 代码确认 |

### 复现场景 (用户确认)

```
用户操作:
1. 右键节点A，点击"四层次解释"
2. 处理中（40秒），再点击"口语化解释"
3. 两个请求并发执行 (lockKey不同: four-level-A vs oral-A)
4. Canvas read-modify-write 产生竞态条件
5. 结果: 生成多份文档（部分相同部分不同）
```

### Epic 12.x 系列"幻觉"问题回顾

| Epic | 声称解决 | 实际状态 |
|------|---------|---------|
| Epic 12.F.4 去重机制 | ✅ 已实现 | ⚠️ 只防相同lockKey，不防不同Agent并发 |
| Epic 12.G 响应提取 | ✅ 已实现 | ✅ 真正解决 |
| Epic 12.A RAG集成 | ❌ 未开始 | 规划详细但代码未实现 |
| Epic 12.D FILE节点 | ❌ 未开始 | P0 BLOCKER 标注但无代码 |

### 成功标准

| 指标 | 当前值 | 目标值 |
|------|-------|-------|
| 点击一次生成文档数 | 1-3份 | 精确1份 |
| 用户可见请求状态 | ❌ | ✅ |
| 支持取消请求 | ❌ | ✅ |
| Canvas写入成功率 | ~80% | 99%+ |

---

## Stories

### Story 12.H.1: Canvas Service 并发锁 [P0 BLOCKER]

**优先级**: P0 (阻塞后续开发)
**预估**: 1 小时

**问题**: `canvas_service.py` 的 read-modify-write 无任何同步原语

**验收标准**:
1. 添加 `asyncio.Lock` 按 Canvas 文件名分锁
2. `write_canvas` 方法使用 `async with` 获取锁
3. 并发写入测试通过（10个并发请求只产生1份文档）
4. 性能影响 < 5%

**技术方案**:
```python
class CanvasService:
    def __init__(self):
        self._write_locks: Dict[str, asyncio.Lock] = {}

    def _get_lock(self, canvas_name: str) -> asyncio.Lock:
        if canvas_name not in self._write_locks:
            self._write_locks[canvas_name] = asyncio.Lock()
        return self._write_locks[canvas_name]

    async def write_canvas(self, canvas_name: str, canvas_data: Dict) -> bool:
        async with self._get_lock(canvas_name):
            # 原有写入逻辑
```

**关键文件**:
- `backend/app/services/canvas_service.py:88-140`

---

### Story 12.H.2: 同一节点并发Agent限制 [P0]

**优先级**: P0
**预估**: 2 小时

**问题**: 前端 `callAgentWithLock` 只防相同lockKey，不防同一节点的不同Agent

**验收标准**:
1. 同一节点同时只允许一个 Agent 请求
2. 后续请求进入队列等待
3. 用户收到明确提示 "节点 X 正在处理中，请稍候"
4. 队列中的请求按顺序执行

**技术方案 (节点级别并发队列)**:
```typescript
class NodeRequestQueue {
    private nodeQueues: Map<string, Promise<any>> = new Map();

    async enqueue<T>(nodeId: string, fn: () => Promise<T>): Promise<T> {
        const prev = this.nodeQueues.get(nodeId) || Promise.resolve();
        const current = prev.then(() => fn()).finally(() => {
            if (this.nodeQueues.get(nodeId) === current) {
                this.nodeQueues.delete(nodeId);
            }
        });
        this.nodeQueues.set(nodeId, current);
        return current;
    }
}
```

**关键文件**:
- `canvas-progress-tracker/obsidian-plugin/main.ts:101-102, 1911-1936`

---

### Story 12.H.3: 任务管理可视化面板 [P1]

**优先级**: P1
**预估**: 4 小时

**用户需求** (已确认):
- ✅ 查看当前运行的请求
- ✅ 取消单个请求
- ✅ 查看请求队列
- ✅ 显示进度和预计时间

**验收标准**:
1. 创建 `TaskQueueModal` 模态框
2. 显示所有 pending 请求的状态
3. 每个请求显示: Agent类型、节点、状态、进度、取消按钮
4. 支持点击 Ribbon Icon 或 Command Palette 打开
5. 每 500ms 自动刷新状态

**技术方案**:
```typescript
interface PendingRequest {
    nodeId: string;
    agentType: string;
    status: 'queued' | 'running';
    startTime: number;
    estimatedTime: number;
    abortController: AbortController;
}

class TaskQueueModal extends Modal {
    private tasks: Map<string, PendingRequest>;

    onOpen() {
        this.renderTaskList();
        this.startPolling();
    }

    renderTaskList() {
        // 显示: Agent类型 | 节点 | 状态 | 进度 | [取消]按钮
    }

    cancelTask(lockKey: string) {
        const task = this.tasks.get(lockKey);
        task?.abortController.abort();
    }
}
```

**关键文件**:
- `canvas-progress-tracker/obsidian-plugin/main.ts` (扩展pendingRequests)
- `canvas-progress-tracker/obsidian-plugin/src/modals/TaskQueueModal.ts` (新建)
- `canvas-progress-tracker/obsidian-plugin/src/styles/task-queue.css` (新建)

---

### Story 12.H.4: 前端取消请求支持 [P1]

**优先级**: P1
**预估**: 2 小时
**依赖**: Story 12.H.3

**问题**: 当前 ApiClient 无取消单个请求的能力

**验收标准**:
1. `ApiClient` 支持 `AbortController` 管理
2. 每个请求关联一个 `AbortController`
3. 提供 `cancelRequest(lockKey)` 方法
4. 取消后显示 "请求已取消" 提示
5. 取消的请求不会写入 Canvas

**技术方案**:
```typescript
class ApiClient {
    private abortControllers: Map<string, AbortController> = new Map();

    async callAgentWithCancel(
        lockKey: string,
        endpoint: string,
        data: any
    ): Promise<Response | null> {
        const controller = new AbortController();
        this.abortControllers.set(lockKey, controller);

        try {
            return await fetch(endpoint, {
                ...options,
                signal: controller.signal
            });
        } finally {
            this.abortControllers.delete(lockKey);
        }
    }

    cancelRequest(lockKey: string): boolean {
        const controller = this.abortControllers.get(lockKey);
        if (controller) {
            controller.abort();
            return true;
        }
        return false;
    }
}
```

**关键文件**:
- `canvas-progress-tracker/obsidian-plugin/src/api/ApiClient.ts`

---

### Story 12.H.5: 后端二级防重复 [P2]

**优先级**: P2
**预估**: 2 小时

**问题**: API 端点无请求去重，同一请求可能被处理多次

**验收标准**:
1. 添加请求缓存，TTL 60秒
2. 重复请求返回 HTTP 409 Conflict
3. 缓存 key 格式: `{canvas_name}:{node_id}:{agent_type}`
4. 日志记录重复请求

**技术方案**:
```python
class RequestCache:
    def __init__(self, ttl: int = 60):
        self.cache: Dict[str, Tuple[float, Any]] = {}
        self.ttl = ttl

    def get_key(self, canvas_name: str, node_id: str, agent_type: str) -> str:
        return hashlib.md5(f"{canvas_name}:{node_id}:{agent_type}".encode()).hexdigest()

    def is_duplicate(self, key: str) -> bool:
        if key in self.cache:
            timestamp, _ = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return True
        return False

request_cache = RequestCache(ttl=60)

@agents_router.post("/explain/oral")
async def explain_oral(request: ExplainRequest) -> ExplainResponse:
    cache_key = request_cache.get_key(request.canvas_name, request.node_id, "oral")
    if request_cache.is_duplicate(cache_key):
        raise HTTPException(409, "Duplicate request in progress")
    # ...
```

**关键文件**:
- `backend/app/api/v1/endpoints/agents.py`

---

## 实施优先级

| 优先级 | Story | 依赖 | 预估 | 效果 |
|--------|-------|------|------|------|
| **P0** | 12.H.1 Canvas并发锁 | 无 | 1h | 根除竞态条件 |
| **P0** | 12.H.2 节点并发限制 | 无 | 2h | 阻止同节点多Agent |
| **P1** | 12.H.3 任务管理面板 | 12.H.2 | 4h | 用户可见性 |
| **P1** | 12.H.4 取消请求支持 | 12.H.3 | 2h | 用户可操作性 |
| **P2** | 12.H.5 后端防重复 | 无 | 2h | 二级防护 |

**总预估**: 11 小时

---

## 关键文件清单

### 需要修改的文件

| 文件 | 修改内容 | Story |
|------|---------|-------|
| `backend/app/services/canvas_service.py` | 添加asyncio.Lock | 12.H.1 |
| `canvas-progress-tracker/obsidian-plugin/main.ts` | 扩展pendingRequests + 节点锁 | 12.H.2, 12.H.3 |
| `canvas-progress-tracker/obsidian-plugin/src/api/ApiClient.ts` | 添加AbortController管理 | 12.H.4 |
| `backend/app/api/v1/endpoints/agents.py` | 添加请求缓存 | 12.H.5 |

### 新增文件

| 文件 | 用途 | Story |
|------|------|-------|
| `canvas-progress-tracker/obsidian-plugin/src/modals/TaskQueueModal.ts` | 任务队列模态框 | 12.H.3 |
| `canvas-progress-tracker/obsidian-plugin/src/styles/task-queue.css` | 样式文件 | 12.H.3 |

---

## 兼容性要求

- [x] 现有 API 接口保持不变
- [x] 现有 Agent 调用流程向后兼容
- [x] 插件向后兼容
- [x] 不影响已有的 Canvas 文件
- [x] pendingRequests 数据结构向后兼容

---

## 风险缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| asyncio.Lock 性能影响 | 中 | 按Canvas文件分锁，不用全局锁 |
| AbortController 兼容性 | 低 | Obsidian 内置支持 |
| 任务面板刷新频率 | 低 | 使用500ms轮询，可配置 |
| 节点队列内存占用 | 低 | 请求完成后自动清理 |

**回滚计划**:
- 所有更改可通过 Git revert 快速回滚
- 并发锁可通过配置开关禁用
- 任务面板是独立功能，不影响核心流程

---

## Definition of Done

- [ ] Story 12.H.1 完成 → Canvas 并发写入测试通过
- [ ] Story 12.H.2 完成 → 同一节点快速点击不同Agent只生成一份文档
- [ ] Story 12.H.3 完成 → 任务面板可查看当前请求
- [ ] Story 12.H.4 完成 → 点击"取消"按钮可中止请求
- [ ] Story 12.H.5 完成 → 后端拒绝重复请求
- [ ] 插件重新构建并部署成功
- [ ] 所有 12 个学习 Agent 功能验证通过

---

## 验证检查清单

- [ ] 同一节点快速点击不同Agent → 只生成一份文档
- [ ] 同一节点快速双击同一Agent → 被阻止并提示
- [ ] 任务面板显示当前运行的请求
- [ ] 点击"取消"按钮可以中止请求
- [ ] Canvas写入无竞态条件（并发测试）
- [ ] 后端返回 409 拒绝重复请求

---

## Story Manager 交接

**请为此棕地 Epic 开发详细用户故事。关键考虑：**

- 这是对运行中系统的增强，技术栈为 FastAPI + TypeScript
- 集成点: `CanvasService` ↔ `main.ts` ↔ `ApiClient`
- 需遵循的现有模式:
  - 并发控制使用 `asyncio.Lock`
  - 前端锁使用 `pendingRequests` Map
  - 模态框继承 `Modal` 类
- 关键兼容性要求: 现有 Agent 调用流程不变
- 每个 Story 必须包含验证现有功能完整性的测试

**Epic 目标**: 彻底解决重复生成文档问题，并提供用户可见的任务管理能力。

---

## 变更日志

| 日期 | 版本 | 变更内容 |
|------|------|---------|
| 2025-12-17 | 1.0 | 初始创建 (基于 UltraThink 深度调研) |
