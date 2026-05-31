# 锚定 PRD 关键章节节选 (原白板 + 检验白板设计)
> 来源: /Users/Heishing/Desktop/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md (7594 行, 只读)
> 本文件是节选, 供 ChatGPT 设计审查. 完整 PRD 是唯一真相源.


================================================================================
## [PRD 节选] §1 灵魂二分法 + 原白板 vs 检验白板 + Edge 对话 + 拉节点 (line 116-500)
================================================================================

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



================================================================================
## [PRD 节选] §2 检验白板 100% 等价实现 (灵魂章节) + frontmatter schema + /start_exam_board 10 步 (line 905-1210)
================================================================================

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



================================================================================
## [PRD 节选] 上下文隔离规则 + 三路融合 + reference_answer=None 五层数据流 (line 1522-1750)
================================================================================

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


================================================================================
## [PRD 节选] 检验白板 Tab 行为铁律 (Active Recall 保护) (line 2150-2200)
================================================================================

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


================================================================================
## [PRD 节选] concept md schema + edge md schema (line 3341-3470)
================================================================================

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



================================================================================
## [PRD 节选] §4 核心 Skill: chat_with_context + edge_discuss (line 3604-3760)
================================================================================

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


================================================================================
## [PRD 节选] /start_exam_board skill 定义 (line 3951-3990)
================================================================================

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


================================================================================
## [PRD 节选] §8 用户旅程 1 (原白板剖析) + 旅程相关 (line 6940-7060)
================================================================================

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
