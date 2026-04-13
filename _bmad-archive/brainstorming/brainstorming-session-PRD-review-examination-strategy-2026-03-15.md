# PRD Review New Tab — 检验白板考察策略深度调研

> **Session**: PRD-Review-执行 (New Tab)
> **日期**: 2026-03-15
> **来源**: 用户提问 → 3 轮并行 Agent 调研 → 用户确认
> **状态**: 4 项修正全部用户确认，待主 Tab 更新 PRD
> **Pencil 产出**: `UI 相关设计样式.pen` → frame `DO8ew`（检验白板修正工作流 6 屏）

---

## 起因

用户在审阅 PRD 时对 Edge 对话的"三重策略"提出质疑：

> "你这里的策略 3 主动回忆是什么意思？...这更像是检验白板的考察流程"

随后深入讨论了检验白板的考察模式设计，提出了原白板内容类型与考察模式映射的设计洞察。

---

## 修正 1：Edge 对话 — 三重策略 → 双重策略

### 问题

PRD 第 130、382、647 行声称 Edge 对话"同时激活精细化追问、自我解释和主动回忆三种学习策略"。

### 调研方法

3 路并行 Agent 调研：
1. **Brainstorming 原始记录搜索** — 还原 Edge 对话最初设计意图
2. **社区/论文调研** — Elaborative Interrogation vs Active Recall 学术边界
3. **Graphiti 历史搜索** — 跨 session 决策追溯

### 调研结论

三种策略操作在**不同认知阶段**，不能在同一交互中同时触发：

| 策略 | 认知阶段 | 信息是否可见 | Dunlosky 2013 评级 |
|------|---------|-----------|-------------------|
| 精细化追问（Elaborative Interrogation） | 编码阶段 | ✅ 可见 | 中等 |
| 自我解释（Self-Explanation） | 编码阶段 | ✅ 可见 | 中等 |
| 主动回忆（Active Recall / Retrieval Practice） | 检索阶段 | ❌ 不可见 | **高** |

**核心矛盾**：Edge 对话发生时两个概念节点在白板上可见。要求"不看笔记凭记忆回答"与场景逻辑冲突。

**学术证据**：
- Karpicke & Blunt 2011（*Science*）：概念图连线本质是 Elaborative Encoding，不是 Retrieval Practice
- Endres et al. 2017（*Learning and Instruction*）：EI+SE 先编码，RP 后检索，**顺序配合**效果最优
- Dunlosky et al. 2013（*Psychological Science in the Public Interest*）：三种策略的效用评级

**Brainstorming 原始记录佐证**（Session D, 2026-03-11）：
- Edge 对话原始设计核心是"**探索 + 理解 + 连接**"
- Active Recall 是后期补偿性加入，归属位置错误
- 原始评估："主动回忆+间隔重复 ⚠️ 最弱 — 设计偏 elaborative encoding"

### 修正方案

- **Edge 对话** → 双重策略（EI + SE）：帮用户在连线时想清楚"为什么连在一起"
- **检验白板** → Active Recall：信息不可见，从记忆中提取
- 两个工作流形成**先编码后检索**的最优学习路径（Endres 2017）

### PRD 影响位置

- 第 130 行：工作流 1 中"三重学习策略对话" → "双重学习策略对话"
- 第 382 行：创新聚焦表 Edge 对话描述
- 第 647 行：FR-EDGE-04 "同时激活...三种学习策略" → 两种

---

## 修正 2：检验白板 — 两种可选考察模式

### 问题

PRD 将检验白板描述为单一考察流程，未区分考察模式。

### 调研结论

| 模式 | 学术名称 | 考什么 | 成熟度 |
|------|---------|-------|-------|
| 点对点突破 | Discrete-point Assessment | 逐个概念考察 | ✅ Oller 1979, Bloom Remember/Understand |
| 综合题 | Integrative Assessment | 多概念关系、应用迁移 | ✅ Bloom Analyze/Evaluate, SOLO Relational |

两者配合形成递归：综合题考关系 → 发现薄弱 → 拆开用点对点追问具体哪个点不会。学术上叫 **Adaptive Formative Assessment**，有成熟 CAT（计算机自适应测试）理论支撑。

### 修正方案

检验白板生成时增加模式选择：
- 📝 **点对点突破** — "逐个考我知识点/易错点，查漏补缺"
- 🧩 **综合题考察** — "出一道类似新题，看我能不能举一反三"
- 🔀 **混合模式** — "先点对点找弱点，再出综合题验证"

### PRD 影响位置

- 能力域 4（FR-EXAM 系列）新增 FR-EXAM-09/10

---

## 修正 3：考察模式与原白板内容类型映射

### 问题

PRD 未区分原白板的内容类型，也未将内容类型与考察模式关联。

### 用户洞察

> "如果原白板是知识点的剖析，那么我会选择点对点突破；如果是题目的剖析，那么我可能会选择综合性题目，看我能不能举一反三。"

### 调研结论 — Constructive Alignment（Biggs 1996）

**建构性对齐**是高等教育领域最核心的设计原则：怎么学就应该怎么考。

| 原白板内容 | 知识类型 | Bloom 层级 | 推荐考察模式 | 学术依据 |
|---------|---------|-----------|-----------|---------|
| 知识点剖析 | 概念性知识 | Remember / Understand | 点对点突破 | Novak & Gowin 1984; Ruiz-Primo & Shavelson 1996 |
| 题目解题剖析 | 程序性知识 | Apply / Analyze | 综合题/举一反三 | Gick & Holyoak 1983; Sweller 1988; Renkl & Atkinson 2003 |

**举一反三的学术验证**（Schema Induction, Gick & Holyoak 1983）：
- 学了 1 个解题过程 → 30% 能解出类似新题
- 学了 2 个并对比总结 → 52% 能解出
- 关键：能否举一反三取决于是否抽象出了解题过程的核心模式

**项目内搜索**：PRD 和所有 brainstorming 中完全没有区分原白板内容类型。这是全新设计维度。

### 修正方案

- 系统可基于 Edge 标签语义自动推荐模式（概念关系 → 点对点；过程关系 → 综合题）
- 用户也可手动选择

### PRD 影响位置

- 产品范围、能力域 4、工作流 2 描述

---

## 修正 4：点对点突破 — 两种子策略

### 问题

点对点突破被视为单一模式，但针对不同白板类型，考察方向应不同。

### 用户洞察

> "知识大多是不懂不理解，似懂非懂；题目则是易错点，破题出问题，思维出问题，出现了混淆性思维。"

### 设计方案

| 原白板类型 | 学生的问题特征 | AI 考察方向 | 对应弱点类型 |
|---------|------------|-----------|-----------|
| **知识点** | 不懂、不理解、似懂非懂 | 定义 + 解释 + 辨析 | 概念误解、理解深度不足 |
| **题目** | 易错点、破题思路错、混淆性思维 | 易错点意识 + 破题方法 + 混淆排除 | 推理错误、前置知识缺口 |

AI 出题 prompt 策略根据白板类型定制：
- 知识点白板："什么是 X？请用自己的话解释"（考理解度）
- 题目白板："这道题第一步你会怎么入手？为什么不是用 Y 方法？"（考易错点 + 思维正确性）

### PRD 影响位置

- 能力域 4 + 算法架构（出题策略适配器）

---

## 前端设计产出

已在 `UI 相关设计样式.pen` 中创建检验白板修正工作流 6 屏设计（frame ID: `DO8ew`）：

| 步骤 | Frame ID | 内容 | 颜色标识 |
|------|---------|------|---------|
| ① 选择白板 | `Ai7TG` | Dashboard 选择原白板，点击"生成检验白板" | 🟣 紫 |
| ② AI 分析薄弱点 | `BX2RT` | 空白白板 + AI 列出 FSRS+BKT 排序的薄弱点 | 🟣 紫 |
| ③ 点对点突破 | `A5QVT` | 聚焦单概念，"信息已隐藏，凭记忆回答"，标签"点对点" | 🔴 红 |
| ④ 评分+精通度 | `uOH9a` | 75/100 评分 + 精通度 0.35→0.55 + 三维度评分条 | 🟢 绿 |
| ⑤ 综合题考察 | `IFPGX` | 两节点+Edge，引用 Edge 理由出关系题，标签"综合题" | 🟡 橙 |
| ⑥ 递归深入 | `ws2ry` | 新盲区生成虚线节点 + "回写原白板"标签 | 🟣 紫 |

---

## 完整工作流（修正后）

```
原白板学习（Edge 对话 = 双重策略 EI+SE）
  │ 积累 Edge 理由、Tips、对话错误
  │
  ▼
生成检验白板（选择考察模式）
  │
  ├─ 知识点白板 → 推荐"点对点突破"
  │    └─ AI 侧重：定义+解释+辨析（考理解度）
  │
  ├─ 题目白板 → 推荐"综合题"
  │    └─ AI 出类似新题（考举一反三）
  │
  └─ 混合模式 → 先点对点找弱点，再综合题验证
       │
       ▼
  Active Recall 考察（信息不可见）
       │
       ├─ 评分 + 精通度更新
       │
       ├─ 发现新盲区 → 生成新节点
       │    └─ 回写原白板 → 递归考察
       │
       └─ 闭环：新数据反哺下次考察精准度
```

---

## 学术引用汇总

| 论文 | 年份 | 期刊 | 支撑内容 |
|------|------|------|---------|
| Dunlosky et al. | 2013 | *Psych Science in the Public Interest* | EI/SE/RP 三策略评级 |
| Karpicke & Blunt | 2011 | *Science* | 概念图 = Elaborative Encoding ≠ Retrieval Practice |
| Endres et al. | 2017 | *Learning and Instruction* | 先编码后检索顺序配合效果最优 |
| Biggs | 1996 | *Higher Education* | Constructive Alignment 建构性对齐 |
| Anderson & Krathwohl | 2001 | (专著) | Revised Bloom's Taxonomy 二维矩阵 |
| Gick & Holyoak | 1983 | *Cognitive Psychology* | Schema Induction 举一反三 |
| Sweller | 1988 | *Cognitive Science* | Cognitive Load Theory 认知负荷 |
| Renkl & Atkinson | 2003 | *J Experimental Education* | Faded Worked Examples 渐退示例 |
| Novak & Gowin | 1984 | (专著) | 概念图评分方法 |
| Ruiz-Primo & Shavelson | 1996 | *J Research in Science Teaching* | 概念图评估框架 |
| Black & Wiliam | 1998 | *Assessment in Education* | 形成性评估 Assessment FOR/AS Learning |
| Chi, Feltovich & Glaser | 1981 | *Cognitive Science* | 专家-新手问题分类差异 |

---

## 后续行动

1. **主 Tab** 根据以上 4 项修正更新 PRD 文档
2. 记录 `[Decision-Review]` — 4 项修正需独立 session 验证
3. 继续主 Tab 的 BMAD validate-prd 工作流下一步（Format Detection）
