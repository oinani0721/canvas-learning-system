---
stepsCompleted: [1, 2, 3, 4]
inputDocuments: ['_bmad-output/planning-artifacts/prd.md', '.claude/agents/scoring-agent.md', 'backend/app/services/mastery_engine.py', 'backend/app/models/mastery_state.py']
session_topic: 'Calibration Tracking Deep Explore — PRD 验证中发现的 3 个缺口的成熟方案调研'
session_goals: '为 PRD 中 Calibration Tracking 的评分可靠性、校准阈值、Rubric 维度找到社区/学术验证的成熟方案'
selected_approach: 'ai-recommended'
techniques_used: ['Deep Explore (4路并行WebSearch)', 'Adversarial Code Review (独立Agent)', 'Graphiti Cross-Session Knowledge']
ideas_generated: ['三层评分保险机制', 'Area9 2x2置信度矩阵', '3维SOLO Rubric', '三阶段冷启动']
context_file: ''
session_active: false
workflow_completed: true
decision_review_count: 1
decision_review_status: 'PENDING'
code_review_rating: '需修复 (2 CRITICAL + 3 HIGH)'
web_searches: 14
academic_sources: 25+
---

# Calibration Tracking Deep Explore — 调研报告

**Facilitator:** ROG
**Date:** 2026-03-15
**来源 Session:** PRD-Review-Validation (New Tab)
**技法组合:** 4 路并行 Deep Explore (WebSearch) + 独立 Agent 对抗性代码审查 + Graphiti 知识检索

---

## 一、Session 概要

**背景:** 在 PRD Review 过程中，用户询问 Calibration Tracking 的评分标准制定依据。经调查发现 3 个验证缺口：
1. AI 评分可靠性验证方案不完整
2. 15% 偏差阈值和 5 条冷启动无学术依据
3. PRD "3 维 rubric" 与代码实际 "4 维" 不一致

**目标:** 通过社区调研 + 成熟论文 + Graphiti 遗漏检查 + 代码审查，为每个缺口找到成熟解决方案。

**方法:** 4 路并行 Agent 调研（14 次 WebSearch，25+ 学术来源）+ 1 路独立代码审查

---

## 二、调研路线 1 — AI 评分可靠性验证方案

### 2.1 核心发现

**行业标准（ETS，25 年实践）：**
- QWK (Quadratic Weighted Kappa) >= 0.70 且 Pearson r >= 0.70
- 降级标准：AI-人类一致性不能比人类-人类一致性低超过 0.10
- 单用 Pearson r 不够——它只衡量相关性，不反映系统性偏差

**LLM 实际表现：**
- 变异极大：同一模型在不同场景下 r=0.38 到 r=0.95
- GPT-4 作文评分最佳条件 QWK=0.99，一般条件 QWK=0.68
- LLM 自我偏好偏差已被 NeurIPS 2024 确认

### 2.2 推荐方案：三层评分保险机制

| 层级 | 方案 | 原理 | 成本 | 来源 |
|------|------|------|------|------|
| **第 1 层** | Self-Consistency（3 次采样多数投票） | 同一道题让 AI 打 3 遍，取多数一致结果；不一致则标记"低置信度" | +2 次 API 调用 | Self-Consistency 是 2023 年以来最广泛验证的 LLM 可靠性方法 |
| **第 2 层** | Rubric 分解评分 | 按评分标准逐项给分再汇总，提高可解释性 | 不增加成本，改 prompt | AutoSCORE (2025)、Autorubric (2025) |
| **第 3 层** | 双模型交叉验证 | 重要考察时用两个不同 LLM 分别打分，分歧超阈值标记低置信度 | +1 次不同模型 API 调用 | Dual-Model Validation (EmergentMind)、K-12 Multi-LLM (arXiv:2602.13243) |

**适配建议：**
- 日常练习：第 1+2 层即可
- 阶段性考察：加第 3 层
- 持续监控 self-consistency rate 作为系统健康指标

### 2.3 学术来源

- ETS e-rater 操作标准 (25 年实践)
- ACL BEA 2025: Advances in Auto-Grading with LLMs
- NeurIPS 2024: Self-Preference Bias in LLM-as-a-Judge
- BJET 2025 (Yavuz): Fine-tuned ChatGPT ICC=0.972
- ACM L@S 2024: GPT-4 Short Answer Grading Pearson r=0.87
- Preprints.org 2025: Self-Consistency for Reliable LLM Grading
- AutoSCORE 2025: Multi-Agent LLM Scoring
- arXiv 2602.13243: K-12 Multi-LLM Evaluation

---

## 三、调研路线 2 — 校准阈值与冷启动学术依据

### 3.1 核心发现

**"15% 偏差收敛"——无学术依据：**
- 学术界没有将 15% 作为校准偏差阈值的标准
- 教育心理学更关注趋势方向（偏差是否在改善）而非某个绝对值
- 如果一定要设阈值，学术上更接近 Bias <= 0.10（10%），但也非硬性标准

**"5 条冷启动"——远远不够：**
- Gamma 相关系数需要至少 20 道中等难度题目才可靠 (Schraw 1995; Fleming & Lau 2014)
- 少于 10 道的校准指数被文献明确标为"不稳定"
- ECE 分桶方法总体至少需要 50+ 数据点

**Area9 Lyceum 模型（3000 万用户验证）：**
- 核心机制：2x2 置信度矩阵（答案正误 × 信心高低）
- 四种知识状态：有意识胜任、无意识不胜任（最危险）、无意识胜任、有意识不胜任
- "Teaching by Asking"——先提问再学习
- 每题必须选择置信度水平

**Dunning-Kruger 效应争议：**
- Gignac & Zajenkowski (2020) 和 Jansen et al. (2021) 论证 DK 效应"大部分是统计伪影"
- 不建议使用 DK 标签，而是追踪校准偏差方向

### 3.2 推荐方案

| 设计决策 | PRD 现在写的 | 推荐改为 | 依据 |
|---------|-------------|---------|------|
| 校准阈值 | 偏差收敛至 <=15% | 不设固定阈值，追踪偏差趋势是否持续缩小 | 学术界无统一阈值标准 |
| 冷启动门槛 | 5 条配对后启动 | <10 条仅收集不展示、10-20 条"初步趋势"、20+ 条"可靠评估" | Fleming & Lau 2014; Schraw 1995 |
| 核心模型 | 简单差值（自评-实际） | Area9 2x2 置信度矩阵（答案正误 × 信心高低） | Area9 3000 万用户验证 |
| DK 效应 | 基于 Dunning-Kruger | 不使用 DK 标签，追踪偏差方向+四种知识状态 | DK 有统计伪影争议 |
| 偏差计算 | 未明确 | 签名偏差（方向）+ 绝对偏差（大小）双指标 | 教育心理学文献最广泛组合 |

### 3.3 学术来源

- Fleming & Lau (2014): How to measure metacognition (PMC)
- Schraw (1995): Measures of metacognitive monitoring
- Gignac & Zajenkowski (2020): DK effect is mostly statistical artefact (Intelligence)
- Jansen et al. (2021): Rational model of DK effect (Nature Human Behaviour)
- Area9 Lyceum: Four-dimensional personalized learning (官方文档)
- Confido Institute: Calibration and calibration curves
- PMC 2012: Calibration Research - Where Do We Go from Here?

---

## 四、调研路线 3 — Rubric 维度设计最佳实践

### 4.1 核心发现

**3-4 维是 LLM 自动评分的甜蜜点：**
- 2025 年研究对比发现 4 个 LLM 中 3 个在简化 rubric 下效果 ≈ 详细 rubric，但 token 消耗大降
- 维度太多增加 prompt 复杂度，降低评分一致性

**SOLO Taxonomy 最适合评估"理解深度"：**
- Prestructural → Unistructural → Multistructural → Relational → Extended Abstract
- 直接可转化为评分 rubric (ERIC 2016 验证)
- 与 Bloom 相比，SOLO 更关注"理解有多连贯"，Bloom 更关注"能做什么操作"

**ICAP 框架（Chi & Wylie 2014）：**
- 自我解释属于 Constructive 活动——评分应区分"复述"和"真正的自我解释"
- Passive → Active → Constructive → Interactive

**等权 vs 加权：**
- Moskal & Leydens (2000)：加权与不加权在学生表现区分上差异极小
- 推荐：等权起步，收集 100+ 样本后可统计验证

### 4.2 推荐方案：3 维分析式 Rubric（等权）

| 维度 | 评估什么 | 理论基础 | 评分等级 (0-3) |
|------|---------|---------|--------------|
| **Correctness（正确性）** | 知识内容是否准确 | Bloom: Remember+Understand | 0=严重错误, 1=部分正确, 2=基本正确, 3=完全正确 |
| **Completeness（完整性）** | 是否覆盖关键知识组件 | SOLO: Multistructural | 0=严重遗漏, 1=<50%, 2=大部分, 3=全面覆盖 |
| **Depth（深度）** | 理解的结构复杂度 | SOLO: Relational→Extended Abstract, ICAP: Constructive | 0=无解释, 1=复述原文, 2=建立联系, 3=推理迁移 |

**替代现有 4 维（准确性+形象性+完整性+原创性）的理由：**
- "形象性"在学术上缺乏支撑——不是评估理解深度的有效维度
- "原创性"容易与"深度"混淆——SOLO 的 Relational/Extended Abstract 层级已涵盖
- 3 维更清晰、LLM prompt 更简洁、评分一致性更高

### 4.3 学术来源

- Do We Need a Detailed Rubric for AES using LLMs? (arXiv 2025)
- AutoSCORE: Multi-Agent LLM Scoring (arXiv 2025)
- LLM-Rubric: Microsoft ACL 2024
- NGSS 3D Rubric (Kaldaras et al., Frontiers 2022): kappa 0.82-0.97
- ICAP Framework (Chi & Wylie 2014)
- SOLO Taxonomy (Biggs & Collis)
- Transforming Taxonomies into Rubrics (ERIC 2016)
- Moskal & Leydens (2000): Scoring Rubric Development

---

## 五、代码审查结果（独立 Agent 对抗性审查）

### 5.1 总体评级：需修复 (NEEDS FIX)

核心 BKT+FSRS 引擎质量较高可复用，但存在多处管道断裂和 PRD 不一致。

### 5.2 问题清单

#### CRITICAL (2 项)

| # | 问题 | 涉及文件 | 影响 |
|---|------|---------|------|
| C1 | **Calibration Tracking 完全未实现** — PRD 明确要求但代码为零，无偏差计算/配对记录/趋势分析 | 整个后端代码库 | PRD 核心功能缺失 |
| C2 | **surprise_failures 计数器永远为 0** — false_mastery_risk() 函数 40% 权重的 Factor 1 完全失效 | mastery_engine.py:370-393, mastery_state.py:110 | 无法检测"以为会了其实不会" |

#### HIGH (3 项)

| # | 问题 | 涉及文件 | 影响 |
|---|------|---------|------|
| H1 | **PRD "3 维 rubric" vs 代码 4 维不一致** | prd.md:416/656, scoring-agent.md, ScoringCheckpointService.ts:62-66 | 文档与实现矛盾 |
| H2 | **三套独立评分-to-mastery 管道互不协调** — agent_service / review_service / verification_service 各自为政，review_service 有独立 FSRS 状态不与 MasteryEngine 同步 | agent_service.py:3651-3669, review_service.py:840-864, verification_service.py:690-746 | 同一概念两份不同步的 FSRS 状态 |
| H3 | **self-assess 只存最新值（覆盖式），无历史追踪** | mastery_engine.py:361-367, mastery_state.py:105-106 | 无法实现配对追踪和趋势分析 |

#### MEDIUM (3 项)

| # | 问题 | 影响 |
|---|------|------|
| M1 | BKT 的 P_L0 参数定义但未使用 | easy/hard 概念初始精通度不准 |
| M2 | SELF_ASSESS_COLOR_MAP 颜色含义注释前后端不一致 | 维护困惑 |
| M3 | find_concept_by_name 使用 CONTAINS 模糊匹配 | 短名称概念可能误匹配 |

### 5.3 数据流断裂分析

```
PRD 定义的完整链路：
自评 → 记录 self_report → 考察评分 → 记录 actual → 配对(5+条) → 偏差计算 → 趋势 → 可视化

实际代码链路：
自评 → 只存最新值（覆盖式，无历史）
考察评分 → BKT+FSRS 更新（只有 agent_service 路径打通）
配对计算 → ❌ 不存在
偏差追踪 → ❌ 不存在
趋势分析 → ❌ 不存在

断裂点：自评值和考察评分在 effective_proficiency() 中被混合加权，
但从未独立保存做配对比较。系统能算混合精通度，但无法告诉学生
"你以为自己 90 分但实际只有 60 分"。
```

---

## 六、PRD 修正建议汇总（Decision-Review PENDING）

| # | PRD 现在写的 | 建议改为 | 学术/产业依据 |
|---|-------------|---------|-------------|
| 1 | "Pearson > 0.7 验证 AI 评分" (第 93 行) | 三层保险机制：Self-Consistency + Rubric 分解 + 双模型交叉验证 | ETS 25 年标准 + NeurIPS 2024 + AutoSCORE 2025 |
| 2 | "偏差收敛至 ≤15%，5 条启动" (第 93、121 行) | 追踪趋势方向 + 10 条初步/20 条可靠 + Area9 2x2 矩阵 | Fleming & Lau 2014 + Area9 3000 万用户 |
| 3 | "3 维 rubric" (第 416、656 行) 但代码 4 维 | 统一 3 维：正确性 + 完整性 + 深度（SOLO），等权 0-3 分 | SOLO/ICAP/AutoSCORE 2025 |
| 4 | Calibration Tracking "已设计" | 明确标注"代码待建"，参考 Area9 2x2 模型 | 代码审查确认零实现 |

**验证状态：** PENDING — 由独立验证 session 制定验收标准并测试

---

## 七、给主 Tab PRD Review 的衔接说明

本文档的 4 项修正建议可直接作为 PRD 验证报告 (`prd-validation-report.md`) 的 findings 输入。

**主 Tab 下一步：**
1. 加载本文档作为额外参考文档
2. 继续 step-v-01-discovery（选 C 进入 Format Detection）
3. 在验证过程中将这 4 项 finding 写入验证报告的对应章节
4. 用户确认后，修正 PRD 文档本体

**Graphiti 记录：**
- `[Session-Start] PRD-Review-Validation 正式开始验证流程`
- `[Progress] PRD-Review Step V-01 Discovery 完成`
- `[Research] PRD-Review 发现 Calibration Tracking 三个验证缺口`
- `[Research-Tech] AI 评分可靠性调研完成：ETS 标准 QWK>=0.70 + 三层保障方案`
- `[Research-Tech] 校准阈值调研：15% 无依据、5 条太少需 20+、推荐 Area9 2x2 矩阵`
- `[Research-Tech] Rubric 维度调研：推荐 3 维分析式（正确性+完整性+深度）`
- `[Code-Review] 评分/校准代码审查：需修复，2 CRITICAL + 3 HIGH`
- `[Decision-Review] PRD Calibration Tracking 4 项修正方案 — 待验证`
