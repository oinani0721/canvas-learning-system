# Agentic RAG API 文档

## 概述

Epic 12的Agentic RAG提供了增强的检索能力，通过LangGraph编排多源并行检索、智能融合和质量控制。

**核心特性**:
- 多源并行检索 (Graphiti + LanceDB)
- 3种融合策略 (RRF, Weighted, Cascade)
- 混合Reranking (Cohere + Local)
- 自适应质量控制循环
- 完整LangSmith追踪

---

## 核心API

### `canvas_agentic_rag.ainvoke()`

异步调用Agentic RAG检索。这是主要的入口点。

**签名**:
```python
async def ainvoke(
    input: Dict[str, Any],
    config: Optional[RunnableConfig] = None
) -> Dict[str, Any]
```

**请求格式**:
```python
from src.agentic_rag.state_graph import canvas_agentic_rag

result = await canvas_agentic_rag.ainvoke({
    # 必填参数
    "query": "什么是逆否命题?",

    # 可选参数
    "canvas_file": "离散数学.canvas",      # Canvas文件路径
    "is_review_mode": False,               # 复习模式
    "fusion_strategy": "rrf",              # 融合策略: rrf, weighted, cascade
    "reranking_strategy": "local",         # Reranking策略: local, cohere
    "top_k": 10,                           # 返回结果数量
    "quality_threshold": 0.6,              # 质量阈值
    "max_rewrites": 2,                     # 最大Query重写次数
})
```

**响应格式**:
```python
{
    # 原始查询
    "query": "什么是逆否命题?",
    "rewritten_query": "逆否命题的定义和性质",  # 重写后的查询（如有）

    # 检索结果
    "graphiti_results": [
        {
            "id": "concept_123",
            "name": "逆否命题",
            "content": "若原命题为p→q，则逆否命题为¬q→¬p",
            "score": 0.95,
            "source": "graphiti",
            "metadata": {
                "node_type": "Concept",
                "last_accessed": "2025-11-28T10:00:00Z"
            }
        },
        # ...
    ],

    "lancedb_results": [
        {
            "id": "vec_456",
            "content": "逆否命题与原命题等价...",
            "score": 0.88,
            "source": "lancedb",
            "metadata": {
                "canvas_file": "离散数学.canvas",
                "node_id": "node_789"
            }
        },
        # ...
    ],

    # 融合后结果
    "fused_results": [
        {
            "id": "concept_123",
            "content": "若原命题为p→q，则逆否命题为¬q→¬p",
            "fused_score": 0.92,
            "sources": ["graphiti", "lancedb"],
            "fusion_method": "rrf"
        },
        # ...
    ],

    # Reranking后结果
    "reranked_results": [
        {
            "id": "concept_123",
            "content": "若原命题为p→q，则逆否命题为¬q→¬p",
            "final_score": 0.95,
            "rerank_method": "cohere"
        },
        # ...
    ],

    # 元数据
    "quality_score": 0.85,           # 最终质量分数
    "latency_ms": 320,               # 总延迟(ms)
    "rewrite_count": 0,              # Query重写次数
    "cost_usd": 0.002,               # 本次请求成本

    # 追踪信息
    "trace_id": "abc123",            # LangSmith trace ID
    "run_id": "def456"               # LangGraph run ID
}
```

---

### `canvas_agentic_rag.invoke()`

同步版本，适用于不使用async的场景。

**签名**:
```python
def invoke(
    input: Dict[str, Any],
    config: Optional[RunnableConfig] = None
) -> Dict[str, Any]
```

**使用方式**:
```python
result = canvas_agentic_rag.invoke({
    "query": "什么是逆否命题?"
})
```

---

### `canvas_agentic_rag.stream()`

流式返回中间结果，适用于需要展示进度的场景。

**签名**:
```python
def stream(
    input: Dict[str, Any],
    config: Optional[RunnableConfig] = None
) -> Iterator[Dict[str, Any]]
```

**使用方式**:
```python
for event in canvas_agentic_rag.stream({"query": "逆否命题"}):
    node_name = event.get("node")
    data = event.get("data")
    print(f"[{node_name}] {data}")
```

**事件格式**:
```python
# 并行检索完成
{"node": "parallel_retrieval", "data": {"graphiti_count": 5, "lancedb_count": 8}}

# 融合完成
{"node": "fusion", "data": {"method": "rrf", "result_count": 10}}

# Reranking完成
{"node": "reranking", "data": {"method": "cohere", "top_score": 0.95}}

# 质量评估
{"node": "quality_control", "data": {"score": 0.85, "passed": True}}

# 最终结果
{"node": "output", "data": {"result_count": 10, "latency_ms": 320}}
```

---

## 融合策略API

### RRF (Reciprocal Rank Fusion)

**适用场景**: 通用检索，平衡不同来源

```python
from src.agentic_rag.fusion import RRFFusion

fusion = RRFFusion(k=60)  # k是调节参数
fused = fusion.fuse(graphiti_results, lancedb_results)
```

**参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| k | int | 60 | RRF常数，值越大，排名差异影响越小 |

### Weighted Fusion

**适用场景**: 检验白板生成，需要强调薄弱点

```python
from src.agentic_rag.fusion import WeightedFusion

fusion = WeightedFusion(
    graphiti_weight=0.7,  # 薄弱点来源权重
    lancedb_weight=0.3
)
fused = fusion.fuse(graphiti_results, lancedb_results)
```

**参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| graphiti_weight | float | 0.7 | Graphiti结果权重 |
| lancedb_weight | float | 0.3 | LanceDB结果权重 |

### Cascade Fusion

**适用场景**: 高精度需求，分层过滤

```python
from src.agentic_rag.fusion import CascadeFusion

fusion = CascadeFusion(
    primary_threshold=0.8,  # 主源阈值
    secondary_threshold=0.6  # 次源阈值
)
fused = fusion.fuse(graphiti_results, lancedb_results)
```

**参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| primary_threshold | float | 0.8 | 主源通过阈值 |
| secondary_threshold | float | 0.6 | 次源通过阈值 |

---

## Reranking API

### Cohere Reranking

**适用场景**: 高质量场景（检验白板生成）

```python
from src.agentic_rag.reranking import CohereReranker

reranker = CohereReranker(
    model="rerank-english-v3.0",
    top_n=10
)
reranked = await reranker.rerank(query, documents)
```

**参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| model | str | "rerank-english-v3.0" | Cohere模型 |
| top_n | int | 10 | 返回数量 |

**成本**: ~$0.001/请求

### Local Reranking

**适用场景**: 日常检索（零成本）

```python
from src.agentic_rag.reranking import LocalReranker

reranker = LocalReranker(
    model="cross-encoder/ms-marco-MiniLM-L-6-v2"
)
reranked = reranker.rerank(query, documents)
```

**参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| model | str | "ms-marco-MiniLM-L-6-v2" | 本地模型 |
| batch_size | int | 32 | 批处理大小 |

**成本**: 免费

---

## 质量控制API

### QualityController

```python
from src.agentic_rag.quality import QualityController

controller = QualityController(
    threshold=0.6,
    max_rewrites=2
)

# 评估质量
score = controller.evaluate(query, results)

# 决定是否重写
should_rewrite = controller.should_rewrite(score)

# 生成重写Query
if should_rewrite:
    new_query = await controller.rewrite_query(query, results)
```

---

## 错误码

| 错误码 | 描述 | HTTP状态码 | 处理方式 |
|--------|------|------------|----------|
| `GRAPHITI_UNAVAILABLE` | Graphiti连接失败 | 503 | 降级到LanceDB单源 |
| `LANCEDB_UNAVAILABLE` | LanceDB连接失败 | 503 | 降级到Graphiti单源 |
| `COHERE_TIMEOUT` | Cohere API超时 | 504 | 降级到Local Reranking |
| `COHERE_RATE_LIMITED` | Cohere限流 | 429 | 降级到Local Reranking |
| `QUALITY_LOW` | 检索质量低 | 200 | 触发Query重写 |
| `MAX_REWRITES_EXCEEDED` | 重写次数超限 | 200 | 返回当前最佳结果 |
| `INVALID_QUERY` | 查询格式错误 | 400 | 返回错误信息 |
| `BUDGET_EXCEEDED` | 成本超预算 | 402 | 切换到免费策略 |

**错误响应格式**:
```python
{
    "error": {
        "code": "GRAPHITI_UNAVAILABLE",
        "message": "Unable to connect to Neo4j at bolt://localhost:7687",
        "details": {
            "retry_count": 3,
            "last_error": "Connection refused"
        }
    },
    "fallback_used": True,
    "fallback_source": "lancedb"
}
```

---

## 使用示例

### 基础检索

```python
from src.agentic_rag.state_graph import canvas_agentic_rag

# 简单查询
result = await canvas_agentic_rag.ainvoke({
    "query": "逆否命题的定义"
})

print(f"找到 {len(result['reranked_results'])} 个结果")
print(f"最佳匹配: {result['reranked_results'][0]['content']}")
print(f"延迟: {result['latency_ms']}ms")
```

### 检验白板生成（高质量）

```python
# 使用Weighted融合 + Cohere Reranking
result = await canvas_agentic_rag.ainvoke({
    "query": "检索薄弱概念用于生成检验题",
    "canvas_file": "离散数学.canvas",
    "fusion_strategy": "weighted",
    "reranking_strategy": "cohere",
    "top_k": 15,
    "quality_threshold": 0.7
})

# 使用结果生成检验题
weak_concepts = result['reranked_results'][:5]
for concept in weak_concepts:
    print(f"薄弱概念: {concept['content'][:50]}...")
```

### 复习模式

```python
# 复习模式会优先返回需要复习的内容
result = await canvas_agentic_rag.ainvoke({
    "query": "复习逆否命题相关内容",
    "is_review_mode": True,
    "fusion_strategy": "cascade"  # 使用分层过滤
})

# 结果会按FSRS调度优先级排序
for item in result['reranked_results']:
    due_date = item.get('metadata', {}).get('fsrs_due_date')
    print(f"内容: {item['content'][:30]}... (到期: {due_date})")
```

### 流式进度显示

```python
import asyncio

async def search_with_progress(query: str):
    print(f"搜索: {query}")
    print("-" * 40)

    async for event in canvas_agentic_rag.astream({"query": query}):
        node = event.get("node", "unknown")
        data = event.get("data", {})

        if node == "parallel_retrieval":
            print(f"✓ 并行检索完成: Graphiti={data.get('graphiti_count')}, LanceDB={data.get('lancedb_count')}")
        elif node == "fusion":
            print(f"✓ 融合完成: {data.get('method')}, 结果数={data.get('result_count')}")
        elif node == "reranking":
            print(f"✓ Reranking完成: {data.get('method')}, 最高分={data.get('top_score'):.2f}")
        elif node == "quality_control":
            status = "通过" if data.get('passed') else "需重写"
            print(f"✓ 质量评估: {data.get('score'):.2f} ({status})")
        elif node == "output":
            print(f"✓ 完成! 延迟={data.get('latency_ms')}ms")

    print("-" * 40)

# 运行
asyncio.run(search_with_progress("什么是逆否命题?"))
```

### 错误处理

```python
from src.agentic_rag.exceptions import (
    GraphitiUnavailableError,
    CohereTimeoutError,
    QualityLowError
)

try:
    result = await canvas_agentic_rag.ainvoke({
        "query": "逆否命题",
        "quality_threshold": 0.9  # 高阈值
    })
except GraphitiUnavailableError as e:
    print(f"Graphiti不可用: {e}")
    print(f"使用降级结果: {e.fallback_results}")
except CohereTimeoutError as e:
    print(f"Cohere超时，已切换到本地Reranking")
    result = e.fallback_result
except QualityLowError as e:
    print(f"检索质量低 ({e.score:.2f})，已尝试 {e.rewrite_count} 次重写")
    result = e.best_result
```

---

## 配置参考

### 环境变量

```bash
# Agentic RAG配置
AGENTIC_RAG_DEFAULT_FUSION=rrf
AGENTIC_RAG_DEFAULT_RERANKING=local
AGENTIC_RAG_QUALITY_THRESHOLD=0.6
AGENTIC_RAG_MAX_REWRITES=2
AGENTIC_RAG_TIMEOUT_MS=5000

# 并行检索配置
PARALLEL_RETRIEVAL_WORKERS=4
PARALLEL_RETRIEVAL_TIMEOUT=2.0

# Cohere配置
COHERE_API_KEY=your_key
COHERE_MODEL=rerank-english-v3.0

# 成本控制
COST_TRACKING_ENABLED=true
COHERE_MONTHLY_BUDGET=3.0
```

### Python配置

```python
from src.agentic_rag.config import AgenticRAGConfig

config = AgenticRAGConfig(
    default_fusion="rrf",
    default_reranking="local",
    quality_threshold=0.6,
    max_rewrites=2,
    timeout_ms=5000,
    parallel_workers=4,
    cost_tracking=True
)

# 应用配置
canvas_agentic_rag.with_config(config)
```

---

## 性能基准

| 操作 | P50 | P95 | P99 |
|------|-----|-----|-----|
| 并行检索 | 80ms | 150ms | 200ms |
| RRF融合 | 5ms | 10ms | 15ms |
| Weighted融合 | 5ms | 10ms | 15ms |
| Cascade融合 | 10ms | 20ms | 30ms |
| Local Reranking | 50ms | 100ms | 150ms |
| Cohere Reranking | 150ms | 300ms | 400ms |
| **端到端 (Local)** | 150ms | 300ms | 400ms |
| **端到端 (Cohere)** | 250ms | 400ms | 550ms |

---

## 版本信息

- **API版本**: 2.0.0
- **兼容性**: Python 3.9+
- **依赖**: langgraph>=0.2.55, lancedb>=0.6.0
