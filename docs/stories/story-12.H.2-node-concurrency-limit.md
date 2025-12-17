# Story 12.H.2: 同一节点并发 Agent 限制

**Story ID**: STORY-12.H.2
**Epic**: Epic 12.H - Canvas 并发控制 + 任务管理面板
**优先级**: P0
**状态**: Implemented
**预估时间**: 2 小时
**创建日期**: 2025-12-17

---

## 用户故事

**作为** Canvas Learning System 的用户
**我希望** 同一节点同时只执行一个 Agent 请求
**以便** 避免生成重复的解释文档

---

## 问题背景

### 当前问题

前端 `callAgentWithLock` 只防止相同 `lockKey` 的重复请求：

```typescript
// 当前 lockKey 格式: ${agentType}-${nodeId}
// 问题: 不同 Agent 类型有不同的 lockKey，可以并发执行

// 示例:
// "four-level-node123" - 四层次解释
// "oral-node123" - 口语化解释
// 这两个请求可以同时发起!
```

### 问题场景

```
用户操作:
1. 右键节点A，点击"四层次解释" → lockKey = "four-level-A"
2. 等待中（40秒），再点击"口语化解释" → lockKey = "oral-A" (不同!)
3. 两个请求并发执行
4. 都尝试写入 Canvas
5. 结果: 生成多份文档或数据丢失
```

### 问题影响

- 同一节点生成多份重复文档
- 用户困惑
- Canvas 布局混乱

---

## 验收标准

- [x] AC1: 同一节点同时只允许一个 Agent 请求
- [x] AC2: 后续请求进入队列等待
- [x] AC3: 用户收到明确提示 "节点正在处理中，请稍候"
- [x] AC4: 队列中的请求按顺序执行
- [x] AC5: 不同节点的请求可以并发

---

## Tasks / Subtasks

- [x] **Task 1**: 创建 NodeRequestQueue 类 (AC: 1, 2, 4)
  - [x] 1.1 实现 `nodeQueues: Map<string, Promise<any>>` 存储节点队列
  - [x] 1.2 实现 `nodeAgentTypes: Map<string, string>` 记录当前运行的Agent
  - [x] 1.3 实现 `enqueue<T>(nodeId, agentType, fn)` 方法，使用 Promise 链保证顺序执行
  - [x] 1.4 实现 `isProcessing(nodeId)` 和 `getCurrentAgentType(nodeId)` 辅助方法
  - [x] 1.5 确保请求完成后自动清理 Map 条目

- [x] **Task 2**: 集成到 CanvasReviewPlugin 类 (AC: 1, 3, 5)
  - [x] 2.1 添加 `private nodeRequestQueue: NodeRequestQueue` 实例属性
  - [x] 2.2 创建 `callAgentWithNodeQueue<T>(nodeId, agentType, fn)` 包装方法
  - [x] 2.3 在包装方法中集成现有 `pendingRequests` 去重逻辑 (Story 12.F.4 兼容)
  - [x] 2.4 添加用户提示 Notice: "节点正在处理 '{agentType}'，请稍候..."

- [x] **Task 3**: 更新所有 Agent 菜单处理器 (AC: 1)
  - [x] 3.1 替换 `callAgentWithLock` 为 `callAgentWithNodeQueue` (11个菜单项)
  - [x] 3.2 传递用户可见的 Agent 类型名称 (中文)
  - [x] 3.3 保持现有 Notice 提示和预估时间显示

- [x] **Task 4**: 测试验证 (AC: 1-5)
  - [x] 4.1 测试同一节点快速点击不同Agent → 按顺序执行 (Unit test: `should process same node requests sequentially`)
  - [x] 4.2 测试不同节点并发 → 可以并发 (Unit test: `should process different node requests concurrently`)
  - [x] 4.3 测试同一节点同一Agent重复点击 → 被阻止 (Handled by Story 12.F.4 dedup in `callAgentWithNodeQueue`)

- [x] **Task 5**: 构建和部署
  - [x] 5.1 运行 `npm run build` 构建插件
  - [x] 5.2 复制 main.js 到 Obsidian 插件目录
  - [ ] 5.3 重启 Obsidian 验证功能

---

## Dev Notes

### SDD规范参考 (必填)

此 Story 为纯前端 TypeScript 实现，不涉及 API 端点或数据 Schema 变更。

**现有代码参考**:
- 文件: `canvas-progress-tracker/obsidian-plugin/main.ts`
- `pendingRequests` 定义: 行 101-102
- `callAgentWithLock` 方法: 行 1911-1936
- 现有 lockKey 模式: `${agentType}-${nodeId}` (如 `oral-node123`, `four-level-node123`)

**Obsidian API 参考**:
- `Notice` 类: 用于用户提示 [Source: Context7 /obsidianmd/obsidian-api]
- `Plugin` 基类: 插件生命周期 [Source: Context7 /obsidianmd/obsidian-api]

**无 OpenAPI/JSON Schema 变更**: 此 Story 仅修改前端逻辑，不涉及后端 API。

### ADR决策关联 (必填)

| ADR编号 | 决策标题 | 对Story的影响 |
|---------|----------|---------------|
| ADR-001 | 使用 Obsidian Canvas | 必须遵循 Obsidian Plugin API 规范 |

**关键约束**:
- 必须兼容现有 Story 12.F.4 的 `pendingRequests` 去重机制
- 不能破坏现有 Agent 调用流程
- Promise 链模式确保内存安全（自动清理）

**无直接相关 ADR**: 并发控制为增量优化，遵循现有模式。

### 相关源码树

```
canvas-progress-tracker/obsidian-plugin/
├── main.ts                 # 主要修改文件
│   ├── Line 101-102       # pendingRequests 定义
│   ├── Line 311-690       # Agent 菜单处理器 (11个)
│   └── Line 1911-1936     # callAgentWithLock 方法
├── manifest.json
└── package.json
```

### Testing Standards

**测试位置**: 单元测试可在 `canvas-progress-tracker/obsidian-plugin/` 目录下创建

**测试框架**: Jest (Obsidian 插件标准)

**测试要求**:
- NodeRequestQueue 类的单元测试
- 同节点顺序执行测试
- 不同节点并发测试
- 状态查询方法测试

---

## 技术方案

### 修改文件

- `canvas-progress-tracker/obsidian-plugin/main.ts`

### 方案: 节点级别请求队列

```typescript
/**
 * Story 12.H.2: 节点级别请求队列
 * 确保同一节点同时只有一个 Agent 请求在执行
 */
class NodeRequestQueue {
    private nodeQueues: Map<string, Promise<any>> = new Map();
    private nodeAgentTypes: Map<string, string> = new Map(); // 记录当前运行的Agent类型

    /**
     * 将请求加入节点队列
     * @param nodeId 节点ID
     * @param agentType Agent类型（用于提示）
     * @param fn 实际执行的函数
     */
    async enqueue<T>(
        nodeId: string,
        agentType: string,
        fn: () => Promise<T>
    ): Promise<T> {
        // 检查是否有正在进行的请求
        const currentAgent = this.nodeAgentTypes.get(nodeId);
        if (currentAgent) {
            new Notice(`节点正在处理 "${currentAgent}"，请稍候...`);
        }

        // 获取当前节点的队列（如果有）
        const prev = this.nodeQueues.get(nodeId) || Promise.resolve();

        // 创建新的 Promise 链
        const current = prev.then(async () => {
            this.nodeAgentTypes.set(nodeId, agentType);
            try {
                return await fn();
            } finally {
                // 清理
                if (this.nodeQueues.get(nodeId) === current) {
                    this.nodeQueues.delete(nodeId);
                    this.nodeAgentTypes.delete(nodeId);
                }
            }
        });

        this.nodeQueues.set(nodeId, current);
        return current;
    }

    /**
     * 检查节点是否有正在进行的请求
     */
    isProcessing(nodeId: string): boolean {
        return this.nodeQueues.has(nodeId);
    }

    /**
     * 获取当前处理的 Agent 类型
     */
    getCurrentAgentType(nodeId: string): string | undefined {
        return this.nodeAgentTypes.get(nodeId);
    }
}
```

### 集成到 main.ts

```typescript
class CanvasReviewPlugin extends Plugin {
    /** Story 12.F.4: Pending requests map for deduplication */
    private pendingRequests: Map<string, boolean> = new Map();

    /** Story 12.H.2: Node-level request queue */
    private nodeRequestQueue: NodeRequestQueue = new NodeRequestQueue();

    /**
     * Story 12.H.2: 使用节点队列执行 Agent 调用
     */
    private async callAgentWithNodeQueue<T>(
        nodeId: string,
        agentType: string,
        fn: () => Promise<T>
    ): Promise<T | null> {
        const lockKey = `${agentType}-${nodeId}`;

        // 先检查相同请求是否在进行中 (Story 12.F.4)
        if (this.pendingRequests.get(lockKey)) {
            new Notice('相同请求处理中，请稍候...');
            return null;
        }

        // 通过节点队列执行 (Story 12.H.2)
        return this.nodeRequestQueue.enqueue(nodeId, agentType, async () => {
            this.pendingRequests.set(lockKey, true);
            try {
                return await fn();
            } finally {
                this.pendingRequests.delete(lockKey);
            }
        });
    }
}
```

### 使用示例

```typescript
// 修改前 (Story 12.F.4)
generateOralExplanation: async (context: MenuContext) => {
    const lockKey = `oral-${context.nodeId}`;
    await this.callAgentWithLock(lockKey, async () => {
        // ...
    });
}

// 修改后 (Story 12.H.2)
generateOralExplanation: async (context: MenuContext) => {
    await this.callAgentWithNodeQueue(
        context.nodeId,
        '口语化解释',  // 用户可见的名称
        async () => {
            new Notice('正在生成口语化解释... (预计25秒)');
            // ...
        }
    );
}
```

---

## 测试用例

### 手动测试

1. **同一节点快速点击不同Agent**
   - 右键节点A，点击"四层次解释"
   - 在处理中，再点击"口语化解释"
   - 预期: 显示 "节点正在处理 '四层次解释'，请稍候..."
   - 四层次完成后，口语化开始执行
   - 最终: 两份文档按顺序生成

2. **不同节点并发**
   - 右键节点A，点击"四层次解释"
   - 右键节点B，点击"口语化解释"
   - 预期: 两个请求并发执行
   - 最终: 各自生成一份文档

3. **同一节点同一Agent重复点击**
   - 右键节点A，点击"四层次解释"
   - 再次点击"四层次解释"
   - 预期: 显示 "相同请求处理中，请稍候..."

### 自动化测试

```typescript
describe('NodeRequestQueue', () => {
    let queue: NodeRequestQueue;

    beforeEach(() => {
        queue = new NodeRequestQueue();
    });

    it('should process same node requests sequentially', async () => {
        const order: number[] = [];

        const promise1 = queue.enqueue('node-1', 'agent-a', async () => {
            await sleep(100);
            order.push(1);
            return 'result-1';
        });

        const promise2 = queue.enqueue('node-1', 'agent-b', async () => {
            order.push(2);
            return 'result-2';
        });

        await Promise.all([promise1, promise2]);

        // 应该按顺序执行
        expect(order).toEqual([1, 2]);
    });

    it('should process different node requests concurrently', async () => {
        const results: string[] = [];

        const promise1 = queue.enqueue('node-1', 'agent-a', async () => {
            await sleep(100);
            results.push('node-1');
            return 'result-1';
        });

        const promise2 = queue.enqueue('node-2', 'agent-a', async () => {
            results.push('node-2');
            return 'result-2';
        });

        await Promise.all([promise1, promise2]);

        // node-2 应该先完成（因为没有等待）
        expect(results[0]).toBe('node-2');
    });

    it('should report processing status correctly', async () => {
        const promise = queue.enqueue('node-1', 'agent-a', async () => {
            await sleep(100);
            return 'result';
        });

        // 在执行中
        expect(queue.isProcessing('node-1')).toBe(true);
        expect(queue.getCurrentAgentType('node-1')).toBe('agent-a');

        await promise;

        // 执行完成
        expect(queue.isProcessing('node-1')).toBe(false);
        expect(queue.getCurrentAgentType('node-1')).toBeUndefined();
    });
});
```

---

## 需要修改的菜单项

| 菜单项 | Agent类型显示名 |
|--------|----------------|
| 澄清路径 | 澄清路径 |
| 四层次解释 | 四层次解释 |
| 基础拆解 | 基础拆解 |
| 深度拆解 | 深度拆解 |
| 口语化解释 | 口语化解释 |
| 例题教学 | 例题教学 |
| 记忆锚点 | 记忆锚点 |
| 对比表 | 对比表 |
| 问题拆解 | 问题拆解 |
| 生成检验问题 | 检验问题 |
| 评分 | 评分 |

---

## 依赖关系

- **前置依赖**: 无（可与 12.H.1 并行开发）
- **被依赖**: Story 12.H.3 (任务管理面板需要使用 NodeRequestQueue)

---

## Definition of Done

- [x] NodeRequestQueue 类实现 (Task 1)
- [x] 集成到 CanvasReviewPlugin (Task 2)
- [x] 所有 11 个 Agent 菜单项已更新 (Task 3)
- [x] 同一节点请求按顺序执行 (AC1, AC2, AC4)
- [x] 不同节点请求可以并发 (AC5)
- [x] 用户提示清晰 (AC3)
- [x] 单元测试验证通过 (16 tests, Task 4)
- [x] 插件构建并部署成功 (Task 5)

---

## Change Log

| 日期 | 版本 | 变更内容 | 作者 |
|------|------|---------|------|
| 2025-12-17 | 1.0 | 初始创建 Story | PO |
| 2025-12-17 | 1.1 | 添加 Tasks/Subtasks, Dev Notes (SDD/ADR), Change Log - 模板合规修复 | Sarah (PO Agent) |
| 2025-12-17 | 1.2 | 实现完成: NodeRequestQueue类 + callAgentWithNodeQueue方法 + 11个Agent菜单更新 + 构建部署 | James (Dev Agent) |

---

## QA Results

### Review Date: 2025-12-17

### Reviewed By: Quinn (Test Architect)

### Code Quality Assessment

**Overall**: HIGH QUALITY implementation with solid architecture. The NodeRequestQueue class demonstrates proper Promise chaining pattern for concurrent control, clean TypeScript generics usage, and excellent documentation. All 11 agent handlers successfully migrated to `callAgentWithNodeQueue`.

**Strengths Identified:**
- ✅ Well-documented JSDoc comments on all methods (lines 67-74, 115-119, 125-130)
- ✅ Proper TypeScript generics: `enqueue<T>()` preserves return types
- ✅ Clean integration with existing patterns (Story 12.F.4 dedup, 12.H.3 registry, 12.H.4 abort)
- ✅ Memory-safe cleanup in `finally` block (lines 100-106) prevents memory leaks
- ✅ Console logging with Story references aids debugging
- ✅ Backward compatibility: `callAgentWithLock` preserved at line 2179

**Code Locations:**
- `NodeRequestQueue` class: `main.ts:60-134`
- `callAgentWithNodeQueue` method: `main.ts:2226-2262`
- Agent handlers: `main.ts:411, 456, 503, 550, 646, 691, 738, 785, 832, 881, 928`

### Requirements Traceability (Given-When-Then)

| AC | Status | Verification |
|----|--------|--------------|
| **AC1**: Same node = one Agent at time | ✅ PASS | **Given** user clicks Agent A on node-1, **When** user clicks Agent B on node-1 before A completes, **Then** B is queued (Promise chain at line 92) |
| **AC2**: Queue subsequent requests | ✅ PASS | **Given** node-1 has running Agent, **When** new request arrives, **Then** request chains via `prev.then()` (line 92) |
| **AC3**: User notice | ✅ PASS | **Given** node is busy, **When** user clicks another Agent, **Then** Notice shows `"节点正在处理 '${currentAgent}'，请稍候..."` (line 84) |
| **AC4**: Queue executes in order | ✅ PASS | **Given** requests A, B queued for node-1, **When** A completes, **Then** B executes (FIFO via Promise chain) |
| **AC5**: Different nodes concurrent | ✅ PASS | **Given** node-1 has running Agent, **When** user clicks Agent on node-2, **Then** node-2 executes immediately (separate Map entries) |

### Refactoring Performed

No refactoring performed. Code quality meets standards.

### Compliance Check

- Coding Standards: ✓ TypeScript best practices followed
- Project Structure: ✓ Code in correct location (main.ts)
- Testing Strategy: ✓ **16 unit tests added** (see `tests/NodeRequestQueue.test.ts`)
- All ACs Met: ✓ All 5 ACs implemented correctly

### Improvements Checklist

- [x] NodeRequestQueue class implements Promise chaining correctly
- [x] callAgentWithNodeQueue integrates with 12.F.4/12.H.3/12.H.4
- [x] All 11 agent handlers updated (verified via grep)
- [x] User notices implemented in Chinese
- [x] **NodeRequestQueue unit tests added** (16 tests in `tests/NodeRequestQueue.test.ts`)
- [x] **Testing verification complete** (Task 4 - all tests pass)
- [ ] Restart Obsidian to verify (Task 5.3 - user action required)
- [ ] Consider: Queue timeout mechanism for stuck requests (future improvement)
- [ ] Consider: Max queue depth limit to prevent memory issues (future improvement)

### Security Review

**Status: PASS**
- No authentication/authorization code touched
- No sensitive data handling
- No external API keys exposed
- Input validation exists (`context.nodeId || ''` fallback)

### Performance Considerations

**Status: PASS**
- O(1) Map operations for queue lookup/insertion
- No blocking operations in critical path
- Memory cleanup in `finally` block prevents leaks
- Promise chaining is non-blocking

**Minor Observation:** No queue depth limit - theoretically unbounded memory if user queues many requests. Low risk for typical usage.

### Reliability Assessment

**Status: CONCERNS**
- No timeout mechanism for stuck Agent requests
- If Agent never returns, queue blocks forever for that node
- Mitigation: Story 12.H.4 provides AbortController support for cancellation

### Files Modified During Review

None. No refactoring required.

### Gate Status

**Gate: PASS** → `docs/qa/gates/12.H.2-node-concurrency-limit.yml`

**Reason:** All acceptance criteria implemented correctly with high-quality code. Unit tests added (16 tests, all passing). Only remaining item is user verification in Obsidian (Task 5.3).

### Recommended Status

**✓ Ready for Done** - All technical requirements met:
1. ✅ All 5 ACs implemented and tested
2. ✅ 16 unit tests added and passing
3. ⚠️ Task 5.3: Restart Obsidian to verify (user action)

Story can be marked Done after user verifies plugin in Obsidian.
