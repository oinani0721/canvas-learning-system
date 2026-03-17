<!-- prompts/scoring/stage2_rubric.md -->
<!-- Story 6.4 AC-2: AutoSCORE Stage 2 — SOLO-anchored Rubric Scoring -->
<!-- Referenced by: services/autoscore.py:AutoScorer._score_with_rubric() -->
<!-- Version: v1 | Created: 2026-03-16 -->

基于证据提取结果，对学生回答进行 4 维评分。

### SOLO 分类锚定评分标准

每个维度采用 0-3 分制：

#### 概念准确性（concept_accuracy）
- **0 分 (前结构)**: 核心概念完全错误或无关
- **1 分 (单点结构)**: 仅涉及一个正确概念，其余有误或缺失
- **2 分 (多点结构)**: 多个概念正确但存在个别不准确
- **3 分 (关联结构)**: 所有涉及概念准确无误，术语使用规范

#### 推理质量（reasoning_quality）
- **0 分**: 无推理过程或完全不相关
- **1 分**: 有推理尝试但逻辑链不完整或有明显谬误
- **2 分**: 推理基本正确但有小的逻辑跳跃
- **3 分**: 推理链完整、逻辑严密、因果清晰

#### 知识覆盖（knowledge_coverage）
- **0 分**: 未覆盖任何要点
- **1 分**: 覆盖不足 40% 的要点
- **2 分**: 覆盖 40%-80% 的要点
- **3 分**: 覆盖 80% 以上的要点

#### 知识整合（knowledge_integration）
- **0 分**: 知识点孤立罗列，无联系
- **1 分**: 尝试联系但联系牵强或错误
- **2 分**: 部分概念有合理联系
- **3 分**: 概念间联系紧密，展现系统性理解

### 输入
- **证据提取结果**: {{evidence}}

### 评分规则
1. 严格基于证据评分，不可臆测
2. 每维评分必须附带证据引用作为理由
3. 若证据不足以判断某维度，给出保守评分

### 输出格式
```json
{
  "scores": {
    "concept_accuracy": {"score": 0, "justification": "理由"},
    "reasoning_quality": {"score": 0, "justification": "理由"},
    "knowledge_coverage": {"score": 0, "justification": "理由"},
    "knowledge_integration": {"score": 0, "justification": "理由"}
  },
  "overall_score": 0,
  "confidence": "high",
  "feedback_summary": "简要反馈"
}
```
