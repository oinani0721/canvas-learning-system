---
stepsCompleted: ['prd-gap-discovery', 'community-research-8-products', 'academic-research-OLM-papers', 'adversarial-code-review', 'design-recommendation']
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/brainstorming/brainstorming-session-2026-03-11-001.md
  - docs/community-product-research.md
session_topic: 'PRD Review — 节点学习痕迹前端展示（错误/Tips/关键问答）'
session_goals: '发现PRD缺口→调研竞品+论文→代码审查→推荐设计方案'
selected_approach: 'adversarial-deep-explore'
techniques_used: ['竞品调研(8款产品)', '学术论文搜索(OLM/Bull&Kay/元认知/错误心理学)', '对抗性代码审查(5维度)', 'Graphiti跨session知识共享']
review_status: 'completed'
review_date: '2026-03-15'
review_agents: 3
review_papers: '15+'
review_products: 8
verdict: 'PRD GAP CONFIRMED — 建议新增 FR'
---

# PRD Review — 节点学习痕迹前端展示调研报告

**Session：** PRD-Review New Tab（深潜讨论）
**日期：** 2026-03-15
**调研规模：** 3 个独立 Agent、15+ 篇论文、8 款商业产品、5 维度代码审查
**主 Tab 关联：** PRD Review 工作流 Step 1 完成，本报告供主 Tab 继续验证时引用

---

## 一、问题发现

### 1.1 发现经过

用户查看 PRD 中 Hot-Warm-Cold 对话归档数据流图时提出问题：

> "后续如果我查看相应白板，我点击相关的节点，前端里是否可以查看永久保存的错误/Tips/关键问答？"

### 1.2 PRD 缺口确认

PRD 当前只定义了这些数据的**被动用途**（AI 自动利用），未定义**主动浏览 UI**：

| 用户想做的 | PRD 当前状态 | 相关 FR |
|---------|------------|---------|
| 点击节点 → 看到"我标过哪些 Tips" | ❌ 没有对应 FR | — |
| 点击节点 → 看到"我犯过哪些错" | ❌ 没有对应 FR | — |
| 点击节点 → 看到"关键问答历史" | ❌ 没有对应 FR | — |
| AI 对话时自动利用这些数据 | ✅ 已定义 | FR-CONV-03 |
| 检验白板利用历史错误出题 | ✅ 已定义 | FR-EXAM-03 |

### 1.3 Graphiti 已知相关事实

- `"PRD boundary excludes Graphiti personal memory (Tips/Edge/Errors)"` — PRD 明确排除了 Graphiti 个人记忆
- `"OLM Layer2 的展示设计存在根本性问题"` — 已知 OLM 展示问题
- `"Graphiti弱点存储Schema未定义"` — schema 尚未设计

---

## 二、竞品调研（8 款产品）

### 2.1 核心发现：几乎没有产品直接向学生展示"错误列表"

| 产品 | 展示具体错误内容？ | 实际展示什么 |
|------|:---:|---|
| **Anki** | ❌ | Per-card 复习历史表格（日期/评级/间隔），不记录错误内容本身 |
| **Duolingo** | ❌ **反而移除了** | 曾有 Words 强弱表，后来删了。趋势是减少暴露给用户的详细数据 |
| **RemNote** | ❌ | Per-card Mastery level + Practice History（答对/错时间序列） |
| **Khan Academy** | **教师端 ✅** 学生端 ❌ | 学生只看 Mastery levels，教师能看每题的具体回答（Responses Report） |
| **Math Academy** | ❌ | Knowledge Graph 进度 + XP，不展示错误历史 |
| **Knewton Alta** | ❌ | 答错时即时反馈+补救路径，但不保存"错误清单"给用户翻阅 |
| **Area9 Lyceum** | ❌ 但有元认知校准 | 四象限展示"你以为会但其实不会"（unconscious incompetence），最接近本需求 |
| **Quizlet** | ❌ | 三分类（没学/还在学/掌握了） |

### 2.2 关键模式总结

1. **无一产品向学生展示"你犯过的具体错误列表"**
2. Khan Academy 只在教师端展示具体回答（Responses Report），学生端只看 Mastery Level
3. Duolingo 的 Words Tab 移除案例说明：**即使是聚合数据（强弱程度），平台也可能决定不展示**
4. Area9 Lyceum 的四象限模型（unconscious incompetence）是最接近"展示错误"的设计，但仍是聚合可视化而非原始错误列表

### 2.3 来源

- [Anki Manual - Statistics](https://docs.ankiweb.net/stats.html)
- [Duolingo Blog - How We Learn](https://blog.duolingo.com/how-we-learn-how-you-learn/)
- [RemNote - Flashcard Statistics](https://help.remnote.com/en/articles/7970392-flashcard-statistics)
- [Khan Academy - Responses Reports](https://support.khanacademy.org/hc/en-us/articles/115000780012)
- [Math Academy - How It Works](https://www.mathacademy.com/how-it-works)
- [Knewton Alta Features](https://www.wiley.com/en-us/education/alta/features)
- [Area9 Lyceum - Four Dimensions](https://area9lyceum.com/adaptive-learning/multidimensional-learning/)
- [Quizlet - Using Progress](https://help.quizlet.com/hc/en-us/articles/360048803491)

---

## 三、学术论文调研（15+ 篇）

### 3.1 OLM 研究（Bull & Kay SMILI 框架）

- OLM 展示学习者模型的方式从简单（skill meters）到复杂（3D 网络、贝叶斯网络）
- **SMILI 框架**定义四个层次：Inspectable → Negotiable → Editable → Persuasive/Adaptive
- OLM **推荐展示 misconceptions**，但以**聚合可视化**形式（skill meters、concept maps、颜色编码），而非原始错误列表
- 研究证实 OLM 支持 metacognition（自我监控、反思、规划）和 self-regulated learning
- **来源**：Bull & Kay - SMILI Framework (Springer 2015), OLM for Self-Regulated Learning (ScienceDirect 2020)

### 3.2 展示错误的心理学效应 — 利弊并存

**正面效果：**
- **Hypercorrection Effect**（Metcalfe & Butterfield）：高置信度错误被纠正的概率 70-90%，"以为对但其实错"产生的惊讶感触发更深层认知加工
- Erroneous examples（展示错误示例让学生找错）可以增强学习

**负面效果 / 重要警告：**
- **2025 论文 "Students Ignore Their Mistakes"**：低成绩学生（最需要错误反馈的人）反而最不会主动查看详细错误反馈，也最不觉得错误反馈有用
- 当学生对犯错感到压力/焦虑时，展示错误反而导致更少的适应性行为、更低的坚持性
- 简单展示正确答案可能不够：75% 通过课程的学生在后测中仍犯与前测相同的 misconception 错误

**来源**：
- [Students Ignore Their Mistakes (ScienceDirect 2025)](https://www.sciencedirect.com/science/article/pii/S0361476X25000608)
- [Hypercorrection Effect Guide](https://www.structural-learning.com/post/hypercorrection-effect-teachers-guide)
- [Learning from Errors (PMC 2025)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11803059/)

### 3.3 Learning Analytics Dashboard 研究

- Misconception 跟踪和具体错误分析**主要出现在教师端仪表盘**
- 学生端仪表盘主要展示：学习活动量、进度、mastery level
- 研究警告：仪表盘可能导致**认知过载**，特别是对数据可视化素养有限的用户
- **来源**：Sahin & Ifenthaler (2021) Visualizations and Dashboards for Learning Analytics

### 3.4 综合学术结论

学术证据**支持展示学习痕迹**，但有**五个严格设计条件**：

| # | 设计条件 | 来源 |
|---|---------|------|
| 1 | **正面框架** — "需要加强的方向"而非"你的错误记录" | OLM 研究 + 错误心理学 |
| 2 | **双重解释** — 为什么错 + 正确是什么 | Hypercorrection Effect |
| 3 | **进步叙事** — 展示从错误到掌握的进步轨迹 | Learning Analytics Dashboard |
| 4 | **元认知提示** — "你当时以为会但其实不会" | Area9 + Dunning-Kruger |
| 5 | **视觉区分** — 区分"误解"和"还没学到" | OLM SMILI 框架 |

### 3.5 推荐三层渐进展示架构

| 层级 | 展示内容 | 可见性 | 对应 |
|------|---------|--------|------|
| **L1** | 聚合精通度（温度计/进度条） | 始终可见 | PRD 现有 FR-MAST-03 |
| **L2** | Tips 列表 + "需要加强"方向（聚合的误解模式） | 按需展开 | **新增 FR** |
| **L3** | 具体对话片段 + 关键问答精选（按主题聚类） | 深度钻取 | **新增 FR** |

---

## 四、对抗性代码审查（5 维度）

> 由独立 Agent 执行，审查现有代码中与学习痕迹展示相关的基础设施。

### 4.1 审查结果总览

| 组件 | 质量评级 | 关键发现 |
|------|---------|---------|
| **实体类型定义** | ✅ 可复用 | `memory_format.py` 有 9 种类型（Misconception/ProblemTrap/LogicalFallacy/GuidedThinking 等），**但缺 Tips 和 KeyQA 类型** |
| **写入管道** | ⚠️ 需修复 | `GraphitiBridgeService.bridge_to_claude_format()` 真实实现，但 node_id 格式不一致：bridge 写 `canvas-{id}`，react_agent 写 `agent-{timestamp}`。且仅 score<80 时写入，正面学习时刻不记录 |
| **对话提取归档（Hot-Warm-Cold）** | ❌ 完全不存在 | 零实现。PRD 数据流图中画的管道还没有任何代码。无自动提取错误/Tips/关键问答的系统 |
| **按节点查询 API** | ❌ 不存在 | 无法"给我这个节点的所有学习痕迹"。`search_claude_records()` 可用但未暴露为 API 端点 |
| **前端展示组件** | ❌ 不存在 | Demo 和插件中均无展示学习痕迹的 UI 组件 |

### 4.2 可复用资产

1. **`memory_format.py`** — 9 种实体类型定义 + 模板（添加 Tips/KeyQA 类型即可扩展）
2. **`GraphitiBridgeService.bridge_to_claude_format()`** — 真实写入管道（需统一 node_id 格式）
3. **`search_claude_records()`** — 文本搜索 EntityNode，可做（需暴露为 API + 加 node_id 过滤）
4. **`react_agent.record_learning_memory()` 工具** — LLM 主动记录学习事件（已连通）
5. **现有 `/episodes` + `/concepts/{id}/history` API** — 评分历史（可补充 L1 精通度数据）

### 4.3 需要新建的

1. **对话提取管道** — Hot→Warm 归档时自动提取错误/Tips/关键问答（PRD 中画了但代码不存在）
2. **Tips/KeyQA 实体类型** — 在 `memory_format.py` 中增加
3. **按 node_id 查询 API** — `GET /api/v1/nodes/{node_id}/learning-traces`
4. **node_id 格式统一** — 所有写入路径用统一的 `canvas-{nodeId}` 格式
5. **前端 "学习档案" tab 组件** — 三层渐进展示

### 4.4 代码审查来源文件

- `backend/app/services/graphiti_bridge_service.py` — 写入+搜索
- `backend/app/core/memory_format.py` — 实体类型定义
- `backend/app/services/memory_service.py` — 学习事件记录
- `backend/app/agents/react_agent.py` — Agent 工具中的 record_learning_memory
- `backend/app/api/agents.py` — API 端点

---

## 五、推荐设计方案

### 5.1 交互模式：节点侧边栏 "学习档案" Tab

```
用户点击知识节点 → 打开右侧面板 → 多 Tab 布局：
  [对话] [学习档案] [复习]

"学习档案" Tab 内容：

  ┌─ L1 掌握度指示器 ────────────────────────┐
  │  ████████░░░░  65%  "进步中"              │
  │  （基于 BKT+FSRS 聚合）                    │
  └──────────────────────────────────────────┘

  ┌─ L2 你标注的 Tips ───────────────────────┐
  │  📌 "consistent 是更强的条件"              │
  │  📌 "A* 最优性取决于 h(n) admissibility"   │
  │  📌 [点击展开查看对话上下文]                │
  └──────────────────────────────────────────┘

  ┌─ L2 需要加强的方向 ──────────────────────┐
  │  ⚡ "admissibility vs consistency 区分"    │
  │  ⚡ "启发函数边界情况"                     │
  │  （聚合的误解模式，非原始错误列表）          │
  └──────────────────────────────────────────┘

  ┌─ L3 关键问答精选（折叠，按需展开）──────────┐
  │  ▶ 主题：admissibility 条件              │
  │    Q: "什么是 admissibility？"            │
  │    A: "h(n) <= h*(n)，即..."              │
  │  ▶ 主题：A* vs Dijkstra                  │
  └──────────────────────────────────────────┘
```

### 5.2 设计原则（来自研究证据）

| 原则 | 来源 | 实现方式 |
|------|------|---------|
| 聚合优先，详情按需 | OLM/Bull & Kay; 竞品共识 | Mastery meter + 可展开详情 |
| 支持性语调 | "Students Ignore Mistakes" 论文 | "需要加强的方向"而非"你的错误记录" |
| 可操作 | Learning Analytics Dashboard 研究 | 每个洞见附带"去复习"按钮 |
| 避免认知过载 | Dashboard 认知过载警告 | 默认折叠详情，分 Tab 展示 |
| 不暴露原始数据 | Duolingo 移除 Words Tab 的趋势 | 用自然语言描述代替数字/图表 |

### 5.3 不推荐的模式

- ❌ **时间线展示所有错误历史** — 认知过载 + 学生不会看
- ❌ **独立"错误日志"页面** — 无竞品先例，研究表明低成绩学生不会去看
- ❌ **在节点上直接显示"错误 N 次"** — 缺少基准，可能引发焦虑

---

## 六、建议新增的 PRD 功能需求

> 以下 FR 建议添加到 PRD 的"能力域 5：精通度与学习追踪"中，或新建"能力域 9：学习档案"。

| ID | 功能需求 | 优先级 | 来源 |
|----|---------|--------|------|
| FR-TRACE-01 | 用户点击节点可查看该节点的学习档案面板，包含聚合精通度指示器 | P1 | OLM 三层渐进 L1 |
| FR-TRACE-02 | 学习档案面板展示用户在该节点标注的所有 Tips（关键知识点），可展开查看来源对话上下文 | P1 | 竞品安全共识 |
| FR-TRACE-03 | 学习档案面板展示该节点的"需要加强方向"（聚合的误解模式），使用正面支持性语言 | P1 | OLM + 错误心理学 |
| FR-TRACE-04 | 学习档案面板提供关键问答精选（按主题聚类），默认折叠，按需展开 | P2 | Learning Analytics Dashboard |
| FR-TRACE-05 | 系统在对话归档时自动提取并持久化错误/Tips/关键问答到知识图谱 | P1 | Hot-Warm-Cold 归档依赖 |

---

## 七、Decision-Review 记录

### [Decision] 三层渐进侧边栏学习档案方案

- **选择**：节点侧边栏 "学习档案" Tab，三层渐进展示（L1 精通度 → L2 Tips + 加强方向 → L3 对话片段 + Q&A）
- **否决**：原始错误列表展示、独立错误日志页面、时间线模式
- **理由**：8 竞品无一展示错误列表给学生；OLM/Bull&Kay 推荐聚合可视化；2025 论文警告低成绩学生不会看错误反馈
- **验证状态**：PENDING（待用户确认方向 + 独立 session 制定验收标准）

### [Code-Review] 学习痕迹展示基础设施

- **评级**：部分可复用 + 大量需新建
- **可复用**：entity types（4 种）、bridge write path、search_claude_records
- **需新建**：对话提取管道（Hot-Warm-Cold 零实现）、Tips/KeyQA 实体类型、按 node_id 查询 API、前端组件
- **关键问题**：node_id 格式不一致（bridge vs react_agent）

---

## 八、与主 Tab PRD Review 的关系

本报告为主 Tab PRD Review 提供以下输入：

1. **PRD 缺口确认** — FR-TRACE-01 ~ FR-TRACE-05 建议新增
2. **代码现状评估** — Hot-Warm-Cold 对话归档管道零实现（PRD 中画了但代码不存在）
3. **设计方向** — 三层渐进展示（待用户确认）
4. **学术证据** — 展示学习痕迹有正面效果但需严格设计条件

主 Tab 在继续验证时应引用本报告的发现，特别是：
- Step 2 格式检测时，注意 PRD 缺少的 FR-TRACE 系列
- 后续步骤验证功能需求完整性时，需评估是否纳入 FR-TRACE
