---
story_id: "LITE-5-7"
epic_id: "5"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P1"
estimate_hours: 3
depends_on: ["INFRA-002"]
blocks: []
sprint: "Sprint 3+"
supersedes: "_bmad-output/implementation-artifacts/epic-5/5-7-three-layer-memory-retrieval.md"
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
saves_hours: 2
trace:
  - "FR-MEM-04 (简化版, 单 Layer Graphiti 而非 3 层 fallback)"
  - "用户原话: round-7 Q2 (2026-04-15) + round-9 Q1 + 2026-05-13 核心闭环 + 2026-05-22 答疑 v2"
naming_note: "改名于 2026-05-24 — 旧名'三层记忆简化' 误导（用户 mental model 只有 2 系统, 见调研报告）"
---

# Story LITE-5.7: 两个记忆系统最小接通（Lite — 保 LanceDB + Graphiti 用户视角入口）

Status: ready-for-dev

> ⚠️ **2026-05-24 重写**: 旧 spec "三层记忆简化（禁 Layer 1/2/3）" 被证实**严重偏差** — 把 PRD §1.5 三层 fallback 跟用户的 2 系统混为一谈。详见 `_bmad-output/审查/2026-05-24-prd-epic-vs-spec-对比报告.md`。
>
> 本 spec 修正方向：**保留**用户已锁定的 2 个记忆系统（LanceDB vault_notes 笔记检索 + Graphiti 学习历程），只砍"3 层 fallback 调度 + Hot/Warm/Cold 归档"等过早优化逻辑。

## Story

As a 学习者,
I want **两个我已经口头确认的记忆系统**在 Sprint 2 末"最小可用":
- **系统 1 (LanceDB vault_notes)**: 我能精确检索我的个人笔记片段（语义搜索, bge-m3 向量, 已在跑）
- **系统 2 (Graphiti)**: 我的学习历程被记录（callout/error/calibration 写 episode）+ 出题时能查"X 和 Y 的关系"(search_facts),

So that 我使用检验白板时, 系统能用上我**原白板学习过程**做"极其针对性的考察"（用户 2026-05-13 核心闭环原话）。

## Acceptance Criteria

1. **Given** 用户在 Obsidian 保存任意 md (含节点 md, 含 callout) **When** Tauri plugin file-save hook 触发 **Then** plugin 调 `POST /index/refresh-changed` **And** backend `lancedb_index_service.schedule_note_index()` 异步分块 + bge-m3 embed + 增量写 LanceDB `vault_notes` 表（**这部分已在跑, AC #1 仅是行为约束保留**）

2. **Given** LITE-4-3 出题或 EXAM-001 评分调 `ContextService.get_recent_context(node_id, n=3)` **When** ContextService 内部实现 **Then**:
   - **路线 A (主路径, 永远跑)**: 读节点本地 md, regex parse 出最近 3 条 `[!tip]+`/`[!error]+`/`[!question]+` callout
   - **路线 B (Graphiti 增量, 失败降级)**: 调 `search_facts(query=node_id, max_results=3, group_id="vault:<vault_id>")` 取 Graphiti 中**与该节点关联的历史 facts**（如"用户上次说过 X 错"）
   - 路线 B 超时 1s 或抛异常 → **降级为路线 A 单独返回**, 不阻塞调用方

3. **Given** 用户写一个 callout 触发 add_episode（Story 1.16-callout-graphiti-hook 实施）**When** episode 入队 **Then** Graphiti 异步处理 → 节点 + edge + valid_at 时序写入 Neo4j

4. **Given** 用户后续触发 `search_facts("X 和 Y 的关系")` (未来 Story 提供 UI 入口) **When** Graphiti 查询 **Then** 能返回**所有历史 callout / wikilink / calibration vote** 中提到的 X-Y 关系

5. **Given** 性能约束 **When** `get_recent_context` 调用 **Then** P95 < 500ms（**路线 A < 200ms + 路线 B 1s 上限**）

6. **Given** 路线 B Graphiti 不可用 (Docker 关 / 7691 down) **When** 调用 **Then** 路线 A 单独返回, 标记 `graphiti_status: "degraded"` 在 metadata, 不抛异常

7. **Given** **不实施**的简化范围 **Then**:
   - ❌ 不做 PRD §1.5 完整 3 层 fallback 调度 (Graphiti → Neo4j fulltext → Cache 三 Tier) — 留 Sprint 4+
   - ❌ 不做 Hot/Warm/Cold 三层归档 (Story 5.8 已砍)
   - ❌ 不做 71x token 压缩
   - ❌ 不做跨节点 backlinks 扩展（节点本地 + Graphiti facts 即可）

## Tasks / Subtasks

- [ ] Task 1: 验证 LanceDB vault_notes 索引管道在跑 (AC: #1)
  - [ ] `backend/app/services/lancedb_index_service.py::schedule_note_index()` 已实现
  - [ ] `backend/app/api/v1/endpoints/index.py::refresh_changed_endpoint` 已实现
  - [ ] Tauri/Obsidian plugin `vault.on("modify")` → `POST /index/refresh-changed` 已接
  - [ ] **本 Story 不动这部分代码, 只验证 e2e 跑通**: 保存 md → 30s 内 vault_notes 表新增 record

- [ ] Task 2: 新建 `ContextService.get_recent_context(node_id, n=3)` (AC: #2)
  - [ ] `backend/app/services/context_service.py`
  - [ ] 路线 A: vault.read 节点 md + regex parse callout（< 200ms）
  - [ ] 路线 B: 调 `graphiti_client.search_facts(query=node_id, max_results=n, group_id=...)` (1s 超时)
  - [ ] 合并去重: 同一文本不重复返回
  - [ ] 单元测试: 路线 A only / 路线 B only / 双路 / Graphiti down 降级

- [ ] Task 3: Graphiti search_facts 节点级查询 (AC: #4)
  - [ ] 用 `build_vault_group_id(vault_id, subject_id, canvas_path)` from Story 2.5.Y
  - [ ] query 用 node_id 作 Lucene 查询
  - [ ] 单元测试: 节点无 facts → 返回 [] 不抛异常

- [ ] Task 4: 性能 P95 < 500ms (AC: #5)
  - [ ] aiofiles 异步读 md
  - [ ] Graphiti 1s 超时强制 cancel
  - [ ] 性能测试: 100 次调用 P95 < 500ms

- [ ] Task 5: 路线 B 降级路径 (AC: #6)
  - [ ] try/except 捕 GraphitiUnavailableError / TimeoutError
  - [ ] structlog 记录降级事件
  - [ ] metadata 加 `graphiti_status` 字段

- [ ] Task 6: 集成到 LITE-4-3 + EXAM-001
  - [ ] LITE-4-3 Task 1 路线 3 改调 `get_recent_context(node_id, n=3, types=["tip"])`
  - [ ] EXAM-001 评分调用 `get_recent_context(node_id, n=5, types=["error", "question"])`

- [ ] Task 7: 文档化"砍 vs 留"决策 (AC: #7)
  - [ ] Dev Notes 标记"3 层 fallback 留 Sprint 4+"
  - [ ] Sprint 4+ 加 Story `LITE-5-9-full-three-layer-fallback`（占位）

## Simplification Rules（修正后的边界）

| PRD §1.5 完整设计 | LITE-5-7 修正后 | 决策依据 |
|---|---|---|
| **LanceDB vault_notes 笔记检索** | ✅ **完全保留**（已在跑）| 用户 round-7 Q2 (2026-04-15) 原话锁定，砍掉 = 砍核心 UX |
| **Graphiti search_facts 节点级查询** | ✅ **保留**（路线 B, 1s 超时降级）| 用户 2026-05-13 核心闭环"原白板学习过程"原话 |
| **Graphiti add_episode 写 callout/vote/error** | ✅ 由 Story 1.16-callout-graphiti-hook + LITE-5-6 修正版 提供 | 学习历程必须被记录 |
| ❌ 3 层 fallback 调度 (Graphiti → Neo4j → Cache) | ❌ **不做** Sprint 1+2 | 单用户阶段无必要，留 FR-MEM-04 完整版到 Sprint 4 |
| ❌ Hot/Warm/Cold 异步归档 | ❌ **不做** | Story 5.8 已砍 (FR-MEM-06) |
| ❌ 71x token 压缩 | ❌ **不做** | 单用户阶段无必要 |
| ❌ 跨节点 backlinks 扩展 | ❌ **不做** | 节点本地 + Graphiti facts 够用 |

## Background Decision Trace

- **2026-04-15 round-7 Q2**: 用户原话"LanceDB 是用来精确的检索笔记文件夹的笔记片段才是对的吧？" — 锁定**系统 1**
- **2026-04-15 round-9 Q1**: 表格分工 "我最近错过什么 → Graphiti / 笔记内容检索 → LanceDB vault_notes" — 锁定**系统 2 + 2 系统分工**
- **2026-05-13 核心闭环文档**: 用户原话"批注是核心，我需要用我的个人记忆系统充分理解我使用原白板的学习过程" — 锁定**Graphiti = 学习历程**
- **2026-05-22 答疑 v2**: "Graphiti 个人记忆 = 读你所有 callout: Tips/Errors/Questions/Hints" — 终极确认
- **2026-05-24 偏差发现 + 修正**: Claude 之前 LITE-5-7 v1 把 PRD §1.5 三层 fallback (FR-MEM-04) 跟用户 2 系统混淆全砍, 用户指出偏差 → 4 并行 Agent 调研 → 本 spec v2 修正

## Dev Notes

### Architecture

```
LITE-4-3 出题
EXAM-001 评分
    ↓ 调用
ContextService.get_recent_context(node_id, n=3)
    ↓
    ├─ 路线 A (主, < 200ms): vault.read node.md → regex parse callout
    └─ 路线 B (增量, 1s timeout): graphiti.search_facts(query=node_id, group_id="vault:<vault_id>")
                                       ↓ 失败降级
                                  metadata.graphiti_status = "degraded"
```

并行运行的独立管道（不在本 Story 范围, 验证存在即可）:
```
Obsidian md 保存 → Tauri plugin → POST /index/refresh-changed
                                       → lancedb_index_service.schedule_note_index()
                                       → 异步 bge-m3 embed → LanceDB vault_notes
```

```
用户写 callout (Story 1.16-callout-graphiti-hook 提供)
LITE-5-6 calibration vote (修正版)
STORY-2-10 wikilink change
    ↓ 全部经过统一管道
episode_worker.add_episode(group_id="vault:<vault_id>")
    ↓
Graphiti (Neo4j 7691) → 之后 search_facts 可查
```

### File Paths
- 新建: `backend/app/services/context_service.py`
- 复用 (验证存在): `backend/app/services/lancedb_index_service.py`
- 复用 (验证存在): `backend/app/services/episode_worker.py::add_episode` (port 7691)
- caller 1: `backend/app/services/context_enrichment_service.py::assemble_simplified_context()` (LITE-4-3)
- caller 2: `backend/app/services/scorer_service.py::grade_with_context()` (EXAM-001)

### Testing
- 单元: `backend/tests/unit/test_context_service.py`
- 性能: `backend/tests/perf/test_context_service_latency.py`
- 降级路径: `backend/tests/integration/test_context_service_graphiti_down.py`
- e2e: 保存 md → 30s 后 search vault_notes 能查到（LanceDB 管道）

### Project Structure Notes
- 不再调用旧 5-7 的 `three_layer_memory_service.py` (已 [DEPRECATED])
- Sprint 4+ 可加 Story `LITE-5-9-full-three-layer-fallback` 实现 FR-MEM-04 完整 3 Tier
- 复用 Story 2.5.Y `build_vault_group_id()` 保 group_id 规约

### References
- **From 用户原话**: round-7 Q2 (2026-04-15) / round-9 Q1 / 2026-05-13 核心闭环 / 2026-05-22 答疑 v2
- **From 偏差调研**: `_bmad-output/审查/2026-05-24-prd-epic-vs-spec-对比报告.md`
- **From PRD**: §1.5 三层记忆 (FR-MEM-04 简化) + §2.4 校准回写
- 旧 spec ([DEPRECATED]): `epic-5/5-7-three-layer-memory-retrieval.md`

## UAT Script

> 1. 在 canvas-vault 选一个有 5+ `[!tip]+` callout 的节点 md
> 2. 写一个新 callout (Cmd+Shift+A → tip)
> 3. 保存 md (Cmd+S)
> 4. **等 30s**(LanceDB index) + **2min**(Graphiti episode batch — 见 STORY-2-10)
> 5. `Cmd+Shift+Q` 触发 quick exam
> 6. 看题目应引用**最近 3 条 tip + Graphiti facts** (如 "你之前提到过 X, 这次进一步问 Y")
> 7. 如果 Docker Graphiti 关闭 (port 7691 down), 题目仍能出 (路线 A 降级)

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| 路线 A callout parse | unit | `pytest backend/tests/unit/test_context_service_route_a.py` | 0 failures |
| 路线 B Graphiti search_facts | unit | `pytest backend/tests/unit/test_context_service_route_b.py` | 0 failures |
| 降级路径 (Graphiti down) | integration | `pytest backend/tests/integration/test_context_service_graphiti_down.py` | 路线 A 单独返回 |
| LanceDB vault_notes 已在跑 | e2e | save md → wait 30s → query vault_notes | record 新增 |
| P95 < 500ms | perf | `pytest backend/tests/perf/test_context_service_latency.py` | P95 < 500ms |
| group_id 规约 | static | `grep "build_vault_group_id" backend/app/services/context_service.py` | ≥ 1 match |

## Dev Agent Record

待 dev 填充。

## Change Log

- 2026-05-24 v1: spec 创建 — 旧名"三层记忆简化版", 误把 PRD §1.5 三层 fallback 跟用户 2 系统混淆, 全砍 LanceDB/Graphiti
- 2026-05-24 v2: 用户指出偏差 → 4 Agent 调研找回用户原话证据链 → **完全重写为"两个记忆系统最小接通"**, 保 LanceDB vault_notes + Graphiti search_facts 节点级查询, 估时 2h → 3h
