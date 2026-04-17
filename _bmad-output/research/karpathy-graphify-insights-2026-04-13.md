---
title: "Karpathy LLM-Wiki & Graphify 调研报告 — 对 Canvas Paradigm 2 的启发"
date: 2026-04-13
trigger: "Story 1.2 line 74 + Story 1.3 line 46 用户批注"
related_plan: "STORY-1-3-PARADIGM-SHIFT-v1"
research_agents: 3
type: "external-research"
---

# Karpathy LLM-Wiki & Graphify 调研报告

> **调研缘起**：Story 1.2 line 74 用户批注提出"wikilink 图的构建方式/存储方式/和 Graphiti 关系"4 个架构定位问题；Story 1.3 line 46 用户批注提出"检索定位（个人记忆 vs 笔记检索）/大规模笔记高效检索策略/Karpathy 与 Graphsify 的 Obsidian 实践启发"3 个问题。本报告通过 3 个并行 Agent（Karpathy 社区追踪 + Graphify 项目拆解 + 项目内部架构定位）综合调研后产出，用于沉淀社区一手资料，避免未来讨论时凭记忆编造。
>
> **关键纠正**：用户批注里提到的 "Graphsify" 实际拼写为 "Graphify"（作者 safishamsi）。本文统一用 Graphify。

---

## Part 1 — Andrej Karpathy 的 LLM-Wiki 架构

### 1.1 他真的用 Obsidian

- 2024-02-25 Karpathy 在 X 公开："love letter to @obsdmd" — 明确表态切换到 Obsidian 做个人知识管理
- 2026-04 发布 `llm-wiki` gist（GitHub 5000+ stars，X 达 16M views）— 公开了完整架构
- **注意**：他的**日常碎片**笔记仍用 Apple Notes 单 note（append-and-review 模式），Obsidian 主要承载 "LLM-Wiki" 这个场景

### 1.2 LLM-Wiki 三层架构

```
raw sources (不可变源材料，人写)
    ↓ LLM ingest
wiki (LLM 生成的 markdown 聚合页)
    ↓ LLM query
schema (CLAUDE.md / AGENTS.md 指挥 LLM 怎么组织)
```

- **raw sources**：原始信息（讲座、论文、书、个人笔记），人写，AI 不动
- **wiki**：LLM 读 raw 后**主动写**的聚合 markdown（Concept Pages / Entity Pages / Comparison Pages）
- **schema**：`CLAUDE.md` 告诉 LLM 怎么写 wiki（分类规则、标题格式、前缀 tag）

### 1.3 两个驱动导航的特殊文件

| 文件 | 作用 | 内容示例 |
|------|------|----------|
| `index.md` | AI 冷启动入口 | 每个 note 一行摘要 + wikilink 目录 |
| `log.md` | append-only 操作审计 | `2026-04-13T10:00 ingest: llrb-tree.md`、`query: "left rotate"` |

### 1.4 他的核心哲学（反 RAG）

> "Knowledge is compiled once and then kept current, not re-derived on every query."
> — Karpathy llm-wiki gist

要点：
- **一次 compile**：ingest 阶段 LLM 就把"Concept Page / Entity Page"写成独立 md 文件
- **query 时只读聚合页**：不再现场拼装、不再跑向量检索
- 约 100 篇文章 / 400k 字之后，LLM agent 能回答复杂问题，不需要 embedding 管道

### 1.5 检索友好的前缀 tag

Karpathy append-and-review 用 `watch:` / `listen:` / `read:` 前缀——让 Cmd+F 和 LLM 都能一秒筛选。CS 学习场景可类比迁为 `concept:` / `proof:` / `gotcha:` / `review:`。

---

## Part 2 — Graphify（`safishamsi/graphify`）项目拆解

### 2.1 项目核心

- **类型**：AI 编码助手 **skill / CLI 工具**（**不是** 传统 Obsidian 插件）
- **做什么**：一条 `/graphify` 命令把任意文件夹（代码/文档/论文/图片/视频）转成可查询的知识图谱，生成 Obsidian vault + wiki
- **社区热度**：Karpathy 本人在 Threads 点名后 48h 内爆火；作者 `safishamsi`
- **关键卖点**：52 文件混合 corpus，相比让 AI 读原文 **节省 71.5× tokens**

### 2.2 三段 Pipeline

```
AST 确定性提取（Tree-sitter 20 语言，0 LLM 成本）
    ↓
转录（faster-whisper 本地跑，不依赖云）
    ↓
Claude subagents 并行语义提取（LLM 只做语义层）
    ↓ 边带 3 种 tag
    EXTRACTED / INFERRED / AMBIGUOUS + 0-1 confidence
    ↓
NetworkX + Leiden 聚类（按边密度分簇，替代向量库）
```

### 2.3 暴露的 4 个正交 MCP 工具（关键！）

```
query_graph(query, depth, token_budget)
get_node(node_id)
get_neighbors(node_id)
shortest_path(from, to)
```

**这对 Canvas Story 1.3 的 8 工具设计几乎是同一思路**。说明"拆多个正交 MCP 工具"是 2026 社区收敛答案，不是我们独创。

### 2.4 Obsidian 集成

- `--obsidian` flag → 输出 per-community markdown + `index.md` 入口（Karpathy 风格！）
- 可选推 Neo4j bolt（如需图数据库持久化）
- `graph.json` 纯本地持久化产物，无强制依赖 Neo4j

### 2.5 Graphify 与 Canvas Learning System 的关键差异

| 维度 | Graphify | Canvas |
|------|---------|--------|
| 目标 | 让 AI 理解**代码库** | 让人**学习**知识 |
| 核心数据 | 代码 AST + 文档 | 学习笔记 + FSRS 复习 |
| 缺少的能力 | 掌握度、间隔复习、session 记忆 | —（Canvas 独有） |

所以 Canvas 可以借鉴 Graphify 的**架构模式**，但不能直接套用其数据模型。

---

## Part 3 — 项目三套检索系统（官方 PRD 定义）

### 3.1 PRD §三套检索系统（line 317-323）

| 系统 | 定位 | 技术栈 | 更新 | Token 效率 |
|------|------|--------|------|-----------|
| **Graphify**（项目内部同名组件） | 笔记关系（概念间结构） | `graphify_core + Neo4j` | 定期手动触发 | 71× 压缩 |
| **LanceDB + bge-m3** | 笔记片段（精确段落） | LanceDB 向量库 + Ollama bge-m3 | 实时增量（文件保存） | 1× |
| **Graphiti + Neo4j** | 个人记忆（错误/历史/掌握度） | Neo4j 知识图谱 + EventBus MCP | 自动异步 | N/A |

### 3.2 Graphify 真相（2026-04-13 深度修正）

#### 初版推测（已作废）
- ~~外部 Graphify：`safishamsi/graphify` 开源项目（本报告 Part 2）~~
- ~~项目内部 Graphify：PRD §三套检索系统里的自研组件（可能借其名或命名巧合）~~
  **User1：这里面项目的内部Graphify 请你给我调查清楚究竟是什么？**

> **[A1 2026-04-13]** 深度调查（独立 Explore Agent 扫 PRD + architecture + backend code + Git log + OpenSpec）结论：**外部 Graphify 和"项目内部 Graphify"是同一个东西，不存在命名冲突**。
>
> **真相**：所谓"项目内部 Graphify" = 计划集成 `graphifyy` v0.3.17 PyPI 包（即 `safishamsi/graphify` 的 Python 发行版）。**不是自研**。
>
> **分类**：⚠️ **空规划**（PRD 写了但代码没落地），比 G-FAKE（有名无实的代码）更隐蔽。

#### 当前状态矩阵

| 维度 | 状态 |
|---|---|
| PRD line 76 声明 | ✅ `Graphify v0.3.17` 列入技术栈 |
| PRD line 317-323 | ✅ 列入三套检索系统 |
| backend/requirements.txt | ❌ **未添加 `graphifyy` 依赖** |
| `backend/**/*graphify*.py` | ❌ **零文件** |
| `class Graphify` 定义 | ❌ 不存在 |
| Story 3.2 (关系提取) | 📋 ready-for-dev，**从未启动** |
| Story 3.5 (KG 健康检查) | 📋 ready-for-dev，**从未启动** |

#### 建议后续动作

1. **若保留 Graphify 集成**：`backend/requirements.txt` 添加 `graphifyy>=0.3.17`，排期 Story 3.2/3.5
2. **若改用 Wikilink 图替代**：Story 3.2/3.5 改为"基于 wikilink 图的关系检索"，免外部包
3. **PRD 措辞修正**：把"项目内部同名组件"改为"计划集成 `graphifyy` v0.3.17 PyPI 包（即 `safishamsi/graphify` 的 Python 发行版）"

#### 原"命名冲突警示"作废

既然外部 Graphify 和"项目内部 Graphify"是同一个东西，**不存在命名冲突**。之前建议内部组件改名 `NoteGraphIndex` / `CanvasGraphify` 的提议**撤回**。

### 3.3 Story 1.2 Wikilink 图的架构定位

- **不属于三套检索系统的任何一套**
- 定位：**笔记检索系统的前置基础设施**
- 技术：obsidiantools（Python，NetworkX-based）
- 消费者：Story 1.3 的 `get_neighbors` MCP 工具（Paradigm 2 AI 按需调用）

### 3.4 Story 1.3 MCP 工具的架构定位

- 全部 8 个工具属于 **「笔记检索」** 方向
- **不涉及** Graphiti / LanceDB / Graphify 组件（这些有独立的 MCP 工具）
- 工具访问路径：
  - `read_note` / `extract_tips` / `extract_errors` / `get_relationships` / `get_frontmatter` / `list_wikilinks` → 直接读 `.md` 文件
  - `get_neighbors` → 调 WikilinkGraphService（Story 1.2 内存图）
  - `read_canvas_node` → 读 `.canvas` JSON

### 3.5 Graphiti vs Wikilink 图 — 分工对照

| 维度 | Wikilink 图（Story 1.2） | Graphiti + Neo4j |
|------|---|---|
| 存什么 | 笔记间的**静态**引用关系 | 你的**动态**学习史：错误、掌握度、对话事件 |
| 存在哪 | 后端内存（NetworkX Python 对象） | Neo4j 数据库（port 7689，group_id `canvas-dev`） |
| 更新时机 | 文件保存 → 热更新 | 对话/考察/错误时 episode_worker 异步写入 |
| 典型查询 | "LLRB 相邻概念" | "我以前在哪些错误上摔过跤" |

### 3.6 性能目标（PRD NFR-PERF line 530-538）

- Wikilink 图构建：~200 文件 + ~500 links **< 2s**
- 2-hop 邻居遍历 **< 200ms**
- LanceDB 增量索引 **< 500ms/file**
- Graphiti 记忆搜索 **< 3s**

---

## Part 4 — 5 条可操作借鉴 Insight（按优先级排序）

### P0（Story 1.3 即可加入）

1. **加 `index.md` 入口工具** — 新增第 9 个 MCP 工具 `read_index()` 返回 vault 概览。AI 冷启动先读一页 overview 再决定深挖子图。
   - 证据：Karpathy llm-wiki 核心 + Graphify `--obsidian` 同样生成 `index.md`
   - 实施成本：低（1 个 MCP 工具 + vault 预处理脚本）

### P1（后续 Story 考虑）

2. **预编译聚合页** — ingest 阶段写好"概念总结页"，query 时 AI 只读已编译聚合，不每次现场拼装。
   - 证据：Karpathy "compile once, keep current"
   - 对抗的坑：Paradigm 2 退化成 RAG-lite
   - 实施成本：中（需要 ingest pipeline + 定期 rebuild trigger）

3. **两段式丰富流水线** — WikilinkGraph 先做 0-LLM 确定性遍历（免费）→ Graphiti 只做语义层丰富（付费）。
   - 证据：Graphify Tree-sitter → LLM 的两段模式
   - 实施成本：中（需要重新组织 context_enrichment pipeline）

### P2（Phase 2+ 探索）

4. **Edge 三态 tag + confidence 迁到掌握度系统** — `EXTRACTED`（直接有笔记记载） / `INFERRED`（AI 推测） / `AMBIGUOUS`（待复核），配 0-1 confidence。
   - 证据：Graphify edge tag 模型
   - 对齐价值：与 BKT / FSRS 的不确定性建模天然契合
   - 实施成本：中-高（touch 掌握度数据模型）

5. **Leiden 社区聚类做笔记簇自动发现** — 按 wikilink 边密度分簇（替代向量固定维度）。
   - 证据：Graphify `graspologic` Leiden 实现
   - 应用场景：Dashboard 自动给笔记分组、考察范围推荐
   - 实施成本：高（引入 graspologic 依赖，设计分簇触发机制）

---

## Part 5 — 风险警示

### 5.1 G-FAKE 已知坑（codebase-memory 报告）

项目后端有 **42+ 个函数名字含 `graphiti` 但实际调裸 Neo4j Cypher**（见 `docs/known-gotchas.md` G-FAKE 条目）。

- **影响**：讨论 Graphiti 时不要被函数名骗，必须读实现看真相
- **应对**：写 MCP 工具或 context assembly 时，用 `codebase-memory recall` 先确认"这个 `graphiti_*` 函数是真 Graphiti 还是伪装"

### 5.2 命名冲突风险

外部 Graphify（社区爆火项目）与项目内部 Graphify 组件同名。

- **未来讨论时**：Issue / PR / Deviation Note 必须明确标注"外部 Graphify" vs "内部 Graphify"
- **建议**：长期看将内部组件改称 `NoteGraphIndex` 或 `CanvasGraphify`

### 5.3 Paradigm 2 退化成 RAG-lite 的坑

Story 1.3 的 MCP 工具设计是"AI 每次按需读取"，但如果每次 query 都让 AI 重新读所有相关笔记 → 其实就是 RAG 的慢速版本。

- **对抗措施**：借鉴 Karpathy "compile once" 哲学，在 ingest 阶段预写聚合页
- **监控指标**：每次对话 AI 调 `read_note` 的次数——如果长期 > 10 次/对话，说明退化了

---

## Part 6 — 来源列表

### Karpathy 调研
- [Karpathy X post "love letter to Obsidian" (2024-02-25)](https://x.com/karpathy/status/1761467904737067456)
- [Karpathy llm-wiki gist (2026-04)](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [The append-and-review note (bearblog)](https://karpathy.bearblog.dev/the-append-and-review-note/)
- [VentureBeat: Karpathy LLM Knowledge Base architecture](https://venturebeat.com/data/karpathy-shares-llm-knowledge-base-architecture-that-bypasses-rag-with-an)
- [Hacker News discussion](https://news.ycombinator.com/item?id=44658745)
- [MindStudio: Karpathy's LLM Wiki](https://www.mindstudio.ai/blog/andrej-karpathy-llm-wiki-knowledge-base-claude-code)

### Graphify 调研
- [GitHub: safishamsi/graphify](https://github.com/safishamsi/graphify)
- [Graphify 官网](https://graphify.net/)
- [Graphify README v3](https://github.com/safishamsi/graphify/blob/v3/README.md)
- [Threads: Karpathy 点名 Graphify 48h 爆火](https://www.threads.com/@charliehills/post/DW0p6LQFErc/)
- [graphifyy PyPI](https://pypi.org/project/graphifyy/0.3.14/)
- [lucasrosati/claude-code-memory-setup（Obsidian + Graphify 社区集成）](https://github.com/lucasrosati/claude-code-memory-setup)

### 项目内部引用
- `_bmad-output/planning-artifacts/prd.md:317-323` — 三套检索系统官方定义
- `_bmad-output/planning-artifacts/prd.md:530-538` — NFR-PERF 性能目标
- `_bmad-output/planning-artifacts/prd.md:367` — FR-CONV-11 Paradigm 2 决议
- `_bmad-output/implementation-artifacts/epic-1/1-2-wikilink-graph-build.md:114` — "Neo4j 无关"独立性声明
- `_bmad-output/implementation-artifacts/epic-1/1-3-wikilink-context-assembly.md:113-127` — Paradigm 2 理由 + Mode D 架构

---

## Changelog

- 2026-04-13: 初版，响应 Story 1.2 + 1.3 批注，3 并行 Agent 综合调研产出
