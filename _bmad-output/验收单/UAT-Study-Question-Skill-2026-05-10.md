---
story: "Study-Question-P0 (Story 2.3 Phase 1)"
title: "study-question-skill-deep-mode"
status: "review"
version: "1.2"
date: "2026-05-11"
developer: "Claude Code (Opus 4.7 1M context)"
commit: "f3c002a (initial) + v1.2 删 hotkey 保 command (pending commit)"
---

# 解题深度模式 Skill — 验收单（给你看的版本）

> [!info]+ 这是什么
> 你最初反馈："解题时对相关内容不懂、知识点不懂时，需要全局搜索教学笔记给我回复"。这次实施了 **解题深度模式 skill** — 跟 Cmd+Shift+E 快问快答互补，30-45s 给你一份**强制 4 段结构化诊断**（定义/直觉/反例/联系），不是自由对话。
> 这份文档只列你能看到、点击、感觉到的行为。
> **触发路径**：编辑器内 Cmd+P 命令面板搜「解题深度模式」 / Claudian 内直打 `/study-question 问题`。**无 hotkey**（v1.2 修复，详见末尾历史追溯）。

---

## 🎯 这个 Skill 要做到什么

**你在解题不懂时按 Cmd+P 搜「解题深度模式」，30-45s 内拿到一份「严格 4 段诊断」，每个声明都引用真实笔记的具体段落。**

---

## 📖 用户故事（你的视角）

**作为** 学习者在解题时不懂某个概念，
**我想** 通过 Cmd+P 命令面板触发"解题深度模式"，让 AI 先做"是什么 / 怎么做 / 为什么 / 比较" 四类分类，再读 3 个完整教学章节，给我一份强制结构化的诊断（包含定义、直觉、反例、联系节点），每个声明都有 wikilink 指向具体段落，
**以便** 我不用东拼西凑读半小时笔记，直接看 AI 整合的"教学版答案"。

---

## 🖥️ 你会看到的交互（一步一步）

**路径 A — 编辑器内触发（保留 backend full RAG 注入）**：

```
1. 我在 Obsidian 打开 节点/<不懂的概念>.md
       ↓
2. 我按 Cmd+P 打开命令面板
       ↓
3. 我输入 "解题" → 看到 "解题深度模式（study-question · 30-45s 4 段结构化诊断）" 条目 → 回车
       ↓
4. 弹出 "💬 你想问什么？" 输入框
       ↓
5. 我输入 "什么是 admissibility 怎么证明" → Enter
       ↓
6. 右上角弹出 "🧠 解题深度模式已就绪 XKB / N 邻居 + N 补充材料 ⭐（deep 模式）"
       ↓
7. Obsidian 自动切到 Claudian 侧栏 → 我 Cmd+V 粘贴 → Enter
       ↓
8. Claude 先输出 "[1/5] Query intent: Definition" → "[2/5]..." → "[3/5]..." → "[4/5]..." → "[5/5]..."
       ↓
9. Claude 输出主答案 — 4 段严格结构：
   ## 严格定义 (含 [[file#heading]] 引用)
   ## 直觉理解 (含 wikilink)
   ## 1 个反例 / 边界 (含 wikilink)
   ## 联系节点 (1-hop / 2-hop 邻居 + mastery 颜色)
       ↓
10. 末尾 --- 分隔后展示完整 supplementary 列表
```

**路径 B — Claudian 内直接触发（light RAG，无 backend 注入）**：

```
1. 我在 Claudian 侧栏输入框
       ↓
2. 我打 "/study-question 什么是递归" → Enter
       ↓
3. Claude Code SDK 加载 study-question SKILL.md
       ↓
4. Claude 用 Read/Glob 自己找 vault 节点 → 按 4 段结构合成
```

---
**User: 我在 claudian 输入的时候，是没有看到/study-question 这个 skill 的命令。**

## 🤖 Claude 已代验（你不用跑，给你看证据用）

> [!success]+ 这一段是 Claude 自动跑完贴证据
> **你不用跑也不用懂**。出现 `Pydantic` / `Literal` / `mode=deep` / `top_k_max` / `pytest` 等技术词不算 bug，是 Claude 应该处理的。

| # | 技术验证项 | 结果 |
|---|---|---|
| 1 | SQ-1 `canvas-vault/.claude/skills/study-question/SKILL.md` 文件就位（15 HARD CONSTRAINTS + 5 阶段 pipeline + 4 段输出按 intent 路由） | ✅ 文件存在 |
| 2 | SQ-2 main.ts cmds 数组 `id: "canvas:study-question"` command 已注册（Cmd+P 命令面板可搜到），`DEFAULT_HOTKEYS` v1.2 已移除 hotkey 绑定（避免占心智） | ✅ grep 验证 deployed main.js 含 2 处 canvas:study-question refs（cmd 注册 + handler log），0 处 hotkey binding |
| 3 | SQ-2 `handleStudyQuestion()` 方法已实现（170 行，复用 chat-with-context 80% 逻辑） | ✅ tsc --noEmit 0 新 error |
| 4 | SQ-3 `EnrichContextRequest.mode` Literal 扩展 `['preload', 'answer', 'deep']` | ✅ `test_mode_deep_accepted_by_request_model` passed |
| 5 | SQ-3 `mode=deep` 时 supplementary 用 `top_k_max=30 / hard_cap=20`（vs answer 20/15） | ✅ `test_mode_deep_uses_top_k_30_and_hard_cap_20` + `test_mode_answer_keeps_top_k_20_and_hard_cap_15` passed |
| 6 | SQ-3 `mode=deep` 无 user_question 时跳过 supplementary search（与 answer 一致） | ✅ `test_mode_deep_without_user_question_skips_search` passed |
| 7 | SQ-3 非法 mode（如 `'shallow'`）被 Pydantic 拒绝 422 | ✅ `test_mode_invalid_rejected_by_pydantic` passed |
| 8 | SQ-4 8 个新单测全部通过 + 65 总测试 0 regression（含多 vault P0-1 8 isolation 测试） | ✅ `pytest tests/unit/test_study_question_deep_mode.py tests/unit/test_rag_p0_* tests/unit/test_enrich_context_vault_isolation.py` 65 passed |
| 9 | Pre-push A11 regression suite 19 passed / 13 skipped | ✅ commit f3c002a backup + origin push 全通过 |
| 10 | OpenAPI spec 自动同步（mode='deep' 已写入 schema） | ✅ spec-sync hook 已重新导出 openapi.json |
| 11 | v1.2 plugin 重建 + 部署到 canvas-vault | ✅ npm run build (133K) + cp 到 `.obsidian/plugins/canvas-learning-system/main.js` |

---

## 👤 你来验（产品使用体验 — 5 步，10 分钟内全在 Obsidian 里完成）

> [!warning]+ 这段的硬规矩
> ✅ 句型："**我做 X → 我看到 Y → 我感觉 Z**"
> ✅ 工具白名单：Obsidian 主界面 + Claudian 侧栏
> ⛔ 全部 Obsidian 内完成，不需要离开

### 第 0 步：First 5 seconds（plugin 加载完 + command 注册生效）

> Plugin build 后需要 Reload 让新 main.js 生效。这一步只做一次。

- [ ] 我在 Obsidian 按 **Cmd+P** 打开命令面板
- [ ] 我输入 "Reload app without saving" → 回车
- [ ] 5 秒内 Obsidian 重新加载完成
- [ ] 我感觉：(a) 一切正常 (b) 有报错弹窗 — 选: ___

### 第 1 步：核心场景 — Cmd+P 触发深度模式

- [ ] 我在 Obsidian 打开任意 `节点/<concept>.md`（例 `节点/admissibility.md` 或你想深问的任意节点）
- [ ] 我按 **Cmd+P** 打开命令面板
- [ ] 我输入 "解题"（或 "深度模式" / "study-question"）→ 应看到条目 **"解题深度模式（study-question · 30-45s 4 段结构化诊断）"**
- [ ] 我回车选中
- [ ] 我看到弹出 "💬 你想问什么？" 输入框（与 Cmd+Shift+E 同样的 modal）
- [ ] 我感觉：命令面板入口清晰，3 秒内找到正确条目

### 第 2 步：输入问题 + 看 Notice

- [ ] 我输入一个**真不懂**的问题（例 "什么是 admissibility，怎么证明？" 或 "局部最优陷阱怎么解"）→ 按 Enter
- [ ] 我等 5-15 秒（比 Cmd+Shift+E 慢一些，是正常的，deep 模式召回 30 条比 20 条多）
- [ ] 我看到右上角 Notice：**"🧠 解题深度模式已就绪 XKB / N 邻居 + N 补充材料 ⭐（deep 模式） / X/Y tokens（XXXms） 切到 Claudian 粘贴 — 预计 30-45s 出 4 段结构化诊断"**
- [ ] **关键标识**：Notice 文字含 "**deep 模式**" 和 "**4 段结构化诊断**"（区别于 Cmd+Shift+E 的 "AI 对话 v2"）
- [ ] 我感觉：明确知道这次是深度模式，不是普通快问快答

### 第 3 步：粘贴到 Claudian + 看 5 阶段进度

- [ ] 我看到 Obsidian 自动切到 Claudian 侧栏
- [ ] 我在 Claudian 输入框粘贴（Cmd+V）→ 按 Enter
- [ ] 我**等 30-45 秒**（深度模式慢，是设计的）
- [ ] 我看到 Claude 先输出 **5 行进度提示**：
  ```
  [1/5] Query intent: <Definition / Procedure / Causal / Comparison>
  [2/5] 检索维度: ...
  [3/5] backend 召回 N 条 (score X.XX-Y.YY)
  [4/5] Read 完整章节: rank-1 / rank-2 / rank-3
  [5/5] 合成中...
  ```
- [ ] 我感觉：AI 没有沉默 30s，每一步都告诉我它在做什么

### 第 4 步：检查 4 段强制结构化输出

- [ ] 我看到主答案有**清晰的 4 段标题**（按问题类型路由）：
  - 问"是什么 / 定义" → `## 严格定义` / `## 直觉理解` / `## 1 个反例 / 边界` / `## 联系节点`
  - 问"怎么做 / 步骤" → `## 前提条件` / `## 执行步骤` / `## 完整例子` / `## 联系节点`
  - 问"为什么 / 原因" → `## 因果链` / `## 每步证据` / `## 误区 / 常见混淆` / `## 联系节点`
  - 问"X vs Y" → `## X 是什么` / `## Y 是什么` / `## 关键差异` / `## 何时选谁` / `## 共同祖先`
- [ ] 我看到每个段落里的引用都是**精确到 heading**的格式：`[[file#heading]]` 或 `[[file#^block]]`
- [ ] 我看到**不是** `[[file]]` 这种全文模糊引用（如果出现 = ❌ 在批注区记录）
- [ ] 末尾 `---` 分隔后有完整 supplementary 列表（rank/title/wikilink/snippet/score）
- [ ] 我感觉：(a) 这是教学版答案，不是普通对话 (b) 还是普通对话，没看出深度差异 — 选: ___

### 第 5 步：测试 Claudian 路径 + 边界（留空问题）

**5a — Claudian 内直触发**：
- [ ] 我直接在 Claudian 输入框打 `/study-question 什么是递归` → Enter
- [ ] 我看到 Claude 加载 SKILL.md 并按 4 段结构回答（**light RAG，无 backend full 注入** — 这是设计预期）
- [ ] 我感觉：双路径都能用，按场景选

**5b — Cmd+P 路径留空问题**：
- [ ] 我打开任意节点 → 按 Cmd+P → 选 "解题深度模式"
- [ ] 我**留空**输入框 → 按 Enter
- [ ] 我看到 Notice："深度解题模式需要明确的问题（无法空查询）。请输入要解的题/概念"
- [ ] 我感觉：被明确拦住了，没有奇怪的"在思考..."无限等待

### 主观打分（Felt-sense）

- [ ] **答案深度**（1=和 Cmd+Shift+E 一样 / 5=明显更深入）：___
- [ ] **4 段结构清晰度**（1=没看出结构 / 5=每段都有清晰标题）：___
- [ ] **wikilink 引用准确度**（1=点了打不开 / 5=每条都跳对地方）：___
- [ ] **30-45s 等待感**（1=太慢想关 / 5=值得等）：___
- [ ] **触发路径友好度**（Cmd+P vs hotkey vs /command）：___
- [ ] 一句话：你打这些分的最主要原因是 ___

---

## 🚦 验收结果

**所有步骤 ✅** → 告诉我 "**Study-Question 通过**" → Claude mark as **done**，Phase 2（multi-query Haiku 拆解 + multi-hop 并发）可以排期。

**第 4 步没看到 4 段结构** → 在批注区记下截图，Claude 强化 SKILL.md 的 HARD CONSTRAINTS prompt。

**第 4 步看到 `[[file]]` 全文模糊引用** → 在批注区记下，Claude 在 ANCHOR_INSTRUCTION 加更强约束。

**第 5a Claudian 内 /study-question 不识别** → 在批注区记下，可能 SKILL.md 还没被 Claude Code SDK 加载（确认 `canvas-vault/.claude/skills/study-question/SKILL.md` 路径正确）。

---

## 📝 你的批注区

> [!question]+ 你对解题深度模式 Skill 的批注
>
> 用 Cmd+Shift+A 在上面任何一段批注 `❌ 错误` / `❓ 提问` / `💡 建议`。
>
> （空）

### 已知的已批注问题（历史追溯）

> [!error]+ 2026-05-10 — v1.0 → v1.1 → v1.2 三次修复（hotkey 设计认知逐步深入）
>
> **v1.0 → v1.1（hotkey Q → S）**
> 你的原批注 1："Cmd+Shift+Q 是关掉程序的设计，而且如果你是设计的是 skill，那么完全可以使用 /命令 在 claudian 的对话框触发"
> 根因 1：Cmd+Shift+Q 是 macOS 系统级"注销用户"hotkey（Apple 不可被 app 覆盖 → plugin 永远绑不上 + 误触注销账号）
> 已做（v1.1）：hotkey Q → S（S=Study/Solve 语义匹配）
>
> **v1.1 → v1.2（删 hotkey 完全 / 保留 plugin command）— 你的批注 2 深层洞察**
> 你的追问："Cmd+Shift+S 没反应 + 一个搜索信息的 skill 你为什么绑定快捷键的理由是什么？"
> 根因 2：search-info 类 skill 不依赖编辑器 selection / 不改文件 → hotkey 占心智但无价值。hotkey 应该留给"必须从编辑器某状态触发"的 ai-linked-doc / annotate-callout / configure-whiteboard。
> 已做（v1.2）：
> - `main.ts` DEFAULT_HOTKEYS 完全移除 canvas:study-question 一行
> - SKILL.md description / argument-hint / 全文 hotkey 引用替换为 "Cmd+P → 解题深度模式"
> - **plugin command 保留**：Cmd+P 命令面板可搜 → 走相同 backend full RAG path
> - 双轨：Cmd+P 命令面板（保留 full RAG）+ Claudian 直打 `/study-question`（light RAG）

### v1.0 → v1.1 → v1.2 你将看到的变化

| 维度 | v1.0（已淘汰） | v1.1（已淘汰） | **v1.2（现在）** |
|---|---|---|---|
| Hotkey | Cmd+Shift+Q（macOS 系统级拦截）| Cmd+Shift+S | **无 hotkey** |
| 编辑器内触发 | hotkey | hotkey | **Cmd+P → "解题深度模式"** |
| Claudian 内触发 | hotkey | hotkey + `/study-question` | **`/study-question`** |
| Hotkey 占心智 | 1 个 | 1 个 | **0** |
| Backend full RAG | 通过 hotkey | 通过 hotkey | **通过 Cmd+P 命令面板**（路径相同）|
| 误触代价 | 弹出注销账号确认框 | 无（但浪费心智）| **无** |

---

## 🔗 技术 spec 参考（给 Claude 读的）

- **设计文档**：`_bmad-output/research/round-23-study-question-skill-design-2026-05-10.md`（1067 行，含 8 业界产品对照 + 5 学术教训）
- **修改文件**：
  - `canvas-vault/.claude/skills/study-question/SKILL.md` — Skill 主文件（15 HARD CONSTRAINTS + 5 阶段 + 4 段结构）
  - `frontend/obsidian-plugin/src/main.ts` — cmds 数组 command 注册 + handleStudyQuestion 方法（v1.2 hotkey 已删）
  - `backend/app/api/v1/endpoints/chat.py` — EnrichContextRequest.mode Literal 扩展 + handler 按 mode 路由参数
- **单元测试**：`backend/tests/unit/test_study_question_deep_mode.py` — 8 用例 / 8 passed
- **Git commit**：
  - `f3c002a` — `feat(study-question-p0)` 初版（v1.0）
  - v1.2 改动 pending commit
- **业界对照**：Perplexity Deep Research / NotebookLM / SocraticLM / CausalRAG / StepChain（multi-pass 共识）
- **3 并行 agent deep explore 结论**：search-info 类 skill 不应绑 hotkey；hotkey 应留给"必须从编辑器状态触发"的副作用类 skill

---

## 📅 下一步（你批完这份单后）

1. **全部 ✅** → 说 "Study-Question 通过" → Claude mark done → Phase 2（multi-query + multi-hop 并发）排期
2. **第 4 步部分 ❌** → 在批注区记录哪段缺失 → Claude 跑 `bmad-bmm-correct-course` 强化 SKILL.md prompt
3. **想暂停验证** → 告诉 Claude "暂停 Study-Question UAT"
