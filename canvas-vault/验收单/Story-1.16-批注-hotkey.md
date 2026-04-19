---
story: "1.16"
title: "批注 Hotkey + 4 Tag + 3 态理解度"
status: "review"
version: "v2"
date: "2026-04-18"
developer: "Claude Code (Opus 4.7)"
---

# Story 1.16 验收单（给你看的版本）

> [!info]+ 这是什么
> 这是 Story 1.16 的用户验收文档，**给你（非技术）读的版本**。
> 技术 spec 在 `_bmad-output/implementation-artifacts/epic-1/1-16-annotate-callout-hotkey.md`（Claude 读的）。
> 这份文档里没有技术术语，只有你能看到、摸到、点击的行为。

---

## 🎯 这个 Story 要做到什么

你**选中笔记里的一段文字**，按 **`Cmd+Shift+A`**，就能快速把它标成 4 种"用途"之一（Tips / 错误 / 提问 / 关键点），并且标上你对这段内容的**理解程度**（已懂 / 模糊 / 不懂）。

以后 AI 出题时会优先拿"模糊 / 不懂"的内容考你，你点击 checkbox 还能随时改理解度。

---

## 📖 用户故事（你的视角）

**作为** 正在学知识的你，
**我想** 选中一段看不懂/要记住的文字，一个 hotkey 就能给它贴标签、标理解度，
**以便** 不用记 Obsidian 的 callout 语法，也不用离开编辑器，就能把"这里我懂了 / 这里我糊涂 / 这里是重点"记下来，未来复习时有迹可循。

---

## 🖥️ 你会看到的交互（一步一步）

```
1. 在笔记里选中一段文字
       ↓
2. 按 Cmd+Shift+A
       ↓
3. 弹出 [第 1/2 步] 小窗口，你选 4 种标签之一：
       💡 Tips  /  ❌ 错误  /  ❓ 提问  /  📌 关键点
       ↓
4. 自动弹出 [第 2/2 步] 小窗口，你选 3 种理解程度之一：
       ✅ 已懂  /  🤔 模糊  /  ❌ 不懂
       ↓
5. 你选中的文字变成这样（举例你选了 💡 Tips + 🤔 模糊）：

       > [!tips]+ 💡 Tips
       > - [ ] ✅ 已懂
       > - [x] 🤔 模糊
       > - [ ] ❌ 不懂
       >
       > <你原本选中的文字>

6. 切 Reading View (Cmd+E) 看到完整 callout 块 + 3 个可点击的 checkbox
7. 以后想改理解度，直接点 checkbox 切换 ✅ ↔ [空]
```

---

## ✅ 验收清单（10 步 UAT — 你一步步跑，勾掉每一项）

> [!tip]+ 怎么用这份清单
> 每跑完一步，**选中那一行的 `- [ ]`**，**按 `Cmd+Shift+A`**？不行，用**直接点击 checkbox 切换**更简单（Obsidian 原生支持）。
> 发现不对劲 → **选中整行 → Cmd+Shift+A → ❌ 错误 + ❌ 不懂**，把问题批到这个文档里，我会看到。

### 第 0 步：前置（必须做）

- [ ] 已经按 `Cmd+Q` 完全关闭 Obsidian 再重开（加载新 main.js v2）
- [ ] Settings > Hotkeys 搜 "批注" 看到 "批注为标注" 绑着 `Cmd+Shift+A`
- [ ] 知道 `Cmd+E` 可以在编辑/阅读视图之间切换

### 第 1 步：空选中提醒

- [ ] 不选任何文字，按 `Cmd+Shift+A`
- [ ] 右上角弹出 3 秒黑色 Notice："**请先选中文本再批注**"
- [ ] **不**弹任何 modal 窗口

### 第 2 步：第 1/2 步 modal

- [ ] 在笔记里选中 "this is important"
- [ ] 按 `Cmd+Shift+A`
- [ ] 弹出一个 modal，顶部输入框写着 "**第 1/2 步：选标签类型**"
- [ ] 看到 4 个选项（带 emoji）：💡 Tips / ❌ 错误 / ❓ 提问 / 📌 关键点

### 第 3 步：选 Tag "💡 Tips"

- [ ] 输 "tips" 过滤，或用上下箭头选到 "💡 Tips"
- [ ] 按回车
- [ ] 第 1 步 modal 关闭

### 第 4 步：第 2/2 步 modal 自动弹出

- [ ] 大约 50 毫秒后，第二个 modal 自动弹出
- [ ] 输入框写着 "**第 2/2 步：选理解度（Tag: 💡 Tips）**"（注意包含你刚选的 Tag）
- [ ] 看到 3 个选项：✅ 已懂 / 🤔 模糊 / ❌ 不懂

### 第 5 步：选 "🤔 模糊"

- [ ] 输 "模糊" 或箭头选中
- [ ] 按回车
- [ ] modal 关闭，焦点回到笔记
- [ ] 选中的 "this is important" 变成 6 行：
  ```
  > [!tips]+ 💡 Tips
  > - [ ] ✅ 已懂
  > - [x] 🤔 模糊
  > - [ ] ❌ 不懂
  >
  > this is important
  ```

### 第 6 步：Reading View 看渲染

- [ ] 按 `Cmd+E` 切到 Reading View
- [ ] 看到一个灰色 callout 块（`[!tips]` 非 Obsidian 原生会 fallback 灰色，但 header 显示 💡 Tips）
- [ ] callout 块里包含 3 个 checkbox
- [ ] 第 2 个 checkbox（🤔 模糊）**是打勾状态**
- [ ] 最底下有你原本的文字 "this is important"

### 第 7 步：点击 checkbox 切换理解度

- [ ] 在 Reading View 里点击 "✅ 已懂" 这个 checkbox
- [ ] 它从 `[ ]` 变 `[x]`（打勾）
- [ ] 再点一次变回 `[ ]`（取消）
- [ ] 能和其他 checkbox 独立切换（不是单选）

### 第 8 步：多行 + 另一 Tag + 不懂

- [ ] 切回编辑视图（再按 `Cmd+E`）
- [ ] 选中**两行**新文字（比如 "第一行\n第二行"）
- [ ] 按 `Cmd+Shift+A` → 选 "❌ 错误" → 选 "❌ 不懂"
- [ ] 生成结果的 header 是 `> [!error]+ ❌ 错误`
- [ ] 第 3 个 checkbox（❌ 不懂）打勾
- [ ] body 部分两行文字**各自**有 `> ` 前缀

### 第 9 步：Esc 取消（第 1 步）

- [ ] 选中文字 → `Cmd+Shift+A`
- [ ] 第 1/2 步 modal 出现
- [ ] 按 `Esc`
- [ ] modal 关闭，**原文字不变**

### 第 10 步：Esc 取消（第 2 步）

- [ ] 选中文字 → `Cmd+Shift+A` → 随便选一个 Tag
- [ ] 第 2/2 步 modal 出现
- [ ] 按 `Esc`
- [ ] modal 关闭，**原文字不变**（第 1 步选的 Tag 也不会写入）

---

## 🚦 验收结果

**如果 10 步全部 ✅**：告诉我 "**Story 1.16 通过**"，我把它 mark as **done**，立即启动 Story 1.17（AI 双链文档）。

**如果有任何一步 ❌**：在下面批注区写出具体哪一步 + 你看到的实际现象，我根据你反馈 `bmad-bmm-correct-course` 调整。

---

## 📝 你的批注区

> [!question]+ 你对 Story 1.16 v2 的批注
>
> 在这里写任何疑问/建议/不满意。或者直接用 `Cmd+Shift+A` 批注上面任何一段。
>
> （空）

### 已知的已批注问题（历史追溯）

> [!error]+ 2026-04-18 — v1 严重 scope 偏离
> **你的原批注**："没看到我的批注可以标记我的理解程度"+"我明确有在我们的 PRD 标记过批注可以标记理解，似懂非懂，不理解 3 种情况"
>
> **根因**：Story 1.16 spec 偏离了 Round 3 QA 的锁定方案（Round 3 QA 明确 4 Tag + 3 态 checkbox，但审计报告把它降级成了 7 个原生 Obsidian callout），我没查 PRD 就实施了。
>
> **已修复**：v2 重写 callout 模块 + Modal（2 步）+ 3 态 checkbox。等你这次 UAT 10 步跑完验收。

### v1 → v2 你将看到的变化

| 维度 | v1（已淘汰） | v2（现在） |
|---|---|---|
| Callout 种类 | 7 个原生（tip/question/warning/...）| **4 个语义 Tag**（Tips/错误/提问/关键点）|
| 理解度标记 | ❌ 无 | ✅ **3 态 checkbox**（已懂/模糊/不懂）|
| Modal 步骤 | 1 步 | **2 步**（先选 Tag，再选理解度）|
| Markdown 行数 | 1 行 header + body | **6 行**（header + 3 checkbox + 空行 + body）|
| 可事后改理解度 | ❌ | ✅ **点击 checkbox 切换**|

---

## 🔗 技术 spec 参考（给 Claude 读的，不是给你读的）

- Story spec：`_bmad-output/implementation-artifacts/epic-1/1-16-annotate-callout-hotkey.md`
- 源代码：`frontend/obsidian-plugin/src/callout.ts` + `src/main.ts`
- 单元测试：`frontend/obsidian-plugin/tests/callout.test.ts`（9 用例 9/9 通过）
- Git commit：`e200ca8` — refactor(epic-1): story 1.16 v2

---

## 📅 下一步（你批完这份单后）

1. **全部 ✅** → 说 "通过" → 我立即 mark done → 启动 Story 1.17（AI 双链）
2. **部分 ❌** → 在批注区写清楚，或者选中那几行用 `Cmd+Shift+A` 批 `❌ 错误 + ❌ 不懂` → 我跑 correct-course 再次修正
