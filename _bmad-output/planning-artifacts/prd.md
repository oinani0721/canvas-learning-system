---
stepsCompleted:
  - step-01-init
  - step-02-discovery
  - step-03-success
classification:
  projectType: desktop_app
  domain: edtech
  complexity: high
  projectContext: brownfield
inputDocuments:
  - path: '/Users/Heishing/Desktop/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md'
    type: 'prd-source'
    description: 'PRD v5 - Scheme A Learning Effect Conservation PRD (7594 lines, 13 sections)'
  - path: '_bmad-output/planning-artifacts/prd-tauri-archived-20260401.md'
    type: 'archived-prd'
    description: 'Archived Tauri PRD (74KB, superseded by Obsidian Hybrid)'
  - path: '_bmad-output/planning-artifacts/architecture.md'
    type: 'architecture'
    description: 'Architecture document (68KB)'
  - path: '_bmad-output/planning-artifacts/epics.md'
    type: 'epics'
    description: 'Epics document (65KB)'
  - path: '_bmad-output/planning-artifacts/ux-design-specification.md'
    type: 'ux-design'
    description: 'UX Design Specification (37KB)'
  - path: 'docs/architecture.md'
    type: 'project-docs'
    description: 'Project architecture documentation'
documentCounts:
  briefs: 0
  research: 65
  brainstorming: 0
  projectDocs: 6
workflowType: 'prd'
anchor_source: '/Users/Heishing/Desktop/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md'
---

# Product Requirements Document - Canvas

**Author:** ROG
**Date:** 2026-04-12

## Success Criteria

### User Success

- **核心诉求**（用户批注 #8 锁定）："批注驱动的精确考察" — LLM 读懂 callout 批注 → 生成针对个人的考察 → 用户回答 → 更新掌握度 → 循环
- **灵魂标准**：检验白板提供 100% 等价的 Active Recall 环境（Karpicke 2011, d=1.50）
- **守恒标准**：12 个学习设计的效应量独立保留（narrative synthesis，不给单一百分比）
  - 9 个设计 ≥ 85% 守恒（检验白板 95%、Generation Effect 95%、BKT+FSRS 95%、正面措辞 100% 等）
  - 3 个设计 60-80% 有降级策略（Edge 对话 75%、隐形评分 70%、节点颜色 75%）
  - 0 个设计严重丢失（< 50%）
- **交互标准**：6 个 Claude Code Skill 通过 hotkey 触发完整学习闭环
- **出题个人化**：三路数据源融合（Graphiti 个人记忆 + Graphify 知识图谱 + Obsidian frontmatter 掌握度）生成针对用户当前状态的题目

### Business Success

- 能走通完整的"贴入笔记 → Graphify 知识图谱构建 → 检验白板考察 → 错误修正 → 掌握度更新"闭环
- Phase 1 骨架 2-3 周内可验证灵魂流程（检验白板 10 步 workflow）
- Phase 2 所有 12 个设计可验证（6 skill 全落地）
- 三套检索系统协同运行：Graphify（笔记关系，71x token 减少）+ LanceDB（笔记片段精确召回）+ Graphiti（个人学习记忆）

### Technical Success

- FastAPI 后端 + 14 MCP 工具正常运行（Day 1 Spike 1 验证）
- canvas_agentic_rag import 链 LANGGRAPH_AVAILABLE=True（Plan v23 已验证）
- Obsidian vault + Claudian + 10 插件稳定协作
- Graphify 7 层管道正确处理 wiki/ 目录输出 graph.json（定期全量索引）
- LanceDB + bge-m3 实时增量索引（MIRACL nDCG@10=63.9）
- BKT + FSRS + 5 信号融合系统正确更新 wiki/concepts/*.md frontmatter 掌握度
- Graphiti 通过 MCP 工具异步非阻塞写入 Neo4j

### Measurable Outcomes

- 检验白板：exam_boards/*.md 打开时零 wiki/concepts/ 内容泄漏（§2.4 三重保证）
- Generation Effect：书签式新节点正确归入 wiki/concepts/（不中断考察流程）
- 隐形评分：frontmatter 5 信号成功更新（用户感知不到评分过程）
- Dataview Dashboard：处方性措辞实时反映学习状态
- RAG 管道：Precision@5 ≥ 0.70、Recall@10 ≥ 0.80、MRR@10 ≥ 0.70

## Product Scope

### MVP - Phase 1 骨架 (2-3 周)

- vault 初始化（canvas-vault/ 目录结构 + CLAUDE.md + 5 强制插件）
- Claudian 配置（Claude Code CLI path + hotkey 绑定验证）
- Canvas 后端启动（14 MCP 工具可调用 + Blocker #1/#2/#3 修复）
- 3 个最小 skill：`/chat_with_context`、`/start_exam_board`（灵魂）、`/extract_node`
- Templater 模板：exam-board.md、concept.md、edge.md
- Graphify 集成（pip install + 第一次 /graphify 验证）
- 第一次检验白板 demo（完整 10 步 workflow 跑通）

### Growth Features - Phase 2 学习闭环 (2-4 周)

- 剩余 3 个 skill：`/edge_discuss`、`/quiz_from_callout`、`/review_profile`
- Dataview Dashboard 完善（2x2 校准矩阵可视化 + 处方性措辞全覆盖）
- 10 个插件全装（Tasks/Smart Connections/Kanban/Metadata Menu/Obsidian Git）
- Graphify health check 定期任务
- 第一个真实学习 demo（MT2 LLRB 章节完整闭环）

### Vision - Phase 3 精修 (持续)

- FSRS 插件替换 SM-2（等社区 FSRS 插件稳定）
- Canvas↔Graphiti 双向同步（历史会话归档）
- 校准投票的 few-shot 改进 LLM 评分
- 元认知 2x2 可视化升级
- Graphify cluster-based 主题自动发现
