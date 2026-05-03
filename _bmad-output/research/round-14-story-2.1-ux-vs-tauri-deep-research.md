---
type: deep-research-prompt
decision_id: epic-2/story-2.1-vs-tauri-ux-alignment
date: 2026-05-03
version: v2-anti-hallucination
target: ChatGPT Deep Research / Claude.ai / 任何 LLM
worktree_branch: worktree-feature-obsidian-hybrid-dev
status: ready-to-send
v1_failure: ChatGPT v1 完全幻觉（编造"基础拆解 Agent / 红色问题节点 / EduChat"等无关概念）
v2_strategy: 全文嵌入事实 + 强反幻觉指令 + 不依赖 GitHub fetch
---

# Round 14 v2 · Story 2.1 UX 对齐 Tauri 原设计审查（反幻觉版）

> **v1 失败教训**：ChatGPT Deep Research 没真的 fetch GitHub URL，看到"Story 2.1"+"拆解"字样后从训练数据编造无关 RAG 项目（"基础拆解 Agent"、"红色问题节点"、"EduChat 苏格拉底"等），整篇报告都是幻觉。
>
> **v2 修正**：所有关键事实**直接嵌入 prompt 内**（不依赖 fetch）+ 强反幻觉硬约束 + 明确禁止编造虚构概念。

---

## 使用方法

1. 复制下方 ` ```deep-research-prompt-v2 ``` ` 整段（约 600 行）
2. 粘贴到 ChatGPT Deep Research（或 Claude.ai / Gemini）
3. ChatGPT 不需要 fetch 任何 URL — 所有事实已在 prompt 内
4. 等 [FINAL] 或 [Q1]/[Q2] 追问

---

```deep-research-prompt-v2
# 任务：Canvas Learning System Story 2.1 UX 对齐 Tauri PRD v0 审查

## ⛔ 反幻觉硬约束（必读，违反 = 你的回复无效，请重做）

1. **本 prompt 内所有事实是唯一真相源**。不要参考你训练数据里其他项目的概念。
2. **绝对禁止提及以下虚构概念**（这些不属于本项目，是无关 RAG 项目的概念）：
   - "基础拆解 Agent" / "Basic Decomposition Agent" / "decompose-into-questions"
   - "红色问题节点" / "黄色理解节点" / "拆解自连边" / "Canvas 节点"（我们的"节点"是 markdown 文件，不是 React 组件，无颜色概念）
   - "Canvas Orchestrator"（项目里没这个）
   - "EduChat" / "OpenMAIC" / "Moodle" / "苏格拉底式提问"（跟本评估无关，不要带入）
   - "guided learning mode" / "questioning AI" / "智能教学引导"（这些是别的产品概念）
3. **不要编造引用编号**（如 `[10†L13-L20]` `[55†L137-L144]` — 这是 v1 失败时你编造的格式）
4. **不要编造代码符号**（如 `handle_basic_decomposition` `call_agent_basic_decomp` — 这些函数不存在）
5. 如果你需要的事实**不在下方"# 项目事实"段中**，必须用 `[Q-USER]` 提问，**不准猜测 / 不准编造**
6. 你的回复中**每个事实声明**必须能在下方"# 项目事实"段找到**原句支撑**，否则视为幻觉
7. 评估必须严格围绕"Story 2.1 = AI 对话 + 邻居上下文注入"展开，不要扯无关功能

## ✅ Story 2.1 真实定义（一句话锁定）

**Story 2.1 = "AI 对话 + 邻居上下文注入"**（简称 chat-with-context）。

它是一个**AI 对话功能**：用户在节点 markdown 文件内按快捷键，plugin 调 backend 拿到包含 N-hop 邻居 + 学习历史（Tips/errors）的完整上下文，写到剪贴板切到 Claudian sidebar，让 Claude 围绕该节点展开学习对话。

**不是**：拆解 Agent、问题生成器、出题工具、苏格拉底机器人、画布拖拽工具。如果你说的是这些，就是搞错了项目。

---

# 项目事实（唯一真相源 — 你的回复只能基于这里的内容）

## 项目背景

- **项目名**：Canvas Learning System
- **GitHub**：https://github.com/oinani0721/canvas-learning-system （Public）
- **原架构（已 archived）**：Tauri v0 — React + ReactFlow + Rust backend，节点是 React 可视化组件
- **现架构**：Obsidian Hybrid — Obsidian plugin（TS）+ Claudian sidebar（Claude Code CLI 内嵌）+ FastAPI backend（Python + Neo4j + LanceDB + Ollama bge-m3）
- **节点（concept）**：在 Obsidian 内是 `节点/<concept>.md` markdown 文件（扁平池），**不是**任何可视化组件
- **白板（whiteboard）**：`原白板/<board>.md` markdown 文件
- **节点间关系**：通过 Obsidian wikilink 语法 `[[X]]` + frontmatter `relationships[]` 字段
- **LLM 调用**：通过 Mode D — Claude Code CLI（用户订阅，Claudian sidebar 内嵌执行 Skills），**zero backend LLM cost**
- **降级原因**：Tauri+React 工程复杂度过高 + Obsidian 复用社区生态降本
- **设计哲学**：用户**学习效果守恒**（Effect Conservation） — 不强求 UI 1:1，但学习闭环不能丢

## Tauri v0 PRD 原始 FR-CONV 表（PRD v0 line 744-758 全文 — 不要编造其他 FR）

```
| ID | 功能需求 |
|----|---------|
| FR-CONV-01 | 用户点击任意节点可以打开该节点的独立 AI 对话窗口 |
| FR-CONV-02 | 每个节点拥有独立的对话历史，跨 session 持久化 |
| FR-CONV-03 | AI 对话时自动注入用户在该节点及其 1-hop 邻居节点的学习上下文（Tips、错误记录、Edge 理由等） |
| FR-CONV-04 | 用户可以在对话中使用 /命令 调用已注册的 Agent 技能 |
| FR-CONV-05 | 用户可以在对话窗口中标记 Tips（关键知识点） |
| FR-CONV-06 | 系统自动从对话中提取、分类并归档用户的错误（4 主类：破题错误/推理谬误/知识点缺失/似懂非懂） |
| FR-CONV-07 | 对话消息按时间进行三层归档（完整保留→摘要+提取→仅提取） |
| FR-CONV-08 | 用户可以选取对话中的文字拖出为新的知识节点 |
| FR-CONV-09 | 用户切换节点时，前一个节点的 AI 回答在后台继续生成（不取消） |
| FR-CONV-10 | 用户切换到新节点对话时，系统通过 Edge 语义检索相关的前序节点对话摘要，自动注入新节点对话上下文（Phase 2） |
| FR-CONV-11 | 系统按三层策略管理对话上下文窗口：Tier 1 全量注入（当前节点完整对话历史）+ Tier 2 摘要注入（1-hop 邻居节点对话摘要）+ Tier 3 按需检索（远端节点按需检索）。当节点拥有超过 5 个（可配置）1-hop 邻居时，按查询相关性、交互时间和精通度缺口优先排序注入，总量受 ACP token 预算约束 |
| FR-CONV-12 | 用户可通过 /resume 命令查看和切换节点对话 session |
| FR-CONV-13 | Agent 上下文窗口压缩发生时，系统保留关键学习数据（Tips、错误记录、精通度状态） |
```

**FR-AGENT-02**（PRD v0 line 870）：Agent 对话支持 per-node 独立 Session（createSession / resumeSession），切换节点时保持独立对话上下文。

**FR-TRACE-02**（PRD v0 line 836）：学习档案展示用户标注的所有 Tips，可展开查看来源对话上下文。

### Tauri v0 视觉示例（PRD line 433 原文）

> 节点详情面板顶部通过颜色和描述性标签显示掌握状态（如"需要加强"/"基本掌握"），下方写着"建议复习 admissibility 相关内容"。面板上有"启动单节点考察"按钮，可直接对该节点发起专项考察。接着是他之前标注的 3 条 Tips—— 每条 Tips 都可以展开看当时的对话上下文。

## Obsidian Story 2.1 v1.0 实施现状（2026-05-02 ship review）

### 真实触发流程（按时间顺序）

```
1. 用户打开 节点/<concept>.md（必须先打开节点页，无视觉触发器）
2. 用户按 Cmd+Shift+E（plugin 命令名: canvas:chat-with-context）
3. plugin 检查 active file 是否在 节点/ 路径（不在则拒绝并提示）
4. plugin 收集 current_note：path + 正文 + frontmatter
5. plugin 发 POST /api/v1/chat/enrich-context
   Body: { node_path, current_note_content, current_note_frontmatter, max_hops: 2, token_budget: null }
6. backend wikilink_context_service.enrich_from_wikilink_graph()：
   - 调 wikilink_graph_service.get_neighbors(node_path, hop=2)（NetworkX BFS, 200ms 超时）
   - 返回 List[NeighborNote]（每个含 title/path/hop_distance/frontmatter）
   - 转换为 List[WikilinkNeighborContext]（加 relationship_type 提取 — 从 frontmatter relationships[] 中找 target 含 target_slug 的）
7. backend chat_context_assembler.assemble_context()：
   - 5 优先级填充 token 预算（默认 8192，env CHAT_CONTEXT_TOKEN_BUDGET 可配）：
     P1: 当前笔记全文（最高，不可压缩）
     P2: 1-hop frontmatter + Tips + errors
     P3: 1-hop content_summary
     P4: 2-hop frontmatter
     P5: 2-hop content_summary
   - tiktoken cl100k_base 计 token
   - LaTeX 公式（$$...$$ / $...$）+ 代码块 ```...``` 视为 atomic 块（整块保留或整块丢弃）
   - 排序：按 hop_distance 升序 + 字段类型优先级（frontmatter > Tips > content_summary）
8. backend 返回 EnrichContextResponse: 
   { enriched_context: str, used_tokens: int, budget: int, truncated: bool, sections_included: [...], 
     neighbors_count: int, degraded: bool, degraded_reason: str|null, enrichment_elapsed_ms: float }
9. plugin 收到响应，组装最终 prompt:
   "/chat-with-context\n\n{enriched_context}\n\n---\n请基于以上上下文回答我的问题。问题：（在这里输入）"
10. plugin 写剪贴板（navigator.clipboard.writeText）+ Notice "已组装 backend RAG 上下文 X.XKB / Y 邻居 / Z/8192 tokens"
11. plugin 调 app.commands.executeCommandById("claudian:open-view") 切到 Claudian sidebar
12. 用户在 Claudian Cmd+V 粘贴
13. Claudian 加载 chat-with-context Skill (canvas-vault/.claude/skills/chat-with-context/SKILL.md)
14. Claude 解析 sections → 给开场白（节点速览 + 关键邻居 + 可问方向）
15. 用户提问 → Claude 用注入的完整上下文 + 邻居关系作答
```

### Story 2.1 实际代码核心摘要

`backend/app/services/wikilink_context_service.py`（180 行）：

```python
@dataclass
class WikilinkNeighborContext:
    slug: str
    path: str
    hop_distance: int
    relationship_type: str | None = None
    frontmatter: dict[str, Any] = field(default_factory=dict)
    content_summary: str | None = None

@dataclass
class EnrichmentResult:
    neighbors: list[WikilinkNeighborContext] = field(default_factory=list)
    degraded: bool = False
    degraded_reason: str | None = None  # "wikilink_graph_not_built" / "traversal_timeout" / "unexpected_error: <Type>"
    elapsed_ms: float = 0.0

async def enrich_from_wikilink_graph(
    node_path: str,
    max_hops: int = 2,           # 默认 2-hop（注意：比 PRD v0 FR-CONV-03 的 1-hop 更广）
    timeout_ms: int = 200,       # 200ms 超时（NFR-PERF）
    graph_service: WikilinkGraphService | None = None,
) -> EnrichmentResult:
    # 调 wikilink_graph_service.get_neighbors → 转 WikilinkNeighborContext
    # 异常 / 图未 build / 超时 → degraded=True + 空 neighbors（不抛）
```

`backend/app/services/chat_context_assembler.py`（240 行）：

```python
class ChatContextAssembler:
    def __init__(self, token_budget: int | None = None, encoding_name: str = "cl100k_base"):
        ...
    def compress_content(self, text: str, max_tokens: int) -> str:
        # 按句子边界压缩，atomic 块（$$...$$ / $...$ / ```...```) 整块保留或丢弃
    def assemble_context(self, current_note, neighbors, token_budget=None) -> AssembledContext:
        # 5 优先级填充（不按"相关性 / 交互时间 / 精通度缺口"排序，仅按 hop + 字段类型）
        # 返回 AssembledContext(text, used_tokens, budget, truncated, sections_included)
```

`frontend/obsidian-plugin/src/main.ts`（handleChatWithContext +131 行）：

```typescript
private async handleChatWithContext() {
    // active file 检查 → 必须在 节点/ 路径
    // 读 vault.read(activeFile) + extractBodyWithoutFrontmatter
    // POST /api/v1/chat/enrich-context
    // 拿 enriched_context → 写剪贴板 + 切 Claudian
}
```

### 5 AC 实施状态

- AC #1: 2-hop wikilink 遍历 + NeighborContext ✅ 实现
- AC #2: LLM 上下文组装 + frontmatter/Tips/errors 注入 ✅
- AC #3: token 预算压缩 + LaTeX 公式 / 代码块 atomic 保护 ✅
- AC #4: LLM 首 token < 5s P95 🟡 待用户实测
- AC #5: 降级处理（图未 build / 超时 / 异常）✅

### 测试覆盖
- backend 50 单元测试 / plugin 98 单元测试，全 green
- 集成测试 / 性能测试推迟到 Task 5.4

---

# 关键差异表（待你评估每条是否"使用层面等价" — 严格基于上方事实）

| 维度 | Tauri v0 原设计（FR-XXX 引用） | Obsidian Story 2.1 实施 | 用户感知差异 |
|---|---|---|---|
| 触发 | FR-CONV-01: **点击任意节点**（视觉一键）| Cmd+Shift+E hotkey + **必须先打开节点 .md 文件** | 步数 1 → 4 |
| 对话窗口 | FR-CONV-01: **节点的独立 AI 对话窗口**（per-node 视觉聚焦）| Claudian sidebar（**全局共享 sidebar，不是节点旁的窗口**）| 视觉聚焦丢失？|
| 对话历史持久化 | FR-CONV-02: **每个节点拥有独立对话历史，跨 session 持久化** | **未实现** — 每次 Cmd+Shift+E 重新组装 context（不含 prior 对话历史） | 重大丢失？|
| 邻居 hop | FR-CONV-03: **1-hop** | **2-hop**（更广） | 上下文更广 |
| 上下文注入内容 | FR-CONV-03: Tips + 错误记录 + Edge 理由 | frontmatter + Tips + errors + relationship_type（**无 Edge 理由独立字段**，仅有 wikilink 隐含关系）| 信息有损？|
| 三层上下文管理 | FR-CONV-11: Tier 1 全量历史 + Tier 2 邻居摘要 + Tier 3 按需检索 + **按相关性/时间/精通度缺口排序** | 5 优先级 token 预算（hop_distance + 字段类型排序，**无相关性 / 时间 / 精通度排序**）| 邻居选择有偏？|
| Edge 语义检索前序对话 | FR-CONV-10: Phase 2 计划 | **未实施**（依赖未启动的 Story 2.6 对话归档 + Graphiti） | 推迟可接受？|
| Per-node 独立 Session | FR-AGENT-02: createSession / resumeSession 持久化 | **未实施** | 重大丢失？|
| Tips 标记 | FR-CONV-05: 用户在对话窗口中标记 Tips | **未实施** | 推迟可接受？|
| 错误自动归档 | FR-CONV-06: 4 主类自动提取分类 | **未实施**（依赖 Story 2.5）| 推迟可接受？|
| 对话三层归档 | FR-CONV-07: 完整保留 → 摘要+提取 → 仅提取 | **未实施**（依赖 Story 2.6）| 推迟可接受？|
| 节点视觉聚焦 | PRD line 433: 节点旁面板含 mastery 颜色 + Tips 列表 + 单节点考察按钮 | mastery 字段散在节点 markdown frontmatter；Tips 散在节点正文 callout；考察散在 Cmd+P 命令面板 | 视觉散布认知负担？|
| 后台流式生成 | FR-CONV-09: 切节点时前一节点 AI 回答后台继续生成 | **未实施** — Cmd+Shift+E 完成后剪贴板切 Claudian，无后台生成概念 | 重大丢失？|

---

# 待你回答的具体问题（请严格基于上方事实，不准编造）

## Q1: 触发交互的"学习效果守恒"评估
Tauri v0 是"点击节点即弹独立对话窗口"（1 步），Obsidian Story 2.1 是"打开节点 md → Cmd+Shift+E → 剪贴板 → 切 Claudian → Cmd+V 粘贴 → 提问"（5 步）。

请评估：
- 这是否破坏 PRD v0 的"learning effect conservation"原则？
- 学习心流（study flow）研究上有多大影响？
- 步数从 1 → 5 是否会让用户**忘记使用**这个功能（学习闭环断裂）？

## Q2: per-node 对话历史持久化的丢失（FR-CONV-02 / FR-AGENT-02）
Tauri v0 是 createSession/resumeSession 持久化每节点的对话历史（用户 3 天后回到 Eigenvalues 节点，能 resume 之前对话）；Obsidian Story 2.1 每次 Cmd+Shift+E 都是**新对话**（context 含静态 Tips/errors 但**不含 prior 对话历史**）。

请评估：
- 这对**复习时回到旧节点连贯思考**的用户体验影响多大？
- 是否致命到 Story 2.1 不应被标 review until 这个补足？
- 还是可以推迟到 Story 3.7 dialog-pullout-node 实施？

## Q3: 三层 Tier vs 5 优先级排序（FR-CONV-11）
FR-CONV-11 强调按"**查询相关性 + 交互时间 + 精通度缺口**"排序邻居（>5 邻居时），但 Story 2.1 实施仅按"hop_distance + 字段类型"排序。

请评估：
- 是否会导致 token 预算用在不重要邻居上？
- 是否需要 v1.1 加上"相关性 / 时间 / 精通度"三维排序？
- 还是 hop + 字段类型已经足够近似？

## Q4: 节点视觉聚焦丢失
Tauri v0 节点旁面板有 mastery 颜色 + Tips 列表 + 单节点考察按钮（视觉一站式）；Obsidian Story 2.1 后这些散在 frontmatter / 命令面板 / Dashboard.md。

请评估：
- 用户**主动查找认知负担**是否过高？
- 是否需要 Obsidian plugin 加 "sidebar widget"（节点级 mastery + Tips 视图）？
- 还是 Obsidian Properties 渲染 frontmatter 字段已够用？

## Q5: 缺失的 4 个 FR 是否阻塞 Story 2.1 review
缺失：FR-CONV-02（per-node 持久化）/ FR-CONV-05（标记 Tips）/ FR-CONV-06（错误自动归档）/ FR-CONV-07（三层归档）/ FR-CONV-09（后台流式）/ FR-CONV-10（跨节点 Edge 检索）/ FR-AGENT-02（session）/ FR-TRACE-02（Tips 溯源）

请评估：
- 这些是 OK 推迟（每个对应未启动的 Story）？
- 还是 Story 2.1 不应该被标 review until 至少有 stub？
- 哪些是"不补会让 Story 2.1 实质偏离 Tauri 设计"的硬阻塞？

## Q6: 整体判断
请给出三选一最终判断：
- (A) **使用层面等价** — Story 2.1 守住了学习效果守恒，可以 review 通过
- (B) **部分等价 + N 处需补强** — 列出哪些必须 v1.1 加上才能通过
- (C) **已实质偏离 PRD v0** — Story 2.1 应回炉重做

并给出基于学习心流 / 学习记忆持久化 / 用户研究的**学术或工业证据**支撑（如 Karpicke 2011 retrieval practice / Sweller cognitive load / Notion-Obsidian 用户研究）。**不要编造证据来源，如果你没有具体证据请说"无具体证据"**。

---

## ⭐ Q7: 三种检索路径技术对比（用户审核重点 — 来自验收单批注）

### 用户原话（2026-05-03 批注 Story 2.1 验收单）

> 这里的上下文注入，你是学习 Karpathy 的 wiki 方式通过双向链接方式读取了链接的文档，然后同时后端的 Graphiti 也是有把前端 md 文件之间联系构建了关系图谱然后读取，那么我要明确你这里用到了什么 RAG，以及和 Claude Code 自己 Grep 文件来读，哪一个是更优的，我需要你在技术角度来 deep explore 这一点。

### 项目内三种检索路径现状（事实嵌入 — 来自 backend 代码 + Round-13 决策）

**路径 A · Wikilink BFS（Karpathy 风格）— Story 2.1 当前实施的唯一路径**
- 实现：`backend/app/services/wikilink_graph_service.py` (NetworkX BFS N-hop, 200ms 超时)
- 数据源：obsidiantools 解析 vault md 文件的 `[[X]]` wikilink 语法 → 内存图
- 调用方：Story 2.1 `wikilink_context_service.enrich_from_wikilink_graph` → `get_neighbors(node_path, hop=2)`
- 特点：零成本 / 显式关系 / 静态结构 / 启动 < 2s / 遍历 < 200ms

**路径 B · Graphiti 时序图（Neo4j 知识图谱）— 项目内已集成但 Story 2.1 未用**
- 实现：`graphiti-core v0.28.2` + `backend/app/clients/graphiti_client.py`
- 三个未通电的 API：`search_facts` / `search_nodes` / `search_communities`
- `valid_at` / `invalid_at` 时序追踪能力（用户 mastery 演化、错误修正历史）
- 计划用法：Round-13 决策 — 仅对**会变化的属性**（mastery_score / understanding / last_reviewed）通过 `add_episode` 写入；md frontmatter 是"声明式快照"，Graphiti 是"事件流"，单向同步（永不反向）

**路径 C · Claude Code Grep + Read（Mode D Skill 内置工具）— chat-with-context Skill 允许**
- 实现：Claudian sidebar 内的 Claude Code CLI 自带 `Read / Glob / Grep` 工具
- Skill 配置：`canvas-vault/.claude/skills/chat-with-context/SKILL.md` 的 `allowed-tools: [Read, Glob, Grep]`
- 调用模式：用户粘贴 enriched_context 后 Claude 可在对话中**主动 Grep / Read** 邻居节点 md 获取更多细节
- 特点：lazy 检索 / 用户语义驱动 / 不限定 hop / 但每次调用消耗 tokens

### Round-12/13 已锁定的决策结论（项目历史）

来源：`_bmad-output/research/round-13-wikilink-vs-graphiti-five-questions-answer-2026-04-29.md`

| Q | 结论 |
|---|---|
| Q1 谁更高效精确 | **不是替代关系，是分工** — Wikilink 做骨架（零成本 + 显式），Graphiti 做时序补充（语义 + 演化） |
| Q5 双引擎并用 | **✅ 2026 社区共识** — 三层分层检索（Wikilink → Graphiti → LanceDB）+ RRF 融合 |
| Q3 md 属性进 Graphiti | 仅时序属性（mastery / understanding / last_reviewed），单向 md → Graphiti，永不反向 |

**关键认知差距**：Round-13 决策"三层 RRF 融合"，但 Story 2.1 实施**只用了路径 A wikilink BFS**，未集成 Graphiti（路径 B）也未让 Skill 主动 Grep（路径 C）。

### 待你（ChatGPT）评估的具体问题

**Q7-1 · 三路径的技术权衡**：
对比下表中每条维度，给出技术优劣判断（**仅基于上方事实，不准引用其他项目**）：

| 维度 | A. Wikilink BFS | B. Graphiti 时序 | C. Claude Grep |
|---|---|---|---|
| 检索精度（相关性）| ?  | ? | ? |
| 时序感知（mastery 演化）| ? | ? | ? |
| 调用延迟（< 200ms / < 5s / ?）| ? | ? | ? |
| Token 成本（每次对话）| ? | ? | ? |
| 实现复杂度 | ? | ? | ? |
| 冷启动时间 | ? | ? | ? |
| 数据一致性风险（双源真理）| ? | ? | ? |
| 用户场景适配（学习对话 vs 复习查史）| ? | ? | ? |

**Q7-2 · Story 2.1 现状（仅路径 A）vs Round-13 决策（三层 RRF）的差距**：
- Story 2.1 v1.0 是否实质偏离 Round-13 决策？
- 如果偏离，是渐进可接受（先 wikilink 再加 Graphiti）还是必须立即补 Graphiti？

**Q7-3 · Claude Grep（路径 C）的角色定位**：
- chat-with-context Skill 已经允许 Claude 主动 Grep — 这是否实质上提供了"延迟检索的兜底"？
- 还是说"显式 backend 检索（路径 A/B）"vs "Claude 自主 Grep（路径 C）"在工程上是两种哲学（pre-fetch vs lazy-fetch），各有适用场景？
- 哪种适合 Canvas 学习对话场景（学习者每次提问的相关性变化大）？

**Q7-4 · 三选一推荐**：
对于 Story 2.1 的 v1.x 演进路线，给出三选一推荐：
- (A) **保持 wikilink-only**（当前），Graphiti 推迟到 Story 2.5/2.6（错误归档 / 对话归档）
- (B) **立即加 Graphiti search_facts**（v1.1 实施，激活 Round-13 决策的三层 RRF 第二层）
- (C) **依赖 Claude Grep 兜底**（让 Skill 自主 Grep 替代部分 Graphiti 功能，简化 backend）

请给出**学术或工业证据**（如 Karpathy second brain wikilink 论文 / Zep Graphiti 案例 / RAG vs lazy retrieval benchmark / Aider Cursor 上下文管理）。**不要编造证据来源，如果你没有具体证据请说"无具体证据"**。

---

# 已知约束（请勿建议这些方案 — 不可逆）

- ❌ Obsidian 无法实现"点击节点弹独立窗口"（Obsidian 是 markdown 编辑器，节点 = .md 文件，无 React 节点的视觉概念）
- ❌ 不可改用 Tauri / Electron / 自建 React UI（已 archived 不可逆）
- ❌ 不可改 Mode D（Claude Code CLI + Claudian sidebar 是 architecture.md:113 锁定的，零 backend LLM 成本架构）
- ❌ Per-node Session 持久化需要 Story 3.7 dialog-pullout-node 实施（未启动）
- ❌ Edge 语义检索需要 Story 2.6 对话归档 + Graphiti（未启动）
- ❌ 不要建议"重构 OpenSpec / BMAD"（项目流程基石）

---

# 应答格式

## 如果信息充分 → 直接 [FINAL]：

```
[FINAL]

## Q1 触发交互评估
（基于事实的具体回答 — 不要扯无关概念）

## Q2 持久化丢失评估
...

## Q3 三层 Tier vs 5 优先级
...

## Q4 视觉聚焦
...

## Q5 缺失 FR 是否阻塞
...

## Q6 整体判断 (A/B/C)
（三选一 + 学术/工业证据，不能编造证据来源）

## Q7 三种检索路径技术对比（用户审核重点）
- Q7-1 三路径权衡表（A wikilink / B Graphiti / C Claude Grep 各 8 维度）
- Q7-2 Story 2.1 vs Round-13 决策的差距（是否实质偏离）
- Q7-3 Claude Grep 的角色（lazy retrieval vs pre-fetch RAG）
- Q7-4 三选一推荐：保持 wikilink-only / 立即加 Graphiti / 依赖 Claude Grep 兜底
- 必须给学术或工业证据，不能编造证据来源

## Story 2.1 处置建议
- 是否继续 review 通过 / 回炉 / 加 stub 后通过
- 必须在 Epic 2 完成前补 stub 的 FR 列表

## 实施注意事项（≤3 条）
...
```

## 如果信息不足 → 用 [Q-USER] 问用户具体追加事实，不要编造。

---

# 你的回答自检（提交前必跑）

提交前请检查你的回复：

- [ ] 没有提及"基础拆解 Agent / Basic Decomposition Agent / decompose"等无关概念
- [ ] 没有提及"红色问题节点 / 黄色理解节点 / 拆解自连边"
- [ ] 没有提及 EduChat / OpenMAIC / Moodle（除非是评估"用户研究"时引用具体论文）
- [ ] 没有编造引用编号 `[N†L...-L...]`
- [ ] 没有编造代码符号（`handle_basic_decomposition` 等本项目没有的函数）
- [ ] 每个事实声明能在上方"# 项目事实"段找到原句支撑
- [ ] 评估对象始终是"Story 2.1 = AI 对话 + 邻居上下文注入"，不是其他任何虚构功能

如果任何一项 ❌，请重做你的回复。
```

---

## 文档状态

- **创建时间**：2026-05-03
- **版本**：v2 反幻觉版（替换 v1）
- **关键改进**：全文嵌入事实 + 反幻觉硬约束 + 自检清单
- **预期归档**：完成后 → Graphiti `canvas-dev` group + 决策内容写回此文档"## 最终决定" section
