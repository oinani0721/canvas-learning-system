---
story: "1.17"
title: "AI 双链文档（形态 β：Plugin + Claudian Skill）"
status: "review"
version: "v2.1"
date: "2026-04-20"
developer: "Claude Code (Opus 4.7)"
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
---

> [!error]+ 2026-04-20 — v2 → v2.1 critical correct-course（基于你的 UAT 批注）
> **你的原批注**（上一轮 UAT）：
> 1. "Cmd+Shift+D 和 Cmd+Shift+V 有什么区别吗？Cmd+Shift+D 我是使用后也没有自动把文字复制到剪贴板，然后后续的操作也都没有触发"
> 2. "最后这 3 行没看到，感觉成为了类似的幻觉"
> 3. "创建了不存在的双向链接，生成文档自以为是偏离主题没有原文，然后也没有返回从哪一个拉出来的双向链接"
> 4. "没有双链 / 文档不存在" (index.md)
>
> **3 并行 Agent 调研根因**：
> - **Claudian plugin 本身不路由 Skill** — 核心颠覆发现！Claudian 只在用户输入框显示 slash 提示的 dropdown，**Skill 是否调用完全由 Claude 模型判断**（Claudian main.js:60410 把整段 prompt 送 Claude Agent SDK，不做路由）。原 SKILL.md 的 description 写的是"做什么"不是"何时调用" → 模型看不到强 signal → 自由发挥，写到 `wiki/concepts/` 还捏造一堆不存在的 wikilink。
> - **源笔记路径问题** — 你测试用的是 `未命名.md`（vault 根），不在 `wiki/canvases/math240/` 下 → Plugin 拿到 `sourcePath=未命名.md` + `subject=unknown` → Skill 应该 AskUserQuestion，但 Claude 自由发挥时跳过了。
> - **Notice 不够醒目** — Obsidian 右下角 Notice 3 秒太短，文案不够明确。
>
> **已修复**（v2.1）：
> - `buildAIDocPrompt` prompt 加显式指令：`Please invoke the Skill tool with skill_name="ai-linked-doc"` + `Do NOT answer freely`
> - SKILL.md description 重写为触发条件（"当消息以 /ai-linked-doc 开头时必须调用"）
> - SKILL.md 开头加 `⛔ CRITICAL TRIGGER & HARD CONSTRAINTS` 7 条硬约束（必须 Step 1-7 顺序 / 不得自由发挥 / 必写 wiki/canvases/ / 禁捏造 wikilink / 必返 3 行 ✓ / unknown subject 必问 / 非 canvases 路径必问）
> - SKILL.md Step 4 加硬验证（路径不以 wiki/canvases/ 开头则 abort）
> - SKILL.md 末尾加 6 项执行自检清单
> - Plugin `handleAILinkedDoc` 加 `console.log("[canvas:ai-linked-doc] triggered")`，"编辑器未激活"Notice 改为 5 秒详细指引，非 canvases 路径预警 7 秒 Notice，成功 Notice 改为 8 秒含 "首行是 /ai-linked-doc 会触发 Skill" 提示
> - build 11608 bytes（v2 10571 + 1037B 强化）
>
> **请按下方 v2.1 UAT Script 重新跑**（主要区别见清单"v2 → v2.1 你将看到的变化"）。

# Story 1.17 验收单（给你看的版本）

> [!info]+ 这是什么
> 这是 Story 1.17 的用户验收文档，**给你（非技术）读的版本**。
> 技术 spec 在 `_bmad-output/implementation-artifacts/epic-1/1-17-ai-linked-doc.md`（Claude 读的）。
> 这份文档里没有技术术语，只有你能看到、摸到、点击的行为。

---

## 🎯 这个 Story 要做到什么
**User:按 Cmd+Shift+D    和 Cmd+Shift+V 有什么区别吗？你这里好像就变成了单纯的复制操作，然后Cmd+Shift+D 我是使用后也没有自动把文字复制到剪贴板 ，然后后续的操作也都没有触发**
你在学习笔记里**选中一段看不懂/要提炼的文字**，按 **`Cmd+Shift+D`**，插件会自动把文字复制到剪贴板并打开 Claudian 侧栏。你在侧栏 `Cmd+V` 粘贴 → 回车，**Claude Code 用你的订阅额度**（不用额外充 API key 钱）生成一份结构化的概念文档，把源笔记里你选的那段文字自动替换成 `[[概念名]]` 双链，还会在当前"原白板"的 `index.md` 里自动加一条记录。

等同于：**一键从"阅读中的一段话" → "一个可跳转的独立概念笔记 + 自动入目录"**。

---

## 📖 用户故事（你的视角）

**作为** 正在读资料的学生，
**我想** 读到看不懂的段落时，一键把它变成一个独立概念笔记并自动双链回来，
**以便** 不用打断阅读去手动建文件、复制粘贴、打标题、加 wikilink —— 所有机械动作 AI 自动做完，我专注理解。

---

## 🖥️ 你会看到的交互（一步一步）

```
在 wiki/canvases/math240/Fundamentals.md 选中:
    "Eigenvalues are special vectors that satisfy Av = λv"
        ↓ 按 Cmd+Shift+D
        ↓
Plugin 自动做 3 件事:
 1. 复制 prompt 到剪贴板（含选中文本 + 源笔记路径 + 学科）
 2. 弹 Notice: "已复制到剪贴板，切到 Claudian 粘贴即可触发"
 3. 打开 Claudian 侧栏（右侧）
        ↓
你在 Claudian 输入框 Cmd+V 粘贴 → Enter
        ↓
Claude Code（你的订阅额度）识别 /ai-linked-doc 加载 Skill
        ↓
Skill 执行 6 步（约 10-30 秒）:
  Step 1: 解析输入（选中文本 / 源笔记 / 学科）
  Step 2: 生成三段式概念文档（## 核心概念 / ## 关键点 / ## 关联概念）
  Step 3: 提取主概念名（如 "Eigenvalues"）
  Step 4: 写 wiki/canvases/math240/Eigenvalues.md
  Step 5: 把源笔记选中文本替换为 [[Eigenvalues]]
  Step 6: 更新 wiki/canvases/math240/index.md（doc_count +1）
        ↓
Claudian 返回 3 行 ✓ 摘要
        ↓
你切回源笔记看到 [[Eigenvalues]] 双链 → 点击跳转到新文件
```

**零额外付费**：用你的 Claude Code Pro/Max 订阅额度，不需要去 console.anthropic.com 再配 API key。

---

## ✅ 验收清单（14 步 UAT）

> [!tip]+ 怎么用这份清单
> 每跑完一步点击对应 `- [ ]` 切换为 `[x]`。
> 发现不对劲 → 选中行 `Cmd+Shift+A`（Story 1.16 的 hotkey）→ `❌ 错误` + `❌ 不懂`，把问题批到文档里。

### 第 0 步：前置（v2.1 — 每项必须逐条满足）

- [ ] **关键**：Obsidian 里按 `Cmd+P` → 搜 "reload" → 点 "**Reload app without saving**"（让新 main.js v2.1 加载到内存，不能仅靠 Cmd+Q，有时窗口复用会保留旧插件实例）
- [ ] 确认 canvas-vault 左下角显示 "canvas-vault"（不是 _bmad-output）
- [ ] Claudian 已启用（Settings > Community plugins 开关打开）
- [ ] Claudian Settings 里 "Claude CLI Path" 填了 `/Users/Heishing/.local/bin/claude`
- [ ] Settings > Hotkeys 搜 "AI 创建双链文档" 给它绑 `Cmd+Shift+D`（**看到绑定显示 `⌘⇧D` 才算成功**）
- [ ] **测试文件必须在正确路径**：在 `canvas-vault/wiki/canvases/math240/` 下建一个 `Fundamentals.md`（frontmatter `subject: math240`，body 写一段 "Eigenvalues are special vectors that satisfy Av = λv"）—— 不能用 vault 根的"未命名.md"（v2 就是被这个坑了）
- [ ] `wiki/canvases/math240/index.md` **可以不存在**（下方验证 auto-create）

### 第 1 步：验证第 8 命令注册

- [ ] Cmd+Shift+P 打开命令面板 → 搜 "AI 创建双链文档"
- [ ] 看到命令 `Canvas Learning System: AI 创建双链文档` 出现在列表

### 第 2 步：验证 Skill 文件存在

- [ ] Finder 打开 `/Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/.claude/skills/ai-linked-doc/`
- [ ] 看到文件 `SKILL.md`（或者按 Cmd+Shift+. 显示隐藏文件夹再看）
- [ ] 文件首行是 `---`（frontmatter 起始）

### 第 3 步：空选中提醒

- [ ] 在 Obsidian 里打开任意笔记，不选任何文字
- [ ] 按 `Cmd+Shift+D`
- [ ] 弹 Notice "请先选中文本再创建双链"（3 秒）
- [ ] **不**触发剪贴板/Claudian 切换

### 第 4 步：选中文本 + 触发

- [ ] 打开 `wiki/canvases/math240/Fundamentals.md`
- [ ] 选中 `Eigenvalues are special vectors that satisfy Av = λv` 这段
- [ ] 按 `Cmd+Shift+D`

### 第 5 步：验证 Notice + Claudian 自动打开

- [ ] 弹 Notice "已复制到剪贴板，切到 Claudian 粘贴即可触发"（5 秒）
- [ ] Claudian 侧栏自动出现在右侧（如果已经开着，保持激活）

### 第 6 步：粘贴 prompt

- [x] 点击 Claudian 输入框获取焦点
- [x] `Cmd+V` 粘贴 → 应该看到：
  ```
  /ai-linked-doc
  选中文本:
  Eigenvalues are special vectors that satisfy Av = λv

  源笔记路径: wiki/canvases/math240/Fundamentals.md
  学科: math240

  请为这段内容创建一个概念文档（三段式：## 核心概念 / ## 关键点 / ## 关联概念）。
  ```
- [x] 按 Enter 提交

### 第 7 步：等 Skill 执行（10-30 秒）

- [x] Claudian 开始 "Thinking..." 或类似指示
- [x] 看到 Claude 在工作：解析输入 → 生成文档 → 写文件 → 替换 → 更新 index.md

### 第 8 步：验证最终摘要

- [ ] Claudian 输出**最后 3 行**类似： **User：最后这 3 行没看到，感觉成为了类似的幻觉**
  ```
  ✓ Eigenvalues.md 已创建 (wiki/canvases/math240/)
  ✓ 源笔记 [[Fundamentals]] 已替换为 [[Eigenvalues]]
  ✓ index.md (math240) 已更新 (doc_count → 1)
  ```

### 第 9 步：验证新文件

- [ ] Obsidian 左侧文件树展开 `wiki/canvases/math240/`
- [ ] 看到新文件 `Eigenvalues.md`
- [ ] 打开它，看到：
  - frontmatter 含 `type: concept` / `subject: math240` / `mastery_score: 0.30` / `created_from: ai_linked_doc`
  - `# Eigenvalues` 标题
  - `## 核心概念` 一段（1-2 句定义）
  - `## 关键点` 3-5 个 bullet
  - `## 关联概念` 含 `- [[Fundamentals]] — extracted from this note`
**User：创建了不存在的双向链接，生成文档自以为是偏离主题没有原文，然后也没有返回从哪一个拉出来的双向链接**
### 第 10 步：验证源笔记替换

- [ ] 切回源笔记 `Fundamentals.md` tab
- [ ] 原本选中的 `Eigenvalues are special vectors that satisfy Av = λv` 这段 → 已经变成 `[[Eigenvalues]]`
- [ ] 点击 `[[Eigenvalues]]` → 跳转到新文件（双链工作）
**User：没有双链**
### 第 11 步：验证 index.md（auto-create 或更新）
**User：文档不存在**

- [ ] 打开 `wiki/canvases/math240/index.md`
- [ ] frontmatter 含 `doc_count: 1`（若第 0 步前 index.md 就存在则 +1）
- [ ] body `## Concepts` 段有 `- [[Eigenvalues]] — extracted, weak (0.30)`
- [ ] 若 index.md 之前不存在 → 还看到 `## Recent Activity` 段 + 时间戳行

### 第 12 步：测试中文选中

- [ ] 在另一个笔记（或新建一个 frontmatter `subject: cs61b` 的笔记）里写一段中文
- [ ] 例如 "递归是函数调用自身以解决规模更小的相同问题"
- [ ] 选中 → `Cmd+Shift+D` → Claudian 粘贴 → Enter
- [ ] 验证生成的新文件**全部用中文**（`## 核心概念` 内容、`## 关键点` bullet 全中文）

### 第 13 步：测试 index.md auto-create

- [ ] 先手动删除 `wiki/canvases/math240/index.md`（或者第 0 步干脆不建）
- [ ] 重复第 4-8 步做一次新概念提取
- [ ] 验证 `wiki/canvases/math240/index.md` 自动被创建，含完整骨架

### 第 14 步：边界 — Claudian 未装

- [ ] Settings > Community plugins → 临时关闭 Claudian
- [ ] 按 `Cmd+Shift+D`
- [ ] 弹 Notice "未检测到 Claudian 插件，请先安装并登录 Claude Code"（5 秒）
- [ ] Obsidian **不崩溃**，console (F12) 无 JS error
- [ ] 重新打开 Claudian 恢复

---

## 🚦 验收结果

**如果所有步骤 ✅**：告诉我 "**Story 1.17 通过**"，我把它 mark as **done**，启动下一个 Story（1.18 Dashboard MVP 或 1.19 原白板配置 Skill）。

**如果有任何一步 ❌**：在下面批注区写清楚哪一步 + 看到的实际现象（截图或文字），我根据反馈 `bmad-bmm-correct-course` 调整。

---

## 📝 你的批注区

> [!question]+ 你对 Story 1.17 v2 的批注
>
> 在这里写任何疑问/建议/不满意。或者直接用 `Cmd+Shift+A` 批注上面任何一段。
>
> （空）

### 已知的已批注问题（历史追溯）

> [!error]+ 2026-04-19 — v1 架构偏离（双重付费）
> **你的原批注**："我们不是可以直接使用 claude code 的订阅额度吗"
>
> **根因**：Story 1.17 spec v1 方案让 Obsidian plugin 直调 Anthropic API，让你配独立 API key，违反了项目早就锁定的架构决策（`architecture.md:113` Mode D = Claude Code CLI 订阅额度）。根因和 Story 1.16 一样：审计报告在 scope 传递中丢失了架构约束。
>
> **已修复**：v2 改成形态 β —— Plugin 只做剪贴板 + 切 Claudian 侧栏，所有 AI 调用 / 文件操作都搬到 Claudian Skill 侧。你的订阅额度够用，零额外付费。

> [!error]+ 2026-04-19 — 双 Vault 错配（插件装错了地方）
> **你的原批注**："我测试不是在 canvas vault 上吗？开发相关的文档在 bmad output，然后测试相关的内容在 canvas vault"
>
> **根因**：我错把插件和 Claudian 规划到 _bmad-output（文档 vault），应该在 canvas-vault（测试 vault）。
>
> **已修复**：插件 main.js / Claudian / Skills 全部规范在 canvas-vault；_bmad-output 只放验收单 + spec + 开发文档。CLAUDE.md 已固化"双 Vault 架构"规则（round-7）。

### v2 → v2.1 你将看到的变化

| 维度 | v2（失败原因） | v2.1（修复） |
|---|---|---|
| Plugin prompt 强制力 | 只说"请为这段内容创建概念文档" | **加 `Please invoke the Skill tool with skill_name="ai-linked-doc"` + `Do NOT answer freely` 显式指令** |
| SKILL.md description | 描述"做什么"（生成文档、写路径...） | **改为描述"何时调用"（当消息以 /ai-linked-doc 开头时必须调用）** |
| Skill 硬约束 | 无明确防幻觉指令 → Claudian 自由发挥 | **开头 7 条 CRITICAL TRIGGER 硬约束 + Step 4 硬验证 + 末尾 6 项执行自检清单** |
| 路径保护 | Plugin 无检查 → 源文件在 vault 根也能触发 | **Plugin 预警 Notice + Skill Step 1 降级 AskUserQuestion** |
| 捏造 wikilink | Claudian 自由列 `[[其他相关概念]]` | **硬约束：关联概念只能列源笔记 stem，禁止列未确认存在的概念** |
| Notice 时长 | 3-5 秒 | **5-8 秒**，文案加长指引 |
| 控制台诊断 | 无 | `console.log("[canvas:ai-linked-doc] triggered")` 供 F12 Console 验证 |
| 构建大小 | 10571 bytes | **11608 bytes** (+1037B 强化) |

### v1 → v2 历史变化（存档参考）

| 维度 | v1（已淘汰） | v2 |
|---|---|---|
| AI 调用方式 | Obsidian plugin 直调 Anthropic API | Claudian Skill 走 Claude Code 订阅 |
| API key 配置 | 用户在 Settings 填独立 API key | 无需配置 |
| index.md 缺失 | 硬报错 | auto-create |
| 估时 | 10h | 6h |

---

## 🔗 技术 spec 参考（给 Claude 读的，不是给你读的）

- **Story spec**：`_bmad-output/implementation-artifacts/epic-1/1-17-ai-linked-doc.md`（v2 2026-04-19 重写）
- **Plugin 源代码**：
  - `frontend/obsidian-plugin/src/ai-linked-doc.ts`（pure function `buildAIDocPrompt`）
  - `frontend/obsidian-plugin/src/main.ts`（第 8 命令 + `handleAILinkedDoc`）
- **Skill 源代码**：`canvas-vault/.claude/skills/ai-linked-doc/SKILL.md`
- **单元测试**：`frontend/obsidian-plugin/tests/ai-linked-doc.test.ts`（4 用例，13/13 total pass）
- **架构锚定**：`planning-artifacts/architecture.md:113` Mode D（Claude Code CLI 订阅）
- **Round 3 QA System Prompt 模板来源**：`research/obsidian-qa-round3-claude-answers-2026-04-14.md:141-177`
- **AC 10 条 → 代码对应**：
  - AC #1-4（Plugin 侧）→ `src/main.ts:handleAILinkedDoc`
  - AC #5-10（Skill 侧）→ `canvas-vault/.claude/skills/ai-linked-doc/SKILL.md` Step 1-7

---

## 📅 下一步（你批完这份单后）

1. **全部 ✅** → 说 "Story 1.17 通过" → 我立即 mark done → 启动 Story 1.18（Dashboard MVP）或 Story 1.19（原白板配置 Skill），你选
2. **部分 ❌** → 在批注区写清楚 → 我跑 `bmad-bmm-correct-course` 再修
3. **想中间看 Skill 跑的日志** → 在 Claudian 侧栏展开 "Thinking" 详情看每一步工具调用
