# Story 12.1: Graphiti时序知识图谱集成

**Epic**: Epic 12 - 3层记忆系统 + Agentic RAG集成
**优先级**: P0 (MVP Must-Have)
**Story Points**: 2
**工期**: 2天
**依赖**: 无
**Assignee**: Dev Agent (James)
**状态**: Ready for Development

---

## User Story

> As a **Canvas学习系统开发者**, I want to **集成Graphiti时序知识图谱**, so that **系统能追踪概念关系和学习历史，支持跨会话的知识网络检索**。

---

## Acceptance Criteria

### AC 1.1: Neo4j Community Edition部署成功

**验收标准**: Neo4j Community Edition 5.0+成功安装并运行

**验证步骤**:
- [ ] Docker Compose一键部署或Windows本地安装
- [ ] Neo4j Browser可访问 (http://localhost:7474)
- [ ] 默认数据库`neo4j`创建成功
- [ ] 连接凭证配置正确 (bolt://localhost:7687)

**验证命令**:
```bash
# Docker方式
docker run -d --name neo4j -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5.0-community

# 验证连接
curl http://localhost:7474
```

---

### AC 1.2: Graphiti Python客户端连接成功

**验收标准**: GraphitiClient初始化成功，健康检查通过

**验证步骤**:
- [ ] `graphiti-core` Python库安装 (pip install graphiti-core)
- [ ] GraphitiClient初始化成功
- [ ] 健康检查通过 (`client.health_check()`)
- [ ] 连接池配置正确

**技术验证**: 参见Dev Notes Section 1

---

### AC 1.3: add_episode()正确提取概念和关系

**验收标准**: 学习会话文本正确提取Entity和Relationship

**验证步骤**:
- [ ] 输入: 学习会话文本 (例如: "用户学习了逆否命题的定义和证明方法")
- [ ] 输出: Entity节点 (逆否命题, 证明方法)
- [ ] 输出: Relationship (逆否命题 USED_IN 证明方法)
- [ ] 时序边: valid_at timestamp正确记录

**测试用例**:
```python
# ✅ Verified from Graphiti Skill - Quick Reference > Adding Episodes
from datetime import datetime

episode_content = "用户在离散数学Canvas中学习了逆否命题的定义: 如果原命题是'如果p则q'，逆否命题是'如果非q则非p'。逆否命题与原命题等价。"

await graphiti.add_episode(
    name="test_episode_contrapositive",
    episode_body=episode_content,
    source_description="离散数学.canvas - 逆否命题章节",
    reference_time=datetime.now()
)

# Graphiti自动提取:
# - Entities: "逆否命题", "原命题", "证明方法"
# - Relationships: 语义关系 (stored as edges)
# - Temporal metadata: valid_at timestamp

# 验证: 通过search查询确认提取成功
results = await graphiti.search(
    query="逆否命题",
    num_results=5
)
assert len(results.edges) >= 1, "应至少提取1个关系"
```

---

### AC 1.4: hybrid_search()返回Graph + Semantic + BM25结果

**验收标准**: 混合搜索返回高质量结果

**验证步骤**:
- [ ] 输入query: "逆否命题的应用场景"
- [ ] 返回: List[SearchResult]，至少5个结果
- [ ] 结果包含: Graph匹配 + 语义相似 + 关键词匹配
- [ ] 人工检查Top-5相关性 >= 80%

**测试用例**:
```python
# ✅ Verified from Graphiti Skill - Quick Reference > Searching the Graph
# Graphiti.search() 实现混合搜索 (Semantic + BM25 + Graph)

results = await graphiti.search(
    query="逆否命题的应用场景",
    num_results=10,
    center_node_uuid=None  # Optional: 从特定节点出发搜索
)

# 结果包含edges(关系/事实)、nodes(实体)、episodes(数据源)
assert len(results.edges) >= 5, "应至少返回5个相关事实"

# 人工验证Top-5相关性
for i, edge in enumerate(results.edges[:5]):
    print(f"#{i+1}: {edge.fact}")
    print(f"  Valid from: {edge.valid_at}")
    print(f"  Invalid at: {edge.invalid_at if edge.invalid_at else 'Still valid'}")
```

---

### AC 1.5: 数据持久化和查询性能

**验收标准**: 性能和存储指标达标

**验证步骤**:
- [ ] 100个Episode添加成功，无数据丢失
- [ ] `hybrid_search()`延迟 < 100ms (100个概念，P95)
- [ ] Neo4j数据库大小 < 50MB (100个概念场景)

**性能测试脚本**:
```python
# ✅ Verified from Graphiti Skill - API Reference
import time
import numpy as np
from datetime import datetime

# 添加100个Episode
for i in range(100):
    await graphiti.add_episode(
        name=f"performance_test_{i}",
        episode_body=f"学习概念 {i}: 示例内容描述...",
        source_description=f"test-canvas-{i}",
        reference_time=datetime.now()
    )

# 性能测试
latencies = []
for _ in range(100):
    start = time.perf_counter()
    await graphiti.search("查询测试", num_results=10)
    end = time.perf_counter()
    latencies.append((end - start) * 1000)

p95 = np.percentile(latencies, 95)
assert p95 < 100, f"P95延迟超标: {p95}ms"
print(f"P95 Latency: {p95:.2f}ms ✅")
```

---

## Technical Details

### 核心实现代码

```python
# ✅ Verified from Graphiti Skill (2025-11-21)
# 参见: @graphiti SKILL.md - Quick Reference > Installation and Setup

from graphiti_core import Graphiti
from graphiti_core.driver.neo4j_driver import Neo4jDriver
from datetime import datetime

# 1. 初始化Neo4j Driver
driver = Neo4jDriver(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="your-password"
)

# 2. 创建Graphiti实例
graphiti = Graphiti(driver)

# 3. 添加学习会话 (Episode)
# ✅ Verified from Graphiti Skill - Quick Reference > Adding Episodes
await graphiti.add_episode(
    name="canvas_learning_session",
    episode_body="用户在离散数学Canvas中学习了逆否命题的定义: 如果原命题是'如果p则q'，逆否命题是'如果非q则非p'。逆否命题与原命题等价。",
    source_description="离散数学.canvas - 逆否命题章节",
    reference_time=datetime.now()
)

# 4. 搜索知识图谱
# ✅ Verified from Graphiti Skill - Quick Reference > Searching the Graph
results = await graphiti.search(
    query="逆否命题的应用场景",
    num_results=10,
    center_node_uuid=None  # Optional: 从特定节点搜索
)

# 返回结果包含:
# - results.edges: 关系和事实
# - results.nodes: 实体节点
# - results.episodes: 原始数据源
for edge in results.edges:
    print(f"Fact: {edge.fact}")
    print(f"Valid from: {edge.valid_at}")
```

---

## Dev Notes (技术验证引用)

### Section 1: Graphiti API验证

**文档来源**: `@graphiti` Local Skill (2025-11-21验证)

**关键API验证清单**:

| API | 参数 | 返回值 | 验证状态 |
|-----|------|--------|---------|
| `Neo4jDriver.__init__()` | uri, user, password | Neo4jDriver | ✅ 已验证 |
| `Graphiti.__init__()` | driver: Neo4jDriver | Graphiti | ✅ 已验证 |
| `graphiti.add_episode()` | name, episode_body, source_description, reference_time | None (自动提取entities/edges) | ✅ 已验证 |
| `graphiti.search()` | query, num_results, center_node_uuid | SearchResults (edges, nodes, episodes) | ✅ 已验证 |

**验证来源**:
- Quick Reference > Installation and Setup
- Quick Reference > Adding Episodes
- Quick Reference > Searching the Graph

**注意**: Graphiti使用`search()`而非`hybrid_search()`，混合搜索(Semantic + BM25 + Graph)是内置行为

### Section 2: Neo4j连接验证

**文档来源**: Context7 MCP `/websites/neo4j_operations-manual-current`

**关键配置**:
- Bolt协议端口: 7687
- HTTP API端口: 7474
- 认证: `NEO4J_AUTH=neo4j/password`

**验证命令**:
```python
mcp__context7-mcp__get-library-docs(
    context7CompatibleLibraryID="/websites/neo4j_operations-manual-current",
    topic="connection configuration bolt"
)
```

### Section 3: 架构文档参考

**必读文档**:
1. `docs/architecture/GRAPHITI-KNOWLEDGE-GRAPH-INTEGRATION-ARCHITECTURE.md` - 完整集成设计
2. `docs/architecture/ADR-003-AGENTIC-RAG-ARCHITECTURE.md` - RAG架构决策
3. `docs/epics/EPIC-12-STORY-MAP.md` Lines 426-522 - Story规格

---

## Dependencies

### 外部依赖
- Neo4j Community Edition 5.0+
- Python graphiti-core库 (`pip install graphiti-core`)
- Docker (optional, for containerized deployment)

### Story依赖
- 无前置Story依赖 (Epic 12起点)

### 被依赖
- Story 12.5 (StateGraph构建) 依赖本Story
- Story 12.11 (Agent接口封装) 依赖本Story

---

## Risks

### R2: Neo4j性能瓶颈

**风险描述**: Neo4j在大规模概念图谱下可能出现性能瓶颈

**缓解策略**:
- AC 1.5包含性能测试 (P95 < 100ms)
- 预先进行POC性能测试
- 配置Neo4j索引优化
- 监控查询计划，优化Cypher查询

**回退方案**: 如果P95 > 200ms，考虑:
1. 增加Neo4j内存配置
2. 优化图谱模式设计
3. 添加查询缓存层

---

## DoD (Definition of Done)

### 代码完成
- [ ] Neo4j运行，可通过Browser访问
- [ ] Graphiti client连接成功，health check通过
- [ ] AC 1.1-1.5全部验收通过

### 测试完成
- [ ] 单元测试: `tests/test_graphiti_integration.py` (10个测试)
- [ ] 性能测试: P95延迟 < 100ms
- [ ] 数据持久化测试: 100个Episode无丢失

### 文档完成
- [ ] 设置指南: `docs/architecture/GRAPHITI-SETUP-GUIDE.md`
- [ ] API文档: GraphitiClient class docstring
- [ ] 配置说明: Neo4j连接参数文档

### 集成完成
- [ ] 代码位置: `src/memory_system/graphiti_client.py`
- [ ] 配置位置: `config/neo4j.yaml`
- [ ] 集成到: `canvas_utils.py` KnowledgeGraphLayer

---

## QA Checklist

- [ ] 所有AC验收通过
- [ ] 代码Review通过
- [ ] 测试覆盖率 >= 80%
- [ ] 性能指标达标
- [ ] 文档完整
- [ ] 无安全漏洞 (Neo4j凭证不硬编码)

---

**Story创建者**: SM Agent (Bob)
**创建日期**: 2025-11-21
**最后更新**: 2025-11-21
