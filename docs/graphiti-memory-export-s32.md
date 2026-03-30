# Graphiti Memory Export — canvas-dev group (50 episodes, 30 facts)

> Exported at 2026-03-28 for Gemini Deep Research analysis.
> This file contains ALL active episodes and facts from the project's knowledge graph.

---

## Active Facts (30, exclude_invalidated=true)

1. 用户要求包含了开发纪律规则固化
2. Sprint2阶段后端的目标是修复Graphiti
3. Deep Explore开发流程的决策和审查维度适用于整个开发流程
4. 推荐方案与现有的Graphiti决策一致
5. 消灭AI Agent返工：BMAD+Graphiti混合架构完整指南 describes architecture involving Graphiti
6. Decision-Review记录 is an uncompleted item for 后端graphiti_core集成调研
7. 5个hook在技术层面工作正常
8. 项目已有的架构设计中包含Graphiti Bridge
9. 15项决策已确认，作为UX-Design-Create-2026-03-16工作流的前置条件
10. 该决策的P1优先级事项包括Graphiti group_id重构
11. Graphiti与Agentic RAG的组合可行性正等待用户P0确认
12. The user is inquiring about the feasibility of Graphiti combined with Agentic RAG
13. Agentic RAG maturity assessment explores how Agentic RAG could combine with Graphiti
14. agentic RAG uses GraphitiClient
15. Agent的代码修改和错误没有被记录在Graphiti中
16. 工作流1涉及Agent线程化改造
17. 工作流2涉及检验白板
18. RAG-Scale-Quality的后续工作需要与代码审查进行交叉比对
19. PRD更新将影响工作流2
20. MVP刚需确认了14项MVP刚需 + 2个底层系统
21. 架构基准包括MVP刚需14项
22. 所有MVP刚需均可在原生Canvas扩展模式下实现
23. session-start v4是5个hook中的一个

---

## Episodes Summary (50 most recent)

### Root-Cause Analysis
独立Agent根因分析五大发现：1.披着敏捷皮的瀑布—5个Sprint 90分钟50K行代码 2.写代码成本归零但验证成本没变 3.1167个markdown文件43744行规划膨胀 4.环境盲区37个隐性约束 5.AI知识偏差驱动过度设计。DD-01/DD-04有害推向论文级复杂度，DD-10最重要但最被忽视。核心结论：AI写代码太快验证来不及。

### Stop Hook Fix
搜索不等于记录。拆分为 hasAddMemory 和 hasSearchOnly 两个独立检测。

### Key Decisions
- S1 死代码清理范围扩大至8200+行
- T11 Graphiti SDK重写基于GraphitiTemporalClient模式
- S27 路径A确认：先打通管道再打磨体验（4Phase）
- Neo4j 7691保留学习数据专用，7689开发记忆
- group_id按白板命名，白板名=group_id
- prompt禁止硬编码，必须外部文件
- Gemini全家桶（GeminiClient+GeminiEmbedder+GeminiRerankerClient）
- S29 bypassPermissions修复 permissionMode default+canUseTool白名单
- S29 PostToolUse BEA提取 SDK native hook+fire-and-forget

### GDA Findings
42处假命名(12C+13H)。backend/app/零graphiti-core调用,30+函数名含graphiti全是Neo4j Cypher。根因:AI混淆写入Neo4j不等于写入Graphiti。

### GDR Findings
- 记忆重构策略C asyncio.Queue+Worker，官方验证
- Tier B增强CLI方案——90%SDK能力+30%复杂度
- S31 GDR 规范驱动开发工作流重构

### Research Highlights
- Agentic RAG三层成熟度：Tier1元数据预过滤 Tier2 Adaptive路由+CRAG Tier3多Agent(100K+)
- 120个笔记文件约130-200K tokens，3个genuine bug修复可覆盖80%+收益
- Karpicke陷阱：检索练习效果优于概念图，效应量d=1.50
- S29 MCP端到端验证通过 record_learning_memory成功

### S32 Current Session
工作流重构计划：基于三份Deep Research报告制定CLAUDE.md+/commands改造方案。用户核心诉求：SSD高质量实施+Graphiti噪音清理+Agentic RAG混合架构+封装为Claude Code /commands。

---

## Key Statistics
- Total episodes: 50 (2026-03-11 to 2026-03-28)
- Decision episodes: ~20
- Research episodes: ~15
- Dev-Complete episodes: ~8
- Known issues: 42 fake-named functions, 6 broken pipelines, 20 gotchas (8 fixed, 12 pending)
