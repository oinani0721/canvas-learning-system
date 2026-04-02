# Requirements

This file is the explicit capability and coverage contract for the Canvas Learning System.

Use it to track what is actively in scope, what has been validated by completed work, what is intentionally deferred, and what is explicitly out of scope.

Guidelines:
- Keep requirements capability-oriented, not a giant feature wishlist.
- Requirements should be atomic, testable, and stated in plain language.
- Every **Active** requirement should be mapped to a slice, deferred, blocked with reason, or moved out of scope.
- Each requirement should have one accountable primary owner and may have supporting slices.
- Research may suggest requirements, but research does not silently make them binding.
- Validation means the requirement was actually proven by completed work and verification, not just discussed.

---

## Active

### 核心对话链路

### R001 — Sidecar MCP 工具触发修复
- Class: core-capability
- Status: active
- Description: Sidecar 流式对话已通，但 MCP 工具调用不触发（generate_question、score_answer、search_memories 等）。修复 sidecar→MCP→后端全链路，使 Agent 能调用后端算法工具。
- Why it matters: 所有上层功能（考察、评分、记忆写入）都依赖 MCP 工具链路
- Source: user
- Primary owning slice: M001/S01
- Supporting slices: none
- Validation: unmapped
- Notes: 当前 sidecar.js 已有 MCP_TOOLS 白名单和 canUseTool 权限控制，问题可能在连接配置或后端 MCP 端点

### R002 — 对话上下文三层管理
- Class: core-capability
- Status: active
- Description: 实现完整的 Tier1（当前节点完整上下文，~3K tokens）+ Tier2（邻居摘要，~1K tokens）+ Tier3（按需 RAG 检索）三层对话上下文管理。当前 Tier3 仅有文档无代码。
- Why it matters: 对话质量的基石——Agent 需要精确的学习上下文才能给出个性化回答
- Source: FR-CONV-11, B5 验证报告
- Primary owning slice: M001/S03
- Supporting slices: none
- Validation: unmapped
- Notes: learning_context_service.py 已有 Tier1/2 框架，TIER1_CHAR_BUDGET=6000 和 TIER2_CHAR_BUDGET=2000 声明但未使用

### R003 — 上下文压缩 + 中文 Token 预算动态调整
- Class: core-capability
- Status: active
- Description: 后端 3 处暴力截断改用 LLM 语义摘要（参考 Claude Code 泄漏的压缩算法）。对话中压缩维持 SDK 原生。中文场景 token 预算从 4K 提升至 6-8K（中文每字符 1.33-2 token 膨胀率）。
- Why it matters: 当前暴力截断丢失语义关键信息；4K 预算对中文严重不足
- Source: user 确认, FR-CONV-13, B5-DR
- Primary owning slice: M001/S03
- Supporting slices: none
- Validation: unmapped
- Notes: 后端压缩点：learning_context_service.py（section pop）、compression.py（extractive）、question_generator.py（字段截断）。SDK 原生 compaction 通过 compact_boundary 事件透传前端。

### R004 — 节点间对话继承（Edge 语义检索前序摘要注入）
- Class: core-capability
- Status: active
- Description: 切换节点时通过 Edge 语义检索前序节点的对话摘要，注入新节点对话上下文（Phase 2）。当前 conversation_inheritance.py 已有 1-hop 框架但仅 MAX_INHERITED_NEIGHBORS=2 且无排序。
- Why it matters: 相邻概念的对话历史能帮助 Agent 理解知识关联
- Source: FR-CONV-10
- Primary owning slice: M002
- Supporting slices: none
- Validation: unmapped
- Notes: Phase 2 标记

### R005 — /resume 命令 session 管理 + session 手动命名
- Class: core-capability
- Status: active
- Description: 用户可通过 /resume 命令查看和切换节点对话 session。显示 session-节点映射关系。支持 session 手动命名/重命名，便于查找。
- Why it matters: 用户说"不进行命名的话，很难找到相关的 session"
- Source: user 确认, FR-CONV-12
- Primary owning slice: M002
- Supporting slices: none
- Validation: unmapped
- Notes: claude-engine.ts 有 per-node session ID 映射，但 /resume 命令和命名功能未实现

### R006 — 节点切换时后台继续生成 + 并发上限 + 状态指示
- Class: core-capability
- Status: active
- Description: 用户切换节点时，前一个节点的 AI 回答在后台继续生成（不取消）。节点上显示生成状态指示（生成中/完成未读/空闲）。同时并发生成上限 3 个，超出排队。
- Why it matters: 避免切换节点时丢失正在生成的回答
- Source: FR-CONV-09
- Primary owning slice: M002
- Supporting slices: none
- Validation: unmapped
- Notes: 当前 chat-store.ts 明确 "Prevent concurrent conversations for the same node"，需要重新设计

### R007 — Hot-Warm-Cold 三层对话归档
- Class: continuity
- Status: active
- Description: Hot（0-30天完整保留）→ Warm（30天-6月摘要+结构化提取）→ Cold（>6月仅结构化数据）。Cold 层恢复时先执行 Warm 精炼保证数据完整。蒸馏用 Opus 模型做高质量摘要。
- Why it matters: 控制 LLM 上下文窗口 + 保留长期学习记忆
- Source: FR-CONV-07, B5, user 确认
- Primary owning slice: M002
- Supporting slices: none
- Validation: unmapped
- Notes: conversation_archive.py + archive_scheduler.py 已有框架。Edge 对话不蒸馏，直接存为结构化 Edge 语义标签。

### Graphiti 记忆系统

### R008 — Graphiti 写入全链路验证
- Class: core-capability
- Status: active
- Description: 验证 Tips/错误/Edge 理由→MemoryService→EpisodeWorker→graphiti_core.add_episode 全链路可用。确保写入成功率和数据完整性。
- Why it matters: 个人记忆系统是"系统越来越懂你"的基石
- Source: user, B3
- Primary owning slice: M001/S02
- Supporting slices: none
- Validation: unmapped
- Notes: 当前仅 2 个 graphiti_core SDK 调用点（add_episode + search）

### R009 — Graphiti 检索精准度（3 层降级搜索 + ACP 组装）
- Class: core-capability
- Status: active
- Description: search_memories 3 层降级（Graphiti 语义→Neo4j fulltext→内存子串）能精确返回相关学习记忆。ACP 组装验证端到端数据链路。
- Why it matters: 检索不精准→出题不精准→考察无效
- Source: user, B3
- Primary owning slice: M001/S02
- Supporting slices: none
- Validation: unmapped
- Notes: 当前 3 层结果堆叠无统一 relevance 排序，Tier1 语义和 Tier3 子串平等对待

### R010 — LearningMemoryClient JSON 遗留清理 + graphiti_client.py stub 清理
- Class: quality-attribute
- Status: active
- Description: 消除 LearningMemoryClient（JSON 文件存储）在 6 个服务中的双写注入。清理 graphiti_client.py/graphiti_client_base.py 兼容 stub。所有记忆读写统一走 MemoryService→Graphiti 路径。
- Why it matters: 双写导致数据不一致，JSON 路径绕过 Graphiti 的语义能力
- Source: B3-DR, scout 扫描
- Primary owning slice: M001/S02
- Supporting slices: none
- Validation: unmapped
- Notes: LearningMemoryClient 仍注入 AgentService、ContextEnrichmentService、LearningContextService、ReviewService 等 6 处

### R011 — G-FAKE 42 假命名函数清理（Epic 3）
- Class: quality-attribute
- Status: active
- Description: 清理 42 个假命名函数（函数名含"graphiti"但实际调 Neo4j Cypher 或 JSON 文件）。Phase 4 残留命名清理。
- Why it matters: 假命名严重拖慢开发效率和 bug 追踪
- Source: B3-DR, known-gotchas G-FAKE-001
- Primary owning slice: M001/S02
- Supporting slices: none
- Validation: unmapped
- Notes: S34 已完成核心类重命名（17 项），残留在 API 模型名和 config 属性

### R012 — Episode ID 哈希扩展 [:16]→[:32]
- Class: quality-attribute
- Status: active
- Description: 确定性 Episode ID 使用 >= 32 位十六进制哈希，防止长期百万事件碰撞覆盖 FSRS 时间线。
- Why it matters: 数据完整性风险
- Source: B3-DR
- Primary owning slice: M001/S02
- Supporting slices: none
- Validation: unmapped
- Notes: 当前 hexdigest()[:16]

### R013 — Graph Temporal Compaction（90 天 CRON 清理失效边）
- Class: quality-attribute
- Status: active
- Description: 实现 90 天定期任务清理 t_invalid 失效边（序列化到冷存储 + Neo4j 硬删除）。修正 _calculate_complexity_score 仅计算活跃边。
- Why it matters: 防止图谱膨胀导致复杂度分数虚高和搜索性能退化
- Source: B3-DR, PRD 可扩展性章节
- Primary owning slice: M001/S02
- Supporting slices: none
- Validation: unmapped
- Notes: archive_scheduler.py 只处理对话消息，不清理图谱节点/边

### R060 — Graphiti 自定义 Entity/Edge Types
- Class: core-capability
- Status: active
- Description: 定义 LearningConcept/Mastery/Prerequisite 等 Pydantic 模型作为 add_episode 的 entity_types/edge_types 参数，让 Graphiti LLM 提取管道自动结构化学习数据。
- Why it matters: 当前 Graphiti 利用率仅 25%，自定义类型让提取更精准
- Source: user 确认, Graphiti API 审计
- Primary owning slice: M001/S02
- Supporting slices: none
- Validation: unmapped
- Notes: 当前 add_episode 仅使用 name/episode_body/group_id，未使用自定义类型

### R061 — Graphiti 高级搜索全量接入
- Class: core-capability
- Status: active
- Description: 接入 search_() + 4 种搜索配方（NODE_HYBRID_SEARCH_RRF、EDGE_HYBRID_SEARCH_CROSS_ENCODER、COMBINED_HYBRID_SEARCH_CROSS_ENCODER、EDGE_HYBRID_SEARCH_RRF）+ SearchFilters（DateFilter 时序过滤、node_labels 过滤、edge_types 过滤）+ center_node_uuid 图距离重排。
- Why it matters: 当前只用基础 search()，高级搜索支持时序查询和精确过滤
- Source: user 确认, Graphiti API 审计
- Primary owning slice: M001/S02
- Supporting slices: none
- Validation: unmapped
- Notes: 这是 Graphiti 最大的未利用能力

### R062 — Graphiti 社区检测（Leiden 算法）
- Class: core-capability
- Status: active
- Description: 接入 build_communities() 自动发现知识簇。可用于自动聚类相关概念（如"微积分相关概念"）。
- Why it matters: 无需手动分类，系统自动发现知识结构
- Source: user 确认, Graphiti API 审计
- Primary owning slice: M001/S02
- Supporting slices: none
- Validation: unmapped
- Notes: Leiden 算法自动聚类强关联节点并生成社区摘要

### R063 — Graphiti 批量摄入
- Class: core-capability
- Status: active
- Description: 接入 add_episode_bulk() 批量导入学习历史，大幅减少开销。
- Why it matters: 导入历史学习记录时效率提升
- Source: user 确认, Graphiti API 审计
- Primary owning slice: M001/S02
- Supporting slices: none
- Validation: unmapped
- Notes: 当前逐条 add_episode 通过 asyncio.Queue

### R064 — Graphiti 时间线检索
- Class: core-capability
- Status: active
- Description: 接入 retrieve_episodes() 获取有序学习活动时间线，支持学习活动回放视图。
- Why it matters: 学习时间线是学习档案的重要组成
- Source: user 确认, Graphiti API 审计
- Primary owning slice: M001/S02
- Supporting slices: none
- Validation: unmapped
- Notes: 支持按 group_id、source 类型、时间范围过滤

### R065 — AI 主动识别错误/疑问 → 强制写入 Graphiti
- Class: core-capability
- Status: active
- Description: AI 在对话过程中自动识别用户犯的错误和提出的疑问，强制写入 Graphiti 个人记忆系统。不仅等 MCP 工具触发（score_answer/record_error），每轮对话后都要检测并记录。
- Why it matters: 用户说"我们的记忆强制写入没有做到"
- Source: user 确认
- Primary owning slice: M001/S02
- Supporting slices: none
- Validation: unmapped
- Notes: 当前 PostToolUse BEA 提取仅对 score_answer 和 record_error 两个工具触发

### 检索系统

### R014 — RAG 端点修复
- Class: core-capability
- Status: active
- Description: RAG API 端点能返回真实笔记片段。当前端点级别不工作。
- Why it matters: 检索是所有上层功能的基石
- Source: user 反馈
- Primary owning slice: M001/S03
- Supporting slices: none
- Validation: unmapped
- Notes: src/agentic_rag（19K 行）是完整管道，backend/app/rag_service.py 已 import 并调用

### R015 — Reranker 中文适配
- Class: core-capability
- Status: active
- Description: 将 Reranker 从 gte-reranker-modernbert-base（英语为主）迁移至 Qwen3-Reranker-0.6B（中文原生多语言优化）。
- Why it matters: 英语 Reranker 对中文字符碎片化，严重降低中文检索精度
- Source: B1-DR
- Primary owning slice: M001/S03
- Supporting slices: none
- Validation: unmapped
- Notes: 当前 src/agentic_rag/reranking.py 使用 Alibaba-NLP/gte-reranker-modernbert-base

### R016 — Adaptive RAG Router
- Class: core-capability
- Status: active
- Description: 按查询复杂度选择检索通道（简单查询仅 LanceDB，时序查询触发 Graphiti，视觉查询触发 Multimodal），而非无条件 4 通道并行。
- Why it matters: 降低延迟、节约算力，简单问题不需要全通道搜索
- Source: B1-DR
- Primary owning slice: M001/S03
- Supporting slices: none
- Validation: unmapped
- Notes: 当前 state_graph.py 无条件 5 路并行扇出

### R017 — 中文搜索效果对齐
- Class: core-capability
- Status: active
- Description: jieba 已在 agentic_rag 中实现，需激活数据流入（笔记被正确索引到 LanceDB）并验证中英文搜索效果对齐（Recall@10 差距 <15%）。
- Why it matters: 中文搜索不工作则系统对中文用户无用
- Source: FR-RET-09, B1
- Primary owning slice: M001/S03
- Supporting slices: none
- Validation: unmapped
- Notes: Phase 3 Pipeline Repair 已完成 jieba 激活，但用户反馈 RAG 端点级不工作

### R018 — 笔记增量索引（文件指纹 + 去重）
- Class: core-capability
- Status: active
- Description: 文件变化检测 + 文件指纹比对只处理修改过的文件 + 旧索引清除。
- Why it matters: 修改 N 次笔记后仍只有 1 份索引
- Source: FR-RET-07
- Primary owning slice: M001/S03
- Supporting slices: none
- Validation: unmapped
- Notes: 当前纯追加无去重

### R019 — Per-白板笔记文件夹绑定
- Class: core-capability
- Status: active
- Description: 每个白板可绑定独立的笔记文件夹路径，Agent 检索以此为搜索范围。当前为全局设置。
- Why it matters: 不同白板=不同学科=不同索引范围
- Source: user 批注, FR-KG-08
- Primary owning slice: M002
- Supporting slices: none
- Validation: unmapped
- Notes: Settings.tsx 有路径配置但是全局的

### R020 — src/agentic_rag 与 backend/app/rag_service 关系梳理
- Class: quality-attribute
- Status: active
- Description: 梳理两套系统关系：src/agentic_rag（19K 行完整管道）是实际执行引擎，backend/app/rag_service.py 是调用入口。agent_graph.py（Phase 3 Agent 图）是孤儿代码需接入。
- Why it matters: 架构清晰度直接影响维护效率
- Source: scout 扫描
- Primary owning slice: M001/S03
- Supporting slices: none
- Validation: unmapped
- Notes: agent_graph.py 完整但从未被任何端点调用

### R021 — 检索上下文压缩（保护代码/公式）+ 面包屑前缀
- Class: quality-attribute
- Status: active
- Description: 分块保护代码块/数学公式/表格不被切断，每个分块附带面包屑路径前缀（文档>章节>小节）。
- Why it matters: 代码/公式被切断则检索结果无用
- Source: FR-RET-08, FR-RET-12
- Primary owning slice: M002
- Supporting slices: none
- Validation: unmapped
- Notes: compression.py 已有原子块保护（代码/公式/表格正则），面包屑前缀未实现

### R022 — CRAG 吸收进 Reranker 置信度
- Class: quality-attribute
- Status: active
- Description: 消除独立 CRAG LLM 评估步骤，改用 Reranker 输出置信度分数触发质量阈值，降低 >150ms 延迟。
- Why it matters: 降低检索延迟
- Source: B1-DR
- Primary owning slice: M001/S03
- Supporting slices: none
- Validation: unmapped
- Notes: 当前 check_quality 节点使用独立 LLM 二元评分

### 检验白板 + 考试

### R023 — 检验白板考察全链路
- Class: core-capability
- Status: active
- Description: 出题（FSRS+BKT+KG 三角选择 + ACP + 5 层 Prompt）→ 评分（AutoSCORE 4 维 SOLO）→ BKT/FSRS 更新 → 精通度变化可视化。
- Why it matters: 核心差异化功能——递归考察检验
- Source: FR-EXAM-01~04
- Primary owning slice: M001/S04
- Supporting slices: none
- Validation: unmapped
- Notes: 后端算法代码全部已实现（question_generator、autoscore、mastery_engine），需端到端验证

### R024 — 新节点继承原白板属性 + 实时可见同步回原白板
- Class: core-capability
- Status: active
- Description: 检验白板中拉出的新节点自动继承原白板的 subject/canvas_id/group_id。数据变更（Tips/新节点/精通度）实时同步回原白板，原白板上实时可见变化。
- Why it matters: 检验白板和原白板是一体的学习闭环
- Source: user 确认, FR-EXAM-05, FR-EXAM-18
- Primary owning slice: M001/S04
- Supporting slices: none
- Validation: unmapped
- Notes: 原白板上如何呈现实时变化需要设计

### R025 — 节点切换时自动触发隐形评分
- Class: core-capability
- Status: active
- Description: 检验白板中 Agent 考完当前节点切换到下一个时，后台自动对已讨论节点执行 AutoSCORE 4 维评分并更新 BKT/FSRS。评分对用户隐形，通过节点颜色变化传达。
- Why it matters: 无缝的学习体验——评分不打断考察流程
- Source: FR-EXAM-16
- Primary owning slice: M001/S04
- Supporting slices: none
- Validation: unmapped
- Notes: 当前无任何 "node switch → auto-score" 事件处理代码

### R026 — 考试 AI 推荐节点设安全阀
- Class: quality-attribute
- Status: active
- Description: AI 自动推荐的新概念节点设安全阀（5-10 个/会话上限），用户手动拉出不限数量。
- Why it matters: 防止 AI 无限生成节点导致 UI 混乱和 KG 噪音
- Source: B4-DR, user 确认
- Primary owning slice: M001/S04
- Supporting slices: none
- Validation: unmapped
- Notes: 用户明确：手动拉出不限，AI 推荐设限

### R027 — 考后审查门控
- Class: quality-attribute
- Status: active
- Description: 新节点需用户确认才写入知识图谱，防止污染 KG。
- Why it matters: 数据质量保障
- Source: B4-DR
- Primary owning slice: M001/S04
- Supporting slices: none
- Validation: unmapped
- Notes: 考后审查面板本身已废弃（FR-EXAM-10），但门控机制保留

### R028 — 4 级渐进提示（Chain-of-Hints）
- Class: core-capability
- Status: active
- Description: Level 1 方向提示→Level 2 关键词→Level 3 部分答案框架→Level 4 分步脚手架引导。不提供"直接告诉答案"。可选"跳过这题"（不惩罚 BKT）。
- Why it matters: 帮助学生在不直接给答案的情况下逐步理解
- Source: FR-EXAM-19
- Primary owning slice: M001/S04
- Supporting slices: none
- Validation: unmapped
- Notes: HintButton.tsx + hint_level1-4.md 已实现

### R029 — 动态置信度评分路由
- Class: quality-attribute
- Status: active
- Description: 默认 1x CoT Rubric 评分，仅低置信度（max-min>1）时触发 3x 采样多数投票。降低 2/3 评分 API 成本。
- Why it matters: 降本增效——大部分题目 1x 评分已够准确
- Source: B6-DR
- Primary owning slice: M001/S04
- Supporting slices: none
- Validation: unmapped
- Notes: 当前 autoscore.py 默认每次都 3x 采样

### 精通度

### R030 — 5 信号融合→单维掌握度
- Class: core-capability
- Status: active
- Description: BKT(0.30) + FSRS_R(0.25) + ExamScore(0.25) + CalibrationBias(0.10) + SelfConfidence(0.10) 加权平均融合为单维掌握度。互补性 |r| < 0.7。
- Why it matters: 精通度是学习追踪和出题的基础
- Source: FR-MAST-06, B2
- Primary owning slice: M001/S04
- Supporting slices: none
- Validation: unmapped
- Notes: MasteryFusionEngine + SignalRegistry 已实现，MVP 用加权平均，Phase 2 升级 Beta-Bayesian

### R031 — 冷启动阈值修订
- Class: quality-attribute
- Status: active
- Description: <100 数据点禁用元认知惩罚（Calibration Bias 和 Self-Confidence 权重设为 0，仅用软性定性提示）/ 100-400 趋势期 / 400+ 统计可靠期。当前 <10/10-20/20+ 阈值统计无效。
- Why it matters: 低样本量下元认知指标是噪音不是信号
- Source: B2+B6-DR
- Primary owning slice: M001/S04
- Supporting slices: none
- Validation: unmapped
- Notes: calibration_tracker.py 当前用 <10/10-20/20+ 三阶段

### R032 — 精通度可视化
- Class: primary-user-loop
- Status: active
- Description: 节点精通度色条（左侧）+ 进度条（底部）+ 处方性展示（"建议复习 X"）。精通度颜色与用户手动标记颜色分离——两套颜色互不干扰。
- Why it matters: 用户感知精通度变化的主要途径
- Source: FR-MAST-03, user 确认颜色分离
- Primary owning slice: M002
- Supporting slices: none
- Validation: unmapped
- Notes: KnowledgeNode.tsx 当前无精通度色条/进度条 UI

### R033 — Calibration Tracking（Area9 2x2 + 三阶段渐进）
- Class: differentiator
- Status: active
- Description: Area9 式 2x2 置信度矩阵（掌握/误解/运气/未学）。数据通过考察前 AI 口头询问"你觉得自己会吗？"收集。三阶段渐进：<100 仅收集 / 100-400 趋势 / 400+ 统计可靠。不使用 DK 标签。
- Why it matters: 识别"以为会了其实不会"的危险盲区
- Source: FR-MAST-05, user 确认口头询问形式
- Primary owning slice: M002
- Supporting slices: none
- Validation: unmapped
- Notes: calibration_tracker.py 已实现 2x2 分类和三阶段

### 算法管道

### R034 — LangGraph 原生 Checkpointer 恢复
- Class: quality-attribute
- Status: active
- Description: 迁移至 LangGraph 原生 PostgresSaver/SQLiteSaver 处理执行状态持久化，消除自定义 JSON/Neo4j 回退的竞态条件风险。
- Why it matters: 自定义状态管理丢失了时间旅行和可靠恢复能力
- Source: B5-DR
- Primary owning slice: M002
- Supporting slices: none
- Validation: unmapped
- Notes: 当前 FallbackSyncService + JSON 锁文件绕过 LangGraph 原生持久化

### R035 — EventBus 两个 stub handler 补全
- Class: quality-attribute
- Status: active
- Description: handle_rag_weight_adjust（RAG 权重调整→LanceDB 实际写入）和 handle_ui_mastery_push（WebSocket 精通度推送→前端实时更新）从 log-only 补全为真实实现。
- Why it matters: 数据管道完整性
- Source: scout 扫描
- Primary owning slice: M002
- Supporting slices: none
- Validation: unmapped
- Notes: event_handlers.py 中这两个 handler 仅 log 无实际功能

### R036 — Prompt 管道统一
- Class: quality-attribute
- Status: active
- Description: agent_service.py 可能存在的 4 路 Prompt 分叉统一为 1 条管道。
- Why it matters: 减少维护负担和行为不一致
- Source: Brainstorming Session 4
- Primary owning slice: M002
- Supporting slices: none
- Validation: unmapped
- Notes: 需进一步审查确认是否仍有 4 路分叉

### R037 — BKT 维持 MVP + Phase 3 评估替代
- Class: constraint
- Status: active
- Description: BKT 维持用于 MVP（可解释性优先）。Phase 3 评估 LKT/SAINT+ 替代（深度学习精度更高但黑箱）。
- Why it matters: BKT 对 MVP 足够，但长期可能需要升级
- Source: B2-DR
- Primary owning slice: M002+
- Supporting slices: none
- Validation: unmapped
- Notes: BKT 4 参数 HMM 在纯预测 AUC 上已被超越，但可解释性适合教育场景

### Edge / 拉出 / 技能

### R038 — Edge 对话双重策略（EI+SE）
- Class: differentiator
- Status: active
- Description: Edge 对话同时激活精细化追问（Elaborative Interrogation）和自我解释（Self-Explanation）。3-4 轮密度控制。Edge 对话属于原白板剖析功能，不属于验证/考察。Edge 对话不蒸馏，产出直接存为结构化 Edge 语义标签。
- Why it matters: 全球独创——连线对话叠加两种学习策略
- Source: FR-EDGE-01~04, user 确认不蒸馏
- Primary owning slice: M002
- Supporting slices: none
- Validation: unmapped
- Notes: Active Recall 归属检验白板（原白板 Edge 可见不构成回忆检索）

### R039 — 对话拉出节点 + 自动建议关系
- Class: core-capability
- Status: active
- Description: 选取对话文字拖出为新知识节点，系统自动建议与原节点的关系类型。
- Why it matters: 对话中的洞见能快速转化为知识图谱节点
- Source: FR-CONV-08
- Primary owning slice: M002
- Supporting slices: none
- Validation: unmapped
- Notes: usePullToNode.ts + SelectionToolbar.tsx 已实现

### R040 — /命令技能系统 + 对标 Claude Code 命令全量迁移
- Class: core-capability
- Status: active
- Description: 预装学习辅助技能（拆解/解释/对比/记忆/练习/检验）+ 可扩展注册机制。对标 Claude Code 原生 /命令集全量迁移到对话框。
- Why it matters: 用户说"现在并没有完全迁移 claude code 的所有命令"
- Source: FR-SKILL-01~05, user 确认对标迁移
- Primary owning slice: M002
- Supporting slices: none
- Validation: unmapped
- Notes: SkillSelector.tsx + skill_registry.py 已有框架

### UI / 系统

### R041 — 前端 1730 TS 错误修复
- Class: quality-attribute
- Status: active
- Description: 修复 frontend/ 中 1730 个 TypeScript 错误（主要是隐式 any 类型），建立类型安全基线。
- Why it matters: 类型安全是代码质量的基础
- Source: user
- Primary owning slice: M001/S01
- Supporting slices: none
- Validation: unmapped
- Notes: 主要集中在 mastery-store.ts 等 store 文件

### R042 — 垃圾文件全量清理
- Class: quality-attribute
- Status: active
- Description: 清理根目录 7 个 Windows temp 泄漏文件 + backend/ 13 个乱码文件 + _archive/_bmad-output 中过时工件。
- Why it matters: 代码库卫生
- Source: user
- Primary owning slice: M001/S01
- Supporting slices: none
- Validation: unmapped
- Notes: UsersHeishingAppDataLocalTemp* + backend/햎/ÃÏ/Ð 等

### R043 — Mac 为 M001 主要平台
- Class: constraint
- Status: active
- Description: M001 专注 Mac（M5 Max + 128GB）。Windows 支持延后到 M002+。当前 Windows 代码分支（isWindows()、taskkill 等）保留不删除但不在 M001 验证。
- Why it matters: 聚焦主要平台，避免分散精力
- Source: user 确认
- Primary owning slice: M001 cross-cutting
- Supporting slices: none
- Validation: unmapped
- Notes: Rust 1.94.1 已安装（aarch64-apple-darwin），Ollama 原生 Metal GPU

### R044 — 学习档案面板完整闭环
- Class: primary-user-loop
- Status: active
- Description: 节点 Profile 面板包含：精通度 + Tips（可展开看来源对话）+ "需要加强方向"（正面措辞）+ QA 精选 + 考察记录列表（哪次考试考过/得分）+ 错误历史时间线 + 点击跳转到对话/白板 + 启动单节点考察入口（FR-EXAM-17）。
- Why it matters: 用户描述的完整学习闭环核心
- Source: FR-TRACE-01~05, FR-EXAM-17, user 确认考察记录+跳转
- Primary owning slice: M002
- Supporting slices: none
- Validation: unmapped
- Notes: LearningProfile.tsx 已有 Tips/弱点/QA，缺少考察记录和跳转

### R045 — Dashboard 完整版
- Class: primary-user-loop
- Status: active
- Description: 白板列表 + 检验白板列表 + 历史检验白板列表（时间/掌握度变化/考察节点数）+ 从 Dashboard 启动检验白板考察入口。
- Why it matters: 学习管理的中心
- Source: FR-DASH-01~04, FR-EXAM-20
- Primary owning slice: M002
- Supporting slices: none
- Validation: unmapped
- Notes: App.tsx 有白板切换但无独立 Dashboard 页面

### R046 — Catppuccin Mocha 深色主题全局应用
- Class: launchability
- Status: active
- Description: 将 Catppuccin Mocha 暗色主题应用到所有组件。当前仅局部组件（NodeContextMenu、ToolCallCard）使用深色。
- Why it matters: PRD 设计决策 DE-2，用户反馈"一直是浅色 UI"
- Source: user, PRD NFR
- Primary owning slice: M002
- Supporting slices: none
- Validation: unmapped
- Notes: TailwindCSS v4 CSS 变量体系已在 devDependencies

### R047 — 系统健康面板 + 安装引导向导
- Class: launchability
- Status: active
- Description: 首次使用安装引导（5 步检测：Docker→后端→Neo4j→LLM API Key→首个白板）+ 常驻健康面板（Docker/后端/Neo4j/LLM/LanceDB 5 组件状态）。
- Why it matters: 新用户首次体验的关键
- Source: FR-SYS-01, FR-SYS-04
- Primary owning slice: M002
- Supporting slices: none
- Validation: unmapped
- Notes: StatusBar.tsx 和 health.py 已有基础框架

### R048 — 模型配置面板
- Class: launchability
- Status: active
- Description: 配置 LLM 供应商和 API Key + 为不同任务（对话/评分/Embedding）指定不同模型。对话框内可通过 / 命令切换模型。
- Why it matters: 模型灵活性是 PRD 核心设计原则
- Source: FR-SYS-02~03, FR-SYS-09
- Primary owning slice: M002
- Supporting slices: none
- Validation: unmapped
- Notes: Settings.tsx 有 API Key 配置，per-task 模型选择和 / 命令切换未实现

### R049 — 双上下文系统统一
- Class: quality-attribute
- Status: active
- Description: context_enrichment_service.py（读 .canvas 文件边，静态图）vs learning_context_service.py（读 Neo4j，动态图）两套独立上下文系统需要统一或明确边界。
- Why it matters: 两套系统并存导致混乱
- Source: scout 扫描
- Primary owning slice: M002
- Supporting slices: none
- Validation: unmapped
- Notes: 注入 Claude system prompt 的是 learning_context_service（via /api/v1/context/{nodeId}）

### R050 — 考察记录永久保存 + Dashboard 查看
- Class: continuity
- Status: active
- Description: 每个检验白板的完整考察记录（对话/评分/精通度变化/新发现节点）永久保存。Dashboard 可查看所有历史检验白板。
- Why it matters: 学习历史不可丢失
- Source: FR-EXAM-20
- Primary owning slice: M002
- Supporting slices: none
- Validation: unmapped
- Notes: exam_sessions.py API 存在，前端 Dashboard 视图不完整

### Graphiti 全量接入（续）

### R066 — 节点 Profile 完整闭环（考察记录 + 错误时间线 + 跳转）
- Class: primary-user-loop
- Status: active
- Description: 点击节点查看 Profile 面板时，除了现有的 Tips/弱点/QA，新增：考察记录列表（哪次考试考过、得分）+ 错误历史按时间排列 + 点击错误/疑惑→跳转到当时的对话/考试白板。
- Why it matters: 用户在 MVP #7 详细描述的完整学习闭环
- Source: user 确认
- Primary owning slice: M002
- Supporting slices: none
- Validation: unmapped
- Notes: 需要记录每条错误的 source_session_id + source_canvas_id 支持跳转

### R067 — Session 手动命名 + /resume 导航
- Class: core-capability
- Status: active
- Description: 用户可为对话 session 命名/重命名。/resume 命令显示 session-节点映射关系（含命名），支持快速导航。
- Why it matters: 不命名就很难找到 session
- Source: user 确认
- Primary owning slice: M002
- Supporting slices: none
- Validation: unmapped
- Notes: 合并 R005 的 session 管理需求

### R068 — 对标 Claude Code 注册所有 /命令
- Class: core-capability
- Status: active
- Description: 对标 Claude Code / Claudian 的原生 /命令集，全量迁移到对话框。
- Why it matters: 用户反复要求
- Source: user 确认
- Primary owning slice: M002
- Supporting slices: none
- Validation: unmapped
- Notes: 合并到 R040

### R069 — 前端压缩指示 + 完整对话历史呈现
- Class: core-capability
- Status: active
- Description: 前端对话窗口同时显示完整对话历史（从 Dexie 加载）和压缩指示（标记哪里被 SDK 压缩了）。用户能感知压缩状态。
- Why it matters: 用户要知道上下文被压缩了，同时能看到完整历史
- Source: user 确认
- Primary owning slice: M002
- Supporting slices: none
- Validation: unmapped
- Notes: 当前 chat-store.ts 有 compact_boundary 事件处理，显示系统消息

### R070 — 检验白板→原白板实时可见同步
- Class: core-capability
- Status: active
- Description: 检验白板中的数据变更（Tips/Tag 标注/新节点/精通度更新）实时同步回原白板，原白板上新节点实时出现、精通度色条实时更新。
- Why it matters: 学习闭环的可见性
- Source: user 确认
- Primary owning slice: M001/S04
- Supporting slices: none
- Validation: unmapped
- Notes: 用户确认要实时可见变化

### R071 — Graph Temporal Compaction（与 R013 合并）
- Class: quality-attribute
- Status: active
- Description: 与 R013 相同，90 天 CRON 清理失效边。
- Why it matters: 同 R013
- Source: scout, B3-DR
- Primary owning slice: M001/S02
- Supporting slices: none
- Validation: unmapped
- Notes: 合并到 R013，此条可删除

### R072 — search_memories 跨层 relevance 统一排序 + FSRS R 值注入
- Class: core-capability
- Status: active
- Description: search_memories 3 层结果合并后按统一 relevance score 排序（Tier1 Graphiti score / Tier2 fulltext score / Tier3 固定低分），并注入 FSRS 可检索度 R 值作为 reranking 信号。低 R 概念的相关记忆应被优先返回。
- Why it matters: 当前结果堆叠无排序，语义搜索和子串匹配平等对待
- Source: scout 扫描
- Primary owning slice: M001/S02
- Supporting slices: none
- Validation: unmapped
- Notes: R 用于题目选择但不用于记忆检索排序

### R073 — Obsidian 笔记片段跳转 + 未安装时内置降级
- Class: core-capability
- Status: active
- Description: Agent 引用笔记时双向链接支持文件级/章节级/块级三种精度跳转（obsidian://open + obsidian://adv-uri）。Obsidian 未安装时降级为内置 Markdown 渲染器显示目标文件。
- Why it matters: 精确笔记片段跳转是检索系统的最终交付
- Source: FR-RET-13, user 确认降级, researcher 验证技术可行
- Primary owning slice: M002
- Supporting slices: none
- Validation: unmapped
- Notes: obsidian-link.ts 已有骨架，tauri-plugin-shell 已配置 obsidian:// 协议

### R074 — 已废弃代码清理
- Class: quality-attribute
- Status: active
- Description: 删除 CognitiveLoadTimer 后端 API（/exam/{id}/cognitive-load 端点 + COGNITIVE_LOAD_* 常量 + get_cognitive_load_message()）+ ExamSummary 总用时显示。
- Why it matters: 已废弃功能的代码残留导致混乱
- Source: user 确认, 决策 GDA-5
- Primary owning slice: M001/S01
- Supporting slices: none
- Validation: unmapped
- Notes: 前端 CognitiveLoadTimer 组件已删除，后端残留

### R075 — Edge 对话不蒸馏
- Class: constraint
- Status: active
- Description: Edge 对话的产出直接存为结构化 Edge 语义标签（理由记录），不走 LLM 蒸馏。只有节点对话需要蒸馏。
- Why it matters: Edge 产出本身就是结构化的，无需再提取
- Source: user 确认
- Primary owning slice: M002
- Supporting slices: none
- Validation: unmapped
- Notes: 当前 conversation_distiller.py 可能不区分 Edge vs 节点对话

### R076 — 蒸馏模型可选 Opus + 对话框内模型可切换
- Class: core-capability
- Status: active
- Description: 对话历史蒸馏可选用 Claude Opus 做高质量摘要（当前 Tier1 Qwen3 8B→Tier2 Haiku→Tier3 LiteLLM）。对话框内用户可通过 /命令 切换活跃 LLM 模型。
- Why it matters: Opus 蒸馏质量最高，模型切换提供灵活性
- Source: user 确认
- Primary owning slice: M002
- Supporting slices: none
- Validation: unmapped
- Notes: conversation_distiller.py 的 3-tier cascade 需增加 Opus 选项

### R077 — 后端压缩改用 LLM 语义摘要
- Class: quality-attribute
- Status: active
- Description: 后端 3 处暴力截断（learning_context_service.py section pop / compression.py extractive / question_generator.py 字段截断）改用 LLM 语义摘要（参考 Claude Code 泄漏的压缩算法）。对话中压缩维持 SDK 原生。
- Why it matters: 暴力截断丢失语义关键信息
- Source: user 确认
- Primary owning slice: M002
- Supporting slices: none
- Validation: unmapped
- Notes: 需要研究 Claude Code 泄漏的压缩算法细节

### R078 — 多 hop 对话摘要继承
- Class: core-capability
- Status: active
- Description: A→B→C 链式连接时，C 能看到 A 的对话摘要（通过递归蒸馏或摘要链路）。当前只有 1-hop。
- Why it matters: 知识链路中远端概念的上下文也很重要
- Source: user 确认
- Primary owning slice: M002
- Supporting slices: none
- Validation: unmapped
- Notes: conversation_inheritance.py 当前 MATCH 1-hop only

### R079 — 多邻居智能排序
- Class: core-capability
- Status: active
- Description: 当节点有 5+ 邻居时，按相关性×时间×精通度缺口综合评分选择 Top-N 注入（而非随机取前 2 个）。Neo4j 查询需增加 ORDER BY。
- Why it matters: 选错邻居注入等于注入噪音
- Source: user 确认, FR-CONV-11
- Primary owning slice: M002
- Supporting slices: none
- Validation: unmapped
- Notes: 当前 MAX_INHERITED_NEIGHBORS=2，Neo4j 查询无 ORDER BY

### 安全+可靠性（本轮新增）

### R080 — 数据零丢失 RPO=0
- Class: quality-attribute
- Status: active
- Description: 用户操作后 1s 内同步确认写入后端。崩溃恢复后最后操作已持久化。
- Why it matters: 学习数据不可丢失
- Source: PRD NFR 可靠性
- Primary owning slice: M001 cross-cutting
- Supporting slices: none
- Validation: unmapped
- Notes: fallback_sync_service.py + Dexie outbox 有基础

### R081 — LLM 断连降级
- Class: quality-attribute
- Status: active
- Description: 断连检测 <5s + 断连后白板操作延迟不变（<16ms）+ 前端显示"离线模式：AI 功能暂不可用" + FSRS 复习提醒正常。
- Why it matters: LLM 不可用时系统不应崩溃
- Source: PRD NFR 可靠性
- Primary owning slice: M001 cross-cutting
- Supporting slices: none
- Validation: unmapped
- Notes: health_monitor.py 有健康检查，但无前端"离线模式"UI

### R082 — Neo4j 异常降级
- Class: quality-attribute
- Status: active
- Description: Neo4j 异常时写操作队列暂存（上限 1000 条或 24h），超出告警。恢复后自动重放。
- Why it matters: 数据库暂时不可用不应阻断用户操作
- Source: PRD NFR 可靠性
- Primary owning slice: M001 cross-cutting
- Supporting slices: none
- Validation: unmapped
- Notes: fallback_sync_service.py 已有 JSONL 队列+恢复

### R083 — 错误不静默
- Class: quality-attribute
- Status: active
- Description: 所有 HTTP 4xx/5xx 在 UI 2s 内展示错误提示。无静默失败。
- Why it matters: 用户需要知道发生了什么
- Source: PRD NFR 可靠性
- Primary owning slice: M001 cross-cutting
- Supporting slices: none
- Validation: unmapped
- Notes: RecoveryBanner.tsx 存在，需验证覆盖度

### R084 — 双层 Key 分离
- Class: quality-attribute
- Status: active
- Description: 外层 Agent Key（用户自己的 Claude 订阅额度，用于对话）vs 内层后端 Key（后端配置的 Gemini/OpenAI Key，用于评分/提取/索引）。两套 Key 独立配置、独立作用域、不可互相读取。
- Why it matters: 安全隔离 + 成本可控
- Source: PRD 模型灵活性
- Primary owning slice: M001 cross-cutting
- Supporting slices: none
- Validation: unmapped
- Notes: 当前 Settings.tsx 只有单一 API Key 配置

### R085 — Layer 3 回退策略
- Class: quality-attribute
- Status: active
- Description: 每个 Layer 3 创新功能异常时自动降级：Edge 对话→静态标签边 / 检验白板递归→单轮考察 / 元认知校准→单一精通度百分比 / 对话拉出节点→手动创建。向用户通知降级状态。
- Why it matters: 创新功能不稳定时不应让整个系统不可用
- Source: PRD Layer 3 回退表
- Primary owning slice: M002
- Supporting slices: none
- Validation: unmapped
- Notes: 当前 FR 只定义正常路径，无降级条件和退化行为

### 算法+架构（本轮新增）

### R086 — 错误类型→出题策略映射
- Class: core-capability
- Status: active
- Description: 4 类错误→差异化出题策略作为独立需求：破题错误→同结构换包装 / 推理谬误→反例诱导 / 知识点缺失→回退定义题 / 似懂非懂→辨析迁移题。
- Why it matters: 差异化补救是考察精准度的关键
- Source: PRD 算法架构, B4
- Primary owning slice: M001/S04
- Supporting slices: none
- Validation: unmapped
- Notes: question_generator.py 的 REMEDIATION_STRATEGIES 已实现，需作为独立需求追踪

### R087 — BKT/FSRS 冷启动策略
- Class: core-capability
- Status: active
- Description: 新用户使用默认先验值启动（无冷启动诊断题）。通过前几次自然交互渐进建立学习画像。Agent 在低数据量下行为定义（不引用个人数据，仅通用教学）。
- Why it matters: 新用户首次体验不应有诊断测试
- Source: PRD 旅程 4, 决策"冷启动诊断→删除"
- Primary owning slice: M001/S04
- Supporting slices: none
- Validation: unmapped
- Notes: 决策 V-01 已确认删除冷启动诊断

### R088 — 功能引导 Onboarding
- Class: launchability
- Status: active
- Description: 首次连线时弹出 Edge 对话引导提示 + 首次节点对话时引导 + 功能发现提示。区别于 R047 的系统安装引导。
- Why it matters: 功能引导帮助用户发现核心功能
- Source: PRD 旅程 4
- Primary owning slice: M002
- Supporting slices: none
- Validation: unmapped
- Notes: FR-SYS-01 只覆盖安装引导，不覆盖 in-app 功能引导

### 用户批注补充（本轮新增）

### R089 — 疑惑节点归类
- Class: core-capability
- Status: active
- Description: AI 识别到用户疑惑时，记录必须明确归类到引发疑惑的源节点。不是自动创建节点，而是确保疑惑记录有明确的节点归属。
- Why it matters: 疑惑归类不准则后续考察不精准
- Source: user 确认
- Primary owning slice: M001/S02
- Supporting slices: none
- Validation: unmapped
- Notes: 用户明确：疑问节点由用户手动创建，AI 负责归类

### R090 — Per-白板索引状态可视化
- Class: core-capability
- Status: active
- Description: 每个白板独立显示索引进度/完成/失败状态。当前 FR-KG-07 的四种状态指示是全局的，需改为 per-board。
- Why it matters: 不同白板=不同学科=不同索引状态
- Source: user 批注
- Primary owning slice: M002
- Supporting slices: none
- Validation: unmapped
- Notes: 与 R019 per-白板路径绑定配合

### R091 — Graphiti 写入兜底
- Class: quality-attribute
- Status: active
- Description: Graphiti 写入失败时：3 次指数退避重试→JSON 降级写入→Hook 拦截保证零数据丢失。
- Why it matters: 记忆数据不可丢失
- Source: user 确认
- Primary owning slice: M001/S02
- Supporting slices: none
- Validation: unmapped
- Notes: episode_worker.py 已有 3-retry + dead-letter JSONL，需验证端到端

### R092 — 薄弱方向跳转
- Class: primary-user-loop
- Status: active
- Description: FR-TRACE-03 "需要加强方向"条目可点击跳转到具体对话片段（与 FR-TRACE-02 Tips 来源追溯对齐）。
- Why it matters: 用户在旅程 6 中描述"点击一条'需要加强'，直接跳转到对应的对话片段"
- Source: PRD 旅程 6, user 确认
- Primary owning slice: M002
- Supporting slices: none
- Validation: unmapped
- Notes: FR-TRACE-02（Tips）有来源对话追溯，FR-TRACE-03（薄弱方向）缺跳转

---

## Deferred

### R051 — Beta-Bayesian 融合替代静态加权平均
- Class: differentiator
- Status: deferred
- Description: Phase 2 升级为 Beta-Bayesian 融合，捕捉信号间协方差关系。
- Why it matters: 加权平均过于简单，假设信号线性独立
- Source: B2-DR
- Primary owning slice: M003+
- Supporting slices: none
- Validation: unmapped
- Notes: MasteryFusionEngine 注释保留 Phase 2+ 升级路径

### R052 — 多学科隔离
- Class: core-capability
- Status: deferred
- Description: group_id + subject 字段隔离不同学科知识图谱。
- Why it matters: 同时学多门课需要隔离
- Source: PRD Phase 2
- Primary owning slice: M003+
- Supporting slices: none
- Validation: unmapped
- Notes: subject_config.py 已有 stub

### R053 — 自动备份与恢复
- Class: continuity
- Status: deferred
- Description: 每日自动备份 + 手动触发 + 一键恢复（RTO <5min）。
- Why it matters: 数据安全保障
- Source: PRD Phase 2
- Primary owning slice: M003+
- Supporting slices: none
- Validation: unmapped
- Notes: backup-manager.ts 已存在

### R054 — 图片节点内行内混排
- Class: core-capability
- Status: deferred
- Description: 节点内容区域支持文本+图片混排（对标 Obsidian Canvas）。
- Why it matters: 丰富的内容类型
- Source: FR-KG-09
- Primary owning slice: M002+
- Supporting slices: none
- Validation: unmapped
- Notes: 当前仅独立图片节点

### R055 — LKT/SAINT+ 知识追踪升级
- Class: differentiator
- Status: deferred
- Description: Phase 3+ 评估用语义理解替代数值 ID 的知识追踪模型。
- Why it matters: 深度学习精度更高
- Source: B2-DR
- Primary owning slice: M003+
- Supporting slices: none
- Validation: unmapped
- Notes: BKT 可解释性优先 MVP

### R056 — 动态信号权重 ML 优化器
- Class: differentiator
- Status: deferred
- Description: 用机器学习层替代静态权重分配。
- Why it matters: 数据量足够后可自适应调优
- Source: B2-DR
- Primary owning slice: M003+
- Supporting slices: none
- Validation: unmapped
- Notes: 需要足够样本量训练

### R093 — Dashboard LLM/Embedding 模型管理面板
- Class: launchability
- Status: deferred
- Description: Dashboard 上查看各 LLM/Embedding 模型运行状态、在线/离线、本地运行情况，前端和后端同步管理。
- Why it matters: 用户强烈要求但决策 GDA-7 放 Phase 4
- Source: user, 决策 GDA-7
- Primary owning slice: M002+
- Supporting slices: none
- Validation: unmapped
- Notes: 用户语气强烈但协商后延后

---

## Out of Scope

### R057 — 移动端支持
- Class: constraint
- Status: out-of-scope
- Description: 不支持移动端（依赖本地 Docker 运行 Neo4j + FastAPI）。
- Why it matters: 明确排除避免范围蔓延
- Source: PRD 明确排除
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: none

### R058 — 多用户/SaaS
- Class: constraint
- Status: out-of-scope
- Description: 个人使用，非多用户系统。
- Why it matters: 架构决策——单用户场景无需多租户
- Source: 个人使用
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: none

### R059 — CognitiveLoadTimer（计时功能）
- Class: constraint
- Status: out-of-scope
- Description: 计时功能已被用户抛弃（决策 GDA-5）。
- Why it matters: 避免复活已否决功能
- Source: 决策 GDA-5
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: 后端代码残留需清理（R074）

---

## Traceability

| ID | Class | Status | Primary Owner | Priority | Proof |
|---|---|---|---|---|---|
| R001 | core-capability | active | M001/S01 | 🔴 高 | mapped |
| R002 | core-capability | active | M001/S03 | 🔴 高 | mapped |
| R003 | core-capability | active | M001/S03 | 🔴 高 | mapped |
| R004 | core-capability | active | M002 | 🟡 中 | mapped |
| R005 | core-capability | active | M002 | 🟡 中 | mapped |
| R006 | core-capability | active | M002 | 🟡 中 | mapped |
| R007 | continuity | active | M002 | 🟡 中 | mapped |
| R008 | core-capability | active | M001/S02 | 🔴 高 | mapped |
| R009 | core-capability | active | M001/S02 | 🔴 高 | mapped |
| R010 | quality-attribute | active | M001/S02 | 🔴 高 | mapped |
| R011 | quality-attribute | active | M001/S02 | 🔴 高 | mapped |
| R012 | quality-attribute | active | M001/S02 | 🟡 中 | mapped |
| R013 | quality-attribute | active | M001/S02 | 🔴 高 | mapped |
| R014 | core-capability | active | M001/S03 | 🔴 高 | mapped |
| R015 | core-capability | active | M001/S03 | 🔴 高 | mapped |
| R016 | core-capability | active | M001/S03 | 🟡 中 | mapped |
| R017 | core-capability | active | M001/S03 | 🔴 高 | mapped |
| R018 | core-capability | active | M001/S03 | 🟡 中 | mapped |
| R019 | core-capability | active | M002 | 🟡 中 | mapped |
| R020 | quality-attribute | active | M001/S03 | 🟡 中 | mapped |
| R021 | quality-attribute | active | M002 | 🟡 中 | mapped |
| R022 | quality-attribute | active | M001/S03 | 🟡 中 | mapped |
| R023 | core-capability | active | M001/S04 | 🔴 高 | mapped |
| R024 | core-capability | active | M001/S04 | 🔴 高 | mapped |
| R025 | core-capability | active | M001/S04 | 🔴 高 | mapped |
| R026 | quality-attribute | active | M001/S04 | 🟡 中 | mapped |
| R027 | quality-attribute | active | M001/S04 | 🟡 中 | mapped |
| R028 | core-capability | active | M001/S04 | 🟡 中 | mapped |
| R029 | quality-attribute | active | M001/S04 | 🟡 中 | mapped |
| R030 | core-capability | active | M001/S04 | 🟡 中 | mapped |
| R031 | quality-attribute | active | M001/S04 | 🔴 高 | mapped |
| R032 | primary-user-loop | active | M002 | 🟡 中 | mapped |
| R033 | differentiator | active | M002 | 🟡 中 | mapped |
| R034 | quality-attribute | active | M002 | 🟡 中 | mapped |
| R035 | quality-attribute | active | M002 | 🟡 中 | mapped |
| R036 | quality-attribute | active | M002 | 🟡 中 | mapped |
| R037 | constraint | active | M002+ | 🟢 低 | mapped |
| R038 | differentiator | active | M002 | 🟡 中 | mapped |
| R039 | core-capability | active | M002 | 🟡 中 | mapped |
| R040 | core-capability | active | M002 | 🟡 中 | mapped |
| R041 | quality-attribute | active | M001/S01 | 🔴 高 | mapped |
| R042 | quality-attribute | active | M001/S01 | 🔴 高 | mapped |
| R043 | constraint | active | M001 | 🔴 高 | mapped |
| R044 | primary-user-loop | active | M002 | 🟡 中 | mapped |
| R045 | primary-user-loop | active | M002 | 🟡 中 | mapped |
| R046 | launchability | active | M002 | 🟡 中 | mapped |
| R047 | launchability | active | M002 | 🟡 中 | mapped |
| R048 | launchability | active | M002 | 🟡 中 | mapped |
| R049 | quality-attribute | active | M002 | 🟡 中 | mapped |
| R050 | continuity | active | M002 | 🟡 中 | mapped |
| R051 | differentiator | deferred | M003+ | 🟡 中 | unmapped |
| R052 | core-capability | deferred | M003+ | 🟡 中 | unmapped |
| R053 | continuity | deferred | M003+ | 🟡 中 | unmapped |
| R054 | core-capability | deferred | M002+ | 🟡 中 | unmapped |
| R055 | differentiator | deferred | M003+ | 🟢 低 | unmapped |
| R056 | differentiator | deferred | M003+ | 🟡 中 | unmapped |
| R057 | constraint | out-of-scope | — | — | n/a |
| R058 | constraint | out-of-scope | — | — | n/a |
| R059 | constraint | out-of-scope | — | — | n/a |
| R060 | core-capability | active | M001/S02 | 🔴 高 | mapped |
| R061 | core-capability | active | M001/S02 | 🔴 高 | mapped |
| R062 | core-capability | active | M001/S02 | 🟡 中 | mapped |
| R063 | core-capability | active | M001/S02 | 🟡 中 | mapped |
| R064 | core-capability | active | M001/S02 | 🟡 中 | mapped |
| R065 | core-capability | active | M001/S02 | 🔴 高 | mapped |
| R066 | primary-user-loop | active | M002 | 🟡 中 | mapped |
| R067 | core-capability | active | M002 | 🟡 中 | mapped |
| R068 | core-capability | active | M002 | 🟡 中 | mapped |
| R069 | core-capability | active | M002 | 🟡 中 | mapped |
| R070 | core-capability | active | M001/S04 | 🔴 高 | mapped |
| R071 | quality-attribute | active | M001/S02 | — | merged into R013 |
| R072 | core-capability | active | M001/S02 | 🔴 高 | mapped |
| R073 | core-capability | active | M002 | 🟡 中 | mapped |
| R074 | quality-attribute | active | M001/S01 | 🟡 中 | mapped |
| R075 | constraint | active | M002 | 🟡 中 | mapped |
| R076 | core-capability | active | M002 | 🟡 中 | mapped |
| R077 | quality-attribute | active | M002 | 🟡 中 | mapped |
| R078 | core-capability | active | M002 | 🟡 中 | mapped |
| R079 | core-capability | active | M002 | 🟡 中 | mapped |
| R080 | quality-attribute | active | M001 | 🔴 高 | mapped |
| R081 | quality-attribute | active | M001 | 🟡 中 | mapped |
| R082 | quality-attribute | active | M001 | 🟡 中 | mapped |
| R083 | quality-attribute | active | M001 | 🟡 中 | mapped |
| R084 | quality-attribute | active | M001 | 🔴 高 | mapped |
| R085 | quality-attribute | active | M002 | 🟡 中 | mapped |
| R086 | core-capability | active | M001/S04 | 🟡 中 | mapped |
| R087 | core-capability | active | M001/S04 | 🟡 中 | mapped |
| R088 | launchability | active | M002 | 🟡 中 | mapped |
| R089 | core-capability | active | M001/S02 | 🟡 中 | mapped |
| R090 | core-capability | active | M002 | 🟡 中 | mapped |
| R091 | quality-attribute | active | M001/S02 | 🔴 高 | mapped |
| R092 | primary-user-loop | active | M002 | 🟡 中 | mapped |
| R093 | launchability | deferred | M002+ | 🟡 中 | unmapped |

---

## Coverage Summary

- Active requirements: 86
- Mapped to M001 slices: 38 (🔴 高 20 项 + 🟡 中 18 项)
- Mapped to M002: 41
- Cross-cutting M001: 7
- Deferred: 7
- Out of Scope: 3
- Merged: 1 (R071→R013)
- **Total: 93**
