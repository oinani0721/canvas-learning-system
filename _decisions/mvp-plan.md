# MVP Plan: 14项刚需 × 代码真实状态 = 具体任务

> **Date**: 2026-03-24 | **Status**: DRAFT — 等待用户批注
> **依据**: docs/index.md (BMAD exhaustive scan) + memory/project_mvp_essentials.md (用户确认清单)
> **方法**: Boris Tane plan.md 模式 — 用户批注后再编码

---

## 状态说明

| 图标 | 含义 |
|------|------|
| ✅ | 已实现，可直接使用 |
| ⚠️ | 代码存在但需激活/接线/修复 |
| ⛔ | 缺失或被阻塞 |
| 🔗 | 需要验证管道打通 |

---

## MVP 14 项逐项分析

### #1 原白板前端设计 ✅

**现状**: 已实现。
- `frontend/src/App.tsx`: ReactFlow canvas，KnowledgeNode + ImageNode
- `canvas-store.ts`: boards/nodes/edges CRUD + Dexie persistence
- `NodeContextMenu`: 右键 7 操作（对话/profile/重命名/颜色/考试/关系/删除）
- `useBoardData.ts`: Dexie liveQuery 响应式数据

**剩余**: 无阻塞任务。可能需要 UI 打磨（Pencil 范式确认）。

<!-- 用户批注: -->
User： 颜色设计我们保留是用来干嘛的？颜色设计目前还会和我们的后端进行联动吗？ 然后现在的Canvas learning systeam 的UI 和 我们实际的编写UI差的很远，我不知道是不是后端功能不同步，因为我们的UI 到现在为止都还是浅色UI
User2:  #1 UI 浅色 + 颜色联动

  浅色 UI 问题：Pencil 设计了 Catppuccin Mocha 深色主题，但代码中 TailwindCSS v4 只在局部组件（NodeContextMenu、ToolCallCard）用了深色。全局主题没有切换。

  颜色联动：当前 NodeContextMenu 的颜色只改节点边框视觉。mastery-utils.ts 有精通度→颜色映射逻辑（new/learning/familiar/proficient/mastered →
  不同颜色），但没有自动应用到节点。设计意图是用户手动选颜色 OR 精通度自动着色 — 这两个路径需要你决定。

  你需要告诉我：颜色是用户手动控制（标记重要程度等），还是系统根据精通度自动着色？
(我觉得我们的颜色标记仅仅是用来个人标记颜色而已，我们很早就抛弃了颜色和后端联系在一起）

---

### #2 检验白板前端设计 ✅

**现状**: 已实现。
- `ExamCanvas`: 全屏考试视图（ReactFlow + ChatPanel sidebar + toolbar）
- `ExamModeSelector`: 3 种模式（点对点/综合/混合）+ AI 推荐
- `ExamSummary`: 考后统计（校准投票/精通度/分数/时间）
- `CognitiveLoadTimer`: 认知负荷计时 + 45min 休息提醒
- `HintButton`: 4 级渐进提示 + 精通度衰减
- `SkipButton`: 跳过 + 确认对话框
- `exam-store.ts`: 完整状态管理

**剩余**: 无阻塞任务。

<!-- 用户批注: -->
时间的功能是用来干嘛的？我记得我已经抛弃了记时的功能了吧。，考后统计 时怎么触发的，你和我解释一下，我要确保你是按照我的想法进行的。然后检验白板的设计我们还没有进行验证。然后还有我们的整一个Canvas Learning system 在前端Dashboard 上缺少了 管理后端各个LLM 和embedding 模型的api 以及我们本地运行的情况。这里我希望可以设计出前端和后端可以进行同步管理
User2：  考后统计触发流程：
  用户点击"完成考试" → exam-store.updateStatus('completed')
    → App.tsx 检测 examStatus === 'completed'
    → 渲染 ExamSummary 组件
    → ExamSummary 调用 POST /api/v1/exam/{id}/complete 保存记录
    → 显示：考察的节点数、发现的新节点、每个节点的精通度变化、总用时
（这里的这个触发流程我觉得是不符合我们的之前Graphiti 所定下来的决策的，我们现在是完全不考虑记时的，然后还有一个关于考察时的自评我记得也是统计我关于每个点的掌握情况，这一点我们之前也是决策过的，请你deep explore）
User3：  考后流程（决策确认版）

  考试中 AI 用 AutoSCORE 打分 (Stage1证据提取 → Stage2四维打分×3投票)
    → 考完：ExamSummary 面板
      → 显示：4维分数分解 + 精通度变化柱状图
      → 用户操作：对每题标记"偏高/偏低/准确"（校准投票）
      → 不显示计时
      → 精通度自动更新（FSRS+BKT）
      → 一句话通知掌握度变化

  答前自评按钮历史

  - 最初由 AI 推断添加 → 用户明确否决（打断对话式考试流程）
  - 改为考后在 ExamSummary 中通过"偏高/偏低/准确"间接收集校准数据
  - 自信度按钮组（Area9 2x2）仍 PENDING review

  代码现状 vs 决策

  ┌─────────────────────┬───────────┬────────────────────────────────┬────────┐
  │                     │   决策    │              代码              │  状态  │
  ├─────────────────────┼───────────┼────────────────────────────────┼────────┤
  │ AutoSCORE 4维×3投票 │ ✅ 确认   │ AutoScorer 已实现              │ ✅     │
  ├─────────────────────┼───────────┼────────────────────────────────┼────────┤
  │ 考后校准投票        │ ✅ 确认   │ ExamSummary calibration voting │ ✅     │
  ├─────────────────────┼───────────┼────────────────────────────────┼────────┤
  │ Calibration 存储    │ ✅ 确认   │ record_calibration 端点        │ ✅     │
  ├─────────────────────┼───────────┼────────────────────────────────┼────────┤
  │ CognitiveLoadTimer  │ ⛔ 抛弃   │ 代码存在                       │ 需移除 │
  ├─────────────────────┼───────────┼────────────────────────────────┼────────┤
  │ 总用时显示          │ ⛔ 不需要 │ ExamSummary 显示               │ 需移除 │
  ├─────────────────────┼───────────┼────────────────────────────────┼────────┤
  │ 自信度按钮组        │ PENDING   │ 不存在                         │ 暂不做 │
  └─────────────────────┴───────────┴────────────────────────────────┴────────┘
（这里除了自评以外，我记得使用检验白板考察的时候，我们还涉及的点是，你出题后我记得有跳过等选项给我选择的）
---

### #3 检验白板考察提示词 🔗

**现状**: 后端已实现，需验证前后端打通。
- Backend `agents.py`: decompose_basic/deep, score_answer, explain_*, verification_question
- Backend `AgentService` (5155行): LLM 调用逻辑
- MCP tools: `generate_question`, `score_answer` (pipeline_token 串联)
- Backend `QuestionGenerator` (785行), `AutoScorer` (444行)

**需验证**:
1. ExamCanvas → ChatPanel → sidecar → MCP generate_question → backend → 返回题目 管道是否打通
2. 3 种考察模式提示词是否覆盖用户需求（点对点突破/混淆融合/举一反三）

**任务**: 启动产品 → 创建考试 → 实际触发出题 → 验证返回

<!-- 用户批注: -->
题目的质量也是有待我去检验
---

### #4 节点 AI 对话 ⚠️

**现状**: 代码已实现，但 Agent SDK sidecar 未在 Windows 验证。
- `claude-engine.ts`: Singleton sidecar 管理器（spawn Node.js 进程）
- `sidecar/sidecar.js` (468行): Agent SDK wrapper，NDJSON IPC
- `engine-fallback.ts`: Claude Code CLI → API Key 降级
- `crash-recovery.ts`: 断路器（3 次 crash / 5min）
- `ChatPanel`: 流式对话 + tool call 4 态 + 权限请求

**阻塞**: Agent SDK sidecar Windows spawn 稳定性未验证（Decision-Review PENDING）。

**任务**:
1. ⛔ 验证 `npm run tauri dev` → sidecar spawn → 对话可用
2. 如 spawn 失败 → engine-fallback 降级到 API Key 模式是否工作

<!-- 用户批注: -->
降级到API key ；你是打算使用 CIL proxy吗？
---

### #5 Tips/Edge/错误/提问 写入+检索 🔗

**现状**: 后端+前端代码都存在，需验证端到端。
- Frontend: `InlineAnnotation` (文本选择→浮动工具栏→4 类标注: tip/error/question/keypoint)
- Frontend: `TipsList` (显示保存的 tips，localStorage + backend merge)
- Backend: `memory/episodes` 端点（创建/查询学习事件）
- Backend: `ConversationDistiller` (对话蒸馏为 tips/errors/QA)
- Backend: MCP `record_learning_memory`, `record_error`
- Backend: `MemoryService` (Neo4j + JSON dual-write)

**需验证**:
1. InlineAnnotation → POST /api/v1/tips/ → 持久化 → 刷新后可见
2. sidecar record_learning_memory MCP tool → MemoryService → Neo4j 写入
3. 检索路径：search_memories → 能返回之前写入的 tips/errors

**任务**: 端到端测试写入+检索链路

<!-- 用户批注: -->
 record_learning_memory 我记得完全没有按照我们的Graphiti来进行设计，graphit 本身设计的add memory 和search memory 也没有进行调用，然后关于我们的记忆强制写入也没有做到，关于我们提到的hook 设计 还有关于一部分的强制的兜底机制我们也没有考虑吧
---

### #6 检验白板新发现写入 🔗

**现状**: MCP tool 存在。
- MCP `create_exam_node`: 在考试中发现新概念 → 创建节点到画布
- Frontend: ExamCanvas 支持节点操作

**需验证**: 考试中 → AI 发现新概念 → 调用 create_exam_node → 节点出现在画布上

<!-- 用户批注: -->
这个功能我还没有验证，这个拉出节点的机制应该是要和我们的使用原白板时从对话中拉出节点时一样的。

---

### #7 Dashboard ⚠️

**现状**: 基础框架存在，功能可能不完整。
- Frontend: App.tsx `view === 'dashboard'` 视图
- Frontend: `ReviewItem` (复习节点卡片), `ExamCard` (考试卡片)
- Backend: review/schedule, review/history, exam/records 端点

**需验证**:
1. Dashboard 是否显示白板列表（canvas_boards from Dexie）
2. 是否显示检验白板列表（exam sessions）
3. 3 个操作按钮（创建/打开/考试）是否存在

**任务**: 启动产品 → Dashboard → 确认 UI 完整度 → 可能需 Pencil 设计补充

<!-- 用户批注: -->
还有一点关于节点的 3层 profile ，就是说可以在白板上查看node，然后点击node，能看到这个node 的考察记录错误历史，以及这个tips 以及其他点，我在通过使用过检验白板考察后我能知道我的这些点的掌握情况，而且本身我在使用检验白板考察的过程中，也会暴露我的新的疑问，这些新的疑问本身也会进行记录，然后也作为一个新的点，我再下次使用检验白板的时候可以被考察到这一点，然后还有一点我希望我可以点击我的疑惑来进行跳转，让我也能看到当时我解答疑惑探究的过程，那么这个时候就是涉及了我点击相关错误可以选择到相关的白板来进行跳转了。
User2：  你描述的是一个完整的学习闭环：

  Node A (微积分-极限)
    → 点击查看 Profile：考察记录 / 错误历史 / Tips / 精通度
    → 考察中暴露新疑问 → 自动记录为新节点
    → 新疑问节点下次考试时可被考察
    → 点击错误/疑惑 → 跳转到当时的对话/考试白板

  当前代码状态：
  - LearningProfile 组件已有：精通度指标、tips、弱点、QA highlights、FSRS 复习日期
  - 缺失：
    a. 考察记录列表（哪次考试考过这个节点、得分多少）— 需要从 exam records 聚合
    b. 错误历史（按时间排列的错误列表）— 需要从 Neo4j :Misconception 节点查询
    c. 疑惑→新节点自动创建 — 需要 sidecar 在考试对话中识别"新疑问"并调用 create_exam_node
    d. 点击跳转到对话/白板 — 需要记录每条错误/疑惑的 source_session_id + source_canvas_id，然后跳转
（这里新的疑问节点创建，我记得我们在Graphiti 决策过不是你自动创建的，而是我来手动决定，但是当你发现我有疑问进行记录的时候，是要明确归类到哪一个节点这是很重要的）
---

### #8 Edge 对话 2重策略 ✅

**现状**: 已实现。
- Frontend: `chat-store.ts` 有 `switchToEdge`/`exitEdgeMode` + `EdgeContext`
- Frontend: `EdgeGuideTooltip` 首次使用引导
- Backend: `/api/v1/edges/rationale` 记录 edge 对话理由
- Backend: `/api/v1/inheritance/distill` edge-based 对话蒸馏
- Backend: `ConversationDistiller` 处理 edge 对话

**剩余**: 验证 2 重策略（EI + SE）的提示词是否正确实现。

<!-- 用户批注: -->
edge-based 对话蒸馏 你这里的对话蒸馏打算是怎么设计的，
User2：    → LLM 提取 4 类信息：
      1. Tips（学习窍门）
      2. Errors（错误/误解）
      3. QA Highlights（关键问答）
      4. Guided Thinking（引导思路）
（你这里的对话蒸馏到底是edge 蒸馏还是节点的上下文蒸馏，这一点你要确立清楚）
---

### #9 Agentic RAG L1+L2 ✅

**现状**: 已实现，是代码库最成熟的模块。
- `src/agentic_rag/` (19,220行): 完整 LangGraph StateGraph
- 6 路并行检索: graphiti + lancedb + multimodal + textbook + cross_canvas + vault_notes
- Fusion (layered_rrf) → Rerank (gte-reranker) → Quality check (CRAG) → Compress → Faithfulness
- Backend: `rag_service.py` wraps StateGraph
- Phase 3 agent_graph: LLM-controlled Adaptive+Corrective RAG

**剩余**: 确认 Docker 环境中 Ollama bge-m3 模型已拉取且 RAG 查询可用。

<!-- 用户批注: -->
我们的这个RAG 还是不能正常使用，而且我的前端还有一个设计由于我的不同白板对应的是不同的学科所以我要给我的白板选择索引笔记的路径，所以我觉得不同的白板会有不同的索引情况
---

### #10 笔记精准检索返回 ⚠️

**现状**: 基础设施存在，但数据流入未确认。
- Backend: `/api/v1/canvas-meta/index/vault` 索引全部 .md 文件
- Backend: `/api/v1/canvas-meta/index/vault/incremental` 增量索引
- Backend: `LanceDBIndexService` 自动索引 + 500ms debounce
- LanceDB: `vault_notes` 集合存储 .md 文件 embeddings
- MCP: `search_notes` 6 源 RAG 管道搜索
- Frontend: `obsidian-link.ts` 跳转 Obsidian (3 级降级)

**⛔ 关键问题**:
1. vault .md 文件是否已被索引到 LanceDB？需要手动触发 index/vault
2. bge-m3 embedding 需要 Ollama 运行
3. 用户提到的"精确笔记片段返回+跳转链接"需要验证

**任务**:
1. 确认 CANVAS_BASE_PATH 指向正确的 vault 路径
2. 调用 POST /api/v1/canvas-meta/index/vault 触发索引
3. 验证 search_notes → 返回精确片段 → obsidian-link 跳转

<!-- 用户批注: -->
目前使用的时候说是索引成功但是实际上什么笔记片段都没有返回，我完全没有看到agent 回复的时候有很好的进行表述
---

### #11 基础 Hybrid Search ✅

**现状**: 已实现。
- LanceDB with bge-m3: dense (1024d) + sparse (BM25-like) 混合搜索
- `src/agentic_rag/clients/lancedb_client.py`: hybrid_search()
- Reranker: gte-reranker-modernbert-base

**剩余**: 无阻塞。

<!-- 用户批注: -->
你这里是指agent 在回复的时候，先去查看一下相关笔记吗？
---

### #12 Claude Code 迁移 ⚠️

**现状**: 架构已实现，Windows 验证待完成。
- `claude-engine.ts`: Tauri Shell spawn Node.js sidecar
- `sidecar/sidecar.js`: @anthropic-ai/claude-agent-sdk 0.2.74
- 15 MCP tools 暴露给 sidecar（pipeline_token 串联）
- PreToolUse 选择性权限 hook（record_learning_memory, record_error 需批准）

**⛔ 阻塞**: 同 #4 — Windows spawn 稳定性未验证。

**任务**: 与 #4 合并验证。

<!-- 用户批注: -->

---

### #13 /命令调用提示词模板 ✅

**现状**: 已实现。
- Backend: `SkillRegistry` (331行) + `/api/v1/skills/` 端点
- Frontend: `SkillSelector` 组件（'/' 触发浮动选择器 + 键盘导航）
- 支持: decompose, score, explain (6种), verification_question, question_decompose, recommend_action

**剩余**: 无阻塞。

<!-- 用户批注: -->
现在并没有实现完全的迁移 claude code 的所有的命令
---

### #14 对话拉出节点 ✅

**现状**: 已实现。
- `usePullToNode` hook: 选中文本 → 创建 KnowledgeNode → 定位源节点右侧 300px → 自动创建 edge
- 写入 ReactFlow + Dexie + sync_outbox

**剩余**: 无阻塞。

<!-- 用户批注: -->

---

## 底层系统

### 笔记片段精准检索系统 ⚠️

**现状**: 架构完整，需激活数据流入。
- LanceDB vault_notes 集合 ✅
- bge-m3 embedding 模型 ✅ (需 Ollama 运行)
- 索引端点 ✅ (index/vault + incremental)
- 6 源 RAG 搜索 ✅
- **缺失**: vault 数据可能未实际索引（需手动触发）

### Agent 记忆系统 ⛔ 阻塞

**现状**: MemoryService 使用 JSON fallback + Neo4j Cypher，NOT 真正的 Graphiti。
- 42 处假命名（12C+13H）— 函数名说 "graphiti" 实际是 Neo4j/JSON
- graphiti-core 零调用
- 6Phase 迁移计划已就绪（_decisions/migration-plan-graphiti-real-integration.md）
- **⛔ 被 Gemini 免费额度阻塞**（10RPM/250RPD 不够）
User：请你查看我们当前claude code 的 graphiti 的 Gemini 的api ，你直接照搬就好。
---

## 优先级排序

### P0 — 立即可做（无阻塞）

| 任务 | 预估 | 说明 |
|------|------|------|
| 启动产品验证 #1/#2/#7 | 1h | `npm run tauri dev` → 验证画布+考试+Dashboard UI |
| 验证 #4/#12 sidecar | 2h | Windows spawn → 对话 → 降级测试 |
| 验证 #3 考察提示词 | 1h | 创建考试 → 出题 → 验证 3 模式 |
| 验证 #5 写入+检索 | 1h | InlineAnnotation → tips 写入 → 检索返回 |
| 激活 #10 笔记索引 | 1h | 配置 vault 路径 → 触发索引 → 搜索验证 |

### P1 — 需修复后可用

| 任务 | 预估 | 说明 |
|------|------|------|
| Dashboard UI 补全 #7 | 2-4h | Pencil 设计 → 确认 → 实现缺失部分 |
| 验证 Edge 2重策略 #8 | 1h | 确认 EI+SE 提示词 |

### P2 — 被阻塞

| 任务 | 阻塞项 | 预估 |
|------|--------|------|
| Agent 记忆系统 | Gemini 额度决定 | 9-13h (6Phase) |

---

## 执行建议

**下个 Session** 按 P0 顺序执行：
1. 先 `docker compose up -d` + `npm run tauri dev` 启动产品
2. 逐项验证 #1→#2→#7→#4→#3→#5→#10
3. 每项验证结果记录到此文件
4. 发现问题 → 直接修复（<50行直接 commit，不走完整审查）

<!-- 用户批注区 ———————————————————————————
Q1: P0 验证顺序你同意吗？还是想调整优先级？ User： 我对优先级觉得没有什么问题。
Q2: Gemini 额度问题：付费升级？换 Provider？还是先跳过 Agent 记忆，做完其他 13 项？User：这里直接使用
Q3: 还有什么需要补充的？ User：我们知道每个node 都是有单独的对话历史和记忆，然后有一点十分关键的是，你告诉我Canvas learning systeam 既有 claude code 的session 记忆，又有我们的node 的对话历史，那么前端界面我是怎么进行管理的？这一点你有没有进行思考 ；
 User 2：当你从 Node A 切到 Node B，sidecar session 的 context 怎么处理？当前设计是 per-node session（sidecar.js 有 sessionMap），但跨 node
  的知识是否应该共享——这正是 Agent 记忆系统要解决的问题  （关于你这里的说法我没有理解，我的理解是我们使用的claude SDK 本身就是有seesion 的对话历史，然后我们自己又设计了节点的对话历史，按照我的理解的话，这两个历史是一样的，seesion 的上下文有上限，但是节点的上下文没有，所以这里又要考虑到上下文压缩的问题吗？请你查看一下 claudian 是怎么做的） 
User 3前端管理方式：chat-store.ts 的 switchNode(nodeId) 切换节点时加载该节点的历史。但 Claude Code 的 session 上下文（system prompt 中注入的记忆）是通过
  ContextEnrichmentService 在每次对话开始时组装的，不是持久化的 session。

  坦率说：这两个记忆层的交互设计确实不够清晰。用户在节点 A 的对话中暴露的错误，应该在节点 B 的考试中被检索到 — 这依赖 Agent 记忆系统（Graphiti），而 Graphiti
  目前是假的。 （我对你的这个claude code session 的上下文 管理还是不太理解是什么意思，这和我们的claude code CIL 的上下文管理有什么区别；然后还有一点就是 User 2 提到的上下文压缩你完全没有想到）User4：  用户切到 Node B → sidecar 创建 Session-B（新的 Claude SDK 对话）
    ↳ Session-A 的 context 保留在 sessionMap 中（内存）
    ↳ 切回 Node A 时复用 Session-A（如进程没重启）（这里关于保存到内存里进行切换是成熟的做法吗？然后还有一个关键点是我的建议是claudian 注册了什么claude code命令，那么我们就注册什么命令到我们的对话框上，然后还有一点，关于/resume 启动session 如果不进行命名的话，我们是很难找到相关的seesion，然后还有一点，我们的前端对话窗口会呈现上下文压缩吗？还是说呈现完整的对话历史，然后还有一点，现在claude cdoe opus 是支持 1M 上下文窗口了）
————————————————————————————————————————— -->
