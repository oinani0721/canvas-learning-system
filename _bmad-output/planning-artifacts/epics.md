---
stepsCompleted:
  - step-01-validate-prerequisites
  - step-02-design-epics
  - step-03-create-stories
  - step-04-final-validation
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture.md
  - '/Users/Heishing/Desktop/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md'
---

# Canvas Learning System — Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for Canvas Learning System (Obsidian Hybrid), decomposing the 85 FRs (12 capability domains) + 9 NFR categories from the BMAD PRD into 9 user-value-driven Epics and ~54 implementable stories.

**Source PRD**: `_bmad-output/planning-artifacts/prd.md` (706 lines, 2026-04-12)
**Anchor PRD**: `14-scheme-a-implementation-prd.md` (7594 lines, read-only)

---

## Requirements Inventory

### Functional Requirements

**FR-CONV (学习对话与知识探索) — 11 FRs**
- FR-CONV-01: 学习者可以启动 AI 对话，系统自动发现当前笔记的相邻概念并注入对话上下文
- FR-CONV-02: 系统可以在对话中基于个人历史误解主动提醒学习者
- FR-CONV-03: 学习者可以在对话回答中看到可点击的补充学习材料列表
- FR-CONV-04: 对话上下文自动注入当前笔记的 1-hop 邻居信息
- FR-CONV-05: 学习者可以在对话中通过 callout 批注标记关键知识点（Tips）
- FR-CONV-06: 系统自动从对话中提取、分类并归档学习者的错误（4 主类 + 2 子类）
- FR-CONV-07: 系统可以在对话结束时自动归档会话到长期记忆
- FR-CONV-08: 学习者可以从对话中选取内容提取为新的知识节点
- FR-CONV-09: 对话消息按时间进行三层归档
- FR-CONV-10: 系统可以通过 Edge 语义检索相关前序笔记讨论摘要
- FR-CONV-11: 系统可以在上下文压缩时保留关键学习数据并通知学习者

**FR-EDGE (Edge 对话) — 4 FRs**
- FR-EDGE-01: 学习者可以选中两个概念之间的关系启动深度讨论
- FR-EDGE-02: 系统在 Edge 讨论中同时激活 EI 和 SE 两种学习策略
- FR-EDGE-03: 系统记录学习者对关系的解释理由，存储为结构化语义标签
- FR-EDGE-04: Edge 讨论自动注入两端概念的掌握度和历史记忆

**FR-EXAM (考察与评估) — 22 FRs**
- FR-EXAM-01: 学习者可以生成完全空白的检验白板考察（信息隔离）
- FR-EXAM-02: 系统基于 BKT/FSRS 自动选出薄弱节点
- FR-EXAM-03: 系统融合三路数据生成个人化题目
- FR-EXAM-04: 系统对回答进行 4 维 4 分制评分
- FR-EXAM-05: 学习者在 md 编辑器中手写答案并手动提交（D14 锁定）
- FR-EXAM-06: 系统静默评分，结果更新掌握度
- FR-EXAM-07: 4 级渐进提示（方向→关键词→框架→脚手架）
- FR-EXAM-08: 跳过题目且不受惩罚
- FR-EXAM-09: 基于 callout 批注触发快速考察
- FR-EXAM-10: 防止在检验白板内再次生成检验白板
- FR-EXAM-11: 三种考察模式
- FR-EXAM-12: 系统根据内容类型推荐考察模式
- FR-EXAM-13: 按白板类型定制出题策略
- FR-EXAM-14: 考中书签式概念提取
- FR-EXAM-15: 考后校准投票
- FR-EXAM-16: 节点切换时自动后台评分
- FR-EXAM-17: 数据变更同步回源白板
- FR-EXAM-18: 考察记录永久保存
- FR-EXAM-19: IRT 连续难度匹配 ≥ 70%
- FR-EXAM-20: 确认的新节点可继续讨论
- FR-EXAM-21: 不限数量的检验白板
- FR-EXAM-22: 三重信息隔离保证

**FR-KG (知识图谱构建) — 9 FRs**
- FR-KG-01: 通过双向链接创建概念间关系
- FR-KG-02: 从对话/考察中提取新概念并创建文件
- FR-KG-03: 从笔记自动提取概念关系（Graphify）
- FR-KG-04: 考中书签式提取不中断流程
- FR-KG-05: 三级置信度标注
- FR-KG-06: 概念关系 frontmatter relationships[] 记录
- FR-KG-07: 概念关系图 71x 压缩检索
- FR-KG-08: 知识图谱健康检查
- FR-KG-09: 图片内容纳入知识图谱上下文

**FR-MAST (掌握度追踪) — 6 FRs**
- FR-MAST-01: BKT 模型实时更新
- FR-MAST-02: FSRS 最优复习间隔
- FR-MAST-03: 5 信号融合
- FR-MAST-04: 评分操作链顺序完整性
- FR-MAST-05: 2x2 元认知校准矩阵追踪
- FR-MAST-06: 仅通过考察更新掌握度

**FR-MEM (学习记忆管理) — 6 FRs**
- FR-MEM-01: 错误 4 类分类双写
- FR-MEM-02: 校准数据记录
- FR-MEM-03: AI 评分投票反馈
- FR-MEM-04: 3 层记忆检索
- FR-MEM-05: 异步非阻塞写入
- FR-MEM-06: Hot/Warm/Cold 消息归档

**FR-VIZ (学习进度可视化) — 6 FRs**
- FR-VIZ-01: 全局 Dashboard 三层布局
- FR-VIZ-02: 处方性措辞
- FR-VIZ-03: 元认知 2x2 校准矩阵视图
- FR-VIZ-04: 一键启动考察
- FR-VIZ-05: 单概念详细档案
- FR-VIZ-06: 正面措辞

**FR-SPACE (间隔复习与错误修正) — 5 FRs**
- FR-SPACE-01: Dashboard NextReview + Bases 表格过滤提醒
- FR-SPACE-02: 复习时注入历史误解
- FR-SPACE-03: 辨析题验证纠正
- FR-SPACE-04: 复习任务列表
- FR-SPACE-05: FSRS 自适应复习间隔

**FR-SYS (Vault 管理与配置) — 6 FRs**
- FR-SYS-01: Templater 模板自动生成
- FR-SYS-02: Hotkey 自定义绑定
- FR-SYS-03: 可选 Git 备份
- FR-SYS-04: Hotkey 冲突检测
- FR-SYS-05: KG 索引健康检查
- FR-SYS-06: 首次安装引导

**FR-ADAPT (架构适配) — 3 FRs**
- FR-ADAPT-01: 双向链接图遍历邻居发现
- FR-ADAPT-02: 双向链接图上下文组装
- FR-ADAPT-03: 双向链接图热更新

**FR-OBS (可观测性) — 4 FRs**
- FR-OBS-01: 记忆操作摘要行
- FR-OBS-02: 连接状态指示
- FR-OBS-03: 操作审计日志
- FR-OBS-04: 写入失败通知

**FR-MM (多模态学习) — 3 FRs**
- FR-MM-01: 笔记图片识别纳入对话上下文
- FR-MM-02: 基于图片内容发起 AI 讨论
- FR-MM-03: 图片内容作为考察出题素材

### Non-Functional Requirements

- NFR-PERF: 性能（LLM < 5s P95 · Dashboard < 1s · 图构建 < 2s · 遍历 < 200ms · Graphify < 30s · LanceDB < 500ms · 记忆搜索 < 3s · 写入 < 10s）
- NFR-INT: 数据完整性（frontmatter 安全 · 写入原子性 · 数据本地性 · 隐私保护）
- NFR-REL: 集成可靠性（MCP 14/14 · 评分链 5 步 · 图热更新 · 读写时序 · 级联触发）
- NFR-DEG: 优雅降级（6 场景：插件崩溃 · API 离线 · Graphiti 不可用 · Graphify 失败 · 隔离失败 · 写入失败）
- NFR-OBS: 可观测性（Skill 摘要 · 连接指示 · 审计日志 · 断开通知）
- NFR-SEC: 安全与隐私（数据本地化 · API Key 安全 · localhost 绑定 · 注入防护 · 无遥测）
- NFR-A11Y: 无障碍（键盘导航 · 颜色对比 ≥ 4.5:1 · 处方性颜色）
- NFR-COMPAT: 兼容性（Obsidian v1.5+ · macOS M-series · Python 3.12+ · Neo4j 5.x · Ollama · Claude API）
- NFR-MAINT: 可维护性（MCP schema 100% · Prompt 回归 ≥ 80% · 算法覆盖 ≥ 90% · 端到端 100%）

### Architecture Requirements

- AR1: 后端启动顺序：Neo4j → Ollama(bge-m3) → FastAPI → MCP → 就绪
- AR2: Hot-Warm-Cold 三层时间归档（0-30d / 30-180d / 180d+）
- AR3: 4 类错误自动分类器差异化补救路由
- AR4: AutoSCORE 两阶段隐形评分（证据提取 → 4维4分制 × 3次采样多数投票）
- AR5: RAG 增量索引管道（content_hash 去重 + 标题智能分块 + 面包屑前缀）
- AR6: 检索后处理（reranker 精排 + Adaptive-k + A-RAG 迭代验证）
- AR7: 上下文压缩（公式/代码整块保护）
- AR8: pipeline_token 5 步防篡改链
- AR9: Token 成本追踪 + 按任务统计
- AR10: 离线降级 4 场景
- AR11: context_enrichment 重构为 wikilink 图遍历

---

## FR Coverage Map

| FR | Epic | Story | 简述 |
|----|------|-------|------|
| FR-CONV-01 | 2 | 2.1 | AI 对话 + 邻居上下文 |
| FR-CONV-02 | 2 | 2.3 | 历史误解提醒 |
| FR-CONV-03 | 2 | 2.2 | 补充材料列表 |
| FR-CONV-04 | 2 | 2.1 | 1-hop 邻居注入 |
| FR-CONV-05 | 2 | 2.4 | Callout Tips |
| FR-CONV-06 | 2 | 2.5 | 错误自动提取 |
| FR-CONV-07 | 2 | 2.6 | 对话归档 |
| FR-CONV-08 | 2 | 2.7 | 新概念提取 |
| FR-CONV-09 | 2 | 2.6 | 三层消息归档 |
| FR-CONV-10 | 2 | 2.7 | Edge 语义注入 |
| FR-CONV-11 | 2 | 2.7 | 压缩数据保留 |
| FR-EDGE-01 | 6 | 6.1 | Edge 讨论触发 |
| FR-EDGE-02 | 6 | 6.2 | EI+SE 双策略 |
| FR-EDGE-03 | 6 | 6.3 | 语义标签存储 |
| FR-EDGE-04 | 6 | 6.1 | Edge 上下文注入 |
| FR-EXAM-01 | 4 | 4.1 | 空白检验白板 |
| FR-EXAM-02 | 4 | 4.2 | 薄弱节点选题 |
| FR-EXAM-03 | 4 | 4.3 | 三路融合出题 |
| FR-EXAM-04 | 4 | 4.6 | 4D4 分评分 |
| FR-EXAM-05 | 4 | 4.5 | MD 答题提交 |
| FR-EXAM-06 | 4 | 4.6 | 静默评分 |
| FR-EXAM-07 | 4 | 4.7 | 渐进提示 |
| FR-EXAM-08 | 4 | 4.7 | 跳过不惩罚 |
| FR-EXAM-09 | 4 | 4.11 | Callout 考察 |
| FR-EXAM-10 | 4 | 4.1 | 防嵌套 |
| FR-EXAM-11 | 4 | 4.4 | 三种考察模式 |
| FR-EXAM-12 | 4 | 4.4 | 模式推荐 |
| FR-EXAM-13 | 4 | 4.3 | 出题策略定制 |
| FR-EXAM-14 | 4 | 4.8 | 书签式提取 |
| FR-EXAM-15 | 4 | 4.9 | 校准投票 |
| FR-EXAM-16 | 4 | 4.6 | 隐形评分 |
| FR-EXAM-17 | 4 | 4.9 | 数据同步回源 |
| FR-EXAM-18 | 4 | 4.10 | 永久记录 |
| FR-EXAM-19 | 4 | 4.11 | IRT 难度匹配 |
| FR-EXAM-20 | 4 | 4.8 | 新节点继续讨论 |
| FR-EXAM-21 | 4 | 4.10 | 不限数量白板 |
| FR-EXAM-22 | 4 | 4.1 | 三重隔离保证 |
| FR-KG-01 | 3 | 3.1 | Wikilink 关系 |
| FR-KG-02 | 3 | 3.1 | 概念提取创建 |
| FR-KG-03 | 3 | 3.2 | Graphify 提取 |
| FR-KG-04 | 3 | 3.4 | 书签式考中提取 |
| FR-KG-05 | 3 | 3.2 | 三级置信度 |
| FR-KG-06 | 3 | 3.3 | frontmatter 关系记录 |
| FR-KG-07 | 3 | 3.3 | 71x 压缩检索 |
| FR-KG-08 | 3 | 3.5 | KG 健康检查 |
| FR-KG-09 | 3 | 3.5 | 图片入图 |
| FR-MAST-01 | 5 | 5.1 | BKT 更新 |
| FR-MAST-02 | 5 | 5.2 | FSRS 间隔 |
| FR-MAST-03 | 5 | 5.3 | 5 信号融合 |
| FR-MAST-04 | 5 | 5.4 | 评分链完整性 |
| FR-MAST-05 | 8 | 8.3 | 2x2 校准矩阵 |
| FR-MAST-06 | 5 | 5.3 | 仅考察更新 |
| FR-MEM-01 | 5 | 5.5 | 错误双写 |
| FR-MEM-02 | 5 | 5.6 | 校准数据 |
| FR-MEM-03 | 5 | 5.6 | 评分投票 |
| FR-MEM-04 | 5 | 5.7 | 3 层检索 |
| FR-MEM-05 | 5 | 5.8 | 异步写入 |
| FR-MEM-06 | 5 | 5.8 | Hot/Warm/Cold |
| FR-VIZ-01 | 8 | 8.1 | Dashboard 三层 |
| FR-VIZ-02 | 8 | 8.2 | 处方性措辞 |
| FR-VIZ-03 | 8 | 8.3 | 2x2 矩阵视图 |
| FR-VIZ-04 | 8 | 8.4 | 一键考察 |
| FR-VIZ-05 | 8 | 8.4 | 概念档案 |
| FR-VIZ-06 | 8 | 8.2 | 正面措辞 |
| FR-SPACE-01 | 7 | 7.2 | NextReview+Bases 提醒 |
| FR-SPACE-02 | 7 | 7.3 | 误解注入 |
| FR-SPACE-03 | 7 | 7.4 | 辨析题 |
| FR-SPACE-04 | 7 | 7.1 | 任务列表 |
| FR-SPACE-05 | 7 | 7.2 | FSRS 时机 |
| FR-SYS-01 | 1 | 1.1 | Templater 模板 |
| FR-SYS-02 | 1 | 1.4 | Hotkey 绑定 |
| FR-SYS-03 | 1 | 1.6 | Git 备份 |
| FR-SYS-04 | 1 | 1.5 | Hotkey 冲突 |
| FR-SYS-05 | 1 | 1.6 | KG 健康检查 |
| FR-SYS-06 | 1 | 1.1 | 安装引导 |
| FR-ADAPT-01 | 1 | 1.2 | 图遍历邻居 |
| FR-ADAPT-02 | 1 | 1.3 | 图上下文组装 |
| FR-ADAPT-03 | 1 | 1.2 | 图热更新 |
| FR-OBS-01 | 8 | 8.5 | 记忆摘要行 |
| FR-OBS-02 | 8 | 8.6 | 连接状态 |
| FR-OBS-03 | 8 | 8.7 | 审计日志 |
| FR-OBS-04 | 8 | 8.6 | 写入失败通知 |
| FR-MM-01 | 2 | 2.8 | 图片识别对话 |
| FR-MM-02 | 2 | 2.8 | 图片 AI 讨论 |
| FR-MM-03 | 9 | 9.1 | 图片考察素材 |

**Coverage: 85/85 FRs mapped (100%)**

---

## Epic List

| Epic | 名称 | Phase | 旅程 | FR 数 | Story 数 |
|------|------|-------|------|-------|---------|
| 1 | 学习环境搭建与冷启动 | 1 | 4 | 9 | 6 |
| 2 | 智能学习对话 | 1 | 1,5 | 13 | 8 |
| 3 | 知识图谱构建 | 1-2 | 1 | 9 | 5 |
| 4 | 检验白板 Active Recall（灵魂） | 1 | 2 | 22 | 11 |
| 5 | 掌握度追踪与记忆管理 | 1-2 | 2,3 | 12 | 8 |
| 6 | Edge 对话与深度剖析 | 2 | 1 | 4 | 3 |
| 7 | 错误修正与间隔复习 | 2 | 3 | 5 | 4 |
| 8 | 学习 Dashboard 与可观测性 | 2 | 6 | 10 | 7 |
| 9 | 多模态增强与持续改进 | 3 | 5 | 1 | 2 |

---

## Epic 1: 学习环境搭建与冷启动

学习者可以拥有一个配置完整的 Obsidian vault，模板自动生成、hotkey 就绪、后端连通、wikilink 图遍历可用，开始第一次学习。

**FRs:** FR-SYS-01~06, FR-ADAPT-01~03
**NFRs:** NFR-COMPAT (全部), NFR-PERF (图构建 < 2s, 遍历 < 200ms), NFR-REL (MCP 14/14), NFR-SEC (本地化, localhost), NFR-A11Y (键盘), NFR-MAINT (MCP schema)
**Depends on:** 无
**Phase:** 1 MVP · 旅程 4（冷启动）

### Story 1.1: Vault 初始化 + Templater 模板

As a 学习者,
I want vault 初始化和 Templater 模板自动就绪,
So that 我新建概念/考察文件时自动获得标准 frontmatter 结构。

**Acceptance Criteria:**

**Given** 学习者首次打开 canvas-vault
**When** 运行安装引导
**Then** vault 目录结构（raw/ · wiki/concepts/ · wiki/canvases/ · outputs/exam_boards/ · CLAUDE.md）自动创建
**And** 3 强制插件 + Obsidian Bases 原生已就绪（Dataview/Templater/QuickAdd + Bases（交互式表格/卡片视图，原生核心插件））
**And** 后端启动顺序验证通过（Neo4j → Ollama → FastAPI → MCP · AR1）

**Given** 学习者用 Templater 创建新概念文件
**When** 触发 concept.md 模板
**Then** frontmatter 包含 mastery/bkt/fsrs/errors/tips 等标准字段
**And** 已有笔记不被模板自动修改

**Given** 学习者用 Templater 创建新考察文件
**When** 触发 exam-board.md 模板
**Then** frontmatter 包含 type: exam_board + source_canvas + selected_nodes + questions 等字段

### Story 1.2: Wikilink 图构建与邻居发现

As a 系统,
I want 解析 vault 中所有 .md 文件的 wikilinks 构建双向链接图,
So that AI 对话和考察能发现概念间的邻居关系。

**Acceptance Criteria:**

**Given** vault 包含 ~200 个 .md 文件和 ~500 个 wikilinks
**When** 后端启动时构建图
**Then** 图构建完成 < 2s（NFR-PERF）
**And** 2-hop 邻居遍历 < 200ms（NFR-PERF）
**And** 循环链接不导致无限遍历

**Given** 学习者编辑 .md 文件并保存
**When** 文件变更事件触发
**Then** 图增量更新（非全量重建）
**And** 更新后遍历结果立即反映变化

### Story 1.3: Wikilink 上下文组装

As a 系统,
I want 基于 wikilink 图为 AI 对话组装完整上下文包,
So that AI 能理解当前概念与邻居的关系和掌握度。

**Acceptance Criteria:**

**Given** 学习者在某概念笔记上启动 AI 对话
**When** 系统组装上下文
**Then** 上下文包含当前笔记 + N-hop 邻居的 frontmatter + 内容摘要 + Tips + 错误记录 + Edge 理由
**And** 压缩后不超过 token 预算（AR7）
**And** 公式和代码块整块保护不切断

### Story 1.4: Hotkey 绑定配置

As a 学习者,
I want 为 6 个 Skill 配置自定义快捷键,
So that 我可以通过键盘快速触发学习操作。

**Acceptance Criteria:**

**Given** 学习者打开 Obsidian Hotkeys 设置面板
**When** 搜索 "Canvas"
**Then** 显示 6 个 Skill 命令（中文名称）
**And** 学习者可以为每个命令绑定自定义快捷键
**And** 快捷键在所有 UI 区域全局响应

### Story 1.5: Hotkey 冲突检测

As a 学习者,
I want 启动时自动检测快捷键冲突,
So that 我不会因冲突而无法触发 Skill。

**Acceptance Criteria:**

**Given** 两个命令绑定了相同的快捷键
**When** Obsidian 启动
**Then** 显示警告通知（列出冲突命令，持续 8 秒）
**And** 不自动修改任何绑定

**Given** 无快捷键冲突
**When** Obsidian 启动
**Then** 不显示任何通知

**Given** 其他插件的快捷键
**When** 检测冲突
**Then** 只检查本插件命令，不产生误报

### Story 1.6: Git 备份 + KG 索引健康检查

As a 学习者,
I want 可选的 Git 自动备份和知识图谱健康检查,
So that 我的数据安全且图谱结构健康。

**Acceptance Criteria:**

**Given** 学习者启用了 Obsidian Git 插件
**When** 自动备份触发
**Then** 备份异步运行，不阻塞学习操作
**And** 系统在无 Git 备份时仍正常工作

**Given** 学习者触发健康检查
**When** 系统扫描知识图谱索引
**Then** 报告孤立节点数量、矛盾关系和置信度分布

---

## Epic 2: 智能学习对话

学习者可以和 AI 进行有上下文感知的对话。AI 通过 wikilink 图遍历获取相邻概念、注入个人历史记忆、显示补充学习材料，自动提取错误并归档到 Graphiti。

**FRs:** FR-CONV-01~11, FR-MM-01~02
**NFRs:** NFR-PERF (LLM < 5s, 记忆搜索 < 3s), NFR-INT (frontmatter 安全, 只传筛选片段), NFR-SEC (注入防护), NFR-DEG (API 离线降级)
**Depends on:** Epic 1 (wikilink 图, vault 模板)
**Phase:** 1 MVP · 旅程 1（日常学习）+ 旅程 5（图片学习）

### Story 2.1: AI 对话 + 邻居上下文注入

As a 学习者,
I want 启动 AI 对话时系统自动注入相邻概念和掌握度信息,
So that AI 的回答基于我笔记的实际结构和我的学习状态。

**Acceptance Criteria:**

**Given** 学习者在某笔记页面启动 AI 对话
**When** 对话启动
**Then** 系统调用 wikilink 图遍历获取 2-hop 邻居
**And** 将当前笔记 + 邻居的 frontmatter/内容摘要注入 LLM 上下文
**And** 上下文压缩后不超过 token 预算（AR7）
**And** LLM 首 token < 5s P95（NFR-PERF）

### Story 2.2: 补充学习材料搜索

As a 学习者,
I want 对话回答中看到可点击的补充学习材料列表,
So that 我可以深入探索相关内容。

**Acceptance Criteria:**

**Given** AI 回答涉及可关联的概念
**When** 回答生成完成
**Then** 附带语义搜索结果列表（最多 5 条）
**And** 每条结果可点击跳转到对应笔记

### Story 2.3: 历史误解主动提醒

As a 学习者,
I want AI 在对话中基于我的历史误解主动提醒,
So that 我不会重复犯同样的错误。

**Acceptance Criteria:**

**Given** 学习者讨论的概念有历史误解记录
**When** 系统从长期记忆检索到相关错误
**Then** AI 回答中自然融入提醒（非生硬插入）
**And** 记忆搜索 < 3s（NFR-PERF）
**And** Graphiti 不可用时静默跳过（NFR-DEG）

### Story 2.4: Callout 批注标记 Tips

As a 学习者,
I want 在对话中用 callout 批注标记关键知识点,
So that 系统能识别我的 Tips 并在后续考察中使用。

**Acceptance Criteria:**

**Given** 学习者在笔记中写 `[!tip]+` callout
**When** 保存笔记
**Then** 系统识别 Tips 并更新 frontmatter 的 tips[] 字段
**And** Tips 在后续 AI 对话和考察中作为上下文注入

### Story 2.5: 错误自动提取与分类

As a 学习者,
I want 系统自动从对话中提取我的错误并分类,
So that 我的错误被记录用于个人化出题。

**Acceptance Criteria:**

**Given** AI 对话中检测到学习者的误解
**When** 对话轮次结束
**Then** 系统自动提取错误并分类为 4 主类之一（概念混淆/推理谬误/粗心/元认知）
**And** 错误双写到 frontmatter errors[] 和 Graphiti
**And** 不同错误类型关联差异化补救策略（AR3）

### Story 2.6: 对话归档与三层消息管理

As a 学习者,
I want 对话结束后自动归档到长期记忆,
So that 历史学习对话可以被检索并用于个人化。

**Acceptance Criteria:**

**Given** 对话 session 结束
**When** 系统触发归档
**Then** 会话完整保存到 Graphiti 长期记忆
**And** 消息按 Hot-Warm-Cold 三层归档（0-30d 完整 → 30-180d 摘要 → 180d+ 仅提取 · AR2）
**And** 归档异步执行，不阻塞用户操作

### Story 2.7: 新概念提取 + Edge 语义注入 + 压缩保留

As a 学习者,
I want 从对话中提取新概念并在上下文压缩时保留关键数据,
So that 知识图谱持续增长且重要信息不丢失。

**Acceptance Criteria:**

**Given** 学习者在对话中选取内容
**When** 触发提取操作
**Then** 系统创建新的概念 .md 文件并自动建议与原节点的关系
**And** 通过 Edge 语义检索注入相关前序讨论摘要

**Given** 上下文窗口压缩发生
**When** 系统执行压缩
**Then** 保留 Tips、错误记录、掌握度状态
**And** 通知学习者压缩已发生

### Story 2.8: 图片识别对话

As a 学习者,
I want 贴入图片后 AI 能识别并讨论图片内容,
So that 我可以用图片辅助学习。

**Acceptance Criteria:**

**Given** 学习者在笔记中嵌入图片
**When** 启动 AI 对话
**Then** AI 原生图像识别分析图片内容
**And** 图片内容纳入对话上下文
**And** 降级：图片不自动持久化到知识图谱索引

---

## Epic 3: 知识图谱构建

学习者可以从对话中提取新概念创建双向链接，探索概念间关系，并通过 Graphify 自动提取隐含关系生成 AI 检索索引。

**FRs:** FR-KG-01~09
**NFRs:** NFR-PERF (Graphify < 30s, LanceDB < 500ms), NFR-DEG (Graphify 失败降级)
**Depends on:** Epic 1 (vault 结构, 图遍历)
**Phase:** 1-2 · 旅程 1（日常学习 — 深度剖析）

### Story 3.1: 概念提取 + Wikilink 创建

As a 学习者,
I want 从对话或考察中提取新概念时自动创建双向链接文件,
So that 知识图谱自然增长。

**Acceptance Criteria:**

**Given** 学习者在对话中提取新概念
**When** 触发 `/extract_node`
**Then** 在 wiki/concepts/ 下创建新 .md 文件（Templater 标准 frontmatter）
**And** 在原笔记中插入 `[[new-concept]]` wikilink
**And** 系统自动建议与原概念的关系类型

### Story 3.2: Graphify 关系提取 + 置信度

As a 系统,
I want 通过 Graphify 从笔记中自动提取概念关系,
So that AI 有 71x token 压缩的知识图谱检索索引。

**Acceptance Criteria:**

**Given** 学习者触发 Graphify 索引
**When** Graphify 处理 wiki/ 目录
**Then** 生成独立的 graph.json（不修改用户 wikilinks）
**And** 全量索引 < 30s for ~100 文件（NFR-PERF）
**And** 每个概念标注三级置信度（EXTRACTED / INFERRED / AMBIGUOUS）

### Story 3.3: 概念关系 frontmatter + 71x 检索

As a 学习者,
I want 在概念文件的 frontmatter relationships[] 中记录概念间关系，存储语义类型和讨论历史,
So that 概念间关系有结构化记录。

**Acceptance Criteria:**

**Given** 学习者确认两个概念间的关系
**When** 系统记录关系
**Then** 概念文件 frontmatter 的 relationships[] 中新增关系条目（含语义类型和讨论历史）
**And** 通过概念关系图提供补充学习材料时实现 71x token 压缩

### Story 3.4: 书签式考中提取

As a 学习者,
I want 在考察中提取新概念时不中断当前流程,
So that Active Recall 不被打断。

**Acceptance Criteria:**

**Given** 学习者在检验白板考察中发现新概念
**When** 触发提取操作
**Then** 系统只插入书签标记（`[!discussion_later]+`）
**And** 不切换 Tab，不打开新文件
**And** 考后可通过书签找到待讨论的概念

### Story 3.5: KG 健康检查 + 图片入图

As a 学习者,
I want 知识图谱健康检查和图片内容纳入图谱,
So that 图谱结构健康且多模态内容可被检索。

**Acceptance Criteria:**

**Given** 学习者触发健康检查
**When** 系统扫描 Graphify 索引
**Then** 报告孤立节点、矛盾关系、置信度分布

**Given** 笔记中嵌入图片
**When** AI 识别图片内容
**Then** 识别出的概念信息可作为知识图谱上下文

---

## Epic 4: 检验白板 Active Recall — 灵魂 Epic

学习者可以在完全空白的检验白板中接受个人化考察。系统通过三路融合出题，支持 md 编辑器手写答案、静默评分、4 级渐进提示、跳过不惩罚、书签式概念提取和防嵌套保护。这是产品灵魂——Karpicke 2011 Retrieval Practice d=1.50 的 100% 等价实现。

**FRs:** FR-EXAM-01~22 (全部 22 条)
**NFRs:** NFR-PERF (LLM < 5s), NFR-INT (frontmatter 安全, 评分链), NFR-REL (评分链 5 步, 级联触发), NFR-DEG (隔离失败 → callout 降级), NFR-MAINT (Prompt 回归)
**Depends on:** Epic 1 (模板), Epic 2 (对话基础), Epic 3 (KG 出题素材)
**Phase:** 1 MVP · 旅程 2（灵魂旅程，95% 守恒）

### Story 4.1: 信息隔离 + 防嵌套

As a 学习者,
I want 检验白板打开时完全看不到笔记原文,
So that 我在纯 Active Recall 环境中学习。

**Acceptance Criteria:**

**Given** 学习者启动检验白板
**When** exam_boards/*.md 打开
**Then** 零 wiki/concepts/ 内容泄漏（三重保证：type 标记 + AI 上下文重置 + Skill prompt 约束 · FR-EXAM-22）
**And** 已在检验白板内时禁止再次生成检验白板（FR-EXAM-10）
**And** 防嵌套检查先于所有其他操作

### Story 4.2: 薄弱节点选题

As a 系统,
I want 基于 BKT/FSRS 掌握度自动选出薄弱节点,
So that 考察聚焦学习者最需要强化的知识。

**Acceptance Criteria:**

**Given** 学习者启动考察
**When** 系统查询掌握度数据
**Then** 选出掌握度最低的 N 个节点作为考察范围
**And** 选题结果排除已完全掌握（≥ 0.90）的节点

### Story 4.3: 三路融合出题 + 出题策略

As a 系统,
I want 融合三路数据生成个人化题目,
So that 考察精准针对学习者的薄弱点。

**Acceptance Criteria:**

**Given** 选定考察节点
**When** 系统生成题目
**Then** 融合个人记忆（Graphiti）+ 知识图谱关系（Graphify）+ 掌握度数据（frontmatter）
**And** 知识点白板侧重定义辨析，题目白板侧重易错点和破题方法（FR-EXAM-13）
**And** LLM 出题 < 5s P95（NFR-PERF）

### Story 4.4: 考察模式选择

As a 学习者,
I want 选择考察模式或接受系统推荐,
So that 考察方式匹配我的学习需求。

**Acceptance Criteria:**

**Given** 学习者启动考察
**When** 进入模式选择
**Then** 提供三种模式：点对点突破 · 综合题考察 · 混合模式
**And** 系统根据白板内容类型推荐模式（可覆盖）

### Story 4.5: MD 编辑器答题 + 提交

As a 学习者,
I want 在 markdown 编辑器中手写答案并手动提交,
So that 答题过程就像写批注（D14 用户哲学选择）。

**Acceptance Criteria:**

**Given** 系统出题完毕
**When** 学习者在 md 编辑器中写完答案
**Then** 手动触发提交（非自动检测）
**And** 答案永久保存在 exam_boards/*.md 中
**And** AI 侧边栏不显示题目/分数/提示等实质学习内容

### Story 4.6: 静默评分 + AutoSCORE

As a 系统,
I want 对学习者的回答静默评分,
So that 评分过程不打断学习 Flow。

**Acceptance Criteria:**

**Given** 学习者提交答案
**When** 系统触发评分
**Then** 执行 AutoSCORE 两阶段评分（证据提取→4维4分制 · AR4）
**And** 学习者不感知评分过程
**And** 结果更新 frontmatter 掌握度数据
**And** 节点切换时自动触发后台评分（FR-EXAM-16）

### Story 4.7: 4 级渐进提示 + 跳过不惩罚

As a 学习者,
I want 答不出时请求渐进提示或跳过,
So that 我既能获得帮助又不被迫回答。

**Acceptance Criteria:**

**Given** 学习者答不出题目
**When** 请求提示
**Then** 提供 4 级渐进提示：方向→关键词→框架→脚手架
**And** 每次点击升一级
**And** 不提供"直接告诉答案"选项

**Given** 学习者选择跳过
**When** 跳过题目
**Then** 标记为未作答，不惩罚 BKT/FSRS

### Story 4.8: 考中书签式概念提取

As a 学习者,
I want 考察中发现新概念时不中断考察,
So that Active Recall 不被打断。

**Acceptance Criteria:**

**Given** 考察中学习者发现不懂的概念
**When** 触发提取
**Then** 插入 `[!discussion_later]+` 书签，不切 Tab
**And** 确认的新节点可继续深入讨论（FR-EXAM-20）
**And** 考后可通过书签回到待讨论概念

### Story 4.9: 校准投票 + 数据同步

As a 学习者,
I want 考后对 AI 评分投票反馈并同步数据到源白板,
So that AI 评分越来越准确。

**Acceptance Criteria:**

**Given** 评分完成后话题切换
**When** 系统询问"你觉得评分准确吗"
**Then** 学习者可反馈偏高/偏低/准确（可选不强制）
**And** 反馈标记为 few-shot 校准样本

**Given** 考察中产生数据变更
**When** Tips/新节点/掌握度更新
**Then** 变更同步回源知识白板（FR-EXAM-17）

### Story 4.10: 考察记录持久化

As a 学习者,
I want 每次考察的完整记录永久保存,
So that 我可以回顾历史考察。

**Acceptance Criteria:**

**Given** 考察结束
**When** 系统保存记录
**Then** 完整考察记录永久保存（对话 + 评分 + 掌握度变化 + 新发现节点）
**And** 可在 Dashboard 查看历史
**And** 同一知识白板可生成不限数量的检验白板

### Story 4.11: IRT 难度匹配 + Callout 快速考察

As a 学习者,
I want 题目难度匹配我的掌握水平，且可以从批注触发快速考察,
So that 考察既不太简单也不太难。

**Acceptance Criteria:**

**Given** 系统生成题目
**When** 匹配难度
**Then** 采用连续 IRT difficulty 参数（非离散分级）
**And** 难度匹配率 ≥ 70%（FR-EXAM-19）

**Given** 学习者在笔记中选中 callout 批注
**When** 触发快速考察
**Then** 基于该批注内容生成针对性题目（FR-EXAM-09）

---

## Epic 5: 掌握度追踪与记忆管理

系统准确追踪每个概念的掌握程度（BKT+FSRS+5 信号融合），记录错误（4 类分类双写），管理学习记忆（3 层检索+异步写入），支持校准投票。

**FRs:** FR-MAST-01~04,06, FR-MEM-01~06
**NFRs:** NFR-PERF (记忆搜索 < 3s, 写入 < 10s), NFR-INT (写入原子性, 评分链), NFR-REL (读写时序, 级联触发), NFR-DEG (Graphiti 不可用降级), NFR-MAINT (算法覆盖 ≥ 90%)
**Depends on:** Epic 4 (考察产生掌握度数据)
**Phase:** 1-2 · 支撑旅程 2 + 旅程 3

### Story 5.1: BKT 掌握概率更新

As a 系统,
I want 使用 BKT 模型实时更新每个概念的掌握概率,
So that 掌握度反映学习者的真实水平。

**Acceptance Criteria:**

**Given** 考察评分完成
**When** 系统更新 BKT
**Then** p_mastery 基于贝叶斯公式更新
**And** 新概念默认 BKT=0.30 先验
**And** 更新写入 frontmatter bkt_p_mastery 字段

### Story 5.2: FSRS 复习间隔计算

As a 系统,
I want 使用 FSRS 算法计算最优复习间隔,
So that 间隔复习时机科学。

**Acceptance Criteria:**

**Given** 掌握度更新完成
**When** 系统计算 FSRS
**Then** 更新 frontmatter fsrs_* 字段（stability, difficulty, next_review_date）
**And** 复习间隔随掌握度自适应

### Story 5.3: 5 信号融合 + 仅考察更新

As a 系统,
I want 融合 5 个信号为单维掌握度,
So that 掌握度评估全面且稳健。

**Acceptance Criteria:**

**Given** BKT + FSRS + 错误历史 + 校准偏差 + 自评置信度 5 个信号
**When** 系统执行融合
**Then** 信号互补性 r < 0.7
**And** 融合后掌握度与考察表现 Spearman rho > 0.6
**And** 掌握度仅通过考察更新（非自评修改 · FR-MAST-06）

### Story 5.4: 评分操作链完整性

As a 系统,
I want 保证评分操作链顺序不可跳步,
So that 算法管道不被篡改。

**Acceptance Criteria:**

**Given** 考察评分流程
**When** 执行 5 步链（出题→评分→BKT→FSRS→校准）
**Then** 每步产生 pipeline_token，下步必须携带上步 token（AR8）
**And** 跳步时后端拒绝执行
**And** EventBus 级联保证自动触发

### Story 5.5: 错误 4 类分类双写

As a 系统,
I want 记录学习者的错误并按 4 类分类存储,
So that 个人化出题能基于错误模式。

**Acceptance Criteria:**

**Given** 对话或考察中检测到错误
**When** 系统分类存储
**Then** 双写到 frontmatter errors[] 和 Graphiti
**And** 分类为 4 主类：概念混淆/推理谬误/粗心/元认知
**And** 写入原子性（失败不产生半截数据 · NFR-INT）

### Story 5.6: 校准数据 + 评分投票

As a 系统,
I want 记录学习者的校准数据和评分投票,
So that 评分精度持续改进。

**Acceptance Criteria:**

**Given** 学习者完成考后校准投票
**When** 系统记录
**Then** 校准数据（准确/偏高/偏低）写入 Graphiti
**And** 标记为 few-shot 校准样本
**And** 三阶段渐进：<100 题仅收集 / 100-400 趋势参考 / 400+ 统计可靠

### Story 5.7: 3 层记忆检索

As a 系统,
I want 通过 3 层检索找到学习者的历史记忆,
So that AI 对话和出题有个人化上下文。

**Acceptance Criteria:**

**Given** 需要检索学习者历史
**When** 系统执行搜索
**Then** 按 3 层优先级检索（知识图谱→图数据库→缓存）
**And** 搜索 < 3s（NFR-PERF）
**And** Graphiti 不可用时降级到默认先验（NFR-DEG）

### Story 5.8: 异步写入 + Hot/Warm/Cold 归档

As a 系统,
I want 异步非阻塞地写入学习事件并分层归档,
So that 写入不影响用户体验。

**Acceptance Criteria:**

**Given** 学习事件产生（评分/错误/归档）
**When** 系统写入
**Then** 异步非阻塞执行
**And** 写入 < 10s/episode（NFR-PERF）
**And** 失败自动重试 3 次 + 审计日志 + 通知
**And** 消息按 Hot-Warm-Cold 分层归档（AR2）

---

## Epic 6: Edge 对话与深度剖析

学习者可以选中两个概念之间的关系启动 EI+SE 双策略深度讨论，记录结构化的语义标签。

**FRs:** FR-EDGE-01~04
**NFRs:** NFR-PERF (LLM < 5s)
**Depends on:** Epic 2 (对话基础), Epic 3 (KG Edge 文件)
**Phase:** 2 · 旅程 1（深度剖析）

### Story 6.1: 关系讨论触发 + 上下文

As a 学习者,
I want 选中两个概念间的关系启动深度讨论,
So that 我能理解概念间的连接。

**Acceptance Criteria:**

**Given** 学习者选中两个概念间的关系（通过 frontmatter relationships[]）
**When** 触发 `/edge_discuss`
**Then** 自动注入两端概念的掌握度和历史记忆（从 frontmatter 读取）
**And** AI 询问学习者为何认为这两个概念相关

### Story 6.2: EI+SE 双策略激活

As a 系统,
I want 在 Edge 讨论中同时激活 EI 和 SE 策略,
So that 学习者同时练习精细化追问和自我解释。

**Acceptance Criteria:**

**Given** Edge 讨论进行中
**When** AI 引导讨论
**Then** 同时激活 Elaborative Interrogation（追问"为什么"）和 Self-Explanation（要求解释）
**And** 两种策略自然交替，不生硬

### Story 6.3: 语义标签存储

As a 系统,
I want 记录学习者对关系的解释并存储为结构化标签,
So that 关系解释可被后续检索使用。

**Acceptance Criteria:**

**Given** 关系讨论结束
**When** 系统存储结果
**Then** 解释理由存储为结构化语义标签（概念文件 frontmatter relationships[] 更新）
**And** 语义标签可被 Graphiti 和图遍历检索

---

## Epic 7: 错误修正与间隔复习

学习者在犯错后获得 Day 3 + Day 7 定时提醒，复习时自动注入历史误解上下文，通过辨析题验证误解已纠正。

**FRs:** FR-SPACE-01~05
**NFRs:** NFR-PERF (FSRS 计算), NFR-DEG (Graphiti 不可用降级)
**Depends on:** Epic 4 (考察产生错误), Epic 5 (记忆存储错误)
**Phase:** 2 · 旅程 3（错误修正闭环，90% 守恒）

### Story 7.1: 复习任务列表

As a 学习者,
I want 查看待完成的复习任务列表,
So that 我知道需要复习什么。

**Acceptance Criteria:**

**Given** 学习者有待复习的概念
**When** 查看任务列表
**Then** 显示待复习概念、截止日期和优先级
**And** 按 FSRS next_review_date 排序

### Story 7.2: Day 3 + Day 7 定时提醒

As a 系统,
I want 在 Day 3 和 Day 7 主动提醒学习者复习误解,
So that 间隔复习效应得以实现（Cepeda 2006, d≈0.55）。

**Acceptance Criteria:**

**Given** 学习者在 Day 0 标记了错误
**When** Day 3 到来
**Then** Dashboard 的 NextReview 查询 + Bases 表格过滤显示待复习项
**And** 复习间隔随掌握度自适应（FR-SPACE-05）

### Story 7.3: 复习时误解上下文注入

As a 系统,
I want 复习时自动注入历史误解上下文,
So that AI 能针对性帮助学习者纠正。

**Acceptance Criteria:**

**Given** 学习者进入复习
**When** 系统准备上下文
**Then** 从 3 层记忆检索注入历史误解
**And** AI 对话中自然融入误解提醒

### Story 7.4: 辨析题生成验证

As a 系统,
I want 基于历史误解生成辨析题验证纠正效果,
So that 系统能确认误解已被纠正。

**Acceptance Criteria:**

**Given** 学习者完成复习
**When** 系统生成辨析题
**Then** 题目基于历史误解设计（非随机出题）
**And** 正确回答更新掌握度
**And** 重复错误触发新一轮间隔复习

---

## Epic 8: 学习 Dashboard 与可观测性

学习者可以查看全局 Dashboard（Dataview 三层布局 + 处方性措辞），浏览元认知 2x2 校准矩阵，一键启动考察，查看概念档案。系统可见的操作状态通过摘要行、指示灯和审计日志展示。

**FRs:** FR-VIZ-01~06, FR-OBS-01~04, FR-MAST-05
**NFRs:** NFR-PERF (Dashboard < 1s), NFR-OBS (全部), NFR-A11Y (颜色对比, 处方性颜色)
**Depends on:** Epic 4 (考察历史), Epic 5 (掌握度数据)
**Phase:** 2 · 旅程 6（档案浏览，75% 守恒）

### Story 8.1: 全局 Dashboard Dataview 三层

As a 学习者,
I want 查看全局 Dashboard 了解学习全貌,
So that 我知道哪些需要复习、考察和加强。

**Acceptance Criteria:**

**Given** 学习者打开 wiki/dashboard.md
**When** Dataview 查询执行
**Then** 显示三层布局：Layer 1 原白板卡片（节点数/均掌握度/考察按钮）· Layer 2 考察历史 · Layer 3 分析链
**And** Dashboard 刷新 < 1s（NFR-PERF）

### Story 8.2: 处方性措辞 + 正面措辞

As a 学习者,
I want 学习状态用处方性和正面措辞展示,
So that 我收到可行动的建议而非冷冰冰的数字。

**Acceptance Criteria:**

**Given** Dashboard 展示掌握度状态
**When** 渲染文本
**Then** 使用"🔴 建议优先复习 X"而非"mastery: 0.62"
**And** 使用"建议加强/可以改进"而非"错误/失败/不合格"
**And** 颜色对比 ≥ 4.5:1（NFR-A11Y）

### Story 8.3: 元认知 2x2 校准矩阵

As a 学习者,
I want 查看元认知校准矩阵,
So that 我能发现"以为会了其实不会"的盲区。

**Acceptance Criteria:**

**Given** 学习者有足够的考察数据
**When** 查看校准矩阵
**Then** 显示 2x2 矩阵（会+自信 / 会+不自信 / 不会+自信 / 不会+不自信）
**And** 三阶段渐进：<100 题仅收集 / 100-400 趋势参考 / 400+ 统计可靠（FR-MAST-05）

### Story 8.4: 一键考察 + 概念档案

As a 学习者,
I want 从 Dashboard 一键启动考察并查看概念详情,
So that 学习流程无缝衔接。

**Acceptance Criteria:**

**Given** Dashboard 中的白板卡片
**When** 点击"开始考察"按钮
**Then** 直接启动该主题的检验白板（FR-VIZ-04）

**Given** 学习者选中某概念
**When** 查看详情
**Then** 显示 5 信号 + Tips + 待纠正 + 相关 Edges（FR-VIZ-05）

### Story 8.5: 记忆操作摘要行

As a 学习者,
I want 每次交互后看到记忆操作摘要,
So that 我知道系统在后台做了什么。

**Acceptance Criteria:**

**Given** 对话或考察结束
**When** 系统完成操作
**Then** 展示摘要行：已加载 N 条记忆 · 已保存 M 条记录 · 连接状态
**And** 状态可见，分数隐藏（透明度分层）

### Story 8.6: 连接状态指示 + 写入失败通知

As a 学习者,
I want 实时看到知识图谱连接状态,
So that 我知道系统是否正常工作。

**Acceptance Criteria:**

**Given** 知识图谱服务状态变化
**When** 状态更新
**Then** 指示器显示 🟢 正常 / 🟡 重试 / 🔴 断开
**And** 写入失败时 < 5s 弹出通知

### Story 8.7: 操作审计日志

As a 学习者,
I want 查看操作审计日志,
So that 我可以排查问题。

**Acceptance Criteria:**

**Given** 系统执行记忆操作
**When** 操作完成
**Then** 审计日志记录时间戳 + 类型 + 目标 + 延迟 + 状态
**And** 日志保存在 vault 内可查阅

---

## Epic 9: 多模态增强与持续改进

学习者获得增强的图片考察素材、FSRS 插件升级和校准改进。

**FRs:** FR-MM-03
**NFRs:** NFR-MAINT (Prompt 回归)
**Depends on:** Epic 2 (图片对话), Epic 4 (考察)
**Phase:** 3 · 旅程 5（图片学习，70% 守恒）

### Story 9.1: 图片内容作为考察素材

As a 学习者,
I want 图片内容在考察时作为出题素材,
So that 多模态学习更深入。

**Acceptance Criteria:**

**Given** 笔记中含有图片且图片内容已被识别
**When** 系统生成考察题目
**Then** 图片中提取的概念信息可作为出题素材
**And** 降级：图片不自动持久化到检索索引

### Story 9.2: Phase 3 持续改进

As a 学习者,
I want FSRS 插件升级和校准投票改进,
So that 学习系统越来越精确。

**Acceptance Criteria:**

**Given** Phase 2 完成
**When** 进入 Phase 3
**Then** SM-2 可升级为 FSRS 插件（社区稳定后）
**And** 校准投票 few-shot 样本持续积累改进评分精度

---

## Validation

### FR Coverage Verification

- Total FRs in PRD: 85
- Total FRs mapped in Coverage Map: 85
- Coverage: **100%**
- Unmapped FRs: **0**
- Old FR references (FR1-FR46): **0**

### Dependency Verification

- Forward dependencies (Story N depends on Story N+1): **0**
- Circular dependencies: **0**
- All dependencies are backward-only: **Yes**

### Epic Independence

- Each Epic delivers complete user value: **Yes**
- No Epic requires a later Epic to function: **Yes**
- Epic 1 has no dependencies: **Yes**

### Story Count

| Epic | Stories |
|------|---------|
| 1 | 6 |
| 2 | 8 |
| 3 | 5 |
| 4 | 11 |
| 5 | 8 |
| 6 | 3 |
| 7 | 4 |
| 8 | 7 |
| 9 | 2 |
| **Total** | **54** |
