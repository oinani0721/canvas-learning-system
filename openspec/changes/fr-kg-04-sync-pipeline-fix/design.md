# FR-KG-04 Sync 管道修复 — 设计方案

## 架构决策

### D1: 拓扑排序策略

**问题**：batch 中 edge 和 node 的顺序不确定，edge 先于 node 到达会导致静默失败。

**方案**：在 `process_sync_batch()` 中对 operations 排序：
- create/update: board(0) → node(1) → edge(2)
- delete: edge(0) → node(1) → board(2)

```python
def _sort_key(op: SyncOperation) -> tuple[int, int]:
    if op.operation in ("create", "update"):
        pri = {"board": 0, "node": 1, "edge": 2}.get(op.entity_type, 99)
        return (0, pri)
    # delete: reverse order
    pri = {"edge": 0, "node": 1, "board": 2}.get(op.entity_type, 99)
    return (1, pri)
```

**理由**：create 时先建容器再建关系；delete 时先删关系再删实体。与 Gemini 报告建议一致。

### D2: Edge 写入显式失败

**问题**：MATCH 找不到节点时不报错，但 MERGE 不执行。

**方案**：改用 OPTIONAL MATCH + 状态返回

```cypher
OPTIONAL MATCH (source:CanvasNode {id: $source_node_id})
OPTIONAL MATCH (target:CanvasNode {id: $target_node_id})
WITH source, target,
     CASE
       WHEN source IS NULL THEN 'missing_source'
       WHEN target IS NULL THEN 'missing_target'
       ELSE 'ok'
     END AS status
FOREACH (_ IN CASE WHEN status = 'ok' THEN [1] ELSE [] END |
    MERGE (source)-[e:CANVAS_EDGE {id: $entity_id}]->(target)
    SET e.label = $label,
        e.canvasId = $canvas_id,
        e.updatedAt = $timestamp
    ON CREATE SET e.createdAt = $timestamp
)
RETURN status
```

当 `status != 'ok'` 时抛出 `ValueError`，让上层标记 `success=False`。

**理由**：保留 MERGE 幂等性，同时让失败可见。拓扑排序已经大幅减少此场景，但作为防御性编程仍需保留。

### D3: 字段名对齐方向

**问题**：写 `r.score`，读 `r.last_score`。

**方案**：读侧改为 `r.score as last_score`（改读不改写）。

**理由**：
- 写侧 `r.score` 语义更清晰
- 读侧只需改 Cypher alias，对外 API 无影响
- 同时添加 `r.review_count = coalesce(r.review_count, 0) + 1`

### D4: 错误分类

**方案**：sync.py 的 except 拆分为四层：

```python
except ValueError as e:
    # 输入校验失败 → 400
except (ServiceUnavailable, AuthError, ConnectionError) as e:
    # Neo4j 不可用 → 503，不泄露细节
except Neo4jError as e:
    # Neo4j 查询错误 → 500，不泄露细节
except Exception as e:
    # 未知错误 → 500，不泄露细节
```

### D5: Payload 校验

**方案**：在 `SyncOperation` Pydantic model 中添加 `model_validator`：
- edge 的 create/update 必须有 `source_node_id`/`sourceNodeId` 和 `target_node_id`/`targetNodeId`
- 支持 snake_case 和 camelCase 两种格式（兼容前端）
- node content 上限 20000 字符
- edge label 上限 2000 字符
- 批次上限 `max_length=500`

## 数据流变化

```
  修复前：
  
  batch [edge, node, node] → 按顺序执行 → edge 静默失败 → 报告 success
  
  修复后：
  
  batch [edge, node, node]
    │
    ▼ 拓扑排序
  [node, node, edge]
    │
    ▼ 按顺序执行
  node ✅ → node ✅ → edge ✅（节点已存在）
    │
    ▼ 如果仍然失败（极端情况）
  edge → OPTIONAL MATCH → status='missing_source' → ValueError → success=false
```

## 2026-04-06 架构升级：D6 + D7

### D6: Segment 原子提交架构

**问题**：Story 1.5 AC-7 的"部分提交"（单事务 + `if synced > 0: tx.commit()`）在依赖场景下会放大不一致。例如 batch = [node_A 失败, edge_A→B 成功]，旧逻辑会 commit 一个孤边，但 node_A 永远缺失。D1 的拓扑排序只能保证**顺序**，不能保证**依赖失败时后续不再提交**。

**方案**：把单事务按实体类型拆为 3 个独立 Segment，每段有自己的原子规则：

```python
async def process_sync_batch(self, request: SyncBatchRequest) -> SyncBatchResponse:
    # Step 1: 预处理 —— 去重 + Pydantic 校验（Task 3 + Task 8）
    ops = _deduplicate_by_operation_id(request.operations)

    # Step 2: 分段（替代 D1 的 sort_key，更结构化）
    segments = _partition_by_entity_type(ops, request.operation)
    # create: [board_segment, node_segment, edge_segment]
    # delete: [edge_segment, node_segment, board_segment]  (逆序)

    results: list[SyncOperationResult] = []

    # Step 3: 按段执行
    for idx, segment in enumerate(segments):
        is_edge_segment = (idx == 2 and request.operation != "delete") \
                       or (idx == 0 and request.operation == "delete")

        async with session.begin_transaction() as tx:
            segment_results = []
            segment_all_ok = True

            for op in segment:
                try:
                    await self._execute_operation(tx, op, ...)
                    segment_results.append(SyncOperationResult(
                        operation_id=op.operation_id, success=True
                    ))
                except SyncDependencyError as e:
                    # 端点缺失等依赖问题
                    segment_results.append(SyncOperationResult(
                        operation_id=op.operation_id,
                        success=False,
                        error_class=SyncErrorClass.DEPENDENCY_MISSING,
                        error=str(e)[:200],
                    ))
                    segment_all_ok = False
                except (ValueError, ValidationError) as e:
                    segment_results.append(SyncOperationResult(
                        operation_id=op.operation_id,
                        success=False,
                        error_class=SyncErrorClass.VALIDATION_ERROR,
                        error=str(e)[:200],
                    ))
                    segment_all_ok = False
                except (RuntimeError, ConnectionError, Neo4jError) as e:
                    segment_results.append(SyncOperationResult(
                        operation_id=op.operation_id,
                        success=False,
                        error_class=SyncErrorClass.TRANSIENT_ERROR,
                        error="Neo4j transient error",
                    ))
                    segment_all_ok = False

            # Segment 原子性规则
            if is_edge_segment:
                # Edge 段：允许部分失败，只要至少一个成功就 commit
                if any(r.success for r in segment_results):
                    await tx.commit()
                else:
                    await tx.rollback()
            else:
                # Board/Node 段：严格原子，任一失败即 rollback
                if segment_all_ok:
                    await tx.commit()
                else:
                    await tx.rollback()
                    results.extend(segment_results)
                    # 后续段全部标记为 DEPENDENCY_MISSING
                    remaining = [o for s in segments[idx+1:] for o in s]
                    for op in remaining:
                        results.append(SyncOperationResult(
                            operation_id=op.operation_id,
                            success=False,
                            error_class=SyncErrorClass.DEPENDENCY_MISSING,
                            error="previous segment failed",
                        ))
                    return SyncBatchResponse(results=results, ...)

            results.extend(segment_results)

    return SyncBatchResponse(results=results, ...)
```

**关键设计点**：
1. **D1 拓扑排序被 D6 的分段吸收**——不再需要独立的 `_sort_key` 函数，分段本身就是按实体类型拆
2. **D2 的 OPTIONAL MATCH + status 返回仍然保留**，作为 Segment 3 内 per-op fail fast 的实现细节
3. **Delete 逆序**是 segment 列表的构造规则，不是每个 op 的 sort key
4. **Segment 失败的"冒泡"**：Board 段失败会把 Node 和 Edge 段都标记为 DEPENDENCY_MISSING 返回，让前端明确知道"这批次要整个重试"
5. **Edge 段的容忍性**：原 AC-7 的"只要成功过就 commit"只在 Edge 段保留，因为边是叶子级操作，一条边失败不应阻止其他独立边成功

**理由**：
- Neo4j 官方文档建议避免大事务（内存压力），Segment 拆分天然符合
- 依赖感知提交消除了"孤边"问题，前端能立即看到"因为 Node 失败所以 Edge 没做"
- 保留 Edge 段的 AC-7 语义是对 Story 1.5 的尊重——画布是高频操作流，Edge 的偶发失败不应让整批回滚

### D7: SyncErrorClass 错误分类枚举

**问题**：D4 只做了 HTTP 状态码层面的错误分类（400/500/503），但 per-operation 失败原因仍是自由文本。前端 sync-engine.ts 无法据此决定"这个条目应该永久失败 / 优先重试 / 指数退避"。

**方案**：引入 3 值枚举，附加到 `SyncOperationResult` 结构：

```python
# backend/app/models/sync_models.py
from enum import Enum

class SyncErrorClass(str, Enum):
    VALIDATION_ERROR = "VALIDATION_ERROR"      # payload 本身不对，重试无用
    DEPENDENCY_MISSING = "DEPENDENCY_MISSING"  # 依赖的实体缺失，重试可能有用
    TRANSIENT_ERROR = "TRANSIENT_ERROR"        # Neo4j 网络/锁等，重试大概率有用

class SyncOperationResult(BaseModel):
    operation_id: str
    success: bool
    error_class: Optional[SyncErrorClass] = None  # 仅 success=False 时有值
    error: Optional[str] = None                    # 截断后的人类可读消息
```

**前端消费策略（sync-engine.ts）**：

```typescript
// 根据 error_class 决定 outbox 条目的下一步命运
for (const result of response.results) {
  const entry = findOutboxEntryByOpId(result.operationId);
  if (!entry) continue;

  if (result.success) {
    await db.sync_outbox.update(entry.id!, { syncedAt: new Date().toISOString() });
    continue;
  }

  switch (result.errorClass) {
    case 'VALIDATION_ERROR':
      // 永久失败：payload 有问题，重试无用
      await db.sync_outbox.update(entry.id!, {
        permanentlyFailed: true,
        failureClass: result.errorClass,
        lastError: result.error,
      });
      break;
    case 'DEPENDENCY_MISSING':
      // 保留在 outbox，下次同步时提升优先级（优先发送 Node/Board 段）
      await db.sync_outbox.update(entry.id!, {
        failureClass: result.errorClass,
        retryPriority: 1, // 默认 0，1 表示优先
      });
      break;
    case 'TRANSIENT_ERROR':
    default:
      // 正常指数退避重试
      await db.sync_outbox.update(entry.id!, {
        failureClass: result.errorClass,
        nextRetryAt: computeExponentialBackoff(entry.retryCount),
      });
      break;
  }
}
```

**Dexie schema 升级**（`dexie-db.ts`）：

```typescript
db.version(NEXT_VERSION).stores({
  sync_outbox: '++id, entityType, entityId, operation, syncedAt, permanentlyFailed, retryPriority, nextRetryAt',
}).upgrade(async (tx) => {
  // 现有条目默认值：permanentlyFailed=false, retryPriority=0, nextRetryAt=null
});
```

**理由**：
- 3 值是最小必要分类：re-try 取决于"是谁的锅"——payload / 上游 / 基础设施
- 枚举而非 HTTP 状态码：HTTP 是 batch 层面的结果，需要 per-operation 粒度
- 前端降级兼容：若后端返回 undefined `error_class`，前端 switch 走 default 即 TRANSIENT 路径，保持原行为
- Dexie 升级走标准 version bump，upgrade 回调给现有条目填默认值

## 不变量

- 前端 API 请求格式不变（字段名仍 camelCase）
- ~~前端 SyncEngine 不需要任何改动~~ ← **2026-04-06 修订：Task 9 引入前端错误回流，此不变量被打破**
- Neo4j 中已有的 CANVAS_EDGE 数据不受影响
- 其他服务（推荐系统读 CANVAS_EDGE）不受影响
- Story 1.5 AC-7 的"部分提交"精神仅在 Edge 段保留（D6）
