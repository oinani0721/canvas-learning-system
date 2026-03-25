# 数据模型文档

> 生成时间: 2026-03-24 | 扫描模式: exhaustive

## 1. Pydantic Models

> 位置: `backend/app/models/` (24 文件)

### 模型文件清单

| 文件 | 主要 Model | 说明 |
|------|-----------|------|
| `__init__.py` | 导出汇总 | 统一导出 CanvasResponse, NodeCreate, NodeRead, NodeUpdate, EdgeCreate, EdgeRead 等 |
| `schemas.py` | CanvasResponse, NodeCreate, NodeRead, NodeUpdate, EdgeCreate, EdgeRead, ErrorResponse | 核心 Canvas CRUD 模型 (41,906 行) |
| `common.py` | PaginatedResponse, StatusResponse | 通用响应模型 |
| `enums.py` | MasteryLevel, ReviewStatus, NodeType | 枚举定义 |
| `canvas_events.py` | LearningEvent, LearningEventType | 画布学习事件模型 |
| `edge_rationale.py` | EdgeRationale, RationaleWriteResult | 边推理依据模型 |
| `exam_models.py` | ExamSessionCreate, ExamSessionResponse, HintRequest, HintResponse, SkipRequest, SkipResponse | 考试模型 (21,531 行) |
| `session_models.py` | SessionCreate, SessionResponse | 会话管理模型 |
| `review_models.py` | ReviewSchedule, ReviewRecord, ReviewHistory | 复习调度模型 (23,490 行) |
| `mastery_models.py` | MasteryState, MasteryBatchResponse, GradeRequest | 掌握度模型 |
| `mastery_state.py` | MasteryStateDetail, CalibrationPoint | 掌握度详细状态 |
| `memory_schemas.py` | LearningEpisode, TemporalQueryResponse, ReviewSuggestion | 学习记忆模型 (17,119 行) |
| `metadata_models.py` | CanvasMetadata, IndexRequest, IndexStatus | 元数据与索引模型 |
| `multimodal_schemas.py` | MultimodalContent, MediaType, MultimodalMetadata | 多模态内容模型 (15,486 行) |
| `intelligent_parallel_models.py` | ParallelSession, AgentResult, WSEvent | 智能并行处理模型 (25,535 行) |
| `agent_routing_models.py` | AgentRoute, RoutingDecision | Agent 路由模型 |
| `qa_models.py` | QAMetrics, ExtractionRecord | QA 质量指标模型 |
| `recommendation_models.py` | RecommendationResponse, DismissedPairsRequest | 关系推荐模型 |
| `rollback.py` | OperationRecord, Snapshot, RollbackRequest | 回滚模型 (10,901 行) |
| `subject_models.py` | Subject, SubjectCreate, SubjectUpdate | 学科管理模型 |
| `sync_models.py` | SyncBatchRequest, SyncResult | 数据同步模型 |

## 2. Neo4j 节点类型

> 客户端: `backend/app/clients/neo4j_client.py`
> 实体定义: `backend/app/graphiti/entity_types.py`

### 核心节点类型 (Label)

| 节点类型 | 主要属性 | 说明 |
|----------|---------|------|
| `Canvas` | path, name | 画布文件，对应一个 .canvas 文件 |
| `Node` | id, type, text, color, x, y, width, height | 画布中的知识节点 |
| `Concept` | name | 概念实体，从节点内容中提取 |
| `User` | id | 用户实体 |
| `Episode` | id, timestamp, event_type, score, duration | 学习事件记录 |
| `LearningNode` | (与 Node 类似) | 包含 HAS_CONCEPT 关系的学习节点 |

### Graphiti 实体类型 (Pydantic Schema)

| 实体 | 主要字段 | 说明 |
|------|---------|------|
| `LearningTip` | tip_id, content, title, tags, node_id, source_timestamp | 用户标注的学习提示 |
| `Misconception` | misconception_id, error_type, description, context, remedy_strategy, node_id | Agent 检测的理解错误 (4 类分类) |

### 错误类型枚举 (ErrorType)

| 类型 | 中文 | 对应补救策略 |
|------|------|------------|
| `problem_framing` | 破题错误 | 同结构新题练习 |
| `reasoning_fallacy` | 推理谬误 | 找错练习 + 反例构造 |
| `knowledge_gap` | 知识点缺失 | 回退到定义题 |
| `superficial` | 似懂非懂 | 辨析题 + 迁移应用题 |

## 3. Neo4j 关系类型

### Canvas 结构关系

| 关系类型 | 方向 | 说明 |
|----------|------|------|
| `CONTAINS_NODE` | Canvas -> Node | 画布包含节点 |
| `CONNECTS_TO` | Node -> Node | 节点之间的边连接 (edge_id 属性) |
| `HAS_CONCEPT` | LearningNode -> Concept | 节点关联的概念 |
| `CONTAINS` | Canvas -> LearningNode | 画布包含学习节点 |

### 学习关系

| 关系类型 | 方向 | 说明 |
|----------|------|------|
| `LEARNED` | User -> Concept | 用户学习过的概念 (含 mastery, updated_at 属性) |
| `SCORED` | Episode -> (评分数据) | 学习事件的评分记录 (grade, score 属性) |

### 跨画布关系

| 关系类型 | 方向 | 说明 |
|----------|------|------|
| `ASSOCIATED_WITH` | Canvas -> Canvas | 跨画布关联 (association_id 属性) |

### 知识关系 (Graphiti/Suggestion)

| 关系类型 | 方向 | 中文标签 | 说明 |
|----------|------|---------|------|
| `HAS_TIP` | ConceptNode -> LearningTip | - | 概念的学习提示 |
| `HAS_MISCONCEPTION` | ConceptNode -> Misconception | - | 概念的理解错误 |
| `IS_PREREQUISITE` | Node -> Node | 是前置知识 | 前置知识关系 |
| `IS_APPLICATION` | Node -> Node | 是应用案例 | 概念的应用场景 |
| `CONTRASTS_WITH` | Node -> Node | 是对比概念 | 对比/辨析关系 |
| `IS_SUBCONCEPT` | Node -> Node | 是子概念 | 父子概念关系 |
| `SUPPLEMENTS` | Node -> Node | 是补充说明 | 补充/扩展关系 |

## 4. LanceDB 集合

> 服务: `backend/app/services/lancedb_index_service.py`
> 存储路径: `data/lancedb/` (本地文件)

### 集合配置

| 集合名 | 配置项 | Embedding | 维度 | 说明 |
|--------|--------|-----------|------|------|
| `canvas_nodes` | LANCEDB_INDEX_TABLE_NAME | bge-m3 | 1024 | Canvas 节点向量索引，用于语义检索 |

说明：
- 集合名通过 `settings.LANCEDB_INDEX_TABLE_NAME` 配置，默认值为 `canvas_nodes`
- Vault 笔记和多模态内容的检索通过 `src/agentic_rag/` 管道中的 LanceDB 检索器实现
- Embedding 使用 Ollama 本地部署的 bge-m3 模型 (中英双语, 1024 维向量)

## 5. 前端数据模型 (Dexie/IndexedDB)

> 文件: `frontend/src/services/dexie-db.ts`

### Dexie 表结构

| 表名 | 主要字段 | 说明 |
|------|---------|------|
| `boards` | id, name, filePath, createdAt, updatedAt | 画布列表 |
| `nodes` | id, canvasId, type, title, content, x, y, width, height, color, masteryStatus, effectiveProficiency, indexStatus, imageData | 画布节点 |
| `edges` | id, canvasId, fromNode, toNode, label, fromSide, toSide | 画布边 |
| `messages` | id, boardId, role, content, timestamp, toolCalls | 对话消息 |
| `sync_outbox` | id, table, recordId, action, payload, createdAt | 同步队列 (Outbox 模式) |
