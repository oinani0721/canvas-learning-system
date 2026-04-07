# A6 Phase 0 — OpenSpec 追踪 + 后端 E2E 测试 Reference Card

> **性质**: 单页 reference card，下次需要追踪 A6 进展或做后端 E2E 时打开这份文件。
> **不是实施计划** — 不包含可执行任务；所有任务已于 2026-04-07 完成并归档。
> **不 cover 前端** — ReviewItem 尚无 Rate 按钮 + api-client 无 `/review/record` 方法，见 Non-Goals。

---

## ✅ 验证戳 (Verification Stamp)

| 时间 | 执行者 | 分支 | 结果 |
|---|---|---|---|
| 2026-04-07 | Claude Code | `main` + worktree `fix-concept-id-identity-unification`@`34c4152` | **全部验证通过** |
| 2026-04-07（第 2 次进入） | Claude Code | 文档追加（无代码变更） | **§C traceability 映射新增**（基于 A6-resolution-summary.md §3-§7 和 design.md §Deferred 的 grep 验证） |

### 验证证据

- **§A 的 3 个 OpenSpec 文件**: 3/3 存在 ✅
  - `openspec/changes/archive/2026-04-07-a6-phase0-fsrs-card-state-bucket-preservation/design.md` — `## Deferred (Future Changes)` §1-§5 完整
  - `docs/project-status/fr-exploration/A6-resolution-summary.md` — 存在但**不含** phase 0 fix 记录（无 commit hash `34c4152`/`8328264`、无 `test_review_service_legacy_bucket_round_trip.py`），符合 plan 原 warning
  - `openspec/specs/concept-identity/spec.md` — 3 个 scenario 完整；**Purpose = TBD 占位符已确认**（line 4）
- **§B 的 3 个测试文件**: 3/3 存在于 worktree ✅
  - `test_review_service_legacy_bucket_round_trip.py`（7059 bytes，Apr 7 09:08）
  - `test_card_states_compat_read.py`（6432 bytes，Apr 6 20:03）
  - `test_card_state_concurrent_write.py`（6254 bytes，Apr 6 19:08）
- **§B.1 单测**: `15 passed, 10 warnings in 0.50s` ✅ 精确匹配 plan 的 "15 passed in 0.5s" 预期
- **修复代码位置**: `.worktrees/fix-concept-id-identity-unification/backend/app/services/review_service.py:413`
  - 原 plan 说 "406 行附近"（verbatim: "406 行附近命中"）→ 实际 413 行，偏移 +7（方法 docstring 扩展导致）
- **Conftest fixture**: `backend/tests/conftest.py:227` 定义 `isolate_card_states_file`（plan 说 226-237，实际 227 起）
- **Worktree 存在**: `.worktrees/fix-concept-id-identity-unification` HEAD = `34c4152`（fix 提交）
- **OpenSpec archive commit**: `8328264 docs(openspec): archive a6-phase0-fsrs-card-state-bucket-preservation`（已在 main）

### 原 plan vs. 当前状态的小偏差

| Plan 声明 | 实际 | 影响 |
|---|---|---|
| `review_service.py:406` 是 fix 行 | 实际在 `:413` | 用下面 grep 命令定位即可，不影响可用性 |
| `conftest.py:226-237` 是 fixture | 实际起于 `:227` | 行范围偏移 1 行，含义不变 |
| A6-resolution-summary.md 可能没更新 phase 0 | 确认没更新 | 已列入 "follow-up，不在 scope" |

---

## §A · 最重要的 3 个 OpenSpec 追踪文件（按优先级）

### 🥇 第 1 名：archived design.md — 决策 + Deferred 清单

**绝对路径**:
```
openspec/changes/archive/2026-04-07-a6-phase0-fsrs-card-state-bucket-preservation/design.md
```

**打开它能回答的问题**:
- 根因：`review_service.py:413` 为什么是 silent data-loss bug（`## Context` 表格列出 5 个 explore agent 的 verdict，含 ChatGPT 的 4 个 false alarm）
- 为什么只修 1 个 P0：`## Goals / Non-Goals` + 3 个 Decision (D1 merge-vs-sidecar / D2 test file location / D3 archive order)
- **后续 5 个 change 的开盘清单**：`## Deferred (Future Changes)` 段落列出 §1-§5 名字、open question、为什么不在 phase 0 scope：

| § | Change 名字 | 等级 | 一句话说明 |
|---|---|---|---|
| §1 | `a6-phase1-relates-to-write-side-activation` | P0 | `add_relationship()` 有定义但零调用方，RELATES_TO 从未被写入 |
| §2 | `a6-phase1-fsrs-difficulty-integration-to-priority` | P0 | `fsrs_difficulty` 被计算但 priority 公式不读，"难度分层"只是文档声称 |
| §3 | `a6-phase1-frontend-edge-sync-pipeline` | P0 | 前端画边完全不调用 `/api/v1/sync/batch`，后端看不到用户画的图 |
| §4 | `a6-phase2-concept-name-path-guard-hardening` | P2 | `ConceptRef` 只挡 POSIX 路径，不挡 Windows/URL scheme |
| §5 | `a6-phase2-rag-faithfulness-ci-gate` | P2 | faithfulness check 存在但没 CI gate 卡住低分 PR |

---

### 🥈 第 2 名：A6-resolution-summary.md — 跨分支全局地图

**绝对路径**:
```
docs/project-status/fr-exploration/A6-resolution-summary.md
```

**打开它能回答的问题**:
- User 2 原问的 3 个问题（Q1 graph merging / Q2 RAG / Q3 FSRS）映射到哪些具体修复 / 测试覆盖率
- 哪些修复已在 main / 哪些还在 worktree branch

**⚠️ 已确认的 gap**（2026-04-07 验证）:
- 此文档 **不含** `test_review_service_legacy_bucket_round_trip.py`
- 不含 commit hash `34c4152`（phase 0 fix）或 `8328264`（archive）
- 不含 "bucket preservation" 相关措辞
- **Follow-up**: 下次谁实施 `a6-phase1-*` 时可顺手补一条 phase 0 记录

---

### 🥉 第 3 名：openspec/specs/concept-identity/spec.md — 累积的规范契约

**绝对路径**:
```
openspec/specs/concept-identity/spec.md
```

**当前内容**：1 个 Requirement `FSRS Card State Legacy Bucket Preservation On Save` + 3 个 `#### Scenario:`
  1. Round-trip preserves both buckets
  2. Save with empty legacy bucket is byte-equivalent to UUID-only case
  3. Save preserves new UUID entries written via save_card_state

**打开它能回答的问题**:
- 审查新 PR 是否破坏 FSRS 双桶不变式 → 这里的 3 个 scenario 是 acceptance criteria
- 将来的 `a6-phase1-*` 归档时 spec 累积在哪 → 同一个文件

**⚠️ GOTCHA（仅提醒，不是任务）**:
line 4 是 CLI 自动生成的 `## Purpose` 占位符：
```markdown
## Purpose
TBD - created by archiving change a6-phase0-fsrs-card-state-bucket-preservation. Update Purpose after archive.
```
用户决策：**不在本 reference card 的 scope 里处理**；下次 phase 1 change 归档时顺手把 Purpose 填真内容。

---

### 为什么没选另外 3 个候选

| 候选文件 | 为什么不在 Top 3 |
|---|---|
| `.../proposal.md` | 叙述性（ChatGPT review 链 + 发现过程），与 `design.md` 的 Context 冗余。onboard 新人有用，日常追踪 forward value 低 |
| `.../tasks.md` | 纯实施 checklist，所有 `[x]` 完成。前向追踪价值为零 |
| `docs/project-status/fr-exploration/A6.md` | User 2 原问题，**未被修改**。查原问用，追踪修复状态 → `A6-resolution-summary.md` 更高效 |

---

## §C · A6.md Q1/Q2/Q3 → 3 个 OpenSpec 文件的 traceability 映射

> **目的**：§A 从"工程结构"视角选 Top 3（决策中枢 / 全局地图 / 规范契约）。本段从 **user-intent**（A6.md 原题 Q1/Q2/Q3）视角补上映射，显示 Top 3 选择**同时满足**两个视角。
>
> **信息论角度的选择正当性**：每个 Q 至少被 2 个 Top 文件命中，Q3 被全部 3 个命中，**没有**任何 Q 被全部 3 个文件漏掉 — 详见 C.4。

### C.1 A6.md 原题重述（User 2 verbatim）

源文件: `docs/project-status/fr-exploration/A6.md`

- **Q1（图谱合并）**: 白板节点 edges 图谱 vs 概念 edges 图谱，是否合并为一？能否直接用 Graphiti 工具包？前端 edges 涉及增加和修改，真的有成熟方案构建一个可读的关系图谱吗？
- **Q2（RAG 语义检索）**: "这里的 RAG 语义检索是什么？用了哪一个 RAG？是笔记片段的精确检索返回的 RAG 吗？"
- **Q3（FSRS 评分历史）**: "FSRS 评分历史如何融入关系图谱？对使用检验白板实际有什么影响？这个算法在我们的变量中是如何进行调用使用的？"

### C.2 三层视角：Surface fix → Phase 0 fix → Deferred deep gap

| Q | Surface fix（已在 `origin/main`） | Phase 0 fix（2026-04-07） | Deferred deep gap |
|---|---|---|---|
| **Q1 图谱合并** | `fix-fr-kg-04-schema-drift-and-sync-hardening` 加权融合 `CANVAS_EDGE (1.0) + RELATES_TO (0.7)`（不合并物理图谱，在查询层加权融合） | — | design.md §Deferred §1 `a6-phase1-relates-to-write-side-activation` (P0, RELATES_TO 写入路径零调用方) + §3 `a6-phase1-frontend-edge-sync-pipeline` (P0, 前端画边不同步) |
| **Q2 RAG** | 3 个归档 change 合成 Agentic RAG 5 路并行 + L1 LLM 路由 + Faithfulness + CRAG fallback（`agentic-rag-l1-llm-router` / `fix-rag-faithfulness-and-add-crag-quality-loop` / `fix-rag-transform-and-episode-isolation`） | — | design.md §Deferred §5 `a6-phase2-rag-faithfulness-ci-gate` (P2, Faithfulness 有 check 但无 CI gate 门) |
| **Q3 FSRS** | `fix-concept-id-identity-unification` ConceptRef 身份契约统一（**worktree 分支未 merge**，让 memory_service 按 UUID 直查 `review_service.get_fsrs_state()`） | `a6-phase0-fsrs-card-state-bucket-preservation` 双桶 preservation，防止 `_save_card_states` silent data loss | design.md §Deferred §2 `a6-phase1-fsrs-difficulty-integration-to-priority` (P0, `fsrs_difficulty` 被算但 `question_generator.py:202-206` priority 公式不读) |

### C.3 Q × 文件 covering matrix（3 Top 文件 × 3 Q）

| Q | design.md | A6-resolution-summary.md | concept-identity/spec.md |
|---|---|---|---|
| **Q1** | §Context 表第 1 行 RELATES_TO verdict + §Deferred §1 + §Deferred §3 | ★ §3 "Q1 图谱合并：CANVAS_EDGE vs RELATES_TO" 全节（解答/commits/证据/决策/限制 共 5 小节）+ §6 Q1 测试覆盖 (13 unit + 7 e2e: `test_kg_relevance_weighted.py`, `test_a11_kg_relevance_e2e.py`) + §7 `fix-fr-kg-04-schema-drift-and-sync-hardening` | **无直接契约**（spec 只 cover FSRS 双桶，与图谱合并不相关） |
| **Q2** | §Deferred §5 (`rag-faithfulness-ci-gate`) | ★ §4 "Q2 RAG 语义检索" 全节（解答/commits/证据/决策 共 4 小节）+ §6 Q2 测试覆盖 (25 unit) + §7 三个 Q2 archived changes | **无直接契约** |
| **Q3** | ★ §Context 表（phase 0 根因 silent data loss）+ §Decisions D1/D2/D3 + §Deferred §2 | §5 "Q3 FSRS 评分历史如何融入" 全节 ⚠️ **未更新 phase 0 fix** + §6 Q3 测试覆盖 (77 unit on worktree 分支) + §7 `fix-concept-id-identity-unification` 未归档说明 + §9 "Q3 worktree 分支 merge 决策 待 review 后定" | ★★ **3 个 scenario 全部是 Q3 相关**：`FSRS Card State Legacy Bucket Preservation On Save`（round-trip / empty-legacy / save preserves new UUID） |

**Legend**:
- ★ = 该文件是该 Q 的主要回答点
- ★★ = 该文件是该 Q 的唯一正式契约

### C.4 为什么这 3 个 OpenSpec 文件是 Top 3（user-intent 答案）

- **design.md** 回答所有 3 个 Q 的 **"为什么 surface fix 不够"** — Context 表（5 parallel Explore agents 的 verdict）+ Deferred §1~§5（每一条都挂钩到某个 Q 的 deep gap）。这是 A6 系列的 **真相源 / 诚实版本**。没有它，读者会以为 A6.md 的 3 问已 ✅ 解决；有它，读者知道真实解决度 ≈ 30%（4 个 P0 中仅 1 个被 phase 0 修）
- **A6-resolution-summary.md** 回答所有 3 个 Q 的 **"surface fix 在哪 + 覆盖率"** — §3/§4/§5 逐题 walkthrough（每节有解答/commits/证据/决策 4 小节），§6 测试覆盖总览（Q1: 13u+7e / Q2: 25u / Q3: 77u），§7 OpenSpec 规范化证据。这是 A6 系列的 **全景地图 / 乐观版本**
- **concept-identity/spec.md** 只回答 Q3 的 **"不变式 acceptance criteria"** — 3 个 scenario 锁住 phase 0 fix 的语义。这是 A6 系列在 phase 0 唯一触达的 **正式契约**。Q1/Q2 没有对应 spec 条目，因为它们的修复已由其他 archived change 累积进 `openspec/specs/algo-rag/spec.md`、`openspec/specs/algo-question/spec.md` 等（详见 A6-resolution-summary.md §7）

**信息论角度的选择理由**:
- **每个 Q 至少命中 2 个 Top 文件**（冗余带来容错）
- **Q3 命中全部 3 个**（phase 0 fix 本身就是 Q3 相关，自然覆盖全栈）
- **Q1/Q2 各命中 2 个**（spec.md 不 cover，但 design.md + summary.md 已足够回答 "为什么不够" + "现状在哪"）
- **没有任何一个 Q 被 3 个文件全部漏掉** ← 这是 "Top 3" 选择正当性的核心证明

---

## §B · Claude Code Desktop 后端 E2E 测试文件清单

**前提**：下次要做 "跑后端 + 命中真实端点 + 检查磁盘状态" 的 E2E 验证时用。

### B.0 先决条件检查

```bash
# 1. 工作目录 = worktree 分支
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.worktrees/fix-concept-id-identity-unification/backend

# 2. venv 存在（在主 repo backend/ 下，worktree 共享）
/Users/Heishing/Desktop/canvas/canvas-learning-system/backend/.venv/bin/python --version
# 期望: Python 3.14.x

# 3. 确认 fix 在当前 checkout 上（精确行号 = 413）
grep -n "combined = {\*\*self._legacy_card_states" app/services/review_service.py
# 期望: 413:                combined = {**self._legacy_card_states, **self._card_states}
```

### B.1 单测路径（最快、无副作用、**首选**）

**执行命令**:
```bash
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.worktrees/fix-concept-id-identity-unification/backend
/Users/Heishing/Desktop/canvas/canvas-learning-system/backend/.venv/bin/pytest \
  tests/unit/test_review_service_legacy_bucket_round_trip.py \
  tests/unit/test_card_states_compat_read.py \
  tests/unit/test_card_state_concurrent_write.py \
  -x -v
```

**已验证结果 (2026-04-07)**: `15 passed, 10 warnings in 0.50s`

**文件清单**:
| 路径 | 用途 | 验证状态 |
|---|---|---|
| `backend/tests/unit/test_review_service_legacy_bucket_round_trip.py` | A6 Phase 0 修复的**直接回归测试**：3 scenario | ✅ 3 tests pass |
| `backend/tests/unit/test_card_states_compat_read.py` | Load 端双桶回归（9 scenario） | ✅ 9 tests pass |
| `backend/tests/unit/test_card_state_concurrent_write.py` | `async with _card_states_lock` 并发安全（3 scenario） | ✅ 3 tests pass |
| `backend/tests/conftest.py:227` | `isolate_card_states_file` fixture 定义 | ✅ 存在 |

### B.2 真实 HTTP 端点路径（完整 E2E、写真实磁盘）

**启动 backend**:
```bash
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.worktrees/fix-concept-id-identity-unification/backend
/Users/Heishing/Desktop/canvas/canvas-learning-system/backend/.venv/bin/python start_server.py --port 8001 --no-reload
# 健康检查: curl http://127.0.0.1:8001/api/v1/health
```

**触发 save**:
```bash
curl -X PUT http://127.0.0.1:8001/api/v1/review/record \
  -H "Content-Type: application/json" \
  -d '{
    "canvas_name": "test-canvas",
    "node_id": "a1b2c3d4-5678-4def-89ab-cdef01234567",
    "score": 75
  }'
```

**验证磁盘**:
```bash
cat backend/data/fsrs_card_states.json | python -m json.tool
# 期望: 包含刚才 POST 的 UUID key + 原有 entries 全部保留
```

**相关文件清单**:
| 路径 | 用途 |
|---|---|
| `backend/app/api/v1/endpoints/review.py:1062-1148` | `PUT /api/v1/review/record` 端点 |
| `backend/app/services/review_service.py:397-430` | `_save_card_states()` 方法本体（fix 行在 :413） |
| `backend/data/fsrs_card_states.json` | 持久化文件 — E2E 最终检查对象 |
| `backend/start_server.py` | Uvicorn 启动脚本，默认 127.0.0.1:8001 |
| `backend/tests/e2e/test_review_fsrs_degradation.py` | 现有 review/FSRS 相关 E2E 测试，参考 fixture 用法 |
| `backend/tests/e2e/test_health_endpoint.py` | 现有 health endpoint E2E，示范 `client` fixture + 断言 pattern |
| `backend/tests/e2e/conftest.py` | E2E 专用 fixture（`client` TestClient + canvas mocks + performance timers） |

### B.3 污染防护 — 用临时 FSRS 文件

**风险**：直接对 `backend/data/fsrs_card_states.json` 做 E2E 会污染真实开发数据。

**两种隔离方式**:

**方式 A（最干净）** — 跑**单测** §B.1，自动用 tmp_path，无污染风险。

**方式 B（真跑 server 时）** — 先备份再跑:
```bash
# 备份
cp backend/data/fsrs_card_states.json backend/data/fsrs_card_states.json.bak-$(date +%s)

# 预埋 mixed 桶 fixture（可选，验证双桶保留）
cat > backend/data/fsrs_card_states.json <<'EOF'
{
  "f4d10d8b-1234-4abc-89ab-cdef01234567": "{\"stability\":1.0,\"difficulty\":5.0}",
  "legacy_node_123": "{\"stability\":3.0,\"difficulty\":6.0}"
}
EOF

# ... 跑 E2E ...

# 恢复
mv backend/data/fsrs_card_states.json.bak-* backend/data/fsrs_card_states.json
```

### B.4 Gotchas

| # | 陷阱 | 如何规避 |
|---|---|---|
| G1 | `isolate_card_states_file` fixture **只对 pytest 有效**，手动跑 server 需要自己备份/恢复 | 用 B.3 方式 B，或干脆走 B.1 单测路径 |
| G2 | `start_server.py` 默认 **8001** 端口（不是 8000） | 启动命令显式 `--port 8001`，curl 也用 8001 |
| G3 | ReviewService 是 singleton — 两次跑之间 in-memory 状态不重置 | 先 kill server 再重启，或接受这是设计的跨请求持久化 |
| G4 | `.env` 里 `USE_FSRS=false` 会走 `ebbinghaus-fallback`，响应里 `fsrs_state` 为 None（修复仍生效但 response 观感不同） | 确认 `.env` `USE_FSRS=true` 或接受 degraded 模式 |
| G5 | Neo4j / LanceDB / Graphiti **不是** `/api/v1/review/record` 的依赖 | 测 A6 时不用 `docker compose up`，省 30s |
| G6 | parallel session p0-2 给 `memory.py` 加了 `SIDECAR_OBSERVER_TOKEN` 鉴权，但**只影响** `/extract-conversation`，**不影响** `/review/record` | 不需要 `X-Canvas-Observer-Token` header 来测 A6 |
| G7 | 代码 fix 在 **worktree** 分支 `fix-concept-id-identity-unification`@`34c4152`，main 分支上**没有**（仅 OpenSpec archive 在 main） | E2E 必须 `cd .worktrees/fix-concept-id-identity-unification/backend`，在 main repo 跑会测到旧的 buggy 代码 |

### B.5 Non-Goals（明确排除）

❌ **前端 E2E**：`ReviewItem.tsx` 无 Rate 按钮，`api-client.ts` 无 `/review/record` 调用 → 触发 save 的 UI 路径**不存在**。要跑前端 → 先实施 `a6-phase1-frontend-edge-sync-pipeline`
❌ **Tauri desktop E2E**：Tauri 应用未编译，前端功能无法验证
❌ **`mcp__claude-in-chrome__*` 浏览器自动化**：基于上两条理由没东西可浏览
❌ **Purpose 占位符补齐**：用户选 "仅提醒不包含任务"
❌ **Deferred §1-§5 的任何实施**
❌ **更新 A6-resolution-summary.md 加入 phase 0 条目**（是 follow-up）
❌ **对 main repo 或 worktree 的任何 commit/push**

---

## Critical Files 速查表

> 下次一开 session 要查 A6 相关代码时按此顺序打开。

### OpenSpec 追踪（§A 前 3 名）
1. `openspec/changes/archive/2026-04-07-a6-phase0-fsrs-card-state-bucket-preservation/design.md`
2. `docs/project-status/fr-exploration/A6-resolution-summary.md`
3. `openspec/specs/concept-identity/spec.md`

### 代码修复（worktree 分支上）
- `.worktrees/fix-concept-id-identity-unification/backend/app/services/review_service.py:413` — **fix 本体** (`combined = {**legacy, **uuid}`)
- `.worktrees/fix-concept-id-identity-unification/backend/tests/unit/test_review_service_legacy_bucket_round_trip.py` — 回归测试

### 后端 E2E 切入点
- `backend/app/api/v1/endpoints/review.py:1062-1148` — `PUT /api/v1/review/record`
- `backend/tests/conftest.py:227` — `isolate_card_states_file` fixture
- `backend/tests/e2e/conftest.py` — E2E client + canvas mocks
- `backend/start_server.py` — 启动脚本（默认 8001）

### 源头文档
- `docs/project-status/fr-exploration/A6.md` — User 2 原问题（未修改，参考用）

---

## Bailout

下次打开这份 plan 发现：

- §B.2 `PUT /review/record` 返回 404 → 检查是不是 checkout 了旧分支（main 上**没有** `_save_card_states` 的 merge 修复）
- 单测 fail 且错误是 `AttributeError: '_legacy_card_states'` → 代码 fix 没在当前 branch 上，`cd .worktrees/fix-concept-id-identity-unification`
- §A 第 2 名 `A6-resolution-summary.md` 里看不到 phase 0 fix 记录 → 这是已知 gap（见"验证戳"），不是 plan 的问题

---

**维护**: 本文档是 frozen reference card。Phase 1 落地后，开一份新的 `A6-phase1-reference-card.md` 而非修改本文件。
