# Brainstorming Session: PRD 信号融合 + 响应时间深度探索

**Session:** PRD-Review New Tab — 定向深度探索
**Date:** 2026-03-15
**Context:** PRD 验证框架下对"10信号→5维 Beta-Bayesian 融合"和"响应时间作为核心信号"进行深度调研

---

## 调研方法

三路并行深度调研：

1. **代码库审查**（独立 Agent）— 搜索 10 信号和 5 维度的完整定义、现有代码实现状态
2. **学术论文/社区调研**（独立 Agent）— MIRT、PDT、ECD、BBN、Nature 2025、van der Linden 等
3. **Graphiti 历史决策汇总**（独立 Agent）— 搜集之前所有 session 的相关结论和待解问题

---

## 调研 1：10信号→5维 Beta-Bayesian 融合

### 发现：PRD 中的具体定义

PRD 描述："10 信号 → 5 维精通度，Per-Dimension Beta-Bayesian Evidence Accumulation"

**问题：PRD 和代码库中均未完整列出 10 个信号和 5 个维度的具体定义。**

代码库中可识别的信号源：
1. BKT p_mastery（贝叶斯知识追踪概率）
2. FSRS retrievability（可检索性/遗忘曲线）
3. override_value（显式覆盖）
4. self_assess_value（Canvas 色彩隐含自评）
5. fluent_count（流畅解释计数）
6. misconception（概念误解信号，Graphiti Bridge）
7. problem_trap（问题陷阱信号，Graphiti Bridge）
8. guided_thinking_correct（指导性思维正确信号）
9. interaction_count（交互总数）
10. false_mastery_flags / surprise_failures（虚假掌握/意外失败）

五维理解模型（来自 brainstorming）：
1. 概念误解 (Misconception)
2. 推理错误 (Reasoning Error)
3. 前置知识缺口 (Prerequisite Gap)
4. 理解深度 (Understanding Depth)
5. 元认知偏差 (Metacognitive Gap)

### ✅ 合理

| 方面 | 学术支撑 |
|------|---------|
| 多信号融合大方向 | 多源学生建模 > 单源，学术充分验证 |
| Beta-Bernoulli 共轭更新 | 教科书级数学，PDT 论文已用 Beta-DBN |
| 优雅降级到先验 | 数据稀疏时安全回退 |
| 五维精通度模型思路 | MIRT 60+ 年验证 |
| 之前 session 已确认降到 5-6 信号 | 与 Nature 2025 的 3-5 变量 plateau 吻合 |

### ❌ 不合理

| 问题 | 证据 |
|------|------|
| 10 信号过多 | Nature 2025：超过 3-5 变量边际递减；单用户 5-20 次交互无法校准 50 参数 |
| "Per-Dimension Beta-Bayesian Evidence Accumulation" 自创 | 学术文献中未找到，全球无开源实现 |
| Per-Dimension 独立融合 | MIRT 证明联合建模更优，布鲁姆维度天然层次依赖 |
| 信号冗余→过度自信 | 相关信号当独立证据 = "证据双重计数"，Beta 过度收窄 |
| 缺信号互补性验证 | PRD 提到条件但无验收标准 |

### 之前 session 已确认的 5-6 核心信号

| 信号 | 观察什么 | 互补性 |
|------|---------|--------|
| BKT 掌握概率 | 对/错历史轨迹 | 最基础追踪 |
| FSRS 可检索性 | 遗忘效应 | 时间维度，与 BKT 互补 |
| 考察表现 | 检验白板答题质量 | 最直接能力证据 |
| 校准差距 | 自以为懂 vs 实际表现 | 元认知，与前三独立 |
| 响应时间 | 答题速度 | 流畅度 ← **本次调研质疑此信号** |

### 建议：修改 PRD

1. "10信号" → "5-6核心信号"，列出具体列表
2. 标注 Per-Dimension 独立性为"数据稀疏约束下的工程简化"
3. 添加信号互补性验收标准
4. 添加融合净收益验收标准

---

## 调研 2：响应时间是否应作为核心信号

### 用户原始质疑

"响应时间有前端按钮控制吗？用户离开电脑怎么办？无限计时？"

### 深度调研结论

**6 大平台对比：仅 Area9 用响应时间做核心精通度信号（且必须搭配自信度自评）**

| 平台 | 用户规模 | 用 RT 判断掌握程度 |
|------|---------|-------------------|
| Khan Academy | 1.2亿+ | 不用 |
| IXL | 1400万+ | 不用 |
| ALEKS | 3000万+ | 不用（提供"我不知道"按钮） |
| Duolingo | 5亿+ | 间接用（仅学习间隔，非单题 RT） |
| Area9 | 3000万 | 用（必须搭配自信度评分） |
| Knewton | 已关闭 | 用学习材料时间，非答题时间 |

### 响应时间的 5 个核心缺陷

1. **用户离开电脑** — 计时器无限运行，数据失真
2. **快 ≠ 掌握** — 可能是 rapid guessing（学术大量研究）
3. **慢 ≠ 不掌握** — 可能是认真思考/焦虑/题型差异
4. **个体差异巨大** — 性格/阅读速度/打字速度
5. **题型不可比** — MCQ 3秒 vs 文本 3分钟 vs 代码 30分钟

### 推荐方案

**响应时间降级为辅助信号，自信度自评升级为核心信号：**

| 方面 | 响应时间（降级） | 自信度自评（升级） |
|------|----------------|------------------|
| 角色 | 辅助：回答有效性门控 + FSRS 难度调节 | 核心：直接输入精通度计算 |
| 前端 | 暂停按钮+标签页检测+空闲检测 | "确定/不确定/猜的"按钮组 |
| 学术 | van der Linden 2007: 有限信息增益 | Area9: 25年3000万用户验证 |
| 用户离开问题 | 需要复杂异常检测 | 天然免疫 |

### 前端需新增控件

| 控件 | 优先级 | 说明 |
|------|--------|------|
| 自信度按钮组 | MUST | 回答后点"确定/不确定/猜的" |
| 暂停按钮 | MUST | 检验白板中可暂停计时 |
| "我不知道"按钮 | SHOULD | 跳过，不记 RT |
| Tab 切换检测 | SHOULD | Page Visibility API 自动暂停 |
| 空闲检测 | NICE TO HAVE | 60秒无操作提示 |

---

## 待用户确认的方向

| # | 决策点 | 推荐方向 | 状态 |
|---|--------|---------|------|
| 1 | 10信号→5-6核心信号 | 降到 5-6（BKT+FSRS+考察+校准+自信度） | ⏳ 待确认 |
| 2 | 响应时间角色 | 从核心降为辅助 | ⏳ 待确认 |
| 3 | 自信度自评 | 替代响应时间成为第5核心信号 | ⏳ 待确认 |
| 4 | Per-Dimension 独立性标注 | 标注为"工程简化"非理论最优 | ⏳ 待确认 |
| 5 | 信号互补性验收标准 | 相关系数 < 0.7 | ⏳ 待确认 |

---

## 学术参考文献

- MIRT (Multidimensional Item Response Theory) — 60+ years of psychometric validation
- PDT (Performance Distribution Tracing) — Beta distributions in DBN, arxiv 2501.10050
- ECD (Evidence-Centered Design) — Mislevy's framework
- Nature 2025 — 3-5 variables plateau for fusion marginal returns
- van der Linden 2007 — Hierarchical model for RT + accuracy (Psychometrika)
- Pelanek 2023 — Survey: Leveraging Response Times in Learning Environments
- Area9 Lyceum — 30M+ users, 25 years, RT + confidence rating
- Khan Academy — "Measures knowledge, not time"
- ALEKS — Knowledge Space Theory + "I don't know" button
- Duolingo — Half-Life Regression (inter-session intervals only)
- pyBKT / catsim / EduStudio — Mature open-source implementations (none support multi-signal fusion)

---

## Graphiti 记录

本 session 已记录到 Graphiti (group_id: canvas-dev)：
- `[Session-Start] PRD-Review-续3 — 正式启动验证流程`
- `[Research] PRD验证-10信号融合深度探索结论`
- `[Research] 响应时间信号深度探索 — 降级为辅助信号，自信度自评替代`
