---
stepsCompleted:
  - step-01-validate-prerequisites
  - step-02-design-epics
  - step-03-create-stories
  - step-04-final-validation
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

---

## Epic 1: 学习环境搭建

学习者可以拥有一个配置完整的 Obsidian vault，启动后端服务，开始第一次学习。包括 vault 初始化、Templater 模板、hotkey 配置、context_enrichment 重构为 wikilink 图遍历。

### Story 1.1: Vault 初始化与 Templater 标准模板

As a 学习者,
I want 在 Obsidian vault 中自动生成标准 frontmatter 模板（含掌握度、BKT 参数、FSRS 参数等字段）,
So that 每个新建笔记都有统一的元数据结构供系统读写。

**Acceptance Criteria:**

**Given** 学习者安装了 Templater 插件并配置了模板目录
**When** 学习者在 vault 中创建新笔记
**Then** Templater 自动注入标准 frontmatter（含 mastery_score、bkt_params、fsrs_params、error_history 等字段）
**And** frontmatter 字段符合 PRD §4 定义的 schema

**Given** 学习者编辑已有笔记
**When** 笔记缺少必要 frontmatter 字段
**Then** 系统不自动补全（只对新笔记生效，避免意外覆盖）

**Given** 后端服务启动
**When** Docker 编排执行
**Then** 按顺序就绪：Neo4j → Ollama(bge-m3) → FastAPI → MCP 连接
**And** 前一服务未就绪时后续服务等待（不跳过）
**And** 全部就绪后系统标记为可用

*FRs: FR38 · ARs: AR1*

### Story 1.2: context_enrichment 重构为 wikilink 图遍历

As a 系统,
I want 将 context_enrichment 模块从读取 .canvas JSON 重构为通过 wikilink 图解析库（obsidiantools）遍历双向链接,
So that 降级到 Obsidian Hybrid 方案后仍能发现相邻概念作为对话上下文。

**Acceptance Criteria:**

**Given** 后端 context_enrichment 模块启动
**When** 系统接收一个笔记路径作为输入
**Then** 通过 obsidiantools 解析 vault 中的 [[wikilinks]]，返回 N-hop 邻居列表（默认 2-hop）
**And** 每个邻居包含标题、路径、frontmatter 摘要
**And** 遍历延迟 < 200ms（NFR-PERF-6）
**And** wikilink 图构建 < 2s（NFR-PERF-5）

**Given** vault 中某笔记的 wikilinks 发生变化
**When** 系统下次查询该笔记的邻居
**Then** 图支持热更新，返回最新的邻居列表（NFR-REL-4）

*FRs: FR42, FR43 · ARs: AR11*

### Story 1.3: Hotkey 自定义绑定

As a 学习者,
I want 自定义所有 Skill（对话、考察、概念提取等）的 hotkey 绑定,
So that 我可以用自己习惯的快捷键快速启动各个功能。

**Acceptance Criteria:**

**Given** 学习者打开 Obsidian Settings → Hotkeys
**When** 学习者搜索 Canvas Learning System 的 Skill 命令
**Then** 所有已注册 Skill 都出现在列表中，可分配自定义快捷键

**Given** 学习者为某 Skill 设置了快捷键
**When** 学习者按下该快捷键
**Then** 对应 Skill 立即启动

*FRs: FR37*

### Story 1.4: Hotkey 冲突检测与警告

As a 系统,
I want 在启动时检测 hotkey 冲突并发出警告,
So that 学习者不会因为快捷键冲突导致功能不可达。

**Acceptance Criteria:**

**Given** 系统启动或 hotkey 配置变更
**When** 两个或以上 Skill 绑定了相同的快捷键
**Then** 系统弹出警告通知，列出冲突的 Skill 名称和快捷键
**And** 不强制修改，只提醒

*FRs: FR41*

### Story 1.5: Obsidian Git 自动备份

As a 学习者,
I want 选择性启用 Obsidian Git 自动备份,
So that 我的学习数据可以自动同步到 Git 仓库，防止丢失。

**Acceptance Criteria:**

**Given** 学习者安装了 Obsidian Git 插件
**When** 学习者在 Settings 中启用自动备份
**Then** 系统按配置间隔自动 commit + push（默认 30 分钟）
**And** 备份不影响正常使用（异步执行）

**Given** 学习者未启用 Obsidian Git
**When** 系统正常运行
**Then** 不因缺少 Git 备份而报错或降级

*FRs: FR39*

---

## Epic 2: 智能学习对话

学习者可以和 AI 进行有上下文感知的对话。AI 通过 wikilink 图遍历获取相邻概念、注入个人历史记忆、显示补充学习材料，并在对话结束后自动归档到 Graphiti。

### Story 2.1: AI 对话 + wikilink 上下文注入

As a 学习者,
I want 启动 AI 对话时，系统自动通过 wikilink 图遍历发现当前笔记的相邻概念，读取 frontmatter 和内容作为对话上下文,
So that AI 对话具有充分的知识背景，回答更精准。

**Acceptance Criteria:**

**Given** 学习者在某笔记页面启动 AI 对话
**When** 对话启动
**Then** 系统调用 Story 1.2 的 wikilink 遍历获取 2-hop 邻居
**And** 将当前笔记 + 邻居的 frontmatter 和内容摘要注入 LLM 上下文
**And** 上下文压缩后不超过 3K tokens（AR7）
**And** 公式和代码块整块保护不被截断（AR7）

**Given** LLM 上下文已注入
**When** 学习者提出问题
**Then** AI 回答引用了相邻概念的知识
**And** LLM 出题/评分延迟 < 5s（NFR-PERF-1）

*FRs: FR1 · ARs: AR7*

### Story 2.2: 补充学习材料搜索

As a 学习者,
I want 在对话回答中看到可点击的补充学习材料列表,
So that 我可以快速跳转到相关笔记深入学习。

**Acceptance Criteria:**

**Given** AI 生成对话回答
**When** 回答涉及 vault 中其他笔记的主题
**Then** 系统通过 LanceDB hybrid search 检索相关笔记
**And** 检索后经过 reranker 精排 + Adaptive-k 筛选（AR6）
**And** 在回答末尾展示可点击的 [[wikilink]] 列表（≤5 条）
**And** LanceDB 增量索引 < 500ms per file（NFR-PERF-4）

*FRs: FR3 · ARs: AR5, AR6*

### Story 2.3: 历史误解主动提醒

As a 系统,
I want 在对话中基于学习者的个人历史误解主动提醒,
So that 学习者不会重复犯相同的错误。

**Acceptance Criteria:**

**Given** 学习者在对话中讨论某个概念
**When** 该概念存在历史误解记录（Graphiti 中）
**Then** AI 在回答中主动提醒："你之前在 X 概念上曾有误解：Y"
**And** Graphiti search 延迟 < 3s（NFR-PERF-7）
**And** 只在 API 可用时提醒，Graphiti 不可用时静默跳过（NFR-DEG-3）

*FRs: FR2*

### Story 2.4: 对话归档到 Graphiti

As a 系统,
I want 在对话结束时自动将会话归档到 Graphiti 长期记忆,
So that 未来对话可以引用历史交互内容。

**Acceptance Criteria:**

**Given** 学习者结束对话（关闭对话面板或手动结束）
**When** 系统处理对话归档
**Then** 异步非阻塞地将对话摘要写入 Graphiti（NFR-REL-5）
**And** 写入原子性（NFR-INT-2），失败自动重试 3 次（NFR-DEG-6）
**And** Graphiti 写入队列延迟 < 10s per episode（NFR-PERF-8）
**And** 归档不阻塞 UI（学习者可立即开始其他操作）

*FRs: FR5*

### Story 2.5: 图片识别纳入 AI 对话上下文

As a 学习者,
I want 系统识别笔记中嵌入的图片并纳入 AI 对话上下文,
So that 我可以就图片内容（图表、公式截图等）向 AI 提问。

**Acceptance Criteria:**

**Given** 当前笔记中嵌入了图片（![[image.png]] 或 ![](path)）
**When** 学习者启动 AI 对话
**Then** 系统提取图片并通过多模态 LLM 获取描述
**And** 图片描述作为额外上下文注入对话
**And** 只传筛选后的图片，不传整个 vault 的图片（NFR-INT-3）

*FRs: FR46*

---

## Epic 3: 检验白板 — Active Recall（灵魂 Epic）

学习者可以在完全空白的检验白板中接受个人化考察。系统通过三路融合出题，支持 md 编辑器手写答案、静默评分、4 级渐进提示、跳过不惩罚、书签式概念提取和防嵌套保护。

### Story 3.1: 空白检验白板创建 + 信息隔离 + 防嵌套

As a 学习者,
I want 启动完全空白的检验白板，看不到笔记原文,
So that 我可以在没有参考材料的环境下真正考察自己的理解。

**Acceptance Criteria:**

**Given** 学习者触发考察命令（hotkey 或按钮）
**When** 系统创建检验白板
**Then** 白板为完全空白状态，不显示任何笔记原文
**And** 学习者无法在白板内查看原始笔记（信息隔离）

**Given** 学习者已在一个检验白板内
**When** 学习者尝试再次启动检验白板
**Then** 系统拒绝创建并提示"不可在检验白板内嵌套考察"（FR14）

*FRs: FR6, FR14*

### Story 3.2: BKT/FSRS 自动选弱项

As a 系统,
I want 基于 BKT 掌握概率和 FSRS 复习间隔自动选出薄弱节点作为考察范围,
So that 考察聚焦于学习者最需要强化的概念。

**Acceptance Criteria:**

**Given** 学习者启动检验白板
**When** 系统确定考察范围
**Then** 从 vault frontmatter 中读取所有概念的 BKT mastery_score 和 FSRS due_date
**And** 优先选择 mastery_score 最低的 + 已过 FSRS due_date 的概念
**And** 选出 3-5 个概念作为本次考察范围

**Given** Graphiti 不可用
**When** 系统选择考察范围
**Then** 退回到仅使用 frontmatter 数据的默认先验模式（NFR-DEG-3）

*FRs: FR7*

### Story 3.3: 三路融合个人化出题

As a 系统,
I want 融合个人记忆（Graphiti）、知识图谱关系（Graphify）和掌握度数据（frontmatter）生成个人化题目,
So that 题目针对学习者的个人薄弱点和知识结构定制。

**Acceptance Criteria:**

**Given** 系统已选定考察概念（Story 3.2）
**When** 系统生成题目
**Then** 从 Graphiti 获取学习者的个人记忆（历史误解、已确认理解）
**And** 从 Graphify 获取概念间关系（前置、关联、对比）
**And** 从 frontmatter 获取掌握度数据
**And** 三路数据融合后发送 LLM 生成题目
**And** LLM 出题延迟 < 5s（NFR-PERF-1）

*FRs: FR8*

### Story 3.4: Markdown 编辑器手写答案 + 手动提交

As a 学习者,
I want 在检验白板的 markdown 编辑器中手写答案，手动触发提交,
So that 我可以按自己的节奏组织答案，不被自动提交打断。

**Acceptance Criteria:**

**Given** 题目已展示在检验白板中
**When** 学习者在 markdown 编辑器中编写答案
**Then** 编辑器支持标准 markdown 语法（标题、列表、代码块、公式）
**And** 不自动提交，只在学习者手动点击"提交"时触发

**Given** 学习者点击"提交"
**When** 答案被提交
**Then** 答案内容被发送到评分系统（Story 3.5）
**And** 编辑器进入只读状态，防止提交后修改
**And** 答案内容进入评分流程

*FRs: FR9*

### Story 3.5: 静默评分 + AutoSCORE + 操作链顺序保证

As a 系统,
I want 在学习者不感知评分过程的情况下静默评分，结果写入 frontmatter,
So that 评分不干扰学习流程，且数据自动持久化。

**Acceptance Criteria:**

**Given** 学习者提交答案
**When** 系统执行评分
**Then** 使用 AutoSCORE 两阶段隐形评分（证据提取 → 4维4分制 × 3次采样多数投票）（AR4）
**And** 评分过程对学习者不可见（无 loading spinner / 进度条显示评分细节）
**And** 评分结果写入 frontmatter（不可因 Skill 异常损坏 frontmatter，NFR-INT-1）

**Given** 评分需要多个步骤（证据提取 → 维度评分 → 汇总）
**When** 操作链执行
**Then** 步骤顺序完整不可跳步（FR22）
**And** 每步完成后才进入下一步（NFR-REL-3）

*FRs: FR10, FR22 · ARs: AR4*

### Story 3.6: 4 级渐进提示

As a 学习者,
I want 在答不出时请求 4 级渐进提示（方向 → 关键词 → 框架 → 脚手架）,
So that 我可以在不同程度的帮助下逐步找到答案。

**Acceptance Criteria:**

**Given** 学习者正在作答一道题目
**When** 学习者点击"提示"按钮
**Then** 系统按顺序给出 4 级渐进提示：
  1. 方向提示（指明思考方向，不给具体内容）
  2. 关键词提示（给出核心关键词）
  3. 框架提示（给出答案框架/结构）
  4. 脚手架提示（给出接近完整的答案骨架）
**And** 每次点击只展示下一级，不跳级

**Given** 学习者已使用了提示
**When** 评分时
**Then** 提示使用次数记录在 frontmatter 中供掌握度计算参考

*FRs: FR11*

### Story 3.7: 跳过题目不惩罚

As a 学习者,
I want 可以跳过题目且不受评分惩罚,
So that 我可以策略性地跳过暂时无法回答的题目，不影响掌握度分数。

**Acceptance Criteria:**

**Given** 学习者正在检验白板中面对一道题目
**When** 学习者点击"跳过"
**Then** 该题标记为 skipped，不计入掌握度评分
**And** 跳过事件记录在 frontmatter 中（用于后续分析，但不影响 BKT/FSRS 参数）
**And** 系统自动展示下一道题目

*FRs: FR12*

### Story 3.8: 书签式概念提取（不中断考察）

As a 学习者,
I want 在考察中发现新概念时，以书签方式标记稍后处理,
So that 不中断当前考察流程，考后再深入讨论新概念。

**Acceptance Criteria:**

**Given** 学习者在检验白板答题过程中发现新概念
**When** 学习者点击"书签"或快捷键标记
**Then** 新概念被添加到临时书签列表（不立即创建笔记）
**And** 考察流程不中断，继续当前题目

**Given** 考察结束
**When** 系统展示考察总结
**Then** 书签列表中的新概念显示在总结页
**And** 学习者可以选择是否为每个概念创建新笔记

*FRs: FR16*

---

## Epic 4: 知识图谱构建

学习者可以从对话中提取新概念创建双向链接，探索概念间关系（EI+SE 双策略），并通过 Graphify 自动提取隐含关系生成 AI 检索索引。

### Story 4.1: 新概念提取 + wikilink 双向链接创建

As a 学习者,
I want 从对话或考察中提取新概念，系统自动创建带 [[wikilink]] 双向链接的 .md 文件,
So that 我的知识图谱随学习过程自动扩展。

**Acceptance Criteria:**

**Given** 学习者在对话或考察中识别到一个新概念
**When** 学习者选中文本并触发"提取概念"
**Then** 系统创建新 .md 文件，文件名为概念名
**And** 新文件自动填入 Templater 标准 frontmatter
**And** 在原笔记中插入 [[新概念]] wikilink
**And** 在新文件中插入 [[原笔记]] 反向链接

*FRs: FR15*

### Story 4.2: Graphify 关系提取 + graph.json 索引

As a 系统,
I want 通过 Graphify 从笔记文本中自动提取概念关系，生成独立 AI 检索索引 graph.json,
So that AI 可以理解概念之间的关系用于出题和对话。

**Acceptance Criteria:**

**Given** vault 中有笔记内容
**When** 系统运行 Graphify 提取
**Then** 从文本中识别概念关系（前置、关联、对比、包含等）
**And** 生成 graph.json 作为 AI 检索索引
**And** 全量索引 < 30s for ~100 文件（NFR-PERF-3）

**Given** 学习者新建或修改了笔记
**When** 下次 Graphify 运行
**Then** 增量更新 graph.json（不需要全量重建）

*FRs: FR17*

### Story 4.3: 三级置信度标注

As a 系统,
I want 为 Graphify 提取的每个概念标注三级置信度（EXTRACTED / INFERRED / AMBIGUOUS）,
So that 系统和学习者可以区分高确信的关系和需要验证的推测。

**Acceptance Criteria:**

**Given** Graphify 提取了一组概念关系
**When** 系统标注置信度
**Then** 直接从文本提取的关系标注为 EXTRACTED
**And** 通过推理得出的关系标注为 INFERRED
**And** 不确定或矛盾的关系标注为 AMBIGUOUS
**And** 置信度信息存储在 graph.json 中

*FRs: FR18*

### Story 4.4: EI+SE 双策略深度讨论

As a 学习者,
I want 选中两个概念之间的关系文本启动 EI+SE 双策略深度讨论,
So that 我可以深入理解概念关系的细微差别。

**Acceptance Criteria:**

**Given** 学习者在笔记中看到两个 [[wikilink]] 概念
**When** 学习者选中关系文本并触发"深度讨论"
**Then** AI 使用 Elaborative Interrogation（追问"为什么"）和 Self-Explanation（引导自我解释）两种策略
**And** 对话围绕两个概念的关系展开（不偏离到其他概念）

*FRs: FR4*

---

## Epic 5: 掌握度追踪与记忆管理

系统准确追踪每个概念的掌握程度（BKT+FSRS+5 信号融合），记录错误（4 类分类双写），管理学习记忆（3 层检索+异步写入），支持校准投票。

### Story 5.1: BKT 模型实时更新掌握概率

As a 系统,
I want 使用 BKT（Bayesian Knowledge Tracing）模型实时更新每个概念的掌握概率,
So that 系统始终拥有学习者对每个概念的最新掌握估计。

**Acceptance Criteria:**

**Given** 学习者完成一道关于概念 X 的考察题
**When** 评分结果产生（正确/部分正确/错误）
**Then** 系统用贝叶斯更新公式计算 X 的新 mastery_score
**And** 更新后的 mastery_score 写入 X 笔记的 frontmatter
**And** 更新过程原子性保证（NFR-INT-1）

*FRs: FR19*

### Story 5.2: FSRS 复习间隔计算

As a 系统,
I want 使用 FSRS（Free Spaced Repetition Scheduler）算法计算每个概念的最优复习间隔,
So that 学习者可以在记忆衰退前得到复习提醒。

**Acceptance Criteria:**

**Given** 学习者完成某概念的考察
**When** 评分结果写入
**Then** FSRS 算法根据难度、稳定性、可提取性计算下次 due_date
**And** due_date 写入概念笔记的 frontmatter
**And** 多次练习后 FSRS 参数根据实际表现动态调整

*FRs: FR20*

### Story 5.3: 5 信号融合掌握度评估

As a 系统,
I want 维护 5 信号融合的掌握度评估,
So that 掌握度评估比单一指标更准确全面。

**Acceptance Criteria:**

**Given** 某概念有多维度学习数据
**When** 系统计算综合掌握度
**Then** 融合 5 个信号：BKT mastery、FSRS stability、答题准确率、提示使用率、校准偏差
**And** 每个信号有配置权重（可调整但有合理默认值）
**And** 融合结果作为最终 mastery_score 写入 frontmatter

*FRs: FR21*

### Story 5.4: 错误 4 类分类 + 双写存储

As a 系统,
I want 记录学习者的错误并按 4 类自动分类存储（双写到 frontmatter + Graphiti）,
So that 系统可以针对不同类型的错误提供差异化补救。

**Acceptance Criteria:**

**Given** 学习者答错一道题
**When** 系统记录错误
**Then** 自动分类为 4 类之一（概念性错误 / 程序性错误 / 粗心错误 / 知识空白）（AR3）
**And** 错误记录双写：frontmatter error_history 数组 + Graphiti episode
**And** 每类错误关联差异化补救路由（AR3）

*FRs: FR23 · ARs: AR3*

### Story 5.5: 自我评估校准数据记录

As a 系统,
I want 记录学习者的自我评估校准数据,
So that 系统可以衡量学习者的元认知准确性。

**Acceptance Criteria:**

**Given** 学习者完成答题后
**When** 系统提示学习者自评"你觉得自己答得怎么样？"
**Then** 学习者选择自评等级（高/中/低信心）
**And** 自评结果与实际评分结果对比存储
**And** 校准偏差（自评 vs 实际）纳入 5 信号融合（Story 5.3）

*FRs: FR24*

### Story 5.6: AI 评分投票反馈

As a 学习者,
I want 对 AI 评分投票反馈（准确 / 偏高 / 偏低）,
So that 评分系统可以根据我的反馈持续改进。

**Acceptance Criteria:**

**Given** 系统展示评分结果
**When** 学习者看到分数
**Then** 出现三个投票按钮：准确 / 偏高 / 偏低
**And** 学习者点击后投票结果存储到 Graphiti
**And** 投票是可选的（可以不投票直接继续）

*FRs: FR25*

### Story 5.7: 历史记忆 3 层检索

As a 系统,
I want 通过 3 层检索搜索学习者的历史记忆,
So that 系统可以准确找到相关的历史学习数据。

**Acceptance Criteria:**

**Given** 系统需要查询学习者关于某概念的历史记忆
**When** 执行 3 层检索
**Then** 第 1 层：frontmatter 本地数据（最快，< 100ms）
**And** 第 2 层：LanceDB 向量检索（语义相关，< 500ms）
**And** 第 3 层：Graphiti 知识图谱检索（关系推理，< 3s，NFR-PERF-7）
**And** 三层结果融合去重后返回

**Given** Graphiti 不可用
**When** 系统执行 3 层检索
**Then** 退回到前 2 层（frontmatter + LanceDB），不报错（NFR-DEG-3）

**Given** 历史记忆有时间维度
**When** 记忆超过 6 个月
**Then** 自动归档到 Cold 层（AR2 Hot-Warm-Cold 三层时间归档）

*FRs: FR26 · ARs: AR2*

### Story 5.8: 异步非阻塞知识图谱写入

As a 系统,
I want 异步非阻塞地将学习事件写入知识图谱,
So that 写入操作不影响学习者的交互体验。

**Acceptance Criteria:**

**Given** 学习事件发生（答题、评分、概念提取等）
**When** 系统需要写入 Graphiti
**Then** 写入操作通过异步队列执行，不阻塞 UI 和 API 请求（AR27）
**And** Graphiti 读在 LLM 调用前、写在操作后（NFR-REL-5）
**And** EventBus 级联自动触发 Graphiti 写入（NFR-REL-6）
**And** 写入失败自动重试 3 次（NFR-DEG-6）
**And** 写入原子性（NFR-INT-2）

*FRs: FR27*

---

## Epic 6: 错误修正与间隔复习

学习者在犯错后获得 Day 3 + Day 7 定时提醒，复习时自动注入历史误解上下文，通过辨析题验证误解已纠正。支持 callout 批注驱动的快速考察。

### Story 6.1: 待复习任务列表

As a 学习者,
I want 查看待复习任务列表,
So that 我知道哪些概念需要复习以及优先级。

**Acceptance Criteria:**

**Given** 学习者打开复习任务页面
**When** 系统加载任务列表
**Then** 显示所有已过 FSRS due_date 的概念（按逾期天数排序）
**And** 显示所有有未关闭误解记录的概念
**And** 每项显示：概念名、上次考察日期、掌握度评分、逾期天数

*FRs: FR36*

### Story 6.2: Day 3 + Day 7 主动复习提醒

As a 系统,
I want 在 Day 3 和 Day 7 主动提醒复习误解概念,
So that 学习者在记忆衰退的关键时间点得到提醒。

**Acceptance Criteria:**

**Given** 学习者在考察中某概念出现误解（错误记录为概念性错误或知识空白）
**When** 距误解发生 3 天或 7 天
**Then** 系统在启动时或 Dashboard 中显示提醒通知
**And** 提醒包含概念名称和原始误解的简短描述
**And** 可点击提醒直接进入该概念的复习

*FRs: FR33*

### Story 6.3: 复习时注入历史误解上下文

As a 系统,
I want 在复习时自动注入学习者的历史误解上下文,
So that AI 出题和对话时能针对性地验证误解是否已纠正。

**Acceptance Criteria:**

**Given** 学习者对某概念进行复习
**When** AI 准备对话或出题上下文
**Then** 从 Graphiti 获取该概念的历史误解记录
**And** 将误解上下文注入 LLM prompt（"该学习者曾在 X 方面有误解：Y"）
**And** AI 的回答/题目会有意探测误解是否仍存在

*FRs: FR34*

### Story 6.4: 辨析题生成

As a 系统,
I want 基于学习者的历史误解自动生成辨析题,
So that 学习者可以通过辨析正确与错误理解来彻底纠正误解。

**Acceptance Criteria:**

**Given** 学习者复习某个有历史误解的概念
**When** 系统生成辨析题
**Then** 题目包含正确理解和学习者曾有的错误理解
**And** 要求学习者辨别并解释为什么一个对一个错
**And** 评分验证学习者是否能准确区分

*FRs: FR35*

### Story 6.5: Callout 批注驱动快速考察

As a 学习者,
I want 基于笔记中的 callout 批注触发快速考察,
So that 我可以在阅读笔记时随时对标注的重点进行自测。

**Acceptance Criteria:**

**Given** 笔记中有 `> [!quiz]` 或 `> [!test]` callout 批注
**When** 学习者点击 callout 或触发快速考察命令
**Then** 系统基于 callout 内容生成 1-3 道快速题目
**And** 在当前笔记旁展示（不需要创建完整检验白板）
**And** 评分结果同样写入 frontmatter

**Given** 检验白板隔离失败
**When** 系统降级
**Then** 自动退回到 callout 快速考察模式（NFR-DEG-5）

*FRs: FR13*

---

## Epic 7: 学习 Dashboard 与档案

学习者可以查看全局 Dashboard（Dataview 三层布局 + 处方性措辞），浏览元认知 2x2 校准矩阵，一键启动考察，查看单概念详细档案。

### Story 7.1: 全局 Dashboard — Dataview 三层布局

As a 学习者,
I want 查看全局 Dashboard 展示我的学习状态,
So that 我可以一目了然地了解自己的整体学习进度和薄弱领域。

**Acceptance Criteria:**

**Given** 学习者打开 Dashboard 笔记
**When** Dataview 查询执行
**Then** 展示三层布局：
  1. 顶层：全局统计（总概念数、已掌握比例、待复习数）
  2. 中层：分领域掌握度热力图
  3. 底层：近期学习活动时间线
**And** Dashboard 刷新 < 1s（NFR-PERF-2）

*FRs: FR28*

### Story 7.2: 处方性措辞展示学习状态

As a 系统,
I want 使用处方性措辞展示学习状态,
So that 学习者看到的不是冰冷数据而是具有指导意义的建议。

**Acceptance Criteria:**

**Given** Dashboard 展示学习数据
**When** 系统生成状态描述
**Then** 使用处方性措辞而非纯数据（例："建议优先复习「递归」——上次考察正确率 40%，3 天后到复习窗口"）
**And** 措辞根据掌握度等级变化（红区/黄区/绿区对应不同语气）

*FRs: FR29*

### Story 7.3: 元认知 2x2 校准矩阵

As a 学习者,
I want 查看元认知 2x2 校准矩阵,
So that 我可以了解哪些概念我以为懂了但实际没懂（盲点），哪些概念我以为不懂但实际掌握了。

**Acceptance Criteria:**

**Given** 学习者有足够的校准数据（至少 5 次自评+实际评分）
**When** 学习者查看 2x2 矩阵
**Then** 展示四象限：
  1. 知道自己知道（高自评+高实际）— 绿色
  2. 不知道自己知道（低自评+高实际）— 蓝色
  3. 知道自己不知道（低自评+低实际）— 黄色
  4. 不知道自己不知道（高自评+低实际）— 红色/盲点
**And** 红色象限（盲点）高亮警告

*FRs: FR30*

### Story 7.4: Dashboard 一键启动检验白板

As a 学习者,
I want 从 Dashboard 一键启动检验白板,
So that 我可以快速开始考察而不需要手动切换到笔记页面。

**Acceptance Criteria:**

**Given** 学习者在 Dashboard 页面
**When** 学习者点击"开始考察"按钮
**Then** 系统自动根据 Dashboard 显示的薄弱领域选题并创建检验白板
**And** 考察范围基于 Dashboard 当前数据（不需要学习者手动选概念）

*FRs: FR31*

### Story 7.5: 单概念详细档案

As a 学习者,
I want 查看单个概念的详细档案,
So that 我可以深入了解某个概念的学习历程和掌握度变化。

**Acceptance Criteria:**

**Given** 学习者在 Dashboard 或笔记中点击某个概念名
**When** 档案页面加载
**Then** 展示：
  1. 基础信息：概念名、创建日期、所属领域
  2. 掌握度曲线：BKT mastery_score 随时间的变化图
  3. 复习记录：历次考察日期、题目、得分、使用提示数
  4. 误解记录：历史错误分类和修正状态
  5. 关联概念：来自 Graphify 的关系图（前置/关联/对比）
  6. FSRS 参数：当前 difficulty、stability、due_date

*FRs: FR32*

---

## Epic 8: 系统健康与 Graphiti 可观测性

学习者可以确认 Graphiti 记忆系统正常工作（Skill 末尾摘要行 + 状态栏指示灯），审计操作历史（vault 内日志），执行 Graphify health check。

### Story 8.1: Skill 末尾 Graphiti 操作摘要行

As a 系统,
I want 在 Skill 结束时附加 Graphiti 操作摘要行,
So that 学习者可以确认每次操作后 Graphiti 是否成功记录。

**Acceptance Criteria:**

**Given** 任意 Skill（对话、考察、概念提取等）执行完毕
**When** Skill 返回结果
**Then** 末尾附加摘要行，格式：`[Graphiti] wrote N episodes, read M facts (Xms)`
**And** 如果 Graphiti 写入失败，显示：`[Graphiti] ⚠ write failed (will retry)`

*FRs: FR44 · NFRs: NFR-OBS-1*

### Story 8.2: Vault 内 Graphiti 操作审计日志

As a 系统,
I want 在 vault 内维护 Graphiti 操作审计日志,
So that 学习者和开发者可以审计所有 Graphiti 交互历史。

**Acceptance Criteria:**

**Given** 任何 Graphiti 读/写操作发生
**When** 操作完成
**Then** 审计日志追加一条记录到 vault 内 `_system/graphiti-audit.log`
**And** 记录包含：时间戳、操作类型（read/write）、目标（episode/fact）、延迟、结果（success/fail）
**And** 日志轮转：单文件不超过 10MB（超过后归档为 .1/.2）

*FRs: FR45 · NFRs: NFR-OBS-3*

### Story 8.3: Graphify Health Check

As a 学习者,
I want 执行 Graphify health check 确认知识图谱状态正常,
So that 我可以确认 Graphify 索引没有损坏且是最新的。

**Acceptance Criteria:**

**Given** 学习者触发 Graphify health check 命令
**When** 系统执行检查
**Then** 报告：graph.json 最后更新时间、节点数、边数、vault 笔记总数 vs 已索引数
**And** 如果有未索引的笔记，列出文件名
**And** 如果 graph.json 损坏，报告错误并建议重建

**Given** Graphify 失败
**When** 系统降级
**Then** 退回到读 frontmatter + wikilinks 模式（NFR-DEG-4）

*FRs: FR40*

### Story 8.4: Token 成本追踪

As a 系统,
I want 追踪 LLM API 的 token 消耗并按任务类型统计,
So that 学习者和开发者可以了解成本分布并优化高消耗操作。

**Acceptance Criteria:**

**Given** 任何 LLM API 调用发生
**When** 调用返回
**Then** 记录 token 消耗：prompt_tokens、completion_tokens、model、task_type（chat/score/quiz/graphify）
**And** 统计数据可通过 Dashboard 查看（按天/周/月聚合）

**Given** Claude API 不可用
**When** 系统降级到离线模式
**Then** 使用本地 Ollama 模型，token 追踪仍然生效（AR8, NFR-DEG-2）

*ARs: AR8, AR9, AR10*

---

## AR Coverage Map

| AR | Story | 说明 |
|---|---|---|
| AR1 | Story 1.1 | Docker 启动顺序 Neo4j→Ollama→FastAPI→MCP |
| AR2 | Story 5.7 | Hot-Warm-Cold 三层时间归档 |
| AR3 | Story 5.4 | 4 类错误分类器差异化补救路由 |
| AR4 | Story 3.5 | AutoSCORE 两阶段隐形评分 |
| AR5 | Story 2.2 | RAG 增量索引管道 |
| AR6 | Story 2.2 | 检索后处理（reranker + Adaptive-k） |
| AR7 | Story 2.1 | 上下文压缩 15K→3K |
| AR8 | Story 8.4 | LiteLLM 统一层 + 双层 Key 分离 |
| AR9 | Story 8.4 | Token 成本追踪 |
| AR10 | Story 8.4 | 离线降级 4 场景 |
| AR11 | Story 1.2 | context_enrichment wikilink 重构 |

## NFR Coverage Summary

| NFR 类别 | 覆盖 Stories | 验证方式 |
|---|---|---|
| PERF（性能） | 2.1, 2.2, 2.3, 2.4, 3.3, 4.2, 5.7, 7.1 | AC 中包含延迟要求 |
| INT（完整性） | 2.4, 3.5, 5.1, 5.8 | AC 中包含原子性/安全写入要求 |
| REL（可靠性） | 1.2, 3.5, 5.8 | AC 中包含顺序保证/热更新/级联触发 |
| DEG（降级） | 2.3, 3.2, 5.7, 6.5, 8.3, 8.4 | AC 中包含降级行为描述 |
| OBS（可观测性） | 8.1, 8.2 | 专属 Story 覆盖 |
