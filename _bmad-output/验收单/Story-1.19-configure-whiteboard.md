---
story: "1.19"
title: "原白板配置 Skill（场景 A 从零建 + 场景 B 从任意 md 派生）"
status: "review"
version: "v2.1"
date: "2026-04-20"
developer: "Claude Code (Opus 4.7)"
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
---

# Story 1.19 验收单 v2.1 — 完整验收流程

> [!info]+ 这份文档为什么重写（v2 → v2.1）
> 你 2026-04-20 在 v2 第 7 步下方批注了 2 个深层问题，3 个并行 agent deep explore 给出结论后，我把 Skill、template、验收单全部升级到 v2.1。这份文档重新设计，**直接在开头完整回答你的 2 个问题**（不再埋在第 7/11 步），然后给你从零跑一遍的 11 步清单。

---

## 💬 你的 2 个批注 — 直接答案（看完这段再看别的）

### Q1 · 学科和白板名之间怎么区分？

**A：这是 2 个不同字段，刻意分开。不合并。**

| 字段 | 角色 | 格式 | 例子 | 给谁看 |
|---|---|---|---|---|
| **`subject`** | **文件夹代码 (slug)** | lowercase + 字母数字 + 连字符 | `math240`, `cs-61b`, `phil-a250` | **机器**：文件夹路径 / Dataview / Graph View 分组 / Dashboard 筛选 |
| **`board_name`** | **显示名** | 自由（中文/空格/大小写都行） | `线性代数`, `CS 61B 数据结构`, `Linear Algebra II` | **你**：index.md 的 H1 标题 / Dashboard 列表 |

**关系**：一个 `subject` 配一个 `board_name`（1:1 对应）。改 `subject` = 文件夹改名（破坏性，wikilink 会断）；改 `board_name` = 只改标题（安全）。

**为什么必须分两个？**
- 文件夹名 `wiki/canvases/<subject>/` 要被 wikilink 引用 / Graph View 过滤 / Dataview 查询 → 必须 **ASCII + 无空格 + 短** 不然各种工具都炸
- 但人看的标题要自然 → 所以单独留一个 `board_name` 字段放完整名称

**v2.1 UX 改动**：Skill 以前一次问两个容易混，现在**分 2 次问**你，每次问都明确"这次问的是 subject 代码"或"这次问的是 board_name 显示名"，并配格式要求 + 3 个例子。

---

### Q2 · 我移动的 md 没双链关系，Skill 怎么在 index.md 归纳它们的联系？

**A：Skill 刻意不归纳语义关系。做了就是幻觉（违反项目 DD-03 铁律）。**

关系有 **3 个真实来源**，分工如下：

| 来源 | 谁建 | 什么时候建 | 怎么看 |
|---|---|---|---|
| ① **你手写 `[[wikilink]]`** | 你自己 | 任何笔记正文打 `[[` 自动补全候选文件名 | `Cmd+G` Graph View 立即可见 |
| ② **Story 1.17 AI 双链** | `/ai-linked-doc` Skill（你按 `Cmd+Shift+D` 触发）| 选中文本 → AI 派生新概念时**自动给源笔记 + 新概念互相建 `[[...]]`** | Graph View 自动更新 + 两个笔记正文都能看到 wikilink |
| ③ **未来 Story 2.x 知识图谱** | 后端 Graphiti 做 entity extraction | 后端异步跑（未来 Epic 2-3）| 写入 index.md 的 `## Relationship Graph` section |

**所以你现在移动两个 md 但没写 wikilink → `## Relationship Graph` section 就是空的**。这不是 bug，是设计：

- 如果 1.19 Skill 读两个 md 然后凭空说"A 依赖 B"，这是 LLM 幻觉，项目 DD-03 禁止 mock/臆造
- 真关系来自**你在笔记里写过的 wikilink**（来源 ①）或 **AI 派生概念时自动建的双链**（来源 ②）
- 如果笔记里真的没任何 wikilink，也没跑过 1.17 → 当前"无关系"是事实，不能假装有

**现在就想看关系怎么办？3 条路**：
1. **最快（零配置）**：`Cmd+G` 打开 Obsidian 原生 Graph View → 左上 `Filters` 输 `path:wiki/canvases/<subject>/` → 你本白板里**所有 wikilink** 拓扑立即可见
2. **让 AI 帮你建关系**：在一个笔记里选中一段文字 → `Cmd+Shift+D`（Story 1.17） → AI 派生新概念 + **自动在两个笔记建双向 wikilink**
3. **手写 1 条看看**：在任意笔记正文写 `这依赖 [[另一个笔记名]]` → Graph View 立即多一条线

**v2.1 template 改动**：我把 index.md 的 `## Relationship Graph` section 从空白注释改成了 `[!info]+` callout，里面就是上面这段解释 + Dataview 代码示例（留给未来装 Dataview 后嵌入动态图）。

---

## 🎯 Story 1.19 要做到什么（一句话）

**让你从 0 建第一个原白板**：要么从零指定主题（场景 A），要么一键把你已有的任意 md 派生成一个原白板（场景 B）。Skill 自动建文件夹 / 生成 index.md / 迁笔记 / 加 wikilink。

---

## 📖 完整交互流程（ASCII 图）

### 场景 A · 从零建白板（先有主题，没笔记）

```
你在 Claudian 侧栏输:
  /configure-whiteboard "线性代数" "math240"   ← 带参一次搞定
或
  /configure-whiteboard                          ← 无参，Skill 分步问
        ↓
Skill Step 1: 识别场景 A
Skill Step 2: 若缺参数 → 分 2 步问你:
  Q1: "新白板的 subject 代码？"（例 math240）
  Q2: "新白板的 board_name 显示名？"（例 线性代数）
        ↓
Skill Step 3: 检查 wiki/canvases/math240/ 是否已存在
  若已存在 → 问"重用还是换代码？"
        ↓
Skill Step 4: mkdir wiki/canvases/math240/
              读 template 替换 {{board_name}}/{{subject}}/{{created_at}}
              生成 wiki/canvases/math240/index.md
        ↓
Skill Step 5: 若你当前打开的笔记不在 canvases/ → 问"要迁入作为种子笔记吗？"
  是 → 走 Step 6 (move/copy/更 frontmatter/append index.md)
  否 → 跳过
        ↓
Skill Step 6.5: 声明"不做语义关系归纳"（template 里的 Relationship Graph 保持 [!info] callout）
        ↓
Skill Step 7: 回执 (空白板: 4 行描述 / 有种子: 3 行 ✓)
```

### 场景 B · 从任意 md 派生（你已有笔记想变白板）

```
你打开任意位置的 md (例: wiki/raw/my-notes.md 或 vault 根的 未命名.md)
        ↓
你在 Claudian 输:
  /configure-whiteboard from wiki/raw/my-notes.md   ← 显式路径
或
  /configure-whiteboard                              ← 若当前 active 笔记不在 canvases/ 自动降级场景 B
        ↓
Skill Step 1: 识别场景 B，拿 source_path
        ↓
Skill Step 2: Glob 现有白板列表 → AskUserQuestion:
  "归入哪个白板？（显示现有代码 → 板名对照）
   - math240 → 线性代数 (5 笔记)
   - cs-61b → CS 61B 数据结构 (12 笔记)
   - 新建..."
  若选"新建" → 分 2 步问 subject + board_name（同场景 A）
        ↓
Skill Step 3: 检查冲突
        ↓
Skill Step 4: mkdir + 生成 index.md (若新白板) / 跳过 (若选已有白板)
        ↓
Skill Step 5: AskUserQuestion: "种子笔记 move 还是 copy？"
              move → Bash: mv source_path target
              copy → Bash: cp source_path target
        ↓
Skill Step 6: 更新种子 frontmatter (加 subject 字段) + append index.md ## Concepts
        ↓
Skill Step 6.5: 同上
        ↓
Skill Step 7: 3 行 ✓ 回执
```

---

## 🔧 前置条件（P1-P4）

### P1 · 部署完整性验证（在终端跑，30 秒）

```bash
# 1. Skill 文件存在
ls /Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/.claude/skills/configure-whiteboard/SKILL.md

# 2. Template 文件存在
ls /Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/.claude/skills/configure-whiteboard/templates/index.md.template

# 3. SKILL.md 含 v2.1 的 subject vs board_name 分工说明
grep -c "两个字段的分工" /Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/.claude/skills/configure-whiteboard/SKILL.md

# 4. Template 含 v2.1 的 Relationship Graph callout
grep -c "怎么看笔记之间的关系" /Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/.claude/skills/configure-whiteboard/templates/index.md.template
```

预期：4 个命令都返回文件路径或 ≥1 次命中。

### P2 · Claudian 就绪（Cmd+Q 重开 Obsidian 再验证）

- [ ] Cmd+Q 退 Obsidian，重新打开 `canvas-vault`
- [ ] 左下角显示 "canvas-vault"
- [ ] Settings → Community plugins → Claudian 开关已开
- [ ] Settings → Claudian → Claude CLI Path = `/Users/Heishing/.local/bin/claude`
- [ ] 点 Claudian sidebar → 输入框出现 + 能打字

### P3 · Claudian 识别 Skill（关键！）

- [ ] 在 Claudian 输入框打 `/config`
- [ ] **Slash dropdown 菜单**里应该看到 `/configure-whiteboard`
  - 如果没看到 → Claudian 没扫描到 Skill，转 **诊断 A**
- [ ] 鼠标悬停 `/configure-whiteboard` → 看到 description（"当用户消息以 /configure-whiteboard 开头..."）

### P4 · 场景 B 测试准备（造一个种子笔记）

- [ ] 在 Obsidian 左边文件树 `wiki/` 下建新文件夹 `raw`（如果没有）
- [ ] 在 `wiki/raw/` 下建文件 `my-recursion-notes.md`，粘贴以下完整内容：

```markdown
---
created: 2026-04-20
---

# 递归笔记

递归是函数调用自身以解决规模更小的相同问题。

## 核心模式

每个递归函数有两部分：
- **base case**：递归终止条件
- **recursive case**：函数调用自身，问题规模变小

## 例子

计算阶乘 n!：
- base case: 0! = 1
- recursive case: n! = n × (n-1)!
```

⛔ **这里不要加 `subject:` frontmatter** — 用 v2.1 的 Skill 自动加才是验证场景。

---

## ✅ UAT 11 步（按顺序跑，每步勾 `- [ ]`）

### 第 1 步 · DevTools Console 打开（诊断用）

- [ ] `Cmd+Opt+I` 打开 DevTools → 切 Console 标签
- [ ] 清屏（垃圾桶图标）
- [ ] 拖到右边让 Obsidian 主窗口可见

### 第 2 步 · 场景 A 触发 · 完整带参调用（最快成功路径）

- [ ] 在 Claudian 输入框输入（**完整包括引号**）：
  ```
  /configure-whiteboard "线性代数" "math240"
  ```
- [ ] 按 Enter

**预期**：Claude 识别 `/configure-whiteboard` + 两个引号参数 → 直接进 Step 3 冲突检查（跳过 Step 2 的 AskUserQuestion，因为参数齐）。

### 第 3 步 · 场景 A 种子笔记 AskUserQuestion

- [ ] Skill 会问：**"当前打开的笔记 [xxx] 要作为种子笔记迁入 wiki/canvases/math240/ 吗？"**
- [ ] 因为你前面没打开笔记（或在打 Claudian），选 **"跳过"**（建空白板）

**预期**：Skill 进 Step 7 空白板回执。

### 第 4 步 · 场景 A 验证回执 + 文件结构

- [ ] Claudian 输出 4 行回执（含 `✓ 原白板 "线性代数" 已建立`）
- [ ] Obsidian 左边文件树刷新（右键文件夹 → Refresh）
- [ ] 看到新文件夹 `wiki/canvases/math240/`
- [ ] 里面有 `index.md`

### 第 5 步 · 场景 A 验证 index.md 模板完整

打开 `wiki/canvases/math240/index.md`，**逐项核对**：

- [ ] frontmatter：
  - `type: whiteboard_index` ✓
  - `board_name: "线性代数"` ✓
  - `subject: "math240"` ✓
  - `created_at: "2026-04-20T..."` ✓
  - `doc_count: 0` ✓
  - `doc_mastery_avg: 0.00` ✓
- [ ] 顶部 `# 线性代数` H1 标题
- [ ] **`[!info]+ 原白板说明（subject vs board_name 分工）` callout** — 这里是你 Q1 答案的永久版：
  - 说 "`subject: math240` = 机器可读的文件夹代码（slug）..."
  - 说 "`board_name: 线性代数` = 人类可读的显示名..."
  - 附 "你在这白板里能做什么" 3 条快捷键
- [ ] 5 个 body section：
  - `## Concepts` — 空 + 注释说 3 来源
  - `## Theorems & Proofs` — 空
  - `## Common Errors` — 空
  - `## Relationship Graph` — **v2.1 关键**，这里是你 Q2 答案的永久版，完整 `[!info]+` callout 说"怎么看笔记之间的关系"
  - `## Recent Activity` — 有 1 条 "Whiteboard created"

**如果 `## Relationship Graph` 下面不是 callout 只是 `<!-- 注释 -->`** → template 没到 v2.1，转**诊断 B**。

### 第 6 步 · 场景 B 触发 · 从任意 md 派生

- [ ] 在 Claudian 输入框输入：
  ```
  /configure-whiteboard from wiki/raw/my-recursion-notes.md
  ```
- [ ] 按 Enter

### 第 7 步 · 场景 B AskUserQuestion 流程（**v2.1 核心改进**）

这是你 Q1 批注的实操验证点。Skill 会**按顺序问你这些**：

**Q-1: 归属哪个白板？（显示对照表）**
- [ ] 看到选项列表：
  ```
  - math240 → "线性代数" (0 笔记)
  - 新建...
  ```
  注意：**左边 subject 代码，右边箭头，再右边 board_name 显示名** — 这就是分工！
- [ ] 选 **"新建"**

**Q-2: 新白板的 subject 代码？**
- [ ] 问题文案包含：
  - "机器可读的文件夹代码 / slug"
  - "文件夹名 + frontmatter slug"
  - "必须 lowercase + 字母数字 + 连字符"
  - 示例：`math240` / `cs-61b` / `phil-a250`
  - **解释"为什么不用中文"**：给 Dataview / Graph View / wikilink 用
- [ ] 输入 `cs-61b`（小写、连字符、ASCII）

**Q-3: 新白板的 board_name 显示名？**
- [ ] 问题文案包含：
  - "人类可读的显示名"
  - "出现在 index.md 的 H1 + Dashboard 列表"
  - "格式自由（可含中文、空格、大小写）"
  - 示例：`线性代数` / `CS 61B 数据结构` / `抽象代数 II`
- [ ] 输入 `CS 61B 数据结构`（中文 + 空格 + 数字混用）

**Q-4: move 还是 copy？**
- [ ] 选 **move**

**✅ 验证点**：这 4 个 AskUserQuestion **每一个**都应该明确说"这次问的是 subject / board_name / move vs copy"，**不会**出现 v2 那样含糊的"学科代码"让你搞不清是 subject 还是 board_name。

### 第 8 步 · 场景 B 验证派生结果（3 行 ✓）

- [ ] Claudian 输出类似：
  ```
  ✓ 原白板 "CS 61B 数据结构" 已建立 (wiki/canvases/cs-61b/index.md)
  ✓ 种子笔记 my-recursion-notes.md 已 move 到 wiki/canvases/cs-61b/
  ✓ index.md 的 ## Concepts section 已添加 [[my-recursion-notes]] (seed note, mastery: 0.30)
  ```

### 第 9 步 · 场景 B 验证文件变化

- [ ] `wiki/raw/my-recursion-notes.md` **消失**（move 删了原位置）
- [ ] `wiki/canvases/cs-61b/my-recursion-notes.md` 存在
- [ ] 打开它 → frontmatter **多了 `subject: "cs-61b"`** 字段（Skill 加的，这是 Q1 分工的落地证据）
- [ ] `wiki/canvases/cs-61b/index.md` 打开 → `## Concepts` section 有：
  ```
  - [[my-recursion-notes]] — seed note (mastery: 0.30)
  ```

### 第 10 步 · 边界测试（冲突 + copy）

**10a 冲突**：
- [ ] 在 Claudian 重输 `/configure-whiteboard "线性代数 v2" "math240"`（subject 已存在）
- [ ] Skill 应 AskUserQuestion 问 "重用还是换代码？"
- [ ] 选 "换代码" → 输入 `math240-v2` → 继续建新白板

**10b copy 模式**：
- [ ] 在 `wiki/raw/` 再建 `test-copy.md`（随便写两句）
- [ ] 输入 `/configure-whiteboard from wiki/raw/test-copy.md`
- [ ] 归属选已有 `cs-61b`（第 7 步建的）
- [ ] move vs copy 选 **copy**
- [ ] 验证：
  - `wiki/raw/test-copy.md` **保留**（copy 不删原文件）
  - `wiki/canvases/cs-61b/test-copy.md` 也存在

### 第 11 步 · 验证 `## Relationship Graph` + Graph View 关系（**Q2 实操验证**）

这是你 Q2 批注的实操验证点。

#### 11a · 打开 index.md 看 `## Relationship Graph` callout

- [ ] 打开 `wiki/canvases/cs-61b/index.md`
- [ ] 滚到 `## Relationship Graph` section
- [ ] **必须看到 `[!info]+ 怎么看笔记之间的关系（/configure-whiteboard Skill 不做语义归纳）` callout**，不是空白
- [ ] Callout 内容包含：
  - "**本 Skill 刻意不生成语义关系**"声明
  - "关系的 3 个真实来源"（你手写 / Story 1.17 AI 派生 / 未来 2.x Graphiti）
  - "现在就能看的关系" — Cmd+G + `path:` filter 教程
  - "想要把 Graph View 嵌入这里" — Dataview plugin 代码示例

**如果这里是空白只有 `<!-- 注释 -->`** → template 没到 v2.1，转**诊断 B**。

#### 11b · Graph View 看零关系状态（验证"没写就是没有"）

- [ ] 按 `Cmd+G` 打开 Obsidian Graph View
- [ ] 左上 `Filters` 面板输入：
  ```
  path:wiki/canvases/cs-61b/
  ```
- [ ] 应该看到：
  - `index` 节点
  - `my-recursion-notes` 节点
  - `test-copy` 节点
  - `index → my-recursion-notes` 一条线（因为 Step 8 在 index.md 的 `## Concepts` append 了 `[[my-recursion-notes]]`）
  - `index → test-copy` 一条线（copy 时也 append 了）
  - `my-recursion-notes` 和 `test-copy` 之间**没线**（因为你没在这两个笔记正文写 wikilink）

**这就是 Q2 答案的可视化证明**：Skill 没帮你脑补 `my-recursion-notes` 和 `test-copy` 的语义关系（幻觉风险），只把 index.md 的"目录引用"体现为 wikilink。

#### 11c · 手写 wikilink 看关系立即出现（来源 ①）

- [ ] 打开 `wiki/canvases/cs-61b/my-recursion-notes.md`
- [ ] 在 `## 例子` section 后加一行：
  ```
  补充参考：[[test-copy]] 里也提到了类似模式。
  ```
- [ ] 保存（Cmd+S）
- [ ] 回到 Graph View
- [ ] 应看到 `my-recursion-notes → test-copy` **多了一条线**（双向关系自动出现，不需要 Skill 重跑）

#### 11d · Story 1.17 AI 双链验证（来源 ②，可选）

只有你已完成 Story 1.17 UAT 前置条件 + 新 hotkey 绑定时才能测：

- [ ] 在 `my-recursion-notes.md` 选中 "base case" 文本
- [ ] 按 `Cmd+Shift+D`（Story 1.17 hotkey）
- [ ] 切到 Claudian sidebar → 粘贴（Cmd+V） → Enter
- [ ] 等 Skill 生成 `base-case.md`
- [ ] 回 Graph View → 看到 `base-case` 节点 + 到 `my-recursion-notes` 的**双向线**（AI 自动建双链）

这条验证 Story 1.17 的职责（而不是 1.19）。

---

## 🚦 验收结果

### 全 11 步 ✅
→ 回我 "**Story 1.19 通过**"  
→ 我 mark 1.19 done → 自动 unblock Story 1.17 UAT（那时 1.17 有白板可用了）

### 部分 ❌
→ 告诉我 "**诊断 [A/B/C/...]**" + 哪步失败 + 截图  
→ 我针对性 correct-course 到 v2.2

---

## 🔴 诊断矩阵

### 🔴 诊断 A · Claudian slash dropdown 没有 `/configure-whiteboard`

1. 终端跑 `head -15 /Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/.claude/skills/configure-whiteboard/SKILL.md`
2. 首行应是 `---` + `name: configure-whiteboard` + description 合法
3. 若 SKILL.md 本身有问题 → 我检查 frontmatter
4. 若 SKILL.md 没问题 → Claudian 没扫到。重启 Obsidian（Cmd+P → "Reload app without saving"）强制 Claudian 重扫 vault/.claude/skills/

### 🔴 诊断 B · index.md 的 `## Relationship Graph` 是空白不是 callout

- 说明 `canvas-vault/.claude/skills/configure-whiteboard/templates/index.md.template` 没到 v2.1
- 终端跑：`grep "怎么看笔记之间的关系" /Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/.claude/skills/configure-whiteboard/templates/index.md.template`
  - 应该 ≥1 次命中
- 若没命中 → 我来修 template
- 若命中但你在 index.md 看不到 → 告诉我，可能是 Skill 用旧 template 渲染的

### 🔴 诊断 C · Skill 自由发挥（捏造 wikilink、写错路径）

- 同 Story 1.17 v2.1 的诊断 C
- Skill 开头的 `⛔ CRITICAL TRIGGER & HARD CONSTRAINTS` 6 条硬约束没生效
- 最可能：你在 Claudian 里没用 `/configure-whiteboard` 开头直接对话
- 解决：严格用 slash 命令触发

### 🔴 诊断 D · AskUserQuestion 没分两步问 subject / board_name

- 说明 SKILL.md 的 Step 2 没到 v2.1
- 终端跑：`grep "两个字段的分工" /Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/.claude/skills/configure-whiteboard/SKILL.md`
  - 应该 ≥1 次命中
- 若没命中 → v2.1 没部署，重拉仓库

---

## 📝 你的批注区

> [!question]+ 你对 Story 1.19 v2.1 的批注
>
> 在这里写任何疑问/建议/不满意。或者直接用 `Cmd+Shift+A` 批注上面任何一段。
>
> （空）

### 历史追溯

> [!error]+ 2026-04-20 — v2 → v2.1 correct-course（用户批注 2 个深层问题）
> **你的原批注**：
> 1. "这里有个问题学科和白板名之间怎么区分"
> 2. "然后我移动的 md 文档，如果我没有提及各个 md 文件之间的双向链接关系的话，那么请问你如何在 index.md 文件中，归纳这两个 md 文件的联系呢？"
>
> **3 并行 agent deep explore 结论**：
> - Q1：subject（slug）vs board_name（显示名）必须分离，分别承担文件系统 / 多学科隔离 / 人类可读职责。不能合并（Dashboard 列需要 board_name，Dataview 过滤需要 subject）
> - Q2：关系归纳属于 1.17 / Graph View / 未来 2.x KG 三层分工，1.19 只做"归类 + 列条目"。Skill 自己臆造关系违反 DD-03
>
> **已修复**：
> - SKILL.md Step 2 AskUserQuestion 分 2 步问 subject / board_name + 每步说明角色
> - SKILL.md 新增 Step 6.5 职责分工表（1.19 / 1.17 / Graph View / 未来 2.x）
> - index.md.template 顶部 `[!info]+` callout 讲 subject vs board_name 分工 + "你能做什么" 快捷键
> - index.md.template 的 `## Relationship Graph` section 从空白注释改为完整 `[!info]+` callout（3 关系来源 + `Cmd+G` 教程 + Dataview 预留）
> - 本验收单重写，把 2 个答案提到开头

---

## 🔗 技术 spec 参考（给 Claude 读的）

- **Story spec**：`_bmad-output/implementation-artifacts/epic-1/1-19-configure-whiteboard-skill.md`（v2.1）
- **Skill**：`canvas-vault/.claude/skills/configure-whiteboard/SKILL.md`
- **Template**：`canvas-vault/.claude/skills/configure-whiteboard/templates/index.md.template`
- **Commits**：
  - `8374e10` v2 实施
  - `c934dee` v2.1 subject-vs-boardname-and-relationship-scope
  - （本次）验收单 v2.1 全面重写

---

## 📅 你的下一步

1. **跑 P1 部署验证**（30 秒终端）
2. **Cmd+Q 重开 Obsidian + Claudian 启用**（2 分钟）
3. **按 11 步 UAT 依次跑**（15-20 分钟，场景 A + B + 边界 + 关系图）
4. **反馈**：
   - 全 ✅ → "Story 1.19 通过"
   - 部分 ❌ → "诊断 [X]" + 截图

反馈后：
- 通过 → mark 1.19 done → unblock 1.17 UAT（切回测 1.17 AI 双链，那时候终于有白板环境）
- 部分失败 → correct-course → 回到 UAT 重跑
