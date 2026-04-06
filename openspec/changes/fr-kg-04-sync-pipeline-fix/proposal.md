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

### 发现来源
- FR-KG-04 Deep Explore（本 session，2026-04-04）
- Gemini Deep Research 对抗性审查报告（`/Users/Heishing/Downloads/deep-research-report.md`）
- 三个独立 Agent 交叉验证确认报告准确性

## What Changes

### 目标
1. 消除 edge 静默失败 → 要么成功创建，要么明确报错
2. 修复字段名不一致 → 复习建议能读到正确分数
3. 错误分类正确 → 前端能区分"修 payload"和"重试连接"

### 范围

**做**：
- Sync 批处理拓扑排序（node 先于 edge）
- edge payload 强校验（source_node_id/target_node_id 必填）
- `_upsert_edge()` 改用 OPTIONAL MATCH + 显式状态返回
- 批次内 operation_id 去重
- 批次大小上限（max_length=500）
- `sync.py` 错误分类（400/500/503 区分）
- `neo4j_client.py` 字段对齐（`r.score` → `r.last_score` 或反向统一）
- `review_count` 在 Cypher 中递增

**不做（延后）**：
- Neo4j 三层图谱合并（需要更大的设计讨论）
- RAG 注入防护增强（独立 change）
- API Key 认证（仅 localhost 部署，优先级低）
- CONNECTS_TO 死代码清理（取决于图层合并方案）

### 影响文件

| 文件 | 改动 |
|------|------|
| `backend/app/services/sync_service.py` | 拓扑排序 + 去重 + _upsert_edge 显式失败 |
| `backend/app/models/sync_models.py` | payload 校验 + 批次上限 |
| `backend/app/api/v1/endpoints/sync.py` | 错误分类（400/500/503） |
| `backend/app/clients/neo4j_client.py` | r.score/r.last_score 对齐 + review_count |

### 验证方式

1. **单元测试**：构造乱序 batch（edge 先于 node），验证拓扑排序后 edge 成功创建
2. **单元测试**：edge payload 缺 source_node_id → 返回 400（非 503）
3. **单元测试**：重复 operation_id → 标记为 `duplicate_operation_id_skipped`
4. **单元测试**：`get_review_suggestions()` 返回非 null 的 `last_score`
5. **集成测试**：关闭 Neo4j → 返回 503 且不泄露内部细节
6. **回归测试**：正常 batch 流程不受影响

### 回滚方式
所有改动在后端 Python 文件中，互不依赖。可按文件单独 revert。前端无改动，无前端回滚需求。

### 风险
- 拓扑排序改变了操作执行顺序，需确认不影响 delete 场景（delete edge 应先于 delete node）
- payload 校验可能拒绝旧格式的前端请求（需确认前端 SyncEngine 发送的字段名是 `sourceNodeId` 还是 `source_node_id`）

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
