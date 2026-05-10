---
title: study-question Skill 完整设计报告（解题深度模式）
date: 2026-05-10
plan: EPIC1-BMAD-DEV-ASSESS-2026-04-17
trigger: 用户最早原话"我在解题的时候对待相关内容产生不解...需要全局搜索相关的教学笔记"
inputs:
  - 4 并行 agent deep explore (业界对照 / 技术方案 / Skill 机制 / 痛点边界)
  - Phase A0/A0.5/B0 实施现状
  - 用户给的 ground truth 输出样本 (1067+ 行 4 层结构)
status: 待用户批注 §8 4 个 Q → 选择 Phase 1 / Phase 1+2 实施
---

# Study-Question Skill 完整设计报告

> **核心问题**：用户最早提的"解题深度模式 skill"我们一直没做，光做了 hook RAG 改进。Hook 修了**召回精度**（A），但 4 个核心痛点（B 深度 / C 命令触发 / D 输出结构化 / E multi-hop）**hook 架构边界内做不到**。

---

## 1. 用户原始需求 vs 我们已做

### 1.1 用户最早原话（多次重复）

> "我在解题的时候对待相关内容产生不解还有一个就是对应的知识点不懂的时候，那么这时候我是需要全局搜索相关的教学笔记来给我回复"

> "建议启动并行 agent deep explore，查看社区成熟的案例，看怎么样检索的更加精确一点"

### 1.2 用户给的 ground truth 输出样本（1067+ 行）

用户最早问"什么是局部最优陷阱"得到的 Claude 回答含：
- **4 层结构**：定义 / 4 种解决方法 / 对比表 / 跟当前节点的关系
- **多 hop 联系**：lecture 4 → lecture 2 → 节点/规划的分类
- **完整章节引用**：lecture 4 第 990-1067 行
- **inline wikilink** + 末尾 supplementary 列表

**这个输出是 hook auto-RAG 单独产生的吗？— 不是**。它包含 multi-hop（lecture 4→lecture 2）+ 结构化合成 + 1067 行长 context — 这超出 hook 5s 预算 + 短 snippet 设计。

### 1.3 痛点分析（4 agent 共识）

| 痛点 | 描述 | hook 修了？ | study-question 要解？ |
|---|---|---|---|
| **A 召回精度漂移** | rank 8-10 含无关节点 | ✅ Phase A0 (commit aef95be) | ❌ 不重复 |
| **B 深度不够** | 10 条短 snippet (300字) + 无合成 | ❌ **5s 预算限制** | ✅ **核心** |
| **C 缺乏命令触发** | hook auto-trigger，用户无法主动深化 | ❌ 设计边界 | ✅ **必做** |
| **D 输出结构化** | "定义/方法/对比/关联" 四层 | ❌ hook 无 LLM 重排 | ✅ **prompt 层** |
| **E Multi-hop** | lecture 4 → lecture 2 自动联想 | ❌ Phase A0.5 明确不做 | ✅ **wikilink 2-hop BFS** |

**结论**：hook 解决了 A，但 B+C+D+E 仍然空白 — 这就是 study-question skill 必要性的来源。

---

## 2. 业界对照（Agent 1 调研产出）

### 2.1 8 个产品对照表（解题/学习场景特殊处理）

| 产品 | 关键机制 | 我们能借鉴的 |
|---|---|---|
| **Perplexity Deep Research** | Multi-pass query decomposition → 子问题独立检索 → cross-source 矛盾检测 → 800-1500 词结构化合成 | Query 拆解协议 + cross-source 一致性检查（标记冲突而非藏起来） |
| **NotebookLM Agentic Researcher** (2026) | 拆 sub-question + 标注 missing info + inline citation 指向具体段落 | "Missing info" 显式标注（不编造）+ citation 必须含 wikilink anchor |
| **Phind** (已关停) | Real-time curated 高质量源 + 强制 citation + 引擎不许"无源生成" | Citation-first：先列源再合成 |
| **Khoj GraphRAG** | 知识图谱 subgraph exploration — 多跳实体扩展（不止 vector sim） | wikilink 图遍历 N-hop |
| **CC-RAG / CausalRAG** (2025) | DAG of `<cause, relation, effect>` triples + forward/backward chaining 处理"为什么"查询 | "为什么 X" 类查询走因果链遍历，不走 vector |
| **StepChain GraphRAG** (2025) | BFS reasoning flow — 子问题 → 沿图边扩展 → 显式 evidence chain | 输出"推理链"而不是黑盒答案 |
| **SocraticLM / KELE** (2025) | 多 Agent: Teacher 拟答 → Dean 审查教学法 → 强制带反例 | 输出结构强制 "定义 → 直觉 → 反例 → 联系" |
| **EduChat** (arXiv 2308.02773) | 教育场景 fine-tune + Socratic prompt | 不需 fine-tune，prompt engineering 够用 |

### 2.2 关键学术教训

- **CausalRAG (ACL 2025)**: vector RAG 在"为什么"问题上失败 — 关键证据"语义不相似但因果相关"。**教训：解题 query 不能只靠 cosine sim**
- **FACTUM (2026)**: 57% 的 RAG citation 看起来在但实际不支持声明 — **必须做 citation back-verification**
- **NotebookLM Socratic tutor (arXiv 2504.09720)**: closed-RAG 显著降幻觉；inline citation 指向"精确段落位置"是用户信任前提

### 2.3 5 条核心建议（Agent 1 综合）

1. **Query intent 路由**：入口先 classify {Definition, Procedure, Causal, Comparison} → 4 套不同 retrieval pipeline
2. **Multi-hop wikilink BFS + 完整章节 read**：vector top-k 是种子；沿 wikilink 扩展 2-3 hop + Read 完整 lecture md
3. **强制结构化输出**（防 hallucinated bridges）：prompt 锁死段落 — `## 定义 / ## 直觉 / ## 反例 / ## 联系节点`
4. **Citation back-verification + missing info 显式标注**（防 FACTUM 现象）
5. **进度透明化 + 30-45s 预算**：超 60s 必须降级，不让用户瞎等

---

## 3. 4 类解题 Query + 路由策略

| Query 类型 | 例子 | 推荐处理 pipeline |
|---|---|---|
| **是什么 (Definition)** | "什么是局部最优陷阱" | vector top-k → Read 完整 lecture 章节 → 输出"严格定义 + 直觉 + 1 反例"三段 |
| **怎么做 (Procedure)** | "alpha-beta pruning 怎么用" | wikilink 1-hop 找父概念 + examples/ 文件夹习题 → "前提 → 步骤 → 完整例子" |
| **为什么 (Causal)** | "梯度下降为何震荡" | **不走 vector** — 走 prerequisite/cause 边图遍历（CC-RAG 思路）→ 因果链 + 每跳 cite |
| **联系 (Comparison)** | "梯度下降 vs 牛顿法" | 双 query 各 retrieve → wikilink 找共同祖先节点 → 输出"共性/差异/何时选谁"对照表 |

**关键**：Skill 入口先做 query intent classification（Claude Haiku 3.5，3s timeout，规则 fallback），不要一个 pipeline 套所有。

---

## 4. 技术方案（Agent 2 综合）

### 4.1 推荐方案：**A+B 混合实施**

```
Phase 1 (4-6h): Skill 直接调现有 search_supplementary
  ├─ 不加新 endpoint, 复用 hook 路径
  ├─ Skill prompt 锁住 multi-step + 结构化输出
  └─ Claude 200K context 自己 multi-step 推理

Phase 2 (+6-8h): backend 加 /api/v1/study/decompose-search endpoint
  ├─ 内部跑 multi_query_rewrite (复用 mastery_injection.py:296)
  ├─ 并行 N 次 supplementary → fuse + dedup
  └─ Skill 仅调一次拿合并结果
```

**总工时**：10-14h（Phase 1 + Phase 2）

### 4.2 跟现有 hook RAG 的协同关系

```
用户提问任意 query
       │
       ├─ Hook auto-inject (5s) → baseline 5-10 条 supplementary
       │  → 适合"快问快答"
       │
       └─ 用户主动 /study-question (30-45s) → 深度模式
          ├─ Query intent 分类 (Haiku 3s)
          ├─ Multi-query rewrite (拆 2-3 sub-query)
          ├─ Parallel retrieval (top_k_max=30, hard_cap=20)
          ├─ wikilink 2-hop BFS 邻居扩展
          ├─ Read 3 完整章节
          └─ Claude 结构化合成 (定义/方法/对比/关联)
```

**互补不冲突**：
- hook = 自动 baseline（每次提问都注入）
- study-question = 显式深化（用户主动等待 30s+）
- skill 进入时检查 additionalContext 是否已有 hook 注入 → 不重复召回相同 query，只补差集

### 4.3 关键参数对比

| 参数 | hook (auto) | study-question (manual) |
|---|---|---|
| 触发方式 | UserPromptSubmit auto | `/study-question` 命令 |
| 延迟预算 | 5s 严格 | 30-45s |
| top_k_max | 20 | **30** |
| hard_cap | 15 | **20** |
| Multi-hop | ❌ | ✅ wikilink 2-hop BFS |
| Query rewrite | ❌ | ✅ Haiku decompose 2-3 sub-query |
| Read 章节 | 0-1 个 | **3 个完整章节** |
| 输出结构 | 自由 | 强制 4 段（定义/方法/对比/关联） |
| Citation back-verify | ❌ | ✅ Claude 自查每个 wikilink |

---

## 5. Skill 实现（Agent 3 骨架）

### 5.1 文件位置

`canvas-vault/.claude/skills/study-question/SKILL.md`（新建）

### 5.2 Frontmatter schema

```yaml
---
name: study-question
description: "当用户消息以 /study-question 开头（通常由 Canvas plugin Cmd+Shift+Q 触发 + 剪贴板注入），必须调用此 Skill 进入解题深度模式。Story 2.3 v1.0：基于 hook auto-RAG baseline 之上，加入 query intent 分类、multi-query 拆解、wikilink 2-hop 邻居扩展、Read 3 完整章节、强制结构化输出。本 Skill 是纯诊断对话 — 不创建/不修改任何文件，区别于 ai-linked-doc 派生流程。"
argument-hint: "[由 plugin Cmd+Shift+Q 从剪贴板注入：用户问题 + 当前节点上下文]"
allowed-tools:
  - Read
  - Glob
  - Grep
model: sonnet
---
```

### 5.3 Skill body 完整骨架

```markdown
# Study-Question Skill v1.0 — 解题深度模式

## ⛔ HARD CONSTRAINTS（违反 = 任务失败）

1. **必须先 Query intent 分类**: Definition / Procedure / Causal / Comparison
   - 不分类直接答 → ❌
   - 分类用规则（关键词）+ Claude 兜底
2. **必须 Read 至少 3 完整 lecture 章节**（不只是 snippet）
   - 仅靠 supplementary snippet 答 → ❌
3. **必须 wikilink 2-hop BFS 找邻居**
   - 当前节点 → 1-hop 邻居 → 2-hop 邻居 (限 prerequisite/extends/refines 关系)
4. **输出必须 4 段结构**
   - `## 定义` / `## 直觉` / `## 反例 / 边界` / `## 联系节点`
   - Causal 类换成 `## 因果链` / `## 每步证据`
5. **每个声明必带 inline `[[wikilink#anchor]]`**
   - 无 wikilink 的句子标 `(推论)` 显式标注
6. **生成后 self-check**：每个 wikilink 是否真支持该声明
   - 找不到证据的声明 → 改为 `(vault 中无证据，AI 推断)`

## 触发识别

用户消息以 `/study-question` 开头（plugin Cmd+Shift+Q 触发）→ 立即进入本 Skill。
消息包含 `<study_context>` block：当前节点 + 问题 + N-hop 邻居（与 chat-with-context 同格式）。

## 执行 Pipeline (5 阶段，每阶段告诉用户进度)

### [1/5] Query Intent 分类（< 1s 规则匹配，兜底 Haiku）

```
关键词规则:
  "什么是 / 是什么 / 定义"     → Definition
  "怎么 / 如何 / 步骤"         → Procedure
  "为什么 / 因为什么 / 导致"   → Causal
  "X 跟 Y / X 和 Y / X vs Y"  → Comparison
```

### [2/5] Multi-Query Decomposition（Haiku 3s）
拆解策略按 intent 类型：
- Definition: 不拆，直接 retrieve
- Procedure: 拆"前提"+"步骤"+"例子"
- Causal: 拆"现象"+"原因"+"机制"
- Comparison: 拆"X 是什么"+"Y 是什么"+"X→Y 联系"

### [3/5] Parallel Retrieval（每 sub-query 调 search_supplementary）
- top_k_max=30, hard_cap=20, elbow_drop=0.05
- 复用 Phase A0/A0.5 修复（taint scan + chunks→source 回写）

### [4/5] Wikilink 2-hop BFS（基于当前节点）
- 1-hop: 直接邻居（来自 frontmatter relationships[]）
- 2-hop: 邻居的邻居（限 prerequisite/extends/refines 关系类型）
- callout 优先级: `[!error]+` > `[!question]+` > `[!tip]+`

### [5/5] Read 3 完整章节 + 结构化合成
- Read 前 3 名最相关 lecture 章节完整内容
- Claude 200K context 自己合成 4 段结构（按 §intent 路由）
- 每个声明 inline `[[wikilink#anchor]]`
- self-check 每个 citation

## 对话开场模板

```
[正在执行解题深度模式...]
[1/5] Query intent: <分类结果>
[2/5] 拆解为 <N> 个 sub-query
[3/5] 检索 <N> × 30 候选 → fuse <X> 条
[4/5] wikilink 2-hop 找到 <Y> 个邻居
[5/5] Read 3 完整章节 + 合成中...

🔍 解题诊断（基于 vault 真实材料）
```

## 边界（不该做的）

| 用户请求 | 该走哪 |
|---|---|
| "我想派生新节点" | `/ai-linked-doc` |
| "我要考自己" | 检验白板 (Story 6) |
| "纯本地不要 RAG" | `/node-chat` |
| "随便聊聊" | hook auto-RAG 默认即可 |
```

### 5.4 Plugin 集成（TypeScript）

```typescript
// frontend/obsidian-plugin/src/main.ts 加快捷键
this.addCommand({
    id: 'study-question',
    name: '深度解题模式 (study-question)',
    hotkeys: [{ modifiers: ['Mod', 'Shift'], key: 'Q' }],
    editorCallback: async (editor, view) => {
        const selection = editor.getSelection() || prompt('要解的题/概念：');
        const node = view.file?.path;
        const payload = `/study-question\n<study_context>\n  <user_question>${selection}</user_question>\n  <current_note>${node}</current_note>\n</study_context>`;
        await navigator.clipboard.writeText(payload);
        new Notice('已复制到剪贴板，请粘贴到 Claudian');
    }
});
```

---

## 6. ChatGPT V4 Deep Research Prompt

> 复制下面 `~~~~~~` 整段给 ChatGPT Deep Research：

~~~~~~
# Tech Decision: study-question Skill — 解题深度模式 RAG 设计对抗审查

## Context

仓库: https://github.com/oinani0721/canvas-learning-system
Branch: `worktree-feature-obsidian-hybrid-dev`

我设计了一个 `/study-question` Claude Code Skill — 用户在解题不懂时显式触发，做"深度教学笔记搜索"。当前 hook auto-RAG (commit aef95be) 解决了召回精度，但 4 个核心痛点 hook 架构边界内做不到：

- **B 深度不够**: hook 只 10 条短 snippet (300 字)
- **C 缺乏命令触发**: hook auto-trigger，用户无法主动深化
- **D 输出无结构**: hook 无 LLM 重排
- **E 无 Multi-hop**: lecture 4 → lecture 2 联系自动抓不住

## Our Proposed Design

详见 `_bmad-output/research/round-23-study-question-skill-design-2026-05-10.md`：

1. Query intent 路由 (Definition/Procedure/Causal/Comparison) → 4 套 pipeline
2. Multi-query rewrite (Haiku 3s) → 拆 2-3 sub-query 并行 retrieval
3. wikilink 2-hop BFS（限 prerequisite/extends/refines 关系）
4. Read 3 完整章节 + 强制 4 段输出结构（定义/直觉/反例/联系）
5. Citation back-verification（每个 [[wikilink]] 是否真支持声明）
6. 30-45s 总预算 + 进度透明化

工时: Phase 1 (skill+SKILL.md, 4-6h) + Phase 2 (backend decompose-search endpoint, 6-8h) = 10-14h

## 必读文件 (Tier 0)

- `_bmad-output/research/round-23-study-question-skill-design-2026-05-10.md` — 本设计完整
- `_bmad-output/research/round-23-multi-vault-implementation-plan-2026-05-10.md` — 多 vault 上下文
- `canvas-vault/.claude/skills/chat-with-context/SKILL.md` — 现有最相关 skill
- `canvas-vault/.claude/skills/node-chat/SKILL.md` — 节点级对话对照
- `canvas-vault/.claude/skills/ai-linked-doc/SKILL.md` — 派生节点对照
- `backend/app/api/v1/endpoints/chat.py:201-316` — `/api/v1/chat/enrich-context` 现有 endpoint
- `backend/app/api/v1/endpoints/chat.py:589-696` — `/api/v1/chat/rag/enrich-hook` hook (Phase A0.5-L 已加鉴权)
- `backend/app/services/supplementary_search_service.py` — 主管道（Phase A0.5-P taint 扫描）
- `backend/app/services/wikilink_context_service.py` — wikilink 图遍历
- `backend/lib/agentic_rag/mastery_injection.py:296` — multi_query_rewrite (复用)

## What I Need From You (5 Adversarial Tasks)

### 1. 验证我们的痛点诊断
hook 真的不能 multi-hop / 长 context 吗？还是我们没用对？读 hook endpoint 代码确认。

### 2. 挑战 4 类 query 路由设计
- "局部最优陷阱"是 Definition 还是 Procedure（带"怎么解"暗示）？分类边界如何处理？
- Causal 走"图遍历不走 vector"会不会丢真相关材料？
- 用 Haiku 分类 vs 规则关键词，哪个更稳？

### 3. 提出 2 套对抗替代方案

**方案 X**: 不新建 skill，而是**强化 chat-with-context** 加 query intent 路由 + multi-hop。理由：减少 skill 数量，降低用户认知负担。

**方案 Y**: 完全反其道 — 不做 query rewrite，而是**让 Claude Opus 用 200K context 直接读全 vault**（< 200K token 的 vault 都能塞）。理由：长 context 模型已经能 in-context multi-hop。

请对比我们的方案 vs X/Y，给决策矩阵。

### 4. 设计 study-question vs chat-with-context 边界
两个 skill 都做 RAG，怎么避免用户混淆？UI 怎么提示？

### 5. 评估 Phase 1（4-6h）就能 ship 吗
- 不加 backend endpoint，仅靠 SKILL.md + 现有 search_supplementary，能不能产出我们期望的"4 层结构"输出？
- 还是 Phase 2 backend endpoint 是必须？

## Constraints
- macOS M-series 本地 + 5s hook 预算保留
- bge-m3 embedding 锁定
- Apache-2.0 / MIT 兼容
- 不 fork Claudian
- 跟现有 4 个 skill (chat-with-context / node-chat / ai-linked-doc / configure-whiteboard) 边界清晰

## Output Format
1. 痛点诊断验证（hook 真做不到 multi-hop 吗）
2. 4 类 query 路由对抗结论
3. 方案 X / Y 决策矩阵
4. study-question vs chat-with-context UI 边界设计
5. Phase 1 vs Phase 2 必要性
6. 你的最大盲点是什么（一段长答）
~~~~~~

---

## 7. 用户决策点（请你勾选）

> [!question]+ Q1: Phase 1 vs Phase 2 实施范围
> - [ ] 选项 A: 只做 Phase 1（skill + SKILL.md + plugin Cmd+Shift+Q，4-6h）— 复用现有 search_supplementary
> - [ ] 选项 B: Phase 1 + Phase 2（含 backend decompose-search endpoint，10-14h）— 完整方案
> - [ ] 选项 C: 等 ChatGPT V4 反馈再决定

> [!question]+ Q2: Query intent 分类机制
> - [ ] 规则关键词（< 1ms，免费但可能漏分类）
> - [ ] Claude Haiku 3s（精准但延迟高）
> - [ ] 双层（规则优先，模糊 case 兜底 Haiku）⭐ 推荐

> [!question]+ Q3: study-question 触发方式
> - [ ] Plugin 快捷键 Cmd+Shift+Q（推荐，符合现有 Cmd+Shift+E/C/D 一致性）
> - [ ] 用户在 Claudian 直接打 `/study-question 概念`（无快捷键）
> - [ ] 双轨（快捷键 + 命令字都支持）

> [!question]+ Q4: 输出结构强制度
> - [ ] 强制 4 段 (定义/直觉/反例/联系)，违反 = Skill 失败
> - [ ] 推荐 4 段，但 Claude 可根据 query 类型调整
> - [ ] 完全自由（不强制结构，靠 prompt engineering 引导）⭐ 推荐

---

## 8. 关键文件参考

### 待新建（Phase 1）
- `canvas-vault/.claude/skills/study-question/SKILL.md` — Skill 主文件
- `frontend/obsidian-plugin/src/study-question-command.ts` — Plugin 快捷键

### 复用（不动）
- `backend/app/services/supplementary_search_service.py` — 主管道
- `backend/app/services/wikilink_context_service.py:317` — `enrich_from_wikilink_graph`
- `backend/lib/agentic_rag/mastery_injection.py:296` — `multi_query_rewrite`
- `backend/app/services/wikilink_graph_service.py` — BFS N-hop
- `backend/app/api/v1/endpoints/chat.py:201-316` — `/api/v1/chat/enrich-context` (现有)

### 可能扩展（Phase 2）
- `backend/app/api/v1/endpoints/chat.py` 加 `POST /api/v1/study/decompose-search`

---

## 9. ★ 关键 Insight

### 9.1 我们之前为什么漏了这个 skill

整个 session 我把焦点放在 hook RAG 改进（A0/A0.5/B0/Round-3/4），**忘了 hook 是 baseline 不是深度模式**。用户最早原话"全局搜索教学笔记"被我隐式理解为"hook 召回精度问题"，但实际上用户要的是**主动触发的深度学习辅助**。

**教训**：用户原话的"全局搜索"是表象，深层需求是"解题不懂时给完整解"。修 hook 召回精度只解决了表象，没碰深层需求。

### 9.2 hook 边界论 — 为什么 5s 预算硬性

hook 在每次提问都触发（auto），所以延迟必须 < 5s 否则破坏对话体验。这意味着：
- ❌ 不能加 query rewrite（多一次 LLM 调用）
- ❌ 不能 multi-hop（多次 retrieval）
- ❌ 不能 Read 完整章节（IO 慢）
- ❌ 不能强制结构化（需 LLM rerank）

**这些"不能"不是 hook 实现 bug，是 hook 设计哲学**。要在用户主动等待场景做这些 → 必须新建 skill。

### 9.3 业界共识 — 解题/学习场景必须 Multi-pass

8 个产品调研一致：Perplexity / NotebookLM / Khoj / CausalRAG / StepChain 全部用 multi-pass（query 拆解 → 多次 retrieve → 合成）。**单 pass RAG 在解题场景必然劣化**。我们的 study-question 设计直接对齐这个共识。

### 9.4 hook + skill 互补的工程哲学

- hook = 自动 baseline（每次都注入，5s 预算）
- skill = 显式深化（用户主动等待 30s+）

这是**性能/精度取舍的两个极**：
- hook 偏性能（5s）牺牲深度
- skill 偏精度（30s）牺牲实时性

**用户根据场景自己选**：快问快答用 hook，解题深挖用 skill。**不是替代关系，是协同关系**。

---

*Generated 2026-05-10 by 4 parallel agent deep explore (业界对照 / 技术方案 / Skill 机制 / 痛点边界) — 持续 ~7 min*

**Plan Anchor**: EPIC1-BMAD-DEV-ASSESS-2026-04-17
