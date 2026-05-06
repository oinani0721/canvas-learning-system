---
story: "1.17"
title: "AI 双链文档（形态 β：Plugin + Claudian Skill）"
status: "review"
unblocked_by: "1.19 v4 UAT 通过 (2026-04-30)"
version: "v3.0"
date: "2026-04-30"
developer: "Claude Code (Opus 4.7)"
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
d4_decisions: "v3.0 Hybrid (plugin 脚本 <100ms 建骨架 + Skill v5.0 异步填正文); 含 v2.2 + v2.4 + v2.5 + v2.6 行为"
---

# Story 1.17 验收单 v3.0 — ✅ Hybrid 架构落地（plugin 立即建骨架 + Skill 异步填正文）

> [!tip]+ ✅ 2026-04-30 v3.0 已 ship — 请跑 v3.0 hybrid UAT（22 步 = v2.6 20 步 + v3 hybrid 2 步）
>
> **v3.0 颠覆性变化**：截图你看到的"Claudian 跑 15-45s 才看到节点"问题已根治。现在按 Cmd+Shift+D 后：
>
> ```
> 阶段 1（plugin 脚本，<100ms）：
>   ✓ 节点 md 立即建好（含 frontmatter + status: ai_pending + placeholder 正文）
>   ✓ 源笔记 wikilink + 关系 callout 立即替换
>   ✓ 白板 ## Concepts + ## Recent Activity 立即更新
>   ✓ 你**马上**看到 Notice "节点骨架已建好（阶段 1: XXms）"
>
> 阶段 2（Claudian Skill v5.0 异步，15-45s）：
>   ✓ 你不需要等！继续读源笔记或干别的
>   ✓ Claudian 后台跑：仅生成 3 段正文 + Edit 替换 placeholder + 改 status 为 ai_complete
>   ✓ 跑完后节点 md 自动从 placeholder 变成完整的概念笔记（你打开节点 md 即可看到）
> ```
>
> **架构对比**：
>
> | 维度 | v2.6 当前 | v3.0 hybrid |
> |---|---|---|
> | 看到新节点的延迟 | 15-45s 等 LLM | **<100ms** |
> | 你能继续读源笔记？ | 不能 | **能（异步）** |
> | LLM token 量 | ~2000-3000 | **~800-1200** |
> | Skill 失败时 | 整个流程崩 | 节点骨架保留 + 可重试 |
> | Mode D 合规 | ✅ | ✅ 仍走 Claudian/CLI 订阅额度 |
>
> **跑 UAT 之前**：在 obsidian Settings → Community plugins → 重启 canvas-learning-system 插件（让 main.js v3.0 生效，应 31768B）。

---

> [!info]+ v2.6 → v3.0 行为变化（本次重点测）
>
> **触发的命令变了**：剪贴板 prompt 首行从 `/ai-linked-doc` 改成 `/ai-linked-doc-fill`，触发新 Skill `ai-linked-doc-fill`（v5.0 极简版）
>
> **Skill 工作量变了**：
> - v2.6 Skill `ai-linked-doc`：8 步全 LLM 推理（Step 1-8 含 Glob 白板 / 读 yaml / AskUserQuestion / 派生 / 替换 / 更新白板）
> - v3.0 Skill `ai-linked-doc-fill`：仅 2 步（Read 节点 md → 生成 3 段 + Edit 替换 placeholder + 改 status）
>
> **节点 md 状态机**：
> - 阶段 1 完成：`status: ai_pending`，正文是 placeholder（含 ⏳ callout 提示用户 AI 还在跑）
> - 阶段 2 完成：`status: ai_complete`，正文是 3 段（## 核心概念 / ## 关键点 / ## 关联概念）
>
> **白板 ## Concepts 行**：阶段 1 写入 `- [[节点/X]] — refines, weak (0.30) ⏳ ai_pending`，阶段 2 不改这一行（保留 ⏳，因为 dataviewjs 用 frontmatter status 过滤显示）

---

> [!warning]+ ⛔ 旧 v2.6 UAT 步骤（v2.5 19 步）已不再适用 — 请用下方 v3.0 UAT
>
> 旧 UAT 假设你需要等 Claudian 跑完才看到节点；v3.0 后**阶段 1 立即可见**，UAT 重点变成"骨架立即生成 + 异步填充"。
>
> 旧 UAT 文档保留在文件下方供历史追溯，但**请优先跑下面 v3.0 UAT 22 步**。

---

## v3.0 UAT 22 步（最新主测）

### 前置（P1-P4 不变）
- 重启 obsidian + main.js 已是 31768B
- canvas-vault 至少有 1 个白板（如 `原白板/特征值与特征向量.md`）
- 至少有 1 个已派生节点（如 `节点/Characteristic-Equation-for-Eigenvalues.md`，v2.4 测过的）
- Cmd+Shift+D 已绑定 `canvas:ai-linked-doc`

### V3-1 至 V3-4 · Modal 链（与 v2.5 一致，确保兼容）
- [ ] V3-1：在 `节点/Characteristic-Equation-for-Eigenvalues.md`（已有 source_board）选一段文字
- [ ] V3-2：按 Cmd+Shift+D → 立即弹关系 modal（7 类）→ 选 `extends`
- [ ] V3-3：弹描述 modal → 输入"测试 v3 hybrid 流程的派生意图"→ Cmd+Enter
- [ ] V3-4：v2.6 节点继承 Notice 应该弹（"继承源节点白板归属：特征值与特征向量"）

### V3-5 · ⭐ 阶段 1 立即骨架（v3.0 核心新功能）
- [ ] modal 关闭后**立即**（<200ms）右下角弹绿色 Notice：
  ```
  ✓ 节点骨架已建好 [[节点/<新概念名>]]（阶段 1: XXms）。
  继续读源笔记，AI 后台填正文。
  ```
- [ ] **关键**：你**不需要等**，立刻可以做下面 V3-6 ~ V3-8 的验证

### V3-6 · ⭐ 阶段 1 节点 md 立即可见且含 placeholder
- [ ] 立即（不等 Claudian）打开新建的 `节点/<新概念名>.md`
- [ ] frontmatter 含完整字段：
  ```yaml
  type: concept
  mastery_score: 0.3
  source_note: "[[Characteristic-Equation-for-Eigenvalues]]"
  source_board: "[[原白板/特征值与特征向量]]"
  created_from: ai_linked_doc
  up: "[[Characteristic-Equation-for-Eigenvalues]]"
  derived-from: "[[Characteristic-Equation-for-Eigenvalues]]"
  status: ai_pending          ← v3.0 新字段
  relationships:
    - type: extends
      target: "[[Characteristic-Equation-for-Eigenvalues]]"
      description: "测试 v3 hybrid 流程的派生意图"
  ```
- [ ] 正文是 **placeholder**（不是 3 段正文）：
  ```markdown
  # <概念名>

  <!-- AI_BODY_PLACEHOLDER -->

  > [!info]+ ⏳ AI 正在生成正文
  > ...

  <!-- 选中文本（供 Skill 阶段 2 生成正文用） -->
  <!-- SELECTED_TEXT_START
  <你选的原文>
  SELECTED_TEXT_END -->
  ```

### V3-7 · ⭐ 阶段 1 源笔记立即更新
- [ ] 切回源笔记 `节点/Characteristic-Equation-for-Eigenvalues.md`
- [ ] 你刚才选中的文字已**立即**替换为 wikilink + 关系 callout（5 行，含派生意图）
- [ ] **不**需要等 Claudian

### V3-8 · ⭐ 阶段 1 白板立即更新
- [ ] 打开 `原白板/特征值与特征向量.md`
- [ ] `## Concepts` 末尾**立即**新增一行：`- [[节点/<新概念名>]] — extends, weak (0.30) ⏳ ai_pending`（含 ⏳ status 标记）
- [ ] `## Recent Activity` 末尾**立即**新增一行：`- <ISO>: Extracted [[节点/<新概念名>]] via /ai-linked-doc from [[Characteristic-Equation-for-Eigenvalues]]（关系: extends, status: ai_pending）`

### V3-9 · 阶段 2 触发 Claudian
- [ ] V3-5 Notice 后 plugin 自动切到 Claudian sidebar
- [ ] Claudian 输入框已**自动**粘贴 prompt（剪贴板）—— 你**不需要 Cmd+V**，直接看到内容
- [ ] 输入框首行是 `/ai-linked-doc-fill`（**不是** `/ai-linked-doc`）
- [ ] prompt 内容含：节点路径 / 概念名 / 关系类型 / 用户派生意图 / 选中文本

### V3-10 · 阶段 2 Skill v5.0 跑（验证 Skill 极简）
- [ ] 在 Claudian 输入框按 Cmd+V 粘贴（如 plugin 自动粘贴失败）+ Enter
- [ ] **关键**：Skill 应**只**调 2-3 个 tool：
  1. `Read 节点/<概念>.md`（读节点验证 placeholder 标记）
  2. `Edit 节点/<概念>.md`（替换 placeholder 为 3 段正文）
  3. `Edit 节点/<概念>.md`（改 status: ai_pending → ai_complete）
- [ ] **不应**调：Glob 原白板/、Read .canvas-config.yaml、AskUserQuestion、Write 白板 md、Edit 源笔记
- [ ] 总耗时应**比 v2.6 短**（v2.6 ~30s 含 8 步推理；v3 ~10-15s 仅生成 + Edit）

### V3-11 · 阶段 2 完成后节点 md 状态
- [ ] Claudian 跑完后打开 `节点/<新概念名>.md`
- [ ] frontmatter `status: ai_complete`（不再是 ai_pending）
- [ ] 正文是 3 段（不再是 placeholder）：
  ```markdown
  # <概念名>

  ## 核心概念
  （AI 生成的 1-2 句定义，应呼应你的派生意图"为了测试 v3 hybrid 流程"）

  ## 关键点
  - 要点 1
  - ...

  ## 关联概念
  - [[Characteristic-Equation-for-Eigenvalues]] — extracted from this note
  ```
- [ ] **不**含 AI_BODY_PLACEHOLDER 标记
- [ ] **不**含 SELECTED_TEXT_START/END 注释

### V3-12 · ⭐ 失败恢复（partial commit 哲学）

**测试 1：阶段 2 跑一半你关 Claudian**
- [ ] 在 Claudian 跑步骤时手动关 sidebar
- [ ] 节点 md 应保持 `status: ai_pending` + placeholder 正文
- [ ] **不**回滚阶段 1（节点 md / 源笔记 wikilink / 白板都保留）
- [ ] 你可以手动调 `/ai-linked-doc-fill <概念名>` 重跑（plugin 写剪贴板的 prompt 仍可粘贴）

**测试 2：节点 md 已被 Skill 跑过（再次触发 fill）**
- [ ] 对已 ai_complete 的节点再次手动调 `/ai-linked-doc-fill`
- [ ] Skill 应返回 `✗ 节点 md 不含 AI_BODY_PLACEHOLDER 标记，可能已被填过` → skip

### V3-13 至 V3-16 · 验证 v2.6 行为不破坏（回归）
- [ ] V3-13：在原白板 md 派生（不是节点）→ activeBoard 直接从路径取，不走继承
- [ ] V3-14：节点继承 source_board 仍工作（v2.6 验证）
- [ ] V3-15：关系类型 7 选 modal 仍工作
- [ ] V3-16：描述 modal 留空提交仍工作（描述行 `(用户留空)`）

### V3-17 至 V3-22 · 边界 + 性能
- [ ] V3-17：选中含 emoji / 特殊符号的文本 → stub 名清洗后仍能建文件
- [ ] V3-18：选中超长文本（500+ 字符）→ stub 截断到 40 字符
- [ ] V3-19：节点池已有同名 → 自动 `_2 / _3`
- [ ] V3-20：源笔记不在 `原白板/` 也不在 `节点/`（如 `wiki/canvases/...`）→ Notice 报错"未确定活动白板"，不建文件
- [ ] V3-21：原白板 md 不存在（用户删了）→ Notice 报错"请先 /configure-whiteboard"，不建文件
- [ ] V3-22：阶段 1 总耗时 < 200ms（看 V3-5 Notice 中的 XXms 数字）

### 全 22 步 ✅ → 告诉我 "**Story 1.17 v3.0 通过**"

---

## 旧 v2.6 UAT 文档（保留追溯，不需要跑）

> [!tip]+ ✅ 2026-04-30 v2.6 已 ship — 请跑 v2.6 UAT（20 步 = v2.5 19 步 + v2.6 节点继承 1 步）
> **截图 bug 已修**：之前你在节点 md 派生时 Skill 弹 AskUserQuestion 让你选白板（明明节点本身已有 source_board frontmatter），现在 plugin 自动读 frontmatter 继承。main.js 20348B 已 ship。
>
> **v2.6 新增功能**（你这次跑 UAT 时会感知）：
> - **节点派生节点自动继承白板归属**：
>   - 当源笔记是 `节点/<concept>.md`（已有 source_board frontmatter）→ Cmd+Shift+D 后 plugin 自动读取并继承
>   - 不再弹 AskUserQuestion 让你重选
>   - 弹 Notice `继承源节点白板归属：<board>（v2.6 自动）` (3s) 让你知道发生了什么
> - **不命中场景的 fallback**（保持原行为）：
>   - 源笔记**不是**节点（如 wiki/canvases/old/Foo.md / vault 根的未命名.md）→ Skill 走 .canvas-config.yaml 或 AskUserQuestion
>   - 节点 frontmatter 缺 source_board / 格式异常 → Skill 走 .canvas-config.yaml fallback（规则 2.5 双保险）
>
> **v2.5 已有功能保留**：派生描述 modal（textarea，可选）+ 三处落地（callout body + frontmatter + AI prompt）
> **v2.4 已有功能保留**：关系类型 modal（7 类）+ 双写
> **v2.2 已有功能保留**：D4-1 toast 不打断 + D4-2 toast + 重试按钮
>
> **跑 UAT 之前**：在 obsidian Settings → Community plugins → 重启 canvas-learning-system 插件（让 main.js v2.6 生效）。
>
> 历史"暂挂起"上下文（已解决）：

> [!error]+ ~~⛔⛔⛔ 本 UAT 暂时挂起 — 请先等 Story 1.19 完成~~ （✅ 2026-04-30 已解决）
> **2026-04-20 你的批注精准命中 bug**：
> 
> > "双链提问节点的功能本身就是要在原白板里面使用的。"
> > "我现在有一个在任意文件夹的 md 文件那么我想要从这个文件开始生成原白板，请问我该如何操作？"
> 
> **3 并行 Agent deep explore 结论**：
> - Story 1.19 (`configure-whiteboard` Skill) 的 YAML 早就写了 `blocks: ["1.17","1.18"]` — **数据层早就规定 1.19 要先做**
> - 但 Claude 此前在 CLAUDE.md line 145 按"工作量从小到大"排序成 `1.16→1.17→1.18→3.X`，违反 Story 1.19 blocks 声明
> - 用户实际使用链路：**第一件事是建白板（Story 1.19），之后才能在白板里用双链（Story 1.17）**
> - PRD Persona 旅程 4 明确："新同学**创建了第一个白板**，粘贴了课件内容"（prd-tauri-original-2ae5897.md:411）
> 
> **立即行动**（Claude 已执行）：
> 1. ✅ sprint-status 1.17 状态 `review → blocked`（blocked_by: 1.19）
> 2. ✅ sprint-status 1.19 状态 `ready-for-dev → in-progress`
> 3. ✅ CLAUDE.md 实施顺序修正为 `1.16 → 1.19 → 1.17 → 1.18`
> 4. ✅ Story 1.19 scope 扩展：v1 只有场景 A（从零建）→ v2 新增场景 B（从任意 md 派生），回应你的"我现在有一个任意文件夹的 md..."诉求
> 5. ⏳ 立即启动 Story 1.19 实施（~8h = 原 6h + 场景 B 扩展 2h）
> 
> **你现在要做的**：**不要**按下面 v2.1 UAT 测 1.17。等我 ship Story 1.19 的验收单，**先跑 1.19 的 UAT 建第一个原白板**，之后再回来跑 1.17 UAT（本文档仍保留，前置条件届时会成立）。
> 
> **1.17 代码本身不变**（v2.1 已 ship commit `67faa9d`），只是暂停测试 — 代码不丢，等待白板环境就绪。

---

## 📋 等 1.19 完成后，你会看到什么

1. 你打开 canvas-vault，看到一个随意位置的 md（如 `raw/my-notes.md` 或 vault 根的 `未命名.md`）
2. 在 Claudian 侧栏输 `/configure-whiteboard` → Skill 弹 AskUserQuestion 问你：
   - 种子笔记路径（可 `from <path>`，或直接用当前 active 笔记）
   - 学科代码（例 `math240`）+ 板名（例 `Linear Algebra`）
   - move 还是 copy（默认 move）
3. Skill 自动建 `wiki/canvases/math240/` + `index.md` + 把你的笔记迁入 + 更新 wikilink
4. 此时**第一个原白板诞生**。
5. 回到 1.17 UAT：打开迁入的笔记 → 选中文本 → `Cmd+Shift+D` → Claudian → Skill 派生新概念笔记到同一白板目录下

---

## 🔽 以下是原 v2.1 UAT 文档（等 1.19 done 后再跑）

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

| 项                       | 验证方法                                                                     | 预期                                             |
| ----------------------- | ------------------------------------------------------------------------ | ---------------------------------------------- |
| Plugin main.js v2.1 已部署 | 终端 `wc -c canvas-vault/.obsidian/plugins/canvas-learning-system/main.js` | **11608**                                      |
| Skill 文件已部署             | 终端 `ls canvas-vault/.claude/skills/ai-linked-doc/SKILL.md`               | 存在                                             |
| Claudian v2.0.2 已装      | Obsidian Settings > Community plugins                                    | 启用状态                                           |
| Claude CLI 可用           | 终端 `which claude && claude --version`                                    | `/Users/Heishing/.local/bin/claude` + v2.1.114 |

### P2 · 强制 Reload Obsidian（关键！）

**v2 失败很可能就是因为旧插件实例还在内存**。Cmd+Q 有时不够（窗口复用）。必须：

- [x] **在 Obsidian 里按 `Cmd+P`** 打开命令面板
- [x] 输入 `reload`
- [x] 选 **"Reload app without saving"** → 回车
- [x] 窗口短暂刷新 → 所有插件强制重新加载内存

### P3 · 准备测试文件（必须在正确路径）
**User：我现在有一个在任意文件夹的 md 文件那么我想要从这个文件开始生成原白板，请问我该如何操作？**

- [x] 在 Obsidian 左边文件树 `wiki/canvases/` 下建新文件夹 `math240`（如果没有）
- [x] 在 `wiki/canvases/math240/` 下建文件 `Fundamentals.md`
- [x] 文件内容粘贴以下（**完整**，**不能缺 frontmatter**）：

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

- [x] Settings > Hotkeys → 搜 "AI 创建双链文档"
- [x] 看到右边显示 `⌘⇧D`
- [x] 如果未绑定 → 点 `+` 按 Cmd+Shift+D

---

## ✅ 12 步 UAT（按顺序跑，每步勾掉 `- [ ]`）

### 第 1 步：F12 打开 DevTools Console（用于诊断）

- [x] 在 Obsidian 里按 `Cmd+Opt+I`（或菜单 Help > Toggle Developer Tools）
- [x] 切到 **Console** 标签页
- [x] 清屏（垃圾桶图标）
- [x] 保持 DevTools 打开（可以拖一边让 Obsidian 主窗口仍可见）

### 第 2 步：打开源笔记 + 点击正文让光标进入

- [x] 打开 `wiki/canvases/math240/Fundamentals.md`
- [x] **顶部 tab 必须显示铅笔图标**（Edit view，不是书本图标 Reading view）
- [x] 点击 body 任意位置让光标进入正文（看到光标闪）

### 第 3 步：空选中测试（Plugin 防护）

- [x] 不选中任何文字（光标空置）
- [x] 按 `Cmd+Shift+D`
- [x] **Console 应看到** `[canvas:ai-linked-doc] triggered`
- [x] 右下角 Notice："请先选中文本再创建双链"（3 秒）
- [x] Claudian sidebar **不**自动打开

**如果没看到 Console 日志** → Plugin 命令没触发，转下方"🔴 诊断 A"

### 第 4 步：选中目标文本

- [x] 用鼠标或 Shift+Arrow 选中文字：
  ```
  Eigenvalues are special vectors that satisfy Av = λv
  ```
- [x] 选中高亮（蓝底白字）显示![[截屏2026-04-30 上午3.14.32.png]]

### 第 5 步：按 Cmd+Shift+D 触发

- [ ] 按 `Cmd+Shift+D`
- [ ] **Console 必看到** `[canvas:ai-linked-doc] triggered`
- [ ] **v2.4 新行为**：屏幕中央**立即弹出 modal**（不再立即写剪贴板），placeholder："派生关系：新节点和当前源笔记是什么关系？(7 类，输入过滤)"

**如果 Console 没日志 + 没 modal** → 转 "🔴 诊断 A"  
**如果有 Console 日志但 Notice 是"编辑器未激活"** → 转 "🔴 诊断 B"  
**如果 Notice 是"当前笔记 XXX 不在原白板路径下"** → 你的测试文件路径不对，按 P3 重建（warning Notice 不阻止 modal 出现）

### 第 5.5 步：⭐ v2.4 新增 — 关系类型 modal（D1-2）

- [ ] modal 显示 **7 个选项**（顺序固定）：
  1. **先修 (prerequisite)** — 新节点是源笔记的先修知识
  2. **依赖 (depends_on)** — 新节点在概念上依赖源笔记
  3. **细化 (refines)** — 新节点是源笔记某段的更细化版本
  4. **扩展 (extends)** — 新节点在源笔记基础上延伸或补全
  5. **例子 (example_of)** — 新节点是源笔记某概念的具体例子
  6. **反驳 (contradicts)** — 新节点与源笔记观点矛盾或反驳
  7. **相关 (related_to)** — 一般性关联（兜底）
- [ ] 输入"细"过滤 → 只剩"细化 (refines)"
- [ ] 用键盘 ↓↓↓ 或鼠标点选一项（如选 `refines`）
- [ ] **v2.5 新行为**：选完关系类型后**不立即写剪贴板**，**继续弹 DescriptionModal**（见第 5.6 步）

**如果 modal 没弹出** → main.js 不是 v2.5 版本（应 19159B），重启 obsidian 让插件刷新；仍无 → 转"🔴 诊断 E"  
**如果按 Esc 取消 RelationTypeModal** → 应该 silent return，不写剪贴板 / 不开 Claudian / 没弹 description modal

### 第 5.6 步：⭐ v2.5 新增 — 派生描述 modal（D1-4 可选 + D1-5 三处落地）

关系 modal 选完后立即弹出第二个 modal：

- [ ] 标题: `派生描述（关系: refines）`（含你刚选的关系 key）
- [ ] 一句说明: `可选：用一句话描述「为什么把这个节点拉出来」。留空 / 按 Esc 跳过。`
- [ ] 一个 4 行 textarea，placeholder 示例: `例如：为了单独梳理特征方程的求解步骤，避免 Fundamentals 笔记过长。`
- [ ] 右下角两个按钮：「跳过 (Esc)」+「提交 (Cmd/Ctrl+Enter)」(蓝色 mod-cta)

**测试 3 条提交路径，3 选 1 跑**：

**路径 a · 写描述并提交**（推荐路径，验证三处落地）
- [ ] 在 textarea 输入 "为了单独梳理特征方程的求解步骤"
- [ ] 按 `Cmd+Enter` 或点「提交」按钮
- [ ] modal 关闭 → Notice 出现，文案含 `+描述` 标识："已复制到剪贴板（关系: refines+描述）。"

**路径 b · 留空跳过**（验证 D1-4 可选）
- [ ] textarea 不输入任何东西
- [ ] 按 Esc / 点「跳过」/ 直接关闭 modal
- [ ] modal 关闭 → Notice 出现，文案**不**含 `+描述`："已复制到剪贴板（关系: refines）。"

**路径 c · 输入后按 Esc**
- [ ] textarea 输入文字
- [ ] 不点提交，直接按 Esc
- [ ] **预期行为**：当作"留空跳过"处理（onClose 默认 onPicked("")）→ 路径 b 的 Notice

**3 条路径任一通过 + Claudian sidebar 自动激活** → 第 5.6 步 ✅

### 第 6 步：粘贴到 Claudian 输入框

- [ ] 点击 Claudian 输入框让光标进入
- [ ] `Cmd+V` 粘贴
- [ ] 输入框**首行**必须显示 `/ai-linked-doc`（这是关键！）
- [ ] 第二行是 `Please invoke the Skill tool with skill_name="ai-linked-doc"...`
- [ ] 后面是 `选中文本: / 源笔记路径: / 活动白板: / 关系类型: / 派生描述:` **五**字段（v2.5 加 派生描述 行）
- [ ] **关系类型行**形如 `关系类型: refines (细化 (refines))`（key + 中文标签）
- [ ] **派生描述行**：路径 a → `派生描述: 为了单独梳理特征方程的求解步骤`；路径 b/c → `派生描述: (用户留空)`

**如果粘贴出来不是上述格式** → 说明 plugin 剪贴板写入没成功，转 "🔴 诊断 A"

**User：1，我发现节点创建原白板的时候，并没有标记来源于哪一个原白板；2，我们的原白板标记节点之间的联系我觉得使用 mermaid 还是用 Karpathy 的 wiki 方式表示关联的方式会更好？因为我现在打开原白板中并不是很明显表示出节点之间的关系，请你启动并行 agent deep explore 社区成熟的方案**
![[截屏2026-04-30 上午4.44.24.png]]
### 第 7 步：发送 prompt
![[截屏2026-04-30 上午4.47.27.png]]
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
      
最终输出：

> [!NOTE]
> 
> ## **Step 8 · 执行自检 + 回执**

```
自检清单：
[x] Step 5 new_file_path = "节点/Characteristic-Equation-for-Eigenvalues.md"（以 "节点/" 开头）
[x] generated_md frontmatter 无 subject 字段 + 无 tags 数组
[x] ## 关联概念 只列 [[Fundamentals]] 一条，无捏造
[x] Step 6 实际调了 Edit 工具 + replace_all: false
[x] Step 7 白板 md 路径 = 原白板/特征值与特征向量.md
[x] ## Concepts 的 wikilink 用完整路径 "节点/Characteristic-Equation-for-Eigenvalues"
[x] 回执 3 行格式
```

---

```
✓ 节点/Characteristic-Equation-for-Eigenvalues.md 已创建（扁平池）
✓ 源笔记 [[Fundamentals]] 第 12 行已替换为 [[节点/Characteristic-Equation-for-Eigenvalues]]
✓ 原白板/特征值与特征向量.md 的 ## Concepts 已添加新节点（doc_count → 1）

💡 你想看新节点 → Cmd+Click [[节点/Characteristic-Equation-for-Eigenvalues]] 跳转
   （不强制，可继续留在源笔记读下去）
```

**如果没有 3 行 ✓ 结构** → Skill 自检失败或没完整跑，转 "🔴 诊断 C"

### 第 8.5 步：⭐ v2.4 新增 — 验证回执含关系类型（D1-3 视觉确认）

v2.4 回执是 **4 行**（不再是 3 行），最后一行写关系类型：

- [ ] Skill 回执的**最后一行**形如 `关系类型: refines (细化 (refines))`
- [ ] 4 行回执其中 ✓ 第 1 行末尾包含 `frontmatter relationships: [{type: refines}]` 文字
- [ ] 4 行回执其中 ✓ 第 2 行末尾包含 `+ [!relation/refines]+ callout` 文字
- [ ] 4 行回执其中 ✓ 第 3 行末尾包含 `（关系: refines）` 文字

**如果回执还是 v2.2 的 3 行格式（无关系类型行）** → SKILL.md 不是 v4.4 版本，检查 `cat canvas-vault/.claude/skills/ai-linked-doc/SKILL.md | head -20` 应见 `v4.4 扁平架构 + 关系类型双写`

### 第 9 步：验证新概念文件

- [ ] Obsidian 左边文件树展开 `节点/`（v4.4 扁平池，不再是 wiki/canvases/）
- [ ] 看到**新文件** `节点/<concept-name>.md`
- [ ] **路径必须是 `节点/`，不能是 `wiki/canvases/` 或 `wiki/concepts/`**
- [ ] 打开它，内容满足：
  - frontmatter 含 `type: concept` / `mastery_score: 0.30` / `source_note: "[[源笔记]]"` / `source_board: "[[原白板/<board>]]"` / `created_from: ai_linked_doc` / `up: [[源笔记]]` / `derived-from: [[源笔记]]`
  - **⭐ v2.4 新增**：frontmatter 含 `relationships:` 数组：
    ```yaml
    relationships:
      - type: refines
        target: "[[Fundamentals]]"
    ```
  - frontmatter **无** `subject` / `tags` 字段
  - `# <概念名>` 标题
  - `## 核心概念` 1-2 句定义（语言匹配选中文本）
  - `## 关键点` 3-5 个 bullet
  - `## 关联概念` **只列 `- [[源笔记]] — extracted from this note`**（不能列捏造的其他概念）

### 第 9.5 步：⭐ v2.4 新增 — 验证源笔记 callout 双写（D1-3 视觉半边）

回到源笔记，找到选中文本被替换的位置：

- [ ] 选中文本已**替换为 wikilink** `[[节点/<concept-name>]]`
- [ ] wikilink **下方紧跟 callout**（5 行格式）：
  ```
  [[节点/<concept-name>]]

  > [!relation/refines]+ 派生关系: 细化
  > 上方 wikilink 节点派生自这段文本，关系类型为 **refines**。
  ```
- [ ] callout 标题中文标签匹配你选的关系（refines→细化 / extends→扩展 / prerequisite→先修 等）
- [ ] callout 类型 `[!relation/refines]+` 中的 key 和 frontmatter `relationships[0].type` **一致**
- [ ] Reading View（按 `Cmd+E`）下，callout 渲染为带颜色的可折叠块（具体颜色取决于 obsidian 主题对未知 callout type 的处理）

**如果只有 wikilink 没 callout** → SKILL.md Step 6 没改对，检查 `grep -A 5 "Step 6" canvas-vault/.claude/skills/ai-linked-doc/SKILL.md`

### 第 9.6 步：⭐ v2.4 新增 — 验证白板 ## Concepts 含关系 key

打开 `原白板/<active_board>.md`：

- [ ] `## Concepts` section 末尾新加一行：`- [[节点/<concept-name>]] — refines, weak (0.30)`（**关系 key 替代 v2.2 的 `extracted` 字样**）
- [ ] `## Recent Activity` section 末尾新加一行末尾含 `（关系: refines）`

### 第 4.5 步：⭐ v2.6 新增 — 节点派生节点自动继承白板（截图 bug 修复）

**前提**：你已经至少派生过 1 个节点（v2.4 / v2.5 测过的话已有 `节点/Characteristic-Equation-for-Eigenvalues.md` 这种）。

**测试场景 A · 节点继承（v2.6 主路径）**：

- [ ] 在 obsidian 打开**已派生的节点 md**（例 `节点/Characteristic-Equation-for-Eigenvalues.md`）
- [ ] 确认其 frontmatter 含 `source_board: "[[原白板/特征值与特征向量]]"`（这是之前派生时 Skill 写的）
- [ ] 在节点 md 正文选一段文字（任意句子）
- [ ] 按 Cmd+Shift+D
- [ ] **预期**：右下角弹 Notice `继承源节点白板归属：特征值与特征向量（v2.6 自动）` (3s)
- [ ] 关系 modal + 描述 modal 正常出现（不变）
- [ ] 提交 prompt 到 Claudian
- [ ] **关键验收**：Skill 跑完后**不**弹 AskUserQuestion 问你白板归属
- [ ] 新节点正确写到 `节点/<新概念>.md`，frontmatter `source_board: "[[原白板/特征值与特征向量]]"` 与源节点一致
- [ ] 原白板 `原白板/特征值与特征向量.md` 的 ## Concepts 多 1 行新节点

**测试场景 B · 不在节点路径下（v2.6 fallback 验证）**：

- [ ] 在 `wiki/canvases/math140/Fundamentals.md`（非 `节点/` 路径）选中文字
- [ ] 按 Cmd+Shift+D
- [ ] **预期**：Notice `当前笔记 wiki/canvases/math140/Fundamentals.md 不在 原白板/ 或 节点/ 路径下...`
- [ ] **不**弹"继承源节点白板归属"的 Notice（因为不是节点）
- [ ] Skill 仍走 .canvas-config.yaml / AskUserQuestion 流程（保持原行为）

**测试场景 C · 节点 frontmatter 无 source_board（v2.6 fallback 验证）**：

- [ ] 手动建一个 `节点/test-no-board.md`，frontmatter 不写 source_board 字段
- [ ] 在其中选中文字按 Cmd+Shift+D
- [ ] **预期**：plugin 不弹"继承源节点白板归属"的 Notice
- [ ] Skill Step 2.5 fallback 命中：Skill 自己 Read 源节点 frontmatter（仍无 source_board）→ 走规则 3 / 4
- [ ] AskUserQuestion 出现，你能正常选白板

**3 个场景任一通过即 v2.6 节点继承核心 OK**。场景 A 是正路，场景 B/C 验证不破坏原行为。

### 第 9.7 步：⭐ v2.5 新增 — 验证派生描述三处落地（仅路径 a 跑此步）

跑路径 a 的用户必须验证 3 处落地。**留空（路径 b/c）跳过此步**：

- [ ] **落地 1 · 源笔记 callout body** — 回到源笔记，找 `[!relation/refines]+ 派生关系: 细化` callout，body 应有 **3 行**（v2.5 路径 B 6 行模板）：
  ```
  > 上方 wikilink 节点派生自这段文本，关系类型为 **refines**。
  > 你的派生意图: 为了单独梳理特征方程的求解步骤
  ```
- [ ] **落地 2 · 新节点 frontmatter** — 打开 `节点/<concept>.md`，frontmatter `relationships[0]` 含 `description` 子字段：
  ```yaml
  relationships:
    - type: refines
      target: "[[Fundamentals]]"
      description: "为了单独梳理特征方程的求解步骤"
  ```
- [ ] **落地 3 · AI 写的正文反映你的意图** — `## 核心概念` 段不应只是机械复读你的描述，而是：
  - 真的从"特征方程的求解步骤"角度展开
  - 不是从其他角度（如 "what is 特征方程" 一般定义）切入
  - **路径 b/c 留空的对比**：留空时 AI 自己选最常见的角度，可能是一般定义；填了描述则按你的角度切入

**留空（路径 b/c）的反向验证**：
- [ ] frontmatter `relationships[0]` **不**含 `description` 字段（不要 `description: ""`）
- [ ] callout body **没有**第三行 `> 你的派生意图:`（5 行模板，路径 A）

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

### 🔴 诊断 E — v2.5 modal 没弹出（关系 modal 或描述 modal 任一缺失）

按完 Cmd+Shift+D 立刻进入剪贴板写入而**跳过两个 modal**：

1. 检查 main.js 大小：`stat -f "%z" canvas-vault/.obsidian/plugins/canvas-learning-system/main.js` 应见 `20348`（v2.6）
2. 不是 20348 → 重新 build + cp：
   ```bash
   cd frontend/obsidian-plugin && npm run build
   cp main.js ../../canvas-vault/.obsidian/plugins/canvas-learning-system/main.js
   ```
3. cp 完后**必须**在 obsidian 重启（Cmd+Q 退出再开 / Cmd+P → "Reload app without saving"）
4. 仍跳过 modal → 检查 `frontend/obsidian-plugin/src/main.ts` 第 130 行附近含 `new RelationTypeModal(this.app, ...)`

modal 弹出但选完没反应（剪贴板没写入）：
1. F12 console 看是否报 `RelationTypeModal is not defined`
2. 或 `RELATION_TYPES is not exported` → ai-linked-doc.ts 没改对
3. 重 build 即可

---

## 🚦 验收结果

### 理想情况（全 20 步 ✅，含 v2.4 关系类型 3 步 + v2.5 派生描述 2 步 + v2.6 节点继承 1 步）
→ 告诉我 "**Story 1.17 v2.6 通过**"  
→ 我 mark done + 启动下一个 Story（1.18 Dashboard MVP 或 wikilink 图谱构建 Story 1.2）

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
