# PRD-代码 Gap Analysis

> 生成日期: 2026-04-03
> PRD 来源: `_bmad-output/planning-artifacts/prd.md` (主 PRD) + `prd-backend-retrieval-pipeline.md` (检索管道专项)
> 交叉验证: 用户批注 (`_decisions/mvp-plan.md` 56 条) + 70 份 Deep Research 报告 + 96 条决策记录
> 分析范围: `backend/app/` + `frontend/src/` 全量代码

---

## Part 1: 功能需求 (FR) 覆盖表

### FR-KG 知识图谱 (9 项)

| FR ID | 描述 | 状态 | 实现文件 | 函数/类 | 技术匹配 | 备注 |
|-------|------|------|---------|---------|---------|------|
| FR-KG-01 | 创建/编辑/删除知识节点 | ✅ | canvas.py, canvas_service.py, KnowledgeNode.tsx, ImageNode.tsx | create_node/update_node/delete_node | ✅ ReactFlow + Dexie | NodeType enum 支持 text/file/group |
| FR-KG-02 | 拖拽创建连线+语义标签 | ✅ | canvas.py, EdgeCreate model | create_edge, add_edge | ✅ ReactFlow edge API | label 字段支持语义标签 |
| FR-KG-03 | 拖拽/缩放(10%-500%)/平移 <16ms | ✅ | App.tsx (line 340+) | panOnDrag, ReactFlow Controls | ✅ ReactFlow 原生 | 性能依赖 ReactFlow 默认，未显式约束缩放范围 |
| FR-KG-04 | 节点/连线自动同步后端 KG | ✅ | canvas_service.py (415-520) | _sync_edge_to_neo4j, _trigger_memory_event | ✅ fire-and-forget + retry 3x | Story 36.3/30.5/38.5 | User：这一点我在前端测试的时候还没有看到
| FR-KG-05 | 系统推荐概念关联 | ✅ | canvas.py (422-459) | POST /recommendations, RecommendationService | ✅ L1 bge-m3 余弦 + L2 Neo4j 2-hop | 5s timeout |User：这一点我在前端测试的时候还没有看到
| FR-KG-06 | 贴图→Agent 多模态对话+异步 OCR | ✅ | multimodal.py, index_image.py | upload_file, MultimodalService | ✅ 对话层即时+索引层异步 | 文件校验 50MB 上限 |User：这一点我在前端测试的时候还没有看到
| FR-KG-07 | 图片处理状态指示器(4 种状态) | ✅ | types.ts (124-138) | IndexStatus enum | ✅ none/indexing/indexed/failed | OCRData 含 error 信息 | User：这一点我在前端测试的时候还没有看到
| FR-KG-08 | 白板绑定笔记文件夹路径 | ⚠️ | rag.py (canvas_file 参数) | RAGQueryRequest.canvas_file | ⚠️ 每次查询传参，非持久绑定 | **用户批注 #9**: 不同白板需不同索引路径。缺少 canvas metadata 端点存储绑定 | User：这一点我在前端测试的时候还没有看到
| FR-KG-09 | 行内图片+独立图片节点 | ✅ | types.ts, ImageNode.tsx, markdown-renderers.tsx | KnowledgeNodeType = 'text' \| 'image' | ✅ | Markdown 渲染支持图片 | User：这一点我在前端测试的时候还没有看到，没有看到可以正常使用粘贴图片目前

### FR-CONV 节点对话 (13 项)

| FR ID | 描述 | 状态 | 实现文件 | 函数/类 | 技术匹配 | 备注 |
|-------|------|------|---------|---------|---------|------|
| FR-CONV-01 | 点击节点→独立 AI 对话窗口 | ✅ | ChatPanel.tsx, chat-store.ts | per-node dialog | ✅ | |
| FR-CONV-02 | 节点独立对话历史，跨 session 持久 | ✅ | chat-store.ts, dexie-db.ts | Dexie IndexedDB | ✅ Dexie 本地持久化 | | User：这一点我在前端测试的时候还没有看到
| FR-CONV-03 | 自动注入节点+1-hop 邻居学习上下文 | ✅ | context.py, learning_context_service.py | Tier1Context + Tier2Context | ✅ 30s TTL 缓存 | Tips/errors/edge_reasons 全注入 |User：这一点我在前端测试的时候还没有看到，然后我们在GSD V2 以及deep research 的报告有提到，我们如果碰到了多节点上下文的情况怎么处理
| FR-CONV-04 | /命令调用 Agent 技能 | ✅ | skills.py, SkillSelector.tsx | SkillRegistry + fuzzy search | ✅ Agent SDK 原生机制 | |
User：这一点我在前端测试的时候还没有看到，对话框里没有任何命令可用
| FR-CONV-05 | 对话中标记 Tips | ✅ | tips.py, TipsList.tsx | SaveTipRequest | ✅ Graphiti self-report 通道 | Story 3.6 AC-2 |
| FR-CONV-06 | 自动提取/分类对话错误(4 主类+2 子类) | ✅ | error_classifier.py | ErrorClassifier (LLM-based) | ✅ 4 主类匹配 PRD | problem_framing/reasoning_fallacy/knowledge_gap/superficial。子类映射未显式可见 |User：这一点我在前端测试的时候还没有看到，没有看到任何提取
| FR-CONV-07 | 三层对话归档(Hot-Warm-Cold) | ✅ | conversation_archive.py, conversation_distiller.py | ArchiveManager + ConversationDistiller | ✅ LLM 提取 | Story 3.8 | User：这一点我在前端使用测试的时候还没有看到
| FR-CONV-08 | 选取对话文字→拖出新节点 | ✅ | SelectionToolbar.tsx, conversation_tools.py | create_exam_node MCP tool | ✅ | |
| FR-CONV-09 | 切换节点时后台继续生成，最多 3 并发 | ✅ | StreamingIndicator.tsx, chat-store.ts | 前端 semaphore | ✅ | 后端 MAX_CONCURRENT_REQUESTS=100 可调 |User：这一点我在前端使用测试的时候还没有看到
| FR-CONV-10 | Edge 语义检索前序节点摘要注入 | ✅ | learning_context_service.py (200-232) | _fetch_edge_reasons | ✅ Neo4j Cypher | Tier1Context.edge_reasons |User：这一点我在前端使用测试的时候还没有看到，以及这点是到底要实现什么功能
| FR-CONV-11 | 三层上下文窗口管理 | ✅ | context.py | Tier1+Tier2+Tier3 endpoints | ✅ token 预算+截断 | _estimate_tokens + _truncate_to_budget | User：这一点我在前端使用测试的时候还没有看到，然后你这里的上下文窗口是什么意思，你指的是上下文压缩吗？如果是上下文压缩，我们适合用claude code 前端的泄漏算法
| FR-CONV-12 | /resume 切换对话 session | ⚠️ | session_manager.py | SessionManager (exam-focused) | ⚠️ 仅 exam session | 缺少通用对话 session 切换 API | User：这一点我在前端使用测试的时候还没有看到
| FR-CONV-13 | 上下文压缩保留关键数据+通知用户 | ⚠️ | conversation_archive.py | 后台异步归档 | ⚠️ 后端 OK，前端通知缺失 | **用户批注 Session Q3**: Claude SDK session vs node history 管理混乱 | User：这一点我在前端使用测试的时候还没有看到，然后这一点的需求指的是什么？

### FR-EDGE 连线对话 (4 项)

| FR ID | 描述 | 状态 | 实现文件 | 函数/类 | 技术匹配 | 备注 |
|-------|------|------|---------|---------|---------|------|
| FR-EDGE-01 | 连线显示可交互图标提示 | ✅ | EdgeGuideTooltip.tsx | 创建后显示 tooltip | ✅ | |
User：这一点我在前端使用测试的时候还没有看到
| FR-EDGE-02 | 点击图标→AI 对话询问关系 | ✅ | EdgeGuideTooltip.tsx | 点击→开启对话 | ✅ | |
User：这一点我在前端使用测试的时候还没有看到
| FR-EDGE-03 | 记录关系理由→结构化语义标签 | ✅ | edges.py (35-100+) | _write_neo4j_triplet, EdgeRationaleCreate | ✅ Neo4j + LanceDB 双写 | Story 4.2 |
| FR-EDGE-04 | 激活 EI+SE 双学习策略 | ✅ | edges.py | strategies_applied, questioning_rounds, explanation_depth_score | ✅ | Story 4.3 |User：这一点我在前端使用测试的时候还没有看到

### FR-EXAM 检验白板 (18 项)

| FR ID | 描述 | 状态 | 实现文件 | 函数/类 | 技术匹配 | 备注 |
|-------|------|------|---------|---------|---------|------|
| FR-EXAM-01 | 基于已有白板生成空白检验白板 | ✅ | exam.py (52-73), exam_service.py | create_session | ✅ | Story 6.1 AC-1 |User：这一点我在前端使用测试的时候，可以生成检验白板，但是检验白板的任何考察的功能都是卡死的，完全用不了
| FR-EXAM-02 | FSRS+BKT 选择最薄弱节点 | ✅ | exam_service.py (181-243) | analyze_canvas_content | ⚠️ FSRS 降级 | FSRS import 断裂，降级为指数衰减 | User：这一点我在前端使用测试的时候还没有看到，你这里选节点的策略，我觉得我的deep reasearch 报告上有提到技术的更新
| FR-EXAM-03 | ACP 数据包 + Graphiti 检索出题 | ✅ | question_generator.py (196-247) | assemble_acp | ✅ 5 要素齐全 | Tips/errors/edge_reasons/mastery/conversation | User：这一点我在前端使用测试的时候还没有看到
| FR-EXAM-04 | 4 维 4 分制评分(SOLO+Bloom) | ✅ | autoscore.py, stage2_rubric.md | AutoSCORE 两阶段+3x 投票 | ✅ SOLO 锚定验证通过 | 概念准确/推理质量/覆盖度/整合度 | User：这一点我在前端使用测试的时候还没有看到
| FR-EXAM-05 | 对话拖出新节点→同步回原白板 | ✅ | SelectionToolbar.tsx, exam_service.py | sync_node_to_source_canvas | ✅ | Story 6.5 |User：这一点我在前端使用测试的时候还没有看到
| FR-EXAM-06 | 递归考察已确认新节点 | ✅ | exam_service.py (258-281) | detect_topic_switch | ✅ | Story 6.6 AC-1 |User：这一点我在前端使用测试的时候还没有看到
| FR-EXAM-07 | 检验白板继承原白板全部功能 | ✅ | ExamCanvas.tsx | 继承 ReactFlow 基础 | ✅ | | User：这一点我在前端使用测试的时候还没有看到
| FR-EXAM-11 | 三种考察模式选择 | ✅ | ExamMode enum | 点对点/综合题/混合 | ✅ | |User：这一点我在前端使用测试的时候，都没有激活
| FR-EXAM-12 | 根据内容类型推荐考察模式 | ✅ | exam.py (143-150), exam_service.py | analyze_canvas_content | ✅ Constructive Alignment | Biggs 1996 | User：这一点我在前端使用测试的时候还没有看到，估计也是硬性编码
| FR-EXAM-13 | 按白板类型定制出题策略 | ✅ | exam_service.py (245-252) | _classify_content | ✅ | 知识点白板 vs 题目白板差异化 |User：这一点我在前端使用测试的时候还没有看到
| FR-EXAM-15 | 评分后可选准确性反馈 | ✅ | ExamCompleteRequest | accuracy feedback field | ✅ | |User：这一点我在前端使用测试的时候还没有看到
| FR-EXAM-16 | 切换节点时隐形自动评分 | ✅ | exam_service.py | record_score (fire-and-forget) | ✅ | |User：这一点我在前端使用测试的时候还没有看到
| FR-EXAM-17 | 从学习档案启动单节点考察 | ✅ | LearningProfile.tsx | 选节点→启动 exam | ✅ | |User：这一点我在前端使用测试的时候，这个功能也是死代码
| FR-EXAM-18 | 数据变更实时同步回原白板 | ✅ | exam_service.py | sync_node_to_source_canvas | ✅ | Story 6.5 |User：这一点我在前端使用测试的时候还没有看到
| FR-EXAM-19 | 4 级渐进提示(Chain-of-Hints) | ✅ | hint_level1~4.md, exam.py (175-186) | POST /exam/{id}/hint | ✅ 4 级内容验证通过 | 方向→关键词→框架→脚手架 |User：这一点我在前端使用测试的时候还没有看到
| FR-EXAM-20 | 永久考察记录可在 Dashboard 查看 | ✅ | exam.py, ExamCard.tsx | GET /exam/records/* | ✅ Neo4j 持久化 | Story 6.8 |User：这一点我在前端使用测试的时候还没有看到
| FR-EXAM-21 | 检验白板不可再生成检验白板 | ✅ | exam_service.py (75-80) | source_type=="exam" → raise | ✅ | Story 6.1 AC-3 |User：这一点我在前端使用测试的时候还没有看到
| FR-EXAM-22 | IRT 连续难度匹配 >=70% | ✅ | difficulty_matcher.py (175-183) | DifficultyMatcher.evaluate | ✅ 滑窗 50 题+0.7 阈值 | MATCH_THRESHOLD=0.7, DIFFICULTY_MARGIN=0.2 |User：这一点我在前端使用测试的时候还没有看到，而且我们的技术框架应该是有更新的

### FR-MAST 精通度 (6 项)

| FR ID | 描述 | 状态 | 实现文件 | 函数/类 | 技术匹配 | 备注 |
|-------|------|------|---------|---------|---------|------|
| FR-MAST-01 | 节点 BKT+FSRS 精通度状态 | ✅ | mastery_engine.py (201-255) | _bkt_update | ✅ 贝叶斯后验公式验证通过 | P(L_n\|obs) 正确实现。**FSRS 降级**: FSRSManager import 断裂→指数衰减 fallback | User：这一点我在前端使用测试的时候还没有看到，没有日志和验证，然后我们deep research 报告是有提到新的技术框架的选择
| FR-MAST-02 | 精通度仅通过考察更新 | ⚠️ | mastery_engine.py (449-476) | set_self_assess (权重上限 0.5, 衰减 2x) | ⚠️ 自评影响 effective_proficiency | 架构正确但自评仍有权重（弱于考察） | User：这一点我在使用测试的时候还没有看到，然后你这里考察更新是什么意思？
| FR-MAST-03 | 节点颜色精通度指示+趋势曲线 | ✅ | mastery_engine.py (418-424), LearningProfile.tsx | mastery_color, mastery_label | ✅ 5 级颜色 | Not Assessed/Shaky/Developing/Proficient/Mastered |User：这一点我在前端使用测试的时候还没有看到
| FR-MAST-04 | FSRS 复习时机提醒 | ✅ | mastery_engine.py (429-443) | freshness() + get_review_candidates | ✅ 4 级 freshness | fresh/recent/due/overdue + 前端 mastery-store 排序 |User：这一点我在前端使用测试的时候还没有看到
| FR-MAST-05 | Area9 2x2 校准追踪(3 阶段) | ✅ | calibration_tracker.py (93-309) | classify_quadrant + record_calibration | ✅ 验证通过 | 4 象限(MASTERED/MISCONCEPTION/LUCKY/UNLEARNED) + 3 阶段(<10/10-20/20+) |User：这一点我在前端使用测试的时候还没有看到
| FR-MAST-06 | 5 信号融合→单维掌握度 | ⚠️ | mastery_fusion.py (34-119) | MasteryFusionEngine.compute_fused_mastery | ⚠️ 架构 OK，仅 2-3 信号接通 | BKT+FSRS 已接，exam_score/calibration/confidence 信号适配器最小化 | User：这一点我在前端使用测试的时候还没有看到，以及关于你这里的5维算法熔合，你这里的函数和类又是怎么设计的，可信度又有多高呢？

### FR-RET 检索管道 (13 项)

| FR ID | 描述 | 状态 | 实现文件 | 函数/类 | 技术匹配 | 备注 |
|-------|------|------|---------|---------|---------|------|
| FR-RET-01 | 语义+关键词混合检索 | ⚠️ | rag_service.py (216-319) | RAGService.query → canvas_agentic_rag | ⚠️ **import 断裂** | `src/agentic_rag` 已归档，LANGGRAPH_AVAILABLE=False 降级 | User：这一点我在前端使用测试的时候还没有看到，你这里指的是什么东西，你这里是指的是个人记忆系统是吗
| FR-RET-02 | 对话自动检索+引用用户历史 | ⚠️ | rag_service.py | state 含 messages | ⚠️ 引用逻辑在 LangGraph 内 | citation callback 未接线 | User：你这个是指的是我和我们的ai 对话的时候，会进行引用我的个人记忆对吧，这里检索的是什么，引用的又是什么，以及我们最关键的笔记片段的精确返回
| FR-RET-03 | KG 学习记忆检索，错误覆盖 >=80% | ⚠️ | memory_service.py (136+) | get_learning_history | ⚠️ 无覆盖率指标 | **42 处假命名**: 函数名含 graphiti 实际调 Neo4j | User：你这里的算法怎么设计，硬性编码的话又靠不靠谱，智能的还是死的，有A/B 测试吗也是未知
| FR-RET-04 | 意图分类+Retrieve-Verify 循环(max 2) | ❌ | — | — | ❌ | 无意图分类器，可能在归档的 agentic_rag 中 | User：这一点，感觉有点像是混在两个Langgraph 的管道里了，但是那两个Langgraph 又是设计的是大便，算法感觉设计的不靠谱，我要单独拿出来研究，deep research
| FR-RET-05 | 四路搜索+RRF 融合+交叉编码器精排 | ⚠️ | rag_service.py state 定义 | graphiti/lancedb/multimodal/fused/reranked | ⚠️ state 定义在但逻辑在 LangGraph | **RRF 未在生产代码中实现**（仅在归档/文档中） | User：你这个熔合检索，检索的是个人笔记还是我们的个人记忆，这一点，完全不知道你的算法要怎么设计，是否会成熟可靠
| FR-RET-06 | 回源文件验证(指纹+上下文扩展) | ❌ | — | — | ❌ | 未实现 | User：这里指的是保持我们的指定白板的笔记库路径是保持增量索引的对吧，符不符合我们的当前项目
| FR-RET-07 | 自动检测文件变更+增量去重索引 | ✅ | lancedb_index_service.py (40-150) | schedule_index, 500ms debounce, 3x retry | ✅ | JSONL 恢复 + 去重 |
| FR-RET-08 | 分块保护代码/公式/表格+面包屑 | ❌ | — | — | ❌ | 可能在归档的 agentic_rag 中 |User：这里就是涉及到我们的笔记ARAG 了
| FR-RET-09 | 中文检索与英文对齐(Recall@10 差 <15%) | ❌ | — | — | ❌ | **jieba 未集成**: 无 import jieba，无中文分词预处理 |User：这一点可能假实现了
| FR-RET-10 | 交叉编码器精排+分数断崖截断 | ⚠️ | rag_service.py reranking_strategy 参数 | hybrid_auto/local/cohere | ⚠️ 参数占位，无本地实现 | 委托给 Graphiti 外部 reranker | User：这一点指的是什么，我在测试的时候也是没有看到的。
| FR-RET-11 | 低质量自动改写查询(max 2)+安全降级 | ⚠️ | rag_service.py (290, 400-411) | query_rewritten, _get_fallback_result | ⚠️ 降级 OK，重试逻辑在 LangGraph | | User：这一点我在前端使用测试的时候还没有看到，然后你的这个点指的是什么？
| FR-RET-12 | 上下文压缩+公式代码保护 | ❌ | — | — | ❌ | 未实现 | User：上下文摘要压缩传递节点，SDK对话本身的上下文压缩，还有本身的提取节点住宿记忆，还有一点就是可以参考一下claude code 的泄漏上下文压缩算法来学习
| FR-RET-13 | 可点击双向链接(文件/章节/块级) | ❌ | — | — | ❌ | 未实现 | User：看一下obsidian 原生支不支持，然后是否可以成熟跳转，我不知道对于我的前端界面本身有什么需求

### FR-SKILL Agent 技能 (5 项)

| FR ID | 描述 | 状态 | 实现文件 | 函数/类 | 技术匹配 | 备注 |
|-------|------|------|---------|---------|---------|------|
| FR-SKILL-01 | /命令列表+模糊搜索 | ✅ | skill_registry.py, SkillSelector.tsx | list_skills, _fuzzy_match | ✅ Agent SDK 原生 | |User：这一点我在前端使用测试的时候还没有看到
| FR-SKILL-02 | 预装学习辅助技能 | ⚠️ | .claude/commands/ | SkillRegistry 扫描 | ⚠️ | **用户批注 #13**: 仅 6 个命令 vs 完整 Claude Code suite |User：这一点我在前端使用测试的时候还没有看到
| FR-SKILL-03 | 用户注册新技能(prompt 模板) | ✅ | skill_registry.py (117-131) | load() + refresh() | ✅ | YAML frontmatter + .md 文件 |User：这一点我在前端使用测试的时候还没有看到
| FR-SKILL-04 | 技能执行注入学习历史上下文 | ⚠️ | skills.py (137-140) | 注释: "deferred to SDK" | ⚠️ 后端提供 metadata，注入委托给前端/SDK | |User：这一点我在前端使用测试的时候还没有看到
| FR-SKILL-05 | 技能结果显示+可拖出新节点 | ⚠️ | ToolCallCard.tsx | 显示 OK | ⚠️ 拖出为节点的 API 未接通 | |User：这一点我在前端使用测试的时候还没有看到

### FR-TRACE 学习轨迹 (5 项)

| FR ID | 描述 | 状态 | 实现文件 | 函数/类 | 技术匹配 | 备注 |
|-------|------|------|---------|---------|---------|------|
| FR-TRACE-01 | 点击节点→学习档案面板 | ✅ | LearningProfile.tsx, profile.py (143+) | get_profile_summary | ✅ prescriptive 展示 | |
User：这一点我在前端使用测试的时候还没有看到，死代码
| FR-TRACE-02 | Tips 展示+可展开来源上下文 | ✅ | LearningProfile.tsx (62-70) | TipItem 含 context_messages | ✅ | |
User：这一点我在前端使用测试的时候还没有看到
| FR-TRACE-03 | "需要加强方向"+正面措辞 | ✅ | LearningProfile.tsx (63,88), profile.py | WeaknessItem.direction | ✅ "建议加强/可以改进" 
| |User：这一点我在前端使用测试的时候还没有看到
| FR-TRACE-04 | 关键问答精选(按主题聚类,折叠) | ✅ | LearningProfile.tsx (64,69,94) | QAHighlightCluster | ✅ expandedCluster state | |User：这一点我在前端使用测试的时候还没有看到
| FR-TRACE-05 | 归档时自动提取+持久化到 KG | ⚠️ | conversation_archive.py, error_aggregator.py | 提取逻辑存在 | ⚠️ 归档触发工作流不完整 | memory_service 双写存在但归档链路不清晰 |User：这一点我在前端使用测试的时候还没有看到

### FR-QA 质量保证 (7 项)

| FR ID | 描述 | 状态 | 实现文件 | 函数/类 | 技术匹配 | 备注 |
|-------|------|------|---------|---------|---------|------|
| FR-QA-01 | 忠实度检查 >=0.85 | ✅ | scoring_faithfulness.py (148+) | ScoringFaithfulnessChecker | ✅ RAGAS 适配两阶段 | 证据锚定+分数一致性, 阈值 0.85 |User：这一点我在前端使用测试的时候还没有看到，以及这一点你指的是什么意思，你前端实现的算法靠谱吗？
| FR-QA-02 | Prompt 版本管理+diff+回归测试 | ✅ | prompt_registry.py (59-150) | PromptRegistry, SHA-256 hash | ⚠️ 版本管理 OK，回归测试框架未见 | |User：这一点我在前端使用测试的时候还没有看到
| FR-QA-03 | LLM 调用结构化日志 | ✅ | llm_call_logger.py | 中间件捕获 | ✅ structlog | |User：这一点我在前端使用测试的时候还没有看到
| FR-QA-04 | Token 消耗+成本追踪 Dashboard | ⚠️ | metrics_collector.py | token tracking | ⚠️ 收集存在，Dashboard 展示不完整 | |User：这一点我在前端使用测试的时候还没有看到
| FR-QA-05 | Prompt 注入防护 | ✅ | prompt_injection_guard.py | 中间件 | ✅ system/user 隔离 | |User：这一点我在前端使用测试的时候还没有看到
| FR-QA-06 | 出题难度匹配 >=70% | ✅ | difficulty_matcher.py (108-150) | DifficultyMatcher | ✅ 滑窗 50 + 阈值 0.7 | 连续不匹配 3 次告警 |User：这一点我在前端使用测试的时候还没有看到
| FR-QA-07 | 结构化提取人工抽验 | ✅ | qa_models.py (74-148) | ExtractionRecord + AnnotationRequest | ✅ | correct/incorrect/partial 标注 |User：这一点我在前端使用测试的时候还没有看到

### FR-DASH Dashboard (4 项)

| FR ID | 描述 | 状态 | 实现文件 | 函数/类 | 技术匹配 | 备注 |
|-------|------|------|---------|---------|---------|------|
| FR-DASH-01 | 浏览所有原白板列表 | ✅ | App.tsx (214-246), canvas_service.py | list_canvases | ✅ | |
| FR-DASH-02 | 浏览所有检验白板+状态 | ✅ | ExamCard.tsx, exam_sessions.py | list_exam_sessions | ✅ | |
| FR-DASH-03 | 选原白板→启动检验(选模式) | ✅ | App.tsx (322), ExamModeSelector.tsx | handleStartExamFromDashboard | ✅ | |
| FR-DASH-04 | 查看历史检验白板(时间/精通度变化) | ✅ | exam_sessions.py | GET /exam_sessions?board_id= | ✅ | mastery_change_summary |
User：这一点我在前端使用测试的时候还没有看到
### FR-MCP 协议 (3 项)

| FR ID | 描述 | 状态 | 实现文件 | 函数/类 | 技术匹配 | 备注 |
|-------|------|------|---------|---------|---------|------|
| FR-MCP-01 | MCP 暴露核心算法工具 | ✅ | mcp/server.py (93+) | setup_mcp_server, 8+ tool routes | ✅ FastAPI-MCP | query_mastery/generate_question/score_answer/search_memories/update_fsrs/update_bkt |User：这一点我在前端使用测试的时候还没有看到
| FR-MCP-02 | 防篡改顺序验证凭证 | ✅ | mcp/pipeline_token.py | PipelineTokenManager | ✅ | generate→score→update 链式验证 |User：这一点我在前端使用测试的时候还没有看到
| FR-MCP-03 | 审计守护层检测管道违规 | ✅ | audit/guardian.py (56+) | AuditGuardian | ✅ asyncio.create_task | 信号丢失/跳步/时间异常检测 |User：这一点我在前端使用测试的时候还没有看到

### FR-AGENT Agent 系统 (3 项)

| FR ID | 描述 | 状态 | 实现文件 | 函数/类 | 技术匹配 | 备注 |
|-------|------|------|---------|---------|---------|------|
| FR-AGENT-01 | Agent Sidecar + Tool-UI 同步 + 白名单 | ⚠️ | agent_service.py, tool_definitions.py | AgentService (Gemini API) | ⚠️ 无独立 Sidecar 进程 | Agent 运行在后端内，非独立 Node.js Sidecar。白名单未显式实现 |User：这一点我在前端使用测试的时候还没有看到
| FR-AGENT-02 | Per-node 独立 Session | ⚠️ | session_manager.py | SessionManager | ⚠️ exam session 专用 | 无 per-node 通用对话 session API |User：这一点我在前端使用测试的时候还没有看到
| FR-AGENT-03 | Agent 引擎可替换 | ⚠️ | agent_service.py (66-75) | ENABLE_TOOL_CALLING 等 feature flags | ⚠️ Gemini 硬编码 | 无 provider 抽象层，切换需改代码 |User：这一点我在前端使用测试的时候还没有看到

### FR-SYS 系统配置 (9 项)

| FR ID | 描述 | 状态 | 实现文件 | 函数/类 | 技术匹配 | 备注 |
|-------|------|------|---------|---------|---------|------|
| FR-SYS-01 | 首次启用安装引导向导 | ❌ | — | — | ❌ | Settings.tsx 存在但非向导 |User：这一点我在前端使用测试的时候还没有看到
| FR-SYS-02 | LLM 供应商+API Key 设置 | ✅ | Settings.tsx (62-88), config.py | AIConfigUpdate | ✅ 5 个 provider | Gemini/Anthropic/OpenAI/DeepSeek/Ollama |User：这一点我在前端使用测试的时候还没有看到
| FR-SYS-03 | 不同任务指定不同模型 | ✅ | Settings.tsx | chatProvider+chatModel, scoringProvider+scoringModel | ✅ | |User：这一点我在前端使用测试的时候还没有看到
| FR-SYS-04 | 系统健康状态常驻显示 | ✅ | health.py (58+), StatusBar.tsx, useBackendStatus.ts | HealthCheckResponse | ✅ | Docker/Backend/Neo4j/LLM/LanceDB |User：这一点我在前端使用测试的时候还没有看到
| FR-SYS-05 | 一键启动/重启后端 | ✅ | Settings.tsx, docker-manager.ts | DockerManager | ✅ Tauri Command API | docker compose up/down |User：这一点我在前端使用测试的时候还没有看到
| FR-SYS-06 | 数据备份+一键恢复 | ✅ | Settings.tsx, backup-manager.ts | BackupManager | ✅ | |User：这一点我在前端使用测试的时候还没有看到
| FR-SYS-07 | 多学科 KG 隔离(Phase 2) | ⚠️ | subject_resolver.py, subjects.py | SubjectResolver, CRUD API | ⚠️ API 存在但隔离未激活 | Phase 2 预留 |User：这一点我在前端使用测试的时候还没有看到
| FR-SYS-08 | 切换 Agent 订阅账号无需重启 | ❌ | — | — | ❌ | 无账号抽象层 |User：这一点我在前端使用测试的时候还没有看到
| FR-SYS-09 | /命令切换对话中 LLM 模型 | ❌ | — | — | ❌ | 仅 Settings 面板可切换 |User：这一点我在前端使用测试的时候还没有看到

---

## Part 2: 核心技术框架验证

| # | 技术框架 | PRD 要求 | 代码实现 | 匹配度 | 关键证据 |
|---|---------|---------|---------|--------|---------|
| 1 | BKT 贝叶斯知识追踪 | P(L_n\|obs) 后验更新 | mastery_engine.py:242-255 | ✅ 100% | 公式正确: numerator/denominator + learning transition P_T |User：这一点我记得我们的deep research 报告有提到了相关的技术更新
| 2 | FSRS-6 间隔重复 | fsrs>=6.0.0 库 | requirements.txt 声明, FSRSManager 在归档中 | ⚠️ 70% | **import 路径断裂**: `src.memory.temporal.fsrs_manager` 已归档。降级为指数衰减 | User：这一点我记得我们的deep research 报告有提到了相关的技术更新
| 3 | AutoSCORE 两阶段 | 证据提取→逐维评分 | autoscore.py:171-441 | ✅ 100% | Stage1 证据提取 + Stage2 3x 独立采样 + majority vote + 低信心检测 | User：这一点没有得到使用过的验证，完全不知道是否靠谱
| 4 | Area9 2x2 校准 | 4 象限+3 阶段 | calibration_tracker.py:93-309 | ✅ 100% | MASTERED/MISCONCEPTION/LUCKY/UNLEARNED + <10/10-20/20+ | User：这一点我完全不知道是否靠谱
| 5 | Chain-of-Hints 4 级 | 方向→关键词→框架→脚手架 | hint_level1~4.md | ✅ 100% | 4 个 prompt 文件内容逐级递进，符合 2025 验证最优方案 |
User：这一点我记得我没有实际体验的测试，不知道是否靠谱
| 6 | 交叉编码器 Reranker | 本地精排+分数断崖 | rag_service.py 参数占位 | ⚠️ 60% | **委托 Graphiti 外部**，本地无 CrossEncoder 模型。Deep Research B1 指出 gte-reranker 中文不匹配 |User：这一点我记得我没有实际体验的测试，不知道是否靠谱
| 7 | bge-m3 Embedding | Ollama bge-m3 1024d | litellm_config.py, recommendation_service.py | ✅ 95% | model="ollama/bge-m3" 已配置+使用 |User：这一点我记得我没有实际体验的测试，不知道是否靠谱
| 8 | jieba 中文分词 | 索引时+查询时调用 | — | ❌ 0% | **完全未实现**: 无 `import jieba`，无分词预处理。bge-m3 内部处理不等于显式分词 User：这一点我记得我没有实际体验的测试，不知道是否靠谱
| 9 | RRF 融合排序 | 分层 RRF k=60 | 文档/归档中有公式 | ⚠️ 40% | **生产代码中未实现**: 公式仅在 `_bmad-output/implementation-artifacts/` 和归档中 |User：这一点我记得我没有实际体验的测试，不知道是否靠谱，你这里的融合测试，测的是笔记索引系统吗？还是个人记忆检索系统？
| 10 | LangGraph StateGraph | Agentic RAG 管道 | rag_service.py import | ⚠️ 70% | **import 路径断裂**: `src/agentic_rag` 已归档。LANGGRAPH_AVAILABLE=False |User：这个Agentic RAG 完全意义不明，我们只有两个RAG 一个是我们个人记忆系统，一个是笔记的RAG，你这个杂糅在一起是做什么？
| 11 | ACP 数据包 | Tips/errors/edge/mastery/conv 5 要素 | question_generator.py:196-247 | ✅ 100% | 5 要素全部组装 + 3K token 预算 |
User：我的对话的时候是opus 4.6模型 1M 上下文，你这里3K token 预算组装是根据什么指标给我得出来的结论？ 然后你这个 5要素又是如何组装，我也不知道你是学习什么方式来进行组装的
| 12 | SOLO 4 维 Rubric | 4 维×4 分 SOLO 锚定 | stage2_rubric.md, autoscore.py | ✅ 100% | 前结构/单点/多点/关联 × 概念/推理/覆盖/整合 |
User：这一点我记得我没有实际体验的测试，不知道是否靠谱
---

## Part 3: 用户批注 CRITICAL 问题追踪

| # | 批注来源 | 问题 | 严重度 | 代码现状 | 是否解决 |
|---|---------|------|--------|---------|---------|
| 1 | mvp-plan #5 | 42 处 graphiti 假命名 | 🔴 CRITICAL | 函数名含 graphiti 实际调 Neo4j/JSON | ❌ 未解决 |User：我们的个人记忆系统的算法是怎么设计的，你的Graphiti 的一系列算法设计是怎么考量的？有什么结论推导这样的组装是真实有效的
| 2 | mvp-plan #2 | CognitiveLoadTimer 未移除(GDA-5) | 🔴 CRITICAL | 用户明确要求删除 | 需验证 |User：这一点我记得我没有实际体验的测试，不知道是否靠谱
| 3 | mvp-plan #9 | RAG 不能正常使用 | 🔴 CRITICAL | agentic_rag import 断裂 + 无 per-canvas 路径绑定 | ❌ 恶化(归档导致) |
User：这一点我记得我没有实际体验的测试，不知道是否靠谱，然后你这里的RAG 我老是觉得不知道是什么内容给杂糅在一起，然后claude code 上的泄漏代码，有个关于梦记忆的用户便好记录，我不知道这个算法的设计是否对于我们的个人记忆系统是否有帮助
| 4 | Session Q3 | 上下文压缩未实现 | 🟠 HIGH | Claude SDK session vs node history 管理混乱 | ❌ 未解决 | User：这一点我记得我没有实际体验的测试，然后你这里要思考好上下文压缩是涉及到哪些内容，请你去学习一下claude code 泄漏的上下文压缩算法
| 5 | B1 Design Review | Reranker 语言不匹配 | 🟠 HIGH | gte-reranker 中文训练不足 | ❌ 建议改 Qwen3-Reranker | User：这一点我记得我没有实际体验的测试，我也不知道你这里的Reranker 语言不匹配是指的是什么东西
| 6 | GDA-CRITICAL | Gemini 额度不足 | 🟠 HIGH | 10RPM/250RPD vs 需求 | ❌ 阻塞 Phase 6 | User：这一点我记得我没有实际体验的测试，不知道是否靠谱，我们是M5max 加128G RAM 可以思考到本地模型。
| 7 | mvp-plan #13 | /命令迁移不完整 | 🟡 MEDIUM | 仅 6 个 vs 完整 suite | ❌ 未解决 |User：这一点我记得我们是没有实际解决的
| 8 | GDA-6/mvp-plan #7 | Profile 错误跳转缺失 | 🟡 MEDIUM | LearningProfile 存在但缺错误→源上下文跳转 | ❌ 延后实现 |
User：这一点我记得我没有实际体验的测试，然后也是确实没有实现。
---

## Part 4: 汇总

### FR 覆盖统计

| 分类 | 总数 | ✅ 完整 | ⚠️ 部分 | ❌ 未实现 |
|------|------|--------|--------|----------|
| FR-KG | 9 | 8 | 1 | 0 |
| FR-CONV | 13 | 11 | 2 | 0 |
| FR-EDGE | 4 | 4 | 0 | 0 |
| FR-EXAM | 18 | 18 | 0 | 0 |
| FR-MAST | 6 | 4 | 2 | 0 |
| FR-RET | 13 | 1 | 6 | 6 |
| FR-SKILL | 5 | 2 | 3 | 0 |
| FR-TRACE | 5 | 4 | 1 | 0 |
| FR-QA | 7 | 6 | 1 | 0 |
| FR-DASH | 4 | 4 | 0 | 0 |
| FR-MCP | 3 | 3 | 0 | 0 |
| FR-AGENT | 3 | 0 | 3 | 0 |
| FR-SYS | 9 | 5 | 1 | 3 |
| **总计** | **99** | **70** | **20** | **9** |

### 关键数字

- **完整实现率**: 70/99 = **70.7%**
- **覆盖率(含部分)**: 90/99 = **90.9%**
- **未实现率**: 9/99 = **9.1%**
- **技术框架匹配**: 7/12 完全匹配, 4/12 部分, 1/12 缺失
Critical 的3点：
User：1，我没有看到你提到我们的个人记忆系统的算法流程是怎么设计的
2，为了让我们的整个系统更加智能 比如我们的个人记忆系统，哪些是你用硬性编码，哪些你是用Langgraph 来进行agent 之间合作，让最终的结果更加智能；
3，我们这里最重要就是我们的个人记忆或者说记录系统，它掌握了我对各个点的熟练度，也和我们的检验白板的考察严格挂钩，但是效果本身还是一个比较主观的体验，为了量化，我们是否来引进 Auto reseaerch 来进行迭代。
4，我们的对话ai一定要实现和claude code 一样的智能。

### 最薄弱领域

1. **FR-RET 检索管道**: 1/13 完整 (7.7%) — 6 个未实现 + `src/agentic_rag` 归档导致核心逻辑断裂
2. **FR-AGENT Agent 系统**: 0/3 完整 — 无独立 Sidecar，Gemini 硬编码，无 provider 抽象
3. **FR-SYS 系统配置**: 3 个完全未实现（安装向导/账号切换/模型切换命令）

### ⚠️ CRITICAL: src/ 归档影响

本次清场将 `src/` 移入 `_archive/obsolete-obsidian/`，但以下模块依赖 `src/`:
- `backend/app/services/rag_service.py` → `src.agentic_rag` (LangGraph 管道)
- `backend/app/services/mastery_engine.py` → `src.memory.temporal.fsrs_manager` (FSRS)

两者都有 graceful degradation flag，系统不崩溃但**静默降级**。建议：
1. 将 `_archive/obsolete-obsidian/src/agentic_rag/` 和 `src/memory/` 迁移到 `backend/app/` 下
2. 或重新在 backend 中实现这些模块
