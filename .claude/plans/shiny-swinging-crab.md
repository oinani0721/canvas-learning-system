# Epic 12.H 深度调研计划: Canvas 并发控制 + 任务管理面板

**创建日期**: 2025-12-17
**类型**: 深度调研 + Brownfield Epic
**优先级**: P0 Critical

---

## 一、问题根源诊断 (UltraThink 深度调研结果)

### 1.1 BUG 根本原因

经过深度代码分析和网上资料搜索，确认了 **"点击一次生成多份解释文档"** 的根本原因：

| # | 根本原因 | 概率 | 位置 | 验证状态 |
|---|---------|------|------|---------|
| **1** | **Canvas Service 无并发锁** | 95% | `canvas_service.py` | ✅ 代码确认 |
| **2** | **不同Agent可并发执行** | 85% | `main.ts` lockKey设计 | ✅ 用户确认 |
| **3** | 后端无二级防重复 | 60% | `agents.py` | ✅ 代码确认 |
| **4** | 多条write路径 | 30% | `agent_service.py` | ✅ 代码确认 |

### 1.2 复现场景 (用户确认)

```
用户操作:
1. 右键节点A，点击"四层次解释"
2. 处理中（40秒），再点击"口语化解释"
3. 两个请求并发执行 (lockKey不同: four-level-A vs oral-A)
4. Canvas read-modify-write 产生竞态条件
5. 结果: 生成多份文档（部分相同部分不同）
```

### 1.3 Epic 12.x 系列"幻觉"问题

| Epic | 声称解决 | 实际状态 |
|------|---------|---------|
| Epic 12.F.4 去重机制 | ✅ 已实现 | ⚠️ 只防相同lockKey，不防不同Agent并发 |
| Epic 12.G 响应提取 | ✅ 已实现 | ✅ 真正解决 |
| Epic 12.A RAG集成 | ❌ 未开始 | 规划详细但代码未实现 |
| Epic 12.D FILE节点 | ❌ 未开始 | P0 BLOCKER 标注但无代码 |

---

## 二、Epic 12.H 目标

### 2.1 必须解决的问题

1. **Canvas 并发写入竞态条件** (P0)
   - 添加文件锁或asyncio.Lock
   - 防止 read-modify-write 冲突

2. **同一节点多Agent并发限制** (P0)
   - 扩展防重复机制，限制同一节点的并发Agent数量
   - 或使用全局节点锁

3. **任务管理可视化面板** (P1)
   - 查看当前运行的请求
   - 取消单个请求
   - 查看请求队列
   - 显示进度和预计时间

### 2.2 成功标准

| 指标 | 当前值 | 目标值 |
|------|-------|-------|
| 点击一次生成文档数 | 1-3份 | 精确1份 |
| 用户可见请求状态 | ❌ | ✅ |
| 支持取消请求 | ❌ | ✅ |
| Canvas写入成功率 | ~80% | 99%+ |

---

## 三、Stories 规划

### Story 12.H.1: Canvas Service 并发锁 [P0 BLOCKER]

**问题**: `canvas_service.py` 的 read-modify-write 无任何同步原语

**修复**:
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

**预估**: 1小时

---

### Story 12.H.2: 同一节点并发Agent限制 [P0]

**问题**: 前端 `callAgentWithLock` 只防相同lockKey，不防同一节点的不同Agent

**方案A**: 修改lockKey策略
```typescript
// 当前: lockKey = `${agentType}-${nodeId}` (不同Agent可并发)
// 修改: lockKey = `node-${nodeId}` (同一节点全局锁)
```

**方案B**: 节点级别并发队列
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

**预估**: 2小时

---

### Story 12.H.3: 任务管理可视化面板 [P1]

**用户需求** (已确认):
- ✅ 查看当前运行的请求
- ✅ 取消单个请求
- ✅ 查看请求队列
- ✅ 显示进度和预计时间

**实现方案**:

1. **扩展 pendingRequests 数据结构**:
```typescript
interface PendingRequest {
    nodeId: string;
    agentType: string;
    status: 'queued' | 'running';
    startTime: number;
    estimatedTime: number;  // 秒
    abortController: AbortController;
}

private pendingRequests: Map<string, PendingRequest> = new Map();
```

2. **创建 TaskQueueModal**:
```typescript
class TaskQueueModal extends Modal {
    private tasks: Map<string, PendingRequest>;

    onOpen() {
        this.renderTaskList();
        this.startPolling();  // 每500ms刷新
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

3. **添加 Ribbon Icon 或 Command**:
```typescript
this.addRibbonIcon('list-todo', 'Task Queue', () => {
    new TaskQueueModal(this.app, this.pendingRequests).open();
});

this.addCommand({
    id: 'open-task-queue',
    name: 'Open Agent Task Queue',
    callback: () => new TaskQueueModal(...).open()
});
```

**关键文件**:
- `canvas-progress-tracker/obsidian-plugin/main.ts` (扩展pendingRequests)
- `canvas-progress-tracker/obsidian-plugin/src/modals/TaskQueueModal.ts` (新建)
- `canvas-progress-tracker/obsidian-plugin/src/styles/task-queue.css` (新建)

**预估**: 4小时

---

### Story 12.H.4: 前端取消请求支持 [P1]

**问题**: 当前 ApiClient 无取消单个请求的能力

**修复**:
```typescript
// ApiClient.ts
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

**预估**: 2小时

---

### Story 12.H.5: 后端二级防重复 [P2]

**问题**: API 端点无请求去重

**修复**: 添加请求缓存
```python
# agents.py
from functools import lru_cache
import hashlib

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

**预估**: 2小时

---

## 四、实施优先级

| 优先级 | Story | 依赖 | 预估 | 效果 |
|--------|-------|------|------|------|
| **P0** | 12.H.1 Canvas并发锁 | 无 | 1h | 根除竞态条件 |
| **P0** | 12.H.2 节点并发限制 | 无 | 2h | 阻止同节点多Agent |
| **P1** | 12.H.3 任务管理面板 | 12.H.2 | 4h | 用户可见性 |
| **P1** | 12.H.4 取消请求支持 | 12.H.3 | 2h | 用户可操作性 |
| **P2** | 12.H.5 后端防重复 | 无 | 2h | 二级防护 |

**总预估**: 11小时

---

## 五、关键文件清单

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

## 六、风险缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| asyncio.Lock 性能影响 | 中 | 按Canvas文件分锁，不用全局锁 |
| AbortController 兼容性 | 低 | Obsidian 内置支持 |
| 任务面板刷新频率 | 低 | 使用500ms轮询 |

---

## 七、验证检查清单

- [ ] 同一节点快速点击不同Agent → 只生成一份文档
- [ ] 同一节点快速双击同一Agent → 被阻止并提示
- [ ] 任务面板显示当前运行的请求
- [ ] 点击"取消"按钮可以中止请求
- [ ] Canvas写入无竞态条件（并发测试）
- [ ] 插件重新构建并部署成功

---

**计划状态**: Ready for Review
**下一步**: 用户确认后，运行 `*create-brownfield-epic` 创建正式 Epic 文档
