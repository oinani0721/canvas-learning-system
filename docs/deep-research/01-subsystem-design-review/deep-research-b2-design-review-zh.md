# B2 设计评审：信号融合、知识追踪范式与心理测量冷启动机制的综合分析

**要点与执行摘要**

*   **权重合理性：** 当前信号融合权重（0.30 BKT / 0.25 FSRS / 0.25 Exam / 0.10 Bias / 0.10 Confidence）代表了一种务实的最小可行产品（MVP）分配方案。证据表明，虽然这些权重可以作为功能性基线，但静态权重缺乏数学上的精细度，无法在没有机器学习驱动的自适应机制的情况下捕捉动态学习行为。
*   **BKT vs. DKT/SAINT+：** 研究表明，Bayesian Knowledge Tracing（贝叶斯知识追踪，BKT）在结构上较为陈旧，在预测准确性方面通常被 Deep Knowledge Tracing（深度知识追踪，DKT）和基于 Transformer 的模型（如 SAINT+）所超越。然而，BKT 并未完全过时；它因其可解释性以及对猜测/失误参数的显式建模而保留了显著价值，而这正是神经网络"黑箱"难以提供的。
*   **冷启动问题（<10 个数据点）：** 心理测量数据强烈表明，使用少于 10 个数据点来评估认知掌握程度会产生统计上无效的噪声。可靠的指标通常至少需要 100 次试验，而黄金标准的稳定性则需要 400 次以上的试验。
*   **加权平均算法：** 数学上归一化的加权平均是一种简单的线性方法。它假设信号之间相互独立，无法捕捉认知指标之间复杂的协方差关系。
*   **改进路径：** 系统架构最优的演进方向是在第二阶段升级至 Beta-Bayesian 融合（Beta-贝叶斯融合），集成 Language Model-based Knowledge Tracing（基于语言模型的知识追踪，LKT）以解决零样本冷启动问题，并采用动态心理测量阈值。

---

## 1. B2 信号融合的架构概述

B2 框架当前实现了一个多信号融合架构，旨在评估学习者的认知状态和记忆保持情况。该基础设施主要在 `MasteryFusionEngine` 中运行，并遵循标记为 FR-MAST-06 的核心架构要求 [cite: 1]。

### 1.1 五个核心信号
在第 0 阶段 / 第 1 阶段最小可行产品（MVP）状态下，B2 系统动态注册并整合五个不同的信号，以计算一个单维度的掌握程度分数 [cite: 1]。该框架要求每个活跃信号提供一个介于 0.0 和 1.0 之间的归一化值。这些信号及其基础权重如下：
1.  **BKT 掌握概率 (`bkt_mastery`) -- 0.30：** 从 `ConceptState.p_mastery` 变量推导而来，表示学生已在概念层面掌握材料的贝叶斯后验概率 [cite: 1]。
2.  **FSRS 可提取性 (`fsrs_retrievability`) -- 0.25：** 由 Free Spaced Repetition Scheduler（自由间隔重复调度器，FSRS）提供，该指标（$R$）量化了记忆稳定性以及在给定时间点回忆某条独立信息的概率性可能 [cite: 1]。
3.  **考试成绩平均值 (`exam_score_avg`) -- 0.25：** 该指标追踪学生在多维度自动化评估（AutoSCORE）中的近期表现的归一化平均值 [cite: 1]。
4.  **校准偏差 (`calibration_bias`) -- 0.10：** 一个反向指标，追踪学习者的元认知准确性。它通过将有符号偏差转换为惩罚指标来运作（偏差越大表示掌握可靠性越低）[cite: 1]。
5.  **自信心平均值 (`self_confidence_avg`) -- 0.10：** 从最近 $N$ 次交互中的自我报告调查数据推导而来，有助于系统理解学习者感知到的自我效能感 [cite: 1]。

### 1.2 MVP 融合的数学执行
当前实现通过重新归一化的加权求和算法来数学地解析这些不同的指标。融合引擎轮询 `SignalRegistry` 以获取活跃信号 [cite: 1]。考虑到教育数据经常是稀疏的——即用户可能参与了间隔重复但缺失了自信心自评——系统依赖于一套回退重新归一化协议 [cite: 1]。

对于任何节点 $k$，当其中一部分信号存在缺失数据时，算法会过滤掉非活跃信号，并重新计算活跃信号的权重使其总和等于 1.0。该逻辑的数学表达式为：

\[ W_{sum} = \sum_{j \in active} w_j \]
\[ w_{norm, i} = \frac{w_i}{W_{sum}} \]
\[ fused\_mastery = \sum_{i \in active} (w_{norm, i} \times value_i) \]

输出随后被严格限制在 $[0.0, 1.0]$ 范围内 [cite: 1]。如果没有任何信号包含数据（$K=0$），系统默认返回未评估状态 0.0 [cite: 1]。

---

## 2. 信号权重的批判性评估 (0.30/0.25/0.25/0.10/0.10)

明确的问题是：静态权重分配 `(0.30/0.25/0.25/0.10/0.10)` 是否合理。评估这一点需要从教育学理论、算法设计和系统约束三个方面进行分析。

### 2.1 权重分配的合理性论证
在 MVP 的语境下，该权重分配展示了一种合乎逻辑但高度概括化的教学层次结构。
*   **BKT 的首要地位 (0.30)：** 将最大的数学权重分配给贝叶斯知识追踪模块在理论上是合理的。BKT 基于知识图谱（KG）关联进行运算，追踪的是某个概念的潜在认知掌握程度，而非孤立的机械记忆 [cite: 1]。真正的教育掌握通常定义为概念理解而非简单回忆。
*   **记忆与应用的平衡 (0.25 / 0.25)：** FSRS 可提取性和考试成绩平均值的相同权重建立了时间衰减记忆保持（FSRS）与应用实践知识（考试成绩）之间的平衡 [cite: 1]。FSRS 算法建模的是纯粹的时间衰减 [cite: 1]，而考试测试的是应用能力。
*   **元认知惩罚 (0.10 / 0.10)：** 校准偏差和自信心作为少数修正因子。该架构明确降低了自我评估相对于客观表现的影响力 [cite: 1]。其理由是自我报告的指标高度主观且容易受到噪声干扰。B2 的早期阶段之所以降低了掌握仪表盘的优先级，正是因为旧版自我评估权重与累积 BKT 理念相冲突 [cite: 1]。

### 2.2 静态权重的局限性
虽然对于初始 MVP 来说是合理的，但固定线性权重在先进的智能辅导系统（ITS）和多传感器数据融合网络中受到了严厉批评。
静态权重假设信号的相对可靠性无论在何种上下文、何种学生、何种数据量下都保持恒定。这是一个有缺陷的假设。例如，一个拥有 500 次 BKT 交互但只有 2 次自信心交互的学生，其稀疏且高度波动的自信心数据仍会以固定的 10% 来惩罚其掌握分数（除非被次级可靠性修正器显式处理）[cite: 1]。

在更广泛的信号融合文献中——例如生理信号处理或探地雷达（GPR）——静态无权重或固定权重的空间域平均通常被弃用，转而采用动态互相关算法或小波变换，这些方法根据实时信号熵自适应地分配权重 [cite: 2, 3]。

### 2.3 基于证据的固定权重替代方案
内部文档表明计划向动态权重和 Beta-Bayesian 模型过渡 [cite: 1]。为类似系统设计的机器学习模块明确利用移动平均和反馈循环来动态优化权重。例如，B2 环境中的代码展示了一个用于算法代理的动态权重优化器：
```python
alpha = 0.1  # Learning rate
new_weight = (1 - alpha) * current_weight + alpha * feedback_score
new_weight = max(0.0, min(1.0, new_weight))
```
[cite: 1]。实现类似的学习率（$\alpha$）来根据历史预测准确性（使用考试成绩的交叉验证作为基准真值）动态缩放 0.30/0.25/0.25 的 BKT/FSRS 参数，将提供一个远比硬编码静态浮点数更具经验依据的权重系统。

---

## 3. 知识追踪范式：BKT 相比 DKT/SAINT+ 是否已经过时？

系统设计评审的核心支柱之一是：基础性的 BKT 算法与当代的深度知识追踪（DKT）和基于 Transformer 的模型（如 SAINT+）相比是否已经过时。对教育数据挖掘（EDM）文献的详尽审查揭示了一个细致入微的现实：虽然 BKT 在结构上较为陈旧且数学上更简单，但它服务于一个独特的运营目的，而现代神经网络直到最近才开始尝试复制这一功能。

### 3.1 Bayesian Knowledge Tracing (BKT) 的机制
BKT 作为隐马尔可夫模型（HMM）被引入，它假设学生对特定知识组件（Knowledge Component，KC）的认知掌握存在于一个二元潜在状态中：已学会或未学会 [cite: 4, 5]。可观察的行为（正确或错误地回答问题）通过概率参数与这个隐藏状态相关联。

B2 架构完美地映射了经典 BKT 的执行过程，使用四个核心参数 [cite: 1]：
*   **$p_{prev}$（先验）：** 掌握的初始概率。
*   **$P_S$（失误）：** 尽管已知概念仍犯错的概率 $P(\text{incorrect} | \text{mastered})$。
*   **$P_G$（猜测）：** 在没有真正知识的情况下正确回答的概率 $P(\text{correct} | \text{not mastered})$。
*   **$P_T$（转移）：** 在一次交互后学会该概念的概率 $P(\text{learn} | \text{not mastered})$。

后验更新遵循贝叶斯定理。对于正确回答，掌握概率更新为：
\[ p_{posterior} = \frac{p_{prev} \times (1-P_S)}{p_{prev} \times (1-P_S) + (1-p_{prev}) \times P_G} \]
对于错误回答：
\[ p_{posterior} = \frac{p_{prev} \times P_S}{p_{prev} \times P_S + (1-p_{prev}) \times (1-P_G)} \]
最后，系统考虑学习转移：
\[ p_{new} = p_{posterior} + (1 - p_{posterior}) \times P_T \]
B2 系统将这些值限制在 `[0.001, 0.999]` 范围内，以防止零分母边界错误 [cite: 1]。

**BKT 是否过时？** 就纯预测准确性而言，是的。然而，BKT 提供了无与伦比的**可解释性**。每个参数都直接对应于人类教学概念。教师和系统管理员可以轻松理解分数为何发生变化 [cite: 6]。一项关于教师决策的研究发现，BKT 在"理解"子量表上获得的评分显著高于 DKT [cite: 7]。此外，BKT 已建立了样本量要求，允许系统设计者在数学上确定统计可靠性所需的数据量——这是大多数现代神经算法明显缺乏的特性 [cite: 8]。

### 3.2 Deep Knowledge Tracing (DKT) 深度知识追踪
由 Piech 等人于 2015 年提出，深度知识追踪通过放弃 BKT 手工制作的、孤立的隐马尔可夫模型，转而采用循环神经网络（RNN）和长短期记忆（LSTM）模型，彻底革新了这一领域 [cite: 5, 6]。

DKT 将学生在一段时间内的整个学习序列表示为高维连续的隐藏状态 [cite: 9]。与 BKT 独立建模知识组件不同，DKT 能够自动推断不同技能之间的复杂关系，而无需领域专家手动定义"Q-矩阵" [cite: 5, 10]。

*   **性能：** 经验数据一致表明 DKT 优于 BKT。追踪编程入门学生的研究显示，DKT 及其领域特定变体（如 Code-DKT）在 ROC 曲线下面积（AUC）方面比 BKT 高出 3.07% 至 4.00% [cite: 5]。在拥有海量数据集的环境中，DKT 建立了稳健的预测基准 [cite: 5, 11]。
*   **局限性：** 尽管准确性更高，DKT 存在严重的缺陷，这些缺陷为其被排除在 B2 当前 MVP 之外提供了合理依据。首先，DKT 模型是不透明的"黑箱"；它们无法解释*为什么*一个学生被认为是精通的 [cite: 6, 12]。其次，DKT 容易出现"退化行为"。研究人员发现，在某些情况下，学生答对一道题实际上会导致 DKT 模型的预测知识概率下降，同时在极短时间内表现出剧烈且无法解释的概率估计波动 [cite: 8]。最后，DKT 需要海量数据集才能有效运行，使其高度容易受到冷启动问题的影响 [cite: 11, 13]。

### 3.3 Transformer 模型：SAINT 和 SAINT+
数值序列知识追踪领域的最前沿已从 RNN 转向基于 Transformer 的架构，由 Separated Self-Attentive Neural Knowledge Tracing（分离式自注意力神经知识追踪，SAINT）模型及其后继者 SAINT+ 引领 [cite: 4, 9]。

SAINT 使用类似于自然语言处理（NLP）模型的编码器-解码器框架。编码器处理练习嵌入流，而解码器通过多头自注意力机制处理回答正确性嵌入流 [cite: 4, 14]。
**SAINT+** 引入了 BKT 和传统 DKT 都不具备的关键时间特征：
*   **答题用时（Elapsed Time）：** 学生回答问题所花费的实际时间。
*   **间隔时间（Lag Time）：** 两次连续学习交互之间的时间间隔 [cite: 8, 14]。

通过编码这些时间序列，SAINT+ 在 EdNet 数据集（目前最大的公开教育数据集之一）上相对于 DKT 实现了额外 1.25% 至 2.76% 的 AUC 提升 [cite: 4, 5]。

### 3.4 范式过时性的裁定
为直接回答设计评审的问题：**BKT 在原始预测 AUC 方面在技术上已经过时，但对于 MVP 架构而言并*非*功能性过时。**
B2 系统当前依赖于一个显式融合引擎（`MasteryFusionEngine`），该引擎要求标量值（0.0 到 1.0）且具有高可解释性 [cite: 1]。将 BKT 替换为 DKT 或 SAINT+ 需要部署大型深度学习推理服务器，处理不透明的黑箱参数——这与系统的 `self_confidence` 和 `calibration_bias` 透明性目标相冲突，并且在引入新教育概念时面临严重的冷启动惩罚。BKT 的简洁性、透明性和计算效率使其非常适合 B2 的第 0/1 阶段 [cite: 1]。

---

## 4. 冷启动困境与稀疏数据处理（<10 个数据点）

"少于 10 个数据点时会发生什么？"这一问题触及了心理测量评估和机器学习系统中最普遍的缺陷之一：冷启动问题。

### 4.1 样本量的心理测量学现实
当系统使用少于 10 个数据点来评估认知表现、一致性或元认知校准时，所得指标被统计噪声所主导。
在评估序列测试数据的认知控制和心理测量可靠性研究中（例如 Stroop 类范式、任务级抑制），分半信度（Split-half reliability，即数据随机分半后的相关系数 $r$）需要大量试验才能达到有效性 [cite: 15, 16]。
*   **最低可行样本量：** 关于视觉和认知辨别任务的研究表明，计算分半信度至少需要 **100 次试验**，才能达到可接受的相关系数 $r > 0.5$ [cite: 1, 17]。在 100 次试验时，平均 68.2% 可信区间精度约为 0.055 到 0.071 [cite: 18]。
*   **黄金标准样本量：** 要获得稳定的、高置信度的重测信度（test-retest reliability）——这对精确的掌握追踪算法至关重要——研究人员认为每个受试者至少需要 **400 次试验**。信度增长率在 400 到 700 次试验后急剧趋于平缓，确立了 400 次作为稳态指标提取的理想阈值 [cite: 1, 17]。

**对当前系统阈值的批评：**
B2 内部架构承认了诸如 `<10`、`10-20` 和 `20+` 等用于确定元认知可靠性的阈值。这些在统计上被认为是无效的 [cite: 1]。在不足 20 个问题的情况下，将用户的校准或自信心呈现为"可靠"指标——并对其掌握分数施加 10% 的惩罚权重——将使用户的学习轨迹受到虚假数据的影响，导致糟糕的自我调节学习决策 [cite: 1]。

### 4.2 知识追踪中的冷启动问题
在算法领域，"冷启动问题"发生在新学生进入系统或引入新课程/知识组件（KC）时。由于传统模型（DKT、DKVMN、SAKT）完全依赖由数值 ID 定义的历史交互序列，当历史数据缺失时它们会完全失效 [cite: 12, 13, 19]。
如果一个学生的数据点少于 10 个，深度学习模型将难以预测未来状态。研究表明，冷启动条件下的 DKT 模型本质上退化为随机猜测（AUC $\approx 0.5$），因为它们无法利用基于孤立数值标识符的预训练 [cite: 13, 19]。

### 4.3 B2 中当前的回退机制
面对稀疏数据时，B2 系统当前执行两种主要的回退算法：
1.  **FSRS 时间衰减回退：** 如果学生的数据点少于 10 个，且不存在正式的间隔重复卡片，引擎会依赖连续的指数衰减数学估计，而非纯粹的神经追踪。可提取性 $R$ 基于经过的时间动态计算：
    \[ R = e^{-\frac{\Delta t}{\max(S, 1)}} \]
    其中 $\Delta t$ 是自 `last_interaction_ts` 以来的 `days_elapsed`（经过天数）[cite: 1]。如果用户*从未*与该概念交互过，可提取性默认为理论值 `1.0`（作为未评估的基线）[cite: 1]。
2.  **信号重新归一化：** 如果某个信号由于低样本量而严格未能返回数据（`value = None`），`MasteryFusionEngine` 会临时移除其分配的权重（例如校准偏差的 0.10），并在数学上将剩余有效信号重新归一化至等于 100% [cite: 1]。

为在数据少于 10 个点时大幅提升系统完整性，UI 和 API 应采用**预测性稳定化**策略。系统应采用修订后的阶段划分：
*   **第一阶段：探索期（<100 个点）：** 仅使用软性定性启发式（例如"正在收集基线数据"）。对于推导出的元认知指标，信号权重应有效设为 0 [cite: 1]。
*   **第二阶段：趋势期（100 - 400 个点）：** 数据被使用，但附带可见的置信区间 [cite: 1]。

---

## 5. 加权平均算法是否过于简单？

该问题质疑数学上归一化的加权求和逻辑（`fused_mastery = Σ(w_i_norm * value_i)`）是否过于简单 [cite: 1]。

### 5.1 系统简化及其缺陷
是的，对于一个高保真的智能辅导系统而言，加权平均从根本上过于简单——这一事实被系统自身的文档隐含地承认，其中将"高级 Beta-Bayesian 融合"保留给第 2 阶段以后 [cite: 1]。

加权平均的主要局限在于它假设信号之间具有**线性独立性**。在认知心理学和学习科学中，记忆保持（FSRS）、概念掌握（BKT）和自信心等信号具有高度的共线性和相互依赖性。
例如，B2 框架内部有一个用于计算 `effective_proficiency`（有效熟练度）的算法，计算方式为 `min(p_mastery, R)` [cite: 1]。这一逻辑正确地断言：
*   高掌握但低可提取性 = "学过但忘了。"
*   低掌握但高可提取性 = "记住了机械性事实，但缺乏概念理解。"

然而，将这些高度相互依赖的变量输入平坦的线性加权平均会破坏其中的细微差别。加权平均允许某一指标的高分掩盖另一指标的关键缺陷。如果学生的 FSRS 可提取性为 0.90 但 BKT 掌握度仅为 0.20，平均值将输出一个中等分数，虚假地暗示部分掌握，而实际上该学生完全依赖对表面特征的短期机械记忆。

### 5.2 高级多流融合基准
在复杂的信号处理领域（例如生理传感器数据、探地雷达），朴素加权平均通常作为早期基准使用，但很快被时空算法所取代 [cite: 2, 3]。

1.  **多相关时空融合（Multi-Correlation Spatiotemporal Fusion，STMF）：** 在机械和传感应用中，自适应权重通过实时分析信号能量的互相关函数来计算 [cite: 3]。将其应用于 B2，意味着如果 `self_confidence` 的方差与 `exam_score_avg` 的方差不相关，则其权重将动态降至接近零。
2.  **图卷积网络（Graph Convolutional Network，GCN）弱信号融合：** 在高级编程知识追踪（PKT）中，弱信号簇（例如微小的代码修改或有噪声的自信心评分）使用簇感知 GCN 进行融合。该技术从不需要的噪声中隔离出核心语义表示 [cite: 20]。基本加权平均将噪声和有效数据同等对待，只要它们共享相同的输入管道。

---

## 6. 战略建议：如何改进 B2 系统

为使 B2 框架超越其 MVP 状态，并纠正关于过时 KT 模型、无效冷启动阈值和过于简单的融合算法等问题，应整合以下结构性改进：

### 6.1 过渡到 Beta-Bayesian 信号融合（第二阶段）
最直接的算法改进是执行计划中的向 Beta-Bayesian 融合的过渡 [cite: 1]。系统不应生成平坦的标量平均值，而应将输出掌握度视为一个概率分布（由 $\alpha$ 和 $\beta$ 参数化的 Beta 分布，分别代表成功和失败次数）。
*   诸如 `exam_score` 和 `bkt_mastery` 等信号更新分布的形状参数。
*   这种方法本质上解决了权重分配问题：具有高方差的信号（低可靠性，例如 $<10$ 个数据点）自然会产生宽而平的后验分布，确保它们相比高置信度信号对聚合掌握指标的拉力几乎可以忽略。

### 6.2 采用基于语言模型的知识追踪 (LKT) 以克服冷启动
为在不丧失 BKT 可解释性或采用 DKT 刚性黑箱神经结构的前提下实现知识追踪引擎的现代化，架构应转向 **Language-based Knowledge Tracing（基于语言的知识追踪，LKT）** [cite: 13, 19, 21]。

LKT 用知识概念（KC）和问题的原始文本表示替换了 DKT 使用的数值 ID 序列。序列使用自然语言标记进行格式化（例如 `[CLS] concept_text question_text [CORRECT] [EOS]`），并输入到预训练语言模型（如 BERT 或 RoBERTa）中 [cite: 21]。
*   **解决冷启动：** 由于 LKT 理解语义含义，它可以推断一个拥有零历史数据点的*全新问题*的难度和认知要求 [cite: 13, 19, 22]。它绕过了 $<10$ 个数据点的失效循环。
*   **可解释性：** 与 DKT 不同，LKT 的注意力图可以通过 Local Interpretable Model-agnostic Explanations（局部可解释性模型无关解释，LIME）进行分析，以精确显示学生在*哪些词*或概念上存在困难，从而保留了 BKT 的教学可解释性 [cite: 13, 22]。

### 6.3 实施动态机器学习权重
与其争论 `0.30` 还是 `0.25` 是否合理，框架应扩展在其他 B2 领域中使用的机器学习权重模块 [cite: 1]。通过建立基准真值（例如总结性考试的表现），系统可以训练一个简单的逻辑回归或注意力层，以针对每位学生动态分配传入信号的权重。如果特定学习者经常表现出高校准偏差但考试成绩优秀，机器学习层将自主降低其 `calibration_bias` 的权重。

### 6.4 建立心理测量级别的数据阶段划分
最后，系统必须放弃 `<10 / 10-20` 的可靠性阈值。UI 和 API 必须重构以实施严格的心理测量门控：
1.  **$< 100$ 次交互：** 隐藏硬性掌握数值。显示置信区间或启发式提示（"正在建立基线"）。完全禁用 `self_confidence` 和 `calibration_bias` 惩罚，因为它们在统计上是无意义的噪声 [cite: 1, 17]。
2.  **$100 - 400$ 次交互：** 开始显示定量融合指标，但保持较高的误差范围方差。
3.  **$> 400$ 次交互：** 启用完整的算法影响力。应用所有元认知惩罚，因为重测信度在数学上已趋于稳定 [cite: 1, 17]。

通过放弃静态线性权重、采用 LKT 实现语义冷启动解决方案、并强制执行严格的心理测量数据阈值，B2 系统将从一个功能性 MVP 过渡为一个在学术上严谨的、最先进的智能辅导架构。

**参考来源：**
1. docs/deep-research-b2-signal-fusion.md (fileSearchStores/persistentcanvaslearningsys-z2njevmxp7md)
2. [nih.gov](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGsFhiHLDO6jqQ8zpnJWdQbsP6Lp7ilBpZ8NGknLoDpn6dkZRN03AU5IRZjg04HfcOuHU7U1lBRUdbeHcmIHfyOvMrxRbNPQWRffIqTp1kCVXH4kwEPkBlqeZuCk5SpSwoXBpay78HCPw==)
3. [mdpi.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH4eP0KpVvmHoRRTl4ND78xNzS8Wll9nkCKt9Fk9zjEYcoHA_aXJ3K7RaFbwhGUyxZVFB_eRZl1QrH8KFsNqTi-J3D3iEoAQjmbME6YnF-RAv_2auKiapdXNuev7K92nw==)
4. [rtest.ai](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFBPmVuBpsn1dKC4JzSa3b1Q3NPH21IauwaZhfb3o-AlFz7zdA_bhUv1e1lDrwPntERLWwtDdDugF3fO9WVZllW5nWmBt8fU3gjia60Lzl-fwZgvMsX5oAYsOxd5Ts=)
5. [educationaldatamining.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE3hl00IWpUKuVqQo7TwTbXi2xH9u7jgL0IE4CqKGpRxgGntWDY5Y5B4nP7v3c_uAbz8MGlvolr3M2EmUYaFcjUdiLRU1a0AdYGDH2voL-l_BQwo34G7SIIjn2XO3Qh3BDZbcidBhITcip5A8PZqu3lb8taq8SiEi6y8X_ZOS0lDZMwaC1kycYtYeSsfFY=)
6. [medium.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGStodZNx7pH_xipvSFoNemp-ku4ZKgTcFlmJYYE48OkmwiaUbDjrrf-CN7eGJ90-0jFykC9aG8eCTuNeYguRR91FKpWuPp61hhhKPDDT0Rc6ivwCZMWntMsN1F18Od-TJpf-YcCQRksZ8eWezmPNxcKHkI5-N6jaJjJZsjQ3UVTEjtiGdtZjVFJqE5LWJp3HM3mWDYvlg=)
7. [themoonlight.io](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGdPucdv2Cj7XqmUblYr4xlVkibeqNLUOWPoa9oKBXixu_FX6pUKS5jd75Z3ZqX7qwxMPrRAibnkt5PASayn_j5_SrKP7YSaxXBlElcDffv5Irp7Q0mrMa_Nj4Fc7ZjGRwCA5HLu7q4SeOrS-N5XZ2nt5Sy7VyZ7DUh03ZvQCUqRq8YVhju6KnCcnE2Rcysq7pqkiWQ4Bqpt4Pop1wB0ZWQ1vVhQRJyyJzmGBJJYw==)
8. [upenn.edu](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHQwjjkvzrmJ6VuYRt_SLAtFq_ofcdeyBPBXnzhiZt5Tp_A0iDBX6GS1r8EDL0LNmfMPP2siVQ0Q_lr4v_akUwN4vAwBb5IR0DGxDjkMn_qD3yOkca1-RQIWL7K6UdjlF64iWW-i7NR2GXgxv8t3wNGyGtUE8Cw2Fe79PxCIC9ZrxehltBXj2qjW5Hk8drP_84=)
9. [arxiv.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFjNHSg5vV6Y4t6vF6taF-e2IeqmilctZfzXNq2lQx5bMQ4kA2imtmWxd3AfjemCMbmXPXQM_UVvIYUnNShsamq06JFq1jN5lrGR6rReHLudWrBdQ62qc3tvw==)
10. [researchgate.net](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHcqHcU5qQOCOYAHGVN-evn1TfAkpNoXgngm6ttf2-3OydnAaI3TyqPCi43jCCxxSS-XmLagcsSagNqIbMEw6UK6kWf7HHCZUpRpyubku0uOZ_HzgobAV55aGGbBBvNreJnf-76EdJfYEXeaN7d-g0jfTFQELbqppveKxyfvVAwBUf3f8lmdXVbH1rkXjMqUQqgD-sFpBCS53uRfR18MF-qwRV6ECXQ6Hm2TFLbV84=)
11. [polimi.it](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFUbBViCC2uLSKTlFBye3JLWoioRdEPivR8nKTR_3zwbJjX_Qddhpd9e-q3oRSGrAfFAHQ5259fwgAgtGEMdh1xQ-HlXSJEN1aLcPzrA0-CsUf6LSguDhHKUNosksAwLOlKbkVnpQ9H5aaXGdCVSE64LODJbmZ06LLoEfvXGQwYWKpe2mqVqJLjnQTGfMuJvSDOgHlcUPQlH5Gfo7Lo-OK4kCr1k5enUJakRNjlme6JMuz4QoTtvoGUZ9K7E5ywzmzJqv6J7U2fENk5NIm0ERVUto12MYYIFJYMrisW6S9-YfnfBT_xp-O6VkUU4qwEqzQrz-06Ld84XP2iO6BJMutsBR_nWY5sIPBPWQPkDQyq7Ge6BrGUbMkW0oDAH_5D6dnf6RceFVrC)
12. [researchgate.net](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGBYMsnkKoM9nYFHJcwrH7K9vAQ3sP6SfenoMGmn4gHVr7t51buSplIrG1rgZjjxxwLqkVUXbLF3d2aIrzsNqhUKcjH_ctM6Oo5fGRmyXo8BNlOHy4iQoRpGwMOU5vuM9MwM96vNZ36QfaAy0SGVW1m8waqAH68JytFWn_9F2O4aiuQNeKxDjCQkHXvZ3vAP24eDLajn_-h79ume1cRYHp-PwZawOIdB7gBmA==)
13. [arxiv.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQErap_QALe5F8kDfPI8UZzWh6QPe4bTl-ZhM9pkfJ-3R19QL3_dZTmZNYbK4M_igXJtuG5SiRTbsb1tZDVhhPL-5szEg24WzpzEaNP9A8S6httecBa_jvFX1g==)
14. [computer.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGtN6DSrJtp7okHJz4F47HhgqvXBdnL50V882TygcXR2UitveJ7Cuib6YJOoo95un5ue6V-h4JruOzY2SRJXwo_dCB_jjEcKYkjaip-q3DqOd-gtWn_oULWgI1YVGxrjuxQQFOGnVQzA1XCfrMhO2NfAVkq2IhiO4f1MZU=)
15. [nih.gov](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHVRYhiNRP_AIB4WT88H89DrLLGlQ_wVpMJkCjdyKet2b991vuSfGG4U7g9IDUh8ZS854YtzOHuECeGm-30gDB4iEDf_eR9DptKp4aaza8_7jm3IekfecZnzqSP0qMjGX5YfjMrAjE6)
16. [researchgate.net](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQF7mUikH8SlVZYWsbYdOafikTnMx_GL5qYq0riYbzITzmvAiGXjCDFq3pATSty-lVGgweqWKwvu2zxOaJbn9KPlCn7496PRCXd7eAeYdacZtD6gRQgpat6s7HwM8yQLe0qRFLgclMxtSKNEe37-oGplKUBQm2AfZyF2S9u5-LXq2UXxzIHyPv8LjQDjp3z_sphgKBa5D9RHu3vki6bORE-qTM9DniZPM9sRx9CFKCLYXUs2H06ayTRL9oiPnJxlrTjeO7sM2l-9egSVQ1FgzlGI2ojLIncDJLKVYMvYvYNozPeAguwZQHzvRTiGcYWCzt8aoSD3z68ftVUox6BTaXSXFQHAYUgq9WPpUj5kV-meRAftWX4z1z8R0LzVXvAG1-pS8WqLPw==)
17. [frontiersin.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQELdt7KJFFiFl_Zmmym7GGflzhvtCvLbWcIZbb7_ps1f4L7daRPUIS2OoXvBT8wKx5ApMvbStsBdYRFAg_FqzOsEsDSgjAa-bqDPWPTcqbZvCTPG_qo5rL_bMrydcn8_H21DomTjBOLYwCPOKDav-AECfNQ9nJzlgnqMTm7oNYRjXG-VYnHelL4Hgr4ng==)
18. [arvojournals.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQF6q8zh64dqNktaxFARPMRHHaE69te3x_iwDDmcF6zog9Niel1tvRdbFKaxr9pHuXklF50frdFK3MDoCrpqjCwcRFO9NIdNWaE7Ggb_cV-tM4PSnbGlhenR24c5mdTM80F0w1HCKHSvL5z-jYBlymgt6g==)
19. [arxiv.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHgdjezWchmy9sN-kIJF66X9Pz8KaN_E_UAMW9CPHuqTtLmEjlLQTHdWTBlapn_ZeAXf73y6ZVU9tD7p7e92LWfm8cFflAFPinU0bA4WcW49TwM54zlbw==)
20. [arxiv.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFZMl1QO_K5tuO3pTrmC_0-8AeGnRD-gBzWljckw1B8TXE3QCiF44qfGvoJwrJzOheHkeb-gUs9r4w-hewLURw1lAKDeKOGadOv6t1LqLFe8d0X4knWnA==)
21. [themoonlight.io](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFECwd5Zn4g8DBleymSZc_3MzlaDZ0cqW8FbAm-MDBZk1-XdwQbKsjLdUbOoIReJ4RIgmxvjbeBbS4T77FcUqPGf-jeNvB3MQT0jq4F0sFVzeGVSbiJW9sXybAPEYodkjb4LsolQNlWnxv2wEUSL6DhKAFA2WAeY03TLILTqYXOBmBHfz3EZDKejUl9y6ziW8hRJBoGi_6WOXy3tmtLgPaNGTqG4mhhf2A_jMvTXJyz1GnVFeQ4AhNVO-2bDOJ9jm1CN6kidbLtvIVyTez3aPj1DffLNUO37A==)
22. [emergentmind.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHpankGly81cL6pOdzWUSHqykTzxLbgsSQm4vGu-EjFjQqQF_1Dmhk6ClQJRPlyh50arId5Hmxyk3QYrna_3uUweHT57NQqJTPe0B1xu5ysKfWly0c0M2o1x57DqwChR5Qr3kV5G0f5RQXMY9ai2A==)
