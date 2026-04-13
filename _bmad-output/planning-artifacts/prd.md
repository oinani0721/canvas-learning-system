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
lastEdited: '2026-04-13'
editHistory:
  - date: '2026-04-13'
    changes: '用户批注反馈: 插件5→3+Bases、edge.md→frontmatter relationships[]、FR-KG-06/FR-SPACE-01更新'
  - date: '2026-04-12'
    changes: 'BMAD 全面重写: 46→103 FR (12 能力域) + 5→9 NFR 类别 (含验证方法) + 新增竞品分析/风险矩阵/废弃FR/决策索引/旅程追溯'
  - date: '2026-04-12'
    changes: '实现泄漏清理: 移除 wikilink 图解析库/Claudian 侧边栏/文件路径等实现细节，转换为能力语言'
inputDocuments:
  - path: '/Users/Heishing/Desktop/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md'
    type: 'prd-source'
    description: 'PRD v5 - Scheme A Learning Effect Conservation PRD (7594 lines, 13 sections, read-only anchor)'
  - path: '_bmad-output/planning-artifacts/prd-tauri-archived-20260401.md'
    type: 'archived-prd'
    description: 'Archived Tauri PRD (971 lines, 12 capability domains, 103 FRs — quality bar reference)'
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

# Product Requirements Document — Canvas Learning System

**Author:** ROG
**Date:** 2026-04-12
**Anchor Source:** PRD v5 (`14-scheme-a-implementation-prd.md`, 7594 lines, read-only)

---

## Executive Summary

> **From PRD**: §0 架构锁定声明 (line 38-113)

Canvas Learning System 是基于 Obsidian + Claudian + Canvas 后端的个人化学习桌面应用。从 Tauri+React 架构转型到 Obsidian Hybrid 部署，追求**学习效果守恒**而非 UI 1:1 还原。

**产品差异化**: 12 个学习设计各有学术效应量 (d-value)，通过 narrative synthesis（Cochrane Handbook Ch 12）独立评估守恒度，而非传统 UI 机械对照（Agent G 44.2%）。

**目标用户**: 个人学习者（ROG，CS 61B 学生），使用 Obsidian markdown + wikilinks 构建个人知识图谱，通过 6 个 Claude Code Skill 触发 AI 驱动的学习闭环。

**核心诉求**（用户批注 #8 锁定）: "批注驱动的精确考察" — LLM 读懂 callout 批注 → 生成针对个人的考察 → 用户回答 → 更新掌握度 → 循环。

**技术栈**: Obsidian v1.5+ · Claudian plugin · 7 Obsidian 插件 + Bases 原生 · FastAPI 后端 · 14 MCP 工具 · 6 Claude Code Skill · Graphiti/Neo4j · LanceDB/bge-m3 · Graphify v0.3.17 · Claude API

**灵魂设计**: 检验白板 100% 等价实现（Karpicke 2011, Retrieval Practice d=1.50）— 不可妥协底线。

**用户决策锁定**（2026-04-08）:
1. 学习效果 > UI 体验
2. 时间充裕 · 架构优先
3. 检验白板不可妥协 · 必须 100% 等价实现
4. Plan v23 scope B + Phase 1 骨架直接启动

---

## Success Criteria

> **From PRD**: §9 学习效果守恒度评估 (line 7120-7232) + §10 分阶段实施路线 (line 7235-7378)

### User Success

| 标准 | 可测量指标 | 验证方法 |
|------|----------|---------|
| 灵魂标准 | 检验白板提供 100% Active Recall 隔离（d=1.50） | exam_boards/*.md 打开时零 wiki/concepts/ 内容泄漏 |
| 守恒标准 | 9 个设计 ≥85% 守恒，3 个 60-80% 有降级策略 | 12 设计逐项评估（narrative synthesis，不给单一数字） |
| 交互标准 | 6 个 Skill 通过 hotkey 完成完整学习闭环 | Cmd+Option+{C,R,E,Q,X,P} 端到端操作 |
| 个人化标准 | 三路融合出题包含个人历史数据 | Precision@5 ≥ 0.70 · Recall@10 ≥ 0.80 · MRR@10 ≥ 0.70 |

### Business Success

| 标准 | 可测量指标 | 验证方法 |
|------|----------|---------|
| 闭环完整 | 笔记 → 图谱 → 考察 → 修正 → 掌握度 | 端到端流程 walkthrough |
| 骨架验证 | Phase 1 骨架 2-3 周内完成 | Day 1 Spike 通过 + 首次考察 demo |
| 检索协同 | 三套系统各有贡献 | Graphify(71x) + LanceDB(片段) + Graphiti(记忆) 各返回结果 |

### Technical Success

| 标准 | 可测量指标 | 验证方法 |
|------|----------|---------|
| 后端就绪 | 14 MCP 工具全部可调用 | Day 1 Spike smoke test |
| RAG 可用 | LANGGRAPH_AVAILABLE=True | Plan v23 已验证 |
| 异步写入 | Graphiti 非阻塞 | 写入不阻塞 Skill 响应 |
| 掌握度融合 | BKT + FSRS + 5 信号正确更新 | frontmatter 字段验证 |

### Differentiation Success

| 标准 | 可测量指标 | 验证方法 |
|------|----------|---------|
| 竞品优势 | 9 组件集成，竞品 max 4/9 | 竞品对比矩阵 |
| 学术根基 | 12 设计全有 d-value | 论文引用验证 |
| 独特交叉 | 检验白板 × 批注出题全球无先例 | 文献搜索 |

---

## Product Scope

> **From PRD**: §10 分阶段实施路线 (line 7235-7378)

### MVP — Phase 1 骨架 (2-3 周)

**MVP Approach:** Problem-Solving MVP — 验证检验白板灵魂流程能否在 Obsidian 中完整跑通。
**MVP 判定标准:** `/start_exam_board` 完成一次完整 10 步考察，信息隔离 + 静默评分 + 书签式提取全部工作。
**资源:** 单人开发（ROG + Claude Code）。

**Must-Have:**
- vault 初始化（canvas-vault/ + CLAUDE.md + 3 强制插件 + Obsidian Bases 原生：Dataview/Templater/QuickAdd + Bases（交互式表格/卡片视图，原生核心插件））
- Claudian 配置 + Canvas 后端启动（14 MCP 工具可调用）
- 3 核心 Skill：`/chat_with_context` · `/start_exam_board` · `/extract_node`
- Templater 模板：exam-board.md · concept.md（relationships[] 在 frontmatter 中）
- **复习调度由后端 FSRS 驱动**：`update_fsrs()` MCP 计算 nextReview/reviewLevel → 写入 frontmatter（权威源），前端只读展示
- Day 1 Spike：后端启动验证 + canvas_agentic_rag import + UserPromptSubmit hook
- context_enrichment 重构为双向链接图遍历（降级架构断层修复）
- Graphify 集成（Phase 1 后段）

**Core Journeys Supported:** 旅程 2（检验白板）完整 · 旅程 1（日常学习）基础 · 旅程 4（冷启动）自然

### Growth — Phase 2 学习闭环 (2-4 周)

- 剩余 3 Skill：`/edge_discuss` · `/quiz_from_callout` · `/review_profile`
- Dataview Dashboard [DECISION-PENDING: dashboard-interactive-ui]（三层布局 + CSS 卡片 + 处方性措辞 + 2x2 校准矩阵。交互式 UI 方案待社区调研：Meta Bind+Dataview+Buttons / Obsidian Bases / Kanban / React Components / Custom CSS）
- 7 插件全装 · Graphify health check · 错误修正闭环（3 天 + 1 周）
- 真实学习 demo（MT2 LLRB 章节）

### Vision — Phase 3 精修 (持续)

- FSRS 插件替换 SM-2 · Canvas↔Graphiti 双向同步 · 校准投票 few-shot 改进
- 元认知 2x2 可视化升级（需 400+ 题）· Graphify cluster 主题发现 · 图片学习增强

---

## User Journeys

> **From PRD**: §8 6 个用户旅程的完整 md 实现 (line 6936-7116)

### 旅程 1 · 日常学习（剖析模式）

**核心原理**: Edge 对话 EI+SE (d=0.80-1.00) + Generation Effect (d=0.65) | **守恒 85%**

ROG 做 A* 练习题遇到不懂的点，用 `[!question]+` callout 批注困惑。Claudian 通过 `/chat_with_context` 回答（自动挂载笔记 + 拉取历史误解）。发现更深知识点 → `/extract_node` 创建新概念 → wikilink 切到新文档 → 进入剖析模式深度讨论 → `/edge_discuss` 探索关系。

### 旅程 2 · 检验白板考察（灵魂旅程）

**核心原理**: Retrieval Practice d=1.50 (Karpicke 2011) | **守恒 95%**

Cmd+Option+E → 防嵌套检查 → 选题模式 → 查询薄弱节点 → 生成空白 exam board → AI 上下文重置 → 三路融合出题 → md 编辑器手写答案 → 手动提交 → 静默评分 + BKT/FSRS 更新。考察中发现不懂 → 书签式节点提取（不切 Tab）→ 考后深度讨论。

### 旅程 3 · 错误修正记忆闭环

**核心原理**: Error Correction (Metcalfe 2017) + Spacing Effect d≈0.55 | **守恒 90%**

Day 0：标记错误 + 写入长期记忆 + 生成复习提醒。Day 3：间隔复习弹出 + 注入历史误解 + 更新记忆。Day 7：辨析题考察验证纠正。

### 旅程 4 · 新用户冷启动

**核心原理**: Progressive Calibration | **守恒 90%**

安装 vault + 插件 + 后端 → 首次对话无个性化（BKT=0.30 先验）→ 第 5 次开始返回有价值历史 → 第 8 次基于错误出题 → 体感"越来越懂我"。

### 旅程 5 · 图片密集型学习

**核心原理**: Multi-modal Learning (Mayer 2009) d=0.40-0.60 | **守恒 70%**（降级）

贴入图片 → AI 原生图像识别 → 分析回答。降级：图片不自动持久化到知识图谱索引。

### 旅程 6 · 学习档案浏览

**核心原理**: Formative Feedback d=0.50-0.80 (Hattie 2007) | **守恒 75%**

查看 Dashboard 三层布局：Layer 1 原白板卡片（一键考察）· Layer 2 处方性措辞复习建议 · Layer 3 元认知 2x2 校准矩阵。

### 旅程 → 能力域追溯映射

| 旅程 | FR-CONV | FR-EDGE | FR-EXAM | FR-KG | FR-MAST | FR-MEM | FR-VIZ | FR-SPACE | FR-SYS | FR-ADAPT | FR-OBS | FR-MM |
|------|---------|---------|---------|-------|---------|--------|--------|----------|--------|----------|--------|-------|
| 1 日常学习 | ●01-06 | ●01-04 | | ●01-03 | | ●01,05 | | | | ●01-02 | ●01 | |
| 2 检验白板 | | | ●01-22 | ●04-05 | ●01-06 | ●01-04 | ●05 | | ●02 | ●01-02 | ●01-03 | |
| 3 错误修正 | ●02 | | | | ●01-02 | ●01-04 | | ●01-04 | | | ●01 | |
| 4 冷启动 | ●01 | | | | | ●05 | | | ●01,06 | ●01-03 | | |
| 5 图片学习 | ●01 | | | | | | | | | | | ●01-03 |
| 6 档案浏览 | | | | | ●06 | | ●01-06 | ●04 | | | ●01 | |

---

## Domain-Specific Requirements

> **From PRD**: §1 12 个学习设计 (line 116-2743) + §9 守恒度评估 (line 7120-7232)

### 学习科学合规

领域合规来自**学习科学效应量标准**（非传统 EdTech 法规）。12 个设计各有学术来源和 d-value，每个设计独立评估守恒度。

**方法论声明**（Plan v19 修正）：本 PRD 采用 Cochrane Handbook Ch 12 叙述综合，不给出单一加权守恒百分比。Cohen's d 非线性不可直接加权。

| # | 学习设计 | d-value | 守恒率 | 状态 | 学术来源 |
|---|---------|---------|--------|------|---------|
| 1 | 原白板 vs 检验白板二分法 | 1.50 | 95% | ✅ 灵魂 | Karpicke & Blunt 2011 |
| 2 | 拉出新节点交互 | 0.65 | 95% | ✅ 灵魂 | Slamecka & Graf 1978 |
| 3 | Edge 对话 EI+SE 双策略 | 0.80-1.00 | 75% | ⚠️ 部分 | Dunlosky et al. 2013 |
| 4 | 4 维 4 分制评分双框架 | 0.70 | 85% | ✅ | Black & Wiliam 1998 |
| 5 | BKT + FSRS + 5 信号融合 | 1.00 | 95% | ✅ 灵魂 | Corbett & Anderson 1994 |
| 6 | 节点切换时隐形评分 | 0.40 | 70% | ⚠️ 部分 | Cassady & Johnson 2002 |
| 7 | 节点颜色处方性措辞 | 0.50-0.80 | 75% | ⚠️ 部分 | Shute 2008 |
| 8 | 3 天 + 1 周主动提醒 | 0.55 | 90% | ✅ | Cepeda et al. 2006 |
| 9 | 4 级渐进提示 | 0.70 | 90% | ✅ | Hsu et al. 2025 |
| 10 | 元认知 2x2 校准矩阵 | 0.60 | 85% | ✅ | Kruger & Dunning 1999 |
| 11 | 考后校准投票 | 0.50 | 85% | ✅ | Nelson & Narens 1990 |
| 12 | 学习档案正面措辞 | 0.40-0.60 | 100% | ✅ 灵魂 | Dweck 2006 |

### 评估完整性

- **信息隔离**: 检验白板打开时零笔记原文泄漏（三重保证机制）
- **静默评分**: 学习者不感知评分过程（Cassady 2002 焦虑防护）
- **个人化出题**: 三路融合（Graphiti 个人记忆 + Graphify 知识图谱 + frontmatter 掌握度）
- **校准机制**: 考后投票防 AI 评分偏差

### 数据本地性

所有数据本地存储（vault + Neo4j + LanceDB）。LLM API 是唯一外部数据流出。无云端同步、无数据收集、无遥测。

---

## Innovation & Novel Patterns

> **From PRD**: §0.1 哲学 (line 40-56) + §9.5 对比 (line 7222)

**1. "学习效果守恒"评估范式**: 用 12 个 d-value 替代 UI 机械对照（44.2%），采用 Cochrane Ch 12 narrative synthesis。

**2. Markdown 里的 Active Recall 隔离区**: frontmatter type 防嵌套 + AI 上下文重置 + Skill prompt 禁读笔记 = 三重信息隔离。Obsidian 生态无先例。

**3. 三路数据融合出题**: Graphiti（错误历史）+ Graphify（概念关系，71x 压缩）+ frontmatter（BKT/FSRS）= 个人化题目。

**4. 书签式节点提取**: 考察中提取新概念不切 Tab，只插书签标记。保护 d=1.50 Active Recall + 不丢失 d=0.65 Generation Effect。

**Validation:** Phase 1 检验白板 demo → Phase 2 真实学习验证 → 每个设计增量验证。
**Fallback:** 隔离失败 → callout 快速考察（d≈1.09）· 三路融合复杂 → Graphiti-only 先行。

### 竞品分析

| 组件 | Canvas | Anki | Duolingo | RemNote | Math Academy |
|------|--------|------|----------|---------|-------------|
| 视觉知识图谱 | ✅ | ❌ | ❌ | ⚠️ | ❌ |
| AI 节点对话 | ✅ | ❌ | ❌ | ⚠️ | ❌ |
| 精通度追踪 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 间隔复习 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 检验白板 | ✅ | ❌ | ❌ | ❌ | ⚠️ |
| 元认知校准 | ✅ | ❌ | ❌ | ❌ | ✅ |
| 错误修正闭环 | ✅ | ❌ | ⚠️ | ❌ | ✅ |
| 可检视学习模型 | ✅ | ❌ | ❌ | ❌ | ⚠️ |
| 批注驱动出题 | ✅ | ❌ | ❌ | ❌ | ❌ |
| **覆盖率** | **9/9** | **2/9** | **2/9** | **2/9** | **4/9** |

无现有产品同时集成全部 9 个组件。Math Academy 最接近（4/9），但缺少知识图谱、AI 对话和批注驱动出题。

---

## Desktop Application Specific Requirements

> **From PRD**: §0.3 组件清单 (line 69-78) + §5 插件 (line 4841-5750) + §7 MCP 工具 (line 6159-6937)

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

### Update Strategy

- **Obsidian + 7 插件**: 应用内自动更新
- **Canvas 后端**: `git pull` + `uv sync`（手动，版本控制）
- **Graphify**: `pip install --upgrade graphifyy`（手动）
- **Neo4j / Ollama**: Docker 容器更新（手动）
- **Obsidian vault 数据**: Obsidian Git 插件可选自动备份

### 三套检索系统

| 系统 | 搜什么 | 更新机制 | Token 效率 |
|------|--------|---------|-----------|
| Graphify | 笔记关系（概念间结构） | 定期手动触发 | 71x 压缩 |
| LanceDB + bge-m3 | 笔记片段（精确段落） | 实时增量（文件保存触发） | 1x |
| Graphiti + Neo4j | 个人记忆（错误/历史/掌握度） | 自动（EventBus + MCP 写入） | N/A |

### Graphiti 读写时序

**READ（LLM 回答前注入记忆）**: 对话启动 · 考察选题 · 考察出题 · 关系讨论 · 档案浏览
**WRITE（用户操作后异步记录）**: 对话归档 · 评分级联 · 考后校准 · 错误记录 · 关系讨论/新节点

### 错误双存储

- **Obsidian .md**（用户可见）: frontmatter `errors[]` + `[!fail]+` callout + Dataview 查询
- **Graphiti Neo4j**（AI 可见）: 4 类分类 + 修正策略 + session 链接

---

## Functional Requirements

> **Capability Contract**: 下游工作只做这里列出的功能。UX 只设计这些能力，架构只支持这些能力，Epic 只实现这些能力。每项需求只描述 WHO 和 WHAT，不描述 HOW。

### 能力域分组

| 分组 | 能力域 | 说明 |
|------|--------|------|
| **核心学习** | 1 对话 · 2 Edge · 3 考察 · 4 知识图谱 · 5 掌握度 · 6 记忆 | 直接影响学习体验 |
| **展示与调度** | 7 可视化 · 8 间隔复习 | 学习循环辅助 |
| **系统运维** | 9 Vault 管理 · 10 架构适配 · 11 可观测性 · 12 多模态 | 系统基础设施 |

---

### 能力域 1：学习对话与知识探索 (FR-CONV)

> **From PRD**: §4.1 /chat_with_context (line 3647-3898) + §8.1 旅程 1 (line 6940-6965)

| ID | 功能需求 | Enables |
|----|---------|---------|
| FR-CONV-01 | 学习者可以启动 AI 对话，系统自动发现当前笔记的相邻概念并注入对话上下文 | 旅程 1,4 |
| FR-CONV-02 | 系统可以在对话中基于个人历史误解主动提醒学习者（从长期记忆检索相关错误） | 旅程 1,3 |
| FR-CONV-03 | 学习者可以在对话回答中看到可点击的补充学习材料列表（语义搜索结果） | 旅程 1 |
| FR-CONV-04 | 对话上下文自动注入当前笔记的 1-hop 邻居信息（Tips、错误记录、Edge 理由、掌握度） | 旅程 1 |
| FR-CONV-05 | 学习者可以在对话中通过 callout 批注标记关键知识点（Tips） | 旅程 1 |
| FR-CONV-06 | 系统自动从对话中提取、分类并归档学习者的错误（4 主类：概念混淆/推理谬误/粗心/元认知，含 2 子类） | 旅程 1 |
| FR-CONV-07 | 系统可以在对话结束时自动归档会话到长期记忆 | 旅程 1 |
| FR-CONV-08 | 学习者可以从对话中选取内容提取为新的知识节点，系统自动建议与原节点的关系 | 旅程 1 |
| FR-CONV-09 | 对话消息按时间进行三层归档（完整保留 → 摘要+提取 → 仅提取） | 旅程 1 |
| FR-CONV-10 | 系统可以通过 Edge 语义检索相关的前序笔记讨论摘要，自动注入新笔记对话上下文 | 旅程 1 |
| FR-CONV-11 | 系统可以在上下文压缩时保留关键学习数据（Tips、错误记录、掌握度状态）并通知学习者 | 旅程 1 |

### 能力域 2：Edge 对话 (FR-EDGE)

> **From PRD**: §1.3 Edge 对话 EI+SE (line 374-502) + §4.2 /edge_discuss (line 3899-3942)

| ID | 功能需求 | Enables |
|----|---------|---------|
| FR-EDGE-01 | 学习者可以选中两个概念之间的关系启动深度讨论 | 旅程 1 |
| FR-EDGE-02 | 系统在 Edge 讨论中同时激活精细化追问（EI）和自我解释（SE）两种学习策略 | 旅程 1 |
| FR-EDGE-03 | 系统记录学习者对关系的解释理由，存储为结构化的语义标签 | 旅程 1 |
| FR-EDGE-04 | Edge 讨论自动注入两端概念的掌握度和历史记忆作为讨论上下文 | 旅程 1 |

### 能力域 3：考察与评估 (FR-EXAM)

> **From PRD**: §2 检验白板 100% 等价实现 (line 905-2743) + §4.3-4.4 Skills (line 3943-4254)

| ID | 功能需求 | Enables |
|----|---------|---------|
| FR-EXAM-01 | 学习者可以基于已有知识白板生成完全空白的检验白板考察（信息隔离，看不到笔记原文） | 旅程 2 |
| FR-EXAM-02 | 系统可以基于 BKT/FSRS 掌握度分数自动选出薄弱节点作为考察范围 | 旅程 2 |
| FR-EXAM-03 | 系统可以融合个人记忆、知识图谱关系和掌握度数据生成个人化题目 | 旅程 2 |
| FR-EXAM-04 | 系统可以对学习者回答进行 4 维 4 分制评分（概念准确/推理质量/知识覆盖/知识整合） | 旅程 2 |
| FR-EXAM-05 | 学习者可以在 markdown 编辑器中手写答案并手动触发提交（D14 用户锁定：答题即批注） | 旅程 2 |
| FR-EXAM-06 | 系统可以静默评分（学习者不感知评分过程），结果更新掌握度数据 | 旅程 2 |
| FR-EXAM-07 | 学习者可以在答不出时请求 4 级渐进提示（方向 → 关键词 → 框架 → 脚手架） | 旅程 2 |
| FR-EXAM-08 | 学习者可以跳过题目且不受惩罚（标记为未作答，不影响掌握度） | 旅程 2 |
| FR-EXAM-09 | 学习者可以基于笔记中的 callout 批注触发快速考察（批注驱动出题） | 旅程 2 |
| FR-EXAM-10 | 系统可以防止在检验白板内再次生成检验白板（防嵌套） | 旅程 2 |
| FR-EXAM-11 | 检验白板支持三种考察模式：点对点突破 · 综合题考察 · 混合模式 | 旅程 2 |
| FR-EXAM-12 | 系统根据知识白板内容类型自动推荐考察模式，学习者可手动覆盖 | 旅程 2 |
| FR-EXAM-13 | 系统按白板类型定制出题策略：知识点侧重定义辨析，题目侧重易错点和破题方法 | 旅程 2 |
| FR-EXAM-14 | 考察过程中学习者可从讨论中提取新概念而不中断当前考察流程（书签式提取） | 旅程 2 |
| FR-EXAM-15 | 评分后系统在话题切换时询问"你觉得评分准确吗"（可选），学习者可反馈偏高/偏低/准确 | 旅程 2 |
| FR-EXAM-16 | 系统在节点切换时自动触发后台评分并更新掌握度，学习者不感知（Flow 保护） | 旅程 2 |
| FR-EXAM-17 | 检验白板中的所有数据变更（Tips/新节点/掌握度）同步回源知识白板 | 旅程 2 |
| FR-EXAM-18 | 每个检验白板的完整考察记录永久保存，学习者可在 Dashboard 查看历史 | 旅程 2,6 |
| FR-EXAM-19 | AI 出题难度匹配学习者当前掌握度（连续 IRT difficulty，非离散分级），匹配率 ≥ 70% | 旅程 2 |
| FR-EXAM-20 | 考察中学习者确认的新节点可继续被深入讨论（用户驱动终止） | 旅程 2 |
| FR-EXAM-21 | 同一知识白板可生成不限数量的检验白板 | 旅程 2 |
| FR-EXAM-22 | 检验白板的信息隔离采用三重保证机制（文件类型标记 + AI 上下文重置 + Skill prompt 约束） | 旅程 2 |

### 能力域 4：知识图谱构建 (FR-KG)

> **From PRD**: §1.2 Generation Effect (line 277-373) + §3 目录结构 (line 3258-3461) + §6 Graphify (line 5815-6158)

| ID | 功能需求 | Enables |
|----|---------|---------|
| FR-KG-01 | 学习者可以通过双向链接创建概念间的关系，系统自动维护链接完整性 | 旅程 1 |
| FR-KG-02 | 学习者可以从对话或考察中提取新概念，系统自动创建双向链接的概念文件 | 旅程 1,2 |
| FR-KG-03 | 系统可以从笔记文本中自动提取概念关系，生成独立 AI 检索索引（不修改用户的双向链接） | 旅程 1 |
| FR-KG-04 | 系统可以在考察中提取新概念时不中断当前流程（书签式标记，考后再深度讨论） | 旅程 2 |
| FR-KG-05 | 系统可以为自动提取的每个概念标注三级置信度（EXTRACTED / INFERRED / AMBIGUOUS） | 旅程 1 |
| FR-KG-06 | 学习者可以在概念文件的 frontmatter relationships[] 中记录概念间关系，存储语义类型和讨论历史 | 旅程 1 |
| FR-KG-07 | 系统可以通过概念关系图提供补充学习材料（71x token 压缩检索） | 旅程 1,2 |
| FR-KG-08 | 系统可以定期检查知识图谱健康状况（孤立节点、矛盾关系、置信度分布） | 旅程 1 |
| FR-KG-09 | 学习者可以在粘贴图片时让 AI 识别并将图片内容纳入知识图谱上下文 | 旅程 5 |

### 能力域 5：掌握度追踪 (FR-MAST)

> **From PRD**: §1.5 BKT+FSRS+5信号融合 (line 599-681) + §7 MCP 工具 (line 6159-6937)

| ID | 功能需求 | Enables |
|----|---------|---------|
| FR-MAST-01 | 系统可以使用 BKT 模型实时更新每个概念的掌握概率 | 旅程 2,3 |
| FR-MAST-02 | 系统可以使用 FSRS 算法计算最优复习间隔 | 旅程 3 |
| FR-MAST-03 | 系统可以维护 5 信号融合的掌握度评估（BKT + FSRS + 错误历史 + 校准偏差 + 自评置信度） | 旅程 2 |
| FR-MAST-04 | 系统可以保证评分操作链的顺序完整性（出题 → 评分 → BKT → FSRS → 校准 不可跳步） | 旅程 2 |
| FR-MAST-05 | 系统可以通过 2x2 置信度矩阵追踪学习者元认知校准（答前自评 vs 实际表现）。三阶段：<100 题仅收集 / 100-400 趋势参考 / 400+ 统计可靠 | 旅程 2,6 |
| FR-MAST-06 | 掌握度仅通过考察表现更新（非自评直接修改），信号互补性 r < 0.7，融合后 Spearman rho > 0.6 | 旅程 2 |

### 能力域 6：学习记忆管理 (FR-MEM)

> **From PRD**: §7 MCP 工具 (line 6159-6937) + §8.3 旅程 3 (line 7012-7021)

| ID | 功能需求 | Enables |
|----|---------|---------|
| FR-MEM-01 | 系统可以记录学习者的错误并按 4 类分类存储（本地文件 + 知识图谱双写） | 旅程 1,2,3 |
| FR-MEM-02 | 系统可以记录学习者的自我评估校准数据（考后校准投票） | 旅程 2 |
| FR-MEM-03 | 学习者可以对 AI 评分投票反馈（准确 / 偏高 / 偏低），标记为 few-shot 校准样本 | 旅程 2 |
| FR-MEM-04 | 系统可以搜索学习者的历史记忆（3 层检索：知识图谱 → 图数据库 → 缓存） | 旅程 1,2,3 |
| FR-MEM-05 | 系统可以异步非阻塞地将学习事件写入知识图谱 | 旅程 1,2,4 |
| FR-MEM-06 | 对话消息按时间分层归档（Hot 0-30d 完整 → Warm 30-180d 摘要 → Cold 180d+ 仅提取） | 旅程 1 |

### 能力域 7：学习进度可视化 (FR-VIZ)

> **From PRD**: §5.1.1 Dashboard 设计 (line 4880-5185) + §8.6 旅程 6 (line 7083-7116)

| ID | 功能需求 | Enables |
|----|---------|---------|
| FR-VIZ-01 | 学习者可以查看全局 Dashboard（三层布局：原白板卡片 · 考察历史 · 分析链） | 旅程 6 |
| FR-VIZ-02 | 系统可以使用处方性措辞展示学习状态（"建议优先复习 X" 而非 "mastery: 0.62"） | 旅程 6 |
| FR-VIZ-03 | 学习者可以查看元认知 2x2 校准矩阵（会+自信 / 会+不自信 / 不会+自信 / 不会+不自信） | 旅程 6 |
| FR-VIZ-04 | 学习者可以从 Dashboard 一键启动指定主题的检验白板 | 旅程 6 |
| FR-VIZ-05 | 学习者可以查看单个概念的详细档案（5 信号 + Tips + 待纠正 + 相关 Edges） | 旅程 2,6 |
| FR-VIZ-06 | 学习档案的措辞使用"建议加强/可以改进"而非"错误/失败/不合格" | 旅程 6 |

### 能力域 8：间隔复习与错误修正 (FR-SPACE)

> **From PRD**: §1.8 间隔复习 (line 2824-2932) + §8.3 旅程 3 (line 7012-7021)

| ID | 功能需求 | Enables |
|----|---------|---------|
| FR-SPACE-01 | 系统可以通过 Dashboard 的 NextReview 查询 + Bases 表格过滤提醒学习者复习标记的误解 | 旅程 3 |
| FR-SPACE-02 | 系统可以在复习时自动注入历史误解上下文 | 旅程 3 |
| FR-SPACE-03 | 系统可以基于历史误解生成辨析题验证纠正效果 | 旅程 3 |
| FR-SPACE-04 | 学习者可以查看待完成的复习任务列表（含截止日期和优先级） | 旅程 3,6 |
| FR-SPACE-05 | 系统可以基于 FSRS 算法安排复习时机，复习间隔随掌握度自适应 | 旅程 3 |

### 能力域 9：Vault 管理与配置 (FR-SYS)

> **From PRD**: §3 目录结构 (line 3258-3461) + §5 插件 (line 4841-5750)

| ID | 功能需求 | Enables |
|----|---------|---------|
| FR-SYS-01 | 学习者可以通过模板自动生成考察文件、概念文件和边文件的标准化结构 | 旅程 1,2 |
| FR-SYS-02 | 学习者可以自定义所有 Skill 的 hotkey 绑定 | 旅程 1-6 |
| FR-SYS-03 | 学习者可以选择性启用自动备份（版本控制） | 旅程 1-6 |
| FR-SYS-04 | 系统可以在启动时检测 hotkey 冲突并警告 | 旅程 1-6 |
| FR-SYS-05 | 系统可以执行知识图谱索引的健康检查并报告问题 | 旅程 1 |
| FR-SYS-06 | 首次使用时系统提供安装引导，逐步检测并完成依赖配置 | 旅程 4 |

### 能力域 10：架构适配 (FR-ADAPT)

> **From PRD**: §7.6 后端服务清单 (line 6628-6936) | **Phase 1 scope**

| ID | 功能需求 | Enables |
|----|---------|---------|
| FR-ADAPT-01 | 系统可以通过双向链接图遍历发现概念间的邻居关系（替代原有 JSON 结构） | 旅程 1,2 |
| FR-ADAPT-02 | 系统可以基于双向链接图为 AI 对话组装完整上下文包（邻居笔记 + Tips + Edges + 错误） | 旅程 1,2 |
| FR-ADAPT-03 | 双向链接图支持热更新（文件变更时增量重建，非全量） | 旅程 1,2 |

### 能力域 11：可观测性 (FR-OBS)

> **From PRD**: §7 Graphiti 读写时序 (line 6275-6627)

| ID | 功能需求 | Enables |
|----|---------|---------|
| FR-OBS-01 | 系统可以在每次对话/考察结束时展示记忆操作摘要（已加载 N 条 · 已保存 M 条 · 连接状态） | 旅程 1,2,3,6 |
| FR-OBS-02 | 系统可以展示知识图谱连接状态（正常 / 重试中 / 断开） | 旅程 1,2 |
| FR-OBS-03 | 系统可以维护操作审计日志（时间戳 + 类型 + 目标 + 延迟 + 状态） | 旅程 2 |
| FR-OBS-04 | 系统可以在知识图谱写入失败时通知学习者并自动重试 | 旅程 1,2 |

### 能力域 12：多模态学习 (FR-MM)

> **From PRD**: §8.5 旅程 5 (line 7046-7069)

| ID | 功能需求 | Enables |
|----|---------|---------|
| FR-MM-01 | 系统可以识别笔记中嵌入的图片并将图片内容纳入 AI 对话上下文 | 旅程 5 |
| FR-MM-02 | 学习者可以基于图片内容发起 AI 对话讨论 | 旅程 5 |
| FR-MM-03 | 系统可以从图片中提取的概念信息在考察时作为出题素材（降级：不自动持久化到索引） | 旅程 5 |

---

**FR 统计**: 12 能力域 · 85 条活跃需求 + 8 条废弃（FR-CONV:11 · FR-EDGE:4 · FR-EXAM:22 · FR-KG:9 · FR-MAST:6 · FR-MEM:6 · FR-VIZ:6 · FR-SPACE:5 · FR-SYS:6 · FR-ADAPT:3 · FR-OBS:4 · FR-MM:3 · 废弃:8 见附录 A）

> **与旧 PRD 对比**: 旧版 103 条中 18 条因架构转型（Tauri→Obsidian Hybrid）废弃或合并，净增 0 条新 FR（架构适配 FR-ADAPT 3 条为新增）。

---

## Non-Functional Requirements

### 性能

| 指标 | 目标值 | 测试场景 | 验证方法 |
|------|--------|---------|---------|
| LLM 出题/评分 | < 5s P95 | 10 次连续出题 | 测量 Skill 触发到 AI 响应完成的 P95 延迟 |
| Dashboard 刷新 | < 1s | 100 个概念文件 | Dataview 查询执行到 UI 渲染完成 |
| Graphify 全量索引 | < 30s | wiki/ ~100 文件 | CLI 输出时间戳 start→finish |
| LanceDB 增量索引 | < 500ms/file | 单文件保存后 | 后端日志 reindex_start→reindex_end |
| Vault 图构建 | < 2s | ~200 文件 + ~500 wikilinks | 后端启动日志 graph_build_start→done |
| 图遍历查询 | < 200ms | N-hop query, N≤3 | context_enrichment 延迟日志 |
| 记忆搜索 | < 3s | 3 层检索 | MCP 响应计时 request→response |
| 记忆写入 | < 10s/episode | 单条学习事件 | episode_worker 日志 |

### 数据完整性

| 指标 | 目标值 | 测试场景 | 验证方法 |
|------|--------|---------|---------|
| Frontmatter 安全 | 零损坏 | Skill 异常中断 | 操作链防篡改验证 + 异常注入测试 |
| 写入原子性 | 零半截数据 | 写入过程中断 | 模拟写入中断 → 验证无残留数据 |
| 数据本地性 | 100% 本地 | 全部操作 | 网络审计：仅 LLM API + 配置域名 |
| 隐私保护 | 不传 vault 全文 | AI 对话 | 仅传 context_enrichment 筛选片段 |

### 集成可靠性

| 指标 | 目标值 | 测试场景 | 验证方法 |
|------|--------|---------|---------|
| MCP 可用率 | 14/14 工具可调用 | Day 1 Spike | 逐工具 smoke test |
| 评分链完整 | 5 步不跳步 | 完整考察 | 验证 pipeline_token 5 步传递 |
| 图热更新 | 文件变更 < 5s 反映 | 编辑 .md + 保存 | 观察图遍历结果变化 |
| 读写时序 | READ 在 LLM 前，WRITE 在操作后 | 完整对话/考察流程 | 日志时序验证 |
| 级联触发 | 评分自动触发记忆写入 | 完成一题评分 | 验证 EventBus 触发 + 记忆写入成功 |

### 优雅降级

| 故障 | 降级方案 | 验证方法 |
|------|---------|---------|
| AI 插件挂掉 | CLI 直接交互 | 模拟插件崩溃 → 验证 CLI 可用 |
| Claude API 不可用 | 离线阅读/复习/Dashboard | 断网 → 验证离线功能 |
| Graphiti/Neo4j 不可用 | 无个性化出题（默认先验）+ 状态指示 | 停 Neo4j → 验证降级 |
| Graphify 失败 | 读 frontmatter + wikilinks（损失 71x 压缩） | 删 graph.json → 验证降级 |
| 检验白板隔离失败 | callout 快速考察（d=1.50 → d≈1.09） | 模拟隔离漏洞 → 验证 fallback |
| 记忆写入失败 | 自动重试 3 次 + 审计日志 + 通知 | 模拟写入超时 → 验证重试 |

### 可观测性

| 指标 | 目标值 | 测试场景 | 验证方法 |
|------|--------|---------|---------|
| Skill 末尾摘要 | 每次交互可见 | 对话/考察结束 | 验证摘要行出现（状态可见，分数隐藏） |
| 连接状态 | 实时 🟢🟡🔴 指示 | 正常/重试/断开 | 模拟各状态 → 验证指示器变化 |
| 审计日志 | 全操作记录 | 10 次混合操作 | 验证日志覆盖率 100% |
| 断开通知 | < 5s 弹出 | 断开 Neo4j | 验证通知延迟 |

### 安全与隐私

| 维度 | 要求 | 验证方法 |
|------|------|---------|
| 数据本地化 | 所有学习数据存储在本地，不上传外部服务 | 网络审计：出站仅允许 LLM API 域名 |
| API Key 安全 | 加密存储（OS keychain 优先），日志自动脱敏 | 代码审查确认无明文 Key |
| 本地通信 | 前端-后端通信绑定 127.0.0.1 | 端口扫描验证仅监听 localhost |
| Prompt 注入防护 | system/user 消息隔离 + 输出过滤 | 注入测试集 (≥10 种攻击) 拦截率 ≥ 90% |
| 无遥测 | 零数据收集、零追踪 | 代码审查 + 网络审计 |

### 无障碍

| 维度 | 要求 | 验证方法 |
|------|------|---------|
| 键盘导航 | 所有核心操作可通过 hotkey 完成（6 Skill + Obsidian 原生快捷键） | 纯键盘完成一次完整学习流程 |
| 颜色对比 | 文本与背景对比度 ≥ 4.5:1（WCAG 2.1 AA） | Obsidian 主题对比度检测 |
| 处方性颜色 | 掌握度颜色不仅靠色相区分（🔴🟡🟢 + 文字说明） | 色盲模拟验证 |

### 兼容性

| 维度 | 要求 | 验证方法 |
|------|------|---------|
| Obsidian | v1.5+（Community plugins API stable） | 插件安装 + 功能 smoke test |
| macOS | M-series (ARM64)，macOS 12+ | 主开发环境验证 |
| Python | 3.12+（asyncio.TaskGroup 支持） | 后端启动验证 |
| Neo4j | Community 5.x | bolt:// 连接 + 图查询验证 |
| Ollama | latest（bge-m3 模型支持） | 模型加载 + embedding 验证 |
| Claude API | 最新稳定版 | API 调用 + 响应验证 |

### 可维护性

| 维度 | 要求 | 验证方法 |
|------|------|---------|
| MCP 接口契约 | schema 验证覆盖率 100% | 每个 MCP 工具有 schema 定义 + CI 自动验证 |
| Prompt 回归 | 标准测试集 ≥ 20 题，变更后一致率 ≥ 80% | 模板变更触发回归测试 |
| 算法单元测试 | BKT/FSRS/融合/ACP 核心模块覆盖率 ≥ 90% | CI 报告覆盖率 |
| 集成测试 | 评分 → 掌握度 → FSRS 端到端管道 100% 通过 | CI 端到端测试 |

---

## 风险缓释矩阵

| 风险类型 | 具体风险 | 概率 | 影响 | 缓解方案 | 状态 |
|---------|---------|------|------|---------|------|
| 技术 | 三重信息隔离在 Obsidian 中实现不完整 | 中 | 极高 | Phase 1 首日验证 · fallback: callout 考察 (d≈1.09) | 待验证 |
| 技术 | Graphiti 写入延迟影响学习体验 | 低 | 中 | 异步非阻塞 · 重试 3 次 · 降级到默认先验 | 已设计 |
| 技术 | context_enrichment 重构复杂度超预期 | 中 | 高 | Phase 1 优先处理 · 双向链接图遍历方案已调研 | 进行中 |
| 学习科学 | d=1.50 Active Recall 在 md 编辑器中效果打折 | 低 | 极高 | D14 用户哲学选择 · md 答题 = 批注延伸 · 真实测试验证 | D14 锁定 |
| 体验 | AI 评分不准导致校准失效 | 中 | 高 | 先验证评分可靠性 · few-shot 校准 · 用户反馈投票 | 待验证 |
| 资源 | 单人开发进度不足 | 中 | 中 | Phase 分阶段 · 优先灵魂功能 · Claude Code 辅助 | 持续 |

---

## 附录 A：已废弃的功能需求

| 旧 ID | 原内容 | 废弃原因 |
|--------|--------|---------|
| FR-KG-03 (旧) | 白板上拖拽节点和连线，缩放平移 < 16ms | 架构转型：Obsidian 不支持自定义白板操作 |
| FR-CONV-09 (旧) | 切换节点时后台继续生成，并发上限 3 个 | 架构转型：Claudian 单会话模型 |
| FR-EXAM-07 (旧) | 检验白板继承原白板所有基础功能 | 架构转型：无 ReactFlow 白板基础功能 |
| FR-EXAM-08 (旧) | 考察计时功能 | 决策 GDA-5 移除计时 |
| FR-EXAM-09 (旧) | 手动拉出节点不受数量限制 | 已合并至 FR-EXAM-14（书签式提取） |
| FR-EXAM-10 (旧) | 考后审查面板 | 用 Dashboard 历史替代 |
| FR-AGENT-01~03 (旧) | Agent Sidecar 进程 + per-node Session | 架构转型：改为 Claude Code Skill 模型 |
| FR-SYS-08~09 (旧) | 切换 Agent 订阅账号 / 对话中切换 LLM | 架构转型：Claude API 统一 |

---

## 附录 B：决策点索引 (D1-D14)

> **From PRD**: §12 决策点清单 + 批注区 (line 7460-7504)

### D1-D9 继承自 v11-v2

| D# | 决策 | 选项 | AI 建议 | 状态 |
|----|------|------|---------|------|
| D1 | vault 位置 | (a) 扩展 CS 61B/ / (b) 新建 canvas-vault/ | **(b)** | ☐ 待确认 |
| D2 | raw_notes/ 迁移 | (a) 一次性 / (b) 渐进 | **(b)** | ☐ 待确认 |
| D3 | Neo4j/LanceDB/Graphiti | 强制保留 | 继承 | ✅ 锁定 |
| D4 | Skill ↔ MCP 职责 | (a) Skill 管 I/O, MCP 管算法 / (b) 全面重写 | **(a)** | ☐ 待确认 |
| D5 | 历史数据处理 | (a) 保留 / (b) 迁移 / (c) 双向链接+查询 | **(c)** | ☐ 待确认 |
| D6 | Hotkey 绑定 | 6 × Cmd+Option+{C,R,E,Q,X,P} | 已定 | ☐ 待确认 |
| D7 | Phase 1 测试对象 | (a) LLRB / (b) asymptotics / (c) 自选 | **(a)** | ☐ 待确认 |
| D8 | OpenSpec 流程 | (a) CLI / (b) 非正式 Plan | **(a)** | ☐ 待确认 |
| D9 | 权重公式 | (1) FSRS / (2) 双因子 / (3) 数据驱动 | **(1)** | ☐ 待确认 |

### D10-D14 新增

| D# | 决策 | 选项 | AI 建议 | 状态 |
|----|------|------|---------|------|
| D10 | 最小插件集 vs 完整 | (a) Phase 1 装 5 个 / (b) 立即装 10 个 | **(a)** | ☐ 待确认 |
| D11 | SM-2 vs FSRS 插件 | (a) SM-2 先行 / (b) 等 FSRS 稳定 | **(a)** | ☐ 待确认 |
| D12 | Phase 1 后立即测试 | (a) 立即 / (b) 等 Phase 3 | **(a)** | ☐ 待确认 |
| D13 | Graphify 自动注入 | (a) 自动 / (b) 手动 | **(a)** | ☐ 待确认 |
| D14 | 答题媒介 | (a) Chat / **(b) md 编辑器** / (c) 混合 | **(b)** | ☑ **锁定** |

> **D14 哲学选择**：用户原话"这样回答问题就好比打批注"。答题 = 批注的延伸 → md 文件永久保留 → Karpathy "write stuff down" → 批注驱动闭环（批注→考察→答题→又是批注）。

---

## 附录 C：编辑历史与文档元信息

### 编辑历史

| 日期 | 作者 | 变更摘要 |
|------|------|---------|
| 2026-04-12 | Claude Code | BMAD 全面重写：46→103 FR + 5→9 NFR 类别 + 竞品分析/风险矩阵/废弃FR/决策索引 |

### 上游文档索引

| 文档 | 行数 | 作用 |
|------|------|------|
| PRD v5 (14-scheme-a-implementation-prd.md) | 7594 | 唯一真相源 · read-only 锚定文档 |
| Archived PRD (prd-tauri-archived-20260401.md) | 971 | 质量标杆 · 12 能力域 103 FR |
| 9 前序 Explore Agent (A/B/C/D/E/F/G/J/L) | - | Agent J 认知科学解构 (12 d-value) |

### 引用格式说明

本 PRD 每个章节头部标注来源章节：`> **From PRD**: §X [标题] (line YYYY-ZZZZ)`
灵魂 FR（FR-EXAM-01, FR-EXAM-05, FR-EXAM-22）另有独立引用。

---

> **Canvas Learning System PRD 结束**
>
> **核心承诺**（Plan v19 修正）:
> - 4 个灵魂设计完整保留 (≥ 95%): 检验白板 · 新节点提取 · BKT+FSRS 融合 · 正面措辞
> - 检验白板 **100% 等价实现**（FR-EXAM-01 + FR-EXAM-22 三重保证）
> - "批注驱动的精确考察"**完整实现**（FR-EXAM-09 + FR-EXAM-05 · D14 锁定）
