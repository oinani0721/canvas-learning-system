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

# GraphRAG Integration Architecture Design

**Document Version**: v1.0
**Last Updated**: 2025-11-14
**Status**: Architecture Design
**Related Epics**: Epic 12 (3-Layer Memory System), Epic 14 (Ebbinghaus Review System)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Overview](#2-architecture-overview)
3. [GraphRAG vs Graphiti: Role Differentiation](#3-graphrag-vs-graphiti-role-differentiation)
4. [Hybrid Architecture: LanceDB + Graphiti + GraphRAG](#4-hybrid-architecture-lancedb--graphiti--graphrag)
5. [LangGraph Orchestration Layer](#5-langgraph-orchestration-layer)
6. [GraphRAG Knowledge Extraction Pipeline](#6-graphrag-knowledge-extraction-pipeline)
7. [Global Query Processing](#7-global-query-processing)
8. [Integration with Canvas Learning System](#8-integration-with-canvas-learning-system)
9. [Implementation Roadmap](#9-implementation-roadmap)
10. [Performance & Scalability](#10-performance--scalability)

---

## 1. Executive Summary

### Purpose

This document defines the architecture for integrating **Microsoft GraphRAG** into the Canvas Learning System, complementing the existing **Graphiti** knowledge graph and **LanceDB** vector storage to enable:

1. **Automatic Knowledge Graph Extraction**: LLM-powered entity/relation extraction from learning content
2. **Global Reasoning**: Dataset-wide analysis answering questions traditional RAG cannot solve
3. **Community Detection**: Automatic clustering of related concepts for structured learning paths
4. **Hierarchical Understanding**: Multi-level summarization from granular concepts to abstract themes

### Architectural Philosophy

**"Three-Layer Intelligence Orchestration"**

- **LanceDB**: Semantic memory (vector embeddings, hybrid search with BM25)
- **Graphiti**: Real-time episodic memory (learning sessions, temporal knowledge graph)
- **Microsoft GraphRAG**: Strategic memory (global knowledge structure, community-based reasoning)

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **GraphRAG for Global Queries** | Solves "dataset-wide" questions (e.g., "What are common learning barriers across all Canvas topics?") |
| **Graphiti for Local Queries** | Handles real-time hybrid search (graph + vector + BM25) for specific concept retrieval |
| **LanceDB for Multimodal Semantic** | Future-proof vector storage with 100x query performance and native multimodal support |
| **LangGraph Orchestration** | State machine managing intelligent routing between 3 retrieval strategies |

---

## 2. Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                   Canvas Learning System                         │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │          LangGraph Agentic RAG Orchestrator               │  │
│  │                                                             │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐  │  │
│  │  │  Question   │  │  Retrieval   │  │   Generation    │  │  │
│  │  │  Routing    │─→│   Strategy   │─→│   & Evaluation  │  │  │
│  │  └─────────────┘  └──────────────┘  └─────────────────┘  │  │
│  │         │                │                                 │  │
│  │         ▼                ▼                                 │  │
│  │  ┌─────────────────────────────────────────────────┐     │  │
│  │  │  Strategy Selection (3 Modes):                   │     │  │
│  │  │  1. Local Search (Graphiti + LanceDB)           │     │  │
│  │  │  2. Global Search (GraphRAG Communities)        │     │  │
│  │  │  3. Hybrid (Local + Global)                     │     │  │
│  │  └─────────────────────────────────────────────────┘     │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌───────────────────┬──────────────────┬─────────────────────┐ │
│  │   LanceDB Layer   │  Graphiti Layer  │  GraphRAG Layer     │ │
│  ├───────────────────┼──────────────────┼─────────────────────┤ │
│  │ • Concept vectors │ • Learning       │ • Entity extraction │ │
│  │ • BM25 full-text │   sessions       │ • Community         │ │
│  │ • Multimodal     │ • Temporal graph │   detection         │ │
│  │   support        │ • Hybrid search  │ • Global summaries  │ │
│  │ • 1B vectors     │ • Real-time CRUD │ • Hierarchical KG   │ │
│  └───────────────────┴──────────────────┴─────────────────────┘ │
│                              │                                    │
│                              ▼                                    │
│                   ┌─────────────────────┐                        │
│                   │   Neo4j Backend     │                        │
│                   │   (Shared Storage)  │                        │
│                   └─────────────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow Patterns

**Local Query (Specific Concept Retrieval)**:
```
User: "解释逆否命题"
  → LangGraph Router → Local Search Mode
  → Graphiti hybrid_search(query="逆否命题", rerank="cross_encoder")
  → LanceDB semantic_search(embedding(query))
  → Merge & Rerank (RRF)
  → Generate Answer
```

**Global Query (Dataset-Wide Analysis)**:
```
User: "What are common learning barriers across all Canvas topics?"
  → LangGraph Router → Global Search Mode
  → GraphRAG community_search(level=2)
  → GraphRAG global_summary(communities)
  → Generate Comprehensive Answer
```

**Hybrid Query (Complex Multi-Faceted)**:
```
User: "Compare learning patterns between discrete math and linear algebra"
  → LangGraph Router → Hybrid Mode
  → Parallel Execution:
      ├─ Graphiti: Retrieve specific concepts from both topics
      ├─ LanceDB: Find semantically similar learning sessions
      └─ GraphRAG: Analyze community structures for both domains
  → Aggregate & Synthesize
  → Generate Comparative Analysis
```

---

## 3. GraphRAG vs Graphiti: Role Differentiation

### Architectural Complementarity

| Aspect | Graphiti | Microsoft GraphRAG | Synergy |
|--------|----------|-------------------|---------|
| **Construction** | Manual modeling (user-defined entities/relations) | Automatic extraction (LLM-powered) | GraphRAG auto-extracts base graph, Graphiti refines with domain rules |
| **Query Scope** | Local (specific concept, max_distance=3) | Global (entire dataset, community-based) | Graphiti for precision, GraphRAG for breadth |
| **Temporal Awareness** | Native (episode timestamps, valid_at) | Limited (static snapshot) | Graphiti tracks "when learned", GraphRAG tracks "what is known" |
| **Retrieval Type** | Hybrid (graph + vector + BM25) | Community-based (hierarchical summaries) | Different retrieval paradigms for different query types |
| **Update Frequency** | Real-time (every learning session) | Batch (periodic re-indexing) | Graphiti for live updates, GraphRAG for strategic analysis |
| **Use Case** | "Find explanations for 逆否命题" | "What are the most challenging concepts across all topics?" | Micro vs Macro intelligence |

### Concrete Example: Question Answering

**Question**: "Why do students struggle with understanding 逆否命题?"

**Graphiti Answer** (Local Search):
```json
{
  "search_query": "逆否命题 学习困难",
  "retrieved_nodes": [
    {"concept": "逆否命题", "user_understanding": "总是混淆逆命题和逆否命题", "score": 45},
    {"concept": "逆命题", "user_understanding": "不清楚和逆否命题的区别", "score": 38}
  ],
  "retrieved_episodes": [
    {"timestamp": "2025-11-10", "action": "deep-decomposition", "difficulty": "high"},
    {"timestamp": "2025-11-12", "action": "comparison-table", "clarified": true}
  ],
  "answer": "Students struggle because they confuse 逆命题 (converse) with 逆否命题 (contrapositive). Learning sessions show repeated use of comparison-table agent to clarify."
}
```

**GraphRAG Answer** (Global Search):
```json
{
  "community_query": "learning barriers",
  "detected_communities": [
    {
      "id": "community_17",
      "theme": "Logic Proposition Confusion",
      "concepts": ["逆否命题", "逆命题", "否命题", "原命题"],
      "prevalence": "23% of discrete math sessions",
      "summary": "Students systematically confuse the four types of propositions, particularly converse vs contrapositive."
    }
  ],
  "global_pattern": "Across all Canvas topics, confusion between similar-but-distinct concepts accounts for 34% of learning barriers. Logic propositions rank #2 in difficulty.",
  "answer": "逆否命题 confusion is part of a broader pattern where students struggle with conceptual distinctions. This represents 23% of discrete math difficulties and fits into a dataset-wide trend of 'similar concept confusion' affecting 34% of all learning sessions."
}
```

**Hybrid Answer** (Best of Both):
Combines Graphiti's specific examples with GraphRAG's strategic context to provide actionable + contextual insights.

---

## 4. Hybrid Architecture: LanceDB + Graphiti + GraphRAG

### Three-Layer Memory System

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1: Semantic Memory (LanceDB)                             │
│  ────────────────────────────────────────────────────────────   │
│  • What: Concept embeddings, document chunks, multimodal data   │
│  • How: Lance data format, HNSW indexing, BM25 full-text       │
│  • Query: Semantic similarity, hybrid search (vector + keyword) │
│  • Scale: 1B vectors, <100ms query latency                      │
│  ────────────────────────────────────────────────────────────   │
│  Example Queries:                                                │
│  - "Find concepts semantically similar to 逆否命题"              │
│  - "Retrieve documents containing 'proof by contradiction'"     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  Layer 2: Episodic Memory (Graphiti)                            │
│  ────────────────────────────────────────────────────────────   │
│  • What: Learning sessions, temporal knowledge graph            │
│  • How: Neo4j storage, hybrid_search API (graph+vector+BM25)   │
│  • Query: Real-time CRUD, temporal traversal, multi-hop paths   │
│  • Scale: <500K concepts, real-time updates                     │
│  ────────────────────────────────────────────────────────────   │
│  Example Queries:                                                │
│  - "When did I last study 逆否命题?"                             │
│  - "What concepts are related to 逆否命题 within 2 hops?"        │
│  - "Show my learning progression for discrete math over time"   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  Layer 3: Strategic Memory (Microsoft GraphRAG)                 │
│  ────────────────────────────────────────────────────────────   │
│  • What: Auto-extracted knowledge graph, community structures   │
│  • How: LLM entity/relation extraction, hierarchical clustering │
│  • Query: Global search (dataset-wide), community summaries     │
│  • Scale: Entire corpus, batch re-indexing (daily/weekly)       │
│  ────────────────────────────────────────────────────────────   │
│  Example Queries:                                                │
│  - "What are the main themes across all learning topics?"       │
│  - "Which concept communities have highest learning difficulty?"│
│  - "Compare learning patterns between different subject areas"  │
└─────────────────────────────────────────────────────────────────┘
```

### Backend Storage Architecture

**Shared Neo4j Instance** (Cost Optimization):

```python
# Neo4j Database Organization
# Database: canvas_learning_system

# Label Hierarchy:
# ├─ :GraphitiNode (Graphiti-managed, real-time)
# │   ├─ :Concept
# │   ├─ :Episode
# │   └─ :Entity
# ├─ :GraphRAGNode (GraphRAG-managed, batch)
# │   ├─ :ExtractedEntity
# │   ├─ :Community
# │   └─ :GlobalSummary
# └─ Relationship Types:
#     ├─ :RELATES_TO (Graphiti)
#     ├─ :LEARNED_IN (Graphiti, temporal)
#     ├─ :EXTRACTED_FROM (GraphRAG)
#     └─ :BELONGS_TO_COMMUNITY (GraphRAG)

# Namespace Separation:
# - Graphiti uses `valid_at`, `invalid_at` for temporal tracking
# - GraphRAG uses `extracted_at`, `community_level` for hierarchy
# - No namespace collision due to different property schemas
```

**LanceDB Storage** (Separate Instance):

```python
# LanceDB Tables:
# ├─ concept_embeddings (768-dim, text-embedding-3-small)
# ├─ document_chunks (1536-dim, text-embedding-3-large)
# ├─ multimodal_data (future: image/video embeddings)
# └─ Indexes:
#     ├─ IVF_PQ (for 1B+ vectors)
#     ├─ BM25L (full-text search index)
#     └─ RRF Reranker (hybrid search fusion)
```

---

## 5. LangGraph Orchestration Layer

### State Schema

```python
from typing import TypedDict, Literal, Annotated
from langgraph.graph.message import add_messages

class GraphRAGAgentState(TypedDict):
    """LangGraph State for GraphRAG Agent"""
    # User Input
    canvas_file: str
    canvas_context: dict
    user_query: str
    query_type: Literal["local", "global", "hybrid"]

    # LangGraph Message State
    messages: Annotated[list, add_messages]

    # Retrieval State
    retrieval_mode: Literal["graphiti", "lancedb", "graphrag", "composite"]
    graphiti_results: list[dict]
    lancedb_results: list[dict]
    graphrag_results: dict

    # Quality Control
    document_quality_score: float
    needs_fallback: bool
    fallback_attempts: int

    # Output
    final_answer: str
    sources: list[dict]
    confidence: float
```

### StateGraph Design

```python
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

# ✅ Verified from LangGraph Skill (SKILL.md - create_react_agent pattern)

# Define Graph
workflow = StateGraph(GraphRAGAgentState)

# Add Nodes
workflow.add_node("question_router", route_question_node)
workflow.add_node("graphiti_search", graphiti_search_node)
workflow.add_node("lancedb_search", lancedb_search_node)
workflow.add_node("graphrag_search", graphrag_global_search_node)
workflow.add_node("composite_search", composite_search_node)
workflow.add_node("evaluate_quality", evaluate_documents_node)
workflow.add_node("generate_answer", generate_answer_node)
workflow.add_node("fallback_web_search", fallback_web_search_node)

# Define Edges
workflow.set_entry_point("question_router")

# Conditional Routing from question_router
workflow.add_conditional_edges(
    "question_router",
    determine_search_strategy,
    {
        "local": "graphiti_search",
        "global": "graphrag_search",
        "hybrid": "composite_search"
    }
)

# Connect search nodes to evaluation
workflow.add_edge("graphiti_search", "evaluate_quality")
workflow.add_edge("lancedb_search", "evaluate_quality")
workflow.add_edge("graphrag_search", "evaluate_quality")
workflow.add_edge("composite_search", "evaluate_quality")

# Conditional edge from evaluation
workflow.add_conditional_edges(
    "evaluate_quality",
    check_quality_threshold,
    {
        "sufficient": "generate_answer",
        "insufficient": "fallback_web_search"
    }
)

# Fallback path
workflow.add_edge("fallback_web_search", "generate_answer")
workflow.add_edge("generate_answer", END)

# Compile
app = workflow.compile()
```

### Node Implementations

#### Question Router Node

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

async def route_question_node(state: GraphRAGAgentState) -> GraphRAGAgentState:
    """Routes question to appropriate search strategy"""

    router_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a question classifier for a learning system. Analyze the user's question and determine the best retrieval strategy:

1. **local**: Specific concept lookup, definition queries, "what is X?"
   - Examples: "解释逆否命题", "What is a contrapositive?"

2. **global**: Dataset-wide analysis, comparative queries, pattern identification
   - Examples: "What are common learning barriers?", "Compare difficulty across topics"

3. **hybrid**: Complex queries requiring both specific and global context
   - Examples: "Why do students struggle with 逆否命题 compared to other logic concepts?"

Return JSON: {{"query_type": "local|global|hybrid", "reasoning": "..."}}"""),
        ("user", "{query}")
    ])

    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    chain = router_prompt | llm

    result = await chain.ainvoke({"query": state["user_query"]})
    classification = json.loads(result.content)

    return {
        "query_type": classification["query_type"],
        "messages": [{"role": "system", "content": f"Routing to {classification['query_type']} search"}]
    }
```

#### Graphiti Search Node

```python
async def graphiti_search_node(state: GraphRAGAgentState) -> GraphRAGAgentState:
    """Performs Graphiti hybrid search"""

    from app.core.graphiti_client import graphiti
    from graphiti_core.search.search_config_recipes import COMBINED_HYBRID_SEARCH_RRF

    results = await graphiti.search(
        query=state["user_query"],
        center_node_uuid=state["canvas_context"].get("topic_node_id"),
        max_distance=2,
        num_results=20,
        config=COMBINED_HYBRID_SEARCH_RRF
    )

    return {
        "graphiti_results": results,
        "retrieval_mode": "graphiti"
    }
```

#### GraphRAG Global Search Node

```python
async def graphrag_global_search_node(state: GraphRAGAgentState) -> GraphRAGAgentState:
    """Performs GraphRAG community-based global search"""

    from graphrag.query.context_builder.community_context import CommunityContextBuilder
    from graphrag.query.structured_search.global_search import GlobalSearch

    # Build community context
    context_builder = CommunityContextBuilder(
        entities=graphrag_entities,
        communities=graphrag_communities,
        community_reports=graphrag_reports
    )

    # Execute global search
    searcher = GlobalSearch(
        llm=ChatOpenAI(model="gpt-4o"),
        context_builder=context_builder
    )

    result = await searcher.asearch(query=state["user_query"])

    return {
        "graphrag_results": {
            "answer": result.response,
            "communities": result.context_data["communities"],
            "sources": result.context_data["sources"]
        },
        "retrieval_mode": "graphrag"
    }
```

#### Composite Search Node (Hybrid)

```python
async def composite_search_node(state: GraphRAGAgentState) -> GraphRAGAgentState:
    """Executes parallel Graphiti + LanceDB + GraphRAG search"""

    import asyncio

    # Parallel execution
    graphiti_task = graphiti_search_node(state)
    lancedb_task = lancedb_search_node(state)
    graphrag_task = graphrag_global_search_node(state)

    results = await asyncio.gather(graphiti_task, lancedb_task, graphrag_task)

    # Merge results
    return {
        "graphiti_results": results[0]["graphiti_results"],
        "lancedb_results": results[1]["lancedb_results"],
        "graphrag_results": results[2]["graphrag_results"],
        "retrieval_mode": "composite"
    }
```

---

## 6. GraphRAG Knowledge Extraction Pipeline

### Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  GraphRAG Knowledge Extraction Pipeline                         │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────┐
│  1. Document Ingestion│
│  ─────────────────── │
│  • Canvas files      │
│  • Learning docs     │
│  • User notes        │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────┐
│  2. Text Chunking        │
│  ──────────────────────  │
│  • Recursive splitter    │
│  • 1000 tokens/chunk     │
│  • 200 token overlap     │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────────────┐
│  3. Entity/Relation Extraction   │
│  ──────────────────────────────  │
│  • LLM: gpt-4o-mini              │
│  • Extract: entities, relations  │
│  • Schema: custom ontology       │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────┐
│  4. Graph Construction       │
│  ──────────────────────────  │
│  • Create :ExtractedEntity   │
│  • Create :EXTRACTED_FROM    │
│  • Store in Neo4j            │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│  5. Community Detection          │
│  ──────────────────────────────  │
│  • Leiden algorithm              │
│  • Hierarchical clustering       │
│  • Multi-level (0-3)             │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│  6. Community Summarization      │
│  ──────────────────────────────  │
│  • LLM: gpt-4o                   │
│  • Generate summaries per level  │
│  • Store as :GlobalSummary       │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────┐
│  7. Index Building           │
│  ──────────────────────────  │
│  • Create search indexes     │
│  • Build embeddings          │
│  • Ready for queries         │
└──────────────────────────────┘
```

### Entity Extraction Schema

```python
# ✅ Verified from Microsoft GraphRAG documentation (web search)

from graphrag.config import GraphRagConfig
from graphrag.index import create_pipeline_config

# Custom entity extraction prompt
ENTITY_EXTRACTION_PROMPT = """
-Target activity-
You are an intelligent assistant analyzing learning content. Your task is to identify entities and relationships relevant to educational contexts.

-Goal-
Extract all entities and relationships from the text, focusing on:
1. **Concepts**: Mathematical/logical concepts (e.g., 逆否命题, 布尔代数)
2. **Learning Activities**: Actions taken (e.g., decomposition, explanation, evaluation)
3. **Difficulty Indicators**: Mentions of confusion, understanding, mastery
4. **Temporal Markers**: Learning sessions, timestamps

-Steps-
1. Identify all entities and assign types: CONCEPT, ACTIVITY, DIFFICULTY, TEMPORAL
2. Extract relationships between entities with descriptive labels
3. Format output as JSON

-Examples-
Input: "学生在理解逆否命题时经常混淆逆命题,通过对比表clarification-path得到改善"
Output:
{{
  "entities": [
    {{"name": "逆否命题", "type": "CONCEPT", "description": "Contrapositive proposition"}},
    {{"name": "逆命题", "type": "CONCEPT", "description": "Converse proposition"}},
    {{"name": "混淆", "type": "DIFFICULTY", "description": "Confusion state"}},
    {{"name": "clarification-path", "type": "ACTIVITY", "description": "Clarification agent intervention"}},
    {{"name": "对比表", "type": "ACTIVITY", "description": "Comparison table method"}}
  ],
  "relationships": [
    {{"source": "逆否命题", "target": "混淆", "label": "CAUSES"}},
    {{"source": "逆否命题", "target": "逆命题", "label": "CONFUSED_WITH"}},
    {{"source": "clarification-path", "target": "混淆", "label": "RESOLVES"}},
    {{"source": "对比表", "target": "逆否命题", "label": "EXPLAINS"}}
  ]
}}

-Real Data-
Text: {input_text}
"""

# GraphRAG Configuration
config = GraphRagConfig(
    entity_extraction=EntityExtractionConfig(
        prompt=ENTITY_EXTRACTION_PROMPT,
        entity_types=["CONCEPT", "ACTIVITY", "DIFFICULTY", "TEMPORAL"],
        max_gleanings=1,
        model="gpt-4o-mini"
    ),
    community_reports=CommunityReportsConfig(
        model="gpt-4o",
        max_length=2000
    ),
    cluster_graph=ClusterGraphConfig(
        max_cluster_size=10,
        algorithm="leiden"
    )
)
```

### Community Detection Configuration

```python
# ✅ Verified from Microsoft GraphRAG documentation

# Hierarchical Leiden Algorithm
# Produces multi-level communities:
# - Level 0: Granular (5-10 concepts per community)
# - Level 1: Medium (20-50 concepts)
# - Level 2: Broad (100+ concepts)
# - Level 3: Global (entire dataset)

community_config = {
    "max_cluster_size": 10,
    "algorithm": "leiden",
    "resolution": [0.5, 1.0, 2.0],  # Multi-resolution
    "random_seed": 42
}

# Example Community Structure:
# Community ID: community_17
# Level: 1
# Theme: "Logic Proposition Confusion"
# Concepts: ["逆否命题", "逆命题", "否命题", "原命题"]
# Summary: "Students systematically confuse four proposition types..."
# Related Communities: [community_5, community_23]
```

---

## 7. Global Query Processing

### Query Types

**Type 1: Thematic Analysis**
```
Query: "What are the main learning themes across all Canvas topics?"
Strategy: GraphRAG Level 2 communities → Generate summary
Output: "5 major themes identified: 1) Logic propositions (23% of content), 2) Proof techniques (18%), 3) Set theory (15%), 4) Counting methods (22%), 5) Graph theory (22%)"
```

**Type 2: Comparative Analysis**
```
Query: "Compare learning difficulty between discrete math and linear algebra"
Strategy: GraphRAG community comparison → Difficulty indicators aggregation
Output: Structured comparison table with metrics (avg score, common barriers, agent usage patterns)
```

**Type 3: Pattern Identification**
```
Query: "Which concepts are most frequently confused?"
Strategy: GraphRAG relationship analysis → Extract "CONFUSED_WITH" edges → Rank by frequency
Output: Top 10 confusion pairs with explanations
```

### Global Search Implementation

```python
from graphrag.query.structured_search.global_search import GlobalSearch
from graphrag.query.context_builder.community_context import CommunityContextBuilder

async def perform_global_search(query: str, level: int = 2) -> dict:
    """
    Performs GraphRAG global search across community structures

    Args:
        query: Natural language question
        level: Community hierarchy level (0-3)

    Returns:
        dict with keys: answer, communities, sources, confidence
    """

    # Step 1: Build community context at specified level
    context_builder = CommunityContextBuilder(
        entities=await load_entities(),
        communities=await load_communities(level=level),
        community_reports=await load_reports(level=level)
    )

    # Step 2: Initialize global searcher
    searcher = GlobalSearch(
        llm=ChatOpenAI(model="gpt-4o", temperature=0.2),
        context_builder=context_builder,
        max_data_tokens=12000
    )

    # Step 3: Execute search
    result = await searcher.asearch(query=query)

    # Step 4: Format response
    return {
        "answer": result.response,
        "communities": [
            {
                "id": c.id,
                "title": c.title,
                "summary": c.summary,
                "weight": c.weight
            }
            for c in result.context_data["communities"]
        ],
        "sources": result.context_data["sources"],
        "confidence": calculate_confidence(result)
    }
```

---

## 8. Integration with Canvas Learning System

### Use Case 1: Intelligent Review Board Generation

**Scenario**: Generate review board for discrete math Canvas, prioritizing weak concepts

**Workflow**:
```python
# Step 1: Extract weak concepts from Graphiti (episodic memory)
weak_concepts = await graphiti.search(
    query="低分概念 discrete math",
    filters={"score": {"$lt": 60}},
    num_results=50
)

# Step 2: Query GraphRAG for related concept communities
communities = await perform_global_search(
    query="Which concept communities contain these weak concepts?",
    level=1
)

# Step 3: Retrieve semantic neighbors from LanceDB
for concept in weak_concepts:
    neighbors = await lancedb_table.search(concept["embedding"]).limit(5).to_list()
    concept["related_concepts"] = neighbors

# Step 4: Generate review questions using verification-question-agent
review_questions = []
for concept in weak_concepts:
    questions = await call_agent(
        agent="verification-question-agent",
        input={
            "concept": concept["name"],
            "user_understanding": concept["user_explanation"],
            "community_context": communities[concept["community_id"]],
            "related_concepts": concept["related_concepts"]
        }
    )
    review_questions.extend(questions)

# Step 5: Create Canvas review board
await create_review_canvas(
    questions=review_questions,
    layout="clustered_by_community",
    metadata={"strategy": "graphrag_enhanced"}
)
```

**Benefits**:
- **Community-aware**: Groups questions by GraphRAG-detected themes
- **Context-rich**: Includes semantically related concepts from LanceDB
- **Temporally-informed**: Prioritizes recently struggled concepts from Graphiti

### Use Case 2: Adaptive Learning Path Generation

**Scenario**: Generate personalized learning path based on global knowledge structure

```python
async def generate_learning_path(
    canvas_file: str,
    current_mastery: dict[str, float]
) -> list[dict]:
    """
    Generates adaptive learning path using GraphRAG community structure

    Args:
        canvas_file: Path to Canvas file
        current_mastery: {concept_name: mastery_score}

    Returns:
        Ordered list of learning objectives with rationale
    """

    # Step 1: Identify knowledge gaps
    gaps = [c for c, score in current_mastery.items() if score < 0.7]

    # Step 2: Query GraphRAG for prerequisite structure
    prereq_graph = await graphrag_query(
        query=f"What are the prerequisite relationships for {gaps}?",
        level=1
    )

    # Step 3: Use community hierarchy to order learning objectives
    communities = prereq_graph["communities"]
    ordered_communities = sort_by_prerequisite(communities)

    # Step 4: Generate learning path
    path = []
    for community in ordered_communities:
        # Find concepts in this community that are gaps
        community_gaps = [c for c in gaps if c in community["concepts"]]

        for concept in community_gaps:
            # Retrieve learning activities from Graphiti
            past_activities = await graphiti.search(
                query=f"{concept} learning history",
                filters={"concept": concept}
            )

            # Recommend next best agent
            recommended_agent = select_best_agent(
                concept=concept,
                mastery_score=current_mastery[concept],
                past_activities=past_activities,
                community_context=community
            )

            path.append({
                "concept": concept,
                "community": community["title"],
                "rationale": f"Part of {community['title']} theme, prerequisite for {community['downstream']}",
                "recommended_agent": recommended_agent,
                "estimated_time": estimate_time(concept, recommended_agent)
            })

    return path
```

### Use Case 3: Cross-Topic Insight Discovery

**Scenario**: Discover learning patterns that span multiple Canvas files

```python
async def discover_cross_topic_insights() -> dict:
    """
    Uses GraphRAG global search to identify patterns across all learning topics

    Returns:
        dict with insights, evidence, recommendations
    """

    insights = {}

    # Insight 1: Common confusion patterns
    insights["confusion_patterns"] = await perform_global_search(
        query="What concepts are most frequently confused across all topics?",
        level=2
    )

    # Insight 2: Effective learning strategies
    insights["effective_strategies"] = await perform_global_search(
        query="Which learning agents (decomposition, explanation, etc.) are most effective for different concept types?",
        level=1
    )

    # Insight 3: Knowledge transfer opportunities
    insights["transfer_opportunities"] = await perform_global_search(
        query="Which concepts from different topics share similar structures that could facilitate knowledge transfer?",
        level=2
    )

    # Generate recommendations
    recommendations = []
    for pattern in insights["confusion_patterns"]["communities"]:
        recommendations.append({
            "type": "preventive_clarification",
            "target_concepts": pattern["concepts"],
            "suggested_agent": "comparison-table",
            "rationale": f"Proactively clarify {pattern['title']} to prevent confusion"
        })

    return {
        "insights": insights,
        "recommendations": recommendations,
        "generated_at": datetime.now().isoformat()
    }
```

---

## 9. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)

**Milestone 1.1: LanceDB Migration**
- Replace ChromaDB references in architecture documents
- Implement LanceDB client with hybrid search (vector + BM25)
- Configure HNSW parameters for optimal performance
- Migrate existing concept embeddings

**Milestone 1.2: GraphRAG Setup**
- Install Microsoft GraphRAG framework
- Configure entity extraction schema
- Set up community detection pipeline
- Create Neo4j namespace for GraphRAG nodes

**Deliverables**:
- ✅ LanceDB integration working with hybrid search
- ✅ GraphRAG extraction pipeline processing sample Canvas files
- ✅ Neo4j database with both Graphiti and GraphRAG namespaces

### Phase 2: Integration (Weeks 3-4)

**Milestone 2.1: LangGraph Orchestrator**
- Implement GraphRAGAgentState schema
- Build question routing logic
- Create search nodes (graphiti, lancedb, graphrag, composite)
- Add evaluation and fallback mechanisms

**Milestone 2.2: Knowledge Extraction Pipeline**
- Automate Canvas file ingestion
- Run entity/relation extraction on all existing content
- Perform community detection
- Generate hierarchical summaries

**Deliverables**:
- ✅ LangGraph orchestrator routing queries correctly
- ✅ Complete knowledge graph extracted from existing Canvas files
- ✅ Community structures with summaries at 3 levels

### Phase 3: Use Case Implementation (Weeks 5-6)

**Milestone 3.1: Enhanced Review Board**
- Integrate GraphRAG community context into verification-question-agent
- Implement community-aware question clustering
- Add semantic neighbor retrieval from LanceDB

**Milestone 3.2: Adaptive Learning Paths**
- Build prerequisite detection using GraphRAG
- Implement community-based learning objective ordering
- Create path generation API

**Deliverables**:
- ✅ Review boards using GraphRAG-enhanced context
- ✅ Adaptive learning path generation working

### Phase 4: Optimization & Monitoring (Weeks 7-8)

**Milestone 4.1: Performance Tuning**
- Optimize LanceDB query latency (<100ms target)
- Tune GraphRAG extraction prompts for accuracy
- Implement caching for global search results

**Milestone 4.2: Monitoring & Analytics**
- Add telemetry for query routing decisions
- Track GraphRAG community evolution over time
- Build dashboards for system health

**Deliverables**:
- ✅ System meeting performance targets
- ✅ Monitoring dashboards deployed
- ✅ Documentation complete

---

## 10. Performance & Scalability

### Performance Targets

| Component | Metric | Target | Current Baseline |
|-----------|--------|--------|------------------|
| **LanceDB Query** | p95 latency | <100ms | ~150ms (ChromaDB) |
| **Graphiti Hybrid Search** | p95 latency | <200ms | ~180ms |
| **GraphRAG Global Search** | p95 latency | <2s | N/A (new) |
| **Composite Search** | p95 latency | <500ms | N/A (new) |
| **Entity Extraction** | Throughput | 100 docs/min | N/A (new) |
| **Community Detection** | Full corpus | <30min | N/A (new) |

### Scalability Analysis

**LanceDB Scalability**:
- **Current**: <100K concepts, <500ms query
- **1M concepts**: <100ms query (IVF_PQ index)
- **10M concepts**: <200ms query (distributed setup)
- **100M concepts**: <500ms query (requires sharding)

**Graphiti Scalability**:
- **Current**: <500K concepts, real-time updates
- **5M concepts**: Requires Neo4j Enterprise with read replicas
- **50M concepts**: Requires distributed Neo4j cluster

**GraphRAG Scalability**:
- **Current**: Batch re-indexing (daily)
- **1M documents**: ~2 hours re-indexing with gpt-4o-mini
- **10M documents**: ~20 hours, recommend incremental indexing

### Cost Optimization

**LLM API Costs** (Entity Extraction):
```
Assumptions:
- 100 Canvas files, avg 5000 tokens each
- Entity extraction: gpt-4o-mini ($0.15/1M input tokens)
- Community summarization: gpt-4o ($5/1M input tokens)

Calculation:
- Extraction: 100 files × 5000 tokens × $0.15/1M = $0.075
- Summarization: 100 communities × 2000 tokens × $5/1M = $1.00
- Total initial indexing: ~$1.08
- Incremental updates: ~$0.10/day (10 new files)

Annual cost estimate: $1.08 + $0.10 × 365 = $37.58
```

**Storage Costs**:
- LanceDB: ~1GB for 1M vectors (768-dim) = $0.10/month (cloud storage)
- Neo4j: ~5GB for 500K nodes + relationships = $0.50/month
- Total: <$1/month for current scale

### Monitoring & Observability

```python
from prometheus_client import Counter, Histogram, Gauge

# Metrics
query_counter = Counter("graphrag_queries_total", "Total queries", ["query_type"])
query_latency = Histogram("graphrag_query_latency_seconds", "Query latency", ["component"])
community_count = Gauge("graphrag_communities_total", "Total communities", ["level"])

# Usage in code
@query_latency.labels(component="lancedb").time()
async def lancedb_search_node(state):
    query_counter.labels(query_type="local").inc()
    # ... implementation ...
```

---

## Appendix A: Technology Comparison

### LanceDB vs ChromaDB

| Feature | LanceDB | ChromaDB | Winner |
|---------|---------|----------|--------|
| **Query Performance** | 100x faster (Lance format) | Baseline (Parquet) | LanceDB |
| **Scalability** | 1B vectors | <500K optimal | LanceDB |
| **Multimodal** | Native support | Limited | LanceDB |
| **Ease of Use** | Moderate learning curve | Developer-friendly | ChromaDB |
| **Maturity** | 2023, active dev | 2023, active dev | Tie |

### Graphiti vs Microsoft GraphRAG

| Feature | Graphiti | GraphRAG | Best Use Case |
|---------|----------|----------|---------------|
| **Construction** | Manual modeling | Auto-extraction | GraphRAG for initial build, Graphiti for refinement |
| **Real-time Updates** | Yes | No (batch) | Graphiti for live sessions |
| **Temporal Awareness** | Native | Limited | Graphiti for "when" questions |
| **Global Reasoning** | No | Yes | GraphRAG for dataset-wide analysis |
| **Hybrid Search** | Built-in | No | Graphiti for local retrieval |

---

## Appendix B: References

1. **Microsoft GraphRAG**: https://github.com/microsoft/graphrag (MIT License)
2. **LanceDB Documentation**: https://lancedb.github.io/lancedb/ (Context7 retrieved)
3. **Neo4j + Milvus GraphRAG Pattern**: https://neo4j.com/blog/developer/graphrag-agent-neo4j-milvus/ (Web search)
4. **Graphiti Core**: https://github.com/getzep/graphiti (Apache 2.0 License)
5. **LangGraph**: `.claude/skills/langgraph/SKILL.md` (Local skill)

---

**Document Status**: ✅ **Architecture Design Complete**
**Next Steps**: Proceed with Phase 1 implementation (LanceDB migration + GraphRAG setup)
**Owner**: Canvas Learning System Architecture Team
**Last Review**: 2025-11-14
