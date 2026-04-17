---
title: "Obsidian 翻译问答 Round 2 主答复文件（⚠️ 部分未读 /recovered，Round 3 已纠正；Round 4 无新批注进入本文件）"
date: 2026-04-14
trigger: "用户在 obsidian-translation-qa-2026-04-14.md 追加 19 条 round-2 批注"
type: "qa-round2-answers"
status: "round3-corrected"
parent_file: "[[obsidian-translation-qa-2026-04-14]]"
round3_followup_file: "[[obsidian-qa-round3-claude-answers-2026-04-14]]"
round4_followup_file: "[[obsidian-qa-round4-claude-answers-2026-04-14]]"
round4_new_annotations_in_this_file: 0
round5_followup_file: "[[obsidian-qa-round5-claude-answers-2026-04-15]]"
round5_new_annotations_in_this_file: 0
related_plan: "OBSIDIAN-QA-ROUND5-2026-04-15"
round3_deviations_count: 5
explore_agents:
  - "Explore 1: Tauri PRD 节点本质"
  - "Explore 2: 引用诚实度验证"
  - "Explore 3: 后端机制真实实现"
---

# Obsidian 翻译问答 Round 2 主答复文件

> **⚠️ [Round 3 纠正警示 · 2026-04-14]** 本文件部分答复**未读 `/recovered` 权威证据 + 前端真实代码**，有以下 5 处偏离，完整纠正见 [[obsidian-qa-round3-claude-answers-2026-04-14]]:
>
> 1. **R2-Q8.1 / R2-Q9**：说 "PRD 无 3 态理解程度主动标记机制" 错。**前端 `InlineAnnotation.tsx:38` 真实实现 UnderstandingLevel = 'understood' \| 'fuzzy' \| 'not-understood'**。Round 2 只 Grep FR 行号漏掉 Persona + 前端实现（见 R3-QA1 / R3-QA5）
> 2. **R2-Q17**：说 "Tips 不在节点 frontmatter" 错。**事实是三存储 all-of**：md frontmatter tips[] + Graphiti Neo4j + SQLite（见 R3-QA13）
> 3. **R2-Q0.6.2**：说 "FSRS 节点级是实现偏离" 错。**节点级是 PRD 原设计**（`/recovered/prd-tauri:326, 777`），白板级是 Dashboard UI 聚合（见 R3-QA2）
> 4. **R2-Q10.1**：未明确 Obsidian 降级后 Graphiti 的新定位。**Obsidian 无 hook，改 Claude Code Skill + MCP 工具**（见 R3-QA9）
> 5. **R2-Q15**：说 "归档时生成对话 md 文件" 错。**后端只记 ArchiveStatus JSON，不生成 md**（见 R3-QA11）
>
> 此外 Round 2 的 `node_type` 保留建议已被用户 Round 3 明确反对（见 R3-QA3 / R3-QA4）。
>
> **阅读指引**: 本文件是 [[obsidian-translation-qa-2026-04-14]] 的 Round 2 深度答复。
>
> Round 1 的 `[A2 2026-04-14]` 答复里有 **11 条幻觉引用** + **4 大偏离原 PRD**，本文件逐条纠正（但本文件自身又被 Round 3 纠正 5 处，详见上方警示）。
>
> **跨 session 可读性约定**:
> - 原文件每条用户 round-2 批注下方有 `[A3 2026-04-14 → round2]` 简答 + wikilink 跳转至本文件对应 `R2-Qn` section
> - 本文件每条用户 round-3 批注下方有 `[A4 2026-04-14 → round3]` 简答 + wikilink 跳转至 Round 3 主文件对应 `R3-Qn` section
> - 本文件每个 section 的 heading 都是 `## R2-Qn · <标题>`，可用 `[[obsidian-qa-round2-claude-answers-2026-04-14#R2-Qn-标题]]` 精准跳转
> - 所有 wikilink 引用已 Grep 验证存在（遵守 **引用诚实度硬规则 IC-1/IC-2/IC-3**；Round 3 新增 IC-4~IC-6）

## Round 2 的 4 大核心纠正（概览）

| # | Round 1 错误 | Round 2 纠正 | PRD 原文证据 |
|---|------------|-----------|----------|
| **1** | 说 Tips 在节点 frontmatter `tips[]` 字段 | Tips 是独立对话标注，存 Graphiti，**不在 frontmatter** | prd-v0 Line 751 (FR-CONV-05) |
| **2** | 编 6 种 callout（含 exam-focus/mastery/reasoning-path）| PRD 只定义 1 种 Tips 标注 + Area9 式答前自评 | prd-v0 Line 800-801 (FR-MAST-05) |
| **3** | 说 Concepts/Proofs/Gotchas 分组来自 PRD | PRD 对节点展示分组**完全沉默**，是我从 Karpathy 搬的 | prd-v0 无此内容 |
| **4** | 编 `node_type: concept/problem/example/error` | PRD 只有 `source`（来源 5 种）+ `content_type`（内容 3 种）| prd-v0 Line 280-282, 738-741 |
**User：Tips 完全就是我选择和 claudian 对话的相关内容，或者节点上的相关文本，选中来打标签而已，上面会写着我的个人理解或者疑问，还会标着我的理解程度。**/Users/Heishing/Desktop/canvas/canvas-learning-system/_bmad-output/planning-artifacts/recovered；请你查看该文件夹。

> **[A4 2026-04-14 → round3]** 🚨 Round 2 严重偏离。**前端 `InlineAnnotation.tsx:35` 已 100% 实现你描述的 UX**：4 种 AnnotationTag（tips/error/question/keypoint）+ 3 种 UnderstandingLevel（understood/fuzzy/not-understood）。交互：选中对话文本 → 浮动工具栏 → 标注面板 → 选 Tag + 写说明 + 选理解度 → 保存。`/recovered/prd-tauri-original-2ae5897.md:399` Persona 故事也明确描述此流程（ROG 选中 Agent 解释 + 标"✓ 已理解" + 写 Tips）。
> 完整证据：[[obsidian-qa-round3-claude-answers-2026-04-14#R3-QA1-Tips-完整定义User-权威原话|📚 R3-QA1]]
## 引用诚实度硬规则（所有后续答复遵守）

- **IC-1**: 所有 wikilink `[[文件#section]]` 必须 Grep 验证 section 真实存在
- **IC-2**: 禁止虚构 section 名（如已失效的 "Agent X §Qn"）
- **IC-3**: 引用代码必须带 `file.py:LINE`，且该行实际存在

---

# T0 入口阶段

## R2-Q0.6.1 · 原白板为什么按 Concepts/Proofs/Gotchas 分组

> **用户 round-2 原话**: "为什么按照 Concepts/Proofs/Gotchas 来分组，请你参考我的 prd-v0-original-tauri 来 deep explore 后回答我"

### Explore 1 调研结论

**PRD 完全没规定此分组**。Concepts/Proofs/Gotchas 是我从 Karpathy `llm-wiki` 示例（gist 442a6bf5）里直接搬来的，违反了 PRD 沉默原则。

搜索 `prd-v0-original-tauri.md` 全文：
- **无** "Concepts/Proofs/Gotchas" 字样
- **无** 节点展示分组的任何规定
- 只有 Line 247 / 518 的 `subject` + `group_id` **数据字段**（隔离用，非展示分组）
- Line 720 的"能力域分组"是 FR 功能分组（非白板内节点）

### 纠正

Round-1 错把 Karpathy 示例当成 Canvas PRD 规定。实际 PRD **只约束数据字段**（group_id / subject / canvas_id / mastery_state），**分组展示完全是前端 UX 自由度**。

### 新方案

**原白板分组应由用户自己按学科特性决定**，不需要统一模板：

| 学科 | 建议分组（用户可自定义）|
|-----|--------------------|
| CS 61B | 概念 / 算法 / 易错点 |
| 数学 | 定义 / 定理 / 反例 |
| 文学 | 人物 / 主题 / 原文引证 |
| 历史 | 事件 / 人物 / 影响 |

**实施**: 原白板 md 文件按用户习惯写 `## <分组名>` heading + `- [[wikilink]] — 一句话摘要`，Obsidian 原生渲染即可。不强制模板。

### Obsidian 可导航引用

- [[karpathy-graphify-insights-2026-04-13#Part-1-Andrej-Karpathy-的-LLM-Wiki-架构]] — Karpathy 方法论来源（调研已验证真实存在）
- `prd-v0-original-tauri.md:247` — group_id 按白板命名
- `prd-v0-original-tauri.md:518` — subject 隔离方案

---

## R2-Q0.6.2 · 每日复习选白板而非单节点

> **用户 round-2 原话**: "我每日要选择的复习是，知道要选择哪一个原白板来生成检验白板复习，而不是专门选择单个节点来复习"

### Explore 3 调研结论

后端**当前只有节点级 FSRS API**（`backend/app/services/review_service.py:195-200` + `backend/app/api/v1/endpoints/review.py:596-700`）。`generate_review_for_canvas(canvas_name)` 返回的是节点列表，**没有白板级推荐 endpoint**。

### 纠正

Round-1 Q13 答"选 C 两层都有"但未明确这是**缺口**而非已实现。用户 Q0.6.2 诉求的"每日选白板"目前**不支持**。
**User：请你启动并行 agent deep explore ，因为我觉得我们原本在 Tauri前端的时候，就是设计我们的 FERS 是针对白板的，为什么变成节点级了？**

> **[A4 2026-04-14 → round3]** 🚨 温和澄清。**FSRS 节点级从一开始就是 PRD 原规定**（`/recovered/prd-tauri:326` 精通度节点级 + `/recovered/prd-tauri:777` FR-EXAM-13 白板类型策略非 FSRS 粒度 + `backend/app/services/review_service.py:225-227` 每节点独立 FSRSManager）。你 Round 2 说"原设计白板级"可能是**记忆偏差**（混淆了数据粒度 vs UI 粒度），或指 Dashboard 的白板聚合视图。真相：**两层模型** — 数据层节点级计算（FSRS 6 字段）+ UI 层白板聚合（`canvas.next_review_at = min(node.fsrs_next_review_at)`）。
> 完整两层模型：[[obsidian-qa-round3-claude-answers-2026-04-14#R3-QA2-FSRS-粒度澄清|📚 R3-QA2]]
### 新方案

**新增后端 endpoint**: `GET /api/v1/review/canvases-due`

聚合公式（Explore 3 推荐 A）：
```python
canvas.next_review_at = min(node.fsrs_next_review_at for node in canvas.nodes if node.fsrs_next_review_at)
canvas.due_count = count(node for node in canvas.nodes if node.fsrs_next_review_at <= today)
```

**Dashboard UI（Bases + Meta Bind）展示**: 白板列表（非节点列表），按 `next_review_at` 升序，每行含 `due_count` 徽章 + "生成检验白板"按钮。

### Obsidian 可导航引用

- `backend/app/services/review_service.py:195-200` — 当前节点级 FSRS 实现
- `backend/app/api/v1/endpoints/review.py:596-700` — 节点级 API 现状
- **缺口**: 需新建 Story 11.X 补白板级聚合 endpoint

---

# T0 入口 · Dashboard

## R2-Q1 · Bases 数据库引用补救

> **用户 round-2 原话**: "你这里关于 Base 数据库你给我提供的双向链接我点击进去后并没有看到提及相关的 base 内容"

### Explore 2 调研结论

Round-1 的 `[[karpathy-graphify-insights-2026-04-13|📚 Agent E §Q4 Dashboard 三方案]]` **是幻觉引用**。`karpathy-graphify-insights-2026-04-13.md` 中**无 "Agent E"、无 "§Q4"** 字样（Grep 验证零结果）。

### 纠正

Round-1 凭记忆编 "Agent E §Q4 Dashboard 三方案"，实际调研在对话中完成，未写入研究文档。

### 新方案（Bases + Meta Bind 组合）

**Obsidian Bases**（核心插件 v1.9+，无第三方依赖）:
- 功能：从 vault 所有 md frontmatter 自动聚合成表格 / 卡片 / 图表视图
- 类似 Notion 数据库，但原生

**Meta Bind**（社区插件）:
- 在 Bases 单元格中加按钮、下拉、表单 input
- 按钮可绑定 Obsidian command（如 `claudian:run-skill`）

**组合效果**: `dashboard.md` 顶部写 Bases view → 显示所有白板 frontmatter → 每行右侧 Meta Bind 按钮 → 点击触发 Claudian skill。

### Obsidian 可导航引用

- [Obsidian Bases 官方文档（外部）](https://help.obsidian.md/Plugins/Bases) — Bases 核心插件说明
- [Meta Bind GitHub（外部）](https://github.com/mProjectsCode/obsidian-meta-bind-plugin) — 插件源
- **待新建**: `canvas-dashboard-spec-v2.md`（Bases + Meta Bind 配置示例）

---

# T1 · 节点创建

## R2-Q4.1 · type 分类的 PRD 依据

> **用户 round-2 原话**: "你这里的 type 分类有什么依据吗？请你参考我的 Tauri 原设计的 PRD"

### Explore 1 调研结论

**原 PRD 完全未定义 `type` 字段枚举**。Grep 搜索 prd-v0-original-tauri.md 全文：
- Line 280-282: 定义 **5 种节点 source**（手动创建 / 对话拉出 / 检验白板生成 / 导入 / AI 推荐）
- Line 738-741: 定义 **3 种 content_type**（文本 / 图片 / 文件嵌入 / 链接）
- **没有 "type: concept|problem|example|error"**

### 纠正

Round-1 的 `node_type: concept|problem|example|error` **完全是我编的**，没有 PRD 依据。Tauri 前端代码的 `KnowledgeNode` vs `ImageNode` 区分是**前端实现自由度**，不是 PRD 规定。

### 新方案（采纳 PRD 原生字段）

**节点 frontmatter 推荐**:
```yaml
---
source: manual | pullout | exam_generated | imported | ai_recommended  # PRD 5 种
content_type: text | image | link | embed                               # PRD 4 种
canvas_id: CS61B-LLRB                                                   # 白板归属
group_id: CS61B-LLRB                                                    # 数据隔离（等于 canvas_id）
mastery_score: 0.32                                                     # BKT
fsrs_next_review_at: 2026-04-15                                         # FSRS
---
```

**题目节点 = content_type: text** + body 含题目内容 + `source: manual`（你粘贴的）或 `source: pullout`（对话拖出）。**不需要 `type: problem`**。
**User2：你要和我解释清楚你这样划分 Type 实际上是有什么作用？完全没必要划分材料类型的 Type，claudian 又不是读不懂**

> **[A4 2026-04-14 → round3]** ✅ **采纳 User2 建议**。PRD 无 NodeType 枚举（`/recovered/prd-tauri:280-282` 只有 5 种 `source` + 4 种 `content_type`），前端 `frontend/src/types.ts:160` 的 `KnowledgeNodeType = 'text' | 'image'` 仅用于 ReactFlow **渲染器选择**（非内容类型）。Round 3 最终裁决：**完全删除 `node_type` 字段**，统一 1 个 `new-node.md` 模板，Claudian 多模态直读图片。
> 完整方案：[[obsidian-qa-round3-claude-answers-2026-04-14#R3-QA3-Type-字段无必要User2-直接反对|📚 R3-QA3]]
### Obsidian 可导航引用

- `prd-v0-original-tauri.md:280-282` — 5 种 source 定义
- `prd-v0-original-tauri.md:738-741` — 3-4 种 content_type 定义

---

## R2-Q4.2 · 快捷键设计更新说明

> **用户 round-2 原话**: "[[karpathy-graphify-insights-2026-04-13|📚 Agent E §Q3 快捷键设计]] 你的这部分内容也没有进行更新说明"

### Explore 2 调研结论

此 wikilink 是幻觉引用。`karpathy-graphify-insights-2026-04-13.md` **无 "Agent E §Q3 快捷键设计"** section。

### 纠正

Round-1 引用了一个不存在的 section。快捷键设计方案实际在 round-1 对话中产生，未沉淀到研究文档。

### 新方案（快捷键真实方案）

基于 R2-Q4.1 纠正后的字段，快捷键设计：

| 快捷键            | 动作          | Templater 模板                  | 创建的节点                                               |
| -------------- | ----------- | ----------------------------- | --------------------------------------------------- |
| `Cmd+Option+N` | 新概念         | `templates/new-concept.md`    | `source: manual`, `content_type: text`              |
| `Cmd+Option+P` | 新题目（也是文本节点） | `templates/new-problem.md`    | `source: manual`, `content_type: text`, body 预留题目位置 |
| `Cmd+Option+I` | 新图片节点       | `templates/new-image.md`      | `source: manual`, `content_type: image`             |
| `Cmd+Option+E` | 生成检验白板      | `templates/new-exam-board.md` | `source: exam_generated`                            |
|                |             |                               |                                                     |
**User：完全没有必要考虑图片节点类型，因为我们在 md 上粘贴图片，claudian 自己会去主动的阅读**

> **[A4 2026-04-14 → round3]** ✅ 采纳。Claudian 基于 Claude Code SDK 原生多模态（Claude 3.7 / Gemini 2.5 / GPT-4 都可直读图片）。Obsidian 粘贴图片 → 自动 `![[img.png]]` 内联语法 → Claudian 读 md 时 Agent SDK 直读图片，无需区分 node type。Round 3 快捷键简化：仅保留 `Cmd+Option+N`（新节点，统一模板）+ `Cmd+Option+E`（生成检验白板）。
> 完整方案：[[obsidian-qa-round3-claude-answers-2026-04-14#R3-QA4-图片节点在-Obsidian-下无必要|📚 R3-QA4]]
**所有快捷键通过 Templater + QuickAdd + Hotkeys for Templates 实现，零代码**。

### Obsidian 可导航引用

- **待新建**: `canvas-hotkeys-spec-v2.md`（Templater 模板配置示例）
- Story 1.1 `1-1-vault-init-templates.md`（现有模板基础）

---

# T1 · 笔记检索

## R2-Q6 · Graphify 只跑笔记之间关系

> **用户 round-2 原话**: "我的建议是 Graphify 应该只跑笔记文件里面的笔记之间各种关系。"

### Explore 调研结论

用户意图：**Graphify 的作用域只限 `raw/` 目录下的学习资料笔记**（学科资料库），提取笔记间的概念关系。**不跑 `wiki/concepts/` 下的白板节点**（那些有专门的对话、FSRS、掌握度系统管理）。

### 纠正

Round-1 模糊说"Graphify 处理笔记资料"但未限定作用域。用户明确：Graphify 作用域 = **`raw/` 学习资料**，不触碰 `wiki/` 和 `outputs/`。

### 新方案（Graphify 作用域分层）

```
vault/
├── raw/              ← Graphify 作用域（课件/论文/教材）
│   └── [Graphify 跑这里 → 生成关系图 → Claudian 检索]
├── wiki/             ← 白板节点 + 概念笔记
│   ├── canvases/     ← 原白板 index.md（Graphify 不跑）
│   └── concepts/     ← 用户剖析过的节点（对话 + FSRS 管理，不跑 Graphify）
└── outputs/          ← 检验白板（Graphify 不跑）
    └── exam_boards/
```

**Claudian 检索策略**:
- 用户问"这概念的定义" → Claudian 先查 `wiki/concepts/`（已剖析）→ 查不到再调 Graphify 查 `raw/`
- `wiki/concepts/` 间的关系走 **Obsidian wikilink + Wikilink Graph**（Story 1.2），不走 Graphify

### Obsidian 可导航引用

- [[karpathy-graphify-insights-2026-04-13#Part-2-Graphify-safishamsi-graphify-项目拆解]] — Graphify 能力清单（调研已验证真实存在）
- Story 1.2 `1-2-wikilink-graph-build.md` — Wikilink 图（wiki/ 目录的关系管理）
- Story 3.2 `3-2-graphify-relation-extraction.md`（待启动）

---

# T1 · 拉出新节点

## R2-Q7 · Claudian 右键失败后的粘贴-拉出方案

> **用户 round-2 原话**: "如果路径 A 实现失败，那么我就把我要拉出到新节点的内容，粘贴到原节点上，然后告诉 claudian 这是新节点的内容，请它进行拉出来双向链接"

### Explore 调研结论

用户的 Fallback 方案本质是"**用户当节点路由器**"——把新内容先写到当前 md，然后让 Claudian 通过 slash command 识别并拉出。**完全可行，零代码**。

### 纠正

Round-1 Q7 没给 Fallback 方案。用户自己提出了这个实用路径。

### 新方案（多层 Fallback）

```
Level 1（首选 · 快捷键拉出）:
  选中对话文字 → Cmd+Shift+X → Claudian `/extract-node` skill
  → 后端创建新节点 md + 双向链接

Level 2（Fallback · 粘贴 + 命令触发）:
  选中对话文字 → 粘贴到当前节点 md 某处 → 选中这段文字 → 
  Claudian 对话输入 "这是新节点 <slug> 的内容，请拉出" →
  Claudian 识别 → 创建 wiki/concepts/<slug>.md + 替换原处为 [[<slug>]]

Level 3（Fallback · 完全手动）:
  用户 Cmd+Option+N 新建节点 → 粘贴内容 → 回原节点写 [[<slug>]]
```

**Level 1 失败时自动降级 Level 2**（用户已提出的方案），Level 3 是最后兜底。

### Obsidian 可导航引用

- **待新建**: `claudian-extract-node-skill-v2.md`（Claudian skill 配置示例）
- Tauri 原版实现: `frontend/src/hooks/usePullToNode.ts:24-87` — 自动位置 +300px 逻辑

---

# T2 · 批注体系（核心偏离）

## R2-Q8.1 · exam-focus/mastery 不符原 PRD 的 callout 重设计

> **用户 round-2 原话**: "!exam-focus；!mastery；这几个 callout 都是不符合我原来的 PRD 的需求，我的批注是用来标记我的疑问以及我的理解程度，然后我可以选择标记的理解程度，一个是我完全理解，一个是我似懂非懂，还有一个是我完全不理解的情况，请你从 git 历史中 deep explore 我的 PRD 先，请你不要搞混了"

### Explore 1 调研结论（最关键）

**PRD 完全没有规定"理解程度 3 态"的批注机制**。Grep 结果：
- Line 751 (FR-CONV-05): "用户可以在对话窗口中标记 Tips（关键知识点）" — **只有 1 种 Tips 标注**  **User：/Users/Heishing/Desktop/canvas/canvas-learning-system/_bmad-output/planning-artifacts/recovered ；错误的，我们之前在前端上和 ai 对话的时候，就可以选中任意的文本，来进行批注，然后标记理解程度。请你仔细 deep explore 我们之前的 PRD ，实际的代码以及我的批注**

> **[A4 2026-04-14 → round3]** 🚨 Round 2 严重违反 IC-6（"用户说这存在就必须先 Read /recovered + 前端代码"）。Round 3 核实：(1) `/recovered/prd-tauri:399` **Persona 故事**明确描述 "选中对话解释 + 标 ✓ 已理解 + 写 Tips"；(2) `frontend/src/components/chat/InlineAnnotation.tsx:35-38` **完整实现** 4 种 AnnotationTag + 3 种 UnderstandingLevel。Round 2 只 Grep FR 行号导致漏掉 Persona + 前端代码两层权威证据。
> 完整纠正：[[obsidian-qa-round3-claude-answers-2026-04-14#R3-QA5-批注-vs-答前自评|📚 R3-QA5]]
- Line 752 (FR-CONV-06): "系统自动从对话中提取、分类并归档用户的错误（4 主类：破题错误 / 推理谬误 / 知识点缺失 / **似懂非懂**）" — **"似懂非懂" 是错误类型**，**不是用户主动标记的理解程度**
- Line 800-801 (FR-MAST-05): "Area9 式 2x2 置信度矩阵追踪用户元认知校准（答前自评 vs 实际表现）..." — **这是答前自评**（考察时的机制），**不是节点批注**

### 纠正（全部 6 种 callout 撤回）

Round-1 我编的 6 种 callout **全部违反原 PRD**：
- ❌ `[!question]+` — PRD 无"疑问"批注机制
- ❌ `[!my-understanding]+` — PRD 无"理解"批注机制
- ❌ `[!ai-explanation]+` — PRD 无此 callout
- ❌ `[!exam-focus]+` — 用户明确说不符
- ❌ `[!mastery]+` — 用户明确说不符
- ❌ `[!reasoning-path]+` — 完全虚构

### 新方案（回归 PRD + 为用户诉求新增 1 种）

**方案 A（纯回归 PRD）**:
只保留 `[!tip]+ 标注`（PRD 原生，FR-CONV-05）。理解程度走**答前自评 UI**（FR-MAST-05 Area9 式），在考察时触发，不在节点批注里。
**User：答前自评完全是另外一回事，这里的 tips 标记批注，绝对不是答前自评，我需要你进行 deep explore 我们 /Users/Heishing/Desktop/canvas/canvas-learning-system/_bmad-output/planning-artifacts/recovered 中的 PRD 文件以及我的个人批注，还有我们前端和后端所实现的代码**

> **[A4 2026-04-14 → round3]** ✅ 采纳用户概念分离。两者是**完全不同机制**：(1) **批注理解程度** = 原白板剖析时用户主观自评（选中文本 + 4 种 Tag + 3 态理解），存 md frontmatter + Graphiti + SQLite；(2) **Area9 答前自评** = 检验白板出题时 AI 问"会吗" + 用户答会/不会，仅用于元认知校准 4 象限统计。Round 2 R2-Q8.1 方案 A（"纯回归 PRD"说理解程度走答前自评）**整体作废**。
> 完整两机制对照表：[[obsidian-qa-round3-claude-answers-2026-04-14#R3-QA6-Round-2-Area9-混淆澄清|📚 R3-QA6]]

**方案 B（PRD + 用户诉求新增）**: 推荐
```
Callout 1 · PRD 原生:
  [!tip]+ 关键知识点（FR-CONV-05）
  Cmd+Shift+T 触发

Callout 2 · 用户新增（对应"3 态理解程度"）:
  [!confidence]+ 理解程度
  body 固定 3 选 1：
    - ☐ 完全理解 (confidence: high)
    - ☐ 似懂非懂 (confidence: mid)
    - ☐ 完全不理解 (confidence: low)
  Cmd+Shift+C 触发
  frontmatter 自动同步 confidence_marks: [...]
```

**用户需要确认**: 选 A 还是 B？（我默认推荐 B，让用户的诉求得到精准满足，同时最小化偏离 PRD）
**User：选择 B，但是请你先仔细 deep explore 我们 /Users/Heishing/Desktop/canvas/canvas-learning-system/_bmad-output/planning-artifacts/recovered 中的 PRD 文件以及我的个人批注，还有我们前端和后端所实现的代码****

> **[A4 2026-04-14 → round3]** ✅ 采纳"选 B"但**命名修正**。Round 2 方案 B 的 `[!confidence]+` callout 名字**不匹配前端实现**。Round 3 最终 callout 设计 100% 对齐 `InlineAnnotation.tsx:35` 真实 4 种 category：`[!tips]+` / `[!error]+` / `[!question]+` / `[!keypoint]+`，每种 callout 内嵌 3 选 1 理解程度 checkbox（已懂/模糊/不懂）。frontmatter 同步 `tips[]` / `errors[]` / `questions[]` / `keypoints[]` 4 数组。
> 完整 callout schema：[[obsidian-qa-round3-claude-answers-2026-04-14#R3-QA7-选-B-的-recovered-深度证据|📚 R3-QA7]]
### Obsidian 可导航引用

- `prd-v0-original-tauri.md:751` — FR-CONV-05 Tips 标注（PRD 唯一原生批注）
- `prd-v0-original-tauri.md:752` — FR-CONV-06 错误 4 主类（含"似懂非懂"作为错误分类）
- `prd-v0-original-tauri.md:800-801` — FR-MAST-05 Area9 答前自评（理解程度的真实对应机制）

---

## R2-Q8.2 · Q8 引用补全

> **用户 round-2 原话**: "同样你这里的 callout 相关内容引用是不存在的"

### Explore 2 调研结论

Round-1 Q8 引用的 `[[karpathy-graphify-insights-2026-04-13|📚 Agent E §Q3 6 callout 设计]]` **是幻觉**。

### 纠正

6 callout 设计整个方案偏离 PRD（见 R2-Q8.1），此 wikilink 也指向不存在的 section。**引用和方案同时作废**。

### 新方案

引用替换为 PRD 原文行号（见 R2-Q8.1 底部）。不再引用 karpathy 文件的虚构 section。

---

# T2 · AI 解释批注

## R2-Q9 · 理解程度标记的原 PRD 映射

> **用户 round-2 原话**: "标记出我的理解程度，是核心，你这里没有告诉我你该如何给我标记理解程度"

### Explore 1 调研结论

PRD 的理解程度追踪机制有 2 层:

1. **答前自评**（Area9 式 2x2，FR-MAST-05 Line 800-801）:
   - 考察时 AI 问"你觉得自己会这道题吗？"
   - 用户选 "会 / 不会"
   - 配合实际答题结果 → 4 象限：（自信+正确）/（自信+错误）/（不自信+正确）/（不自信+错误）
   - 用于**校准追踪**

2. **错误自动分类**（FR-CONV-06 Line 752）:
   - AI 评分后自动归类到 4 错误主类之一：破题 / 推理 / 知识点缺失 / 似懂非懂
   - "似懂非懂" 已覆盖用户说的中间状态

### 纠正

Round-1 我说"用户手动打 callout 标理解程度"**偏离 PRD**。PRD 的理解程度是**系统自动推断**（答前自评 + 答题结果 + 错误分类），**不是用户主动标记**。


### 新方案（2 层结合）

**Layer 1 · 被动（PRD 原生，无需用户动手）**:
- 考察时 Area9 答前自评 → 系统自动记录 confidence 标签
- 答题后 AI 归类到 4 错误主类之一 → 自动标记

**Layer 2 · 主动（用户新诉求，新增）**:
- 用户在节点 md 里 `[!confidence]+ 理解程度` callout（见 R2-Q8.1 方案 B）
- 3 选 1：完全理解 / 似懂非懂 / 完全不理解
- frontmatter `confidence_marks: [{text, mark, timestamp}]` 同步
- 考察出题时 AI 优先对"似懂非懂 / 完全不理解"的内容出题
**User：Layer 1 · 被动 这里明明是用在检验白板，而不是在使用原白板的时候进行标记； Layer 2  这里明明就是对照我们原来前端的选中对划框的文本来书写我们的 tips ，然后再来标记理解程度，请你请你先仔细 deep explore 我们 /Users/Heishing/Desktop/canvas/canvas-learning-system/_bmad-output/planning-artifacts/recovered 中的 PRD 文件以及我的个人批注，还有我们前端和后端所实现的代码******

> **[A4 2026-04-14 → round3]** ✅ Round 3 重新定位两层：**原白板剖析 = Layer 2 划框写 Tips**（用户主动，选中对话文本 + 4 Tag + 3 态理解度）；**检验白板考察 = Layer 1 Area9 答前自评**（AI 引导，答前问"会吗"+ 答后 4 象限校准）。Round 2 R2-Q9 把 Layer 1 错放在原白板（R2-Q9 "考察时 Area9 答前自评 → 系统自动记录 confidence" 是 Layer 1 但说错了时机）。Round 3 修正后两层完全独立不冲突。
> 完整两层时机表：[[obsidian-qa-round3-claude-answers-2026-04-14#R3-QA8-Layer-1-vs-Layer-2-划框写-Tips|📚 R3-QA8]]
### Obsidian 可导航引用

- `prd-v0-original-tauri.md:800-801` — FR-MAST-05 Area9 答前自评
- `prd-v0-original-tauri.md:752` — FR-CONV-06 错误自动分类

---

# T3 · 检验白板

## R2-Q10.1 · Graphiti 历史误解触发机制

> **用户 round-2 原话**: "这里关于 Graphiti 的历史误解记录是如何触发记录的，这一点你也没有给我明确下来机制"

### Explore 3 调研结论（代码深挖）

**当前机制（部分实现）**:

```
score_answer(student_answer) [exam_tools.py:366-542]
  → autoscore.evaluate() → grade 1-4
  → 发布 SCORE_SUBMITTED 事件 [exam_tools.py:480-491]
    → handle_score_submitted [event_handlers.py:35-100]
      → BKT/FSRS 更新
    → ⚠️ 不自动触发 MEMORY_WRITE_REQUESTED
  
  显式触发 MEMORY_WRITE_REQUESTED 事件（由上游）
    → handle_memory_write_requested [event_handlers.py:244-277]
      → memory_service.record_learning_event() [memory_service.py:346-481]
        → _enqueue_episode() [memory_service.py:464-474]
          → GraphitiEpisodeWorker.enqueue [episode_worker.py:1-150]
            → asyncio.Queue 异步处理
            → graphiti.add_episode() [sequential]
```

**当前缺口**（Explore 3 报告 M1）:
1. `MEMORY_WRITE_REQUESTED` 不自动触发（需要上游显式发事件）
2. `record_learning_event` 不区分"学习成功" vs "误解"（episode body 无错误分类信息）
3. 后续 `generate_question` 不检索历史误解

### 纠正

Round-1 Q11 说"Graphiti 历史误解记忆需要显式让 AI 调 `search_memory_facts`"部分正确，但**未暴露机制缺口**。

### 新方案（缺口补救）

**Story 11.X 新增任务**:
1. **自动触发**: `score_answer` 中 `grade ≤ 2` 时自动发布 `MEMORY_WRITE_REQUESTED` 事件
2. **区分 episode 类型**: episode body 格式升级：
   ```
   type: misconception  # 新增
   error_class: 推理谬误  # FR-CONV-06 4 主类之一
   student_answer: "..."
   correct_answer: "..."
   grade: 1
   ```
3. **检索整合**: `generate_question` 在 QuestionGenerator 里增加第 5 路数据源 Graphiti 历史误解
**User：Graphiti 上的记忆检索和记忆注入，我之前都是用 hook 来触发的，但是我们现在 Canvas learning systeam 降级了，所以我们需要明确的一点是 Graphiti 在我们这里的定位是什么？我们现在有批注，有双向链接来连接各个节点**

> **[A4 2026-04-14 → round3]** ✅ Round 3 明确 Graphiti 新定位。**Tauri 用 Agent SDK PostToolUse Hook 自动触发**（`/recovered/prd-tauri:77`），但 **Obsidian 完全没有 hook 概念**（插件 API 无 PostToolUse），必须改 **Claude Code Skill + MCP 工具**（手动 + 隐式触发）。新架构：3 Skill — (1) `/chat_with_context` 对话前自动注入（隐式）；(2) `/record_annotation` 用户标注时触发；(3) `/start_exam_board` 生成检验白板时触发检索 + 写入。Graphiti 后端 `GraphitiEpisodeWorker`（`backend/app/services/episode_worker.py`）**完全不变**（asyncio.Queue 异步写入）。一句话总结：**Graphiti = Canvas 的 "AI 专用记忆层"，Skill 显式触发替代 Hook 自动触发**。
> 完整方案 + 代码位置：[[obsidian-qa-round3-claude-answers-2026-04-14#R3-QA9-Graphiti-降级后定位Hook-→-Skill|📚 R3-QA9]]
### Obsidian 可导航引用

- `backend/app/mcp/tools/exam_tools.py:480-491` — SCORE_SUBMITTED 事件发布（当前）
- `backend/app/services/event_handlers.py:244-277` — MEMORY_WRITE_REQUESTED handler
- `backend/app/services/memory_service.py:346-481` — record_learning_event
- `backend/app/services/episode_worker.py:1-150` — GraphitiEpisodeWorker

---

## R2-Q10.2 · Q10 引用补全

> **用户 round-2 原话**: "依旧我没有看到相关的解释和回答回复"

### 纠正

Round-1 Q10 引用 `[[karpathy-graphify-insights-2026-04-13]]` 末尾无具体 section 定位，用户点进去看不到直接相关内容。

### 新方案

引用补全（见 R2-Q10.1 Obsidian 可导航引用），全部改为 `file.py:line` 格式（可在 IDE 验证）。

---

## R2-Q11 · Q11 空引用修复

> **用户 round-2 原话**: "你这里的文档引用依旧还空引用，我点击双向链接后没有查看到你所说的相关内容。"

### Explore 2 调研结论

Round-1 Q11 的 3 条引用:
- `Agent B §Q3 检验白板检索` — 🔴 幻觉
- 其他 — 🔴 幻觉

### 纠正

全部删除，替换为 Explore 3 提供的真实 file:line 引用。

### 新方案（检验白板真实检索清单）

**QuestionGenerator 三因子加权选题**（`backend/app/services/question_generator.py:45-48`）:
```python
W_MASTERY = 0.4        # 1 - p_mastery
W_RETRIEVABILITY = 0.3 # 1 - R (FSRS)
W_KG_RELEVANCE = 0.3   # 知识图谱关联度
```

**实际检索源**:
| 优先级 | 数据源 | 代码 | 用途 |
|-------|------|------|------|
| 1 | 节点 mastery (Neo4j EntityNode) | `_get_mastery_data(node_id)` | p_mastery + fsrs_retrievability |
| 2 | Neo4j 知识图谱关系 | `_get_kg_relevance(node_id, source_canvas_id)` | 关联节点权重 |
| 3 | 节点 frontmatter callouts | Canvas YAML 提取 | 例题 / 关键点 / 常见错误 |
| 4 | EntityNode interaction_count | EntityNode 属性 | 复习频率信号 |

**注意**: `generate_question` 当前**不直接调 LanceDB / Graphiti**。Graphiti 历史误解需显式调用（见 R2-Q10.1 缺口 3）。
 **User：请你 deep explore 我们 /Users/Heishing/Desktop/canvas/canvas-learning-system/ _bmad-output/planning-artifacts/recovered 中的 PRD 文件以及我的个人批注，还有我们前端和后端所实现的代码 ；查看一下我们之前的检验白板是如何设计权重来出题的，然后请你结合社区成熟案例和学术论文给我列出 10 个成熟的关于检验白板的考察方案**

> **[A4 2026-04-14 → round3]** ✅ Canvas 权重公式真实存在（`backend/app/services/question_generator.py:45-48`：W_MASTERY=0.4 / W_RETRIEVABILITY=0.3 / W_KG_RELEVANCE=0.3），与学术共识一致。Agent C 深度调研 10 方案按 Canvas 适配度排序：**① Retrieval Practice (Karpicke & Blunt 2011, d=1.50)** / ② FSRS 间隔重复（已集成）/ ③ Metacognitive Calibration (Area9, d=1.00) / ④ Active Recall (Roediger & Karpicke 2006, d=1.20) / ⑤ Generation Effect (Slamecka & Graf 1978, **d=1.20**) / ⑥ Corrective Retrieval CRAG / ⑦ Adaptive Testing IRT / ⑧ Bloom's Taxonomy + IRT / ⑨ Interleaved Practice / ⑩ Feynman Technique。**3 个最推荐（Canvas 现状 + Obsidian 降级）**：①+③ 零成本 d=1.50；⑦ 补 IRT 减题量 40-60%；⑤ 纯 prompt 工程 d=1.20。
> 完整 10 方案 + arxiv URL + 效应量：[[obsidian-qa-round3-claude-answers-2026-04-14#R3-QA10-10-社区考察方案Agent-C-深度调研|📚 R3-QA10]]

### Obsidian 可导航引用

- `backend/app/services/question_generator.py:45-48` — 三因子权重常量
- `backend/app/mcp/tools/exam_tools.py:155-250` — score_answer 主逻辑
- `backend/app/services/mastery_store.py:48` — group_id 强制过滤

---

## R2-Q12 · Q12 空引用修复

> **用户 round-2 原话**: "依旧你这里的引用文档的内容是缺失的"

### Explore 2 + Explore 3 调研结论

Round-1 Q12 引用 `[[karpathy-graphify-insights-2026-04-13|📚 Agent B §Q5 节点提取时机]]` — **幻觉**。

真实情况（Explore 3）:
- `/extract_node` MCP 工具**后端未实现**（Grep 零结果）
- 前端 Tauri 有 `frontend/src/stores/exam-store.ts:recordNodeDiscovered` 但仅前端记录
- 后端只有 `ExamService.sync_node_to_source_canvas()` 做节点同步

### 纠正

Round-1 说"用户主动 recordNodeDiscovered 已实现"**不准确** — 仅前端记录，后端 MCP 缺失。

### 新方案

**Story 11.X 新增任务**:
- 实现后端 MCP 工具 `extract_node(canvas_id, slug, content, source_exam_board)`
- 创建 `wiki/concepts/<slug>.md` frontmatter stub
- 更新 `exam_boards/*.md` 插入 `[!discussion_later]+ [[<slug>]]`
- 不切 Tab（保护 Active Recall d=1.50）

**提取时机由用户决定**（你的 round-1 确认）:
- 考察中按快捷键 `Cmd+Shift+X` → Claudian 提示输入 slug → 触发

### Obsidian 可导航引用

- `frontend/src/stores/exam-store.ts:recordNodeDiscovered` — 前端现有机制
- `backend/app/services/exam_service.py:150-200` — sync_node_to_source_canvas（相关但非 extract_node）
- **缺口**: 后端 `/extract_node` MCP 工具未实现，进 Story 11.X

---

# T4 · FSRS

## R2-Q13 · Q13 空引用 + 后端 FSRS 真实设计

> **用户 round-2 原话**: "依旧你引用的文档不存在，然后请你查看一下之前我的 后端 FSRS 是怎么设计的？"

### Explore 3 调研结论（代码深挖）

**库**: `py-fsrs`
**粒度**: **节点级**（每个 EntityNode 一张 FSRS 卡片）

**6 字段**（存 Neo4j EntityNode 属性）:
```python
fsrs_stability: float      # 记忆稳定性
fsrs_difficulty: float     # 题目难度 1-10
fsrs_state: int            # FSRS 状态枚举
fsrs_reps: int             # 复习次数
fsrs_lapses: int           # 遗忘次数
fsrs_card_data: Optional[str]  # 完整 FSRS Card JSON
```

**更新链路**:
```
score_answer → grade 1-4
  → update_bkt(node_id, grade)   # [mastery_tools.py:240-290]
  → update_fsrs(node_id, grade)  # [mastery_tools.py]
    → FSRSManager.update_card_state(grade)  # [review_service.py:225-227]
      → 计算新 stability/difficulty/next_review_at
    → MasteryStore.save_concept()  # [mastery_store.py:81]
      → Neo4j EntityNode MERGE
```

**BKT + FSRS 融合**（`backend/app/mcp/tools/mastery_tools.py:193-194`）:
```python
effective_proficiency = min(p_mastery, R)  # 降级公式
```

### 纠正

Round-1 Q13 引用 `Agent B §Q2 FSRS 设计代码` — 幻觉引用。现用真实 file:line 替换。

### 新方案

1. **采纳节点级 FSRS 现状**（已实现）
2. **新增白板级聚合**（见 R2-Q0.6.2 方案）
3. **缺口**: 白板级 endpoint 进 Story 11.X

### Obsidian 可导航引用

- `backend/app/services/review_service.py:195-231` — FSRSManager 入口
- `backend/app/services/mastery_store.py:48, 85` — group_id 过滤 + FSRS 字段持久化
- `backend/app/mcp/tools/mastery_tools.py:193-194, 240-290` — BKT/FSRS 融合 + update_fsrs
- `backend/app/models/mastery_state.py:87-93` — 6 字段 frontmatter schema

---

# T5 · 跨会话恢复

## R2-Q15 · 对话归档 "关闭节点" 判断 + Q15 引用补全

> **用户 round-2 原话**: "你这里引用的文档不存在，然后还有一点就是你到底怎么判断我是关闭节点的。"

### Explore 3 调研结论（代码深挖）

**后端归档机制**（**不是前端"关闭节点"事件**）:
```
backend/app/services/archive_scheduler.py:44-75
  → 启动 asyncio 定时任务
  → 每 24 小时执行 _run_check() [archive_scheduler.py:99-115]
    → conversation_archive.check_and_archive() [conversation_archive.py:139-260]
      → 双触发:
        - 时间: 最旧消息 > 30 天 → Hot→Warm
        - 时间: 最旧消息 > 6 月 → Warm→Cold
        - 容量: 单节点对话 > 50K tokens → 立即 Hot→Warm
```

### 纠正

Round-1 Q15 说"推荐关闭节点时归档（Tauri exam-store 已验证）" **完全错误** — Tauri 也是后端定时触发，不是前端关闭事件。

### 新方案

**Obsidian + Claudian 迁移方案**（Explore 3 推荐）:
**User：我觉得这个方案可行，我们现在对话现在是会被 claude code 本身的 session 存储一遍，然后也会来生成一个相关的对话文件来储存我们的对话是吗？**

> **[A4 2026-04-14 → round3]** ⚠️ **部分纠正用户假设**。对话**三存储**真实存在：(1) **Claude Code CLI session JSONL**（`~/.claude/projects/<project-hash>/*.jsonl` 完整原始对话 append-only）；(2) **前端 Dexie IndexedDB** 缓存；(3) **后端 SQLite ArchiveStatus** 只记元数据 JSON（`backend/app/services/conversation_archive.py:35-64`）。**不自动生成 `outputs/sessions/*.md` 文件**（用户假设不成立）。如需 md 文件，可新建 `/archive_conversation` Skill 手动触发（导出 JSONL → 格式化 md）。另有 **Graphiti Neo4j** 存学习痕迹（Tips/errors/episodes）。四存储各自独立不自动同步。
> 完整三存储对比：[[obsidian-qa-round3-claude-answers-2026-04-14#R3-QA11-对话三存储验证|📚 R3-QA11]]
使用 Obsidian 原生事件 `app.workspace.on('file-open')`:
```typescript
app.workspace.on('file-open', async (file: TFile | null) => {
  if (!file) return;
  
  const previousNodeId = store.getActiveNodeId();
  if (previousNodeId) {
    // 文件切换时，前节点立即归档
    await fetch('http://localhost:8000/api/v1/archive/check', {
      method: 'POST',
      body: JSON.stringify({ node_id: previousNodeId })
    });
  }
  
  store.setActiveNodeId(file.basename);
});
```

**组合策略**:
- 即时触发：文件切换（Obsidian `file-open` 事件）
- 兜底触发：后端 24 小时定时（现有机制）
- 容量触发：50K tokens 自动触发（现有机制）

### Obsidian 可导航引用

- `backend/app/services/archive_scheduler.py:44-75` — 定时任务
- `backend/app/services/conversation_archive.py:139-260` — 双触发逻辑
- `backend/app/api/v1/endpoints/archive.py:63-91` — archive/trigger endpoint
- **待新建**: Claudian plugin 的 `file-open` hook 集成代码（Story 11.X 一部分）

---

# Tag 体系

## R2-Q16 · Karpathy 仅作参考 + Canvas 主体落地

> **用户 round-2 原话**: "我是要我的 Canvas learning system 的学习方法完全落地，Karpathy 只是给我的 obsidian 关于落地 Canvas learning system 的 obsidian 配置提供参考建议"

### Explore 1 调研结论

**原 PRD 的 Canvas 学习思路是主体**，Karpathy llm-wiki 只是借鉴点：
- PRD 的 12 个学习设计（Retrieval Practice d=1.50 / EI d=0.80 / SE d=1.00 等）是 Canvas 的核心
- Karpathy 贡献 = 帮助在 Obsidian 里落地（如 `index.md` 入口、三层 vault 分离、callout 驱动）
- **不是 Canvas 借 Karpathy 重新设计**

### 纠正

Round-1 过度引用 Karpathy 方案（如 Concepts/Proofs/Gotchas 分组），偏离 Canvas PRD 主体。

### 新方案

**优先级顺序**（从强到弱）:
1. **原 PRD 规定** → 无条件遵守（FR-CONV-05 Tips / FR-MAST-05 Area9 / FR-CONV-06 错误分类）
2. **Tauri 前端实现** → 映射到 Obsidian 等价（每节点 session / 拉节点 / 掌握度颜色）
3. **Obsidian 原生能力** → 替换缺失的 UI（Bases / Graph View / Dataview）
4. **Karpathy 参考** → 仅在 PRD 沉默处借鉴（分组、index.md 入口、log.md 审计）

### Tag 体系最终方案（Canvas 主体）

**纯 group_id + frontmatter**（后端已实现，Story 11.X 无需新增）:
- `group_id`: 白板隔离（= canvas_id）
- `subject`: 学科（PRD Line 518）
- `source`: 节点来源（PRD Line 280-282）
  **User：这里的节点来源的设置是什么意思？**

> **[A4 2026-04-14 → round3]** ✅ `source` 字段 PRD 原生（`/recovered/prd-tauri:280-282`），5 种来源：`manual`（手动创建）/ `pullout`（对话拉出）/ `exam_generated`（检验白板生成）/ `imported`（外部导入）/ `ai_recommended`（AI 推荐）。**3 个实际作用**：(1) **信度权重**（FR-CONV-06 错误分类时 manual 权重高、ai_recommended 权重低）；(2) **审计追溯**（FR-TRACE-02 用户打开节点看到"2026-04-10 从对话拉出"，可跳转原对话）；(3) **FSRS 调度差异**（exam_generated 节点更高初始 difficulty，manual 默认）。Round 3 保留 source（PRD 原生 + 有实际作用），撤回 node_type（见 R3-QA3）。
> 完整作用解释：[[obsidian-qa-round3-claude-answers-2026-04-14#R3-QA12-节点来源-source-字段含义|📚 R3-QA12]]
- `content_type`: 内容类型（PRD Line 738-741）
- `mastery_score` + `fsrs_*`: 学习状态

**Obsidian tag 仅用于 Karpathy 风格轻量筛选**（非系统主干）:
- `#board/CS61B-LLRB` — Obsidian 原生 tag pane 浏览（替代 Dataview）
- **不要 type/state/todo 前缀 tag**（撤回 round-1 设计）

### Obsidian 可导航引用

- `prd-v0-original-tauri.md:280-282` — source 5 种
- `prd-v0-original-tauri.md:518` — subject 字段
- `prd-v0-original-tauri.md:738-741` — content_type
- [[canvas-crossdiscipline-tags-v1]] — ⚠️ **已作废**（见文件头部警示，取代方案见此 section）

---

# 原白板节点内容

## R2-Q17 · 原白板节点内容真实定义

> **用户 round-2 原话**: "你完全没有理解原白板的节点内容是什么，请你 deep explore 原来的 PRD 设计。"

### Explore 1 调研结论

**PRD 原文**:
- Line 280-282: "节点结构包含文本内容（非仅标题标签）、精通度元数据、FSRS 调度参数" + "5 种节点来源验证"
- Line 738-741: "支持的内容类型包括：文本、图片、文件嵌入、链接" + "对话层通过 Agent 原生多模态能力立即可对话讨论图片；检索层后台异步提取文字/公式/概念进入搜索索引"

**节点内容真实定义**:
```
节点 = 文本内容片段 + 多媒体（图片/表格/代码 / 文件 / 链接）+ metadata
  ├─ body: 用户粘贴的原始素材（题目 / 截图 / 论文摘要 / 等）
  ├─ frontmatter:
  │   ├─ source: 手动/对话拉出/检验生成/导入/AI推荐
  │   ├─ content_type: text/image/link/embed
  │   ├─ subject: 学科
  │   ├─ canvas_id: 白板归属
  │   ├─ group_id: = canvas_id
  │   ├─ mastery_score: 0.0-1.0
  │   └─ fsrs_*: 6 字段
  └─ 关联（不在节点里，在外部）:
      ├─ Tips → Graphiti（对话标注，FR-CONV-05）
      ├─ 错误 → Graphiti（自动分类，FR-CONV-06）
      └─ Edge 关系 → Neo4j Graphify
```

### 纠正

Round-1 我说"节点 = frontmatter tips[] + errors[] + 多层结构"**完全错误**。Tips 和 errors **不在节点 frontmatter**，是独立存 Graphiti 的。
**User：这里我需要得到一个 Graphit 的验证，我需要你证明，tips[] + errors[] 这个内容是存在我们的 md 节点文档，然后本身的双向链接来给claudian 检索高效还是放在 Neo4j 后端检索高效，因为我们相当于有两个关系图谱。**

> **[A4 2026-04-14 → round3]** 🚨 **Round 2 R2-Q17 "Tips 不在 frontmatter" 完全错**。Round 3 核实：**三存储 all-of**（同时存）：(1) md frontmatter `tips[]` / `errors[]`（用户可见 + Dataview 查询 ⚡极快）；(2) Neo4j EntityNode + Graphiti episode（AI 可见 + 语义向量 + 错误分类 🔵中等）；(3) SQLite ArchiveStatus（长期归档 🟡慢）。**哪个更高效按场景分**：用户浏览用 md/Dataview；AI 语义检索用 Neo4j；跨白板统计用 Neo4j Cypher；长期归档用 SQLite。**"两个关系图谱"对应**：(A) Obsidian Wikilink Graph（`[[xxx]]` 双链 - 用户人工关系）；(B) Neo4j Graphiti（语义图谱 - AI 自动提取）。不冲突，分工明确。
> 完整三存储 + 两图谱对比：[[obsidian-qa-round3-claude-answers-2026-04-14#R3-QA13-tips-errors-存储位置对比md-vs-Neo4j|📚 R3-QA13]]

### 新方案

**原白板节点 md 最小 frontmatter**（Canvas PRD 原生）:
```yaml
---
source: manual
content_type: text
subject: cs61b
canvas_id: CS61B-LLRB
group_id: CS61B-LLRB
mastery_score: 0.0
fsrs_stability: 0.0
fsrs_difficulty: 0.0
fsrs_state: 0
fsrs_reps: 0
fsrs_lapses: 0
fsrs_next_review_at: null
---

# <节点标题>

<用户粘贴的题目 / 概念 / 资料原文 — 不需要特殊格式>
```

**Tips 和错误由后端管理**:
- 用户标记 Tips → Claudian 调 `record_tip(node_id, tip_text)` → 写 Graphiti + **同步 md body** 末尾追加 `[!tip]+` callout（方便用户查看，**不是 frontmatter**）
- AI 评分后错误 → 自动归类到 Graphiti（FR-CONV-06）

### Obsidian 可导航引用

- `prd-v0-original-tauri.md:280-282` — 节点结构定义
- `prd-v0-original-tauri.md:738-741` — content_type + 两层处理
- `prd-v0-original-tauri.md:751` — Tips 在对话（FR-CONV-05）
- `prd-v0-original-tauri.md:752` — 错误自动归档（FR-CONV-06）

---

## R2-Q18 · Q18 引用补全

> **用户 round-2 原话**: "我是完全没有看到你所引用的内容"

### 纠正

Round-1 Q18 引用的 `Agent E §Q7` — 幻觉。三个补偿方案的原始分析**在对话中产出，未写入 karpathy 研究文档**。

### 新方案

**5 个损失补偿的最终决策**（用户 round-1 已批）:

| # | 损失 | 用户决策 | 实施 |
|---|-----|--------|------|
| 1 | 实时颜色 60fps | 放弃 | 无 |
| 2 | 空间心智地图 | 放弃 | 无 |
| 3 | 连线流畅性 | QuickAdd macro | **Story 11.X 含 `Cmd+Shift+L` wikilink suggester macro** |
| 4 | Agent 主动推荐 | 用户主动（Q12）| 无额外实现 |
| 5 | 多节点并行 | Obsidian 多 Tab + Dashboard 聚合 | **Story 11.X 含 Bases + Meta Bind Dashboard** |

### Obsidian 可导航引用

- 参考 R2-Q0.6.2 (Dashboard 聚合)
- 参考 R2-Q7 (连线流畅性 Level 2 Fallback)

---

# 后续动作清单

完成用户审计后：

1. **新建 Story 11.X**（补后端 3 大缺口）:
   - 11.1: Graphiti 历史误解自动触发（R2-Q10.1）
   - 11.2: `/extract_node` MCP 工具（R2-Q12）
   - 11.3: 白板级 FSRS 聚合 endpoint（R2-Q0.6.2 / R2-Q13）

2. **新建方案文档**:
   - `canvas-dashboard-spec-v2.md`（Bases + Meta Bind 配置）
   - `canvas-hotkeys-spec-v2.md`（Templater 模板 + 快捷键映射）
   - `claudian-extract-node-skill-v2.md`（Claudian skill 配置）

3. **修订 Story 1.2 / 1.3** 让它们对齐 round-2 结论

4. **更新 PRD 措辞**（如权限允许）: FR-ADAPT-02 + FR-CONV-11

## Changelog

- 2026-04-14 v1: Round-2 主答复文件初版，基于 3 路并行 Explore Agent 调研产出
- 调研范围: Tauri PRD v0 精确 Grep + 12 条引用真实性验证 + 后端代码路径深挖 (exam_tools/event_handlers/memory_service/episode_worker/review_service/conversation_archive 等)
