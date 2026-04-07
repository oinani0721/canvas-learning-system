## Context

FR-KG-04 是 Canvas Learning System 的一个关键批注集，追踪从 Neo4j 图谱到验证评分服务的"三层图谱"断裂问题。本次变更源于用户提供的 3 份独立研究材料（项目内 FR-KG-04 批注 + deep-research-report-2 + ChatGPT Report 2）与 4 轮代码对抗性核实的综合结论。

**关键背景（Meta-lesson）**：两份独立的深度研究报告都基于**过时代码快照**展开分析，共同提议修复的 A10（RAG 字段契约错位）和 A2/A5（Schema 断裂查询）**已经在 `verification_service.py` 被早期修复**（代码中有 `# FR-KG-04 fix:` 注释为证）。这意味着按报告照搬修复会引入**双重转换层**（double adapter），造成二阶故障。更严重的是，报告都漏掉了真正的 P0 bug：`_get_kg_relevance` 的 Cypher 查询字段（`{uuid}` + `canvas_id`）与 `SyncService` 的写入字段（`{id}` + `canvasId`）完全不匹配，导致 KG 相关性信号**永远返回默认值 0.5**，30% 的考试优先级权重完全失效，而且不抛异常、无日志、无 UI 告警——这是教科书级的 silent degradation。

**当前状态**：
- `backend/app/services/sync_service.py` 写入 `CanvasNode {id, canvasId}`（camelCase）
- `backend/app/services/recommendation_service.py` 查询 `{canvasId}` ✅ 与写入一致，正常工作
- `backend/app/services/question_generator.py:673,751` 查询 `{uuid}` + `canvas_id` ❌ 永远查空
- `backend/app/services/exam_service_ext.py:67,100-101` 写入 `{uuid}` ❌ 第三套幽灵 schema
- `backend/app/api/v1/endpoints/sync.py:37` 完全无鉴权
- `backend/app/services/sync_service.py:238-254` `_upsert_edge` 无 `RETURN`，静默 no-op
- `backend/app/middleware/prompt_injection_guard.py:78-92` `PromptTemplate.build()` 的 `context` 参数完全不扫注入

## Goals / Non-Goals

**Goals:**
- 统一 `CanvasNode` 节点的 Neo4j schema 到 `{id}` + `canvasId`（SyncService 是 source of truth）
- 让 `kg_relevance` 在生产中返回实际计算值而非恒定 0.5
- 升级 `kg_relevance` 公式到 `CANVAS_EDGE + RELATES_TO` 加权融合
- 为 `/sync/batch` 添加设备级 API Key 鉴权，防止未授权客户端污染图数据
- 消除 `_upsert_edge` 的静默 no-op，让 source/target 缺失时抛错
- 对 batch ops 做依赖拓扑排序，确保 `board → node → edge` 顺序
- 修复异常分类错误，停止将逻辑 bug 伪装成 "Neo4j unreachable"
- 扩展 prompt injection 防护到检索上下文，关闭间接注入攻击面
- 删除 `CONNECTS_TO` 写入死代码，简化三层图谱为两层（`CANVAS_EDGE` 用户画线 + `RELATES_TO` Graphiti 抽取）
- 建立 RAGAS 离线回归防止契约漂移复发

**Non-Goals:**
- 不做 `kg_relevance` 时间衰减（延后到下一迭代，依赖 FSRS `last_review` 数据成熟度）
- 不做 JWT/OAuth2 鉴权升级（Tauri 本机部署，API Key 足够）
- 不统一 Canvas 主键为单键（保留 `canvas_id` UUID + `canvas_name` 双键，用联合唯一约束收敛风险）
- 不做 Graphiti `RELATES_TO` 的数据质量评估（依赖 RAGAS 管线建设完成后另立变更）
- 不做前端 Outbox 的 operation_id 持久化去重（当前 side effects 未集成，MERGE 数据级幂等已足够；待 Graphiti/event bus 集成时升级）
- 不重新激活 `CONNECTS_TO`（绕过已经完成，成本 > 收益）
- 不修改 `verification_service.py:1832-1947`（`# FR-KG-04 fix:` 已处理 A10/A2/A5，严禁双重转换）

## Decisions

### D1 Schema 统一方向：`{id}` 而非 `{uuid}`

**选择**：`exam_service_ext.py:67` 改为 `MERGE (n:CanvasNode {id: $node_id})`；`question_generator.py:673,751` 改为 `MATCH (n:CanvasNode {id: $node_id})` + `WHERE neighbor.canvasId = $canvas_id`。

**理由**：SyncService 是前端同步的 source of truth，写入频率远高于 `exam_service_ext`。统一到 `{id}` + `canvasId` 最少破坏现有数据。`recommendation_service.py` 已经用这套 schema 正常工作，验证了方向正确性。

**替代方案**：
- ❌ 让 SyncService 改为 `{uuid}` — 会破坏 `recommendation_service.py` 和所有前端同步历史数据
- ❌ 保留双 schema 并添加桥接层 — 增加复杂度，违反 KISS，且无法解决 silent degradation

### D2 `kg_relevance` 公式升级

**选择**：
```
MATCH (n:CanvasNode {id: $node_id})-[r:CANVAS_EDGE|RELATES_TO]-(neighbor:CanvasNode)
WHERE neighbor.canvasId = $canvas_id
RETURN 
  SUM(CASE type(r) 
      WHEN 'CANVAS_EDGE' THEN 1.0 
      WHEN 'RELATES_TO' THEN 0.7 
      ELSE 0 END) AS weighted_degree,
  COUNT(neighbor) AS neighbor_count
```
归一化：`min(1.0, weighted_degree / 8.0)`

**理由**：
- 用户画线（CANVAS_EDGE）是**显式意图**，权重最高 = 1.0
- Graphiti 抽取的关系（RELATES_TO）是**推断**，权重 0.7
- 归一化除数 8.0 对应"8 个强连接达到满分"的直觉
- 空图结果返回 `(0.5, degraded_reason="empty_graph")` 而非静默 0.5

**替代方案**：
- ❌ 仅用 CANVAS_EDGE（保守方案）— 会忽略 Graphiti 发现的隐含关系
- ❌ 加入 2-hop 邻居 — 需要节点预算控制，延后到下一迭代
- ❌ 加入 mastery gap × time_decay — 依赖 FSRS 数据成熟度

### D3 鉴权方案：设备级 API Key

**选择**：`X-CLS-Internal-Key` header，配合 `INTERNAL_API_KEY` 环境变量。

**Fail-closed 策略**：
| DEBUG | KEY 配置 | 行为 |
|-------|----------|------|
| True  | 空       | 警告放行（开发便利） |
| True  | 非空     | 严格校验 |
| False | 空       | **503 fail-closed**（防生产裸奔） |
| False | 非空     | 严格校验 |

**理由**：Tauri 本机部署场景下，localhost 是隐式信任边界。JWT/OAuth2 过度设计；mTLS 部署复杂；API Key 在 FastAPI 官方 Security 文档中有一等公民支持（`APIKeyHeader`）。

**替代方案**：
- ❌ JWT — 需要用户账号体系，与 MVP 本机定位不符
- ❌ mTLS — 证书管理复杂度高，不适合桌面应用
- ❌ IP allowlist — Tauri sidecar 的 IP 不稳定

### D4 Batch Ops 拓扑排序

**选择**：引入 `_operation_sort_key` 静态方法，排序规则：

```
优先级: (op_order, entity_order)
  create/update:
    board  → node  → edge
    (0,0)  (0,1)   (0,2)
  delete:
    edge   → node  → board
    (1,0)  (1,1)   (1,2)
```

**理由**：`_upsert_edge` 依赖 source/target 节点已存在。原始实现按前端提交顺序执行，前端 Outbox 可能因重试/乱序导致 `edge` 先于 `node` 到达。稳定排序消除这个时序 bug。删除操作反向排序：先删边再删点，避免 DETACH DELETE 意外级联。

### D5 CONNECTS_TO 弃用策略

**选择**：
1. **Step 1 grep 证据**：仓库全搜 `CONNECTS_TO` 和 `_sync_edge_to_neo4j`，证明除 `canvas_service.py` 的写入和已绕过的 verification 查询外无其他读写路径
2. **Step 2 标注弃用**：在 `canvas_service._sync_edge_to_neo4j` 中加 `# DEPRECATED v0.X.Y: will be removed in v0.(X+1).0` 注释
3. **Step 3 删除**：下一个 minor 版本删除代码和相关死测试

**理由**：verification_service 已经用 `# FR-KG-04 fix:` 绕过了 `CONNECTS_TO`；重新激活的工程成本（双写 + 一致性保证）远高于收益（零消费）。语义边的表达归并到 Graphiti 的 `RELATES_TO` 抽取能力。

### D6 Prompt Injection 扫描扩展

**选择**：在 3 个注入点加 `check_input(context)` 校验：
1. `claude_client.py:247` — `system_prompt = f"...{context}"` 前
2. `gemini_client.py:441` — 相同位置
3. `context_enrichment_service._format_learning_context` — 在返回格式化 chunks 前

**降级策略**：扫描命中时不是 raise，而是返回 `{context: "[filtered: suspicious content detected]", degraded_reason: "prompt_injection_risk"}`。这样保证业务连续性，同时留下可观测性。

**理由**：OWASP GenAI Top 10 将 Prompt Injection 列为首要风险，特别强调外部内容（检索片段、上传文件、网页抓取）应视为**不可信输入**。当前 `check_input` 只扫 user_prompt，属于典型的"信任边界画错位置"——把 RAG 结果当作可信来源。

### D7 Dependency-Aware Segment Commit（2026-04-07 吸收自 sync-pipeline-fix）

**问题**：原 D4 拓扑排序只解决"顺序"，不解决"依赖失败时后续是否应该停止"。例如 batch = `[node_A 失败, edge_A→B 成功]`，D4 会按 node → edge 顺序执行，但在单事务 + "部分提交"语义下，最终会 commit 一个孤边（node 失败，edge 成功），数据不一致。

**方案**：把 `process_sync_batch` 的单事务按实体类型拆为 3 个独立 Segment，每段有自己的原子规则：

```python
async def process_sync_batch(self, request: SyncBatchRequest) -> SyncBatchResponse:
    # Step 1: 预处理 —— 去重 + Pydantic 校验
    ops = _deduplicate_by_operation_id(request.operations)

    # Step 2: 分段（天然包含 D4 的拓扑排序）
    segments = _partition_by_entity_type(ops, request.operation)
    # create/update: [board_segment, node_segment, edge_segment]
    # delete:        [edge_segment, node_segment, board_segment]

    results: list[SyncOperationResult] = []

    # Step 3: 按段执行
    for idx, segment in enumerate(segments):
        is_edge_segment = _is_edge_segment(idx, request.operation)

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
                    segment_results.append(SyncOperationResult(
                        operation_id=op.operation_id, success=False,
                        error_class=SyncErrorClass.DEPENDENCY_MISSING,
                        error=str(e)[:200],
                    ))
                    segment_all_ok = False
                except (ValueError, ValidationError) as e:
                    segment_results.append(SyncOperationResult(
                        operation_id=op.operation_id, success=False,
                        error_class=SyncErrorClass.VALIDATION_ERROR,
                        error=str(e)[:200],
                    ))
                    segment_all_ok = False
                except (RuntimeError, ConnectionError, Neo4jError) as e:
                    segment_results.append(SyncOperationResult(
                        operation_id=op.operation_id, success=False,
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
                # Board/Node 段：严格原子，任一失败即 rollback + 后续段标 DEPENDENCY_MISSING
                if segment_all_ok:
                    await tx.commit()
                else:
                    await tx.rollback()
                    results.extend(segment_results)
                    remaining = [o for s in segments[idx+1:] for o in s]
                    for op in remaining:
                        results.append(SyncOperationResult(
                            operation_id=op.operation_id, success=False,
                            error_class=SyncErrorClass.DEPENDENCY_MISSING,
                            error="previous segment failed",
                        ))
                    return SyncBatchResponse(results=results, ...)

            results.extend(segment_results)

    return SyncBatchResponse(results=results, ...)
```

**关键设计点**：
1. **D4 拓扑排序被 D7 的分段吸收** — 不再需要独立的 `_operation_sort_key` 函数，分段本身就是按实体类型拆
2. **D3 的 OPTIONAL MATCH + status 返回仍保留**（下沉到 `_upsert_edge` 内部），作为 Segment 3 内 per-op fail fast 的实现细节
3. **Delete 逆序**是 segment 列表的构造规则，不是每个 op 的 sort key
4. **Segment 失败的"冒泡"**：Board 段失败会把 Node 和 Edge 段都标记为 DEPENDENCY_MISSING 返回，前端明确知道"这批次要整个重试"
5. **Edge 段的容忍性**：原"部分提交"语义只在 Edge 段保留，因为边是叶子级操作

**理由**：
- Neo4j 官方文档建议避免大事务（内存压力），Segment 拆分天然符合
- 依赖感知提交消除了"孤边"问题，前端能立即看到"因为 Node 失败所以 Edge 没做"
- 保留 Edge 段的容忍性是对 Story 1.5 AC-7 精神的尊重——画布是高频操作流

**替代方案**：
- ❌ D4 单事务拓扑排序 + `except Exception` per-op 隔离 — 会在依赖失败时产生孤边
- ❌ 全原子 —— 任一失败整批回滚 —— 体验差，高频 edge 抖动会导致整批返工
- ❌ Saga 模式 — 过度设计，Tauri 本机场景不需要分布式事务

### D8 SyncErrorClass per-op 错误分类（2026-04-07 吸收自 sync-pipeline-fix）

**问题**：D7 Segment Commit 产生 per-operation 失败原因，但若以自由文本返回，前端 sync-engine.ts 无法据此决定"永久失败 / 优先重试 / 指数退避"。

**方案**：引入 3 值枚举，附加到 `SyncOperationResult`：

```python
# backend/app/models/sync_models.py
from enum import Enum

class SyncErrorClass(str, Enum):
    VALIDATION_ERROR = "VALIDATION_ERROR"      # payload 本身不对，重试无用
    DEPENDENCY_MISSING = "DEPENDENCY_MISSING"  # 依赖实体缺失，重试可能有用
    TRANSIENT_ERROR = "TRANSIENT_ERROR"        # Neo4j 网络/锁，重试大概率有用

class SyncOperationResult(BaseModel):
    operation_id: str
    success: bool
    error_class: Optional[SyncErrorClass] = None  # 仅 success=False 时有值
    error: Optional[str] = None                    # 截断后的人类可读消息

class SyncDependencyError(Exception):
    """Raised when an operation depends on an entity that is missing or failed upstream."""
```

**理由**：
- 3 值是最小必要分类：重试取决于"是谁的锅"——payload / 上游 / 基础设施
- 枚举而非 HTTP 状态码：HTTP 是 batch 层面的结果，需要 per-operation 粒度
- 前端降级兼容：若后端返回 undefined `error_class`，前端 switch 走 default 即 TRANSIENT 路径
- 与 D7 Segment Commit 严密配对：Segment 失败冒泡依赖 DEPENDENCY_MISSING

### D9 前端错误回流 + Outbox Schema 扩展（2026-04-07 吸收自 sync-pipeline-fix）

**问题**：sync-engine.ts 原有逻辑在 batch 部分失败时可能错误地把所有 entry 标记为 synced（silent data loss）。而且 outbox 没有持久化的失败原因字段，每次重试无法判断"这条是否应该永久放弃"。

**方案**：

**前端消费策略（sync-engine.ts）**：

```typescript
for (const result of response.results) {
  const entry = findOutboxEntryByOpId(result.operationId);
  if (!entry) continue;

  if (result.success) {
    await db.sync_outbox.update(entry.id!, { syncedAt: new Date().toISOString() });
    continue;
  }

  switch (result.errorClass) {
    case 'VALIDATION_ERROR':
      await db.sync_outbox.update(entry.id!, {
        permanentlyFailed: true,
        failureClass: result.errorClass,
        lastError: result.error,
      });
      break;
    case 'DEPENDENCY_MISSING':
      await db.sync_outbox.update(entry.id!, {
        failureClass: result.errorClass,
        retryPriority: 1, // 默认 0，1 表示优先
      });
      break;
    case 'TRANSIENT_ERROR':
    default:
      await db.sync_outbox.update(entry.id!, {
        failureClass: result.errorClass,
        nextRetryAt: computeExponentialBackoff(entry.retryCount),
      });
      break;
  }
}
```

**Dexie schema 升级（dexie-db.ts）**：

```typescript
db.version(NEXT_VERSION).stores({
  sync_outbox: '++id, entityType, entityId, operation, syncedAt, permanentlyFailed, retryPriority, nextRetryAt',
}).upgrade(async (tx) => {
  // 现有条目默认值：permanentlyFailed=false, retryPriority=0, nextRetryAt=null
});
```

**CanvasId 强制校验（Patch-4 微补）**：

```typescript
// sync-engine.ts sendBatch()
const canvasId =
  (entry.payload.canvasId as string) ??
  (entry.payload.canvas_id as string);
if (!canvasId) {
  console.warn('[SyncEngine] Outbox entry missing canvasId, skipping', entry.id);
  continue;  // 不再 fallback 到 'default'
}
```

**理由**：
- VALIDATION_ERROR 永远不会因为重试变好，必须 mark permanent
- DEPENDENCY_MISSING 需要等上游节点同步后才能重试，提升优先级让下一轮优先发送
- TRANSIENT_ERROR 走指数退避（Wave 1 已有基础实现）
- `'default'` fallback 在 Wave 1 修了上游后实际不会触发，但删除它消除隐患（防御性编程）

**替代方案**：
- ❌ 保留 `'default'` fallback 作为"最后防线"——理论上可能触发，实际上 Wave 1 已覆盖所有路径，保留它只会降低问题可观测性

## Risks / Trade-offs

| 风险 | 影响 | 缓解 |
|------|------|------|
| **Schema 迁移破坏历史数据** | `{uuid}` 节点在新 schema 下变成孤儿 | 提供反向迁移脚本；发布前 dry-run 统计 `MATCH (n:CanvasNode) WHERE n.uuid IS NOT NULL RETURN count(n)` |
| **API Key 前端忘配** | 所有 sync 调用 403 | 前端启动时检测 `VITE_INTERNAL_API_KEY`，未配置时在控制台警告 + Tauri 配置向导 |
| **Edge no-op 变成 edge failure** | 历史"看似成功"的 edge 现在抛错 | 回归测试覆盖正常路径；若影响面大，用 feature flag `STRICT_EDGE_VALIDATION` 逐步开启 |
| **拓扑排序改变 batch 执行顺序** | 可能破坏某些依赖前端顺序的隐含契约 | 单元测试覆盖各种 ops 组合；集成测试验证端到端结果一致 |
| **Context 注入扫描增加延迟** | 每次 RAG 调用额外 ~5-10ms | 基准测试证明延迟可接受（check_input 是纯正则） |
| **CONNECTS_TO 删除影响未发现的消费者** | 隐藏依赖失效 | 弃用窗口 1 个 minor 版本；保留带 DEPRECATED 注释的代码作为"刹车" |
| **RAGAS 阈值 0.7 过严/过松** | CI 阻塞或遗漏回归 | 初始阈值设为观察模式，收集 1 周数据后正式启用阻断 |

### Meta-risk: 研究报告过时陷阱

这次变更本身的**元教训**是：基于文件快照的外部研究（即使是 deep research 级别）会系统性漏掉"代码中已有的修复"。两份独立 ChatGPT 报告都提议修复已经修完的 A10 问题，如果按报告照搬，会引入双重转换层。

**预防措施写入本 spec**：
- **代码引用必须独立 Agent 对抗性审查**（CLAUDE.md 已有规则）
- **修改前必须 grep 自己将要改的关键字**（本次发现 `# FR-KG-04 fix:` 注释的方法）
- **多份报告的"高共识"不等于"代码真相"**——共识可能来自共同的过时输入

## Migration Plan

### Phase 1 — Schema 统一（Week 1 Day 1）

1. Dry-run 盘点：`MATCH (n:CanvasNode) WHERE n.uuid IS NOT NULL RETURN count(n)`
2. 数据迁移脚本：`MATCH (n:CanvasNode) WHERE n.uuid IS NOT NULL SET n.id = n.uuid REMOVE n.uuid`（在测试数据库先跑）
3. 修改 `exam_service_ext.py:67,100-101` 和 `question_generator.py:673,751`
4. 补单元测试：真实数据路径验证 `kg_relevance` 返回非 0.5

### Phase 2 — 鉴权（Week 1 Day 2）

1. 新建 `backend/app/security.py` + `require_internal_api_key` 依赖
2. `backend/app/config.py` 添加 `INTERNAL_API_KEY` Settings 字段
3. `sync.py:37` 添加 `Depends(require_internal_api_key)`
4. 前端 `api-client.ts` 添加 `X-CLS-Internal-Key` header 注入
5. 前端启动时检查 `VITE_INTERNAL_API_KEY` 配置，未配置时警告
6. `backend/tests/conftest.py` 注入 `INTERNAL_API_KEY="test-internal-key"`

### Phase 3 — Edge 一致性（Week 1 Day 3）

1. `_upsert_edge` 添加 `RETURN e.id`，`result.single() is None` 时抛 `RuntimeError`
2. 引入 `_operation_sort_key` 拓扑排序
3. `except (RuntimeError, ConnectionError)` 扩展为 `except Exception`（per-op 级）

### Phase 4 — 异常分类 + Neo4j 约束（Week 1 Day 4）

1. `sync.py:57-66` 拆分异常分类
2. 新建 `backend/migrations/001_canvas_constraints.cypher`
3. 启动时自动执行约束迁移脚本

### Phase 5 — kg_relevance 加权（Week 2 Day 1-2）

1. `question_generator._get_kg_relevance` 改写 Cypher 为加权公式
2. 归一化与 degraded_reason 返回
3. NodePriority 模型添加 `kg_relevance_degraded` 字段

### Phase 6 — CONNECTS_TO 弃用（Week 2 Day 3）

1. 全仓 grep `CONNECTS_TO`，形成"零消费"证据
2. `canvas_service._sync_edge_to_neo4j` 加 DEPRECATED 注释
3. 文档 `docs/known-gotchas.md` 标记 G-FAKE-XX

### Phase 7 — 唯一约束 + 数据迁移（Week 2 Day 4-5）

1. `(subjectId, name)` 联合唯一约束迁移脚本
2. 冲突检测脚本：`MATCH (b1:CanvasBoard), (b2:CanvasBoard) WHERE b1.subjectId = b2.subjectId AND b1.name = b2.name AND id(b1) < id(b2) RETURN b1, b2`

### Phase 8 — Context 注入扫描（Week 3 Day 1-2）

1. `context_enrichment_service._format_learning_context` 添加扫描
2. `claude_client.py:247`、`gemini_client.py:441` 添加扫描
3. 新增 `test_prompt_injection_context.py` 回归测试

### Phase 9 — RAGAS 离线评估（Week 3 Day 3-5）

1. 添加 `ragas` 依赖到 `requirements-dev.txt`
2. 建立评估集 `backend/tests/regression/ragas_eval/fixtures/`
3. CI gate 脚本：`faithfulness < 0.7` 阻断
4. 初始运行在观察模式，收集 1 周 baseline 后启用阻断

### Phase 11 — Segment Commit 架构升级（Week 1 Day 3-4，与 Phase 3 合并执行）

1. 引入 `SyncDependencyError` 自定义异常类
2. 引入 `_deduplicate_by_operation_id` 辅助函数
3. 引入 `_partition_by_entity_type` 辅助函数
4. 改写 `process_sync_batch` 为 3 段独立事务结构（见 D7 代码）
5. `_upsert_edge` 改用 OPTIONAL MATCH + status 返回（承接 Phase 3 的 fail fast）
6. 单元测试：构造 [edge, node] 乱序 → 验证 edge 在 Segment 3 成功
7. 单元测试：Segment 2 Node 失败 → Segment 3 标 DEPENDENCY_MISSING

### Phase 12 — SyncErrorClass + 前端错误回流（Week 2 Day 3-4）

1. `sync_models.py` 新增 `SyncErrorClass` 枚举 + `SyncOperationResult.error_class` 字段
2. `sync_service.py` 的各 exception handler 设置对应的 error_class
3. `frontend/src/services/dexie-db.ts` version bump + `sync_outbox` 新字段
4. `frontend/src/services/sync-engine.ts` 按 error_class 分支处理失败 entry
5. 前端单元测试：mock 后端返回 VALIDATION_ERROR → entry `permanentlyFailed=true`
6. 集成测试：前后端 error_class 端到端传递

### Phase 13 — Payload Pydantic 校验（Week 1 Day 4，与 Phase 11 并行）

1. `sync_models.py` 给 `SyncOperation` 和 `SyncBatchRequest` 加 `model_validator`
2. Edge create/update 必须有 source/target（camelCase 和 snake_case 双兼容）
3. Node content ≤ 20000 字符、edge label ≤ 2000 字符
4. `operations` 列表 max_length=500
5. 单元测试：缺字段 → ValidationError；超长 → ValidationError；超批次 → ValidationError

### Phase 14 — 前端 canvasId fallback 删除（Week 2 Day 4，与 Phase 12 并行）

1. `frontend/src/services/sync-engine.ts` 的 `sendBatch` 中删除 `?? 'default'` fallback
2. 改为 console.warn + continue（entry 保留在 outbox 不发送）
3. 前端单元测试：构造一条无 canvasId 的 outbox entry → 验证未进入任何 canvas group

### Phase 15 — Learning relationship 字段一致性（Week 1 Day 2，与 Phase 2 并行）

1. `neo4j_client.py` 的 `get_review_suggestions` Cypher 改为 `RETURN r.score AS last_score`
2. `create_learning_relationship` 在 Cypher 中加 `SET r.review_count = coalesce(r.review_count, 0) + 1`
3. 单元测试：写入 → 读取，`last_score` 非 null
4. 单元测试：三次 scoring → `review_count = 3`

## Open Questions

1. **`kg_relevance` 归一化除数 8.0 是否合理？** 需要在真实数据上跑一次分布统计，看节点度数的 p50/p95，再决定是否调整
2. **历史 `{uuid}` 节点的规模？** Phase 1 的 dry-run 会给出答案。如果规模很小（<10 条），可以手工迁移；如果规模大（>100 条），需要写正式迁移脚本
3. **RAGAS 评估集的数据来源？** 是否复用现有的用户学习对话日志？还是需要人工标注新集？
4. **`operation_id` 持久化去重是否应该提前到本次变更？** 当前判断是"延后"，因为 side effects 未集成。如果 Week 1 发现 Graphiti 事件已经开始触发副作用，需要升级到 P1
5. **Frontend Tauri 配置向导如何引导用户设置 API Key？** 用户体验上是否需要"首次启动自动生成"还是"强制用户手动输入"？
