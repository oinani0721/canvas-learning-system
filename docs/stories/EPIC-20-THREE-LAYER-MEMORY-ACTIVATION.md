> **DEPRECATED** - 此Epic已合并到 [Epic 30: Memory System Complete Activation](../epics/EPIC-30-MEMORY-SYSTEM-COMPLETE-ACTIVATION.md)
>
> 合并日期: 2026-01-15 | 请参考Epic 30获取最新实施计划

---

# Epic 20: 三层记忆系统触发时机与冲突避免 - Brownfield Enhancement

## Epic Goal

正式启用 Canvas Learning System 的三层记忆系统（Temporal/Graphiti/Semantic），明确每个 Canvas 操作的记忆触发时机，并确保与 LangGraph Checkpointer 的存储隔离。

---

## Epic Description

### Existing System Context

- **当前相关功能**: Canvas Learning System 已实现三层记忆架构的 95% 代码，但核心触发节点未启用
- **技术栈**: FastAPI + LangGraph + Neo4j(JSON模拟) + SQLite + LanceDB
- **集成点**:
  - `src/agentic_rag/state_graph.py` - RAG 图编译
  - `backend/app/services/memory_service.py` - 记忆服务 API
  - `backend/app/api/v1/endpoints/canvas.py` - Canvas CRUD 端点

### Enhancement Details

**What's being added/changed**:
1. 升级 Neo4j 客户端从 JSON 模拟到真实数据库连接
2. 为 Canvas CRUD 操作添加记忆写入触发
3. 在 RAG 状态图中启用 `update_learning_behavior` 节点
4. 创建"记忆触发时机映射表"文档

**How it integrates**:
- 增量启用：先 Layer 2 (Graphiti)，验证后再 Layer 1 (Temporal)
- 保持 LangGraph Checkpointer 与三层记忆的存储隔离
- 异步非阻塞写入，不影响用户响应

**Success criteria**:
- [ ] Canvas 操作正确触发对应记忆层写入
- [ ] Neo4j 数据库连接稳定，有回退机制
- [ ] FSRS 学习行为更新正常工作
- [ ] 记忆触发时机映射表完整且准确

---

## Stories

### Story 20.1: Neo4j 连接升级 (Layer 2)

**标题**: 将 Neo4j 客户端从 JSON 模拟升级到真实数据库连接

**描述**: 当前 `neo4j_client.py` 使用 JSON 文件模拟 Neo4j 存储。需要升级为真实的 Neo4j 驱动连接，同时保留 JSON 作为回退机制。

**验收标准**:
- [ ] AC 1.1: Neo4j 配置项添加到 `backend/app/core/config.py`（NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD）
- [ ] AC 1.2: Neo4j 客户端成功连接真实数据库
- [ ] AC 1.3: 数据迁移脚本创建并测试（清理损坏的 Unicode 数据）
- [ ] AC 1.4: 健康检查端点返回连接状态
- [ ] AC 1.5: 连接失败时自动回退到 JSON 存储

**关键文件**:
| 文件 | 修改类型 |
|------|----------|
| `backend/app/core/config.py` | 修改 |
| `backend/app/clients/neo4j_client.py` | 修改 |
| `scripts/migrate_neo4j_data.py` | 新建 |
| `backend/app/api/v1/endpoints/health.py` | 修改 |

---

### Story 20.2: Canvas CRUD 记忆触发 (Layer 2)

**标题**: 为 Canvas 节点 CRUD 操作添加记忆写入触发

**描述**: 当前 `canvas.py` 的 CRUD 操作为 Placeholder 实现，不会触发任何记忆写入。需要连接到 `CanvasService` 并在每个操作后触发 `record_learning_event()`。

**验收标准**:
- [ ] AC 2.1: `add_node` 触发 `record_learning_event(event_type="node_created")`
- [ ] AC 2.2: `update_node` 触发 `record_learning_event(event_type="node_updated")`
- [ ] AC 2.3: `delete_node` 触发 `record_learning_event(event_type="node_deleted")`
- [ ] AC 2.4: 代码注释标注写入哪层记忆（`# [Layer 2: Graphiti Memory]`）
- [ ] AC 2.5: 记忆写入异步执行，不阻塞用户响应

**记忆触发时机映射表**:

| Canvas 操作 | 记忆层级 | 触发函数 | 触发时机 |
|-------------|----------|----------|----------|
| 节点创建 (用户回答) | Layer 2 (Graphiti) | `record_learning_event(event_type="node_created")` | 节点写入 Canvas 后 |
| 节点更新 (颜色变更) | Layer 2 (Graphiti) | `record_learning_event(event_type="node_updated")` | 节点属性更新后 |
| 节点删除 | Layer 2 (Graphiti) | `record_learning_event(event_type="node_deleted")` | 节点从 Canvas 移除后 |
| 边创建 | Layer 2 (Graphiti) | `add_edge_relationship()` | 边连接建立后 |
| Agent 分析完成 | Layer 2 + Layer 1 | `record_learning_episode()` + `update_behavior()` | Agent 返回结果后 |

**关键文件**:
| 文件 | 修改类型 |
|------|----------|
| `backend/app/services/canvas_service.py` | 修改 |
| `backend/app/api/v1/endpoints/canvas.py` | 修改 |

---

### Story 20.3: Temporal Memory 节点启用 (Layer 1)

**标题**: 在 RAG 状态图中启用 `update_learning_behavior` 节点

**描述**: `update_learning_behavior()` 节点在 `nodes.py:800` 已定义但未添加到状态图。需要在 `state_graph.py` 中启用此节点，并在 `CanvasRAGState` 中添加必要的字段。

**验收标准**:
- [ ] AC 3.1: `CanvasRAGState` 包含时序记忆字段（session_id, current_concept, rating, weak_concepts, behavior_updated）
- [ ] AC 3.2: `update_learning_behavior` 节点添加到 RAG 图
- [ ] AC 3.3: `session_id` 在 RAG 查询开始时正确初始化（UUID）
- [ ] AC 3.4: 学习活动后 FSRS 卡片正确更新

**State Schema 添加**:
```python
# src/agentic_rag/state.py CanvasRAGState 新增字段:
session_id: Annotated[Optional[str], "学习会话ID，用于追踪"]
current_concept: Annotated[Optional[str], "当前学习的概念"]
rating: Annotated[Optional[int], "用户评分 (1=Again, 2=Hard, 3=Good, 4=Easy)"]
weak_concepts: Annotated[List[Dict[str, Any]], "FSRS 识别的薄弱概念"]
behavior_updated: Annotated[bool, "学习行为是否已更新"]
```

**关键文件**:
| 文件 | 修改类型 |
|------|----------|
| `src/agentic_rag/state.py` | 修改 |
| `src/agentic_rag/state_graph.py` | 修改 |
| `src/agentic_rag/nodes.py` | 修改（导出） |

---

## Compatibility Requirements

- [x] 现有 API 保持不变（仅添加新功能）
- [x] 数据库 schema 变更向后兼容（JSON 回退机制）
- [x] UI 变更遵循现有模式（无 UI 变更）
- [x] 性能影响最小化（异步非阻塞写入）

---

## Risk Mitigation

### Primary Risk: Neo4j 连接失败

**风险描述**: Neo4j 服务不可用或配置错误导致记忆系统无法工作

**缓解措施**:
1. 实现 JSON 存储作为回退机制
2. 添加连接健康检查端点
3. 设置连接超时（5秒）和重试（3次）

### Secondary Risk: 数据迁移损坏

**风险描述**: 现有 `neo4j_memory.json` 包含损坏的 Unicode 数据，迁移可能失败

**缓解措施**:
1. 迁移前创建备份
2. 实现数据清洗脚本
3. 支持回滚到备份

### Rollback Plan

如需回滚：
1. 在 `config.py` 中设置 `NEO4J_ENABLED=False`
2. 系统自动回退到 JSON 存储
3. 移除 `update_learning_behavior` 节点的边连接

---

## Definition of Done

- [ ] 所有 Story 完成，验收标准全部通过
- [ ] 现有功能通过回归测试验证
- [ ] 集成点正常工作（Neo4j、FSRS、Canvas CRUD）
- [ ] 文档更新：
  - [ ] PRD 包含"记忆触发时机映射表"
  - [ ] 代码注释标注写入哪层记忆
  - [ ] 隔离策略文档化
- [ ] 无现有功能回归

---

## Technical Notes

### 隔离策略：LangGraph Checkpointer vs 三层记忆

| 系统 | 用途 | 存储后端 | 生命周期 | 标识符 |
|------|------|----------|----------|--------|
| LangGraph Checkpointer | 工作流状态持久化 | SQLite (bmad.db) | 会话级 | thread_id |
| Layer 1 (Temporal) | FSRS 学习行为 | SQLite (learning_behavior.db) | 永久 | user_id + concept |
| Layer 2 (Graphiti) | 知识图谱关系 | Neo4j | 永久 | episode_id |
| Layer 3 (Semantic) | 向量检索 | LanceDB | 永久 | document_id |

**隔离保证**: 两个系统使用完全不同的存储路径和连接实例，无冲突风险。

### 数据流示意图

```
用户操作
    │
    ▼
┌─────────────────┐
│ Canvas CRUD API │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐  ┌────────────┐
│Canvas │  │MemoryService│
│Service│  │(Background) │
└───────┘  └─────┬──────┘
                 │
         ┌───────┼───────┐
         ▼       ▼       ▼
     ┌──────┐┌──────┐┌──────┐
     │Neo4j ││SQLite││LanceDB│
     │(L2)  ││(L1)  ││(L3)   │
     └──────┘└──────┘└──────┘
```

---

## Story Manager Handoff

**Story Manager Handoff:**

"Please develop detailed user stories for this brownfield epic. Key considerations:

- This is an enhancement to an existing system running **FastAPI + LangGraph + Neo4j + SQLite + LanceDB**
- Integration points: `state_graph.py`, `memory_service.py`, `canvas.py`, `neo4j_client.py`
- Existing patterns to follow: 异步 BackgroundTasks 记忆写入、MCP 工具回退模式
- Critical compatibility requirements: JSON 回退机制、现有 API 不变
- Each story must include verification that existing functionality remains intact

The epic should maintain system integrity while delivering **正式启用三层记忆系统，明确触发时机，确保存储隔离**."

---

## References

- 调研报告: `.claude/plans/effervescent-soaring-dragonfly.md`
- 现有记忆服务: `backend/app/services/memory_service.py`
- RAG 状态图: `src/agentic_rag/state_graph.py`
- Neo4j 客户端: `backend/app/clients/neo4j_client.py`
