# Story 4.4: Edge 对话回退策略

Status: ready-for-dev

## Story

As a 开发者,
I want Edge 对话功能失败时优雅退化为静态标签边,
so that 系统不会因为 Layer 3 创新失败而崩溃。

## Acceptance Criteria

1. **AC-1: Agent 不可用时退化为静态标签编辑**
   - **Given** Edge 对话功能出现异常（Agent 不可用 / Claude Code spawn 失败 / MCP 断连）
   - **When** 用户点击 Edge 上的 EdgeDialogTrigger 图标
   - **Then** 右侧面板不显示 Edge 对话（因 Agent 不可用），改为就地弹出标签编辑 UI
   - **And** 用户可手动输入关系标签文字（如"是前提条件"、"是特殊情况"等）
   - **And** 手动输入的标签保存到 Edge 的 label 属性中，白板上可见
   - **And** 手动标签同步到 IndexedDB + Neo4j（走正常 delta sync 通道）

2. **AC-2: 降级提示通知**
   - **Given** Agent 不可用导致 Edge 对话降级
   - **When** 用户点击 EdgeDialogTrigger 图标
   - **Then** 显示提示"AI 对话暂时不可用，已切换为手动标签模式"
   - **And** 提示为橙色通知条（面板顶部样式），持续到用户关闭或 Agent 恢复
   - **And** 提示不阻塞标签编辑操作
   - **And** Agent 恢复后，提示自动消失，后续点击 EdgeDialogTrigger 恢复 Edge 对话模式

3. **AC-3: MCP 工具调用失败回退**
   - **Given** Edge 对话中 Agent 调用 record_edge_rationale MCP 工具
   - **When** MCP 工具调用失败（网络/后端/超时）
   - **Then** Agent 在对话中告知用户"理由保存遇到问题，稍后重试"
   - **And** 理由数据放入 Outbox 队列等待重试（指数退避，最多 3 次）
   - **And** 对话本身不中断——用户可继续与 Agent 讨论
   - **And** Outbox 重试成功后，Edge 标签正常更新

4. **AC-4: 双写部分失败处理**
   - **Given** record_edge_rationale 执行双写
   - **When** Graphiti 写入成功但 LanceDB 写入失败（或反之）
   - **Then** 成功的部分保留，失败的部分进入 Outbox 单独重试
   - **And** 不因部分失败回滚已成功的写入
   - **And** 双写全部失败时，对话中 Agent 显示"理由暂存本地，稍后同步"
   - **And** 理由临时写入 IndexedDB 暂存，等后端恢复后重试双写

5. **AC-5: 已记录 Edge 理由不丢失**
   - **Given** 系统出现异常（Agent 崩溃 / 后端重启 / 网络中断）
   - **When** 异常发生时有未完成的 Edge 对话
   - **Then** 之前已通过 MCP 成功记录的 Edge 理由不受影响（Graphiti + LanceDB 持久化）
   - **And** 当前对话中已输入但未保存的内容，通过 session resume 恢复（Claude Code session 持久化）
   - **And** IndexedDB 暂存的理由数据在后端恢复后自动同步

6. **AC-6: 降级状态检测与恢复**
   - **Given** 系统处于 Edge 对话降级模式
   - **When** Agent 恢复可用（Agent bridge 检测到连接恢复）
   - **Then** 自动退出降级模式，后续点击 EdgeDialogTrigger 恢复 Edge 对话
   - **And** 降级期间手动输入的标签保留不丢失
   - **And** Agent 恢复后，手动标签可通过 Edge 对话进一步讨论和结构化

7. **AC-7: EdgeDialogTrigger 图标始终可见**
   - **Given** 无论 Agent 是否可用
   - **When** 白板上有连线
   - **Then** EdgeDialogTrigger 图标始终渲染（不因 Agent 不可用而隐藏）
   - **And** 图标外观可区分当前模式：正常模式（彩色）vs 降级模式（灰色/虚线）
   - **And** 降级模式下 hover 提示文字改为"手动添加标签"

## Tasks / Subtasks

- [ ] **Task 1: Agent 可用性检测** (AC: #1, #6)
  - [ ] 1.1 在 `src/services/agent-bridge.ts` 中实现 Agent 可用性状态检测方法 `isAgentAvailable(): boolean`
  - [ ] 1.2 检测逻辑：Claude Code 进程存活 + MCP 连接正常 + 最近一次心跳 < 30s
  - [ ] 1.3 将 Agent 可用性状态暴露到 `src/stores/system-state.svelte.ts`
  - [ ] 1.4 实现状态恢复监听：Agent 重新可用时触发状态更新

- [ ] **Task 2: EdgeDialogTrigger 降级模式 UI** (AC: #7)
  - [ ] 2.1 EdgeDialogTrigger 组件读取 Agent 可用性状态
  - [ ] 2.2 正常模式：彩色图标 + hover 提示"点击讨论关系"
  - [ ] 2.3 降级模式：灰色/虚线图标 + hover 提示"手动添加标签"
  - [ ] 2.4 CSS 变体使用 Svelte 条件类名 `cl-canvas-edge-trigger--degraded`

- [ ] **Task 3: 静态标签编辑 UI** (AC: #1)
  - [ ] 3.1 创建 `src/components/canvas/EdgeLabelEditor.svelte`：
    - 就地弹出的轻量编辑框（点击 EdgeDialogTrigger 时出现）
    - 输入框 + 确认按钮 + 取消按钮
    - 输入后回车确认，Escape 取消
  - [ ] 3.2 标签保存到 Edge 的 label 属性（IndexedDB → Neo4j delta sync）
  - [ ] 3.3 CSS 前缀 `cl-canvas-edge-label-editor`，适配 Light/Dark 主题

- [ ] **Task 4: 降级提示通知** (AC: #2)
  - [ ] 4.1 在 EdgeDialogTrigger 点击处理中添加 Agent 不可用分支
  - [ ] 4.2 不可用时显示 Obsidian Notice（橙色提示条）："AI 对话暂时不可用，已切换为手动标签模式"
  - [ ] 4.3 Agent 恢复后自动清除降级提示

- [ ] **Task 5: MCP 工具调用失败处理** (AC: #3)
  - [ ] 5.1 在 `src/services/agent-bridge.ts` 中 Edge 对话的 MCP 工具调用添加 try-catch
  - [ ] 5.2 调用失败时将理由数据放入 Outbox 队列（复用 `src/services/sync-engine.ts` Outbox 模式）
  - [ ] 5.3 Outbox 重试：指数退避（1s/2s/4s），最多 3 次
  - [ ] 5.4 重试成功后触发 Edge 标签 UI 更新

- [ ] **Task 6: 双写部分失败处理** (AC: #4)
  - [ ] 6.1 在 `backend/app/api/v1/endpoints/edges.py` 的 record_edge_rationale 中实现部分失败处理
  - [ ] 6.2 Graphiti 写入和 LanceDB 写入独立 try-catch
  - [ ] 6.3 部分成功时返回 partial_success 状态码（207）+ 失败详情
  - [ ] 6.4 前端接收 207 后，将失败部分放入 Outbox 单独重试
  - [ ] 6.5 全部失败时前端将理由临时写入 IndexedDB 暂存

- [ ] **Task 7: IndexedDB 理由暂存** (AC: #4, #5)
  - [ ] 7.1 在 Dexie schema 中添加 `pendingEdgeRationales` 表：edge_id, rationale_data, created_at, retry_count
  - [ ] 7.2 后端恢复后，SyncEngine 自动检测 pending rationales 并重试双写
  - [ ] 7.3 重试成功后从 pendingEdgeRationales 表删除

- [ ] **Task 8: 数据不丢失验证** (AC: #5)
  - [ ] 8.1 验证场景：Edge 对话中途 Agent 崩溃 → session resume 恢复对话
  - [ ] 8.2 验证场景：record_edge_rationale 双写失败 → IndexedDB 暂存 → 后端恢复 → 自动同步
  - [ ] 8.3 验证场景：降级模式手动标签 → Agent 恢复 → 手动标签保留 + 可继续对话

- [ ] **Task 9: 测试** (AC: #1-#7)
  - [ ] 9.1 创建 `__tests__/components/EdgeDialogTrigger-fallback.test.ts`：
    - Agent 可用时点击 → 打开 Edge 对话
    - Agent 不可用时点击 → 打开标签编辑器
    - 降级模式图标样式变化
    - Agent 恢复后自动切换回正常模式
  - [ ] 9.2 创建 `__tests__/unit/services/edge-fallback.test.ts`：
    - MCP 调用失败 → Outbox 入队 → 重试成功
    - 双写部分失败 → 部分保留 + 失败重试
    - IndexedDB 暂存 → 后端恢复 → 自动同步
  - [ ] 9.3 创建 `backend/tests/unit/test_edge_rationale_fallback.py`：
    - record_edge_rationale 双写部分失败返回 207
    - Graphiti 异常不影响 LanceDB 写入（独立 try-catch）
    - LanceDB 异常不影响 Graphiti 写入
  - [ ] 9.4 编辑后运行 `ruff check` 确认 lint 通过

## Dev Notes

### Layer 3 回退策略

Edge 对话是 Layer 3 创新功能（[Source: architecture.md#能力域3]、[Source: epics.md#Epic4]）。回退策略是退化为静态标签边——这与 Heptabase 当前的连线标签功能相当。回退不丢失任何用户数据。

### 回退层次

| 层次 | 触发条件 | 行为 |
|------|---------|------|
| **L0: 正常** | Agent 可用 + MCP 正常 | Edge 对话全功能 |
| **L1: MCP 工具失败** | Agent 可用但后端 MCP 不可用 | 对话正常但理由暂存 Outbox |
| **L2: Agent 不可用** | Claude Code 进程不可用 | 退化为静态标签编辑 |
| **L3: 全部不可用** | Agent + 后端都不可用 | 标签编辑 + IndexedDB 暂存 |

### 数据不丢失保障

三层数据保障机制：

1. **Session 持久化**：Claude Code session 自动持久化对话历史，crash 后可 resume
2. **Outbox 队列**：MCP 调用失败的理由数据进入 Outbox，恢复后自动重试
3. **IndexedDB 暂存**：双写全部失败时理由临时写入 IndexedDB，后端恢复后自动同步

### 与 Story 3.9 (Engine Fallback) 的关系

Story 3.9 处理 Claude Code spawn 失败的全局 fallback。本 Story 在此基础上处理 Edge 对话特定的降级逻辑：
- Story 3.9：Agent 不可用 → 全局通知 + 切换 API Key 模式
- Story 4.4：Agent 不可用 → Edge 特定降级 → 静态标签编辑

### 降级期间手动标签的后续处理

降级期间用户输入的手动标签存储在 Edge 的 label 属性中。当 Agent 恢复后：
- 手动标签保留不丢失
- 用户点击 Edge 可进入 Edge 对话，Agent 能看到已有的手动标签
- Agent 可基于手动标签继续追问和结构化（将手动标签提取为 KG-triplet）

### Project Structure Notes

- `src/components/canvas/EdgeDialogTrigger.svelte` — 修改（降级模式 UI）
- `src/components/canvas/EdgeLabelEditor.svelte` — 新建（静态标签编辑器）
- `src/services/agent-bridge.ts` — 修改（Agent 可用性检测 + 降级处理）
- `src/stores/system-state.svelte.ts` — 修改（Agent 可用性状态）
- `src/services/sync-engine.ts` — 修改（Edge 理由 Outbox 支持）
- `src/services/dexie-db.ts` — 修改（pendingEdgeRationales 表）
- `backend/app/api/v1/endpoints/edges.py` — 修改（双写部分失败处理）

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story4.4] — AC 原文
- [Source: _bmad-output/planning-artifacts/architecture.md#能力域3] — Layer 3 回退：退化为静态标签边
- [Source: _bmad-output/planning-artifacts/architecture.md#离线降级4场景] — 4 种离线降级策略
- [Source: _bmad-output/planning-artifacts/architecture.md#Cross-Cutting Concerns] — Outbox 模式 + CircuitBreaker 降级
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#反馈模式] — 橙色通知条持续到恢复
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Design Anti-Patterns] — Heptabase 连线只是静态标签（我们的回退底线）
- [Source: _bmad-output/planning-artifacts/prd.md#NFR-REL-01~05] — 数据零丢失 + 错误不静默

## Dev Agent Record

### Agent Model Used

(待开发时填写)

### Debug Log References

(待开发时填写)

### Completion Notes List

(待开发时填写)

### File List

- `src/components/canvas/EdgeDialogTrigger.svelte` — 修改（降级模式）
- `src/components/canvas/EdgeLabelEditor.svelte` — 新建
- `src/services/agent-bridge.ts` — 修改（可用性检测）
- `src/stores/system-state.svelte.ts` — 修改（Agent 状态）
- `src/services/sync-engine.ts` — 修改（Outbox 支持）
- `src/services/dexie-db.ts` — 修改（pendingEdgeRationales）
- `backend/app/api/v1/endpoints/edges.py` — 修改（部分失败处理）
- `__tests__/components/EdgeDialogTrigger-fallback.test.ts` — 新建
- `__tests__/unit/services/edge-fallback.test.ts` — 新建
- `backend/tests/unit/test_edge_rationale_fallback.py` — 新建
