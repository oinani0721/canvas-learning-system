# A3 修复追踪 + Claude Code Desktop 端到端测试矩阵

> **来源**：FR-KG-04 / A3 user2 批注 + OpenSpec change 已归档（`archive/2026-04-07-fix-fr-kg-04-schema-drift-and-sync-hardening/`）
> **日期**：2026-04-07
> **目标**：（1）给用户 3 个最关键的 openspec 文件用于 A3 代码追踪；（2）列出 Claude Code Desktop 可直接执行的端到端验证入口（前后端都能测）
>
> **覆盖说明**：本文件取代上一份 distributed-jingling-gizmo.md 中过时的 Tier A/B/C 全景导航。上一份的 openspec 路径全都失效（change 已被 archive），且漏掉了真正的 Phase 5 Task 5.1 实现 `test_a11_kg_relevance_e2e.py`。

---

## Context

### 为什么需要这次更新

1. **OpenSpec 状态变了**：原 `openspec/changes/fix-fr-kg-04-schema-drift-and-sync-hardening/` 已被 archive 到 `openspec/changes/archive/2026-04-07-fix-fr-kg-04-schema-drift-and-sync-hardening/`。上一份导航文档里所有 `openspec/changes/fix-fr-kg-04-schema-drift-and-sync-hardening/...` 的引用现在都是断链。
2. **Phase 5 Task 5.1 不再 deferred**：上一份 plan 写的 `❌ NOT YET CREATED`是错的。文件已经存在：`backend/tests/e2e/test_a11_kg_relevance_e2e.py`（15663 bytes, 2026-04-07 04:12 创建，7 个 test）。对 CC Desktop 来说这是最重要的端到端入口。
3. **CC Desktop 的能力边界没人列过**：CC Desktop 能跑 pytest、启动 uvicorn、curl 测 API、用 `mcp__claude-in-chrome__*` 驱动 Vite dev server，但**不能驱动 Tauri 桌面窗口**。上一份 Tier C 写的"在 Tauri app 里手动点"对 CC Desktop 不可行 — 需要重写为"Vite web mode + Chrome 自动化"。

### A3 是什么（一句话回顾）

`docs/project-status/fr-exploration/FR-KG-04/FR-KG-04-user2-annotations.md` 第 3 条：「评分验证是自己编的还是社区认证的？」直接质疑两件事：
- **质疑 1**：`verification_service.py` 评分系统的成熟度（无 inter-rater reliability、无 ground truth）→ 修复：Phase 17.1 fail-closed + Phase 17.2 path traversal hardening
- **质疑 2**：`question_generator.py` 三因子权重 `W_KG_RELEVANCE=0.3` 的"无学术支撑"→ 修复：Phase 1 + Sprint 1.2.1 让加权公式真正生效（之前 silent 0.5 bug 让 30% 权重永远失效）

修复**没有**直接回应"社区认证"问题（那是另一个开放议题），而是**让 A3 质疑的公式能真正先跑起来**。

---

## Part 1 — 3 个最重要的 OpenSpec 文件（A3 代码追踪）

> **绝对路径根**：`/Users/Heishing/Desktop/canvas/canvas-learning-system/openspec/changes/archive/2026-04-07-fix-fr-kg-04-schema-drift-and-sync-hardening/`

### 🎯 #1 — `specs/verification-service/spec.md`（126 行）

**追踪 A3 的哪个方面**：质疑 1（评分系统成熟度）

**完整路径**：
```
openspec/changes/archive/2026-04-07-fix-fr-kg-04-schema-drift-and-sync-hardening/specs/verification-service/spec.md
```

**关键章节**：
- `## ADDED Requirements`
  - `### Requirement: Fail-Closed Degraded Scoring`（Phase 17.1）
  - `### Requirement: Canvas File Access Defense-in-Depth`（Phase 17.2）

**读这份 spec 你能直接定位**：
- `_mock_evaluate_answer` 在所有路径必须返回 `(quality="unknown", score=0.0)`，禁止根据 `user_answer` 长度/内容启发式打分
- `_do_extract_concepts` 必须用 `CanvasService.read_canvas(canvas_name)` 委托验证（method 1），后端独立调用 `_resolve_safe_canvas_path` 双层防护（method 2），失败 fallback 到 `["默认概念"]`
- **16 个 Scenario**（Phase 17.1 fail-closed 8 个 + Phase 17.2 path traversal 8 个）一对一覆盖具体行为：1000 字符噪音、`../../etc/passwd`、null byte、绝对路径、non-canvas 后缀、嵌套合法路径、双后缀、e2e traversal 等

**为什么是它 #1**：A3 的核心质疑是评分可靠性。这份 spec 直接定义了"不可靠时怎么办"的合同——fail-closed，不污染掌握度。读完 126 行你就理解了 verification 服务硬化的全部要求。

---

### 🎯 #2 — `specs/algo-question/spec.md`（93 行）

**追踪 A3 的哪个方面**：质疑 2（三因子权重无学术支撑）

**完整路径**：
```
openspec/changes/archive/2026-04-07-fix-fr-kg-04-schema-drift-and-sync-hardening/specs/algo-question/spec.md
```

**关键章节**（5 个 Requirement）：
- `### Requirement: kg_relevance Schema Correctness`（Cypher 字段名 schema 对齐）
- `### Requirement: kg_relevance Weighted Edge Formula`（CANVAS_EDGE 1.0 / RELATES_TO 0.7 / 归一化 /8.0）
- `### Requirement: Degraded Reason Observability`（degraded marker 通过 NodePriority 传播）
- `### Requirement: NodePriority Formula Stability`（三因子 0.4/0.3/0.3 锁定 + degraded 处理）
- `### Requirement: exam_service_ext Schema Alignment`（移除幽灵 schema）

**读这份 spec 你能直接定位**：
- 修复前的 silent 0.5 bug：`{uuid}` + `canvas_id`（snake_case）→ 永远查空 → 30% 权重失效
- 修复后的查询：`{id}` + `canvasId`（camelCase）匹配 SyncService 写入字段
- 加权公式：`weighted_degree = Σ(edge_weight × count) / 8.0`，2 条 CANVAS_EDGE + 3 条 RELATES_TO → `(2×1.0 + 3×0.7) / 8.0 = 0.5125`
- 注：Sprint 1.2.1 H-1 多边膨胀防护（`WITH neighbor MAX(...)` + `COUNT(DISTINCT neighbor)`）**不在本 spec 内** —— 它是代码层修复，由 `test_kg_relevance_weighted.py::TestKgRelevanceMultiEdgeInflation` 守卫，相关讨论见 `design.md` D-fix 段

**为什么是它 #2**：A3 直指三因子权重，这份 spec 是"权重之一（kg_relevance）从坏到好"的完整契约。配合 #1 verification-service spec，覆盖 A3 的两个质疑。

---

### 🎯 #3 — `design.md`（25226 bytes，464 行左右）

**追踪 A3 的哪个方面**：所有质疑的"为什么"+ Meta-lesson 段落

**完整路径**：
```
openspec/changes/archive/2026-04-07-fix-fr-kg-04-schema-drift-and-sync-hardening/design.md
```

**关键章节**：
- `## Meta-lesson` 段落 (line 5: "这是教科书级的 silent degradation") — 直接回应 A3 的 "silent degradation" 质疑
- D1-D9 决策（特别是 D7 Dependency-Aware Segment Commit @ line 132 和 D8 SyncErrorClass @ line 231；D6 已被合并删除）
- `**Non-Goals:**` 段（line 30-37）严禁修改清单
- `**当前状态**:` 段（line 8-14）documents 受影响文件 + 行号 + ✅/❌ 状态标记 — **注意 design.md 没有显式 `## Affected Code` header**，相关内容在 `**当前状态**:` 段

**读这份 design.md 你能直接定位**：
- 为什么 schema drift 问题没被任何深度研究报告发现：研究报告基于过时代码快照，漏掉了真正的 P0 bug
- 完整的"silent degradation"文字记录："`_get_kg_relevance` 的 Cypher 查询字段（`{uuid}` + `canvas_id`）与 `SyncService` 的写入字段（`{id}` + `canvasId`）完全不匹配，导致 KG 相关性信号永远返回默认值 0.5，30% 的考试优先级权重完全失效"
- 三套幽灵 schema 的位置：`question_generator.py:673,751` + `exam_service_ext.py:67,100-101`
- 异常分类决策树（Phase 4/8）

**为什么是它 #3**：spec 告诉你"应该是什么"，design.md 告诉你"为什么这样"。A3 用户问"是不是自己编的"——design.md 的 meta-lesson 段落是最直接的回答："不是编的，是修了一个被两份独立深度研究都漏掉的 silent degradation"。

---

### 不推荐为 #4 但值得知道的文件

| 文件 | 大小 | 何时读 |
|---|---|---|
| `tasks.md` | 33831 bytes | 想看 Phase 编号到具体 task 的对应；想看 Sprint 1.2.1 Code Review fixes 的完整清单 |
| `proposal.md` | 16513 bytes | 想看修复的 Why + What Changes + Affected Code 的高层视角 |
| `specs/canvas-sync/spec.md` | 281 行 | 想追踪 sync 三段事务 + X-CLS-Internal-Key 鉴权 spec |
| `specs/llm-safety/spec.md` | 93 行 | 想追踪 LLM prompt injection 防护 |
| `specs/algo-scoring/spec.md` | 29 行 | 想追踪 BKT 评分链路 |
| `deprecation-schedule.md` | 1851 bytes | 想看哪些代码被标记为 deprecated（CONNECTS_TO 等）|

---

## Part 2 — Claude Code Desktop 可执行的端到端测试矩阵

### CC Desktop 能力清单

| 能力 | 工具 | 适用场景 |
|---|---|---|
| ✅ 跑 pytest | Bash | backend 全部 unit/integration/e2e 测试 |
| ✅ 启动 uvicorn 后台 | Bash (`run_in_background=true`) | 让 backend 持续在 :8000 运行 |
| ✅ Curl HTTP API | Bash | 测试 `/api/v1/sync/batch`、`/api/v1/exam/start` 等 |
| ✅ 启动 Vite dev server 后台 | Bash (`npm run dev`, `run_in_background=true`) | 前端跑在 :5173 浏览器可访问 |
| ✅ Chrome 浏览器自动化 | `mcp__claude-in-chrome__*` | 操作 React UI、读 console、读 network、跑 JavaScript |
| ✅ 跑 vitest | Bash (`npm test`) | 前端单元测试 |
| ❌ 操作 Tauri 桌面窗口 | — | Tauri app 窗口 Chrome 看不到 |
| ❌ 操作 sidecar 进程 | — | sidecar 是 Tauri Command 启动的，Chrome 自动化无法触发 |

### 测试入口分类

#### **Lane 1：纯 pytest（最快、零依赖）**

`★ 推荐 ★` 这是 CC Desktop 最直接的端到端验证方式。所有以下测试都已落地、可立即运行。

| 文件 | 测试数 | 直接关联 A3 的什么 | 外部依赖 |
|---|---|---|---|
| `backend/tests/unit/test_kg_relevance_weighted.py` | 19 | A3 质疑 2：kg_relevance 加权 + 多边防护 + degraded marker | 无 |
| `backend/tests/unit/test_mock_degradation_transparency.py` | **30** (Phase 3 实测) | A3 质疑 1：Phase 17.1 fail-closed + Phase 17.2 path traversal + Story 31.A.8 mock degradation logging | 无 |
| `backend/tests/unit/test_verification_service_activation.py` | 15 | Phase 17 verification 初始化 + 降级 + path traversal 集成 | 无 |
| `backend/tests/unit/test_verification_service_injection.py` | 5 | Story 31.A.1 graphiti_client 注入链 | 无 |
| `backend/tests/unit/test_neo4j_field_consistency.py` | 7 | Phase 15 字段一致性（r.score / r.review_count） | 无 |
| `backend/tests/unit/test_sync_batch_auth.py` | 7 | Phase 2 X-CLS-Internal-Key fail-closed 矩阵 | 无 |
| `backend/tests/unit/test_sync_segment_commit.py` | 14 | Phase 4/8/11 三段事务 + ConstraintError 分类 | 无 |
| `backend/tests/unit/test_sync_payload_validation.py` | 11 | Phase 13 Pydantic validators | 无 |
| `backend/tests/unit/test_sync_exception_classification.py` | 6 | Phase 4 异常分类 503/500 | 无 |
| `backend/tests/integration/test_verification_service_e2e.py` | 6 | Story 31.1 verification 完整流程（mock-based） | 无 |
| `backend/tests/integration/test_verification_service_di_completeness.py` | 6 | DI 完整性 + Settings.canvas_base_path 传播 | 无 |
| `backend/tests/e2e/test_a11_kg_relevance_e2e.py` | 7 | **Phase 5 Task 5.1 真正的 e2e**：Schema、kg_relevance 加权、degraded marker、select_target_node 排序 | **可选** Neo4j @ bolt://localhost:7692（不可达自动 skip 不 fail） |

**Lane 1 一键全跑命令**（CC Desktop 直接执行）：
```bash
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/backend
.venv/bin/pytest \
  tests/unit/test_kg_relevance_weighted.py \
  tests/unit/test_mock_degradation_transparency.py \
  tests/unit/test_verification_service_activation.py \
  tests/unit/test_verification_service_injection.py \
  tests/unit/test_neo4j_field_consistency.py \
  tests/unit/test_sync_batch_auth.py \
  tests/unit/test_sync_segment_commit.py \
  tests/unit/test_sync_payload_validation.py \
  tests/unit/test_sync_exception_classification.py \
  tests/integration/test_verification_service_e2e.py \
  tests/integration/test_verification_service_di_completeness.py \
  tests/e2e/test_a11_kg_relevance_e2e.py \
  -v --tb=short
```

**预期**：**133 tests** 全绿（其中 7 个 e2e 如果 Neo4j 7692 不可达会自动 skip 而非 fail）。Phase 3 review (2026-04-07) 修正：上一版 plan 写 117，错误源是 `test_mock_degradation_transparency.py` 实际 30 tests 而非 14。

---

#### **Lane 2：HTTP-level（uvicorn + curl）**

`★ CC Desktop 启动后台进程 + curl 验证 ★`

**启动**（CC Desktop 用 `run_in_background=true`）：
```bash
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/backend
.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**关键端点（端到端 A3 链路）**：

| Endpoint | 实现文件 | 验证点 | A3 关联 |
|---|---|---|---|
| `POST /api/v1/sync/batch` | `backend/app/api/v1/endpoints/sync.py:23` | Phase 2 鉴权 fail-closed 矩阵 + Phase 4 异常分类 + Phase 11 三段事务 | 间接：让 kg_relevance 公式有数据可算 |
| `POST /api/v1/exam/start` | `backend/app/api/v1/endpoints/exam.py:52` | 进入 `select_target_node()` → `_get_kg_relevance()` 加权公式生效 | 直接：质疑 2 |
| `POST /api/v1/exam/{id}/verify` | `backend/app/api/v1/endpoints/exam.py` | 进入 `VerificationService.process_answer()` → fail-closed 路径 | 直接：质疑 1 |
| `POST /api/v1/exam/{id}/hint` | `backend/app/api/v1/endpoints/exam.py` | Chain-of-Hints | 间接 |
| `POST /api/v1/exam/{id}/complete` | `backend/app/api/v1/endpoints/exam.py` | 写入考试记录 | 间接 |
| `GET /api/v1/exam/by-canvas/{canvas_id}` | `backend/app/api/v1/endpoints/exam.py` | 列举 session | 无 |

**鉴权**：所有 `/sync/batch` 请求需要 `X-CLS-Internal-Key` header（生产模式 503 if missing；DEBUG 模式允许 with warning）。

**Curl 示例（CC Desktop 可直接执行）**：
```bash
# 1. 测 sync 鉴权矩阵 — 期望 200 (DEBUG mode 允许空 key)
curl -X POST http://127.0.0.1:8000/api/v1/sync/batch \
  -H "Content-Type: application/json" \
  -d '{"canvas_id":"test-canvas","subject_id":"test-subject","operations":[]}'

# 2. 测 sync 节点写入 — 端到端 SyncService → Neo4j
curl -X POST http://127.0.0.1:8000/api/v1/sync/batch \
  -H "Content-Type: application/json" \
  -d '{
    "canvas_id":"test-canvas",
    "subject_id":"test-subject",
    "operations":[{
      "operation_id":"00000000-0000-0000-0000-000000000001",
      "entity_type":"node",
      "entity_id":"node-1",
      "operation":"create",
      "payload":{"title":"Newton First Law","content":"测试节点"},
      "timestamp":"2026-04-07T00:00:00Z"
    }]
  }'

# 3. 触发考试模式 — 走 kg_relevance 加权路径
curl -X POST http://127.0.0.1:8000/api/v1/exam/start \
  -H "Content-Type: application/json" \
  -d '{"source_canvas_id":"test-canvas","exam_mode":"comprehensive"}'

# 4. 测 path traversal 防护 — 期望返回 ["默认概念"]，不读宿主文件
curl -X POST http://127.0.0.1:8000/api/v1/exam/test-id/verify \
  -H "Content-Type: application/json" \
  -d '{"canvas_name":"../../etc/passwd","user_answer":"test"}'
```

---

#### **Lane 3：Vite Web Mode + Chrome 自动化**

`★ CC Desktop 用 mcp__claude-in-chrome__* 驱动浏览器 ★`

**前置可行性确认**（来自 Agent 3 探索）：
- ✅ `frontend/package.json` 有 `npm run dev`（Vite dev server, port 5173）
- ✅ `frontend/src/main.tsx` 无 Tauri 硬依赖
- ✅ 4 个 Tauri-only service（docker-manager / backup-manager / obsidian-link / claude-engine）都是延迟加载，不影响启动
- ✅ Canvas / Exam / Chat / Verification UI 全部可用
- ❌ Sidecar 不可用（Claude scoring 走 sidecar 时无法测）

**启动**（CC Desktop 后台）：
```bash
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/frontend
npm run dev
# → http://localhost:5173
```

**Chrome 自动化可测的 A3 路径**：

| 测试场景 | Chrome 工具 | 验证点 |
|---|---|---|
| Canvas → Outbox 流水线 | `javascript_tool` 查询 IndexedDB | 验证 `db.sync_outbox` 在 addNode 后有新条目 |
| API X-CLS-Internal-Key 注入 | `read_network_requests` | 验证 `/sync/batch` 请求 header 含 `X-CLS-Internal-Key` |
| SyncErrorClass 路由 | `javascript_tool` mock fetch + 查 outbox | 模拟后端返回 VALIDATION_ERROR → 验证 `permanentlyFailed=true` |
| VerificationModal degraded UI | `find` + `form_input` + `read_page` | 提交答案后断言橙色警告条出现 |
| Console 日志检查 | `read_console_messages` (pattern: `kg_relevance`) | 验证后端通过 fetch 返回的 `degraded` 字段 |

**关键前端文件**（A3 修复入口，CC Desktop 用 Chrome 操作时要观察这些位置）：

| 文件 | 行号 | 功能 |
|---|---|---|
| `frontend/src/services/api-client.ts` | L130 / L176-185 | `internalApiKey` + `buildHeaders()` 注入 X-CLS-Internal-Key |
| `frontend/src/services/sync-engine.ts` | L266-290 | SyncErrorClass 路由（VALIDATION/DEPENDENCY_MISSING/TRANSIENT） |
| `frontend/src/components/review/VerificationModal.tsx` | L205, L219-227 | `degraded` flag 解构 + 橙色警告条 |
| `frontend/src/services/__tests__/sync-engine-error-class.test.ts` | 245 行 | Vitest 覆盖 SyncErrorClass 路由 |
| `frontend/src/services/__tests__/sync-engine-canvasid-enforcement.test.ts` | 139 行 | Vitest 覆盖 canvasId 强制 |
| `frontend/src/services/api-client.test.ts` | 131 行 | Vitest 覆盖 X-CLS-Internal-Key 注入 |

**前端测试一键跑命令**：
```bash
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/frontend
npm test
```

**Chrome 自动化可行性等级（来自 Agent 3 评估）**：**Medium-High**
- ✅ 完整可测：Canvas/Exam/Chat 交互 + sync outbox 状态 + verification UI + API header 检查
- ⚠️ 受限：Sidecar 通信不可用（影响真正的 LLM 评分），但可以 mock fetch 绕过
- ❌ 不可用：Docker / Backup / Obsidian (Tauri-only)

---

## Part 3 — 推荐执行顺序（CC Desktop 实操路径）

| 步骤 | 命令 / 操作 | 时长 | 产出 |
|---|---|---|---|
| **S1** | Bash: 跑 Lane 1 一键全跑（`pytest ... 12 个文件`） | ~30s | **133 tests** 数字 + skip 数（确认 e2e Neo4j 状态） |
| **S2** | Bash 后台: `uvicorn app.main:app --port 8000` | 即时 | backend 跑起来 |
| **S3** | Bash: 跑 Lane 2 4 个 curl（sync_batch 鉴权 + sync_batch 写节点 + exam_start + verify path traversal） | ~5s | HTTP 200/403/503 状态 + JSON 响应 |
| **S4** | Bash 后台: `cd frontend && npm run dev` | 5-10s | Vite dev server :5173 |
| **S5** | Chrome: `tabs_create_mcp("http://localhost:5173")` → `read_page` 检查 React 加载 | 即时 | App 启动确认（无 Tauri 崩溃） |
| **S6** | Chrome: `find` 找节点创建按钮 → `form_input` 输入标题 → `read_network_requests` 抓 sync 请求 | ~20s | 端到端 sync 流水线证据 |
| **S7** | Bash: `npm test`（前端 vitest） | ~10s | 前端单元测试结果 |

**总耗时估计**：~60-90 秒（不含 npm install / venv 准备）。

---

## Critical Files 索引（绝对路径，给 CC Desktop 用）

### OpenSpec 追踪 (3 个最重要)

| 优先 | 文件 | 行数 |
|---|---|---|
| #1 | `/Users/Heishing/Desktop/canvas/canvas-learning-system/openspec/changes/archive/2026-04-07-fix-fr-kg-04-schema-drift-and-sync-hardening/specs/verification-service/spec.md` | 126 |
| #2 | `/Users/Heishing/Desktop/canvas/canvas-learning-system/openspec/changes/archive/2026-04-07-fix-fr-kg-04-schema-drift-and-sync-hardening/specs/algo-question/spec.md` | 93 |
| #3 | `/Users/Heishing/Desktop/canvas/canvas-learning-system/openspec/changes/archive/2026-04-07-fix-fr-kg-04-schema-drift-and-sync-hardening/design.md` | ~464 (25KB) |

### CC Desktop 可执行 e2e 测试文件（12 个）

```
/Users/Heishing/Desktop/canvas/canvas-learning-system/backend/tests/unit/test_kg_relevance_weighted.py
/Users/Heishing/Desktop/canvas/canvas-learning-system/backend/tests/unit/test_mock_degradation_transparency.py
/Users/Heishing/Desktop/canvas/canvas-learning-system/backend/tests/unit/test_verification_service_activation.py
/Users/Heishing/Desktop/canvas/canvas-learning-system/backend/tests/unit/test_verification_service_injection.py
/Users/Heishing/Desktop/canvas/canvas-learning-system/backend/tests/unit/test_neo4j_field_consistency.py
/Users/Heishing/Desktop/canvas/canvas-learning-system/backend/tests/unit/test_sync_batch_auth.py
/Users/Heishing/Desktop/canvas/canvas-learning-system/backend/tests/unit/test_sync_segment_commit.py
/Users/Heishing/Desktop/canvas/canvas-learning-system/backend/tests/unit/test_sync_payload_validation.py
/Users/Heishing/Desktop/canvas/canvas-learning-system/backend/tests/unit/test_sync_exception_classification.py
/Users/Heishing/Desktop/canvas/canvas-learning-system/backend/tests/integration/test_verification_service_e2e.py
/Users/Heishing/Desktop/canvas/canvas-learning-system/backend/tests/integration/test_verification_service_di_completeness.py
/Users/Heishing/Desktop/canvas/canvas-learning-system/backend/tests/e2e/test_a11_kg_relevance_e2e.py   ← 真正的 Phase 5 Task 5.1 e2e
```

### 实现侧代码入口

| 文件 | 行号 | 修复 |
|---|---|---|
| `backend/app/services/question_generator.py` | 26, 103-203, 700-792 | kg_relevance 加权 + Sprint 1.2.1 typed exception catch |
| `backend/app/services/verification_service.py` | 760-860 + `_resolve_safe_canvas_path` | Phase 17.1 fail-closed + Phase 17.2 path traversal |
| `backend/app/services/sync_service.py` | `process_sync_batch` | Phase 11 三段事务 + Phase 4/8 异常分类 |
| `backend/app/api/v1/endpoints/sync.py` | 23 | Phase 2 `require_internal_api_key` 依赖 |
| `backend/app/security.py` | — | X-CLS-Internal-Key 实现 |
| `backend/migrations/001_canvas_constraints.cypher` | — | Neo4j 索引迁移 |
| `frontend/src/services/api-client.ts` | L130, L176-185 | X-CLS-Internal-Key 注入 |
| `frontend/src/services/sync-engine.ts` | L266-290 | SyncErrorClass 路由 |
| `frontend/src/components/review/VerificationModal.tsx` | L205, L219-227 | degraded 警告 UI |

---

## Verification — 怎么知道这份 plan 有效

**最低验证**（CC Desktop 1 步执行）：
```bash
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/backend
.venv/bin/pytest tests/unit/test_kg_relevance_weighted.py tests/e2e/test_a11_kg_relevance_e2e.py -v --tb=short
```
预期：19 + 7 = 26 tests，e2e 部分如 Neo4j 不可达会显示 7 skipped 而非 7 failed。看到 `test_canvas_edge_only_three_neighbors PASSED` 证明 plan 文档对应的 A3 修复在你的本地有效。

**中级验证**：跑 Part 2 Lane 1 一键全跑命令（117 tests）。

**完整验证**：依次跑 S1 → S7（推荐执行顺序），结合 Chrome 自动化驱动 Vite web mode 完成端到端 A3 链路验证。

---

## What Changed vs. 上一份 plan

| 方面 | 上一份 plan | 本次更新 |
|---|---|---|
| OpenSpec 路径 | `openspec/changes/fix-fr-kg-04-schema-drift-and-sync-hardening/...`（**全部失效**） | `openspec/changes/archive/2026-04-07-fix-fr-kg-04-schema-drift-and-sync-hardening/...` |
| Phase 5 Task 5.1 | `❌ NOT YET CREATED` | ✅ 已存在 `tests/e2e/test_a11_kg_relevance_e2e.py`（7 tests） |
| Tier C "Tauri 操作" | 写"在 Tauri app 里点" | 改为 Vite web mode + Chrome 自动化（CC Desktop 可执行） |
| 测试文件清单 | 8 个 | 12 个（新增 verification_service_activation/injection、neo4j_field_consistency、di_completeness、a11_kg_relevance_e2e） |
| OpenSpec 关键文件 | 5 个混合（tasks/spec/design/proposal/deprecation） | 聚焦 3 个（verification-service spec / algo-question spec / design.md），用户用它们定位 A3 |

---

## Self-Check

- [x] Phase 1 探索：3 个并行 Explore agent（openspec 文件 / backend e2e 入口 / frontend web mode）
- [x] Phase 1 verification：用绝对路径验证 agent 报告（archive 路径正确、test_a11_kg_relevance_e2e.py 存在、cwd 是 backend 不是 root）
- [x] Phase 2 设计：跳过独立 Plan agent — 这是导航文档不是实施任务
- [x] Phase 3 review：纠正 agent 错误（archive 路径、cwd 混淆 + Agent C cwd 大错位）
- [x] Phase 4 写入计划文件（覆盖上一份过时的 distributed-jingling-gizmo.md）
- [x] Phase 5 ExitPlanMode → main session 实测：30 tests 全绿（含 sentinel `test_canvas_edge_only_three_neighbors`），Neo4j 7692 本地可达 → 0 skipped
- [x] **Phase 6 (2026-04-07 second pass)** Deep verify by 3 fresh Explore agents → 4 真实 gap 修正（Part 1#1 scenario 8→16、Part 1#2 删 H-1 误置 claim、Part 1#3 修 design.md header 描述、Part 2 test count 14→30 / 117→133）

---

## Phase 6 — Deep Verification Findings (2026-04-07)

> 用户在 second pass plan mode 显式要求"启动并行 agent deep explore"。3 个 Explore agent 独立验证当前 plan 的所有具体声明，发现 5 处 mismatch（4 个真实 plan gap + 1 个 agent cwd 错位）。

### Real plan gaps (已修正)

| # | Source | Claim 错误 | 实际 | 修正动作 |
|---|---|---|---|---|
| 1 | Agent A | `verification-service/spec.md` 8 个 Scenario | **16 个**（fail-closed 8 + path traversal 8）| ✅ Part 1 #1 已改 |
| 2 | Agent A | `algo-question/spec.md` 含 Sprint 1.2.1 H-1 多边膨胀防护 | **不在 spec 内** — 是代码层修复 | ✅ Part 1 #2 加注释说明位置 |
| 3 | Agent A | `design.md` 有 `## Affected Code` header | **不存在** — 内容在 `**当前状态**:` 段 (line 8-14) | ✅ Part 1 #3 修正 header 描述 |
| 4 | Agent B | `test_mock_degradation_transparency.py` 14 tests | **30 tests** → Lane 1 总数 117 → **133** | ✅ Part 2 Lane 1 表格 + 预期 + S1 全部已改 |

### Agent C 失误案例 (不是 plan 错，是 agent 错)

Agent C 报告 frontend Lane 3 几乎全部声明失实：
- ❌ Agent C 说: `sync-engine.ts` 不存在 → **实际存在** (验证见 main session)
- ❌ Agent C 说: `VerificationModal.tsx` 不存在 → **实际存在** (`components/review/`)
- ❌ Agent C 说: 3 个测试文件不存在 → **实际全部存在** (`api-client.test.ts` + `__tests__/sync-engine-error-class.test.ts` + `__tests__/sync-engine-canvasid-enforcement.test.ts`)
- ❌ Agent C 说: 4 个 Tauri-only services 不存在 → **实际全部存在** (`docker-manager.ts`, `backup-manager.ts`, `obsidian-link.ts`, `claude-engine.ts`)
- ❌ Agent C 说: vite 端口 1420 → **实际 5173** (`vite.config.ts:20`)，1421 是 HMR not main port

**Root cause hypothesis**: Agent C 报告的路径有 `frontend/frontend/src/main.tsx` 双 frontend 前缀 — 明显的 cwd 混淆，可能 agent 在 frontend 子目录里跑然后又用了 `frontend/` 相对前缀。

**Lesson**: Phase 3 independent file Read 是不可省略的安全防线。如果直接信任 Agent C，会把 30% 的 plan 内容（Lane 3）误删。

### 5/5 行号声明全部独立验证为 ✅

Phase 3 review 用 main session 直接 Read 验证：

| 文件 | 行号 | Plan claim | 实际内容 (来自 Read) |
|---|---|---|---|
| `vite.config.ts` | 20 | 端口 5173 | `port: 5173, strictPort: true` ✅ |
| `api-client.ts` | 130 | `internalApiKey` 字段 | `private internalApiKey: string \| null = null;` ✅ |
| `api-client.ts` | 176-185 | `buildHeaders()` 注入 X-CLS-Internal-Key | `private buildHeaders(...) { ... headers['X-CLS-Internal-Key'] = this.internalApiKey; ...}` ✅ |
| `VerificationModal.tsx` | 205 | `degraded` flag 解构 | `const { quality, score, degraded, degradedWarning, hint, action } = lastResult;` ✅ |
| `VerificationModal.tsx` | 219-227 | 橙色警告条 | `<div className="p-3 bg-orange-900/30 border border-orange-500/50 rounded-lg">...</div>` (Phase 17.1 注释明确) ✅ |
| `sync-engine.ts` | 266-290 | SyncErrorClass switch | `const errorClass = result.errorClass ?? 'TRANSIENT_ERROR'; switch(errorClass) { case 'VALIDATION_ERROR': ... case 'DEPENDENCY_MISSING': ... case 'TRANSIENT_ERROR': ... }` ✅ |

### 不推荐合并的 #4 候选 (Agent A 建议)

Agent A 建议把 `proposal.md` 加为 #4，因为它的 A3 framing 比 design.md 更尖锐（line 36-38 "Schema drift civil war"）。**决定不加** —— plan 的目标是"3 个最重要"不是"5 个候选"。在"不推荐为 #4"表里 proposal.md 已经存在，不需要再升级。如果用户想要更尖锐的 A3 framing，直接读 proposal.md 即可。
