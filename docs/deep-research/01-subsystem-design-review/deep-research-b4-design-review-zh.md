# B4-DESIGN REVIEW：考试系统架构综合分析

**核心要点：**
*   **错误类型抽象化：** 系统将错误归纳为四种认知错误类型，在 3K token 限制下提供了必要的计算效率，但研究表明这可能过度简化了现实中细致入微的数学和逻辑误解。
*   **补救策略有理论根基：** 动态画布策略和四级提示链与 Constructive Alignment（建设性对齐理论）和 Knowledge Space Theory（知识空间理论，KST）高度一致。
*   **评分可靠性：** 采用 3-shot self-consistency（3 次自一致性采样）模型配合多数投票，能有效缓解 Large Language Model（大语言模型，LLM）的幻觉问题，但相较于最优的集成方法（如 20 次采样的 SURE 框架）仍然较为粗糙。
*   **三角测量启发式方法：** 集成 FSRS、BKT 和 Knowledge Graph（知识图谱，KG）相关性在数学上是合理的且经过计算优化，前提是需要严格监控信号冗余。
*   **已识别的主要风险：** 系统性漏洞包括节点生成无上限、跨层错误累积，以及因未经验证的回写导致的潜在知识图谱污染。
*   **战略改进建议：** 需要立即实施 FR-EXAM-09（生成限制）和 FR-EXAM-10（考后审查门控），以维护教学完整性并防止视觉混乱。

以下报告讨论了 B4 考试系统的关键设计组件、教学有效性、算法可靠性以及系统性风险。从目前来看，虽然该系统代表了 AI 辅助个性化教育的范式转变，但管理动态生成能力与严格教育评估标准之间的张力仍然是其核心挑战。

***

## 1. 四种认知错误类型评估

B4 考试系统的一个基础机制是其补救策略，该策略将四种不同的认知错误类型——**Breakthrough Error（突破性错误）**、**Reasoning Fallacy（推理谬误）**、**Knowledge Gap（知识缺口）** 和 **Partial Understanding（部分理解）**——以编程方式映射到针对性的 prompt injection（提示注入）策略 [cite: 1]。要判断这四种错误类型是否足够，需要审视底层的教育框架和系统的计算约束。

### 1.1 与 MathCCS 基准的比较

该系统的错误分类方法深受个性化错误诊断领域最新进展的影响，最值得注意的是 Mathematical Classification and Constructive Suggestions（数学分类与建设性建议，MathCCS）基准 [cite: 2, 3]。MathCCS 是一个多模态、多类型的错误分析基准，整合了真实世界的数学题、学生答案和专家标注 [cite: 3]。

原始 MathCCS 数据集包含约 70,000 条来自小学生的解题记录，采用由专家标注的分类法，包含 9 个主要类别和 29 到 37 个子类别（取决于数据集的迭代版本）[cite: 2, 4]。具体子类别的示例包括：
*   移项符号错误 [cite: 4]
*   基本运算错误 [cite: 4]
*   模型误用 [cite: 4]
*   注意力细节错误 [cite: 4]

相比之下，B4 考试系统将这些高度细粒度的子类别抽象为恰好四个宏观认知维度 [cite: 1]。

### 1.2 充分性与计算效率

将系统限制为四种错误类型的决策，是 **Assessment Context Pack（评估上下文包，ACP）** 架构的直接结果，该架构必须在严格的 3K token 预算下聚合 Graphiti 记忆、精通度指标和对话上下文 [cite: 1]。

1.  **Breakthrough Error（突破性错误）**：映射到"注意力细节"或执行层面的失误。
2.  **Reasoning Fallacy（推理谬误）**：映射到"模型误用"或逻辑失败。
3.  **Knowledge Gap（知识缺口）**：映射到"核心概念未掌握" [cite: 4]。
4.  **Partial Understanding（部分理解）**：映射到 Bayesian Knowledge Tracing（贝叶斯知识追踪，BKT）中的过渡状态。

**四种错误类型够用吗？** 从纯教学角度来看，四个类别构成了一个还原性的分类法。使用 MathCCS 基准进行的实证评估显示，即使是最先进的多模态大语言模型（MLLMs），如 GPT-4o 和 Claude 3.5 Sonnet，在面对完整的 37 子类别分类法时，分类准确率也难以超过 30% [cite: 2, 4]。

然而，从架构和运营角度来看，四个类别是高度务实的。鉴于 ACP 的 3K token 预算 [cite: 1]，将 37 类别的分类体系传入 LLM 的上下文窗口会挤占关键的运营数据，如 Graphiti 记忆和对话上下文 [cite: 1]。此外，这四种类型直接映射到可操作的 prompt injection 策略 [cite: 1]。一个高度细粒度的错误（如"移项符号错误"）和一个更广泛的推理错误，从根本上都需要"Reasoning Fallacy"补救提示来引导学生回归逻辑一致性。因此，虽然四种类型在诊断粒度上有所妥协，但它们足以驱动可操作的、差异化的教学干预。

## 2. 教育研究视角下的补救策略效果

B4 考试系统实施了一套动态的、上下文感知的补救策略，由一组功能需求（FR-EXAM）管控。通过既有教育研究的视角分析这些策略，展现出了高度的教学有效性。

### 2.1 Constructive Alignment 与画布策略（FR-EXAM-13）

系统根据特定学习画布的性质动态定制考试策略，这种方法植根于 **Constructive Alignment（建设性对齐）** 理论 [cite: 1]。该理论由 John Biggs 于 1996 年提出，主张评估任务必须与预期的学习成果直接对齐 [cite: 1]。

B4 引擎利用信号分类启发式方法（`_classify_content`）来评估画布中的所有文本，累积 `knowledge_signals`（知识信号）和 `problem_signals`（问题信号）[cite: 1]。
*   **Point-to-Point Mode（逐点模式，知识信号 >65%）**：分配给知识密集型的概念图。它隔离单个概念，深入定义准确性和概念辨析 [cite: 1]。这与 Bloom's Taxonomy（布鲁姆分类法）中的 *Remembering*（记忆）和 *Understanding*（理解）层级对齐 [cite: 1]。
*   **Comprehensive Mode（综合模式，知识信号 <35%）**：分配给问题密集型的流程板。它要求综合多个节点来解决复杂场景，与布鲁姆分类法的 *Applying*（应用）、*Analyzing*（分析）和 *Evaluating*（评价）对齐 [cite: 1]。
*   **Mixed Mode（混合模式，信号 35% - 65%）**：通过算法在诊断性逐点问题和整体性综合问题之间切换 [cite: 1]。

这种动态映射确保了补救策略的生态效度。用定义性闪卡测试一个流程性数学白板将违反 Constructive Alignment；B4 系统的自动路由机制可以防止此类教学失误 [cite: 1]。

### 2.2 Knowledge Space Theory（知识空间理论，KST）与外部边缘

该系统的补救策略从根本上与 **Knowledge Space Theory（知识空间理论，KST）** 相连，这是 Doignon 和 Falmagne 于 1985 年提出的一种非数值评估的数学方法 [cite: 5, 6]。在 KST 中，一个知识领域是概念的集合，学生的知识状态是他们已掌握概念的子集 [cite: 6]。

B4 系统利用了 KST 中 **Inner Fringe（内部边缘）**（学生已掌握且可回退的内容）和 **Outer Fringe（外部边缘）**（学生在概念上已准备好学习的下一步内容）的概念 [cite: 6, 7]。在递归考试过程中，AI 根据学生的表现，从 Outer Fringe 生成新发现的节点 [cite: 1, 6]。通过沿 Outer Fringe 构建补救路径，系统在学生的 Zone of Proximal Development（最近发展区，ZPD）内运作 [cite: 5]。

### 2.3 四级提示链

当用户在某个概念上遇到困难时，B4 系统采用四级渐进式脚手架机制（FR-EXAM-19）[cite: 1]。
1.  **Level 1（第一级）**：方向性提示（不暴露答案）。
2.  **Level 2（第二级）**：关键词提示。
3.  **Level 3（第三级）**：部分答案框架。
4.  **Level 4（第四级）**：逐步引导支架。

关键的是，系统不提供"直接答案"选项，强制要求认知参与 [cite: 1]。这种"Chain-of-Hints（提示链）"策略得到了认知科学的充分支持，能够防止过早的认知闭合并鼓励有成效的挣扎过程。

## 3. LLM 评分在实践中的可靠性

使用大语言模型对开放式简答题进行自动评分，长期以来一直受到准确性不一致、系统性偏差（如评分偏低）和幻觉问题的困扰 [cite: 8]。为缓解此问题，B4 AutoScorer 系统实施了 **3-shot self-consistency sampling methodology（3 次自一致性采样方法）** [cite: 1]。

### 3.1 3-Shot Self-Consistency 的机制

Self-consistency decoding（自一致性解码）将推理路径的生成与最终答案的选择解耦。它基于一个前提：不同的正确推理路径往往收敛到相同的答案，而幻觉或错误的路径通常是独特的 [cite: 9, 10]。

在 B4 的实现中，系统对 LLM 执行三次独立查询，根据四维 SOLO 锚定评分标准（Concept Accuracy（概念准确性）、Reasoning Quality（推理质量）、Knowledge Coverage（知识覆盖）、Knowledge Integration（知识整合））对回答进行评分 [cite: 1]。总分范围为 0 到 12 [cite: 1]。然后系统使用 `statistics.mode` 进行多数投票 [cite: 1]。

```python
except statistics.StatisticsError:
    voted = int(statistics.median(values))
    final_scores[dim] = voted

    if max(values) - min(values) > 1:
        low_conf_dims.append(dim)
    return final_scores, low_conf_dims
```
*（展示 B4 回退逻辑的代码片段 [cite: 1]）*

如果三次采样产生完全不同的分数（例如 [cite: 1]），则抛出 `StatisticsError`，系统默认使用数学中位数 [cite: 1]。此外，如果最高分和最低分之间的差异超过 1，该维度将被标记为 `low_confidence`（低置信度），可以触发人工审查 [cite: 1]。

### 3.2 与 SURE 框架的对比评估

近期学术文献，如 Selective Uncertainty-based Re-Evaluation（基于选择性不确定性的重新评估，SURE）框架，为评估这种方法的可靠性提供了参考 [cite: 8]。SURE 研究使用 GPT-4 等模型评估答案，发现基于 20 次重复提示的多数投票显著降低了评分偏低的偏差 [cite: 8]。

该研究特别指出，将样本量减少到 7 次会导致更粗糙的确定性估计，这意味着偏离多数投票的情况更加频繁 [cite: 8]。B4 系统仅使用 3 次采样（很可能是为了在实时考试环节中控制 API 成本和延迟）。虽然 3 次投票在推理任务上相比单次提示（贪婪解码）可获得 5-25% 的准确率提升 [cite: 9]，但从统计学角度来看，它比 20 次集成采样更为粗糙。

然而，B4 系统纳入的不确定性标志（`max - min > 1`）[cite: 1] 是非常精巧的。它在功能上复制了 SURE 框架基于不确定性的标记机制，使得混合式 Human-in-the-Loop（HITL，人在回路中）的安全保障成为可能——将低置信度分数传回给用户或管理员 [cite: 8]。因此，虽然受限于 3 次采样的数学约束，但由于其严格的边界检查和中位数回退逻辑，评分可靠性在实践中是功能健壮的。

## 4. FSRS + BKT + KG 三角测量启发式方法的复杂性

节点选择机制是 B4 个性化考试的引擎。为优化认知效率，系统执行了一个统一间隔重复算法、认知状态建模和拓扑相关性的三角测量启发式方法 [cite: 1]。

### 4.1 优先级公式

该公式在 `QuestionGenerator` 的 `select_target_node` 方法中实现，每个符合条件的节点被分配一个数学优先级分数：

```python
priority = (
    W_MASTERY * (1.0 - p_mastery)
    + W_RETRIEVABILITY * (1.0 - retrievability)
    + W_KG_RELEVANCE * kg_relevance
)
```
*（定义优先级公式的代码片段 [cite: 1]）*

架构规范中的权重如下：FSRS Urgency（FSRS 紧迫度）40%、Behavior Weight/Mastery（行为权重/精通度）30%、Network Centrality/KG（网络中心性/知识图谱）20%、Interaction Weight（交互权重）10% [cite: 1]。在代码逻辑中，`W_MASTERY = 0.4`，代表 Bayesian Knowledge Tracing（贝叶斯知识追踪，BKT）的精通概率 [cite: 1]。

### 4.2 组件解构

1.  **FSRS (Free Spaced Repetition Scheduler，自由间隔重复调度器)**：FSRS 使用三组分 DSR 模型（Difficulty（难度）、Stability（稳定性）、Retrievability（可提取性））[cite: 11, 12]。通过计算 `1.0 - retrievability`，系统优先选择学生在统计上即将遗忘的节点（可提取性接近 90% 或低于 `shaky_threshold` 0.40）[cite: 1, 11]。
2.  **BKT (Bayesian Knowledge Tracing，贝叶斯知识追踪)**：BKT 是一种 Hidden Markov Model（隐马尔可夫模型），追踪用户掌握某一特定概念的潜在概率（`p_mastery`）[cite: 1]。通过计算 `1.0 - p_mastery`，系统优先选择学生近期表现不佳的概念。
3.  **KG (Knowledge Graph，知识图谱) Relevance（相关性）**：由 Network Centrality（网络中心性）表示，确保先修节点或高度连接的核心概念优先于边缘琐碎内容 [cite: 1]。

### 4.3 是否过度复杂？

从表面上看，将三个不同的数学模型合并为一个线性组合存在特征重叠的风险。FSRS（Retrievability）和 BKT（Mastery）都随时间追踪认知表现。

然而，设计明确解决了这一风险。FR-MAST-06 规定这些信号必须表现出互补性，要求指标间的相关系数 `< 0.7` 以验证其独立性 [cite: 1]。FSRS 追踪的是*随时间推移的记忆衰退*（不考虑底层逻辑），而 BKT 追踪的是*技能习得概率*（不考虑时间流逝）。

在计算方面，当评估庞大画布中每个节点的优先级时，存在 N+1 数据库查询的风险。B4 的实现通过 `asyncio.gather` 缓解了这一问题，将 Mastery 和 KG 查询并发批量处理（`mastery_results, kg_results = await asyncio.gather(...)`）[cite: 1]。

结论：三角测量并非过度复杂；它是必要的多维向量。仅依赖 FSRS 会将系统变成一个简单的闪卡应用 [cite: 11]，而仅依赖 BKT 则忽略了间隔效应的神经生物学现实 [cite: 13]。KG 相关性的加入保证了考试环节维持结构化的课程连贯性。

## 5. 系统性风险与漏洞

尽管有着坚实的架构基础，严格的设计审查揭示了 B4 考试系统内的几个关键漏洞。这些风险主要源于 AI 智能体与知识图谱交互时的递归生成特性。

### 5.1 无限制生成与视觉混乱（Gap 4）

在递归考试过程中（FR-EXAM-06），AI 可以根据学生的对话输入和发现的盲点生成新的概念节点 [cite: 1]。然而，一个已记录的系统性缺陷（"Gap 4"）指出，目前在单个会话中 AI 生成节点的数量没有上限 [cite: 1]。

如果学生进行长时间的对话，AI 可能会同时产生数十个新节点。这会导致 UI 上严重的**视觉混乱**，破坏布局计算（例如，聚类间距降至最小 100px 阈值以下）[cite: 1]，并造成用户的认知过载。

### 5.2 跨层错误累积与知识图谱污染（Gap 3 和 Gap 5）

更严重的教学风险是"Gap 3"（跨层错误累积）和"Gap 5"（回写无质量门控）[cite: 1]。
由于 LLM 可能产生幻觉 [cite: 8, 14]，AI 可能错误地将用户正确但非常规的推理识别为"Knowledge Gap"。因此，它可能生成一个幻觉化的"盲点"节点 [cite: 1]。如果没有质量门控（Gap 5），这些不准确的节点会被永久写回原始学习画布的知识图谱 [cite: 1]。经过多次会话，这会造成**知识图谱污染**，降低未来 RAG（Retrieval-Augmented Generation，检索增强生成）查询的有效性并破坏课程体系 [cite: 1]。

### 5.3 技术债务：分词与单体命名空间

在数据层存在两个严重风险：
*   **分词失败（高风险 H1）**：LanceDB 的实现使用 Tantivy 全文搜索引擎，默认采用空格分词。连续的中文字符（如"贝叶斯定理"）会被散列为单一 token，导致检索失败 [cite: 1]。
*   **单体 `group_id`**：系统的早期版本将所有 Graphiti 记忆和决策转储到单一的 `group_id` 中。这种结构性缺陷破坏了检索精度，因为智能体会被矛盾或无关的记忆干扰 [cite: 1]。

## 6. 战略改进建议

为确保 B4 考试系统的教学有效性和架构稳定性，必须优先实施以下改进：

### 6.1 实施 FR-EXAM-09（生成限制）

为解决 Gap 4（视觉混乱）并与 KST 的"Outer Fringe"原则对齐，系统必须对节点生成实施严格限制。
*   **建议**：按照深度调研笔记中的规范实施 **FR-EXAM-09** [cite: 1]。在单次考试会话中，系统生成的新发现节点不应超过 $N$ 个（建议 $N=3$）[cite: 1]。这些节点应严格按照其在知识图谱中与当前主题的拓扑距离排序，优先选择最直接、最高度相关的先修概念或概念邻居 [cite: 1]。

### 6.2 实施 FR-EXAM-10（考后审查门控）

为解决 Gap 3 和 Gap 5（知识图谱污染），系统必须将知识图谱的控制权交还给人类用户，确保有 Human-in-the-Loop 的安全保障来对抗 AI 幻觉。
*   **建议**：实施 **FR-EXAM-10** [cite: 1]。在考试会话结束时，系统必须呈现一个"购物车"风格的摘要面板，展示所有新生成的节点 [cite: 1]。这些节点应保持临时状态标记（例如"待确认"）。用户必须手动批准或拒绝每个节点，才能将其永久写入原始学习画布 [cite: 1]。

### 6.3 解决数据层瓶颈

*   **分词器修复**：在 LanceDB 摄入之前，使用 `jieba.cut(text, cut_all=False)` 精确模式对所有非空格分隔语言（如中文）进行预处理。token 必须用空格连接，以便 Tantivy 引擎将它们作为伪英文单词进行索引 [cite: 1]。此外，将搜索模式默认设置为 `Hybrid`（Dense bge-m3 + FTS）以获得最佳召回率 [cite: 1]。
*   **分类命名空间**：重构 Graphiti 的 `group_id`，使用严格的分类命名空间。实施隔离边界，如 `{project_id}__feature_specs`，以保证多租户隔离并消除检索噪音 [cite: 1]。
*   **Layer 1 上下文隔离**：为防止前端 UI 组件与 FastAPI 后端之间的跨层漂移，强制执行 OpenAPI 契约自动生成（`schema.json`）。SubAgents 必须被沙盒化，严格从 schema 读取，以确保 API 一致性 [cite: 1]。

***

### 表 1：系统组件与效果总结

| 组件 | B4 实现 | 理论基础 | 评定 |
| :--- | :--- | :--- | :--- |
| **错误诊断** | 四类型映射 | MathCCS Benchmark（9/37 类型）[cite: 2, 4] | 在 3K token 限制下的务实简化；存在遗漏细微差异的风险，但确保了可操作的提示 [cite: 1]。 |
| **画布策略** | 逐点、混合、综合 | Constructive Alignment（Biggs, 1996）[cite: 1] | 高度有效；确保评估匹配认知需求 [cite: 1]。 |
| **评分引擎** | 3-Shot Self-Consistency（众数/中位数）| SURE Framework / Majority Voting [cite: 1, 8] | 稳健。`max - min > 1` 不确定性标志正确处理了 3 次采样限制的统计粗糙性 [cite: 1, 8]。 |
| **节点选择** | FSRS + BKT + KG 线性优先级 | Spaced Repetition、Markov Models、KST [cite: 1, 6] | 数学上合理。通过异步批量处理避免了 N+1 查询瓶颈 [cite: 1]。 |

### 结论

B4 考试系统展示了认知科学、心理测量学和大语言模型架构的高度精巧综合。与 MathCCS 基准相比，简化为四种错误类型虽然在理论上较为狭窄，但却是一种必要且高度实用的工程妥协。通过三角测量启发式方法整合 FSRS、BKT 和 Knowledge Space Theory，为个性化间隔重复提供了精英级标准，同时没有陷入不必要的复杂性。

然而，AI 的生成特性在知识图谱污染和 UI 混乱方面带来了严重的系统性风险。通过部署推荐的 Human-in-the-Loop 审查门控（FR-EXAM-10）和严格的拓扑生成限制（FR-EXAM-09），系统可以缓解这些风险并实现卓越的教学效果。

**来源：**
1. docs/deep-research-b4-exam-system.md (fileSearchStores/persistentcanvaslearningsys-z2njevmxp7md)
2. [themoonlight.io](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH1lcIGPFEH-Ct6YtrqnseCLmjyrqUihWmEckg09E_HztC5S6LCRy6ZqC7VYn1q2pbGKNhiZx5NtmbF7cT0BSt16IMr15Pd-IMxAcfS_gWMOParW_2bMn3CT_2KYPcSQiH0eNVG5ZxmogK8AQd35I-KSRIfoZtWcgHHCvcFoa-9hwrz4R7KDcwUDVgwF_B8Wa8Y3dWaQtRoMCqrIeVcTKNWuybIqoLgXfDewmSwwOqljdqHnyc=)
3. [arxiv.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGef-Mk0q-7W8tTO7Jv4xqzDBLau-4ESFMItt9N9vLgcnmx0MlQr5289hXnZCUFGqMoXtubA67ELrfQCKEHUZb2cOH_PM1qPgg3Qf6P78Ah4sy16gxAuhFa)
4. [arxiv.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGEsqlqP02lrKjOXNg_y_4gyR8YvgvYLVnEg5gePfScEH2d1U7tu8a9we5hNXp029qsntLl6zxnud_7pOSOekz3BSJvsWerU_7kWuPFWspmSE6oupFMPw==)
5. [github.io](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQF14Vb_AmHgezdxGDHy0onDA6fjCJXDUPHRD20FLUhBOB83tQEX0pEeIxFl74B7_Vj1zOuIexYyAguT4xZXDw_Xoq2ETWz-Lm3Z7y-Hjcc6fIpE-7mekutNLiCfko3RBpmj520VrIqFgACFSYOlWDy8kEjVAPAGFVJ3aaa6hkejROYPN1s3Jw==)
6. [wikipedia.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE-KsosMh9togZgj68kxLHtlNSPS_2xdCq_pRDj_XVrTACtgbfdZuc-3fPFZjPEvyeXb0124AtT4spVhfy6VCDB4OaFAoGFWGiZ4Ur8Enqbel4wuia0XClXMh3x6Vh5F2owAQ==)
7. [medium.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHZApfsVzNQ1gkuly9RwWkn2yvq-R6UhtG_28Aa0nIxwozOTipeecMIFxMtU1OepzGH7wSrR19VXv_WyNNrh4uf5-FrP4Wst6mYrVf_P1J35WLwggPyflJw1UaxuXd7SqCqfxKiBKvbGB78PjJYx2ZrGAuldgUd6ETAmxlDbxjOp-vVvQ==)
8. [mdpi.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEwLszsLNZEDRlNaCw_ltZ45ZQ3eohxOlWWYXuHD7duhenDMHDEkUNhOi5qfjRKZuH0eCUVapxLDUYKQAPjiJy7e_ZM3RtEKM-ns6P_5X8xZrwSHgRJRIC-nEA=)
9. [medium.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG9xqGVlAIHe842QcuAEw0PTE2cGoTyMtHzSu0a8MPi53b1BhhUk1rQPjlW5vhp5VUCuRtkrBHcLQnE5WkZD-EvcZqXMVSzj2QRUP4n2p20TjGZTq5KnGRnfDpjMfzBaGtKoOZSp6iKqLo3MkQSj_pA92HA96MwuuVaviyb3EShbfkGBnxAHUvKHNZ_fNLrooeH-t6Tiow2kHMNozTt7Jw2iH3wYgs=)
10. [emergentmind.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHlQerp5o29fqYFiljJbbHxDogEjO1EQi90K8oIUIMsprjEFeyIfQ0RpSmJtqtNuOVEbJxDdOUJasMovR0zGCQQvlDdmeyABtf_bb80jgcJVQuFusmjuDvJkqxWUrByPvDs9apMrndnT3--sBB84j5wq1Cc)
11. [domenic.me](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHuAayDKwHYbOECNi89XHfWvN6xkFjVwPrujVCzYG_8wcwwtg58nywpw0YkYBeUQLGhIXiqGnEDRZPkFdSeDeJHDwdIKoiejvlUxN9KPw==)
12. [reddit.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFqlVUfR402aEvOXBaUDHdsYROGxZakKpkPnhIVyfiEgBHMsA1iqg8xlCIS9-kXqv8ERc2vpEE0HjKprr7YUZtL6W-QpRXQZ_BfpVXRlkrfGDdMNqn020UjqQhEawJCwoaPW39MopEY-90o4TKTxmc_bX99OattcaX8uKIm2yJv_fJBiZelNTwCa87SH4t4Rqaqyhk6H_w=)
13. [reddit.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHU3NfJ3onNGHGYnF2EiWvVmgbOeU3SbIWp7Egttwf5wMAwspZpBuke-vdt-Ie5mFxqRuTLuBl23MkytLKsjCGCS_l7b54shZta0ruZH7BoeVlOhN6kUCHv1zMvBowgYWYfJqS8e0dHxmk95E5Q7Wwxs_D1FkcwsCbDMaSmK-aFSCpJUk1veN80FZ3hIw==)
14. [aclanthology.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE2ivGWAWiJWcb-EB0RvnCwIhCT-6BjqoGR9tKAYAjnqtQjL5CQifxWhLUxL9MyVLLuebbvi6Y5AiwYL_L3fyw2JAG61iFfiVZkIv_4iXQp14ehaSMpOi7GoJGcbhmlEy_6OIlslyROw0M=)
