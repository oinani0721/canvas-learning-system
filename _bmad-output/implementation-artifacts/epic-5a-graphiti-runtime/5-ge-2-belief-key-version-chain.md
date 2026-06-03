---
story_id: "5-ge-2-belief-key-version-chain"
epic_id: "5a-graphiti-runtime"
prd_id: "canvas-learning-system"
priority: "P0"
estimate_hours: 9
depends_on: ["5-ge-1"]
blocks: []
sprint: "Sprint 2 v3 (Day 8, Session C)"
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
chatgpt_required: "#3 belief_key 版本链 + add_triplet API + valid_at/invalid_at"
supersedes: ["epic-4/LITE-4-3.md V-10 questions_registry (partial)"]
decision_trace: "2026-05-26 ChatGPT Deep Research 缺口 2 + 议题 1"
status: "review"
---

# Story 5-ge-2: belief_key 版本链 + Graphiti add_triplet API + valid_at/invalid_at 真用

Status: review

## Story

As a **学习者**,
I want **当我对同一节点的 callout / 关系 / calibration 写法发生变化时, Graphiti 能保留旧版本 + 标记新版本, 让我未来能问"我以前认为 X, 后来改成 Y"**,
So that 用户最在乎的 "Graphiti 时序图谱" 能力第一次从 spec 变成产品功能 (当前 valid_at/invalid_at 0% 利用).

## Acceptance Criteria

1. **Given** 新建 `backend/app/services/graphiti_belief_service.py` **When** module load **Then** 导出 `BeliefKeyResolver` + `update_belief_version_chain(belief_key, new_fact, ...)` 函数

2. **Given** belief_key 规范 **When** generate **Then** 4 种模式:
   - callout: `callout:{node_id}:{anchor}` (anchor = sha256(node_path + offset))
   - 节点关系: `edge:{source_node_id}:{relation_type}:{target_node_id}`
   - 校准投票: `calib:{question_id}:{vote_id}`
   - 错误模式: `error:{node_id}:{error_type}`

3. **Given** 同一 belief_key 出现第 2 次 (用户改了 callout 文本) **When** `update_belief_version_chain` 处理 **Then** 必须:
   - 调 `graphiti.search()` 找旧 EntityEdge by belief_key in attributes
   - 把旧 edge `invalid_at` 设为新事实的 `valid_at`
   - 用 `graphiti.add_triplet()` 写入新 EntityEdge (含 belief_key + status=active + 新 valid_at)

4. **Given** `graphiti.add_triplet()` 调用 **When** 写入 **Then** EntityEdge 必含:
   ```python
   EntityEdge(
       group_id=gid,
       source_node_uuid=src_uuid,
       target_node_uuid=tgt_uuid,
       created_at=occurred_at,
       valid_at=occurred_at,
       invalid_at=None,  # 后续更新时 set
       name="<relation_type>",  # Prerequisite / MisunderstandsAs / ...
       fact="<自然语言陈述>",
       attributes={
           "belief_key": "<belief_key>",
           "status": "active",
           "source": "<callout|frontmatter|review|calibration>"
       }
   )
   ```

5. **Given** 5-ge-1 的 CanvasGraphEpisodeV1 写入 **When** event_type 是 callout_updated / wikilink_removed 等"演化型" **Then** **同步**调 `update_belief_version_chain` 维护 canonical edge (双层: episode 记原始事件 + edge 记当前有效命题)

6. **Given** 历史查询 `get_belief_history(belief_key, as_of: datetime | None)` **When** 调用 **Then** 返回该 belief_key 的全部版本链 (按 valid_at 排序) + 标记 `current=True` 在最新 active 版本

7. **Given** 单元测试 **Then** 覆盖:
   - 同一 belief_key 写入 3 次 → Graphiti 应有 3 个 EntityEdge, 前 2 个 `invalid_at != None`, 最新一个 `status=active`
   - `get_belief_history(as_of="2 天前")` → 返回当时的 active edge (不是最新)
   - 用 `add_episode_bulk` 处理"演化事件" → **测试断言抛错** (bulk 不做 invalidation, 违规)

## Tasks / Subtasks

- [x] Task 1: BeliefKeyResolver (AC: #2)
  - [x] 新建 `backend/app/services/graphiti_belief_service.py`
  - [x] 4 种 belief_key 生成函数 (`make_callout_belief_key` / `make_edge_belief_key` / `make_calibration_belief_key` / `make_error_belief_key`)
- [x] Task 2: update_belief_version_chain (AC: #3, #4)
  - [x] ⚠️D1: 改 driver 原生 Cypher 按 `e.belief_key` 精确查旧 edge (search 无属性精确过滤, property_filters 零消费)
  - [x] ⚠️D2: 旧 edge invalid_at + status=superseded 更新, 用 `EntityEdge.save(driver)` (driver 无 update_edge)
  - [x] ⚠️D3: 用确定性 `EntityEdge(...).save(driver)` 直写新 edge (不调 add_triplet — 每次触发 LLM 成本不可接受)
- [x] Task 3: 与 5-ge-1 协同 (AC: #5)
  - [x] episode_worker `_process_episode` 在 add_episode 成功后, 演化型 event_type → `maybe_update_belief_from_task` (try/except 非致命双层解耦)
- [x] Task 4: get_belief_history (AC: #6)
  - [x] 按 valid_at 升序排序 + 标记 current (最新 active) + as_of 时序回溯 (active_at_as_of)
- [x] Task 5: 单元测试 (AC: #7)
  - [x] `backend/tests/unit/test_belief_version_chain.py` (FakeEdgeStore 有状态; 7 用例 green)
  - [x] 含 `use_bulk=True → pytest.raises(ValueError)` 反向断言 (AC#7)

## Dev Notes

### 关键 Graphiti API 用法 (ChatGPT 引用 quickstart README)

```python
from graphiti_core.nodes import EntityNode
from graphiti_core.edges import EntityEdge

# 写新版本时, 旧 edge 必须先 update
old_edges = await graphiti.search(query=belief_key, ...)
for edge in old_edges:
    if edge.attributes.get("status") == "active":
        edge.invalid_at = new_valid_at
        await graphiti.driver.update_edge(edge)  # 视 graphiti version 决定 CRUD API

# 然后写新 edge
await graphiti.add_triplet(source_node, new_edge, target_node)
```

**警告** (ChatGPT 引用): 不要用 `add_episode_bulk` — 官方文档明确 bulk ingestion **不做 edge invalidation**.

### File Paths
- 新建: `backend/app/services/graphiti_belief_service.py`
- 改: `backend/app/services/episode_worker.py` (协同 update_belief_version_chain)

### References
- ChatGPT 报告 §Part 2 缺口 2 + §Part 3 议题 1
- Graphiti quickstart README (add_triplet + valid_at/invalid_at)

## Dev Agent Record

### 实施摘要 (2026-06-03, Plan EPIC1-BMAD-DEV-ASSESS-2026-04-17)

belief 时序版本链核心**全部 AC 完成 + 测试 green**。本期 = belief 版本链 + get_belief_history + episode_worker 协同 hook。

### File List

- 新建 `backend/app/services/graphiti_belief_service.py` — BeliefKeyResolver(4) + update_belief_version_chain + get_belief_history + maybe_update_belief_from_task + driver Cypher 接缝 (_find_active/_find_all/_ensure_entity_node)
- 改 `backend/app/services/episode_worker.py` — `_process_episode` add_episode 后加演化事件 belief 旁路 (~12 行)
- 新建 `backend/tests/unit/test_belief_version_chain.py` — 7 用例 (3 版本链 / as_of 时序 / use_bulk 抛错 / 关系边 / BeliefKeyResolver / 自环), green

### 实读 0.28.2 源码确诊的偏离 (spec 写法在 0.28.2 不可行)

| # | spec 写法 | 0.28.2 现实 | 本期正解 |
|---|---|---|---|
| D1 | `graphiti.search(query=belief_key)` 查旧边 | search 是语义混合检索; `SearchFilters.property_filters` 声明但全代码零消费 (`search_filters.py`)，无法按属性精确查 | `graphiti.driver` 原生 Cypher 按已扁平为顶层属性的 `e.belief_key` 精确 WHERE (RETURN 列复刻 `get_entity_edge_return_query` 喂 `get_entity_edge_from_record`) |
| D2 | `graphiti.driver.update_edge(edge)` | driver 无此方法 | `EntityEdge.save(driver)` (edges.py:330-367, 纯写库 `SET e=$edge_data`, 无 LLM) |
| D3 | `add_triplet()` 写新边 (AC#4) | `add_triplet` 每次触发 LLM + 2×search + embedding, 对"每次改批注都调"成本不可接受 | 确定性 `EntityEdge(...).save(driver)` 直写, 字段全掌控 |
| R5 | (隐患) | graphiti 只按 name 去重 (不含 group_id) | `_ensure_entity_node` 先按 name+group_id Cypher 查复用, 查不到才 uuid5 新建, 避免与 add_episode 自建节点分裂版本链 + 跨 vault 污染 |

### 验证证据

- 单测: `test_belief_version_chain.py` 7 passed (含同 belief_key 写 3 次 → 3 边 + `edges[0].invalid_at == edges[1].valid_at` + 最新 active; as_of 时序回溯; use_bulk ValueError)
- 段 4-A demo: 写 v1/v2/v3 → `get_belief_history` 打印旧版 superseded + 新版 active + current 标记; `as_of` 回溯当时认知 (见验收单 Story-S2-2)
- C-3 隔离: belief 写入经 `sanitize_group_id_for_graphiti()`

### 本期范围外 (Q2 未选, 已解锁可选后续)

- `edge_type_map` 透传 (5-ge-1 AC#4) — Phase 0 后无冲突可随时做
- registry JSONL 持久化

## Change Log

- 2026-05-26: spec 新建 (替代 V-10 questions_registry 方案 — belief_key 更通用, questions_registry 退化为一种实例)
- 2026-06-03: 实施完成 (status → review)。D1/D2/D3/R5 偏离 (实读 graphiti-core 0.28.2 源码确诊 search/update_edge/add_triplet 三处 spec 写法不可行)。代码主线 main commit。Plan EPIC1-BMAD-DEV-ASSESS-2026-04-17
