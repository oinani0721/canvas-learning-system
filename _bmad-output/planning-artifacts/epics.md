---
stepsCompleted:
  - step-01-validate-prerequisites
  - step-02-design-epics
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture.md
---

# Canvas - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for Canvas Learning System (Obsidian Hybrid), decomposing the 46 FRs + NFRs from the BMAD PRD and backend-relevant Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1: 学习者可以启动 AI 对话，AI 通过 wikilink 图解析库解析 [[wikilinks]] 发现相邻概念，读取 frontmatter 和内容作为对话上下文
FR2: 系统可以在对话中基于个人历史误解主动提醒学习者
FR3: 学习者可以在对话回答中看到可点击的补充学习材料列表（LanceDB hybrid search）
FR4: 学习者可以选中两个概念之间的关系文本启动 EI+SE 双策略深度讨论
FR5: 系统可以在对话结束时自动归档会话到 Graphiti 长期记忆
FR6: 学习者可以启动完全空白的检验白板考察（信息隔离，看不到笔记原文）
FR7: 系统可以基于 BKT/FSRS 掌握度分数自动选出薄弱节点作为考察范围
FR8: 系统可以融合个人记忆（Graphiti）、知识图谱关系（Graphify）和掌握度数据（frontmatter）生成个人化题目
FR9: 学习者可以在 markdown 编辑器中手写答案并手动触发提交
FR10: 系统可以静默评分（学习者不感知评分过程），结果写入 frontmatter
FR11: 学习者可以在答不出时请求 4 级渐进提示（方向 → 关键词 → 框架 → 脚手架）
FR12: 学习者可以跳过题目且不受惩罚
FR13: 学习者可以基于笔记中的 callout 批注触发快速考察
FR14: 系统可以防止在检验白板内再次生成检验白板（防嵌套）
FR15: 学习者可以从对话或考察中提取新概念，自动创建 [[wikilink]] 双向链接的 .md 文件
FR16: 系统可以在考察中提取新概念时不中断当前流程（书签式，考后再深度讨论）
FR17: 系统可以通过 Graphify 从笔记文本中自动提取概念关系，生成独立 AI 检索索引 graph.json
FR18: 系统可以为 Graphify 提取的每个概念标注三级置信度（EXTRACTED / INFERRED / AMBIGUOUS）
FR19: 系统可以使用 BKT 模型实时更新每个概念的掌握概率
FR20: 系统可以使用 FSRS 算法计算最优复习间隔
FR21: 系统可以维护 5 信号融合的掌握度评估
FR22: 系统可以保证评分操作链的顺序完整性（不可跳步）
FR23: 系统可以记录学习者的错误并按 4 类分类存储（双写）
FR24: 系统可以记录学习者的自我评估校准数据
FR25: 学习者可以对 AI 评分投票反馈（准确 / 偏高 / 偏低）
FR26: 系统可以搜索学习者的历史记忆（3 层检索）
FR27: 系统可以异步非阻塞地将学习事件写入知识图谱
FR28: 学习者可以查看全局 Dashboard（Dataview 三层布局）
FR29: 系统可以使用处方性措辞展示学习状态
FR30: 学习者可以查看元认知 2x2 校准矩阵
FR31: 学习者可以从 Dashboard 一键启动检验白板
FR32: 学习者可以查看单个概念的详细档案
FR33: 系统可以在 Day 3 和 Day 7 主动提醒复习误解
FR34: 系统可以在复习时自动注入历史误解上下文
FR35: 系统可以基于历史误解生成辨析题
FR36: 学习者可以查看待复习任务列表
FR37: 学习者可以自定义所有 Skill 的 hotkey 绑定
FR38: 系统可以通过 Templater 模板自动生成标准 frontmatter
FR39: 学习者可以选择性启用 Obsidian Git 自动备份
FR40: 系统可以执行 Graphify health check
FR41: 系统可以在启动时检测 hotkey 冲突并警告
FR42: 系统必须将 context_enrichment 重构为 wikilink 图解析（Phase 1 必修）
FR43: 系统必须支持 wikilink 双向链接邻居发现
FR44: 系统可以在 Skill 结束时附加 Graphiti 操作摘要行
FR45: 系统可以在 vault 内维护 Graphiti 操作审计日志
FR46: 系统可以识别笔记中嵌入的图片并纳入 AI 对话上下文

### NonFunctional Requirements

NFR-PERF-1: LLM 出题/评分 < 5s for 95th percentile
NFR-PERF-2: Dataview Dashboard 刷新 < 1s
NFR-PERF-3: Graphify 全量索引 < 30s for ~100 文件
NFR-PERF-4: LanceDB 增量索引 < 500ms per file
NFR-PERF-5: wikilink 图构建 < 2s
NFR-PERF-6: wikilink 图遍历 < 200ms per N-hop query
NFR-PERF-7: Graphiti search < 3s
NFR-PERF-8: Graphiti 写入队列 < 10s per episode
NFR-INT-1: frontmatter 不可因 Skill 异常损坏
NFR-INT-2: Graphiti 写入原子性
NFR-INT-3: LLM API 只传筛选片段
NFR-INT-4: 全部数据本地存储
NFR-REL-1: Claudian 故障 → CLI 降级
NFR-REL-2: 14 MCP 工具全部可调用
NFR-REL-3: 操作链 5 步完整传递
NFR-REL-4: wikilink 图支持热更新
NFR-REL-5: Graphiti 读在 LLM 前写在操作后
NFR-REL-6: EventBus 级联自动触发 Graphiti 写入
NFR-DEG-1: Claudian 挂掉 → CLI 降级
NFR-DEG-2: Claude API 不可用 → 离线模式
NFR-DEG-3: Graphiti 不可用 → 默认先验出题
NFR-DEG-4: Graphify 失败 → 读 frontmatter + wikilinks
NFR-DEG-5: 检验白板隔离失败 → /quiz_from_callout 降级
NFR-DEG-6: Graphiti 写入失败 → 自动重试 3 次
NFR-OBS-1: Skill 末尾 Graphiti 摘要行
NFR-OBS-2: 状态栏指示灯
NFR-OBS-3: 审计日志全操作记录

### Additional Requirements

From Architecture (backend-relevant, Tauri frontend excluded):
- AR1: Docker 启动顺序：Neo4j → Ollama(bge-m3) → FastAPI → MCP 连接 → 就绪
- AR2: Hot-Warm-Cold 三层时间归档（0-30天/30天-6月/6月+）
- AR3: 4 类错误自动分类器差异化补救路由
- AR4: AutoSCORE 两阶段隐形评分（证据提取 → 4维4分制 × 3次采样多数投票）
- AR5: RAG 增量索引管道（content_hash去重 + 标题智能分块 + 面包屑前缀 + jieba中文）
- AR6: 检索后处理（reranker精排 + Adaptive-k + A-RAG迭代验证）
- AR7: 上下文压缩 15K→3K（句子级提取，公式/代码整块保护）
- AR8: LiteLLM 统一层 + 双层 Key 分离
- AR9: Token 成本追踪 + 按任务统计
- AR10: 离线降级 4 场景
- AR11: context_enrichment 重构为 wikilink 图遍历（与 FR42 对齐）

### FR Coverage Map

| FR | Epic | 简述 |
|---|---|---|
| FR1 | Epic 2 | AI 对话 + wikilink 上下文 |
| FR2 | Epic 2 | 历史误解提醒 |
| FR3 | Epic 2 | 补充材料列表 |
| FR4 | Epic 4 | Edge 讨论 |
| FR5 | Epic 2 | 对话归档 Graphiti |
| FR6 | Epic 3 | 空白检验白板 |
| FR7 | Epic 3 | BKT/FSRS 选弱项 |
| FR8 | Epic 3 | 三路融合出题 |
| FR9 | Epic 3 | md 编辑器手写答案 |
| FR10 | Epic 3 | 静默评分 |
| FR11 | Epic 3 | 4 级渐进提示 |
| FR12 | Epic 3 | 跳过不惩罚 |
| FR13 | Epic 6 | callout 批注考察 |
| FR14 | Epic 3 | 防嵌套 |
| FR15 | Epic 4 | 提取新概念 wikilink |
| FR16 | Epic 3 | 书签式提取 |
| FR17 | Epic 4 | Graphify graph.json |
| FR18 | Epic 4 | 三级置信度 |
| FR19 | Epic 5 | BKT 掌握概率 |
| FR20 | Epic 5 | FSRS 复习间隔 |
| FR21 | Epic 5 | 5 信号融合 |
| FR22 | Epic 3 | 操作链顺序保证 |
| FR23 | Epic 5 | 错误 4 类分类 |
| FR24 | Epic 5 | 校准数据 |
| FR25 | Epic 5 | AI 评分投票 |
| FR26 | Epic 5 | 历史记忆搜索 |
| FR27 | Epic 5 | 异步写入 |
| FR28 | Epic 7 | 全局 Dashboard |
| FR29 | Epic 7 | 处方性措辞 |
| FR30 | Epic 7 | 2x2 校准矩阵 |
| FR31 | Epic 7 | 一键启动考察 |
| FR32 | Epic 7 | 单概念档案 |
| FR33 | Epic 6 | Day 3+7 提醒 |
| FR34 | Epic 6 | 复习注入历史 |
| FR35 | Epic 6 | 辨析题 |
| FR36 | Epic 6 | 任务列表 |
| FR37 | Epic 1 | hotkey 自定义 |
| FR38 | Epic 1 | Templater 模板 |
| FR39 | Epic 1 | Git 备份 |
| FR40 | Epic 8 | Graphify health |
| FR41 | Epic 1 | hotkey 冲突检测 |
| FR42 | Epic 1 | context_enrichment 重构 |
| FR43 | Epic 1 | wikilink 邻居发现 |
| FR44 | Epic 8 | Graphiti 摘要行 |
| FR45 | Epic 8 | 审计日志 |
| FR46 | Epic 2 | 图片识别 |

## Epic List

### Epic 1: 学习环境搭建

学习者可以拥有一个配置完整的 Obsidian vault，启动 Claudian 和后端，开始第一次学习。包括 vault 初始化、Templater 模板、hotkey 配置、context_enrichment 从 .canvas JSON 重构为 wikilink 图遍历。

**FRs covered:** FR37, FR38, FR39, FR41, FR42, FR43
**Phase:** 1 MVP · 对应旅程 4（冷启动）

### Epic 2: 智能学习对话

学习者可以和 AI 进行有上下文感知的对话。AI 通过 wikilink 图遍历获取相邻概念、注入个人历史记忆、显示补充学习材料，并在对话结束后自动归档到 Graphiti。

**FRs covered:** FR1, FR2, FR3, FR5, FR46
**Phase:** 1 MVP · 对应旅程 1（日常学习）+ 旅程 5（图片学习）

### Epic 3: 检验白板 — Active Recall（灵魂 Epic）

学习者可以在完全空白的检验白板中接受个人化考察。系统通过三路融合出题，支持 md 编辑器手写答案、静默评分、4 级渐进提示、跳过不惩罚、书签式概念提取和防嵌套保护。

**FRs covered:** FR6, FR7, FR8, FR9, FR10, FR11, FR12, FR14, FR16, FR22
**Phase:** 1 MVP · 对应旅程 2（灵魂旅程）

### Epic 4: 知识图谱构建

学习者可以从对话中提取新概念创建双向链接，探索概念间关系（EI+SE 双策略），并通过 Graphify 自动提取隐含关系生成 AI 检索索引。

**FRs covered:** FR4, FR15, FR17, FR18
**Phase:** 1-2 · 对应旅程 1（深度剖析部分）

### Epic 5: 掌握度追踪与记忆管理

系统准确追踪每个概念的掌握程度（BKT+FSRS+5 信号融合），记录错误（4 类分类双写），管理学习记忆（3 层检索+异步写入），支持校准投票。

**FRs covered:** FR19, FR20, FR21, FR23, FR24, FR25, FR26, FR27
**Phase:** 1-2 · 支撑 Epic 3 和 Epic 6

### Epic 6: 错误修正与间隔复习

学习者在犯错后获得 Day 3 + Day 7 定时提醒，复习时自动注入历史误解上下文，通过辨析题验证误解已纠正。支持 callout 批注驱动的快速考察。

**FRs covered:** FR13, FR33, FR34, FR35, FR36
**Phase:** 2 · 对应旅程 3（错误修正闭环）

### Epic 7: 学习 Dashboard 与档案

学习者可以查看全局 Dashboard（Dataview 三层布局 + 处方性措辞），浏览元认知 2x2 校准矩阵，一键启动考察，查看单概念详细档案。

**FRs covered:** FR28, FR29, FR30, FR31, FR32
**Phase:** 2 · 对应旅程 6（档案浏览）

### Epic 8: 系统健康与 Graphiti 可观测性

学习者可以确认 Graphiti 记忆系统正常工作（Skill 末尾摘要行 + 状态栏指示灯），审计操作历史（vault 内日志），执行 Graphify health check。

**FRs covered:** FR40, FR44, FR45
**Phase:** 2 · 来源于 PRD 创建 session 发现的可观测性需求
