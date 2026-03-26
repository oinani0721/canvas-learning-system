# Session S29 提示词 — Phase 2.6 自动触发 + Phase 3 管道修复

## 上一 Session S28 完成了：
1. **Phase 2 Graphiti 真实接入**（15 commits）
   - GraphitiEpisodeWorker：asyncio.Queue + Gemini 全家桶（gemini-2.5-flash + gemini-embedding-001 + GeminiRerankerClient）
   - SEMAPHORE_LIMIT=3 + max_coroutines=3
   - 临界交换：record_learning_event + record_knowledge_entity → _enqueue_episode
   - 三层搜索：Graphiti 语义(5条) + Neo4j fulltext(1条) + 内存(1条) 全部验证通过
   - 旧代码删除：graphiti_bridge_service.py + JSON 双写 + 假命名清理
2. **排障修复**（6个运行时问题）
   - GOOGLE_API_KEY docker 覆盖 → 从 docker-compose 移除
   - 缺少 GeminiRerankerClient cross-encoder
   - embedding 模型 text-embedding-001 → gemini-embedding-001
   - SEMAPHORE_LIMIT 未设置
   - Neo4j fulltext 索引名修复
   - 用户 Google Billing 从 inactive 升级为 pay-as-you-go
3. **验证通过**
   - 写入管道：POST /memory/episodes → enqueue → add_episode 成功（23.9s）
   - 搜索管道：三层搜索全部返回结果
   - Worker 监控：/api/v1/metrics/episode-worker → running

## ⛔ 遗留的关键问题
**前端对话不自动触发 enqueue** — 用户在产品中对话后，Worker episodes_enqueued 为 0。原因：没有代码在对话流程中调用 record_learning_event()。需要 Phase 2.6 PostToolUse Hook 或其他自动触发机制。

## S29 目标

### 必须先做：Phase 2.6 自动触发机制
设计文档定义了 PostToolUse Hook BEA 4 维度提取，但依赖 sidecar。
需要先调研：当前对话流程的触发点在哪里？conversation_distiller 是已知的一个触发点（S28 测试中成功 enqueue 了 2 条），但不够——需要覆盖：
- 每次 AI 对话回复后自动记录
- Tips 标注时记录
- 考试评分时记录
- 错误分类时记录

### 然后：Phase 3 管道修复（设计文档已定义）
- 3.1 Sidecar Windows 验证（MVP #4 + #12）
- 3.2 笔记索引修复（MVP #10）
- 3.3 检验白板 Prompt 文件外部化（决策 S27-GDA-4）
- 3.4 点击跳转功能（决策 S27-GDA-6，最高优先级）
- 3.5 record_learning_memory 格式修复
- 3.6 补救策略消费
- 3.7 RAG 管道精简（移除 2 个 TODO 空通道）
- 3.8 考察中交互规则

## 关键文件（必须读取）
- docs/superpowers/specs/2026-03-25-path-a-pipeline-design.md — APPROVED 设计文档（Phase 3 章节）
- docs/superpowers/specs/2026-03-25-review-checklist.md — 审查清单
- docs/superpowers/plans/2026-03-26-phase2-graphiti-real-integration.md — Phase 2 实施记录
- _decisions/decision-log.md — 全量决策索引
- backend/app/services/episode_worker.py — Worker 核心文件
- backend/app/services/memory_service.py — _enqueue_episode + 三层搜索

## 执行方式
1. 先 /gda 全量审计（16 Agent）— 理清 Phase 2→3 过渡期的决策状态
2. 然后 Superpowers Writing Plans → Subagent-Driven Development
