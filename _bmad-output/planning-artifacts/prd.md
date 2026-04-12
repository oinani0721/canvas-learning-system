---
stepsCompleted:
  - step-01-init
  - step-02-discovery
  - step-03-success
  - step-04-journeys
  - step-05-domain
  - step-06-innovation
  - step-07-project-type
  - step-08-scoping
  - step-09-functional
  - step-10-nonfunctional
  - step-11-polish
  - step-12-complete
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

# Product Requirements Document - Canvas Learning System

**Author:** ROG
**Date:** 2026-04-12
**Anchor Source:** PRD v5 (`14-scheme-a-implementation-prd.md`, 7594 lines, read-only)

## Executive Summary

Canvas Learning System 是基于 Obsidian + Claudian + Canvas 后端的个人化学习桌面应用。从 Tauri+React 架构降级到 Obsidian Hybrid 部署后，追求**学习效果守恒**而非 UI 1:1 还原。

**产品差异化**: 12 个学习设计各有学术效应量 (d-value)，通过 narrative synthesis（Cochrane Handbook Ch 12）独立评估守恒度，而非传统 UI 机械对照（Agent G 44.2%）。

**目标用户**: 个人学习者（ROG，CS 61B 学生），使用 Obsidian markdown + wikilinks 构建个人知识图谱，通过 6 个 Claude Code Skill 触发 AI 驱动的学习闭环。

**核心诉求**（用户批注 #8 锁定）: "批注驱动的精确考察" — LLM 读懂 callout 批注 → 生成针对个人的考察 → 用户回答 → 更新掌握度 → 循环。

**技术栈**: Obsidian v1.5+ · Claudian plugin · 10 Obsidian 插件 · FastAPI 后端 · 14 MCP 工具 · 6 Claude Code Skill · Graphiti/Neo4j · LanceDB/bge-m3 · Graphify · Claude API

**灵魂设计**: 检验白板 100% 等价实现（Karpicke 2011, Retrieval Practice d=1.50）— 不可妥协底线。

## Success Criteria

### User Success

- **灵魂标准**: 检验白板提供 100% 等价的 Active Recall 环境（d=1.50）
- **守恒标准**: 12 个学习设计效应量独立保留（9 个 ≥85%，3 个 60-80% 有降级策略，0 个 <50%）
- **交互标准**: 6 个 Skill 通过 hotkey 触发完整学习闭环
- **出题个人化**: 三路融合（Graphiti 个人记忆 + Graphify 知识图谱 + frontmatter 掌握度）

### Business Success

- 完整闭环可走通：贴入笔记 → 知识图谱 → 检验白板 → 错误修正 → 掌握度更新
- Phase 1 骨架 2-3 周内验证灵魂流程
- 三套检索系统协同：Graphify（笔记关系，71x 压缩）+ LanceDB（片段召回）+ Graphiti（个人记忆）

### Technical Success

- FastAPI 后端 + 14 MCP 工具正常运行（Day 1 Spike 验证）
- canvas_agentic_rag LANGGRAPH_AVAILABLE=True（Plan v23 已验证）
- Graphiti 通过 MCP 异步非阻塞写入 Neo4j
- BKT + FSRS + 5 信号融合正确更新 frontmatter 掌握度

### Measurable Outcomes

- 检验白板：exam_boards/*.md 打开时零 wiki/concepts/ 内容泄漏
- Generation Effect：书签式新节点正确归入 wiki/concepts/
- 隐形评分：frontmatter 5 信号更新，用户不感知评分过程
- RAG 管道：Precision@5 ≥ 0.70、Recall@10 ≥ 0.80、MRR@10 ≥ 0.70

## Product Scope

### MVP — Phase 1 骨架 (2-3 周)

**MVP Approach:** Problem-Solving MVP — 验证检验白板灵魂流程能否在 Obsidian 中完整跑通。
**MVP 判定标准:** `/start_exam_board` 完成一次完整 10 步考察，信息隔离 + 静默评分 + 书签式提取全部工作。
**资源:** 单人开发（ROG + Claude Code）。

**Must-Have:**
- vault 初始化（canvas-vault/ + CLAUDE.md + 5 强制插件：Dataview/Templater/QuickAdd/Periodic Notes/Spaced Repetition）
- Claudian 配置 + Canvas 后端启动（14 MCP 工具可调用）
- 3 核心 Skill：`/chat_with_context` (Cmd+Option+C) · `/start_exam_board` (Cmd+Option+E) · `/extract_node` (Cmd+Option+X)
- Templater 模板：exam-board.md · concept.md · edge.md
- Day 1 Spike：后端启动验证 + canvas_agentic_rag import + UserPromptSubmit hook
- context_enrichment 重构：从 .canvas JSON 改为 obsidiantools wikilink 图遍历（降级架构断层修复）
- Graphify 集成（Phase 1 后段）

**Core Journeys Supported:** 旅程 2（检验白板）完整 · 旅程 1（日常学习）基础 · 旅程 4（冷启动）自然

### Growth — Phase 2 学习闭环 (2-4 周)

- 剩余 3 Skill：`/edge_discuss` · `/quiz_from_callout` · `/review_profile`
- Dataview Dashboard（三层布局 + CSS 卡片 + 处方性措辞 + 2x2 校准矩阵）
- 10 插件全装 · Graphify health check · 错误修正闭环（3 天 + 1 周）
- 真实学习 demo（MT2 LLRB 章节）

### Vision — Phase 3 精修 (持续)

- FSRS 插件替换 SM-2 · Canvas↔Graphiti 双向同步 · 校准投票 few-shot 改进
- 元认知 2x2 可视化升级（需 400+ 题） · Graphify cluster 主题发现 · 图片学习增强

## User Journeys

### 旅程 1 · 日常学习（剖析模式）

**核心原理**: Edge 对话 EI+SE (d=0.80-1.00) + Generation Effect (d=0.65)

ROG 做 A* 练习题遇到不懂的点，用 `[!question]+` callout 批注困惑。Claudian 通过 `/chat_with_context` 回答（自动挂载笔记 + search_memories 拉取历史误解）。发现更深知识点 → Cmd+Option+X `/extract_node` → 在批注附近插入 `[[new-concept]]` wikilink + 创建概念 .md 骨架。点击 wikilink 切到新文档 → Claudian 重新挂载检测 `extracted_from` → 进入剖析模式深度讨论 → `/edge_discuss` 探索关系。**守恒 85%**

### 旅程 2 · 检验白板考察（灵魂旅程）

**核心原理**: Retrieval Practice d=1.50 (Karpicke 2011)

Cmd+Option+E → 防嵌套检查 → 选题模式 → `query_mastery` 选弱项 → Templater 生成空白 exam board → Claudian 重置上下文 → `generate_question` 三路融合出题 → md 编辑器手写答案 → Cmd+Option+S 提交 → 静默评分 + BKT/FSRS 更新。考察中发现不懂 → 书签式 `/extract_node`（不切 Tab）→ 考后深度讨论。**守恒 95%**

### 旅程 3 · 错误修正记忆闭环

**核心原理**: Error Correction (Metcalfe 2017) + Spacing Effect d≈0.55

Day 0：标记 `[!fail]+` callout + `record_error` 写入 Graphiti + Tasks 生成提醒。Day 3：Spaced Repetition 弹出 + Claudian 注入历史误解 + `update_fsrs`。Day 7：辨析题考察验证纠正。**守恒 90%**

### 旅程 4 · 新用户冷启动

**核心原理**: Progressive Calibration

安装 vault + 插件 + 后端 → 首次对话无个性化（BKT=0.30）→ 第 5 次 `search_memories` 返回有价值历史 → 第 8 次 `generate_question` 基于错误出题 → 体感"越来越懂我"。**守恒 90%**

### 旅程 5 · 图片密集型学习

**核心原理**: Multi-modal Learning (Mayer 2009) d=0.40-0.60

贴入图片 `![[img.png]]` → Claudian 原生图像识别 → Claude 分析回答。降级：图片不自动持久化到 Graphify。**守恒 70%**

### 旅程 6 · 学习档案浏览

**核心原理**: Formative Feedback d=0.50-0.80 (Hattie 2007)

Cmd+Option+P `/review_profile` 或直接打开 `wiki/dashboard.md`。Dataview 三层布局：Layer 1 原白板卡片（CSS Grid + Buttons 一键考察） · Layer 2 处方性措辞复习建议（🔴🟡🟢） · Layer 3 元认知 2x2 校准矩阵（dataviewjs）。插件栈：Dataview + Buttons + QuickAdd + TfTHacker Dashboard++ CSS + Homepage。**守恒 75%**

### Journey → Capability Mapping

| 旅程 | 核心能力 |
|---|---|
| 1 日常学习 | `/chat_with_context` + `/edge_discuss` + `/extract_node` + context_enrichment |
| 2 检验白板 | `/start_exam_board` + query_mastery + generate_question + score_answer |
| 3 错误修正 | record_error + Spaced Repetition + Tasks + search_memories |
| 4 冷启动 | Claudian + 后端 + 默认 BKT 先验 |
| 5 图片学习 | Claudian 图像识别 |
| 6 档案浏览 | `/review_profile` + Dataview Dashboard + Buttons + QuickAdd |

## Domain-Specific Requirements

### 学习科学合规

领域合规来自**学习科学效应量标准**（非传统 EdTech 法规）：
- 12 个设计各有学术来源和 d-value（PRD v5 §1）
- 每个设计独立评估守恒度（narrative synthesis，Cochrane Handbook Ch 12）
- 9 个 ≥85% 守恒是可行性前提
- 检验白板 d=1.50 不可妥协

### 评估完整性

- **信息隔离**: exam_boards/*.md 不泄漏 wiki/concepts/（§2.4 三重保证）
- **静默评分**: 用户不感知评分过程（Cassady 2002 焦虑防护）
- **个人化出题**: 三路融合（Graphiti + Graphify + frontmatter）
- **校准机制**: 考后投票防 AI 评分偏差

### 数据本地性

所有数据本地存储（vault + Neo4j + LanceDB）。LLM API 是唯一外部数据流出。无云端同步、无数据收集、无遥测。

## Innovation & Novel Patterns

**1. "学习效果守恒"评估范式**: 用 12 个 d-value 替代 UI 机械对照（44.2%），采用 Cochrane Ch 12 narrative synthesis。

**2. Markdown 里的 Active Recall 隔离区**: frontmatter `type: exam_board` 防嵌套 + Claudian 上下文重置 + Skill prompt 禁读 wiki/concepts/ = 三重信息隔离。Obsidian 生态无先例。

**3. 三路数据融合出题**: Graphiti（错误历史）+ Graphify（概念关系，71x 压缩）+ frontmatter（BKT/FSRS）= 个人化题目。

**4. 书签式节点提取**: 考察中 `/extract_node` 不切 Tab，只插 `[!discussion_later]+` 书签。保护 d=1.50 Active Recall + 不丢失 d=0.65 Generation Effect。

**Validation:** Phase 1 检验白板 demo → Phase 2 真实学习验证 → 每个设计增量验证。
**Fallback:** 隔离失败 → `/quiz_from_callout`（d≈1.09）· 三路融合复杂 → Graphiti-only 先行。

## Desktop Application Specific Requirements

### 6 层通信栈

1. **UI**: Obsidian editor + Claudian 侧边栏
2. **Skill**: 6 个 Claude Code Skill（Claudian → Claude Code CLI）
3. **MCP**: 14 工具（Claude Code → FastAPI `/mcp`）— 评估 5 + 记忆 5 + 检索 4
4. **Service**: RAG（4 路融合）· Memory（3 层 fallback）· Scoring
5. **Data**: Neo4j · LanceDB · Obsidian vault
6. **Model**: Claude API · Ollama bge-m3

### Platform & Offline

- **主平台**: macOS M5 Max · Obsidian v1.5+ · Python 3.12+
- **离线可用**: 笔记编辑 · wikilink · Dataview · Graph View · LanceDB 查询 · Spaced Repetition
- **需要网络**: Claude API 对话/出题/评分 · Graphify 索引 · Ollama 首次下载

### 三套检索系统

| 系统 | 搜什么 | 更新机制 | Token 效率 |
|---|---|---|---|
| Graphify | 笔记关系（概念间结构） | 定期手动 `/graphify ./wiki` | 71x 压缩 |
| LanceDB + bge-m3 | 笔记片段（精确段落） | 实时增量（文件保存触发） | 1x |
| Graphiti + Neo4j | 个人记忆（错误/历史/掌握度） | 自动（EventBus + MCP 写入） | N/A |

Graphify 生成独立 graph.json，**不读写**用户 wikilinks。两个图谱互补共存。

### Graphiti 读写时序

**READ（LLM 回答前注入记忆）**: `/chat_with_context` Step 4 · `/start_exam_board` Step 4+7.1 · `/edge_discuss` Step 2 · `/review_profile` Step 2-3
**WRITE（用户操作后异步记录）**: 对话结束 `archive_conversation` · 评分后 EventBus 级联 · 考后 `record_calibration` · 发现错误 `record_error` · Edge 讨论/新节点 `record_learning_memory`

### 错误双存储

- **Obsidian .md**（用户可见）: frontmatter `errors[]` + `[!fail]+` callout + Dataview 查询
- **Graphiti Neo4j**（AI 可见）: 4 类分类（conceptual_confusion / procedural_error / careless_slip / metacognitive_error）+ 修正策略 + session 链接

## Functional Requirements

> **Capability Contract**: 下游工作只做这里列出的功能。

### 学习对话与知识探索

- **FR1**: 学习者可以启动 AI 对话，AI 通过 obsidiantools 解析 `[[wikilinks]]` 发现相邻概念，读取 frontmatter 和内容作为上下文
- **FR2**: 对话中基于个人历史误解主动提醒
- **FR3**: 对话中显示可点击的补充学习材料列表（LanceDB hybrid search）
- **FR4**: 选中关系文本启动 EI+SE 双策略深度讨论
- **FR5**: 对话结束自动归档到 Graphiti

### 考察与评估

- **FR6**: 启动完全空白的检验白板（信息隔离，看不到笔记原文）
- **FR7**: 基于 BKT/FSRS 自动选出薄弱节点
- **FR8**: 三路融合生成个人化题目（Graphiti + Graphify + frontmatter）
- **FR9**: markdown 编辑器手写答案 + 手动触发提交
- **FR10**: 静默评分，结果写入 frontmatter
- **FR11**: 4 级渐进提示（方向 → 关键词 → 框架 → 脚手架）
- **FR12**: 跳过题目不受惩罚
- **FR13**: 基于 callout 批注触发快速考察
- **FR14**: 防嵌套（检验白板内不能再生成检验白板）

### 知识图谱构建

- **FR15**: 提取新概念自动创建 `[[wikilink]]` 双向链接的 .md 文件
- **FR16**: 考察中提取不中断流程（书签式 `[!discussion_later]+`）
- **FR17**: Graphify 从文本自动提取概念关系生成独立 graph.json（不读写用户 wikilinks）
- **FR18**: Graphify 三级置信度标注（EXTRACTED / INFERRED / AMBIGUOUS）

### 掌握度追踪

- **FR19**: BKT 模型实时更新掌握概率
- **FR20**: FSRS 算法计算最优复习间隔
- **FR21**: 5 信号融合（BKT + FSRS + 错误历史 + 校准偏差 + 自评置信度）
- **FR22**: pipeline_token 链防篡改（generate → score → bkt → fsrs → calibration）

### 学习记忆管理

- **FR23**: 错误按 4 类分类存储（Graphiti + frontmatter 双写）
- **FR24**: 记录自我评估校准数据
- **FR25**: 对 AI 评分投票反馈（准确 / 偏高 / 偏低）
- **FR26**: 搜索历史记忆（3 层：Graphiti → Neo4j → 缓存）
- **FR27**: 异步非阻塞写入知识图谱

### 学习进度可视化

- **FR28**: 全局 Dashboard（wiki/dashboard.md，Dataview 三层布局）
- **FR29**: 处方性措辞（"🔴 建议优先复习 X" 而非 "mastery: 0.62"）
- **FR30**: 元认知 2x2 校准矩阵
- **FR31**: Dashboard 一键启动检验白板（Buttons + QuickAdd → Skill）
- **FR32**: 单概念详细档案（5 信号 + Tips + 待纠正 + Edges）

### 间隔复习与错误修正

- **FR33**: Day 3 + Day 7 主动提醒复习误解（Spaced Repetition + Tasks）
- **FR34**: 复习时自动注入历史误解上下文
- **FR35**: 基于历史误解生成辨析题
- **FR36**: 待复习任务列表（含截止日期）

### Vault 管理与配置

- **FR37**: 自定义 Skill hotkey 绑定
- **FR38**: Templater 模板自动生成标准 frontmatter
- **FR39**: Obsidian Git 可选自动备份
- **FR40**: Graphify health check（孤立节点 + 矛盾关系）
- **FR41**: 启动时 hotkey 冲突检测

### 架构适配

- **FR42**: context_enrichment 重构为 obsidiantools wikilink 图遍历（Phase 1 必修）
- **FR43**: wikilink 双向链接邻居发现（替代 .canvas JSON edges）

### Graphiti 可观测性

- **FR44**: Skill 结束时 Claudian 末尾附加 Graphiti 摘要行（N 条记忆 · M 条记录 · 状态）
- **FR45**: vault 内审计日志 `outputs/graphiti-audit.log`（时间戳 + 类型 + 延迟 + 状态）

## Non-Functional Requirements

### Performance

- LLM 出题/评分 < 5s · Dataview 刷新 < 1s · Graphify 全量索引 < 30s
- LanceDB 增量 < 500ms · obsidiantools 图构建 < 2s · wikilink 遍历 < 200ms
- Graphiti search < 3s · Graphiti 写入队列 < 10s

### Data Integrity

- frontmatter 不可因 Skill 异常损坏（pipeline_token 防篡改）
- Graphiti 写入原子性（失败不产生半截数据）
- LLM API 只传 context_enrichment 筛选片段（不传 vault 全文）
- 全部数据本地（vault + Neo4j + LanceDB），无云端同步

### Integration Reliability

- Claudian 故障 → Claude Code CLI 降级
- 14 MCP 工具全部可调用（Day 1 Spike 验证）
- pipeline_token 5 步完整传递
- obsidiantools 图支持热更新
- Graphiti 读写时序：读在 LLM 前，写在操作后（异步）
- EventBus 级联保证评分事件自动触发 Graphiti 写入

### Graceful Degradation

| 故障 | 降级方案 |
|---|---|
| Claudian 挂掉 | Claude Code CLI 直接交互 |
| Claude API 不可用 | 离线阅读/复习/Dashboard |
| Graphiti/Neo4j 不可用 | 无个人化出题（默认先验）+ 🔴 状态指示 |
| Graphify 失败 | 读 frontmatter + wikilinks（损失 71x 压缩） |
| 检验白板隔离失败 | `/quiz_from_callout`（d=1.50 → d≈1.09） |
| Graphiti 写入失败 | 自动重试 3 次 + 审计日志 + Toast 通知 |

### Graphiti 可观测性

- Skill 末尾摘要行：状态可见，分数隐藏（透明度分层）
- 状态栏指示灯（🟢 正常 / 🟡 重试 / 🔴 断开）
- 审计日志全操作记录 · 断开时 Toast 通知
