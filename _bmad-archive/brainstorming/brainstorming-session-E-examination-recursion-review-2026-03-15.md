# Session E 检验白板递归设计审查 — Brainstorming 总结

> 汇总日期：2026-03-15
> 来源：New Tab Session（PRD Review 支线讨论）
> 关联：主 Tab PRD Review 验证工作流
> 状态：调研完成，结论待写入 PRD

---

## 一、Session 目标

审查 PRD 中检验白板递归考察机制的设计可靠性，识别 Gap 并寻找成熟解决方案。

---

## 二、递归机制现状（PRD 原版描述）

### 核心流程

```
用户创建检验白板 → 系统选薄弱节点 → AI 出题考察
  → 用户回答 → AI 评分 → 发现盲区 → 生成新节点回写原白板
  → 新节点可继续被点击剖析和考察（递归）
```

### 涉及的 PRD 条目

- FR-EXAM-05: 考察中发现的新见解/盲区可生成新节点回写到原白板
- FR-EXAM-06: 检验白板支持递归考察——新生成的节点可被点击继续深入剖析和考察
- FR-EXAM-07: 检验白板继承原白板的所有基础功能（节点对话、Edge 对话等）
- FR-EXAM-08: 系统提供认知负荷控制（15/25/35/45 分钟递进提醒）
- 创新聚焦：递归最大风险"越深越打击信心" → 认知负荷控制 + 多题验证（3 题多数投票 85%→95%）

### 已有保护措施

- 认知负荷时间提醒（15/25/35/45 分钟）
- 3 题多数投票提高单层评分准确性
- 回退策略：退化为单轮考察

---

## 三、初始分析：发现 5 个 Gap

| 编号 | 严重度 | 问题 | 说明 |
|------|--------|------|------|
| Gap 1 | 🔴 高 | 无递归终止条件 | 没有算法层面的 base case，只有时间提醒（提醒 ≠ 强制终止） |
| Gap 2 | 🔴 高 | 无递归深度上限 | A*→admissibility→一致性→三角不等式…可无限展开，时间控制 ≠ 深度控制 |
| Gap 3 | 🟡 中 | 跨层误差累积 | AI 第 1 层误判→第 2 层基于错误前提展开→用户被考已会的东西。3 题投票只解决单层 |
| Gap 4 | 🟡 中 | 每层新节点数无限制 | 一次考察发现 5 个盲区→5 个新节点→下层再发现→爆炸式增长 |
| Gap 5 | 🟡 中 | 回写无质量关卡 | AI 误判产生的低质量节点直接污染原白板，无用户确认机制 |

---

## 四、深度定向调研结果

### 4.1 RPKT 论文（2025 IEEE — 最重要发现）

**论文**: RPKT: Learning What You Don't Know — Recursive Prerequisite Knowledge Tracing in Conversational AI Tutors for Personalized Learning

**与我们的检验白板递归几乎同构**：也是用 LLM 递归挖掘学习者的知识盲区，一层一层追踪先修知识直到到达知识边界。

| 机制 | RPKT 的做法 | 对我们的启示 |
|------|-----------|-----------|
| 深度限制 | `d_max` 参数，实测 L0-L3（4 层） | 可参考设为 d_max=3 |
| 知识边界检测 | Binary assessment（懂/不懂），用户标记"懂"就停止该分支 | 用户点击新节点=确认深入，不点=停止 |
| 状态追踪 | Session Management System 防止重复查询同一概念 | 检验白板中已检查的概念不再出题 |
| 认知负荷 | 二元选择替代量表评估，降低认知负担 | 简单的点击/不点击已是最低负荷 |

**来源**: https://arxiv.org/html/2508.11892

### 4.2 Knowledge Space Theory / ALEKS（40 年理论 + 3000 万用户）

| 概念 | 含义 | 对我们的启示 |
|------|------|-----------|
| Outer Fringe | 学生"准备好学"的下一层知识集合 | 新节点应限制在与原主题相关的"下一层"范围内 |
| Inner Fringe | 学生当前能力的"高点"集合 | 考察应从 inner fringe 的薄弱点入手 |
| 范围约束 | 只评估 fringe 上的知识，不跳跃式展开 | 每层新节点按知识图谱距离排序，优先最近的 |

**来源**: https://www.aleks.com/about_aleks/knowledge_space_theory

### 4.3 CAT 停止规则（心理测量学 40+ 年工业实践）

| 停止规则 | 原理 | 适用性 |
|---------|------|-------|
| Standard Error (SE) | 测量精度足够时停止 | 适合精通度估计 |
| SPRT | 序贯概率比检验，对 mastery/non-mastery 做分类决策 | 适合"是否达标"判断 |
| Fixed Length | 最大题目数兜底 | 简单可靠的安全阀 |
| Minimum Information | 没有更多有信息量的题目时停止 | 适合防止低效出题 |

**来源**: https://www.healthmeasures.net/resource-center/measurement-science/computer-adaptive-tests-cats/stopping-rules

### 4.4 BKT 精通阈值

- 标准实践：P(mastery) >= 0.75 视为掌握
- Khan Academy / Coursera 验证有效
- PRD 已有 BKT，可直接复用此阈值

### 4.5 Stepwise Verification（2024 arXiv）

- Verifier + Tutor 两步解耦：先由独立验证器判断学生错误，再由 tutor 生成反馈
- Error Description 验证准确率 82.4%
- 可阻断误差传递（单步错误不会自动传播到下一步）

**来源**: https://arxiv.org/html/2407.09136v1

---

## 五、关键转折：用户洞察

### 用户指出：递归控制权天然在用户手里

> "检验白板和原白板一样，拥有点击节点切换对话的功能。当点击到新发现的问题节点，不就是可以进行继续进一步的剖析了吗？"

这一洞察改变了问题的性质：

```
递归模型（PRD 原版意图）：
  AI 考察 → 发现盲区 → 生成新节点出现在白板上
                                    ↓
                    用户想深入？点击它 → 打开对话 → 剖析/继续考
                    不想深入？不点就行 → 自然结束
```

**用户的"点击"行为本身就是递归的确认和终止控制。**

### 重新评级

| Gap | 原严重度 | 新评估 | 原因 |
|-----|---------|--------|------|
| Gap 1 无终止条件 | 🔴 高 | 🟢 自然解决 | 用户不点 = 终止 |
| Gap 2 无深度上限 | 🔴 高 | 🟢 自然解决 | 用户控制点几层 |
| Gap 3 跨层误差累积 | 🟡 中 | 🟡 降低 | 风险变为"AI 生成不准确的盲区节点"，但用户有选择权不点 |
| Gap 4 节点数无限制 | 🟡 中 | 🟡 仍需解决 | 一次考察生成多个新节点→视觉混乱 |
| Gap 5 回写无质量关卡 | 🟡 中 | 🟡 仍需解决 | 新节点写回原白板仍需用户确认 |

---

## 六、最终结论：PRD 需要补充的内容

### 仍需写入 PRD 的 2 条新 FR

#### FR-EXAM-09：每次考察新节点数量控制

> 检验白板单次考察中，系统生成的新发现节点不超过 N 个（建议 N=3），按与当前考察主题在知识图谱上的距离排序，优先生成最相关的节点。已检查过的概念不再重复生成。

**学术支撑**：Knowledge Space Theory "outer fringe" 概念（ALEKS 3000 万用户验证）+ RPKT session state tracking

#### FR-EXAM-10：考后审查与回写确认

> 检验白板考察结束后，系统展示"本次发现"总结面板，列出所有新生成的节点。用户可逐个确认保留或删除。仅用户确认保留的节点才写入原白板知识图谱。新节点在未确认前标记为"💡 待确认"状态。

**设计原理**：防止 AI 误判产生的低质量节点污染原白板；"购物车"式审查机制给用户最终控制权。

### 可选优化（不必写入 PRD，实现阶段考虑）

| 优化 | 说明 | 优先级 |
|------|------|--------|
| d_max 深度限制 | 虽然用户驱动已解决，但可作为后台安全阀（如 d_max=5） | P3 |
| 精通度跳过 | BKT >= 0.75 的节点不再自动生成考察题 | P2（已由 FSRS+BKT 选题逻辑隐含） |
| 递归范围约束 | 新节点必须与原白板主题在图谱上 N 跳以内 | P3 |

### 不需要改动的部分

- 认知负荷时间提醒（15/25/35/45 分钟）— 保留作为兜底
- 3 题多数投票 — 单层评分准确性控制仍有效
- 回退策略（退化为单轮考察）— 保留

---

## 七、调研来源汇总

| 来源 | 类型 | 链接 |
|------|------|------|
| RPKT (2025 IEEE) | 论文 | https://arxiv.org/html/2508.11892 |
| Knowledge Space Theory / ALEKS | 理论+产品 | https://www.aleks.com/about_aleks/knowledge_space_theory |
| CAT Stopping Rules | 心理测量学标准 | https://www.healthmeasures.net/resource-center/measurement-science/computer-adaptive-tests-cats/stopping-rules |
| Stepwise Verification (2024) | 论文 | https://arxiv.org/html/2407.09136v1 |
| BKT Mastery Threshold | 标准实践 | https://en.wikipedia.org/wiki/Bayesian_knowledge_tracing |
| CAT Stopping Rules Comparison | 论文 | https://www.ideals.illinois.edu/items/107231 |

---

## 八、与主 Tab PRD Review 的衔接

本文档作为 PRD 验证的参考输入：

1. **主 Tab 验证时**：在 FR-EXAM 域的检查中，引用本文档的 Gap 分析和结论
2. **PRD 修订时**：将 FR-EXAM-09 和 FR-EXAM-10 写入 PRD 功能需求章节
3. **验证报告中**：记录"递归设计审查已完成，发现 2 项需补充的 FR"

---

*本文档由 New Tab brainstorming session 生成，供主 Tab PRD Review 工作流引用。*
