---
story: "1.19"
title: "原白板配置 Skill（场景 A 从零建 + 场景 B 从任意 md 派生）"
status: "review"
version: "v2.1"
date: "2026-04-20"
developer: "Claude Code (Opus 4.7)"
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
---

# Story 1.19 验收单 — 原白板配置 Skill

> [!info]+ 这是什么
> 这是 Story 1.19 的用户验收文档。Story 1.19 是"**用户打开 Canvas 第一件事**" — 创建第一个原白板。之前 Story 1.17 UAT 卡住就是因为没有这个入口。
>
> 技术 spec 在 `_bmad-output/implementation-artifacts/epic-1/1-19-configure-whiteboard-skill.md`（Claude 读的）。

> [!question]+ 2026-04-20 用户第 7 步批注 — 已在 v2.1 回应（跳到第 7 步 + 第 11 步）
> 用户在 v2 第 7 步批注：
> 1. **"学科和白板名之间怎么区分？"** → v2.1 改进：AskUserQuestion 文案明确 `subject` = **文件夹代码**（ASCII slug）vs `board_name` = **显示名**（可中文），**分两步问**你，不让你搞混。详见第 7 步下方 [!tip]+ callout。
> 2. **"我移动的 md 文档如果没提双向链接关系，你如何在 index.md 归纳两个 md 文件的联系？"** → v2.1 回答：**Skill 刻意不做语义关系归纳**（做了就是幻觉）。关系有 3 来源：(a) 用户手写 `[[wikilink]]` (b) Story 1.17 AI 双链自动建 (c) 未来 Story 2.x 知识图谱。现在就能看关系 → 按 `Cmd+G` 打开 Graph View。详见第 11 步下方 [!tip]+ callout + index.md 的 `## Relationship Graph` section 内的 [!info]+ 解释。

---

## 🎯 这个 Story 要做到什么

通过 **Claudian Skill `/configure-whiteboard`**，你可以：
- **场景 A**：从零建一个全新的学习主题原白板（例："Linear Algebra" + `math240`）
- **场景 B**：把你任意文件夹的现有 md 笔记**一键派生成一个新原白板**（回应你 2026-04-20 的"我现在有一个在任意文件夹的 md 文件那么我想要从这个文件开始生成原白板"诉求）

Skill 自动做 4 件事：
1. 建文件夹 `wiki/canvases/<subject>/`
2. 生成 `index.md`（含 frontmatter + Concepts/Theorems/Errors/Relationship/RecentActivity 5 段结构）
3. 把你的种子笔记 move（或 copy）到白板目录
4. 更新种子笔记 frontmatter + index.md wikilink 列表

---

## 📖 两种交互流程

### 场景 A · 从零建（你有学习主题想法但没笔记）

```
你在 Claudian 输: /configure-whiteboard "Linear Algebra" "math240"
        ↓
Skill Step 1-3: 解析参数 + 验证 subject 合法性
        ↓
Step 4: mkdir wiki/canvases/math240/ + 生成 index.md
        ↓
Step 5: 询问 "把当前打开的笔记作为种子迁入吗？"
        → 不 → 跳过 Step 5-6
        → 是 + 按 Step 5-6 流程
        ↓
Step 7: 返回 "✓ 原白板 Linear Algebra 已建立"
```

### 场景 B · 从任意 md 派生（你已有笔记想变成白板，2026-04-20 新增）

```
你有一个 wiki/raw/my-notes.md 或 vault 根的 未命名.md
        ↓
你在 Claudian 输: /configure-whiteboard from wiki/raw/my-notes.md
        或 /configure-whiteboard（如果笔记已 active）
        ↓
Skill Step 1: 识别场景 B (含 from <path> 或 active note 不在 canvases/)
        ↓
Step 2: AskUserQuestion "归属哪个学科？"
        → 列出已有 subject（math240, cs-61b, ...）+ "新建" 选项
        → 读源 md 的 subject frontmatter 预填（如有）
        ↓
Step 3: 检查 wiki/canvases/<subject>/ 是否已存在（已存在 → 问"重用/换代码"）
        ↓
Step 4: mkdir + 生成 index.md
        ↓
Step 5: AskUserQuestion "move（推荐）还是 copy？" → 执行
        ↓
Step 6: 更新种子笔记 frontmatter subject + index.md ## Concepts 加 wikilink
        ↓
Step 7: 返回 "✓ 白板已从 my-notes.md 派生，种子笔记已归入"
```

---

## 🔧 前置条件

### P1 · 环境验证

- [ ] canvas-vault 的 Claudian 已启用 + CLI path 填对（Story 1.17 P1 完成后这里就 OK）
- [ ] 终端 `ls canvas-vault/.claude/skills/configure-whiteboard/SKILL.md` 存在
- [ ] 终端 `ls canvas-vault/.claude/skills/configure-whiteboard/templates/index.md.template` 存在

### P2 · 强制 Reload Obsidian

- [ ] `Cmd+P` → "Reload app without saving"（让 Claudian 重新扫描 Skills）

---

## ✅ UAT（11 步 — 场景 A + B 双路径 + v2.1 关系归纳验证）

### 第 1 步：F12 DevTools Console（用于诊断，可选）

- [ ] `Cmd+Opt+I` 打开 Console

### 第 2 步：Claudian slash 补全验证

- [ ] 打开 Claudian 侧栏
- [ ] 在输入框输 `/config`
- [ ] Slash dropdown 里应**看到 `/configure-whiteboard`**（如没有 → Skill 文件没被扫到，转诊断 A）

### 第 3 步：场景 A 测试（从零建）

- [ ] 在 Claudian 输入：
  ```
  /configure-whiteboard "Linear Algebra" "math240"
  ```
- [ ] 按 Enter
- [ ] Claudian 开始执行 Skill（约 5-20s）

### 第 4 步：场景 A · Skill 询问"种子笔记"

- [ ] Claude 应该 AskUserQuestion 问："把当前打开的笔记作为种子迁入吗？"
- [ ] 若你没打开任何笔记或选"不"→ 跳过迁入，只建空白板
- [ ] 若选"是" → Skill 进入 Step 5-6 流程

### 第 5 步：场景 A · 验证回执 + 结构

- [ ] Claudian 最终返回回执，含 `✓ 原白板 "Linear Algebra" 已建立`
- [ ] Obsidian 左侧文件树刷新看到 `wiki/canvases/math240/` 文件夹
- [ ] 里面有 `index.md`
- [ ] 打开 `index.md` 看到：
  - frontmatter 含 `type: whiteboard_index` / `board_name: "Linear Algebra"` / `subject: "math240"` / `doc_count: 0` / `doc_mastery_avg: 0.00`
  - `# Linear Algebra` 标题
  - 5 个 section：`## Concepts` / `## Theorems & Proofs` / `## Common Errors` / `## Relationship Graph` / `## Recent Activity`
  - Recent Activity 段有 1 条 "Whiteboard created" 记录

### 第 6 步：场景 B 测试（从任意 md 派生）

- [ ] 在 canvas-vault 任意位置（例 `wiki/raw/`）建测试文件 `my-recursion-notes.md`：
  ```markdown
  # 递归笔记
  
  递归是函数调用自身以解决规模更小的相同问题。
  
  基本模式：base case（边界）+ recursive case（自调用）。
  ```
- [ ] 在 Claudian 输：
  ```
  /configure-whiteboard from wiki/raw/my-recursion-notes.md
  ```
- [ ] 按 Enter

### 第 7 步：场景 B · Skill AskUserQuestion 流程（v2.1 文案改进）

- [ ] Claudian 问 "这个原白板归属哪个学科**文件夹**（**subject 是文件夹代码**，例 `math240`、`cs-61b`）？"（注意：问法明确是 "文件夹代码"，不是含糊的"学科"）
- [ ] 选项列出已有的 `math240 → "线性代数"（N 笔记）`（显示 "代码 → 板名" 对应关系）+ "新建"
- [ ] 选 **"新建"** → Claudian 分**两步**问你：
  - 第 1 问：**subject 代码**（文件夹名 slug，必须 lowercase + 字母数字 + 连字符）→ 输 `cs-61b`
  - 第 2 问：**board_name 显示名**（可含中文 / 空格 / 大小写，出现在 H1 + Dashboard 列表）→ 输 `CS 61B 数据结构`
- [ ] Claudian 问 "move 还是 copy？" → 选 move
- [ ] Skill 开始执行

> [!tip]+ 2026-04-20 用户批注回应 — subject vs board_name 的分工
> **用户原批注**："学科和白板名之间怎么区分？"
>
> **回答**：这是**两个不同的字段**，刻意分开：
>
> | 字段 | 角色 | 格式 | 例子 |
> |---|---|---|---|
> | **`subject`** | 机器可读 **文件夹代码 / slug** | lowercase + 字母数字 + 连字符 | `math240`, `cs-61b`, `phil-a250` |
> | **`board_name`** | 人类可读 **显示名** | 自由（可中文 / 空格 / 大小写） | `线性代数`, `CS 61B 数据结构`, `Linear Algebra II` |
>
> **为什么分两个？**
> - 文件夹名 `wiki/canvases/<subject>/` 要给 wikilink、Graph View 分组、Dataview 查询、Dashboard 筛选用 → **必须短 + ASCII + 无空格**，不然各种工具会坏
> - 但你自己看的时候想看到自然语言 → 所以 `board_name` 保留完整中文 / 正常大小写 / 带空格
>
> **两个字段 1:1 对应**（一个 subject 配一个 board_name）。Skill v2.1 把 AskUserQuestion 改成**显式分两问**了 — 不会再让你搞混哪个是哪个。

### 第 8 步：场景 B · 验证派生结果

- [ ] Claudian 返回 3 行 ✓：
  ```
  ✓ 原白板 "CS 61B 数据结构" 已建立
  ✓ 种子笔记 my-recursion-notes.md 已归入 wiki/canvases/cs-61b/
  ✓ index.md 的 Concepts section 已添加 [[my-recursion-notes]]
  ```
- [ ] 验证：
  - `wiki/raw/my-recursion-notes.md` **已消失**（move 删了原文件）
  - `wiki/canvases/cs-61b/my-recursion-notes.md` **存在**
  - 打开它 → frontmatter 有 `subject: "cs-61b"`（Skill 加的）
  - `wiki/canvases/cs-61b/index.md` 的 `## Concepts` section 有 `- [[my-recursion-notes]] — seed note (mastery: 0.30)`

### 第 9 步：验证已有白板场景（copy 测试）

- [ ] 再建一个测试文件 `wiki/raw/test-copy.md`（写几句话）
- [ ] 在 Claudian 输 `/configure-whiteboard from wiki/raw/test-copy.md`
- [ ] 归属选已有的 `math240`（不是新建）
- [ ] move vs copy 选 **copy**
- [ ] 验证：
  - `wiki/raw/test-copy.md` **仍然存在**（copy 保留原文件）
  - `wiki/canvases/math240/test-copy.md` 也存在
  - `wiki/canvases/math240/index.md` 的 `doc_count` 字段从 0 增加到 1（若 Skill 有实现），且 Concepts section 加了 `[[test-copy]]`

### 第 10 步：边界 — 冲突重试

- [ ] 重新输 `/configure-whiteboard "Linear Algebra" "math240"`（重名）
- [ ] Skill AskUserQuestion 问 "重用还是换代码？"
- [ ] 选"换代码" → 输新代码 → 确认建新白板

### 第 11 步（v2.1 新增）：验证 `## Relationship Graph` section + Graph View 关系

> [!tip]+ 2026-04-20 用户批注回应 — 关系归纳的职责分工
> **用户原批注**："我移动的 md 文档，如果我没有提及各个 md 文件之间的双向链接关系的话，那么请问你如何在 index.md 文件中，归纳这两个 md 文件的联系呢？"
>
> **回答（核心）**：Skill 1.19 **刻意不做语义关系归纳** — 因为 Skill 自己臆造"A 依赖 B"这类关系 = 幻觉，严禁。关系有 3 个真实来源，分工如下：
>
> | 来源 | 谁建的 | 什么时候触发 | 在哪看 |
> |---|---|---|---|
> | **你手写的 `[[wikilink]]`** | 你自己 | 任何笔记正文打 `[[` 自动补全 | Graph View（Cmd+G）立即可见 |
> | **Story 1.17 AI 双链**（`Cmd+Shift+D`）| `/ai-linked-doc` Skill | 选中文本 → AI 派生新概念时**自动给源笔记 + 新概念**建双向 wikilink | Graph View 自动更新 + 两个笔记正文里都有 `[[...]]` |
> | **Story 2.x 知识图谱**（未来）| 后端 Graphiti 语义抽取 | 后端异步跑 entity extraction | 写入 index.md 的 `## Relationship Graph` section |
>
> 所以**你现在移动了两个 md 但没手写 wikilink → `## Relationship Graph` 就是空的**。这不是 bug，是刻意设计。要看关系有 3 条路：
> 1. **最快**：按 `Cmd+G` 打开 Obsidian Graph View → 左上 `Filters` 输 `path:wiki/canvases/<subject>/` → 实际 wikilink 拓扑立刻可见（不需装任何插件）
> 2. **让 AI 帮你建关系**：在 `my-recursion-notes.md` 里选中 "base case" 文本 → `Cmd+Shift+D`（Story 1.17） → AI 派生 `base-case.md` + **自动**在两个笔记里建 `[[...]]`
> 3. **自己手写**：在任意笔记里写 `这个概念依赖 [[another-note]]` → Graph View 立即多一条线 + 对方笔记的 backlinks 面板也会出现反链

**UAT 验证步骤**：

- [ ] 打开 `wiki/canvases/cs-61b/index.md`（第 8 步建的）
- [ ] 滚到 `## Relationship Graph` section → 看到 **[!info]+ callout 说明** 而**不是空白**
  - Callout 标题："怎么看笔记之间的关系（/configure-whiteboard Skill 不做语义归纳）"
  - 列出 3 个关系来源 + "现在就能看的关系"段（Graph View）+ "想嵌入怎么办"段（Dataview 示例）
- [ ] 按 `Cmd+G` 打开 Graph View
  - 左上 `Filters` 面板输入 `path:wiki/canvases/cs-61b/`
  - 应该看到 `my-recursion-notes` + `index` 两个节点，**之间有线**（因为 Step 6 在 `index.md` 的 `## Concepts` 段 append 了 `- [[my-recursion-notes]] — seed note`，触发 wikilink）
- [ ] 在 `my-recursion-notes.md` 正文手写一行 `这里依赖 [[index]] 的定义`
- [ ] 回 Graph View → 看到 `my-recursion-notes → index` 多了一条反向线（双向关系自动出现，不需要 Skill 干预）
- [ ] 选中 `my-recursion-notes.md` 里的 "base case" 文本 → `Cmd+Shift+D`（Story 1.17 命令）
  - 等 AI 派生 `base-case.md` 完成
  - 回 Graph View → 看到 `base-case` 节点 + 到 `my-recursion-notes` 的线（AI 自动建双链）
  - 这就是 Story 1.17 的职责，不是 1.19 的

**如果你看到 `## Relationship Graph` section 空白（只有 `<!-- -->` 注释，没 callout）** → 说明 template 未更新到 v2.1，检查 `canvas-vault/.claude/skills/configure-whiteboard/templates/index.md.template`。

---

## 🚦 验收结果

### 理想（全 11 步 ✅）
→ 告诉我 "**Story 1.19 通过**"  
→ 我 mark done → 然后**自动回到 Story 1.17 UAT**（前置条件终于成立了）

### 部分失败
→ 告诉我哪步 ❌ + 截图  
→ 我 `bmad-bmm-correct-course` 到 v2.1

### 诊断 A · Skill 不在 Slash dropdown
- 验证文件：`head -15 canvas-vault/.claude/skills/configure-whiteboard/SKILL.md`
- 必须首行 `---` + `name: configure-whiteboard` + `description` 合法 YAML
- Reload Obsidian（Cmd+P → "Reload app"）让 Claudian 重扫

### 诊断 B · Skill 触发但不走 6 步流程
- 同 Story 1.17 的 Claudian 自由发挥问题
- 检查 SKILL.md 开头的 CRITICAL TRIGGER 是否完整
- 降级：在 Claudian 里明说 "请调用 configure-whiteboard Skill 严格按 Step 1-7 处理"

---

## 📝 你的批注区

> [!question]+ 你对 Story 1.19 的批注
>
> 在这里写任何疑问/建议/不满意。
>
> （空）

### 这个 Story 解决了什么历史问题

> [!error]+ 2026-04-20 — 用户 UAT Story 1.17 批注暴露 onboarding 入口缺失
> **你的批注**：
> 1. "双链提问节点的功能本身就是要在原白板里面使用的"
> 2. "我现在有一个在任意文件夹的 md 文件那么我想要从这个文件开始生成原白板，请问我该如何操作？"
>
> **根因**：Story 1.19 yaml 早就声明 `blocks: ["1.17","1.18"]`（数据层规定 1.19 先做），但 Claude 之前在 CLAUDE.md 按工作量排序成 `1.16→1.17→1.18→3.X` 覆盖了依赖。用户 Story 1.17 UAT 时没有白板可用 → 只能手动 mkdir + 建笔记，体验割裂。
>
> **已修复**：
> - 顺序修正 `1.16 → 1.19 → 1.17 → 1.18`
> - Story 1.19 scope 从 v1 的"场景 A"扩展为 v2 的"场景 A + 场景 B"（6h → 8h），回应"任意文件夹 md 派生"诉求
> - Story 1.17 暂 blocked，等 1.19 done 后回头测

---

## 🔗 技术 spec 参考（给 Claude 读的）

- **Story spec**：`_bmad-output/implementation-artifacts/epic-1/1-19-configure-whiteboard-skill.md`（v2 2026-04-20）
- **Skill**：`canvas-vault/.claude/skills/configure-whiteboard/SKILL.md`
- **Template**：`canvas-vault/.claude/skills/configure-whiteboard/templates/index.md.template`
- **3 并行 Agent 调研报告**：2026-04-20 round-8（story 依赖链 + 原白板定义 + 用户旅程）
- **Commit**：
  - `b660445`：round-8 顺序 correct-course + 1.17 blocked + 1.19 scope v2 扩展
  - 本次 commit：Skill + template 实施

---

## 📅 下一步（你批完这份单后）

1. **全 ✅** → 说 "Story 1.19 通过" → 我 mark 1.19 done → 自动启动 1.17 UAT（本身代码不变，只是前置成立了）
2. **部分 ❌** → 批注 → 我 correct-course 到 v2.1
3. **建议 UAT 顺序**：
   - 先跑场景 A 建个小白板看看整体流程
   - 再跑场景 B 从任意 md 派生（这是你最初 2026-04-20 的诉求）
   - 最后测边界（冲突 / move vs copy）
