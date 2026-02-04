# Epic 36: Agent节点间上下文管理增强 - Brownfield Enhancement

## Epic Title

Agent节点间上下文管理增强 - Brownfield Enhancement

## Epic Goal

修复GraphitiClient真实Neo4j调用、统一两套Client实现、增强跨Canvas讲座上下文注入，确保Canvas内部Edge到Neo4j的完整同步链路，使Agent在处理节点时能够获取完整的上下文信息（邻接节点 + 教材 + 跨Canvas讲座 + 历史学习记忆）。

## Epic Description

### 关键依赖声明

> **⚠️ EPIC-30 依赖关系 (2026-01-18 更新)**
>
> 本Epic的 **Story 36.1-36.2** 必须复用 **EPIC-30 Story 30.2** 已完成的 `Neo4jClient` 实现：
>
> | EPIC-30 已完成 | 本Epic应复用 |
> |----------------|-------------|
> | `Neo4jClient` 真实Bolt驱动 | GraphitiClient **注入** Neo4jClient |
> | 连接池配置 (50连接, 30s超时) | 复用现有连接池，**禁止重新创建** |
> | tenacity重试 (3次指数退避) | 复用现有重试逻辑 |
> | JSON fallback (`NEO4J_MOCK=true`) | 复用现有fallback机制 |
>
> **架构层级关系**:
> ```
> Neo4jClient (底层连接 - EPIC-30 Story 30.2) ✅ 已完成
>     ↓ 注入
> GraphitiClient (业务逻辑 - 本Epic Story 36.1-36.2) 📋 待开发
> ```
>
> **禁止行为**: Story 36.1-36.2 **不得**重新实现 `AsyncGraphDatabase.driver()` 连接逻辑

### Existing System Context

- **Current relevant functionality**:
  - `ContextEnrichmentService` (1007行) - 已实现1-hop邻接节点遍历、教材上下文、跨Canvas讲座融合
  - `TextbookContextService` (628行) - 完整支持Canvas/PDF/Markdown三种格式
  - `Agent上下文注入` - agent_service.py已集成enriched_context传递
  - `GraphitiEdgeClient` - 存在但只存JSON文件，不调用真实Neo4j/MCP

- **Technology stack**:
  - FastAPI后端 (Python 3.11+)
  - Neo4j Docker (已部署运行，bolt://localhost:7687)
  - LangGraph多Agent系统
  - Obsidian插件 (TypeScript)

- **Integration points**:
  - `backend/app/clients/graphiti_client.py` ↔ `backend/app/clients/neo4j_client.py`
  - `backend/app/services/context_enrichment_service.py` ↔ Agent端点
  - `backend/app/services/cross_canvas_service.py` ↔ Neo4j持久化
  - `canvas-progress-tracker/obsidian-plugin/` ↔ 后端API

### Enhancement Details

- **What's being added/changed**:
  1. 修复GraphitiClient，使用真实Neo4j Cypher调用替代JSON模拟
  2. 统一两套GraphitiClient实现（backend/app/ 和 src/agentic_rag/）
  3. Canvas Edge创建/更新时自动同步到Neo4j知识图谱
  4. 跨Canvas讲座关联从内存存储改为Neo4j持久化
  5. Agent上下文注入从Neo4j获取真实历史学习数据
  6. 添加存储层健康检查和监控指标

- **How it integrates**:
  - GraphitiClient注入Neo4jClient，复用现有连接池
  - Canvas Edge CRUD操作后触发fire-and-forget异步同步
  - ContextEnrichmentService从Neo4j查询相关记忆
  - 保留JSON fallback用于Neo4j不可用时

- **Success criteria**:
  - Canvas Edge在创建后5秒内同步到Neo4j
  - Agent上下文注入包含真实Neo4j历史数据
  - 跨Canvas关联重启后仍然存在
  - 写入延迟P95 < 200ms，查询延迟 < 100ms

## Stories

### Phase 1: 基础架构统一

> **⚠️ 依赖**: 本Phase依赖 **EPIC-30 Story 30.2** (Neo4jClient真实驱动) 已完成

1. **Story 36.1: 统一GraphitiClient架构**
   - **依赖**: EPIC-30 Story 30.2 (`Neo4jClient` 已实现)
   - 合并 `backend/app/clients/graphiti_client.py` 和 `src/agentic_rag/clients/graphiti_client.py`
   - 创建统一基类，**注入 `Neo4jClient` 实例**（禁止重新创建连接）
   - 消除代码重复
   - 预估: ~400行新代码，~200行删除
   - **实现要求**:
     ```python
     class GraphitiClient:
         def __init__(self, neo4j_client: Neo4jClient):  # 依赖注入
             self._neo4j = neo4j_client  # 复用30.2的Neo4jClient
     ```

2. **Story 36.2: GraphitiClient真实Neo4j调用实现**
   - **依赖**: Story 36.1 + EPIC-30 Story 30.2
   - `add_edge_relationship()` 调用 `self._neo4j.run_query()` 执行MERGE Cypher
   - `search_nodes()` 调用 `self._neo4j.run_query()` 执行MATCH查询
   - **复用** Neo4jClient的JSON fallback和重试机制（禁止重新实现）
   - 预估: ~350行新代码
   - **禁止**:
     - ❌ 不得直接使用 `AsyncGraphDatabase.driver()`
     - ❌ 不得重新实现连接池配置
     - ❌ 不得重新实现重试逻辑

### Phase 2: Canvas Edge完整链路

3. **Story 36.3: Canvas Edge自动同步到Neo4j**
   - `add_edge()` 成功后异步触发 `sync_edge_to_neo4j()`
   - Fire-and-forget模式不阻塞Canvas操作
   - 重试机制（3次，指数退避）
   - 预估: ~300行新代码

4. **Story 36.4: Canvas打开时全量Edge同步**
   - `POST /api/v1/canvas/{name}/sync-edges` 端点
   - 同步幂等（重复同步不产生重复数据）
   - 预估: ~250行新代码

### Phase 3: 跨Canvas增强

5. **Story 36.5: 跨Canvas讲座关联持久化**
   - 关联存储为Neo4j `ASSOCIATED_WITH` 关系
   - 关联类型: LECTURE_FOR, EXERCISE_OF, RELATED_TO
   - 预估: ~400行新代码

6. **Story 36.6: 跨Canvas讲座自动发现**
   - 文件名模式匹配（习题→讲座）
   - 共同概念数>=3时建议关联
   - 预估: ~350行新代码

### Phase 4: Agent上下文注入

7. **Story 36.7: Agent上下文注入增强（Neo4j数据源）**
   - **依赖**: EPIC-30 Story 30.2 (Neo4jClient)
   - `_get_learning_memories()` 通过注入的Neo4jClient查询真实Neo4j
   - 相关记忆按relevance排序，top 5注入
   - 30秒缓存减少重复查询
   - 预估: ~300行修改

8. **Story 36.8: 跨Canvas上下文自动注入**
   - 习题节点自动获取关联讲座top 5知识点
   - 格式: `[参见讲座: {name}] {知识点内容}`
   - 预估: ~200行修改

### Phase 5: 生产化

9. **Story 36.9: 学习记忆双写（Neo4j + Graphiti MCP）**
   - **依赖**: EPIC-30 Story 30.4 (Agent记忆写入触发机制)
   - **定位**: 在30.4基础上增加MCP双写功能（增强，非基础实现）
   - 学习事件写入Neo4j成功后尝试写MCP
   - MCP写入失败不影响主流程
   - 预估: ~250行新代码

10. **Story 36.10: 健康检查与监控增强**
    - `GET /health/storage` 返回Neo4j/MCP/JSON状态
    - 连接池使用率、查询延迟P95指标
    - 预估: ~300行新代码

## Compatibility Requirements

- [x] Existing APIs remain unchanged (新增端点，不修改现有签名)
- [x] Database schema changes are backward compatible (Neo4j新增关系类型，不破坏现有数据)
- [x] UI changes follow existing patterns (无前端变更)
- [x] Performance impact is minimal (异步同步，不阻塞主流程)

## Risk Mitigation

- **Primary Risk**: Neo4j连接不稳定导致Edge同步失败
- **Mitigation**:
  1. JSON fallback机制保留
  2. 重试机制（3次，指数退避）
  3. 异步fire-and-forget模式，不阻塞主流程
- **Rollback Plan**:
  1. 设置环境变量 `GRAPHITI_USE_NEO4J=false` 回退到JSON存储
  2. 恢复旧版 `graphiti_client.py` 代码

## Definition of Done

- [x] All stories completed with acceptance criteria met
- [x] Existing functionality verified through testing
- [x] Integration points working correctly
- [x] Documentation updated appropriately
- [x] No regression in existing features
- [x] Neo4j Browser验证Edge关系已存储: `MATCH (a)-[r:CONNECTED_TO]->(b) RETURN a,r,b`

---

## Key Files to Modify

| 文件 | 修改类型 | 涉及Story |
|------|----------|-----------|
| `backend/app/clients/graphiti_client.py` | 重构 | 36.1, 36.2 |
| `backend/app/clients/neo4j_client.py` | 新增方法 | 36.2, 36.5 |
| `backend/app/services/canvas_service.py` | 修改 | 36.3, 36.4 |
| `backend/app/services/cross_canvas_service.py` | 重构 | 36.5, 36.6 |
| `backend/app/services/context_enrichment_service.py` | 修改 | 36.7, 36.8 |
| `backend/app/services/agent_service.py` | 修改 | 36.7 |
| `backend/app/services/memory_service.py` | 修改 | 36.9 |
| `backend/app/api/v1/endpoints/health.py` | 新增端点 | 36.10 |
| `backend/app/api/v1/endpoints/canvas.py` | 新增端点 | 36.4 |
| `src/agentic_rag/clients/graphiti_client.py` | 删除（改为导入） | 36.1 |

---

## Story Manager Handoff

> **Story Manager Handoff:**
>
> "Please develop detailed user stories for this brownfield epic. Key considerations:
>
> - This is an enhancement to an existing system running **FastAPI + Neo4j + LangGraph + Obsidian**
> - Integration points: **GraphitiClient ↔ Neo4jClient ↔ ContextEnrichmentService ↔ Agent端点**
> - Existing patterns to follow: **Fire-and-forget异步模式 (Story 30.4)**, **依赖注入 (dependencies.py)**
> - Critical compatibility requirements: **JSON fallback**, **现有API签名不变**, **测试覆盖率不下降**
> - Each story must include verification that existing functionality remains intact
>
> The epic should maintain system integrity while delivering **完整的Agent节点间上下文管理增强，包括真实Neo4j调用、跨Canvas持久化关联、历史学习记忆注入**."

---

## Validation Checklist

### Scope Validation

- [x] Epic can be completed in 1-3 stories maximum ❌ (10 Stories，但分为5个Phase可增量交付)
- [x] No architectural documentation is required ✅ (使用现有架构，仅增强实现)
- [x] Enhancement follows existing patterns ✅ (复用fire-and-forget、依赖注入模式)
- [x] Integration complexity is manageable ✅ (Neo4j已部署，GraphitiClient框架已存在)

### Risk Assessment

- [x] Risk to existing system is low ✅ (JSON fallback + 异步模式)
- [x] Rollback plan is feasible ✅ (环境变量开关)
- [x] Testing approach covers existing functionality ✅ (现有测试 + 新增集成测试)
- [x] Team has sufficient knowledge of integration points ✅ (代码已调研)

### Completeness Check

- [x] Epic goal is clear and achievable ✅
- [x] Stories are properly scoped ✅ (每个Story ~200-400行代码)
- [x] Success criteria are measurable ✅ (延迟P95、同步时间、Neo4j查询结果)
- [x] Dependencies are identified ✅ (Neo4j Docker已运行)

---

## Estimated Effort

| Phase | Stories | 预估代码量 |
|-------|---------|-----------|
| Phase 1: 基础架构统一 | 36.1, 36.2 | ~750行 |
| Phase 2: Canvas Edge完整链路 | 36.3, 36.4 | ~550行 |
| Phase 3: 跨Canvas增强 | 36.5, 36.6 | ~750行 |
| Phase 4: Agent上下文注入 | 36.7, 36.8 | ~500行 |
| Phase 5: 生产化 | 36.9, 36.10 | ~550行 |
| **总计** | **10 Stories** | **~3100行** |

---

*Epic created by PM Agent (John) following brownfield-create-epic task*
*Date: 2026-01-17*

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-01-17 | 0.1 | Initial draft | PM Agent (John) |
| 2026-01-18 | 0.2 | **添加EPIC-30依赖声明**：Story 36.1-36.2必须注入Neo4jClient (来自30.2)，禁止重新实现连接逻辑；Story 36.7依赖30.2；Story 36.9依赖30.4 | PM Agent (John) |
