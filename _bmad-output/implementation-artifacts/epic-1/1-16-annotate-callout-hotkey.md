---
story_id: "1.16"
epic_id: "1"
prd_id: "canvas-learning-system"
status: "in-progress"
priority: "P0"
estimate_hours: 6
depends_on: ["1.4"]
blocks: ["1.17"]
trace: ["FR-SYS-02","FR-SYS-04","FR-CONV-05"]
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
revision: "v2-round3-qa-align-2026-04-18"
---

# Story 1.16: 批注 Hotkey + 4 Tag + 3 态理解度 Callout

**Epic**: 1 — 基础设施 + Obsidian 插件命令
**Status**: in-progress (v2 correct-course 对齐 Round 3 QA；v1 实施后 UAT 发现缺 3 态理解度 2026-04-18)
**Plan**: EPIC1-BMAD-DEV-ASSESS-2026-04-17
**Priority**: P0
**Estimate**: ~4h
**Dependency**: Story 1.4 (hotkey 注册框架) 已 ready

---

## Story

作为 学习者，
我想 选中文本后按一个 hotkey，先选 4 种语义 Tag（Tips / 错误 / 提问 / 关键点），再选 3 种理解程度（已懂 / 模糊 / 不懂），文本被自动包成 callout 且内置 3 选 1 checkbox，
以便 记录自己对该内容的分类归属和理解程度，并在后续复习/考察时由 AI 优先对"模糊 / 不懂"的内容出题。

> **来源对齐**：前端旧代码 `frontend/src/components/chat/InlineAnnotation.tsx:35-38, 58-69`（4 AnnotationTag + 3 UnderstandingLevel）+ PRD Persona `prd-tauri-original-2ae5897.md:399` + Round 3 QA `obsidian-qa-round3-claude-answers-2026-04-14.md:283-291`（callout 内置 3 选 1 checkbox）。

## Behavior（用户视角）

```
选中文本 "this is important"
        ↓ 按 hotkey (用户在 Obsidian Settings 自绑，默认无)
        ↓
【第 1/2 步】 Modal: 选 4 Tag
    💡 Tips / ❌ 错误 / ❓ 提问 / 📌 关键点
        ↓ 用户选 "💡 Tips"
        ↓
【第 2/2 步】 Modal: 选 3 理解度
    ✅ 已懂 / 🤔 模糊 / ❌ 不懂
        ↓ 用户选 "🤔 模糊"
        ↓
文本变为:
> [!tips]+ 💡 Tips
> - [ ] ✅ 已懂
> - [x] 🤔 模糊
> - [ ] ❌ 不懂
>
> this is important
```

在 Reading View 看到 callout 块 + 3 checkbox。用户可**事后点击 checkbox** 切换理解度（Obsidian 原生支持）。Dataview 可按 `[x] 模糊` / `[x] 不懂` 查薄弱节点。

---

## Acceptance Criteria

### AC #1: 命令注册
- [x] 命令 `canvas:annotate-callout` 注册在 Obsidian 命令面板（v1 已 done）
- [x] 中文名: "批注为标注"（v1 已 done）
- [x] Settings > Hotkeys 搜 "Canvas" 看到 7 条（v1 已 done）
- [x] 默认 `hotkeys: []`（用户自绑）

### AC #2: 第 1/2 步 Modal — 选 4 语义 Tag（v2 重做）
- [ ] 命令触发且选中文本存在后，第一个 modal 出现
- [ ] Placeholder 文本: "第 1/2 步：选标签类型"
- [ ] **4 选项**（按 `InlineAnnotation.tsx:58-63`）:
  - `💡 Tips`（tips）
  - `❌ 错误`（error）
  - `❓ 提问`（question）
  - `📌 关键点`（keypoint）
- [ ] Fuzzy search 工作（输 "关" 过滤到 "📌 关键点"）
- [ ] Esc 关闭 modal，无副作用，不进入第 2 步

### AC #3: 第 2/2 步 Modal — 选 3 理解度（v2 新增）
- [ ] 用户在第 1/2 步选完 Tag 后，~50ms 内第 2/2 步 modal 自动弹出
- [ ] Placeholder 含所选 Tag: "第 2/2 步：选理解度（Tag: 💡 Tips）"
- [ ] **3 选项**（按 `InlineAnnotation.tsx:65-69`）:
  - `✅ 已懂`（understood）
  - `🤔 模糊`（fuzzy）
  - `❌ 不懂`（not-understood）
- [ ] Esc 关闭 modal，无副作用，原文不变（**v2**: 第 1 步 Tag 也被丢弃，不写入）

### AC #4: 选中文本必需
- [x] 命令触发但无选中文本 → Notice "请先选中文本再批注"（3秒）（v1 已 done）
- [x] 不打开第 1 步 modal（v1 已 done）

### AC #5: 文本包裹（v2 新格式）
- [ ] 用户完成两步选择后，选中文本被替换为下述 **6 行 callout**：
  ```
  > [!{tag-value}]+ {tag-label}
  > - [ ] ✅ 已懂
  > - [x] 🤔 模糊        ← 仅用户所选行打 x
  > - [ ] ❌ 不懂
  >
  > <原选中文本>
  ```
- [ ] 多行选中: body 每行前加 `> `
- [ ] 空行保留 `> `（不 strip）
- [ ] 光标位置: 替换后停在 callout 末尾
- [ ] 12 种组合 (4 Tag × 3 Level) 语法均正确（单元测试覆盖）

### AC #6: Callout + Checkbox 渲染（v2）
- [ ] 切到 Reading View 看到 callout 块：
  - `[!error]` 和 `[!question]` 为 Obsidian 原生类型，显示彩色边框 + 图标
  - `[!tips]` 和 `[!keypoint]` 非原生，fallback 到灰色样式但 header 显示 emoji label
- [ ] 3 个 checkbox 可点击切换 `[x]` ↔ `[ ]`（Obsidian 原生行为）
- [ ] `[!xxx]+` 的 `+` 号让 callout 默认展开可见

### AC #7: Modal 焦点行为
- [ ] 第 2 步 modal 选完后自动关闭
- [ ] 焦点返回编辑器
- [ ] Console (F12) 无错误

### AC #8: Hotkey 冲突检测（来自 Story 1.5）
- [x] 若 hotkey 与其他 canvas 命令冲突，Story 1.5 检测器自动报告（v1 已验证）

---

## Tasks

### Dev Tasks — v2 correct-course (2026-04-18)

- [x] **重写 `src/callout.ts`**（替换 v1 CALLOUT_TYPES）
   - 导出 `TAG_OPTIONS`（4 个 {value, label, callout}，按 InlineAnnotation.tsx:58-63）
   - 导出 `UNDERSTANDING_OPTIONS`（3 个 {value, label}，按 InlineAnnotation.tsx:65-69）
   - 新 `wrapSelection(text, tag: TagOption, understanding: UnderstandingValue)` 生成 6 行 callout
- [x] **重写 `main.ts` Modal**（替换 v1 CalloutTypeModal）
   - `TagTypeModal extends FuzzySuggestModal<TagOption>` — 第 1/2 步，placeholder "第 1/2 步：选标签类型"
   - `UnderstandingModal extends FuzzySuggestModal<UnderstandingOption>` — 第 2/2 步，placeholder 含所选 Tag
   - 两步之间 `setTimeout(50ms)` 衔接（避免 Obsidian modal stack 闪烁）
- [x] **命令和 handler 保留**（v1 已实施部分）
   - 命令 ID `canvas:annotate-callout`、名称 "批注为标注" 不变
   - Handler 逻辑不变（检查 editor + 选中 + 打开 TagTypeModal）
- [x] **扩展测试**（`tests/callout.test.ts` v2）
   - 9 用例：TAG_OPTIONS / UNDERSTANDING_OPTIONS 结构 + wrapSelection 4 组合 + 4×3=12 穷举 + 空行保留 + 纯空格
- [x] **build + deploy**:
   - `npm run build` → `main.js` 7886 bytes (v1 6535)
   - `cp main.js canvas-vault/.obsidian/plugins/canvas-learning-system/`
   - grep 验证 canvas-vault/main.js 含 `TagTypeModal / UnderstandingModal / TAG_OPTIONS / UNDERSTANDING_OPTIONS / 已懂 / 模糊 / 不懂` 9 处
- [ ] **UAT v2**：用户 hotkey `Cmd+Shift+A`（已绑），跑 2 步 modal + 理解度选择，验证 6 行 callout + Reading View 渲染 + 可点 checkbox 切换

### QA Tasks

- [ ] UAT v2 通过（待用户 hands-on 跑，见下方新 UAT Script）
- [x] 单元测试 9 用例通过（`npm test` → 9/9 green，含 4×3=12 组合穷举）
- [ ] 边界：`[!tips]` 和 `[!keypoint]` 非原生，Reading View 渲染为 fallback 灰色 callout（已知限制，后续 Story 可配 Callout Manager 定义颜色）

---

## Dev Notes

### 已锁技术决策（v2 对齐 Round 3 QA 2026-04-14）

| 决策点 | 选择 | 理由 |
|---|---|---|
| Modal class | 2 个 `FuzzySuggestModal`（TagTypeModal + UnderstandingModal） | 内置 fuzzy search + 两步分离清晰 |
| 两步衔接 | `setTimeout(50ms)` 让第 1 步 modal 完全关闭再开第 2 步 | 避免 Obsidian modal stack 闪烁 |
| 文本包裹 | `editor.replaceSelection(wrapped)` | cursor-aware，多行原生处理 |
| Callout Tag | **4 语义 Tag** (tips/error/question/keypoint) | 对齐 `InlineAnnotation.tsx:58-63` + Round 3 QA Line 283 |
| 理解度 3 态 | **内置 3 选 1 checkbox**（已懂/模糊/不懂） | 对齐 `InlineAnnotation.tsx:65-69` + Round 3 QA Line 284；用户可点击切换 |
| Markdown 格式 | `[!tag]+` 展开 + 3 checkbox + 空 `>` 分隔 + body | 用户 2026-04-18 Option B UX 决策 `story-1.16/tips-markdown-format` |
| Hotkey 默认 | `hotkeys: []` | Obsidian 社区标准 |

### v1→v2 correct-course 触发点

- **Gap**: Round 3 审计报告 (`epic-1-audit-response-round-3-2026-04-17.md:102-110`) 技术决策表只抄了 "7 callout" 实现细节，**未整合** Round 3 QA Claude answers (`obsidian-qa-round3-claude-answers-2026-04-14.md:283-291`) 锁定的 "4 Tag + 3 态 checkbox" 设计。
- **发现**: 用户 2026-04-18 hands-on UAT v1 时批注 "没看到批注可以标记理解程度"，并确认 PRD 明确有"理解 / 似懂非懂 / 不理解" 3 种。
- **溯源确认**：
  - `_bmad-output/planning-artifacts/recovered/prd-tauri-original-2ae5897.md:399`（PRD Persona "ROG 选中对话 + 标 ✓已理解 + 写 Tips"）
  - `frontend/src/components/chat/InlineAnnotation.tsx:35-38,58-69`（前端旧代码 100% 实现过）
  - `_bmad-output/research/obsidian-qa-round3-claude-answers-2026-04-14.md:283-291`（Obsidian 等价方案：4 callout + 内置 3 checkbox）

### 代码骨架（v2 实施版）

实际代码见 `frontend/obsidian-plugin/src/callout.ts` + `src/main.ts`。核心形状：

```typescript
// callout.ts
export const TAG_OPTIONS = [
  { value: "tips",     label: "💡 Tips",     callout: "tips" },
  { value: "error",    label: "❌ 错误",     callout: "error" },
  { value: "question", label: "❓ 提问",     callout: "question" },
  { value: "keypoint", label: "📌 关键点",   callout: "keypoint" },
] as const;
export const UNDERSTANDING_OPTIONS = [
  { value: "understood",     label: "✅ 已懂" },
  { value: "fuzzy",          label: "🤔 模糊" },
  { value: "not-understood", label: "❌ 不懂" },
] as const;

export function wrapSelection(text, tag, understanding) {
  const header = `> [!${tag.callout}]+ ${tag.label}`;
  const checkboxes = UNDERSTANDING_OPTIONS
    .map((o) => `> - [${o.value === understanding ? "x" : " "}] ${o.label}`)
    .join("\n");
  const body = text.split("\n").map((l) => `> ${l}`).join("\n");
  return `${header}\n${checkboxes}\n>\n${body}`;
}

// main.ts
class TagTypeModal extends FuzzySuggestModal<TagOption> { /* 第 1/2 步 */
  onChooseItem(tag) {
    setTimeout(() => new UnderstandingModal(app, editor, selected, tag).open(), 50);
  }
}

class UnderstandingModal extends FuzzySuggestModal<UnderstandingOption> { /* 第 2/2 步 */
  onChooseItem(und) {
    editor.replaceSelection(wrapSelection(selected, tag, und.value));
  }
}
```

### 风格参考
- 现有 6 命令模式: `frontend/obsidian-plugin/src/main.ts:24-67`
- Notice 用法: `new Notice(msg, ms)`
- Editor 访问: `this.app.workspace.activeEditor?.editor`

---

## UAT Script v2 (非技术用户 10 步)

**前置**: Obsidian 已 Cmd+Q 重开加载 v2 main.js；hotkey 已绑（v1 已绑 `Cmd+Shift+A`，v2 保留不变）

1. **重载插件**：Cmd+Q 彻底退出 Obsidian，重新打开 canvas-vault
2. **测试空选中**: 不选文本，按 `Cmd+Shift+A` → Notice "请先选中文本再批注"（3 秒）
3. **测试第 1/2 步 modal**: 输入 "this is important" → 选中 → `Cmd+Shift+A` → 弹 modal placeholder "第 1/2 步：选标签类型"，4 选项 `💡 Tips / ❌ 错误 / ❓ 提问 / 📌 关键点`
4. **选 Tag "💡 Tips"**: 输 "tips" → Enter → 第 1 步关闭
5. **测试第 2/2 步 modal**: ~50ms 内第二个 modal 自动弹，placeholder "第 2/2 步：选理解度（Tag: 💡 Tips）"，3 选项 `✅ 已懂 / 🤔 模糊 / ❌ 不懂`
6. **选理解度 "🤔 模糊"**: 输 "模糊" → Enter → 文本变：
   ```
   > [!tips]+ 💡 Tips
   > - [ ] ✅ 已懂
   > - [x] 🤔 模糊
   > - [ ] ❌ 不懂
   >
   > this is important
   ```
7. **看 Reading View**: `Cmd+E` 切 Reading View → 看到 callout 块 + 3 个可点击的 checkbox（第 2 个打勾）
8. **测试 checkbox 切换**: 点击 "✅ 已懂" 那个 checkbox → `[ ]` 变 `[x]`（Obsidian 原生行为），同时 "🤔 模糊" 仍可保留打勾（或你手动再点取消 — 3 checkbox 是独立 task list，不是 radio）
9. **测试多行 + 另一 Tag + 不懂**: 选两行文本 → `Cmd+Shift+A` → 第 1 步选 "❌ 错误" → 第 2 步选 "❌ 不懂" → 看生成的 callout：`[!error]+` header + 第 3 checkbox 打勾 + body 两行各有 `> ` 前缀
10. **测试 Esc**: 选文本 → `Cmd+Shift+A` → 第 1 步 modal 出现 → Esc → 原文不变；再选 → `Cmd+Shift+A` → 第 1 步选 Tag 后 → 第 2 步 Esc → 原文不变（第 1 步 Tag 也不写入）

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

## 不会做的事 (v2)
- ❌ 不调 AI（Story 1.17 的事）
- ❌ 不写后端（纯 frontend plugin）
- ❌ 不改其他 6 命令（独立第 7 命令）
- ❌ 不预绑 hotkey（用户自定；v1 已绑 `Cmd+Shift+A`）
- ❌ **不同步 frontmatter `confidence_marks[]`**（Round 3 QA Line 286 完整设计的一部分，但涉及 FileManager API + cache 处理，延后到 Story 1.17 做 AI 双链时统一处理）
- ❌ **不注入 callout CSS**（`[!tips]` / `[!keypoint]` 非 Obsidian 原生 fallback 到灰色是已知限制，建议用户装 Callout Manager 插件自定义颜色；CSS 注入超出 1.16 scope）
- ❌ **不写"补充说明"文字**（Round 3 QA Line 257 提到的"Tag + 说明 + 理解度"3 步里的"说明"，用户 UX 决策选 Option B 只要 Tag + 理解度 2 步；说明作为 1.17 AI 双链的文本字段）

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

#### v1 (2026-04-18 22:13 UTC-7, commit 799b33c)

1. **AC #1 命令注册** — 第 7 命令 `canvas:annotate-callout`（"批注为标注"）追加到 `registerCanvasCommands()`，默认 `hotkeys: []`。
2. **v1 Modal** — `CalloutTypeModal extends FuzzySuggestModal<CalloutType>`（7 Obsidian 原生 callout），`setPlaceholder("选择标注类型")`。
3. **AC #3 空选中必需** — 双重防护：无 `activeEditor` → "编辑器未激活"；`getSelection()` 空 → "请先选中文本再批注"（3 秒）。
4. **v1 文本包裹** — `wrapSelection(text, type)` 首行 `> [!type]` + 每行 `> ` 前缀。
5. **v1 部署** — `main.js` 6535 bytes，cp 到 canvas-vault。用户 Cmd+Q 重载后验证命令列表 6 → 7。
6. **v1 hotkey 绑定** — 用户在 Settings > Hotkeys 绑 `Cmd+Shift+A`，Story 1.5 冲突检测无警告。

#### v2 correct-course (2026-04-18 22:45 UTC-7)

7. **触发点** — 用户 hands-on UAT 截图显示 callout 有 header 无 body（"this is important" 选中后生成 `> [!tip]` 但无 body 可点），批注原话："没要看到我的批注可以标记我的理解程度" + "我明确有在我们的 PRD 标记过批注可以标记理解，似懂非懂，不理解 3 种情况"。
8. **溯源确认** — (a) `_bmad-output/planning-artifacts/recovered/prd-tauri-original-2ae5897.md:399` PRD Persona 明确；(b) `frontend/src/components/chat/InlineAnnotation.tsx:35-38,58-69` 前端旧代码 100% 实现（Tauri 前端被 Obsidian 替代前）；(c) `_bmad-output/research/obsidian-qa-round3-claude-answers-2026-04-14.md:283-291` Round 3 QA 明确锁定 Obsidian 等价 = 4 callout + 内置 3 选 1 checkbox；(d) `_bmad-output/research/obsidian-qa-round2-claude-answers-2026-04-14.md:445` 3 选 1 "完全理解 / 似懂非懂 / 完全不理解"；(e) **Gap**：`_bmad-output/review/epic-1-audit-response-round-3-2026-04-17.md:102-110` 审计 Sec R2 技术决策表降级为 "7 callout"，丢失了 4 Tag + 3 态 checkbox。
9. **UX 决策** — `[DECISION-UX:story-1.16/tips-markdown-format]` 用户 2026-04-18 选 Option B（2 步 modal + 3 checkbox）。闭合 `[DECISION-RESOLVED:story-1.16/tips-markdown-format]`。
10. **代码改造** — `src/callout.ts` 重写（TAG_OPTIONS 4 项：`tips/error/question/keypoint` + emoji label；UNDERSTANDING_OPTIONS 3 项：`understood/fuzzy/not-understood` + emoji label；新 `wrapSelection(text, tag, understanding)` 生成 6 行 callout：header + 3 checkbox + `>` 分隔 + body）。`src/main.ts` 拆 `CalloutTypeModal` 为 `TagTypeModal`（第 1/2 步）+ `UnderstandingModal`（第 2/2 步），`setTimeout(50ms)` 衔接避免 modal stack 闪烁；placeholder 分别含 "第 1/2 步：选标签类型" / "第 2/2 步：选理解度（Tag: {label}）"。
11. **测试扩展** — `tests/callout.test.ts` v2: 9 个用例（TAG_OPTIONS 结构 / UNDERSTANDING_OPTIONS 结构 / 4 组具名 wrapSelection 用例 / 4×3=12 穷举 / 纯空格 / 空行保留）。`npm test` 9/9 green。
12. **部署** — `main.js` v2 7886 bytes（v1 6535），cp 到 canvas-vault；grep 验证 9 处 v2 符号（TagTypeModal / UnderstandingModal / TAG_OPTIONS / UNDERSTANDING_OPTIONS / 已懂 / 模糊 / 不懂）命中。
13. **非原生 callout 已知限制** — `[!tips]` 和 `[!keypoint]` 非 Obsidian 原生，Reading View fallback 为灰色样式但 header 仍显示 emoji label；`[!error]` 和 `[!question]` 保持原生彩色 + 图标。建议用户装 Callout Manager 插件自定义颜色（超出 Story 1.16 scope）。
14. **未做项（v2 scope 之外）** — frontmatter `confidence_marks[]` 同步（Round 3 QA Line 286，涉及 FileManager API）和 "补充说明"文字输入（Round 3 QA Line 257 的第 3 步）延后到 Story 1.17 AI 双链实施。

### File List (v2 累积)

- **MOD**（v2 重写）: `frontend/obsidian-plugin/src/callout.ts` — 替换 `CALLOUT_TYPES`/`CalloutType` 为 `TAG_OPTIONS` (4) + `UNDERSTANDING_OPTIONS` (3) + 新 `wrapSelection(text, tag, understanding)`
- **MOD**（v2 重写）: `frontend/obsidian-plugin/src/main.ts` — 拆 `CalloutTypeModal` 为 `TagTypeModal`（第 1/2 步）+ `UnderstandingModal`（第 2/2 步），`setTimeout(50ms)` 衔接
- **MOD**（v2 扩展）: `frontend/obsidian-plugin/tests/callout.test.ts` — 9 个 `node:test` 用例（v1 的 6 个被重写，+4×3=12 穷举 + 空行保留 + 纯空格）
- **NEW**（v1）: `frontend/obsidian-plugin/.gitignore`
- **MOD**（v1）: `frontend/obsidian-plugin/package.json` — `test` script 不变
- **MOD**: `_bmad-output/implementation-artifacts/sprint-status.yaml` — 1-16 状态 `review → in-progress`（correct-course 回退）
- **MOD**: `_bmad-output/implementation-artifacts/epic-1/1-16-annotate-callout-hotkey.md` — AC v2 重写、Dev Tasks v2、File List v2、Change Log v2 条目

构建产物 `frontend/obsidian-plugin/main.js` (v2 7886 bytes，v1 6535) 和部署副本 `canvas-vault/.obsidian/plugins/canvas-learning-system/main.js` 不入 git（`.gitignore`），由 `npm run build` 即时重建。

### Change Log

- 2026-04-18 v1 — 初次实施 Story 1.16。新增 callout 模块 + 第 7 命令 + CalloutTypeModal（7 Obsidian 原生 callout）。6/6 单元测试通过。部署到 canvas-vault。Commit `799b33c`. [PLAN: EPIC1-BMAD-DEV-ASSESS-2026-04-17]
- 2026-04-18 v2 correct-course — 用户 UAT v1 后批注 "没看到批注可以标记理解程度"，溯源确认 Story 1.16 spec 偏离 Round 3 QA 定案（`obsidian-qa-round3-claude-answers-2026-04-14.md:283-291` 锁定的 "4 Tag + 3 态 checkbox" 被 Round 3 审计报告 `epic-1-audit-response-round-3-2026-04-17.md:102-110` 降级为 "7 callout"），且 PRD Persona (`prd-tauri-original-2ae5897.md:399`) 和前端旧代码 (`frontend/src/components/chat/InlineAnnotation.tsx:35-38, 58-69`) 交叉印证 4 AnnotationTag + 3 UnderstandingLevel。用户 `[DECISION-UX:story-1.16/tips-markdown-format]` 选 Option B（2 步 modal + 3 checkbox）。重写 `src/callout.ts`（TAG_OPTIONS 4 / UNDERSTANDING_OPTIONS 3 / 新 wrapSelection）+ `src/main.ts`（TagTypeModal + UnderstandingModal）+ `tests/callout.test.ts` 扩至 9 用例（含 4×3=12 穷举）。9/9 测试通过。build 7886 bytes（v1 6535）。待 UAT v2 + code review。[PLAN: EPIC1-BMAD-DEV-ASSESS-2026-04-17]
