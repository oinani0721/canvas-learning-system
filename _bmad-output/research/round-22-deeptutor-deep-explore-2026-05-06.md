# Round-22 DeepTutor 深度探索报告（10 Agent 并行调研）

> **Plan ID**: EPIC1-BMAD-DEV-ASSESS-2026-04-17（Round-22 DeepTutor Fork MVP）
> **执行时间**: 2026-05-06
> **延展自**: `_bmad-output/research/round-22-deeptutor-fork-mvp-2026-05-06.md`
> **数据来源**: `~/Desktop/canvas/deeptutor-fork/`（v1.3.7，commit 9389178）

---

## 摘要

用户在 Day 1 wikilink 集成验收后提出**两个根本性问题**：

> Q1: DeepTutor 是不是已经有"知识图谱式"功能？我做 wikilink 双链是不是重复劳动？
> Q2: DeepTutor 原生功能能否渲染图谱或可阅读式书籍，把"原白板作为 index 呈现各节点关系"的交互逻辑直接呈现？

为客观回答，启动**两轮各 5 个并行 Explore agent** 共 10 个深度调研：
- **第一轮（数据层）**：knowledge_base / notebook / memory / book / 学习追踪 / 思维模型
- **第二轮（渲染交互层）**：CONCEPT_GRAPH 渲染 / Book 阅读 UX / 14 块对照 / 外部注入 API / 原白板承载

**结论**：Canvas 5 大核心 → DeepTutor 集成是 **100% 必要、0 冗余**。但路线图需重大调整：发现 2 条降本路径（confirm-spine API 绕过 AI + Cytoscape 已装未用）+ 1 个范式承载缺口（白板即主入口）。10 天 MVP 可行但 Day 5+ 重排。

---

## 第一部分：数据层调研（5 agents）

### 1.1 Knowledge Base RAG（Agent 1.1）

**调研目的**：确认 DeepTutor RAG 是纯向量还是图增强。

**关键发现**：
- 后端：LlamaIndex VectorStoreIndex（纯余弦相似度 Top-K）
- 文档间关系建模：**完全缺失**（grep `class.*Edge|class.*Link|class.*Relation` 零结果）
- `graph_store.json` 是 LlamaIndex 默认产物，**从未被读取或使用**
- 反向索引：**零**（无法回答"哪些文档引用了 X"）
- SmartRetriever 是多查询并行检索，仍是纯向量

**关键代码位置**：
- `/deeptutor/services/rag/pipelines/llamaindex/storage.py:165-170` — `retrieve_nodes()` 纯向量
- `/deeptutor/services/rag/pipelines/llamaindex/pipeline.py:198-222` — `_nodes_to_result()` 无关联字段
- `/deeptutor/services/rag/pipelines/llamaindex/document_loader.py:55-65` — 文档加载无关系提取

**判断**：跨文档关系感知 ✗✗✗ 完全缺失。Canvas wikilink + NetworkX 是**补全**，不是重复。

---

### 1.2 Notebook + Memory 子系统（Agent 1.2）

**调研目的**：确认 DeepTutor 的"记录 + 记忆"是不是有显式关联建模。

**关键发现**：

**Notebook 数据模型**（`data/user/workspace/notebook/{id}.json`）：
```
Notebook
├── id, name, description, color, icon
└── records: [
    {id, type, title, summary, user_query, output, kb_name, created_at}
]
```
- **扁平化设计**：records 是原子单位，无 cell 概念
- **无概念标签 / 主题字段** → grep `Concept|Topic|Tag` 全无

**Memory 系统**（`data/user/memory/`）：
- `SUMMARY.md` + `PROFILE.md` 双 markdown
- **覆盖式更新**（每次完整重写，无版本历史）
- 由 LLM 维护一致性（prompt 约束 section 结构）

**Notebook ↔ Memory 关联**：
- 完全独立、单向流动
- chat 引用 notebook 是 chip selector + list filter（不是 RAG，不是图遍历）
- Memory 不感知 notebook 选择

**判断**：DeepTutor 是"记录库 + 用户状态跟踪"，**不是知识图**。Canvas Graphiti episodic memory（事件时间线 + 因果链）是**关键补全**。

---

### 1.3 Book + CONCEPT_GRAPH Multi-agent Pipeline（Agent 1.3）

**调研目的**：CONCEPT_GRAPH block 是真图谱还是可视化糖衣？

**重大发现**：CONCEPT_GRAPH **是真正的有向无环图（DAG）**！

**ConceptGraph schema**（`deeptutor/book/models.py`）：
```python
class ConceptNode:
  id: str           # slug "fourier_basis"
  label: str        # human-readable
  chapter_id: str   # 绑定 chapter
  description: str
  weight: float     # 中心度

class ConceptEdge:
  src, dst: str
  relation: str     # 'depends_on' | 'extends' | 'related'
  rationale: str    # 推理依据

class ConceptGraph:
  nodes, edges
```

**生成流程**：
- `SpineSynthesizer` agent 多轮 Draft → Critique → Revise（max_rounds=2）
- 后处理：拓扑排序、循环移除、Jaccard 相似度覆盖填充

**关键限制**：
- 图是 **AI 生成的**，无用户编辑入口（no manual graph construction UI）
- 绑定 **chapter 维度**（不是文档维度）
- 仅在 book 内有意义，跨 book **不可复用**
- 持久化在 spine JSON，**不是图数据库**（无遍历查询）

**Book 数据模型**：
- Book → Spine（chapters + concept_graph）→ Pages（ordered blocks）→ Blocks
- Block 间关联：**线性 list**（无 next/prev 显式指针，array index 即顺序）
- Page 间关联：`PageLink` 模型支持 deepens/prereq/references 关系

**判断**：CONCEPT_GRAPH 数据结构强大但**用户主权被剥夺**。Canvas wikilink（用户写 `[[xxx]]`）填补"用户亲手定义关系"空白。

---

### 1.4 学习追踪机制（Agent 1.4）

**调研目的**：DeepTutor 是否有 mastery / FSRS / 错误归因？

**关键发现**：DeepTutor **完全缺失**学习追踪：

**`notebook_entries` 表**（`sqlite_store.py`）：
```sql
CREATE TABLE notebook_entries (
  id, session_id, question_id, question, ...
  is_correct  -- 仅 0/1 二值
  -- 无 mastery, stability, difficulty, retrievability
  -- 无 error_type, mistake_category
  -- 无 next_review, last_review_grade
)
```

**对比 Canvas 设计**：

| 维度 | DeepTutor | Canvas | 缺口 |
|---|---|---|---|
| 掌握度 | `is_correct` 二值 | BKT P(L)/P(G)/P(S) | DeepTutor 完全缺失 |
| 间隔重复 | 无 | FSRS difficulty/stability/retrievability | DeepTutor 完全缺失 |
| 问题-概念 | `concentration` 字符串无持久化 | node_id + pipeline_token + 5 层 ACP | DeepTutor 弱关联 |
| 错误归因 | 无 | 4 类 ErrorCandidate (misconception/careless/computational/slip) | DeepTutor 完全缺失 |
| 复习排程 | 无 | `/review/due` Day 0/3/7 | DeepTutor 完全缺失 |

**意外发现**：`exam_proxy.py` 框架（staging cp 进 fork）已预留 `update_bkt/update_fsrs/search_memories` 接口——**DeepTutor 设计者自留 Canvas 集成 hook**。

**判断**：DeepTutor 是"答题 + 讲解"系统，不是"学习追踪"。Canvas BKT/FSRS/AutoSCORE/ErrorCandidate 全部是**激活已留接口**而非新增能力。

---

### 1.5 Canvas vs DeepTutor 思维模型差异（Agent 1.5）

**用户主权差异**：

| 维度 | Canvas | DeepTutor |
|---|---|---|
| 存储单元 | md 文件（用户拥有） | Book JSON（系统目录） |
| 用户主动权 | 写笔记 + 标 wikilink + 加 callout | 提主题，AI 生成 |
| 关系定义 | `[[concept]]` + `[!relation/type]` 用户亲手 | LLM 推断 ConceptEdge.relation |
| 数据所有权 | 用户 owns（删 vault 笔记消失） | 用户 rents（删 fork 全丢） |
| 跨 session 复用 | 永久（图持续累积） | 每个 book 独立从零推断 |

**核心例子（Agent 5 第 6 节）**：
- 用户想说"递归是数学归纳法的特例"
- **Canvas**：编辑 Recursion.md 写 `[[Mathematical_Induction]]` + `[!relation/specialization]` → 一次定义、永久持续、跨笔记复用
- **DeepTutor**：每次新 book 都让 AI 从零推断（可能对可能错），book A 的关系 book B 不知道

**判断**：Canvas 是"用户主导的知识图"，DeepTutor 是"AI 自动生成的教科书"——**目标正交**。集成 wikilink 不是重复 DeepTutor 关系推断，是补全"用户显式标注"能力让知识从一次性推断升级为可复用网络。

---

## 第二部分：渲染交互层调研（5 agents）

### 2.1 CONCEPT_GRAPH 前端渲染（Agent 2.1）

**调研目的**：用户实际看到的图谱是静态还是可交互？

**关键发现**：

**渲染引擎**：Mermaid.js 11.14.0（**纯静态 SVG**）
- 流程：`payload.code.content` (Mermaid 源码) → MarkdownRenderer 包装 fenced block → mermaid.render() → SVG via `dangerouslySetInnerHTML`
- Mermaid 配置：theme="neutral", flowchart curve="basis"

**意外发现**：**Cytoscape v3.33.1 已装但完全未用**！
- `package.json` 含 cytoscape 依赖
- 整仓库无 cytoscape import / 无 `cy.on()` 事件
- 这是 fork 现成的"已支付红利"

**交互能力清单（grep 验证）**：

| 能力 | 状态 | 备注 |
|---|---|---|
| 节点点击 | ❌ | grep `onClick\|onNodeClick` 零结果 |
| 节点拖拽 | ❌ | grep `drag` 零结果 |
| 缩放/平移 | ❌ | 仅浏览器原生 zoom |
| 搜索/过滤 | ❌ | 无 input UI |
| 高亮 | ❌ | 无 focus mode |
| 全屏 | ❌ | 无独立路由 |
| 边标签 | ❌ | relation 字段不渲染 |
| Chapter 索引点击 | ✅ | 右侧 sidebar 唯一可交互 |

**用户实际体验**：看图（静态 SVG）+ 点 chapter 标题跳页。**节点本身不可交互**。

**集成 Canvas 路径**：
- 选项 1：保留 Mermaid，把 Canvas vault 转 Mermaid 源码（最低成本，但 UX 不变）
- 选项 2：**替换为 Cytoscape**（已装），1-3 天工作量，节点全套交互能力激活

---

### 2.2 Book 阅读体验（Agent 2.2）

**调研目的**：Book 真的是"可阅读式书籍"吗？

**用户操作流程**：
1. 进入 `/book` → BookLibrary 列表 → 选 book → PageReader
2. PageReader 布局：
   - 左侧 BookSidebar（chapter 列表，可折叠）
   - 中间主内容（max-width: 78ch）— **单列连续滚动**，无翻页
   - 右侧 PageOutlineNav（block 级跳转，自动追踪当前位置）

**Block 渲染特性**：
- 每个 block 顶部 `scroll-mt-6` 跳转锚点
- Block 间 `bridge_text` markdown 缝合（"过渡词"）
- Quiz inline 答题 + 即时反馈
- FlashCards 翻卡 + prev/next/flip
- DeepDive 按钮 → 触发后端生成 sub-page

**关键限制**：
- ❌ **无 prev/next 按钮**（必须回 sidebar 切换）
- ❌ **无阅读进度记录**（关浏览器丢位置）
- ❌ **Overview chapter 强制首页**（破坏阅读节奏）
- ❌ **Mermaid 静态**（不可点）
- ❌ **无节点级笔记**（只有 page 级 user_note）

**最接近"可阅读书籍"对比**：

| 入口 | 流式 | Markdown | 交互 | 视觉连贯 |
|---|---|---|---|---|
| Book | ✅ 单列流 | ✅ 14+ 块类型 | ✅ Quiz/FlashCards/DeepDive | ⚠️ bridge_text 缝合 |
| Co-Writer | ✅ 编辑/预览 | ✅ 纯 Markdown | ❌ 仅编辑 | ⚠️ 无过渡 |
| Notebook | ❌ 卡片列表 | ⚠️ 题目内 MD | ❌ 仅 Quiz 回顾 | ❌ 表格行 |

**改造工作量**（让 Book 承载 Canvas 白板交互）：
- ConceptGraphBlock 互动化（Mermaid → Cytoscape）：4 天
- 节点-Page 双向链接：3 天
- 阅读上下文持久化（localStorage + 后端）：2 天
- Sidebar/进度/面包屑增强：4 天
- **最小可用 7-8 天 / 完整体验 11-12 天**

---

### 2.3 14 BlockType 渲染对照（Agent 2.3）

**调研目的**：每个 block 真实 DOM 长什么样？哪些自动获得 wikilink 渲染？

**Day 1 wikilink 实际覆盖：9/14 blocks**

✅ **支持 wikilink**（调用 MarkdownRenderer）：
- TextBlock（content body）
- SectionBlock（intro + subsections）
- QuizBlock（question + correct_answer + explanation）
- UserNoteBlock（body）
- CodeBlock（fenced code 外文本）
- FigureBlock（figcaption）
- InteractiveBlock（description）
- AnimationBlock（summary）
- ConceptGraphBlock（mermaid 外文本）

❌ **不支持 wikilink**：
- **CalloutBlock** — `<div>{body}</div>` 纯文本（**1 行修复机会**）
- TimelineBlock — date/title/description 纯文本
- FlashCardsBlock — front/back/hint 纯文本
- DeepDiveBlock — topic/rationale 纯文本
- PlaceholderBlock — 占位符

**Block 三级分类**：

**纯静态展示（5 个）**：Text/Section/Callout/Timeline/Code
**互动展示（6 个）**：Quiz/FlashCards/DeepDive/Figure/Interactive/Animation
**可编辑（3 个）**：UserNote/ConceptGraph/Placeholder（**实际都不可编辑**——UserNote 仅展示无 contentEditable）

**CHANGEABLE_TYPES = 11/14**：除 user_note/concept_graph/placeholder 外可类型互转 → 这是 OriginWhiteboard 集成机会（用户可把 TextBlock 升级成白板视图）

**Day 5 BlockType Enum 扩展必要性**：

| Canvas 块 | DeepTutor 现状 | 必要性 |
|---|---|---|
| OriginWhiteboard | 无白板嵌入 | ⛔ 必加 |
| ExamWhiteboard | 无考试模式 | ⛔ 必加 |
| MasteryDashboard | 无学习曲线 | ⛔ 必加 |
| ErrorCandidate | 无错误归因 | ⛔ 必加 |
| EditableCalloutBlock | Callout 不走 MarkdownRenderer | 顺手 1 行修 |

---

### 2.4 外部数据注入 API（Agent 2.4）

**调研目的**：能否绕过 AI 直接注入 Book/ConceptGraph？

**重大发现**：**`POST /books/confirm-spine` API 接受完整 Spine payload**！

**API 清单**：

| API | 能注入 | 不能注入 | 工作量 |
|---|---|---|---|
| `POST /books` | user_intent + KB list | ❌ 直接 BookProposal | — |
| `POST /books/confirm-proposal` | ✅ 完整 BookProposal | ❌ 跳过 SpineSynthesizer | — |
| **`POST /books/confirm-spine`** | ✅ **完整 Spine + ConceptGraph** | ❌ — | **路径 B 核心** |
| `POST /books/compile-page` | params 字典 | ❌ 直接 block payload | — |
| `POST /books/insert-block` | block_type + params | ⚠️ 仍触发 LLM 编译 | — |
| `POST /knowledge/create` | files 上传 | — | 路径 A |
| `POST /skills/create` | prompt 模板 | ❌ 不影响 book 生成 | — |

**3 条 vault → DeepTutor 候选路径**：

**路径 A：Vault → KB Upload → AI 生成 Book**
- 流程：vault → markdown → POST /knowledge upload → POST /books（让 AI 生成）
- 工作量：~0 行代码（最低）
- 缺点：LLM 成本高 + AI 主导（不保留 vault 结构）
- 适用：快速验证 RAG

**路径 B：Vault → 直接 POST Spine Payload（推荐）**
- 流程：vault NetworkX 图 → 转 Spine JSON → POST /books → POST /books/confirm-spine（绕过 AI）
- 工作量：~300 行 Python（CanvasVaultAdapter）
- 优点：保留 vault 结构 + LLM 成本最低 + 用户主权 100%
- 适用：MVP 主路径

**路径 C：Vault → SpineSynthesizer Hint（混合）**
- 现状：API 不存在，需 fork 加 endpoint
- 工作量：~400 行新代码 + prompt 工程
- 不推荐：收益不足

**关键判断**：**路径 B 可行，无需 fork DeepTutor 内部代码**。CanvasVaultAdapter 作为外部转换层即可。

---

### 2.5 原白板模式 vs DeepTutor UX（Agent 2.5）

**调研目的**：Canvas 原白板交互能否在 DeepTutor 承载？

**Canvas 5 大核心交互路径**：
1. 白板引导入口（Dashboard → 选板 → Canvas 视图）
2. 从图探索到节点（Cmd+Click wikilink → 节点详情页）
3. ReactFlow 画布导航（点节点 → 侧栏对话/学习档案）
4. 右键关联探索（高亮所有连接边 + 关联节点列表）
5. 对话拉出新节点（usePullToNode hook）

**承载差距 5 大缺口**：

| Canvas 行为 | DeepTutor 现状 | 影响 |
|---|---|---|
| 白板即主入口 | 无白板列表首页 | 用户进来看不到知识图 |
| 以图浏览 + 点节点 | ConceptGraph 只读 Mermaid | 图只是装饰 |
| 节点双向 wikilink + 关联高亮 | Book Pages 无 wikilink | 概念孤立 |
| 边对话（关系讨论） | 无边的概念 | 无法讨论概念间关系 |
| AI 拉出节点 | 仅 Deep Dive 自动生成 | 用户决策权被剥夺 |

**3 个改造方案对比**：

| 方案 | 做法 | 工作量 | 与 10 天 MVP 契合 |
|---|---|---|---|
| **X 轻** | 复用 ConceptGraphBlock + 全屏路由 | 4-6 h | ✅ Day 5-6 可插入 |
| **Y 中（推荐）** | 新建 `/whiteboard` 路由 + ReactFlow + 后端 Neo4j | 18-24 h | ✅ Day 5-8 落地 |
| Z 重 | 重构 Space 主页为图谱入口 | 40-50 h | ❌ 超时不可行 |

**方案 Y 推荐理由**：
- 用户痛点（跨 book 概念关联）由独立 whiteboard 路由解决
- Day 5-8 时间表可控（20-26h < 48h 可用）
- Whiteboard 与 Book 解耦（不破坏现有功能）
- 复用 Canvas 已验证的 ReactFlow + Neo4j

**改造地图**（Day 5-8 任务分解）：

```
Day 5 上午（6h）— 后端
  POST /api/v1/whiteboard/         创建白板
  GET  /api/v1/whiteboard/:id/graph 返回 nodes + edges JSON
  POST /api/v1/whiteboard/:id/pull-node 拉节点逻辑

Day 5 下午 + Day 6（12h）— 前端
  /whiteboard route + WhiteboardCanvas 组件
  ReactFlow + ChatPanel sidebar
  NodeContextMenu 右键菜单（cp Canvas 逻辑）
  WorkspaceSidebar 加 "Whiteboard" tab
  usePullToNode hook（cp Canvas 改 endpoint）

Day 7-8（4-6h）— 集成
  端到端测试：建白板 → 加载图 → 选节点 → 对话 → 拉新节点
  Dexie sync 改造（whiteboard state 可能独立）
```

---

## 第三部分：整合判断

### 3.1 集成必要性结论（10 agent 收敛）

**Canvas 5 大核心 → DeepTutor 集成**：

| Canvas 核心 | DeepTutor 现状 | 集成必要性 |
|---|---|---|
| OriginWhiteboard + wikilink 双链 | AI 推断 + book 内孤立 + 跨 book 不复用 | ⛔ 必要补全 |
| MasteryDashboard (BKT + FSRS) | `is_correct` 二值，无掌握度建模 | ⛔ 必要补全（DeepTutor 自留 hook） |
| ExamWhiteboard + AutoSCORE | 无 4 维评分 | ⛔ 必要补全 |
| ErrorCandidate (4 类错误) | 无错误归因 | ⛔ 必要补全 |
| Graphiti episodic memory | 覆盖式 markdown 无版本 | ⛔ 必要补全 |
| **Whiteboard UI 入口** | 无以图为入口的浏览模式 | ⛔ **必要补全（Round-22 原报告漏项）** |

**结论：100% 必要、0 冗余**。

### 3.2 关键意外发现（路线图修订依据）

1. **Cytoscape v3.33.1 已装但未用**（Agent 2.1）— 节省 Day 5 升级图库时间
2. **`POST /books/confirm-spine` 直接注入 Spine**（Agent 2.4）— 路径 B 可行，绕过 AI
3. **CalloutBlock 不走 MarkdownRenderer**（Agent 2.3）— 1 行修复让 callout 内 wikilink 渲染
4. **DeepTutor 自留 Canvas 集成 hook**（Agent 1.4）— `services/canvas/client.py` 接口框架已存在
5. **CHANGEABLE_TYPES 11/14**（Agent 2.3）— OriginWhiteboard 可作为 TextBlock 的"升级形态"

### 3.3 修订后 10 天 MVP 路线图

| Day | 目标 | 核心动作 | 来源 Agent |
|---|---|---|---|
| Day 0 ✅ | 准备 | worktree + staging + 脚本 | — |
| Day 1 ✅ | wikilink 渲染端到端 | RichMarkdownRenderer + wikilink_proxy | — |
| Day 2 | 清理 + 数据布线 | (a) `client.py` neighbors path param 修<br>(b) **CalloutBlock 1 行修**<br>(c) Canvas vault 路径挂载到 fork | 2.3 |
| Day 3 | CanvasVaultAdapter 后端 | NetworkX → Spine JSON 转换器（300 行 Python） | 2.4 |
| Day 4 | 路径 B 端到端验证 | curl POST /books/confirm-spine 注入 vault 图 | 2.4 |
| Day 5 上午 | whiteboard 后端 3 endpoint | POST /whiteboard + GET graph + POST pull-node | 2.5 |
| Day 5 下午-Day 6 | whiteboard 前端 + ReactFlow | cp Canvas App.tsx + WorkspaceSidebar 加 tab | 2.5 |
| Day 7 | MasteryDashboard block | BlockType Enum +1 + 接 Canvas BKT/FSRS | 1.4 |
| Day 8 | ExamWhiteboard + ErrorCandidate | BlockType Enum +2 + AutoSCORE | 1.4 |
| Day 9 | UserNote 现场编辑 | UserNoteBlock contentEditable + 持久化 API | 2.3 |
| Day 10 | UAT + 收官 | 5 验证场景 + tag `mvp-complete` | — |

### 3.4 与 Round-22 原报告的差异

| 项 | 原计划 | 修订后 | 原因 |
|---|---|---|---|
| BlockType Enum 加 4 块 | Day 5 一次性 | Day 7-8 分批 + Day 9 加 UserNote 编辑 | Agent 2.2/2.3 工作量被低估 |
| Whiteboard 路由 | 无规划 | Day 5-6 核心新增（方案 Y） | Agent 2.5 发现"白板即入口"是不可妥协痛点 |
| confirm-spine 路径 | 假设 AI 主导生成 book | Day 3-4 路径 B（300 行 adapter） | Agent 2.4 关键 API 发现 |
| Cytoscape/ReactFlow | 无决策 | Day 5 ReactFlow（cp Canvas 代码最快） | Agent 2.1+2.5 |
| CalloutBlock wikilink | 未注意 | Day 2 顺手 1 行修 | Agent 2.3 |

### 3.5 待用户决策点（默认推荐已标注）

| 决策 | 选项 | 推荐 |
|---|---|---|
| **A. Day 5 图库选型** | (1) ReactFlow（cp Canvas 代码，需 npm install）<br>(2) Cytoscape（fork 已装，需重写交互） | **(1) ReactFlow** — 节省 50% 时间 |
| **B. Day 3-4 路径 B 范围** | (1) 仅 CanvasVaultAdapter 转 spine（最小）<br>(2) 加全 vault → multi-book batch import | **(1) 最小** — Day 5+ 还有大量工作 |
| **C. Day 9 UserNote 优先级** | (1) 现场编辑 + 持久化（高工作量）<br>(2) 跳过留 production 阶段 | **(1) 必做** — 不能编辑笔记的"白板"是矛盾设计 |

---

## 附录：Agent 调研产物索引

第一轮（数据层）输出文件：
- `tasks/af40b3f7d88353ec0.output` — Agent 1.1 knowledge_base RAG
- `tasks/a2127a461c3edd3d9.output` — Agent 1.2 notebook + memory
- `tasks/ab0ee73b149b4805f.output` — Agent 1.3 book + CONCEPT_GRAPH
- `tasks/a777578fda077a05e.output` — Agent 1.4 学习追踪
- `tasks/a1fb8f32ecd26a31a.output` — Agent 1.5 思维模型差异

第二轮（渲染交互层）输出文件：
- `tasks/a47ce8a9d893f5938.output` — Agent 2.1 CONCEPT_GRAPH 渲染
- `tasks/a9e34a18ef106afb2.output` — Agent 2.2 Book 阅读体验
- `tasks/ac2faf5501786bdef.output` — Agent 2.3 14 BlockType 渲染
- `tasks/a8f12ee6fa8d2ff3f.output` — Agent 2.4 外部数据注入 API
- `tasks/a4b5e833019eb69ee.output` — Agent 2.5 原白板 vs DeepTutor UX

---

**报告生成**: Claude Code (Opus 4.7 1M context)
**Plan ID**: EPIC1-BMAD-DEV-ASSESS-2026-04-17
**关联 commit**: `oinani0721/DeepTutor@23a2853`（Day 1 wikilink 集成）+ tag `mvp-day-1-patches`
