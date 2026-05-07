---
story_id: "10.8"
epic_id: "10"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P1"
estimate_hours: 6
depends_on: ["10.7"]
blocks: ["10.9"]
trace: ["FR-DEEP-08", "M5", "M7", "UX-1", "UX-4"]
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
day: "Day 9"
target_date: "2026-05-15"
fixes_gap: "Agent 2.3 发现的 UserNote 仅展示限制"
uat_sheet: "_bmad-output/验收单/Story-10.8-day9-user-note-edit.md"
---

# Story 10.8: Day 9 UserNote 现场编辑

**Status**: ready-for-dev (target Day 9, 2026-05-15)

## Story（用户故事）

As a 学习者, I want to add my own annotations to whiteboard nodes and book pages in real-time so that I own my learning experience and can capture insights as they happen — like Obsidian's `Cmd+Shift+A` annotation flow inside DeepTutor.

> **映射对**: M5（14 块 + user_note → 原白板拆解 + 批注）+ M7（批注/标记理解程度）+ UX-1（批注是核心操作单位）+ UX-4（Graphiti 同步）

## 通俗化解释（给学习者）

> **一句话说**: 在 DeepTutor 阅读 book 或看 whiteboard 时，能现场写自己的笔记（不用切到 Obsidian），写完自动保存。

**你会遇到的场景**:
- 在 whiteboard 看节点详情时，想记一句"这个跟昨天学的 X 类似"
- 期望旁边有"+ 添加笔记"按钮
- 点开 → textarea 出现 → 输入 → blur 自动保存
- 下次再来还在

**这个功能帮你**:
- 思考的瞬间能记录（不用打断流程切应用）
- 笔记和节点绑定（不丢失上下文）
- 同步回 Canvas vault（你的笔记永远是 md 真相源）

**用个比喻**: ✏️ 就像在书边写铅笔字——不用关闭书拿出本子另写，写完合上书还在。

## Acceptance Criteria

### AC #1: UserNoteBlock contentEditable

- **Given** fork `UserNoteBlock.tsx` 当前仅 `<MarkdownRenderer content={body} />` 只读
- **When** 加 `<textarea contentEditable>` 编辑模式 + 切换按钮
- **Then** 用户点 "Edit" → textarea 替换 markdown 渲染
- **And** 输入流畅（无 lag）
- **And** 点"Save"或 blur → 切回渲染模式 + 保存

### AC #2: 持久化 API

- **Given** 用户编辑笔记
- **When** blur 触发 saveNote
- **Then** POST `/api/v1/notes/:note_id/user-annotation` 含 `{content, timestamp}`
- **And** 后端代理到 Canvas vault md 文件（直接写入 Obsidian 笔记）
- **And** debounce 500ms 避免 API spam

### AC #3: 离线 + 同步

- **Given** 网络断开时
- **When** 用户编辑笔记
- **Then** localStorage key `user_note_{note_id}` 存草稿
- **And** 网络恢复时自动同步（5s 内重试）
- **And** 冲突解决：服务端版本 wins（或显示 dialog 让用户选）

### AC #4: Whiteboard 节点点击 → 加笔记

- **Given** Story 10.5 Whiteboard 已实装
- **When** 用户点击某节点 → ChatPanel 打开
- **Then** ChatPanel 含"添加笔记"按钮
- **And** 点击 → 编辑器出现 → 写完保存
- **And** 笔记关联到节点（不是 page level）

## Tasks / Subtasks

### Frontend

- [ ] Task 1: UserNoteBlock 编辑模式 (AC: #1)
  - [ ] 1.1: Edit `web/app/(workspace)/book/components/blocks/UserNoteBlock.tsx`
  - [ ] 1.2: 加 state `[isEditing, setIsEditing]`
  - [ ] 1.3: isEditing=true → `<textarea>`，false → `<MarkdownRenderer>`
  - [ ] 1.4: blur 或 Cmd+S → handleSave + setIsEditing(false)

- [ ] Task 2: useUserNote hook (AC: #2)
  - [ ] 2.1: 新建 `web/hooks/useUserNote.ts`
  - [ ] 2.2: state `{content, isSaving, error}`
  - [ ] 2.3: method `saveNote(note_id, content)` POST 到后端
  - [ ] 2.4: debounce 500ms

- [ ] Task 3: localStorage 离线 (AC: #3)
  - [ ] 3.1: hook 加 `restoreFromCache(note_id)`
  - [ ] 3.2: 每次 blur 同时写 localStorage
  - [ ] 3.3: 成功 sync 后清除 localStorage 项

- [ ] Task 4: Whiteboard NodeDetailPanel 加 UserNote (AC: #4)
  - [ ] 4.1: Edit Story 10.5 的 NodeDetailPanel 组件
  - [ ] 4.2: 加 "Add Note" 按钮 → 弹 UserNoteBlock 编辑器
  - [ ] 4.3: 笔记 link 到 node_id (不是 page_id)

### Backend

- [ ] Task 5: user_note router (AC: #2)
  - [ ] 5.1: 新建 `deeptutor/api/routers/user_note.py`
  - [ ] 5.2: route `POST /api/v1/notes/:note_id/user-annotation`
  - [ ] 5.3: 代理到 Canvas (vault md 文件直接 append/edit)

- [ ] Task 6: Canvas vault 写入 (AC: #2, UX-4)
  - [ ] 6.1: CanvasClient 加 `update_note(note_path, annotation)` 方法
  - [ ] 6.2: Canvas backend `/api/v1/notes/:path/annotation` 直接写 md 文件
  - [ ] 6.3: Graphiti episodic memory 同步记录该 annotation 事件 (UX-4)

### Test

- [ ] Task 7: Hook 单元测试
  - [ ] 7.1: 测 debounce 行为（不连续 POST）
  - [ ] 7.2: 测 localStorage 离线 + 网络恢复同步

- [ ] Task 8: E2E (AC: #1-4)
  - [ ] 8.1: 在 whiteboard 节点写笔记 → blur → 保存
  - [ ] 8.2: 关闭浏览器 + 重开 → 笔记还在
  - [ ] 8.3: vault md 文件检查 → 看到 annotation 已写入
  - [ ] 8.4: Graphiti search → 查到 annotation event

## Dev Notes

### 修复 Agent 2.3 发现的瓶颈
- DeepTutor 原 UserNoteBlock **仅展示无编辑**（contentEditable 缺失）
- Story 10.8 修复让 user 能在 book 阅读流中现场添加笔记
- 没有这个能力的"白板"是矛盾设计（白板核心 = 用户写笔记 + 标关系）

### UX-1 + UX-4 落地
- UX-1（批注是核心）：UserNote 现在是一等公民交互，不是被动展示
- UX-4（Graphiti 同步）：每次 annotation 写入 Graphiti episodic memory（事件时间线）

### Markdown 预览（可选 P1）
- 简单版：纯文本保存 + 渲染时再 MarkdownRenderer 解析
- 高级版：split-view 编辑/预览（DeepTutor Co-Writer 已有此模式可借鉴）
- Day 9 默认简单版（时间紧）

### debounce 500ms
- 连续输入不会触发多次 POST（避免 spam）
- 但 blur 立即触发（用户切走时保存）

## UAT 验收

详见 `_bmad-output/验收单/Story-10.8-day9-user-note-edit.md`

## References

- Deep Explore §2.3 14 BlockType 渲染（UserNote 不可编辑限制）
- Deep Explore §1.2 notebook + memory（覆盖式无版本，Graphiti 补全）
- Round-22 §五 可接受 Hack（Day 9 之前 user_note 简单版）

## 下一步

→ Story 10.9 Day 10 UAT 收官 + go/no-go 决策
