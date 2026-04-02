# Graphiti-Core Python SDK — 完整 API 能力审计报告

> 研究时间: 2026-04-02  
> 当前项目版本: `graphiti-core>=0.28.2` (最新稳定版)  
> 数据来源: Context7 文档、PyPI、GitHub Releases、项目代码库

---

## 1. 版本状态

| 版本 | 日期 | 要点 |
|------|------|------|
| **0.28.2** (当前/最新稳定) | 2026-03-11 | 安全: Cypher 注入防护; GLiNER2 hybrid LLM 客户端 |
| 0.28.1 | 2026-02-19 | 移除 diskcache (CVE 修复); 修复自定义 edge 属性提取 |
| 0.28.0 | 2026-02-17 | **Driver 操作架构重设计**; 简化提取管道; 批量实体摘要; Neptune/Kuzu driver |
| 0.27.0 | 2026-02-11 | 效率提升; 实体摘要中加入 edge facts; Gemini 3 支持; prompt 系统重构 |
| 0.26.x | 2026-01 | GraphOperationsInterface 更新; 直接数据库调用路径 |

**项目 `requirements.txt` 指定 `graphiti-core>=0.28.2` — 已锁定最新稳定版。**

---

## 2. Graphiti 类 — 完整公共 API

### 2.1 构造器与生命周期

| 方法 | 签名 | 项目使用状态 |
|------|------|-------------|
| `__init__` | `Graphiti(uri, user, password, llm_client, embedder, cross_encoder, max_coroutines, graph_driver)` | ✅ 使用 (episode_worker.py) |
| `build_indices_and_constraints` | `await graphiti.build_indices_and_constraints()` | ✅ 使用 |
| `close` | `await graphiti.close()` | ✅ 使用 |

#### 构造器参数详解:

```python
Graphiti(
    uri="bolt://localhost:7687",       # Neo4j 连接 URI
    user="neo4j",                       # Neo4j 用户名
    password="password",                # Neo4j 密码
    llm_client=None,                    # LLM 客户端 (OpenAI/Gemini/Groq/Anthropic)
    embedder=None,                      # 嵌入器 (OpenAI/Gemini/VoyageAI/SentenceTransformers)
    cross_encoder=None,                 # 交叉编码器重排器
    max_coroutines=3,                   # 并发协程限制
    graph_driver=None,                  # 自定义 graph driver (Neo4j/FalkorDB/Neptune/Kuzu)
)
```

**项目使用**: 使用 `GeminiClient` + `GeminiEmbedder` + `GeminiRerankerClient`，直接传入 Neo4j 连接参数。

### 2.2 数据摄入 (Ingestion)

| 方法 | 签名 | 项目使用状态 |
|------|------|-------------|
| `add_episode` | `await graphiti.add_episode(name, episode_body, source, source_description, reference_time, group_id, entity_types, edge_types, edge_type_map)` | ✅ 使用 (核心路径) |
| `add_episode_bulk` | `await graphiti.add_episode_bulk(bulk_episodes, group_id)` | ❌ 未使用 |
| `add_triplet` | `await graphiti.add_triplet(source_node, edge, target_node)` | ⚠️ 测试中引用，生产代码未使用 |

#### `add_episode` 完整参数:

```python
await graphiti.add_episode(
    name="Meeting Notes",                   # Episode 名称
    episode_body="Alice is the CEO...",      # 内容 (text 或 JSON 字符串)
    source=EpisodeType.text,                 # 来源类型: text | json | message
    source_description="Team meeting",       # 来源描述
    reference_time=datetime.now(utc),        # 时间戳 (必须 UTC-aware)
    group_id="project-alpha",                # 命名空间 (可选)
    entity_types={"Person": PersonModel},    # 自定义实体类型 (可选)
    edge_types={"Employment": EmplModel},    # 自定义边类型 (可选)
    edge_type_map={("Person","Company"): ["Employment"]},  # 边类型映射 (可选)
)
```

**项目使用**: 仅使用 `name`, `episode_body`, `group_id`, `source_description`, `reference_time`。**未使用自定义实体/边类型**。

#### `add_episode_bulk` (批量摄入):

```python
from graphiti_core.utils.bulk_utils import RawEpisode

episodes = [
    RawEpisode(name="...", content="...", source=EpisodeType.text,
               source_description="...", reference_time=datetime(...)),
    ...
]
result = await graphiti.add_episode_bulk(bulk_episodes=episodes, group_id="...")
```

**机会**: 学习系统可以在导入历史学习记录时使用批量摄入，大幅减少开销。

### 2.3 搜索 (Search)

| 方法 | 签名 | 项目使用状态 |
|------|------|-------------|
| `search` | `await graphiti.search(query, group_ids, num_results, center_node_uuid)` | ✅ 使用 (memory_service.py) |
| `search_` (高级) | `await graphiti.search_(query, config, group_ids, search_filter)` | ❌ 未使用 |

#### 基础搜索:

```python
# 简单混合搜索
results = await graphiti.search(query="...", group_ids=["canvas-dev"])

# 带节点距离重排序
results = await graphiti.search(query="...", center_node_uuid="node-uuid-here")
```

#### 高级搜索 (`search_`):

```python
from graphiti_core.search.search_config_recipes import (
    NODE_HYBRID_SEARCH_RRF,              # 节点搜索 + RRF 重排
    EDGE_HYBRID_SEARCH_CROSS_ENCODER,    # 边搜索 + 交叉编码器重排
    COMBINED_HYBRID_SEARCH_CROSS_ENCODER,# 节点+边+社区组合搜索
    EDGE_HYBRID_SEARCH_RRF,              # 边搜索 + RRF 重排
)
from graphiti_core.search.search_filters import (
    SearchFilters, DateFilter, ComparisonOperator,
)

# 按节点标签过滤
filter = SearchFilters(node_labels=["Person", "Concept"])

# 按边类型过滤
filter = SearchFilters(edge_types=["LEARNS", "RELATED_TO"])

# 按日期范围过滤 (时序查询关键能力!)
filter = SearchFilters(valid_at=[[
    DateFilter(
        date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        comparison_operator=ComparisonOperator.greater_than_equal
    )
]])

# 组合搜索
results = await graphiti.search_(
    query="Who manages engineering?",
    config=EDGE_HYBRID_SEARCH_RRF,
    search_filter=filter,
)
```

**项目使用**: 仅使用基础 `search()`。**高级搜索 `search_()` 完全未使用** — 这是最大的未开发能力。

### 2.4 检索 (Retrieval)

| 方法 | 签名 | 项目使用状态 |
|------|------|-------------|
| `retrieve_episodes` | `await graphiti.retrieve_episodes(reference_time, last_n, group_ids, source)` | ❌ 未使用 |

```python
episodes = await graphiti.retrieve_episodes(
    reference_time=datetime.now(timezone.utc),
    last_n=10,
    group_ids=["canvas-dev"],
    source=EpisodeType.message
)
```

**机会**: 可用于显示最近学习活动的时间线视图。

### 2.5 删除 (Deletion)

| 方法 | 签名 | 项目使用状态 |
|------|------|-------------|
| `remove_episode` | `await graphiti.remove_episode(episode_uuid)` | ❌ 未使用 |

### 2.6 社区 (Communities)

| 方法 | 签名 | 项目使用状态 |
|------|------|-------------|
| `build_communities` | `await graphiti.build_communities(group_ids)` | ❌ 未使用 |

```python
communities, community_edges = await graphiti.build_communities(
    group_ids=["canvas-dev"]
)
for c in communities:
    print(f"Community: {c.name}, Summary: {c.summary}")
```

**Leiden 算法**自动聚类强关联节点，生成社区摘要。

**机会**: 学习系统中，社区可自动发现"知识簇" — 例如将相关概念自动聚合为"微积分"、"线性代数"等主题组。

### 2.7 数据清理

| 方法 | 签名 | 项目使用状态 |
|------|------|-------------|
| `clear_data` | `from graphiti_core.utils.maintenance.graph_data_operations import clear_data; await clear_data(graphiti.driver)` | ❌ 未使用 |

### 2.8 命名空间访问 (v0.28+ 新架构)

```python
# 节点命名空间
graphiti.nodes.entity    # EntityNodeNamespace
graphiti.nodes.episode   # EpisodeNodeNamespace
graphiti.nodes.community # CommunityNodeNamespace
graphiti.nodes.saga      # SagaNodeNamespace

# 边命名空间
graphiti.edges.entity    # EntityEdgeNamespace
graphiti.edges.episodic  # EpisodicEdgeNamespace
graphiti.edges.community # CommunityEdgeNamespace
graphiti.edges.has_episode    # HasEpisodeEdgeNamespace
graphiti.edges.next_episode   # NextEpisodeEdgeNamespace
```

**项目使用**: ❌ 完全未使用。这是 v0.28 driver 重设计引入的新底层 API。

---

## 3. Entity 类型与定义方式

### 3.1 内建节点类型

| 类型 | 描述 | 导入路径 |
|------|------|---------|
| `EntityNode` | 知识实体 (人、概念、物品等) | `graphiti_core.nodes.EntityNode` |
| `EpisodicNode` | Episode 记录 | `graphiti_core.nodes.EpisodicNode` (内部) |
| `CommunityNode` | 社区聚类节点 | `graphiti_core.nodes.CommunityNode` (内部) |

#### EntityNode 关键属性:

```python
EntityNode(
    uuid="...",
    name="Alice",
    group_id="canvas-dev",
    summary="...",        # LLM 生成的实体摘要
    labels=["Person"],    # Neo4j 标签
    # 内部属性:
    # created_at, name_embedding
)
```

### 3.2 内建边类型

| 类型 | 描述 | 导入路径 |
|------|------|---------|
| `EntityEdge` | 实体间的事实关系 | `graphiti_core.edges.EntityEdge` |
| `EpisodicEdge` | Episode 到实体的关联 | 内部 |
| `CommunityEdge` | 社区到实体的关联 | 内部 |

#### EntityEdge 关键属性:

```python
EntityEdge(
    uuid="...",
    group_id="canvas-dev",
    source_node_uuid="...",
    target_node_uuid="...",
    name="WORKS_FOR",
    fact="Alice works for TechCorp as CTO",
    created_at=datetime.now(),
    # 时序属性 (核心!):
    # valid_at        — 事实开始生效时间
    # expired_at      — 事实失效时间 (None = 仍然有效)
    # invalid_at      — 被标记为无效的时间
)
```

### 3.3 自定义实体类型 (Pydantic 模型)

```python
from pydantic import BaseModel, Field

class LearningConcept(BaseModel):
    """学习概念实体"""
    difficulty: Optional[str] = Field(None, description="难度等级")
    subject_area: Optional[str] = Field(None, description="学科领域")
    prerequisites: Optional[str] = Field(None, description="前置知识")

class MasteryRelation(BaseModel):
    """掌握程度关系"""
    mastery_level: Optional[float] = Field(None, description="掌握度 0-1")
    last_reviewed: Optional[datetime] = Field(None, description="最后复习时间")
    review_count: Optional[int] = Field(None, description="复习次数")

# 在 add_episode 中使用
await graphiti.add_episode(
    ...,
    entity_types={"LearningConcept": LearningConcept},
    edge_types={"MasteryRelation": MasteryRelation},
    edge_type_map={("Person", "LearningConcept"): ["MasteryRelation"]},
)
```

**项目使用**: ❌ **完全未使用自定义实体/边类型**。这是最大的未利用能力之一 — 学习系统非常适合定义 `Concept`、`LearningGoal`、`MasteryLevel` 等自定义类型。

### 3.4 Schema Evolution

Graphiti 支持 schema 演进 — 可以向已有实体类型添加新属性，旧节点保留原始数据，新节点支持新属性。无需迁移。

---

## 4. Episode 生命周期

```
创建 ──> 处理 ──> 存储 ──> 搜索 ──> (可选)删除
 │        │        │        │         │
 │        │        │        │         └─ remove_episode(uuid)
 │        │        │        └─ search() / search_() / retrieve_episodes()
 │        │        └─ Neo4j 持久化 (EpisodicNode + EntityNode + EntityEdge)
 │        └─ LLM 提取实体/关系 → 去重/合并 → 嵌入生成
 └─ add_episode() / add_episode_bulk()
```

### Episode 类型 (`EpisodeType`):

| 类型 | 描述 |
|------|------|
| `EpisodeType.text` | 纯文本内容 |
| `EpisodeType.json` | 结构化 JSON 数据 |
| `EpisodeType.message` | 对话消息 |

### Episode 处理管道:

1. **输入**: 文本/JSON → LLM 提取实体和关系
2. **实体解析**: 检测是否与已有实体重复 → 合并或创建新节点
3. **关系建立**: 在实体间创建 EntityEdge，包含 `fact` 属性
4. **时序标记**: 自动设置 `valid_at`、检测矛盾并标记旧 edge 的 `expired_at`
5. **嵌入生成**: 为实体名和 edge fact 生成向量嵌入
6. **摘要更新**: 更新受影响实体的 summary

---

## 5. group_id 设计意图与用法

### 设计意图:
- **命名空间隔离**: 不同 `group_id` 的数据完全隔离
- **多租户**: 单个 Neo4j 实例支持多个独立图
- **作用域**: 所有节点和边都携带 `group_id`
- **性能**: 搜索限定在特定命名空间内，减少扫描范围

### 用法模式:

```python
# 摄入时指定
await graphiti.add_episode(..., group_id="canvas-dev")

# 搜索时限定
results = await graphiti.search(query="...", group_ids=["canvas-dev"])

# 手动创建节点时
EntityNode(uuid="...", name="...", group_id="canvas-dev")
```

### 学习系统的推荐用法:

| group_id 模式 | 适用场景 |
|---------------|---------|
| `user:{user_id}` | 每用户一个独立知识图谱 |
| `canvas:{canvas_name}` | 每个 Canvas 文件一个子图 |
| `subject:{subject}` | 按学科组织 |
| `canvas-dev` (当前) | 开发/全局共享 |

**项目当前**: 使用单一 `group_id` 或基于配置的值。未利用多命名空间做细粒度隔离。

---

## 6. 搜索能力详解

### 6.1 搜索配方 (Search Recipes)

| 配方 | 组合策略 | 适用场景 |
|------|---------|---------|
| `NODE_HYBRID_SEARCH_RRF` | 语义+BM25 → RRF 融合 | 查找实体节点 |
| `EDGE_HYBRID_SEARCH_RRF` | 语义+BM25 → RRF 融合 | 查找事实关系 |
| `EDGE_HYBRID_SEARCH_CROSS_ENCODER` | 语义+BM25 → 交叉编码器重排 | 高精度事实检索 |
| `COMBINED_HYBRID_SEARCH_CROSS_ENCODER` | 节点+边+社区 → 交叉编码器 | 全面检索 |

### 6.2 搜索过滤器

```python
SearchFilters(
    node_labels=["Person", "Concept"],    # 按节点标签过滤
    edge_types=["LEARNS", "RELATED_TO"],  # 按边类型过滤
    valid_at=[[DateFilter(...)]],         # 按时间范围过滤
)
```

### 6.3 图感知搜索 (Node Distance Reranking)

```python
# 找到焦点节点后，基于图距离重排结果
results = await graphiti.search(
    query="related concepts",
    center_node_uuid="focal-node-uuid"  # 按图距离重排
)
```

### 6.4 搜索结果结构

```python
# search() 返回 EntityEdge 列表
for edge in results:
    edge.uuid             # 边 UUID
    edge.fact             # 事实文本
    edge.name             # 关系名
    edge.source_node_uuid # 源节点
    edge.target_node_uuid # 目标节点
    edge.created_at       # 创建时间
    edge.valid_at         # 生效时间
    edge.expired_at       # 失效时间

# search_() 返回结构化结果
results.nodes   # EntityNode 列表
results.edges   # EntityEdge 列表
```

---

## 7. 时序知识图谱特性 (Temporal Aspects)

### 7.1 核心时序字段

| 字段 | 含义 | 自动管理 |
|------|------|---------|
| `created_at` | 记录创建时间 | ✅ 自动 |
| `valid_at` | 事实开始生效时间 | ✅ 从 reference_time 推断 |
| `expired_at` | 事实失效时间 | ✅ 矛盾检测时自动设置 |
| `invalid_at` | 被标记为无效的时间 | ✅ 矛盾检测时自动设置 |

### 7.2 知识演变追踪

当新信息与旧信息矛盾时:

```
Episode 1 (2024-01): "Alice is a junior developer"
  → Edge: Alice --IS_A--> Junior Developer (valid_at: 2024-01)

Episode 2 (2024-06): "Alice was promoted to tech lead"
  → Edge: Alice --IS_A--> Junior Developer (expired_at: 2024-06)  ← 自动标记过期
  → Edge: Alice --IS_A--> Tech Lead (valid_at: 2024-06)          ← 新事实
```

### 7.3 时间点查询

通过 `DateFilter` 可以查询特定时间点的知识状态:

```python
# 查询 2024年1月时的知识状态
filter = SearchFilters(valid_at=[[
    DateFilter(date=datetime(2024, 1, 1), comparison_operator=ComparisonOperator.greater_than_equal),
    DateFilter(date=datetime(2024, 2, 1), comparison_operator=ComparisonOperator.less_than),
]])
```

### 7.4 学习系统的时序应用

| 场景 | Graphiti 能力 |
|------|--------------|
| 知识掌握度变化 | `valid_at`/`expired_at` 追踪掌握度随时间变化 |
| 遗忘曲线 | `reference_time` 记录每次复习时间，可推算间隔 |
| 知识演变 | 矛盾检测自动标记旧理解，保留历史 |
| 学习时间线 | `retrieve_episodes` 获取有序学习记录 |
| 点时间查询 | DateFilter 查询"某个时间点用户知道什么" |

---

## 8. 与 Neo4j 的关系

### 8.1 Graphiti 在 Neo4j 之上的抽象层

| 能力 | Neo4j 原生 | Graphiti 添加 |
|------|-----------|--------------|
| 图存储 | ✅ | — |
| Cypher 查询 | ✅ | — |
| 全文索引 | ✅ | 自动创建和使用 |
| 向量索引 | ✅ (5.x+) | 自动嵌入生成和索引 |
| LLM 实体提取 | ❌ | ✅ 从自然语言自动提取 |
| 自动去重/合并 | ❌ | ✅ 实体解析 |
| 矛盾检测 | ❌ | ✅ 时序一致性 |
| 混合搜索 | 手动实现 | ✅ 预置配方 |
| 社区检测 | 手动实现 | ✅ Leiden 算法 |
| Schema 演进 | 手动管理 | ✅ 自动向后兼容 |

### 8.2 Graphiti 独有能力

1. **LLM 驱动的实体/关系自动提取** — 从非结构化文本到知识图谱
2. **增量更新** — 无需完整重建图
3. **时序矛盾解决** — 自动检测和标记过期事实
4. **混合搜索融合** — 语义 + BM25 + 图距离的组合
5. **自定义本体论** — Pydantic 模型定义领域特定类型

### 8.3 支持的后端 (v0.28+)

| 后端 | 状态 | 驱动 |
|------|------|------|
| Neo4j | ✅ 默认 | `Neo4jDriver` |
| FalkorDB | ✅ | `FalkorDriver` |
| Amazon Neptune | ✅ | `NeptuneDriver` |
| Kuzu | ✅ (v0.28+新增) | `KuzuDriver` |

---

## 9. 项目使用状态总览

### ✅ 已使用

| 能力 | 位置 | 用法 |
|------|------|------|
| `Graphiti()` 构造 | `episode_worker.py` | Gemini LLM + Embedder |
| `build_indices_and_constraints()` | `episode_worker.py` | 启动时调用 |
| `add_episode()` | `episode_worker.py` | 异步队列处理 |
| `search()` | `memory_service.py` | 基础搜索，2s 超时 |
| `close()` | `episode_worker.py` | 关闭时调用 |
| `group_id` | 多处 | 基本命名空间 |
| `EpisodeType.text` | `episode_worker.py` | 隐式使用 |

### ❌ 未使用 — 高价值未利用能力

| 能力 | 价值 | 学习系统适用度 |
|------|------|---------------|
| **`search_()` 高级搜索** | ⭐⭐⭐⭐⭐ | 极高 — 可用 NODE/EDGE/COMBINED 配方、过滤器、交叉编码器 |
| **`SearchFilters` 过滤器** | ⭐⭐⭐⭐⭐ | 极高 — DateFilter 实现时序查询，node_labels 过滤概念类型 |
| **自定义 Entity/Edge 类型** | ⭐⭐⭐⭐⭐ | 极高 — 定义 Concept, MasteryLevel, LearningGoal 等 |
| **`center_node_uuid` 图距离重排** | ⭐⭐⭐⭐ | 高 — 从一个概念出发发现相关概念 |
| **`add_episode_bulk()`** | ⭐⭐⭐⭐ | 高 — 批量导入学习历史 |
| **`build_communities()`** | ⭐⭐⭐⭐ | 高 — 自动发现知识簇/学科主题 |
| **`retrieve_episodes()`** | ⭐⭐⭐ | 中 — 学习时间线视图 |
| **`remove_episode()`** | ⭐⭐ | 中 — 数据清理 |
| **`add_triplet()`** | ⭐⭐ | 中 — 手动创建精确关系 |
| **Node/Edge Namespace API** | ⭐⭐ | 中 — 底层细粒度操作 |
| **Schema Evolution** | ⭐⭐⭐ | 中高 — 随学习系统演进添加新属性 |

---

## 10. 学习系统推荐使用模式

### 10.1 当前架构 vs 推荐增强

```
当前:
  用户操作 → episode_worker.add_episode() → Graphiti → Neo4j
  查询 → memory_service.search() → Graphiti.search() → 返回边列表

推荐:
  用户操作 → episode_worker.add_episode(entity_types=学习类型) → Graphiti → Neo4j
  查询 → search_(config=适配配方, filter=时序+类型过滤) → 节点+边+社区
  定期 → build_communities() → 发现知识簇
  时间线 → retrieve_episodes() → 学习活动回放
  概念探索 → search(center_node_uuid=焦点概念) → 关联知识发现
```

### 10.2 自定义类型推荐

```python
# 学习系统推荐的 Entity Types
class LearningConcept(BaseModel):
    difficulty: Optional[str] = None         # easy/medium/hard
    subject: Optional[str] = None            # 学科
    bloom_level: Optional[str] = None        # 布鲁姆认知层次

class LearnerProfile(BaseModel):
    preferred_style: Optional[str] = None    # visual/auditory/kinesthetic
    current_level: Optional[str] = None      # beginner/intermediate/advanced

# 学习系统推荐的 Edge Types
class Mastery(BaseModel):
    level: Optional[float] = None            # 0.0-1.0
    last_review: Optional[datetime] = None
    next_review: Optional[datetime] = None   # 基于遗忘曲线计算
    review_count: Optional[int] = None

class Prerequisite(BaseModel):
    importance: Optional[str] = None         # required/recommended/optional
    confidence: Optional[float] = None

# Edge Type Map
edge_type_map = {
    ("LearnerProfile", "LearningConcept"): ["Mastery"],
    ("LearningConcept", "LearningConcept"): ["Prerequisite"],
}
```

### 10.3 遗忘曲线实现方案

利用 Graphiti 时序能力实现间隔重复:

```python
# 1. 每次复习时添加 episode
await graphiti.add_episode(
    name=f"Review: {concept_name}",
    episode_body=f"User reviewed '{concept_name}' and scored {score}/100",
    reference_time=datetime.now(timezone.utc),
    group_id=f"user:{user_id}",
    entity_types={"LearningConcept": LearningConcept},
    edge_types={"Mastery": Mastery},
)

# 2. 查询需要复习的概念 (基于时间过滤)
from graphiti_core.search.search_filters import SearchFilters, DateFilter, ComparisonOperator

stale_filter = SearchFilters(valid_at=[[
    DateFilter(
        date=datetime.now(timezone.utc) - timedelta(days=7),
        comparison_operator=ComparisonOperator.less_than
    )
]])
stale_concepts = await graphiti.search_(
    query="mastery level",
    config=EDGE_HYBRID_SEARCH_RRF,
    search_filter=stale_filter,
    group_ids=[f"user:{user_id}"],
)

# 3. 知识演变: Graphiti 自动追踪掌握度变化
# Episode 1: "用户第一次学习微积分, 掌握度 20%"
# Episode 2: "用户复习微积分, 掌握度 60%"  → 旧边自动 expired
# Episode 3: "用户考试微积分, 掌握度 85%"  → 旧边自动 expired
```

---

## 11. LLM 客户端支持

| 提供者 | 模块 | extras |
|--------|------|--------|
| OpenAI | `graphiti_core.llm_client.OpenAIClient` | 默认 |
| Gemini | `graphiti_core.llm_client.gemini_client.GeminiClient` | `google-genai` |
| Anthropic | — | `anthropic` |
| Groq | — | `groq` |
| VoyageAI (embedder) | — | `voyageai` |
| Sentence Transformers (embedder) | — | `sentence-transformers` |
| GLiNER2 (hybrid) | — | `gliner2` (v0.28.2 新增) |

**项目使用**: Gemini (GeminiClient + GeminiEmbedder + GeminiRerankerClient)

---

## 12. 总结: 利用率评分

| 类别 | 已用/总计 | 利用率 |
|------|----------|--------|
| 生命周期管理 | 3/3 | 100% |
| 数据摄入 | 1/3 | 33% |
| 搜索 | 1/2 (基础) | 20%* |
| 检索 | 0/1 | 0% |
| 删除 | 0/1 | 0% |
| 社区 | 0/1 | 0% |
| 自定义类型 | 0/1 | 0% |
| 时序过滤 | 0/1 | 0% |
| 图距离重排 | 0/1 | 0% |

> *搜索 20% = 使用了 search() 但未用 search_()、SearchFilters、SearchRecipes、center_node_uuid

**整体利用率: ~25%**。项目使用了 Graphiti 的基本摄入和搜索，但其最强大的能力 — 高级搜索、时序查询、自定义类型、社区检测、图距离搜索 — 全部未开发。

---

## Sources

1. [graphiti-core PyPI](https://pypi.org/project/graphiti-core/) — v0.28.2 (latest stable, 2026-03-11)
2. [GitHub Releases](https://github.com/getzep/graphiti/releases) — Changelog
3. [Graphiti Documentation](https://help.getzep.com/graphiti) — Official docs
4. [GitHub Repository](https://github.com/getzep/graphiti) — 24.4k stars, source code + specs
5. Context7 library documentation snapshots (2026-03-25/26)
