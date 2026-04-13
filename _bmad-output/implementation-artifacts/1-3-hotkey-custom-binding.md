---
doc_type: story
story_id: "1.3"
aliases: ["1.3"]
epic_id: "EPIC-1"
prd_id: "PRD14"
status: ready-for-dev
priority: "P1"
estimate_hours: 4
depends_on: []
blocks: ["1.4"]
trace:
  decisions: []
  bugs: []
---
# Story 1.3: Hotkey 自定义绑定

## Story

As a 学习者,
I want 自定义所有 Skill（对话、考察、概念提取等）的 hotkey 绑定,
So that 我可以用自己习惯的快捷键快速启动各个功能。

## Acceptance Criteria

1. **Given** 学习者打开 Obsidian Settings → Hotkeys
   **When** 学习者搜索 Canvas Learning System 的 Skill 命令
   **Then** 所有已注册 Skill 都出现在列表中，可分配自定义快捷键
   **And** 每个命令的显示名称清晰描述对应功能（如 "Canvas Learning: 启动 AI 对话"）

2. **Given** 学习者为某 Skill 设置了快捷键
   **When** 学习者按下该快捷键
   **Then** 对应 Skill 立即启动
   **And** 无论当前焦点在哪个面板，快捷键均可响应

## Tasks / Subtasks

- [ ] Task 1: 定义 Skill 命令清单 (AC: #1)
  - [ ] 1.1 确定需注册的全部 Skill 命令列表（参见 Dev Notes §Skill 列表）
  - [ ] 1.2 为每个 Skill 分配唯一 command ID（格式：`canvas-learning:<skill-kebab-name>`）
  - [ ] 1.3 确定每个命令的 `name` 字段（中文显示名称，供 Hotkeys 搜索面板展示）

- [ ] Task 2: 在插件中注册命令 (AC: #1, #2)
  - [ ] 2.1 在 `main.ts` 的 `onload()` 中使用 `this.addCommand()` 注册所有 Skill 命令
  - [ ] 2.2 每个命令的 `callback` 仅触发对应 Skill 的启动逻辑（调用现有或占位的 Skill 入口函数）
  - [ ] 2.3 不在命令注册阶段设置默认 hotkey（hotkey 由用户在 Settings → Hotkeys 自行分配）
  - [ ] 2.4 验证注册后命令在 Settings → Hotkeys 中可搜索到

- [ ] Task 3: 验证快捷键可响应 (AC: #2)
  - [ ] 3.1 在 Obsidian Settings → Hotkeys 中为其中一个命令（如 "启动 AI 对话"）分配测试快捷键
  - [ ] 3.2 按下该快捷键，确认 Skill 启动（或触发对应 Notice 提示，若 Skill 本体尚未实现）
  - [ ] 3.3 切换至不同 pane（编辑器、文件树、图谱视图），验证快捷键仍可响应

- [ ] Task 4: 编写测试 (AC: #1, #2)
  - [ ] 4.1 单元测试：验证 `onload()` 调用后 `addCommand` 被调用的次数等于 Skill 数量
  - [ ] 4.2 单元测试：验证每个命令的 `id` 符合 `canvas-learning:*` 格式且唯一
  - [ ] 4.3 单元测试：验证每个命令的 `name` 字段非空

## Dev Notes

### Skill 命令列表（Story 1.3 注册范围）

以下 Skill 对应 PRD 中已明确的用户触发入口，在本 Story 中全部通过 `this.addCommand()` 注册：

| Command ID | 显示名称（name） | 对应 FR |
|---|---|---|
| `canvas-learning:start-dialog` | Canvas Learning: 启动 AI 对话 | FR1 |
| `canvas-learning:start-examination` | Canvas Learning: 启动检验白板 | FR6 |
| `canvas-learning:extract-concept` | Canvas Learning: 提取新概念 | FR15 |
| `canvas-learning:quiz-from-callout` | Canvas Learning: 从批注快速考察 | FR13 |
| `canvas-learning:open-dashboard` | Canvas Learning: 打开学习 Dashboard | FR28 |
| `canvas-learning:open-review-queue` | Canvas Learning: 打开复习队列 | FR36 |

> **注意**：本 Story 只负责命令注册（`addCommand`）。各 Skill 的完整实现在对应 Epic Story 中完成。本 Story 的 `callback` 可调用占位函数（输出 Notice），但不得为空函数（违反 DD-03）。

### Obsidian `addCommand()` API 规范

参考 Obsidian API（[官方文档](https://docs.obsidian.md/Reference/TypeScript+API/Plugin/addCommand)）：

```typescript
this.addCommand({
  id: 'canvas-learning:start-dialog',
  name: 'Canvas Learning: 启动 AI 对话',
  callback: () => {
    // 调用 Skill 启动函数，或在 Skill 未就绪时 new Notice(...)
    this.skillDispatcher.dispatch('start-dialog');
  },
});
```

- `id`：全局唯一，建议用 `<plugin-id>:<action>` 格式
- `name`：出现在 Settings → Hotkeys 搜索框中，必须包含插件名称前缀以便用户识别
- 不设置 `hotkeys` 字段 — hotkey 完全由用户自行在 Hotkeys 面板分配（符合 Obsidian 最佳实践）
- `editorCallback` 适用于需要编辑器上下文的命令；`callback` 适用于全局命令。本 Story 所有 Skill 均用 `callback`

### 项目结构注记

- 命令注册代码位置：`_archive/obsidian-canvas-learning/src/main.ts` 的 `onload()` 方法
- Skill 调度入口（本 Story 实现占位）：可在 `main.ts` 内定义 `dispatchSkill(skillId: string)` 私有方法
- 后续 Skill Story 实现时直接替换对应 `dispatchSkill` 分支，无需改动命令注册层

### NFR 关联

- NFR-REL-2：14 MCP 工具全部可调用 — 命令注册是 MCP 工具可达性的前置条件
- NFR-INT-1：frontmatter 不可因 Skill 异常损坏 — `callback` 须捕获异常，确保注册层不抛出未处理错误

## References

- [Source: _archive/obsidian-canvas-learning/src/main.ts] — 插件主入口，命令注册位置
- [Source: _bmad-output/planning-artifacts/epics.md#Story-1.3] — AC 和 FR 映射原始来源
- [Source: _bmad-output/planning-artifacts/epics.md#Story-1.4] — blocks 关系：1.4 冲突检测依赖 1.3 注册完成
- [Obsidian API: Plugin.addCommand()] — https://docs.obsidian.md/Reference/TypeScript+API/Plugin/addCommand

## UAT Script

> Non-technical user validation: no code terminology, only describe what to click and what to see.

1. **验证命令出现在 Hotkeys 搜索列表** (AC: #1)
   - 打开 Obsidian
   - 点击左下角齿轮图标，进入 Settings
   - 在左侧菜单中找到 "Hotkeys"，点击进入
   - 在搜索框中输入 "Canvas Learning"
   - 应该看到至少以下 6 条命令出现在列表中：
     - "Canvas Learning: 启动 AI 对话"
     - "Canvas Learning: 启动检验白板"
     - "Canvas Learning: 提取新概念"
     - "Canvas Learning: 从批注快速考察"
     - "Canvas Learning: 打开学习 Dashboard"
     - "Canvas Learning: 打开复习队列"
   - 如果搜索结果为空，或命令数量少于 6 条，记录 Story 1.3 和实际看到的条目数

2. **验证快捷键可绑定并触发** (AC: #2)
   - 在 Hotkeys 列表中找到 "Canvas Learning: 启动 AI 对话"
   - 点击右侧 "+" 按钮，按下你想用的快捷键（如 Ctrl/Cmd + Shift + D）
   - 关闭 Settings，回到任意笔记编辑界面
   - 按下刚才设置的快捷键
   - 应该看到 AI 对话面板打开，或屏幕右上角出现提示信息
   - 如果没有任何反应，记录 Story 1.3 和你按下的快捷键

3. **验证快捷键在不同区域均可响应** (AC: #2)
   - 分别在以下位置按下上一步设置的快捷键：
     - 正在编辑笔记内容时
     - 点击左侧文件树面板后
     - 点击右侧侧边栏面板后
   - 每次都应该看到相同的响应（面板打开或提示信息）
   - 如果某个区域无响应，记录 Story 1.3 和失败的区域名称

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-1.3.1 | vitest | `npm run test -- --testPathPattern=commands` | 0 failed |
| CP-1.3.2 | vitest | `npm run test -- --testPathPattern=command-ids` | 0 failed (all IDs unique and match `canvas-learning:*`) |
| CP-1.3.3 | manual | Settings → Hotkeys → search "Canvas Learning" | 6 commands visible |

## User Feedback & Changes

### Feedback Log

<!-- Users write BMAD-ANNO callouts below. Claude scans and dispatches by intent. -->

### Deviation Notes

<!-- Claude auto-fills: summary of historically processed feedback -->

## Dev Agent Record

### Agent Model Used

(to be filled by Dev agent)

### Debug Log References

### Completion Notes List

### File List

## Relations

- EPIC: [[EPIC-1]]
- PRD: [[PRD14]]
- Blocks: [[1.4]]
