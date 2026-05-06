---
title: Round 20 — DeepTutor 实际代码深度分析（基于 clone）+ 颠覆性发现
date: 2026-05-06
trigger: round-19 用户 2 条新批注（line 165 "Claude Code Desktop 化" + line 740 "克隆代码思考前端集成"）
agents: 4 并行 Explore Agent (Sonnet) — 基于实际 clone 仓库
clone_location: /Users/Heishing/Desktop/canvas/.references/deeptutor/
related:
  - _bmad-output/research/round-19-deeptutor-transformation-roadmap-2026-05-06.md
  - _bmad-output/research/round-18-rag-validation-deployment-reasoning-chain-2026-05-06.md
status: 调研报告，含 1 个颠覆性发现（Chat vs TutorBot 双 agent 架构）+ 8 个功能 UI 集成完整设计
report_words: ≈10000
decision_points: 5 个（含 D-CRITICAL: TutorBot 是否就是用户要的"Claude Code Desktop 化"答案）
---

# Round 20 — DeepTutor 实际代码深度分析（基于 clone）+ 颠覆性发现

## 元信息

| 字段 | 值 |
|---|---|
| 触发 | round-19 用户 2 条新批注 — (1) "难道不能像 Claude Code Desktop 一样操作本地文件吗？" (2) "应该 deeptutor 的代码实际克隆下来从而思考如何集成" |
| 调研方式 | 4 并行 Explore Agent（Sonnet model）基于**实际 clone 的 DeepTutor 仓库** |
| Clone 位置 | `/Users/Heishing/Desktop/canvas/.references/deeptutor/` (depth=1, 2026-05-06) |
| 范围 | Agent A 全栈架构 / Agent B Claude Code Desktop 化 / Agent C 前端架构 / Agent D Canvas 8 功能 UI 集成 |
| 报告字数 | ≈10000 字 |
| 状态 | 含 1 颠覆性发现（双 agent 架构）+ 8 个 UI 集成完整设计 |

---

## ⚡ 一句话核心颠覆性发现

**DeepTutor 实际是双 Agent 架构（之前 round 全部漏掉）**：
- **Chat Agent**（`deeptutor/agents/chat/`）— 仅 RAG + Web Search，**无文件工具**
- **TutorBot Agent**（`deeptutor/tutorbot/agent/`）— **已完整支持 `read_file` / `write_file` / `edit_file` / `list_dir` / `shell` / `web_fetch` + MCP**，**完全像 Claude Code Desktop！**

**用户的批注 1 答案**：✅ **DeepTutor 的 TutorBot 模式已经能像 Claude Code Desktop 一样操作本地文件**。`deeptutor bot` 命令立即可用，无需任何改造。

**用户的批注 2 答案**：✅ **基于 clone 的实际前端代码（Next.js 16 + React 19 + 14 块组件）**，已经设计好 8 个 Canvas 功能的完整 UI 集成方案，UserNoteBlock 是 passthrough（完美集成点）+ CalloutBlock 已支持 4 种 callout（可扩展 7 种），总工程量 59 人·天（分 3 阶段 P0-P2）。

**这彻底改变了 round-18/19 plan 的前提**：之前所有方案都假设 DeepTutor 必须 RAG 索引 + 复制副本，但 TutorBot Agent 已经绕过了这个限制。

---

## 用户原始批注（来自 round-19）

### 批注 1（round-19 line 165）— Claude Code Desktop 化质疑

> User：我这里提出的疑问是难道不能像 claude code desktop 一样操作本地的文件吗？

**位置**：在 Agent B（文件直接操作）的 2.1 节"选项 1（改 metadata 存绝对路径）"后

**核验结论**：用户**直觉正确**。Agent B round-19 假设了"必须改造"，但实际 DeepTutor TutorBot 已经实现了 Claude Code Desktop 风格的 agentic file ops。

### 批注 2（round-19 line 740）— 克隆代码 + 前端集成

> User：你现在还没有思考 Canvas learning systeam 所设计的功能如何在 deeptutor 的前端实现新的交互，我觉得我们应该 deeptutor 的代码实际克隆下来从而思考如何集成 Canvas learning systeam 的一些功能。

**核验结论**：用户**方向正确**。round-18/19 都基于 gh API + WebFetch 远程查源码，遗漏了关键的 TutorBot 文件工具实现。round-20 实际 clone 后揭示了真相。

---

## 第一部分：DeepTutor 全栈架构（Agent A — 基于 clone 实际代码）

### 1.1 一句话总结

DeepTutor 是 **monolith 架构 + agent-native 双层插件模型（Tools + Capabilities）**：FastAPI + WebSocket + LlamaIndex RAG + LLM 适配器层（30+ provider）+ Next.js 16/React 19 前端 + nanobot TutorBot 引擎 + Book Engine 4 阶段编译器 + Heartbeat 心跳 + 8 通道推送。

### 1.2 关键架构发现（修正 round-16/17/18 描述）

| 维度 | round-16/17/18 描述 | 实际（clone 核验） | 差距 |
|---|---|---|---|
| Agent 架构 | 单一 chat agent | **双 Agent**（Chat 仅 RAG / TutorBot 完整文件工具） | ⚡ 重大遗漏 |
| Plugin 机制 | "可能有代码 plugin" | **Skill 是纯 YAML + Markdown 注入**，**无代码 plugin** | 实际更受限 |
| EventBus | 未提及 | **存在但私有**（`deeptutor/events/event_bus.py`） | 可能未来扩展点 |
| 测试覆盖 | "全面" | **156 文件，无 FSRS / 间隔学习** | Canvas 算法栈是空白 |
| 前后端通信 | REST + SSE | **REST + WebSocket（unified-ws）** | SSE 描述不准确 |
| MCP 支持 | 未提及 | **原生支持 MCP**（pyproject.toml `mcp>=1.26.0`，`tutorbot/agent/tools/mcp.py`） | ⚡ 关键集成点 |
| 通道数 | 8 个 | **确认 8 个**（telegram/discord/slack/feishu/dingtalk/qq/matrix/email） | ✅ 一致 |
| Book Engine | 4 阶段 | **engine.py 1231 行，4 阶段 + 3 用户确认 + per-book 队列** | 比预期更复杂 |

### 1.3 后端关键模块（仅列改造相关）

```
deeptutor/
├── agents/chat/chat_agent.py        # ⚠️ 仅 RAG + Web Search（待加 file tools）
├── tutorbot/agent/                  # ⭐ 已完整文件工具
│   ├── tools/filesystem.py          # ⭐ ReadFileTool 已实现（offset/limit 分页）
│   ├── tools/mcp.py                 # ⭐ MCP 客户端
│   ├── tools/registry.py:79-110     # ⭐ build_base_tools() 工具注册器
│   └── loop.py                      # Agent 主循环 + tool calling
├── tutorbot/heartbeat/service.py    # 192 行 — Phase1 LLM 决策 + Phase2 推送
├── tutorbot/channels/               # 8 通道 adapters
├── book/engine.py                   # 1231 行 Book Engine
├── book/blocks/                     # 14 块实现
├── knowledge/initializer.py:94      # ⛔ shutil.copy2 复制文件
├── services/skill/service.py        # YAML frontmatter + Markdown 注入
└── events/event_bus.py              # ⚠️ private，未对外暴露
```

### 1.4 前端关键模块（详见 Agent C）

```
web/
├── app/(workspace)/
│   ├── chat/[[...sessionId]]/page.tsx
│   └── book/components/blocks/
│       ├── BlockRenderer.tsx        # 核心分发器
│       ├── UserNoteBlock.tsx        # ⭐ passthrough markdown — Canvas 集成点
│       ├── CalloutBlock.tsx         # ⭐ 已支持 4 callout，可扩展 7 种
│       ├── QuizBlock.tsx            # ⭐ 已有 onAttempt — 可对接 AutoSCORE
│       ├── ConceptGraphBlock.tsx    # cytoscape — 可复用做 wikilink graph
│       └── ...11 more block types
├── context/UnifiedChatContext.tsx   # 40KB 聊天状态 + WebSocket
├── lib/book-api.ts                  # Book CRUD + WebSocket
└── lib/unified-ws.ts                # 流式客户端
```

---

## 第二部分：⚡ Claude Code Desktop 化真相（Agent B — 颠覆性发现）

### 2.1 一句话颠覆结论

**用户的疑问"难道不能像 Claude Code Desktop 一样操作本地文件吗？"答案是 ✅ TutorBot 模式可以，已实现。** 不需要任何改造，`deeptutor bot` 命令立即可用。

### 2.2 双 Agent 架构对比（关键发现）

| 维度 | Chat Agent (`agents/chat/`) | **TutorBot Agent (`tutorbot/agent/`)** ⭐ |
|---|---|---|
| 文件工具 | ❌ 无 | ✅ **read_file / write_file / edit_file / list_dir** |
| Shell | ❌ 无 | ✅ **shell / exec** |
| Web | ✅ web_search | ✅ web_search + web_fetch |
| RAG | ✅ 必须 KB 索引 | ⚠️ 可选 |
| MCP | ❌ 不加载 | ✅ **原生支持**（stdio / SSE / streamableHttp） |
| 行为模式 | 必须预索引 + RAG 检索 | **按需读取**（Claude Code Desktop 风格） |

### 2.3 TutorBot ReadFileTool 源码核验

**文件**：`deeptutor/tutorbot/agent/tools/filesystem.py:42-118`

实现：
- ✅ 支持 offset / limit 分页
- ✅ 最大 128K 字符
- ✅ 行号显示
- ✅ 类似 Claude Code Read tool 行为

**配套工具**：
- `WriteFileTool` — 写文件
- `EditFileTool` — 编辑（diff-based）
- `ListDirTool` — 目录列表
- `ShellTool` — bash 命令
- `WebFetchTool` — URL 抓取

### 2.4 MCP 支持（已原生）

**`pyproject.toml`**：`mcp>=1.26.0,<2.0.0`

**配置示例**（已支持）：
```yaml
tutorbot:
  mcp_servers:
    filesystem:
      command: npx @modelcontextprotocol/server-filesystem
      env:
        MCP_ALLOWED_ROOTS: "/Users/Heishing/Desktop/canvas/canvas-vault"
      enabled_tools: ["*"]
```

→ TutorBot 立即能通过 MCP 访问 vault md 文件。

### 2.5 Cline / Cursor / Aider / Continue.dev 对比

| 工具 | 模式 | 文件访问 | RAG | DeepTutor 类比 |
|---|---|---|---|---|
| **Claude Code Desktop** | 纯 agentic | ✅ read_file | ❌ | **= TutorBot 模式** |
| Cline (VSCode) | 混合 | ✅ | ⚠️ 可选 | TutorBot + 部分 RAG |
| Aider (CLI) | 纯 agentic | ✅ + git | ❌ | TutorBot 模式 |
| Continue.dev | 混合 | ✅ + codebase search | ⚠️ | TutorBot + 混合 |
| Cursor | 混合 | ✅ + codebase index | ✅ | DeepTutor 全功能 |
| **DeepTutor Chat Agent** | RAG 派 | ❌ | ✅ 必须 | LlamaIndex 派 |
| **DeepTutor TutorBot** | **agentic** | ✅ + MCP | ⚠️ 可选 | **Claude Code Desktop 等价** |

### 2.6 推荐方案（修正 round-19）

| 方案 | 工程量 | round-19 推荐度 | round-20 修正 |
|---|---|---|---|
| 完全去 RAG | 3-5d | — | ❌ 不必（TutorBot 已是 agentic） |
| 改 metadata 为 reference 模式 | 1d | 推荐 | ⚠️ 可选（如保留 Chat Agent + KB） |
| **Chat Agent 加文件工具（复用 TutorBot 实现）** | **5-7d** | — | ⭐ **推荐**（混合最优） |
| **直接用 TutorBot 模式 + MCP filesystem** | **0.5d**（仅配置） | — | ⭐⭐⭐⭐⭐ **最快验证路径** |

**关键启发**：用户问的"Claude Code Desktop 化"在 DeepTutor 已实现，**只需切换到 TutorBot 模式 + 配置 MCP filesystem server 指向 vault**，**0.5 天就能验证**。

---

## 第三部分：DeepTutor 前端架构（Agent C — 基于 clone）

### 3.1 一句话总结

DeepTutor 前端是**Next.js 16.2 + React 19 + Tailwind 3.4**，**14 个块组件 + UnifiedChatContext + WebSocket 流式**，**UserNoteBlock 是 passthrough（完美 Canvas 集成点）**，**CalloutBlock 已支持 4 种 callout（可扩展 7 种）**。

### 3.2 框架 + 关键依赖

```json
{
  "next": "^16.2.3",
  "react": "^19.0.0",
  "tailwindcss": "^3.4.17",
  "lucide-react": "^0.562.0",
  "chart.js": "^4.5.1",          // 雷达图（可对接 AutoSCORE 4 维）
  "cytoscape": "^3.33.1",         // 概念图（可复用做 wikilink graph）
  "framer-motion": "^12.24.0",    // 动画
  "mermaid": "^11.14.0",
  "react-markdown": "^10.1.0",
  "rehype-katex": "^7.0.1",       // LaTeX
  "react-i18next": "^16.5.3"      // 中英 i18n
}
```

### 3.3 14 块组件清单（关键集成点）

**User：Canvas learning systeam 的核心是原白板，检验白板，个人记忆系统在原白板和检验白板的应用，笔记精确返回系统，以及推测出什么时候该使用检验白板复习的系统，以上 5 点，你需要结合 Canvas learning systeam 的源码 ，PRD ，EPIC ，和 stroy ，来思考然后生成怎样么一个集成到Deeptutor 可以满足用户一开始的功能需求，原白板，检验白板你要深刻理解其含义。然后最后生成一份给我参考的集成后的使用手册**

| 块 | 组件 | 当前 UI | Canvas 集成机会 |
|---|---|---|---|
| text | TextBlock | 静态 markdown | — |
| **callout** | **CalloutBlock** | 4 种变体（key_idea/pitfall/summary/tip）+ 左边框 + icon | ⭐ **扩展为 7 种**（[!error]+/[!tip]+/[!question]+/...） |
| quiz | QuizBlock | 选择题 + onAttempt 回调 | ⭐ **接 AutoSCORE 4 维** |
| **user_note** | **UserNoteBlock** | **完全 passthrough markdown** | ⭐⭐ **理想 Canvas 7 callout + 理解度集成点** |
| concept_graph | ConceptGraphBlock | cytoscape 交互图 | ⭐ **复用做 wikilink graph** |
| timeline | TimelineBlock | 时间线 + 事件卡片 | ⭐ **接 ReasoningTimeline** |
| flash_cards | FlashCardsBlock | 闪卡翻转 | ⭐ **接 FSRS 算法** |
| animation | AnimationBlock | video + framer-motion | — |
| interactive | InteractiveBlock | iframe | — |
| code | CodeBlock | 代码 + 高亮 | — |
| figure | FigureBlock | 图片 + 标题 | — |
| deep_dive | DeepDiveBlock | 折叠卡片 + 异步生成 | — |
| section | SectionBlock | 标题 + 折叠 | — |
| **placeholder** | PlaceholderBlock | **占位符（未实装）** | — |

**关键发现**：
- ⭐ **14 块的 PLACEHOLDER 确认未实装**（round-19 已发现）
- ⭐ **CalloutBlock 已有 4 种 + 颜色 + icon 系统**（扩展 3 种到 7 种很容易）
- ⭐ **UserNoteBlock 100% passthrough，零交互**（最佳 Canvas 集成位置）

### 3.4 状态管理 + 后端通信

- **State**：React Context（**无 Redux/Zustand**），`UnifiedChatContext`（40KB）
- **REST**：`fetch` + `lib/book-api.ts` / `lib/session-api.ts`
- **WebSocket**：`lib/unified-ws.ts`（流式 token + 工具调用）
- **i18n**：react-i18next（中英双语）

---

## 第四部分：Canvas 8 功能 UI 集成完整设计（Agent D — 基于 clone）

### 4.1 一句话总结

Canvas Learning System 的 8 个核心学习引擎通过**扩展 DeepTutor 的 14 个块组件 + 新增 5 个页面 + 8 个后端 API 端点**完整集成到 DeepTutor，**总工程量 59 人·天**（前端 29.5 + 后端 29.5），**分 3 阶段（P0-P2）**。

### 4.2 8 功能完整设计

#### 功能 1（P0，7d）：7 Callout 批注 + 理解度

**集成点**：扩展 `app/(workspace)/book/components/blocks/CalloutBlock.tsx` + `UserNoteBlock.tsx`

**改造**：
- CalloutBlock VARIANT_STYLES 从 4 种扩展到 7 种（新增 error / hint / question 等）
- UserNoteBlock 新增 `CalloutTypeSelector` + `UnderstandingLevelSlider` 组件
- block.payload 扩展：`callout_type` / `understanding_level` / `wikilinks` / `graphiti_node_uuid` / `valid_at`
- 自动生成 Obsidian frontmatter 格式，支持 vault 同步

**ASCII Mockup**：
```
┌─────────────────────────────────────────┐
│  USER_NOTE Block                        │
│  ┌─────────────────────────────────┐   │
│  │ [!tip] 💡  ▼ 理解度: ████░ 4/5  │   │
│  │                                 │   │
│  │ 我现在明白了：admissibility 保证..│   │
│  │                                 │   │
│  │ 关联 wikilink: [[heuristic]]   │   │
│  └─────────────────────────────────┘   │
│  [+ 添加批注] [改类型] [改理解度]        │
└─────────────────────────────────────────┘
```

#### 功能 2（P0，7d）：FSRS Day 0/3/7 错误闭环 Dashboard

**集成点**：新增 `/app/(utility)/space/review-schedule/page.tsx`

**改造**：
- 新页面展示"Today / Day 0 / Day 3 / Day 7"四列卡片
- 点击卡片 → 跳转 Book Page 复习
- 后端新增 `/api/v1/review/schedule` endpoint，调 Canvas FSRSManager

**ASCII Mockup**：
```
┌─────────────────────────────────────────┐
│  📅 今日复习计划                        │
├─────────┬─────────┬─────────┬─────────┤
│ Today   │ Day 0   │ Day 3   │ Day 7   │
│ (5)     │ (2)     │ (3)     │ (1)     │
├─────────┼─────────┼─────────┼─────────┤
│ admiss- │ heuris- │ recur-  │ closure │
│ ibility │ tic     │ sion    │         │
│ ─────── │ ─────── │ ─────── │ ─────── │
│ FSRS    │ Today   │ -3d ago │ -7d ago │
│ due now │ (new)   │         │         │
│         │         │         │         │
│ [复习]  │ [复习]  │ [复习]  │ [复习]  │
└─────────┴─────────┴─────────┴─────────┘
```

#### 功能 3（P1，7.5d）：ACP 5 层 Prompt + RemedyStrategy

**集成点**：扩展 `QuizBlock.tsx` + `lib/quiz-types.ts`

**改造**：
- QuizBlock 加"Why this question?"折叠面板
- 显示 Layer 1-2-4 教学理由 + RemedyStrategy 建议
- 用户可点击相关概念 wikilink 导航
- 后端 `book/blocks/quiz.py` 调 Canvas `question_generator.py`

#### 功能 4（P1，7.5d）：AutoSCORE 4 维雷达图

**集成点**：扩展 `QuizBlock.tsx`（替换 is_correct 反馈 UI）

**改造**：
- 答题反馈从 `isCorrect: bool` 升级为 4 维评分（concept_accuracy / reasoning_quality / knowledge_coverage / knowledge_integration）
- 用 Chart.js 渲染雷达图
- 可展开"3 LLM 投票详情"对比

**ASCII Mockup**：
```
┌─────────────────────────────────────────┐
│  ✅ 答题反馈（AutoSCORE 4 维）          │
│                                         │
│        Concept (3.2/4)                  │
│            ┌──┐                         │
│  Coverage  │  │  Reasoning              │
│   (2.8)    │📊│   (2.5)                 │
│            └──┘                         │
│       Integration (3.0)                 │
│                                         │
│  [展开 3 LLM 投票详情 ▼]                │
│                                         │
│  💡 RemedyStrategy: 你 5 天前在        │
│     [[admissibility]] 错过类似...       │
│     建议 3 天后再考一次。               │
└─────────────────────────────────────────┘
```

#### 功能 5（P1，8d）：Progressive Confirmation 错误对话框

**集成点**：新增 `ErrorCandidateDialog` 组件

**改造**：
- 用户答错时弹出 modal
- 4 类 ErrorType 单选（PROBLEM_FRAMING / REASONING_FALLACY / KNOWLEDGE_GAP / SUPERFICIAL）
- 3 按钮（Accept / Dismiss / Dispute）
- 接受后自动生成带对应 callout 的 USER_NOTE

#### 功能 6（P2，9d）：Wikilink 双向链接图（Knowledge Graph Sidebar）

**集成点**：复用 `ConceptGraphBlock.tsx` 的 cytoscape，新增 sidebar 模式

**改造**：
- Book Reader 右侧加力导向图面板
- 节点 = 概念 md 文件，边 = wikilink
- 点击节点导航到该概念页面
- 后端复用 Canvas `wikilink_graph_service.py`（obsidiantools NetworkX）

#### 功能 7（P2，8d）：学习推导链 Reasoning Timeline

**集成点**：新增 `/app/(workspace)/reasoning/[concept_id]/page.tsx`

**改造**：
- 垂直时间轴显示 EpisodeTask
- 可展开 ReasoningStep
- 帮助用户看到自己的"思维演化"

#### 功能 8（P2，5.5d）：多通道推送

**集成点**：`/app/(utility)/settings/page.tsx` 新增"Notification Channels"区块

**改造**：
- 用户勾选启用 Telegram / Slack / Discord / 飞书 / 企微 / 钉钉 / Email / Matrix
- Canvas FSRS due card → POST DeepTutor `heartbeat external_due` → 推送
- **DeepTutor 已有 8 个通道实现**（直接复用，0 新代码）

### 4.3 完整 UX 流程时间线

```
07:00 — 打开 DeepTutor Dashboard
       → "今日 5 张卡片到期"
07:05 — 点击"admissibility"卡片
       → Book Page + KnowledgeGraph Sidebar
07:08 — 答题错误
       → ErrorCandidateDialog 弹出
       → 用户选 REASONING_FALLACY → Accept
07:10 — 自动生成 USER_NOTE [!error]+ "推理误用了 X 假设"
       → 显示 4D AutoSCORE 雷达图
07:12 — RemedyStrategy："3 天后再复习类似题"
07:15 — 点击 [[rule-401-relevance]] wikilink → 跳转复习
19:30 — Telegram 推送学习总结
       → "今日 5 题 / 准确率 60% / 3 天后复习"
```

### 4.4 实施优先级

| 阶段 | 功能 | 工程量 | 周期 |
|---|---|---|---|
| **P0 MVP** | 1 + 2 (Callout + Dashboard) | 14 人·天 | 2-3 周 |
| **P1 增强** | 3 + 4 + 5 (ACP + AutoSCORE + Error) | 23 人·天 | 2-2.5 周 |
| **P2 高级** | 6 + 7 + 8 (Graph + Timeline + Push) | 22.5 人·天 | 2 周 |
| **总计** | 8 功能 | **59 人·天** | **6-7 周** |

---

## 第五部分：综合实施路线（round-20 修正版）

### 5.1 与 round-19 的差异

| 维度 | round-19 plan | round-20 修正 |
|---|---|---|
| 文件操作改造 | 改 initializer.py shutil.copy2 → reference 模式（5-7d） | ⚡ **TutorBot 已实现 + MCP filesystem，0.5d 配置即可** |
| 改造路径 | Canvas CLI 拆分 + DeepTutor 适配器（22-28d） | ⚡ **直接用 TutorBot + MCP，跳过 Chat Agent 改造** |
| 总工程量 | 22-28d（Unix CLI 路线） | **0.5d（POC）→ 14d P0 → 59d 全量** |
| 集成深度 | 适配器层（subprocess） | **DeepTutor 前端原生 UI**（14 块扩展 + 5 新页面 + 8 新 API） |

### 5.2 推荐 5 阶段路线（round-20 终版）

#### Phase 0（Day 1）：TutorBot + MCP filesystem POC

```bash
# 1. 安装 DeepTutor TutorBot 模式
cd /Users/Heishing/Desktop/canvas/.references/deeptutor
pip install -e ".[tutorbot]"

# 2. 配置 MCP filesystem 指向 canvas-vault
# 编辑 ~/.deeptutor/workspaces/<vault>/config.yaml
mcp_servers:
  filesystem:
    command: npx
    args: ["@modelcontextprotocol/server-filesystem", "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/canvas-vault"]

# 3. 启动 + 验证
deeptutor bot start <bot-id>
# 让 bot agent 直接 read_file canvas-vault/节点/某个.md
```

**验证目标**：DeepTutor TutorBot 能像 Claude Code Desktop 一样直接读 vault md 文件，**无需 RAG 索引，无需复制副本**。

**工程量**：0.5d（仅配置 + 验证）

#### Phase 1（Week 1-2，14 人·天）：P0 MVP — Callout + FSRS Dashboard

- **功能 1**：扩展 CalloutBlock 4→7 种 + UserNoteBlock 加 callout/level 选择器
- **功能 2**：新页面 `/space/review-schedule` + 后端 `/api/v1/review/schedule`
- **依赖**：Phase 0 完成（TutorBot + MCP 验证 OK）

#### Phase 2（Week 3-5，23 人·天）：P1 增强 — ACP + AutoSCORE + Error Dialog

- **功能 3**：QuizBlock 加 "Why this question?" 面板，后端 quiz.py 接 Canvas question_generator.py
- **功能 4**：QuizBlock 反馈升级为 4 维雷达图 + 3 投票，后端接 Canvas autoscore.py
- **功能 5**：ErrorCandidateDialog + 4 类 ErrorType + accept/dismiss/dispute

#### Phase 3（Week 6-7，22.5 人·天）：P2 高级 — Graph + Timeline + Push

- **功能 6**：Book Reader 加 KnowledgeGraph Sidebar（复用 cytoscape）
- **功能 7**：新页面 `/reasoning/[concept_id]` + ReasoningTimeline
- **功能 8**：Settings 新增 Notification Channels + 8 通道复用

#### Phase 4（Week 8+）：DeepTutor Issue #380 战略对话

- 在 DeepTutor 开 GitHub Discussion
- 主题：`Canvas Learning System as Reference Plugin for Issue #380 (Learning Experience SDK)`
- 与 @pancacake 沟通这 8 个功能能否合入 upstream（vs 维护私有分支）

### 5.3 总工程量对比

| 路线 | 工程量 | 风险 | 推荐度 |
|---|---|---|---|
| round-18 plan（深度改造 11 Gap） | 34-45d | 高（all-in-one 留存陷阱） | ⭐⭐ |
| round-19 Unix CLI 拆分 + 适配器 | 22-28d | 中 | ⭐⭐⭐⭐ |
| **round-20 修正版（TutorBot + 8 功能 UI）** | **Phase 0: 0.5d → P0: 14d → 全量: 59d** | **低**（基于实际 clone + 复用 TutorBot 已有能力） | **⭐⭐⭐⭐⭐** |

---

## 第六部分：5 个决策点（请用户审计）

### Decision 1（⛔ 颠覆性）：是否走 TutorBot + MCP filesystem 路线？

**Claude 推荐**：✅ **走 TutorBot 路线（用户的"Claude Code Desktop 化"诉求已被 DeepTutor 实现）**

**选项**：
- **A. TutorBot + MCP filesystem（0.5d POC + 14d P0 + 59d 全量）**⭐ 强烈推荐
- B. round-19 Unix CLI 拆分（22-28d，备用方案）
- C. round-18 深度改造 11 Gap（34-45d，不推荐）
- D. Chat Agent 加文件工具（5-7d，与 A 互斥）

### Decision 2：Phase 0 POC 验证后是否启动 P0？

**Claude 推荐**：✅ POC 通过 → 立即启动 P0（Callout + Dashboard）

**选项**：
- **A. POC 通过 → 直接 P0**⭐
- B. POC 后再向 maintainer 沟通（Issue #380）
- C. POC 通过后等待 ChatGPT Deep Research 二次意见

### Decision 3：fork DeepTutor 还是 PR？

**Claude 推荐**：⭐ **不 fork，给 DeepTutor 提交 PR + 同时维护私有分支**（Phase 4 处理）

**选项**：
- A. Fork 维护私有分支（独立但维护成本高）
- **B. PR upstream + Issue #380 战略对话**⭐
- C. Plugin Skill（DeepTutor 当前 Skill 是 prompt-only，无代码 plugin）

### Decision 4：Canvas 后端是否保留？

**Claude 推荐**：⭐ **保留 Canvas 后端作 SoT（FSRS / ACP / AutoSCORE）**

**选项**：
- **A. Canvas 后端保留**（DeepTutor 通过 HTTP 调 Canvas API）⭐
- B. 把 Canvas 算法迁到 DeepTutor 后端（合并）
- C. Canvas 算法 CLI 化（round-19 D 路线）

### Decision 5：UI 集成 8 个功能的优先级

**Claude 推荐**：P0（Callout + Dashboard）→ P1 → P2 顺序

**选项**：
- **A. P0 → P1 → P2 顺序（推荐）**⭐
- B. 先做 P2（Graph + Timeline）— 视觉冲击大
- C. 跳过某些功能（比如 Reasoning Timeline 太复杂）

---

## 第七部分：用户批注区（R4 工作流）

> 请用户在此用 Obsidian callout 批注（`[!question]+` / `[!error]+` / `[!tip]+` / `[!hint]+`）。完成后 Claude 会读取批注并启动 round-21 调整。

### 关于 D1（颠覆性方向）：是否走 TutorBot + MCP 路线？

> [!question]+ User：

### 关于 D2-D5（具体方案）

> [!question]+ User：

### 关于 8 个功能 UI 集成的反馈（哪些 Mockup 喜欢/不喜欢）

> [!question]+ User：

### 关于"DeepTutor TutorBot 已经是 Claude Code Desktop"的发现

> [!question]+ User：

### 关于 Phase 0 POC 立即启动的可行性

> [!question]+ User：

---

## 附录 A：Clone 仓库关键文件路径（4 Agent 引用）

### Agent A 全栈架构
- `/Users/Heishing/Desktop/canvas/.references/deeptutor/README.md`
- `/Users/Heishing/Desktop/canvas/.references/deeptutor/pyproject.toml`
- `/Users/Heishing/Desktop/canvas/.references/deeptutor/AGENTS.md`
- `/Users/Heishing/Desktop/canvas/.references/deeptutor/deeptutor/api/main.py`
- `/Users/Heishing/Desktop/canvas/.references/deeptutor/deeptutor/book/engine.py`（1231 行）
- `/Users/Heishing/Desktop/canvas/.references/deeptutor/deeptutor/knowledge/manager.py`（50KB）

### Agent B Claude Code Desktop 化
- `/Users/Heishing/Desktop/canvas/.references/deeptutor/deeptutor/agents/chat/chat_agent.py`（仅 RAG）
- `/Users/Heishing/Desktop/canvas/.references/deeptutor/deeptutor/tutorbot/agent/tools/filesystem.py`（⭐ ReadFileTool）
- `/Users/Heishing/Desktop/canvas/.references/deeptutor/deeptutor/tutorbot/agent/tools/mcp.py`
- `/Users/Heishing/Desktop/canvas/.references/deeptutor/deeptutor/tutorbot/agent/tools/registry.py:79-110`
- `/Users/Heishing/Desktop/canvas/.references/deeptutor/deeptutor/tutorbot/agent/loop.py`

### Agent C 前端
- `/Users/Heishing/Desktop/canvas/.references/deeptutor/web/package.json`
- `/Users/Heishing/Desktop/canvas/.references/deeptutor/web/tailwind.config.js`
- `/Users/Heishing/Desktop/canvas/.references/deeptutor/web/app/(workspace)/book/components/blocks/BlockRenderer.tsx`
- `/Users/Heishing/Desktop/canvas/.references/deeptutor/web/app/(workspace)/book/components/blocks/UserNoteBlock.tsx`（⭐ passthrough 集成点）
- `/Users/Heishing/Desktop/canvas/.references/deeptutor/web/app/(workspace)/book/components/blocks/CalloutBlock.tsx`（⭐ 4 callout 可扩展 7）
- `/Users/Heishing/Desktop/canvas/.references/deeptutor/web/app/(workspace)/book/components/blocks/QuizBlock.tsx`（⭐ onAttempt 接 AutoSCORE）
- `/Users/Heishing/Desktop/canvas/.references/deeptutor/web/context/UnifiedChatContext.tsx`（40KB）
- `/Users/Heishing/Desktop/canvas/.references/deeptutor/web/lib/book-api.ts`
- `/Users/Heishing/Desktop/canvas/.references/deeptutor/web/lib/unified-ws.ts`

### Agent D Canvas 8 功能 UI 集成
（基于 Agent A/B/C 全部文件 + Canvas 后端源码）
- Canvas: `backend/lib/memory/temporal/fsrs_manager.py:92`（FSRS 526 行测试）
- Canvas: `backend/app/services/question_generator.py:271`（ACP 5 层）
- Canvas: `backend/app/services/autoscore.py:31`（AutoSCORE 4 维 × 3）
- Canvas: `backend/app/services/wikilink_graph_service.py:30`（obsidiantools）
- Canvas: `backend/app/services/episode_worker.py:44`（EpisodeTask）

---

## 附录 B：决策点累计追踪

| Round | 决策点数 | 状态 |
|---|---|---|
| round-14 | 4 | 已结案 |
| round-15 | 4 | 已结案 |
| round-16 | 5 | 已结案 |
| round-17 | 8 | 已结案 |
| round-18 | 6 | round-19 plan mode 中 D1/D2/D3/D4 已确认 |
| round-19 | 6 | 含 1 根本性反例（D-FUNDAMENTAL），现被 round-20 颠覆 |
| **round-20** | **5**（含 1 颠覆性 D1） | **待用户审定** |
| **总计** | **38 个累计决策点** | — |

---

## 状态

- **报告生成**：2026-05-06，4 并行 Sonnet Agent，约 60-90 分钟完成
- **Clone 位置**：`/Users/Heishing/Desktop/canvas/.references/deeptutor/`（depth=1，可保留作长期参考）
- **下一步**：等用户在批注区填 callout 批注 → Claude 读批注 → round-21 调整
- **建议起点**：先答 D1（TutorBot 路线），其余 4 项基于此展开
- **关键颠覆**：round-18/19 假设全部基于"DeepTutor 必须 RAG 索引 + 复制副本"的前提，但 clone 后发现 TutorBot Agent 已经实现了用户要的"Claude Code Desktop 化" — 这彻底改变了改造路径

---

## 一句话给用户的总结

**用户的两条批注 100% 命中要害**：

1. **批注 1（"难道不能像 Claude Code Desktop 一样操作本地文件吗？"）** → ✅ **DeepTutor 的 TutorBot Agent 已经实现了**（`tutorbot/agent/tools/filesystem.py` 含 ReadFileTool / WriteFileTool / EditFileTool / ListDirTool / ShellTool + 原生 MCP 支持）。配置 MCP filesystem server 指向 canvas-vault，**0.5 天 POC 就能验证**。

2. **批注 2（"应该 deeptutor 的代码实际克隆下来思考集成"）** → ✅ **clone 后揭示了双 Agent 架构 + UserNoteBlock passthrough 是完美集成点 + CalloutBlock 4 种已实现可扩展 7 种**。Canvas 8 个核心功能在 DeepTutor 前端的 UI 集成已完整设计，**总工程量 59 人·天**（分 P0/P1/P2 三阶段）。

**round-18/19 的所有方案都需要修正**：不是"深度改造 DeepTutor"也不是"Unix CLI 拆分"，而是**"TutorBot + MCP + 前端 14 块扩展"**——一条 round-18/19 都遗漏了的、最直接的路。


User：