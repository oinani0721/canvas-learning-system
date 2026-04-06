# FR-KG-04 Sync 管道修复 — 任务清单

## Task 1: SyncService 拓扑排序 + 去重
- **文件**: `backend/app/services/sync_service.py`
- **改动**:
  - `process_sync_batch()` 中对 operations 按 entity_type 排序（见 design.md D1）
  - 按 operation_id 去重（重复的标记为 `duplicate_operation_id_skipped`）
- **验证**: 单元测试 — 乱序 batch 排序后 node 在 edge 前面；重复 op_id 被跳过
- **状态**: [ ] 未开始

## Task 2: _upsert_edge 显式失败检测
- **文件**: `backend/app/services/sync_service.py`
- **改动**:
  - `_upsert_edge()` 改用 OPTIONAL MATCH + 状态返回（见 design.md D2）
  - 签名添加 `subject_id` 参数
  - 缺节点时抛 ValueError 而非静默成功
- **验证**: 单元测试 — source 不存在 → ValueError + success=false
- **依赖**: 无（但 Task 1 的排序会减少此场景发生概率）
- **状态**: [ ] 未开始

## Task 3: SyncOperation payload 校验
- **文件**: `backend/app/models/sync_models.py`
- **改动**:
  - 添加 `model_validator` 校验 edge 的 source_node_id/target_node_id 必填
  - 添加 node content/title 长度上限
  - `operations` 字段添加 `max_length=500`
- **验证**: 单元测试 — 缺字段 → Pydantic ValidationError
- **状态**: [ ] 未开始

## Task 4: sync.py 错误分类
- **文件**: `backend/app/api/v1/endpoints/sync.py`
- **改动**:
  - 拆分 `except Exception` 为四层（ValueError→400, ServiceUnavailable→503, Neo4jError→500, Exception→500）
  - 移除 `str(e)[:200]` 泄露（503 只返回 "Neo4j unavailable"）
- **验证**: 手动测试 — 缺字段→400，关 Neo4j→503，正常→200
- **状态**: [ ] 未开始

## Task 5: Neo4jClient 字段一致性修复
- **文件**: `backend/app/clients/neo4j_client.py`
- **改动**:
  - `get_review_suggestions()` 的 `r.last_score` 改为 `r.score as last_score`（两处 query）
  - `create_learning_relationship()` 添加 `r.review_count = coalesce(r.review_count, 0) + 1`
- **验证**: 单元测试 — 查询返回的 last_score 非 null；review_count 递增
- **状态**: [ ] 未开始

## Task 6: 测试补充
- **文件**: `backend/tests/unit/test_sync_robustness.py`（新建）
- **改动**: 覆盖 Task 1-4 的单元测试
  - 乱序 batch 排序验证
  - operation_id 去重验证
  - edge 缺节点显式失败验证
  - payload 校验拒绝验证
  - 错误码分类验证
- **文件**: `backend/tests/unit/test_neo4j_field_consistency.py`（新建）
- **改动**: 覆盖 Task 5 的单元测试
  - score 字段别名验证
  - review_count 递增验证
- **状态**: [ ] 未开始

## 执行顺序

```
Task 3 (payload 校验)     ← 最独立，先做
Task 4 (错误分类)         ← 独立，可并行
Task 5 (字段一致性)       ← 独立，可并行
    │
    ▼
Task 1 (拓扑排序+去重)   ← 依赖 Task 3 的校验逻辑
Task 2 (显式失败)         ← 依赖 Task 1 的排序
    │
    ▼
Task 6 (测试)             ← 最后补全测试
```

Task 3/4/5 可并行执行，Task 1→2 串行，Task 6 收尾。
