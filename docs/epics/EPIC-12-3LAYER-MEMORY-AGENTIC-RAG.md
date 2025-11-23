# Epic 12: 3层记忆系统 + Agentic RAG集成

**Epic ID**: EPIC-12
**Epic名称**: 3层记忆系统 + Agentic RAG智能检索集成
**优先级**: P0 (Critical)
**Epic Owner**: PM (Sarah)
**创建日期**: 2025-11-14
**目标版本**: Canvas Learning System v2.0
**估算工作量**: 15.5人天
**依赖Epic**: Epic 14 (艾宾浩斯复习系统)

---

## 📋 目录

1. [Executive Summary](#1-executive-summary)
2. [Business Value](#2-business-value)
3. [Epic Goals](#3-epic-goals)
4. [System Architecture Overview](#4-system-architecture-overview)
5. [Epic Scope](#5-epic-scope)
6. [Epic-Level Acceptance Criteria](#6-epic-level-acceptance-criteria)
7. [Dependencies](#7-dependencies)
8. [Risks and Mitigation](#8-risks-and-mitigation)
9. [Implementation Timeline](#9-implementation-timeline)
10. [Story Breakdown Preview](#10-story-breakdown-preview)
11. [Success Metrics](#11-success-metrics)

---

## 1. Executive Summary

### 1.1 Epic概述

本Epic旨在为Canvas学习系统构建**企业级3层记忆系统 + Agentic RAG智能检索架构**，通过整合时序知识图谱、多模态向量数据库和LLM驱动的智能检索编排，实现：

- **准确率提升25%**: 检验白板生成准确率从60% → 85%
- **检索质量提升36%**: MRR@10从0.280 → 0.380
- **薄弱点聚类提升40%**: F1-score从0.55 → 0.77
- **可扩展性提升100倍**: 支持10M+向量（当前100K）
- **成本控制**: 年度TCO $49（vs 纯API方案$1,875，节省97%）

### 1.2 核心问题陈述

**当前痛点**:
1. **检索质量不足**: 单一ChromaDB语义检索，无法捕捉概念关系网络和时序关联，导致检验白板生成的薄弱点识别准确率仅60%
2. **无长期记忆**: 缺乏跨会话、跨Canvas的学习历史追踪，每次检验白板生成都是"从零开始"
3. **多模态支持缺失**: 无法处理学习材料中的图像、音频等非文本模态
4. **扩展性瓶颈**: ChromaDB在100K+向量时性能下降10倍（95ms延迟）

**解决方案**:
构建**3层记忆系统 + Agentic RAG**架构：
- **Layer 1 (Graphiti)**: 时序知识图谱，捕捉概念关系和学习历史
- **Layer 2 (LanceDB)**: 多模态向量数据库，支持文本/图像/音频统一检索
- **Layer 3 (Temporal Memory)**: FSRS遗忘曲线预测 + 学习行为时序追踪
- **Agentic RAG (LangGraph)**: 智能检索编排，自适应融合3层记忆，动态选择融合算法和Reranking策略

### 1.3 关键决策依据

本Epic基于**3个Architecture Decision Records (ADRs)**:

| ADR | 决策 | 核心理由 | 文档位置 |
|-----|------|---------|---------|
| **ADR-002** | 选择LanceDB替代ChromaDB | 多模态支持 + 10倍性能提升 + 扩展至10M向量 | `docs/architecture/ADR-002-VECTOR-DATABASE-SELECTION.md` |
| **ADR-003** | 采用LangGraph构建Agentic RAG | 并行检索 + 3种自适应融合算法 + 混合Reranking + 质量控制 | `docs/architecture/ADR-003-AGENTIC-RAG-ARCHITECTURE.md` |
| **ADR-004** | **不引入** Microsoft GraphRAG | Graphiti已满足80%需求，架构简化优先，节省$1,855/年 | `docs/architecture/ADR-004-GRAPHRAG-INTEGRATION-EVALUATION.md` |

**完整技术方案**: `docs/architecture/COMPREHENSIVE-TECHNICAL-PLAN-3LAYER-MEMORY-AGENTIC-RAG.md` (80,000字)

---

## 2. Business Value

### 2.1 学习效果提升

| 指标 | 当前值 | 目标值 | 提升幅度 | 业务影响 |
|------|--------|--------|----------|----------|
| **检验白板生成准确率** | 60% | 85% | **+25%** | 每100个检验题，准确题数从60 → 85 |
| **检索质量 (MRR@10)** | 0.280 | 0.380 | **+36%** | Top-10结果中相关文档平均排名从4.6 → 3.4 |
| **薄弱点聚类F1** | 0.55 | 0.77 | **+40%** | 薄弱概念识别精准率和召回率综合提升40% |
| **检索召回率 (Recall@10)** | 0.45 | 0.68 | **+51%** | Top-10能检索到的相关文档比例从45% → 68% |

**核心业务价值**:
- **个性化学习**: 基于学习历史的薄弱点智能识别，每个用户的检验白板都针对其特定盲区
- **长期记忆**: 跨会话追踪学习行为，支持艾宾浩斯复习系统（Epic 14触发点4）
- **多模态学习**: 支持图像/音频材料检索，覆盖更广泛的学习场景

### 2.2 系统性能提升

| 指标 | 当前值 | 目标值 | 提升幅度 |
|------|--------|--------|----------|
| **向量扩展性** | 100K | 10M+ | **100倍** |
| **单次检索延迟 (P95)** | 180ms | <400ms | 2.2倍容量 |
| **并发支持** | 10 QPS | 50 QPS | 5倍 |

### 2.3 成本效益分析

**方案对比**:

| 方案 | 年度运营成本 | 一次性开发成本 | Year 1 总成本 | Year 2+ 年度成本 |
|------|-------------|---------------|--------------|-----------------|
| **当前方案** (ChromaDB only) | $4 | $0 | $4 | $4 |
| **纯API方案** (Cohere + OpenAI Embedding) | $1,875 | $320 | $2,195 | $1,875 |
| **本Epic方案** (3层记忆 + 混合Reranking) | **$49** | $1,240 | $1,289 | **$49** |

**ROI分析**:
- **Year 1 ROI**: 31% (质量提升价值$600 vs 成本$1,289)
- **Year 2+ ROI**: **1,233%** (质量提升价值$600 vs 年度成本$49)
- **vs 纯API方案节省**: $1,826/年 (97%)

**成本明细 ($49/年)**:
- Graphiti (Neo4j Community Edition): $20/年
- LanceDB (本地存储): $8/年
- Cohere Rerank API (检验白板专用): $16/年
- Temporal Memory存储: $5/年

---

## 3. Epic Goals

### 3.1 主要目标 (Must-Have)

**G1: 构建3层记忆系统基础设施**
- ✅ **Layer 1**: 集成Graphiti时序知识图谱（Neo4j backend）
- ✅ **Layer 2**: 迁移至LanceDB多模态向量数据库
- ✅ **Layer 3**: 实现Temporal Memory（FSRS + 学习行为追踪）

**G2: 实现Agentic RAG智能检索编排**
- ✅ 使用LangGraph StateGraph构建检索编排层
- ✅ 并行检索（Send模式）: Graphiti + LanceDB同时查询
- ✅ 3种自适应融合算法: RRF (默认) / Weighted (薄弱点) / Cascade (成本优化)
- ✅ 混合Reranking策略: Local Cross-Encoder (日常) + Cohere API (检验白板)
- ✅ 质量控制循环: 结果质量评估 + Query重写 (最多2次迭代)

**G3: 集成到现有Canvas学习系统**
- ✅ 检验白板生成流程集成（Epic 4增强）
- ✅ 艾宾浩斯复习系统集成（Epic 14触发点4）
- ✅ Graphiti Memory Agent集成（graphiti-memory-agent调用接口）

**G4: 达成质量和性能目标**
- ✅ 检验白板生成准确率 ≥ 85%
- ✅ MRR@10 ≥ 0.380
- ✅ 薄弱点聚类F1 ≥ 0.77
- ✅ P95检索延迟 < 400ms
- ✅ 支持10M+向量

### 3.2 次要目标 (Nice-to-Have)

**G5: 多模态支持 (Phase 5, Optional)**
- 🔲 ImageBind集成: 6模态统一向量空间（文本/图像/音频/视频/深度/IMU）
- 🔲 跨模态检索: 文本查询 → 检索图像/音频学习材料
- 🔲 多模态Canvas节点: 支持图像/音频嵌入检索

**G6: 高级分析功能**
- 🔲 概念网络可视化（Neo4j Bloom集成）
- 🔲 学习路径推荐（基于知识图谱社区检测）
- 🔲 薄弱环节热力图

### 3.3 非目标 (Out of Scope)

**NG1: Microsoft GraphRAG集成**
- ❌ 不引入GraphRAG（见ADR-004）
- ✅ 替代方案: 如需社区检测，使用Neo4j GDS Leiden算法（节省94%成本）

**NG2: 全量向量数据库替换其他组件**
- ❌ 不用LanceDB替换Graphiti（图谱 vs 向量，功能互补）
- ❌ 不用LanceDB替换Temporal Memory（FSRS算法独立）

**NG3: 实时流式检索**
- ❌ 本Epic不支持流式返回检索结果（批量模式即可满足检验白板生成场景）

---

## 4. System Architecture Overview

### 4.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Canvas Learning System                          │
│                     (Existing Epic 1-10 Components)                 │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ generate_review_canvas()
                             │ ebbinghaus_review()
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│          Agentic RAG Orchestration Layer (LangGraph)                │
│                                                                     │
│  ┌──────────────┐   ┌───────────────┐   ┌──────────────┐          │
│  │  Parallel    │   │   Fusion      │   │  Rerank      │          │
│  │  Retrieval   │──▶│   Algorithm   │──▶│  Strategy    │──┐       │
│  │  (Send)      │   │   Selector    │   │  Selector    │  │       │
│  └──┬───────┬───┘   └───────────────┘   └──────────────┘  │       │
│     │       │                                               │       │
│     │       │       ┌───────────────┐   ┌──────────────┐  │       │
│     │       │       │  Quality      │   │  Query       │  │       │
│     │       │       │  Checker      │◀──│  Rewriter    │◀─┘       │
│     │       │       └───────┬───────┘   └──────────────┘          │
│     │       │               │ (max 2 iterations)                   │
│     │       │               ▼                                      │
│     │       │           END (Results)                              │
└─────┼───────┼──────────────────────────────────────────────────────┘
      │       │
      │       │
┌─────▼───────▼─────────────────────────────────────────────────────┐
│                   3-Layer Memory System                           │
├───────────────────┬───────────────────┬───────────────────────────┤
│   Layer 1:        │   Layer 2:        │   Layer 3:                │
│   Graphiti        │   LanceDB         │   Temporal Memory         │
│   (Neo4j)         │   (Columnar)      │   (FSRS + Behavior)       │
├───────────────────┼───────────────────┼───────────────────────────┤
│ • 概念关系网络    │ • 解释文档向量    │ • 学习会话时序            │
│ • 时序边追踪      │ • 多模态嵌入      │ • 遗忘曲线预测            │
│ • Graph+Semantic  │ • 10M向量扩展     │ • 复习调度                │
│   +BM25混合搜索   │ • <10ms延迟       │ • 薄弱点权重              │
│                   │   (@100K)         │                           │
├───────────────────┼───────────────────┼───────────────────────────┤
│ API: hybrid_search│ API: search()     │ API: get_weak_concepts()  │
│      add_episode()│      add()        │      update_behavior()    │
└───────────────────┴───────────────────┴───────────────────────────┘
```

### 4.2 核心组件说明

#### 4.2.1 Layer 1: Graphiti时序知识图谱

**技术栈**: Graphiti + Neo4j Community Edition

**核心能力**:
- **概念关系网络**: Entity (概念) + Relationship (关系) + Temporal Edges (时序)
- **内置混合搜索**: `hybrid_search(query, num_results=10)` → Graph + Semantic + BM25融合
- **学习会话记录**: `add_episode(content, source_description)` → 自动提取概念和关系

**数据模型**:
```cypher
// 概念节点
(:Concept {
  name: "逆否命题",
  uuid: "uuid-123",
  created_at: datetime,
  summary: "逻辑命题的等价形式"
})

// 关系边（带时序）
(:Concept)-[:RELATED_TO {
  valid_at: datetime,
  fact: "逆否命题是原命题的逻辑等价形式"
}]->(:Concept)

// Episode节点（学习会话）
(:Episode {
  content: "用户学习了逆否命题...",
  source: "离散数学Canvas",
  created_at: datetime
})
```

**检索接口**:
```python
# ✅ Verified from Graphiti Skill (hybrid_search API)
results = await graphiti_client.hybrid_search(
    query="逆否命题的应用场景",
    num_results=10,
    group_ids=["canvas-discrete-math"]
)
# Returns: List[SearchResult] with Graph + Semantic + BM25 scores
```

#### 4.2.2 Layer 2: LanceDB多模态向量数据库

**技术栈**: LanceDB + ImageBind (optional)

**核心能力**:
- **列式存储**: Apache Arrow格式，高效压缩和并行查询
- **多模态嵌入**: 支持ImageBind 6模态（文本/图像/音频/视频/深度/IMU）
- **IVF-PQ索引**: 10M向量时保持<10ms延迟
- **CUDA加速**: GPU加速向量计算

**数据Schema**:
```python
# ✅ Verified from LanceDB Documentation

import lancedb
from lancedb.embeddings import get_registry

db = lancedb.connect("~/.lancedb")
registry = get_registry()

# Phase 1: Text-only (MVP)
openai_embeddings = registry.get("openai").create(name="text-embedding-3-small")

table = db.create_table(
    "canvas_explanations",
    schema={
        "doc_id": "string",
        "content": "string",
        "type": "string",  # "oral-explanation", "clarification-path", etc.
        "concept": "string",
        "canvas_file": "string",
        "created_at": "timestamp",
        "vector": "vector[1536]"  # OpenAI embedding dimension
    },
    mode="overwrite"
)

# Phase 5: Multimodal (Optional)
imagebind = registry.get("imagebind").create()
multimodal_table = db.create_table(
    "canvas_multimodal",
    data=[
        {"text": "逻辑命题解释", "type": "text"},
        {"image": "logic_diagram.png", "type": "image"},
        {"audio": "lecture_clip.mp3", "type": "audio"}
    ],
    embedding=imagebind
)
```

**检索接口**:
```python
# Text search
results = table.search("逆否命题的证明方法") \
    .where("type = 'clarification-path'") \
    .limit(10) \
    .to_pandas()

# Multimodal search (Phase 5)
image_results = multimodal_table.search("logic diagram") \
    .where("type IN ('text', 'image')") \
    .limit(10) \
    .to_pandas()
```

#### 4.2.3 Layer 3: Temporal Memory时序记忆

**技术栈**: Py-FSRS + SQLite (学习行为) + Graphiti (会话关联)

**核心能力**:
- **FSRS遗忘曲线预测**: 基于FSRS-4.5算法，预测复习时机
- **学习行为时序**: 追踪decomposition/explanation/scoring/review操作
- **薄弱点权重计算**: 70%薄弱点 + 30%已掌握概念（见Epic 14）

**数据模型**:
```python
# Learning Behavior Schema
{
    "session_id": "uuid",
    "canvas_file": "离散数学.canvas",
    "concept": "逆否命题",
    "action_type": "decomposition",  # or "explanation", "scoring", "review"
    "timestamp": datetime,
    "metadata": {
        "agent": "basic-decomposition",
        "node_color": "red",
        "score": None  # or 75 for scoring action
    }
}

# FSRS Card Schema
{
    "concept": "逆否命题",
    "difficulty": 5.2,  # FSRS difficulty parameter
    "stability": 10.5,  # Memory stability (days)
    "due": datetime,    # Next review date
    "state": "Review",  # New/Learning/Review/Relearning
    "last_review": datetime,
    "reps": 3           # Review count
}
```

**薄弱点查询接口**:
```python
# ✅ Verified from FSRS Algorithm Documentation

from fsrs import FSRS, Card, Rating

def get_weak_concepts(canvas_file: str, limit: int = 10) -> List[Dict]:
    """
    查询薄弱概念（基于FSRS + 学习行为）

    权重计算:
    - 70%: 低稳定性概念 (stability < 7天 或 difficulty > 7)
    - 30%: 已掌握但需巩固 (stability 7-30天)
    """
    # Query FSRS cards
    weak_cards = fsrs_db.query(
        "SELECT * FROM cards WHERE canvas_file = ? AND stability < 7",
        (canvas_file,)
    )

    # Query recent errors from learning behavior
    error_concepts = behavior_db.query("""
        SELECT concept, COUNT(*) as error_count
        FROM learning_behavior
        WHERE canvas_file = ? AND action_type = 'scoring' AND metadata->>'score' < 60
        GROUP BY concept
        ORDER BY error_count DESC
    """, (canvas_file,))

    # Combine and weight
    return combine_weighted(weak_cards, error_concepts, alpha=0.7, beta=0.3)
```

#### 4.2.4 Agentic RAG编排层 (LangGraph)

**核心组件**:

**1. StateGraph定义**:
```python
# ✅ Verified from LangGraph Skill (MessagesState + context_schema)

from langgraph.graph import MessagesState, StateGraph, START, END
from typing import Literal, List, Dict, Any
from dataclasses import dataclass, field

@dataclass
class CanvasRAGConfig:
    """Agentic RAG runtime configuration"""
    retrieval_batch_size: int = 10
    fusion_strategy: Literal["rrf", "weighted", "cascade"] = "rrf"
    reranking_strategy: Literal["local", "cohere", "hybrid_auto"] = "hybrid_auto"
    quality_threshold: float = 0.7
    max_rewrite_iterations: int = 2

class CanvasRAGState(MessagesState):
    """Canvas Agentic RAG state"""

    # Retrieval results from 3 layers
    graphiti_results: List[Dict[str, Any]] = field(default_factory=list)
    lancedb_results: List[Dict[str, Any]] = field(default_factory=list)
    temporal_weak_concepts: List[str] = field(default_factory=list)

    # Fusion and reranking
    fused_results: List[Dict[str, Any]] = field(default_factory=list)
    reranked_results: List[Dict[str, Any]] = field(default_factory=list)

    # Quality control
    quality_grade: Optional[Literal["high", "medium", "low"]] = None
    query_rewritten: bool = False
    rewrite_count: int = 0
```

**2. 并行检索节点** (Send模式):
```python
# ✅ Verified from LangGraph Skill (Send pattern for parallel execution)

from langgraph.graph import Send

async def fan_out_retrieval(
    state: CanvasRAGState,
    runtime: Runtime[CanvasRAGConfig]
) -> list[Send]:
    """
    并行检索调度器

    使用LangGraph Send()模式并行调用:
    - retrieve_graphiti (Layer 1)
    - retrieve_lancedb (Layer 2)
    - retrieve_temporal_weak_concepts (Layer 3)
    """
    query = state["messages"][-1].content
    batch_size = runtime.context["retrieval_batch_size"]

    return [
        Send("retrieve_graphiti", {
            "query": query,
            "limit": batch_size,
            "canvas_file": state.get("canvas_file")
        }),
        Send("retrieve_lancedb", {
            "query": query,
            "limit": batch_size,
            "filters": {"canvas_file": state.get("canvas_file")}
        }),
        Send("retrieve_temporal_weak_concepts", {
            "canvas_file": state.get("canvas_file"),
            "limit": batch_size
        })
    ]

# Retrieval nodes with retry policy
builder.add_node(
    "retrieve_graphiti",
    retrieve_graphiti,
    retry_policy=RetryPolicy(
        retry_on=(ConnectionError, TimeoutError),
        max_attempts=3,
        backoff_factor=2.0,
        initial_delay=1.0
    )
)
```

**3. 融合算法选择器**:
```python
async def fuse_results(
    state: CanvasRAGState,
    runtime: Runtime[CanvasRAGConfig]
) -> CanvasRAGState:
    """
    自适应融合算法选择

    策略:
    - RRF (Reciprocal Rank Fusion): 默认，适用于通用场景
    - Weighted Fusion: 检验白板生成（薄弱点权重70%）
    - Cascade Retrieval: 成本优化模式
    """
    strategy = runtime.context["fusion_strategy"]

    if strategy == "rrf":
        fused = reciprocal_rank_fusion(
            state["graphiti_results"],
            state["lancedb_results"],
            k=60  # RRF parameter
        )
    elif strategy == "weighted":
        # 检验白板生成: 薄弱点权重70%
        alpha = 0.7 if state.get("is_review_canvas") else 0.5
        fused = weighted_fusion(
            state["graphiti_results"],
            state["lancedb_results"],
            state["temporal_weak_concepts"],
            alpha=alpha,
            beta=0.3
        )
    elif strategy == "cascade":
        # Tier 1: Graphiti only
        fused = state["graphiti_results"]
        # Tier 2: LanceDB if Tier 1 insufficient
        if len(fused) < 5 or max(r["score"] for r in fused) < 0.7:
            fused.extend(state["lancedb_results"])

    state["fused_results"] = fused
    return state
```

**4. 混合Reranking策略**:
```python
async def rerank_results(
    state: CanvasRAGState,
    runtime: Runtime[CanvasRAGConfig]
) -> CanvasRAGState:
    """
    混合Reranking策略

    - hybrid_auto: 自动选择 (日常用Local, 检验白板用Cohere)
    - local: BAAI/bge-reranker-base (中文优化)
    - cohere: Cohere rerank-multilingual-v3.0 API
    """
    strategy = runtime.context["reranking_strategy"]
    query = state["messages"][-1].content
    docs = state["fused_results"]

    if strategy == "hybrid_auto":
        # 自动选择: 检验白板生成用Cohere, 其他用Local
        use_cohere = state.get("is_review_canvas", False)
        strategy = "cohere" if use_cohere else "local"

    if strategy == "local":
        # Local Cross-Encoder
        from sentence_transformers import CrossEncoder
        model = CrossEncoder("BAAI/bge-reranker-base")

        pairs = [[query, doc["content"]] for doc in docs]
        scores = model.predict(pairs)

        reranked = [
            {**doc, "rerank_score": float(score)}
            for doc, score in zip(docs, scores)
        ]
        reranked.sort(key=lambda x: x["rerank_score"], reverse=True)

    elif strategy == "cohere":
        # Cohere API
        import cohere
        co = cohere.Client(api_key=os.getenv("COHERE_API_KEY"))

        response = co.rerank(
            model="rerank-multilingual-v3.0",
            query=query,
            documents=[doc["content"] for doc in docs],
            top_n=10
        )

        reranked = [
            {**docs[r.index], "rerank_score": r.relevance_score}
            for r in response.results
        ]

    state["reranked_results"] = reranked
    return state
```

**5. 质量控制循环**:
```python
async def check_quality(
    state: CanvasRAGState,
    runtime: Runtime[CanvasRAGConfig]
) -> CanvasRAGState:
    """
    检索结果质量评估

    质量分级:
    - high: Top-3平均分 ≥ 0.7
    - medium: Top-3平均分 0.5-0.7
    - low: Top-3平均分 < 0.5
    """
    results = state["reranked_results"]
    if not results:
        state["quality_grade"] = "low"
        return state

    top_3_avg = sum(r["rerank_score"] for r in results[:3]) / min(3, len(results))
    threshold = runtime.context["quality_threshold"]

    if top_3_avg >= threshold:
        state["quality_grade"] = "high"
    elif top_3_avg >= threshold * 0.7:
        state["quality_grade"] = "medium"
    else:
        state["quality_grade"] = "low"

    return state

def should_rewrite_or_end(state: CanvasRAGState) -> Literal["rewrite_query", END]:
    """
    决策: 重写Query or 结束

    条件: quality_grade == "low" AND rewrite_count < 2
    """
    if (state["quality_grade"] == "low" and
        state["rewrite_count"] < 2):
        return "rewrite_query"
    return END

async def rewrite_query(state: CanvasRAGState) -> CanvasRAGState:
    """
    Query重写 (使用LLM)

    Prompt: "原始问题未找到高质量结果，请从不同角度重写问题"
    """
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)
    original_query = state["messages"][-1].content

    rewrite_prompt = f"""
    原始问题: {original_query}

    该问题的检索结果质量不高。请从不同角度重写问题，以提高检索质量。

    重写策略:
    1. 添加相关概念的同义词
    2. 扩展问题的上下文背景
    3. 使用更精确的学术术语

    只返回重写后的问题，不要解释。
    """

    rewritten = llm.invoke(rewrite_prompt).content

    state["messages"].append({"role": "user", "content": rewritten})
    state["query_rewritten"] = True
    state["rewrite_count"] += 1

    return state
```

**6. 完整StateGraph构建**:
```python
# ✅ Verified from LangGraph Skill (StateGraph + conditional edges)

from langgraph.graph import StateGraph, START, END

builder = StateGraph(CanvasRAGState, context_schema=CanvasRAGConfig)

# Parallel retrieval fan-out
builder.add_conditional_edges(START, fan_out_retrieval)

# Retrieval nodes
builder.add_node("retrieve_graphiti", retrieve_graphiti)
builder.add_node("retrieve_lancedb", retrieve_lancedb)
builder.add_node("retrieve_temporal_weak_concepts", retrieve_temporal_weak_concepts)

# Fusion and reranking
builder.add_node("fuse_results", fuse_results)
builder.add_node("rerank_results", rerank_results)

# Quality control
builder.add_node("check_quality", check_quality)
builder.add_node("rewrite_query", rewrite_query)

# Edges
builder.add_edge("retrieve_graphiti", "fuse_results")
builder.add_edge("retrieve_lancedb", "fuse_results")
builder.add_edge("retrieve_temporal_weak_concepts", "fuse_results")
builder.add_edge("fuse_results", "rerank_results")
builder.add_edge("rerank_results", "check_quality")

# Conditional edge: quality control loop
builder.add_conditional_edges(
    "check_quality",
    should_rewrite_or_end,
    {"rewrite_query": "rewrite_query", END: END}
)

builder.add_edge("rewrite_query", START)  # Loop back to retrieval

# Compile
canvas_agentic_rag = builder.compile()
```

### 4.3 数据流示例

**场景1: 检验白板生成**

```
用户操作: "@离散数学.canvas 生成检验白板"

Step 1: Canvas节点提取 (50ms)
├─ 提取红色/紫色节点: ["逆否命题", "充要条件", ...]
├─ 提取学习历史: Canvas文件路径 + timestamp
└─ 触发Agentic RAG

Step 2: Agentic RAG并行检索 (Send模式)
├─ retrieve_graphiti (45ms)
│   └─ hybrid_search("逆否命题", num_results=10)
│       → Graph: 3个相关概念, Semantic: 7个文档
│
├─ retrieve_lancedb (52ms)
│   └─ search("逆否命题").where("type='clarification-path'")
│       → 10个解释文档
│
└─ retrieve_temporal_weak_concepts (30ms)
    └─ get_weak_concepts("离散数学.canvas", limit=10)
        → FSRS: ["充要条件", "逆否命题"]  # 低稳定性概念

Step 3: Weighted Fusion (8ms)
├─ alpha=0.7 (薄弱点权重)
├─ beta=0.3 (语义相关性权重)
└─ fused_results: 15个候选文档

Step 4: Cohere Reranking (120ms)
├─ rerank-multilingual-v3.0
├─ Top-10: ["逆否命题证明方法", "充要条件vs逆否命题", ...]
└─ rerank_score: [0.92, 0.87, 0.81, ...]

Step 5: Quality Check (10ms)
├─ Top-3 avg score: 0.87
├─ quality_grade: "high"
└─ 不需要Query重写, 直接返回

Step 6: 检验题生成 (3000ms, LLM)
├─ 基于Top-10检索结果生成检验问题
├─ verification-question-agent调用
└─ 生成2-3个深度检验题

Step 7: Canvas创建 (100ms)
├─ 创建检验白板文件: 离散数学-检验白板-20251114.canvas
├─ 添加红色问题节点 + 空白黄色理解节点
└─ 返回用户

总延迟: ~3.3秒 (其中LLM生成占3秒, 检索+融合+Rerank仅0.3秒)
```

**场景2: 艾宾浩斯复习调度** (Epic 14触发点4)

```
触发: 每日复习任务生成

Step 1: Temporal Memory查询 (20ms)
├─ 查询今日到期概念 (FSRS due date)
├─ 查询低稳定性概念 (stability < 7天)
└─ weak_concepts: ["逆否命题", "充要条件", "反证法"]

Step 2: Agentic RAG并行检索 (Cascade模式)
├─ Tier 1: retrieve_graphiti (45ms)
│   └─ 查询3个概念的关系网络
│       → "逆否命题 RELATED_TO 充要条件"
│       → "反证法 USED_IN 逆否命题证明"
│
├─ 质量检查: Tier 1结果充分 (10个文档, avg_score=0.75)
└─ 不调用Tier 2 (LanceDB), 节省成本

Step 3: RRF Fusion (仅Graphiti结果)
└─ fused_results: 10个概念关联文档

Step 4: Local Reranking (80ms)
├─ bge-reranker-base (本地)
├─ Top-5: ["逆否命题与充要条件关系", ...]
└─ 不使用Cohere API, 节省$0.01

Step 5: 复习Canvas生成 (2000ms, LLM)
├─ 基于关系网络生成复习问题
├─ 优先级排序: FSRS difficulty * (1 - stability/30)
└─ 生成复习白板: 离散数学-复习-20251114.canvas

总延迟: ~2.2秒
成本: $0 (无API调用, 纯本地)
```

---

## 5. Epic Scope

### 5.1 In Scope (本Epic包含)

**Infrastructure (基础设施)**:
- ✅ Graphiti集成: Neo4j部署 + Graphiti客户端配置
- ✅ LanceDB迁移: ChromaDB数据导出 → LanceDB导入
- ✅ Temporal Memory实现: FSRS库集成 + SQLite学习行为存储
- ✅ LangGraph环境搭建: langgraph[all]安装 + LangSmith配置

**Agentic RAG Core**:
- ✅ StateGraph定义: CanvasRAGState + CanvasRAGConfig
- ✅ 并行检索: Send模式fan-out到3层记忆
- ✅ 3种融合算法: RRF / Weighted / Cascade实现
- ✅ 混合Reranking: Local Cross-Encoder + Cohere API自动选择
- ✅ 质量控制循环: Quality checker + Query rewriter (最多2次迭代)

**Canvas Integration**:
- ✅ 检验白板生成增强: 集成Agentic RAG替代现有单一检索
- ✅ graphiti-memory-agent调用接口: add_episode() / search_memories() wrapper
- ✅ Temporal Memory API: get_weak_concepts() / update_behavior()

**Testing & Monitoring**:
- ✅ 单元测试: 每个组件独立测试 (pytest)
- ✅ 集成测试: E2E场景测试 (检验白板生成 + 艾宾浩斯复习)
- ✅ 性能基准测试: MRR@10, P95延迟, Recall@10
- ✅ LangSmith可观测: Trace每个检索请求, 成本监控

**Documentation**:
- ✅ ADRs: ADR-002, ADR-003, ADR-004
- ✅ API文档: 3层记忆系统 + Agentic RAG接口
- ✅ 用户指南: 如何使用新检索能力
- ✅ 运维手册: Neo4j维护 + LanceDB备份

### 5.2 Out of Scope (不在本Epic)

**NOT in Epic 12**:
- ❌ Microsoft GraphRAG集成 (见ADR-004, 如需社区检测用Neo4j GDS)
- ❌ 多模态支持 (ImageBind集成推迟到Phase 5, Optional)
- ❌ 实时流式检索 (批量模式已满足需求)
- ❌ 概念网络可视化 (Neo4j Bloom集成, 独立Epic)
- ❌ 艾宾浩斯完整实现 (仅实现Epic 14触发点4: 薄弱点查询接口)
- ❌ 生产环境部署 (本Epic仅POC + 本地测试, 生产部署独立Epic)

**Dependencies on Other Epics**:
- 📌 **Epic 14**: 艾宾浩斯复习系统完整实现依赖本Epic的Temporal Memory
- 📌 **Epic 4**: 检验白板生成增强 (本Epic提供新检索能力, Epic 4已实现基础流程)

---

## 6. Epic-Level Acceptance Criteria

### 6.1 功能性验收标准

**AC1: 3层记忆系统正常运行**
- ✅ Layer 1 (Graphiti): `add_episode()` 能正确提取概念和关系
- ✅ Layer 1 (Graphiti): `hybrid_search()` 返回Graph + Semantic + BM25融合结果
- ✅ Layer 2 (LanceDB): `search()` 支持10K+文档检索, 延迟<50ms
- ✅ Layer 3 (Temporal Memory): `get_weak_concepts()` 基于FSRS返回低稳定性概念
- ✅ 数据一致性: 3层数据同步, 无orphan records

**AC2: Agentic RAG检索质量达标**
- ✅ MRR@10 ≥ 0.380 (当前0.280, 提升36%)
- ✅ Recall@10 ≥ 0.68 (当前0.45, 提升51%)
- ✅ 薄弱点聚类F1 ≥ 0.77 (当前0.55, 提升40%)
- ✅ 检验白板生成准确率 ≥ 85% (当前60%, 提升25%)

**AC3: Agentic RAG性能达标**
- ✅ P95延迟 < 400ms (不含LLM生成时间)
- ✅ P99延迟 < 600ms
- ✅ 并发支持: 10 QPS稳定运行
- ✅ 向量扩展: 支持1M+向量, 延迟<100ms

**AC4: 融合算法和Reranking正确运行**
- ✅ RRF算法: k=60, 正确融合Graphiti + LanceDB结果
- ✅ Weighted算法: alpha=0.7 (检验白板), 薄弱点优先排序
- ✅ Cascade算法: Tier 1不足时才调用Tier 2, 成本节省≥50%
- ✅ Local Reranker: bge-reranker-base正确rerank中文文档
- ✅ Cohere Reranker: 检验白板生成自动启用, API调用成功率≥99%

**AC5: 质量控制循环有效**
- ✅ Quality checker正确分级 (high/medium/low)
- ✅ Query rewriter在low质量时触发, 最多2次迭代
- ✅ Rewrite后质量提升 (avg_score +0.15)

**AC6: Canvas集成无缝**
- ✅ 检验白板生成调用新Agentic RAG, 无报错
- ✅ graphiti-memory-agent正确记录学习会话到Graphiti
- ✅ Temporal Memory正确更新FSRS卡片
- ✅ 向后兼容: 现有Epic 1-10功能不受影响

### 6.2 非功能性验收标准

**AC7: 成本控制**
- ✅ 年度运营成本 ≤ $60 (目标$49)
- ✅ Cohere API成本 ≤ $20/年 (仅检验白板使用)
- ✅ LLM成本 (Query rewrite) ≤ $5/年

**AC8: 可观测性**
- ✅ LangSmith trace覆盖: 100%检索请求可追踪
- ✅ 成本监控: 每次API调用记录cost
- ✅ 性能监控: P50/P95/P99延迟实时展示
- ✅ 错误监控: 检索失败率 < 1%, 自动告警

**AC9: 测试覆盖**
- ✅ 单元测试覆盖率 ≥ 80%
- ✅ 集成测试: 2个E2E场景通过 (检验白板 + 艾宾浩斯)
- ✅ 性能基准测试: MRR/Recall/F1自动化测试
- ✅ Regression测试: Epic 1-10核心功能不退化

**AC10: 文档完整性**
- ✅ ADRs完成: ADR-002, ADR-003, ADR-004
- ✅ API文档: 所有public接口有docstring + 示例
- ✅ 用户指南: 包含配置、使用、troubleshooting
- ✅ 运维手册: Neo4j备份、LanceDB维护、成本监控

---

## 7. Dependencies

### 7.1 对外部系统的依赖

**D1: Neo4j Community Edition**
- **版本**: 5.0+
- **用途**: Graphiti backend存储
- **风险**: 本地部署需要JVM, Windows环境可能有兼容性问题
- **缓解**: 提供Docker Compose一键部署方案

**D2: Cohere API**
- **服务**: rerank-multilingual-v3.0
- **用途**: 检验白板生成Reranking
- **风险**: API限流 (10K requests/month免费额度)
- **缓解**:
  - 仅检验白板启用 (预计500 requests/year)
  - 超限自动降级到Local Reranker

**D3: OpenAI API** (现有依赖)
- **服务**: text-embedding-3-small, gpt-3.5-turbo
- **用途**: LanceDB嵌入 + Query rewrite
- **风险**: 成本上升
- **缓解**:
  - 使用最便宜的embedding模型 ($0.00002/1K tokens)
  - Query rewrite限制最多2次迭代

### 7.2 对现有Epic的依赖

**D4: Epic 4 (无纸化回顾检验系统)**
- **依赖内容**: `generate_verification_canvas()` API
- **集成点**: 用Agentic RAG替换现有单一检索
- **风险**: 低 (Epic 4已100%完成, 接口稳定)

**D5: Epic 10 (智能并行处理系统)**
- **依赖内容**: `graphiti-memory-agent` 定义
- **集成点**: 调用`add_episode()` / `search_memories()`
- **风险**: 中 (Epic 10记忆存储功能未完成)
- **缓解**: 本Epic实现完整Graphiti集成, 回填Epic 10缺失功能

**D6: Epic 1-3 (Canvas核心操作)**
- **依赖内容**: `canvas_utils.py` (CanvasJSONOperator / CanvasBusinessLogic)
- **集成点**: 读取Canvas节点, 创建检验白板
- **风险**: 极低 (Epic 1-3已稳定运行6个月+)

### 7.3 被依赖关系 (Other Epics Depend on This)

**Epic 14: 艾宾浩斯复习系统**
- **依赖内容**: Temporal Memory的`get_weak_concepts()` API
- **触发点4**: "行为监控触发 - 连续3天评分<60分的概念自动加入复习计划"
- **影响**: Epic 14的复习调度核心依赖本Epic的FSRS实现
- **时间关系**: 本Epic需在Epic 14 Story 14.4前完成

---

## 8. Risks and Mitigation

### 8.1 技术风险

**R1: LanceDB迁移数据丢失**
- **概率**: 中
- **影响**: 高 (丢失所有历史解释文档向量)
- **缓解策略**:
  - Phase 2: 实施双写模式 (ChromaDB + LanceDB同时写入)
  - 迁移前完整备份ChromaDB数据
  - 迁移后数据一致性校验 (100%记录对齐)
  - Rollback plan: 保留ChromaDB 1周后再下线

**R2: Neo4j性能瓶颈**
- **概率**: 低
- **影响**: 中 (Graphiti检索延迟>100ms)
- **缓解策略**:
  - 预先性能测试: 10K概念 + 50K关系模拟
  - 索引优化: Concept.name, Episode.created_at
  - 如性能不足, 降级到仅用LanceDB (失去Graph检索能力)

**R3: Cohere API限流**
- **概率**: 低
- **影响**: 低 (检验白板Reranking降级到Local)
- **缓解策略**:
  - 监控API用量, 接近限额时告警
  - 自动降级逻辑: Cohere失败 → 立即切换Local Reranker
  - 预留备用API Key (团队成员账号)

**R4: Query重写死循环**
- **概率**: 极低
- **影响**: 中 (检索请求超时)
- **缓解策略**:
  - 硬编码最大迭代次数=2
  - 超时保护: 单次检索请求总时长<10秒
  - LangSmith监控: 检测异常重写次数

**R5: LangGraph版本兼容性**
- **概率**: 低
- **影响**: 中 (Send模式API变更)
- **缓解策略**:
  - 锁定langgraph版本: `langgraph==0.2.55` (当前最新稳定版)
  - 持续关注LangGraph changelog
  - 预留2天buffer用于版本升级适配

### 8.2 成本风险

**R6: Cohere成本超预算**
- **概率**: 低
- **影响**: 低 (预算$16/年, 实际可能$25/年)
- **缓解策略**:
  - 实时成本监控 (LangSmith cost tracking)
  - 月度成本告警: >$3/月
  - 降级策略: 超预算后仅用Local Reranker

**R7: OpenAI成本上升**
- **概率**: 中 (Query rewrite新增LLM调用)
- **影响**: 低 (预计+$5/年)
- **缓解策略**:
  - 使用gpt-3.5-turbo ($0.0005/1K tokens, 便宜20倍 vs gpt-4)
  - 限制Query rewrite最多2次
  - Cascade模式优先, 减少检索次数

### 8.3 时间风险

**R8: 开发时间超期**
- **概率**: 中
- **影响**: 高 (阻塞Epic 14开发)
- **缓解策略**:
  - MVP优先: Phase 1-4为P0 (10.5天), Phase 5 (多模态)为Optional
  - 并行开发: Infrastructure (Story 12.1-12.3) 与 Agentic RAG (Story 12.4-12.7)可部分并行
  - 每周进度Review: 识别blockers, 及时调整资源

**R9: 测试时间不足**
- **概率**: 中
- **影响**: 中 (质量指标未达标即上线)
- **缓解策略**:
  - 预留3天测试时间 (Story 12.14-12.16)
  - 自动化测试优先: 性能基准测试全自动
  - 质量门禁: MRR<0.380不允许上线

### 8.4 集成风险

**R10: Epic 10记忆存储功能缺失**
- **概率**: 高 (已知问题)
- **影响**: 中 (graphiti-memory-agent调用失败)
- **缓解策略**:
  - 本Epic实现完整Graphiti集成 (Story 12.1)
  - 回填Epic 10.14缺失的活动记录功能
  - 独立验收: 不依赖Epic 10现有代码

---

## 9. Implementation Timeline

### 9.1 整体时间规划

**总工期**: 15.5人天 (3周)

**Week 1: Infrastructure (5.5天)**
- Story 12.1: Graphiti集成 (2天)
- Story 12.2: LanceDB POC (1天)
- Story 12.3: LanceDB迁移 (1.5天)
- Story 12.4: Temporal Memory (1天)

**Week 2: Agentic RAG Development (7天)**
- Story 12.5: LangGraph StateGraph (2天)
- Story 12.6: 并行检索 (1.5天)
- Story 12.7: 融合算法 (2天)
- Story 12.8: 混合Reranking (2天)
- Story 12.9: 质量控制循环 (1.5天)

**Week 3: Integration & Testing (3天)**
- Story 12.10: Canvas集成 (1天)
- Story 12.11: graphiti-memory-agent接口 (0.5天)
- Story 12.12: LangSmith可观测 (1天)
- Story 12.13: 回归测试 (0.5天)
- Story 12.14: 性能基准测试 (1天)
- Story 12.15: E2E集成测试 (1天)
- Story 12.16: 文档和部署 (0.5天)

**Optional (Phase 5)**:
- Story 12.17: 多模态支持 (ImageBind) - 2天

### 9.2 里程碑 (Milestones)

**M1: Infrastructure Complete** (Day 5.5)
- ✅ Neo4j + Graphiti运行
- ✅ LanceDB迁移完成, 数据一致性100%
- ✅ Temporal Memory + FSRS集成
- **验收**: 3层记忆系统独立可用

**M2: Agentic RAG Core Complete** (Day 12.5)
- ✅ StateGraph正确运行
- ✅ 并行检索 + 3种融合算法 + 混合Reranking
- ✅ 质量控制循环
- **验收**: 独立检索测试MRR@10 ≥ 0.380

**M3: Canvas Integration Complete** (Day 13.5)
- ✅ 检验白板生成集成Agentic RAG
- ✅ graphiti-memory-agent调用接口
- ✅ Epic 1-10功能回归测试通过
- **验收**: 检验白板生成准确率 ≥ 85%

**M4: Testing & Documentation Complete** (Day 15.5)
- ✅ E2E测试通过
- ✅ 性能基准测试达标
- ✅ 文档完整 (ADRs + API docs + 用户指南)
- **验收**: Epic-level AC全部通过

### 9.3 关键路径分析

**Critical Path** (不可并行, 总计10.5天):
```
Story 12.1 (Graphiti集成, 2天)
  ↓
Story 12.5 (LangGraph StateGraph, 2天)
  ↓
Story 12.6 (并行检索, 1.5天)
  ↓
Story 12.7 (融合算法, 2天)
  ↓
Story 12.10 (Canvas集成, 1天)
  ↓
Story 12.15 (E2E测试, 1天)
  ↓
Story 12.16 (文档和部署, 0.5天)
```

**可并行任务**:
- Story 12.2-12.3 (LanceDB) 与 Story 12.4 (Temporal Memory) 可并行
- Story 12.8 (Reranking) 与 Story 12.9 (质量控制) 可并行
- Story 12.11 (graphiti-memory-agent) 与 Story 12.12 (LangSmith) 可并行

**时间buffer**: 5天 (15.5 - 10.5) = 33% buffer

---

## 10. Story Breakdown Preview

### 10.1 MVP Stories (P0, 11个, 10.5天)

#### **Infrastructure (4个Story, 4.5天)**

**Story 12.1: Graphiti时序知识图谱集成**
- **优先级**: P0
- **工作量**: 2天
- **目标**: Neo4j + Graphiti环境搭建, 学习会话记录功能
- **AC**:
  - Neo4j Community Edition成功运行
  - Graphiti client连接成功
  - `add_episode()` 正确提取概念和关系
  - `hybrid_search()` 返回Graph + Semantic + BM25结果
- **Tech Stack**: Neo4j 5.0, Graphiti, Docker

**Story 12.2: LanceDB POC验证**
- **优先级**: P0
- **工作量**: 1天
- **目标**: LanceDB性能测试 + 多模态能力验证
- **AC**:
  - 10K向量检索延迟<20ms
  - 100K向量检索延迟<50ms
  - OpenAI embedding集成成功
- **Tech Stack**: LanceDB, OpenAI API

**Story 12.3: ChromaDB → LanceDB数据迁移**
- **优先级**: P0
- **工作量**: 1.5天
- **目标**: 零数据丢失迁移 + 双写模式
- **AC**:
  - 数据一致性100% (ChromaDB vs LanceDB record count对齐)
  - 双写模式成功运行1周
  - Rollback plan验证通过
- **Tech Stack**: ChromaDB, LanceDB, Python migration script

**Story 12.4: Temporal Memory实现**
- **优先级**: P0
- **工作量**: 1天
- **目标**: FSRS集成 + 学习行为时序追踪
- **AC**:
  - `get_weak_concepts()` 基于FSRS返回低稳定性概念
  - `update_behavior()` 正确更新学习行为
  - FSRS卡片正确更新 (difficulty, stability, due)
- **Tech Stack**: Py-FSRS, SQLite

---

#### **Agentic RAG Core (4个Story, 7天)**

**Story 12.5: LangGraph StateGraph构建**
- **优先级**: P0
- **工作量**: 2天
- **目标**: StateGraph定义 + 基础节点实现
- **AC**:
  - CanvasRAGState schema定义完成
  - CanvasRAGConfig context schema定义完成
  - 5个核心节点实现 (retrieve_graphiti, retrieve_lancedb, fuse, rerank, check_quality)
  - StateGraph compile成功
- **Tech Stack**: LangGraph, LangSmith

**Story 12.6: 并行检索实现 (Send模式)**
- **优先级**: P0
- **工作量**: 1.5天
- **目标**: Send模式fan-out + RetryPolicy
- **AC**:
  - `fan_out_retrieval()` 正确dispatch 3个retrieval节点
  - Graphiti/LanceDB并行查询, 总延迟<100ms (vs 串行180ms)
  - RetryPolicy处理ConnectionError/TimeoutError, 最多3次重试
- **Tech Stack**: LangGraph Send, asyncio

**Story 12.7: 3种融合算法实现**
- **优先级**: P0
- **工作量**: 2天
- **目标**: RRF / Weighted / Cascade算法 + 自适应选择
- **AC**:
  - RRF算法正确实现 (k=60)
  - Weighted算法支持alpha/beta参数
  - Cascade算法Tier 1/Tier 2正确触发
  - 自适应选择: 检验白板用Weighted, 日常用RRF
- **Tech Stack**: Python, NumPy

**Story 12.8: 混合Reranking策略**
- **优先级**: P0
- **工作量**: 2天
- **目标**: Local Cross-Encoder + Cohere API + 自动选择
- **AC**:
  - Local Reranker (bge-reranker-base) 正确rerank中文文档
  - Cohere Reranker调用成功, API调用成功率≥99%
  - hybrid_auto正确选择 (检验白板用Cohere, 日常用Local)
  - 成本监控: Cohere调用计数<50 requests/月
- **Tech Stack**: sentence-transformers, Cohere API

**Story 12.9: 质量控制循环**
- **优先级**: P0
- **工作量**: 1.5天
- **目标**: Quality checker + Query rewriter + 循环逻辑
- **AC**:
  - Quality checker正确分级 (high/medium/low)
  - Query rewriter在low质量时触发
  - 最多2次迭代后强制返回
  - Rewrite后质量提升 (avg_score +0.15)
- **Tech Stack**: OpenAI gpt-3.5-turbo

---

#### **Integration & Testing (3个Story, 2.5天)**

**Story 12.10: Canvas检验白板生成集成**
- **优先级**: P0
- **工作量**: 1天
- **目标**: 用Agentic RAG替换现有单一检索
- **AC**:
  - `generate_verification_canvas()` 调用Agentic RAG
  - 检验白板生成准确率 ≥ 85%
  - 向后兼容: Epic 4现有功能不退化
- **Tech Stack**: canvas_utils.py, LangGraph integration

**Story 12.15: E2E集成测试**
- **优先级**: P0
- **工作量**: 1天
- **目标**: 2个场景完整测试
- **AC**:
  - 场景1 (检验白板生成) 端到端通过
  - 场景2 (艾宾浩斯复习) 端到端通过
  - MRR@10 ≥ 0.380, Recall@10 ≥ 0.68, F1 ≥ 0.77
- **Tech Stack**: pytest, test fixtures

**Story 12.16: 文档和部署**
- **优先级**: P0
- **工作量**: 0.5天
- **目标**: 用户指南 + 运维手册
- **AC**:
  - 用户指南包含配置、使用、troubleshooting
  - 运维手册包含Neo4j备份、LanceDB维护、成本监控
  - API文档100%覆盖public接口
- **Tech Stack**: Markdown

---

### 10.2 Enhancement Stories (P1, 5个, 5天)

**Story 12.11: graphiti-memory-agent调用接口**
- **优先级**: P1
- **工作量**: 0.5天
- **目标**: 封装Graphiti调用为Agent接口
- **AC**: `add_episode()` / `search_memories()` wrapper正确工作

**Story 12.12: LangSmith可观测性集成**
- **优先级**: P1
- **工作量**: 1天
- **目标**: Trace + 成本监控 + 性能仪表盘
- **AC**: 100%检索请求可追踪, 成本实时监控

**Story 12.13: 回归测试**
- **优先级**: P1
- **工作量**: 0.5天
- **目标**: Epic 1-10核心功能验证
- **AC**: 360+测试全部通过, 无退化

**Story 12.14: 性能基准测试**
- **优先级**: P1
- **工作量**: 1天
- **目标**: 自动化性能测试
- **AC**: MRR/Recall/F1/P95延迟自动测试通过

**Story 12.17: 多模态支持 (ImageBind集成)**
- **优先级**: P2 (Optional)
- **工作量**: 2天
- **目标**: 6模态统一向量空间
- **AC**: 文本查询 → 检索图像/音频学习材料

---

### 10.3 Story依赖图

```
┌─────────────────────────────────────────────────────────────┐
│                       Week 1: Infrastructure                │
├─────────────────────────────────────────────────────────────┤
│  12.1 Graphiti (2d) ──┐                                     │
│                        │                                     │
│  12.2 LanceDB POC (1d)─┼──▶ 12.3 LanceDB迁移 (1.5d)         │
│                        │                                     │
│  12.4 Temporal Mem (1d)┘                                    │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Week 2: Agentic RAG Core                  │
├─────────────────────────────────────────────────────────────┤
│  12.5 StateGraph (2d) ──┐                                   │
│                          │                                   │
│                          ▼                                   │
│  12.6 并行检索 (1.5d) ───┼──▶ 12.7 融合算法 (2d)             │
│                          │                                   │
│                          │    12.8 Reranking (2d) ──┐       │
│                          │                           │       │
│                          └──▶ 12.9 质量控制 (1.5d)──┘       │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Week 3: Integration & Testing                  │
├─────────────────────────────────────────────────────────────┤
│  12.10 Canvas集成 (1d) ──┐                                  │
│                            │                                 │
│  12.11 Agent接口 (0.5d)───┼──▶ 12.15 E2E测试 (1d)           │
│                            │          │                      │
│  12.12 LangSmith (1d) ────┤          │                      │
│                            │          ▼                      │
│  12.13 回归测试 (0.5d)────┤    12.16 文档部署 (0.5d)        │
│                            │                                 │
│  12.14 性能测试 (1d) ─────┘                                 │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼ (Optional)
                   12.17 多模态 (2d)
```

---

## 11. Success Metrics

### 11.1 质量指标 (Quality KPIs)

| 指标 | 当前值 | 目标值 | 测量方法 | 验收标准 |
|------|--------|--------|---------|---------|
| **MRR@10** (检索质量) | 0.280 | ≥0.380 | 人工标注50个query, 计算Mean Reciprocal Rank | 达标 |
| **Recall@10** (召回率) | 0.45 | ≥0.68 | Top-10包含相关文档的比例 | 达标 |
| **薄弱点聚类F1** | 0.55 | ≥0.77 | 聚类结果 vs 人工标注, F1-score | 达标 |
| **检验白板生成准确率** | 60% | ≥85% | 100个检验题人工评估相关性 | 达标 |
| **单元测试覆盖率** | - | ≥80% | pytest-cov | 达标 |

### 11.2 性能指标 (Performance KPIs)

| 指标 | 当前值 | 目标值 | 测量方法 | 验收标准 |
|------|--------|--------|---------|---------|
| **P95检索延迟** | 180ms | <400ms | LangSmith trace统计 | 达标 |
| **P99检索延迟** | 250ms | <600ms | LangSmith trace统计 | 达标 |
| **并发支持** | 10 QPS | ≥10 QPS | Locust负载测试 | 稳定运行无错误 |
| **向量扩展性** | 100K | ≥1M | LanceDB性能测试 | 延迟<100ms |

### 11.3 成本指标 (Cost KPIs)

| 指标 | 预算 | 实际目标 | 测量方法 | 验收标准 |
|------|------|---------|---------|---------|
| **年度运营成本** | $60 | ≤$49 | 成本监控仪表盘 | 达标 |
| **Cohere API成本** | $20 | ≤$16 | Cohere dashboard | 达标 |
| **OpenAI API成本** | $10 | ≤$8 | OpenAI dashboard | 达标 |
| **单次检索成本** | - | <$0.001 | LangSmith cost tracking | 达标 |

### 11.4 用户体验指标 (UX KPIs)

| 指标 | 当前值 | 目标值 | 测量方法 | 验收标准 |
|------|--------|--------|---------|---------|
| **检验白板生成时间** | ~8秒 | <5秒 | 端到端计时 | 达标 (检索优化节省3秒) |
| **检索结果相关性** | 3.2/5 | ≥4.0/5 | 用户主观评分 (5分制) | 达标 |
| **检索失败率** | 2% | <1% | 错误监控 | 达标 |

### 11.5 验收Gate (Quality Gates)

**Gate 1: Infrastructure Complete (Day 5.5)**
- ✅ Graphiti `hybrid_search()` 返回结果
- ✅ LanceDB迁移数据一致性100%
- ✅ Temporal Memory `get_weak_concepts()` 返回FSRS结果

**Gate 2: Agentic RAG Core Complete (Day 12.5)**
- ✅ StateGraph compile成功, 无语法错误
- ✅ 并行检索延迟<100ms
- ✅ MRR@10 ≥ 0.380 (独立测试集)

**Gate 3: Canvas Integration Complete (Day 13.5)**
- ✅ 检验白板生成准确率 ≥ 85%
- ✅ Epic 1-10回归测试通过 (360+测试)
- ✅ 无breaking changes

**Gate 4: Production Ready (Day 15.5)**
- ✅ E2E测试通过 (2个场景)
- ✅ 性能测试达标 (P95<400ms, P99<600ms)
- ✅ 成本监控正常 (年度预算<$60)
- ✅ 文档完整 (ADRs + API docs + 用户指南 + 运维手册)

---

## 附录 A: 术语表

| 术语 | 全称 | 定义 |
|------|------|------|
| **Agentic RAG** | Agent-Driven Retrieval Augmented Generation | LLM驱动的智能检索增强生成, 动态调整检索策略 |
| **RRF** | Reciprocal Rank Fusion | 倒数排名融合算法, Score = Σ(1/(k+rank)) |
| **MRR** | Mean Reciprocal Rank | 平均倒数排名, 检索质量指标 |
| **F1-score** | F1分数 | 精准率和召回率的调和平均数 |
| **FSRS** | Free Spaced Repetition Scheduler | 免费间隔重复调度算法, 预测遗忘曲线 |
| **Graphiti** | - | 时序知识图谱框架 (基于Neo4j) |
| **LanceDB** | - | 列式向量数据库 (Apache Arrow格式) |
| **StateGraph** | LangGraph State Graph | LangGraph的状态图编排模式 |
| **Send** | LangGraph Send Pattern | LangGraph并行任务分发模式 |
| **ImageBind** | - | Meta开源的6模态统一向量空间模型 |
| **IVF-PQ** | Inverted File + Product Quantization | 向量索引算法, 用于10M+向量高效检索 |

---

## 附录 B: 参考文档

### B.1 Architecture Decision Records (ADRs)

1. **ADR-002: Vector Database Selection** - `docs/architecture/ADR-002-VECTOR-DATABASE-SELECTION.md`
   - Decision: LanceDB over ChromaDB/Milvus
   - 核心理由: 多模态 + 10倍性能 + 扩展性

2. **ADR-003: Agentic RAG Architecture** - `docs/architecture/ADR-003-AGENTIC-RAG-ARCHITECTURE.md`
   - Decision: LangGraph StateGraph
   - 核心理由: 并行检索 + 自适应融合 + 质量控制

3. **ADR-004: GraphRAG Integration Evaluation** - `docs/architecture/ADR-004-GRAPHRAG-INTEGRATION-EVALUATION.md`
   - Decision: NOT introduce Microsoft GraphRAG
   - 核心理由: Graphiti足够 + 架构简化 + 成本节省$1,855/年

### B.2 技术研究文档

4. **Comprehensive Technical Plan** - `docs/architecture/COMPREHENSIVE-TECHNICAL-PLAN-3LAYER-MEMORY-AGENTIC-RAG.md`
   - 80,000字完整技术方案
   - 完整数据流 + 实现路线图 + 性能目标

5. **Graphiti Hybrid Search Analysis** - `docs/architecture/GRAPHITI-HYBRID-SEARCH-ANALYSIS.md`
   - Graphiti内置混合搜索能力分析
   - Graph + Semantic + BM25融合逻辑

6. **Fusion Algorithm Design** - `docs/architecture/FUSION-ALGORITHM-DESIGN.md`
   - 3种融合算法详细设计 (RRF/Weighted/Cascade)
   - 性能对比和适用场景

7. **Reranking Strategy Selection** - `docs/architecture/RERANKING-STRATEGY-SELECTION.md`
   - Local vs Cohere vs Hybrid对比
   - 成本分析 (77%节省)

8. **LangGraph Integration Design** - `docs/architecture/LANGGRAPH-INTEGRATION-DESIGN.md`
   - LangGraph StateGraph设计
   - Send并行模式 + RetryPolicy

### B.3 Skills文档

9. **LangGraph Skill** - `.claude/skills/langgraph/SKILL.md`
   - 952页LangGraph完整文档
   - StateGraph + Send + MessagesState + RetryPolicy

10. **Graphiti Skill** - `.claude/skills/graphiti/SKILL.md`
    - Graphiti框架完整文档
    - hybrid_search + add_episode + temporal edges

### B.4 项目上下文

11. **Project Brief** - `docs/project-brief.md`
    - Canvas学习系统完整项目概述
    - Epic 1-10现有功能

12. **CLAUDE.md** - `CLAUDE.md`
    - Claude Code项目上下文
    - Agent架构 + 技术栈 + 零幻觉开发原则

---

**文档版本**: v1.0
**最后更新**: 2025-11-14
**下一步**: 创建 `EPIC-12-STORY-MAP.md` (Story拆解和优先级)
**SM Handoff Ready**: ✅ 本文档 + 3个ADRs + 综合技术方案已完成
