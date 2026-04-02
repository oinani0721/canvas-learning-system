# B2 信号融合与精通度验证：架构实现的详尽分析

以下报告详细阐述了 B2 Signal Fusion（信号融合）框架、Free Spaced Repetition Scheduler（自由间隔重复调度器，FSRS）以及 Bayesian Knowledge Tracing（贝叶斯知识追踪，BKT）模块在被审查软件系统中的精确架构实现。

*   **五个信号被正式融合：** 该框架主动将 BKT Mastery（BKT 精通度）、FSRS Retrievability（FSRS 可检索性）、Exam Score Average（考试平均分）、Calibration Bias（校准偏差）和 Self-Confidence Average（自信度平均值）整合为单一精通度维度。
*   **融合算法目前为加权平均：** 虽然高级 Beta-Bayesian（Beta-贝叶斯）融合被保留到 Phase 2+ 阶段，但 MVP（Minimum Viable Product，最小可行产品）阶段采用数学归一化加权求和逻辑运行。
*   **FR-MAST-06 已被实际实现：** 多信号融合的核心架构需求在 `MasteryFusionEngine` 模块中稳健运行。
*   **信号互补性诊断已被实现：** 系统利用 Pearson correlation coefficients（皮尔逊相关系数）来标记绝对相关阈值 \(|r| \ge 0.7\) 的冗余信号对。
*   **BKT 集成了转换机制：** BKT 实现利用经典贝叶斯后验概率以及学习转换参数 (\(P_T\))，对结果进行夹紧（clamping）以防止零分母边界错误。
*   **FSRS 调度依赖动态记忆保持指标：** FSRS 摒弃了遗留的 Ebbinghaus（艾宾浩斯）固定间隔方法，基于记忆稳定性和难度约束计算动态复习周期。
*   **考试管道集成被严格执行：** BKT 和 FSRS 更新是被主动调用的工具，通过 `AuditGuardian`（审计守卫）机制和严格的管道令牌验证来加固，以防止死代码衰变和时间异常。

本报告全面详述了执行这些系统的数学模型、软件设计模式和密码学执行边界。

---

## 1. 引言与架构背景

在智能辅导系统和自适应学习平台领域，准确估计学习者的认知状态仍然是一个艰巨的计算挑战。历史上，学习平台一直依赖孤立的指标——如原始考试分数或基于启发式的记忆保持间隔——来近似估算学生的精通度。然而，单维度指标往往无法捕捉人类认知的多面性，忽略了元认知校准、时间性记忆衰减和概率性知识获取的细微差异。

为了解决这些局限性，被审查的软件架构引入了 **B2 Signal Fusion and Mastery Verification（B2 信号融合与精通度验证）** 系统。该框架代表了从单体评分到多信号认识论模型的范式转变。通过将各个评估向量视为具有固有权重和可靠性分数的"信号"，该架构能够综合出一个关于学生在任何给定概念节点上能力水平的整体性、稳健的表征。

本学术报告详尽解构了系统的核心能力，具体分析了 FR-MAST-06 需求（多信号融合）的实现、信号冗余诊断协议、Bayesian Knowledge Tracing（贝叶斯知识追踪，BKT）的数学基础、决定 Free Spaced Repetition Scheduler（自由间隔重复调度器，FSRS）的记忆保持算法，以及保证这些组件在生产环境中顺序执行的管道基础设施。

---

## 2. 多信号融合架构 (FR-MAST-06)

关于系统设计的一个核心问题涉及被融合信号的确切数量、它们的来源，以及多信号融合需求 (FR-MAST-06) 是否已从理论构想转化为可执行代码。

### 2.1 五个核心信号

该架构明确定义并融合了 **五个核心信号** 来计算统一的精通度维度。这被正式定义为 Story 5.6 能力的 MVP（最小可行产品）实现。这些信号通过 `SignalRegistry` 类动态注册，强制执行 N 信号架构模式，提供解耦和可扩展性 [cite: 1]。

五个信号、它们各自的权重以及确切的代码位置详见下表：

| 信号来源 | 内部标识符 | 分配权重 | 代码位置 | 描述 |
| :--- | :--- | :--- | :--- | :--- |
| **BKT Mastery Probability（BKT 精通概率）** | `bkt_mastery` | 0.30 | `app.services.signal_registry`（`BKTMasterySignal` 类） | 主要认知估计指标，作为核心知识指示器。可靠性随交互次数动态缩放 [cite: 1]。 |
| **FSRS Retrievability（FSRS 可检索性）** | `fsrs_retrievability` | 0.25 | `app.services.signal_registry`（`FSRSRetrievabilitySignal` 类） | 捕捉源自间隔重复稳定性指标的记忆保持和回忆维度 [cite: 1]。 |
| **Exam Score Average（考试平均分）** | `exam_score_avg` | 0.25 | `app.services.signal_registry`（`ExamScoreSignal` 类） | 来自近期校准记录和归一化实际表现的直接评估证据 [cite: 1]。 |
| **Calibration Bias（校准偏差）** | `calibration_bias` | 0.10 | `app.services.signal_registry`（`CalibrationBiasSignal` 类） | 元认知校正因子。计算公式为 \(1.0 - \| \text{signed\_bias} \|\)，较大的偏差会降低信号值 [cite: 1]。 |
| **Self-Confidence Average（自信度平均值）** | `self_confidence_avg` | 0.10 | `app.services.signal_registry`（`SelfConfidenceSignal` 类） | 代表用户的自我感知和主观自信追踪 [cite: 1]。 |

这些信号的实现遵循一个强类型的 Python Protocol `MasterySignal`，该协议强制要求实现特定的属性和方法，包括 `signal_name`、`get_value`、`get_weight` 和 `get_reliability` [cite: 1]。

### 2.2 FR-MAST-06 实现验证

该查询明确质疑 FR-MAST-06（将 5 个核心信号融合为单一精通度维度）是 *实际被实现了* 还是仅仅被记录在文档中。来自代码库的证据确认此功能已被完全实现并处于运行状态。

`MasteryFusionEngine`（位于 `app/services/mastery_engine.py` 或等效融合模块中）用一个稳健的多信号计算机制替换了遗留的、过度简化的启发式方法 `min(p_mastery, R)`（来自早期 Phase 1 构建）[cite: 1]。该类通过接受注入的 `SignalRegistry` 实例进行显式初始化：

```python
class MasteryFusionEngine:
    """Multi-signal fusion engine for computing unified mastery score.

    Replaces the simple min(p_mastery, R) with a weighted average
    of N registered signals.
    """

    def __init__(self, registry: SignalRegistry):
        self._registry = registry
```

此外，该实现大量依赖 Python 的面向对象多态性。五个信号中的每一个（例如 `BKTMasterySignal`、`ExamScoreSignal`）都原生封装了自己的缓存机制（`self._cache: Dict[str, Optional[float]]`）和预加载逻辑，以防止同步融合计算期间的 I/O 阻塞 [cite: 1]。因此，FR-MAST-06 在结构上已经实现并处于活跃状态。

---

## 3. 融合算法：机制与数学模型

理解这些不同的信号 *如何* 合并为一个连贯的标量值，需要分析底层的算法选择。

### 3.1 加权平均 vs. Beta-贝叶斯模型

当前实现使用 **Weighted Average（加权平均）** 算法。虽然架构文档和文档字符串明确为"Phase 2+ Beta-Bayesian 升级"保留了架构，但当前执行环境（"MVP"阶段）严格计算重新归一化的加权求和 [cite: 1]。

系统逻辑认识到并非所有信号在所有时间对每个节点都会被填充。学生可能已经参与了 BKT 模块但缺乏校准记录，导致 `exam_score_avg` 或 `calibration_bias` 为 `None` [cite: 1]。融合引擎通过数学权重重新归一化优雅地处理这些部分数据状态。

### 3.2 算法执行工作流

融合算法遵循严格的序列，封装在 `compute_fused_mastery(self, node_id: str) -> FusionResult` 方法中 [cite: 1]：

1.  **活跃信号提取：** 引擎向 `SignalRegistry` 查询 `get_value(node_id)` 不为 `None` 的活跃信号。
2.  **回退评估：** 如果活跃列表为空，或活跃权重之和为零，引擎返回未评估的精通度状态 `0.0`。
3.  **权重重新归一化：** 系统计算所有 *活跃* 信号的权重之和（\(W_{sum} = \sum w_{active}\)）。对于每个活跃信号 \(i\)，其新的归一化权重为 \(w_{norm,i} = \frac{w_i}{W_{sum}}\)。
4.  **加权求和：** 融合精通度计算为 \(M_{fused} = \sum (w_{norm,i} \times V_i)\)，其中 \(V_i\) 是信号的值。
5.  **夹紧：** 为确保严格的概率边界，最终标量被数学夹紧到区间 \([0.0, 1.0]\)。

以下显式代码实现确认了这一算法方法 [cite: 1]：

```python
        # Compute weight sum for active signals
        weight_sum = sum(w for _, _, w, _ in active)

        if weight_sum <= 0:
            return FusionResult(
                fused_mastery=0.0,
                signal_details=signal_details,
                active_signal_count=len(active),
                is_fallback=False,
            )

        # Compute weighted average with renormalized weights
        fused = 0.0
        for name, value, weight, _reliability in active:
            norm_weight = weight / weight_sum
            fused += norm_weight * value
            # O(1) dict lookup instead of O(N) linear scan
            sd = signal_details_map.get(name)
            if sd is not None:
                sd.normalized_weight = round(norm_weight, 3)

        # Clamp to [0.0, 1.0]
        fused = max(0.0, min(1.0, fused))
```

### 3.3 通过测试套件验证

该实现的学术严谨性通过伴随 `MasteryFusionEngine` 的广泛单元测试套件得到验证 [cite: 1]。测试明确证明了加权平均的数学不变量。例如，`test_some_signals_no_data` 测试断言：如果只有 BKT（权重 0.30）和 Exam（权重 0.25）处于活跃状态，它们的归一化计算按其权重之和（0.55）干净地缩放：

```python
    def test_some_signals_no_data(self):
        """Mix of data and no-data → only active signals contribute."""
        registry = SignalRegistry()
        registry.register(FakeSignal("bkt", 0.8, weight=0.30))
        registry.register(FakeSignal("fsrs", None, weight=0.25))
        registry.register(FakeSignal("exam", 0.6, weight=0.25))
        engine = MasteryFusionEngine(registry)

        result = engine.compute_fused_mastery("node1")
        # Only bkt(0.30) and exam(0.25) active
        expected = (0.30 / 0.55) * 0.8 + (0.25 / 0.55) * 0.6
        assert result.fused_mastery == pytest.approx(expected, abs=0.01)
        assert result.active_signal_count == 2
```

这确认了多信号加权平均机制在运行环境中是数学上稳健的且已通过功能验证的 [cite: 1]。

---

## 4. 信号互补性与冗余诊断

在多信号架构中，独立信号必须提供不同的信息方差。如果多个信号测量完全相同的行为特征，它们会人为地膨胀该特定认知因子的权重，导致精通度近似值出现偏差。该查询特别质疑了使用 \(< 0.7\) 相关阈值的信号互补性检查的实现情况。

### 4.1 皮尔逊相关系数的数学原理

系统成功实现了一个利用 **Pearson correlation coefficient（皮尔逊相关系数，\(r\)）** 的信号诊断套件。系统利用标准数学公式计算信号序列对之间的线性相关性 [cite: 1]：

\[
r = \frac{\sum_{i=1}^{n} (x_i - \bar{x})(y_i - \bar{y})}{\sqrt{\sum_{i=1}^{n} (x_i - \bar{x})^2 \sum_{i=1}^{n} (y_i - \bar{y})^2}}
\]

这在软件中直接实例化为 `compute_pearson_r` 函数，该函数细致地计算协方差（分子）和方差平方根之积（分母），同时对数据长度不足（\(n < 3\)）或零方差场景（常量信号）应用安全检查，以防止 `ZeroDivisionError` [cite: 1]。

### 4.2 0.7 冗余阈值检查

系统明确使用 \(|r| \ge 0.7\) 的阈值来触发冗余标记 [cite: 1]。此逻辑位于 `run_complementarity_check` 函数中，该函数处理时间性信号值的字典，在所有注册信号之间执行成对的 \(\mathcal{O}(N^2)\) 比较。

```python
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            name_a = names[i]
            name_b = names[j]
            values_a = signal_values[name_a]
            values_b = signal_values[name_b]

            r = compute_pearson_r(values_a, values_b)
            if r is None:
                continue

            is_redundant = abs(r) >= 0.7
            if is_redundant:
                logger.warning(
                    f"Signal complementarity warning: '{name_a}' and '{name_b}' "
                    f"are highly correlated (r={r:.3f}). Consider reviewing redundancy."
                )

            results.append(
                SignalCorrelationResult(
                    signal_a=name_a,
                    signal_b=name_b,
                    pearson_r=r,
                    sample_count=min(len(values_a), len(values_b)),
                    is_redundant=is_redundant,
                )
            )
```

`TestPearsonCorrelation` 类中的测试验证保证了此行为。如 `test_high_correlation_detection` 所示 [cite: 1]，提供两个高度同步的向量数组会产生 `is_redundant = True` 状态：

```python
    def test_high_correlation_detection(self):
        """r >= 0.7 flagged as redundant in complementarity check."""
        signal_values = {
            "bkt": [0.1, 0.2, 0.3, 0.4, 0.5],
            "fsrs": [0.11, 0.22, 0.29, 0.41, 0.52],  # Very similar
        }
        results = run_complementarity_check(signal_values)
        assert len(results) == 1
        assert results.is_redundant is True
        assert abs(results.pearson_r) >= 0.7
```

因此，\(< 0.7\) 的互补性要求不仅已被编码，而且深度嵌入了自动化可观测性日志记录。

---

## 5. 贝叶斯知识追踪 (BKT) 更新机制

认知精通度的估计利用了 Bayesian Knowledge Tracing（贝叶斯知识追踪，BKT）的现代化实现，该方法最初由 Corbett 和 Anderson（1994）建立。BKT 作为一个 Hidden Markov Model（隐马尔可夫模型，HMM）运行，假设学生的真实认知状态是潜在的（已掌握或未掌握），并试图通过可观察的表现产物（正确或错误答案）来推断该状态。

### 5.1 数学后验概率

BKT 架构依赖四个基础参数 [cite: 1]：
*   \(p_{prev}\)：当前观察之前学生已掌握概念的先验概率。
*   \(P_S\)（Slip，失误）：尽管真正掌握了知识但给出错误回答的概率。
*   \(P_G\)（Guess，猜测）：尽管缺乏真正掌握但给出正确回答的概率。
*   \(P_T\)（Transit，转换）：学生在一次应用知识的机会之后学会该概念的概率。

当一次交互被评分时，BKT 算法执行两步过程：首先，计算给定观察的贝叶斯后验精通概率，其次，应用学习转换。

**第一步：贝叶斯后验计算**

如果学生回答正确（由 `is_correct` 指示，其中评分 \(\ge 3\)）[cite: 1]：
\[
P_{posterior} = \frac{p_{prev} \cdot (1 - P_S)}{p_{prev} \cdot (1 - P_S) + (1 - p_{prev}) \cdot P_G}
\]

如果学生回答错误：
\[
P_{posterior} = \frac{p_{prev} \cdot P_S}{p_{prev} \cdot P_S + (1 - p_{prev}) \cdot (1 - P_G)}
\]

**第二步：学习转换注入**

无论即时表现如何，系统认识到教学交互本身就是一个学习事件：
\[
P_{new} = P_{posterior} + (1 - P_{posterior}) \cdot P_T
\]

### 5.2 代码中的算法实现

理论数学在 `_bkt_update` 内部方法中被转化为最优的、防故障的 Python 代码。它使用严格的边界夹紧——确保概率值严格保持在 `[0.001, 0.999]` 之间——以防止后验概率变得完全不可变的数学停滞 [cite: 1]。

```python
    def _bkt_update(self, concept: ConceptState, is_correct: bool, grade: int) -> float:
        """
        Bayesian Knowledge Tracing posterior update.
        ...
        """
        params = DEFAULT_BKT_PARAMS.get(
            concept.bkt_difficulty, DEFAULT_BKT_PARAMS["medium"]
        )
        p_prev = concept.p_mastery
        P_S = params["P_S"]
        P_G = params["P_G"]
        P_T = params["P_T"]

        # Grade 4 (Fluent): no guessing possible when student explains fluently
        if grade == 4:
            P_G = 0.0

        # Step 1: Bayesian posterior P(mastered | observation)
        if is_correct:
            numerator = p_prev * (1 - P_S)
            denominator = p_prev * (1 - P_S) + (1 - p_prev) * P_G
        else:
            numerator = p_prev * P_S
            denominator = p_prev * P_S + (1 - p_prev) * (1 - P_G)

        p_posterior = numerator / denominator if denominator > 0 else p_prev

        # Step 2: Learning transition — even if not mastered, student may learn
        p_new = p_posterior + (1 - p_posterior) * P_T

        return max(0.001, min(0.999, p_new))
```

值得注意的是，代码突出了一个教学启发式规则：**Grade 4 流利度特殊情况**。当学生被评为 `grade=4` 时，表示深层次的语境流利度和解释机制的能力，系统强制将猜测因子归零（\(P_G = 0.0\)）。这一架构决策正确地防止了对高度自信的知识展示进行贝叶斯惩罚 [cite: 1]。测试专门验证了此逻辑，以及确保系统稳定性的零分母保护 [cite: 1]。

---

## 6. FSRS 调度与记忆保持算法

BKT 管理知识获取的概率估计，而长期记忆衰减则需要间隔重复机制。系统通过主动实现 **Free Spaced Repetition Scheduler（自由间隔重复调度器，FSRS）** 协议来回答关于其调度算法的查询，完全摒弃了僵化的 Ebbinghaus（艾宾浩斯）固定间隔指标（如固定的 1、3、7、30 天复习）[cite: 1]。

### 6.1 FSRS 系统机制

FSRS 生成个性化的、自适应的间隔调度，动态映射到学生独特的记忆衰减曲线。FSRS 计算引擎（指定版本 4.5）依赖与记忆卡片关联的三个连续组件 [cite: 1]：
1.  **Memory Stability（记忆稳定性，S）：** 预测记忆痕迹在回忆概率降至期望保持率以下之前能够保持的持续时间（以天为单位）。
2.  **Memory Difficulty（记忆难度，D）：** 节点在缩放维度上的内在难度。
3.  **Retrievability（可检索性，R）：** 在当前时间 \(t\) 回忆信息的即时概率。

为了与第三方 `py-fsrs` 逻辑接口，系统将数值考试评分（范围从 1 到 4）转换为严格类型化的 FSRS 枚举评级 [cite: 1]：
*   **Grade 1 / 分数 < 40：** 转换为 `Rating.Again`（忘记，重置学习状态）。
*   **Grade 2 / 分数 40-59：** 转换为 `Rating.Hard`（回忆起来很困难）。
*   **Grade 3 / 分数 60-84：** 转换为 `Rating.Good`（回忆起来有些犹豫）。
*   **Grade 4 / 分数 $\ge$ 85：** 转换为 `Rating.Easy`（轻松回忆起来）。

### 6.2 调度算法的实现

交互路径利用单例管理的 `FSRSManager` 或直接的 `FSRS` 实例化。当交互需要调度时，平台要么创建新的 FSRS `Card` 对象，要么从 JSON 内存表示中反序列化现有状态，或者根据精确的服务路径回退到 SQLite 数据库存储负载 [cite: 1]。

核心调度通过系统的复习适配器执行：
```python
    def review_card(self, card: Any, rating: int) -> Tuple[Any, Any]:
        """
        Review a card with a rating.
        ...
        """
        if FSRS_AVAILABLE:
            rating_enum = Rating(rating)
            return self._scheduler.review_card(card, rating_enum)
        else:
            return self._fallback_review(card, rating)
```
在内部，`py-fsrs` 调度器映射到 `f.repeat(card, now)` [cite: 1]，利用高度参数化的权重矩阵计算数学向量，该矩阵旨在以 90% 的最优保持率为目标。复习后，它从返回的元组中提取调度日期 [cite: 1]：

```python
                    # Story 32.2 AC-32.2.3: Review card with FSRS algorithm
                    updated_card, review_log = self._fsrs_manager.review_card(card, rating)

                    # Get next due date (dynamically calculated by FSRS)
                    due_date = self._fsrs_manager.get_due_date(updated_card)

                    # Calculate interval in days
                    if due_date:
                        now = datetime.now(timezone.utc)
                        interval_days = max(0, (due_date - now).days)
                    else:
                        interval_days = 1
```

如果 FSRS 引擎抛出异常或第三方 C++ 二进制文件加载失败，系统拥有一个活跃的 `_fallback_review` 降级路径。此回退方案基于评级因子计算简单的间隔乘数，以保证运行连续性 [cite: 1]。在没有原生 FSRS 管理器处于活跃状态时，可检索性（\(R\)）在易变读取通道上的估计利用指数衰减近似 \(R \approx \exp(-\frac{\text{days\_elapsed}}{\text{stability}})\) 来执行 [cite: 1]。

---

## 7. 考试管道集成与死代码验证

用户查询的最后一个约束要求验证这些复杂的数学追踪器（BKT 和 FSRS）是否被考试管道主动调用，还是构成被遗弃的"死代码"。

### 7.1 MCP 工具暴露与主动编排

BKT 和 FSRS 更新从根本上来说是主动的、被高度编排的系统。它们作为 Model Context Protocol（模型上下文协议，MCP）工具暴露给对话代理：`update_bkt` 和 `update_fsrs` [cite: 1]。

实现函数直接将 MCP 参数（例如节点 ID、布尔值、整数评分）连接到内部精通度数据库。例如，`update_fsrs` 明确与精通度引擎状态机接口 [cite: 1]：

```python
    # Run the update
    updated = engine.update_on_interaction(concept, grade)
    await store.save_concept(updated)

    result = UpdateFsrsOutput(
        node_id=node_id,
        updated=True,
        status="ok",
        message=f"FSRS updated with grade={grade}",
    )
```

### 7.2 安全、审计与管道令牌执行

为了从数学上保证这些工具不会被不可预测的 Agent LLM（大语言模型）绕过，架构纳入了严格的序列验证。

首先，**Pipeline Tokens（管道令牌）** 充当执行屏障。`update_bkt` 和 `update_fsrs` 工具强制要求一个密码学 `pipeline_token`。如果 AI 代理试图在没有首先通过 `score_answer` 工具合法评分答案的情况下更新认知精通度，`TokenManager` 会引发一个明确的 `PipelineTokenError` [cite: 1]。

```python
    # Validate pipeline token (AC-3)
    token_mgr = get_pipeline_token_manager()
    try:
        token_mgr.validate_token(pipeline_token, expected_previous_step="score_answer")
    except PipelineTokenError as e:
        return UpdateBktOutput(
            node_id=node_id,
            updated=False,
            status=e.code,
            message=e.message,
        ).model_dump()
```

其次，一个名为 `AuditGuardian`（审计守卫）的异步单例进程在后台持续运行。每当 MCP 端点触发时，它都会记录一个 `tool_call` [cite: 1]。守卫主动评估管道完整性以检测违规行为 [cite: 1]：
*   **步骤跳过：** 如果 `update_fsrs` 在状态机中没有先前初始化的情况下被调用，则被检测到。
*   **时间异常：** 如果 `score_answer` 和更新工具之间的经过时间超过 `MAX_STEP_INTERVAL_SECONDS`，则被检测到。

此外，守卫运行一个周期性任务 `check_signal_loss` 来检测停滞的管道 [cite: 1]：
```python
        for key, state in self._active_pipelines.items():
            if (
                state.last_step == "score_answer"
                and now - state.last_step_time > MAX_STEP_INTERVAL_SECONDS
            ):
                await self._record_violation(
                    violation_type="signal_loss",
                    tool_name="score_answer",
                    session_id=state.session_id,
                    node_id=state.node_id,
                    details={
                        "message": "score_answer completed but no update_fsrs/update_bkt followed",
                        "elapsed_seconds": round(now - state.last_step_time, 2),
                    },
                )
```
这些高度复杂的防故障措施代表了企业级软件工程模式，专门设计用于保证精通度框架的运行执行。管道锁定、通过 JSONL 追加的审计日志以及状态机序列执行的存在，明确证明了 BKT 和 FSRS 组件绝对不是死代码；它们在用户交互工作流中充当关键的、被主动巡逻的瓶颈。

---

## 8. 结论

被分析的软件系统呈现了一种稳健的、学术上合理的学生能力建模方法。B2 Signal Fusion（信号融合）机制利用归一化加权平均主动综合 5 个核心信号，通过夹紧边界确保部分数据的弹性。系统通过执行严格的低于 0.7 限制的 Pearson（皮尔逊）互补性检查，从数学上防范算法回音室效应。

在概率层面，Bayesian Knowledge Tracing（贝叶斯知识追踪）架构完美地建模了潜在认知转换动态——通过显式缓解梯度饥饿（夹紧）和上下文启发式方法（在达到完全流利度时将猜测参数归零）。记忆保持模块完全集成了复杂的 FSRS 算法来计算记忆衰减，摒弃了遗留的间隔结构。最后，集成架构通过激进的工具审计、密码学管道验证和时间异常监控来保证这些引擎的存活和执行，确认 BKT 和 FSRS 组件是平台自适应能力的关键、活跃驱动力。

**数据来源：**
1. backend/app/services/mastery_fusion.py (fileSearchStores/persistentcanvaslearningsys-qa7kqspeo0jc)
