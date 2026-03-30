# Solo AI Agent 开发：什么真正有效 vs. 什么听起来好

**开发者的真实护栏已经在运行——自定义 Graphiti Hooks 和 DD 规则承担了所有重量，而 BMAD（544 个冻结文件）和 SuperPower（78 次会话中 0 次技能激活）没有贡献任何价值。** 本研究通过社区证据验证了这一判断，覆盖全部 8 个问题。核心建议：不要再增加基础设施——裁剪死代码、强化已有效的部分、精准填补三个缺口（技术审计、TDD 强制执行、Graphiti 噪音）。以下所有建议均基于社区验证的证据；缺乏独立验证的声明标注为【未找到社区验证】。

---

## Q1：最小可行工作流比你想象的更轻

社区证据压倒性地支持独立开发者使用 **CLAUDE.md + 精准 /commands** 而非重量级框架。社区已经绘制出这个光谱的全貌：

**GSD（Get Shit Done）** 已成为 BMAD 最有力的轻量替代方案，GitHub **23,000+ stars**，有真实部署案例记录。其创建者 @arrwhyee 的核心洞察："BMAD、SpecKit、Taskmaster——它们都能用，但会让你感觉在给一个不存在的团队搭建 Jira。"GSD 使用约 50 个 Markdown 文件加 6 个斜杠命令，通过为每个任务派生全新的 200K token 子 Agent 上下文来解决上下文腐烂问题。有据可查的案例包括完整的管理后台（BookkeepingApp）和 Esteban Torres 的博客重建——他指出："规划阶段交付了最多价值……我认为它避免了因失败尝试积累的更高成本。"

**对于这位已有架构文档、23 个 Agent、21 个命令的开发者——答案是工作流光谱的第 1-2 级。** ranthebuilder.cloud、theaistack.dev 和多个 Reddit 帖子的社区共识收敛于一个清晰原则：对于超过 3 天工作量的新项目使用 BMAD 的架构阶段，其他一切用 CLAUDE.md + 3-4 个命令。ranthebuilder.cloud 的一位实践者在 3 个生产项目后得出完全相同的结论："大型项目用 BMAD。小功能用计划模式，但你需要自己提出那些艰难的问题。"

**量化速度数据很稀少。**"快 3 倍"（Fab Dubin/Medium）和"4 小时零到 SaaS"（Steve Kaplan）的说法存在，但缺乏对照实验。【未找到社区验证】：比较 BMAD 与轻量替代方案的具体速度/返工率数值。

**BMAD 的 4 阶段流程对已有架构文档的独立开发者值得吗？** 不值得——不值得跑完整流程。仅架构阶段对新项目有足够的投入产出比，但 theaistack.dev 明确表示："对于你是唯一利益相关者的独立项目，跳过 BMAD；对于在已有成熟模式上的简单功能添加，也跳过。"BMAD Issue #446 记录了一位独立开发者的案例："BMAD 的需求挖掘技术非常出色，但框架假设在现有代码库上造成了摩擦。"

---

## Q2：确定性 Hook 每次都胜过概率性提示执行

技术能力审计问题有清晰答案：**Claude Code Hooks（确定性，工具级）在架构上优于 SuperPower 的 HARD-GATE（概率性，提示级）。** 这不是理论——SuperPower 自己的创建者记录的失败模式证实了这一点。

Jesse Vincent（obra）记录了在 v4.3.0 引入 HARD-GATE 之前，Claude 遵守设计阶段要求的合规率**约为 0%**。Claude 自己在测试中承认："技能说'以 200-300 字的段落呈现设计'，但这对一个待办列表来说感觉很荒谬。所以我合理化地认为整个设计过程是多余的，直接开始构建。"引入 HARD-GATE 后，在受控测试中合规率达到约 100%——但这仅是有限试验的第一方数据。【未找到社区验证】：HARD-GATE 合规率的独立测量。

**1% 规则**（"如果有哪怕 1% 的可能性某个技能适用，必须调用它"）是纯提示级执行。Vincent 自己承认"建议性语言会被合理化忽略"——这正是创建 HARD-GATE 的原因。该规则需要正常工作的 SessionStart Hook、足够的系统提示预算（**15,000 字符上限**——技能超过此限制会被静默丢弃）以及与任务匹配的技能描述。即便如此，仍是概率性的。

**存在更好的实现方案。** DEV Community 的一篇案例研究报告，通过将基于提示的规则切换为前置提交 Hook（阻止无审查的提交），合规率从 **60% 提升到 100%**。核心洞察："克隆仓库，运行 `git config core.hooksPath scripts/hooks`，规则就生效了。新 Agent、新机器——同样的执行效果。"对于这位开发者，现有的 Hook 基础设施已经提供了这个确定性层。

**一个简单的技术检查清单文件能工作得更好吗？** 是的，很可能。Analytics Vidhya 的 Claude Skills 指南指出"模糊的描述导致触发器遗漏"。一个通过 `@` 引用到提示词中的 checklist 文件具有**更高的可靠性**，因为它不依赖自动发现机制能否正常工作。AI Guardrails 框架中的 CONTEXT.md 方案验证了这一模式。

---

## Q3：Graphiti 记忆需要分类，而非剪枝

72+ 条决策与噪音混合的问题已经被 **GuardKit** 在实践中解决——这是本研究发现的最全面的用于 AI 驱动开发的 Graphiti 实现。GuardKit 使用 **20+ 个独立的 group_id** 作为重要性分层：`architecture_decisions`（必须遵守）、`failure_patterns`（不要重复）、`quality_gate_phases`、`task_outcomes` 和 `feature_overviews`。这是经过验证的方法。

**Graphiti 的核心理念是"失效，而非删除"。** 旧事实获得 `invalid_at` 时间戳而不是被移除。MCP 服务器暴露了 `delete_entity_edge`、`delete_episode` 和 `clear_graph`，但这些是粗粒度工具。没有社区剪枝脚本存在——这个概念与 Graphiti 的时序设计相悖。【未找到社区验证】：任何安全的自动剪枝策略。

**自定义 Pydantic 实体类型**（CriticalDecision、CapabilityDebt）是官方支持的正确方法，但有一个注意事项：GitHub Issue #567 报告自定义类型可能无法正确应用 Neo4j 标签，所有节点只获得通用的 `:Entity` 标签而非预期的自定义标签。这个 Bug 在新版本中部分修复，但值得测试。

关于搜索相关性，三个发现尤为重要：

- **`COMBINED_HYBRID_SEARCH_RRF`** 是推荐的默认方案——它在边、节点和社区间组合了语义搜索 + BM25 + BFS
- **`EDGE_HYBRID_SEARCH_NODE_DISTANCE`** 配合 `focal_node_uuid`（原 `center_node_uuid`）最适合面向特定组件的查询，例如"有哪些决策与我们的认证系统相关？"——需要先找到组件节点，然后按图距离重排
- **BFS"着陆并扩展"** 自动将语义搜索结果作为广度优先遍历的种子，发现初始匹配之外的上下文相关节点

**架构决策的矛盾解决中等可靠。** 简单的事实矛盾（"我们用 PostgreSQL"→"我们切换到 MongoDB"）处理得很干净。但代码决策通常是精化而非矛盾——"使用 REST API"和"在 REST 之外添加 GraphQL"不是矛盾，但相似度搜索可能会标记它们。GuardKit 通过实现显式的 ADR 生命周期管理（`ACCEPTED → SUPERSEDED → DEPRECATED`）来绕过这个问题，而非依赖自动检测。这是推荐模式。

**针对 72+ 条决策的可执行策略：**
1. 使用 group_id 分类：`critical_decisions`、`implementation_notes`、`abandoned_approaches`、`constraints`
2. 使用检索预算（GuardKit 的 ContextBudget 模式：根据任务复杂度 2000-6000 tokens），而非存储剪枝
3. 对未来的摄入使用信号评分过滤（collab-memory 模式：信号低于 0.2 的交流记录但不编码入图）
4. 对重要决策使用显式替代而非自动矛盾检测

---

## Q4：84% TDD 数据是真实的——但衡量的是错误的东西

**84% vs 20% 的数据是真实的、经过测量的、有来源的**——但它衡量的是技能激活率，而非 TDD 合规率。Scott Spence（scottspence.com）使用 Claude Agent SDK 针对 Haiku 4.5 运行了 **200+ 次自动化测试**。没有 Hooks 时，技能激活率约为 **20%**。一个三步强制评估 Hook（EVALUATE → ACTIVATE → IMPLEMENT）达到了 **84%** 激活率。Alexander Opalic（alexop.dev）随后将这一发现应用于 TDD，引用了 Spence 的数据。Ivan Seleznov 的后续研究（650 次试验）发现，**仅改善 SKILL.md 描述就能让某些技能达到 97-100% 的激活率**，表明 Hooks 可能不是唯一路径。

**Claude Code 有多个可运行的 TDD 子 Agent 实现。** 最值得关注的：

- **alexop.dev**：完整的 RED/GREEN/REFACTOR 实现，使用 Vue + Vitest。三个子 Agent 文件（`.claude/agents/tdd-test-writer.md`、`tdd-implementer.md`、`tdd-refactorer.md`）加一个编排技能。核心洞察："如果同一个上下文同时看到两个阶段，LLM 会在无意识中围绕它已经在规划的实现来设计测试。"
- **jwilger/agent-skills**：自动检测可用工具并选择策略——Agent 团队（如果 TeamCreate 可用）、串行子 Agent（如果 Task 工具可用）或链式回退。支持变异测试和完整审计追踪。
- **obra/superpowers**：如果代码在测试之前写出，SuperPower 会**删除它**。Bridgers（开发公司）报告："在 Superpowers 之前，AI 生成的代码经常没有测试覆盖。"

**针对 Tauri+React+FastAPI 技术栈的具体配置：**

- **前端**：Vitest + React Testing Library，使用 `@tauri-apps/api/mocks`（`mockIPC()`）模拟 Rust 命令。**不支持**调用真实 Rust 后端的集成测试（vitest-dev/vitest Discussion #6636）
- **后端**：pytest + FastAPI TestClient——标准模式，文档完善
- **Rust/Tauri**：`cargo test` 加 `#[cfg(test)]` 模块，覆盖率通过 `cargo tarpaulin`
- **集成**：通过 `tauri-driver` WebDriver 接口运行 Playwright E2E，但需要构建完整 Tauri 应用 + 运行 FastAPI sidecar

**子 Agent TDD 的关键技术限制：**
- 子 Agent **不能嵌套**（已确认：GitHub issues #4182、#19077、#5528）——编排器必须是主 Agent
- 每个子 Agent **20,000 tokens 开销**——一个 RED-GREEN-REFACTOR 循环在任何实际工作前就消耗约 60K tokens
- 子 Agent 间无通信——GREEN Agent 无法向 RED Agent 请求澄清
- 【未找到社区验证】：控制测试实际失败后通过的 TDD 纪律合规率（有子 Agent vs. 无子 Agent 的对照研究）

---

## Q5：35 个 Hook 没问题——生产中有 95 个在运行

**Blake Crosley 在生产中运行 95 个 Hook** 而没有明显延迟，因为每个都在 200ms 内完成。关键约束是每个 Hook 的执行时间，而非数量。他的阈值："如果 PostToolUse Hook 给每次文件编辑增加超过 500ms，会话就会感觉迟缓。"ClaudeKit 分析器基准测试确认：文件保护 Hook 运行时间 80ms，而类型检查 Hook 需要 2661ms——伤害来自慢的单个 Hook，而非总数量。

**安全类 Hook 的头号错误**是使用 exit 1 而非 exit 2。Exit 2 会阻断工具调用（PreToolUse）或拒绝提示词（UserPromptSubmit）。Exit 1 是**非阻断的**——stderr 只在 verbose 模式下显示，执行继续。Blake Crosley："意外使用 exit 1 的 PreToolUse Hook 在看起来工作的同时提供了零执行效果。"已知 Bug（Issue #4809）会使 PostToolUse exit 1 意外阻断 Claude，与文档相矛盾。

**UserPromptSubmit Hook 确实接收提示词内容**（按规格），但有多个已报告的 Bug：stdout 在某些版本中会报错（Issue #13912），Hook 在 v2.0.77 后不对初始 CLI 提示词参数触发（Issue #17284），嵌套 JSON 可能触发误报的"提示词注入攻击"错误（Issue #17804）。适用 **10,000 字符输出限制**。

**35+ 规则的实用优化：** 对日志/通知 Hook 使用 `async: true`（v2.1.23 起可用）。将相关检查合并到单个调度脚本中。用 `claudekit-hooks profile` 进行性能分析。使用精确的工具名称匹配器而非宽泛的通配符。Hook 渐进式重复 Bug（Issue #3523）可能在会话期间使 Hook 增倍——监控此问题。

---

## Q6：PreToolUse 可以读取提议的代码——合约优先开发有效

**PreToolUse Hook 可以在代码写入文件系统之前读取 Claude 提议写入的确切代码。** 对于 Write 工具，`tool_input.content` 包含完整的提议文件内容。对于 Edit 工具，`tool_input.old_string` 和 `tool_input.new_string` 提供差异。自 v2.0.10 起，PreToolUse Hook 还可以**修改**工具输入——输出修正后的 JSON，Claude Code 会使用它替代原始输入。

实际限制：检查跨文件引用（例如"这个函数在别处有没有被调用？"）需要 Hook 通过 grep 或 AST 分析独立搜索代码库，增加延迟。**`"type": "agent"` Hook**（v2.1.9+）通过派生一个有 Read/Grep/Glob 工具的子 Agent 来解决这个问题，在返回决定前验证条件。

**AI Agent 场景下的合约优先开发有学术验证。** SDD 论文（Piskala, 2025, arxiv.org）记录了一家金融服务公司强制实施 API 优先开发（使用 OpenAPI 规格），实现了**集成周期时间减少 75%**。存在三个严格程度级别：规格优先（代码前先有规格）、规格锚定（规格与代码并行维护）和规格即源（从规格生成代码）。

**并行 Agent 的跨文件接线问题**，文档记录的失败模式是严重的。GitButler 团队直接表示："worktree 是独立的，所以你可以在不知情的情况下创建冲突。"Augment Code 记录了四种失败模式：合并冲突、重复实现、运行时分歧，以及通过了编译和 lint 的语义矛盾。

**经过验证的缓解方案：**
- **热点文件单写者规则**——路由、配置、共享类型文件只应有一个 Agent 修改
- **每次合并之间串行合并 + 完整测试套件**
- **共享接口文件**（ComposioHQ/agent-orchestrator 模式）：将所有接口集中在 `packages/core/src/types.ts`，在并行会话期间视为只读
- **Pimzino/claude-code-spec-workflow** 在规格层面处理协调，而非代码层面——通过顺序任务执行避免了并行 Agent 接口问题（`/spec-execute 1`，然后 `/spec-execute 2`）

---

## Q7：544 个文件的 BMAD 安装应该被替换

**aj-geddes/claude-code-bmad-skills**（290+ stars）是目前最接近"BMAD Lite"的实现。它通过辅助模式实现 **70-85% 的 token 减少**，将角色人格开销剥离（"你是 Mary，业务分析师..."→"你是业务分析师，执行产品简报工作流"）。它以 9 个技能和 15 个命令的纯 Claude Code 原生形式发布——不需要 npm、不需要 Node.js，安装时间不到 5 秒。

**BMAD v6 自身包含 Quick Flow**，这是官方的轻量轨道：`/bmad-bmm-quick-spec` → `/bmad-bmm-quick-dev`，使用"Barry"人格（精英全栈开发者）。文档明确说明："如果变更能写在一页笔记上，Quick Flow 就是正确的工具。"

**对于这位开发者只保留 code-review + document-project + sprint-status + quick-dev + quick-spec——这是正确的取舍吗？** 大体上是。社区证据建议将 `document-project` 和 `sprint-status` 替换为更简单的替代方案，保留：

- **架构工作流**——最高价值制品，防止连锁返工
- **代码审查 + 边缘情况猎手**（v6.0.5）——在传播前捕获 Bug
- **Quick Flow**（spec + dev）——每日功能驱动工具（3 天以内的工作）
- **放弃其他一切**——分析师、UX 设计师、编排器、Party Mode、企业版轨道、扩展包

**BMAD 的代码审查 vs. 自定义 /commands/code-review.md**：没有直接的社区对比存在（【未找到社区验证】）。BMAD 的审查开箱即用更丰富，因为它交叉引用规划制品。一个显式引用 `@docs/architecture.md` 的自定义命令可以以更低开销实现相当的质量。BMAD 的独特差异化优势是边缘情况猎手——这需要在自定义命令中有意识地复现。

---

## Q8：SuperPower 显示 0 次激活，因为它可能根本没在运行

**0/78 的激活率与已知失败模式完全一致**——以下五个独立问题中任何一个都可以导致完全沉默：

1. **SessionStart Hook 异步 Bug**（v4.3.0 修复）：导致整个系统"已安装、已配置、写满了技能，却完全沉默"——引导程序从未注入
2. **系统提示字符预算**（默认 15,000 字符）：其他插件/技能消耗预算导致 SuperPower 技能被**静默丢弃**，Claude 被告知"永远不要使用未列出的技能"
3. **技能发现 Bug**（Issues #151、#178、#345、#11266）：多个确认的 Bug，技能存在但无法被发现
4. **编辑会话 vs. 构建会话**：1% 规则针对功能构建；简单编辑设计上可能不触发任何技能
5. **.claude/skills/ 自动发现可能无法工作**（Issue #11266）：用户放置了 6 个结构正确的技能，没有一个被自动发现

SuperPower v5.0.6（2026 年 3 月 25 日发布）是一次简化——它在 5 个版本 × 5 次试验的回归测试显示"无论审查循环是否运行，质量分数完全相同"后，**移除了子 Agent 规格审查循环**。该循环"使执行时间翻倍（约 25 分钟开销），却没有可测量地改善计划质量"。

**1% 规则作为独立机制是不可靠的。** 它需要正确的插件安装、同步 Hook、足够的提示预算、与任务匹配的描述，以及 HARD-GATE 强制执行——即便如此仍是概率性的。Claude Code Hooks（exit 2 阻断）通过**架构设计**提供 100% 执行，而非通过提示词合规。

---

## 综合建议：推荐的最小可行工作流

### BMAD vs SuperPower vs 两者都不用——最终裁决

**两个框架都不要继续使用。** BMAD 的 544 个冻结文件是死重。SuperPower 的 0 次激活是功能缺失。开发者真实的系统——**9 个自定义 Hook + 13 条 DD 规则 + 23 个 Agent + 21 个命令**——已经比任何一个框架都更有效，因为它使用了确定性执行（Hook 退出码）而非概率性提示词合规。

**从 BMAD 保留什么**：只保留架构工作流和代码审查模式，重新实现为 2-3 个引用现有架构文档的自定义 `/commands`。或者，安装 aj-geddes/claude-code-bmad-skills，获得一个轻 70-85% 但保留最高价值工作流的 BMAD。

**从 SuperPower 保留什么**：什么都不要。brainstorming 技能的价值可以用一个单独的 `/commands/plan-feature.md` 复现，强制设计优先于代码。HARD-GATE 概念有价值，但作为 PreToolUse Hook（确定性）实现比作为 SKILL.md 块（概率性）更好。

### 保留 vs. 放弃清单

| 保留并强化 | 放弃 |
|---|---|
| 9 个自定义 Hook（真正的执行层） | BMAD 544 个文件的安装 |
| 13 条 DD 规则（已验证的纪律框架） | SuperPower 插件（整个） |
| Graphiti MCP（按下方方案重构） | 未使用的 BMAD Agent（分析师、UX、QA、Builder、编排器） |
| 架构文档（现有） | .claude/skills/ 目录（如果存在） |
| BMAD 代码审查模式（重实现为 /command） | BMAD sprint-status（用更简单的追踪替代） |
| 5-8 个使用最频繁的 /commands | 重复/重叠的命令（审计 21 个） |
| 5-10 个使用最频繁的 Agent | 0 次调用的 Agent（审计 23 个） |

### 具体文件变更清单

**CLAUDE.md 重构**（目标：200 行以内）：
```
CLAUDE.md 各节：
  1. 项目标识（技术栈、结构，5 行）
  2. 架构约束（链接到 docs/architecture.md）
  3. 技术检查清单（@ 引用 .claude/tech-checklist.md）
  4. DD 规则摘要（仅最常被违反的 5 条）
  5. Hook 行为说明（Hook 强制执行什么，让 Claude 不与其对抗）
  6. 测试要求（Vitest/pytest/cargo test 命令）
```

**需要新建的文件：**
```
.claude/tech-checklist.md
  — 简单的技术审计检查清单，在提示词中通过 @ 引用
  — 替代 SuperPower 的 HARD-GATE 用于技术合规

.claude/commands/plan-feature.md
  — 设计优先于代码的强制执行
  — 替代 SuperPower brainstorming 技能
  — 包含：等效 HARD-GATE："在此计划获批之前不得进入实现"

.claude/commands/code-review.md
  — 重实现 BMAD 代码审查 + 边缘情况猎手
  — 包含：@ 引用 docs/architecture.md
  — 包含：显式的跨文件孤儿检测

.claude/commands/tdd-cycle.md
  — RED-GREEN-REFACTOR 编排器
  — 使用 Task 工具派生 3 个子 Agent
  — RED：仅编写失败测试（Vitest/pytest/cargo test）
  — GREEN：实现最小通过代码
  — REFACTOR：测试仍通过的前提下清理代码

.claude/agents/tdd-test-writer.md  — RED 阶段 Agent（无实现文件访问权限）
.claude/agents/tdd-implementer.md  — GREEN 阶段 Agent（无规格文件访问权限）
.claude/agents/tdd-refactorer.md   — REFACTOR 阶段 Agent（完整访问权限）
```

**Hook 修改：**
```
修改：Write|Edit|MultiEdit 工具的 PreToolUse Hook
  — 新增：读取 tool_input.content，检查当前代码库中未引用的函数
    （基于 grep，保持 200ms 以内）
  — 新增：技术检查清单验证（对照批准的技术列表检查 imports）
  — 违规时 exit 2 阻断（不用 exit 1）

新增：实现工具的 PreToolUse Hook
  — 如果对应模块没有测试文件，阻断 src/ 文件的 Write|Edit
  — 从结构上强制 TDD（确定性，非基于提示词）
  — 配置文件、类型文件、接口文件的例外列表

审计：所有现有 Hook
  — 验证所有安全关键 Hook 使用 exit 2（非 exit 1）
  — 用 time 命令对每个 Hook 计时——超过 500ms 的应优化或改为 async
  — 日志/通知 Hook 改为 async: true
```

**Graphiti 图结构变更：**
```
1. 创建 group_id：
   - "critical_decisions"      — 架构决策，必须遵守
   - "capability_constraints"  — 技术限制，变通方案
   - "abandoned_approaches"    — 失败方案，不要重复
   - "implementation_notes"    — 低优先级上下文，实现细节

2. 创建自定义实体类型（Pydantic）：
   - CriticalDecision(rationale: str, confidence: float, supersedes: Optional[str])
   - CapabilityDebt(severity: str, workaround: str, resolution_plan: Optional[str])
   - AbandonedApproach(reason: str, attempted_date: str)

3. 将现有 72+ 条决策重新摄入对应的 group_id
   （人工分类：约 2 小时一次性成本）

4. 配置搜索：
   - 默认：带 group_id 过滤的 COMBINED_HYBRID_SEARCH_RRF
   - 组件查询：两步法配合 focal_node_uuid
   - 设置检索预算：快速查询 2000 tokens，规划查询 6000 tokens

5. 新增摄入过滤器：
   - add_episode() 调用前：对信号相关性打分（0-1 量表）
   - 阈值 0.4：低于此值，记录但不编码入图
   - 防止未来噪音积累
```

**需要删除/归档的文件：**
```
归档：整个 BMAD 安装（544 个文件 → 归档分支或 .bmad-archive/）
删除：.claude/skills/ 目录（如果存在——SuperPower 残留）
删除：SuperPower 插件（如果已安装）
审计并删除：21 个命令中 0 次调用的命令
审计并删除：23 个 Agent 中 0 次调用的 Agent
```

### 精准填补四个缺口

**返工率**：通过 `/plan-feature.md` 命令实现合约优先开发。SDD 论文记录了规格优先方案使**集成周期时间减少 75%**。对于超过 1 天工作量的功能，在任何实现前要求一个计划制品。对于更小的工作，现有架构文档 + 代码审查命令已经足够。

**Graphiti 噪音**：上述 group_id 重构立即将信号与噪音分离。检索预算（2000-6000 tokens，根据任务决定）确保关键决策优先浮出。摄入过滤器防止未来噪音积累。不要删除现有数据——重新分类它。

**技术审计缺口**：`.claude/tech-checklist.md` 文件通过 `@` 在提示词中引用，提供了简单的确定性检查。配合 PreToolUse Hook（验证 imports 是否在批准的技术列表中）强化。这用确定性执行替代了 SuperPower 的概率性 HARD-GATE。

**TDD 缺口**：3 个 Agent 的 TDD 循环（`tdd-test-writer`、`tdd-implementer`、`tdd-refactorer`）配合阻断无测试实现的 PreToolUse Hook，从结构上提供强制执行。每个循环约 60K tokens 的开销是真正 TDD 的代价——但它防止了每位实践者都报告的"Claude 在实现后写测试"反模式。对于 30 分钟以内的快速修复，跳过子 Agent TDD，改用每次文件编辑后运行测试套件的 PostToolUse Hook。

**所有建议的总实施成本约为 8-12 小时**集中工作：Graphiti 重构 2 小时，新命令/Agent 2-3 小时，Hook 修改 2-3 小时，CLAUDE.md 重写及对现有 23 个 Agent + 21 个命令的审计 2-4 小时。完成后，开发者将拥有一个更精简、确定性更强的系统——建立在实际运行的基础上，而非理论上安装的框架。
