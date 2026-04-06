# FR-KG-04 User2 批注索引 — Deep Research 参考文档

> **用途**: 将用户批注与代码调研结论一一对应，供 Deep Research 快速定位待验证/待改进的问题
> **批注来源**: `FR-KG-04.md` 中所有 `User2:` 标记的内容
> **日期**: 2026-04-04 ~ 04-05

---

## 批注总览

| # | 行号 | 主题 | 批注核心问题 | 调研状态 | 严重度 |
|---|------|------|-------------|----------|--------|
| A1 | 307 | RAG 检索 | 6 路检索到底靠谱吗？ | ✅ 已调研 | HIGH |
| A2 | 317 | 图层 1 | CANVAS_EDGE 是否可以直接废除并合并？ | ✅ 已调研 | MEDIUM |
| A3 | 374 | 验证服务 | 评分验证是自己编的还是社区认证的？ | ✅ 已调研 | HIGH |
| A4 | 391 | 验证服务 | 评分用了什么成熟算法框架？查询方案是否该用 Graphiti？ | ✅ 已调研 | HIGH |
| A5 | 401 | Graphiti | 记忆提取方式是 Hook 触发还是自定义？LLM 是云端还是本地？ | ✅ 已调研 | MEDIUM |
| A6 | 464 | 图谱合并 | 两个图谱能否合并？RAG 语义检索是什么？FSRS 怎么融入？ | ✅ 已调研 | CRITICAL |
| A7 | 503 | RAG 5路 | Graphiti 图谱几个？LanceDB vs Vault？图片算法？跨白板？ | ✅ 已调研 | HIGH |
| A8 | 506 | RAG 融合 | 融合怎样才是高质量？是否该用 Opus 4.6 deep explore？ | ⏳ 待深入 | HIGH |
| A9 | 510 | RAG 路由 | 激活几路的算法？融合+重排序算法是否成熟？ | ⏳ 待深入 | HIGH |
| A10 | 541 | FSRS 融合 | FSRS 和其他算法如何融合？没有理清楚 | ⏳ 待深入 | CRITICAL |
| A11 | 653 | 缓存上限 | 2000 上限是 per group_id 还是全局？ | ✅ 已调研 | MEDIUM |
| A12 | 753 | 出题策略 | 除了 plan 文件，社区还有什么成熟高效做法？ | ⏳ 待深入 | HIGH |

---

## A1: 6 路检索到底靠谱吗？

**批注位置**: Line 307
**批注原文**: `User2：这里的 6 路检索到底靠谱吗？`

**挂钩内容**: 下游消费者分析中提到"RAG 6路检索"

**调研结论**:
- 实际是 **5 路**（不是 6 路），S27-GDA-2 决策取消了教材检索和跨白板检索
- 5 路 = Graphiti + LanceDB + 多模态 + 跨白板(TODO) + Vault 笔记
- 路由算法（L1 分类）是简单的关键词匹配，不够智能
- 融合用 RRF（Reciprocal Rank Fusion），是业界标准但参数未调优
- **验证服务调用 RAG 时字段名不匹配**（期望 `learning_history`，实际返回 `reranked_results`）→ 拿到空值

**相关代码**:
- `backend/lib/agentic_rag/state_graph.py:65-243` — 5路并行检索定义
- `backend/lib/agentic_rag/nodes.py:400-406` — 融合权重 (0.25/0.25/0.15/0.10/0.25)
- `backend/app/services/verification_service.py:1835-1837` — 字段名 bug

**Deep Research 待验证**: RRF 融合是否适合这个场景？权重是否需要基于用户行为动态调整？

---

## A2: CANVAS_EDGE 是否可以直接废除并合并？

**批注位置**: Line 317
**批注原文**: `User2：这里我理解为只是把前端节点之间的链接，传到后端而已是吧，但是实际上没意义？对后端的一切算法都没有作用？那么是否可以直接废除，然后和我们的后端其他数据库合并？`

**挂钩内容**: 三层图架构中图层 1（CANVAS_EDGE）

**调研结论**:
- 用户理解基本正确——CANVAS_EDGE 对学习算法**几乎无作用**
- 唯一读取方：推荐系统（recommendation_service）用 2-hop 图模式推荐新连线
- 推荐系统本身也可以改用 Graphiti 的 `add_triplet()` 统一管理
- **可以合并**：Graphiti SDK 原生支持手动添加关系（`add_triplet()`），支持更新（时间模型）
- 合并后推荐系统改读 `RELATES_TO`，所有图层统一

**相关代码**:
- `backend/app/services/sync_service.py:242` — CANVAS_EDGE MERGE 写入
- `backend/app/services/recommendation_service.py:192` — CANVAS_EDGE 2-hop 读取
- Graphiti SDK: `graphiti.add_triplet(source, edge, target)` — 替代方案

**Deep Research 待验证**: 合并后推荐系统的查询性能是否受影响？Graphiti 的 RELATES_TO 是否支持 2-hop 模式查询？

---

## A3: 评分验证是自己编的还是社区认证的？

**批注位置**: Line 374
**批注原文**: `User2：...以及你所设立的这个评分验证，是你自己编的还是你在社区有广泛认证？`

**挂钩内容**: 验证服务（verification_service）的评分系统

**调研结论**:
- 评分由 **scoring-agent**（AI 驱动）完成，不是固定规则
- AI 评分后映射到 0-100 分，再映射到 FSRS Grade 1-4
- 评分 prompt 参考了 Bloom's Taxonomy（有 arXiv:2408.04394 引用）
- 但**评分的可靠性没有系统性验证**（无 inter-rater reliability 测试、无 ground truth 对比）
- verification_service 的图谱查询只有简陋的 1-hop CONNECTS_TO（空的）

**相关代码**:
- `backend/app/services/verification_service.py:682-798` — process_answer() 评分流程
- `backend/app/services/verification_service.py:1874-1884` — 1-hop CONNECTS_TO 查询
- `backend/app/services/question_generator.py:44-47` — 三因子权重（无学术支撑）

**Deep Research 待验证**: AI 评分的一致性如何？是否需要 calibration（校准）？社区有什么成熟的 AI 评分框架？

---

## A4: 验证服务的查询方案是否该改用 Graphiti？

**批注位置**: Line 391
**批注原文**: `user2：你这里想要用 1，验证服务来对关系进行更加准确的评估，那么请问你有使用成熟什么算法框架，来真正的证明你的的评分是真实有效的；2，你这里查询概念的方案本身也是比较死板的，还说接入使用 Graphiti 的方式来进行查看？`

**挂钩内容**: 验证服务内部三路上下文获取

**调研结论**:
1. **评分框架**: 无成熟算法框架证明评分有效。AI 评分 + Bloom's Taxonomy prompt 是主要方法
2. **查询方案**: 当前 1-hop CONNECTS_TO 非常死板（LIMIT 8，无排序）。验证服务内部已有 Graphiti client 接入但只是补充来源
3. **建议**: 应该用 Graphiti `search_()` 替代 1-hop Cypher 查询，获得向量搜索 + 时间推理 + cross-encoder 重排序能力

**相关代码**:
- `backend/app/services/verification_service.py:1852-1965` — `_get_graph_context_for_concept()` 简陋 1-hop
- `backend/app/services/verification_service.py:1922-1941` — Graphiti client 已接入但未主力使用

**Deep Research 待验证**: Graphiti search_() 是否能完全替代 1-hop 查询？延迟是否可接受（200ms vs <50ms）？

---

## A5: Graphiti 记忆提取是 Hook 还是自定义？

**批注位置**: Line 401
**批注原文**: `User2：这里的 Graphiti 的记忆提取方式是想在 claude code 中的一样 用 hook 来判定检索...因为我之前有看到 hook 的调用在对话的时候`

**挂钩内容**: Graphiti 图层 3 的记忆提取机制

**调研结论**:
- **不是 Hook**，是**事件驱动**：Agent 回答后 → FastAPI background_task → episode_worker.enqueue()
- 用的是**正规官方 SDK** (`graphiti-core >= 0.28.2`)
- LLM = **Gemini 2.5 Flash**（云端，非本地模型，无 fallback）
- 类型化提取：Pydantic 模型（LearningConcept, Misconception, LearningTip, MasteryRecord）
- 与 Claude Code 的 Hook 机制本质不同：Claude Code 是文件级记忆，这里是图谱级语义提取

**相关代码**:
- `backend/app/services/episode_worker.py:212-277` — Graphiti 初始化（GeminiClient）
- `backend/app/services/episode_worker.py:372-401` — add_episode() 调用
- `backend/app/graphiti/entity_types.py:247-256` — 类型化实体定义

**Deep Research 待验证**: 用户提到"看到 hook 调用"——需要确认前端是否有 hook 机制还是混淆了概念

---

## A6: 两个图谱能否合并？RAG 是什么？FSRS 怎么融入？（综合大问题）

**批注位置**: Line 464
**批注原文**: `User 2：按照检验白板的逻辑的话，那么我发现有个图谱...1，这两个关系图谱是否合并为一个关系图谱...2，你这里的 RAG 语义检索是什么...3，FSRS 评分历史...`

**挂钩内容**: 验证服务三路上下文（RAG + 图谱 + FSRS）

**调研结论**:
1. **图谱合并**: 可以，Graphiti SDK 有 `add_triplet()` 方法原生支持手动添加关系，项目基础设施 90% 到位
2. **RAG 语义检索**: 5 路并行系统（LangGraph），LanceDB 返回原文片段（bge-m3 向量，512 token 分块）
3. **FSRS**: 存在 Neo4j 节点属性上（fsrs_stability, fsrs_difficulty 等），影响出题难度（<60 基础题，60-79 验证题，≥80 应用题），但与关系图谱**分开存储**，不在同一层

**用户核心关切**: 这三个系统如何有机协作？当前是各自为政。

**Deep Research 待验证**: Graphiti add_triplet() + FSRS node properties + LanceDB 向量搜索能否在一个统一查询接口下工作？

---

## A7: Graphiti 图谱几个？LanceDB vs Vault？图片算法？跨白板？

**批注位置**: Line 503
**批注原文**: `User2：1，我们的 Graphiti 知识图谱有几个...2.Lance DB 和笔记...3，关于在原白板嵌入的图片...4，跨白板关联...`

**挂钩内容**: RAG 5路检索系统的每一路

**调研结论**:
1. **Graphiti 图谱**: 一个 Neo4j（7691），按 group_id 逻辑隔离（`"学科:白板名"`）
2. **LanceDB vs Vault**: 不同数据源——LanceDB 索引白板节点文本，Vault Notes 索引 .md 笔记文件。两者都返回原文片段但来源不同。**LanceDB 和 Graphiti 不冲突**：Graphiti 返回 LLM 提取的事实，LanceDB 返回原文（互补）
3. **图片处理**: Gemini 2.0 Flash Vision API（OCR + 概念提取）。**用户决策：改用本地模型**
4. **跨白板**: 原设计是手动关联（Story 16.1），代码用了自动 Jaccard（不符原意），已被 S27-GDA-2 取消

**相关代码**:
- `backend/app/core/subject_config.py:192-206` — build_group_id()
- `backend/lib/agentic_rag/clients/lancedb_client.py:306-310` — LanceDB 索引
- `backend/app/api/v1/endpoints/index_image.py:72-177` — Gemini Vision 图片处理
- `backend/app/services/cross_subject_bridge.py:22-39` — Jaccard 相似度

---

## A8: RAG 融合怎样才是高质量？

**批注位置**: Line 506
**批注原文**: `User2：你这里的融合到底怎么样才是高质量，是否需要专门的 agent deep research 不如调用我们的 claude code opus 4.6 专门启动并行 deep explore 生成 plan 文件然后总结放回了上下文，还是说你有什么更加优秀的算法设计？`

**挂钩内容**: RAG 融合（RRF）+ 重排序 + 质量检查

**调研结论**: ⏳ **待深入调研**

当前实现：
- 融合策略：RRF（Reciprocal Rank Fusion）或 weighted fusion
- 重排序：Cohere 或本地 cross-encoder
- 质量检查：low/medium/high 三档，low 时重写查询重试

**用户的提议值得探索**: 用 Opus 4.6 作为"智能融合 agent"——先 deep explore 生成 plan，然后按 plan 组织上下文。这符合"clever agent; dumb tool"原则。

**Deep Research 待验证**: 
1. RRF vs Learned Fusion（学习型融合）在教育场景的效果对比
2. 用 LLM 做 query-time reasoning（查询时推理）是否比固定权重更好
3. 社区 RAG 最佳实践（如 LlamaIndex 的 fusion retriever、LangChain 的 ensemble retriever）

---

## A9: RAG 路由算法和重排序是否成熟？

**批注位置**: Line 510-513
**批注原文**: `User2：你这里一开始没有向我解释，你是用什么算法来决定激活几路，然后又怎么样来把这6源来进行融合的...如果算法不够灵活智能，那么 dumb tool，smart agent，交给 opus 4.6 来进行成熟的判断...`

**挂钩内容**: L1 路由 + 融合 + 重排序

**调研结论**: ⏳ **待深入调研**

当前 L1 路由（`classify_query_intent`）是**关键词匹配**：
- 包含"笔记/文件" → file_locate 意图 → 优先 Vault + LanceDB
- 包含"之前/复习" → learning_history 意图 → 优先 Graphiti + LanceDB
- 其他 → comprehensive → 全部 5 路

**问题**: 关键词匹配太死板，同一个查询在不同上下文可能需要不同路由策略

**Deep Research 待验证**:
1. 是否该用 LLM 做意图分类（取代关键词匹配）？
2. 动态路由（根据前几路结果质量决定是否启动后续路）vs 静态全路并行？
3. 社区方案：Adaptive RAG, Self-RAG, CRAG（Corrective RAG）

---

## A10: FSRS 和其他算法如何融合？

**批注位置**: Line 541
**批注原文**: `USer2：...（这里你还是没有理清楚 FSRS 的算法是如何和其他的算法进行融合的）`

**挂钩内容**: FSRS + BKT + KG relevance 三因子公式

**调研结论**: ⏳ **待深入调研**

当前融合方式：
```python
priority = 0.4 * (1 - p_mastery)       # BKT
         + 0.3 * (1 - retrievability)   # FSRS
         + 0.3 * kg_relevance           # 图谱
```

**问题**:
1. 权重 0.4/0.3/0.3 无学术支撑，无 ablation study
2. 三个信号可能**高度相关**（p_mastery 低 ↔ retrievability 低），线性加权会重复计数
3. 设计文档说的权重（40% FSRS / 30% BKT / 20% KG / 10% 交互）与代码不一致
4. **验证服务完全不看 FSRS**——节点按文件顺序出题

**相关代码**:
- `backend/app/services/question_generator.py:44-47, 165-169` — 三因子公式
- `backend/app/services/verification_service.py:628` — 文件顺序出题

**Deep Research 待验证**:
1. BKT 和 FSRS 的数学关系是什么？是否可以只保留一个？
2. 教育技术领域对 multi-signal fusion 的最佳实践是什么？
3. 是否该用 Bayesian Optimization / Multi-Armed Bandit 自动调权重？

---

## A11: Episode 缓存 2000 上限的范围

**批注位置**: Line 653
**批注原文**: `User: 这里上限 2000，可是我的节点总结肯定会超过 2000 的，那么你这里是指的是 group id 的 episode 上限 2000 还是整一个的 Neo4j 是 20000`

**挂钩内容**: 噪音控制三层防线

**调研结论**:
- **全局 2000**，不是 per group_id（`self._episodes` 是单一全局列表）
- **只影响内存缓存**，Neo4j **无上限**，永久保留
- 正常查询走 Neo4j，超时才 fallback 到内存缓存
- **发现 bug**: 内存缓存查询时没有按 group_id 过滤（`memory_service.py:561`），可能导致其他白板数据混入

**相关代码**:
- `backend/app/services/memory_service.py:151` — MAX_EPISODE_CACHE = 2000
- `backend/app/services/memory_service.py:167` — self._episodes: List（全局列表）
- `backend/app/services/memory_service.py:561` — 缺少 group_id 过滤 (BUG)

---

## A12: 除了 Plan 文件出题，社区还有什么成熟做法？

**批注位置**: Line 753
**批注原文**: `User2：除了这种出 plan 文件来考察我之外，社区上还有什么成熟高效的做法？`

**挂钩内容**: 出题策略讨论（验证服务 vs 考试系统）

**调研结论**: ⏳ **待深入调研**

已知的出题策略：
1. **当前验证服务**: 文件顺序（最弱，不看任何学习状态）
2. **当前考试系统**: 三因子融合（BKT+FSRS+KG，权重 ad-hoc）
3. **用户提议**: Plan 文件式逐步递进（类似 Mastery-Based Progression）

**Deep Research 待验证**:
1. **Mastery-Based Learning** (Bloom 1968) — 精通导向，前置概念必须通过才进下一阶段
2. **Knowledge Space Theory** (Doignon & Falmagne 1999) — 概念拓扑排序
3. **Adaptive Testing (CAT)** — 计算机自适应测试，根据回答动态调整题目难度
4. **Zone of Proximal Development** (Vygotsky) — 最近发展区，出刚好超出当前能力的题
5. **Curriculum Learning** (Bengio 2009) — 从简单到复杂的课程学习
6. 社区实现：OpenStax Tutor、Duolingo 的 BIRRT 算法、Khan Academy 的 mastery system

---

## 问题优先级矩阵（供 Deep Research 参考）

```
                    影响大
                      │
         A10(FSRS融合) │  A6(图谱合并)
         A9(RAG路由)   │  A3(评分可靠性)
                       │  A1(RAG靠谱性)
  ─────────────────────┼──────────────────
         A11(缓存)     │  A8(融合质量)
         A5(Graphiti)  │  A4(Graphiti替代)
                       │  A12(出题策略)
                       │  A2(CANVAS_EDGE废除)
                    影响小
         
         已有方案 ◀──────▶ 需要调研
```

## Deep Research 推荐调研顺序

1. **A10 + A3**: FSRS/BKT 融合算法 + AI 评分可靠性 — 决定核心算法是否可信
2. **A6 + A2**: 图谱合并可行性 — 决定架构重构方向
3. **A8 + A9**: RAG 融合/路由成熟度 — 决定检索质量上限
4. **A12**: 社区出题策略 — 决定检验白板的重设计方向
