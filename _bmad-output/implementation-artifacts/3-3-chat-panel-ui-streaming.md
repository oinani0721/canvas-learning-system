# Story 3.3: 对话面板 UI（ChatPanel + 流式输出）

Status: ready-for-dev

## Story

As a 用户,
I want 在右侧面板看到美观的对话界面，消息流式显示，支持 Markdown 渲染和代码高亮,
so that 对话体验流畅自然。

## Acceptance Criteria

1. **AC-1: ChatPanel Svelte 组件**
   - **Given** 用户点击节点打开对话
   - **When** 右侧面板切换到对话视图
   - **Then** 显示 ChatPanel 组件，包含消息列表区域和底部输入栏
   - **And** 用户消息右对齐深色气泡（`.cl-chat-bubble-user`）
   - **And** Agent 消息左对齐浅色气泡（`.cl-chat-bubble-agent`）
   - **And** 适配 Obsidian Light/Dark 主题（使用 `var(--background-primary)` 等 CSS 变量）

2. **AC-2: 流式文本渲染**
   - **Given** 用户发送消息
   - **When** Claude Code 返回 stream-json NDJSON 流
   - **Then** 实时逐字渲染 Agent 回复（不等全部完成）
   - **And** 显示 StreamingIndicator（打字动画 / 光标闪烁）
   - **And** 流式输出期间输入栏禁用（防止重复发送）

3. **AC-3: Markdown 渲染与代码高亮**
   - **Given** Agent 回复包含 Markdown 内容
   - **When** 消息渲染
   - **Then** 使用 Obsidian `MarkdownRenderer.render()` 渲染 Markdown
   - **And** 代码块有语法高亮（Obsidian 内置 Prism.js）
   - **And** 数学公式正确渲染（MathJax/KaTeX，Obsidian 内置）
   - **And** 渲染结果在 `.cl-chat-markdown` 容器内，CSS 隔离不影响外部

4. **AC-4: 对话历史持久化与加载**
   - **Given** 用户重新打开节点对话
   - **When** ChatPanel 加载
   - **Then** 从 SQLite 加载该节点的对话历史显示在面板中
   - **And** 对话历史跨 Obsidian session 持久化（关闭重开不丢失）
   - **And** 历史消息懒加载（初始显示最近 50 条，上滑加载更多）

5. **AC-5: 输入体验**
   - **Given** 用户在输入栏
   - **When** 按 Enter 发送消息 / Shift+Enter 换行 / Escape 取消
   - **Then** 快捷键行为符合 UX 规范
   - **And** 输入栏支持多行文本（自动扩展高度，最多 6 行）
   - **And** 空消息不可发送（发送按钮禁用）

6. **AC-6: 首 Token 性能**
   - **Given** 用户发送消息
   - **When** 等待 Agent 响应
   - **Then** 对话首 token < 2s（NFR-PERF-03）
   - **And** 超过 2s 显示等待提示（"正在思考..."）

## Tasks / Subtasks

- [ ] **Task 1: ChatPanel 组件骨架** (AC: #1)
  - [ ] 1.1 创建 `obsidian-canvas-learning/src/components/chat/ChatPanel.svelte`
  - [ ] 1.2 三区域布局：顶部标题栏（节点名称 + 状态指示）/ 中部消息列表 / 底部输入栏
  - [ ] 1.3 CSS 使用 Obsidian 变量：`--background-primary`, `--text-normal`, `--interactive-accent`
  - [ ] 1.4 所有 CSS 类名 `.cl-chat-*` 前缀

- [ ] **Task 2: MessageBubble 组件** (AC: #1, #3)
  - [ ] 2.1 创建 `obsidian-canvas-learning/src/components/chat/MessageBubble.svelte`
  - [ ] 2.2 根据 `role` prop 决定样式：user（右对齐深色）/ assistant（左对齐浅色）
  - [ ] 2.3 assistant 消息使用 `MarkdownRenderer.render()` 渲染
  - [ ] 2.4 渲染容器 `.cl-chat-markdown` 做 CSS 隔离（防止 Markdown 样式泄漏）
  - [ ] 2.5 消息底部显示时间戳（相对时间："刚刚" / "3分钟前"）

- [ ] **Task 3: InputBar 组件** (AC: #5)
  - [ ] 3.1 创建 `obsidian-canvas-learning/src/components/chat/InputBar.svelte`
  - [ ] 3.2 `<textarea>` 多行输入，auto-resize（min 1 行 max 6 行）
  - [ ] 3.3 键盘事件：Enter 发送 / Shift+Enter 换行 / Escape 清空
  - [ ] 3.4 发送按钮：空消息禁用 / 流式输出中禁用
  - [ ] 3.5 `/` 字符触发事件（供 Story 3.5 SkillSelector 消费，此处仅 emit 事件）

- [ ] **Task 4: 流式渲染管道** (AC: #2, #6)
  - [ ] 4.1 创建 `obsidian-canvas-learning/src/components/chat/StreamingIndicator.svelte`
  - [ ] 4.2 在 `chat-state.svelte.ts` 中实现流式消息追加：`appendStreamChunk(text: string)`
  - [ ] 4.3 接收 Story 3.1 的 `StreamEvent`，逐 chunk 更新当前 assistant 消息
  - [ ] 4.4 流完成后标记消息为 `complete`（触发完整 Markdown 渲染）
  - [ ] 4.5 2s 超时显示"正在思考..."提示

- [ ] **Task 5: 对话历史存储** (AC: #4)
  - [ ] 5.1 扩展 `session-store.ts`（Story 3.1）添加 `messages` 表
  - [ ] 5.2 `messages` schema：`id TEXT PK, nodeId TEXT, role TEXT, content TEXT, createdAt TEXT, metadata TEXT`
  - [ ] 5.3 实现 `saveMessage` / `loadMessages(nodeId, limit, offset)` 方法
  - [ ] 5.4 消息保存时机：用户发送后立即存 / Agent 完成后存（流完成）
  - [ ] 5.5 懒加载：初始 50 条，IntersectionObserver 触发上滑加载

- [ ] **Task 6: ItemView 集成** (AC: #1)
  - [ ] 6.1 扩展 `main-view.ts`（Story 1.1）支持 ChatPanel 视图模式
  - [ ] 6.2 右侧面板视图切换逻辑：Dashboard / Chat / Profile（单视图模式，切换即替换）
  - [ ] 6.3 节点点击事件 → 切换到 Chat 视图 → mount ChatPanel

## Dev Notes

### ChatPanel 三模式设计

ChatPanel 组件设计为三模式复用（普通/考察/Edge），此 Story 仅实现普通对话模式。考察模式（Story 6.x）和 Edge 模式（Story 4.x）通过 Svelte 5 Snippet 注入差异化 UI。

```svelte
<!-- ChatPanel.svelte -->
<script lang="ts">
  let { mode = 'chat', nodeId, ... } = $props();
  // mode: 'chat' | 'exam' | 'edge'
</script>
```

### Markdown 渲染方式

使用 Obsidian 原生 `MarkdownRenderer.render()` 而非第三方库：
```typescript
import { MarkdownRenderer, Component } from 'obsidian';

// 在 MessageBubble 中渲染
const container = document.createElement('div');
container.classList.add('cl-chat-markdown');
await MarkdownRenderer.render(app, content, container, sourcePath, component);
```

### CSS 隔离策略

```css
/* styles.css */
.cl-chat-panel { /* 面板容器 */ }
.cl-chat-bubble-user { background: var(--interactive-accent); color: var(--text-on-accent); }
.cl-chat-bubble-agent { background: var(--background-secondary); }
.cl-chat-markdown { /* Markdown 渲染容器，隔离样式 */ }
.cl-chat-input { /* 输入栏 */ }
.cl-chat-streaming { /* 流式指示器 */ }
```

### 关键约束

1. **右侧面板单视图模式**：切换即替换不叠加（UX 规范）
2. **MarkdownRenderer.render()**：Obsidian 原生 API，支持内部链接、代码高亮、数学公式
3. **CSS 变量**：必须使用 Obsidian 400+ CSS 变量体系，不硬编码颜色
4. **Svelte 5 mount/unmount**：ItemView 中使用 `mount()` / `unmount()`
5. **消息存储**：SQLite（与 Story 3.1 共用数据库文件），不用 IndexedDB 存消息

### 不做的事项（防蔓延）

- 不实现 /命令 SkillSelector（Story 3.5，此处仅 emit 事件）
- 不实现 Tips 标注浮动面板（Story 3.6）
- 不实现文字拖出创建节点（Story 3.7）
- 不实现考察模式 / Edge 模式（Story 6.x / 4.x）
- 不实现 Agent 工具调用 UI 展示（如展示"正在查询精通度..."）
- 不实现双向链接跳转（Story 3.4 的一部分）

### Project Structure Notes

- 新建 Svelte 组件在 `obsidian-canvas-learning/src/components/chat/` 目录
- 组件文件名 PascalCase.svelte：`ChatPanel.svelte`, `MessageBubble.svelte`, `InputBar.svelte`, `StreamingIndicator.svelte`
- CSS 在组件内 scoped + 全局 `styles.css` 中定义 `.cl-chat-*` 变量映射

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.3] — Story 需求和 AC
- [Source: _bmad-output/planning-artifacts/architecture.md#Frontend Architecture] — ChatPanel 三模式复用
- [Source: _bmad-output/planning-artifacts/architecture.md#Structure Patterns] — 前端组件命名和目录
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md] — 右侧面板单视图 + 键盘快捷键 + CSS 隔离

## Dev Agent Record

### Agent Model Used

(to be filled by dev agent)

### Debug Log References

### Completion Notes List

### File List
