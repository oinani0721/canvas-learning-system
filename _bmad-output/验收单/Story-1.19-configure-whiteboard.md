---
story: "1.19"
title: "原白板配置 Skill（场景 A 从零建 + 场景 B 从任意 md 派生）"
status: "review"
version: "v3"
date: "2026-04-20"
developer: "Claude Code (Opus 4.7)"
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
---

# Story 1.19 验收单 v3 — 重新设计的完整验收流程

> [!info]+ 这份文档为什么 v3 重写
> 你在 v2/v2.1 UAT 批注 2 个深层问题（学科 vs 白板名 / Skill 如何归纳 md 关系），3 并行 agent deep explore 回答。v2.1 把答案埋在第 7/11 步 `[!tip]+` callout 里，但你说没搜到 → v3 把 **2 个核心概念提升到文档顶部**（第 2、3 段），然后 **UAT 11 步重新组织为 4 阶段**（前置 / 场景 A / 场景 B / 关系验证）+ 诊断矩阵 A-E。
>
> 历史追溯（v1/v2/v2.1 演进）见文档底部"历史追溯"段。
>
> v2.1 代码已 ship（commit `c934dee`）。本文档覆盖原 UAT 11 步（无代码变更，只重组 UAT 文案）。

---

## 📌 核心概念 1 · subject vs board_name 的分工（必读，避免混淆）

Skill 会问你**两个**字段，名字像但角色完全不同：

| 字段 | 角色 | 格式 | 例子 | 给谁用 |
|---|---|---|---|---|
| **`subject`** | 机器可读 **文件夹代码 / slug** | lowercase + 字母数字 + 连字符 | `math240`、`cs-61b`、`phil-a250` | **机器**：`wiki/canvases/<subject>/` 路径 / Dataview 过滤 / Graph View 分组 / Dashboard 筛选键 |
| **`board_name`** | 人类可读 **显示名** | 自由（可中文 / 空格 / 大小写） | `线性代数`、`CS 61B 数据结构`、`Linear Algebra II` | **人**：index.md 的 `# H1` 标题 + Dashboard 列表看到的名字 |

**为什么不合并为一个？**
- 文件夹路径、wikilink、Dataview 查询 `FROM "wiki/canvases/..."`、Graph View 分组 —— 都要求 **短 + ASCII + 无空格**（不然会坏）
- 但你读文档时想看到自然语言（中文、空格、大小写）
- 所以 1:1 对应：一个 `subject` 配一个 `board_name`。改 subject = 文件夹改名（破坏性），改 board_name = 只改 H1 + frontmatter（安全）

**v2.1 Skill UX**：AskUserQuestion 分**两步**问 — 第一步问 `subject`（含格式约束 + 示例），第二步问 `board_name`（自由格式 + 解释为什么不能合并）。每步都明确标注"这是代码不是显示名"或反之。

> [!tip]+ 形象比喻（如果仍觉得混淆）
> 就像**域名 vs 网站名**。`google.com` 是机器可读的域名（必须 ASCII、不能有空格），`Google 搜索` 是给人看的网站名（随便用。`google.com` = `subject`，`Google 搜索` = `board_name`。

---

## 📌 核心概念 2 · 笔记间关系的 3 个真实来源（Skill 不做语义归纳）

> **你的原问题**："我移动的 md 文档，如果我没有提及各个 md 文件之间的双向链接关系的话，那么请问你如何在 index.md 文件中，归纳这两个 md 文件的联系呢？"
>
> **短回答**：**Skill 1.19 刻意不归纳语义关系**（做了就是幻觉，违反 DD-03 铁律）。关系从下面 3 处来：

| 来源 | 谁建的 | 什么时候触发 | 在哪看 |
|---|---|---|---|
| **① 你手写 `[[wikilink]]`** | 你自己 | 在任何笔记正文打 `[[` 触发文件名补全 | Graph View (`Cmd+G`) 立即可见 |
| **② Story 1.17 AI 双链** | `/ai-linked-doc` Skill | 选中文本 → `Cmd+Shift+D` → AI 派生新概念，**自动**在源笔记 + 新概念笔记**双向**建 wikilink | Graph View 自动更新 + 两笔记正文都有 `[[...]]` |
| **③ Story 2.x Graphiti 知识图谱**（未来）| 后端语义抽取 | 后端异步跑 entity extraction | 写入 index.md 的 `## Relationship Graph` section |

**所以你移了 2 个 md 但没手写 wikilink → `## Relationship Graph` 就是空的**。这不是 bug，是设计。**现在就能看关系，3 条路径**：

### 路径 X（零成本推荐）· Obsidian 原生 Graph View
1. 按 `Cmd+G` 打开 Graph View
2. 左上 `Filters` 面板 → 输 `path:wiki/canvases/<subject>/`
3. 看到每条线 = 一条**真实的** wikilink（没装 Dataview 也行）
4. Hover 某笔记 → 高亮它的入链 + 出链

### 路径 Y · 让 AI 自动建关系
- 在任一笔记选中一段文字 → `Cmd+Shift+D`（Story 1.17）
- AI 派生新概念 md + **双向**建 `[[...]]`
- 两个笔记之间自动出现关系（Graph View 自动更新）

### 路径 Z · 自己手写 wikilink
- 在笔记正文打 `[[` → Obsidian 自动补全现有文件名
- 例：`递归是 [[base-case]] 加上 [[recursive-case]]`
- 马上 Graph View 出现 3 个节点 + 2 条线

> [!warning]+ 绝对不做的事
> Skill **绝对不会**扫描两个 md 的内容然后说"我猜它们有关系"—— 这是 LLM 幻觉的高发区。举例：移入 `递归.md` 和 `循环.md`，Skill 不会写"递归依赖循环" 或 "递归等价于循环"（这些说法在教科书里都是错的）。**关系必须有证据**：要么你写了 wikilink、要么 AI 有选中文本做派生、要么未来 Graphiti 语义抽取有置信度。

---

# 🔧 前置条件（UAT 跑之前必须满足）

## P1 · 部署验证（终端跑一次）

```bash
# 1. Skill 文件存在
ls canvas-vault/.claude/skills/configure-whiteboard/
# 应看到 SKILL.md + templates/

# 2. template 存在
cat canvas-vault/.claude/skills/configure-whiteboard/templates/index.md.template | head -15
# 首行应是 `---`，含 `type: whiteboard_index` / `board_name` / `subject` frontmatter

# 3. SKILL.md frontmatter 合法
head -13 canvas-vault/.claude/skills/configure-whiteboard/SKILL.md
# 应含 `name: configure-whiteboard` / `description: "当用户消息以..."`  / 6 allowed-tools

# 4. Claudian 可用（CLI + sidebar）
which claude && claude --version
# /Users/Heishing/.local/bin/claude + v2.1.114
```

## P2 · 强制 Reload Obsidian（关键！）

- [ ] `Cmd+P` → 搜 `reload` → 选 **"Reload app without saving"** → 回车（让 Claudian 重扫 Skills）
- [ ] canvas-vault 左下角显示 "canvas-vault"（不是 `_bmad-output`）

## P3 · 准备测试素材（场景 B 要用）

创建测试种子笔记 `canvas-vault/wiki/raw/my-recursion-notes.md`（用 Finder 或 Obsidian 创建）：

```markdown
# 递归笔记

递归是函数调用自身以解决规模更小的相同问题。

基本模式：base case（边界条件）+ recursive case（递推关系）。

例：阶乘 factorial(n) = n * factorial(n-1)，base case 是 factorial(0) = 1。
```

（故意**不加** frontmatter + **不加** wikilink，验证 Skill 在"裸 md"上正常工作，且 `## Relationship Graph` 正确保持空白 + 显示 [!info]+ 说明）

---

# ✅ UAT 11 步（4 阶段）

## 阶段 1 · 基础验证（第 1-2 步）

### 第 1 步：F12 DevTools Console（诊断用）

- [ ] 按 `Cmd+Opt+I` → 切 **Console** 标签 → 清屏（保持打开）

### 第 2 步：Claudian slash 补全识别 Skill

- [ ] 打开 Claudian 侧栏
- [ ] 输入框打 `/config`
- [ ] Slash dropdown **必看到** `/configure-whiteboard`

**失败** → 转 [🔴 诊断 A](#诊断-a--skill-不在-slash-补全)

---

## 阶段 2 · 场景 A 从零建白板（第 3-6 步）

### 第 3 步：场景 A 触发（带参）

- [ ] 在 Claudian 输：
  ```
  /configure-whiteboard "Linear Algebra" "math240"
  ```
- [ ] 按 Enter
- [ ] Claudian 开始调用 Skill（约 5-15 秒）

### 第 4 步：场景 A · Skill 询问"种子笔记"

- [ ] Claude 问："把当前打开的笔记作为种子迁入吗？"
- [ ] 选"不"（场景 A 测试空白建）

### 第 5 步：场景 A · 验证回执

- [ ] Claudian 最终返回含 `✓ 原白板 "Linear Algebra" 已建立`
- [ ] 含位置 `wiki/canvases/math240/index.md`

### 第 6 步：场景 A · 验证物理结构

- [ ] Obsidian 左侧文件树展开 `wiki/canvases/math240/`
- [ ] 看到 `index.md`
- [ ] 打开 `index.md`，验证：
  - frontmatter 含 `type: whiteboard_index` + `board_name: "Linear Algebra"` + `subject: "math240"` + `doc_count: 0` + `doc_mastery_avg: 0.00`
  - 顶部 `# Linear Algebra` 标题
  - 下方 `[!info]+ 原白板说明（subject vs board_name 分工）` callout
  - 5 个 section：`## Concepts` / `## Theorems & Proofs` / `## Common Errors` / `## Relationship Graph` / `## Recent Activity`
  - **`## Relationship Graph` section 不是空白** — 含 [!info]+ callout 讲解 3 个关系来源 + Graph View 教程（**这是 v2.1 最关键的改动**）

**失败** → 转 [🔴 诊断 B](#诊断-b--skill-触发但写路径错-wikiconcepts)

---

## 阶段 3 · 场景 B 从任意 md 派生（第 7-9 步）

### 第 7 步：场景 B · 触发 + AskUserQuestion（subject vs board_name 分工验证）

- [ ] 在 Claudian 输：
  ```
  /configure-whiteboard from wiki/raw/my-recursion-notes.md
  ```
- [ ] 按 Enter
- [ ] Claudian 依次弹出以下问题（**注意每个问题的文案是否清晰区分 subject 和 board_name**）：

  **Q1（选学科文件夹）**：
  > 这个原白板归属哪个学科**文件夹**（**subject 是文件夹代码**，例 `math240`、`cs-61b`）？
  > 
  > 已有学科：
  > - `math240` → "Linear Algebra"（第 3-6 步建的）
  > - 或选 "新建" → 分两步问 subject + board_name
  
  → 选 **"新建"**
  
  **Q2（subject 代码）**：
  > 新白板的 **subject 代码**（文件夹名 + frontmatter slug）是什么？格式：lowercase + 字母数字 + 连字符。例 `math240`、`cs-61b`、`phil-a250`。
  > 
  > 为什么是代码不是中文？因为文件夹名要给 Dataview / Graph View / wikilink 用，必须短 + ASCII + 无空格。
  
  → 输 `cs-61b`
  
  **Q3（board_name 显示名）**：
  > 这个白板的 **显示名**（board_name，出现在 H1 + Dashboard）是什么？格式自由（可含中文、空格、大小写）。例 `线性代数`、`CS 61B 数据结构`。
  > 
  > 可以和 subject 长得不一样（subject `math240` 配 board_name `线性代数` 很常见）。
  
  → 输 `CS 61B 数据结构`
  
  **Q4（move vs copy）**：
  > 种子笔记要 move（推荐，原位置删除）还是 copy（保留原位置副本）？
  
  → 选 `move`

**关键验证**：Q1/Q2/Q3 的文案**必须清晰区分** subject（代码）vs board_name（显示名）。如果 Claude 问 "输入学科代码" 就结束了（没问 board_name）→ **SKILL.md 没 v2.1 更新，转 [🔴 诊断 C](#诊断-c--skill-只问一个字段)**。

### 第 8 步：场景 B · 验证摘要 + 物理结构

- [ ] Claudian 返回 3 行 ✓：
  ```
  ✓ 原白板 "CS 61B 数据结构" 已建立
  ✓ 种子笔记 my-recursion-notes.md 已归入 wiki/canvases/cs-61b/
  ✓ index.md 的 Concepts section 已添加 [[my-recursion-notes]]
  ```
- [ ] 验证：
  - `wiki/raw/my-recursion-notes.md` **已消失**（move 删原文件）
  - `wiki/canvases/cs-61b/my-recursion-notes.md` **存在**
  - 打开它 → frontmatter 自动加了 `subject: "cs-61b"`
  - `wiki/canvases/cs-61b/index.md`：
    - H1 标题 = `CS 61B 数据结构`（board_name，不是代码！）
    - frontmatter `subject: cs-61b` + `board_name: CS 61B 数据结构`
    - `## Concepts` section 有 `- [[my-recursion-notes]] — seed note (mastery: 0.30)`
    - `## Relationship Graph` section 仍是 [!info]+ callout（**没有捏造任何 `[[XXX]]`**）

### 第 9 步：copy 模式 + 已有白板场景

- [ ] 创建 `wiki/raw/test-copy.md`（随便写几句话）
- [ ] 在 Claudian 输 `/configure-whiteboard from wiki/raw/test-copy.md`
- [ ] Q1 问学科时 → 选已有的 `math240`（不是新建）
- [ ] Q4 问 move vs copy → 选 **copy**
- [ ] 验证：
  - `wiki/raw/test-copy.md` **仍然存在**（copy 保留原件）
  - `wiki/canvases/math240/test-copy.md` **也存在**
  - `wiki/canvases/math240/index.md` 的 `## Concepts` 段多一行 `- [[test-copy]]`

---

## 阶段 4 · 关系验证（第 10-11 步，核心对应用户批注）

### 第 10 步：验证 `## Relationship Graph` section 是 [!info]+ callout（不是空白）

- [ ] 打开 `wiki/canvases/cs-61b/index.md`
- [ ] 滚到 `## Relationship Graph` section
- [ ] 应看到 **一大段 [!info]+ callout**（template v2.1 的核心改动），内容包含：
  - 标题："怎么看笔记之间的关系（/configure-whiteboard Skill 不做语义归纳）"
  - 3 个关系来源（手写 wikilink / Story 1.17 / 未来 Story 2.x）
  - "现在就能看的关系" 段 — 讲 `Cmd+G` Graph View 和 `path:` filter 用法
  - "想嵌入 Graph View 怎么办" 段 — Dataview plugin 代码示例（本 MVP 未装）

**失败**（section 是空白 `<!-- -->` 或只有段标题）→ template 未更新到 v2.1，转 [🔴 诊断 D](#诊断-d--template-未更新到-v21)

### 第 11 步：实操 Graph View 看真实关系

**目的**：验证"Skill 不归纳，但关系确实能看"——3 条路径。

#### 子步 11a · Obsidian 原生 Graph View（路径 X）

- [ ] 按 `Cmd+G` 打开 Graph View
- [ ] 左上 `Filters` 面板 → 输 `path:wiki/canvases/cs-61b/`
- [ ] 看到 2 个节点：
  - `index`（刚建的 index.md）
  - `my-recursion-notes`（种子笔记）
- [ ] **节点之间有线**（因为 Step 6 在 `index.md` 的 `## Concepts` append 了 `- [[my-recursion-notes]]`，触发 wikilink）

#### 子步 11b · 手写 wikilink（路径 Z）

- [ ] 打开 `wiki/canvases/cs-61b/my-recursion-notes.md`
- [ ] 在正文某处手写：`这里引用 [[index]] 的定义`
- [ ] 回 Graph View 查看 → 多一条 `my-recursion-notes → index` 的反向线
- [ ] 打开 `index.md` 右下角 **Backlinks** 面板 → 应看到 `my-recursion-notes.md` 有反链到 `index`

#### 子步 11c · AI 自动建关系（路径 Y，跨 Story 1.17）

> ⚠️ 这步**依赖 Story 1.17 已 ship**（它是）+ Story 1.17 UAT 的 Claudian 自由发挥 bug 已修。如果 1.17 Skill 不触发，这步会失败 —— 这**不是 1.19 的问题**，是 1.17 的问题。

- [ ] 打开 `wiki/canvases/cs-61b/my-recursion-notes.md`
- [ ] 选中 `base case（边界条件）`
- [ ] 按 `Cmd+Shift+D`（Story 1.17）
- [ ] Claudian 侧栏自动打开 + `Cmd+V` 粘贴 + Enter
- [ ] Story 1.17 Skill 派生 `base-case.md`（或类似概念名）到 `wiki/canvases/cs-61b/`
- [ ] 回 Graph View → 看到 3 个节点（`index` / `my-recursion-notes` / `base-case`）+ 源笔记 ↔ 新概念的双向线

> [!tip]+ 如果 11c 失败
> 说明 Story 1.17 v2.1 的 Skill trigger bug 仍存在（独立于 1.19 的问题）。**不阻塞 1.19 验收通过** — 因为 11a/11b 已证明 Skill 职责边界是对的（不归纳 = 设计正确）。11c 是"顺便测 1.17 集成"，失败就告诉我，我们专门修 1.17。

---

# 🚦 验收结果

## 理想（第 1-11 步全 ✅）

→ 告诉我 "**Story 1.19 通过**"  
→ 我 mark 1.19 done → **自动 unblock Story 1.17 UAT**（前置条件终于成立）

## 部分失败

→ 告诉我 "**诊断 [A/B/C/D/E]**" + 截图 → 我 correct-course

## 完全失败（Claudian 不认 Skill）

→ 讨论方案 C：写一个独立的 Python CLI 或 Obsidian plugin command 直接做 configure-whiteboard 不依赖 Claudian Skill（~8h 保底方案）

---

# 🔴 诊断矩阵

## 诊断 A · Skill 不在 slash 补全

**症状**：Claudian 打 `/config` 没看到 `/configure-whiteboard` 条目。

1. 终端验证文件存在：
   ```bash
   ls canvas-vault/.claude/skills/configure-whiteboard/SKILL.md
   head -13 canvas-vault/.claude/skills/configure-whiteboard/SKILL.md
   ```
2. frontmatter 必须合法（首行 `---`、`name: configure-whiteboard` 必须有）
3. Obsidian 按 `Cmd+P` → "Reload app without saving"（让 Claudian 重扫）
4. 如果重扫后仍没 → Claudian Settings 有没有 "Reload skills" 按钮，手动点
5. 如果还是没 → commit `c934dee` 没 pull 到本地，`git pull origin main`

## 诊断 B · Skill 触发但写路径错（wiki/concepts/）

**症状**：Skill 把文件写到 `wiki/concepts/` 而不是 `wiki/canvases/<subject>/`。

- 原因：这是 Story 1.17 v2 被 Claudian 自由发挥坑过的 bug（Claude 模型自行推断路径）
- Story 1.19 SKILL.md v2.1 有 **Step 6 硬验证 + 7 条 CRITICAL TRIGGER HARD CONSTRAINTS**（首条就是"必须写 wiki/canvases/"）
- 如果仍写错 → SKILL.md 未更新到 v2.1，`head -30 canvas-vault/.claude/skills/configure-whiteboard/SKILL.md` 看 Line 17-29 有没有 `⛔⛔⛔ CRITICAL TRIGGER & HARD CONSTRAINTS`

## 诊断 C · Skill 只问一个字段（没分两步问 subject/board_name）

**症状**：Claudian 问你 "学科代码？" → 输完就结束，没再问 "显示名？"

- 原因：SKILL.md v1 只问一个字段；v2.1 改为分两步问
- 验证：`grep -n "board_name 显示名" canvas-vault/.claude/skills/configure-whiteboard/SKILL.md`
  - 应命中 Line 96-102 附近（Step 2 Q5 AskUserQuestion "第 2 问"）
- 没命中 → v2.1 没 ship，`git pull` 然后 Reload Obsidian

## 诊断 D · template 未更新到 v2.1（index.md 的 Relationship Graph section 空白）

**症状**：建完白板后打开 index.md，`## Relationship Graph` section 是空的或只有注释 `<!-- 概念之间的关系图 -->`，而不是 [!info]+ callout。

1. 验证 template：
   ```bash
   grep -A 2 "Relationship Graph" canvas-vault/.claude/skills/configure-whiteboard/templates/index.md.template
   ```
   预期：紧接着是 `> [!info]+ 怎么看笔记之间的关系` 开头的 callout（约 30+ 行）
2. 如果看到的是 `<!-- 概念之间的关系图 -->` → template 未 ship v2.1
3. `git pull origin main` 拉最新 → 删掉旧建的 index.md → 重跑 Skill 建新白板 → 确认

## 诊断 E · Claudian 自由发挥（不按 Skill Step 1-7）

**症状**：Claude 回复像聊天（"好的，我来为你建白板..."）但没走 AskUserQuestion / 没动文件 / 没返回 ✓ 摘要

- 这是 Story 1.17 v2 遇到过的根本问题 —— Claudian plugin 不强制 Skill 调用，模型可自由发挥
- Story 1.19 v2.1 SKILL.md 的 `⛔⛔⛔ CRITICAL TRIGGER` + 6 条硬约束是对抗这个的
- 如果仍自由发挥 → 在 Claudian 里明确说："请调用 Skill 工具 skill_name=configure-whiteboard，严格按 Step 1-7 执行，不要自由回答"
- 这是最后的降级指令，应该能强制 Claude 走 Skill path

---

# 📝 你的批注区

> [!question]+ 你对 Story 1.19 v3 的批注
>
> 在这里写任何疑问/建议/不满意。也可以直接用 `Cmd+Shift+A` 批注上面任何一段。
>
> （空）

---

# 📜 历史追溯（v1 → v2 → v2.1 → v3 演进）

> [!error]+ 2026-04-20 · 用户批注 2 个深层问题（触发 v2 → v2.1）
> **你的原批注**：
> 1. "**学科和白板名之间怎么区分？**"（看到 Skill 问两个字段懵了）
> 2. "**我移动的 md 文档，如果我没有提及各个 md 文件之间的双向链接关系的话，那么请问你如何在 index.md 文件中，归纳这两个 md 文件的联系呢？**"（期待 Skill 能归纳语义关系但无数据源）
>
> **根因（3 并行 Agent deep explore）**：
> - Agent 1：subject/board_name 不能合并（Dashboard/ReviewNode/Neo4j group_id 都需要 ASCII slug + 人可读名分离），但 UX 要分两步问
> - Agent 2：Skill 语义归纳 = 幻觉（违反 DD-03）；关系有 3 来源（手写 / 1.17 AI / Cmd+G / 未来 2.x KG）
> - Agent 3：具体 patch 清单 — SKILL.md / template / spec / 验收单各自改什么
>
> **v2.1 已修**（commit `c934dee`，2026-04-20）：
> - SKILL.md Step 2 分两步 AskUserQuestion（subject 代码 → board_name 显示名）+ 新增 Step 6.5 关系归纳边界（4 行职责分工表 + 4 条关系来源）
> - index.md.template 顶部加 [!info]+ 分工 callout + `## Relationship Graph` section 改为 [!info]+ 完整 3 来源说明 + Cmd+G 教程 + Dataview 预留代码
> - 验收单 v2.1 在第 7 / 11 步下加 [!tip]+ callout（但用户搜不到）
>
> **v3 进一步改**（2026-04-20 晚些）：把 2 个核心答案**从埋在步骤里提到文档顶部**（本文 "核心概念 1 / 核心概念 2" 段）+ 整个 UAT 重组为 4 阶段 + 诊断矩阵 A-E。代码无变更。

> [!error]+ 2026-04-20 · Epic 1 story 顺序 correct-course（触发 1.19 提升为 P0）
> **你的原批注**："双链提问节点的功能本身就是要在原白板里面使用的。我现在有一个在任意文件夹的 md 文件那么我想要从这个文件开始生成原白板。"
>
> **根因**：Story 1.19 yaml 早就声明 `blocks: ["1.17","1.18"]`，但 Claude 在 CLAUDE.md 按工作量排序成 `1.16→1.17→1.18→3.X`，违反依赖。
>
> **已修**：
> - 顺序修正 `1.16 → 1.19 → 1.17 → 1.18`
> - Story 1.19 scope 从 v1 的"场景 A 从零建"扩展为 v2 的"场景 A + 场景 B 从任意 md 派生"，priority P1→P0，estimate 6h→8h
> - Story 1.17 状态 review → blocked（等 1.19 done 再测）

> [!success]+ 2026-04-19 · Story 1.16 批注 hotkey 通过
> 10 步 UAT 全绿；Cmd+Shift+A 双步 modal 工作；4 Tag + 3 态 checkbox 正确；用户 "前端验证都没有什么问题"。

---

# 🔗 技术 spec 参考（给 Claude 读的）

- **Story spec**：`_bmad-output/implementation-artifacts/epic-1/1-19-configure-whiteboard-skill.md` (v2.1 revision `v2.1-subject-vs-boardname-and-relationship-scope-2026-04-20`)
- **Skill**：`canvas-vault/.claude/skills/configure-whiteboard/SKILL.md` (v2.1 含 CRITICAL TRIGGER 硬约束 + Step 2 分步问 + Step 6.5 关系边界)
- **Template**：`canvas-vault/.claude/skills/configure-whiteboard/templates/index.md.template` (v2.1 含顶部分工 callout + `## Relationship Graph` section [!info]+ 完整说明)
- **3 并行 Agent 调研报告**：2026-04-20 round-8（见 commit `b660445`、`c934dee` 的 message）
- **Commit history**：
  - `b660445`：round-8 顺序 correct-course + 1.17 blocked + 1.19 scope v2 扩展
  - `8374e10`：1.19 v2 实施完成（SKILL.md + template 首次 ship）
  - `c934dee`：1.19 v2.1 subject/board_name + 关系归纳 scope 修复
  - 本次 commit：验收单 v3 重写（UAT 重组 + 核心概念提顶）

---

# 📅 下一步

1. **跑 UAT**（约 15-20 分钟）：按 P1-P3 前置 + 第 1-11 步顺序执行
2. **反馈**：
   - 全 ✅ → "**Story 1.19 通过**" → mark done → unblock 1.17 UAT
   - 部分 ❌ → "**诊断 [A-E]**" + 截图
3. **建议 UAT 顺序**：
   - 阶段 1（2 步）→ 确认 Skill 能被 Claudian 识别
   - 阶段 2（4 步）→ 场景 A 验证主流程正确性
   - 阶段 3（3 步）→ 场景 B 验证你最初的诉求 + subject/board_name 分工
   - 阶段 4（2 步）→ 验证关系归纳分工（你第 2 个批注的核心）
