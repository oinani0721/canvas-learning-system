---
name: ai-linked-doc
description: "当用户消息以 /ai-linked-doc 开头（通常由 Canvas plugin 通过 Cmd+Shift+D 触发 + 剪贴板注入），必须调用此 Skill 派生新节点。v4.5 扁平架构 + 关系类型双写 + 派生描述三处落地：新节点写到 vault 根 节点/<concept>.md 扁平池；同时更新 原白板/<active_board>.md 的 ## Concepts section + 源笔记选中文本替换为 [[节点/<concept>]] wikilink + 紧跟 [!relation/<type>]+ callout（视觉，含用户描述）；新节点 frontmatter relationships[] 字段（机器可读，含 description）；用户描述注入到正文生成 prompt 让 AI 据此生成。严禁写到弃用的 wiki/canvases/ 或 wiki/concepts/ 路径。"
argument-hint: "[由 Canvas plugin 从剪贴板注入包装好的 prompt]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Bash
  - AskUserQuestion
  - mcp__canvas-learning-mcp__get_board_manifest
model: sonnet
---

<!-- ROUTING:BEGIN v1 -->
## ⛔ 检索平面协议 v1（RAG-S2.6 导航改造 · 先看目录再精读）

⛔ **动手前先判定平面**，判错 = 白烧上下文（vault 越大越明显）。四个平面，每个只有一个正确的第一动作：

| 平面 | 什么问题属于它 | 第一动作（唯一正确） |
|---|---|---|
| **STRUCTURE** | 这块板拆了哪些节点 / 谁派生自谁 / 哪个最该考 / 掌握度与考察历史 | **1 次** `get_board_manifest` —— 不先 Grep、不 Read 白板全文 |
| **SEMANTIC** | 「关于 X 的内容在哪」「X 和 Y 什么关系」 | 先用 manifest 成员清单**限域**，再在域内检索；⛔ 不得退化成全库 `**/*.md` 裸扫 |
| **CONTENT** | 已知是哪个文件，要它的正文 | 直接 `Read` / `Grep` 该文件 —— **不过 manifest**（manifest 按设计不含正文） |
| **EXAM** | 出题 / 评分 / 检验白板 | 受 HARD-ISO 信息隔离约束：结构走 manifest `view:"exam"`，正文一律不进上下文 |

**硬约束**

- **HARD-NAV-1**：`get_board_manifest` **一次调用即返回该板全部结构**（成员 + 派生原因 + 掌握度四态 + 占位标记 + 选点秩 + 考察历史 + 题面摘句）。同一板同一轮**不得调第 2 次**。
- **HARD-NAV-2**：manifest **不含节点正文**。要正文 → 转 CONTENT 平面，别指望 manifest 给。
- **HARD-NAV-3**：每处 manifest 调用**必须**配成对 `<!-- FALLBACK:BEGIN/END -->` 降级块。失败 / 超时 / 空结果 / 后端未起 → **静默**退回块内写明的原路径，**离线可用不破**，且不因此中止任务。
- **HARD-NAV-4**：本块在 8 份 skill 里**逐字节相同**，由 `backend/scripts/check_skill_routing_block.py` 校验。要改就 8 份一起改。
<!-- ROUTING:END v1 -->

<!-- PLANE-BINDING v1
primary_plane: STRUCTURE
uses_structure: yes
structure_tool: mcp__canvas-learning-mcp__get_board_manifest
manifest_view: study
fallback_path: Glob 原白板/*.md 枚举候选板（Step 1 归属级联第 4 级的 FALLBACK 块）
-->

# AI 双链文档 Skill v4.5（Canvas Learning System · 扁平架构 + 关系双写 + 派生描述三处落地）

## ⛔⛔⛔ CRITICAL TRIGGER & HARD CONSTRAINTS（round-11 扁平 + Story 1.17 v2.5）

**识别触发**：
- 若用户消息以 `/ai-linked-doc` 开头 → **立即调用本 Skill**
- 消息一般由 Canvas plugin 的 Cmd+Shift+D 生成 + 剪贴板注入，含 4 个字段：`选中文本` / `源笔记路径` / `活动白板` / `关系类型`

**执行硬约束**（v4.5 扁平架构 + 关系双写 + 派生描述三处落地）：

1. **新节点 md 必须写到 `节点/<concept>.md`**（vault 根下扁平池）
2. **严禁写到 `wiki/canvases/`、`wiki/concepts/` 或其他弃用路径**
3. **更新白板 md** 在 `原白板/<active_board>.md`，不再是 `wiki/canvases/<subject>/index.md`
4. **subject 字段 vault 级透明**：读 `.canvas-config.yaml`，不再向用户问；白板/节点 md 的 frontmatter 都不含 subject 字段
5. **不得自由发挥** / **不得捏造 wikilink** / **节点池重名时加 `_N` 后缀**（最多 `_9`）
6. **关系类型双写硬约束**（v2.4 D1-3 决策 C）：
   - 源笔记 wikilink 后必须紧跟 `> [!relation/<type>]+ ...` callout（视觉提示）
   - 新节点 frontmatter 必须含 `relationships:` 数组字段（机器可读）
   - 7 类合法 key：`prerequisite / depends_on / refines / extends / example_of / contradicts / related_to`
   - 收到非 7 类合法 key → 回落 `related_to` 不抛错
7. **派生描述三处落地硬约束**（v2.5 D1-5 决策 C）：
   - 解析 `派生描述:` 行；若值是 `(用户留空)` → 三处落地都跳过（callout body 不加描述行 + frontmatter 不写 description 字段 + 不注入 AI prompt 描述指令）
   - 若值非空非占位 → 三处落地：
     - **(1) 源笔记 callout body** 加一行 `> 你的派生意图: <description>`
     - **(2) 新节点 frontmatter** `relationships[0].description: "<description>"`
     - **(3) AI prompt 注入** 让 Step 3 概念生成器用用户的描述指导 `## 核心概念` 的角度
   - **⛔ description ≠ AI 自由发挥**：AI 必须忠实表达用户意图，不得忽略或反着写
8. **必须返回 Step 8 的回执**（✓/✗/⚠ 组合 + 关系类型 + 描述落地三勾）
9. **必须按 Step 1→8 顺序执行**，不得跳步

---

## 执行步骤（v4.4 扁平架构 + 关系类型双写）

### Step 1 · 解析输入

从用户消息抽 5 个字段：
- **`选中文本`**：多行可能，从 `选中文本:` 行后读到 `源笔记路径:` 行前
- **`源笔记路径`**：相对 vault 根（例 `原白板/CS 61B.md` 或 `节点/recursion.md` 或 `raw/lecture.md`）
- **`活动白板`** *(plugin 可能注入，可选)*：例 `CS 61B 数据结构`
- **`关系类型`** *(v2.4 plugin 必传)*：形如 `refines (细化 (refines))`，从中提取 key（前空格前的部分）
  - 7 类合法 key：`prerequisite / depends_on / refines / extends / example_of / contradicts / related_to`
  - 解析失败 / 不在 7 类 → 回落 `related_to` + 在回执中标记 `⚠ 关系类型回落`
- **`派生描述`** *(v2.5 plugin 必传)*：自由文本，可能是 `(用户留空)` 占位或真实描述
  - 占位 `(用户留空)` → 设 `description = ""`（下游三处落地都跳过）
  - 非占位 → 设 `description = <原值 trim>`（下游三处落地全部启用）

### Step 2 · 确定 `active_board`（新节点要 append 到哪个白板 md）

优先级（v2.6 加规则 2.5 节点继承）：
1. **plugin 注入的"活动白板"字段**（如有）→ 直接用
2. **源笔记路径在 `原白板/<board>.md`** → `active_board = basename 去扩展名`
2.5. **源笔记路径在 `节点/<concept>.md`**（v2.6 节点派生节点继承规则）：
     - 用 `Read` 读源节点 md frontmatter
     - 提取 `source_board` 字段（实际格式 `"[[原白板/<board>]]"`）
     - 用 regex 匹配 `原白板/([^\]\|]+?)(?:\.md)?(?:\|[^\]]*)?` 提取 board name
     - 命中 → `active_board = <提取的 board name>`，**不弹 AskUserQuestion**
     - 未命中（源节点 frontmatter 无 source_board / 格式异常）→ 走规则 3
3. **`.canvas-config.yaml` 的 `active_board:` 字段** → 读取
4. **AskUserQuestion**（RAG-S2.6：候选板改用 **1 次列板 manifest** 枚举，STRUCTURE 平面）：
   - 调 `get_board_manifest{ view: "study" }`（不传 `board_id`）→ `boards[]`
   - 选项文案带上规模，让用户看得出该往哪归：
   > 新派生的节点要归属哪个原白板？
   >
   > 已有白板：
   > - `CS 61B 数据结构`（2 个节点，1 张检验白板）
   > - `线性代数`（0 个节点）
   > - ...
   > - 或"新建" → 建议你先用 `/configure-whiteboard` 建白板
   - ⛔ 选项用 `board_id`（文件名 stem）作实际值，`board_name` 只用于显示——两者可以不等（真实反例：文件 `CS 61B.md` 的 `board_name: CS 61B 数据结构`）。

<!-- FALLBACK:BEGIN Step 2 规则 4 候选板枚举降级 -->
manifest 不可用 → **静默退回** `Glob 原白板/*.md` 枚举文件名（拿不到成员数/检验白板数，选项就只列板名）。归属判定语义不变。
<!-- FALLBACK:END -->

若仍无值 → 返回错误 `✗ 无法确定活动白板，请先 /configure-whiteboard 建一个`，停止执行。

### Step 3 · 生成概念文档（三段式 + relationships[] + 用户描述指导）

用 System Prompt 模板生成概念 md 完整内容。**v2.5 关键**：若 `description` 非空，必须把它注入 prompt 让生成器据此调整 `## 核心概念` 的角度（不是机械重复用户描述，而是让 AI 写出符合用户派生意图的内容）。

```
你是 Canvas Learning System v4.5 扁平架构 + 关系双写 + 派生描述三处落地的概念文档生成器。

任务：基于"选中文本"生成结构化概念笔记，frontmatter 必须含 relationships[] 字段（含 description 子字段当且仅当用户描述非空）。

【用户派生意图】（仅当 description 非空时注入此段）：
{description}

⚠️ 你必须忠实表达用户意图：`## 核心概念` 的角度要呼应用户描述的"为什么派生"，
   不要忽略用户意图自由发挥；不要简单复读描述文字。

输出格式（完整 md，含 frontmatter）：

---
type: concept
mastery_score: 0.30
created_at: <ISO 8601>
source_note: "[[{源笔记 stem}]]"
source_board: "[[原白板/{active_board}]]"
created_from: ai_linked_doc
up: "[[{源笔记 stem}]]"
derived-from: "[[{源笔记 stem}]]"
relationships:
  - type: {关系类型 key}
    target: "[[{源笔记 stem}]]"
    derived_at: <ISO 8601, 与顶部 created_at 同值>
    {source_mastery: 源笔记 frontmatter 有 mastery_score 时加 → source_mastery_at_derivation: <该值>}
    {confusion: 源笔记选中文本附近有 [!question]/[!error] 批注时加 → confusion: "<最近一条批注原文, ≤100 字>"}
    {description 非空时加: description: "{description}"}
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
- ⛔ 严禁在 `## 关联概念` 列其他"可能相关"的概念（**反幻觉硬约束 v2.3**）
  - 只列 `[[源笔记 stem]]` 一条
  - 不列"相邻课题" / "先修知识" / "未来扩展" / "可能用到"等虚构节点
  - "相关"由用户手写 wikilink 或未来 Graphiti 推断（**不由 AI**）
- ⛔ frontmatter 无 subject 字段（vault 级透明）
- ⛔ frontmatter 无 tags 数组（非 MVP）
- ✅ frontmatter `up:` 和 `derived-from:` 必填**真实源笔记**（基于 Skill 派生动作，**非 AI 编造的依赖**）→ Breadcrumbs 插件可自动渲染矩阵 / 树形视图
- ✅ frontmatter `relationships:` 数组必含 1 项 `{type: <关系类型 key>, target: [[<源笔记 stem>]]}`（v2.4 D1-3 双写之"机器可读"半边）
- ⛔ 关系类型 key 必须是 7 类合法值之一（解析失败时由 Skill 回落 `related_to`，**不**由生成器自行选择）
- ✅ 若 description 非空：frontmatter `relationships[0].description` 必填用户描述原文（不裁剪，不复读到正文）
- ✅ **理解快照随边（批次4' 3-1/3-2，MEM-FLYWHEEL）**：`relationships[0]` 必含 `derived_at`（拆分时序）；源笔记有 `mastery_score` 时加 `source_mastery_at_derivation`（派生瞬间你对源概念的掌握档——「当时为什么困惑」的一半）；选中文本前后 10 行内有 `[!question]`/`[!error]` 批注时加 `confusion`（最近一条原文 ≤100 字——另一半）。投影 sync 会把这三个字段透传入 CANVAS_EDGE 永久留档
- ✅ **学习事件落日志（批次4'，MEM-FLYWHEEL）**：新节点写入成功后，`Bash` 追加一条事件（⛔ 逐字模板，仅替换两处 `<>`）：`python3 -c "import json,os,sys; ev='<vault绝对路径>/learning_events.jsonl'; evid='derive:<新节点名>'; seen=os.path.exists(ev) and any(json.dumps(evid,ensure_ascii=False) in l for l in open(ev,encoding='utf-8')); from datetime import datetime,timezone; ts=datetime.now(timezone.utc).isoformat(); seen or open(ev,'a',encoding='utf-8').write(json.dumps({'event_id':evid,'event_version':1,'event_type':'node_derived','node_id':'<新节点名>','recorded_at':ts,'effective_at':ts,'payload':{}},ensure_ascii=False)+'\n')"`（写失败不阻断派生）
- ⛔ 若 description 为空：frontmatter `relationships[0]` 不写 `description` 字段（不要 description: ""）
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

### Step 6 · 替换源笔记选中文本为 wikilink + 关系 callout（v2.4 D1-3 + v2.5 D1-5 双写视觉半边）

- 用 `Read` 读源笔记全文
- 用 `Edit`：
  - `file_path`: `{源笔记路径}`
  - `old_string`: `{选中文本}`（原样含换行）
  - `new_string` 模板（按 description 是否为空走两条路径之一）：

  **路径 A · description 为空（5 行模板）**：
  ```
  [[节点/{concept_name}]]

  > [!relation/{关系类型 key}]+ 派生关系: {关系类型中文标签}
  > 上方 wikilink 节点派生自这段文本，关系类型为 **{关系类型 key}**。
  ```

  **路径 B · description 非空（6 行模板，多 1 行用户意图）**：
  ```
  [[节点/{concept_name}]]

  > [!relation/{关系类型 key}]+ 派生关系: {关系类型中文标签}
  > 上方 wikilink 节点派生自这段文本，关系类型为 **{关系类型 key}**。
  > 你的派生意图: {description}
  ```

  - `replace_all`: false

> 关系类型中文标签映射（不要写英文 key 作 label）：
> - `prerequisite` → `先修`
> - `depends_on` → `依赖`
> - `refines` → `细化`
> - `extends` → `扩展`
> - `example_of` → `例子`
> - `contradicts` → `反驳`
> - `related_to` → `相关`

**失败处理**（不抛错，继续 Step 7）：
- 选中文本未找到 → 摘要 `✗ 源笔记替换失败: 选中文本未找到`
- 多次出现 → 仅替换首个 + 摘要 `⚠`

### Step 7 · 更新白板 md（RAG-S2.6：`## Concepts` 改由同步脚本重算）

⛔ **`## Concepts` 已降级为只读派生物**（RAG-S2.6 T2，用户 2026-08-11 裁定）：
真相源是新节点 frontmatter 的 `source_board`（Step 5 已写入）。本 Skill
**不再** append `- [[节点/...]]` 行、**不再**手动 `doc_count += 1` ——
手写进 sentinel 之间的行会在下次同步时被覆盖，手改的 `doc_count` 会被重算掉。

- `board_md_path = 原白板/{active_board}.md`
- **若 board_md 不存在**（罕见，用户先派生后建白板）→ 不 auto-create，返回
  `⚠ 原白板/{active_board}.md 不存在，请先 /configure-whiteboard 建白板`
- 用 `Edit` 在 `## Recent Activity` section append（这段仍由本 Skill 维护，脚本不碰）：
  ```
  - {ISO}: Extracted [[节点/{concept_name}]] via /ai-linked-doc from [[{源笔记 stem}]]（关系: {关系类型 key}）
  ```
- 然后 **`Bash` 跑一次目录同步**（`## Concepts` 行 + `doc_count` 都由脚本从
  `source_board` 重算，掌握度/已考次数取当前真值，不再写死 `weak (0.30)`）：
  ```bash
  python3 .claude/scripts/sync_board_concepts.py --board "{active_board}"
  ```
  - 输出 `~ {active_board}  (N 成员, 需更新)` → 新节点已进目录、`doc_count → N`

<!-- FALLBACK:BEGIN Step 7 目录同步降级 -->
**⛔ 同步失败一律不阻断派生**（节点 md + 源笔记 wikilink 已落盘，才是真正的产物）：
脚本不存在 / 非零退出 / 报 `无 ## Concepts 段` → 只在回执标注
`⚠ 白板目录同步失败，节点已建（下次任一次同步会自动补齐）`，
**不要**退回手写 `- [[节点/...]]` 行 —— 手写行与脚本重算冲突，且下次同步即被覆盖。
<!-- FALLBACK:END -->

### Step 8 · 返回回执（4 行 ✓ 或 ✓/✗/⚠ 组合 + 关系类型）

**D4-1 决策**：Skill **不**主动开新 tab（不调 obsidian:// URI / 不让 plugin 调 workspace.openLinkText），用户**留在源笔记**继续阅读。回执文本含 wikilink 让用户可**手动 Cmd+Click 跳转**（不强制）。

**成功路径（v2.5 5 行格式 · description 非空时 +1 行）**：
```
✓ 节点/{concept_name}.md 已创建（扁平池，frontmatter relationships: [{type: {关系类型 key}{描述非空时: , description: ...}}]）
✓ 源笔记 [[{源笔记 stem}]] 已替换为 [[节点/{concept_name}]] + [!relation/{关系类型 key}]+ callout{描述非空时: + 你的派生意图行}
✓ 原白板/{active_board}.md 目录已重算（## Concepts 收录新节点，doc_count → N，关系: {关系类型 key}）
关系类型: {关系类型 key} ({关系类型中文标签})
派生意图: {description 或 (留空)}

💡 你想看新节点 → Cmd+Click 上面的 [[节点/{concept_name}]] 跳转（不强制，可继续读源笔记）
```

**关系类型回落**（plugin 传的 key 不在 7 类）：
```
⚠ 关系类型回落: 收到非法 key '{原值}'，已回落 'related_to'（请用户检查 plugin 版本）
✓ 节点/{concept_name}.md 已创建
✓ 源笔记替换 + callout 完成（关系: related_to）
✓ 原白板更新完成
```

**部分失败**：
```
✓ 节点/{concept_name}.md 已创建
✗ 源笔记替换失败: 选中文本未找到（用户可能在等待期间改了文件）
⚠ 原白板/{active_board}.md 已更新
请手动在源笔记插入 [[节点/{concept_name}]] wikilink + [!relation/{key}]+ callout
```

---

## 执行自检清单（Step 8 回执前必 tick）

```
[ ] Step 1 关系类型 key 已解析；如非 7 类合法值 → 回落 related_to + 回执标 ⚠ 回落
[ ] Step 1 派生描述已解析；占位 (用户留空) → description=""，否则 trim 后保留
[ ] Step 5 new_file_path 以 "节点/" 开头（非 wiki/canvases/ 或其他）
[ ] generated_md frontmatter 无 subject 字段 + 无 tags 数组
[ ] generated_md frontmatter 含 relationships: [{type: <key>, target: [[源笔记]]}]（v2.4 双写机器可读半边）
[ ] description 非空 → relationships[0] 含 description 子字段（v2.5 D1-5 落地点 2）
[ ] description 为空 → relationships[0] 不含 description 字段（不要写 description: ""）
[ ] description 非空 → Step 3 prompt 含【用户派生意图】段（v2.5 D1-5 落地点 3）
[ ] generated_md ## 关联概念段只列 [[源笔记 stem]] 一条，不捏造其他
[ ] Step 6 实际调了 Edit 工具 + replace_all: false
[ ] Step 6 new_string 含 wikilink + 紧跟 [!relation/<key>]+ callout（v2.4 双写视觉半边）
[ ] description 非空 → Step 6 callout body 多 1 行 `> 你的派生意图: <description>`（v2.5 D1-5 落地点 1）
[ ] Step 7 白板 md 路径 = 原白板/{active_board}.md
[ ] Step 7 ⛔ 未手写 `- [[节点/...]]` 行、未手改 doc_count —— 只跑了 sync_board_concepts.py --board
[ ] Step 7 同步脚本输出里新节点已出现在成员数里（N 已含它）；失败则回执已标 ⚠ 且节点仍已落盘
[ ] 回执 5 行（关系类型行 + 派生意图行）或 ✓/✗/⚠ 组合
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
