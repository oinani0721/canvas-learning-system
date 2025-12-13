# Epic 23: RAG智能推理系统

---
epic_id: EPIC-23
title: "RAG智能推理系统"
status: planned
priority: P1
created: 2025-12-11
estimated_stories: 4
related_bugs: [Bug-7]
dependencies: [EPIC-22]
---

## 1. 问题概述

### 1.1 Bug描述

**Bug 7: Agentic RAG不工作**

当前系统的RAG (Retrieval-Augmented Generation) 功能完全失效，导致：
- Agent无法获取相关的学习历史上下文
- 检验白板生成缺少知识图谱支持
- 多源信息融合不可用

### 1.2 根因分析

```python
# backend/app/services/rag_service.py
try:
    from agentic_rag import canvas_agentic_rag, CanvasRAGConfig
    LANGGRAPH_AVAILABLE = True
except ImportError as e:
    LANGGRAPH_AVAILABLE = False  # ❌ 所有RAG调用失败
    _IMPORT_ERROR = str(e)
```

**根因链路**:
```
src/agentic_rag 模块导入失败
    ↓
LANGGRAPH_AVAILABLE = False
    ↓
RAGService.query() 返回空结果或抛出异常
    ↓
所有依赖RAG的功能失效
```

### 1.3 具体问题

| 问题 | 描述 | 影响 |
|------|------|------|
| **LangGraph导入失败** | `agentic_rag` 模块依赖未满足 | RAG完全不可用 |
| **Embedding Pipeline缺失** | LanceDB向量化流程未配置 | 语义检索失败 |
| **StateGraph配置问题** | 节点函数或边配置错误 | Graph编译失败 |
| **多源融合未连接** | Graphiti/LanceDB/Multimodal未集成 | 检索结果不完整 |

---

## 2. 技术架构

### 2.1 RAG系统架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                        RAG Service (FastAPI)                         │
│                              ↓                                       │
│                    canvas_agentic_rag                                │
│                     (LangGraph StateGraph)                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐          │
│  │  Graphiti   │  │  LanceDB    │  │   Multimodal        │          │
│  │  (时序图谱)  │  │  (向量检索)  │  │  (图像+文本检索)    │          │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘          │
│         │                 │                    │                     │
│         └─────────────────┼────────────────────┘                     │
│                           ↓                                          │
│                    ┌───────────────┐                                 │
│                    │ 融合算法      │                                 │
│                    │ (RRF/Weighted)│                                 │
│                    └───────┬───────┘                                 │
│                            ↓                                         │
│                    ┌───────────────┐                                 │
│                    │ Reranking     │                                 │
│                    │ (Local/Cohere)│                                 │
│                    └───────┬───────┘                                 │
│                            ↓                                         │
│                    ┌───────────────┐                                 │
│                    │ 质量控制      │                                 │
│                    │ (Query重写)   │                                 │
│                    └───────────────┘                                 │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 StateGraph流程

```
         START
           │
           ▼
    ┌─────────────┐
    │  fan_out    │ ─── Send to parallel retrieval
    └─────────────┘
           │
     ┌─────┼─────┐
     ↓     ↓     ↓
┌────────┐ ┌────────┐ ┌─────────────┐
│Graphiti│ │LanceDB │ │ Multimodal  │
└───┬────┘ └───┬────┘ └──────┬──────┘
    └──────────┼─────────────┘
               ↓
         ┌───────────┐
         │   Fuse    │
         └─────┬─────┘
               ↓
         ┌───────────┐
         │  Rerank   │
         └─────┬─────┘
               ↓
         ┌───────────┐      low quality
         │  Quality  │ ─────────────────→ rewrite_query ──→ START
         │  Check    │
         └─────┬─────┘
               │ medium/high quality
               ↓
              END
```

### 2.3 现有代码结构

```
src/agentic_rag/
├── __init__.py              # 模块入口 (导入问题所在)
├── state.py                 # CanvasRAGState定义
├── config.py                # CanvasRAGConfig定义
├── state_graph.py           # LangGraph StateGraph构建
├── nodes.py                 # 检索/融合/Rerank节点
├── clients/
│   ├── lancedb_client.py    # LanceDB向量库客户端
│   ├── graphiti_client.py   # Graphiti图谱客户端
│   └── temporal_client.py   # 时序记忆客户端
├── fusion/
│   ├── rrf_fusion.py        # RRF融合算法
│   ├── weighted_fusion.py   # 加权融合算法
│   └── cascade_retrieval.py # 级联检索
├── quality/
│   ├── quality_checker.py   # 质量评估
│   └── query_rewriter.py    # Query重写
├── retrievers/
│   └── multimodal_retriever.py  # 多模态检索
└── processors/
    ├── multimodal_vectorizer.py # 多模态向量化
    └── pdf_processor.py     # PDF处理
```

---

## 3. Stories

### Story 23.1: LangGraph导入问题修复

**优先级**: P0 (Critical)
**估计**: 2 Story Points

#### 描述

修复 `src/agentic_rag` 模块的导入问题，确保 `LANGGRAPH_AVAILABLE = True`。

#### 根因

1. **依赖缺失**: `langgraph`, `lancedb`, `langchain` 可能未安装或版本不兼容
2. **循环导入**: 模块间可能存在循环导入
3. **路径问题**: `sys.path` 可能未正确配置

#### 验收标准 (AC)

- [ ] AC 1: `from agentic_rag import canvas_agentic_rag` 成功
- [ ] AC 2: `LANGGRAPH_AVAILABLE = True` 在 `rag_service.py` 中
- [ ] AC 3: 所有依赖版本记录在 `requirements.txt`
- [ ] AC 4: 添加导入诊断日志

#### 技术任务

1. 检查 `requirements.txt` 依赖完整性
2. 验证 langgraph, lancedb, langchain 版本兼容性
3. 修复 `__init__.py` 中可能的导入顺序问题
4. 添加 fallback 导入机制
5. 编写导入测试用例

#### 关键文件

- `src/agentic_rag/__init__.py`
- `backend/requirements.txt`
- `backend/app/services/rag_service.py`

---

### Story 23.2: LanceDB Embedding Pipeline

**优先级**: P0 (Critical)
**估计**: 3 Story Points

#### 描述

实现完整的LanceDB向量化流程，支持Canvas节点内容的语义检索。

#### 当前状态

- `lancedb_client.py` 存在但可能未正确配置
- Embedding模型未指定
- 向量化pipeline未连接

#### 验收标准 (AC)

- [ ] AC 1: 支持文本内容向量化
- [ ] AC 2: 支持Canvas节点批量索引
- [ ] AC 3: 支持语义相似度查询
- [ ] AC 4: 向量维度和模型可配置
- [ ] AC 5: 索引持久化到本地文件

#### 技术任务

1. 选择Embedding模型 (sentence-transformers/all-MiniLM-L6-v2)
2. 实现 `LanceDBClient.embed()` 方法
3. 实现 `LanceDBClient.index_canvas()` 方法
4. 实现 `LanceDBClient.search()` 方法
5. 添加批量处理支持
6. 编写集成测试

#### 关键文件

- `src/agentic_rag/clients/lancedb_client.py`
- `src/agentic_rag/processors/multimodal_vectorizer.py`
- 新建: `backend/data/lancedb/` 目录

#### 配置示例

```python
# config.py
LANCEDB_CONFIG = {
    "db_path": "backend/data/lancedb",
    "table_name": "canvas_nodes",
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "embedding_dim": 384,
    "batch_size": 100,
}
```

---

### Story 23.3: StateGraph智能推理链配置

**优先级**: P1 (High)
**估计**: 3 Story Points

#### 描述

修复并验证LangGraph StateGraph的完整配置，确保图能够正确编译和执行。

#### 当前状态

- `state_graph.py` 已存在基本结构
- 节点函数可能存在运行时错误
- 边配置可能不完整

#### 验收标准 (AC)

- [ ] AC 1: `canvas_agentic_rag.compile()` 成功
- [ ] AC 2: 并行检索 (Send模式) 正常工作
- [ ] AC 3: 融合算法可切换 (RRF/Weighted/Cascade)
- [ ] AC 4: 质量控制循环正常工作
- [ ] AC 5: 端到端测试通过

#### 技术任务

1. 验证所有节点函数签名与State兼容
2. 修复 `fan_out_retrieval` Send配置
3. 验证条件边 `route_after_quality_check`
4. 添加节点执行日志
5. 编写StateGraph单元测试
6. 编写端到端集成测试

#### 关键文件

- `src/agentic_rag/state_graph.py`
- `src/agentic_rag/state.py`
- `src/agentic_rag/nodes.py`

#### 测试用例

```python
def test_stategraph_compile():
    """验证StateGraph编译成功"""
    from agentic_rag import canvas_agentic_rag
    assert canvas_agentic_rag is not None
    # Graph应该已编译

def test_parallel_retrieval():
    """验证并行检索"""
    result = canvas_agentic_rag.invoke({
        "messages": [("user", "什么是逆否命题？")]
    })
    assert "graphiti_results" in result
    assert "lancedb_results" in result
```

---

### Story 23.4: 多源融合 (教材+历史+跨Canvas)

**优先级**: P1 (High)
**估计**: 4 Story Points

#### 描述

实现多源信息融合，将教材上下文、学习历史、跨Canvas关联整合到RAG检索中。

#### 数据源

| 数据源 | 存储 | 用途 |
|--------|------|------|
| **教材上下文** | TextbookContextService | PDF/笔记内容 |
| **学习历史** | Graphiti/Neo4j | 概念关系+时序记忆 |
| **跨Canvas** | CrossCanvasService | 关联Canvas节点 |
| **当前Canvas** | LanceDB | 当前Canvas语义检索 |

#### 验收标准 (AC)

- [ ] AC 1: RAG支持教材上下文注入
- [ ] AC 2: RAG支持学习历史检索
- [ ] AC 3: RAG支持跨Canvas关联
- [ ] AC 4: 支持数据源权重配置
- [ ] AC 5: 融合结果包含来源标注

#### 技术任务

1. 扩展 `CanvasRAGState` 支持多源输入
2. 实现 `TextbookRetriever` 节点
3. 实现 `CrossCanvasRetriever` 节点
4. 修改融合算法支持4路输入
5. 添加来源元数据到结果
6. 编写多源融合测试

#### 关键文件

- `src/agentic_rag/state.py` (扩展State)
- `src/agentic_rag/state_graph.py` (添加新节点)
- `src/agentic_rag/nodes.py` (新检索节点)
- `backend/app/services/textbook_context_service.py`
- `backend/app/services/cross_canvas_service.py`

#### 架构变更

```python
# 扩展State
class CanvasRAGState(MessagesState):
    # 现有字段...
    graphiti_results: List[SearchResult]
    lancedb_results: List[SearchResult]

    # 新增字段
    textbook_results: List[SearchResult]      # 教材检索结果
    cross_canvas_results: List[SearchResult]  # 跨Canvas检索结果
```

```python
# 扩展fan_out
def fan_out_retrieval(state: CanvasRAGState) -> list[Send]:
    return [
        Send("retrieve_graphiti", state),
        Send("retrieve_lancedb", state),
        Send("retrieve_multimodal", state),
        Send("retrieve_textbook", state),       # 新增
        Send("retrieve_cross_canvas", state),   # 新增
    ]
```

---

## 4. 依赖关系

### 4.1 Epic依赖

```
Epic 22 (记忆系统) ──→ Epic 23 (RAG)
    │                     │
    │  Neo4j/Graphiti     │  需要Graphiti客户端
    │  TemporalClient     │  需要时序记忆
    │                     │
    └─────────────────────┘
```

### 4.2 Story依赖

```
Story 23.1 ──→ Story 23.2 ──→ Story 23.3 ──→ Story 23.4
(导入修复)    (Embedding)    (StateGraph)   (多源融合)
```

---

## 5. 风险评估

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| LangGraph版本不兼容 | 中 | 高 | 锁定版本，添加版本检查 |
| Embedding模型下载失败 | 低 | 中 | 提供离线模型路径配置 |
| LanceDB性能问题 | 中 | 中 | 添加索引优化和缓存 |
| 多源融合复杂度 | 高 | 中 | 分阶段实现，先2源后4源 |

---

## 6. 测试策略

### 6.1 单元测试

- `test_langgraph_import.py` - 导入测试
- `test_lancedb_client.py` - 向量库测试
- `test_stategraph.py` - StateGraph测试
- `test_fusion.py` - 融合算法测试

### 6.2 集成测试

- `test_rag_e2e.py` - 端到端RAG流程
- `test_multi_source.py` - 多源融合测试

### 6.3 性能测试

- 检索延迟 < 500ms (单源)
- 检索延迟 < 1000ms (多源融合)
- 支持100+节点索引

---

## 7. 完成标准

- [ ] 所有4个Stories完成
- [ ] `LANGGRAPH_AVAILABLE = True`
- [ ] StateGraph编译成功
- [ ] 端到端RAG查询正常工作
- [ ] 多源融合返回标注来源
- [ ] 测试覆盖率 > 80%
- [ ] 文档更新完成

---

## 8. 参考资料

- [LangGraph Skill](/.claude/skills/langgraph/SKILL.md) - StateGraph模式
- [Graphiti Skill](/.claude/skills/graphiti/SKILL.md) - 时序知识图谱
- [src/agentic_rag/](../../../src/agentic_rag/) - 现有RAG代码
- [Epic 22](./EPIC-22-MEMORY-SYSTEM-NEO4J-GRAPHITI.md) - 记忆系统依赖
