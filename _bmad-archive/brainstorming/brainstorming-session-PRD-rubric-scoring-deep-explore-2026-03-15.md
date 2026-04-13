---
stepsCompleted: [1, 2, 3]
inputDocuments: ['_bmad-output/planning-artifacts/prd.md']
session_topic: 'PRD Review — Rubric 评分系统设计 Deep Explore'
session_goals: '验证 PRD 中 3维 rubric 评分设计的学术依据、识别错误分类缺口、调研行业最佳实践、推荐改进方案'
selected_approach: 'deep-explore-with-adversarial-review'
techniques_used: ['2-agent-parallel-deep-explore', 'adversarial-code-review', 'community-research', 'prd-gap-analysis', 'deep-clarification']
ideas_generated: ['4-dimension-rubric', '4-point-scale', 'two-layer-separation', 'SOLO-anchoring', 'AutoSCORE-two-stage', 'error-type-classification']
context_file: '_bmad-output/planning-artifacts/prd.md'
technique_execution_complete: true
session_active: false
workflow_completed: false
decision_status: '推荐方案已提出，待用户确认'
---

# Brainstorming Session Results

**Facilitator:** ROG
**Date:** 2026-03-15
**Session Type:** PRD Review New Tab — Rubric 评分系统 Deep Explore

## Session Overview

**Topic:** PRD 中 AI 评分 Rubric 维度设计验证 + 错误分类策略缺口分析

**Goals:**
1. 验证 PRD 中 3 维 rubric（准确性/完整性/深度）是否有学术依据
2. 识别 PRD 中"错误归档 → 出题利用"链条中的缺失环节
3. 审查现有评分代码的实际状态（mock vs 真实）
4. 基于社区/论文调研推荐改进方案

**来源 Session:** PRD-Review-Validation（主 Tab 的 BMAD validate-prd Step 1 Discovery 阶段分支出来的深度调研）

---

## 发现 1：PRD 缺口 — 错误分类与差异化补救策略未定义

### 问题

PRD 当前设计链条：`错误归档(FR-CONV-06) → 用历史错误精准出题(FR-EXAM-03)`

**缺失环节**：归档后，系统没有对错误进行分类，也没有基于分类采取不同的补救策略。

### 用户识别的 4 种错误类型

| 错误类型 | 用户体感 | 应对策略 |
|---------|---------|---------|
| **破题出问题** | "根本没读懂题在问啥" | 引导重新理解题意，提供更简单的类似题对比 |
| **推理逻辑谬误** | "知识点懂，但推到某步歪了" | 精确定位断点，用反例证伪 |
| **知识点不理解** | "这个概念根本不会" | 退回前置概念，调用 /四层解释 或 /口语化解释 重教 |
| **似懂非懂** | "觉得懂了但深问答不出" | 出变式题/迁移题，追问边界条件 |

### 影响

- 与核心成功标志"系统越来越懂你"直接矛盾——"懂你" ≠ 记住你犯过什么错，而是知道**为什么**犯这个错并用对的方式帮你
- 影响 FR-CONV-06（需扩展：不仅归档还要分类）、FR-EXAM-03（需扩展：根据错误类型选不同考察策略）
- 可能需要新增 FR

### Graphiti 记录

- `[Research] PRD缺口发现——错误分类与差异化补救策略未定义`

---

## 发现 2：PRD 缺口 — 3 维 Rubric 评分维度未经学术验证

### 问题

PRD 中 FR-EXAM-04 定义了"3 维 rubric"用于评分，截图示例为 `准确性 85 / 完整性 60 / 深度 70`。

经 Graphiti 搜索确认：Session-B 只推荐了"holistic → rubric-based"的方向升级，但 **3 个维度的选择没有任何社区调研或论文支撑**。

### 严重性

**高** — rubric 是整个精通度系统的数据输入源。维度不对 → BKT/FSRS/Beta-Bayesian 融合全部建立在错误信号上。

### Graphiti 记录

- `[Research] PRD缺口——3维rubric评分维度未经deep explore验证`

---

## Deep Explore 执行：双 Agent 并行调研

### Agent 1：社区/论文调研（16 篇论文 + 产品实践）

**调研覆盖**：AutoSCORE (2025), RULERS (2025/2026), LLM-Rubric (ACL 2024), FLASK (ICLR 2024), CheckEval (EMNLP 2025), Autorubric (2026), CARO (2026), MRBench (NAACL 2025), PEARL (2025), Grade Like a Human (2024), RubricBench (2026), LLM-Driven Algebraic Assessment (2025), Reflective Prompt Engineering (2025), Duolingo DET, Khan Academy/Khanmigo, Coursera AI Grading

**核心结论**：

| 问题 | 结论 | 论文依据 |
|------|------|---------|
| "深度"是否好维度？ | **不好** — 学术文献中极少独立出现，与 Completeness 重叠，缺乏行为锚定 | FLASK, SOLO 文献 |
| 缺什么维度？ | **推理质量 (Reasoning Quality)** — 几乎所有框架都包含 | FLASK, CheckEval, MRBench |
| 用什么量表？ | **4-point (0-3)** — LLM 连续分数校准极差，离散化可靠 | Autorubric (2026), LLM-Rubric (ACL 2024) |
| SOLO 怎么用？ | **不作维度，作量表锚定** — 定义每个分值长什么样 | SOLO 教育文献, RULERS |
| 打分和找错分开？ | **必须分开** — 混合会导致"规则稀释" | CARO (2026), AutoSCORE |
| Rubric 怎么执行？ | **两阶段：先找证据再打分** | AutoSCORE (2025) |
| Rubric 谁设计？ | **必须人工设计**，LLM 自动生成质量差 | RubricBench (2026) |

### Agent 2：代码对抗性审查（13 个评分相关模块）

**审查范围**：`src/api/routers/agents.py`, `src/api/models/agent.py`, `backend/app/models/schemas.py`, `backend/app/api/v1/endpoints/agents.py`, `backend/app/services/agent_service.py`, `.claude/agents/scoring-agent.md`, `backend/app/services/verification_service.py`, `canvas-progress-tracker/.../ScoringCheckpointService.ts`, `canvas-progress-tracker/.../ScoringResultPanel.ts`, `src/memory/temporal/fsrs_manager.py`, `tests/bdd/test_scoring_agent.py`, `tests/contract/test_schema_validation.py`, `canvas-progress-tracker/.../api/types.ts`

**核心发现**：

| 发现 | 严重性 | 详情 |
|------|--------|------|
| PRD 3维 vs 代码 4维 不匹配 | HIGH | PRD: 准确性/完整性/深度；代码: accuracy/imagery/completeness/originality |
| 两套不兼容 NodeScore schema | HIGH | `src/` 用 0-10/0-40，`backend/` 用 0-25/0-100 |
| ⛔ 前端 scale mismatch bug | CRITICAL | `ScoringCheckpointService.ts` 按旧 0-40 制乘 2.5 → 后端 85 分变 212 分 |
| ⛔ Score edge case bug | CRITICAL | `agent_service.py` 对 ≤1.0 分数乘 100 → 1分变100分 |
| `src/api/agents.py` 评分 | DEAD CODE | 100% MOCK（硬编码 accuracy=8.0 等） |
| BDD 测试只测 mock | NEEDS FIX | 不测真实评分行为 |
| scoring-agent.md prompt | GOOD | 4维设计良好，有 self-reflection |

**总体评级**：60% 可用 / 20% 需修复 / 20% 需重写

### Graphiti 记录

- `[Code-Review] 评分系统代码审查——4维实现vs PRD 3维 + 2个严重bug`
- `[Research-Tech] Rubric评分维度deep explore——16篇论文+产品调研完整结论`

---

## 推荐方案（待用户确认）

### Layer 1：质量评分 — 4 维度 x 4-point (0-3)

| 维度 | 评估什么 | 对应错误类型 | SOLO 锚定 |
|------|---------|------------|----------|
| **Conceptual Accuracy（概念准确）** | 核心概念对不对 | 知识点不理解 | 0=概念错误, 1=部分正确有关键错误, 2=基本正确轻微不精确, 3=完全正确 |
| **Reasoning Quality（推理质量）** | 推理链有没有逻辑跳跃 | 推理逻辑谬误 | 0=无推理或逻辑完全错, 1=有逻辑跳跃/谬误, 2=基本合理轻微缺口, 3=完整严谨 |
| **Completeness（知识覆盖）** | 该说的点都说到了吗 | 破题出问题 | 0=遗漏所有要素, 1=仅覆盖1个, 2=大部分覆盖, 3=全部覆盖 |
| **Integration（知识整合）** | 把相关概念串起来了吗 | 似懂非懂 | 0=孤立陈述, 1=提到关系未解释, 2=解释部分关联, 3=整合为连贯整体 |

### Layer 2：错误诊断（分类任务，非评分）

| 字段 | 类型 | 取值 |
|------|------|------|
| error_type | enum | `no_error` / `framing_error` / `reasoning_fallacy` / `concept_gap` / `superficial_understanding` |
| error_description | text | 具体错误描述 |
| confidence | enum | `high` / `medium` / `low` |

### 评分执行方式

```
Step 1: Evidence Extraction (AutoSCORE 风格)
  → 从学生回答中提取与各维度相关的证据

Step 2: Per-Criterion Atomic Scoring (RULERS 风格)
  → 对每个维度独立评分（4次独立判断）

Step 3: Error Diagnosis (独立任务)
  → 基于证据分类错误类型
```

### 与下游系统对接

| 下游系统 | 输入方式 |
|---------|---------|
| BKT | 4 维平均 ≥ 2.0 → correct, < 2.0 → incorrect |
| FSRS | 4 维分数映射到 Again/Hard/Good/Easy |
| Beta-Bayesian | 各维度分数直接作为 evidence 输入 |
| 教学策略选择器 | Layer 2 error_type 驱动策略选择 |

### 设计依据汇总

| 设计决策 | 学术支撑 |
|---------|---------|
| 4 维度（非 3/12） | FLASK 12维太多, 代数评估 3维验证可行, 4维平衡精简与信息量 |
| Integration 替代 Depth | SOLO 文献 + FLASK Insightfulness 定义 |
| 增加 Reasoning Quality | FLASK(Logical Correctness), CheckEval, MRBench |
| 4-point 量表 | LLM-Rubric(1-4验证) + Autorubric(离散化推荐) + 教育学(偶数避免中间聚集) |
| SOLO 锚定 | SOLO 教育文献 + RULERS 行为锚定原则 |
| 两层分离 | AutoSCORE(两阶段) + CARO(规则稀释警告) + MRBench(维度独立) |
| 人工设计 rubric | RubricBench(模型生成差距大) |

### 三方对比

| | PRD 当前 | 代码当前 | 论文推荐 |
|--|---------|----------|----------|
| 维度 | 准确性/完整性/深度 | accuracy/imagery/completeness/originality | **概念准确/推理质量/知识覆盖/知识整合** |
| 量表 | 未定义 | 0-25 每维, 0-100 总分 | **0-3 每维, 0-12 总分** |
| 错误诊断 | 未提及 | 未实现 | **独立 Layer 2** |
| 评分方式 | 一次性 | 一次性 | **两阶段（证据提取→打分）** |

### Graphiti 记录

- `[Decision] Rubric评分设计——推荐4维4分制+两层分离+SOLO锚定+AutoSCORE两阶段`
- `[Decision-Review] Rubric评分4维4分制+两层分离设计 — 待验证 (PENDING)`

---

## 代码层面需修复的紧急问题

| Bug | 文件 | 严重性 | 影响 |
|-----|------|--------|------|
| 前端 scale 乘 2.5 | `ScoringCheckpointService.ts:578-580` | CRITICAL | 后端 85 分 → 前端 212 分 |
| Score ≤1.0 乘 100 | `agent_service.py:3618-3619` | CRITICAL | 真实 1 分 → 100 分（满分） |
| 两套 NodeScore schema | `src/api/models/agent.py` vs `backend/app/models/schemas.py` | HIGH | 数据格式不兼容 |
| BDD 测试只测 mock | `tests/bdd/test_scoring_agent.py` | MEDIUM | 无真实评分测试覆盖 |

---

## 后续行动

1. **待用户确认**：4维4分制+两层分离方案是否符合预期
2. **确认后**：更新 PRD 相关 FR（FR-EXAM-04 + 新增 FR）
3. **回到主 Tab**：继续 validate-prd Step 1 → Step 2 Format Detection
4. **代码 bug**：前端 scale bug 和 edge case bug 应尽早修复（不依赖 rubric 决策）

---

## 参考论文列表

| 论文/框架 | 年份 | 来源 |
|---------|------|------|
| AutoSCORE | 2025 | arXiv 2509.21910 |
| RULERS | 2025/2026 | arXiv 2601.08654 |
| LLM-Rubric | 2024 | ACL 2024 (Microsoft) |
| FLASK | 2024 | ICLR 2024 Spotlight (KAIST) |
| CheckEval | 2025 | EMNLP 2025 |
| Autorubric | 2026 | arXiv 2603.00077 |
| CARO | 2026 | arXiv 2603.00451 |
| MRBench | 2025 | NAACL 2025 |
| PEARL | 2025 | MDPI Information |
| Grade Like a Human | 2024 | arXiv 2405.19694 |
| RubricBench | 2026 | arXiv 2603.01562 |
| LLM-Driven Algebraic Assessment | 2025 | arXiv 2510.06253 |
| Reflective Prompt Engineering | 2025 | Taylor & Francis |
