---
story_id: "5-ge-1-canvas-graph-episode-v1"
epic_id: "5-graphiti-era"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P0"
estimate_hours: 16
depends_on: ["INFRA-002"]
blocks: ["5-ge-2", "5-ge-3", "5-ge-5"]
sprint: "Sprint 2 v3 (Day 6-7, Session B)"
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
chatgpt_required: "#1 unified schema + #2 edge_type_map 透传"
supersedes: ["epic-1/1-16-callout-graphiti-hook.md (partial)", "epic-2/2-10-wikilink-graphiti-sync.md (partial)"]
decision_trace: "2026-05-26 ChatGPT Deep Research 缺口 1 + 议题 2"
---

# Story 5-ge-1: CanvasGraphEpisodeV1 统一事件 schema + edge_type_map 透传

Status: ready-for-dev

## Story

As a **Graphiti 写入子系统**,
I want **一套统一的 `CanvasGraphEpisodeV1` payload schema 让所有事件源 (callout/wikilink/calibration/error/recovery) 走同一 `add_episode` 写入口, 并把 `edge_type_map` 真传给 Graphiti**,
So that 未来 `search_facts("X 和 Y 的关系")` 能查到 wikilink 探索路径 + callout 上下文, 且 Graphiti custom ontology 真生效约束节点对 → 关系类型提取.

## Acceptance Criteria

1. **Given** 新建 `backend/app/graphiti/canvas_episode.py` **When** module load **Then** 导出 `CanvasGraphEpisodeV1` Pydantic model + `EVENT_TYPES` enum (7 类: wikilink_added/removed, callout_added/updated/removed, calibration_vote, error_marked)

2. **Given** event payload **When** validate by Pydantic **Then** 必含字段:
   ```python
   class CanvasGraphEpisodeV1(BaseModel):
       schema_version: Literal["CanvasGraphEpisodeV1"] = "CanvasGraphEpisodeV1"
       event_id: str  # deterministic SHA-256 of (vault_id + canvas_path + anchor + timestamp)
       event_type: EventType  # 7 enum
       occurred_at: datetime
       vault_id: str
       group_id: str  # vault:<vault_id>[:<subject>]
       canvas_path: str
       node_id: str
       source_node_id: str | None = None
       target_node_id: str | None = None
       relation_type: str | None = None  # prerequisite/depends_on/refines/extends/example_of/contradicts/related_to
       belief_key: str  # 见 5-ge-2 belief_key 规范
       callout: CalloutPayload | None = None
       context: ContextPayload  # source_board / path_trace / in_links / out_links
       narrative: str  # ⛔ 必填 — Graphiti search_facts 命中关键
   ```

3. **Given** 新建 `backend/app/graphiti/entity_types.py` 扩展 **When** module load **Then** 导出:
   ```python
   CANVAS_ENTITY_TYPES = {"CanvasNode": CanvasNode}
   CANVAS_EDGE_TYPES = {
       "Prerequisite": Prerequisite, "Elaborates": Elaborates,
       "Contrasts": Contrasts, "ExampleOf": ExampleOf,
       "Causes": Causes, "PartOf": PartOf, "RelatedTo": RelatedTo,
   }
   CANVAS_EDGE_TYPE_MAP = {
       ("CanvasNode", "CanvasNode"): list(CANVAS_EDGE_TYPES.keys())
   }
   ```

4. **Given** 改造 `backend/app/services/episode_worker.py` **When** `_call_add_episode(task)` **Then** 必须**新增传 `edge_type_map=CANVAS_EDGE_TYPE_MAP` 参数** (修复 line 550-560 漏传):
   ```python
   await self._graphiti.add_episode(
       name=f"{task.event_type}:{task.event_id}",
       episode_body=task.episode_body,
       source=EpisodeType.json,
       source_description=f"canvas:{task.event_type}",
       reference_time=task.occurred_at,
       group_id=sanitize_group_id_for_graphiti(task.group_id),
       entity_types=CANVAS_ENTITY_TYPES,
       edge_types=CANVAS_EDGE_TYPES,
       edge_type_map=CANVAS_EDGE_TYPE_MAP,  # ⛔ ChatGPT 必修 #2
   )
   ```

5. **Given** 4 个事件源 (callout / wikilink / calibration / error) **When** plugin POST event **Then** backend `POST /api/v1/event/canvas-graph` 接收 + validate by `CanvasGraphEpisodeV1` + 写入 `events_queue` (LanceDB unified table 替代分散 callout_events / wikilink_events / calibration_events)

6. **Given** `narrative` 字段 **When** generate **Then** 必须是自然语言句子, 含 wikilink 关系 + 探索路径. 示例:
   ```
   用户在 [递归白板] 中沿 [概览]→[递归定义]→[base case] 路径,
   对节点 [[recursion-base-case]] 写下 tip: "递归一定要先想 base case".
   该节点出链到 [回溯][树递归], 被 [递归总览][DFS] 反向引用.
   ```

7. **Given** 单元测试 `tests/unit/test_canvas_episode_v1.py` **When** pytest 跑 **Then** 覆盖:
   - 7 event_type × 各 1 用例 (schema 合法性)
   - edge_type_map 真传 (mock graphiti.add_episode 断言收到 edge_type_map)
   - narrative 字段必填 (空 → ValidationError)
   - sanitize_group_id_for_graphiti 真用 (`vault:cs_61b:recursion` → `vault__cs_61b__recursion`)

## Tasks / Subtasks

- [ ] Task 1: Pydantic schema 定义 (AC: #2)
  - [ ] 新建 `backend/app/graphiti/canvas_episode.py`
  - [ ] CanvasGraphEpisodeV1 + EventType enum + CalloutPayload + ContextPayload
- [ ] Task 2: entity_types 扩展 (AC: #3)
  - [ ] 改 `backend/app/graphiti/entity_types.py`
  - [ ] 加 CANVAS_ENTITY_TYPES + CANVAS_EDGE_TYPES (7 类 Pydantic) + CANVAS_EDGE_TYPE_MAP
- [ ] Task 3: episode_worker 改造 (AC: #4)
  - [ ] 改 `backend/app/services/episode_worker.py:550-560`
  - [ ] 加 edge_type_map 参数 + 改 episode_body 接受 CanvasGraphEpisodeV1
- [ ] Task 4: 统一 events_queue 表 (AC: #5)
  - [ ] 改 `backend/app/infra/lancedb_init.py` 加 `canvas_graph_events` 表
  - [ ] schema 含 CanvasGraphEpisodeV1 全字段
- [ ] Task 5: endpoint (AC: #5)
  - [ ] 新建 `backend/app/api/v1/endpoints/canvas_graph_event.py`
  - [ ] POST `/api/v1/event/canvas-graph` 接收 + validate + 写 queue
- [ ] Task 6: narrative 生成 helper (AC: #6)
  - [ ] 新建 `backend/app/graphiti/narrative_builder.py`
  - [ ] 函数 `build_narrative(payload) -> str`
- [ ] Task 7: 单元测试 (AC: #7)
  - [ ] `backend/tests/unit/test_canvas_episode_v1.py` (7 用例)
  - [ ] `backend/tests/unit/test_edge_type_map_propagation.py` (mock graphiti)

## Dev Notes

### Architecture

```
4 plugin 事件源 (callout-sync.ts / wikilink-sync.ts / calibration-sync / error-mark)
    ↓ POST /api/v1/event/canvas-graph (CanvasGraphEpisodeV1 payload)
backend: canvas_graph_event endpoint validate + 写 LanceDB canvas_graph_events 表
    ↓ 5 min sweep (5-ge-3 改造的 sweep cron)
backend: episode_worker._call_add_episode (含 edge_type_map)
    ↓
Graphiti (Neo4j 7691): node + edge + valid_at + entity_type 真生效
```

### File Paths
- 新建: `backend/app/graphiti/canvas_episode.py`
- 新建: `backend/app/graphiti/narrative_builder.py`
- 新建: `backend/app/api/v1/endpoints/canvas_graph_event.py`
- 改: `backend/app/graphiti/entity_types.py` (加 EDGE_TYPES + EDGE_TYPE_MAP)
- 改: `backend/app/services/episode_worker.py` (line 540-562 加 edge_type_map)
- 改: `backend/app/infra/lancedb_init.py` (加 canvas_graph_events 表)

### Background Decision Trace
- 2026-05-26 ChatGPT Deep Research 缺口 1 + 议题 2
- ChatGPT 引用 Graphiti 官方: episodes negotiates provenance + point-in-time
- ChatGPT 引用 custom ontology: edge_type_map 必传

### References
- ChatGPT 报告: `_bmad-output/审查/2026-05-26-chatgpt-graphiti-deep-research-报告.md` §Part 2 缺口 1
- 决策清单 schema 速查: `_bmad-output/审查/2026-05-26-graphiti-sprint-2-决策清单.md` §4 必修 #1

## Change Log

- 2026-05-26: spec 新建 (替代 1-16-callout-graphiti-hook V-07 + 2-10 V-09 拼凑方案), Plan EPIC1-BMAD-DEV-ASSESS-2026-04-17
