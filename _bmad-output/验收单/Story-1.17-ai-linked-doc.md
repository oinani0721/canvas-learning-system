---
story: "1.17"
title: "AI 双链文档（形态 β：Plugin + Claudian Skill）"
status: "review"
version: "v2.1"
date: "2026-04-20"
developer: "Claude Code (Opus 4.7)"
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
---

# Story 1.17 验收单 v2.1（重新设计的完整验收流程）

> [!info]+ 这份文档为什么被重写
> 你的 v2 UAT 批注指出了 4 个核心问题（Cmd+Shift+D 像纯 copy / 3 行 ✓ 没看到 / 捏造双向链接 / 没更新 index.md）。3 个并行 Agent 深度调研发现根因是：
> 1. **Claudian plugin 本身从不路由 Skill**（Claudian main.js:60410 直送 prompt 给 Claude Agent SDK，Skill 调用权 100% 在 Claude 模型侧）
> 2. 原 SKILL.md 描述的是"做什么"不是"何时调用" → 模型自由发挥
> 3. 用户测试源文件在 vault 根（未命名.md），不在 canvases/ 路径
> 
> v2.1 已修复（+1037B 强化，commit `67faa9d`）。本验收单重新设计了从 0 开始的完整流程 + 失败时的诊断矩阵。

---

## 🎯 你要做什么（一句话）

跑完下面的 **12 步 UAT**，验证"选中文本 → Cmd+Shift+D → Claudian 自动生成概念笔记 + 自动替换成 [[双链]] + 自动更新 index.md"整条链路在 v2.1 下能稳定走通。

---

## 📖 正确流程长什么样（看懂了再动手）

```
┌─────────────────────────────────────────────────────────────────┐
│ 阶段 1 · Plugin 侧（Obsidian 插件做的，约 0.5 秒）              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 1. 你在 wiki/canvases/math240/Fundamentals.md 里选中一段文字    │
│    例："Eigenvalues are special vectors that satisfy Av = λv" │
│                                                                 │
│ 2. 按 Cmd+Shift+D（你事先在 Hotkeys 绑定的）                    │
│                                                                 │
│ 3. Plugin 做 4 件事（**全自动，你看不到中间过程**）：           │
│    a. 检查编辑器激活（光标必须在 markdown 正文里）              │
│    b. 检查有选中文本                                            │
│    c. 读当前文件 frontmatter 的 subject 字段                    │
│    d. 把下面这段包装好的 prompt 写入剪贴板（不只是选中文本！）  │
│       ┌────────────────────────────────────┐                   │
│       │ /ai-linked-doc                      │ ← 首行 slash 命令 │
│       │ Please invoke the Skill tool...    │ ← 强制 Skill 调用 │
│       │ Do NOT answer freely               │ ← 防自由发挥      │
│       │                                     │                   │
│       │ 选中文本:                           │                   │
│       │ Eigenvalues are special...         │                   │
│       │                                     │                   │
│       │ 源笔记路径: wiki/canvases/...      │                   │
│       │ 学科: math240                       │                   │
│       │                                     │                   │
│       │ 请为这段内容创建一个概念文档...    │                   │
│       └────────────────────────────────────┘                   │
│    e. 右下角弹 Notice（8 秒）："已复制到剪贴板..."              │
│    f. 自动打开 Claudian sidebar                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 阶段 2 · 你手动操作（约 2 秒）                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 4. 点 Claudian 输入框（让光标进去）                             │
│ 5. Cmd+V 粘贴（你会看到整段 /ai-linked-doc 开头的 prompt）     │
│ 6. 按 Enter 发送                                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 阶段 3 · Claudian Skill 自动执行（约 15-45 秒）                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 7. Claude 识别 /ai-linked-doc 前缀 + Skill 调用指令             │
│    → 加载 canvas-vault/.claude/skills/ai-linked-doc/SKILL.md   │
│    → 按 Skill 的 CRITICAL TRIGGER & HARD CONSTRAINTS 执行      │
│                                                                 │
│ 8. Skill 按 Step 1-7 自动跑：                                  │
│    Step 1: 解析输入（选中文本 + 源笔记 + 学科）                 │
│    Step 2: 生成 markdown（三段式：核心概念 / 关键点 / 关联概念）│
│    Step 3: 提取主概念名（如 "Eigenvalues"）                     │
│    Step 4: 写 wiki/canvases/math240/Eigenvalues.md              │
│            ⛔ 硬验证：路径必须以 wiki/canvases/ 开头            │
│    Step 5: Edit 源笔记，把选中文本替换为 [[Eigenvalues]]        │
│    Step 6: 更新或 auto-create wiki/canvases/math240/index.md    │
│    Step 7: 返回 3 行 ✓ 摘要                                    │
│                                                                 │
│ 9. Claudian sidebar 最后显示：                                  │
│    ✓ Eigenvalues.md 已创建 (wiki/canvases/math240/)             │
│    ✓ 源笔记 [[Fundamentals]] 已替换为 [[Eigenvalues]]           │
│    ✓ index.md (math240) 已更新 (doc_count → 1)                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 阶段 4 · 你验证结果（约 30 秒）                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 10. 切回源笔记 Fundamentals.md → 看到原本选中文本变 [[...]]    │
│ 11. 点击 [[Eigenvalues]] → 跳转到新概念笔记                     │
│ 12. 打开 index.md → 看到 doc_count +1 + Concepts 段新条         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 前置条件（必须全部满足后才能开始 UAT）

### P1 · 部署完整性（我已做完，你只需验证）

| 项 | 验证方法 | 预期 |
|---|---|---|
| Plugin main.js v2.1 已部署 | 终端 `wc -c canvas-vault/.obsidian/plugins/canvas-learning-system/main.js` | **11608** |
| Skill 文件已部署 | 终端 `ls canvas-vault/.claude/skills/ai-linked-doc/SKILL.md` | 存在 |
| Claudian v2.0.2 已装 | Obsidian Settings > Community plugins | 启用状态 |
| Claude CLI 可用 | 终端 `which claude && claude --version` | `/Users/Heishing/.local/bin/claude` + v2.1.114 |

### P2 · 强制 Reload Obsidian（关键！）

**v2 失败很可能就是因为旧插件实例还在内存**。Cmd+Q 有时不够（窗口复用）。必须：

- [ ] **在 Obsidian 里按 `Cmd+P`** 打开命令面板
- [ ] 输入 `reload`
- [ ] 选 **"Reload app without saving"** → 回车
- [ ] 窗口短暂刷新 → 所有插件强制重新加载内存

### P3 · 准备测试文件（必须在正确路径）

- [ ] 在 Obsidian 左边文件树 `wiki/canvases/` 下建新文件夹 `math240`（如果没有）
- [ ] 在 `wiki/canvases/math240/` 下建文件 `Fundamentals.md`
- [ ] 文件内容粘贴以下（**完整**，**不能缺 frontmatter**）：

```markdown
---
subject: math240
type: concept
---

# Linear Algebra Fundamentals

Eigenvalues are special vectors that satisfy Av = λv, where A is a square matrix, v is the eigenvector, and λ is the eigenvalue.

An eigenvalue of a linear transformation represents a scaling factor for its corresponding eigenvector.

Determinants help us find eigenvalues by solving det(A - λI) = 0.
```

⛔ **不要用 vault 根的 `未命名.md`** — v2 你就是踩这个坑被 Claude 自由发挥坑了。

### P4 · 确认 Hotkey 绑定

- [ ] Settings > Hotkeys → 搜 "AI 创建双链文档"
- [ ] 看到右边显示 `⌘⇧D`
- [ ] 如果未绑定 → 点 `+` 按 Cmd+Shift+D

---

## ✅ 12 步 UAT（按顺序跑，每步勾掉 `- [ ]`）

### 第 1 步：F12 打开 DevTools Console（用于诊断）

- [ ] 在 Obsidian 里按 `Cmd+Opt+I`（或菜单 Help > Toggle Developer Tools）
- [ ] 切到 **Console** 标签页
- [ ] 清屏（垃圾桶图标）
- [ ] 保持 DevTools 打开（可以拖一边让 Obsidian 主窗口仍可见）

### 第 2 步：打开源笔记 + 点击正文让光标进入

- [ ] 打开 `wiki/canvases/math240/Fundamentals.md`
- [ ] **顶部 tab 必须显示铅笔图标**（Edit view，不是书本图标 Reading view）
- [ ] 点击 body 任意位置让光标进入正文（看到光标闪）

### 第 3 步：空选中测试（Plugin 防护）

- [ ] 不选中任何文字（光标空置）
- [ ] 按 `Cmd+Shift+D`
- [ ] **Console 应看到** `[canvas:ai-linked-doc] triggered`
- [ ] 右下角 Notice："请先选中文本再创建双链"（3 秒）
- [ ] Claudian sidebar **不**自动打开

**如果没看到 Console 日志** → Plugin 命令没触发，转下方"🔴 诊断 A"

### 第 4 步：选中目标文本

- [ ] 用鼠标或 Shift+Arrow 选中文字：
  ```
  Eigenvalues are special vectors that satisfy Av = λv
  ```
- [ ] 选中高亮（蓝底白字）显示

### 第 5 步：按 Cmd+Shift+D 触发

- [ ] 按 `Cmd+Shift+D`
- [ ] **Console 必看到** `[canvas:ai-linked-doc] triggered`
- [ ] 右下角 Notice（**8 秒**）："已复制到剪贴板。切到 Claudian 侧栏 → 输入框 Cmd+V 粘贴 → 回车。首行是 /ai-linked-doc 会触发 Skill。"
- [ ] Claudian sidebar 自动激活（如果没打开会打开；已打开会保持前台）

**如果 Console 没日志 + 没 Notice** → 转 "🔴 诊断 A"  
**如果有 Console 日志但 Notice 是"编辑器未激活"** → 转 "🔴 诊断 B"  
**如果 Notice 是"当前笔记 XXX 不在原白板路径下"** → 你的测试文件路径不对，按 P3 重建

### 第 6 步：粘贴到 Claudian 输入框

- [ ] 点击 Claudian 输入框让光标进入
- [ ] `Cmd+V` 粘贴
- [ ] 输入框**首行**必须显示 `/ai-linked-doc`（这是关键！）
- [ ] 第二行是 `Please invoke the Skill tool with skill_name="ai-linked-doc"...`
- [ ] 后面是 `选中文本: / 源笔记路径: / 学科:` 三字段

**如果粘贴出来不是上述格式** → 说明 plugin 剪贴板写入没成功，转 "🔴 诊断 A"

### 第 7 步：发送 prompt

- [ ] 按 `Enter`
- [ ] Claudian 开始显示 "Thinking..." 或类似指示
- [ ] 你应该看到 Claude 在**按顺序调用工具**（Glob / Read / Write / Edit），约 15-45 秒

**关键观察**：
- ✅ **正确行为**：Claude 直接开始调 Glob 或 Write，不先说"我来为你创建..."
- ❌ **错误行为**：Claude 先解释一大段"好的，我来帮你创建..."然后才动手 → Skill 没走，转 "🔴 诊断 C"

### 第 8 步：验证最终摘要（最关键！）

- [ ] Claudian 最后输出**必须是 3 行 ✓**（可能含中英混排，但结构必对）：
  ```
  ✓ Eigenvalues.md 已创建 (wiki/canvases/math240/)
  ✓ 源笔记 [[Fundamentals]] 已替换为 [[Eigenvalues]]
  ✓ index.md (math240) 已更新 (doc_count → 1)
  ```
- [ ] 或部分失败时，含 `✓` / `✗` / `⚠` 组合（Step 7 Skill 规范）

**如果没有 3 行 ✓ 结构** → Skill 自检失败或没完整跑，转 "🔴 诊断 C"

### 第 9 步：验证新概念文件

- [ ] Obsidian 左边文件树展开 `wiki/canvases/math240/`
- [ ] 看到**新文件** `Eigenvalues.md`
- [ ] **路径必须是 wiki/canvases/math240/，不能是 wiki/concepts/**
- [ ] 打开它，内容满足：
  - frontmatter 含 `type: concept` / `subject: math240` / `mastery_score: 0.30` / `source_note: "[[Fundamentals]]"` / `created_from: ai_linked_doc`
  - `# Eigenvalues` 标题
  - `## 核心概念` 1-2 句英文定义（v2 中文原文，这里也应该是英文因为选中文本是英文）
  - `## 关键点` 3-5 个 bullet
  - `## 关联概念` **只列 `- [[Fundamentals]] — extracted from this note`**（不能列捏造的其他概念）

**如果路径是 wiki/concepts/** → Skill 没走，转 "🔴 诊断 C"  
**如果 `## 关联概念` 列了一堆不存在的 `[[XXX]]`** → Skill 硬约束没生效，转 "🔴 诊断 C"

### 第 10 步：验证源笔记 wikilink 替换

- [ ] 切回 `Fundamentals.md` tab
- [ ] 原本选中的 `Eigenvalues are special vectors that satisfy Av = λv` → **已经变成 `[[Eigenvalues]]`**
- [ ] 点击 `[[Eigenvalues]]` → 跳转到新文件（双链工作）

**如果源笔记没被替换** → Skill Step 5 失败，可能 Step 8 摘要里有 `✗ 源笔记替换失败`

### 第 11 步：验证 index.md（auto-create）

- [ ] 左边文件树刷新（右键文件夹 > Refresh）
- [ ] 看到新文件 `wiki/canvases/math240/index.md`（P3 没建则是 auto-create 的）
- [ ] 打开它，内容满足：
  - frontmatter 含 `type: board_index` / `subject: math240` / `doc_count: 1`
  - body `## Concepts` 段有 `- [[Eigenvalues]] — extracted, weak (0.30)`
  - body `## Recent Activity` 段有时间戳

### 第 12 步：中文测试（可选但推荐）

- [ ] 新建 `wiki/canvases/cs61b/Recursion.md`（frontmatter `subject: cs61b`）
- [ ] 写一段中文：`递归是函数调用自身以解决规模更小的相同问题`
- [ ] 选中这句 → `Cmd+Shift+D` → Claudian 粘贴 → Enter
- [ ] 验证生成的 `wiki/canvases/cs61b/递归.md`（或类似中文概念名）**全部用中文**

---

## 🔴 诊断矩阵（某步失败时对号入座）

### 🔴 诊断 A — Cmd+Shift+D 没反应 / Console 没日志

1. 终端跑 `ps -eo pid,lstart,comm | grep -i obsidian`（查 Obsidian 进程启动时间）
2. 终端跑 `stat -f "%Sm" canvas-vault/.obsidian/plugins/canvas-learning-system/main.js`（查 main.js 修改时间）
3. 如果 Obsidian 启动时间 < main.js 修改时间 → **Reload 没生效** → 再次 Cmd+P → "Reload app without saving"
4. 仍无反应 → Cmd+Shift+P → 搜 "AI 创建双链文档" → 看命令是否在列表（如果不在 → plugin 根本没装 v2.1，复 deploy）
5. 命令在但按 hotkey 不触发 → Settings > Hotkeys 检查 Cmd+Shift+D 是否绑到其他命令

**绕过 hotkey 手动触发**（验证 handler 本身）：
```javascript
// 在 Obsidian DevTools Console 里跑：
app.commands.executeCommandById("canvas-learning-system:canvas:ai-linked-doc")
```
这应该直接触发 handler，看 Notice 行为。

### 🔴 诊断 B — Notice 显示"编辑器未激活"

1. 你的光标没在 Markdown 编辑器正文里
2. 确认 tab 是铅笔图标（Edit view），不是书本（Reading view）
3. 点击 body 文字让光标进入
4. 确认不是在 Claudian sidebar / 文件树 / 标签栏上按 hotkey

### 🔴 诊断 C — Claudian 自由发挥（没走 Skill）

表现：回复像自由对话、无 3 行 ✓、写到 wiki/concepts/、捏造 wikilink

1. **先验证剪贴板格式**：按完 Cmd+Shift+D 后，在任意编辑器 Cmd+V，看是否首行 `/ai-linked-doc` + 显式 Skill 调用指令。如果缺 → plugin 没跑对，转诊断 A。
2. **Skill 文件验证**：
   ```bash
   head -15 /Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/.claude/skills/ai-linked-doc/SKILL.md
   ```
   - 首行必须是 `---`
   - `name: ai-linked-doc`
   - `description: "当用户消息以 /ai-linked-doc 开头..."` 必须存在
3. **手动触发 Skill（绕过 plugin）**：
   - 直接在 Claudian 输入框打 `/ai-linked-doc` + 粘贴完整 prompt
   - 观察 Claude 第一反应：如果先解释再动手 → SKILL.md 没被加载
   - 如果直接调 Glob/Read/Write → Skill 在跑
4. **检查 CLAUDE.md 读取**：
   - 在 Claudian 里单独问："你现在是否加载了 ai-linked-doc skill？"
   - Claude 应该说"是的，我加载了..."（如果说"没有"或模糊 → description 没匹配上）
5. **降级方案**：如果多次试都是自由发挥，可以直接在 Claudian 输入：
   ```
   请调用 Skill 工具，skill_name=ai-linked-doc，按照 SKILL.md 的 6 步流程处理以下输入：
   [粘贴 plugin 生成的 prompt]
   ```
   这个显式指令几乎总能强制 Claude 调 Skill 工具。

### 🔴 诊断 D — 非 canvases 路径预警

Notice: "当前笔记 xxx 不在原白板路径下"

- 这是 v2.1 新加的保护机制。你的测试文件不在 `wiki/canvases/<subject>/` 下
- 解决：按 P3 把文件放到正确路径
- 或：继续推进，Skill 的 Step 1 会 AskUserQuestion 让你选 subject

---

## 🚦 验收结果

### 理想情况（全 12 步 ✅）
→ 告诉我 "**Story 1.17 通过**"  
→ 我 mark done + 启动下一个 Story（1.18 Dashboard MVP 或 1.19 原白板配置 Skill，你选）

### 部分失败（哪步 ❌ 告诉我哪个诊断）
→ 告诉我 "**诊断 [A/B/C/D]**" + 截图  
→ 我针对性 correct-course 到 v2.2

### 完全不通（Claudian 根本不识别 Skill）
→ 考虑方案 C（Plugin subprocess spawn claude CLI，完全绕开 Claudian）  
→ 这是 3 agent 调研的备选方案，工作量 ~8h

---

## 📝 你的批注区

> [!question]+ 你对 Story 1.17 v2.1 的批注
>
> 在这里写任何疑问/建议/不满意。或者直接用 `Cmd+Shift+A` 批注上面任何一段。
>
> （空）

### 已知的已批注问题（历史追溯）

> [!error]+ 2026-04-20 — v2 → v2.1 critical correct-course
> **你的原批注**：
> 1. "Cmd+Shift+D 和 Cmd+Shift+V 有什么区别吗？Cmd+Shift+D 我是使用后也没有自动把文字复制到剪贴板，然后后续的操作也都没有触发"
> 2. "最后这 3 行没看到，感觉成为了类似的幻觉"
> 3. "创建了不存在的双向链接，生成文档自以为是偏离主题没有原文"
> 4. "没有双链 / index.md 文档不存在"
>
> **根因（3 并行 Agent 调研）**：
> - Claudian plugin **本身从不路由 Skill**（main.js:60410 直送 prompt 给 Claude Agent SDK）
> - SKILL.md description 写"做什么"而非"何时调用" → Claude 自由发挥
> - 测试文件在 vault 根（未命名.md），非 canvases/ 路径
>
> **已修复**：
> - Plugin prompt 加 `Please invoke the Skill tool` 显式指令
> - SKILL.md description 改为触发条件
> - SKILL.md 开头 7 条 CRITICAL TRIGGER 硬约束 + Step 4 硬验证 + 末尾 6 项自检清单
> - Plugin 加 `console.log` 诊断 + Notice 文案强化 + 非 canvases 路径预警
> - 5 用例测试（+isCanvasesPath）14/14 green
> - build 11608B（+1037B）

> [!error]+ 2026-04-19 — v1 架构偏离（双重付费）
> **你的原批注**："我们不是可以直接使用 claude code 的订阅额度吗"
> **根因**：v1 plugin 直调 Anthropic API 违反 architecture.md:113 Mode D
> **已修复**：v2 改成形态 β Plugin + Claudian Skill，零额外付费

> [!error]+ 2026-04-19 — 双 Vault 错配
> **你的原批注**："我测试不是在 canvas vault 上吗？开发相关的文档在 bmad output，然后测试相关的内容在 canvas vault"
> **已修复**：插件/Claudian/Skills 全部规范在 canvas-vault；_bmad-output 只放文档

---

## 🔗 技术 spec 参考（给 Claude 读的）

- **Story spec**：`_bmad-output/implementation-artifacts/epic-1/1-17-ai-linked-doc.md`（v2.1 2026-04-20）
- **Plugin 源代码**：
  - `frontend/obsidian-plugin/src/ai-linked-doc.ts`（pure function + isCanvasesPath）
  - `frontend/obsidian-plugin/src/main.ts`（第 8 命令 + handleAILinkedDoc）
- **Skill 源代码**：`canvas-vault/.claude/skills/ai-linked-doc/SKILL.md`（v2.1 含 7 条硬约束 + 6 项自检清单）
- **单元测试**：`frontend/obsidian-plugin/tests/ai-linked-doc.test.ts`（5 用例，14/14 total pass）
- **架构锚定**：`planning-artifacts/architecture.md:113` Mode D（Claude Code CLI 订阅）
- **Commit history**：
  - `486dcf2`：v2 实施
  - `67faa9d`：v2.1 correct-course

---

## 📅 你的下一步

1. **按 P1-P4 前置清单跑一遍**（约 5 分钟）
2. **按 12 步 UAT 依次跑**（约 10 分钟，含 Claude 执行等待时间）
3. **反馈**：
   - 全 ✅ → "Story 1.17 通过"
   - 部分 ❌ → "诊断 [A/B/C/D]" + 截图
   - 完全不通 → 讨论方案 C（plugin subprocess 绕开 Claudian）
