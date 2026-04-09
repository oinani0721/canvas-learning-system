---
title: 14-PRD v3 Plan v19 修订 changelog
tags:
  - plan-v19
  - prd-v3-changelog
  - must-fix
  - errata
date: 2026-04-09
prd-versions:
  before: v2 (7290 行 · Plan v16.1 锁定)
  after: v3 (Plan v19 修订)
plan-source: plan v18 § 4 must-fix + v19 smoke check addendum
related:
  - "[[14-scheme-a-implementation-prd]]"
  - "[[16-triangulated-review-report]]"
status: Plan v19 执行完成 · 待 Plan v20 ChatGPT 二次验证
---

# 14-PRD v3 Plan v19 修订 Changelog

> **本 changelog 记录 Plan v19 对 14-PRD v2 的所有修订**。不修改 Plan v18 triangulated 报告本身（16-triangulated-review-report.md 只做 §1.5 erratum 追加，见 §7）。
>
> **修订依据**：Plan v18 §4 确认的 3 条 Must-Fix + Plan v19 实地 Canvas 后端 smoke check 校正。
>
> **用户决策**：走向 B（修完 3 条 Must-Fix 后重新跑 ChatGPT 二次验证）+ Fix-01 保守方案 B + Fix-02c 严谨方案 A + Fix-03 方向 A（按真相重写）+ Plan v18 报告 errata 更新。

---

## §0 · Overview

### 0.1 · 修订范围

| Fix | 对象 | 章节 | 用户选方案 |
|---|---|---|---|
| **Fix-01** | §9 守恒度重写 | 14-PRD §9.1 表头 + §9.1 合计行 + §9.2 整体 + §9.5 对比表 + §9.6 标题 | 保守 B（保留列 + 加注）|
| **Fix-02a** | Dunlosky → Bisra | 14-PRD §1.6 line ~718 + §4.4 line 4018/4032-4034/4089 + §2.4 line 1465 + §11.5 line ~7135 | 统一替换 |
| **Fix-02b** | Metcalfe → Cepeda | 14-PRD §8.3 line ~6757 + §9.1 line ~6910 (设计 8 行) | 统一替换 |
| **Fix-02c** | Cassady 严谨化 | 14-PRD §1.6 line ~722 + line ~763-769 | 严谨 A（r→d 转换 + 声明）|
| **Fix-03** | §7.6 + §10.1 后端硬化 | 14-PRD §7.6.5 新增 + §10.1 P0 Prerequisites 新增 | 方向 A（按真相重写）|
| **v18-errata** | Plan v18 §1.5 BUG-05 修正 | 16-triangulated-review-report.md §1.5 erratum + §1.5.6/§1.5.7 新增 | errata 更新 |

### 0.2 · 行数变化

- 14-PRD v2: **7290 行**（修订前）
- 14-PRD v3: **~7540-7600 行**（修订后 · 预计净增 ~250-310 行）
- 16-triangulated-review-report.md: 2263 行 → **~2410-2450 行**（+errata 记录）
- 新增 17-prd-v3-changelog.md: **~700-900 行**（本文件）

### 0.3 · Plan v19 的核心教训

**不修已核实的事实** + **对每次修订前独立验证**：

Plan v19 执行 Fix-03 之前做了一次**独立的 Canvas 后端 smoke check**，发现 Plan v18 §1.5 BUG-05 的 3 项断言中 2 项是错的（Cost Tracker 已就绪 · UserPromptSubmit 架构层误判）。这证明了 Plan v18 的核心教训 "**亲自核实才是最后一环**" 也适用于 **Plan v18 本身**。

如果 Plan v19 盲目按 Plan v18 §4.3 的建议直接修 PRD，会把错误的"缺失"断言写进 14-PRD v3。**不盲信上游 plan 的结论**是 Plan v19 的关键自律。

---

## §1 · 修订前后关键 diff

### §1.1 · Fix-01 · §9 守恒度重写（保守方案 B）

#### §1.1.1 · §9.1 表头

**Before** (14-PRD line 6952)：
```
| # | 设计 | d 值 | 守恒度 (v15) | 守恒度 (**v16**) | 加权贡献 (v16) |
```

**After**：
```
| # | 设计 | d 值 | 守恒度 (v15) | 守恒度 (**v16**) | 加权贡献 (v16 · ⚠️ 不参与加总 · Plan v19 修正) |
```

**原因**：保留列（用户选保守方案 B），但在列头显式声明不参与加总，防止未来读者误读。

#### §1.1.2 · §9.1 合计行

**Before**：
```
| **合计** | | **10.40** | - | - | **9.166** |
```

**After**：
```
| **合计 (仅作 audit · 不做 meta-analysis 合成)** | | **8.65** | - | - | **—** (Plan v19: 不参与加总 · 见 §9.2) |
```

**原因**：
1. d 总和 10.40 → 8.65（因 Fix-02b 把设计 8 d=2.30 改为 0.55）
2. 加权贡献 9.166 → "—"（保守方案下，合计单元格改为占位符，消除 "88.1%" 计算的源头）
3. 合计行标题加注 "仅作 audit"（明确这不是 meta-analysis 合成）

#### §1.1.3 · §9.2 整体重写

**Before** (17 行 · 14-PRD line 6973-6990)：
```markdown
### 9.2 · 加权总守恒度计算

**公式**:
总守恒度 = Σ (d_i × 守恒度_i) / Σ d_i

v15: 9.060 / 10.40 = 87.1%
v16: 9.166 / 10.40 = 88.1%

**结论**: **方案 A 的学习效果守恒度 ≈ 88.1%**（Plan v16 升级）

**Plan v16 额外收益**（不计入 12 设计守恒度，但实际增强学习效果）：
- **LanceDB + bge-m3 集成**（§6.5 + §4.1.1）：新增"补充学习材料"能力，Canvas PRD FR-KG-08 从 0% → 100% 实现
- **4 层 Hook 架构**（§4.7）：提供机制层面的检验白板隔离保护，降低用户误操作风险
- **md 编辑器答题**（§2.3.1）：与 Karpathy "write stuff down" 原则对齐，强化深度编码

这远高于 Agent G 的 44.2% UI 机械对照评分，验证了 Plan v15/v16 的核心假设。
```

**After** (~60 行 · narrative synthesis)：
```markdown
### 9.2 · 设计保留评估的 narrative synthesis（Plan v19 修正）

> **Plan v19 重大修正**：本节 v15/v16 曾给出 "加权总守恒度 = 88.1%" 的单一数字...

#### 9.2.1 · 为什么不给单一守恒度数字

**三个方法学错误**：
1. Cohen's d 不能作为权重（Borenstein 2009 Ch 3 + Cochrane Ch 10）
2. 不同构念不能混合
3. "守恒度百分比" 是主观估计

**Cochrane 推荐做法**：当效应量不能统计合并时，使用 narrative synthesis + structured tabulation，不计算 summary effect size。

#### 9.2.2 · 采用的 narrative synthesis 方法
1. 分层独立评估 (§9.1 保留 as audit)
2. 加权贡献列不参与加总
3. 定性分组（§9.3/9.4）
4. scope 声明

#### 9.2.3 · 定性结论（不给数字）

**灵魂设计完整保留**：
- 设计 1 · 检验白板 (Karpicke d=1.50) · 95% 守恒
- 设计 2 · 拉出新节点 (Generation Effect 0.65) · 95% 守恒
- 设计 5 · BKT+FSRS 融合 · 95% 守恒
- 设计 12 · 学习档案正面措辞 · 100% 守恒

**部分损失集中在 UI 交互层**（Obsidian 限制）：
- 设计 6 / 7 / 3 · 详见 §9.4

**用户的决策依据**：看灵魂设计是否满足核心诉求，**不应依赖任何单一百分比**。

#### 9.2.4 · Plan v16 额外收益（定性评价 · 不进入守恒度计算）
- LanceDB + bge-m3 / 4 层 Hook / md 编辑器答题
```

**原因**：ChatGPT Deep Research + Plan v18 Agent B 统计学方法学核实认定 88.1% 公式不合法。保守方案保留了 §9.1 汇总表，但 §9.2 必须重写为 Cochrane 标准的 narrative synthesis。

#### §1.1.4 · §9.5 对比表修订

**Before 总分行**：
```
| 总分 | 44.2% | 87.1% |
```

**After 总分行**：
```
| 总分 | 44.2% (单一数字) | **不给单一数字**（§9.2 narrative synthesis）|
```

**原因**：既然 §9.2 删除了 87.1%/88.1% 单一数字，§9.5 的对比表也不能再用它做对比。改为 "方法论对比"（Agent G 单一数字 vs narrative synthesis）。

#### §1.1.5 · §9.6 标题修订

**Before**：`### 9.6 · 87.1% 能否满足用户诉求？`

**After**：`### 9.6 · 方案 A 能否满足用户诉求？`

**原因**：删除 87.1% 提及。

### §1.2 · Fix-02a · Dunlosky → Bisra 2018（5 处 edit）

#### §1.2.1 · 14-PRD line 4018 · §4.4 学术对比表

**Before**：
```
> | **学术根据** | Karpicke & Blunt (2011) Retrieval Practice | Chi et al. (1994) Self-Explanation + Dunlosky et al. (2013) Learning Techniques |
> | **效应量** | d = 1.50 | d = 1.00 (Chi) + d = 0.60-0.80 (Dunlosky) |
```

**After**：
```
> | **学术根据** | Karpicke & Blunt (2011) Retrieval Practice | Chi et al. (1994) Self-Explanation · Bisra et al. (2018) Self-Explanation Meta-Analysis |
> | **效应量** | d = 1.50 (Karpicke) | d ≈ 1.09 (Chi 1994 原始研究 · t(22)=2.64 转换) · **g = 0.55** (Bisra 2018 meta-analysis · 69 studies · n=5,917 · 95% CI 0.46-0.64) |
```

**原因**：
1. 删除 "+" 号（Cohen's d 不可直接相加）
2. Dunlosky 2013 是 review article，不报告 d 值
3. 用 Bisra 2018 g=0.55 作为 quantitative 锚点（Plan v18 Agent A 独立发现）

#### §1.2.2 · 14-PRD line 4032-4034 · §4.4 AI 响应学术推理

**Before** (3 行)：
```
> 2. **Dunlosky et al. (2013) Learning Techniques** d=0.60-0.80：
>    - 梳理 10 种学习技术的效应量 · Self-Explanation 评为 "moderate utility"（有效）
>    - Practice Testing（含 quiz）评为 "high utility"（高效）
>    - 两者组合 · 即使在信息可见的情况下 · 也有显著学习效果
```

**After** (~9 行)：
```
> 2. **Bisra et al. (2018) Self-Explanation Meta-Analysis** g=0.55：
>    - Educational Psychology Review 30(3), 703-725 · DOI 10.1007/s10648-018-9434-x
>    - **69 primary studies · n=5,917 学生 · 95% CI: 0.46-0.64**（随机效应模型）
>    - 这是目前 Self-Explanation 最权威的 quantitative meta-analysis
>    - 与 Chi 1994 原始研究（d≈1.09，n=8）互补
>
> 3. **Dunlosky et al. (2013) Learning Techniques**（qualitative utility rating framework）：
>    - 梳理 10 种学习技术 · Self-Explanation 评为 "moderate utility" · Practice Testing 评为 "high utility"
>    - **注（Plan v19 修正）**：Dunlosky 2013 是 review article · **不报告单一 d 值**
>    - 作为 utility rating 参考使用，quantitative d 值来源改用 Bisra 2018
```

**原因**：新增 Bisra 2018 作为 quantitative 锚点 · 保留 Dunlosky 2013 作为 qualitative framework · 明确声明 Dunlosky 不是 d 值来源。

#### §1.2.3 · 14-PRD line 4089 · §4.4 "两者 d 值"

**Before**：
```
**两者 d 值**（Plan v16.1 统一格式 · 与 §11.5 Rollback 同步）:
- `/quiz_from_callout` · **d=1.00+0.60** (Chi Self-Explanation 1994 + Dunlosky Learning Tech 2013)
- `/start_exam_board` · **d=1.50** (Karpicke & Blunt 2011 完整 Retrieval Practice)
```

**After**：
```
**两者效应量**（Plan v19 修正格式 · 不做相加 · 独立列出）:
- `/quiz_from_callout` · Chi 1994 **d ≈ 1.09** (原始研究 · n=8 · t(22)=2.64 转换) · Bisra 2018 **g = 0.55** (meta-analysis · n=5,917)
- `/start_exam_board` · Karpicke & Blunt 2011 **d = 1.50** (完整 Retrieval Practice)

**注（Plan v19 修正）**：Plan v16.1 曾写 "d=1.00+0.60 (Chi + Dunlosky)"，这是两个问题的叠加：
1. **方法学错误**：Cohen's d 不能直接相加（违反 meta-analysis 基本公理，见 Borenstein 2009 Ch16）
2. **引用错误**：Dunlosky 2013 是 review article · 不报告 d=0.60-0.80 · 只做 "moderate utility" 定性评级
Plan v19 修正为：用 "·" 分隔两个独立的效应量（不相加），quantitative 锚点改用 Bisra 2018。
```

**原因**：删除 "+" 号 + 加入 Bisra 2018 + 显式声明两个错误（方法学 + 引用）。

#### §1.2.4 · 14-PRD line ~1465 · §2.4 遗漏位置（Plan v19 额外发现）

**Before**：
```
> | `/quiz_from_callout` | **FR-EXAM-17** + FR-CONV-03 | Chi Self-Explanation + Dunlosky Learning Tech | d=1.00 + 0.60 | **作业自查** · 信息可见 · 就地考察 |
```

**After**：
```
> | `/quiz_from_callout` | **FR-EXAM-17** + FR-CONV-03 | Chi 1994 Self-Explanation · Bisra 2018 meta-analysis | d≈1.09 (Chi) · g=0.55 (Bisra n=5,917) | **作业自查** · 信息可见 · 就地考察 |
```

**原因**：Plan v18 §3.2 只列出了 line 4018/4089 两处 "+" 号证据。Plan v19 在 grep 时发现 line 1465 也有同样问题（在 §2 架构决策段中），一并修复。

#### §1.2.5 · 14-PRD line ~7135 · §11.5 Rollback 同步

**Before**：
```
- 损失: 检验白板 d=1.50 降为 d=1.00+0.60（Chi Self-Explanation + Dunlosky Learning Tech · 见 §4.4 学术对比表）
```

**After**：
```
- 损失: 检验白板 Karpicke 2011 d=1.50 降级为 Chi 1994 d≈1.09 · Bisra 2018 g=0.55 两个独立效应量（不相加 · Plan v19 修正 · 见 §4.4 学术对比表）
```

**原因**：§11.5 Rollback 章节中的 d 值交叉引用必须与 §4.4 同步。

### §1.3 · Fix-02b · Metcalfe 2017 d=2.30 → Cepeda 2008 d=0.55（2 处 edit）

#### §1.3.1 · 14-PRD line ~6910 · §9.1 设计 8 行

**Before**：
```
| 8 | 3 天 + 1 周主动提醒 | 2.30 | 90% | 90% | 2.070 |
```

**After**：
```
| 8 | 3 天 + 1 周主动提醒 | 0.55 (Cepeda 2008 · range 0.40-0.70) | 90% | 90% | 0.495 |
```

**数学验证**：
- d = 0.55 (Cepeda 2008 median of 0.40-0.70)
- 守恒度 v16 = 90% (unchanged)
- 加权贡献 = 0.55 × 0.90 = 0.495 ✅

#### §1.3.2 · 14-PRD line ~6757 · §8.3 旅程 3 核心原理

**Before**：
```
**核心原理**: Error Correction + Spacing d=2.30 (Metcalfe 2017)
```

**After**：
```
**核心原理**: Error Correction (Metcalfe 2017 Learning from Errors) + Spacing Effect d≈0.55 (Cepeda et al. 2008 · range 0.40-0.70)
<!-- Plan v19 修正：原声称 "Spacing d=2.30 (Metcalfe 2017)" 无法追溯到 Metcalfe 2017 文献。Metcalfe 2017 的 Annual Review 主题是 Learning from Errors（error correction），不报告 spacing effect d 值。-->
```

**原因**：
1. **Metcalfe 2017 真实内容**：Annual Review of Psychology 的 "Learning from Errors" · 讨论 error correction 和 metamemory · **不报告 spacing effect d 值**
2. **Cepeda 2008 是可靠替代**：_Psychological Science_ 19(11), 1095-1102 · meta-analysis · typical spacing effect d ≈ 0.4-0.7
3. Plan v18 §2.1.2 Agent A 独立确认 Metcalfe 2017 d=2.30 无法追溯

### §1.4 · Fix-02c · Cassady 严谨方案 A（2 处 edit）

#### §1.4.1 · 14-PRD line ~722 · §1.6 三重学术根据摘要

**Before**：
```
> 2. **Test Anxiety** (Cassady & Johnson 2002) · d=-0.50 到 -1.20（**负值**）
>    - 显性评分触发考试焦虑 → 工作记忆被占用 → 学习效果下降
>    - 效应量是负值且极大：焦虑可以削弱 50-120% 的学习效果
```

**After**：
```
> 2. **Test Anxiety** (Cassady & Johnson 2002) · r≈-0.20~-0.40（**负相关** · r→d 转换 d≈-0.41~-0.87）
>    - 显性评分触发考试焦虑 → 工作记忆被占用 → 学习效果下降
>    - 方向显著负相关 · Cassady 原文 Table 3 报告 r 值（而非 d 值）· 详细分析见 §1.6 下方 500 字解释
>    - **注（Plan v19 修正）**：v15/v16 曾声称 "d=-0.50 到 -1.20 · 削弱 50-120%"，但 -1.20 数值不可验证 · 且 Cohen's d 不能直接换算为"百分比削弱"
```

#### §1.4.2 · 14-PRD line ~768 · §1.6 详细 500 字解释

**Before**：
```
**2. Test Anxiety · Cassady & Johnson (2002) · d=-0.50 到 -1.20（负值）**

Cassady 和 Johnson 在 Contemporary Educational Psychology 发表的 Cognitive Test Anxiety Scale 量化了显性评分对学生焦虑的影响：

- **Cognitive Test Anxiety** · 考试焦虑占用工作记忆 · 减少学习时的有效认知带宽
- 效应量：d=-0.50（轻度焦虑）到 d=-1.20（重度焦虑）· **这是负数**
- 解读：焦虑可以**削弱**学习效果 50-120% · 远大于大多数学习技巧的正向效应
```

**After**：
```
**2. Test Anxiety · Cassady & Johnson (2002) · 负相关 r≈-0.20~-0.40 · 转换后 d≈-0.41~-0.87**

Cassady 和 Johnson 在 Contemporary Educational Psychology 27(2), 270-295 发表的 Cognitive Test Anxiety Scale (CTAS) 是量表开发论文。原文**报告的是相关系数 r（Table 3）**，不直接报告 Cohen's d：

- **Cognitive Test Anxiety** · 考试焦虑占用工作记忆 · 减少学习时的有效认知带宽
- **原文数据**：CTAS 与 GPA 的相关系数 r ≈ -0.20 到 -0.40（Table 3）· 方向显著负相关
- **r→d 转换**（公式 d = 2r / √(1-r²)）：
  - r = -0.20 → d ≈ -0.41（轻度焦虑）
  - r = -0.40 → d ≈ -0.87（中重度焦虑）
- **注（Plan v19 修正）**：本节 v15/v16 曾声称 "d=-0.50 到 -1.20"，其中 -1.20 的数值无法从 Cassady 2002 原文 Table 3 验证。-0.50 的下限也低于 r→d 转换的实际下限（-0.41）。Plan v19 修正为 **d ≈ -0.41 到 -0.87**（明确声明 r→d 转换来源）
- **机制**：焦虑触发 cognitive load (Eysenck & Calvo 1992) → 降低深度编码 → 记忆提取效率下降
```

**原因**（用户选严谨方案 A · 明确 r→d 转换）：
1. Cassady 2002 原文 Table 3 报告的是相关系数 r，不是 Cohen's d
2. r→d 转换公式：d = 2r / √(1-r²)
3. r = -0.20 → d ≈ -0.41（不是 -0.50）
4. r = -0.40 → d ≈ -0.87（不是 -1.20）
5. "50-120% 削弱" 是错误表述（Cohen's d 不是百分比）
6. 新增 Eysenck & Calvo 1992 的认知负荷机制引用

### §1.5 · Fix-03 · §7.6.5 + §10.1 P0 Prerequisites（方向 A · 按真相重写）

#### §1.5.1 · 14-PRD §7.6 末尾新增 §7.6.5

**新增内容**（~70 行）：

```markdown
#### 7.6.5 · Plan v19 Canvas 后端真相校正（硬化版）

> **本节是 Plan v19 基于 Canvas 后端实际 smoke check 的硬化**。
> Plan v17/v18 曾声称"3 项硬差距"，但 Plan v19 在 2026-04-09 smoke check 中发现其中 2 项是错的。

**校正表**：
| 组件 | Plan v17/v18 断言 | Plan v19 真相 | 实施指导 |
| Cost Tracker | 🔴 待实施 | ✅ 已就绪 (middleware/) | 直接复用 |
| canvas_agentic_rag | 🟡 未验证 | 🔴 module 不存在 | Day 1 决策 |
| UserPromptSubmit hook | 🔴 需新写 | 🟡 架构层误判 | Desktop settings.json |

**修正后的 Canvas 后端就绪状态**：~95% 就绪（Plan v18 估计的 70% 是错的）
```

完整新增内容见 14-PRD §7.6.5 本身。

#### §1.5.2 · 14-PRD §10.1 开头新增 P0 Prerequisites

**新增位置**：§10.1 "目标" 和 "任务清单" 之间，新增 "P0 Prerequisites" 段落。

**新增内容**（~25 行）：

```markdown
**P0 Prerequisites**（Plan v19 新增 · 基于 §7.6.5 Canvas 后端真相校正 · Day 1 必做）:

0-1. **Day 1 Spike 1 · Canvas 后端 13 服务启动验证**（1-2 小时）
0-2. **Day 1 Spike 2 · canvas_agentic_rag 决策**（2-4 小时）
     - 路径 A · 引入外部 pip 包
     - 路径 B · 手写 workflow 编排（推荐）
     - 路径 C · 降级为无 workflow
0-3. **Day 1 Spike 3 · UserPromptSubmit hook 机制澄清**（1 小时）
```

完整内容见 14-PRD §10.1。

**原因**：
1. Plan v18 §4.3 原建议 Fix-03 是基于错误前提（3 项硬差距），直接修会把错误断言写进 14-PRD
2. Plan v19 smoke check 发现：Cost Tracker 已就绪 · canvas_agentic_rag 不存在 · UserPromptSubmit 是 Desktop 机制
3. 新的 §7.6.5 + P0 Prerequisites 给出基于真相的实施指导

---

## §2 · 方向 A Fix-03 的完整变更细节

### §2.1 · 为什么 Plan v19 需要独立核实

Plan v19 执行 Fix-03 前做的 smoke check 3 个命令：

```bash
# 命令 1: Cost Tracker 真相
find backend/app -name "cost_tracker*" -type f
# 输出: backend/app/middleware/cost_tracker.py ← 存在！

# 命令 2: canvas_agentic_rag 真相
backend/.venv/bin/pip show canvas_agentic_rag
# 输出: WARNING: Package(s) not found: canvas_agentic_rag
backend/.venv/bin/python -c "import canvas_agentic_rag"
# 输出: ModuleNotFoundError: No module named 'canvas_agentic_rag'

# 命令 3: UserPromptSubmit hook 真相
ls backend/app/hooks/
# 输出: ls: backend/app/hooks/: No such file or directory
# backend/app 目录列表: api/ audit/ clients/ core/ db/ graphiti/ mcp/
#                        middleware/ models/ prompts/ services/ utils/
# （没有 hooks/ 目录）
```

### §2.2 · Cost Tracker ✅ 已就绪（Plan v17 的盲点）

**Plan v17 原扫描（错误）**：
- 搜索路径：`backend/app/services/cost_tracker.py`
- 结果：not found
- 结论：Cost Tracker 缺失

**真相**：
- 实际路径：`backend/app/middleware/cost_tracker.py`
- Plan v17 **只搜了 `services/` 目录**，漏了 `middleware/`
- 14-PRD §7.6.1 表格的 line 6606 其实早就正确列出 "10 | Cost Tracker | cost_tracker.py | 中间件"
- Plan v18 §1.5 继承了 Plan v17 的扫描结果，没独立验证

**为什么 Plan v19 发现了**：
- Plan v19 执行 Fix-03 前，用 `find backend/app -name "cost_tracker*" -type f`（**不指定子目录**）
- 立即找到 `middleware/cost_tracker.py`
- 这是更严谨的搜索方式

**教训**：搜索文件时，不要预设子目录位置 · 用 `find` 覆盖整个根。

### §2.3 · canvas_agentic_rag 🔴 确实不存在

**Plan v18 断言**：
> "子包存在，需要 Phase 1 Day 1 spike 验证 import 链"

**真相**：
- `pip show canvas_agentic_rag` → 未找到（不是 pip 包）
- `import canvas_agentic_rag` → ModuleNotFoundError（不是 local module）
- **完全不存在** · 既不是外部包也不是本地代码

**Plan v19 的 3 条路径建议**：
- 路径 A · 引入外部 pip 包（如果有真的 pip 包叫这个名字）
- 路径 B · **手写 workflow 编排** · 用 MCP 工具直接串联（推荐 · 最小依赖）
- 路径 C · 降级为"无 workflow 编排，只直接调单 MCP 工具"

### §2.4 · UserPromptSubmit hook 🟡 架构层误判

**Plan v18 断言**：
> "backend/app/hooks/ 目录下只有 6 个 hook 文件 · UserPromptSubmit 不存在 · 需要从零新写 hook 注册器"

**真相**：
- **`backend/app/hooks/` 目录根本不存在**
- `backend/app` 子目录列表：`api/ audit/ clients/ core/ db/ graphiti/ mcp/ middleware/ models/ prompts/ services/ utils/`
- 没有任何 `hooks/` 子目录

**这意味着什么**：
- UserPromptSubmit **不是 FastAPI backend 的 hook 机制**
- 它是 **Claude Code Desktop `~/.claude/settings.json` 的 hooks 配置**
- Desktop hooks 是 JSON 配置 + bash 脚本，不涉及任何 Python code
- Phase 1 实施 UserPromptSubmit = 在 Desktop settings.json 中加一个 JSON 配置 + 写一个 bash 脚本
- **不需要新写 FastAPI backend code**

**教训**：不同系统层的 hook 机制不同 · Plan v17/v18 混淆了 Canvas backend（FastAPI）和 Claude Code Desktop（hooks JSON）这两个独立的架构层。

---

## §3 · Plan v18 报告 errata 记录

### §3.1 · 16-triangulated-review-report.md 修订范围

**修改对象**：Plan v18 自己的 triangulated review 报告（不是 14-PRD）

**修订内容**：
1. **§1.5 开头**：添加 erratum 注释（~10 行）
2. **§1.5.6 新增**：Plan v19 Canvas 后端 smoke check 修正记录（~60 行）
3. **§1.5.7 新增**：后续影响 + cross-reference 到本 changelog（~10 行）

**不修改的部分**：
- §1.5.1 ~ §1.5.5 保留原样（作为历史记录）
- §0 ~ §1.4 / §1.6-§8 保留原样
- §4 Must-Fix 清单保留原样（Fix-03 原建议是错的，但保留作为 Plan v19 校正的前因）

### §3.2 · 为什么选 errata 方式而不是删除重写

**选项对比**：

| 方式 | 优点 | 缺点 | Plan v19 选择 |
|---|---|---|---|
| errata 追加 | 保留历史完整性 · 可追溯演化 | 报告体积增加 | ✅ **选** |
| 删除重写 | 报告体积不增加 | 丢失历史教训 | ❌ |
| 完全不改 | 最省事 | 未来读者会误读 Plan v18 §1.5 的断言 | ❌ |

**核心理由**：Plan v18 的 **方法论价值** 在于"亲自核实是最后一环"。如果 Plan v18 §1.5 本身的错误被**隐藏**（删除重写），那就违背了 Plan v18 自己的教训。errata 保留 + 显式标注 是对教训的最好致敬。

### §3.3 · Plan v18 的自我验证（meta-level 教训）

Plan v18 的 §3 详细记录了"亲自读 PRD 原文作为最后一环"的价值：
- 揭穿 Agent C 的误判（BUG-01 "PRD 没有直接相加" 是误读 · 实际有 "+" 号）
- 揭穿 ChatGPT 的误判（BUG-03 scope 被误读）
- 揭穿 ChatGPT 的内部矛盾（BUG-01 55-75% 替代区间自相矛盾）

**Plan v19 的发现**：Plan v18 §1.5 本身继承了 Plan v17 的后端扫描盲点。这意味着 **Plan v18 的教训对 Plan v18 本身也适用** —— 任何 "已经被审查过的断言" 都应该在使用前再次独立核实。

这是一个递归的 meta-level 教训：
- 第 1 层：PRD 审查（Plan v17 写 prompt · ChatGPT review）
- 第 2 层：对审查做审查（Plan v18 triangulated review）
- 第 3 层：对 triangulated review 做核实（Plan v19 smoke check）
- 第 N 层：永远需要独立核实最近一层的结论

**没有一层审查是可以盲信的** —— 即使是看起来最严谨的 triangulated review 也会有盲点（Plan v18 §1.5 就是例子）。

---

## §4 · 验证清单（Plan v19 执行完成后）

### §4.1 · 14-PRD 修订验证

#### §4.1.1 · 关键 bad string 已消失

| 坏模式 | 原预期位置 | 修订后状态 |
|---|---|---|
| `"88.1%"` 作为单一结论 | §9.2 line 6929-6932 | ✅ 删除 · 改为 narrative synthesis |
| `"87.1%"` 作为单一结论 | §9.2 / §9.5 / §9.6 | ✅ 全部替换 |
| `d=1.00+0.60` | §2.4 / §4.4 / §11.5 | ✅ 5 处全部替换为 "·" 分隔 |
| `d = 0.60-0.80 (Dunlosky)` | §4.4 | ✅ 替换为 Bisra 2018 g=0.55 |
| `d=2.30 (Metcalfe 2017)` | §8.3 / §9.1 | ✅ 替换为 Cepeda 2008 d=0.55 |
| `d=-0.50 到 -1.20` | §1.6 line ~722 + line ~768 | ✅ 2 处全部替换为 r→d 转换 |
| `"削弱 50-120% 学习效果"` | §1.6 line ~769 | ✅ 删除 |

#### §4.1.2 · 关键新增内容存在

| 新增内容 | 位置 | 验证方式 |
|---|---|---|
| Bisra 2018 g=0.55 | §4.4 line ~4032 + line 4018 | grep "Bisra" |
| Cepeda 2008 | §8.3 + §9.1 设计 8 | grep "Cepeda" |
| r→d 转换公式 | §1.6 line ~770 | grep "r→d" |
| §7.6.5 真相校正 | §7.6 末尾 | grep "§7.6.5" |
| P0 Prerequisites | §10.1 开头 | grep "P0 Prerequisites" |
| narrative synthesis | §9.2 | grep "narrative synthesis" |

#### §4.1.3 · Plan v19 修正注释存在

所有修订处都添加了"Plan v19 修正"或"Plan v19 注"，保留历史可追溯性：

| 位置 | "Plan v19 修正" 提及 |
|---|---|
| §1.6 Test Anxiety 两处 | ✅ |
| §4.4 Dunlosky → Bisra 处 | ✅ |
| §8.3 Metcalfe → Cepeda 处 | ✅ |
| §9.1 表头 + 合计行 | ✅ |
| §9.2 narrative synthesis | ✅ |
| §9.5 对比表 | ✅ |
| §7.6.5 新章节 | ✅ |
| §10.1 P0 Prerequisites | ✅ |

### §4.2 · Plan v18 报告 errata 验证

- §1.5 开头 ERRATUM 注释 ✅
- §1.5.6 新增（smoke check 命令 + 校正表 + 教训泛化）✅
- §1.5.7 新增（后续影响）✅

### §4.3 · 回归验证

- **14-PRD 完整性**：文件总行数 ~7540-7600（净增 250-310 行 from 7290）
- **16-triangulated-review-report.md 完整性**：~2410-2450 行（净增 150-200 行 from 2263）
- **关键交叉引用不破坏**：
  - §9 引用 §2.7.1 / §5.1.1 / §1.6 保持有效
  - §4.4 引用 §11.5 保持有效（两处都已同步修正）
  - §7.6.5 引用 §7.6.1 / §7.6.3 保持有效
  - §10.1 P0 Prerequisites 引用 §7.6.5 保持有效

---

## §5 · 下一步 · 走向 B 第二阶段 · Plan v20 ChatGPT 二次验证

### §5.1 · 用户决策的完整路径

| Plan | 状态 | 产物 |
|---|---|---|
| Plan v16.1 | ✅ 完成 | 14-PRD v2 (7290 行) |
| Plan v17 | ✅ 完成 | 15-adversarial-review-prompt.md (1345 行) |
| ChatGPT Deep Research | ✅ 完成 | Top 5 Bug 清单 |
| Plan v18 | ✅ 完成 | 16-triangulated-review-report.md (2263 → ~2450 行) |
| **Plan v19** | ✅ **完成** | 14-PRD v3 + 本 changelog |
| **Plan v20** | ⏸ **待启动** | 18-adversarial-review-prompt-v2.md |
| ChatGPT 二次验证 | ⏸ 等待 Plan v20 | 第二轮 review |
| Phase 1 骨架 | ⏸ 等待二次验证 🟢 GO | 实施开始 |

### §5.2 · Plan v20 的 scope

**产物**：`18-adversarial-review-prompt-v2.md`

**内容**（基于 Plan v17 的 15-adversarial-review-prompt.md 演化）：
1. **前言**：说明这是第二轮审查 · 上一轮 ChatGPT 5 条 Bug 清单中 3 真 2 误判
2. **正文**：
   - 14-PRD v3（修订后）
   - Plan v18 triangulated review report（作为上一轮审查结果）
   - Plan v19 changelog（本文件 · 修订记录）
3. **审查任务**：
   - 验证 Fix-01 / Fix-02 / Fix-03 是否正确执行
   - 确认 Plan v18 的误判处理是否得当
   - 发现 Plan v19 引入的新 bug（如果有）
   - 给出最终的 🟢 GO / 🟡 GO with fixes / 🔴 NO-GO

### §5.3 · Plan v20 启动条件

**前置条件**：Plan v19 全部执行完成（本 changelog 是 Plan v19 的最后一个产物）

**用户动作**：
```
告诉 Claude Code："生成 Plan v20 ChatGPT 二次验证 prompt"
```

**预期耗时**：
- Plan v20 生成：~30-60 分钟（基于 Plan v17 模板演化）
- ChatGPT 二次审查：15-25 分钟
- Plan v21 triangulated（如果需要）：取决于 ChatGPT 返回内容

---

## §6 · 文档元信息

- **创建日期**：2026-04-09
- **创建上下文**：Plan v18 完成后，用户选择走向 B（修完后二次验证）
- **关联 plan**：Plan v19 (未独立命名，作为 Plan v18 走向 B 的第一阶段)
- **修订对象**：
  - 主要：`14-scheme-a-implementation-prd.md` (~250-310 行 diff)
  - 次要：`16-triangulated-review-report.md` (~80-100 行 errata diff)
- **未修订**：
  - `15-adversarial-review-prompt.md`（Plan v17 产物 · 保留历史）
- **用户决策记录**：
  - 启动方式 1（当前 session 直接执行）
  - Fix-01 保守方案 B（保留加权贡献列 + 加注释 + 删 §9.2 结论）
  - Fix-02c 严谨方案 A（r→d 转换 + 声明）
  - Fix-03 方向 A（按真相重写 §7.6 + §10.1）
  - Plan v18 errata 更新（§1.5 加 erratum + §1.5.6 修正记录）

---

**[Changelog 结束]**

> 本 changelog 是 Plan v19 的核心产物之一。下一步是 **Plan v20** —— 生成 ChatGPT 二次验证 prompt。等用户明确告知 "生成 Plan v20 ChatGPT 二次验证 prompt" 后启动。
