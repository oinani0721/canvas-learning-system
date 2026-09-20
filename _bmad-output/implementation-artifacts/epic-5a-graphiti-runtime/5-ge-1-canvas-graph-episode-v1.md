---
story_id: "5-ge-1-canvas-graph-episode-v1"
epic_id: "5a-graphiti-runtime"
prd_id: "canvas-learning-system"
status: "review"
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

Status: review

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
- [ ] Task 3: episode_worker edge_type_map 透传 (AC: #4) — 🔁 **移交**（CARD-DEBT-11 裁定 2026-09-18）：落点 `episode_worker.py:596-607` / `EpisodeTask:85-86` / `memory_service.py:476,645,1657` 属 P2 outbox 地盘；归属待主 session 排（候选 DEBT-12 facade 卡或 P2 后续），本 story review 状态不含此项
- [x] ~~Task 4: 统一 events_queue 表 (AC: #5)~~ ❌ 废弃于 5-ge-1（CARD-DEBT-11 裁定 2026-09-18）：AC#5 按 D5 以 payload 进 episode_body 达成；`canvas_graph_events` 表 / `POST /api/v1/event/canvas-graph` 候选树零存在；5-ge-3 :32「(5-ge-1 建)」措辞与 D5 矛盾，登记待 5-ge-3 改（不在本卡地盘）
- [x] ~~Task 5: endpoint (AC: #5)~~ ❌ 废弃于 5-ge-1（CARD-DEBT-11 裁定 2026-09-18）：AC#5 按 D5 以 payload 进 episode_body 达成；`canvas_graph_events` 表 / `POST /api/v1/event/canvas-graph` 候选树零存在；5-ge-3 :32「(5-ge-1 建)」措辞与 D5 矛盾，登记待 5-ge-3 改（不在本卡地盘）
- [x] Task 6: narrative 生成 helper (AC: #6)
  - [x] 新建 `backend/app/graphiti/narrative_builder.py`
  - [x] `build_narrative(payload) -> str` (7 event_type 分支, 含 [[wikilink]] + path_trace; 输出对齐 AC#6 示例)
- [x] Task 7: 单元测试 (AC: #7) — schema 部分完成（19 用例 green，CARD-DEBT-11 复跑存档 `evidence-debt11/episode-v1-open-*.txt` / `episode-v1-close-*.txt`）；edge_type_map 透传测试随 Task 3 移交
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

> ⚠️ **2026-09-18 CARD-DEBT-11 裁定后注**：本节架构图为 2026-05-26 **历史目标态**。其中 plugin POST `/api/v1/event/canvas-graph`、`canvas_graph_events` 表 属 Task 4/5（**已废弃**）；worker `edge_type_map` 属 Task 3（**已移交**，落点在 P2 地盘）；下方 File Paths 同名条目（endpoint / episode_worker / lancedb_init）同为历史目标态。以「Tasks / Subtasks」与「### 裁定 2026-09-18 (CARD-DEBT-11)」为准。

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

## Schema 冻结声明（2026-09-18，CARD-DEBT-11）

- **版本（不变）**: `schema_version: Literal["CanvasGraphEpisodeV1"] = "CanvasGraphEpisodeV1"`（**可省略字段；省略时默认值即该 Literal 值**；`canvas_episode.py:226`，行号实测——r3 LOW-2 订正）。
- **冻结面（实测，2026-09-18）**:
  - 15 字段（名 / 类型 / 必填性）: `schema_version: Literal["CanvasGraphEpisodeV1"]` · `event_id: str = ""`（空则按公式派生） · `event_type: EventType`（必填） · `occurred_at: datetime`（必填） · `vault_id: str`（必填） · `group_id: str`（必填） · `canvas_path: str`（必填） · `node_id: str`（必填） · `source_node_id: str | None = None` · `target_node_id: str | None = None` · `relation_type: str | None = None` · `belief_key: str`（必填） · `callout: CalloutPayload | None = None` · `context: ContextPayload`（必填） · `narrative: str`（必填 + 非空校验）
  - `EventType` 7 值: `wikilink_added / wikilink_removed / callout_added / callout_updated / callout_removed / calibration_vote / error_marked`
  - `CANVAS_GRAPH_ENTITY_TYPES`（1 键）: `CanvasNode`{node_id: str 必填 / title: str = "" / subject_area: str = ""}
  - `CANVAS_GRAPH_EDGE_TYPES`（10 键，**逐键含字段类型/默认值/必填性**）: 公共基 `_RelationEdge`{statement: str = ""}；关系型 7 = `Prerequisite`{+strength: str = "strong"} / `Elaborates` / `Contrasts` / `ExampleOf` / `Causes` / `PartOf` / `RelatedTo`；自环型 3 = `SelfAnnotation`{+callout_type: str = ""} / `SelfMisconception`{+error_type: str = ""} / `CalibrationVote`{+vote: str = ""}
  - `CANVAS_EDGE_TYPE_MAP`（1 键对，冻结）: 恰 `("CanvasNode", "CanvasNode") → list(CANVAS_GRAPH_EDGE_TYPES.keys())`（10 键，顺序 = 上述定义序）
  - `RELATION_TYPE_TO_EDGE_NAME`（11 键，**逐键冻结**）: prerequisite→Prerequisite · depends_on→Prerequisite · refines→Elaborates · extends→Elaborates · elaborates→Elaborates · contradicts→Contrasts · contrasts→Contrasts · example_of→ExampleOf · causes→Causes · part_of→PartOf · related_to→RelatedTo；`edge_name_for_relation` 行为冻结：None/空/未命中 → `RelatedTo`（查表前 `lower()`）
  - 嵌套 payload **冻结**：`CalloutPayload`{callout_type: str 必填 / text: str 必填 / offset: int = 0}（anchor/belief_key 派生**不属** C-1 冻结面——实际语义 = `graphiti_belief_service.BeliefKeyResolver.make_callout_belief_key`：`sha256(f"{node_path}:{offset}")[:16]`，见 `graphiti_belief_service.py:62-67`）· `ContextPayload`{source_board: str = "" / path_trace: list[str] = [] / in_links: list[str] = [] / out_links: list[str] = []}
  - `EVOLUTION_EVENT_TYPES`（派生 5 值）: `WIKILINK_REMOVED` / `CALLOUT_UPDATED` / `CALLOUT_REMOVED` / `CALIBRATION_VOTE` / `ERROR_MARKED`
  - `compute_event_id` 派生公式: `sha256(vault_id|canvas_path|anchor|occurred_at.isoformat())`；`_autofill_event_id` 语义冻结：仅当 `event_id` 为空时触发，`anchor = belief_key or node_id`，occurred_at 的 ISO 文本参与哈希
- **禁改规则（freeze）**: 任何字段增删 / 改类型 / 改必填 / 改 enum 值 / 改 event_id 公式 **一律不得就地改 V1**，必须新开 `CanvasGraphEpisodeV2`（新 Literal 值 + 新类；V1 保留供历史 episode 反序列化）+ 新 story + `[Decision-Review]`。
- **允许面**: 纯注释 / docstring / 新增**非**字段的 helper（D-32 口径由主 session 核）。
- **本体接线状态（如实登记）**: `edge_type_map` 生产透传 = Task 3，已移交 ⇒ 本次冻结 = **schema 契约层**冻结；「Graphiti custom ontology 真生效」不在冻结完成度内。
- **消费方清单（实测 3 处生产）**: `narrative_builder.py:12` / `graphiti_belief_service.py:34`（实调 :235）/ `episode_worker.py:620`；测试侧 `tests/unit/test_canvas_episode_v1.py`。
- **复跑存档**: `_bmad-output/审查/evidence-debt11/episode-v1-open-*.txt`（19 passed 开工档；收工档 `episode-v1-close-*.txt` 同目录）。

## Dev Agent Record

### 裁定 2026-09-18 (CARD-DEBT-11)

- **Task 3 = 移交**：`edge_type_map` 生产透传零存在——`episode_worker.py:596-607` 的 `_call_add_episode` kwargs 只有 name/episode_body/group_id/source_description/reference_time（无 `edge_type_map`）；`EpisodeTask:85-86` 无此字段；`grep -rn -i edge_type_map backend/app` 仅命中 `canvas_episode.py:12`（头部注释）/ `:186`（注释）/ `:187`（`CANVAS_EDGE_TYPE_MAP` 定义）；落点全在 P2 outbox 地盘（`episode_worker.py` / `memory_service.py:476,645,1657`）⇒ 本 story 不改，归属待主 session 排（候选 DEBT-12 facade 卡或 P2 后续）。
- **Task 4/5 = 废弃于本 story**：`grep -rn -e canvas_graph_events -e 'event/canvas-graph' backend/app` 实测 **0 命中**（rc=1；早期勘探曾记「两条 [Source] 注释命中」，系记述误差——两处 [Source] 注释只含 spec 文件名、不含该二模式）⇒ 表与端点候选树零存在；`5-ge-3-query-time-flush.md:32` 自述「读 LanceDB `canvas_graph_events` 表 (5-ge-1 建)」与 5-ge-1「D5」字样处（本文件 Tasks 段 Task 4/5 行 + 偏离表）互指、无 owner —— 登记待 5-ge-3 改（不在本卡地盘）。
- **Task 7 = schema 部分完成**：`test_canvas_episode_v1.py` 19 用例 green（CARD-DEBT-11 开工/收工复跑存档 `evidence-debt11/episode-v1-*.txt`）；edge_type_map 透传测试随 Task 3 移交。

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
- 2026-09-18: CARD-DEBT-11 schema 冻结 + Task 3 移交 / Task 4/5 废弃 + status → review；同 commit supersede 1-16-callout-graphiti-hook / 2-10
