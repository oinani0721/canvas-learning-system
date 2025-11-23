# Story GraphRAG.3: 智能问题路由与融合重排序

---
**Status**: ❌ **Deprecated (已废弃)**
**Deprecated Date**: 2025-11-14
**Deprecated Reason**: 父Epic (EPIC-GraphRAG) 因过度设计问题已暂停
**Replacement**: EPIC-Neo4j-GDS-Integration
**Decision Record**: ADR-004, SCP-005
---

## ⚠️ Story状态：已废弃

**废弃日期**: 2025-11-14
**废弃原因**: 父Epic (EPIC-GraphRAG) 因过度设计问题已暂停

**替代方案**:
- Epic层面：EPIC-Neo4j-GDS-Integration (无需复杂路由和融合)
- 功能实现：Graphiti hybrid_search已提供Graph + Semantic + BM25混合检索

**详情参见**:
- Sprint Change Proposal: SCP-005 (GraphRAG过度设计纠偏)
- Architecture Decision Record: ADR-004 (Do Not Integrate GraphRAG)

**历史价值**: 保留此Story作为检索路由架构参考

---

## 原始Story定义（以下内容为历史记录）

---

## Status
~~In Progress~~ ❌ Deprecated

## Story

**As a** Canvas学习系统,
**I want** 实现智能问题路由和四层检索融合重排序，自动选择最佳检索策略（Local/Global/Hybrid）并优化结果质量,
**so that** 用户能够获得精准、全面、高效的检验问题生成，无论是具体概念查询、数据集级分析还是复杂综合查询。

## Acceptance Criteria

1. `question_router_node`成功实现，准确率≥90%（100次查询中≥90次正确分类）
2. 支持3种查询类型路由：local（具体概念）、global（数据集级）、hybrid（复杂综合）
3. `composite_search_node`成功并行执行4层检索（Graphiti + LanceDB + Temporal + GraphRAG）
4. `fusion_rerank_node`使用RRF算法融合4源结果，去重率≥30%（合并相同概念）
5. Hybrid路径端到端延迟<12秒（P95）
6. Local路径端到端延迟<5秒（P95）
7. Global路径端到端延迟<8秒（P95）
8. 融合后文档相关性提升≥15%（vs 单源检索，NDCG@10指标）

## Tasks / Subtasks

### Task 1: 实现和验证question_router_node (AC: 1, 2)

- [ ] **Subtask 1.1**: 验证Section 10.5.2的question_router_node实现
  - [ ] ✅ 验证LangGraph Skills - 路由节点设计模式
  - [ ] 检查代码是否符合LANGGRAPH-MEMORY-INTEGRATION-DESIGN.md Section 10.5.2
  - [ ] 验证Prompt模板包含3种路由规则（local/global/hybrid）
  - [ ] 验证JSON输出格式和结构化解析

- [ ] **Subtask 1.2**: 优化路由Prompt模板
  - [ ] 添加Few-shot示例（每种类型3个示例）
  - [ ] 优化路由规则描述（更明确的关键词匹配）
  - [ ] 添加边界情况处理（模糊查询的默认路由）
  - [ ] 测试中文查询的路由准确性

- [ ] **Subtask 1.3**: 实现路由决策日志
  - [ ] 记录每次路由决策：query → query_type → reasoning
  - [ ] 添加置信度评分（confidence: 0-1）
  - [ ] 低置信度时(<0.7)触发告警或人工审核
  - [ ] 日志输出到`logs/question_router.log`

- [ ] **Subtask 1.4**: 创建路由准确率测试数据集
  - [ ] 收集100个查询样本（涵盖3种类型）
    - Local: 30个（如"什么是逆否命题？"）
    - Global: 30个（如"离散数学中哪些概念最容易混淆？"）
    - Hybrid: 40个（如"逻辑推理的核心概念是什么，我在哪些方面最薄弱？"）
  - [ ] 人工标注Ground Truth（正确的query_type）
  - [ ] 存储为JSON：`tests/fixtures/routing_test_dataset.json`

- [ ] **Subtask 1.5**: 路由准确率测试
  - [ ] 使用100样本测试路由准确率
  - [ ] 验证准确率≥90%（至少90次正确分类）
  - [ ] 分析错误案例（误分类的query类型）
  - [ ] 根据错误案例优化Prompt模板

- [ ] **Subtask 1.6**: 单元测试
  - [ ] 测试Local查询路由（"什么是X？"→ local）
  - [ ] 测试Global查询路由（"哪些X？"→ global）
  - [ ] 测试Hybrid查询路由（"X+Y"→ hybrid）
  - [ ] 测试模糊查询的默认路由
  - [ ] 测试路由日志记录

### Task 2: 实现和验证composite_search_node (AC: 3)

- [ ] **Subtask 2.1**: 验证Section 10.5.2的composite_search_node实现
  - [ ] ✅ 验证LangGraph Skills - 并行执行模式
  - [ ] 检查asyncio.gather()并行调用4个工具
  - [ ] 验证超时控制（单工具5秒，总超时10秒）
  - [ ] 验证失败降级（至少2个工具成功即可继续）

- [ ] **Subtask 2.2**: 实现4层检索工具适配
  - [ ] 适配graphiti_hybrid_search_tool（20个结果）
  - [ ] 适配lancedb_hybrid_search_tool（15个结果）
  - [ ] 适配temporal_behavior_query_tool（10个结果）
  - [ ] 适配graphrag_global_search_tool（10个结果）
  - [ ] 统一输出格式（source, content, metadata, relevance_score）

- [ ] **Subtask 2.3**: 优化并行执行性能
  - [ ] 使用asyncio.create_task()而非gather()（提前启动任务）
  - [ ] 实现超时后的优雅取消（cancel unfinished tasks）
  - [ ] 添加工具执行延迟监控（记录每个工具的延迟）
  - [ ] 验证并行执行延迟<8秒（P95）

- [ ] **Subtask 2.4**: 实现失败降级策略
  - [ ] 定义降级阈值：至少2个工具成功
  - [ ] 失败时记录详细错误日志（工具名、失败原因）
  - [ ] 部分成功时添加质量告警标记
  - [ ] 全部失败时返回空文档并触发query rewrite

- [ ] **Subtask 2.5**: 单元测试
  - [ ] 测试4工具全部成功
  - [ ] 测试部分工具失败（2/4成功）
  - [ ] 测试单工具超时
  - [ ] 测试全部工具失败
  - [ ] 测试并行执行延迟

### Task 3: 实现和验证fusion_rerank_node (AC: 4)

- [ ] **Subtask 3.1**: 验证Section 10.5.2的fusion_rerank_node实现
  - [ ] ✅ 验证LanceDB Context7 - RRF Reranker模式
  - [ ] 检查RRF算法实现（k=60, RRF公式）
  - [ ] 验证去重逻辑（基于concept字段）
  - [ ] 验证输出格式（rrf_score字段）

- [ ] **Subtask 3.2**: 实现RRF融合算法
  - [ ] 实现rrf_fusion函数（见Section 10.5.2代码）
  - [ ] 按source分组并计算排名（rank）
  - [ ] 计算每个文档的RRF分数：`Σ 1/(k + rank_source(doc))`
  - [ ] 按RRF分数降序排序
  - [ ] 添加RRF分数归一化（0-1范围）

- [ ] **Subtask 3.3**: 实现去重逻辑
  - [ ] 基于concept字段识别重复文档
  - [ ] 合并相同概念的多源证据（保留最高RRF分数）
  - [ ] 添加multi_source标记（标识来自多个数据源）
  - [ ] 记录去重统计（去重前数量 → 去重后数量）

- [ ] **Subtask 3.4**: 支持多种融合策略（可选）
  - [ ] 实现CrossEncoder重排序（使用sentence-transformers）
  - [ ] 实现线性加权融合（可配置权重）
  - [ ] 实现MMR多样性重排序（避免结果过于集中）
  - [ ] 添加fusion_strategy参数（rrf/cross_encoder/linear/mmr）

- [ ] **Subtask 3.5**: 验证去重率和质量提升
  - [ ] 测试去重率（去重文档数 / 总文档数）
  - [ ] 验证去重率≥30%
  - [ ] 使用NDCG@10指标评估融合后相关性
  - [ ] 验证融合后相关性提升≥15%（vs 单源检索）

- [ ] **Subtask 3.6**: 单元测试
  - [ ] 测试RRF算法计算准确性
  - [ ] 测试去重逻辑（相同concept合并）
  - [ ] 测试多源证据合并
  - [ ] 测试融合策略切换（rrf/cross_encoder/linear）

### Task 4: 集成StateGraph并验证三条路径 (AC: 5, 6, 7)

- [ ] **Subtask 4.1**: 验证Section 10.5.1的StateGraph定义
  - [ ] ✅ 验证LangGraph Skills - StateGraph构建模式
  - [ ] 检查节点定义（question_router, generate_query_*, tool nodes, fusion, grade, rewrite, generate）
  - [ ] 验证边和条件路由（route_by_query_type, route_query, grade_documents_route）
  - [ ] 验证Self-Correction Loop（rewrite → question_router）

- [ ] **Subtask 4.2**: 实现条件路由函数
  - [ ] 实现route_by_query_type（从question_router路由到3种generate_query节点）
  - [ ] 实现route_query（决定是否需要检索）
  - [ ] 实现grade_documents_route（基于质量决定rewrite or generate）
  - [ ] 添加路由决策日志（每次路由都记录）

- [ ] **Subtask 4.3**: 端到端Local路径测试
  - [ ] 测试查询："什么是逆否命题？"
  - [ ] 验证路径：question_router → local → generate_query_local → local_search_tools → grade_documents → generate
  - [ ] 验证端到端延迟<5秒（P95）
  - [ ] 验证检索结果质量（包含相关概念）

- [ ] **Subtask 4.4**: 端到端Global路径测试
  - [ ] 测试查询："离散数学中哪些概念最容易混淆？"
  - [ ] 验证路径：question_router → global → generate_query_global → graphrag_global_search → grade_documents → generate
  - [ ] 验证端到端延迟<8秒（P95）
  - [ ] 验证返回数据集级分析结果（包含社区摘要）

- [ ] **Subtask 4.5**: 端到端Hybrid路径测试
  - [ ] 测试查询："逻辑推理的核心概念是什么，我在哪些方面最薄弱？"
  - [ ] 验证路径：question_router → hybrid → generate_query_hybrid → composite_search → fusion_rerank → grade_documents → generate
  - [ ] 验证端到端延迟<12秒（P95）
  - [ ] 验证4源融合结果（包含Graphiti/LanceDB/Temporal/GraphRAG）

- [ ] **Subtask 4.6**: Self-Correction Loop测试
  - [ ] 测试模糊查询："离散数学"（质量不足触发rewrite）
  - [ ] 验证路径：question_router → local → local_search_tools → grade_documents (质量低) → rewrite → question_router → ...
  - [ ] 验证最多重试3次（避免无限循环）
  - [ ] 验证重写后查询质量提升

### Task 5: 性能优化和监控 (AC: 5, 6, 7, 8)

- [ ] **Subtask 5.1**: 实现延迟监控
  - [ ] 记录每个节点的执行延迟（question_router, tool_execution, fusion, grade, generate）
  - [ ] 计算端到端延迟（从START到END）
  - [ ] 分路径统计（Local/Global/Hybrid的P50/P95/P99延迟）
  - [ ] 提供延迟查询接口：`get_latency_stats() -> Dict`

- [ ] **Subtask 5.2**: 优化Local路径性能
  - [ ] 并行执行Graphiti/LanceDB/Temporal（asyncio.gather）
  - [ ] 减少Graphiti结果数量（20→15）
  - [ ] 使用缓存（相同查询5分钟内返回缓存结果）
  - [ ] 验证优化后延迟<5秒（P95）

- [ ] **Subtask 5.3**: 优化Global路径性能
  - [ ] 使用本地模型（Qwen2.5）替代API（降低网络延迟）
  - [ ] 降低max_data_tokens（12000→8000，减少推理时间）
  - [ ] 使用Level 2社区（vs Level 3，速度快2倍）
  - [ ] 验证优化后延迟<8秒（P95）

- [ ] **Subtask 5.4**: 优化Hybrid路径性能
  - [ ] 使用asyncio.create_task()提前启动4个检索任务
  - [ ] 实现超时取消（8秒后取消未完成的任务）
  - [ ] 优化RRF融合算法（使用字典缓存，避免重复计算）
  - [ ] 验证优化后延迟<12秒（P95）

- [ ] **Subtask 5.5**: 实现质量监控
  - [ ] 记录融合后NDCG@10分数（vs 单源检索）
  - [ ] 记录去重率（去重文档数 / 总文档数）
  - [ ] 记录路由准确率（正确分类 / 总查询数）
  - [ ] 提供质量查询接口：`get_quality_metrics() -> Dict`

- [ ] **Subtask 5.6**: 单元测试
  - [ ] 测试延迟监控准确性
  - [ ] 测试缓存机制（相同查询返回缓存）
  - [ ] 测试超时取消（8秒后未完成的任务）
  - [ ] 测试质量指标计算

### Task 6: 集成测试和文档 (ALL AC)

- [ ] **Subtask 6.1**: 端到端集成测试
  - [ ] 测试完整流程（START → question_router → 检索 → 融合 → 评分 → 生成 → END）
  - [ ] 测试3种路径（Local/Global/Hybrid）
  - [ ] 测试Self-Correction Loop（模糊查询重写）
  - [ ] 测试失败降级（部分工具失败）

- [ ] **Subtask 6.2**: 性能基准测试
  - [ ] 测试Local路径延迟（100次查询，验证P95<5秒）
  - [ ] 测试Global路径延迟（50次查询，验证P95<8秒）
  - [ ] 测试Hybrid路径延迟（50次查询，验证P95<12秒）
  - [ ] 生成性能基准报告：`performance_routing_fusion_report.md`

- [ ] **Subtask 6.3**: 质量验证测试
  - [ ] 使用100样本测试路由准确率（验证≥90%）
  - [ ] 使用50样本测试融合去重率（验证≥30%）
  - [ ] 使用NDCG@10指标验证融合质量提升（验证≥15%）
  - [ ] 生成质量验证报告：`quality_routing_fusion_report.md`

- [ ] **Subtask 6.4**: 创建用户文档
  - [ ] 编写`docs/user-guides/graphrag-routing-fusion-guide.md`
  - [ ] 包含：3种路由规则、Hybrid路径优势、RRF融合原理
  - [ ] 添加使用示例（不同查询类型的路由结果）
  - [ ] 添加监控指标查看指南

- [ ] **Subtask 6.5**: 创建开发者文档
  - [ ] 编写`docs/architecture/graphrag-routing-fusion-architecture.md`
  - [ ] 包含：StateGraph架构图、3条路径流程、RRF算法详解
  - [ ] 添加扩展指南（如何添加新的路由类型）
  - [ ] 添加性能优化建议

## Dev Notes

### 架构上下文

**Agentic RAG架构** [Source: docs/architecture/LANGGRAPH-MEMORY-INTEGRATION-DESIGN.md#Section 10.2]

本Story实现Section 10已设计的智能问题路由和融合重排序功能，是GraphRAG集成的核心智能层。

```
┌──────────────────────────────────────────────────────────┐
│  Agentic RAG架构全景（含GraphRAG智能路由）                │
│                                                           │
│  ┌─────────────────┐                                     │
│  │ question_router │ ← 智能问题分类器（本Story核心1）      │
│  └────────┬────────┘                                     │
│           │                                              │
│     ┌─────┴──────┬──────────┐                           │
│     ↓            ↓          ↓                            │
│  ┌──────┐   ┌─────────┐ ┌────────┐                      │
│  │Local │   │ Global  │ │ Hybrid │                      │
│  │Path  │   │ Path    │ │ Path   │                      │
│  └──┬───┘   └────┬────┘ └───┬────┘                      │
│     │            │           │                           │
│     ↓            ↓           ↓                           │
│  ┌──────────┐ ┌────────┐ ┌────────────────┐             │
│  │3工具检索│ │GraphRAG│ │composite_search│              │
│  │(Graphiti│ │Global  │ │(4工具并行)     │ ← 本Story核心2│
│  │LanceDB  │ │Search  │ └───────┬────────┘             │
│  │Temporal)│ │        │         │                       │
│  └────┬─────┘ └───┬────┘         ↓                       │
│       │           │        ┌────────────┐                │
│       │           │        │fusion_     │ ← 本Story核心3  │
│       │           │        │rerank(RRF) │                │
│       │           │        └─────┬──────┘                │
│       └───────────┴──────────────┘                       │
│                   ↓                                      │
│          ┌──────────────────┐                            │
│          │ grade_documents  │                            │
│          └────────┬─────────┘                            │
│                   │                                      │
│            ┌──────┴──────┐                               │
│            ↓             ↓                               │
│       ┌────────┐    ┌─────────┐                          │
│       │generate│    │rewrite  │                          │
│       └────────┘    └─────┬───┘                          │
│                           │                              │
│                           └──────→ question_router       │
│                                    (Self-Correction Loop)│
└──────────────────────────────────────────────────────────┘
```

**核心组件**:
1. **question_router**: 智能问题分类器（local/global/hybrid）
2. **composite_search_node**: 4层并行检索（Graphiti + LanceDB + Temporal + GraphRAG）
3. **fusion_rerank_node**: RRF融合重排序

**3种检索路径**:
- **Local Path**: 具体概念查询 → 3工具检索 → <5秒
- **Global Path**: 数据集级分析 → GraphRAG Global Search → <8秒
- **Hybrid Path**: 复杂综合查询 → 4工具并行 + RRF融合 → <12秒

### 技术栈

**LangGraph StateGraph** [Source: LangGraph Skill - StateGraph构建模式]

```python
# ✅ Verified from LangGraph Skill (references\llms-txt.md:8723-8825)
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

# Step 1: 定义State Schema
class AgenticRAGState(TypedDict):
    query_type: Literal["local", "global", "hybrid"]
    routing_reasoning: str
    current_query: str
    retrieved_documents: list[dict]
    fusion_strategy: Literal["rrf", "cross_encoder", "linear"]
    workflow_stage: Literal[
        "routing",
        "query_generation",
        "tool_execution",
        "fusion_reranking",
        "document_grading",
        "question_generation"
    ]
    # ... 其他字段

# Step 2: 创建StateGraph
builder = StateGraph(AgenticRAGState)

# Step 3: 添加节点
builder.add_node("question_router", question_router_node)
builder.add_node("generate_query_local", generate_query_or_respond_node)
builder.add_node("generate_query_global", generate_query_or_respond_node)
builder.add_node("generate_query_hybrid", generate_query_or_respond_node)
builder.add_node("local_search_tools", ToolNode([graphiti_tool, lancedb_tool, temporal_tool]))
builder.add_node("graphrag_global_search", graphrag_global_search_node)
builder.add_node("composite_search", composite_search_node)
builder.add_node("fusion_rerank", fusion_rerank_node)
builder.add_node("grade_documents", grade_documents_node)
builder.add_node("rewrite", rewrite_query_node)
builder.add_node("generate", generate_questions_node)

# Step 4: 添加边和条件路由
builder.add_edge(START, "question_router")

builder.add_conditional_edges(
    "question_router",
    route_by_query_type,
    {
        "local": "generate_query_local",
        "global": "generate_query_global",
        "hybrid": "generate_query_hybrid"
    }
)

# ... 其他边定义

# Step 5: 编译graph
graph = builder.compile()
```

**Question Router实现** [Source: LANGGRAPH Section 10.5.2 - question_router_node]

```python
# ✅ Verified from LANGGRAPH-MEMORY-INTEGRATION-DESIGN.md Section 10.5.2
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

async def question_router_node(state: AgenticRAGState) -> AgenticRAGState:
    """智能问题路由节点"""

    router_prompt = ChatPromptTemplate.from_messages([
        ("system", """你是Canvas学习系统的查询路由器。
        分析用户的查询，确定最佳检索策略。

        **路由规则**：

        1. **local** - 具体概念查询
           - 关键词: "什么是", "定义", "解释", "具体概念"
           - 示例: "什么是逆否命题？", "解释特征向量的定义"
           - 检索策略: Graphiti + LanceDB + Temporal (3工具)

        2. **global** - 数据集级分析
           - 关键词: "哪些", "比较", "整体", "数据集级", "最容易混淆"
           - 示例: "离散数学中哪些概念最容易混淆？", "线性代数的核心知识点有哪些？"
           - 检索策略: GraphRAG Global Search (社区检测)

        3. **hybrid** - 复杂综合查询
           - 关键词: 同时包含具体概念和全局分析 (如"核心概念+薄弱点")
           - 示例: "逻辑推理的核心概念是什么，我在哪些方面最薄弱？"
           - 检索策略: 四层并行检索 + RRF融合

        返回JSON格式:
        {{
          "query_type": "local" | "global" | "hybrid",
          "reasoning": "分类依据的简短说明",
          "confidence": 0.0-1.0
        }}
        """),
        ("user", "{query}")
    ])

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    chain = router_prompt | llm | StrOutputParser()

    result_str = await chain.ainvoke({"query": state["canvas_context"]["query"]})

    # 解析JSON输出
    result = json.loads(result_str)

    return {
        **state,
        "query_type": result["query_type"],
        "routing_reasoning": result["reasoning"],
        "workflow_stage": "query_generation"
    }
```

**Composite Search实现** [Source: LANGGRAPH Section 10.5.2 - composite_search_node]

```python
# ✅ Verified from LANGGRAPH-MEMORY-INTEGRATION-DESIGN.md Section 10.5.2
import asyncio

async def composite_search_node(state: AgenticRAGState) -> AgenticRAGState:
    """组合搜索节点：并行执行4层检索"""

    # 定义4个并行任务
    async def graphiti_task():
        return await graphiti_hybrid_search_tool(
            query=state["current_query"],
            canvas_context=state["canvas_context"],
            max_results=20,
            rerank_strategy="rrf"
        )

    async def lancedb_task():
        return await lancedb_hybrid_search_tool(
            query=state["current_query"],
            n_results=15,
            rerank_strategy="rrf"
        )

    async def temporal_task():
        return await temporal_behavior_query_tool(
            concept=state["current_query"],
            query_type="learning_history",
            days_lookback=30
        )

    async def graphrag_task():
        return await graphrag_global_search_tool(
            query=state["current_query"],
            community_level=2,  # Level 2速度快
            max_data_tokens=8000
        )

    # 并行执行，设置超时
    try:
        results = await asyncio.wait_for(
            asyncio.gather(
                graphiti_task(),
                lancedb_task(),
                temporal_task(),
                graphrag_task(),
                return_exceptions=True  # 允许部分失败
            ),
            timeout=10.0  # 总超时10秒
        )

        # 收集成功的结果
        all_docs = []
        successful_count = 0

        for i, result in enumerate(results):
            if not isinstance(result, Exception):
                all_docs.extend(result["documents"])
                successful_count += 1

        # 至少2个工具成功
        if successful_count < 2:
            raise Exception(f"Only {successful_count}/4 tools succeeded")

        return {
            **state,
            "retrieved_documents": all_docs,
            "workflow_stage": "fusion_reranking"
        }

    except asyncio.TimeoutError:
        # 超时处理
        return {
            **state,
            "error_log": state.get("error_log", []) + [{
                "timestamp": datetime.now().isoformat(),
                "error": "Composite search timeout (>10s)"
            }],
            "workflow_stage": "query_rewriting"  # 触发重写
        }
```

**RRF Fusion实现** [Source: LANGGRAPH Section 10.5.2 - fusion_rerank_node]

```python
# ✅ Verified from LANGGRAPH-MEMORY-INTEGRATION-DESIGN.md Section 10.5.2
from collections import defaultdict

async def fusion_rerank_node(state: AgenticRAGState) -> AgenticRAGState:
    """融合重排序节点：使用RRF融合4个数据源"""

    retrieved_docs = state.get("retrieved_documents", [])

    if not retrieved_docs:
        return {**state, "workflow_stage": "document_grading"}

    # 使用RRF融合
    reranked_docs = rrf_fusion(retrieved_docs, k=60)

    # 去重：基于concept字段
    deduplicated_docs = deduplicate_by_concept(reranked_docs)

    return {
        **state,
        "retrieved_documents": deduplicated_docs,
        "workflow_stage": "document_grading"
    }


def rrf_fusion(docs: list[dict], k: int = 60) -> list[dict]:
    """
    Reciprocal Rank Fusion (RRF)算法

    公式：RRF_score(doc) = Σ 1/(k + rank_source_i(doc))

    Args:
        docs: 文档列表（包含source字段）
        k: 常数（推荐60）

    Returns:
        按RRF分数降序排序的文档列表
    """
    # Step 1: 按source分组
    docs_by_source = defaultdict(list)
    for doc in docs:
        docs_by_source[doc["source"]].append(doc)

    # Step 2: 计算每个source内的排名
    for source, source_docs in docs_by_source.items():
        sorted_docs = sorted(
            source_docs,
            key=lambda d: d["metadata"].get("relevance_score", 0),
            reverse=True
        )
        for rank, doc in enumerate(sorted_docs, start=1):
            doc["rank"] = rank

    # Step 3: 计算RRF分数
    rrf_scores = defaultdict(float)
    for doc in docs:
        doc_id = doc["metadata"].get("concept", "") + doc.get("content", "")[:50]
        rrf_scores[doc_id] += 1.0 / (k + doc.get("rank", 1))

    # Step 4: 重新排序
    for doc in docs:
        doc_id = doc["metadata"].get("concept", "") + doc.get("content", "")[:50]
        doc["rrf_score"] = rrf_scores[doc_id]

    return sorted(docs, key=lambda d: d.get("rrf_score", 0), reverse=True)


def deduplicate_by_concept(docs: list[dict]) -> list[dict]:
    """基于concept字段去重，保留最高RRF分数的文档"""
    concept_docs = {}

    for doc in docs:
        concept = doc["metadata"].get("concept", "")
        if concept:
            if concept not in concept_docs or doc.get("rrf_score", 0) > concept_docs[concept].get("rrf_score", 0):
                concept_docs[concept] = doc
                # 标记为多源
                if concept in concept_docs:
                    concept_docs[concept]["metadata"]["multi_source"] = True

    return list(concept_docs.values())
```

### 文件位置

**现有文件（已实现）**:
```
C:/Users/ROG/托福/
├── docs/architecture/
│   └── LANGGRAPH-MEMORY-INTEGRATION-DESIGN.md   # Section 10已有完整实现
```

**新创建的文件**:
```
C:/Users/ROG/托福/
├── tests/
│   ├── test_question_router.py
│   ├── test_composite_search.py
│   ├── test_fusion_rerank.py
│   ├── test_agentic_rag_graph.py            # 端到端测试
│   └── fixtures/
│       ├── routing_test_dataset.json        # 100样本路由测试数据
│       └── fusion_test_dataset.json         # 50样本融合测试数据
├── logs/
│   ├── question_router.log                  # 路由决策日志
│   └── agentic_rag_performance.log          # 性能监控日志
└── docs/
    ├── user-guides/
    │   └── graphrag-routing-fusion-guide.md
    ├── architecture/
    │   └── graphrag-routing-fusion-architecture.md
    └── reports/
        ├── performance_routing_fusion_report.md
        └── quality_routing_fusion_report.md
```

### 性能要求

**延迟目标** [Source: Epic AC]

| 检索路径 | P50延迟 | P95延迟 | P99延迟 | 目标 |
|---------|---------|---------|---------|------|
| **Local Path** | <3秒 | **<5秒** | <7秒 | ✅ P95<5秒 |
| **Global Path** | <5秒 | **<8秒** | <10秒 | ✅ P95<8秒 |
| **Hybrid Path** | <8秒 | **<12秒** | <15秒 | ✅ P95<12秒 |

**质量目标** [Source: Epic AC]
- 路由准确率: ≥90%（100次查询中≥90次正确分类）
- 融合去重率: ≥30%（去重文档数 / 总文档数）
- 融合质量提升: ≥15%（NDCG@10指标，vs 单源检索）

### 依赖项

**Python依赖** [Source: requirements.txt]
```
# LangGraph
langgraph>=0.0.20
langchain-core>=0.1.0
langchain-openai>=0.0.5

# RRF Reranker
lancedb[rerankers]>=0.3.0
sentence-transformers>=2.2.0  # CrossEncoder

# 质量评估
scikit-learn>=1.3.0           # NDCG计算
```

**系统依赖**
- **Section 10实现**: LANGGRAPH-MEMORY-INTEGRATION-DESIGN.md Section 10.5.1-10.5.2
- **4层检索工具**: Story GraphRAG.1生成的实体数据 + Story GraphRAG.2的本地模型
- **LLM Provider**: Qwen2.5-14B（本地）+ gpt-4o-mini（路由分类）

### 测试要求

**测试覆盖率目标** [Source: CLAUDE.md#测试规范]
- 单元测试覆盖率: ≥90%
- 集成测试覆盖关键流程: 100%

**关键测试用例**

1. **路由测试**
   - Local查询路由准确性
   - Global查询路由准确性
   - Hybrid查询路由准确性
   - 模糊查询的默认路由
   - 路由置信度计算

2. **Composite Search测试**
   - 4工具全部成功
   - 部分工具失败（2/4成功）
   - 单工具超时
   - 全部工具失败
   - 并行执行延迟

3. **RRF Fusion测试**
   - RRF算法计算准确性
   - 去重逻辑（相同concept合并）
   - 多源证据合并
   - 融合质量提升验证（NDCG@10）

4. **端到端测试**
   - Local路径完整流程
   - Global路径完整流程
   - Hybrid路径完整流程
   - Self-Correction Loop（rewrite → router）

### 故障排查

**问题1: 路由准确率<90%**
- **原因**: Prompt模板不明确或Few-shot示例不足
- **解决**:
  1. 增加Few-shot示例（每种类型3个→10个）
  2. 优化关键词匹配规则
  3. 调整LLM temperature（0→0.1）
  4. 收集错误案例，针对性优化Prompt

**问题2: Hybrid路径延迟>12秒**
- **原因**: 4工具串行执行或单工具延迟过高
- **解决**:
  1. 确保使用asyncio.gather()并行执行
  2. 降低单工具超时（5秒→3秒）
  3. 减少GraphRAG max_data_tokens（8000→6000）
  4. 使用本地模型替代API（降低网络延迟）

**问题3: 融合去重率<30%**
- **原因**: concept字段不一致或去重逻辑错误
- **解决**:
  1. 标准化concept字段（统一大小写、去空格）
  2. 使用模糊匹配（相似度>0.9即视为相同）
  3. 添加别名映射（"逆否命题" = "contrapositive"）

**问题4: Composite Search频繁失败**
- **原因**: 4个工具中某个工具频繁超时或失败
- **解决**:
  1. 识别失败的工具（查看error_log）
  2. 增加该工具的超时时间
  3. 降低该工具的结果数量
  4. 实现降级策略（该工具失败时跳过）

### 监控指标

**关键监控指标** [Source: Epic成功指标]

1. **路由健康度**
   - 路由准确率: ≥90%
   - 路由置信度平均值: ≥0.8
   - Local/Global/Hybrid分布: 40%/30%/30%（预期）

2. **性能指标**
   - Local路径P95延迟: <5秒
   - Global路径P95延迟: <8秒
   - Hybrid路径P95延迟: <12秒
   - 工具执行成功率: ≥95%

3. **质量指标**
   - 融合去重率: ≥30%
   - NDCG@10提升: ≥15%（vs 单源检索）
   - 多源证据覆盖率: ≥40%（文档来自≥2个数据源）

4. **系统健康**
   - Self-Correction触发率: <10%（高质量查询不需要重写）
   - 工具失败率: <5%（单个工具失败比例）

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-01-14 | 1.0 | 初始Story创建，基于LANGGRAPH Section 10现有实现 | SM Agent (Bob) |

## Dev Agent Record

### Agent Model Used
claude-sonnet-4.5 (claude-sonnet-4-5-20250929)

### Debug Log References
待开发

### Completion Notes
待开发

### File List
待开发

## QA Results

### Review Date
待QA审查

### Reviewed By
Quinn (Senior Developer QA)

### Code Quality Assessment
待QA审查

### Compliance Check
待QA审查

### Final Status
In Progress - 等待开发开始，Section 10已有完整实现代码，本Story重点是验证、测试和优化
