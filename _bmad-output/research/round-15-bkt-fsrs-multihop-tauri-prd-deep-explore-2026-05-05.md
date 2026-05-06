---
title: Round 15 — BKT+FSRS+多段推理+Tauri PRD 历史设计 Deep Explore
date: 2026-05-05
trigger: round-14 line 207-208 用户批注（4 个核心机制 + 2 大压力点）
agents: 4 并行 Explore Agent (Sonnet)
related:
  - _bmad-output/research/round-14-graphiti-retrieval-deep-explore-2026-05-05.md
  - _bmad-output/planning-artifacts/recovered/prd-tauri-original-2ae5897.md
  - _bmad-output/planning-artifacts/recovered/prd-annotations-2ae5897.md
  - _bmad-output/planning-artifacts/epics.md
status: draft for user review
---

# Round 15 — BKT + FSRS + 多段推理 + Tauri PRD 历史设计 Deep Explore

## 元信息

| 字段 | 值 |
|---|---|
| 触发 | `_bmad-output/research/round-14-graphiti-retrieval-deep-explore-2026-05-05.md:207-208` 用户批注 |
| 调研方式 | 4 并行 Explore Agent（Sonnet model）|
| 日期 | 2026-05-05 |
| 范围 | 业界 BKT+FSRS+KG+LLM 综合系统 + Obsidian↔KG 同步成熟方案 + Tauri PRD/EPIC 历史设计 + 多段推理工程方案 |
| 报告字数 | ≈10000 字 |
| 状态 | 初稿，待用户审阅 4 个决策点 |

---

## 用户新批注原文（round-14 line 207-208）

> **User：我在 obsidian 上是用 obsidian 的 md 文件 然后再加上了 自己定义双向链接 来规划各个节点之间联系。**
>
> **然后我们的个人记忆系统 所使用的是 Graphiti，那么我们各个节点之间是有用 BKT 来标记理解程度，然后用到 FSRS 来标记出复习时间，那么我们这里的核心压力点：1，能不能推测出各个原白板精确复习时间；2，能不能在使用原白板生成检验白板时，是否可以精确的多段推理各个节点之间的关系，然后能理解到我各个节点相关内容所标记的理解程度，各个节点犯下的错误，以及各个节点我自己打下的批注，结合以上节点考察我，让我想起了原白板的内容，并且再次考察我是否会犯下原白板中相似的错误。**

### 拆解

**前端架构（用户已有）**：
- Obsidian md 文件
- 自己定义双向链接 → 规划节点之间联系

**后端记忆系统（已有）**：
- Graphiti（temporal KG）
- BKT（Bayesian Knowledge Tracing）→ 标记每个节点的理解程度（mastery）
  **User： 节点的理解程度是如何批判的，我个人更倾向于，我对md 节点内容所打下批注的过程，这个批注则是我的核心的想法也是我后续需要聚焦考察的点，不过请你也参考一下 Tarui 的 PRD 时期，这一部分是怎么设计的。**
- FSRS（Free Spaced Repetition Scheduler）→ 标记复习时间

**两大压力点（用户最关心）**：
1. **能否推测各原白板精确复习时间？**
2. **能否在原白板生成检验白板时，精确多段推理各节点关系**，融合：
   - 各节点理解程度（BKT mastery）
   - 各节点犯下的错误（errors / candidates）
   - 各节点用户批注（callouts）
   → 综合考察用户，让用户想起原白板内容
   → 再次考察是否会犯相似错误

---

## 一句话核心结论

**用户愿景在 Tauri PRD 时期已设计完整（覆盖度 7/10）**，但降级到 Obsidian Hybrid 时部分功能（节点 mastery 色条 / 检验白板拖拽 / 答前自评 / OLM 面板 / 四路 CRAG）被推到 Phase 2。**唯一 Tauri PRD 也没显式设计的就是"多段推理 over KG"——这是最大 Gap，但业界 4 个核心机制（BKT+FSRS 联动 / 错误回顾 / 批注出题 / 多段推理）目前在生产中均无完整先例**，意味着用户这个愿景是真实的工程机会，而不是别人已做过的 commodity feature。

**User：我原本使用 Graphiti 的原因之一就是我之前查到资料，Graphiti 的多段推理能力在 Graph RAG 上表现的十分优秀，所以我才选择它**

**好消息**：4 个 Agent 均给出可直接落地的工程方案——**总工作量约 10-13 天**（含 round-14 推荐的 6-7 天 Graphiti 修复）。

---

## 第一部分：业界 BKT+FSRS+KG+LLM 综合系统盘点（Agent 1）

### 1.1 一句话结论

**「需自己组合」** — 4 个核心机制在学术界均有独立成熟原型，但**完整打包成生产系统**截至 2026 年 5 月在开源/商业产品中**均无先例**。

### 1.2 10 个同类系统真实状态

| 系统 | 规模 | 有什么 | 缺什么 | 离用户愿景距离 |
|---|---|---|---|---|
| **Anki + FSRS** | 全球最大 SRS 部署 | FSRS 时间调度（7 亿条记录训练）| 无 BKT / KG / LLM；leech 错题机制粗粒度 | 仅有 SRS 调度 |
| **ASSISTments / pyBKT** | WPI 大规模生产，2019-2024 五学年稳定 | BKT 4 参数 HMM | 无 FSRS / KG / LLM / 批注 | 仅有 BKT |
| **OATutor-LLM-Learner** (UC Berkeley) | 高中数学 ITS | BKT mastery + Firebase + LLM hint 评估 | 无 FSRS / KG / 批注 | 距离最近的 BKT+LLM 案例 |
| **Khanmigo** (Khan Academy) | 700K+ 用户（2024-25 学年）| GPT-4 + Khan 内容 + 安全护栏 | **已放弃 BKT**；无 KG / SRS | 转向 LLM-only，与愿景方向相反 |
| **LECTOR** (arxiv 2508.03275, 2025-08) | 学术原型 | LLM In-Context + 扩展遗忘曲线 | 无 BKT / KG / 批注 / 错误重生成 | LLM+SRS 最接近原型 |
| **SuperMemo SM-18/19** | 商业产品 | 20×20 stability-difficulty 矩阵（400 条遗忘曲线）| 无 LLM / KG / BKT | 最精密 SRS 但无智能 |
| **RemNote** | 商业产品 | 双链 + FSRS + LLM flashcard generator | 无 BKT / 批注作 seed / 错误回顾 | 最接近商业产品但核心机制全缺 |
| **Eureka Labs** (Karpathy) | 仅愿景层 | LLM101n 课程发布 | 无任何技术细节公开 | 仅口号 |
| **mem0 / Letta** | agent memory 中等规模 | 个性化 memory layer | 无 BKT / FSRS / 教育导向 | 通用 memory，非教育 |
| **Synthesis Tutor** | 商业 AI tutor | 综合学习路径 + 错误追踪 | 无公开 BKT / FSRS | 黑盒，无法借鉴细节 |

### 1.3 4 个核心机制成熟度

**User： Anki 的 FSRS 难道不是根据你对每个单词卡片回答记得还是不记得，从而推算出掌握程度，然后再来推算出你的复习时间吗？我的 Canvas learning systeam 的检验白板一开始也是根据我对 这个原白板中各个节点的实际掌握情况，精确推算精确的复习时间，然后生成精确的检验白板来最大限度的回顾起我原白板的一切内容。**
**所以我也不会局限于 BKT。我只是要找到最成熟最稳定的方案，因为没有人做过的东西，我很难验证，你这里所说 DKT 也就可以尝试，因为我也不知道 BKT 和 DKT 之间的区别**

| 机制                     | 成熟度                            | 关键发现                                                                                                                                                                                                                                                                                                                                                                                |
| ---------------------- | ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **A. BKT + FSRS 联动**   | 🔴 **学术原型级，无生产**               | BKT 建模"是否已掌握"（latent binary）；FSRS 建模"何时会忘记"（continuous retrievability）。**两者从未在同一生产系统中正式联动**。MLEKT (PRICAI 2025) 最接近，但在 deep KT 框架内做的，不是 BKT+FSRS 直接组合。**open-spaced-repetition/awesome-fsrs 截至 2026 年无任何 BKT 联动条目**                                                                                                                                                                 |
| **B. 错误记录 → 复习挑选**     | 🟠 粗粒度生产存在，**精细化仅学术原型**        | Anki leech（连续错 N 次暂停）是唯一大规模生产，但**仅统计频次，无错误语义**。LLM 驱动智能错题推荐：ASSISTments follow-up question（2024-25）/ LAK 2025 dialogue-kt 论文，但都是单轮 QA，**不是"3 周前在 admissibility 上犯的错 → 今天出一道触发类似思路的题"** 这种跨时间跨节点的精确重现                                                                                                                                                                                |
| **C. 用户批注 → LLM 题目生成** | 🟠 **组件存在，完整管道无生产**            | Obsidian 社区已有 Quiz Generator plugin（OpenAI/Gemini/Ollama）/ Flashcards LLM plugin / ODIN（LangChain+KG）。但都是**整段 note 喂 LLM**，**没人把 `[!error]+` / `[!tip]+` callout 的语义内容作为差异化 prompt seed**                                                                                                                                                                                           |
| **D. 多段推理生成考察题**       | 🔴 学术研究活跃，**教育场景生产 near-zero** | LLM+KG multi-hop reasoning 在 QA 任务上研究活跃（EMNLP 2024 GMeLLo / ACL 2024 RDPG / Microsoft GraphRAG）。**但这些 KG 节点是客观三元组**（entity-relation-entity），用户愿景的 KG 节点带有 mastery 分数 + 错误历史 + 个人批注等**主观元数据**。"给定一组带 frontmatter（mastery+errors+annotations）的节点 → 生成涵盖节点关系且触发用户易犯错误的综合考题"这条完整管道，在教育 AI 文献和开源项目中**均未见生产级实现**。最接近的 DeepTutor (HKUDS, 2025) 和 KG-CQ (MDPI 2025) 都没有个人 mastery/error 元数据 |

### 1.4 5 大风险（用户愿景实施前必读）

#### 风险 1（最大）：BKT 冷启动数据稀缺

- BKT 需要每个知识节点足够的答题序列才能准确拟合 4 参数（L0/T/S/G）
- 个人学习系统单节点答题次数极少（3-5 次）
- → BKT 估算的 P(mastery) 方差极大
- → 喂给 FSRS 的初始 difficulty 会严重失真

**对策**：
- 用 ASSISTments 公开数据的群体参数作冷启动 prior
- 样本稀少时降级回 FSRS 默认参数

#### 风险 2：BKT-FSRS 接口未定义

- BKT 输出 P(mastery) ∈ [0,1]
- FSRS 输入 stability s 和 difficulty d（DSR 模型 19 参数）
- **两者数学语义对齐方式无文献参考**

**自定义映射函数风险**：
- 错误的映射 → 高掌握度节点被过频复习 / 低掌握度节点被遗忘
- 推荐起点：`d = 1 - P(mastery)`，`s = f(transit_rate)`

#### 风险 3：批注语义提取一致性

- 用户写 `[!error]+ 我在 admissibility 上一直把 precedent 当成 holding`
- LLM 理解这句"可考察性"因 prompt 设计差异极大
- 需要**结构化 seed extraction pipeline**（节点 + 错误类型 + 概念关系）

#### 风险 4：多段推理"精确性"难评估

- 用户愿景要求"精确的多段推理各节点关系"
- **当前无任何自动评估指标**能验证生成题目是否真正覆盖用户历史犯错的思维路径
- 生产验证需用户逐题确认 → 工程量难预估

#### 风险 5（本项目特有）：Graphiti 与 Obsidian 批注零同步

- 见 round-14 第 4 部分
- BKT+FSRS 的所有输入数据（历史答题 / 错误语义 / 批注内容）依赖此同步管道
- **当前管道为空**，需 6-8 天工程修复后才能作为本架构的数据基础

### 1.5 7 个可借鉴的开源仓库

| 仓库                                                                                                | 用途                                     |
| ------------------------------------------------------------------------------------------------- | -------------------------------------- |
| [open-spaced-repetition/fsrs4anki](https://github.com/open-spaced-repetition/fsrs4anki)           | FSRS 调度全量参考（Python+JS）                 |
| [open-spaced-repetition/py-fsrs](https://github.com/open-spaced-repetition/py-fsrs)（PyPI: `fsrs`） | Python 后端直接 import                     |
| [CAHLR/pyBKT](https://github.com/CAHLR/pyBKT)                                                     | BKT 4 参数拟合 + 预测 mastery（30,000x 性能于原始） |
| [HKUDS/DeepTutor](https://github.com/HKUDS/DeepTutor)                                             | CLI-native 个人化学习 agent，KG+LLM 架构参考     |
| [umass-ml4ed/dialogue-kt](https://github.com/umass-ml4ed/dialogue-kt)                             | LLM 在对话中自动标注 KC 正确性 → 可改造为 BKT 数据源     |
| [getzep/graphiti](https://github.com/getzep/graphiti)                                             | 本项目已用，可存 mastery + error episode       |
| [CAHLR/OATutor-LLM-Learner](https://github.com/CAHLR/OATutor-LLM-Learner)                         | BKT + Firebase + LLM hint 完整参考架构       |


**User：我们要不要直接 先在这个 https://github.com/HKUDS/DeepTutor 来改造，我觉得额外我需要的能力是：1，我学习是会以一个 vault  文件夹作为核心，那么我需要 ai 在给我解释讲解题目的时候，能精确返回我储存在笔记库里的笔记片段；2，就是我对于知识点的掌握度分析，我在学习知识的时候是以题目以及笔记片段为核心来分析，在分析的过程中我是会不停的打批注，那么我在打批注然后双向链接来表示各个片段关系时，我是希望 agent 能充分理解我的拆解链条的，所以才可以更加合理出闪卡和题目来考察我（这里我就不太清楚 deepTutor 他是怎么进行记忆管理的，它的 RAG 是否靠谱）；3，最好还是用 FSRS 的配合，这样我就知道最佳复习时机，所以原白板是拆解学习知识点过程；检验白板则是测试考察我的这个复习的过程，FSRS 则是梳理清楚我什么时候使用检验白板**

---

## 第二部分：Obsidian wikilink ↔ KG 同步成熟方案（Agent 2）

### 2.1 一句话结论

**端到端方案目前仍属碎片化组合**——没有一个插件同时覆盖**双向、无损、生产可靠**的全链路。MegaMem (Graphiti) 最接近本项目需求，但反向回写仍弱，性能受 LLM 抽取速率制约。

### 2.2 5 个直接可参考的方案

#### 方案 1：MegaMem (C-Bjorn/MegaMem) — 最接近本项目

- **GitHub**: https://github.com/C-Bjorn/MegaMem
- **数据流**：Obsidian 笔记 → 扫描 frontmatter 推断 Pydantic entity schema → LLM 抽取实体/关系 → `add_episode` 写入 Graphiti → MCP 暴露给 Claude
- **同步触发**：3 档（单笔记工具栏图标 / 命令面板批量 / 可配置间隔定时）
- **性能优化**：SQLite (`sync.db`) 跟踪每文件 content hash → 未变更零成本跳过
- **实体失效**：旧 fact 标记 invalid（不删除），天然支持增量
- **反向回写**：MCP 暴露 11 个 Obsidian 文件工具（create/search/update），但**是"AI 主动触发"路径，不是 KG 自动推送**
- **缺口**：无 KG 推断关系 → 自动追加 wikilink；无循环检测

#### 方案 2：obsidian-neo4j-stream (HEmile)

- **GitHub**: https://github.com/HEmile/obsidian-neo4j-stream
- **解析层最完整**：tags → Neo4j 标签；YAML frontmatter → 节点属性；`[[wikilink]]` → `:inline` 关系；`- linkType [[note]]` 语法 → 自定义命名关系类型；正文 → node.content
- ⚠️ **作者明确警告**："自动反映变更仍非常 buggy"
- ⚠️ 已被 `Juggl` 替代（移除了 Neo4j 依赖）
- **适合**：作为 Cypher schema 参考，**不建议生产直用**

#### 方案 3：basic-memory (basicmachines-co/basic-memory) — Markdown-native KG

- **GitHub**: https://github.com/basicmachines-co/basic-memory
- **核心创新**：用本地 Markdown 文件**本身**作为知识图存储
  - frontmatter 中 `type`/`permalink` 定义实体
  - 正文列表项 `[category] content #tag` 标注观察
  - `relation_type [[WikiLink]]` 语法明确关系类型
- **同步**：`basic-memory sync`（一次性）/ `--watch`（实时文件监听 v0.12.0+ 默认启用）
- **MCP 写入**：`write_note()` / `edit_note()` 直接修改本地 md，**人和 LLM 共享同一文件系统**
- **关键价值**：证明"Markdown-native KG"路径可消灭双向同步死锁——KG 真相就是文件本身
- **缺口**：不写 Neo4j，无法 Cypher 图查询

#### 方案 4：obsidian-wikilink-types (penfieldlabs)

- **GitHub**: https://github.com/penfieldlabs/obsidian-wikilink-types
- **解决**：在 wikilink alias 中写 `@supersedes` → 自动同步为 frontmatter YAML `supersedes: [[Analysis]]`
- **触发**：文件保存时自动运行
- **设计**：YAML 为程序权威源，`@type` 语法为用户操作界面
- **本项目最容易低成本集成的前端链接层**

#### 方案 5：engraph (devwhodevs/engraph) — 最扎实增量同步

- **GitHub**: https://github.com/devwhodevs/engraph
- **存储栈**：SQLite + FTS5（全文）+ 向量（llama.cpp/GGUF 本地模型）+ wikilink edges
- **同步**：fs 监听 + 2s debounce + 启动时 reconciliation
- **写入**：section-level 精准编辑（replace/prepend/append by heading），保护 frontmatter
- **性能**：88 文件索引 70 秒（带 LLM embedding）
- **可借鉴**：debounce + hash-skip 增量同步模式

### 2.3 5 维成熟度对比表

| 维度 | basic-memory | neo4j-stream (HEmile) | MegaMem | wikilink-types | engraph |
|---|---|---|---|---|---|
| **同步触发器** | `--watch` 文件监听，成熟 | vault.on('modify')，已知 buggy | 手动/间隔，无事件推送 | 文件保存钩子，成熟 | fs 监听 + 2s debounce，成熟 |
| **frontmatter 解析** | title/type/permalink，结构约定强 | YAML → 节点属性，完整 | 自动 schema 推断（LLM 辅助）| 写入 YAML（仅关系字段）| 读取保护，不强解析 |
| **wikilink 解析** | `relation_type [[X]]` 约定，手动 | `[[X]]`→`:inline`，`- type [[X]]`→命名关系，完整 | LLM 从正文抽关系，**不按 wikilink** | `@type [[X]]`→YAML，完整 | wikilink edges 存 SQLite |
| **写入 KG 协议** | 写本地 md（KG=文件），无冲突 | Python stream → Neo4j Cypher（buggy）| Graphiti `add_episode` + fact invalidation | 无后端 | SQLite，无 Neo4j |
| **反向回写** | 双向：人和 LLM 共写文件 | 无 | MCP 工具主动写（非自动）| 无 | section-level 精准写 |
| **性能（大 vault）** | `--watch` 实时，增量 | 未知，Python 进程常驻 | hash skip，LLM 抽取慢（主要瓶颈）| 仅前端，微秒级 | 88 文件/70s（含 embedding）|
| **循环防护** | 无需（文件=KG）| 无文档 | 无文档 | N/A | 无文档 |

### 2.4 本项目可借鉴的 3 步升级路径

本项目已有 3 个良好基础：
- `backend/app/services/wikilink_graph_service.py` — obsidiantools 构建 NetworkX 图，BFS 邻居查询，asyncio.Lock 热更新（**仅内存图，不写 Neo4j**）
- `backend/app/services/sync_service.py` — Outbox 模式 + Segment Commit（Board→Node→Edge 依赖序）+ MERGE 幂等写入 Neo4j
- `frontend/obsidian-plugin/src/main.ts:93-98` — `metadataCache.on('changed')` 钩子已注册（**只清 masteryCache，未触发 KG 同步**）

#### 第一步：前端钩子 → Outbox 扩展（1-2 天）

在现有 `metadataCache.on('changed')` 钩子（main.ts:93）中：
```typescript
this.app.metadataCache.on('changed', async (file) => {
  // 已有：清 masteryCache
  this.masteryCache.delete(file.path);

  // 新增：debounced sync
  this.outboxQueue.enqueue({
    op: 'note_upsert',
    path: file.path,
    payload: {
      frontmatter: this.app.metadataCache.getFileCache(file)?.frontmatter,
      links: this.app.metadataCache.getFileCache(file)?.links,
    },
    timestamp: Date.now(),
  });
});
// + 2 秒 debounce 防止每次击键触发
// + vault.on('delete') 处理删除
```

#### 第二步：后端新增 WikilinkSyncService（2-3 天）

参照 `sync_service.py` 的 MERGE 模式：

```cypher
// note 节点
MERGE (n:VaultNote {path: $path})
SET n.title = $title,
    n.frontmatter = $frontmatter_json,
    n.updatedAt = $timestamp
ON CREATE SET n.createdAt = $timestamp;

// wikilink 关系（先 MERGE 两端节点允许 ghost）
MERGE (a:VaultNote {title: $source})
MERGE (b:VaultNote {title: $target})
MERGE (a)-[r:WIKILINK {type: $link_type}]->(b)
SET r.updatedAt = $timestamp;
```

**stale 关系处理**：每次 note upsert 前先删除该节点所有出边再重建（neo4j-stream 方案核心做法）。

#### 第三步：wikilink_graph_service 与 Neo4j 对齐（2 天）

`wikilink_graph_service.py` 当前 `refresh()` 是全量 rebuild。升级为增量：
- 接收 `changed_files` 列表
- 仅对这些文件调用 `vault.get_front_matter()` + `vault.get_wikilinks()`
- 增量 patch NetworkX 图
- 调用 WikilinkSyncService 写 Neo4j
- → NetworkX（内存快速查询）和 Neo4j（持久图存储）保持一致

#### 反向回写（可选，低优先）

借鉴 Graphiti/MegaMem 方案：AI 推断关系 → 写入**专用 frontmatter 字段**（如 `kg_suggested_links:`），**不覆盖**用户定义的 wikilink，留给用户确认后手动提升为正式链接。

### 2.5 4 大风险

| 风险 | 等级 | 缓解 |
|---|---|---|
| 双向同步死锁 | 🔴 最高 | 后端写 Obsidian 前设 `isSyncing=true` 标志；回调中跳过 isSyncing=true 操作 |
| 用户工作流冲突 | 🟠 中 | 命名空间区分字段：`user_links:` vs `ai_inferred_links:`，后者只读 |
| 首次全量同步性能 | 🟠 中 | 启动仅 build 索引；改懒加载 + 后台队列逐文件 MERGE，优先最近修改 |
| frontmatter 数组对象序列化 | 🟡 低 | `relations: [{type, target}]` 序列化为 JSON 字符串或拆解为独立关系节点 |

---

## 第三部分：Tauri PRD/EPIC 历史设计调研（Agent 3）

### 3.1 一句话结论

**Tauri v0 PRD 对用户愿景覆盖度 7/10** — 核心机制（原白板→检验白板 / BKT/FSRS / 错误记录 / 批注出题）均有完整设计；但**"多段推理各节点关系"在 Tauri 时期只是检索的隐含假设，未作为独立设计显式定义**。

### 3.2 5 大机制对照表

| 机制 | Tauri v0 PRD 设计 | Obsidian Hybrid 当前实施 | Gap |
|---|---|---|---|
| **原白板 → 检验白板** | ✅ 完整：用户在 Dashboard 选原白板 → 点"生成检验白板" → 空白 exam board + 三重信息隔离（type 标记 + AI 上下文重置 + Skill prompt 约束）→ 防嵌套；触发为手动或 FSRS due 提醒后手动；**FR-EXAM-01/10/21/22** (`prd-tauri-original-2ae5897.md:773-790`) | 保留三重隔离（FR-EXAM-01/10/22 in `epics.md:611-623`）；触发 Cmd+Option+E → `/start_exam_board` Skill；防嵌套已实施；`exam_boards/*.md` 作为检验白板文件 | 触发逻辑守恒（手动），但 Obsidian 无 Dashboard 卡片"一键考察"按钮（Epic 8 Story 8.4 待 Phase 2）；FSRS-based 自动提醒目前只在 Dashboard Dataview 表格显示，非主动推送 |
| **BKT mastery** | ✅ Khan Academy 默认参数：p_init=0.30 先验；BKT 贝叶斯公式更新 p_mastery；新概念默认 BKT=0.30；切换节点时后台自动评分 → BKT 更新 → 写入 frontmatter `bkt_p_mastery`；**FR-MAST-01/02/06** (`prd-tauri-original-2ae5897.md:796-801`) | 保留完整设计：Story 5.1 AC 明确"p_mastery 基于贝叶斯公式更新，新概念默认 BKT=0.30 先验，写入 frontmatter bkt_p_mastery 字段"（`epics.md:793-798`）；frontmatter 是权威源 | BKT 公式参数（p_learn, p_slip, p_guess 具体数值）两版 PRD **均未显式列出** — 仅说 Khan 默认先验；当前 Story 5.1 已定义 AC 但实施状态待验证 |
| **FSRS 调度** | ✅ FSRS 管复习调度（假设知识项孤立），BKT 管掌握度（利用 KG 关联）；字段：`fsrs_*`（stability, difficulty, next_review_date）；`update_fsrs()` MCP 工具写入 frontmatter；**FSRS-BKT 设计折衷** (`prd-tauri-original-2ae5897.md:326`)；FR-MAST-01/02 | 保留（Story 5.2：更新 frontmatter `fsrs_*` 字段；复习间隔随掌握度自适应）；后端 `update_fsrs()` 是权威源，前端只读展示（`prd-obsidian-feedback-6146489.md:142`）；Dashboard `NextReview` Dataview 查询 | **BKT mastery 如何影响 FSRS retrievability 的公式两版 PRD 均未显式定义**（仅说"信号融合"）；5 信号融合公式 = 抽象描述，无数学表达式 |
| **错误回顾** | ✅ 完整：4 主类（破题错误/推理谬误/知识点缺失/似懂非懂）+ 2 子类；双写到 frontmatter `errors[]` + Graphiti；检验白板出题时注入历史错误（**ACP 第 3 层：FR-CONV-06 / FR-EXAM-03**）；旅程 3 明确：一周后辨析题直接针对历史误解 (`prd-tauri-original-2ae5897.md:338-342, 403`)；用户批注确认了推理谬误出题策略 (`prd-annotations-2ae5897.md:169-170`) | 保留：错误双写（FR-MEM-01 / Story 5.5）；复习时注入历史误解（FR-SPACE-02）；辨析题生成（Story 7.4）；4 类分类 AR3（`epics.md:153`）；旅程 3 完整流程在 Phase 2 实施（Epic 7）| Day 3 + Day 7 提醒机制（Story 7.2）目前是 Dashboard 被动展示，非主动推送；Graphiti 错误检索注入到出题 prompt 的具体实施在 Story 4.3，状态待实施 |
| **多段推理生成考题** | ⚠️ 部分：出题 Prompt **5 层结构**第 3 层（**ACP 学生数据包**）注入 Tips/错误记录/Edge 理由/精通度/对话历史；KG 三角协作选题（FSRS+BKT+KG 选择薄弱节点）；Graphiti 三层分级搜索；**FR-EXAM-03"融合三路数据生成个人化题目"** (`prd-tauri-original-2ae5897.md:329-334, 202-203`)。**但**没有明确定义"多段推理"或"multi-hop reasoning over KG" — 只用 Hybrid Search + Adaptive Router 检索 top-K | Story 4.3：三路融合出题（Graphiti 个人记忆 + Graphify 知识图谱 + frontmatter 掌握度）；71x token 压缩检索（FR-KG-07）；但目前 Story 2.1 邻居注入只是按 hop_distance 排序，**不是真正的关系语义推理**（仅 BFS 图遍历，chat_context_assembler.py 不做关系理解）；Story 4.3 出题 prompt 待实施 | 🔴 用户当前愿景"精确多段推理各节点之间的关系"**超出 Tauri PRD 原设计**：Tauri 只做 simple retrieval（ACP top-K 注入），未设计 chain-of-thought over KG。**这是最大 Gap** |

### 3.3 关键 PRD 段落（必读引用）

#### 引用 1：原白板→检验白板触发机制（工作流 2）

`_bmad-output/planning-artifacts/recovered/prd-tauri-original-2ae5897.md:200-212`

> 用户在 Dashboard 选择原白板 → 选择考察模式（点对点/综合题/混合）→ 系统基于 FSRS+BKT+KG 三角协作选择薄弱节点 → AI 基于 ACP 考察数据包 + 4 维 Rubric 出题考察

#### 引用 2：ACP 出题 Prompt 5 层结构（BKT+错误+批注融合的核心）⭐

`_bmad-output/planning-artifacts/recovered/prd-tauri-original-2ae5897.md:329-334`

> 第 3 层（动态）：ACP 学生数据包注入——Tips/错误记录/Edge 理由/精通度/对话历史

#### 引用 3：错误类型→出题策略映射（推理谬误"诱导再犯"设计）⭐

`_bmad-output/planning-artifacts/recovered/prd-tauri-original-2ae5897.md:336-342`

> 推理谬误 → 出与原题结构相似的新题，设置能诱导学生重蹈同一推理错误的陷阱，验证学生是否已真正克服该推理谬误

#### 引用 4：用户批注确认推理谬误理解（原始用户意图）

`_bmad-output/planning-artifacts/recovered/prd-annotations-2ae5897.md:168-170`

> 这里推理谬误，指的是我一开始在原白板解这道题目的时候，犯了推理上的错误，那么在这次检验白板中，那么你再次尝试使用题目来考察我，**诱导我陷入同样的错误**

#### 引用 5：用户批注提出"三角协作 + Graphiti 检索精度 + 提示词设计"⭐⭐⭐

**注意**：这是用户在 Tauri 时期的原始问题，**与 round-14 line 207-208 新批注完全一脉相承**！

`_bmad-output/planning-artifacts/recovered/prd-annotations-2ae5897.md:97-100`

> 你这里打算怎么设计 3 角协作，请你使用 /gemini-deep-research 来 code 分析，而且我的 tips edge，以及我在和 ai 对话所犯下的错误以及混淆点，是记录到 Graphiti 的，**首先你在你记录到 Graphiti 后，上面就是我的学习个人历史，那么你是要怎么记录我的历史和检索我的历史，才能精确在检验白板中精准命中我的问题**

#### 引用 6：FSRS-BKT 角色分工

`_bmad-output/planning-artifacts/recovered/prd-tauri-original-2ae5897.md:326`

> FSRS 管复习调度（假设知识项孤立），BKT 管掌握度追踪（利用 KG 关联），两者角色边界明确

#### 引用 7：5 信号融合定义

`_bmad-output/planning-artifacts/recovered/prd-obsidian-feedback-6146489.md:432-435`

> FR-MAST-03: BKT + FSRS + 错误历史 + 校准偏差 + 自评置信度 5 个信号；信号互补性 r < 0.7，融合后 Spearman rho > 0.6

#### 引用 8：三路融合出题（Obsidian Hybrid 当前定义）

`_bmad-output/planning-artifacts/epics.md:648-651`

> 融合个人记忆（Graphiti）+ 知识图谱关系（Graphify）+ 掌握度数据（frontmatter）

### 3.4 降级时丢失的 7 项设计

Tauri v0 有但 Obsidian Hybrid 暂未实施（或推至 Phase 2+）：

1. **可视化节点精通度色条 + 进度条** — Tauri 节点颜色直接在 ReactFlow 白板实时反映 BKT 更新；Obsidian 版只能通过 frontmatter 字段和 Dashboard Dataview 查询显示，**无原白板内联视觉反馈**
2. **检验白板中实时"拉出新节点"的可视化操作** — Tauri 拖拽文字到 ReactFlow 白板生成节点；Obsidian 版降级为书签式 `[!discussion_later]+` callout（`epics.md:578-583` Story 3.4）
3. **检验白板 → 递归考察** — Tauri FR-EXAM-06：确认的新节点可被点击继续深入剖析和考察；Obsidian 版 Story 4.8 只做了书签提取
4. **考后审查面板（Post-exam Review Panel）** — 已在 Tauri v0 PRD 附录标注废弃（`prd-tauri-original-2ae5897.md:970`）
5. **答前自评按钮** — 用户答题前 AI 问"你觉得自己会吗？"收集显式置信度；Obsidian 版废弃（`prd-tauri-original-2ae5897.md:971`：对话式考察会打断对话流）
6. **节点级学习档案详情面板（OLM 三层面板）** — 推至 Obsidian Phase 2（掌握度百分比+题目标签薄弱方向+趋势曲线+处方性建议+证据追溯）
7. **Adaptive Router 四路搜索完整 CRAG 闭环** — LanceDB Dense + Sparse + Graphiti 时序 + Vault 笔记四路并行 + Reranker 精排；Obsidian Hybrid Story 2.1 只实现了 BFS wikilink 遍历 + 上下文组装

### 3.5 5 个可重新激活的 Tauri PRD 设计（直接拿来用）

#### 重新激活 1：ACP 出题 Prompt 5 层结构（最直接可用）⭐

源：`prd-tauri-original-2ae5897.md:329-334`

第 3 层"ACP 学生数据包"内容定义（**Tips + 错误记录 + Edge 理由 + 精通度 + 对话历史**）已经是用户愿景"多段推理 + 节点批注 + 错误"的最接近表达。Obsidian Hybrid Story 4.3 的 AC 已引用此设计，但 prompt 具体内容未实施。**可立即转化为 Story 4.3 的出题 prompt 模板**。

#### 重新激活 2：错误类型 → 出题策略映射（4 类）

源：`prd-tauri-original-2ae5897.md:336-342`

4 主类映射完全可重用：
- 推理谬误 → 设置诱导陷阱验证是否已克服
- 知识点缺失 → 先出 Bloom Remember 定义题
- 似懂非懂 → 辨析/反例/迁移题
- 破题错误 → 类似结构题+不同表层

→ Story 4.3（出题策略）和 Epic 7（错误修正）的直接输入

#### 重新激活 3：旅程 3 错误修正记忆闭环时序（Day 0/3/7）

源：`prd-tauri-original-2ae5897.md:396-405`

- Day 0 标记错误
- Day 3 复习提醒 + 历史误解注入
- Day 7 辨析题验证

→ 对应 Epic 7（Story 7.2/7.3/7.4），可直接作为 Story 7.x 的行为叙述来源

#### 重新激活 4：IRT 难度连续参数设计（非离散分级）

源：`prd-tauri-original-2ae5897.md:790`（Tauri FR-EXAM-22）

> 难度采用连续 IRT difficulty 参数（非 Easy/Medium/Hard 离散分级），校准依据 BKT 掌握概率和同类主题历史表现，难度匹配率 >= 70%

→ Obsidian Hybrid FR-EXAM-19/Story 4.11 已保留，但实施中需要从 frontmatter 读取 BKT 值动态调节 IRT 参数的逻辑未明确写出。可从此段直接提炼 AC

#### 重新激活 5：FSRS-BKT 角色分工原则 ⭐ 直接回答压力点 1

源：`prd-tauri-original-2ae5897.md:326`

> FSRS 管复习调度（假设知识项孤立），BKT 管掌握度追踪（利用 KG 关联）

→ **这是回答用户压力点 1（"能否推算各原白板精确复习时间"）的直接设计原则**：FSRS `next_review_date` 字段就是复习时间，BKT `p_mastery` 影响 FSRS stability 参数计算。可以以此为基础直接起草 **Story 2.5.Z（"FSRS 驱动的原白板复习精确调度"）**

### 3.6 直接回答用户两大压力点

#### 压力点 1：能否推算各原白板精确复习时间？

**Tauri PRD 已设计** ✅

- FSRS `next_review_date` 由 `update_fsrs()` MCP 计算并写入每个节点 frontmatter
- Dashboard `NextReview` 查询聚合所有节点的 due 时间
- Obsidian Hybrid Story 5.2 已保留此设计

**当前实施状态**：需要确认 `update_fsrs()` 是否已被激活并写入 frontmatter（通过 sprint-status 或代码 grep 确认）

#### 压力点 2：多段推理 + 节点理解程度 + 错误 + 批注综合出题

**Tauri PRD 部分设计** ⚠️

- ACP 5 层 prompt 结构（`prd-tauri-original-2ae5897.md:329-334`）是最接近的设计
- 但它是**"检索注入"而非"推理"** — 系统拿 top-K 相关记忆直接注入 prompt，让 LLM 本身做推理，而非系统预先做 multi-hop graph reasoning
- 用户当前愿景"精确多段推理各节点之间的关系"实际上需要在 Story 4.3 的出题 prompt 中**显式设计 chain-of-thought 推理步骤**
- **这超出了 Tauri PRD 原有设计，是需要新增的内容**

→ 见第四部分 Agent 4 的工程方案

---

## 第四部分：多段推理生成考察题工程方案（Agent 4）

### 4.1 一句话结论

**自己组合（Self-Assembly）** — 核心组件（BKT/FSRS 驱动 + 错误回顾 + prompt 分层）均有学术原型和社区案例，但"wikilink 多跳子图 → 融合错误状态 → 生成多 hop 题目"的完整管道目前**无成熟生产实现**，需在现有 `question_generator.py` 5 层 prompt 框架上**补充 2 个关键模块**。

### 4.2 多段推理 + 学习状态融合的成熟模式

#### 模式 1：Generation-with-Scratchpad（CoT 在生成阶段的变体）

CoT 常用于答题评分端，但在生成端有有效变体：先让 LLM 输出一段内部推理链（"学生在节点 A 的错误是 X，节点 B 与 A 通过 [[推理规则]] 相连，因此跨节点弱点是 Y……"），再从该链生成最终题目。

**arXiv:2408.04394（PS4 策略，本项目已引用的 5 层 prompt 论文）**：在 system prompt 中内嵌 Chain-of-Thought 结构可提升题目针对性约 18%。

**本项目可行改进**：在 user_message 中加 `"请先用 2 句话分析学生的跨节点弱点，再出题"`

#### 模式 2：Graph-of-Thought (GoT) — KG 指导生成

GoT (Besta et al., 2023, arXiv:2308.09687) 将推理步骤表示为图操作。

**GraphRAG 子图注入（更实用工程替代）**：
1. 用 Cypher 提取 2-hop 子图（锚点节点 + 邻居 + 邻居的邻居）
2. 序列化为 `Node A --[关系]-- Node B --[关系]-- Node C` 的线性文本
3. 注入 prompt，要求 LLM 生成"必须同时涉及 A 和 C"的题目

**本项目现状**：`_get_kg_relevance()` 已有 Neo4j 1-hop `CANVAS_EDGE|RELATES_TO` 查询，但 `assemble_acp()` 中 `edge_reasons` 仅提取边的**理由文本**（5 条），并未提取完整子图路径结构。**多跳题目生成的关键缺口正在这里**。

#### 模式 3：反向 MultiHop QA (HotpotQA 风格)

```
输入：[节点A内容, 节点B内容, A→B的wikilink关系标签]
→ 生成：需同时理解A和B才能回答的桥接题
```

**Prompt 例子**（可直接加入 layer3）：

```markdown
**多跳考察子图**（请出一道必须推理以下路径才能回答的题目）：
- 节点A: "可容许性(Admissibility)" — mastery=0.3 — 历史错误: 混淆定义
- 关系: [[可容许性]] → [[零知识证明]] (用户标注: "前者是后者的安全假设")
- 节点B: "零知识证明" — mastery=0.6

出题要求: 题目必须要求学生先理解「可容许性」再推导「零知识证明」中的某个性质。
```

#### 模式 4：学习状态融合 Prompt 完整模板

```markdown
[Layer 3 扩展版 — 含多跳结构]

**目标节点**: {node_A_content}
**精通度**: p_mastery={0.3}, R={0.85}, level=初学
**历史错误**:
  - [知识点缺失] 混淆了「可容许性」与「安全性」的定义边界

**关联节点（2-hop 子图）**:
  - 1-hop: [[零知识证明]] — mastery=0.6 — 边类型: CANVAS_EDGE(用户画) — 理由: "前者是后者的安全假设"
  - 2-hop: [[交互式证明系统]] — mastery=0.4 — 边类型: RELATES_TO(AI 推断)

**出题策略**:
- mastery < 0.3: 基础定义/识别题
- 关联子图存在: 额外要求题目必须跨越1-2个节点推理
- 错误类型"知识点缺失": 先确认A的定义，再问A→B的推导
```

**难度控制逻辑**（现有 `layer4_rules.md` 已实现 Bloom 分级）：

| mastery | 多 hop | Bloom 层 | 题型 |
|---|---|---|---|
| < 0.3 | 多 hop | Remember | 先问单节点定义 |
| 0.3-0.5 | 多 hop | Understand | 问"为什么 A 是 B 的前提" |
| > 0.5 | 多 hop | Analyze | 问"如果 A 不成立，B 会怎样变化" |

### 4.3 5 个社区案例 Prompt 设计

| 案例 | Prompt 设计 |
|---|---|
| **Khan Academy Khanmigo**（公开博客 2023）| **Socratic Error Re-Activation**：不直接告知错误，再次遇到相同结构题时先问"你上次解这类题时哪里卡住了？"，再问本题 |
| **Anki AI Plugins**（Reddit r/Anki 2024）| Cloze deletion 自动化：md 段落 → LLM 生成 `{{c1::}}` 填空。**FSRS retrievability < 阈值** 作触发条件。本项目 `select_target_node()` 中 `W_RETRIEVABILITY=0.3` 已实现 |
| **Synthesis Tutor**（Sal Khan 系，2024）| **Dependency graph traversal**：从 mastery 最低的叶节点反向追溯到根，生成链式问答（每题答案是下一题输入）。本项目 wikilink 图 `get_neighbors(hop=2)` BFS 遍历可直接支持 |
| **EduChat / GPT-4 教育数据集**（arXiv:2308.02773）| 三类 prompt persona：导师模式（引导）/ 考察模式（严格）/ 同伴模式（讨论）。本项目 `ExamMode` 枚举已对应，layer2_mode.md 的 `{{exam_mode}}` 注入已实现 |
| **GraphRAG + 题目生成**（Microsoft, arXiv:2404.16130）| 社区摘要（community report）包含多实体关系综合描述，可作为多跳题目生成上下文。**本项目 Graphiti 的 `search_communities()` 接口未被 `assemble_acp()` 调用，是可快速补充的集成点** |

### 4.4 4 阶段工程方案（约 3.5 天）

#### Phase 1：节点子图提取 — Cypher 多跳 + frontmatter 聚合（0.5 天）

**目标**：扩展 `_get_kg_relevance()` 为 `_get_subgraph_context()`，返回 2-hop 子图结构化 JSON。

**关键 Cypher**：
```cypher
MATCH path = (n:CanvasNode {id: $node_id, canvasId: $canvas_id})-[r1:CANVAS_EDGE|RELATES_TO]-
             (m:CanvasNode)-[r2:CANVAS_EDGE|RELATES_TO]->(k:CanvasNode)
WHERE m.canvasId = $canvas_id AND k.canvasId = $canvas_id
RETURN n.id, n.text, type(r1), m.id, m.text, type(r2), k.id, k.text
LIMIT 20
```

**输出格式**：
```json
{"hops": [
  {"from": "可容许性", "relation": "CANVAS_EDGE", "to": "零知识证明", "reason": "安全假设"},
  {"from": "零知识证明", "relation": "RELATES_TO", "to": "交互式证明系统"}
]}
```

**修改文件**：`question_generator.py` — 新增 `_get_subgraph_context()` 方法，在 `assemble_acp()` 中调用并写入 `acp.subgraph_context`

#### Phase 2：学习状态融合 Prompt 构造（0.5 天）

**目标**：扩展 `_format_acp_layer()` 注入多跳子图 + 错误-节点关联

```python
if acp.subgraph_context and acp.subgraph_context.get("hops"):
    hops = acp.subgraph_context["hops"][:3]
    hop_str = " → ".join([
        f"[[{h['from']}]]→[[{h['to']}]]({h.get('reason','')})"
        for h in hops
    ])
    optional_parts.append(f"**关联路径（请出需跨节点推理的题）**: {hop_str}")
```

**难度控制**：在 `build_5_layer_prompt()` 加 multi-hop 触发条件——仅当 `len(hops) >= 1 AND acp.effective_proficiency > 0.3` 时注入子图路径（低 mastery 先考单节点基础）

#### Phase 3：LLM 多 hop 题目生成（1 天）

**目标**：修改 `_call_llm_for_question()` 的 user_message，要求输出带 `bridge_nodes` 字段的 JSON，追加 scratchpad 推理步骤

```python
user_message = (
    f"请先用1句话分析学生在「{acp.node_content[:50]}」及其关联节点的跨节点弱点，"
    f"再出一道考察题。\n\n"
    f"JSON格式: {{'reasoning': '跨节点分析', 'question_text': '...', "
    f"'bridge_nodes': ['节点A', '节点B'], 'question_type': '...', ...}}"
)
```

更新 `QuestionGenerationResult` 模型：增加 `bridge_nodes: List[str]` 和 `reasoning: str` 字段。

**Token 预算**：
- 当前 `ACP_MAX_CHARS = 9000`（约 3K tokens）
- 子图注入约增加 300 tokens（3 hop = ~150 chars），在预算内
- 大型白板（>20 节点）需截断为 `LIMIT 5` hops

#### Phase 4：题目落地为检验白板 md + 反向更新 BKT/FSRS（1.5 天）

**目标**：`review_service.py` 的 `generate_verification_canvas()` 已生成 `{canvas_name}-检验白板-{timestamp}.md`，需追加：

1. 将 `bridge_nodes` 写入题目 frontmatter：`bridge_nodes: [节点A, 节点B]`
2. 用户答题后 `process_answer()` 调用 `mastery_engine.update()` 时，对所有 `bridge_nodes` 中的节点也执行 partial BKT 更新（答对 → 相关节点 mastery +0.05）
3. FSRS：对 `bridge_nodes` 中 `retrievability < 0.5` 的节点触发间隔缩短

**总工作量**：约 **3.5 天**（Phase 1-4 顺序实施，假设 Neo4j + Graphiti 服务正常）

### 4.5 5 大风险

| # | 风险 | 缓解 |
|---|---|---|
| 1 | **题目质量低**（多 hop 题变成双节点列举题）| 在 layer4_rules.md 增加禁止语："禁止出'A 和 B 有什么关系？'式描述题；要求题目只给出 A 的条件，让学生推导 B 的某个性质"。用 LLM-as-judge 做自动质量检查（temperature=0 再评分）|
| 2 | **多 hop 路径不准**（Graphiti RELATES_TO 质量）| 优先使用用户画的 `CANVAS_EDGE`（权重 1.0）；仅当 CANVAS_EDGE 不足 2 条时才引入 RELATES_TO；在 `_get_subgraph_context()` 中加 `edge_type_filter` 参数 |
| 3 | **Token 爆炸** | 现有 `_enforce_token_budget()` 已做截断；子图路径额外增加 `hops_budget = min(3, (ACP_MAX_CHARS - current_len) // 100)` 动态限制。最坏退化到单节点考察 |
| 4 | **重复生成相同题目** | `QuestionGenerationResult` 增加 `question_hash = hash(question_text[:50])`，存入 session；下次生成前加 `"请勿重复以下题目模式: {past_question_hashes}"` 到 user_message。可引入 temperature 递增（第 N 次同节点 → temperature += 0.1，上限 0.9）|
| 5 | **BKT 多节点反向更新信号污染** | partial update 系数 0.5（`bridge_node_update_weight = 0.5`）；仅主节点做完整 BKT slip/transit 更新；bridge 节点仅做轻量 retrievability 刷新，不改变 p_mastery |

---

## 第五部分：综合推荐 — 基于 Tauri PRD 重新激活的实施方案

### 5.1 用户愿景 ↔ 4 Agent 调研发现 ↔ Tauri PRD 对照

| 用户愿景元素 | Agent 1 业界 | Agent 2 同步 | Agent 3 Tauri PRD | Agent 4 多跳工程 |
|---|---|---|---|---|
| **Obsidian 双链规划关系** | — | MegaMem / wikilink-types 借鉴 | ✅ Tauri 已设计 vault frontmatter | — |
| **BKT mastery** | 学术原型多，pyBKT 可用 | — | ✅ Tauri FR-MAST-01 完整 | — |
| **FSRS 复习时间** | py-fsrs / fsrs4anki 成熟 | — | ✅ Tauri FR-MAST-02 完整 | — |
| **错误记录** | Anki leech 粗 / 学术原型精 | — | ✅ Tauri 4 主类映射完整 | Phase 4 反向更新 |
| **用户批注 → 出题** | 组件存在，无完整管道 | — | ✅ Tauri ACP 第 3 层 | Phase 2 prompt 注入 |
| **多段推理** | 教育生产 near-zero | — | ⚠️ Tauri 仅 simple retrieval | ✅ Phase 1+3 完整方案 |
| **同步前后端一致** | — | 3 步升级路径 | — | — |
| **检验白板生成** | — | — | ✅ Tauri FR-EXAM-01/10/21/22 | Phase 4 落地 |

### 5.2 推荐实施路线（4 阶段，10-13 天）

#### Stage A：数据基础修复（来自 round-14，6-7 天）

| # | 改动 | 工作量 |
|---|---|---|
| A1 | 接入 lib/agentic_rag embedding search 到主 RAG pipeline | 2-3 天 |
| A2 | 错误用独立 group_id `vault:<vault>:errors` + TTL 30 天 | 2 天 |
| A3 | D16 group_id 落地 backend：实现 `build_vault_group_id()` + `cypher_helpers.py` | 1 天 |
| A4 | Plugin v1.5 静默 post-turn-extract + Dashboard 角标 | 1 天 |

#### Stage B：前后端同步（来自 Agent 2，4-5 天）

| # | 改动 | 工作量 |
|---|---|---|
| B1 | Plugin metadataCache.on('changed') → Outbox 扩展（含 wikilink + frontmatter）| 1-2 天 |
| B2 | Backend 新增 `WikilinkSyncService`（MERGE Cypher 节点+关系）| 2-3 天 |
| B3 | wikilink_graph_service 与 Neo4j 对齐（增量同步）| 2 天 |

#### Stage C：检验白板多段推理（来自 Agent 4，3.5 天）

| # | 改动 | 工作量 |
|---|---|---|
| C1 | `_get_subgraph_context()` 2-hop Cypher | 0.5 天 |
| C2 | layer3 子图注入 + 难度 mastery 触发 | 0.5 天 |
| C3 | LLM scratchpad + bridge_nodes JSON | 1 天 |
| C4 | 检验白板 frontmatter + BKT/FSRS 反向更新 | 1.5 天 |

#### Stage D：BKT-FSRS 联动定义（来自 Agent 1，2-3 天）

| # | 改动 | 工作量 |
|---|---|---|
| D1 | 定义 BKT mastery → FSRS difficulty/stability 映射函数（参考 Tauri prd:326）| 0.5 天 |
| D2 | 实施 5 信号融合公式（BKT+FSRS+错误+校准+自评，Spearman rho > 0.6）| 1.5 天 |
| D3 | unit test：冷启动 prior + ASSISTments 群体参数 fallback | 1 天 |

### 5.3 总工作量估算

- Stage A：6-7 天（Graphiti 数据基础）
- Stage B：4-5 天（前后端同步）
- Stage C：3.5 天（多段推理）
- Stage D：2-3 天（BKT-FSRS 联动）
- **合计**：**16-18.5 天**（约 3-4 周连续工作）

可分 4 个 Story 实施：
- **Story 2.5.Z**：Graphiti 数据基础修复（Stage A）
- **Story 2.5.AA**：Obsidian↔Graphiti 双向同步（Stage B）
- **Story 4.3 升级**：检验白板多段推理（Stage C）
- **Story 5.3**：BKT-FSRS 联动 + 5 信号融合（Stage D）

### 5.4 直接回答用户两大压力点

#### 压力点 1：能否推算各原白板精确复习时间？

**✅ 可以，但当前实施不完整**：
- Tauri PRD 已设计完整（FSRS `next_review_date` + `update_fsrs()` MCP）
- Obsidian Hybrid Story 5.2 保留设计
- 当前 Gap：BKT mastery 如何影响 FSRS retrievability 公式**两版 PRD 均未显式定义**
- → 需 Stage D 实施 5 信号融合（约 2-3 天）

#### 压力点 2：精确多段推理 + 节点理解程度 + 错误 + 批注综合出题？

**⚠️ 部分超出 Tauri 原设计，但完全可工程实现**：
- Tauri PRD ACP 5 层 prompt 是最接近的设计（**检索注入**）
- 用户当前愿景需要**显式 chain-of-thought over KG**（**真正多段推理**）
- → 需 Stage C 实施（约 3.5 天）+ Tauri 重新激活 ACP 5 层 prompt

---

## 第六部分：4 个决策点（请用户判断）

### Decision 1：是否按 Stage A→B→C→D 顺序实施？

**背景**：4 Stage 有依赖关系（B 依赖 A 的 group_id；C 依赖 B 的 wikilink 同步；D 依赖 A 的 Graphiti 错误读取）

**选项**：
- A. 严格 A→B→C→D 顺序（16-18.5 天，安全）
- B. A、B 并行（A 修后端，B 改前端）→ 节省 2-3 天
- C. 先做 C（检验白板核心 ROI）→ 用户最快看到效果，但数据基础有 G-FAKE 风险
- D. 跳过 D（5 信号融合）→ 用 mastery 直接决定 next_review，简单但精度低

**Claude 推荐**：B（A、B 并行 12-14 天）

### Decision 2：多段推理深度怎么定？

**背景**：Cypher `LIMIT 20` 会拿 2-hop 子图，但 token 预算 3K 限制只能注入 3 hops。深度越深质量越差（RELATES_TO 噪声 + LLM 理解难度）。

**选项**：
- A. 严格 1-hop（仅 CANVAS_EDGE 用户画的边）→ 精度高，覆盖窄
- B. 1-hop 优先 + 2-hop 兜底（CANVAS_EDGE 不足时引入 RELATES_TO）→ 推荐
- C. 2-hop 强制（无论边类型）→ 覆盖广，质量风险高

**Claude 推荐**：B

### Decision 3：BKT-FSRS 联动公式选哪个？

**背景**：两版 PRD 均未显式定义。需要选一个起点。

**选项**：
- A. 简单线性：`d = 1 - P(mastery)`，`s = stability_init * (1 + transit_rate)` → 工作量小但精度未知
- B. 参考 LECTOR (arxiv 2508.03275) 的扩展遗忘曲线公式 + ASSISTments BKT 默认参数 → 学术依据更强
- C. 自己拟合：先用简单公式上线，3 个月后用 user data 拟合个性化参数 → 长期最优

**Claude 推荐**：A 起步 + C 长期（先简单后优化）

### Decision 4：批注 callout 是否作为出题 seed？

**背景**：用户用 `[!error]+ [!question]+ [!tip]+` 等 callout 在原白板批注。Agent 1 发现"完整管道无生产先例"。

**选项**：
- A. 立即把 callout 内容注入 layer3 ACP（用户愿景核心，1 天工作）
- B. 仅注入 `[!error]+` callout（最高信号，避免噪声）
- C. 先观察 Stage C 效果再决定（保守）

**Claude 推荐**：B（高信号优先，避免噪声）

---

## 附录 A — 4 Agent 引用文件清单

### Agent 1（业界 BKT+FSRS+KG+LLM 综合系统）
- 见 §1.5 7 个开源仓库（含 GitHub 链接）
- 学术论文：arxiv 2508.03275 (LECTOR) / arxiv 2504.19413 (Mem0) / arxiv 2308.09687 (GoT) / arxiv 2308.02773 (EduChat) / arxiv 2404.16130 (GraphRAG) / arxiv 2408.04394 (PS4)

### Agent 2（Obsidian↔KG 同步方案）
- `backend/app/services/wikilink_graph_service.py`（已实现，仅前端 BFS）
- `backend/app/services/sync_service.py`（已实现，Outbox + Segment Commit）
- `frontend/obsidian-plugin/src/main.ts:93-98`（钩子已注册）
- 5 个开源仓库：MegaMem / obsidian-neo4j-stream / basic-memory / wikilink-types / engraph

### Agent 3（Tauri PRD 历史设计）
- `_bmad-output/planning-artifacts/recovered/prd-tauri-original-2ae5897.md:200-212, 326, 329-334, 336-342, 396-405, 773-790, 796-801, 970-971`
- `_bmad-output/planning-artifacts/recovered/prd-annotations-2ae5897.md:97-100, 168-170`
- `_bmad-output/planning-artifacts/recovered/prd-obsidian-feedback-6146489.md:142, 432-435`
- `_bmad-output/planning-artifacts/epics.md:153, 578-583, 611-623, 648-651, 793-798`

### Agent 4（多段推理工程方案）
- `backend/app/services/question_generator.py`（待扩展）
- `backend/app/services/review_service.py::generate_verification_canvas()`（待扩展）
- `backend/app/services/chat_context_assembler.py`（当前仅 BFS，无关系语义推理）
- `backend/app/services/verification_service.py`（已有验证服务）

---

## 附录 B — 用户压力点 ↔ 调研发现 ↔ Tauri PRD 完整对照

| 压力点 | 业界成熟度 | Tauri PRD 设计 | 当前 Obsidian Hybrid 实施 | 推荐 Stage | 工作量 |
|---|---|---|---|---|---|
| 推算原白板精确复习时间 | ✅ FSRS 成熟（py-fsrs）| ✅ FR-MAST-02 完整 | ⚠️ Story 5.2 保留但 update_fsrs() 待激活 | D（联动公式）| 2-3 天 |
| 多段推理各节点关系 | 🔴 教育生产 near-zero | ⚠️ ACP 检索注入（非真推理）| ❌ Story 2.1 仅 BFS | C（多 hop）| 3.5 天 |
| 节点理解程度（BKT）| 🟠 学术多生产少 | ✅ FR-MAST-01 完整 | ⚠️ Story 5.1 AC 定义但实施待验证 | D | 1 天 |
| 节点错误记录 | 🟠 粗粒度 Anki 生产 | ✅ 4 主类 + 双写 | ⚠️ 写入 Graphiti 但只写不读（round-14）| A2 | 2 天 |
| 节点用户批注 | 🟠 组件存在无管道 | ✅ ACP 第 3 层 | ❌ Story 4.3 待实施 | C2（layer3）| 0.5 天 |
| 综合考察让用户想起原白板 | 🔴 业界无先例 | ✅ ACP 5 层 prompt | ❌ Story 4.3 待实施 | C3（scratchpad）| 1 天 |
| 考察是否再犯相似错误 | 🟠 学术原型 | ✅ 推理谬误"诱导再犯"FR-EXAM-03 | ❌ Story 4.3+7.4 待实施 | C+Epic 7 | 含在 C |
| Graphiti 后端 ↔ 前端高度一致 | ⚠️ 碎片化方案 | — | ❌ 零同步（round-14）| B（同步）| 4-5 天 |
| Graphiti 节点关系 ↔ 用户定义关系一致 | ⚠️ 同上 | — | ❌ wikilink 不写 Neo4j | B2 | 含在 B |

---

## 状态

- **报告生成**：2026-05-05 23:XX
- **下一步**：等用户对 4 个决策点反馈
- **依赖**：round-14 第 7 部分 4 个决策点尚未确认（Stage A 启动前提）
- **建议归档位置**：本文件位于 `_bmad-output/research/`，与 round-12/13/14 同级
- **后续动作**：用户决策后，转 `_bmad-output/_decisions/` 形成 Story 2.5.Z / 2.5.AA / 4.3 升级 / 5.3 的 spec 输入
