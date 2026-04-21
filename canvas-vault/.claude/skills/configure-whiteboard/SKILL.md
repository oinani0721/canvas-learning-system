---
name: configure-whiteboard
description: "当用户消息以 /configure-whiteboard 开头请求建立新原白板时，必须调用此 Skill。两种场景：A 从零建（/configure-whiteboard \"<board-name>\" \"<subject>\"）；B 从任意 md 派生（/configure-whiteboard from <md-path> [subject]）。Skill 会自动 mkdir wiki/canvases/<subject>/ + 生成 index.md + 归类种子笔记 + 更新 frontmatter + append wikilink。严禁自由对话或写到其他路径。"
argument-hint: "[from <path>] 或 [<board-name> <subject>] 或无参（走 AskUserQuestion）"
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - AskUserQuestion
model: sonnet
---

# 原白板配置 Skill（Canvas Learning System · Story 1.19 v2）

## ⛔⛔⛔ CRITICAL TRIGGER & HARD CONSTRAINTS

**识别触发**：
- 若用户消息以 `/configure-whiteboard` 开头 → **立即调用本 Skill**

**执行硬约束**（全部满足才算成功）：

1. **必须按下方 Step 1→7 顺序执行**，不得跳步
2. **必须写到 `wiki/canvases/<subject>/`**，严禁写到 `wiki/concepts/`、`wiki/raw/` 或其他
3. **subject 代码验证**：必须 lowercase + 字母数字 + 可含连字符（例：`math240`、`cs-61b`、`default`）；违反则 AskUserQuestion 重问
4. **move 失败保护**：若 move 源 md 到目标时失败（例如跨卷 rename 失败）→ 回退为 copy + 提示用户手动删源文件
5. **已有白板保护**：若 `wiki/canvases/<subject>/` 已存在 + 已有 `index.md` → AskUserQuestion 问 "重用白板" 还是 "用新 subject 代码"
6. **必须返回 Step 7 的回执**（成功或部分失败 ✓/✗/⚠ 组合）

---

## 两种使用场景

### 场景 A · 从零建白板

用户消息：
```
/configure-whiteboard "Linear Algebra" "math240"
```
或直接 `/configure-whiteboard`（无参 → AskUserQuestion 补 board_name + subject）

### 场景 B · 从任意 md 派生（2026-04-20 新增）

用户消息：
```
/configure-whiteboard from wiki/raw/my-notes.md math240
```
或 `/configure-whiteboard from <path>`（不给 subject → AskUserQuestion 智能候选）
或 `/configure-whiteboard` 无参但当前 active 笔记不在 canvases/ → 降级为场景 B

---

## 执行步骤

### Step 1 · 解析参数 + 场景判定

从消息提取：
- 若消息含 `from <path>` → **场景 B**，`source_path = <path>`
- 若消息含 `"<board-name>" "<subject>"` 两个引号参数 → **场景 A**
- 若无任何参数 → 看 Claudian context 有无 "active note" 提示（用户当前打开的笔记）
  - 有 + 该 active note 不在 `wiki/canvases/` → **场景 B**，`source_path = active note`
  - 无 → **场景 A**，后面 AskUserQuestion 补

### Step 2 · 补齐 subject 和 board_name

> **两个字段的分工**（必须向用户讲清楚，不可混用）：
> - **`subject`** = **机器可读的文件夹代码** = 文件夹名 `wiki/canvases/<subject>/` + frontmatter `subject:` 字段 + Dashboard 过滤用的 slug。格式：`^[a-z0-9]+(-[a-z0-9]+)*$`（lowercase + 数字 + 连字符）。例 `math240`、`cs-61b`。
> - **`board_name`** = **人类可读的显示名** = index.md 的 `# H1` 标题 + frontmatter `board_name:` + Dashboard 列表里显示给用户看的名字。格式自由（可含中文、空格、大小写）。例 `线性代数`、`CS 61B 数据结构`、`Linear Algebra II`。
>
> 一个 subject 对应一个 board_name（1:1）。subject 变更 = 文件夹改名（破坏性），board_name 变更 = 只改 frontmatter + H1（安全）。

**subject 智能候选**（场景 A + B 共用）：
1. 用 `Glob` 搜 `wiki/canvases/*/index.md` 枚举现有 subject + board_name（读 frontmatter `subject` 和 `board_name` 字段配对）
2. 若场景 B + 源 md 有 `subject` frontmatter → 预填该值为默认推荐
3. `AskUserQuestion`（必须显式区分两个字段的角色，不要只写 "归属哪个学科"）：
   > 这个原白板归属哪个学科文件夹（**subject 是文件夹代码**，例如 `math240`、`cs-61b`）？
   >
   > **已有学科**（显示 "代码 → 板名" 对应关系，帮你记住哪个是哪个）：
   > - `math240` → "线性代数"（5 笔记）
   > - `cs-61b` → "CS 61B 数据结构"（12 笔记）
   > - ...
   >
   > 选已有代码 → 种子笔记直接并入该白板，**不会新建**；
   > 或选 **"新建"** → 我会分两步问你：先问新 subject 代码（机器用），再问 board_name 显示名（人看的）。

   若已有白板被选 → 跳到 Step 4（直接 append 到现有 index.md，不重建）
4. 若选"新建" → `AskUserQuestion`（**第 1 问：subject 代码**）：
   > 新白板的 **subject 代码**（文件夹名 + frontmatter slug）是什么？
   >
   > 格式要求：lowercase + 字母数字 + 可含连字符（正则 `^[a-z0-9]+(-[a-z0-9]+)*$`）。
   >
   > 例 `math240`（数学 240）、`cs-61b`（CS 61B）、`phil-a250`（哲学 A250）。
   >
   > 为什么是代码不是中文？因为文件夹名 + frontmatter slug 要给 Dataview 过滤、Graph View 分组、跨笔记 wikilink 用，必须短 + ASCII + 无空格。
5. 若场景 A（继续问 board_name）→ `AskUserQuestion`（**第 2 问：board_name 显示名**）：
   > 这个白板的 **显示名**（board_name，出现在 index.md 的 H1 标题 + Dashboard 列表里给你看）是什么？
   >
   > 格式自由（可含中文、空格、大小写）。例 `线性代数`、`CS 61B 数据结构`、`Linear Algebra`、`抽象代数 II`。
   >
   > 可以和 subject 代码长得不一样（subject `math240` 配 board_name `线性代数` 很常见）。
6. 若场景 B → board_name 可选（默认用 source_path 的文件名 stem 作为 board_name，**但仍要 AskUserQuestion 确认** — 文件名不总是好的白板名）

**subject 验证**：正则 `^[a-z0-9]+(-[a-z0-9]+)*$`。不符合 → 重问（显示 "subject 必须是 lowercase 字母数字和连字符，例 `math240`；这不是 board_name，board_name 可以是中文"）。

### Step 3 · 重名冲突处理

用 `Glob wiki/canvases/{subject}/index.md` 检查是否已存在：

- **已存在** → `AskUserQuestion`：
  > `wiki/canvases/{subject}/` 已有白板。怎么处理？
  > - 重用（把当前种子笔记加入现有白板）→ 跳 Step 5
  > - 换代码（让我重新问 subject）→ 回 Step 2
- **不存在** → 继续 Step 4

### Step 4 · 创建文件夹 + index.md

```bash
mkdir -p "wiki/canvases/{subject}"
```

用 Read + Write 替换模板：

```bash
# 1. 读模板
template=$(cat ".claude/skills/configure-whiteboard/templates/index.md.template")

# 2. 生成时间戳
created_at=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# 3. 替换变量（Bash 里用 sed 简单替换）
echo "$template" | \
  sed "s|{{board_name}}|{board_name}|g" | \
  sed "s|{{subject}}|{subject}|g" | \
  sed "s|{{created_at}}|{created_at}|g" \
  > "wiki/canvases/{subject}/index.md"
```

若 sed 失败 → 用 Read template + Write 替换后内容（等价路径，更稳）。

### Step 5 · 种子笔记归类（场景 B 必跑；场景 A 可选）

**场景 B**（已有 `source_path`）：

1. `AskUserQuestion`：
   > 种子笔记要 **move**（推荐，原位置删除）还是 **copy**（保留原位置副本）到白板？
2. 若 move：`Bash: mv "{source_path}" "wiki/canvases/{subject}/{basename}"`
3. 若 copy：`Bash: cp "{source_path}" "wiki/canvases/{subject}/{basename}"`
4. 若 move 失败（跨卷）：`Bash: cp "{source_path}" "target" && rm "{source_path}"` 降级；失败则报告

**场景 A** + 当前 active note 不在 canvases 路径：
- 询问是否把 active note 作为种子笔记迁入（AskUserQuestion）
- 同意 → 走上述 move/copy 流程（active note path 作 source_path）
- 不同意 → 跳过 Step 5（白板目录里只有 index.md）

记录 `seed_note_path = wiki/canvases/{subject}/{basename}` 供 Step 6/7 使用。

### Step 6 · 更新种子笔记 frontmatter + index.md

**更新种子笔记 frontmatter**（如有 seed_note_path）：

- 用 `Read` 读 seed note
- 检查 frontmatter 是否有 `subject` 字段
  - 无 → 在 frontmatter 末尾加 `subject: "{subject}"`
  - 有但值不同 → `AskUserQuestion` 问 "覆盖吗？"
  - 有且值相同 → 跳过
- 用 `Edit`（`old_string` 精准对齐 frontmatter 当前内容）或 `Write` 覆盖

**更新 index.md 的 ## Concepts section**（如有 seed_note_path）：

- 用 `Read` 读 index.md
- 在 `## Concepts` section 末尾 append：
  ```
  - [[{basename-stem}]] — seed note (mastery: 0.30)
  ```
- 用 `Write` 覆盖 index.md

**更新 index.md 的 Recent Activity**：

- append：
  ```
  - {ISO}: Seed note {basename-stem}.md imported into whiteboard
  ```

### Step 6.5 · 关系归纳边界（重要 — 不要越权）

**本 Skill 不做 "笔记之间的语义关系归纳"**。明确职责分工：

| 职责 | 归属 | 什么时候触发 |
|---|---|---|
| 把种子笔记"归入白板目录" + 记 wikilink 到 `## Concepts` 列表 | **本 Skill（1.19）** | 用户 `/configure-whiteboard` |
| 从现有笔记派生**新概念**并在源笔记里建 `[[wikilink]]` 双链 | **Story 1.17 `/ai-linked-doc`** | 用户 `Cmd+Shift+D` 选中文本 |
| 批量读白板里所有笔记的现有 wikilink 在 `## Relationship Graph` 里可视化 | **Obsidian 原生 Graph View** | 用户 `Cmd+G` 或 hover 预览 |
| 识别"概念 A **依赖** 概念 B" / "概念 A **是** 概念 B 的特例" 这类语义关系 | **Story 2.x Knowledge Graph**（未来） | 后端 Graphiti + entity extraction |

**所以 index.md 的 `## Relationship Graph` section 在本 Skill 执行完后是空的 — 这是预期行为，不是 bug**。关系图的填充来源：

1. **用户手动 `[[wikilink]]`** 写在任意笔记正文里（你在 Obsidian 打 `[[` 就会自动补全）
2. **Story 1.17 AI 派生概念**时自动给源笔记 + 新概念笔记**双向**建 wikilink
3. **Obsidian Graph View**（`Cmd+G`）聚合所有 wikilink 自动绘关系图 — **不需要本 Skill 干预**
4. **未来 Story 2.x** 通过 Graphiti 在 `## Relationship Graph` 写入"A depends on B"这类带类型的语义关系

**本 Skill 只做"归类 + 列条目"，不做"语义归纳"**。这是刻意的设计边界 — 防止自由发挥臆造笔记之间的关系（例如断言 "递归 依赖 循环" 这种没证据的声明）。用户看到 `## Relationship Graph` 为空时，请打开 Graph View 看 wikilink 拓扑图。

### Step 7 · 返回回执

**场景 A 成功**（无种子笔记）：
```
✓ 原白板 "{board_name}" 已建立
📍 位置: wiki/canvases/{subject}/index.md
🏷️ 代码: {subject}
📝 关联笔记: 0（空白板）

下一步：
- 在 Claudian sidebar 关闭此对话后，打开 wiki/canvases/{subject}/ 开始学习
- 选中笔记内容 → Cmd+Shift+D 让 AI 自动派生概念
- 选中内容 → Cmd+Shift+A 加 Tips/错误/提问标注
```

**场景 A/B 成功含种子笔记**（3 行 ✓ + 1 行关系图提示）：
```
✓ 原白板 "{board_name}" 已建立（subject 代码 {subject} / 显示名 {board_name}）
✓ 种子笔记 {basename} 已归入 wiki/canvases/{subject}/
✓ index.md 的 Concepts section 已添加 [[{basename-stem}]]

💡 关系图怎么看：index.md 的 ## Relationship Graph 现在是空的（Skill 不做语义归纳）。
   - 按 Cmd+G 打开 Obsidian Graph View → 聚焦 wiki/canvases/{subject}/ 文件夹
   - 看到的线条 = 笔记之间实际存在的 [[wikilink]]
   - 没有线？先手写 [[名字]] 或用 Cmd+Shift+D（Story 1.17）让 AI 自动建双链
```

**部分失败**（ ✓/✗/⚠ 组合）：
```
✓ 原白板已建立
✗ 种子笔记 move 失败: <原因>
⚠ 请手动将 {source_path} 移到 wiki/canvases/{subject}/
```

---

## 执行自检清单（Step 7 返回前必 tick）

```
[ ] Step 4 mkdir 路径以 "wiki/canvases/" 开头
[ ] index.md frontmatter 含 type: whiteboard_index / board_name / subject / doc_count: 0
[ ] 若有种子笔记 seed_note_path 以 "wiki/canvases/{subject}/" 开头
[ ] 种子笔记 frontmatter 有 subject 字段（值 = {subject}）
[ ] index.md 的 ## Concepts section 存在 + 含种子笔记 wikilink（若有）
[ ] 返回回执格式正确（场景 A 或 A/B 成功 3 行 ✓ / 部分失败 ✓✗⚠）
```

若任一 ☐ 未勾 → 回溯修复。

---

## 错误场景速查

| 症状 | Skill 响应 |
|---|---|
| subject 不合法（含空格/大写） | AskUserQuestion 重问 |
| `wiki/canvases/<subject>/` 已存在 | AskUserQuestion 问重用/换代码 |
| 源 md 不存在（场景 B） | 返回 `✗ 源笔记 {path} 不存在`，停止 |
| 源 md 已在 `wiki/canvases/<existing>/` | 返回 `⚠ 已属于 <existing> 白板，不执行`，停止 |
| move 跨卷失败 | 降级为 cp + rm；再失败则返回 `✗` + 手动指引 |
| 种子笔记 frontmatter 解析错 | 用 Write 覆盖整个 frontmatter，不用 Edit |
| sed 替换失败 | 回退用 JS 字符串替换 + Write |

---

## 约束

- **不调 Graphiti / 后端 API**（MVP 纯 vault 文件级）
- **不碰 `raw/` 目录**（降级后 raw 保留给课件原件；概念笔记归 `wiki/canvases/`）
- **不做 Modal / Settings UI**（纯 Claudian 交互）
- **不做 debounce / 并发控制**（Skill 同步执行）
- **不生成 `.canvas` 文件**（Obsidian Canvas view 不是 MVP）

---

## 参考

- Story spec：`_bmad-output/implementation-artifacts/epic-1/1-19-configure-whiteboard-skill.md`
- 用户批注来源：`_bmad-output/验收单/Story-1.17-ai-linked-doc.md:133`（"我现在有一个在任意文件夹的 md 文件..."）
- 3 并行 agent 调研：2026-04-20 round-8
- 架构：`planning-artifacts/architecture.md:113` Mode D（Claude Code CLI 订阅）
- 下游 Story 1.17：`canvas-vault/.claude/skills/ai-linked-doc/SKILL.md`（需要本 Skill 建的白板环境）
- 下游 Story 1.18：Dataview `FROM "wiki/canvases"` 需要本 Skill 产出的 `type: whiteboard_index` + `board_name` + `doc_mastery_avg` 字段
