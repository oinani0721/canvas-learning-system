---
story_id: "1.16-callout-graphiti-hook"
epic_id: "1"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P1"
estimate_hours: 5
depends_on: ["INFRA-002", "STORY-2-10-wikilink-graphiti-sync"]
blocks: ["LITE-4-3", "LITE-5-7"]
sprint: "Sprint 2 (修正方案 A, 2026-05-24; V-07 patch 2026-05-26)"
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
decision_trace: "round-9 Q1 + 2026-05-13 核心闭环 + 2026-05-22 答疑 v2 + 2026-05-24 偏差修正 + 2026-05-26 ChatGPT V-07 修复"
trace:
  - "FR-MEM-01 (学习历程 episode 记录)"
  - "FR-MEM-05 (Tips/Errors/Questions/Hints 写入 Graphiti)"
  - "FR-WIKI-CONTEXT (V-07 修复 — callout 带双链上下文写 Graphiti)"
---

# Story 1.16-callout-graphiti-hook: Callout 写 Graphiti Episode 自动 hook

Status: ready-for-dev

> **2026-05-24 新建**: 修正方案 A 第 4 步 — 让用户日常写 callout 时自动写入 Graphiti **学习历程系统**，激活用户 2026-05-13 锁定的"个人记忆系统理解原白板学习过程"诉求。复用 STORY-2-10 的 events_queue 管道，零额外基础设施。

## Story

As a 学习者,
I want **每次我在 canvas-vault 写 `[!tip]+` / `[!error]+` / `[!question]+` / `[!hint]+` callout 时**，系统自动把这条 callout 作为 episode 写入 Graphiti 学习历程,
So that 未来出题、评分、检验白板时, 系统能用 `search_facts` 调出我**之前说过的话**，做"极其针对性的考察"（用户 2026-05-13 核心闭环原话）。

## Acceptance Criteria

1. **Given** 用户在 obsidian-plugin 用 `Cmd+Shift+A` 触发 callout 命令（Story 1.16 已实施 7 callout 类型） **When** callout 写入 md **Then** plugin 通过 `metadataCache.on("changed")` 监听到 callout 新增 / 修改

2. **Given** plugin 监测到 callout 变化 **When** 计算 delta **Then** plugin 调 `POST /api/v1/event/callout` 带 body（**V-07 修复 2026-05-26：增加 wikilink 双链上下文字段**）:
   ```json
   {
     "kind": "callout_change",
     "action": "added" | "modified" | "removed",
     "node_id": "eigenvalue",
     "node_path": "节点/eigenvalue.md",
     "source_board": "原白板/线代.md" | "检验白板/线代期末.md" | null,
     "callout_type": "tip" | "error" | "question" | "hint" | "warning" | "note" | "info",
     "callout_text": "callout 的文本内容",
     "callout_anchor": "唯一锚 — 如 sha256(node_path+offset)",
     "out_links": ["determinant", "matrix-rank"],
     "in_links": ["spectral-theorem", "PCA-应用"],
     "path_trace": ["原白板/线代.md", "节点/matrix-rank.md", "节点/eigenvalue.md"],
     "timestamp": "2026-05-24T14:30:00Z",
     "vault_id": "<configured-vault-id>"
   }
   ```
   **字段语义** (V-07 修复关键):
   - `node_id`: 当前节点稳定 ID (vault 内 unique, **新加**)
   - `source_board`: 这条 callout 是在哪个白板**通过 wikilink 跳到此节点后**写的 (从 plugin workspace last-focused board 取, 没有则 null, **新加**)
   - `out_links[]`: 当前节点正文中 `[[wikilink]]` 解析后的目标 node_id 数组 (用 obsidian `metadataCache.resolvedLinks` 取, **新加**)
   - `in_links[]`: 当前节点被哪些节点反向链接 (用 `metadataCache.getBacklinksForFile()` 取, **新加**)
   - `path_trace[]`: 用户从哪个白板出发, 经过哪几个节点跳到此节点 (plugin 维护 navigation history, max 5 跳, **新加**)
   - **修复理由**: 旧 schema 只存"句子", 不存"探索路径". V-07 修复后, 未来 `search_facts(query="<node_id> 的关系")` 才能查出"用户在原白板 X 沿 A→B→C 探索后, 对 C 写了 tip Y" 的完整学习上下文

3. **Given** backend 收 event **When** endpoint 处理 **Then** **复用 STORY-2-10 的 events_queue**（不新建表）：写入 `callout_events` LanceDB 临时表（与 `wikilink_events` 并列），返回 `202 Accepted`，< 100ms

4. **Given** hourly cron 触发（与 STORY-2-10 同一 `wikilink_batch_sweep.py` 扩展，**不另起 cron**） **When** sweep 启动 **Then** 读 `callout_events` 未消费记录, 按 `vault_id` 分组, **逐条**调 add_episode (不再 batch json — V-09 修复方向, 保留自然语言可检索性):
   ```python
   # V-07 修复: episode_body 不再只塞 callout_text, 必须自然语言化关系
   episode_body = (
       f"用户在 {event.source_board or '独立节点'} 中, "
       f"经过路径 {' → '.join(event.path_trace)}, "
       f"对节点 [[{event.node_id}]] 写了一条 {event.callout_type} 类型反思: "
       f"\"{event.callout_text}\". "
       f"此节点的关系语境: 出链到 {event.out_links}, 被 {event.in_links} 反向引用."
   )
   add_episode(
     name=f"callout_{event.callout_anchor[:12]}_{event.timestamp}",
     episode_body=episode_body,
     source="callout_sync",
     source_description=f"callout {event.callout_type} @ {event.node_id}",
     group_id=f"vault:{vault_id}",
     reference_time=event.timestamp,
   )
   ```
   **修复理由 (V-07 + V-09)**: 旧设计 batch json.dumps → Graphiti 只能存"字符串", 不能用 `search_facts("X 和 Y 的关系")` 检索关系网. 新设计每 callout 一条自然语言 episode, **保留 wikilink 双链关系** + Graphiti embedding 可检索性

5. **Given** 同一 callout `callout_anchor` 重复（用户改一字保存多次）**When** sweep 处理 **Then** 用 Graphiti `valid_at` / `invalid_at` 表达版本演化（旧版 invalid_at = 新版 valid_at）— **激活 PRD §1.5 时序追踪能力**

6. **Given** 用户删除一个 callout (action: "removed") **When** sweep 处理 **Then** Graphiti episode 标 `invalid_at = removal_time`，**不物理删除** (历史可回溯)

7. **Given** `add_episode` 失败 **When** 重试 **Then** 复用 STORY-2-10 重试机制 (3 次 → failed_events 表)

8. **Given** 后续 LITE-5-7 路线 B 调用 `search_facts(query=node_id)` **When** Graphiti 查询 **Then** 能返回此节点的所有 callout episode (Tips/Errors/Questions/Hints) — **闭环达成**

## Tasks / Subtasks

- [ ] Task 1: plugin 侧 callout delta 计算 (AC: #1, #2)
  - [ ] `frontend/obsidian-plugin/src/callout-sync.ts` 新建
  - [ ] 复用 Story 2.4 已实施的 callout parser (`callout.ts` 严格协议 regex)
  - [ ] 监听 `metadataCache.on("changed")`, 维护 in-memory cache `Map<filePath, Map<callout_anchor, callout_text>>`
  - [ ] 计算 added / modified / removed delta
  - [ ] 单元测试: 加 callout / 改 callout / 删 callout / 同时改多个

- [ ] **Task 1.5: 抓 wikilink 双链上下文 (V-07 修复关键, AC: #2)**
  - [ ] `frontend/obsidian-plugin/src/wikilink-context.ts` 新建
  - [ ] `getOutLinks(file)`: 读 `app.metadataCache.resolvedLinks[file.path]` → 提取 target node_id 数组
  - [ ] `getInLinks(file)`: 调 `app.metadataCache.getBacklinksForFile(file)` → 提取 source node_id 数组
  - [ ] `getPathTrace()`: 维护 plugin 级 navigation history (workspace `on('file-open')` push, max 5)
  - [ ] `getSourceBoard()`: 从 history 取最近一个 `原白板/` 或 `检验白板/` 目录下的 file path
  - [ ] callout-sync.ts 调用此 helper 填 `out_links / in_links / path_trace / source_board`
  - [ ] 单元测试: 5 个边界 (无 wikilink / 无 backlink / history 空 / source_board 不在白板目录 / max 5 截断)

- [ ] Task 2: plugin POST event 到 backend (AC: #2)
  - [ ] 复用 PLUGIN-001 的 `backend-client.ts::callBackend()` helper
  - [ ] body schema 严格匹配 AC#2
  - [ ] retry 3 次指数退避（与 STORY-2-10 一致）

- [ ] Task 3: backend endpoint `POST /api/v1/event/callout` (AC: #3)
  - [ ] 扩展 STORY-2-10 已新建的 `backend/app/interfaces/api/event.py`
  - [ ] handler 写 `callout_events` 表（并列 wikilink_events）
  - [ ] 单元测试: concurrent write 50 events

- [ ] Task 4: callout_events 表 schema (AC: #3) — **V-07 修复: 扩展 schema**
  - [ ] LanceDB 临时表 schema:
    ```python
    {
      "event_id": "uuid",
      "vault_id": "string",
      "node_id": "string",          # V-07 新加
      "node_path": "string",
      "source_board": "string?",    # V-07 新加 (nullable)
      "callout_anchor": "string",
      "callout_type": "string",
      "callout_text": "string",
      "out_links": "list<string>",  # V-07 新加
      "in_links": "list<string>",   # V-07 新加
      "path_trace": "list<string>", # V-07 新加 (max 5)
      "action": "string",           # added | modified | removed
      "timestamp": "datetime",
      "retry_count": "int",
      "consumed_at": "datetime?"
    }
    ```

- [ ] Task 5: sweep 扩展支持 callout (AC: #4)
  - [ ] 扩展 `backend/scripts/wikilink_batch_sweep.py` 同时 sweep `wikilink_events` + `callout_events`
  - [ ] **不另起 cron** — 复用同一 hourly trigger
  - [ ] callout episode_body schema 跟 wikilink 不同 (json.dumps callouts list)

- [ ] Task 6: 时序追踪 valid_at / invalid_at (AC: #5, #6)
  - [ ] 同 callout_anchor 第二次出现 → 查上次 episode → invalidate
  - [ ] action=removed → invalid_at = removal_time
  - [ ] 单元测试: 模拟改 callout 多次, Graphiti episode 数 N + invalid_at 链正确

- [ ] Task 7: 重试机制 (AC: #7)
  - [ ] 完全复用 STORY-2-10 Task 7 的 failed_events 路径

- [ ] Task 8: 集成测试 (AC: #8)
  - [ ] e2e: plugin 写 callout → 1h cron → `search_facts(query=node_id)` 能返回此 callout

## Background Decision Trace

- **2026-04-15 round-9 Q1**: 用户表格"我最近错过什么 → Graphiti" — 锁定**Graphiti = 学习历程记录**
- **2026-05-13 核心闭环原话**: "**批注是核心**，我需要用我的**个人记忆系统**充分理解我使用原白板的**学习过程**" — 锁定 callout 必入 Graphiti
- **2026-05-22 答疑 v2 表格**: "Graphiti 个人记忆 = 读你所有 callout: Tips/Errors/Questions/Hints" — 终极确认 callout → Graphiti
- **2026-05-24 偏差发现**: Claude LITE-4-3 v1 错砍 `search_memories` → 用户提示偏差 → 4 Agent 调研发现"两个记忆系统"被砍 → **本 Story 新建为修正方案 A 第 4 步**

## Dev Notes

### Architecture

```
用户 Cmd+Shift+A 写 callout
    ↓ md 保存
plugin: callout-sync.ts (delta calc, 复用 callout.ts parser)
    ↓ POST /api/v1/event/callout
backend: events_queue.callout_events (LanceDB, 并列 wikilink_events)
    ↓ hourly cron (复用 STORY-2-10 同一 sweep, 不另起)
backend: wikilink_batch_sweep.py (扩展支持 callout)
    ↓ group by vault_id
backend: episode_worker.add_episode(name="callout_batch_...", group_id="vault:<vault_id>")
    ↓
Graphiti (Neo4j 7691)
    ↓ 未来 LITE-5-7 路线 B + 检验白板出题 调
search_facts(query=node_id, max_results=3)
    ↓
返回此节点历史 callouts (Tips/Errors/Questions/Hints) ✓ 学习历程闭环
```

### File Paths
- plugin: `frontend/obsidian-plugin/src/callout-sync.ts`（新建）
- plugin entry: `frontend/obsidian-plugin/src/main.ts` 注册 CalloutSync
- backend endpoint: `backend/app/interfaces/api/event.py`（扩展 STORY-2-10 已建文件）
- backend cron: `backend/scripts/wikilink_batch_sweep.py`（扩展支持 callout）
- backend schema: `backend/app/infra/lancedb_init.py`（加 callout_events 表）

### Testing
- 单元: `frontend/obsidian-plugin/tests/callout-sync.test.ts`
- 集成: `backend/tests/integration/test_callout_graphiti_sync.py`
- e2e: 模拟用户写 5 个 callout + cron + search_facts → 返回 5 条

### Project Structure Notes
- **不新建基础设施**: 复用 STORY-2-10 的 events_queue + sweep cron + episode_worker
- group_id 规约: 复用 `build_vault_group_id()` (Story 2.5.Y)
- callout_anchor 唯一性: `sha256(node_path + offset_in_md)` — 用户重命名节点时新 anchor (旧 invalid_at)

### References
- **From 用户原话**: round-9 Q1 / 2026-05-13 核心闭环 / 2026-05-22 答疑 v2
- **From 偏差调研**: `_bmad-output/审查/2026-05-24-prd-epic-vs-spec-对比报告.md`
- **From STORY-2-10**: `_bmad-output/implementation-artifacts/epic-2/2-10-wikilink-graphiti-sync.md` (复用其管道)
- **From PRD**: §1.5 Graphiti add_episode + valid_at/invalid_at 时序追踪
- **From Story 2.4**: callout parser 严格协议 (复用)

## UAT Script

> 1. canvas-vault 选一个节点 md
> 2. `Cmd+Shift+A` 写一个 `[!tip]+` callout（"X 概念其实是 Y"）
> 3. 保存 md
> 4. **等 1-60 分钟**（或手动跑 sweep cron）
> 5. 触发 Claudian skill 或 plugin command 调 `search_facts(query="<节点名>")`
> 6. 应返回你刚才写的 tip 内容
> 7. 修改这个 callout（"X 概念其实是 Y2"），重复 4-5 步
> 8. 应返回 v2 + v1 标 invalid_at（时序追踪 OK）

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| plugin delta calc | unit | `npm test -- callout-sync.test.ts` | 0 failures |
| backend endpoint < 100ms | perf | `pytest backend/tests/perf/test_event_callout_latency.py` | P95 < 100ms |
| callout_events 写入 | unit | `pytest backend/tests/unit/test_callout_events_queue.py` | 0 failures |
| sweep 扩展支持 callout | unit | `pytest backend/tests/unit/test_sweep_callout.py` | 0 failures |
| valid_at/invalid_at 链 | unit | `pytest backend/tests/unit/test_callout_timeseries.py` | 0 failures |
| 复用 STORY-2-10 管道 | static | `grep "wikilink_batch_sweep" backend/scripts/wikilink_batch_sweep.py` | 含 callout sweep 逻辑 |
| e2e callout → search_facts | e2e | `pytest backend/tests/e2e/test_callout_graphiti_e2e.py` | 返回所写 callout |

## Dev Agent Record

待 dev 填充。

## Change Log

- 2026-05-24: spec 新建（修正方案 A 第 4 步, Plan `EPIC1-BMAD-DEV-ASSESS-2026-04-17`）— 用户指出"三层记忆"偏差 → 4 Agent 调研找回 round-9/13/22 用户原话锁定 Graphiti = 学习历程 → 本 Story 提供 callout → Graphiti 自动 hook
- **2026-05-26 V-07 修复** (ChatGPT Deep Research 审计 CRITICAL #7 `CALL_OUT_OF_GRAPH`): AC#2 / AC#4 / Task 1.5 (新) / Task 4 schema / `2-10-wikilink-graphiti-sync` 共用字段 — callout 写 Graphiti 必带 `node_id / source_board / out_links / in_links / path_trace`. **修复理由**: 旧设计 callout episode 只存句子不存学习上下文 → 未来 `search_facts("X 和 Y 的关系")` 查不出探索路径 → 直接违背用户 2026-05-13 核心闭环原话 "批注+双链探索+个人记忆系统". estimate_hours 3h → 5h (+2h for Task 1.5)
