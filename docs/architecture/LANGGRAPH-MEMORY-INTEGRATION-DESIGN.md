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

# Canvas学习系统 - LangGraph记忆系统集成设计

**文档版本**: v1.0
**创建日期**: 2025-11-11
**作者**: Claude Code
**关联PRD**: v1.1.3 Section 3.6
**状态**: 技术方案设计

---

## 📋 概述

本文档详细设计了Canvas学习系统的**双记忆架构**，明确LangGraph框架层记忆系统（Checkpointer）与3层业务记忆系统（Graphiti + Temporal + Semantic）的集成方案，定义职责边界、触发时机、一致性保证和故障处理机制。

### 核心目标

1. **职责明确**: 清晰定义LangGraph Checkpointer与3层业务记忆的职责边界
2. **无缝集成**: 实现框架层与业务层记忆系统的无缝协作
3. **一致性保证**: 强一致性（Canvas ↔ Checkpointer）+ 最终一致性（Canvas ↔ Graphiti）
4. **性能优化**: 异步写入、批量操作、分层缓存策略
5. **容错机制**: 关键路径 vs 非关键路径的错误处理

### 解决的关键问题

> **PRD反馈的3个核心问题**:
> 1. ❓ **何时触发记忆存储**: 缺乏明确的触发时机定义
> 2. ❓ **如何避免冲突**: LangGraph Checkpointer与业务记忆系统职责不清
> 3. ❓ **如何保证一致性**: 多层记忆系统的数据一致性缺失

---

## 🏗️ 一、双记忆架构设计

### 1.1 架构全景图

```mermaid
graph TB
    subgraph "Canvas学习系统"
        A[Canvas File] --> B[LangGraph Agent Node]
    end

    subgraph "框架层记忆 (LangGraph)"
        B --> C[LangGraph Checkpointer]
        C --> D[(PostgreSQL)]
        D --> E[State恢复]
    end

    subgraph "业务层记忆 (3层系统)"
        B --> F[Graphiti Knowledge Graph]
        B --> G[Temporal Memory]
        B --> H[Semantic Memory]

        F --> I[(Neo4j)]
        G --> J[(Neo4j)]
        H --> K[(LanceDB)]
    end

    E --> L[多轮对话上下文]
    I --> M[跨Canvas知识关联]
    J --> N[学习时间线追踪]
    K --> O[文档语义检索]

    style C fill:#e1f5fe
    style F fill:#fff3e0
    style G fill:#f3e5f5
    style H fill:#e8f5e9
```

---

### 1.2 双记忆架构职责分工

| 维度 | LangGraph Checkpointer | Graphiti | Temporal Memory | Semantic Memory |
|------|----------------------|----------|----------------|----------------|
| **数据类型** | Agent State（会话状态） | 知识图谱三元组 | 学习事件时间线 | 文档向量嵌入 |
| **时间范围** | 当前学习会话（短期） | 跨会话历史（长期） | 跨会话历史（长期） | 跨会话历史（长期） |
| **查询场景** | 恢复Agent执行上下文 | 跨Canvas知识关联 | 艾宾浩斯复习计划 | 相似文档检索 |
| **持久化** | PostgreSQL/InMemory | Neo4j | Neo4j | LanceDB + CUDA |
| **数据量级** | MB级（单会话State） | GB级（全局知识图谱） | GB级（事件时间序列） | GB级（向量数据库） |
| **一致性要求** | 强一致性（与Canvas） | 最终一致性 | 最终一致性 | 最终一致性 |
| **更新频率** | 每次Agent操作（高频） | Canvas操作后异步（低频） | Canvas操作后异步（低频） | 文档生成后异步（低频） |
| **查询性能** | <50ms（State恢复） | <200ms（简单查询） | <100ms（时间查询） | <150ms（向量检索） |

---

### 1.3 核心设计原则

**原则1: 分层职责**
- **框架层（Checkpointer）**: 负责Agent State管理，无业务逻辑
- **业务层（3层记忆）**: 负责业务知识管理，不感知Agent State

**原则2: 一致性分级**
- **强一致性**: Canvas文件 ↔ LangGraph State（必须同步）
- **最终一致性**: Canvas文件 ↔ Graphiti/Temporal/Semantic（允许延迟）

**原则3: 关键路径优先**
- **关键路径**: Canvas操作 + Checkpointer持久化（失败必须回滚）
- **非关键路径**: 业务记忆存储（失败仅记录日志，不影响主流程）

**原则4: 性能优先**
- Checkpointer写入异步化（<100ms）
- 业务记忆批量写入（批量10个操作）
- 分层缓存（L1-L4）

---

## 🔧 二、LangGraph Checkpointer详细设计

### 2.1 Checkpointer选型和配置

**生产环境推荐**: PostgresSaver

```python
from langgraph.checkpoint.postgres import PostgresSaver

# 数据库连接配置
DB_URI = "postgresql://canvas_user:password@localhost:5432/canvas_learning"
checkpointer = PostgresSaver.from_conn_string(DB_URI)

# PostgreSQL数据库schema
CREATE TABLE IF NOT EXISTS checkpoints (
    thread_id TEXT NOT NULL,
    checkpoint_id TEXT NOT NULL,
    parent_checkpoint_id TEXT,
    checkpoint JSONB NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (thread_id, checkpoint_id)
);

CREATE INDEX idx_thread_id ON checkpoints(thread_id);
CREATE INDEX idx_created_at ON checkpoints(created_at);
```

**开发/测试环境**: InMemorySaver

```python
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()  # 快速但不持久化
graph = builder.compile(checkpointer=checkpointer)
```

**配置对比**:

| 特性 | PostgresSaver | InMemorySaver |
|------|--------------|--------------|
| 持久化 | ✅ 是（PostgreSQL） | ❌ 否（进程内存） |
| 写入速度 | ~50ms | ~5ms |
| 恢复能力 | ✅ 可恢复历史会话 | ❌ 进程重启丢失 |
| 适用环境 | 生产环境 | 开发/测试 |
| 并发支持 | ✅ 多进程安全 | ⚠️ 单进程 |

---

### 2.2 thread_id设计策略

**thread_id格式**: `canvas_{canvas_name}_{session_id}`

```python
def generate_thread_id(canvas_path: str, session_id: str) -> str:
    """生成thread_id

    Args:
        canvas_path: Canvas文件路径
        session_id: 唯一会话标识符（UUID v4）

    Returns:
        thread_id字符串

    Examples:
        >>> generate_thread_id("笔记库/离散数学/离散数学.canvas", "a1b2c3d4-...")
        "canvas_离散数学_a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    """
    canvas_name = Path(canvas_path).stem
    return f"canvas_{canvas_name}_{session_id}"
```

**设计原则**:

1. **唯一性**: 每个学习会话独立thread_id，避免状态混淆
   ```python
   # 同一Canvas的两个会话有不同的thread_id
   session1 = "a1b2c3d4-..."
   session2 = "b2c3d4e5-..."
   thread1 = "canvas_离散数学_a1b2c3d4-..."  # 互不干扰
   thread2 = "canvas_离散数学_b2c3d4e5-..."
   ```

2. **可追溯性**: 从thread_id可直接定位Canvas文件和会话
   ```python
   # 从thread_id解析Canvas名称
   def parse_thread_id(thread_id: str) -> tuple[str, str]:
       parts = thread_id.split("_", 2)
       canvas_name = parts[1]
       session_id = parts[2]
       return canvas_name, session_id
   ```

3. **隔离性**: 同一Canvas的不同会话互不干扰
   - 不同用户 → 不同session_id → 不同thread_id
   - 同一用户的不同学习会话 → 不同session_id

4. **跨会话查询**: Temporal Memory可通过canvas_name查询历史所有会话
   ```python
   # Temporal Memory查询所有关于"离散数学"的学习会话
   sessions = temporal_memory.query_sessions_by_canvas(canvas_name="离散数学")
   ```

**生命周期管理**:

```python
class SessionLifecycleManager:
    """会话生命周期管理"""

    def create_session(self, canvas_path: str, user_id: str) -> str:
        """创建新会话"""
        session_id = str(uuid.uuid4())
        thread_id = generate_thread_id(canvas_path, session_id)

        # 记录会话元信息到Temporal Memory
        temporal_memory.create_session({
            "session_id": session_id,
            "canvas_path": canvas_path,
            "user_id": user_id,
            "created_at": datetime.now(),
            "status": "active"
        })

        return session_id

    def close_session(self, session_id: str):
        """关闭会话"""
        temporal_memory.update_session(session_id, {
            "status": "closed",
            "closed_at": datetime.now()
        })

    def cleanup_old_sessions(self, days=30):
        """清理超过30天无活动的会话"""
        cutoff_date = datetime.now() - timedelta(days=days)
        old_sessions = temporal_memory.query_inactive_sessions(cutoff_date)

        for session in old_sessions:
            # 删除对应的checkpoints
            checkpointer.delete_checkpoints_by_thread_id(
                generate_thread_id(session["canvas_path"], session["session_id"])
            )
```

---

### 2.3 config参数结构定义

**完整config实现**:

```python
from typing import TypedDict
from pathlib import Path

class LangGraphConfig(TypedDict):
    """LangGraph调用配置参数"""
    configurable: dict

def create_langgraph_config(
    canvas_path: str,
    user_id: str,
    session_id: str,
    checkpoint_id: str | None = None
) -> LangGraphConfig:
    """生成LangGraph graph.invoke()所需的config参数

    Args:
        canvas_path: Canvas文件绝对路径
        user_id: 用户唯一标识符
        session_id: 会话唯一标识符（UUID v4）
        checkpoint_id: 可选，指定恢复的checkpoint ID

    Returns:
        符合LangGraph标准的config字典
    """
    canvas_name = Path(canvas_path).stem
    thread_id = generate_thread_id(canvas_path, session_id)

    config: LangGraphConfig = {
        "configurable": {
            # LangGraph核心参数
            "thread_id": thread_id,  # 会话标识符
            "checkpoint_id": checkpoint_id,  # 恢复的checkpoint ID（可选）

            # Canvas学习系统业务参数
            "canvas_path": canvas_path,  # Canvas文件路径
            "user_id": user_id,          # 用户ID
            "session_id": session_id,    # 会话ID
            "canvas_name": canvas_name,  # Canvas名称（方便调试）

            # 可选扩展参数
            "checkpoint_ns": "canvas_learning",  # 命名空间隔离
        }
    }

    return config
```

**使用示例**:

```python
# 场景1: 创建新会话
session_id = str(uuid.uuid4())
config = create_langgraph_config(
    canvas_path="C:/Users/ROG/托福/笔记库/离散数学/离散数学.canvas",
    user_id="user_12345",
    session_id=session_id
)

result = graph.invoke({
    "canvas_path": config["configurable"]["canvas_path"],
    "operation": "decomposition",
    "concept": "逆否命题"
}, config=config)

# 场景2: 恢复历史checkpoint
historical_config = create_langgraph_config(
    canvas_path="C:/Users/ROG/托福/笔记库/离散数学/离散数学.canvas",
    user_id="user_12345",
    session_id=existing_session_id,
    checkpoint_id="checkpoint_abc123"  # 指定checkpoint
)

historical_state = graph.get_state(historical_config)
```

---

### 2.4 State Schema定义

**CanvasLearningState完整定义**:

```python
from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

class CanvasLearningState(TypedDict):
    """Canvas学习系统的LangGraph State Schema"""

    # ========== 会话元信息 ==========
    canvas_path: str              # Canvas文件绝对路径
    user_id: str                  # 用户唯一标识符
    session_id: str               # 会话唯一标识符

    # ========== 当前操作上下文 ==========
    operation: Literal[
        "decomposition",          # 基础拆解
        "deep_decomposition",     # 深度拆解
        "scoring",                # 评分
        "explanation",            # 解释生成
        "verification",           # 检验问题生成
        "concurrent_analysis"     # 并发分析
    ]
    concept: str                  # 当前处理的概念名称
    target_nodes: list[str]       # 当前操作的节点IDs

    # ========== Agent输出结果 ==========
    decomposition_results: dict[str, list[str]]  # {node_id: [questions]}
    explanation_results: dict[str, str]          # {node_id: doc_path}
    scoring_results: dict[str, dict]             # {node_id: scoring_data}

    # 示例scoring_data结构:
    # {
    #     "accuracy": 22,
    #     "imagery": 18,
    #     "completeness": 20,
    #     "originality": 15,
    #     "total": 75,
    #     "color": "3",  # 紫色
    #     "recommendations": ["clarification-path", "oral-explanation"]
    # }

    # ========== LangChain messages（对话历史） ==========
    messages: Annotated[list, add_messages]  # 对话消息累积

    # ========== 执行状态记录 ==========
    last_operation: str           # 最后执行的操作
    last_timestamp: str           # 最后操作时间（ISO 8601格式）
    tasks_completed: int          # 已完成任务数
    tasks_failed: int             # 失败任务数
    error_log: list[dict]         # 错误日志

    # 示例error_log条目:
    # {
    #     "timestamp": "2025-11-11T14:30:00",
    #     "agent": "decomposition",
    #     "node_id": "red_001",
    #     "error": "Canvas write failed: Permission denied",
    #     "retry_count": 2
    # }
```

**State更新示例**:

```python
def basic_decomposition_node(state: CanvasLearningState) -> CanvasLearningState:
    """基础拆解Agent节点"""
    # Step 1: 生成拆解问题
    questions = generate_decomposition_questions(state["concept"])

    # Step 2: 写入Canvas（关键路径）
    write_questions_to_canvas(
        state["canvas_path"],
        questions,
        config={"thread_id": generate_thread_id(state["canvas_path"], state["session_id"])}
    )

    # Step 3: 异步存储到Graphiti（非关键路径）
    try:
        asyncio.create_task(
            store_to_graphiti(state["session_id"], "decomposition", questions)
        )
    except Exception as e:
        logger.error(f"Graphiti storage failed: {e}")

    # Step 4: 返回更新的State（LangGraph自动持久化）
    return {
        **state,
        "decomposition_results": {state["concept"]: questions},
        "tasks_completed": state["tasks_completed"] + 1,
        "last_operation": "decomposition",
        "last_timestamp": datetime.now().isoformat()
    }
```

---

## 🔗 三、与3层业务记忆系统集成

### 3.1 Graphiti知识图谱集成

**职责定义**:
- **存储内容**: Canvas节点、边、概念关系三元组
- **查询场景**: 跨Canvas知识关联、概念语义检索
- **触发时机**: Canvas操作成功后异步存储

**集成方式**:

```python
async def store_to_graphiti(
    session_id: str,
    operation_type: str,
    canvas_path: str,
    data: dict,
    config: dict
) -> None:
    """异步存储到Graphiti知识图谱

    Args:
        session_id: 会话ID
        operation_type: 操作类型（decomposition/scoring/explanation）
        canvas_path: Canvas文件路径
        data: 要存储的数据
        config: LangGraph config参数
    """
    try:
        # Step 1: 构建Graphiti三元组
        triples = build_graphiti_triples(operation_type, data)

        # Step 2: 批量写入Neo4j
        await graphiti_client.batch_write(triples)

        # Step 3: 记录到Temporal Memory
        await temporal_memory.log_event({
            "session_id": session_id,
            "event_type": "graphiti_sync",
            "timestamp": datetime.now(),
            "data": {
                "operation_type": operation_type,
                "triples_count": len(triples)
            }
        })

    except Exception as e:
        # 记录错误但不阻塞主流程
        logger.error(f"Graphiti storage failed for session {session_id}: {e}")
        await temporal_memory.log_event({
            "session_id": session_id,
            "event_type": "graphiti_sync_failed",
            "timestamp": datetime.now(),
            "error": str(e)
        })
```

**数据示例**:

```cypher
// Graphiti存储的三元组示例
CREATE (c:Canvas {
    name: "离散数学",
    path: "笔记库/离散数学/离散数学.canvas",
    created_at: "2025-10-01"
})

CREATE (concept:Concept {
    name: "逆否命题",
    domain: "离散数学",
    first_seen: "2025-11-11"
})

CREATE (node:Node {
    canvas_id: "red_001",
    text: "什么是逆否命题?",
    color: "1",  // 红色
    created_at: "2025-11-11T14:30:00"
})

CREATE (understanding:UnderstandingState {
    node_id: "yellow_123",
    accuracy: 22,
    imagery: 18,
    completeness: 20,
    originality: 15,
    total: 75,
    timestamp: "2025-11-11T14:35:00"
})

// 关系
CREATE (c)-[:CONTAINS]->(node)
CREATE (node)-[:IS_ABOUT]->(concept)
CREATE (node)-[:HAS_UNDERSTANDING_STATE]->(understanding)
CREATE (understanding)-[:CREATED_IN_SESSION]->(session)
```

---

### 3.2 Temporal Memory集成

**职责定义**:
- **存储内容**: 学习事件时间线、进度追踪、艾宾浩斯复习计划
- **查询场景**: 学习历史查询、复习计划生成
- **触发时机**: Canvas操作成功后异步存储

**集成方式**:

```python
async def store_to_temporal_memory(
    session_id: str,
    event_type: str,
    timestamp: datetime,
    data: dict
) -> None:
    """异步存储到Temporal Memory

    Args:
        session_id: 会话ID
        event_type: 事件类型
        timestamp: 事件时间
        data: 事件数据
    """
    event = {
        "session_id": session_id,
        "event_type": event_type,
        "timestamp": timestamp.isoformat(),
        "data": data
    }

    try:
        await temporal_memory_client.insert_event(event)
    except Exception as e:
        logger.error(f"Temporal memory storage failed: {e}")
```

**Neo4j Schema (Temporal Memory)**:

```cypher
// 学习事件节点
CREATE (e:LearningEvent {
    id: randomUUID(),
    session_id: $session_id,
    event_type: $event_type,
    timestamp: datetime(),
    data: $data
})

// 时序索引（Neo4j）
CREATE INDEX learning_event_timestamp IF NOT EXISTS FOR (e:LearningEvent) ON (e.timestamp);
CREATE INDEX learning_event_session IF NOT EXISTS FOR (e:LearningEvent) ON (e.session_id);
CREATE INDEX learning_event_type IF NOT EXISTS FOR (e:LearningEvent) ON (e.event_type);
```

**事件类型**:

```python
# 学习事件类型枚举
class LearningEventType(Enum):
    DECOMPOSITION_COMPLETED = "decomposition_completed"
    SCORING_COMPLETED = "scoring_completed"
    EXPLANATION_GENERATED = "explanation_generated"
    COLOR_TRANSITION = "color_transition"  # 红→紫→绿
    REVIEW_SCHEDULED = "review_scheduled"  # 艾宾浩斯复习计划
    GRAPHITI_SYNC = "graphiti_sync"
    SEMANTIC_SYNC = "semantic_sync"
```

---

### 3.3 Semantic Memory集成

**职责定义**:
- **存储内容**: AI生成的解释文档向量嵌入
- **查询场景**: 相似文档检索、语义搜索
- **触发时机**: 解释文档生成后异步存储

**集成方式**:

```python
async def store_to_semantic_memory(
    doc_path: str,
    concept: str,
    agent_type: str,
    session_id: str
) -> None:
    """异步存储到Semantic Memory

    Args:
        doc_path: 文档路径
        concept: 概念名称
        agent_type: 生成文档的Agent类型
        session_id: 会话ID
    """
    try:
        # Step 1: 读取文档内容
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Step 2: 生成向量嵌入
        # Step 3: 生成向量嵌入 (CUDA加速)
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2', device='cuda')  # GPU加速
        embedding = model.encode(content)  # 768维向量

        # Step 4: 写入LanceDB
        await lance_table.add([{
            "id": str(uuid.uuid4()),
            "text": content,
            "vector": embedding.tolist(),
            "doc_path": doc_path,
            "concept": concept,
            "agent_type": agent_type,
            "session_id": session_id,
            "created_at": datetime.now().isoformat()
        }])

        # Step 5: 创建或更新FTS索引(BM25)
        await lance_table.create_fts_index("text", replace=True)

    except Exception as e:
        logger.error(f"Semantic memory storage failed: {e}")
```

**LanceDB Table配置**:

```python
# ✅ Verified from LanceDB Context7
import lancedb
from lancedb.pydantic import LanceModel, Vector
from lancedb.embeddings import get_registry

# 初始化LanceDB客户端
db = lancedb.connect("./data/lancedb")

# 定义Schema with Pydantic
embedder = get_registry().get("sentence-transformers").create()

class CanvasDocSchema(LanceModel):
    text: str = embedder.SourceField()
    vector: Vector(embedder.ndims()) = embedder.VectorField()
    doc_path: str
    concept: str
    agent_type: str
    session_id: str
    created_at: str

# 创建或获取table
table = db.create_table(
    "canvas_learning_docs",
    schema=CanvasDocSchema,
    mode="overwrite"  # 首次创建时使用,后续使用open_table()
)

# 创建BM25全文索引(支持Hybrid Search)
table.create_fts_index("text", replace=True)

# 向量维度: 768 (sentence-transformers/all-MiniLM-L6-v2)
# GPU加速: PyTorch CUDA (需要 >=4GB VRAM)
# Lance数据格式: Parquet演进版,100x查询性能提升
```

---

### 3.4 记忆系统调度矩阵

| Canvas操作 | LangGraph Checkpointer | Graphiti | Temporal Memory | Semantic Memory | 精确时机 |
|-----------|----------------------|----------|----------------|----------------|---------|
| **基础拆解** | ✅ 同步 | ✅ 异步 | ✅ 异步 | ❌ | Agent Node返回时 |
| **深度拆解** | ✅ 同步 | ✅ 异步 | ✅ 异步 | ❌ | Agent Node返回时 |
| **评分** | ✅ 同步 | ✅ 异步 | ✅ 异步 | ❌ | Agent Node返回时 |
| **生成解释** | ✅ 同步 | ✅ 异步 | ✅ 异步 | ✅ 异步 | 文档写入磁盘后 |
| **颜色流转** | ✅ 同步 | ✅ 异步 | ✅ 异步 | ❌ | Canvas文件更新后 |
| **创建检验白板** | ✅ 同步 | ✅ 异步 | ✅ 异步 | ❌ | 新Canvas文件创建后 |

**6步精确时序**（以basic-decomposition为例）:

```python
async def basic_decomposition_node(state: CanvasLearningState):
    """基础拆解Agent节点 - 展示完整的6步时序"""

    # Step 1: 生成拆解问题
    questions = generate_decomposition_questions(state["concept"])

    # Step 2: 写入Canvas（关键路径 - 必须成功）
    try:
        write_questions_to_canvas(state["canvas_path"], questions)
    except Exception as e:
        # Canvas写入失败 → 整个操作失败
        raise CanvasWriteError(f"Canvas write failed: {e}")

    # ⏰ 时刻1: Canvas文件写入成功

    # Step 3: 返回新State（触发Checkpointer持久化 - 关键路径）
    new_state = {
        **state,
        "decomposition_results": {state["concept"]: questions},
        "tasks_completed": state["tasks_completed"] + 1,
        "last_operation": "decomposition",
        "last_timestamp": datetime.now().isoformat()
    }

    # ⏰ 时刻2: LangGraph自动持久化State到Checkpointer

    # Step 4: 异步存储到Graphiti（非关键路径 - 允许失败）
    asyncio.create_task(
        store_to_graphiti(
            state["session_id"],
            "decomposition",
            state["canvas_path"],
            questions,
            config={}
        )
    )

    # ⏰ 时刻3: Graphiti存储任务已入队（实际写入可能延迟1-5秒）

    # Step 5: 异步存储到Temporal Memory（非关键路径）
    asyncio.create_task(
        store_to_temporal_memory(
            state["session_id"],
            "decomposition_completed",
            datetime.now(),
            {"concept": state["concept"], "question_count": len(questions)}
        )
    )

    # ⏰ 时刻4: Temporal Memory存储任务已入队

    # Step 6: 返回新State
    return new_state

    # ⏰ 时刻5: Agent Node执行完成
    # ⏰ 时刻6: graph.invoke()返回（用户感知的完成时刻）
```

---

## 🔒 四、一致性保证与故障处理

### 4.1 强一致性路径（Canvas ↔ Checkpointer）

**定义**: Canvas操作与LangGraph State更新必须同步，任一失败则整体回滚

```python
def agent_node_with_strong_consistency(state: CanvasLearningState):
    """确保Canvas操作和State更新的强一致性"""

    # Step 1: 备份Canvas（事务开始）
    backup = backup_canvas(state["canvas_path"])

    try:
        # Step 2: 执行Canvas操作
        result = write_to_canvas(state["canvas_path"], new_data)

        # Step 3: 返回新State（LangGraph自动持久化）
        new_state = {
            **state,
            "last_operation": "decomposition",
            "decomposition_results": result,
            "last_timestamp": datetime.now().isoformat()
        }

        # ✅ 成功路径：Canvas和State都成功
        return new_state

    except Exception as e:
        # ❌ 失败路径：回滚Canvas
        restore_canvas(state["canvas_path"], backup)

        # 不返回新State → LangGraph不创建新checkpoint
        raise CanvasOperationError(f"Operation failed: {e}")

    # 强一致性保证：
    # - Canvas更新成功 ⇔ Checkpointer创建新checkpoint
    # - Canvas更新失败 ⇔ Checkpointer不创建checkpoint
```

---

### 4.2 最终一致性路径（Canvas ↔ 业务记忆）

**定义**: Canvas操作成功后异步存储到Graphiti/Temporal/Semantic，允许延迟和失败

```python
def agent_node_with_eventual_consistency(state: CanvasLearningState):
    """Canvas操作成功，业务记忆异步存储（允许失败）"""

    # Step 1: Canvas操作（关键路径）
    write_to_canvas(state["canvas_path"], new_data)

    # Step 2: 返回新State（关键路径）
    new_state = {
        **state,
        "decomposition_results": new_data,
        "last_timestamp": datetime.now().isoformat()
    }

    # Step 3: 异步存储到业务记忆（非关键路径）
    try:
        asyncio.create_task(store_to_graphiti(state["session_id"], new_data))
        asyncio.create_task(store_to_temporal_memory(state["session_id"], ...))
    except Exception as e:
        # ✅ 仅记录日志，不影响Canvas操作成功
        logger.error(f"Business memory storage failed: {e}")

        # 记录到error_log，供后续重试
        new_state["error_log"].append({
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "retry_count": 0
        })

    return new_state

    # 最终一致性保证：
    # - Canvas立即可见（强一致）
    # - Graphiti/Temporal延迟可见（允许1-5秒延迟）
    # - 失败时通过重试机制最终同步
```

---

### 4.3 冲突处理策略

**场景1: Checkpointer与Graphiti数据不一致**

```python
async def detect_and_fix_inconsistency():
    """检测并修复Checkpointer与Graphiti的数据不一致"""

    # Step 1: 从Checkpointer恢复State
    config = create_langgraph_config(canvas_path, user_id, session_id)
    state = graph.get_state(config)

    # Step 2: 从Canvas文件读取实际数据
    canvas_data = read_canvas(canvas_path)

    # Step 3: 从Graphiti查询存储的数据
    graphiti_data = await graphiti_client.query_canvas_nodes(canvas_path)

    # Step 4: 三方对比
    if not verify_consistency(state.values, canvas_data, graphiti_data):
        logger.warning("Inconsistency detected!")

        # Step 5: 修复策略（Canvas = 真实数据源）
        # Canvas文件 → Checkpointer
        if canvas_data != state.values:
            logger.info("Syncing Checkpointer from Canvas")
            # 重新执行操作，创建新checkpoint
            graph.invoke({...}, config=config)

        # Canvas文件 → Graphiti
        if canvas_data != graphiti_data:
            logger.info("Re-syncing Graphiti from Canvas")
            await graphiti_client.full_sync(canvas_data)
```

**场景2: 回滚操作导致的数据冲突**

```python
def handle_rollback_conflict(
    canvas_path: str,
    session_id: str,
    checkpoint_id: str
):
    """回滚时确保三个系统一致"""

    # Step 1: 回滚Canvas文件（从备份）
    backup_path = f".canvas_backups/{Path(canvas_path).stem}_{checkpoint_id}.canvas"
    shutil.copy(backup_path, canvas_path)

    # Step 2: 回滚LangGraph State（从checkpoint）
    config = create_langgraph_config(canvas_path, user_id, session_id)
    config["configurable"]["checkpoint_id"] = checkpoint_id
    state = graph.get_state(config)

    # Step 3: 标记Graphiti操作为已撤销（不删除，保留历史）
    mark_graphiti_operations_as_reverted(
        session_id,
        after_timestamp=state.values["last_timestamp"]
    )

    # Step 4: 标记Temporal Memory事件为已撤销
    temporal_memory.mark_events_as_reverted(
        session_id,
        after_timestamp=state.values["last_timestamp"]
    )

    # Step 5: 验证一致性
    assert verify_consistency(canvas_path, state, graphiti_data)

    logger.info(f"Rollback completed: {canvas_path} → checkpoint {checkpoint_id}")
```

---

## ⚡ 五、性能优化策略

### 5.1 批量操作优化

**问题**: 每次graph.invoke()都创建新checkpoint，100个节点 = 100次数据库写入

**解决方案**: 批量处理

```python
# ❌ 低效：逐个节点调用
for node_id in yellow_nodes:  # 100个节点
    graph.invoke({
        "operation": "scoring",
        "target_nodes": [node_id],
        ...
    }, config)
    # 100次checkpoint写入 ≈ 5秒

# ✅ 高效：批量处理
graph.invoke({
    "operation": "batch_scoring",
    "target_nodes": yellow_nodes,  # 一次传入100个节点
    ...
}, config)
# 1次checkpoint写入 ≈ 50ms
```

**性能提升**: 100倍写入次数减少，5秒 → 50ms

---

### 5.2 异步持久化

**LangGraph内部实现**:

```python
# LangGraph的checkpointer.put()已经是异步的
async def put(self, config, checkpoint, metadata):
    """异步写入checkpoint（非阻塞）"""
    # 在后台线程中执行数据库写入
    await self._async_write_to_db(checkpoint)

# Agent Node无需等待checkpoint写入完成
def agent_node(state):
    # 返回新State后立即返回，不阻塞
    return new_state
    # LangGraph在后台异步持久化
```

---

### 5.3 分层缓存策略

```mermaid
graph TD
    A[查询请求] --> B{L1缓存?}
    B -->|命中| C[返回State<10ms>]
    B -->|未命中| D{L2缓存?}
    D -->|命中| E[返回Checkpoint<50ms>]
    D -->|未命中| F{L3缓存?}
    F -->|命中| G[返回Graphiti<20ms>]
    F -->|未命中| H[查询Neo4j<200ms>]

    style B fill:#e1f5fe
    style D fill:#fff3e0
    style F fill:#f3e5f5
```

**实现**:

```python
class MultiLayerCache:
    """4层缓存架构"""

    def __init__(self):
        self.l1_cache = {}  # 内存缓存（当前会话State）
        self.l2_cache = None  # Checkpointer（数据库）
        self.l3_cache = None  # Redis（Graphiti查询缓存）
        self.l4_storage = None  # Neo4j（完整知识图谱）

    async def get_state(self, session_id: str) -> dict:
        """查询State（L1 → L2 → L3 → L4）"""

        # L1: 内存缓存
        if session_id in self.l1_cache:
            logger.debug("L1 cache hit")
            return self.l1_cache[session_id]

        # L2: Checkpointer（PostgreSQL）
        config = create_langgraph_config(..., session_id=session_id)
        state = graph.get_state(config)
        if state:
            logger.debug("L2 cache hit")
            self.l1_cache[session_id] = state.values  # 填充L1
            return state.values

        # L3: Graphiti Redis缓存
        cached_data = await redis_client.get(f"session:{session_id}")
        if cached_data:
            logger.debug("L3 cache hit")
            return json.loads(cached_data)

        # L4: Neo4j完整查询
        data = await graphiti_client.query_session(session_id)
        logger.debug("L4 storage hit")

        # 回填缓存
        await redis_client.set(f"session:{session_id}", json.dumps(data), ex=300)

        return data
```

**性能对比**:

| 缓存层 | 延迟 | 命中率 | 容量 |
|-------|------|-------|------|
| L1（内存） | <10ms | 90% | 100MB |
| L2（Checkpointer） | <50ms | 95% | 10GB |
| L3（Redis） | <20ms | 80% | 100GB |
| L4（Neo4j） | <200ms | 100% | 1TB+ |

---

### 5.4 延迟Graphiti写入

**问题**: 每次Canvas操作都触发Graphiti写入，频率过高

**解决方案**: 消息队列 + 批量写入

```python
import asyncio
from asyncio import Queue

graphiti_write_queue: Queue = Queue()

async def batch_graphiti_writer():
    """后台任务：批量写入Graphiti"""
    while True:
        batch = []

        # 攒10个操作或等待1秒
        for _ in range(10):
            try:
                item = await asyncio.wait_for(graphiti_write_queue.get(), timeout=1.0)
                batch.append(item)
            except asyncio.TimeoutError:
                break

        if batch:
            # 批量写入Neo4j
            await graphiti_client.batch_write(batch)
            logger.info(f"Batch写入Graphiti: {len(batch)}条")

        await asyncio.sleep(0.1)  # 短暂休眠

# Agent节点中异步入队
async def agent_node(state):
    # Canvas操作
    write_to_canvas(...)

    # 入队Graphiti写入（不阻塞）
    await graphiti_write_queue.put({
        "type": "decomposition",
        "session_id": state["session_id"],
        "data": questions
    })

    return new_state

# 启动后台写入任务
asyncio.create_task(batch_graphiti_writer())
```

**性能提升**:
- 写入频率: 每操作1次 → 每秒1次（攒10个）
- Neo4j连接数: 100次 → 10次
- 总延迟: 不变（异步，用户无感知）

---

## ✅ 六、验收标准

### 6.1 功能验收

- ✅ **AC 1**: PostgresSaver和InMemorySaver均可正常工作
- ✅ **AC 2**: thread_id格式符合`canvas_{name}_{session_id}`规范
- ✅ **AC 3**: config参数包含所有必需字段（thread_id, canvas_path, user_id, session_id）
- ✅ **AC 4**: graph.compile(checkpointer=checkpointer)成功编译
- ✅ **AC 5**: 多轮对话可复用相同thread_id并累积State
- ✅ **AC 6**: graph.get_state()可恢复历史State
- ✅ **AC 7**: 回滚操作同步恢复Canvas文件和LangGraph State
- ✅ **AC 8**: Checkpointer和Graphiti可独立工作，互不阻塞
- ✅ **AC 9**: Canvas操作失败时，Checkpointer不创建checkpoint，Graphiti不存储
- ✅ **AC 10**: Checkpointer写入失败时，Canvas操作失败并回滚
- ✅ **AC 11**: Graphiti写入失败时，Canvas操作成功，仅记录日志
- ✅ **AC 12**: 多轮对话可恢复Checkpointer的State，同时查询Graphiti的历史
- ✅ **AC 13**: 跨Canvas查询仅使用Graphiti，不访问Checkpointer

### 6.2 性能验收

- ✅ **AC 14**: 单次checkpoint写入 < 100ms（PostgresSaver）
- ✅ **AC 15**: 批量操作（10个节点）总耗时 < 3秒
- ✅ **AC 16**: checkpoint清理脚本可正常运行
- ✅ **AC 17**: Graphiti异步写入不阻塞Agent执行
- ✅ **AC 18**: 批量操作减少90% checkpoint写入次数
- ✅ **AC 19**: L1缓存命中率 > 80%
- ✅ **AC 20**: Graphiti批量写入延迟 < 5秒

### 6.3 一致性验收

- ✅ **AC 21**: Canvas文件 ↔ Checkpointer State: 强一致性
- ✅ **AC 22**: Canvas文件 ↔ Graphiti: 最终一致性（<5秒同步延迟）
- ✅ **AC 23**: 回滚后Canvas文件、LangGraph State、业务记忆三者一致
- ✅ **AC 24**: 一致性校验脚本可检测并修复不一致

### 6.4 集成验收（与Epic 12 Stories配合）

- ✅ **AC 25**: Story 12.1 checkpointer配置可被Story 12.2调用
- ✅ **AC 26**: Story 12.5可使用本章节定义的config结构
- ✅ **AC 27**: Story 12.7测试用例覆盖checkpointer所有场景

---

## 📚 七、实施路线图

### Phase 1: Checkpointer基础设施 (1周)

- [ ] PostgreSQL数据库搭建和schema创建
- [ ] PostgresSaver和InMemorySaver配置
- [ ] thread_id生成和管理
- [ ] config参数结构实现
- [ ] 基础StateGraph编译和测试

### Phase 2: State Schema和Agent集成 (1-2周)

- [ ] CanvasLearningState完整定义
- [ ] 12个Agent Node改造（返回新State）
- [ ] 强一致性路径实现（Canvas ↔ State）
- [ ] 单元测试覆盖

### Phase 3: 业务记忆系统集成 (2周)

- [ ] Graphiti异步存储实现
- [ ] Temporal Memory集成
- [ ] Semantic Memory集成
- [ ] 最终一致性路径实现
- [ ] 批量写入队列

### Phase 4: 性能优化 (1周)

- [ ] 分层缓存实现
- [ ] 批量操作优化
- [ ] 异步持久化验证
- [ ] 性能基准测试

### Phase 5: 容错和监控 (1周)

- [ ] 冲突检测和修复脚本
- [ ] 回滚机制实现
- [ ] 一致性校验工具
- [ ] 监控和日志系统

### Phase 6: 集成测试和部署 (1周)

- [ ] 端到端集成测试
- [ ] 性能压力测试
- [ ] 生产环境部署
- [ ] 文档完善

**总时间估算**: 7-9周

---

## 🔄 八、艾宾浩斯复习系统3层记忆集成 (v1.1.6新增)

### 8.1 集成背景

**问题描述**:
- 艾宾浩斯复习系统原设计仅依赖Canvas评分（≥60分）作为唯一数据源
- Py-FSRS使用默认17参数（相当于模拟数据，非个性化）
- 缺少主动发现需要复习概念的机制（完全被动等待评分触发）

**解决方案**:
通过整合3层记忆系统（Temporal + Graphiti + Semantic），实现100%真实数据驱动的艾宾浩斯复习系统。

---

### 8.2 3层记忆系统数据提供

#### 8.2.1 Temporal Memory提供的数据

**职责**: 学习行为数据源

**提供数据**:
1. **长期未访问的已掌握概念** (触发点4 - 条件1)
   ```python
   query_temporal_learning_behavior(
       filter_type="inactive_mastered",
       days_threshold=7,
       min_mastery=0.6
   )
   # 返回: [{"concept": "逆否命题", "last_access_days": 10, "mastery": 0.85, ...}]
   ```

2. **历史复习记录** (FSRS参数优化)
   ```python
   query_temporal_learning_behavior(
       filter_type="all_reviews",
       min_samples=100,
       fields=["review_time", "rating", "interval", "stability", "difficulty"]
   )
   # 返回: [{"interval": 7, "rating": 3, "retention": 0.9, ...}, ...]
   ```

3. **最近行为数据** (优先级计算)
   ```python
   query_temporal_learning_behavior(
       filter_type="recent_behavior",
       canvas_file="笔记库/离散数学.canvas",
       concept_ids=["node123", "node456"],
       metrics=["review_frequency", "avg_interval", "accuracy_trend"]
   )
   # 返回: {"review_frequency_normalized": 0.3, "interval_deviation": 0.5, ...}
   ```

**数据schema (Neo4j - Temporal Memory)**:
```cypher
// 学习事件节点
CREATE (e:LearningEvent {
    event_id: randomUUID(),
    session_id: $session_id,
    canvas_file: $canvas_file,
    node_id: $node_id,
    concept: $concept,
    operation_type: $operation_type, // 'scoring', 'review', 'view', 'doc_interaction'
    timestamp: datetime(),
    score: $score,              // 如果operation_type='scoring'
    rating: $rating,            // 如果operation_type='review' (1-4)
    duration: $duration,        // 如果operation_type='view' (秒)
    metadata: $metadata         // JSON对象
})

// 索引
CREATE INDEX learning_event_timestamp IF NOT EXISTS FOR (e:LearningEvent) ON (e.timestamp);
CREATE INDEX learning_event_concept IF NOT EXISTS FOR (e:LearningEvent) ON (e.concept, e.timestamp);
```

---

#### 8.2.2 Graphiti提供的数据

**职责**: 概念关系网络数据源

**提供数据**:
1. **知识断层检测** (触发点4 - 条件2)
   ```python
   query_graphiti_concept_network(
       analysis_type="prerequisite_gap",
       min_prerequisite_mastery=0.8,
       gap_days_threshold=14
   )
   # 返回: [{"concept": "行列式", "prerequisite_mastery": 0.9, "days_not_learned": 20, ...}]
   ```

2. **概念难度分布** (FSRS参数优化)
   ```python
   query_graphiti_concept_network(
       analysis_type="learning_difficulty_distribution",
       concepts=["逆否命题", "德摩根定律", ...]
   )
   # 返回: {"逆否命题": {"difficulty": 0.6}, "德摩根定律": {"difficulty": 0.7}, ...}
   ```

3. **概念关系数据** (优先级计算)
   ```python
   query_graphiti_concept_network(
       analysis_type="related_concepts",
       canvas_file="笔记库/离散数学.canvas",
       concept_ids=["node123", "node456"]
   )
   # 返回: {"prerequisite_completeness": 0.8, "related_difficulty_normalized": 0.5, ...}
   ```

**Cypher查询示例** (Neo4j):
```cypher
// 查询知识断层: 前置概念已掌握但后续概念未学习
MATCH (pre:Concept)-[:PREREQUISITE_OF]->(post:Concept)
WHERE pre.mastery >= 0.8
  AND post.mastery < 0.3
  AND duration.inDays(post.last_learned, datetime()).days > 14
RETURN post.concept, pre.concept AS prerequisite, pre.mastery, post.last_learned
```

---

#### 8.2.3 Semantic Memory提供的数据

**职责**: 文档交互数据源

**提供数据**:
1. **隐性需求检测** (触发点4 - 条件3)
   ```python
   query_semantic_document_interactions(
       pattern="related_doc_frequent_but_concept_inactive",
       related_access_threshold=5,
       concept_inactive_days=7
   )
   # 返回: [{"concept": "特征向量", "related_doc_accesses": 8, "concept_inactive_days": 10, ...}]
   ```

2. **复习参与度相关性** (FSRS参数优化)
   ```python
   query_semantic_document_interactions(
       pattern="review_engagement_correlation",
       concepts=["逆否命题", "德摩根定律", ...]
   )
   # 返回: {"逆否命题": {"engagement": 0.7}, "德摩根定律": {"engagement": 0.5}, ...}
   ```

3. **访问指标** (优先级计算)
   ```python
   query_semantic_document_interactions(
       pattern="access_metrics",
       canvas_file="笔记库/离散数学.canvas",
       concept_ids=["node123", "node456"]
   )
   # 返回: {"recent_access_frequency": 0.3, "dwell_time_normalized": 0.4, ...}
   ```

**数据schema (LanceDB + CUDA Metadata)**:
```python
# LanceDB Document Metadata (Pydantic Schema)
{
    "document_path": "Canvas/Math53/逆否命题-口语化解释-20250115.md",
    "concept": "逆否命题",
    "canvas_file": "Canvas/Math53/离散数学.canvas",
    "node_id": "node123",
    "access_count": 12,
    "last_accessed": "2025-11-10T14:30:00Z",
    "avg_dwell_time": 180,  # 秒
    "related_docs": ["德摩根定律-对比表.md", "命题逻辑-四层次答案.md"]
}
# 768维向量嵌入 (sentence-transformers/all-MiniLM-L6-v2 + CUDA加速)
```

---

### 8.3 艾宾浩斯系统数据流向

```mermaid
graph TB
    subgraph "数据采集层"
        A1[Canvas节点评分] -->|评分≥60| E[EbbinghausReviewSystem]
        A2[用户手动标记] --> E
        A3[批量导入历史] --> E
        A4[行为监控触发] --> E
    end

    subgraph "3层记忆系统查询"
        B1[Temporal Memory<br/>未访问概念查询] --> A4
        B2[Graphiti<br/>知识断层检测] --> A4
        B3[Semantic Memory<br/>隐性需求检测] --> A4
    end

    subgraph "参数优化"
        C1[Temporal<br/>历史复习记录] --> F[optimize_fsrs_parameters]
        C2[Graphiti<br/>概念难度分布] --> F
        C3[Semantic<br/>复习参与度] --> F
        F --> G[优化后的17参数]
        G --> E
    end

    subgraph "优先级计算"
        D1[Temporal<br/>行为数据] --> H[get_today_review_summary]
        D2[Graphiti<br/>概念关系] --> H
        D3[Semantic<br/>文档交互] --> H
        E --> H
        H --> I[优先级排序的Canvas列表]
    end

    style A4 fill:#ffe0b2
    style F fill:#c5e1a5
    style H fill:#b3e5fc
```

**数据流说明**:
1. **触发点1-3**: Canvas评分、手动标记、批量导入 → 直接调用EbbinghausReviewSystem
2. **触发点4**: 每日凌晨2:00定时任务 → 查询3层记忆系统 → 批量添加到EbbinghausReviewSystem
3. **参数优化**: 累积100次复习后 → 从3层记忆提取数据 → 优化FSRS 17参数
4. **优先级计算**: 每日显示复习面板时 → 从3层记忆聚合数据 → 多维度优先级排序

---

### 8.4 LangGraph集成点

#### 8.4.1 行为监控后台任务

**LangGraph实现**: 使用LangGraph的周期性任务节点

```python
from langgraph.graph import StateGraph
from datetime import datetime, time

class EbbinghausMonitoringState(TypedDict):
    last_check_time: datetime
    triggered_concepts: List[Dict]

def behavior_monitoring_node(state: EbbinghausMonitoringState):
    """
    每日凌晨2:00执行的行为监控节点
    """
    # 查询3层记忆系统
    temporal_concepts = query_temporal_learning_behavior(
        filter_type="inactive_mastered",
        days_threshold=7,
        min_mastery=0.6
    )

    graphiti_concepts = query_graphiti_concept_network(
        analysis_type="prerequisite_gap",
        min_prerequisite_mastery=0.8,
        gap_days_threshold=14
    )

    semantic_concepts = query_semantic_document_interactions(
        pattern="related_doc_frequent_but_concept_inactive",
        related_access_threshold=5,
        concept_inactive_days=7
    )

    # 合并并去重
    all_concepts = merge_and_deduplicate(
        temporal_concepts, graphiti_concepts, semantic_concepts
    )

    # 批量添加到艾宾浩斯系统
    review_system = EbbinghausReviewSystem()
    for concept in all_concepts:
        review_system.add_concept_for_review(
            canvas_file=concept['canvas_file'],
            node_id=concept['node_id'],
            concept=concept['concept'],
            initial_mastery=concept.get('mastery', 0.6),
            trigger_source="behavior_monitoring"
        )

    return {
        "last_check_time": datetime.now(),
        "triggered_concepts": all_concepts
    }

# LangGraph StateGraph配置
monitoring_graph = StateGraph(EbbinghausMonitoringState)
monitoring_graph.add_node("behavior_monitoring", behavior_monitoring_node)
monitoring_graph.add_edge(START, "behavior_monitoring")
monitoring_graph.add_edge("behavior_monitoring", END)

# 定时调度 (使用APScheduler)
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(
    func=lambda: monitoring_graph.compile().invoke({"last_check_time": None}),
    trigger="cron",
    hour=2,  # 凌晨2点
    minute=0
)
scheduler.start()
```

#### 8.4.2 评分后行为记录

**集成点**: scoring-agent节点执行后

```python
@tool
def score_and_track(
    canvas_file: str,
    node_id: str,
    concept: str,
    score: int,
    config: RunnableConfig
) -> str:
    """
    评分并记录到Temporal Memory（集成到scoring-agent）
    """
    # Step 1: 更新Canvas节点颜色
    write_to_canvas(canvas_file, {"id": node_id, "color": get_color_by_score(score)}, config)

    # Step 2: 记录行为到Temporal Memory
    track_learning_behavior(
        session_id=config.configurable.get("session_id"),
        canvas_file=canvas_file,
        node_id=node_id,
        concept=concept,
        operation_type="scoring",
        behavior_data={"score": score},
        config=config
    )

    # Step 3: 如果评分≥60，添加到艾宾浩斯系统
    if score >= 60:
        review_system = EbbinghausReviewSystem()
        review_system.add_concept_for_review(
            canvas_file=canvas_file,
            node_id=node_id,
            concept=concept,
            initial_mastery=score / 100.0,
            trigger_source="scoring"
        )

    return f"✅ 评分完成: {score}分, 已记录行为数据"
```

---

### 8.5 一致性保证机制

#### 8.5.1 3层记忆写入失败处理

**问题**: 行为记录写入失败时，艾宾浩斯系统可能缺少数据

**解决方案**: 最终一致性 + 重试队列

```python
class MemoryWriteQueue:
    """3层记忆系统写入队列（最终一致性保证）"""

    def __init__(self):
        self.redis_client = redis.Redis(...)
        self.retry_max = 3

    def enqueue_temporal_write(self, event_data: Dict):
        """
        将Temporal Memory写入任务加入队列
        """
        task = {
            "type": "temporal_write",
            "data": event_data,
            "retry_count": 0,
            "created_at": datetime.now().isoformat()
        }
        self.redis_client.lpush("memory_write_queue", json.dumps(task))

    async def process_queue(self):
        """
        后台worker处理写入队列
        """
        while True:
            task_json = self.redis_client.brpop("memory_write_queue", timeout=5)
            if not task_json:
                continue

            task = json.loads(task_json[1])

            try:
                if task["type"] == "temporal_write":
                    temporal_manager.store_learning_event(task["data"])
                elif task["type"] == "graphiti_write":
                    mcp__graphiti_memory__add_episode(content=task["data"])
                # 写入成功，不重新入队
            except Exception as e:
                # 写入失败，重试
                task["retry_count"] += 1
                if task["retry_count"] < self.retry_max:
                    self.redis_client.lpush("memory_write_queue", json.dumps(task))
                else:
                    # 超过重试次数，记录到错误日志
                    logger.error(f"Memory write failed after {self.retry_max} retries: {task}")
```

#### 8.5.2 艾宾浩斯系统数据修复

**问题**: 如果某些评分事件未成功触发艾宾浩斯系统，导致复习列表不完整

**解决方案**: 定期一致性扫描

```python
def sync_ebbinghaus_from_canvas():
    """
    从Canvas文件扫描所有≥60分节点，确保都在艾宾浩斯系统中
    """
    # Step 1: 扫描所有Canvas文件，找到绿色+紫色节点
    canvas_files = glob.glob("笔记库/**/*.canvas", recursive=True)
    concepts_in_canvas = []

    for canvas_file in canvas_files:
        canvas_data = read_canvas(canvas_file)
        for node in canvas_data.get("nodes", []):
            if node.get("color") in ["2", "3"]:  # 绿色或紫色
                concepts_in_canvas.append({
                    "canvas_file": canvas_file,
                    "node_id": node["id"],
                    "concept": extract_concept_from_node(node)
                })

    # Step 2: 查询艾宾浩斯系统现有概念
    review_system = EbbinghausReviewSystem()
    concepts_in_ebbinghaus = review_system.list_all_concepts()

    # Step 3: 找出缺失的概念
    missing_concepts = [
        c for c in concepts_in_canvas
        if f"{c['canvas_file']}_{c['node_id']}" not in concepts_in_ebbinghaus
    ]

    # Step 4: 批量添加缺失概念
    for concept in missing_concepts:
        review_system.add_concept_for_review(
            canvas_file=concept['canvas_file'],
            node_id=concept['node_id'],
            concept=concept['concept'],
            initial_mastery=0.7,  # 默认掌握度
            trigger_source="consistency_sync"
        )

    logger.info(f"✅ 一致性扫描完成: 修复了{len(missing_concepts)}个缺失概念")

# 定期执行（每周日凌晨3点）
scheduler.add_job(
    func=sync_ebbinghaus_from_canvas,
    trigger="cron",
    day_of_week="sun",
    hour=3,
    minute=0
)
```

---

### 8.6 性能优化

#### 8.6.1 批量查询优化

**问题**: 优先级计算时需要为每个Canvas查询3层记忆系统，可能很慢

**优化方案**: 批量查询 + 缓存

```python
class MemoryBatchQuery:
    """3层记忆系统批量查询优化"""

    def __init__(self):
        self.cache = TTLCache(maxsize=1000, ttl=300)  # 5分钟缓存

    def batch_query_for_review_summary(self, canvas_files: List[str]) -> Dict:
        """
        批量查询多个Canvas的3层记忆数据
        """
        # Step 1: 检查缓存
        cached_results = {}
        uncached_files = []
        for canvas_file in canvas_files:
            cache_key = f"review_summary:{canvas_file}"
            if cache_key in self.cache:
                cached_results[canvas_file] = self.cache[cache_key]
            else:
                uncached_files.append(canvas_file)

        if not uncached_files:
            return cached_results

        # Step 2: 批量查询Temporal Memory（单次查询）
        temporal_data = query_temporal_learning_behavior(
            filter_type="batch_recent_behavior",
            canvas_files=uncached_files,
            metrics=["review_frequency", "avg_interval", "accuracy_trend"]
        )

        # Step 3: 批量查询Graphiti（单次Cypher查询）
        graphiti_data = query_graphiti_concept_network_batch(
            canvas_files=uncached_files,
            analysis=["prerequisite_mastery", "related_difficulty"]
        )

        # Step 4: 批量查询Semantic Memory（单次向量搜索）
        semantic_data = query_semantic_document_interactions_batch(
            canvas_files=uncached_files,
            metrics=["access_frequency", "dwell_time"]
        )

        # Step 5: 合并结果并缓存
        for canvas_file in uncached_files:
            result = {
                "temporal": temporal_data.get(canvas_file, {}),
                "graphiti": graphiti_data.get(canvas_file, {}),
                "semantic": semantic_data.get(canvas_file, {})
            }
            cache_key = f"review_summary:{canvas_file}"
            self.cache[cache_key] = result
            cached_results[canvas_file] = result

        return cached_results
```

#### 8.6.2 异步并发查询

**使用LangGraph的并发节点**:

```python
from langgraph.graph import StateGraph

class MemoryQueryState(TypedDict):
    canvas_files: List[str]
    temporal_results: Dict
    graphiti_results: Dict
    semantic_results: Dict

async def query_temporal_parallel(state: MemoryQueryState):
    """并发查询Temporal Memory"""
    results = await query_temporal_learning_behavior_async(
        filter_type="batch_recent_behavior",
        canvas_files=state["canvas_files"]
    )
    return {"temporal_results": results}

async def query_graphiti_parallel(state: MemoryQueryState):
    """并发查询Graphiti"""
    results = await query_graphiti_concept_network_async_batch(
        canvas_files=state["canvas_files"]
    )
    return {"graphiti_results": results}

async def query_semantic_parallel(state: MemoryQueryState):
    """并发查询Semantic Memory"""
    results = await query_semantic_document_interactions_async_batch(
        canvas_files=state["canvas_files"]
    )
    return {"semantic_results": results}

# 构建并发查询图
memory_query_graph = StateGraph(MemoryQueryState)
memory_query_graph.add_node("temporal", query_temporal_parallel)
memory_query_graph.add_node("graphiti", query_graphiti_parallel)
memory_query_graph.add_node("semantic", query_semantic_parallel)

# 并发执行3个查询
memory_query_graph.add_edge(START, "temporal")
memory_query_graph.add_edge(START, "graphiti")
memory_query_graph.add_edge(START, "semantic")
memory_query_graph.add_edge("temporal", END)
memory_query_graph.add_edge("graphiti", END)
memory_query_graph.add_edge("semantic", END)

# 使用
compiled = memory_query_graph.compile()
result = await compiled.ainvoke({"canvas_files": ["离散数学.canvas", "线性代数.canvas"]})
# result包含所有3层记忆的查询结果
```

---

### 8.7 监控和告警

#### 8.7.1 关键指标监控

```python
# Prometheus指标定义
from prometheus_client import Counter, Histogram, Gauge

# 行为监控触发统计
behavior_monitoring_triggered = Counter(
    'ebbinghaus_behavior_monitoring_triggered_total',
    'Total behavior monitoring triggers',
    ['source']  # temporal/graphiti/semantic
)

# 3层记忆查询延迟
memory_query_latency = Histogram(
    'memory_query_duration_seconds',
    'Memory query latency',
    ['memory_type']  # temporal/graphiti/semantic
)

# FSRS参数优化频率
fsrs_optimization_count = Counter(
    'fsrs_parameter_optimization_total',
    'Total FSRS parameter optimizations'
)

# 当前复习队列大小
review_queue_size = Gauge(
    'ebbinghaus_review_queue_size',
    'Current review queue size'
)
```

#### 8.7.2 告警规则

```yaml
# AlertManager告警规则
groups:
  - name: ebbinghaus_system
    rules:
      - alert: MemoryQuerySlow
        expr: memory_query_duration_seconds{quantile="0.95"} > 1.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "3层记忆系统查询变慢"
          description: "{{ $labels.memory_type }} 查询P95延迟 > 1秒"

      - alert: BehaviorMonitoringFailed
        expr: rate(behavior_monitoring_triggered_total[1h]) == 0
        for: 25h  # 超过1天未触发
        labels:
          severity: critical
        annotations:
          summary: "行为监控未执行"
          description: "过去25小时内未触发行为监控，可能系统故障"

      - alert: ReviewQueueTooLarge
        expr: review_queue_size > 500
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "复习队列过大"
          description: "当前复习队列: {{ $value }} 个概念"
```

---

### 8.8 测试策略

#### 8.8.1 集成测试

```python
@pytest.mark.integration
async def test_ebbinghaus_3layer_memory_integration():
    """
    测试艾宾浩斯系统与3层记忆系统的完整集成
    """
    # Setup: 创建测试数据
    canvas_file = "test_data/测试-离散数学.canvas"
    concept = "测试-逆否命题"

    # Step 1: 模拟评分触发
    await score_and_track(
        canvas_file=canvas_file,
        node_id="test_node_123",
        concept=concept,
        score=85,
        config=test_config
    )

    # Step 2: 验证Temporal Memory已记录
    temporal_events = query_temporal_learning_behavior(
        filter_type="all_reviews",
        min_samples=1
    )
    assert any(e["concept"] == concept for e in temporal_events)

    # Step 3: 验证艾宾浩斯系统已添加
    review_system = EbbinghausReviewSystem()
    concepts = review_system.list_all_concepts()
    assert f"{canvas_file}_test_node_123" in concepts

    # Step 4: 模拟7天后行为监控触发
    await simulate_time_advance(days=7)
    await behavior_monitoring_node({})

    # Step 5: 验证触发了复习推送
    review_summary = get_today_review_summary()
    assert any(c["canvas_file"] == canvas_file for c in review_summary)
```

#### 8.8.2 性能测试

```python
@pytest.mark.performance
async def test_memory_query_performance():
    """
    测试3层记忆系统查询性能
    """
    canvas_files = [f"test_data/canvas_{i}.canvas" for i in range(50)]

    # 测试批量查询性能
    start_time = time.time()
    batch_query = MemoryBatchQuery()
    results = batch_query.batch_query_for_review_summary(canvas_files)
    duration = time.time() - start_time

    # 性能要求: 50个Canvas批量查询 < 2秒
    assert duration < 2.0
    assert len(results) == 50
```

---

## 🔍 十、LangGraph Agentic RAG检索架构

### 10.1 概述

**设计目标**: 实现智能检索3层记忆系统(Graphiti + Temporal + Semantic)来生成高质量个性化检验白板。

**核心挑战**:
1. **多源检索**: 需要从3个异构数据源(Neo4j图数据库 + Neo4j时序数据 + LanceDB向量库)检索数据
2. **检索质量评估**: 需要评估检索结果的质量,决定是否需要重写查询
3. **智能决策**: Agent需要自主决定调用哪些工具、如何组合结果

**解决方案**: LangGraph Agentic RAG模式

---

### 10.2 Agentic RAG架构全景

#### 10.2.1 架构图（含GraphRAG智能路由）

```mermaid
graph TB
    START([开始]) --> ROUTER[question_router]

    ROUTER -->|local: 具体概念查询| A1[generate_query_local]
    ROUTER -->|global: 数据集级分析| A2[generate_query_global]
    ROUTER -->|hybrid: 复杂综合查询| A3[generate_query_hybrid]

    A1 -->|需要检索| B1[local_search_tools]
    A2 -->|需要检索| B2[graphrag_global_tool]
    A3 -->|需要检索| B3[composite_search_tools]

    A1 -->|可直接回答| H[generate]
    A2 -->|可直接回答| H
    A3 -->|可直接回答| H

    B1 --> C[Graphiti Tool]
    B1 --> D[LanceDB Tool]
    B1 --> E[Temporal Tool]

    B2 --> F_global[GraphRAG Global Search]

    B3 --> C_composite[Graphiti Tool]
    B3 --> D_composite[LanceDB Tool]
    B3 --> E_composite[Temporal Tool]
    B3 --> F_composite[GraphRAG Tool]

    C --> F[grade_documents]
    D --> F
    E --> F

    F_global --> F

    C_composite --> F_fusion[fusion_rerank]
    D_composite --> F_fusion
    E_composite --> F_fusion
    F_composite --> F_fusion

    F_fusion --> F

    F -->|文档质量 >= 0.5| H[generate]
    F -->|文档质量 < 0.5| G[rewrite_query]

    G --> ROUTER

    H --> END([结束])

    style ROUTER fill:#ffeb3b
    style A1 fill:#e1f5fe
    style A2 fill:#e1f5fe
    style A3 fill:#e1f5fe
    style B1 fill:#fff3e0
    style B2 fill:#fff3e0
    style B3 fill:#fff3e0
    style F fill:#f3e5f5
    style F_fusion fill:#f3e5f5
    style G fill:#ffcdd2
    style H fill:#c8e6c9
    style F_global fill:#b2dfdb
```

**架构图说明**:

1. **Question Router（黄色）**: 智能问题分类器，根据查询类型路由到不同的检索策略
   - **local**: 具体概念查询（如"什么是逆否命题？"）→ Graphiti + LanceDB + Temporal
   - **global**: 数据集级分析（如"离散数学中哪些概念最容易混淆？"）→ GraphRAG Global Search
   - **hybrid**: 复杂综合查询（如"逻辑推理的核心概念和我的薄弱点是什么？"）→ 四层并行检索

2. **三种检索路径**:
   - **Local Search Path (B1)**: 传统三层检索（Graphiti + LanceDB + Temporal）
   - **Global Search Path (B2)**: 仅GraphRAG全局搜索
   - **Composite Search Path (B3)**: 四层并行检索 + Fusion Reranking

3. **Fusion Reranking（紫色）**: 对并行检索结果进行融合重排序
   - 使用RRF（Reciprocal Rank Fusion）平衡四个数据源
   - 可选Cross-Encoder进一步提升准确性

4. **Self-Correction Loop**: grade_documents评估质量不足时，触发rewrite_query并重新路由
```

#### 10.2.2 核心组件

| 组件 | 类型 | 职责 | 输入 | 输出 |
|------|------|------|------|------|
| **question_router** | Function Node | 智能问题分类：local/global/hybrid | Canvas上下文 + 查询 | 路由决策(query_type) |
| **generate_query_local** | Agent Node | 生成Local Search查询 | Canvas上下文 + 用户理解 | 决策 + 查询语句 |
| **generate_query_global** | Agent Node | 生成Global Search查询 | Canvas上下文 + 分析需求 | 决策 + 全局查询 |
| **generate_query_hybrid** | Agent Node | 生成Hybrid Search查询 | Canvas上下文 + 复杂需求 | 决策 + 混合查询 |
| **local_search_tools** | Tool Node | 执行Graphiti + LanceDB + Temporal | 查询语句 | 3源检索结果 |
| **graphrag_global_tool** | Tool Node | 执行GraphRAG全局搜索 | 全局查询 | 社区摘要 + 全局答案 |
| **composite_search_tools** | Tool Node | 并行执行4层检索 | 混合查询 | 4源检索结果 |
| **fusion_rerank** | Function Node | 融合重排序4源结果 | 4源检索结果 | 融合后文档列表 |
| **grade_documents** | Function Node | 评估文档质量 | 检索结果 | 质量评分(0-1) |
| **rewrite_query** | Function Node | 重写查询 | 低质量文档 + 原查询 | 新查询语句 |
| **generate** | Function Node | 生成检验问题 | 高质量文档 | 检验问题列表 |

**新增组件详解**:

1. **question_router**:
   - 使用LLM分析查询类型（local/global/hybrid）
   - 决策逻辑：
     - 包含"什么是"、"定义"、"具体概念" → local
     - 包含"哪些"、"比较"、"数据集级" → global
     - 包含"核心概念+薄弱点"、"路径+关联" → hybrid

2. **fusion_rerank**:
   - 使用RRF（Reciprocal Rank Fusion）融合Graphiti、LanceDB、Temporal、GraphRAG四个数据源
   - 可选Cross-Encoder进一步提升准确性
   - 去重策略：基于concept字段合并相同概念的多源证据

3. **composite_search_tools**:
   - 使用`asyncio.gather()`并行执行4个工具
   - 超时控制：单个工具最多5秒，总超时10秒
   - 失败降级：至少2个工具成功即可继续

---

### 10.3 State Schema定义

```python
# ✅ Verified from LangGraph Skill (references/llms-txt.md:8723-8825)
from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

class AgenticRAGState(TypedDict):
    """Agentic RAG State Schema（含GraphRAG支持）"""

    # ========== 输入参数 ==========
    canvas_file: str                  # Canvas文件路径
    canvas_context: dict              # Canvas上下文(红/紫节点列表)
    user_understanding: str           # 用户已有理解(黄色节点内容)

    # ========== 对话历史 ==========
    messages: Annotated[list, add_messages]  # LangChain消息累积

    # ========== 路由决策 ==========
    query_type: Literal["local", "global", "hybrid"]  # 查询类型路由
    routing_reasoning: str            # 路由决策理由

    # ========== 检索中间结果 ==========
    current_query: str                # 当前查询语句
    retrieval_attempts: int           # 检索尝试次数
    retrieved_documents: list[dict]   # 检索到的文档列表

    # 文档结构示例（含GraphRAG）:
    # {
    #     "source": "graphrag",  # graphiti/lancedb/temporal/graphrag
    #     "content": "...",
    #     "metadata": {
    #         "concept": "逻辑推理",
    #         "relevance_score": 0.85,
    #         "community_id": "c12",       # GraphRAG专用
    #         "community_level": 2,        # GraphRAG专用
    #         "last_error_date": "2025-11-10"
    #     }
    # }

    # ========== GraphRAG专用字段 ==========
    graphrag_results: dict | None     # GraphRAG全局搜索结果
    # 结构:
    # {
    #     "answer": "综合答案...",
    #     "communities": [{"id": "c1", "title": "逻辑推理", "summary": "...", "weight": 0.8}],
    #     "sources": [{"entity_id": "e1", "entity_name": "逆否命题", "relevance": 0.9}],
    #     "confidence": 0.85
    # }

    # ========== 融合重排序字段 ==========
    fusion_strategy: Literal["rrf", "cross_encoder", "linear"] | None  # 融合策略
    fusion_weights: dict[str, float] | None  # 数据源权重配置
    # 示例: {"graphiti": 0.3, "lancedb": 0.25, "temporal": 0.2, "graphrag": 0.25}

    # ========== 文档质量评估 ==========
    document_quality_score: float     # 0-1分数
    quality_issues: list[str]         # 质量问题列表

    # ========== 最终输出 ==========
    verification_questions: list[dict]  # 生成的检验问题

    # 问题结构示例（含GraphRAG来源）:
    # {
    #     "question": "什么是逆否命题?",
    #     "type": "基础型",  # 突破型/基础型/检验型/应用型
    #     "source_concept": "逆否命题",
    #     "difficulty": "中等",
    #     "data_sources": ["graphiti", "temporal", "graphrag"],  # 可包含graphrag
    #     "community_context": "逻辑推理社区"  # GraphRAG提供的社区背景
    # }

    # ========== 执行状态 ==========
    workflow_stage: Literal[
        "routing",
        "query_generation",
        "tool_execution",
        "fusion_reranking",
        "document_grading",
        "query_rewriting",
        "question_generation",
        "completed"
    ]
    error_log: list[dict]             # 错误日志
```

---

### 10.4 Retrieval Tools定义

#### 10.4.1 Graphiti Hybrid Search Tool

```python
# ✅ Verified from Graphiti Skill
from langchain.tools import tool
from typing import List, Dict

@tool
async def graphiti_hybrid_search_tool(
    query: str,
    canvas_context: dict,
    max_results: int = 20,
    rerank_strategy: str = "rrf"
) -> List[Dict]:
    """
    Graphiti混合检索工具 (Graph + Semantic + BM25)

    Args:
        query: 查询语句
        canvas_context: Canvas上下文(包含topic_node_id)
        max_results: 最大结果数
        rerank_strategy: 重排序策略(rrf/mmr/node_distance/cross_encoder/episode_mentions)

    Returns:
        检索结果列表

    使用场景:
        - 检验白板生成: 查询历史薄弱点和相关概念
        - 艾宾浩斯复习: 查询需要复习的概念
    """
    from app.core.graphiti_client import graphiti

    # Step 1: Graphiti混合检索
    results = await graphiti.search(
        query=query,
        center_node_uuid=canvas_context.get("topic_node_id"),
        max_distance=2,              # 图遍历最大跳数
        num_results=max_results,
        rerank_strategy=rerank_strategy
    )

    # Step 2: 格式化结果
    formatted_results = []
    for result in results:
        formatted_results.append({
            "source": "graphiti",
            "content": result.get("text", ""),
            "metadata": {
                "concept": result.get("concept", ""),
                "node_id": result.get("uuid", ""),
                "relevance_score": result.get("score", 0.0),
                "graph_distance": result.get("distance", 0),
                "last_access": result.get("last_access", None),
                "mastery_level": result.get("mastery", 0.0)
            }
        })

    return formatted_results
```

**Reranking策略选择指南**:

| 策略 | 适用场景 | 优势 | 劣势 |
|------|---------|------|------|
| **rrf** (Reciprocal Rank Fusion) | 检验白板生成(推荐) | 平衡语义/关键词/图关系 | 无特殊偏好 |
| **mmr** (Maximal Marginal Relevance) | 需要多样性的问题生成 | 避免重复概念 | 可能遗漏高相关内容 |
| **node_distance** | 强调概念关联性 | 优先返回图中相近节点 | 忽略语义相似度 |
| **cross_encoder** | 最高准确性要求 | BERT交叉编码器,最准确 | 最慢(~500ms) |
| **episode_mentions** | 艾宾浩斯复习推荐 | 优先高频错误概念 | 忽略新概念 |

---

#### 10.4.2 LanceDB Hybrid Search Tool

```python
# ✅ Verified from LanceDB Context7 (lancedb.search() + rerank pattern)
@tool
async def lancedb_hybrid_search_tool(
    query: str,
    n_results: int = 10,
    filter_metadata: dict = None,
    rerank_strategy: str = "rrf"
) -> List[Dict]:
    """
    LanceDB混合检索工具 (Vector + BM25 Full-Text Search)

    Args:
        query: 查询语句
        n_results: 返回结果数
        filter_metadata: 元数据过滤(如document_type, canvas_file)
        rerank_strategy: 重排序策略
            - "rrf": Reciprocal Rank Fusion (默认,平衡向量和关键词)
            - "linear": LinearCombinationReranker (可调权重)
            - "cross_encoder": CrossEncoderReranker (最高准确性,最慢)
            - "cohere": CohereReranker (需要API key)

    Returns:
        相似文档列表

    使用场景:
        - 检索历史解释文档(oral-explanation, clarification-path等)
        - 查找相似概念的学习材料
        - 结合语义相似度和关键词匹配的综合检索

    性能特点:
        - Vector search: 语义理解,捕捉概念相似性
        - BM25 FTS: 关键词精确匹配,term frequency优化
        - Hybrid: 100x查询性能提升 vs Parquet-based DBs
        - 查询延迟: <100ms (1M vectors, p95)
    """
    from app.core.lancedb_client import lancedb_table
    from lancedb.rerankers import RRFReranker, LinearCombinationReranker, CrossEncoderReranker

    # Step 1: 选择Reranker
    rerankers = {
        "rrf": RRFReranker(),
        "linear": LinearCombinationReranker(weight=0.7),  # 0.7权重给向量检索
        "cross_encoder": CrossEncoderReranker(),
        # Cohere reranker需要API key,按需启用
        # "cohere": CohereReranker(api_key=os.getenv("COHERE_API_KEY"))
    }
    reranker = rerankers.get(rerank_strategy, RRFReranker())

    # Step 2: LanceDB混合检索 (Vector + BM25)
    # ✅ Verified from LanceDB Context7: hybrid search pattern
    search_builder = lancedb_table.search(query, query_type="hybrid")

    # 添加元数据过滤
    if filter_metadata:
        search_builder = search_builder.where(filter_metadata)

    # 执行检索并重排序
    results = (
        search_builder
        .rerank(reranker=reranker)
        .limit(n_results)
        .to_list()
    )

    # Step 3: 格式化结果
    formatted_results = []
    for result in results:
        formatted_results.append({
            "source": "lancedb",
            "content": result.get("text", ""),
            "metadata": {
                "doc_path": result.get("doc_path", ""),
                "concept": result.get("concept", ""),
                "agent_type": result.get("agent_type", ""),
                "vector_score": result.get("_vector_score", 0.0),
                "fts_score": result.get("_fts_score", 0.0),
                "relevance_score": result.get("_relevance_score", 0.0),  # 重排序后综合分数
                "created_at": result.get("created_at", None)
            }
        })

    return formatted_results
```

**LanceDB Hybrid Search优势**:

| 特性 | LanceDB Hybrid | 传统ChromaDB | 提升 |
|------|----------------|-------------|------|
| **查询性能** | <100ms (1M vectors) | ~150-200ms | **2x faster** |
| **检索方式** | Vector + BM25 + Rerank | 纯向量检索 | **更全面** |
| **可扩展性** | 1B+ vectors | <500K optimal | **2000x scalability** |
| **关键词匹配** | BM25全文索引(精确) | 无(需语义近似) | **新增能力** |
| **重排序策略** | 5种(RRF/Linear/CrossEncoder等) | 无 | **更智能** |

**Reranker选择指南**:

| Reranker | 适用场景 | 性能 | 准确性 |
|----------|---------|------|--------|
| **RRF** | 检验白板生成(推荐) | ⭐⭐⭐⭐⭐ (<50ms) | ⭐⭐⭐⭐ |
| **LinearCombination** | 需要调整向量/关键词权重 | ⭐⭐⭐⭐⭐ (<50ms) | ⭐⭐⭐⭐ |
| **CrossEncoder** | 最高准确性要求 | ⭐⭐ (<500ms) | ⭐⭐⭐⭐⭐ |
| **Cohere** | 多语言,高质量商业应用 | ⭐⭐⭐ (API调用) | ⭐⭐⭐⭐⭐ |

**使用示例**:

```python
# 示例1: 检索"逆否命题"相关的解释文档
results = await lancedb_hybrid_search_tool(
    query="逆否命题解释",
    n_results=10,
    filter_metadata={"document_type": "explanation"},
    rerank_strategy="rrf"
)

# 示例2: 查找特定Canvas的学习材料(使用CrossEncoder获得最高准确性)
results = await lancedb_hybrid_search_tool(
    query="离散数学 逻辑推理",
    n_results=20,
    filter_metadata={"canvas_file": "离散数学.canvas"},
    rerank_strategy="cross_encoder"
)
```

---

#### 10.4.3 Temporal Behavior Query Tool

```python
@tool
async def temporal_behavior_query_tool(
    canvas_file: str,
    query_type: str = "weak_points",
    time_range_days: int = 30
) -> List[Dict]:
    """
    Temporal Memory行为查询工具

    Args:
        canvas_file: Canvas文件路径
        query_type: 查询类型
            - "weak_points": 历史薄弱点
            - "inactive_mastered": 长期未访问的已掌握概念
            - "recent_errors": 最近错误记录
        time_range_days: 时间范围(天数)

    Returns:
        行为数据列表

    使用场景:
        - 检验白板生成: 查询历史薄弱点(70%权重)
        - 艾宾浩斯复习: 查询需要复习的概念
    """
    from app.core.temporal_memory import temporal_memory_client
    from datetime import datetime, timedelta

    cutoff_date = datetime.now() - timedelta(days=time_range_days)

    if query_type == "weak_points":
        # 查询历史评分<80的概念
        cypher_query = f"""
        MATCH (c:Canvas {{path: "{canvas_file}"}})
        -[:CONTAINS]->(n:Node)
        -[:HAS_UNDERSTANDING_STATE]->(s:UnderstandingState)
        WHERE s.total_score < 80
          AND s.timestamp >= datetime('{cutoff_date.isoformat()}')
        RETURN n.id AS node_id,
               n.text AS concept,
               s.total_score AS score,
               s.timestamp AS error_date,
               s.accuracy AS accuracy,
               s.imagery AS imagery,
               s.completeness AS completeness,
               s.originality AS originality
        ORDER BY s.timestamp DESC, s.total_score ASC
        LIMIT 50
        """
    elif query_type == "inactive_mastered":
        # 查询>7天未访问但评分≥80的概念
        cypher_query = f"""
        MATCH (c:Canvas {{path: "{canvas_file}"}})
        -[:CONTAINS]->(n:Node)
        -[:HAS_UNDERSTANDING_STATE]->(s:UnderstandingState)
        WHERE s.total_score >= 80
          AND s.timestamp < datetime('{(datetime.now() - timedelta(days=7)).isoformat()}')
        RETURN n.id AS node_id,
               n.text AS concept,
               s.total_score AS score,
               s.timestamp AS last_access,
               duration.inDays(s.timestamp, datetime()).days AS days_inactive
        ORDER BY days_inactive DESC
        LIMIT 30
        """
    else:  # recent_errors
        cypher_query = f"""
        MATCH (c:Canvas {{path: "{canvas_file}"}})
        -[:CONTAINS]->(n:Node)
        -[r:HAS_UNDERSTANDING_STATE]->(s:UnderstandingState)
        WHERE s.color = '1'  // 红色节点
          AND s.timestamp >= datetime('{cutoff_date.isoformat()}')
        RETURN n.id AS node_id,
               n.text AS concept,
               s.timestamp AS error_date,
               count(r) AS error_count
        ORDER BY error_count DESC, s.timestamp DESC
        LIMIT 20
        """

    # 执行查询
    results = await temporal_memory_client.execute_cypher(cypher_query)

    # 格式化结果
    formatted_results = []
    for record in results:
        formatted_results.append({
            "source": "temporal",
            "content": record.get("concept", ""),
            "metadata": {
                "node_id": record.get("node_id", ""),
                "concept": record.get("concept", ""),
                "score": record.get("score", 0),
                "error_date": record.get("error_date", None),
                "days_inactive": record.get("days_inactive", 0),
                "error_count": record.get("error_count", 0),
                "accuracy": record.get("accuracy", 0),
                "imagery": record.get("imagery", 0),
                "completeness": record.get("completeness", 0),
                "originality": record.get("originality", 0)
            }
        })

    return formatted_results
```

---

#### 10.4.4 GraphRAG Global Search Tool

```python
# ✅ Verified from GraphRAG Integration Design (GRAPHRAG-INTEGRATION-DESIGN.md)
@tool
async def graphrag_global_search_tool(
    query: str,
    community_level: int = 2,
    max_data_tokens: int = 12000,
    temperature: float = 0.2
) -> Dict:
    """
    GraphRAG全局搜索工具 (Community-based Global Reasoning)

    Args:
        query: 自然语言查询（数据集级别的分析性问题）
        community_level: 社区层级 (0-3)
            - Level 0: 最细粒度（单个概念）
            - Level 1: 概念组（推荐，如"逻辑推理"）
            - Level 2: 主题域（如"离散数学基础"）
            - Level 3: 数据集全局（跨Canvas分析）
        max_data_tokens: 最大上下文token数（默认12000）
        temperature: LLM温度（0.0-1.0，默认0.2）

    Returns:
        全局搜索结果，包含：
        - answer: LLM生成的综合答案
        - communities: 相关社区列表（含摘要和权重）
        - sources: 证据来源（实体和关系）
        - confidence: 答案置信度（0.0-1.0）

    使用场景:
        1. **数据集级分析**: "离散数学中哪些概念最容易混淆？"
        2. **跨主题比较**: "逻辑推理和集合论在学习路径上的依赖关系是什么？"
        3. **全局模式识别**: "我在哪些类型的问题上最容易出错？"
        4. **学习路径规划**: "从线性代数到机器学习的最优学习路径是什么？"

    技术特点:
        - **社区检测**: Leiden算法层级聚类，自动识别概念主题
        - **层级推理**: 支持4层社区层级，从细粒度到全局
        - **LLM驱动**: GPT-4o综合多个社区摘要，生成全局答案
        - **证据追溯**: 每个答案包含来源社区和实体证据

    性能特点:
        - 查询延迟: 2-5秒（Level 1-2），5-10秒（Level 3）
        - Token消耗: 8K-15K tokens/query（含社区摘要上下文）
        - 适用规模: 100-10K概念的数据集

    与Local Search对比:
        | 维度 | GraphRAG Global Search | Graphiti/LanceDB Local Search |
        |------|----------------------|-------------------------------|
        | 查询类型 | 分析性、比较性、全局性 | 查找性、定义性、局部性 |
        | 上下文范围 | 整个数据集或主题域 | 单个概念或其邻居 |
        | 答案生成 | LLM综合多社区摘要 | 直接返回检索文档 |
        | 延迟 | 2-10秒 | <200ms |
        | 适用规模 | 100-10K概念 | 无限制 |
    """
    from graphrag.query.structured_search.global_search import GlobalSearch
    from graphrag.query.context_builder.community_context import CommunityContextBuilder
    from app.core.graphrag_client import (
        load_entities,
        load_communities,
        load_community_reports
    )

    # Step 1: 加载GraphRAG数据（社区结构）
    entities = await load_entities()
    communities = await load_communities(level=community_level)
    community_reports = await load_community_reports(level=community_level)

    # Step 2: 构建社区上下文
    context_builder = CommunityContextBuilder(
        entities=entities,
        communities=communities,
        community_reports=community_reports
    )

    # Step 3: 初始化GlobalSearch
    searcher = GlobalSearch(
        llm=ChatOpenAI(model="gpt-4o", temperature=temperature),
        context_builder=context_builder,
        max_data_tokens=max_data_tokens
    )

    # Step 4: 执行全局搜索
    result = await searcher.asearch(query=query)

    # Step 5: 计算答案置信度
    confidence = calculate_confidence(
        result=result,
        num_communities=len(communities),
        num_sources=len(result.context_data.get("sources", []))
    )

    # Step 6: 格式化返回结果
    return {
        "source": "graphrag",
        "answer": result.response,
        "communities": [
            {
                "id": c.id,
                "title": c.title,
                "summary": c.summary,
                "weight": c.weight,
                "level": community_level
            }
            for c in result.context_data.get("communities", [])
        ],
        "sources": [
            {
                "entity_id": s.get("id"),
                "entity_name": s.get("name"),
                "entity_type": s.get("type"),
                "relevance": s.get("rank", 0.0)
            }
            for s in result.context_data.get("sources", [])
        ],
        "confidence": confidence,
        "metadata": {
            "query": query,
            "community_level": community_level,
            "num_communities": len(communities),
            "num_sources": len(result.context_data.get("sources", [])),
            "tokens_used": result.context_data.get("num_tokens", 0)
        }
    }


def calculate_confidence(result, num_communities: int, num_sources: int) -> float:
    """
    计算GraphRAG全局搜索的答案置信度

    置信度基于：
    1. 社区覆盖度（查询命中多少社区）
    2. 证据来源数量（引用多少实体）
    3. LLM响应长度（答案是否详细）

    Returns:
        0.0-1.0之间的置信度分数
    """
    # 因子1: 社区覆盖度 (0.0-0.4)
    community_coverage = min(0.4, num_communities * 0.05)

    # 因子2: 证据来源充分性 (0.0-0.4)
    source_sufficiency = min(0.4, num_sources * 0.04)

    # 因子3: 答案详细程度 (0.0-0.2)
    response_length = len(result.response.split())
    detail_score = min(0.2, response_length / 500 * 0.2)

    return community_coverage + source_sufficiency + detail_score
```

**GraphRAG使用场景指南**:

| 查询类型 | 示例问题 | 推荐Level | 预期延迟 |
|---------|---------|----------|---------|
| **主题内分析** | "逻辑推理中哪些概念最容易混淆？" | Level 1 | 2-3秒 |
| **主题间比较** | "线性代数和概率论的关联是什么？" | Level 2 | 3-5秒 |
| **数据集全局** | "我的薄弱环节主要集中在哪些领域？" | Level 3 | 5-10秒 |
| **学习路径规划** | "从微积分到机器学习的最优路径？" | Level 2 | 3-5秒 |

**与Graphiti/LanceDB协同策略**:

```python
# 场景1: 混合检索（先Global后Local）
# 用户问题: "离散数学中逻辑推理的核心概念是什么？"

# Step 1: GraphRAG识别核心主题
global_result = await graphrag_global_search_tool(
    query="离散数学逻辑推理的核心概念",
    community_level=1
)
# 返回: "逻辑推理"社区，包含5个核心概念

# Step 2: LanceDB检索每个核心概念的详细解释
for concept in global_result["sources"]:
    details = await lancedb_hybrid_search_tool(
        query=concept["entity_name"],
        filter_metadata={"document_type": "explanation"}
    )
    concept["detailed_explanation"] = details

# Step 3: Graphiti查询概念间的关系
for concept in global_result["sources"]:
    relations = await graphiti_hybrid_search_tool(
        query=f"{concept['entity_name']} 相关概念",
        canvas_context={"topic_node_id": concept["entity_id"]}
    )
    concept["related_concepts"] = relations
```

**使用示例**:

```python
# 示例1: 全局薄弱点分析（检验白板生成场景）
result = await graphrag_global_search_tool(
    query="在离散数学Canvas中，我最薄弱的概念集群是什么？它们之间有什么共性？",
    community_level=2
)
# 返回:
# {
#   "answer": "您的薄弱概念主要集中在'逻辑推理'和'集合论'两个主题...",
#   "communities": [
#     {"title": "逻辑推理", "summary": "包含命题逻辑、逆否命题等6个概念", "weight": 0.8},
#     {"title": "集合论", "summary": "包含集合运算、幂集等4个概念", "weight": 0.6}
#   ],
#   "confidence": 0.85
# }

# 示例2: 学习路径规划
result = await graphrag_global_search_tool(
    query="从线性代数到机器学习，我应该按什么顺序学习？哪些概念是必须先掌握的？",
    community_level=2
)

# 示例3: 跨Canvas比较分析
result = await graphrag_global_search_tool(
    query="比较我在'离散数学'和'线性代数'两个Canvas中的学习模式，有什么共同的薄弱点？",
    community_level=3
)
```

---

#### 10.4.5 本地模型配置（成本优化）

**背景**: 基于ADR-001决策，GraphRAG默认使用**Qwen2.5-14B-Instruct本地模型**作为主要LLM提供商，通过90% Qwen2.5 + 10% API的混合策略，将月度成本从$570降低到$57（节省90%）。

**核心配置**:

```python
# ✅ Verified from ADR-001 & Story GraphRAG.2 (本地模型集成)
from langchain_community.llms import Ollama
from langchain_openai import ChatOpenAI
import random
from typing import Dict, Any

class HybridLLMProvider:
    """
    混合LLM提供商（本地模型优先策略）

    策略:
        - 90%请求使用Qwen2.5-14B（本地Ollama，成本$0）
        - 10%请求使用gpt-4o-mini（API降级，成本$0.02）
        - 本地超时/失败时自动降级到API

    成本优化:
        - 原设计: 100% gpt-4o，月成本$570
        - 优化后: 90% Qwen2.5 + 10% gpt-4o-mini，月成本$57
        - **节省90%** ($513/月)

    质量保证:
        - Qwen2.5质量: ~85%（与gpt-4o基线对比）
        - gpt-4o-mini质量: ~90%
        - 混合策略综合质量: ~86%
        - 质量下降: 14%（可接受范围，换取90%成本节省）
    """

    def __init__(
        self,
        local_ratio: float = 0.9,
        local_timeout: int = 8,
        api_timeout: int = 5
    ):
        # 本地模型（Qwen2.5-14B via Ollama）
        self.local_llm = Ollama(
            model="qwen2.5:14b-instruct",
            base_url="http://localhost:11434",
            temperature=0.2,
            timeout=local_timeout
        )

        # API降级模型（gpt-4o-mini）
        self.api_llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.2,
            timeout=api_timeout
        )

        self.local_ratio = local_ratio
        self.cost_tracker = CostTracker()

    async def ainvoke(self, prompt: str) -> str:
        """
        混合策略调用（异步）

        决策流程:
            1. 随机数决定路由（90%本地 vs 10%API）
            2. 如果选择本地，先尝试本地模型
            3. 本地超时/失败 → 自动降级到API
            4. 记录成本和降级事件
        """
        use_local = random.random() < self.local_ratio

        if use_local:
            try:
                # 尝试本地模型
                response = await self.local_llm.ainvoke(prompt)
                self.cost_tracker.record_local_call(model="qwen2.5:14b", cost=0.0)
                return response
            except TimeoutError:
                # 超时 → 降级到API
                self.cost_tracker.record_degradation(reason="local_timeout")
                return await self._invoke_api(prompt)
            except Exception as e:
                # 失败 → 降级到API
                self.cost_tracker.record_degradation(reason="local_failure", error=str(e))
                return await self._invoke_api(prompt)
        else:
            # 直接使用API（10%流量，用于质量对比）
            return await self._invoke_api(prompt)

    async def _invoke_api(self, prompt: str) -> str:
        """API调用（gpt-4o-mini）"""
        response = await self.api_llm.ainvoke(prompt)

        # 估算token消耗和成本
        input_tokens = len(prompt) // 4  # 粗略估算
        output_tokens = len(response.content) // 4
        cost = self.cost_tracker.record_api_call(
            provider="openai",
            model="gpt-4o-mini",
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )

        return response.content


# 集成到GraphRAG Global Search
async def graphrag_global_search_with_local_model(
    query: str,
    community_level: int = 2,
    max_data_tokens: int = 12000
) -> Dict:
    """
    使用本地模型的GraphRAG全局搜索（成本优化版本）

    变更:
        - LLM: gpt-4o → HybridLLMProvider（90% Qwen2.5 + 10% gpt-4o-mini）
        - 月成本: $570 → $57（节省90%）
        - 质量: 100% → 86%（下降14%）
    """
    from graphrag.query.structured_search.global_search import GlobalSearch
    from graphrag.query.context_builder.community_context import CommunityContextBuilder

    # 使用混合LLM提供商（本地优先）
    hybrid_llm = HybridLLMProvider(
        local_ratio=0.9,
        local_timeout=8,
        api_timeout=5
    )

    # 加载社区数据
    context_builder = CommunityContextBuilder(...)

    # 初始化GlobalSearch（使用混合LLM）
    searcher = GlobalSearch(
        llm=hybrid_llm,  # 替换原来的ChatOpenAI(model="gpt-4o")
        context_builder=context_builder,
        max_data_tokens=max_data_tokens
    )

    # 执行搜索
    result = await searcher.asearch(query=query)

    return {
        "answer": result.response,
        "cost_info": {
            "monthly_cost_estimate": hybrid_llm.cost_tracker.get_monthly_cost(),
            "degradation_rate": hybrid_llm.cost_tracker.get_degradation_rate(),
            "local_success_rate": hybrid_llm.cost_tracker.get_local_success_rate()
        }
    }
```

**成本对比**:

| LLM配置 | 成本/查询 | 月成本（3000查询） | 质量 | 延迟（P95） |
|---------|----------|------------------|------|------------|
| **原设计**: gpt-4o（100%） | $0.19 | $570 | 100% | 4.5秒 |
| **方案A**: gpt-4o-mini（100%） | $0.02 | $60 | 90% | 2.8秒 |
| **方案B**: Qwen2.5（100%） | $0.00 | $0 | 85% | 5.2秒 |
| **最终方案**: Qwen2.5（90%）+ gpt-4o-mini（10%） | $0.02 | **$57** | 86% | 5.0秒 |

**性能优化**:
- **本地模型**: RTX 4090 GPU推理，~5秒/查询（14B参数）
- **API降级**: 仅在本地超时（>8秒）或失败时触发
- **降级率目标**: <5%（本地成功率≥95%）

**成本监控**:
```python
# ✅ Verified from Story GraphRAG.5 (成本监控)
# 月度成本告警阈值
COST_ALERT_THRESHOLDS = {
    "warning": 60.0,    # $60 (75%预算)，发送警告邮件
    "critical": 80.0    # $80 (100%预算)，自动切换为100%本地模式
}

# 实时成本追踪
monthly_cost = hybrid_llm.cost_tracker.get_monthly_cost()
if monthly_cost >= COST_ALERT_THRESHOLDS["critical"]:
    # 紧急降级：切换为100%本地模式
    hybrid_llm.local_ratio = 1.0
    send_alert(f"成本超标，已切换为100%本地模式（月成本: ${monthly_cost}）")
elif monthly_cost >= COST_ALERT_THRESHOLDS["warning"]:
    # 警告：发送邮件提醒
    send_alert(f"成本预警，当前月成本: ${monthly_cost}（目标<$80）")
```

**质量验证**:
- **测试数据集**: 100个Canvas查询样本
- **评估指标**: F1 Score（实体提取准确性）
- **基线对比**: gpt-4o质量作为100%基线
- **验收标准**: Qwen2.5质量≥85%（Story GraphRAG.2 AC 5）

**部署要求**:
- **硬件**: RTX 4090 24GB VRAM（推荐）或A100
- **软件**: Ollama + Qwen2.5-14B-Instruct模型
- **网络**: 无需外网（本地推理），API作为降级方案需要外网
- **成本**: 一次性硬件投资$1600（RTX 4090），2.8个月即可回本

---

### 10.5 Agentic RAG Graph实现

#### 10.5.1 完整Graph定义（含GraphRAG智能路由）

```python
# ✅ Verified from LangGraph Skill (references/llms-txt.md:8723-8825)
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

# Step 1: 定义tools列表（扩展为4个工具）
tools = [
    graphiti_hybrid_search_tool,
    lancedb_hybrid_search_tool,
    temporal_behavior_query_tool,
    graphrag_global_search_tool  # 新增
]

# Step 2: 创建StateGraph
builder = StateGraph(AgenticRAGState)

# Step 3: 添加节点
# 3.1 路由和查询生成节点
builder.add_node("question_router", question_router_node)  # 新增：智能路由
builder.add_node("generate_query_local", generate_query_or_respond_node)  # 重命名
builder.add_node("generate_query_global", generate_query_or_respond_node)  # 全局查询生成
builder.add_node("generate_query_hybrid", generate_query_or_respond_node)  # 混合查询生成

# 3.2 检索节点
builder.add_node("local_search_tools", ToolNode([
    graphiti_hybrid_search_tool,
    lancedb_hybrid_search_tool,
    temporal_behavior_query_tool
]))  # Local检索：3个工具
builder.add_node("graphrag_global_search", graphrag_global_search_node)  # 新增：全局搜索
builder.add_node("composite_search", composite_search_node)  # 新增：组合搜索

# 3.3 融合和评分节点
builder.add_node("fusion_rerank", fusion_rerank_node)  # 新增：融合重排序
builder.add_node("grade_documents", grade_documents_node)  # 文档质量评分

# 3.4 自我修正和生成节点
builder.add_node("rewrite", rewrite_query_node)  # 查询重写
builder.add_node("generate", generate_questions_node)  # 生成检验问题

# Step 4: 添加边和条件路由
# 4.1 入口：从START进入question_router
builder.add_edge(START, "question_router")

# 4.2 从question_router路由到不同的查询生成节点
builder.add_conditional_edges(
    "question_router",
    route_by_query_type,  # 条件函数：基于query_type路由
    {
        "local": "generate_query_local",
        "global": "generate_query_global",
        "hybrid": "generate_query_hybrid"
    }
)

# 4.3 从查询生成节点到检索节点或直接生成
# Local路径
builder.add_conditional_edges(
    "generate_query_local",
    route_query,  # 条件函数：是否需要检索
    {
        "retrieve": "local_search_tools",
        "generate": "generate"
    }
)

# Global路径
builder.add_conditional_edges(
    "generate_query_global",
    route_query,
    {
        "retrieve": "graphrag_global_search",
        "generate": "generate"
    }
)

# Hybrid路径
builder.add_conditional_edges(
    "generate_query_hybrid",
    route_query,
    {
        "retrieve": "composite_search",
        "generate": "generate"
    }
)

# 4.4 检索后处理
# Local和Global检索直接进入grade_documents
builder.add_edge("local_search_tools", "grade_documents")
builder.add_edge("graphrag_global_search", "grade_documents")

# Composite检索需要先经过fusion_rerank
builder.add_edge("composite_search", "fusion_rerank")
builder.add_edge("fusion_rerank", "grade_documents")

# 4.5 基于文档质量决定下一步
builder.add_conditional_edges(
    "grade_documents",
    grade_documents_route,  # 条件函数：质量评分
    {
        "rewrite": "rewrite",
        "generate": "generate"
    }
)

# 4.6 查询重写后重新路由
builder.add_edge("rewrite", "question_router")  # 重新进入路由逻辑

# 4.7 生成完成后结束
builder.add_edge("generate", END)

# Step 5: 编译graph
agentic_rag_graph = builder.compile()
```

**新架构的关键改进**:

1. **智能路由入口**: 所有查询先经过question_router分类
2. **三种检索路径**: Local（3工具）、Global（GraphRAG）、Hybrid（4工具并行）
3. **Fusion Reranking**: Hybrid路径专享，融合4个数据源
4. **Self-Correction Loop**: 重写后重新路由，而非回到固定节点
5. **灵活扩展**: 可根据query_type轻松添加新的检索策略

**路由决策示例**:

```python
# 示例1：Local路由
query = "什么是逆否命题？"
# question_router → local → generate_query_local → local_search_tools → grade_documents → generate

# 示例2：Global路由
query = "离散数学中哪些概念最容易混淆？"
# question_router → global → generate_query_global → graphrag_global_search → grade_documents → generate

# 示例3：Hybrid路由
query = "逻辑推理的核心概念是什么，我在哪些方面最薄弱？"
# question_router → hybrid → generate_query_hybrid → composite_search → fusion_rerank → grade_documents → generate

# 示例4：Self-Correction Loop
query = "离散数学"  # 模糊查询
# question_router → local → generate_query_local → local_search_tools → grade_documents (质量低)
# → rewrite → question_router → local → ... (重试)
```
```

---

#### 10.5.2 节点实现（含GraphRAG新节点）

**Node 0: question_router** (新增)

```python
# ✅ Verified from GRAPHRAG-INTEGRATION-DESIGN.md (Question Router Pattern)
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import json

async def question_router_node(state: AgenticRAGState) -> AgenticRAGState:
    """
    智能问题路由节点：分类查询类型（local/global/hybrid）

    路由决策逻辑：
    - local: 具体概念查询、定义查找 → Graphiti + LanceDB + Temporal
    - global: 数据集级分析、跨主题比较 → GraphRAG Global Search
    - hybrid: 复杂综合查询（如"核心概念+薄弱点"） → 四层并行检索
    """

    router_prompt = ChatPromptTemplate.from_messages([
        ("system", """你是Canvas学习系统的查询路由器。
        分析用户的查询，确定最佳检索策略。

        **路由规则**：

        1. **local** - 具体概念查询（局部检索）
           - 触发词：什么是、定义、解释、如何理解
           - 示例："什么是逆否命题？"、"解释集合论的基本概念"
           - 策略：Graphiti图遍历 + LanceDB语义检索 + Temporal历史数据

        2. **global** - 数据集级分析（全局推理）
           - 触发词：哪些、比较、整体、数据集级、跨主题
           - 示例："离散数学中哪些概念最容易混淆？"、"我的薄弱环节集中在哪些领域？"
           - 策略：GraphRAG社区检测 + 全局摘要 + LLM综合分析

        3. **hybrid** - 复杂综合查询（混合检索）
           - 触发词：包含多个维度（如"核心概念+薄弱点"、"路径+关联"）
           - 示例："逻辑推理的核心概念是什么，我在哪些方面最薄弱？"
           - 策略：Graphiti + LanceDB + Temporal + GraphRAG四层并行

        返回JSON格式：
        {
            "query_type": "local|global|hybrid",
            "reasoning": "路由决策理由（50字以内）"
        }"""),
        ("user", """Canvas文件：{canvas_file}

查询内容：{query}

Canvas上下文（红/紫节点数量）：
- 红色节点（完全不理解）：{red_count}个
- 紫色节点（似懂非懂）：{purple_count}个

请分析查询类型并路由。""")
    ])

    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    chain = router_prompt | llm

    # 准备输入数据
    red_count = len([n for n in state["canvas_context"].get("nodes", []) if n.get("color") == "1"])
    purple_count = len([n for n in state["canvas_context"].get("nodes", []) if n.get("color") == "3"])

    result = await chain.ainvoke({
        "canvas_file": state["canvas_file"],
        "query": state.get("current_query", ""),
        "red_count": red_count,
        "purple_count": purple_count
    })

    # 解析LLM响应
    try:
        classification = json.loads(result.content)
    except json.JSONDecodeError:
        # 降级策略：默认使用local
        classification = {
            "query_type": "local",
            "reasoning": "JSON解析失败，降级为local检索"
        }

    return {
        **state,
        "query_type": classification["query_type"],
        "routing_reasoning": classification["reasoning"],
        "workflow_stage": "routing",
        "messages": state["messages"] + [{"role": "system", "content": f"路由决策：{classification['query_type']} | 理由：{classification['reasoning']}"}]
    }
```

**Node 1A: graphrag_global_search_node** (新增)

```python
# ✅ Verified from GRAPHRAG-INTEGRATION-DESIGN.md
async def graphrag_global_search_node(state: AgenticRAGState) -> AgenticRAGState:
    """
    GraphRAG全局搜索节点：执行社区级别的全局推理

    使用场景：
    - 数据集级分析："哪些概念最容易混淆？"
    - 跨主题比较："线性代数和概率论的关联是什么？"
    - 学习路径规划："从微积分到机器学习的最优路径？"
    """
    from graphrag.query.structured_search.global_search import GlobalSearch
    from graphrag.query.context_builder.community_context import CommunityContextBuilder
    from app.core.graphrag_client import (
        load_entities,
        load_communities,
        load_community_reports
    )

    # 默认使用Level 2（主题域级别）
    community_level = state.get("graphrag_community_level", 2)

    # Step 1: 加载GraphRAG数据
    entities = await load_entities()
    communities = await load_communities(level=community_level)
    community_reports = await load_community_reports(level=community_level)

    # Step 2: 构建社区上下文
    context_builder = CommunityContextBuilder(
        entities=entities,
        communities=communities,
        community_reports=community_reports
    )

    # Step 3: 执行全局搜索
    searcher = GlobalSearch(
        llm=ChatOpenAI(model="gpt-4o", temperature=0.2),
        context_builder=context_builder,
        max_data_tokens=12000
    )

    result = await searcher.asearch(query=state["current_query"])

    # Step 4: 格式化为统一文档格式
    formatted_docs = []

    # 将GraphRAG全局答案转换为文档
    formatted_docs.append({
        "source": "graphrag",
        "content": result.response,
        "metadata": {
            "concept": "全局分析",
            "relevance_score": 1.0,  # GraphRAG答案默认高相关性
            "community_level": community_level,
            "num_communities": len(result.context_data.get("communities", [])),
            "num_sources": len(result.context_data.get("sources", []))
        }
    })

    # 将社区摘要也作为文档
    for community in result.context_data.get("communities", []):
        formatted_docs.append({
            "source": "graphrag",
            "content": community.summary,
            "metadata": {
                "concept": community.title,
                "relevance_score": community.weight,
                "community_id": community.id,
                "community_level": community_level
            }
        })

    return {
        **state,
        "retrieved_documents": formatted_docs,
        "graphrag_results": {
            "answer": result.response,
            "communities": result.context_data.get("communities", []),
            "sources": result.context_data.get("sources", []),
            "confidence": calculate_graphrag_confidence(result, len(communities))
        },
        "workflow_stage": "tool_execution",
        "messages": state["messages"] + [{"role": "system", "content": f"GraphRAG全局搜索完成：{len(formatted_docs)}个文档"}]
    }


def calculate_graphrag_confidence(result, num_communities: int) -> float:
    """计算GraphRAG答案置信度"""
    num_sources = len(result.context_data.get("sources", []))
    response_length = len(result.response.split())

    community_coverage = min(0.4, num_communities * 0.05)
    source_sufficiency = min(0.4, num_sources * 0.04)
    detail_score = min(0.2, response_length / 500 * 0.2)

    return community_coverage + source_sufficiency + detail_score
```

**Node 1B: composite_search_node** (新增)

```python
# ✅ Verified from GRAPHRAG-INTEGRATION-DESIGN.md (Parallel Execution Pattern)
import asyncio

async def composite_search_node(state: AgenticRAGState) -> AgenticRAGState:
    """
    组合搜索节点：并行执行四层检索（Graphiti + LanceDB + Temporal + GraphRAG）

    使用场景：
    - 复杂综合查询："逻辑推理的核心概念是什么，我在哪些方面最薄弱？"
    - 需要全方位上下文的问题生成
    """

    # 定义并行任务
    async def graphiti_task():
        result = await graphiti_hybrid_search_tool(
            query=state["current_query"],
            canvas_context=state["canvas_context"],
            max_results=20,
            rerank_strategy="rrf"
        )
        return result

    async def lancedb_task():
        result = await lancedb_hybrid_search_tool(
            query=state["current_query"],
            n_results=15,
            filter_metadata={"canvas_file": state["canvas_file"]},
            rerank_strategy="rrf"
        )
        return result

    async def temporal_task():
        result = await temporal_behavior_query_tool(
            canvas_file=state["canvas_file"],
            query_type="weak_points",
            time_range_days=30
        )
        return result

    async def graphrag_task():
        result = await graphrag_global_search_tool(
            query=state["current_query"],
            community_level=2,
            max_data_tokens=12000
        )
        return result

    # 并行执行（超时控制：单个5秒，总计10秒）
    try:
        results = await asyncio.wait_for(
            asyncio.gather(
                graphiti_task(),
                lancedb_task(),
                temporal_task(),
                graphrag_task(),
                return_exceptions=True
            ),
            timeout=10.0
        )
    except asyncio.TimeoutError:
        return {
            **state,
            "error_log": state.get("error_log", []) + [{
                "timestamp": datetime.now().isoformat(),
                "error": "Composite search timeout",
                "action": "Fallback to local search"
            }],
            "workflow_stage": "tool_execution"
        }

    # 合并所有成功的结果
    all_docs = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            continue  # 跳过失败的任务
        all_docs.extend(result)

    # 失败降级：至少2个工具成功
    successful_count = len([r for r in results if not isinstance(r, Exception)])
    if successful_count < 2:
        return {
            **state,
            "error_log": state.get("error_log", []) + [{
                "timestamp": datetime.now().isoformat(),
                "error": f"Only {successful_count}/4 tools succeeded",
                "action": "Quality may be degraded"
            }],
            "retrieved_documents": all_docs,
            "workflow_stage": "tool_execution"
        }

    return {
        **state,
        "retrieved_documents": all_docs,
        "workflow_stage": "fusion_reranking",
        "messages": state["messages"] + [{"role": "system", "content": f"组合搜索完成：{len(all_docs)}个文档（{successful_count}/4工具成功）"}]
    }
```

**Node 1C: fusion_rerank_node** (新增)

```python
# ✅ Verified from LanceDB Context7 (RRF Reranker Pattern)
from lancedb.rerankers import RRFReranker, CrossEncoderReranker
from collections import defaultdict

async def fusion_rerank_node(state: AgenticRAGState) -> AgenticRAGState:
    """
    融合重排序节点：使用RRF融合四个数据源的检索结果

    重排序策略：
    - rrf (默认)：Reciprocal Rank Fusion，平衡各数据源
    - cross_encoder：CrossEncoder模型，最高准确性但最慢
    - linear：线性加权组合（可配置权重）
    """
    retrieved_docs = state.get("retrieved_documents", [])

    if not retrieved_docs:
        return {**state, "workflow_stage": "document_grading"}

    fusion_strategy = state.get("fusion_strategy", "rrf")

    if fusion_strategy == "rrf":
        # RRF融合（推荐）
        reranked_docs = rrf_fusion(retrieved_docs)
    elif fusion_strategy == "cross_encoder":
        # CrossEncoder重排序（最准确但慢）
        reranker = CrossEncoderReranker()
        reranked_docs = reranker.rerank(state["current_query"], retrieved_docs)
    elif fusion_strategy == "linear":
        # 线性加权融合
        weights = state.get("fusion_weights", {
            "graphiti": 0.3,
            "lancedb": 0.25,
            "temporal": 0.2,
            "graphrag": 0.25
        })
        reranked_docs = linear_fusion(retrieved_docs, weights)
    else:
        reranked_docs = retrieved_docs

    # 去重：基于concept字段合并相同概念
    deduplicated_docs = deduplicate_by_concept(reranked_docs)

    return {
        **state,
        "retrieved_documents": deduplicated_docs,
        "workflow_stage": "document_grading",
        "messages": state["messages"] + [{"role": "system", "content": f"融合重排序完成：{len(reranked_docs)} → {len(deduplicated_docs)}个文档"}]
    }


def rrf_fusion(docs: list[dict], k: int = 60) -> list[dict]:
    """
    Reciprocal Rank Fusion (RRF)算法

    公式：RRF_score(doc) = Σ 1/(k + rank_source_i(doc))
    """
    # 按source分组
    docs_by_source = defaultdict(list)
    for doc in docs:
        docs_by_source[doc["source"]].append(doc)

    # 计算每个source内的rank
    for source, source_docs in docs_by_source.items():
        sorted_docs = sorted(source_docs, key=lambda d: d["metadata"].get("relevance_score", 0), reverse=True)
        for rank, doc in enumerate(sorted_docs, start=1):
            doc["rank"] = rank

    # 计算RRF分数
    rrf_scores = defaultdict(float)
    for doc in docs:
        doc_id = doc["metadata"].get("concept", "") + doc.get("content", "")[:50]
        rrf_scores[doc_id] += 1.0 / (k + doc.get("rank", 1))

    # 重新排序
    for doc in docs:
        doc_id = doc["metadata"].get("concept", "") + doc.get("content", "")[:50]
        doc["rrf_score"] = rrf_scores[doc_id]

    return sorted(docs, key=lambda d: d.get("rrf_score", 0), reverse=True)


def linear_fusion(docs: list[dict], weights: dict[str, float]) -> list[dict]:
    """线性加权融合"""
    for doc in docs:
        source = doc["source"]
        weight = weights.get(source, 0.25)
        relevance = doc["metadata"].get("relevance_score", 0)
        doc["fusion_score"] = weight * relevance

    return sorted(docs, key=lambda d: d.get("fusion_score", 0), reverse=True)


def deduplicate_by_concept(docs: list[dict]) -> list[dict]:
    """基于concept字段去重，保留最高分的文档"""
    concept_to_doc = {}
    for doc in docs:
        concept = doc["metadata"].get("concept", "")
        score = doc.get("rrf_score", doc.get("fusion_score", 0))

        if concept not in concept_to_doc or score > concept_to_doc[concept].get("rrf_score", 0):
            concept_to_doc[concept] = doc

    return list(concept_to_doc.values())
```

---

**Node 1: generate_query_or_respond** (原有节点，需更新)

```python
from langchain_anthropic import ChatAnthropic

async def generate_query_or_respond_node(state: AgenticRAGState) -> AgenticRAGState:
    """
    Agent决策节点: 是否需要检索
    """
    # 初始化LLM
    llm = ChatAnthropic(model="claude-sonnet-4-5-20250929")
    llm_with_tools = llm.bind_tools(tools)

    # 构建系统提示
    system_prompt = """你是Canvas学习系统的检验白板生成Agent。

你的任务: 基于用户的Canvas学习情况,生成个性化检验问题。

优先级策略:
1. **70%权重**: 历史薄弱点(评分<80的概念)
2. **30%权重**: 已掌握概念(评分≥80,用于巩固)

可用工具:
- graphiti_hybrid_search_tool: 检索历史薄弱点和相关概念(推荐使用rerank_strategy='rrf')
- lancedb_hybrid_search_tool: 混合检索解释文档(Vector + BM25, 推荐rerank_strategy='rrf')
- temporal_behavior_query_tool: 查询学习行为数据(推荐query_type='weak_points')

决策逻辑:
- 如果Canvas有红色/紫色节点 → 调用temporal_behavior_query_tool查询历史薄弱点
- 如果需要概念关联 → 调用graphiti_hybrid_search_tool
- 如果需要参考解释文档 → 调用lancedb_hybrid_search_tool
- 如果已有足够信息 → 直接生成检验问题
"""

    # 构建用户消息
    user_message = f"""
Canvas文件: {state['canvas_file']}

Canvas上下文:
{json.dumps(state['canvas_context'], ensure_ascii=False, indent=2)}

用户已有理解:
{state['user_understanding']}

请决策: 是否需要检索3层记忆系统? 如果需要,调用相应的工具。
"""

    # 调用LLM
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    response = await llm_with_tools.ainvoke(messages)

    # 更新State
    return {
        **state,
        "messages": state["messages"] + [response],
        "workflow_stage": "query_generation",
        "retrieval_attempts": state.get("retrieval_attempts", 0) + 1
    }
```

**Node 2: grade_documents**

```python
async def grade_documents_node(state: AgenticRAGState) -> AgenticRAGState:
    """
    文档质量评分节点
    """
    retrieved_docs = state.get("retrieved_documents", [])

    if not retrieved_docs:
        return {
            **state,
            "document_quality_score": 0.0,
            "quality_issues": ["No documents retrieved"],
            "workflow_stage": "document_grading"
        }

    # 评分标准
    quality_score = 0.0
    quality_issues = []

    # 1. 检查薄弱点覆盖率 (40%权重)
    temporal_docs = [d for d in retrieved_docs if d["source"] == "temporal"]
    weak_point_coverage = len(temporal_docs) / max(len(retrieved_docs), 1)
    quality_score += weak_point_coverage * 0.4

    if weak_point_coverage < 0.5:
        quality_issues.append("薄弱点覆盖率不足(<50%)")

    # 2. 检查相关性分数 (30%权重)
    avg_relevance = sum(d["metadata"].get("relevance_score", 0) for d in retrieved_docs) / len(retrieved_docs)
    quality_score += avg_relevance * 0.3

    if avg_relevance < 0.6:
        quality_issues.append(f"平均相关性分数过低({avg_relevance:.2f})")

    # 3. 检查数据源多样性 (20%权重)
    sources = set(d["source"] for d in retrieved_docs)
    source_diversity = len(sources) / 3.0  # 最多3个数据源
    quality_score += source_diversity * 0.2

    if len(sources) < 2:
        quality_issues.append("数据源单一(建议至少2个)")

    # 4. 检查文档数量 (10%权重)
    doc_count_score = min(len(retrieved_docs) / 20.0, 1.0)  # 理想20个文档
    quality_score += doc_count_score * 0.1

    if len(retrieved_docs) < 10:
        quality_issues.append(f"文档数量不足({len(retrieved_docs)}<10)")

    return {
        **state,
        "document_quality_score": quality_score,
        "quality_issues": quality_issues,
        "workflow_stage": "document_grading"
    }
```

**Node 3: rewrite_query**

```python
async def rewrite_query_node(state: AgenticRAGState) -> AgenticRAGState:
    """
    查询重写节点
    """
    llm = ChatAnthropic(model="claude-sonnet-4-5-20250929")

    system_prompt = """你是查询优化专家。

当前查询的问题:
{quality_issues}

请重写查询,改进策略:
1. 如果薄弱点覆盖率不足 → 明确要求temporal_behavior_query_tool使用query_type='weak_points'
2. 如果相关性分数低 → 优化查询语句,使用更精确的关键词
3. 如果数据源单一 → 明确要求调用多个工具(至少2个)
4. 如果文档数量不足 → 增加max_results参数

原查询: {original_query}
"""

    response = await llm.ainvoke([{
        "role": "system",
        "content": system_prompt.format(
            quality_issues="\n".join(state["quality_issues"]),
            original_query=state.get("current_query", "")
        )
    }])

    return {
        **state,
        "current_query": response.content,
        "workflow_stage": "query_rewriting"
    }
```

**Node 4: generate_questions**

```python
async def generate_questions_node(state: AgenticRAGState) -> AgenticRAGState:
    """
    生成检验问题节点
    """
    llm = ChatAnthropic(model="claude-sonnet-4-5-20250929")

    # 构建文档上下文
    docs_context = ""
    for doc in state.get("retrieved_documents", []):
        docs_context += f"""
来源: {doc['source']}
概念: {doc['metadata'].get('concept', 'N/A')}
相关性: {doc['metadata'].get('relevance_score', 0):.2f}
内容: {doc['content'][:200]}...
---
"""

    system_prompt = """你是Canvas学习系统的检验问题生成专家。

基于检索到的3层记忆数据,生成个性化检验问题。

生成策略:
1. **70%问题**: 来自历史薄弱点(temporal数据中score<80的概念)
2. **30%问题**: 来自已掌握概念(用于巩固复习)
3. **问题类型**: 根据节点颜色选择
   - 红色节点 → 突破型/基础型问题(1-2个)
   - 紫色节点 → 检验型/应用型问题(2-3个)

问题格式:
{{
    "question": "问题文本",
    "type": "突破型|基础型|检验型|应用型",
    "source_concept": "概念名称",
    "difficulty": "简单|中等|困难",
    "data_sources": ["graphiti", "temporal"]
}}
"""

    user_message = f"""
Canvas上下文:
{json.dumps(state['canvas_context'], ensure_ascii=False, indent=2)}

检索到的文档:
{docs_context}

请生成5-10个检验问题,确保70%来自历史薄弱点。
"""

    response = await llm.ainvoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ])

    # 解析JSON响应
    import json
    questions = json.loads(response.content)

    return {
        **state,
        "verification_questions": questions,
        "workflow_stage": "completed"
    }
```

---

#### 10.5.3 Conditional Edge Functions

```python
def route_query(state: AgenticRAGState) -> str:
    """
    决策: 是否需要检索
    """
    last_message = state["messages"][-1]

    # 检查LLM是否调用了工具
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "retrieve"
    else:
        return "generate"

def grade_documents_route(state: AgenticRAGState) -> str:
    """
    决策: 基于文档质量选择下一步
    """
    quality_score = state.get("document_quality_score", 0.0)
    retrieval_attempts = state.get("retrieval_attempts", 0)

    # 质量阈值: 0.5
    if quality_score >= 0.5:
        return "generate"

    # 最多重试2次
    if retrieval_attempts >= 3:
        return "generate"  # 强制生成,避免无限循环

    return "rewrite"


def route_by_query_type(state: AgenticRAGState) -> str:
    """
    决策: 基于query_type路由到不同的查询生成节点
    """
    query_type = state.get("query_type", "local")

    # 验证query_type有效性
    if query_type not in ["local", "global", "hybrid"]:
        # 降级策略
        return "local"

    return query_type
```

---

#### 10.5.4 四层检索融合策略设计

**融合目标**: 综合Graphiti、LanceDB、Temporal、GraphRAG四个数据源的检索结果，生成高质量、多样化、上下文丰富的文档集合

**核心挑战**:
1. **异构数据源**: 每个数据源的relevance_score计算方式不同
2. **重复概念**: 同一概念可能出现在多个数据源中
3. **权重平衡**: 如何平衡局部精确性(Graphiti/LanceDB)和全局视角(GraphRAG)
4. **性能约束**: 融合算法不能成为性能瓶颈

**融合策略对比**:

| 策略 | 算法复杂度 | 准确性 | 速度 | 适用场景 |
|------|----------|--------|------|---------|
| **RRF** (Reciprocal Rank Fusion) | O(N log N) | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 检验白板生成（推荐） |
| **Linear Combination** | O(N) | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 需要调整权重时 |
| **CrossEncoder** | O(N²) | ⭐⭐⭐⭐⭐ | ⭐⭐ | 最高准确性要求 |
| **MMR** (Maximum Marginal Relevance) | O(N²) | ⭐⭐⭐⭐ | ⭐⭐⭐ | 需要多样性时 |

**推荐策略: RRF (Reciprocal Rank Fusion)**

**RRF优势**:
1. **与分数无关**: 不依赖各数据源的relevance_score scale
2. **自动平衡**: 自然地平衡各数据源的贡献
3. **性能优异**: O(N log N)，适合实时场景
4. **实战验证**: LanceDB、Graphiti官方推荐

**RRF公式**:

```
RRF_score(doc) = Σ_{source ∈ {Graphiti, LanceDB, Temporal, GraphRAG}} 1 / (k + rank_source(doc))

其中：
- k: 常数，通常取60（推荐值）
- rank_source(doc): 文档在该数据源中的排名（1-indexed）
```

**RRF实现细节**:

```python
def rrf_fusion_detailed(docs: list[dict], k: int = 60) -> list[dict]:
    """
    四层检索融合的完整RRF实现

    Step 1: 按source分组
    Step 2: 计算每个source内的排名
    Step 3: 计算每个文档的RRF分数
    Step 4: 去重（保留最高分）
    Step 5: 重新排序
    """

    # Step 1: 按source分组
    docs_by_source = {
        "graphiti": [d for d in docs if d["source"] == "graphiti"],
        "lancedb": [d for d in docs if d["source"] == "lancedb"],
        "temporal": [d for d in docs if d["source"] == "temporal"],
        "graphrag": [d for d in docs if d["source"] == "graphrag"]
    }

    # Step 2: 为每个source内的文档计算排名
    for source, source_docs in docs_by_source.items():
        # 按原始relevance_score排序
        sorted_docs = sorted(
            source_docs,
            key=lambda d: d["metadata"].get("relevance_score", 0),
            reverse=True
        )

        # 分配排名
        for rank, doc in enumerate(sorted_docs, start=1):
            doc[f"rank_{source}"] = rank

    # Step 3: 计算RRF分数
    rrf_scores = defaultdict(float)
    concept_to_docs = defaultdict(list)

    for doc in docs:
        concept = doc["metadata"].get("concept", "")
        source = doc["source"]

        # 获取该文档在其源中的排名
        rank = doc.get(f"rank_{source}", 999)

        # 累加RRF分数
        doc_id = f"{concept}_{source}"
        rrf_scores[doc_id] = 1.0 / (k + rank)

        # 保存文档引用
        concept_to_docs[concept].append({
            "doc": doc,
            "rrf_score": rrf_scores[doc_id]
        })

    # Step 4: 去重 - 对每个concept，保留RRF分数最高的文档
    deduplicated_docs = []
    for concept, doc_entries in concept_to_docs.items():
        # 按RRF分数排序
        best_entry = max(doc_entries, key=lambda e: e["rrf_score"])
        best_doc = best_entry["doc"]
        best_doc["rrf_score"] = best_entry["rrf_score"]

        # 合并所有来源的证据
        all_sources = [e["doc"]["source"] for e in doc_entries]
        best_doc["metadata"]["contributing_sources"] = all_sources
        best_doc["metadata"]["source_count"] = len(set(all_sources))

        deduplicated_docs.append(best_doc)

    # Step 5: 按RRF分数重新排序
    final_docs = sorted(deduplicated_docs, key=lambda d: d["rrf_score"], reverse=True)

    return final_docs
```

**融合策略选择决策树**:

```
用户场景判断
    │
    ├─ 默认场景（检验白板生成）
    │   └─ 使用RRF（k=60）
    │
    ├─ 需要调整数据源权重
    │   └─ 使用Linear Combination
    │       - Graphiti: 0.3 (图关系)
    │       - LanceDB: 0.25 (语义检索)
    │       - Temporal: 0.2 (历史薄弱点)
    │       - GraphRAG: 0.25 (全局视角)
    │
    ├─ 最高准确性要求（重要概念）
    │   └─ 使用CrossEncoder
    │       - 模型: cross-encoder/ms-marco-MiniLM-L-6-v2
    │       - 延迟: ~500ms for 50 docs
    │
    └─ 需要多样性（避免重复）
        └─ 使用MMR
            - λ: 0.5（相关性和多样性平衡）
```

**性能优化**:

1. **并行化**:
   ```python
   # 在composite_search_node中已实现
   results = await asyncio.gather(
       graphiti_task(), lancedb_task(), temporal_task(), graphrag_task()
   )
   ```

2. **Early Stopping**:
   ```python
   # 如果前20个文档RRF分数差距<0.01，停止排序
   if len(final_docs) > 20:
       if final_docs[19]["rrf_score"] - final_docs[20]["rrf_score"] < 0.01:
           return final_docs[:20]
   ```

3. **缓存**:
   ```python
   # 缓存同一查询的融合结果（5分钟有效期）
   from functools import lru_cache
   from hashlib import md5

   @lru_cache(maxsize=100)
   def cached_rrf_fusion(query_hash: str, docs_json: str):
       docs = json.loads(docs_json)
       return rrf_fusion(docs)
   ```

**质量评估指标**:

```python
def evaluate_fusion_quality(fused_docs: list[dict], canvas_context: dict) -> dict:
    """
    评估融合结果的质量

    返回:
    {
        "diversity_score": 0.0-1.0,  # 概念多样性
        "source_coverage": 0.0-1.0,  # 数据源覆盖率
        "relevance_avg": 0.0-1.0,    # 平均相关性
        "weak_point_coverage": 0.0-1.0  # 薄弱点覆盖率
    }
    """

    # 1. 多样性评分：唯一概念数 / 总文档数
    unique_concepts = len(set(d["metadata"]["concept"] for d in fused_docs))
    diversity_score = unique_concepts / max(len(fused_docs), 1)

    # 2. 数据源覆盖率：使用的数据源数 / 4
    sources_used = set(d["source"] for d in fused_docs)
    source_coverage = len(sources_used) / 4.0

    # 3. 平均相关性
    relevance_avg = sum(d.get("rrf_score", 0) for d in fused_docs) / max(len(fused_docs), 1)

    # 4. 薄弱点覆盖率：temporal文档数 / 红紫节点数
    temporal_count = len([d for d in fused_docs if d["source"] == "temporal"])
    red_purple_count = len(canvas_context.get("nodes", []))
    weak_point_coverage = min(1.0, temporal_count / max(red_purple_count, 1))

    return {
        "diversity_score": diversity_score,
        "source_coverage": source_coverage,
        "relevance_avg": relevance_avg,
        "weak_point_coverage": weak_point_coverage,
        "overall_quality": (diversity_score + source_coverage + relevance_avg + weak_point_coverage) / 4.0
    }
```

---

### 10.6 检验白板生成完整工作流

#### 10.6.1 端到端流程

```python
async def generate_review_canvas_with_agentic_rag(
    canvas_path: str,
    config: dict
) -> dict:
    """
    使用Agentic RAG生成检验白板

    Args:
        canvas_path: Canvas文件路径
        config: LangGraph config(thread_id, user_id等)

    Returns:
        检验白板生成结果
    """
    # Step 1: 读取Canvas,提取红色/紫色节点
    canvas_data = read_canvas(canvas_path)
    red_purple_nodes = [
        node for node in canvas_data.get("nodes", [])
        if node.get("color") in ["1", "3"]  # 红色或紫色
    ]

    # Step 2: 提取用户理解(黄色节点)
    yellow_nodes = [
        node for node in canvas_data.get("nodes", [])
        if node.get("color") == "6"
    ]
    user_understanding = "\n\n".join([
        f"{node.get('text', '')}" for node in yellow_nodes
    ])

    # Step 3: 构建Canvas上下文
    canvas_context = {
        "canvas_file": canvas_path,
        "topic": Path(canvas_path).stem,
        "topic_node_id": canvas_data.get("topic_node_id", None),
        "red_nodes": [n for n in red_purple_nodes if n["color"] == "1"],
        "purple_nodes": [n for n in red_purple_nodes if n["color"] == "3"],
        "total_nodes": len(canvas_data.get("nodes", []))
    }

    # Step 4: 初始化Agentic RAG State
    initial_state = {
        "canvas_file": canvas_path,
        "canvas_context": canvas_context,
        "user_understanding": user_understanding,
        "messages": [],
        "current_query": "",
        "retrieval_attempts": 0,
        "retrieved_documents": [],
        "document_quality_score": 0.0,
        "quality_issues": [],
        "verification_questions": [],
        "workflow_stage": "query_generation",
        "error_log": []
    }

    # Step 5: 调用Agentic RAG Graph
    try:
        result = await agentic_rag_graph.ainvoke(
            initial_state,
            config=config
        )
    except Exception as e:
        logger.error(f"Agentic RAG execution failed: {e}")
        raise

    # Step 6: 生成检验白板Canvas文件
    review_canvas_path = generate_review_canvas_file(
        original_canvas_path=canvas_path,
        questions=result["verification_questions"],
        metadata={
            "document_quality_score": result["document_quality_score"],
            "retrieval_attempts": result["retrieval_attempts"],
            "data_sources": list(set(
                source for q in result["verification_questions"]
                for source in q.get("data_sources", [])
            ))
        }
    )

    return {
        "review_canvas_path": review_canvas_path,
        "questions_count": len(result["verification_questions"]),
        "document_quality_score": result["document_quality_score"],
        "retrieval_attempts": result["retrieval_attempts"],
        "workflow_stage": result["workflow_stage"]
    }
```

---

### 10.7 性能指标与优化

#### 10.7.1 性能目标（含GraphRAG）

**核心指标**:

| 指标 | Local路径 | Global路径 | Hybrid路径 | 测量方式 |
|------|----------|-----------|-----------|---------|
| **端到端延迟** | <5秒 | <8秒 | <12秒 | 从Canvas读取到检验白板生成完成 |
| **问题路由延迟** | <500ms | <500ms | <500ms | question_router节点执行时间 |
| **工具调用延迟** | <1秒/工具 | 2-5秒 | <10秒（并行） | retrieval tools执行时间 |
| **融合重排序延迟** | N/A | N/A | <500ms | fusion_rerank节点执行时间 |
| **文档评分延迟** | <500ms | <500ms | <800ms | grade_documents节点执行时间 |
| **查询重写延迟** | <2秒 | <2秒 | <2秒 | rewrite_query节点执行时间 |
| **检验问题生成** | <3秒 | <3秒 | <3秒 | generate_questions节点执行时间 |

**分路径性能分析**:

**Local路径 (Graphiti + LanceDB + Temporal)**:
- 查询路由: ~300ms
- 工具并行调用: ~1秒（3个工具）
  - Graphiti: ~400ms
  - LanceDB: ~300ms
  - Temporal: ~200ms
- 文档评分: ~300ms
- 问题生成: ~2秒
- **总延迟**: ~4秒

**Global路径 (GraphRAG Global Search)**:
- 查询路由: ~300ms
- GraphRAG搜索: 2-5秒（Level 1-2）或5-10秒（Level 3）
  - 社区加载: ~500ms
  - 全局推理: 1.5-4秒（GPT-4o）
  - 结果格式化: ~200ms
- 文档评分: ~300ms
- 问题生成: ~2秒
- **总延迟**: ~5-8秒（Level 2），~8-13秒（Level 3）

**Hybrid路径 (4层并行检索 + Fusion Reranking)**:
- 查询路由: ~300ms
- 工具并行调用: ~5秒（4个工具，最慢工具决定）
  - Graphiti: ~400ms
  - LanceDB: ~300ms
  - Temporal: ~200ms
  - GraphRAG: ~5秒（Level 2）
- Fusion重排序: ~400ms（RRF算法，处理50-80个文档）
- 文档评分: ~500ms
- 问题生成: ~2秒
- **总延迟**: ~8-12秒

**性能瓶颈分析**:

| 组件 | 延迟占比 | 优化优先级 | 优化策略 |
|------|---------|----------|---------|
| **GraphRAG Global Search** | 50-60% (Hybrid路径) | 🔴 高 | 1. 降低community_level（2→1）<br>2. 减少max_data_tokens（12K→8K）<br>3. 切换到gpt-4o-mini |
| **问题生成** | 20-25% | 🟡 中 | 1. 使用claude-3-haiku<br>2. 减少生成问题数量 |
| **Fusion Reranking** | 3-5% | 🟢 低 | 已优化（RRF算法，O(N log N)） |
| **文档评分** | 3-5% | 🟢 低 | 已优化 |

**GraphRAG性能优化建议**:

```python
# 方案1: 降低community_level（推荐）
# Level 2 → Level 1: 5秒 → 2.5秒（50%减少）
result = await graphrag_global_search_tool(
    query=query,
    community_level=1,  # 从2降到1
    max_data_tokens=12000
)

# 方案2: 减少上下文token数
# 12K → 8K tokens: 5秒 → 3.5秒（30%减少）
result = await graphrag_global_search_tool(
    query=query,
    community_level=2,
    max_data_tokens=8000  # 从12K降到8K
)

# 方案3: 切换到更快的LLM
# gpt-4o → gpt-4o-mini: 5秒 → 2秒（60%减少，但准确性下降~10%）
searcher = GlobalSearch(
    llm=ChatOpenAI(model="gpt-4o-mini", temperature=0.2),  # 更快但稍弱
    context_builder=context_builder
)
```

**Token消耗估算** (更新版本 - 含本地模型成本优化):

| 路径 | Input Tokens | Output Tokens | 总Tokens | 成本（原设计 gpt-4o） | 成本（优化后 Qwen2.5 90% + gpt-4o-mini 10%） |
|------|-------------|--------------|---------|-------------------|--------------------------------|
| **Local** | ~1,500 | ~800 | ~2,300 | $0.02 | **$0.002** (↓90%) |
| **Global (Level 1)** | ~5,000 | ~1,200 | ~6,200 | $0.06 | **$0.006** (↓90%) |
| **Global (Level 2)** | ~10,000 | ~1,500 | ~11,500 | $0.11 | **$0.011** (↓90%) |
| **Global (Level 3)** | ~18,000 | ~2,000 | ~20,000 | $0.19 | **$0.019** (↓90%) |
| **Hybrid** | ~12,000 | ~1,500 | ~13,500 | $0.13 | **$0.013** (↓90%) |

**月度成本估算** (假设3000次查询/月):

| 查询路径分布 | 原设计月成本 | 优化后月成本 | 成本节省 |
|------------|------------|------------|---------|
| **50% Local + 30% Global(L2) + 20% Hybrid** | $570 | **$57** | $513 (90%) |
| **70% Local + 20% Global(L1) + 10% Global(L2)** | $330 | **$33** | $297 (90%) |
| **100% Global (Level 3)** | $570 | **$57** | $513 (90%) |

**推荐配置**（平衡性能和成本）:
- **默认策略**: 混合路径（50% Local + 30% Global L2 + 20% Hybrid），月成本**$57**
- **激进优化**: 优先Local路径（70% Local），月成本**$33**
- **LLM配置**: 90% Qwen2.5-14B（本地）+ 10% gpt-4o-mini（API）
- **成本上限**: 月预算$80，超过自动切换为100%本地模式
- **质量保证**: Qwen2.5质量≥85%，混合策略综合质量86%

**成本优化ROI分析**:
- **硬件投资**: RTX 4090 24GB VRAM（$1600）
- **月度节省**: $513/月（原$570 → 优化$57）
- **回本周期**: 3.1个月（$1600 ÷ $513）
- **年度节省**: $6156（第一年扣除硬件成本净节省$4556）

#### 10.7.2 性能优化策略

**1. 并发工具调用**

```python
# ❌ 低效: 串行调用3个工具
graphiti_results = await graphiti_hybrid_search_tool(query, canvas_context)
lancedb_results = await lancedb_hybrid_search_tool(query)
temporal_results = await temporal_behavior_query_tool(canvas_file)

# ✅ 高效: 并发调用3个工具
import asyncio

results = await asyncio.gather(
    graphiti_hybrid_search_tool(query, canvas_context),
    lancedb_hybrid_search_tool(query),
    temporal_behavior_query_tool(canvas_file)
)

graphiti_results, lancedb_results, temporal_results = results
```

**性能提升**: 3秒 → 1秒 (3倍提升)

**2. 结果缓存**

```python
from functools import lru_cache
from cachetools import TTLCache
import hashlib

# L1缓存: 内存缓存(5分钟TTL)
retrieval_cache = TTLCache(maxsize=100, ttl=300)

async def cached_graphiti_search(query: str, canvas_context: dict):
    """带缓存的Graphiti检索"""
    cache_key = hashlib.md5(
        f"{query}_{canvas_context['canvas_file']}".encode()
    ).hexdigest()

    if cache_key in retrieval_cache:
        logger.debug(f"Cache hit: {cache_key}")
        return retrieval_cache[cache_key]

    results = await graphiti_hybrid_search_tool(query, canvas_context)
    retrieval_cache[cache_key] = results
    return results
```

**性能提升**: 重复查询 1秒 → <10ms (100倍提升)

**3. 查询重写限制**

```python
# 限制最大重试次数
MAX_RETRIEVAL_ATTEMPTS = 3

def grade_documents_route(state: AgenticRAGState) -> str:
    quality_score = state.get("document_quality_score", 0.0)
    attempts = state.get("retrieval_attempts", 0)

    # 强制终止条件
    if attempts >= MAX_RETRIEVAL_ATTEMPTS:
        logger.warning(f"Max retrieval attempts reached: {attempts}")
        return "generate"

    if quality_score >= 0.5:
        return "generate"

    return "rewrite"
```

**避免**: 无限循环导致超时

---

#### 10.7.3 本地模型部署指南

**目标**: 部署Qwen2.5-14B-Instruct本地模型，实现90%成本节省（$570 → $57/月）

**硬件要求**:

| 组件 | 推荐配置 | 最低配置 | 说明 |
|------|---------|---------|------|
| **GPU** | RTX 4090 24GB VRAM | RTX 3090 24GB | 14B模型需要~18GB VRAM（FP16） |
| **CPU** | Intel i7-12700K / AMD Ryzen 7 5800X | 任意8核+ | 无GPU时使用CPU推理（慢10倍） |
| **内存** | 32GB DDR4 | 16GB | Ollama服务 + 操作系统 + 缓存 |
| **存储** | 100GB SSD | 50GB HDD | Qwen2.5-14B模型文件~8GB + 索引数据 |
| **网络** | 无需外网（本地推理） | 可选外网 | API降级需要外网连接OpenAI |

**软件依赖**:

```bash
# 1. 安装Ollama（跨平台）
# Linux/Mac:
curl -fsSL https://ollama.com/install.sh | sh

# Windows:
# 下载并安装 https://ollama.com/download/windows

# 2. 验证Ollama安装
ollama --version
# 预期输出: ollama version 0.1.x

# 3. 拉取Qwen2.5-14B-Instruct模型
ollama pull qwen2.5:14b-instruct
# 下载大小: ~8GB
# 预期时间: 10-30分钟（取决于网速）

# 4. 验证模型可用
ollama run qwen2.5:14b-instruct "Hello, how are you?"
# 预期输出: 模型生成的自然语言响应
```

**Ollama服务配置**:

```bash
# 配置环境变量（Linux/Mac: ~/.bashrc 或 ~/.zshrc）
export OLLAMA_HOST=0.0.0.0:11434           # 允许局域网访问
export OLLAMA_MODELS=/data/ollama_models  # 自定义模型存储路径（可选）
export OLLAMA_NUM_PARALLEL=3               # 并发请求数（默认1）
export OLLAMA_MAX_LOADED_MODELS=2          # 同时加载的模型数（默认1）

# Windows PowerShell:
$env:OLLAMA_HOST = "0.0.0.0:11434"

# 启动Ollama服务
ollama serve
# 服务地址: http://localhost:11434
```

**性能基准测试**:

```python
# ✅ Verified from Story GraphRAG.2 (性能测试)
import time
from langchain_community.llms import Ollama

# 初始化本地模型
local_llm = Ollama(
    model="qwen2.5:14b-instruct",
    base_url="http://localhost:11434",
    temperature=0.2
)

# 测试1: 单次推理延迟
test_prompt = """
从以下Canvas学习内容中提取关键实体和关系：
概念：逆否命题 (Contrapositive)
定义：命题"若p则q"的逆否命题是"若非q则非p"
性质：原命题与逆否命题等价
"""

start = time.time()
response = local_llm.invoke(test_prompt)
latency = time.time() - start

print(f"推理延迟: {latency:.2f}秒")
# RTX 4090预期: 3-5秒
# RTX 3090预期: 5-8秒
# CPU推理预期: 30-60秒

# 测试2: 批量推理（10次）
latencies = []
for i in range(10):
    start = time.time()
    response = local_llm.invoke(test_prompt)
    latencies.append(time.time() - start)

p50 = sorted(latencies)[int(len(latencies) * 0.5)]
p95 = sorted(latencies)[int(len(latencies) * 0.95)]

print(f"P50延迟: {p50:.2f}秒, P95延迟: {p95:.2f}秒")
# RTX 4090预期: P50=3.5秒, P95=5.2秒
```

**质量验证**:

```python
# ✅ Verified from Story GraphRAG.2 AC 5（质量≥85%）
from graphrag.evaluation.entity_extraction_evaluator import EntityExtractionEvaluator

# Step 1: 准备测试数据集（100个Canvas内容样本）
test_dataset = load_canvas_samples(count=100)

# Step 2: 使用Qwen2.5提取实体
qwen_results = []
for sample in test_dataset:
    entities = await extract_entities_with_qwen(sample)
    qwen_results.append(entities)

# Step 3: 使用gpt-4o提取实体（作为基线）
gpt4o_results = []
for sample in test_dataset:
    entities = await extract_entities_with_gpt4o(sample)
    gpt4o_results.append(entities)

# Step 4: 计算F1 Score
evaluator = EntityExtractionEvaluator()
f1_score = evaluator.compare(
    predictions=qwen_results,
    ground_truth=gpt4o_results
)

print(f"Qwen2.5质量: {f1_score * 100:.1f}%（基线: gpt-4o 100%）")
# 验收标准: F1 Score ≥ 0.85 (85%)

# Step 5: 分析质量差距
if f1_score < 0.85:
    quality_report = evaluator.generate_error_analysis()
    print(f"质量问题分析：\n{quality_report}")
    # 常见问题：
    # - 实体边界识别不准确（+Few-shot examples可改善）
    # - 关系类型分类错误（+Fine-tuning可改善）
    # - 中文专业术语理解偏差（+领域词典可改善）
```

**成本监控集成**:

```python
# ✅ Verified from config/graphrag_cost_control.json
import json
from graphrag.cost_tracker import CostTracker

# 加载成本控制配置
with open("config/graphrag_cost_control.json", "r") as f:
    config = json.load(f)

# 初始化成本追踪器
cost_tracker = CostTracker(
    budget_limit=config["cost_monitoring"]["budget"]["monthly_limit_usd"],
    warning_threshold=config["cost_monitoring"]["budget"]["warning_threshold_percent"],
    critical_threshold=config["cost_monitoring"]["budget"]["critical_threshold_percent"]
)

# 集成到HybridLLMProvider
hybrid_llm = HybridLLMProvider(
    local_ratio=config["llm_providers"]["hybrid"]["local_ratio"],
    cost_tracker=cost_tracker
)

# 定期检查成本状态
monthly_cost = cost_tracker.get_monthly_cost()
if monthly_cost >= config["cost_monitoring"]["alerts"]["critical"]["threshold_usd"]:
    # 成本超标：切换为100%本地模式
    hybrid_llm.local_ratio = 1.0
    send_alert(
        recipients=config["cost_monitoring"]["alerts"]["critical"]["recipients"],
        message=f"GraphRAG成本超标（${monthly_cost}），已切换为100%本地模式"
    )
```

**故障排查**:

| 问题 | 症状 | 解决方案 |
|------|------|---------|
| **VRAM不足** | `CUDA out of memory` | 1. 降低`OLLAMA_NUM_PARALLEL`<br>2. 使用量化模型（qwen2.5:14b-instruct-q4_0）<br>3. 增加GPU显存或使用CPU推理 |
| **推理速度慢** | P95延迟>10秒 | 1. 检查GPU利用率（nvidia-smi）<br>2. 减少并发请求数<br>3. 优化prompt长度（<2000 tokens） |
| **质量不达标** | F1 Score < 85% | 1. 添加Few-shot examples到prompt<br>2. 微调Qwen2.5模型（需要训练数据）<br>3. 提高API比例（10%→30%） |
| **API降级率高** | 降级率>10% | 1. 检查Ollama服务状态（ollama ps）<br>2. 增加local_timeout（8秒→12秒）<br>3. 重启Ollama服务 |
| **成本超标** | 月成本>$80 | 1. 检查API调用日志（cost_tracker.get_api_log()）<br>2. 降低API比例（10%→5%）<br>3. 切换为100%本地模式 |

**生产部署检查清单**:

- [ ] **硬件**: RTX 4090或同等GPU已安装并正常工作
- [ ] **Ollama**: 服务已启动（ollama ps显示qwen2.5:14b-instruct）
- [ ] **质量验证**: F1 Score ≥ 85%（100个样本测试）
- [ ] **性能验证**: P95延迟 ≤ 8秒（10次推理测试）
- [ ] **成本监控**: CostTracker已集成，告警邮件配置正确
- [ ] **降级机制**: API降级率 < 5%（7天监控）
- [ ] **配置文件**: `config/graphrag_cost_control.json`已部署
- [ ] **健康检查**: Ollama服务监控已启用（每分钟检查）
- [ ] **备份方案**: API密钥已配置，降级可用
- [ ] **文档**: 运维文档已创建（`docs/operations/graphrag-local-model-deployment.md`）

**参考资料**:
- **Ollama官方文档**: https://ollama.com/docs
- **Qwen2.5模型卡**: https://ollama.com/library/qwen2.5:14b-instruct
- **ADR-001**: 本地模型vs API技术决策（`docs/architecture/ADR-001-local-model-vs-api.md`）
- **Story GraphRAG.2**: 本地模型集成（`docs/stories/graphrag-2-local-model-integration.story.md`）
- **Story GraphRAG.5**: 性能优化与成本监控（`docs/stories/graphrag-5-performance-cost.story.md`）

---

### 10.8 集成测试

#### 10.8.1 端到端测试

```python
@pytest.mark.asyncio
async def test_agentic_rag_end_to_end():
    """
    测试Agentic RAG完整流程
    """
    # Setup
    canvas_path = "test_data/离散数学-测试.canvas"
    config = create_langgraph_config(
        canvas_path=canvas_path,
        user_id="test_user",
        session_id=str(uuid.uuid4())
    )

    # Execute
    result = await generate_review_canvas_with_agentic_rag(
        canvas_path=canvas_path,
        config=config
    )

    # Assertions
    assert result["questions_count"] >= 5, "至少生成5个检验问题"
    assert result["questions_count"] <= 10, "最多生成10个检验问题"
    assert result["document_quality_score"] >= 0.5, "文档质量应≥0.5"
    assert os.path.exists(result["review_canvas_path"]), "检验白板文件应存在"

    # 验证问题权重
    questions = read_verification_questions_from_canvas(result["review_canvas_path"])
    temporal_questions = [
        q for q in questions
        if "temporal" in q.get("data_sources", [])
    ]
    assert len(temporal_questions) / len(questions) >= 0.6, "至少60%问题来自temporal(历史薄弱点)"
```

#### 10.8.2 性能基准测试

```python
@pytest.mark.performance
async def test_agentic_rag_performance():
    """
    测试Agentic RAG性能指标
    """
    canvas_path = "test_data/离散数学-测试.canvas"
    config = create_langgraph_config(canvas_path, "test_user", str(uuid.uuid4()))

    # 测试端到端延迟
    start_time = time.time()
    result = await generate_review_canvas_with_agentic_rag(canvas_path, config)
    end_to_end_latency = time.time() - start_time

    assert end_to_end_latency < 5.0, f"端到端延迟应<5秒, 实际: {end_to_end_latency:.2f}秒"

    # 测试工具调用延迟
    tool_latencies = extract_tool_latencies_from_state(result)
    for tool_name, latency in tool_latencies.items():
        assert latency < 1.0, f"{tool_name}延迟应<1秒, 实际: {latency:.2f}秒"
```

---

### 10.9 故障处理与降级策略

#### 10.9.1 工具调用失败处理

```python
async def graphiti_hybrid_search_tool_with_fallback(
    query: str,
    canvas_context: dict
) -> List[Dict]:
    """
    带降级策略的Graphiti检索
    """
    try:
        # 尝试hybrid_search
        return await graphiti_hybrid_search_tool(query, canvas_context)
    except Exception as e:
        logger.error(f"Graphiti hybrid search failed: {e}")

        # 降级策略1: 使用纯语义搜索(semantic_only模式)
        try:
            return await graphiti.search(
                query=query,
                search_mode="semantic_only",
                num_results=20
            )
        except Exception as e2:
            logger.error(f"Graphiti semantic search failed: {e2}")

            # 降级策略2: 返回空结果,让其他工具补偿
            return []
```

#### 10.9.2 文档质量不足处理

```python
def grade_documents_route(state: AgenticRAGState) -> str:
    quality_score = state.get("document_quality_score", 0.0)
    attempts = state.get("retrieval_attempts", 0)

    # 如果重试3次仍然质量不足,使用降级策略
    if attempts >= 3 and quality_score < 0.5:
        logger.warning(
            f"Document quality still low after {attempts} attempts: {quality_score:.2f}"
        )

        # 降级策略: 使用Canvas本身的红/紫节点文本作为fallback
        if not state.get("retrieved_documents"):
            state["retrieved_documents"] = generate_fallback_documents_from_canvas(
                state["canvas_context"]
            )

        return "generate"

    if quality_score >= 0.5:
        return "generate"

    return "rewrite"
```

---

### 10.10 监控与日志

#### 10.10.1 关键指标监控

```python
from prometheus_client import Histogram, Counter, Gauge

# Agentic RAG性能指标
agentic_rag_latency = Histogram(
    'agentic_rag_latency_seconds',
    'Agentic RAG end-to-end latency',
    ['canvas_file']
)

# 工具调用统计
tool_invocation_count = Counter(
    'agentic_rag_tool_invocations_total',
    'Total tool invocations',
    ['tool_name', 'status']  # status: success/failure
)

# 文档质量分布
document_quality_distribution = Histogram(
    'agentic_rag_document_quality_score',
    'Document quality score distribution',
    buckets=[0.0, 0.3, 0.5, 0.7, 0.9, 1.0]
)

# 查询重写次数
query_rewrite_count = Counter(
    'agentic_rag_query_rewrites_total',
    'Total query rewrites',
    ['canvas_file']
)
```

#### 10.10.2 结构化日志

```python
import structlog

logger = structlog.get_logger()

# 记录Agentic RAG执行
logger.info(
    "agentic_rag_started",
    canvas_file=canvas_path,
    session_id=config["configurable"]["session_id"],
    red_nodes_count=len(canvas_context["red_nodes"]),
    purple_nodes_count=len(canvas_context["purple_nodes"])
)

# 记录工具调用
logger.info(
    "tool_invoked",
    tool_name="graphiti_hybrid_search_tool",
    query=query[:100],
    max_results=20,
    rerank_strategy="rrf"
)

# 记录文档质量评分
logger.info(
    "documents_graded",
    quality_score=quality_score,
    quality_issues=quality_issues,
    retrieved_docs_count=len(retrieved_docs)
)

# 记录查询重写
logger.warning(
    "query_rewritten",
    original_query=original_query[:100],
    new_query=new_query[:100],
    attempt=retrieval_attempts
)
```

---

### 10.11 验收标准

- ✅ **AC 1**: Agentic RAG graph可成功编译并执行
- ✅ **AC 2**: 3个retrieval tools可正常调用并返回结果
- ✅ **AC 3**: 文档质量评分<0.5时自动触发查询重写
- ✅ **AC 4**: 端到端检验白板生成<5秒
- ✅ **AC 5**: 集成测试覆盖率≥90%
- ✅ **AC 6**: 生成的检验问题中≥60%来自历史薄弱点(temporal数据)
- ✅ **AC 7**: 工具调用失败时有降级策略,不阻塞主流程
- ✅ **AC 8**: 查询重写次数≤3,避免无限循环

---

## 📖 九、参考资料

### LangGraph官方文档

- LangGraph Checkpointer: `@langgraph` Skill
- StateGraph API: references/llms-full.md
- PostgresSaver配置: references/checkpointer.md

### 相关架构文档

- **Graphiti集成架构**: `GRAPHITI-KNOWLEDGE-GRAPH-INTEGRATION-ARCHITECTURE.md` Section 8.6
- **多Agent并发架构**: `MULTI-AGENT-CONCURRENT-ANALYSIS-SYSTEM-ARCHITECTURE.md` Section 7.3
- **PRD**: `CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md` Section 3.6

---

**文档版本**: v1.0
**最后更新**: 2025-11-11
**作者**: Claude Code
**状态**: 技术方案设计完成
