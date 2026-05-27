---
story_id: "5-ge-3-query-time-flush"
epic_id: "5a-graphiti-runtime"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P0"
estimate_hours: 4
depends_on: ["5-ge-1"]
blocks: []
sprint: "Sprint 2 v3 (Day 9 AM, Session C)"
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
chatgpt_required: "#4 (前半) Hot/Warm/Cold 三层时延 + query-time flush"
supersedes: ["epic-2/2-10-wikilink-graphiti-sync.md sweep 部分"]
decision_trace: "2026-05-26 ChatGPT Deep Research 缺口 4 + 议题 4"
---

# Story 5-ge-3: query-time flush + Hot/Warm/Cold 三层时延

Status: ready-for-dev

## Story

As a **学习者**,
I want **当我写完 callout 立刻触发 quick exam 时, 系统能在 1.2 秒内把刚写的 callout flush 到 Graphiti, 让出题真考到我刚说的话**,
So that 不用等 1h sweep cron, "我刚标了 tip, 怎么没考到这个?" UX 断层修复.

## Acceptance Criteria

1. **Given** 新建 `backend/app/services/graphiti_write_facade.py` **When** module load **Then** 导出 `flush_pending(group_id, canvas_path, max_wait_ms=1200)` 函数

2. **Given** 查询前调用 `flush_pending` **When** 处理 **Then**:
   - 读 LanceDB `canvas_graph_events` 表 (5-ge-1 建) 中 `consumed_at IS NULL AND group_id=? AND canvas_path=?` 的事件
   - 立即调 episode_worker 的同步版本 (不入异步队列) 写 Graphiti
   - 写完标 `consumed_at = NOW()`
   - max_wait_ms 超时 → 返回 `{"flushed": N, "timeout": True}` (不抛异常)

3. **Given** sweep cron 改造 **When** `wikilink_batch_sweep.py` 跑 **Then** 改 `0 * * * *` (1h) → `*/5 * * * *` (5 min) — Warm path 兜底

4. **Given** Cold path **When** 夜间 cron **Then** 跑 `build_communities(group_id=gid)` (5-ge-5 facade 用)

5. **Given** 3 层时延承诺 **When** 用户体验 **Then**:
   - Hot path: 保存后 3-10 秒内可查 (5-ge-5 facade 调 flush_pending)
   - Warm path: 5 分钟 sweep
   - Cold path: 夜间 community 重建

6. **Given** flush_pending 失败 (graphiti down) **When** 调用方处理 **Then** 降级为不 flush, 走 LanceDB only 出题 (LITE-4-3 路线 1/3 + LITE-5-7 路线 A 仍可用)

## Tasks / Subtasks

- [ ] Task 1: flush_pending 函数 (AC: #1, #2)
  - [ ] 新建 `backend/app/services/graphiti_write_facade.py`
  - [ ] 查 unconsumed events + 同步写 + 标 consumed_at
  - [ ] 超时降级
- [ ] Task 2: sweep cron 改 5 min (AC: #3)
  - [ ] 改 `backend/scripts/wikilink_batch_sweep.py` (改名 `canvas_graph_sweep.py`)
  - [ ] crontab 改 `*/5 * * * *`
- [ ] Task 3: build_communities Cold path (AC: #4)
  - [ ] 新建 `backend/scripts/nightly_build_communities.py`
  - [ ] crontab 加 `0 3 * * * python nightly_build_communities.py`
- [ ] Task 4: 集成测试 (AC: #5, #6)
  - [ ] `backend/tests/integration/test_query_time_flush.py`
  - [ ] Graphiti up: flush 1.2s 内成功
  - [ ] Graphiti down: 降级走 LanceDB only

## Dev Notes

### Architecture

```
[Hot path]
用户 Cmd+Shift+Q (quick exam)
    ↓
backend: LITE-4-3 路线 4 调用前
    ↓ await flush_pending(group_id, canvas_path, max_wait_ms=1200)
backend: graphiti_write_facade.flush_pending
    ↓ 查 canvas_graph_events 表 unconsumed
    ↓ 同步 add_episode (含 edge_type_map from 5-ge-1)
    ↓ Graphiti (Neo4j 7691)
    ↓ 标 consumed_at
backend: LITE-4-3 路线 4 调 search_relation_facts (5-ge-5 facade)
    ↓ 返回真有 fresh callout 的 facts

[Warm path]
5 min cron → canvas_graph_sweep.py → 处理所有 unconsumed events

[Cold path]
夜间 03:00 cron → build_communities(group_id=gid) → 5-ge-5 search_error_communities 用
```

### File Paths
- 新建: `backend/app/services/graphiti_write_facade.py`
- 新建: `backend/scripts/nightly_build_communities.py`
- 改名: `backend/scripts/wikilink_batch_sweep.py` → `canvas_graph_sweep.py` (扩展 unified table)

### References
- ChatGPT 报告 §Part 2 缺口 4 + §Part 3 议题 4
- Graphiti 官方: real-time incremental updates (vs Canvas 之前 1h delay)

## Change Log

- 2026-05-26: spec 新建 (替换 2-10 1h sweep 主路径方案)
