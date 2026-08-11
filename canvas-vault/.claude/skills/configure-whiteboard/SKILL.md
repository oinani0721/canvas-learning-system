---
name: configure-whiteboard
description: "当用户消息以 /configure-whiteboard 开头时，必须调用此 Skill 建立新原白板。v3 扁平架构：白板 = 原白板/<board>.md 单 md 文件；节点扁平池在 节点/ 文件夹；一 vault 一学科（subject 从 .canvas-config.yaml 读，对用户透明）。两种场景：A 从零建（/configure-whiteboard \"<board-name>\"）；B 从任意 md 派生（/configure-whiteboard from <md-path>）。严禁写到弃用的 wiki/canvases/ 路径。"
argument-hint: "[from <md-path>] 或 [\"<board-name>\"] 或无参（走 AskUserQuestion）"
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
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
fallback_path: Glob 节点/*.md + 逐个 Read frontmatter 找反向引用（Step 4.2 的 FALLBACK 块）
-->

# 原白板配置 Skill v3（Canvas Learning System · 扁平架构）

> **v3.1 (2026-05-01) 修复**：Step 4 加入"反向引用检测"防止盲建重复白板（用户 2026-04-30 批注 bug 修复）。详见 Step 4.2。
>
> ## ⚠️ [DEPRECATED v4.0 起] — 推荐用 plugin 命令 `canvas:configure-whiteboard`
>
> Story 1.19 v4.0（2026-05-01）已把全部 7 步流程迁回 plugin script，零 LLM 调用，<300ms 完成（vs 本 Skill 15-30s LLM 推理）。社区共识：deterministic 工作（文件 I/O / 路径检测 / 反向引用查询）必须脚本，不该 LLM。
>
> **新主路径**：在 obsidian 命令面板搜 `建/配置原白板（v4 全 plugin 脚本）` 或绑快捷键到 `canvas:configure-whiteboard`。
>
> **本 Skill 仍保留作 fallback**（用户在 Claudian 输 `/configure-whiteboard` 时触发），但 v3.1 SKILL 不再积极维护。所有 deterministic 改进只进 plugin 端。

## ⛔⛔⛔ CRITICAL TRIGGER & HARD CONSTRAINTS（round-11 扁平架构）

**识别触发**：
- 若用户消息以 `/configure-whiteboard` 开头 → **立即调用本 Skill**

**执行硬约束**（v3 扁平架构，违反 = 执行错误）：

1. **白板 md 必须写到 `原白板/<board>.md`**（vault 根下的 `原白板/` 文件夹）
2. **节点 md 必须写到 `节点/<concept>.md`**（扁平池，非嵌套子文件夹）
3. **严禁写到 `wiki/canvases/`、`wiki/concepts/` 或其他弃用路径**（v2.1 及以前的旧结构已废弃）
4. **subject 字段对用户透明**：从 vault 根 `.canvas-config.yaml` 读；若文件不存在则让用户一次性创建；**不要**每次问用户
5. **board_name 可以是中文**（例 `CS 61B 数据结构`、`线性代数`）；文件名用 board_name 原文（Obsidian 支持中文文件名）
6. **必须按 Step 1→7 顺序执行**，不得跳步
7. **已有白板保护**：若 `原白板/<board>.md` 已存在 → AskUserQuestion "覆盖重建 / 追加种子笔记 / 换名"
8. **必须返回 Step 7 的回执**（✓/✗/⚠ 组合）

---

## 两种使用场景

### 场景 A · 从零建白板

```
/configure-whiteboard "CS 61B 数据结构"
```
或 `/configure-whiteboard` 无参 → AskUserQuestion 问 board_name

### 场景 B · 从任意 md 派生（Claudian 自动挂载的 active file 优先）

```
/configure-whiteboard from raw/my-recursion-notes.md
```
或 `/configure-whiteboard` 无参 + Claudian context 含 active note 路径不在 `原白板/` → 自动降级场景 B，把 active note 作为种子

---

## 执行步骤（v3 扁平架构）

### Step 1 · 读 vault 级 subject（或首次创建）

- 用 Read 尝试读 `.canvas-config.yaml`
- 若存在 → 解析 `subject: <value>` 字段，记为 `vault_subject`
- 若不存在 → `AskUserQuestion`：
  > 首次使用：本 vault 要学习哪个学科？（subject 代码，例 `cs-61b`、`math240`、`phil-a250`。格式：lowercase + 字母数字 + 连字符。**一 vault 一学科**，后续所有白板/节点都归属这个学科）
- 用户回答后，`Write` 新建 `.canvas-config.yaml`：
  ```yaml
  subject: <用户回答>
  active_board: null
  created_at: <ISO 8601>
  ```
- `vault_subject` 设为用户回答值

### Step 2 · 场景判定 + 参数解析

- 若消息含 `from <path>` → 场景 B，`source_path = <path>`
- 若消息含 `"<board-name>"` 单参数 → 场景 A
- 若消息无参数：
  - 看 Claudian context 有 active note 路径且不在 `原白板/` → 场景 B，source_path = active note
  - 否则 → 场景 A，后面问 board_name

### Step 3 · 确定 board_name

**场景 A**：
- 若 `"<board-name>"` 参数已给 → 直接用
- 若无 → `AskUserQuestion`：
  > 新白板叫什么名字？（board_name 是**显示名**，可中文/空格/大小写，直接作为文件名。例 `CS 61B 数据结构`、`线性代数 II`）

**场景 B**：
- 默认用 source md 的文件名 stem 作为 board_name 候选
- 但仍 `AskUserQuestion` 确认（源文件名可能不是理想白板名）

### Step 4 · 冲突检测（文件级 + 反向引用）

#### Step 4.1 · 文件级冲突

用 `Glob 原白板/{board_name}.md` 检查：

- **已存在** → `AskUserQuestion`：
  > `原白板/{board_name}.md` 已存在。怎么处理？
  > - 覆盖重建（丢弃现有内容）
  > - 追加种子笔记到现有白板的 `## Concepts` section（仅场景 B）
  > - 换名（回 Step 3 重问）
- **不存在** → 继续 Step 4.2

#### Step 4.2 · 反向引用检测（v3.1 新增 · bug 修复）

**为什么**：用户原批注（2026-04-30）— "用 configure-whiteboard 把 `wiki/canvases/math140/Fundamentals.md` 迁成新白板，但 Fundamentals 已被 `节点/Characteristic-Equation-for-Eigenvalues.md` 的 `derived-from: [[Fundamentals]]` 反向引用"。Skill 此前不检测反向引用 → 用户错把已有白板的种子笔记当作新白板源头建了重复白板。

**仅场景 B 跑此步**（场景 A 从零建无 source_path，跳过）：

> **RAG-S2.6（STRUCTURE 平面）**：本步原来是 `Glob 节点/*.md` + **逐个 Read frontmatter**
> ——全库唯一的 O(节点数) 全节点 Read 循环，节点池一大就是纯烧上下文，而且靠 regex
> 猜 wikilink 格式。现在改成读 manifest 的结构化关系：**O(非空板数)**（真 vault
> 15 次 → 5 次），且拿到的是服务端归一好的 `relation.target_node_id`，不用自己处理
> `[[x]]` / `[[节点/x]]` / `[[x.md]]` / `[[x|alias]]` 四种写法。

1. **提取 source_path 文件名**：从 `source_path` 取 stem，例 `wiki/canvases/math140/Fundamentals.md` → `Fundamentals`

2. **1 次列板** `get_board_manifest{ view: "study" }`（不传 `board_id`）→ 得 `boards[]`（含 `board_id` / `board_name` / `member_count_actual`）与 `orphans[]`。

3. **逐块非空板取成员**（`member_count_actual > 0` 的才取，空板不可能引用；每块 **1 次**，HARD-NAV-1）：
   `get_board_manifest{ board_id: "<board_id>", view: "study", include_exam_history: false }`
   在 `nodes[]` 里命中任一条即算反向引用：
   - `node_id == <source_stem>` → source 本身就是该板成员
   - `relation.target_node_id == <source_stem>` → 有节点派生自它（原 bug 的 `derived-from` 情形）
   - `source_note == <source_stem>` → 有节点以它为源笔记
   
   ⛔ 服务端已把三种归属都归一成 basename，**不要**再自己写 wikilink regex。

<!-- FALLBACK:BEGIN Step 4.2 反向引用检测降级 -->
manifest 不可用（调用失败 / 超时 / `source_status: "error"`）→ **静默退回 2.6 前的原路径**，检测语义不变、只是慢：
- `Glob 节点/*.md` 枚举所有节点，**逐个 Read frontmatter**，检查 3 个反向引用字段
  （`source_note` / `derived-from` / `up`），regex 用
  `\[\[(?:[^\]]*\/)?<source_stem>(?:\.md)?(?:\|[^\]]*)?\]\]` 覆盖
  `[[Fundamentals]]` / `[[节点/Fundamentals]]` / `[[Fundamentals.md]]` / `[[Fundamentals|alias]]` 四种格式。
- ⛔ 不得因为降级就**跳过**本检测——它防的是「盲建重复白板」，是用户 2026-04-30 批注打出来的护栏。
<!-- FALLBACK:END -->

4. **若任一节点反向引用 source_stem**：
   - `existing_boards` = 这些命中所在的 `board_id` 集合（**manifest 路径下就是发起该次调用的板**，不用再回读 frontmatter；降级路径才需从节点 `source_board` 提取）
   - **AskUserQuestion**（强制阻止盲建新白板）：
     > ⚠️ **检测到反向引用**：
     > 
     > `{source_path}` 已被以下节点引用：
     > - `[[节点/X]]` derived-from `[[{source_stem}]]`（属于白板 `{board_A}`）
     > - `[[节点/Y]]` source_note `[[{source_stem}]]`（属于白板 `{board_B}`）
     > 
     > 这意味着 `{source_stem}` 已经是某个白板的种子或派生节点。怎么处理？
     > 
     > - **A. 追加到已有白板 `{board_A}`** （把 source_path 的内容作为新种子加到 `{board_A}.md` 的 `## Concepts`）— 推荐
     > - **B. 仍建新白板 `{board_name}`**（覆盖反向引用，承担"碎片化"风险，可能造成同一概念多白板分裂）
     > - **C. 取消**（先去看一下 `{board_A}` 再决定）

5. **若用户选 A**：跳到 Step 6 但用 `existing_boards[0]` 替换 `{board_name}`（即追加到已有白板）

6. **若用户选 B**：继续原 Step 5（建新白板，记录 `⚠ 用户选择忽略反向引用` 到回执）

7. **若用户选 C**：halt，输出 `✗ 用户取消，请去 [[原白板/{board_A}]] 查看后再决定`

8. **零反向引用**：直接继续 Step 5

### Step 5 · 创建目录结构 + 白板 md

```bash
# 确保 vault 根三个扁平文件夹存在（幂等）
mkdir -p "原白板" "节点" "检验白板"
```

用 Read + 字符串替换生成白板 md：

1. Read `.claude/skills/configure-whiteboard/templates/whiteboard.md.template`
2. 生成 `created_at = date -u +"%Y-%m-%dT%H:%M:%SZ"`
3. 替换 `{{board_name}}` / `{{created_at}}`
4. Write 到 `原白板/{board_name}.md`

### Step 6 · 场景 B · 种子笔记归类

若 source_path 存在（场景 B 或场景 A + active note 不在 `原白板/`）：

1. `AskUserQuestion`：
   > 种子笔记 `{source_path}` 要 **move**（推荐，原位置删除）还是 **copy**（保留原位置副本）到 `节点/`？
2. 记录 `seed_basename = basename(source_path)`，种子笔记目标 = `节点/{seed_basename}`
3. **节点池重名保护**：用 `Glob` 检查 `节点/{seed_basename}` 是否存在
   - 存在 → `AskUserQuestion`：
     > `节点/{seed_basename}` 已存在（一 vault 一学科理论不应重名，可能是概念拆分问题）。怎么办？
     > - 自动加 `_2` 后缀 → `节点/{stem}_2.md`
     > - 换名 → 用户输入新 basename
4. Bash：
   - move: `mv "{source_path}" "节点/{seed_basename}"`
   - copy: `cp "{source_path}" "节点/{seed_basename}"`
   - move 跨卷失败 → 降级 `cp && rm`
5. 更新种子笔记 frontmatter（**不加 subject 字段**，vault 级透明）：
   - 若原 frontmatter 无 `type: concept` → 加
   - 若原 md 无 frontmatter → 加最小 frontmatter `--- type: concept ---`
   - ⛔ **必须写 `source_board: "[[原白板/{board_name}]]"`**（RAG-S2.6 T2）：
     它是白板成员归属的**唯一真相源**，`## Concepts` 与 `doc_count` 都从它重算。
     漏写 = 该种子永远不进目录、也永远不会被 `/start-exam-board` 选中考察。
     （plugin 命令 `canvas:configure-whiteboard` 已在 main.ts 写入此字段，本 Skill 之前漏写。）
6. **`Bash` 跑一次目录同步**（`## Concepts` 行 + `doc_count` 由脚本从 `source_board` 重算）：
   ```bash
   python3 .claude/scripts/sync_board_concepts.py --board "{board_name}"
   ```
   ⛔ **不要**手写 `- [[节点/{seed_stem}]] — seed note (mastery: 0.30)` 行、
   **不要**手改 `doc_count`：`## Concepts` 自 RAG-S2.6 起是**只读派生物**，
   写进 sentinel 之间的手写行会在下次同步时被覆盖，写死的 `(mastery: 0.30)`
   也与真值脱节（脚本按当前掌握度/已考次数如实渲染）。

   <!-- FALLBACK:BEGIN Step 6 目录同步降级 -->
   同步失败（脚本缺失 / 非零退出 / 报「无 `## Concepts` 段」）→ **不阻断建板**：
   白板 md 与种子笔记已落盘，回执标注
   `⚠ 白板目录同步失败，种子已归入 节点/（下次任一次同步会自动补齐）`。
   **不要**退回手写目录行。
   <!-- FALLBACK:END -->
7. 在白板 md 的 `## Recent Activity` section append（这段仍由本 Skill 维护，脚本不碰）：
   ```
   - {ISO}: Seed note {seed_basename} imported
   ```

### Step 7 · 返回回执（3 行 ✓ 或 ✓/✗/⚠ 组合）

**场景 A 成功**（无种子）：
```
✓ 原白板 "{board_name}" 已建立
📍 位置: 原白板/{board_name}.md
🏷️ 学科（vault 级）: {vault_subject}
📝 种子笔记: 0（空白板，可后续选中文本 Cmd+Shift+D 派生节点）
```

**场景 A/B 成功含种子**（3 行 ✓）：
```
✓ 原白板 "{board_name}" 已建立（原白板/{board_name}.md）
✓ 种子笔记 {seed_basename} 已归入 节点/
✓ 白板目录已重算（## Concepts 收录 [[节点/{seed_stem}]]，doc_count → N）
```

**部分失败示例**：
```
✓ 原白板 "{board_name}" 已建立
✗ 种子笔记 move 失败: 跨卷 rename → 已降级 cp + rm
⚠ 请确认原位置 {source_path} 已清除
```

---

## 执行自检清单（Step 7 回执前必 tick）

```
[ ] 白板 md 写到 "原白板/{board_name}.md"（不是 wiki/canvases/ 或其他）
[ ] 节点 md（若有种子）写到 "节点/{basename}"（扁平，非嵌套）
[ ] 白板 md frontmatter 含 type: whiteboard + board_name + created_at + doc_count + doc_mastery_avg
[ ] 白板 md frontmatter **无 subject 字段**（vault 级透明）
[ ] 种子笔记 frontmatter 无 subject（vault 级透明）
[ ] ⛔ 种子笔记 frontmatter 已写 source_board: "[[原白板/{board_name}]]"（成员归属唯一真相源）
[ ] ⛔ 未手写 ## Concepts 行、未手改 doc_count —— 只跑了 sync_board_concepts.py --board
[ ] 同步脚本输出里种子已计入成员数；失败则回执已标 ⚠ 且白板/种子仍已落盘
[ ] 未写入弃用路径 wiki/canvases/ 或 wiki/concepts/
[ ] 回执格式 3 行 ✓ 或 ✓/✗/⚠ 组合
```

---

## 弃用路径清单（v3 绝对禁止）

| 弃用路径 | 替代 |
|---|---|
| `wiki/canvases/<subject>/index.md` | `原白板/<board_name>.md` |
| `wiki/canvases/<subject>/<concept>.md` | `节点/<concept>.md` |
| `wiki/concepts/*.md` | `节点/*.md` |
| `outputs/exam_boards/<exam>.md` | `检验白板/<exam>.md`（outputs/exam_boards/ 只放输出，不放白板本身） |

若 Skill 识别到消息要求写旧路径 → 立即返回 `✗ 弃用路径`，不执行。

---

## 中文目录编码兼容提示

Bash 命令处理中文路径需注意：
- `mkdir -p "原白板"` 直接用双引号即可（Bash 默认 UTF-8）
- `mv "{source}" "节点/{basename}"` 源路径和目标都加引号
- macOS HFS+ 用 NFD（Unicode Normalization Form D），`ls` 可能看到分解形式；Linux 用 NFC。跨机器同步（例 iCloud）可能出问题 — 如发生，降级为英文目录名（见 Story 1.19 v4 验收单诊断）

---

## 约束

- **不调 Graphiti / 后端 API**（MVP 阶段纯 vault 文件级，后端 subject 固化留给下轮）
- **不碰 `raw/` 目录**（保留给课件原件 + 视频转录）
- **生成内容不含 AI 自我介绍**
- **不做 debounce / 并发控制**（Skill 同步执行）

---

## 错误场景速查

| 症状 | Skill 响应 |
|---|---|
| `.canvas-config.yaml` 不存在 | Step 1 AskUserQuestion 一次性创建 |
| board_name 含文件系统非法字符 `/ \ : * ? " < > \|` | AskUserQuestion 重问 |
| `原白板/{board_name}.md` 已存在 | AskUserQuestion 覆盖/追加/换名 |
| 种子笔记在 `节点/` 已重名 | AskUserQuestion _N 后缀 / 换名 |
| move 跨卷失败 | 降级 cp + rm，摘要 `⚠` |
| 中文目录 mkdir 失败（罕见） | 回退到 ASCII fallback `boards/nodes/exams/`，记入 deviation |

---

## 参考

- Round-10 批注回复：`_bmad-output/验收单/批注回复/Round-10-架构重设计.md`
- Story spec：`_bmad-output/implementation-artifacts/epic-1/1-19-configure-whiteboard-skill.md` (v3)
- CLAUDE.md 扁平架构段：`_bmad-output/.claude/CLAUDE.md` round-11（"Vault 扁平架构"）
- 社区对齐：Nick Milo Ideaverse Atlas/Maps + Atlas/Notes（https://www.linkingyourthinking.com/）
- 下游：`ai-linked-doc/SKILL.md`（Story 1.17 v4）需要本 Skill 产出的 `原白板/` + `节点/` 目录
