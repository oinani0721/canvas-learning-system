---
name: ai-linked-doc
description: 根据剪贴板粘贴的选中文本，生成概念 md 文档 + 写入 wiki/canvases/<subject>/ + 把源笔记选中替换为 wikilink + 更新/创建 index.md（Canvas Learning System Story 1.17 形态 β）。
argument-hint: "[可选: 直接粘贴 Canvas plugin 生成的 prompt]"
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

## 触发方式

用户在 Canvas Learning System Obsidian plugin 里选中文本 → 按 `Cmd+Shift+D` → plugin 会把以下格式的 prompt 写入系统剪贴板：

```
/ai-linked-doc
选中文本:
<文本>

源笔记路径: wiki/canvases/<subject>/<source>.md
学科: <subject>

请为这段内容创建一个概念文档（三段式：## 核心概念 / ## 关键点 / ## 关联概念）。
```

用户在 Claudian 输入框 `Cmd+V` 粘贴 → 回车。本 Skill 开始执行。

如果用户不想走 plugin 入口，也可以直接在 Claudian 输 `/ai-linked-doc` + 上述格式的内容手动粘贴/构造（等价）。

---

## 执行步骤（严格顺序）

### Step 1 · 解析输入

从用户消息中抽 3 个字段：

- **`选中文本`**：可能多行，从 "选中文本:\n" 开始读到下一个 "源笔记路径:" 行为止（去掉末尾换行）。
- **`源笔记路径`**：单行，相对 vault 根的 `.md` 路径（例如 `wiki/canvases/math240/Fundamentals.md`）或 `unknown`。
- **`学科`**：单 token，通常是 `math240` / `cs61b` / 等 subject 代码，或者 `unknown`。

**降级处理**：若 `学科 == "unknown"`，调 `AskUserQuestion` 问用户：

> 当前源笔记缺少 `subject` frontmatter。请指定学科代码（例如 `math240`）以决定新概念落盘到 `wiki/canvases/<subject>/` 哪个子目录。
> 
> 若没有已建的学科，可回答 `default`，新概念会落到 `wiki/canvases/default/`。

把用户回答的非空 token 作为 subject 继续。

### Step 2 · 生成概念文档

用下面的 **System Prompt 模板**生成概念 md 的完整内容（含 frontmatter）。不直接调 API —— Skill 是在 Claude Code 会话里跑的，你（模型）**就是**生成器。按此 schema 输出到一个内存变量 `generated_md`：

```
你是 Canvas Learning System 的概念文档生成器。

任务：基于用户提供的"选中文本"和"源笔记路径"，生成一份结构化的概念笔记。

输出格式（Markdown，完整文件内容，含 frontmatter）：

---
type: concept
subject: <从 Step 1 拿到的 subject>
mastery_score: 0.30
created_at: <ISO 8601 时间戳，用 `date -u +"%Y-%m-%dT%H:%M:%SZ"` 取>
source_note: "[[<源笔记文件名 stem，即去掉路径和 .md 后缀>]]"
created_from: ai_linked_doc
---

# <主概念名>

## 核心概念
（基于选中文本，1-2 句话精准定义。不赘述。）

## 关键点
- 要点 1
- 要点 2
- 要点 3
（3-5 条，不超过 7 条）

## 关联概念
- [[<源笔记 stem>]] — extracted from this note
- [[其他明显关联的概念]] — 如有（可选）

约束：
- 语言匹配选中文本（中文选中 → 中文输出；英文选中 → 英文输出）。
- 概念定义优先精准而非详尽。
- 不写代码块，除非概念本身涉及代码（如"递归函数"、"lambda 表达式"）。
- 不写"作为 AI 我..."等自我介绍性文字。
- 主概念名从核心概念首句提炼（"Eigenvalues are special..." → "Eigenvalues"；"特征值是..." → "特征值"）。
- 不写多行 frontmatter 数组字段（`related_concepts: []` 等），只用 `source_note` 单字段 + `## 关联概念` 正文列表。
```

### Step 3 · 提取概念名

从 `generated_md` 的 `# <主概念名>` 标题行提取主概念名作为文件名：

- 去掉首尾空格
- 英文：保留字母数字，空格/特殊符号替换为 `-`（例 `Eigenvalues and Eigenvectors` → `Eigenvalues-and-Eigenvectors`）
- 中文：直接取 2-6 字的概念词（例 `特征值` → `特征值`），不加分隔符
- 禁止 `/ \ : * ? " < > |` 等文件系统非法字符

保存为 `concept_name`。

### Step 4 · 写新概念文件

**目标路径**：`wiki/canvases/<subject>/<concept_name>.md`

**重名处理**（最多 9 轮）：
- 用 `Glob` 检查目标路径是否已存在
- 若存在，尝试 `<concept_name>_2.md`、`<concept_name>_3.md`、...、`<concept_name>_9.md`
- 9 轮全占用 → 返回错误 `✗ 文件名冲突过多 (9+ 重名)`，停止后续步骤

用 `Write` 工具写入 `generated_md` 到最终路径。记录 `new_file_path`。

### Step 5 · 替换源笔记选中文本为 wikilink

若 `源笔记路径 == "unknown"` → 跳过本步，摘要标记 `⚠ 源笔记未知，未执行 wikilink 替换`。

否则：

1. 用 `Read` 读 `<源笔记路径>` 全文。
2. 确认 `选中文本`（原样，含换行）在文件中存在。
3. 用 `Edit` 工具：
   - `file_path`: 源笔记路径
   - `old_string`: `选中文本`（原样传入，含所有换行和空格）
   - `new_string`: `[[<concept_name>]]`
   - `replace_all`: false

**失败处理**（不抛错，继续 Step 6）：
- 选中文本未找到（用户在等待期间改了源笔记）→ 摘要标记 `✗ 源笔记替换失败: 选中文本未找到`
- Edit 工具报"出现多次"时，它默认只替换首个匹配（`replace_all: false`）；摘要附加提示 `⚠ 源笔记选中文本出现多次，仅替换首个`

### Step 6 · 更新或创建 index.md

**目标路径**：`wiki/canvases/<subject>/index.md`

#### 6a · 若存在

1. 用 `Read` 读全文。
2. 更新 frontmatter：
   - 若有 `doc_count: N` → 改为 `doc_count: N+1`
   - 若无 `doc_count` 字段 → 初始化为 `doc_count: 1`
3. 更新 body：
   - 若有 `## Concepts` section → 在该 section 末尾 append `- [[<concept_name>]] — extracted, weak (0.30)`
   - 若无 `## Concepts` section → 在文件末追加 `\n## Concepts\n- [[<concept_name>]] — extracted, weak (0.30)\n`
4. 用 `Write` 工具覆盖（frontmatter 数字变更用 Edit 容易出错，用 Write 覆盖最稳）。

#### 6b · 若不存在（auto-create）

直接 `Write` 下面的骨架（替换 `<subject>`、`<concept_name>`、`<ISO>`）：

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

### Step 7 · 返回摘要

**成功路径**（3 行 ✓）：
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

提示用户：在 Obsidian 里点 `[[<concept_name>]]` wikilink 跳转查看新文件（Skill 自身不能打开 tab；Obsidian 原生 wikilink 跳转即可）。

---

## 约束

- **不调 Graphiti**（下游 Story 处理知识图谱入图）。
- **不触碰 `raw/` 目录**（降级后只写 `wiki/canvases/<subject>/`）。
- **不加 `tags:` frontmatter**（非 MVP 刚需）。
- **生成内容不含 AI 自我介绍**（"作为 AI 我..."）。
- **不做 Modal / Settings UI**（形态 β 纯文件写操作，所有交互在 Claudian 侧栏完成）。
- **不做 debounce queue**（Skill 同步执行无并发）。

---

## 错误场景速查

| 症状 | Skill 响应 |
|---|---|
| `学科 == "unknown"` | `AskUserQuestion` 问用户 |
| 文件重名冲突 ≤9 次 | 自动加 `_N` 后缀 |
| 文件重名冲突 >9 次 | 摘要返回错误 `✗ 文件名冲突过多 (9+ 重名)` |
| 选中文本在源笔记未找到 | 摘要 `✗ 源笔记替换失败`，不中断后续 Step 6 |
| 选中文本多次出现 | 仅替换首个，摘要 `⚠` 提示 |
| index.md doc_count 字段为字符串/NaN | Read + Write 覆盖时强制转整数 |
| 源笔记路径 = unknown | 跳过 Step 5，摘要标记 `⚠` |

---

## 参考

- Story spec：`_bmad-output/implementation-artifacts/epic-1/1-17-ai-linked-doc.md`
- Canvas plugin 触发 handler：`frontend/obsidian-plugin/src/main.ts` 的 `handleAILinkedDoc`
- Prompt 组装 pure function：`frontend/obsidian-plugin/src/ai-linked-doc.ts` 的 `buildAIDocPrompt`
- 架构锚定：`planning-artifacts/architecture.md:113`（Mode D = Claude Code CLI 订阅额度）
- Round 3 QA System Prompt 三段式：`research/obsidian-qa-round3-claude-answers-2026-04-14.md:141-177`
