# Graphiti 记忆燃料策略 · Deep Research 任务书

> 使用方法：把本文件 + 附件 `graphiti-fuel-strategy_pack_2026-07-23.md`（脱敏源码包，348KB）一起上传给 ChatGPT Deep Research。

```xml
<review_request>

<role>
你是「LLM 长期记忆系统 / 时序知识图谱（Graphiti、Zep、GraphRAG、Mem0 生态）」专家审查员。
深度检索中英文一手来源（官方文档、论文、issue、生产实践博客），每条结论带 URL + 证据等级。
不确定就明说不确定；反对我们的判断时直说，不需要客气。
</role>

<goal>
回答一个核心决策：**用户批注（Obsidian callout）是否应该直接写入 Graphiti 作为燃料**，
以及在 vault 数据量激增（预期：概念节点数百→数千、批注几十条/天、每日多学习会话）时，
整个 ingestion 策略应如何设计才能「越用越准」而不是「越用越糊」。
</goal>

<environment>
- 单机 macOS（Apple Silicon），无云依赖诉求，成本敏感
- Obsidian vault（markdown frontmatter 为唯一真相源）+ FastAPI 后端 + Neo4j Community（Docker）
- Graphiti（Zep 开源版）做时序知识图谱记忆；LLM 抽取用本地 Qwen3.5（llama-server，实测 add_episode 约 7 秒/条）；
  embedding 用 Ollama bge-m3；精排 bge-reranker-v2-m3（本地）
- 检索面刚完成一轮治理：25 条 gold set 评测门禁（recall@5 68.18%、重复率 0%、假阳性 20%）、
  cross_encoder 已接线、文本去重、相关度地板、CJK 分词、中英检索束
- 用户是单人学习者（CS 课程 + 数学），系统目标 =「越考越准」的个人学习记忆飞轮
</environment>

<problem>
**当前 Graphiti 燃料盘点（写入面实况，源码见附件）：**

| # | 写入通道 | 内容 | 触发 | 状态 |
|---|---|---|---|---|
| 1 | SessionEnd 会话归档（双通道） | 蒸馏产物（摘要/tips/错误/QA）→ 结构化主链；对话全文 → semantic 影子图 | 每次 AI 对话结束自动 | ✅ 活 |
| 2 | record_learning_memory（MCP 工具） | 对话中显式学习事件 | AI 判断调用 | ✅ 活 |
| 3 | accept_candidate | 用户复盘确认的错误 → Misconception 实体 | 用户点确认 | ✅ 活 |
| 4 | 派生关系实时上报 | 「为什么拆出这个概念」的原因边 | Cmd+Shift+D 派生 | ✅ 活 |
| 5 | 考察事件 | 建检验白板等事件实体 | 出题流程 | ✅ 活 |
| 6 | **批注直连管道** | 批注 callout → 图 | 打批注即写 | ❌ **断（HTTP 410 死代码，历史遗留）** |

**不入图、只留在 frontmatter/文件的燃料**：掌握度状态（mastery_a/b）、校准日志
（calibration_log）、错误候选（error_candidates[]）、批注本体（tips[] + 正文 callout）、
统一学习事件日志（learning_events.jsonl，append-only，8 类事件）。

**批注现状**：用户用快捷键打的 7 类批注（疑问/错误/tips 等）是最高频、最原始的学习信号
（几十条/天的量级预期），但它们**只能间接入图**——等 SessionEnd 蒸馏（有丢失风险：蒸馏
只保留 LLM 认为重要的）或考察流程归纳。打完批注到可被图谱检索之间有小时级延迟甚至永远进不去。

**两难**：
- 全量直连入图：每条批注一次 LLM 抽取（本地 ~7s），几十条/天可接受但数千节点后图膨胀、
  近重实体增殖（我们刚实测过重复率 27% 的教训）、检索噪音回升
- 保持间接：批注延迟入图/有损入图，「打完批注立刻问 AI 就能引用」做不到
</problem>

<already_tried_and_concluded>
- 检索侧治理已完成（不要再建议 reranker/去重/阈值——都做了，附件有对抗审查报告）
- 测试数据污染已清（B 迁出隔离组）；写入层 group_id fail-closed 强校验已上
- AI 抽取的错误已改 candidate_only（用户主权：AI 只提名，用户确认才入图）——
  这个设计定调不动，批注入图方案必须兼容它
- frontmatter 为真相源、图可重建的架构定调不动（learning_events.jsonl 已提供事件重放兜底）
- 曾拍板「舍弃逐批注实时同步」是因为当时管道质量差，不是原则性反对
</already_tried_and_concluded>

<key_files>
附件 `graphiti-fuel-strategy_pack_2026-07-23.md`（Repomix 打包，已脱敏）含 21 个文件：
全部写入面服务源码（memory_service/episode_worker/conversation_distiller/error_writer/
graphiti_structured_writer/learning_event_log）、断裂的批注管道（tips.py，搜 "410"）、
隔离与投影（group_id_compat/subject_config/canvas_projection_sync）、plugin 派生与批注
同步（node-derivation.ts/frontmatter-tips-sync.ts）、检索对抗审查报告、计划 v2、当前任务锚点。
注：包内 3 处 `[REDACTED:env-cred]` 若上下文是 `sorted(key=...)` 即 `lambda` 被脱敏器误伤，非泄密。
</key_files>

<research_questions>
1. **批注入图判据**：个人级（单用户、几十条/天）批注流，社区成熟做法是全量入图、
   规则过滤入图（如只入疑问/错误类）、批量微 batch 入图、还是保持会话级蒸馏？
   判据是什么（检索增益 vs 图膨胀 vs 抽取成本）？
2. **episode 粒度**：Graphiti/Zep 生态对 episode 的粒度最佳实践——单条批注一个 episode、
   还是聚合（按节点/按天/按会话）？聚合的窗口和触发怎么定？
3. **图膨胀治理**：数千节点 + 每天几十 episode 的规模下，实体去重（我们吃过近重实体增殖的亏）、
   community 构建、episode TTL/摘要压缩、边失效，哪些该开、何时开、开销多大？
4. **双层记忆边界**：frontmatter（结构化状态）+ Graphiti（语义时序）的分工边界怎么划最稳？
   哪类信号放文件就够（图只做索引），哪类必须进图才有检索价值？
5. **ingestion 背压与优先级**：本地 LLM 7s/条的抽取吞吐下，队列策略（实时/微批/夜间批）、
   优先级（错误>疑问>tips？）、失败重试与死信的成熟模式？
6. **规模化断点预警**：从当前 118 节点到数千节点，Graphiti+Neo4j Community 单机会先在哪断
   （检索延迟/抽取积压/内存/social community 计算）？各断点的量化阈值和预案？
7. **「越用越准」的闭环验证**：怎么度量「批注入图后检索/出题真的变准了」？
   我们有 25 条 gold set 门禁，批注入图前后应加什么指标？
</research_questions>

<case_requirements>
找 10+ 个成熟案例（Graphiti/Zep 生产使用、Obsidian+KG 记忆系统、个人知识库 ingestion 策略、
GraphRAG 规模化治理），每个 7 字段：
url_primary / url_wayback / accessed_date(+HTTP状态) / info_type(fact|opinion|benchmark) /
sample_size / tier(T1官方|T2权威|T3社区|T4传闻) / fit_score(1-5，对照单机个人学习者画像)
</case_requirements>

<deliverable>
1. 批注入图的**明确建议**（直连全量/过滤直连/微批/维持蒸馏，或分阶段），附判据与反例
2. ingestion 架构建议图（写入通道 × 粒度 × 时机 × 背压）
3. 规模化断点表（量化阈值 + 预案）
4. 案例表（7 字段 × 10+）
5. 分场景建议：当前量级（百节点）vs 激增后（千节点）各自的最小改动
6. 诚实标注 gap：哪些问题社区没有可信答案、需要我们自己实验
</deliverable>

</review_request>
```
