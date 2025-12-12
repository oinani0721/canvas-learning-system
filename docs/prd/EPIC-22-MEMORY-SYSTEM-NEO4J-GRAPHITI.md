---
document_type: "PRD"
version: "1.0.0"
last_modified: "2025-12-11"
status: "draft"
iteration: 1

authors:
  - name: "PM Agent"
    role: "Product Manager"

reviewers:
  - name: "PO Agent"
    role: "Product Owner"
    approved: false

compatible_with:
  architecture: "v1.0"
  api_spec: "v1.0"

changes_from_previous:
  - "Initial Epic created for memory system (Neo4j/Graphiti)"

git:
  commit_sha: ""
  tag: ""

metadata:
  project_name: "Canvas Learning System"
  epic_count: 1
  fr_count: 4
  nfr_count: 3
---

# Epic 22: 记忆系统 (Neo4j/Graphiti)

**Epic ID**: Epic 22
**Epic名称**: 记忆系统 (Neo4j/Graphiti)
**优先级**: P1
**预计时间**: 2周 (40小时)
**状态**: 准备启动
**创建日期**: 2025-12-11
**负责PM**: PM Agent (John)
**依赖**: Epic 20完成 (多Provider稳定性)、Epic 21完成 (Agent流程)
**阻塞**: Epic 23 (RAG系统需要历史记忆)、Epic 24 (检验白板需要学习进度)

---

## 目录

1. [Epic概述](#epic概述)
2. [问题分析 (Bug 3详解)](#问题分析-bug-3详解)
3. [业务价值和目标](#业务价值和目标)
4. [技术架构](#技术架构)
5. [Story详细分解](#story详细分解)
6. [验收标准](#验收标准)
7. [风险评估](#风险评估)

---

## Epic概述

### 问题陈述

Canvas Learning System 的记忆系统完全不工作：

1. **Neo4j配置缺失**: `config.py`中没有`NEO4J_URI/USERNAME/PASSWORD`配置
2. **TemporalClient类不存在**: `src/agentic_rag/clients/temporal_client.py`文件缺失
3. **Graphiti MCP未连接**: Graphiti MCP服务器未配置或未启动
4. **学习历史丢失**: 每次会话后学习进度和历史不被保存

**后果**:
- 无法追踪用户学习进度
- 无法实现艾宾浩斯复习提醒
- Agent无法利用历史学习数据
- 跨会话的知识图谱不存在

### 解决方案

**构建完整的记忆系统**，支持：

1. ✅ Neo4j知识图谱存储学习实体和关系
2. ✅ Graphiti时序记忆支持学习历史
3. ✅ MCP协议集成Claude Code记忆能力
4. ✅ 学习历史查询和分析API

### Epic范围

**包含在Epic 22中**:
- ✅ Neo4j配置和连接
- ✅ TemporalClient实现 (Graphiti时序查询)
- ✅ Graphiti MCP集成
- ✅ 学习历史存储和查询API

**不包含在Epic 22中** (后续Epic):
- ❌ RAG智能推理 (Epic 23)
- ❌ 艾宾浩斯复习算法 (Epic 13 已有基础)
- ❌ 跨Canvas关联存储 (Epic 25)

---

## 问题分析 (Bug 3详解)

### 根因分析

```
记忆系统不工作
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│ 根因1: Neo4j配置缺失                                     │
│ ─────────────────────────────────────────────────────── │
│ 文件: backend/app/config.py                             │
│ 问题: 没有 NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD    │
│       相关配置项                                        │
└─────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│ 根因2: TemporalClient类不存在                            │
│ ─────────────────────────────────────────────────────── │
│ 预期文件: src/agentic_rag/clients/temporal_client.py    │
│ 实际状态: 文件不存在                                    │
│                                                         │
│ 使用场景:                                               │
│ - 存储学习事件 (学习时间、内容、得分)                    │
│ - 查询学习历史 (按时间范围、知识点)                      │
│ - 时序分析 (学习频率、复习间隔)                          │
└─────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│ 根因3: Graphiti MCP未配置                               │
│ ─────────────────────────────────────────────────────── │
│ 配置文件: claude_desktop_config.json 或类似             │
│ 问题: Graphiti MCP服务器条目缺失或未启动                │
│                                                         │
│ 期望配置:                                               │
│ {                                                       │
│   "mcpServers": {                                       │
│     "graphiti-memory": {                                │
│       "command": "python",                              │
│       "args": ["-m", "graphiti_mcp"]                    │
│     }                                                   │
│   }                                                     │
│ }                                                       │
└─────────────────────────────────────────────────────────┘
```

### 期望的记忆系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     Canvas Learning System                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Memory Layer                          │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │                                                          │   │
│  │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │   │
│  │   │ Neo4j        │  │ Graphiti     │  │ Graphiti MCP │ │   │
│  │   │ Knowledge    │  │ Temporal     │  │ Memory       │ │   │
│  │   │ Graph        │  │ Client       │  │ Server       │ │   │
│  │   ├──────────────┤  ├──────────────┤  ├──────────────┤ │   │
│  │   │ • 概念节点    │  │ • 学习事件   │  │ • Claude MCP │ │   │
│  │   │ • 关系边      │  │ • 时间戳     │  │ • add_memory │ │   │
│  │   │ • 属性存储    │  │ • 时序查询   │  │ • search     │ │   │
│  │   └──────────────┘  └──────────────┘  └──────────────┘ │   │
│  │          │                  │                  │        │   │
│  │          └──────────────────┼──────────────────┘        │   │
│  │                             │                            │   │
│  │                             ▼                            │   │
│  │              ┌──────────────────────────────┐           │   │
│  │              │      Memory Service          │           │   │
│  │              │ (Unified Query Interface)    │           │   │
│  │              └──────────────────────────────┘           │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 业务价值和目标

### 业务价值

| 价值项 | 重要性 | 说明 |
|--------|--------|------|
| **学习连续性** | ⭐⭐⭐⭐⭐ | 跨会话保持学习进度 |
| **个性化学习** | ⭐⭐⭐⭐⭐ | 基于历史推荐复习内容 |
| **知识图谱** | ⭐⭐⭐⭐ | 可视化学习的概念网络 |
| **复习提醒** | ⭐⭐⭐⭐ | 艾宾浩斯遗忘曲线自动提醒 |

### 目标

#### 短期目标 (Epic 22完成后)
- [ ] Neo4j连接正常建立
- [ ] 学习事件能够存储
- [ ] 学习历史能够查询
- [ ] Graphiti MCP服务正常运行

#### 质量指标
- [ ] Neo4j连接成功率 > 99%
- [ ] 写入延迟 < 100ms
- [ ] 查询延迟 < 500ms
- [ ] 数据持久化成功率 100%

---

## 技术架构

### 数据模型设计

```
┌─────────────────────────────────────────────────────────────────┐
│                     Neo4j 知识图谱模型                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  节点类型 (Labels):                                              │
│  ───────────────────────────────────────────────────────────    │
│  (:Concept)     - 学习概念/知识点                               │
│  (:CanvasNode)  - Canvas中的节点                                │
│  (:LearningSession) - 学习会话                                  │
│  (:User)        - 用户                                          │
│                                                                  │
│  关系类型 (Relationships):                                       │
│  ───────────────────────────────────────────────────────────    │
│  -[:CONTAINS]->       Canvas包含节点                            │
│  -[:LEARNED]->        用户学习了概念                            │
│  -[:REVIEWED]->       用户复习了概念                            │
│  -[:PREREQUISITE]->   概念的前置关系                            │
│  -[:RELATED_TO]->     概念之间的关联                            │
│  -[:SCORED]->         用户对概念的评分                          │
│                                                                  │
│  示例查询:                                                       │
│  ───────────────────────────────────────────────────────────    │
│  // 获取用户学习历史                                            │
│  MATCH (u:User {id: $userId})-[r:LEARNED]->(c:Concept)         │
│  RETURN c, r.timestamp, r.score                                 │
│                                                                  │
│  // 获取需要复习的概念 (艾宾浩斯)                                │
│  MATCH (u:User {id: $userId})-[r:LEARNED]->(c:Concept)         │
│  WHERE r.next_review < datetime()                               │
│  RETURN c ORDER BY r.next_review                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Graphiti 时序数据模型

```python
# 学习事件 Episode
{
    "episode_id": "ep_001",
    "timestamp": "2025-12-11T10:30:00Z",
    "event_type": "LEARNING",
    "data": {
        "canvas_path": "离散数学.canvas",
        "node_id": "node_123",
        "concept": "逆否命题",
        "agent_used": "basic-decomposition",
        "duration_seconds": 300,
        "score": 85
    }
}

# 学习实体 Entity
{
    "entity_id": "ent_concept_001",
    "entity_type": "Concept",
    "name": "逆否命题",
    "properties": {
        "difficulty": "medium",
        "subject": "离散数学",
        "first_learned": "2025-12-10",
        "total_reviews": 3
    }
}
```

---

## Story详细分解

### Story 22.1: Neo4j配置与连接

**Story ID**: Story-22.1
**标题**: Neo4j配置与连接
**优先级**: P1
**预计时间**: 6小时
**状态**: 待开发

#### 用户故事
```
作为系统管理员
我希望能够配置Neo4j数据库连接
以便系统能够存储和查询知识图谱数据
```

#### 验收标准 (AC)
- [ ] AC-22.1.1: config.py包含完整Neo4j配置 (URI, USERNAME, PASSWORD)
- [ ] AC-22.1.2: .env.example包含Neo4j配置模板
- [ ] AC-22.1.3: 启动时验证Neo4j连接
- [ ] AC-22.1.4: 连接失败时有友好错误提示
- [ ] AC-22.1.5: 支持连接池配置

#### 技术任务
1. **扩展config.py**
   ```python
   # backend/app/config.py 新增

   # Neo4j Configuration
   NEO4J_URI: str = Field(default="bolt://localhost:7687")
   NEO4J_USERNAME: str = Field(default="neo4j")
   NEO4J_PASSWORD: str = Field(default="")
   NEO4J_DATABASE: str = Field(default="neo4j")
   NEO4J_MAX_POOL_SIZE: int = Field(default=50)
   ```

2. **创建Neo4j客户端**
   ```python
   # backend/app/clients/neo4j_client.py

   from neo4j import AsyncGraphDatabase

   class Neo4jClient:
       def __init__(self, uri: str, username: str, password: str):
           self._driver = AsyncGraphDatabase.driver(
               uri, auth=(username, password)
           )

       async def verify_connectivity(self) -> bool:
           try:
               await self._driver.verify_connectivity()
               return True
           except Exception as e:
               logger.error(f"Neo4j connection failed: {e}")
               return False
   ```

3. **添加启动验证**
4. **更新.env.example**

#### 关键文件
- `backend/app/config.py` (修改)
- `backend/app/clients/neo4j_client.py` (新增)
- `backend/.env.example` (修改)

---

### Story 22.2: TemporalClient实现

**Story ID**: Story-22.2
**标题**: TemporalClient实现 (Graphiti时序查询)
**优先级**: P1
**预计时间**: 10小时
**状态**: 待开发

#### 用户故事
```
作为Agent服务
我希望能够存储和查询学习事件的时序数据
以便支持基于时间的学习分析
```

#### 验收标准 (AC)
- [ ] AC-22.2.1: 能够存储学习事件 (episode)
- [ ] AC-22.2.2: 能够按时间范围查询事件
- [ ] AC-22.2.3: 能够按实体类型查询
- [ ] AC-22.2.4: 支持时间窗口聚合查询
- [ ] AC-22.2.5: 与Graphiti库正确集成

#### 技术任务
1. **创建TemporalClient类**
   ```python
   # src/agentic_rag/clients/temporal_client.py

   from graphiti_core import Graphiti
   from graphiti_core.nodes import EpisodeType

   class TemporalClient:
       """Graphiti时序查询客户端"""

       def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
           self.graphiti = Graphiti(
               neo4j_uri=neo4j_uri,
               neo4j_user=neo4j_user,
               neo4j_password=neo4j_password
           )

       async def add_learning_episode(
           self,
           content: str,
           episode_type: str = "learning",
           metadata: Dict = None
       ) -> str:
           """添加学习事件"""
           episode = await self.graphiti.add_episode(
               name=f"learning_{datetime.now().isoformat()}",
               episode_body=content,
               source=EpisodeType.text,
               reference_time=datetime.now()
           )
           return episode.uuid

       async def search_by_time_range(
           self,
           start_time: datetime,
           end_time: datetime,
           entity_type: str = None
       ) -> List[Dict]:
           """按时间范围搜索"""
           results = await self.graphiti.search(
               query="",
               center_node_uuid=None,
               num_results=100
           )
           # 过滤时间范围
           filtered = [
               r for r in results
               if start_time <= r.created_at <= end_time
           ]
           return filtered
   ```

2. **实现Episode存储**
3. **实现时序查询**
4. **添加单元测试**

#### 关键文件
- `src/agentic_rag/clients/temporal_client.py` (新增)
- `src/agentic_rag/clients/__init__.py` (修改)
- `tests/unit/test_temporal_client.py` (新增)

---

### Story 22.3: Graphiti MCP集成

**Story ID**: Story-22.3
**标题**: Graphiti MCP集成
**优先级**: P1
**预计时间**: 8小时
**状态**: 待开发

#### 用户故事
```
作为Claude Code用户
我希望通过MCP协议与Graphiti记忆系统交互
以便在对话中使用学习历史
```

#### 验收标准 (AC)
- [ ] AC-22.3.1: Graphiti MCP服务器能够启动
- [ ] AC-22.3.2: Claude Code能够连接到MCP服务器
- [ ] AC-22.3.3: add_memory工具正常工作
- [ ] AC-22.3.4: search_memories工具正常工作
- [ ] AC-22.3.5: 配置文件模板完整

#### 技术任务
1. **创建MCP配置文件**
   ```json
   // .claude/mcp/graphiti-config.json
   {
     "mcpServers": {
       "graphiti-memory": {
         "command": "python",
         "args": ["-m", "graphiti_mcp"],
         "env": {
           "NEO4J_URI": "${NEO4J_URI}",
           "NEO4J_USERNAME": "${NEO4J_USERNAME}",
           "NEO4J_PASSWORD": "${NEO4J_PASSWORD}"
         }
       }
     }
   }
   ```

2. **验证MCP工具可用性**
3. **创建集成测试**
4. **编写使用文档**

#### 关键文件
- `.claude/mcp/graphiti-config.json` (新增)
- `docs/guides/graphiti-mcp-setup.md` (新增)

---

### Story 22.4: 学习历史存储与查询

**Story ID**: Story-22.4
**标题**: 学习历史存储与查询API
**优先级**: P1
**预计时间**: 8小时
**状态**: 待开发

#### 用户故事
```
作为前端应用
我希望能够通过API存储和查询学习历史
以便展示学习进度和推荐复习内容
```

#### 验收标准 (AC)
- [ ] AC-22.4.1: POST /api/v1/memory/episodes 存储学习事件
- [ ] AC-22.4.2: GET /api/v1/memory/episodes 查询学习历史
- [ ] AC-22.4.3: GET /api/v1/memory/concepts/{id}/history 查询概念学习历史
- [ ] AC-22.4.4: GET /api/v1/memory/review-suggestions 获取复习建议
- [ ] AC-22.4.5: 支持分页和过滤

#### 技术任务
1. **创建MemoryService**
   ```python
   # backend/app/services/memory_service.py

   class MemoryService:
       def __init__(
           self,
           neo4j_client: Neo4jClient,
           temporal_client: TemporalClient
       ):
           self.neo4j = neo4j_client
           self.temporal = temporal_client

       async def record_learning_event(
           self,
           user_id: str,
           canvas_path: str,
           node_id: str,
           concept: str,
           agent_type: str,
           score: Optional[int] = None
       ) -> str:
           """记录学习事件"""
           # 存储到Neo4j
           await self.neo4j.create_learning_relationship(
               user_id, concept, score
           )
           # 存储到Graphiti
           episode_id = await self.temporal.add_learning_episode(
               content=f"Learned {concept} using {agent_type}",
               metadata={
                   "canvas_path": canvas_path,
                   "node_id": node_id,
                   "score": score
               }
           )
           return episode_id

       async def get_review_suggestions(
           self,
           user_id: str,
           limit: int = 10
       ) -> List[Dict]:
           """获取复习建议 (基于艾宾浩斯)"""
           query = """
           MATCH (u:User {id: $userId})-[r:LEARNED]->(c:Concept)
           WHERE r.next_review < datetime()
           RETURN c.name as concept, r.next_review as due_date
           ORDER BY r.next_review
           LIMIT $limit
           """
           return await self.neo4j.run_query(query, userId=user_id, limit=limit)
   ```

2. **创建Memory API端点**
3. **添加Pydantic模型**
4. **添加API测试**

#### 关键文件
- `backend/app/services/memory_service.py` (新增)
- `backend/app/api/v1/endpoints/memory.py` (新增)
- `backend/app/models/memory_schemas.py` (新增)

---

## 验收标准

### Epic级别验收标准

| ID | 验收标准 | 验证方法 |
|----|----------|----------|
| AC-22.E1 | Neo4j连接正常 | 健康检查API |
| AC-22.E2 | 学习事件能够存储 | API测试 |
| AC-22.E3 | 学习历史能够查询 | API测试 |
| AC-22.E4 | Graphiti MCP正常运行 | MCP工具测试 |
| AC-22.E5 | 复习建议能够生成 | 功能测试 |

### 测试计划

1. **单元测试**
   - Neo4j客户端测试
   - TemporalClient测试
   - MemoryService测试

2. **集成测试**
   - 完整学习流程测试
   - MCP集成测试
   - API端到端测试

3. **性能测试**
   - 写入延迟测试
   - 查询延迟测试
   - 并发测试

---

## 风险评估

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| Neo4j服务不可用 | 中 | 高 | 本地Docker部署，健康检查 |
| Graphiti库版本兼容 | 中 | 中 | 锁定版本，集成测试 |
| MCP协议变更 | 低 | 中 | 关注官方更新 |
| 数据迁移 | 中 | 中 | 设计迁移脚本 |

---

## 依赖关系

### 上游依赖
- Epic 20: 多Provider稳定性 ⏳
- Epic 21: Agent端到端流程 ⏳

### 下游依赖
- Epic 23: RAG智能推理 (需要历史记忆)
- Epic 24: 检验白板 (需要学习进度)
- Epic 13: 艾宾浩斯复习 (需要记忆系统)

---

## 附录

### A. Neo4j Docker部署

```bash
# docker-compose.yml
version: '3.8'
services:
  neo4j:
    image: neo4j:5.15.0
    ports:
      - "7474:7474"  # HTTP
      - "7687:7687"  # Bolt
    environment:
      NEO4J_AUTH: neo4j/your_password
      NEO4J_PLUGINS: '["apoc"]'
    volumes:
      - neo4j_data:/data

volumes:
  neo4j_data:
```

### B. Graphiti安装

```bash
pip install graphiti-core
pip install graphiti-mcp
```

### C. API端点规范

```yaml
# Memory API

POST /api/v1/memory/episodes:
  description: 记录学习事件
  body:
    canvas_path: string
    node_id: string
    concept: string
    agent_type: string
    score: int (optional)
  response:
    episode_id: string

GET /api/v1/memory/episodes:
  description: 查询学习历史
  params:
    start_date: datetime (optional)
    end_date: datetime (optional)
    concept: string (optional)
    limit: int (default: 50)
  response:
    episodes: array

GET /api/v1/memory/review-suggestions:
  description: 获取复习建议
  params:
    limit: int (default: 10)
  response:
    suggestions:
      - concept: string
        due_date: datetime
        priority: high|medium|low
```
