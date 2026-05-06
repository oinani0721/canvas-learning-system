# EPIC 1 审计回应文档 — Round 2

> **回应对象**: [[epic-1-audit-response-2026-04-17]]（Round 1）+ [[epic-1-audit-2026-04-17]]（Audit）
> **Round 3**: [[epic-1-audit-response-round-3-2026-04-17]]（回应本文档 N1-N6 新批注 R1-R4）
> **Plan ID**: EPIC1-BMAD-DEV-ASSESS-2026-04-17
> **Date**: 2026-04-17
> **Round 2 决策锚点**:
> - N1 隔离方案 = `_bmad-output/.claude/CLAUDE.md` + `claudeMdExcludes`（社区验证 monorepo 子目录模式）
> - N2 批注 UX = 单 hotkey + modal 选 7 种 callout 类型
> - N4 Dashboard = Hybrid: MD MVP 起步 → 瓶颈时迁 WebUI
>
> **使用方式**: 本文档回应 round-1 中你新加的 6 条批注（N1-N6）。新批注占位符在每 Sec 末尾。

---

## Sec N1: 新文件夹方案 + _bmad-output 作开发根（回应 round-1 Sec 1 + Sec 3 批注）

### 你的原批注
> "请你启动并行 agent deep explore 找到社区成熟的解决方案... 我们的整个新的 claude code 的开发仓库聚焦于 _bmad-output；我们进入这一个文件夹来 claude code 开发"
>
> "给项目开启一个新的 claude.md 就是为了不让 claude code 被之前 claude.md 中的过时内容所误导"

### 调研真相（Agent 1）

**关键事实**: Claude Code CLAUDE.md 加载是 **additive**（所有祖先目录都读，无优先级覆盖）— `cd _bmad-output && claude` **仍会**读 `canvas-learning-system/CLAUDE.md`。这意味着只创建子 CLAUDE.md 不够 — 必须显式排除父级。

**官方文档**: https://code.claude.com/docs/en/memory

### 推荐方案（你已选）: `_bmad-output/.claude/CLAUDE.md` + `claudeMdExcludes`

#### 实施步骤

1. **创建子 CLAUDE.md**:
   ```bash
   mkdir -p _bmad-output/.claude
   touch _bmad-output/.claude/CLAUDE.md
   touch _bmad-output/.claude/settings.local.json
   ```

2. **`_bmad-output/.claude/settings.local.json` 内容**:
   ```json
   {
     "claudeMdExcludes": [
       "/Users/Heishing/Desktop/canvas/canvas-learning-system/CLAUDE.md"
     ]
   }
   ```
   （不排除全局 `/Users/Heishing/CLAUDE.md` + 父项目 `/Users/Heishing/Desktop/canvas/CLAUDE.md` — 那些应保留）

3. **`_bmad-output/.claude/CLAUDE.md` 草稿**（详见下方）:
   聚焦 BMAD 流程 + Obsidian Hybrid + 4 MVP 功能 + 跨目录编辑指引

4. **启动 Claude Code**:
   ```bash
   cd /Users/Heishing/Desktop/canvas/canvas-learning-system/_bmad-output
   claude --add-dir ../backend --add-dir ../frontend/obsidian-plugin --add-dir ../canvas-vault
   ```
   `--add-dir` 让 Claude 能编辑 sibling 目录代码

#### 新 CLAUDE.md 内容草稿

```markdown
# Canvas Learning System — Obsidian Hybrid Development

## 项目定位（最高优先）

**当前架构**: Obsidian Hybrid（已从 Tauri v0 降级）
- UI: Obsidian Editor + Claudian 侧栏
- Skill 引擎: Claude Code Skill (官方集成)
- 后端: FastAPI + Neo4j + LanceDB + Ollama bge-m3
- LLM: Claude API（主）+ Gemini（仅 Graphiti）

**开发聚焦**: 你（Claude Code）此 session 在 `_bmad-output/` 工作目录。
sibling 代码目录通过 --add-dir 接入：
- ../backend/        FastAPI + 28 服务
- ../frontend/obsidian-plugin/  Obsidian 插件 (TS)
- ../canvas-vault/   验收 vault

**禁读** (`claudeMdExcludes` 已排除):
- ../CLAUDE.md (Tauri 时期遗留)
- ../docs/ (Tauri 时期文档)
- ../_decisions/ (旧 MVP 计划)

## 开发文档（你改动的文件）

- `implementation-artifacts/` — Story spec + sprint-status.yaml
- `../backend/app/`            后端代码
- `../frontend/obsidian-plugin/src/`  Obsidian plugin 代码
- `../canvas-vault/`           验收 vault（真实数据）

## 真相源（你只读，不改）

按优先级递减：
1. `planning-artifacts/epics.md` 五星 (BDD + AC)
2. `planning-artifacts/prd.md` 四星 (需求)
3. `planning-artifacts/architecture.md` 三星 (约束)
4. `planning-artifacts/ux-design-specification.md` 三星 (UX)
5. `planning-artifacts/recovered/prd-tauri-original-2ae5897.md` (Tauri v0 历史)
6. `research/obsidian-qa-round2-*.md` (13 轮决策追溯)

外部锚定 PRD: `/Users/Heishing/Desktop/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md` (只读，pretool-guard 阻断)

## 已归档/作废（Sec 1 + 5）

- `../archive/legacy-tauri-v0/` (待执行) — Tauri v0 代码
- `../archive/legacy-docs/` (待执行) — docs/ 中无用户批注的部分
- `../docs/` 中**有用户批注的保留**作追溯（待人工筛选）

## BMAD 流程（你的开发循环）

1. 用 `bmad-bmm-create-story` Skill 创建 Story（最小验收单位）
2. 等用户人工批注审核 spec
3. 用 `bmad-bmm-dev-story` Skill 实施 AC
4. 小白用 UAT 矩阵验收（见 review/epic-1-uat-guide-2026-04-17.md）
5. 偏离时用对齐矩阵的"技术层 trace"诊断根因

## 4 MVP 优先功能（来自 round-2 N2，未来 Story 1.14-1.17 主题）

1. **Hotkey 一: 批注**: 选中文本 → modal 选 7 callout 类型 → 包裹（无 AI）
2. **Hotkey 二: AI 双链**: 选中文本 → AI 创建新 .md + wikilink → 更新原白板 index.md
3. **Skill 一: 原白板配置**: Claudian 询问名 + 学科 → 创建 index.md + 归类
4. **Skill 二: Dashboard 一键考察**: dashboard.md 检索 → 启动 exam_board

## 硬规则（来自父项目 CLAUDE.md，仍生效）

- DD-03 禁 mock：不写 stub / fake API / 空函数
- DD-12 范围约束：frontend agent 改 ../frontend/，backend agent 改 ../backend/
- DD-13 名实一致：函数名匹配实际行为
- DD-14 追踪链：commit 含 PLAN-NNN

## MCP 工具

- Sequential Thinking: 复杂推理必调
- Context7: 查库/框架/API
- Graphiti: search_memory_facts 每轮（group_id: canvas-dev）

## 风格参考

- 后端 service: ../backend/app/services/rag_service.py
- 后端 router: ../backend/app/api/v1/endpoints/canvas.py
- Obsidian plugin: ../frontend/obsidian-plugin/src/main.ts
```

### 5 个 Pitfall（来自 Agent 1）

1. **Hook 在子目录可能不触发** (GitHub Issue #10367) — 父级 `.claude/hooks/` 不会从 `_bmad-output/.claude/` 自动继承。需要把关键 hook（pretool-guard, context-inject）复制到 `_bmad-output/.claude/hooks/` 或全用 `--add-dir` 跑
2. **MCP 路径解析** — MCP 工具按 cwd 解析路径，`_bmad-output/` 启动时 `../backend/` 路径需绝对化
3. **Git 操作仍在仓库根** — `git status` / `git commit` 从 `_bmad-output/` 仍操作整仓库（这是好事）
4. **Skill 自动发现** — `_bmad-output/.claude/skills/` 自动加载，sibling `../backend/.claude/skills/` 不加载（如果存在）
5. **`.claude/settings.json` 优先级** — 子目录 settings 覆盖父，但权限合并

### Round-1 Sec 1 你问的 "yes, archive" 仍未答

待你批注。归档清单见 round-1 Sec 1。

> [!question]+ 用户批注 - Sec N1
> 新 CLAUDE.md 草稿是否符合预期？是否需要增删？是否授权创建 `_bmad-output/.claude/CLAUDE.md` + `settings.local.json`？是否同时执行 Tauri v0 归档（round-1 Sec 1 的 7 步）？
> （批注区）
> 请你执行

---

## Sec N2: 4 MVP 功能优先级（回应 round-1 Sec 2 第一个批注）

### 你的原批注
> "请你先实现两个核心 hotkey 和两个核心 skill。1，批注 hotkey... 2，对于我选中的文本，通过 ai 来创建出新的双向链接文档... 3，原白板配置 skill... 4，dashboard 一键启动检验白板... 而且建议关于 dashboard 设计，是否换成 webUI 更好"

### 4 MVP 功能正式定义（基于 Agent 2 调研 + 你的 Q2/Q4 选项）

#### Function 1: Hotkey 一 — 批注（无 AI）

**社区参考**: [Callout Toggles](https://github.com/alythobani/obsidian-callout-toggles) + [Callout Manager](https://github.com/eth-p/obsidian-callout-manager)

**UX 模式**（你 Q2 选 = 单 hotkey + modal）:

```
用户在 md 选中文本
    下一步 按 hotkey (用户在 Obsidian Settings 自定义)
    下一步
modal 弹出 7 选项: question / tip / error / hint / note / warning / info
    下一步 用户选 1 个
    下一步
插件用 editor.replaceSelection() 包裹为:
> [!<type>]
> <selected text>
```

**实现位置**: `frontend/obsidian-plugin/src/main.ts` 加 `addCommand({ id: "canvas:annotate-callout", editorCallback: ... })`

**新 Story 候选**: Story 1.16 「批注 hotkey + 7 callout 类型」(P0, ~4h)

#### Function 2: Hotkey 二 — AI 双向链接文档

**社区参考**: [Smart Composer](https://github.com/glowingjade/obsidian-smart-composer) + [Note Refactor](https://github.com/lynchjames/note-refactor-obsidian)

**UX 模式**:

```
用户在 md 选中文本
    下一步 按 hotkey
    下一步
modal 弹出: 输入新文档名 + 可选 AI 提示
    下一步 用户输入
    下一步
AI 调用 (Claude API) 分析选中文本 + 生成新文档 body
    下一步
插件创建文件: <subject_folder>/<filename>.md
    下一步
插件替换原选中为 wikilink: [[filename]]
    下一步
插件 append 到 当前原白板 index.md 的 "## Concepts" section
    下一步
新文件在新 tab 打开
```

**关键依赖**: 需要先知道当前 md 的"原白板归属"— 通过 frontmatter `subject` 字段或 `wiki/canvases/<subject>/index.md` 路径推导（详见 Sec N3）

**新 Story 候选**: Story 1.17 「AI 双链文档 + index.md 更新」(P0, ~10h，含 Anthropic SDK 集成)

#### Function 3: Skill 一 — 原白板配置

**社区参考**: [Folder Notes](https://github.com/xpgo/obsidian-folder-note-plugin) + [Templater](https://github.com/SilentVoid13/Templater) + [QuickAdd](https://github.com/chhoumann/quickadd)

**UX 模式**:

```
用户在任意 md 触发 /configure-whiteboard Skill (Claudian)
    下一步
Claudian 提问: "这是什么原白板？" (e.g. "Linear Algebra Fundamentals")
    下一步 用户回答
Claudian 提问: "对应什么学科？" (e.g. "math240")
    下一步 用户回答
Skill 执行:
  1. 创建文件夹 wiki/canvases/<subject>/
  2. 创建 index.md (Templater 模板，详见 Sec N4)
  3. 把当前 md 移入 wiki/canvases/<subject>/<filename>.md
  4. 更新 frontmatter subject: <subject>
  5. 在 index.md 加入 wikilink 引用
    下一步
回复: "原白板已配置。Index: wiki/canvases/<subject>/index.md"
```

**新 Story 候选**: Story 3.X 「原白板配置 Skill」(EPIC 3, ~6h)

#### Function 4: Skill 二 — Dashboard 一键启动检验

**你 Q4 选 = Hybrid (MD MVP 起步)**

**Phase 1 (MD MVP)**:

```
canvas-vault/dashboard.md 内容:

---
type: dashboard
---

# Learning Dashboard

## 活跃原白板
\`\`\`dataview
TABLE board_name, subject, doc_count, doc_mastery_avg
FROM "wiki/canvases"
WHERE type = "whiteboard_index"
\`\`\`

## 准备中的检验白板
\`\`\`dataview
TABLE source_canvas, due_date, status
FROM "outputs/exam_boards"
WHERE status != "scored"
\`\`\`

## 一键操作
[启动 Math240 检验白板](obsidian://execute?command=canvas:start-examination?board=math240)
[启动 CS61B 检验白板](obsidian://execute?command=canvas:start-examination?board=cs61b)
```

**Phase 2 (WebUI 迁移条件)**:
- Dataview 在 1000+ 节点变慢
- 需要 FSRS timeline / mastery heatmap 可视化
- 需要拖拽排程

**WebUI 方案**: [Local REST API plugin](https://github.com/coddingtonbear/obsidian-local-rest-api) + 自定义 React/Svelte view in plugin

**新 Story 候选**: Story 1.18 「Dashboard MVP (MD)」(P1, ~6h)

### 5 个 Cross-cutting Pitfall（来自 Agent 2）

1. **Wikilink 双向更新**: 用 `vault.modify(file, content)` 不用 `editor.replaceSelection`，否则 graph 不刷新
2. **Frontmatter 一致性**: 全 vault 用同一字段名（`subject` 不混用 `whiteboard`）
3. **Index.md race condition**: 新文件创建后等 200ms 或监听 `metadataCache.onChanged` 再更新 index
4. **Callout 类型验证**: modal dropdown 限定 7 种，避免用户输入非法类型导致渲染失败
5. **命令 namespace 冲突**: 4 hotkey 加现有 6 共 10 个 — 全用 `canvas:` 前缀 + Story 1.5 冲突检测覆盖

### 4 个 MVP 功能新 Story 列表（候选）

| Story | 标题 | EPIC | 优先级 | 工作量 |
|---|---|---|---|---|
| 1.16 | 批注 hotkey + 7 callout 类型 | EPIC 1 | P0 | ~4h |
| 1.17 | AI 双链文档 + index.md 更新 | EPIC 1 | P0 | ~10h |
| 3.X | 原白板配置 Skill | EPIC 3 | P1 | ~6h |
| 1.18 | Dashboard MVP (MD + Dataview + Bases) | EPIC 1 | P1 | ~6h |

总：~26h（约 3-4 天）

### 现有 Story 的关系

- Story 1.4 (hotkey-binding-config) 已包含通用 hotkey 注册框架 — 1.16 + 1.17 复用
- Story 1.5 (hotkey-conflict-detection) 已涵盖冲突检测 — 1.16 + 1.17 自动受益
- Story 1.14 Draft (md import) 与 1.16/1.17 互补：1.14 = 外部 md 导入；1.17 = AI 从选中文本派生新节点

**user：这个技术问题我不清楚，请你自行决策，我只审核和非技术相关的内容，请你在 claude.md .其余你拿不定的技术决策我给 ChatGPt deep research。**
> [!question]+ 用户批注 - Sec N2
> 4 MVP 功能定义是否符合预期？4 个新 Story 候选（1.16/1.17/3.X/1.18）的 EPIC 归属和优先级是否合适？AI 双链 Story 1.17 是否依赖 Sec 7 的 LLM 切换（先做 1.15 Anthropic 集成）？
> （批注区）

---

## Sec N3: /extract_node + /chat_with_context Contract（回应 round-1 Sec 2 第二个批注）

### 你的原批注
> "1，我们强调过 /extract_node 就是会让我说明，前后文档之间的联系
> 2，/chat_with_context 是用来告诉 claudian，我们当前使用的是原白板吗？这里我觉得让 claudian 意识到的事情只要是，知道我们当前的 md 文件归属于哪一个原白板，并且能找 index.md 阅读理解各个文档之间的关系；/extract_node 则是提取创建新的节点后，能关系原白板的 index.md"

### 调研发现（Agent 3）

两 Skill 的 contract 都围绕 **index.md 作为 MOC（Map of Content）**展开。

#### /extract_node Contract

**输入**:
```
- selected_text: 选中文本
- current_note_path: 当前文档路径
- relationship_type: 用户选 (depends_on / prerequisite_of / related_to / contrast_with / part_of)
- target_concept: 用户输入的关联概念 (wikilink 或新名)
```

**执行步骤**:

1. **创建新文件**:
   - 路径: `wiki/canvases/<subject>/<new_concept>.md`
   - 模板: Templater 填充 frontmatter (type:concept, mastery_score: 0.30, relationships: [])
   - 内容: 选中文本放入 `## 核心概念` section

2. **更新 SOURCE 笔记**（当前文档）:
   - frontmatter `relationships[]` append:
     ```yaml
     relationships:
       - target: "[[<new_concept>]]"
         semantic_type: "<relationship_type>"
         rationale: "<用户填写或选中文本摘要>"
         created: "<ISO8601>"
     ```

3. **更新原白板 index.md**:
   - frontmatter: `doc_count` += 1, `doc_mastery_avg` 重算
   - body "## Concepts" section: append `- [[<new_concept>]] — extracted, weak (0.30)`
   - body "## Recent Activity": append `- <date> — Extracted [[<new_concept>]] from [[<source>]]`
   - body "## Relationship Graph" 表格: append 一行

4. **返回**:
   - 新文件 wikilink 给用户
   - 在新 tab 打开新文件

#### /chat_with_context Contract

**自动检测原白板**（不需用户告知）:

1. 读当前 md frontmatter 的 `subject` 字段
2. 路径推导：扫描 `wiki/canvases/<subject>/index.md`
3. 如果找不到：grep 所有 index.md，匹配 frontmatter `board_name` 或 `subject`

**Context 装配**:

1. 加载 index.md：board_name + relationships 表 + recent activity
2. 1-hop 邻居加载：从 index.md "## Concepts" 取所有 wikilink，逐个读 frontmatter (mastery_score, tips[], errors[])
3. 历史检索：
   - Graphiti `search_memory_facts(group_id=<subject>, query=<current concept>)`
   - LanceDB 语义检索（可选，3-5 snippet）
4. 注入 Claude system prompt：
   ```
   Current whiteboard: <board_name> (subject: <subject>)
   Current node: [[<current>]]
   Related nodes: [[A]] (mastery 0.85), [[B]] (mastery 0.62)
   Learning history:
   - Tips: <从邻居 frontmatter 提取>
   - Errors: <从 Graphiti 提取>
   - Recent exam: <分数 + 弱点>
   ```

**对话期间**:
- 用户问问题 → Claude 用注入 context 回答
- 用户可触发 `/extract_node` 把对话内容拉出新节点
- 对话结束 → 归档到 Graphiti，更新邻居 frontmatter `tips[]` `errors[]`

### 实施先后

- 先做 /extract_node（依赖最少，纯文件操作）
- 后做 /chat_with_context（依赖 Graphiti + LanceDB，复杂）

### 与现有 Story 关系

- [[3-1-concept-extraction-wikilink]] = /extract_node 的早期 Story spec — 但当时未明确 index.md 更新行为
- [[2-7-concept-extraction-edge-inject]] = /extract_node 的另一面（edge 注入）
- 建议下次 session 用 `bmad-bmm-create-story` 创建/更新 Story 3.1 的 AC，把"index.md 更新"加进去

> [!question]+ 用户批注 - Sec N3
> 两 Skill 的 contract 是否符合你的"前后文档联系 + index.md 中心枢纽"诉求？/extract_node 步骤 1-3 是否齐全？/chat_with_context 自动检测原白板的方式（先 frontmatter subject 后路径推导）是否 OK？
> （批注区）

---

## Sec N4: index.md MOC Schema（支撑 Sec N3）

### 设计来源（Agent 3）

参考 Nick Milo 的 LYT (Linking Your Thinking) 框架 + Obsidian Folder Notes 插件 + 我们 PRD 已定义的 frontmatter schema。

### Schema 草稿

**位置**: `wiki/canvases/<subject>/index.md`

```yaml
---
# 元数据 (机器可读)
type: whiteboard_index
board_name: "Linear Algebra Fundamentals"
subject: "math240"
created_at: "2026-04-18T00:00:00Z"
updated_at: "2026-04-18T12:30:00Z"
doc_count: 12
doc_mastery_avg: 0.65
node_mastery_distribution:
  - count: 3
    range: "[0.8, 1.0]"
  - count: 5
    range: "[0.5, 0.8]"
  - count: 4
    range: "[0, 0.5]"
relationships_format: "frontmatter"
last_exam_at: "2026-04-17T14:20:00Z"
last_exam_score: 0.78
---

# Linear Algebra Fundamentals 原白板

**Subject**: math240 · **Mastery**: 65% · **Last Reviewed**: 4/17

## Concepts (6 nodes)
- [[Vector-Space]] — foundational, mastered (0.85)
- [[Matrix-Operations]] — computational, learning (0.62)
- [[Eigenvalues-Eigenvectors]] — core difficulty, weak (0.38)
- [[Linear-Transformations]] — bridge, learning (0.70)
- [[Basis-Dimension]] — structural, mastered (0.80)
- [[Determinants]] — technical, weak (0.35)

## Theorems & Proofs (3 nodes)
- [[Spectral-Theorem]] — symmetry, learning (0.55)
- [[Rank-Nullity-Theorem]] — foundational, mastered (0.88)
- [[Diagonalization-Existence]] — application, weak (0.42)

## Common Errors (3 nodes)
- [[Eigenvalue-Eigenvector-Confusion]] — typical error, 0 cleared
- [[Determinant-Intuition-Gap]] — geometric meaning, 2 examples
- [[Matrix-vs-Transformation]] — abstraction mix-up, 1 clarification

## Relationship Graph
| Source | Target | Type | Status |
|--------|--------|------|--------|
| [[Vector-Space]] | [[Basis-Dimension]] | prerequisite | discussed (4/10) |
| [[Matrix-Operations]] | [[Linear-Transformations]] | enables | discussed |
| [[Eigenvalues-Eigenvectors]] | [[Spectral-Theorem]] | required_for | weak link |
| [[Determinants]] | [[Rank-Nullity-Theorem]] | supports | discussed |

## Recent Activity
- 2026-04-17 14:20 — Exam "LA-Midterm-Practice" scored 78%
- 2026-04-16 10:15 — Edge discussion: Vector-Space + Basis-Dimension
- 2026-04-15 — Extracted [[Determinant-Geometric-Meaning]]
- 2026-04-14 — Extracted [[Matrix-Rank-Definition]]
```

### 设计要点

| 要点 | 选择 | 理由 |
|---|---|---|
| Frontmatter 元数据 vs body | Frontmatter 存数字+状态，body 存语义 | Dataview/Bases 可查询 + 人类可读 |
| Relationships 存哪 | concept.md 的 frontmatter `relationships[]` | index.md 只引用，避免重复维护 |
| 状态可视化 | mastery 数字（emoji 可选） | Obsidian 原生渲染 |
| Sections | 6 段（Concepts / Theorems / Errors / Graph / Activity） | 学习者认知单元 + 教学法 |
| 自动更新 | /extract_node + /chat_with_context 触发 | 不靠 cron 或 file watcher |

### 学科分类（Hybrid 推荐）

```
canvas-vault/
├── wiki/
│   ├── canvases/
│   │   ├── cs61b/
│   │   │   ├── index.md     ← MOC for CS61B 原白板
│   │   │   └── ...
│   │   ├── math240/
│   │   │   ├── index.md     ← MOC for Math240
│   │   │   └── ...
│   │   └── history101/
│   │       ├── index.md
│   │       └── ...
│   └── concepts/             ← 跨学科共用概念
│       ├── Binary-Search.md  (frontmatter: subject: cs61b)
│       └── Vector-Space.md   (frontmatter: subject: math240)
└── outputs/exam_boards/
    ├── cs61b-Exam-01.md
    └── math240-Quiz-02.md
```

- **文件夹**: 视觉组织 + 自然路径
- **frontmatter `subject`**: 机器可读隔离
- **Wikilink 跨学科**: 允许，但 context 默认按 subject 过滤

### canvas-vault 现状（实测）

- `wiki/canvases/` **空**（无 index.md）
- `wiki/concepts/` **3 测试节点**（TestConceptA/B/C，frontmatter 不匹配 PRD schema）
- `templates/concept.md` 已有，含 `relationships: []`
- `templates/exam-board.md` 已有

**意味着**: blank slate，N3 实施时第一次 `/configure-whiteboard` 触发即创建第一个 index.md。无迁移成本。

> [!question]+ 用户批注 - Sec N4
> index.md schema 6 段是否合适？是否要增删 sections？mastery 数字 vs emoji 状态可视化你倾向哪个？学科 hybrid 分类（folder + frontmatter）是否同意？
> （批注区）

---

## Sec N5: docs/ 选择性迁移（回应 round-1 Sec 3 批注）

### 你的原批注
> "有我的批注的保留，其余的迁移"

### 实施方案

**两步过程**:

1. **筛选阶段**（人工 + 自动）:
   - 自动: grep `docs/` 找含 "User:" / "用户:" / 你的批注语言模式
   - 人工: 你审 grep 结果，确认哪些值得保留

2. **迁移阶段**:
   - 有批注的 → 保留在 `docs/`，加 README 说明"含用户批注的历史追溯"
   - 无批注的 → 移到 `archive/legacy-docs/`

### grep 命令草稿

```bash
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/docs
grep -rln "User:\|用户:\|User注\|用户批注" .
```

### 已知含批注的 docs 文件（基于 Graphiti / 历史 session 记忆）

候选清单（待 grep 验证）:
- `docs/project-status/gap-analysis.md` — 99 FR + 99+ 用户批注
- `docs/project-status/annotation-tracker.md` — 108 条分类追踪
- `docs/known-gotchas.md` — 用户标注的 12 待修
- `docs/scheme-a-planning/14-scheme-a-implementation-prd.md` — 实际是外部 PRD 副本，看是否需保留

### 预期归档结构

```
canvas-learning-system/
├── docs/                              ← 含批注的文件保留
│   ├── README.md                       说明 "Tauri 时期文档 + 用户批注追溯"
│   ├── project-status/
│   │   ├── gap-analysis.md
│   │   └── annotation-tracker.md
│   └── known-gotchas.md
└── archive/
    ├── legacy-tauri-v0/                Tauri v0 代码
    └── legacy-docs/                    无批注的旧 docs
        ├── architecture.md
        ├── api-contracts-backend.md
        ├── component-inventory-frontend.md
        └── ...
```

### 不在本次执行

需先做 grep 筛选 → 你审清单 → 再 git mv。下次 session 操作。
User：请你直接执行。
> [!question]+ 用户批注 - Sec N5
> 筛选 + 迁移两步过程是否合适？grep 命令是否需调整（加更多模式如"我"、"我觉得"）？预期归档结构是否合理？
> （批注区）

---

## Sec N6: UAT 矩阵 + "小白不满意" 列（回应 round-1 Sec 4 批注）

### 你的原批注
> "还要有小白觉得不满意的地方需要改进的点进行批注"

### UAT 矩阵 v2（增加 1 列）

原 round-1 设计 6 列。新增 1 列变 7 列：

| Story / AC | 小白行为（你做什么） | 小白观察（你看到什么） | 通过/失败判据 | 偏离预警 | 技术层 trace | **小白改进批注** ⭐新 |
|---|---|---|---|---|---|---|
| Story 1.4 AC #1 | 在 Settings > Hotkeys 搜 "Canvas" | 看到 6 行 `canvas:*` 命令 | 6 行=通过；少则失败 | 若 < 6 → main.ts addCommand 注册数错 | `grep "addCommand" main.ts` | 若你觉得名字难懂、应该多一栏说明 → 写在这里 |
| Story 1.16 AC #1 | 选中文字 → 按批注 hotkey | 弹出 7 类型 modal | modal 出现+选 question 后插入 callout | 若 modal 不弹 → 检查 modal 类是否 import | `console.log` 在 editorCallback 头部 | 若你觉得 modal 7 选项排序不合理 / 视觉丑 → 写在这里 |

### "小白改进批注" 列的填法约定

每个 Story 跑 UAT 后，小白用 3 个标签填：

- 满意 — 体验流畅，无改进点
- 可改进 — 能用但有摩擦点（具体描述）
- 必须改 — 阻塞使用或严重困惑（具体描述）

### Round-trip 流程

```
小白填批注（可改进/必须改）
    下一步
你（用户）汇总到 _bmad-output/review/uat-feedback-<date>.md
    下一步
下次 session 你告诉我："读 uat-feedback，把必须改改进点放回 Story spec 重新过 dev"
    下一步
Claude Code: 用 bmad-bmm-correct-course Skill 调整 Story
    下一步
重新跑 dev-story → 重新 UAT
```

### 工作量

UAT 指南改造（增加 1 列 + 13 Story 全部填）: ~2h

### 与现有 epic-1-uat-guide-2026-04-17.md 的关系

现有指南是"Story → 验收方法 → 验收手段"3 列。改造为 7 列需要重写每个 Story 章节。建议**改造到新文件** `epic-1-uat-matrix-v2-2026-04-17.md`，保留旧版作历史。

> [!question]+ 用户批注 - Sec N6
> UAT v2 增加"小白改进批注"列是否符合预期？3 标签是否够？是否授权下次 session 改造为 v2 矩阵？是否 keep 旧版 v1？
> （批注区）

---

## Sec N7: 综合行动顺序（更新 round-1 Sec 10）

基于 round-1 + round-2 全部批注 + 决策，更新执行顺序：

| # | 动作 | 前置条件 | 工作量 |
|---|---|---|---|
| 1 | 创建 `_bmad-output/.claude/CLAUDE.md` + `settings.local.json` (claudeMdExcludes) | 你批 Sec N1 "yes" | ~30 min |
| 2 | 复制必要 hook (pretool-guard, context-inject) 到 `_bmad-output/.claude/hooks/` | 配合 #1 | ~30 min |
| 3 | 归档 Tauri v0 (round-1 Sec 1 的 7 步 git mv) | 你批 round-1 Sec 1 "yes, archive" | ~15 min |
| 4 | grep `docs/` 找批注 → 你审 → 移无批注的到 `archive/legacy-docs/` | 你批 Sec N5 + 审 grep 结果 | ~1 h |
| 5 | 改造 UAT 指南为 v2 矩阵（7 列含小白改进） | 你批 Sec N6 "yes" | ~2 h |
| 6 | 用 `bmad-bmm-create-story` 生成 Story 1.14 (md import) | 你批 round-1 Sec 6 AC | ~2 h |
| 7 | 用 `bmad-bmm-create-story` 生成 Story 1.16 (批注 hotkey) | 你批 Sec N2 | ~1 h |
| 8 | 用 `bmad-bmm-create-story` 生成 Story 1.17 (AI 双链) | 你批 Sec N2 + Sec N3 contract | ~2 h |
| 9 | 用 `bmad-bmm-create-story` 生成 Story 1.18 (Dashboard MD) | 你批 Sec N2 + Sec N4 | ~1 h |
| 10 | 用 `bmad-bmm-create-story` 生成 Story 3.X (原白板配置 Skill) | 你批 Sec N2 + Sec N3 + Sec N4 | ~1.5 h |
| 11 | 用 `bmad-bmm-create-story` 生成 Story 1.15 (Anthropic LLM 切换) | 你批 round-1 Sec 7 | ~2 h |
| 12 | 启动 `bmad-bmm-dev-story` 跑 Story 1.2 + 1.8 + 1.16 并行 | 1-11 完成 | ~1 周 sprint |

总工作量（不含 dev sprint）: ~12 h Story 创建 + 配置

### 推荐 Sprint 安排

**第 1 天（4h）**: 步骤 1-5（基础设施 + 归档 + UAT）
**第 2 天（5h）**: 步骤 6-9（4 个 Story spec 创建）
**第 3 天（3.5h）**: 步骤 10-11（剩 2 个 Story spec）+ 准备 dev-story 启动

### 不会自动做的事

- ❌ 任何 Story spec 改动（等你批 round-1 + round-2 各 Sec）
- ❌ Tauri v0 归档（等 "yes, archive"）
- ❌ docs/ 迁移（等 grep + 你审）
- ❌ 改根 CLAUDE.md 直接（用 claudeMdExcludes 而非删父文件）
- ❌ 后端代码改动
- ❌ commit / push
- ❌ 启动 `bmad-bmm-dev-story`（直到 1-11 完成）

> [!question]+ 用户批注 - Sec N7
> 12 步顺序是否合理？3 天 sprint 是否激进？是否要先做 1-5 再决定 6-11 顺序？
> （批注区）

---

## 附录: Round-2 批注引用速查

| Round-1 批注 | Round-2 Sec | 关键发现/决策 |
|---|---|---|
| Sec 1: deep explore 归档方案 | Sec N1 | _bmad-output 作开发根 + claudeMdExcludes |
| Sec 2: 4 MVP 功能 + Dashboard | Sec N2 | 4 新 Story 候选 (1.16/1.17/3.X/1.18) |
| Sec 2: extract_node + chat_with_context | Sec N3 | 完整 Skill contract 围绕 index.md |
| Sec 3: 新 CLAUDE.md 不被旧污染 | Sec N1 | claudeMdExcludes 阻断父级 |
| Sec 3: docs 选择性迁移 | Sec N5 | grep 筛选 + 两步过程 |
| Sec 4: 小白不满意改进列 | Sec N6 | UAT 矩阵 v2 加第 7 列 |

---

## 附录: 三个 Round 文档关系图

```
[[epic-1-audit-2026-04-17]]                ← Audit (含你 9 条原批注)
        ↑                                   
        │ Round 1 反链                      
        │                                   
[[epic-1-audit-response-2026-04-17]]       ← Round 1 (回应 9 条 audit 批注)
        ↑                                   
        │ Round 2 反链                      
        │                                   
[[epic-1-audit-response-round-2-2026-04-17]] ← 本文档 (回应 round 1 的 6 条新批注 N1-N6)
```

每轮回应完，你在新文档加批注 → 下一轮再回应。

---

> [!tip]+ 综合意见 - Round 2
> Round-2 整体回应是否充分？4 MVP Story (1.16-1.18 + 3.X) 是否有遗漏？最迫切先推进哪个 Sec？
> （批注区）


**User：请你在 claude.md 强调，我是一个非技术背景的用户，我告诉你的 PRD ，或者编写的 EPIC，我只是告诉你我对于我们的 Canvas learning  systeam 产品的期望是什么样子，我规定的使用行为行为和交互逻辑，背后的技术细节实现，你需要启动并行 agent 在社区 deep explore，如果还有什么技术的难点决策不了，那么你给我相关的提示词，我给ChatGPt deep research；然后你每一个具体根据我们抽象的行为 定义的 EPIC 所落地技术实现的 story ，这里技术 stroy 的实现，需要给我这个只关注交互行为规范的用户，可以明显的上手感受，这个产品的功能有没有问题，是否使用的时候满足我的预期，我都会给你批注说明。这是我们核心的核心，我的 Bmad 开发 Canvas learning systeam 就是要走这个流程**