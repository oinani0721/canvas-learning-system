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

## 不变量

- 前端 SyncEngine 不需要任何改动
- 前端 API 请求格式不变
- Neo4j 中已有的 CANVAS_EDGE 数据不受影响
- 其他服务（推荐系统读 CANVAS_EDGE）不受影响
