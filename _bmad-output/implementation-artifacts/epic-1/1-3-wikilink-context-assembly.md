---
story_id: "1.3"
epic_id: "1"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P0"
estimate_hours: 6
depends_on: ["1.2"]
blocks: ["2.1"]
trace:
  - "FR-ADAPT-02"
---

# Story 1.3: Wikilink MCP 工具注册

> **[RENAMED TITLE]**: 本文件原名 `Wikilink 上下文组装`（Paradigm 1 预组装+压缩），2026-04-13 重写为 `Wikilink MCP 工具注册`（Paradigm 2 AI 按需调用）。文件名 `1-3-wikilink-context-assembly.md` 保留以维持 References 链完整性。详见 Deviation Note N8。

Status: ready-for-dev

## Story

As a 系统,
I want 把双向链接图的查询能力注册为 MCP 工具供 Claude Code CLI 按需调用,
So that AI 能自主决定读取哪些笔记、何时拉取邻居，由 Opus 1M 上下文窗 + Anthropic `compact_20260112` API 承担容量压力，Backend 不做预组装也不做压缩。

## 通俗化解释（给学习者）

> **一句话说**: 以前是系统替 AI 决定"该看你哪些笔记"然后打包塞过去，现在是 AI 自己判断"我该翻哪篇"然后按需去取，像真人助教一样只拿当下用得上的材料。

**你会遇到的场景**:
- 你问 AI："LLRB 树的删除操作为什么这么复杂？"—— AI 会先翻你的 LLRB 笔记原文，再顺手看一眼相邻概念（红黑树、2-3 树）
- 你让 AI 分析："为什么我做这道递归题又错了？"—— AI 会直接去翻你过往记录的错误清单，而不是每次都让你重述一遍

**这个功能帮你**:
- 回答更贴你的笔记：AI 看的就是你写过的原文，而不是凭空猜测或套用通用知识 📚
- 不再被无关信息淹没：AI 只拉它真正要用的那几篇，速度更快、思路更清楚 ⚡
- 记录有温度：你标过的 tips、踩过的坑、讨论过的概念关系，AI 下次会主动翻出来用

**旧方式 vs 新方式**（生活化比喻）🍳:
- ❌ **旧方式像做菜前**：厨房助手替你把冰箱里 20 种食材全切好、装碗、按比例摆出来 —— 万一你今天只想吃个清炒西兰花，那 90% 的食材都白切了，桌子还被占满
- ✅ **新方式像自助厨房**：你只说"想做清炒西兰花"，AI 自己走到冰箱按需取西兰花 + 蒜 + 油，其他 17 样原封不动 —— 需要时再去拿，不需要就不碰

**你能看到/操作到什么**:
- 你提问后，可以在对话区下方看到实时的"工具调用"指示器：会显示"正在读取你关于 LLRB 的笔记"、"正在查看相邻概念"、"正在翻查历史错误记录"等反馈 🔍
- 这是 AI 在"边想边查"，而不是以前那种"一次性吞下一大堆然后慢慢消化"
  **User：首先你要明确定位一下，你这里的检索是对应我的 Canvas learning systeam 中的个人记忆系统，还是我们的笔记检索系统，以及如果笔记一多怎么检索才能高效，是否可以参考 Karpathy 和 Graphsify 的 obsidian 检索操作，你可以和我说一下，你从他们哪里获得了什么启发。**

> **[A 2026-04-13]** 简答如下，完整调研（3 并行 Agent：Karpathy 社区追踪 + Graphify 项目拆解 + 项目内部架构）沉淀至 [[karpathy-graphify-insights-2026-04-13|📚 完整研究报告]]：
>
> **① 定位**：本 Story 的 8 个 MCP 工具**全部属于「笔记检索系统」方向**，不涉及个人记忆。个人记忆检索走独立路径（Graphiti MCP 工具 + LanceDB 向量，均不在本 Story 范围）。PRD §三套检索系统（line 317-323）的完整图景：Graphify（项目内部同名组件）负责概念结构 · LanceDB+bge-m3 负责段落向量 · Graphiti 负责学习历程。
>
> **② 大量笔记的高效检索策略**：**User：2-hop 硬限制 + BFS + visited set 去循环，你这个是在原来 Canvas learning systeam 上使用的，我都降级在 claudian 加 obsidian 的情况下，请问我还需要使用这个吗？**
>
> > **[A2 2026-04-13 N1]** ✅ **仍需保留**，但**定位变了**。原 Canvas 架构下 2-hop 是"防 IPC 载荷 > 100KB 的容量约束"；降级后（Claudian+Obsidian）Backend 依然保留（FastAPI+Neo4j+LanceDB），AI 通过 MCP 工具 `get_neighbors` 按需调用。2-hop 硬限从"**容量瓶颈**"转为"**AI 自主决策下的性能保障**"——防后端图遍历指数爆炸（< 200ms SLA）+ 防 Opus 1M 上下文窗过载。不能删。详见 [[karpathy-graphify-insights-2026-04-13|📚 研究报告]] §N1。
>
> - **当前已规划**：2-hop 硬限制 + BFS + visited set 去循环；frontmatter 摘要优先（`extract_tips` 比 `read_note` 快）；Opus 1M 窗 + Anthropic `compact_20260112` API 兜底
> - **需补充**（源自调研）：`index.md` 入口（冷启动 AI 先读 overview 再深挖）· 预编译聚合页（ingest 阶段就写好概念总结，不每次现场拼装）· 两段式流水线（Wikilink 图先 0-LLM 遍历，Graphiti 再语义丰富）
>   **User：你这里 index.md 主要归纳什么内容？：1，表示原白板的节点或者检验白板的节点？；2，用来归纳我们的批注，方便来考察我？ 请你结合我们原来的 Canvas learning systeam 的设计和 Karpathy 的思路后 分别启动两个并行 agent deep explore 后回复我**
>
> > **[A2 2026-04-13 N2]** 🟡 **不是 1 也不是 2，而是 1+2+学习数据融合**。已按你要求启动 2 并行 Agent（Karpathy gist 原样核查 + Canvas 白板结构深挖）。**Karpathy 原定义**：index.md 是 content-oriented catalog，LLM 自动维护，格式 `- [[link]] — one-liner (metadata)`，按 category 分 section，用于 LLM 冷启动找相关页再 drill into。**Canvas 版应叠加**：mastery 分组（🔴弱/🟡学习中/🟢已掌握）+ recent exams 索引 + annotations **热点统计**（不是批注全文，批注全文留在各节点 page 里）。**核心定位**：回答"你现在该刷哪几个节点？"（学习导航），**不是**"文件系统 ls"（目录清单）。完整规范（含字段清单、更新机制、MCP 工具映射、开放问题）详见 [[canvas-index-md-spec-v1|📐 Canvas index.md 规范 v1]]。
>
> **③ Karpathy 启发**（他 2024-02-25 在 X 公开"love letter to @obsdmd"，2026-04 发 `llm-wiki` gist 5k+ stars / 16M X views）：
> - **三层架构**：`raw sources`（不可变）+ `wiki`（LLM 生成 md）+ `schema`（CLAUDE.md 指挥）
> - **`index.md` + `log.md` 双文件驱动**：前者是 AI 入口，后者是 append-only 操作审计
> - **反 RAG 哲学**："Knowledge is compiled once and then kept current, not re-derived on every query"——对抗 Paradigm 2 退化成 RAG-lite 最关键的心智模型
> - **前缀 tag**：他用 `watch:` / `listen:` / `read:`，可迁为 `concept:` / `proof:` / `gotcha:` / `review:`
>   **User：`concept:` / `proof:` / `gotcha:` / `review `  你这里的几个 Tag 的设计是否对上了我的 Canvas learning systeam 的设计需求，我们的整一个 Canvas learning systeam 的使用又不是只局限于 CS 的课程**
>
> > **[A2 2026-04-13 N3]** ❌ **你指出的对，旧设计不够通用**。调研 Matuschak / Zettelkasten / Ahrens / PARA / Anki 五大 PKM 学派后确认：`proof:` 偏 CS/数学（历史/文学没"证明"一说），`gotcha:` 是编程术语。新设计：**4 维正交 tag 体系**——`type/*`（concept/claim/question/example/reference/moc/fleeting）+ `state/*`（new/learning/mastered/weak/confused）+ `src/*`（read/watch/listen/lecture/exercise，保留 Karpathy 风格）+ `todo/*`（review/exam/expand/link，基于 PARA）。旧 tag 裁决：`proof:` → 拆为 `type/claim` + `type/example`；`gotcha:` → `state/weak`（通用薄弱点）。跨学科已验证 CS/数学/文学/历史/哲学/艺术/语言/物理全覆盖。Obsidian 原生支持前缀 tag，**零代码改动**。完整规范（含维度表、组合示例、实施要点、Matuschak 陷阱警示）详见 [[canvas-crossdiscipline-tags-v1|🏷️ 跨学科 tag 体系 v1]]。
>
> **④ Graphify 启发**（`safishamsi/graphify`，Karpathy Threads 点名，48h 爆火）：
> - **4 个正交 MCP 工具**：`query_graph` / `get_node` / `get_neighbors` / `shortest_path`——**与本 Story 的 8 工具高度同构**，证明"拆多个正交 MCP 工具"是 2026 社区收敛答案，非我们独创
> - **两段式提取**：Tree-sitter 先做 0-LLM 结构化 → Claude subagents 再做语义（71× token 压缩）
> - **Edge 三态 tag + confidence**：`EXTRACTED` / `INFERRED` / `AMBIGUOUS` + 0-1 分数，可迁到掌握度建模
> - **Leiden 社区聚类**：按边密度分簇，替代向量库固定维度，未来笔记簇自动发现可用
>
> **⚠️ 命名冲突**：~~外部开源 Graphify（Karpathy 点名爆火）与 PRD §三套检索里的项目内部 Graphify 组件同名，未来讨论需明确前缀。~~ **【此警示已于 2026-04-13 作废，详见下方 A2 N4】**
> **User：你要弄清楚我们 PRD 里面所提到的Graphify 组件 究竟是什么？**
>
> > **[A2 2026-04-13 N4]** 💥 **重大发现：不存在"命名冲突"——两者是同一个东西**。深度调查（独立 Explore Agent 扫 PRD + architecture + backend code + Git log + OpenSpec + Story 3.2/3.5）确认：⚠️ **空规划 + 借用外部包**。
> >
> > - PRD line 76 声明 `Graphify v0.3.17` ✅，line 317-323 列入三套检索 ✅
> > - `backend/requirements.txt` **未添加 `graphifyy` 依赖** ❌
> > - `backend/**/*graphify*.py` 文件数为 **0** ❌
> > - `class Graphify` 定义不存在 ❌
> > - Story 3.2 (`pip install graphifyy>=0.3.17`) 和 Story 3.5 均 `ready-for-dev` **从未启动** ❌
> >
> > **结论**："项目内部 Graphify" = 计划集成外部 `graphifyy` v0.3.17 PyPI 包（即 `safishamsi/graphify` 的 Python 发行版），**不是自研**。本文上方 ⚠️ 命名冲突警示已**作废**。完整证据链、当前状态矩阵、3 个后续动作建议详见 [[karpathy-graphify-insights-2026-04-13|📚 研究报告]] §3.2（已于 2026-04-13 修正版）。
>
> **5 条可操作借鉴（按优先级）**：P0 加 `read_index()` MCP 工具 · P1 预编译聚合页 · P1 两段式流水线 · P2 Edge 三态 tag 迁到掌握度 · P2 Leiden 聚类做笔记簇。详细证据链、优先级理由、实施成本见研究文档。

## Acceptance Criteria

1. **Given** 学习者通过 Claude Code CLI 发起对话
   **When** AI 判断需要上下文时
   **Then** AI 可调用 `read_note(path)` 读取任意 .md 笔记原文
   **And** 返回内容包含完整 frontmatter + body，无压缩无截断

2. **Given** AI 需要发现概念间关系
   **When** 调用 `get_neighbors(note_path, hop=2)`
   **Then** 返回 N-hop 邻居列表（由 WikilinkGraphService 支持，Story 1.2）
   **And** 每个邻居包含 `path` + `title` + `hop_distance`

3. **Given** 学习者的 concept.md 含 `tips[]` / `errors[]` / `relationships[]`
   **When** AI 调用 `extract_tips` / `extract_errors` / `get_relationships`
   **Then** 结构化返回对应字段数组
   **And** 不读 body，只读 frontmatter，响应更快

4. **Given** 某笔记的 frontmatter 解析失败或文件不存在
   **When** MCP 工具被调用
   **Then** 返回 `{"error": "parse_failed" | "not_found", "path": ...}`
   **And** 不抛异常，AI 可收到错误继续决策

5. **Given** AI 需要规划"读哪些邻居"
   **When** 调用 `list_wikilinks(note_path)`
   **Then** 返回笔记内所有 `[[wikilinks]]` 的解析路径
   **And** AI 可选择性后续调用 `read_note`

6. **Given** 原笔记挂在 Canvas 节点上
   **When** 调用 `read_canvas_node(canvas_id, node_id)`
   **Then** 返回节点关联的 .md 路径 + 节点元数据

## Tasks / Subtasks

- [ ] Task 1: MCP 工具注册骨架 (AC: #1-6)
  - [ ] 1.1: 创建 `backend/app/mcp/tools/wikilink_tools.py`
  - [ ] 1.2: 为 8 个工具定义函数签名 + docstring + Pydantic schema（`read_note` / `get_neighbors` / `get_frontmatter` / `extract_tips` / `extract_errors` / `get_relationships` / `list_wikilinks` / `read_canvas_node`）

- [ ] Task 2: 读取类工具实现 (AC: #1, #3, #5)
  - [ ] 2.1: `read_note` 用 `python-frontmatter` 拆分 frontmatter + body，原文返回
  - [ ] 2.2: `extract_tips` 正则匹配 `[!tip]+` callout（多行）
  - [ ] 2.3: `extract_errors` / `get_relationships` 从 frontmatter 字段读（不读 body）
  - [ ] 2.4: `list_wikilinks` 正则匹配 `[[...]]` 模式（含 `[[Concept|Alias]]` 形式）
  - [ ] 2.5: `get_frontmatter` 仅返回 frontmatter 字段

- [ ] Task 3: 图遍历类工具 (AC: #2, #6)
  - [ ] 3.1: `get_neighbors` 调用 `WikilinkGraphService.get_neighbors()`（Story 1.2 产出）
  - [ ] 3.2: `read_canvas_node` 读 .canvas JSON 映射节点到 .md 路径（保留旧 .canvas 读取能力作为辅助）

- [ ] Task 4: 在 MCP server 注册 (AC: #1-6)
  - [ ] 4.1: 在 `backend/app/mcp/server.py` 添加 "Wikilink Tools" 标签
  - [ ] 4.2: 参照现有 `query_mastery` (mastery_tools.py) 注册方式
  - [ ] 4.3: 验证 FastAPI-MCP v0.4.0 patch 不影响新工具

- [ ] Task 5: 错误容忍 (AC: #4)
  - [ ] 5.1: frontmatter 解析失败 → 返回 `{"error": "parse_failed", "path": ...}`
  - [ ] 5.2: 文件不存在 → 返回 `{"error": "not_found", "path": ...}`
  - [ ] 5.3: structlog warning 记录每次错误，不抛异常

- [ ] Task 6: 测试 (AC: #1-6)
  - [ ] 6.1: `backend/tests/unit/test_wikilink_tools.py` — 每个工具 happy path + error path
  - [ ] 6.2: 对 `extract_tips` 的多行 callout 正则做专项测试（含嵌套、嵌入代码块）
  - [ ] 6.3: 对 `list_wikilinks` 的别名语法（`[[A|显示名]]`）做专项测试

## Dev Notes

- **Paradigm 2 vs Paradigm 1**: 本 Story 采用工具化范式（AI 自主调用），非组装化范式（Backend 预包装）。对应 `_bmad-output/planning-artifacts/architecture.md` 的 Mode D 架构（Claude Agent SDK spawn 官方 Claude Code CLI + FastAPI-MCP ASGI 直连）
- **为什么不压缩**:
  - (a) Opus 1M 上下文窗足够宽
  - (b) Claude Code CLI 会用 Anthropic `compact_20260112` API 在超窗时兜底压缩
  - (c) AI 自主调用不会"过度拉取"（相比于 Backend 预先组装打包所有邻居）
  - (d) 2025 社区 Paradigm 1（预组装+压缩）已 ABANDONED，被 Tool-based 和 RAG 全面替代
- **WikilinkGraphService 依赖**: Story 1.2 的产出；本 Story 的 `get_neighbors` 工具是其 MCP 包装层
- **frontmatter 解析**: 用 `python-frontmatter`（已在 backend 依赖中），不自己 YAML parse
- **callout 正则**: `[!tip]+` 多行匹配模式 `^>\s*\[!tip\]\+[\s\S]*?(?=^[^>]|\Z)`，MULTILINE 模式
- **wikilink 正则**: `\[\[([^\]]+?)(?:\|.*?)?\]\]` 处理 `[[Concept]]` 和 `[[Concept|Alias]]`
- **MCP 工具风格参考**: `backend/app/mcp/tools/mastery_tools.py` 的 `query_mastery` 模式
- **错误容忍哲学**: 所有工具不抛异常，只返回 `{"error": ..., "path": ...}` 字典让 AI 决策后续行动
- **[DECISION-CONFIRMED: context-assembly-paradigm] 2026-04-13**: 决议采用 Paradigm 2 工具化架构。证据链：Opus 1M GA + Claudian 代码零压缩逻辑（GitHub 实证）+ P1 社区废弃 + Mode D 架构本身就是 P2
- **Attribution**: 架构方法论参考 `gitee.com/free/claude-code`（Apache 2.0）的 MCP 工具注册模式，不抄代码
- **遗留 DialogContextService 处理**: 不新建。如未来需要"手动预组装"场景（例如无 CLI 的批处理），再独立 Story 引入
- **structlog**: `structlog.get_logger(__name__)` 统一

### 触发机制说明（沿用 Paradigm 1 版本，内容不变）

| 元素 | 触发方式 | 写入目标 |
|------|---------|---------|
| Tips `[!tip]+` | 用户在 md 编辑器中手写 `> [!tip]+ 关键知识点` → 保存文件时系统解析 callout | frontmatter `tips[]` 数组更新 |
| Errors `errors[]` | AI 对话中检测到误解 → `record_error` MCP 工具自动触发 | frontmatter `errors[]` + Graphiti 双写 |
| Relationships `relationships[]` | `/edge_discuss` Skill 讨论结束 → 更新当前概念的 frontmatter | concept.md 的 `relationships[]` 字段 |

**注意**: Tips 是用户主动标记，errors 是 AI 自动检测，relationships 是 Skill 讨论后自动记录。本 Story 仅提供"读取"工具，不负责写入。

### Project Structure Notes

- 新建文件：`backend/app/mcp/tools/wikilink_tools.py`
- 修改文件：`backend/app/mcp/server.py`（注册 8 个新工具）
- 测试文件：`backend/tests/unit/test_wikilink_tools.py`
- 遗留文件**不动**：`backend/app/services/context_enrichment_service.py`（保留 .canvas JSON fallback 能力）

### References

- [Source: _bmad-output/planning-artifacts/prd.md#FR-ADAPT-02] — 双向链接图为 AI 对话提供按需查询工具（措辞已于 2026-04-13 更新为 Paradigm 2）
- [Source: _bmad-output/planning-artifacts/prd.md#FR-CONV-11] — 上下文管理原则（Paradigm 2 下由 Anthropic compact API 兜底，详见 FR-CONV-11 新措辞）
- [Source: _bmad-output/planning-artifacts/epics.md#Story-1.3] — AC 原文
- [Source: _bmad-output/planning-artifacts/architecture.md] — Mode D 架构（本 Story 是其实施落地）
- [Source: backend/app/services/wikilink_graph_service.py] — Story 1.2 产出，本 Story 的 `get_neighbors` 工具后端
- [Source: backend/app/mcp/tools/mastery_tools.py] — MCP 工具风格参考
- [Source: backend/app/mcp/server.py] — MCP 注册方式参考
- [Source: gitee.com/free/claude-code] — Apache 2.0 开源项目（MCP 工具注册模式参考，不抄代码）

## UAT Script

> 非技术用户验收脚本

1. **验证 read_note 被自主调用** (AC: #1)
   - 通过 Claude Code CLI 打开任意概念笔记，问一个关于该概念的问题
   - 观察后端 structlog 日志：应看到 `mcp_tool_invoked: read_note(path=...)` 记录
   - AI 回答中应引用到笔记原文细节（而不只是通用知识）

2. **验证 get_neighbors 被按需调用** (AC: #2)
   - 问 AI："这个概念和它的相关概念有什么关系？"
   - 观察后端日志：应看到 `mcp_tool_invoked: get_neighbors(note_path=..., hop=2)` 记录
   - AI 回答中涉及的"邻居"应和笔记实际的 `[[wikilinks]]` 一致

3. **验证 extract_tips 按需调用** (AC: #3)
   - 向 AI 询问："这个概念的关键 tips 有哪些？"
   - 观察后端日志：应看到 `extract_tips` 被调用
   - 返回的 tips 应来自笔记 frontmatter 的 `tips[]` 字段

4. **验证错误容忍** (AC: #4)
   - 让 AI 尝试读取一个不存在的笔记名（例如故意输入错别字）
   - 观察后端日志：应看到 `not_found` 错误 warning，但不抛异常
   - AI 应收到错误信号并给出"笔记不存在"的回应，而非系统崩溃

5. **验证图遍历缓存生效** (AC: #2, 回归 Story 1.2)
   - 连续让 AI 对同一笔记做 20 次邻居查询（不同问题）
   - 观察 WikilinkGraphService 的日志：首次 `graph_build`，后续应命中缓存
   - 响应体感时间不退化

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-1.3.1 | pytest | `.venv/bin/pytest backend/tests/unit/test_wikilink_tools.py -x -q` | 0 failed |
| CP-1.3.2 | ruff | `ruff check backend/app/mcp/tools/wikilink_tools.py` | exit 0 |
| CP-1.3.3 | manual | 启动后端 → `curl http://localhost:8001/mcp/list_tools` | 返回值含 8 个新工具名 |

## User Feedback & Changes

### Feedback Log
<!-- Users write BMAD-ANNO callouts below -->

### Deviation Notes

**批注处理记录 (2026-04-13)**
1. **压缩算法** (User line 33, User2 line 34 — 已失效): 在原 Paradigm 1 范式下标记为 TECH 决策待定，社区调研 Claude Code 压缩方案。**本项已由 N8 Paradigm 切换消解**（Paradigm 2 无需压缩算法）。
2. **Tips 触发** (User line 38): 用户手写 [!tip]+ callout → 保存时解析。触发机制说明保留，仅 MCP 工具消费方式从"预组装注入"改为"AI 按需调用 extract_tips"。
3. **errors 触发** (User line 43): AI 对话自动检测 → record_error MCP。保留。
4. **Edge 触发** (User line 48): 改为 /edge_discuss → frontmatter relationships[]。保留，MCP 工具消费方式从"预组装注入"改为"AI 按需调用 get_relationships"。
5. **N3: 自动触发确认** (User line 108): ✅ 拉出新节点时，如果两端概念之间存在关系，可以自动触发 `/edge_discuss` 讨论（非强制，用户可跳过）。error 检测在 Claudian 对话流程中由 AI 自动检测并调用 `record_error` MCP。保留。
6. **N8: Paradigm 彻底切换** (2026-04-13): 用户批注 line 33/34 的压缩算法问题引出更深层议题——整个 Paradigm 1 方向在社区已 ABANDONED。经 3 轮并行 Agent 调研（gitee Java 重实现 + NanmiCoder TS + Claudian 源码 + 5 Paradigm 对比 + backend MCP 审计）确认：
   - Opus 1M + Anthropic `compact_20260112` API 让"后端压缩"失去必要性
   - Claudian 代码零压缩（依赖 Claude API）
   - Paradigm 1（预组装+压缩）在社区已 ABANDONED，被 RAG 和 Tool-based 全面替代
   - Canvas 的 Mode D 架构本身就是 Paradigm 2
   故 Story 1.3 从"组装化"重写为"工具化"。删除 DialogContextService / 压缩算法 / token 预算。新增 8 个按需 MCP 工具。
   压缩算法原 TECH 决策 `[DECISION-TECH-PENDING: context-assembly/compression-algorithm]` 闭合为 `[DECISION-CONFIRMED: context-assembly-paradigm]` = Paradigm 2 工具化，不再需要压缩算法。
   用户决策（Plan Mode 对话）：
   - Q: 是否继续 Paradigm 1 压缩？→ ❌ "搞个屁的压缩"
   - Q: 重写方向？→ ✅ A. Paradigm 2 工具化
   - Q: Apache 2.0 attribution？→ ✅ A. 引用但不抄代码
7. **遗留 compression.py 不动** (2026-04-13): `backend/lib/agentic_rag/compression.py`（Story 2.10 产出）服务 RAG pipeline，与本 Story 无关，保留不动。
8. **Story 1.2 下游变更** (2026-04-13): 主消费者从 DialogContextService 改为 wikilink_tools.py 的 `get_neighbors` 工具。接口 `get_neighbors(note_path, hop=2)` 保持不变。

9. **架构定位 + 社区启发问答响应** (2026-04-13): 响应 line 46 用户批注（检索定位 / 笔记爆量高效策略 / Karpathy 和 Graphsify 的 Obsidian 启发 3 问题）。批注下方已插入简答 `[A 2026-04-13]`，完整调研（3 并行 Agent + WebSearch + codebase-memory）沉淀至 [[karpathy-graphify-insights-2026-04-13|📚 完整研究报告]]。关键结论：(a) 本 Story 的 8 工具纯属笔记检索方向 (b) Karpathy `llm-wiki` 架构与 Graphify MCP 4 工具已成 2026 社区共识，验证 Paradigm 2 方向正确 (c) 用户原拼 "Graphsify" 实为 "Graphify"（`safishamsi/graphify`，Karpathy Threads 点名），项目内部同名组件需警惕命名冲突 (d) 未来 5 条可操作借鉴（P0-P2），最高优先级是新增第 9 个 MCP 工具 `read_index()` 作为 AI 冷启动入口，对抗 Paradigm 2 退化成 RAG-lite 的坑。

10. **N10: 2-hop 降级适用性** (2026-04-13): 响应 line 52 批注。结论：✅ 仍需保留，**定位变了**（从"IPC 容量约束"→"AI 自主决策的性能保障"）。证据：后端 FastAPI+Neo4j+LanceDB 保留不变，MCP 工具 `get_neighbors` 按需调用，Opus 1M 仍有窗压力 + < 200ms SLA。详见 [[karpathy-graphify-insights-2026-04-13|📚]] §N1。

11. **N11: Canvas 版 index.md 规范** (2026-04-13): 响应 line 55 批注（含 2 并行 Agent deep explore 要求）。2 Agent 已跑：Karpathy gist 原样核查 + Canvas 白板结构深挖。结论：不是用户猜的 1（纯节点索引不够）也不是 2（批注全文不该放 index），而是"catalog + mastery 分组 + exam 历史 + annotations 热点统计"融合版。核心定位"你现在该刷哪几个节点"。完整规范（frontmatter、section 排序、更新机制、MCP `read_index()` 工具定义、drift 检测、开放问题 4 条）见新建文档 [[canvas-index-md-spec-v1|📐 Canvas index.md 规范 v1]]。

12. **N12: 跨学科通用 tag 体系** (2026-04-13): 响应 line 62 批注。用户指出 `proof:`/`gotcha:` 偏 CS。调研 Matuschak / Zettelkasten / Ahrens / PARA / Anki 五大 PKM 学派，设计 4 维正交体系（`type/*` + `state/*` + `src/*` + `todo/*`）。旧 tag 裁决：`proof:` → `type/claim` + `type/example`；`gotcha:` → `state/weak`。Obsidian 原生支持，零代码改动。跨学科验证覆盖 CS/数学/文学/历史/哲学/艺术/语言/物理。详见新建文档 [[canvas-crossdiscipline-tags-v1|🏷️ 跨学科 tag 体系 v1]]。

13. **N13: Graphify 组件真相（重大修正）** (2026-04-13): 响应 line 71 批注 + research.md line 129 同款批注。深度调查（Explore Agent 扫 PRD / architecture / backend / Git log / OpenSpec / Story 3.2/3.5）确认：⚠️ **空规划 + 借用外部包**。所谓"项目内部 Graphify" = 计划集成 `graphifyy` v0.3.17 PyPI 包（即 `safishamsi/graphify` 的 Python 发行版），不是自研。PRD line 76 + 317-323 已声明，但 `backend/requirements.txt` 未添加 `graphifyy`，`backend/**/*graphify*.py` 零文件，Story 3.2/3.5 从未启动。研究文档 §3.2 "命名冲突警示" 已**作废**（改名建议 `NoteGraphIndex`/`CanvasGraphify` 撤回）。建议动作：① 更新 PRD 措辞 ② 决定 Story 3.2/3.5 排期（保留集成 vs 改用 Wikilink 图替代）。详见 [[karpathy-graphify-insights-2026-04-13|📚]] §3.2（2026-04-13 修正版）。

## Dev Agent Record

### Agent Model Used
(to be filled by Dev agent)

### Debug Log References

### Completion Notes List

### File List
