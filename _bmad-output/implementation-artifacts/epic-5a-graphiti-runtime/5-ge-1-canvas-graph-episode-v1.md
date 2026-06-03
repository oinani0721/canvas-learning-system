---
story_id: "5-ge-1-canvas-graph-episode-v1"
epic_id: "5a-graphiti-runtime"
prd_id: "canvas-learning-system"
status: "in-progress"
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

Status: in-progress

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

- [x] Task 1: Pydantic schema 定义 (AC: #2)
  - [x] 新建 `backend/app/graphiti/canvas_episode.py`
  - [x] CanvasGraphEpisodeV1 + EventType enum (7) + CalloutPayload + ContextPayload + event_id 工厂 + narrative 必填校验
- [x] Task 2: entity/edge 本体定义 (AC: #3)
  - [x] ⚠️D4: **不改** `entity_types.py` (已有同名 CANVAS_ENTITY_TYPES/CANVAS_EDGE_TYPES 被已活管道 import, 覆盖会打断)。改放 `canvas_episode.py` 用新名
  - [x] CANVAS_GRAPH_ENTITY_TYPES (CanvasNode) + CANVAS_GRAPH_EDGE_TYPES (7 关系 + 3 自环 = 10 类) + CANVAS_EDGE_TYPE_MAP
- [ ] Task 3: episode_worker edge_type_map 透传 (AC: #4) — ⏸ **本期 Q2 未选** (已解锁可选后续; Phase 0 后无冲突)
  - [ ] `_process_episode` 加 `edge_type_map=CANVAS_EDGE_TYPE_MAP` 参数
- [ ] Task 4: 统一 events_queue 表 (AC: #5) — ⏸ **D5 降级 5-ge-3** (本期用 payload 进 episode_body 达成; 不新建平行主干护 C-1)
  - [ ] `canvas_graph_events` LanceDB 表
- [ ] Task 5: endpoint (AC: #5) — ⏸ **D5 降级 5-ge-3**
  - [ ] POST `/api/v1/event/canvas-graph`
- [x] Task 6: narrative 生成 helper (AC: #6)
  - [x] 新建 `backend/app/graphiti/narrative_builder.py`
  - [x] `build_narrative(payload) -> str` (7 event_type 分支, 含 [[wikilink]] + path_trace; 输出对齐 AC#6 示例)
- [~] Task 7: 单元测试 (AC: #7) — schema 部分完成, edge_type_map 透传测试随 Task 3 延后
  - [x] `backend/tests/unit/test_canvas_episode_v1.py` (19 用例: 7 event_type + narrative 必填 + event_id 确定性 + sanitize, green)
  - [ ] `backend/tests/unit/test_edge_type_map_propagation.py` (随 Task 3 edge_type_map 透传一起做)

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

## Dev Agent Record

### 实施摘要 (2026-06-03, Plan EPIC1-BMAD-DEV-ASSESS-2026-04-17)

**部分完成 (status = in-progress)**: 统一 schema (Task 1) + 本体类型 (Task 2) + narrative (Task 6) + schema 单测 (Task 7 部分) 已 done。
传输层 (Task 4 lancedb 表 / Task 5 endpoint) **D5 降级到 5-ge-3**; edge_type_map 透传 (Task 3) **Q2 未选**, 列为已解锁可选后续。本期 schema 作为 episode_body 结构化载体达成 AC#5 实质 (不新建平行主干, 护 C-1)。

### File List

- 新建 `backend/app/graphiti/canvas_episode.py` — EventType(7) + CalloutPayload + ContextPayload + CanvasGraphEpisodeV1 (event_id SHA-256 工厂 + narrative 必填校验) + CanvasNode + 10 边类 + CANVAS_GRAPH_ENTITY_TYPES / CANVAS_GRAPH_EDGE_TYPES / CANVAS_EDGE_TYPE_MAP + edge_name_for_relation
- 新建 `backend/app/graphiti/narrative_builder.py` — build_narrative(payload) 纯函数
- 新建 `backend/tests/unit/test_canvas_episode_v1.py` — 19 passed

### 偏离 (记入 Change Log)

| # | spec 写法 | 本期正解 |
|---|---|---|
| D4 | AC#3 把 `CANVAS_ENTITY_TYPES`/`CANVAS_EDGE_TYPES` 放进 `entity_types.py` | 该文件已有同名常量 (值=LearningConcept.../PrerequisiteRelation) 被已活 `memory_service` import, 覆盖会**打断已活管道**。改用新名 `CANVAS_GRAPH_ENTITY_TYPES`/`CANVAS_GRAPH_EDGE_TYPES`/`CANVAS_EDGE_TYPE_MAP` 放**新文件** `canvas_episode.py` (C-1 owner) |
| D5 | Task4/5 新建 lancedb `canvas_graph_events` 表 + `/event/canvas-graph` endpoint | `app/infra/` 不存在; 真实 LanceDB schema-on-write; 已活管道已持久化 (Neo4j + worker 队列 + 幂等)。**降级 5-ge-3** (队列/sweep 本就是 5-ge-3 scope); AC#5 用 payload 进 episode_body 达成 |

### 验证证据

- 单测: `test_canvas_episode_v1.py` 19 passed (7 event_type 各 1 + narrative 空/whitespace/missing → ValidationError + event_id 确定性 + sanitize + edge type 本体)
- narrative smoke: callout_added 输出逐字对齐 AC#6 示例 ([[recursion-base-case]] + [概览]→[递归定义]→[base case] + 出链/反向引用)

## Change Log

- 2026-05-26: spec 新建 (替代 1-16-callout-graphiti-hook V-07 + 2-10 V-09 拼凑方案), Plan EPIC1-BMAD-DEV-ASSESS-2026-04-17
- 2026-06-03: 部分实施 (status → in-progress)。Task 1/2/6 + 7 部分 done; D4 (新名避开 entity_types.py 同名常量) + D5 (lancedb/endpoint 降级 5-ge-3) 偏离。Task 3 edge_type_map 透传 Q2 未选。代码主线 main commit。
