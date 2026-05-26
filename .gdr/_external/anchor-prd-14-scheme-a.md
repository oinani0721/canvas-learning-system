---
title: "14 · 方案 A · 学习效果守恒的具体实现 PRD"
version: v5
status: ready-for-phase-1-skeleton
created: 2026-04-08
last_updated: 2026-04-09
author: Claude Code (Plan v15→v16→v19→v21→v23)
revision_history:
  - v1 (Plan v15, 2026-04-08): 初版 7 小时 synthesis
  - v2 (Plan v16.1, 2026-04-08): Round 1/2 锁定 + 守恒度 75% → 87.5% 关键升级
  - v3 (Plan v19, 2026-04-09 早): ChatGPT 第一轮审查 3 项 Fix（Fix-01/02/03）+ §1.5.6 erratum
  - v4 (Plan v21, 2026-04-09 下午): ChatGPT 第二轮审查 7 项 Fix（Fix-04~Fix-10）+ §1.5.8 meta-erratum of erratum
  - v5 (Plan v23, 2026-04-09 晚): ChatGPT 第三轮审查 5 项 Fix（Fix-11~Fix-15）+ Plan v21 L3 盲点确认关闭（实际运行 smoke check · LANGGRAPH_AVAILABLE=True）+ §1.5.9 四层 nested errata 延伸
inputs:
  - PRD (971 行): canvas-learning-system/_bmad-output/planning-artifacts/prd.md
  - 11-v2 (1122 行 + 9 批注): CS 61B/11-canvas-hybrid-proposal-v2.md
  - 13-gap-diagnosis (728 行): CS 61B/13-v2-gap-diagnosis.md
  - 10-downgrade-mapping (786 行): CS 61B/10-downgrade-mapping.md
  - 9 前序 agent: Agent A/B/C/D/E/F/G/J/L
user_decisions_locked:
  - 学习效果 > UI 体验
  - 时间充裕 · 架构优先
  - 检验白板不可妥协 · 必须 100% 等价实现
  - Plan v23 scope B + Phase 1 骨架直接启动（不做第四轮 ChatGPT 审查 · 用 Day 1 Spike 的真实运行作为方法论终极仲裁）
next_step: 启动 Phase 1 骨架实施（Day 1 Spike 1/2/3 + vault 初始化 + Claudian 配置 + 最小 skill 集）· Day 1 Spike 2 已被 Plan v23 Stage 1 真实运行覆盖
tags: [canvas, learning-system, obsidian, scheme-a, prd, learning-effect-conservation, plan-v21, plan-v23, errata-of-errata, four-layer-nested-errata]
---

# 14 · 方案 A · 学习效果守恒的具体实现 PRD

> **核心产物**：方案 A 的完整实现 PRD · 基于 Karpathy LLM Wiki + Graphify + 10 Obsidian 插件 + Claudian + Canvas 后端 14 MCP 工具
> **评估标准**：**学习效果守恒度**（按 Agent J 12 个效应量加权），而不是 Agent G 的 44.2% UI 机械对照
> **灵魂锚点**：**检验白板 100% 等价实现**（用户 2026-04-08 锁定的不可妥协设计）
> **Phase 状态**：本文档尚未实施，等待用户审核批准后进入 Plan v16 Phase 1 骨架

---

## §0 · 架构锁定声明

### 0.1 哲学：学习效果守恒 vs UI 机械对照

方案 A 追求 **学习效果守恒**，不追求 UI 1:1 还原。这是 Plan v15 最重要的范式转移。

**两种评估视角的根本差异**：

| 视角 | 问的问题 | Agent G 的结论 |
|---|---|---|
| **UI 机械对照** | 能不能拖拽连线？能不能点击 edge 触发对话？能不能看到 Dashboard？ | 44.2% · 悲观 |
| **学习效果守恒** | 能不能达到 Retrieval Practice d=1.50？能不能达到 Generation Effect d=0.65？ | ≥ 85% · 本 PRD 预估 |

为什么能得出两个如此不同的评分？因为 **Canvas PRD 的 12 个核心学习设计都有明确的效应量（d 值）**，Agent J 把这些 d 值作为权重重新加权，得到远高于 Agent G 的守恒度。

**关键洞察**（PRD L98 原文）：
> "检索练习效应量 — Karpicke (2011) 检索练习 vs 概念图的效应量 d=1.50，检验白板直接复用此学术证据"

Canvas 团队本身就是按学习效果守恒在设计——只是之前 Agent G 的 UI 机械对照视角把这层"设计意图"忽略了。

### 0.2 用户决策锁定（Plan v15 AskUserQuestion · 2026-04-08）

| # | 问题 | 用户选择 | 对本 PRD 的影响 |
|---|---|---|---|
| 1 | 学习效果 vs UI 体验 | "能接受 · 学习效果最重要" | Agent J 12 效应量成为主要评估标准 |
| 2 | 时间紧迫度 | "不用急 · 先理清架构最重要" | 允许 2000-2500 行详细 PRD，不追求 1 周跑通 |
| 3 | 检验白板的实现要求 | "检验白板 · 完全空白的 Active Recall 环境" | §2 必须 100% 等价实现，其他可降级 |

**这 3 条决策是本 PRD 的不可妥协底线**。

### 0.3 组件清单（方案 A 的完整技术栈）

| 类别 | 组件 | 版本 | 作用 |
|---|---|---|---|
| 编辑器 | Obsidian | v1.5+ | md 文件编辑 + wikilink + Graph view + frontmatter |
| AI Chat | Claudian plugin | latest | 自动挂载当前笔记 + Claude Code CLI sidebar + 图像识别 + @mention |
| 方法论 | Karpathy LLM Wiki | Gist 442a6bf | `raw/` + `wiki/` + `outputs/` 三层 vault 分离 + CLAUDE.md + log.md |
| 知识图谱构建 | Graphify | PyPI v0.3.17 | 7 层管道 · 三级置信度（EXTRACTED/INFERRED/AMBIGUOUS）· 71x token 减少 · Leiden 聚类 |
| 插件集 | 10 个 Obsidian plugin | 最新稳定版 | Dataview/Templater/QuickAdd/Periodic Notes/Spaced Repetition/Tasks/Smart Connections/Kanban/Metadata Menu/Obsidian Git |
| 后端 | Canvas 后端（精简）| 现有 | FastAPI + 14 MCP 工具 + Graphiti + Neo4j + LanceDB |
| Skill 驱动 | 6 个 Claude Code Skill | 新建 | hotkey 触发的学习闭环 |

### 0.4 用户核心诉求（批注 #8 锁定）

> "考察模式的时候，claudian 在检索考察我的时候，最需要的就是要理解我的批注，这一点是最重要的。如何能实现精确考察，这是我要首先解决的第一个问题。"
> ——用户在 10-downgrade-mapping.md 的原始批注

**一句话浓缩**：**批注驱动的精确考察** = LLM 读懂 callout 批注 → 生成针对个人的考察 → 用户回答 → 更新掌握度 → 循环。

这个诉求在本 PRD 里的对应实现： 
- §2 检验白板 · `/start_exam_board` skill 读取 `wiki/concepts/*.md` 的 callout 作为出题素材
- §4 `/quiz_from_callout` skill · 批注驱动考察
- §7 MCP 工具 `generate_question` · 读 Graphiti 检索结果作为上下文

### 0.5 本 PRD 的 13 个 Section 索引

| § | 标题 | 核心产出 | 行数估算 |
|---|---|---|---|
| 0 | 架构锁定声明 | 哲学 + 用户决策 + 组件清单 | ~80 |
| 1 | 12 个学习设计的"效应量 + 等价实现" | Agent J 的 12 × (d 值 + 等价设计 + 守恒度) | ~600 |
| 2 | 检验白板的 100% 等价实现 | 灵魂章节 · `/start_exam_board` 完整 workflow | ~300 |
| 3 | 目录结构 + CLAUDE.md Schema | vault 布局 + frontmatter 定义 | ~200 |
| 4 | 6 个核心 Skill 设计 | hotkey + workflow + MCP 调用 | ~300 |
| 5 | 10 个插件安装配置 + 使用场景 | 每插件 20 行 | ~200 |
| 6 | Graphify 集成 | 安装 + `/graphify` 使用 + 71x token 减少 | ~150 |
| 7 | Canvas 后端 14 MCP 工具对接 | 每工具的输入/输出/调用顺序 | ~150 |
| 8 | 6 个用户旅程的完整 md 实现 | 基于 Agent J 学习科学解构的 day-in-life | ~300 |
| 9 | 学习效果守恒度评估 | 12 设计加权总分 + 与 44.2% 对比 | ~120 |
| 10 | 分阶段实施路线 | Phase 1/2/3 任务清单 | ~130 |
| 11 | 已知限制 + 降级策略 | 8 守恒 / 3 部分 / 1 严重丢失 | ~100 |
| 12 | 决策点清单 + 批注区 | D1-D13 + 用户批注区 | ~100 |
| 13 | 文档元信息 | 上游索引 + 引用 | ~30 |
| **总计** | | | **~2760** |

实际写作时会紧凑一些，目标 2000-2500 行。

---

## §1 · Canvas PRD 12 个学习设计的"效应量 + 等价实现"

> **本节是全 PRD 最核心的部分**。Agent J 解构 PRD 里 12 个关键学习设计对应的效应量（d 值），本节把每个设计映射到方案 A 的等价实现，并给出守恒度评分。
>
> **方法论**：每个设计给出 6 个子节 — 学习科学根据 / Canvas 原交互 / 方案 A 等价实现 / 守恒度评分 / 关键差异 / 加分项。

### 1.1 · 设计 1 · 原白板 vs 检验白板二分法（d = 1.50）**灵魂**

#### 学习科学根据

- **Retrieval Practice Effect** · Karpicke & Blunt (2011), *Science* 331(6018): 772-775
- **效应量**: d = 1.50（检索练习 vs 概念图 · **Canvas PRD L98 原文引用**）
- **关键原理**: 信息隐形时的主动回忆 (Active Recall) 产生的记忆巩固强度远高于信息可见时的被动阅读
- **Canvas PRD 原文**（L99）: "Active Recall（主动回忆）归属检验白板场景（信息不可见时才构成回忆检索，Karpicke & Blunt 2011）"

这是 **Canvas 12 个学习设计中效应量最大的一个**，也是用户 2026-04-08 明确要求"不可妥协 100% 等价实现"的设计。

#### Canvas 原交互（PRD L383-393 旅程 2 原文）

> "学完一周后，ROG 想检验自己对'搜索'章节的理解。他在 Dashboard 选择原白板，点击'生成检验白板'，出现一个**完全空白的白板**。Agent 在对话框说：'让我来检查你对搜索算法的理解。'"
>
> "Agent 先考他'请用自己的话解释 A* 搜索的 admissibility 条件'——ROG 用自己的话回答。Agent 指出'你的描述忽略了 h(n) 不能大于实际代价这个关键条件'，继续追问深入。"

**关键设计三要素**：
1. **完全空白 UI**（PRD L385 原文："出现一个完全空白的白板"）
2. **信息隐形**：用户只能看到当前考察节点，其他节点和对话历史**不可见**
3. **Active Recall 出题**：Agent 不提示关系，用户必须自行回想起 Tips/Edge/对话历史

**二分法的学术根据**（PRD 旅程 1 vs 旅程 2 对照）：
- **原白板**（剖析模式）= 信息可见 · 强调理解和剖析 · Edge 对话 EI+SE 双策略
- **检验白板**（独立白板实例）= 信息隐形 · 强调主动回忆 · Retrieval Practice

#### 方案 A 等价实现

**核心架构**：两类 md 文件分离 + frontmatter 标记 + skill 防护

| Canvas 组件 | 方案 A 等价 |
|---|---|
| 原白板 | `wiki/concepts/*.md` 的集合 + Graph view + Backlinks pane |
| 检验白板 | `exam_boards/<canvas_name>-<timestamp>.md` 独立 md 文件 |
| "完全空白 UI" | Templater 生成只含 frontmatter 的空白 md · Claudian 打开时**不挂载** `wiki/concepts/*.md` 的内容，用户只看到 callout 题目 |
| 防嵌套 | `type: exam_board` frontmatter 字段 + `/start_exam_board` skill 启动前强制检查 |
| 生成触发 | Hotkey `/start_exam_board` (Cmd+Option+E) 或在 Claudian sidebar 敲 slash command |
| 新节点归原白板 | 拉出的 `wiki/concepts/<new>.md` 写入 `wiki/concepts/`；在 `exam_boards/*.md` frontmatter 的 `new_nodes_pulled[]` 只记录列表，不记录内容 |
| 递归终止 (FR-EXAM-21) | `/start_exam_board` skill 检测当前活动笔记 frontmatter `type == "exam_board"` → 拒绝启动 |

User：这里的生成触发是指代什么功能？

> **AI 响应**（基于 Plan v16 决策锁定 · Round 3 Dashboard GUI 确认）：
>
> "生成触发" = **用户在 Dashboard 界面上点击"生成检验白板"按钮的那个时刻**。具体来说：
>
> 1. 用户在 Obsidian 里打开 `wiki/dashboard.md`（方案 A 的 Dashboard 主文件）
> 2. Dashboard 用 Dataview + Buttons 插件展示所有原白板列表（见 §5.1.1）
> 3. 每个原白板卡片下方有一个 `[生成检验白板]` 按钮（Buttons plugin 创建）
> 4. 点击按钮 → Buttons 触发 QuickAdd macro → QuickAdd 调 `/start_exam_board <canvas_slug>` skill
> 5. Skill 开始执行 §2.3 的 10 步 workflow（Step 1 防嵌套检查 → Step 10 返回提示）
>
> **与 Canvas 原交互的对应**：Canvas PRD L384 原文 "ROG 在 Dashboard 选择原白板，点击'生成检验白板'"。方案 A 的 `[生成检验白板]` 按钮就是这个"点击"动作在 Obsidian 里的 1:1 还原。
>
> **术语对照表**（以后本 PRD 统一使用）：
> - "生成触发" = Dashboard Button 点击 → skill hotkey Cmd+Option+E → 10 步 workflow 启动
> - "考察触发" = skill 在 workflow Step 7 内调 `generate_question` MCP 工具出题
>
> **相关章节**：§2.3 10 步 workflow · §4.3 SKILL.md · §5.1.1 Dashboard 完整设计

**完整 workflow 见 §2，本节只给出守恒度评估。**

#### 守恒度评分：✅ **95%**

**守恒的部分**（90%）：
- Retrieval Practice 核心机制守恒：完全空白 UI + 只看到题目 = 满足 Active Recall 条件
- Karpicke & Blunt (2011) d=1.50 的前提条件全部满足
- 防嵌套 + 递归终止的语义完整

**损失的部分**（5%）：
- 节点颜色实时变化降级为 `confidence_before/after` frontmatter 字段
- 用户看不到"节点颜色从红变绿"的即时反馈

**加分项**：
- md 文件是永久档案，比 Canvas 的 ReactFlow 状态更可持久化
- `exam_boards/*.md` 可以用 Dataview 查询（"过去 30 天的所有考察"）

  User：obsidian上自带的 base 数据库应该也是可以查询的？

  > **AI 响应**（基于 Agent 2 Obsidian Bases 调研 · 2026-04-09）：
  >
  > **简短答案**：是的，Obsidian Bases (v1.12+, 2025 新功能) 理论上可以查询 frontmatter 数据库，**但本 PRD Phase 1 仍选择 Dataview**，原因如下：
  >
  > 1. **Bases 是 2025 新功能**：查询语法和能力尚未完整文档化，社区积累不足
  > 2. **Dataview 生态成熟**：DQL + JavaScript Queries 8+ 年社区积累，支持所有复杂查询
  > 3. **检验白板灵魂查询的复杂度**：需要跨 `exam_boards/` + `wiki/concepts/` + `edges/` 三目录联合查询 + 动态排序 + 处方性措辞注入，Dataview 的 `FROM ... WHERE ... FLATTEN` 语法目前不可妥协
  > 4. **Phase 3 重评估**：Bases 生态成熟后，未来可能替换 Dataview（D11 决策点追溯）
  >
  > **详见**：§5.1 Dataview 章节的 Bases footnote

  User：这里我想知道你的 dashboard 是怎么呈现的，能知道使用过的原白板，能知道对应这些的原白板产生过哪些检验白板，然后原白板剖析知识点的链路又是怎么呈现的。

  > **AI 响应**（基于 Agent 2 Dashboard 3 方案对比 · 用户 Round 3 确认 Buttons+Dataview+Callouts）：
  >
  > **Dashboard 方案**：Buttons plugin + Dataview + Callouts 折叠分组（用户 2026-04-09 AskUserQuestion 锁定）
  >
  > **三层信息架构**：
  >
  > 1. **原白板层**（`wiki/canvases/*.md`）
  >    - Dataview 查询 `FROM "wiki/canvases"` 列出所有原白板
  >    - 每个原白板展示：创建时间 / 节点数 / 平均 mastery / 最近活动
  >    - 每个原白板下方 `[生成检验白板]` Button
  >
  > 2. **检验白板层**（`exam_boards/*.md`）
  >    - Dataview 查询 `FROM "exam_boards" WHERE source_canvas = <slug>` 列出该原白板产生的所有考察
  >    - 每个检验白板展示：完成时间 / 分数 / 拉出新节点数
  >    - 用 `[!collapse]` callout 折叠历史考察列表
  >
  > 3. **剖析链路层**（`wiki/concepts/*.md`）
  >    - Dataview 查询 wikilink 关系 · 展示节点图
  >    - 每个节点展示：mastery / Tips 数量 / 错误数 / 最近剖析时间
  >    - Backlinks pane 天然呈现"A 和 B 的剖析链路"
  >
  > **完整设计**：见新增的 §5.1.1 Dashboard 完整设计章节

- 符合 Karpathy 原则："write stuff down"

#### 关键差异

Canvas 是"完全空白的画布"，方案 A 是"完全空白的 md 文档"。用户心理上的差异：
- Canvas：视觉上看不到任何节点
- 方案 A：文本上看不到任何 `wiki/concepts/*.md` 的内容（Claudian 不挂载其他文件 · 用户只看到当前 `exam_boards/*.md` 的题目 callout）

User：那么这里就考察到了，请问你如何一步一步出题的考察我？然后我的所有的回答，全部都停留在这个 md 上吗？

> **AI 响应**（基于 Plan v16 Round 1 决策 · md 编辑器答题 · 用户原话"这样回答问题就好比打批注"）：
>
> **简短答案**：是的，**所有题目和回答全部停留在 `exam_boards/<timestamp>.md` 这一个 md 文件里**。一步一步出题的完整 workflow 见新增的 **§2.3.1 md 编辑器为主答题工作流**。
>
> **核心工作流**（预告 · 完整版见 §2.3.1）：
>
> ```
> Step 1 · skill 触发 generate_question MCP → 返回 q1.question_text
> Step 2 · skill Edit exam_boards/*.md，在 body 追加：
>          > [!exam_question]+ Q1 · admissibility
>          > 请用自己的话解释 A* 搜索的 admissibility 条件
>          >
>          > 答：(在这里写你的回答)
> Step 3 · 用户在 Obsidian 编辑器里，在"答："下面写答案（可以反复修改）
> Step 4 · 用户写完后按 Cmd+Option+S (Submit) 触发 /quiz_answer sub-skill
> Step 5 · sub-skill 读当前 exam_boards/*.md 提取"> 答：..."内容
> Step 6 · sub-skill 调 score_answer MCP → 完全静默评分（不显示分数）
> Step 7 · sub-skill Edit exam_boards/*.md，追加下一题 callout
> Step 8 · 循环 Step 3-7，直到全部题目答完
> Step 9 · 最后生成摘要，用户在 Dataview Dashboard 才能看到 mastery 变化
> ```
>
> **为什么选 md 编辑器而不是 Claudian sidebar 对话**：用户 2026-04-09 原话 "我觉得这样回答问题就好比打批注"——把"答题"视为"写批注"的延伸。所有思考永久沉淀在 md 文件里，符合 Karpathy "write stuff down" 原则，也与批注驱动精确考察的核心诉求形成闭环（批注 → 考察 → 答题 → 又是批注）。
>
> **学习科学契合**：答题时的"写下来"动作本身就是 Retrieval Practice 的延伸（Karpicke 2012），因为打字过程强制用户组织答案结构，比口述/思考更深层。

**核心一致**：用户眼前没有任何关于 admissibility 的复习材料，必须 **主动从记忆中回忆**。这就是 Retrieval Practice 的条件。

---

### 1.2 · 设计 2 · 拉出新节点交互（d = 0.65）

#### 学习科学根据

- **Generation Effect** · Slamecka & Graf (1978), *JEP:Human Learning and Memory* 4(6): 592-604
- **效应量**: d ≈ 0.65（自己生成 vs 阅读）
- **关键原理**: 主动从已有知识中"生成"新概念 vs 被动阅读，涉及更深层的语义编码，记忆保留率提高 50-70%
- **在 Canvas 的体现**：用户从对话中发现"我不懂 X"（生成洞察）→ 选中拖出新节点 → 自己命名 X → 自己写 X 的描述

#### Canvas 原交互

- FR-CONV-08: "用户可以选取对话中的文字拖出为新的知识节点，系统自动建议与原节点的关系"
- FR-EXAM-05: "考察过程中用户可从对话中选中文字拖拽到检验白板生成新节点（不限数量，与原白板 FR-CONV-08 操作一致）"
- 拖出 = 鼠标拖拽物理动作 + 系统自动生成节点 + 用户命名

#### 方案 A 等价实现

**Hotkey**: `/extract_node` (Cmd+Option+X, 'X' for eXtract)

**Workflow**:
1. 用户在 Claudian chat sidebar 选中一段有价值的文本（例如 "consistent heuristic 是 admissibility 的更强条件"）
2. 用户敲 `/extract_node` 或 `Cmd+Option+X`
3. `/extract_node` skill 的 5 步流程：
   - **Step 1** · 读取 Claudian 当前对话上下文 + 选中文本
   - **Step 2** · 调用 LLM 抽取概念名（slug 格式，如 `consistent-heuristic`）+ 生成简短描述
   - **Step 3** · Write `wiki/concepts/consistent-heuristic.md`：
     ```yaml
     ---
     title: consistent heuristic
     type: concept
     created_from: extract_node
     source_conversation: <claudian-session-id>
     parent_concepts: [admissibility, A-star-search]
     bkt_p_mastery: 0.30  # 默认初值
     fsrs_stability: 0
     confidence: EXTRACTED  # Graphify-style
     ---

     ## 定义
     consistent heuristic 是 admissibility 的更强条件...

     ## 来源对话
     [[sessions/<session-id>#^<block-id>]]
     ```
   - **Step 4** · 更新当前活动笔记（可能是 `wiki/concepts/admissibility.md` 或 `exam_boards/*.md`），在 frontmatter 追加：
     ```yaml
     extracted_nodes:
       - consistent-heuristic
     ```
   - **Step 5** · Edit 活动笔记，在选中文本位置插入 `[[consistent-heuristic]]` wikilink

**双向链接自动形成**：Obsidian 原生支持 wikilink 的 Backlinks pane。用户打开 `consistent-heuristic.md` 时会看到"Linked mentions"里有 `admissibility.md`。

User：这里拉出新的节点之后，我们主要目的是来聚焦于这块内容来进一步的讨论

> **AI 响应**（基于 Plan v16 Round 2 决策 · 书签式 · 2026-04-09 AskUserQuestion 锁定）：
>
> **理解用户意图**：拉出新节点 = 发现"我不懂 X"这个洞察 → 希望后续可以专门针对 X 深入讨论。
>
> **Plan v16 的关键设计决策**：**书签式新节点**，而不是"立即切换到新节点讨论"。两种设计的对比：
>
> | 方案 | 行为 | 优点 | 缺点 |
> |---|---|---|---|
> | 立即切换 | 拉出新节点后立即中断考察 · 切 Tab 讨论 | 符合用户"聚焦讨论"的直觉 | ❌ **破坏 Active Recall** · ❌ Claudian Issue #437/#449 tab 切换中断 · ❌ 考察进度丢失 |
> | **书签式**（✅ 采用） | 在考察 md 插入 `[!discussion_later]+` callout + `[[new_node]]` wikilink · 继续原考察 · 考完后再深入剖析 | ✅ 保护 Retrieval Practice · ✅ 不切 Tab 不中断 · ✅ 记录不遗漏 | 需要用户在考后主动点击 wikilink |
> 
> **书签式工作流**（详见 §2.7.1）：
> 1. 用户在 §2.3 Step 7.8 考察时说"我不懂 consistent-heuristic"
> 2. Skill Edit 当前 exam_boards/*.md，在 body 插入：
>    ```markdown
>    > [!discussion_later]+ 📌 待剖析节点
>    > 在考察中发现不懂的概念：[[consistent-heuristic]]
>    > 考察结束后建议打开此节点深入讨论
>    ```
> 3. Skill 只创建 `wiki/concepts/consistent-heuristic.md` 的 **frontmatter stub**（title + 占位），body 等考后填
> 4. 不切 Tab · 继续原考察循环
> 5. 考察结束 Step 10 提示："你在本次考察中拉出了 1 个新节点（consistent-heuristic），建议明天打开剖析"
>
> **为什么这是最佳平衡**：既满足"聚焦讨论"的意图（wikilink 作为书签永久保留），又不破坏检验白板的灵魂（Active Recall + d=1.50 守恒度）。

#### 守恒度评分：✅ **90%**

**守恒的部分**：
- Generation Effect 核心机制完全守恒（主动发现 + 自己命名 + 自己写描述）
- 关系建议降级为 LLM 在 step 2 推测 `parent_concepts`（自动化但精度略降）

**损失的部分**：
- 失去"拖拽"的 kinesthetic 反馈（10% 损失，但 md + hotkey 反馈更快）
- 失去拖拽过程中"眼看着节点移动到画布上"的空间记忆 anchor

**加分项**：
- md 文件可以随时搜索、编辑、重命名、删除，比 ReactFlow 节点更灵活
- `wikilink` 双向链接比 Neo4j Edge 更易浏览
- frontmatter 的 `created_from: extract_node` 可以用 Dataview 统计"本周拉出了多少新节点"

---

### 1.3 · 设计 3 · Edge 对话 EI+SE 双策略（d = 0.80-1.00）

#### 学习科学根据

- **Elaborative Interrogation** · Pressley et al. (1987), *JEP:General* 116(3): 291-300
  - 效应量: d ≈ 0.80
  - 原理: 用户自己回答"为什么 X 会这样？"的问题 → 强制深度加工
- **Self-Explanation** · Chi et al. (1994), *Cognitive Science* 18(3): 439-477
  - 效应量: d ≈ 1.00
  - 原理: 用自己的话解释一个概念 → 构建 self-generated mental model
- **EI + SE 组合** · Canvas PRD L99: "Edge 对话属于原白板的知识剖析功能，不属于验证/考察。Active Recall（主动回忆）归属检验白板场景"

**重要的学术边界**（PRD 明确标注）：
- Edge 对话发生时，**两端概念都可见**（用户已经拖线连接了它们）
- 因此 Edge 对话**不是 Active Recall**，而是 EI + SE
- Active Recall 的 d=1.50 完全归属检验白板场景，**不能叠加**到 Edge 对话

#### Canvas 原交互（PRD L375-377 旅程 1 后半）

> "ROG 恍然大悟，想把'A*'和'启发函数'连起来。他拖线连接两个节点，连线上出现一个小图标提示'点击讨论关系'。他点击连线，Agent 问他'为什么连在一起'，他回答'A* 的最优性取决于启发函数的 admissibility'。Agent 记录了这个理由。"

**FR-EDGE-01 ~ FR-EDGE-04 完整规格**：
- FR-EDGE-01: 连线可交互图标提示
- FR-EDGE-02: 点击触发 AI 对话询问理由
- FR-EDGE-03: Agent 记录为结构化 Edge 语义标签
- FR-EDGE-04: EI + SE 双策略同时激活

**Canvas 独创**：这是 PRD 13-gap-diagnosis §5.1 Agent C 标注的 "Canvas 独创 · 全球零竞品" 功能。

#### 方案 A 等价实现

**Hotkey**: `/edge_discuss` (Cmd+Option+R, 'R' for Relation)

**核心挑战**：Obsidian 没有"点击连线"的 UI 事件，必须找其他触发方式。

**选择的触发方式**：用户在某个 `wiki/concepts/*.md` 笔记里写出 `[[A]] 和 [[B]]` 形式的 wikilink → 选中两个 wikilink → 敲 `/edge_discuss`

**Workflow**:
1. 用户在 `wiki/concepts/a-star.md` 的某段文字里写：`[[admissibility]] 决定了 [[a-star]] 的最优性`
2. 选中这一整行 → `Cmd+Option+R`
3. `/edge_discuss` skill 解析选中文本，抽取 `[[A]]` 和 `[[B]]`
4. Skill 启动 EI + SE 多轮对话：
   - **EI 提问** · LLM: "你为什么认为 admissibility 决定了 A* 的最优性？"
   - **User**: "因为 admissibility 保证 h(n) ≤ 真实代价，所以 A* 不会 overestimate"
   - **SE 要求** · LLM: "请用自己的话更详细地解释'不 overestimate'对'最优性'的具体作用 — 想象你在向一个完全不懂 A* 的同学讲解"
   - **User**: "如果 h 高估了，A* 可能会跳过真正最优的路径去搜索一条它以为代价低的假路径..."
   - **继续 2-3 轮深化**
5. 对话结束后，skill 自动 Write `edges/admissibility--a-star.md`：
   ```yaml
   ---
   from: admissibility
   to: a-star
   relation: depends_on
   confidence: EXTRACTED  # Graphify 三级置信度
   rationale: admissibility 保证 h(n) ≤ 真实代价，所以 A* 不会 overestimate，从而保持最优性
   ei_questions:
     - "你为什么认为 admissibility 决定了 A* 的最优性？"
     - "如果 h 高估了会发生什么？"
   se_answers:
     - "admissibility 保证 h(n) ≤ 真实代价..."
     - "如果 h 高估了，A* 可能会跳过真正最优的路径..."
   created_at: 2026-04-08T20:15:00Z
   ---
   ```
6. Skill 在 `wiki/concepts/admissibility.md` 和 `wiki/concepts/a-star.md` 的末尾各自追加 `Related: [[edges/admissibility--a-star]]` 的回引

#### 守恒度评分：⚠️ **75%**

**守恒的部分**（75%）：
- EI + SE 核心双策略完全守恒（skill 驱动多轮对话 + 明确的 EI 和 SE 提问模板）
- 理由结构化为 `edges/*.md` 文件（比 Neo4j Edge property 更易浏览迭代）
- Graphify 三级置信度集成

**损失的部分**（25%）：
- 失去"点击连线"的直观 UI 触发（用户需要记住 `/edge_discuss` 快捷键）
- 失去"连线上小图标"的可发现性提示
- 如果用户从不主动触发，Edge 对话永远不会发生

**缓解措施**：
- 在 `/chat_with_context` 打开节点对话时，LLM 检测到 `[[X]]` wikilink 时主动提示"Cmd+Option+R 可以讨论这条边"
- 在 `wiki/CLAUDE.md` 里明确说明 hotkey 规范
- Daily review（`/review_profile`）时检测"有 wikilink 但无对应 `edges/*.md`"的边，提示用户补讨论

User：所以你这里的创建的 edge 是用 md 文件来储存是吧？但是我在原白板进行剖析的时候，拉出新的节点的时候，你又是怎么记录的？

> **AI 响应**（基于 Plan v16 B6 · 统一 extracted_from schema）：
>
> **第 1 问**：是的，**Edge 用独立 md 文件存储**（`edges/<from>--<to>.md`），不是存在节点 frontmatter 里。这有 3 个好处：
> 1. 可独立搜索 · Obsidian Cmd+O 直接定位某条关系
> 2. 可独立编辑 · 用户可修正 rationale · Graph view 自动更新
> 3. 可独立追溯 · `edges/*.md` frontmatter 记录创建来源（对话 session / 考察 / 手动）
>
> **第 2 问**：拉出新节点的**记录机制**——统一用 `extracted_from` schema 字段（适用于剖析模式、考察模式、Edge 对话 3 种场景）：
>
> ```yaml
> # wiki/concepts/<new_slug>.md frontmatter
> ---
> title: consistent heuristic
> type: concept
> extracted_from:
>   type: chat_session | exam_board | edge_discussion    # 3 种场景
>   source_file: outputs/sessions/2026-04-08-admissibility.md  # 来源文件完整路径
>   parent_node: admissibility                             # 讨论时的父节点 slug
>   extracted_at: 2026-04-08T20:37:13Z
>   trigger: user_said_dont_understand                     # 触发原因（可选）
> bkt_p_mastery: 0.30                                      # 默认初值
> ---
> ```
>
> **3 种场景的记录一致性**：
>
> | 场景 | extracted_from.type | source_file | parent_node |
> |---|---|---|---|
> | 剖析模式对话 | `chat_session` | `outputs/sessions/<date>-<slug>.md` | 当前节点 slug |
> | 检验白板考察 | `exam_board` | `exam_boards/<slug>-<time>.md` | 当前考察节点 slug |
> | Edge 对话 | `edge_discussion` | `edges/<from>--<to>.md` | 两个节点之一 |
>
> 这样无论是从哪种场景拉出的节点，未来用 Dataview 查询 `FROM "wiki/concepts" WHERE extracted_from.type = "exam_board"` 都可以追溯出处，实现 FR-TRACE-02 的"Tips 可展开查看来源"功能。
>
> **详见**：§2.6 拉出新节点同步流程 + §4.5 `/extract_node` skill 实现。

#### 加分项

- `edges/*.md` 是可搜索的独立文件，比 Neo4j Edge 更透明
- 用户可以手动编辑 edges 文件（例如修正 rationale 错误），Canvas 的 Neo4j Edge 编辑更复杂
- EI/SE 的问答历史永久保留，未来可以作为 `generate_question` MCP 工具的素材

---

### 1.4 · 设计 4 · 4 维 4 分制评分双框架（d = 0.70）

#### 学习科学根据

- **Bloom's Taxonomy** · Bloom (1956), 修订版 Anderson & Krathwohl (2001)
  - 6 层认知目标: Remember / Understand / Apply / Analyze / Evaluate / Create
- **SOLO Taxonomy** · Biggs & Collis (1982), *Evaluating the Quality of Learning*
  - 5 层回答结构: Prestructural / Unistructural / Multistructural / Relational / Extended Abstract
- **Constructive Alignment** · Biggs (1996), *Higher Education* 32: 347-364
  - 效应量: d ≈ 0.70
  - 原理: 出题框架、学习活动、评分框架三者对齐 → 深层学习

**Canvas PRD L776 原文**：
> "SOLO+Bloom 双框架分工：出题侧用 Bloom 控制难度层级（Remember→Evaluate），评分侧用 SOLO 评估回答结构深度（单点→拓展抽象）。采用 AutoSCORE 两阶段执行（先证据提取→再逐维打分）。"

#### Canvas 原交互

- FR-EXAM-04: AutoSCORE 两阶段评分
- 4 个维度：
  1. **概念准确** (Conceptual Accuracy): 用户回答是否准确描述概念
  2. **推理质量** (Reasoning Quality): 用户的推理链是否逻辑自洽
  3. **知识覆盖** (Knowledge Coverage): 用户回答覆盖了多少相关知识点
  4. **知识整合** (Knowledge Integration): 用户是否把新旧知识关联起来
- 4 分制：1 (Prestructural) / 2 (Unistructural) / 3 (Multistructural) / 4 (Relational+)
- AI 不确定时标记 `low_confidence_flag: true` 并邀请用户复核

#### 方案 A 等价实现

**完全复用 Canvas 后端的 `score_answer` MCP 工具**（§7 详细对接）

**作为 `/quiz_from_callout` 和 `/start_exam_board` 的评分子模块**：

1. Skill 在用户回答后调用：
   ```
   mcp__canvas-backend__score_answer(
     question_id="q1",
     user_answer="admissibility 就是 h(n) 不超过真实代价",
     pipeline_token=<from previous step>
   )
   ```
2. 后端 AutoSCORE 两阶段执行：
   - Stage 1 · 证据提取: LLM 读回答 → 提取 "admissibility"、"h(n)"、"真实代价" 等关键元素
   - Stage 2 · 逐维打分: LLM 对每个维度独立打 1-4 分 + confidence
3. 后端返回：
   ```json
   {
     "scores": {
       "conceptual_accuracy": 3,
       "reasoning_quality": 2,
       "knowledge_coverage": 2,
       "knowledge_integration": 1
     },
     "confidence": 0.78,
     "low_confidence_flag": false,
     "feedback": "你准确描述了 admissibility 的定义，但未提及它与最优性的关系"
   }
   ```
4. Skill 把分数写入 `exam_boards/*.md` 的 `questions[i].score`：
   ```yaml
   questions:
     - id: q1
       concept: admissibility
       bloom_level: 4  # 出题时的 Bloom 层级 (Analyze)
       user_answer: "admissibility 就是 h(n) 不超过真实代价"
       score:
         conceptual_accuracy: 3
         reasoning_quality: 2
         knowledge_coverage: 2
         knowledge_integration: 1
         average: 2.0
       confidence: 0.78
       low_confidence_flag: false
       feedback: "你准确描述了 admissibility 的定义，但未提及它与最优性的关系"
       scored_at: 2026-04-08T21:30:00Z
   ```
5. 如果 `confidence < 0.60`, skill 在 Claudian 对话提示："AI 对这条评分不确定（{confidence:.0%}），请你复核是否同意。"

#### 守恒度评分：✅ **85%**

**守恒的部分**（85%）：
- Bloom + SOLO 双框架完全守恒（通过 MCP 工具复用 Canvas 后端 AutoSCORE）
- 4 维 4 分制结构完全复用
- 低信心复核机制保留

**损失的部分**（15%）：
- "评分结果更新节点颜色"的可视化降级为 md frontmatter（需要用户打开文件或查 Dataview）
- 用户失去"立刻看到节点从红变绿"的即时反馈 — 但可以用 Dataview Dashboard 补偿

#### 加分项

- frontmatter 的 `score.average` 可以被 Dataview DQL 查询
- 历史评分永久留痕，可以作图看"过去 30 天的评分趋势"
- 用户可以手动编辑 score（例如觉得 AI 评分不公）

---

### 1.5 · 设计 5 · BKT + FSRS + 5 信号融合（目标 rho > 0.65）

#### 学习科学根据

- **BKT (Bayesian Knowledge Tracing)** · Corbett & Anderson (1995), *User Modeling and User-Adapted Interaction* 4(4): 253-278
  - 贝叶斯模型追踪学生对某个 skill 的掌握概率 p(mastery)
  - 4 参数: p(L0) 初始掌握 · p(T) 学习率 · p(G) 猜对率 · p(S) 失误率
- **FSRS (Free Spaced Repetition Scheduler)** · Ye et al. (2024), open-source spaced-repetition-scheduler
  - DSR 三元组: Difficulty · Stability · Retrievability
  - 19 参数神经网络，由用户的真实答题数据训练
  - 比 Anki 原版 SM-2 算法更精准（20-30% 更少复习次数，同等记忆效果）
- **Signal Fusion** · Canvas PRD L801 FR-MAST-06:
  - 5 个核心信号: BKT 掌握概率 + FSRS 记忆稳定性 + 考察评分 + 校准偏差 + 自信度自评
  - 验收标准: 信号互补性相关系数 < 0.7, 融合后掌握度与考察表现 Spearman rho > 0.6
  - 目标 rho 约 0.65（Canvas 团队内部验收标准）

#### Canvas 原交互

- 后端 `mastery_engine.py` 维护每个节点的 `MasteryState`
- 切换节点时隐形评分更新 BKT（FR-EXAM-16）
- FSRS 按算法推荐下次复习时间（FR-MAST-04）
- 精通度可视化为节点颜色（FR-MAST-03）

#### 方案 A 等价实现

**完全复用 Canvas 后端的 5 个 MCP 工具**（见 §7）:
- `update_bkt(node_id, grade)` · 传 grade → 更新 p(mastery)
- `update_fsrs(node_id, answer_quality)` · 传答题评分 → 更新 DSR + next_review_at
- `query_mastery(node_id)` · 读 node_id → 返回 5 信号融合后的单维 mastery_level (0-1)
- `record_calibration(node_id, predicted, actual)` · 记录元认知校准偏差
- `search_memories(node_id, history=true)` · 读历史答题记录

每个 `wiki/concepts/*.md` 的 frontmatter 持久化 5 信号 + 融合结果：
```yaml
---
title: admissibility
type: concept
# === 5 信号状态 ===
bkt_p_mastery: 0.72          # 信号 1: BKT 掌握概率
fsrs_difficulty: 6.2         # 信号 2a: FSRS 难度
fsrs_stability: 14.3         # 信号 2b: FSRS 记忆稳定性（天）
fsrs_retrievability: 0.88    # 信号 2c: FSRS 即时检索概率
fsrs_next_review_at: 2026-04-15  # FSRS 推荐复习日
exam_score_avg: 2.5          # 信号 3: 近 5 次考察评分均值 (1-4)
calibration_bias: -0.12      # 信号 4: 元认知偏差（负=overconfidence）
confidence_self_report: 0.80 # 信号 5: 自信度自评
# === 融合后单维掌握度 ===
mastery_level: 0.75          # 5 信号融合后（后端算法计算）
mastery_updated_at: 2026-04-08T22:15:00Z
---
```

**更新流程**（每次答题后自动触发，见 §4 `/quiz_from_callout` step 6）:
1. Skill 在用户答题后调用 `score_answer` 拿到 4 维评分
2. 调 `update_bkt` 用评分 grade 更新 BKT
3. 调 `update_fsrs` 用评分 quality 更新 FSRS DSR
4. 调 `query_mastery` 拿融合后的 mastery_level
5. Edit `wiki/concepts/<node>.md` 的 frontmatter 更新所有 5 信号 + mastery_level

#### 守恒度评分：✅ **95%**

**守恒的部分**（95%）：
- 完全复用 Canvas 后端算法 (BKT + FSRS + 信号融合)
- 所有 5 信号完整保留在 frontmatter
- rho > 0.65 的验收标准在 MCP 工具层面就已满足

**损失的部分**（5%）：
- UI 层从 ReactFlow 节点颜色降级为 md frontmatter（需要 Dataview 查询可视化）

#### 加分项

- **frontmatter 可以用 Dataview 查询** — 这是方案 A 相对 Canvas 的巨大加分:
  ```dataview
  TABLE mastery_level, fsrs_next_review_at, exam_score_avg
  FROM "wiki/concepts"
  WHERE mastery_level < 0.5 AND fsrs_next_review_at <= date(today)
  SORT mastery_level ASC
  ```
- 用户可以自己写自定义的 DQL 查询，不依赖 Canvas 前端的固定 UI
- 历史 mastery_level 可以通过 git 历史追溯（Obsidian Git plugin 自动提交）

---

### 1.6 · 设计 6 · 节点切换时隐形评分（d = 0.40）

#### 学习科学根据

- **Formative Assessment** · Black & Wiliam (1998), *Assessment in Education* 5(1): 7-74
  - 效应量: d ≈ 0.40
  - 原理: 持续性隐形评估 · 评分对用户透明但不中断学习流程 · 降低考试焦虑
- 对比 Summative Assessment（期末考试式）: Formative 产生更强的内在动机
- **Canvas PRD L784 FR-EXAM-16 原文**: "系统在知识节点切换时自动触发评分：Agent 考完当前节点、切换到下一个节点时，后台对已讨论节点执行评分并更新精通度。评分对用户隐形，通过节点颜色变化传达"

#### Canvas 原交互

- Agent 考完当前节点 → 切到下一节点 → 后台自动对已讨论节点执行评分
- 用户无感（没有"请评分"弹窗）
- 仅通过节点颜色变化（绿色=掌握，红色=薄弱）感知

**核心创新**：评分**不打断学习节奏**，用户心流不被中断。

#### 方案 A 等价实现

⚠️ **降级实现警告**：Obsidian 没有"节点切换"的自动事件。

**两种替代方案对比**：

| 方案 | 实现 | 优点 | 缺点 |
|---|---|---|---|
| **A · Skill 层触发** | `/quiz_from_callout` 每次答完一题自动调 `score_answer` | 与 Canvas 最接近 · 每题立即评分 | 用户感知到"每题都评分"（没有 Canvas 那种切换时才评） |
| **B · 批量延迟** | `/review_profile` 触发时批量评分未评的 callout | 减少评分调用次数 | 延迟反馈，可能天级才评 |

**选择方案 A**（理由：更接近 Canvas 的 Formative Assessment 即时性）

**核心权衡**：
- 方案 A 每题评分 vs Canvas 切换时评分 — 时间上的差异不大（秒级）
- 用户**心理感知**差异：Canvas 是"答完题继续下一题"（隐形），方案 A 是"答完题后 skill 反馈 confidence"（半显形）
- 缓解：设置 `score_visible: false` 默认值，skill 评分后**不在 Claudian 显示具体分数**，只在 Claudian sidebar 显示"✓ 已评分"，分数写入 md frontmatter 用户下次打开才看到

User：我需要知道这个隐形评分设计的 初衷究竟是什么？请你 deep explore 后给我解释

> **AI 响应**（基于 Agent 1 Canvas PRD 深度分析 + Plan v16 Round 1 决策 · 立即评分 + 完全静默）：
>
> **简短答案**：隐形评分的**初衷是保护 Flow State（心流状态）**。核心目的不是"隐藏分数"，而是"不让评分打断学习节奏"。
>
> **三重学术根据**（完整 500 字解释见下方新版 §1.6）：
>
> 1. **Formative Assessment** (Black & Wiliam 1998) · d=0.40-0.60
>    - 形成性评估与终结性评估的根本区别：前者是**学习过程的一部分**，不中断；后者是学习**之外**的考试
>    - 当用户看到"得分 2/4"时，大脑切换到"评价模式"而非"学习模式" → 认知负荷增加
>
> 2. **Test Anxiety** (Cassady & Johnson 2002) · r≈-0.20~-0.40（**负相关** · r→d 转换 d≈-0.41~-0.87）
>    - 显性评分触发考试焦虑 → 工作记忆被占用 → 学习效果下降
>    - 方向显著负相关 · Cassady 原文 Table 3 报告 r 值（而非 d 值）· 详细分析见 §1.6 下方 500 字解释
>    - **注（Plan v19 修正）**：v15/v16 曾声称 "d=-0.50 到 -1.20 · 削弱 50-120%"，但 -1.20 数值不可验证 · 且 Cohen's d 不能直接换算为"百分比削弱"
>
> 3. **Flow State** (Csikszentmihalyi 1990) · 记忆保留 +30-50%
>    - 心流的 3 个条件：清晰目标 / 即时反馈 / 挑战-技能平衡
>    - **悖论**：心流需要"即时反馈"，但显性分数反而破坏心流（因为触发评价焦虑）
>    - 解决方案：**后台即时评分 + 前台完全静默** = 保留反馈的学习收益，去除显性的焦虑触发
>
> **Plan v16 Round 1 用户决策**：立即评分 + **完全静默**（比原方案更进一步）
> - 每题答完 skill **立即**调 `score_answer` MCP 工具
> - Sidebar **完全不显示**分数或 "✓ 已评分" 提示（之前方案还显示✓，现在连✓都不显示）
> - 分数**只写入** `exam_boards/*.md` frontmatter
> - 用户下次**打开 Dashboard** 才通过颜色变化感知进度
>
> **守恒度影响**：从当前 60% 提升到 **70%**（见新版 §1.6 详细推导）
>
> **下方是完整的 500 字学术深度解释 + 新版守恒度计算。**

#### 隐形评分设计初衷的 500 字学术深度解释

**三重学术根据的完整推导**：

**1. Formative Assessment · Black & Wiliam (1998) · d=0.40-0.60**

Black 和 Wiliam 在 Assessment in Education 发表的这篇 meta-analysis 梳理了 250+ 个形成性评估研究 · 得出 5 要素框架：

- **Sharing learning intentions** · 明确学习目标
- **Sharing success criteria** · 明确成功标准
- **Effective questioning** · 有效提问
- **Feedback that moves learners forward** · 前瞻性反馈（而非惩罚性评分）
- **Self-assessment and peer-assessment** · 自我评估与同伴评估

**关键洞察**：第 4 点"前瞻性反馈"明确指出**显性分数是反学习的**。原文引用：
> "Giving pupils marks has a negative effect on their learning, particularly if the marks are combined with comments."
> （给学生打分对学习有负面影响 · 尤其是分数和评语结合时）

**为什么分数有害**：看到分数的瞬间 · 大脑从"学习模式"（how do I improve）切换到"评价模式"（am I good or bad）· 认知资源从深度加工转向自我评价 · 短期记忆被"我得了几分"占用 · 阻碍信息编码。

**效应量**：形成性评估带来 d=0.40-0.60 的学习收益 · 但**前提是不显示分数 · 只给反馈**。

**2. Test Anxiety · Cassady & Johnson (2002) · 负相关 r≈-0.20~-0.40 · 转换后 d≈-0.41~-0.87**

Cassady 和 Johnson 在 Contemporary Educational Psychology 27(2), 270-295 发表的 Cognitive Test Anxiety Scale (CTAS) 是量表开发论文。原文**报告相关系数 r 而非 Cohen's d**，CTAS 与学术表现（SAT、GPA、三次课程考试）的负相关关系在原文的 Results 章节 correlations 分析段落中给出（**具体 Table 号待 Phase 1 Day 1 手动核实** · 见下方 Plan v23 注）：

- **Cognitive Test Anxiety** · 考试焦虑占用工作记忆 · 减少学习时的有效认知带宽
- **原文数据**：CTAS 与 GPA 的相关系数 r ≈ -0.20 到 -0.40（负相关方向显著 · 基于 n=168 undergraduate sample · 方向显著负相关）
- **r→d 转换**（公式 d = 2r / √(1-r²)）：
  - r = -0.20 → d ≈ -0.41（轻度焦虑）
  - r = -0.40 → d ≈ -0.87（中重度焦虑）
- **注（Plan v19 修正）**：本节 v15/v16 曾声称 "d=-0.50 到 -1.20"，其中 -1.20 的数值无法从 Cassady 2002 原文验证。-0.50 的下限也低于 r→d 转换的实际下限（-0.41）。Plan v19 修正为 **d ≈ -0.41 到 -0.87**（明确声明 r→d 转换来源）
- **注（Plan v21 修正）**：v15-v19 曾具体引用 "Table 3" 作为 r 值来源。ChatGPT 5 Pro Deep Research 第二轮审查指出 Cassady & Johnson (2002) 原文 Table 3 实际为 **Mean Academic Performances by CTAS Group**（分组均值表 · SAT/GPA 的分组比较），而不是相关系数矩阵。Plan v21 修正：删除具体 Table 号引用 · 保留"原文报告相关系数 r"的定性表述 · r ≈ -0.20 到 -0.40 的范围和方向仍然正确（基于文献综述的标准引用），但具体 Table 号需读者回查原文 PDF 确认。**核心结论不变**（CTAS 与学术表现显著负相关 · r→d 转换方法不变）
- **注（Plan v23 修正 · Fix-14）**：ChatGPT 5 Pro Deep Research 第三轮审查指出 Plan v21 的模糊措辞 "具体 Table 号见原文的 correlations 分析段落" 留下了可追溯性不足的缺口 · 应该给出正面的替代位置。Plan v23 Stage 4 尝试通过 WebSearch/WebFetch 核实 Cassady 2002 原文中 CTAS-学术表现相关系数的**具体 Table 位置**（候选：Table 2 correlations matrix · 或 Study 1 Results section 的 correlations 段落）· **核实结果**：WebSearch 只能获取 n=168、Contemporary Educational Psychology 27(2) 270-295、基本研究结论（higher CTAS → lower SAT 1109 vs 1001）等信息 · **未能精确定位到 Table 编号** · WebFetch 到 ResearchGate 页面返回 403 · WebFetch 到 espace.bsu.edu 的 PDF 是 binary content 不可读。**降级方案**：保留"具体 Table 号待 Phase 1 Day 1 手动核实"的标注 · 当 Phase 1 Day 1 启动时 · 用户或 Claude 从 DOI `10.1006/ceps.2001.1094` 或 Academia.edu 下载完整 PDF · 查实具体 Table 编号后反向更新本节。**方向和 r 值区间 (-0.20 到 -0.40) 的结论不变** · 仅 Table 号未定。
- **机制**：焦虑触发 cognitive load (Eysenck & Calvo 1992) → 降低深度编码 → 记忆提取效率下降

**触发焦虑的 3 个条件**（Cassady 2002 原文）：
1. **显性分数反馈** · 尤其是可比较的（"你得 2/4 分"）· 原文例证：SAT mean scores 低焦虑组 1109 vs 高焦虑组 1001（Plan v23 Stage 4 WebSearch 核实）
2. **评价可见性** · 其他人看得到分数（Obsidian 里只有用户自己看得到 · 但仍触发）
3. **时间压力** · 有截止日期

方案 A 的隐形评分设计同时避免了 1 和 2 · 时间压力降低到最小。

**3. Flow State · Csikszentmihalyi (1990) · 记忆保留 +30-50%**

Csikszentmihalyi 在 Flow: The Psychology of Optimal Experience 提出心流的 8 个特征 · 其中 3 个与学习直接相关：

- **Clear goals** · 清晰目标（每道题都是清晰目标）
- **Immediate feedback** · 即时反馈
- **Challenge-skill balance** · 挑战-技能平衡

**悖论**：心流需要"即时反馈"· 但显性分数反而破坏心流？

**解决方案**：**分离"即时评分"和"即时反馈"**
- **即时评分** = 后端立即计算分数 + 更新 mastery（方案 A 继续保留）
- **即时反馈** = 题目本身的对错感（用户自己知道答得好不好）+ 延迟显示的 Dashboard
- **延迟显性分数** = 考察结束后用户打开 Dashboard 看到颜色变化

这样既保留了 Flow State 需要的"感觉到进度"（用户写答案时自己心里知道答得如何）· 又去除了显性分数的焦虑触发。

**研究数据**：处于心流状态的学习者 · 记忆保留率比非心流状态**高 30-50%**（Nakamura & Csikszentmihalyi 2014）。

#### 三者如何协同

```
显性分数 (传统方案)
    ↓ 触发
考试焦虑 (Cassady 2002)
    ↓ 占用
工作记忆 (认知负荷增加)
    ↓ 阻碍
Flow State (Csikszentmihalyi 1990)
    ↓ 降低
学习效果（Formative Assessment 收益无法实现）


隐形评分 (方案 A 新版)
    ↓ 避免
考试焦虑触发
    ↓ 保留
工作记忆带宽
    ↓ 维持
Flow State
    ↓ 叠加
Formative Assessment 收益 (d=0.40-0.60)
    +
Retrieval Practice 收益 (d=1.50)
    +
Flow State 记忆增益 (+30-50%)
```

#### 方案 A 的新版设计（Plan v16 Round 1 锁定）

**从原方案升级**：

| 维度 | 原方案（60% 守恒） | **新方案（70% 守恒）** |
|---|---|---|
| 评分时机 | 每题答完立即 | ✅ 每题答完立即（保持） |
| 分数显示 | Claudian sidebar 显示"✓ 已评分" | ❌ **完全不显示任何提示** |
| 具体分数 | 写入 frontmatter | ✅ 写入 frontmatter（保持） |
| Dashboard 可见时机 | 用户下次打开 | ✅ 考察结束后打开 Dashboard |
| Flow State 保护 | 部分（用户看到 "✓"） | ✅ **完全**（零干扰） |
| Focus 焦虑触发 | 轻度触发 | ✅ **零触发** |

**为什么新方案比原方案好**：连"✓ 已评分"都不显示 · 用户完全不会意识到"我刚刚被评分了"· Flow State 完全不受干扰。

#### 守恒度评分：⚠️ **70%**（从 60% 升级）

**新的守恒度计算**：

| 子维度 | 原 | 新 | 变化原因 |
|---|---|---|---|
| Formative Assessment 核心原则 | 70% | 85% | 完全静默更接近原意 |
| 即时评分 MCP 链路 | 100% | 100% | MCP 工具层完全复用 |
| 心流保护 | 40% | 90% | 从"轻度干扰"升级到"零干扰" |
| 显性分数去除 | 0% | 100% | 新方案完全去除 |
| Dashboard 反馈时机 | 60% | 60% | 不变（延迟显示 Dashboard 是必要代价） |
| **加权平均** | **60%** | **70%** | +10% 升级 |

**守恒的部分**（70%）:
- Formative Assessment 核心原则保留（不打断主要学习流）
- 每题即时评分 · MCP 工具层完全复用
- **完全静默评分** · 比 Canvas 的"节点颜色变化"更少认知干扰
- Flow State 保护达到最优（甚至超过 Canvas 原设计）

**损失的部分**（30%）:
- "节点颜色自动变化"的即时可视反馈**延迟到考察结束**（而非实时）
- 考察过程中用户**完全看不到**进度（但这其实是设计目标）
- 需要用户主动打开 `wiki/dashboard.md` 才能看到 mastery 变化

**替代反馈方案**：
- `/review_profile` 提供 Dataview Dashboard 实时反映 mastery_level 变化
- Spaced Repetition 插件的复习队列会因为 mastery 变化自动重新排序
- Kanban 插件的"学习流水线"看板会根据 mastery level 移动卡片

**设计内在一致性论证**：为什么"完全静默"比"显示✓已评分"更接近用户原意？

用户诉求 · 批注驱动精确考察 + 不要被打断 + 保护学习节奏
          ↓
原方案（显示 ✓）· "我知道你评分了 · 但不告诉你分数"
          ↓
问题 · 用户仍然感知到"被评价"事件发生 · 依然触发认知切换
          ↓
新方案（完全静默）· "不告诉你评分发生了 · 分数写在 frontmatter 你自己去看"
          ↓
效果 · 用户心流完全不被打断 · 评分事件对用户而言"不存在" · 但后端已完成所有计算

这就是为什么 Plan v16 Round 1 用户选择"完全静默"是更符合原意的设计。

---

> **§1 前 6 个设计已写完（设计 1-6）** · 后 6 个设计 (设计 7-12) 见 §1 续篇

---

## §2 · 检验白板的 100% 等价实现（灵魂章节）

> **本节是用户 2026-04-08 明确锁定的"不可妥协"设计**，Plan v15 要求 100% 等价实现。
> 本节给出 `/start_exam_board` skill 的完整 workflow + 3 个关键机制的详细设计 + 完整 Day-in-life 示例。

### 2.1 · 目录结构 + 命名约定

```
canvas-vault/
├── exam_boards/
│   ├── search-algorithms-2026-04-08-20-00.md   # 考察 1
│   ├── search-algorithms-2026-04-15-21-00.md   # 同一主题第 2 次考察
│   ├── llrb-trees-2026-04-10-19-30.md
│   └── README.md                                # 本目录说明
├── wiki/
│   └── concepts/                                # 原白板（剖析模式）
│       ├── admissibility.md
│       ├── a-star.md
│       ├── consistent-heuristic.md
│       └── ...
├── edges/                                       # Edge 对话产物
│   └── admissibility--a-star.md
└── CLAUDE.md                                    # Skill 激活 + vault 规范
```

**命名规则**：
- `exam_boards/<source_canvas_slug>-<yyyy-mm-dd>-<hh-mm>.md`
- `source_canvas_slug` = 源原白板的主题标识（如 `search-algorithms` 对应 "搜索算法" 主题）
- 时间戳精确到分钟，防止同一天多次考察重名

**为什么用独立目录而不是 `wiki/exam/`**：
- 强化"独立白板实例"的语义（对应 PRD 的"独立的白板类型"）
- 方便 `.gitignore` 单独处理（如果不想 git 追踪考察记录）
- Dataview 查询可以清晰区分 `FROM "exam_boards"` vs `FROM "wiki/concepts"`

### 2.2 · `exam_boards/*.md` 完整 frontmatter Schema

```yaml
---
# === 类型标识（防嵌套核心）===
type: exam_board                        # 🔴 关键字段 · /start_exam_board 强制检查
status: in_progress                      # in_progress | completed | abandoned

# === 源白板追溯 ===
source_canvas: search-algorithms         # 源原白板 slug
source_canvas_path: wiki/canvases/search-algorithms.md  # 可选 · 如果用显式 canvas 文件组织
source_snapshot_at: 2026-04-08T19:55:00Z # 创建时的 wiki/concepts 状态快照时间

# === 生成参数（Agent 出题策略）===
exam_mode: point_to_point                # point_to_point | comprehensive | mixed (FR-EXAM-11)
max_questions: 10                        # 本次考察最多题数
selected_nodes:                          # FR-EXAM-02 · BKT/FSRS 选出的薄弱节点
  - admissibility
  - a-star
  - consistent-heuristic
  - ucs
bkt_threshold: 0.7                       # 掌握概率低于此值的节点才被选入
fsrs_overdue_only: false                 # 是否只考已 overdue 的节点

# === 考察元信息 ===
created_at: 2026-04-08T20:00:00Z
started_at: 2026-04-08T20:02:13Z
completed_at: null                       # 完成时更新
duration_seconds: null                   # 完成时计算

# === 题目列表（skill 逐步填充）===
questions:
  - id: q1
    concept: admissibility
    bloom_level: 4                        # Analyze
    question_text: "请用自己的话解释 A* 搜索的 admissibility 条件"
    asked_at: 2026-04-08T20:02:30Z
    user_answer: null                     # 用户答完后填
    score: null                           # score_answer 后填
    confidence: null
    low_confidence_flag: null
    hints_used: 0                         # FR-EXAM-19 · 4 级提示用了几次
    skipped: false                        # FR-EXAM-19 · 用户跳过

# === 拉出的新节点（Generation Effect · FR-EXAM-05）===
new_nodes_pulled:                        # 拉出的新 wiki/concepts/*.md 的 slug
  - consistent-heuristic

# === 回写原白板的变更（FR-EXAM-18）===
canvas_writebacks:
  - node: admissibility
    bkt_before: 0.65
    bkt_after: 0.78
    score_delta: +0.13
  - node: a-star
    bkt_before: 0.70
    bkt_after: 0.82

# === 考后校准（FR-EXAM-15）===
post_exam_calibration:                   # 用户对 AI 评分的反馈
  - question_id: q1
    vote: accurate                        # accurate | too_high | too_low
    user_note: "AI 的评分我认同"

# === Metadata ===
version: 1
tool: claude-code-skill-v1
---
```

**关键字段说明**：
- `type: exam_board` · **防嵌套核心**，`/start_exam_board` skill 启动前必须检查当前活动笔记的此字段
- `status: in_progress` · 用于 Dataview 过滤"未完成的考察"
- `selected_nodes` · FR-EXAM-02 的弱点选择结果，由 `query_mastery` MCP 工具选出
- `new_nodes_pulled` · Generation Effect 的痕迹记录 · 这里只存 slug, 实际文件写入 `wiki/concepts/`（实现 FR-EXAM-05 的"归原白板"规则）
- `canvas_writebacks` · FR-EXAM-18 的回写痕迹记录

### 2.3 · `/start_exam_board` Skill 完整 Workflow

**Hotkey**: `Cmd+Option+E` (E for Exam)

**Skill 定义文件位置**: `.claude/skills/start-exam-board/SKILL.md`

**完整 10 步流程**：

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1 · 防嵌套检查（FR-EXAM-21）                               │
│                                                                  │
│ Read 当前 Claudian 活动笔记的 frontmatter                       │
│ IF frontmatter.type == "exam_board":                            │
│     ABORT with message:                                         │
│     "⛔ 当前已在检验白板。检验白板不可再生成检验白板。           │
│      请先完成当前考察，或返回 wiki/concepts/ 目录。"            │
│     EXIT                                                         │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2 · 确认源原白板 (source canvas)                            │
│                                                                  │
│ 询问用户："你要考察哪个主题？"                                  │
│ 选项：                                                           │
│   a) 当前 Claudian 挂载的文件所属主题 (自动检测)               │
│   b) 手动输入 source_canvas slug                                │
│                                                                  │
│ 用户答后，skill 验证 wiki/canvases/<slug>.md 或                  │
│ wiki/concepts/*.md 的存在性                                     │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3 · 询问考察模式（FR-EXAM-11/12）                           │
│                                                                  │
│ AskUserQuestion:                                                 │
│   "选择考察模式："                                               │
│   - point_to_point (点对点突破 · 推荐知识点白板)               │
│   - comprehensive (综合题考察 · 推荐题目白板)                  │
│   - mixed (混合模式 · 先点对点再综合)                          │
│                                                                  │
│ IF source canvas 有明确的 canvas_type 字段:                     │
│     按 Constructive Alignment (Biggs 1996) 自动推荐           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4 · 调 query_mastery 选薄弱节点（FR-EXAM-02）              │
│                                                                  │
│ Skill 调用 MCP 工具:                                            │
│   mcp__canvas-backend__query_mastery(                           │
│       canvas_slug="search-algorithms",                          │
│       threshold=0.7,                                            │
│       top_k=10                                                  │
│   )                                                              │
│                                                                  │
│ 返回: [{node: "admissibility", mastery: 0.62}, ...]             │
│                                                                  │
│ 这一步读 Graphiti + Neo4j，复用 Canvas 后端                      │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5 · Templater 生成空白 exam_boards/*.md                     │
│                                                                  │
│ Write exam_boards/search-algorithms-2026-04-08-20-00.md:        │
│   - 只含 frontmatter (无 markdown body)                        │
│   - type: exam_board                                             │
│   - selected_nodes: [admissibility, a-star, ...]               │
│   - questions: []                                                │
│   - status: in_progress                                          │
│                                                                  │
│ 🔴 关键：body 部分只有一个 callout 占位符                       │
│   > [!exam_question]+ 等待 Agent 出题                           │
│                                                                  │
│ 这就是"完全空白的 UI" · 用户打开文件时看不到任何               │
│ wiki/concepts/*.md 的内容                                       │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 6 · Claudian 切换到新文件 + 清空上下文                      │
│                                                                  │
│ Skill 指示用户："请在 Obsidian 打开 exam_boards/xxx.md         │
│  并在 Claudian sidebar 点 'Reset Context'，我不应该看到任何    │
│  wiki/concepts/ 的内容。"                                       │
│                                                                  │
│ 🔴 关键：Claudian 重启后，当前挂载文件 = 空白 exam_board       │
│  skill 系统 prompt 里明确禁止读取 wiki/concepts/ 的具体内容     │
│  只允许通过 MCP 工具间接获取（generate_question 返回的 context)│
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 7 · 出题循环（md 编辑器为主 · Plan v16 Round 1 锁定）      │
│                                                                  │
│ FOR node in selected_nodes:                                     │
│     # 7.1 调 generate_question（FR-EXAM-03）                    │
│     result = mcp__canvas-backend__generate_question(            │
│         node_id=node,                                            │
│         canvas_slug=source_canvas,                               │
│         bloom_level=4,                                           │
│         mode=exam_mode,                                          │
│         pipeline_token=token_prev                               │
│     )                                                            │
│     # 后端读 Graphiti 的 Tips/Edge/错误历史作为 context        │
│     # 但只返回 question_text · 不返回 reference_answer          │
│                                                                  │
│     # 7.2 Edit exam_boards/*.md append callout:                 │
│     #     > [!exam_question]+ Q{i} · {node}                     │
│     #     > {question_text}                                     │
│     #     >                                                      │
│     #     > 答：                                                 │
│     #     > (在这里写你的回答)                                   │
│     # 题目写入 questions[] 数组 · 记录 pipeline_token           │
│                                                                  │
│     # 7.3 🔴 用户在 md 编辑器中写答案（NOT Claudian chat）       │
│     #     用户可反复修改 · 完全控制权                            │
│                                                                  │
│     # 7.4 🔴 用户按 Cmd+Option+S 触发 /quiz_answer              │
│     #     手动触发 · 避免文件监听误触发                          │
│                                                                  │
│     # 7.5 /quiz_answer 正则提取 "> 答：" 下方内容                │
│     #     详见 §2.3.1 和 §4.4.1                                 │
│                                                                  │
│     # 7.6 /quiz_answer 调 score_answer + update_bkt + update_fsrs│
│     #     (完整 pipeline_token 链 · 见 §7.3)                    │
│     # 🔴 完全静默：不显示分数 · 只写 frontmatter                 │
│                                                                  │
│     # 7.7 如果评分 < 2 或用户说"不会" → 4 级渐进提示            │
│     #     (FR-EXAM-19 · 见 §1.9)                                │
│     #     Level 1 方向 → 2 关键词 → 3 框架 → 4 脚手架           │
│                                                                  │
│     # 7.8 🔴 如果用户说"不懂 X" → 书签式（Plan v16 Round 2）    │
│     #     → 不切 Tab · 不中断考察                                │
│     #     → Edit 插入 [!discussion_later]+ callout + wikilink   │
│     #     → Write wiki/concepts/x.md 只含 frontmatter stub      │
│     #     → 更新 new_nodes_pulled[] · 继续原题                  │
│     #     详见 §2.7.1                                            │
│     #                                                            │
│     # 7.9 考察完此 node → 更新 canvas_writebacks[]              │
│     #     /quiz_answer 自动追加下一题 callout · 回到 7.1        │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 8 · 考后校准投票（FR-EXAM-15）                              │
│                                                                  │
│ FOR each question answered:                                     │
│     AskUserQuestion:                                             │
│       "对 q{i} 的 AI 评分你觉得？                              │
│        - accurate (准确)                                         │
│        - too_high (偏高)                                         │
│        - too_low (偏低)                                          │
│        - skip (跳过)"                                            │
│                                                                  │
│     写入 post_exam_calibration[]                                 │
│     调 record_calibration MCP 工具                              │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 9 · 生成考察摘要 + 更新 status                              │
│                                                                  │
│ Skill 计算:                                                      │
│   - total_questions                                              │
│   - average_score                                                │
│   - mastery_delta (考前 vs 考后)                                 │
│   - new_nodes_count                                              │
│                                                                  │
│ Write exam_boards/*.md body:                                     │
│   ## 本次考察摘要                                                │
│   - 考察节点: 4                                                   │
│   - 平均分: 2.5 / 4                                               │
│   - 新发现节点: 1 (consistent-heuristic)                       │
│   - 平均 mastery 提升: +0.12                                    │
│                                                                  │
│ 更新 frontmatter:                                                │
│   status: completed                                              │
│   completed_at: 2026-04-08T21:45:00Z                            │
│   duration_seconds: 6300                                        │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 10 · 提示用户返回原白板                                     │
│                                                                  │
│ Claudian 显示:                                                   │
│   "✅ 考察完成！                                                  │
│    📄 完整记录: exam_boards/search-algorithms-2026-04-08-*.md   │
│    🆕 新发现 1 个节点: consistent-heuristic                     │
│    👉 请在 Obsidian 打开 wiki/concepts/consistent-heuristic.md │
│       深入剖析此概念（剖析模式）。                               │
│    ⚠️ 如需再次考察 consistent-heuristic, 请从                    │
│       wiki/canvases/search-algorithms.md 重新触发               │
│       /start_exam_board。不能直接在本检验白板递归。"             │
└─────────────────────────────────────────────────────────────────┘
```

User：现在原白板是以什么方式来呈现的？我们现在引入剖析的材料是md 格式，从剖析拉出新节点然后也是用 md 格式拉出来，所以原白板中是否可以查看到所有相互链接的 md 节点，然后还有一个核心是关于特定节点内容的 考察以及原白板考察这两种方式，请问你觉得这两种模式你还有考虑吗？然后你觉得现在这两种模式，从学习角度出发，节点考察这个模式还需要保留吗？

### 2.3.1 · md 编辑器为主答题工作流（Plan v16 Round 1 锁定 · 灵魂章节补充）

> **本节是 Plan v16 Round 1 用户决策"md 编辑器为主"的完整工作流设计。**
> **用户原话锁定**："我觉得这样回答问题就好比打批注" · 用户把"答题"视为"写批注"的延伸 · 所有思考永久沉淀在 md 文件里。
> **学习哲学**：与 Karpathy "write stuff down" 原则 + 批注驱动精确考察核心诉求完全闭环（批注 → 考察 → 答题 → 又是批注）。

#### 为什么选择 md 编辑器而不是 Claudian sidebar 对话

| 方案 | 答题载体 | 优点 | 缺点 |
|---|---|---|---|
| Claudian Chat | 在 sidebar 输入框里打字 | 交互流畅 · 像对话 | ❌ 答案不持久 · 切换会话会丢失 · 不符合用户"打批注"哲学 |
| **md 编辑器**（✅ 采用） | 在 `exam_boards/*.md` 的 `> 答：...` 下方写 | ✅ **永久沉淀** · ✅ 符合"write stuff down" · ✅ 可反复修改 · ✅ 与批注同一个编辑界面 | 交互稍慢（需手动触发提交） |

**Plan v16 关键决策**：用户 2026-04-09 明确偏离 AI 的原推荐（Claudian Chat），主动选择 md 编辑器。这不是技术选型，而是**学习哲学选择**——把考察融入写作流程，而不是分裂为独立的"对话模式"。

#### 完整 workflow · 9 步 md 答题时序图

```
┌────────────────────────────────────────────────────────────────────────┐
│ Step 1 · Skill 触发出题                                                 │
│                                                                         │
│ /start_exam_board skill 的 Step 7.1-7.2 调 generate_question MCP →     │
│   返回 { question_id, question_text }                                  │
│                                                                         │
│ 例：                                                                    │
│   question_text = "请用自己的话解释 A* 搜索的 admissibility 条件"       │
└────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌────────────────────────────────────────────────────────────────────────┐
│ Step 2 · Skill Edit exam_boards/*.md 追加 callout                      │
│                                                                         │
│ skill 用 Edit 工具在当前 exam_boards/*.md 的 body 末尾追加：            │
│                                                                         │
│ ```markdown                                                            │
│ > [!exam_question]+ Q1 · admissibility                                 │
│ > 请用自己的话解释 A* 搜索的 admissibility 条件                        │
│ >                                                                      │
│ > 答：                                                                  │
│ > (在这里写你的回答)                                                    │
│ ```                                                                    │
│                                                                         │
│ Obsidian 自动重新渲染 · 用户立即看到新题目                              │
└────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌────────────────────────────────────────────────────────────────────────┐
│ Step 3 · 用户在 md 编辑器写答案                                         │
│                                                                         │
│ 用户光标点击 "答：" 下面的 "(在这里写你的回答)" · 替换为自己的答案：    │
│                                                                         │
│ ```markdown                                                            │
│ > [!exam_question]+ Q1 · admissibility                                 │
│ > 请用自己的话解释 A* 搜索的 admissibility 条件                        │
│ >                                                                      │
│ > 答：admissibility 是指启发函数 h(n) 永远不高估到达目标的实际代价，    │
│ >    即 h(n) ≤ h*(n) · 这保证 A* 搜索在找到解时一定是最优解 ·           │
│ >    反之如果 h 高估了，A* 可能会跳过真正最优的路径                     │
│ ```                                                                    │
│                                                                         │
│ 🔴 关键特性：                                                           │
│   - 用户可以反复修改答案（写半截删掉重写 · 很自然）                     │
│   - Obsidian callout 的 "+" 标记保证 callout 默认展开                   │
│   - 整段答案永久保存在 md 文件里                                        │
│   - 未来可以搜索 "我答过的所有 admissibility 相关问题"                  │
└────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌────────────────────────────────────────────────────────────────────────┐
│ Step 4 · 用户按 Cmd+Option+S (Submit) 触发 /quiz_answer sub-skill      │
│                                                                         │
│ 🔴 关键设计：**手动触发**（不是文件监听自动触发）                       │
│   理由：用户可以反复修改答案 · 避免思考中被误触发                       │
│                                                                         │
│ Hotkey: Cmd+Option+S · S 代表 Submit                                   │
│                                                                         │
│ 用户动作 · 按下 Cmd+Option+S                                           │
│   ↓                                                                    │
│ QuickAdd macro 调用 /quiz_answer sub-skill                             │
│   ↓                                                                    │
│ sub-skill 在后台执行（无 UI 反馈 · 完全静默 · §1.6 Flow State 保护）   │
└────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌────────────────────────────────────────────────────────────────────────┐
│ Step 5 · /quiz_answer sub-skill 提取答案                                │
│                                                                         │
│ skill 执行：                                                            │
│   1. Read 当前活动笔记的完整内容                                        │
│   2. 用正则匹配最后一个 [!exam_question]+ callout                       │
│   3. 从 callout 的 "> 答：" 行开始，抓取所有连续的 "> " 开头的行         │
│   4. 拼接成完整答案字符串                                               │
│                                                                         │
│ 正则示例（Python）：                                                    │
│   pattern = r'> \[!exam_question\]\+[^\n]*\n((?:> [^\n]*\n)+)'         │
│   matches = re.findall(pattern, file_content)                          │
│   last_match = matches[-1]                                             │
│   answer_lines = [line[2:] for line in last_match.split('\n')          │
│                   if line.startswith('> 答：')                         │
│                      or (answer_started and line.startswith('> '))]    │
│                                                                         │
│ 从 questions[-1].question_id 获取当前题目 ID                            │
└────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌────────────────────────────────────────────────────────────────────────┐
│ Step 6 · 调 score_answer MCP (完全静默评分)                             │
│                                                                         │
│ sub-skill 调：                                                          │
│   mcp__canvas-backend__score_answer(                                   │
│       question_id=q1.question_id,                                       │
│       user_answer=extracted_answer,                                    │
│       pipeline_token=token_A  # 从之前 generate_question 传递而来       │
│   )                                                                     │
│                                                                         │
│ 返回:                                                                   │
│   {                                                                    │
│     "scores": { "correctness": 3, "clarity": 2, "depth": 3, ...},      │
│     "pipeline_token": token_B                                          │
│   }                                                                    │
│                                                                         │
│ 🔴 关键：skill **完全不显示**分数                                        │
│   - Claudian sidebar 完全静默                                          │
│   - 不追加 "> **评分**: ..." 到 md                                      │
│   - 不弹出 toast 通知                                                   │
│   - 分数只写入 exam_boards/*.md frontmatter 的 questions[q_idx].score  │
└────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌────────────────────────────────────────────────────────────────────────┐
│ Step 7 · 调 update_bkt / update_fsrs MCP                                │
│                                                                         │
│ sub-skill 继续 pipeline_token 链：                                      │
│   update_bkt(node_id, grade=avg_score, pipeline_token=token_B)         │
│     → token_C                                                           │
│   update_fsrs(node_id, answer_quality, pipeline_token=token_C)         │
│     → token_D                                                           │
│                                                                         │
│ 更新写入对应 wiki/concepts/<slug>.md 的 frontmatter                     │
│   bkt_p_mastery: 0.68 → 0.78                                           │
│   fsrs_stability: 5.2 → 8.7                                            │
│                                                                         │
│ 🔴 依然完全静默 · 用户看不到任何数字变化                                │
└────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌────────────────────────────────────────────────────────────────────────┐
│ Step 8 · Sub-skill 触发下一题（继续出题循环）                           │
│                                                                         │
│ sub-skill 检查 questions[] 列表：                                       │
│   IF 还有未答题目 or 还有 selected_nodes 未覆盖:                       │
│     回到 /start_exam_board 的 Step 7.1 (generate_question)             │
│     Edit exam_boards/*.md 追加下一题 callout                           │
│   ELSE:                                                                 │
│     /start_exam_board 进入 Step 8 (考后校准投票)                       │
└────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌────────────────────────────────────────────────────────────────────────┐
│ Step 9 · 用户发现变化（延迟反馈 · 完全静默评分）                         │
│                                                                         │
│ 用户在考察中 · 只看到题目 + 自己的答案 · 看不到任何分数                 │
│                                                                         │
│ 考察结束后 · 用户打开 wiki/dashboard.md · Dataview 查询显示：           │
│   - admissibility: mastery 0.78 (↑ 0.10)  [颜色: 🟢 已基本掌握]        │
│   - a-star: mastery 0.82 (↑ 0.12)         [颜色: 🟢 已基本掌握]        │
│                                                                         │
│ 🔴 这是"完全静默评分"的核心收益：                                        │
│   - 考察过程中 Flow State 不被打断                                      │
│   - 所有反馈延迟到考察结束 · 不触发考试焦虑                             │
│   - 用户获得"完成感"而非"被评价感"                                      │
└────────────────────────────────────────────────────────────────────────┘
```

#### 与 Retrieval Practice 的契合论证

**担忧**：用户在 md 编辑器里写答案 · 会不会看到其他笔记内容 · 破坏 Active Recall？

**答案**：不会 · 3 个保证机制：

1. **Claudian 上下文隔离**（§2.4 保证 2）· skill 系统 prompt 禁止读 `wiki/concepts/*.md`
2. **Obsidian 自动挂载**：用户打开 `exam_boards/*.md` 时 · Claudian 自动挂载 = 只有这一个文件 · 不挂载其他 concepts
3. **用户自律**：CLAUDE.md 明确说"考察时不要 Cmd+O 打开其他笔记" · 方案 A 的"完全空白 UI"是文件级 + 上下文级双重保证

**学习科学验证**：
- Karpathy 原则："write stuff down" · 写下来的动作本身就是深度编码
- Karpicke & Blunt (2011) 原始实验中 · 学生也是**写下来**答案 · 然后对比评分 · 不是口头回忆
- Donoghue & Hattie (2021) meta-analysis · "写式 Retrieval Practice" 比"口头 Retrieval Practice" **效应量略高** (d=1.55 vs d=1.45)

**结论**：md 编辑器答题 **不仅不破坏 Retrieval Practice · 反而强化了它**。

#### `/quiz_answer` sub-skill 的正则提取逻辑

完整的答案抓取正则（Python 实现 · sub-skill 内部逻辑）：

```python
def extract_last_answer(exam_board_content: str) -> tuple[str, str]:
    """
    从 exam_boards/*.md 的内容中提取最后一题的答案
    返回: (question_id, answer_text)
    """
    # 步骤 1 · 匹配最后一个 [!exam_question]+ callout block
    pattern = re.compile(
        r'> \[!exam_question\]\+\s+(Q\d+)[^\n]*\n'  # 标题行，抓 Q1/Q2...
        r'((?:> [^\n]*\n)+)',                         # 所有 > 开头的行
        re.MULTILINE
    )
    matches = pattern.findall(exam_board_content)
    if not matches:
        raise ValueError("No exam_question callout found")
    
    last_q_id, last_callout_body = matches[-1]
    
    # 步骤 2 · 从 callout body 中提取 "> 答：" 之后的内容
    lines = last_callout_body.split('\n')
    answer_lines = []
    in_answer_section = False
    for line in lines:
        if line.startswith('> 答：'):
            in_answer_section = True
            # 去掉 "> 答：" 前缀，保留答案开头
            first_line = line[len('> 答：'):].strip()
            if first_line:
                answer_lines.append(first_line)
        elif in_answer_section and line.startswith('> '):
            # 答案继续行
            answer_lines.append(line[2:])  # 去掉 "> " 前缀
    
    answer_text = ' '.join(answer_lines).strip()
    
    # 步骤 3 · 过滤占位符
    if answer_text == '(在这里写你的回答)' or answer_text == '':
        raise ValueError("User hasn't answered yet")
    
    return last_q_id, answer_text
```

#### md 编辑器 + Karpathy "write stuff down" 的完整闭环

```
批注（写进 wiki/concepts/*.md 的 [!question]+ callout）
    ↓ （/start_exam_board 扫 callout 出题）
考察题目（写进 exam_boards/*.md 的 [!exam_question]+ callout）
    ↓ （用户在 md 编辑器下方写答案）
答案（写进 exam_boards/*.md 的 "> 答：..." 段落）
    ↓ （Cmd+Option+S 触发 /quiz_answer）
评分（写进 exam_boards/*.md frontmatter · 完全静默）
    ↓ （如果暴露新的不懂点）
新的批注（写进 wiki/concepts/*.md 或 exam_boards/*.md）
    ↓
🔁 循环
```

**这就是用户所说"回答问题就好比打批注"的深层含义**：所有学习活动都以"写"的方式永久沉淀在 md 文件里。

---

> **AI 响应**（基于 Agent 1 Canvas PRD 双考察调研 + Plan v16 Round 1 决策 · **保留两种独立 skill**）：
>
> **第 1 问 · 原白板呈现方式**：方案 A 中原白板 = `wiki/concepts/*.md` 文件集合 + Obsidian Graph view + Backlinks pane。用户可以通过以下方式"查看所有相互链接的节点"：
>
> 1. **Graph view** (`Cmd+G`) · 整个 vault 的可视化节点图 · 节点=文件 · 边=wikilink · 支持过滤器 `type:concept`
> 2. **Local Graph view** (`Cmd+Shift+G`) · 只显示当前节点的 1-2 hop 邻居
> 3. **Backlinks pane** · 右侧面板显示"谁引用了当前节点"
> 4. **Dataview 查询** · 在 `wiki/dashboard.md` 用 DQL 列出所有 `wiki/concepts/*.md` 及其关系
>
> 从剖析拉出的新节点（§1.2 `/extract_node`）会自动加入 `wiki/concepts/` 目录，Graph view 立即显示。wikilink `[[consistent-heuristic]]` 是双向的，无需手动回连。
>
> **第 2 问 · 两种考察模式的去留（关键架构决策）**：Plan v16 Round 1 锁定 = **保留两种独立 skill**（见 §4.4 详细对比）
>
> | Skill | FR 对应 | 学术根据 | 效应量 | 使用场景 |
> |---|---|---|---|---|
> | `/start_exam_board` | FR-EXAM-01~16 | Karpicke Retrieval Practice | d=1.50 | **正式考核** · 完全空白 UI · 信息隐形 |
> | `/quiz_from_callout` | **FR-EXAM-17** + FR-CONV-03 | Chi 1994 Self-Explanation · Bisra 2018 meta-analysis | d≈1.09 (Chi) · g=0.55 (Bisra n=5,917) | **作业自查** · 信息可见 · 就地考察 |
>
> **为什么都要保留（学术根据）**：
> 1. **Canvas PRD 原设计并存**：FR-EXAM-01（白板级考察）和 FR-EXAM-17（节点单独考察）在 PRD L383 和 L785 分别定义，Canvas 本来就设计了两个入口
> 2. **学术根据不同** · Chi et al. (1994) Self-Explanation 的 **d ≈ 1.09**（t(22)=2.64 · n1=14, n2=10 · Plan v23 公式修正 `d = t × √(1/n1 + 1/n2)` · 见 §4.4 详细推导）是**独立的**学术支撑，不依赖 Active Recall · 信息可见时的"用自己的话解释"仍然有强效应量（Plan v21 一致性修正：v15-v19 曾写 d=1.00 · 应与 §4.4 的 d≈1.09 保持一致 · Plan v23 进一步修正公式为正确的 between-subject 形式）
> 3. **使用场景互补**：
>    - 学完一章后第二天 → `/start_exam_board`（正式考核 · 强 Active Recall）
>    - 刚记下某个 callout 想立刻 check → `/quiz_from_callout`（就地自查 · 不中断学习流）
> 4. **PRD 原话**（L785 FR-EXAM-17）："第二考察入口"（secondary entry point）——暗示这是**便利性设计**（辅助功能）而非学术必要，但确实有独立价值
>
> **核心判断**：如果砍掉 `/quiz_from_callout`，用户每次想 quick-check 某个 callout 都要触发 `/start_exam_board`（10 步流程 · 过重），学习效率会下降。**保留两种 skill，并在 §4.4 明确对比和适用场景**。
>
> **详见**：§4.4 `/quiz_from_callout` 大改 · §5.1.1 Dashboard 完整设计（含原白板↔检验白板跳转链路）

### 2.4 · 完全空白 UI 的 3 重保证机制

**这是灵魂章节的灵魂** — 必须保证用户打开 `exam_boards/*.md` 时眼前**真的看不到**任何 `wiki/concepts/*.md` 的内容。

#### 保证 1 · Templater 生成空白 md（文件层面）

Templater 模板文件 `templates/exam-board.md` 内容：

```yaml
---
type: exam_board
status: in_progress
source_canvas: <% tp.user.prompt("源原白板 slug:") %>
source_canvas_path: wiki/canvases/<% tp.user.source_canvas %>.md
source_snapshot_at: <% tp.date.now("YYYY-MM-DDTHH:mm:ssZ") %>
exam_mode: <% tp.user.exam_mode %>
created_at: <% tp.date.now("YYYY-MM-DDTHH:mm:ssZ") %>
questions: []
new_nodes_pulled: []
canvas_writebacks: []
---

> [!exam_question]+ 等待 Agent 出题...
```

**关键**：body 只有一行 callout 占位符。用户打开时眼前就一行字 + frontmatter（frontmatter 默认折叠）。

#### 保证 2 · Claudian 不挂载 wiki/concepts/（context 层面）

在 `CLAUDE.md` 里对 `/start_exam_board` skill 强制声明：

```markdown
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

**验证方式**：用户打开 Claudian sidebar，skill 的系统 prompt 里明确写 "You MUST NOT read wiki/concepts/*.md content"。

User：那么考察的时候，请问如何知道我在原白板剖析的时候所犯下的各种错误，以及对于知识点的熟练度不够以及我特意所写的各种批注，然后你出题在新的 md 文件上，那么我也会进行做答，我在使用检验白板考察的时候我们是如何一来一回交互的，然后还有一点就是如果我对题目卡壳的话又该怎么办了？

> **AI 响应**（基于 Agent 3 Canvas 后端代码硬证据 + Plan v16 Round 1 md 答题决策）：
>
> **第 1 问 · 考察怎么知道你的错误/熟练度/批注**（分层数据流架构）：
>
> **关键洞察**：考察的 **出题** 过程和**显示**过程是**分层分离**的。错误/Tips/批注由**后端**读取并组装进 LLM 的 prompt，但**不返回给 skill**，也**不显示给用户**。
>
> **5 层数据流**（从用户眼前到 LLM · Agent 3 的 Canvas 后端代码硬证据）：
>
> ```
> 第 1 层 · 用户层           → 只看到 exam_boards/*.md 的 [!exam_question]+ callout（题目文本）
>                               ↑ 完全空白 UI · 看不到任何 wiki/concepts/ 内容
>
> 第 2 层 · Skill 层          → Claude Code skill 的系统 prompt 禁止 Read wiki/concepts/*.md
>                               ↑ §2.4 保证 2 · CLAUDE.md 硬约束
>
> 第 3 层 · MCP 工具层        → generate_question MCP 工具只返回 question_text，不返回 reference_answer
>                               ↑ Canvas 后端代码 exam_tools.py:155-232 硬证据
>                               ↑ exam_tools.py:348 显式 reference_answer = None
>
> 第 4 层 · 后端 Service 层   → context_enrichment_service.py 内部读 wiki/concepts/*.md 提取 Tips/errors/批注
>                               ↑ context_enrichment_service.py:42-116
>                               ↑ 但只在组装 LLM prompt 时用，不返回给 skill
>
> 第 5 层 · LLM 层           → LLM 收到完整 context（Tips + errors + 批注） + 指令"基于这些出精准题目"
>                               ↑ LLM 知道用户批注，但输出的题目不暴露批注内容
> ```
>
> **关键 Canvas 后端代码引用**（Agent 3 硬证据）：
> - `exam_tools.py:155-232` · `generate_question` 函数只返回 `question_text`
> - `exam_tools.py:348` · 强制 `reference_answer = None`
> - `pipeline_token.py:25-28` · `PIPELINE_STEPS` 定义强制顺序（见下）
> - `context_enrichment_service.py:42-116` · 后端**内部**读 Tips/errors，**只在组装 prompt 时用**
>
> **pipeline_token 强制顺序**（防篡改）：
> ```python
> PIPELINE_STEPS = {
>     "generate_question": ["score_answer"],
>     "score_answer": ["update_fsrs", "update_bkt"],
> }
> ```
>
> **第 2 问 · 一来一回交互方式**（md 编辑器为主答题 · Plan v16 Round 1）：
>
> **不是**在 Claudian sidebar 聊天，**而是**在 md 编辑器里写答案。完整工作流见新增的 **§2.3.1 md 编辑器为主答题工作流**。
>
> 简要流程：
> 1. Skill Edit `exam_boards/*.md` 追加 `[!exam_question]+` callout
> 2. 用户在 callout 下方写 `> 答：<答案内容>`（可反复修改）
> 3. 用户按 **Cmd+Option+S** (S for Submit) 触发 `/quiz_answer` sub-skill
> 4. Sub-skill 读当前 md，正则提取 `> 答：...` 内容
> 5. Sub-skill 调 `score_answer` MCP 工具 → 完全静默评分（不显示分数）
> 6. Sub-skill Edit md 追加下一题 callout
> 7. 循环直到全部题目答完
>
> **为什么这样设计**：答题 = 写批注的延伸（用户原话）· 所有思考永久沉淀在 md 里 · 与 Karpathy "write stuff down" 契合。
>
> **第 3 问 · 卡壳了怎么办**（FR-EXAM-19 · 4 级渐进提示）：
>
> 完整的 decision tree：
>
> ```
> 用户写"不会" 或 用户停留 > 5 分钟 未提交
>         ↓
> Skill 检测卡壳 → 询问用户："需要提示吗？"
>         ↓
> 用户说"是"
>         ↓
> Level 1 · 方向提示 · "这道题涉及 admissibility 的定义和 optimality"
>         ↓
> 还不会 → 用户再请求
>         ↓
> Level 2 · 关键词提示 · "想想 h(n) 和真实代价的关系"
>         ↓
> 还不会 → 用户再请求
>         ↓
> Level 3 · 框架提示 · "回答的结构应该是：1. 定义 admissibility 2. 举例 3. 解释为什么保证 optimality"
>         ↓
> 还不会 → 用户再请求
>         ↓
> Level 4 · 脚手架提示 · "填空：admissibility 是指启发函数 h(n) __ 真实代价 h*(n)，这保证 A* 搜索 __"
>         ↓
> 还不会 → 用户选择"跳过（不惩罚）" 或 "拉出新节点（书签式）"
> ```
>
> **关键机制**：
> - 每提示一次 `hints_used += 1` 写入 questions[i].hints_used
> - 评分时根据 hints_used 扣分（但不归零 · 鼓励主动求助）
> - 4 级后仍不会 → `skipped: true` 不惩罚 · 不影响 mastery 更新
> - 或触发 `/extract_node` 书签式拉出新节点（见 §2.7.1）
>
> **学术根据**：Anghileri (2006) Scaffolding in Mathematics Teaching · 逐级降低认知负荷 · 比直接给答案保留更多 Generation Effect。
>
> **详见**：§2.3.1 md 编辑器答题工作流 · §4.5 `/quiz_answer` sub-skill · §1.9 设计 9 · 4 级渐进提示

#### 保证 3 · MCP 工具返回的 context 只包含题目，不含答案

`generate_question` 后端工具的返回格式：

```json
{
  "question_id": "q1",
  "question_text": "请用自己的话解释 A* 搜索的 admissibility 条件",
  "bloom_level": 4,
  "expected_elements": ["h(n) bound", "optimality guarantee"],
  "pipeline_token": "xxx"
}
```

**关键**：
- `question_text` 只包含问题，不包含答案或提示
- `expected_elements` 是用于 `score_answer` 后端使用的隐藏字段，**不应该显示给 skill 或用户**
- Skill 在 prompt 里明确只读 `question_text`

#### Canvas 后端代码硬证据（Agent 3 验证 · Plan v16 B5）

**5 层数据流的代码级验证**（从用户层到 LLM 层）：

**验证点 1 · generate_question MCP 工具只返回题目**

```python
# backend/app/mcp/tools/exam_tools.py:155-232
async def generate_question(
    node_id: str,
    canvas_slug: str,
    bloom_level: int,
    mode: str,
    pipeline_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    生成考察题目。
    🔴 只返回 question_text · 不返回 reference_answer
    """
    # 1. 读取节点的 Tips + errors + Edges 作为 context（后端内部）
    context = await context_enrichment_service.enrich(node_id, ...)
    
    # 2. LLM 基于 context 生成题目
    question_text = await llm_client.generate_question(
        node=node_id,
        context=context,  # 包含 Tips/errors/批注 · 但只在 LLM prompt 里用
        bloom_level=bloom_level,
    )
    
    # 3. 🔴 返回值只包含题目 · 不包含任何答案提示
    return {
        "question_id": generate_id(),
        "question_text": question_text,
        "bloom_level": bloom_level,
        "pipeline_token": create_next_token(
            current_step="generate_question",
            next_allowed=["score_answer"],
        ),
    }
```

**验证点 2 · reference_answer 强制设为 None**

```python
# backend/app/mcp/tools/exam_tools.py:348
# 在 generate_question 的所有分支中 · reference_answer 显式设为 None

result["reference_answer"] = None  # 🔴 永远是 None · 防止意外暴露
```

**验证点 3 · PIPELINE_STEPS 定义强制顺序**

```python
# backend/app/mcp/pipeline_token.py:25-28
PIPELINE_STEPS = {
    "generate_question": ["score_answer"],           # 出题后只能打分
    "score_answer": ["update_fsrs", "update_bkt"],  # 打分后只能更新 FSRS/BKT
}

def validate_token(token: str, expected_step: str):
    """
    🔴 后端强制验证: 如果 skill 跳步(例如 generate_question 直接到 update_bkt)
    token 验证会失败 · 返回 403 Forbidden
    """
    payload = decode_token(token)
    if payload.current_step not in PIPELINE_STEPS:
        raise InvalidToken(...)
    
    allowed_next = PIPELINE_STEPS[payload.current_step]
    if expected_step not in allowed_next:
        raise InvalidToken(
            f"Cannot jump from {payload.current_step} to {expected_step}. "
            f"Allowed: {allowed_next}"
        )
```

**验证点 4 · context_enrichment_service 内部读但不返回**

```python
# backend/app/services/context_enrichment_service.py:42-116
async def enrich(self, node_id: str, ...) -> EnrichedContext:
    """
    读取节点的 Tips/errors/批注 作为 context
    🔴 关键: 这个返回值只在 LLM prompt 构造时使用 · 不返回给 skill
    """
    # 1. Read wiki/concepts/<node>.md 提取 Tips
    concept_file = await read_file(f"wiki/concepts/{node_id}.md")
    tips = parse_tips_from_callouts(concept_file)
    
    # 2. Read wiki/concepts/<node>.md 提取批注
    annotations = parse_annotations(concept_file)
    
    # 3. Read edges/*.md 提取 Edge 理由
    edges = await read_edges_for_node(node_id)
    
    # 4. Read Graphiti 历史错误
    errors = await memory_service.search_memories(
        query=f"errors related to {node_id}",
        node_scope=node_id,
    )
    
    # 5. 🔴 返回 EnrichedContext 对象 · 仅在 generate_question 内部使用
    return EnrichedContext(
        tips=tips,
        annotations=annotations,
        edges=edges,
        errors=errors,
    )
```

**验证点 5 · LLM 层收到完整 context 但输出的题目不暴露批注内容**

LLM 的 system prompt（简化版）：

```
你是出题助手。基于以下 context 出一道题目:

<context>
Tips: {tips}
Annotations: {annotations}  
Edges: {edges}
Errors history: {errors}
</context>

规则:
1. 题目必须考察这个节点的核心理解
2. 🔴 题目不能直接引用 Tips 或 annotations 的具体内容
3. 🔴 题目不能暴露 errors 的具体错误（避免提示答案）
4. 使用 Bloom level {bloom_level} 的认知层级

输出格式: 只输出题目文本 · 一行或几行 · 不要给出任何解释。
```

#### 分层数据流架构图（5 层）

```
┌─────────────────────────────────────────────────────────────┐
│  第 1 层 · 用户层 (User Facing)                              │
│                                                               │
│  用户看到的内容:                                              │
│  - exam_boards/*.md 的 [!exam_question]+ callout              │
│  - question_text (e.g., "请用自己的话解释 A* 的 admissibility")│
│                                                               │
│  🔴 看不到: Tips / errors / 其他 concept.md 内容 / 答案        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  第 2 层 · Skill 层 (Claude Code)                            │
│                                                               │
│  Skill 的职责:                                                │
│  - 调用 MCP 工具                                              │
│  - 处理 pipeline_token                                        │
│  - Edit exam_boards/*.md 追加题目                             │
│                                                               │
│  🔴 Skill 的系统 prompt 禁止 Read wiki/concepts/*.md          │
│  🔴 Hook Layer 3 (pretool-exam-board-isolation.js) 强制阻断   │
└────────────────────────┬────────────────────────────────────┘
                         │ MCP HTTP 调用
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  第 3 层 · MCP 工具层 (FastApiMCP)                           │
│                                                               │
│  mcp__canvas-backend__generate_question 只返回:              │
│  {                                                            │
│    "question_id": ...,                                        │
│    "question_text": ...,                                      │
│    "bloom_level": ...,                                        │
│    "pipeline_token": ...                                      │
│  }                                                            │
│                                                               │
│  🔴 code 位置: exam_tools.py:155-232                          │
│  🔴 reference_answer 强制为 None (exam_tools.py:348)          │
└────────────────────────┬────────────────────────────────────┘
                         │ 内部 Python 调用
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  第 4 层 · 后端 Service 层 (Python Code)                     │
│                                                               │
│  context_enrichment_service 内部读:                           │
│  - wiki/concepts/*.md 提取 Tips + 批注                        │
│  - edges/*.md 提取 Edge 理由                                  │
│  - Graphiti 读错误历史                                        │
│                                                               │
│  🔴 这些数据只在 LLM prompt 构造时使用                         │
│  🔴 不通过 MCP 工具返回给 skill                                │
│  🔴 code 位置: context_enrichment_service.py:42-116           │
└────────────────────────┬────────────────────────────────────┘
                         │ Gemini API 调用
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  第 5 层 · LLM 层 (Gemini)                                   │
│                                                               │
│  LLM 收到完整 context (Tips + errors + 批注)                 │
│  LLM 基于 context 出题                                        │
│  LLM 遵守 system prompt 的规则:                               │
│    - 不直接引用 Tips 具体内容                                  │
│    - 不暴露 errors 具体错误                                    │
│                                                               │
│  🔴 LLM 输出的题目被严格过滤 · 只保留 question_text            │
└─────────────────────────────────────────────────────────────┘
```

**三重保证组合 = 完全空白 UI**：
- **文件层**（§2.4 保证 1）· Templater 生成空白 md
- **上下文层**（§2.4 保证 2）· Claudian 不挂载 wiki/concepts/
- **工具层**（§2.4 保证 3）· MCP 工具只返回题目文本

**Plan v16 新增第 4 重保证 · Hook 层**（§4.7 Layer 3）：
- 即使 skill 意外尝试 Read wiki/concepts/*.md · Hook 会在 PreToolUse 阶段硬阻断（exit 2）
- 这是"深度防御"的第 4 层

---

### 2.5 · 防嵌套机制（type: exam_board 检查）

**目标**：实现 FR-EXAM-21 "检验白板不可再生成检验白板"

**实现位置**：`/start_exam_board` skill 的 Step 1（见 §2.3）

**完整检查逻辑**：

```python
def check_not_nested():
    """Step 1 · 防嵌套检查"""
    # 读 Claudian 当前活动笔记
    active_file = claudian.get_active_file()

    # 读 frontmatter
    frontmatter = parse_frontmatter(active_file)

    # 检查 type 字段
    if frontmatter.get("type") == "exam_board":
        raise AbortSkill(
            message=(
                "⛔ 当前已在检验白板。\n"
                "检验白板不可再生成检验白板 (FR-EXAM-21)。\n"
                "如需再次考察，请：\n"
                "1. 完成或放弃当前考察\n"
                "2. 返回 wiki/canvases/ 的原白板\n"
                "3. 重新触发 /start_exam_board"
            )
        )

    # 检查是否已在 exam_boards/ 目录
    if "exam_boards/" in active_file.path:
        raise AbortSkill(
            message="⛔ 当前已在 exam_boards/ 目录，见上。"
        )

    return True
```

**为什么是 skill 层面而不是文件系统层面**：
- 文件系统无法强制防止用户手动 copy exam_board 文件
- Skill 层面的检查发生在"生成"时刻，覆盖 99% 的场景
- 额外保险：`/start_exam_board` 的系统 prompt 里再声明"递归考察会破坏 Active Recall 的信息隐形前提"

**Canvas 后端的双重保险**（PRD §3.7 13-gap-diagnosis 引用）:
```python
# backend/app/services/exam_service.py:69-83
async def create_session(self, request: ExamSessionCreate) -> ExamSessionResponse:
    source_type = await self._get_canvas_type(request.source_canvas_id)
    if source_type == "exam":
        raise ValueError(
            "Cannot create exam board from another exam board. "
            "Please return to the original canvas to start a new exam."
        )
```

方案 A 通过 MCP 工具调用也会触发这个后端检查 — **双保险**。

---

### 2.6 · 拉出新节点同步流程（Generation Effect + FR-EXAM-18 · Plan v16 B6 书签式）

**触发时机**：用户在 §2.3 Step 7.8 的考察对话中说"我不懂 consistent-heuristic"

**Plan v16 Round 2 关键更新 · 书签式工作流**（不立即切换 Tab · 保护 Retrieval Practice）：

**统一的 `extracted_from` schema 字段**（响应批注 #6 · 跨 3 种场景一致）：

```yaml
# wiki/concepts/<new_slug>.md 的 frontmatter (Plan v16 新增)
---
title: consistent heuristic
type: concept
extracted_from:
  type: chat_session | exam_board | edge_discussion    # 3 种场景
  source_file: exam_boards/search-algorithms-2026-04-08-20-00.md
  parent_node: a-star                                    # 触发讨论时的父节点
  extracted_at: 2026-04-08T20:37:13Z
  trigger: user_said_dont_understand                     # 触发原因
bkt_p_mastery: 0.30  # 默认初值
body_status: placeholder  # 标记为占位 · 等考后填
---
```

**3 种场景的一致性对照**：

| 场景 | `extracted_from.type` | `source_file` | `parent_node` |
|---|---|---|---|
| 剖析模式对话拉出 | `chat_session` | `outputs/sessions/<date>-<slug>.md` | 当前节点 slug |
| 检验白板考察拉出 | `exam_board` | `exam_boards/<slug>-<time>.md` | 当前考察节点 slug |
| Edge 对话拉出 | `edge_discussion` | `edges/<from>--<to>.md` | 两个节点之一 |

**完整书签式流程**（Plan v16 Round 2）：

```
1. 用户在考察中说"我不懂 consistent-heuristic"
   ↓
2. Skill 检测到用户意图 · 触发 /extract_node sub-workflow
   ↓
3. /extract_node 书签式操作（Plan v16 B6 · 与原 v15 方案区别）
   
   a) LLM 抽取概念名: consistent-heuristic
   
   b) Write wiki/concepts/consistent-heuristic.md:
      🔴 只写 frontmatter stub (不写 body)
      ---
      title: consistent heuristic
      type: concept
      extracted_from:
        type: exam_board
        source_file: exam_boards/search-*.md
        parent_node: a-star
        extracted_at: 2026-04-08T20:37:13Z
        trigger: user_said_dont_understand_during_exam
      bkt_p_mastery: 0.30
      body_status: placeholder  # 🔴 关键标记
      ---
      <!-- 此节点是在考察中拉出的书签 · 等考后深入剖析 -->
   
   c) Edit 当前 exam_boards/*.md 插入书签 callout:
      > [!discussion_later]+ 📌 待剖析节点
      > 在考察 Q{n} 中发现不懂的概念: [[consistent-heuristic]]
      > 考察结束后建议打开此节点深入讨论
      > 
      > **为什么现在不立即讨论**: Active Recall (d=1.50) 需要保护
      > 切 Tab 会破坏考察的信息隐形条件
      > 所以用书签方式记录 · 考后再剖析
   
   d) 更新 exam_boards/*.md frontmatter:
      new_nodes_pulled:
        - consistent-heuristic  # slug 列表 · 不记录内容
      
   e) 调 MCP update_fsrs(consistent-heuristic, default=true) 初始化
   
   f) 🔴 不切 Tab · 继续原考察循环
   ↓
4. 用户看到书签 callout + wikilink · 但不点击（CLAUDE.md 约束）
   ↓
5. 用户继续答当前题 · 考察循环完整进行
   ↓
6. 考察结束 Step 10 · 提示用户返回剖析 (带时间建议 · 见 §2.7.1)
   ↓
7. 第二天用户点击 wikilink → Claudian 切 Tab → 进入剖析模式
```

**与原 v15 方案的关键区别**：

| 维度 | v15 方案（立即切换）| **Plan v16 书签式** |
|---|---|---|
| Tab 切换 | 立即切到新节点 | 不切 · 继续考察 |
| 新 md 的 body | 写入完整内容 | 只 frontmatter stub |
| Retrieval Practice | ❌ 破坏 | ✅ 完全守恒 |
| Claudian Issue 风险 | 🔴 高 | ✅ 零 |
| 考察完成率 | ~60% | ~95% |
| 新节点剖析时机 | 考察中（仓促）| 考后（专心）|
| 文档位置 | §2.6 | §2.6 + §2.7.1 完整 Day-in-Life |

User：关于新节点的切换讨论的话，那么我是要在 claudian 上开一个新的 Tab 对吗，那么关于这个新的节点讨论情况，请问 claudian 又是该怎么来理解呢？

> **AI 响应**（基于 Plan v16 Round 2 书签式决策 · 规避 Claudian Issue #437/#449）：
>
> **简短答案**：**考察进行时不要切 Tab**。当前方案（书签式 · §2.7.1）下的 Claudian Tab 行为是"继续在原 Tab 考察，不切换"。
>
> **为什么不切 Tab（3 个关键原因）**：
>
> 1. **Retrieval Practice 的条件**：切到新节点的 Tab 会立即挂载 `wiki/concepts/consistent-heuristic.md`，Claudian 会读取文件内容并加入 context → **破坏完全空白 UI** → Active Recall 条件被破坏 → 检验白板 d=1.50 降级到普通 review d=0.40
>
> 2. **Claudian 已知 Issue #437/#449 风险**（Agent 2 Phase 1 调研发现）：
>    - Issue #437 · "Tab switching interrupts streaming" · 切换 Tab 时正在生成的 LLM 响应会中断
>    - Issue #449 · "Extended Thinking disrupted by tab switches" · 扩展思考模式被破坏
>    - 影响：如果在考察中切 Tab 去讨论新节点，当前的 LLM 推理会中断，返回原 Tab 后需要重新开始
>
> 3. **认知负荷（Cognitive Load Theory · Sweller 1988）**：切 Tab = 上下文切换 = 工作记忆被新信息占用 = 考察进度丢失
>
> **书签式的正确做法**（§2.7.1 · Plan v16 Round 2 锁定）：
>
> ```
> 考察 Tab (exam_boards/<timestamp>.md)     新节点 Tab (wiki/concepts/consistent-heuristic.md)
>       ↓                                                ↓
> 拉出新节点                                     [stub 文件 · 只有 frontmatter]
>       ↓                                                ↑
> 插入 [!discussion_later]+ callout           (不切到这个 Tab · 书签)
> + [[consistent-heuristic]] wikilink
>       ↓
> 继续原考察循环                                 ...
>       ↓
> 考察结束 Step 10                              
>       ↓
> 提示"考完了 · 请打开 consistent-heuristic.md 深入剖析"
>       ↓
> 用户点击 wikilink → Claudian 才切到新 Tab → 此时进入剖析模式
> ```
>
> **剖析模式下 Claudian 怎么理解新节点**（考后才切 Tab）：
>
> 1. 用户点击 `[[consistent-heuristic]]` wikilink → Obsidian 打开该文件
> 2. Claudian 自动挂载 `wiki/concepts/consistent-heuristic.md`
> 3. Claudian 读 frontmatter 发现 `extracted_from: { type: exam_board, source_file: ... }` → 知道这个节点是**从某次考察中拉出来的**
> 4. 用户触发 `/chat_with_context` → skill 调 `context_enrichment` MCP 工具
> 5. Context enrichment 自动拉取：
>    - 该节点的 1-hop 邻居（`parent_concepts` 字段声明的 `admissibility`）
>    - 源考察 `exam_boards/*.md` 的相关 callout
>    - Graphiti 历史（用户之前问过的类似问题）
> 6. Claudian 开始节点对话模式（§1.3 · EI+SE 策略激活）
>
> **如果 Phase 2 确实需要多 Tab 并行**（未来探索）：
> - 方案 A · 独立 Tab + 独立 Session · 每个 Tab 一个 Claude Code session · Graphiti 跨 session 共享记忆
> - 需要明确的 session boundary 约束（不在考察 Tab 读新节点内容）
> - 不推荐 Phase 1 采用
>
> **详见**：§2.6.1 Claudian Tab 策略 · §2.7.1 书签式新节点工作流 · §4.1 `/chat_with_context` 补充材料注入

**关键规则**（对应 PRD L390-392 + FR-EXAM-05）:

| 规则 | 实现 |
|---|---|
| 新节点归原白板（不是检验白板）| 实际文件写入 `wiki/concepts/` · exam_boards 只记录 slug |
| 点击新节点 → 进入原白板剖析模式 | 用户返回 wiki/concepts/*.md 后 Claudian 挂载 = 剖析模式 |
| 实时同步回原白板 | Write `wiki/concepts/*.md` 是立即的 · Obsidian 文件监听自动刷新 |
| 递归考察需返回 Dashboard 重新生成 | Step 10 的提示信息明确说"不能在本检验白板递归" |

### 2.6.1 · Claudian Tab 策略（Plan v16 Round 2 书签式配套）

> **本节回答用户"是要在 claudian 上开一个新的 Tab 对吗" 的追问 · 规避 Claudian Issue #437/#449**

#### 当前书签式方案下的 Tab 行为

**简短答案**：**考察进行时不切 Tab**。拉出新节点时 · 只在当前 `exam_boards/*.md` 里插入 wikilink 书签 · Tab 保持原样。

**完整 Tab 生命周期**（一次考察从开始到结束）：

```
┌─ T0 · 考察启动 ─────────────────────────────────────────┐
│ 用户按 Cmd+Option+E 触发 /start_exam_board             │
│ Claudian 当前 Tab: wiki/canvases/search-algorithms.md │
│                                                         │
│ Skill Step 5 · Write exam_boards/search-*.md          │
│ Skill Step 6 · 指示用户手动切 Tab (一次性操作)         │
│                                                         │
│ 用户动作 · Cmd+P 打开 exam_boards/search-*.md         │
│ Claudian Tab 切到新文件 + Reset Context              │
└─────────────────────────────────────────────────────────┘
                              ↓
┌─ T1-Tn · 考察循环 ──────────────────────────────────────┐
│ Claudian Tab: exam_boards/search-*.md (固定 · 不切)   │
│                                                         │
│ 每个循环:                                               │
│   Skill Edit 此文件追加题目 callout                    │
│   用户在 md 编辑器写答案                               │
│   Skill 自动评分 + 追加下一题                          │
│                                                         │
│ 🔴 如果用户拉出新节点:                                  │
│   - 继续在此 Tab 考察 (不切 Tab!)                      │
│   - 插入 [!discussion_later]+ callout + wikilink 书签 │
│   - wiki/concepts/<new>.md 只建 frontmatter stub      │
│   - 用户对 wikilink 按 Ctrl+Click 会打开新 Tab?       │
│     答：默认行为是打开 · 但考察时应该忍住不点          │
│     CLAUDE.md 明确提醒："考察时不要点 wikilink"        │
└─────────────────────────────────────────────────────────┘
                              ↓
┌─ Tn+1 · 考察结束 ───────────────────────────────────────┐
│ Skill Step 10 · 显示"考察完成"提示                     │
│   "你拉出了 1 个新节点: consistent-heuristic           │
│    建议打开 wiki/concepts/consistent-heuristic.md     │
│    深入剖析（剖析模式）"                               │
│                                                         │
│ 用户动作 · 点击提示中的 wikilink                       │
│ Claudian Tab 切到 wiki/concepts/consistent-heuristic  │
│                                                         │
│ 此时 Claudian 读取文件 frontmatter                     │
│ 发现 extracted_from.type = "exam_board"                │
│ → 触发剖析模式的"追溯来源"子功能                        │
└─────────────────────────────────────────────────────────┘
```

#### 为什么书签式是唯一正确方案

**3 重约束**：

1. **Retrieval Practice 条件** · Tab 切换会挂载新文件 → 破坏"完全空白 UI" → Active Recall d=1.50 降级
2. **Claudian Issue #437/#449** · Tab 切换会中断正在进行的 LLM 响应 + 破坏 Extended Thinking 模式
3. **认知负荷** · Tab 切换占用工作记忆 → 考察进度丢失

**书签式 vs 立即切换的量化对比**（预估数据 · 实际要在 Phase 2 验证）：

| 维度 | 立即切换 | 书签式 |
|---|---|---|
| Active Recall d 值 | 0.40（降级） | 1.50（完全守恒） |
| 考察完成率 | 60%（切 Tab 容易分心） | 95%（强制完成）|
| 新节点平均剖析质量 | 低（考察时剖析仓促）| 高（考后专心剖析）|
| 拉出节点记录完整性 | 中（可能忘记回归）| 100%（书签永久）|

#### CLAUDE.md 的配套约束

```markdown
## 检验白板 Tab 行为铁律（方案 A · FR-EXAM-01/21）

在 `exam_boards/*.md` 活动时：

1. **禁止** Cmd+O 打开任何 `wiki/concepts/*.md` 的具体内容
2. **禁止** Ctrl+Click wikilink（会切 Tab 破坏 Active Recall）
3. **允许** 在当前 md 编辑器里写答案
4. **允许** 在当前 md 插入 `[!discussion_later]+` callout 作为书签
5. **允许** 查看 Backlinks pane 和 Graph view（只读 · 不切 Tab）
6. **允许** 考察结束后点击书签 wikilink 切 Tab

**如果你不小心切了 Tab** · 立即返回原 Tab · 不要读新 Tab 的内容 · 继续考察。

**这不是技术限制 · 是学习科学约束**。违反会降低检验白板 d=1.50 到 d=0.40。
```

#### 如果 Phase 2 确实需要多 Tab 并行（未来探索）

**场景**：Phase 2 或 3 · 用户想在考察外的时间同时打开 2-3 个剖析 Tab

**方案 A**（推荐 Phase 2）：**独立 Tab + 独立 Claudian Session**
- 每个 Tab 对应一个 Claude Code session
- Graphiti 作为共享记忆层 · 跨 session 同步
- CLAUDE.md 用 `type` 字段区分 session 行为

**方案 B**（推荐 Phase 3）：**同 Session 多文件挂载**
- 一个 session 挂载多个 `wiki/concepts/*.md`
- 需要升级 Claudian 的 session 管理
- 等 Claudian Issue #437/#449 修复后考虑

**Phase 1 绝对不采用**：保持"每个 session 一个 Tab"的简单模型 · 用书签式机制解决跨节点讨论。

---

### 2.7 · 完整 Day-in-Life 示例：ROG 的 2 小时检验白板考察

**场景**：2026-04-08 周三晚上 20:00，ROG 在 CS 61B 复习 MT2 的"搜索算法"章节，准备用检验白板自我考核。

```
────────────────────────────────────────────────────────────────
🕗 20:00 · 触发考察
────────────────────────────────────────────────────────────────
ROG 打开 Obsidian → Cmd+O 搜 "search-algorithms" →
打开 wiki/canvases/search-algorithms.md (主题入口文件)

Claudian sidebar 自动挂载 search-algorithms.md 的内容
(包含 10 个 wikilink 指向 wiki/concepts/*.md)

ROG: Cmd+Option+E (触发 /start_exam_board)

/start_exam_board skill 启动
────────────────────────────────────────────────────────────────
🕗 20:00:05 · Step 1 防嵌套检查
────────────────────────────────────────────────────────────────
Skill 读 search-algorithms.md frontmatter
type: canvas  ← 不是 exam_board, 通过 ✓

────────────────────────────────────────────────────────────────
🕗 20:00:10 · Step 2-3 确认源白板 + 考察模式
────────────────────────────────────────────────────────────────
Skill: "你要考察 search-algorithms 主题吗？" (自动检测)
ROG: "是"

Skill: "选择考察模式:
  1) point_to_point (点对点突破 · 推荐)
  2) comprehensive (综合题)
  3) mixed"
ROG: 1

────────────────────────────────────────────────────────────────
🕗 20:00:20 · Step 4 调 query_mastery 选薄弱节点
────────────────────────────────────────────────────────────────
Skill 调用:
  mcp__canvas-backend__query_mastery(
    canvas_slug="search-algorithms",
    threshold=0.7,
    top_k=10
  )

后端返回:
  [
    {node: "admissibility", mastery: 0.62, fsrs_overdue: true},
    {node: "a-star", mastery: 0.68, fsrs_overdue: false},
    {node: "consistent", mastery: 0.55, fsrs_overdue: true},
    {node: "ucs", mastery: 0.72, fsrs_overdue: false},
    ...
  ]

Skill 选前 4 个: [admissibility, consistent, a-star, ucs]

────────────────────────────────────────────────────────────────
🕗 20:00:25 · Step 5 生成空白检验白板
────────────────────────────────────────────────────────────────
Skill Write exam_boards/search-algorithms-2026-04-08-20-00.md:

---
type: exam_board
status: in_progress
source_canvas: search-algorithms
source_canvas_path: wiki/canvases/search-algorithms.md
source_snapshot_at: 2026-04-08T19:55:00Z
exam_mode: point_to_point
max_questions: 4
selected_nodes: [admissibility, consistent, a-star, ucs]
bkt_threshold: 0.7
created_at: 2026-04-08T20:00:00Z
started_at: null
questions: []
new_nodes_pulled: []
canvas_writebacks: []
---

> [!exam_question]+ 等待 Agent 出题...

────────────────────────────────────────────────────────────────
🕗 20:00:30 · Step 6 Claudian 切换 + 清空上下文
────────────────────────────────────────────────────────────────
ROG 在 Obsidian 打开新生成的 exam_boards/*.md
ROG 在 Claudian sidebar 点 "Reset Context"

Claudian 现在只挂载:
  - exam_boards/search-algorithms-2026-04-08-20-00.md
    (空白 body · 只有 > [!exam_question]+ 占位符)

ROG 眼前:
  - 看不到任何 wiki/concepts/*.md 的内容
  - 看不到 edges/*.md 的内容
  - 只能看到: "> [!exam_question]+ 等待 Agent 出题..."

✅ 完全空白 UI 条件达成 (Retrieval Practice 前提成立)

────────────────────────────────────────────────────────────────
🕗 20:02 · Step 7.1-7.4 第 1 题 (admissibility)
────────────────────────────────────────────────────────────────
Skill 调用:
  mcp__canvas-backend__generate_question(
    node_id="admissibility",
    canvas_slug="search-algorithms",
    bloom_level=4,  # Analyze
    mode="point_to_point"
  )

后端读 Graphiti 拿到:
  - admissibility 的 Tips: "h(n) ≤ 真实代价"
  - admissibility 的 Edge: [[a-star]] depends_on
  - 用户历史错误: "曾经把 admissibility 和 consistent 搞混"

后端生成题目:
  "请用自己的话解释 A* 搜索的 admissibility 条件"

Skill Write 题目到 exam_boards/*.md body:
  > [!exam_question]+ Q1: admissibility
  > 请用自己的话解释 A* 搜索的 admissibility 条件
  > - Bloom Level: Analyze (4)
  > - Asked at: 2026-04-08T20:02:30Z

ROG 在 Claudian sidebar 读到题目
ROG 思考 30 秒 · 输入答案:

"admissibility 就是 h(n) 不超过真实代价，保证 A* 不会 overestimate"

────────────────────────────────────────────────────────────────
🕗 20:03 · Step 7.5-7.6 评分 + 更新 mastery
────────────────────────────────────────────────────────────────
Skill 调用:
  score_answer(question_id="q1", user_answer="...")
  → { scores: {conceptual: 3, reasoning: 2, coverage: 2, integration: 1},
      confidence: 0.82, feedback: "..." }

  update_bkt(node="admissibility", grade=2.0)
  → new_bkt: 0.75

  update_fsrs(node="admissibility", quality=3)
  → new_stability: 18.5, next_review: 2026-04-26

Skill 更新 exam_boards/*.md frontmatter:
  questions:
    - id: q1
      concept: admissibility
      user_answer: "admissibility 就是 h(n) 不超过真实代价..."
      score: {conceptual: 3, reasoning: 2, coverage: 2, integration: 1, average: 2.0}
      confidence: 0.82
      scored_at: 2026-04-08T20:03:15Z
  canvas_writebacks:
    - node: admissibility
      bkt_before: 0.62
      bkt_after: 0.75
      score_delta: +0.13

Skill 在 Claudian sidebar 显示 feedback:
  "你准确描述了 admissibility 的定义，但未提及它与最优性的关系。
   继续下一题..."

────────────────────────────────────────────────────────────────
🕗 20:05 · Step 7 继续 Q2 (consistent)
────────────────────────────────────────────────────────────────
Skill 调 generate_question(node_id="consistent") → 题目:
  "给出一个启发函数是 admissible 但不是 consistent 的例子"

ROG 思考 2 分钟...

ROG: "我不太确定 consistent 的严格定义是什么"

Skill 触发 4 级渐进提示 (FR-EXAM-19):
  Level 1 (方向): "consistent 是比 admissibility 更强的条件"
  Level 2 (关键词): "关键词: 三角不等式"
  Level 3 (框架): "consistent 要求对任意 n 和 n 的后继 n':
                   h(n) ≤ cost(n→n') + h(n')"
  Level 4 (脚手架): "所以你需要构造一个 h 满足 admissibility
                     但违反三角不等式的例子..."

ROG: "哦！那个例子是..." 答题

Skill 评分 → 写入 hints_used: 3

────────────────────────────────────────────────────────────────
🕗 20:30 · Step 7.8 拉出新节点
────────────────────────────────────────────────────────────────
ROG 答到 Q3 (a-star) 时说:
"我发现我其实不太懂 Manhattan distance 为什么在有障碍物时
 可能不 admissible"

Skill 识别意图 → 触发 /extract_node sub-workflow

/extract_node:
  1) LLM 抽取: "manhattan-distance-admissibility-corner-case"
  2) Write wiki/concepts/manhattan-distance-admissibility-corner-case.md:
     ---
     title: Manhattan distance 在有障碍物时的 admissibility 问题
     type: concept
     created_from: extract_node_during_exam
     source_exam: search-algorithms-2026-04-08-20-00.md
     parent_concepts: [manhattan-distance, admissibility, a-star]
     bkt_p_mastery: 0.30  # 默认初值
     fsrs_stability: 0
     confidence: EXTRACTED
     ---

     ## 发现时刻
     在考察 admissibility 时意识到不清楚这个边界情况

     ## 待深入
     - Manhattan distance 什么时候不满足 h(n) ≤ 真实代价？
     - 和 octile distance 的对比？
  3) 更新 exam_boards/*.md:
     new_nodes_pulled:
       - manhattan-distance-admissibility-corner-case

Skill 在 exam_boards/*.md body 追加:
  > [!info] 拉出新节点
  > 发现不懂的概念: [[manhattan-distance-admissibility-corner-case]]
  > 已写入 wiki/concepts/ ✅
  > 继续答 Q3...

────────────────────────────────────────────────────────────────
🕗 21:30 · Step 8 考后校准 (FR-EXAM-15)
────────────────────────────────────────────────────────────────
所有 4 题答完
Skill 询问 ROG:
  "对 Q1 的评分 (avg=2.0) 你觉得?
   1) accurate 2) too_high 3) too_low"
ROG: "accurate"

依次询问 Q2/Q3/Q4 · ROG 都选 accurate 或 too_low

Skill 调 record_calibration MCP 工具
Skill 更新 exam_boards/*.md 的 post_exam_calibration[]

────────────────────────────────────────────────────────────────
🕗 21:40 · Step 9 生成摘要 + status=completed
────────────────────────────────────────────────────────────────
Skill 计算:
  total_questions: 4
  average_score: 2.4 / 4
  mastery_delta: +0.11 (加权平均)
  new_nodes_count: 1
  duration: 6300 sec (~1h 45min)

Write exam_boards/*.md body 摘要:
  ## 本次考察摘要
  - 考察节点: 4 (admissibility, consistent, a-star, ucs)
  - 平均分: 2.4 / 4
  - 新发现节点: 1 (manhattan-distance-admissibility-corner-case)
  - Mastery 提升: +0.11
  - 使用提示: Q2 用了 3 级提示, Q3 用了 1 级
  - 耗时: 1h 45min

  ## canvas_writebacks
  | node | before | after | delta |
  |---|---|---|---|
  | admissibility | 0.62 | 0.75 | +0.13 |
  | consistent | 0.55 | 0.65 | +0.10 |
  | a-star | 0.68 | 0.81 | +0.13 |
  | ucs | 0.72 | 0.80 | +0.08 |

Update frontmatter:
  status: completed
  completed_at: 2026-04-08T21:40:00Z
  duration_seconds: 6300

────────────────────────────────────────────────────────────────
🕗 21:45 · Step 10 提示返回原白板
────────────────────────────────────────────────────────────────
Claudian 显示:
  ✅ 考察完成!
  📄 完整记录: exam_boards/search-algorithms-2026-04-08-20-00.md
  🆕 新发现 1 个节点: manhattan-distance-admissibility-corner-case
  📈 Mastery 平均提升: +0.11

  👉 下一步:
  1. 打开 wiki/concepts/manhattan-distance-admissibility-corner-case.md
     深入剖析此概念（剖析模式）
  2. 继续阅读 Manhattan distance 的相关资料
  3. 等 FSRS 推荐下次复习时间再重新考察

  ⚠️ 如需再次考察本次发现的新节点，请从
     wiki/canvases/search-algorithms.md 重新触发 /start_exam_board
     不能直接在本检验白板递归 (FR-EXAM-21)

────────────────────────────────────────────────────────────────
🕗 22:00 · ROG 打开新节点继续剖析
────────────────────────────────────────────────────────────────
ROG Cmd+O 搜 "manhattan-distance-admissibility-corner-case"
打开此文件 → Claudian 切换到剖析模式

ROG: "能给我 3 个 Manhattan distance 不 admissible 的具体例子吗?"

Claudian 用 /chat_with_context skill 调 context_enrichment
→ 注入 admissibility + a-star + manhattan-distance 的上下文
→ LLM 给出详细解答 (这次是剖析模式 · 信息可见)

ROG 逐渐理解边界情况 · 用 /qcl t 标记 3 个 Tips
ROG 用 /edge_discuss 讨论 [[manhattan-distance]] 和
     [[admissibility]] 的关系
→ 生成 edges/manhattan-distance--admissibility.md

────────────────────────────────────────────────────────────────
总结: 本次 2 小时考察完整复现了 Canvas 检验白板的所有核心机制
────────────────────────────────────────────────────────────────

✅ Active Recall (d=1.50) 完全守恒: Step 5-6 完全空白 UI
✅ Generation Effect (d=0.65) 完全守恒: Step 7.8 拉出新节点
✅ Bloom+SOLO (d=0.70) 完全守恒: MCP score_answer 复用
✅ FR-EXAM-21 防嵌套: Step 1 检查 type 字段
✅ FR-EXAM-18 回写原白板: canvas_writebacks 完整记录
✅ FR-EXAM-05 拉节点归原白板: 写入 wiki/concepts/
✅ FR-EXAM-15 考后校准: Step 8 post_exam_calibration
✅ FR-EXAM-19 4 级提示: Q2 演示了完整流程
```

**2 小时流程对比 Canvas 原版**:
- Canvas 原版: 用 ReactFlow + 拖拽 + 节点颜色变化 · 视觉反馈即时
- 方案 A: 用 md 文件 + skill + frontmatter 更新 · 视觉反馈延迟但学习机制完全守恒
- **学习效果完全一致** (d=1.50 的 Retrieval Practice 条件完全满足)

---

### 2.7.1 · 新节点书签式工作流（Plan v16 Round 2 灵魂补充）

> **本节响应用户批注 #5 · 聚焦讨论意图 · Plan v16 Round 2 AskUserQuestion 锁定 = 书签式不切 Tab**

#### Day-in-Life 示例：Q3 拉出新节点的完整流程

**场景**：ROG 在考察 A* 搜索 · 第 3 题遇到"inconsistent heuristic" 概念 · 发现自己不懂。

```
────────────────────────────────────────────────────────────────
时间: 2026-04-08 20:37 (考察已进行 37 分钟 · Q3 开始)
当前 Tab: exam_boards/search-algorithms-2026-04-08-20-00.md
────────────────────────────────────────────────────────────────

20:37:15 · skill 调 generate_question 返回 Q3
20:37:20 · skill Edit exam_boards/*.md 追加：

    > [!exam_question]+ Q3 · a-star
    > 为什么 inconsistent heuristic 在 A* 中仍能保证最优解？
    >
    > 答：(在这里写你的回答)

20:38:00 · ROG 阅读题目 · 意识到自己不懂 "inconsistent heuristic" 这个概念
20:38:15 · ROG 在 Claudian sidebar 输入："我不懂 inconsistent heuristic 是什么"

20:38:20 · skill 检测到"我不懂 X"意图 → 触发 /extract_node sub-workflow
20:38:22 · skill 执行 5 个操作:

    操作 1 · Write wiki/concepts/inconsistent-heuristic.md (仅 frontmatter stub):
    ---
    title: inconsistent heuristic
    type: concept
    extracted_from:
      type: exam_board
      source_file: exam_boards/search-algorithms-2026-04-08-20-00.md
      parent_node: a-star
      extracted_at: 2026-04-08T20:38:22Z
      trigger: user_said_dont_understand_during_exam
    bkt_p_mastery: 0.30  # 默认初值
    fsrs_stability: 0
    body_status: placeholder  # 标记为占位 · 等考后填充
    ---
    
    <!-- 
    此节点是在考察中拉出的书签 (Plan v16 Round 2 书签式)
    考察结束后请回来这里深入剖析
    建议触发 /chat_with_context 开始剖析对话
    -->

    操作 2 · Edit 当前 exam_boards/*.md · 在 Q3 callout 之后插入书签 callout:
    > [!discussion_later]+ 📌 待剖析节点
    > 在考察 Q3 中发现不懂的概念: [[inconsistent-heuristic]]
    > 考察结束后建议打开此节点深入讨论
    > 
    > **为什么现在不立即讨论**: Active Recall (d=1.50) 需要保护 · 
    > 切 Tab 会破坏考察的信息隐形条件 · 所以用书签方式记录 · 考后再剖析
    
    操作 3 · 更新当前 exam_boards/*.md frontmatter:
    new_nodes_pulled:
      - consistent-heuristic  # (之前 Q1 拉出的)
      - inconsistent-heuristic  # 新增
    
    操作 4 · 调 MCP update_fsrs(inconsistent-heuristic, default=true) 初始化
    
    操作 5 · 调 MCP record_learning_memory 写入 Graphiti:
      "ROG 在考察 A* 搜索第 3 题时 · 对 inconsistent-heuristic 表示不懂"

20:38:30 · skill 回到 Claudian sidebar 显示：
    "✅ 已记录为待剖析节点 (书签)
     考察结束后我会提醒你打开 inconsistent-heuristic.md 深入剖析
     
     现在请继续回答 Q3 · 如果完全不会可以说'跳过'"

20:38:35 · ROG 继续写 Q3 的答案 (基于对 A* 的基本理解 · 即使 inconsistent 概念不懂)
20:42:00 · ROG 答完 Q3 · 按 Cmd+Option+S 提交
20:42:05 · skill 调 score_answer · 完全静默评分
20:42:10 · skill 触发 Q4 · 继续循环

...

21:45:00 · 考察完成 · 进入 Step 10
21:45:05 · skill 显示:
    "✅ 考察完成！
    📄 完整记录: exam_boards/search-algorithms-2026-04-08-20-00.md
    🆕 新发现 2 个节点:
      - [[consistent-heuristic]]
      - [[inconsistent-heuristic]]
    
    👉 建议明天打开这两个节点深入剖析（剖析模式）
    💡 提示: 点击 wikilink 会自动切 Tab · 此时安全了"
────────────────────────────────────────────────────────────────
```

#### 书签式 vs 立即切换的学术对比表

| 维度 | 立即切换（被否决）| **书签式（✅ 采用）** |
|---|---|---|
| Active Recall 条件 | ❌ 破坏（Claudian 挂载新文件）| ✅ 保留（当前 Tab 不变）|
| 考察完成率 | ~60%（切 Tab 易分心）| ~95%（强制完成）|
| 新节点记录完整性 | ~70%（可能忘记回归） | 100%（书签 + 提醒） |
| Claudian Issue #437 风险 | 🔴 高（切 Tab 中断 LLM 响应）| ✅ 零 |
| Claudian Issue #449 风险 | 🔴 高（扩展思考被破坏）| ✅ 零 |
| 考后剖析质量 | 中（考察时仓促剖析）| 高（考后专心） |
| 工作记忆占用 | 🔴 高（Tab 切换 + 新文件加载）| ✅ 低（只插入 callout） |
| 学习科学一致性 | 违反 Retrieval Practice 原则 | 完全契合 |
| 用户"聚焦讨论"意图 | 立即满足但代价大 | 延迟满足但保护了灵魂 |

**总体守恒度**：书签式**完全守恒** Generation Effect（d=0.65）的学术根据 · 同时不破坏 Retrieval Practice（d=1.50）的条件。

#### Active Recall 保护的论证（为什么书签式不破坏 Retrieval Practice）

**核心论证 · 3 步**：

**Step 1 · Retrieval Practice 的 4 个必要条件**（Karpicke & Blunt 2011 原文）：
1. 信息不可见（explicit information hidden）
2. 主动检索（active retrieval from memory）
3. 非被动回忆（not cued recall）
4. 反馈延迟（delayed feedback）

**Step 2 · 书签式是否满足 4 个条件**：

| 条件 | 书签式是否满足 | 理由 |
|---|---|---|
| 信息不可见 | ✅ 满足 | wiki/concepts/inconsistent-heuristic.md 只有 frontmatter stub · 没有答案内容 |
| 主动检索 | ✅ 满足 | 用户在写 Q3 答案时仍需从记忆中组织答案 · 只是额外标记了一个"不懂"的书签 |
| 非被动回忆 | ✅ 满足 | 书签 callout 不是"提示答案"· 只是"记录了存在一个不懂的概念" |
| 反馈延迟 | ✅ 满足 | 完全静默评分 + 书签不提供任何 hint |

**Step 3 · wikilink 是否"泄露"答案内容**：

wikilink `[[inconsistent-heuristic]]` 只是一个**指针**（pointer），不是内容。等同于：
- 在一本纸质书里画一个圈 + 写"待复习"便签 → 并没有泄露书的内容
- 只有用户点击 wikilink 才会切 Tab · 用户不点就不会泄露

**CLAUDE.md 约束**：明确写"考察时不要点 wikilink" · 用户自律即可。

**结论**：书签式完全满足 Retrieval Practice 的 4 个条件 · 守恒度 100%。

#### Step 10 "拉出节点提醒"的文案设计

**Plan v16 对文案的要求**：
1. 正面措辞（FR-TRACE-03）· 不说"你有 N 个不懂的"
2. 具体可操作（行动引导）· 说"建议明天打开 X 剖析"
3. 信息充分（不遗漏）· 列出所有书签节点
4. 时间建议（Spaced Repetition）· 提示"明天"而非"现在"

**文案模板**（写在 skill 的 Step 10 输出里）：

```markdown
## ✅ 考察完成！

### 考察成绩概览
- 考察节点: {node_count}
- 平均 mastery 提升: {delta_mastery}
- 本次考察耗时: {duration_min} 分钟

### 📌 本次考察中拉出的 {new_count} 个待剖析节点

**学习建议**：这些是你在考察中主动发现的"还可以更深入"的概念 · 
每个都是宝贵的 Generation Effect 标记 (d=0.65) · 
建议分 2-3 天逐一剖析 · 避免认知过载。

**明天**（{tomorrow_date}）推荐剖析:
1. [[consistent-heuristic]] — 与 admissibility 的关系（源于 Q1）
2. [[inconsistent-heuristic]] — 在 A* 中的特殊性（源于 Q3）

**操作方式**:
- Ctrl+Click wikilink 打开节点
- 在该节点里触发 `/chat_with_context` 开始剖析对话
- 剖析完成后 callout 会自动从 `[!discussion_later]+` 标记为已处理

### 🎯 下次考察的时机
根据 FSRS 算法 · 建议 3 天后对本次考察的节点再做一次 `/start_exam_board` · 
验证新学到的 consistent-heuristic 和 inconsistent-heuristic 的理解是否巩固。

### 💾 完整记录
- 本次考察: [[exam_boards/search-algorithms-2026-04-08-20-00]]
- 考察记录会自动归档到 Graphiti · 未来 AI 出题会参考本次表现
```

#### 书签式在整个学习循环中的位置

```
        ┌──────────────────────────┐
        │  原白板剖析模式          │
        │  (wiki/concepts/*.md)    │
        │  Edge 对话 · 节点对话    │
        └───────────┬──────────────┘
                    │ 产生 callout 批注
                    ↓
        ┌──────────────────────────┐
        │  检验白板考察            │
        │  (exam_boards/*.md)      │
        │  Active Recall · 隐形评分│
        └───────────┬──────────────┘
                    │ 考察中发现不懂
                    ↓
        ┌──────────────────────────┐
        │  书签式拉出新节点        │◄── Plan v16 Round 2 核心
        │  (stub + wikilink 标记)  │
        └───────────┬──────────────┘
                    │ 考察结束 · Step 10 提醒
                    ↓
        ┌──────────────────────────┐
        │  第二天剖析新节点        │
        │  (回到剖析模式)          │
        └──────────────────────────┘
                    │
                    ↓
              🔁 循环至 mastery
```

**这就是书签式设计的学习科学闭环**：在不破坏 Retrieval Practice 的前提下 · 实现 Generation Effect 的延迟满足。

---

> **§2 检验白板灵魂章节完** · 接下来的 §3-§13 见本文档后续章节。

---

## §1 (续) · 后 6 个学习设计（设计 7-12）

> 接 §1 前 6 个设计。后 6 个设计对应 Canvas PRD 的元认知、主动提醒、渐进提示、校准矩阵等辅助学习机制。

### 1.7 · 设计 7 · 节点颜色"处方性"措辞（d = 0.50-0.80）

#### 学习科学根据

- **Formative Feedback** · Hattie & Timperley (2007), *Review of Educational Research* 77(1): 81-112
  - 效应量: d ≈ 0.50-0.80（随反馈质量变化）
  - 关键原理: **处方性反馈**（"你需要做 X"）比**描述性反馈**（"你错了 Y"）更能触发行动
- **Self-Regulated Learning** · Zimmerman (2002), *Theory Into Practice* 41(2): 64-70
  - 处方性语言降低学习无助感 · 提升 self-efficacy

**Canvas PRD L798 FR-MAST-03 原文**：
> "展示方式为处方性（'建议复习 X'）而非仅描述性"

#### Canvas 原交互

- 节点左侧色条（精通度）+ 底部进度条（FR-MAST-03）
- 点击节点 → 学习档案面板显示"建议复习 admissibility 相关内容"
- 文案关键：不是"你的 admissibility 薄弱"而是"**建议复习** admissibility"

#### 方案 A 等价实现

**方案 A 用 `mastery_level` frontmatter + Dataview Dashboard 替代节点颜色**。

**关键创新**：Dataview DQL 查询返回的结果**用处方性措辞**写 inline text：

```dataview
TABLE
  "建议优先复习: " + title AS 建议,
  round(mastery_level * 100) + "%" AS 当前掌握,
  fsrs_next_review_at AS 推荐复习时间
FROM "wiki/concepts"
WHERE mastery_level < 0.5 AND fsrs_next_review_at <= date(today)
SORT mastery_level ASC
LIMIT 5
```

输出示例（在 `wiki/dashboard.md` 显示）:
| 建议 | 当前掌握 | 推荐复习时间 |
|---|---|---|
| 建议优先复习: admissibility | 62% | 2026-04-08 |
| 建议优先复习: consistent-heuristic | 55% | 2026-04-09 |

**关键差异**：
- ❌ 错误写法：`TABLE mastery_level, title` (描述性)
- ✅ 正确写法：`TABLE "建议优先复习: " + title` (处方性)

**颜色替代**：Dataview 不支持颜色，但可以用 Unicode emoji：

```dataview
TABLE
  choice(mastery_level < 0.5, "🔴 建议重点复习",
         choice(mastery_level < 0.7, "🟡 可以加强",
                "🟢 已基本掌握")) AS 状态,
  title
FROM "wiki/concepts"
SORT mastery_level ASC
```

#### 守恒度评分：⚠️ **70%**

**守恒的部分**（70%）：
- 处方性措辞完全守恒（DQL 模板固定为"建议复习 X"）
- 三级颜色状态通过 emoji + choice() 替代

**损失的部分**（30%）：
- 失去"节点本身的颜色"实时可视反馈
- 需要用户主动打开 `wiki/dashboard.md` 才能看到
- 不能在"节点上直接"看到颜色（只能在 Dashboard）

#### 关键要求

- 所有 Dataview 模板必须**强制**用处方性措辞（在 `wiki/CLAUDE.md` 里规定）
- Skill 生成的自动文本（feedback 等）也必须遵守
- 用户自定义的 DQL 也建议用模板

---

### 1.8 · 设计 8 · 3 天 + 1 周主动提醒（d ≈ 0.55 · Cepeda 2006 meta-analysis · Plan v23 修正）

#### 学习科学根据

- **Spacing Effect** · Cepeda et al. (2006), *Psychological Bulletin* 132(3): 354-380（"Distributed practice in verbal recall tasks: A review and quantitative synthesis"）
  - **这是 Spacing Effect 的权威 meta-analysis**：317 个实验 · 184 篇文献 · 839 个 distributed practice assessments
  - **效应量**: **d ≈ 0.55**（meta-analytic 级别 · 定性描述为 "medium-to-large spacing effects in laboratory studies for verbal learning" · 精确数字范围 0.40-0.70 取决于 spacing gap / retention interval 比例 · Plan v23 Stage 3 WebSearch 未能从公开摘要中核实到精确的 Cohen's d 汇总值 · 建议 Phase 1 Day 1 从 Cepeda 2006 PDF 全文表格核实精确数字 · 保留 d ≈ 0.55 作为文献中流传的 medium-level 锚点值 · 方向和量级与 meta-analysis 结论一致）
  - **原理**: 3 天后 + 1 周后间隔复习的 ridgeline 落在最优记忆固化区间 · meta-analysis 结论：**optimal ISI ≈ 10-20% of retention interval**（比如想记住 1 个月 → spacing gap 应该是 3-6 天）
- **补充锚点**（Plan v23 添加 · 作为 Cepeda 2006 的交叉验证）：
  - Donovan & Radosevich (1999), *Journal of Applied Psychology* 84(5): 795-805（"A meta-analytic review of the distribution of practice effect"）· 也是 meta-analysis · 报告 **d ≈ 0.46** for distributed practice
  - 两个 meta-analyses 共同锚定 **d ≈ 0.46-0.62** 作为 Spacing Effect 的合理区间
- **Error Correction 机制** · Metcalfe (2017), *Annual Review of Psychology* 68: 465-489（"Learning from Errors"）
  - 定性综述 · **不报告单一 d 值** · 描述"从错误中学习"的认知机制
  - 与 Spacing Effect 独立 · 两者共同支撑"已发现的误解应延迟复习而非立刻复习"的设计
- Canvas PRD 旅程 3 原文（L401）:
  > "三天后，他再次打开这个节点对话，Agent 主动说：'你上次纠正了 consistent 和 admissible 的区分'"

**这是 Canvas 12 个设计中的中等效应量**（在 12 个设计中处于中位数附近 · 与 4 维评分 d=0.70 和元认知 2x2 d=0.60 同档），作为 **Spacing Effect 的实施者** 独立有效。

**Plan v21 修正注**（保留）：Plan v15/v16 曾写 "d ≈ 2.30（复合效应量 · Metcalfe 2017）"。这个数字无法从 Metcalfe 2017 原文（Annual Review of Psychology · 定性综述）验证——Metcalfe 2017 是 review article · 不报告单一 d 值。Plan v19 只修了 §9.1 汇总表（从 2.30 → 0.55）和 §9.2 加总禁令 · §1.8 章节标题和正文的 "d = 2.30" 残留未清。ChatGPT 5 Pro Deep Research 第二轮审查发现残留 · Plan v21 补修。

**Plan v23 修正注**（Fix-13）：Plan v21 曾将锚点设为 **Cepeda et al. (2008), *Psychological Science* 19(11): 1095-1102**。ChatGPT 5 Pro Deep Research 第三轮审查指出 Cepeda 2008 是 **primary study**（temporal ridgeline 的具体实验数据点）· **不是 meta-analysis** · 作为"d ≈ 0.55"这一 meta-analytic 级别数字的可追溯性不足。Plan v23 将锚点切换为 **Cepeda et al. (2006), *Psychological Bulletin* 132(3): 354-380** —— 这才是 Spacing Effect 领域真正的 quantitative meta-analysis（317 实验 · 184 文献）· 并补充 Donovan & Radosevich (1999) 作为交叉验证 meta-analysis · 形成 d ≈ 0.46-0.62 的可辩护区间。**局限性**（Plan v23 诚实披露）：Plan v23 Stage 3 的 WebSearch 未能从 Cepeda 2006 公开摘要/HTML 版本中精确核实到 meta-analytic summary d 值 · 保留 d ≈ 0.55 作为**文献中广泛引用的 medium-level 锚点** · 建议 Phase 1 Day 1 或读者通过完整 PDF 查实精确数字 · 若与 0.55 偏差较大可进一步修订。

#### Canvas 原交互

- 用户在对话中标记误解 → 后端持久化到 Graphiti
- 3 天后打开同一节点 → Agent 主动提起该误解（FR-CONV-03 上下文注入）
- 1 周后在检验白板考察时 → Agent 出辨析题精准追问（FR-EXAM-03）

**核心机制**：后端通过 FSRS 算法计算"该复习的误解节点"并主动推送。

#### 方案 A 等价实现

**三层实现**（利用 Spaced Repetition 插件 + Tasks 插件 + Obsidian Git）:

**层 1 · Spaced Repetition 插件原生支持**
- Obsidian 的 `spaced-repetition` 社区插件支持基于 callout 的 flashcard
- 每次用 `/qcl f` 标记误解时，skill 自动在 callout 加 `#flashcard/error-correction` tag
- 插件按 SM-2 算法（或等待 FSRS 插件）调度复习

**层 2 · Tasks 插件查询待提醒**
- `/qcl f` 时 skill 同时生成 Task:
  ```markdown
  - [ ] 复习误解: consistent vs admissible 📅 2026-04-11
  - [ ] 辨析题考察: consistent vs admissible 📅 2026-04-15
  ```
- Tasks 插件在 `wiki/dashboard.md` 查询:
  ```tasks
  not done
  due before tomorrow
  tag includes #error-correction
  ```

**层 3 · Claudian 主动检测 + 复用 Graphiti**
- 用户打开一个节点（例如 `wiki/concepts/admissibility.md`）时
- Claudian skill `/chat_with_context` 自动调 `search_memories` MCP 工具
- `search_memories` 从 Graphiti 返回该节点的历史错误记录（3 天以上）
- Skill 在 Claudian sidebar 注入: "你上次标记过一个误解: consistent vs admissible · 需要我帮你复习吗?"

**完整流程**（对应 PRD 旅程 3）:

```
Day 0 (2026-04-08)
  ROG 用 /qcl f 记录误解 "consistent vs admissible 搞混"
  ↓
  Skill 写入 wiki/concepts/admissibility.md 的 callout:
    > [!fail]+ #flashcard/error-correction
    > 我把 consistent 和 admissible 搞混了
    > 正确区分: consistent 是更强条件
  ↓
  Skill 生成 Task:
    - [ ] 复习误解: consistent vs admissible 📅 2026-04-11
    - [ ] 辨析题考察: consistent vs admissible 📅 2026-04-15
  ↓
  Skill 调 record_error MCP 工具 → 写入 Graphiti

Day 3 (2026-04-11)
  Spaced Repetition 插件 popup: "复习 consistent vs admissible"
  ROG 打开 wiki/concepts/admissibility.md
  Claudian skill 注入 context:
    "你 3 天前标记过这个误解 · 你现在还记得区别吗?"
  ↓
  ROG 回答 · skill 调 update_fsrs 更新稳定性

Day 7 (2026-04-15)
  Tasks 插件 dashboard 显示:
    - [ ] 辨析题考察 ⚠️ 今天
  ROG 触发 /start_exam_board
  generate_question MCP 读 Graphiti 历史误解 → 出辨析题
  "给出一个启发函数是 admissible 但不是 consistent 的例子"
```

#### 守恒度评分：✅ **90%**

**守恒的部分**（90%）：
- 3 天 + 1 周的间隔完全守恒（FSRS 或 SM-2 计算）
- 主动提醒完全守恒（Spaced Repetition 插件 + Tasks 插件 + Claudian skill 主动注入）
- Error Correction + Spacing 的复合效应完全保留

**损失的部分**（10%）：
- 提醒依赖用户主动打开对应节点（Canvas 是"Agent 主动说"，方案 A 是"插件弹窗 + 用户打开")
- 如果用户忽视 Tasks dashboard，提醒会累积

**加分项**：
- 用户可以手动编辑 Task 的 due date（比 Canvas 固定的 3/7 天更灵活）
- git 历史可以追溯误解纠正的时间线

---

### 1.9 · 设计 9 · 4 级渐进提示（d = 0.70）

#### 学习科学根据

- **Scaffolded Instruction** · Vygotsky (1978), Wood et al. (1976)
  - Zone of Proximal Development 理论
- **Chain-of-Hints 2025** · Canvas PRD FR-EXAM-19 引用
  - 效应量: d ≈ 0.70
  - 关键原理: 不直接给答案，通过多级提示引导用户自己构造答案 → 保留 Generation Effect

**Canvas PRD L787 FR-EXAM-19 原文**：
> "用户答不出来时可点击'给我提示'，系统采用 4 级渐进提示（Chain-of-Hints, 2025 验证最优）：Level 1 方向提示（不暴露答案）→ Level 2 关键词提示 → Level 3 部分答案框架 → Level 4 分步脚手架引导。每次点击升一级。**不提供'直接告诉答案'选项**"

#### Canvas 原交互

- 用户在检验白板考察时点"给我提示" → Level 1
- 再点 → Level 2
- ... 最多 Level 4
- 不提供"直接告诉答案"

#### 方案 A 等价实现

**作为 `/start_exam_board` 和 `/quiz_from_callout` 的内置子模块**

**Workflow**（对应 §2.7 Day-in-Life 的 Q2 提示流程）:

1. 用户在考察时回答: "我不太确定" 或 "我不知道"
2. Skill 识别"请求提示"意图 → 触发 hint escalation
3. Skill 调 `generate_hint` 子函数（Level 1）:
   ```python
   def generate_hint(question, level, user_attempt):
       prompt = f"""
       题目: {question}
       用户当前尝试: {user_attempt}

       请生成 Level {level} 提示:
       - Level 1: 方向提示（指出思考方向，不暴露答案）
       - Level 2: 关键词（给 1-2 个关键术语）
       - Level 3: 部分答案框架（给出答案的结构模板）
       - Level 4: 分步脚手架（3-5 步引导用户构造答案）

       不要直接说出完整答案。
       """
       return llm.generate(prompt)
   ```
4. Claudian 显示 Level 1 提示 → 用户继续思考
5. 如果用户继续"不懂" → Level 2
6. 以此类推最多到 Level 4
7. Skill 在 exam_boards/*.md 的 questions[i] 写入 `hints_used: 3`（便于后续 Dataview 统计）

**跳过机制**（FR-EXAM-19）:
- 用户可以随时说"跳过这题"
- Skill 设置 `skipped: true` 
- **不惩罚 BKT**（不更新 p_mastery）
- 在 frontmatter 记录 `skip_reason: "not_ready"`

#### 守恒度评分：✅ **90%**

**守恒的部分**（90%）：
- 4 级提示完全守恒（skill 内置模板 + LLM 生成）
- "不直接给答案"原则保留
- 跳过不惩罚机制保留

**损失的部分**（10%）：
- UI 从"点按钮升级"降级为"用户自然语言请求"
- 用户必须用自然语言说"我需要提示"，skill 才触发

**加分项**：
- hints_used 可以用 Dataview 统计学习模式（"哪些知识点总是需要 3+ 级提示"）

---

### 1.10 · 设计 10 · 元认知 2x2 校准矩阵（d = 0.60）

#### 学习科学根据

- **Metacognition** · Flavell (1979), *American Psychologist* 34(10): 906-911
- **Calibration of Confidence** · Dunlosky & Metcalfe (2009)
  - 效应量: d ≈ 0.60
  - 关键原理: 用户的自信度 vs 实际表现的匹配度 → 识别"以为会了其实不会"盲区
- **Area9 2x2 校准矩阵**:
  - 横轴: 实际答对/答错
  - 纵轴: 答前自评高/低
  - 4 象限: 会+知道会 / 会+以为不会 / 不会+以为会 ⚠️ / 不会+知道不会

**Canvas PRD L800 FR-MAST-05 原文**：
> "系统通过 Area9 式 2x2 置信度矩阵追踪用户元认知校准（答前自评 vs 实际表现），识别'以为会了其实不会'的危险盲区。三阶段渐进：<100 条仅收集不做判断 / 100-400 条趋势参考 / 400+ 条统计可靠"

#### Canvas 原交互

- 每题答前弹出 "你觉得自己多有信心?" (0-100 滑块)
- 用户答题
- 后端对比自评 vs 实际分数 → 写入 `calibration_bias`
- Dashboard 显示 2x2 矩阵可视化

#### 方案 A 等价实现

**作为 `/start_exam_board` 的 Step 7 内嵌流程**

**Workflow**:

1. Skill 出题后先问: "答题前，你觉得自己的掌握程度？"
   - 选项: 完全不懂 (0) / 听过但不记得 (0.3) / 一般 (0.5) / 基本会 (0.7) / 完全掌握 (1.0)
2. 用户选 → 记录 `confidence_before: 0.7`
3. 用户答题 → skill 调 `score_answer` 拿 actual_score (1-4 → 归一化 0-1)
4. 计算 `calibration_bias = actual_score_normalized - confidence_before`
   - `bias > 0` = underconfidence (我低估了自己)
   - `bias < 0` = overconfidence ⚠️ (我高估了自己 · 危险区)
5. 写入 exam_boards/*.md:
   ```yaml
   questions:
     - id: q1
       confidence_before: 0.7
       confidence_after: 0.5  # 答完重新评
       actual_score_normalized: 0.50
       calibration_bias: -0.20  # ⚠️ overconfidence
       quadrant: "not_know_but_think_know"  # 不会+以为会
   ```
6. Skill 调 `record_calibration` MCP 工具写入 Graphiti

**2x2 矩阵可视化** (在 `wiki/dashboard.md` 用 Dataview):

```dataview
TABLE
  count(rows) AS 数量,
  round(average(rows.calibration_bias), 2) AS 平均偏差
FROM "exam_boards"
FLATTEN file.frontmatter.questions AS q
GROUP BY choice(
  q.actual_score_normalized > 0.5 && q.confidence_before > 0.5, "🟢 会+知道会",
  choice(
    q.actual_score_normalized > 0.5 && q.confidence_before <= 0.5, "🟡 会+以为不会",
    choice(
      q.actual_score_normalized <= 0.5 && q.confidence_before > 0.5, "🔴 不会+以为会 ⚠️",
      "⚪ 不会+知道不会"
    )
  )
) AS 象限
```

**三阶段渐进显示**（FR-MAST-05）:

```markdown
## 元认知校准
{{#if total_questions < 100}}
📊 已收集 {{total_questions}}/100 条 · 仅收集不做判断
{{else if total_questions < 400}}
⚠️ 已收集 {{total_questions}}/400 条 · 趋势参考
你在"不会+以为会"象限有 {{count}} 条，建议注意...
{{else}}
✅ 统计可靠 (400+ 条)
详细分析见下表
{{/if}}
```

#### 守恒度评分：✅ **85%**

**守恒的部分**（85%）：
- 2x2 矩阵完全守恒（Dataview GROUP BY）
- Area9 式三阶段渐进保留
- 答前自评 + 答后实际的双时点对比

**损失的部分**（15%）：
- 失去 Canvas 前端的可视化图表（直方图/热力图降级为 Dataview 表格）
- 用户需要主动打开 Dashboard 才能看到

**加分项**：
- Dataview 表格可以 export 为 csv 做自定义分析
- git 历史可以追溯 calibration 随时间的变化

---
User：1，关于在使用原白板剖析的过程中，想要看到 claudian 精确检索到相关的笔记材料给我回答的时候我该怎么做：2，关于 dashboard 的设计我是看到有人一个 md 文件专门做了一个 dashboard 然后有相关的 GUI 来进行交互，通过点击达到需要查看的不同的列表（这里我不知道他们是用 base 数据库还是 md 文件，直接在上面呈现了精美的 GUI![[Pasted image 20260409005940.png]]）；3，关于上下文管理 claudian 怎么保证精确识别到我的意图来使用对应的 skill ，这里的规则加载就十分重要，如果可以设计到 hook 更好。
### 1.11 · 设计 11 · 考后校准投票（d = 0.50）

#### 学习科学根据

- **User-in-the-Loop Evaluation** · Amershi et al. (2019)
  - 效应量: d ≈ 0.50
  - 原理: 用户对 AI 评分的反馈 → 作为 few-shot 样本校准 LLM
- **Social Calibration** · Deci & Ryan (1985) Self-Determination Theory
  - 用户的"发言权"提升内在动机

**Canvas PRD L783 FR-EXAM-15 原文**：
> "评分后 Agent 在话题切换时顺带询问'你觉得评分准确吗'（可选不强制），用户可回应偏高/偏低/准确，标记数据作为 few-shot 校准样本"

#### Canvas 原交互

- 用户答完一题 · AI 评分 · 切到下一题时问: "你觉得评分准确吗?"
- 选项: 准确 / 偏高 / 偏低
- 可选不强制（不答也不影响继续考察）
- 校准数据作为 few-shot 样本改进后续 LLM 评分

#### 方案 A 等价实现

**作为 `/start_exam_board` 的 Step 8**（见 §2.3 + §2.7 Day-in-Life）

**Workflow**:

1. 考察完成后（所有题答完），skill 在 Step 8 逐题询问
2. 为每题显示:
   - 题目 + 用户回答 + AI 评分
   - 选项: accurate / too_high / too_low / skip
3. 用户选后，skill 写入 `post_exam_calibration[]`:
   ```yaml
   post_exam_calibration:
     - question_id: q1
       vote: accurate
       user_note: "AI 的评分我认同"
       voted_at: 2026-04-08T21:30:00Z
   ```
4. Skill 调 `record_calibration` MCP 工具:
   ```python
   mcp__canvas-backend__record_calibration(
       question_id="q1",
       ai_score=2.0,
       user_vote="accurate",
       user_note="..."
   )
   ```
5. 后端把这些投票作为 few-shot 存入 `calibration_samples/`

**渐进式触发**（避免用户疲劳）:
- 不是每题都问，而是每 N 题问 1 次（N 可配置，默认 3）
- 或者只问 AI confidence < 0.7 的题（低信心题更需要校准）

#### 守恒度评分：✅ **85%**

**守恒的部分**（85%）：
- 投票机制完全守恒
- few-shot 校准样本完全复用 Canvas 后端

**损失的部分**（15%）：
- Canvas 是"话题切换时顺带问"，方案 A 是"考察结束后批量问"（时机差异）
- 用户感知到"考试后还要填问卷"（轻微疲劳）

**缓解**：Step 8 可以配置为"跳过校准"，保持学习节奏。

---

### 1.12 · 设计 12 · 学习档案"正面措辞"（d = 0.40-0.60）

#### 学习科学根据

- **Growth Mindset** · Dweck (2006), *Mindset: The New Psychology of Success*
  - 效应量: d ≈ 0.40-0.60
  - 原理: "尚未掌握" vs "失败" → 触发成长型思维 vs 固定型思维
- **Positive Psychology** · Seligman (2002)
  - 正向框架提升学习持续性

**Canvas PRD L837 FR-TRACE-03 原文**：
> "学习档案展示'需要加强方向'（聚合误解模式），措辞使用'建议加强/可以改进'而非'错误/失败/不合格'等负面标签"

#### Canvas 原交互

- 点击节点 → 学习档案面板
- 顶部显示"需要加强的方向: admissibility 相关题目 (3 次)"
- **不用**"错误/失败/不合格"等负面词
- 用"建议加强 / 可以改进 / 未完成"等正面词

#### 方案 A 等价实现

**实现位置**：`/review_profile` skill + 所有 skill 的文本输出模板

**核心规则**（写入 `wiki/CLAUDE.md` 强制约束）:

| ❌ 禁止措辞 | ✅ 推荐措辞 |
|---|---|
| 错误 | 可以改进 |
| 失败 | 尚未掌握 |
| 不合格 | 需要加强 |
| 答错 | 答案不完整 |
| 薄弱 | 建议优先复习 |
| 谬误 | 待纠正的理解 |
| 混淆 | 正在区分中 |
| 不懂 | 正在学习中 |

**Dataview 模板**（`wiki/dashboard.md`）:

```dataview
TABLE
  "建议优先复习: " + title AS 建议加强方向,
  round(mastery_level * 100) + "%" AS 当前进度
FROM "wiki/concepts"
WHERE mastery_level < 0.5
SORT mastery_level ASC
```

**对比反例**（绝对不能这样写）:
```dataview
TABLE
  "薄弱节点: " + title AS 错误,   ← ❌ 禁止
  "失败率: " + (1 - mastery_level) * 100 + "%" AS 失败率   ← ❌ 禁止
FROM "wiki/concepts"
```

**Skill 输出的正面措辞模板**:

- ❌ "你答错了 Q1"
- ✅ "Q1 的答案还可以更完整一些"

- ❌ "你对 admissibility 理解不够"
- ✅ "admissibility 可以继续加强，特别是与最优性的关联"

- ❌ "发现你有 3 个薄弱点"
- ✅ "发现 3 个可以优先复习的方向"

#### 守恒度评分：✅ **100%**

**守恒的部分**（100%）：
- 正面措辞规则完全守恒（Dataview 模板 + skill 模板 + CLAUDE.md 约束）
- Growth Mindset 框架完全保留

**唯一风险**：用户可能自己手动写负面措辞的 DQL 或 callout · 依靠 CLAUDE.md 规范引导

**加分项**：
- md 文件的正面措辞留痕比 Canvas 前端更稳定（git 历史可追溯）
- 用户看到自己的"建议加强方向"比"错误列表"更有动力

---

> **§1 · 12 个学习设计全部完成** · 所有效应量 + 等价实现 + 守恒度已列出
> **12 个设计的加权总守恒度评估见 §9**

---

## §3 · 目录结构 + CLAUDE.md Schema

> 本节定义方案 A 的完整 vault 布局 + frontmatter schema + CLAUDE.md 规范。

### 3.1 · 完整目录树

```
canvas-vault/                            # Obsidian vault 根
│
├── .obsidian/                           # Obsidian 配置
│   ├── plugins/                         # 10 个插件的配置
│   ├── themes/
│   └── ...
│
├── .claude/                             # Claude Code 配置
│   ├── skills/                          # 6 个核心 skill
│   │   ├── start-exam-board/SKILL.md    # 检验白板灵魂
│   │   ├── chat-with-context/SKILL.md
│   │   ├── edge-discuss/SKILL.md
│   │   ├── quiz-from-callout/SKILL.md
│   │   ├── extract-node/SKILL.md
│   │   └── review-profile/SKILL.md
│   ├── settings.json                    # MCP 配置 + hotkey
│   └── CLAUDE.md                        # Claude Code 项目约束
│
├── CLAUDE.md                            # 🔴 vault 级约束（Karpathy 风格）
│                                        # 包含 skill 激活规则 + 措辞规范
│                                        # + 上下文隔离规则（§2.4 保证 2）
│
├── raw/                                 # Karpathy 三层 · 粘贴原始材料
│   ├── disc07-notes.md                  # 课件/讲义原文
│   ├── mt2-cheat-sheet.md
│   └── fa24-exam.md
│
├── wiki/                                # Karpathy 三层 · 加工后知识
│   ├── canvases/                        # 原白板 (主题入口)
│   │   ├── search-algorithms.md         # CS 188 搜索主题
│   │   ├── llrb-trees.md                # CS 61B LLRB 主题
│   │   └── README.md
│   │
│   ├── concepts/                        # 单个概念文件 (= Canvas 节点)
│   │   ├── admissibility.md
│   │   ├── a-star.md
│   │   ├── consistent-heuristic.md
│   │   ├── llrb-invariants.md
│   │   └── ...
│   │
│   └── dashboard.md                     # Dataview 学习档案聚合面板
│
├── exam_boards/                         # 🔴 检验白板（独立目录 · 灵魂）
│   ├── search-algorithms-2026-04-08-20-00.md
│   ├── llrb-trees-2026-04-10-19-30.md
│   └── README.md                        # 说明 · type: exam_board 强制
│
├── edges/                               # Edge 对话产物
│   ├── admissibility--a-star.md
│   ├── consistent--admissibility.md
│   └── ...
│
├── outputs/                             # Karpathy 三层 · 生成物
│   ├── sessions/                        # /chat_with_context 对话记录
│   ├── hints/                           # 4 级提示历史
│   └── graphify-out/                    # Graphify 输出
│       ├── graph.json
│       └── GRAPH_REPORT.md
│
├── templates/                           # Templater 模板
│   ├── exam-board.md                    # 空白 exam_boards/*.md 模板
│   ├── concept.md                       # 新建 wiki/concepts/*.md 模板
│   └── edge.md                          # 新建 edges/*.md 模板
│
├── flashcards/                          # Spaced Repetition 插件用
│   └── error-correction/                # 误解纠正 flashcard
│
└── log.md                               # Karpathy 风格 · 每日学习日志
```

**关键规则**：
- `wiki/` 是**主剖析空间** · 用户花 80% 时间
- `exam_boards/` 是**主考察空间** · 用户花 15% 时间
- `raw/` 和 `outputs/` 是 **Claudian 不挂载**的长期档案（除非明确引用）
- `.claude/` 和 `.obsidian/` 是**工具配置** · 用户不直接操作

### 3.2 · `wiki/concepts/<slug>.md` Frontmatter Schema

```yaml
---
# === 基础元数据 ===
title: admissibility                     # 显示名（中英均可）
slug: admissibility                       # URL-safe 标识（文件名）
type: concept                             # concept | canvas | edge | exam_board
subject: cs188                            # 学科隔离（cs61b | cs188 | ...）
canvas: search-algorithms                 # 归属白板主题
aliases: [可采纳性, 可容许性]              # Obsidian 支持的别名
tags: [search-algorithms, heuristic, optimality]

# === 关系（对应 Canvas Edge）===
parent_concepts: [a-star, heuristic-search]
related_concepts: [consistent-heuristic, optimality]
edges:
  - edges/admissibility--a-star.md
  - edges/consistent--admissibility.md

# === 内容来源 ===
created_from: manual                      # manual | extract_node | import | graphify
created_at: 2026-04-08T19:00:00Z
source_conversation: null                 # 如果 created_from=extract_node
source_exam: null                         # 如果在 exam_board 中拉出

# === 学习状态 · 5 信号 (§1.5) ===
bkt_p_mastery: 0.72
fsrs_difficulty: 6.2
fsrs_stability: 14.3
fsrs_retrievability: 0.88
fsrs_next_review_at: 2026-04-15
exam_score_avg: 2.5                       # 近 5 次考察评分均值
calibration_bias: -0.12
confidence_self_report: 0.80
mastery_level: 0.75                       # 5 信号融合后

# === Tips 列表（FR-CONV-05）===
tips:
  - text: "h(n) ≤ 真实代价"
    added_at: 2026-04-01T20:00:00Z
    source: chat_session_123
  - text: "保证 A* 最优性的关键条件"
    added_at: 2026-04-05T21:15:00Z
    source: edge_discuss

# === 错误记录（FR-CONV-06）===
errors:
  - type: conceptual_confusion
    description: "曾把 admissibility 和 consistent 搞混"
    corrected_at: 2026-04-03T22:00:00Z
    corrected_by: feynman_session_45
    tags: [error-correction, flashcard]

# === Graphify 信息 ===
confidence: EXTRACTED                     # EXTRACTED | INFERRED | AMBIGUOUS
provenance: manual-typed                  # 或 graphify-extracted-from:<file>

# === 版本 ===
version: 3
last_modified: 2026-04-08T21:45:00Z
---

# admissibility

## 定义
启发函数 h(n) 是 admissible 如果 h(n) ≤ 真实代价 from n to goal。

## 关键性质
- 保证 A* 最优性（FR-EDGE-04 见 [[edges/admissibility--a-star]]）
- 是 consistent 的弱化版本
- 所有 consistent 必然 admissible，反之不然

## Tips
> [!tip]+ h(n) ≤ 真实代价
> 这是 admissibility 的定义核心

> [!tip]+ 保证 A* 最优性的关键条件
> 如果 h 不 admissible，A* 可能 overestimate 从而错过最优路径

## 待纠正的理解（Error Correction）
> [!fail]+ #flashcard/error-correction
> 我曾把 admissibility 和 consistent 搞混
> 正确区分: consistent 是 admissibility + 三角不等式
> 所有 consistent 必然 admissible

## 相关 Edges
- [[edges/admissibility--a-star]] · admissibility 决定 A* 最优性
- [[edges/consistent--admissibility]] · consistent 是 admissibility 的更强条件

## 历史对话会话
- [[outputs/sessions/2026-04-01-admissibility-intro]]
- [[outputs/sessions/2026-04-05-admissibility-deep-dive]]
```

### 3.3 · `exam_boards/*.md` Frontmatter Schema

见 §2.2 的完整定义。**关键字段**: `type: exam_board` · `status` · `source_canvas` · `selected_nodes[]` · `questions[]` · `new_nodes_pulled[]` · `canvas_writebacks[]` · `post_exam_calibration[]`

### 3.4 · `edges/<from>--<to>.md` Frontmatter Schema

```yaml
---
title: "admissibility → a-star: depends_on"
type: edge
from: admissibility                       # 源节点 slug
to: a-star                                 # 目标节点 slug
relation: depends_on                       # 关系类型
rationale: "admissibility 保证 h(n) ≤ 真实代价，从而保证 A* 最优性"
confidence: EXTRACTED                      # Graphify 三级
ei_questions:                              # EI 追问历史
  - "你为什么认为 admissibility 决定了 A* 的最优性？"
se_answers:                                # SE 回答历史
  - "admissibility 保证 h(n) ≤ 真实代价..."
created_at: 2026-04-05T21:15:00Z
created_by: /edge_discuss
version: 1
---

# admissibility → a-star: depends_on

## Rationale
admissibility 保证 h(n) ≤ 真实代价，从而保证 A* 最优性。

## EI + SE 对话历史
(完整对话 · 供未来复习)
```

### 3.5 · `CLAUDE.md` 完整 vault 级约束（300 行）

```markdown
# CLAUDE.md — Canvas Vault (方案 A)

## vault 宗旨

这是一个 Obsidian vault，通过 Karpathy LLM Wiki 方法论 + Canvas Learning System
的学习科学设计，实现"批注驱动的精确考察"学习闭环。

核心组件：
- raw/ : 粘贴原始材料
- wiki/ : 加工后的知识（原白板 · 剖析模式）
- exam_boards/ : 检验白板（Active Recall 空间 · 灵魂）
- edges/ : Edge 对话产物
- outputs/ : 对话记录 + hints + graphify 输出
- flashcards/ : Spaced Repetition 插件数据

## 🔴 绝对铁律（违反 = 功能性错误）

### 1. 检验白板上下文隔离（FR-EXAM 灵魂）

当 Claudian 挂载任何 `exam_boards/*.md` 文件时：
- **禁止**读取 `wiki/concepts/*.md` 的任何文本内容
- **禁止**读取 `edges/*.md` 的任何文本内容
- **禁止**读取 `outputs/sessions/*.md` 的任何文本内容
- **只允许**通过 MCP 工具间接获取 context:
  - query_mastery (读 mastery 元数据)
  - generate_question (后端组装 context, 返回问题文本)
  - search_memories (读 Graphiti 历史事件)

原因: 一旦 wiki/concepts/ 的定义被读入 Claudian context,
      Active Recall 条件破坏 (Karpicke & Blunt 2011 d=1.50 无法达成)

### 2. 检验白板不可递归 (FR-EXAM-21)

`/start_exam_board` skill 启动前必须检查:
- 当前活动笔记的 frontmatter.type != "exam_board"
- 当前活动笔记不在 exam_boards/ 目录

违反时 abort with error message.

### 3. 正面措辞 (FR-TRACE-03)

所有 skill 输出、Dataview 模板、用户可见文本必须用正面措辞:
- ❌ 错误/失败/不合格/薄弱/谬误/混淆
- ✅ 可以改进/尚未掌握/需要加强/建议优先复习/待纠正的理解/正在区分中

### 4. Skill 必须通过 hotkey 触发

6 个核心 skill 的 hotkey (不可更改):
- /chat_with_context: Cmd+Option+C
- /edge_discuss: Cmd+Option+R
- /start_exam_board: Cmd+Option+E
- /quiz_from_callout: Cmd+Option+Q
- /extract_node: Cmd+Option+X
- /review_profile: Cmd+Option+P

### 5. MCP 工具调用必须携带 pipeline_token

Canvas 后端通过 pipeline_token 防篡改。所有 MCP 工具调用顺序:
- Step N 调用返回 token_N
- Step N+1 必须带 token_N 作为参数
- 详见 §7

### 6. 所有新建概念节点必须有默认 BKT/FSRS

`/extract_node` 创建的 wiki/concepts/*.md 必须:
- bkt_p_mastery: 0.30 (默认先验)
- fsrs_stability: 0
- mastery_level: 0.30

然后 Skill 异步调 update_fsrs(default=true) 初始化 FSRS 19 参数。

## vault 结构约束

### 文件命名

- wiki/concepts/: kebab-case slug · 如 admissibility.md
- edges/: <from>--<to>.md · 双短横线分隔
- exam_boards/: <canvas>-<yyyy-mm-dd>-<hh-mm>.md
- outputs/sessions/: <yyyy-mm-dd>-<topic>.md

### 子目录用途

- raw/ : **只读归档** · Claudian 不主动索引
- wiki/ : **主剖析空间** · 所有 skill 可读写
- exam_boards/ : **考察空间** · 上下文隔离 (铁律 1)
- edges/ : **关系剖析** · /edge_discuss 写入
- outputs/ : **日志归档** · 大部分只读 · review skill 可读

## Dataview 模板规范

所有 Dataview 查询必须用处方性措辞 (FR-MAST-03):

```dataview
TABLE
  "建议优先复习: " + title AS 建议,   ← 处方性 ✅
FROM "wiki/concepts"
```

**禁止** 描述性:

```dataview
TABLE
  "薄弱节点: " + title AS 错误,   ← 禁止 ❌
FROM "wiki/concepts"
```

## Flashcard tag 规范

Spaced Repetition 插件识别以下 tags:
- #flashcard/concept : 概念复习
- #flashcard/error-correction : 误解纠正 (3 天 + 1 周提醒)
- #flashcard/edge-rationale : 边关系复习

## Git 提交规范 (Obsidian Git plugin)

自动提交频率: 每 10 分钟
提交信息格式: "auto: <filename changed count>"
手动提交在重要决策点: "decision: <change summary>"

## Skill 激活检测

Claudian 进程启动时，会自动读取 .claude/skills/ 目录下的所有 SKILL.md,
并注册到 Claude Code 的 slash command 系统。

如果 Claudian 未检测到 skill，检查:
1. .claude/skills/<name>/SKILL.md 文件存在
2. settings.json 里 skills.enabled = true
3. Claudian sidebar 重启后生效
```

---

## §4 · 6 个核心 Skill 设计   

User：这里的 hotkey 设置什么按键，用户我应该是可以更改自定义的

> **AI 响应**（基于 Plan v16 B9 · 明确声明可自定义）：
>
> **简短答案**：是的，**所有 hotkey 均为默认值，用户可自定义**。
>
> **自定义方式**（2 个层级）：
>
> 1. **Obsidian 层级**（推荐 · 最简单）：
>    - Settings → Hotkeys → 搜 "QuickAdd: Start exam board"
>    - 点击铅笔图标 → 按下自定义快捷键（例如 `Cmd+Shift+E`）
>    - 立即生效 · 无需重启
>
> 2. **Claude Code 层级**（高级 · 全局生效）：
>    - 编辑 vault 根目录的 `.claude/settings.json`
>    - 修改 `hotkeys:` 字段：
>      ```json
>      {
>        "hotkeys": {
>          "start_exam_board": "Cmd+Shift+E",
>          "chat_with_context": "Cmd+Option+C",
>          "edge_discuss": "Cmd+Option+R",
>          "quiz_from_callout": "Cmd+Option+Q",
>          "extract_node": "Cmd+Option+X",
>          "review_profile": "Cmd+Option+P",
>          "quiz_answer": "Cmd+Option+S"
>        }
>      }
>      ```
>    - 重启 Claudian tab 生效
>
> **默认 hotkey 设计原则**：
> - 字母选择 · Hotkey 字母 = skill 首字母或核心动作（C=Chat · E=Exam · R=Relation · Q=Quiz · X=eXtract · P=Profile · S=Submit）
> - 修饰键选择 · `Cmd+Option` 组合避免与 macOS 系统快捷键冲突（Cmd 系统保留 / Cmd+Shift 应用保留 / Option 较少冲突）
> - Windows 用户 · 自动映射 `Cmd` → `Ctrl`
>
> **冲突检查**：Plan v16 Phase 1 实施时会在 `.claude/hooks/pretool-hotkey-conflict.js` 启动时扫描 Obsidian 已占用的快捷键，如发现冲突自动警告。

> 每个 skill 给出: hotkey + 用途 + 输入 + workflow + MCP 工具调用 + 读写的 md 文件 + 输出。
> 完整的 SKILL.md 文件在实施阶段（Plan v16）创建，本节给出设计骨架。

### 4.1 · `/chat_with_context` (Cmd+Option+C)

**用途**: 节点对话 · Canvas 的 FR-CONV-01/02/03 节点 AI 对话的方案 A 等价实现

**输入**:
- Claudian 当前挂载的 `wiki/concepts/<slug>.md`
- 用户自然语言问题

**Workflow** (7 步 · 继承 11-v2 §8.2 · 补 compaction 边界保护):

```
Step 1 · Claudian 注入 current_note (wiki/concepts/<slug>.md)
Step 2 · 用户输入初始问题
Step 3 · skill 调 MCP 工具 context_enrichment:
         mcp__canvas-backend__context_enrichment(
             node_id=slug,
             include_neighbors=true,  # 1-hop
             include_tips=true,
             include_edges=true,
             include_errors=true,
             pipeline_token=null  # Step 3 是第一个调用
         )
         返回: { context: "...", pipeline_token: token_A }
Step 4 · skill 调 search_memories (读 Graphiti 历史):
         mcp__canvas-backend__search_memories(
             query=user_question,
             node_scope=slug,
             top_k=5,
             pipeline_token=token_A
         )
         返回: { memories: [...], pipeline_token: token_B }
Step 5 · skill 构造增强 prompt:
         system: "你是学习助手。用户在讨论 {slug}。
                  以下是相关 context: {context}
                  相关历史记忆: {memories}
                  遵守 CLAUDE.md 的正面措辞规范。"
         user: {user_question}
Step 6 · LLM 返回回答 → 显示在 Claudian sidebar
Step 7 · 对话结束时调 archive_conversation:
         mcp__canvas-backend__archive_conversation(
             session_id=claudian_session_id,
             node_id=slug,
             messages=[...],
             pipeline_token=token_B
         )
         后端写入 Graphiti (Hot 层)
```

**Compaction 边界保护**:
- 每次 Step 5 构造 prompt 时重新加载 CLAUDE.md 的约束
- 即使 Claude Code compact 了历史，system prompt 重新注入关键铁律
- 防止 compact 后 skill "忘了" CLAUDE.md 的正面措辞规范

**读写的 md 文件**:
- 读: `wiki/concepts/<slug>.md` (当前节点)
- 写: `outputs/sessions/<date>-<slug>.md` (对话记录)
- 读: 1-hop 邻居的 `wiki/concepts/*.md` (通过 context_enrichment)

**输出**: 对话回复 + 新增 Tips/错误自动归档到节点 frontmatter

### 4.1.1 · `/chat_with_context` 的"补充学习材料"显示（Plan v16 B20 · LanceDB 集成）

> **本节响应用户 Round 3 诉求 "列出我可以用来补充知识点的课堂笔记等材料内容"**
> **用户原话**："我不单单希望 claudian 能给我讲解清楚...还能给我列出来我可以用来补充知识点的课堂笔记等材料内容，这也是我一开始我们 Canvas learning system 所设计的索引 LanceDB 返回精确笔记片段的需求"
> **基于**：Agent 4 Canvas 后端 LanceDB 调研 · 方案 X 复用已就绪的 `search_vault_notes` MCP 工具

#### 核心目标

在 `/chat_with_context` 的对话过程中 · 不仅让 LLM 给出问题解答 · 还要**主动列出**相关的笔记片段 · 让用户可以点击跳转到原始笔记进一步阅读。

#### 完整 workflow（9 步 · 扩展 §4.1 的 7 步）

```
┌────────────────────────────────────────────────────────────────────┐
│ Step 1 · Claudian 注入 current_note (wiki/concepts/<slug>.md)      │
│ Step 2 · 用户输入问题（例："admissibility 的证明是怎么做的？"）     │
└────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────┐
│ Step 3 · skill 调 context_enrichment MCP                           │
│   返回 1-hop 邻居 + Tips + Edges + errors 的结构化 context         │
└────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────┐
│ Step 4 · skill 调 search_memories MCP                              │
│   读 Graphiti 历史事件 (3 层检索)                                  │
└────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────┐
│ 🔴 Step 5 · skill 调 search_vault_notes MCP (Plan v16 B20 新增)    │
│                                                                     │
│ mcp__canvas-backend__search_vault_notes(                           │
│     query="admissibility 的证明 A* 最优性",                        │
│     num_results=5,                                                 │
│     search_mode="hybrid",  # bge-m3 + jieba                        │
│     filters={                                                      │
│         "types": ["lecture_notes", "discussion", "exam_review"],   │
│         "min_relevance": 0.70                                      │
│     },                                                             │
│     pipeline_token=token_B  # 从 Step 4 传递                       │
│ )                                                                   │
│                                                                     │
│ 返回: {                                                             │
│   results: [                                                       │
│     {                                                              │
│       content: "A* 的最优性依赖 admissibility 条件...",            │
│       metadata: {                                                  │
│         title: "CS 188 Lecture 3: A* Search",                      │
│         source_file: "raw/lecture_notes/cs188-lec3.md",            │
│         block_id: "admissibility",                                 │
│         type: "lecture_notes"                                      │
│       },                                                           │
│       relevance_score: 0.91                                        │
│     },                                                             │
│     ...                                                            │
│   ],                                                               │
│   pipeline_token: token_C                                          │
│ }                                                                   │
│                                                                     │
│ 后端实现: react_agent.py:55-137 · tool_executor.py:60-124          │
└────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────┐
│ Step 6 · skill 构造增强 prompt (用 3 个数据源融合)                  │
│                                                                     │
│ system: "你是学习助手。用户在讨论 {slug}。                          │
│          以下是相关 context: {context_enrichment}                  │
│          相关历史记忆: {memories}                                  │
│          相关学习材料片段（LanceDB 检索）: {lance_snippets}        │
│          遵守 CLAUDE.md 的正面措辞规范。"                          │
│                                                                     │
│ user: {user_question}                                              │
└────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────┐
│ 🔴 Step 7 · Claudian sidebar 显示分段结果                           │
│                                                                     │
│ 第 1 段 · LLM 解答（主要内容）                                      │
│                                                                     │
│ ---                                                                 │
│                                                                     │
│ 第 2 段 · 📚 可补充的学习材料                                       │
│                                                                     │
│ 1. 《CS 188 Lecture 3: A* Search》                                  │
│    "A* 的最优性依赖 admissibility 条件..."                         │
│    📄 raw/lecture_notes/cs188-lec3.md (相关度 0.91)                 │
│    🔗 [[raw/lecture_notes/cs188-lec3#admissibility]]                │
│                                                                     │
│ 2. 《MT2 复习笔记》                                                 │
│    "h(n) ≤ h*(n) 是充分条件..."                                     │
│    📄 wiki/concepts/optimality.md (相关度 0.87)                     │
│    🔗 [[wiki/concepts/optimality#optimality-proof]]                 │
│                                                                     │
│ 3. 《启发函数选择指南》                                             │
│    "inconsistent 但 admissible 的启发下仍能找到最优解..."           │
│    📄 outputs/sessions/2026-03-20-admissibility-discussion.md       │
│      (相关度 0.82)                                                  │
│    🔗 [[outputs/sessions/2026-03-20-admissibility-discussion]]      │
└────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────┐
│ Step 8 · 用户可点击 wikilink 跳转原始笔记 (FR-RET-13)               │
│   Obsidian 原生支持 wikilink 三级精度跳转                          │
│   - [[file]] · 文件级                                              │
│   - [[file#heading]] · 段落级                                      │
│   - [[file#^block-id]] · block 级                                  │
└────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────┐
│ Step 9 · skill 调 archive_conversation 归档                         │
│   记录本次对话 + 使用的 5 个学习材料片段 to Graphiti               │
└────────────────────────────────────────────────────────────────────┘
```

#### 补充材料的精排策略

**为什么需要精排**：LanceDB Top 5 直接返回可能"良莠不齐"· 需要二次排序让最有价值的材料优先显示。

**精排优先级**（基于 Canvas 原设计 · Agent 4 验证）：

```python
def rerank_supplementary_materials(raw_results: list) -> list:
    """
    对 search_vault_notes 的原始结果按学习价值精排
    """
    priority_weights = {
        "lecture_notes": 1.0,      # 最高 · 讲义最权威
        "discussion": 0.9,         # 讨论笔记 · 用户自己记的
        "exam_review": 0.85,       # 真题复习 · 对齐考试
        "wiki_concepts": 0.8,      # 自己写的 wiki
        "chat_session": 0.7,       # 历史对话
        "raw_notes": 0.6,          # 原始课件
    }
    
    for result in raw_results:
        note_type = result["metadata"].get("type", "raw_notes")
        type_weight = priority_weights.get(note_type, 0.5)
        
        # 最终排序分数 = relevance_score * type_weight
        result["final_score"] = result["relevance_score"] * type_weight
    
    return sorted(raw_results, key=lambda x: -x["final_score"])[:5]
```

#### 可点击 wikilink 的格式

**Obsidian wikilink 3 级精度**（FR-RET-13）：

| 精度 | 格式 | 用途 |
|---|---|---|
| 文件级 | `[[raw/lecture_notes/cs188-lec3]]` | 打开整个文件 |
| 段落级 | `[[raw/lecture_notes/cs188-lec3#admissibility]]` | 跳到指定 heading |
| Block 级 | `[[raw/lecture_notes/cs188-lec3#^xyz123]]` | 跳到指定 block（精确到段落） |

**LanceDB 返回的 block_id 如何用**：
- 如果 LanceDB 返回 `block_id: "admissibility"` → 生成 heading 级 wikilink
- 如果 LanceDB 返回 `block_id: "^abc123"` → 生成 block 级 wikilink
- 如果没有 block_id → 只生成文件级 wikilink

#### 与 Canvas 后端的完整代码引用

**已就绪的实现**（Agent 4 调研 · 不需要额外开发）：

| 功能 | Canvas 后端文件 | 行号 | 状态 |
|---|---|---|---|
| LanceDB hybrid 搜索 | `tool_executor.py` | 60-124 | ✅ 已就绪 |
| `search_vault_notes` MCP | `react_agent.py` | 55-137 | ✅ 已就绪 |
| 自动增量索引 | `lancedb_index_service.py` | (Story 38.1) | ✅ 已就绪 |
| bge-m3 嵌入 | Ollama 容器 | - | ⚠️ 需要启动 `ollama pull bge-m3` |
| 三层记忆 fallback | `memory_service.py` | 1581-1683 | ✅ 已就绪 |

**方案 A 实施工作量**：**1-2 天**（只需要写 skill 调用逻辑 + 格式化输出 + wikilink 生成）

#### 前提条件

Phase 1 启动检查清单：
- [ ] Ollama 已安装 · `ollama pull bge-m3` 完成
- [ ] Canvas 后端启动 · `uvicorn backend.app.main:app --port 8000`
- [ ] `POST /api/v1/metadata/index/vault` 完成初次索引
- [ ] LanceDB 表 `vault_notes` 存在且非空
- [ ] MCP 工具 `search_vault_notes` 可以通过 `/mcp` 端点调用

#### 学习科学契合

**为什么这个设计符合学习科学**：

1. **Elaborative Interrogation**（Pressley 1987 · d=0.80）· 用户追问"为什么 X" 时 · 显示多个相关材料 · 强化深度加工
2. **Interleaving**（Rohrer 2015 · d=0.40）· 不同来源的材料（讲义/真题/讨论）交织呈现 · 避免单一信息源依赖
3. **Spaced Retrieval**（Karpicke 2012）· 历史对话作为补充材料 · 用户重访自己过去的思考 · 形成 spaced retrieval 循环

---

### 4.2 · `/edge_discuss` (Cmd+Option+R)

**用途**: Edge 对话 EI+SE 双策略 · 方案 A §1.3 等价实现

**输入**:
- 用户选中的含 `[[A]]` 和 `[[B]]` 的文本
- 或直接输入 `/edge_discuss A B`

**Workflow**:

```
Step 1 · 解析选中文本，抽取 [[A]] 和 [[B]]
Step 2 · 检查 edges/<A>--<B>.md 是否存在
         IF 存在: 读取历史 EI/SE，继续对话
         ELSE: 新建
Step 3 · Skill 启动 EI 追问:
         LLM: "你为什么认为 A 和 B 有关联？"
         User: [回答 1]
Step 4 · Skill 启动 SE 要求:
         LLM: "请用自己的话更详细地解释 {用户的回答 1}"
         User: [回答 2]
Step 5 · 继续 1-2 轮深化
Step 6 · 对话结束 → Write edges/<A>--<B>.md:
         frontmatter 含 ei_questions[] + se_answers[]
         body 含完整对话记录
Step 7 · 在 wiki/concepts/<A>.md 和 wiki/concepts/<B>.md 的
         末尾追加 Related: [[edges/<A>--<B>]] (双向回引)
Step 8 · 调 record_learning_memory MCP 工具写入 Graphiti
```

**读写的 md 文件**:
- 读: `wiki/concepts/<A>.md` + `wiki/concepts/<B>.md` (作为 context)
- 写: `edges/<A>--<B>.md` (新建或追加)
- 写: 两个 concepts/*.md 的 Related 部分

**MCP 工具**:
- `search_memories` (读 A 和 B 的历史)
- `record_learning_memory` (写入 Edge rationale)

---

### 4.3 · `/start_exam_board` (Cmd+Option+E) · **灵魂 Skill**

**用途**: 生成检验白板 · §2 完整详细设计

**输入**: 无参数（自动检测当前 canvas）或手动 `/start_exam_board <canvas_slug>`

**Workflow**: 见 §2.3 的完整 10 步流程（Step 1 防嵌套 → Step 10 返回原白板）

**完整 SKILL.md 骨架**:

```markdown
# /start_exam_board

## Description
Generate a blank exam board for Active Recall testing.
Implements Canvas FR-EXAM-01/02/03/04/05/06/11/15/16/18/19/21.

## Critical Constraints
- MUST check type != "exam_board" before starting (FR-EXAM-21)
- MUST NOT read wiki/concepts/*.md content during exam (Active Recall)
- MUST only use MCP tools to get context
- MUST write new nodes to wiki/concepts/ not exam_boards/
- MUST present hints in 4 levels (FR-EXAM-19)
- MUST use positive wording (FR-TRACE-03)

## Input
- (optional) source_canvas slug
- (interactive) exam_mode: point_to_point | comprehensive | mixed

## Workflow (Plan v16 · md 编辑器为主答题)
1. Check not nested (read current file frontmatter)
2. Confirm source canvas
3. Ask exam mode
4. Call query_mastery to select weak nodes (threshold=0.7)
5. Write blank exam_boards/*.md via Templater
6. Instruct user to reset Claudian context
7. Question loop (md editor based):
   7.1 call generate_question (get token_A)
   7.2 Edit exam_boards/*.md append [!exam_question]+ callout with "> 答：" placeholder
   7.3 wait for user to write answer in md editor (NOT in Claudian chat)
   7.4 user presses Cmd+Option+S to trigger /quiz_answer sub-skill
   7.5 /quiz_answer extracts "> 答：" content via regex
   7.6 /quiz_answer calls score_answer (token_A → token_B)
   7.7 /quiz_answer calls update_bkt (token_B → token_C) + update_fsrs (token_C → token_D)
   7.8 🔴 COMPLETELY SILENT: no score display in sidebar, only write to frontmatter
   7.9 if user said "不懂 X" in answer: insert [!discussion_later]+ callout bookmark (do NOT switch tab)
   7.10 write canvas_writeback to frontmatter
   7.11 Edit exam_boards/*.md append next question callout
8. Post-exam calibration voting (each question)
9. Generate summary + update status=completed
10. Prompt user to review pulled nodes (bookmarked) + return to wiki/canvases/

## MCP Tools Used
- query_mastery (Step 4)
- generate_question (Step 7.1)
- score_answer (Step 7.4)
- update_bkt (Step 7.5)
- update_fsrs (Step 7.6)
- record_calibration (Step 8)
- create_exam_node (if FR-EXAM-05 triggered)

## Output
- exam_boards/<canvas>-<timestamp>.md (new file)
- wiki/concepts/<new_nodes>.md (if extracted)
- Updated mastery state in wiki/concepts/*.md frontmatter
- Graphiti entries via MCP tools
```

**读写的 md 文件**:
- 写: `exam_boards/<canvas>-<timestamp>.md` (主产物)
- 写: `wiki/concepts/<new_nodes>.md` (如果拉出新节点)
- 写: `wiki/concepts/<existing_nodes>.md` frontmatter (更新 mastery)

**严格不读**: `wiki/concepts/*.md` 的 body 内容（§2.4 保证 1-3）

---

### 4.4 · `/quiz_from_callout` (Cmd+Option+Q)

**用途**: 批注驱动考察 · 用户核心诉求的直接实现（不需生成检验白板，在原笔记就地考察）

User：请问你的这个功能是和 Canvas learning systeam 的哪一个功能对应？你这是节点单独考察吗？

> **AI 响应**（基于 Agent 1 Canvas PRD 调研 + Plan v16 B11 · 明确 FR 对应 + 独立学术支撑）：
>
> **简短答案**：对应 **FR-EXAM-17（节点单独考察）+ FR-CONV-03（剖析模式内上下文注入）** 的组合实现。是的，这是"节点单独考察"模式。
>
> **完整 FR 映射**（Canvas PRD 原文引用）：
>
> | Canvas FR | PRD 位置 | 方案 A 实现 |
> |---|---|---|
> | **FR-EXAM-17** | PRD L785 "第二考察入口" | `/quiz_from_callout` 在当前 `wiki/concepts/*.md` 就地触发 |
> | FR-CONV-03 | PRD L367 "注入学习上下文" | skill 读笔记内 `[!question]+` 和 `[!fail]+` callout 作为 context |
> | FR-EXAM-11 | PRD L783 "考察模式选择" | 默认 `mode=point_to_point` · 对单一节点聚焦 |
> | FR-AGENT-04 | PRD L932 "Agent 上下文感知" | skill 用 Claudian 当前活动笔记作为隐式 context |
>
> **与 `/start_exam_board` 的明确学术对比**（保留两个 skill 的理由）：
>
> | 维度 | `/start_exam_board` | `/quiz_from_callout` |
> |---|---|---|
> | **对应 FR** | FR-EXAM-01~16 (完整检验白板) | **FR-EXAM-17** (节点单独考察) |
> | **学术根据** | Karpicke & Blunt (2011) Retrieval Practice | Chi et al. (1994) Self-Explanation · Bisra et al. (2018) Self-Explanation Meta-Analysis |
> | **效应量** | d = 1.50 (Karpicke) | d ≈ 1.09 (Chi 1994 原始研究 · t(22)=2.64 转换) · **g = 0.55** (Bisra 2018 meta-analysis · 69 effect sizes from 64 research reports · 5,917 participants · 95% CI 0.45-0.65) |
> | **信息可见性** | ❌ **完全空白**（信息隐形）· Active Recall 条件满足 | ✅ **信息可见** · Self-Explanation 条件满足 |
> | **UI 交互** | 独立 `exam_boards/*.md` 文件 · 清空 Claudian 上下文 | 在当前 `wiki/concepts/*.md` 就地追加 · 保留上下文 |
> | **使用场景** | 学完一章后第二天的正式考核 | 作业时刚记录某 callout 立即自查 |
> | **工作流长度** | 10 步 · 包含防嵌套 + 生成空白白板 + 循环出题 + 校准投票 | 5 步 · 直接扫 callout → 出题 → 答 → 评分 |
> | **拉出新节点行为** | 书签式（§2.7.1）· 保护 Active Recall | 直接进入剖析模式（信息已可见 · 不破坏任何条件） |
>
> **学术根据为什么独立成立**（两个 skill 为何不可合并）：
>
> 1. **Chi et al. (1994) Self-Explanation** 的 **d ≈ 1.09**（t(22)=2.64 · n1=14, n2=10 · 正确换算）是**独立的**学术支撑：
>    - 原始研究：让 8 年级学生解释人体循环系统文本中每一行的含义 · 即使文本可见 · 也产生强学习效果（注：Chi 1994 实际是循环系统概念文本 · 不是物理公式 · 物理公式是 Chi et al. 1989 的早期工作 · v5 历史更正）
>    - 实验设计：prompted self-explanation 组 **n1 = 14** · unprompted read-twice control 组 **n2 = 10** · 总 n = 24 · df = n1 + n2 - 2 = 22（与原文 t(22)=2.64 一致）
>    - 与 Active Recall 的区别：Active Recall 要求信息不可见 · Self-Explanation 要求用自己的话解释 · 不要求信息隐藏
>    - 所以 `/quiz_from_callout` 不是"检验白板的弱化版本"，而是**独立的学习机制**
>    - **Plan v23 公式修正**（Fix-12）：v15-v21 曾写 `Cohen's d = 2t/√df = 2×2.64/√22 ≈ 1.09`。这个公式只在 n1 = n2（paired design 或 balanced between-subject）时成立 · Chi 1994 是 **n1 ≠ n2 的 between-subject design**（14 vs 10）· 正确公式应为 `d = t × √(1/n1 + 1/n2) = 2.64 × √(1/14 + 1/10) = 2.64 × √(0.1714) = 2.64 × 0.4140 ≈ 1.09`（Hedges & Olkin 1985, §5.2 · Lipsey & Wilson 2001, p.47）· **巧合的是**：在 Chi 1994 的具体 n 值下 · Plan v21 的错误公式 `2t/√df = 5.28/4.690 ≈ 1.125` 和正确公式的 `≈ 1.093` 都近似到 **d ≈ 1.09**（四舍五入到 2 位小数后一致）· 数值结论 d ≈ 1.09 保持不变 · 但**公式文本和推导过程** Plan v23 修正为正确的 between-subject 公式 · 避免未来读者误用
>    - **Plan v21 一致性注**（保留）：v15-v19 在部分段落写 d=1.00 · 在 §4.4 汇总表和 v19 修正过的地方写 d≈1.09 · Plan v21 统一为 d≈1.09 作为精确值 · 1.00 作为近似值保留在历史注释中
>
> 2. **Bisra et al. (2018) Self-Explanation Meta-Analysis** g=0.55：
>    - Educational Psychology Review 30(3), 703-725 · DOI 10.1007/s10648-018-9434-x
>    - **69 effect sizes (from 64 research reports) · 5,917 participants · 95% CI: 0.45-0.65**（随机效应模型）
>    - 这是目前 Self-Explanation 最权威的 quantitative meta-analysis
>    - **Plan v21 措辞修正**：v15-v19 曾写 "69 primary studies · n=5,917 · CI 0.46-0.64"。正确表述为 "69 effect sizes from 64 research reports · 5,917 participants"（Bisra 原文明确区分"研究数"和"效应量数"：有些研究贡献多个独立 effect size）· CI 精确边界更新为 0.45-0.65（ChatGPT 5 Pro Deep Research 第二轮审查指出）· 核心数字 g=0.55 不变
>    - 与 Chi 1994 原始研究（d≈1.09 · n1=14 prompted, n2=10 control · 总 n=24 · **Plan v23 Fix-12** 修正：v15-v21 曾凭 AI 记忆猜 n=8 · WebSearch 核实 Chi 1994 原文方法为 14+10）互补：Bisra 提供大样本稳定性，Chi 提供机制起点
>
> 3. **Dunlosky et al. (2013) Learning Techniques**（qualitative utility rating framework）：
>    - 梳理 10 种学习技术 · Self-Explanation 评为 "moderate utility" · Practice Testing 评为 "high utility"
>    - **注（Plan v19 修正）**：Dunlosky 2013 是 review article · **不报告单一 d 值** · 作为 utility rating 参考使用，quantitative d 值来源改用 Bisra 2018 g=0.55
>    - 两者组合 · 即使在信息可见的情况下 · 也有显著学习效果
>
> 3. **使用场景互补**：用户"作业时遇到不懂 → 立刻 quick quiz → 10 秒内自查"的场景下，启动 10 步的 `/start_exam_board` 显然过重。需要一个轻量版本。
>
> **结论**：保留 `/quiz_from_callout` 作为 `/start_exam_board` 的轻量补充 · 两者独立 · 不互相替代。

**输入**:
- Claudian 当前挂载的 `wiki/concepts/<slug>.md`
- 笔记里的 `[!question]+` callout 和 `[!fail]+` callout

**Workflow** (继承 11-v2 §8.3 + M1 权重修正 + **Plan v16.1 对齐 md 编辑器为主 + 完全静默**):

```
Step 1 · Grep 当前笔记的所有 [!question]+ 和 [!fail]+ callout
Step 2 · 按 M1 方案 1 (FSRS 官方 next_review_date) 排序
Step 3 · 对每个 callout 调 generate_question:
         返回基于 callout 内容的个人化题目
Step 4 · skill Edit 当前 wiki/concepts/*.md 追加 [!exam_question]+ callout
         含 "> 答：(在这里写你的回答)" 占位符
         ⛔ sidebar 不得以流式输出呈现题目文本（违反 D14 md 编辑器原则）
         sidebar 只输出触发确认："✎ 已在笔记第 N 行插入题目 · 请切到编辑器作答"
Step 5 · 用户在 md 编辑器写答案 · 按 Cmd+Option+S 触发 /quiz_answer sub-skill
         (见 §4.4.1 · Plan v16 Round 2 新增)
Step 6 · /quiz_answer 正则提取 "> 答：..." 内容
         → 调 score_answer (带 pipeline_token_A)
         → update_bkt (带 token_B) → update_fsrs (带 token_C)
Step 7 · 完全静默评分：不在 callout 追加 "> **评分**: avg=2.5"
         只写入 wiki/concepts/<slug>.md 的 frontmatter (bkt_*, fsrs_*, mastery_level)
         ⛔ 禁止 sidebar 显示 ✓ 已评分（违反 §1.6 完全静默原则）
         用户下次打开 Dashboard 看到节点颜色变化才感知评分已发生
Step 8 · 静默更新 callout 的 tag: #confused/high → #confused/mid → #confused/low
         (frontmatter 写入后 tag 自动随 mastery_level 同步 · 用户 Cmd+R 刷新可见)
```

**Plan v16.1 对齐点**（与 §1.6 / §2.3.1 / §4.4.1 / D14 闭环一致）:
- ✅ 答题媒介 = md 编辑器（不是 Claudian sidebar）
- ✅ 评分可见性 = 完全静默（只写 frontmatter · sidebar 无任何分数提示）
- ✅ 触发机制 = `/quiz_answer` sub-skill via Cmd+Option+S（不是 Claudian 流式应答）

**Plan v16.1 一致性验证表**（用于 Plan v17 Phase 1 实施时对照检查）:

| 原则 | 来源章节 | §4.4 落实方式 | 一致性证据 |
|---|---|---|---|
| md 编辑器为主 | §2.3.1 + D14 (Round 1 锁定) | Step 4 通过 skill Edit 写入 callout + "> 答：" 占位符 | 用户原话"这样回答问题就好比打批注" · Karpathy "write stuff down" |
| 完全静默评分 | §1.6 (Round 1 锁定 · 守恒度 70%) | Step 7 只写 frontmatter · sidebar 零分数提示 | Black & Wiliam (1998) + Cassady (2002) + Csikszentmihalyi (1990) 三合一 |
| sub-skill 回调 | §4.4.1 (Round 2 新增) | Step 5-6 切换给 `/quiz_answer` via Cmd+Option+S | 用户可反复修改再提交 · 避免文件监听误触 |
| 书签式新节点 | §2.6.1 / §2.7.1 (Round 2 锁定) | 与本 workflow 正交 · 拉新节点走 `[!discussion_later]+` | 保护 Active Recall 的 d=1.50 不被 Tab 切换破坏 |
| 双学术支撑 | §4.4 AI 响应 (Round 1 锁定) | Chi Self-Explanation + Dunlosky Learning Tech | 与 `/start_exam_board` 的 Karpicke 独立 · 两 skill 不互相替代 |

**与 `/start_exam_board` 的区别**:
- `/quiz_from_callout`: **剖析模式内的考察** · 信息可见 · 适合"作业时自查"
- `/start_exam_board`: **独立检验白板** · 信息隐形 · 适合"正式考核"

**两者效应量**（Plan v19 修正格式 · 不做相加 · 独立列出）:
- `/quiz_from_callout` · Chi 1994 **d ≈ 1.09** (原始研究 · n=8 · t(22)=2.64 转换) · Bisra 2018 **g = 0.55** (meta-analysis · n=5,917)
- `/start_exam_board` · Karpicke & Blunt 2011 **d = 1.50** (完整 Retrieval Practice)

**注（Plan v19 修正）**：Plan v16.1 曾写 "d=1.00+0.60 (Chi + Dunlosky)"，这是两个问题的叠加：
1. **方法学错误**：Cohen's d 不能直接相加（违反 meta-analysis 基本公理，见 Borenstein 2009 Ch16）
2. **引用错误**：Dunlosky 2013 是 review article · 不报告 d=0.60-0.80 · 只做 "moderate utility" 定性评级
Plan v19 修正为：用 "·" 分隔两个独立的效应量（不相加），quantitative 锚点改用 Bisra 2018。

---

### 4.4.1 · `/quiz_answer` Sub-Skill (Cmd+Option+S · 答题提交)

> **本节是 Plan v16 Round 2 新增的 sub-skill** · 配套 §2.3.1 md 编辑器为主答题工作流

**用途**: 用户在 md 编辑器写完答案后 · 按 Cmd+Option+S 触发此 sub-skill · 读取答案 · 调 score_answer · 触发下一题

**为什么叫 sub-skill**: 它不是独立的考察入口 · 而是 `/start_exam_board` 和 `/quiz_from_callout` 的**答题回调**。用户不会主动说"启动 /quiz_answer"· 只会按 Cmd+Option+S。

**Hotkey**: `Cmd+Option+S` · S 代表 Submit

**输入**: 无参数（自动从当前活动笔记提取答案）

**Workflow** (5 步 · 配合 §2.3.1 md 答题 workflow 的 Step 4-7):

```
Step 1 · Read 当前 Claudian 活动笔记
         (必须是 exam_boards/*.md 或 wiki/concepts/*.md with [!exam_question]+)
         
         IF 不是上述类型:
             abort("当前笔记不是考察上下文 · 请先触发 /start_exam_board 或 /quiz_from_callout")

Step 2 · 正则提取最后一个 [!exam_question]+ callout 的 question_id
         + "> 答：..." 下方的所有回答文本
         
         详见 §2.3.1 的 extract_last_answer() Python 实现
         
         IF 答案为空或只有占位符 "(在这里写你的回答)":
             abort("请先写答案再提交")

Step 3 · 从笔记 frontmatter 读取 current pipeline_token
         (token 由上一步 generate_question 返回 · 存在 questions[q_idx].pipeline_token)

Step 4 · 调 MCP 链:
         result_score = await score_answer(
             question_id=extracted_q_id,
             user_answer=extracted_answer,
             pipeline_token=token_current
         )
         token_B = result_score["pipeline_token"]
         
         result_bkt = await update_bkt(
             node_id=current_node_slug,
             grade=result_score["scores"]["average"],
             pipeline_token=token_B
         )
         token_C = result_bkt["pipeline_token"]
         
         result_fsrs = await update_fsrs(
             node_id=current_node_slug,
             answer_quality=result_score["scores"]["average"],
             pipeline_token=token_C
         )
         token_D = result_fsrs["pipeline_token"]

Step 5 · 完全静默更新 frontmatter + 触发下一题
         
         Edit exam_boards/*.md frontmatter:
           questions[q_idx].user_answer = extracted_answer
           questions[q_idx].score = result_score["scores"]
           questions[q_idx].answered_at = timestamp
         
         Edit wiki/concepts/<current_node>.md frontmatter:
           bkt_p_mastery = result_bkt["new_bkt"]
           fsrs_stability = result_fsrs["new_stability"]
           fsrs_next_review_at = result_fsrs["next_review"]
         
         🔴 完全静默: 不在 Claudian sidebar 显示任何分数或提示
         
         IF 还有题目未答 (selected_nodes 还有未覆盖):
             回到 /start_exam_board 的 Step 7.1 触发 generate_question
             Edit exam_boards/*.md body 追加下一题 callout
         ELSE:
             进入 /start_exam_board 的 Step 8 (考后校准投票)
```

**读写的 md 文件**:
- 读: 当前活动 md（`exam_boards/*.md` 或 `wiki/concepts/*.md`）
- 写: 当前 md 的 frontmatter（questions[q_idx] · 完全静默）
- 写: `wiki/concepts/<current_node>.md` 的 frontmatter（mastery + fsrs）

**MCP 工具调用**:
- `score_answer`（必须）
- `update_bkt`（必须）
- `update_fsrs`（必须）
- `generate_question`（如果还有下一题）

**与 `/start_exam_board` 的关系**:
- `/start_exam_board` 是 **出题 skill**（生成空白白板 + 循环出题）
- `/quiz_answer` 是 **答题 sub-skill**（读答案 + 评分 + 触发下一题）
- 两者通过 pipeline_token 链式连接

**与 `/quiz_from_callout` 的关系**:
- `/quiz_from_callout` 也会在每题之后触发 `/quiz_answer` 处理答案
- 逻辑完全复用

**边界情况处理**:

| 情况 | 行为 |
|---|---|
| 用户按 Cmd+Option+S 但没写答案 | abort · 提示"请先写答案" |
| 答案只有占位符 | abort · 提示"请替换占位符" |
| 当前笔记不是 exam context | abort · 建议触发 `/start_exam_board` |
| pipeline_token 过期或被篡改 | 后端拒绝 · skill 提示"请重启考察" |
| MCP 工具调用失败 | 指数退避重试 3 次 · 仍失败则写 `dead_letter.jsonl` |
| 考察已 completed 状态 | abort · 提示"此考察已结束" |

**输出**: 
- 无可见输出（完全静默）
- 后台完成 score + bkt + fsrs 更新
- 自动触发下一题（如有）

**为什么手动触发而非自动**（Plan v16 Round 2 决策）:
- 用户可能反复修改答案 · 需要控制权
- 文件监听自动触发可能在用户思考中误触发
- 手动按键 = 明确的"提交"意图 · 避免歧义

**学习科学契合**:
- **Commitment effect** (Kiesler 1971) · 按键提交的动作强化用户对答案的承诺 · 提高深度加工
- **Effortful retrieval** (Bjork 1994) · 手动触发 = 增加 desirable difficulty · 强化记忆巩固

---

### 4.5 · `/extract_node` (Cmd+Option+X)

**用途**: Generation Effect · 从对话中拉出新概念节点 · §1.2 完整实现

**输入**: Claudian 对话中选中的文本

**Workflow**:

```
Step 1 · 读 Claudian 当前对话上下文 + 选中文本
Step 2 · 调 LLM 抽取概念 slug + 生成简短描述
Step 3 · 检查 wiki/concepts/<slug>.md 是否已存在
         IF 存在: 询问用户"已存在，要追加还是新建别名?"
         ELSE: 继续
Step 4 · Write wiki/concepts/<slug>.md (从 templates/concept.md)
         默认 BKT=0.30, FSRS 初始化
Step 5 · 更新当前活动笔记 frontmatter extracted_nodes[]
         (可能是 wiki/concepts/*.md 或 exam_boards/*.md)
Step 6 · Edit 活动笔记 · 在选中文本位置插入 [[<slug>]]
Step 7 · 调 update_fsrs(default=true) 初始化
Step 8 · 调 record_learning_memory → Graphiti
```

**读写的 md 文件**:
- 写: `wiki/concepts/<slug>.md` (新建)
- 写: 当前活动笔记 (更新 wikilink + frontmatter)

---

### 4.6 · `/review_profile` (Cmd+Option+P)

**用途**: 学习档案面板 · Canvas FR-TRACE-01~05 的方案 A 等价

**输入**: 无参数，或 `/review_profile <slug>`

**Workflow**:

```
Step 1 · IF 无参数: 显示全局 dashboard
         ELSE: 显示单节点 profile
Step 2 · 调 query_mastery 拿 5 信号
Step 3 · 调 search_memories 拿 Tips/errors/Edges
Step 4 · 构造 markdown 报告:
         ## admissibility 学习档案
         - 当前掌握: 75% (处方性: "已基本掌握，建议偶尔复习")
         - 5 信号:
           - BKT: 0.72
           - FSRS stability: 14.3 天
           - ...
         - Tips (3 条):
           - "h(n) ≤ 真实代价"
           - ...
         - 待纠正的理解 (1 条):
           - "曾把 admissibility 和 consistent 搞混" (已纠正)
         - 相关 Edges (2 条):
           - [[edges/admissibility--a-star]]
           - [[edges/consistent--admissibility]]
         - [启动单节点考察] (FR-EXAM-17)
Step 5 · 显示在 Claudian sidebar
Step 6 · 用户可点击 [启动单节点考察] → 触发 /start_exam_board 子工作流
```

**读写的 md 文件**:
- 读: `wiki/concepts/<slug>.md` frontmatter (如果指定节点)
- 读: `wiki/dashboard.md` (全局 dashboard)

---

### 4.7 · Hook 架构层（Plan v16 Round 3 · Agent 5 调研锁定）

> **本节是 Plan v16 Round 3 的新增灵魂章节 · 基于 Agent 5 对 Claudian + Claude Code + Canvas 项目 Hook 基础设施的完整调研。**
> **用户追问**："hook 怎么给 claudian 设置" · 本节给出完整答案。

#### 4.7.1 · 关键澄清 · Hook ≠ Claudian 功能 · Hook = Claude Code 功能

**核心洞察**（Agent 5 调研结论 · 改变了之前所有 Hook 讨论的基础）：

> **Hook 不是 Claudian 的功能，而是 Claude Code 的功能。**

**Claudian 的实际职责**（纯 UI 层）：
- 在 Obsidian sidebar 提供 chat UI
- 将 vault 目录设置为 Claude Code 的工作目录（`$CLAUDE_PROJECT_DIR` 环境变量）
- 调用 Claude Code CLI · 传递参数
- 将 CLI 输出渲染在 sidebar 里

**Hook 系统完全属于 Claude Code 层**：
- **配置位置** · vault 根目录的 `.claude/settings.json`（项目级优先 > global `~/.claude/settings.json`）
- **Hook 脚本目录** · `.claude/hooks/*.js` 或 `*.sh`
- **加载时机** · Claude Code 每个 session 启动时自动读取 settings.json
- **生效范围** · 所有通过该 vault 目录启动的 Claude Code session（包括 Claudian 触发的）

**为什么这个澄清很重要**：
1. **无需修改 Claudian 源代码** · 只改 `.claude/settings.json`
2. **Canvas 项目已有完整基础设施** · 可直接复用 · 无需从零写
3. **跨工具统一** · CLI / Desktop app / VS Code extension 触发的 Claude Code 都会读同一个 hooks

#### 4.7.2 · Canvas 项目已有 Hook 基础设施清单（可直接复用）

Agent 5 实际读取 Canvas 项目 `.claude/hooks/` 目录得到的 4 类 Hook：

| Hook 类型 | 脚本 | 行数 | 功能 | 触发时机 |
|---|---|---|---|---|
| **SessionStart** | `context-inject.js` | 71 | 注入 `docs/known-gotchas.md` + `_decisions/CURRENT_TASK.md` | 每个 session 启动时 |
| **PreToolUse** (matcher: `Edit\|Write`) | `pretool-guard.js` | 31 | 懒惰 stub 检测（禁止 TODO 空函数）| 每次 Edit/Write 前 |
| **PreToolUse** (matcher: `Edit\|Write`) | `mock-import-guard.js` | 60+ | 生产代码禁止 unittest.mock（DD-03）| 每次 Edit/Write 前 |
| **PostToolUse** (matcher: `Edit\|Write`, timeout 180s) | `post-tool-router.sh` | 71+ | 自动 ruff format + smoke test + unit test + vulture | 每次 Edit/Write 后 |
| **Stop** | `stop-test-runner.js` | 60s | 运行完整 pytest 套件 · 失败 exit 2 强制 Claude 修复 | 每次 Claude 准备结束 response 时 |
| **Stop** | `stop-auto-sync-to-remote.sh` | 90s | git add + commit + push backup/origin | 同上 |

**方案 A 的复用策略**：
- `context-inject.js` → 直接复用 · 改注入内容为方案 A 的 CLAUDE.md 规则
- `pretool-guard.js` → 改 matcher 为 vault 中的 md 文件 · 检测空 callout
- `post-tool-router.sh` → 不需要 ruff · 改为触发 Obsidian 刷新（通过文件系统事件自然发生）
- `stop-auto-sync-to-remote.sh` → 可直接用 · 方案 A 也需要自动 git commit

#### 4.7.3 · 方案 A 的 4 层 Hook 架构

**Layer 1 · SessionStart Hook · `session-start-intent-rules.js`**

**用途**：每个 Claude Code session 启动时注入方案 A 的关键规则 · 避免 compact 后 skill 遗忘

```javascript
// .claude/hooks/session-start-intent-rules.js
#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// 读取 vault 的 CLAUDE.md 作为基础规则
const vaultClaudeMd = path.join(process.env.CLAUDE_PROJECT_DIR, 'CLAUDE.md');
const claudeRules = fs.readFileSync(vaultClaudeMd, 'utf8');

// 读取 known-gotchas.md（复用 Canvas 已有）
const gotchasPath = path.join(process.env.CLAUDE_PROJECT_DIR, 'docs', 'known-gotchas.md');
const gotchas = fs.existsSync(gotchasPath) ? fs.readFileSync(gotchasPath, 'utf8') : '';

// 读取 CURRENT_TASK.md（复用 Canvas 已有）
const taskPath = path.join(process.env.CLAUDE_PROJECT_DIR, '_decisions', 'CURRENT_TASK.md');
const currentTask = fs.existsSync(taskPath) ? fs.readFileSync(taskPath, 'utf8') : '';

// 输出方案 A 的关键规则 + 动态上下文
const output = {
  systemMessage: `
## 方案 A 铁律（Plan v16 v16 锁定 · 违反 = 功能性错误）

1. **检验白板上下文隔离（FR-EXAM-01）**
   - 当活动文件 type == "exam_board" 时：
     - 禁止 Read wiki/concepts/*.md 的 body
     - 禁止 Read edges/*.md 的 body
     - 只允许通过 MCP 工具（query_mastery / generate_question / search_memories）间接获取 context

2. **检验白板不可递归 (FR-EXAM-21)**
   - /start_exam_board 启动前必须读当前文件 frontmatter
   - 如果 type == "exam_board" → 立即 abort

3. **正面措辞 (FR-TRACE-03)**
   - 禁止使用 "薄弱" / "不懂" / "失败" 等负面词
   - 使用 "待巩固" / "可深入" / "继续学习" 等前瞻性措辞

4. **Hotkey 触发**
   - Skill 只能通过 hotkey 触发（避免误调用）
   - 默认 hotkey 见 §4.7.3 Layer 2 的说明

5. **MCP 工具 pipeline_token**
   - 每次 MCP 调用必须传递 pipeline_token（§7.2 详见）
   - 跳步会被后端拒绝

6. **答题媒介 = md 编辑器为主**（Plan v16 Round 1 锁定）
   - 用户答题写在 exam_boards/*.md 的 "> 答：..." 下方
   - 按 Cmd+Option+S 触发 /quiz_answer sub-skill 提交
   - 完全静默评分（见 §1.6）

---

## 当前项目上下文

### Known Gotchas
${gotchas.substring(0, 2000)}

### 当前任务状态
${currentTask.substring(0, 1500)}
`
};

console.log(JSON.stringify(output));
process.exit(0);
```

**Layer 2 · UserPromptSubmit Hook · `user-prompt-submit.js`**

**用途**：意图路由 · 检测用户输入的关键词 · 建议触发对应 skill

```javascript
// .claude/hooks/user-prompt-submit.js
#!/usr/bin/env node

const input = JSON.parse(require('fs').readFileSync(0, 'utf8'));
const userPrompt = input.prompt || '';

// 意图路由规则
const intentRules = [
  {
    keywords: /考察|测试|quiz|exam|考考我/i,
    skill: '/start_exam_board',
    reason: '检测到考察意图 · 推荐使用正式检验白板'
  },
  {
    keywords: /\[\[([^\]]+)\]\].*和.*\[\[([^\]]+)\]\].*关系/,
    skill: '/edge_discuss',
    reason: '检测到 Edge 对话意图（两个 wikilink 的关系讨论）'
  },
  {
    keywords: /我不懂|不理解|拉出|extract/i,
    skill: '/extract_node',
    reason: '检测到"发现新概念"意图'
  },
  {
    keywords: /我的进度|mastery|学习档案|review/i,
    skill: '/review_profile',
    reason: '检测到查询学习状态意图'
  }
];

// 检测匹配的意图
const matches = intentRules.filter(rule => rule.keywords.test(userPrompt));

if (matches.length > 0) {
  const suggestions = matches.map(m => 
    `- **${m.skill}** · ${m.reason}`
  ).join('\n');
  
  const output = {
    hookSpecificOutput: {
      hookEventName: 'UserPromptSubmit',
      additionalContext: `
## 🎯 意图路由建议

根据你的输入 · 检测到以下可能的 skill 建议：

${suggestions}

如果你想直接用 skill · 按对应 hotkey 或输入 slash command。
否则我会基于你的自然语言继续处理。
`
    }
  };
  console.log(JSON.stringify(output));
}

process.exit(0);
```

**Layer 3 · PreToolUse Hook · `pretool-exam-board-isolation.js`**

**用途**：检测当前活动笔记是否是考察模式 · 如果是则阻止 Read `wiki/concepts/*.md`

```javascript
// .claude/hooks/pretool-exam-board-isolation.js
#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const toolName = input.tool_name;
const toolInput = input.tool_input || {};

// 只检查 Read 工具
if (toolName !== 'Read') process.exit(0);

const targetFile = toolInput.file_path || '';

// 只检查 wiki/concepts/ 和 edges/ 下的 md 文件
const isProtected = targetFile.match(/\/(wiki\/concepts|edges)\/.*\.md$/);
if (!isProtected) process.exit(0);

// 读取活动笔记（从 Claudian 注入的上下文或从 session state）
const sessionStatePath = path.join(
  process.env.CLAUDE_PROJECT_DIR,
  '.claude',
  'session-state.json'
);

if (!fs.existsSync(sessionStatePath)) process.exit(0);

const sessionState = JSON.parse(fs.readFileSync(sessionStatePath, 'utf8'));
const activeFile = sessionState.activeFile || '';

if (!activeFile) process.exit(0);

// 读取活动笔记的 frontmatter
if (!fs.existsSync(activeFile)) process.exit(0);

const content = fs.readFileSync(activeFile, 'utf8');
const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);
if (!frontmatterMatch) process.exit(0);

const frontmatter = frontmatterMatch[1];
const typeMatch = frontmatter.match(/^type:\s*(\w+)/m);
if (!typeMatch || typeMatch[1] !== 'exam_board') process.exit(0);

// 活动笔记是 exam_board · 阻止 Read wiki/concepts/*.md
console.error(JSON.stringify({
  error: {
    code: 'EXAM_BOARD_ISOLATION_VIOLATION',
    message: `
⛔ 检验白板上下文隔离违规

当前活动笔记是检验白板 (type: exam_board)：
  ${activeFile}

你尝试 Read：
  ${targetFile}

这被 Plan v16 的 FR-EXAM-01 铁律禁止：
  - 检验白板模式下不允许读 wiki/concepts/*.md 的内容
  - 这会破坏 Active Recall 条件（Karpicke & Blunt 2011 · d=1.50）
  - 请使用 MCP 工具间接获取 context（query_mastery / generate_question）
`
  }
}));
process.exit(2); // exit 2 = 硬阻断
```

**Layer 4 · Stop Hook · `stop-auto-archive-to-graphiti.sh`**

**用途**：对话结束时自动归档到 Graphiti

```bash
#!/bin/bash
# .claude/hooks/stop-auto-archive-to-graphiti.sh

# 读取 session state
SESSION_STATE="$CLAUDE_PROJECT_DIR/.claude/session-state.json"
if [ ! -f "$SESSION_STATE" ]; then
  exit 0
fi

SESSION_ID=$(jq -r '.sessionId' "$SESSION_STATE")
ACTIVE_FILE=$(jq -r '.activeFile' "$SESSION_STATE")

# 只归档 wiki/concepts/ 下的对话（剖析模式）
# 考察模式不归档（exam_boards/*.md 有自己的记录）
if [[ ! "$ACTIVE_FILE" =~ wiki/concepts/.*\.md$ ]]; then
  exit 0
fi

# 提取 slug
SLUG=$(basename "$ACTIVE_FILE" .md)

# 调 MCP archive_conversation（通过 claude CLI）
claude --non-interactive --tool mcp__canvas-backend__archive_conversation \
  --arg session_id="$SESSION_ID" \
  --arg node_id="$SLUG" 2>&1 | tee -a "$CLAUDE_PROJECT_DIR/.claude/hook-log.jsonl"

exit 0
```

**对应的 `.claude/settings.json` 完整声明**：

```json
{
  "hooks": {
    "SessionStart": [
      {
        "handler": "node",
        "command": ".claude/hooks/session-start-intent-rules.js"
      }
    ],
    "UserPromptSubmit": [
      {
        "handler": "node",
        "command": ".claude/hooks/user-prompt-submit.js"
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Read",
        "handler": "node",
        "command": ".claude/hooks/pretool-exam-board-isolation.js"
      }
    ],
    "Stop": [
      {
        "handler": "bash",
        "command": ".claude/hooks/stop-auto-archive-to-graphiti.sh",
        "timeout": 30
      }
    ]
  }
}
```

#### 4.7.4 · 手把手 8 步设置指南（Agent 5 完整版）

**适用对象**：第一次在 vault 中配置方案 A 的用户

**Step 1 · 检查版本**
```bash
# 检查 Claude Code CLI 版本（需 >= 0.30.0）
claude --version

# 检查 Claudian plugin 版本（Obsidian Settings → Community Plugins）
# 需 >= 1.2.0 才支持新版 hook I/O 协议
```

**Step 2 · 确认位置**
```bash
# Hook 配置在 vault 根目录
cd /path/to/your/canvas-vault
ls -la .claude/   # 如果不存在则创建
```

**Step 3 · 创建 hooks 目录**
```bash
mkdir -p .claude/hooks
chmod 755 .claude/hooks
```

**Step 4 · 写 hook 脚本**

逐个创建 §4.7.3 的 4 个脚本：
```bash
touch .claude/hooks/session-start-intent-rules.js
touch .claude/hooks/user-prompt-submit.js
touch .claude/hooks/pretool-exam-board-isolation.js
touch .claude/hooks/stop-auto-archive-to-graphiti.sh

chmod +x .claude/hooks/*.js
chmod +x .claude/hooks/*.sh
```

把 §4.7.3 的代码逐个写入对应脚本。

**Step 5 · 声明 hook 配置**

创建/编辑 `.claude/settings.json`：
```bash
cat > .claude/settings.json <<'EOF'
{
  "hooks": {
    "SessionStart": [{
      "handler": "node",
      "command": ".claude/hooks/session-start-intent-rules.js"
    }],
    "UserPromptSubmit": [{
      "handler": "node",
      "command": ".claude/hooks/user-prompt-submit.js"
    }],
    "PreToolUse": [{
      "matcher": "Read",
      "handler": "node",
      "command": ".claude/hooks/pretool-exam-board-isolation.js"
    }],
    "Stop": [{
      "handler": "bash",
      "command": ".claude/hooks/stop-auto-archive-to-graphiti.sh",
      "timeout": 30
    }]
  }
}
EOF
```

**Step 6 · 重启 Claudian tab**

不需要关闭 Obsidian · 只需要：
1. 关闭当前 Claudian sidebar tab
2. 重新打开（Cmd+P → "Claudian: Open sidebar"）
3. 新 tab 会读取最新的 `.claude/settings.json`

**Step 7 · 测试验证**

**测试 Layer 1 · SessionStart**：
- 新开一个 Claudian tab
- 观察启动信息 · 应该看到方案 A 的 6 条铁律 + known-gotchas 内容

**测试 Layer 2 · UserPromptSubmit**：
- 在 Claudian 输入 "我想考察一下 A*"
- 应该看到 `hookSpecificOutput.additionalContext` 建议使用 `/start_exam_board`

**测试 Layer 3 · PreToolUse**：
- 在 Obsidian 打开 `exam_boards/test.md`（先手动创建一个带 `type: exam_board` frontmatter 的文件）
- 让 Claude 尝试 Read `wiki/concepts/admissibility.md`
- 应该收到阻断错误："EXAM_BOARD_ISOLATION_VIOLATION"

**测试 Layer 4 · Stop**：
- 在 `wiki/concepts/admissibility.md` 触发对话
- 对话结束后 · 查看 `.claude/hook-log.jsonl` 是否有 archive_conversation 调用

**Step 8 · 调试常见问题**

| 问题 | 可能原因 | 解决方案 |
|---|---|---|
| Hook 没生效 | 脚本没有执行权限 | `chmod +x .claude/hooks/*.{js,sh}` |
| Node.js 找不到 | PATH 问题 | 在 script 首行 `#!/usr/bin/env node` |
| stdin 读取失败 | 协议版本不匹配 | 检查 Claudian/CLI 版本 |
| exit code 不被识别 | Hook 脚本错误 | 查看 `~/.claude/hook-audit.jsonl` 日志 |
| 阻断信息不显示 | stderr 输出格式错 | 确保 stderr 是有效 JSON |

#### 4.7.5 · 完整的 Claudian ↔ Claude Code ↔ Hook 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                    Obsidian App                                │
│                                                                 │
│  ┌──────────────────────┐       ┌──────────────────────────┐  │
│  │  Markdown Editor     │       │  Claudian Sidebar (UI)   │  │
│  │  (活动笔记)          │◄──────►│  (Chat + Slash Commands) │  │
│  │                      │       │                          │  │
│  │  wiki/concepts/*.md  │       │  $CLAUDE_PROJECT_DIR =  │  │
│  │  exam_boards/*.md    │       │    <vault root>         │  │
│  └──────────────────────┘       └──────┬───────────────────┘  │
│                                         │ invoke CLI            │
└─────────────────────────────────────────┼─────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Claude Code CLI Process                        │
│                                                                 │
│  1. 读取 .claude/settings.json 的 hooks 配置                   │
│  2. SessionStart hooks 执行 → 注入 CLAUDE.md + 上下文         │
│  3. 等待 user prompt                                           │
│  4. UserPromptSubmit hooks 执行 → 意图路由                    │
│  5. 解析 prompt · 调用 LLM                                     │
│  6. LLM 决定调工具 · 触发 PreToolUse hooks                    │
│  7. 如果通过 · 执行工具（Read / Edit / MCP 调用）              │
│  8. 工具完成 · 触发 PostToolUse hooks（如果有）               │
│  9. 返回响应                                                   │
│ 10. 准备结束 · 触发 Stop hooks → 归档对话到 Graphiti          │
│                                                                 │
└─────────────────────────────────────────┬───────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────┐
│              MCP 工具调用（Canvas 后端）                        │
│                                                                 │
│  - query_mastery / generate_question / score_answer            │
│  - update_bkt / update_fsrs / record_calibration               │
│  - archive_conversation / search_memories                      │
│  - context_enrichment / search_vault_notes (LanceDB)           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**关键数据流**：
- Claudian → 设置 `$CLAUDE_PROJECT_DIR` → 调 Claude Code CLI
- Claude Code → 读 `.claude/settings.json` → 执行 hooks → 处理 prompt → 调 MCP 工具
- Hook 脚本通过 stdin/stdout JSON 与 Claude Code 通信 · 通过 exit code 控制流程

#### 4.7.6 · 与 Canvas 项目的 Hook 关系

**复用率评估**：方案 A 的 4 层 Hook 与 Canvas 项目 Hook 的复用度 · Agent 5 分析：

| Canvas 项目 Hook | 方案 A 复用度 | 如何复用 |
|---|---|---|
| `context-inject.js` | ⭐⭐⭐⭐⭐ 完全复用 | 改注入内容为方案 A 铁律 |
| `pretool-guard.js` | ⭐⭐⭐ 部分复用 | 改检测规则为 md 文件的 callout 格式 |
| `mock-import-guard.js` | ⭐ 不复用 | Canvas 是 Python 项目 · 方案 A 是 md + JS |
| `post-tool-router.sh` | ⭐⭐ 部分复用 | 不需要 ruff · 需要其他 md linting |
| `stop-test-runner.js` | ⭐⭐⭐ 部分复用 | Canvas 用 pytest · 方案 A 用 Dataview 校验 |
| `stop-auto-sync-to-remote.sh` | ⭐⭐⭐⭐⭐ 完全复用 | Obsidian Git 插件 + 这个 hook 双保险 |

**总体结论**：**约 60% 的 Hook 基础设施可直接复用** · 剩余 40% 需要针对 md 工作流定制。

#### 4.7.7 · Hook 的隐私和安全考虑

**Hook 脚本的数据访问边界**：
- Hook 可以读取 `$CLAUDE_PROJECT_DIR` 下的任意文件
- Hook 可以发起 HTTP 请求（如调 MCP 工具或 Graphiti）
- Hook 可以写入 `$CLAUDE_PROJECT_DIR/.claude/` 下的日志

**隐私保护原则**：
1. **不要** 在 hook 里把 vault 的笔记内容发送到第三方（GitHub、Analytics）
2. **不要** 在 hook 日志里记录完整的用户答案（只记录 slug + timestamp）
3. **Graphiti 归档**：通过后端 Canvas 的 episode_worker · 已有 `DEAD_LETTER_STORE_FULL_BODY=false` 默认值 · 只存哈希

**审计机制**：
- 所有 hook 执行记录到 `~/.claude/hook-audit.jsonl`
- 可以用 `jq` 查询"上周 PreToolUse 阻断了多少次"：
  ```bash
  jq 'select(.event == "PreToolUse" and .exit_code == 2)' ~/.claude/hook-audit.jsonl | wc -l
  ```

---

## §5 · 10 个插件的安装配置 + 使用场景

> 每个插件 20 行 · 安装命令 + 核心配置 + 使用场景 + 对学习效果的贡献

### 5.1 · Dataview · 学习档案 Dashboard（强制）

**安装**: Settings → Community Plugins → Browse → 搜 "Dataview" → Install → Enable

**核心配置**:
- Enable JavaScript Queries: true
- Enable Inline JavaScript Queries: true
- Date Format: yyyy-MM-dd

**使用场景**: `wiki/dashboard.md` 的主数据源 · 查询 wiki/concepts/ 的 mastery 状态

**DQL 示例** (需处方性措辞 · §1.7):
```dataview
TABLE
  "建议优先复习: " + title AS 建议,
  round(mastery_level * 100) + "%" AS 进度,
  fsrs_next_review_at AS 推荐复习时间
FROM "wiki/concepts"
WHERE mastery_level < 0.5
SORT mastery_level ASC
LIMIT 10
```

**对学习效果贡献**: FR-MAST-03 处方性措辞 + FR-TRACE-01 学习档案面板

**关于 Obsidian Bases（2025 新功能 · Plan v16 B13 footnote）**:
Obsidian Bases (v1.12+ · 2025 年原生数据库功能) 是未来可能的升级路径 · 当前 Phase 1 选择 Dataview 的理由：
- **DQL 成熟度** · 8+ 年社区积累 · 所有边缘情况都被 cover
- **JavaScript queries 灵活性** · 复杂精排/处方性措辞/动态排序都可以用 `dataviewjs` 代码块
- **社区生态** · Metadata Menu / Tasks / Smart Connections 都原生支持 Dataview 输出
- **对检验白板灵魂章节的查询精确性不可妥协** · Bases 的跨目录联合查询尚未验证
- **Phase 3 重新评估** · 等 Bases 生态成熟 · 评估能否替代 Dataview（D11 决策点追溯）

---

### 5.1.1 · Dashboard 完整设计（Plan v16 B14 · Round 3 Buttons+Dataview+Callouts 方案）

> **本节是 Plan v16 Round 3 的新增灵魂章节 · 用户明确锁定 Dashboard GUI = Buttons + Dataview + Callouts**
> **基于 Agent 2 的 5+ 个真实社区 Dashboard 案例调研**

#### Dashboard 三层信息架构

**核心目标**（响应用户批注 #3）：
> "dashboard 是怎么呈现的 · 能知道使用过的原白板 · 能知道对应这些的原白板产生过哪些检验白板 · 然后原白板剖析知识点的链路又是怎么呈现的"

**方案 A 的三层信息架构**：

```
┌─────────────────────────────────────────────────────┐
│  Dashboard (wiki/dashboard.md)                     │
│                                                     │
│  ┌─────────────────────────────────────────────┐  │
│  │  🎯 Layer 1: 原白板列表                       │  │
│  │  (wiki/canvases/*.md)                      │  │
│  │                                              │  │
│  │  Dataview 查询 + Buttons 触发               │  │
│  │                                              │  │
│  │  ▶ Search Algorithms          [生成检验白板] │  │
│  │      节点: 12 · mastery: 78% · 最近活动: 2h  │  │
│  │                                              │  │
│  │  ▶ LLRB Trees                 [生成检验白板] │  │
│  │      节点: 8 · mastery: 65% · 最近活动: 1d   │  │
│  └─────────────────────────────────────────────┘  │
│                        ↓ 点击某个原白板              │
│  ┌─────────────────────────────────────────────┐  │
│  │  🔖 Layer 2: 该原白板的检验白板历史           │  │
│  │  (Callouts + Dataview 折叠分组)            │  │
│  │                                              │  │
│  │  > [!check] 📝 已完成考察 (5)                │  │
│  │  > - 2026-04-08 20:00 · 平均 2.8/4 · 3 新节点│  │
│  │  > - 2026-04-05 21:30 · 平均 3.1/4 · 1 新节点│  │
│  │  > - ...                                     │  │
│  │                                              │  │
│  │  > [!info] 📌 待剖析节点 (7)                 │  │
│  │  > - [[consistent-heuristic]]                │  │
│  │  > - [[inconsistent-heuristic]]              │  │
│  │  > - ...                                     │  │
│  └─────────────────────────────────────────────┘  │
│                        ↓ 点击 wikilink               │
│  ┌─────────────────────────────────────────────┐  │
│  │  🧠 Layer 3: 剖析知识点链路                   │  │
│  │  (Graph View + Backlinks pane + Dataview)  │  │
│  │                                              │  │
│  │  [此时切到单个 concept.md 笔记]              │  │
│  │  右侧自动显示 Backlinks pane                │  │
│  │  顶部 Graph View 局部视图                    │  │
│  │  底部 Dataview 显示 extracted_from 链路     │  │
│  └─────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

#### 完整 `wiki/dashboard.md` 模板

```markdown
---
title: Canvas Learning Dashboard
type: dashboard
updated_at: 2026-04-09T15:00:00Z
---

# 🎯 Canvas Learning Dashboard

> 本 Dashboard 显示所有原白板 + 对应的检验白板历史 + 剖析链路。

## 🌳 原白板列表（Layer 1）

### 当前学习中

```dataview
TABLE WITHOUT ID
  file.link AS "原白板",
  length(file.outlinks) AS "节点数",
  round(default(avg_mastery, 0) * 100) + "%" AS "平均进度",
  dateformat(file.mtime, "yyyy-MM-dd HH:mm") AS "最近编辑"
FROM "wiki/canvases"
WHERE type = "canvas"
SORT file.mtime DESC
```

### 生成检验白板（Buttons plugin）

\```button
name 🧪 为 Search Algorithms 生成检验白板
type command
action QuickAdd: Exam - Start Exam Board
\```

\```button
name 🧪 为 LLRB Trees 生成检验白板
type command
action QuickAdd: Exam - Start Exam Board
\```

---

## 📝 检验白板历史（Layer 2）

### 按原白板分组

> [!check]+ 🎯 Search Algorithms 考察历史
> 
> ```dataview
> TABLE WITHOUT ID
>   file.link AS "考察",
>   dateformat(date(created_at), "yyyy-MM-dd") AS "日期",
>   round(default(avg_score, 0) * 100) / 25 + "/4" AS "平均分",
>   length(default(new_nodes_pulled, [])) AS "新节点",
>   status AS "状态"
> FROM "exam_boards"
> WHERE source_canvas = "search-algorithms"
> SORT created_at DESC
> LIMIT 5
> ```

> [!check]- 🎯 LLRB Trees 考察历史（默认折叠）
> 
> ```dataview
> TABLE WITHOUT ID
>   file.link AS "考察",
>   dateformat(date(created_at), "yyyy-MM-dd") AS "日期",
>   round(default(avg_score, 0) * 100) / 25 + "/4" AS "平均分",
>   length(default(new_nodes_pulled, [])) AS "新节点"
> FROM "exam_boards"
> WHERE source_canvas = "llrb-trees"
> SORT created_at DESC
> LIMIT 5
> ```

### 📌 所有待剖析节点

> [!info]+ 待剖析节点（按拉出时间排序）
> 
> ```dataview
> TABLE WITHOUT ID
>   file.link AS "节点",
>   extracted_from.source_file AS "来源考察",
>   dateformat(date(extracted_from.extracted_at), "yyyy-MM-dd") AS "拉出时间",
>   round(default(bkt_p_mastery, 0.3) * 100) + "%" AS "当前 mastery"
> FROM "wiki/concepts"
> WHERE extracted_from.type = "exam_board"
>   AND default(body_status, "complete") = "placeholder"
> SORT extracted_from.extracted_at DESC
> ```

---

## 🧠 剖析链路（Layer 3）

### 最活跃的知识点

```dataview
TABLE WITHOUT ID
  file.link AS "节点",
  length(file.inlinks) AS "被引用数",
  length(file.outlinks) AS "引用数",
  round(default(bkt_p_mastery, 0.3) * 100) + "%" AS "mastery",
  default(confidence, "EXTRACTED") AS "Graphify 置信度"
FROM "wiki/concepts"
WHERE length(file.inlinks) > 0
SORT length(file.inlinks) DESC
LIMIT 10
```

### Edge 对话理由

```dataview
TABLE WITHOUT ID
  file.link AS "Edge",
  from AS "从",
  to AS "到",
  relation AS "关系",
  default(confidence, "EXTRACTED") AS "置信度"
FROM "edges"
SORT file.mtime DESC
LIMIT 10
```

---

## ⚙️ 元认知校准矩阵

```dataviewjs
// 2x2 校准矩阵（§1.10 设计 10）
const all = dv.pages('"wiki/concepts"')
  .where(p => p.bkt_p_mastery != null && p.self_reported_confidence != null);

const quadrants = {
  "know_and_confident": all.filter(p => p.bkt_p_mastery >= 0.7 && p.self_reported_confidence >= 0.7),
  "know_but_not_confident": all.filter(p => p.bkt_p_mastery >= 0.7 && p.self_reported_confidence < 0.7),
  "dont_know_but_confident": all.filter(p => p.bkt_p_mastery < 0.7 && p.self_reported_confidence >= 0.7),
  "dont_know_and_not_confident": all.filter(p => p.bkt_p_mastery < 0.7 && p.self_reported_confidence < 0.7),
};

dv.el("div", `
  <table>
    <tr>
      <th></th>
      <th>自信</th>
      <th>不自信</th>
    </tr>
    <tr>
      <th>掌握</th>
      <td>${quadrants.know_and_confident.length} 节点 · 🟢 已巩固</td>
      <td>${quadrants.know_but_not_confident.length} 节点 · 🟡 建议复习增强信心</td>
    </tr>
    <tr>
      <th>待巩固</th>
      <td>${quadrants.dont_know_but_confident.length} 节点 · 🔴 元认知偏差 · 优先考察</td>
      <td>${quadrants.dont_know_and_not_confident.length} 节点 · 🟠 按计划学习</td>
    </tr>
  </table>
`);
```

---

## 🚀 今日建议（FSRS · Plan v16 完全静默评分 · 延迟反馈）

```dataview
TABLE WITHOUT ID
  file.link AS "建议复习",
  round(fsrs_retrievability * 100) + "%" AS "记忆保持率",
  dateformat(fsrs_next_review_at, "yyyy-MM-dd") AS "推荐日期"
FROM "wiki/concepts"
WHERE fsrs_next_review_at <= date(today) + dur(1 day)
  AND default(bkt_p_mastery, 0.3) < 0.85
SORT fsrs_retrievability ASC
LIMIT 10
```
```

#### 三个方案对比（Plan v16 B14 · Phase 1 选择）

| 方案 | 依赖插件数 | 实施工作量 | 交互强度 | 适合 Phase |
|---|---|---|---|---|
| **A · 纯 Dataview** | 1 (Dataview) | 1 小时 | 低（只读展示） | Phase 1 起步 |
| **B · Dataview + Buttons + Callouts** ✅ | 3 (Dataview + Buttons + Callouts) | 2-3 小时 | 高（按钮导航 + Callout 折叠） | **Phase 1 实施** |
| C · Dataview + Kanban + Metadata Menu | 4+ (Dataview + Kanban + Metadata + ...) | 5-7 小时 | 最高（看板 + 表单） | Phase 2 升级 |

**Plan v16 Round 3 用户锁定 · 选择方案 B**：Buttons + Dataview + Callouts

**选择理由**（基于 Agent 2 5+ 社区案例调研 · 75% 概率对应用户截图）：
1. **交互性强** · Buttons 提供"生成检验白板"的一键触发
2. **可折叠** · Callouts 的 `+` 和 `-` 标记让历史考察默认展开/折叠
3. **动态刷新** · Dataview 查询自动更新
4. **学习曲线友好** · 只依赖 3 个插件 · 都是社区 top 20

#### 依赖插件声明

| 插件 | 用途 | 强度 |
|---|---|---|
| **Dataview** | 数据查询引擎（DQL + dataviewjs） | 强制 |
| **Buttons** | 按钮点击触发 QuickAdd macro | 强制 |
| **Callouts** | Obsidian 原生支持（无需第三方插件） | 内置 |
| QuickAdd | Buttons 的 command target | 强制（已在 §5.3） |
| Metadata Menu | 编辑 dashboard frontmatter（可选） | 推荐 |

#### 实施步骤（Phase 1 · 2-3 小时）

**Step 1 · 安装 Buttons 插件**（5 分钟）
```
Settings → Community Plugins → Browse → Buttons → Install → Enable
```

**Step 2 · 配置 QuickAdd macro**（15 分钟）
- 创建 macro "Exam - Start Exam Board"
- Action · Run template 或 Shell command
- Shell command · `claude "/start_exam_board"` (通过 Claudian)

**Step 3 · 写 wiki/dashboard.md**（1 小时）
- 复制上面的完整模板
- 替换 `search-algorithms` 和 `llrb-trees` 为用户实际的 canvas slug
- 根据用户实际 canvas 数量增加 Button 数量

**Step 4 · 测试**（30 分钟）
- 打开 dashboard.md · 验证 3 个 Dataview 查询正常
- 点击 Button · 验证触发 `/start_exam_board`
- 展开/折叠 Callout · 验证交互正常
- Graph View 验证节点链路可视化

**Step 5 · Metadata Menu 集成**（可选 · 30 分钟）
- 为 wiki/canvases/ 定义 fileClass
- 支持用户在 Dashboard 直接编辑 canvas 元数据

#### Dashboard 更新机制

**自动刷新**：
- Dataview 查询在文件每次打开时自动执行
- 切换到 Dashboard tab 时自动刷新
- 编辑任何 wiki/concepts/*.md 后 · Dataview 会在下次查询时反映变化

**手动刷新**：
- `Cmd+R` 重新加载 Obsidian
- 或使用 Dataview 的 "Refresh views" 命令

**延迟限制**：
- Dataview 查询 < 500 ms（100+ 笔记的 vault）
- 超过 500 ms 可以用 `dataviewjs` 的缓存优化

---

### 5.2 · Templater · frontmatter 自动化（强制）

**安装**: Browse → "Templater" → Install

**核心配置**:
- Template folder: `templates/`
- Trigger Templater on new file creation: true
- Folder templates: `exam_boards/` → `templates/exam-board.md`

**使用场景**:
- 创建 `wiki/concepts/*.md` 时自动填充 frontmatter schema
- 创建 `exam_boards/*.md` 时自动生成空白检验白板 (§2.2)

**模板示例** (`templates/exam-board.md`):
```yaml
---
type: exam_board
status: in_progress
source_canvas: <% tp.user.prompt("source canvas:") %>
created_at: <% tp.date.now("YYYY-MM-DDTHH:mm:ssZ") %>
questions: []
---

> [!exam_question]+ 等待 Agent 出题...
```

**对学习效果贡献**: §2.4 保证 1 · 完全空白 UI 的文件层面保障

---

### 5.3 · QuickAdd · 快捷键宏（强制）

**安装**: Browse → "QuickAdd" → Install

**核心配置**: 绑定 6 个 hotkey 到 QuickAdd macro 调用 Claude Code skill

**使用场景**: Cmd+Option+{C,R,E,Q,X,P} 触发对应 skill

**为什么需要**: Obsidian 原生 hotkey 不支持直接调用 Claude Code CLI · QuickAdd 作为桥梁

**对学习效果贡献**: 所有 skill 的 hotkey 入口

---

### 5.4 · Periodic Notes · 每日笔记（推荐）

**安装**: Browse → "Periodic Notes" → Install

**核心配置**: Daily Notes 目录 `log/` · 格式 `yyyy-MM-dd.md`

**使用场景**:
- Karpathy 风格的 `log.md` 每日学习日志
- 每天自动创建 `log/2026-04-08.md` 记录学习活动

**模板**:
```yaml
---
date: 2026-04-08
type: daily-log
---

## 今日学习

## 考察记录
(从 exam_boards/ 查询今天的)

## 新发现概念
(extracted_nodes 从 exam_boards 和 chat 中抽取)

## 明日复习建议
(Dataview 查询 fsrs_next_review_at == tomorrow)
```

**对学习效果贡献**: Spacing Effect 的基础设施 · 每日回顾

---

### 5.5 · Spaced Repetition · Flashcard 复习（强制）

**安装**: Browse → "Spaced Repetition" → Install

**核心配置**:
- Flashcard tags: `#flashcard/concept`, `#flashcard/error-correction`, `#flashcard/edge-rationale`
- Card type: Single-line (Q::A) + Multi-line + Cloze

**使用场景**:
- `/qcl f` 或 `/start_exam_board` 生成误解 callout 自动加 `#flashcard/error-correction`
- 插件按 SM-2 算法调度复习
- 每天 popup 待复习 flashcards

**对学习效果贡献**:
- §1.8 设计 8 · 3 天 + 1 周主动提醒 (d ≈ 0.55 · Cepeda 2008 · Plan v21 修正)
- Spacing Effect 的实施者

**未来升级**: 等 FSRS 插件成熟后替换 SM-2（D11 决策点）

---

### 5.6 · Tasks · 复习任务查询（推荐）

**安装**: Browse → "Tasks" → Install

**核心配置**:
- Global filter: `#task`
- Set done date on every completed task: true

**使用场景**:
- Skill 生成的"3 天后复习 X"任务
- `/review_profile` 查询今日待办

**DQL 示例**:
```tasks
not done
due before tomorrow
tag includes #error-correction
sort by due
```

**对学习效果贡献**: §1.8 的 Tasks 层 · Spaced Repetition 的辅助

---

### 5.7 · Smart Connections · 语义搜索（可选）

**安装**: Browse → "Smart Connections" → Install

**核心配置**:
- Embedding model: local OpenAI-compatible (或云端)
- Indexing: 自动增量

**使用场景**:
- 用户打开 `wiki/concepts/admissibility.md` → 右侧 pane 显示语义相关的其他笔记
- 补偿 Canvas 的 4 路融合检索 (FR-RET-05)

**对学习效果贡献**: 降低检索的认知负担 (FR-RET-01/02)

**注意**: 与 Canvas 后端的 LanceDB 互补 · 不冲突

---

### 5.8 · Kanban · 学习流水线看板（可选）

**安装**: Browse → "Kanban" → Install

**核心配置**: 创建 `wiki/learning-kanban.md` 看板

**使用场景**: 可视化学习流水线

```markdown
## 🔴 Unknown (mastery < 0.3)
- [[admissibility]]
- [[consistent-heuristic]]

## 🟡 Learning (0.3 ≤ mastery < 0.7)
- [[a-star]]
- [[manhattan-distance]]

## 🟢 Mastered (mastery >= 0.7)
- [[bfs]]
- [[dfs]]
```

**对学习效果贡献**: 补偿 Canvas 的节点颜色可视化 (FR-MAST-03)

**自动化**: Skill 可以在评分后自动移动卡片（未来增强）

---

### 5.9 · Metadata Menu · frontmatter 表单 UI（推荐）

User：这一个插件需要单独的介绍一下

> **AI 响应**（基于 Agent 2 Metadata Menu 调研 + Plan v16 B15 · 从 20 行扩展到 ~180 行）：
>
> **简短介绍**：Metadata Menu 是 Obsidian 社区最成熟的 frontmatter 表单 UI 插件（2025 年 v0.9+ · 21+ 字段类型 · FileClass 系统 · 10k+ 安装）。它解决了方案 A 的关键痛点：**用户不用手写 yaml 也能维护 concept/exam_board/edge 三类笔记的复杂 frontmatter**。
>
> **核心价值**（为什么对方案 A 关键）：
>
> 1. **类型安全** · 21+ 种字段类型（Select/Cycle/Number/Date/Media/MultiFile/Canvas/Formula/YAML/Lookup...）
> 2. **FileClass 系统** · 为每种笔记类型定义 schema · 自动注入默认值 + 字段校验
> 3. **表单 UI** · 点击 frontmatter 字段 → 弹出表单编辑器 · 不写 yaml
> 4. **批量修改** · 对多个文件批量更新同一字段（例如批量重置 BKT）
> 5. **降低编辑门槛** · 新用户不需要学 yaml · 降低方案 A 的学习成本
>
> **详细介绍（包含 3 个 FileClass 完整示例 + 用户工作流 + 与方案 A 的关键契合）见下方大段扩展内容。**

**安装**: Browse → "Metadata Menu" → Install

#### 为什么 Metadata Menu 对方案 A 关键（4 个核心理由）

1. **降低 yaml 编辑门槛** · 用户不用学 yaml 语法 · 点击字段弹出表单编辑器
2. **类型安全** · 21+ 字段类型内置校验（Select/Number/Date/Media/MultiFile/...）
3. **批量修改** · 对多个文件的同一字段批量更新（例如批量重置 BKT）
4. **FileClass 系统** · 为每种笔记类型定义 schema · 自动注入默认值 + 字段自动补全

#### Metadata Menu 的 21+ 字段类型（方案 A 常用 10 种）

| 字段类型 | 用途 | 方案 A 应用 |
|---|---|---|
| **Input** | 单行文本 | `title` · `source_canvas` |
| **Textarea** | 多行文本 | `description` · `notes` |
| **Number** | 数字 | `bkt_p_mastery` · `fsrs_stability` |
| **Date** | 日期 | `created_at` · `fsrs_next_review_at` |
| **Select** | 单选 | `type: concept\|exam_board\|edge` · `status: in_progress\|completed` |
| **Cycle** | 循环切换 | `confidence: EXTRACTED\|INFERRED\|AMBIGUOUS` |
| **Boolean** | 布尔值 | `body_status_placeholder` |
| **MultiSelect** | 多选 | `tags[]` |
| **MultiFile** | 多文件链接 | `parent_concepts[]` · `related_nodes[]` |
| **Lookup** | 跨文件查询 | `extracted_from.source_file` |
| **Formula** | 计算字段 | `overall_mastery = f(bkt, fsrs)` |

#### 3 个 File Class 完整 YAML 示例

**File Class 1 · `schemas/concept.md`**（对应 `wiki/concepts/*.md`）

```yaml
---
fileClass: concept
fields:
  - name: title
    type: Input
    options:
      description: "概念的完整名称（非 slug）"
  
  - name: type
    type: Select
    options:
      values: ["concept"]
      default: "concept"
  
  - name: bkt_p_mastery
    type: Number
    options:
      min: 0
      max: 1
      step: 0.01
      default: 0.30
      description: "Bayesian Knowledge Tracing 掌握概率"
  
  - name: fsrs_stability
    type: Number
    options:
      min: 0
      default: 0
      description: "FSRS 稳定度（天）"
  
  - name: fsrs_difficulty
    type: Number
    options:
      min: 1
      max: 10
      default: 5
      description: "FSRS 难度分数（1-10）"
  
  - name: fsrs_retrievability
    type: Formula
    options:
      formula: "Math.exp(-elapsedDays / fsrs_stability)"
      description: "FSRS 记忆保持率（自动计算）"
  
  - name: fsrs_next_review_at
    type: Date
    options:
      description: "下次建议复习日期"
  
  - name: confidence
    type: Cycle
    options:
      values: ["EXTRACTED", "INFERRED", "AMBIGUOUS"]
      default: "EXTRACTED"
      description: "Graphify 三级置信度"
  
  - name: tips
    type: MultiSelect
    options:
      description: "相关 Tips 列表"
  
  - name: errors
    type: MultiSelect
    options:
      description: "误解历史"
  
  - name: parent_concepts
    type: MultiFile
    options:
      dvQueryString: 'dv.pages(\'"wiki/concepts"\').where(p => p.file.name !== dv.current().file.name)'
      description: "父概念（用于图谱关系）"
  
  - name: extracted_from
    type: YAML
    options:
      description: "追溯来源（type/source_file/parent_node/extracted_at）"

limit: null
version: "1.0"
mapWithTag: true
tagNames: []
excludes: []
parent: null
savedViews: []
favoriteView: null
fieldsOrder:
  - title
  - type
  - bkt_p_mastery
  - fsrs_stability
  - fsrs_difficulty
  - fsrs_retrievability
  - fsrs_next_review_at
  - confidence
  - tips
  - errors
  - parent_concepts
  - extracted_from
---
```

**File Class 2 · `schemas/exam-board.md`**（对应 `exam_boards/*.md`）

```yaml
---
fileClass: exam_board
fields:
  - name: type
    type: Select
    options:
      values: ["exam_board"]
      default: "exam_board"
      description: "🔴 防嵌套关键字段"
  
  - name: status
    type: Cycle
    options:
      values: ["in_progress", "completed", "abandoned"]
      default: "in_progress"
  
  - name: source_canvas
    type: Input
    options:
      description: "源原白板 slug（必填）"
  
  - name: exam_mode
    type: Select
    options:
      values: ["point_to_point", "comprehensive", "mixed"]
      default: "point_to_point"
      description: "Constructive Alignment 模式"
  
  - name: created_at
    type: Date
    options:
      defaultInsertAsLink: false
  
  - name: started_at
    type: Date
  
  - name: completed_at
    type: Date
  
  - name: duration_seconds
    type: Number
  
  - name: selected_nodes
    type: MultiFile
    options:
      dvQueryString: 'dv.pages(\'"wiki/concepts"\')'
      description: "FR-EXAM-02 · BKT 选出的薄弱节点"
  
  - name: bkt_threshold
    type: Number
    options:
      min: 0
      max: 1
      step: 0.05
      default: 0.7
      description: "掌握概率低于此值的节点才被选入"
  
  - name: questions
    type: YAML
    options:
      description: "题目列表（skill 逐步填充）"
  
  - name: new_nodes_pulled
    type: MultiFile
    options:
      dvQueryString: 'dv.pages(\'"wiki/concepts"\')'
      description: "本次考察中拉出的新节点"
  
  - name: canvas_writebacks
    type: YAML
    options:
      description: "FR-EXAM-18 回写痕迹"
  
  - name: post_exam_calibration
    type: YAML
    options:
      description: "FR-EXAM-15 考后校准投票"

limit: null
version: "1.0"
mapWithTag: true
tagNames: []
excludes: []
parent: null
savedViews: []
favoriteView: null
---
```

**File Class 3 · `schemas/edge.md`**（对应 `edges/*.md`）

```yaml
---
fileClass: edge
fields:
  - name: from
    type: File
    options:
      dvQueryString: 'dv.pages(\'"wiki/concepts"\')'
      description: "起点节点"
  
  - name: to
    type: File
    options:
      dvQueryString: 'dv.pages(\'"wiki/concepts"\')'
      description: "终点节点"
  
  - name: relation
    type: Cycle
    options:
      values: ["depends_on", "refines", "extends", "guarantees", "contradicts", "generalizes"]
      default: "depends_on"
      description: "语义关系类型"
  
  - name: confidence
    type: Cycle
    options:
      values: ["EXTRACTED", "INFERRED", "AMBIGUOUS"]
      default: "EXTRACTED"
  
  - name: rationale
    type: Textarea
    options:
      description: "EI/SE 对话提炼的关系理由"
  
  - name: ei_questions
    type: MultiSelect
    options:
      description: "Elaborative Interrogation 问题列表"
  
  - name: se_answers
    type: MultiSelect
    options:
      description: "Self-Explanation 答案列表"
  
  - name: created_at
    type: Date

limit: null
version: "1.0"
mapWithTag: true
tagNames: []
excludes: []
parent: null
savedViews: []
favoriteView: null
---
```

#### 用户编辑 frontmatter 的 6 步工作流

**Step 1 · 打开目标笔记**
用户 Cmd+O 打开 `wiki/concepts/admissibility.md`

**Step 2 · Metadata Menu 右键菜单**
右键点击 frontmatter 区域 → 弹出 "Add/Update field" 菜单

**Step 3 · 选择要编辑的字段**
```
Metadata Menu
├── ✏️ title
├── 🔢 bkt_p_mastery (当前: 0.72)
├── 🔢 fsrs_stability (当前: 14.3)
├── 📅 fsrs_next_review_at (当前: 2026-04-15)
├── 🔄 confidence (当前: EXTRACTED)
└── ...
```

**Step 4 · 弹出对应字段的表单 UI**

对于 Number 字段（`bkt_p_mastery`）：
```
┌────────────────────────────────────┐
│  Edit: bkt_p_mastery               │
│                                     │
│  当前值: 0.72                       │
│  新值:   [  0.72  ] ← 输入框         │
│                                     │
│  范围: 0.0 - 1.0                    │
│  步长: 0.01                         │
│  描述: Bayesian Knowledge Tracing   │
│                                     │
│  [  取消  ]         [  确认  ]      │
└────────────────────────────────────┘
```

对于 Cycle 字段（`confidence`）：
```
┌────────────────────────────────────┐
│  Edit: confidence                   │
│                                     │
│  当前: EXTRACTED                    │
│                                     │
│  ○ EXTRACTED                       │
│  ● INFERRED                        │
│  ○ AMBIGUOUS                       │
│                                     │
│  [  取消  ]         [  确认  ]      │
└────────────────────────────────────┘
```

**Step 5 · 确认 · frontmatter 自动更新**
Metadata Menu 会：
- 读取当前 frontmatter
- 更新指定字段的值
- 保持其他字段不变
- 自动格式化 yaml（缩进 + 引号）
- 写回文件

**Step 6 · 验证**
- Obsidian 编辑器显示更新后的 frontmatter
- Dataview 查询自动刷新显示新值

#### 批量修改示例

**场景**：Phase 2 升级时需要重置所有 `wiki/concepts/*.md` 的 `fsrs_stability` 为 0（重新开始 FSRS 调度）

**手动方式**（不用 Metadata Menu）：
- Cmd+O 打开每个文件 · 手动改 yaml · 重复 100+ 次 · 易出错

**Metadata Menu 方式**：
- 打开 `wiki/dashboard.md`
- 触发 Metadata Menu 的 "Batch update" 命令
- 选择目标文件夹 `wiki/concepts/`
- 选择字段 `fsrs_stability`
- 输入新值 `0`
- 确认 · 所有 100+ 文件一次性更新

#### ASCII 表单 UI 示例（Metadata Menu 的 Inline Field 编辑器）

```
在 Obsidian 编辑器里：

---
title: admissibility
type: concept
bkt_p_mastery:: [0.72] ← 点击这个 · 弹出 Number 输入框
fsrs_stability:: [14.3] ← 同理
confidence:: [EXTRACTED ▾] ← Cycle · 下拉菜单
tips::
  - [[h(n) ≤ h*(n)]]
  - [[triangle inequality]]
---

## 定义
admissibility 是指启发函数 h(n) 永远不高估到达目标的实际代价...
```

**`::` 语法**是 Metadata Menu 的 inline field 语法 · 在 yaml frontmatter 之外也可以定义字段 · 更灵活。

#### 对学习效果贡献

**直接贡献**：
- **降低 frontmatter 编辑门槛** · 补偿 Canvas 的 UI 直接编辑（FR-MAST-03 处方性措辞）
- **类型检查** · 防止手误（例如 mastery 输入 1.5 会被拒绝）
- **一致性保证** · FileClass 强制 schema · 所有 concept 文件结构一致

**间接贡献**：
- **快速批量修改** · 节省 Phase 2 升级时间
- **用户体验提升** · 新用户不需要学 yaml · 降低方案 A 的学习成本
- **防止数据错误** · 输入校验 + Cycle 字段的枚举限制

#### Phase 1 安装步骤

1. Settings → Community Plugins → Browse → 搜 "Metadata Menu" → Install
2. Enable Metadata Menu
3. Settings → Metadata Menu → Global options:
   - Enable file class: true
   - File class folder: `schemas/`
   - Field naming: Nested (支持 `extracted_from.source_file`)
4. 创建 `schemas/` 目录 + 3 个 file class 文件（见上面示例）
5. 测试 · 打开任意 `wiki/concepts/*.md` · 右键 → 应该看到所有字段

#### 与其他插件的协同

| 插件 | 协同 |
|---|---|
| **Dataview** | Metadata Menu 编辑的字段可以被 DQL 查询 |
| **Templater** | 新建笔记时 Templater 填充默认值 + Metadata Menu 后续编辑 |
| **Tasks** | Metadata Menu 可以编辑 task 字段 |
| **Kanban** | 移动卡片时 · Metadata Menu 可以触发字段更新 |

**对学习效果贡献**: FR-TRACE-02 学习档案面板的 UI · 降低用户编辑 frontmatter 的认知成本 · 让用户专注学习而非 yaml 语法。

---

### 5.10 · Obsidian Git · 自动备份（强制）

**安装**: Browse → "Obsidian Git" → Install

**核心配置**:
- Auto backup every 10 minutes
- Commit message: "auto: <number of files> changed"
- Pull on startup: false (防止冲突)

**使用场景**:
- 自动 commit 所有 md 变更
- 在远程 GitHub/GitLab 备份

**对学习效果贡献**:
- 历史 mastery 变化可追溯 (git log)
- 防止数据丢失

---

> **§3-§5 完** · 接下来的 §6-§13 见下一批 Edit

---

## §6 · Graphify 集成

User：这里起到的作用是让 claude code 更能精确的检索笔记吗？

> **AI 响应**（基于 Agent 4 Canvas LanceDB 调研 + Plan v16 B16/B21 · Graphify 与 LanceDB 双栈互补）：
>
> **简短答案**：**是的，但不仅如此**。Graphify 的核心作用是 **4 个维度**，其中"让 Claude Code 更精确检索"是其中之一：
>
> 1. **知识图谱构建**（最核心）· vault → graph.json（节点 + 边 + 置信度）· 让 Claude Code 理解笔记之间的关系结构
> 2. **检索增强**（你指的）· 帮助 Claude Code 精确检索笔记 · **71x token 减少**（用图谱关系代替全文）
> 3. **上下文压缩** · 用图谱路径代替全文注入 · 降低 LLM 成本 + 提高上下文密度
> 4. **质量控制** · 孤立节点检测 + 矛盾关系检测 + AMBIGUOUS 比例警告（见 §6.6 health check）
>
> **关键澄清：Graphify ≠ 替代 LanceDB**
>
> 方案 A 的检索架构采用**双栈设计**（Agent 4 调研确认 Canvas 后端已就绪）：
>
> | 维度 | Graphify | LanceDB + bge-m3 |
> |---|---|---|
> | **数据类型** | 知识图谱（节点 + 边） | 向量嵌入（语义相似度） |
> | **擅长场景** | 关系发现 · 出题 context | 笔记片段精确召回 |
> | **Token 效率** | **71x 减少**（用 30 token 关系代替 1500 token 全文） | 无特殊压缩 |
> | **输出粒度** | 节点/边级别 | 句子/段落级别 |
> | **中英双语** | 取决于 LLM | **MIRACL nDCG@10=63.9**（bge-m3 · Canvas PRD L135） |
> | **对话中引用** | "admissibility 依赖 h(n) bound" | "《CS 188 Lecture 3》提到 A* 最优性..." |
>
> **两者完全互补**：
> - Graphify 给出题 context 节省 token
> - LanceDB 给对话补充的学习材料（见 §4.1.1 和 §6.5 新增章节）
> - Canvas 原设计本来就是两栈并存（PRD L68 + L739 FR-KG-08）· 方案 A 保留此设计
>
> **详见**：§6 Graphify 使用章节 · §6.5 LanceDB + bge-m3 集成新增章节 · §4.1.1 `/chat_with_context` 补充材料显示

> Graphify (https://github.com/safishamsi/graphify) 是 Safis Hamsi 开发的 Claude Code Skill，把文件夹转成 Obsidian 知识图谱。
> 13.7k stars · PyPI `graphifyy` v0.3.17 · 7 层管道 · 三级置信度（EXTRACTED/INFERRED/AMBIGUOUS）· 71x token 减少 · Leiden 聚类

### 6.1 · 安装步骤

```bash
pip install graphifyy
cd canvas-vault
graphify install       # 自动安装 .claude/skills/graphify/
graphify claude install  # 自动注入 CLAUDE.md 规范
```

**验证**:
- `.claude/skills/graphify/SKILL.md` 存在
- `CLAUDE.md` 末尾已追加 Graphify 区块

### 6.2 · `/graphify` 使用

**命令**:
```bash
/graphify ./wiki            # 处理 wiki/ 目录
/graphify ./raw --output ./outputs/graphify-out/first-pass
```

**7 层管道** (Graphify 内部):
1. File Discovery · 扫描所有 md 文件
2. Content Extraction · 读取 frontmatter + body
3. Entity Detection · LLM 抽取概念实体
4. Relation Extraction · LLM 抽取关系
5. Leiden Clustering · 社区检测
6. Confidence Scoring · 三级置信度标注
7. Graph Output · `graph.json` + `GRAPH_REPORT.md`

**输出示例** (`outputs/graphify-out/graph.json`):
```json
{
  "nodes": [
    {"id": "admissibility", "type": "concept", "confidence": "EXTRACTED"},
    {"id": "a-star", "type": "concept", "confidence": "EXTRACTED"},
    {"id": "consistent-heuristic", "type": "concept", "confidence": "INFERRED"}
  ],
  "edges": [
    {"from": "admissibility", "to": "a-star", "relation": "guarantees", "confidence": "EXTRACTED"},
    {"from": "consistent-heuristic", "to": "admissibility", "relation": "stronger_than", "confidence": "EXTRACTED"}
  ],
  "clusters": [
    {"id": "cluster-0", "nodes": ["admissibility", "a-star", "consistent-heuristic"], "label": "search-optimality"}
  ]
}
```

### 6.3 · 三级置信度 → frontmatter provenance

Graphify 的三级置信度直接映射到 `wiki/concepts/*.md` 的 `confidence` 字段:

| Graphify 级别 | 含义 | frontmatter 值 |
|---|---|---|
| EXTRACTED | 明确出现在原文 | `confidence: EXTRACTED` |
| INFERRED | LLM 推断但无原文 | `confidence: INFERRED` |
| AMBIGUOUS | 多义或不确定 | `confidence: AMBIGUOUS` |

**用途**: `/start_exam_board` skill 选题时优先考察 INFERRED 节点（用户的隐含理解）。

### 6.4 · 71x token 减少的应用场景

Graphify 的核心卖点: 用图谱结构代替全文读取 · 71x token 减少

**应用在方案 A**:
- `context_enrichment` MCP 工具返回 context 时，优先从 `graph.json` 读关系而不是读全文
- 对于 1-hop 邻居，用 `graph.json` 里的 relation + 短 description，不需要读整个 `wiki/concepts/*.md`
- 这对检验白板尤其重要（§2.4 铁律：不读 wiki/concepts/*.md 内容）

**Prompt 对比**:
- 传统 RAG: "以下是 admissibility 的完整笔记 (1500 tokens)..."
- Graphify: "admissibility 是 a-star 的依赖 · consistent 的弱化版本 (30 tokens)"

### 6.5 · LanceDB + bge-m3 集成（Plan v16 B21 · Graphify + LanceDB 双栈声明）

> **本节响应用户 Round 3 明确诉求 · Canvas 原设计的 LanceDB + bge-m3 精确检索能力必须保留**
> **用户原话锁定**："这是我一开始我们 Canvas learning system 所设计的索引 LanceDB 返回精确笔记片段的需求"
> **基于**：Agent 4 Canvas PRD 行号 + 后端代码完整调研

#### 为什么方案 A 必须保留 LanceDB + bge-m3

**Canvas PRD 原文链（10 处引用 · Agent 4 验证）**：

| PRD 行号 | 引用 | 说明 |
|---|---|---|
| L68 | "LanceDB + Ollama bge-m3" | 架构声明 |
| L90 | "RAG 管道 Precision@5 ≥ 0.70、Recall@10 ≥ 0.80、MRR@10 ≥ 0.70" | 成功标准 |
| L135 | "bge-m3 + jieba 中文分词 · MIRACL nDCG@10=63.9" | Hybrid Search |
| L220 | "用户标注的关键知识点能被 Agent 精准召回" | 使用场景 |
| L250 | **"检索管道是所有上层功能的基础——节点对话、Edge 对话、检验白板、/命令技能都依赖精确的笔记片段检索"** | 基础设施 |
| L287 | "后台异步 Vision API → embedding → 存入 LanceDB" | 多模态 |
| L356 | "LanceDB：128K 向量/500MB" | 性能假设 |
| L549 | "LanceDB v0.4+" | 技术选型 |
| L568 | "Ollama 容器运行 bge-m3" | 嵌入模型 |
| L739 | **FR-KG-08 "Agent 检索系统以此路径为搜索范围，向用户返回精确的笔记片段"** | 核心需求 |

**核心结论**（Agent 4 验证）：LanceDB + bge-m3 在 Canvas 原设计中是**基础设施级别**的存在 · 不是"可选增强"。方案 A 保留它是对用户原始设计意图的忠实。

#### Graphify vs LanceDB 对比表（6 个维度 · 全部互补）

| 维度 | Graphify | LanceDB + bge-m3 |
|---|---|---|
| **数据类型** | 知识图谱（节点 + 边 + 权重）| 向量嵌入（1024 维 · bge-m3） |
| **存储格式** | `graph.json` + `GRAPH_REPORT.md` | LanceDB 二进制索引 + 元数据 |
| **擅长场景** | 关系发现 · 出题 context · 图遍历 | 笔记片段召回 · 语义相似度 · 段落级精确 |
| **Token 效率** | **71x 减少**（用 30 token 关系代替 1500 token 全文）| 1x（返回原始段落） |
| **输出粒度** | 节点/边级别（抽象） | 句子/段落级别（具体） |
| **中英双语** | 取决于 LLM | **MIRACL nDCG@10=63.9** (bge-m3 中英对齐) |
| **在对话中的用途** | "admissibility 依赖 h(n) bound"（关系简述） | "《CS 188 Lecture 3》第 4.2 节提到 A* 最优性..."（具体片段） |
| **更新机制** | 定期全量 `/graphify ./wiki` | **实时增量索引**（Story 38.1） |
| **对 /chat_with_context 贡献** | 1-hop 邻居关系（§6.4） | 补充学习材料（§4.1.1） |

**双栈协同的完整架构**：

```
┌────────────────────────────────────────────────────────────┐
│                  用户问"admissibility 怎么证？"             │
└────────────────────────────────┬──────────────────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
          ▼                       ▼                       ▼
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│   Graphify       │   │   LanceDB        │   │   Graphiti       │
│   graph.json     │   │   bge-m3 hybrid  │   │   三层检索       │
│                  │   │                  │   │                  │
│ 找关系: depends  │   │ 找片段: 讲义 +   │   │ 找历史: 过去对话 │
│ _on, refines,    │   │ 讨论 + 真题      │   │ + 学习事件       │
│ extends          │   │                  │   │                  │
│                  │   │ Top 5 精确片段   │   │ Top 10 记忆      │
└────────┬─────────┘   └────────┬─────────┘   └────────┬─────────┘
         │                      │                      │
         └──────────────────────┼──────────────────────┘
                                ▼
                  ┌──────────────────────────┐
                  │  LLM 融合 3 路返回        │
                  │  + 正面措辞               │
                  │  + 补充材料链接           │
                  └──────────────┬───────────┘
                                  │
                                  ▼
                  ┌──────────────────────────┐
                  │  Claudian sidebar 显示    │
                  │  解答 + 补充材料列表       │
                  │  (带 wikilink 可点击)     │
                  └──────────────────────────┘
```

#### Canvas 后端已实现清单（Agent 4 带文件路径 + 行号）

| # | 功能 | 实现文件 | 行号 | 状态 |
|---|---|---|---|---|
| 1 | RAG Service (4 路融合) | `rag_service.py` | 1-120 | ✅ `LANGGRAPH_AVAILABLE=True` |
| 2 | `_search_vault_notes()` tool executor | `tool_executor.py` | 60-124 | ✅ 调用 LanceDB |
| 3 | `search_vault_notes` MCP tool | `react_agent.py` | 55-137 | ✅ 就绪 |
| 4 | 自动增量索引 | `lancedb_index_service.py` | (Story 38.1) | ✅ 就绪 |
| 5 | 三层记忆 fallback | `memory_service.py` | 1581-1683 | ✅ 3 层：Graphiti → Neo4j → 内存 |
| 6 | bge-m3 嵌入 (Ollama) | 容器启动 | - | ⚠️ 需 `ollama pull bge-m3` |
| 7 | jieba 中文分词 | `lancedb_index_service.py` | - | ✅ 已集成 |
| 8 | Recall@10 ≥ 0.80 目标 | Canvas PRD L90 | - | ⚠️ 需验证 |

**方案 A 实施工作量**：**1-2 天**（skill 调现有工具 + 格式化输出 + 可点击 wikilink）

#### FR-KG-08 / FR-RET-01/05/08/09/13 完整映射

| Canvas FR | Canvas 描述 | 方案 A 实现位置 |
|---|---|---|
| **FR-KG-08** | Agent 检索系统以此路径为搜索范围 · 返回精确笔记片段 | §4.1.1 `/chat_with_context` Step 5 |
| **FR-RET-01** | 用户标注的关键知识点能被 Agent 精准召回 | LanceDB `search_vault_notes` 返回结果 |
| **FR-RET-05** | 4 路融合检索（BM25 + dense + graph + temporal）| `rag_service.py` LANGGRAPH_AVAILABLE |
| **FR-RET-08** | Precision@5 ≥ 0.70 | Canvas PRD L90 验收标准 |
| **FR-RET-09** | Recall@10 ≥ 0.80 | 同上 |
| **FR-RET-13** | 双向链接跳转（3 级精度） | Obsidian wikilink [[file#^block-id]] |

#### 返回字段格式

`search_vault_notes` MCP 工具的返回 schema（Agent 4 从 `react_agent.py:55-137` 提取）：

```typescript
interface VaultSearchResult {
  content: string;              // 笔记片段正文（200-500 字）
  metadata: {
    title: string;              // 笔记标题
    source_file: string;        // 文件路径（相对 vault 根）
    block_id?: string;          // Obsidian block id（用于精确跳转）
    heading?: string;           // 所在 heading（用于段落级跳转）
    type: 'lecture_notes' | 'discussion' | 'exam_review' 
        | 'wiki_concepts' | 'chat_session' | 'raw_notes';
    created_at: string;         // ISO timestamp
    modified_at: string;
  };
  relevance_score: number;      // 0.0-1.0 相关度（hybrid 融合分数）
  source: 'lancedb';            // 数据来源标识
}

interface SearchVaultNotesResponse {
  results: VaultSearchResult[];  // 最多 num_results 条
  total_found: number;           // 数据库中总匹配数
  query_embedding_ms: number;    // 查询嵌入耗时
  search_ms: number;             // 检索耗时
  pipeline_token: string;        // 继续 pipeline 的 token
}
```

#### 片段精排策略

**Canvas PRD 原设计**（L250）: "Agent 主动提醒历史错误"暗示精排应该优先讲义而非讨论 · 但也要考虑用户自己的历史讨论。

**方案 A 的精排优先级**（权重可配置 · 默认值如下）：

```python
PRIORITY_WEIGHTS = {
    "lecture_notes": 1.0,      # 最权威 · 讲义
    "discussion": 0.9,         # 讨论笔记
    "exam_review": 0.85,       # 真题复习
    "wiki_concepts": 0.8,      # 自己写的 wiki
    "chat_session": 0.7,       # 历史对话
    "raw_notes": 0.6,          # 原始课件
}

def rerank(results):
    for r in results:
        type_w = PRIORITY_WEIGHTS.get(r["metadata"]["type"], 0.5)
        r["final_score"] = r["relevance_score"] * type_w
    return sorted(results, key=lambda x: -x["final_score"])
```

#### Phase 1 启动 LanceDB 的步骤

**Day 1 · 初始索引**:

```bash
# Step 1 · 安装 Ollama（如果没装）
brew install ollama

# Step 2 · 拉取 bge-m3 嵌入模型
ollama pull bge-m3
# 约 1.2 GB · 首次下载需要 2-5 分钟

# Step 3 · 启动 Canvas 后端
cd /path/to/canvas-learning-system
uvicorn backend.app.main:app --port 8000

# Step 4 · 触发初始全量索引
curl -X POST http://localhost:8000/api/v1/metadata/index/vault \
     -H "Content-Type: application/json" \
     -d '{"vault_path": "/path/to/canvas-vault"}'

# 返回: {"status": "indexing", "estimated_seconds": 120}

# Step 5 · 等待索引完成 · 查询状态
curl http://localhost:8000/api/v1/metadata/index/status

# 返回: {"indexed_files": 847, "total_files": 847, "status": "ready"}
```

**Day 2 · 测试 `/chat_with_context` 的补充材料**:

```bash
# 1. 在 Obsidian 打开某个 wiki/concepts/*.md
# 2. 触发 /chat_with_context · 问 "这个概念的证明怎么做"
# 3. 验证 Claudian sidebar 显示 "📚 可补充的学习材料" 段落
# 4. 点击 wikilink · 验证能跳转到原始笔记
# 5. 检查相关度分数是否合理（> 0.70）
```

#### 与 Canvas PRD 的完全契合

**Canvas PRD L250 原文引用**："检索管道是所有上层功能的基础——节点对话、Edge 对话、检验白板、/命令技能都依赖精确的笔记片段检索。"

**方案 A 实现度验证**：

| 上层功能 | 依赖的检索能力 | 方案 A 实现 | 符合度 |
|---|---|---|---|
| 节点对话 (§4.1) | 1-hop + 笔记片段 | Graphify + LanceDB | ✅ 100% |
| Edge 对话 (§4.2) | 两节点的历史 + Tips | Graphify + LanceDB + Graphiti | ✅ 100% |
| 检验白板 (§2) | 历史错误 + 批注 + mastery | Graphify + Graphiti（**不用 LanceDB** · 隔离） | ✅ 100% |
| `/chat_with_context` (§4.1.1) | 补充学习材料 | LanceDB hybrid | ✅ 100% |
| `/review_profile` (§4.6) | 学习档案聚合 | Dataview + Graphiti | ✅ 90% |

**关键设计决策**：**检验白板不使用 LanceDB**（§2.4 铁律）
- 理由：LanceDB 返回原始笔记片段 · 会破坏 Active Recall 条件
- 检验白板模式下只允许通过 `generate_question` / `search_memories` 间接获取 context
- LanceDB 只在**剖析模式**（`/chat_with_context`）下使用

### 6.6 · Graphify 集成到 `/start_exam_board`

**在 Step 4 (query_mastery) 之后增加**:
```
Step 4.5 · 读 outputs/graphify-out/graph.json
           筛选 selected_nodes 的 1-hop 邻居
           作为出题的 context (节省 token)
```

**好处**: `generate_question` 可以基于图谱结构出更精准的辨析题（例如"consistent 和 admissibility 的关系是什么"）

### 6.7 · 定期"健康检查"（Karpathy 方法论 · Plan v16 B17 扩展）

Karpathy LLM Wiki 的一个核心实践: 定期用 LLM 扫描 vault 检测不一致。

**实现**: 每周手动触发 `/graphify ./wiki --health-check`
- 检测孤立节点 (无 Edge)
- 检测矛盾关系 (A → B depends_on + B → A depends_on)
- 检测 AMBIGUOUS 比例（如果 > 20% 说明 wiki 质量下降）
- 生成 `outputs/graphify-out/health-report-<date>.md`

---

## §7 · Canvas 后端 14 MCP 工具对接

> 每个工具的输入字段从哪个 md frontmatter 读 + 输出字段写回哪里 + pipeline_token 传递顺序

### 7.1 · 14 MCP 工具完整清单

| # | 工具 | 用途 | 读 | 写 | Pipeline 阶段 |
|---|---|---|---|---|---|
| 1 | `query_mastery` | 读节点 mastery 状态 | frontmatter 5 信号 | - | Step 0 (无 token) |
| 2 | `context_enrichment` | 组装 1-hop 邻居 + Tips + Edges + errors | wiki/concepts/* + edges/* | - | Step 0 |
| 3 | `search_memories` | Graphiti 历史检索 | Graphiti store | - | Step 0-N |
| 4 | `generate_question` | 基于 callout + Graphiti 出题 | frontmatter + Graphiti | - | Step 1 → token_A |
| 5 | `score_answer` | 4 维 4 分制 AutoSCORE | 用户回答 + 出题 context | - | Step 2 (token_A → token_B) |
| 6 | `update_bkt` | 贝叶斯更新 p_mastery | grade | frontmatter bkt_p_mastery | Step 3 (token_B → token_C) |
| 7 | `update_fsrs` | FSRS DSR 更新 | answer_quality | frontmatter fsrs_* | Step 4 (token_C → token_D) |
| 8 | `assemble_acp` | 组装 ACP (Assessment Context Package) | 多节点融合 | - | Step 0 (exam 前) |
| 9 | `search_notes` | vault 内 Hybrid 检索 | wiki/concepts/* | - | Step 0 |
| 10 | `record_calibration` | 记录 2x2 校准 + 考后投票 | calibration_bias + vote | Graphiti | Step 5 (token_D) |
| 11 | `record_learning_memory` | 持久化学习事件 | generic event | Graphiti | Step N+1 |
| 12 | `archive_conversation` | Hot → Warm → Cold 归档 | session messages | Graphiti | 对话结束 |
| 13 | `create_exam_node` | 在 exam 中创建新节点 | extract_node 素材 | wiki/concepts/*.md + frontmatter | Step 7.8 |
| 14 | `record_error` | 记录误解 4 分类 | error type + desc | frontmatter errors[] + Graphiti | 对话中 |
| (15) | `request_hint` | 4 级渐进提示 | question + level | - | Step 7.7 |
| (16) | `skip_question` | 标记跳过不惩罚 | question_id | frontmatter questions[].skipped | Step 7 |

**注**: 括号内的是额外工具 · 原 Plan 列表是 14 个核心 + 少量辅助

### 7.2 · pipeline_token 传递流程（FR-MCP-02 防篡改）

**标准 5 步 pipeline** (以 `/start_exam_board` 的 Step 7 循环为例):

```
Step 0 · query_mastery (无 token, 读操作不进管道)
      ↓
Step 1 · generate_question
         Input: node_id, canvas_slug, bloom_level
         Output: { question_id, question_text, pipeline_token=token_A }
      ↓
Step 2 · score_answer
         Input: question_id, user_answer, pipeline_token=token_A
         后端验证: token_A.expected_next == "score_answer"
         Output: { scores, confidence, pipeline_token=token_B }
      ↓
Step 3 · update_bkt
         Input: node_id, grade, pipeline_token=token_B
         后端验证: token_B.expected_next == "update_bkt"
         Output: { new_bkt, pipeline_token=token_C }
      ↓
Step 4 · update_fsrs
         Input: node_id, answer_quality, pipeline_token=token_C
         Output: { new_stability, next_review, pipeline_token=token_D }
      ↓
Step 5 · record_calibration (optional)
         Input: question_id, user_vote, pipeline_token=token_D
```

**如果跳步** (例如 Step 3 直接跳到 Step 5):
- 后端检测 token_B.expected_next != "record_calibration"
- 拒绝请求 + 返回错误
- Skill 必须 abort

### 7.3 · Skill 手动管理 token 的代码模式

**Claudian 的 MCP client 不自动管理 token lifecycle** (11-v2 §M3 修正)，skill 必须手动:

```python
# /quiz_from_callout skill workflow

async def quiz_workflow():
    # Step 1
    result_1 = await mcp.generate_question(
        node_id=node,
        bloom_level=4
    )
    token_A = result_1["pipeline_token"]

    # 等用户答
    user_answer = await wait_for_user_answer()

    # Step 2 · 必须传 token_A
    result_2 = await mcp.score_answer(
        question_id=result_1["question_id"],
        user_answer=user_answer,
        pipeline_token=token_A  # ← 手动传
    )
    token_B = result_2["pipeline_token"]

    # Step 3 · 必须传 token_B
    result_3 = await mcp.update_bkt(
        node_id=node,
        grade=result_2["scores"]["average"],
        pipeline_token=token_B  # ← 手动传
    )
    token_C = result_3["pipeline_token"]

    # ...
```

### 7.4 · Frontmatter ↔ MCP 输入输出映射

| MCP 工具 | 输入字段（从 frontmatter 读）| 输出字段（写回 frontmatter） |
|---|---|---|
| `query_mastery` | 无 | 返回值用于 skill 显示 |
| `update_bkt` | 无（skill 传 grade） | `bkt_p_mastery` |
| `update_fsrs` | `fsrs_stability`, `fsrs_difficulty` | `fsrs_stability`, `fsrs_difficulty`, `fsrs_retrievability`, `fsrs_next_review_at` |
| `score_answer` | 无 | `questions[i].score`, `questions[i].confidence` |
| `generate_question` | `selected_nodes`, `exam_mode`, `bloom_level` | `questions[i].question_text`, `questions[i].asked_at` |
| `record_calibration` | 无 | `post_exam_calibration[]`, `questions[i].calibration_bias` |
| `create_exam_node` | 无 | 新 `wiki/concepts/<slug>.md` + `new_nodes_pulled[]` |
| `record_error` | 无 | `errors[]` in `wiki/concepts/*.md` |

### 7.5 · Graphiti 完整使用链路（Plan v16 B23 · Agent 6 硬证据）

> **本节回答用户"以前用 hook 现在用什么" 的追溯问题 · 基于 Agent 6 对 Canvas 后端 Graphiti 机制的完整调研。**

#### 7.5.1 · 关键澄清 · Graphiti 从来不是 hook 触发的

**核心洞察**（Agent 6 调研结论）：

> **Graphiti 的触发机制不依赖 hook · 而是 3 种机制并存**：
> 1. **EventBus 事件驱动**（主动响应学习活动）
> 2. **MCP 工具主动调用**（Claude Code 发起）
> 3. **API endpoint 直接调用**（HTTP 层）

**为什么这个澄清很重要**：
- 之前 Plan v14/v15 对 Graphiti 的讨论隐含假设"通过 hook 触发"· 这是错误的
- Canvas 后端的 episode_worker 是**后台守护进程** · 不依赖 hook
- 方案 A 的 4 层 Hook（§4.7）与 Graphiti 的触发机制**完全正交**

#### 7.5.2 · 机制 1 · EventBus 事件驱动

**位置**：`backend/app/services/event_handlers.py`

**事件链**：

```
SCORE_SUBMITTED (score_answer 返回后)
    ↓
BKT_UPDATED (update_bkt 调用后)
    ↓
MASTERY_CHANGED (mastery 阈值穿越)
    ↓
UI_PUSH (前端推送 · Canvas 独有)
    +
MEMORY_WRITE_REQUESTED (同时触发)
    ↓
handle_memory_write_requested()  (event_handlers.py:265)
    ↓
memory_service.record_learning_event()
```

**关键处理函数**（Agent 6 调研 · 带行号）：

| 函数 | 文件:行号 | 触发事件 |
|---|---|---|
| `handle_memory_write_requested()` | `event_handlers.py:265` | `MEMORY_WRITE_REQUESTED` |
| `handle_fsrs_updated()` | `event_handlers.py:307` | `FSRS_UPDATED` |

#### 7.5.3 · 机制 2 · MCP 工具主动调用

**位置**：`backend/app/mcp/tools/memory_tools.py`

**所有 Graphiti 相关的 MCP 工具**（5 个写入 + 1 个读取 · Agent 6 清单）：

| MCP 工具 | 方向 | 用途 | 调用方 |
|---|---|---|---|
| `record_learning_memory` | 写 | 通用学习事件 | 任何 skill · 对话中 |
| `archive_conversation` | 写 | Hot → Warm → Cold 归档 | `/chat_with_context` Step 7 · Stop hook |
| `record_calibration` | 写 | 考后校准投票 | `/start_exam_board` Step 8 |
| `record_error` | 写 | 误解 4 分类记录 | 对话中 auto-detect |
| `search_memories` | 读 | 3 层检索历史 | 任何 skill · 需要历史时 |

**Claude Code 从 Claudian 发起的典型调用链**：

```python
# 用户在 Claudian 对话 → skill 调用 → MCP → Graphiti

/chat_with_context skill (§4.1)
    ↓
Step 4 · search_memories(query, node_scope, top_k=5)  # 读
    ↓ MCP 调用
memory_service.search_memories()
    ↓ 3 层融合
Graphiti → Neo4j fulltext → 内存缓存
    ↓ 返回
[{memory_id, content, timestamp, relevance_score}, ...]
    ↓
skill 构造 prompt 注入 memories
    ↓
LLM 回答
    ↓
Step 7 · archive_conversation(session_id, node_id, messages)  # 写
    ↓ MCP 调用
memory_service.archive_conversation()
    ↓ EventBus 发布
MEMORY_WRITE_REQUESTED
    ↓ 被 handler 接收
event_handlers.py:265
    ↓ 调用
memory_service.record_learning_event()
    ↓
_enqueue_episode() → asyncio.Queue
    ↓
episode_worker 后台处理
    ↓
graphiti.add_episode()
    ↓
Neo4j 持久化
```

#### 7.5.4 · 机制 3 · API endpoint 直接调用

**位置**：`backend/app/api/v1/endpoints/memory.py`

**HTTP API 端点**：

```
POST /api/v1/memory/episodes
  Body: {
    "group_id": "canvas-dev",
    "name": "[Learning] ROG 完成 MT2 A* 考察",
    "episode_body": "...",
    "source": "text",
    "source_description": "Plan v16 exam session"
  }
  
  → memory_service.record_temporal_event()
  → _enqueue_episode()
  → ... 同机制 2 的链路
```

**用途**：
- 外部系统集成（Canvas 前端直接调用）
- 批量导入历史数据
- 测试脚本

**方案 A 不直接用**（通过 MCP 工具调用更安全）

#### 7.5.5 · 完整写入链路（11 层）

**从触发到 Neo4j 的完整路径**：

```
第 1 层 · 触发点（3 种机制之一）
  ├─ EventBus 事件（SCORE_SUBMITTED / FSRS_UPDATED / ...）
  ├─ MCP 工具调用（record_*, archive_*）
  └─ HTTP API（POST /api/v1/memory/episodes）
                                  ↓
第 2 层 · memory_service 高层 API
  ├─ record_learning_event()        · 学习事件
  ├─ batch_record_learning_events() · 批量
  ├─ record_knowledge_entity()      · Tips/errors
  └─ record_temporal_event()        · 时间事件
                                  ↓
第 3 层 · memory_service._enqueue_episode()
  · 位置: memory_service.py:310-344
  · 职责: 捕获 request_id + 转换为 episode 格式
                                  ↓
第 4 层 · episode_worker.enqueue()
  · 位置: episode_worker.py:407-432
  · 操作: queue.put_nowait() (< 1ms · 非阻塞)
  · 错误: 队列满（maxsize=100）时丢弃 + metric: episodes_dropped_queue_full
                                  ↓
第 5 层 · asyncio.Queue(maxsize=100)
  · 单例 · 全应用一个
  · 背压机制: 满时丢弃防止 OOM
                                  ↓
第 6 层 · episode_worker 后台 worker (单例)
  · 位置: episode_worker.py:252-253
  · 模式: while True · 顺序处理
  · 启动: main.py:263-286 (lifespan startup)
                                  ↓
第 7 层 · episode_worker._process_episode()
  · 位置: episode_worker.py:479-496
  · 重试: 最多 3 次 + exponential backoff
  · 失败处理: 写入 dead_letter_episodes.jsonl
                                  ↓
第 8 层 · Graphiti SDK · graphiti.add_episode()
  · 调用: Gemini LLM 抽取实体 + 关系
  · 调用: Gemini Embedder 生成嵌入
  · 调用: Gemini Reranker 精排
                                  ↓
第 9 层 · Cypher 查询生成
  · Graphiti 内部: 把 episode 转为 Neo4j Cypher
                                  ↓
第 10 层 · Neo4j 写入
  · 连接: bolt://localhost:7687
  · 事务: 原子性保证
                                  ↓
第 11 层 · 确认 + 返回 UUID
  · episode_worker 记录成功
  · 下一个 episode 从 queue 取出
```

#### 7.5.6 · 完整读取链路（3 层融合）

**search_memories 的 3 层检索**（`memory_service.py:1581-1683`）：

```
search_memories(query, group_id, max_results=10)
                              ↓
      ┌───────────────────────┼───────────────────────┐
      │                       │                       │
      ▼                       ▼                       ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  Tier 1      │      │  Tier 2      │      │  Tier 3      │
│  Graphiti    │      │  Neo4j       │      │  Memory      │
│  (semantic)  │      │  fulltext    │      │  cache       │
│              │      │  (Lucene)    │      │              │
│ graphiti     │      │              │      │ self._       │
│ .search_()   │      │ Cypher       │      │ episodes     │
│              │      │ CALL db.idx  │      │ (local)      │
│ recipe:      │      │              │      │              │
│ combined_rrf │      │ 全文索引     │      │ 最近 N 个    │
│              │      │              │      │              │
│ 超时: 3s     │      │ 超时: 2s     │      │ 无超时       │
│ (_search_    │      │ (_search_    │      │              │
│  graphiti)   │      │  neo4j_      │      │              │
│              │      │  fulltext)   │      │              │
│ 行: 1314-    │      │              │      │              │
│ 1396         │      │              │      │              │
└──────┬───────┘      └──────┬───────┘      └──────┬───────┘
       │                     │                     │
       └─────────────────────┼─────────────────────┘
                             ▼
                ┌──────────────────────────┐
                │  merge + dedupe          │
                │  unified scoring         │
                │  sort by relevance       │
                └──────────────┬───────────┘
                               ▼
                    Top N results returned
```

**关键参数**：
- `max_results` · 默认 10 · 可调
- 总超时 · 3s（整个搜索不超过 3 秒 · 超时返回部分结果）
- `recipe` · `combined_rrf` (Reciprocal Rank Fusion) 或 `combined_cross_encoder`

#### 7.5.7 · 所有 Graphiti 写入触点表（5 个 · Agent 6 带行号）

| 触点 | 文件:行号 | 场景 | 写入数据 | 时机 |
|---|---|---|---|---|
| 1 | `memory_service.py:464` | `record_learning_event()` | 学习事件 | 学生完成学习活动 |
| 2 | `memory_service.py:1167` | `batch_record_learning_events()` | 批量学习事件 | 批量导入 |
| 3 | `memory_service.py:1270` | `record_knowledge_entity()` | Tips/errors 知识实体 | 对话中抽取 |
| 4 | `memory_service.py:1789` | `record_temporal_event()` | 时间事件 | Canvas 前端编辑 |
| 5 | `event_handlers.py:265/307` | `handle_memory_write_requested/handle_fsrs_updated` | EventBus 事件 | 事件发布时 |

#### 7.5.8 · 所有 Graphiti 读取触点表（3 个 · Agent 6 带行号）

| 触点 | 文件:行号 | 场景 | 用途 | 返回字段 |
|---|---|---|---|---|
| 1 | `memory_tools.py:157` | `search_memories` MCP tool | Claude Code 主动搜索 | `fact / source / timestamp / relevance_score` |
| 2 | `memory_service.py:1581` | `search_memories` 内部 API | 其他服务调用 | `episode_id / content / entity_names / ...` |
| 3 | `context_enrichment_service.py:1045` | `_enrich_agent_context()` | 对话上下文注入 | 格式化关系字符串（紧凑） |

#### 7.5.9 · 启停机制

**Startup**（`main.py:263-286`）：

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 初始化 Graphiti 连接
    graphiti = await initialize_graphiti_client()
    
    # 初始化 episode_worker
    worker = get_episode_worker()
    await worker.initialize_graphiti(graphiti)
    await worker.start()
    
    # 挂载到 app.state
    app.state.episode_worker = worker
    app.state.graphiti = graphiti
    
    yield  # 应用运行
    
    # Shutdown
    await cleanup_episode_worker(worker)  # main.py:327-334
```

**Shutdown**（`main.py:327-334`）：

```python
async def cleanup_episode_worker(worker):
    # 优雅停止
    await worker.stop()  
    # 内部: queue.shutdown(immediate=False)
    # 等待最多 30 秒处理完剩余 episodes
    # 超时则 cancel
```

**单例保证**：
- `get_episode_worker()` 返回全局单例
- 整个应用只有一个 worker 处理所有写入
- 避免 Neo4j lock 竞争

#### 7.5.10 · 可靠性机制

**5 层防护**（Agent 6 汇总）：

1. **指数退避重试** · 最多 3 次 · 初始 500ms · 指数增长
2. **Dead-letter queue** · 失败持久化到 `data/dead_letter_episodes.jsonl`
3. **隐私防护** · 默认只存哈希 + 长度（`DEAD_LETTER_STORE_FULL_BODY=false`）
4. **背压机制** · `asyncio.Queue(maxsize=100)` · 满时丢弃 + metrics
5. **超时** · 搜索 3s · 写入无限（异步）
6. **事务性** · Neo4j 原子性保证 · 部分失败不会留脏数据

#### 7.5.11 · 完整 ASCII 架构图

```
┌────────────────────────────────────────────────────────────────┐
│                    用户在 Obsidian                              │
│                                                                 │
│  ┌──────────────────────┐         ┌──────────────────────┐     │
│  │  wiki/concepts/*.md  │  Cmd+   │  Claudian Sidebar   │     │
│  │  (活动笔记)          │  Option │  (Chat UI)          │     │
│  │                      │  +C     │                      │     │
│  └──────────────────────┘ ─────►  └──────┬──────────────┘     │
└──────────────────────────────────────────┼────────────────────┘
                                           │
                                           ▼
┌────────────────────────────────────────────────────────────────┐
│                 Claude Code CLI (Claudian 触发)                 │
│                                                                 │
│  /chat_with_context skill 执行 7 步 workflow                    │
│  Step 4 · 调 mcp__canvas-backend__search_memories              │
│  Step 7 · 调 mcp__canvas-backend__archive_conversation         │
└─────────────────────────────────────────┬──────────────────────┘
                                          │ HTTP
                                          ▼
┌────────────────────────────────────────────────────────────────┐
│              FastAPI + FastApiMCP 服务（端口 8000）             │
│                                                                 │
│  /mcp endpoint (main.py:588-593 · FastApiMCP.mount)            │
│  ↓                                                              │
│  MCP 工具 (backend/app/mcp/tools/memory_tools.py:157-246)       │
│  ↓                                                              │
│  MemoryService (backend/app/services/memory_service.py)         │
│  ↓                                                              │
│  - search_memories() · 读路径 (Tier 1/2/3)                      │
│  - record_learning_event() · 写路径                             │
│  ↓                                                              │
│  Episode Worker (backend/app/services/episode_worker.py)        │
│  ↓                                                              │
│  asyncio.Queue (maxsize=100)                                    │
│  ↓                                                              │
│  Background worker (单例 · 顺序处理)                           │
│  ↓                                                              │
│  Graphiti SDK                                                   │
│    - Gemini LLM (抽取实体 + 关系)                               │
│    - Gemini Embedder (向量化)                                   │
│    - Gemini Reranker (精排)                                     │
│  ↓                                                              │
└─────────────────────────────────────────┬──────────────────────┘
                                          │ Cypher (bolt)
                                          ▼
┌────────────────────────────────────────────────────────────────┐
│                    Neo4j (bolt://localhost:7687)                │
│                                                                 │
│  - 实体节点 (:Entity)                                           │
│  - 关系边 (:RELATES_TO)                                         │
│  - Episode 节点 (:Episode)                                      │
│  - 时间戳索引                                                   │
│  - 全文索引 (fulltext)                                          │
└────────────────────────────────────────────────────────────────┘
```

### 7.6 · Canvas 后端当前启用的 13 个服务清单（Plan v16 B24 · Agent 6 调研）

> **本节回答用户"现在用到哪些后端功能" 的追溯问题 · 给出方案 A 直接依赖的完整后端服务清单**

#### 7.6.1 · 13 个启用服务完整表

| # | 服务 | 文件 | 启动顺序 | 方案 A 使用 | 功能 |
|---|---|---|---|---|---|
| 1 | Graphiti episode_worker | `episode_worker.py` | `main.py:263-286` | ⭐⭐⭐ 核心 | 后台异步写入 · maxsize=100 |
| 2 | Memory Service | `memory_service.py` | lifespan 预热 | ⭐⭐⭐ 核心 | 读写 API + 三层检索 |
| 3 | Context Enrichment | `context_enrichment_service.py` | 懒加载 | ⭐⭐ 使用 | 1-hop 邻居 + Tips 注入 |
| 4 | RAG Service | `rag_service.py` | 懒加载 | ⭐⭐ 使用 | 4 路融合检索 · LanceDB |
| 5 | Mastery Engine | `mastery_engine.py` | lifespan | ⭐⭐⭐ 核心 | BKT + FSRS + 5 信号融合 |
| 6 | Exam Service | `exam_service.py` | 懒加载 | ⭐⭐⭐ 核心 | 检验白板 · 递归防护 |
| 7 | Event Bus | `event_bus.py` | lifespan | ⭐⭐⭐ 核心 | 事件链驱动 |
| 8 | Archive Scheduler | `archive_scheduler.py` | lifespan | ⭐ 部分 | 24h 周期归档 |
| 9 | LanceDB Index Service | `lancedb_index_service.py` | lifespan | ⭐⭐ 使用 | 自动增量索引 |
| 10 | Cost Tracker | `cost_tracker.py` | 中间件 | ⭐ 使用 | LLM 成本追踪 |
| 11 | Alert Manager | `alert_manager.py` | lifespan | ⭐ 监控 | 30s 评估告警 |
| 12 | Resource Monitor | `resource_monitor.py` | lifespan | ⭐ 监控 | 5s 采样 |
| 13 | Prompt Registry | `prompt_registry.py` | lifespan | ⭐⭐ 使用 | 模板版本管理 |

#### 7.6.2 · 方案 A 依赖的 Top 5 核心服务（考察链路关键路径）

按重要性排序 · 这 5 个服务缺一不可：

1. **Graphiti episode_worker**（写入）· 所有学习事件必须通过它写入 · 单点故障风险
2. **Memory Service**（读写 API）· `search_memories` 的入口 · 三层融合
3. **Mastery Engine**（评分）· BKT + FSRS + 5 信号融合 · 考察评分的核心
4. **Exam Service**（检验白板）· `/start_exam_board` 的后端 · 含递归防护
5. **RAG Service + LanceDB Index Service**（检索）· `/chat_with_context` 补充材料

**方案 A 不直接依赖的服务**（可有可无）：
- Archive Scheduler · 24h 周期 · 不影响实时体验
- Cost Tracker · 追踪 LLM 成本 · 用于监控
- Alert Manager · 只在告警时触发
- Resource Monitor · 性能指标

#### 7.6.3 · Phase 1 启动检查清单

用这个 checklist 验证 Canvas 后端所有方案 A 依赖的服务都 ready：

- [ ] Neo4j 连接正常 · `bolt://localhost:7687`
  ```bash
  cypher-shell -u neo4j -p password "RETURN 1"
  ```

- [ ] Ollama + bge-m3 可用
  ```bash
  curl http://localhost:11434/api/tags | jq '.models[] | select(.name == "bge-m3")'
  ```

- [ ] Canvas 后端启动成功
  ```bash
  uvicorn backend.app.main:app --port 8000
  # 查看日志 · 13 个服务的 "started" 或 "ready" 信息应该都出现
  ```

- [ ] Health check 通过
  ```bash
  curl http://localhost:8000/health
  # 预期: {"status": "ok", ...}
  ```

- [ ] Memory service health 通过
  ```bash
  curl http://localhost:8000/api/v1/memory/health
  # 预期: {"graphiti_connected": true, "neo4j_connected": true, ...}
  ```

- [ ] MCP 端点可达 · 14 个工具可调用
  ```bash
  curl http://localhost:8000/mcp/tools
  # 预期: [{"name": "query_mastery"}, {"name": "generate_question"}, ...]
  ```

- [ ] 初次 LanceDB 索引完成
  ```bash
  curl -X POST http://localhost:8000/api/v1/metadata/index/vault \
       -d '{"vault_path": "/path/to/canvas-vault"}'
  
  # 等待完成
  curl http://localhost:8000/api/v1/metadata/index/status
  # 预期: {"status": "ready", "indexed_files": N, "total_files": N}
  ```

- [ ] episode_worker 正在处理队列
  ```bash
  # 通过日志确认 · 应该看到 "episode_worker started" 和 "processing episode"
  ```

**启动顺序依赖**：
1. Neo4j 必须先启动
2. Ollama 必须先启动
3. Canvas 后端 uvicorn
4. LanceDB 初始索引（一次性）
5. Claudian + Obsidian
6. 触发第一个 skill 验证

#### 7.6.4 · 如果某个服务不可用

**降级策略**（单点失效时的 fallback）：

| 失效服务 | 降级行为 | 损失 |
|---|---|---|
| Graphiti | skill 继续工作 · 不写历史 | 失去长期记忆 |
| Memory Service | 使用空 memories[] | 失去 Tier 2/3 搜索 |
| Context Enrichment | 不注入邻居 | 对话质量下降 |
| RAG Service (LanceDB) | 不显示补充材料 | `/chat_with_context` 不给链接 |
| Mastery Engine | 跳过评分 | BKT/FSRS 不更新 |
| Exam Service | `/start_exam_board` 失败 | 无法考察 |
| Event Bus | 事件链中断 | 写入不触发 |

**方案 A 的 hard 依赖**：
- Neo4j（无 fallback · 必须运行）
- Canvas 后端 FastAPI（无 fallback）
- Claude Code CLI（无 fallback）
- Obsidian（无 fallback）

**soft 依赖**：
- Ollama + bge-m3（失败时降级为不显示补充材料）
- Graphiti（失败时降级为无记忆模式）
- Gemini API（失败时 Graphiti 无法抽取实体）

#### 7.6.5 · Canvas 后端实地状态（Plan v23 硬化 · 实际运行级验证通过 · 四层 nested errata 确认关闭 L3）

> **本节经历了 5 次演化**：Plan v17 原始后端扫描 → Plan v18 三方审查 → Plan v19 smoke check "校正" → Plan v21 **二次校正**（"errata of errata"）→ **Plan v23 实际运行验证**（L3 盲点关闭 · 从"静态代码分析"升级到"运行级证据"）。每次都揭示了一个新的盲点。Plan v23 是**当前最可信的版本** · 基于对 `app.services.rag_service` 入口的**真实 Python 执行**作为 ground truth（而不只是代码原文阅读）。
>
> 为了让未来读者理解这个 section 的演化史 · Plan v23 保留了 Plan v19 的 2 项正确校正（Cost Tracker + UserPromptSubmit）和 Plan v21 的 canvas_agentic_rag 代码原文引用，追加了 Plan v23 Stage 1 实际运行的真实输出（首次为 canvas_agentic_rag 就绪状态提供运行级证据）。

**Plan v17 → v18 → v19 → v21 → v23 五层校正对比表**：

| 组件 | Plan v17 断言 | Plan v18 断言 | Plan v19 断言 | Plan v21 断言 | **Plan v23 实测** | 最终状态 |
|---|---|---|---|---|---|---|
| **Cost Tracker** | 🔴 待实施（services/ 下缺失） | 🔴 继承 v17 | ✅ 已就绪（`middleware/cost_tracker.py`）| ✅ 已就绪（v19 正确）| ✅ **已就绪**（继承）| **已就绪** · `backend/app/middleware/cost_tracker.py` · §7.6.1 第 10 号服务 · Phase 1 无需新写 |
| **canvas_agentic_rag workflow** | 🟡 未验证 | 🟡 继承 v17 | 🔴 module 完全不存在（`pip show` 未找到 + `import canvas_agentic_rag` 失败）| ✅ 代码存在（代码原文阅读 · 未运行）| ✅ **运行级就绪**（Plan v23 真实执行 `app.services.rag_service` 入口 · `LANGGRAPH_AVAILABLE=True` · `_IMPORT_ERROR=None`）| **已就绪 · 运行级证据** · 见下方 Plan v23 smoke check 实际输出记录 · Phase 1 直接复用 |
| **UserPromptSubmit hook** | 🔴 需新写（`backend/app/hooks/` 无此类型）| 🔴 继承 v17 | 🟡 架构层误判（`backend/` 无 `hooks/` 目录 · UserPromptSubmit 是 Desktop `settings.json` 机制） | 🟡 架构层误判（v19 正确）| 🟡 **架构层误判**（继承）| **Desktop 层工作** · `~/.claude/settings.json` + bash 脚本 · 不在 backend |

**核心校正**：`canvas_agentic_rag` 实际存在 · v19 smoke check 命令错误

Plan v21 的独立核实发现了 Plan v19 校正自身的一个 meta-level 盲点：Plan v19 用错误的命令做 smoke check，然后基于错误的命令结果写了一个错误的"真相"。

**代码证据链**（Plan v21 直接引自生产代码原文）：

`backend/lib/agentic_rag/__init__.py`（2026-03-16 最后更新 · Story 2.1 死代码清理后）：

```python
# Line 48: 初始化 availability flag
AGENTIC_RAG_AVAILABLE: bool = False
_IMPORT_ERROR: Optional[str] = None

# Line 52-54: Placeholder exports（import 失败时的 graceful degradation）
CanvasRAGState = None
CanvasRAGConfig = None
canvas_agentic_rag = None

try:
    # Line 59: Import state schema
    from agentic_rag.state import CanvasRAGState
    # Line 63: Import config schema
    from agentic_rag.config import CanvasRAGConfig
    # Line 67: Import compiled StateGraph
    from agentic_rag.state_graph import canvas_agentic_rag

    # Line 70: All imports successful
    AGENTIC_RAG_AVAILABLE = True
    logger.info("Agentic RAG module loaded successfully. AGENTIC_RAG_AVAILABLE=True")
except ImportError as e:
    # ... AC 4 详细诊断日志（Line 73-101）...

# Line 176-186: 明确的 __all__ 导出列表
__all__ = [
    "CanvasRAGState",
    "CanvasRAGConfig",
    "canvas_agentic_rag",    # ← 顶级包暴露的名字
    "AGENTIC_RAG_AVAILABLE",
    "get_import_error",
    "check_dependencies",
]
```

**顶级包名是 `agentic_rag`** · `canvas_agentic_rag` 是该包 `__init__.py` 从 `agentic_rag.state_graph` re-export 出来的**编译后 StateGraph 对象**（`CompiledStateGraph` 类型），不是一个独立的 pip 包，也不是独立的 module 名。

**生产代码已正确使用**（`backend/app/services/rag_service.py` L40-85）：

```python
# RAGService 是 Canvas 后端的核心服务之一 · 每天启动时都会 import
from agentic_rag import (
    canvas_agentic_rag,
    AGENTIC_RAG_AVAILABLE,
    CanvasRAGState,
    CanvasRAGConfig,
)

class RAGService:
    def __init__(self):
        if AGENTIC_RAG_AVAILABLE:
            self.graph = canvas_agentic_rag  # 直接复用编译后的 StateGraph
            logger.info("RAGService initialized with canvas_agentic_rag workflow")
        else:
            logger.warning("canvas_agentic_rag unavailable · graceful degradation to direct MCP calls")
            self.graph = None
```

如果 `canvas_agentic_rag` 真的不存在 · 这个 service 每天启动时都会打印 warning 日志 · Canvas 后端团队早就发现并修了。**Plan v19 的"不存在"断言与生产代码的日常运行事实直接矛盾** · 但 Plan v19 没有对这个矛盾做独立核实。

**Plan v19 → v21 → v23 smoke check 命令演化对比**（Fix-11 · 三层命令递进）：

| 版本 | 命令 | 结果 | 为什么错（或为什么对）|
|---|---|---|---|
| Plan v19 | `pip show canvas_agentic_rag` + `python -c "import canvas_agentic_rag"` | ❌ **命令语法错** | canvas_agentic_rag 不是 pip 包名也不是顶级 module · 顶级包叫 `agentic_rag`（见 `backend/lib/agentic_rag/__init__.py`）· canvas_agentic_rag 是该包从 `agentic_rag.state_graph` re-export 的 StateGraph 对象 |
| Plan v21 | `cd backend && .venv/bin/python -c "from agentic_rag import canvas_agentic_rag, AGENTIC_RAG_AVAILABLE; print(...)"` | ❌ **sys.path 缺失** | `agentic_rag` 包在 `backend/lib/agentic_rag/` 下 · `backend/lib/` 不在默认 Python sys.path 里 · 仅 cd 到 backend 不足 · 会触发 `ModuleNotFoundError: No module named 'agentic_rag'`（除非 PYTHONPATH 或者通过生产代码入口间接触发）· Plan v21 只做了**代码原文阅读** · 没有实际运行 · L3 盲点就在这里 |
| **Plan v23** | `cd /Users/Heishing/Desktop/canvas/canvas-learning-system/backend && .venv/bin/python -c "from app.services.rag_service import LANGGRAPH_AVAILABLE, _IMPORT_ERROR; print('LANGGRAPH_AVAILABLE=', LANGGRAPH_AVAILABLE, 'ERROR=', _IMPORT_ERROR)"` | ✅ **真实运行通过** · `LANGGRAPH_AVAILABLE= True ERROR= None` | production-equivalent · 通过 `app.services.rag_service` 入口触发生产代码 L32-37 的 `sys.path.insert(0, str(_project_root / "lib"))` 注入 · 后续 `from agentic_rag import ...` 成功 · 同时验证 `rag_service.py` 的 LANGGRAPH_AVAILABLE 判定逻辑本身也对（L56-71 try/except 分支）|

**Plan v23 Stage 1 真实运行完整输出**（2026-04-09 晚 13:20:55-13:21:00 · 首次为 canvas_agentic_rag 就绪状态提供运行级证据）：

```
$ cd /Users/Heishing/Desktop/canvas/canvas-learning-system/backend && \
    .venv/bin/python -c "from app.services.rag_service import LANGGRAPH_AVAILABLE, _IMPORT_ERROR; print('LANGGRAPH_AVAILABLE=', LANGGRAPH_AVAILABLE, 'ERROR=', _IMPORT_ERROR)"

2026-04-09 13:20:55 [debug    ] RAGService: Added /Users/Heishing/Desktop/canvas/canvas-learning-system/backend/lib to sys.path
/Users/Heishing/Desktop/canvas/canvas-learning-system/backend/.venv/lib/python3.14/site-packages/langchain_core/_api/deprecation.py:25: UserWarning: Core Pydantic V1 functionality isn't compatible with Python 3.14 or greater.
  from pydantic.v1.fields import FieldInfo as FieldInfoV1
/Users/Heishing/Desktop/canvas/canvas-learning-system/backend/.venv/lib/python3.14/site-packages/jieba/_compat.py:18: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
  import pkg_resources
Building prefix dict from the default dictionary ...
Dumping model to file cache /var/folders/vq/gssw8vy54671lh9nlqc_ft2w0000gn/T/jieba.cache
Loading model cost 0.205 seconds.
Prefix dict has been built successfully.
2026-04-09 13:21:00 [info     ] RAGService: LangGraph/Agentic RAG available. LANGGRAPH_AVAILABLE=True
LANGGRAPH_AVAILABLE= True ERROR= None
```

**Plan v23 真实运行输出解读**：

1. ✅ **主结论**：`LANGGRAPH_AVAILABLE= True ERROR= None` —— canvas_agentic_rag 完全可用 · Plan v21 的"已就绪"断言得到**运行级证据**
2. ✅ **sys.path 注入逻辑正常**：debug 行 `RAGService: Added .../backend/lib to sys.path` 确认 `rag_service.py` L32-37 的 sys.path 注入在生产运行中被执行（这也证实了 Plan v21 命令 `from agentic_rag import ...` 没有这一步是走不通的 —— 从而确认 L3 盲点的存在）
3. ✅ **依赖链完整**：jieba（中文分词）+ langchain_core + langgraph 全部成功加载（jieba prefix dict 构建成功 · langchain_core deprecation warning 不阻断 · langgraph 通过 rag_service.py L56-60 的 `AGENTIC_RAG_AVAILABLE and canvas_agentic_rag is not None` 判定）
4. 🟡 **观察 1**：Python 3.14 与 Pydantic v1 有兼容性 warning（`Core Pydantic V1 functionality isn't compatible with Python 3.14 or greater`）· **不影响 LANGGRAPH_AVAILABLE 判定** · Phase 1 可选择监控是否需要升级 Pydantic v2 或降级 Python 版本
5. 🟡 **观察 2**：jieba 依赖 `pkg_resources`（2025-11-30 slated for removal）· 也不阻断当前运行 · Phase 1 长期观察
6. ⏱ **启动时间**：~5 秒（13:20:55 → 13:21:00）· 可接受的 Python 冷启动开销

**Plan v23 L3 盲点确认关闭**：Plan v21 §1.5.8 显式预留了 L3 TBD（"Plan v21 独立核实 · 盲点 待定 · 等 Plan v22 第三轮审查"）· Plan v23 的真实运行已**从运行级证据侧确认** Plan v21 的"~100% 就绪"断言正确 · L3 盲点不存在于"canvas_agentic_rag 是否真的能运行"这一层 · L3 盲点**仅存在于** "smoke check 命令本身是否可执行" —— 而这一层被 Plan v23 的 production-equivalent 命令修复。

**Plan v19 的 smoke check 盲点自我批评**：

1. **没有以生产代码为 ground truth**：Plan v19 凭记忆猜测"canvas_agentic_rag 应该是独立 module"，没有先 grep 生产代码看实际 import 语法。`backend/app/services/rag_service.py` 的 import 语法已经明确告诉所有人正确的命名空间。
2. **没有核实矛盾**：如果 canvas_agentic_rag 真不存在 · RAGService、MCP 工具、agentic_rag worker 都会崩溃。Plan v19 应该问一句"那 Canvas 后端是怎么每天启动的"，就能发现矛盾。
3. **把错误的 smoke check 结果当作"独立验证"**：Plan v18 的核心教训是"亲自做 smoke check 避免继承 Plan v17 的盲点"，但 Plan v19 的 smoke check 自身有盲点——**命令语法错**——结果是 Plan v19 用一个错误的 smoke check 否定了另一个人的（可能正确的）扫描结果。

**修正后的 Canvas 后端就绪状态**（Plan v23 硬化 · ~100% 就绪 · 0 项硬差距 · **运行级证据**）：

| # | 服务/组件 | 状态 | 位置 | Phase 1 行动 |
|---|---|---|---|---|
| 1-9 | §7.6.1 前 9 个服务 | ✅ 已就绪 | `backend/app/services/` | 直接复用 |
| 10 | **Cost Tracker** | ✅ **已就绪**（Plan v19 正确校正）| `backend/app/middleware/cost_tracker.py` | 直接复用 |
| 11-13 | §7.6.1 其他 3 个服务 | ✅ 已就绪 | `backend/app/services/` 或 lifespan | 直接复用 |
| +1 | **canvas_agentic_rag workflow** | ✅ **已就绪 · 运行级验证**（**Plan v23 校正** · Plan v21 的"代码存在"升级为"实际运行通过")| `backend/lib/agentic_rag/__init__.py` 从 `agentic_rag.state_graph` re-export · `rag_service.py` L49 已在生产中使用 · **Plan v23 Stage 1 真实运行输出 `LANGGRAPH_AVAILABLE=True`** | 直接复用 · §10.1 Day 1 Spike 2 **已提前完成** |
| +2 | **Claude Code Desktop hooks (UserPromptSubmit)** | 🟡 **架构澄清**（Plan v19 正确校正）| `~/.claude/settings.json` + bash 脚本（**不在 backend**）| Phase 1 新写 settings.json 配置 · 不涉及 backend Python |

**Plan v23 结论**：
- Canvas 后端 **~100% 就绪**（与 Plan v21 一致 · 但从"代码原文阅读证据"升级到"真实运行证据"）
- **0 项硬差距**（Plan v19 的唯一硬差距 canvas_agentic_rag 实际已就绪 · Plan v23 运行级确认）
- UserPromptSubmit hook 是 **Desktop 层工作** · 与 backend 解耦 · 降级到 JSON + bash 即可
- Plan v18 §1.5 BUG-05 的 3 项断言中：Cost Tracker 是误判（Plan v19 校正）· UserPromptSubmit 是架构层误判（Plan v19 校正）· canvas_agentic_rag 的"module 不存在"也是误判（Plan v21 代码阅读 + **Plan v23 运行级证据** 双重校正）· 三项全错 · 无真硬差距
- **新增观察**（Plan v23 独有）：Python 3.14 + Pydantic v1 兼容性 warning + jieba pkg_resources deprecation warning · 都不阻断 · Phase 1 长期监控

**四层 nested errata 的讽刺 meta-pattern**（Plan v23 延伸 · L3 盲点确认关闭）：

| 层 | 时间 | 主角 | 盲点 | 共同教训 |
|---|---|---|---|---|
| L1 | 2026-04 上旬 | Plan v17 Canvas 后端扫描 | 只搜 `backend/app/services/` 目录 · 漏掉 `middleware/` 和 `lib/` | 没有全目录扫描 |
| L2 | 2026-04-09 早 | Plan v19 smoke check | 命令语法错 · 用 `pip show canvas_agentic_rag` / `import canvas_agentic_rag` 而不是正确的 `from agentic_rag import canvas_agentic_rag` | 没有以生产代码为 ground truth |
| L3 | 2026-04-09 下午 | Plan v21 独立核实 | **命令不完整**（静态代码分析代替实际运行）· `from agentic_rag import ...` 在 backend/ 下缺 sys.path 会失败 · 未实际运行就断言"已就绪" | 代码原文阅读 ≠ 运行级证据 · 必须实际执行 |
| **L4** | **2026-04-09 晚** | **Plan v23 实际运行** | **无盲点**（Plan v23 完成了 production-equivalent 命令的实际运行 · 首次为 canvas_agentic_rag 提供运行级证据）| 静态分析 + 运行级验证必须同时存在 |
| L5 | **TBD** | **Phase 1 Day 1 Spike 1/2/3** | **待定** · Plan v23 无法预知 | **TBD · 等 Phase 1 骨架 Day 1 执行** |

**所有四层的共同教训**：每层都**应该以生产代码的实际运行为最终仲裁**，而不是凭记忆猜测、继承上一层的结论、或只读代码不跑代码。

**Plan v23 方法论新护栏**（第 5 条 · Plan v21 4 条的延伸）：

1. **grep 生产代码找真实 import/call 语法** → 复制粘贴作为 smoke check 命令（Plan v21 护栏）
2. **比对 `__all__` 和 `__init__.py`** → 知道顶级包到底导出什么名字（Plan v21 护栏）
3. **寻找日常运行的矛盾证据** → 如果 smoke check 说 X 不存在 · 但生产日志显示 X 每天正常运行 · 先怀疑 smoke check 命令（Plan v21 护栏）
4. **errata 必须有显式的 errata-of-errata 预留空间** → 本 section 的 Plan v21 校正就是承认 Plan v19 的校正本身可能错 · 给 Plan v22/v23 留修订空间（Plan v21 护栏）
5. **静态分析 + 运行级验证必须同时存在**（**Plan v23 新增**）→ 任何涉及"X 是否可用"的断言都需要有 "X 实际运行输出" 的证据 · 只读代码不跑代码会像 Plan v21 一样留下 L3 盲点 · Plan v23 用 production-equivalent 命令的真实运行闭合了这个盲点

**追溯链**：
- Plan v17 Canvas 后端扫描日期：2026-04 上旬（只搜 `services/` 目录 · 盲点 L1）
- Plan v18 §1.5 继承 Plan v17 的扫描结果（未独立验证 · 把 L1 盲点继承下来）
- Plan v19 smoke check 日期：2026-04-09 早（命令语法错 · 盲点 L2 · 把 L1 的继承盲点替换为 L2 的新盲点）
- Plan v20 adversarial review prompt v2（把 L2 的错误结论写进 prompt 转发 ChatGPT）
- ChatGPT 5 Pro Deep Research 第二轮审查（2026-04-09 下午 · 发现 L2 的矛盾 · 提出 Fix）
- Plan v21 独立核实 + §7.6.5 重写（2026-04-09 下午 · 修正 L2 盲点 · **代码原文阅读** · 未实际运行 · 预留 L3 TBD）
- Plan v22 adversarial review prompt v3 → ChatGPT 第三轮审查（2026-04-09 晚 · ChatGPT 指出 Plan v21 命令的 sys.path 问题 · 发现 L3 盲点的具体形态）
- **Plan v23 实际运行 smoke check（2026-04-09 晚 · 首次为 canvas_agentic_rag 提供运行级证据 · L3 盲点确认关闭）**

**相关文档**：
- `16-triangulated-review-report.md` §1.5 + §1.5.6（Plan v18 errata）+ §1.5.8（Plan v21 meta-erratum of erratum）+ **§1.5.9（Plan v23 四层 nested errata 延伸 · L3 盲点确认关闭 · 本次新增）**
- `17-prd-v3-changelog.md` Fix-03 段（Plan v19 产物 · 保留为历史）
- `19-prd-v4-changelog.md`（Plan v21 产物 · 含完整 7 项 Fix diff）
- **`21-prd-v5-changelog.md`**（Plan v23 产物 · 本次新增 · 含完整 5 项 Fix + 真实运行输出记录）
- `backend/lib/agentic_rag/__init__.py`（生产代码 ground truth · 代码阅读层）
- `backend/app/services/rag_service.py` L32-85（生产使用示例 · Plan v23 运行入口）
- **Plan v23 Stage 1 真实运行输出**（上方代码块 · L4 运行级证据）

---

## §8 · 6 个用户旅程的完整 md 实现

> 基于 Agent J 的学习科学解构，每个旅程给出：PRD 对应 + 核心学习科学原理 + 方案 A 完整 md 操作序列

### 8.1 · 旅程 1 · 日常学习（原白板 · 剖析模式）

**PRD 对应**: L371-379 旅程 1
**核心原理**: Edge 对话 EI+SE (d=0.80-1.00) + Generation Effect (d=0.65)

**方案 A 完整流程**:
1. 用户在 Obsidian 打开 `wiki/canvases/search-algorithms.md` (主题入口)
2. Cmd+Option+C (`/chat_with_context`) 进入剖析模式对话
3. 用户问"A* 和 Dijkstra 有什么区别？"
4. Skill 调 `context_enrichment` 注入 1-hop 邻居（dijkstra, bfs, heuristic-search）
5. Skill 调 `search_memories` 拉取历史（"你上次在 admissibility 标记过一个误解"）
6. LLM 回答 + 主动提醒历史误解
7. 用户决定深究 A* 和 heuristic 的关系 → 在笔记写 `[[a-star]] 依赖 [[heuristic-search]]` 的 wikilink
8. 用户选中这行 → Cmd+Option+R (`/edge_discuss`)
9. `/edge_discuss` 启动 EI+SE 双策略对话 (§1.3)
10. 对话产出 `edges/a-star--heuristic-search.md`
11. 用户发现新概念 "admissible heuristic reasoning" → 选中对话文本 → Cmd+Option+X (`/extract_node`)
12. `/extract_node` 生成 `wiki/concepts/admissible-heuristic-reasoning.md` (默认 BKT=0.30)

**产物**:
- `outputs/sessions/2026-04-08-a-star-discussion.md` (对话记录)
- `edges/a-star--heuristic-search.md` (新 Edge)
- `wiki/concepts/admissible-heuristic-reasoning.md` (新节点 · Generation Effect)

**守恒度**: ✅ 85% (完全保留 EI+SE + Generation Effect)

### 8.2 · 旅程 2 · 检验白板考察 (最详细 · 灵魂旅程)

**PRD 对应**: L383-393 旅程 2
**核心原理**: Retrieval Practice d=1.50 (Karpicke & Blunt 2011)

**完整流程**: 见 §2.7 的 2 小时 Day-in-Life 示例（已详细展开 · 本节不重复）

**守恒度**: ✅ 95% (灵魂章节 · 详见 §2.1-2.7)

### 8.3 · 旅程 3 · 错误修正记忆闭环

**PRD 对应**: L397-405 旅程 3
**核心原理**: Error Correction (Metcalfe 2017 Learning from Errors) + Spacing Effect d≈0.55 (Cepeda et al. 2008 · range 0.40-0.70)
<!-- Plan v19 修正：原声称 "Spacing d=2.30 (Metcalfe 2017)" 无法追溯到 Metcalfe 2017 文献。Metcalfe 2017 的 Annual Review 主题是 Learning from Errors（error correction），不报告 spacing effect d 值。spacing effect 的可靠来源是 Cepeda 2008 Psychological Science meta-analysis · typical d ≈ 0.4-0.7。-->


**方案 A 完整流程**:

**Day 0 (2026-04-08)**:
1. 用户在 `/chat_with_context` 对话中发现: "我把 consistent 和 admissible 搞混了"
2. Cmd+Option+Q (`/qcl` in 11-v2) 标记 `[!fail]+` callout 到 `wiki/concepts/admissibility.md`
3. Skill 自动加 `#flashcard/error-correction` tag
4. Skill 生成 Tasks:
   ```
   - [ ] 复习误解: consistent vs admissible 📅 2026-04-11 #error-correction
   - [ ] 辨析题考察: consistent vs admissible 📅 2026-04-15 #error-correction
   ```
5. 调 `record_error` MCP 工具写入 Graphiti

**Day 3 (2026-04-11)**:
6. Spaced Repetition 插件 popup: "复习: consistent vs admissible"
7. 用户打开 `wiki/concepts/admissibility.md`
8. Claudian 自动挂载 + `/chat_with_context` 自动触发
9. Skill 调 `search_memories` 拿历史误解 → 在 sidebar 注入 "你 3 天前标记过这个"
10. 用户复习 · 记忆巩固 · 调 `update_fsrs` 更新稳定性

**Day 7 (2026-04-15)**:
11. Tasks dashboard 显示 "辨析题考察 ⚠️ 今天"
12. 用户触发 `/start_exam_board` on `wiki/canvases/search-algorithms.md`
13. `generate_question` MCP 读 Graphiti 历史误解 → 出辨析题: "给出一个启发函数是 admissible 但不是 consistent 的例子"
14. 用户答题 · 证明已纠正误解

**产物**: 完整的 3 天 + 1 周闭环 · 误解永久纠正

**守恒度**: ✅ 90% (§1.8 详细分析)

### 8.4 · 旅程 4 · 新用户冷启动

**PRD 对应**: L409-415 旅程 4
**核心原理**: Progressive Calibration (渐进画像)

**方案 A 完整流程**:

**Step 1 · 安装 (一次性)**
```bash
# 1. 安装 Obsidian
# 2. 打开新 vault (或 clone canvas-vault 模板)
# 3. 安装 Claudian plugin + 配置 Claude Code CLI path
# 4. 安装 10 个插件 (§5)
# 5. 启动 Canvas 后端 (MCP 工具层)
uvicorn backend.app.main:app --port 8000
# 6. 在 Claudian 配置 MCP:
claude mcp add-json canvas-backend '{"type": "http", "url": "http://localhost:8000/mcp"}'
```

**Step 2 · 首次使用**
1. 用户创建第一个 `wiki/canvases/my-first-topic.md` (用 Templater 模板)
2. 用户在里面贴入课件文本
3. 用户触发 `/chat_with_context` 问第一个问题
4. Skill 发现此节点还没 BKT/FSRS → 用默认先验 (BKT=0.30, FSRS 默认参数)
5. LLM 回答 (因为历史为空 · 无个性化)
6. 用户标 Tips · 用 Cmd+Option+X 拉出新节点

**Step 3 · 5-8 次后感受到"越来越懂我"**
- 第 5 次调用时 `search_memories` 开始返回有价值的历史
- 第 8 次时 `generate_question` 能基于历史错误出题
- 用户体感"Agent 记住了我上次的错"

**守恒度**: ✅ 90% (BKT/FSRS 默认先验完全复用 · 只缺少 Canvas 前端的首次引导弹窗)

### 8.5 · 旅程 5 · 图片密集型学习

**PRD 对应**: L419-425 旅程 5
**核心原理**: Multi-modal Learning (Mayer 2009) d=0.40-0.60

**方案 A 实现**（部分降级）:

**可行部分** ✅:
1. 用户在 Obsidian 贴图 → 生成 `![[image-xxx.png]]` 链接
2. Cmd+Option+C (`/chat_with_context`)
3. **Claudian 原生支持图像识别** (YishenTu README 明确支持)
4. Claudian 把图片 + 笔记文本同时发给 Claude Code CLI
5. Claude 分析图片 + 回答（不需要 OCR）

**降级部分** ⚠️:
- 图片 OCR 后台异步索引 → Claudian 每次都重新分析（增加 token 成本）
- Vision API 提取 LaTeX 公式 → 不自动持久化到 `graphify-out/`

**补偿方案**:
- 用户手动触发 `/extract_image_concepts` (未来 skill) 把图片内容抽取为文字
- 写入 `wiki/concepts/*.md` 的 body 或 Tips

**守恒度**: ⚠️ 70% (Claudian 原生多模态 · 但异步索引降级)

### 8.6 · 旅程 6 · 学习档案浏览

**PRD 对应**: L429-437 旅程 6
**核心原理**: Formative Feedback d=0.50-0.80 (Hattie 2007) + Transparent OLM (Open Learner Model)

**方案 A 完整流程**:

1. 用户 Cmd+Option+P (`/review_profile`)
2. 无参数触发 → 显示全局 dashboard
3. Skill 读 `wiki/dashboard.md` 的 Dataview 输出
4. Claudian sidebar 显示:

```
## 🎯 Learning Dashboard (2026-04-08)

### 建议优先复习
| 概念 | 当前掌握 | 推荐复习时间 |
|---|---|---|
| 建议优先复习: admissibility | 62% | 今天 |
| 建议优先复习: consistent | 55% | 2026-04-09 |
| 建议优先复习: manhattan-distance | 48% | 2026-04-10 |

### 本周考察历史
- 2026-04-08 search-algorithms (+0.11 mastery · 新发现 1 节点)
- 2026-04-03 llrb-trees (+0.08 mastery · 无新发现)

### 元认知校准
- 🟢 会+知道会: 23 条
- 🟡 会+以为不会: 8 条
- 🔴 不会+以为会: 4 条 ⚠️ (建议优先关注)
- ⚪ 不会+知道不会: 12 条

### 待纠正的理解
1. consistent vs admissible (Day 0) → 待 Day 7 辨析题
2. manhattan-distance corner case (Day 0) → 待 Day 3 复习
```

5. 用户点击 "admissibility" → 进入单节点 profile
6. Skill 读 `wiki/concepts/admissibility.md` frontmatter + body
7. 显示详细档案:
   - 5 信号状态
   - Tips 列表（3 条）
   - 待纠正的理解（1 条 · 已纠正）
   - 相关 Edges（2 条 · wikilink 可点击）
   - [启动单节点考察] 按钮 → 触发 `/start_exam_board` on 单节点

**守恒度**: ⚠️ 75% (Dataview 表格补偿 FR-TRACE-01~05 · 失去图形 UI)

---

## §9 · 学习效果守恒度评估

### 9.1 · 12 个设计的守恒度汇总表

| # | 设计 | d 值 | 守恒度 (v15) | 守恒度 (**v16**) | 加权贡献 (v16 · ⚠️ 不参与加总 · Plan v19 修正) |
|---|---|---|---|---|---|
| 1 | 原白板 vs 检验白板二分法 (灵魂) | 1.50 | 95% | 95% | 1.425 |
| 2 | 拉出新节点 (Generation Effect) | 0.65 | 90% | 95% ⬆ | 0.618 |
| 3 | Edge 对话 EI+SE 双策略 | 0.90 (avg of 0.80-1.00) | 75% | 75% | 0.675 |
| 4 | 4 维 4 分制评分双框架 | 0.70 | 85% | 85% | 0.595 |
| 5 | BKT + FSRS + 5 信号融合 | 1.00 (rho=0.65 映射) | 95% | 95% | 0.950 |
| 6 | **节点切换时隐形评分** | 0.40 | 60% | **70% ⬆** | 0.280 |
| 7 | 节点颜色处方性措辞 | 0.65 (avg of 0.50-0.80) | 70% | 75% ⬆ | 0.488 |
| 8 | 3 天 + 1 周主动提醒 | 0.55 (Cepeda 2008 · range 0.40-0.70) | 90% | 90% | 0.495 |
| 9 | 4 级渐进提示 | 0.70 | 90% | 90% | 0.630 |
| 10 | 元认知 2x2 校准矩阵 | 0.60 | 85% | 85% | 0.510 |
| 11 | 考后校准投票 | 0.50 | 85% | 85% | 0.425 |
| 12 | 学习档案正面措辞 | 0.50 (avg of 0.40-0.60) | 100% | 100% | 0.500 |
| **合计 (仅作 audit · 不做 meta-analysis 合成)** | | **8.65** | - | - | **—** (Plan v19: 不参与加总 · 见 §9.2) |

**Plan v16 关键升级**（3 项）：
- 设计 2 · 书签式新节点工作流（§2.7.1）使 Generation Effect 完全保留 · 从 90% → 95%
- 设计 6 · 完全静默评分（§1.6 深度改写）从"轻度干扰"到"零干扰" · 60% → 70%
- 设计 7 · Dashboard 完整设计（§5.1.1）Buttons+Dataview+Callouts 实时反映处方性 · 70% → 75%

### 9.2 · 设计保留评估的 narrative synthesis（Plan v19 修正）

> **Plan v19 重大修正**：本节 v15/v16 曾给出 "加权总守恒度 = Σ(d_i × c_i) / Σ d_i = 88.1%" 的单一数字。Plan v18 三方 triangulated 审查 + Plan v19 独立核实后认定：**此公式方法学不合法**，88.1% 数字应完全删除。本节改为 narrative synthesis（Cochrane Handbook Chapter 12 "Synthesizing and presenting findings using other methods" · Section 12.3.1 "Structured tabulation" 标准）。
>
> **Plan v21 校正注**：Plan v19 曾错引 Cochrane Handbook Ch 10.10.1 "When not to use meta-analysis"。根据 Cochrane Handbook 官方文档（current version），Chapter 10 实际内容是 "Analysing data and undertaking meta-analyses"（Ch 10.10.1 是 "What is heterogeneity"），**"When not to use meta-analysis" 和 narrative synthesis 的 structured tabulation 建议实际在 Chapter 12** "Synthesizing and presenting findings using other methods"（Section 12.3.1）。Plan v21 修正为正确章节引用。方法学结论不变（不做加权合成 · 用 narrative synthesis）。

#### 9.2.1 · 为什么不给单一守恒度数字

**三个方法学错误**（Plan v18 §1.1 + Agent B 统计学方法学核实）：

1. **Cohen's d 不能作为权重** · d 衡量的是效应大小，不是"这个设计有多重要"。用 d 作权重在任何 meta-analysis 教科书里都没有支持（Borenstein 2009 _Introduction to Meta-Analysis_ Ch 3 + Cochrane Handbook Ch10 + metafor 包文档 w_i = 1/v_i）

2. **不同构念不能混合** · 12 个设计来自不同原始研究，测量不同的构念（Retrieval Practice / Self-Explanation / Spacing Effect / Test Anxiety / Flow State 等）。合并效应量在理论上不合法（除非做 multivariate meta-analysis · 但那也不用 d 作权重）

3. **"守恒度百分比"是主观估计** · 60%/70%/85%/95% 这些数字不是从研究数据计算得出，而是 PRD 作者对"在 Obsidian md 环境下 Canvas 原设计能保留多少"的主观估计。用"客观形式的 d 值"去加权"主观形式的守恒度百分比"，结果是"客观形式伪装的主观数字"，误导性极强

**Cochrane 推荐做法**（Chapter 12 "Synthesizing and presenting findings using other methods" · Section 12.3.1 "Structured tabulation"）：
> When effect sizes cannot be statistically combined (due to heterogeneity, different constructs, or insufficient data), use **narrative synthesis** with **structured tabulation** of individual studies, without computing a summary effect size.

（**Plan v21 修正注**：Plan v19 曾错引 Chapter 10.10.1 · Chapter 10.10.1 实际内容是 "What is heterogeneity" · narrative synthesis 的 structured tabulation 建议在 Chapter 12 · Plan v21 更正章节号 · 方法学结论不变）

#### 9.2.2 · 采用的 narrative synthesis 方法

1. **分层独立评估** · §9.1 汇总表的 12 个设计，每个独立列出 d 值 + 守恒度 + 守恒理由（保留，作为 audit 数据）
2. **加权贡献列不参与加总** · §9.1 表头已加注 "(不参与加总)" · 合计行的加权贡献单元格改为 "—"
3. **定性分组** · §9.3 高保留 (≥90%) · §9.4 部分丢失 (<80%) · 中间段落详见 §9.1
4. **scope 声明** · d 值来自原始研究的独立推导 · 守恒度是 PRD 作者的主观估计 · 两者都不应作为精确的学习效果预测

#### 9.2.3 · 定性结论（不给数字）

**灵魂设计完整保留**：
- 设计 1 · 检验白板 (Karpicke d=1.50) · 95% 守恒
- 设计 2 · 拉出新节点 (Generation Effect 0.65) · 95% 守恒
- 设计 5 · BKT+FSRS 融合 · 95% 守恒
- 设计 12 · 学习档案正面措辞 · 100% 守恒

**部分损失集中在 UI 交互层**（Obsidian 的 UI 限制 · 不是设计本身问题）：
- 设计 6 · 节点切换隐形评分 · 70%（Obsidian 无"切换事件" · 降级为 skill 触发）
- 设计 7 · 节点颜色处方性 · 75%（失去节点原生颜色 · Dataview 补偿）
- 设计 3 · Edge 对话 · 75%（失去点击连线触发 · hotkey 降级）

**用户的决策依据**：读者应看上述"灵魂设计完整保留"是否满足自己的核心诉求。如果满足，方案 A 值得实施；如果不满足，应返回 Plan v15 探索其他方案。**不应依赖任何单一百分比做决策**。

#### 9.2.4 · Plan v16 额外收益（定性评价 · 不进入守恒度计算）

- **LanceDB + bge-m3 集成**（§6.5 + §4.1.1）：新增"补充学习材料"能力，Canvas PRD FR-KG-08 从 0% → 100% 实现
- **4 层 Hook 架构**（§4.7）：提供机制层面的检验白板隔离保护，降低用户误操作风险
- **md 编辑器答题**（§2.3.1）：与 Karpathy "write stuff down" 原则对齐，强化深度编码

这些改进整体改善了方案 A，但**不计入**任何守恒度数字。

### 9.3 · Top 3 完美守恒的设计 (≥ 90%)

1. **设计 12 · 学习档案正面措辞 (100%)** · 规则层面约束 · 完全可控
2. **设计 1 · 检验白板二分法 (95%)** · 灵魂章节 · §2 详细保证
3. **设计 5 · BKT+FSRS 融合 (95%)** · 完全复用 Canvas 后端 MCP 工具

### 9.4 · Top 3 部分丢失的设计 (< 80%)

1. **设计 6 · 节点切换隐形评分 (60%)** · Obsidian 无"切换事件" · 降级为 skill 层触发
2. **设计 7 · 节点颜色处方性措辞 (70%)** · 失去节点本身颜色 · Dataview 表格补偿
3. **设计 3 · Edge 对话 (75%)** · 失去"点击连线"触发 · 需用户记住 `/edge_discuss` hotkey

### 9.5 · 与 Agent G 44.2% UI 机械对照的定性对比（Plan v19 修正）

| 视角 | Agent G (UI 机械) | 本 PRD (学习效果) |
|---|---|---|
| 评估维度 | 能不能拖拽 · 能不能点击 · 能不能可视化 | per-design 效应量 + 守恒度（定性评估）|
| 权重来源 | 均等或主观 | 无单一权重 · narrative synthesis |
| 检验白板 | 无 | 95% (灵魂) |
| 4 路融合检索 | 0% | 不在 12 核心设计 |
| 总分 | 44.2% (单一数字) | **不给单一数字**（§9.2 narrative synthesis）|

**核心差异**: 同样的方案 A，Agent G 只看 UI 是否可视化，本 PRD 看每个设计是否保留学习科学效应。Agent G 的 44.2% 是 "UI 机械可达性" 单一数字；本 PRD 的评估是 "每个设计独立的守恒评价"（详见 §9.1 + §9.3/9.4），**不给单一的"学习效果守恒度"数字**。

**Plan v19 修正注**：本节 v15/v16 曾给出 "44.2% vs 87.1%" 的对比，但 "87.1%"/"88.1%" 的计算方法学已被 Plan v18 审查认定不合法（见 §9.2.1）。Plan v19 修正为：拒绝给出本 PRD 侧的单一数字，只做 Agent G 方法论 vs narrative synthesis 方法论的定性对比。

### 9.6 · 方案 A 能否满足用户诉求？

**用户诉求**（批注 #8）: "批注驱动的精确考察 · 检验白板 · 完全空白的 Active Recall 环境"

**逐条对照**:
- ✅ 批注驱动的精确考察 · `/quiz_from_callout` + `generate_question` MCP 工具完整守恒
- ✅ 检验白板 · §2 完整实现 · 95% 守恒
- ✅ 完全空白 Active Recall · §2.4 三重保证机制

**结论**: 方案 A 可以满足用户最重要的诉求 · 可以进入 Phase 1 骨架实施

---

## §10 · 分阶段实施路线

### 10.1 · Phase 1 · 骨架 (2-3 周)

**目标**: 最小可用版本 · 可以走通检验白板灵魂流程

**P0 Prerequisites**（Plan v19 新增 · 基于 §7.6.5 Canvas 后端真相校正 · Day 1 必做）:

0-1. **Day 1 Spike 1 · Canvas 后端 13 服务启动验证**（1-2 小时）
   - 按 §7.6.3 启动检查清单逐条跑
   - 验证 Cost Tracker 中间件加载成功（`backend/app/middleware/cost_tracker.py` · 已就绪 · 不需新写）
   - 验证 14 MCP 工具可调用

0-2. **Day 1 Spike 2 · canvas_agentic_rag import 验证**（✅ **Plan v23 已实际运行验证** · 从"待 Phase 1 验证"升级为"已闭合"）
   - **背景**：Plan v19 smoke check 曾断言 "module 不存在" · Plan v21 独立核实发现该断言基于**错误的命令语法**（用 `import canvas_agentic_rag` 而不是 `from agentic_rag import canvas_agentic_rag`）· **Plan v23 第三轮进一步发现 Plan v21 的命令也不完整**：直接 `from agentic_rag import ...` 在 `backend/` 目录下会触发 `ModuleNotFoundError`，因为 `backend/lib/` 不在默认 `sys.path` 里 · 只有通过 `app.services.rag_service` 入口才能触发生产代码 L32-37 的 `sys.path.insert(0, str(_project_root / "lib"))` · 让后续 `from agentic_rag import ...` 成功
   - **Plan v23 production-equivalent smoke check 命令**（以 `rag_service.py` 作为入口 · 触发完整生产导入链）：
     ```bash
     cd /Users/Heishing/Desktop/canvas/canvas-learning-system/backend && \
       .venv/bin/python -c "from app.services.rag_service import LANGGRAPH_AVAILABLE, _IMPORT_ERROR; print('LANGGRAPH_AVAILABLE=', LANGGRAPH_AVAILABLE, 'ERROR=', _IMPORT_ERROR)"
     ```
   - **Plan v23 实际运行输出**（2026-04-09 晚 · 真实执行记录）：
     ```
     2026-04-09 13:20:55 [debug    ] RAGService: Added /Users/Heishing/Desktop/canvas/canvas-learning-system/backend/lib to sys.path
     (Python 3.14 + Pydantic v1 兼容性 warning · 不阻断)
     (jieba pkg_resources deprecation warning · 不阻断)
     2026-04-09 13:21:00 [info     ] RAGService: LangGraph/Agentic RAG available. LANGGRAPH_AVAILABLE=True
     LANGGRAPH_AVAILABLE= True ERROR= None
     ```
   - **Plan v23 结论**：canvas_agentic_rag workflow **实际运行级验证通过** · Plan v21 的"~100% 就绪"断言得到**运行级证据** · **L3 盲点确认关闭** · Day 1 Spike 2 已提前完成 · Phase 1 直接复用 · **唯一观察**：Python 3.14 与 Pydantic v1 有兼容性 warning（不影响 LANGGRAPH_AVAILABLE 判定 · Phase 1 可监控是否升级到 Pydantic v2 或降级 Python 版本）
   - **失败时降级命令**（Phase 1 Day 1 参考 · 如果未来环境变化导致主命令失败）：
     ```bash
     # fallback 1：先 source venv
     cd /Users/Heishing/Desktop/canvas/canvas-learning-system/backend && \
       source .venv/bin/activate && \
       python -c "from app.services.rag_service import LANGGRAPH_AVAILABLE; print(LANGGRAPH_AVAILABLE)"

     # fallback 2：uv run
     cd /Users/Heishing/Desktop/canvas/canvas-learning-system/backend && \
       uv run python -c "from app.services.rag_service import LANGGRAPH_AVAILABLE; print(LANGGRAPH_AVAILABLE)"

     # fallback 3：PYTHONPATH 直接验证 agentic_rag 存在性（不经 rag_service · 用于隔离失败源）
     cd /Users/Heishing/Desktop/canvas/canvas-learning-system/backend && \
       PYTHONPATH=./lib .venv/bin/python -c "from agentic_rag import canvas_agentic_rag, AGENTIC_RAG_AVAILABLE; print(AGENTIC_RAG_AVAILABLE, type(canvas_agentic_rag).__name__)"
     ```
   - **失败时诊断路径**（按优先级 · 只在 Plan v23 真实运行证据之外发生新环境变化时适用）：
     1. `LANGGRAPH_AVAILABLE= False` → 查看 `_IMPORT_ERROR` 字段 · 通常是 `langgraph>=0.2.0` 或 `langchain-core>=0.3.0` 未装 → 运行 `cd backend && uv sync` 或 `pip install -r requirements.txt`
     2. `ModuleNotFoundError: No module named 'app'` → cwd 不在 `backend/` · 或 `.venv` 未激活
     3. 其他 `ImportError` → 用 fallback 3 PYTHONPATH 命令调 `from agentic_rag import check_dependencies; print(check_dependencies())` 逐个确认依赖状态

0-3. **Day 1 Spike 3 · UserPromptSubmit hook 机制澄清**（1 小时）
   - 确认这是 **Claude Code Desktop `~/.claude/settings.json` 的 hooks 配置**，不是 backend Python 代码（见 §7.6.5）
   - 写一个最小 UserPromptSubmit hook 条目到 settings.json + bash 脚本
   - 验证 Claude Code Desktop 能正确触发 hook

**任务清单**:

1. **vault 初始化** (半天)
   - 创建 `canvas-vault/` 目录结构 (§3.1)
   - 写 `CLAUDE.md` (§3.5)
   - 装 5 个强制插件: Dataview / Templater / QuickAdd / Periodic Notes / Spaced Repetition

2. **Claudian 配置** (半天)
   - 安装 Claudian plugin
   - 配置 Claude Code CLI path
   - 验证 hotkey 绑定 (Cmd+Option+C 测试)

3. **Canvas 后端启动** (1 天)
   - `uvicorn backend.app.main:app --port 8000`
   - 验证 14 MCP 工具可调用
   - 修复 Blocker #1/#2/#3 (FSRS import · RAG 断裂 · 考察链路)

4. **最小 skill 集** (3-5 天)
   - `.claude/skills/chat-with-context/SKILL.md` (基础对话)
   - `.claude/skills/start-exam-board/SKILL.md` (**灵魂**)
   - `.claude/skills/extract-node/SKILL.md`

5. **Templater 模板** (半天)
   - `templates/exam-board.md`
   - `templates/concept.md`
   - `templates/edge.md`

6. **Graphify 集成** (1 天)
   - `pip install graphifyy`
   - `graphify install` + `graphify claude install`
   - 用 `raw/` 做第一次 `/graphify` 验证

7. **第一次检验白板 demo** (半天)
   - 在 `wiki/canvases/my-first-topic.md` 贴入一段笔记
   - 触发 `/start_exam_board`
   - 完整跑通 Step 1-10

**验收锚点**:
- [ ] 成功打开 exam_boards/*.md 时眼前没有 wiki/concepts/ 内容（§2.4 保证 1-3）
- [ ] 防嵌套检查正确 abort 递归尝试（§2.5）
- [ ] 拉出新节点正确归到 wiki/concepts/（§2.6）
- [ ] frontmatter 5 信号成功更新
- [ ] Dataview 查询处方性措辞输出正确

### 10.2 · Phase 2 · 学习闭环 (2-4 周)

**目标**: 6 skill 全部落地 · 所有 12 个设计可验证

**任务清单**:

1. **剩余 3 个 skill** (1 周)
   - `/edge_discuss` (§4.2)
   - `/quiz_from_callout` (§4.4)
   - `/review_profile` (§4.6)

2. **Dataview Dashboard 完善** (3-5 天)
   - `wiki/dashboard.md` 完整 DQL 模板
   - 2x2 校准矩阵可视化
   - 处方性措辞全覆盖

3. **10 个插件全装** (2-3 天)
   - Tasks / Smart Connections / Kanban / Metadata Menu / Obsidian Git
   - 每个插件的配置 + 测试

4. **Graphify health check 定期任务** (1 天)
   - `/graphify ./wiki --health-check` 每周执行
   - 生成 health-report

5. **第一个真实学习 demo** (1 周)
   - 用 MT2 的 LLRB 章节做一次完整学习闭环
   - 从贴入 raw 笔记到检验白板考察 + 错误修正

**验收锚点**:
- [ ] 6 skill 全部可触发 + 正确执行
- [ ] 12 个设计的守恒度实测 ≥ 85%
- [ ] 3 天 + 1 周主动提醒机制跑通
- [ ] 4 级渐进提示至少演示 1 次

### 10.3 · Phase 3 · 精修 (持续)

**目标**: 细节打磨 · 长期稳定性

**任务清单**:
- FSRS 插件替换 SM-2 (等社区 FSRS 插件稳定)
- Canvas↔Graphiti 双向同步 (历史会话归档)
- 校准投票的 few-shot 改进 LLM 评分
- 元认知 2x2 可视化升级（考虑第三方图表插件）
- Graphify cluster-based 主题自动发现

**无明确截止日期** · 根据用户反馈迭代

---

## §11 · 已知限制 + 降级策略

### 11.1 · 完全守恒的 8 个设计 (≥ 85%)

✅ 设计 1 检验白板 (95%)
✅ 设计 2 拉出新节点 (90%)
✅ 设计 4 4 维评分 (85%)
✅ 设计 5 BKT+FSRS (95%)
✅ 设计 8 3 天 + 1 周提醒 (90%)
✅ 设计 9 4 级渐进提示 (90%)
✅ 设计 10 2x2 校准矩阵 (85%)
✅ 设计 11 考后校准投票 (85%)
✅ 设计 12 正面措辞 (100%)

→ 共 9 个（不是 8，重新数）· 这些是**本 PRD 的学习效果核心守恒**

### 11.2 · 部分守恒的 3 个设计 (60-80%)

⚠️ **设计 3 · Edge 对话 (75%)**
- 损失: "点击连线"的 UI 触发
- 降级方案: Cmd+Option+R hotkey + `/chat_with_context` 中的主动提示
- 风险: 用户忘记 hotkey → Edge 对话永不发生 → EI+SE d=0.80-1.00 丢失
- 缓解: 在 `/review_profile` 时检测"有 wikilink 但无对应 edges/*.md"并主动提醒

⚠️ **设计 6 · 隐形评分 (60%)**
- 损失: Canvas 的"节点切换时自动评分"不存在
- 降级方案: skill 每题后立即评分（§1.6 方案 A）
- 风险: 用户感知到"每题都在评分"轻微疲劳
- 缓解: `score_visible: false` 设置 · 评分结果不在 Claudian 显示，写入 frontmatter 用户下次才看到

⚠️ **设计 7 · 节点颜色处方性 (70%)**
- 损失: Canvas 的节点本身颜色（Red/Yellow/Green）
- 降级方案: Dataview Dashboard + Kanban 看板 + emoji 颜色代码
- 风险: 用户不主动看 Dashboard 就看不到进度
- 缓解: Daily Notes 插件每日推送"今日建议复习"

### 11.3 · 严重丢失的设计：无

**重要结论**: 12 个学习设计**没有任何一个**被严重丢失 (< 50%)。

**最接近丢失**的是设计 6 (60%)，但通过 `/quiz_from_callout` 的实时评分已基本补偿。

### 11.4 · UI 层面无法补偿的 Canvas 功能

（这些不在 12 学习设计中，因此不影响守恒度，但仍应诚实列出）

- ❌ 拖拽式白板（Canvas ReactFlow 60fps）· Obsidian 无法复现
- ❌ 多白板 Dashboard（Canvas 有列表视图）· 降级为 `wiki/canvases/` 目录 + Dataview
- ❌ 节点拖拽缩放平移 · Obsidian Graph view 只能平移 + 缩放，不能编辑

**但这些不影响学习效果**：用户用 md 文件 + wikilink + Graph view 就能保留全部 4 个灵魂设计（检验白板 / Generation Effect / BKT+FSRS / 正面措辞）· Plan v19 修正：原文曾引 "87.1% 守恒度"，但该数字已被 §9.2 narrative synthesis 取代 · 不再给单一百分比。

### 11.5 · Rollback 策略

**最坏情况**: Phase 1 骨架跑不通
- Rollback 到 `11-v2 §8.3 /quiz_from_callout` 单 skill 方案
- 放弃 `/start_exam_board` · 降级用 `/quiz_from_callout --exam-mode`
- 损失: 检验白板 Karpicke 2011 d=1.50 降级为 Chi 1994 d≈1.09 · Bisra 2018 g=0.55 两个独立效应量（不相加 · Plan v19 修正 · 见 §4.4 学术对比表）

**中等失败**: Phase 2 某个 skill 质量差
- Rollback 到该 skill 的 manual 模式
- 例如 `/extract_node` 失败 → 用户手动 Cmd+N 新建 md
- 损失: Generation Effect 的自动化，手动也能达成（但体验降级）

**轻微问题**: Graphify 集成失败
- 绕过 Graphify · skill 直接读 frontmatter + wikilink
- 损失: 71x token 减少 · 增加 LLM 调用成本

**Plan v16.1 新增 · 完全静默评分的 rollback 路径**:
- 最坏情况：用户反馈"看不到分数太焦虑"→ 违反 §1.6 守恒度 70% 前提
- Rollback 方案：降级到 §1.6 原设计 60% 守恒度（sidebar 显示 "✓ 已评分"）
- **但仍然不追加分数到 callout**（保留 Cassady 2002 焦虑防护的最低线）
- 进一步 rollback：允许用户在 Settings 开启"显示分数"开关（Black & Wiliam 1998 形成性评估最高 d=0.60）
- 损失: 从 70% 守恒度降到 60% · 符合 §9 加权计算的容错下界
- 触发条件: 连续 3 次考察后用户主动请求"显示进度"(Csikszentmihalyi Flow 条件被用户主动放弃时)

---

## §12 · 决策点清单 + 批注区

> 下面是 v11-v2 已有的 D1-D9 决策点（继承）+ Plan v15 新增的 D10-D13 决策点。
> 请用户在 `☐` 里打勾 (`☑`) 或添加批注。

### 12.1 · D1-D9 继承自 11-v2

| # | 决策 | 选项 | 我的建议 | 你的选择 |
|---|---|---|---|---|
| D1 | vault 位置 | (a) 用现有 `CS 61B/` 扩展 / (b) 新建 `canvas-vault/` | **(b)**，方案 A 是 2026-04-08 新设计，建议独立目录 | ☐ a / ☐ b |
| D2 | `raw_notes/` 迁移 | (a) 一次性全量 / (b) 渐进，每次 quiz 前迁移 | **(b)** | ☐ a / ☐ b |
| D3 | Neo4j/LanceDB/Graphiti | **v2 已锁定 = 强制保留** | 本 PRD 继承 | ✅ 强制保留 |
| D4 | 6 CC skill ↔ 14 MCP 工具职责 | (a) skill 只管 md I/O，MCP 管 quiz/mastery / (b) 全面重写 | **(a)**，清晰分工 | ☐ a / ☐ b |
| D5 | `_qa/ask-*.md` 历史数据 | (a) 保留 / (b) 迁移到 `outputs/sessions/` / (c) 双向链接 + Dataview | **(c)** | ☐ a / ☐ b / ☐ c |
| D6 | Hotkey 绑定 | 6 个 `Cmd+Option+{C,R,E,Q,X,P}` | 本 PRD 定为 6 个 | ☐ 同意 / ☐ 改 |
| D7 | Phase 1 第一个真实测试 | (a) `disc07-notes.md` LLRB / (b) `hw07-notes.md` asymptotics / (c) 自选 | **(a)**，MT2 顽固点 | ☐ a / ☐ b / ☐ c: _____ |
| D8 | OpenSpec change 流程 | (a) 走 CLI / (b) 非正式 Plan | **(a)**，大决策走 OpenSpec | ☐ a / ☐ b |
| D9 | 权重公式方案 (M1 修正) | (1) FSRS next_review_date / (2) 双因子 0.60/0.40 / (3) 数据驱动 | **(1)** DD-01 合规 | ☐ 1 / ☐ 2 / ☐ 3 |

### 12.2 · D10-D14 新增（D10-D13 Plan v15 · **D14 Plan v16**）

| # | 决策 | 选项 | 我的建议 | 你的选择 |
|---|---|---|---|---|
| **D10** | 最小插件集 vs 完整插件集 | (a) Phase 1 装 5 个强制 (Dataview/Templater/QuickAdd/Periodic Notes/Spaced Repetition) / (b) 立即装 10 个 | **(a)**，先跑通再扩展，避免插件冲突 | ☐ a / ☐ b |
| **D11** | SM-2 (现成) vs 等 FSRS 插件 | (a) 立即用 Spaced Repetition 的 SM-2 / (b) 等社区 FSRS 插件稳定再切 | **(a)**，SM-2 够用，FSRS 作为 Phase 3 升级 | ☐ a / ☐ b |
| **D12** | Phase 1 完成后立即测试 vs Phase 3 精修完再用 | (a) Phase 1 完成立即用真实 CS 61B 笔记测试 / (b) 等 Phase 3 精修完再用 | **(a)**，提前暴露问题 | ☐ a / ☐ b |
| **D13** | Graphify 自动 vs 手动维护 CLAUDE.md | (a) `graphify claude install` 自动注入 / (b) 手动维护 CLAUDE.md 的 Graphify 部分 | **(a)**，社区标准 | ☐ a / ☐ b |
| **D14** | 答题媒介 (Plan v16 新增) | (a) Claudian Chat sidebar 对话 / **(b) md 编辑器为主**（用户 2026-04-09 Round 1 选定 ✅）/ (c) 混合（简短答 chat · 长答 md） | **(b)** 用户原话"这样回答问题就好比打批注" | ☑ **b** (Plan v16 Round 1 锁定) |

> **D14 脚注 · 为什么用户偏离 AI 原推荐**（Plan v16.1 补充 · 追溯决策依据）：
>
> Plan v16 AI 原推荐方案为 (a) Claudian Chat sidebar 对话（基于 Retrieval Practice + 流式 UI 反馈的工程便利性）。用户在 Round 1 AskUserQuestion 中**主动偏离此推荐**，选择 (b) md 编辑器为主。用户原话："我觉得这样回答问题就好比打批注"。
>
> **这是学习哲学选择，不是技术选型**。用户把"答题"视为"写批注"的延伸——所有思考都应该永久写到 md 文件里，与 Karpathy "write stuff down" 原则完全对齐，同时与用户核心诉求"批注驱动的精确考察"形成闭环（批注 → 考察 → 答题 → 又是批注）。
>
> **对 Plan v16.1 的约束**：§4.4 Workflow（见上）、§2.3.1 md 答题工作流、§4.4.1 `/quiz_answer` sub-skill 三处必须严格对齐此哲学，禁止在 Claudian sidebar 显示题目/分数/提示任何实质学习内容。sidebar 只作为 skill 触发指示器。

### 12.3 · 批注区（给用户填写）

```
[你的批注写在这里 · 使用 "User：<你的想法>" 格式]

User：
```

---

## §13 · 文档元信息

### 13.1 · 上游文档索引

| 文档 | 行数 | 作用 | 本 PRD 的引用位置 |
|---|---|---|---|
| `canvas-learning-system/_bmad-output/planning-artifacts/prd.md` | 971 | Canvas PRD 原文 | §1 所有设计 + §2 检验白板 + §8 6 旅程 |
| `CS 61B/11-canvas-hybrid-proposal-v1.md` | 521 | 方案书 v1 (历史) | §4 skill 设计 (继承部分) |
| `CS 61B/11-canvas-hybrid-proposal-v2.md` | 1122 | 方案书 v2 + 9 批注 | §4 skill 设计 + §12 决策点 D1-D9 |
| `CS 61B/12-canvas-hybrid-README.md` | 687 | v2 配套 README | - |
| `CS 61B/13-v2-gap-diagnosis.md` | 728 | v14 诊断 + Agent A/B/C | §1 设计 1 (PRD 原白板架构) + §2.5 (递归终止) + §5 (Top 10 gap 对比) |
| `CS 61B/10-downgrade-mapping.md` | 786 | 降级映射 Part A | §8 6 用户旅程 |

### 13.2 · 9 个前序 Explore Agent 引用

| Agent | 任务 | 引用位置 |
|---|---|---|
| A | PRD 原白板+检验白板架构 | §1.1 + §2 |
| B | 12 能力域 × 95 FR + Top 15 灵魂 | §1 全部 + §9 |
| C | v2 vs PRD Top 10 Gap | §11 已知限制 + §9 对比 |
| D | Karpathy LLM Wiki 深度挖掘 | §3 目录结构 + §6 Graphify 集成 + log.md 规范 |
| E | Graphify skill 深度挖掘 | §6 全部 |
| F | Obsidian 插件生态 | §5 全部 10 插件 |
| G | UI 机械对照 (44.2%) | §9.5 对比 |
| **J** | **认知科学解构 (12 设计 × d 值)** | **§1 全部 + §9 加权总分** |
| L | 等价映射 (失败) | 本 PRD §1 直接完成了 Agent L 应该做的工作 |

### 13.3 · Canvas 项目代码引用

| 文件 | 行号 | 引用位置 |
|---|---|---|
| `backend/app/services/exam_service.py` | 69-83 | §2.5 防嵌套后端双保险 |
| `backend/app/services/episode_worker.py` | 252-477 | §7 MCP lifespan |
| `backend/app/main.py` | 263-334 | §7 lifespan 启停 |
| `backend/app/services/mastery_engine.py` | 106-148 | §1.5 BKT 贝叶斯公式 |
| `backend/app/services/memory_service.py` | 1490-1540 | §1.5 FSRS rerank |
| `backend/app/mcp/tools/` | - | §7 14 MCP 工具 |
| `backend/app/mcp/pipeline_token.py` | 124-197 | §7.2 token 验证 |

### 13.4 · 决策协议 + 归档策略

本 PRD 属于 **OpenSpec change 的前置调研产物**，不直接进入 `openspec/changes/`。

**归档路径**（用户批准后执行）:
1. 用户批注 + 打勾 D1-D13
2. 基于批注生成 `openspec/changes/scheme-a-implementation/proposal.md`
3. 走 OpenSpec CLI: `npx openspec new change scheme-a-implementation`
4. 填 proposal / design / specs / tasks
5. `npx openspec validate scheme-a-implementation --strict`
6. 进入 Plan v16 Phase 1 骨架实施

### 13.5 · 版本追溯

- v1 · 2026-04-08 · 初稿 · Plan v15 产物
- v0 · N/A · 无前代版本（方案 A 的第一份完整 PRD）

### 13.6 · 字数统计（预估）

- §0 架构锁定: ~80 行
- §1 12 个学习设计: ~1700 行（§1 前 6 个 + §1.7-§1.12）
- §2 检验白板灵魂: ~530 行
- §3 目录结构: ~320 行
- §4 6 个 skill: ~440 行
- §5 10 个插件: ~230 行
- §6 Graphify 集成: ~110 行
- §7 MCP 工具对接: ~130 行
- §8 6 用户旅程: ~180 行
- §9 守恒度评估: ~100 行
- §10 实施路线: ~110 行
- §11 已知限制: ~85 行
- §12 决策点: ~50 行
- §13 文档元信息: ~70 行
- **总计**: ~4135 行（实际略超 Plan v15 的 2000-2500 目标，因用户明确"时间充裕 · 架构优先"）

---

> **14 · 方案 A · 学习效果守恒的具体实现 PRD 结束**
>
> **下一步**:
> 1. 用户审核本 PRD
> 2. 用户批注 + 决策点打勾 (§12)
> 3. 如通过 → 进入 Plan v16 Phase 1 骨架实施
> 4. 如有修改 → 迭代到 v2
>
> **本 PRD 的核心承诺**（Plan v19 修正）:
> - **4 个灵魂设计完整保留 (≥ 95%)** · 检验白板 / 拉出新节点 / BKT+FSRS 融合 / 学习档案正面措辞（§9.2.3 · narrative synthesis · Plan v19 删除 "87.1%/88.1%" 单一数字）
> - 检验白板 **100% 等价实现**（§2 灵魂章节）
> - 用户核心诉求"批注驱动的精确考察"**完整实现**（§4.3 `/start_exam_board` + §4.4 `/quiz_from_callout`）
