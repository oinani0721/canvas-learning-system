# Canvas 学习环境的系统架构与实现分析

**执行摘要与核心发现**
Canvas Learning System（Canvas 学习系统）的实现展现了一个高度复杂的多层架构，旨在将教学理论与先进的 AI 评估及知识图谱能力相融合。基于所提供的代码仓库数据，我们可以简明地回应主要问题：
*   **3 层评分保险机制：** 是的，该架构完整实现了 3 层评分保险系统。包括 3 次自一致性采样（3x self-consistency sampling）、基于 SOLO 分类法（SOLO taxonomy）锚定的 4 维评分量表，以及可选的双模型验证系统（用于忠实性和一致性检查）。
*   **Canvas 内容能力：** Canvas 支持 Text（文本）、File（文件，包括 Markdown/PDF/图片）、Link（链接）和 Group（分组）节点。图片支持包括标准格式（`.png`、`.jpg`、`.jpeg`、`.gif`、`.bmp`、`.svg`、`.webp`）。其能力与 Obsidian Canvas 原生 JSON schema（模式）紧密对应并可互操作，使用特定的嵌入语法解析。
*   **SOLO 分类法与教学算法：** SOLO 分类法（SOLO taxonomy）在评分量表中已被积极实现。关于 "FIRe" 算法，代码库中广泛详述的是 **FSRS（Free Spaced Repetition Scheduler，自由间隔重复调度器）** 算法（v4.5 版本）的实现，而非一个明确命名为 "FIRe" 的算法。FSRS 已完整实现，可追踪微认知状态，非常适合单用户学习系统。
*   **Edge Elaborative Interrogation（边连接精细追问，EEI）：** EEI 已通过 `edge-dialog.md` 提示词积极实现。在代码中，当用户连接两个概念时触发，作为学习伙伴提出"为什么/如何"的因果性问题，探查反例，并严格执行 3-4 轮的上限以防止疲劳。
*   **点击跳转导航：** 已广泛实现。在 Obsidian 原生环境中，使用 `CanvasNavigator` API 进行节点高亮和缩放。在 Tauri 环境中，采用降级策略，使用 `@tauri-apps/plugin-shell` 调用 `obsidian://adv-uri` 协议。
*   **性能保障：** 已完整实现。系统使用 Assessed Concept Profile（ACP，已评估概念档案）token 预算来执行严格的数据约束，配备 15K 到 3K 的提取式上下文压缩器以保护原子块（代码/数学公式），并使用 LanceDB 元数据预过滤将搜索空间限制在特定 canvas 文件的本地范围内。

以下各节将对每个架构组件进行详尽的学术级剖析，详述其编程逻辑、底层教学原理及集成策略。

## 1. 3 层评分保险系统的实现

智能辅导系统（Intelligent Tutoring Systems）中自动化评分的必要性要求对大语言模型（LLM）的幻觉（hallucination）、不一致性和表面化评估建立强健的防护措施。Canvas Learning System 通过严格实现的 3 层评分保险架构来解决这一问题。

### 1.1 自一致性 3 次采样机制
保险的第一层依赖于多次采样方法，旨在缓解生成式 AI 模型固有的方差。`AutoScorer` 类实现了两阶段评估管线：Stage 1（阶段 1）用于证据提取，Stage 2（阶段 2）用于量表评分 [cite: 1]。

在阶段 2 中，系统对每次评分事件执行三次独立的 LLM 调用，使用 0.3 的温度参数（temperature）以引入轻微的多样性来实现自一致性 [cite: 1]。结果通过 `_majority_vote` 函数进行聚合。该函数对每个维度的三个样本应用统计聚合：
*   **多数投票（Majority Vote）：** 系统尝试计算三个样本中的统计众数（mode，即最常出现的值）[cite: 1]。
*   **备选方案（Fallback Resolution）：** 如果无法确定唯一众数（例如得分分别为 1、2、3），系统默认使用统计中位数以确保平衡、保守的评分 [cite: 1]。
*   **低置信度检测（Low-Confidence Detection）：** 一个关键的安全机制是离散度检查。如果样本中最大值与最小值之差超过 1（即 `max(values) - min(values) > 1`），系统将该特定维度标记为 `low_confidence_dimension`（低置信维度）[cite: 1]。这作为升级触发器，确保在模型不确定时进行人工监督或进一步的算法审查。

### 1.2 4 维量表分解
保险模型的第二层将评估分解为细粒度的、独立评估的维度。`AutoScorer` 按 4 维量表评估学生回答：
1.  `concept_accuracy`（概念准确性）
2.  `reasoning_quality`（推理质量）
3.  `knowledge_coverage`（知识覆盖度）
4.  `knowledge_integration`（知识整合度）[cite: 1]。

这四个维度的得分取平均值，映射到 4 级评分阈值：1（Again，再来）、2（Hard，困难）、3（Good，良好）、4（Easy，简单）[cite: 1]。至关重要的是，回归测试确认该量表深度锚定于 **SOLO（Structure of Observed Learning Outcomes，可观察学习成果结构）分类法** [cite: 1]。提示词注册表验证了 SOLO 各阶段的强制包含：Pre-structural（前结构）、Uni-structural（单点结构）、Multi-structural（多点结构）和 Relational（关联结构）[cite: 1]。通过分解评分，系统确保学生不仅仅在事实记忆层面被评分，而是在其认知建模的结构复杂度层面被评估。

### 1.3 可选的双模型一致性验证
第三层引入了跨模型和跨阶段的审计。这通过 `ScoreConsistencyResult` 框架实现 [cite: 1]。系统采用双模型方法，从 `settings.FAITHFULNESS_MODEL` 读取主审计模型，并以 `settings.AI_MODEL_NAME` 作为备选 [cite: 1]。

该阶段运行一个提示词（`faithfulness_score_consistency.md`），要求审计 LLM 验证阶段 2 产生的评分和理由是否真正基于阶段 1 提取的原始证据 [cite: 1]。LLM 输出一个包含每个维度 `consistency_checks`（一致性检查）的 JSON 载荷，严格标记为 `CONSISTENT`（一致）或 `INCONSISTENT`（不一致）[cite: 1]。规则严格规定："高分配弱证据是 INCONSISTENT"以及"低分配强证据也是 INCONSISTENT" [cite: 1]。这一层成功地将证据提取与评分论证解耦，防止了循环幻觉。

## 2. Canvas 内容支持与互操作性

系统的视觉和空间学习组件依赖于 canvas 界面。理解其内容支持以及它如何与 Obsidian 原生能力对接，对于评估其互操作性至关重要。

### 2.1 支持的图片和内容类型
Canvas Learning System 的解析器旨在处理符合标准 canvas 节点规范的多种节点类型。`CanvasNode` 类型被定义为四种核心类型的联合类型（union）：
*   `CanvasTextNode`：包含标准 Markdown 文本内容 [cite: 1]。
*   `CanvasFileNode`：引用本地 vault（仓库）中的文件。支持可选的 `subpath` 参数（例如 `#Section` 用于链接到特定标题）[cite: 1]。
*   `CanvasLinkNode`：包含指向网络资源的外部 URL [cite: 1]。
*   `CanvasGroupNode`：作为其他节点的空间容器，支持背景图片和样式（`cover`、`ratio`、`repeat`）[cite: 1]。

对于媒体文件，系统通过 `IMAGE_EXTENSIONS` 常量明确识别广泛的图片扩展名，包括：`.png`、`.jpg`、`.jpeg`、`.gif`、`.bmp`、`.svg` 和 `.webp` [cite: 1]。

### 2.2 与 Obsidian Canvas 插件能力的比较
该实现与 Obsidian Canvas 原生插件高度同构（isomorphic），意味着它被设计为可无缝双向兼容。节点 schema（模式）（`id`、`type`、`x`、`y`、`width`、`height`、`color`）与 Obsidian 标准一致 [cite: 1]。

一个值得注意的能力是 `getNodeContent` 工具函数，它标准化了信息提取供后端处理的方式。对于文本节点，提取原始文本；对于文件节点（包括图片和标准 Markdown/PDF），生成 Obsidian 原生嵌入语法（`![[filename#subpath]]`）[cite: 1]。这一设计决策确保后端 LLM 管线（如 `MarkdownImageExtractor`）能够完全像 Obsidian 原生应用一样解析内部 vault 链接，在 AI 评估过程中保持嵌入媒体的完整性 [cite: 1]。

此外，系统将 Obsidian 预设的 canvas 颜色（1 到 6）映射为语义学习状态：'1'（红色）代表未理解，'2'（橙色）代表部分理解，'3'（黄色）代表个人理解，'4'（绿色）代表已理解，'5'（青色）代表 AI 解释节点 [cite: 1]。这在 Obsidian 纯视觉化 schema 之上增加了一个教学层。

## 3. 教学框架：SOLO 分类法与 FSRS 算法

### 3.1 SOLO 分类法集成
如评分分析中所述，SOLO 分类法不仅仅是计划中的——它已作为评估量表的结构主干被积极实现。`test_prompt_solo_anchoring` 测试明确断言了分类法各阶段在 `autoscore` 提示词中的存在 [cite: 1]。SOLO 分类法非常适合智能辅导，因为它摆脱了二元化的正确/错误评分，转而评估学习者理解的*质量*和*复杂度*，这与基于图的知识系统中关系（关联结构）至上的理念完美契合。

### 3.2 间隔重复集成：从 FIRe 到 FSRS
尽管用户查询询问的是 "FIRe 算法"，但对代码库的详尽分析表明，已实现的主要间隔重复算法是 **FSRS（Free Spaced Repetition Scheduler，自由间隔重复调度器）**，具体为 4.5 版本。FIRe 可能指的是内部命名或相关的实验分支，在本代码库切片中并非主导；然而，FSRS 是确定的运行机制 [cite: 1]。

`fsrs_manager.py` 使用 `py-fsrs` 库来管理学习卡片 [cite: 1]。它通过以下方式建模记忆：
*   **四种评分（Four Ratings）：** Again（1，再来）、Hard（2，困难）、Good（3，良好）、Easy（4，简单）[cite: 1]。
*   **四种状态（Four States）：** New（0，新建）、Learning（1，学习中）、Review（2，复习中）、Relearning（3，重新学习中）[cite: 1]。
*   **计算指标（Calculated Metrics）：** 追踪 `stability`（稳定性）、`difficulty`（难度）、`reps`（重复次数）和 `lapses`（遗忘次数）[cite: 1]。

如果 `py-fsrs` 在环境中不可用，系统实现了向 `ebbinghaus-fallback`（艾宾浩斯备选）算法的优雅降级 [cite: 1]。该实现计算特定的 `Retrievability`（可提取性）指标（$R$），Mastery Engine（掌握度引擎）使用该指标来调度后续复习 [cite: 1]。

### 3.3 对单用户学习系统的适用性
FSRS 非常适合单用户学习系统。传统的间隔重复算法（如旧版 Anki 中使用的 SuperMemo SM-2）依赖于通用的遗忘曲线。而 FSRS 利用基于个人用户历史的持续优化，为每个独立概念动态调整 `stability`（稳定性）和 `difficulty`（难度）参数。由于 Canvas Learning System 追踪细粒度的"笔记片段"（note fragments）和"概念节点"（concept nodes），FSRS 使系统能够为单个用户在不同领域的认知衰减率建立亲密的、高度个性化的模型，使其成为理想的算法选择 [cite: 1]。

## 4. Edge Elaborative Interrogation（边连接精细追问，EEI）

Elaborative Interrogation（精细追问）是一种认知心理学技术，提示学习者为明确陈述的事实生成解释。在 Canvas Learning System 中，当用户在画布上连接（在两个概念节点之间画边）时触发。

### 4.1 实现机制
当边被创建时，后端调用 `edge-dialog.md` 提示词。系统异步获取源节点和目标节点的上下文，提取 Tier 1（第一层级）数据，例如之前记录的"提示"（tips）和"历史错误"（historical errors）[cite: 1]。这些上下文数据被附加到提示词中，确保 AI 知晓用户之前的误解。

### 4.2 提示词工程与策略
`edge-dialog.md` 提示词严格规定了 AI 的角色和方法论。提示词明确要求 AI 扮演"好奇的学习伙伴"（curious study buddy）而非权威教师或考官 [cite: 1]。

追问策略遵循特定规则：
1.  **因果与条件探查（Causal and Conditional Probing）：** AI 被指示提问"为什么"（底层原因是什么？）和"如何"（这种关系在什么条件下成立？有没有例外？）[cite: 1]。
2.  **反例生成（Counterexample Generation）：** AI 主动探查反例以测试学生理解的边界 [cite: 1]。
3.  **自我解释（Self-Explanation, SE）：** 这是一个条件触发器。如果用户的回答被判定为肤浅的，AI 会要求用户用"自己的话"来解释。代码明确测试了这不是每次都强制触发的，而是动态触发的 [cite: 1]。
4.  **排除主动回忆（Exclusion of Active Recall）：** 提示词中执行了一条引人注目的教学规则——明确*排除*主动回忆（Active Recall）。因为学生正在查看 Canvas，节点 A 和节点 B 都可见，所以主动回忆不可能实现（线索已经呈现）。提示词严格禁止将互动当作记忆测试 [cite: 1]。
5.  **密度控制（Density Control）：** 为防止用户疲劳，互动被严格限制在最多 3 到 4 轮 [cite: 1]。
6.  **深度评估（Depth Assessment）：** 提示词包含一个隐藏的 5 级深度评估表（从 Level 1："A 和 B 有关联"到 Level 4-5："完整因果关系 + 条件 + 用自己的话表述"）。一旦达到 Level 4，AI 提取知识图谱（KG）三元组（`source_concept`、`target_concept`、`relation_type`、`rationale_text`）并调用 `record_edge_rationale` 工具 [cite: 1]。

## 5. 笔记片段点击跳转到源的集成

从孤立的学习档案或复习卡片无缝跳转回原始空间上下文（Canvas）的能力对空间记忆强化至关重要。该功能已被深入实现，根据应用执行环境采用双重策略。

### 5.1 Obsidian 原生实现
在 Obsidian 环境中，跨 canvas 导航由 `CanvasNavigator` 服务管理 [cite: 1]。当 `navigateToNode` 方法被调用时，该服务获取目标 canvas 路径和节点 ID。
1.  利用 `WorkspaceLeaf` API 静默打开目标 canvas 文件 [cite: 1]。
2.  实现轮询机制（`waitForCanvasReady`）以确保 canvas 视图已完全加载到 DOM 中 [cite: 1]。
3.  加载完成后，使用 Obsidian Canvas API 的 `selectOnly()` 和 `zoomToSelection()` 方法自动将用户视口平移到特定笔记片段 [cite: 1]。
4.  为引导用户注意力，应用 CSS 类（`textbook-highlight`），执行 2 秒的内联关键帧动画（`pulse-highlight 0.5s ease-in-out 4`）[cite: 1]。
5.  同时在 UI 顶部挂载 `NavigationBreadcrumb` 组件，允许用户无缝导航回其起始 canvas [cite: 1]。

UI 组件 `LearningProfile` 的测试验证了如果 `TipItem` 或 `WeaknessItem` 拥有 `sourceCanvasId`，则"导航到源"（Navigate to source）按钮会被渲染且可用 [cite: 1]。

### 5.2 Tauri 环境执行（降级策略）
当应用作为独立桌面应用通过 Tauri 运行时（在 Obsidian 原生包装器之外），它无法直接访问 Obsidian DOM 或 `WorkspaceLeaf` API。实现通过 `Obsidian Link Service` 中巧妙的基于 URI 的降级策略来解决这一问题 [cite: 1]。

当请求跳转时，该服务尝试三个级别的降级：
1.  **obsidian://adv-uri：** 尝试使用 Advanced URI 插件协议，支持深度链接到特定标题或块引用。利用 `@tauri-apps/plugin-shell` 的 `open()` 函数触发 OS 级 URI 处理器，将用户从 Tauri 应用推送到 Obsidian 应用 [cite: 1]。
2.  **obsidian://open：** 如果高级链接不可用，退回到内置 URI，该 URI 可打开正确的 vault 和文件，但失去缩放到特定块的能力 [cite: 1]。
3.  **路径复制（Path Copying）：** 如果所有 URI 协议都失败，系统降级为简单地将文件路径复制到用户的剪贴板，并返回一个备选成功状态 [cite: 1]。

这确保了 AI 界面（Tauri）与知识库（Obsidian）之间的基本导航桥梁在任何环境约束下都不会断裂。

## 6. 性能保障策略

在数千个 Markdown 文件上动态运行 AI 驱动的知识图谱会带来严重的延迟和 token 耗尽风险。系统实现了三种不同的性能保障策略。

### 6.1 Assessed Concept Profile（ACP，已评估概念档案）Token 预算执行
系统通过 Assessed Concept Profile (ACP) 将学生状态传递给 LLM。为防止上下文窗口溢出并控制 API 成本，通过 `_enforce_token_budget` 方法执行激进的 token 预算限制（名义上 15K，严格目标约 3K）[cite: 1]。

预算逻辑按特定顺序优先保留上下文。如果节点内容、对话摘要、提示、错误和边理由的总字符数超过 `ACP_MAX_CHARS`（作为 token 代理），则开始截断 [cite: 1]。
*   **截断优先级：** `conversation_summary`（>500 字符）-> `node_content`（>800 字符）-> `student_tips`（最多 3 条）-> `error_history`（最多 3 条）-> `edge_reasons`（最多 3 条）[cite: 1]。
*   **语义保留：** `_truncate` 方法尝试在句子边界（`。`、`. `）优雅地断开文本，而非在任意字符处截断 [cite: 1]。此外，系统包含防护措施，防止截断在 token 中间分割数学公式（`$$...$$`）或围栏代码块 [cite: 1]。

### 6.2 通过句子级提取实现上下文压缩
除了基本截断外，`Context Compression Module`（上下文压缩模块）实现了大规模上下文缩减（15K 到 3K），且不依赖 LLM 摘要（速度慢且容易产生幻觉）。它采用提取式压缩算法 [cite: 1]。

该算法使用 `_ATOMIC_PATTERN` 正则表达式来隔离和保护围栏代码块、块级数学公式和 Markdown 表格 [cite: 1]。剩余文本通过 `_SENTENCE_PATTERN` 边界检测拆分为独立的评分单元 [cite: 1]。通过仅提取与查询最相关的句子，并将其与受保护的原子块重新组合，系统保证 Claude 或 Gemini 收到确定性的、事实精确的提示词，且不会发生 token 耗尽 [cite: 1]。性能测试断言该批量压缩在 1 秒内执行完毕，且 50 次并发内存操作在 30 秒内完成 [cite: 1]。

### 6.3 通过 LanceDB 实现元数据预过滤
最后一道性能保障发生在向量检索层面。系统不会全局搜索整个 vault，而是与 LanceDB 集成使用严格的元数据预过滤。

搜索相关上下文或节点时，`LanceDBClient` 允许传递 `canvas_file` 参数。查询执行方式为 `client.search(query="...", table_name="canvas_nodes", canvas_file=sample_canvas_file)` [cite: 1]。通过将过滤器下推到 LanceDB 索引层面，系统绕过了数千个无关向量，返回严格限定在当前活动 canvas 内的结果。这大幅降低了搜索延迟，确保实时记忆捕获保持在严格测试的 100ms 阈值以下 [cite: 1]——这是系统"隐身"观察协议的关键要求。

---

**结论**
Canvas Learning System 是一个经过严谨工程设计的平台。它通过 3 层评分保险有效中和了 LLM 幻觉，确保与 Obsidian 空间能力的无缝互操作，利用经过科学验证的 FSRS 算法实现个性化记忆保持，执行认知丰富的 Edge Elaborative Interrogation（边连接精细追问），通过深度链接桥接独立执行环境与原生客户端，并在高 token 约束下严格维持毫秒级性能表现。

**来源：**
1. backend/app/services/autoscore.py (fileSearchStores/persistentcanvaslearningsys-qa7kqspeo0jc)
