---
story_id: "STORY-2-10-wikilink-graphiti-sync"
epic_id: "2"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P1"
estimate_hours: 6
depends_on: ["INFRA-002", "PLUGIN-001"]
blocks: []
sprint: "Sprint 2 Day 9 (用户 1B 决策插队)"
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
decision_trace: "round-13-wikilink-vs-graphiti-five-questions-answer-2026-04-29.md Q4 (line 237-259)"
trace:
  - "FR-KG-NEW-01 (wikilink-Graphiti 单向同步)"
  - "FR-KG-04 (group_id 隔离)"
---

# Story 2.10: Wikilink → Graphiti 单向事件流同步（Lazy + Batch）

Status: ready-for-dev

## Story

As a 学习者,
I want **每次保存 md 时，wikilink 图的变化在 1-60 分钟内同步到 Graphiti 知识图谱**,
So that 学习事件检索（错误模式聚类 / 时序追踪 / "X 和 Y 的关系"查询）能用到最新的概念关联，**但不影响 md 保存性能**。

## Acceptance Criteria

1. **Given** 用户在 canvas-vault 保存 md（`vault.modify` 事件） **When** plugin 监听到 modify **Then** plugin 用 `metadataCache.getFileCache(file).links` 计算与上次缓存的 wikilink delta（added / removed）

2. **Given** delta 非空 **When** plugin 处理 **Then** POST `/api/v1/event/navigation` 带 body：
   ```json
   {
     "kind": "wikilink_change",
     "source_node": "<vault-relative-path>",
     "added": ["<target1>", "<target2>"],
     "removed": ["<target3>"],
     "timestamp": "2026-05-24T14:30:00Z",
     "vault_id": "<configured-vault-id>"
   }
   ```

3. **Given** backend 收到 event **When** endpoint 处理 **Then** **不阻塞**直接写入 `events_queue`（LanceDB 临时表 `wikilink_events` 或 Redis stream），返回 `202 Accepted` **And** 单次写入 < 100ms

4. **Given** hourly cron 触发 (`backend/scripts/wikilink_batch_sweep.py`) **When** sweep 启动 **Then** 从 `events_queue` 读取所有未消费 event，按 `vault_id` 分组，调 Graphiti `add_episode`：
   ```python
   add_episode(
       name=f"wikilink_batch_{vault_id}_{batch_timestamp}",
       episode_body=json.dumps({"changes": [...]}),  # 含 added/removed/source_node
       source="wikilink_sync",
       group_id=f"vault:{vault_id}",  # 用 §Story 2.5.Y group_id 规约
       reference_time=batch_timestamp,
   )
   ```

5. **Given** Graphiti `add_episode` 失败 **When** 重试 **Then** event 保留在 `events_queue` 标 `retry_count += 1` **And** 最多重试 3 次，3 次后写入 `failed_events` 表 + structlog ERROR

6. **Given** Graphiti `add_episode` 成功 **When** 写入完成 **Then** event mark `consumed_at = <timestamp>` **And** 从 `events_queue` 删除 / 归档

7. **Given** 用户查询 `search_facts("X 和 Y 的关系")` **When** Graphiti 查询 **Then** 能返回 **1-60 分钟前**同步的 wikilink edges（latency 验证）

8. **Given** 单 batch event 数 > 1000 **When** sweep 处理 **Then** 分块写入（chunk_size=200），避免单次 `add_episode` 超时

## Tasks / Subtasks

- [ ] Task 1: plugin 侧 wikilink delta 计算 (AC: #1)
  - [ ] `frontend/obsidian-plugin/src/wikilink-sync.ts` 新建
  - [ ] 监听 `vault.on("modify", ...)`，维护 in-memory cache `Map<filePath, Set<targetPath>>`
  - [ ] 调 `app.metadataCache.getFileCache(file).links` 取当前 links
  - [ ] 计算 added/removed
  - [ ] 单元测试：first save / 加 1 link / 删 1 link / 改名 link

- [ ] Task 2: plugin POST event 到 backend (AC: #2)
  - [ ] 用 PLUGIN-001 抽取的 `backend-client.ts::callBackend()` helper
  - [ ] body schema 严格匹配 AC #2
  - [ ] retry: 3 次指数退避（1s/2s/4s），失败后入 plugin local queue
  - [ ] 单元测试：mock backend 200/500/timeout

- [ ] Task 3: backend endpoint `POST /api/v1/event/navigation` (AC: #3)
  - [ ] 新建 `backend/app/interfaces/api/event.py`（如不存在）
  - [ ] handler：validate body → write to `events_queue` → return 202
  - [ ] **不**直接调 Graphiti（保持 < 100ms）
  - [ ] 单元测试：concurrent write 50 events / invalid body / missing vault_id

- [ ] Task 4: events_queue schema (AC: #3)
  - [ ] 用 LanceDB 临时表 `wikilink_events` schema:
    ```python
    schema = {
        "event_id": "uuid",
        "kind": "string",
        "vault_id": "string",
        "source_node": "string",
        "added": "list[string]",
        "removed": "list[string]",
        "timestamp": "datetime",
        "retry_count": "int",
        "consumed_at": "datetime?"
    }
    ```
  - [ ] table init in `backend/app/infra/lancedb_init.py`

- [ ] Task 5: hourly cron sweep (AC: #4)
  - [ ] `backend/scripts/wikilink_batch_sweep.py` 新建
  - [ ] cron 配置：`crontab.txt` 加 `0 * * * * python3 wikilink_batch_sweep.py`
  - [ ] 实现：read unconsumed → group by vault_id → call add_episode → mark consumed
  - [ ] 与 `episode_worker.py:562` 已有 add_episode 框架对接

- [ ] Task 6: Graphiti add_episode wikilink format (AC: #4)
  - [ ] `backend/app/services/episode_worker.py` 加 `make_wikilink_episode_body()` helper
  - [ ] episode_body JSON 格式：`{"changes": [{"added": [...], "removed": [...], "source_node": "..."}]}`
  - [ ] group_id 用 §Story 2.5.Y 规约 `vault:<vault_id>` (`build_vault_group_id`)

- [ ] Task 7: 重试机制 (AC: #5)
  - [ ] failed_events 表 schema
  - [ ] sweep 失败 → retry_count++
  - [ ] retry_count >= 3 → 移到 failed_events + structlog ERROR
  - [ ] 单元测试：连续失败 4 次的转移

- [ ] Task 8: 集成测试 (AC: #7)
  - [ ] e2e 测试：
    1. plugin 模拟 modify md (加 `[[BST]]` link)
    2. 等待 ≥ 1h 或手动跑 sweep
    3. backend search_facts("BST") 应返回新 edge
  - [ ] CI: 用 mock sweep 立即触发，缩短 hour wait

- [ ] Task 9: 分块写入 > 1000 events (AC: #8)
  - [ ] sweep 加 chunk_size=200 循环
  - [ ] structlog 记录 batch count / chunk count

- [ ] Task 10: 性能验证
  - [ ] plugin modify → POST endpoint < 100ms
  - [ ] sweep 1000 events < 30s (chunked)
  - [ ] e2e 端到端 < 60min (cron interval)

## Background Decision Trace（新需求 — 详细决策追溯）

### round-13 Q4 (2026-04-29) 设计原文
- **设计名**: 单向事件流 (Lazy + Batch)
- **完整数据流** (round-13 line 237-259):
  ```
  md 保存
    → Wikilink Graph 立即更新 (Obsidian metadataCache)
    → EventBus 发事件
    → Background Worker
    → Batch sweep (hourly cron)
    → Graphiti add_episode
  ```
- **关键决策**:
  - ❌ 不实时双写 (避免性能问题)
  - ✅ md → Graphiti **单向**，永不反向
  - ⏱️ 延迟 1-60 分钟可接受

### Graphiti 工具集激活状态（2026-05-22 答疑 v2 §批注①）

| Graphiti API | 当前调用 | 应该用于 | gap |
|---|---|---|---|
| `add_episode` | ✅ 框架就绪 (`episode_worker.py:562`) | 每次学习事件都写 | 仅学习事件接，**wikilink 同步零调用** |
| `search_nodes` | ✅ 2 处 | 节点检索 | 基础可用 |
| `search_facts` | ❌ 0 处 | "X 和 Y 的关系"查询 | **本 Story 激活** |
| `search_communities` | ❌ 0 处 | 错误模式聚类 | 后续 Story 激活 |
| `valid_at/invalid_at` | ❌ 0 处 | 时序追踪 | 本 Story `consumed_at` 部分触达 |

### 用户 1B 决策 (2026-05-22)

> "wikilink-Graphiti 同步加速到 Sprint 2 Day 9 (+6h)"

- 加速理由：3 agent 一致设计已 ready (round-13 Q4)，工作量 ~6h 可控
- 影响：Sprint 2 Day 9 +6h，但管道激活后 search_facts / search_communities 后续 Story 可用

### 现状（实施前 baseline）

| 层 | 状态 | 证据 |
|---|---|---|
| 设计 | ✅ 完整 (round-13 Q4) | 2026-04-29 已定稿 |
| 后端框架 | 🟡 部分 (`episode_worker.py` 有 `add_episode`) | 已写但 wikilink 管道零调用 |
| plugin 代码 | ❌ 零行 | 本 Story Task 1+2 实施 |
| endpoint | ❌ 零行 | 本 Story Task 3 实施 |
| 集成测试 | ❌ 零行 | 本 Story Task 8 实施 |

## Dev Notes

### Architecture

```
canvas-vault md 保存
    ↓
plugin: vault.on("modify")
    ↓ (delta calc)
plugin: backend-client.callBackend("POST /api/v1/event/navigation")
    ↓
backend: events_queue (LanceDB wikilink_events)
    ↓ (hourly cron)
backend: wikilink_batch_sweep.py
    ↓ (group by vault_id, chunked add_episode)
backend: episode_worker.add_episode(group_id="vault:<vault_id>")
    ↓
Graphiti (Neo4j 7691)
```

### File Paths
- plugin: `frontend/obsidian-plugin/src/wikilink-sync.ts`（新建）
- plugin entry: `frontend/obsidian-plugin/src/main.ts` 注册 WikilinkSync
- backend endpoint: `backend/app/interfaces/api/event.py`（新建或扩展）
- backend service: `backend/app/services/episode_worker.py`（加 wikilink helper）
- backend cron: `backend/scripts/wikilink_batch_sweep.py`（新建）
- backend schema: `backend/app/infra/lancedb_init.py`（加 wikilink_events 表）

### Testing
- 单元测试：plugin delta calc + backend endpoint + sweep helper
- 集成测试：`backend/tests/integration/test_wikilink_graphiti_sync.py`
- e2e 测试：mock cron 立即触发，验证 add_episode 调用

### Project Structure Notes
- group_id 必须用 §Story 2.5.Y 规约：`build_vault_group_id(vault_id, subject_id, canvas_path)`
- Cypher 查询防御：用 `cypher_with_group_filter()` 防忘传 group_id 跨 vault 泄漏

### References
- **From PRD**: §1.5 三层记忆架构 + §2.4 数据保证
- **From round-13 Q4**: `_bmad-output/research/round-13-wikilink-vs-graphiti-five-questions-answer-2026-04-29.md` (line 237-259)
- **From Sprint v3**: `_bmad-output/research/2026-05-21-sprint-plan-v3.md` 新需求
- **From 2026-05-22 答疑 v2**: `_bmad-output/研究/2026-05-22-3批注答疑v2-我的认知校准.md` §批注 ① Graphiti 同步真相
- **From §Story 2.5.Y**: `backend/app/core/subject_config.py::build_vault_group_id`
- **From CLAUDE.md**: Graphiti group_id 命名规约
- **Graphiti 社区源码**: https://github.com/getzep/graphiti

## UAT Script（用户视角验证 — 实际数据流测试）

> 1. 在 canvas-vault 打开一个节点 md（如 `节点/eigenvalue.md`）
> 2. 加一个新 wikilink（如插入 `[[linear-algebra-basics]]`）
> 3. Cmd+S 保存
> 4. **等 1-60 分钟**（或问 Claude "现在手动跑 sweep"）
> 5. 在 canvas-vault 中触发 search_facts 查询（如 plugin command "查询 eigenvalue 关系" — 或 Claude MCP 跑）
> 6. 应能看到新 edge `eigenvalue → linear-algebra-basics` 在 Graphiti 返回中
> 7. 验证 backend log 含 `[wikilink_batch_sweep] consumed N events`

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| plugin delta calc | unit | `npm test -- wikilink-sync.test.ts` | 0 failures |
| backend endpoint < 100ms | perf | `pytest backend/tests/perf/test_event_navigation_latency.py` | P95 < 100ms |
| events_queue 写入 | unit | `pytest backend/tests/unit/test_wikilink_events_queue.py -x` | 0 failures |
| sweep chunked > 1000 | unit | `pytest backend/tests/unit/test_wikilink_sweep_chunking.py -x` | 0 failures |
| 重试 3 次 + failed_events | unit | `pytest backend/tests/unit/test_wikilink_retry.py -x` | 0 failures |
| group_id 规约符合 | static | `grep "build_vault_group_id" backend/app/services/episode_worker.py` | ≥ 1 match |
| e2e wikilink → search_facts | e2e | `pytest backend/tests/e2e/test_wikilink_graphiti_e2e.py -x` | 0 failures |

## Dev Agent Record

待 dev 填充。

## Change Log

- 2026-05-24: spec 创建（Plan `EPIC1-BMAD-DEV-ASSESS-2026-04-17`，用户 1B 决策 2026-05-22 锁定 Sprint 2 Day 9 插队）
