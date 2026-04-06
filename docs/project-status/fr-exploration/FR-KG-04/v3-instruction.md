# Deep Research 分析请求 — FR-KG-04 User2 批注专项 (v3)

## 项目背景
- 技术栈：Tauri 2 + React + TypeScript + FastAPI + Neo4j + LanceDB + Graphiti
- 架构：前端 (React/Zustand) ↔ Tauri IPC ↔ 后端 (FastAPI) ↔ Neo4j + LanceDB + Graphiti
- 本 pack 聚焦：RAG 管道内部算法 + FSRS/BKT 融合 + 评分可靠性 + 出题策略
- 配套 pack：v2 pack 覆盖同步管道（SyncService/CanvasService/三层图架构）

## 分析议题
用户（非程序员，AI 辅助开发）对系统中 5 个关键算法设计提出质疑，需要 Deep Research 验证其成熟度和改进方向。

### 待验证问题（按优先级）

**A10 [CRITICAL]: FSRS 和 BKT 如何融合？权重有学术支撑吗？**
- 代码：`question_generator.py:44-47` — 三因子公式 `0.4*BKT + 0.3*FSRS + 0.3*KG`
- 代码：`mastery_engine.py` — BKT+FSRS 并行更新
- 代码：`mastery_fusion.py` — 5 信号加权平均
- 问题：权重无论文/实验依据，与设计文档不一致

**A3/A4 [HIGH]: AI 评分的可靠性如何证明？**
- 代码：`autoscore.py` — 两阶段评分 + 3x 采样 + 多数投票
- 代码：`scoring_faithfulness.py` — NLI 忠实度检查（阈值 0.85）
- 代码：`calibration_tracker.py` — Area9 2x2 校准矩阵
- 问题：无 inter-rater reliability 测试，无 ground truth 对比

**A8/A9 [HIGH]: RAG 路由和融合算法是否成熟？**
- 代码：`state_graph.py:65-129` — L1 关键词路由（非 LLM）
- 代码：`nodes.py:409-932` — 4 种融合策略（RRF/Weighted/Cascade/Layered-RRF）
- 代码：`reranking.py` — Local/Cohere/Hybrid 三模式重排序
- 问题：路由太简单（关键词匹配），融合权重无调优依据

**A12 [HIGH]: 出题策略有什么社区成熟做法？**
- 代码：`verification_service.py:537-680` — 按文件顺序出题（最弱）
- 代码：`question_generator.py:102-201` — 三因子优先级选择
- 用户期望：类似 Plan 文件的逐步递进考察（Mastery-Based Progression）
- 问题：无拓扑排序、无依赖分析、无分阶段计划

## 打包内容
51 个文件，~650K tokens：RAG 管道(14) + FSRS/评分(12) + 出题策略(10) + Prompts(12) + 文档(3)

## 分析方法
1. 通读 `<directory_structure>` 建立心智模型
2. 从 `FR-KG-04-user2-annotations.md` 获取每个问题的完整上下文
3. 引用 `<file path="...">` + 行号作为证据
4. 对比社区最佳实践（FSRS 论文、CAT 自适应测试、RAGAS 框架等）

## 请分析
1. **A10**: BKT+FSRS 融合的学术依据是什么？社区有什么成熟的多信号融合方案？
2. **A3/A4**: AutoSCORE 两阶段评分 + NLI 忠实度检查的可靠性如何？如何改进？
3. **A8/A9**: L1 路由该升级为 LLM 分类吗？4 种融合策略各适合什么场景？
4. **A12**: Mastery-Based Progression / Knowledge Space Theory / CAT 哪个最适合这个系统？
5. 每个问题：CRITICAL / HIGH / MEDIUM / LOW 严重度 + 具体改进建议

## 输出格式
| 编号 | 严重度 | 文件:行号 | 问题 | 社区最佳实践 | 改进建议 |
