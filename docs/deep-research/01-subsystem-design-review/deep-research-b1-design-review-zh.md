# B1-DESIGN REVIEW: Canvas Learning System 检索管道架构分析

**核心要点:**
*   **管道架构:** 当前的 4 通道混合搜索（LanceDB、Graphiti、Multimodal（多模态）、Vault Notes（笔记库））提供了卓越的召回率，但对于在单用户个人笔记库上无条件执行而言，很可能是过度工程化的。它引入了显著的计算开销。
*   **中文模型选择:** 当前硬编码的 `gte-reranker-modernbert-base` 是一个以英语为主的模型，对于中文查询来说并非最优。`Qwen3-Reranker`（0.6B 或 4B）在多语言和中文文本排序方面显著更优。
*   **CRAG 的效用:** Corrective RAG（修正性 RAG，简称 CRAG）能有效减少幻觉并提高事实准确性，但它天然引入延迟惩罚（通常 >150ms），这直接威胁到系统严格的 400ms 检索 SLA（Service Level Agreement，服务级别协议）。
*   **系统弱点:** 主要弱点包括语言-模型不匹配、高顺序延迟开销，以及缺乏查询复杂度路由。
*   **建议:** 迁移到轻量级的中文能力 reranker（重排序器），实施 Adaptive Routing（自适应路由，即 Adaptive RAG）以在简单查询时绕过重量级通道，并将 CRAG evaluator（评估器）与 reranker 的原生评分紧密集成以节省一次 LLM 往返。

### 执行摘要
本报告对 Canvas Learning System 中的 "B1" Retrieval Pipeline（检索管道）进行全面的设计审查。该系统当前采用 Agentic RAG（智能体化检索增强生成）架构，利用并行 4 通道搜索策略、Reciprocal Rank Fusion（RRF，倒数排名融合）、Cross-encoder Reranking（交叉编码器重排序）以及 Corrective RAG（CRAG）机制来查询个人笔记库。虽然该系统展示了最先进的架构模式，但对其组件的分析揭示了精度、延迟和资源利用率之间的关键权衡——特别是在单用户场景和中文查询部署方面。

### 方法论说明
以下架构分析是基于提供的 `B1-DESIGN REVIEW` 代码库片段、API 规范以及关于高级 RAG 系统的外部文献综合而成。它直接回应了用户关于管道复杂性、reranker 模型效能、CRAG 延迟影响以及整体系统改进的问题。

---

## 1. 架构分析：4 通道混合搜索是否过度工程化？

Canvas Learning System 当前采用了高度复杂的 4 通道并行检索架构。当用户发出查询（例如通过 MCP `search_notes` 工具）时，系统同时查询四个不同的数据源：LanceDB（向量搜索和全文搜索）、Graphiti（时序知识图谱）、Multimodal（多模态，图片和 PDF）以及跨 Canvas 关系 [cite: 1]。

### 1.1 4 通道管道的组成

1.  **LanceDB Hybrid Search（混合搜索）**: 系统使用 LanceDB 进行 Dense Vector Search（稠密向量搜索）和 Sparse Full-Text Search（稀疏全文搜索，FTS）。由于 LanceDB 缺乏原生的稀疏向量列，系统巧妙地利用 Tantivy FTS 结合 `jieba` 分词来实现等效的中文稀疏检索 [cite: 1]。稠密分支和稀疏分支的结果通过 Reciprocal Rank Fusion（RRF，倒数排名融合）进行融合 [cite: 1]。
2.  **Graphiti Temporal Knowledge Graph（时序知识图谱）**: 为了处理多跳推理和时序关系（例如跟踪用户的学习行为或薄弱概念随时间的变化），系统使用了 Graphiti [cite: 1]。Graphiti 将数据增量式地集成到时序图中，允许查询遵循事件时间和事务时间的双时态模型 [cite: 2, 3]。
3.  **Multimodal Search（多模态搜索）**: 此通道处理视觉数据，例如嵌入在 Markdown 笔记中的图片或 PDF 教材摘录 [cite: 1]。
4.  **Vault Notes / Cross-Canvas（笔记库/跨 Canvas）**: 此通道过滤和搜索互连的 `.canvas` 文件和原始 `.md` 笔记，利用 frontmatter 标签和跨学科 Jaccard 相似度桥接 [cite: 1]。

### 1.2 对单用户场景过度工程化的评估

对于管理个人知识库（PKB，Personal Knowledge Base）或学生笔记库的单用户而言，对每个查询无条件执行所有四个通道**在结构上是过度工程化的**。

*   **计算冗余**: 在单用户场景中，数据集通常由几百到几千个 Markdown 文件组成。经过良好调优的 LanceDB 混合搜索（稠密嵌入 + BM25/FTS）通常足以在标准查询中实现 >95% 的召回率 [cite: 4, 5]。对于简单查询（例如"什么是逆否命题？"），无条件执行 Graphiti 节点遍历和多模态嵌入会消耗不必要的计算资源 [cite: 1, 6]。
*   **延迟惩罚**: 系统有严格的 SLA 要求，检索延迟必须保持在 400ms 以下 [cite: 1]。执行四个并行通道，再加上去重、RRF 或级联融合以及交叉编码器重排序，留给错误的余量极其狭窄。如果任何单个通道（例如 Graphiti 遍历）经历冷启动或阻塞 I/O，整个检索阶段都会降级 [cite: 1]。
*   **"检索税"**: 正如高级 RAG 文献中所指出的，对简单查询执行重量级检索管道会施加"检索税" [cite: 6]。简单查询不会从时序图遍历中获益，但却要支付初始化 Graphiti 客户端的延迟和计算成本。

**结论**: 这四个通道的*可用性*是优秀的，但它们的*无条件并行执行*是过度工程化的。系统缺乏一个预检索路由层（通常称为 Adaptive RAG，自适应 RAG），该层对查询复杂度进行分类并仅选择必要的检索通道 [cite: 7, 8]。

---

## 2. Reranker 选择：`gte-reranker-modernbert-base` vs. `Qwen3-Reranker` 在中文场景下的对比

RAG 管道的精度在很大程度上取决于重排序阶段。当前系统架构（截至 Story 2.5）明确硬编码 `Alibaba-NLP/gte-reranker-modernbert-base` 作为默认的本地 reranker，通过 `sentence-transformers` 库以 `float16` 精度运行 [cite: 1]。

### 2.1 `gte-reranker-modernbert-base` 概况

`gte-reranker-modernbert-base` 是由阿里巴巴通义实验室开发的 1.49 亿参数的 Cross-encoder（交叉编码器） [cite: 9, 10]。
*   **架构**: 基于 ModernBERT encoder-only 基础架构构建，支持令人印象深刻的 8,192 token 上下文窗口和 Flash Attention 2 [cite: 9, 11]。
*   **性能**: 在特定基准测试上取得了最先进的结果，如 LoCo（长文档检索，得分 90.68）和 BEIR（得分 56.19） [cite: 9, 10]。
*   **致命缺陷（语言不匹配）**: 尽管由中国公司（阿里巴巴）开发，官方模型规格明确声明其**主要语言是英语** [cite: 9, 12]。由于底层 ModernBERT 架构主要在英语语料库上训练，其 tokenizer（分词器）和 attention heads（注意力头）对中文字符高度未优化。

鉴于 Canvas Learning System 处理中文教育内容（例如 `query="什么是逆否命题？"` 以及 `jieba` 分词）[cite: 1]，使用一个以英语为主的交叉编码器来重排序中文文档将导致严重的分词碎片化和相关性评分降级。

### 2.2 `Qwen3-Reranker` 概况

`Qwen3-Reranker` 系列（2025 年中发布）代表了一个范式转变。与传统的基于 BERT 的交叉编码器不同，Qwen3-Reranker 利用生成式大语言模型（LLM）架构来适配 listwise（列表级）或 pointwise（逐点）重排序 [cite: 13, 14]。
*   **多语言优势**: 它天然支持超过 100 种语言，继承了 Qwen3 基础模型的大规模多语言预训练。它毫无疑问针对中文文本进行了优化 [cite: 15, 16]。
*   **灵活性**: 提供三种参数规模：0.6B、4B 和 8B [cite: 16, 17]。即使是最小的 0.6B 模型也在众多检索任务中超越了此前表现最佳的模型，并提供 32,000 token 的上下文窗口 [cite: 16, 18]。
*   **架构**: 生成式 reranker 通过评估最终位置上特定输出 token（例如 "yes" vs "no"）的概率来比较 query-document 对 [cite: 13]。相比于一个小型的 1.49 亿参数掩码语言模型，这允许对复杂中文查询进行更深层次的语义理解。

### 2.3 比较结论

对于处理中文查询的系统，**`Qwen3-Reranker` 在所有维度上都优于 `gte-reranker-modernbert-base`。**

当前代码库中使用 `gte-reranker-modernbert-base` 构成了一个架构性漏洞。虽然 `gte` 模型速度快（CPU 延迟低于 200ms）[cite: 1]，但其无法原生理解中文语义意味着重排序阶段很可能在引入噪声而非提升精度。迁移到 `Qwen/Qwen3-Reranker-0.6B` 将显著改善中文相关性评分，尽管内存占用略高（0.6B vs 1.49 亿参数）[cite: 12, 15]。

---

## 3. Corrective RAG（CRAG，修正性 RAG）：实际价值 vs. 延迟开销

Canvas Learning System 通过安全降级和质量监控（例如跟踪 `crag_trigger_rate`，目标为 15-30%）[cite: 1] 融入了 Corrective RAG（CRAG）的元素。CRAG 的核心前提是部署一个轻量级的检索评估器，在文档到达生成阶段之前将其评级为 Correct（正确）、Ambiguous（模糊）或 Incorrect（不正确）[cite: 19]。

### 3.1 CRAG 的实际价值

CRAG 在特定的高风险环境中提供不可否认的价值。
*   **幻觉缓解**: 传统 RAG 假设所有检索到的上下文都是有用的。如果检索器获取了不相关的数据，LLM 就被迫基于"垃圾"生成答案，导致幻觉 [cite: 20, 21]。
*   **自适应回退**: 如果 CRAG 将检索评级为"不正确"（例如所有文档评分 < 0.3），它会立即丢弃不良上下文并回退到网络搜索或更广泛的参数化知识生成 [cite: 19, 20]。如果评级为"模糊"，则将本地上下文与外部网络搜索结合 [cite: 6, 22]。
*   **实证收益**: 学术基准测试表明，CRAG 在 PopQA 上比标准 RAG 基线提高了 19% 的准确率，在 PubHealth 上提高了 36.6% [cite: 19, 22]。在企业应用中，它防止过时或冲突的文档条款破坏最终输出 [cite: 21]。

### 3.2 延迟惩罚

尽管在准确性方面有价值，CRAG 在延迟和计算方面代价高昂。
*   **顺序瓶颈**: CRAG 在检索和生成*之间*引入了额外的推理步骤。评估器模型（如微调过的 T5-large）必须针对每个检索到的文本块处理查询 [cite: 19, 22]。
*   **实测开销**: 原始 CRAG 论文报告每次查询在标准 RAG 基础上最少增加约 150ms 的延迟 [cite: 19]。在依赖 API 往返调用评估器的生产环境中，这个惩罚很容易翻倍。此外，如果系统触发了"模糊"或"不正确"路径，执行二次网络搜索会引入巨大的、不可预测的延迟峰值 [cite: 22, 23]。

### 3.3 在 Canvas Learning System 中的应用

在 Canvas Learning System 的上下文中——该系统运行在严格的 `<400ms` 检索 SLA 下 [cite: 1]——**CRAG 代表了严重的运营风险。**

现有架构试图将 LanceDB（向量+FTS）、Graphiti、Multimodal、Fusion（融合）和 Reranking（重排序）塞进 400ms 的窗口内 [cite: 1]。添加一个离散的 CRAG 评估器来顺序评分这些文档，使得 400ms 目标在负载下几乎不可能持续维持。

此外，对于单用户的个人知识库，CRAG 主要功能——网络搜索回退——的效用值得商榷。如果用户询问关于其个人笔记的问题，系统未能在本地找到答案，从网络获取一个通用答案就违背了隔离式个人笔记库工具的初衷 [cite: 19, 22]。

**结论**: 在这个特定的单用户笔记检索管道中，CRAG 作为离散的 LLM 评估步骤带来的延迟多于价值。它*确实*提供的价值（过滤不良上下文）可以通过更快的方式实现——简单地使用 `Qwen3-Reranker` 生成的置信度分数来动态截断上下文窗口（系统已通过 `_adaptive_k_truncate` 部分尝试了这一点）[cite: 1]。

---

## 4. 当前管道中已识别的弱点

基于对现有架构和 RAG 最佳实践的综合分析，B1 检索管道中浮现了几个关键弱点：

### 4.1 严重的 SLA 脆弱性
系统目标是 400ms 检索延迟 [cite: 1]。然而，一个执行多达四个并行数据库客户端（LanceDB、Graphiti 等）、执行复杂的倒数排名融合、执行外部 Cohere API 调用或本地 1.49 亿参数交叉编码器、然后可能还要运行 CRAG LLM 评估的管道，从数学上就倾向于违反此 SLA。测试负载具体列出了模拟延迟：LanceDB（32ms）、Graphiti（45ms）、Multimodal（58ms）、Fusion（5ms）和 Reranking（12ms）[cite: 1]。虽然这些合成数据看起来很乐观，但实际部署——尤其是使用未优化的 Python async 事件循环和冷启动 I/O 时——将经常突破 400ms 的限制 [cite: 1]。

### 4.2 语言/工具不匹配
如第 2 节所述，系统依赖 `gte-reranker-modernbert-base` 处理中文教育笔记是一个根本性的设计缺陷 [cite: 1, 9]。这迫使交叉编码器将词汇表外的中文字符映射为未知 token，破坏了重排序阶段的精度。

### 4.3 管道刚性（缺乏灵活性）
系统使用静态执行图。无论用户提出的是简单的事实检索问题（"重力公式是什么？"）还是复杂的关系查询（"过去一个月我对物理的理解是如何演变的？"），系统都盲目地触发所有检索通道 [cite: 1]。这种缺乏预检索查询路由的做法导致不必要的计算浪费和上下文稀释 [cite: 7, 8]。

### 4.4 未优化的时序知识图谱集成
Graphiti 是一个强大的时序知识图谱，非常适合跟踪状态随时间的变化 [cite: 2, 3]。然而，对*每一个*标准语义搜索查询都通过并行分支查询它是低效的。传统的语义问题不需要时序边遍历 [cite: 3]。在没有上下文感知路由的情况下将标准向量检索与图检索组合，会导致提取出不相关的事实，稀释 LLM 的 prompt 窗口。

---

## 5. 改进策略建议

为了将 Canvas Learning System 从一个过度工程化的概念验证系统演进为高性能、生产就绪的 Agentic RAG 系统，必须实施以下架构改进：

### 5.1 迁移到中文原生 Reranker
**行动**: 弃用 `gte-reranker-modernbert-base`，立即采用 `Qwen/Qwen3-Reranker-0.6B`。
**理由**: `Qwen3-Reranker-0.6B` 提供最先进的多语言排序、32,000 token 上下文窗口，并且专门针对中文语言的细微差别进行了优化 [cite: 15, 16]。因为它是基于 Qwen3 骨干网络的生成式 reranker，比 1.49 亿参数的掩码语言模型能更好地理解深层语义 [cite: 13, 18]。为了适应更大的模型规模（0.6B），应使用优化的推理后端部署，如带 Flash Attention 的 vLLM [cite: 24]，或在 VRAM 严重受限时量化为 INT8。

### 5.2 实施自适应查询路由（L1 路由）
**行动**: 用 Adaptive RAG Router（自适应 RAG 路由器）替代静态的 4 通道并行执行。
**理由**: 在执行任何搜索之前，使用一个轻量级、快速的分类器（或快速的 LLM 调用）来确定查询意图 [cite: 7, 8]。
*   如果查询是简单的事实查找，**仅**路由到 LanceDB（混合稠密/FTS）[cite: 1]。
*   如果查询涉及时序方面（"我什么时候..."、"展示我的进步..."），路由到 Graphiti [cite: 3]。
*   如果查询明确要求视觉上下文，触发 Multimodal 通道 [cite: 1]。
这大幅减少了计算开销，限制了上下文稀释，并确保检索延迟保持在远低于 400ms SLA 的水平 [cite: 1, 7]。

### 5.3 优化或绕过 CRAG 评估器
**行动**: 消除独立的 CRAG LLM 评估器，改用 `Qwen3-Reranker` 的校准输出分数。
**理由**: CRAG 约 150ms 的惩罚来自于使用单独的 LLM（如 T5-large）来评级文档 [cite: 19]。由于像 Qwen3 这样的生成式 reranker 输出校准概率（对应相关性的 logits），系统可以使用 reranker 自身的置信度分数来触发 CRAG 阈值 [cite: 13, 21]。
*   如果 `Qwen3-Reranker` 最高分 > 0.8，继续执行（正确）。
*   如果最高分 < 0.3，触发安全降级或网络搜索（不正确）。
这实现了 CRAG 的全部好处（防幻觉和质量门控），且零额外延迟惩罚，将重排序和评估步骤无缝合并 [cite: 1, 21]。

### 5.4 利用 LanceDB 新特性整合基础设施
**行动**: 关注 LanceDB 路线图，目标是整合图和向量存储。
**理由**: 当前架构为向量维护 LanceDB，为 Graphiti 维护单独的后端 [cite: 1, 4]。管理多个数据库连接增加了故障点。随着向量数据库演进为原生支持图结构，团队应着眼于统一存储层，允许在单次数据库调用中进行混合向量-图遍历，从而大幅减少网络 I/O 和架构复杂性 [cite: 3, 4]。

### 5.5 优化倒数排名融合（RRF）参数
**行动**: 审计 `rrf_k` 常数（当前设置为 60）[cite: 1]。
**理由**: RRF 对 `k` 参数高度敏感。虽然 60 是一个常见的默认值，但它严重偏向于出现在多个列表中的文档，而非来自单个列表中的高置信度文档。在混合差异巨大的模态（Dense、FTS、Graph）的系统中，动态或加权融合策略通常优于原始 RRF [cite: 1]。系统已经具备 `weighted`（加权）融合策略配置；应将其设为多模态集成的默认选项 [cite: 1]。

## 6. 总结

Canvas Learning System 的检索管道是现代 AI 范式的高度雄心勃勃的集成，融合了 Agentic RAG、时序知识图谱和混合语义搜索。然而，其当前迭代存在管道臃肿和语言不匹配问题。

4 通道搜索对于在单用户文本笔记上无条件执行而言是过度工程化的，必须通过 Adaptive RAG 路由加以驯服。硬编码的以英语为中心的 `gte-reranker-modernbert-base` 正在主动损害中文查询精度，必须替换为原生的 `Qwen3-Reranker`。最后，虽然 Corrective RAG（CRAG）在概念上是合理的，但其传统实现引入了不可接受的延迟税，威胁系统的 SLA；必须通过将评估逻辑吸收到 reranker 的输出概率中来进行优化。通过实施这些结构性优化，系统可以同时实现无缝用户体验所需的闪电般的 400ms 响应时间，以及企业级学习工具所期望的高保真事实基础。

**参考来源:**
1. backend/app/mcp/tools/note_search_tools.py (fileSearchStores/persistentcanvaslearningsys-v3fu37ya38pg)
2. [cursor.directory](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFL2fJyUOR3Rp5iqTaVTXP-raLjqyKmLzB_ggTnVWbaJCAWtgLmca4MGJZwU1Ca906_4B1wg-Lss0OS78x549V62mNpfOlK8VgBaMNE-LdliRRb-8BSo3VblkVONA==)
3. [letta.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGpHL20Ob66D1W1K4QQhlGlMc6E2zuSCRXAfVURoptj12sV48zH8We0Gk9mQox6wpJdzEiPbx3Y4FCeDqyF2fYxdtuG5_ehSqLgOHGPnLh-j_OmDkjgYVikE9lKrPG0oVwAGzyuKgmEzUpWhJ4JRzT9o7zYMuVtYAT4xphjmVY=)
4. [stackone.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGY7txCJJUdJ_2KIIDkyD1xi5DBPSyElc4xZ0OKeq-iAhP33GxCsHilQrjERErVlu-wOrBRQQnw1D-NUCx3VHySsUdyBRgwc4LWMBe9wpByY1uliXXc1IP7HXsq5ah0mjslAHjvxdfM_SkSqILknGB-U_8=)
5. [reddit.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQETu2PYrPrJcGeeZS0SgxAHngQsqu_48AR7AigpqosV66NsQ3BnKXUxazhfvnrCyZ33_J8u9pIUzAz8XONQnoxcxikiZEMEoK1ykYcrXP1b-0gFMSvYk1IqKPkdh5fa5Jv-6i2fXAMNAHFugak4GHb5ZgOUn6BbEIC7OEWA-JL1bqI1Wfnb1RKmk056QbtrSxe71piB4buH2aK5_6oy)
6. [chanl.ai](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHjfWeASwKyAUJBYtMJotUIlHPaMa7USuWRUQ5Xd9rQzDlYWLM7K_TtfBUZfZkLRjSc3l1okt-K0eAUyemjUwjxBruEnVJNyLKY4HgeRlo0GZ8WGZ-sJNjzVDPrLQeP3z8oFTk_3VZ7lZI_jckQh5jlTECZ1nyehR4RxnkNYWyRi9FyTE-d)
7. [gitconnected.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG4gzLDeHUqA2jB72h_EiGyfG57jT4kJJqQBN7360IKBgXArqTXW6xkp72PF7Veddo8ibZSx3yZ0AO7u-c17aH-dmTsh-9ATTWkMf4yxfdUVbiigV8CQmk98BqoZPVSR1iXI2wIuUezahGDfX9c-d8O3sSNwnNvtTinMpi6ZEThSUXPZgBnqt-RZooe6wByXYiOB1f2o0UmyhThZ5-G7O54-HH6NHAIXvXr08lq5O3k)
8. [zbrain.ai](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGXTjMWJJFzaGrESosnjhhh9LHgFqwBO8iy1CCDC5aZVEq_WUOhxvl1zBZMl4oqvQX283o4ke8FQKj4rGv7NkNJLHVAvJGYGAmi8Jzg-gzo7bkMY2U=)
9. [huggingface.co](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQExjS3dkQ93X9bjIdq1i7QpBsDB6Nvn81OiLgdwre-mKHLOP9P_q4kSVJEECRZo3wqS9TXDA9VlINJfCdj3iwPfaow4eGjDX8c143tum465TGmGJICefnSnUrJED4xnh0ghLhZ8Lzb1dSLgQxmVzrjbismyHzU=)
10. [promptlayer.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGwgutbLpY4JKdZZ2Wi3JqbLsng47UUeyjSgJFdBK1hQhXkjKsFVEI7WtWn1jCKzLrmOV--_-nw3YlPT9NjqqOZBFt5DfEP6jUABho3LeIBdzME1nX68X58DJClYIYMlSl2Fwks9aG57haSId_cxNvtcHW2lwA=)
11. [modelscope.cn](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG9L3z1CxcypVJCNQ3WSLN0tCPJP9opjXZ_4XabJCqA_neH4esfHwj9E_r504dA71Rt3TLjgfZTIZCac9466jQgfvj3e4CPPPN34ip-QHnUul2U16FQ8e87P1VPKvs92GpmvUpSfmTgJ-TEa9w3VVLej3-hB636dQCqTW_41Z15vQIsG3GkAn9lHJQ=)
12. [huggingface.co](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFmRqXQu5fClyurZYeAvI1Fb2d7zoVWr26SjlB9msaIkHsNQ3oMSFSWm2T512YZcastCfJfr0kTuoX9MVu626KwrL0JgjMMxw25wYmS4ippOG9gM0WdCsd39W3rhiVoob9wo0zhkCAr_O3fpV0=)
13. [readthedocs.io](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH1tWjKFglROz6vfFfS0WqPCTrgKxB7y4s_Xlyk3K4wqgAIOPBJlZlAf4KccnzYj5-cDvhG492vnzEcW9-F5Eedx2wfdwvQ1DN-1paMsfsq21u9zpXyarn7xNkjP0cQVX5fa0MKhi_meM6TZ8b7zU1BX9EQhTTF)
14. [arxiv.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGXK46NEq66XeRBnfEWTATvdl60iCJ0FBxOnvD60QhLBBXxSVI2s0t5poM4q7TNhTkDY6qmzxxQ8M75a8ULAIKVy1PDYbJsKSA1iTrwoOj0utLc05RtIw8tFw==)
15. [huggingface.co](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHMCPztOHy-tgOxruB8SjguWMF7mZpUtyJOq8XkSTQ1uy4OVAHm5n5rKmTT7-b9wZv-ya1NoZFhLT-zknmahlZqdzaHxC135tNQCWQV7w8sUq1u0uoKA8167A4kptFqX7RzraM=)
16. [huggingface.co](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEQ19-_VuQx-zHThAqRGaR-nXlxn7hOkimFMnegK3gw8FmEmRwoEg_3ixH_bDlaZIWAKkQrL23MRoqMflu8NWHhCAt_McNmhNKqfi5NnR8962wyG6_ED-str5p0GYYE9gjONfM=)
17. [huggingface.co](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHdww1j0FBF3_soadstJQOxu1S__rxY8Y1Q3YMLjeWVzTtur7024GaVekRtn816-0AOFbvgrXBv_JtbaEumJHziSBSKeKVL3bwd5nTguglVwF7hYn2dYMUlck0hFl2zivokbcK6qA881l6uRXs=)
18. [arxiv.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEzthcpm-YNrJtiQoxtv9A4u1KABt14IyYrsSUvGyimthtLoHrbBwHgOspI5vwoRrDSZr-zfZ6XYrds9k-mWCWIRskLLHBPbKjVK-BNTXFNoiIkfSwCUxrODQ==)
19. [towardsai.net](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE8WhF5G2ICjg8kWx57-Jq12Eqi_JxQJhN4fDppHxxzpQRghHXW5ziOHaQkl962K3JUFMHvF1vSU_oB3fK5I6oDm6vFbcbHa9xafsnu2kKwDqiBcPI0DwVm_5N69UMLAxbZNYu8ti7mS_ykrhij9R1Lmpc8w-T2d4Xwc0I86eJTXOcndKcnQI5-7aSpehu52b20E0HoABZXqv3xondkBqfcmkYtmrKO9Ll9sZUQGeYSYKM=)
20. [plainenglish.io](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG7aNRByeSIEoZye0HNFpf7nWtsTqcovEUruoyYuUl9ywQ1e3YFHJ0LlTpZM9i_30e5im0MPmZq6A4qPt7u2mAfaTfOVf5oltd38l6Sprd85eOMBGh7vc_4a03BTexZTYiYJuT8DetLMEWwusLeHsWn6Rw-i1Ut3R1xli90VvXsltk-1Jmh32RLI6ecWHNOgvmuXcLOgl3WXp--49viQZtnNw==)
21. [medium.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFpQ_Xhkl0N9I4JCJzcF-T5wwG0216u5-UjJWhOedSeNWoTtiVP9QkLgO7srmmpjJ7xxKQmht3wHV8IdLZXyE-uHmWNwHiQnUroOIra15T5_oQKvzolEiSi5wM1w5sXT-UPN5dfw-QOk2VzlpBQSAxRI1056aXpM2EcEuus2pfLU8W0yNvyLIm_sjZFEHdSn2CXkuS76ma0k4fnfKuflnbND5GsJK5-7MZGP73ZHwnNDjb3vEdqM7h4E9EQFKc=)
22. [medium.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHmWiNfbA15wDz7X_5Ns7iviXm8OJnDjMdLWLX7OvqIkHSPl07ixajq2KD60jmv2Pa13Q0s54FPRIsTWLKxdzlEY0h68YWq5HVjunlrB_inbT6BE0S9mx1lU3uYhRBxtOAexONy50y7iaFHQWmjyjqI9g==)
23. [medium.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHkPmrW1veheS-4cVx1Y--Dhz3t4TDEpQSJe3v2UUrWQO3FM6hgy128Q3wyFQz_YkcOWopW-ZqvdxMwD6TwvbmEytURs3c4oZzDCvzjpH0IcyYDgcFQOeb80adBPTH0pPu6tUZTh-lW5neW-A88IXLfz4gNicY=)
24. [vllm.ai](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEO0BoO-iUvY7TkNUm2cgw3QuuDt3Pl7AyrU5KHRJIIbZ6Lz9usCJifTET7oERYUf6saYNQaCydCcV7zr95r-tma2ZGbA753YP3wVGue0T-6nP-_G-3Q1pnOLNMylj-dH7Zyuk0IbTiwgqiV0S38IDzZMO6GFZWoMHbhhNQVIpIHTM0usGrZo_NJQ==)
