# Story 3.8: 对话归档与异步生成管理

Status: ready-for-dev

## Story

As a 用户,
I want 对话历史自动归档管理，切换节点时后台 AI 继续生成不中断,
so that 我的对话数据安全且不错过任何 AI 回答。

## Acceptance Criteria

1. **AC-1: Hot-Warm-Cold 三层归档**
   - **Given** 对话积累到一定量级
   - **When** 对话归档管道触发（时间 + 容量 50K tokens 双触发）
   - **Then** Hot（0-30天）：完整保留所有消息
   - **And** Warm（30天-6月）：LLM 生成对话摘要 + 结构化提取保留
   - **And** Cold（6月+）：仅保留结构化提取数据（错误/Tips/关键问答）
   - **And** 原始消息在 Warm/Cold 阶段不立即删除，标记为 archived

2. **AC-2: 结构化提取永久保存**
   - **Given** 对话进入 Warm/Cold 归档阶段
   - **When** 归档管道执行
   - **Then** LLM 从对话中提取结构化数据：
     - 错误记录（4 类分类，复用 Story 3.6 的分类器）
     - Tips（关键知识点）
     - 关键问答精选（按主题聚类）
   - **And** 提取结果永久保存到 Graphiti（对话蒸馏通道）
   - **And** 提取结果可在学习档案面板（Story 5.3）查看

3. **AC-3: 异步后台生成管理**
   - **Given** 用户在节点 A 对话中，AI 正在生成回复
   - **When** 用户切换到节点 B
   - **Then** 节点 A 的 AI 回答在后台继续生成（不取消进程）
   - **And** 节点 B 使用独立的 Claude Code 进程
   - **And** 节点 A 的生成完成后，消息自动保存到该节点的对话历史

4. **AC-4: 节点生成状态指示**
   - **Given** 有节点在后台生成中
   - **When** 白板渲染
   - **Then** 该节点显示生成状态指示：
     - 🔵 生成中（旋转动画）
     - 🟢 完成未读（绿色圆点，用户切回后消失）
     - ⚪ 空闲（无标记）
   - **And** 状态指示在节点右上角，不遮挡节点内容

5. **AC-5: 并发上限与排队**
   - **Given** 同时有 3 个节点在后台生成
   - **When** 用户在第 4 个节点发起对话
   - **Then** 第 4 个请求进入排队（不立即 spawn）
   - **And** 前 3 个中任一完成后，队列中的第一个自动开始
   - **And** 排队状态在 UI 中提示（"已排队，等待前面 1 个完成"）

## Tasks / Subtasks

- [ ] **Task 1: 归档管道引擎** (AC: #1, #2)
  - [ ] 1.1 创建 `backend/app/services/conversation_archive.py`
  - [ ] 1.2 实现 `ArchiveManager` 类：管理归档生命周期
  - [ ] 1.3 归档触发条件检测：每次对话结束时检查
    - 时间触发：消息创建时间 > 30天 → Hot→Warm
    - 时间触发：消息创建时间 > 6月 → Warm→Cold
    - 容量触发：单节点对话 tokens > 50K → 触发 Warm 归档
  - [ ] 1.4 实现 `archiveToWarm(nodeId)`: LLM 生成对话摘要 + 结构化提取
  - [ ] 1.5 实现 `archiveToCold(nodeId)`: 删除摘要，仅保留结构化提取
  - [ ] 1.6 归档后标记消息 `status: 'archived'`（不物理删除）

- [ ] **Task 2: 对话蒸馏提取** (AC: #2)
  - [ ] 2.1 创建 `backend/app/services/conversation_distiller.py`
  - [ ] 2.2 实现 `distillConversation(messages)`: LLM 提取结构化数据
  - [ ] 2.3 提取内容：
    - 错误记录：复用 `error_classifier.py`（Story 3.6）
    - Tips：关键知识点摘录
    - 关键问答：有价值的 Q&A 对，按主题聚类
    - 对话摘要：1-3 句话概括对话主题和收获
  - [ ] 2.4 提取结果写入 Graphiti（对话蒸馏通道）
  - [ ] 2.5 使用 LiteLLM 调用（成本敏感：用 Flash 模型，非主力模型）

- [ ] **Task 3: 归档定时任务** (AC: #1)
  - [ ] 3.1 创建 `backend/app/services/archive_scheduler.py`
  - [ ] 3.2 实现定时检查：FastAPI 启动时注册 `asyncio` 定时任务（每 24 小时检查一次）
  - [ ] 3.3 批量处理：每次最多处理 10 个节点的归档（防止长时间阻塞）
  - [ ] 3.4 归档进度日志记录

- [ ] **Task 4: 异步生成管理器** (AC: #3, #5)
  - [ ] 4.1 创建 `obsidian-canvas-learning/src/services/generation-manager.ts`
  - [ ] 4.2 实现 `GenerationManager` 类：
    - `activeGenerations: Map<string, ChildProcess>` — 活跃进程追踪
    - `queue: Array<PendingGeneration>` — 排队请求
    - `MAX_CONCURRENT = 3` — 并发上限
  - [ ] 4.3 `startGeneration(nodeId, message)`: 检查并发数 → 可用则 spawn / 已满则排队
  - [ ] 4.4 `onGenerationComplete(nodeId)`: 移除活跃记录 → 处理队列中下一个
  - [ ] 4.5 节点切换时：不取消活跃进程，保持后台运行

- [ ] **Task 5: 节点状态指示 UI** (AC: #4)
  - [ ] 5.1 创建 `obsidian-canvas-learning/src/components/canvas/NodeStatusIndicator.svelte`
  - [ ] 5.2 三种状态渲染：generating（旋转动画）/ unread（绿色圆点）/ idle（隐藏）
  - [ ] 5.3 在 CanvasNode 组件右上角渲染（z-index 高于节点内容）
  - [ ] 5.4 状态数据来源：`GenerationManager` 的状态 → 通过 Svelte Store 响应式绑定
  - [ ] 5.5 用户切换到该节点时：unread → idle（标记已读）

- [ ] **Task 6: 后端归档 API** (AC: #1)
  - [ ] 6.1 创建 `backend/app/api/v1/archive.py`
  - [ ] 6.2 `POST /api/v1/archive/trigger` — 手动触发归档检查
  - [ ] 6.3 `GET /api/v1/archive/status/{node_id}` — 查询节点归档状态
  - [ ] 6.4 `GET /api/v1/archive/summary/{node_id}` — 获取 Warm 阶段的对话摘要

## Dev Notes

### Hot-Warm-Cold 归档架构

```
Hot (0-30天) ──[30天 or 50K tokens]──> Warm (30天-6月) ──[6月]──> Cold (6月+)
     │                                      │                        │
     └─ 完整消息保留                          └─ 摘要 + 结构化提取       └─ 仅结构化提取
                                             └─ 原始消息标记 archived     └─ 可选删除原始
```

### 异步生成管理器并发模型

```
MAX_CONCURRENT = 3

用户在节点A发送消息 → spawn 进程 A (active: [A])
用户切到节点B发送   → spawn 进程 B (active: [A, B])
用户切到节点C发送   → spawn 进程 C (active: [A, B, C])
用户切到节点D发送   → 排队 D      (active: [A, B, C], queue: [D])
进程A完成          → 出队 D       (active: [B, C, D])
```

### 生成状态管理

```typescript
// generation-manager.ts
type GenerationStatus = 'generating' | 'unread' | 'idle';

class GenerationManager {
  private active = new Map<string, ChildProcess>();
  private queue: PendingGeneration[] = [];
  private status = $state(new Map<string, GenerationStatus>());

  get nodeStatus() { return this.status; } // Svelte Store 响应式
}
```

### 关键约束

1. **归档不删除**：Warm/Cold 阶段标记 `archived`，不物理删除原始消息（可恢复）
2. **蒸馏用 Flash 模型**：归档提取是批量任务，用低成本模型（LiteLLM 任务路由）
3. **并发上限 3**：受限于 Claude Code 订阅额度并发策略（避免触发 rate limit）
4. **进程隔离**：每个节点的 spawn 进程完全独立，一个崩溃不影响其他
5. **归档触发**：双触发机制（时间 + 容量），任一满足即触发

### 不做的事项（防蔓延）

- 不实现学习档案面板的提取数据展示（Story 5.3）
- 不实现对话归档 UI（用户感知归档仅通过学习档案面板）
- 不实现手动归档（仅自动触发）
- 不实现 Cold 阶段的物理删除策略（标记即可）
- 不实现跨节点的对话摘要合并

### Project Structure Notes

- 后端新建：`backend/app/services/conversation_archive.py`
- 后端新建：`backend/app/services/conversation_distiller.py`
- 后端新建：`backend/app/services/archive_scheduler.py`
- 后端新建：`backend/app/api/v1/archive.py`
- 前端新建：`obsidian-canvas-learning/src/services/generation-manager.ts`
- 前端新建：`obsidian-canvas-learning/src/components/canvas/NodeStatusIndicator.svelte`

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.8] — Story 需求和 AC
- [Source: _bmad-output/planning-artifacts/architecture.md#Requirements Overview] — Hot-Warm-Cold 三层归档 + 异步并发管理
- [Source: _bmad-output/planning-artifacts/architecture.md#Cross-Cutting Concerns] — 对话归档生命周期

## Dev Agent Record

### Agent Model Used

(to be filled by dev agent)

### Debug Log References

### Completion Notes List

### File List
