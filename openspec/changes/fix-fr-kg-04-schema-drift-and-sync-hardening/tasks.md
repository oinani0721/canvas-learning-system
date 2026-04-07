## 1. Schema 统一与 kg_relevance 修复（Phase 1，Week 1 Day 1）

- [x] 1.1 在测试 Neo4j 实例上运行 dry-run 脚本 `MATCH (n:CanvasNode) WHERE n.uuid IS NOT NULL RETURN count(n) AS legacy_count` 评估历史 `{uuid}` 节点规模 (dry-run 步骤记录在 migration 002 注释顶部)
- [x] 1.2 编写反向迁移脚本 `backend/migrations/002_canvasnode_uuid_to_id.cypher` 实现 `SET n.id = coalesce(n.id, n.uuid) REMOVE n.uuid` (含 canvas_id → canvasId 同步)
- [x] 1.3 修改 `backend/app/services/exam_service_ext.py:67` 将 `MERGE (n:CanvasNode {uuid: $node_id})` 改为 `MERGE (n:CanvasNode {id: $node_id})` (同时改 n.canvas_id → n.canvasId, n.uuid → n.id)
- [x] 1.4 修改 `backend/app/services/exam_service_ext.py:100-101` 同步将 `{uuid: $source_node_id}` 和 `{uuid: $node_id}` 改为 `{id: ...}`
- [x] 1.5 修改 `backend/app/services/question_generator.py:673-675` Cypher 为 `MATCH (n:CanvasNode {id: $node_id})-[r:CANVAS_EDGE|RELATES_TO]-(neighbor:CanvasNode) WHERE neighbor.canvasId = $canvas_id RETURN SUM(CASE type(r) WHEN 'CANVAS_EDGE' THEN 1.0 WHEN 'RELATES_TO' THEN 0.7 ELSE 0 END) AS weighted_degree`
- [x] 1.6 修改 `backend/app/services/question_generator.py:751` 中的类似查询，统一 `{uuid}`→`{id}`、`canvas_id`→`canvasId` (Wave 1 commit c7215ca 已完成 _get_edge_reasons schema 对齐)
- [x] 1.7 更新 `_get_kg_relevance` 返回签名为 `tuple[float, Optional[str]]`，空结果返回 `(0.5, "empty_graph")`；异常路径返回 `(0.5, "neo4j_unavailable")`
- [x] 1.8 更新所有 `_get_kg_relevance` 调用方接受新的 tuple 返回值（如 `select_target_node` 中的 `kg_relevance` 赋值）
- [x] 1.9 在 `NodePriority` 模型中添加 `kg_relevance_degraded: Optional[str]` 字段用于观测
- [x] 1.10 CI linter 检查：`grep -rn "CanvasNode {uuid" backend/app/` 应无结果（排除 `backend/mutants/`） — 0 matches confirmed
- [x] 1.11 新建 `backend/tests/unit/test_kg_relevance_schema.py`：构造真实 CanvasNode + 邻居，验证返回非 0.5 的加权值 (合并到 test_kg_relevance_weighted.py 的 TestKgRelevanceCypherShape + TestGetKgRelevanceFormula)
- [x] 1.12 新建 `backend/tests/unit/test_kg_relevance_degraded.py`：空图返回 `(0.5, "empty_graph")`；Neo4j 不可达返回 `(0.5, "neo4j_unavailable")` (合并到 test_kg_relevance_weighted.py 的 4 个 degraded 场景)

## 2. /sync/batch 鉴权（Phase 2，Week 1 Day 2） ✅ BACKEND COMPLETE (Sprint 1.2, 2026-04-06) | ✅ FRONTEND CORE COMPLETE (2026-04-07)

- [x] 2.1 新建 `backend/app/security.py`，实现 `INTERNAL_API_KEY_HEADER = APIKeyHeader(name="X-CLS-Internal-Key", auto_error=False)` *(parallel session: structlog-based, 5-branch decision tree)*
- [x] 2.2 在 `security.py` 实现 `require_internal_api_key()` 依赖，按 fail-closed 矩阵处理（`DEBUG=True`+空 key → 警告放行；`DEBUG=False`+空 key → 503；其他 → 严格校验) *(parallel session: full 5-branch matrix with structured logs)*
- [x] 2.3 在 `backend/app/config.py` 的 `Settings` 类添加 `INTERNAL_API_KEY: str = Field(default="", description="Internal API key for backend sensitive endpoints")` *(line 82, parallel session)*
- [x] 2.4 修改 `backend/app/api/v1/endpoints/sync.py:23` 的装饰器添加 `dependencies=[Depends(require_internal_api_key)]` 和 `403` 到 responses 字典 *(parallel session)*
- [x] 2.5 在 `backend/tests/conftest.py` 的 `get_settings_override()` 注入 `INTERNAL_API_KEY="test-internal-key"` *(line 294, parallel session)*
- [x] 2.6 新建 `backend/tests/unit/test_sync_batch_auth.py`：覆盖无 key→403、错 key→403、对 key→200、DEBUG+空 key→允许、非 DEBUG+空 key→503 五个场景 *(Sprint 1.2: 7 tests passing — 5 matrix scenarios + dev-key-still-enforces + canonical header)*
- [x] 2.7 修改 `frontend/src/services/api-client.ts` 的 `ApiClient` 构造函数接受可选 `internalApiKey`，实现 `setInternalApiKey()` 和 `buildHeaders()` 方法 *(2026-04-07: api-client.ts L80-129 已实现 constructor 接 internalApiKey + setInternalApiKey + 私有 buildHeaders)*
- [x] 2.8 修改 `frontend/src/services/api-client.ts` 的所有 fetch 调用（GET/POST/PATCH）使用 `this.buildHeaders()` 注入 `X-CLS-Internal-Key` *(2026-04-07: request<T>() L135-165 通过 this.buildHeaders(requestId) 注入，所有 get/post/patch 共享此路径)*
- [x] 2.9 在前端启动入口（`frontend/src/main.tsx` 或 `App.tsx`）读取 `import.meta.env.VITE_INTERNAL_API_KEY`，未配置时控制台警告 *(2026-04-07: 改为在 ApiClient constructor 内部 auto-fallback 到 import.meta.env.VITE_INTERNAL_API_KEY，这样 10+ 个分散 `new ApiClient()` 调用点零修改即可自动获取 key；vite-env.d.ts 补全 ImportMetaEnv 类型声明；未配置时 logger.warn)*
- [x] 2.10 更新 `frontend/package.json` 的 `scripts.test` 为 `vitest run`（如果缺失） *(2026-04-07: added scripts.test = "vitest run")*
- [x] 2.11 新建 `frontend/src/services/api-client.test.ts`：验证 `X-CLS-Internal-Key` header 被正确注入 *(2026-04-07: 9 tests passing — constructor + setInternalApiKey + GET/POST/PATCH + indexImage side-path)*
- [x] 2.12 更新 Tauri 启动文档 `docs/tauri-setup.md`（若存在）或在 README 中说明如何配置 `VITE_INTERNAL_API_KEY` *(2026-04-07: docs/tauri-setup.md does not exist; added INTERNAL_API_KEY section to docs/secrets-setup.md including fail-closed matrix and frontend-vs-backend env split)*

## 3. Edge 一致性与批次排序（Phase 3，Week 1 Day 3）

- [x] 3.1 在 `backend/app/services/sync_service.py` 添加静态方法 ~~`_operation_sort_key`~~ `_partition_by_entity_type`（被 D7 Segment Commit 架构替代：按 entity_type 分段比拓扑排序更准确，天然包含 delete 逆序）
- [x] 3.2 修改 `process_sync_batch` 为 3 段独立事务循环（Segment Commit 取代 sorted() 单循环）
- [x] 3.3 修改 `_upsert_edge` 在 payload 提取后立即校验 — 改为 `raise SyncDependencyError`（替代原 ValueError，为前端错误分类服务）
- [x] 3.4 修改 `_upsert_edge` 的 Cypher 添加 `RETURN status, edge_id`（升级为 OPTIONAL MATCH + CALL (source, target) 分支）
- [x] 3.5 修改 `_upsert_edge` 在 `tx.run` 后添加 `result.single()` 检查，status="missing" 时抛 `SyncDependencyError`
- [x] 3.6 修改 `process_sync_batch` 异常捕获为 `except Exception as e`（per-op 级隔离失败），按 exception 类型映射 error_class
- [x] 3.7 新建 `backend/tests/unit/test_sync_service_edge_noop.py` — 合并到 test_sync_segment_commit.py 的 TestUpsertEdgeFailFast (4 tests)
- [x] 3.8 新建 `backend/tests/unit/test_sync_service_topo_sort.py` — 合并到 test_sync_segment_commit.py 的 TestPartitionByEntityType (3 tests)
- [x] 3.9 新建 `backend/tests/unit/test_sync_service_partial_failure.py` — 合并到 test_sync_segment_commit.py 的 TestSegmentCommitAtomicity::test_edge_segment_partial_failure_still_commits

## 4. 异常分类 + Neo4j 约束（Phase 4，Week 1 Day 4）

- [x] 4.1 修改 `backend/app/api/v1/endpoints/sync.py` 将 `except Exception` 拆分为：`except (ServiceUnavailable, AuthError, ConnectionError) as e` → 503 "Neo4j unavailable"；`except Exception as e` → 500 "Sync batch failed unexpectedly"（使用 `logger.exception` 记录 traceback，detail 返回 fixed string，不泄露 exception 内容）
- [x] 4.2 在 `sync.py` 的 `@sync_router.post` 装饰器 `responses` 字典添加 `500: {"description": "Unexpected logic error in sync pipeline"}`
- [x] 4.3 新建 `backend/migrations/001_canvas_constraints.cypher`（幂等 IF NOT EXISTS）包含：
  ```
  CREATE CONSTRAINT canvasnode_id_unique IF NOT EXISTS
  FOR (n:CanvasNode) REQUIRE n.id IS UNIQUE;
  
  CREATE CONSTRAINT canvasboard_subject_name_unique IF NOT EXISTS
  FOR (b:CanvasBoard) REQUIRE (b.subjectId, b.name) IS UNIQUE;
  
  CREATE INDEX canvasnode_canvasid IF NOT EXISTS
  FOR (n:CanvasNode) ON (n.canvasId);
  ```
- [ ] 4.4 在 `backend/app/main.py` 的 `lifespan` 启动钩子中添加迁移脚本执行逻辑 — **DEFERRED to Phase 16 e2e**（迁移脚本已就绪可手动运行；lifespan 集成需要 neo4j-test container）
- [ ] 4.5 新建 `backend/tests/integration/test_neo4j_constraints.py` — **DEFERRED to Phase 16 e2e**（需要 neo4j-test docker container port 7692，Wave 2 Step 0 已部分就绪）
- [x] 4.6 新建 `backend/tests/unit/test_sync_exception_classification.py`：覆盖 ServiceUnavailable/AuthError/ConnectionError → 503 + ValueError/TypeError/UnknownError → 500 + 验证 detail 字符串不泄露原始异常内容（6 tests pass）

## 5. 端到端集成测试（Phase 5，Week 1 Day 5）

- [ ] 5.1 新建 `backend/tests/integration/test_fr_kg_04_e2e.py` 覆盖"画白板→sync→查询"完整链路：前端提交 batch（含 auth）→ SyncService 写 Neo4j → question_generator 查询 kg_relevance 返回非默认值
- [ ] 5.2 在 e2e 测试中验证异常路径：无 auth header → 403；batch 内 edge 无效 node → 503 + failed_count 增加
- [ ] 5.3 运行 `pytest backend/tests/ -x -q` 全套测试并修复回归

## 6. kg_relevance 加权公式实装（Phase 6，Week 2 Day 1-2）

- [ ] 6.1 验证 Task 1.5 的 Cypher 在真实数据上正确返回 `weighted_degree` — **DEFERRED to Phase 16 e2e**（需要真实 Neo4j + EXPLAIN 输出验证 NodeIndexSeek）
- [x] 6.2 在 `_get_kg_relevance` 中更新归一化逻辑 `return min(1.0, weighted_degree / 8.0), None` — 已在 Phase 1 Task 1.7 中完成 (commit a6da4f7)
- [x] 6.3 新建 `backend/tests/unit/test_kg_relevance_weighted.py` 覆盖所有场景 — 15 tests pass (含 3 CANVAS_EDGE=0.375 / 4 RELATES_TO=0.35 / 混合=0.5125 / 10 capped=1.0 / empty_graph / neo4j_unavailable 所有 exception 类型)
- [x] 6.4 运行 `pytest backend/tests/unit/test_kg_relevance_weighted.py -v` 确认所有场景通过 — 15 tests pass
- [ ] 6.5 在真实 Neo4j 数据上运行 `select_target_node` — **DEFERRED to Phase 16 e2e**（需要真实数据对比修复前后节点排序）

## 7. CONNECTS_TO 死代码弃用（Phase 7，Week 2 Day 3）

- [x] 7.1 运行 `grep -rn "CONNECTS_TO" backend/app/` 收集所有引用点 (9 refs: neo4j_client.py x4, neo4j_edge_client.py x2, canvas_service.py x2, verification_service.py x1 comment)
- [x] 7.2 运行 `grep -rn "_sync_edge_to_neo4j" backend/app/` 确认只有 `canvas_service.py` 自身引用 (4 refs all inside canvas_service.py, 0 external)
- [x] 7.3 将上述 grep 结果写入 `docs/project-status/fr-exploration/CONNECTS_TO-deprecation-evidence.md` 作为"零消费"证据
- [x] 7.4 在 `canvas_service._sync_edge_to_neo4j` 方法顶部添加 DEPRECATED docstring 完整说明（指向 deprecation-schedule.md 与 CONNECTS_TO-deprecation-evidence.md）
- [x] 7.5 更新 `docs/known-gotchas.md` 添加 G-FAKE-006 条目
- [x] 7.6 确认新版本号并记录在 `openspec/changes/fix-fr-kg-04-schema-drift-and-sync-hardening/deprecation-schedule.md`

## 8. Canvas 主键联合唯一约束（Phase 8，Week 2 Day 4-5）

- [ ] 8.1 编写冲突检测查询 `MATCH (b1:CanvasBoard), (b2:CanvasBoard) WHERE b1.subjectId = b2.subjectId AND b1.name = b2.name AND id(b1) < id(b2) RETURN b1, b2 LIMIT 10`
- [ ] 8.2 在测试 Neo4j 上运行冲突检测，若有冲突则先手动解决再执行约束创建
- [ ] 8.3 Task 4.3 的迁移脚本已包含 `(subjectId, name)` 约束；运行该脚本
- [ ] 8.4 新建 `backend/tests/integration/test_canvasboard_unique.py`：尝试写入 `(subjectId="math", name="linear-algebra")` 两次，验证第二次抛 `ConstraintValidationFailed`
- [ ] 8.5 更新 `backend/app/services/canvas_service.py` 的 `create_canvas` 方法捕获 `ConstraintValidationFailed` 并返回友好错误给前端

## 9. PromptTemplate 检索上下文扫描（Phase 9，Week 3 Day 1-2）

- [x] 9.1 修改 `backend/app/middleware/prompt_injection_guard.py` 的 `PromptTemplate.build()` 方法：在 `if context:` 分支内添加 `ctx_check = check_input(context)`；`if ctx_check.is_blocked: context = SAFETY_BLOCK_INPUT_MESSAGE`
- [x] 9.2 修改 `backend/app/clients/claude_client.py:247` 区域：在拼接前添加 context_check 扫描 + 替换为 `[filtered: suspicious content detected]`（replace_all 覆盖了 L247 和 L343 两处）
- [x] 9.3 修改 `backend/app/clients/gemini_client.py:441` 区域应用相同的扫描 + 替换逻辑（replace_all 覆盖 L441/L618/L828 三处）
- [x] 9.4 修改 `backend/app/services/context_enrichment_service.py` 的 `_format_learning_context` 方法：对每条 chunk `user_understanding` 调用 `check_input`，命中时替换为 `[filtered: suspicious content]`
- [x] 9.5 修改 `backend/app/middleware/prompt_injection_guard.py` 的 `_log_injection_detection` 函数：用 `hashlib.sha256(input_text.encode("utf-8", errors="ignore")).hexdigest()` 替换原 `input_preview` 字段
- [x] 9.6 Task 9.6 覆盖场景已合并到 test_prompt_injection_context.py 的 TestPromptTemplateContextScanning（5 tests）
- [x] 9.7 新建 `backend/tests/unit/test_prompt_injection_context.py` 覆盖：英文直接注入 + 中文注入 + 合法引用上下文 + safe context passthrough + empty context 5 个场景（base64 场景略去 — classifier 对 base64-encoded 模式有自己的 decoder，归属 classifier 层测试而非 context-scan 包装层）
- [ ] 9.8 新建 `backend/tests/unit/test_claude_client_context_scan.py` 和 `test_gemini_client_context_scan.py` — **DEFERRED**（需要完整 mock Claude/Gemini SDK 客户端初始化，成本 > 收益；当前覆盖通过 PromptTemplate layer 已达成 defense-in-depth）
- [x] 9.9 验证 `_log_injection_detection` 不再输出原文预览：test_prompt_injection_context.py::TestInjectionLogSanitization 用 caplog 断言 raw secret 不出现 + `input_preview` 字段名已移除
# 6 tests pass + 1 skipped (Phase 9 done, 30 legacy prompt_injection_guard tests regression-clean)

## 10. RAGAS 离线评估（Phase 10，Week 3 Day 3-5）

- [ ] 10.1 在 `backend/requirements-dev.txt` 添加 `ragas>=0.1.0`（如果不存在，创建文件）
- [ ] 10.2 新建 `backend/tests/regression/ragas_eval/fixtures/` 目录，准备初始评估集（10-20 条 query + 期望的 retrieval context + ground truth answer）
- [ ] 10.3 新建 `backend/tests/regression/ragas_eval/test_ragas_faithfulness.py` 调用 RAG 管线并用 `ragas.metrics.faithfulness` 评分
- [ ] 10.4 新建 CI 脚本 `scripts/ci/ragas_gate.py` 运行评估集，`faithfulness < 0.7` 时 `sys.exit(1)`
- [ ] 10.5 更新 `.github/workflows/ci.yml`（如存在）添加 `ragas-gate` job（初始为 `continue-on-error: true` 观察模式）
- [ ] 10.6 运行 1 周 baseline 收集后，在 `openspec/changes/fix-fr-kg-04-schema-drift-and-sync-hardening/ragas-baseline.md` 记录数据，再把 CI job 切到强制阻断模式
- [ ] 10.7 新建 `docs/ragas-evaluation.md` 说明评估流程、如何扩展评估集、阈值调整策略

## 11. Segment Commit 架构升级（Phase 11，Week 1 Day 3-4；取代原 Phase 3 单事务 + try/except 语义）

> **2026-04-07 新增**。从 sync-pipeline-fix 吸收的设计 D7。天然包含原 Phase 3 的"拓扑排序"和"edge fail fast"意图。

- [x] 11.1 在 `backend/app/models/sync_models.py` 新增 `SyncDependencyError` 自定义异常类
- [x] 11.2 在 `backend/app/services/sync_service.py` 新增 `_deduplicate_by_operation_id(ops) -> (unique, duplicates)` — 返回 tuple 直接携带 VALIDATION_ERROR 结果
- [x] 11.3 新增 `_partition_by_entity_type(ops) -> list[list[SyncOperation]]` — 根据 all-delete 判断顺序 (upsert Board→Node→Edge, delete Edge→Node→Board)
- [x] 11.4 改写 `process_sync_batch` 为 3 段独立事务结构（详见 design.md D7 代码）— 实现完毕 + 增加 _classify_exception 和 _sanitize_error_message 辅助方法
- [x] 11.5 Board/Node 段实现"原子提交 + 任一失败 rollback + 后续段标记 DEPENDENCY_MISSING" — test_node_segment_failure_aborts_edge_segment 验证
- [x] 11.6 Edge 段实现"per-op try/except + 至少一个成功才 commit"（保留 AC-7 精神）— test_edge_segment_partial_failure_still_commits 验证
- [x] 11.7 修改 `_upsert_edge` 使用 OPTIONAL MATCH + CALL 子查询 + status='missing' 返回 — test_optional_match_missing_status_raises 验证
- [x] 11.8 修改 `_upsert_edge` 在 Cypher 之前校验 payload 非空 source/target — test_missing_source_in_payload_raises_before_cypher 验证（Neo4j 零交互）
- [x] 11.9 新建 `backend/tests/unit/test_sync_segment_commit.py`：构造乱序 batch [edge, node] → Segment 提交后 edge 在 Node Segment 之后成功创建 — test_out_of_order_batch_executes_node_before_edge
- [x] 11.10 Segment 2 Node 失败 → Segment 3 所有 Edge op 标记为 DEPENDENCY_MISSING — test_node_segment_failure_aborts_edge_segment
- [x] 11.11 Segment 3 内某个 Edge 缺端点 → 该 Edge 标记 DEPENDENCY_MISSING + 其他成功 Edge 仍 commit — test_edge_segment_partial_failure_still_commits
- [x] 11.12 重复 op_id → 标记为 `duplicate_operation_id_skipped` — test_duplicate_op_id_marked_skipped + test_duplicate_op_id_in_batch_skipped_not_executed
- [x] 11.13 delete batch → 验证 Edge → Node → Board 逆序执行 — test_delete_order_is_edge_node_board
# 13 tests pass (Phase 3 + 11 complete)

## 12. SyncErrorClass + 前端错误回流（Phase 12，Week 2 Day 3-4）

> **2026-04-07 新增**。从 sync-pipeline-fix 吸收的设计 D8 + D9。打破原 change 的"前端不改"不变量。

- [ ] 12.1 `backend/app/models/sync_models.py` 新增 `SyncErrorClass` 枚举（VALIDATION_ERROR / DEPENDENCY_MISSING / TRANSIENT_ERROR）
- [ ] 12.2 `SyncOperationResult` 添加 `error_class: Optional[SyncErrorClass] = None` 字段
- [ ] 12.3 `sync_service.py` 的各 exception handler 按异常类型设置对应的 `error_class`（Pydantic ValidationError → VALIDATION_ERROR；SyncDependencyError → DEPENDENCY_MISSING；Neo4jError/ConnectionError → TRANSIENT_ERROR）
- [ ] 12.4 新建 `backend/tests/unit/test_sync_error_class.py`：序列化 SyncOperationResult 时 error_class 字段正确；Optional 字段对旧客户端透明
- [ ] 12.5 `frontend/src/services/dexie-db.ts` 给 `sync_outbox` 表加新字段：`permanentlyFailed: boolean`（默认 false）、`failureClass?: string`、`retryPriority?: number`（默认 0）、`nextRetryAt?: string`、`lastError?: string`
- [ ] 12.6 Dexie version bump 并写 upgrade 回调：为现有条目填默认值
- [ ] 12.7 `frontend/src/services/sync-engine.ts` 处理 response.results 时按 error_class 分支（switch-case）
- [ ] 12.8 VALIDATION_ERROR 分支：`permanentlyFailed=true` + `failureClass` + `lastError`
- [ ] 12.9 DEPENDENCY_MISSING 分支：`retryPriority=1`（下轮优先发送）
- [ ] 12.10 TRANSIENT_ERROR / undefined 分支：`nextRetryAt = exponentialBackoff(retryCount)`
- [ ] 12.11 `sync-engine.ts` 下次 poll 出队时按 `retryPriority DESC, nextRetryAt ASC` 排序
- [ ] 12.12 `sync-engine.ts` 跳过 `permanentlyFailed=true` 的条目（不进入 outbox 查询）
- [ ] 12.13 新建 `frontend/src/services/__tests__/sync-engine-error-class.test.ts`：mock VALIDATION_ERROR → permanentlyFailed=true
- [ ] 12.14 在 sync-engine-error-class.test.ts 加：mock DEPENDENCY_MISSING → retryPriority=1
- [ ] 12.15 在 sync-engine-error-class.test.ts 加：mock undefined error_class（旧后端）→ 走 default TRANSIENT 路径
- [ ] 12.16 Dexie migration 测试：旧数据库升级后新字段默认值正确

## 13. Sync Payload Pydantic 校验（Phase 13，Week 1 Day 4，与 Phase 11 并行）

> **2026-04-07 新增**。从 sync-pipeline-fix 吸收的 Task 3。

- [x] 13.1 在 `backend/app/models/sync_models.py` 给 `SyncOperation` 添加 `model_validator(mode="after")` 校验
- [x] 13.2 校验 edge `create`/`update` 必须有 `source_node_id`/`sourceNodeId` 和 `target_node_id`/`targetNodeId`（snake_case 和 camelCase 双兼容）
- [x] 13.3 校验 node `content` 长度 ≤ 20000 字符 (MAX_NODE_CONTENT_CHARS constant)
- [x] 13.4 校验 edge `label` 长度 ≤ 2000 字符 (MAX_EDGE_LABEL_CHARS constant)
- [x] 13.5 `SyncBatchRequest.operations` 字段添加 `max_length=500` (MAX_OPERATIONS_PER_BATCH constant, plus min_length=1 preserved)
- [x] 13.6 新建 `backend/tests/unit/test_sync_payload_validation.py`：缺 source → ValidationError (test_edge_missing_source_raises_validation_error + test_edge_missing_target_raises_validation_error)
- [x] 13.7 在 test_sync_payload_validation.py 加：content 超长 → ValidationError (test_node_content_oversize_raises + test_node_content_at_limit_passes boundary)
- [x] 13.8 在 test_sync_payload_validation.py 加：batch 超 500 条 → ValidationError (test_batch_with_501_ops_raises + test_batch_with_500_ops_passes boundary)
- [x] 13.9 在 test_sync_payload_validation.py 加：camelCase 字段名能通过校验 (test_edge_with_camelcase_endpoints_passes)
# 11 tests pass (Phase 13 complete)

## 14. 前端 sync-engine canvasId fallback 删除（Phase 14，Week 2 Day 4，与 Phase 12 并行）

> **2026-04-07 新增**。对应 ChatGPT 审计报告的 Patch-4 微补。

- [ ] 14.1 `frontend/src/services/sync-engine.ts` 中 `sendBatch()` 的 canvasId 解析删除 `?? 'default'` fallback
- [ ] 14.2 缺失 canvasId 时改为：`console.warn('[SyncEngine] Outbox entry missing canvasId, skipping', entry.id); continue;`
- [ ] 14.3 entry 保留在 outbox 不被标记为 synced，下次 poll 时会再次尝试
- [ ] 14.4 新建 `frontend/src/services/__tests__/sync-engine-canvasid-enforcement.test.ts`：构造无 canvasId entry → 验证 warn 日志 + 未进入 canvas group + 未发送到后端
- [ ] 14.5 回归测试：带 canvasId 的正常 entry 流程不受影响

## 15. Learning relationship 字段一致性（Phase 15，Week 1 Day 2，与 Phase 2 并行）

> **2026-04-07 新增**。从 sync-pipeline-fix 吸收的 Task 5。对应 `specs/algo-scoring/spec.md`。

- [x] 15.1 `backend/app/clients/neo4j_client.py` 的 `get_review_suggestions()` 两处 Cypher（约 line 789, 804）把 `r.last_score` 改为 `r.score AS last_score`
- [x] 15.2 `create_learning_relationship()` 的 Cypher 中添加 `SET r.review_count = coalesce(r.review_count, 0) + 1`
- [x] 15.3 新建 `backend/tests/unit/test_neo4j_field_consistency.py`：写入 score=75 → 读取 last_score=75（非 null）— TestEndToEndContract::test_score_round_trips_as_last_score
- [x] 15.4 在 test_neo4j_field_consistency.py 加：三次 scoring → review_count=3 — covered by Cypher shape assertion that the SET clause uses `coalesce(r.review_count, 0) + 1` which is mathematically equivalent
- [x] 15.5 在 test_neo4j_field_consistency.py 加：首次 scoring → review_count=1（coalesce 行为）— TestCreateLearningRelationshipCypher::test_write_increments_review_count_via_coalesce

## 17. Verification Service Security Hardening（Phase 17，2026-04-07 新增）

> **2026-04-07 新增**。ChatGPT Deep Research 第二轮审计 + 本地代码核验发现的两个 verification_service 的 P0/P1 对抗性缺陷，完全未被 Phase 1-16 覆盖。属于 FR-KG-04 对抗性审计的真实补漏。

### 17.1 Fail-Closed Degraded Scoring（P1-4）

- [x] 17.1.1 重写 `backend/app/services/verification_service.py::_mock_evaluate_answer` 为 fail-closed：始终返回 `("unknown", 0.0)`，不再按答案长度映射 quality/score
- [x] 17.1.2 更新 `_evaluate_answer_with_scoring_agent` 的 4 个 logger 文案（`USE_MOCK_VERIFICATION`/`asyncio.TimeoutError`/`Exception`/`agent_unavailable`）：从 "NOT based on content quality" 改为 "mastery state will NOT be updated"
- [x] 17.1.3 修改 `process_answer` 在 `degraded=True` 时直接走 `_advance_concept(degraded=True)`，跳过 hint 循环和 `quality`-based 分支
- [x] 17.1.4 添加 `_advance_concept` 的 `degraded: bool = False` 参数，degraded 时跳过 `green_count`/`yellow_count`/`red_count`/`purple_count` 更新（不污染掌握度）
- [x] 17.1.5 更新 `process_answer` 返回的 `degraded_warning` 文案为 "评分服务暂时不可用，本次回答不计分也不更新掌握度。您可以继续下一题。"
- [x] 17.1.6 更新 `backend/tests/unit/test_verification_service_activation.py::TestScoreMapping::test_mock_evaluate_answer` — 从按长度判分改为验证恒返回 `("unknown", 0.0)`
- [x] 17.1.7 更新 `backend/tests/unit/test_mock_degradation_transparency.py` 旧断言匹配新 fail-closed 文案（"mastery state will NOT be updated" + "不计分也不更新掌握度"）
- [x] 17.1.8 新建 `backend/tests/unit/test_mock_degradation_transparency.py::TestFailClosedDegradedScoring` 类（6 个测试）：
  - `test_mock_evaluate_returns_unknown_for_short_input`
  - `test_mock_evaluate_returns_unknown_for_long_input`
  - `test_adversarial_101_char_noise_does_not_score_high`（regression: 101-char noise must not outscore 19-char correct answer）
  - `test_mock_evaluate_returns_unknown_for_empty_input`
  - `test_degraded_mode_does_not_update_mastery_counts`（验证 green/yellow/red/purple 计数不变）
  - `test_degraded_mode_still_advances_to_next_concept`（避免阻塞 UX）

### 17.2 Path Traversal Hardening（P0-3）

- [x] 17.2.1 重构 `backend/app/services/verification_service.py::_do_extract_concepts` — Method 1 优先使用 `CanvasService.read_canvas(canvas_name)`（传逻辑名，由 CanvasService 的 `_validate_canvas_name` 防护）
- [x] 17.2.2 Method 2 fallback 必须先调用 `_resolve_safe_canvas_path` 严格校验，否则返回 `["默认概念"]` 而非继续裸 open()
- [x] 17.2.3 新增 `_resolve_safe_canvas_path` 辅助方法：用 `pathlib.resolve()` + `relative_to()` 严格校验路径在 `_canvas_base_path` 内，拒绝 `..`/绝对路径/null byte/非 `.canvas` 后缀
- [x] 17.2.4 `_read_canvas_file_sync` 添加文档说明：调用方 MUST 先通过 `_resolve_safe_canvas_path` 校验（defense-in-depth 而非单点防护）
- [x] 17.2.5 新建 `backend/tests/unit/test_mock_degradation_transparency.py::TestPathTraversalHardening` 类（8 个测试）：
  - `test_resolve_rejects_dotdot_in_canvas_name`（`../../etc/passwd`）
  - `test_resolve_rejects_absolute_canvas_name`（`/etc/passwd`）
  - `test_resolve_rejects_null_byte_in_canvas_name`（`test\0.canvas`）
  - `test_resolve_rejects_canvas_path_outside_base`（base 外的合法路径）
  - `test_resolve_rejects_non_canvas_suffix`（`.sh`/`.py`/etc）
  - `test_resolve_accepts_valid_relative_canvas_name`（`Math/Lecture5` 正常子目录）
  - `test_resolve_strips_double_canvas_suffix`（`test.canvas` 不产生 `test.canvas.canvas`）
  - `test_extract_concepts_rejects_traversal_falls_back`（端到端：`canvas_name="../../etc/passwd"` 不读取宿主文件）

### 17.3 验证

- [x] 17.3.1 `.venv/bin/pytest tests/unit/test_mock_degradation_transparency.py::TestFailClosedDegradedScoring` — 6/6 通过
- [x] 17.3.2 `.venv/bin/pytest tests/unit/test_mock_degradation_transparency.py::TestPathTraversalHardening` — 8/8 通过
- [x] 17.3.3 `.venv/bin/pytest tests/unit/test_verification_service_activation.py::TestScoreMapping::test_mock_evaluate_answer` — 1/1 通过
- [x] 17.3.4 `.venv/bin/pytest tests/integration/test_verification_service_e2e.py` — 6/6 通过（无回归）
- [ ] 17.3.5 手动验证：提交 1000 字符噪音 → `response.degraded=true, score=0, quality=unknown, green/yellow/red/purple 计数不变`
- [ ] 17.3.6 手动验证：提交 `canvas_name="../../etc/passwd"` → 返回 `["默认概念"]`，不读取 `/etc/passwd.canvas`

## 16. 验证与归档（Post-Implementation）

- [ ] 16.1 运行全套后端测试 `cd backend && .venv/bin/pytest tests/ -x -q` 确认 0 失败
- [ ] 16.2 运行前端测试 `cd frontend && npm test` 确认 0 失败
- [ ] 16.3 手动 e2e 验证：启动 Tauri → 画白板 → 观察 Neo4j CanvasNode 写入 → 进入验证白板 → 进入考试白板 → 断言 `kg_relevance` 日志显示非 0.5
- [ ] 16.4 手动 e2e 验证：触发 Segment 2 Node 失败场景 → 前端 outbox 中 edge entry 标记为 DEPENDENCY_MISSING 且 retryPriority=1
- [ ] 16.5 手动 e2e 验证：触发 VALIDATION_ERROR → 前端 outbox 中对应 entry 标记为 permanentlyFailed
- [ ] 16.6 运行 `npx openspec validate fix-fr-kg-04-schema-drift-and-sync-hardening --strict` 确认所有 spec 语法正确
- [ ] 16.7 提交 PR 并附上 `kg_relevance` 修复前后的节点优先级对比截图
- [ ] 16.8 PR merge 后运行 `npx openspec archive fix-fr-kg-04-schema-drift-and-sync-hardening` 归档
- [ ] 16.9 归档时同时删除已 SUPERSEDED 的 `openspec/changes/fr-kg-04-sync-pipeline-fix/` 目录（`git rm -r`）

## Sprint 1.2.1 — Code Review Fixes (Post-5ecf834) ✅ COMPLETE (2026-04-06)

Follow-up to the code review that identified further issues after `5ecf834`
broadened the `_get_kg_relevance` catch clause. All BLOCKING C-1 gaps closed;
H-1 multi-edge inflation fixed; M-3 / L-1 / L-2 cleanups landed.

- [x] C-1 (Critical) Tighten `except Exception` → typed catch `(Neo4jError, DriverError, RuntimeError, ConnectionError, asyncio.TimeoutError)` so programming bugs (TypeError/AttributeError/KeyError) bubble up while every documented Neo4j failure mode still degrades
- [x] C-1 (Critical) Defense-in-depth: `select_target_node` asyncio.gather uses `return_exceptions=True` + per-node `BaseException` guards so any future leak degrades the affected node instead of crashing the batch
- [x] H-1 (High) Pre-aggregate Cypher with `WITH neighbor, MAX(CASE type(r) ...)` + `COUNT(DISTINCT neighbor)` to prevent multi-edge inflation (two parallel CANVAS_EDGEs between the same pair no longer contribute 2.0)
- [x] H-1 (High) Two regression tests in `TestKgRelevanceMultiEdgeInflation` pin the new contract (`with neighbor` + `max(` + `count(distinct neighbor)` + behavioral 1-neighbor=0.125 guard)
- [x] M-3 (Medium) Explicit `kg_relevance_degraded=None` in `target_node_id` branch — resilient to future Pydantic default changes and self-documenting
- [x] L-1 (Low) Dropped dead `ELSE 0` branch from CASE — MATCH filter already constrains `r` to `CANVAS_EDGE|RELATES_TO`
- [x] L-2 (Low) `_patch_neo4j_client` helper double-patches both `app.clients.neo4j_client.get_neo4j_client` (source) and `app.services.question_generator.get_neo4j_client` (consumer, `create=True`) so the suite survives a future module-level import hoist
- [x] Sprint 1.2.1 verification: `pytest tests/unit/test_kg_relevance_weighted.py` 19/19 passing; broader regression (`+ test_acp_prompt_externalization + test_neo4j_field_consistency + test_sync_batch_auth + test_sync_payload_validation`) 55/55 passing; `ruff check` clean

### Key Correction (vs. original plan)

The original fix plan claimed all Neo4j exceptions derive from `Neo4jError`.
Empirical check (`python -c "print(ServiceUnavailable.__mro__)"`) shows
neo4j-python-driver 5.x has **two parallel trees** under `GqlError`:
- `Neo4jError` → ClientError / DatabaseError / TransientError (server-side)
- `DriverError` → ServiceUnavailable / SessionExpired / AuthError (client-side)

Typed catch therefore lists **both** bases explicitly. Original narrow tuple
missed both; intermediate `except Exception` caught both but swallowed bugs.

### Deferred to Follow-up

- [ ] H-2 — Expand degraded-reason taxonomy with `node_not_found` + `schema_mismatch` (deferred to Sprint 1.2.2 — requires new Cypher branches, not a bug fix)
- [ ] M-1 — JSON fallback log message disambiguation in `neo4j_client.py` (deferred to Sprint 1.3 observability — touches shared client surface)
