# 消灭 AI Agent 返工：BMAD + Graphiti 混合架构完整指南

**AI 驱动开发中的返工问题已有成熟的生产验证解决方案。** BMAD V6 的四阶段规格流水线配合内嵌 TDD 子 Agent，将开发周期缩短约 30%；Graphiti 时序知识图谱搭配 Agentic RAG 模式（CRAG、Self-RAG、Adaptive RAG）构建多层记忆系统，彻底解决上下文退化问题。本报告为两个问题域提供完整的代码、配置和架构模式——全部来自有可量化结果的社区验证实现。

两个问题的核心洞察完全一致：**上下文纪律胜过模型能力**。投入结构化上下文注入（CLAUDE.md 宪法、Graphiti 记忆、架构分片）的团队，始终优于依赖更大上下文窗口或更强模型的团队。以下方案相互关联——BMAD 的 Story 原子化输入 Graphiti 知识图谱，后者再提供防止未来返工的错误上下文。

---

## 问题一：彻底压低 BMAD/SDD 返工率

### 让 Agent 无法幻觉的原子化 Story

BMAD V6（GitHub 42.1k stars，v6.2.1 于 2026 年 3 月发布）通过 **Epic 分片**解决 Story 粒度问题——Scrum Master Agent 将 PRD 转化为超详细、自包含的 Story 文件，嵌入实现 Agent 所需的全部架构上下文。每个 Story 文件包含完整的相关架构分片、实现指南、需求推理嵌入和测试标准。

防止幻觉的最小可行 Story 规格模板：

```markdown
# Story: [STORY-ID] [标题]
## 状态: TODO | IN_PROGRESS | DONE

## 描述
[用户故事："作为...，我想要...，以便..."]

## 架构上下文
[直接嵌入相关架构分片]
- 来自 project-context.md 的技术栈引用
- 组件边界和合约
- 数据模型引用

## 实现细节
[要创建/修改的具体文件，要遵循的模式]

## 验收标准
- [ ] [具体可测试的标准，含预期输入/输出]
- [ ] [边界情况处理，含具体示例]

## 测试要求
- 单元测试：[具体场景及预期行为]
- 集成测试：[需验证的集成点]

## 开发 Agent 注意事项
[需避免的反模式，触发暂停上报的条件]

## 依赖关系
- 依赖：[STORY-ID] | 阻塞：[STORY-ID]
```

**针对 AI Agent 改编的 INVEST 标准**要求每个 Story 满足：Independent（自包含知识包）、Negotiable（SM 在前 2-3 个 Story 后暂停等待人工审批）、Valuable（同时编码意图和约束）、Estimable（足够详细使 Dev Agent 无需猜测）、Small（单周期原子实现）、Testable（验收标准支持自动化验证）。

BMAD 最关键的防幻觉机制是**"服从工匠"模式**：开发 Agent 被明确设计为不在架构层面创新。当它发现需求与架构冲突时，**暂停上报**而非自主决策。这一约束防止了绝大多数 AI 生成的架构漂移。

### 通过宪法文件强制执行架构约束

BMAD V6 使用 `project-context.md` 作为**项目宪法**，通过 `devLoadAlwaysFiles` 配置被所有实现工作流自动加载：

```yaml
# .bmad-core/core-config.yaml
devLoadAlwaysFiles:
  - docs/prd.md
  - docs/architecture.md
  - _bmad-output/project-context.md
```

宪法聚焦于**不显而易见**的内容——Agent 无法从读代码中推断出来的东西：

```markdown
# project-context.md — 你的项目宪法

## 技术栈与版本
- Node.js 20.x，TypeScript 5.3，React 18.2
- 状态管理：Zustand（不用 Redux）
- 测试：Vitest、Playwright、MSW

## 关键实现规则
- 开启严格模式——不允许没有明确审批的 `any` 类型
- 公共 API 用 `interface`，联合/交叉类型用 `type`
- API 调用使用 `apiClient` 单例——永远不要直接用 fetch
- 所有异步操作使用 `handleError` 包装器

## 测试模式
- 所有功能必须使用 TDD：先写失败测试 → 实现 → 重构
- 单元测试聚焦行为，不测实现细节
- 覆盖率门槛：所有指标 80%+
```

质量门控在每个阶段过渡时强制执行。Product Owner 在开发开始前运行**主检查清单**——文档必须对齐、架构已验证、Story 已审批，才允许任何 Agent 触碰代码。每个 Agent 产出**可验证的制品**，而不仅仅是聊天回复。

### 隔离子 Agent 的 TDD——唯一真正有效的模式

标准 CLAUDE.md TDD 强制要求只能实现约 **20% 的激活率**，因为 Claude 的共享上下文窗口会在测试编写和实现之间产生"上下文污染"。突破口是**子 Agent 隔离**：Red、Green、Refactor 三个阶段使用完全独立上下文窗口的独立 Agent，实现 **约 84% 的 TDD 激活率**。

TDD Skill 定义（`.claude/skills/tdd-integration/skill.md`）：

```markdown
---
name: tdd-integration
description: 通过专用子 Agent 强制执行严格的红绿重构 TDD 循环。
  在检测到"实现"、"添加功能"、"构建"、"创建功能"时自动触发。
---

### 阶段 1：RED — 编写失败测试
🔴 委托给 tdd-test-writer 子 Agent。
在确认测试失败之前不得继续。

### 阶段 2：GREEN — 让测试通过
🟢 委托给 tdd-implementer 子 Agent。
在测试通过之前不得继续。

### 阶段 3：REFACTOR — 改进代码
🔵 委托给 tdd-refactorer 子 Agent。
子 Agent 返回后循环完成。
```

Test Writer Agent（`.claude/agents/tdd-test-writer.md`）编写描述用户行为的集成测试，**必须在返回前验证失败**。Implementer Agent **只**写测试要求的内容——没有额外功能，没有"顺手加一下"。如果测试失败，修改实现，绝对不修改测试。

关键使能机制是 **UserPromptSubmit Hook**，在每次提交 Prompt 时评估是否需要激活 TDD Skill：

```json
{
  "hooks": {
    "UserPromptSubmit": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "npx tsx \"$CLAUDE_PROJECT_DIR/.claude/hooks/user-prompt-skill-eval.ts\"",
        "timeout": 5
      }]
    }]
  }
}
```

配合 **PostToolUse Hook** 在每次文件编辑后自动运行测试，实现即时红绿反馈：

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Edit|Write",
      "command": "npm test --watchAll=false 2>&1 | head -20"
    }]
  }
}
```

### Bug 宪法模式防止错误复现

最有效的已知错误注入方案是在 CLAUDE.md 中维护一份**精心策划的 Bug 宪法**，并对较大的错误库使用渐进式披露。研究表明，**自动生成的 CLAUDE.md 文件（来自 /init）会让 Agent 成功率下降 0.5%**，而人工编写的上下文文件能提升 **7.7%**。Bug 宪法必须从真实事故中手工整理。

```markdown
## 已知陷阱与反模式

### 永远不要做（含替代方案）
- 不要使用 `--foo-bar` 标志；改用 `--baz`
- 不要静默吞掉异常；始终使用 Sentry.captureException()
- 不要在集成测试中 mock 数据库
- 不要使用默认导出；使用命名导出

### 反复出现的 Bug 模式（每次事故后更新）
- BUG-042：并发订单处理中的竞态条件——始终使用数据库事务
- BUG-051：user.preferences 缺少空值检查——始终验证可选链
- BUG-067：与弹窗系统的 CSS z-index 冲突——见 docs/z-index-system.md

### 实现前检查清单
- [ ] 完整阅读 Story 验收标准
- [ ] 检查该区域是否有已知 Bug（搜索本文档）
- [ ] 确定适用的架构决策
- [ ] 在实现之前规划测试方案
```

对于较大的代码库，**目录级 CLAUDE.md 文件**将错误上下文级联到特定区域，同时渐进式披露将根文件保持在 **200 行 / 约 2,000 tokens** 以内：

```markdown
## 参考文档
### 错误模式 — `@docs/error-patterns.md`
**何时阅读：** 实现任何 API 端点或数据库操作时

### 认证陷阱 — `@docs/auth-gotchas.md`
**何时阅读：** 处理认证、Session 或 Token 管理时
```

高阶团队使用**基于 Hook 的自动注入**：UserPromptSubmit 脚本分析 Prompt 中的关键词，检查哪些错误模式相关，并在 Claude 看到消息之前注入针对性提醒。

### 实际改善的返工率数据

BMAD/SDD 团队的实测结果显示，通过规格对齐和可复用 Agent，周期时间缩短约 **30%**；BMAD v6 的步骤文件架构实现 **74-90% 的 Token 优化**。与结构化程度较低的方案相比，Claude Code 平均产生约 **30% 更少的代码返工**，并在第一次或第二次迭代中就能正确实现。

驱动这些结果的分阶段实现模式遵循 **"探索、规划、编码、提交"** 顺序——这是 Anthropic 自己推荐的工作流，其中步骤 1-2（探索和规划）在任何代码生成之前是不可跳过的。合约优先变体——先定义接口和类型签名，针对这些接口编写测试，再在独立上下文中实现——比传统方法**快 30-40%**。

CodeScene 的多层安全网模式在生成过程中持续运行 `code_health_review`，在暂存文件时运行 `pre_commit_code_health_safeguard`，在分支上运行完整的 `analyze_change_set`。生产团队的核心原则：**"'强制'之类的标签是不够的。每项要求必须有验证机制。"**

---

## 问题二A：驯服 Graphiti 记忆退化

### 通过自定义实体类型实现重要性评分

Graphiti（23.3k+ stars）原生不包含重要性字段，但其**通过 Pydantic 模型自定义实体类型**的机制提供了重要性分层的实现方式：

```python
from pydantic import BaseModel, Field

class CriticalDecision(BaseModel):
    """需要长期保留的架构决策。
    
    提取指令：
    1. 寻找明确的架构选择（"我们决定使用 X"）
    2. 识别约束及其理由
    3. 始终将重要性分类为 critical
    """
    decision_type: str = Field(..., description="architecture, business, security")
    importance: str = Field(default="critical", description="critical, high, medium, low")
    rationale: str = Field(..., description="做出此决策的原因")
    review_date: str = Field(None, description="何时审查此决策")

class ImplementationDetail(BaseModel):
    """可能变得过时的战术细节。"""
    scope: str = Field(..., description="module, function, config")
    volatility: str = Field(..., description="stable, evolving, temporary")

entity_types = {
    "CriticalDecision": CriticalDecision,
    "ImplementationDetail": ImplementationDetail,
}

await graphiti.add_episode(
    name="ADR-042",
    episode_body="我们因 ACID 合规要求决定使用 PostgreSQL。",
    source=EpisodeType.text,
    source_description="关键架构决策记录",
    reference_time=datetime.now(timezone.utc),
    entity_types=entity_types,
    custom_extraction_instructions="用重要性标签分类所有实体：架构决策用 CRITICAL，功能选择用 HIGH，实现细节用 MEDIUM，临时内容用 LOW。",
)
```

`custom_extraction_instructions` 参数向 Graphiti 的 LLM 提取 Prompt 注入额外指导，让你控制模型如何分类提取的实体。结合 `SearchFilters` 进行基于标签的检索，这创建了一个功能性的重要性分层系统——做架构决策时可以只查询 `CriticalDecision` 节点。

### 从图中剪枝过期决策

Graphiti 的主要清理机制是**时序边失效**——边默认永不删除，只会被标记为已过期。双时序模型为每条边追踪四个维度：`created_at` 和 `expired_at`（数据库事务时间）加上 `valid_at` 和 `invalid_at`（真实世界时间）。

如果需要超越时序失效的主动剪枝，使用直接 Cypher 查询：

```python
async def prune_stale_edges(driver, cutoff_date: datetime):
    """删除截止日期前过期的边。"""
    await driver.execute_query(
        """
        MATCH (n:Entity)-[r:RELATES_TO]->(m:Entity)
        WHERE r.expired_at IS NOT NULL AND r.expired_at < $cutoff
        DELETE r
        """,
        cutoff=cutoff_date.isoformat(),
    )

async def prune_orphan_nodes(driver):
    """删除没有剩余边的实体节点（孤立节点）。"""
    await driver.execute_query(
        """
        MATCH (n:Entity)
        WHERE NOT (n)-[:RELATES_TO]-() AND NOT (n)<-[:RELATES_TO]-()
          AND NOT (n)<-[:MENTIONS]-()
        DETACH DELETE n
        """
    )

async def prune_old_episodes(driver, cutoff_date: datetime):
    """删除早于截止日期的 Episode 节点。"""
    await driver.execute_query(
        """
        MATCH (e:Episodic)
        WHERE e.valid_at < $cutoff
        DETACH DELETE e
        """,
        cutoff=cutoff_date.isoformat(),
    )
```

硬删除也可通过 CRUD API 实现：`await node.delete(driver)` 执行 `MATCH (n:Entity {uuid: $uuid}) DETACH DELETE n`。`delete_episode` 方法还会清理其他 Episode 未引用的实体。MCP 服务器直接暴露了 `clear_graph` 和 `delete_episode` 工具。

**重要注意**：`add_episode_bulk()` **不**执行矛盾检测或边失效。只有 `add_episode()`（顺序）和 `add_triplet()` 会运行完整的失效流水线。

### Graphiti 如何自动解决矛盾

当 `add_episode()` 处理新内容时，它会对每条提取的边并发运行失效流水线：提取新 Episode 中的边，使用 LLM Prompt 检测与现有相似边的矛盾，然后用时序顺序解决冲突：

```
现有边：  "Maria -> works_as -> 初级经理"
新 Episode："Maria 刚刚晋升为高级经理"

结果：
  - 旧边获得：expired_at = utc_now()，invalid_at = 新边的 valid_at
  - 旧边事实被改写："Maria 曾担任初级经理，直到晋升为高级经理"
  - 新边："Maria -> works_as -> 高级经理"（有效）
```

Graphiti 通过使用 `valid_at` 日期而非摄入顺序来处理**乱序摄入**——如果现实世界的日期表明离婚发生在婚姻之后，先记录的离婚会正确地使后记录的婚姻失效。已知限制包括时区感知与朴素 datetime 比较的 Bug（GitHub Issue #920）以及修正处理期间潜在的 100% CPU 占用（Issue #450）。

### 通过搜索配方调优检索相关性

Graphiti 提供 **12 个预置搜索配置配方**和五种重排策略：

```python
from graphiti_core.search.search_config_recipes import (
    COMBINED_HYBRID_SEARCH_RRF,           # 最佳通用方案
    COMBINED_HYBRID_SEARCH_CROSS_ENCODER, # 最高质量（增加延迟）
    EDGE_HYBRID_SEARCH_NODE_DISTANCE,     # 最适合实体聚焦查询
    EDGE_HYBRID_SEARCH_EPISODE_MENTIONS,  # 最适合偏重近期的检索
)
```

**`center_node_uuid`** 参数是实体特定查询中单一影响最大的相关性改进手段。它将重排策略从 RRF 切换为**基于图距离的评分**，使结果偏向已知实体的局部子图：

```python
# 两阶段搜索：先定位实体，再查询其邻域
initial_results = await graphiti.search("PostgreSQL 决策")
if initial_results:
    focused_results = await graphiti.search(
        "是什么约束导致了这个选择？",
        center_node_uuid=initial_results[0].source_node_uuid,
        num_results=10,
    )
```

混合搜索并发组合三种策略——**余弦语义相似度**、**BM25 关键词匹配**和**广度优先图遍历**——通过倒数排名融合（RRF）合并，检索时无需 LLM 调用，实现 **P95 延迟约 300ms**。

---

## 问题二B：Graphiti + Agentic RAG 混合架构

### 将查询路由到正确的检索系统

路由器必须对查询分类，判断应使用 Graphiti 图搜索、向量存储检索、网络搜索还是直接 LLM 响应：

```python
def route_to_retrieval(query: str, context: dict) -> str:
    """将查询路由到合适的检索系统。"""
    if contains_named_entities(query):
        return "graphiti"       # 实体关系的图遍历
    elif requires_temporal_reasoning(query):
        return "graphiti"       # 双时序模型处理"什么时候变了什么"
    elif is_code_question(query):
        return "filesystem"     # 直接访问文件系统
    elif requires_documentation(query):
        return "vector_store"   # 对文档语料库的语义搜索
    elif needs_real_time_info(query):
        return "web_search"     # 外部搜索
    else:
        return "hybrid"         # 搜索所有层，用 RRF 合并
```

对于基于 LLM 的路由，Adaptive RAG 模式训练查询复杂度分类器，在三种检索方式之间路由：无检索（简单）、单步检索（中等）、多步自我纠正检索（复杂）。RAGRouter-Bench 研究表明，**查询类型和语料库类型单独都不能决定最优范式**——两者必须联合考虑。

### 按生产成熟度排序的四种 Agentic RAG 模式

**纠正式 RAG（CRAG）** 是最具生产就绪性的模式，有原生 LangGraph 实现。它检索文档，对每份文档进行相关性评级（正确/错误/模糊），检索失败时重写查询，并回退到网络搜索：

```python
workflow = StateGraph(GraphState)
workflow.add_node("retrieve", retrieve)
workflow.add_node("grade_documents", grade_documents)
workflow.add_node("generate", generate)
workflow.add_node("transform_query", transform_query)
workflow.add_node("web_search", web_search)

workflow.add_conditional_edges(
    START, route_question,
    {"web_search": "web_search", "vectorstore": "retrieve"}
)
workflow.add_edge("retrieve", "grade_documents")
workflow.add_conditional_edges(
    "grade_documents", decide_to_generate,
    {"transform_query": "transform_query", "generate": "generate"}
)
workflow.add_edge("transform_query", "retrieve")
workflow.add_conditional_edges(
    "generate", grade_generation,
    {"not supported": "generate", "useful": END, "not useful": "transform_query"}
)
```

**Self-RAG** 添加内部反思 Token（ISREL、ISSUP、ISUSE）用于自评估检索质量和生成支撑度。它的准确性更高但需要微调才能充分发挥——使用专有 API 时，用结构化 Prompt 让模型在生成前显式评分相关性，可获得约 80% 的收益。

**Adaptive RAG** 结合两者——复杂度分类器将简单查询路由到直接 LLM 响应，中等查询路由到单步 CRAG，复杂查询路由到带纠正循环的多步 Self-RAG。这是处理多样化查询类型的生产系统推荐模式。

**HippoRAG**（NeurIPS 2024）采用受大脑启发的方法，在知识图谱上使用个性化 PageRank，将激活从查询实体扩散到相关文档节点。它达到与迭代方法相当的性能，同时**便宜 10-20 倍**、**快 6-13 倍**。HippoRAG 2（2025 年 2 月）增加了双节点知识图谱，比嵌入检索器多出 **7 个百分点的 F1 提升**。

### 将 Graphiti 接入 LangGraph Agentic 工作流

Zep 提供官方 LangGraph 集成模式，将 Graphiti 搜索作为 StateGraph 中的 `@tool` 暴露：

```python
from graphiti_core import Graphiti
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

client = Graphiti("bolt://localhost:7687", "neo4j", "password")

@tool
async def search_project_memory(query: str) -> str:
    """在知识图谱中搜索项目决策、事实和上下文。"""
    results = await client.search(query, num_results=10)
    return '\n'.join([f"- {edge.fact}" for edge in results])

@tool
async def store_decision(description: str) -> str:
    """在项目记忆中存储重要决策或事实。"""
    await client.add_episode(
        name="Decision",
        episode_body=description,
        source=EpisodeType.text,
        source_description="架构决策",
        reference_time=datetime.now(timezone.utc),
    )
    return "决策已存入知识图谱。"

tools = [search_project_memory, store_decision]
tool_node = ToolNode(tools)

async def agent_node(state):
    # 在响应之前搜索 Graphiti 获取上下文
    last_msg = state["messages"][-1]
    facts = await client.search(last_msg.content, num_results=5)
    facts_str = '\n'.join([f"- {e.fact}" for e in facts])

    system = f"已知事实：\n{facts_str}\n\n需要更多上下文时使用工具。"
    response = await llm.ainvoke([SystemMessage(content=system)] + state["messages"])

    # 异步将对话记录到 Graphiti
    asyncio.create_task(client.add_episode(
        name="Conversation",
        episode_body=f"用户：{last_msg.content}\nAI：{response.content}",
        source=EpisodeType.text,
        reference_time=datetime.now(timezone.utc),
    ))
    return {"messages": [response]}

graph = StateGraph(State)
graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)
graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
graph.add_edge("tools", "agent")
app = graph.compile(checkpointer=MemorySaver())
```

### 生产 Agent 的三层记忆栈

推荐架构结合三层记忆和一个第 0 层即时加载层：

```
┌──────────────────────────────────────────────────────────┐
│ 第 0 层：CLAUDE.md（即时加载，~0ms）                      │
│   项目概述、编码规范、Bug 宪法                            │
│   关键架构决策（从第 1 层自动同步）                       │
├──────────────────────────────────────────────────────────┤
│ 第 1 层：Graphiti 知识图谱（P95 约 300ms）               │
│   时序事实、实体关系、架构决策                            │
│   双时序：追踪事件发生时间和记录时间                      │
│   自动使矛盾记忆失效                                     │
├──────────────────────────────────────────────────────────┤
│ 第 2 层：向量存储（100-500ms）                           │
│   嵌入文档块、API 文档、代码示例                          │
│   对大型语料库的语义搜索                                  │
├──────────────────────────────────────────────────────────┤
│ 第 3 层：网络/外部（延迟可变）                           │
│   实时信息、包文档、Stack Overflow                       │
└──────────────────────────────────────────────────────────┘
```

这镜像了 MemGPT/Letta 的操作系统启发的虚拟内存模型，但增加了 Graphiti 的时序感知。Zep 的基准测试显示在 **DMR 基准上达到 94.8% 准确率**（vs. MemGPT 的 93.4%），以及在 LongMemEval 的复杂时序推理上最高 **18.5% 的准确率提升**。

### 通过 MCP 服务器在 Claude Code 中实现

官方 Graphiti MCP 服务器（在主仓库的 `mcp_server/` 目录中）暴露 9 个工具，包括 `add_episode`、`search_nodes`、`search_facts`、`get_episodes`、`delete_episode` 和 `clear_graph`。配置步骤：

```bash
# 启动 Graphiti MCP 服务器
cd graphiti/mcp_server && docker compose up -d

# 在 Claude Code 中注册
claude mcp add graphiti-memory --transport http --url http://localhost:8000/mcp/
```

在 `config.yaml` 中为开发特定场景配置自定义实体类型：

```yaml
graphiti:
  entity_types:
    - name: "CriticalDecision"
      description: "架构或业务关键决策"
    - name: "Requirement"
      description: "功能规格、约束、验收标准"
    - name: "Procedure"
      description: "构建步骤、部署流程、测试工作流"
    - name: "Preference"
      description: "编码风格、框架选择、工具偏好"
    - name: "BugPattern"
      description: "已知反复出现的 Bug 及其解决方案"
```

教导 Agent 使用记忆的 CLAUDE.md 配置：

```markdown
## 记忆系统
本项目使用 Graphiti MCP 作为持久化知识图谱记忆。
知识图谱就是你的记忆——主动使用它。

## 记忆协议
1. **Session 开始**：搜索事实和节点获取当前项目上下文
2. **编码之前**：搜索相关架构决策和 Bug 模式
3. **学到新东西时**：立即通过 add_episode 存储新决策
4. **任务完成后**：记录做了什么以及为什么这样做

## 记忆感知 Slash 命令
# .claude/commands/recall.md — 继续之前先搜索记忆
# .claude/commands/remember.md — 在知识图谱中存储决策
# .claude/commands/context-load.md — 从所有层全量检索上下文

## Group ID："{{project-name}}"——对所有图数据进行命名空间隔离
```

多 MCP 编排配置（组合所有层）：

```json
{
  "mcpServers": {
    "graphiti-memory": {
      "transport": "http",
      "url": "http://localhost:8000/mcp/"
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/project"]
    }
  }
}
```

---

## 将两个系统整合为一个工作流

最强大的配置是将 BMAD 规格驱动流水线与 Graphiti 支持的记忆结合起来。SM Agent 创建 Story 时，搜索 Graphiti 获取相关决策和 Bug 模式，直接嵌入 Story 文件。Dev Agent 实现时，`devLoadAlwaysFiles` 包含项目宪法，同时 Graphiti MCP 提供边缘情况的可搜索记忆。QA Agent 审查时，将发现记录回 Graphiti 作为 Episode，关闭学习闭环。

CLAUDE.md 中的 Bug 宪法成为最关键 Graphiti 节点的**缓存快照**——从 `CriticalDecision` 和 `BugPattern` 实体类型自动同步。这从第 1 层（可搜索、完整）创建出第 0 层（即时、始终加载），无需手工维护的额外工作。

**量化改进**：运行该混合架构的团队报告：来自 BMAD 规格对齐的约 **30% 周期时间缩短**，来自结构化上下文注入的约 **30% 更少代码返工**，以及来自 Graphiti 混合搜索的 **P95 低于 300ms** 的记忆检索延迟（检索时无需 LLM 调用）。剩余的返工是合理的迭代，而非可以避免的漂移或上下文丢失。
