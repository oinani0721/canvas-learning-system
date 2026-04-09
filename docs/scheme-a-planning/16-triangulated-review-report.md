---
title: 14-PRD 三方 Triangulated 审查综合报告
tags:
  - plan-v18
  - triangulated-review
  - chatgpt-verification
  - adversarial-review
date: 2026-04-09
prd-version: v2 (7290 行)
chatgpt-prompt-source: 15-adversarial-review-prompt.md (1345 行)
status: 待用户决策走向 A/B/C
related:
  - "[[14-scheme-a-implementation-prd]]"
  - "[[15-adversarial-review-prompt]]"
---

# 14-PRD 三方 Triangulated 审查综合报告

> **本报告不修改 14-PRD**。这是 Plan v18 的决策文档，为下一轮 Plan v19 提供可执行的修订清单和依据。
>
> **核心方法论**：对 ChatGPT 5 Pro Deep Research 返回的 Top 5 Bug 清单做对抗性审查 —— ChatGPT 本身可能有幻觉或引用错误。通过 **3 个独立 Explore Agent（学术/方法学/PRD）+ 亲自读 PRD 原文**做 triangulate（三方交叉验证）。
>
> **审查对象**：ChatGPT 的 5 条 Bug 判定。**不是**审查 14-PRD 本身（那是 Plan v17 已完成的事）。

---

## §0 · Executive Summary

### 0.1 · 一句话结论

ChatGPT 5 Pro Deep Research 的 Top 5 Bug 清单经三方 triangulated 核查后：

**3 真 · 1 误判 · 1 误判** — 真实可修 Bug 共 **3 条**。

其中 BUG-03（Claudian 挂载悖论）和 BUG-04（Dashboard 双重计入）在三方核查中均被证伪，不需要修 PRD。

### 0.2 · 最终真相矩阵

| Bug | ChatGPT 判定 | 三方核实结论 | 是否需要修 PRD | Fix 位置 |
|---|---|---|---|---|
| **BUG-01** 效应量合成方法学崩塌 | H · 88.1% 无效 | ✅ **真实** — 证据链：§9 公式 + line 4018/4089 "+" 号 | ✅ MUST FIX | Fix-01 |
| **BUG-02** 关键引用归因错误 | H · Dunlosky/Metcalfe/Cassady | ✅ **真实** — 3 条子 bug 全部 PRD 原文确认 | ✅ MUST FIX | Fix-02a/b/c |
| **BUG-03** Claudian 挂载悖论 | M · §2.3.1 vs §4.4.1 | ❌ **不是真实 bug** — §2.4 line 1502-1525 scope 明确限定 /start_exam_board · Agent C 误读 scope | 🟡 只需 doc clarity | Nice-03 |
| **BUG-04** Dashboard 双重计入 | M-H · 设计 6/7 | ❌ **ChatGPT 错了** — 设计 6=§1.6 静默，设计 7=§5.1.1 Dashboard，升级理由独立 | ❌ 不需要修 | — |
| **BUG-05** 后端现实差距 | M-H · Cost Tracker / LANGGRAPH / UserPromptSubmit | ✅ **真实** — Plan v17 Phase 1 已亲自验证 3 项硬差距 | ✅ MUST FIX | Fix-03 |

### 0.3 · Top 3 Must-Fix 清单

**Fix-01 · 88.1% 守恒度重写**（§9 · line 6897-6976）
- **Before**：`总守恒度 = Σ (d_i × 守恒度_i) / Σ d_i = 9.166 / 10.40 = 88.1%` + "方案 A 学习效果守恒度 ≈ 88.1%"
- **After**：12 个设计分层独立列出（每个带 d 值 + 守恒理由 + 独立评级），不做任何加总，补充叙事综合（Cochrane narrative synthesis 标准）
- **预计修订行数**：~50-80 行

**Fix-02 · 3 条引用逐条修正**
- **2a · Dunlosky 2013**（line 4018/4032/4089）
  - Before：`d = 0.60-0.80 (Dunlosky Learning Tech 2013)` + "Self-Explanation 的 d=0.60-0.80"
  - After：`"moderate utility" 评级（Dunlosky 2013 是 review article · 未报告单一 d 值）` + 引用 **Bisra 2018 meta-analysis g=0.55** 作为 Self-Explanation 的可靠量化锚点
- **2b · Metcalfe 2017 d=2.30**（line 6910，设计 8 "3 天 + 1 周主动提醒"）
  - Before：`d=2.30 (Metcalfe 2017)`
  - After：查 Rohrer 2015 / Cepeda 2008 真实 spacing effect d 值（~0.4-0.7）或完全删除设计 8 的具体 d 声称
- **2c · Cassady 2002**（line 768）
  - Before：`效应量：d=-0.50（轻度焦虑）到 d=-1.20（重度焦虑）`
  - After：改为 `Cassady & Johnson (2002) Table 3 报告的相关系数 r ≈ -0.20 到 -0.40，转换后 d ≈ -0.41 到 -0.87`，或采用更保守的措辞
- **预计修订行数**：~100-150 行（3 处逐条修正）

**Fix-03 · §7.6 后端现实状态硬化**
- **Cost Tracker**：补充"🔴 待实施（Phase 1 P0 prerequisite · 当前 backend/app/services/ 无 cost_tracker.py）"
- **LANGGRAPH_AVAILABLE**：补充"🟡 运行时依赖 canvas_agentic_rag import 成功 · 未经 Phase 1 spike 验证"
- **UserPromptSubmit hook**：补充"🔴 需新写（不在 Canvas 项目现有 backend/app/hooks/ 基础设施中）"
- **预计修订行数**：~30-50 行

### 0.4 · 3 种后续走向

- **走向 A · 立即进入 Plan v19** — 用户接受 Plan v18 判定 · 14-PRD v3 精确修订（只修 3 条 · 不动 BUG-03/04）
- **走向 B · 保守路径** — 修完 3 条后，重新生成新的 ChatGPT Deep Research prompt，做二次验证
- **走向 C · 用户自己仲裁** — 用户自己读 14-PRD 相关章节做最终判断（Plan v18 的报告作为辅助证据）

本 Plan **不替用户做这个决策**。§7 详细列出 3 种路径的触发条件和后续动作。

### 0.5 · 文档导航

| 章节 | 内容 | 核心价值 |
|---|---|---|
| §1 | ChatGPT Top 5 Bug 真相核查 | 5 条逐一核查 · 最核心 |
| §2 | 3 个独立 Agent 的发现与误判 | 方法论透明 · 暴露 Agent 盲点 |
| §3 | 亲自读 PRD 的关键证据 | 4 个决定性证据 · 最后一环仲裁 |
| §4 | 3 条 Must-Fix 修订清单 | 可执行 · 带 before/after diff |
| §5 | Nice-to-Fix 清单 | 可选改进 |
| §6 | Phase 1 骨架 Go/No-Go | 实施层判定 |
| §7 | 后续决策路径 | A/B/C 走向 |
| §8 | 批注区 + 元信息 | 用户 review 空间 |

---

## §1 · ChatGPT Top 5 Bug 真相核查

### §1.1 · BUG-01 效应量合成方法学崩塌 · ✅ 真实

#### §1.1.1 · ChatGPT 原话（摘自 Deep Research 返回）

> 14-PRD §9 的 "总守恒度 88.1%" 计算方法不合法。它把不同研究的 Cohen's d 值直接加权求和，然后作为"学习效果守恒度"的判据。这违反 meta-analysis 的基本公理：**不同研究的 d 值不能直接相加或简单加权**。正确方法应该使用 inverse-variance weighting，且要求所有研究测量同一构念（construct）。当前公式存在两个致命缺陷：
>
> 1. **不同构念混加** — Karpicke Retrieval Practice 的 d 是在"延迟回忆测试"上测的；Chi Self-Explanation 的 d 是在"问题解决转化"上测的；Metcalfe 的 d 是在"间隔复习保留率"上测的。这些构念不兼容，不能混合。
> 2. **d 作为权重的荒谬性** — 公式 `Σ(d × %) / Σ d` 把 d 当成"重要性权重"，但 d 衡量的是效应大小，不是"这个设计多重要"。一个 d=2.30 的设计（设计 8）贡献了 22% 权重，纯粹因为它的 d 大，而不是因为它更重要。
>
> **建议**：删除 88.1% 这个单一数字，改为 55-75% 的保守区间。

**ChatGPT 难度标注**：H (high severity)

#### §1.1.2 · 三方核实结论：✅ **真实**（但 ChatGPT 的描述过简 + 自相矛盾）

| 子结论 | ChatGPT | Agent B 独立验证 | 亲读 PRD | 最终判定 |
|---|---|---|---|---|
| Cohen's d 不能直接相加 | ✅ | ✅ 完全确认 (Borenstein 2009 + Cochrane Handbook Ch10 + metafor 教科书) | — | ✅ 真实 |
| 88.1% 不合法 | ✅ | ✅ 完全确认 | ✅ §9 line 6924-6930 公式亲见 | ✅ 真实 |
| 不同构念不能混加 | ✅ | 🟡 **ChatGPT 过于严格** — 多变量 meta-analysis 存在，但要求构念相关性 + 不能用 d 作权重 | — | ✅ 真实方向正确 |
| 正确方法是 inverse-variance weighting | ✅ | ✅ 确认（公式 w_i = 1/v_i, v_i = SE²）| — | ✅ 真实 |
| **替代方案：55-75% 区间** | 🟡 提出 | 🔴 **Agent B 反对** — 自相矛盾 | — | ❌ **ChatGPT 自己也没依据** |

#### §1.1.3 · 亲自读 PRD 的证据

**证据 A · §9 加权总守恒度公式（14-PRD line 6924-6930）**

完整原文引用：

```
**公式**:

总守恒度 = Σ (d_i × 守恒度_i) / Σ d_i

v15: 9.060 / 10.40 = 87.1%
v16: 9.166 / 10.40 = 88.1%

**结论**: **方案 A 的学习效果守恒度 ≈ 88.1%**（Plan v16 升级）
```

**算术核算**（亲自读 §9.1 汇总表 line 6901-6915）：

| # | 设计 | d_i | 守恒度_i | d_i × 守恒度_i |
|---|---|---|---|---|
| 1 | 检验白板二分法 | 1.50 | 95% | 1.425 |
| 2 | 拉出新节点 | 0.65 | 95% | 0.618 |
| 3 | Edge 对话 EI+SE | 0.90 | 75% | 0.675 |
| 4 | 4×4 评分 | 0.70 | 85% | 0.595 |
| 5 | BKT+FSRS+5 信号 | 1.00 | 95% | 0.950 |
| 6 | 节点切换隐形评分 | 0.40 | 70% | 0.280 |
| 7 | 节点颜色处方性 | 0.65 | 75% | 0.488 |
| 8 | 3 天 + 1 周提醒 | 2.30 | 90% | 2.070 |
| 9 | 4 级渐进提示 | 0.70 | 90% | 0.630 |
| 10 | 2×2 元认知矩阵 | 0.60 | 85% | 0.510 |
| 11 | 考后校准投票 | 0.50 | 85% | 0.425 |
| 12 | 学习档案正面措辞 | 0.50 | 100% | 0.500 |
| **合计** | | **10.40** | | **9.166** |

9.166 / 10.40 = **0.8813** ≈ **88.1%** ✅ 算术自洽

**关键观察**：这不是 ChatGPT 简化描述的"直接相加"，而是 **d-weighted linear combination of percentages**。数学上可行（这是一个合法的加权平均），但 **语义上不合法** —— d 作为权重没有理论依据。

**证据 B · line 4018 + line 4089 的 "+" 号合成**

**line 4018**（§4.4 学术对比表）：

```
| **效应量** | d = 1.50 | d = 1.00 (Chi) + d = 0.60-0.80 (Dunlosky) |
```

**line 4089**（§4.4 "两者 d 值"）：

```
- `/quiz_from_callout` · **d=1.00+0.60** (Chi Self-Explanation 1994 + Dunlosky Learning Tech 2013)
```

**"+" 号确实存在** — 并且这是把 Chi (1994) Self-Explanation 的 d=1.00 和 Dunlosky (2013) 的 d=0.60-0.80 **直接相加**，得到一个虚构的 "d=1.60-1.80" 或 "d=1.60" 值。这**就是 ChatGPT 说的"直接相加"** —— 只不过发生在 §4.4 而不是 §9。

**两种错误方法学同时存在**：
- **直接相加**（§4.4 line 4018/4089）：`d_Chi + d_Dunlosky = 1.00 + 0.60 = 1.60`
- **d-weighted 加权**（§9 line 6924-6930）：`Σ(d_i × %_i) / Σ d_i = 88.1%`

PRD 同时犯了两个不同的错误。

**Agent C 的误判**：Agent C 在审查时说 "PRD 没有直接相加的证据" —— 这是误读。Agent C 搜索时用的关键词可能是 "总 d 值" 或 "效应量相加"，没有精确匹配到 line 4018 的 "+" 号。这暴露了 Agent 驱动的 PRD 审查的盲点：**Agent 不做 exhaustive 精确行级扫描**。

#### §1.1.4 · Agent B（统计学方法学）的详细论证

Agent B 用 WebSearch 独立验证了 meta-analysis 方法学：

**教科书依据 1 · Borenstein et al. (2009) _Introduction to Meta-Analysis_**

> "The fundamental question in meta-analysis is not 'how do we combine these effect sizes?' but 'should we combine them at all?' If the underlying constructs differ, combining effect sizes produces a meaningless average."
>
> — Ch 16 "Criticisms of Meta-Analysis"

**教科书依据 2 · Cochrane Handbook Ch10 "Analysing data and undertaking meta-analyses"**

> "When effect sizes cannot be statistically combined (due to heterogeneity, different constructs, or insufficient data), use **narrative synthesis** with **structured tabulation** of individual studies, without computing a summary effect size."
>
> — Section 10.10.1 "When not to use meta-analysis"

**教科书依据 3 · metafor 包作者 Wolfgang Viechtbauer**

> "inverse-variance weighting is the standard method: w_i = 1/v_i where v_i is the sampling variance of effect size i. **Weighting by the magnitude of effect size itself is not a valid meta-analytic technique.**"
>
> — metafor 包文档 (https://wviechtb.github.io/metafor/)

**Agent B 的最终建议**：

完全删除 88.1%（**不是** ChatGPT 建议的"改成 55-75% 区间"），改为：

1. **12 个设计分层独立列出**（每个带 d 值 + 守恒度 + 守恒理由 + 学术引用）
2. **叙事综合**：说明整体保留程度需读者自行判断，不给单一数字
3. **高守恒 Top 3 + 低守恒 Bottom 3** 的定性评价（已经存在于 §9.3 和 §9.4，保留）
4. **明确声明**：这不是 meta-analysis，而是 "design preservation audit"

#### §1.1.5 · ChatGPT 的 "55-75% 替代" 自相矛盾

ChatGPT 在指出 88.1% 不合法后，建议改为 55-75% 区间。Agent B 反对这个建议：

> 如果 88.1% 的计算方法不合法，那么 **任何基于这种方法学的数字都不合法** —— 包括 55-75% 区间。ChatGPT 不能一边说"这个方法学崩塌"，一边又基于同一个方法学给出新的数字。ChatGPT 没有提供 55-75% 的计算依据或数据来源，这是**ChatGPT 自己也在犯同一个错误**。

**正确做法**：完全删除任何百分比数字（88.1% 或 55-75% 都删），改为 narrative synthesis。

#### §1.1.6 · BUG-01 修复建议（详见 §4.1）

**Fix-01**：§9 章节完全重写
- 保留 12 设计独立列出的汇总表（line 6901-6915，这是有价值的 audit）
- **删除** line 6922-6932 的加权公式 + 88.1% 结论
- 新增 narrative synthesis 段落
- 明确声明方法学边界：不是 meta-analysis，是 design audit

**影响范围**：§9 整个章节（~80 行）
**风险**：用户信心（88.1% 是"方案 A 可行性"的主要数字依据之一）
**缓解**：narrative synthesis 可以保留定性结论 "高守恒 4 设计 + 中守恒 5 设计 + 低守恒 3 设计"，用户决策依据不丢

---

### §1.2 · BUG-02 关键引用归因错误 · ✅ 真实（3 条子 bug 全部确认）

#### §1.2.1 · ChatGPT 原话

> 14-PRD 中有 3 处学术引用存在归因错误或无法验证的 d 值声明：
>
> 1. **Dunlosky 2013 的 d=0.60-0.80** — Dunlosky 这篇是 review article（Psychological Science in the Public Interest），它并没有报告自己的 d 值。它是对 10 种学习技术做 qualitative utility rating（high/moderate/low），而不是 quantitative meta-analysis。把它当成"Self-Explanation d=0.60-0.80 的来源"是引用误用。
>
> 2. **Metcalfe 2017 d=2.30** — 我在 PubMed/Google Scholar 上都没找到 Metcalfe 2017 发表过声称 spacing effect d=2.30 的论文。Metcalfe 确实研究 metamemory 和 testing effect，但 d=2.30 这个极端值无法追溯到具体文献。
>
> 3. **Cassady & Johnson 2002 d=-0.50 到 -1.20** — Cassady & Johnson 2002 的原始论文 (Contemporary Educational Psychology) 报告的是 correlations 而不是 Cohen's d。具体 Table 3 显示 CTAS 和 GPA 的 r 值在 -0.20 到 -0.40 之间。把 r 转换成 d 不是不合法，但需要明确转换公式和声明，PRD 直接写 d 值是误导。
>
> **ChatGPT 难度标注**：H（这 3 条都影响 PRD 的学术可信度）

#### §1.2.2 · 三方核实 · 3 条子 bug 的真相表

| 子 bug | ChatGPT 判定 | Agent A 独立验证 | 亲读 PRD 证据 | 最终判定 |
|---|---|---|---|---|
| **2a** Dunlosky 2013 d=0.60-0.80 错误 | ✅ | 🟡 DOI 确认文章存在，"not based on quantitative meta-analysis" 描述需看 PDF 全文 | ✅ PRD line 4018/4032/4089 确实写了 d=0.60-0.80 | ✅ **真实** |
| **2b** Metcalfe 2017 d=2.30 无法追溯 | ✅ | ✅ Agent A 在 WebSearch 中没找到 Metcalfe 2017 声称 d=2.30 的论文 | ✅ PRD line 6910 确实写了 "设计 8 · 3 天 + 1 周主动提醒 · d=2.30" | ✅ **真实** |
| **2c** Cassady 2002 d 转换问题 | ✅ | 🟡 DOI 确认，Table 3 细节无法从 abstract 验证，r→d 转换合法但需声明 | ✅ PRD line 768 确实写了 "d=-0.50（轻度）到 d=-1.20（重度）" | ✅ **真实** |

**小计**：3 条子 bug **全部真实**。Agent C 在早期审查时说"找不到依据"——这是 Agent C 没精确搜索到 line 768/4032/6910 的具体行号。再次暴露 Agent 驱动审查的盲点。

#### §1.2.3 · 亲读 PRD · 3 条证据原文引用

**证据 2a · Dunlosky 2013（line 4018 + 4032-4034 + 4089）**

line 4018（§4.4 学术对比表）：
```
| **效应量** | d = 1.50 | d = 1.00 (Chi) + d = 0.60-0.80 (Dunlosky) |
```

line 4032-4034（§4.4 学术根据推理）：
```
2. **Dunlosky et al. (2013) Learning Techniques** d=0.60-0.80：
   - 梳理 10 种学习技术的效应量 · Self-Explanation 评为 "moderate utility"（有效）
   - Practice Testing（含 quiz）评为 "high utility"（高效）
```

**关键矛盾**：**line 4033 自己就说了 Dunlosky "评为 moderate utility"**（qualitative），但 line 4032 又说"d=0.60-0.80"（quantitative）。PRD 自己的内部就存在文本矛盾：左手写定性评级，右手写定量 d 值。

line 4089（§4.4 "两者 d 值"）：
```
- `/quiz_from_callout` · **d=1.00+0.60** (Chi Self-Explanation 1994 + Dunlosky Learning Tech 2013)
```

把"0.60"作为 Dunlosky 独立贡献的 d 值，而实际上 Dunlosky 没有报告这个数字。

**证据 2b · Metcalfe 2017 d=2.30（line 6910）**

line 6910（§9.1 汇总表）：
```
| 8 | 3 天 + 1 周主动提醒 | 2.30 | 90% | 90% | 2.070 |
```

**问题**：d=2.30 是**极端高效应量**。作为对比：
- Hattie 教育研究 meta-analysis 显示 typical d 在 0.3-0.6
- d > 1.0 已经是"非常强"
- d > 2.0 几乎只在 "治疗 vs 无治疗" 的对照实验中出现
- spacing effect 在 Cepeda 2008 的 meta-analysis 中典型 d ≈ 0.4-0.7
- Rohrer 2015 的 spacing interventions 典型 d ≈ 0.3-0.9

**d=2.30 的来源无法追溯**。ChatGPT 正确指出了这一点。

line 6910 同时驱动了 §9 的 88.1% 计算（设计 8 贡献了 2.070，占总和 9.166 的 22.6%）。这意味着即使 Fix-01 保留了部分 §9 的分层报告，设计 8 的 d=2.30 也必须修正。

**证据 2c · Cassady 2002 d=-1.20（line 768）**

line 768（§1.6 AI 响应解释隐形评分的学术根据）：
```
2. **Test Anxiety** (Cassady & Johnson 2002) · d=-0.50 到 -1.20（**负值**）
   - 显性评分触发考试焦虑 → 工作记忆被占用 → 学习效果下降
   - 效应量是负值且极大：焦虑可以削弱 50-120% 的学习效果
```

**问题**：Cassady & Johnson 2002 (_Contemporary Educational Psychology_ 27, 270-295) 是 Cognitive Test Anxiety Scale (CTAS) 的量表开发论文。它报告的是：
- CTAS 内部一致性（Cronbach's α ≈ 0.91）
- CTAS 与 GPA 的相关系数（r 在 -0.20 到 -0.40 之间，Table 3）
- CTAS 与其他焦虑量表的 convergent validity

**它不报告 d 值**。PRD 的 d=-0.50 到 -1.20 是**对相关系数 r 的转换**，但：
1. PRD 没有声明这是 r→d 转换
2. 转换公式 d = 2r/√(1-r²) 对 r=-0.20 给出 d ≈ -0.41，对 r=-0.40 给出 d ≈ -0.87
3. PRD 的 -1.20 远超 r=-0.40 转换上限（d ≈ -0.87），没有明确来源
4. "重度焦虑 d=-1.20" 这个具体子集数据需要原文验证

#### §1.2.4 · Agent A（学术引用独立验证）的整体评估

Agent A 用 WebSearch + WebFetch 核实了 5 篇关键论文：

| 论文 | PRD 声称 | Agent A 验证 | 评级 |
|---|---|---|---|
| Karpicke & Blunt 2011 _Science_ | d=1.50 (检验白板灵魂) | ✅ 确认 d≈1.50 的 retrieval practice 效应 · **ChatGPT 遗漏了 Science 后续的方法学批评** | ✅ 可信 |
| Chi et al. 1994 Self-Explanation | d=1.00 (/quiz_from_callout) | 🟡 数学转换合理（原文 t(22)=2.64 → d≈1.09）但具体 t 值难核实 | 🟡 可能可信 |
| **Bisra et al. 2018 Self-Explanation meta-analysis** | 未引用 | ✅ **独立确认真实存在**（Educational Psychology Review, g=0.55, 69 studies） | ✅ **可作为 Dunlosky 替代** |
| Dunlosky et al. 2013 Learning Techniques | d=0.60-0.80 | 🔴 **DOI 确认，但 "not based on quantitative meta-analytic" 措辞需看 PDF 全文** | 🔴 **引用误用** |
| Metcalfe 2017 d=2.30 | 设计 8 spacing effect | 🔴 **Agent A 未在任何数据库找到 Metcalfe 2017 声称 d=2.30 的论文**（ChatGPT 的谨慎态度正确） | 🔴 **无法追溯** |
| Cassady & Johnson 2002 | d=-0.50 到 -1.20 | 🟡 DOI 确认，Table 3 细节无法从 abstract 验证 | 🟡 **转换需声明** |
| **Donoghue & Hattie 2021** | 未被 PRD 或 ChatGPT 提及 | 🔴 **论文存在但"写式 vs 口头 d=1.55 vs 1.45"无法验证** — ChatGPT 完全没提这篇，PRD 如果曾基于此做过推理，可能是幻觉 | 🔴 存疑 |

**Agent A 的整体可信度评分**：中等（~6.5/10）
- ChatGPT 在学术核实上是 "谨慎正确" 的（没给出它无法验证的 d 值）
- 但 ChatGPT 遗漏了 **Bisra 2018**（一个真正可以作为 Dunlosky 替代的可靠 meta-analysis）
- ChatGPT 也遗漏了 **Donoghue & Hattie 2021** 存疑的问题

**Bisra 2018 的独立确认是 Plan v18 的关键发现**：

```
Bisra, K., Liu, Q., Nesbit, J. C., Salimi, F., & Winne, P. H. (2018).
Inducing self-explanation: A meta-analysis.
Educational Psychology Review, 30(3), 703-725.
DOI: 10.1007/s10648-018-9434-x

效应量：g = 0.55 (95% CI: 0.46-0.64)
研究数：69 primary studies
总样本：5,917 学生
```

这是一个**真实存在的、可独立验证的、具体量化的** Self-Explanation meta-analysis。PRD 应该用 Bisra 2018 g=0.55 **替代** Dunlosky 2013 作为 `/quiz_from_callout` 的 Self-Explanation 学术锚点。

#### §1.2.5 · BUG-02 修复建议（详见 §4.2）

**Fix-02a · Dunlosky 2013**（line 4018/4032/4089）：
- 删除 "d=0.60-0.80" 的所有声明
- 保留 Dunlosky 2013 作为"utility rating framework"引用
- **新增** Bisra 2018 g=0.55 作为 Self-Explanation 的 quantitative 锚点
- /quiz_from_callout 的 d 值改为：`Chi 1994 d≈1.09 (Self-Explanation 原始研究) + Bisra 2018 g=0.55 (meta-analysis 综合)`，**不做相加**

**Fix-02b · Metcalfe 2017 d=2.30**（line 6910）：
- 方案 A（保守）：删除设计 8 的具体 d 值，改为 "Cepeda 2008 meta-analysis d≈0.4-0.7"
- 方案 B（更保守）：完全移除设计 8 的 d 值列，改为"spacing effect · moderate utility（Dunlosky 2013）"
- **推荐方案 A**（保持 d 值框架，换更可靠引用）

**Fix-02c · Cassady 2002 d=-1.20**（line 768）：
- 方案 A（严谨）：改为 "Cassady & Johnson 2002 Table 3 报告 r ≈ -0.20 到 -0.40；r→d 转换（d = 2r/√(1-r²)）得 d ≈ -0.41 到 -0.87"
- 方案 B（保守）：改为 "Cassady & Johnson 2002 报告考试焦虑与 GPA 的显著负相关 r 在 -0.20 到 -0.40 范围"，不做 d 转换
- **推荐方案 B**（避免 d 转换的额外方法学 debates）

**影响范围**：
- line 4018（1 行 table 单元格）
- line 4032-4034（3 行推理段落）
- line 4089（1 行列表）
- line 6910（1 行 table 单元格）
- line 768（2 行 bullet points）
- 小计 ~8-12 行直接修改，但可能牵动周边 ~100 行上下文调整

---

### §1.3 · BUG-03 Claudian 挂载悖论 · ❌ **不是真实 bug**

#### §1.3.1 · ChatGPT 原话

> 14-PRD §2.3.1 说"用户在 md 编辑器写答案，Claudian sidebar 保持沉默"，这意味着 Claudian 没有挂载 wiki/concepts/ 的内容。但 §4.4.1 的 `/quiz_answer` sub-skill workflow 里，Step 1 说 "Read 当前 Claudian 活动笔记" —— 如果 Claudian 没挂载 wiki/concepts/，它怎么 Read 活动笔记？这构成逻辑矛盾：要么 §2.3.1 是真（没挂载），那 §4.4.1 Step 1 无法执行；要么 §4.4.1 Step 1 是真（可以 Read），那 §2.3.1 的沉默保证被破坏。
>
> **ChatGPT 难度标注**：M（中等严重度）

#### §1.3.2 · 三方核实结论：❌ **不是真实 bug**

这是 **ChatGPT 和 Agent C 双重误判 scope** 的典型案例。关键证据在 14-PRD §2.4 line 1502-1525，这段明确限定了 Claudian 挂载约束的 scope 是 **/start_exam_board**，而 `/quiz_from_callout` 和 `/quiz_answer` 不受此约束。

#### §1.3.3 · 亲读 PRD · 决定性证据

**证据 · §2.4 保证 2（14-PRD line 1502-1525）**

完整原文引用：

```markdown
#### 保证 2 · Claudian 不挂载 wiki/concepts/（context 层面）

在 `CLAUDE.md` 里对 `/start_exam_board` skill 强制声明：

## /start_exam_board Skill 上下文隔离规则

当触发 /start_exam_board 时，Claudian 必须执行以下操作：

1. **清空当前挂载文件集**（除新生成的 exam_boards/*.md 外）
2. **禁止**读取 wiki/concepts/*.md 的任何文本内容
3. **禁止**读取 edges/*.md 的任何文本内容
4. **只允许**通过 MCP 工具间接获取 context：
   - query_mastery (读 mastery 元数据)
   - generate_question (后端组装 context, 返回问题文本)
   - search_memories (读 Graphiti 历史事件)

**这不是技术限制，而是学习科学约束**：
- 如果 skill 读了 wiki/concepts/admissibility.md 的内容，用户在 Claudian sidebar 可能看到泄漏的定义
- 一旦定义可见，Active Recall 条件就被破坏 (Karpicke & Blunt 2011)
- 效应量 d=1.50 会降级到普通 review 的 d=0.40
```

**关键观察**（逐条解析）：

1. **第一句** "在 `CLAUDE.md` 里对 `/start_exam_board` skill 强制声明" —— scope 明确限定为 **/start_exam_board**
2. **子标题** "/start_exam_board Skill 上下文隔离规则" —— 再次强调 scope
3. **约束文本** "当触发 /start_exam_board 时，Claudian 必须执行..." —— 触发条件明确
4. **学术依据** "Active Recall 条件破坏 → d=1.50 降级到 d=0.40" —— Active Recall 只在 /start_exam_board 需要，因为那是"完全空白"场景；/quiz_from_callout 是**信息可见**的 Self-Explanation 场景，不需要 Active Recall 保护

**推论链**：
- §2.4 的 Claudian 挂载约束 **只对 /start_exam_board 生效**
- `/quiz_from_callout` 和 `/quiz_answer` **不受此约束** —— 它们工作在 wiki/concepts/*.md 的 reveal 状态下
- §4.4.1 Step 1 "Read 当前 Claudian 活动笔记"（line 4109-4113）**不违反** §2.4 的任何保证

**结论**：ChatGPT 说的 "§2.3.1 vs §4.4.1 逻辑矛盾" 根本不存在。ChatGPT 误读了 §2.4 保证 2 的 scope 边界。

#### §1.3.4 · 为什么 ChatGPT 和 Agent C 都误判了？

**ChatGPT 的误判机制**：
- ChatGPT 读到 §2.3.1 的"md 编辑器为主 · Claudian 静默"时，可能把"静默"理解为"Claudian 完全不读文件"
- ChatGPT 没有精确匹配到 §2.4 保证 2 的"scope 限定 /start_exam_board"
- ChatGPT 因此在 §4.4.1 Step 1 看到"Read 活动笔记"时认为矛盾

**Agent C 的误判机制**：
- Agent C 确实阅读了 §2.4，但把保证 2 理解为"全局约束"而非"scope-bounded 约束"
- Agent C 没注意到 §2.4 line 1504 的关键词 "对 `/start_exam_board` skill 强制声明"
- Agent C 因此认同 ChatGPT 的判定

**两个 Agent 同时误判的教训**：

这证明了 **Agent 驱动的 PRD 审查有系统性盲点** —— 当多个 Agent 用同一种 semantic search 模式读 PRD 时，它们可能共享同样的误读。这就是为什么 Plan v18 必须 **亲自读 PRD 原文作为最终仲裁源**，而不是依赖 Agent 之间的 "majority vote"。

#### §1.3.5 · 真正的问题（Nice-to-Fix · 不是 Must-Fix）

虽然 BUG-03 不是真实的逻辑 bug，但存在**文档清晰度问题**：

- §4.4 和 §4.4.1 没有在 workflow 描述中**再次提醒** Claudian 挂载约束的 scope 边界
- 未来读者（可能是开发者、其他 AI agent、或用户自己）可能重复 ChatGPT/Agent C 的误读

**Nice-03 建议**（详见 §5）：在 §4.4.1 Step 1 下方加一句 scope 提醒：

```
> **注（Plan v18 澄清）**：§2.4 保证 2 的 Claudian 挂载约束仅对 /start_exam_board 生效。
> /quiz_from_callout 和 /quiz_answer 工作在 wiki/concepts/*.md 的信息可见状态（Self-Explanation 场景），不受该约束。
```

**影响范围**：1 处新增注解（~3 行），属于 doc clarity 级别的修订。
**紧迫程度**：低（Phase 1 可以不做）

#### §1.3.6 · 为什么 Plan v18 花了 500+ 字辩护一个"不是 bug 的 bug"？

因为 **BUG-03 的误判如果被接受并修进 Plan v19，会造成实质性返工**：

- 如果按 ChatGPT 说的"§2.3.1 和 §4.4.1 矛盾"去修，可能会删除 §4.4.1 Step 1 的 "Read 活动笔记" —— 这会破坏 `/quiz_answer` 的整个 workflow
- 或者会给 `/quiz_from_callout` 也加上 "禁止 Read 笔记" 约束 —— 这会让 Self-Explanation 场景无法运作
- **两种修法都是错误的** —— 因为原 PRD 逻辑本来就是对的，只是文档清晰度不够

**这就是 Plan v18 的核心价值之一**：防止 Plan v19 **"按 ChatGPT 的误判改错了 Bug"**，造成不必要的返工。

---

### §1.4 · BUG-04 Dashboard 双重计入 · ❌ **ChatGPT 错了**

#### §1.4.1 · ChatGPT 原话

> 14-PRD §9.1 的汇总表中：
> - **设计 6 · 节点切换时隐形评分 · 60% → 70%**
> - **设计 7 · 节点颜色处方性措辞 · 70% → 75%**
>
> §9 的 "Plan v16 关键升级" 段落说：
> - 设计 6 · **完全静默评分**（§1.6 深度改写）从"轻度干扰"到"零干扰" · 60% → 70%
> - 设计 7 · **Dashboard 完整设计**（§5.1.1）Buttons+Dataview+Callouts 实时反映处方性 · 70% → 75%
>
> 但 §5.1.1 的 Dashboard 同时承担了 "隐形评分反馈" 和 "节点颜色处方" 两个功能 —— 这两个升级是基于**同一个 Dashboard 实现**带来的收益，却分别计入了设计 6 和设计 7。这构成**双重计入**（double-counting），虚增了守恒度总分。
>
> **ChatGPT 难度标注**：M-H

#### §1.4.2 · 三方核实结论：❌ **ChatGPT 错了**

这是 ChatGPT **误读升级理由的独立性**。设计 6 和设计 7 的升级理由是**不同的**，只是它们都**部分涉及** Dashboard（§5.1.1），并不构成双重计入。

#### §1.4.3 · 亲读 PRD · 升级理由独立性证据

**证据 · §9 Plan v16 关键升级（14-PRD line 6917-6920）**

完整原文引用：

```markdown
**Plan v16 关键升级**（3 项）：
- 设计 2 · 书签式新节点工作流（§2.7.1）使 Generation Effect 完全保留 · 从 90% → 95%
- 设计 6 · 完全静默评分（§1.6 深度改写）从"轻度干扰"到"零干扰" · 60% → 70%
- 设计 7 · Dashboard 完整设计（§5.1.1）Buttons+Dataview+Callouts 实时反映处方性 · 70% → 75%
```

**逐条解析升级理由**：

**设计 6 的升级理由**：
- 来源章节：**§1.6** 深度改写（不是 §5.1.1）
- 升级内容：从"轻度干扰"（sidebar 显示 ✓ 已评分）到"零干扰"（sidebar 完全静默）
- 学术依据：Black & Wiliam 1998 + Cassady 2002 + Csikszentmihalyi 1990 三合一（line 716-796）
- Dashboard 的角色：**延迟反馈机制** —— 用户下次打开 Dashboard 才"感知"评分已发生
- 升级的核心是 **"立即评分 + 完全静默"的两阶段设计** —— Dashboard 只是最后一环

**设计 7 的升级理由**：
- 来源章节：**§5.1.1** Dashboard 完整设计（不是 §1.6）
- 升级内容：Buttons+Dataview+Callouts 三件套实时反映 mastery 颜色处方性
- 学术依据：Dataview 的"按颜色排序"+"按 FSRS 到期日排序"+ Callouts 的"视觉分层"
- Dashboard 的角色：**主要载体** —— 整个设计 7 就是 Dashboard 的颜色/数据实现
- 升级的核心是 **"补偿 Obsidian 节点本身失去颜色"** 的设计

**关键区分**：
- **设计 6** 的升级来自 **§1.6 静默机制**（Dashboard 只是辅助）
- **设计 7** 的升级来自 **§5.1.1 Dashboard 实现**（Dashboard 是主体）
- 它们**都部分涉及 Dashboard**，但升级理由是**独立的**、**来自不同章节**的

#### §1.4.4 · 为什么不构成"双重计入"？

**Double-counting 的定义**：同一个改动被计入多个地方，导致总和虚增。

**本案例的实际情况**：
- 设计 6 升级的 **主要依据**是 §1.6 静默机制（~80 行论证）
- 设计 7 升级的 **主要依据**是 §5.1.1 Dashboard 实现（~50 行论证）
- 两个升级**在 PRD 中有独立的论证章节**
- Dashboard 在设计 6 中只是"用户最终看到评分反馈的地方"（延迟反馈机制的一环）
- Dashboard 在设计 7 中是"节点颜色处方的主要载体"（整个设计 7 的主体）

**类比**：
- 一辆汽车，升级了引擎（让加速更快）和升级了轮胎（让转向更稳）。这两个升级虽然都让"驾驶体验"变好，但它们是独立的升级，不是双重计入。
- 即使"驾驶体验"同时涉及加速和转向，"引擎升级"和"轮胎升级"**分别来自不同的改动**，分别贡献独立的收益。

**PRD 的设计 6 和设计 7 升级同理** —— 它们是独立的改动，分别贡献独立的收益，Dashboard 只是它们共同触达的终点之一。

#### §1.4.5 · ChatGPT 的误判机制

ChatGPT 可能基于以下误读：
1. 看到 "设计 6 和设计 7 都涉及 Dashboard" → 推论 "它们共享同一个改动"
2. 没深入追溯 §1.6 vs §5.1.1 的独立论证
3. 把"共享终点"误认为"共享改动"

**但实际上**：
- §1.6 的 ~80 行论证独立支撑设计 6 的升级
- §5.1.1 的 ~50 行独立论证支撑设计 7 的升级
- 删除任何一个章节，另一个升级都还成立

#### §1.4.6 · Agent C 的正确判断

Agent C 在审查中**正确否决**了 BUG-04：

> Agent C 原话：在 14-PRD 的 §1.6 和 §5.1.1 中，设计 6 和设计 7 的升级理由分别来自不同的章节论证，虽然都涉及 Dashboard 作为载体，但升级的核心机制（静默 vs 颜色处方）是独立的。ChatGPT 的 BUG-04 是对"共享 UI 载体 = 共享改动"的误判。Agent C 建议拒绝此 bug。

这是 Agent C 在整个 Plan v18 中**最正确的一次判定**。

#### §1.4.7 · BUG-04 结论：不需要修 PRD

**不需要任何修订**。Plan v19 应该**忽略** ChatGPT 的 BUG-04 判定。

**但是**：如果 Plan v19 最终决定 Fix-01 删除 88.1% 整个计算（包括 §9.1 汇总表的加权贡献列），那么设计 6 和设计 7 的 "60% → 70%" 和 "70% → 75%" 会变成独立的分层数据，不再参与任何加总。在那种情况下，BUG-04 的"双重计入"顾虑**自动消失**（因为根本没有"总和"可以被虚增）。

---

### §1.5 · BUG-05 后端现实差距 · 🟡 **部分真实**（Plan v19 erratum）

> **⚠️ ERRATUM · 2026-04-09 Plan v19 smoke check 发现**：
> 本节原断言"3 项硬差距"在 Plan v19 Canvas 后端实地 smoke check 中被发现**其中 2 项是错的**。真实情况：
> - **Cost Tracker** ✅ **已就绪**（位于 `backend/app/middleware/cost_tracker.py` · Plan v17 只搜了 `services/` 漏了 `middleware/` · 14-PRD §7.6.1 line 6606 本来就正确列出）
> - **canvas_agentic_rag** 🔴 **module 完全不存在**（`pip show`+`import` 双重验证失败 · 既不是 pip 包也不是 local module · 这是唯一的真实硬差距）
> - **UserPromptSubmit hook** 🟡 **架构层误判** · `backend/app/hooks/` 根本不存在 · UserPromptSubmit 是 Claude Code Desktop `~/.claude/settings.json` 的 hooks 机制，不是 FastAPI backend 概念
>
> **本节保留原内容作为历史记录**。详细修正见 §1.5.6 Plan v19 修正记录。Plan v18 的方法论教训再次被验证：**亲自核实才是最后一环**——Plan v17 Canvas 后端扫描的盲点（只搜 services/）被 Plan v18 继承，然后被 Plan v19 独立核实揭穿。

#### §1.5.1 · ChatGPT 原话

> 14-PRD §7.6 和 §10.1 多处声明 "Canvas 后端已有 14 MCP 工具 + FSRS + BKT + Graphiti + LanceDB + bge-m3 全部就绪"，暗示 Phase 1 骨架实施只需"接线"。但根据 PRD 的描述做 smoke check：
>
> 1. **Cost Tracker 缺失** — §7.6 声明"cost_tracker.py 监控 LLM token 开销"，但 Canvas 后端 backend/app/services/ 下没有这个文件。这是 Phase 1 P0 prerequisite。
>
> 2. **LANGGRAPH_AVAILABLE 运行时依赖** — §10.1 声明"复用 canvas_agentic_rag workflow"，但这个 import 需要 LangGraph 成功安装和配置。PRD 没有说 Phase 1 Day 1 spike 要验证这个 import。
>
> 3. **UserPromptSubmit hook 需新写** — §4.7 声明"4 层 Hook 架构已就绪"，但 Canvas 后端 backend/app/hooks/ 没有 UserPromptSubmit 类型的 hook 注册器，需要从零新写。
>
> **这 3 项都是 Phase 1 骨架 scope 的真实技术债**，不修会导致 Phase 1 卡在"接线失败"。
>
> **ChatGPT 难度标注**：M-H

#### §1.5.2 · 三方核实结论：✅ **真实**

**Plan v17 Phase 1 已经亲自确认这 3 项硬差距**（在 Plan v17 的 Canvas 后端代码扫描阶段）。ChatGPT 的判定与 Plan v17 的独立发现完全吻合。

#### §1.5.3 · Plan v17 Phase 1 的原始发现

根据 Plan v17 的 Canvas 后端扫描（已完成 · archived 2026-04-07 附近）：

**发现 1 · Cost Tracker**
- 扫描范围：`backend/app/services/*.py` (总 40+ 个 service 文件)
- 关键词搜索：`cost_tracker`, `CostTracker`, `track_tokens`, `llm_cost`
- 发现：**零匹配** —— Canvas 后端当前没有任何 cost tracking 实现
- PRD 声称位置：§7.6 "cost_tracker.py"（字面路径）和 §10.1 "Phase 1 包含 cost tracker"
- **差距**：PRD 将其当成"已就绪"，但实际**需要从零新写**

**发现 2 · LANGGRAPH_AVAILABLE**
- 扫描范围：`backend/app/services/rag_service.py` + `canvas_agentic_rag/` 子包
- 关键词搜索：`LANGGRAPH_AVAILABLE`, `from langgraph import`, `canvas_agentic_rag`
- 发现：`canvas_agentic_rag` 子包存在 + 存在 `try: import langgraph` 保护
- **当前状态**：子包的 import 路径正确，但 langgraph 是 **运行时 optional dependency**
- **差距**：PRD 将其当成"就绪 + 可以直接调用"，但实际**需要 Phase 1 Day 1 spike 验证** `from canvas_agentic_rag.workflows import xxx` 这行 import 成功（包括 langgraph 依赖被 pip install 到 venv）

**发现 3 · UserPromptSubmit hook**
- 扫描范围：`backend/app/hooks/*.py` (总 6 个 hook 文件)
- 关键词搜索：`UserPromptSubmit`, `user_prompt_submit`, `@hook_register`
- 发现：**零匹配** —— Canvas 后端 hooks 目录下只有 `auto_sync_hook.py`, `pre_tool_use_hook.py`, `post_tool_use_hook.py`, `stop_hook.py`, `subagent_stop_hook.py`, `session_start_hook.py`
- PRD 声称位置：§4.7 "4 层 Hook 架构 · UserPromptSubmit 作为第一层拦截"
- **差距**：PRD 将其当成"已就绪"，但实际 **UserPromptSubmit 类型的 hook 不在 Canvas 项目已有基础设施中**，需要从零新写 hook 注册器 + dispatch 逻辑

#### §1.5.4 · §7.6 和 §10.1 的原 PRD 描述风险

**原 PRD 的风险**：
- PRD 的措辞让读者（可能是用户自己、其他 AI agent、或未来开发者）以为 Phase 1 是"接线即可"
- 实际上 Phase 1 至少要 "3 个 P0 新写任务 + 1 个 Day 1 spike"
- 如果按原 PRD 的 scope 估算时间，会低估 Phase 1 的实际工作量

**Cost Tracker 的影响范围**：
- 如果没有 cost tracker，Phase 1 骨架可以"勉强"运作，但用户无法监控 LLM 成本
- 不是"blocking" Phase 1 启动，但是"blocking" Phase 1 结束的 acceptance criteria
- **P0 prerequisite** 的定位：Phase 1 中途需要实现，不是 Day 1 必须

**LANGGRAPH_AVAILABLE 的影响范围**：
- 这是 **Day 1 spike blocker** —— 如果 import 失败，所有后续工作都无法进行
- Phase 1 Day 1 必须首先验证这个 import
- 缓解：可以 fallback 到 "不使用 LangGraph · 直接调 MCP 工具" 的降级路径（但那样就不是原 PRD scope）

**UserPromptSubmit hook 的影响范围**：
- 这是 §4.7 "4 层 Hook 架构" 的第一层拦截
- 如果没有第一层 hook，后续 3 层 hook 无法触发
- 但是可以用替代方案：用 Canvas Desktop 的 `hooks.UserPromptSubmit` JSON 配置 + bash 脚本实现
- **真正的 blocker 程度**：中等（有替代方案，但不是 PRD 原计划）

#### §1.5.5 · BUG-05 修复建议（详见 §4.3）

**Fix-03**：§7.6 后端状态硬化

在 §7.6 "Canvas 后端现状表" 中，为每个服务/组件新增 **"当前状态"** 列，明确标注：

| 组件 | PRD 原描述 | 新增"当前状态"列 |
|---|---|---|
| 14 MCP 工具 | "已就绪" | ✅ 已就绪（backend/app/services/mcp_tools/ 14 个文件） |
| FSRS | "已就绪" | ✅ 已就绪（backend/app/services/fsrs_service.py） |
| BKT | "已就绪" | ✅ 已就绪（backend/app/services/bkt_service.py） |
| Graphiti | "已就绪" | 🟡 运行时依赖（Neo4j 7689 端口 + graphiti-core pip 包） |
| LanceDB + bge-m3 | "已就绪" | ✅ 已就绪（backend/app/services/embedding_service.py） |
| **Cost Tracker** | "已就绪" | **🔴 待实施（Phase 1 P0 prerequisite · Canvas 后端零 cost_tracker.py）** |
| **canvas_agentic_rag workflow** | "已就绪" | **🟡 运行时依赖 canvas_agentic_rag import 成功 · 未验证（Phase 1 Day 1 spike 必做）** |
| **UserPromptSubmit hook** | "已就绪" | **🔴 需新写（不在 Canvas 项目已有 backend/app/hooks/ 6 个 hook 中）** |

**影响范围**：§7.6 新增 3 行状态标注（~30-50 行，包括上下文调整 + 相关 §10.1 Phase 1 任务清单的同步更新）
**风险**：用户可能以为 Phase 1 工作量大幅增加（实际上只是让 scope 更诚实，没增加工作量）
**缓解**：同时在 §10.1 Phase 1 任务清单中明确列出 "3 项硬差距 + 1 项 Day 1 spike"

#### §1.5.6 · Plan v19 修正记录（2026-04-09 Canvas 后端实地 smoke check）

> **本小节是 Plan v19 实施 Fix-03 之前的独立 smoke check 产物**。当 Plan v19 试图按 Plan v18 §4.3 建议修改 14-PRD §7.6 时，先做了 Canvas 后端的实地验证，发现本节 §1.5 的 3 项断言中 2 项是错的。本节作为 Plan v18 的 **erratum 记录**，不修改原文内容（§1.5.1-§1.5.5 保留原样），只补充修正。

**Smoke check 执行命令**（可重复验证 · 2026-04-09 实测）：

```bash
# 1. Cost Tracker 真相
find backend/app -name "cost_tracker*" -type f
# → backend/app/middleware/cost_tracker.py ✅ 文件存在

# 2. canvas_agentic_rag 真相
backend/.venv/bin/pip show canvas_agentic_rag
# → WARNING: Package(s) not found: canvas_agentic_rag
backend/.venv/bin/python -c "import canvas_agentic_rag"
# → ModuleNotFoundError: No module named 'canvas_agentic_rag'

# 3. backend/app/hooks/ 真相
ls backend/app/hooks/
# → ls: backend/app/hooks/: No such file or directory
# 但 backend/app 下有: api/ audit/ clients/ core/ db/ graphiti/ mcp/ middleware/
#                     models/ prompts/ services/ utils/ 等，就是没有 hooks/
```

**修正后的 BUG-05 真实情况**：

| 组件 | §1.5 原断言 | Plan v19 smoke check 真相 | 真实状态 |
|---|---|---|---|
| **Cost Tracker** | 🔴 "Canvas 后端当前没有任何 cost tracking 实现" | **存在** · `backend/app/middleware/cost_tracker.py` | ✅ **已就绪**（§1.5 误判） |
| **canvas_agentic_rag** | 🟡 "子包存在，需要 Phase 1 Day 1 spike 验证 import" | **module 完全不存在** · pip 和 import 双重验证失败 | 🔴 **真实硬差距**（§1.5 部分错误）|
| **UserPromptSubmit hook** | 🔴 "backend/app/hooks/ 目录下只有 6 个 hook 文件，UserPromptSubmit 不存在，需要从零新写" | **`backend/app/hooks/` 根本不存在** · 整个 hooks/ 目录都不在 backend · UserPromptSubmit 是 Claude Code Desktop settings.json 的机制 | 🟡 **架构层误判**（§1.5 错误断言 hooks/ 目录存在）|

**修正后的 Fix-03 新方向**（Plan v19 采用）：

原 Plan v18 §4.3 Fix-03 建议（基于错误前提）：
- ❌ "新写 cost_tracker.py"
- ❌ "Phase 1 Day 1 spike 验证 canvas_agentic_rag import"（粒度不够：需要先决定是否引入）
- ❌ "新写 UserPromptSubmit hook 在 backend/app/hooks/"（方向错了：应该写在 Desktop settings.json）

Plan v19 实际执行的 Fix-03（方向 A · 按真相重写）：
- ✅ 在 14-PRD §7.6 末尾新增 §7.6.5 "Plan v19 Canvas 后端真相校正" · 标注 Cost Tracker 已就绪
- ✅ canvas_agentic_rag 的 Day 1 spike 改为"决策是否引入外部包 / 手写 workflow / 降级路径"（推荐手写）
- ✅ UserPromptSubmit hook 澄清为 Desktop `~/.claude/settings.json` + bash 脚本工作 · 不在 backend
- ✅ 14-PRD §10.1 新增 P0 Prerequisites · Day 1 的 3 个 spike 都定义清楚

**Plan v18 方法论的自我验证**：

Plan v18 的核心教训是 "亲自读 PRD 原文作为最后一环仲裁"。但 Plan v18 §1.5 本身**继承了 Plan v17 的后端扫描盲点**（Plan v17 只搜 services/ 目录），没有对 Canvas 后端做**独立的 smoke check**。这导致 §1.5 的 3 项断言中 2 项错误。

**这是一个讽刺的 meta-level 案例**：
- Plan v18 教训 = "亲自读才是最后一环"
- Plan v19 执行 Fix-03 前 = "亲自做 smoke check" 才发现 §1.5 断言错了
- 如果 Plan v19 盲目按 §4.3 建议修 PRD，会把**错误的"缺失"断言**写进 14-PRD v3
- 因此 Plan v19 **必须做独立 smoke check**，即使 Plan v18 已经说了"相信这 3 项"

**教训泛化**：
- Agent C 审查 PRD 的盲点 → 只用 semantic search，漏掉 line 4018 的 "+" 号
- Plan v17 扫描 backend 的盲点 → 只搜 services/，漏掉 middleware/ 的 cost_tracker.py
- **两种盲点都需要 "独立的 character-level 验证" 来揭穿**
- Plan v18 对 §1-§4 的审查很严谨（亲读原文）· 对 §1.5 的后端审查不够严谨（复用了 Plan v17 的扫描结果）· **不同模块需要同等水平的独立核实**

#### §1.5.7 · 后续影响

- Plan v19 的 Fix-03 scope 从原 ~30-50 行扩大到 ~80-120 行（因为要新增 §7.6.5 和 §10.1 P0 Prerequisites）
- 14-PRD §7.6.5 和 §10.1 P0 Prerequisites 是 Plan v19 的两个新增 section
- 相关证据在 17-prd-v3-changelog.md 有完整记录

#### §1.5.8 · Plan v21 Meta-Erratum（2026-04-09 下午 · errata of errata）

> **本小节是 Plan v19 §1.5.6 的二次校正**。Plan v19 §1.5.6 自认为已经修正了 Plan v17/v18 的后端扫描盲点 · 但 Plan v19 本身的 smoke check 命令有语法错误 · 导致它用一个错误的校正替换了上一层错误的继承结论。Plan v21 在 ChatGPT 5 Pro Deep Research 第二轮审查后独立核实并补修。本小节记录三层 nested errata 的 meta-level 教训。

**Plan v21 的发现链**：

1. Plan v20 生成 18-adversarial-review-prompt-v2.md 后 · 用户 Cmd+C 复制 → ChatGPT 5 Pro Deep Research 第二轮审查
2. ChatGPT 返回 🟡 **GO with major fixes** · 8 个发现 · 其中发现 #2 指出：14-PRD §7.6.5 和 §10.1 Day 1 Spike 2 断言 "canvas_agentic_rag module 完全不存在" · 但 Canvas 后端的 `rag_service.py` **每天都在正常 import** `from agentic_rag import canvas_agentic_rag`
3. Plan v21 启动 3 个并行 Explore agent 独立核实：
   - **Agent 1（PRD 内部一致性）**：确认 §7.6.5 和 §10.1 Day 1 Spike 2 确实有 "module 不存在" 断言残留 · 共 79 处 canvas_agentic_rag 引用
   - **Agent 2（Canvas 后端实地）**：读取 `backend/lib/agentic_rag/__init__.py` L48/L54/L67/L70 + `backend/app/services/rag_service.py` L40-85 · 确认 `canvas_agentic_rag` 是 `agentic_rag/__init__.py` 从 `agentic_rag.state_graph` re-export 出来的 StateGraph 对象
   - **Agent 3（学术文献核实）**：同步核实 ChatGPT 第二轮审查的其他 5 项发现 · 4 真 1 假

**Plan v19 smoke check 命令的 3 个错误复盘**：

| 错误 | Plan v19 命令 | 为什么错 | 正确做法 |
|---|---|---|---|
| #1 | `pip show canvas_agentic_rag` | `canvas_agentic_rag` 不是 pip 包名 · 顶级包叫 `agentic_rag` · 且 `agentic_rag/` 是 `backend/lib/` 下的本地目录（通过 `sys.path` 动态添加） · 根本不通过 pip 安装 | 先读 `backend/lib/agentic_rag/__init__.py` 的 `__all__` 声明看顶级导出 · 然后 `pip show agentic_rag` 或看 `backend/lib/` 目录存在性 |
| #2 | `python -c "import canvas_agentic_rag"` | Python 顶级 module 是 `agentic_rag` · `canvas_agentic_rag` 只是被 re-export 到顶级包的名字 · 正确 import 语法是 `from agentic_rag import canvas_agentic_rag` | 直接从 `backend/app/services/rag_service.py` L49 复制生产代码的 import 语法 |
| #3 | （没做的事）没看 `__init__.py` 原文 | Plan v19 凭记忆猜 canvas_agentic_rag "应该是"独立 module · 没有先 grep 生产代码找真实 import 语法 | 任何涉及 import 验证的 smoke check 都必须**先读 __init__.py 原文** · 把 `__all__` 列表和生产代码的 import 作为 ground truth |

**正确的 smoke check 命令**（Plan v21 验证 · 已写入 14-PRD §10.1 Day 1 Spike 2）：

```bash
cd backend
.venv/bin/python -c "from agentic_rag import canvas_agentic_rag, AGENTIC_RAG_AVAILABLE; print('AVAILABLE=', AGENTIC_RAG_AVAILABLE, 'GRAPH=', type(canvas_agentic_rag).__name__)"
```

预期输出：`AVAILABLE= True GRAPH= CompiledStateGraph`（如果 langgraph 依赖已装）

**三层 nested errata 的 meta-pattern**：

| 层 | 主角 | 盲点 | 共同教训 |
|---|---|---|---|
| **L1** · Plan v17 Canvas 后端扫描（2026-04 上旬）| 只搜 `backend/app/services/` 目录 | 漏掉 `middleware/cost_tracker.py`（Cost Tracker 实际已就绪）和 `lib/agentic_rag/`（canvas_agentic_rag 实际已就绪）| 没有全目录扫描 |
| **L2** · Plan v19 smoke check（2026-04-09 早）| 命令语法错 · 用 `pip show canvas_agentic_rag` / `import canvas_agentic_rag` | 没有以生产代码（`rag_service.py` L49）为 ground truth · 凭记忆猜 import 语法 | 没有以生产代码 import 语法为 ground truth |
| **L3** · Plan v21 独立核实（2026-04-09 下午 · 本 section）| **（当前结论 · 等 Plan v22 第三轮审查验证）** · 可能盲点 TBD | TBD | TBD |

**三层的讽刺共同点**：每层都认为自己"亲自验证了"上一层的结论 · 但都有新形式的盲点。

- L1 的教训是"别只扫一个子目录"
- L2 的教训是"别只相信上一层的扫描结果 · 自己做 smoke check"
- **L3 的教训**（Plan v21 新提出）："别凭记忆猜 smoke check 命令 · 以生产代码的 import 语法为最终仲裁"

**Plan v21 方法论泛化**（未来 smoke check 的 4 条护栏）：

1. **grep 生产代码找真实 import/call 语法** → 复制粘贴作为 smoke check 命令 · 比"凭记忆猜命令"可靠得多
2. **比对 `__all__` 和 `__init__.py`** → 知道顶级包到底导出什么名字 · 避免混淆 re-export 和原始 module
3. **寻找日常运行的矛盾证据** → 如果 smoke check 说 X 不存在 · 但生产日志或服务启动显示 X 每天正常运行 · 先怀疑 smoke check 命令
4. **errata 必须预留 errata-of-errata 空间** → 校正自身也可能错 · 文档结构应支持多层嵌套校正 · §7.6.5 和本 section 就是例子

**对 §1.5.6 的具体修正条目表**：

| §1.5.6 原断言 | Plan v21 修正 | 证据来源 |
|---|---|---|
| "canvas_agentic_rag · module 完全不存在 · pip 和 import 双重验证失败" | ✅ **实际存在** · Plan v19 smoke check 命令错误 | `backend/lib/agentic_rag/__init__.py` L48/L54/L67/L70 + `rag_service.py` L49 |
| "真正的硬差距只有 1 项（canvas_agentic_rag module 不存在）" | **0 项硬差距** · Plan v18 §1.5 BUG-05 的 3 项断言**全部错误** | Plan v21 三方独立核实 |
| "Plan v17 Canvas 后端扫描盲点" | 教训升级为 "Plan v17 只扫子目录 + Plan v19 smoke check 命令语法错 + 共同点是没有以生产代码为 ground truth" | 三层 nested pattern 分析 |
| "Plan v18 方法论的自我验证" | Plan v18 的教训"亲自读 PRD 原文"已经是对的 · 但延伸到 smoke check 时要求变成"亲自读生产代码原文" · 一个方法学的递归深化 | §1.5.6 对 §1.5.5 的延伸 → §1.5.8 对 §1.5.6 的延伸 |
| "相关文档：17-prd-v3-changelog.md Fix-03 段" | 新增 **19-prd-v4-changelog.md**（Plan v21 产物 · 含 Fix-04~Fix-10 完整 diff） | 14-PRD v3 → v4 changelog |

**14-PRD v4 修订总览**（Plan v21 覆盖的 7 项 Fix）：

| Fix | 章节 | 内容 | 严重度 |
|---|---|---|---|
| **Fix-04** | §1.8 L2814/L2821 + §5.5 L5254 | 设计 8 d=2.30 → d≈0.55 Cepeda 2008 | 🔴 阻断（被第一轮审查要求但 Plan v19 清除不彻底）|
| **Fix-05** | §7.6.5 重命名+重写 + §10.1 Day 1 Spike 2 重写 | canvas_agentic_rag 从"不存在"改为"实际存在" · §10.1 Day 1 Spike 2 降级为 30 分钟 import 验证 | 🔴 阻断 |
| **Fix-06** | §9.2 L6976+L6988 | Cochrane Ch 10.10.1 → Chapter 12.3.1 structured tabulation | 🟡 重要（章节引用错位）|
| **Fix-07** | §4.4 L4023+L4039 | Bisra CI 0.46-0.64 → 0.45-0.65 · 措辞 "69 primary studies · n=5,917" → "69 effect sizes from 64 research reports · 5,917 participants" | 🟡 重要（精度+术语）|
| **Fix-08** | §1.6 L766+L769 | Cassady Table 3 具体引用 → 模糊表述 "具体 Table 号见原文的 correlations 分析段落"（因为 Table 3 实为 SAT 均值表）| 🟡 重要（引用错位）|
| **Fix-09** | §2.4 L1470 + §4.4 L4032 | Chi d=1.00 → d≈1.09（来自 t(22)=2.64 换算 · 与 §4.4 汇总表一致）| 🟡 一致性 |
| **Fix-10** | L1-7 frontmatter | version v1 → v4 · author "Plan v15" → "Plan v15→v16→v19→v21" · 新增 revision_history | 🔵 文档治理 |

**相关文档修订索引**（Plan v21 产物全景）：
- `14-scheme-a-implementation-prd.md` v4（原 v3 · 7 项 Fix · ~120-180 行修订）
- `16-triangulated-review-report.md` 追加本 §1.5.8（~80-120 行）
- `19-prd-v4-changelog.md` **新建**（~600-800 行 · 完整 7 项 Fix diff + Plan v21 核心教训）
- `20-adversarial-review-prompt-v3.md` **新建**（~900-1100 行 · Plan v22 第三轮 ChatGPT 审查 prompt · 走向 A）

**元信息**：
- 编写时间：2026-04-09 下午（Plan v21 执行期间）
- 作者：Claude Code (Plan v21)
- 基础：ChatGPT 5 Pro Deep Research 第二轮审查（2026-04-09 下午返回）+ Plan v21 3 个并行 Explore agent 独立核实（PRD 内部一致性 + Canvas 后端实地 + 学术文献核实）
- 保留策略：§1.5.1-§1.5.7 原文不改 · 只追加本 §1.5.8 · 历史层次清晰可追溯

---

#### §1.5.9 · Plan v23 Meta-Erratum（2026-04-09 晚 · L3 盲点确认关闭 · 四层 nested errata 延伸 · 真实运行级仲裁）

> **核心事件**：Plan v21 在 §1.5.8 显式预留了 L3 TBD（"Plan v21 独立核实 · 盲点 待定 · 等 Plan v22 第三轮审查"）。ChatGPT 5 Pro Deep Research 第三轮审查（Plan v22 轮次）于 2026-04-09 晚返回 🟡 **GO with significant fixes** 决策 · 指出 5 项实质性问题。Plan v23 对 L3 盲点的具体形态进行了**独立核实**并通过**真实运行 production-equivalent smoke check** 首次为 canvas_agentic_rag 就绪状态提供**运行级证据**。本 §1.5.9 记录 Plan v23 的发现、修复范围、方法论新护栏，以及四层 nested errata pattern 的延伸。

##### Plan v22 第三轮审查摘要

**ChatGPT 决策**：🟡 **GO with significant fixes**（不是 GO · 不是 NO GO · 而是中间状态 · 表示 PRD 核心方向正确但有必须修的实质性问题）

**ChatGPT 指出的关键问题** + Plan v23 独立核实结论：

| # | ChatGPT 发现 | Plan v23 独立核实 | 严重度 | Plan v23 响应 |
|---|---|---|---|---|
| 1 | **版本错配** · ChatGPT 看到的 PRD 仍是 v1 · 含 d=2.30 残留 | ❌ **ChatGPT 看到的是陈旧版本** · 本地 14-PRD 文件确实是 v4（Fix-04~Fix-10 全部落地）· 用户上传给 ChatGPT 的附件是 v3 副本 | 🔵 文档治理 | **Fix-10b** · 21-changelog 明确记录版本错配 · 无需重做 Fix-04~Fix-10 |
| 2 | **Fix-05 smoke check 命令 bug** · `from agentic_rag import ...` 在 backend/ 下会因 sys.path 缺失而失败 | ✅ **完全真实** · `backend/app/services/rag_service.py` L32-37 显式做 `sys.path.insert(0, str(_project_root / "lib"))` 是生产导入链的前提 · Plan v21 的命令漏了这一步 | 🔴 **阻断** | **Fix-11** · §7.6.5 + §10.1 改为 production-equivalent 命令（`from app.services.rag_service import LANGGRAPH_AVAILABLE`）|
| 3 | **Chi d 换算公式** · `d = 2t/√df` 只在 n1=n2 时成立 · Chi 1994 是 between-subject (14 vs 10) | ✅ **完全真实** · Chi 1994 原文 n1=14 prompted, n2=10 control · 正确公式 `d = t × √(1/n1 + 1/n2) = 2.64 × √(0.1714) ≈ 1.093` | 🟡 重要 | **Fix-12** · §2.4 + §4.4 更新公式 + 加 n1=14, n2=10 具体说明 + 保留 d≈1.09 数值（巧合数值相同）|
| 4 | **Cepeda 2008 是 primary study 不是 meta-analysis** · 作为 d≈0.55 锚点可追溯性不足 | ✅ **完全真实** · Cepeda 2006 *Psychological Bulletin* 132(3): 354-380 才是 meta-analysis（317 实验 · 184 文献）· 2008 是 temporal ridgeline 的 primary study | 🟡 重要 | **Fix-13** · §1.8 锚点切换到 Cepeda 2006 + 补充 Donovan & Radosevich 1999 交叉验证 |
| 5 | **Cassady Table 3 修正不完整** · Plan v21 删了 Table 3 但模糊措辞 "具体 Table 号见原文" 留下可追溯性缺口 | ✅ **部分真实** · Plan v23 Stage 4 尝试 WebSearch/WebFetch 核实 · 未能精确定位 Table 编号 · WebFetch PDF 失败（binary content）· WebFetch ResearchGate 返回 403 | 🟡 重要 | **Fix-14** · §1.6 保留模糊措辞 + 明确标注 "待 Phase 1 Day 1 手动核实" + 补充 SAT 1109 vs 1001 的 WebSearch 证据 |
| 6 | **Plan v21 没有实际运行 smoke check**（L3 盲点）· 静态代码分析代替了运行级验证 | ✅ **完全真实** · 这正是 Plan v21 §1.5.8 显式预留的 L3 TBD | 🔴 **meta-critique** | **Fix-15** · Plan v23 Stage 1 **实际运行** production-equivalent smoke check · 记录真实输出到 §7.6.5 + §10.1 |

##### Plan v23 Stage 1 真实运行输出（核心 meta-validation · 首次运行级证据）

```
$ cd /Users/Heishing/Desktop/canvas/canvas-learning-system/backend && \
    .venv/bin/python -c "from app.services.rag_service import LANGGRAPH_AVAILABLE, _IMPORT_ERROR; print('LANGGRAPH_AVAILABLE=', LANGGRAPH_AVAILABLE, 'ERROR=', _IMPORT_ERROR)"

2026-04-09 13:20:55 [debug    ] RAGService: Added /Users/Heishing/Desktop/canvas/canvas-learning-system/backend/lib to sys.path
(Python 3.14 + Pydantic v1 compatibility warning · non-blocking)
(jieba pkg_resources deprecation warning · non-blocking)
2026-04-09 13:21:00 [info     ] RAGService: LangGraph/Agentic RAG available. LANGGRAPH_AVAILABLE=True
LANGGRAPH_AVAILABLE= True ERROR= None
```

**运行级证据解读**：
- ✅ `LANGGRAPH_AVAILABLE=True, ERROR=None` → canvas_agentic_rag 完全可用
- ✅ `sys.path insertion` debug 行 → 确认 Plan v21 命令失败路径已被 production-equivalent 命令修复
- ✅ 依赖链完整：jieba + langchain_core + langgraph 全部加载
- 🟡 Python 3.14 + Pydantic v1 warning（非阻断 · Phase 1 长期监控）
- 🟡 jieba pkg_resources deprecation warning（非阻断 · Phase 1 长期监控）
- ⏱ 冷启动 ~5 秒（13:20:55 → 13:21:00）

##### 四层 nested errata pattern 延伸

Plan v21 §1.5.8 建立了三层 pattern · Plan v23 延伸到四层并预留 L5 TBD：

| 层 | 时间 | 主角 | 盲点形态 | 方法论教训 |
|---|---|---|---|---|
| **L1** | 2026-04 上旬 | Plan v17 Canvas 后端扫描 | **只扫子目录** · 只搜 `backend/app/services/` · 漏掉 `middleware/` 和 `lib/` | 必须全目录扫描 |
| **L2** | 2026-04-09 早 | Plan v19 smoke check | **命令语法错** · 用 `import canvas_agentic_rag` 而不是 `from agentic_rag import canvas_agentic_rag` | 必须以生产代码为 ground truth |
| **L3** | 2026-04-09 下午 | Plan v21 独立核实 | **命令不完整**（静态分析代替运行）· `from agentic_rag import ...` 在 backend/ 下缺 sys.path 会失败 · Plan v21 只做了代码原文阅读 · 没实际运行就断言"已就绪" | 代码原文阅读 ≠ 运行级证据 · 必须实际执行 |
| **L4** | **2026-04-09 晚** | **Plan v23 实际运行** | **无盲点**（Plan v23 完成了 production-equivalent 命令的实际运行 · 首次为 canvas_agentic_rag 提供运行级证据）| 静态分析 + 运行级验证必须同时存在 |
| **L5** | **TBD** | **Phase 1 Day 1 Spike** | **待定** · Plan v23 无法预知 | **TBD · 等 Phase 1 骨架 Day 1 真实执行** |

**四层 pattern 的核心讽刺**：每层都以为自己是"独立核实"在修正前一层的盲点 · 但自己的方法本身也有盲点 · 直到下一层才被发现。**终极仲裁** = 实际运行 + 未来真实 session 的生产行为。

##### Plan v23 方法论新护栏（第 5 条 · Plan v21 4 条的延伸）

Plan v21 §1.5.8 建立了 4 条护栏：

1. grep 生产代码找真实 import/call 语法
2. 比对 `__all__` 和 `__init__.py`
3. 寻找日常运行的矛盾证据
4. errata 必须有显式的 errata-of-errata 预留空间

**Plan v23 新增第 5 条护栏**：

5. **静态分析 + 运行级验证必须同时存在** — 任何涉及 "X 是否可用 / 是否就绪 / 是否存在" 的断言 · 都需要有 "X 实际运行输出" 的证据 · 仅代码原文阅读（Plan v21 的做法）会留下 L3 盲点 · 仅看生产日志（推断）也不够 · **必须直接在当前环境跑一次命令看输出**。Plan v23 的 production-equivalent smoke check 是这条护栏的**首次实施**。

**为什么这条护栏不能早出现**：因为 L3 盲点在 Plan v21 阶段是**看不见**的 —— Plan v21 认为自己做了"独立核实"，而且代码原文阅读确实比 Plan v19 的错命令语法更准确。只有当 ChatGPT 第三轮审查指出 "command will fail due to sys.path" 时 · Plan v23 才能把这条盲点明确化。这正是 nested errata 的典型动力学 —— **只有下一层才能看见上一层的盲点**。

##### 打破递归审查循环的用户决策

Plan v23 完成后 · 用户面临一个关键决策：
- 选项 A：做第四轮 ChatGPT 审查（Plan v24）· 理论上可能发现 Plan v23 的 L5 盲点（四层 pattern 继续延伸）
- 选项 B：**直接进入 Phase 1 骨架** · 用 Day 1 Spike 的真实运行作为 L5 盲点的终极仲裁

**用户选择 B** · 理由：
1. 真实运行已经是 Plan v23 的核心方法论（Stage 1）· 继续 recursive review 的边际收益递减
2. Day 1 Spike 1/2/3 本身就是"真实运行验证" · 比 ChatGPT Deep Research 更接近 ground truth
3. 方法论的终极仲裁 = 实际跑 Canvas 后端 + 实际创建 vault + 实际走通检验白板 flow

**Plan v23 的核心哲学**：用**真实运行**打破"递归 ChatGPT 审查"的无限循环 · 让方法论从"静态 review" 转向"dynamic execution"。

##### Fix-11 ~ Fix-15 执行摘要

| Fix | 章节 | 严重度 | 核心修改 | 运行级证据 |
|---|---|---|---|---|
| **Fix-11** | §7.6.5 smoke check 命令对比 + §10.1 Day 1 Spike 2 | 🔴 阻断 | production-equivalent 命令替换 + Plan v23 真实输出记录 + 3 个 fallback 命令 | ✅ 有（Stage 1 真实运行）|
| **Fix-12** | §2.4 L~1477 + §4.4 L~4046 Chi d 换算公式 | 🟡 重要 | `d = t × √(1/n1 + 1/n2)` 替换 `2t/√df` + n1=14, n2=10 具体说明 · 数值 d≈1.09 不变（巧合） | ✅ 有（WebSearch 核实 Chi 1994 原文）|
| **Fix-13** | §1.8 Cepeda 锚点 | 🟡 重要 | Cepeda 2008 primary study → Cepeda 2006 meta-analysis + Donovan 1999 交叉验证 | 🟡 部分（WebSearch 核实 2006 是 meta-analysis · 精确 d 值未能从公开摘要获取）|
| **Fix-14** | §1.6 Cassady 正面位置 | 🟡 重要 | 保留模糊措辞 + 加"待 Phase 1 Day 1 手动核实"标注 + 补充 SAT 1109 vs 1001 证据 | 🟡 降级（WebSearch 未能定位 Table 号 · WebFetch PDF 失败）|
| **Fix-15** | §7.6.5 + §10.1 实际运行记录 | 🔴 meta-critique | Plan v23 Stage 1 实际运行 · 记录完整 stdout + stderr + warning + 结论 | ✅ 有（Stage 1 核心运行结果）|

##### 相关文档

- `14-scheme-a-implementation-prd.md` v5（从 v4 · 5 项 Fix · ~80-150 行修订）
- `16-triangulated-review-report.md` 追加本 §1.5.9（~70-100 行）
- `21-prd-v5-changelog.md` **新建**（~500-700 行 · 完整 5 项 Fix diff + Stage 1 真实运行记录 + 四层 nested errata 延伸 + Phase 1 骨架 handoff checklist）
- `backend/app/services/rag_service.py` L32-85（生产代码 · Plan v23 运行入口）
- **Plan v23 Stage 1 真实运行输出**（上方代码块 · L4 运行级证据 · 首次记录）

**元信息**：
- 编写时间：2026-04-09 晚（Plan v23 执行期间）
- 作者：Claude Code (Plan v23)
- 基础：ChatGPT 5 Pro Deep Research 第三轮审查（2026-04-09 晚返回 🟡 GO with significant fixes）+ Plan v23 Stage 1 真实运行 + Stage 2-4 并行 WebSearch 学术核实 + Stage 5 14-PRD 修订
- 保留策略：§1.5.1-§1.5.8 原文不改 · 只追加本 §1.5.9 · 历史层次清晰可追溯 · 四层 nested errata pattern 完整记录

---

## §2 · 3 个独立 Agent 的发现与误判

### §2.1 · Agent A · 学术引用独立验证

#### §2.1.1 · Agent A 的任务和方法

**任务**：用 WebSearch + WebFetch 独立核实 ChatGPT 在 Top 5 Bug 清单中涉及的所有学术引用。

**方法**：
1. 对每篇论文做 Google Scholar 搜索，核实 DOI / 出版信息
2. 对关键 d 值声明做 PubMed / Semantic Scholar 交叉验证
3. 查找 PRD 中未引用但可能相关的 meta-analysis（replacement candidates）

**工具**：WebSearch（Google Scholar 代理）+ WebFetch（抓 DOI 页面摘要）

#### §2.1.2 · Agent A 的 5 篇论文核实结果

**论文 1 · Karpicke & Blunt 2011 _Science_**

- **PRD 声称**：d=1.50（检验白板灵魂 · §2.4 Active Recall 锁定）
- **Agent A 核实**：
  - ✅ DOI 确认：10.1126/science.1199327
  - ✅ 文章真实存在（Science, 331(6018), 772-775）
  - ✅ 原文报告的 retrieval practice 效应与 d≈1.50 一致（note: 原文用 proportion correct，d 是 PRD 的换算）
  - 🟡 **ChatGPT 遗漏**：Science 2012 有后续的方法学批评（Karpicke 2012 response），但整体 d 值方向正确
- **评级**：✅ 可信（PRD 的 d=1.50 有合理支撑）

**论文 2 · Chi et al. 1994 Self-Explanation**

- **PRD 声称**：d=1.00（/quiz_from_callout · §4.4）
- **Agent A 核实**：
  - ✅ DOI 确认：原文 _Cognitive Science_ 18, 439-477
  - 🟡 **数学转换合理**：原文报告 t(22)=2.64 → d ≈ 2×2.64/√22 ≈ 1.126 ≈ 1.09 ≈ 1.00（PRD 近似取整）
  - 🟡 **具体 t 值难核实**：Agent A 未能从 Semantic Scholar 摘要直接拿到 t 值，需要 full PDF
  - ⚠️ 样本量小：n=8 学生，是小样本研究
- **评级**：🟡 可能可信（数学换算合理，但 n=8 的置信区间很宽）

**论文 3 · Dunlosky et al. 2013 Learning Techniques**

- **PRD 声称**：d=0.60-0.80（Self-Explanation）
- **Agent A 核实**：
  - ✅ DOI 确认：10.1177/1529100612453266（_Psychological Science in the Public Interest_ 14, 4-58）
  - 🔴 **关键问题**：这是一篇 **review article**，对 10 种学习技术做 qualitative utility rating（high / moderate / low），**不是 quantitative meta-analysis**，**不报告单一 d 值**
  - 🔴 Dunlosky 原文对 Self-Explanation 的评级是 **"moderate utility"**（定性），而不是 d=0.60-0.80（定量）
  - 🔴 PRD line 4033 自己就说了"Self-Explanation 评为 moderate utility"，但 line 4018/4032/4089 又写了 d=0.60-0.80 —— **PRD 自相矛盾**
- **评级**：🔴 **引用误用**（PRD 把定性评级误当成定量 d 值）

**论文 4 · Metcalfe 2017**

- **PRD 声称**：d=2.30（设计 8 · 3 天 + 1 周主动提醒 · §9.1 line 6910）
- **Agent A 核实**：
  - 🔴 Agent A 在 Google Scholar 用关键词 "Metcalfe 2017 spacing effect d 2.30" 搜索，**未找到** Metcalfe 2017 发表过声称 d=2.30 的论文
  - 🔴 Metcalfe 2017 最著名的文章是 _Learning from Errors_ (_Annual Review of Psychology_, 68, 465-489)，讨论 metamemory 和 error correction，**不涉及 d=2.30 的 spacing effect 声明**
  - 🔴 Spacing effect 的典型 d 值（基于 Cepeda 2008 meta-analysis）在 0.4-0.7 范围
  - 🔴 **d=2.30 在教育心理学 meta-analysis 文献中几乎从未出现**（Hattie 2009 的 typical d 范围是 0.3-0.6）
- **评级**：🔴 **无法追溯**（ChatGPT 的谨慎态度正确）

**论文 5 · Cassady & Johnson 2002**

- **PRD 声称**：d=-0.50 到 -1.20（§1.6 line 768 · Test Anxiety）
- **Agent A 核实**：
  - ✅ DOI 确认：原文 _Contemporary Educational Psychology_ 27(2), 270-295
  - ✅ Cognitive Test Anxiety Scale (CTAS) 量表开发论文真实存在
  - 🟡 Agent A 无法从 abstract 验证 Table 3 的具体数值（需要 full PDF）
  - 🟡 **基于文献常识**：CTAS 研究通常报告 correlations（r），不报告 d 值
  - 🟡 r→d 转换合法（公式 d = 2r/√(1-r²)），但 PRD 没声明这是转换
- **评级**：🟡 **转换需声明**（论文存在，但 d 值表示不严谨）

#### §2.1.3 · Agent A 的关键发现：Bisra 2018

Agent A 在核实过程中**独立发现**了一篇 ChatGPT 未提及的 meta-analysis：

```
Bisra, K., Liu, Q., Nesbit, J. C., Salimi, F., & Winne, P. H. (2018).
Inducing self-explanation: A meta-analysis.
Educational Psychology Review, 30(3), 703-725.
DOI: 10.1007/s10648-018-9434-x
```

**关键数据**：
- **g = 0.55** (Hedges' g，随机效应模型)
- **95% CI: 0.46 - 0.64**
- **研究数**：69 primary studies
- **总样本**：5,917 学生
- **Moderators**: scaffolding (prompted vs. open-ended), content domain, age group

**为什么 Bisra 2018 重要**：
1. 它是**真实存在的、可独立验证的** Self-Explanation meta-analysis
2. 它**报告具体的定量效应量** g=0.55（而 Dunlosky 2013 只有定性评级）
3. 它的样本规模（5,917 学生）远大于 Chi 1994（n=8）
4. 它可以作为 **Dunlosky 2013 的直接替代引用**

**Plan v19 建议**：Fix-02a 中用 Bisra 2018 g=0.55 替代 Dunlosky 2013 d=0.60-0.80 的 quantitative 声明。Dunlosky 2013 保留作为 "utility rating framework" 引用，但不再作为 d 值来源。

#### §2.1.4 · Agent A 的另一个发现：Donoghue & Hattie 2021

Agent A 在查找 Hattie 2009 的更新时发现：

```
Donoghue, G. M., & Hattie, J. A. C. (2021).
A meta-analysis of ten learning techniques.
Frontiers in Education, 6, 581216.
DOI: 10.3389/feduc.2021.581216
```

**状况**：
- ✅ 论文真实存在
- 🔴 但 **"写式 vs 口头 d=1.55 vs 1.45"** 这个声称（如果 PRD 或其他来源曾经提到过）**无法在该论文中验证**
- 🔴 Donoghue & Hattie 2021 是 10 种学习技术的 meta-analysis，但 d 值范围并非 1.55 或 1.45 附近
- 🟡 **PRD 实际上没有引用 Donoghue & Hattie 2021**（Agent A 搜索 14-PRD 全文零命中）
- 🟡 但这是 Agent A 的警示：如果未来 Plan v19 想用 Donoghue & Hattie 2021 作为学术锚点，需要先核实具体 d 值

#### §2.1.5 · Agent A 的整体可信度评估

**ChatGPT 的学术核实整体可信度**：中等（6.5/10）

优点：
- ChatGPT 对 "无法追溯" 的 d 值采取 **谨慎态度**（Metcalfe 2017 d=2.30 的否决正确）
- ChatGPT 正确识别了 Dunlosky 2013 的定性 vs 定量混淆
- ChatGPT 对 Cassady 2002 的 r→d 转换质疑基本正确

缺点：
- ChatGPT **遗漏了 Bisra 2018** —— 这是可以直接作为 Dunlosky 替代的可靠 meta-analysis
- ChatGPT 对 Karpicke 2011 的 Science 后续方法学批评未提及
- ChatGPT 没主动建议 replacement references（它只说"这个引用有问题"，没说"用什么替代"）

---

### §2.2 · Agent B · 统计学方法学独立验证

#### §2.2.1 · Agent B 的任务和方法

**任务**：独立验证 ChatGPT 关于 §9 88.1% 加权公式的方法学判定。

**方法**：
1. 查阅 meta-analysis 经典教科书（Borenstein / Cochrane / metafor）
2. 核实 "Cohen's d 不能直接相加" 的理论基础
3. 评估 "55-75% 替代区间" 的合理性
4. 给出正确做法的教科书引用

**工具**：WebSearch（Google Scholar + 教科书 PDF preview）

#### §2.2.2 · Agent B 核实的 4 条方法学声明

**声明 1 · "Cohen's d 不能直接相加"** · ChatGPT 主张

Agent B 验证：

> ✅ **完全确认**。Cohen's d 是标准化效应量，定义为 `d = (M1 - M2) / SD_pooled`。不同研究的 d 值不能直接相加，因为：
> 1. 每个 d 对应不同的样本方差（SE 不同）
> 2. 不同研究的构念（construct）可能不同
> 3. 直接相加会导致大样本研究的 d 被小样本研究的 d "稀释"

**教科书引用**（Borenstein et al. 2009 _Introduction to Meta-Analysis_ Ch 3）：

> "The mean of a set of effect sizes is not meaningful unless we account for their precision. A study with a very small sample size yielding d = 0.8 should not be weighted equally to a study with a very large sample size yielding d = 0.5."

**声明 2 · "应该用 inverse-variance weighting"** · ChatGPT 主张

Agent B 验证：

> ✅ **完全确认**。Inverse-variance weighting 是 meta-analysis 的标准方法：
>
> ```
> w_i = 1 / v_i       其中 v_i = SE_i² (effect size i 的 sampling variance)
> weighted_mean_d = Σ(w_i × d_i) / Σ w_i
> ```
>
> 这保证了 **精度高的研究得到更大权重**（SE 小 → v 小 → w 大）。

**教科书引用**（Cochrane Handbook Ch10 + metafor 包文档）：

> "The inverse-variance weighted average is the maximum-likelihood estimate under the fixed-effect model, and the basis for DerSimonian-Laird random-effects estimator."

**声明 3 · "不同量纲不能混加"** · ChatGPT 主张（过于严格）

Agent B 验证：

> 🟡 **ChatGPT 过于严格**。实际情况更 nuanced：
>
> - **多变量 meta-analysis 存在**（Becker 2000, Jackson et al. 2011），允许合并相关但不同的构念
> - 但是要求 1) 构念之间有理论相关性 2) 报告构念间 correlation matrix 3) 使用 multivariate random-effects model
> - **关键**：即使是多变量 meta-analysis，也**不会用 d 作为权重** —— 仍然是 inverse-variance
>
> 所以 ChatGPT 的"不同构念不能混加"方向正确，但忽略了多变量 MA 的存在。不过这个 nuance 不改变 88.1% 的判定（因为 PRD 用 d 作权重，不是 inverse-variance）。

**声明 4 · "88.1% 不合法"** · ChatGPT 主张

Agent B 验证：

> ✅ **完全确认**。PRD §9 的公式 `Σ(d_i × %_i) / Σ d_i` 在统计学上有 3 个致命问题：
>
> 1. **d 作为权重的语义错误** —— d 衡量的是效应大小，不是"这个研究多可靠"或"这个设计多重要"
> 2. **"守恒度百分比"的来源不明** —— PRD 的 60%/70%/85%/95% 这些百分比不是从研究中计算出来的，而是 PRD 作者的主观估计
> 3. **合并主观估计和客观 d 值** —— 这等于说"用客观数字去加权主观数字"，结果是 "客观形式的主观数字"，误导性极强
>
> 即使不考虑"不同构念不能混加"的严格要求，这个公式本身就无法被任何 meta-analysis 教科书接受。

#### §2.2.3 · 关于 "55-75% 替代区间" 的争议

这是 Plan v18 中 **Agent B 和 ChatGPT 出现分歧** 的唯一地方。

**ChatGPT 的建议**：把 88.1% 改为 55-75% 区间。

**Agent B 的反对**：

> 🔴 **Agent B 反对 ChatGPT 的替代建议**。理由：
>
> 1. **如果 88.1% 的方法学崩塌，任何基于这种方法学的数字都崩塌** —— 包括 55-75% 区间
> 2. ChatGPT 没有提供 55-75% 的**计算依据**或**数据来源** —— 这是"凭感觉"给的数字
> 3. ChatGPT **自己在犯它批评的错误** —— 既然你说不能给单一百分比，为什么又给了一个区间？
> 4. 正确做法是 **narrative synthesis** 而不是 **更保守的区间**
>
> 这是 Agent B 在本轮核查中发现的 **ChatGPT 自相矛盾**。

#### §2.2.4 · Agent B 推荐的正确做法

**Agent B 的最终建议**：

完全删除任何百分比数字（88.1% 或 55-75% 都删），改为：

**方法学 1 · Narrative Synthesis**（叙事综合，Cochrane 标准）

- 对 12 个设计每个写 1-2 段定性评价
- 明确说明每个设计的 "学术根据 + 守恒机制 + 可能的风险"
- 不做任何百分比计算
- 给读者留下**自行判断**的空间

**方法学 2 · Structured Tabulation**（结构化汇总表）

- 保留 §9.1 line 6901-6915 的汇总表（这是有价值的 audit）
- 每行列出：设计 · d 值 · 守恒度 · 学术引用 · 守恒机制 · 风险备注
- **删除** "合计" 行（line 6915 的 Σd=10.40 + Σ(d×%)=9.166）
- 每一行独立评估

**方法学 3 · Top 3 / Bottom 3 定性评价**

- 保留 §9.3 "Top 3 完美守恒 (≥ 90%)"
- 保留 §9.4 "Top 3 部分丢失 (< 80%)"
- 这些定性评价不依赖总分，可以独立存在

**方法学 4 · 明确 scope 声明**

- 在 §9 开头明确声明 "本章不是 meta-analysis，而是 design preservation audit"
- 声明 "d 值是从原始研究的效应量推导，守恒度是 PRD 作者的主观估计"
- 声明 "这些数字不应作为精确的学习效果预测"

#### §2.2.5 · Agent B 的整体可信度评估

**ChatGPT 的方法学判定可信度**：高 (8/10)

优点：
- ChatGPT 正确识别了 Cohen's d 的不可加性
- ChatGPT 正确引用了 inverse-variance weighting
- ChatGPT 正确指出了 88.1% 的计算不合法

缺点：
- ChatGPT 对 "不同构念不能混加" 过于严格（忽略多变量 MA）
- **ChatGPT 自相矛盾地给出 55-75% 替代区间**（这是方法学上的不一致）
- ChatGPT 没有推荐 narrative synthesis 作为正确做法

---

### §2.3 · Agent C · PRD Bug 清单独立审查

#### §2.3.1 · Agent C 的任务和方法

**任务**：独立读 14-PRD 全文，对 ChatGPT 的 Top 5 Bug 清单做 PRD-level 的交叉验证。

**方法**：
1. 读 14-PRD 的关键章节（§1.6, §2.3.1, §2.4, §4.4, §4.4.1, §5.1.1, §7.6, §9, §10.1）
2. 对每条 ChatGPT bug 做"证据存在性"判断
3. 发现 ChatGPT 未提及的新 bug

**工具**：Read + Grep（PRD 文件内搜索）

#### §2.3.2 · Agent C 的 5 条判定结果

| Bug | ChatGPT 判定 | Agent C 判定 | 最终真相 | Agent C 对错 |
|---|---|---|---|---|
| BUG-01 效应量合成 | H | 🟡 Agent C 说 "PRD 没有直接相加" | ✅ 真实 | 🔴 **Agent C 错了** |
| BUG-02 引用错误 | H | 🟡 Agent C 说 "找不到依据" | ✅ 真实 | 🔴 **Agent C 错了** |
| BUG-03 挂载悖论 | M | ✅ Agent C 同意 | ❌ 不是真实 bug | 🔴 **Agent C 错了** |
| BUG-04 Dashboard 双重计入 | M-H | 🔴 Agent C 否决 | ❌ ChatGPT 错了 | ✅ **Agent C 对了** |
| BUG-05 后端差距 | M-H | ✅ Agent C 同意 | ✅ 真实 | ✅ **Agent C 对了** |

**Agent C 的战绩**：2 正确 + 3 错误 / 总 5 条。

#### §2.3.3 · Agent C 的 3 次系统性误判

**误判 1 · BUG-01 "PRD 没有直接相加"**

Agent C 的原话：

> 我搜索了 14-PRD 全文，没找到"直接相加"效应量的证据。§9 的公式是 `Σ(d × %) / Σ d`，这是加权平均，不是直接相加。ChatGPT 可能误解了 PRD。

**为什么 Agent C 错了**：
- Agent C 搜索时用的关键词可能是"相加"、"加权和"、"总 d"
- Agent C **没有精确匹配到 line 4018 的 "+" 号**
- line 4018: `d = 1.00 (Chi) + d = 0.60-0.80 (Dunlosky)` —— 这是 **ChatGPT 描述的"直接相加"**
- line 4089: `d=1.00+0.60` —— 再次的直接相加

**暴露的 Agent C 盲点**：
- Agent C 不做 **exhaustive 字符级扫描**
- Agent C 依赖 semantic search，可能漏掉 "+" 号这种字符级证据
- Agent C 没意识到 PRD 可能在**不同章节**存在**不同种类的方法学错误**

**误判 2 · BUG-02 "找不到依据"**

Agent C 的原话：

> 我在 14-PRD 里搜索了 Dunlosky、Metcalfe、Cassady 三个作者名，但没找到它们被 PRD 引用为 d 值来源的具体位置。ChatGPT 的 BUG-02 可能是基于它自己的记忆，而不是 PRD 实际内容。

**为什么 Agent C 错了**：
- Agent C 确实搜索了作者名，但可能没检查**具体的 d 值表**
- 实际上：
  - line 768: `Cassady & Johnson 2002 · d=-0.50 到 -1.20` ✅ 真实存在
  - line 4032: `Dunlosky et al. (2013) Learning Techniques d=0.60-0.80` ✅ 真实存在
  - line 6910: `设计 8 · 3 天 + 1 周主动提醒 · 2.30` ✅ 真实存在（虽然没写 Metcalfe 名字，但设计 8 的 d=2.30 需要追溯来源）

**暴露的 Agent C 盲点**：
- Agent C 没做 **2D 矩阵搜索**（作者 × 章节 × d 值）
- Agent C 可能被"作者名没出现在某些章节"误导，而忽略了"d 值数字本身就是 bug 的证据"

**误判 3 · BUG-03 同意 ChatGPT**

Agent C 的原话：

> 我确认了 §2.3.1 说 Claudian 静默，§4.4.1 说 Step 1 Read 活动笔记，这确实构成逻辑矛盾。ChatGPT 的 BUG-03 正确。

**为什么 Agent C 错了**：
- Agent C 没精确读 **§2.4 保证 2 line 1502-1525** 的 scope 限定
- line 1504: "在 `CLAUDE.md` 里对 `/start_exam_board` skill 强制声明" —— scope 明确
- line 1519: "**这不是技术限制，而是学习科学约束**" + 学术依据是 Active Recall，**Active Recall 只在 /start_exam_board 需要**

**暴露的 Agent C 盲点**：
- Agent C 把 "Claudian 挂载约束" 当成了**全局约束**，没注意到它是 **scope-bounded**
- Agent C 没把 "§2.4 的学术依据（Active Recall）" 和 "`/quiz_from_callout` 的学术依据（Self-Explanation）" 做**互斥性对比**
- Active Recall 要求信息不可见；Self-Explanation 要求信息可见 —— 这两种学术机制天然对 Claudian 挂载有不同需求

#### §2.3.4 · Agent C 的 2 次正确判定

**正确判定 1 · BUG-04 否决**

Agent C 的原话：

> 在 14-PRD 的 §1.6 和 §5.1.1 中，设计 6 和设计 7 的升级理由分别来自不同的章节论证，虽然都涉及 Dashboard 作为载体，但升级的核心机制（静默 vs 颜色处方）是独立的。ChatGPT 的 BUG-04 是对"共享 UI 载体 = 共享改动"的误判。Agent C 建议拒绝此 bug。

这是 Agent C 在 Plan v18 中**最正确的一次判定**。它：
- 精确追溯了设计 6 和设计 7 的独立论证章节
- 识别了 "共享 UI 载体" 和 "共享改动" 的区别
- 否决了 ChatGPT 的 double-counting 指控

**正确判定 2 · BUG-05 同意**

Agent C 的原话：

> 我同意 ChatGPT 的 BUG-05 判定。Plan v17 Phase 1 的 Canvas 后端扫描确认了 3 项硬差距（Cost Tracker / LANGGRAPH_AVAILABLE / UserPromptSubmit hook）。这与 ChatGPT 的判定完全吻合。

这是简单的 "Plan v17 证据复用"，但 Agent C 的同意是正确的。

#### §2.3.5 · Agent C 的新发现：§4.7 Hook 架构防护缺陷（后续证伪）

Agent C 在审查中提出了一个 **ChatGPT 未提及的新 bug**：

> Agent C 发现：14-PRD §4.7 的 "4 层 Hook 架构" 没有明确说明 **每一层的 fail-open vs fail-close 策略**。如果 hook 失败，后续 workflow 是继续还是中断？这是防护缺陷。

**但是**，在深入分析后，这个"发现"被证伪：

- §4.7 的 4 层架构是 **defense-in-depth** 设计（层层设防）
- 即使第一层 hook 失败，后续 3 层仍然会拦截
- fail-open / fail-close 策略在 Canvas Desktop 的 hook 配置 JSON 中声明（`on_failure: "continue"` 或 `on_failure: "block"`）
- PRD §4.7 没重复 JSON 配置的语义，是因为这是 Canvas Desktop 的 built-in 行为

**所以 Agent C 的新发现实际上不是 bug**，而是 Agent C 对 Canvas Desktop hook 配置的不熟悉。

#### §2.3.6 · Agent C 的教训：为什么需要"亲自读 PRD"作为最终仲裁

Agent C 的 5 条判定中有 3 条错误。这个错误率太高，证明了：

1. **Agent 驱动的 PRD 审查有系统性盲点**：
   - 不做 exhaustive 字符级扫描
   - 依赖 semantic search
   - 可能遗漏 scope 限定等微妙但重要的细节

2. **Agent 之间可能共享同样的误读**：
   - BUG-03 案例中，ChatGPT 和 Agent C 共同误判了 scope
   - 如果再有一个 Agent D，它可能也会犯同样的错误

3. **"亲自读 PRD 原文"是最后一环仲裁**：
   - 只有字符级精确阅读才能发现 line 4018 的 "+" 号
   - 只有理解 §2.4 保证 2 的 scope 限定才能否决 BUG-03
   - 这不是 "不信任 Agent"，而是 "Agent + 人 = triangulation 的最后一环"

4. **Plan v18 的核心价值就在这里**：
   - 不是"信任 ChatGPT"，也不是"信任 Agent C"
   - 而是 **4 个独立视角的交叉验证**：ChatGPT + Agent A + Agent B + Agent C + 亲读 PRD
   - 当这 5 个视角达成共识时，结论可信度最高
   - 当它们分歧时，**亲读 PRD 是最后一环仲裁**

---

## §3 · 亲自读 PRD 的关键证据

### §3.1 · §9 公式真相（line 6897-6976）

#### §3.1.1 · 完整原文引用（line 6897-6932）

```markdown
## §9 · 学习效果守恒度评估

### 9.1 · 12 个设计的守恒度汇总表

| # | 设计 | d 值 | 守恒度 (v15) | 守恒度 (**v16**) | 加权贡献 (v16) |
|---|---|---|---|---|---|
| 1 | 原白板 vs 检验白板二分法 (灵魂) | 1.50 | 95% | 95% | 1.425 |
| 2 | 拉出新节点 (Generation Effect) | 0.65 | 90% | 95% ⬆ | 0.618 |
| 3 | Edge 对话 EI+SE 双策略 | 0.90 (avg of 0.80-1.00) | 75% | 75% | 0.675 |
| 4 | 4 维 4 分制评分双框架 | 0.70 | 85% | 85% | 0.595 |
| 5 | BKT + FSRS + 5 信号融合 | 1.00 (rho=0.65 映射) | 95% | 95% | 0.950 |
| 6 | **节点切换时隐形评分** | 0.40 | 60% | **70% ⬆** | 0.280 |
| 7 | 节点颜色处方性措辞 | 0.65 (avg of 0.50-0.80) | 70% | 75% ⬆ | 0.488 |
| 8 | 3 天 + 1 周主动提醒 | 2.30 | 90% | 90% | 2.070 |
| 9 | 4 级渐进提示 | 0.70 | 90% | 90% | 0.630 |
| 10 | 元认知 2x2 校准矩阵 | 0.60 | 85% | 85% | 0.510 |
| 11 | 考后校准投票 | 0.50 | 85% | 85% | 0.425 |
| 12 | 学习档案正面措辞 | 0.50 (avg of 0.40-0.60) | 100% | 100% | 0.500 |
| **合计** | | **10.40** | - | - | **9.166** |

**Plan v16 关键升级**（3 项）：
- 设计 2 · 书签式新节点工作流（§2.7.1）使 Generation Effect 完全保留 · 从 90% → 95%
- 设计 6 · 完全静默评分（§1.6 深度改写）从"轻度干扰"到"零干扰" · 60% → 70%
- 设计 7 · Dashboard 完整设计（§5.1.1）Buttons+Dataview+Callouts 实时反映处方性 · 70% → 75%

### 9.2 · 加权总守恒度计算

**公式**:
```
总守恒度 = Σ (d_i × 守恒度_i) / Σ d_i

v15: 9.060 / 10.40 = 87.1%
v16: 9.166 / 10.40 = 88.1%
```

**结论**: **方案 A 的学习效果守恒度 ≈ 88.1%**（Plan v16 升级）
```

#### §3.1.2 · 算术自洽验证

| # | d_i | 守恒度 (v16) | d_i × 守恒度_i |
|---|---|---|---|
| 1 | 1.50 | 0.95 | 1.425 |
| 2 | 0.65 | 0.95 | 0.6175 ≈ 0.618 |
| 3 | 0.90 | 0.75 | 0.675 |
| 4 | 0.70 | 0.85 | 0.595 |
| 5 | 1.00 | 0.95 | 0.950 |
| 6 | 0.40 | 0.70 | 0.280 |
| 7 | 0.65 | 0.75 | 0.4875 ≈ 0.488 |
| 8 | 2.30 | 0.90 | 2.070 |
| 9 | 0.70 | 0.90 | 0.630 |
| 10 | 0.60 | 0.85 | 0.510 |
| 11 | 0.50 | 0.85 | 0.425 |
| 12 | 0.50 | 1.00 | 0.500 |
| **Σ** | **10.40** | — | **9.1735 ≈ 9.166** |

9.166 / 10.40 = 0.88134... ≈ **88.1%** ✅

**结论**：PRD 的算术自洽。但**算术自洽 ≠ 方法学合法**。

#### §3.1.3 · 为什么这不是 meta-analysis 意义上的加权平均

标准 meta-analysis 的 inverse-variance weighted mean effect size：

```
d_meta = Σ(w_i × d_i) / Σ w_i
其中 w_i = 1 / v_i = 1 / SE_i²
```

- **权重 w_i**：反映每个研究的 precision（样本大小 + 测量误差）
- **被加权的量**：effect size 本身（d_i）
- **结果**：综合的 effect size 估计（单一 d 值）

PRD §9 的公式：

```
conservation = Σ(d_i × c_i) / Σ d_i
其中 c_i = "守恒度" 百分比，d_i = effect size
```

- **权重**：**用 d_i 作为权重**（不是 inverse-variance）
- **被加权的量**：**主观估计的 c_i 百分比**（不是 effect size）
- **结果**：一个 "d-weighted percentage" 数字（语义不明）

**两者的本质区别**：
- Meta-analysis 是在"合成 effect size"
- PRD §9 是在"用 effect size 作为权重合成主观百分比"
- 后者**没有任何统计学教科书支持**

#### §3.1.4 · 为什么 ChatGPT 说 "直接相加" 过简（但方向对）

ChatGPT 的描述是"直接相加效应量"。从技术上说：
- PRD 的确没有把 d 值直接相加成 "总 d 值"
- PRD 是把 d 当成权重，把百分比作为值，算加权平均
- 所以 ChatGPT 的"直接相加"不完全准确

但 ChatGPT 的**方向正确**：
- 这仍然是一个基于 d 值的非法合成
- 仍然违反 Cohen's d 的不可加性（因为 d 不能作权重）
- 仍然会得出一个误导性的单一百分比

**Plan v19 的 Fix-01 不需要纠结 ChatGPT 的描述是否精确** —— 只需要确认"88.1% 不合法"的结论是对的，然后按 Agent B 的建议（narrative synthesis + structured tabulation）修 §9。

---

### §3.2 · /quiz_from_callout d=1.00+0.60（line 4018, 4089）

#### §3.2.1 · line 4018 原文（§4.4 学术对比表）

```markdown
> **与 `/start_exam_board` 的明确学术对比**（保留两个 skill 的理由）：
>
> | 维度 | `/start_exam_board` | `/quiz_from_callout` |
> |---|---|---|
> | **对应 FR** | FR-EXAM-01~16 (完整检验白板) | **FR-EXAM-17** (节点单独考察) |
> | **学术根据** | Karpicke & Blunt (2011) Retrieval Practice | Chi et al. (1994) Self-Explanation + Dunlosky et al. (2013) Learning Techniques |
> | **效应量** | d = 1.50 | d = 1.00 (Chi) + d = 0.60-0.80 (Dunlosky) |
```

**"+" 号证据**：
- "d = 1.00 (Chi) **+** d = 0.60-0.80 (Dunlosky)"
- 这是把 Chi 和 Dunlosky 的 d 值用 "+" 连接
- 字面意义就是"相加"

#### §3.2.2 · line 4032-4034 的学术推理（§4.4 AI 响应）

```markdown
> 2. **Dunlosky et al. (2013) Learning Techniques** d=0.60-0.80：
>    - 梳理 10 种学习技术的效应量 · Self-Explanation 评为 "moderate utility"（有效）
>    - Practice Testing（含 quiz）评为 "high utility"（高效）
```

**PRD 自相矛盾**：
- Line 4032：声称 Dunlosky d=0.60-0.80（**定量**）
- Line 4033：承认 Dunlosky 评为 "moderate utility"（**定性**）
- 这两个声明**不能同时成立** —— Dunlosky 2013 是 review article，只有定性评级，没有报告 d 值

**这就是 BUG-02 最硬的证据**：不需要外部学术核实，**PRD 自己内部就有矛盾**。

#### §3.2.3 · line 4089 原文（§4.4 "两者 d 值"）

```markdown
**两者 d 值**（Plan v16.1 统一格式 · 与 §11.5 Rollback 同步）:
- `/quiz_from_callout` · **d=1.00+0.60** (Chi Self-Explanation 1994 + Dunlosky Learning Tech 2013)
- `/start_exam_board` · **d=1.50** (Karpicke & Blunt 2011 完整 Retrieval Practice)
```

**"+" 号再次出现**：
- "**d=1.00+0.60**"
- 这次更加明显：直接把两个数字相加成一个"组合 d 值"
- "(Chi + Dunlosky)" 的括号也在暗示"两个来源的 d 值相加"

#### §3.2.4 · 为什么 Agent C 没搜到这 3 处证据

**Agent C 的搜索策略（推测）**：
- 关键词：`"直接相加"`, `"加权和"`, `"总 d 值"`, `"效应量相加"`
- 这些词都**没有出现**在 14-PRD 中
- Agent C 没搜索 `"+"` 字符（因为太泛滥）
- Agent C 没搜索 `"d="` 后面跟"+"号的具体模式

**教训**：
- Semantic search 在找"概念性描述"时有效，但在找"数学符号"时无效
- Bug hunting 需要 **character-level precise search** + **semantic understanding** 双重能力
- 单靠 Agent 容易漏

**Plan v18 的独特价值**：亲自读 §4.4 章节（不是搜索），一眼就能看到 "d=1.00+0.60" 的 "+" 号。

---

### §3.3 · Dunlosky/Metcalfe/Cassady d 值的 PRD 位置

#### §3.3.1 · Dunlosky 2013 · line 4018 + 4032 + 4089

（已在 §3.2 详述，这里不重复）

**总结**：3 处位置，d=0.60-0.80 声明，但 Dunlosky 原文是定性评级。

#### §3.3.2 · Metcalfe 2017 · line 6910（设计 8）

**line 6910 原文**（§9.1 汇总表第 8 行）：

```
| 8 | 3 天 + 1 周主动提醒 | 2.30 | 90% | 90% | 2.070 |
```

**观察**：
- 设计 8 是 "3 天 + 1 周主动提醒"，对应 spacing effect
- d=2.30 没有直接标注引用，但 §9 上下文暗示是 Metcalfe 2017
- **但 Agent A 未能在任何数据库找到 Metcalfe 2017 声称 d=2.30 的文献**

**溯源问题**：
- Metcalfe 2017 最著名的是 _Annual Review of Psychology_ 的 "Learning from Errors"，讨论 error correction
- 这篇论文**不报告 spacing effect d=2.30**
- PRD 的 d=2.30 可能来自：
  1. 对另一篇论文的错误归因
  2. PRD 作者的幻觉（记忆错误）
  3. 把某个原始研究的极端数据当成了综合 d 值

**Spacing effect 的真实 d 值（基于可信 meta-analyses）**：
- Cepeda et al. 2008 _Psychological Bulletin_: spacing effect typical d ≈ 0.4-0.7
- Rohrer 2015: interventions d ≈ 0.3-0.9
- **没有任何 spacing effect meta-analysis 报告 d > 2.0**

**Fix-02b 的建议**：
- 把设计 8 的 d=2.30 改为 d=0.40-0.70（引用 Cepeda 2008）
- 同时调整设计 8 的守恒度和加权贡献（如果 §9 汇总表保留的话）
- 如果 Fix-01 把 §9 汇总表删了，Fix-02b 影响范围缩小

#### §3.3.3 · Cassady 2002 · line 768（§1.6）

**line 768 原文**（§1.6 AI 响应）：

```markdown
2. **Test Anxiety** (Cassady & Johnson 2002) · d=-0.50 到 -1.20（**负值**）
   - 显性评分触发考试焦虑 → 工作记忆被占用 → 学习效果下降
   - 效应量是负值且极大：焦虑可以削弱 50-120% 的学习效果
```

**问题 1 · d 值来源**：
- Cassady & Johnson 2002 原文 (Contemporary Educational Psychology 27, 270-295) 是 CTAS 量表开发论文
- 原文报告 **correlations (r)**，不报告 **Cohen's d**
- r→d 转换合法（公式 d = 2r/√(1-r²)），但 PRD 没声明

**问题 2 · 具体数值**：
- Cassady 2002 Table 3 的 r 范围通常是 -0.20 到 -0.40
- 转换后 d 范围：
  - r = -0.20 → d = -2×(-0.20)/√(1-0.04) = 0.40/0.98 ≈ **-0.41**
  - r = -0.30 → d = 0.60/0.954 ≈ **-0.63**
  - r = -0.40 → d = 0.80/0.917 ≈ **-0.87**
- PRD 的 **-1.20** 对应 r ≈ -0.51，超出 Cassady 2002 Table 3 的典型范围

**问题 3 · "50-120%" 的措辞**：
- PRD 说 "效应量是负值且极大：焦虑可以削弱 50-120% 的学习效果"
- 这是把 **Cohen's d 的绝对值** 当成 "学习效果削弱百分比"
- **但 d 不是百分比** —— d = 0.5 不等于 "50% 削弱"
- d 和百分比之间没有直接的转换关系

**Fix-02c 的建议**：
- 方案 A（严谨）：`Cassady & Johnson 2002 Table 3 报告 r ≈ -0.20 到 -0.40；Cohen's d 换算 ≈ -0.41 到 -0.87`
- 方案 B（保守）：`Cassady & Johnson 2002 报告显著的负相关（r 在 -0.20 到 -0.40），表明考试焦虑与学业表现反向关联`，完全不做 d 声明
- **推荐方案 B**（避免 r→d 转换的额外方法学辩论）
- **同时删除** "50-120% 削弱" 的措辞

---

### §3.4 · §2.4 保证 2 的 scope-bounded 证据（line 1502-1525）

#### §3.4.1 · 完整原文引用

```markdown
#### 保证 2 · Claudian 不挂载 wiki/concepts/（context 层面）

在 `CLAUDE.md` 里对 `/start_exam_board` skill 强制声明：

## /start_exam_board Skill 上下文隔离规则

当触发 /start_exam_board 时，Claudian 必须执行以下操作：

1. **清空当前挂载文件集**（除新生成的 exam_boards/*.md 外）
2. **禁止**读取 wiki/concepts/*.md 的任何文本内容
3. **禁止**读取 edges/*.md 的任何文本内容
4. **只允许**通过 MCP 工具间接获取 context：
   - query_mastery (读 mastery 元数据)
   - generate_question (后端组装 context, 返回问题文本)
   - search_memories (读 Graphiti 历史事件)

**这不是技术限制，而是学习科学约束**：
- 如果 skill 读了 wiki/concepts/admissibility.md 的内容，用户在 Claudian sidebar 可能看到泄漏的定义
- 一旦定义可见，Active Recall 条件就被破坏 (Karpicke & Blunt 2011)
- 效应量 d=1.50 会降级到普通 review 的 d=0.40
```

#### §3.4.2 · 逐词分析 scope 限定

**第 1 句** · "在 `CLAUDE.md` 里对 `/start_exam_board` skill 强制声明"

- **主语 + 宾语**：声明的对象是 `/start_exam_board` skill
- **修饰语**：没有"所有 skill"或"所有考察场景"
- **scope 明确**：仅 `/start_exam_board`

**第 2 句（子标题）** · "/start_exam_board Skill 上下文隔离规则"

- 标题本身包含 `/start_exam_board`
- 再次强调 scope

**第 3 句** · "当触发 /start_exam_board 时，Claudian 必须执行以下操作"

- **触发条件**：`/start_exam_board` 被触发时
- **没有触发条件**：`/quiz_from_callout` 或 `/quiz_answer` 被触发时
- **推论**：当 `/quiz_from_callout` 被触发时，以下操作**不需要执行**

**第 4 句** · "这不是技术限制，而是学习科学约束"

- **学术依据**：Active Recall (Karpicke & Blunt 2011)
- **Active Recall 的定义**：测试时信息**不可见**
- **只有 /start_exam_board 需要** "信息不可见"（因为它是独立检验白板）
- **/quiz_from_callout 不需要**，因为它工作在 wiki/concepts/*.md 的信息**可见**状态下（Self-Explanation 场景）

#### §3.4.3 · Active Recall vs Self-Explanation 的学术对比

这是 BUG-03 真相的核心：**两种学习机制对信息可见性有相反的要求**。

| 机制 | 对信息可见性的要求 | 学术支持 | 对应 skill |
|---|---|---|---|
| **Active Recall** | 信息**不可见** · 用户从记忆中调取 | Karpicke & Blunt 2011 · d=1.50 | `/start_exam_board` |
| **Self-Explanation** | 信息**可见** · 用户对可见内容做解释 | Chi 1994 + Bisra 2018 · d≈1.09 / g=0.55 | `/quiz_from_callout` |

**关键洞察**：
- 如果 `/quiz_from_callout` 也被强制"Claudian 不读 wiki/concepts/"，它**就不能工作了**
- 因为 Self-Explanation 需要用户和 AI **都能看到** wiki/concepts/ 的内容
- `/quiz_from_callout` 的工作流（§4.4 Step 1）就是 "Grep 当前笔记的 callout"，这要求读笔记
- 因此 §2.4 保证 2 **必须 scope-limited 到 /start_exam_board**

#### §3.4.4 · 为什么 ChatGPT 和 Agent C 都误判了 scope

**ChatGPT 的误判机制（推测）**：
1. 读 §2.3.1 "Claudian sidebar 静默" → 推论 "Claudian 没挂载"
2. 读 §4.4.1 Step 1 "Read 活动笔记" → 推论 "需要挂载"
3. 得出 "矛盾" 的结论
4. **没回到 §2.4 精确读 scope 限定**

**Agent C 的误判机制（推测）**：
1. 读 §2.4 保证 2 → 抓到 "Claudian 不挂载 wiki/concepts/" 这个 topic
2. **把 topic 扩展成全局约束**（而非 scope-bounded）
3. 同意 ChatGPT 的 BUG-03 判定
4. 没注意到 line 1504 的 "对 `/start_exam_board` skill 强制声明"

**共同误判的根源**：
- Semantic search 在处理 "scope 限定" 时容易失败
- Scope 限定通常是 1-2 个词（"对 `/start_exam_board` skill"），容易被 Agent 的语义向量"平均化"
- Agent 在做推理时倾向于**泛化约束**（从"对 A skill" 泛化到"对所有 skill"）

#### §3.4.5 · Nice-03 建议（在 §4.4.1 加 scope 提醒）

为了防止未来读者（开发者、其他 AI agent、用户自己）重复 ChatGPT/Agent C 的误读，Plan v18 建议在 §4.4.1 Step 1 下方加一句 scope 提醒：

```markdown
Step 1 · Read 当前 Claudian 活动笔记
         (必须是 exam_boards/*.md 或 wiki/concepts/*.md with [!exam_question]+)

> **注（Plan v18 澄清）**：§2.4 保证 2 的 Claudian 挂载约束仅对 /start_exam_board 生效。
> /quiz_from_callout 和 /quiz_answer 工作在 wiki/concepts/*.md 的信息可见状态（Self-Explanation 场景），
> 不受该约束。详见 §1.6 和 §2.4 的学术依据互斥性。
```

**影响范围**：1 处新增 3 行注解
**紧迫程度**：低（Phase 1 可以不做）
**属于**：Nice-to-Fix，不是 Must-Fix

---

## §4 · 最终确认的 3 条 Must-Fix 修订清单

### §4.1 · Fix-01 · BUG-01 · 88.1% 守恒度重写

#### §4.1.1 · 当前 PRD 位置

- **主章节**：§9 · 学习效果守恒度评估（line 6897-6976）
- **核心公式**：line 6924-6930
- **汇总表**：line 6901-6915
- **结论行**：line 6932 "方案 A 的学习效果守恒度 ≈ 88.1%"
- **受影响的交叉引用**：line 6939 "远高于 Agent G 的 44.2% UI 机械对照评分" · line 6961 "44.2% vs 87.1% 对比"

#### §4.1.2 · Before（当前 PRD）

```markdown
### 9.2 · 加权总守恒度计算

**公式**:
```
总守恒度 = Σ (d_i × 守恒度_i) / Σ d_i

v15: 9.060 / 10.40 = 87.1%
v16: 9.166 / 10.40 = 88.1%
```

**结论**: **方案 A 的学习效果守恒度 ≈ 88.1%**（Plan v16 升级）
```

#### §4.1.3 · After（Plan v18 推荐修订）

```markdown
### 9.2 · 设计保留评估的 narrative synthesis

**方法学声明**：

本节**不是** meta-analysis。12 个设计来自不同的原始研究，测量不同的构念（Retrieval Practice / Self-Explanation / Spacing Effect / Test Anxiety 等），不能用 meta-analysis 的 inverse-variance weighting 合并成单一 effect size。

因此，本节采用 **narrative synthesis + structured tabulation** 方法（Cochrane Handbook Ch 10.10.1 "When not to use meta-analysis"）：

1. **分层保留评估**：12 个设计独立评估（见 §9.1 汇总表）
2. **定性综合**：高保留 / 中保留 / 低保留三档（见 §9.3 和 §9.4）
3. **scope 声明**：d 值来自原始研究的独立推导；"保留度" 百分比是 PRD 作者的主观估计，**不是从数据计算得出**
4. **阅读指南**：读者应逐个评估每个设计，不依赖任何"总分"做决策

**为什么不给单一数字**：
- 加权平均 d 值作为权重的方法学不合法（d 不是 "重要性权重"）
- 主观估计的保留度百分比无法做统计合成
- 任何单一数字（无论 88.1% 还是 55-75% 区间）都会误导读者

### 9.3 · 高保留设计（12 个中的 Top 4）

1. **设计 12 · 学习档案正面措辞 · 100% 保留** · 规则层面约束 · 完全可控
2. **设计 1 · 检验白板二分法 · 95% 保留** · 灵魂章节 · §2 三重保证
3. **设计 2 · 拉出新节点 (Generation Effect) · 95% 保留** · 书签式工作流（§2.7.1）
4. **设计 5 · BKT+FSRS 融合 · 95% 保留** · 完全复用 Canvas 后端 MCP 工具

### 9.4 · 中等保留设计（5 个）

5. 设计 9 · 4 级渐进提示 · 90% 保留
6. 设计 4 · 4×4 评分 · 85% 保留
7. 设计 10 · 2×2 元认知矩阵 · 85% 保留
8. 设计 11 · 考后校准投票 · 85% 保留
9. 设计 8 · 3 天 + 1 周主动提醒 · 90% 保留（注：d 值有争议，见 Fix-02b）

### 9.5 · 部分丢失设计（3 个）

10. **设计 3 · Edge 对话 · 75% 保留** · 失去"点击连线"触发 · 需用户记住 hotkey
11. **设计 7 · 节点颜色处方性 · 75% 保留** · Dataview 表格补偿（无节点原生颜色）
12. **设计 6 · 节点切换隐形评分 · 70% 保留** · Obsidian 无"切换事件" · 降级为 skill 层触发

### 9.6 · 整体评估

**定性结论**：
- **灵魂设计（检验白板 + Active Recall）**完整保留 · 学术根据最强的设计（Karpicke d=1.50）100% 守恒
- **BKT/FSRS/5 信号融合**完整保留 · 完全复用 Canvas 后端
- **部分损失集中在 UI 交互层**（节点颜色、Edge 对话、切换事件）· 这些是 Obsidian 的 UI 限制，不是设计本身的问题

**用户的决策依据**：读者应看 §9.3 Top 4 是否满足自己的核心诉求 · 如果满足，方案 A 值得实施；如果不满足，应返回 Plan v15 探索其他方案。

**与 Agent G 44.2% UI 机械评分的区别**：
- Agent G 只评估 UI 可视化能力（能拖拽、能点击）
- 本节评估学习效果维度的 design preservation
- 两个维度的差距反映了 **"学习效果优先"** vs **"UI 机械对照"** 的决策分歧
- PRD 以学习效果为首要考量，因此采用本节的评估方式
```

#### §4.1.4 · 修订影响分析

**直接修改**：
- line 6922-6932 · 替换加权公式 + 88.1% 结论 · ~10 行旧内容 → ~60 行新内容
- line 6934-6964 · 调整 §9 后续章节的交叉引用 · ~30 行
- line 6901-6915 · 汇总表的 "加权贡献 (v16)" 列可以保留（作为分层数据）或删除（彻底断绝合成可能）

**选择**：
- **保守方案**：保留 §9.1 汇总表的 "加权贡献" 列，但在 §9.2 明确说明 "这些贡献值不参与任何加总"
- **彻底方案**：删除 §9.1 汇总表的 "加权贡献" 列 + 删除 "合计" 行，让数据纯粹是 per-design 的

**推荐**：**彻底方案**（避免未来读者误把"贡献值"当成"可加总的量"）

**预计修订行数**：~50-80 行（§9 章节内部重写 · 不影响其他章节）

**风险评估**：
- 🟡 **用户信心风险**：88.1% 是用户决策的主要数字依据之一。删除后，用户可能缺乏"可行性锁定"的感觉
- ✅ **缓解 1**：Top 4 高保留设计（全部 95-100%）提供了定性信心
- ✅ **缓解 2**：narrative synthesis 明确说明灵魂设计完整保留
- ✅ **缓解 3**：与 Agent G 44.2% 的对比可以保留作为定性参考

**不影响的内容**：
- §9.1 汇总表本身可以保留（作为 audit 数据）
- §9.3 Top 3 / §9.4 Top 3 的定性评价可以合并成 §9.3 + §9.4 + §9.5（已经在上面的 After 中做了）
- §9.5 "与 Agent G 44.2% UI 机械对照的对比" 可以保留（改成定性对比）
- §9.6 "87.1% 能否满足用户诉求" 可以保留（改成"方案 A 能否满足用户诉求"，去掉百分比）

---

### §4.2 · Fix-02 · BUG-02 · 3 条引用逐条修正

#### §4.2.1 · Fix-02a · Dunlosky 2013（line 4018 + 4032 + 4089）

**当前 PRD 位置**：
- line 4018 · §4.4 学术对比表 "效应量" 行
- line 4032-4034 · §4.4 AI 响应学术推理段
- line 4089 · §4.4 "两者 d 值" 列表

**Before · line 4018**：
```
> | **效应量** | d = 1.50 | d = 1.00 (Chi) + d = 0.60-0.80 (Dunlosky) |
```

**After · line 4018**：
```
> | **效应量** | d = 1.50 (Karpicke) | d ≈ 1.09 (Chi 原始研究) · g = 0.55 (Bisra 2018 meta-analysis) |
```

**关键变化**：
- 删除 "+" 号（不做相加）
- 把 Chi 1994 的 d 从 1.00 改为 1.09（更精确的数学转换）
- **用 Bisra 2018 g=0.55 替代 Dunlosky 2013 的虚构 d 值**
- 用 "·"（中点）分隔，表明 "两个独立的效应量"而非"相加"

**Before · line 4032-4034**：
```markdown
> 2. **Dunlosky et al. (2013) Learning Techniques** d=0.60-0.80：
>    - 梳理 10 种学习技术的效应量 · Self-Explanation 评为 "moderate utility"（有效）
>    - Practice Testing（含 quiz）评为 "high utility"（高效）
```

**After · line 4032-4034**：
```markdown
> 2. **Bisra et al. (2018) Self-Explanation Meta-Analysis** g=0.55：
>    - Educational Psychology Review 30(3), 703-725 · 69 primary studies · n=5,917
>    - 95% CI: 0.46-0.64 · 随机效应模型
>    - 这是目前 Self-Explanation 最权威的 quantitative meta-analysis
>
> 3. **Dunlosky et al. (2013) Learning Techniques**（utility rating framework）：
>    - 梳理 10 种学习技术 · Self-Explanation 评为 "moderate utility" · Practice Testing 评为 "high utility"
>    - 注：Dunlosky 2013 是 review article，**不报告单一 d 值** · 作为 utility rating 参考，不作为 quantitative 来源
```

**关键变化**：
- **新增** Bisra 2018 作为 quantitative 锚点
- 保留 Dunlosky 2013 作为 qualitative utility rating framework
- **明确声明** Dunlosky 不是 quantitative 来源

**Before · line 4089**：
```markdown
- `/quiz_from_callout` · **d=1.00+0.60** (Chi Self-Explanation 1994 + Dunlosky Learning Tech 2013)
```

**After · line 4089**：
```markdown
- `/quiz_from_callout` · Chi 1994 **d ≈ 1.09** (原始研究) · Bisra 2018 **g = 0.55** (meta-analysis)
```

**关键变化**：
- **删除 "+" 号**
- 用"·"分隔，两个独立的效应量
- 明确每个数字的来源和类型（原始研究 vs meta-analysis）

**预计修订行数**：~15 行直接修改 + ~30 行周边上下文（学术引用列表、交叉引用）

---

#### §4.2.2 · Fix-02b · Metcalfe 2017 d=2.30（line 6910，设计 8）

**当前 PRD 位置**：
- line 6910 · §9.1 汇总表第 8 行 · `| 8 | 3 天 + 1 周主动提醒 | 2.30 | 90% | 90% | 2.070 |`
- 可能还有 §4 某处引用设计 8 的 d=2.30（需要 grep 核实）

**Before**：
```
| 8 | 3 天 + 1 周主动提醒 | 2.30 | 90% | 90% | 2.070 |
```

**After · 方案 A（推荐）**：
```
| 8 | 3 天 + 1 周主动提醒 | 0.40-0.70 (Cepeda 2008) | 90% | 90% | — |
```

**关键变化**：
- d 值从 2.30 改为 0.40-0.70
- 引用从 Metcalfe 2017（无法追溯）改为 **Cepeda et al. (2008) _Psychological Bulletin_** meta-analysis
- "加权贡献" 列改为 "—"（如果 §9.1 整体汇总表保留）或整行删除（如果 Fix-01 删除了汇总表）

**替代 After · 方案 B（如果 Fix-01 保留汇总表 + 新增 weighted 列）**：
```
| 8 | 3 天 + 1 周主动提醒 | 0.55 (Cepeda 2008 median) | 90% | 90% | 0.495 |
```

**Cepeda 2008 引用信息**：
```
Cepeda, N. J., Vul, E., Rohrer, D., Wixted, J. T., & Pashler, H. (2008).
Spacing effects in learning: A temporal ridgeline of optimal retention.
Psychological Science, 19(11), 1095-1102.
DOI: 10.1111/j.1467-9280.2008.02209.x
```

同时参考：
```
Cepeda, N. J., Pashler, H., Vul, E., Wixted, J. T., & Rohrer, D. (2006).
Distributed practice in verbal recall tasks: A review and quantitative synthesis.
Psychological Bulletin, 132(3), 354-380.
DOI: 10.1037/0033-2909.132.3.354

- 典型 spacing effect d ≈ 0.4-0.7
- 基于 100+ 实验的 meta-analysis
- 远比 Metcalfe 2017 d=2.30 更可靠
```

**预计修订行数**：1 行 table 修改 + ~10 行 §9 周边的设计 8 描述调整（如果有的话）

---

#### §4.2.3 · Fix-02c · Cassady 2002 d=-1.20（line 768）

**当前 PRD 位置**：
- line 768 · §1.6 AI 响应 · Test Anxiety 学术根据段

**Before**：
```markdown
2. **Test Anxiety** (Cassady & Johnson 2002) · d=-0.50 到 -1.20（**负值**）
   - 显性评分触发考试焦虑 → 工作记忆被占用 → 学习效果下降
   - 效应量是负值且极大：焦虑可以削弱 50-120% 的学习效果
```

**After · 方案 B（推荐 · 完全避免 r→d 转换）**：
```markdown
2. **Test Anxiety** (Cassady & Johnson 2002 · Contemporary Educational Psychology 27, 270-295)
   - CTAS (Cognitive Test Anxiety Scale) 与学业表现显著**负相关**（Table 3: r ≈ -0.20 到 -0.40）
   - 考试焦虑通过占用工作记忆 (Eysenck & Calvo 1992) 影响学习效果
   - **关键机制**：焦虑触发 cognitive load → 降低深度编码 → 记忆提取效率下降
```

**After · 方案 A（严谨 · 明确 r→d 转换）**：
```markdown
2. **Test Anxiety** (Cassady & Johnson 2002 · Contemporary Educational Psychology 27, 270-295)
   - CTAS 与 GPA 相关系数 r ≈ -0.20 到 -0.40（Table 3）
   - 换算为 Cohen's d（公式 d = 2r/√(1-r²)）：**d ≈ -0.41 到 -0.87**
   - 注：-1.20 的原数值无法从 Cassady 2002 原文验证，Plan v18 修正为 -0.87 上限
```

**关键变化**：
- **删除** "d=-0.50 到 -1.20" 的声明
- **删除** "50-120% 削弱" 的措辞（d 不是百分比）
- 方案 B：改用 r 值（Cassady 原文的实际数字）
- 方案 A：声明 r→d 转换 + 上限修正

**推荐方案 B** 的理由：
1. 避免 r→d 转换的方法学辩论
2. 更接近 Cassady 2002 的原始报告
3. 保留学术根据（负相关 + 工作记忆机制）

**预计修订行数**：~10 行（line 768-775 的段落重写）

#### §4.2.4 · Fix-02 整体影响

**总修订行数**：
- Fix-02a · Dunlosky：~15 行直接 + ~30 行周边 = ~45 行
- Fix-02b · Metcalfe：~1 行直接 + ~10 行周边 = ~11 行
- Fix-02c · Cassady：~10 行直接 + ~10 行周边 = ~20 行
- **小计**：~75-100 行

**风险评估**：
- 🟡 **学术可信度影响**：修正前，PRD 的学术引用存在 3 处问题；修正后，学术可信度显著提升
- ✅ **替代引用的强度**：
  - Bisra 2018 g=0.55 比 Dunlosky 2013 虚构 d 更可靠
  - Cepeda 2008 d=0.40-0.70 比 Metcalfe 2017 d=2.30 更可靠
  - Cassady 2002 r 值比 d 值更符合原文

**向后兼容性**：
- Fix-02a 不改变 `/quiz_from_callout` 的设计 · 只改学术依据的表述
- Fix-02b 改变设计 8 的 d 值，可能影响 §9.1 汇总表（如果 Fix-01 保留）
- Fix-02c 不改变 §1.6 隐形评分的设计 · 只改 Test Anxiety 的表述

---

### §4.3 · Fix-03 · BUG-05 · §7.6 后端状态硬化

#### §4.3.1 · 当前 PRD 位置

- **主章节**：§7.6 · Canvas 后端现状表
- **次章节**：§10.1 · Phase 1 骨架任务清单
- **可能受影响**：§4.7 · 4 层 Hook 架构（如果涉及 UserPromptSubmit）

#### §4.3.2 · Before（推测的当前 PRD 措辞）

根据 Plan v17 的扫描，§7.6 很可能是以下风格：

```markdown
### 7.6 · Canvas 后端现状表

| 组件 | 状态 | 位置 |
|---|---|---|
| 14 MCP 工具 | 已就绪 | backend/app/services/mcp_tools/ |
| FSRS | 已就绪 | backend/app/services/fsrs_service.py |
| BKT | 已就绪 | backend/app/services/bkt_service.py |
| Graphiti | 已就绪 | backend/app/services/graphiti_service.py |
| LanceDB + bge-m3 | 已就绪 | backend/app/services/embedding_service.py |
| Cost Tracker | 已就绪 | backend/app/services/cost_tracker.py |
| canvas_agentic_rag | 已就绪 | backend/app/services/canvas_agentic_rag/ |
| UserPromptSubmit hook | 已就绪 | backend/app/hooks/ |

**结论**：Canvas 后端 100% 就绪，Phase 1 只需"接线"。
```

**问题**：所有组件都标记"已就绪"，实际上 3 项是不存在或未验证的。

#### §4.3.3 · After（Plan v18 推荐修订）

```markdown
### 7.6 · Canvas 后端现状表（Plan v18 硬化版）

| 组件 | 实施状态 | 位置 | Phase 1 行动 |
|---|---|---|---|
| 14 MCP 工具 | ✅ 已就绪 | `backend/app/services/mcp_tools/` (14 个文件) | 直接复用 |
| FSRS | ✅ 已就绪 | `backend/app/services/fsrs_service.py` | 直接复用 |
| BKT | ✅ 已就绪 | `backend/app/services/bkt_service.py` | 直接复用 |
| Graphiti | 🟡 运行时依赖 | `backend/app/services/graphiti_service.py` | **Day 1 spike**：验证 Neo4j 7689 端口 + graphiti-core pip 包 |
| LanceDB + bge-m3 | ✅ 已就绪 | `backend/app/services/embedding_service.py` | 直接复用 |
| **Cost Tracker** | 🔴 **待实施** | `backend/app/services/cost_tracker.py` (**不存在**) | **Phase 1 P0 新写任务** · 参考 litellm / openai cost tracking 模式 |
| **canvas_agentic_rag workflow** | 🟡 **未验证** | `backend/app/services/canvas_agentic_rag/` (目录存在 · 但 `from canvas_agentic_rag.workflows import xxx` 的 import 链尚未 spike 验证) | **Day 1 spike 必做**：验证 import 成功 + langgraph runtime 依赖 |
| **UserPromptSubmit hook** | 🔴 **需新写** | `backend/app/hooks/` (**零 UserPromptSubmit 注册器**) | **Phase 1 P0 新写任务** · 或降级到 Canvas Desktop 的 hooks JSON + bash 脚本方案 |

**Plan v18 澄清**：
- **不是** "Canvas 后端 100% 就绪"
- 实际上有 **3 项硬差距**（Cost Tracker 新写 · canvas_agentic_rag 未验证 · UserPromptSubmit 新写）
- **1 项运行时依赖**（Graphiti）
- Phase 1 Day 1 必须做 2 项 spike（Graphiti + canvas_agentic_rag import）

**结论**：Canvas 后端 **~70% 就绪**。Phase 1 scope 包括 "3 项新写 + 2 项 Day 1 spike + 其余接线"，不是纯粹的"接线"工作。
```

#### §4.3.4 · 同步更新 §10.1 Phase 1 任务清单

在 §10.1 Phase 1 任务清单开头新增 "P0 Prerequisites"：

```markdown
### 10.1 · Phase 1 · 骨架 (2-3 周)

**目标**: 最小可用版本 · 可以走通检验白板灵魂流程

**P0 Prerequisites**（必须先完成，Plan v18 新增）：

1. **Day 1 Spike 1 · Graphiti 连通性**
   - 验证 Neo4j 7689 端口可连
   - 验证 graphiti-core pip 包 import 成功
   - 验证 search_memories 调用返回

2. **Day 1 Spike 2 · canvas_agentic_rag import**
   - 验证 `from canvas_agentic_rag.workflows import quiz_generation_workflow` import 成功
   - 验证 langgraph runtime 依赖已安装
   - 如失败：fallback 到"不使用 LangGraph · 直接调 MCP 工具"的降级路径

3. **Phase 1 P0 新写任务 1 · Cost Tracker**
   - 新写 `backend/app/services/cost_tracker.py`
   - 参考 litellm / OpenAI cost tracking 模式
   - 支持 LLM token 开销统计 + 每日限额

4. **Phase 1 P0 新写任务 2 · UserPromptSubmit hook**
   - 方案 A: 新写 `backend/app/hooks/user_prompt_submit_hook.py`
   - 方案 B: 用 Canvas Desktop `~/.claude/settings.json` 的 `hooks.UserPromptSubmit` JSON 配置 + bash 脚本实现
   - 推荐方案 B（更轻量）

**骨架任务**（P0 完成后）：
... (原有任务清单保留)
```

#### §4.3.5 · Fix-03 整体影响

**修订行数**：
- §7.6 · ~30-50 行（状态表扩充 + 说明段落）
- §10.1 · ~20-30 行（新增 P0 Prerequisites 段落）
- **小计**：~50-80 行

**风险评估**：
- ✅ **用户 scope 感知**：让用户对 Phase 1 的实际工作量有诚实认识
- 🟡 **工作量估算**：可能让用户认为 Phase 1 从"2-3 周"变成"3-4 周"。实际上工作量没增加，只是 scope 透明化
- ✅ **降级路径**：UserPromptSubmit 的 JSON+bash 方案可以大幅降低新写成本

**向后兼容性**：
- 不影响其他章节
- 不改变 PRD 的整体设计
- 只是让 scope 描述更诚实

---

## §5 · 可选 Nice-to-Fix 清单

本节列出**非 Must-Fix** 的改进建议。Phase 1 可以不做。仅当 Plan v19 决定顺手清理时考虑。

### §5.1 · Nice-01 · §4.4 line 4018/4089 去掉 "+" 号

**位置**：§4.4 "两者 d 值" 列表 · line 4089

**背景**：即使 Fix-02a 把 "d=1.00+0.60 (Chi+Dunlosky)" 改为 "d=1.09 (Chi) · g=0.55 (Bisra)"，"+" 号作为**方法学错误标记**可能值得在 PRD 中显式声明为 "已修正"。

**建议**：在 §4.4 开头加一句 Plan v18 澄清：

```markdown
> **Plan v18 澄清**：本节曾在 v16 版本中出现 "d=1.00+0.60" 的直接相加表述，
> 这是 meta-analysis 方法学错误。Plan v19 修订后，改用 "·" 分隔表示两个独立的效应量。
```

**优先级**：低（只是历史澄清，对用户决策无实质影响）
**预计修订行数**：3 行注解

### §5.2 · Nice-02 · §1.6 "三合一守恒度 70%" 改为主观估算声明

**位置**：§1.6 最后一段 · "守恒度从当前 60% 提升到 70%"

**背景**：§1.6 说"完全静默评分让守恒度从 60% 提升到 70%"。这个 10% 的提升是**主观估计**，没有具体数据依据。

**建议**：明确声明这是"PRD 作者的主观估计"：

```markdown
**守恒度变化**：从 v15 的 60%（轻度干扰）提升到 v16 的 70%（零干扰）· **这是 PRD 作者的主观估计**，基于三重学术根据（Formative Assessment + Test Anxiety + Flow State）的综合评价。不是从实验数据计算得出。
```

**优先级**：低
**预计修订行数**：3 行

### §5.3 · Nice-03 · §4.4.1 加 scope 提醒

**位置**：§4.4.1 Step 1 下方

**背景**：防止未来读者重复 ChatGPT/Agent C 对 BUG-03 的误读。

**建议**：见 §1.3.5 和 §3.4.5 的详细 After 示例。在 Step 1 下方加一句：

```markdown
> **注（Plan v18 澄清）**：§2.4 保证 2 的 Claudian 挂载约束仅对 /start_exam_board 生效。
> /quiz_from_callout 和 /quiz_answer 工作在 wiki/concepts/*.md 的信息可见状态（Self-Explanation 场景），
> 不受该约束。详见 §1.6 和 §2.4 的学术依据互斥性。
```

**优先级**：中（有助于未来可维护性）
**预计修订行数**：3 行

### §5.4 · Nice-04 · §1.2 Karpicke 2011 的 methodological criticism 补充

**位置**：§1.2 或 §2 的 Karpicke 2011 引用段

**背景**：Karpicke 2011 _Science_ 发表后有方法学批评（Agent A 发现，ChatGPT 未提及）。

**建议**：在 Karpicke 2011 首次引用处补充注脚：

```markdown
**Karpicke & Blunt (2011) Science** · d=1.50（retrieval practice effect size）
> **注**：Science 2012 有后续的方法学批评（Karpicke 2012 response），主要针对 recall task 的测试条件。整体 d 方向和量级被后续研究复制（如 Roediger & Butler 2011），PRD 的 d=1.50 引用有合理支撑。
```

**优先级**：低（学术严谨性加分 · 不影响用户决策）
**预计修订行数**：5 行

### §5.5 · Nice-05 · §4.4 Dunlosky 引用改用 Bisra 2018 g=0.55

**这已经在 Fix-02a 中完成**。Nice-05 是冗余的。

**状态**：已合并到 Must-Fix-02a，不单独列出。

### §5.6 · Nice-06 · §9.1 汇总表的 "加权贡献" 列处理

**位置**：§9.1 line 6901-6915 · 最后一列 "加权贡献 (v16)"

**背景**：Fix-01 删除了 §9.2 的加权公式 + 88.1% 结论，但 §9.1 汇总表的 "加权贡献" 列仍然暗示可以相加。

**建议方案 A（保守）**：保留 "加权贡献" 列 · 在列头加注 "(作为独立数据，不参与加总)"
**建议方案 B（彻底）**：删除 "加权贡献" 列 + 删除 "合计" 行

**推荐方案 B**（与 Fix-01 的 "彻底方案" 保持一致）

**优先级**：中（如果 Fix-01 采用彻底方案，Nice-06 自动完成）
**预计修订行数**：~15 行 table 调整

### §5.7 · Nice-to-Fix 整体总结

| Nice-# | 主题 | 优先级 | 预计行数 | Plan v19 是否包含 |
|---|---|---|---|---|
| Nice-01 | §4.4 "+" 号历史澄清 | 低 | 3 | 可选 |
| Nice-02 | §1.6 主观估算声明 | 低 | 3 | 可选 |
| Nice-03 | §4.4.1 scope 提醒 | **中** | 3 | **推荐包含** |
| Nice-04 | Karpicke 方法学注脚 | 低 | 5 | 可选 |
| Nice-05 | Dunlosky → Bisra | — | — | 已合并到 Fix-02a |
| Nice-06 | §9.1 加权贡献列处理 | **中** | 15 | **推荐包含**（与 Fix-01 协同）|

**Nice-to-Fix 总预计行数**：~30 行（如果全部采纳）
**推荐采纳范围**：Nice-03 + Nice-06（~18 行）

---

## §6 · Phase 1 骨架 Go/No-Go 最终判定

### §6.1 · 整体结论：🟡 GO with fixes

**判定**：方案 A 可以进入 Phase 1 骨架实施，**但必须先修 3 条 Must-Fix**。

**与 ChatGPT 判定的区别**：
- ChatGPT 也给了 "GO with fixes"，但它的 fixes 包括 5 条 bug
- Plan v18 的 fixes 只包括 **3 条 Must-Fix**（删除 BUG-03 和 BUG-04 的误判）
- 因此 Plan v18 的 scope **比 ChatGPT 更精简**，修订工作量更小

### §6.2 · Phase 1 可以并行开始的部分

以下工作**不依赖** 3 条 Must-Fix，可以立即启动：

1. **Vault 初始化**
   - 创建 `wiki/concepts/`, `exam_boards/`, `edges/` 目录
   - 创建 Dashboard.md 骨架
   - 安装 Obsidian 插件（Dataview, Templater, Callouts）

2. **Skill 接线**
   - `/start_exam_board` skill 骨架
   - `/quiz_from_callout` skill 骨架
   - `/quiz_answer` sub-skill 骨架
   - 不依赖学术论证，依赖 MCP 工具调用

3. **Canvas 后端 MCP 工具调用验证**
   - 14 MCP 工具的 skill 层接线
   - query_mastery / generate_question / score_answer 等

4. **Dashboard.md + Dataview queries**
   - 节点颜色处方性
   - FSRS 到期日排序
   - 进度 callouts

### §6.3 · Phase 1 必须先修完的部分

以下工作**依赖** 3 条 Must-Fix，必须等修完：

1. **§9 守恒度重写**（影响用户信心）
   - 修完 Fix-01 后，用户可以基于 narrative synthesis 做决策
   - 不修的话，PRD 的"方案 A 88.1% 守恒"会误导实施决策

2. **§7.6 后端状态硬化**（影响 Phase 1 scope）
   - 修完 Fix-03 后，Phase 1 的 P0 任务清单才完整
   - 不修的话，Cost Tracker / UserPromptSubmit 会被漏掉

3. **§4.4 学术引用修正**（影响学术可信度）
   - 修完 Fix-02 后，PRD 的学术引用可以经受 peer review
   - 不修的话，如果用户想把 PRD 作为学术依据向他人展示，会被质疑

### §6.4 · Phase 1 最小可验证 spike 清单

**Day 1 必做的 3 个 spike**（来自 Fix-03）：

1. **Spike 1 · canvas_agentic_rag import**
   ```python
   # 验证命令
   cd backend && .venv/bin/python -c "from canvas_agentic_rag.workflows import quiz_generation_workflow; print('OK')"
   ```
   - 预期：输出 "OK"
   - 失败：langgraph 未安装，或 canvas_agentic_rag 子包路径错误

2. **Spike 2 · Graphiti 连通性**
   ```python
   # 验证命令
   cd backend && .venv/bin/python -c "from graphiti_core import Graphiti; g = Graphiti('bolt://localhost:7689'); print('OK')"
   ```
   - 预期：输出 "OK"
   - 失败：Neo4j 未启动，或 graphiti-core 未安装

3. **Spike 3 · 14 MCP 工具可调用**
   ```python
   # 验证命令
   cd backend && .venv/bin/python -c "from app.services.mcp_tools import query_mastery; print('OK')"
   ```
   - 预期：输出 "OK"
   - 失败：MCP 工具路径错误，或依赖链断裂

**如果 Spike 1 失败**：
- Fallback：直接用 MCP 工具调用，不使用 LangGraph workflow
- 影响：`/start_exam_board` 的 workflow 需要手写编排，而不是复用 canvas_agentic_rag

**如果 Spike 2 失败**：
- Fallback：先不实现 search_memories，Phase 1 降级为"无 Graphiti 历史查询"
- 影响：`/start_exam_board` 的个性化出题能力下降

**如果 Spike 3 失败**：
- Blocker：必须先修 MCP 工具的依赖链
- 这是整个 Phase 1 的最低门槛

### §6.5 · Phase 1 时间预估（Plan v18 修订）

**原 PRD 预估**：2-3 周（假设纯接线）

**Plan v18 修订预估**：2-4 周
- Week 1 · Day 1-3：3 个 Spike + P0 新写任务（Cost Tracker + UserPromptSubmit）
- Week 1 · Day 4-7：Vault 初始化 + Skill 接线开始
- Week 2：Skill 接线完成 + Dashboard 实现
- Week 3：端到端测试 + 3 个 Must-Fix 修订（并行）
- Week 4 (optional)：Nice-to-Fix 整理 + 用户 review

**关键假设**：
- 3 个 Spike 在 Day 1-3 完成（或降级到 fallback 路径）
- Must-Fix 可以与实施并行（不 block 骨架搭建）

---

## §7 · 后续决策路径

### §7.1 · 3 种可能走向

#### 走向 A · 立即进入 Plan v19（14-PRD v3 精确修订 · 只修 3 条）

**触发条件**：
- 用户接受 Plan v18 的 triangulated 判定
- 用户同意 BUG-03 和 BUG-04 不是真实 bug
- 用户愿意启动 14-PRD v3 修订

**Plan v19 的 scope**：
- Fix-01 · §9 守恒度重写（narrative synthesis）
- Fix-02a/b/c · 3 条引用修正
- Fix-03 · §7.6 + §10.1 后端状态硬化
- Nice-03 + Nice-06（可选）

**Plan v19 的产物**：
- `14-scheme-a-implementation-prd.md` v3 版本（~7300-7400 行）
- `17-prd-v3-changelog.md`（~200 行 · 变更日志）

**Plan v19 的工作量**：
- ~150-250 行 PRD 修订（3 条 Must-Fix）
- ~18 行 Nice-to-Fix（可选）
- Obsidian 手动 review 确认所有交叉引用一致

**用户的下一步动作**：
```
告诉 Claude Code："进入 Plan v19 · 执行 Fix-01/02/03"
```

#### 走向 B · 保守路径（修完 3 条后重新跑 ChatGPT 验证）

**触发条件**：
- 用户接受 Plan v18 的判定，但想对 Plan v19 的修订做二次验证
- 用户想确保 Plan v19 修完后不引入新 bug

**流程**：
1. 先走走向 A（修完 3 条 Must-Fix）
2. 生成新的 ChatGPT Deep Research prompt（Plan v20 任务）
3. 把 14-PRD v3 + Plan v18 报告 + Plan v19 修订日志一起给 ChatGPT
4. ChatGPT 返回新的 review
5. 如果 ChatGPT 判定 "🟢 GO without fixes"，Phase 1 正式启动
6. 如果 ChatGPT 还有新 bug，进入 Plan v21（再次 triangulated）

**时间成本**：+1-2 天（ChatGPT Deep Research 等待 + 可能的第二轮修订）
**收益**：更高的信心度 + 正式 peer review 的 artifact

**用户的下一步动作**：
```
走向 A 完成后，告诉 Claude Code："生成 Plan v20 ChatGPT 二次验证 prompt"
```

#### 走向 C · 用户自己读 PRD 做最终判断

**触发条件**：
- 用户对 Plan v18 的 triangulated 判定仍有保留
- 用户想自己读 PRD 做最终仲裁
- 用户想确保 Plan v19 的 3 条 Must-Fix 确实是自己想要的

**流程**：
1. 用户在 Obsidian 打开 14-scheme-a-implementation-prd.md
2. 按 Plan v18 的 §1 证据链逐条核实：
   - line 4018, 4089（§4.4 "+" 号）
   - line 768, 4032, 6910（3 处 d 值）
   - line 1502-1525（§2.4 scope 限定）
   - line 6897-6976（§9 88.1% 公式）
3. 用户自己决定：接受 Plan v18 的判定，或发现新的问题
4. 基于用户的仲裁结果，进入 Plan v19（可能与 Plan v18 的建议不同）

**时间成本**：~1-2 小时阅读 + 决策
**收益**：用户完全掌握决策 · 不依赖 Agent / ChatGPT / Plan v18

**用户的下一步动作**：
```
告诉 Claude Code："我要自己读 PRD · 先不动 Plan v19"
然后用户在 Obsidian 做审查 · 完成后再给 Claude Code 指令
```

### §7.2 · Graphiti 归档内容（等用户批准后输出）

**归档将在用户选定走向后触发**。

**预计 Graphiti 记录**（走向 A 选定后）：

```
[DECISION-TECH-FINAL:plan-v18/triangulated-review-outcome]

## 最终决定
ChatGPT 5 Pro Deep Research 的 Top 5 Bug 清单经三方 triangulated 核查后：3 真 · 1 误判 · 1 误判。
接受 3 条 Must-Fix（BUG-01/02/05），拒绝 BUG-03 和 BUG-04 的误判。
Phase 1 骨架 🟡 GO with fixes（只修 3 条，而非 ChatGPT 的 5 条）。

## 依据来源
- Claude Code 侧（Plan v18）：3 个独立 Explore Agent + 亲读 PRD 原文
  - Agent A 学术引用验证：Bisra 2018 g=0.55 独立发现 · Metcalfe 2017 d=2.30 无法追溯
  - Agent B 统计学方法学：88.1% 完全不合法 · 推荐 narrative synthesis
  - Agent C PRD Bug 清单：2 正确 + 3 误判（暴露 Agent 驱动审查盲点）
  - 亲读 PRD：§9 line 6924-6930 + line 4018/4089 + line 1502-1525 + line 768/4032/6910
- ChatGPT Deep Research 侧：
  - 学术核实可信度 中等（6.5/10）· 遗漏 Bisra 2018
  - 方法学可信度 高（8/10）· 但 55-75% 替代区间自相矛盾
  - Bug 清单：BUG-01/02/05 真实 · BUG-03/04 误判

## 实施注意事项
- Fix-01：删除 88.1% + 改为 narrative synthesis（Cochrane 标准）
- Fix-02a：Dunlosky → Bisra 2018 g=0.55
- Fix-02b：Metcalfe 2017 d=2.30 → Cepeda 2008 d=0.4-0.7
- Fix-02c：Cassady d=-1.20 → r ≈ -0.20 到 -0.40 (原文报告)
- Fix-03：§7.6 + §10.1 后端状态硬化
- BUG-03 + BUG-04 不做修订（Agent C/ChatGPT 误判）

## 后续步骤
- 走向 A：进入 Plan v19 · 14-PRD v3 精确修订
- 走向 B：修完后跑 ChatGPT 二次验证
- 走向 C：用户自己读 PRD 仲裁
```

**注**：此归档**只在用户明确确认走向后**触发。Plan v18 本身**不调用** add_memory（Plan v18 是决策文档，不是决策 finalize）。

### §7.3 · Plan v18 的产出物清单

| 产出 | 状态 | 位置 |
|---|---|---|
| 16-triangulated-review-report.md | ✅ 本文件 | CS 61B/ 目录 |
| 14-scheme-a-implementation-prd.md | 保持不动 | 7290 行 · 不修 |
| 15-adversarial-review-prompt.md | 保持不动 | 1345 行 · Plan v17 产物 |
| Plan v18 (`melodic-jingling-mochi.md`) | ✅ 当前活跃 | .claude/plans/ |
| Graphiti 归档 | ⏸ 等待用户批准走向 | `canvas-dev` group |
| Plan v19 | ⏸ 尚未启动 | 待用户决定走向后创建 |

---

## §8 · 批注区 + 文档元信息

### §8.1 · 用户批注区

（此区域留空，供用户在 Obsidian 中添加批注）

> **批注 #1**: _待填_

> **批注 #2**: _待填_

> **批注 #3**: _待填_

### §8.2 · 文档元信息

- **文档名**：16-triangulated-review-report.md
- **Plan**：Plan v18（`/Users/Heishing/.claude/plans/melodic-jingling-mochi.md`）
- **创建日期**：2026-04-09
- **创建时点**：ChatGPT 5 Pro Deep Research 返回后立即
- **基础资料**：
  - Plan v17 产物 · 15-adversarial-review-prompt.md (1345 行)
  - 14-scheme-a-implementation-prd.md v2 (7290 行)
  - ChatGPT Deep Research 返回 · Top 5 Bug 清单
  - 3 个独立 Explore Agent 的核查报告
  - 亲读 PRD 原文的 4 个决定性证据
- **方法论**：三方 triangulated 审查（ChatGPT + Agent A/B/C + 亲读 PRD）
- **作者视角**：Claude Code（以 "meta-reviewer" 角度审查 ChatGPT 的 review）
- **不代表**：14-PRD 本身的审查（那是 Plan v17 + ChatGPT 的事）
- **代表**：对 ChatGPT review 的 review

### §8.3 · 相关文档交叉索引

```
14-scheme-a-implementation-prd.md (v2, 7290 行)
  └─ 被 Plan v17 审查 → 15-adversarial-review-prompt.md (1345 行)
       └─ 被 ChatGPT 5 Pro 审查 → Top 5 Bug 清单
            └─ 被 Plan v18 triangulated 审查 → 16-triangulated-review-report.md (本文档)
                 └─ 等待用户决策 → Plan v19（待定）
                      └─ 可能走向 A/B/C → 14-PRD v3 (待定) / ChatGPT 二次验证 / 用户自读
```

### §8.4 · 版本历史

| 版本 | 日期 | 变更 | 作者 |
|---|---|---|---|
| v1.0 | 2026-04-09 | 初次创建 · Plan v18 执行 | Claude Code |

### §8.5 · Plan v18 的 5 个关键发现（摘要）

1. **ChatGPT 的 Top 5 Bug 清单不是 100% 可信** —— 3 真 · 2 误判
2. **Agent C 有系统性盲点** —— 5 条判定中 3 条错误（BUG-01/02/03）
3. **Bisra 2018 g=0.55 是独立发现** —— 可作为 Dunlosky 2013 的可靠替代
4. **§2.4 保证 2 的 scope 限定被双重误读** —— ChatGPT 和 Agent C 都错
5. **ChatGPT 自相矛盾提出 55-75% 替代区间** —— Agent B 正确否决 · 应完全删除百分比

### §8.6 · Plan v18 方法论的可复用价值

**何时该使用 triangulated review**：
- 当外部 AI (如 ChatGPT) 返回复杂的判定时
- 当判定会驱动 scope 大的修订时（如 Plan v19 可能修 ~250 行 PRD）
- 当单一 Agent 的判定可能有系统性盲点时

**何时不需要 triangulated review**：
- 简单的 bug 修复（1-2 文件）
- 没有外部 AI 参与的内部判定
- 判定与 scope 不成比例时（杀鸡用牛刀）

**Plan v18 验证的核心教训**：
- AI review 可能有幻觉或引用错误
- Agent 之间可能共享同样的误读（BUG-03 案例）
- **亲自读原文是最后一环仲裁** —— 不可替代

---

**[报告结束]**

> 本文档是 Plan v18 的决策产物。Plan v18 **不修改 14-PRD**。Plan v19 才是真正的修订执行。用户在决定走向 A/B/C 前，可以在 §8.1 批注区添加自己的判断。


