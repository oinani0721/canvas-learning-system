# 代码归属分类 — 孤儿代码检测

> 生成日期: 2026-04-03
> 扫描范围: backend/app/services/ (59 文件) + backend/app/api/v1/endpoints/ (31 文件)

---

## 结论: 0 个疑似孤儿

所有 90 个文件均可归类为 FR 对应实现或基础设施/工具代码。无发现"有业务逻辑但无对应 FR"的孤儿代码。

---

## Backend Services (59 文件)

### 核心 Canvas & 学习 (5 文件)

| 文件 | 主要类/函数 | 对应 FR | 分类 |
|------|-----------|---------|------|
| canvas_service.py | CanvasService — CRUD .canvas JSON | FR-KG-01~04, FR-DASH-01 | FR 对应 |
| exam_service.py | ExamService — 检验白板工作流 | FR-EXAM-01~22 | FR 对应 |
| exam_service_ext.py | 考察提示/认知负载扩展 | FR-EXAM-19 | FR 对应 |
| mastery_engine.py | MasteryEngine — BKT+FSRS 计算 | FR-MAST-01~04 | FR 对应 |
| mastery_store.py | MasteryStore — 精通度持久化 | FR-MAST-01 | FR 对应 |

### 记忆 & 学习记录 (3 文件)

| 文件 | 主要类/函数 | 对应 FR | 分类 |
|------|-----------|---------|------|
| memory_service.py | MemoryService — Graphiti/Neo4j 集成 | FR-RET-03, FR-MCP-01 | FR 对应 |
| episode_worker.py | GraphitiEpisodeWorker — 异步写入 | FR-RET-03 | FR 对应 |
| conversation_archive.py | ArchiveManager — Hot/Warm/Cold 归档 | FR-CONV-07, FR-TRACE-05 | FR 对应 |

### Agent & 对话 (5 文件)

| 文件 | 主要类/函数 | 对应 FR | 分类 |
|------|-----------|---------|------|
| agent_service.py | AgentService — Gemini API 封装 | FR-AGENT-01 | FR 对应 |
| agent_routing_engine.py | AgentRoutingEngine — 请求路由 | FR-AGENT-01 | FR 对应 |
| agent_selector.py | SelectionContext — Agent 选择逻辑 | FR-AGENT-01 | FR 对应 |
| react_agent.py | React Agent 编排 | FR-AGENT-01 (Phase 4) | FR 对应 |
| conversation_distiller.py | ConversationDistiller — 提取 Tips/errors | FR-CONV-07, FR-TRACE-05 | FR 对应 |

### 出题 & 评分 (3 文件)

| 文件 | 主要类/函数 | 对应 FR | 分类 |
|------|-----------|---------|------|
| question_generator.py | QuestionGenerator — ACP 出题 | FR-EXAM-03, FR-MCP-01 | FR 对应 |
| autoscore.py | AutoScorer — 两阶段 LLM 评分 | FR-EXAM-04 | FR 对应 |
| scoring_faithfulness.py | ScoringFaithfulnessChecker — 忠实度 | FR-QA-01 | FR 对应 |

### RAG & 上下文 (4 文件)

| 文件 | 主要类/函数 | 对应 FR | 分类 |
|------|-----------|---------|------|
| rag_service.py | RAGService — 向量检索 | FR-RET-01~05 | FR 对应 |
| context_enrichment_service.py | 上下文增强 | FR-CONV-03 | FR 对应 |
| learning_context_service.py | 节点上下文格式化 | FR-CONV-03, FR-CONV-11 | FR 对应 |
| conversation_inheritance.py | InheritedNodeContext — 跨节点对话继承 | FR-CONV-10 | FR 对应 |

### 精通度 & 校准 (4 文件)

| 文件 | 主要类/函数 | 对应 FR | 分类 |
|------|-----------|---------|------|
| mastery_fusion.py | MasteryFusionEngine — 信号融合 | FR-MAST-06 | FR 对应 |
| signal_registry.py | SignalRegistry — 信号源追踪 | FR-MAST-06 | FR 对应 |
| calibration_tracker.py | 校准偏差计算 | FR-MAST-05 | FR 对应 |
| difficulty_matcher.py | DifficultyMatcher — 难度匹配 | FR-EXAM-22, FR-QA-06 | FR 对应 |

### 监控 & 可观测 (5 文件)

| 文件 | 主要类/函数 | 对应 FR | 分类 |
|------|-----------|---------|------|
| alert_manager.py | AlertManager — 告警规则 | FR-SYS-04 | 基础设施 |
| health_monitor.py | PipelineHealthMonitor | FR-SYS-04 | 基础设施 |
| metrics_collector.py | Prometheus 指标 | FR-QA-03, FR-QA-04 | FR 对应 |
| resource_monitor.py | ResourceMonitor — CPU/内存/磁盘 | FR-SYS-04 | 基础设施 |
| error_aggregator.py | ErrorAggregator — 错误分类聚合 | FR-CONV-06 | FR 对应 |

### 索引 & 搜索 (3 文件)

| 文件 | 主要类/函数 | 对应 FR | 分类 |
|------|-----------|---------|------|
| lancedb_index_service.py | LanceDBIndexService — 向量索引 | FR-RET-07 | FR 对应 |
| intelligent_grouping_service.py | IntelligentGroupingService — 主题聚类 | FR-TRACE-04 | FR 对应 |
| intelligent_parallel_service.py | IntelligentParallelService — 并行处理 | — | 工具函数 |

### 事件 & 异步 (3 文件)

| 文件 | 主要类/函数 | 对应 FR | 分类 |
|------|-----------|---------|------|
| event_bus.py | EventBus — 发布/订阅 | — | 基础设施 |
| event_handlers.py | register_all_handlers | — | 基础设施 |
| background_task_manager.py | BackgroundTaskManager | — | 基础设施 |

### 工具 & 技能 (3 文件)

| 文件 | 主要类/函数 | 对应 FR | 分类 |
|------|-----------|---------|------|
| tool_definitions.py | Gemini 工具定义 | FR-AGENT-01 | FR 对应 |
| tool_executor.py | ToolExecutor — 工具执行 | FR-AGENT-01 | FR 对应 |
| skill_registry.py | SkillRegistry — 技能注册发现 | FR-SKILL-01~03 | FR 对应 |

### 推荐 & 复习 (3 文件)

| 文件 | 主要类/函数 | 对应 FR | 分类 |
|------|-----------|---------|------|
| recommendation_service.py | RecommendationService — 关联推荐 | FR-KG-05 | FR 对应 |
| review_service.py | ReviewService — 间隔复习调度 | FR-MAST-04 | FR 对应 |
| verification_service.py | 检验问题生成 | FR-EXAM-03 | FR 对应 |

### 基础设施 & 工具 (12 文件)

| 文件 | 主要类/函数 | 对应 FR | 分类 |
|------|-----------|---------|------|
| prompt_registry.py | PromptRegistry — 加载 prompt | FR-QA-02 | 基础设施 |
| markdown_image_extractor.py | MarkdownImageExtractor | FR-KG-06 | 工具函数 |
| notification_channels.py | NotificationChannel (ABC) | — | 基础设施 |
| session_manager.py | SessionManager — 生命周期管理 | FR-AGENT-02 | 基础设施 |
| archive_scheduler.py | ArchiveScheduler — 定时归档 | FR-CONV-07 | 基础设施 |
| batch_orchestrator.py | BatchOrchestrator — 批处理 | — | 工具函数 |
| cross_subject_bridge.py | 跨学科知识链接 | FR-SYS-07 | 工具函数 |
| extraction_validator.py | ExtractionValidator — 提取验证 | FR-QA-07 | 工具函数 |
| fallback_sync_service.py | FallbackSyncService — 离线同步 | FR-KG-04 | 基础设施 |
| error_classifier.py | ErrorClassifier — 错误分类 | FR-CONV-06 | FR 对应 |
| subject_resolver.py | SubjectResolver — 学科检测 | FR-SYS-07 | 工具函数 |
| sync_service.py | SyncService — Neo4j 同步 | FR-KG-04 | 基础设施 |
| topic_clustering.py | TopicClusterer — 文本聚类 | FR-TRACE-04 | 工具函数 |
| weight_calculator.py | WeightCalculator — 节点重要性 | FR-EXAM-02 | 工具函数 |
| multimodal_service.py | MultimodalService — 图片上传索引 | FR-KG-06 | FR 对应 |
| rollback_service.py | RollbackService — 撤销 | — | 基础设施 |
| websocket_manager.py | ConnectionManager — WebSocket | — | 基础设施 |

---

## Backend Endpoints (31 文件)

| 文件 | 端点 | 对应 FR | 分类 |
|------|------|---------|------|
| canvas.py | CRUD + sync + recommendations | FR-KG-01~05, FR-DASH-01 | FR 对应 |
| edges.py | record_edge_rationale | FR-EDGE-01~04 | FR 对应 |
| exam.py | start/get/hint/complete exam | FR-EXAM-01~22 | FR 对应 |
| exam_sessions.py | list_exam_sessions | FR-DASH-02, FR-DASH-04 | FR 对应 |
| review.py | 间隔复习生成 | FR-MAST-04 | FR 对应 |
| mastery.py | batch/board mastery, record grade | FR-MAST-01~06 | FR 对应 |
| mastery_ws.py | WebSocket 精通度实时更新 | FR-MAST-03 | FR 对应 |
| memory.py | learning episodes + history | FR-RET-03 | FR 对应 |
| archive.py | trigger/status archive | FR-CONV-07 | FR 对应 |
| agents.py | agent health + 11 agent 端点 | FR-AGENT-01, FR-SKILL-02 | FR 对应 |
| skills.py | list/get/refresh skills | FR-SKILL-01~03 | FR 对应 |
| rag.py | rag_query, weak_concepts | FR-RET-01~05 | FR 对应 |
| suggestions.py | suggest_relation | FR-KG-05 | FR 对应 |
| health.py | health_check, metrics | FR-SYS-04 | FR 对应 |
| config.py | AI config CRUD | FR-SYS-02, FR-SYS-03 | FR 对应 |
| system.py | (空文件) | — | 基础设施 |
| monitoring.py | alerts, metrics summary | FR-SYS-04 | FR 对应 |
| metadata.py | canvas metadata, index status | FR-KG-07 | FR 对应 |
| subjects.py | subject CRUD | FR-SYS-07 | FR 对应 |
| inheritance.py | distill_conversation | FR-CONV-10 | FR 对应 |
| multimodal.py | file upload/list | FR-KG-06 | FR 对应 |
| index_image.py | OCR index | FR-KG-06 | FR 对应 |
| context.py | node context enrichment | FR-CONV-03, FR-CONV-11 | FR 对应 |
| tips.py | get/save tips | FR-CONV-05 | FR 对应 |
| profile.py | profile summary/tips/weaknesses/qa | FR-TRACE-01~04 | FR 对应 |
| intelligent_parallel.py | canvas analysis + batch | — | 工具函数 |
| rollback.py | operation history + undo | — | 基础设施 |
| debug.py | bug tracking diagnostics | — | 基础设施 |
| ping.py | /ping 连通性检查 | — | 基础设施 |
| websocket.py | WS live progress | — | 基础设施 |
| sync.py | batch Neo4j sync | FR-KG-04 | FR 对应 |

---

## 统计

| 分类 | 数量 | 占比 |
|------|------|------|
| FR 直接对应 | 62 | 68.9% |
| 基础设施 | 19 | 21.1% |
| 工具函数 | 9 | 10.0% |
| 疑似孤儿 | 0 | 0% |
| **总计** | **90** | **100%** |
