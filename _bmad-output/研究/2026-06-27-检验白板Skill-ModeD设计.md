# 检验白板 Skill 设计（Mode D · Claude Code 订阅出题）

> 你定的方向：用 Claude Code(Claudian) 经 Skill 生成检验白板，Skill 合理调 Graphiti/后端拿数据。
> 3 并行 Explore agent 摸清技术现状后的设计。**设计先于代码，请你确认 §6 决策后我再建。**

---

## 1. 核心架构：Mode D —— 谁干什么

| 角色                           | 干什么                          | 用谁的钱                            |
| ---------------------------- | ---------------------------- | ------------------------------- |
| **Claude Code（Claudian 侧栏）** | **出题 + 评分**（读数据后自己生成题目、自己评分） | **你的订阅**（零 API 成本，不受 Gemini 封锁） |
| **后端 MCP 工具（纯数据）**           | 选薄弱节点、给批注/错误/原因/掌握度数据        | 不调任何 LLM                        |
| **Obsidian**                 | 你打开检验白板、md 编辑器手写答、Dashboard 看掌握度 | —                               |

**User：节点颜色你是干什么用的，我记得我很早就打上了相关的批注，来废弃这个功能了**
> **Claude 回应（查证后你是对的）**：节点颜色是 Tauri 时期 ReactFlow 白板按掌握度给节点上色，
> 你 2026-04-14 Round 4 已批注「**不需要染色**」废弃它（Obsidian md 也无法节点着色）。
> 正确的掌握度反馈 = **Dashboard 的 Dataview 表格**（处方性措辞"建议优先复习 X" + 🔴🟡🟢）。
> 我已把设计里所有"节点变色"改成"Dashboard Dataview 反馈"。（熟练度文档同处待改）
**关键**：**绕开**后端的 `generate_question`/`score_answer`（它们内部调 Gemini，地理封锁挂了）。改成 Skill 调纯数据工具 + Claude Code 用订阅出题/评分。

---

## 2. Skill 调哪些工具（已验证纯数据、不调 Gemini）

| MCP 工具 | 用途 | 调 Gemini? |
|---|---|---|
| `select_target_node` | **原白板级**选最该考的薄弱节点（FSRS+BKT+KG） | ❌ 纯算法 ✅可用 |
| `assemble_acp` | 拿节点的批注/错误/原因/掌握度数据包 | ❌ 纯数据 ✅可用 |
| `search_memories` | 查 Graphiti 记忆（批注/错误历史） | ❌ ✅可用 |
| `query_mastery` | 查 BKT+FSRS 掌握度 | ❌ ✅可用 |
| `update_bkt` / `update_fsrs` | 评分后更新掌握度 | ❌ ✅可用 |
| ~~generate_question~~ | ~~后端出题~~ | ⚠️ **调 Gemini，避开** |
| ~~score_answer~~ | ~~后端评分~~ | ⚠️ **调 Gemini，避开** |

> 你的 P0-P5 工作正好喂这条路：批注/原因已干净进 frontmatter + Graphiti，`assemble_acp`/`search_memories` 读得到。

---

## 3. 检验白板 Skill 工作流（从原白板发起一道题的最小闭环）

```
你在原白板（原白板/<board>.md）里 → Claudian 输 /start-exam-board
  ↓
① 防嵌套检查：当前文件 frontmatter type==exam_board？ 是→拒绝（不能在检验白板里再考）
  ↓
② select_target_node(原白板) → 后端按 FSRS+BKT 挑这个白板下最该考你的薄弱节点
  ↓
③ assemble_acp(节点) + search_memories(节点) → 拿你对这个节点的批注/错误/原因/掌握度
  ↓
④ 【Claude Code 用你的订阅出题】基于上述数据，生成"极其针对性、显式引用你批注原话"的题
   （如"你之前批注说『代理就是能感知环境的实体』，那它和'理性代理'的区别你怎么界定？"）
  ↓
⑤ 写检验白板 md：检验白板/<board>-<时间戳>.md
   - frontmatter type=exam_board（防嵌套）+ source_canvas + 选中节点
   - 正文只放题目 callout：> [!exam_question]+ Q1 · <节点>
                          > <题目>
                          > 答：
   - 【信息隔离】md 里不含节点原文定义；Skill 不向侧栏倾倒定义
  ↓
⑥ 你在 md 编辑器"答："下手写答案（像打批注一样）
  ↓
⑦ Cmd+Option+S 触发 /quiz-answer → 提取你的答案
  ↓
⑧ 【Claude Code 用订阅静默评分】读你的答案 + 该节点的标准 → 4 维打分
  ↓
⑨ update_bkt + update_fsrs（纯数据）更新掌握度 → 写节点 frontmatter mastery_level
  ↓
⑩ 静默：不显分、不打断。你考完打开 Dashboard 才看到掌握度变化
   （反馈=Dashboard Dataview 表格 + 处方性措辞"建议优先复习 X" + 🔴🟡🟢；
    **不是节点变色**——你 Round 4 已批注"不需要染色"，Obsidian md 也无法节点着色）
```

---

## 4. 信息隔离怎么保（Karpicke d=1.50 命脉）

三重保证（PRD §2.4）：
1. **检验白板 md 本身不含原文**：只有题目 callout，你打开看不到概念定义。
2. **Skill 禁止向侧栏倾倒原文**：Skill 出题时内部用到数据，但不把节点定义打印到 Claudian 侧栏（SKILL.md 里硬约束声明）。
3. **答题在 md 编辑器，不在侧栏**：你的注意力在检验白板 md 上，不切 Tab 看原文（切了 d=1.50 暴跌到 0.40）。
- 考中发现不懂的概念 → 不切 Tab，插一个 `> [!discussion_later]+ 📌 待剖析` 书签，考完再去原白板剖析。

---

## 5. 检验白板 md 结构（最小版）

```markdown
---
type: exam_board               # 🔴 防嵌套核心
source_canvas: <board-slug>
selected_nodes: [<节点>]
status: in_progress
created_at: <ISO>
questions:
  - id: q1
    concept: <节点>
    question_text: "..."
    user_answer: null
    score: null
---

# <board> — 检验白板

> [!exam_question]+ Q1 · <节点>
> <Claude Code 出的针对性题目>
>
> 答：
> (在这里手写你的回答)
```
- 落盘：`检验白板/<board>-<yyyy-mm-dd-hhmm>.md`（round-11 中文目录约定，非 PRD 的 exam_boards/）。

---

## 6. 请你拍板的决策（确认后我建）

### 决策 A：出题用 Claude Code 订阅 —— 已定（Mode D）✅
你已选。我按"Skill 拿纯数据 + Claude Code 订阅出题"建。

### 决策 B：评分也用 Claude Code 订阅？
- [x] **是**（推荐）：评分也走订阅（绕开 score_answer 的 Gemini），全程不碰 Gemini
- [ ] 否：评分先不做，只出题 + 手写答（评分以后再说）

### 决策 C：最小可用版范围（先做哪些）
建议 MVP 先做**单题闭环**（从原白板 → 选 1 个薄弱节点 → 出 1 道针对性题 → 手写答 → 静默评分 → 更新掌握度），跑通核心。**暂不做**：多题连续循环、考后校准投票、书签拉新节点、节点颜色实时变化。
- [x] 同意，先单题闭环
- [ ] 我要一次到位多题循环
- [ ] 我先只要"出题 + 手写答"，评分/掌握度以后

### 决策 D：触发方式 —— 已定 ✅
- [x] Claudian 侧栏输 `/start-exam-board`（纯 Skill）
     **User：也可以我在 claude code 中使用来出题** ← 已确认可行
- [ ] 也要一个 Obsidian 命令/快捷键触发（前端加个命令调 Skill）

> **查证结论（claude code CLI 出题）**：Claudian = "把 Claude Code 嵌进 Obsidian 侧栏"，
> 和 claude code CLI **同一引擎、同一 .claude/skills + mcp.json、同一订阅额度**
> (~/.claude/.credentials.json)。所以 `/start-exam-board` 在两处都能触发、都用订阅出题、
> 都能写 `检验白板/*.md`。
> **注**：`/start-exam-board` 是**新建 Skill**（现有的 `/exam-quick` 是不写文件的单题
> fallback，不是检验白板）。新 Skill 参照 `ai-linked-doc`（已证明 Skill 能 Write vault 文件）。

---

## 7. 这版和 PRD 的偏离（透明记录）
- PRD 工作流用 `generate_question`/`score_answer`（后端出题/评分）。本设计**偏离**为 Claude Code 订阅出题/评分（Mode D），因为：① 后端那俩调 Gemini，你地理封锁用不了；② 你明确要用 claude code/订阅。其余（信息隔离、原白板级选题、md 手写答、静默评分、防嵌套）**严格遵循 PRD**。
- 落盘目录用 `检验白板/`（round-11 扁平架构，更新于 PRD 的 `exam_boards/`）。
