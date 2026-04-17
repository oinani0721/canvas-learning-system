---
story_id: "1.5"
epic_id: "1"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P2"
estimate_hours: 4
depends_on: ["1.4"]
blocks: []
trace:
  - "FR-SYS-04"
---

# Story 1.5: Hotkey 冲突检测

Status: ready-for-dev

## Story

As a 学习者,
I want 启动时自动检测快捷键冲突,
So that 我不会因冲突而无法触发 Skill 命令。

## 通俗化解释（给学习者）

> **一句话说**: 每次启动 Obsidian，系统帮你给快捷键"体检"一遍，发现打架就提醒你。

**你会遇到的场景**:
- 你把"启动学习对话"绑到 ⌘+Option+C，过几天又把"提取概念"也绑到同一组键，自己完全没察觉
- 某天按快捷键突然没反应，你纳闷到底是谁抢了这个键位 🤔

**这个功能帮你**:
- 启动时一眼看到冲突，不用等踩坑才发现
- 系统只提醒、不乱动你的绑定，改不改、怎么改由你决定

**用个比喻**: 就像小区物业发现两辆车都想停同一个车位 🅿️ — 不会偷偷把哪辆拖走，而是贴张公告"这俩位置冲突，你俩自己协商"，最终钥匙还在你手里。

**你能看到/操作到什么**:
- Obsidian 启动后，右下角弹出一条通知（持续约 8 秒），写明"⌘+Option+C 同时绑定到「启动学习对话」和「提取概念」，请到 Hotkeys 设置里改一下"
- 通知消失后你可以自己打开 Settings → Hotkeys 调整，只改本应用的 6 个命令，不会因为你装了别的插件就瞎报警 ✅

## Acceptance Criteria

1. **Given** 两个 Canvas 插件命令绑定了相同的快捷键
   **When** Obsidian 启动并加载插件
   **Then** 显示警告通知，列出冲突的命令名称和共享的快捷键
   **And** 通知持续 8 秒后自动消失
   **And** 通知文案示例：`Canvas 快捷键冲突: Cmd+Option+C 同时绑定了 "启动学习对话" 和 "提取概念"`

2. **Given** 所有 Canvas 插件命令的快捷键无冲突
   **When** Obsidian 启动
   **Then** 不显示任何冲突通知（静默通过）

3. **Given** 其他第三方插件使用了与 Canvas 命令相同的快捷键
   **When** 检测冲突
   **Then** 只检查 Canvas 插件自身的 6 个命令之间是否冲突
   **And** 不对其他插件的快捷键产生误报

4. **Given** 快捷键使用不同修饰符顺序（如 Cmd+Shift+C vs Shift+Cmd+C）
   **When** 检测冲突
   **Then** 正确识别为同一快捷键（修饰符归一化比较）

5. **Given** Canvas 插件命令未绑定任何快捷键
   **When** 检测冲突
   **Then** 不报冲突（未绑定的命令不参与比较）

## Tasks / Subtasks

- [ ] Task 1: 冲突检测核心逻辑 (AC: #1, #2, #3, #4, #5)
  - [ ] 1.1: 在 Claudian 插件中新增 `checkHotkeyConflicts()` 方法
  - [ ] 1.2: 通过 `this.app.hotkeyManager.getHotkeys(commandId)` 或遍历 `this.app.hotkeyManager.customKeys` 获取本插件 6 个命令的当前绑定
  - [ ] 1.3: 实现修饰符归一化：将 `modifiers` 数组排序后拼接为 canonical 字符串（如 `["Shift","Mod"]` -> `"Mod+Shift"`），确保顺序不同但等价的快捷键被识别
  - [ ] 1.4: 构建 `Map<canonicalKey, commandId[]>`，找到 value.length > 1 的条目即为冲突
  - [ ] 1.5: 只检查以 `canvas:` 前缀开头的命令 ID（排除其他插件命令）

- [ ] Task 2: 通知展示 (AC: #1, #2)
  - [ ] 2.1: 有冲突时使用 `new Notice(conflictMessage, 8000)` 显示 8 秒通知
  - [ ] 2.2: 通知消息格式：`Canvas 快捷键冲突:\n{key1} 同时绑定了 "{name1}" 和 "{name2}"\n...`
  - [ ] 2.3: 多组冲突合并为一条通知
  - [ ] 2.4: 无冲突时不调用 Notice（静默通过）

- [ ] Task 3: 启动时机集成 (AC: #1, #2)
  - [ ] 3.1: 在插件 `onload()` 中，命令注册完成后调用 `checkHotkeyConflicts()`
  - [ ] 3.2: 使用 `this.app.workspace.onLayoutReady(() => ...)` 确保 hotkeyManager 已加载完毕后再检测
  - [ ] 3.3: 检测异常不影响插件正常加载（try-catch 包裹，console.error 记录）

- [ ] Task 4: 测试 (AC: #1, #2, #3, #4, #5)
  - [ ] 4.1: 单元测试 `checkHotkeyConflicts` 的纯逻辑部分（修饰符归一化、冲突检测算法）
  - [ ] 4.2: 测试用例：无绑定（无冲突）、有冲突、修饰符顺序不同但等价、仅 canvas: 前缀命令参与

## Dev Notes

- **Obsidian hotkeyManager API**: `this.app.hotkeyManager` 是内部 API（非官方文档），但社区广泛使用。`customKeys` 是 `Record<string, Hotkey[]>`，`defaultKeys` 是默认值
- **Hotkey 结构**: `{ modifiers: string[], key: string }` — modifiers 可能是 `["Mod"]`（Cmd on Mac），`["Shift"]`，`["Alt"]` 等
- **Mod 归一化**: Obsidian 用 `"Mod"` 表示 Cmd(Mac)/Ctrl(Win)，不需要平台特殊处理
- **只检查自身命令**: FR-SYS-04 明确要求只检查本插件命令的冲突，不涉及其他插件。这避免了误报和不必要的干扰
- **不自动修复**: PRD 要求只警告不修复，用户自行在 Settings > Hotkeys 解决冲突
- **onLayoutReady**: 确保 Obsidian 的 workspace 和各 manager 完全初始化后再执行检测，否则可能读到不完整的 hotkey 数据

### Project Structure Notes

- 修改文件：Claudian 插件主文件（`onload()` 中调用 `checkHotkeyConflicts()`）
- 新增逻辑：`checkHotkeyConflicts()` 方法 + 修饰符归一化工具函数
- 测试文件：插件内单元测试（冲突检测算法）

### References

- [Source: _bmad-output/planning-artifacts/prd.md#FR-SYS-04] — 启动时检测 hotkey 冲突并警告
- [Source: _bmad-output/planning-artifacts/epics.md#Story-1.5] — AC 原文（冲突检测 + 8 秒通知 + 只检查本插件 + 归一化）
- [Source: Story 1.4] — 依赖 1.4 的命令注册（6 个 `canvas:*` 命令 ID）

## UAT Script

> 非技术用户验收脚本

1. **验证冲突检测** (AC: #1)
   - 打开 Obsidian Settings > Hotkeys
   - 将两个 Canvas 命令绑定到相同的快捷键（如都绑到 Cmd+Shift+C）
   - 关闭并重新打开 Obsidian
   - 应该看到一条黄色通知，告诉你哪两个命令有冲突
   - 通知约 8 秒后自动消失

2. **验证无冲突静默** (AC: #2)
   - 确保所有 Canvas 命令的快捷键各不相同（或都未绑定）
   - 重新打开 Obsidian
   - 不应看到任何冲突通知

3. **验证不误报其他插件** (AC: #3)
   - 将某个 Canvas 命令和某个其他插件命令绑定到相同的快捷键
   - 重新打开 Obsidian
   - 不应看到冲突通知（因为只检查 Canvas 插件自身的命令）

4. **验证修饰符顺序不影响检测** (AC: #4)
   - 如果两个命令绑定了相同按键但修饰符顺序不同（如 Shift+Cmd+C 和 Cmd+Shift+C），系统应正确识别为同一快捷键并报冲突

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-1.5.1 | vitest | `cd frontend && npx vitest run --reporter=verbose tests/hotkey-conflict.test.ts` | 0 failed |

## User Feedback & Changes

### Feedback Log
<!-- Users write BMAD-ANNO callouts below -->

### Deviation Notes
<!-- Auto-filled -->

## Dev Agent Record

### Agent Model Used
(to be filled by Dev agent)

### Debug Log References

### Completion Notes List

### File List
