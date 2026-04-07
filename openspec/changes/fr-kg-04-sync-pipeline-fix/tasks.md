# FR-KG-04 Sync 管道修复 — 任务清单

> 2026-04-06 重构：原 Task 1 + Task 2 合并为 Task 7（Segment 提交天然包含顺序和 Fail Fast）；新增 Task 8/9（错误分类 + 前端回流）。

## Task 3: SyncOperation payload 校验
- **文件**: `backend/app/models/sync_models.py`
- **改动**:
  - 添加 `model_validator` 校验 edge 的 source_node_id/target_node_id 必填
  - 支持 snake_case 和 camelCase 字段名（兼容前端，Wave 1 已确认前端发 camelCase）
  - 添加 node content ≤ 20000 字符、edge label ≤ 2000 字符上限
  - `operations` 字段添加 `max_length=500`
- **验证**: 单元测试 — 缺字段 → Pydantic ValidationError；字段超长 → ValidationError
- **状态**: [ ] 未开始
- **优先级**: P1（独立修复，可并行）

## Task 4: sync.py HTTP 错误分类
- **文件**: `backend/app/api/v1/endpoints/sync.py`
- **改动**:
  - 拆分 `except Exception` 为四层（ValueError→400, ServiceUnavailable→503, Neo4jError→500, Exception→500）
  - 移除 `str(e)[:200]` 泄露（503 只返回 "Neo4j unavailable"）
- **验证**: 手动/集成测试 — 缺字段→400，关 Neo4j→503，正常→200
- **状态**: [ ] 未开始
- **优先级**: P1（独立修复，可并行）

## Task 5: Neo4jClient 字段一致性修复
- **文件**: `backend/app/clients/neo4j_client.py`
- **改动**:
  - `get_review_suggestions()` 的 `r.last_score` 改为 `r.score as last_score`（两处 query: line 789, 804）
  - `create_learning_relationship()` 添加 `r.review_count = coalesce(r.review_count, 0) + 1`
- **验证**: 单元测试 — 查询返回的 last_score 非 null；review_count 随每次 update 递增
- **状态**: [ ] 未开始
- **优先级**: P1（独立修复，可并行）

## Task 7: SyncService Segment 原子提交改造
> **合并自原 Task 1（拓扑排序）+ 原 Task 2（显式失败）**。Segment 提交天然包含依赖顺序（Board → Node → Edge）和 Fail Fast 检查。

- **文件**: `backend/app/services/sync_service.py`
- **依赖**: Task 3 (payload 校验), Task 8 (SyncErrorClass 枚举)
- **改动**:
  - `process_sync_batch()` 重写为 3 段独立事务（详见 design.md D6）
    - Segment 1 (Board): 原子提交，任一失败 → rollback + 后续段标记 DEPENDENCY_MISSING
    - Segment 2 (Node): 原子提交，任一失败 → rollback + Segment 3 标记 DEPENDENCY_MISSING
    - Segment 3 (Edge): per-op try/except，末尾一起 commit（保留 AC-7 精神限定到 Edge）
  - Delete 操作构造逆序 segments (Edge → Node → Board)
  - `_deduplicate_by_operation_id()` 辅助函数：重复 op_id 标记为 `duplicate_operation_id_skipped`
  - `_partition_by_entity_type()` 辅助函数：按实体类型拆分 operations
  - `_upsert_edge()` 改用 OPTIONAL MATCH + status 返回（D2），缺端点时抛 `SyncDependencyError`
  - `SyncDependencyError` 自定义异常类（位于 `sync_service.py` 或 `sync_models.py`）
- **验证**:
  - 单元测试：乱序 batch [edge, node] → Segment 提交后 edge 在 Segment 3 成功创建
  - 单元测试：Segment 2 Node 失败 → Segment 3 所有 Edge op 标记为 DEPENDENCY_MISSING
  - 单元测试：Segment 3 内某个 Edge 缺端点 → 该 Edge 标记 DEPENDENCY_MISSING + 其他成功 Edge 仍 commit
  - 单元测试：重复 op_id → 标记为 duplicate_operation_id_skipped
- **状态**: [ ] 未开始
- **优先级**: P0（架构升级核心）

## Task 8: SyncErrorClass 枚举 + SyncOperationResult.error_class 字段
- **文件**: `backend/app/models/sync_models.py`
- **依赖**: 无（但 Task 7 依赖本 Task）
- **改动**:
  - 新增 `SyncErrorClass` 枚举：`VALIDATION_ERROR / DEPENDENCY_MISSING / TRANSIENT_ERROR`
  - `SyncOperationResult` 添加 `error_class: Optional[SyncErrorClass] = None` 字段
  - `SyncDependencyError` 自定义异常类（Task 7 会用）
- **验证**: 单元测试 — 序列化 SyncOperationResult 时 error_class 字段正确；Optional 字段对旧客户端透明
- **状态**: [ ] 未开始
- **优先级**: P0（Task 7 的前置）

## Task 9: 前端 sync-engine.ts 错误回流重试策略
- **文件**: `frontend/src/services/sync-engine.ts` + `frontend/src/services/dexie-db.ts`
- **依赖**: Task 8 (后端 error_class 字段)
- **改动**:
  - `dexie-db.ts` 版本升级：`sync_outbox` 增加 `permanentlyFailed: boolean`、`failureClass?: string`、`retryPriority?: number`、`nextRetryAt?: string`、`lastError?: string` 字段
  - Dexie version bump + upgrade 回调给现有条目填默认值（permanentlyFailed=false, retryPriority=0）
  - `sync-engine.ts` 处理 response.results 时按 error_class 分支：
    - `VALIDATION_ERROR`: 置 `permanentlyFailed=true`
    - `DEPENDENCY_MISSING`: 置 `retryPriority=1`（下轮优先发送）
    - `TRANSIENT_ERROR` / undefined: 置 `nextRetryAt = exponentialBackoff(retryCount)`
  - 下次 poll 时按 `retryPriority DESC, nextRetryAt ASC` 排序出队
  - `permanentlyFailed=true` 的条目跳过，不再进入 outbox 查询
- **验证**:
  - 单元测试：mock 后端返回 `error_class=VALIDATION_ERROR` → 对应条目 `permanentlyFailed=true`
  - 单元测试：mock 后端返回 `error_class=DEPENDENCY_MISSING` → 对应条目 `retryPriority=1`
  - 集成测试：后端返回 undefined `error_class`（兼容性）→ 前端走 default TRANSIENT 路径
  - Dexie migration 测试：旧数据库升级后新字段默认值正确
- **状态**: [ ] 未开始
- **优先级**: P0（Segment 提交的完整闭环）

## Task 6: 测试补充
- **文件**:
  - `backend/tests/unit/test_sync_segment_commit.py`（新建，覆盖 Task 7）
  - `backend/tests/unit/test_sync_error_class.py`（新建，覆盖 Task 8）
  - `backend/tests/unit/test_sync_payload_validation.py`（新建，覆盖 Task 3）
  - `backend/tests/unit/test_sync_http_error_classification.py`（新建，覆盖 Task 4）
  - `backend/tests/unit/test_neo4j_field_consistency.py`（新建，覆盖 Task 5）
  - `frontend/src/services/__tests__/sync-engine-error-class.test.ts`（新建，覆盖 Task 9）
- **改动**: 覆盖所有 Task 的单元测试 + 至少 1 个端到端集成测试（前端构造 payload → 后端 Segment 提交 → 前端接收 error_class 并按策略处理）
- **状态**: [ ] 未开始
- **优先级**: P1（收尾）

## 执行顺序

```
  ┌────────────────────────────────────────────────────┐
  │  Phase 1: 独立修复（可并行）                       │
  │  ├── Task 3: Payload 校验                          │
  │  ├── Task 4: HTTP 错误分类                         │
  │  ├── Task 5: r.score 字段对齐 + review_count       │
  │  └── Task 8: SyncErrorClass 枚举 + error_class 字段│
  ├────────────────────────────────────────────────────┤
  │  Phase 2: 架构升级（依赖 Phase 1 的 Task 3+8）     │
  │  └── Task 7: SyncService Segment 提交改造          │
  ├────────────────────────────────────────────────────┤
  │  Phase 3: 前端闭环（依赖 Task 7 的后端实现）       │
  │  └── Task 9: sync-engine.ts 错误回流 + Dexie 升级  │
  ├────────────────────────────────────────────────────┤
  │  Phase 4: 收尾                                     │
  │  └── Task 6: 测试补充（覆盖所有 Task）             │
  └────────────────────────────────────────────────────┘
```

**关键依赖**：
- Task 7 必须在 Task 3 + Task 8 完成后才能开始
- Task 9 必须在 Task 7 完成后才能开始（需要后端真实返回 error_class）
- Task 6 建议最后统一做，避免边写边改导致测试反复返工

**Commit 粒度建议**：
- Phase 1 的 4 个 Task 各自独立 commit（便于 revert）
- Task 7 单独一个 commit（架构核心变更）
- Task 9 的后端 commit 和前端 commit 建议分开（dexie-db.ts schema 升级单独一个 commit，sync-engine.ts 消费策略另一个 commit）
- Task 6 的测试可以按 Task 分批 commit，也可一次性
