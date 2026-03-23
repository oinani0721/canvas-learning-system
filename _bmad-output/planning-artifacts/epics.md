---
stepsCompleted:
  - step-01-validate-prerequisites
  - step-02-design-epics
  - step-03-create-stories
  - step-04-final-validation
status: complete
completedAt: '2026-03-17'
previousRun:
  completedAt: '2026-03-17'
  status: adapted
  architectureChange: 'Obsidian Plugin + Svelte → Tauri 2.0 + React + ReactFlow 独立桌面应用'
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/prd-backend-retrieval-pipeline.md
  - _bmad-output/planning-artifacts/architecture.md
  - _bmad-output/planning-artifacts/ux-design-specification.md
---

# Canvas - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for Canvas Learning System, decomposing the requirements from the PRD, Backend Retrieval Pipeline PRD, Architecture, and UX Design Specification into implementable stories.

> **⚠️ 架构适配说明（2026-03-17）**
> 前端技术栈已从 Obsidian Plugin + Svelte 变更为 **Tauri 2.0 + React + ReactFlow** 独立桌面应用。
> - 白板引擎：自建 HTML+SVG → **ReactFlow (@xyflow/react, MIT)**
> - UI 框架：Svelte 5 → **React + shadcn/ui + TailwindCSS**
> - 桌面壳：Obsidian Electron → **Tauri 2.0**
> - 数据存储：IndexedDB (Dexie.js) → **本地 JSON 文件**
> - 对话引擎：不变（spawn Claude Code CLI, Claudian 模式）
> - 后端：不变（FastAPI + Neo4j + LanceDB + Ollama）
> - 所有 Story 的**功能逻辑不变**，仅实现方式按新架构适配。

## Requirements Inventory

### Functional Requirements

#### 主 PRD — 能力域 1：知识图谱管理（7 FR）

- FR-KG-01: 用户可以在白板上创建、编辑、删除知识节点（文本节点和图片节点）
- FR-KG-02: 用户可以通过拖拽创建节点间的有向/无向连线（Edge），并为连线添加语义标签
- FR-KG-03: 用户可以在白板上自由拖拽节点和连线，缩放和平移画布
- FR-KG-04: 系统自动将白板上的节点和连线同步到后端知识图谱存储
- FR-KG-05: 系统可以为用户推荐可能的概念关联（基于知识图谱分析）
- FR-KG-06: 用户粘贴图片到白板时，对话层通过 Agent 原生多模态能力立即可对话讨论图片；检索层后台异步提取文字/公式/概念进入搜索索引
- FR-KG-07: 搜索索引建立过程中显示状态指示（建立中→已完成），对话功能不受索引状态影响

#### 主 PRD — 能力域 2：节点 AI 对话（9 FR）

- FR-CONV-01: 用户点击任意节点可以打开该节点的独立 AI 对话窗口
- FR-CONV-02: 每个节点拥有独立的对话历史，跨 session 持久化
- FR-CONV-03: AI 对话时自动注入用户在该节点和相关节点的学习上下文（Tips、错误记录、Edge 理由等）
- FR-CONV-04: 用户可以在对话中使用 `/命令` 调用已注册的 Agent 技能
- FR-CONV-05: 用户可以在对话窗口中标记 Tips（关键知识点）
- FR-CONV-06: 系统自动从对话中提取、分类并归档用户的错误（4 类：破题错误/推理谬误/知识点缺失/似懂非懂），不同错误类型触发差异化补救策略
- FR-CONV-07: 对话消息按时间进行三层归档（完整保留→摘要+提取→仅提取）
- FR-CONV-08: 用户可以选取对话中的文字拖出为新的知识节点，系统自动建议与原节点的关系
- FR-CONV-09: 用户切换节点时，前一个节点的 AI 回答在后台继续生成（不取消）。节点上显示生成状态指示。同时并发生成上限 3 个，超出排队

#### 主 PRD — 能力域 3：Edge 对话（4 FR）

- FR-EDGE-01: 用户创建连线后，连线上显示可交互的图标提示
- FR-EDGE-02: 用户点击连线图标时，触发 AI 对话，Agent 询问用户为何连接这两个概念
- FR-EDGE-03: Agent 记录用户对连线关系的解释理由，存储为结构化的 Edge 语义标签
- FR-EDGE-04: Edge 对话同时激活 EI + SE 两种学习策略

#### 主 PRD — 能力域 4：检验白板（18 有效 FR，3 已废除/合并）

- FR-EXAM-01: 用户可以基于已有白板生成一个空白的检验白板
- FR-EXAM-02: 检验白板中，AI 基于 FSRS+BKT 选择用户最薄弱的知识节点进行考察
- FR-EXAM-03: AI 利用用户的 Tips、Edge 理由和历史错误精准出题
- FR-EXAM-04: AI 4 维 4 分制评分（概念准确/推理质量/知识覆盖/知识整合），AutoSCORE 两阶段执行
- FR-EXAM-05: 考察过程中用户可从对话中选中文字拖拽到检验白板生成新节点，新节点实时同步回原白板
- FR-EXAM-06: 检验白板支持递归考察——确认的新节点可被继续深入剖析和考察
- FR-EXAM-07: 检验白板继承原白板的所有基础功能
- FR-EXAM-08: 认知负荷控制，持续考察后给出休息提醒
- FR-EXAM-09: （已合并至 FR-EXAM-05）
- FR-EXAM-10: （已废除）
- FR-EXAM-11: 三种考察模式选择：点对点突破/综合题考察/混合模式
- FR-EXAM-12: 原白板内容类型与考察模式自动映射（Constructive Alignment）
- FR-EXAM-13: 按白板类型定制出题策略
- FR-EXAM-14: （已废除）
- FR-EXAM-15: 评分后 Agent 顺带询问"你觉得评分准确吗"（可选）
- FR-EXAM-16: 评分触发时机为 Topic-level（知识节点切换时），对用户隐形，通过节点颜色变化传达
- FR-EXAM-17: 用户可从节点学习档案面板启动单节点考察（第二考察入口）
- FR-EXAM-18: 检验白板中所有数据变更实时同步回原白板
- FR-EXAM-19: 4 级渐进提示（Chain-of-Hints）+ "跳过这题"选项
- FR-EXAM-20: 检验白板完整考察记录永久保存，Dashboard 可查看历史
- FR-EXAM-21: 检验白板不可再生成检验白板

#### 主 PRD — 能力域 5：精通度与学习追踪（6 FR）

- FR-MAST-01: 系统为每个知识节点维护精通度状态（BKT + FSRS）
- FR-MAST-02: 精通度仅通过考察表现更新（非自评直接修改）
- FR-MAST-03: MVP 精通度通过三种方式传达：节点颜色 + 学习档案面板 + FSRS 复习提醒
- FR-MAST-04: FSRS 算法安排复习时机提醒
- FR-MAST-05: Area9 式 2x2 置信度矩阵追踪元认知校准
- FR-MAST-06: 5-6 核心信号融合为单维掌握度

#### 主 PRD — 能力域 6：检索与个性化（13 FR）

- FR-RET-01: 语义+关键词混合检索
- FR-RET-02: AI 对话时自动检索相关上下文
- FR-RET-03: 利用 Graphiti 学习记忆增强回答质量
- FR-RET-04: 智能路由 + 迭代 Retrieve-Verify 循环（最多 2 次）
- FR-RET-05: 六路搜索协作 + 分层 RRF 融合 + 交叉编码器精排
- FR-RET-06: 回源文件验证（Staleness Check + Context Expansion）
- FR-RET-07: 文件指纹增量索引 + 旧索引自动清除
- FR-RET-08: 分块保护代码/公式/表格 + 面包屑路径前缀
- FR-RET-09: 中文检索与英文检索效果相当
- FR-RET-10: 交叉编码器精排 + Adaptive-k 动态返回数量
- FR-RET-11: 质量不达标自动改写重搜 + 安全降级
- FR-RET-12: 上下文压缩 + 掌握度注入 prompt 前端位置
- FR-RET-13: Agent 引用附带可点击 Obsidian 双向链接（章节级精度）

#### 主 PRD — 能力域 7：命令技能系统（5 FR）

- FR-SKILL-01: `/` 弹出已注册技能列表，支持模糊搜索
- FR-SKILL-02: 预装学习辅助技能命令
- FR-SKILL-03: 用户/开发者可通过 prompt 模板注册新技能
- FR-SKILL-04: Agent 执行技能时注入学习历史上下文
- FR-SKILL-05: 技能执行结果可被选中拉出为新节点

#### 主 PRD — 能力域 8：学习档案与痕迹浏览（5 FR）

- FR-TRACE-01: 节点学习档案面板（精通度指示器+学习摘要）
- FR-TRACE-02: Tips 列表，可展开查看来源对话上下文
- FR-TRACE-03: "需要加强方向"展示（正面语言）
- FR-TRACE-04: 关键问答精选（按主题聚类，默认折叠）
- FR-TRACE-05: 对话归档时自动提取并持久化错误/Tips/关键问答

#### 主 PRD — 能力域 9：质量保证与可观测性（7 FR）

- FR-QA-01: LLM 忠实度检查（Faithfulness >= 0.85）
- FR-QA-02: Prompt 模板版本管理+回归测试
- FR-QA-03: 所有 LLM 调用结构化日志
- FR-QA-04: Token 消耗和 LLM 调用成本追踪
- FR-QA-05: Prompt 注入防护 + LLM 输出安全检查
- FR-QA-06: 出题难度与掌握度匹配评估
- FR-QA-07: 结构化提取结果支持人工抽验

#### 主 PRD — 能力域 10：Dashboard（4 FR）

- FR-DASH-01: 浏览所有原白板列表
- FR-DASH-02: 浏览所有检验白板列表
- FR-DASH-03: 从 Dashboard 选白板启动检验白板考察
- FR-DASH-04: 查看任意原白板的历史检验白板列表

#### 主 PRD — 能力域 11：Agent 集成与 MCP（6 FR）

- FR-MCP-01: 后端通过 MCP 协议暴露核心算法能力为标准化工具
- FR-MCP-02: MCP 工具执行采用密码学令牌管道
- FR-MCP-03: 后端审计守护层异步检测管道违规
- FR-AGENT-01: 前端通过 Claude Agent SDK 驱动，Tool-UI Bridge 模式
- FR-AGENT-02: Agent 对话支持 per-node 独立 Session
- FR-AGENT-03: Agent 引擎可替换（不锁定厂商）

#### 主 PRD — 能力域 12：系统配置与运维（7 FR）

- FR-SYS-01: 首次启用安装引导向导
- FR-SYS-02: 配置 LLM 模型供应商和 API Key
- FR-SYS-03: 为不同任务指定不同模型
- FR-SYS-04: 系统健康状态面板
- FR-SYS-05: 一键启动/重启后端服务
- FR-SYS-06: 手动数据备份和恢复
- FR-SYS-07: 多学科知识图谱隔离与切换

#### 后端检索管道 PRD — 能力域 1：笔记索引（8 FR）

- FR-IDX-01: 文件指纹增量索引
- FR-IDX-02: 标题智能分块 512 token + 原子保护
- FR-IDX-03: 面包屑路径前缀 + Frontmatter 元数据前缀
- FR-IDX-04: bge-m3 Dense+Sparse 双向量化
- FR-IDX-05: jieba 中文预分词
- FR-IDX-06: 图片 Gemini OCR → 文本管道索引
- FR-IDX-07: delete-before-insert 去重索引
- FR-IDX-08: 全量重建按钮

#### 后端检索管道 PRD — 能力域 2：笔记检索（8 FR）

- FR-RET-P-01: 6 路并行搜索
- FR-RET-P-02: 按课程/标签过滤
- FR-RET-P-03: 渐进范围扩展搜索
- FR-RET-P-04: Wiki-links 1-hop 邻居扩展
- FR-RET-P-05: 3 组分层 RRF 融合
- FR-RET-P-06: gte-reranker-modernbert-base 精排（Story 2.5 已从 bge-reranker-v2-m3 切换）
- FR-RET-P-07: Adaptive-k 动态返回数量
- FR-RET-P-08: 检索结果附带来源信息

#### 后端检索管道 PRD — 能力域 3：质量保障（5 FR）

- FR-QA-P-01: CRAG 二元评分质量门控
- FR-QA-P-02: 查询自动改写重搜（最多 2 次）
- FR-QA-P-03: 安全降级
- FR-QA-P-04: 上下文压缩到 3K token
- FR-QA-P-05: 掌握度信息注入 prompt 前端

#### 后端检索管道 PRD — 能力域 4：配置与运维（4 FR）

- FR-OPS-01: LangGraph Context API 配置传递
- FR-OPS-02: 搜索管道参数可配置
- FR-OPS-03: 多学科 subject 隔离 + Tag Jaccard 桥接
- FR-OPS-04: Obsidian CLI vault 名配置化

### NonFunctional Requirements

#### 主 PRD NFR

**性能：**
- NFR-PERF-01: 白板操作响应 < 16ms (60fps)
- NFR-PERF-02: 节点 CRUD 同步 < 500ms
- NFR-PERF-03: 对话首 token < 2s
- NFR-PERF-04: RAG 检索 < 3s
- NFR-PERF-05: 图片 OCR < 10s（异步不阻塞）
- NFR-PERF-06: 精通度更新 < 100ms
- NFR-PERF-07: 应用启动 < 1s（Tauri，对比 Electron 1-2s）
- NFR-PERF-08: IPC 单次载荷 < 100KB（Windows IPC 10MB=200ms vs macOS 5ms，GDR-P1-4）

**可靠性：**
- NFR-REL-01: 数据零丢失
- NFR-REL-02: LLM API 断连降级（白板/编辑/FSRS 正常）
- NFR-REL-03: Neo4j 异常降级（不崩溃、写操作暂存）
- NFR-REL-04: 备份可恢复
- NFR-REL-05: 错误不静默

**可观测性：**
- NFR-OBS-01: LLM 调用日志 100% 覆盖
- NFR-OBS-02: 管道健康指标实时可查
- NFR-OBS-03: 错误自动分类聚合
- NFR-OBS-04: Token 消耗按任务统计

**可维护性与可测试性：**
- NFR-MAINT-01: MCP 接口契约测试
- NFR-MAINT-02: Prompt 回归测试
- NFR-MAINT-03: 算法单元测试 100% 覆盖
- NFR-MAINT-04: 评分→精通度→FSRS 端到端集成测试

**安全与隐私：**
- NFR-SEC-01: 所有数据存储本地
- NFR-SEC-02: API Key 安全（不明文显示、不写日志）
- NFR-SEC-03: 仅向配置的 LLM API 发请求
- NFR-SEC-04: 首次配置敏感数据提示
- NFR-SEC-05: 前后端通信走 localhost
- NFR-SEC-06: Prompt 注入防护
- NFR-SEC-07: 6 层 Agent 行为约束防御架构

**兼容性：**
- NFR-COMPAT-01: Tauri 2.10.3+（WebView2 Win10 21H2+ / WKWebView macOS 12+ / webkit2gtk Linux）
- NFR-COMPAT-02: Windows 10 21H2+ / macOS 12+ / Linux Ubuntu 20.04+
- NFR-COMPAT-03: Docker Desktop 4.x / Docker Engine 20.10+
- NFR-COMPAT-04: Python 3.11+（Docker 容器内）
- NFR-COMPAT-05: 适配 Dark/Light 主题（Catppuccin Mocha 默认深色，预留浅色切换）
- NFR-COMPAT-06: React ≥19.2.4 + ReactFlow 12.10.1 + Vite pin 7.x（GDR-P1-1 版本锁定）

#### 后端检索管道 PRD NFR

**性能：**
- NFR-RET-PERF-01: 6 路并行搜索（asyncio.gather）
- NFR-RET-PERF-02: Reranker 延迟 < 200ms（CPU，top-20）
- NFR-RET-PERF-03: 增量索引 < 5s（1-3 文件）
- NFR-RET-PERF-04: 全量重建 < 30s GPU / < 2min CPU（120 文件）

**可靠性：**
- NFR-RET-REL-01: 单搜索通道故障不影响其他通道
- NFR-RET-REL-02: 索引一致性（修改后只有 1 份最新版本）
- NFR-RET-REL-03: 配置失效时日志告警

**兼容性：**
- NFR-RET-COMPAT-01: LangGraph v1.0.10+
- NFR-RET-COMPAT-02: LanceDB v0.4+
- NFR-RET-COMPAT-03: FlagEmbedding >= 1.2（bge-m3）
- NFR-RET-COMPAT-04: jieba >= 0.42
- NFR-RET-COMPAT-05: Obsidian v1.4+（Vault 笔记检索仍需 Obsidian CLI 访问用户 Vault）

### Additional Requirements

#### 来自 Architecture 文档（2026-03-17 更新为 Tauri+React+ReactFlow 新架构）

- **Brownfield 项目**：已有后端代码基础（38 个后端服务文件），前端从 Obsidian+Svelte 全量迁移至 Tauri+React+ReactFlow
- **前端架构**：Tauri 2.0 桌面壳 + React 19 + ReactFlow (@xyflow/react, MIT) 白板引擎 + Zustand 全局状态管理（GDR-P1-2）+ 本地 JSON 文件存储 + Neo4j 异步 delta sync
- **UI 组件库**：shadcn/ui + TailwindCSS v4 + Catppuccin Mocha 深色主题（DE-2）
- **对话引擎**：Claude Agent SDK spawn 官方 Claude Code CLI（用户订阅额度，Claudian/Pencil/Zed ACP 模式验证）+ Tool-UI Bridge 模式（Agent 调用工具时同时更新本地存储 + Zustand Store）
- **LLM 调用层**：LiteLLM SDK 统一调用层，不锁定厂商
- **6 层 Agent 防御架构**：后端算法权威 + 密码学令牌管道 + CLAUDE.md/AGENTS.md + Hooks + 后端审计 + 结构化输出
- **存储层**：Neo4j/Graphiti（方案 C 内嵌 graphiti_core）+ LanceDB + SQLite/aiosqlite
- **对话归档**：Hot-Warm-Cold 三层（0-30 天完整 / 30 天-6 月摘要 / 6 月+ 仅提取）
- **对话上下文**：Tier 1 全量 + Tier 2 摘要 + Tier 3 按需 RAG 检索
- **算法管道**：BKT + FSRS + KG 三角协作 + ACP + Hybrid Search + Agentic RAG
- **评分系统**：AutoSCORE 两阶段（证据提取→逐维打分）+ 自一致性 3 次采样
- **Prompt 5 层结构**：角色定义→考察模式→ACP 数据包→出题规则→评分预设
- **检索管道 4 Phase 渐进实施**：Phase 0 基础修复 → Phase 1 核心升级 → Phase 2 新功能 → Phase 3 前端集成
- **Docker 管理**：Tauri Shell Plugin 管理 Docker Compose 生命周期（DE-4）+ HTTP IPC 备选（GDR-P1-3，缓解 Windows Shell bug）
- **IPC 约束**：单次 IPC 载荷 < 100KB + delta 更新（GDR-P1-4）
- **版本锁定**：ReactFlow 12.10.1 + React ≥19.2.4 + Vite pin 7.x（GDR-P1-1）
- **状态管理三层**：useState（组件局部）/ Zustand（全局共享）/ TanStack Query（服务端缓存）（GDR-P1-2）
- **Obsidian 跳转**：obsidian://adv-uri + Tauri Opener 三级降级（OBS-LINK，待最终确认）
- **8 个 CRITICAL 级 + 7 个 HIGH 级后端代码缺陷**需在实施中修复
- **Shared File 加法编辑**：共享文件（types.ts / stores.ts 等）仅做加法编辑；Schema 变更放在独立 Story 中
- **6 阶段增量算法集成**：Phase 0-5 控制集成风险

#### 来自 UX Design 文档（Pencil UI 范式已换皮为 Tauri+React+ReactFlow 风格）

- **React 组件**，7 组（A 对话 / B 检验白板 / C Dashboard / D 学习档案 / E 白板 / F 系统运维 / G 全局状态）
- **shadcn/ui 组件**：Dialog / Sheet / DropdownMenu / Toast / Command / Tabs 等（替代 Obsidian 原生组件）
- **18 个 Pencil UI 范式**已验证（Tauri+React+ReactFlow+shadcn/ui 风格），覆盖 68/68 前端 UI 场景
- **三阶段组件实施路线图**：Phase 1 核心 → Phase 2 检验白板 → Phase 3 档案+标注+系统
- **布局模式**：左侧白板主区 + 右侧可折叠面板（对话/档案/设置），切换即替换不叠加
- **键盘快捷键**：Enter 发送 / Shift+Enter 换行 / Escape 取消 / `/` 命令 / `@` 引用
- **白板操作**：ReactFlow 标准交互（拖拽/缩放/平移/连线）+ 自定义节点/边渲染
- **CSS 策略**：TailwindCSS v4 + Catppuccin Mocha 主题变量 + CSS Modules 隔离
- **精通度颜色系统**：未学习(默认) / 学习中(蓝) / 薄弱(红橙) / 掌握(绿) / 待复习(黄)
- **设置页面**：独立 Settings 路由页面，shadcn/ui Tabs 分区（替代 Obsidian PluginSettingTab）

### FR Coverage Map

| FR ID | Epic | 简述 |
|-------|------|------|
| FR-SYS-01~07 | Epic 1 | 系统安装引导、模型配置、健康面板、一键启动、数据备份、多学科管理 |
| FR-KG-01~07 | Epic 1 | 节点/连线 CRUD、画布操作、KG 同步、概念推荐、图片节点、索引状态 |
| FR-RET-01~12 | Epic 2 | 混合检索、上下文注入、Graphiti 记忆、智能路由、六路搜索、回源验证、增量索引、分块保护、中文检索、精排、质量降级、上下文压缩 |
| FR-IDX-01~08 | Epic 2 | 文件指纹索引、标题智能分块、面包屑前缀、bge-m3 双向量、jieba 中文、OCR 索引、去重、全量重建 |
| FR-RET-P-01~08 | Epic 2 | 6 路并行、课程过滤、渐进范围、Wiki-links 扩展、分层 RRF、gte-reranker-modernbert-base、Adaptive-k、来源信息 |
| FR-QA-P-01~05 | Epic 2 | CRAG 门控、查询改写、安全降级、上下文压缩、掌握度注入 |
| FR-OPS-01~04 | Epic 2 | Config 传递、参数可配置、多学科隔离、vault 名配置 |
| FR-CONV-01~09 | Epic 3 | 独立对话窗口、跨 session 历史、上下文注入、/命令、Tips 标注、错误归档、三层归档、拉出节点、异步生成 |
| FR-AGENT-01~03 | Epic 3 | Tool-UI Bridge、per-node Session、引擎可替换 |
| FR-MCP-01~03 | Epic 3 | MCP 工具暴露、密码学令牌管道、审计守护层 |
| FR-RET-13 | Epic 3 | 双向链接引用（章节级精度） |
| FR-SKILL-01~05 | Epic 3 | /命令列表+模糊搜索、预装技能、自定义注册、上下文注入、结果可拉出 |
| FR-EDGE-01~04 | Epic 4 | 连线图标提示、Edge 对话触发、理由结构化记录、EI+SE 双重策略 |
| FR-MAST-01~06 | Epic 5 | 精通度状态维护、仅考察更新、三种展示方式、FSRS 复习提醒、Calibration 追踪、多信号融合 |
| FR-TRACE-01~05 | Epic 5 | 学习档案面板、Tips 可追溯、薄弱方向展示、问答精选、自动提取持久化 |
| FR-DASH-01~04 | Epic 5 | 原白板列表、检验白板列表、启动考察、历史检验白板 |
| FR-EXAM-01~08, 11~13, 15~21 | Epic 6 | 检验白板生成、薄弱节点选择、精准出题、4 维评分、拉出节点同步、递归考察、基础功能继承、认知负荷控制、三种模式、自动映射、定制出题、评分校准、Topic-level 评分、单节点考察入口、实时同步、4 级提示、记录保存、不可嵌套 |
| FR-QA-01 | Epic 1+6 | 忠实度检查（E1 建立基础，E6 深化评分忠实度） |
| FR-QA-02 | Epic 2 | Prompt 版本管理+回归测试 |
| FR-QA-03 | Epic 1 | LLM 调用结构化日志（基础设施，E1 建立） |
| FR-QA-04 | Epic 3 | Token 消耗和成本追踪 |
| FR-QA-05 | Epic 3 | Prompt 注入防护+输出安全检查 |
| FR-QA-06 | Epic 2+6 | 出题难度匹配（E2 检索侧，E6 考察侧） |
| FR-QA-07 | Epic 5 | 结构化提取人工抽验 |

**覆盖率：96/96 FR = 100%**
**Epic 数量：6 个（原 E7 QA 分散到各 Epic）**

## Epic List

### Epic 1: 桌面应用搭建与画布基础
用户可以安装并启动 Tauri 桌面应用、通过 Tauri Shell Plugin 启动 Docker 后端服务、在 ReactFlow 画布上创建/编辑/删除知识节点和连线（含图片节点），白板数据同步到后端知识图谱。
**FRs covered:** FR-SYS-01~07, FR-KG-01~07, FR-QA-01(基础), FR-QA-03
**NFRs addressed:** NFR-PERF-01/02/07/08, NFR-COMPAT-01~06, NFR-SEC-01~05, NFR-OBS-01
**注意:** FR-SYS-01（安装引导向导）标记为低优先级，先写文档（用户已确认延后）

### Epic 2: 智能检索管道
系统能从用户的笔记中精确检索到相关片段，支持中英双语语义+关键词混合搜索，搜索结果通过精排和质量门控确保准确可靠。
**FRs covered:** FR-RET-01~12, FR-IDX-01~08, FR-RET-P-01~08, FR-QA-P-01~05, FR-OPS-01~04, FR-QA-02, FR-QA-06(检索侧)
**NFRs addressed:** NFR-PERF-04/05, NFR-RET-PERF-01~04, NFR-RET-REL-01~03, NFR-RET-COMPAT-01~05, NFR-MAINT-02

### Epic 3: 节点 AI 对话与交互
用户点击节点开启独立 AI 对话，Agent 自动注入学习上下文，可标注 Tips、归档错误、使用 /命令调用学习技能、选中文字拖出为新节点，Agent 引用附带可点击的笔记双向链接。

**对话引擎决策（2026-03-16 确认，Mode D 架构）：**
- **方案**：Claude Agent SDK spawn 官方 Claude Code CLI，使用用户已有订阅额度（非 API Key 按量付费）
- **参考实现**：Claudian(YishenTu/claudian) spawn 模式、Pencil "Connected via subscription"、Zed ACP 模式
- **per-node session**：通过 Options.resume(session_id) 管理独立对话，SQLite 存 nodeId→sessionId 映射
- **MCP 注入**：通过 Options.mcpServers 注入后端 FastAPI MCP 工具（query_mastery/generate_question/score_answer 等）
- **上下文注入**：通过 --append-system-prompt 动态注入节点 Tips/错误/Edge 理由
- **认证**：自动继承 ~/.claude/.credentials.json，用户无需配置 API Key
- **Tool-UI Bridge**：Agent 调用工具时同时更新本地存储 + Zustand Store → UI 响应式更新
- **Fallback**：FR-AGENT-03 引擎可替换，政策变化时回退 API Key 方案
- **长期可选**：ACP（Agent Client Protocol）标准化支持多引擎（Claude/Codex/Gemini CLI）

**What-If 边界场景补充 Story（Advanced Elicitation 发现）：**
- Story: "引擎 Fallback 机制"——spawn 失败（Anthropic 政策变化）时自动切换 API Key 模式
- Story: "额度管理"——订阅额度耗尽时提示用户 + 降级策略（等待重置/临时 API Key）
- Story: "Crash Recovery"——Claude Code 进程崩溃自动恢复 + 消息重试（参考 Claudian lastSentMessage 机制）

**FRs covered:** FR-CONV-01~09, FR-AGENT-01~03, FR-MCP-01~03, FR-RET-13, FR-SKILL-01~05, FR-QA-04, FR-QA-05
**NFRs addressed:** NFR-PERF-03, NFR-REL-01/02/05, NFR-SEC-06/07, NFR-OBS-04, NFR-MAINT-01

### Epic 4: Edge 连线对话与关系学习
用户连线后可点击连线图标与 AI 讨论两个概念的关系，触发 EI+SE 双重学习策略，理由被结构化记录为 Edge 语义标签。
**FRs covered:** FR-EDGE-01~04
**回退策略:** 失败退化为静态标签边

### Epic 5: 精通度追踪、学习档案与 Dashboard
用户可以通过节点颜色、学习档案面板和 Dashboard 查看精通度状态、Tips、薄弱方向和 FSRS 待复习列表，感知学习进步。
**FRs covered:** FR-MAST-01~06, FR-TRACE-01~05, FR-DASH-01~04, FR-QA-07
**NFRs addressed:** NFR-PERF-06, NFR-OBS-02/03

### Epic 6: 检验白板与递归考察
用户可以生成检验白板、被 AI 基于 FSRS+BKT 精准考察薄弱环节（三种模式），支持递归发现知识盲区、4 级渐进提示、认知负荷控制、考察记录永久保存。
**FRs covered:** FR-EXAM-01~08, FR-EXAM-11~13, FR-EXAM-15~21, FR-QA-01(深化评分忠实度), FR-QA-06(出题难度匹配)
**NFRs addressed:** NFR-MAINT-03/04
**回退策略:** 失败退化为单轮考察

---

## Epic 1: 系统安装与画布基础

用户可以安装配置系统、在画布上创建/编辑/删除知识节点和连线（含图片节点），白板数据同步到后端知识图谱。

### Story 1.1: 项目脚手架与 Docker 环境搭建

As a 开发者,
I want 搭建 Tauri 2.0 + React + Vite 桌面应用项目结构和 Docker Compose 环境（Neo4j + FastAPI + Ollama），
So that 后续所有 Story 有可运行的基础环境。

**Acceptance Criteria:**

**Given** 开发者克隆项目仓库
**When** 执行 `docker-compose up` 并运行 `npm run tauri dev`
**Then** Neo4j、FastAPI、Ollama 三个容器正常启动，Tauri 桌面窗口打开显示应用界面
**And** 应用能通过 localhost 访问 FastAPI 健康检查端点返回 200
**And** 项目结构包含 `src/`（React 组件）、`src-tauri/`（Rust 壳）、`backend/`（FastAPI）、`docker-compose.yml`
**And** ReactFlow 集成成功，能显示空白画布

### Story 1.2: 安装引导向导（⚠️ 低优先级——用户确认延后，先写文档）

As a 新用户,
I want 首次打开应用时自动弹出引导向导，逐步检测 Docker、后端 API、Neo4j、LLM API、LanceDB 五个组件状态，
So that 我知道系统是否就绪，哪里需要修复。

**Acceptance Criteria:**

**Given** 用户首次打开 Tauri 桌面应用（或系统检测到未完成初始化）
**When** 应用加载完成
**Then** 自动弹出安装引导对话框（shadcn/ui Dialog），显示 5 步检测流程
**And** 每个组件显示绿色（就绪）或红色（未就绪）状态灯
**And** 未就绪的组件提供修复指引或一键操作按钮
**And** 全部就绪后显示"系统已准备好，创建你的第一个白板"引导

### Story 1.3: 模型配置与系统设置面板

As a 用户,
I want 在应用设置页面中配置 LLM 模型供应商和 API Key，并为不同任务（对话、评分、Embedding）指定不同模型，
So that 系统能连接到 AI 服务并按需选择模型。

**Acceptance Criteria:**

**Given** 用户打开 应用设置页面
**When** 用户配置对话模型供应商、API Key 并点击"测试连接"
**Then** 系统验证连接并显示成功/失败状态
**And** 用户可以分别为对话、评分、Embedding 三种任务选择不同模型
**And** API Key 存储在 应用本地配置文件中，不明文显示
**And** 系统健康面板（应用设置页面顶部）常驻显示 5 个组件状态

### Story 1.4: 白板核心——ReactFlow 节点与连线 CRUD + 最小化 Dashboard

As a 用户,
I want 在 ReactFlow 画布上创建文本节点（双击空白处）、编辑节点内容、删除节点（Delete 键）、通过 Handle 拖拽创建连线，自由拖拽节点、缩放和平移画布，并有一个最小化 Dashboard 作为白板入口，
So that 我能构建可视化知识图谱，并能浏览和打开已有白板。

**Acceptance Criteria:**

**Given** 用户打开一个白板视图（ReactFlow 画布）
**When** 用户双击空白处
**Then** 通过 ReactFlow addNodes() 创建自定义 KnowledgeNode，可立即编辑内容
**And** 用户可以拖拽移动节点（ReactFlow 原生支持）
**And** 用户可以从节点 Handle 拖出连线到另一个节点（ReactFlow onConnect）
**And** 用户可以为连线添加语义标签（ReactFlow edge label）
**And** 画布平移和缩放（ReactFlow 原生支持）
**And** 选中节点/连线后按 Delete 删除
**And** 白板操作响应 < 16ms（60fps）
**And** 白板数据保存为本地 JSON 文件（ReactFlow toObject() → fs.writeFile）
**And** 最小化 Dashboard 占位：侧面板列出所有白板 JSON 文件、点击打开对应白板（完整 Dashboard 功能留 Epic 5）

### Story 1.5: 白板数据同步到后端 KG

As a 用户,
I want 白板上的节点和连线自动同步到后端 Neo4j 知识图谱，
So that 后端算法（检索、精通度追踪等）能访问我的知识结构。

**Acceptance Criteria:**

**Given** 用户在白板上创建/修改/删除节点或连线
**When** 操作完成后 500ms-1s 内
**Then** 变更通过 delta sync 异步写入后端 Neo4j
**And** 前端采用乐观更新（操作即时生效，不等后端确认）
**And** 后端不可达时，写操作进入内存队列暂存，恢复后自动重放
**And** 本地 JSON 文件与 Neo4j 后端数据最终一致

### Story 1.6: 图片节点与异步索引状态

As a 用户,
I want 粘贴图片到白板时生成图片节点，后台异步通过 Vision API 提取文字/公式/概念建立搜索索引，并显示索引状态，
So that 我的图片内容将来可以被 AI 搜索到，同时贴图后立刻可以对话。

**Acceptance Criteria:**

**Given** 用户粘贴一张图片到白板
**When** 图片节点出现
**Then** 节点底部显示"🔄 索引建立中..."状态
**And** 后台异步执行 Vision API 提取（不阻塞 UI）
**And** 提取完成后状态变为"✅ 已加入搜索索引"
**And** 图片 OCR 处理 < 10s（单张）
**And** 对话功能不受索引状态影响（对话层通过 Agent 原生多模态能力即时可用）

### Story 1.7: 概念关联推荐

As a 用户,
I want 系统基于知识图谱分析为我推荐可能的概念关联，
So that 我能发现未注意到的知识关系。

**Acceptance Criteria:**

**Given** 白板上有 5 个以上未连线的知识节点
**When** 系统分析节点内容和已有连线模式
**Then** 在 UI 中提示可能的关联建议（如"A 和 B 可能相关"）
**And** 用户可以接受（自动创建连线）或忽略建议
**And** 推荐不强制打扰（非模态，可关闭）

### Story 1.8: 后端服务一键启动与数据管理

As a 用户,
I want 通过应用内系统管理面板一键启动/重启后端服务，并能手动触发数据备份和恢复，
So that 我能方便地管理系统运行和数据安全。

**Acceptance Criteria:**

**Given** 用户点击应用内"系统管理"按钮或使用快捷键
**When** 选择"启动后端"
**Then** 通过 Tauri shell API 执行 docker-compose up 启动所有后端服务
**And** 提供"重启后端""停止后端"按钮
**And** 提供"Canvas: 备份数据"命令，备份 Neo4j + LanceDB + 配置到指定目录
**And** 提供"Canvas: 恢复数据"命令，从备份点完整恢复
**And** 备份/恢复操作有进度提示

### Story 1.9: 多学科知识图谱隔离

As a 用户,
I want 管理多门课程的知识图谱隔离与切换，
So that 不同学科的内容互不干扰。

**Acceptance Criteria:**

**Given** 用户在设置中创建多个学科（如 CS188、线性代数）
**When** 用户切换当前学科
**Then** 白板只显示该学科的节点和连线
**And** 检索只搜索该学科的内容（subject 字段隔离）
**And** 支持跨学科 Tag Jaccard 桥接（可选开启）
**And** 学科切换不丢失任何数据

### Story 1.10: LLM 调用结构化日志基础设施

As a 开发者,
I want 所有 LLM 调用自动记录结构化日志（输入/输出/延迟/token 数/成本），
So that 后续所有 Epic 的 LLM 调用都有完整的可观测性基础。

**Acceptance Criteria:**

**Given** 系统中任何模块调用 LLM（LiteLLM SDK 统一层）
**When** 调用完成（成功或失败）
**Then** 自动记录结构化日志：请求 prompt、模型名称、响应内容、延迟 ms、input/output token 数、估算成本
**And** 日志存储在本地 SQLite 数据库中（非文件日志）
**And** 日志覆盖率 100%（NFR-OBS-01）
**And** 日志不包含敏感信息（API Key 脱敏）

### Story 1.11: LLM 忠实度检查基础框架

As a 系统,
I want 建立 LLM 输出忠实度检查的基础管道，
So that 后续各 Epic 的 AI 回答能被自动校验可靠性。

**Acceptance Criteria:**

**Given** LLM 生成回答且有检索上下文作为参考
**When** 忠实度检查管道执行
**Then** 通过 RAGAS 框架计算 Faithfulness 分数
**And** 低于 0.85 的回答被标记为低信心
**And** 检查结果记录在日志中，不阻塞用户体验
**And** 管道支持开关配置（开发阶段可关闭以节省 token）

---

## Epic 2: 智能检索管道

系统能从用户的笔记中精确检索到相关片段，支持中英双语语义+关键词混合搜索，搜索结果通过精排和质量门控确保准确可靠。按后端 PRD 4 Phase 渐进实施。

### Story 2.1: Phase 0 — 死代码清理与配置修复

As a 开发者,
I want 归档 9 个未使用模块、修复 adapter.py L195 配置传递 bug、删除废弃 env_config.py、清理 cs188 硬编码（20+ 处），
So that 代码库清爽，所有配置参数正确生效，支持多学科。

**Acceptance Criteria:**

**Given** 现有代码库存在 9 个未使用模块和配置传递断裂
**When** 完成清理和修复
**Then** 9 个模块移至 archive/ 目录，不影响 import
**And** adapter.py 配置传递修复后 10/10 参数在管道中生效
**And** env_config.py 删除（-283 行），无残留引用
**And** cs188 硬编码全部替换为配置化 subject 参数
**And** `ruff check` lint 通过，无回退风险

### Story 2.2: Phase 0 — 搜索通道修复与激活

As a 用户,
I want 6 条搜索通道全部返回真实数据，精排和质量检查开始工作，
So that AI 对话能搜到我笔记中的相关内容。

**Acceptance Criteria:**

**Given** 当前仅 2/6 搜索通道工作，Reranker 为空壳，CRAG 100% 误触发
**When** 修复完成
**Then** 6/6 搜索通道（Dense + Sparse + Graphiti + Vault + CLI + 图片）均返回数据
**And** Reranker 接入 bge-reranker（非 return results 空壳）
**And** CRAG 健康触发率 15-30%（非 100% 误触发）
**And** 查询改写接入 LLM（非 f"请详细解释:{query}"）
**And** SearchResult 格式统一，搜索结果不再重复

### Story 2.3: Phase 1 — bge-m3 模型迁移与分块升级

As a 用户,
I want 系统使用 bge-m3 中英双语模型和智能分块策略，
So that 中英文笔记都能被准确检索，代码/公式/表格不会被切断。

**Acceptance Criteria:**

**Given** 当前使用旧 embedding 模型，500 字符硬切分块
**When** 迁移到 bge-m3 + 标题智能分块
**Then** bge-m3 1024d Dense 向量生效
**And** 分块按标题→句子→token 三级策略，上限 512 token
**And** 代码块、数学公式、表格整块保护不切断
**And** 每个分块附带面包屑路径前缀（文档 > 章节 > 小节）
**And** 全量重建索引后搜索质量提升可感知

### Story 2.4: Phase 1 — 中文搜索与混合检索

As a 用户,
I want 中文笔记搜索和英文笔记搜索效果相当，支持按课程/标签过滤，
So that 我的中文学习笔记不再搜不到。

**Acceptance Criteria:**

**Given** 当前 FTS 不支持中文分词，中文搜索不工作
**When** 启用 jieba 预分词 + bge-m3 Sparse + Hybrid Search
**Then** 中文查询能正确匹配中文笔记内容
**And** 混合搜索（语义 + 关键词）同时激活
**And** 支持按 course_id 和 tags 前置过滤搜索范围
**And** 20 个中文查询 A/B 测试验证效果达标

### Story 2.5: Phase 1 — 精排与融合升级

As a 用户,
I want 搜索结果经过精排和智能融合，最相关的内容排在最前面，
So that AI 能用最相关的内容回答我的问题。

**Acceptance Criteria:**

**Given** 6 路搜索结果需要融合排序
**When** 经过分层 RRF + 精排 + Adaptive-k
**Then** 3 组分层 RRF 融合（Dense 组 / Graph 组 / Personal 组，k=60）+ z-score 跨组归一化
**And** bge-reranker-v2-m3 fp16 精排，延迟 < 200ms（CPU，top-20）
**And** Adaptive-k 分数断崖自动截取（简单问题少返回、复杂问题多返回）
**And** 精排后 MRR 提升 >= +0.10

### Story 2.6: Phase 1 — CRAG 质量门控与安全降级

As a 用户,
I want 搜索质量不好时系统自动改写查询重搜，而不是用错误内容回答，
So that AI 不会因为搜索质量差而产生幻觉。

**Acceptance Criteria:**

**Given** 精排后的结果可能不相关
**When** CRAG 二元评分判定"不相关"
**Then** 自动改写查询并重新搜索（最多 2 次重试）
**And** 全部不相关时安全降级：告知"信息不足"而非生成幻觉
**And** 智能路由根据查询意图选择最优检索策略（L1）
**And** 迭代 Retrieve-Verify 循环可追踪（日志记录每次重试）

### Story 2.7: Phase 1 — 文件指纹增量索引

As a 用户,
I want 修改笔记后只重新索引改动的文件，且同一文件只有一份最新索引，
So that 索引快速且不会出现重复搜索结果。

**Acceptance Criteria:**

**Given** 用户修改了 vault 中的 3 个 markdown 文件
**When** 索引管道触发
**Then** 通过文件指纹（content_hash）只处理 3 个变化的文件
**And** 使用 delete-before-insert 模式清除旧索引再写入新索引
**And** 增量索引延迟 < 5s（1-3 文件）
**And** 修改 N 次后仍只有 1 份索引数据
**And** 提供全量重建按钮用于模型迁移或异常恢复

### Story 2.8: Phase 2 — 元数据过滤与邻居扩展

As a 用户,
I want 搜索能按课程/标签过滤范围，并自动扩展到相关链接的笔记，
So that 搜索结果更精准且不遗漏关联内容。

**Acceptance Criteria:**

**Given** 用户的笔记有 Frontmatter（course/tags）和 Wiki-links
**When** 执行搜索
**Then** 支持渐进范围搜索：同课程 → 相关课程 → 全库（4 阶段级联）
**And** Wiki-links 邻居自动扩展（搜到的笔记的 1-hop 链接笔记也纳入结果）
**And** 跨课程 Tag Jaccard 桥接可选启用
**And** Frontmatter 元数据正确解析为 LanceDB 列

### Story 2.9: Phase 2 — 图片检索管道

As a 用户,
I want 粘贴的图片中的文字/公式/概念可以被搜索到，
So that 截图的课件内容也能在 AI 对话中被引用。

**Acceptance Criteria:**

**Given** 用户粘贴了包含公式的课件截图
**When** 后台 OCR 提取完成后执行搜索
**Then** 图片中提取的文字/分类/摘要/概念走文本索引管道
**And** 向量维度统一为 1024（修复之前 384/768/1024 冲突）
**And** 检索结果附带来源信息：文件路径 + heading 路径 + 起止行号
**And** 图片内容在搜索结果中标注来源为"图片 OCR"

### Story 2.10: Phase 2 — 上下文压缩与掌握度注入

As a 用户,
I want AI 对话时自动检索相关上下文并精炼注入，Agent 知道我的掌握水平，
So that AI 回答既精准又不浪费 token，难度适配我的水平。

**Acceptance Criteria:**

**Given** 检索返回 15K token 的候选上下文
**When** 上下文压缩管道处理
**Then** 压缩到 3K token（句子级提取，公式/代码整块保护）
**And** 用户掌握度信息注入 prompt 最前端位置（Lost in Middle 缓解）
**And** Graphiti 学习记忆（错误/Tips/关键问答）增强回答质量
**And** 回源验证：content_hash 比对 + 完整段落上下文扩展

### Story 2.11: Phase 2 — 搜索管道参数可配置化

As a 开发者,
I want 搜索管道的融合权重、质量阈值、reranker 策略等参数通过配置文件调整，
So that 可以在真实数据上调优而无需改代码。

**Acceptance Criteria:**

**Given** 搜索管道有多个可调参数
**When** 修改配置文件中的参数值
**Then** 下次搜索自动使用新参数，无需重启
**And** 配置项包括：RRF k 值、融合权重、CRAG 阈值、reranker 策略、Adaptive-k buffer
**And** 配置失效时日志告警，不静默回退默认值

### Story 2.12: 全量重建索引与验收测试

As a 开发者,
I want 用 50+ 真实查询的 Golden Test Set 验收检索管道质量，
So that 确认管道升级后达到生产标准。

**Acceptance Criteria:**

**Given** 完成 Phase 0-2 全部升级
**When** 执行全量重建索引 + Golden Test Set 验收
**Then** 全量重建 < 30s GPU / < 2min CPU（120 文件）
**And** MRR@10 >= 0.70
**And** Precision@5 >= 0.70
**And** Recall@10 >= 0.80
**And** 中文查询效果与英文查询相当
**And** Reranker 延迟 < 200ms（CPU，top-20）
**And** CRAG 健康触发率 15-30%

### Story 2.13: Prompt 版本管理与回归测试

As a 开发者,
I want Prompt 模板有版本管理，变更后自动触发回归测试，
So that Prompt 修改不会意外降低 AI 质量。

**Acceptance Criteria:**

**Given** 开发者修改了 Prompt 模板（检索相关：查询改写、CRAG 判定等）
**When** 模板变更被提交
**Then** 自动触发标准测试集回归测试
**And** 测试结果对比变更前后的质量指标（MRR、Precision、CRAG 触发率）
**And** Prompt 模板存储在版本化目录中，支持回滚

---

## Epic 3: 节点 AI 对话与交互

用户点击节点开启独立 AI 对话，Agent 自动注入学习上下文，可标注 Tips、归档错误、使用 /命令调用学习技能、选中文字拖出为新节点，Agent 引用附带可点击笔记链接。对话引擎：Claude Agent SDK spawn 官方 Claude Code CLI（用户订阅额度）。

### Story 3.1: Claude Code CLI 集成与 per-node Session

As a 用户,
I want 点击白板节点时自动启动 Claude Code 对话，每个节点有独立的对话历史，切换节点时对话无缝恢复，
So that 每个知识点都有专属的 AI 助手记住我们的对话。

**Acceptance Criteria:**

**Given** 用户点击白板上的节点 A
**When** 右侧面板打开对话窗口
**Then** Claude Agent SDK spawn 官方 Claude Code CLI 子进程
**And** 自动继承用户已登录的 Claude Code 订阅认证（~/.claude/.credentials.json）
**And** 使用 Options.resume(sessionId) 恢复该节点的历史对话
**And** SQLite 存储 nodeId → sessionId 映射
**And** 切换到节点 B 时，resume 节点 B 的 session，节点 A 对话完整保留
**And** 引擎可替换（FR-AGENT-03）：接口层解耦，支持未来切换到 API Key 或 ACP

### Story 3.2: MCP 工具暴露——后端算法接口

As a AI Agent,
I want 通过 MCP 协议调用后端算法工具（query_mastery/generate_question/score_answer/search_memories/update_fsrs 等），
So that 对话能利用后端的精通度追踪、出题、评分等算法能力。

**Acceptance Criteria:**

**Given** FastAPI 后端运行中
**When** Claude Code 子进程通过 Options.mcpServers 连接后端 MCP
**Then** 10+ 个标准化 MCP 工具可用（FastAPI-MCP ASGI 直连）
**And** 密码学令牌管道生效（每步产 token，跳步拒绝）
**And** 后端审计守护层异步检测管道违规
**And** MCP 配置通过 --mcp-config 动态注入（不依赖 .claude/ 目录）

### Story 3.3: 对话面板 UI（ChatPanel + 流式输出）

As a 用户,
I want 在右侧面板看到美观的对话界面，消息流式显示，支持 Markdown 渲染和代码高亮，
So that 对话体验流畅自然。

**Acceptance Criteria:**

**Given** 用户在对话框输入消息并发送
**When** Claude Code 返回流式响应
**Then** React ChatPanel 组件实时渲染流式文本（NDJSON 解析 → React state 更新）
**And** 用户消息右对齐深色气泡，Agent 消息左对齐浅色气泡
**And** Agent 回复支持 Markdown 渲染（react-markdown 渲染）
**And** 对话历史跨 session 持久化（后端 SQLite + aiosqlite）
**And** 对话首 token < 2s
**And** Agent 回复支持 Markdown 渲染（react-markdown + rehype-highlight）

### Story 3.4: 学习上下文自动注入

As a 用户,
I want Agent 对话时自动知道我在这个节点写过的 Tips、犯过的错、连线的理由，
So that Agent 的回答基于我的学习历史，而不是从零开始。

**Acceptance Criteria:**

**Given** 用户打开一个有学习历史的节点对话
**When** Agent 生成回复
**Then** 通过 --append-system-prompt 动态注入该节点的 Tips/错误/Edge 理由
**And** 上下文三层管理：Tier1 当前节点全量 / Tier2 相邻节点摘要 / Tier3 远端 RAG 按需
**And** Agent 引用笔记时附带可点击链接（章节级精度 `[[文件名#章节标题]]`），点击通过 obsidian://adv-uri 跳转到 Obsidian 对应位置（OBS-LINK 三级降级：adv-uri→内置URI→文件级）
**And** 前端通过 react-markdown 渲染 + Tauri Opener 事件 hook 实现跳转

### Story 3.5: /命令技能集成

As a 用户,
I want 在对话框输入 `/` 时看到可用的学习技能列表（基础拆解、深度拆解等 11 个），选择后 Claude Code 原生执行，
So that 我能在对话中快速调用专业学习工具。

**Acceptance Criteria:**

**Given** 用户在对话框输入 `/`
**When** 应用读取 .claude/commands/ 目录的技能文件列表
**Then** 弹出技能列表 UI，支持模糊搜索
**And** 用户选择技能后，透传 `/skill-name 参数` 给 Claude Code 原生处理
**And** Claude Code 加载 .claude/commands/skill.md → 读取 .claude/agents/agent.md → 执行
**And** 11 个预装技能开箱可用（拆解/解释/对比/记忆/练习/检验）
**And** 用户可在 .claude/commands/ 添加新 .md 文件自定义技能
**And** 技能执行结果显示在对话中，可被选中拉出为白板节点
**And** 技能执行时注入用户学习历史上下文（个性化）

### Story 3.6: Tips 标注与错误归档

As a 用户,
I want 选中对话文字后标记为 Tips 或让系统自动归档我的错误，
So that 我的关键知识点和薄弱环节被持久化记录，Agent 将来能精准引用。

**Acceptance Criteria:**

**Given** 用户选中对话中的一段文字
**When** 浮动操作面板出现
**Then** 可选"打 Tag"标注分类 + "写 Tips"添加关键笔记
**And** Tips 保存到 Graphiti（三通道写入之 Agent 自报告通道）
**And** 系统自动从对话中提取、分类错误（4 类：破题错误/推理谬误/知识点缺失/似懂非懂）
**And** 不同错误类型触发差异化补救策略映射
**And** 浮动面板不遮挡选中文字，跟随选中位置

### Story 3.7: 对话拉出节点

As a 用户,
I want 选中对话中的精彩解释拖到白板上生成新知识节点，
So that 对话中的见解能成为知识图谱的一部分。

**Acceptance Criteria:**

**Given** 用户选中对话中的文字
**When** 拖拽到白板区域
**Then** 生成新的文本节点，内容为选中文字
**And** 系统自动建议与原节点的关系（LLM 推荐关系类型）
**And** 新节点自动同步到后端 Neo4j
**And** 操作与白板原生创建节点体验一致

### Story 3.8: 对话归档与异步生成管理

As a 用户,
I want 对话历史自动归档管理，切换节点时后台 AI 继续生成不中断，
So that 我的对话数据安全且不错过任何 AI 回答。

**Acceptance Criteria:**

**Given** 对话积累到一定量级
**When** 对话归档管道触发（时间 + 容量 50K tokens 双触发）
**Then** Hot（0-30天）完整保留 → Warm（30天-6月）摘要+提取 → Cold（6月+）仅提取
**And** 结构化提取（错误/Tips/关键问答）永久保存到 Graphiti
**And** 用户切换节点时，前一个节点的 AI 回答在后台继续生成（不取消）
**And** 节点显示生成状态指示（生成中/完成未读/空闲）
**And** 同时并发生成上限 3 个，超出排队

### Story 3.9: 引擎 Fallback 机制

As a 用户,
I want 当 Claude Code spawn 失败时系统自动切换到 API Key 模式，
So that 即使订阅认证不可用，我的对话功能不中断。

**Acceptance Criteria:**

**Given** spawn Claude Code CLI 返回 exit code 2（认证错误）或 ENOENT
**When** 插件检测到 spawn 失败
**Then** 弹出通知"订阅认证不可用，切换到 API Key 模式"
**And** 自动切换到 Claude Agent SDK 直接 API 调用模式
**And** 用户在 设置页面 可配置备用 API Key
**And** 对话历史和 session 数据不丢失

### Story 3.10: 额度管理与降级

As a 用户,
I want 订阅额度用完时清楚知道发生了什么，并有应对方案，
So that 我不会困惑于为什么 AI 突然不回复了。

**Acceptance Criteria:**

**Given** Claude Code 返回 429 Rate Limit 错误
**When** 插件解析 stderr 错误信息
**Then** 对话面板显示"本周订阅额度已用完，下周重置"
**And** 提供两个选项：等待重置（显示倒计时）/ 临时切换 API Key
**And** 白板浏览/编辑/FSRS 提醒等非 AI 功能正常使用

### Story 3.11: Crash Recovery

As a 用户,
I want Claude Code 进程崩溃时自动恢复，不丢失我正在进行的对话，
So that 系统稳定可靠。

**Acceptance Criteria:**

**Given** Claude Code 子进程异常退出（exit code ≠ 0）
**When** 插件检测到进程退出
**Then** 检查 lastSentMessage 是否有未处理的消息
**And** 自动重启 Claude Code 进程
**And** 通过 --resume 恢复 session（对话历史完整）
**And** 重新发送 lastSentMessage（限一次重试）
**And** 连续 crash 3 次 → 通知用户"AI 暂时不可用"并停止重试

### Story 3.12: Token 消耗追踪与成本统计

As a 用户,
I want 查看 AI 使用统计——按任务分类的 Token 消耗和估算成本，
So that 我能了解系统的使用情况和成本分布。

**Acceptance Criteria:**

**Given** Story 1.10 的日志基础设施已就位
**When** 用户在应用设置或 Dashboard 中查看使用统计
**Then** 按任务类型（对话/评分/检索/提取/索引）分类统计 Token 消耗
**And** 显示估算成本（基于各模型定价）
**And** 支持按时间范围筛选（今天/本周/本月/全部）

### Story 3.13: Prompt 注入防护与输出安全检查

As a 系统,
I want 对话输入有 Prompt 注入检测，LLM 输出有安全检查，
So that 恶意输入不能操纵 AI 行为，AI 输出不包含有害内容。

**Acceptance Criteria:**

**Given** 用户在对话中输入内容
**When** 内容发送给 LLM 之前
**Then** system prompt 和 user message 严格隔离（不在 user 层面注入 system 指令）
**And** LLM 输出经过安全检查（检测是否泄漏 system prompt、是否包含不当内容）
**And** 检测到异常时记录日志 + 返回安全降级回答
**And** 6 层 Agent 防御架构中的 Layer 0（后端算法权威）和 Layer 5（结构化输出）在此 Story 实现

---

## Epic 4: Edge 连线对话与关系学习

用户连线后可点击连线图标与 AI 讨论两个概念的关系，触发 EI+SE 双重学习策略，理由被结构化记录为 Edge 语义标签。Layer 3 创新，回退策略：退化为静态标签边。

### Story 4.1: Edge 可交互图标与对话触发

As a 用户,
I want 创建连线后看到连线上的可交互图标，点击后右侧面板切换为 Edge 对话，
So that 我能方便地讨论两个概念之间的关系。

**Acceptance Criteria:**

**Given** 用户拖拽创建两个节点之间的连线
**When** 连线创建完成
**Then** 连线上出现可交互的小图标（ReactFlow 自定义 Edge 组件上的可交互图标）
**And** 首次连线时显示引导提示"点击讨论关系"
**And** 点击图标后，右侧面板从节点对话切换为 Edge 对话模式

### Story 4.2: Edge 对话——Agent 追问与理由记录

As a 用户,
I want Agent 问我"为什么把这两个概念连在一起"，我回答后理由被结构化记录，
So that 系统记住我对概念关系的理解，将来能在对话和考察中引用。

**Acceptance Criteria:**

**Given** 用户点击 Edge 图标进入 Edge 对话
**When** 对话开始
**Then** Agent 自动注入两端节点上下文 + 预设 prompt，主动询问连线理由
**And** 用户回答后，Agent 记录理由为结构化 Edge 语义标签（KG-triplet 格式）
**And** 理由双写：Graphiti 结构化 + LanceDB 向量化（供检索和出题消费）

### Story 4.3: EI+SE 双重学习策略激活

As a 用户,
I want Edge 对话同时触发精细化追问和自我解释两种学习策略，
So that 一次连线交互能最大化学习效果。

**Acceptance Criteria:**

**Given** Edge 对话进行中
**When** Agent 追问和用户回答交互
**Then** 同时激活 Elaborative Interrogation（精细化追问）+ Self-Explanation（自我解释）
**And** Active Recall 不在此场景激活（连线时两端概念可见，不构成回忆检索）
**And** 策略激活对用户透明，体感为"自然对话"而非"做练习"

### Story 4.4: Edge 对话回退策略

As a 开发者,
I want Edge 对话功能失败时优雅退化为静态标签边，
So that 系统不会因为 Layer 3 创新失败而崩溃。

**Acceptance Criteria:**

**Given** Edge 对话功能出现异常（Agent 不可用/MCP 断连）
**When** 用户点击 Edge 图标
**Then** 退化为静态标签编辑（用户手动输入关系标签）
**And** 显示提示"AI 对话暂时不可用，已切换为手动标签模式"
**And** 之前记录的 Edge 理由不丢失

---

## Epic 5: 精通度追踪、学习档案与 Dashboard

用户可以通过节点颜色、学习档案面板和 Dashboard 查看精通度状态、Tips、薄弱方向和 FSRS 待复习列表，感知学习进步。

### Story 5.1: BKT+FSRS 双引擎精通度系统

As a 系统,
I want 为每个知识节点维护精通度状态（BKT 管掌握概率 + FSRS 管复习调度），
So that 系统能准确追踪用户的学习进度。

**Acceptance Criteria:**

**Given** 用户在检验白板中被考察某个知识节点
**When** AutoSCORE 评分完成
**Then** BKT 贝叶斯更新该节点的掌握概率
**And** FSRS 更新记忆稳定性和下次复习时间
**And** effective_proficiency = min(p_mastery, R)
**And** 精通度仅通过考察表现更新（非自评直接修改）
**And** 精通度计算 < 100ms（O(1) 复杂度）
**And** 初始使用默认先验值（不依赖 E6 考察数据），随考察数据积累逐步精确

### Story 5.2: 节点颜色精通度可视化

As a 用户,
I want 白板上的节点颜色反映掌握程度，一眼看出哪些学得好哪些薄弱，
So that 我对学习全貌有直觉感知。

**Acceptance Criteria:**

**Given** 节点有精通度数据
**When** 白板渲染
**Then** 节点颜色按精通度映射：未学习(默认) / 学习中(蓝) / 薄弱(红橙) / 掌握(绿) / 待复习(黄)
**And** 颜色变化在精通度更新后即时反映（ReactFlow 自定义节点的颜色指示器）
**And** 适配 Obsidian Light/Dark 主题

### Story 5.3: 学习档案面板

As a 用户,
I want 点击节点时查看该节点的学习档案——掌握度、Tips、薄弱方向、关键问答，
So that 我能回顾和追踪每个知识点的学习历程。

**Acceptance Criteria:**

**Given** 用户点击节点并切换到学习档案视图
**When** 面板加载
**Then** 顶部显示聚合精通度指示器 + 学习摘要
**And** L2 展示用户标注的所有 Tips，可展开查看来源对话上下文
**And** L2 展示"需要加强方向"（正面语言，聚合误解模式）
**And** L3 展示关键问答精选（按主题聚类，默认折叠按需展开）
**And** 下方显示 FSRS 下次复习日期
**And** 提供"开始考察"按钮（单节点考察入口，FR-EXAM-17）

### Story 5.4: FSRS 复习提醒与 Dashboard

As a 用户,
I want 在 Dashboard 中浏览所有白板、查看待复习节点列表，一键启动考察，
So that 每天打开就知道该复习什么。

**Acceptance Criteria:**

**Given** 用户打开 Dashboard（Dashboard 页面）
**When** Dashboard 加载
**Then** 显示所有原白板列表，点击可打开对应白板
**And** 显示所有检验白板列表，展示考察状态和历史
**And** 显示 FSRS 待复习节点列表（按紧急程度排序）
**And** 可从 Dashboard 选择原白板并启动检验白板考察（选模式→开始）
**And** 可查看任意原白板的历史检验白板列表（时间、掌握度变化、考察节点数）

### Story 5.5: Calibration 校准追踪

As a 用户,
I want 系统追踪我的元认知校准——识别"以为会了其实不会"的危险盲区，
So that 我能发现自己的认知偏差。

**Acceptance Criteria:**

**Given** 用户在检验白板中被考察
**When** 评分完成后
**Then** Area9 式 2x2 置信度矩阵记录（自评 vs 实际表现）
**And** 四种状态分类：确定且正确(掌握) / 确定但错误(误解,最危险) / 不确定但正确(运气) / 不确定且错误(未学)
**And** 三阶段渐进：<10 条仅收集 / 10-20 初步趋势 / 20+ 可靠评估

### Story 5.6: 多信号融合

As a 系统,
I want 将 5-6 核心信号（BKT+FSRS+考察评分+校准偏差+自信度自评）融合为单维掌握度，
So that 精通度评估更全面准确。

**Acceptance Criteria:**

**Given** 多个信号源产生数据
**When** 融合算法执行
**Then** 输出单维掌握度分数
**And** 信号互补性验收：任意两个信号相关系数 < 0.7
**And** N 信号动态接入架构（支持后续新增信号）
**And** 多维精通度为远期研究目标（Phase 3+），当前不实现

### Story 5.7: EventBus 三系统联通

As a 系统,
I want FSRS、Graphiti、RAG 三个子系统通过 EventBus 联通，精通度更新时触发检索权重调整和记忆更新，
So that 学习数据能在系统间自动流动，形成闭环。

**Acceptance Criteria:**

**Given** 用户在检验白板中被考察，精通度更新
**When** BKT/FSRS 更新事件发出
**Then** EventBus 将事件路由到 Graphiti（更新学习记忆）和 RAG（调整检索权重）
**And** 三层优先级队列：P0 精通度更新 / P1 记忆写入 / P2 索引调整
**And** CircuitBreaker 降级：单系统故障不阻塞其他系统
**And** 事件可追踪（日志记录每个事件的来源、目标、处理结果）

### Story 5.8: 结构化提取人工抽验

As a 用户,
I want 系统从对话中自动提取的错误/Tips/关键问答支持人工抽验，
So that 我能确认 AI 的提取结果是否准确，发现错误提取后可修正。

**Acceptance Criteria:**

**Given** 对话归档后 AI 自动提取了错误/Tips/关键问答
**When** 用户在学习档案面板中查看提取结果
**Then** 每条提取内容旁有"查看来源"按钮，跳转到原始对话上下文
**And** 用户可标记"提取正确"或"提取错误"
**And** 错误标记累积，管道健康指标显示提取准确率
**And** 用户可手动修改/删除错误提取

---

## Epic 6: 检验白板与递归考察

用户可以生成检验白板、被 AI 基于 FSRS+BKT 精准考察薄弱环节（三种模式），支持递归发现知识盲区、4 级渐进提示、认知负荷控制。Layer 3 创新，回退策略：退化为单轮考察。

### Story 6.1: 检验白板生成与基础框架

As a 用户,
I want 从 Dashboard 选择原白板生成一个空白的检验白板，继承原白板所有基础功能，
So that 我能在独立空间中被系统考察。

**Acceptance Criteria:**

**Given** 用户在 Dashboard 选择原白板并点击"生成检验白板"
**When** 系统创建检验白板
**Then** 生成空白的检验白板，继承原白板所有基础功能（节点对话/Edge 对话/拖拽连线等）
**And** 同一原白板可生成不限数量的检验白板
**And** 检验白板不可再生成检验白板（防嵌套）

### Story 6.2: 考察模式选择与智能推荐

As a 用户,
I want 选择考察模式（点对点/综合题/混合），系统根据白板内容类型智能推荐，
So that 考察方式匹配我的学习内容。

**Acceptance Criteria:**

**Given** 用户启动检验白板考察
**When** ExamModeSelector 对话框（shadcn/ui Dialog）弹出
**Then** 显示三种模式：点对点突破 / 综合题考察 / 混合模式
**And** 系统根据白板内容类型自动推荐（知识点→点对点，题目→综合题）
**And** 用户可手动覆盖推荐

### Story 6.3: AI 精准出题（ACP 数据包）

As a AI Agent,
I want 基于 FSRS+BKT 选择用户最薄弱节点，利用 Tips/Edge 理由/错误历史精准出题，
So that 考察精准命中知识盲区。

**Acceptance Criteria:**

**Given** 检验白板考察开始
**When** Agent 选题和出题
**Then** FSRS+BKT+KG 三角协作选择最薄弱知识节点
**And** ACP 考察数据包注入 Prompt 第 3 层（Tips/错误/Edge 理由/精通度/对话历史）
**And** Prompt 5 层结构完整（角色→模式→ACP→规则→评分预设）
**And** 点对点按白板类型定制：知识点侧重定义+解释+辨析，题目侧重易错点+破题方法

### Story 6.4: AutoSCORE 隐形评分

As a 系统,
I want 在 Agent 切换考察节点时后台自动评分，评分对用户隐形，通过节点颜色变化传达，
So that 考察流程不被评分打断。

**Acceptance Criteria:**

**Given** Agent 考完当前节点，切换到下一个节点
**When** Topic-level 评分触发
**Then** 后台执行 AutoSCORE 两阶段：Stage1 证据提取 → Stage2 4维4分制 Rubric 逐维打分
**And** 3 次采样多数投票，分差>1 标记 AI 低信心
**And** AI 不确定时邀请用户复核
**And** BKT/FSRS 更新 → 节点颜色变化（Stealth Assessment）
**And** Agent 话题切换时顺带询问"评分准确吗"（可选不强制）

### Story 6.5: 递归考察与新节点同步

As a 用户,
I want 考察中发现新盲区时拉出新节点，新节点可继续被考察，发现的内容实时同步回原白板，
So that 知识盲区不断被发掘并补充到知识图谱中。

**Acceptance Criteria:**

**Given** 用户在检验白板对话中发现新盲区
**When** 选中文字拖到白板生成新节点
**Then** 新节点和数据实时同步回原白板
**And** 确认的新节点可点击继续深入剖析和考察（递归）
**And** 用户驱动终止——"不点"= 自然结束

### Story 6.6: 4 级渐进提示与跳过

As a 用户,
I want 答不出来时可以请求提示（从模糊到具体），也可以跳过这题，
So that 考察不会让我卡住。

**Acceptance Criteria:**

**Given** 用户在考察中答不出来
**When** 点击"给我提示"按钮
**Then** 4 级渐进提示：Level1 方向提示 → Level2 关键词 → Level3 部分框架 → Level4 分步脚手架
**And** 每次点击升一级，不提供"直接告诉答案"选项
**And** 用户也可选"跳过这题"（标记未作答，不惩罚 BKT）

### Story 6.7: 认知负荷控制与休息提醒

As a 用户,
I want 持续考察一段时间后系统提醒我休息，
So that 不会过度考察导致疲劳。

**Acceptance Criteria:**

**Given** 用户持续考察达到时间阈值
**When** 15/25/35/45 分钟递进触发
**Then** 对话内显示休息提醒消息
**And** 用户可选"继续"或"休息"
**And** 选择"休息"时正常结束考察，记录保存

### Story 6.8: 考察记录永久保存

As a 用户,
I want 每次检验白板的完整考察记录永久保存，可在 Dashboard 查看历史，
So that 我能回顾过去的考察表现和进步轨迹。

**Acceptance Criteria:**

**Given** 考察结束（用户休息或自然结束）
**When** 考察记录保存
**Then** 完整记录：考察对话、评分历史、精通度变化、新发现节点
**And** Dashboard 可查看所有历史检验白板
**And** 点击可打开查看完整考察记录

### Story 6.9: 评分忠实度深化检查

As a 系统,
I want 在检验白板评分场景中深化忠实度检查——确保 AutoSCORE 评分基于学生实际回答而非幻觉，
So that 评分可靠，精通度更新准确。

**Acceptance Criteria:**

**Given** AutoSCORE 两阶段评分完成（证据提取→逐维打分）
**When** 忠实度校验管道执行
**Then** 检查 Stage 1 提取的证据是否能在学生原文中找到对应
**And** 检查 Stage 2 各维度打分是否与证据一致（Faithfulness >= 0.85）
**And** 3 次采样结果分差 > 1 的维度标记为"AI 低信心"
**And** 低信心评分不更新精通度（等待下次考察）

### Story 6.10: 出题难度匹配评估

As a 系统,
I want 评估出题难度与用户掌握度的匹配程度，
So that 考察不会过难也不会过简单。

**Acceptance Criteria:**

**Given** 考察过程中 AI 出题
**When** 出题完成并评分后
**Then** 系统计算出题难度匹配率（题目难度 vs 用户 BKT p_mastery）
**And** 出题难度匹配率 >= 70%
**And** 匹配率过低时触发出题策略自动调整
**And** 管道健康指标实时可查（错误自动分类聚合）
