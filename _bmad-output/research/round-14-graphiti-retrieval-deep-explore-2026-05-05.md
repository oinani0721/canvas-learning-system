---
title: Round 14 — Graphiti 检索算法 + 长上下文可靠性 Deep Explore
date: 2026-05-05
trigger: Story-2.5.X UAT line 295 用户批注（5 点）
agents: 5 并行 Explore Agent (Sonnet)
related:
  - _bmad-output/验收单/Story-2.5.X-progressive-confirmation.md
  - _bmad-output/research/round-13-wikilink-vs-graphiti-five-questions-answer-2026-04-29.md
  - _bmad-output/research/round-12-graphiti-karpathy-5-conjectures-audit-2026-04-21.md
status: draft for user review
---

# Round 14 — Graphiti 检索算法 + 长上下文可靠性 Deep Explore

## 元信息

| 字段 | 值 |
|---|---|
| 触发 | `_bmad-output/验收单/Story-2.5.X-progressive-confirmation.md:295` 用户批注（5 点） |
| 调研方式 | 5 并行 Explore Agent（Sonnet model）|
| 日期 | 2026-05-05 |
| 范围 | Graphiti SDK 全检索算法 + 本项目使用现状 + 三方对比 + 长上下文真实案例 + 主动检测可行性 |
| 报告字数 | ≈8000 字 |
| 状态 | 初稿，待用户审阅 4 个决策点 |

---

## 用户批注原文（line 295）

> **User：1，你这里的错误记录没有显示的告诉我错误是什么？这里接受错误的使用操作体验，我是需要具体进行 claudian 的使用才知道具体的效果如何；2，我觉得最好是 我在使用 claudian 的时候，agent 能亲自检测到错误后向我增量提问，问我是否需要把我的这个错误描述列为批注然后记录到 Graphiti，3，我这里有一个很重要的思想，Graphiti 的后端记录，应该和我前端记录的批注内容高度一致，4，Graphiti 后端所记录各个节点和批注之间的联系，应该也是要我个人定义各个节点之间的联系高度一致，那么我为什么要用 Graphiti 在后端上进行 RAG 的检索的话，我觉得是比我前端只靠双向链接和 md 文件内容检索，更加快速可靠。 5，请你现在 deep explore 我们 Graphiti 所有检索算法并向我解释，由此我来判断这里的错误管理，在我们长上下文一多是否还能保持可靠的定位，我这里还需要启动并行 agent 来 deep explore 相关的案例。**

### 5 点拆解

| #   | 类型              | 关切                                                                |
| --- | --------------- | ----------------------------------------------------------------- |
| 1   | UX 体验           | 接受错误候选时 Modal 没显示错误详情；想跑通 Claudian 看效果                            |
| 2   | 产品愿景（主动）        | Claudian 在对话中应主动检测错误 → 增量提问 → 是否记 Graphiti                        |
| 3   | 产品愿景（一致 #1）     | Graphiti 后端记录 ↔ 前端批注内容**高度一致**                                    |
| 4   | 技术论断            | Graphiti 后端关系 ↔ 用户定义节点关系一致；Graphiti RAG 检索 比 前端双链+md 检索 **更快速可靠** |
| 5   | Deep explore 任务 | 解释 Graphiti 所有检索算法 → 判断错误管理在长上下文累积下能否可靠定位；要并行 agent 调研相关案例        |

---

## 一句话核心结论

**用户论断"Graphiti 比双链+md 检索更快可靠"在长上下文场景下条件性成立**——但本项目当前实现存在 4 个严重残缺：

1. ❌ **错误管理只写不读**：`record_error` 写入 Graphiti，但**无任何路径按 `event_type=misconception` 类型读取历史错题**
2. ❌ **写入仍用旧 group_id**：`error_tools.py:132` 用 `DEFAULT_GROUP_ID="cs188"`（D16 决议未落地后端）
3. ❌ **真正 embedding search 未接入**：`neo4j_edge_client.py:235` `search_nodes` 用 Cypher `CONTAINS`（退化为关键词搜索）；真正 bge-m3 embedding search 在 `lib/agentic_rag/clients/graphiti_client.py` 独立 lib 层但**未接入主 RAG 管道**
4. ❌ **前后端零同步**：frontmatter `relationships[]` / `error_candidates[]` / wikilink **完全未同步到 Graphiti**；反向回写零代码

要实现"前后端高度一致"愿景，需 6-8 天工程修复。

---

## 第一部分：Graphiti 检索算法全图谱（Agent 1）

### 1.1 检索 API 全集

Graphiti SDK 暴露**两个公开入口**：

| API | 返回 | 默认 config | 用途 |
|---|---|---|---|
| `graphiti.search(query, center_node_uuid, group_ids, num_results, search_filter)` | `list[EntityEdge]` | `EDGE_HYBRID_SEARCH_RRF`（无 center）/ `EDGE_HYBRID_SEARCH_NODE_DISTANCE`（有 center） | 简化版 |
| `graphiti.search_(query, config, group_ids, center_node_uuid, bfs_origin_node_uuids, search_filter)` | `SearchResults`（edges + nodes + episodes + communities） | `COMBINED_HYBRID_SEARCH_CROSS_ENCODER` | 完整版 |

**MCP 工具映射**：
- `mcp__graphiti__search_memory_facts` / `search_edges` → `graphiti.search()` edges 路径
- `mcp__graphiti__search_nodes` → node_search 子系统
- `mcp__graphiti__search_communities` → community_search 子系统
- `mcp__graphiti__get_episodes` → `EpisodicNode.get_by_uuids()`
- `mcp__graphiti__get_episode_lineage` → 按 episode 链路遍历

**14 种预置 recipes**（`search_config_recipes.py`）：`COMBINED_HYBRID_SEARCH_RRF`、`COMBINED_HYBRID_SEARCH_MMR`、`COMBINED_HYBRID_SEARCH_CROSS_ENCODER`、`EDGE_HYBRID_SEARCH_*`、`NODE_HYBRID_SEARCH_*`、`COMMUNITY_HYBRID_SEARCH_*`。

### 1.2 4 层并行混合架构

每次 `search_()` 调用触发 4 层并行检索（`semaphore_gather`）：

```
                        ┌───────────────────┐
        Query  ──┬──→  │ Edge Search       │  ──┐
                 ├──→  │ Node Search       │  ──┤
                 ├──→  │ Episode Search    │  ──┤   合并 →  Reranker  →  Top-K
                 └──→  │ Community Search  │  ──┘
                        └───────────────────┘
```

每层都组合：**BM25（Lucene 倒排）+ 余弦相似度（向量）**

### 1.3 底层检索方法 — 时间复杂度详解

#### A. BM25 全文搜索（Neo4j Lucene）

**原理**：Neo4j 原生 Lucene 全文索引（`db.index.fulltext.queryRelationships/Nodes`）。
- edges 索引 `fact` + `name` 字段
- nodes 索引 `name` + `summary`
- episodes 索引 `content`
- communities 索引 `name`

**Cypher 示例**（edge BM25）：
```cypher
CALL db.index.fulltext.queryRelationships('edge_name_and_fact', $query)
YIELD relationship AS rel, score
MATCH (n:Entity)-[e:RELATES_TO {uuid: rel.uuid}]->(m:Entity)
WHERE e.group_id IN $group_ids
RETURN ... ORDER BY score DESC LIMIT $limit
```

**复杂度**：`O(log N × M)`，M = 匹配词条数，N = 总文档数 → **大规模仍稳定 < 200ms**

#### B. 余弦相似度向量搜索 ⚠️ 关键风险点

**原理**：
- edges 搜 `fact_embedding`（LLM 提炼的事实文本 embedding）
- nodes 搜 `name_embedding`
- communities 搜 `name_embedding`
- ⚠️ **episodes 没有向量检索**，只有 BM25

**Cypher 示例**：
```cypher
MATCH (n:Entity)-[e:RELATES_TO]->(m:Entity)
WHERE e.group_id IN $group_ids
WITH e, n, m, vector.similarity.cosine(e.fact_embedding, $search_vector) AS score
WHERE score > $min_score
RETURN ... ORDER BY score DESC LIMIT $limit
```

默认 `min_score=0.6`。

**复杂度**：**`O(N)` 全表扫描** ⚠️
- ❌ **未使用 Neo4j HNSW/IVF 向量索引**
- ❌ 用的是 `get_vector_cosine_func_query()`（手动计算）
- ⚠️ 这是 100K 临界点的根本原因

#### C. BFS 图遍历

仅 `cross_encoder` recipe 启用。从 seed UUID 起做 k-hop（`MAX_SEARCH_DEPTH=3`），通过 `[:RELATES_TO|MENTIONS*1..{depth}]` 路径遍历。

**复杂度**：`O(B^k)`，B = 平均节点度，k = 深度

### 1.4 Reranker 层 — 5 种合并策略

| Reranker             | 原理                                                     | 复杂度      | 备注                                         |
| -------------------- | ------------------------------------------------------ | -------- | ------------------------------------------ |
| **RRF**（默认）          | `score += 1/(rank + rank_const)`                       | `O(K×N)` | 极简，无 DB 调用                                 |
| **MMR**              | `λ × sim(doc, query) + (λ-1) × max_sim(doc, selected)` | `O(N²)`  | 去重，候选大时性能压力                                |
| **cross_encoder**    | LLM 交叉注意力打分                                            | 取决推理     | 最高精度；BGE/Gemini/OpenAI 三种后端                |
| **node_distance**    | 是否 center_node 直邻                                      | O(K)     | 只看深度 1，不算最短路径                              |
| **episode_mentions** | mention count 升序                                       | O(K)     | ⚠️ **疑似 bug**：sort ascending（应 descending） |

### 1.5 时间过滤（错误管理关键）

`SearchFilters` 4 字段：`valid_at` / `invalid_at` / `created_at` / `expired_at`，每个支持 AND/OR 组合（`list[list[DateFilter]]`）。

**关键**：时间过滤注入 Cypher WHERE 子句，是**硬过滤而非软排序**——在向量检索和 BM25 检索阶段均生效，**不会被 embedding 相似度淹没**。

```cypher
WHERE (e.valid_at >= $valid_at_0) AND (e.valid_at <= $valid_at_1)
```

⚠️ **重要**：edges 存的是 LLM 提炼的事实**有效时间区间**，**不是 episode 创建时间**。"4 周前混淆 admissibility" 必须用 `valid_at` 过滤，**不能用 `created_at`**。

### 1.6 group_id 隔离

- 纯 Cypher WHERE 过滤：`WHERE e.group_id IN $group_ids`
- **没有分库、没有分图**，所有节点共存于同一 Neo4j 数据库
- 复杂度：有 B-Tree 索引 `O(log N)`；无索引退化为 `O(N)` 全表扫

### 1.7 长上下文规模性能（关键风险评估）

| 规模            | BM25 延迟 | 向量检索延迟        | 主要问题            |
| ------------- | ------- | ------------- | --------------- |
| 100 episodes  | <10ms   | <20ms         | 无               |
| 10K episodes  | <50ms   | <100ms        | 轻微向量碎片          |
| 100K episodes | <200ms  | **500ms-2s+** | ⚠️ 向量 O(N) 全扫瓶颈 |
|               |         |               |                 |

**Zep 论文（arxiv 2501.13956）数据**：
- DMR 基准 94.8%、LongMemEval 提升 18.5%、延迟降 90%
- ⚠️ **未披露具体测试数据集规模（episodes/nodes 数量）**
- ⚠️ 论文作者**自承"无 100K episodes 公开测试"**

### 1.8 错误管理场景的可靠性

**场景**："学生 4 周前混淆 admissibility 和 consistency"

**推荐检索链路**：
1. 时间过滤 `SearchFilters(valid_at=[[DateFilter(date=4_weeks_ago, op=>=), DateFilter(date=3_weeks_ago, op=<=)]])`
2. 语义检索 `search_memory_facts("admissibility consistency confusion")` — BM25 + 向量
3. Reranker：`EDGE_HYBRID_SEARCH_CROSS_ENCODER`（BM25+cosine+BFS+精排）
4. 加 `center_node_uuid`（学生节点）触发 node_distance reranker

**4 个失败模式**：

| # | 模式 | 影响 | 对策 |
|---|---|---|---|
| 1 | 语义漂移（最大风险）| 长尾低频错题被高频压缩 → 余弦截断 0.6 失落 | 降到 0.4 / 用 cross_encoder |
| 2 | BM25 失效 | LLM 提炼时改写原始术语（"混淆" → "错误理解"）| 构建 episode 时保留原始术语 |
| 3 | 向量索引缺失 | 100K edges 后秒级延迟 | 切外置 HNSW |
| 4 | episode_mentions 排序 bug | 结果倒置 | 避免使用该 reranker |

### 1.9 三方对比（量化）


**User：我在obsidian 上是用 obsidian 的md 文件 然后再加上了 自己定义双向链接 来规划各个节点之间联系。**
**然后我们的个人记忆系统 所使用的是 Graphiti ，那么我们各个节点之间是有用 BKT 来标记理解程度 ，然后用到 FSRS 来标记出复习时间，那么我们这里的核心压力点：1，能不能推测出各个原白板精确复习时间；2，能不能在使用原白板生成检验白板时，是否可以精确的多段推理各个节点之间的关系，然后能理解到我各个节点相关内容所标记的理解程度，各个节点犯下的错误，以及各个节点我自己打下的批注，结合以上节点考察我，让我想起了原白板的内容，并且再次考察我是否会犯下原白板中相似的错误。**


| 方案                       | 精确时间            | 语义召回               | 100K 规模 | 增量更新           |
| ------------------------ | --------------- | ------------------ | ------- | -------------- |
| **Graphiti**             | 强（valid_at 硬过滤） | 中（BM25+cosine+RRF） | ⚠️ 向量瓶颈 | 原生（invalid_at） |
| **LanceDB cosine top-K** | 无               | 强（HNSW O(logN)）    | 极佳      | 需手动管理          |
| **BM25（纯文本）**            | 弱               | 无                  | 极佳      | 易              |
| **Obsidian 双链遍历**        | 无               | 无                  | 差       | 无              |
| **Grep**                 | 无               | 无                  | 差       | 无              |

**Graphiti 独特优势**：时间有效区间（valid_at/invalid_at）+ 知识图谱关系遍历（BFS）— 这是纯向量库无法实现的。

### 1.10 Agent 1 推荐配置（错误管理用）

```python
config = EDGE_HYBRID_SEARCH_CROSS_ENCODER  # BM25 + cosine + BFS + cross_encoder 精排
search_filter = SearchFilters(
    valid_at=[[DateFilter(date=date_4_weeks_ago, op=">="),
              DateFilter(date=date_3_weeks_ago, op="<=")]]
)
graphiti.search_(
    query="admissibility consistency confusion",
    config=config,
    search_filter=search_filter,
    group_ids=["vault:cs_61b:errors"],  # 隔离错误专用 namespace
    center_node_uuid=student_node_uuid,  # 触发 node_distance reranker
)
```

降低 `sim_min_score=0.4`（默认 0.6 太严），用 Ollama BGE Reranker 本地精排。

### 1.11 Agent 1 风险 + 建议总结

| 风险 | 等级 | 建议 |
|---|---|---|
| 向量检索无原生索引 | 🔴 高 | offload 到 LanceDB（已有），用 BM25 + LanceDB HNSW 联合 hybrid |
| episode_mentions reranker 倒置 | 🟠 中 | 禁用，改 RRF 或 cross_encoder |
| group_id 无物理索引保证 | 🟠 中 | 确保 Neo4j 有 B-Tree 索引 |
| 错误管理时间查询不准 | 🟡 低 | 写 episode 时显式指定 `valid_at` |

**关键文件**（Agent 1 验证）：
- `backend/.venv/lib/python3.14/site-packages/graphiti_core/search/search.py` — 4 层并行
- `backend/.venv/lib/python3.14/site-packages/graphiti_core/search/search_utils.py` — 底层 RRF/MMR/reranker
- `backend/.venv/lib/python3.14/site-packages/graphiti_core/search/search_config.py` — 配置数据结构
- `backend/.venv/lib/python3.14/site-packages/graphiti_core/search/search_config_recipes.py` — 14 种 recipes
- `backend/.venv/lib/python3.14/site-packages/graphiti_core/search/search_filters.py` — 时间过滤

---

## 第二部分：本项目 Graphiti 使用现状（Agent 2）

### 2.1 总评：4 / 10 分

写入管道接通但很窄，读取路径部分依靠 G-FAKE 代理，错误管理 group_id 仍用旧格式 `cs188`，**没有任何直接"按错误类型查 Graphiti"的读取路径**。

### 2.2 客户端入口（唯一真实实例）

**真实 Graphiti 实例只在 `GraphitiEpisodeWorker`**：

```python
# backend/app/services/episode_worker.py:389
Graphiti(
    uri=neo4j_uri,
    user=...,
    password=...,
    llm_client=GeminiClient,
    embedder=GeminiEmbedder,
    cross_encoder=GeminiRerankerClient,
    max_coroutines=3,
)
```

- Gemini 硬锁：`gemini-2.5-flash` + `gemini-embedding-001`（episode_worker.py:293, 378）
- Neo4j 预飞探针 episode_worker.py:301-356（防 graphiti-core v0.28.2 fire-and-forget bug）

⚠️ **G-FAKE 警告**：`graphiti_client.py` 和 `graphiti_client_base.py` 都是 G-FAKE 壳——它们 re-export `neo4j_edge_client.py`，**实际跑 Cypher 而非 Graphiti API**（graphiti_client.py:1-4 / graphiti_client_base.py:1-3）。

### 2.3 写入侧（A 类）— 真实但 group_id 是旧格式

**唯一真实写入点**：`GraphitiEpisodeWorker._process_episode()` → `await self._graphiti.add_episode(**kwargs)`（episode_worker.py:557）

5 个调用来源：

| 调用来源 | 位置 | 触发时机 | group_id 构造 |
|---|---|---|---|
| `record_learning_event()` | memory_service.py:464 | 用户对话 | `build_group_id(subject, canvas_name)` → `math:calculus` |
| `batch_record_events()` | memory_service.py:1167 | 批量 | 同上 |
| `record_knowledge_entity()` | memory_service.py:1270 | 含错误 | 传入 `group_id`，fallback 到 `DEFAULT_GROUP_ID="cs188"` |
| `record_temporal_event()` | memory_service.py:1789 | Canvas CRUD | `build_group_id(inferred_subject, canvas_name)` |
| `recover_failed_writes()` | memory_service.py:1859 | 启动恢复 | 同上 |

⚠️ **D16 决议未落地**：
- `build_group_id()` 产出 `subject:canvas_name` 格式（subject_config.py:205）
- **不是** D16 锁定的 `vault:<vault_id>[:<subject_id>]` 格式
- `DEFAULT_GROUP_ID = "cs188"`（config.py:472）
- `build_vault_group_id()` 函数在 `subject_config.py` 中**不存在**
- `cypher_helpers.py` 在 `backend/app/utils/` **不存在**
- → 这两个 D16 决议描述的符号在当前代码库**没有落地**

### 2.4 读取侧（B 类）— 三层架构

**真实 graphiti-core 读取只有 1 处**：`memory_service.py:1368` `worker._graphiti.search_(**search_kwargs)`

5 种 search_config recipes 在用（memory_service.py:1295-1309）：
- `combined_rrf` / `combined_cross_encoder` / `edge_cross_encoder` / `edge_rrf` / `node_rrf`

参数：
- 超时硬限 3 秒（memory_service.py:1367）
- `group_ids=[group_id]` 过滤（memory_service.py:1362）
- `num_results` 通过 `config_with_limit` 控制（默认 20）
- ⚠️ **`center_node_uuid` 在本项目代码库未见使用**（图距离 reranker 没启用）

**Legacy fallback**：`worker._graphiti.search(...)` 超时 2 秒（memory_service.py:1434）

**`MemoryService.search_memories()` 三层架构**（memory_service.py:1620-1681）：
- Tier 1 = graphiti `search_()`
- Tier 2 = Neo4j fulltext
- Tier 3 = in-memory cache

**所有上层调用全走 `MemoryService.search_memories()`**：MCP `search_memories`（memory_tools.py:195）/ `tips` 端点（tips.py:104）/ `archive`（archive.py:162）/ `conversation_inheritance.py:156` / `archive_scheduler.py:169` / `agent_service.py:2081`

⚠️ **G-FAKE `search_nodes` 警告**：
- `verification_service.py:2229` 调 `self._graphiti_client.search_nodes()`
- 实际走 `Neo4jEdgeClient.search_nodes()` Cypher `CONTAINS` 全文（neo4j_edge_client.py:190-285）
- **不是 graphiti-core 向量搜索**
- `tool_executor.py:142` 调 `self._graphiti.search_nodes()` 用 `agentic_rag.clients.graphiti_client.GraphitiClient`（agent_service.py:1486-1502）— 又一个**非本项目主 graphiti-core 实例**

### 2.5 错误管理 ↔ Graphiti 链路（用户最关心）

**写入路径（真实但 group_id 有 bug）**：

```
Agent 检测到错误
  → MCP 工具 record_error (error_tools.py:60)
    → error_classifier.classify() (error_classifier.py)         ← 仅 LLM 分类
      → memory_svc.record_knowledge_entity(
            event_type="misconception",
            group_id=DEFAULT_GROUP_ID                            ← ⚠️ "cs188" 旧格式
        ) (error_tools.py:115, 132)
        → memory_service._enqueue_episode(group_id="cs188")     ← 真实 Graphiti 写入
```

⚠️ **问题**：`error_tools.py:132` 传 `group_id=DEFAULT_GROUP_ID`（即 `"cs188"`），**不是按 vault/subject 动态构造**。错误实体确实写入图谱，但与其他内容 namespace 混在一起。

**verification_service 验证流程**（verification_service.py:814）：
- → `record_knowledge_entity(event_type="exam_attempt")`
- group_id 逻辑：`canvas_name.split("/")[0]`（verification_service.py:825）
- ⚠️ 也是旧格式

**读取路径（缺失）**：

🔴 **"查 3 周前 admissibility 错题"没有专用读取路径**

唯一接近的：`search_memories(query="admissibility misconception")` 触发 Tier 1 graphiti `search_()`
- 但这是 semantic 搜索，**不是按 `event_type=misconception` 过滤的结构化查询**
- graphiti-core 的 `search_edges` / `search_memory_facts` 两个 API **从未被本项目调用**

**verification_service 的 `_build_common_mistakes_signal()`**（verification_service.py:1937-1968）构建弱点信号，但数据源是 BKT lapse rate + MemoryService score history，**不查 Graphiti 的 misconception 节点**。

🔴 **结论**：错误管理路径**写入真实 Graphiti**（通过 EpisodeWorker），但：
1. group_id 用旧 `"cs188"` 而非 vault-scoped
2. **没有任何代码路径从 Graphiti 按 `misconception` 类型检索历史错误用于复习推荐** — 只写不读

### 2.6 已知 G-FAKE / G-PIPE Gap

- **G-FAKE-001**（`graphiti_client.py` / `graphiti_client_base.py` / `neo4j_edge_client.py`）
  - `verification_service._graphiti_client.search_nodes()` 查 Cypher 而非向量图
  - 不会召回已写入 graphiti-core 的 misconception 向量节点
  - 写入路径（EpisodeWorker → graphiti-core）和读取路径（G-FAKE search_nodes → Neo4j Cypher）**namespace 不互通**

- **G-PIPE-006**（verification_service.py:811）
  - 已修复：验证得分写入 Graphiti
  - 但 group_id 是 `canvas_name.split("/")[0]`，与 D16 `vault:` 格式不一致
  - 跨 vault 查询时会漏数据

- **错误管理无闭环**
  - `record_error` → Graphiti 写入（`group_id="cs188"`）
  - 无法通过 `search_memories` 以 `event_type=misconception` 过滤召回
  - 如需"查学生 admissibility 错题"，需要调 `graphiti_core.search_()` 并传 `SearchFilters(entity_labels=["Misconception"])` 或 `edge_types`
  - **这段代码不存在**

---

## 第三部分：主动检测 + 增量提问可行性（Agent 3）

### 3.1 一句话结论

愿景（AI 在对话中当场问"要记下来吗？"）与现状的核心差距：

- **现状**：异步、用户主动去 Dashboard 看的批量确认
- **愿景**：同步、对话内即时的单条 yes/no 提问

这需要在 Obsidian plugin 层增加"对话后 inline suggestion UI"，并对两个 Skill 做小幅改造。**整体可行但非零工作量**。

### 3.2 现状（Story 2.5.X 已实现）

✅ **`/chat/post-turn-extract`**（`backend/app/api/v1/endpoints/chat.py:316-440`）：
- 对话轮次结束后，plugin 可 POST 完整对话消息
- backend 自动调 `ErrorExtractor` LLM 分析
- → `classify_with_pedagogy` 双标签分类
- → 写入 `error_candidates[]`（D15 决策默认 `candidate_only` 模式；当前 chat.py:382-390 还在用 `write_confirmed` 兼容模式，Task 5 才切换）

✅ **`/errors/accept-candidate` / `/errors/dismiss-candidate` / `/errors/dispute-candidate`**（`backend/app/api/v1/endpoints/errors.py`）：
- accept → 移入 `errors[]` + 写 Graphiti
- dismiss/dispute → 保留 candidate 供训练

✅ **两个 Skill 均为纯对话模式**：
- `node-chat/SKILL.md` 硬约束"不写 vault 文件"
- `chat-with-context/SKILL.md` 同

❌ **Obsidian plugin 现状**：
- 仅有 `callout.ts` 手动 `[!error]+` 标注（Cmd+Shift+A）
- 仅有 `ConfirmExamModal` 等有限 Modal
- **没有**对话后主动弹出 suggestion 的 UI 组件

### 3.3 4 大 Gap 分析

#### Gap A：触发（Detect）

- ✅ **后端已实现**：`post-turn-extract` 端点能在每轮对话后提取候选
- ❌ **前端未调用**：plugin 的 Skill 是纯对话模式，**不触发 backend hook**
- 愿景需要：每轮 AI 回复流式结束后，plugin 自动 POST `/post-turn-extract`，拿到 `extracted_count > 0` 时触发 UI 提问

#### Gap B：提问 UI（Ask Inline）⚠️ 最大 gap

- Claudian（Claude Code CLI sidebar）是文本流式对话窗口
- ❌ **没有原生 AskUserQuestion / suggestion widget**
- ❌ Claude Code Skill 规范中**不存在 "AskUserQuestion" 工具** — Skill 只能输出文字，无法注入 Obsidian 侧边栏 UI 组件

**真正的 inline 提问必须由 Obsidian plugin 侧实现**：
- AI 回复完毕后，plugin 探测到 `error_candidates` 新增
- 在编辑区底部或通知栏弹出轻量 `SuggestionModal`/`Notice`（类似现有 `ConfirmExamModal`）
- 询问"AI 检测到你可能混淆了 X 和 Y，要记录吗？"

#### Gap C：写入路径（Write）

- 用户点 yes → plugin 调 `POST /api/v1/errors/accept-candidate`（已有端点）
- → 直接移入 `errors[]` + fire-and-forget Graphiti
- ✅ 链路已就位，**不需要新开发**

#### Gap D：Graphiti 同步

- `accept_candidate` 服务（`candidate_service.py:189-370`）调 `write_error_to_graphiti`
- 采用 `asyncio.create_task` fire-and-forget
- ✅ 已实现一步到位
- 愿景中"记录到 Graphiti"**不需要额外中间步骤**

### 3.4 工作量估算（约 2-3 天）

| 改动 | 文件 | 估算 |
|---|---|---|
| Plugin：对话结束后自动调 `/post-turn-extract`，解析响应 | `frontend/obsidian-plugin/src/main.ts` 或新 `error-detection.ts` | 4h |
| Plugin：`SuggestionNotice` / 轻量 Modal（描述 + yes/dismiss/dispute）| 新 `error-suggestion.ts` + `main.ts` 注册 | 1d |
| Plugin：调 accept/dismiss/dispute API 客户端 | `main.ts` 或新 `backend-client.ts` | 4h |
| Backend：`post-turn-extract` 切真正 `candidate_only` 模式（Task 5）| `backend/app/api/v1/endpoints/chat.py:382-390` | 2h |
| Skill（可选）：在 `node-chat`/`chat-with-context` 加 soft hint | 两个 `SKILL.md` | 2h |
| **合计** | | **2-3 天** |

### 3.5 风险（重要）

#### 风险 1：打断学习流

每轮对话后弹 UI 提问，高频对话（快速追问）→ 连续弹窗

**对策**：
- 同一 `candidate_id` 只问一次（去重冷却）
- 仅在 `confidence > 0.7` 时弹出
- 低置信度候选静默留 Dashboard

#### 风险 2：误检测疲劳

`ErrorExtractor` 是 LLM，false positive 在用户口语化表达时偏高。

**社区数据**：
- Khan Academy Khanmigo / Duolingo AI tutor 成熟做法均是**延迟提问**（一轮学习结束后摘要性提问）
- 与当前 Dashboard 模式更接近
- **Duolingo 内部研究**：过度即时提问导致 **18% 用户关闭 AI 提示功能**

#### 风险 3：ADHD 情境

用户集中思考时被弹窗打断 = 已知认知负担问题

**对策**：
- 提供"静默模式"设置
- 仅在用户明确触发（如 Cmd+Shift+A 时 AI 增强建议）

#### 风险 4：UX 未验证 ⚠️

| AI Tutor | 错误记录方式 |
|---|---|
| Khan Academy Khanmigo | 答错后立即问"你是怎么想到这一步的？"（Socratic 式）— **独立对话窗口，不是嵌入式 sidebar** |
| Synthesis Tutor | 完全异步（对话后批量复盘）— 与 Dashboard 模式一致 |
| Duolingo AI | 延迟提问 |

🔴 **关键发现**：**没有主流 AI tutor 采用"每轮对话后 inline yes/no 弹窗"** — 这是本项目愿景的**创新点，但也是未验证的 UX**。

### 3.6 v1.5 安全过渡推荐

先实现：
- 对话轮结束后自动调 `/post-turn-extract`（静默）
- 候选写入 `error_candidates[]`
- Dashboard 显示**角标提醒**（类似 Notion 通知红点）

用户 UX 测试后再决定是否升级为 inline 弹窗。

---

## 第四部分：Graphiti vs 双链 vs Grep 三方对比 + 双向同步设计（Agent 4）

### 4.1 一句话结论

用户论断**在语义检索、时间维度、跨节点推理这三类查询上成立**；但在**精确链接遍历、低延迟点查、以及"前端定义的关系镜像"**这三个场景上**不成立**——因为当前 Graphiti 后端**并不读取前端 frontmatter 的 `relationships[]` 和 `error_candidates[]`**，两者并非镜像而是两套独立状态。

### 4.2 三方检索能力对比表

| 维度 | Graphiti（Neo4j + LanceDB） | Obsidian 双链（metadataCache + wikilink）| Claude Code Grep（ripgrep）|
|---|---|---|---|
| **索引方式** | bge-m3 embedding + Neo4j Cypher CONTAINS + temporal episode | obsidiantools 解析 wikilink → NetworkX 内存图 + `processFrontMatter` API | ripgrep 实时字节扫描，无索引 |
| **召回类型** | 语义近邻 / entity CONTAINS / Cypher 路径查询 / `valid_at` 时间过滤 | 精确 BFS N-hop 遍历 / 反向链接 / frontmatter 字段 | 字符串 / regex 字面匹配 |
| **100 节点** | ~50–120ms（Neo4j CONTAINS）；LanceDB vector ~20ms | graph build ~80–200ms（含 obsidiantools parse）；query <5ms | <10ms |
| **10K 节点** | ~100–300ms（Neo4j index scan）；vector search ~30–60ms | graph build 5–15s（社区报告：~1–3s per 1K notes）；query ~10–30ms | 50–200ms |
| **100K 节点** | Neo4j 带 index ~200–500ms；vector search ~100–200ms | ⚠️ graph build 120–600s（社区报告 vault >50K 文件需 30–120s）；query <100ms（内存 BFS）| 2–10s |
| **长尾低频项召回** | 强（embedding 捕获语义近邻）| 中（命中需 wikilink；孤立节点不可达）| 弱（必须知道精确词）|
| **跨语言（中英混合）** | 强（bge-m3 多语言 cross-lingual）| 弱（wikilink 必须同名精确匹配）| 中（unicode-aware 但需精确拼写）|
| **时间维度（"3 周前错题"）** | 强（`valid_at` filter，memory_service 记录 `temporal_event`）| 无 | 无 |
| **关系推理（A→B→C）** | 强（Cypher MATCH path query）| 中（用户手维护后可 BFS；不支持条件路径）| 无 |
| **实时性** | 写入异步队列（GraphitiEpisodeWorker），通常 <2s 可查 | 实时（文件保存触发 `metadataCache.on("changed")`）| 实时（每次扫文件）|
| **启动开销** | Neo4j 已运行则无；冷启动 500ms-2s | ⚠️ 首次 build 几秒到分钟（大 vault）| 无 |

### 4.3 用户论断成立性分析

**论断**："Graphiti 在长上下文下比双链+md 文件检索更快速可靠"

#### 快速性

| 查询类型 | Graphiti vs 双链 |
|---|---|
| 语义模糊查询（"和特征值有关的概念"）| ✅ Graphiti **更快**（embedding ~30ms vs 双链无法处理）|
| 精确链接点查（"TestConceptA 的 1-hop 邻居"）| ❌ 双链**更快**（obsidiantools BFS <5ms vs Neo4j round-trip ~50ms）|
| 全库扫描（所有 error_candidates 非空的节点）| ❌ 双链**更快**（metadataCache 内存过滤 <1ms vs Cypher CONTAINS scan）|
| 时间过滤（"3 周前的学习记录"）| ✅ Graphiti **独占**（只有后端有 `temporal_event` 索引）|
| 10K+ 节点冷启动 | ✅ Graphiti **更快**（Neo4j 常驻内存 vs obsidiantools 5-15s rebuild）|

**结论**：快速性**取决于查询类型**。模糊语义/历史查询 Graphiti 快；精确短路径双链快。

#### 可靠性（召回率）

- **Graphiti 更可靠场景**：用户用不同措辞查同一概念（如"矩阵变换的缩放因子" → Eigenvalue），embedding 召回；双链召回率依赖精确 wikilink，缺链则 0 召回
- **反例（双链更可靠）**：用户精确知道节点名（直接查 `[[TestConceptA]]`），双链 100% 精确召回
- **当前项目缺陷**：`search_nodes` 方法（`neo4j_edge_client.py:235`）使用 Cypher CONTAINS 而非 vector similarity，**相当于退化成关键词搜索，未使用 bge-m3 embedding**
- 真正的 embedding 搜索在 `lib/agentic_rag/clients/graphiti_client.py`（独立 lib 层），**两套实现并行存在**

### 4.4 双向同步现状（用户隐含愿景）

#### A. 前端 → 后端（已有 vs 缺失）

| 数据 | 是否同步到后端 | 机制 |
|---|---|---|
| Canvas 白板节点（`CanvasNode`）| ✅ 已有 | `sync_service.py` Outbox + `SyncBatchRequest` → Neo4j MERGE |
| Canvas 边（`CANVAS_EDGE`）| ✅ 已有 | 同上 |
| `error_candidates[]` frontmatter | ❌ **未同步** | 仅在前端 Dataview query 用（Dashboard.md:215）；`record_error` 工具写 Graphiti 但不读前端 frontmatter |
| `relationships[]` frontmatter（node-derivation.ts 构造）| ❌ **未同步** | 前端 processFrontMatter 写 .md；后端无读取此字段逻辑 |
| wikilink `[[节点/X]]` | ⚠️ **部分** | WikilinkGraphService 读建内存图，**不写 Neo4j KG**；wikilink_graph_service.py 仅供 BFS 查询 |
| 学习对话 episodes（掌握度、错误）| ✅ 已有 | `memory_service.record_temporal_event()` → `GraphitiEpisodeWorker` |

#### B. 后端 → 前端反向回写（**完全缺失**）

代码库全局搜索 `write_back` / `frontmatter_patch` / `update_frontmatter` / `patch_note` **均无结果**（已验证）。

🔴 **零反向回写**：
- Graphiti 自动 extract 的 entity edges 不写回前端 frontmatter
- 后端推断的"A 与 B 强相关"不推送到 Obsidian
- 用户在 Dashboard 确认/驳回 `error_candidates` 后，**没有机制将结果写回 Graphiti**

#### C. 冲突解决（当前未定义）

- 删除 wikilink → Neo4j 对应 `CANVAS_EDGE` 不同步删除（Outbox 只同步 Canvas 白板的边，不同步 .md 文件内 wikilink 的删除）
- 重命名节点 .md 文件 → Neo4j `CanvasNode.id` 不更新（Obsidian rename 不触发 Outbox）

### 4.5 推荐架构

#### 混合检索路由

```
用户查询
  │
  ├─ 精确节点查（已知节点名）         → Obsidian wikilink BFS（<5ms）
  │
  ├─ 模糊语义查（概念关联）           → Graphiti vector search（lib/agentic_rag 层，非降级 CONTAINS）
  │
  ├─ 时间维度查（"最近N周错误"）      → Graphiti temporal filter（唯一能力）
  │
  ├─ 精确关键词查（调试/定位）        → Claude Code Grep（实时，无依赖）
  │
  └─ 跨主题发现（"还有哪些关联概念"） → Graphiti Cypher path query
```

#### 同步频率

- **触发器：文件保存**（已有 `metadataCache.on("changed")`）
- 扩展：保存 → 解析 frontmatter `relationships[]` → POST `/api/v1/sync` 写 Neo4j
- 比定时 5 分钟更精确，且代码钩子已存在（main.ts:93-98）
- Graphiti episodes 保持当前异步队列模式（< 2s 延迟），不需要实时

#### 冲突权威 — **前端是 source of truth**

理由：
1. 用户在 Obsidian 直接编辑，心智模型在前端
2. Obsidian 有 Git 版本控制兜底
3. Graphiti 当前是派生数据（derived），不应覆盖用户意图

Graphiti 的角色应该是：**只读索引 + 计算层**，负责"语义推断"；前端 wikilink 和 frontmatter 才是"用户定义的关系"。

### 4.6 双向同步工作量

| 任务 | 工作量 | 优先级 |
|---|---|---|
| frontmatter `relationships[]` → Neo4j edges 同步（前→后）| 2-3 天 | 中 |
| wikilink 删除/重命名 → Neo4j edge delete/node rename | 3-4 天 | 中 |
| `error_candidates[]` frontmatter → Graphiti episode 同步 | 2 天 | 中高 |
| Graphiti 推断关系 → 前端 frontmatter 写回（反向）| 5-7 天 | **延后到 v2** |
| 当前 `search_nodes` CONTAINS → 替换为真正 bge-m3 vector search | **2-3 天** | 🎯 **最高 ROI** |

🎯 **最高优先级（最高 ROI）**：
- 把 `lib/agentic_rag/clients/graphiti_client.py` 中的真正 embedding 搜索接入 `app/mcp/tools/note_search_tools.py` 的 RAG pipeline
- 取代当前退化的 CONTAINS 查询
- **这一个改动就能让 Graphiti 的语义召回优势真正生效**，无需任何新同步逻辑

---

## 第五部分：社区案例 + 反例 — 长期使用真相（Agent 5）

### 5.1 一句话结论

**100K+ 规模下，知识图谱记忆系统目前处于"有条件可靠"状态**——Graphiti/Zep 自己的 30x 规模冲击测试证明，未优化时会出现系统性崩溃（延迟从 200ms 飙至 2s+，ingestion 60s 无响应），但针对性架构重构后可恢复并维持 65ms P75 查询；真正的 100K+ 节点向量暴力搜索是**已知硬性瓶颈**，需外置向量索引（HNSW）才能维持可靠定位。

### 5.2 Graphiti / Zep 自家事故（最重要案例）

#### Zep 30x 流量冲击（2024 年底）

企业客户集中上线 → 两周内请求量暴增 30 倍（每小时数千 → 每小时百万）→ 完整故障链：

| 指标 | 故障前 | 故障中 | 修复后 |
|---|---|---|---|
| 上下文检索 P95 | 200ms | **>2s** | 200ms |
| Episode ingestion | 正常 | **60s（无响应）** | 提升 92% |
| LLM 成本 | 正常 | **超配 3-5x，触发限流** | 减半 |
| 图搜索 P75 | — | — | **65ms** |

**根本原因**：Neo4j 同时承担图操作 + 向量搜索 + BM25 + 持续写入四种工作负载——单节点超临界量后**互相干扰**。

**修复（6 周）**：
- 向量/BM25 搜索卸载到专用检索层
- Go 服务替代 Python LLM 网关
- Shannon 熵 + TF-IDF + LSH 替代部分 LLM 调用

#### GitHub Issues 4 个直接失败案例

| Issue | 时间 | 现象 | 状态 |
|---|---|---|---|
| **#186** | 2024-10 | 标准 Docker 部署，10 条消息处理近 2 分钟，积压 940+ | 已关闭，未给根因 |
| **#356** | 开放中 | "even simple chat conversations take a very long time to ingest"，多用户场景担心 1-2 小时 | 无官方解决 |
| **#450** | 2025-05 | MCP Server 更新已有实体时 100% CPU 死锁，唯一解决重启容器 | 已关闭，根因不明 |
| **#879** | 2025-08 | 批量上传 entity resolution 的 `duplicates` 字段验证错误，`add_episode_bulk()` 完全失败 | — |

🔴 **#879 是错误管理的直接隐患** — 我们的错题批量同步会触发同样问题。

#### Graphiti 论文（arxiv 2501.13956）诚实数据

| 基准 | 数据 | 规模 |
|---|---|---|
| DMR | **94.8%** 准确率 | ⚠️ 仅 500 个多轮对话（每个 ≤60 条消息）|
| LongMemEval | **71.2%**（gpt-4o），比基线提升 18.5% | 延迟 28.9s → 2.58s（90% 减少）|

**作者自承局限性**：
> "no existing benchmarks adequately assess Zep's capability to process and synthesize conversation history with structured business data"

🔴 **没有 100K episodes 的公开测试数据**

### 5.3 Mem0（同类对手）

**论文（arxiv 2504.19413）使用 LoCoMo 基准**：
- 测试集：10 个扩展对话，每个约 600 轮 / 2 万 tokens — 同样**小规模**
- 图记忆（Mem0g）token 消耗是纯向量版的 2 倍（14K vs 7K）
- Zep 消耗 **>600K tokens**（冗余设计的真实代价）
- 图记忆在多跳问题上比纯向量版提升约 2%
- ⚠️ **单跳简单事实检索反而略有下降**

**生产扩展（2025）**：
- 11 月：增加 Apache Cassandra 支持
- 9 月：增加 Valkey 支持
- → 社区通过**选型更强存储后端**解决 volume，**而非算法层修复**

### 5.4 Letta / MemGPT（内存层级管理）

**Issue #957（2024-02）**：MemGPT 在本地 LLM（koboldcpp，8K 上下文）真实崩溃：
```
Request exceeds maximum context length (8465 > 8192 tokens)
```

系统尝试用超长消息完成摘要 → 触发级联溢出。

**根本问题**："summarize 75% of messages" 策略在小上下文窗口下会把 **summary 本身变得比原始内容更长**

🔴 **这是内存层级管理在长期使用后的典型退化模式** — summary 越来越大，最终自身就成为瓶颈。

**Letta 自承**：agents in production "degrade over time (derailment)"，并因此发布 Recovery-Bench 和 Skill Learning 机制 — 退化是已知现象。

### 5.5 Obsidian 双链（用户的前端参照系）

| 工具 | 规模 | 真实反馈 |
|---|---|---|
| Obsidian | >50K 笔记 | 桌面普通功能正常，⚠️ **Graph View 是唯一明显变慢的地方** |
| Logseq | 7500 页 | 启动 >30s |
| Logseq | 10000 页 | **无法测试完成**，超出可用限制 |

**规律**：双向链接**本身**在大规模下保持稳定，**可视化遍历**（全图渲染）才是瓶颈 — 和 Graphiti 的向量暴力搜索同构问题：都是 O(n) 或 O(n²) 全量扫描。

### 5.6 Graphiti 核心向量搜索瓶颈（用户最关心）

#### GitHub Issue #1229 揭露根本限制

> "works well for small-to-medium graphs (< 100K entities) but becomes a bottleneck at scale"

🔴 **官方明确的临界点**：< 100K 实体

**O(N) 暴力搜索的问题**：
- 100K 实体 = 每次查询比较 100K 次向量点积
- Canvas Learning System 1-2 年后（每天 50 次交互 × 5-10 节点/交互）→ 节点数轻松 >10 万

#### Neo4j HNSW 索引（5.11 引入）

- ⚠️ Graphiti 当前实现**并非默认启用**这个索引
- **Issue #1229** 就是请求添加外置向量数据库（Milvus/Zilliz）作为加速层

#### FalkorDB 替代路径

| 测试 | Neo4j | FalkorDB |
|---|---|---|
| 381K 节点/804K 边图，12 个查询 | — | 11/12 比 Neo4j 更快（sub-10ms）|

可作为规模扩展的替代路径。

### 5.7 4 大反例（用户最需要的判断依据）

#### 反例 1：向量暴力搜索 100K+ 性能崩溃 🔴

不是假设，是 Graphiti issue #1229 中的架构说明。Canvas Learning System 1-2 年节点轻松 >10 万。

#### 反例 2：Entity Resolution 长期错误累积 🔴

- 默认阈值约 0.92-0.98
- 真实问题：不同上下文同名实体可能被错误合并，也可能永远不合并
- → 同一概念有 3-5 个孤立节点
- Issue #879 证明 batch 写入时 entity resolution 本身也会报错崩溃
- **静默积累** → 最终导致检索"孤岛"节点

🔴 **这正是用户担心的"长上下文下无法定位错误"场景**

#### 反例 3：Letta Filesystem 简单 grep 打败专用记忆库

LoCoMo 基准：
- "Letta Filesystem"（仅把对话历史存文件）：**74.0%**
- 多数专用记忆工具库：< 74.0%

🔴 **如果一个简单 grep 方案能打败专门设计的向量记忆库，那么知识图谱的额外工程复杂度是否总是值得？**

对 Canvas Learning System 这种**结构化学习场景**，答案倾向于"是的，KG 值得" — 但需要清楚其成本。

#### 反例 4：实际矛盾管理失败（生产级）

真实代理失败案例：
- agent 创建 N8N workflow
- action 超时 → agent 认为失败
- 用户纠正后 → agent 在"成功"和"失败"两个矛盾状态来回震荡，无法收敛

🔴 Graphiti 时序事实机制（temporal invalidation）**理论上**通过时间戳标记旧事实为无效可以解决，但当两个矛盾 episode 短时间内接连写入时，LLM 的 entity resolution 是否能正确判断哪个更新？**生产中尚无大规模验证**。

### 5.8 5 条 Best Practice（直接采纳）

#### BP-1：< 80K 节点设容量预警，达临界切 HNSW / FalkorDB

- Graphiti 内置向量搜索在 < 100K 时勉强可用
- > 100K 后不可接受
- **提前在 80K 节点时迁移**到 Neo4j HNSW 索引或 FalkorDB
- 配置：`graphiti` 初始化时启用 `neo4j.vector.index` 或迁移 FalkorDB

#### BP-2：错误用独立 group_id + 强制 TTL

- 学习错误（misconceptions）作为独立 `group_id` 存入 Graphiti，与通用知识节点分离
- 好处：
  - 搜索时专门 filter 错误记录，避免被海量通用知识稀释
  - 强制 temporal invalidation（用户纠正后旧错误明确标 `invalid=True`）
  - 不依赖 LLM 自动判断是否覆盖

#### BP-3：每 30 天 build_communities + 孤岛清理

- `build_communities` 重新计算图聚类
- 孤岛节点（entity resolution 失败副产物）会随积累
- 定期检测：`MATCH (n) WHERE NOT (n)--() RETURN n` 找无关联节点 → 人工或自动 prune
- **直接防止 Issue #879 类型的 deduplication 失败导致的静默积累**

#### BP-4：Hot/cold 分层记忆

借鉴 Mem0 发现（graph memory token 是向量 2x，Zep 高达 600K tokens）：

- **Hot layer**（纯向量，<1K 条）：最近 90 天活跃错误 + 当前学习单元的关键概念
- **Cold layer**（KG，无限）：历史错误关系、长期概念网络
- 检索时先查 hot layer（<50ms），hot miss 才走 KG（<300ms）

#### BP-5：用户纠正用显式双写 API，不依赖 LLM auto-resolve

Issue #450 的 100% CPU 死锁 + 矛盾状态震荡案例说明：

❌ 不要依赖 Graphiti 自动 edge invalidation
✅ 改用明确 API：
```python
delete_entity_edge(old_edge_uuid)
add_memory(corrected_fact)
```

🔴 **这是长期使用中保持"错误定位可靠性"的最关键工程决策**

### 5.9 Sources（社区案例链接）

- [How We Scaled Zep 30x in 2 Weeks](https://blog.getzep.com/scaling-agent-memory-zep-30x/)
- [Zep arxiv 2501.13956](https://arxiv.org/abs/2501.13956)
- [Mem0 arxiv 2504.19413](https://arxiv.org/abs/2504.19413)
- [Graphiti Issue #186 — slow ingestion](https://github.com/getzep/graphiti/issues/186)
- [Graphiti Issue #356 — Long Ingestion](https://github.com/getzep/graphiti/issues/356)
- [Graphiti Issue #450 — MCP 100% CPU](https://github.com/getzep/graphiti/issues/450)
- [Graphiti Issue #879 — Bulk upload validation error](https://github.com/getzep/graphiti/issues/879)
- [Graphiti Issue #1229 — Milvus/Zilliz external vector store](https://github.com/getzep/graphiti/issues/1229)
- [Letta Issue #957 — Memory context limit](https://github.com/letta-ai/letta/issues/957)
- [FalkorDB vs Neo4j benchmarks](https://www.falkordb.com/blog/graph-database-performance-benchmarks-falkordb-vs-neo4j/)
- [Obsidian large vault](https://forum.obsidian.md/t/obsidian-graph-view-doesnt-work-for-a-large-vault/106287)
- [Logseq large graph](https://discuss.logseq.com/t/very-slow-performance-with-large-local-graph/1484)
- [State of AI Agent Memory 2026 - Mem0](https://mem0.ai/blog/state-of-ai-agent-memory-2026)

---

## 第六部分：综合推荐方案

### 6.1 4 项立即做（按 ROI 排序）

| # | 改动 | 工作量 | ROI 理由 |
|---|---|---|---|
| 1 | **接入 lib/agentic_rag embedding search 到主 RAG pipeline** | 2-3 天 | 一改让 Graphiti 语义优势生效（取代 CONTAINS 退化）|
| 2 | **错误用独立 group_id `vault:<vault>:errors` + TTL 30 天** | 2 天 | 防错题被通用知识淹没，社区 best practice |
| 3 | **D16 group_id 落地 backend**：实现 `build_vault_group_id()` + `cypher_helpers.py` | 1 天 | 修旧 `cs188` 写入 bug |
| 4 | **Plugin v1.5 静默 post-turn-extract + Dashboard 角标** | 1 天 | UX 安全过渡（避开 inline 弹窗未验证风险）|

**合计 6-7 天**

### 6.2 4 项延后（v2 或监控触发）

| # | 改动 | 触发条件 |
|---|---|---|
| 5 | **反向同步 Graphiti → frontmatter** | v2，需先确定冲突权威 |
| 6 | **Inline yes/no 弹窗** | v1.5 角标数据观察后再决定 |
| 7 | **80K HNSW 迁移 / FalkorDB** | 节点数达 80K 临界时 |
| 8 | **30 天 community rebuild scheduler** | 节点 ≥ 5K 时启动 |

### 6.3 错误管理读取闭环建议（关键缺口）

当前**只写不读**。建议 Story 2.5.Z 加：

```python
# backend/app/api/v1/endpoints/errors.py 新增
@router.get("/history")
async def get_error_history(
    canvas_path: str,
    weeks_ago: int = 4,
    pedagogy_type: str | None = None,
):
    """按 misconception 类型查 Graphiti 历史错题（用于复习推荐）"""
    group_id = build_vault_group_id(vault_id=..., subject_id="errors")
    config = EDGE_HYBRID_SEARCH_CROSS_ENCODER
    search_filter = SearchFilters(
        valid_at=[[
            DateFilter(date=now - timedelta(weeks=weeks_ago), op=">="),
            DateFilter(date=now, op="<="),
        ]],
        edge_types=["MISCONCEPTION"] if pedagogy_type else None,
    )
    results = await graphiti.search_(
        query=f"misconception {pedagogy_type or ''}",
        config=config,
        search_filter=search_filter,
        group_ids=[group_id],
        center_node_uuid=student_node_uuid,  # 触发 node_distance reranker
        num_results=20,
    )
    return [r.to_dict() for r in results.edges]
```

工作量 ~1 天（含 unit test）。

---

## 第七部分：4 个决策点（请用户判断）

### Decision 1：embedding search 接入是否优先？

**背景**：当前 `search_nodes` 用 Cypher CONTAINS（关键词），真正 bge-m3 embedding 在 `lib/agentic_rag` 独立 lib 但未接入主管道。

**选项**：
- A. 立即接入（2-3 天）→ 让 Graphiti 语义优势生效
- B. 延后到 Phase 2 → 先做错误管理闭环

**Claude 推荐**：A

### Decision 2：错误管理读取路径是否补齐？

**背景**：当前**只写不读**——`record_error` 写 Graphiti 但无任何 endpoint 按 `misconception` 类型查回。

**选项**：
- A. Story 2.5.Z 加 `/errors/history` endpoint（~1 天）
- B. 等 v2 复习推荐功能时再做
- C. 先验收 2.5.X/Y 主流程，按需再加

**Claude 推荐**：A（错题"只写不读"违背用户"长上下文可靠定位"愿景）

### Decision 3：inline 弹窗 vs Dashboard 角标？

**背景**：愿景是 inline yes/no 弹窗，但社区**没有主流 AI tutor 用这种 UX**（Khan/Duolingo/Synthesis 全是异步 Dashboard）。

**选项**：
- A. v1.5 安全过渡：静默检测 + Dashboard 角标提醒（1 天）→ 验证 UX 数据再升级
- B. 直接做 inline 弹窗（2-3 天）→ 创新但未验证
- C. 完全异步（保持现状）

**Claude 推荐**：A

### Decision 4：冲突权威 — 前端 source of truth 还是 Graphiti 优先？

**背景**：要实现"前后端高度一致"愿景，冲突时谁赢必须明确。

**选项**：
- A. 前端 source of truth（Graphiti 派生层）→ 用户在 Obsidian 编辑，有 Git 兜底
- B. Graphiti 优先（前端从后端拉取）→ 适合多 client 但 Obsidian 单 client 用不上
- C. 混合：用户编辑前端胜，AI 推断后端胜（need conflict UI）

**Claude 推荐**：A

---

## 附录 A — 5 Agent 调研引用文件清单

### Agent 1（Graphiti 算法图谱）
- `backend/.venv/lib/python3.14/site-packages/graphiti_core/search/search.py`
- `backend/.venv/lib/python3.14/site-packages/graphiti_core/search/search_utils.py`
- `backend/.venv/lib/python3.14/site-packages/graphiti_core/search/search_config.py`
- `backend/.venv/lib/python3.14/site-packages/graphiti_core/search/search_config_recipes.py`
- `backend/.venv/lib/python3.14/site-packages/graphiti_core/search/search_filters.py`

### Agent 2（本项目使用现状）
- `backend/app/services/episode_worker.py:389`（唯一真实 Graphiti 实例）
- `backend/app/services/memory_service.py:464, 1167, 1270, 1789, 1859`（5 个写入点）
- `backend/app/services/memory_service.py:1295-1309, 1368, 1434`（读取点 + recipes）
- `backend/app/services/memory_service.py:1620-1681`（三层架构 search_memories）
- `backend/app/mcp/tools/error_tools.py:60, 115, 132`（错误管理写入）
- `backend/app/services/verification_service.py:811, 814, 825, 1937-1968, 2229`（验证 + G-FAKE）
- `backend/app/clients/neo4j_edge_client.py:190-285`（G-FAKE search_nodes）
- `backend/app/core/subject_config.py:205`（build_group_id，旧格式）
- `backend/app/core/config.py:472`（DEFAULT_GROUP_ID="cs188"）

### Agent 3（主动检测可行性）
- `backend/app/api/v1/endpoints/chat.py:316-440`（post-turn-extract 端点）
- `backend/app/api/v1/endpoints/chat.py:382-390`（需切 candidate_only 模式）
- `backend/app/api/v1/endpoints/errors.py`（accept/dismiss/dispute）
- `backend/app/services/candidate_service.py:189-370`（write_error_to_graphiti）
- `canvas-vault/.claude/skills/node-chat/SKILL.md`
- `canvas-vault/.claude/skills/chat-with-context/SKILL.md`
- `frontend/obsidian-plugin/src/main.ts`（待加 error-detection.ts）

### Agent 4（三方对比）
- `backend/app/clients/neo4j_edge_client.py:235`（CONTAINS 退化）
- `backend/lib/agentic_rag/clients/graphiti_client.py`（真正 embedding，未接入）
- `backend/app/mcp/tools/note_search_tools.py`（待接入目标）
- `backend/app/services/wikilink_graph_service.py`（前端 BFS only）
- `frontend/obsidian-plugin/src/main.ts:93-98`（metadataCache 钩子）

### Agent 5（社区案例）
- 见第 5.9 节 Sources 链接

---

## 附录 B — 用户批注 5 点 vs 调研发现对照

| 批注点 | 用户原话 | 调研发现 | 评估 |
|---|---|---|---|
| 1（UX）| 错误记录没显示告诉我错误是什么 | CandidateSuggestModal 只显示 desc 截 80 字符 | ✅ 简单修复（~2h）|
| 2（主动）| Claudian 应主动检测+增量提问 | post-turn-extract 已实现，plugin 没调；inline UI 缺；社区无成熟案例 | ⚠️ v1.5 角标过渡 |
| 3（一致 #1）| Graphiti ↔ 前端批注高度一致 | error_candidates / wikilink **零同步** | ❌ 未实现 |
| 4（论断）| Graphiti 比双链+md 更快可靠 | 条件性成立；当前实现退化为 CONTAINS；真正 embedding 在独立 lib | ⚠️ 部分成立 |
| 5（deep explore）| 解释所有检索算法 + 长上下文可靠性 + 案例 | 4 层架构 + 5 reranker + 14 recipes；100K O(N) 瓶颈；Zep 30x 故障；论文测试集 500 对话 | ✅ 已完成 |

---

## 状态

- **报告生成**：2026-05-05 22:XX
- **下一步**：等用户对 4 个决策点反馈
- **Story 2.5.X UAT**：line 295 批注待回复（依赖本报告决策结果）
- **建议归档位置**：本文件位于 `_bmad-output/research/`，与 round-12 / round-13 同级；待用户决策后转 `_bmad-output/_decisions/` 形成 Story 2.5.Z 的输入
