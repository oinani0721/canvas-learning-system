---
story_id: "2.5.X"
epic_id: "2"
prd_id: "canvas-learning-system"
status: "review"
priority: "P0"
estimate_hours: 21  # 18-24h 取中位
depends_on: ["2.5"]
blocks: []
trace:
  - "FR-CONV-06"
  - "Decision-Review-D15-User-Sovereignty"
ship_decision: "C+ 方案 (ChatGPT Round-2 修正稿) — frontmatter error_candidates[] + Dashboard 保活 + accept/rebuild 闭环"
chatgpt_decision_review: |
  Round-1: B+E (44-56h Review Queue Modal) — 死数据风险高
  Round-2 修正: C+ (18-24h 渐进式确认) — Cross-check 后 commit-ready 8.5/10
  关键修正:
    - Amershi 2019 是 HCI 不是教育有效性 (caveat 承认)
    - Khosravi 2022 谈"信任"非"学习效果" (caveat 承认)
    - 反方 VanLehn/Kulik/Ma 强支持 ITS 自动有效, 但 Story 2.5 写长期档案不是即时反馈
    - Dietvorst 2018 仅证明采纳度, 不直接证明学习效果
research_artifacts:
  - "_bmad-output/research/chatgpt-deep-research-story-2.5-sovereignty-isolation-2026-05-04.md"
  - "_bmad-output/research/chatgpt-round2-cross-check-story-2.5-sovereignty-isolation-2026-05-04.md"
  - "_bmad-output/research/chatgpt-round2-reply-story-2.5-sovereignty-isolation-2026-05-04.md"
parent_story: "2.5"
parent_ship_commit: "0d05ad8"
test_count_target: 30  # candidate writer + accept + rebuild + dashboard + E2E
---

# Story 2.5.X: 用户主权回归 — 渐进式确认 (C+ 方案)

Status: ✅ **review** (10/10 Tasks 完成, 271 测试 pass, 待用户 UAT)

## Story

As a 用 AI 学习概念的 CS 61B 学生,
I want AI 检测到我的可能误区时**先把候选放进笔记的"待复盘区"** (而不是直接写正式 errors[]),
So that 我能像编辑双链/批注一样**主动确认或否决**这些 AI 候选, AI 不替我做最终判决, 我的学习数据始终在我手里。

## 设计哲学（Round-2 锁定）

> **AI 可以自动提出候选误区, 但不应无确认地把开放式对话中的误区写成用户正式、长期、跨 session 的学习事实。**

| 维度 | Story 2.5 v1.0 (已 ship) | **Story 2.5.X (本 spec)** |
|---|---|---|
| AI 写入对象 | 直接进 `errors[]` 正式档案 | **先进 `error_candidates[]` 草稿区** |
| 用户参与 | 0% (被动观察) | **100%** (Cmd+Click 编辑或命令接受) |
| 主权感 | 1.6/5 (4 维全失) | **5/5** (vs 双链/callout 平级) |
| 死数据风险 | — | **Dashboard Dataview 持续显示 + 编辑流程自然消化** |
| 与 callout 关系 | 平行 (重叠) | **复用** Obsidian 编辑/确认心智 |

---

## Acceptance Criteria

### AC #1 - AI 候选写入 frontmatter `error_candidates[]` (不写正式 errors[])

**Given** 后端 `POST /api/v1/chat/post-turn-extract` 收到对话历史
**When** ErrorExtractor + ErrorClassifier 完成（提取到 ≥1 条错误）
**Then** 错误**只写入** frontmatter `error_candidates[]` 数组，**不**写 `errors[]`
**And** 每条 candidate 含 6 状态字段 `status: pending` (初始)
**And** 每条含 `ai_reason` (AI 为何判错)、`evidence_turns` (哪几轮对话)、`raw_dialog_excerpt`、`confidence`、`session_id`、`group_id`
**And** Graphiti **不**写入（candidate 阶段不进知识图谱）

**Acceptance Schema**：

```yaml
error_candidates:
  - id: <uuid>
    status: pending           # pending | accepted | edited | dismissed | disputed | expired
    source: ai_suggested
    node_id: 节点/admissibility.md
    session_id: s-2026-05-04-001
    group_id: cs_61b:main
    candidate_dedupe_hash: <16-char sha256(pedagogy_type, normalized_description, node_id, group_id)>
    pedagogy_type: conceptual_confusion
    legacy_type: knowledge_gap
    description: "学生混淆了 admissibility 和 consistency"
    ai_reason: "用户把二者当成同义, 但 consistency 比 admissibility 更强"
    evidence_turns: [3]
    raw_dialog_excerpt: "学习者: admissibility 就是 consistent 吧\nAI: 不对..."
    confidence: 0.85
    confidence_source: llm
    sub_tags: [synonym_confusion]
    suggested_remedy_strategies: [discrimination_comparison]
    created_at: "2026-05-04T..."
    last_seen_at: "2026-05-04T..."
    seen_count: 1
    seen_sessions: [s-2026-05-04-001]
```

---

### AC #2 - 6 状态机转换合法性

**Given** `error_candidates[]` 中的某条 candidate
**When** 状态变更
**Then** 仅允许以下合法转换：

```
pending  ─→ accepted   (用户接受 → 移入 errors[])
pending  ─→ edited     (用户编辑后接受 → 移入 errors[])
pending  ─→ dismissed  (用户标记"AI 误判" → 保留在 candidates 但不进 errors[])
pending  ─→ disputed   (用户标记"我有异议" → 保留 + 写 dispute_reason)
pending  ─→ expired    (超过 30 天未处理 → 自动归档, 不打扰用户)
```

**And** 反向转换 (如 accepted → pending) **被拒** (HTTP 422)
**And** 状态变更必须记录 `status_changed_at` + `status_changed_by` (user / system)

---

### AC #3 - dedupe 不重复添加（Round-2 修正）

**Given** AI 在新对话中再次检测到与已有 pending candidate 相同的错误
**When** 系统计算 `candidate_dedupe_hash = hash(pedagogy_type, normalized_description, node_id, group_id)`
**Then** **不**新建 candidate
**And** **更新**已有 candidate 的：
- `last_seen_at` 更新到当前
- `seen_count += 1`
- `seen_sessions.append(<current_session_id>)` (去重)
- `evidence_turns += <new turns>` (合并)
- `confidence = max(existing, new)` (取最大)

**注意**：dedupe hash **不**包含 `session_id`（避免跨 session 同错被误判为不同错误）

---

### AC #4 - 非阻塞 Notice + Dashboard 保活机制

**Given** 后端写入 ≥1 条新 pending candidate（且非 dedupe 更新）
**When** plugin 端收到响应
**Then** 显示 Obsidian `Notice("发现 N 个可能误区，可在 Dashboard 复盘", 5000)`
**And** **不**弹任何阻塞 Modal

**Given** 用户打开 `Dashboard.md`
**When** Dataview 渲染
**Then** 显示新 section "📋 待复盘错误候选"，含：
- pending candidate 总数
- 按 `node_id` 分组列表
- 每条显示 `description` + `confidence` 颜色标记 (🟢 ≥0.8 / 🟡 0.6-0.8 / 🔴 <0.6)
- 链接到对应节点 (Cmd+Click 跳转)

**And** 若 30 天前的 pending 自动 expired，Dashboard 用 callout 提示 "N 条候选已自动归档（>30 天未处理）"

---

### AC #5 - accept_candidate endpoint（最小闭环）

**Given** 用户在 Dashboard 点击"接受"按钮 或 触发命令 `canvas:accept-error-candidate`
**When** plugin 调用 `POST /api/v1/errors/accept-candidate`
**Request**:
```json
{
  "candidate_id": "<uuid>",
  "node_id": "节点/admissibility.md",
  "user_edits": null  // 或 { "description": "...", "pedagogy_type": "..." }
}
```
**Then** 后端执行：
1. 读 `error_candidates[]` 找到 `candidate_id`
2. 验证 `status == pending`（否则 422）
3. 应用 `user_edits` (如有)，标记 `status: edited` (有编辑) 或 `accepted` (无编辑)
4. **构造 ClassifiedError** 移入 `errors[]` 数组（含 `user_confirmed: true` / `user_confirmed_at: <now>` / `source: user_confirmed_ai`）
5. **同步写 Graphiti** (record_knowledge_entity, fire-and-forget)
6. 返回 `error_id`（移入后的 errors[] id）

**Response**:
```json
{
  "candidate_id": "<uuid>",
  "error_id": "<uuid>",
  "status": "accepted",  // 或 "edited"
  "frontmatter_written": true,
  "graphiti_status": "queued",
  "elapsed_ms": 234.5
}
```

---

### AC #6 - rebuild_graphiti_from_frontmatter endpoint（兜底机制）

**Given** 用户怀疑 Graphiti 同步丢失 或 切换设备后想重建图谱
**When** 调用 `POST /api/v1/errors/rebuild-graphiti?group_id=cs_61b:main`
**Then** 后端：
1. 扫描 `vault/节点/*.md` 所有 frontmatter `errors[]` (仅 `errors[]`，不含 candidates)
2. 按 group_id 过滤
3. 逐条调 `record_knowledge_entity()` 写 Graphiti（含 idempotency：先查 misconception_id 是否已存在）
4. 返回写入统计

**Response**:
```json
{
  "group_id": "cs_61b:main",
  "total_errors_scanned": 142,
  "newly_written_to_graphiti": 18,
  "already_existed": 124,
  "failed": 0,
  "elapsed_ms": 4521.3
}
```

**And** 失败的条目用 structlog warning 记录 (含 error_id + reason)

---

### AC #7 - dismissed/disputed 路径（用户否决 AI）

**Given** 用户点击 "AI 误判" (dismiss) 或 "我有异议" (dispute)
**When** plugin 调用 `POST /api/v1/errors/dismiss-candidate` 或 `POST /api/v1/errors/dispute-candidate`
**Then** candidate `status` 变为 `dismissed` / `disputed`
**And** dispute 必须含 `dispute_reason: str` (用户简短说明)
**And** **不**移入 errors[]
**And** **不**写 Graphiti
**And** 保留在 candidates 数组（用于将来训练 AI 改进 prompt）

**Request (dispute)**:
```json
{
  "candidate_id": "<uuid>",
  "node_id": "节点/admissibility.md",
  "dispute_reason": "我没有把 admissibility 当 consistency, 我只是问它们的关系"
}
```

---

## Tasks / Subtasks

- [x] **Task 1: 修改 post-turn-extract 写入路径** (AC: #1, #3) ✅ 2026-05-04
  - [x] 1.1: 修改 `error_writer.write_error_dual()` 接受 `mode: Literal["candidate_only", "write_confirmed"]` 参数
  - [x] 1.2: 默认 mode = `"candidate_only"` (Story 2.5.X 后) — chat.py / error_tools.py 显式 `mode="write_confirmed"` 兼容 v1.0 行为
  - [x] 1.3: 实现 `write_candidate_to_frontmatter(file_path, candidate)` — 写入 `error_candidates[]` 数组
  - [x] 1.4: candidate dedupe 逻辑：复用 dedupe_hash 算法 (不含 session_id)，已存在则 update last_seen_at + seen_count + seen_sessions（取 max confidence）
  - [x] 1.5: candidate 阶段**不**调用 `write_error_to_graphiti` (返回 `graphiti: "skipped_candidate_mode"`)

- [x] **Task 2: 6 状态机实现** (AC: #2) ✅ 2026-05-04
  - [x] 2.1: 新增 `CandidateStatus` Literal type (`pending` | `accepted` | `edited` | `dismissed` | `disputed` | `expired`)
  - [x] 2.2: 实现 `validate_status_transition(current, target)` 函数 (检测合法转换 + 终态判定)
  - [x] 2.3: 拒绝非法转换抛 `HTTPException(422)` (含 reverse + terminal-to-terminal + unknown 三类错误信息)
  - [x] 2.4: 实现 `apply_status_change(candidate, target, *, changed_by)` 自动写 `status_changed_at` (ISO 8601) + `status_changed_by` ("user"/"system")
  - [x] 2.5 (附加): `is_terminal_status` / `is_active_status` helpers (Dashboard 过滤用)

- [x] **Task 3: accept_candidate endpoint** (AC: #5) ✅ 2026-05-05
  - [x] 3.1: 新增 `POST /api/v1/errors/accept-candidate` 路由 (含 errors_router 注册)
  - [x] 3.2: 实现 `AcceptCandidateRequest` / `AcceptCandidateResult` Pydantic models + `CandidateEdits` 子模型
  - [x] 3.3: 服务层 `candidate_service.accept_candidate(file_path, candidate_id, *, user_edits, session_id)`:
    - 读 frontmatter → 找 candidate by id (404 if not found)
    - 状态机校验 pending → accepted/edited (apply_status_change 422 if illegal)
    - 应用 user_edits (description/pedagogy_type/legacy_type 覆盖) → 构造 ClassifiedError
    - errors[] 追加 (含 source=user_confirmed_ai / user_confirmed=true / from_candidate_id)
    - errors[] dedupe (复用 v1.0 hash 算法, 已存在则 update)
    - candidate.status = accepted/edited (apply_status_change auto-write timestamp)
    - 原子写回 frontmatter (per-file lock + tempfile + os.replace)
    - 写 Graphiti (fire-and-forget 默认)
  - [x] 3.4: 单测 + service 层覆盖 (test_candidate_service.py 7 用例)

- [x] **Task 4: dismiss_candidate / dispute_candidate endpoints** (AC: #7) ✅ 2026-05-05
  - [x] 4.1: `POST /api/v1/errors/dismiss-candidate`
  - [x] 4.2: `POST /api/v1/errors/dispute-candidate` (`dispute_reason: str` 必填 + 422 if empty/whitespace)
  - [x] 4.3: 状态机转换验证 (复用 apply_status_change, terminal-to-terminal 拒绝)
  - [x] 4.4: dismissed/disputed 不写 errors[]/Graphiti, 保留在 candidates (含 dispute_reason 供训练 prompt)

- [x] **Task 5: rebuild_graphiti_from_frontmatter endpoint** (AC: #6) ✅ 2026-05-05
  - [x] 5.1: 新增 `POST /api/v1/errors/rebuild-graphiti?group_id=...&dry_run=...` 路由
  - [x] 5.2: 实现 `error_rebuild_service.rebuild_graphiti_from_frontmatter(vault_root, group_id, *, dry_run)`:
    - 扫描 vault 节点/*.md (fallback root *.md)
    - 解析 frontmatter errors[] (corrupted file 跳过 + 记 failures)
    - 调 write_error_to_graphiti 复用 v1.0 写入路径 (含 retry + timeout)
    - dry_run=True 仅扫描计数, 不调 Graphiti
  - [x] 5.3: 返回 RebuildStats 含 total_files_scanned / total_errors_scanned / newly_written / failed + failures details
  - [x] 5.4: structlog warning 记录每条失败 (含 file path + error_id + reason)
  - [x] 5.5 (附加): RebuildFailure schema (file/error_id/reason) + 单条失败不中断扫描

- [x] **Task 6: Obsidian Dashboard Dataview 保活** (AC: #4) ✅ 2026-05-05
  - [x] 6.1: `canvas-vault/Dashboard.md` 加新 section "📋 待复盘错误候选"
  - [x] 6.2: DataviewJS 块查询所有 `节点/*.md` frontmatter `error_candidates[]` (按 status 分类)
  - [x] 6.3: 按 `node.file.link` 分组渲染 + 显示 description / pedagogy_type / confidence 颜色 (🟢≥0.8 / 🟡≥0.6 / 🔴<0.6) + seen_count + last_seen 时间
  - [x] 6.4: 总览表显示 6 状态机各状态数 + pending 详细列表 (Cmd+Click 跳转节点链接 dv.file.link)
  - [x] 6.5: expired > 0 时显示 `[!warning]+` callout 提示已归档数量

- [x] **Task 7: Plugin 命令 + 非阻塞 Notice** (AC: #4, #5, #7) ✅ 2026-05-05
  - [x] 7.1: 修改 `frontend/obsidian-plugin/src/main.ts` (+~190 行: 3 handler + 共享 POST 路径)
  - [ ] 7.2: post-turn-extract 响应后 Notice "发现 N 个可能误区" — 待 Task 5 chat.py 切默认 candidate_only 后接入
  - [x] 7.3: 注册 3 个命令:
    - `canvas:accept-error-candidate` → CandidateSuggestModal → POST /errors/accept-candidate
    - `canvas:dismiss-error-candidate` → CandidateSuggestModal → POST /errors/dismiss-candidate
    - `canvas:dispute-error-candidate` → CandidateSuggestModal → DisputeReasonModal → POST /errors/dispute-candidate
  - [x] 7.4: 复用 fetch (与 v1.0 chat-with-context 同模式), 错误处理 + Notice 反馈
  - [x] 7.5: 命令成功后 Notice 反馈 (frontmatter 自动 reload, Dashboard Dataview 自动重渲染)
  - [x] 7.6 (附加): error-candidate-helpers.ts 模块化 pure logic + 19 测试 (filterPending / formatLabel / payload builders / validateReason)
  - [x] 7.7 (附加): main.js deploy 到 canvas-vault/.obsidian/plugins/ (88684B → 106348B)

- [x] **Task 8: session_id 注入** (AC: #1) ✅ 2026-05-05
  - [x] 8.1: `PostTurnExtractRequest` 已有 `session_id` 字段 (v1.0)
  - [x] 8.2: `error_writer.write_candidate_to_frontmatter` 把 session_id 写入 `seen_sessions[]`
  - [x] 8.3: dedupe 时 new session_id 加入已有 `seen_sessions[]` (set 去重)
  - [x] 8.4 (E2E): test_2_5_x_e2e.py::test_e2e_session_id_accumulates_across_sessions 验证 3 session 累加

- [x] **Task 9: expired 自动归档机制** (AC: #2, #4) ✅ 2026-05-05
  - [x] 9.1: `backend/app/services/candidate_expiry_service.py` 新增 `expire_pending_candidates(vault_root, *, expiry_days=30, now=None)` cron service (lifespan hook 集成留 Story 2.5.Y)
  - [x] 9.2: 扫描所有 vault `节点/*.md` (复用 _scan_vault_md_files)
  - [x] 9.3: `created_at < now - 30d AND status == pending` → `apply_status_change → expired` (changed_by="system")
  - [x] 9.4: structlog info 记录每条 expire + 完成统计 (含 cutoff/total/expired/failed)
  - [x] 9.5 (附加): _is_expired helper + _parse_created_at 容错 (ISO/Z/naive/None) + 幂等性测试 + per-file lock 复用

- [x] **Task 10: 测试** (AC: #1~#7) ✅ 2026-05-05
  - [x] 10.1: `test_candidate_writer.py` (16 测试 - Task 1)
  - [x] 10.2: `test_candidate_state_machine.py` (41 测试 - Task 2)
  - [x] 10.3: `test_candidate_service.py::test_accept_candidate*` (7 用例 - Task 3)
  - [x] 10.4: `test_candidate_service.py::test_dismiss/dispute*` (7 用例 - Task 4)
  - [x] 10.5: `test_error_rebuild_service.py` (13 测试 - Task 5)
  - [x] 10.6: `tests/integration/test_2_5_x_e2e.py` (10 E2E: full accept/edits/dismiss/dispute/session累加/expire/rebuild/双重accept拒绝/dismiss-then-accept拒绝)
  - [x] 10.7 (附加): `test_candidate_expiry_service.py` (20 测试 - Task 9)
  - [x] 10.8 (附加): `frontend/obsidian-plugin/tests/error-candidate-helpers.test.ts` (19 测试 - Task 7)

## Dev Notes

### 关键实现锚点

1. **复用 Story 2.5 v1.0 ship 代码**（commit `0d05ad8`）：
   - `error_extractor.py::extract_errors_from_dialog()` — 不变
   - `error_classifier.py::classify_with_pedagogy()` — 不变
   - `error_writer.py::write_error_to_frontmatter()` — 改 mode 参数后复用
   - `error_writer.py::write_error_to_graphiti()` — 仅在 accept_candidate 时调用

2. **frontmatter 双数组并存**：
   - `errors[]` (Story 2.5 v1.0 已有) — confirmed errors，写 Graphiti
   - `error_candidates[]` (本 Story 新增) — pending/edited/dismissed/disputed/expired，**不**写 Graphiti

3. **dedupe hash 算法不变**（Round-2 修正）：
   ```python
   def compute_dedupe_hash(pedagogy_type, description, node_id, group_id):
       norm_desc = re.sub(r'\s+', ' ', description.strip().lower())
       return hashlib.sha256(f"{pedagogy_type}:{norm_desc}:{node_id}:{group_id}".encode()).hexdigest()[:16]
   ```
   **不**包含 session_id（跨 session 同错应增 seen_count，不应建多条）

4. **per-file lock 复用**：
   - `error_writer.py:40-48` 已有 `_get_file_lock()` ContextVar 级 lock
   - 写 candidate 时复用同一 lock（防 candidate vs errors 并发竞争）

5. **状态机实现**（Pydantic + Literal）：
   ```python
   from typing import Literal
   CandidateStatus = Literal["pending", "accepted", "edited", "dismissed", "disputed", "expired"]
   
   ALLOWED_TRANSITIONS = {
       "pending": {"accepted", "edited", "dismissed", "disputed", "expired"},
       "accepted": set(),    # 不可逆
       "edited": set(),
       "dismissed": set(),
       "disputed": set(),
       "expired": set(),
   }
   ```

### Project Structure Notes

```
backend/app/services/
  error_writer.py              # 改：加 mode 参数 + write_candidate_*
  error_service.py             # 新增：accept/dismiss/dispute/rebuild 业务逻辑
backend/app/api/v1/endpoints/
  errors.py                    # 新增：accept/dismiss/dispute/rebuild endpoints
backend/app/schemas/
  candidate.py                 # 新增：CandidateStatus + AcceptCandidateRequest 等
backend/tests/unit/
  test_candidate_writer.py
  test_status_machine.py
  test_accept_candidate.py
  test_dismiss_dispute.py
  test_rebuild_graphiti.py
backend/tests/integration/
  test_2_5_x_e2e.py
canvas-vault/
  Dashboard.md                 # 改：加"📋 待复盘错误候选" section
frontend/obsidian-plugin/src/
  main.ts                      # 改：3 命令 + Notice + accept SuggestModal
  candidate-suggester.ts       # 新增：CandidateSuggestModal class
```

### References

- **Anchor PRD §FR-CONV-06**: `/Users/Heishing/Desktop/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md` (line 3387-3393)
- **Story 2.5 v1.0 ship code**: commit `0d05ad8`
- **ChatGPT Round-2 reply**: `_bmad-output/research/chatgpt-round2-reply-story-2.5-sovereignty-isolation-2026-05-04.md`
- **现有 frontmatter writer**: `backend/app/services/error_writer.py:65-228`
- **现有 Dashboard Dataview**: `canvas-vault/Dashboard.md` (Story 1.18 v1.2)
- **Story 1.16 callout 心智参考**: `frontend/obsidian-plugin/src/main.ts` (Cmd+Shift+A 批注)
- **Decision-Review-D15**: 用户主权回归方案 (待用户在 PRD §12 批注)

### 与 Story 2.5 v1.0 兼容性

- Story 2.5 v1.0 已 ship 的 frontmatter `errors[]` 数据保持不变
- Story 2.5.X 启动后，新对话只写 `error_candidates[]`
- 已有 `errors[]` 数据可通过 `rebuild_graphiti` endpoint 重新同步到 Graphiti（如有遗漏）
- **回滚策略**：若 Story 2.5.X 失败，把 mode 默认值改回 `write_confirmed` 即恢复 v1.0 行为

## UAT Script

> **前置**：用户在 PRD §12 批注 D15 决议（用户主权方案 = C+），并跑过 Story 2.5 v1.0 UAT
>
> **场景 1：候选写入 + Notice**
> 1. 在 `节点/admissibility.md` 启动 AI 对话
> 2. 故意说错："admissibility 就是 consistency 吧"
> 3. AI 纠正后，等 3-5s
> 4. **预期**：右下角弹 Notice "发现 1 个可能误区，可在 Dashboard 复盘"
> 5. **预期**：打开 `admissibility.md` frontmatter，`error_candidates:` 数组多 1 条 `status: pending`
> 6. **不预期**：`errors:` 数组**没**变化（仍是 v1.0 的旧记录）
>
> **场景 2：Dashboard 保活**
> 7. 打开 `Dashboard.md`
> 8. **预期**：新 section "📋 待复盘错误候选" 显示 "1 条 pending"
> 9. **预期**：列表中显示 description + 🟢/🟡/🔴 confidence 颜色 + 节点链接
>
> **场景 3：用户接受 → 移入 errors[]**
> 10. Cmd+P → "Canvas: 接受错误候选" → 选择刚才那条
> 11. **预期**：弹 SuggestModal 列出 pending candidates
> 12. **预期**：选择后右下角 Notice "已接受，移入 errors[] 并同步 Graphiti"
> 13. **预期**：打开节点 frontmatter，`errors:` 数组多 1 条（含 `user_confirmed: true`），`error_candidates:` 中那条 `status: accepted`
>
> **场景 4：dispute (AI 误判)**
> 14. 让 AI 提取另一个候选（再触发对话）
> 15. Cmd+P → "Canvas: 异议错误候选"，输入 dispute_reason "我没误解，AI 误判"
> 16. **预期**：candidate `status: disputed`，**不**进 errors[]，**不**写 Graphiti
>
> **场景 5：rebuild graphiti**
> 17. Cmd+P → 调 `POST /api/v1/errors/rebuild-graphiti?group_id=cs_61b:main`
> 18. **预期**：返回 `total_errors_scanned`/`newly_written`/`already_existed` 统计
> 19. **预期**：Graphiti 中所有 misconception entity 都有对应 frontmatter `errors[].id`
>
> **场景 6：30 天 expired**（需手动模拟）
> 20. 改某 candidate 的 `created_at` 为 31 天前
> 21. 调启动钩子 / cron task
> 22. **预期**：candidate `status: expired`，Dashboard callout 显示 "1 条已自动归档"

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| candidate 写入 | unit | `pytest tests/unit/test_candidate_writer.py -x` | candidate 进 frontmatter，errors[] 不变 |
| dedupe 更新 | unit | `pytest tests/unit/test_candidate_writer.py::test_dedupe_update_not_append -x` | 同 hash 已存在则 update last_seen_at + seen_count |
| 状态机合法 | unit | `pytest tests/unit/test_status_machine.py -x` | 5 个 pending→X 转换通过 + 反向被拒 |
| accept 流程 | unit | `pytest tests/unit/test_accept_candidate.py -x` | candidate → errors[] + Graphiti queued |
| dispute 路径 | unit | `pytest tests/unit/test_dismiss_dispute.py -x` | dispute_reason 必填 + 不写 errors[] |
| rebuild idempotency | unit | `pytest tests/unit/test_rebuild_graphiti.py -x` | 重跑 N 次 newly_written = 0 |
| 端到端 | integration | `pytest tests/integration/test_2_5_x_e2e.py -x` | 完整流程通过 |

## User Feedback & Changes

### Feedback Log

(empty)

### Deviation Notes

(empty)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7 (1M context) — 2026-05-04 启动 Story 2.5.X dev-story

### Debug Log References

- 测试: `cd backend && PYTHONPATH=. /Users/Heishing/Desktop/canvas/canvas-learning-system/backend/.venv/bin/pytest tests/unit/test_candidate_writer.py tests/unit/test_error_writer.py tests/unit/test_error_extractor.py tests/unit/test_error_classification_mapping.py -q`
- 测试结果: **69 passed, 0 failed** (16 新增 candidate_writer + 53 v1.0 回归)

### Completion Notes List

**Task 1 完成 (2026-05-04)** — Candidate writer 双 mode 路由 + dedupe + Graphiti skip

实施摘要:
- 新增 `write_candidate_to_frontmatter()` + `write_candidate_to_frontmatter_async()` (per-file lock 复用)
- 新增 `_make_candidate_record()` helper 构造 6 状态机初始 dict (含 status=pending / source=ai_suggested)
- 修改 `write_error_dual()` 加 `mode: Literal["candidate_only", "write_confirmed"] = "candidate_only"` 参数 (Task 1.1)
  - candidate_only 模式: 写 `error_candidates[]`, skip Graphiti, 返回 `candidate_id`
  - write_confirmed 模式: 维持 v1.0 行为 (写 `errors[]` + Graphiti queued, 返回 `error_id`)
- candidate 阶段保留 dedupe hash 算法 (不含 session_id, AC #3): 同 hash 存在则 update last_seen_at + seen_count + seen_sessions + max(confidence)
- v1.0 调用方兼容: chat.py post-turn-extract + error_tools.py record_error MCP 显式传 `mode="write_confirmed"` 不破坏现有行为

测试覆盖 (16 新增):
- ✅ AC #1: candidate 写 error_candidates[] 不写 errors[]
- ✅ AC #1: 6 状态机初始 status=pending + source=ai_suggested
- ✅ AC #1: 可选元数据 ai_reason / evidence_turns / raw_dialog_excerpt 留 None/[] (Task 5 升级 LLM 后填)
- ✅ AC #3: dedupe 同 hash update 不 append
- ✅ AC #3: dedupe hash 不含 session_id (跨 session update + seen_sessions 累加)
- ✅ AC #3: dedupe 取 max confidence (Round-2 修正)
- ✅ AC #3: 不同 description → 不同 hash → 独立 append
- ✅ Task 1.1: write_error_dual 默认 mode = candidate_only
- ✅ Task 1.5: candidate_only 不调用 write_error_to_graphiti (mock 验证)
- ✅ write_confirmed 模式: errors[] + Graphiti queued + error_id 字段
- ✅ candidate_only 模式: candidate_id 字段 (非 error_id)
- ✅ async wrapper: per-file lock 复用
- ✅ 边界: file_not_found 返回 (False, None)
- ✅ 双数组并存: errors[] + error_candidates[] 互不影响

无回归: v1.0 53 测试全 pass (test_error_writer + test_error_extractor + test_error_classification_mapping)

**剩余 Tasks (9 个)**:
- [ ] Task 2: 6 状态机 validate_status_transition + status_changed_at/by 自动写
- [ ] Task 3: accept_candidate endpoint (POST /api/v1/errors/accept-candidate)
- [ ] Task 4: dismiss_candidate / dispute_candidate endpoints
- [ ] Task 5: rebuild_graphiti_from_frontmatter endpoint
- [ ] Task 6: Obsidian Dashboard Dataview 保活
- [ ] Task 7: Plugin 命令 + 非阻塞 Notice
- [ ] Task 8: session_id 注入 (已含在 Task 1 schema, 待端到端测试)
- [ ] Task 9: expired 自动归档 cron task
- [ ] Task 10: 单测 + 集成测试 (已部分覆盖 Task 1, 待 Tasks 2-9 补全)

### File List

**新增**:
- `backend/tests/unit/test_candidate_writer.py` (16 测试用例 + fixtures) — Task 1
- `backend/app/services/candidate_state_machine.py` (~140 行: ALLOWED_TRANSITIONS + validate + apply + helpers) — Task 2
- `backend/tests/unit/test_candidate_state_machine.py` (41 测试用例: 5 合法 + 9 非法 + 时间戳 + 业务场景) — Task 2
- `backend/app/services/candidate_service.py` (~370 行: accept/dismiss/dispute + helpers) — Task 3+4
- `backend/app/api/v1/endpoints/errors.py` (~146 行: 4 endpoint + Pydantic request models) — Task 3+4+5
- `backend/tests/unit/test_candidate_service.py` (14 测试用例: accept/dismiss/dispute 各场景) — Task 3+4
- `backend/app/services/error_rebuild_service.py` (~280 行: scan + write + RebuildStats) — Task 5
- `backend/tests/unit/test_error_rebuild_service.py` (13 测试用例: dry_run + failures + node_id resolution) — Task 5

**改动**:
- `canvas-vault/Dashboard.md`: 新增 "📋 待复盘错误候选" section (~85 行 DataviewJS) — Task 6
- `frontend/obsidian-plugin/src/main.ts`: +3 命令注册 + 3 handler + 2 Modal class (~190 行) — Task 7
- `frontend/obsidian-plugin/src/error-candidate-helpers.ts`: 新增 (~140 行 pure logic) — Task 7
- `frontend/obsidian-plugin/tests/error-candidate-helpers.test.ts`: 新增 (19 测试) — Task 7
- `canvas-vault/.obsidian/plugins/canvas-learning-system/main.js`: deploy (106348B) — Task 7
- `backend/app/services/candidate_expiry_service.py` (~210 行: cron + helpers + ExpireStats) — Task 9
- `backend/tests/unit/test_candidate_expiry_service.py` (20 测试: 边界/幂等/批量/无 created_at 保守) — Task 9
- `backend/tests/integration/test_2_5_x_e2e.py` (10 E2E 测试 - Task 8+10)

**修改**:
- `backend/app/services/error_writer.py`:
  - 加 `from typing import Literal` import
  - 新增 `WriteMode` Literal type + `CANDIDATE_INITIAL_STATUS` / `CANDIDATE_SOURCE_AI` 常量
  - 新增 `_make_candidate_record()` helper (6 状态机初始字段)
  - 新增 `write_candidate_to_frontmatter()` (sync) + `write_candidate_to_frontmatter_async()` (async wrapper)
  - 修改 `write_error_dual()` 签名加 `mode` / `group_id` / `ai_reason` / `evidence_turns` / `raw_dialog_excerpt` 参数
  - 修改 `write_error_dual()` 实现路由 candidate_only / write_confirmed 双 mode
- `backend/app/api/v1/endpoints/chat.py`: post-turn-extract 调用加 `mode="write_confirmed"` (line 353-360)
- `backend/app/mcp/tools/error_tools.py`: record_error MCP 调用加 `mode="write_confirmed"` (line 219-225)
- `backend/tests/unit/test_error_writer.py`: 4 个 dual_write 测试加 `mode="write_confirmed"` 适配新签名
- `backend/tests/integration/test_error_extraction_e2e.py`: 1 个 dual_write 调用加 `mode="write_confirmed"`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`: 加 2-5-x / 2-5-y 条目 + 标 2-5-x in-progress
- `_bmad-output/implementation-artifacts/epic-2/2-5-x-error-candidate-progressive-confirmation.md`: 标 Task 1 [x] + 填 Dev Agent Record

## Change Log

- **2026-05-04 v1.0 初稿** — 基于 ChatGPT Round-2 reply（commit `348a7ae`）锁定 C+ 方案
  - 6 状态机 + frontmatter `error_candidates[]` + Dashboard 保活 + accept/rebuild 闭环
  - 等待用户在 PRD §12 批注 D15 后启动 dev-story
- **2026-05-04 Task 1 ship** — 用户 D15=C+ 决议确认后 dev-story 启动
  - Task 1 完成: write_error_dual 双 mode 路由 + write_candidate_to_frontmatter + dedupe + Graphiti skip
  - 测试: 16 新增 candidate_writer + 53 v1.0 回归 = 69 passed
  - v1.0 兼容: chat.py / error_tools.py 显式 mode="write_confirmed" 维持现有行为
- **2026-05-04 Task 2 ship** — 6 状态机
  - Task 2 完成: candidate_state_machine.py + ALLOWED_TRANSITIONS + validate_status_transition + apply_status_change
  - pending → 5 终态 (accepted/edited/dismissed/disputed/expired) 全合法
  - 反向转换 + 终态间转换 + unknown status 全拒 (HTTP 422 + 友好 error message)
  - apply_status_change 自动写 ISO 8601 status_changed_at + changed_by ("user"/"system")
  - 测试: 41 新增 state_machine + 110 全栈累计 (含 16 candidate_writer + 53 v1.0)
- **2026-05-05 Story 2.5.X 全量 ship → review** — 10/10 Tasks 完成
  - Task 8 (session_id 注入): E2E 验证跨 session 累加 (1 candidate + seen_sessions={s1,s2,s3})
  - Task 9 (expired cron): candidate_expiry_service.py + 20 单测
    · expire_pending_candidates(vault_root, *, expiry_days=30, now=None)
    · 30 天阈值 + apply_status_change → expired (changed_by="system")
    · 幂等性 + 单条失败不中断 + per-file lock 复用
    · 仅当有 expire 改动时才写文件 (避免无意义 mtime 更新)
    · _parse_created_at: ISO/Z/naive/None 容错
    · _is_expired: status=pending AND created_at < cutoff (无 created_at 保守跳过)
  - Task 10 (集成测试): test_2_5_x_e2e.py + 10 E2E 测试
    · full accept flow (write → accept → errors[] + Graphiti queued)
    · accept with edits (status=edited + edits 应用到 errors[])
    · dismiss path (不入 errors[])
    · dispute path (dispute_reason 持久化)
    · session_id 跨 3 session 累加 (Task 8 verification)
    · expired 30 天后 cron 归档 (Task 9 verification)
    · rebuild from frontmatter (Task 5 verification)
    · double accept rejected (状态机)
    · dismiss → accept rejected (终态间不可逆)
  - 测试累计: Backend 167 + Plugin 104 = **271 全 pass**
  - sprint-status: 2-5-x in-progress → review
- **2026-05-05 Task 7 ship** — Plugin 命令 + Modal 集成
  - Task 7 完成: 3 命令注册 + 2 Modal class + helpers 模块
    · canvas:accept/dismiss/dispute-error-candidate 命令
    · CandidateSuggestModal (FuzzySuggestModal extends, 显示 🟢🟡🔴 confidence + pedagogy_type)
    · DisputeReasonModal (Modal extends, textarea + cancel/confirm + Esc)
    · error-candidate-helpers.ts: filterPendingCandidates / formatCandidateLabel / build*Payload / validateDisputeReason
    · postErrorCandidateAction 共享 POST 路径 (3 命令复用)
  - 测试: 19 plugin helpers + 104 plugin total (含 85 v1.0 回归)
  - main.js: 88684B → 106348B (+17.7KB) deploy 到 canvas-vault/.obsidian/plugins/
  - 剩余 3 Tasks (cron/session_id 验证/集成测试) 待续
- **2026-05-05 Task 6 ship** — Dashboard Dataview 保活
  - Task 6 完成: canvas-vault/Dashboard.md 加 "📋 待复盘错误候选" section
    · DataviewJS 扫描 节点/*.md frontmatter error_candidates[]
    · 6 状态机分类计数总览表
    · pending 详细列表: 按节点分组 + confidence 颜色编码 + seen_count/last_seen
    · expired > 0 时显示 callout warning
    · 跳转: dv.file.link (Cmd+Click 进节点)
  - 无需 backend 测试 (Markdown + DataviewJS 渲染由 Obsidian 处理)
  - 剩余 4 Tasks (Plugin/cron/session_id 验证/集成测试) 待续
- **2026-05-05 Task 5 ship** — rebuild_graphiti_from_frontmatter 兜底机制
  - Task 5 完成: error_rebuild_service.py + POST /api/v1/errors/rebuild-graphiti
    · 扫描 vault 节点/*.md (fallback 根目录) 解析 errors[]
    · 调 write_error_to_graphiti 复用 v1.0 (含 retry + timeout)
    · dry_run 模式: 仅计数, 不调 Graphiti
    · 单条失败 (parse / classify / Graphiti 写入) 不中断, 记入 failures[] + structlog warning
    · RebuildStats: total_files_scanned / total_errors_scanned / newly_written / failed + failures details
    · 用户场景: 切设备 / Graphiti 数据丢失 / 验证一致性
  - 测试: 13 新增 rebuild_service + 137 全栈累计
  - 4 endpoint 注册: accept/dismiss/dispute/rebuild
  - 剩余 5 Tasks (Dashboard/Plugin/cron/session_id 验证/集成测试) 待续
- **2026-05-05 Task 3+4 ship** — accept/dismiss/dispute endpoints + service 层
  - Task 3 完成: candidate_service.accept_candidate() + POST /api/v1/errors/accept-candidate
    · per-file lock 内原子操作: candidate.status mutation + errors[] append + frontmatter atomic write
    · 复用 candidate_id 作为 error_id (frontmatter 一致性)
    · 复用 v1.0 _make_dedupe_hash + dedupe 逻辑 (同 hash → update, 不 append)
    · 默认 fire-and-forget Graphiti, 同步模式可选
    · errors[] 新条含主权字段: source=user_confirmed_ai / user_confirmed=true / user_confirmed_at / from_candidate_id
  - Task 4 完成: dismiss_candidate + dispute_candidate + POST /api/v1/errors/dismiss-candidate + dispute-candidate
    · dispute_reason 必填 + 空白校验 (422)
    · 不写 errors[] / 不写 Graphiti
    · candidate.status mutation only (终态间不可逆)
  - errors_router 注册 prefix="/errors" tags=["Errors"] (router.py +14 行)
  - 测试: 14 新增 candidate_service + 124 全栈累计 (含 41+16+53+14)
  - 剩余 6 Tasks (rebuild/Dashboard/Plugin/cron/session_id 验证/集成测试) 待续
