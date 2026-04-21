---
name: ai-linked-doc
description: "当用户消息以 /ai-linked-doc 开头（通常由 Canvas plugin 通过 Cmd+Shift+D 触发 + 剪贴板注入），必须调用此 Skill 派生新节点。v4 扁平架构：新节点写到 vault 根 节点/<concept>.md 扁平池；同时更新 原白板/<active_board>.md 的 ## Concepts section + 源笔记选中文本替换为 [[节点/<concept>]] wikilink。严禁写到弃用的 wiki/canvases/ 或 wiki/concepts/ 路径。"
argument-hint: "[由 Canvas plugin 从剪贴板注入包装好的 prompt]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Bash
  - AskUserQuestion
model: sonnet
---

# AI 双链文档 Skill v4（Canvas Learning System · 扁平架构）

## ⛔⛔⛔ CRITICAL TRIGGER & HARD CONSTRAINTS（round-11 扁平架构）

**识别触发**：
- 若用户消息以 `/ai-linked-doc` 开头 → **立即调用本 Skill**
- 消息一般由 Canvas plugin 的 Cmd+Shift+D 生成 + 剪贴板注入，含 `选中文本` + `源笔记路径` + `活动白板` 字段

**执行硬约束**（v4 扁平架构）：

1. **新节点 md 必须写到 `节点/<concept>.md`**（vault 根下扁平池）
2. **严禁写到 `wiki/canvases/`、`wiki/concepts/` 或其他弃用路径**
3. **更新白板 md** 在 `原白板/<active_board>.md`，不再是 `wiki/canvases/<subject>/index.md`
4. **subject 字段 vault 级透明**：读 `.canvas-config.yaml`，不再向用户问；白板/节点 md 的 frontmatter 都不含 subject 字段
5. **不得自由发挥** / **不得捏造 wikilink** / **节点池重名时加 `_N` 后缀**（最多 `_9`）
6. **必须返回 Step 7 的回执**（✓/✗/⚠ 组合）
7. **必须按 Step 1→7 顺序执行**，不得跳步

---

## 执行步骤（v4 扁平架构）

### Step 1 · 解析输入

从用户消息抽 3 个字段：
- **`选中文本`**：多行可能，从 `选中文本:` 行后读到 `源笔记路径:` 行前
- **`源笔记路径`**：相对 vault 根（例 `原白板/CS 61B.md` 或 `节点/recursion.md` 或 `raw/lecture.md`）
- **`活动白板`** *(plugin 可能注入，可选)*：例 `CS 61B 数据结构`

### Step 2 · 确定 `active_board`（新节点要 append 到哪个白板 md）

优先级：
1. **plugin 注入的"活动白板"字段**（如有）→ 直接用
2. **源笔记路径在 `原白板/<board>.md`** → `active_board = basename 去扩展名`
3. **`.canvas-config.yaml` 的 `active_board:` 字段** → 读取
4. **AskUserQuestion**：
   > 新派生的节点要归属哪个原白板？
   > 
   > 已有白板（从 `Glob 原白板/*.md` 枚举）：
   > - `CS 61B 数据结构.md`
   > - `线性代数.md`
   > - ...
   > - 或"新建" → 建议你先用 `/configure-whiteboard` 建白板

若仍无值 → 返回错误 `✗ 无法确定活动白板，请先 /configure-whiteboard 建一个`，停止执行。

### Step 3 · 生成概念文档（三段式）

用 System Prompt 模板生成概念 md 完整内容：

```
你是 Canvas Learning System v4 扁平架构的概念文档生成器。

任务：基于"选中文本"生成结构化概念笔记。

输出格式（完整 md，含 frontmatter）：

---
type: concept
mastery_score: 0.30
created_at: <ISO 8601>
source_note: "[[{源笔记 stem}]]"
source_board: "[[原白板/{active_board}]]"
created_from: ai_linked_doc
---

# <主概念名>

## 核心概念
（1-2 句精准定义）

## 关键点
- 要点 1
- 要点 2
- 要点 3
（3-5 条）

## 关联概念
- [[{源笔记 stem}]] — extracted from this note

约束：
- 语言匹配选中文本（中文→中文；英文→英文）
- 不写代码块，除非概念涉及代码
- 不写"作为 AI 我..."
- 主概念名从核心概念首句提取
- ⛔ 严禁在 `## 关联概念` 列其他"可能相关"的概念（幻觉防线）
- ⛔ frontmatter 无 subject 字段（vault 级透明）
- ⛔ frontmatter 无 tags 数组（非 MVP）
```

### Step 4 · 提取概念名 + 节点池路径

从生成内容 `# <主概念名>` 行提取 `concept_name`：
- 英文：保留字母数字，空格/特殊符号 → `-`（如 `Eigenvalues and Eigenvectors` → `Eigenvalues-and-Eigenvectors`）
- 中文：直接用 2-6 字概念词（`特征值` → `特征值`）
- 禁止文件系统非法字符 `/ \ : * ? " < > |`

目标路径：**`节点/{concept_name}.md`**（扁平池）

**重名处理**（节点池一 vault 一学科理论应零冲突）：
- 用 `Glob 节点/{concept_name}.md` 检查
- 已存在 → 加 `_N` 后缀尝试 `节点/{concept_name}_2.md` → ... → `_9.md`
- 9 轮全占 → 返回 `✗ 节点池 9+ 重名，请检查是否概念拆分问题`

### Step 5 · 写新节点文件

用 `Write` 工具写入 `节点/{concept_name}.md`（或 `_N` 后缀版本），内容 = Step 3 的 `generated_md`。

**硬验证**：写前检查 `new_file_path.startsWith("节点/")`，不符合 → 停止返回 `✗ 路径硬约束违反`。

### Step 6 · 替换源笔记选中文本为 wikilink

- 用 `Read` 读源笔记全文
- 用 `Edit`：
  - `file_path`: `{源笔记路径}`
  - `old_string`: `{选中文本}`（原样含换行）
  - `new_string`: `[[节点/{concept_name}]]`（**用完整路径** wikilink，避免 Obsidian 歧义解析）
  - `replace_all`: false

**失败处理**（不抛错，继续 Step 7）：
- 选中文本未找到 → 摘要 `✗ 源笔记替换失败: 选中文本未找到`
- 多次出现 → 仅替换首个 + 摘要 `⚠`

### Step 7 · 更新白板 md 的 ## Concepts section

- `board_md_path = 原白板/{active_board}.md`
- 用 `Read` 读白板 md 全文
- 在 `## Concepts` section 末尾 append：
  ```
  - [[节点/{concept_name}]] — extracted, weak (0.30)
  ```
- 在 `## Recent Activity` section append：
  ```
  - {ISO}: Extracted [[节点/{concept_name}]] via /ai-linked-doc from [[{源笔记 stem}]]
  ```
- 更新 frontmatter `doc_count` += 1（若字段不存在则初始化为 1）
- 用 `Write` 覆盖白板 md

**若 board_md 不存在**（罕见，用户先派生后建白板）：
- 不 auto-create，返回 `⚠ 原白板/{active_board}.md 不存在，请先 /configure-whiteboard 建白板`

### Step 8 · 返回回执（3 行 ✓ 或 ✓/✗/⚠ 组合）

**成功路径**：
```
✓ 节点/{concept_name}.md 已创建（扁平池）
✓ 源笔记 [[{源笔记 stem}]] 已替换为 [[节点/{concept_name}]]
✓ 原白板/{active_board}.md 的 ## Concepts 已添加新节点（doc_count → N）
```

**部分失败**：
```
✓ 节点/{concept_name}.md 已创建
✗ 源笔记替换失败: 选中文本未找到（用户可能在等待期间改了文件）
⚠ 原白板/{active_board}.md 已更新
请手动在源笔记插入 [[节点/{concept_name}]] wikilink
```

---

## 执行自检清单（Step 8 回执前必 tick）

```
[ ] Step 5 new_file_path 以 "节点/" 开头（非 wiki/canvases/ 或其他）
[ ] generated_md frontmatter 无 subject 字段 + 无 tags 数组
[ ] generated_md ## 关联概念段只列 [[源笔记 stem]] 一条，不捏造其他
[ ] Step 6 实际调了 Edit 工具 + replace_all: false
[ ] Step 7 白板 md 路径 = 原白板/{active_board}.md
[ ] Step 7 白板 md ## Concepts append 的 wikilink 用完整路径 "节点/{name}"（不只是 "{name}"）
[ ] 回执 3 行或 ✓/✗/⚠ 组合
```

---

## 弃用路径（绝对禁止）

| 弃用 | v4 替代 |
|---|---|
| `wiki/canvases/<subject>/<concept>.md` | `节点/<concept>.md` |
| `wiki/canvases/<subject>/index.md` 作白板 | `原白板/<board>.md`（由 /configure-whiteboard 建） |
| `wiki/concepts/` | `节点/` |
| 问用户 subject 代码 | vault 级 `.canvas-config.yaml` 透明 |

---

## 错误场景速查

| 症状 | Skill 响应 |
|---|---|
| 无 `/ai-linked-doc` 前缀 | 拒绝执行：`请用 /ai-linked-doc 触发 Skill` |
| 无法确定 active_board | AskUserQuestion 或停止返回错误 |
| 节点池重名 ≤9 次 | 自动 `_N` 后缀 |
| 节点池重名 >9 次 | `✗ 9+ 重名，检查概念拆分` |
| 选中文本未找到 | 摘要 `✗`，不中断 Step 7 |
| 白板 md 不存在 | `⚠ 请先 /configure-whiteboard 建白板` |
| 用户在 `节点/<A>.md` 里选中文本派生新节点 | 新节点也写 `节点/<B>.md`；白板 md 的 Concepts 用 `active_board` 决定 |

---

## 约束

- **不调 Graphiti / 后端 API**（MVP 纯 vault 文件级）
- **不碰 `raw/` 目录**（原始课件保护）
- **不做 Modal / Settings UI**
- **不做 debounce**（Skill 同步）

---

## 参考

- Story spec: `_bmad-output/implementation-artifacts/epic-1/1-17-ai-linked-doc.md`（v4）
- 上游 Skill: `.claude/skills/configure-whiteboard/SKILL.md`（v3 建白板）
- Plugin 触发: `frontend/obsidian-plugin/src/main.ts` 的 `handleAILinkedDoc` (v4)
- Prompt 组装: `frontend/obsidian-plugin/src/ai-linked-doc.ts` 的 `buildAIDocPrompt` (v4)
- CLAUDE.md round-11 扁平架构段
