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
model: sonnet
---

# 原白板配置 Skill v3（Canvas Learning System · 扁平架构）

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

### Step 4 · 冲突检测（文件级）

用 `Glob 原白板/{board_name}.md` 检查：

- **已存在** → `AskUserQuestion`：
  > `原白板/{board_name}.md` 已存在。怎么处理？
  > - 覆盖重建（丢弃现有内容）
  > - 追加种子笔记到现有白板的 `## Concepts` section（仅场景 B）
  > - 换名（回 Step 3 重问）
- **不存在** → 继续 Step 5

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
6. 在白板 md 的 `## Concepts` section append：
   ```
   - [[节点/{seed_stem}]] — seed note (mastery: 0.30)
   ```
   注意用**完整相对路径** `节点/{seed_stem}` 让 wikilink 明确指向节点池（避免 Obsidian 自动推导出错）。
7. 在白板 md 的 `## Recent Activity` section append：
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
✓ 白板 ## Concepts 已添加 [[节点/{seed_stem}]]
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
[ ] 白板 ## Concepts 段的 wikilink 含路径 "节点/"
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
