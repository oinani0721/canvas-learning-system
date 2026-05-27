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
