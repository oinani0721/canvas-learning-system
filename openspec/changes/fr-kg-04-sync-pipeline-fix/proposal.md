# FR-KG-04 Sync 管道修复 — 静默失败 + 字段一致性 + 错误分类

## Why

### 问题

FR-KG-04（节点/连线自动同步后端 KG）在 Gap Analysis 中标记为 ✅ Complete，但用户前端测试时标记为 NOT_VISIBLE。经过深度探索（见 `docs/project-status/fr-exploration/FR-KG-04.md`）和 Gemini Deep Research 对抗性审查，发现以下问题：

**P0 — 静默失败（NOT_VISIBLE 的根因）**：
- `SyncService._upsert_edge()` 使用 `MATCH` 查找 source/target 节点
- 当 batch 中 edge 先于 node 到达时，MATCH 匹配 0 行，MERGE 不执行
- 但操作被标记为 `success=True`，前端认为同步成功
- 结果：节点存在但边丢失，且无任何错误信号

**P0 — 字段名不一致**：
- `create_learning_relationship()` 写入 `r.score`
- `get_review_suggestions()` 读取 `r.last_score`
- 复习建议的分数永远是 null，导致复习算法以空值为输入

**P1 — 错误分类错误**：
- `/api/v1/sync/batch` 的 `except Exception` 把所有异常当 503
- 验证错误（应 400）被误报为"Neo4j 不可用"
- 错误详情泄露给客户端（`str(e)[:200]`）

### 2026-04-06 增量更新：三轮交叉验证后的新发现与架构升级

本 change 原版（2026-04-05）采用**防御式补丁哲学**——保持 Story 1.5 AC-7 的"部分提交"语义不变，通过拓扑排序 + 显式失败检查来减少问题。

2026-04-06 经过新一轮对抗性审查（本地 Explore × 3 + GPT Deep Research × 2 次独立分析 + 代码级核验），确认 AC-7 本身是 Story 1.5 的显式设计选择（不是 bug），但在依赖场景下会放大不一致，需要**架构层升级**而非单点补丁：

**新发现**：
- **Segment 提交需求**：用户最终确认采用 C 方案 —— 依赖感知 Segment 提交（Board → Node → Edge 三段），Segment 1/2 原子提交，Segment 3 允许部分失败。这使 Task 1 的"拓扑排序"从"并列操作"升级为"天然的 Segment 分段"。
- **错误分类回流需求**：前端需要根据 per-operation 失败原因决定重试策略（VALIDATION 永久失败 / DEPENDENCY 优先重试 / TRANSIENT 指数退避）。仅有 HTTP 状态码（Task 4）不足以支持 per-op 决策。
- **Wave 1 已执行的前端修复改变了不变量**：canvas-store.ts 的 update/delete 操作现已发送完整 canvasId + sourceNodeId + targetNodeId 字段（commit `1ea43b2`），这使 Task 3 (payload 校验) 从"关键修复"降级为"防御性编程"，但仍值得保留。

**Wave 1 已完成（不在本 change 范围）**：
- `1ea43b2`: 前端 canvas-store.ts 补全 canvasId/source/target
- `c7215ca`: QuestionGenerator KG 查询 schema 对齐（与本 change Task 5 同构的 bug，位于不同文件）
- `27bbd73`: MemoryService group_id 在内存 fallback 路径的过滤修复

### 发现来源
- FR-KG-04 Deep Explore（2026-04-04，原版）
- Gemini Deep Research 对抗性审查报告（`/Users/Heishing/Downloads/deep-research-report.md`）
- ChatGPT Deep Research 二次核验（`/Users/Heishing/Downloads/deep-research-report-10.md`，2026-04-06）
- 本地 Explore Agent × 3 + 代码级直接验证（2026-04-06）
- 三轮交叉验证修正了多项误判（详见 `/Users/Heishing/.claude/plans/snuggly-swimming-marble.md`）

## What Changes

### 目标
1. 消除 edge 静默失败 → 要么成功创建，要么明确报错
2. 修复字段名不一致 → 复习建议能读到正确分数
3. 错误分类正确 → 前端能区分"修 payload"和"重试连接"
4. **（2026-04-06 新增）升级事务语义为 Segment 提交 → 依赖类操作原子化，独立类操作允许部分失败**
5. **（2026-04-06 新增）引入 per-operation 错误分类 → 前端可按失败原因精确重试**

### 范围

**做**：
- **Payload 校验层（P1，独立修复）**
  - edge payload 强校验（source_node_id/target_node_id 必填）
  - 批次大小上限（max_length=500）
  - node content / edge label 长度上限
- **错误处理层（P1，独立修复）**
  - `sync.py` HTTP 错误分类（400/500/503 区分）
  - `neo4j_client.py` 字段对齐（`r.last_score` 读取改为 `r.score as last_score`）
  - `review_count` 在 Cypher 中递增
- **架构升级层（P0，2026-04-06 新增，依赖上面两层完成）**
  - **Segment 原子提交改造**：`process_sync_batch()` 拆分为 3 段独立事务
    - Segment 1 (Board): 原子提交，任一失败 → rollback + 停止 Segment 2/3
    - Segment 2 (Node): 原子提交，任一失败 → rollback + 停止 Segment 3
    - Segment 3 (Edge): per-op try/except，末尾一起 commit（保留 AC-7 精神但限定到独立类操作）
    - Delete 操作逆序（Edge → Node → Board），各段遵循相同原子规则
    - 天然包含原 Task 1 的拓扑排序意图（通过 Segment 分段实现）
  - **per-operation Fail Fast**：`_upsert_edge()` 入口检查 source/target 非空，缺失 → 抛 `SyncDependencyError`
  - **operation_id 幂等去重**：批次内重复 op_id 标记为 `duplicate_operation_id_skipped`
  - **SyncErrorClass 枚举**：`VALIDATION_ERROR / DEPENDENCY_MISSING / TRANSIENT_ERROR`
  - **`SyncOperationResult.error_class` 字段**：per-op 错误原因回流
  - **前端 sync-engine.ts 错误回流重试策略**：
    - `VALIDATION_ERROR`: 永久标记失败（outbox 增 `permanentlyFailed` 字段）
    - `DEPENDENCY_MISSING`: 保留在 outbox，下一轮同步时优先处理（Segment 2 顺序）
    - `TRANSIENT_ERROR`: 指数退避重试
  - **Dexie sync_outbox schema 升级**：新增 `permanentlyFailed` / `failureClass` 字段

**不做（延后）**：
- Neo4j 三层图谱合并（需要更大的设计讨论）
- RAG 注入防护增强（独立 change）
- API Key 认证（Tauri sidecar 单机部署，优先级低）
- CONNECTS_TO 死代码清理（已确认 VerificationService 于 `verification_service.py:1895` 改读 CANVAS_EDGE；CanvasService 的 `_sync_edge_to_neo4j` 路径 B 已不被触发，清理可延后）
- A11 图谱感知考察规划（独立 change，Wave 3 处理）

### 影响文件

| 文件 | 改动 | Wave |
|------|------|:-:|
| `backend/app/services/sync_service.py` | Segment 提交 + Fail Fast + 去重（Task 7） | 2 |
| `backend/app/models/sync_models.py` | payload 校验 + 批次上限（Task 3）+ error_class 字段（Task 8） | 2 |
| `backend/app/api/v1/endpoints/sync.py` | HTTP 错误分类（Task 4） | 2 |
| `backend/app/clients/neo4j_client.py` | r.score/r.last_score 对齐 + review_count（Task 5） | 2 |
| `frontend/src/services/sync-engine.ts` | 错误回流重试策略（Task 9，**打破原 change "前端不改"的不变量**） | 2 |
| `frontend/src/services/dexie-db.ts` | sync_outbox schema 加 permanentlyFailed/failureClass（Task 9） | 2 |

### 验证方式

1. **单元测试**：构造乱序 batch（edge 先于 node）→ Segment 提交后 edge 位于 Segment 3，node 已在 Segment 2 提交，edge 成功创建
2. **单元测试**：edge payload 缺 source_node_id → Pydantic ValidationError → 返回 400（非 503）
3. **单元测试**：重复 operation_id → 标记为 `duplicate_operation_id_skipped`
4. **单元测试**：`get_review_suggestions()` 返回非 null 的 `last_score`
5. **集成测试**：关闭 Neo4j → 返回 503 且不泄露内部细节
6. **回归测试**：正常 batch 流程不受影响
7. **（新）单元测试**：Segment 2 Node 失败 → Segment 3 不执行 → response 中所有 Edge op 标记为 `DEPENDENCY_MISSING`
8. **（新）单元测试**：Segment 3 内部分 Edge 失败 → 其他成功 Edge 仍 commit → response 中失败项标记为对应 error_class
9. **（新）集成测试**：前端模拟收到 `VALIDATION_ERROR` → outbox 中该条目标记 `permanentlyFailed=true`
10. **（新）集成测试**：前端模拟收到 `DEPENDENCY_MISSING` → 下次同步时该条目被优先发送

### 回滚方式
所有改动可按 Task 粒度单独 revert：
- Task 3/4/5 彼此独立，可任意组合回滚
- Task 7 (Segment 提交) 依赖 Task 3 (校验) 和 Task 8 (error_class)
- Task 9 (前端回流) 依赖 Task 8 的后端字段扩展，但前后端分两次 commit 可独立 revert
- 若 Segment 提交引入问题，可将 `process_sync_batch` 回退到原单事务实现，只丢 Task 7 部分

### 风险
- **Segment 提交改变了事务边界**：原"一个 batch 一个事务"变成"一个 batch 三个事务"，需验证在 Neo4j driver 层不会引入意外行为（例如会话锁、连接池压力）
- **前后端版本不对齐风险**：若后端先发布（返回 error_class）而前端未升级，sync-engine.ts 会忽略新字段，降级为原行为（不会崩溃，但新重试策略不生效）。反过来前端先发布则 error_class 永远为 undefined，降级为旧行为
- **Dexie schema 版本升级**：新增字段需要 Dexie version bump，用户首次启动会触发 upgrade migration，需确认不影响现有 outbox 条目
- payload 校验的字段名需确认前端 SyncEngine 发送的是 `sourceNodeId`（camelCase）——Wave 1 修复后已确认是 camelCase
- operation_id 去重的去重范围仅在单批次内，跨批次去重需要后端持久化已处理 op_id（本 change 不做）

## 探索记录

详细探索过程和发现见：
- `docs/project-status/fr-exploration/FR-KG-04.md`（含用户批注）
- Gemini 报告：`/Users/Heishing/Downloads/deep-research-report.md`

### 探索中发现的其他问题（不在本 change 范围内，记录供后续参考）

1. **Neo4j 三层图谱分裂** — CANVAS_EDGE / CONNECTS_TO / RELATES_TO 互不相通
2. **验证服务图查询简陋** — 1-hop CONNECTS_TO 查询，且数据源为空（死代码）
3. **RAG 字段名不匹配** — 验证服务期望 `learning_history` 但 RAG 返回 `reranked_results`
4. **检索文档绕过注入防护** — 用户输入有 3 层防护，但 RAG 检索结果直接进 LLM
5. **验证服务不用 FSRS 排序** — 按文件顺序出题，不看掌握度/遗忘度
6. **跨白板检索已取消** — S27-GDA-2 决策，代码残留但未实现
