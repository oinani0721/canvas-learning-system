# 检验白板出题设计 — ChatGPT Deep Research 简报

> 目的：把"**熟练度如何驱动出题、才能最大化掌握**"这个设计交给 ChatGPT deep research，要一个**学习科学支撑的、可落地的出题设计规范**。
> 本简报自包含：读完可直接研究，无需额外材料。给 ChatGPT 的 prompt 在文末。

---

## 一、研究目标（一句话）

设计一套"**节点熟练度 → 出题策略**"的映射，让检验白板对用户的考察**真正有效**（最大化长期掌握与迁移），并有学习科学证据支撑。**不是重写，是把学习科学灌进现有出题逻辑、补齐缺口。**

---

## 二、背景（自包含）

- **检验白板** = Karpicke & Blunt (2011) 检索练习（Retrieval Practice, **d=1.50**）的落地：**信息全隐形**的独立白板，用户看不到原文、主动回忆作答。它是"原白板（信息可见·剖析）"的对称极。
- **架构（Mode D）**：用户在 Obsidian，出题/评分由 **Claude Code（订阅）** 经 Skill 完成；后端提供纯数据（掌握度/批注/错误）。
- **用户核心诉求（原话）**："我的节点熟练度，决定了你怎么出题考察我，从而确保我真的掌握了相关的知识……我要一个真正有效的考察，通过检验白板的考题，最大限度让我掌握相关内容。"
- **数据已就绪**：用户批注(`tips[]`)、派生原因(`relationships[]`)、错误史、掌握度(BKT `p_mastery` + FSRS 稳定性/可提取性 + 5 信号融合 `mastery_level` + `calibration_bias`)。

---

## 三、现有出题设计（5 层 ACP Prompt）

后端已有一套 5 层 prompt（`backend/app/prompts/exam/layer*.md`）：
- **Layer 1 角色**：经验丰富的学习考官，基于学生数据精准出题、一次一题、不暗示答案、难度匹配掌握度。
- **Layer 2 模式**：point_to_point（单点深挖，Bloom Remember/Understand）/ comprehensive（跨概念综合，Apply/Analyze/Evaluate）/ mixed（先点对点找弱点再综合）。
- **Layer 3 学生数据（ACP）**：节点内容 + 掌握度(p_mastery/retrievability/effective_proficiency/label) + 学生批注 + 错误史(4类) + 概念关系理由 + 对话摘要。
- **Layer 4 规则 + 错误补救**：难度适配 + 4 类错误→差异化补救策略：
  - 破题错误 → 同结构不同包装的变式题
  - 推理谬误 → 给错误推理让学生找错 / 反例题
  - 知识点缺失 → 回退定义级基础题
  - 似懂非懂 → 辨析题 / 反例题 / 迁移题
- **Layer 5 评分预设**：4 维 4 分制（概念准确/推理质量/知识覆盖/知识整合），出开放题、有区分度。
- **信息隔离**：5 层数据流，后端读批注/错误组进 prompt 但不返回给 skill/用户；题目不暴露答案（"你之前说过 X，但其实应该 Y"式引用，非通用题库）。

---

## 四、现有的"熟练度→出题"映射（现状 + 缺口）

**现状**（`question_generator.py:516-523, 663-672`）——只有粗糙 4 档：
```
effective_proficiency < 0.3 → "easy"（定义/识别题）
0.3–0.5 → "medium-easy"（解释题）
0.5–0.7 → "medium-hard"（应用/辨析题）
≥ 0.7 → "hard"（应用/迁移题）
```

**三个关键缺口（要 ChatGPT 研究补齐）**：
1. **Bloom 层级是隐式的**：出题侧本应"用 Bloom 控制难度层级（Remember→Create）"，但代码里 Bloom 层级由 LLM 自主返回、**没有按掌握度显式约束**——可能出的题和掌握度不匹配。
2. **无"期望难度 / 最近发展区"**：Bjork 的 desirable difficulty + Vygotsky ZPD 说"题目略高于当前水平最有效"，现有硬编码区间**没有这个自适应**。
3. **校准偏差(`calibration_bias`)算了却没用于出题**：用户"过度自信（以为会了其实不会）"时应出难题验证、"不自信"时应出简题建信心——这个信号闲置。
（另：无 IRT 难度匹配，只有硬区间。）

---

## 五、学习科学底座（PRD 已锚定 + 2024-2025 论文，带来源）

| 设计要素 | 依据 | 效应量 | 来源 |
|---|---|---|---|
| 检索练习（生成式答题 > 再认） | Karpicke & Blunt 2011 | **d=1.50** | Science 331:772 |
| 生成效应（自己生成 > 阅读） | Slamecka & Graf 1978 | d≈0.65 | JEP:HLM 4(6) |
| 自我解释（用自己的话） | Chi 1994 / Bisra 2018 meta | d≈1.09 / g=0.55 | Cognitive Science 18(3) |
| 期望难度（略难最有效） | Bjork 1994/2011 | — | [Bjork Lab PDF](https://bjorklab.psych.ucla.edu/wp-content/uploads/sites/13/2016/04/EBjork_RBjork_2011.pdf) |
| 最近发展区 ZPD | Vygotsky 1978 | — | — |
| Bloom 层级↔难度 | Anderson & Krathwohl 2001 | 相关 V=0.51 | [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC9673841/) |
| SOLO 评分深度 | Biggs & Collis 1982 | d≈0.70 | — |
| 精细化提问（Why/How） | Chi 1994 / Elaborative Interrogation | 记忆×2 | [LINCS](https://lincs.ed.gov/sites/default/files/12_TEAL_Deeper_Learning_Qs_complete_5_1_0.pdf) |
| 间隔效应 | Cepeda 2006 meta(317 实验) | d≈0.55 | Psych Bulletin 132(3) |
| 反馈时机（延迟>立即纠错） | Smith & Kimball 2010 | — | [PDF](https://www.ou.edu/memorylab/pdfs/SmithKimball_2010_LearningFromFeedback_ms.pdf) |
| 从错误中学习（错误当锚点，延迟复习） | Metcalfe 2017 | — | Annual Review Psych 68 |
| IRT 自适应难度匹配（难度≈能力时信息最大） | CAT/IRT | — | [Cogn-IQ](https://www.cogn-iq.org/learn/theory/adaptive-testing/) |
| LLM 生成检索练习题实证 | 2025 | — | [arXiv 2507.05629](https://arxiv.org/pdf/2507.05629) |

**关键社区共识（2024-2025）**："最大化掌握"是多因素合成：生成式题型 + 难度匹配（challenge-skill 平衡）+ Why/How 深层提问 + Bloom 层级递进 + 间隔化 + 延迟反馈 + 个人化检索线索（用学生自己的错误/解释，但要间隔 3-7 天后用）。

---

## 六、给 ChatGPT 的具体研究问题

1. **熟练度 → Bloom 层级的映射该怎么设计**？给一个有证据支撑的映射表（effective_proficiency 或 5 信号 → Bloom 1-6 / 题型），比现有 4 档更精细、更有效。
2. **"期望难度 / ZPD" 怎么落地**？题目该比当前水平高多少（+0.1?+1 个 Bloom 层级?）最优？有没有量化建议（如答对率目标区间）？
3. **校准偏差怎么用于出题**？过度自信 vs 不自信，出题策略各该怎么调？
4. **个人化检索线索（用学生自己的批注/错误出题）怎么设计最有效**？什么时候用（间隔）、怎么引用（"你之前说 X"）、会不会有反效果？
5. **Why/How 深层提问 vs 定义题**，在不同掌握度下怎么配比？
6. **间隔 + 反馈时机**：检验白板的复习节拍（FSRS next_review）和"延迟反馈"怎么和出题配合？
7. **可落地的出题 prompt 规范**：把上述结论整合成一份"给 Claude Code 出题用的指令 + 熟练度→出题决策规则表"，能直接写进 Skill/prompt。

---

## 七、期望产出

一份**研究支撑 + 可落地**的出题设计规范：
- 熟练度 → (Bloom 层级 + 题型 + 难度) 的决策表（带证据）
- 期望难度/ZPD 的量化规则
- 校准偏差、个人化线索、间隔反馈的使用规则
- 一段可直接用的"检验白板出题 system prompt"草案
- 明确哪些是强证据、哪些是待验证的设计假设
