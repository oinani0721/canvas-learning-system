---
stepsCompleted:
  - step-01-init
  - step-02-discovery
  - step-03-success
  - step-04-journeys
  - step-05-domain
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

## User Journeys

### 旅程 1 · 日常学习（剖析模式）

**用户**: ROG（CS 61B 学生）
**核心原理**: Edge 对话 EI+SE (d=0.80-1.00) + Generation Effect (d=0.65)
**场景**: 解题过程中遇到不懂的知识点

**故事**:
ROG 正在做 A* 搜索的练习题，遇到"为什么 consistent 蕴含 admissible"这个点看不懂。他在 Obsidian 笔记里用 `[!question]+` callout 批注了这个困惑，Claudian 侧边栏立刻回答了他关于批注的疑问（`/chat_with_context` 自动挂载当前笔记 + `search_memories` 拉取历史误解）。

讨论中 ROG 发现"admissible heuristic reasoning"是一个更深的知识点需要单独理解。他选中对话文本，按 Cmd+Option+X 触发 `/extract_node`，在批注附近自动插入 `[[admissible-heuristic-reasoning]]` wikilink（双向链接），同时创建 `wiki/concepts/admissible-heuristic-reasoning.md`（frontmatter 骨架，默认 BKT=0.30）。

ROG 点击 wikilink 切到新文档，Claudian 重新挂载并检测到 `extracted_from` 字段，自动进入剖析模式。他用 `/chat_with_context` 深度讨论这个概念，又用 `/edge_discuss` 探索它与 A* 最优性的关系，产出 `edges/admissible-heuristic-reasoning--a-star.md`。

**产物**: 对话记录 + 新 Edge + 新概念节点（Generation Effect）
**守恒度**: 85%

### 旅程 2 · 检验白板考察（灵魂旅程）

**用户**: ROG
**核心原理**: Retrieval Practice d=1.50 (Karpicke & Blunt 2011)
**场景**: 主动测试自己对搜索算法的掌握程度

**故事**:
ROG 按 Cmd+Option+E 触发 `/start_exam_board`。Skill 防嵌套检查通过后，询问考察主题和模式。`query_mastery` 从 Neo4j 读出��握度分数，选出 admissibility (0.62)、a-star (0.68) 等弱项。Templater 生成空白 `exam_boards/search-algorithms-2026-04-08-20-00.md`。

ROG 在 Obsidian 打开这个空白文件，Claudian 重置上下文。`generate_question` 融合三路数据（Graphiti 个人记忆 + Graphify 知识图谱 + frontmatter 掌握度）生成个人化题目。ROG 在 md 编辑器手写答案，按 Cmd+Option+S 提交。系统静默评分，更新 BKT/FSRS。

考察中发现"不懂 consistent 和 admissible 的区别"→ `/extract_node` 书签式创建新节点（不切 Tab，保护 Active Recall）→ 考完后再深度讨论。

**产物**: 完整考察记录 + 掌握度更新 + 书签式新节点
**守恒度**: 95%

### 旅程 3 · 错误修正记忆闭环

**用户**: ROG
**核心原理**: Error Correction (Metcalfe 2017) + Spacing Effect d≈0.55 (Cepeda 2008)
**场景**: 3 天 + 1 周自动提醒纠正历史误解

**故事**:
Day 0: ROG 在对话中发现"把 consistent 和 admissible 搞混了"，标记 `[!fail]+` callout，Skill 自动生成 Tasks 提醒（Day 3 复习 + Day 7 辨析题），调 `record_error` 写入 Graphiti。

Day 3: Spaced Repetition 插件弹出提醒��ROG 打开笔记，Claudian 自动挂载并注入"你 3 天前标记过这个误解"，引导复习，调 `update_fsrs` 更新稳定性。

Day 7: Tasks dashboard 显示辨析题考察到期。ROG 触发 `/start_exam_board`，`generate_question` 基于 Graphiti 历史误解出辨析题："给出一个启发函数是 admissible 但不是 consistent 的例子"。答对 → 误解永久纠正。

**产物**: 完整 3 天 + 1 周闭环
**守恒度**: 90%

### 旅程 4 · 新用户冷启动

**用户**: 首次使用 Canvas Learning System 的学习者
**核心原理**: Progressive Calibration（渐进画像）
**场景**: 从安装到"系统越来越懂我"

**故事**:
新用户安装 Obsidian + Claudian + 10 插件 + 启动 Canvas 后端。创建第一个主题笔记，贴入课件文本，触发 `/chat_with_context`。因为 Graphiti 历史为空，LLM 回答无个性化（默认 BKT=0.30）。

第 5 次调用时 `search_memories` 开始返回有价值的历史。第 8 次时 `generate_question` 能基于历史错误出题。用户体感"Agent 记住了我上次的错"。

**产物**: 从零到个性化的渐进体验
**守恒度**: 90%

### 旅程 5 · 图片密集型学习

**用户**: ROG（学习含大量图示的算法课件）
**核心原理**: Multi-modal Learning (Mayer 2009) d=0.40-0.60
**场景**: 贴入算法流程图后讨论

**故事**:
ROG 在笔记里贴入 A* 搜索的树状展开图 `![[a-star-tree.png]]`。触发 `/chat_with_context`，Claudian 原生图像识别读取图片内容，Claude 分析图中的搜索路径并回答问题。但图片内容不会自动持久化到 Graphify 索引（降级部分）。

**产物**: 多模态对话记录
**守恒度**: 70%（Claudian 原生多模态，但异步索引降级）

### 旅程 6 · 学习档案浏览

**用户**: ROG
**核心原理**: Formative Feedback d=0.50-0.80 (Hattie 2007) + Open Learner Model
**场景**: 查看学习进度和元认知状态

**故事**:
ROG 按 Cmd+Option+P 触发 `/review_profile`，或直接打开 `wiki/dashboard.md`。Dashboard 由 Dataview 插件驱动，三层布局：

Layer 1 · 原白板卡片（CSS Grid 布局）：每个主题显示节点数 + 平均掌握度 + emoji 状态 + [🧪考察] 按钮（Buttons 插件触发 QuickAdd → Skill）。

Layer 2 · 建议优先复习（Dataview 处方性措辞）：🔴 建议优先复习: admissibility (62%) — 今天。不给数字让用户自己判断，直接告诉"下一步该做什么"。

Layer 3 · 元认知 2x2 校准矩阵（dataviewjs）：按"实际掌握度 × 自我评估置信度"分四象限，重点标出 🔴 "不会但以为会"。

ROG 点击某个概念 → 进入单节点 profile → 5 信号状态 + Tips + 待纠正理解 + 相关 Edges + [启动考察] 按钮。

**插件栈**: Dataview（查询）+ Buttons（交互）+ QuickAdd（桥接 Skill）+ CSS snippets（卡片布局，TfTHacker Dashboard++ 社区方案）+ Homepage（自动打开）

**产物**: 实时学习进度可视化
**守恒度**: 75%

### Journey Requirements Summary

| 旅程 | 依赖的核心能力 |
|---|---|
| 1 日常学习 | `/chat_with_context` + `/edge_discuss` + `/extract_node` + context_enrichment MCP |
| 2 检验白板 | `/start_exam_board` + query_mastery + generate_question + score_answer MCP |
| 3 错误修正 | record_error MCP + Spaced Repetition 插件 + Tasks 插件 + search_memories |
| 4 冷启动 | Claudian + 后端 + 默认 BKT 先验 |
| 5 图片学习 | Claudian 图像识别 + Vision API |
| 6 档案浏览 | `/review_profile` + Dataview Dashboard + Buttons + QuickAdd + CSS snippets |

## Domain-Specific Requirements

### 学习科学合规（核心领域约束）

本产品的领域合规不来自传统 EdTech 法规（COPPA/FERPA 不适用于个人工具），而来自**学习科学效应量标准**：

- 12 个学习设计各有明确的学术来源和效应量 d-value（PRD v5 §1）
- 每个设计独立评估守恒度（narrative synthesis，Cochrane Handbook Ch 12 方法学）
- 9 个设计 ≥ 85% 守恒是产品可行性的前提
- 检验白板 Retrieval Practice d=1.50 (Karpicke 2011) 是不可妥协底线

### 评估完整性约束

- **信息隔离**：检验白板考察时必须保证 exam_boards/*.md 不泄漏 wiki/concepts/ 内容（§2.4 三重保证）
- **静默评分**：用户不感知评分过程（Cassady 2002 考试焦虑防护，§1.6）
- **个人化出题**：三路数据融合（Graphiti 个人记忆 + Graphify 知识图谱 + frontmatter 掌握度）
- **校准机制**：考后校准投票防止 AI 评分偏差（§1.11）

### 数据本地性

- 所有学习数据本地存储（Obsidian vault 文件 + Neo4j + LanceDB）
- LLM API 调用是唯一的外部数据流出
- Obsidian Git 插件可选备份（用户控制是否推送远程）
- 无云端同步、无数据收集、无遥测

### 性能约束

- LLM 出题延迟 < 5 秒（用户等待耐心）
- Dataview Dashboard 查询 < 1 秒刷新
- Graphify 全量索引 < 30 秒（wiki/ 目录规模 ~100 文件）
- LanceDB 增量索引实时（文件保存后自动触发）
- Graphiti 写入异步非阻塞（不影响答题体验）
