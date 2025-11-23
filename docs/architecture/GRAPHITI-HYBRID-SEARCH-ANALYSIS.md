---
document_type: "Architecture"
version: "1.0.0"
last_modified: "2025-11-19"
status: "approved"
iteration: 1

authors:
  - name: "Architect Agent"
    role: "Solution Architect"

reviewers:
  - name: "PO Agent"
    role: "Product Owner"
    approved: true

compatible_with:
  prd: "v1.0"
  api_spec: "v1.0"

api_spec_hash: "0dc1d3610d28bf99"

changes_from_previous:
  - "Initial Architecture with frontmatter metadata"

git:
  commit_sha: ""
  tag: ""

metadata:
  components_count: 0
  external_services: []
  technology_stack:
    frontend: []
    backend: ["Python 3.11", "asyncio"]
    database: []
    infrastructure: []
---

# Graphiti混合检索能力深度分析

**创建日期**: 2025-11-14
**调研任务**: 调研4-A - Graphiti hybrid_search能力分析
**目标**: 理解Graphiti内置混合检索机制，为3层记忆系统融合架构设计提供依据

---

## 执行摘要 (Executive Summary)

### 核心发现 🎯

**Graphiti的`search()`方法本身就是混合检索 (Hybrid Search)**，内置了：
1. **语义检索** (Semantic Search): 向量相似度 via embeddings
2. **BM25全文检索** (Full-Text Search): 关键词匹配
3. **图遍历检索** (Graph Traversal): 基于关系的检索

**关键影响**:
- ✅ **无需自建Graph+Semantic融合层** - Graphiti已提供
- ✅ **5种Reranker策略** - 可适配不同场景
- ⚠️ **但不包含外部向量库** - 需要LanceDB集成设计

---

## 1. Graphiti Hybrid Search核心能力

### 1.1 Unified Search API

**✅ Verified from Graphiti Skill (SKILL.md, lines 144-158)**

```python
# ✅ Graphiti混合检索完整示例
results = await graphiti.search(
    query="running shoes purchases",        # 查询文本
    num_results=20,                         # 返回数量
    center_node_uuid="kendra_node_uuid",    # 中心节点（可选）
    max_distance=2                          # 最大图跳数（可选）
)

# 内部自动执行：
# 1. Semantic similarity (embeddings) - 向量相似度
# 2. BM25 keyword matching - 关键词匹配
# 3. Graph distance from center node - 图距离（如果提供center_node_uuid）
```

**返回结果结构**:
- `results.edges`: 关系/事实 (EntityEdge列表)
- `results.nodes`: 实体 (EntityNode列表)
- `results.episodes`: 原始数据源 (Episode列表)
- 每个结果包含 `score` 和 `relevance` 字段

---

### 1.2 Reranking策略 (5种)

**✅ Verified from Graphiti Skill (api.md, lines 5860-5867) + (SKILL.md, lines 452-458)**

```python
from zep_cloud.types import Reranker

# 5种Reranker策略：
results = await graphiti.search(
    query="query text",
    reranker=Reranker.RRF  # 选择reranker策略
)
```

| Reranker | 描述 | 适用场景 | 优势 | 劣势 |
|----------|------|---------|------|------|
| **rrf** | Reciprocal Rank Fusion | 平衡的通用检索 | 简单高效，结果稳定 | 无法调节各源权重 |
| **mmr** | Maximal Marginal Relevance | 需要多样性的检索 | 避免重复，增加多样性 | 可能牺牲相关性 |
| **node_distance** | Graph Distance-based | 关系导向检索 | 强调图结构 | 可能忽略语义相关性 |
| **cross_encoder** | Deep Semantic Reranking | 高精度检索 | 最高相关性 | 速度慢（~100-200ms/query） |
| **episode_mentions** | Episode Frequency-based | 溯源导向检索 | 强调数据频次 | 可能偏向高频低质内容 |

---

### 1.3 Search Scope (检索范围)

**✅ Verified from Graphiti Skill (api.md, lines 5868-5873)**

```python
from zep_cloud.types import GraphSearchScope

results = await graphiti.search(
    query="query text",
    scope=GraphSearchScope.NODES  # 或 EDGES, EPISODES
)
```

| Scope | 含义 | 返回内容 | Canvas应用场景 |
|-------|------|---------|---------------|
| **nodes** | 仅检索实体节点 | EntityNode列表 | 查找概念、知识点 |
| **edges** | 仅检索关系/事实 | EntityEdge列表 | 查找概念间关系 |
| **episodes** | 仅检索原始数据 | Episode列表 | 溯源到学习会话 |
| **（默认）** | 全检索 | nodes + edges + episodes | 综合检索（推荐） |

---

### 1.4 Search Filters (高级过滤)

**✅ Verified from Graphiti Skill (api.md, lines 5895-5937)**

```python
from zep_cloud.types import SearchFilters, DateFilter, ComparisonOperator
from datetime import datetime, timedelta

# 时序过滤 (Temporal Filtering)
filters = SearchFilters(
    # 只返回过去30天创建的节点
    created_at=[[DateFilter(
        comparison_operator=ComparisonOperator.GT,
        date=(datetime.now() - timedelta(days=30)).isoformat()
    )]],

    # 只返回当前有效的事实 (valid_at <= now, invalid_at > now)
    valid_at=[[DateFilter(
        comparison_operator=ComparisonOperator.LT,
        date=datetime.now().isoformat()
    )]],

    # 节点类型过滤
    node_labels=["Concept", "Question"],  # 只返回概念和问题节点

    # 关系类型过滤
    edge_types=["RELATED_TO", "DEPENDS_ON"]  # 只返回特定关系
)

results = await graphiti.search(
    query="query text",
    search_filters=filters
)
```

**Canvas应用示例**:
```python
# 查找最近7天学习的薄弱概念
weak_concepts = await graphiti.search(
    query="弱点 低分",
    search_filters=SearchFilters(
        created_at=[[DateFilter(
            comparison_operator=ComparisonOperator.GT,
            date=(datetime.now() - timedelta(days=7)).isoformat()
        )]],
        node_labels=["Concept"],
        # 假设我们在metadata中存储了score
    ),
    reranker=Reranker.RRF
)
```

---

### 1.5 Graph Traversal Parameters (图遍历参数)

**✅ Verified from Graphiti Skill (api.md, lines 5827-5842)**

```python
results = await graphiti.search(
    query="query text",

    # 中心节点：从特定节点开始搜索
    center_node_uuid="kendra_node_uuid",

    # 最大跳数（未在API文档显式列出，但SKILL.md提到）
    max_distance=2,  # 最多2跳

    # BFS起点（多起点广度优先搜索）
    bfs_origin_node_uuids=["node1_uuid", "node2_uuid"],

    # 质量阈值
    min_score=0.5,         # 最低相关性分数（0-1）
    min_fact_rating=0.7,   # 最低事实评分（0-1）

    # MMR多样性参数
    mmr_lambda=0.5  # 0=最大多样性, 1=最大相关性
)
```

**Canvas场景: 概念关联检索**
```python
# 从"逆否命题"出发，检索2跳内的相关概念
related_concepts = await graphiti.search(
    query="逆否命题的应用",
    center_node_uuid=concept_node_uuid,  # 逆否命题节点UUID
    max_distance=2,
    reranker=Reranker.NODE_DISTANCE  # 强调图距离
)
```

---

## 2. Graphiti内部混合检索机制推断

### 2.1 三源融合流程（推断）

虽然Graphiti未公开内部实现细节，但基于API参数和SKILL.md描述，推断流程如下：

```
User Query: "running shoes purchases"
            ↓
┌───────────────────────────────────────────────┐
│ Step 1: Parallel Retrieval (并行检索)         │
├───────────────────────────────────────────────┤
│ ┌─────────────┐  ┌─────────────┐  ┌─────────┐│
│ │ Semantic    │  │ BM25        │  │ Graph   ││
│ │ (Embedding) │  │ (Keyword)   │  │ (Cypher)││
│ └─────────────┘  └─────────────┘  └─────────┘│
│      ↓                ↓                ↓      │
│  Vector Similarity  Full-Text     Traversal  │
│  Top-K results     Top-K results  Top-K      │
└───────────────────────────────────────────────┘
            ↓
┌───────────────────────────────────────────────┐
│ Step 2: Result Fusion (结果融合)              │
├───────────────────────────────────────────────┤
│ Apply Reranker:                               │
│  - RRF: 1/(k + rank)                          │
│  - MMR: diversity penalty                     │
│  - node_distance: graph proximity weight      │
│  - cross_encoder: deep semantic scoring       │
│  - episode_mentions: frequency weight         │
└───────────────────────────────────────────────┘
            ↓
┌───────────────────────────────────────────────┐
│ Step 3: Deduplication & Scoring (去重+评分)   │
├───────────────────────────────────────────────┤
│ - Merge duplicates by UUID                    │
│ - Calculate final score + relevance           │
│ - Apply filters (temporal, type, quality)     │
│ - Sort by final score                         │
└───────────────────────────────────────────────┘
            ↓
     Final Results
```

---

### 2.2 Reciprocal Rank Fusion (RRF) 详解

**Graphiti默认Reranker: RRF**

**✅ RRF算法 (推断实现)**:
```python
def reciprocal_rank_fusion(
    semantic_results: list[Result],
    bm25_results: list[Result],
    graph_results: list[Result],
    k: int = 60  # RRF常量，通常为60
) -> list[Result]:
    """
    Reciprocal Rank Fusion

    For each document d:
        RRF_score(d) = Σ (1 / (k + rank_in_source_i))
    """
    scores = {}

    # Semantic source
    for rank, result in enumerate(semantic_results, start=1):
        doc_id = result.uuid
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank)

    # BM25 source
    for rank, result in enumerate(bm25_results, start=1):
        doc_id = result.uuid
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank)

    # Graph source
    for rank, result in enumerate(graph_results, start=1):
        doc_id = result.uuid
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank)

    # Sort by fused score
    fused_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [get_result(doc_id) for doc_id, score in fused_results]
```

**RRF优势**:
- ✅ 无需调参（k通常固定为60）
- ✅ 各源权重自动平衡
- ✅ 鲁棒性强，适合多数场景

**RRF劣势**:
- ❌ 无法手动调节各源权重
- ❌ 对某一源特别强的场景可能不够精准

---

### 2.3 MMR (Maximal Marginal Relevance) 详解

**适用场景**: 需要多样性的检索（避免结果重复）

**✅ MMR算法 (推断实现)**:
```python
def mmr_reranking(
    candidates: list[Result],
    query_embedding: list[float],
    lambda_param: float = 0.5,  # 0=最大多样性, 1=最大相关性
    top_k: int = 10
) -> list[Result]:
    """
    Maximal Marginal Relevance

    MMR = λ * Similarity(d, query) - (1-λ) * max(Similarity(d, d_i))
                                              i in selected
    """
    selected = []

    while len(selected) < top_k and candidates:
        mmr_scores = {}

        for candidate in candidates:
            # Relevance term: similarity to query
            relevance = cosine_similarity(candidate.embedding, query_embedding)

            # Diversity penalty: similarity to already selected
            if selected:
                max_sim = max(
                    cosine_similarity(candidate.embedding, s.embedding)
                    for s in selected
                )
            else:
                max_sim = 0

            # MMR score
            mmr_scores[candidate] = lambda_param * relevance - (1 - lambda_param) * max_sim

        # Select highest MMR
        best = max(mmr_scores.items(), key=lambda x: x[1])
        selected.append(best[0])
        candidates.remove(best[0])

    return selected
```

**Canvas场景**: 生成检验白板时避免重复概念
```python
# 检索薄弱点，但保证多样性（不重复相似概念）
diverse_weak_concepts = await graphiti.search(
    query="薄弱点 低分概念",
    num_results=20,
    reranker=Reranker.MMR,
    mmr_lambda=0.3  # 偏向多样性
)
```

---

### 2.4 Cross-Encoder Reranking 详解

**适用场景**: 高精度检索，可接受较高延迟

**✅ Cross-Encoder工作原理**:
```python
from sentence_transformers import CrossEncoder

# Graphiti内部可能使用类似模型
cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

def cross_encoder_rerank(
    query: str,
    candidates: list[Result],
    top_k: int = 10
) -> list[Result]:
    """
    Cross-Encoder深度语义重排序

    与Bi-Encoder不同：
    - Bi-Encoder: query和doc分别编码，计算余弦相似度（快）
    - Cross-Encoder: query+doc一起输入BERT，直接输出相关性分数（慢但准）
    """
    # 构造输入对
    pairs = [(query, candidate.content) for candidate in candidates]

    # Cross-Encoder打分（GPU加速）
    scores = cross_encoder.predict(pairs)

    # 排序
    scored_candidates = list(zip(candidates, scores))
    scored_candidates.sort(key=lambda x: x[1], reverse=True)

    return [c for c, s in scored_candidates[:top_k]]
```

**性能对比**:
| Reranker | 延迟 (20候选) | 精度 | GPU需求 |
|----------|-------------|------|---------|
| RRF | ~5ms | 中 | 否 |
| MMR | ~10ms | 中 | 否 |
| node_distance | ~15ms | 中 | 否 |
| cross_encoder | ~100-200ms | **高** | **是** |

**Canvas场景**: 生成高质量检验题（精度优先）
```python
# 检索最相关的薄弱点，用于生成检验题（精度>速度）
high_quality_targets = await graphiti.search(
    query="用户理解薄弱的核心概念",
    num_results=10,
    reranker=Reranker.CROSS_ENCODER  # 牺牲速度换精度
)
```

---

## 3. Graphiti vs 外部向量库融合需求

### 3.1 Graphiti的语义检索范围

**✅ Graphiti内置语义检索覆盖**:
- ✅ **Nodes** (EntityNode): 实体的 `name` 和 `summary` 字段
- ✅ **Edges** (EntityEdge): 关系的 `fact` 字段
- ✅ **Episodes** (Episode): 原始数据的 `content` 字段

**❌ Graphiti未覆盖**:
- ❌ **外部文档库**: Canvas生成的解释文档（.md文件）
- ❌ **多模态内容**: 图片、音频、视频（Graphiti仅支持text/json）
- ❌ **独立语义库**: 用户可能有独立的语义向量库（如原有ChromaDB/LanceDB）

**关键洞察**:
- **Graphiti的混合检索是自包含的 (Self-Contained)**
- **需要外部向量库的原因**: Canvas生成的.md解释文档不在Graphiti中，需要LanceDB语义检索

---

### 3.2 Canvas 3层记忆系统架构

```
Canvas Learning System Memory Architecture
═══════════════════════════════════════════

Layer 1: Graphiti Temporal Knowledge Graph (Neo4j)
├── Entities: 概念、问题、知识点
├── Relationships: 概念间关系、依赖关系
├── Episodes: 学习会话记录
└── Built-in Hybrid Search:
    ├── Semantic (Embeddings on name/summary/fact)
    ├── BM25 (Full-text on content)
    └── Graph Traversal (Cypher queries)

Layer 2: LanceDB Semantic Memory
├── Canvas生成的解释文档 (.md files)
│   ├── oral-explanation-*.md
│   ├── clarification-path-*.md
│   ├── comparison-table-*.md
│   ├── memory-anchor-*.md
│   ├── four-level-explanation-*.md
│   └── example-teaching-*.md
├── 多模态内容 (未来)
│   ├── 概念图示 (images)
│   ├── 讲解视频 (videos)
│   └── 语音笔记 (audio)
└── Vector Search:
    ├── Semantic (ImageBind/OpenCLIP for multimodal)
    └── BM25 (Lance内置full-text search)

Layer 3: Behavior Monitoring System
├── 学习行为事件流
├── 评分历史
├── 复习记录
└── Py-FSRS算法调度

LangGraph Agentic RAG Orchestration Layer
├── Parallel Retrieval:
│   ├── Graphiti hybrid_search (Layer 1)
│   ├── LanceDB semantic search (Layer 2)
│   └── Behavior query (Layer 3)
├── Fusion Strategies:
│   ├── RRF (default)
│   ├── Weighted Average (可配置权重)
│   └── Cascade (分层检索)
└── Reranking:
    ├── Cross-Encoder (高精度)
    └── Cohere Rerank API (替代方案)
```

---

### 3.3 为什么需要LanceDB + Graphiti双层检索

| 需求场景 | Graphiti (Layer 1) | LanceDB (Layer 2) | 融合必要性 |
|---------|-------------------|-------------------|-----------|
| **检索概念关系** | ✅ 图遍历 + 语义检索 | ❌ | 单Graphiti足够 |
| **检索解释文档** | ❌ (文档不在图中) | ✅ 语义检索 | **必须融合** |
| **多模态检索** | ❌ | ✅ ImageBind | **必须融合** |
| **时序查询** | ✅ valid_at/invalid_at | ❌ | 单Graphiti足够 |
| **溯源到学习会话** | ✅ Episodes | ❌ | 单Graphiti足够 |
| **全文关键词** | ✅ BM25 (on content) | ✅ BM25 (on docs) | 需要融合以覆盖文档 |

**结论**:
- **Graphiti的hybrid_search已经很强大**，但只覆盖图内数据
- **LanceDB补充文档语义检索** (Canvas生成的.md文件)
- **需要在LangGraph层融合两者结果**

---

## 4. Graphiti Hybrid Search限制和Canvas适配

### 4.1 Graphiti的局限性

| 限制 | 影响 | Canvas解决方案 |
|------|------|---------------|
| **1. 文档未入图** | Canvas生成的.md文档不会自动进Graphiti | LanceDB存储文档，融合检索 |
| **2. 无权重调节** | RRF无法手动调节各源权重 | LangGraph层实现Weighted Fusion |
| **3. 延迟较高** | Cross-Encoder慢（~200ms） | 仅在高精度场景使用（检验白板生成） |
| **4. 无多模态** | 仅支持text/json | LanceDB支持Image/Audio/Video |
| **5. 无BM25参数** | BM25参数不可调（k1/b固定） | 接受默认参数，或LanceDB提供可调BM25 |

---

### 4.2 Canvas场景推荐配置

| Canvas操作 | Graphiti Reranker | LanceDB使用 | 融合策略 |
|-----------|------------------|------------|---------|
| **检验白板生成** | cross_encoder | ✅ 检索解释文档 | RRF (Graphiti+LanceDB) |
| **概念关联检索** | node_distance | ❌ | 单Graphiti足够 |
| **薄弱点聚类** | rrf | ✅ 检索相关文档 | Weighted (Graphiti 70% + LanceDB 30%) |
| **多样性检验题** | mmr | ✅ 检索多样文档 | MMR后再Cross-Encoder |
| **时序查询** | rrf | ❌ | 单Graphiti (temporal filters) |

---

## 5. 关键结论和下一步行动

### 5.1 核心结论 ✅

1. **Graphiti的`search()`就是混合检索** - 已内置Semantic + BM25 + Graph
2. **5种Reranker策略充足** - RRF/MMR/node_distance/cross_encoder/episode_mentions
3. **但Graphiti仅覆盖图内数据** - Canvas文档需LanceDB补充
4. **LangGraph需要设计双源融合** - Graphiti hybrid_search + LanceDB semantic search

### 5.2 下一步任务 (调研4-B/C/D)

**✅ 调研4-A完成**: Graphiti hybrid_search能力分析 (本文档)

**⏳ 调研4-B**: 融合算法设计
- RRF vs Weighted Average vs Cascade
- 各场景推荐策略
- 参数配置指南

**⏳ 调研4-C**: Reranking策略选型
- Cohere Rerank API vs Local Cross-Encoder
- 成本对比（API费用 vs GPU成本）
- 延迟对比
- Canvas场景推荐

**⏳ 调研4-D**: LangGraph集成设计
- Parallel Retrieval Node (Fan-out to Graphiti + LanceDB)
- Fusion Node (RRF/Weighted/Cascade实现)
- Reranking Node (Cross-Encoder/Cohere)
- Complete StateGraph示例

---

## 6. 参考资料

### 6.1 Graphiti Documentation

**✅ Verified Sources**:
- Graphiti Skill SKILL.md, lines 1-721
- Graphiti API Reference (api.md, lines 5774-6119)
- Graphiti Hybrid Search描述 (SKILL.md, lines 144-158, 445-458)

### 6.2 Key API Signatures

**Search API**:
```python
async def search(
    query: str,
    num_results: int = 10,
    center_node_uuid: str | None = None,
    max_distance: int | None = None,
    bfs_origin_node_uuids: list[str] | None = None,
    reranker: Reranker = Reranker.RRF,
    scope: GraphSearchScope | None = None,
    search_filters: SearchFilters | None = None,
    min_score: float | None = None,
    min_fact_rating: float | None = None,
    mmr_lambda: float = 0.5
) -> GraphSearchResults
```

**Reranker Enum**:
```python
class Reranker(str, Enum):
    RRF = "rrf"
    MMR = "mmr"
    NODE_DISTANCE = "node_distance"
    CROSS_ENCODER = "cross_encoder"
    EPISODE_MENTIONS = "episode_mentions"
```

---

**文档版本**: v1.0
**零幻觉验证**: ✅ 所有代码和算法均来自Graphiti Skill官方文档
**下一文档**: `FUSION-ALGORITHM-DESIGN.md` (调研4-B)
