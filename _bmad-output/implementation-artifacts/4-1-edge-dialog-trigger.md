# Story 4.1: Edge 可交互图标与对话触发

Status: ready-for-dev

## Story

As a 用户,
I want 创建连线后看到连线上的可交互图标，点击后右侧面板切换为 Edge 对话,
so that 我能方便地讨论两个概念之间的关系。

## Acceptance Criteria

1. **AC-1: EdgeDialogTrigger 可交互图标渲染**
   - **Given** 用户拖拽创建两个节点之间的连线
   - **When** 连线创建完成
   - **Then** 连线中点位置渲染 EdgeDialogTrigger Svelte 组件（小图标）
   - **And** 图标在 SVG 边渲染层正确叠加，不遮挡连线本身
   - **And** 图标跟随连线位置更新（节点拖拽时实时重新计算中点）
   - **And** 图标具有 hover 状态视觉反馈（放大/高亮）
   - **And** 图标使用 `cl-canvas-` CSS 前缀，适配 Light/Dark 主题

2. **AC-2: 首次连线引导提示**
   - **Given** 用户首次创建连线（系统检测无 Edge 对话使用记录）
   - **When** EdgeDialogTrigger 图标出现
   - **Then** 图标旁显示引导提示文字"点击讨论关系"
   - **And** 提示为非模态灰色浮层，2-3 秒后自动消失
   - **And** 用户点击图标一次后，后续连线不再显示引导提示
   - **And** 引导提示状态持久化到 IndexedDB（重启后不重复显示）

3. **AC-3: 右侧面板切换为 Edge 对话模式**
   - **Given** 用户点击 Edge 上的 EdgeDialogTrigger 图标
   - **When** 点击事件触发
   - **Then** 右侧面板从当前视图（节点对话/Dashboard/学习档案等）切换为 Edge 对话模式
   - **And** 切换即替换不叠加（右侧面板单视图模式）
   - **And** ChatPanel 接收 mode='edge' props，切换为 Edge Q&A 界面
   - **And** ChatPanel 头部显示 Edge 两端节点名称（如"A ↔ B"）
   - **And** 面板切换无加载感，体验流畅

4. **AC-4: Edge 对话上下文注入**
   - **Given** ChatPanel 进入 Edge 模式
   - **When** Agent session 初始化
   - **Then** 通过 --append-system-prompt 注入两端节点的上下文（节点名称、内容摘要、已有 Tips、已有错误记录）
   - **And** 注入 Edge 对话预设 prompt（引导 Agent 主动询问连线理由）
   - **And** Edge 对话使用独立的 session（edge_{edgeId}），不与节点对话 session 混淆

5. **AC-5: 已有 Edge 理由的回显**
   - **Given** 用户点击一条已经有理由记录的 Edge
   - **When** Edge 对话面板打开
   - **Then** 对话历史中显示之前的理由记录和对话
   - **And** Agent 可基于已有理由继续追问或讨论
   - **And** 用户可修改/补充之前的理由

6. **AC-6: 白板操作响应性能**
   - **Given** 白板上有多条连线均显示 EdgeDialogTrigger 图标
   - **When** 用户拖拽节点、缩放画布、平移画布
   - **Then** 所有 EdgeDialogTrigger 图标位置实时更新，无卡顿
   - **And** 白板操作响应 < 16ms（60fps）
   - **And** 视口外的 EdgeDialogTrigger 不渲染（视口裁剪优化）

## Tasks / Subtasks

- [ ] **Task 1: EdgeDialogTrigger 组件实现** (AC: #1)
  - [ ] 1.1 创建 `src/components/canvas/EdgeDialogTrigger.svelte`，接收 edge 数据（sourceNode, targetNode, edgeId）
  - [ ] 1.2 计算连线中点坐标（基于源/目标节点位置），实现响应式位置更新
  - [ ] 1.3 实现 hover 状态视觉效果（CSS transition 放大 + 颜色高亮）
  - [ ] 1.4 使用 Svelte scoped CSS + `cl-canvas-edge-trigger` 类名，引用 Obsidian CSS 变量适配主题
  - [ ] 1.5 实现视口裁剪：仅当 Edge 在视口内时渲染 trigger（ViewportCuller 协作）

- [ ] **Task 2: CanvasEdge 集成 EdgeDialogTrigger** (AC: #1)
  - [ ] 2.1 在 `src/components/canvas/CanvasEdge.svelte` 中集成 EdgeDialogTrigger
  - [ ] 2.2 连线创建时自动渲染 trigger，连线删除时自动销毁
  - [ ] 2.3 节点拖拽时实时更新 trigger 位置（通过 Svelte reactive 绑定）

- [ ] **Task 3: 首次引导提示** (AC: #2)
  - [ ] 3.1 在 IndexedDB（Dexie）schema 中添加 `edgeDialogGuideShown: boolean` 字段
  - [ ] 3.2 EdgeDialogTrigger 组件内实现条件渲染引导提示浮层
  - [ ] 3.3 实现 2-3 秒自动消失动画（CSS fade-out）
  - [ ] 3.4 用户首次点击 trigger 后标记 `edgeDialogGuideShown = true`

- [ ] **Task 4: ChatPanel Edge 模式切换** (AC: #3, #4)
  - [ ] 4.1 在 `src/stores/chat-state.svelte.ts` 中扩展 chatMode 状态：'normal' | 'exam' | 'edge'
  - [ ] 4.2 添加 currentEdge 状态字段（edgeId, sourceNodeName, targetNodeName）
  - [ ] 4.3 EdgeDialogTrigger 点击事件 → 更新 chatMode='edge' + currentEdge 数据
  - [ ] 4.4 ChatPanel 根据 mode='edge' 渲染 Edge 对话头部（"A ↔ B"标识）
  - [ ] 4.5 Edge 对话 session 使用 `edge_{edgeId}` 作为 sessionId（区别于节点 session）

- [ ] **Task 5: Edge 对话上下文注入** (AC: #4)
  - [ ] 5.1 在 `src/services/agent-bridge.ts` 中实现 Edge 模式上下文组装
  - [ ] 5.2 组装两端节点上下文（名称、内容摘要、Tips、错误记录）为 system prompt 片段
  - [ ] 5.3 添加 Edge 对话预设 prompt 模板（引导 Agent 询问"为什么把 A 和 B 连在一起"）
  - [ ] 5.4 通过 --append-system-prompt 注入组装后的上下文

- [ ] **Task 6: 已有理由回显** (AC: #5)
  - [ ] 6.1 ChatPanel Edge 模式打开时，查询该 Edge 的历史对话记录（通过 session resume）
  - [ ] 6.2 如已有理由，显示之前的对话历史
  - [ ] 6.3 Agent 可基于历史继续交互（Options.resume 机制）

- [ ] **Task 7: 性能优化与测试** (AC: #6)
  - [ ] 7.1 实现视口裁剪逻辑：viewport bounds 判定，视口外 trigger 不挂载
  - [ ] 7.2 多连线场景压测：20+ 连线时拖拽/缩放流畅度验证
  - [ ] 7.3 创建 `__tests__/components/EdgeDialogTrigger.test.ts`：
    - 渲染验证、位置计算、hover 状态、点击事件、引导提示条件渲染
  - [ ] 7.4 创建 `__tests__/unit/stores/chat-state-edge.test.ts`：
    - chatMode 切换、currentEdge 状态管理、edge session ID 生成

## Dev Notes

### 架构约束——同 Agent 同 Story

**关键约束**（[Source: architecture.md#跨组实现约束]）：

> EdgeDialog(E) + ChatPanel Edge模式(A) 必须同 Agent 同 Story

本 Story 实现 EdgeDialogTrigger（E 组白板组件）+ ChatPanel Edge 模式切换（A 组对话组件）。两个跨组组件在同一个 Story 中实现以确保 Edge 对话一致性。

### Layer 3 创新——回退策略

Edge 对话是 Layer 3 创新功能。如果本 Story 的 Edge 对话触发机制失败，回退策略是退化为静态标签边（Story 4.4 负责）。本 Story 应确保 EdgeDialogTrigger 的 UI 渲染与 Agent 可用性解耦——即使 Agent 不可用，图标仍然可见。

### ChatPanel 三模式复用

ChatPanel 是三模式复用组件（普通/考察/Edge），通过 props 切换差异化 UI：

- `mode='normal'`：节点对话（头部显示节点名称）
- `mode='exam'`：检验考察（头部显示考察状态）
- `mode='edge'`：Edge Q&A（头部显示 "A ↔ B"）

使用 Svelte 5 Snippet 注入差异化 UI 片段。

### 右侧面板单视图模式

右侧面板永远只显示一个视图，切换即替换不叠加（[Source: ux-design-specification.md#面板切换模式]）。点击 Edge 图标时，无论当前面板显示什么内容，都直接替换为 Edge 对话。

### CSS 隔离

- EdgeDialogTrigger 属 E 组白板，CSS 前缀 `cl-canvas-`
- ChatPanel 属 A 组对话，CSS 前缀 `cl-chat-`
- 两组 CSS 独立不交叉，通过 Svelte scoped CSS 隔离

### Project Structure Notes

- `src/components/canvas/EdgeDialogTrigger.svelte` — 新建，E 组白板
- `src/components/canvas/CanvasEdge.svelte` — 修改，集成 trigger
- `src/components/chat/ChatPanel.svelte` — 修改，添加 Edge 模式分支
- `src/stores/chat-state.svelte.ts` — 修改，扩展 chatMode + currentEdge
- `src/services/agent-bridge.ts` — 修改，添加 Edge 上下文组装
- `src/services/dexie-db.ts` — 修改，添加引导提示状态字段

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story4.1] — AC 原文
- [Source: _bmad-output/planning-artifacts/architecture.md#跨组实现约束] — EdgeDialog + ChatPanel 同 Agent 同 Story
- [Source: _bmad-output/planning-artifacts/architecture.md#前端组件目录] — EdgeDialog.svelte 位于 canvas/ 目录
- [Source: _bmad-output/planning-artifacts/architecture.md#能力域3] — Edge 对话架构含义
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#核心交互2] — Edge 连线 -> Agent Q&A 四步流程
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#E组] — EdgeDialogTrigger 组件归属
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#面板切换模式] — 右侧面板单视图切换
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Implementation Strategy] — ChatPanel 三模式复用

## Dev Agent Record

### Agent Model Used

(待开发时填写)

### Debug Log References

(待开发时填写)

### Completion Notes List

(待开发时填写)

### File List

- `src/components/canvas/EdgeDialogTrigger.svelte` — 新建
- `src/components/canvas/CanvasEdge.svelte` — 修改（集成 trigger）
- `src/components/chat/ChatPanel.svelte` — 修改（Edge 模式分支）
- `src/stores/chat-state.svelte.ts` — 修改（chatMode 扩展）
- `src/services/agent-bridge.ts` — 修改（Edge 上下文组装）
- `src/services/dexie-db.ts` — 修改（引导提示状态）
- `__tests__/components/EdgeDialogTrigger.test.ts` — 新建
- `__tests__/unit/stores/chat-state-edge.test.ts` — 新建
