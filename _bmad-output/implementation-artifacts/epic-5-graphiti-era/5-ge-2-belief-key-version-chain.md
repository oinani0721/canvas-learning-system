---
story_id: "5-ge-2-belief-key-version-chain"
epic_id: "5-graphiti-era"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P0"
estimate_hours: 9
depends_on: ["5-ge-1"]
blocks: []
sprint: "Sprint 2 v3 (Day 8, Session C)"
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
chatgpt_required: "#3 belief_key 版本链 + add_triplet API + valid_at/invalid_at"
supersedes: ["epic-4/LITE-4-3.md V-10 questions_registry (partial)"]
decision_trace: "2026-05-26 ChatGPT Deep Research 缺口 2 + 议题 1"
---

# Story 5-ge-2: belief_key 版本链 + Graphiti add_triplet API + valid_at/invalid_at 真用

Status: ready-for-dev

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

- [ ] Task 1: BeliefKeyResolver (AC: #2)
  - [ ] 新建 `backend/app/services/graphiti_belief_service.py`
  - [ ] 4 种 belief_key 生成函数 (`make_callout_belief_key` 等)
- [ ] Task 2: update_belief_version_chain (AC: #3, #4)
  - [ ] graphiti.search() 查旧 edge by attributes.belief_key
  - [ ] 旧 edge invalid_at 更新 (用 graphiti CRUD)
  - [ ] graphiti.add_triplet() 写新 edge
- [ ] Task 3: 与 5-ge-1 协同 (AC: #5)
  - [ ] episode_worker 在写完 add_episode 后, 演化型 event_type → 同步调 update_belief_version_chain
- [ ] Task 4: get_belief_history (AC: #6)
  - [ ] 按 valid_at desc 排序 + 标记 current
- [ ] Task 5: 单元测试 (AC: #7)
  - [ ] `backend/tests/unit/test_belief_version_chain.py`
  - [ ] 含 `add_episode_bulk 不可用于演化` 反向断言

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

## Change Log

- 2026-05-26: spec 新建 (替代 V-10 questions_registry 方案 — belief_key 更通用, questions_registry 退化为一种实例)
