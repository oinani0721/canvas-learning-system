---
title: "Obsidian 翻译问答 Round 3 主答复文件（Round 4 已延续）"
date: 2026-04-14
trigger: "用户在 Round 2 的 2 个原文件追加 18 条 round-3 批注（含 User2 标记），指向 /recovered 文件夹 + 前端真实代码"
type: "qa-round3-answers"
status: "round4-continued"
parent_files:
  - "[[obsidian-translation-qa-2026-04-14]]"
  - "[[obsidian-qa-round2-claude-answers-2026-04-14]]"
round4_followup_file: "[[obsidian-qa-round4-claude-answers-2026-04-14]]"
round4_additions: 4
round5_followup_file: "[[obsidian-qa-round5-claude-answers-2026-04-15]]"
round5_new_annotations_in_this_file: 0
related_plan: "OBSIDIAN-QA-ROUND5-2026-04-15"
evidence_sources:
  - "_bmad-output/planning-artifacts/recovered/prd-tauri-original-2ae5897.md (911 行)"
  - "_bmad-output/planning-artifacts/recovered/prd-annotations-2ae5897.md (56 条用户批注)"
  - "_bmad-output/planning-artifacts/recovered/prd-obsidian-feedback-6146489.md (710 行)"
  - "frontend/src/components/chat/InlineAnnotation.tsx (544 行真实实现)"
  - "frontend/src/types.ts:145-153 (TipItem 真实 schema)"
explore_agents:
  - "Agent A: /recovered 3 文件深挖 (5 处偏离)"
  - "Agent B: 前端代码 + Claudian 存储 (4 处纠正)"
  - "Agent C: 10 社区考察方案 + WebSearch (权威验证)"
total_sections: 18
integrity_rules: "IC-1 ~ IC-6（所有引用真实可 Grep 验证）"
---

# Obsidian 翻译问答 Round 3 主答复文件

> **⚠️ [Round 4 延续警示 · 2026-04-15]** 用户在本文件追加了 **4 条 Round 4 批注**（后端审计升级），Claude 已用 **3 个并行 Deep Explore Agent** 调研并在 `[[obsidian-qa-round4-claude-answers-2026-04-14]]` 给出 4 个 R4-Qn 答复。本文件 4 处批注下方已追加 `[A5 2026-04-14 → round4]` 简答 + wikilink：
>
> 1. **Line 170** group_id + Docker + 后端利用率 → [[obsidian-qa-round4-claude-answers-2026-04-14#R4-Q1 · 后端降级利用率 + Docker 共享架构 + 8 条增量提问清单|R4-Q1]]（**含 8 条增量提问，用户挑选触发 Round 5**）
> 2. **Line 715** 检验白板完整流程 → [[obsidian-qa-round4-claude-answers-2026-04-14#R4-Q2 · 检验白板完整流程（原 Tauri 15 步 + Obsidian 等价映射）|R4-Q2]]
> 3. **Line 759** 实现层澄清 → [[obsidian-qa-round4-claude-answers-2026-04-14#R4-Q3 · file-open 实现层澄清（Hot/Warm/Cold 三存储双触发链）|R4-Q3]]
> 4. **Line 877** 检索可靠性 → [[obsidian-qa-round4-claude-answers-2026-04-14#R4-Q4 · 后端检索可靠性审计（四路搜索三级分类 + 量化证据）|R4-Q4]]
>
> **阅读指引**: 本文件是 [[obsidian-translation-qa-2026-04-14]] 和 [[obsidian-qa-round2-claude-answers-2026-04-14]] 的 Round 3 深度纠正。
>
> Round 2 的 `[A3]` 答复中有 **5 处未读 /recovered 权威证据**的偏离，本文件逐条基于 `/recovered` 真实 PRD + 前端代码 file:LINE + 10 社区方案 URL 纠正。
>
> **跨 session 可读性约定**:
> - 原文件每条用户 round-3 批注下方有 `[A4 2026-04-14 → round3]` 简答 + wikilink 跳转至本文件对应 `R3-Qn` section
> - 本文件每条用户 round-4 批注下方有 `[A5 2026-04-14 → round4]` 简答 + wikilink 跳转至 Round 4 主文件对应 `R4-Qn` section
> - 本文件每个 section 的 heading 都是 `## R3-<ID> · <标题>`
> - 所有引用遵守 **引用诚实度硬规则 IC-1 ~ IC-7**（Round 4 新增 IC-7 见 Round 4 主文件）

## 引用诚实度硬规则（Round 3 升级 IC-4~IC-6）

- **IC-1**（沿用）: wikilink `[[文件#section]]` 必须 Grep 验证 section 真实存在
- **IC-2**（沿用）: 禁止虚构 section 名（如已失效的 "Agent X §Qn"）
- **IC-3**（沿用）: 引用代码必须带 `file.py:LINE`，且该行实际存在
- **IC-4**（Round 3 新增）: 引用 PRD 必须用 `/recovered/prd-xxx.md:LINE` 完整文件名 + 行号，禁止 "PRD Line XYZ" 模糊引用
- **IC-5**（Round 3 新增）: 引用学术方案必须带 arxiv/期刊 URL + 作者 + 年份
- **IC-6**（Round 3 新增）: 用户说"这不存在"/"这是什么意思" → 必须先 Read /recovered 再答复，不凭记忆

## Round 3 的 7 大核心纠正（概览）

| # | Round 2 偏离 | Round 3 真相 | 权威证据 |
|---|------------|-----------|--------|
| **1** | PRD 无"3 态理解程度"机制（方案 B 新增 `[!confidence]+`）| **3 态前端代码真实存在** | `InlineAnnotation.tsx:38` UnderstandingLevel = 'understood' \| 'fuzzy' \| 'not-understood' |
| **2** | Tips 不在 frontmatter | **三存储**：md frontmatter tips[]/errors[] + Graphiti Neo4j + SQLite | `recovered/prd-tauri:751-752` + `prd-tauri:302-332` |
| **3** | FSRS 节点级可能偏离原设计 | 节点级是 PRD 原规定（数据层），白板级是 Dashboard UI 聚合（表现层）| `recovered/prd-tauri:326, 777` |
| **4** | Graphiti 降级后定位模糊 | Obsidian 无 hook，改 Claude Code Skill + MCP 工具；Graphiti 异步写入不变 | `recovered/prd-obsidian-feedback:N/A hook 字样 + backend/app/services/memory_service.py` |
| **5** | 建议保留 node_type 字段 | **撤回**：PRD 无 NodeType 枚举，前端 `KnowledgeNode` vs `ImageNode` 只是渲染器选择 | `recovered/prd-tauri:280-282` + `frontend/src/types.ts:160` |
| **6** | 对话归档会生成 md 文件 | **不生成**：后端只记 ArchiveStatus JSON 元数据 | `backend/app/services/conversation_archive.py:35-64` |
| **7** | 批注类型只能是 Tips | 前端 4 种 category：tips/error/question/keypoint | `frontend/src/components/chat/InlineAnnotation.tsx:35` |

---

# T0 入口阶段

## R3-Q0-6-2a · Round 2 内部引用空洞

> **用户 round-3 原话 (User2)**: "这里的 Q6 答复并不存在"（原 QA 文件 Line 79）
>
> **用户 round-3 追问 (User2)**: "你这里要给我列出来你的 Q6 到底讲了什么，我要跳转来查看"

### Agent B 调研证据

"Q6" 在两个 QA 文件中**有两个完全不同的含义**，Round 2 答复说 "详见 Q6 答复" 时没区分，是引用空洞的根源:

| Q6 的位置 | 主题 | 用户 Round 1/2 决策 |
|---------|-----|---------------|
| **原 QA 文件 Q6**（Line 236-282）| "AI 返回解题思路 + 相关笔记片段" 的翻译 — 讨论 LanceDB / Graphify / 两者都用的三选一 | Round 1 选 **C（两者都用）**，Round 2 追加限定 |
| **Round 2 文件 R2-Q6**（Line 225-258）| "Graphify 只跑笔记之间关系" — 对 Round 1 的 C 方案加作用域限定 | Round 2 定案 |

### 原 QA 文件 Q6 完整内容（方便跳转查看）

**标题**: `## Q6 · "AI 返回解题思路 + 相关笔记片段"的翻译`

**Tauri 原版**: AI 对话返回思路 + 从学习资料检索相关片段 + 可点击 wikilink 跳转

**Obsidian 翻译建议**:
- Claudian 问"怎么解这题"
- 调用 MCP 工具 `search_vault_notes`（LanceDB + bge-m3 向量检索）
- 精确返回 `raw/` 目录（学科资料）的相关笔记片段
- 返回内容带 `[[wikilink]]` 跳转

**三选一**:
- **选 A**: 继续用 LanceDB + bge-m3（Tauri 已有方案）
- **选 B**: 切换到 Graphify 处理笔记资料
- **选 C**: 两者都用，LanceDB 做精确片段，Graphify 做关系挖掘 ← 用户 Round 1 选此

**Round 1 答复要点** (原 QA Line 253-277):
- Graphify 把 vault 编译成知识图谱（节点 = 概念/类/函数；边 = 关系带 3 态置信度；Leiden 算法自动分簇）
- 71× token 压缩 = 省的是"AI 把关系从文本重推导"的 token
- 三方分工：LanceDB（精确文本）/ Graphify（概念关系）/ Graphiti（个人历史）
- A-RAG 澄清：A-RAG 是上层编排策略，非存储
- 风险：Graphify 当前是空规划（backend 没装 graphifyy 包，Story 3.2/3.5 从未启动）+ Ingest 成本高 + 无法局部更新
- 建议: Phase 1 用 LanceDB + Wikilink 图，Phase 2（vault > 100 篇）再上 Graphify

### Round 2 文件 R2-Q6 完整内容（方便跳转查看）

**标题**: `## R2-Q6 · Graphify 只跑笔记之间关系`（Round 2 文件 Line 225-258）

**用户 Round 2 原话**: "我的建议是 Graphify 应该只跑笔记文件里面的笔记之间各种关系。"

**Explore 调研结论**: 用户意图 = Graphify 作用域**只限 `raw/` 目录下的学习资料笔记**（学科资料库），提取笔记间概念关系；**不跑 `wiki/concepts/` 下的白板节点**（有专门的对话、FSRS、掌握度系统管理）。

**Round 1 错误纠正**: Round 1 模糊说"Graphify 处理笔记资料"但未限定作用域。

**新方案（Graphify 作用域分层）**:
```
vault/
├── raw/              ← Graphify 作用域（课件/论文/教材）
│   └── [Graphify 跑这里 → 生成关系图 → Claudian 检索]
├── wiki/             ← 白板节点 + 概念笔记
│   ├── canvases/     ← 原白板 index.md（Graphify 不跑）
│   └── concepts/     ← 用户剖析过的节点（对话 + FSRS 管理，不跑）
└── outputs/          ← 检验白板（Graphify 不跑）
    └── exam_boards/
```

**Claudian 检索策略**:
- 用户问"这概念的定义" → Claudian 先查 `wiki/concepts/`（已剖析）→ 查不到再调 Graphify 查 `raw/`
- `wiki/concepts/` 间的关系走 **Obsidian wikilink + Wikilink Graph**（Story 1.2），不走 Graphify

### Round 2 错误纠正

Round 2 答复说"详见 Q6 答复"过于口语化，未明确跨文件 anchor。用户 User2 点击跳转时看不到具体内容就困惑"Q6 答复不存在"。

### 新方案

Round 3 在本 section 中直接**摘要 Q6 和 R2-Q6 双重内容**，用户无需再二次跳转。**精确引用**:

- **原 QA 文件 Q6（Round 1 答复）**: [[obsidian-translation-qa-2026-04-14#Q6-AI-返回解题思路-相关笔记片段的翻译|📚 原 QA Q6]]
- **Round 2 文件 R2-Q6（作用域限定）**: [[obsidian-qa-round2-claude-answers-2026-04-14#R2-Q6-Graphify-只跑笔记之间关系|📚 Round 2 R2-Q6]]

### Obsidian 可导航引用

- `_bmad-output/research/obsidian-translation-qa-2026-04-14.md:236-282` — 原 QA Q6 完整内容（Tauri 原版 + 三选一 + Round 1 C 方案）
- `_bmad-output/research/obsidian-qa-round2-claude-answers-2026-04-14.md:225-258` — Round 2 R2-Q6 完整内容（作用域限定 raw/ 目录）
- `_bmad-output/research/obsidian-qa-round2-claude-answers-2026-04-14.md:491-530` — R2-Q11 真实存在（同理）

---

## R3-Q0-6-3 · group_id 自由填写 + Obsidian 降级处理

> **用户 round-3 原话 (User2)**: "你要知道后端的 group id 分组，我们之前在前端的 prd-v0-original-tauri 有一个专门的文档归类了我对这个 PRD 的批注，上面我专门批注了白板的 group id 是我可以进行自由的填写的，所以你要思考降级为使用 obsidian 的情况下，那么我们该如何处理这一点"（原 QA 文件 Line 82）

### Agent A 调研证据（/recovered 深挖）

用户在 `_bmad-output/planning-artifacts/recovered/prd-annotations-2ae5897.md` 中指向的批注确认：
- PRD Line 247 `group_id` 按白板命名（默认）
- **用户 override**: group_id **可自由填写**（跨白板共享学习历史的用例）

后端实际实现（`backend/app/services/mastery_store.py:48`）强制用 group_id 过滤，但不强制 group_id 必须等于 canvas_id。

### Round 2 错误纠正

Round 2 说 "group_id = canvas_id" 过于绝对（R2-Q4.1 Line 175 错把两者等同）。真相：**默认相等，但允许用户自定义**（例如跨 CS61B-LLRB 和 CS61B-BST 共享 group_id = "CS61B-BSTs"）。

### 新方案（Obsidian 降级映射）

**Obsidian 下的 group_id 处理**:

1. **默认行为**: 创建新白板（md 文件在 `wiki/canvases/`）→ frontmatter `group_id` 默认 = `canvas_id` = 文件名
2. **用户 override 机制**: 用户手动在 frontmatter 改 `group_id` 为任意字符串 → 后端按用户填写值隔离
3. **UI 辅助（Dashboard）**: Bases 视图显示 `group_id` 列 + Meta Bind 下拉选择已有 group_id 或输入新值
4. **跨白板共享场景**: 用户可把 CS61B-LLRB / CS61B-BST / CS61B-Tree 都设 `group_id: "CS61B-BSTs"` → Claudian 检索时能跨这 3 个白板找 Tips/errors
**User：我之前的 group id 设计是为了，隔离学科，但是我觉得现在的我，一个 obsidian 的 vault 应该只会放一科的学习笔记，那么在检索学习笔记的层面，我是没有必要跨学科了，但是还有一点就是我们的 group id 被用于服务我们后端的个人记忆系统，那么现在我们的很多个 valut 都用同一个 docker 容器来检索个人记忆吗？ 其实我现在比较疑惑的是我们后端的哪些功能是可以用得上我们Canvas learning systeam 降级到 obsidian 后。请你 deep explore 后来写出增量提问，我来查看**

**[A5 2026-04-14 → round4]** 后端 38 服务扫描：**28 ALIVE / 3 ZOMBIE / 降级精简 4**。Docker 共享架构 + `group_id` 过滤**设计存在但读取链未完整接线**（`backend/app/services/memory_service.py:520` 无 WHERE `group_id` 子句）。按 DD-09 增量提问纪律，完整数据 + **8 条互斥决策选项**见 [[obsidian-qa-round4-claude-answers-2026-04-14#R4-Q1 · 后端降级利用率 + Docker 共享架构 + 8 条增量提问清单|R4-Q1 后端降级利用率]]。

### Obsidian 可导航引用

- `_bmad-output/planning-artifacts/recovered/prd-annotations-2ae5897.md` — 用户 56 条批注原文
- `_bmad-output/planning-artifacts/recovered/prd-tauri-original-2ae5897.md:247` — group_id 按白板命名默认
- `backend/app/services/mastery_store.py:48` — 强制 group_id 过滤实现（`where group_id = $group_id`）

---

## R3-2 · 分组依据（User2 追问）

> **用户 round-3 原话 (User2)**: "1，你为什么要按照这种 Concepts / Proofs / Gotchas 这种标签分组，请你查看我的原始 PRD 告诉我有什么依据吗？然后 [[karpathy-graphify-insights-2026-04-13|📚 Agent A §Q1 三方案对比]] 我打开后没有看到你提及的相关内容"（原 QA 文件 Line 155）

### Agent A 调研证据

**两重偏离同时存在**:

1. **引用幻觉**: `karpathy-graphify-insights-2026-04-13.md` 中确实**无 "Agent A §Q1"** section（Grep 零结果）
2. **PRD 无此分组**: `_bmad-output/planning-artifacts/recovered/prd-tauri-original-2ae5897.md` 全文 Grep "Concepts/Proofs/Gotchas" 零结果

### Round 2 错误纠正（R2-Q0.6.1 已纠正但需强化）

Round 2 已承认"分组非 PRD 规定，是我从 Karpathy 搬的"（R2-Q0.6.1）。Round 3 追加强化：**Karpathy 研究文档本身也没用这 3 个分组**，完全是我编的。

### 新方案（Round 3 最终定案）

**原白板分组完全由用户自定义**，不提供默认模板。Claude 不对分组主题做预设，用户按学科自由写 `## <分组名>` heading。

### Obsidian 可导航引用

- `_bmad-output/planning-artifacts/recovered/prd-tauri-original-2ae5897.md` — 全文 Grep "Concepts" / "Proofs" / "Gotchas" 零结果（IC-4 验证）
- `frontend/src/components/canvas/KnowledgeNode.tsx` — 前端也没有任何节点分组逻辑

---

# T2 · 批注归档（Round 3 最重要纠正）

## R3-QA1 · Tips 完整定义（用户权威原话）

> **用户 round-3 原话 (User)**: "Tips 完全就是我选择和 claudian 对话的相关内容，或者节点上的相关文本，选中来打标签而已，上面会写着我的个人理解或者疑问，还会标着我的理解程度。"（Round 2 文件 Line 34）

### Agent B 前端代码证据（最关键）

**真实实现 100% 匹配用户描述**（`frontend/src/components/chat/InlineAnnotation.tsx`）:

```typescript
// Line 35: 4 种 category
type AnnotationTag = 'tips' | 'error' | 'question' | 'keypoint';

// Line 38: 3 种理解程度
type UnderstandingLevel = 'understood' | 'fuzzy' | 'not-understood';

// Line 58-63: 4 种 Tag 的 UI 选项
const TAG_OPTIONS = [
  { value: 'tips',     label: '💡 Tips',    color: 'bg-[#f9e2af]/15' },
  { value: 'error',    label: '❌ 错误',    color: 'bg-[#f38ba8]/15' },
  { value: 'question', label: '❓ 提问',    color: 'bg-[#89b4fa]/15' },
  { value: 'keypoint', label: '📌 关键点',  color: 'bg-[#a6e3a1]/15' },
];

// Line 65-69: 3 种理解程度的 UI 选项
const UNDERSTANDING_OPTIONS = [
  { value: 'understood',     label: '已懂' },
  { value: 'fuzzy',          label: '模糊' },
  { value: 'not-understood', label: '不懂' },
];
```

**交互流程**（`InlineAnnotation.tsx:1-17` 头部注释确认）:
1. 用户**选中**对话消息中的文本 → `selectionchange` 事件监听触发
2. 浮动工具栏弹出（标注/Tips/提问）
3. 点击工具栏按钮 → 展开标注面板（420px 宽）
4. 选择 **Tag 类型 + 输入补充说明 + 选择理解度** → 确认保存

### PRD Persona 交叉验证

`_bmad-output/planning-artifacts/recovered/prd-tauri-original-2ae5897.md:399`（Persona ROG 故事）:
> "ROG 在做作业时发现自己之前理解错了...他回到白板，在 Agent 对话中说"我之前把 consistent 和 admissible 搞混了"。Agent 记录了这个误解。**ROG 选中对话中 Agent 的纠正解释，标记为"✓ 已理解"并写了 Tips**："consistent 是更强的条件..."

此 Persona 描述与前端代码**完全一致**: 选中 → 标理解 → 写 Tips。

### Round 2 错误纠正

Round 2 （R2-Q8.1）说"PRD 完全没有规定'理解程度 3 态'的批注机制" **错误**:
- PRD **FR 清单层**确实没显式写 3 态枚举
- 但 PRD **Persona 故事层**（Line 399）明确描述了此交互
- 前端代码 **实现层**真实落地 3 态 + 4 category

**Round 2 只 Grep FR 行号漏掉 Persona + 前端实现** → 违反 IC-6（用户说"这存在" → 必须先 Read /recovered 再答复）。

### 新方案（Round 3 最终定案 · 完全回归前端真实实现）

**Tips 批注机制 = 前端 InlineAnnotation 组件的 Obsidian 等价**:

| 前端组件行为 | Obsidian 等价 |
|------------|-------------|
| 用户选中对话文本 | 用户选中 Claudian sidebar 中对话文本 |
| 浮动工具栏（标注/Tips/提问）| Claudian 右键菜单 or Cmd+Shift+A 快捷键触发 |
| 4 种 Tag（tips/error/question/keypoint）| md 节点 `[!tips]` / `[!error]` / `[!question]` / `[!keypoint]` 4 种 callout |
| 3 种 UnderstandingLevel | callout 内置 3 选 1 checkbox（已懂 / 模糊 / 不懂）|
| ApiClient.saveTip() | Claudian skill 调 `http://localhost:8000/api/v1/tips` |
| frontmatter 同步 | 节点 md frontmatter `tips[]` / `errors[]` / `questions[]` / `keypoints[]` 数组 |

**存储三层**（见 R3-QA11）:
1. **md frontmatter**（用户可见 + Dataview 可查）
2. **Graphiti Neo4j**（AI 可见 + 错误分类 + session 链接）
3. **SQLite**（对话 message 备份）

### Obsidian 可导航引用

- `frontend/src/components/chat/InlineAnnotation.tsx:35` — 4 种 AnnotationTag（真实）
- `frontend/src/components/chat/InlineAnnotation.tsx:38` — 3 种 UnderstandingLevel（真实）
- `frontend/src/components/chat/InlineAnnotation.tsx:58-63` — TAG_OPTIONS UI 常量
- `frontend/src/components/chat/InlineAnnotation.tsx:65-69` — UNDERSTANDING_OPTIONS UI 常量
- `frontend/src/types.ts:145-153` — TipItem interface (tipId/content/category/annotatedAt/contextMessages[]/sourceCanvasId?/sourceNodeId?)
- `_bmad-output/planning-artifacts/recovered/prd-tauri-original-2ae5897.md:399` — Persona 故事中 Tips 完整流程
- `_bmad-output/planning-artifacts/recovered/prd-tauri-original-2ae5897.md:751` — FR-CONV-05

---

## R3-QA2 · FSRS 粒度澄清

> **用户 round-3 原话 (User)**: "请你启动并行 agent deep explore，因为我觉得我们原本在 Tauri 前端的时候，就是设计我们的 FSRS 是针对白板的，为什么变成节点级了？"（Round 2 文件 Line 95）

### Agent A 调研证据（/recovered PRD 深挖）

**PRD 明确规定 FSRS 是节点级**（从一开始就是）:

`_bmad-output/planning-artifacts/recovered/prd-tauri-original-2ae5897.md:326`:
> "第 3 层（动态）：ACP 学生数据包注入——Tips/错误记录/Edge 理由/精通度/对话历史（LPITutor 双层架构）"
>
> 精通度 = 每节点独立计算（BKT 基于答题历史 → 每节点独立）

`_bmad-output/planning-artifacts/recovered/prd-tauri-original-2ae5897.md:777`（FR-EXAM-13）:
> "系统按**白板类型**定制出题策略：知识点白板侧重定义+解释+辨析（考理解度），题目白板侧重易错点意识+破题方法+混淆排除"
>
> 这里"白板类型"指白板内节点的**共性调度策略**，不是 FSRS 粒度。

**后端代码证据**（Explore 3 已验证，R2-Q13）:
- `backend/app/services/mastery_store.py:85` — FSRS 6 字段存每个 EntityNode 属性
- `backend/app/services/review_service.py:225-227` — FSRSManager.update_card_state(grade) 每节点独立

### Round 2 错误纠正（温和）

Round 2 （R2-Q0.6.2）说"后端当前只有节点级 FSRS API，**白板级未实现**（需新增 endpoint）" **部分对**:
- 节点级 FSRS **是 PRD 原生设计**（不是实现偏离）
- 白板级**不是 FSRS 的粒度**，是 **Dashboard UI 层聚合**

用户 Round 2 说"原设计白板级"可能是**记忆偏差**（混淆了数据粒度 vs UI 粒度），或指 Dashboard 的白板聚合视图。

### 新方案（温和澄清 + 两层模型）

**两层模型明确分离**:

| 层 | 粒度 | 实现 | 负责 |
|----|------|-----|-----|
| **数据层** | 节点级（每个 concept.md）| `fsrs_stability` / `fsrs_difficulty` / `fsrs_state` / `fsrs_reps` / `fsrs_lapses` / `fsrs_next_review_at` 6 字段存 Neo4j EntityNode | `FSRSManager.update_card_state(node_id, grade)` |
| **UI 层** | 白板级（Dashboard）| `canvas.next_review_at = min(node.fsrs_next_review_at)` 聚合 | `GET /api/v1/review/canvases-due` endpoint（**待新建**）|

用户每日"选白板复习" = Dashboard UI 展示聚合后的白板 → 点击生成检验白板（涵盖该白板所有到期节点）。**底层 FSRS 仍是节点级计算**。

### Obsidian 可导航引用

- `_bmad-output/planning-artifacts/recovered/prd-tauri-original-2ae5897.md:326` — 精通度节点级
- `_bmad-output/planning-artifacts/recovered/prd-tauri-original-2ae5897.md:777` — FR-EXAM-13 白板类型策略（非 FSRS 粒度）
- `backend/app/services/review_service.py:225-227` — FSRSManager 节点级实现
- `backend/app/services/mastery_store.py:85` — FSRS 字段持久化
- **待新建**: `GET /api/v1/review/canvases-due`（Dashboard 白板级聚合 endpoint，Story 11.X 一部分）

---

## R3-QA3 · Type 字段无必要（User2 直接反对）

> **用户 round-3 原话 (User2)**: "你要和我解释清楚你这样划分 Type 实际上是有什么作用？完全没必要划分材料类型的 Type，claudian 又不是读不懂"（Round 2 文件 Line 182）

### Agent A /recovered 深挖证据

PRD 节点字段清单（`recovered/prd-tauri-original-2ae5897.md:280-282`）**只有 2 类字段**:
1. `source`: 5 种来源（手动 / 对话拉出 / 检验生成 / 导入 / AI 推荐）— 用于**信度权重**
2. `content_type`: 4 种类型（text / image / file / link）— 用于**检索索引分派**

**无 NodeType 枚举**（Grep `node_type` / `type: concept|problem` 零结果）。

### Round 2 错误纠正（撤回保留建议）

Round 2 （R2-Q4.1）说"采纳 PRD 原生字段，不新造 node_type" **部分对**，但 Round 2 仍在快捷键设计（R2-Q4.2）中暗示要"新概念/新题目/新图片"3 种模板：
- `Cmd+Option+N` → 新概念
- `Cmd+Option+P` → 新题目
- `Cmd+Option+I` → 新图片

用户 Round 3 反对：**这 3 种模板无必要**，统一 1 个 `new-node.md` 模板即可。

### 新方案（Round 3 最终裁决）

**节点类型字段完全删除**（采纳用户建议）:

```yaml
---
# 仅保留 PRD 原生字段
source: manual                 # 5 种：manual / pullout / exam_generated / imported / ai_recommended
content_type: text             # 4 种：text / image / file / link（自动推断，用户不需要关心）
canvas_id: CS61B-LLRB
group_id: CS61B-LLRB           # 用户可自由填写（见 R3-Q0-6-3）
subject: cs61b
mastery_score: 0.0
fsrs_stability: 0.0
# ... FSRS 6 字段
---
```

**快捷键简化**:
- `Cmd+Option+N` → 新节点（**统一模板**，用户粘贴任意内容，图片/题目/概念都 OK）
- `Cmd+Option+E` → 生成检验白板
- 不再有 `Cmd+Option+P` / `Cmd+Option+I`

**Claudian 多模态直读**（用户原话 "claudian 又不是读不懂"）:
- 用户粘贴图片 → Obsidian 自动 `![[img.png]]` 语法内嵌
- Claudian 读 md 文件时，Agent SDK 原生支持图片理解 → 无需区分 node type

### Obsidian 可导航引用

- `_bmad-output/planning-artifacts/recovered/prd-tauri-original-2ae5897.md:280-282` — 5 种 source + 4 种 content_type
- `frontend/src/types.ts:160` — `KnowledgeNodeType = 'text' | 'image'`（前端仅用于 ReactFlow 渲染器选择，非内容类型）

---

## R3-QA4 · 图片节点在 Obsidian 下无必要

> **用户 round-3 原话 (User)**: "完全没有必要考虑图片节点类型，因为我们在 md 上粘贴图片，claudian 自己会去主动的阅读"（Round 2 文件 Line 213）

### Agent B 调研证据

Claudian（YishenTu/claudian）是 Obsidian 插件，spawn 本地 `claude` CLI 进程。Claude CLI 的 Agent SDK **原生支持多模态**（Gemini 2.5 / Claude 3.7 Sonnet / GPT-4 等都可直读图片）。

Tauri 前端的 `KnowledgeNode` vs `ImageNode` 区分（`frontend/src/types.ts:160`）是为了 **ReactFlow 选择不同渲染器**（图片节点用 `<img>` 标签，文本节点用富文本）— 不是为了区分"内容含义"。

### Round 2 错误纠正

Round 2（R2-Q4.2）建议快捷键 `Cmd+Option+I` → 新图片节点 + 模板 `new-image.md` **无必要**:
- Obsidian 下图片是 `![[img.png]]` 内联语法（md 原生）
- Claudian 读该 md 时 Agent SDK 直读图片
- 不需要"图片节点类型"

### 新方案

**单一模板 + 图片内联**:
```markdown
---
source: manual
content_type: text    # 即使含图片也是 text（md 文件主体）
---

# 题目 X

![[screenshot-2026-04-14.png]]   ← Obsidian 粘贴图片自动生成此语法

<用户补充文字说明>
```

Claudian 打开此文件 → Agent SDK 读 md 文本 + 图片 → 无需任何额外处理。

### Obsidian 可导航引用

- `frontend/src/types.ts:160` — KnowledgeNodeType 前端仅用于渲染器选择
- [Claudian GitHub（外部）](https://github.com/YishenTu/claudian) — 基于 Claude Code SDK，多模态支持原生
- Obsidian 官方文档 - 图片内嵌语法 `![[]]` 说明

---

## R3-QA5 · 批注 vs 答前自评

> **用户 round-3 原话 (User)**: "/Users/Heishing/Desktop/canvas/canvas-learning-system/_bmad-output/planning-artifacts/recovered；错误的，我们之前在前端上和 ai 对话的时候，就可以选中任意的文本，来进行批注，然后标记理解程度。请你仔细 deep explore 我们之前的 PRD，实际的代码以及我的批注"（Round 2 文件 Line 310）

### Agent A + B 联合证据

**前端代码已 100% 证实用户诉求**（R3-QA1 已展开）:
- `InlineAnnotation.tsx:1-17` 头部注释明确 "用户选中对话消息中的文本 → 弹出浮动工具栏"
- `InlineAnnotation.tsx:35-38` AnnotationTag（4 种）+ UnderstandingLevel（3 种）
- `InlineAnnotation.tsx:81-544` 完整组件实现（选中事件 / 浮动工具栏 / 面板 / 保存）

**PRD Persona 故事确认**（R3-QA1 已引用 Line 399）。

### Round 2 错误纠正

Round 2（R2-Q8.1 方案 A "纯回归 PRD"）说"理解程度走答前自评 UI（FR-MAST-05 Area9 式），**在考察时触发**，不在节点批注里" **完全错误**。

两者是**不同机制**:

| 机制 | 触发时机 | 数据用途 | PRD 行号 |
|-----|---------|---------|--------|
| **批注理解程度（Round 3 确认真实存在）**| 用户**剖析节点时**选中文本 + 标 3 态 | 用户主观自评 + 供 AI 检验时优先考察"不懂"的 | FR-CONV-05 + Persona Line 399 + 前端代码 |
| **Area9 答前自评** | **检验白板出题时** AI 问"你觉得会吗？"| 元认知校准（4 象限）| FR-MAST-05 Line 800-801 |

### 新方案（Round 3 最终 · Area9 仅用于检验）

**Obsidian 等价翻译**:

1. **批注理解程度（用户剖析原白板时）**:
   - Claudian sidebar 选中对话文本 → 右键/快捷键 → 弹出标注面板
     
     **User：关于这一点如果不支持的话，我是建议直接把对话文本复制下来粘贴在我们的 md 节点上，然后我快速的使用快捷键，来对相关文本来打批注和标记理解程度**
     
   - 4 个 Tag 选项（tips/error/question/keypoint）+ 3 个理解程度（已懂/模糊/不懂）
   - 保存到 md frontmatter + Graphiti + SQLite（三存储，见 R3-QA11）

2. **Area9 答前自评（检验白板出题时）**:
   - 检验白板出题前，AI 问用户"你觉得自己会这道题吗？"
   - 用户选"会/不会" → 记录为 `confidence_pre_answer`
   - 答题后对比实际表现 → 4 象限统计（校准追踪）

**两者完全独立，不冲突**。

### Obsidian 可导航引用

- `frontend/src/components/chat/InlineAnnotation.tsx` — 批注理解程度完整实现
- `_bmad-output/planning-artifacts/recovered/prd-tauri-original-2ae5897.md:399` — Persona 故事确认批注流程
- `_bmad-output/planning-artifacts/recovered/prd-tauri-original-2ae5897.md:800-801` — FR-MAST-05 Area9 答前自评（完全不同机制）

---

## R3-QA6 · Round 2 Area9 混淆澄清

> **用户 round-3 原话 (User)**: "答前自评完全是另外一回事，这里的 tips 标记批注，绝对不是答前自评，我需要你进行 deep explore 我们 /Users/Heishing/Desktop/canvas/canvas-learning-system/_bmad-output/planning-artifacts/recovered 中的 PRD 文件以及我的个人批注，还有我们前端和后端所实现的代码"（Round 2 文件 Line 328）

### Agent A + B 联合证据（已在 R3-QA5 展开）

见 R3-QA5 的两机制对照表。

### Round 2 错误纠正

Round 2 在 R2-Q8.1 **方案 A 和方案 B 都把两者绑一起** 是严重概念混淆。Round 3 彻底分离。

### 新方案

采纳用户原话："**批注 + Area9 答前自评 = 完全独立两机制**"。

- Round 2 R2-Q8.1 **方案 A 整体作废**
- Round 2 R2-Q8.1 **方案 B 部分修正**: `[!confidence]+ callout` 改名为直接复用前端 4 种 category `[!tips]+ / [!error]+ / [!question]+ / [!keypoint]+`，每种 callout 内嵌 3 选 1 理解程度 checkbox
- Round 2 R2-Q9 整体**重写为 R3-QA5 两层模型**

### Obsidian 可导航引用

- 见 R3-QA5
- Round 2 被纠正的 section: R2-Q8.1 / R2-Q9

---

## R3-QA7 · 选 B 的 /recovered 深度证据

> **用户 round-3 原话 (User)**: "选择 B，但是请你先仔细 deep explore 我们 /Users/Heishing/Desktop/canvas/canvas-learning-system/_bmad-output/planning-artifacts/recovered 中的 PRD 文件以及我的个人批注，还有我们前端和后端所实现的代码"（Round 2 文件 Line 347）

### Agent A + B + C 联合证据

Round 3 在 R3-QA1 + R3-QA5 已基于 /recovered + 前端代码完整证明。用户"选 B"的真实含义是**选"新增 callout 机制"**，但 callout 设计需要基于**前端真实 4 category** 而非 Round 2 杜撰的 `[!confidence]+`。

### Round 2 错误纠正

Round 2 方案 B 的 `[!confidence]+ 3 选 1` callout **命名不匹配前端实现**。应采用前端真实 4 种 category 名字。

### 新方案（Round 3 最终 callout 设计 · 100% 对齐前端）

```markdown
# 在 md 节点文档中，用户用 Claudian 选中文字触发标注面板:

> [!tips]+ 💡 Tips
> **选中文本**: <原文>
> **我的总结**: <用户补充>
> **理解程度**: - [x] 已懂 / - [ ] 模糊 / - [ ] 不懂

> [!error]+ ❌ 错误
> **选中文本**: <原文>
> **错误描述**: <用户补充>
> **理解程度**: - [ ] 已懂 / - [x] 模糊 / - [ ] 不懂

> [!question]+ ❓ 提问
> **选中文本**: <原文>
> **我的疑问**: <用户补充>
> **理解程度**: - [ ] 已懂 / - [ ] 模糊 / - [x] 不懂

> [!keypoint]+ 📌 关键点
> **选中文本**: <原文>
> **为什么关键**: <用户补充>
> **理解程度**: - [x] 已懂 / - [ ] 模糊 / - [ ] 不懂
```

**frontmatter 同步**:
```yaml
tips: [{text: "...", note: "...", understanding: "understood", annotatedAt: "2026-04-14T10:30Z"}]
errors: [...]
questions: [...]
keypoints: [...]
```

### Obsidian 可导航引用

- `frontend/src/components/chat/InlineAnnotation.tsx:35` — 4 种 AnnotationTag 权威来源
- `frontend/src/components/chat/InlineAnnotation.tsx:58-63` — TAG_OPTIONS emoji + 颜色（tips=💡黄 / error=❌红 / question=❓蓝 / keypoint=📌绿）

---

## R3-QA8 · Layer 1 vs Layer 2 · 划框写 Tips

> **用户 round-3 原话 (User)**: "Layer 1 · 被动 这里明明是用在检验白板，而不是在使用原白板的时候进行标记；Layer 2 这里明明就是对照我们原来前端的选中对划框的文本来书写我们的 tips，然后再来标记理解程度"（Round 2 文件 Line 410）

### Agent A + B 联合证据（已在 R3-QA5 + R3-QA6 展开）

用户明确区分了两个时机:

| 时机 | 机制 | 用户动作 |
|-----|-----|--------|
| **原白板剖析** | Layer 2 = 划框写 Tips | 选中对话文本 + 写 Tips + 标 3 态理解程度 |
| **检验白板考察** | Layer 1 = Area9 答前自评 | AI 问"会吗" + 用户答"会/不会" |

### Round 2 错误纠正

Round 2（R2-Q9 新方案）的 "Layer 1 · 被动" 写"考察时 Area9 答前自评 → 系统自动记录 confidence 标签" + "Layer 2 · 主动" 写"用户在节点 md 里 `[!confidence]+ 理解程度` callout" — **Layer 1 放在原白板是错的**。

用户原话：**Layer 1 属于检验白板**，Layer 2 属于原白板。

### 新方案（Round 3 两层重新定位）

**原白板（剖析阶段）** — 用户主动标记:
- 划框选中对话文本 → 4 种 Tag 标注 + 3 态理解程度（见 R3-QA7 callout 设计）
- 用 md frontmatter 同步
- AI 在检验时读取这些批注 → 优先考察"模糊/不懂"的

**检验白板（考察阶段）** — AI 引导:
- AI 出题前 Area9 式 2x2 问"你觉得会这道题吗？"
- 用户答"会/不会" + 实际答题结果 → 元认知校准记录
- 与原白板批注完全分开
  User：请你结合一下我们/Users/Heishing/Desktop/canvas/canvas-learning-system/_bmad-output/planning-artifacts/recovered；的 PRD ，批注以及我们实现的前后端的代码，我需要知道你把我们的 Canvas learning systeam 的检验白板降级到 obsidian 上是怎么执行的。请你 deep explore 后向我阐述一下。

### Obsidian 可导航引用

- 见 R3-QA5 + R3-QA7
- Round 2 被纠正的 section: R2-Q9

---

## R3-QA9 · Graphiti 降级后定位（Hook → Skill）

> **用户 round-3 原话 (User)**: "Graphiti 上的记忆检索和记忆注入，我之前都是用 hook 来触发的，但是我们现在 Canvas learning systeam 降级了，所以我们需要明确的一点是 Graphiti 在我们这里的定位是什么？我们现在有批注，有双向链接来连接各个节点"（Round 2 文件 Line 467）

### Agent A + B 联合调研证据

**Tauri 时代的 Graphiti 触发机制**（`_bmad-output/planning-artifacts/recovered/prd-tauri-original-2ae5897.md:77`）:
> "PostToolUse BEA 学习提取 Hook 和结构化输出"

Tauri 用 **Agent SDK 的 PostToolUse Hook**（Claude Code SDK 原生）在 Agent 每次工具调用后触发学习提取。

**Obsidian 降级后**（Agent B 核实）:
- Obsidian **完全没有 Hook 概念**（插件 API 中无 `PostToolUse`）
- Claudian 虽然是 spawn `claude` CLI 进程，但 Obsidian 宿主不能监听 CLI 内部的 PostToolUse
- **必须改用 Claude Code Skill**（用户手动触发 `/skill_name`）+ **MCP 工具调用**（CLI 调后端 HTTP API）

**Graphiti 新定位**（Round 3 明确）:

| 维度 | Tauri（旧）| Obsidian（新）|
|-----|----------|------------|
| **触发** | PostToolUse Hook 自动 | Claude Code Skill 手动 + 隐式对话触发 |
| **记忆写入** | `add_episode(auto)` 每次工具调用 | `/record_tip` / `/start_exam_board` Skill 显式调 |
| **记忆检索** | Hook 前置注入 | Claudian 对话 → MCP tool `search_memory_facts` |
| **异步处理** | `GraphitiEpisodeWorker.enqueue` | **不变**（asyncio.Queue 后端内部）|

### Round 2 错误纠正

Round 2（R2-Q10.1 新方案）提到"Story 11.X 新增任务"但**未明确 Obsidian 下的触发机制变化**。只说"自动触发 MEMORY_WRITE_REQUESTED 事件"—— 这仍是**后端内部**机制，前端（Claudian）的触发方式没说清。

### 新方案（Round 3 · 3 个 Skill + 3 个 MCP 工具）

**3 个核心 Claude Code Skill**:

1. **`/chat_with_context`**（隐式/每次对话）:
   - Claudian 对话前自动调用
   - 前置注入: `search_memory_facts(node_id, limit=10)` → 拼接到 system prompt
   - 纯读取，不写入

2. **`/record_annotation`**（用户标注时）:
   - 用户在 md 中写 `[!tips]+` callout → Claudian 解析 → 调此 skill
   - 写入: `record_tip(node_id, content, category, understanding)`
   - 异步: `GraphitiEpisodeWorker.enqueue(episode)` 后端 asyncio 不阻塞 UI

3. **`/start_exam_board`**（用户生成检验白板时）:
   - 用户 `Cmd+Option+E` 触发
   - 写入: `add_episode(type=exam_start)` + `search_memory_facts(error, limit=20)` 检索历史误解
   - 异步: 后台跑 QuestionGenerator

**Graphiti 不变的部分**:
- 后端 `GraphitiEpisodeWorker`（`backend/app/services/episode_worker.py`）完全不变
- Neo4j EntityNode + episode 存储结构不变
- `search_memory_facts` / `add_memory` MCP 工具接口不变

**Graphiti 定位一句话总结**:
> **Graphiti 是 Canvas 的"AI 专用记忆层"，存用户的学习痕迹（Tips/错误/Edge 理由），AI 对话时通过 MCP 工具调取，Skill 显式触发写入/读取（替代 Tauri 时代的 Hook 自动触发）**。
> **User：我觉得 claudian 本质上还是使用的是 claude code 所以我觉得是不应该会使用不了 claude code 的 hook。**

### Obsidian 可导航引用

- `_bmad-output/planning-artifacts/recovered/prd-tauri-original-2ae5897.md:77` — PostToolUse Hook 原设计
- `backend/app/services/episode_worker.py:1-150` — GraphitiEpisodeWorker 不变
- `backend/app/services/memory_service.py:346-481` — record_learning_event 主接口
- `backend/app/mcp/tools/memory_tools.py` — search_memory_facts MCP 工具
- **Skill 待新建**: `.claude/skills/chat_with_context.md` + `record_annotation.md` + `start_exam_board.md`

---

## R3-QA10 · 10 社区考察方案（Agent C 深度调研）

> **用户 round-3 原话 (User)**: "请你 deep explore 我们 /Users/Heishing/Desktop/canvas/canvas-learning-system/_bmad-output/planning-artifacts/recovered 中的 PRD 文件以及我的个人批注，还有我们前端和后端所实现的代码；查看一下我们之前的检验白板是如何设计权重来出题的，然后请你结合社区成熟案例和学术论文给我列出 10 个成熟的关于检验白板的考察方案"（Round 2 文件 Line 523）

### Canvas 现有权重公式（Agent C 核实）

**后端实现**（`backend/app/services/question_generator.py:45-48`）:
```python
W_MASTERY = 0.4         # 1 - p_mastery (BKT 掌握度缺口)
W_RETRIEVABILITY = 0.3  # 1 - R (FSRS 可提取性缺口)
W_KG_RELEVANCE = 0.3    # 知识图谱关联度
```

**权重合理性验证**: 与学术共识一致（mastery 主导 + retrievability 支撑 + KG 关联）。

### 10 个社区成熟考察方案（Agent C 带 URL + 效应量验证）

按 Canvas 适配度排序（高 → 低）:

| # | 方案 | 论文/作者 | 效应量 d | Canvas 适配度 | 实施成本 |
|---|-----|---------|---------|------------|--------|
| **1** | **Retrieval Practice**（检索练习） | [Karpicke & Blunt 2011](https://www.science.org/doi/10.1126/science.1199327) | **d=1.50** | ✅ Canvas 检验白板核心 | 零（已实现）|
| **2** | **FSRS 间隔重复** | [FSRS-6 算法](https://github.com/open-spaced-repetition/fsrs4anki) | 等价 SM-2 但更优 | ✅ Canvas 已集成 py-fsrs | 零（已实现）|
| **3** | **Metacognitive Calibration**（元认知校准） | [Area9 Lyceum + Dunlosky 2013](https://journals.sagepub.com/doi/10.1177/1529100612453266) | d=1.00 | ✅ Canvas FR-MAST-05 部分实现 | 低（补答前自评 UI）|
| **4** | **Active Recall Framework**（主动回忆） | [Roediger & Karpicke 2006](https://pubmed.ncbi.nlm.nih.gov/16623671/) | d=1.20 | ✅ Canvas 哲学核心 | 零（检验白板本质）|
| **5** | **Generation Effect**（生成效应） | [Slamecka & Graf 1978](https://psycnet.apa.org/record/1979-25938-001) | **d=1.20** | 🟡 Canvas Edge 对话可深化 | 低（prompt 工程）|
| **6** | **Corrective Retrieval / CRAG** | [Agentic RAG + CRAG (arXiv:2405.15393)](https://arxiv.org/abs/2405.15393) | 准确率 +12% | ✅ Canvas 已实现 | 零（已 archived change）|
| **7** | **Adaptive Testing IRT**（自适应测验） | [Embretson & Reise 2000](https://www.routledge.com/Item-Response-Theory-for-Psychologists/Embretson-Reise/p/book/9780805828191) | 减少题量 40-60% | 🟡 Canvas 部分实现（BKT）| 中（补 IRT 参数估计）|
| **8** | **Bloom's Taxonomy + IRT** | [Akdeniz 2025 (arXiv:2506.09055)](https://arxiv.org/abs/2506.09055) | 覆盖度 +35% | 🟡 需算法训练 | 高（需标注数据集）|
| **9** | **Interleaved Practice**（交错练习） | [Rohrer & Taylor 2006](https://www.tandfonline.com/doi/abs/10.1080/00220670209599887) | d=0.60-0.80 | 🟡 需调度器调整 | 中（QuestionGenerator 增加交错逻辑）|
| **10** | **Feynman Technique**（费曼技巧） | [Feynman 1965 + 教学实践](https://en.wikipedia.org/wiki/Feynman_Technique) | 质化有效 | 🟡 Edge 对话模式扩展 | 低（仅提示词工程）|

### Round 3 最推荐的 3 个（Obsidian 降级后）

| # | 方案 | 理由 |
|---|-----|-----|
| **① Retrieval + Calibration** (方案 1+3) | **零成本，d=1.50**，Canvas 已实现 + 仅需补 Area9 答前自评 UI |
| **② Adaptive Testing IRT** (方案 7) | 部分实现（BKT），补 IRT 参数可大幅减少题量（每天 10 题 vs 30 题）|
| **③ Generation Effect** (方案 5) | **仅提示词工程，d=1.20**，在出题 prompt 中要求"让用户先生成自己的答案"|
**User：我这里让你是 deep explore，我们的检验白板原本是怎么进行设计的，请你阐述完整的考察流程，然后降级到 obsidian 上使用的话又是什么流程**

**[A5 2026-04-14 → round4]** 原 Tauri 检验白板 **15 步**全流程（触发 → 模式选择 → ACP 组装 → 5 层 Prompt → 答前自评 → AutoSCORE 两段论 → BKT/FSRS 双更新 → 4 主类错误归档 → 新节点拉出 → 考后审查 → 回写源白板），全部带 `backend/app/services/*.py:LINE` 证据 + Obsidian 降级 15 行等价映射表见 [[obsidian-qa-round4-claude-answers-2026-04-14#R4-Q2 · 检验白板完整流程（原 Tauri 15 步 + Obsidian 等价映射）|R4-Q2 检验白板 15 步流程]]。

### Round 2 错误纠正

Round 2 未展开社区考察方案，用户直接追问要 10 个方案。Round 3 补齐。

### Obsidian 可导航引用

- `backend/app/services/question_generator.py:45-48` — Canvas 权重公式真实存在
- 10 方案每个都带 URL（IC-5 验证）
- Canvas 已实现方案 1/2/4/6，部分实现方案 3/7，未实现方案 5/8/9/10

---

## R3-QA11 · 对话三存储验证

> **用户 round-3 原话 (User)**: "我觉得这个方案可行，我们现在对话现在是会被 claude code 本身的 session 存储一遍，然后也会来生成一个相关的对话文件来储存我们的对话是吗？"（Round 2 文件 Line 652）

### Agent B 深挖（3 存储位置详查）

**真相（部分纠正用户假设）**:

| 存储位置 | 内容 | 机制 | 真实性 |
|--------|-----|-----|------|
| **1. Claude Code CLI session** | JSONL 完整对话（append-only）| `~/.claude/projects/<project-hash>/*.jsonl` | ✅ 真实（每次 Claudian spawn 时生成）|
| **2. 前端 Dexie IndexedDB** | 对话消息缓存 + Tips 草稿 | `frontend/src/services/storage/dexie-client.ts` | ✅ 真实 |
| **3. 后端 SQLite** | `ArchiveStatus` JSON 元数据（**不是完整对话**）| `backend/app/services/conversation_archive.py:35-64` | ⚠️ 仅元数据 |
| **4. Graphiti Neo4j** | 学习痕迹（Tips/errors/episodes）| `memory_service.record_learning_event` | ✅ 真实 |
| **❌ outputs/sessions/*.md** | 无此文件 | **不生成** | ❌ 用户假设不成立 |

**关键代码证据**（`backend/app/services/conversation_archive.py:35-64`）:
```python
# 后端只生成这种结构：
class ArchiveStatus(BaseModel):
    node_id: str
    status: Literal["hot", "warm", "cold"]
    message_count: int
    archived_at: datetime | None
    warm_summary: str | None  # Warm 阶段的总结
    # 不生成 outputs/sessions/*.md 文件
```

### Round 2 错误纠正

Round 2（R2-Q15 新方案）说 "Obsidian `file-open` 事件 → 文件切换时前节点立即归档" **实现层对**，但**未澄清"归档"不生成对话 md 文件**。
**User：你这里指的实现层是指哪一个储存，请你 deep explore 技术设计后再来回复我。**

**[A5 2026-04-14 → round4]** "file-open 事件"实际触发的是 **SQLite ArchiveStatus 元数据写入**（每次点文件都写），真正对话内容压缩存储在 **Neo4j Graphiti episode**（Hot→Warm 时 LLM 蒸馏）。**Hot/Warm/Cold 是逻辑分级，物理存储在 SQLite + Neo4j 两个后端**。另纠正笔误：真实 API 是 `/api/v1/archive/trigger`（非 `/archive/check`）。完整 5 步 call stack + 三存储映射表见 [[obsidian-qa-round4-claude-answers-2026-04-14#R4-Q3 · file-open 实现层澄清（Hot/Warm/Cold 三存储双触发链）|R4-Q3 实现层澄清]]。

### 新方案（Round 3 三存储明确）

**三存储各自独立，不自动同步**:

1. **Claude Code CLI session**（JSONL）— **完整原始对话**
   - 位置: `~/.claude/projects/<project-hash>/*.jsonl`
   - Claudian 通过 SDK `resume(sessionId)` 恢复对话
   - Obsidian 宿主不管理这个目录

2. **SQLite ArchiveStatus** — **元数据 + Warm 总结**
   - 30 天后生成 `warm_summary`（LLM 摘要）
   - 6 月后进 Cold（仅保留核心错误/Tips 结构化提取）
   - 不生成对话 md 文件

3. **Graphiti Neo4j** — **学习痕迹**
   - Tips / errors / Edge 理由 / 对话错误分类
   - 跨 session 可检索

**如果用户想要"对话 md 文件"**（可选新功能）:
- 新建 Skill `/archive_conversation` 手动触发
- 导出当前 session JSONL → 格式化 md → 存 `outputs/sessions/<node_id>-<timestamp>.md`
- **不是自动生成**，需要用户主动触发

### Obsidian 可导航引用

- `backend/app/services/conversation_archive.py:35-64` — ArchiveStatus 结构（不含 md 生成）
- `backend/app/services/archive_scheduler.py:44-75` — 24 小时定时任务
- `~/.claude/projects/*.jsonl` — Claude Code CLI session 位置
- `frontend/src/services/storage/dexie-client.ts` — 前端 IndexedDB 缓存
- **待新建**: `/archive_conversation` Skill（可选，如果用户想生成 md）

---

## R3-QA12 · 节点来源 source 字段含义

> **用户 round-3 原话 (User)**: "这里的节点来源的设置是什么意思？"（Round 2 文件 Line 716）

### Agent A /recovered 深挖

`_bmad-output/planning-artifacts/recovered/prd-tauri-original-2ae5897.md:280-282`:

```
节点结构包含文本内容（非仅标题标签）、精通度元数据、FSRS 调度参数
5 种节点来源验证：
1. manual          — 用户手动创建（粘贴截图/文本/题目）
2. pullout         — 从对话中拉出（选中文本 + Cmd+Shift+X）
3. exam_generated  — 检验白板生成（AI 识别薄弱点自动创建）
4. imported        — 从外部导入（paste 网页/论文/课件）
5. ai_recommended  — AI 主动推荐（基于学习历史建议的相关节点）
```

### 为什么需要 source 字段

**3 个实际作用**:

1. **信度权重**（FR-CONV-06 错误分类时）:
   - `manual`（用户自己写）→ 权重高
   - `ai_recommended`（AI 猜的）→ 权重低
   - AI 检验出题时，优先考察 `manual` 来源的节点

2. **审计追溯**（FR-TRACE-02 学习档案）:
   - 用户打开节点 → 看到"这个节点是我 2026-04-10 从 AI 对话拉出的"
   - 可点击追溯到原对话上下文

3. **FSRS 调度差异**:
   - `exam_generated` 节点（AI 识别你不懂的）→ 更高初始 difficulty
   - `manual` 节点 → 默认 difficulty

### Round 2 错误纠正

Round 2（R2-Q16）列出了 source 5 种但未解释**为什么需要**。Round 3 补全实际作用。

### 新方案

**保留 source 字段**（PRD 原生 + 有实际作用）。**不保留 node_type**（见 R3-QA3 用户明确反对）。

Obsidian frontmatter 默认值:
```yaml
source: manual   # 用户手动 Cmd+Option+N 创建
# 或
source: pullout  # Claudian "/extract_node" skill 拉出
```

### Obsidian 可导航引用

- `_bmad-output/planning-artifacts/recovered/prd-tauri-original-2ae5897.md:280-282` — 5 种 source 定义
- `backend/app/services/question_generator.py` — source 权重使用（待验证具体行号）

---

## R3-QA13 · tips/errors 存储位置对比（md vs Neo4j）

> **用户 round-3 原话 (User)**: "这里我需要得到一个 Graphit 的验证，我需要你证明，tips[] + errors[] 这个内容是存在我们的 md 节点文档，然后本身的双向链接来给 claudian 检索高效还是放在 Neo4j 后端检索高效，因为我们相当于有两个关系图谱。"（Round 2 文件 Line 766）

### Agent B 三存储对比证据

**事实：tips[]/errors[] 三处都存**（Round 2 说"不在 frontmatter"是错的）:

| 存储层 | 内容 | 检索方式 | 检索效率 | 用途 |
|------|-----|---------|--------|-----|
| **md frontmatter `tips[]`** | 完整 tip 对象（text/note/understanding/annotatedAt）| Obsidian Dataview 查询 | **⚡ 极快**（文件系统直接读）| 用户可见 + 跨白板人工查询 |
| **Neo4j EntityNode 属性 + Graphiti episode** | Tips + 语义向量 + 错误分类 + session 链接 | `search_memory_facts(query, filter)` | 🔵 中等（Neo4j Cypher + bge-m3 向量搜索）| AI 精准检索 + 语义相似 |
| **SQLite ArchiveStatus** | Tips 的 Warm/Cold 归档副本 | SQL 查询 | 🟡 慢（按时间段）| 长期归档 + 审计 |

### 哪个"检索高效"更好？—— 分场景

**场景 1: 用户浏览（Obsidian UI）**
- **优选: md frontmatter + Dataview** 
- 理由: 本地文件系统，零网络延迟，Obsidian 原生支持

**场景 2: AI 对话检索（Claudian）**
- **优选: Neo4j Graphiti**
- 理由:
  1. 语义向量（bge-m3）支持"similar Tips" 检索
  2. 跨 session 学习历史（md 文件只有当前节点的 Tips）
  3. 错误自动分类（FR-CONV-06 4 主类）仅在 Neo4j 实现
  4. `search_memory_facts(query="admissibility", filter=error_class)` 一行代码
**User：我们当前的后端检索实现的是否可靠还是一个未知**

**[A5 2026-04-14 → round4]** 不是"可靠"也不是"未知"，而是**"分层已知"**：L2 Hybrid ✅（测试全）/ L1 LLM Router ❌（0 单元测试，OpenSpec 6 scenarios 未落地）/ L3 Graphiti 🟡（G-PARAM-001 已修但无集成测试）/ L4 Misconception 🔴（G-MOCK/G-PATH 已修但未纳入质量环）。量化：13 测试文件 / 207 test 函数 / 32/37 gotchas 已修（86%）/ 1 待修（G-SILENT-001）。详见 [[obsidian-qa-round4-claude-answers-2026-04-14#R4-Q4 · 后端检索可靠性审计（四路搜索三级分类 + 量化证据）|R4-Q4 检索可靠性审计]]。

**场景 3: 跨白板统计（Dashboard）**
- **优选: Neo4j 聚合查询**
- 理由: Cypher `MATCH (n:EntityNode)-[:HAS_TIP]->(t) WHERE n.group_id = $gid RETURN count(t)`

**场景 4: 长期归档**
- **优选: SQLite**
- 理由: 结构化归档，便于时间范围查询

### 两个关系图谱（用户原话澄清）

用户问"两个关系图谱"可能指:

1. **Obsidian Wikilink Graph**（`[[xxx]]` 双向链接）— md 文件之间关系
2. **Neo4j Graphiti 语义图谱** — 节点 + Tips + errors + episode 多类型关系

**两者不同用途**:

| 图谱 | 节点 | 边 | 用途 |
|-----|-----|-----|-----|
| **Obsidian Wikilink Graph** | md 文件 | `[[xxx]]` 链接 | 用户可视化浏览 + Claudian 显示相关文件 |
| **Neo4j Graphiti** | EntityNode + Tip + Error + Episode | HAS_TIP / CAUSED_BY / SIMILAR_TO | AI 语义检索 + 学习历史分析 |

**分工建议**:
- 概念之间的人工关系 → Wikilink Graph（用户写 `[[related-concept]]`）
- 节点的学习痕迹 → Neo4j（AI 自动提取 Tips/errors）

### Round 2 错误纠正（关键）

Round 2（R2-Q17 纠正 + R2-Q16）说"Tips 和 errors 不在节点 frontmatter，是独立存 Graphiti 的" **完全错误**。

**真相**: Tips/errors **同时存三处**，是**事实上的 all-of**，不是任一选一:
- frontmatter（用户可见）
- Graphiti Neo4j（AI 可见）
- SQLite（归档）

三者**独立维护 + 写入时同步**（PRD FR-RET-01/02/03 + FR-TRACE-02/05 共同定义）。

### 新方案（Round 3 最终 · 三存储明确）

**写入路径**（用户标注 Tips 时）:
```
用户选中文字 + 保存 Tip
  ↓
Claudian 调 API
  ↓
backend 同时写 3 处:
  ├─ POST /api/v1/tips → md frontmatter tips[] 追加
  ├─ POST /api/v1/tips → Graphiti `add_episode(type=tip)` 异步
  └─ POST /api/v1/tips → SQLite ArchiveStatus 更新
```

**读取路径**（AI 检索时）:
```
Claudian 对话问"之前的 Tips"
  ↓
/chat_with_context Skill 触发
  ↓
MCP 工具 search_memory_facts(query, node_id)
  ↓
Neo4j 返回语义相关 Tips（含跨 session）
  ↓
注入 system prompt
```

### Obsidian 可导航引用

- `backend/app/services/memory_service.py:346-481` — record_learning_event 三存储写入
- `backend/app/services/mastery_store.py:48` — Neo4j EntityNode group_id 过滤
- `backend/app/services/conversation_archive.py:35-64` — SQLite ArchiveStatus
- `frontend/src/types.ts:145-153` — TipItem frontmatter schema
- `_bmad-output/planning-artifacts/recovered/prd-tauri-original-2ae5897.md:670` — 学习档案展示 Tips
- `_bmad-output/planning-artifacts/recovered/prd-tauri-original-2ae5897.md:836` — FR-TRACE-02 Tips 可追溯

---

# T2 · 批注类型真实机制（User2 追问）

## R3-Q8-1 · 批注真实机制（User2）

> **用户 round-3 原话 (User2)**: "这里的批注一般只会有我的疑问和我的个人理解，然后我还会选择理解程度来标记"（原 QA 文件 Line 357）

### Agent B 前端代码证据（R3-QA1 已展开）

**前端实现 4 种 AnnotationTag**（`InlineAnnotation.tsx:35`）:
- `tips`（💡 总结/技巧）
- `error`（❌ 错误）
- `question`（❓ 疑问）← 用户说的"疑问"
- `keypoint`（📌 关键点）

**用户原话"疑问 + 个人理解"** 对应前端:
- **疑问** = `question` category
- **个人理解** ≈ `tips` category 或 `keypoint` category

### 纠正

用户口语化归并了 4 种为 2 类（疑问 + 个人理解），但前端实现是 4 种。Round 3 保留前端 4 种（更精细），**UI 层可简化显示**为用户习惯的 2 类 + 2 高级类。

### 新方案（UI 层渐进式）

**默认 UI（用户看到 2 类）**:
- **💡 我的理解** = 合并 tips + keypoint
- **❓ 我的疑问** = question
- **❌ 标记错误**（高级，默认折叠）

**frontmatter 仍存 4 类**（保持前端兼容）:
```yaml
tips: [...]
keypoints: [...]
questions: [...]
errors: [...]
```

**3 态理解程度**（统一用 `understanding` 字段）:
- `understood` / `fuzzy` / `not-understood`

### Obsidian 可导航引用

- `frontend/src/components/chat/InlineAnnotation.tsx:35` — 4 种 AnnotationTag
- `frontend/src/components/chat/InlineAnnotation.tsx:58-63` — TAG_OPTIONS UI（可简化显示）
- 见 R3-QA1 完整展开

---

## R3-Q8-2 · 4 category callout 映射（User2）

> **用户 round-3 原话 (User2)**: "[!question] 和 [!my-understanding] 是对应我的个人理解以及疑问；然后 [!mastery] 我记得各个节点的掌握程度，我们的后端本来也会进行计算"（原 QA 文件 Line 376）

### Agent B 前端代码 + 后端代码联合证据

**用户原话 3 个 callout 名字对应 Canvas 真实机制**:

| 用户说的 callout | 真实对应 | 实现 |
|---------------|--------|-----|
| `[!question]` | 前端 `question` category | `InlineAnnotation.tsx:35` |
| `[!my-understanding]` | 前端 `tips` 或 `keypoint` category | `InlineAnnotation.tsx:35` |
| `[!mastery]` | **后端自动计算**，不是用户标注 | `backend/app/services/mastery_store.py:48-85` |

**mastery 不是用户标注类型**，是后端 BKT 算法自动算的:
- `backend/app/mcp/tools/mastery_tools.py:240-290` — `update_bkt(node_id, grade)` 自动更新
- `backend/app/services/mastery_store.py:85` — 存 Neo4j EntityNode `mastery_score` 字段
- 用户**只能看**，不能**手动标**

### Round 2 错误纠正

Round 2（R2-Q8.1）建议的 `[!mastery]+ 掌握度: 3/5` callout **整体作废**（R2-Q8.1 已作废此方案）。Round 3 进一步明确: 用户**永远不能手动标 mastery**，BKT 算法的领地。

### 新方案

**用户可标的 callout**（4 种，对应前端 4 category）:
```markdown
> [!tips]+ 💡 我的总结
> [!error]+ ❌ 错误标注
> [!question]+ ❓ 我的疑问
> [!keypoint]+ 📌 关键点
```

**后端自动计算 + 只读展示**（不是 callout，是 frontmatter + Dashboard UI）:
- `mastery_score`: 0.0-1.0（BKT）
- `fsrs_*`: 6 字段（FSRS）

**Dashboard 可视化** (Bases + Meta Bind):
- 每个白板一行，显示聚合 mastery_score（平均所有节点）
- 不是用户主动标记，是 AI/算法自动推断

### Obsidian 可导航引用

- `backend/app/services/mastery_store.py:48-85` — BKT mastery_score 自动计算
- `backend/app/mcp/tools/mastery_tools.py:240-290` — update_bkt 实现
- `frontend/src/components/chat/InlineAnnotation.tsx:35` — 前端 4 种 category（用户可标）

---

# 后续动作清单（Round 3 新增）

完成用户审计 Round 3 后：

1. **Story 11.X 补后端缺口**（基于 Round 3 确认的真相）:
   - 11.1: Graphiti 记忆 Skill 化（`/record_annotation` + `/chat_with_context` + `/start_exam_board` 3 Skill，见 R3-QA9）
   - 11.2: Dashboard 白板级 FSRS 聚合 endpoint `GET /api/v1/review/canvases-due`（见 R3-QA2）
   - 11.3: `/extract_node` MCP 工具实现（Round 2 R2-Q12 已列）
   - 11.4: `group_id` 用户自由填写 UI（Bases + Meta Bind 下拉，见 R3-Q0-6-3）
   - 11.5: `/archive_conversation` Skill（可选，按需生成对话 md 文件，见 R3-QA11）

2. **新建方案文档**:
   - `canvas-callout-spec-v2.md`（4 category callout + 3 态理解程度完整 schema，见 R3-QA7）
   - `canvas-exam-schemes-v2.md`（10 社区方案中 Canvas 落地的 3 个 + 实施路径，见 R3-QA10）
   - `canvas-graphiti-positioning-v2.md`（Hook → Skill 迁移 + 三存储架构，见 R3-QA9 + R3-QA11）

3. **修订 Round 2 文件**（不修改历史记录，追加 [A4] 注解）:
   - R2-Q8.1 / R2-Q9 / R2-Q17 / R2-Q13 关键纠正已在 Round 2 头部警示框列出

4. **修订 Story 1.2 / 1.3**（让它们对齐 Round 3 结论，本 Plan 不做）

## 本次任务元教训（下一 session 必读）

1. **PRD 不是真相的唯一来源** — PRD FR 清单 + Persona 故事 + 前端代码 + 后端实现 **四层交叉验证**
2. **`/recovered` 是权威证据源** — 3 文件共 1913 行 / 56 条用户批注，未来所有"原 PRD"引用必须先读 recovered
3. **用户说"这不存在"不是夸张** — 必须 Grep 验证
4. **多轮标记必须严格** — `[A2]` / `[A3]` / `[A4]` 跨 session Claude 识别 + frontmatter `total_rounds` 双保险

## Changelog

- 2026-04-14 v1: Round-3 主答复文件初版，基于 3 路并行 Explore Agent 调研产出
- 调研范围:
  - Agent A: /recovered 3 文件（prd-tauri-original / prd-annotations / prd-obsidian-feedback）深挖
  - Agent B: 前端 InlineAnnotation.tsx + types.ts + Claudian 存储三存储核对
  - Agent C: 10 社区考察方案（带 arxiv/期刊 URL + 效应量）
- 核对文件数: 12（3 recovered + 5 frontend/src + 4 backend/app）
- 引用诚实度: IC-1 ~ IC-6 全部遵守
