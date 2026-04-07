## Why

FR-KG-04 经过 **4 轮对抗性核实**（含 3 份独立深度研究报告 + 本地 Explore Agent × 3 的代码级核验），共发现 P0/P1 级真实 bug 10+ 项。本次变更是这些发现的**统一归集**，取代早期的 `fr-kg-04-sync-pipeline-fix` change（已标记 SUPERSEDED，Wave 2 的先进设计已被本 change 吸收）。

### 2026-04-07 架构重组说明

本 change **吸收了** `fr-kg-04-sync-pipeline-fix` 的核心设计贡献：

| 来自 sync-pipeline-fix 的贡献 | 本 change 吸收位置 |
|---|---|
| Dependency-Aware Segment Commit (D6) | `design.md` D7 + `specs/canvas-sync` 新 requirement |
| SyncErrorClass per-op 错误分类 (D7) | `design.md` D8 + `specs/canvas-sync` |
| 前端 sync-engine.ts 错误回流 | `design.md` D9 + `tasks.md` Phase 12 |
| Outbox schema 扩展（permanentlyFailed 等） | `specs/canvas-sync` |
| Operation ID dedup 幂等 | `specs/canvas-sync` |
| Sync Payload Pydantic 校验 | `specs/canvas-sync` |
| Learning relationship 字段一致性 (`r.score` alias) | `specs/algo-scoring`（新增 capability）|
| 前端 outbox canvasId default fallback 删除（Patch-4）| `specs/canvas-sync` 新 requirement + `tasks.md` Phase 14 |

覆盖规则：本 change 原有的 "Topological Ordering (D4)" 和 "Per-Operation Failure Isolation" 被 sync-pipeline-fix 的 Segment Commit 架构**替代**——因为 3 段式事务在依赖失败场景下更准确（Segment 1/2 原子，Segment 3 容忍部分失败），解决了原 D4 单事务下的"孤边"问题。

### Wave 1 已完成（2026-04-06 前置 commit，不在本 change 范围）

以下修复在 `fr-kg-04-sync-pipeline-fix` 期间已经 ship 到 main 分支，本 change 不重复处理：

- `1ea43b2`: canvas-store.ts 为 update/delete 操作补全 canvasId/source/target 字段（前端写入端）
- `c7215ca`: QuestionGenerator KG 查询 schema 对齐（本 change Phase 1 的局部先手）
- `27bbd73`: MemoryService group_id 在内存 fallback 路径的过滤修复

本 change 的 Phase 1 会完成剩余未覆盖的 schema drift 修复（`exam_service_ext.py`, `question_generator.py` 的其余查询点）。

### 核心问题（本 change 完整范围）

FR-KG-04 在 Gap Analysis 中标记为 ✅ Complete，但用户前端测试时标记为 NOT_VISIBLE。经过深度探索与 Deep Research 对抗性审查，发现的 P0/P1 问题包括：

**Schema drift civil war（所有早期报告都漏掉的真正 P0）**：
- `question_generator._get_kg_relevance` 查询 `CanvasNode {uuid}` + `neighbor.canvas_id`，但 `SyncService` 实际写入的是 `{id}` + `canvasId`（camelCase）——字段命名完全不匹配，导致 `kg_relevance` 在生产中**永远返回默认值 0.5**，考试优先级公式中 30% 权重完全失效，而且不抛异常、无日志告警，是典型的 silent degradation
- `exam_service_ext.py:67` 写入 `{uuid: $node_id}` 形成第三套幽灵 schema

**Sync 管道正确性（P0）**：
- `/api/v1/sync/batch` 完全无鉴权，任何本机进程都可污染图谱
- `_upsert_edge` 使用 `MATCH-MATCH-MERGE` 模式在节点缺失时静默 no-op（产生孤边或丢数据）
- 批次 ops 未按依赖顺序执行，前端 Outbox 乱序可导致 edge 先于 node
- 单事务"部分提交"语义在依赖失败时产生孤边（Story 1.5 AC-7 的设计边界外 bug）
- 异常分类错误地全部归为 503，逻辑 bug 被伪装成"Neo4j 不可用"
- 错误详情泄露给客户端（`str(e)[:200]`）
- Per-operation 失败原因缺乏结构化分类，前端无法据此决定重试策略
- 前端 `sync-engine.ts` 在缺失 canvasId 时静默降级为 `'default'`，导致跨画布污染

**数据字段一致性（P1）**：
- `get_review_suggestions()` 读取 `r.last_score`，但 `create_learning_relationship` 写入 `r.score`，复习建议永远读到 null
- `review_count` 未在 Cypher 中递增

**Prompt injection 盲区（P1）**：
- `PromptTemplate` 完全不扫描检索 context，存在间接提示注入风险
- Claude/Gemini client 拼接 RAG 结果到 system prompt 时无防护

**Neo4j 约束缺失（P1）**：
- 无 `(canvas_id, node_id)` 唯一约束，无 `canvasId` 索引
- `(subjectId, name)` 联合唯一约束缺失，允许同学科重名白板

这些问题构成了"功能看似在跑但实际关键信号被吞掉"的复合风险，必须在 MVP 真实数据测试前统一修复。

### 发现来源

- FR-KG-04 Deep Explore（2026-04-04，原版）
- Gemini Deep Research 对抗性审查报告（`/Users/Heishing/Downloads/deep-research-report.md`）
- ChatGPT Deep Research 二次核验（`/Users/Heishing/Downloads/deep-research-report-10.md`，2026-04-06）
- ChatGPT Deep Research 三次核验（2026-04-07，8 个 Patch 提案）
- 本地 Explore Agent × 3 + 代码级直接验证（2026-04-06/07）
- 四轮交叉验证修正了多项误判（详见 `/Users/Heishing/.claude/plans/snuggly-swimming-marble.md` 和 `misty-hatching-rabin.md`）

## What Changes

### 目标
1. 统一 `CanvasNode` 节点的 Neo4j schema 到 `{id}` + `canvasId`（SyncService 是 source of truth）
2. 让 `kg_relevance` 在生产中返回实际计算值而非恒定 0.5
3. 升级 `kg_relevance` 公式到 `CANVAS_EDGE + RELATES_TO` 加权融合
4. 为 `/sync/batch` 添加设备级 API Key 鉴权
5. 消除 `_upsert_edge` 的静默 no-op（OPTIONAL MATCH + status 返回）
6. 引入 Dependency-Aware Segment Commit 架构（Board → Node → Edge 三段原子事务）
7. 引入 SyncErrorClass per-op 错误分类 + 前端 sync-engine.ts 错误回流重试策略
8. Sync payload Pydantic 校验 + operation_id 批次内去重
9. 修复异常分类错误，停止将逻辑 bug 伪装成 "Neo4j unreachable"
10. 修复 `get_review_suggestions` 的 `r.last_score` 字段名错位 + review_count 递增
11. 扩展 prompt injection 防护到检索上下文
12. 建立 Neo4j 约束与索引迁移
13. 删除 `CONNECTS_TO` 写入死代码
14. 删除前端 `sync-engine.ts` 的 canvasId `'default'` fallback（Patch-4）
15. 建立 RAGAS 离线回归评估集

### 范围

**做**：
- **Phase 1**: `CanvasNode` schema 统一 + `kg_relevance` Cypher 修复 + 加权公式 + degraded_reason 返回
- **Phase 2**: `/sync/batch` API Key 鉴权（`X-CLS-Internal-Key` header + fail-closed）
- **Phase 3**: `_upsert_edge` fail fast + OPTIONAL MATCH + status 返回
- **Phase 4**: HTTP 异常分类拆分 + Neo4j 约束/索引迁移
- **Phase 5**: `kg_relevance` 加权公式实装（Cypher `SUM(CASE type(r) ...)`）
- **Phase 6**: CONNECTS_TO 死代码弃用
- **Phase 7**: Canvas 主键联合唯一约束
- **Phase 8**: PromptTemplate 检索上下文扫描（Claude/Gemini/context_enrichment 三点）
- **Phase 9**: RAGAS 离线评估 CI gate
- **Phase 10**: 验证与归档
- **Phase 11 (新)**: Dependency-Aware Segment Commit 架构升级（取代原 Phase 3 的部分内容）
- **Phase 12 (新)**: SyncErrorClass 枚举 + 前端 sync-engine.ts 错误回流 + Dexie schema 升级
- **Phase 13 (新)**: Sync Payload Pydantic 校验（`SyncOperation` / `SyncBatchRequest` model_validator）
- **Phase 14 (新)**: 前端 sync-engine.ts 删除 canvasId `'default'` fallback
- **Phase 15 (新)**: Learning relationship 字段一致性（`r.score AS last_score` alias + review_count 递增）
- **Phase 17 (2026-04-07 新增)**: Verification Service Security Hardening —
  - P1-4: `_mock_evaluate_answer` fail-closed 改造（不再按答案长度判分，degraded 时返回 `("unknown", 0.0)` 且跳过掌握度更新）
  - P0-3: `_do_extract_concepts` 路径穿越防护（CanvasService 优先 + `_resolve_safe_canvas_path` 严格 base 校验 + 删除不安全 fallback open()）

**不做（延后）**：
- `kg_relevance` 时间衰减（依赖 FSRS `last_review` 数据成熟度）
- JWT/OAuth2 鉴权升级（Tauri 本机部署，API Key 足够）
- Canvas 主键统一为单键（保留 `canvas_id` UUID + `canvas_name` 双键）
- Graphiti `RELATES_TO` 的数据质量评估（依赖 RAGAS 管线完成）
- 前端 Outbox 的 operation_id 持久化跨批次去重（MERGE 数据级幂等已足够）
- 修改 `verification_service.py:1832-1947`（`# FR-KG-04 fix:` 已处理 A10/A2/A5）
- **sidecar 权限闭环 / extract-conversation 鉴权 / MCP token / dead-letter 脱敏 / API key opt-in**（这 5 项由独立的 `fr-kg-04-security-hardening` change 处理，下一轮 session 创建）

## Capabilities

### New Capabilities

- `canvas-sync`: Frontend→backend sync batch 管道的完整契约，含鉴权、Segment Commit 架构、SyncErrorClass 分类、edge 一致性保证、payload 校验、operation_id 去重、前端错误回流重试策略、outbox schema 扩展、CanvasId 强制校验
- `llm-safety`: LLM 客户端的输入/输出/检索上下文三层注入防护，含间接提示注入检测、context 扫描、日志脱敏
- `algo-scoring`: Learning relationship 的字段一致性契约（`r.score` 单一真源 + `r.review_count` 递增语义）

### Modified Capabilities

- `algo-question`: 修复 `_get_kg_relevance` Cypher schema 分裂导致的永远返回 0.5 bug；升级为加权 CANVAS_EDGE+RELATES_TO 公式；明确空图退化策略（`degraded_reason` 标记，禁止静默用默认值）

## Impact

### Affected Code

**Backend services**:
- `backend/app/services/sync_service.py` — Segment Commit 改造、`_upsert_edge` fail fast、`_deduplicate_by_operation_id`、`_partition_by_entity_type`、异常捕获范围扩展
- `backend/app/services/question_generator.py:673,751` — Cypher schema 修正 + kg_relevance 加权公式
- `backend/app/services/exam_service_ext.py:67,100-101` — `{uuid}`→`{id}` 统一 schema
- `backend/app/services/canvas_service.py` — 删除 `_sync_edge_to_neo4j` 中的 `CONNECTS_TO` 写入死代码
- `backend/app/services/context_enrichment_service.py` — `_format_learning_context` 扫描每条检索 chunk

**Backend API & models**:
- `backend/app/api/v1/endpoints/sync.py:37,57-66` — 鉴权依赖 + HTTP 异常分类拆分
- `backend/app/models/sync_models.py` — `SyncErrorClass` 枚举、`SyncOperationResult.error_class`、`SyncDependencyError`、Pydantic payload 校验、批次上限
- `backend/app/clients/claude_client.py:247` — context 拼接前 `check_input`
- `backend/app/clients/gemini_client.py:441` — context 拼接前 `check_input`
- `backend/app/clients/neo4j_client.py` — `get_review_suggestions` 的 `r.score AS last_score` alias + `create_learning_relationship` 的 `review_count` 递增

**Backend infrastructure (new files)**:
- `backend/app/security.py` — `APIKeyHeader` + `require_internal_api_key` 依赖
- `backend/app/config.py` — 新增 `INTERNAL_API_KEY` Settings 字段
- `backend/migrations/001_canvas_constraints.cypher` — Neo4j 约束与索引迁移
- `backend/migrations/002_canvasnode_uuid_to_id.cypher` — 历史 `{uuid}` 节点迁移

**Frontend**:
- `frontend/src/services/api-client.ts` — `syncBatch` 调用附加 `X-CLS-Internal-Key` header
- `frontend/src/services/sync-engine.ts` — 错误回流重试策略（按 error_class 分支）+ 删除 canvasId `'default'` fallback
- `frontend/src/services/dexie-db.ts` — `sync_outbox` 新增 `permanentlyFailed` / `failureClass` / `retryPriority` / `nextRetryAt` / `lastError` 字段 + version bump upgrade 回调
- `frontend/src/config.ts`（或 `.env`）— `VITE_INTERNAL_API_KEY` 环境变量接入

**Tests**:
- `backend/tests/conftest.py` — `INTERNAL_API_KEY="test-internal-key"` 测试配置
- `backend/tests/unit/test_sync_batch_auth.py`（新） — 鉴权 403/200 回归
- `backend/tests/unit/test_sync_segment_commit.py`（新） — Segment Commit 三段原子规则
- `backend/tests/unit/test_sync_error_class.py`（新） — SyncErrorClass 序列化
- `backend/tests/unit/test_sync_payload_validation.py`（新） — Pydantic 校验
- `backend/tests/unit/test_sync_service_edge_noop.py`（新） — edge fail fast
- `backend/tests/unit/test_kg_relevance_schema.py`（新） — kg_relevance 实际数据路径
- `backend/tests/unit/test_kg_relevance_weighted.py`（新） — 加权公式场景覆盖
- `backend/tests/unit/test_neo4j_field_consistency.py`（新） — r.score alias + review_count
- `backend/tests/unit/test_prompt_injection_context.py`（新） — 检索 context 扫描
- `frontend/src/services/__tests__/sync-engine-error-class.test.ts`（新） — error_class 分支处理
- `frontend/src/services/__tests__/sync-engine-canvasid-enforcement.test.ts`（新） — 缺失 canvasId 时跳过不降级
- `backend/tests/regression/ragas_eval/`（新） — RAGAS 离线集

### Affected APIs

- `POST /api/v1/sync/batch` — **BREAKING**: 需要 `X-CLS-Internal-Key` header（除非 `DEBUG=True` 且未配置 key）
- `POST /api/v1/sync/batch` — **BREAKING**: response 新增 `error_class` 字段（Optional，旧客户端降级兼容）

### Affected Dependencies

- 新增 `ragas` Python 依赖（仅 CI/dev 用）

### Systems

- **Neo4j schema**: 所有新写入的 `CanvasNode` 统一用 `id` 主键；历史 `{uuid}` 节点需数据迁移脚本合并
- **Tauri 前端**: 需要环境变量注入 API key；开发模式可省略
- **IndexedDB (Dexie)**: 用户首次启动新版本会触发 sync_outbox 表的 version upgrade

### Not Changing (严禁修改)

- `verification_service.py:1832-1947` — `# FR-KG-04 fix:` 已处理 A10/A2/A5，避免双重转换
- `rag_service.py` 的返回结构契约 — `reranked_results` 是正确契约
- `recommendation_service.py` — schema 与 SyncService 一致，正常工作
- Wave 1 已 ship 的 3 个 commit（`1ea43b2`, `c7215ca`, `27bbd73`）— 本 change 不重复处理

### Rollback

- **schema 修复**：提供反向迁移脚本 `MATCH (n:CanvasNode) WHERE n.uuid IS NOT NULL SET n.id = n.uuid REMOVE n.uuid`
- **鉴权**：前端启动时检查配置，未注入时提示；可通过 `INTERNAL_API_KEY=""` + `DEBUG=True` 临时放行
- **Segment Commit**：若引入问题，可回退 `process_sync_batch` 到原单事务实现，保留 Segment 入口但每段共享事务
- **前端错误回流**：`error_class` 是 Optional 字段，前后端独立 revert 不造成崩溃
- **edge no-op 修复**：回归测试覆盖正常路径；若批量修复导致历史成功变失败，可加 feature flag `STRICT_EDGE_VALIDATION`
- **CONNECTS_TO 弃用窗口**：保留代码 1 个 minor 版本；完全删除前仓库 grep 证明无读写路径
- **Dexie schema 升级**：version bump 有 upgrade 回调兜底；如需回退需手动 downgrade 数据库

### Risk

- **Segment Commit 改变事务边界**：原"一个 batch 一个事务"变成"一个 batch 三个事务"，需验证 Neo4j driver 层不会引入意外行为（会话锁、连接池压力）
- **前后端版本不对齐**：若后端先发布（返回 error_class）而前端未升级，sync-engine.ts 会忽略新字段，降级为原行为（不会崩溃，但新重试策略不生效）
- **Dexie schema 版本升级**：新增字段需要 Dexie version bump，用户首次启动会触发 upgrade migration
- **payload 校验的字段名**：Wave 1 已确认前端 SyncEngine 发送的是 camelCase（`sourceNodeId`）
- **operation_id 去重范围**：仅在单批次内，跨批次去重需要后端持久化（本 change 不做）

## 探索记录

详细探索过程和发现见：
- `docs/project-status/fr-exploration/FR-KG-04.md`（含用户批注）
- Gemini 报告：`/Users/Heishing/Downloads/deep-research-report.md`
- ChatGPT 报告：`/Users/Heishing/Downloads/deep-research-report-4.md`

### 探索中发现的其他问题（不在本 change 范围内，供后续参考）

- **fr-kg-04-security-hardening** (下一 change): sidecar canUseTool fail-closed + permission_request 闭环、extract-conversation 内部 token + group_id 强制、MCP server token middleware、episode dead-letter 脱敏、API key `dangerous-direct-browser-access` opt-in 降级
- **fr-kg-05**: 推荐 UI 断裂管道（G-PIPE）
- **A11 考察规划**: 图谱感知出题策略（Wave 3）
- **三层图谱合并议题**: 需要独立设计讨论
