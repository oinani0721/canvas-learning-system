# 后端 API 合约文档

> 生成时间: 2026-03-24 | 扫描模式: exhaustive
>
> 基础路径: `/api/v1`（由 `backend/app/api/v1/router.py` 统一注册）

## 目录

1. [Canvas CRUD](#1-canvas-crud) (8 端点)
2. [Agents](#2-agents) (13 端点)
3. [Memory](#3-memory) (7 端点)
4. [Exam](#4-exam) (16 端点)
5. [Review](#5-review) (12 端点)
6. [Mastery](#6-mastery) (10 端点)
7. [RAG](#7-rag) (5 端点)
8. [Multimodal](#8-multimodal) (10 端点)
9. [Metadata/Index](#9-metadataindex) (11 端点)
10. [Rollback](#10-rollback) (7 端点)
11. [Cross-Canvas](#11-cross-canvas) (14 端点)
12. [Profile](#12-profile) (4 端点)
13. [System/Health](#13-systemhealth) (24 端点)
14. [Debug](#14-debug) (3 端点)
15. [Config & Misc](#15-config--misc) (13 端点)
16. [WebSocket 端点](#16-websocket-端点) (2 端点)
17. [MCP Tools](#17-mcp-tools) (15 工具)

---

## 1. Canvas CRUD

> 路由前缀: `/api/v1/canvas` | 文件: `endpoints/canvas.py`

| Method | Path | 说明 |
|--------|------|------|
| GET | `/{canvas_name}` | 获取画布完整数据（节点+边） |
| POST | `/{canvas_name}/nodes` | 创建节点 |
| PUT | `/{canvas_name}/nodes/{node_id}` | 更新节点 |
| DELETE | `/{canvas_name}/nodes/{node_id}` | 删除节点 |
| POST | `/{canvas_name}/edges` | 创建边 |
| DELETE | `/{canvas_name}/edges/{edge_id}` | 删除边 |
| POST | `/{canvas_name}/sync-edges` | 全量 Edge 同步 |
| POST | `/{canvas_id}/recommendations` | 获取关系推荐 |

## 2. Agents

> 路由前缀: `/api/v1/agents` | 文件: `endpoints/agents.py`

| Method | Path | 说明 |
|--------|------|------|
| GET | `/health` | Agent 服务健康检查 |
| POST | `/decompose/basic` | 基础分解 (单节点 Agent) |
| POST | `/decompose/deep` | 深度分解 (含 RAG 检索) |
| POST | `/decompose/question` | 题目分解 (考试模式) |
| POST | `/score` | AutoSCORE 评分 |
| POST | `/explain/oral` | 口语化解释 |
| POST | `/explain/clarification` | 澄清式解释 |
| POST | `/explain/comparison` | 对比式解释 |
| POST | `/explain/memory` | 记忆锚点解释 |
| POST | `/explain/four-level` | 四层递进解释 |
| POST | `/explain/example` | 案例式解释 |
| POST | `/verification/question` | 验证性提问 |
| POST | `/recommend-action` | 推荐下一步行动 |

## 3. Memory

> 路由前缀: `/api/v1/memory` | 文件: `endpoints/memory.py`

| Method | Path | 说明 |
|--------|------|------|
| POST | `/episodes` | 记录学习事件 |
| GET | `/episodes` | 查询学习事件列表 |
| GET | `/concepts/{concept_id}/history` | 获取概念学习历史 |
| GET | `/review-suggestions` | 获取复习建议 |
| GET | `/health` | Memory 服务健康检查 |
| POST | `/episodes/batch` | 批量记录学习事件 |
| POST | `/extract-conversation` | 从对话中提取学习事件 |

## 4. Exam

> 路由前缀: 无前缀 (直接挂载) | 文件: `endpoints/exam.py`, `endpoints/exam_sessions.py`

| Method | Path | 说明 |
|--------|------|------|
| POST | `/exam/start` | 创建考试会话 |
| GET | `/exam/{exam_id}` | 获取考试详情 |
| GET | `/exam/by-canvas/{canvas_id}` | 按画布获取考试 |
| PATCH | `/exam/{exam_id}/status` | 更新考试状态 |
| POST | `/exam/analyze-canvas` | 分析画布内容生成考题 |
| POST | `/exam/{exam_id}/sync-node` | 同步节点到考试 |
| POST | `/exam/{exam_id}/hint` | 请求提示 (Chain-of-Hints) |
| POST | `/exam/{exam_id}/skip` | 跳过题目 |
| GET | `/exam/{exam_id}/cognitive-load` | 获取认知负荷 |
| POST | `/exam/{exam_id}/pause` | 暂停考试 |
| POST | `/exam/{exam_id}/resume` | 恢复考试 |
| POST | `/exam/{exam_id}/complete` | 完成考试 |
| GET | `/exam/records` | 获取考试记录列表 |
| GET | `/exam/records/by-canvas/{canvas_id}` | 按画布获取考试记录 |
| GET | `/exam/records/{record_exam_id}` | 获取单条考试记录 |
| GET | `/exam_sessions` | 列出考试会话 |

## 5. Review

> 路由前缀: `/api/v1/review` | 文件: `endpoints/review.py`

| Method | Path | 说明 |
|--------|------|------|
| GET | `/schedule` | 获取复习调度 |
| GET | `/history` | 获取复习历史 |
| POST | `/generate` | 生成复习画布 |
| PUT | `/record` | 记录复习结果 |
| GET | `/progress/multi/{original_canvas_path}` | 获取多节点复习进度 |
| GET | `/verification/history/{concept}` | 获取验证历史 |
| GET | `/fsrs-state/{concept_id}` | 获取 FSRS 状态 |
| GET | `/session/{session_id}/progress` | 获取复习会话进度 |
| POST | `/session/{session_id}/pause` | 暂停复习会话 |
| POST | `/session/{session_id}/resume` | 恢复复习会话 |
| POST | `/session/start` | 开始复习会话 |
| POST | `/session/{session_id}/answer` | 提交复习答案 |

## 6. Mastery

> 路由前缀: 无 (路径已含 `/mastery`) | 文件: `endpoints/mastery.py`

| Method | Path | 说明 |
|--------|------|------|
| GET | `/mastery/batch` | 批量获取掌握度 |
| GET | `/mastery/board/{board_id}` | 按画布获取掌握度 |
| POST | `/mastery/{concept_id}/grade` | 记录评分 |
| POST | `/mastery/{concept_id}/override` | 手动覆盖掌握度 |
| POST | `/mastery/{concept_id}/self-assess` | 自我评估 |
| DELETE | `/mastery/{concept_id}/override` | 重置覆盖 |
| POST | `/mastery/graphiti-sync` | Graphiti 同步 |
| POST | `/mastery/{concept_id}/calibration` | 记录校准数据 |
| GET | `/mastery/{concept_id}/calibration/summary` | 获取校准摘要 |
| GET | `/mastery/calibration/dangerous` | 获取危险节点 |

## 7. RAG

> 路由前缀: `/api/v1/rag` | 文件: `endpoints/rag.py`

| Method | Path | 说明 |
|--------|------|------|
| POST | `/query` | RAG 检索查询 |
| GET | `/weak-concepts/{canvas_file}` | 获取薄弱概念 |
| GET | `/status` | RAG 管道状态 |
| GET | `/config` | 获取 RAG 配置 |
| PUT | `/config` | 更新 RAG 配置 |

## 8. Multimodal

> 路由前缀: `/api/v1/multimodal` | 文件: `endpoints/multimodal.py`

| Method | Path | 说明 |
|--------|------|------|
| POST | `/upload` | 上传多模态内容 |
| POST | `/upload-url` | 通过 URL 上传 |
| GET | `` | 获取多模态内容列表 |
| GET | `/health` | 多模态服务健康检查 |
| GET | `/list` | 列出内容 |
| POST | `/search` | 搜索多模态内容 |
| GET | `/by-concept/{concept_id}` | 按概念获取内容 |
| GET | `/{content_id}` | 获取单条内容 |
| PUT | `/{content_id}` | 更新内容 |
| DELETE | `/{content_id}` | 删除内容 |

## 9. Metadata/Index

> 路由前缀: `/api/v1/canvas-meta` | 文件: `endpoints/metadata.py`

| Method | Path | 说明 |
|--------|------|------|
| GET | `/metadata` | 获取画布元数据 |
| GET | `/index-status` | 获取索引状态 |
| POST | `/index` | 索引单个节点 |
| POST | `/index/batch` | 批量索引 |
| POST | `/index/vault` | Vault 全量索引 |
| GET | `/index/vault/status` | Vault 索引状态 |
| POST | `/index/vault/incremental` | Vault 增量索引 |
| GET | `/config/subject-mapping` | 获取学科映射配置 |
| PUT | `/config/subject-mapping` | 更新学科映射 |
| POST | `/config/subject-mapping/add` | 添加学科映射 |
| DELETE | `/config/subject-mapping/remove` | 删除学科映射 |

## 10. Rollback

> 路由前缀: `/api/v1/rollback` | 文件: `endpoints/rollback.py`

| Method | Path | 说明 |
|--------|------|------|
| GET | `/history/{canvas_path}` | 获取操作历史 |
| GET | `/operation/{operation_id}` | 获取操作详情 |
| GET | `/snapshots/{canvas_path}` | 获取快照列表 |
| POST | `/snapshot` | 创建快照 |
| GET | `/snapshot/{snapshot_id}` | 获取快照详情 |
| POST | `/rollback` | 执行回滚 |
| GET | `/diff/{snapshot_id}` | 获取快照差异 |

## 11. Cross-Canvas

> 路由前缀: 无 (endpoints/cross_canvas.py) | 文件: `endpoints/cross_canvas.py`

| Method | Path | 说明 |
|--------|------|------|
| GET | `/associations` | 列出关联 |
| POST | `/associations` | 创建关联 |
| GET | `/associations/{association_id}` | 获取关联详情 |
| PUT | `/associations/{association_id}` | 更新关联 |
| DELETE | `/associations/{association_id}` | 删除关联 |
| GET | `/paths` | 列出学习路径 |
| POST | `/paths` | 创建学习路径 |
| GET | `/paths/{path_id}` | 获取路径详情 |
| PUT | `/paths/{path_id}/nodes/{canvas_path}/mastery` | 更新路径节点掌握度 |
| DELETE | `/paths/{path_id}` | 删除路径 |
| GET | `/search` | 跨画布搜索 |
| GET | `/statistics` | 跨画布统计 |
| GET | `/suggestions` | 关联建议 |
| POST | `/associations/auto-discover` | 自动发现关联 |

## 12. Profile

> 路由前缀: 无 (路径含 `/profile`) | 文件: `endpoints/profile.py`

| Method | Path | 说明 |
|--------|------|------|
| GET | `/profile/{node_id}/summary` | 获取学习档案摘要 |
| GET | `/profile/{node_id}/tips` | 获取 Tips 列表 |
| GET | `/profile/{node_id}/weaknesses` | 获取薄弱点 |
| GET | `/profile/{node_id}/qa-highlights` | 获取 QA 精华 |

## 13. System/Health

> 路由前缀: 无 (system.py) + (health.py) + (monitoring.py) | 文件: `system.py`, `endpoints/health.py`, `endpoints/monitoring.py`

### system.py 端点

| Method | Path | 说明 |
|--------|------|------|
| GET | `/health` | 系统健康检查 (入口) |
| GET | `/llm-stats` | LLM 调用统计 |
| POST | `/config` | 运行时配置更新 |
| POST | `/test-llm` | LLM 连接测试 |
| GET | `/qa-metrics` | QA 质量指标 |
| GET | `/pipeline-health` | 管道健康状态 |
| GET | `/extraction-records` | 提取记录列表 |
| POST | `/extraction-records/{record_id}/annotate` | 标注提取记录 |
| PATCH | `/extraction-records/{record_id}` | 更新提取记录 |
| DELETE | `/extraction-records/{record_id}` | 删除提取记录 |
| DELETE | `/extraction-records/{record_id}/annotation` | 删除标注 |
| GET | `/error-aggregation` | 错误聚合统计 |

### health.py 端点

| Method | Path | 说明 |
|--------|------|------|
| GET | `/health` | 综合健康检查 |
| GET | `/health/metrics` | 性能指标 |
| GET | `/health/metrics/summary` | 指标摘要 |
| GET | `/health/agents` | Agent 健康状态 |
| GET | `/health/ai` | AI 服务健康状态 |
| GET | `/health/full` | 全量健康检查 |
| GET | `/health/neo4j` | Neo4j 健康状态 |
| GET | `/health/graphiti` | Graphiti 健康状态 |
| GET | `/health/lancedb` | LanceDB 健康状态 |
| GET | `/health/storage` | 存储健康状态 |
| POST | `/health/storage/reset-counters` | 重置存储计数器 |
| GET | `/health/memory-logs` | 内存日志 |

### monitoring.py 端点

| Method | Path | 说明 |
|--------|------|------|
| GET | `/metrics/alerts` | 告警列表 |
| GET | `/metrics/summary` | 监控摘要 |

## 14. Debug

> 路由前缀: `/api/v1/debug` | 文件: `endpoints/debug.py`

| Method | Path | 说明 |
|--------|------|------|
| GET | `/bugs` | Bug 列表 |
| GET | `/bugs/stats` | Bug 统计 |
| GET | `/bugs/{bug_id}` | Bug 详情 |

## 15. Config & Misc

### Config

> 路由前缀: `/api/v1/config` | 文件: `endpoints/config.py`

| Method | Path | 说明 |
|--------|------|------|
| POST | `/ai` | 更新 AI 配置 |
| GET | `/ai` | 获取 AI 配置 |

### Context

| Method | Path | 说明 |
|--------|------|------|
| GET | `/context/{node_id}` | 获取学习上下文 (Tier1+Tier2) |

### Edges

> 路由前缀: `/api/v1/edges`

| Method | Path | 说明 |
|--------|------|------|
| POST | `/record-rationale` | 记录边的推理依据 |

### Subjects

> 路由前缀: `/api/v1/subjects`

| Method | Path | 说明 |
|--------|------|------|
| GET | `/` | 列出学科 |
| POST | `/` | 创建学科 |
| PUT | `/{subject_id}` | 更新学科 |
| DELETE | `/{subject_id}` | 删除学科 |

### Sync / Tips / Suggestions / Archive / Skills / Inheritance / Index-Image / Intelligent-Parallel

| 前缀 | Method | Path | 说明 |
|-------|--------|------|------|
| `/sync` | POST | `/batch` | 批量同步 |
| `/tips` | GET | `` | 获取 Tips |
| `/tips` | POST | `` | 保存 Tip |
| `/suggestions` | POST | `/relation` | 关系建议 |
| `/archive` | POST | `/trigger` | 触发归档 |
| `/archive` | GET | `/status/{node_id}` | 归档状态 |
| `/archive` | GET | `/summary/{node_id}` | 归档摘要 |
| `/skills` | GET | `` | 技能列表 |
| `/skills` | GET | `/{skill_id}` | 技能详情 |
| `/skills` | POST | `/refresh` | 刷新技能 |
| 无 | POST | `/chat/{node_id}/distill` | 对话蒸馏继承 |
| 无 | POST | `/index/image` | 图片索引 |

### Intelligent Parallel

> 路由前缀: `/api/v1/canvas/intelligent-parallel`

| Method | Path | 说明 |
|--------|------|------|
| POST | `/` | 创建并行处理会话 |
| POST | `/confirm` | 确认并行处理 |
| GET | `/{session_id}` | 获取会话状态 |
| POST | `/cancel/{session_id}` | 取消会话 |
| POST | `/canvas/single-agent` | 单 Agent 重试 |

---

## 16. WebSocket 端点

| Path | 说明 | 文件 |
|------|------|------|
| `WS /ws/intelligent-parallel/{session_id}` | 智能并行处理实时进度推送 (30s heartbeat, 10min timeout) | `endpoints/websocket.py` |
| `WS /ws` | Mastery 掌握度实时推送 (mastery_update 消息, 30s heartbeat) | `endpoints/mastery_ws.py` |

---

## 17. MCP Tools

> 端点: `/mcp` (FastAPI-MCP ASGI 集成)
> 路由前缀: `/mcp/tools/*`
> 文件: `backend/app/mcp/server.py` + `backend/app/mcp/tools/`

### pipeline_token 流程

MCP 工具间通过 pipeline_token 强制步骤顺序：

```
generate_question ──token──> score_answer ──token──> update_fsrs / update_bkt
```

- `generate_question` 返回 pipeline_token
- `score_answer` 需要该 token，返回新 token
- `update_fsrs` / `update_bkt` 需要 score_answer 的 token

### 工具列表 (15 个)

| 工具名 | 模块 | 说明 | 需要 pipeline_token |
|--------|------|------|-------------------|
| `query_mastery` | mastery_tools | 查询节点掌握度 (BKT + FSRS) | 否 |
| `update_fsrs` | mastery_tools | 更新 FSRS 间隔重复参数 | 是 |
| `update_bkt` | mastery_tools | 更新 BKT 掌握概率 | 是 |
| `generate_question` | exam_tools | 为概念节点生成考题 | 否 (返回 token) |
| `score_answer` | exam_tools | AutoSCORE 评分 | 是 (返回新 token) |
| `assemble_acp` | exam_tools | 组装 Assessment Context Package | 否 |
| `request_hint` | exam_tools | Chain-of-Hints 渐进提示 (L1-L4) | 否 |
| `skip_question` | exam_tools | 跳过题目 (无 BKT/FSRS 惩罚) | 否 |
| `search_memories` | memory_tools | 搜索学习记忆 (Graphiti KG) | 否 |
| `record_calibration` | memory_tools | 记录校准数据 (元认知追踪) | 否 |
| `record_learning_memory` | memory_tools | 记录学习记忆 (Observer 写入路径) | 否 |
| `archive_conversation` | conversation_tools | 归档完成的对话 | 否 |
| `create_exam_node` | conversation_tools | 在画布上创建考试节点 | 否 |
| `record_error` | error_tools | 记录并分类学生错误 (4 类型) | 否 |
| `search_notes` | note_search_tools | 搜索 Vault 笔记 (6 源 RAG) | 否 |
