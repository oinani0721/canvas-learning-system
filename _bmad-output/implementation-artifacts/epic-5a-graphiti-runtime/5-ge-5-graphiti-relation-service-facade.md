---
story_id: "5-ge-5-graphiti-relation-service-facade"
epic_id: "5a-graphiti-runtime"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P0"
estimate_hours: 3
depends_on: ["5-ge-1", "5-ge-2", "5-ge-3"]
blocks: []
sprint: "Sprint 2 v3 (Day 10 AM, Session D)"
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
chatgpt_required: "#5 GraphitiRelationService facade + search_relation_facts"
supersedes: ["LITE-5-7 路线 B 直调 search_facts 方案", "LITE-4-3 路线 4 直调 search_facts 方案"]
decision_trace: "2026-05-26 ChatGPT Deep Research 缺口 3"
---

# Story 5-ge-5: GraphitiRelationService facade + search_relation_facts + search_error_communities

Status: ready-for-dev

## Story

As a **出题 / 评分 / 复盘子系统**,
I want **一个统一的 `GraphitiRelationService` facade, 不直接调 `graphiti.search_()`, 而是用产品语义级 API (`search_relation_facts` / `search_error_communities`)**,
So that 上层产品语义不依赖 Graphiti API surface 演进, 切换底层 (search_facts vs search_(EDGE_HYBRID_SEARCH_RRF)) 不影响调用方.

## Acceptance Criteria

1. **Given** 新建 `backend/app/services/graphiti_relation_service.py` **When** module load **Then** 导出 `GraphitiRelationService` 类含 2 个公共方法

2. **Given** `search_relation_facts(query, group_id, edge_types=None, limit=8)` **When** 调用 **Then** 返回 `list[RelationFact]`:
   ```python
   @dataclass
   class RelationFact:
       edge_uuid: str
       source_node_id: str
       target_node_id: str
       edge_type: str
       fact: str
       valid_at: datetime
       invalid_at: datetime | None
       belief_key: str
       provenance_episode_ids: list[str]
   ```

3. **Given** 底层实现 **When** facade 调 **Then**:
   - **第一优先**: `graphiti.search_facts(query=..., group_id=..., max_results=limit)` (Graphiti v3 公开 API)
   - **fallback**: `graphiti.search_(query, config=EDGE_HYBRID_SEARCH_RRF)` (兼容旧版本)
   - 解析 edge results → 转 RelationFact dataclass

4. **Given** `search_error_communities(query, group_id, since_days=30, limit=5)` **When** 调用 **Then** 返回 `list[ErrorCommunity]`:
   ```python
   @dataclass
   class ErrorCommunity:
       community_uuid: str
       summary: str
       member_node_ids: list[str]
       dominant_error_type: str | None
       recurrence_count: int
       last_seen_at: datetime
   ```

5. **Given** 底层 community 查询 **When** facade 调 **Then**:
   - `graphiti.search_(query, config=COMMUNITY_HYBRID_SEARCH_RRF)` (默认)
   - 过滤 last_seen_at < since_days
   - 解析 community results → 转 ErrorCommunity

6. **Given** LITE-4-3 路线 4 改造 **When** `context_enrichment_service` 调用 **Then** 改为:
   ```python
   from app.services.graphiti_relation_service import GraphitiRelationService
   facts = await GraphitiRelationService.search_relation_facts(
       query=node_id, group_id=gid, limit=3
   )
   # 不再直接 search_memories / search_facts
   ```

7. **Given** LITE-5-7 路线 B 改造 **When** `ContextService.get_recent_context` 调用 **Then** 改为同上 (用 facade 而非直调)

8. **Given** Graphiti 不可用 **When** facade 调 **Then** 返回空 list + structlog warning, 不抛异常

9. **Given** 单元测试 **Then** 覆盖:
   - search_relation_facts 正常路径
   - search_facts fallback 到 search_ (mock graphiti version)
   - Graphiti down 降级
   - search_error_communities 含 since_days 过滤

## Tasks / Subtasks

- [ ] Task 1: GraphitiRelationService 类 (AC: #1, #2, #4)
  - [ ] 新建 `backend/app/services/graphiti_relation_service.py`
  - [ ] RelationFact + ErrorCommunity dataclass
- [ ] Task 2: search_relation_facts (AC: #3)
  - [ ] 先试 search_facts, fail 走 search_(EDGE_HYBRID_SEARCH_RRF) fallback
- [ ] Task 3: search_error_communities (AC: #5)
  - [ ] search_(COMMUNITY_HYBRID_SEARCH_RRF) + since_days 过滤
- [ ] Task 4: 接入 LITE-4-3 (AC: #6)
  - [ ] 改 `backend/app/services/context_enrichment_service.py` 路线 4 调用
- [ ] Task 5: 接入 LITE-5-7 (AC: #7)
  - [ ] 改 `backend/app/services/context_service.py` 路线 B 调用 (LITE-5-7 spec 内 service)
- [ ] Task 6: 降级 (AC: #8)
  - [ ] try/except + structlog warning
- [ ] Task 7: 单元测试 (AC: #9)
  - [ ] `backend/tests/unit/test_graphiti_relation_service.py`

## Dev Notes

### File Paths
- 新建: `backend/app/services/graphiti_relation_service.py`
- 改: `backend/app/services/context_enrichment_service.py` (LITE-4-3 路线 4)
- 改: `backend/app/services/context_service.py` (LITE-5-7 路线 B, 5-ge-1 依赖)

### Architecture

```
[ChatGPT 推荐架构, 屏蔽 Graphiti API surface 演进]

LITE-4-3 路线 4 (context_enrichment)
LITE-5-7 路线 B (context_service.get_recent_context)
评分复盘 (review_service)
    ↓ 调
GraphitiRelationService.search_relation_facts(query, group_id, limit)
    ↓
    ├─ 第一优先: graphiti.search_facts() (v3 API)
    └─ fallback: graphiti.search_(config=EDGE_HYBRID_SEARCH_RRF)
        ↓
    返回 list[RelationFact] (统一产品语义)
```

### References
- ChatGPT 报告 §Part 2 缺口 3 + §Part 5 (路由规则)
- Graphiti v3 公开 API 主要是 search recipes (ChatGPT 引用)
- Graphiti MCP README: search_nodes / search_facts 工具名

## Change Log

- 2026-05-26: spec 新建 (替代 LITE-5-7 路线 B + LITE-4-3 路线 4 直调方案)
