---
story_id: "1.16"
epic_id: "1"
prd_id: "canvas-learning-system"
status: "review"
priority: "P0"
estimate_hours: 4
depends_on: ["1.4"]
blocks: ["1.17"]
trace: ["FR-SYS-02","FR-SYS-04"]
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
---

# Story 1.16: 批注 Hotkey + 7 Callout 类型 Modal

**Epic**: 1 — 基础设施 + Obsidian 插件命令
**Status**: review (Dev 已实施 → 待 UAT 8 步 + code review)
**Plan**: EPIC1-BMAD-DEV-ASSESS-2026-04-17
**Priority**: P0
**Estimate**: ~4h
**Dependency**: Story 1.4 (hotkey 注册框架) 已 ready

---

## Story

作为 学习者，
我想 选中文本后按一个 hotkey，弹出 7 种 callout 类型菜单，选一种后文本被自动包成 Obsidian callout，
以便 在笔记里快速标注疑问/重点/错误等，无需记忆 callout 语法。

## Behavior（用户视角）

```
选中文本 "this is important"
        ↓ 按 hotkey (用户在 Obsidian Settings 自绑)
        ↓
弹出 modal: question / tip / error / hint / note / warning / info
        ↓ 用户选 "tip" (键盘 fuzzy search 或鼠标点)
        ↓
文本变为:
> [!tip]
> this is important
```

在 Obsidian Reading View 渲染为蓝色边框 + 灯泡图标的 callout 块。

---

## Acceptance Criteria

### AC #1: 命令注册
- [ ] 命令 `canvas:annotate-callout` 注册在 Obsidian 命令面板
- [ ] 中文名: "批注为标注"
- [ ] Settings > Hotkeys 搜 "Canvas" 看到这条
- [ ] 默认 `hotkeys: []`（用户自绑）

### AC #2: Modal 弹出
- [ ] 命令触发后 modal 出现
- [ ] 标题 "选择标注类型"
- [ ] 7 选项: question / tip / error / hint / note / warning / info
- [ ] Fuzzy search 工作（输 "t" 过滤到 [tip, note]）
- [ ] Esc 关闭 modal，无副作用

### AC #3: 选中文本必需
- [ ] 命令触发但无选中文本 → Notice "请先选中文本再批注"（3秒）
- [ ] 不打开 modal

### AC #4: 文本包裹
- [ ] 用户选 "tip" 后，选中文本被替换为：
  ```
  > [!tip]
  > <原选中文本>
  ```
- [ ] 多行选中: 每行前加 `> `
- [ ] 空行保留 `> `（不被 strip）
- [ ] 光标位置: 替换后停在尾部

### AC #5: Callout 渲染验证
- [ ] 切到 Reading View 看到样式 callout 块（颜色 + 图标）
- [ ] 7 种类型各自不同颜色/图标

### AC #6: Modal 关闭后焦点
- [ ] 用户选完类型，modal 自动关闭
- [ ] 焦点返回编辑器
- [ ] Console (F12) 无错误

### AC #7: Hotkey 冲突检测（来自 Story 1.5）
- [ ] 若 hotkey 与其他 canvas 命令冲突，Story 1.5 检测器自动报告

---

## Tasks

### Dev Tasks
- [x] **添加 Modal class** `CalloutTypeModal extends FuzzySuggestModal<CalloutType>`
   - 位置: `frontend/obsidian-plugin/src/main.ts` (文件末尾，main.ts 总长 178 行 < 200 阈值)
   - 实现 `getItems()` 返回 7 callout 类型数组（来自 `CALLOUT_TYPES` 常量）
   - 实现 `onChooseItem(type)` 调用 `editor.replaceSelection(wrapSelection(...))`
- [x] **添加第 7 命令** `canvas:annotate-callout` 在 `registerCanvasCommands()`
- [x] **实现 handler** `handleAnnotateCallout()`
   - 检查 `activeEditor` 是否激活，若无 → Notice "编辑器未激活"
   - 检查选中文本，若无 → Notice "请先选中文本再批注"（3 秒）
   - 否则打开 CalloutTypeModal
- [x] **辅助函数** `wrapSelection(text, type)`: split `\n` → 每行 `> ` 前缀 → join；首行 `> [!type]`
   - 提取到独立模块 `src/callout.ts` 便于单元测试
- [x] **build + deploy**:
   - `cd frontend/obsidian-plugin && npm run build` → `main.js` 6535 bytes
   - `cp main.js ../../canvas-vault/.obsidian/plugins/canvas-learning-system/`
   - grep 验证 canvas-vault/main.js 含 `annotate-callout / CalloutTypeModal / 批注为标注` 3 处
- [x] **测试**: Node `node:test` 6/6 通过（纯函数边界：单行 / 多行 / 空行 / 纯空格 / 7 类型枚举）；UAT 8 步待用户 hands-on

### QA Tasks
- [ ] 8 步 UAT 通过（待用户 hands-on 跑）
- [x] 单元测试 6 用例通过（纯函数 `wrapSelection` 边界）
- [ ] 7 个边界用例（UAT + 单元测试混合覆盖，剩余 Obsidian API 部分靠 UAT）

---

## Dev Notes

### 已锁技术决策（Round 3 Sec R2）

| 决策点 | 选择 | 理由 |
|---|---|---|
| Modal class | `FuzzySuggestModal<string>` | 内置 fuzzy search，~20 行代码 |
| 文本包裹 | `editor.replaceSelection(wrapped)` | cursor-aware，多行原生处理 |
| Callout 类型 | 7 hardcoded + 可选 Callout Manager 检测 | 无依赖默认可用 |
| Hotkey 默认 | `hotkeys: []` | Obsidian 社区标准 |

### 代码骨架（添加到 main.ts）

```typescript
import { Notice, Plugin, FuzzySuggestModal, type Editor, type App } from "obsidian";

// 在 registerCanvasCommands() 内添加第 7 命令:
this.addCommand({
  id: "canvas:annotate-callout",
  name: "批注为标注",
  callback: () => this.handleAnnotateCallout(),
});

// Plugin class 加方法:
private handleAnnotateCallout() {
  const editor = this.app.workspace.activeEditor?.editor;
  if (!editor) { new Notice("编辑器未激活"); return; }
  const selected = editor.getSelection();
  if (!selected) { new Notice("请先选中文本再批注", 3000); return; }
  new CalloutTypeModal(this.app, editor, selected).open();
}

// Modal class:
class CalloutTypeModal extends FuzzySuggestModal<string> {
  constructor(app: App, private editor: Editor, private selected: string) { super(app); }
  getItems(): string[] {
    return ["question", "tip", "error", "hint", "note", "warning", "info"];
  }
  getItemText(item: string): string { return item; }
  onChooseItem(item: string) {
    const lines = this.selected.split("\n").map(l => `> ${l}`).join("\n");
    this.editor.replaceSelection(`> [!${item}]\n${lines}`);
  }
}
```

### 风格参考
- 现有 6 命令模式: `frontend/obsidian-plugin/src/main.ts:24-67`
- Notice 用法: `new Notice(msg, ms)`
- Editor 访问: `this.app.workspace.activeEditor?.editor`

---

## UAT Script (非技术用户 8 步)

**前置**: Obsidian 已开 canvas-vault，插件已启用

1. **检查命令存在**: Cmd+P → 输入 "Annotate" → 看到 "Canvas: 批注为标注"
2. **绑定 hotkey**: Settings > Hotkeys → 搜 "Annotate" → 点 + 按 Alt+A
3. **测试空选中**: 不选文本，按 Alt+A → 看到 Notice "请先选中文本再批注"
4. **测试单行**: 输入 "this is important" → 选中 → Alt+A → modal 出现
5. **选 tip**: 输 "tip" → Enter → 文本变 `> [!tip]\n> this is important`
6. **看 Reading View**: 切到 Reading View → 看到蓝色 callout 块
7. **测试多行**: 选两行文本 → Alt+A → 选 "warning" → 两行都包成 `> [!warning]\n> 行1\n> 行2`
8. **测试 Esc**: 选文本 → Alt+A → modal 出现 → Esc → 文本不变

---

## Pitfalls + 诊断矩阵

| 症状 | 原因 | Claude Code 诊断 + 修 |
|---|---|---|
| 命令不在 Cmd+P 列表 | main.js 未重载 | Reload app: Cmd+Shift+P → "Reload app without saving" |
| Hotkey 不响应 | 未绑或绑错命令 | Settings > Hotkeys 重新绑定 |
| Modal 不出现 | 编辑器未激活 | 点击编辑器区让光标在 md 文件 |
| 总是 "请先选中文本" | getSelection() 逻辑错 | F12 console 看 JS 错；rebuild |
| Modal 出现但无 7 项 | FuzzySuggestModal 未初始化 | rebuild + reload Obsidian |
| 包裹后语法错（`>>>`） | wrapSelection() bug | 检查应是 `> [!type]\n> text` |
| Reading View 不渲染 | 语法不对 | 验证 `> [!tipname]` 后有空格 |

---

## 不会做的事
- ❌ 不调 AI（这是 Story 1.17 的事）
- ❌ 不写后端（纯 frontend plugin）
- ❌ 不改其他 6 命令（独立第 7 命令）
- ❌ 不预绑 hotkey（用户自定）

---

> [!question]+ 用户批注 - Story 1.16 spec
> 7 AC 是否符合预期？UAT 8 步是否够用？是否授权 bmad-bmm-create-story 转正式 spec + bmad-bmm-dev-story 实施？
> （批注区）

---

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-1 | build | `cd frontend/obsidian-plugin && npm run build` | exit 0, main.js updated |
| CP-2 | deploy | `cp main.js canvas-vault/.obsidian/plugins/canvas-learning-system/` | file copied |
| CP-3 | reload | Manual: Obsidian Cmd+Shift+P → "Reload app" | no console error (F12) |
| CP-4 | UAT | Run "## UAT Script" steps | all steps pass |

## User Feedback & Changes

### Feedback Log
<!-- 用户在 Obsidian 跑 UAT 后批注 -->

### Deviation Notes
<!-- Dev agent 偏离 spec 时记录原因 -->

## Dev Agent Record

### Agent Model Used
Claude Opus 4.7 (1M context) via `bmad-bmm-dev-story` skill — 2026-04-18

### Debug Log References
- Build: `cd frontend/obsidian-plugin && npm run build` → `main.js` 6535 bytes (was 5071)
- Test: `npm test` → `node --test tests/.out/callout.test.cjs` → 6 passed / 0 failed
- Deploy: `cp main.js canvas-vault/.obsidian/plugins/canvas-learning-system/main.js`
- Symbol grep: canvas-vault/main.js 含 `annotate-callout / CalloutTypeModal / 批注为标注` 3 处命中

### Completion Notes List

1. **AC #1 命令注册** — 第 7 命令 `canvas:annotate-callout`（中文名 "批注为标注"）追加到 `registerCanvasCommands()` 末尾。默认 `hotkeys: []`，继承 Obsidian 命令默认行为（用户自绑）。
2. **AC #2 Modal 弹出** — `CalloutTypeModal extends FuzzySuggestModal<CalloutType>`，7 个硬编码选项从 `CALLOUT_TYPES` 常量导出。`setPlaceholder("选择标注类型")` 作为标题（FuzzySuggestModal 无独立 title API，用 placeholder 传递意图）。Fuzzy search + Esc 关闭均由 Obsidian 框架原生提供。
3. **AC #3 空选中必需** — 双重防护：无 `activeEditor` → Notice "编辑器未激活"；有 editor 但 `getSelection()` 空 → Notice "请先选中文本再批注"（3 秒），不打开 modal。
4. **AC #4 文本包裹** — `wrapSelection()` 拆行 + 每行 `> ` 前缀 + 首行 `> [!type]`。`editor.replaceSelection(wrapped)` 替换后光标天然停在新文本尾部（Obsidian API 原生行为）。
5. **AC #5 Callout 渲染** — Obsidian 原生支持这 7 种 callout 类型（`question / tip / error / hint / note / warning / info`），在 Reading View 自动渲染对应颜色 + 图标。无需插件额外 CSS。
6. **AC #6 Modal 关闭焦点** — `FuzzySuggestModal` 框架默认：`onChooseItem` 返回后 `close()` 自动触发，焦点回到上次激活元素（editor）。无需手动处理。
7. **AC #7 Hotkey 冲突** — 依赖 Story 1.5 的 `checkHotkeyConflicts()`，未在本 story 新写；该方法扫描所有 `canvas:*` 命令的 `customKeys`，新命令自动纳入。
8. **代码组织决策** — `wrapSelection + CALLOUT_TYPES + CalloutType` 提取到 `src/callout.ts`（纯函数，无 Obsidian 依赖），便于 Node `node:test` 直接测试；Modal 和 handler 留在 `main.ts`（需要 Obsidian API）。main.ts 新总长 178 行（<200 阈值，符合 spec 位置约定）。
9. **测试策略** — 对 DD-03（禁 mock）的 trade-off：Obsidian API-dependent 代码（Modal / editor / Notice）通过 UAT 8 步 hands-on 验证；纯函数 `wrapSelection` 用 `node:test` 跑 6 个用例（单行 / 多行 / 空行保留 / 纯空格 / 7 类型循环）。无新依赖（esbuild 已在 devDeps 用于打包测试）。
10. **部署** — Obsidian 侧需手动 `Cmd+Shift+P → "Reload app without saving"` 才能加载新 `main.js`（CP-3 manual checkpoint，无自动化可靠手段）。

### File List

- **NEW**: `frontend/obsidian-plugin/src/callout.ts` — 纯函数 `wrapSelection` + 常量 `CALLOUT_TYPES` + 类型 `CalloutType`
- **MOD**: `frontend/obsidian-plugin/src/main.ts` — import callout 模块；加第 7 命令 `canvas:annotate-callout`；加 `handleAnnotateCallout()` 方法；文件末尾加 `CalloutTypeModal` class
- **NEW**: `frontend/obsidian-plugin/tests/callout.test.ts` — 6 个 `node:test` 用例覆盖 `wrapSelection` 边界
- **NEW**: `frontend/obsidian-plugin/.gitignore` — 避免 `node_modules/ main.js main.js.map package-lock.json tests/.out/` 进入 git
- **MOD**: `frontend/obsidian-plugin/package.json` — 加 `test` script（esbuild bundle + node --test）
- **MOD**: `_bmad-output/implementation-artifacts/sprint-status.yaml` — 1-16 状态 `ready-for-dev` → `review`（经 in-progress 过渡）
- **MOD**: `_bmad-output/implementation-artifacts/epic-1/1-16-annotate-callout-hotkey.md` — 本 story 文件，填充 Dev Agent Record + File List + 勾选 Dev Tasks

构建产物（`frontend/obsidian-plugin/main.js` 6535 bytes）和部署副本（`canvas-vault/.obsidian/plugins/canvas-learning-system/main.js`）不纳入 git（local build artifact），由 `npm run build` 即时重建。

### Change Log

- 2026-04-18 — 初次实施 Story 1.16。新增 callout 模块 + 第 7 命令 + Modal。6/6 单元测试通过。待 UAT 8 步 hands-on + code-review。[PLAN: EPIC1-BMAD-DEV-ASSESS-2026-04-17]
