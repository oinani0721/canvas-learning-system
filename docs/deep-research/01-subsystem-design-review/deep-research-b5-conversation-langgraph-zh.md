# B5 对话管理与 LangGraph 架构综合分析

* 要点：
* 研究表明，某些 LangGraph 原生功能，特别是内置的内存 checkpointers（检查点持久化器）和原生多智能体 supervisors（调度器），目前并未被使用，取而代之的是自定义状态管理和基于环境变量控制的阶段门控机制。
* 该系统采用了高度结构化的 agent graph（智能体图），包含意图分析、检索、评分和答案生成等独立节点，并通过条件边进行管理。
* FSRS（Free Spaced Repetition Scheduler，自由间隔重复调度器）的集成极有可能成功实现了长期记忆衰减管理，当用户长时间未学习时，通过指数数学回退方法动态计算可检索性。
* 有证据表明系统实施了三层上下文窗口策略，通过严格的 token 与字符比率分配，在完整上下文、合成摘要和按需检索之间取得平衡。
* 会话管理在节点层面通过浏览器端的 `localStorage` 和持久化 JSON 配置文件得到了稳健处理，并具备暂停和恢复对话验证的机制。
* 该架构使用先进的句子级抽取方法处理上下文压缩，在通过 token 重叠评分评估相关性的同时，保护"原子块"（如代码和数学公式）不被截断。
* 对话归档的实现高度依赖三态 Hot-Warm-Cold（热-温-冷）模型，采用双触发器（时间流逝和 token 容量阈值）来安全地精炼和转移记忆。

本报告综合梳理了 B5 对话管理系统的架构机制。报告旨在清晰、全面地阐述该平台如何将先进的基于图的路由（LangGraph）、时间记忆建模（FSRS）、token 预算优化和对话归档等技术紧密结合在一起。对于研究者和系统架构师而言，这些子模块之间的协同交互代表了一种针对学习环境的高度定制化对话式 AI 方案。

工程师们并未纯粹依赖现成的框架功能，而是构建了定制化的覆盖实现。例如，他们用自定义的三层上下文和会话存储来维护状态，而非使用原生 checkpointers；用抽取式句子级压缩算法来处理文本压缩，该算法能够尊重数学公式格式和代码块，而非使用通用的文本截断方法。以下章节将详尽阐述每个机制，展示从系统代码库中提取的实证数据、代码结构和架构算法。

## 1. LangGraph 原生功能与 Agent Graph 结构

### 1.1 未使用的 LangGraph 原生功能
LangGraph 提供了一套强大的原生状态管理和编排工具；然而，B5 架构有意绕过了其中几项，转而采用自定义实现。根据代码库配置，LangGraph 的初始化由 `LANGGRAPH_AVAILABLE` 标志控制，当该库不存在时实现优雅降级路径 [cite: 1]。

目前看来未被使用或被替代的主要原生功能包括：
* **原生线程 Checkpointers（检查点持久化器）**：LangGraph 提供了内置的 SQLite/Postgres checkpointers 用于线程级状态持久化。B5 系统并未使用这些功能，而是选择了自建的 `SessionStore` 和 `TemporalMemory` 系统（其架构的第三层）[cite: 1]。
* **原生多智能体 Supervisors（调度器）**：虽然 LangGraph 开箱即用地支持复杂的多智能体分层路由，但 B5 的实现依赖于通过环境变量和自定义工具执行器管理的手动阶段门控（Phase 1 至 Phase 4）[cite: 1]。
* **内置 Map-Reduce 集成**：图使用显式的"扇出"并行检索节点（例如 `retrieve_graphiti`、`retrieve_lancedb`），手动汇聚到 `fuse_results` 节点，而非严格依赖 LangGraph 的动态 `Send` API 进行任意 map-reduce [cite: 1]。

此外，Phase 2（工具调用）、Phase 3（Agent Graph）和 Phase 4（React Agent）受环境变量门控约束，根据运行时稳定性，有时会被禁用或降级为备用状态 [cite: 1]。

### 1.2 `agent_graph.py` 中的节点与边
系统定义了两个主要的图结构：基础 `agent_graph` 和 `canvas_agentic_rag` 图。标准的 `agent_graph.py` 建立了一个自适应与纠错检索增强生成（Adaptive and Corrective RAG）架构，从硬编码的管道导向转变为智能体引导的流程 [cite: 1]。

**表 1：标准 Agent Graph 中的节点**
| 节点标识符 | 功能描述 |
| :--- | :--- |
| `analyze_intent` | LLM 评估用户查询，决定是搜索知识库还是直接回答 [cite: 1]。 |
| `retrieve` | 如果意图判定有必要，则跨数据源执行搜索 [cite: 1]。 |
| `grade_documents` | 评估检索到的文档的相关性，丢弃匹配度低的结果 [cite: 1]。 |
| `rewrite_query` | 当初始检索失败时，修改原始查询以改善搜索结果 [cite: 1]。 |
| `generate_answer` | 基于充足的上下文，整合生成带引用的最终回复 [cite: 1]。 |

**标准 Agent Graph 的边：**
执行流程由条件路由控制：
1. `START` \(\rightarrow\) `analyze_intent` [cite: 1]。
2. `analyze_intent` \(\rightarrow\) `retrieve` 或 `generate_answer`（条件分支）[cite: 1]。
3. `retrieve` \(\rightarrow\) `grade_documents` [cite: 1]。
4. `grade_documents` \(\rightarrow\) `generate_answer` 或 `rewrite_query`（条件分支）[cite: 1]。
5. `rewrite_query` \(\rightarrow\) `analyze_intent`（回环，用于纠错 RAG）[cite: 1]。
6. `generate_answer` \(\rightarrow\) `END` [cite: 1]。

**Canvas Agentic RAG 扩展：**
扩展的图实现增加了并行检索能力，支持多查询扇出路由。它包含针对特定数据存储的独立节点：`retrieve_graphiti`、`retrieve_lancedb`、`retrieve_multimodal`、`retrieve_cross_canvas` 和 `retrieve_vault_notes` [cite: 1]。所有这些并行节点自动汇聚到 `fuse_results`，然后传递给 `rerank_results`。质量控制循环设有 `check_quality`，它根据条件路由到 `rewrite_query` 或 `compress_context`。最终质量关卡由 `faithfulness_check` 节点在到达 `END` 之前执行 [cite: 1]。

## 2. FSRS 调度与记忆衰减动态

### 2.1 集成 FSRS（Free Spaced Repetition Scheduler，自由间隔重复调度器）
B5 系统通过 `FSRSManager` 实现其架构记忆的第三层，集成了 FSRS-4.5 算法（`fsrs>=4.1.0`）来计算最优学习间隔 [cite: 1]。FSRS 以数学模型建模稳定性（stability）、难度（difficulty）、可检索性（retrievability）和遗忘次数（lapses）。该算法使用高度特定的数学权重来处理回忆后稳定性、稳定性下降因子和遗忘惩罚等操作 [cite: 1]。

当一个概念被学习时，`update_on_interaction` 函数将用户的表现评分（1-4）传递给 FSRS，FSRS 更新卡片的状态，返回稳定性和难度的新值 [cite: 1]。

### 2.2 处理长时间不活动（记忆衰减）
如果用户长时间未学习某个特定概念，FSRS 仍然能够通过量化记忆的衰退来安排复习。可检索性（回忆概率）是动态的，在查询时动态计算，而非静态存储。

如果存在正式的 FSRS 卡片对象，引擎会委托给 `self.fsrs_manager.get_retrievability(card)` [cite: 1]。然而，为了处理边缘情况——例如 FSRS 被禁用，或者概念有基本的交互日志但没有活跃的 FSRS 卡片数据——系统会回退到基于时间的指数衰减估算。

回退算法中使用的衰减公式基本由连续指数衰减定义，其中时间流逝决定了衰退程度：

\[ R = e^{-\frac{\Delta t}{\max(S, 1)}} \]

在系统的 Python 逻辑中，\(\Delta t\) 被定义为 `days_elapsed`，通过从当前 UTC 日期时间中减去 `last_interaction_ts` 来计算：
```python
days_elapsed = (datetime.now(timezone.utc) - concept.last_interaction_ts).total_seconds() / 86400
stability = max(concept.fsrs_stability, 1.0)
return math.exp(-days_elapsed / stability)
```
[cite: 1]。

如果用户从未与该概念交互过（`last_interaction_ts` 为 `None`），系统假设该概念是全新的，默认可检索性为 `1.0` [cite: 1]。一套单元测试验证了这一数学衰减，断言在稳定性为 2.0 的条件下经过三天后，可检索性精确等于 \( e^{-1.5} \) [cite: 1]。

## 3. 三层上下文窗口管理

上下文窗口架构解决了保留密集教育上下文与遵守 LLM token 限制（例如 Claude Code 的限制）之间的固有矛盾。系统正式规定了"Story 3.4 AC-2：三层管理（Tier 1 完整内容，Tier 2 摘要，Tier 3 按需获取）"[cite: 1]。

### 3.1 结构组成
上下文数据在每条用户消息时动态组装，以保证数据新鲜度并防止前端缓存问题 [cite: 1]。`ContextAssembler` 按结构划分数据：
* **Tier 1（核心上下文）：** 代表主要的完整上下文，包含节点名称、精通状态、FSRS 稳定性、学习提示和历史错误 [cite: 1]。
* **Tier 2（摘要上下文）：** 包含聚合的概念摘要，通常由边关系和一跳邻居摘要生成 [cite: 1]。
* **Tier 3（按需上下文）：** 设计用于在目标查询期间动态注入，当明确请求时解析更深层的边上下文。

### 3.2 Token 预算与比率分配
系统基于估算的 token 与字符转换比率，为上下文窗口分配严格的边界。对于混合 CJK（中日韩）和英文的环境，架构在保守的比率约束下运行 [cite: 1]。

**表 2：上下文预算分配**
| 参数 | 值约束 | 描述 |
| :--- | :--- | :--- |
| 最大总 Token 数 | 4,000 | 合并上下文注入的绝对 token 上限 [cite: 1]。 |
| 字符与 Token 比率 | 2:1 至 4:1 | 从每 token 2 个字符（中文为主）到每 token 4 个字符（混合内容为主）[cite: 1]。 |
| 最大上下文字符数 | 16,000 | 强制截断前的聚合字符串长度上限 [cite: 1]。 |
| Tier 1 比率上限 | 70%（`0.7`） | 溢出时分配给 Tier 1 的上下文预算最大百分比 [cite: 1]。 |

当 Tier 1 和 Tier 2 的组合文本超过 `MAX_CONTEXT_CHARS`（16,000 个字符）时，引擎会执行显式截断协议。它为 Tier 1 计算优先预算：`Math.floor(MAX_CONTEXT_CHARS * TIER1_RATIO)` [cite: 1]。Tier 1 保证最多 11,200 个字符，如果被截断则附加 `\n...(截断)`。剩余部分随后分配给 Tier 2。如果 Tier 1 吸收了全部预算（在 Tier 2 非常庞大的场景中），Tier 2 将被无情地截断到剩余配额 [cite: 1]。

## 4. 会话管理与恢复协议

每个节点的会话状态连续性对于跟踪教育对话至关重要。代码库根据环境使用双重会话存储机制——前端界面使用客户端方案，系统操作使用文件备份方案。

### 4.1 节点级会话实现
专用的 `SessionStore` 通过将唯一的 canvas `nodeId` 标识符映射到特定的 LLM 交互线程（`sessionId`）来管理活跃连接 [cite: 1]。
在 Web 环境中，这些数据通过浏览器 `localStorage` 以键名 `'canvas-learning:claude-sessions'` 持久化存储，跨页面刷新保持不变。`SessionStore` 在实例化时解析原始 JSON 映射。如果 JSON 损坏，它会优雅地清空映射并初始化新实例 [cite: 1]。

在后端或 CLI 环境中，会话同步被写入磁盘（例如通过 `mkdirSync` 和 `writeFileSync` 生成 JSON 文件），维护一个按节点 ID 映射的异步目录 [cite: 1]。每条会话记录跟踪 `sessionId`、`createdAt` 和 `lastActiveAt` 时间戳，以防止过时进程重叠 [cite: 1]。

### 4.2 恢复之前的会话
是的，用户可以恢复之前的会话。进程生命周期专门监听过去的会话标识符。如果用户触发了一个拥有预存映射的节点，引擎会调用由 `--resume` 标志的恢复协议 [cite: 1]。

此外，在结构化教学任务（如"验证会话"）期间，系统实现了健壮的暂停和恢复检查。会话状态字典通过 `VerificationStatus` 枚举维护一个显式的 `status` 参数。如果会话被标记为 `PAUSED`，它可以被恢复命令定向 [cite: 1]。恢复操作会累计暂停时长——确保分析指标保持准确——通过计算 `datetime.now()` 与 `progress.paused_at` 之间的差值 [cite: 1]。然后将会话状态更新回 `IN_PROGRESS`，并恢复缓冲区中去重的当前问题，或通过 RAG 动态生成新问题 [cite: 1]。

## 5. 上下文窗口压缩

上下文窗口压缩是缓解延迟和上下文膨胀的关键需求——这些是 Claude Code 等模型中突出的挑战。为解决这一问题，工程师们避免了非确定性的 LLM 摘要（会有幻觉和事实偏移的风险），转而设计了一个抽取式句子级压缩模块（Story 2.10）。

### 5.1 抽取式分割与原子块保护
核心原则是评估单个句子的相关性，只选择排名最高的句子，直到满足 token 预算（默认 3,000 tokens）[cite: 1]。
为防止高度技术性内容的结构损坏，系统识别"原子块"——绝对不能被句子分割器破碎的元素。使用多行正则表达式，引擎保护以下内容：
1. 围栏代码块：`r"(```[\s\S]*?```)"`
2. 块级数学公式：`r"(\$\$[\s\S]*?\$\$)"`
3. Markdown 表格：`r"((?:^[ \t]*\|.+\|[ \t]*$\n?){2,})"` [cite: 1]。

位于这些块之外的内容被标点符号标记（`。！？\.\!\?`）和换行符分割成评分单元 [cite: 1]。

### 5.2 相关性评分算法
每个生成的句子单元会获得一个相关性分数，以确定其保留优先级。系统采用了一种类似 TF-IDF 的启发式关键词重叠技术 [cite: 1]。
* **分词处理：** 为了准确处理多字符语义，引擎优先使用 `jieba` 库进行中文分词。如果不可用，则降级为标准正则表达式 `\w+` 匹配 [cite: 1]。
* **评分逻辑：** 基础相关性是查询词在该单元中出现的比例。系统对精确短语重叠添加子串奖励（每个匹配 0.1 分）[cite: 1]。
* **陈旧惩罚：** 如果上层文档元数据将文本标记为陈旧，其句子相关性分数会被大幅减半（`relevance *= 0.5`）[cite: 1]。
* **原子块奖励：** 受保护的块（数学公式、代码）自动获得最低相关性阈值 `0.3`，以高度偏向在最终输出中保留这些内容 [cite: 1]。

引擎按相关性降序排列这些片段。它依次添加单元，直到再添加一个就会超过 3,000 token 预算为止。最后，选中的子集按其原始索引 `(doc_idx, unit_idx)` 顺序排列，以恢复时间顺序和逻辑流 [cite: 1]。

## 6. 对话归档（Hot-Warm-Cold 生命周期）

大量的对话记忆会急剧增加 LLM 推理成本并降低逻辑连贯性。为应对这一问题，架构通过 `ArchiveManager`（Story 3.8）实现了严格的 Hot-Warm-Cold 三层对话归档系统 [cite: 1]。

### 6.1 生命周期阈值与双触发器
对话片段在各层之间的转换由双触发器控制：经过的时间或纯粹的 token 容量阈值。消息不会被物理删除，而是被安全地标记为 `status: archived` 并转移到对应的存储层 [cite: 1]。

**表 3：对话归档层级**
| 层级 | 触发条件 | 数据保留策略 |
| :--- | :--- | :--- |
| **Hot（热）** | 存在时间 \( \le 30 \) 天。Token 容量 \( \le 50,000 \)。 | 完整的原始消息保留。所有上下文细节均被保存 [cite: 1]。 |
| **Warm（温）** | 存在时间 > 30 天 或 节点容量 > 50,000 tokens。 | 原始文本被抑制。替换为 LLM 生成的对话摘要 + 结构化提取点 [cite: 1]。 |
| **Cold（冷）** | 存在时间 > 180 天（6 个月）。 | 对话摘要被清除。仅保留刚性结构化数据（提示、错误、问答亮点）[cite: 1]。 |

### 6.2 精炼与转换机制
当对话突破 Warm 阈值时，`ArchiveManager` 通过 `conversation_distiller.py` 调用精炼流程。系统异步压缩原始历史记录，提取由 `summary`（摘要）、`tips`（提示）、`errors`（错误）和 `qa_highlights`（问答亮点）组成的可操作元数据 [cite: 1]。这些结构化要点在特定的 group ID 下安全地映射回 Neo4j/Graphiti 知识图谱。

如果一个休眠节点由于六个月的完全不活动而直接从 Hot 层跳转到 Cold 层，系统会智能地先运行 Warm 层精炼协议。它保证在原始上下文被完全截断之前，结构化数据已经存在，从而保护用户初次交互期间产生的事实发现 [cite: 1]。跟踪实体 `ArchiveStatus` 持久化记录当前层级、总消息数、估算 token 数和操作时间戳，以确保系统协调并防止服务器重启时出现重复归档循环 [cite: 1]。

---
*结论：* B5 对话管理系统展示了与标准 LangGraph 模板高度差异化的专业架构。通过使用 FSRS 实现时间衰减、在摘要过程中以数学方式隔离上下文块、通过层级预算确定记忆优先级、以及基于 Hot-Warm-Cold 阈值矩阵积极归档，该平台确保了快速、高度连贯的 Agentic AI 对话，同时避免了无界上下文退化的问题。

**参考来源：**
1. docs/PRD-v3-execution-checklist.md (fileSearchStores/persistentcanvaslearningsys-qa7kqspeo0jc)
