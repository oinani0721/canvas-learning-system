---
doc_type: story
story_id: "1.4"
aliases: ["1.4"]
epic_id: "EPIC-1"
prd_id: "PRD14"
status: ready-for-dev
priority: "P2"
estimate_hours: 2
depends_on: ["1.3"]
blocks: []
trace:
  decisions: []
  bugs: []
---
# Story 1.4: Hotkey 冲突检测与警告

## Story

As a 系统,
I want 在启动时检测 hotkey 冲突并发出警告,
So that 学习者不会因快捷键冲突导致功能不可达。

## Acceptance Criteria

1. **Given** 系统插件加载（`onload()`）或 hotkey 配置发生变更
   **When** 两个或以上 Skill 命令绑定了相同的快捷键（modifiers + key 完全一致）
   **Then** 系统通过 `new Notice()` 弹出警告通知，列出所有冲突的 Skill 名称和对应快捷键
   **And** 通知持续时间不少于 8 秒，让学习者有足够时间阅读
   **And** 不强制修改任何绑定，只提醒

2. **Given** 系统插件加载
   **When** 所有 Skill 命令的快捷键均无冲突（或某 Skill 未绑定快捷键）
   **Then** 系统不弹出任何冲突通知（静默启动）

3. **Given** 冲突检测逻辑
   **When** 遍历 `app.hotkeyManager.hotkeyMap`
   **Then** 只对当前插件注册的命令（命令 ID 以插件 ID 为前缀）进行冲突对比
   **And** 不误报与其他插件或 Obsidian 内置命令的冲突

*FRs: FR41*

## Tasks / Subtasks

- [ ] Task 1: 实现冲突检测核心逻辑 (AC: #1, #2, #3)
  - [ ] 1.1 在插件 `src/` 目录创建 `HotkeyConflictDetector.ts`，导出 `detectHotkeyConflicts(app: App, pluginId: string): ConflictReport[]`
  - [ ] 1.2 遍历 `app.hotkeyManager.hotkeyMap`，收集属于当前插件的所有命令及其绑定快捷键
  - [ ] 1.3 按快捷键字符串（`modifiers.sort().join('+') + '+' + key`）做 Map 聚合，找出同一键值下命令数 ≥ 2 的情况
  - [ ] 1.4 返回 `ConflictReport[]`，每条包含：`hotkey: string`（可读格式）、`commands: string[]`（命令名称列表）

- [ ] Task 2: 在插件 `onload()` 中调用检测并弹出通知 (AC: #1, #2)
  - [ ] 2.1 在 `main.ts` 的 `onload()` 末尾调用 `detectHotkeyConflicts(this.app, this.manifest.id)`
  - [ ] 2.2 如果返回非空数组，调用 `new Notice(message, 8000)` 显示冲突摘要
  - [ ] 2.3 通知文本格式：首行 "⚠️ Canvas Learning System：检测到快捷键冲突"，后续每行列出 "· <快捷键> → <命令A> / <命令B>"
  - [ ] 2.4 如返回空数组，不弹通知（静默）

- [ ] Task 3: 编写单元测试 (AC: #1, #2, #3)
  - [ ] 3.1 在 `tests/` 目录创建 `HotkeyConflictDetector.test.ts`
  - [ ] 3.2 测试场景：两个命令绑定相同快捷键 → 返回 1 条 ConflictReport，名称和快捷键正确
  - [ ] 3.3 测试场景：所有命令快捷键各不相同 → 返回空数组
  - [ ] 3.4 测试场景：某命令未绑定快捷键 → 不计入冲突检测
  - [ ] 3.5 测试场景：其他插件命令与本插件命令共享相同快捷键 → 不误报（AC: #3）

## Dev Notes

- **Obsidian API 访问路径**：`app.hotkeyManager.hotkeyMap` 是一个 `Map<string, Hotkey[]>`，键为命令 ID，值为该命令当前绑定的快捷键数组。此 API 在 Obsidian 0.15+ 可用，无需额外导入。
- **插件命令 ID 前缀**：Obsidian 注册命令时自动添加 `<pluginId>:` 前缀（例如 `canvas-learning-system:canvas-decompose-node`）。过滤时用 `commandId.startsWith(pluginId + ':')` 即可。
- **快捷键规范化**：比较前需将 modifiers 排序（如 `['Shift', 'Mod']` 和 `['Mod', 'Shift']` 视为同一组合），再拼接为字符串做 Map key。
- **`new Notice()` 用法**：`new Notice(message: string | DocumentFragment, timeout?: number)`。超时单位为毫秒；不传则使用 Obsidian 默认（约 5 秒）。本 Story 要求 8000ms。
- **不强制修改**：Story AC 明确"只提醒不修改"，故不调用任何 `app.hotkeyManager.removeHotkeys()` 或类似写操作。
- **依赖 Story 1.3**：Story 1.3 已完成 Skill 命令注册，本 Story 在其基础上读取已注册命令的 hotkey 状态，不重复注册任何命令。

### Project Structure Notes

- 新增文件：`_archive/canvas-progress-tracker/obsidian-plugin/src/managers/HotkeyConflictDetector.ts`
- 新增测试：`_archive/canvas-progress-tracker/obsidian-plugin/tests/managers/HotkeyConflictDetector.test.ts`
- 修改文件：`_archive/canvas-progress-tracker/obsidian-plugin/main.ts`（在 `onload()` 末尾添加约 10 行调用）

### References

- [Source: _archive/canvas-progress-tracker/obsidian-plugin/src/managers/HotkeyManager.ts] — 已有命令注册模式和 `formatHotkey()` 工具函数（本 Story 可复用）
- [Source: _archive/canvas-progress-tracker/obsidian-plugin/tests/managers/HotkeyManager.test.ts] — 测试文件格式参考
- [Source: _bmad-output/planning-artifacts/epics.md#Story-1.4] — AC 和 FR 映射
- [Source: _bmad-output/planning-artifacts/prd.md#FR41] — 原始需求定义
- [Obsidian API: app.hotkeyManager.hotkeyMap] — 快捷键读取入口（`Map<commandId, Hotkey[]>`）
- [Obsidian API: new Notice(message, timeout)] — 通知弹出 API

## UAT Script

> Non-technical user validation: no code terminology, only describe what to click and what to see.

1. **验证冲突警告出现** (AC: #1)
   - 打开 Obsidian Settings → Hotkeys
   - 搜索 "Canvas" 找到两个不同的 Canvas Learning System 命令
   - 为这两个命令都设置**完全相同**的快捷键（比如都设为 Ctrl+Shift+X）
   - 关闭 Settings，然后关闭并重新打开 Obsidian（或在 Settings → Community Plugins 里禁用再启用 Canvas Learning System 插件）
   - 插件重新加载后，屏幕右上角应该出现一条黄色/橙色警告消息，内容包含"快捷键冲突"字样，以及两个命令的名称和那个快捷键
   - 消息应该在屏幕上停留至少 8 秒才消失
   - 如果没有看到这条警告消息，记录 Story 1.4 和实际看到的内容

2. **验证无冲突时无通知** (AC: #2)
   - 打开 Obsidian Settings → Hotkeys
   - 确保所有 Canvas Learning System 命令的快捷键各不相同（或某些命令没有设置快捷键）
   - 关闭 Settings，然后重新加载插件（禁用再启用）
   - 插件加载后，屏幕上**不应该**出现任何"快捷键冲突"相关的消息
   - 如果看到了冲突消息，记录 Story 1.4 和实际看到的内容

3. **验证只提醒不修改** (AC: #1 And 条款)
   - 按照步骤 1 触发冲突警告
   - 警告消息消失后，打开 Obsidian Settings → Hotkeys
   - 检查那两个命令的快捷键：它们应该仍然都绑定着相同的快捷键（系统没有自动清除任何绑定）
   - 如果发现某个命令的快捷键被自动修改或清除，记录 Story 1.4 和修改情况

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-1.4.1 | jest | `cd _archive/canvas-progress-tracker/obsidian-plugin && npx jest tests/managers/HotkeyConflictDetector.test.ts --no-coverage` | 0 failed, 5 passed |
| CP-1.4.2 | jest | `cd _archive/canvas-progress-tracker/obsidian-plugin && npx jest tests/managers/ --no-coverage` | 0 failed (regression guard) |
| CP-1.4.3 | tsc | `cd _archive/canvas-progress-tracker/obsidian-plugin && npx tsc --noEmit` | 0 errors |

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
- Depends on: [[1.3]]
