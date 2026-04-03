# B6 设计评审：评分、边缘对话与校准机制的批判性评估

*   研究表明，为单用户应用部署三层评分保险系统（3x 采样、4 维评分标准、双模型验证）已接近严重的计算资源过度投入，因为现代大语言模型（LLM）利用零样本思维链（Chain-of-Thought, CoT）提示配合严格的评分标准，往往无需多次采样即可达到与人类评估相当的相关性。
*   有很高的可能性认为 **SOLO 分类法**（Structure of Observed Learning Outcome，可观察学习成果结构）从根本上优于 Bloom 修订版分类法（Bloom's Revised Taxonomy）用于自动化 AI 评分，主要原因是 SOLO 评估生成回答的可观察结构性成果，而 Bloom 试图对内部认知过程进行分类。
*   证据倾向于认为精细化追问（Elaborative Interrogation, EI）的 3 至 4 轮限制是最优校准的；这一约束能够有效防止工作记忆过载，减轻额外认知负荷（extraneous cognitive load），同时保留深层语义加工所需的相关认知负荷（germane load）。
*   在 Tauri 中依赖操作系统级自定义协议（如 `obsidian://adv-uri`）会引入关键故障向量；如果目标应用未安装，操作系统无法解析该协议，导致 WebView 中出现静默失败或未处理的 `ERR_UNKNOWN_URL_SCHEME` 异常。
*   当前三阶段元认知校准追踪阈值（<10 收集 / 10-20 趋势 / 20+ 可靠）似乎严重偏低。关于元认知指标（如 Gamma、Phi 和 meta-d'）的学术文献普遍建议基本的折半信度至少需要 100 次试验，400 次试验则是统计稳定性的黄金标准。

B6 系统的设计整合了多种先进的教学和计算机制，涵盖自动化 LLM 裁判评估（LLM-as-a-judge）、元认知校准矩阵（metacognitive calibration matrices）以及通过 Tauri 实现的本地优先应用路由。评估这些子系统的有效性需要跨学科视角，涉及认知心理学、统计测量理论和软件工程。虽然 B6 系统的理论基础展示了对学术严谨性和以用户为中心学习的明确承诺，但将这些理论转化为自动化的单用户软件架构时会产生摩擦点。

在计算成本与评估可靠性之间取得平衡、将 AI 提示框架与适当的教学分类法对齐、以及在主动回忆过程中管理人类认知局限性，都是至关重要的挑战。此外，确保强健的软件降级策略以及为追踪人类自我效能建立数学上合理的样本量，对于系统的长期稳定性至关重要。本报告对 B6 系统的五大核心支柱进行批判性评估，识别理论错位、设计弱点以及可操作的结构性改进路径。

## 1. 三层评分保险：过度投入还是确有必要

B6 系统的自动化评估方法采用三层保险模型：三次（3x）采样、4 维评分标准和双模型验证。核心问题是这种配置对于单用户系统来说是否属于计算过度投入，以及使用评分标准的单次（1x）采样方法是否已经足够。

### LLM 随机性的统计现实
大语言模型具有固有的随机性。从模型概率分布中采样的单个输出可能具有很大的误导性，导致评估分数的波动 [cite: 1]。"LLM 裁判"（LLM-as-a-Judge）的概念作为人类评估的可扩展替代方案已获得广泛关注，但它极易受到多种系统性偏差的影响：
*   **位置偏差（Position Bias）**：模型倾向于偏好首先呈现的选项，而不考虑其内在质量 [cite: 2, 3]。
*   **冗长偏差（Verbosity Bias）**：模型将长度与质量混淆，即使实际内容单薄，也会给更长、结构更复杂的回答打更高分 [cite: 2, 4]。
*   **自我增强（亲和性）偏差（Self-Enhancement/Affinity Bias）**：模型对其自身模型家族生成的文本或与其训练分布相似的文本表现出统计偏好 [cite: 2, 4]。

为了对抗这些偏差，"LLM 陪审团"（LLM-as-a-Jury，多次采样或使用多个不同的 LLM）等技术被提出，用以平均化个别模型的特异性并减少系统性偏差 [cite: 2]。运行多次自助法（bootstrap）采样理论上可以量化测量不确定性；然而，严格的自助法重采样通常需要 500 到 1,000 次迭代才能建立紧密聚集的测量可靠性，这使得计算成本急剧攀升 [cite: 5]。

### 单用户系统的成本效益分析
在单用户教育或个人知识管理环境中，单个分数的风险相对于企业级自动化部署管线来说较低。通过 3x 采样使每次评估交易的 LLM 成本（和延迟）增加两倍，所获得的边际收益递减。

研究表明，当先进的 LLM 受到精心设计的评分标准和思维链（CoT）提示的约束时，仅需单次通过即可达到与人类判断超过 85% 的一致性 [cite: 3, 6]。这一一致性通常超过不同人类标注者之间约 81% 的基线一致率 [cite: 6]。因此，虽然 3x 采样加双模型架构提供了几乎万无一失的评估，但对于常规单用户评分来说，这明显属于**过度投入**。

### 单次采样配合严格评分标准的充分性
单次（1x）采样方法的充分性成立**当且仅当** 4 维评分标准经过适当优化。为了最大化单次通过的可靠性，系统必须采用以下具体缓解策略：
1.  **思维链（CoT）提示**：强制 LLM 在输出最终数值分数之前逐步生成其推理过程，这会将模型牢牢锚定在评分标准上，并大幅提高准确性 [cite: 6, 7]。
2.  **显式偏差惩罚**：为了对抗冗长偏差，4 维评分标准必须明确指示评判者惩罚不必要的冗长回答，并将简洁性作为独立的评分指标 [cite: 4]。
3.  **基于参考的评分**：当提供"黄金标准"的预期输出时，单输出评分具有很高的可靠性，使 LLM 能够计算与已知事实基线之间的距离或相关度 [cite: 6]。

### 设计弱点与具体改进
**弱点**：固定的三层架构造成了不灵活的成本负担和高延迟，在快速学习会话中降低了用户体验。
**改进**：实现**动态置信度路由（Dynamic Confidence Routing）**系统。默认使用高度约束的 CoT 4 维评分标准进行 1x 采样。仅当 1x 通过产生低置信度分数时（例如，LLM 在其生成的 CoT 中表现出不确定性，或分数恰好落在关键的通过/未通过边界上），才触发 3x 采样或双模型降级。

## 2. SOLO 分类法与 Bloom 分类法在 AI 评分中的对比

B6 系统将其评分标准锚定在 **SOLO 分类法**（Structure of Observed Learning Outcome，可观察学习成果结构）上。关键问题是 SOLO 是否是 AI 评分的最优框架，还是 Bloom 修订版分类法等替代方案更为优越。

### SOLO 与 Bloom 的概念区别
要确定自动化评分的最佳框架，必须明确两种分类法的根本目标：
*   **Bloom 分类法**：对**认知过程**以及学习者参与的思维活动类型进行分类（如记忆 Remember、理解 Understand、应用 Apply、分析 Analyze、评价 Evaluate、创造 Create）[cite: 8]。它关注的是*学习者在内部如何处理知识* [cite: 8]。
*   **SOLO 分类法**：对学习过程的**可观察成果**进行分类。它衡量生成回答的结构复杂性和质量（前结构 Prestructural、单点结构 Unistructural、多点结构 Multistructural、关联结构 Relational、抽象拓展 Extended Abstract）[cite: 8]。

### SOLO 在 AI 评估中更优越的原因
LLM 无法窥探学生的内心来评估他们用于得出答案的内部认知过程；AI 只能分析提交给它的文本。由于 Bloom 分类法关注的是不可见的认知过程 [cite: 9]，将其用作自动化评分标准往往导致模糊不清。一个学生可能使用了高级综合能力（Bloom 的高层级），但写出了结构松散、支离破碎的回答。

相反，SOLO 分类法是专门为评估*可观察成果的结构*而设计的 [cite: 8]。LLM 擅长文本分析和结构分解。它可以轻松识别提交的文本是否包含孤立的事实（单点结构）、不相关的事实列表（多点结构）、构成连贯整体的相互关联概念（关联结构），还是应用于新领域的一般化原则（抽象拓展）[cite: 8, 10]。

研究表明，Bloom 分类法和 SOLO 分类法具有高度互补性，而非相互排斥 [cite: 8]。Bloom 描述导致理解的行为，而 SOLO 描述该理解的最终质量 [cite: 8]。

### 设计弱点与具体改进
**弱点**：完全依赖 SOLO 作为系统的*全部*教学框架，忽视了任务本身的生成。AI 模型仅使用 SOLO 难以生成难度适当的问题，因为 SOLO 评估的是成果而非输入。
**改进**：实现**双轨教学框架（Bifurcated Pedagogical Framework）**。在生成端专门使用 **Bloom 分类法**来指导 LLM 如何设计提示并针对特定的认知难度级别 [cite: 9, 10]。然后在评估端的 4 维评分标准中专门使用 **SOLO 分类法**来评估用户生成文本的结构质量和深度 [cite: 8, 11]。

## 3. 边缘精细化追问：评估 3-4 轮限制

B6 系统采用精细化追问（Elaborative Interrogation, EI）机制，上限为 3 至 4 轮。核心问题是这个限制是过于严格还是过于宽松，并寻求有研究支撑的最优 EI 会话长度指导。

### 精细化追问的作用机制
精细化追问是一种循证学习技术，学习者被提示提出"为什么"和"如何"的问题，以生成对概念的解释，迫使他们将新信息与现有心智图式（mental schemas）建立联系 [cite: 12]。这种主动的意义生成防止了被动消费，并将信息从短期处理推入长期记忆 [cite: 13]。

然而，EI 的有效性受到**认知负荷理论（Cognitive Load Theory, CLT）**的严格制约。CLT 认为人类工作记忆具有严重的局限性；过载会导致学习崩溃 [cite: 13, 14, 15]。认知负荷分为三种类型：
1.  **内在负荷（Intrinsic Load）**：材料本身的固有难度 [cite: 16]。
2.  **额外负荷（Extraneous Load）**：由设计不当的教学或环境摩擦造成的不必要心智努力 [cite: 13, 16]。
3.  **相关负荷（Germane Load）**：用于处理信息、构建图式和深度学习的有益心智努力 [cite: 13, 16]。

### 3-4 轮限制的分析
精细化追问需要高强度的主动处理，这会严重消耗工作记忆。让学习者经历过多连续轮次的"为什么"和"如何"提问，会迅速将有益的相关负荷转变为压倒性的额外负荷，导致认知疲劳和收益递减 [cite: 14, 15]。

研究表明，最优认知负荷存在一个"甜蜜点"——即工作记忆被充分调动但未过载的点 [cite: 15]。虽然写作和编辑任务通常会自然地分配为多个聚焦轮次 [cite: 17]，但在没有间隔或交叉练习的情况下持续进行的长时间追问可能会排挤长期记忆 [cite: 18]。

严格的 3 至 4 轮限制与已确立的认知科学中管理认知负荷的协议高度一致 [cite: 15, 16]。它提供了足够的深度来迫使学习者进入 SOLO 分类法的*关联结构*或*抽象拓展*阶段，但在工作记忆耗尽之前及时截止。

### 设计弱点与具体改进
**弱点**：硬编码的固定 3-4 轮限制未能考虑不同主题的*内在负荷*。对于简单的陈述性事实，4 轮可能令人烦躁地多余。对于高度复杂、多层次的科学范式，3 轮可能在学习者达到突破之前人为地截断了其图式构建过程。
**改进**：过渡到**动态负荷监测限制（Dynamic Load-Monitored Limit）**。将 3 轮设为基线默认值。但是，编程充当对话代理的 LLM 以监测用户回答中的认知疲劳迹象（例如句子碎片化、重复、脱离深层语义处理）。如果用户的结构性输出（通过 SOLO 衡量）在第 3 轮开始退化，系统终止会话。如果用户展示出较高的关联能力，系统可以动态允许第 5 轮，但严格限制于此，随后将该主题安排进入间隔重复（Spaced Repetition）以允许记忆巩固 [cite: 12, 18]。

## 4. Tauri 笔记导航：`obsidian://adv-uri` 降级策略

B6 应用使用 Tauri 作为其桌面环境，集成了点击跳转笔记导航系统，该系统使用 `obsidian://adv-uri` 作为降级方案。本节探讨该机制的可靠性、Obsidian 未安装时的后果以及固有的系统弱点。

### Tauri 中自定义协议处理器的机制
Tauri v2 通过操作系统级 WebView 管理外部链接和协议。默认情况下，尝试导航到自定义 URI 方案（如 `obsidian://`）需要严格的配置。Tauri 使用自定义协议处理器安全地向 WebView 提供内容（例如 `tauri://localhost/`），避免暴露传统的 HTTP 服务器 [cite: 19]。

要与 Obsidian 等外部应用交互，应用依赖操作系统内部的 URI 方案注册表。当用户点击 `obsidian://` 链接时，Tauri 前端触发操作系统查找注册到该协议的应用。

### Obsidian 未安装时会发生什么？
如果宿主机上未安装 Obsidian，操作系统将没有任何应用注册来处理 `obsidian://` 协议。因此，当 Tauri WebView 尝试执行该链接时，它将无法解析。

在基于 Chromium 的 WebView（如 Windows WebView2）中，这通常导致控制台抛出未处理的网络错误：`net::ERR_UNKNOWN_URL_SCHEME` [cite: 20]。因为 WebView 不知道如何处理该方案，它会尝试将其作为原生资源请求处理，随后失败——从用户的角度来看，界面毫无反应，造成静默失败；或者如果应用的 URL 状态与源不同步，可能会破坏进程间通信（IPC）命令处理器 [cite: 20, 21]。

### 设计弱点与具体改进
**弱点**：依赖外部操作系统级自定义协议作为硬降级方案引入了脆弱的依赖关系。如果用户未安装 Obsidian，或 `obsidian-advanced-uri` 插件被禁用，系统的导航将静默失败，降低用户体验并可能破坏 Tauri WebView 的作用域检查器的稳定性 [cite: 21]。
**改进**：实现**预检操作系统注册表检查与优雅降级（Pre-flight OS Registry Checks and Graceful Degradation）**。
1.  **后端验证**：利用 Tauri 的 Rust 后端查询宿主操作系统注册表，在 UI 中渲染链接之前验证 `obsidian://` 协议处理器是否存在。
2.  **本地 Markdown 解析降级**：如果 Rust 后端检测到 Obsidian 未安装，UI 不应尝试使用 `obsidian://` 协议。相反，应使用 Tauri 的 `fs` API 直接从本地文件系统读取目标 Markdown 文件，并在 B6 应用内部的模态框或专用阅读视图中原生渲染。
3.  **严格的作用域配置**：确保 `tauri-plugin-opener` 或 `tauri-plugin-deep-link` 在 `Cargo.toml` 和 `tauri.conf.json` 中正确配置，在安全内容安全策略（CSP）中明确允许 `obsidian://` 协议，以防止原生 WebView 阻止 [cite: 20, 22, 23]。

```rust
// Example Tauri Setup for Opener Plugin
tauri::Builder::default()
    .plugin(tauri_plugin_opener::init())
    .run(tauri::generate_context!())
```

## 5. 元认知校准追踪：样本量的现实

B6 系统使用 Area9 风格的 2x2 矩阵追踪用户的元认知校准（主观自我评估与客观表现之间的匹配程度），经过三个阶段：<10 数据点（收集阶段）、10-20（趋势阶段）和 20+（可靠阶段）。

### 元认知校准的数学基础
元认知监控准确性历来通过各种统计度量进行量化，包括 Gamma (\(\gamma\))、Phi (\(\phi\))、分辨力（Resolution）、校准度（Calibration, \(C\)）以及信号检测理论（SDT）指标如 Meta-d' 或 Meta-d'/d' 比率 [cite: 24, 25, 26]。

*   **校准度（\(C\)）**：反映置信度判断与实际表现之间的绝对对应关系（例如置信度减去表现）[cite: 24]。
    \[ C = \frac{1}{N} \sum_{j=1}^{J} N_j (c_j - o_j)^2 \] [cite: 26]
*   **分辨力（Gamma/Phi）**：捕捉个体内部区分正确和错误回答的能力，独立于总体偏差 [cite: 24, 26]。

### 20+ "可靠"阈值的谬误
认为 20+ 数据点即可产生"可靠"校准指标的断言，根据严格的心理测量学文献是明显错误的。元认知表现度量本质上是嘈杂的，因为它们复合了一类表现（实际任务分数，二元正确/错误）和二类表现（主观置信度评级）的测量误差 [cite: 27]。

当样本量较小时，Gamma 等统计量和比率度量在数学上变得不稳定，导致剧烈波动和"元认知膨胀"（metacognitive inflation）[cite: 25, 28]。

*   **最小可行样本（100 次试验）**：跨多个数据集的大量折半信度（split-half reliability）测试表明，元认知度量仅在使用绝对最少 **100 次试验**计算时才开始显示可接受的折半信度（\(r > 0.5\)）[cite: 25, 29]。
*   **黄金标准样本（400+ 次试验）**：为获得稳定、高置信度的重测信度（test-retest reliability）——特别是在使用 Meta-d'/d'（Mratio）等高级指标时——研究者建议每个被试至少进行 **400 次试验** [cite: 27, 28, 30]。在 60% 任务准确率下，即使 400 次试验也会产生较差的 Pearson 信度；系统需要高任务表现（80%+）才能在 400 次试验时达到稳定的指标 [cite: 27]。

### 设计弱点与具体改进
**弱点**：当前阈值（<10 / 10-20 / 20+）在统计学上不足以确定元认知可靠性。在 20 个问题后就将用户的校准呈现为"可靠"，很可能展示的是统计噪声而非真实的元认知能力，导致用户基于虚假数据做出糟糕的自主学习决策。
**改进**：从根本上重新校准追踪阈值以符合心理测量学现实，并为低样本量引入预测性稳定化：
1.  **修订后的阶段划分**：
    *   **阶段 1：探索期（<100 点）**：不显示硬性指标。显示柔性的定性启发信息（例如"正在收集基线数据"）。
    *   **阶段 2：趋势期（100 - 400 点）**：显示带有可见置信区间的指标，警告用户数据仍在趋于稳定。
    *   **阶段 3：可靠期（400+ 点）**：解锁完整的 Area9 2x2 矩阵仪表板。
2.  **贝叶斯正则化（Bayesian Regularization）**：为了使 <100 阶段在无需等待数月积累 400 个数据点的情况下具有一定的可用性，实现贝叶斯正则化（例如分层 Mratio 或有界正则化）。通过应用先验分布，系统可以在数学上将小样本的极端估计值向均值收缩，防止当一类表现方差接近零时出现数学上不可能的比率飙升 [cite: 27]。

## 6. 设计弱点与改进的综合总结

下表对 B6 系统的关键评估进行了综合总结，提供了已识别弱点及即时可操作的工程和设计改进的结构化概览。

| 系统组件 | 已识别的设计弱点 | 学术/技术依据 | 具体的结构性改进 |
| :--- | :--- | :--- | :--- |
| **评分保险** | 3x 采样 + 双模型对于单用户规模严重过度投入，成倍增加 API 成本和延迟，却没有成比例的教学回报。 | 严格的评分标准结合单次思维链（CoT）提示即可达到与人类评估者 85%+ 的相关性 [cite: 3, 6]。 | **动态置信度路由**：默认使用 1x CoT 采样。仅当 1x 分数触及关键通过/未通过边界或表现出低生成置信度时，才触发 3x/双模型。 |
| **分类法锚定** | 完全依赖 SOLO 限制了系统生成任务的能力，因为 SOLO 评估成果而非认知输入。 | Bloom 关注内部认知*过程*，而 SOLO 评估结构性*成果* [cite: 8]。AI 评估文本，需要 SOLO。 | **双轨框架**：在生成端专门使用 Bloom 修订版分类法指导 LLM 的提示生成，在 4 维评分标准中专门使用 SOLO 分类法评分文本输出。 |
| **EI 会话限制** | 固定的 3-4 轮限制过于僵硬；对简单主题可能导致认知疲劳，对复杂主题则可能过早截断深度探索。 | 认知负荷理论指出，持续的追问会使工作记忆饱和（额外负荷），导致学习崩溃 [cite: 13, 14, 15]。 | **动态负荷监测**：设置 3 轮基线。指示 LLM 监测用户的语义深度。如果出现碎片化则提前终止；仅在结构复杂性持续增加时允许最多 5 轮。 |
| **笔记导航** | 对 `obsidian://` 的硬依赖在应用缺失时会抛出 `ERR_UNKNOWN_URL_SCHEME`，可能导致 Tauri IPC 作用域检查崩溃。 | 操作系统对未注册的自定义 URI 没有原生处理器。WebView 将未知方案视为致命网络错误 [cite: 20, 21]。 | **预检检查与降级**：通过 Tauri 的 Rust 后端查询操作系统的协议注册表。如果不存在，则优雅降级为使用 Tauri `fs` API 的内部本地 Markdown 解析器。 |
| **校准矩阵** | 20+ 数据点的"可靠"元认知校准阈值在数学上无效，将显示极端的统计噪声。 | 元认知分辨力和校准度指标（Gamma、Meta-d'）至少需要 100 次试验才能达到折半信度，400 次才能达到稳定性 [cite: 25, 27, 28]。 | **修订阈值与正则化**：将阶段调整为 <100（探索期）、100-400（趋势期）、400+（可靠期）。实现贝叶斯分层建模以在早期探索阶段稳定比率指标。 |

## 结论

B6 系统代表了现代认知科学与生成式 AI 的高度复杂整合。然而，弥合理论教学法与强健软件架构之间的差距需要妥协。通过缩减评分系统的计算蛮力、正确地双轨化分类框架、动态管理认知负荷、强化原生操作系统降级策略，以及将统计阈值与心理测量学现实对齐，B6 系统可以在大幅降低运营成本和故障状态的同时，显著提高其面向用户的分析的有效性。

**参考文献：**
1. [arxiv.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHlcn9gCSWeOz_pT5jxlFHXquQGFdxTdvpROdX2t7ceMaqqZtsaXDmZ8TpPPKKTEzKUFMgrC30sXTX61CuvaS3LpCOovG8v03XRksUxhCzyF4cBC2rqUw==)
2. [labelstud.io](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFHEVFnxAtJp7wJkgWPnsYVO9tSxVr1RVzFcKBCh1jZ7gl2d9HSd2oroh1A3ky8aKHu0QeUl8AmEPJ-XwQtctrU9MCcdqZV_NGtD7fVEwgbpuObPMqqeiC6BVKvGcxl8nfTaHJx7asGlsSZj8kA-4DhZDAHktsTyMyIu20x7jb1yaYckew=)
3. [openlayer.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFnSLDcRmJcyuTkI7Tdb0-d5w2MgwTjVmEtkS3CsgHabLc90_BBsASiKLNuyM2R-nRbgO54IngydgUsiO5fgjnfsyr5Hlk0hItDC4ubbkfdU13vDili1vKPJn1wDxynQSjD_r6o_Z60iTbCd-3crcR5F61YdEZKMQ==)
4. [medium.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEWSM__gjOvAAiJL3ryBWy4zRM-E0baQ5t9KtqeFUsv9fe8buEIhHI0ABMSfyd61KajYcoq_WvprHNXqSA_NYTzI4wkJTBaMQNVfX08K08pik7LjK172quLsEoiLvBUzEdoOaxmaffYFnXVp4pyoCovcJK9_UKGilbqkViU-Rpic8sBCsd7W2dPdlUgVjjaLNKOlh9m9PX1Iy5sT78JAWsXL4Y=)
5. [medium.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFq4SumHgxYm2ikDUj_OrWmrhhuNS8zJIQi7iYdOxchuA1wxWz-sp5ZpYLm1L7ED3XfXDieB-EsO0C6XHYd70H6zgwS6lVmxji0y28ZwgixjhIPMRBGNfPyyrXUF2R43P8fdgmOelWQkVSlZV9v3CI4ae_3n2SATw1gPhb2ZQRPjgUfDvou7c0gTqavRv1my3x80hbpbZW5JPVkgSL9P4QsPSmgZj3HkFjqKpIb583fEHJMux_Lx8cJAavO)
6. [confident-ai.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGFnYxalDK36H50KWGt_vOSvZsEg2CAXkuFj-TFwjeBJ7g552W0vbJQTukXvZjQboKYay3Trm12vIixoJQCj0Khu0eKPi_v9wSRvoIoxOYGoHlXiLXt4ITZJzGD74QtUw8LY5g3kGlueUbcsp8-JQnDaKuUxJBDrXBL5oLkIKYMLmik8bKgWz3plusF8A==)
7. [eugeneyan.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGRwbRlGuUm9jcnPIBGW1shFBeWw3e-V63r3KQUVI4gWfN9EpaDinMO83dMc2aPz-kotZ0MVx9eLzrpi2vszMjvj-cd51t6uQGUsLmpNDqq_MBZfiUElPr_vIpfEMaGUlaQQOU=)
8. [funblocks.net](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEKV7xmHJAyPK-sxzBc7nXu6q9HYpP5UgAE4aA-gSwV05vjc6aejx2TnBOOWuVYByc9XAWSvFFWcSIAdatg4xwR9Lhi8J0UMlKEweJ_4Auej_iBAW0J5I_fvOWyik-XPbNevFfeYi1DZcE4IfCadGx8k0GBDQ9PNQNiqsnmBnDgATuJXgw=)
9. [kwarc.info](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHrND_DYfEA8veoqQESrOrS0qsl_hy40v0LS2wAveB9GObh74iwcFR84_hmm5Y0RA7pwii_gTU5CJp9Zrv-FYpHhZFzCL_pWQjUSLELxKnzh1WMx0fmPEOcmUfGVU3SH3Ti7n7QFLDiZ-RMhw==)
10. [arxiv.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFnywtOVoHbpIEajN5LeuGF_tm7R7LsIF1jEPNwJJgaat1H1g0wlbPhhHXXn6k8kbSMedN_cFh82gc53vX9SepGxv5l3UTMnqBmoBoK6D5yF7uUVskT7A==)
11. [thecasehq.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE4nE-5Rw_x5li7y3P6wiav_xbAfOuHfBP3rdjNhth0f9IhlTs7qOtw1EVLxFPWAse8VGDQA7j1f4YTnplomxDWTWelh_-cKcx7weda1K1CDrObELX9obYnK5xEeuynuLiNycFlEWY3r3AY4kHvlywT10u0P2s=)
12. [pdf.ai](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQF1W5IB2clnIEm5e0oJsBIpBw_bA9GYhPAUePzWKf9JMb7-SYfqlGx1DOUYj8X0ExdCDXHZBEpeEkCpB8xqJ8iO6Ty9X5RfXVRPUza3vABNEjwI8b2WiAAdkfyD8-bepbVQcEyRSP0zleYlwuO_)
13. [structural-learning.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG8Xigu_On9crkiqssTioFMZRQc7ye4hYoByDjdoskYeVCI-HI10kM3pz49oLSN5RDakUgM8rqDJ3Velw3GOJBTT2YuwUssc1zod86AGyNpxIYLhrrf2ZCaKYtn_o7P5soPWU3nzrej2c0pMvgnDM35PWawf_-eJR-KWWXo)
14. [brainscape.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGpR91M3Nkm9qBBELoFkzD_q6tIOQhh8YCybE3XUmTmLn21PzXC9xdvijT8UAjb3I9Awr9dIK7N8hRHa5Gq4PcWuc4Iedt1ZV5PH1GDwNSmOO-fKIFJOvx5jcCRDDWMQ51vhf6G05Jvi7aExRIQI6JXW6iJYg==)
15. [chartered.college](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFmcbHLDu9oLxkWXoaXBfAQ6q-sQL8noGZNtOY4Baecu2vKV7TNkIq2a7Z-lCWzLPrXKBFW6_RlnShibES7qUgnoGuwVBCxvpAz3LWhsvZ9xLCbk97XL2aNEtPfy3i3odsSgzDrlw3NqVPjyN4rhDWkTwtLXCdkm06UNslEsuSZnt8GNkW8BDzssCGp1I7rt3fv)
16. [learnfast.ac](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFTRNNgwrf8u7d8d4e5wWV-35YAceDlv5pjfsInhOetDhpqjZ7ZdGguOnMpFsOFInJew_Ylk95yKsWwm-Dbb0KTXyNr-Tr0mZksTLW2GyPAYMissCmIGvNydfgKEyEJ8KL9ObuGJ5Ph71kr)
17. [learningscientists.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFvKZwTS-KAXw43fvVfroYetyU8snYAPY6droVH9_ylOfc3FVenP-gA0EdjHI20lptmjUR1MkTuaQTRi5THeRIwoEcWAKxYbssJxuR6a-6OiDoa3WJnsWpCUd3DLBdIoyrQ3vqPsU-e4mMv)
18. [llu.edu](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGJjnQBF6LO2fdj5eVRXWmMKE5T2VI4GofA320quTdEroKA6QkkB-5wXp1pZHxTyYPl0GvAqeS5vx7lq08DttLbWZpPvs3RJ1_QhcmRe9S3X8F0NwDFl9lHBfbvK5SZLtSPuR2SEfaOf9rvP_DHNZeVIoAPimR54HwuBEpPpvW9BqxbV0npJIAa8NrYBq5YOf83WM6WoCywObTwrwz8oZxjG3PmqgWsrn53EsSG-yg8hZP0YEp_)
19. [reddit.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFL3LvgT3Z5Dj6JN6lXryJLQVNoYZ_Y2Hv4qviEq51MokPmwLuzCCHh3TyWgMP2hBVAwcq_Bb70T6CRSfueuLfsUwojddV_xGeSzuwQgMhtwRk055w8A1FizIe5SI18QprqVqnf-mnnICo-yTzfeGlv7fwbl-YZyZTBjHHE9KOb83_cwNrtLlDoFh8VRkHW4cK8HNzDEO0=)
20. [stackoverflow.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH5MTPe50Qbtu7mbwOFua4-xuH8oz_CwHzQZbi1adzSDr9wzx6YiyeNOFNxzvnco_pE371ybrhnl6VqDyIumJJPkgqgfc2mGPi-PH-Byo0AVWDt8Grqi3kj-hL-zcRdbcsfPqkjuCaBElzG57tlKtkJMHrBL_490h49vdPfQFlafbxrZ1FJ2eJFopgU)
21. [github.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE_1XQO4zUFAaF9Qhj4WiciBn4QDcJYYOrMybd-lENqk_tHyC6tb95DWQEhoeOFXel14gsP-GRPgJqFkwyqmRV3EIxBPk9dSOMMaJSHMr-2fqHwok4pJ0Y9BtAWF0jEbW1nn07j6w==)
22. [tauri.app](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHfAL_HNgSEEdmYazucz3OqctQc3ngDk2irHOag8l2s_5DWPQn5OsVAHKCD_3hzg3WLPwsLn0CMAbAGrltq7nEwyFJmRBYyM0cuGQcnhAHx7C_x2V-hR432dg==)
23. [dev.to](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFNtXr7NdqywaSxboKfchOQ6TIqRF6CPCKfqYBkvLvIRxeaRvnGh-TbpvmBVrQ2XYFk5U8ZciL6Sr3aIVem53DWjr-PBAhKy98PMeyUoCN8t33wR7g-Z34s3pZhdMOW9_JyJg-IuwdYoHdydvfDuuOsJmtemm2tXmbwZzGjhQmbOCv0hmITaPdUcvvnhMbeCuT468s=)
24. [mdpi.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGrHzQ9r9P7deF4_1dWMvPFdr7FVFUXbDZnc-5NG-N6NUckSMfSfx5lWU3l8QOsZUs0d-Tb3ITmB9ZLJiahrP3wlnR4cE0gxJVnwWGAOs2wEA7_rEKSRjwxwjK5FQ==)
25. [nih.gov](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFhA94uJuJvShabnnR1LHtjJ-GBDNYH1je5kLjmOECH0pBxoFPJJNZ-lSyXU82OjpR7YEtJ72Wp7sRWIXv6XeyKMdQHmaAixnw00fKrCfcfs5aO5olxQ09Gx6TFtL-Gno_85tM6vW6YIQ==)
26. [oup.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQF8g63uTzRgqfcHbni3JjHzF5efh6zLBSpuUFeao6cZMbGA27qYDtz_3emDw5we_44bityqScWldYh0g_ZmUJcTZOjPbzjPV3NjTCUzvZ84mP-QT60VYn9ensQjc5oX0SdgX8FMG34ipqAtwflQ6hk=)
27. [nih.gov](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFl-Te7y9Q2fflHm6nMuWxkWwVeiHJPVhGW9nZXTuT3XzjrcWNziTuKk_BuMEkRariCRfvoKX9LWdh9VwIvInUCxURCGAzKsiArDvcfTg0h9V2uyfLXjX2HcbVVoINmg9ASB8nYPAA9)
28. [researchgate.net](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEcZG6YFw1ABsQ-Wa2kz_tIUHSCWP23OyDjDDIMaSU4zkXTr2Tp6GSxXd0BSSavjrPpPq_ckQqX3ca94DmbEJvbZHAincBkwBVTirJywbPpHVqfcco5fVM7RfRKt4oulDCaobG7FtNBj7SnxiPX5ffAWYWrEVwMa4j6UNHRGS799GMzPf3g821VQbwq9xRq0juW9C7Q6mUuoCV4oYBO2s4xhvdwpoYPlNDIf_SJH7Ls1ucrLFf5PO-jrXZUR1-gLzhMhfHj7u9z)
29. [researchgate.net](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFy1WLlrinhxY3WUqJ1r_qEFkeAlw01ZN_L4rAYuQjbTnE2i8Fnmvp5I0ucJBeUHSTLHgkTGNrqKom9tZZTM3cM4MHnighaEJ4sQsRf66ACF-I4r-ngUqM5jYjvNRwF0QSHTW34wjTocwWZViTx-6Cxa6Oeogbd6IdyVVRNLpl_vaAPEoTzd9lvmLJ-wX5vMM_iAmrZAyfVWaBtfhuY88JBYPAN7pTL2i1CazVNwQM1qyJe)
30. [nih.gov](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFf3OV5uGgY4q3nPG9_JDIF_40bkiXXLQN51Ns1SpvSZosNK7QUjSZep9oDDceqR5OTDzMrfBpBvOMZKwiqhS6CIhvrX-xfrEeaDCE29ZdleHVhptttNrQrP2ElQBDnc28zuz64-sJk)
