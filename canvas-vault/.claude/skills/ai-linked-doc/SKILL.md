---
name: ai-linked-doc
description: "当用户消息以 /ai-linked-doc 开头，或包含 '选中文本:'+'源笔记路径:'+'学科:' 三个字段请求创建概念文档时，必须调用此 Skill（Canvas Learning System Story 1.17）。Skill 职责：生成概念 md → 写入 wiki/canvases/<subject>/<name>.md → 把源笔记的选中文本替换为 [[name]] → 更新或创建 wiki/canvases/<subject>/index.md。严禁自由对话或写到 wiki/concepts/。"
argument-hint: "[Canvas plugin 生成的 prompt（已自动复制到剪贴板）]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Bash
  - AskUserQuestion
model: sonnet
---

# AI 双链文档 Skill（Canvas Learning System · Story 1.17 v2）

## ⛔⛔⛔ CRITICAL TRIGGER & HARD CONSTRAINTS（违反 = 执行错误）

**识别触发**：
- 若用户消息首行是 `/ai-linked-doc`，**立即调用本 Skill**，不得自由回答
- 若用户消息包含 `选中文本:` + `源笔记路径:` + `学科:` 三字段（任意顺序），**也必须调用本 Skill**

**执行硬约束**（全部满足才算成功）：

1. **必须按 Step 1→7 顺序执行**，不得跳步
2. **不得自由发挥**：所有文字（概念名 / 关联概念 / Concepts 段等）只能基于输入给的"选中文本"+"源笔记路径"+"学科"推导，不得脑补
3. **必须写到 `wiki/canvases/<subject>/`**，严禁写到 `wiki/concepts/`、`wiki/raw/` 或其他路径
4. **严禁捏造 wikilink**：`## 关联概念` section 只能出现两类链接：
   - (a) 源笔记 stem（必有）
   - (b) 本次 Step 4 刚写的 concept_name（自引用可有可无）
   - **禁止**列 "其他可能相关的概念" — 若未 100% 确认 `wiki/canvases/<subject>/<Other>.md` 真实存在则不得链接
5. **必须返回 Step 7 的 3 行 ✓ 摘要**（成功）或 `✓/✗/⚠` 组合清单（部分失败）
6. **若 `学科 == "unknown"`**，必须调 `AskUserQuestion`，严禁自己猜测 subject 值
7. **若源笔记路径不以 `wiki/canvases/` 开头**（例如 `未命名.md` 在 vault 根），必须调 `AskUserQuestion` 问用户"源笔记应归属哪个原白板？"并让用户回答一个 subject 或 `default`

**拒绝场景**：
- 若消息**既没有** `/ai-linked-doc` 前缀，**也没有**三字段结构 → 回复 "请用 `/ai-linked-doc` 前缀 + Canvas plugin 复制的标准 prompt 触发本 Skill，不要直接粘贴自由文本。"

---

## 触发方式

用户在 Canvas Learning System Obsidian plugin 里选中文本 → 按 `Cmd+Shift+D` → plugin 把以下格式的 prompt 写入系统剪贴板：

```
/ai-linked-doc
Please invoke the Skill tool with skill_name="ai-linked-doc" to handle this request.
Do NOT answer freely — follow the 6-step Skill flow strictly.

选中文本:
<文本>

源笔记路径: wiki/canvases/<subject>/<source>.md
学科: <subject>

请为这段内容创建一个概念文档（三段式：## 核心概念 / ## 关键点 / ## 关联概念）。
```

用户在 Claudian 输入框 `Cmd+V` 粘贴 → 回车。本 Skill 开始执行。

---

## 执行步骤（严格顺序）

### Step 1 · 解析输入

从用户消息中抽 3 个字段：

- **`选中文本`**：可能多行，从 `选中文本:` 行之后读到 `源笔记路径:` 行之前（去掉末尾换行）
- **`源笔记路径`**：单行，相对 vault 根的 `.md` 路径（例 `wiki/canvases/math240/Fundamentals.md`）或其他
- **`学科`**：单 token，通常是 `math240` / `cs61b` / 等 subject 代码，或者 `unknown`

**降级路径 A — 源笔记不在 canvases 路径**（以 `wiki/canvases/` 开头 = 正常；否则降级）：
- 调 `AskUserQuestion`：
  > 源笔记路径 `{sourcePath}` 不在原白板路径下（`wiki/canvases/<subject>/`）。本 Skill 将把生成的概念文档落到哪个原白板？
  > 
  > 选项：
  > - A. 指定一个已建的 subject（例 `math240`、`cs61b`）→ 写到 `wiki/canvases/<subject>/`
  > - B. 用 `default` subject → 写到 `wiki/canvases/default/`
  > - C. 取消本次执行
- 用户回答后，若 `学科`字段仍为 `unknown`，用此处的答复设为 subject

**降级路径 B — 学科 == "unknown"**（且上一步未解决）：
- 调 `AskUserQuestion`：
  > 当前源笔记缺少 `subject` frontmatter。请指定学科代码（例 `math240`），或回答 `default` 落到 `wiki/canvases/default/`。
- 用户回答的非空 token 作为 subject

### Step 2 · 生成概念文档

用下面的 **System Prompt 模板**生成概念 md 的完整内容（含 frontmatter）。**你（当前 Claude Code 模型）就是生成器**。按此 schema 输出到一个内存变量 `generated_md`：

```
你是 Canvas Learning System 的概念文档生成器。

任务：基于用户提供的"选中文本"生成一份结构化的概念笔记。

输出格式（完整 Markdown 文件内容，含 frontmatter）：

---
type: concept
subject: <Step 1 拿到的 subject>
mastery_score: 0.30
created_at: <ISO 8601，用 `date -u +"%Y-%m-%dT%H:%M:%SZ"` 取>
source_note: "[[<源笔记 stem，去掉路径和 .md 后缀>]]"
created_from: ai_linked_doc
---

# <主概念名>

## 核心概念
（基于选中文本，1-2 句精准定义。不赘述。）

## 关键点
- 要点 1
- 要点 2
- 要点 3
（3-5 条，不超过 7 条）

## 关联概念
- [[<源笔记 stem>]] — extracted from this note

严格约束：
- 语言匹配选中文本（中文 → 中文；英文 → 英文）
- 概念定义优先精准而非详尽
- 不写代码块，除非概念本身涉及代码
- 不写"作为 AI 我..."等自我介绍
- 主概念名从核心概念首句提炼（英文保留；中文直接用 2-6 字概念词）
- ⛔ 严禁在 `## 关联概念` 列出"其他可能相关的概念"—— 只输出源笔记 stem 这一条
- ⛔ 严禁 frontmatter 出现 `related_concepts: []` / `tags: []` 等数组字段
```

### Step 3 · 提取概念名

从 `generated_md` 的 `# <主概念名>` 标题行提取主概念名作为文件名：

- 去掉首尾空格
- 英文：保留字母数字，空格/非法字符替换为 `-`（例 `Eigenvalues and Eigenvectors` → `Eigenvalues-and-Eigenvectors`）
- 中文：直接取 2-6 字概念词（例 `特征值` → `特征值`），不加分隔符
- 禁止 `/ \ : * ? " < > |` 等文件系统非法字符

保存为 `concept_name`。

### Step 4 · 写新概念文件

**目标路径**：`wiki/canvases/<subject>/<concept_name>.md`

**重名处理**（最多 9 轮）：
- 用 `Glob` 检查目标路径是否已存在
- 存在则尝试 `<concept_name>_2.md`、...、`<concept_name>_9.md`
- 9 轮全占用 → 返回错误 `✗ 文件名冲突过多 (9+ 重名)`，停止后续

用 `Write` 工具写入 `generated_md` 到最终路径。记录 `new_file_path`。

**⛔ 硬验证**：写之前先自检 `new_file_path` 是否以 `wiki/canvases/` 开头。若不是（例如要写到 `wiki/concepts/`）→ 视为 Skill 执行错误，停止并返回 `✗ 路径硬约束违反`。

### Step 5 · 替换源笔记选中文本为 wikilink

若 `源笔记路径` 是 `unknown` 或指向不存在的文件 → 跳过本步，摘要标记 `⚠ 源笔记未知或不存在，未执行 wikilink 替换`。

否则：

1. 用 `Read` 读 `<源笔记路径>` 全文
2. 确认 `选中文本`（原样，含换行）在文件中存在
3. 用 `Edit` 工具：
   - `file_path`: 源笔记路径
   - `old_string`: `选中文本`（原样，含所有换行空格）
   - `new_string`: `[[<concept_name>]]`
   - `replace_all`: false

**失败处理**（不抛错，继续 Step 6）：
- 选中文本未找到 → 摘要 `✗ 源笔记替换失败: 选中文本未找到`
- 多次匹配 → Edit 默认只替换首个；摘要附 `⚠ 源笔记选中文本出现多次，仅替换首个`

### Step 6 · 更新或创建 index.md

**目标路径**：`wiki/canvases/<subject>/index.md`

#### 6a · 若存在

1. 用 `Read` 读全文
2. 更新 frontmatter：
   - `doc_count: N` → `doc_count: N+1`
   - 无 `doc_count` → 初始化为 `doc_count: 1`
3. 更新 body：
   - 有 `## Concepts` → 段尾 append `- [[<concept_name>]] — extracted, weak (0.30)`
   - 无 `## Concepts` → 文件末追加 `\n## Concepts\n- [[<concept_name>]] — extracted, weak (0.30)\n`
4. 用 `Write` 工具覆盖

#### 6b · 若不存在（auto-create）

用 `Write` 写入骨架（替换 `<subject>`、`<concept_name>`、`<ISO>`）：

```
---
type: board_index
subject: <subject>
doc_count: 1
created_at: <ISO 8601>
---

# <subject> 原白板

## Concepts
- [[<concept_name>]] — extracted, weak (0.30)

## Recent Activity
- <ISO>: <concept_name>.md created via /ai-linked-doc
```

记录 `doc_count_after`（= 原 N+1 或 1）。

### Step 7 · 返回摘要（必须 3 行 ✓ 或 ✓/✗/⚠ 组合）

**成功路径**（必须 3 行 ✓，不得缺任何一行）：
```
✓ <concept_name>.md 已创建 (wiki/canvases/<subject>/)
✓ 源笔记 [[<source_stem>]] 已替换为 [[<concept_name>]]
✓ index.md (<subject>) 已更新 (doc_count → <N>)
```

**部分失败示例**：
```
✓ Eigenvalues.md 已创建
✗ 源笔记替换失败: 选中文本未找到
⚠ index.md (math240) 已更新 (doc_count → 3)
请手动在源笔记插入 [[Eigenvalues]] wikilink。
```

---

## ✅ 执行自检清单（Step 7 返回摘要前必 tick 全部）

```
[ ] Step 4 写的 new_file_path 开头是 "wiki/canvases/"（不是 wiki/concepts/ 或其他）
[ ] Step 5 实际调了 Edit 工具（不是心算 / 不是写死）
[ ] Step 6 index.md 路径 = wiki/canvases/<subject>/index.md
[ ] 返回的摘要有 3 行（成功）或 ✓/✗/⚠ 组合（部分失败）
[ ] 没有在 `## 关联概念` 列捏造的 [[XX]] 指向未创建的文件
[ ] generated_md frontmatter 无 related_concepts / tags 数组字段
```

若任一 ☐ 未勾 → 回溯对应 Step 修复后重新执行。

---

## 约束总结

- **不调 Graphiti**（下游 Story）
- **不触碰 `raw/` 目录**
- **不加 `tags:` frontmatter**
- **生成内容不含 AI 自我介绍**
- **不做 Modal / Settings UI**
- **不做 debounce queue**（Skill 同步执行无并发）

---

## 错误场景速查

| 症状 | Skill 响应 |
|---|---|
| 消息无 `/ai-linked-doc` 前缀且无三字段 | 拒绝执行，提示用户用 plugin 触发 |
| `学科 == "unknown"` 或源路径不在 canvases | AskUserQuestion 降级询问 subject |
| 文件重名 ≤9 次 | 自动加 `_N` 后缀 |
| 文件重名 >9 次 | 摘要返回错误 `✗ 文件名冲突过多 (9+ 重名)` |
| 选中文本在源笔记未找到 | 摘要 `✗ 源笔记替换失败`，不中断 Step 6 |
| 选中文本多次出现 | 仅替换首个，摘要 `⚠` 提示 |
| index.md doc_count 非整数 | Read + Write 覆盖时强转整数 |
| 源笔记路径 = unknown 或不存在 | 跳过 Step 5，摘要 `⚠` |
| 自检清单有 ☐ 未勾 | 回溯对应 Step 修复 |

---

## 参考

- Story spec：`_bmad-output/implementation-artifacts/epic-1/1-17-ai-linked-doc.md`
- Canvas plugin 触发 handler：`frontend/obsidian-plugin/src/main.ts` 的 `handleAILinkedDoc`
- Prompt 组装：`frontend/obsidian-plugin/src/ai-linked-doc.ts` 的 `buildAIDocPrompt`
- 架构锚定：`planning-artifacts/architecture.md:113`（Mode D = Claude Code CLI 订阅）
- System Prompt 来源：`research/obsidian-qa-round3-claude-answers-2026-04-14.md:141-177`
