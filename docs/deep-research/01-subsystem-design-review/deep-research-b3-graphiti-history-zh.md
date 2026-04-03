# B3 Graphiti 学习历史系统架构设计：Schema（模式）、Retrieval（检索）与 Agentic Integration（智能体集成）

**执行摘要与核心发现**
*   **Schema（模式）与 Storage（存储）：** 系统通过统一的实体命名规范对学习历史进行建模，将知识分为概念型和程序型两类，同时通过专用的 Pydantic 模式区分 `Misconception`（误解）和 `LearningTip`（学习提示）等特定事件。证据表明，Neo4j 的关系（relationships）被大量用于将概念与对应的错误和标注进行关联。
*   **Retrieval Mechanisms（检索机制）：** 系统依赖 Assessment Context Package（评估上下文包，简称 ACP）来聚合学生数据。该包动态拉取 4 类错误历史、边推理（edge reasoning）和精通度状态，在出题前提供学习者的全面画像。
*   **Prompt Design（提示词设计）：** 研究表明系统采用了受 Bloom's Taxonomy（布鲁姆认知分类法）启发的精密 5 层提示词架构。它将特定错误类型映射到针对性的补救策略，将学生从 Graphiti 检索到的历史动态注入提示词，同时采用严格的安全边界防御注入攻击。
*   **Noise（噪声）与 Decay（衰减）管理：** 随着知识图谱的扩展，系统通过分类 `group_id` 命名空间隔离、token 上下文预算，以及基于 FSRS-4.5 算法的双时间维度衰减模型来缓解噪声，该模型可计算知识随时间的可检索度。
*   **K-RAG 实现：** 证据倾向于表明这是一个部分实现的 Knowledge-Enhanced RAG（知识增强检索增强生成）系统。它具备多源检索（LanceDB 和 Graphiti）及降级回退机制，但其在 LangGraph 框架中的完整集成仍在推进中。
*   **Worker 状态与技术债务：** 虽然 `GraphitiEpisodeWorker` 设计了健壮的队列和死信存储机制，但内部诊断揭示了严重的技术债务。很可能许多标记为 "Graphiti" 的函数实际上在执行原始 Neo4j Cypher 查询，绕过了官方 SDK。一项重大重构工作（Epic 3）已计划用于解决这一假象。

**Graphiti 记忆系统通俗介绍**
想象一个高度智能的文件柜，它不仅能存储你的学习笔记，还能记住你*如何*在学习中挣扎、*何时*犯了错误，以及*为什么*两个概念在你脑中是相关的。这就是 B3 Graphiti 学习历史系统的目标。它不把学习当作一串扁平的考试分数，而是构建一个"知识图谱"——一张由你个人学习旅程串联起来的概念网络。

如果你误解了一个数学公式，系统会记录下这个特定的 "Misconception"（误解）并将其与该公式关联。当考试来临时，AI 导师会检索这张记忆之网，回顾你过去的错误，并专门定制一道全新的题目，旨在测试你是否已经克服了那个确切的障碍。为了防止系统被过多陈旧、无关的笔记所淹没，它使用了一种"遗忘曲线"算法，温和地淡化较旧的记忆，除非它们被证明具有高度重要性。虽然理论设计异常先进，但系统目前正在大量施工中，致力于将其宏伟蓝图与稳定的、可在真实环境运行的代码对接。

***

## 1. Graphiti/Neo4j 中的实体与关系模式

B3 学习架构的基础是其知识图谱，它作为高度结构化的仓库，用于跟踪学生进度、捕获细微的学习行为，并在不同学习会话之间维持历史上下文。存储范式使用 Neo4j 作为底层图数据库，通过直接 Cypher 查询和 Graphiti 知识图谱中间件的混合集成进行管理 [cite: 1]。

### 1.1 统一实体命名与事件类型

为了在知识图谱中保持一致性，系统对节点执行严格的统一实体命名规范。根据 `GraphitiEpisodePayload` 模式，实体名称格式被构造为 `"{KnowledgeType}:{EventType}:{concept_name}"` [cite: 1]。

这确保了节点可以通过 Graphiti 的 `search_nodes` 函数轻松检索，而不需要严格依赖内部 UUID。例如，如果一个学生在逆否命题这一逻辑概念上遇到困难，生成的实体名称将是 `"conceptual:misconception:逆否命题"` [cite: 1]。

一个学习事件的数据载荷包含以下关键字段 [cite: 1]：
*   **`schema_version`**：用于向后兼容的版本号。
*   **`event_type`**：具体的触发事件（例如：检测到误解）。
*   **`knowledge_type`**：分类为 `CONCEPTUAL`（概念型）或 `PROCEDURAL`（程序型）。
*   **`severity`**：一个表示事件严重程度的浮点数。
*   **`tags`**：元数据字符串列表（例如：`["needs_review"]`）。
*   **`content`**：事件的原始文本或转录内容。
*   **`node_id`**：链接回原始 Canvas 节点的 UUID。

### 1.2 提示、错误与困惑点的存储

系统明确定义了不同类型学习反馈的模式，特别是 `LearningTip`（学习提示）和 `Misconception`（误解）。它们被实现为 Pydantic 模型，最终被序列化为 Graphiti 实体。

#### 4 类错误分类
模式中的一个核心创新是 `ErrorType` 枚举，它将对话中的错误和困惑点分为四种不同的认知失败类型。该框架直接指导下游的补救措施 [cite: 1]：

| 错误类型键值 | 中文标签 | 描述/症状 |
| :--- | :--- | :--- |
| `PROBLEM_FRAMING` | 破题错误 | 阅读理解错误；遗漏条件；审题失败。 |
| `REASONING_FALLACY` | 推理谬误 | 逻辑跳跃；因果倒置；解题过程中的不当归纳。 |
| `KNOWLEDGE_GAP` | 知识点缺失 | 缺乏先修知识；基础定义未被理解。 |
| `SUPERFICIAL` | 似懂非懂 | 表面层次的理解；学生能背诵事实但在应用时失败。 |

较旧的遗留实体类型通过 `ENTITY_TYPE_TO_UNIFIED` 字典映射到这个新的统一模型。例如，旧的 `ProblemTrap` 被映射为 `PROCEDURAL`（程序型）知识，事件类型为 `PROBLEM_TRAP_DETECTED`，默认严重度为 0.7 [cite: 1]。

### 1.3 Neo4j 节点与边的模式

虽然 Graphiti 对部分图的复杂性进行了抽象，但底层的 Neo4j 模式针对学习场景进行了大量定制。

**节点：**
*   **`CanvasNode`** / **`LearningNode`**：表示用户学习白板（Canvas）中的特定概念或文档。包含 `canvas_path`、`node_id` 和文本内容等属性 [cite: 1]。
*   **`EpisodicNode`**：Graphiti 用于按时间顺序存储事件的主要存储机制。`source_description` 属性用于区分事件类型，例如 `'error_record'` 或 `'conversation_archive'` [cite: 1]。
*   **`EntityNode`**：带有 `["Concept"]` 标签的提取概念，通过 `group_id` 参数（如 `"canvas_concepts"`）对相关概念进行分组 [cite: 1]。

**关系（边）：**
Neo4j 中的边表示概念之间的推理和历史关联。
*   **Canvas 关联**：当两个 Canvas 节点之间检测到关系时，会创建一条边。边标签被规范化（大写加下划线，例如 `CONNECTED_TO` 或 `PREREQUISITE`）[cite: 1]。
*   **边推理（`rationale`）**：一个关键特性是存储边*为何*存在的原因。系统将其存储在关系的 `rationale` 属性中（例如 `(n:CanvasNode)-[r]->(m:CanvasNode)` 其中 `r.rationale` 被填充）[cite: 1]。
*   **反馈边**：实体通过 `HAS_TIP`（将 `ConceptNode` 链接到 `LearningTip`）和 `HAS_MISCONCEPTION`（将 `ConceptNode` 链接到 `Misconception`）等模式进行关联 [cite: 1]。

***

## 2. 个人学习历史的检索

为了生成高度个性化的考试题目，系统必须检索学生独特的学习历史。这通过 **Assessment Context Package（评估上下文包，简称 ACP）** 管道实现，主要由 `assemble_acp` 工具函数调用 [cite: 1]。

### 2.1 Assessment Context Package（ACP）组装

`assemble_acp` 方法作为编排器，从多个微服务拉取多模态数据，构建一个完整的上下文对象（`ACPData`）。该对象的 token 预算被严格限制在 3,000 tokens [cite: 1]。

检索遵循一个有序的流程：
1.  **节点内容分类**：获取目标节点的文本，并将其分类为陈述性知识（`k_signals`）或程序性知识（`p_signals`），以确定 `node_type` [cite: 1]。
2.  **精通度状态提取**：系统查询精通度引擎（依赖 FSRS），获取 `p_mastery`（精通度概率）、`retrievability`（可检索度）、`effective_proficiency`（有效熟练度）以及人类可读的 `mastery_label`（例如 "Not Assessed"，即"未评估"）等指标 [cite: 1]。
3.  **提示检索**：`_get_tips` 函数在 Graphiti 记忆中搜索学生所做的自定义标注 [cite: 1]。
4.  **错误历史检索**：系统在 Graphiti 中查询学生在该特定节点上的过往错误 [cite: 1]。
5.  **边推理**：`_get_edge_reasons` 函数拉取与目标节点相连的关系中的 `rationale` 字符串 [cite: 1]。
6.  **对话摘要**：拉取关于该主题的 AI-学生过往对话的 Tier 2（二级）摘要 [cite: 1]。

### 2.2 基于 Cypher 的图检索

尽管理论上使用 Graphiti SDK，但源代码揭示检索实际上严重依赖通过 `Neo4jClient` 执行的直接 Neo4j Cypher 查询。

例如，要检索 4 类错误历史，系统运行以下查询 [cite: 1]：
```cypher
MATCH (e:EpisodicNode)
WHERE e.source_description = 'error_record'
  AND e.node_id = $node_id
RETURN e.error_type AS error_type, e.description AS description
ORDER BY e.created_at DESC
LIMIT 4
```
这直接获取与该节点关联的四条最近错误，将它们映射回 ACP 所需的 `error_type` 和 `description` 字典 [cite: 1]。

类似地，要检索边推理（困惑点或逻辑关联），系统查询 Canvas 节点之间的关系 [cite: 1]：
```cypher
MATCH (n:CanvasNode {uuid: $node_id})-[r]->(m:CanvasNode)
WHERE r.rationale IS NOT NULL
RETURN r.rationale AS rationale
LIMIT 5
```

### 2.3 目标节点的优先级评分

在选择测试哪个节点时，系统不会随机选取。它使用一个数学优先级函数 [cite: 1]：
\[ \text{Priority} = (W_{MASTERY} \times (1.0 - p_{mastery})) + (W_{RETRIEVABILITY} \times (1.0 - \text{retrievability})) + (W_{KG\_RELEVANCE} \times kg_{relevance}) \]
如果一个节点已经被考核过，其优先级分数会被惩罚（乘以 0.3），以确保出题过程中的新颖性 [cite: 1]。

***

## 3. 提示词设计与 ACP 数据注入

一旦个人学习历史被聚合到 `ACPData` 对象中，它必须被安全且有效地注入到 Large Language Model（大语言模型，简称 LLM）中用于出题。系统采用了受 Bloom's Taxonomy PS4 策略（arXiv:2408.04394）启发的高度结构化的 5 层提示词设计 [cite: 1]。

### 3.1 5 层提示词架构

`build_5_layer_prompt` 函数通过以下隔离的层次构建提示词 [cite: 1]：
1.  **第 1 层（静态）**：定义 AI 的角色人设和考官身份。
2.  **第 2 层（用户选择）**：注入特定的考试模式参数。
3.  **第 3 层（动态）**：ACP 学生数据载荷（学习历史、精通度水平）。
4.  **第 4 层（静态/动态）**：核心出题规则，由计算得出的**补救策略**进行大幅修改。
5.  **第 5 层（静态）**：输出格式化指令（强制严格 JSON 输出）。

### 3.2 动态补救策略

提示词设计之所以强大且独特，在于第 4 层会根据学生 ACP 数据中发现的主导错误类型动态调整。`_determine_remediation_strategy` 函数分析 `error_history` 字典，识别最频繁的错误，并选择一个针对性的提示词注入 [cite: 1]。

注入提示词的策略定义如下 [cite: 1]：

*   **针对 `PROBLEM_FRAMING`（破题错误）**：
    *"【补救策略：破题错误】 该学生存在破题错误——能记住解法但无法灵活应用。请出「同结构不同包装」的新题，验证破题能力而非记忆。例如：更换题目的表面情境但保持底层数学/逻辑结构不变。"*
*   **针对 `REASONING_FALLACY`（推理谬误）**：
    *"【补救策略：推理谬误】... 请采用以下策略之一：1. 给出一段包含错误推理的过程，让学生找出错误并修正；2. 出反例题，要求学生判断某个看似正确的推理为何是错的。"*
*   **针对 `KNOWLEDGE_GAP`（知识点缺失）**：
    *"【补救策略：知识点缺失】... 请回退到定义级别的基础题，确认学生理解核心定义后再逐步升级难度。"*
*   **针对 `SUPERFICIAL`（似懂非懂）**：
    *"【补救策略：似懂非懂】... 请采用以下策略之一：1. 辨析题... 2. 反例题... 3. 迁移题..."*

### 3.3 Token 预算与优雅降级

由于 LLM 的上下文窗口是有限且昂贵的，`_enforce_token_budget` 方法作为一个严格的保障机制。系统计算节点内容、对话摘要、提示、错误和边推理的总字符数 [cite: 1]。

如果合计大小超过 `ACP_MAX_CHARS` 限制，将通过优先队列进行截断：对话摘要首先被截断（至 500 字符），然后是节点内容（至 800 字符），同时确保数学公式（`$...$`）和代码块不会在 token 中间被截断 [cite: 1]。

如果第 3 层的外部模板文件加载失败，系统会依赖程序化回退（优雅降级），手动拼接 `node_content`、`node_type`、`effective_proficiency`，以及动态追加的 `optional_sections`（提示、错误、边推理）[cite: 1]。

### 3.4 安全性与注入防御

将用户生成的内容（如 Canvas 笔记和聊天历史）直接注入提示词存在严重的 prompt injection（提示词注入）漏洞。为了应对这一风险，`PromptTemplate` 类使用 `SYSTEM_BOUNDARY_MARKER` 强制实施结构隔离 [cite: 1]。

此外，系统实现了一套详尽的基于正则表达式的防火墙，用于检测和中和历史数据载荷中的对抗性数据 [cite: 1]。被检测的模式包括：
*   **直接注入**：`ignore\s+(all\s+)?previous\s+instructions`、`you\s+are\s+now\s+a`。
*   **中文注入**：`(请|你)?忽略(之前|以前|上面)(的)?(所有)?指令`。
*   **分隔符伪造**：`<\|system\|>`、`<\|assistant\|>`、`\[SYSTEM\s+OVERRIDE\]`。
*   **间接操纵**：`(this\s+)?(node|content|note).*?should\s+be\s+treated\s+as\s+(system\s+)?instructions?`。

***

## 4. 噪声处理与相关性衰减

随着用户使用考试白板的增加，知识图谱不可避免地会积累数千个节点、事件和边。如果不加以控制，这种"图膨胀"将导致灾难性的检索噪声和 LLM 幻觉（hallucination）。B3 架构通过三种不同的范式来缓解这一问题：Temporal FSRS decay（时间维度 FSRS 衰减）、Categorical Namespacing（分类命名空间）和 Context Budgeting（上下文预算）。

### 4.1 时间维度记忆与 FSRS-4.5 算法

系统不会平等对待所有记忆；它采用了一个由 Free Spaced Repetition Scheduler（自由间隔重复调度器，FSRS v4.5）支撑的双时间维度建模引擎 [cite: 1]。这作为记忆系统的"第 3 层"，通过异步 SQLite 持久化（`aiosqlite`）进行跟踪，并与 Graphiti 图同步 [cite: 1]。

核心衰减机制基于以下公式计算知识保留分数 [cite: 1]：
\[ R(t) = \left(1 + \frac{t}{S}\right)^{-\frac{1}{\text{decay}}} \]
其中 \( S \) 表示有效稳定度（effective stability）。系统使用多个权重修改基础初始稳定度 [cite: 1]：
*   **难度修正因子（Difficulty Modifier）**：`1 + difficultyWeight * (conceptDifficulty - 0.5)`
*   **参与度加成（Engagement Bonus）**：`1 + 0.1 * docEngagement`
*   **先修知识就绪度加成（Prerequisite Bonus）**：`1 + 0.1 * prerequisiteReadiness`

在检索节点时，会评估一个名为 `fsrs_retrievability` 的信号（权重为 0.25）[cite: 1]。如果一个概念的可检索度低于 `shaky_threshold`（0.40），它会被标记为薄弱概念，并被优先用于检索和考核 [cite: 1]。

### 4.2 分类命名空间与 `group_id`

早期迭代中检索噪声的一个主要根本原因是使用了单体式的 Graphiti `group_id`。当所有决策和事件都被塞进一个单一的组中时，检索精度会崩溃 [cite: 1]。

参照社区共识和类似 "GuardKit" 的架构，系统已过渡到按分类和按功能的命名空间。`group_id` 参数作为多租户和图隔离的屏障 [cite: 1]。例如：
*   `{project_id}__feature_specs`：严格隔离到特定科目或功能的上下文。
*   `role_constraints`：不含动态噪声的系统级约束 [cite: 1]。

在 RAG 检索过程中，搜索本质上是有范围限定的。例如，`retrieve_graphiti` 函数在查询图之前，会尝试使用 `scoped_canvas = build_group_id(subject, canvas_file)` 来隔离搜索范围 [cite: 1]。

### 4.3 上下文预算与多信号相关性调优

即使使用了范围限定查询，检索仍可能返回过多匹配结果。系统通过"上下文预算"模式（FEAT-GR-006）来解决这一问题 [cite: 1]。检索器不是拉取一个扁平的 top-K 向量列表，而是为各类别分配严格的百分比限制。

对于 5,000 token 的预算，检索器可能会如此分配 [cite: 1]：
*   `feature_context`（功能上下文）：30%（1,500 tokens）
*   `architecture_context`（架构上下文）：20%（1,000 tokens）
*   `similar_outcomes` / `warnings`（相似结果/警告）：30%（1,500 tokens）
*   `domain_knowledge`（领域知识）：20%（1,000 tokens）

如果检索到的警告超过 1,500 tokens，得分最低的节点会被积极截断。评分是多信号的，将向量相似度与写入时应用的"重要性评分"（0.0 到 1.0）相结合，确保关键的历史修正记录（例如，权重为 0.9）能够轻松超过较旧的、无关紧要的交互 [cite: 1]。Graphiti 的双时间维度跟踪还确保了自动失效；如果一条新事实与旧事实矛盾，系统会在旧边上标记 `t_invalid` 时间戳，允许 Cypher 查询过滤掉 `DEPRECATED`（已弃用）节点 [cite: 1]。

***

## 5. K-RAG（知识增强 RAG）的实现状态

K-RAG（Knowledge-Enhanced Retrieval-Augmented Generation，知识增强检索增强生成），这一架构概念此前在 Gemini 研究和 Agentic RAG 成熟度模型中被重点提出，已在系统中积极实现，尽管设计了"优雅降级"路径。

### 5.1 多源扇出检索

该实现通过 LangGraph（Phase 2）桥接，不仅仅依赖单一的向量数据库 [cite: 1]。`RAGService` 协调对多个数据存储的并行、并发查询：
1.  **LanceDB 节点（`retrieve_lancedb`）**：对 Markdown 讲解文档执行 L2 距离语义搜索。距离通过 `1 / (1 + distance)` 反转为分数 [cite: 1]。性能约束要求 P95 延迟 < 400ms [cite: 1]。
2.  **Graphiti 节点（`retrieve_graphiti`）**：连接到 Graphiti 中间件，拉取结构化数据（节点、边和事件），将有效负载规范化为具有严格模式匹配的统一格式 [cite: 1]。

### 5.2 融合策略与超时容忍

由于多个不同的搜索空间返回结果，系统具有一个聚合数据的 Fusion Node（融合节点）。API 端点接受不同的融合配置：`rrf`（Reciprocal Rank Fusion，互惠排名融合）、`weighted`（加权）或 `cascade`（级联）[cite: 1]。对于"检验白板"的特定用例，`weighted` 策略被定义为默认策略 [cite: 1]。

为了满足实时 AI 智能体的高速要求，K-RAG 实现被超时机制严格门控。`get_rag_context_with_timeout` 函数施加了 `RAG_TIMEOUT_SECONDS = 2.0` 的硬限制 [cite: 1]。

如果 `RAGService` 导入失败、崩溃或 2 秒超时被突破，系统会执行 AC5 优雅降级协议。它记录一条警告（`"RAG query timeout (2.0s), continuing without RAG context"`，即"RAG 查询超时（2.0 秒），继续执行但不注入 RAG 上下文"），并在不注入扩展知识上下文的情况下继续运行，确保核心智能体循环不被阻塞 [cite: 1]。

成功通过融合层的结果会被格式化为独立的引用（例如 `lecture 3.md:29-65 (## A* 搜索) [02:27-04:48]`），然后追加到智能体的提示词上下文中 [cite: 1]。

***

## 6. GraphitiEpisodeWorker 的运行状态

问题 7 询问 `GraphitiEpisodeWorker` 是否真正在工作。研究数据给出了一个细致的回答：Worker 基础设施在队列层面是高度健壮且可运行的，但它存在严重的底层"技术债务"——它与 Graphiti Core SDK 的实际连接要么被绕过，要么通过原始 Cypher 模拟。

### 6.1 Worker 架构与韧性

`GraphitiEpisodeWorker` 被设计为一个异步的、基于队列的后台工作进程（`asyncio.Queue`），旨在序列化对知识图谱的写入 [cite: 1]。
根据代码库，Worker 接收一个包含 `name`、`episode_body` 和 `group_id` 的 `EpisodeTask` [cite: 1]。

为处理瞬态故障（例如 Neo4j 连接中断），Worker 实现了：
*   **带完全抖动的指数退避（Exponential Backoff with Full Jitter）**：等待时间计算为 \( \min(2^{\text{retry\_count}}, 60) \) 乘以一个随机抖动因子 [cite: 1]。
*   **死信存储（Dead-Letter Store）**：如果一个 episode 超出其 `max_retries`（默认为 3）失败，或者队列正在关闭，该任务会被追加到本地 JSONL 文件（`data/dead_letter_episodes.jsonl`）中并附带完整的追踪信息，以便后续手动重放 [cite: 1]。

在 FastAPI 应用生命周期中，Worker 通过 `initialize_graphiti`（实例化 Gemini Embedder 和 LLM 模型）进行初始化，并通过 `await worker.stop(timeout=30.0)` 进行优雅关闭 [cite: 1]。

### 6.2 "假命名"技术债务（Epic 3）

尽管外壳如此健壮，"Graphiti"事件的内部执行目前是一个在开发冲刺中被标记的关键已知问题。

一份根因分析报告明确识别了系统中 **42 处"假命名"** [cite: 1]。具体来说，核心客户端文件 `backend/app/clients/graphiti_client.py` 有 **零个 `graphiti-core` SDK 调用** [cite: 1]。报告指出：*"30+函数名含graphiti全是Neo4j Cypher. 根因: AI混淆写入Neo4j不等于写入Graphiti."*（30+个函数名包含"graphiti"的函数全部是 Neo4j Cypher。根因：AI 将写入 Neo4j 与写入 Graphiti 混为一谈）[cite: 1]。

为解决这一假象，"Epic 3: Graphiti 真实集成"已被规划 [cite: 1]。其目标包括：
*   **S-7**：将具有误导性的 `graphiti_client.py` 重命名为 `neo4j_learning_client.py`，或正确实现 SDK [cite: 1]。
*   **S-8**：确保 `episode_worker.py` 成为 Graphiti 写入的*唯一*授权路径，防止其他微服务执行绕过图的索引和时间引擎的原始 Cypher 插入 [cite: 1]。

因此，虽然 Worker *进程*运行成功，但其当前的数据插入方法严重依赖遗留的 Neo4j 逻辑，需要立即进行重构以发挥 Graphiti 中间件的全部潜力。

***

## 结论

B3 Graphiti 学习历史系统代表了语义知识图谱、双时间维度 FSRS 衰减算法和动态提示词工程的雄心勃勃的融合。通过将错误和提示构建为严格的 4 类分类体系，并通过 3,000 token 的 ACP 管道进行检索，该系统使大语言模型能够充当高度上下文感知的导师。虽然时间维度跟踪成功地管理了相关性衰减并缓解了上下文膨胀，但 `GraphitiEpisodeWorker` 的架构实现仍然是一项进行中的工作，目前严重依赖直接的 Neo4j Cypher 回退来弥合设计与生产之间的差距。

**来源：**
1. backend/app/clients/neo4j_learning_base.py (fileSearchStores/persistentcanvaslearningsys-qa7kqspeo0jc)
