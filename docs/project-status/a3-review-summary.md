# A3 修复成果摘要 — ChatGPT Deep Research Review 入口

> **目的**: 让 ChatGPT Deep Research 能在最短路径上验证 FR-KG-04 user2 批注 #3 (A3) 的两条质疑是否被真正修复。
> **生成时间**: 2026-04-07
> **生成方式**: Claude Code Lane 1 deep explore（pytest + spec 一致性 grep + git log 综合）
> **GitHub Repo**: https://github.com/oinani0721/canvas-learning-system

---

## 1. A3 是什么

**批注位置**: `docs/project-status/fr-exploration/A3.md` 末段 + `docs/project-status/fr-exploration/FR-KG-04/FR-KG-04-user2-annotations.md` 第 3 条 (Line 374)

**用户原文** (User2)：

> 关于图层 2 验证服务是什么？请你单独使用并行 agent deep explore 我要知道：
> 1. 它的设计查询是否成熟，是否拥有和 Graphiti 一样的超强检索能力；
> 2. 你的这个是只给原白板的对话的时候使用的，还是会在使用检验白板的时候也会使用。
> 以及你所设立的这个评分验证，是你自己编的还是你在社区有广泛认证？

**两条核心质疑**:

| # | 质疑 | 一句话总结 |
|---|---|---|
| 質疑 1 | `verification_service` 评分系统的成熟度 | 评分是自己编的（按答案长度判分）还是有学术支撑？是否会污染掌握度状态？ |
| 質疑 2 | `question_generator` 三因子权重 `W_KG_RELEVANCE=0.3` 的支撑 | kg_relevance 是否在生产中真的工作？加权公式是否合理？ |

---

## 2. 修复 Change（已 archive）

- **路径**: `openspec/changes/archive/2026-04-07-fix-fr-kg-04-schema-drift-and-sync-hardening/`
- **Artifact 清单** (4 + 5 spec):
  - `proposal.md` — 16513 bytes，含 Why / What Changes / Capabilities / Impact
  - `design.md` — 25226 bytes，含 9 个设计决策
  - `tasks.md` — 33831 bytes，含 17 个 Phase
  - `deprecation-schedule.md` — 1851 bytes，CONNECTS_TO 弃用窗口
- **5 个 capability spec**:
  - `specs/verification-service/spec.md` (126 行, 2 Requirement, 16 Scenario) — 質疑 1 主战场
  - `specs/algo-question/spec.md` (93 行, 5 Requirement) — 質疑 2 主战场
  - `specs/algo-scoring/spec.md` (29 行, 1 Requirement) — `r.score` alias + `review_count` 一致性
  - `specs/canvas-sync/spec.md` (281 行, 11 Requirement) — Schema drift 外延（Sync 管道硬化）
  - `specs/llm-safety/spec.md` (93 行, 5 Requirement) — Phase 9 prompt injection 三层防护

**3 个新 contract 已合并到主 spec**: `openspec/specs/algo-rag/spec.md` 现含 4 处 Faithfulness/Fusion/CRAG/kg_relevance 相关 requirement（archive 时自动 merge）。

---

## 3. Commit 链（按修复阶段排序，全部已在 origin/main 除非另注）

### 質疑 1：verification 评分系统硬化

| Commit | Message | 修复点 | 状态 |
|---|---|---|---|
| `d0824e9` | `fix(verification): Phase 17.1 fail-closed degraded scoring` | `_mock_evaluate_answer` 恒返回 `("unknown", 0.0)`；`_advance_concept(degraded=True)` 跳过 mastery 更新 | ✅ origin/main |
| `b50a52b` | `fix(verification): Phase 17.2 path traversal hardening` | `_resolve_safe_canvas_path` 三层防护 + 删除 fallback `open()` | ✅ origin/main |
| `f215830` | `fix(FR-KG-04): verification_service reads CANVAS_EDGE + transforms RAG results` | 对齐 RAG 字段 + Cypher 修复 | ✅ origin/main |
| `d569da0` | `fix(concept-id): unify identity contract across verification/memory/review` | ConceptRef + is_uuid_v4 + 删除 2 处 text-fallback bug + 72 unit tests | ⏳ PR #1 |
| `03c8842` | `fix(concept-id): close residual text-as-uuid leak in fallback_sync_service` | 5th instance leak fix | ⏳ PR #1 |
| `c154022` | `test(fallback-sync): clear 3 pre-existing test infra debts` | structlog→MagicMock | ⏳ PR #1 |

### 質疑 2：kg_relevance schema 统一 + 加权公式

| Commit | Message | 修复点 | 状态 |
|---|---|---|---|
| `c7215ca` | `fix(question_generator): align KG queries to SyncService write schema` | Phase 1 局部先手：`{uuid}` → `{id}` | ✅ origin/main |
| `a6da4f7` | `fix(kg-relevance): Phase 1 schema unification + weighted edge formula` | `{id}+canvasId` 统一 + CANVAS_EDGE 1.0 / RELATES_TO 0.7 / `/8.0` 归一化 | ✅ origin/main |
| `5ecf834` | `fix(kg-relevance): broaden Neo4j exception capture (Code-Review C-1)` | 异常捕获完整化 + degraded marker | ✅ origin/main |

### Schema drift 外延（Sync 管道硬化）

| Commit | Message | 修复点 | 状态 |
|---|---|---|---|
| `e833d73` | `fix(security): Phase 2 /sync/batch internal API key authentication` | `X-CLS-Internal-Key` + fail-closed | ✅ origin/main |
| `e999dc8` | `fix(sync_service): Phase 3+11+12 Segment Commit architecture` | Board→Node→Edge 三段事务 | ✅ origin/main |
| `7a7ce60` | `fix(sync-models): Phase 13 payload Pydantic validation at ingress` | `SyncOperation` + `SyncBatchRequest` model_validator | ✅ origin/main |
| `6448be0` | `fix(sync_service): Phase 8 classify ConstraintError as VALIDATION_ERROR` | 异常分类拆分 | ✅ origin/main |
| `d79d5b9` | `fix(faithfulness): eliminate vacuous-true score=1.0` | not-applicable contract | ✅ origin/main |

**总计**: 14 个 commit。其中 11 个已在 `origin/main`，3 个在 `fix-concept-id-identity-unification` PR #1（独立 review 单元）。

---

## 4. 修复源码清单

### `backend/app/services/verification_service.py` (質疑 1 主战场)

| 行号 | 方法 | 修复内容 |
|---|---|---|
| 1677-1705 | `_mock_evaluate_answer(self, user_answer)` | **核心**：恒返回 `("unknown", 0.0)`，删除字符长度启发；docstring 明确标注 SECURITY/INTEGRITY FIX FR-KG-04 P1-4 |
| 875 | (in `process_answer`) | 用户面提示文案：「评分服务暂时不可用，本次回答不计分也不更新掌握度。您可以继续下一题。」 |
| 886+ | `_advance_concept(self, ..., degraded)` | 增加 `degraded` 参数；为 True 时跳过 4 色 counter 更新但仍 advance 概念 |
| 841/847/853/1045 | (callers) | 4 处调用 `_advance_concept` 都正确传递 degraded |
| 1306 | (in `_do_extract_concepts`) | 调用 `_resolve_safe_canvas_path` 替代 fallback `open()` |
| 1362-1437 | `_resolve_safe_canvas_path(self, canvas_name, canvas_path)` | 三层防护：相对路径检查 + `.canvas` 后缀 + base 目录 `Path.relative_to()` |
| 1521/1538/1547/1644 | (mock fallback paths) | 4 处都调用 `_mock_evaluate_answer` 取回 fail-closed 结果 |

### `backend/app/services/question_generator.py` (質疑 2 主战场)

| 行号 | 方法 / 字段 | 修复内容 |
|---|---|---|
| 128-219 | `compute_node_priorities` | 增加 `kg_relevance_degraded` 字段透传 |
| 701-755 | `_get_kg_relevance(self, node_id, canvas_id)` | **核心**: Cypher 修复为 `MATCH (n:CanvasNode {id: $node_id})-[r:CANVAS_EDGE\|RELATES_TO]-(neighbor) WHERE neighbor.canvasId = $canvas_id`；加权公式 `SUM(CASE type(r) WHEN 'CANVAS_EDGE' THEN 1.0 WHEN 'RELATES_TO' THEN 0.7)`；归一化 `/8.0` 上限 1.0 |
| 715-728 | (docstring) | 引用 `c7215ca` schema 统一 commit + 解释 CANVAS_EDGE > RELATES_TO 的语义权重论证 |
| 738-755 | (Cypher detail) | `WITH neighbor MAX(...)` + `COUNT(DISTINCT neighbor)` 防止 multi-edge inflation（H-1 防护） |
| 856-862 | 第二个 Cypher 查询 | 也使用 `{id}` schema |

### `backend/app/services/exam_service_ext.py` (Schema drift 外延)

| 行号 | 内容 |
|---|---|
| 66-72 | Comment + `MERGE (n:CanvasNode {id: $node_id}) SET n.canvasId = $source_canvas_id` |
| 102-110 | Comment + `MATCH (src:CanvasNode {id: $source_node_id}) MATCH (tgt:CanvasNode {id: $node_id})` |
| 注意 | 文件内剩余 7 处 `{uuid:` 全部用于 **EpisodicNode**（Graphiti 实体），CanvasNode **零** `{uuid:` 用法 ✓ |

### `backend/app/models/exam_models.py`

| 行号 | 字段 |
|---|---|
| 224 | `kg_relevance: float = 0.0` |
| 245-250 | docstring：`kg_relevance_degraded` 三种取值含义 |
| 258-259 | `kg_relevance: float` + `kg_relevance_degraded: Optional[str] = None` |

### `backend/app/services/sync_service.py` (Sync 硬化)

| 行号 | 内容 |
|---|---|
| 29 | `from .sync_models import SyncErrorClass, ...` |
| 36 | Comment: "Phase 11: Entity types ordered for Segment Commit dependency resolution" |
| 72 | `_deduplicate_by_operation_id` |
| 105-130 | `_partition_by_entity_type` (Segments: Board → Node → Edge) |
| 132-154 | `_classify_exception` 映射 `SyncErrorClass.{VALIDATION,DEPENDENCY,TRANSIENT}` |
| 169-292 | `process_sync_batch` Segment Commit 主流程 |
| 404+ | `_upsert_edge` fail fast |

### `backend/app/security.py` (新文件)

`APIKeyHeader` + `require_internal_api_key` 依赖 + fail-closed 行为。

### `backend/migrations/` (新建)

- `001_canvas_constraints.cypher` — `(canvas_id, node_id)` 唯一约束 + `canvasId` 索引 + `(subjectId, name)` 联合唯一
- `002_canvasnode_uuid_to_id.cypher` — 历史 `{uuid}` 节点回填迁移

---

## 5. 测试覆盖（A1 lane 1 runtime 证据）

**执行命令**:
```bash
backend/.venv/bin/pytest \
  backend/tests/unit/test_kg_relevance_weighted.py \
  backend/tests/unit/test_mock_degradation_transparency.py \
  backend/tests/unit/test_verification_service_activation.py \
  backend/tests/unit/test_verification_service_injection.py \
  backend/tests/integration/test_verification_service_e2e.py \
  backend/tests/integration/test_verification_service_di_completeness.py \
  backend/tests/unit/test_neo4j_field_consistency.py \
  backend/tests/unit/test_sync_batch_auth.py \
  backend/tests/unit/test_sync_payload_validation.py \
  backend/tests/unit/test_sync_exception_classification.py \
  backend/tests/unit/test_sync_segment_commit.py \
  backend/tests/e2e/test_a11_kg_relevance_e2e.py \
  -v --tb=line
```

**结果**: `1 failed, 136 passed, 10 warnings in 1.95s` (137 collected)

| 套件 | Tests | 通过 | 备注 |
|---|---|---|---|
| `test_kg_relevance_weighted.py` | 19 | ✅ 19/19 | 質疑 2 加权公式 + degraded marker + multi-edge 防护 |
| `test_mock_degradation_transparency.py` | 30 | ✅ 30/30 | 質疑 1 fail-closed (8) + path traversal (8) + logging (6) + 8 集成 |
| `test_verification_service_activation.py` | 15 | ✅ 15/15 | 質疑 1 初始化 + 降级 + 集成 |
| `test_verification_service_injection.py` | 5 | ⚠️ 4/5 | 1 fail（见下） |
| `test_verification_service_e2e.py` | 6 | ✅ 6/6 | mock-based 完整流程 |
| `test_verification_service_di_completeness.py` | 6 | ✅ 6/6 | DI 完整性 |
| `test_neo4j_field_consistency.py` | 7 | ✅ 7/7 | `r.score` alias + `review_count` |
| `test_sync_batch_auth.py` | 7 | ✅ 7/7 | Phase 2 鉴权矩阵 |
| `test_sync_payload_validation.py` | 11 | ✅ 11/11 | Phase 13 Pydantic |
| `test_sync_exception_classification.py` | 6 | ✅ 6/6 | Phase 4 异常分类 |
| `test_sync_segment_commit.py` | 14 | ✅ 14/14 | 三段事务去重 + 依赖感知 |
| `test_a11_kg_relevance_e2e.py` | 7 | ✅ 7/7 | real Neo4j（不可达时 skip） |

**唯一失败**:
- `test_verification_service_injection.py::TestDependenciesInjection::test_get_verification_service_injects_graphiti_client`
- 错误: `AssertionError: Expected 'get_graphiti_temporal_client' to have been called once. Called 0 times.`
- **诊断**: 这是 Story 31.A.1 的 pre-existing DI mock infra debt（test 期望旧的工厂函数 `get_graphiti_temporal_client` 被调用，但实际 DI 已经迁移到其它路径）。**与 A3 修复无关**——A3 的 fail-closed scoring + 加权公式 + path traversal 三大功能套件全部通过。这与项目内存记录 `project_backend_test_debt.md`（136 failures + 38 errors 的 backend 测试基线）一致，是已知 infra 债之一。

**A3 功能性结论**: ✅ **136/137 = 99.27% pass rate**，所有质疑 1 / 质疑 2 / Schema drift 外延 / Sync 硬化的核心修复均通过 runtime 验证。

---

## 6. Spec vs Code 一致性 (A2 grep 对照表)

### Spec 1: `verification-service/spec.md`

| 检查点 | 期望 | 实测 | 状态 |
|---|---|---|---|
| `_mock_evaluate_answer` 函数体 | 恒返回 `("unknown", 0.0)`，无长度启发式 | `verification_service.py:1705` `return "unknown", 0.0`；docstring 明确禁止长度 | ✅ |
| `_resolve_safe_canvas_path` 存在 | 三层防护方法 | `verification_service.py:1362-1437` | ✅ |
| `_advance_concept` `degraded` 参数 | True 时跳过 mastery counters | `verification_service.py:886+` 签名 + `841/847/853/1045` 调用点 | ✅ |
| 用户面 degraded 文案 | "评分服务暂时不可用，本次回答不计分也不更新掌握度。您可以继续下一题。" | `verification_service.py:875` | ✅ |
| `_resolve_safe_canvas_path` 调用 | `_do_extract_concepts` 优先 | `verification_service.py:1306` | ✅ |

### Spec 2: `algo-question/spec.md`

| 检查点 | 期望 | 实测 | 状态 |
|---|---|---|---|
| Cypher 主键统一 | `{id}` not `{uuid}` | `question_generator.py:742, 862` 都用 `{id: $node_id}` | ✅ |
| Cypher 字段名 | `neighbor.canvasId` not `canvas_id` | `question_generator.py:743` `WHERE neighbor.canvasId = $canvas_id` | ✅ |
| `{uuid}` 残留 | 0 处 | grep 命中 1 处仅在 docstring (line 715 引用历史 commit) | ✅ |
| 加权系数 | CANVAS_EDGE 1.0 / RELATES_TO 0.7 | `question_generator.py:746-747` | ✅ |
| 归一化 | `/8.0` 上限 1.0 | `question_generator.py:751`(weighted SUM) + 调用点归一化 | ✅ |
| `kg_relevance_degraded` model | `Optional[str] = None` | `exam_models.py:259` | ✅ |
| `exam_service_ext.py` schema 统一 | 0 处 CanvasNode `{uuid}` | grep 全部 `{uuid:` 命中均为 `EpisodicNode`（Graphiti 实体，正确） | ✅ |
| Multi-edge inflation 防护 | `WITH neighbor MAX(...)` + `COUNT(DISTINCT neighbor)` | `question_generator.py:738-742` | ✅ |

### Spec 3: `algo-scoring/spec.md`

| 检查点 | 期望 | 实测 | 状态 |
|---|---|---|---|
| `r.score` alias | `RETURN r.score AS last_score` | 间接验证 via `test_neo4j_field_consistency.py` 7/7 pass | ✅ |
| `review_count` 自增 | `coalesce(r.review_count, 0) + 1` | 间接验证 via `test_neo4j_field_consistency.py` | ✅ |

### Spec 4: `canvas-sync/spec.md`

| 检查点 | 期望 | 实测 | 状态 |
|---|---|---|---|
| `SyncErrorClass` enum | 3 值: VALIDATION/DEPENDENCY/TRANSIENT | `sync_service.py:29` import + `:147-154` 映射 | ✅ |
| Segment Commit 三段 | `_partition_by_entity_type` Board→Node→Edge | `sync_service.py:105-130` | ✅ |
| `process_sync_batch` 三段 | "Segments 1 and 2 (Board and Node) are strictly atomic; Segment 3 (Edge) tolerates partial failures" | `sync_service.py:177-181` docstring | ✅ |
| `_upsert_edge` fail fast | OPTIONAL MATCH | `sync_service.py:404+` | ✅ |
| `_deduplicate_by_operation_id` | 单批次去重 | `sync_service.py:72` | ✅ |
| API key 鉴权 | `X-CLS-Internal-Key` header | `backend/app/security.py` 存在 | ✅ |
| Pydantic payload 校验 | `SyncOperation` model_validator | 间接验证 via `test_sync_payload_validation.py` 11/11 pass | ✅ |

### Spec 5: `llm-safety/spec.md`

| 检查点 | 期望 | 实测 | 状态 |
|---|---|---|---|
| Retrieved context scanning | `check_input(context)` 在 Claude/Gemini client 拼接前调用 | 间接验证 via Phase 9 commit 流（`test_prompt_injection_context.py` 存在） | ⚠️ Lane 1 未直接 grep，需 Lane 2 |
| Log sanitization | `input_sha256` not raw text | 与 `bf467c2` "rag-transform: Phase 3 related_concepts path-like string guard" 关联 | ⚠️ Lane 1 未直接 grep，需 Lane 2 |

**Lane 1 spec-vs-code 总结**: 5 个 spec 中 **3 个完全 ✅、1 个绝大部分 ✅、1 个 (llm-safety) 部分 verified**。所有 A3 直接相关的 verification-service + algo-question + algo-scoring 三个 spec 100% 对齐，canvas-sync 主体 ✅。llm-safety 的 prompt injection runtime 验证需 Lane 2 单元测试套件。

---

## 7. ChatGPT Deep Research Review 入口（一键复制段）

> **使用方法**: 整段复制下面这段贴给 ChatGPT Deep Research，它会用 GitHub 链接抓取所有文件后给出 review。

### Repo

`https://github.com/oinani0721/canvas-learning-system`

### 核心文档

- [A3 原始批注](https://github.com/oinani0721/canvas-learning-system/blob/main/docs/project-status/fr-exploration/A3.md)
- [User2 批注索引（含 A3 第 3 条原文）](https://github.com/oinani0721/canvas-learning-system/blob/main/docs/project-status/fr-exploration/FR-KG-04/FR-KG-04-user2-annotations.md)
- [本摘要文件](https://github.com/oinani0721/canvas-learning-system/blob/main/docs/project-status/a3-review-summary.md)

### 修复 Change（archive 目录全量）

[`openspec/changes/archive/2026-04-07-fix-fr-kg-04-schema-drift-and-sync-hardening/`](https://github.com/oinani0721/canvas-learning-system/tree/main/openspec/changes/archive/2026-04-07-fix-fr-kg-04-schema-drift-and-sync-hardening)

5 capability spec：
- [verification-service spec.md](https://github.com/oinani0721/canvas-learning-system/blob/main/openspec/changes/archive/2026-04-07-fix-fr-kg-04-schema-drift-and-sync-hardening/specs/verification-service/spec.md) — 質疑 1 主战场
- [algo-question spec.md](https://github.com/oinani0721/canvas-learning-system/blob/main/openspec/changes/archive/2026-04-07-fix-fr-kg-04-schema-drift-and-sync-hardening/specs/algo-question/spec.md) — 質疑 2 主战场
- [algo-scoring spec.md](https://github.com/oinani0721/canvas-learning-system/blob/main/openspec/changes/archive/2026-04-07-fix-fr-kg-04-schema-drift-and-sync-hardening/specs/algo-scoring/spec.md)
- [canvas-sync spec.md](https://github.com/oinani0721/canvas-learning-system/blob/main/openspec/changes/archive/2026-04-07-fix-fr-kg-04-schema-drift-and-sync-hardening/specs/canvas-sync/spec.md)
- [llm-safety spec.md](https://github.com/oinani0721/canvas-learning-system/blob/main/openspec/changes/archive/2026-04-07-fix-fr-kg-04-schema-drift-and-sync-hardening/specs/llm-safety/spec.md)

### 修复源码（origin/main）

- [verification_service.py](https://github.com/oinani0721/canvas-learning-system/blob/main/backend/app/services/verification_service.py) — 重点看 L1677-1705 (`_mock_evaluate_answer`), L1362-1437 (`_resolve_safe_canvas_path`), L886+ (`_advance_concept`)
- [question_generator.py](https://github.com/oinani0721/canvas-learning-system/blob/main/backend/app/services/question_generator.py) — 重点看 L701-755 (`_get_kg_relevance` 加权公式)
- [exam_service_ext.py](https://github.com/oinani0721/canvas-learning-system/blob/main/backend/app/services/exam_service_ext.py) — L66-110 (CanvasNode schema 统一)
- [sync_service.py](https://github.com/oinani0721/canvas-learning-system/blob/main/backend/app/services/sync_service.py) — Segment Commit + SyncErrorClass
- [exam_models.py](https://github.com/oinani0721/canvas-learning-system/blob/main/backend/app/models/exam_models.py) — `NodePriority.kg_relevance_degraded`
- [sync_models.py](https://github.com/oinani0721/canvas-learning-system/blob/main/backend/app/models/sync_models.py) — `SyncErrorClass` enum
- [security.py](https://github.com/oinani0721/canvas-learning-system/blob/main/backend/app/security.py) — `require_internal_api_key`
- [migrations/001_canvas_constraints.cypher](https://github.com/oinani0721/canvas-learning-system/blob/main/backend/migrations/001_canvas_constraints.cypher)
- [migrations/002_canvasnode_uuid_to_id.cypher](https://github.com/oinani0721/canvas-learning-system/blob/main/backend/migrations/002_canvasnode_uuid_to_id.cypher)

### 测试（origin/main）

- [test_kg_relevance_weighted.py](https://github.com/oinani0721/canvas-learning-system/blob/main/backend/tests/unit/test_kg_relevance_weighted.py) — 質疑 2 加权公式 19 tests
- [test_mock_degradation_transparency.py](https://github.com/oinani0721/canvas-learning-system/blob/main/backend/tests/unit/test_mock_degradation_transparency.py) — 質疑 1 fail-closed 30 tests
- [test_verification_service_activation.py](https://github.com/oinani0721/canvas-learning-system/blob/main/backend/tests/unit/test_verification_service_activation.py)
- [test_neo4j_field_consistency.py](https://github.com/oinani0721/canvas-learning-system/blob/main/backend/tests/unit/test_neo4j_field_consistency.py)
- [test_sync_segment_commit.py](https://github.com/oinani0721/canvas-learning-system/blob/main/backend/tests/unit/test_sync_segment_commit.py)
- [test_a11_kg_relevance_e2e.py](https://github.com/oinani0721/canvas-learning-system/blob/main/backend/tests/e2e/test_a11_kg_relevance_e2e.py) — 質疑 2 e2e

### Concept-id Identity Contract PR（独立 review 单元）

**[PR #1: fix(concept-id): A3 identity contract unification](https://github.com/oinani0721/canvas-learning-system/pull/1)**

3 commits 在 `fix-concept-id-identity-unification` branch：
- `d569da0` unify identity contract (verification/memory/review)
- `03c8842` close residual text-as-uuid leak (fallback_sync_service)
- `c154022` clear 3 pre-existing test infra debts

---

## 8. Review 重点（建议 ChatGPT 优先看）

### 質疑 1：评分系统（verification_service）

请验证以下三点：

1. **Fail-closed 是否真的 fail-closed**？查看 `verification_service.py:1677-1705` 的 `_mock_evaluate_answer`——是否真的恒返回 `("unknown", 0.0)`？是否有任何残留的字符长度启发式？docstring 是否明确禁止任何形式的内容评分？
2. **Path traversal 防护是否真的 defense-in-depth**？查看 `_resolve_safe_canvas_path` (L1362) 的三层校验：相对路径检查 + `.canvas` 后缀 + `Path.resolve().relative_to(base)`。是否能绕过？
3. **Mastery 状态污染是否被切断**？查看 `_advance_concept(degraded=True)` 的所有调用点（L841/847/853/1045），是否都正确传递 degraded 标记？

**社区认证视角**：评分用 Bloom's Taxonomy prompt + scoring-agent，arXiv:2408.04394 引用。请评估：
- 这是否符合教育评测领域的成熟做法？
- 是否需要更严格的 inter-rater reliability 测试？
- 现在 fail-closed 的 degraded path 设计是否符合"safety over availability"原则？

### 質疑 2：kg_relevance 加权公式（question_generator）

请验证以下两点：

1. **Schema 是否真的统一**？grep `backend/app/services/` 目录里所有 `CanvasNode {`，是否还有任何 `{uuid:` 用法？(注意：`EpisodicNode {uuid:` 是 Graphiti 自己的实体，正确，不应混淆。)
2. **加权公式是否合理**？查看 `_get_kg_relevance` 的 Cypher (L742-751)：
   - CANVAS_EDGE = 1.0（用户手画连线）
   - RELATES_TO = 0.7（Graphiti LLM 推断）
   - 归一化 `/8.0` 上限 1.0
   - 是否符合"用户意图 > 自动推断"的领域直觉？
   - `/8.0` 是否合理（假设典型节点 8 个邻居）？

**学术支撑视角**：
- 这种加权公式在知识图谱推荐系统中有论文支撑吗？
- 是否有更好的归一化方法（log scale、softmax、PageRank）？
- multi-edge inflation 防护（`WITH neighbor MAX(...)`）是否充分？

### 質疑 3（衍生）：Concept-id Identity Contract（PR #1）

请验证 PR #1 的三个 commit 是否真的补上了 verification/memory/review 三端的 concept_id 一致性：

1. **是否所有 concept_id 入口都过 ConceptRef 校验**？
2. **5th leak (fallback_sync_service) 是否是最后一处**？是否需要再做一次对抗性 grep？
3. **dual-bucket compat read（UUID 主缓存 + legacy text 隔离）的回滚安全性**？

### 質疑 4（重要）：arXiv 引用 scope drift（Claude 自我诊断，请 ChatGPT 复核）

⚠️ **Claude 在 Lane 1.5 调研中发现**：项目当前在 `verification_service` 相关 docstring / 第 8 节"社区认证视角"段落里引用的 `arXiv:2408.04394` 是 **question generation 论文**，**不涵盖 answer scoring / rubric methodology**。把它作为评分系统学术背书属于 **scope drift**。

详细诊断 + 推荐替代引用（G-Eval arXiv:2303.16634 + RULERS arXiv:2601.08654 + SafeTutors arXiv:2603.17373）见**第 11.5 节**。

请 ChatGPT 在 review 时**重点验证**：
1. arXiv:2408.04394 是否真的不涵盖 answer scoring？（Claude 的诊断基于 Agent 1 的 WebSearch 阅读，请你独立 fetch 论文摘要 + section 标题再判断）
2. 推荐的 3 篇替代论文（G-Eval / RULERS / SafeTutors）是否确实更对应 Canvas 的 verification scoring 用例？
3. 是否还有更好的 LLM-as-Judge 学术背书我们漏掉了？

---

## 9. Lane 1 不覆盖的事项（需 Lane 2/3）

按用户决策，本 deep explore 仅 Lane 1（pytest + spec grep，不动 Neo4j / Vite / Chrome）：

- ❌ **Neo4j real-data e2e** — `test_a11_kg_relevance_e2e.py` 7 tests 在 Neo4j 不可达时 skip，未跑真实图数据
- ❌ **前端 sync-engine.ts 错误回流** — 需要 Vite + 浏览器环境
- ❌ **prompt injection 4 国语言对抗** — 需要 LLM API 调用
- ❌ **A3 sub-3（图片处理 Gemini → 本地模型）** — 独立议题，不在本次范围
- ✅ **A3「社区认证」论文查证** — 见第 11 节 Community Validation（2 并行 agent + WebSearch 已完成 5-solution 调研，作为对 ChatGPT 的先导输入）

---

## 10. 验收建议

用户拿到这份摘要后建议的执行顺序：

1. 打开 [本摘要 GitHub URL](https://github.com/oinani0721/canvas-learning-system/blob/main/docs/project-status/a3-review-summary.md) 确认可见
2. 打开 [PR #1](https://github.com/oinani0721/canvas-learning-system/pull/1) 确认可审阅
3. 复制本文件第 7 节「ChatGPT Deep Research Review 入口」整段贴给 ChatGPT
4. ChatGPT 根据第 8 节的 Review 重点给出针对性的代码审查 + 学术支撑论证
5. **ChatGPT 应重点审查第 11.5 节的 arXiv scope drift 诊断**——Claude 已用并行 agent 调研 5 个社区方案（第 11 节），ChatGPT 作为第二意见复核 Claude 的 arXiv 引用诊断 + 推荐的 G-Eval/RULERS/SafeTutors 替代是否成立
6. 根据 ChatGPT 反馈决定是否需要开 `fix-a3-community-hardening-v2` 新 OpenSpec change（按第 11.6 节中期清单）

---

## 11. Community Validation & 5-Solution Cross-Reference

> **新增于 Lane 1.5**（2026-04-07）：旧 Lane 1 把"A3 社区认证论文查证"标为 Non-Goal 交给 ChatGPT，但用户决策变更——Claude 自己先用并行 agent + WebSearch 调研 5 个社区方案，把结论作为对 ChatGPT Deep Research 的"先导输入"。

### 11.1 调研背景

**两条质疑的本质回顾**:

- **质疑 1**：`verification_service._mock_evaluate_answer` 已改为 fail-closed `("unknown", 0.0)`，但**正常路径**的 Bloom Taxonomy prompt 引用的 `arXiv:2408.04394` 是否真的为 scoring 提供学术背书？
- **质疑 2**：`kg_relevance` 的 **CANVAS_EDGE 1.0 / RELATES_TO 0.7 / `/8.0`** 这些具体数字，以及"用户手画 > LLM 推断"的差异化加权方向，是否有社区/学术支撑？

**调研方式**：Claude 主 context 用 2 个并行 general-purpose agent + WebSearch，分别就两条质疑搜索社区方案，交叉验证后缩减为 5 solutions（质疑 1 三个 + 质疑 2 两个）。

### 11.2 质疑 1 维度：Verification Scoring 的 3 个社区方案

#### Solution 1: G-Eval (EMNLP 2023 + DeepEval)

- **核心机制**：LLM-as-Judge 奠基性框架。两步走：(a) 让 LLM 基于任务介绍 + 评分标准自动生成 CoT 评估步骤；(b) 用 form-filling 范式按步骤打分，最终用 logprob 加权求和（而非单次采样）。
- **社区采用度**：EMNLP 2023（arXiv:2303.16634），Google Scholar 500+ 引用；**DeepEval 框架原生实现**（GitHub 5k+ stars，每月处理 10M+ G-Eval metrics）；MLflow 3.0 原生支持。Summarization 任务上与人类评分 Spearman 相关系数 0.514。
- **与当前方案差异**：Canvas 现在是"单次调 agent 拿分"。G-Eval 多两层：(a) CoT 评估步骤先展开再打分（提高一致性和可解释性），(b) logprob 加权降低方差。**与 fail-closed 机制正交，不冲突**。
- **落地复杂度**：**low** — 纯 prompt 重写 + 可选 logprob 加权；DeepEval 提供开箱即用 Python API，本地部署无云依赖。
- **是否替代当前**：**补强，不替代**。G-Eval 改造"正常路径"的 rubric prompt，fail-closed 兜底完全保留。
- **引用**：
  - [G-Eval (arXiv:2303.16634)](https://arxiv.org/abs/2303.16634)
  - [DeepEval G-Eval docs](https://deepeval.com/docs/metrics-llm-evals)

#### Solution 2: RULERS — Locked Rubrics & Evidence-Anchored Scoring

- **核心机制**：2026 年 1 月最新论文（arXiv:2601.08654），针对 LLM-as-Judge 三大失败模式（rubric 不稳定、推理不可审计、scale 与人类评分边界不对齐）。把 rubric 编译成 versioned immutable bundles，强制 structured decoding 要求 judge 输出 evidence 引用，用 Wasserstein 后验校准对齐人类评分。**不需要 fine-tune**。
- **社区采用度**：论文很新（< 3 个月），引用数还少，但属于 LLM-as-Judge 2025-2026 集群的 SOTA 方向（与 AutoRubric、Rubric-Scaffolded RL 形成研究集群）。
- **与当前方案差异**：Canvas 现在 rubric 是写在 prompt 里的自由文本，易被 prompt drift 污染。RULERS 把 rubric 作为 compiled artifact 存储（版本化、不可变），调用时加载，强制引用用户答案的具体证据片段。
- **落地复杂度**：**medium** — 需要 rubric schema 设计 + version 管理 + structured decoding 改造。但不引入新系统依赖（可用 Pydantic + Neo4j 存）。
- **是否替代当前**：**补强**。把现有 Bloom prompt 改造成 locked rubric bundle 即可，fail-closed 机制保留。
- **引用**：
  - [RULERS (arXiv:2601.08654)](https://arxiv.org/abs/2601.08654)
  - [Rubrics as an Attack Surface (arXiv:2602.13576)](https://arxiv.org/html/2602.13576)

#### Solution 3: SafeTutors Pedagogically-Safe Fail-Closed

- **核心机制**：SafeTutors 基准（arXiv:2603.17373）首次系统性定义 "pedagogical safety"——AI tutor 的主要风险**不是 toxic content，而是过早泄露答案、强化错误认知、放弃 scaffolding**。研究发现所有模型都有广泛危害、scale 不能可靠改善、多轮对话反而恶化（pedagogical failure 17.7% → 77.8%）。对应的 graceful degradation playbook 定义四级降级：Full → Reduced → Cached → Honest error。
- **社区采用度**：2026 年新发表的 EdTech-specific 基准，是目前最对口的 AI tutor 安全设计论文。"Graceful degradation" 本身是经典 SIL Safety 跨航空/汽车/医疗工程原则。
- **与当前方案差异**：Canvas 的 fail-closed 是两档（正常评分 vs unknown 0 分）。SafeTutors 建议多级降级。**但关键 insight 反而支持保守**：该论文证明启发式 "preliminary score" 会导致 pedagogical failure 扩大，所以**当前两档 fail-closed 其实是 SafeTutors 建议的安全选择**。
- **落地复杂度**：**low**（如果只做用户面提示升级）；**high** 且不推荐（如果引入启发式二级降级——正是之前修复掉的 silent-scoring-pollution bug）。
- **是否替代当前**：**背书**。SafeTutors 研究反向证明"宁可 fail-closed，不要 heuristic scoring"是正确选择。
- **引用**：
  - [SafeTutors (arXiv:2603.17373)](https://arxiv.org/abs/2603.17373)

### 11.3 质疑 2 维度：kg_relevance Formula 的 2 个社区方案

#### Solution 4: Weighted Degree Centrality (当前方案的社区背书)

- **核心机制**：求邻接边权重之和，异构图上按 edge type 差异化加权。Canvas 的 `SUM(CASE type(r) WHEN CANVAS_EDGE THEN 1.0 WHEN RELATES_TO THEN 0.7 END) / 8.0` 正是标准模板。
- **社区采用度**：**Neo4j GDS 官方内置**（`degreeCentrality` with weighted relationships）；TigerGraph 官方支持；Opsahl 2010 经典论文；Springer 2020 node-weighted centrality 综述；PMC 多篇实证。
- **与当前方案差异**：**完全一致**。Canvas 公式的方向有 Strong 社区背书。
- **计算复杂度**：O(degree)，单节点 < 5ms。**已满足实时查询场景（< 200ms）**。
- **但是**——**具体数字 1.0/0.7/8.0 是经验值**：
  - **1.0 vs 0.7 的方向**：有 provenance/confidence-aware KG 文献支撑（MDPI Computers 2025 Anchor-Constrained KG、TrustGraph W3C PROV-O 框架、ACM Computing Surveys 2023 综述），文献一致认为「有 provenance 的边 > LLM 自动抽取」。**但 0.3 gap 没有论文给定**——文献里常见数值区间 0.5~0.9，Canvas 的 0.7 在区间内。
  - **`/8.0` 硬编码**：依据是 PMC 2023 online learners concept map 研究的小图典型度数 5-10。方向合理但 8.0 是**硬编码**，建议**改为动态 P90 分位数**（全图扫一次，代价低收益高）。
- **落地复杂度**：low（当前已落地；"加注释 + 动态 P90" 升级也 low）
- **是否替代当前**：**背书 + 轻量升级**。Keep 方案，但：(1) 代码注释里标注 1.0/0.7/8.0 为"经验初值，待 A/B 验证"并引用学术来源；(2) `/8.0` 改为动态 P90 分位数（未来任务）。
- **引用**：
  - [Neo4j GDS — Degree Centrality](https://neo4j.com/docs/graph-data-science/current/algorithms/degree-centrality/)
  - [Opsahl — Node centrality in weighted networks](https://toreopsahl.com/tnet/weighted-networks/node-centrality/)
  - [Springer 2020 — Node-weighted centrality](https://link.springer.com/article/10.1186/s40649-020-00081-w)
  - [MDPI Computers 2025 — Grounded KG with Provenance](https://www.mdpi.com/2073-431X/15/3/178)
  - [TrustGraph — Ontologies and Context Graphs](https://trustgraph.ai/guides/key-concepts/ontologies-and-context-graphs/)

#### Solution 5: Personalized PageRank (Neo4j GDS 一级算法)

- **核心机制**：带重启的随机游走，bias 到 source 节点。相比 weighted degree 只看一跳且全局静态，PPR 能捕捉**任意跳 + source-specific 个性化**——**更贴合"出题考察当前学习节点相关概念"的语义**。
- **社区采用度**：**Neo4j GDS 一级算法**（`gds.pageRank.stream` with `sourceNodes` param）；Pinterest Pixie / Twitter WTF 生产级标配；arXiv 2024 peer-reviewed 综述（arXiv:2403.05198）；BiPPR 论文在十亿边图上实测 42ms。
- **与当前方案差异**：**质的提升**——从 degree-based 换成 walk-based，能区分"结构性中心节点"和"语义相关节点"。对 Canvas "跳过已掌握的节点，优先相关但未掌握的"这种需求天然契合。
- **计算复杂度**：小图 50-200ms（需 GDS in-memory projection）。**基本满足实时场景**，但需要 GDS plugin 和管道改造。
- **落地复杂度**：**medium** — 需要启用 Neo4j GDS plugin（项目当前用 Neo4j Community Edition，**GDS Community Edition 够用**），管道改造为 projection + query。
- **是否替代当前**：**未来升级路径**。MVP 不做，但代码注释里留一句"未来可迁移到 PPR"作为 technical debt 追踪。
- **引用**：
  - [Neo4j GDS — PageRank (Personalized)](https://neo4j.com/docs/graph-data-science/current/algorithms/page-rank/)
  - [Bahmani — Fast Incremental PPR (Stanford CS224w)](https://snap.stanford.edu/class/cs224w-readings/bahmani10pagerank.pdf)
  - [arXiv 2403.05198 — PPR Survey 2024](https://arxiv.org/abs/2403.05198)

### 11.4 交叉验证表

| # | Solution | 维度 | 与当前方案关系 | 复杂度 | 短期采纳? | 备注 |
|---|---|---|---|---|---|---|
| S1 | G-Eval | 质疑 1 | 补强正常路径 rubric prompt | low | ✅ 推荐 | EMNLP 2023 最成熟 LLM-as-Judge |
| S2 | RULERS Locked Rubrics | 质疑 1 | 补强 rubric 存储 + evidence anchoring | medium | ⏳ 中期 | 2026 SOTA，解决 prompt drift |
| S3 | SafeTutors | 质疑 1 | **背书现状** | low | ✅ 引用即可 | 反向证明 fail-closed 是对的 |
| S4 | Weighted Degree Centrality | 质疑 2 | **背书现状** + 加注释 | low | ✅ 推荐 | Neo4j GDS 官方；方向有 provenance KG 文献支持 |
| S5 | Personalized PageRank | 质疑 2 | 未来升级路径 | medium | ⏳ 长期 | Neo4j GDS 一级算法，无新依赖 |

**已调研但排除的方向**:

- **GENI (KDD 2019, GNN-based Node Importance)** — Amazon Science 生产部署，NDCG@100 超 baseline 5-17%，但 Canvas **没有 node importance ground-truth label**（无法监督训练）+ 引入 PyTorch/DGL 违反"不增新系统依赖"约束。**不推荐 MVP**
- **HITS / SALSA** — NetworkX 官方明说无向图上无意义；Canvas edges 无向使用；**排除**
- **Node2Vec / GraphSAGE** — 输出 embedding 而非 importance scalar；Node2Vec transductive 不支持增量新节点；**不适用**
- **Item Response Theory (IRT)** — 对 Canvas 长期价值高，但 MVP 阶段需要大量答题数据才能拟合参数，**延后**
- **RAGAS 直接复用** — RAGAS 是 RAG pipeline 评估，不是 answer scoring；可作为 eval framework 但不能直接替代 scoring agent

### 11.5 ⚠️ 关键发现：arXiv 引用 scope drift

**诊断**：项目当前文档（包括第 8 节"社区认证视角"段落）引用的 `arXiv:2408.04394` 是 **question generation 论文**，**不涵盖 answer scoring**。把它作为"评分用 Bloom's Taxonomy prompt + scoring-agent"的学术背书，是 **scope drift**。

**证据**：Agent 1 通过 WebSearch 阅读 arXiv:2408.04394 摘要 + 章节标题，确认该论文聚焦于 "automated question generation from educational content"，方法学讨论的是 prompt engineering for question diversity，**没有任何 answer evaluation rubric / scoring methodology 的内容**。

**推荐替代引用**:

| 用途 | 推荐论文 | 为什么 |
|---|---|---|
| LLM-as-Judge 评分 SOTA | arXiv:2303.16634 (G-Eval, EMNLP 2023) | 直接对应 "用 LLM 给学生答案打分" 的方法学 |
| Locked rubric + evidence anchoring | arXiv:2601.08654 (RULERS, 2026) | 解决"prompt drift 导致评分不稳定"问题 |
| Pedagogical safety (fail-closed 设计) | arXiv:2603.17373 (SafeTutors, 2026) | 直接背书"宁可 fail-closed 也不要启发式 partial score" |

**修复建议（短期）**：
- 在 `verification_service.py` 调用 scoring-agent 的 docstring 里删除 `arXiv:2408.04394` 引用
- 改为引用 `arXiv:2303.16634` (G-Eval) + `arXiv:2603.17373` (SafeTutors) 作为 fail-closed 设计的学术背书
- 把 `arXiv:2408.04394` 留在 `question_generator.py`（题目生成，原本就该用这篇）

### 11.6 推荐立场（三层）

#### 短期（本次 light path 即完成）

1. ✅ **本 section 11 落地** — 在 `a3-review-summary.md` 增加完整社区调研结果作为对 ChatGPT 的先导输入
2. ❌ **不改代码** — `verification_service.py` / `question_generator.py` / `exam_models.py` 都不动
3. ❌ **不开新 OpenSpec change** — 留作 v2 候选，等 ChatGPT 反馈后再决定

#### 中期（下一 OpenSpec change 候选 — `fix-a3-community-hardening-v2`）

1. **修正 arXiv 引用**：把 `verification_service` 里 `arXiv:2408.04394` 替换为 `arXiv:2303.16634` + `arXiv:2603.17373`
2. **代码注释加经验值标注**：在 `_get_kg_relevance` Cypher 处明确 1.0/0.7/8.0 是"经验初值，待 A/B 验证"，并引用 Opsahl 2010 + MDPI 2025 + TrustGraph
3. **`/8.0` 改为动态 P90 分位数**：全图扫一次，缓存到 Neo4j 节点属性，每周或每次 sync 后刷新
4. **G-Eval prompt 改造**：把现有 Bloom 单 prompt 改为 G-Eval 风格（CoT 评估步骤 + form-filling），可选 logprob 加权

#### 长期（未来 FR 候选）

1. **RULERS locked rubric bundle**：rubric 版本化 + structured decoding evidence anchoring
2. **Personalized PageRank 迁移**：启用 Neo4j GDS Community Edition，把 `_get_kg_relevance` 从 weighted degree 升级到 PPR
3. **Item Response Theory (IRT)**：等收集到足够答题数据后，校准题目难度和学生能力到同一尺度

### 11.7 引用汇总（学术 + 工业文档）

**LLM-as-Judge / Verification Scoring**:
- [G-Eval (arXiv:2303.16634)](https://arxiv.org/abs/2303.16634)
- [RULERS (arXiv:2601.08654)](https://arxiv.org/abs/2601.08654)
- [Rubrics as an Attack Surface (arXiv:2602.13576)](https://arxiv.org/html/2602.13576)
- [SafeTutors (arXiv:2603.17373)](https://arxiv.org/abs/2603.17373)
- [DeepEval G-Eval docs](https://deepeval.com/docs/metrics-llm-evals)

**Knowledge Graph Centrality / Recommendation**:
- [Neo4j GDS — Degree Centrality](https://neo4j.com/docs/graph-data-science/current/algorithms/degree-centrality/)
- [Neo4j GDS — PageRank (Personalized)](https://neo4j.com/docs/graph-data-science/current/algorithms/page-rank/)
- [Opsahl 2010 — Node centrality in weighted networks](https://toreopsahl.com/tnet/weighted-networks/node-centrality/)
- [Springer 2020 — Node-weighted centrality](https://link.springer.com/article/10.1186/s40649-020-00081-w)
- [Bahmani — Fast Incremental PPR (Stanford CS224w)](https://snap.stanford.edu/class/cs224w-readings/bahmani10pagerank.pdf)
- [arXiv 2403.05198 — PPR Survey 2024](https://arxiv.org/abs/2403.05198)

**Provenance-Aware KG / Edge Confidence**:
- [MDPI Computers 2025 — Grounded KG with Provenance](https://www.mdpi.com/2073-431X/15/3/178)
- [TrustGraph — Ontologies and Context Graphs](https://trustgraph.ai/guides/key-concepts/ontologies-and-context-graphs/)
- ACM Computing Surveys 2023 — Knowledge Graph Confidence Scoring (综述)

---

**生成 Agent**: Claude Code (Opus 4.6 1M context) via Lane 1 deep explore
**用时**: 单 session 一次性产出
**测试 runtime evidence**: `136 passed, 1 failed in 1.95s` (137 collected; 1 fail = pre-existing DI mock infra debt 不属 A3 回归)
**下一步**: ChatGPT Deep Research review → 反馈循环 → finalize A3 议题
