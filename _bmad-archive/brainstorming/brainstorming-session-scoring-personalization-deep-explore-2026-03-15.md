# Brainstorming Session: LLM 评分个性化——如何让分数匹配用户主观感受

**日期**：2026-03-15
**Session**：PRD-Review New Tab（评分个性化定向 Deep Explore）
**触发**：用户在审阅 PRD 时提出"LLM 3 维 rubric 评分能否真正匹配个人主观感受"的核心担忧
**方法**：社区调研 + 成熟论文 + Graphiti 历史检索 + 生产系统验证

---

## 用户核心担忧

> "如何实现评分符合实际也是一个问题，真正可以符合我的个人主观感受"

用户截图了评分示例（准确性 85 / 完整性 60 / 深度 70 = 总分 75），质疑：纸面上的 3 维 rubric 机制是否真的能让用户感觉"这个分数就是我的真实水平"。

---

## PRD 现有设计

PRD 中已有 3 道防线：
1. **3 维 rubric**（准确性/完整性/深度）— FR-EXAM-04
2. **Calibration Tracking**（自报告 vs 实际表现偏差追踪）— FR-MAST-05
3. **自一致性检查** — 评分公正性策略

**Graphiti 已有结论**：
- LLM-as-Judge binary grading 准确率 >80%
- 社区推荐阈值 0.5-0.7（0.85 过严）
- GPT-4 + few-shot + CoT 达到 >80% 人机一致率
- 校准反馈依赖 AI 评分可靠性前提（AC5.1 > 0.7）
- Phase 0 人工 rubric 评估不可跳过

---

## 深度调研发现：6 类成熟方案

### 方案 1：评分量表优化（0-5 整数量表）

| 维度 | 内容 |
|------|------|
| **来源** | *Grading Scale Impact on LLM-as-a-Judge* (2026) |
| **核心** | 0-5 整数量表的人机评分一致性最高；0-100 分太细导致 AI 乱分，binary 太粗信息不够 |
| **成熟度** | 研究验证（2026 论文） |
| **适配** | PRD 当前未指定量表范围，建议改为每维度 0-5 |

### 方案 2：知识点级评分指南（Grading Notes）

| 维度 | 内容 |
|------|------|
| **来源** | Databricks 生产系统（1 年+使用） |
| **核心** | 每个知识点附一条"评分重点说明"，告诉 AI 此知识点的关键概念是什么 |
| **证据** | Llama3 达 **96.3% 人机一致性**（减少 85% 分歧）；GPT-4o 达 93.1%（67.5% 减少） |
| **成熟度** | **生产验证**（Databricks 1 年+） |
| **适配** | ★★★★★ — 用户的 Tips 和 Edge 理由天然就是 grading notes，零额外成本 |

### 方案 3：用户反馈校准循环

| 维度 | 内容 |
|------|------|
| **来源** | LangChain Align Evals（商用产品） |
| **核心** | 评分后用户可标记"偏高/偏低/准确"→ 纠正积累为 few-shot 校准样本 → AI 逐渐学会用户标准 |
| **证据** | LangChain 商用部署；论文 *Few-shot Personalization of LLMs* (2024) 证实"纠错信号"是最有价值的校准数据 |
| **成熟度** | **生产验证**（LangChain 商用） |
| **适配** | ★★★★★ — 完美匹配"越用越懂你"核心理念 |

### 方案 4：答前自估元认知校准

| 维度 | 内容 |
|------|------|
| **来源** | Brainscape（千万用户）、Area9 Lyceum（20 年+研究） |
| **核心** | 答题前先问"你觉得自己能答对吗？" → 对比 AI 评分 → 校准元认知偏差 |
| **成熟度** | **生产验证**（20 年+历史） |
| **适配** | ★★★★★ — PRD 已有 Calibration Tracking，这正是其具体实现方式 |

### 方案 5：低信心标记（Trust or Escalate）

| 维度 | 内容 |
|------|------|
| **来源** | *Trust or Escalate* (ICLR 2025 Oral，顶会前 1.8%) |
| **核心** | AI 不确定的评分不偷偷给出，明确标记"我不太确定"，邀请用户复核 |
| **证据** | 用 Mistral-7B 就能保证 >80% 人机一致性 + 80% 覆盖率 |
| **成熟度** | **顶会验证**（ICLR 2025 Oral） |
| **适配** | ★★★★ — 增强 PRD 已有的"自一致性检查" |

### 方案 6：拆步骤打分（AutoSCORE）

| 维度 | 内容 |
|------|------|
| **来源** | *AutoSCORE* (2025) |
| **核心** | 双 Agent：Agent1 提取"用户到底说了什么" → Agent2 对照标准逐条打分。模拟人类阅卷过程 |
| **证据** | GPT-4o、LLaMA-3.1-8B/70B 多数据集验证提升 |
| **成熟度** | 研究验证（2025） |
| **适配** | ★★★★ — 提升准确性和可解释性 |

---

## 补充发现：生产系统参考

| 系统 | 评分方案 | 关键数据 |
|------|---------|---------|
| **Khan Academy** | AI 按 rubric 逐 turn 评分 + 合成响应预验证 | 与人类评分者"良好对齐" |
| **Coursera** | AI + rubric + 4 步评估框架 | 30 万份评分；97% 学生偏好 AI 评分 |
| **Duolingo** | IRT 持续校准（联合估计用户能力 + 题目难度） | 数亿用户 |
| **Area9 Lyceum** | 元认知校准 + 掌握度自适应 | 20 年+ 研究 |

### 开源工具

| 工具 | 用途 | 与我们的关系 |
|------|------|-------------|
| **Microsoft LLM-Rubric** (ACL 2024) | 多维度校准评估 + 用户特定参数 | 直接匹配架构 |
| **Prometheus 2** (EMNLP 2024) | 开源 rubric 评估模型，7B 可本地部署 | Pearson 0.897 |
| **DeepEval** | G-Eval 自定义指标 | 已在 Graphiti 中确认为最佳评估框架 |

---

## 推荐方案：3 层评分进化体系

### 第 1 层：基础可靠性（让 AI 打分更靠谱）

- 评分量表改为 **0-5 整数/维度**（人机一致性最高）
- 拆步骤打分：先提取→再对照标准逐条评分
- 对应 PRD 改动：FR-EXAM-04 细化量表规格

### 第 2 层：个性化校准（让评分"越来越懂你"）

- **知识点评分指南**：复用用户 Tips/Edge 理由作为 grading notes（零额外成本）
- **用户反馈校准**：评分后"偏高/偏低/准确"按钮 → few-shot 积累（新增 FR）
- **答前自估**：Calibration Tracking 的具体实现（细化 FR-MAST-05）

### 第 3 层：安全网（防止不准的分偷偷给出）

- **低信心标记**：AI 不确定时明确告知用户（增强自一致性检查）
- 高方差评分触发多次评估或用户复核

---

## 与 PRD 的关系

| 类别 | 具体项 |
|------|-------|
| **已有，需优化** | 3 维 rubric（量表改 0-5）、Calibration Tracking（加答前自估实现）、自一致性（增强为低信心标记） |
| **需新增** | 用户反馈校准循环（"偏高/偏低"按钮）、知识点评分指南（Tips 复用为 grading notes） |
| **不需改** | 评分流程整体架构、Beta-Bayesian 融合、3 维 rubric 维度选择 |

---

## 关键论文和来源

1. *Grading Scale Impact on LLM-as-a-Judge* (2026) — arxiv:2601.03444
2. *LLM-Rubric: Multidimensional Calibrated Approach* (ACL 2024) — arxiv:2501.00274
3. *RULERS: Locked Rubrics + Evidence-Anchored Scoring* (2026) — arxiv:2601.08654
4. *Rubric-Conditioned LLM Grading* (2025) — arxiv:2601.08843
5. *G-Eval: NLG Evaluation using GPT-4* (EMNLP 2023) — arxiv:2303.16634 (492+ 引用)
6. *Prometheus 2* (EMNLP 2024) — arxiv:2405.01535 (Pearson 0.897)
7. *Trust or Escalate* (ICLR 2025 Oral) — arxiv:2407.18370
8. *Human-AI Collaborative Essay Scoring* (LAK 2025) — arxiv:2401.06431
9. *AutoSCORE* (2025) — arxiv:2509.21910
10. *PersonalLLM* (ICLR 2025) — proceedings.iclr.cc
11. *Few-shot Personalization of LLMs* (2024) — arxiv:2406.18678
12. *Evaluating Consistency of LLM Evaluators* (COLING 2025) — arxiv:2412.00543
13. LangChain Align Evals — blog.langchain.com
14. Databricks Grading Notes — databricks.com/blog
15. Khan Academy AI Assessment — blog.khanacademy.org
16. Coursera AI Grading — blog.coursera.org

---

## 状态

- **用户确认**：待确认方向
- **下一步**：用户确认后更新 PRD 评分相关 FR/NFR，补充新增 FR
