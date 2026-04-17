---
story_id: "1.1"
epic_id: "1"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P0"
estimate_hours: 8
depends_on: []
blocks: ["1.2", "1.3", "1.4", "1.6"]
trace:
  - "FR-SYS-01"
  - "FR-SYS-06"
---

# Story 1.1: Vault 初始化 + Templater 模板

Status: ready-for-dev

## Story

As a 学习者,
I want vault 初始化和 Templater 模板自动就绪,
So that 我新建概念/考察文件时自动获得标准 frontmatter 结构（含 relationships[] 关系字段），首次使用有安装引导帮我检测依赖。

## 通俗化解释（给学习者）

> **一句话说**: 第一次打开应用时，帮你把学习笔记的"骨架"搭好，让你专心学 CS 61B 而不是折腾工具。

**你会遇到的场景**:
- 你想开始复习 LLRB 树，打开应用却发现要手动建文件夹、配置笔记格式、装一堆插件，一小时还没开始学
- 你新建一个"异步编程"笔记，每次都要手动敲一遍"掌握度 / 易错点 / 小技巧"这些固定字段，抄到第三个就烦了
- 你想知道两个概念之间的关系（比如"链表是树的前置"），但不知道在哪里记录才不会丢

**这个功能帮你**:
- 打开应用就自带整齐的文件夹 + 笔记模板，直接开始填内容
- 新建概念笔记时，"掌握度、下次复习时间、相关概念"这些字段自动出现，你只要填标题和内容
- 应用启动时自动检查"后端服务、AI 模型、数据库"是否就绪 ，坏了直接告诉你怎么修

**用个比喻**: 就像你刚搬进一套精装修公寓 —— 水电燃气已经接通，书架已经摆好，厨房刀具齐全，你只要把行李箱里的书和衣服放进去就能住。而不是交了钥匙进门发现空房一间，还得自己跑建材市场。

**你能看到/操作到什么**:
- 第一次打开应用，弹出一个"正在为你搭建学习空间"的引导，绿色勾勾逐个亮起 
- 在 Obsidian 里点"新建概念笔记"，弹出的笔记已经帮你填好所有字段框，光标直接落在标题位置
- 复习到某个概念时，笔记顶部自动显示 一个 emoji 标记当前掌握程度（ 精通 / 熟练 / 需复习 / 薄弱 / 空白）
  **User：这里的 vault 初始化，主要是初始了什么内容，我的使用场景，导入了 CS61B 的相关笔记，然后我开始拿出题目，配合 claudian 来拆分题目和刷题**

## Acceptance Criteria

1. **Given** 学习者首次打开 canvas-vault
   **When** 运行安装引导（setup wizard）
   **Then** vault 目录结构自动创建：`raw/` · `wiki/concepts/` · `wiki/canvases/` · `outputs/exam_boards/` · `CLAUDE.md`
   **And** 每个目录包含 `.gitkeep` 占位文件确保 Git 追踪

2. **Given** vault 初始化完成
   **When** 检查 Obsidian 插件列表
   **Then** 4 个强制社区插件已安装并启用：Dataview / Templater / QuickAdd / Meta Bind
   **And** Obsidian Bases（原生核心插件，无需安装）已启用，用于复习 Dashboard 表格视图
   **And** 复习调度由后端 FSRS `update_fsrs()` MCP 计算 → 写入 concept.md frontmatter `lastReview` / `nextReview` / `reviewLevel` 字段（权威源）。前端 Dataview/Bases 只读展示，不重复计算
   **User 3：关于复习调度，我们所链接的后端就是有 相关的算法体现，所以我觉得你的astReview / reviewLevel / nextReview 字段 是怎么决定的，你要和我说清楚，然后还有一点最终我要明白我的复习进度，一定是要有相关的 dashborad UI 来实现的，而且这个 UI 我见到社区上有人用了相关插件，似乎就是可以在前端的 md 文档上渲染出交互式 GUI 的操作**
   
   > **USer: 我这里需要你解释一下，你的这里的几个插件 分别是起什么作用，**请你给我解释一下
   > User2：Periodic Note 和 Spaced Repetition ，首先Periodic Note 你这里每天生成一个新的日志对于我来说完全没有必要，因为我是要一个固定 dashboard 来查看我的每日实时更新的内容，包括你所说的Spaced Repetition 也是，要你在不知名的地方每日弹出复习卡片提醒我，我只是要有固定 dashboard 查看，而且我看社区上也有人实现了这一点，就是用到 obsidian 的 md 文件，以及原生的 base 数据库
   
   
   **And** 缺失插件在安装引导中逐一提示

3. **Given** 安装引导运行
   **When** 检测后端启动状态
   **Then** 按 AR1 顺序验证：Neo4j 连接 → Ollama(bge-m3) 可用 → FastAPI 响应 → MCP 14 工具注册
   **And** 每步失败显示具体错误和修复建议
   **And** 全部通过时显示绿色 "Ready" 状态

4. **Given** 学习者用 Templater 创建新概念文件
   **When** 触发 `concept.md` 模板   **User：请问你这里的 concept.md 的模板是起到什么作用**
   **User2：/extract_node 是聚焦于我在当前文档中，比如解题的时候我特地不懂的内容，想要拉出来讨论，他的 type 类型怎么界定，以及 claudian 怎么给这个单独拉出来的节点所赋予的属性，可以让完全空白新窗口 claudian 也能理解这就是个问题了**
   **Then** frontmatter 包含标准字段：`mastery_score: 0.30` · `bkt_params` · `fsrs_params` · `errors: []` · `tips: []` · `relationships: []` · `lastReview` · `reviewLevel` · `nextReview` · `created_at` · `updated_at`
   **And** `relationships[]` 字段 schema：
   ```yaml
   relationships:
     - target: "[[Concept B]]"
       semantic_type: "prerequisite"
       rationale: ""
       ei_techniques: []
       se_summary: ""
       created: {{date}}
   ```
   **And** 已有笔记不被模板自动修改

5. **Given** 学习者用 Templater 创建新考察文件  
   **When** 触发 `exam-board.md` 模板    **User：请你解释一下这里的`exam-board.md` 的模板是起到了什么作用**
   **Then** frontmatter 包含：`type: exam_board` · `source_canvas` · `selected_nodes: []` · `questions: []` · `score_summary`

6. **Given** concept.md 模板已就绪
   **When** 学习者通过 Templater 创建新概念文件
   **Then** concept.md 模板包含 `relationships[]` 字段用于记录概念间关系（替代独立 edge.md）    **User2： 关于字段你会记录我们的前后文件的联系，那么这里是不是也是似乎涉及到我们的 claudian 上面的 skill 更改**
   **And** 关系通过双向链接 + frontmatter relationships[] 字段定义，无需独立 Edge 文件
   > **User：请你查看一下 PRD 我们的 edge.md 模板是在使用过程中的一个什么样的流程给触发？**
   > User2：我觉得你完全没有必要来专门触发一个 edge 文档来表示前后概念的联系，原本两个文档之间的双向链接就是可以定义很多的属性了，以及还有文档的 Tag 也是同理的，请你查看 obsidian 官方社区，我们本来就是有很多的方式来定义

7. **Given** 后端 `update_fsrs()` MCP 执行完毕
   **When** 返回结果
   **Then** `nextReview` 字段已由 FSRS 算法计算并写入 concept.md frontmatter
   **And** `reviewLevel` 基于 `mastery_score` 自动映射为 emoji（≥0.9 🏆 / 0.7-0.9 🟩 / 0.5-0.7 🟨 / 0.3-0.5 🟧 / <0.3 🔴）
   **And** `lastReview` 更新为当前日期

## Tasks / Subtasks

- [ ] Task 1: Vault 目录初始化脚本 (AC: #1)
  - [ ] 1.1: 创建 `backend/app/services/vault_init_service.py`，实现 `VaultInitService.initialize_vault(vault_path: str)` 方法
  - [ ] 1.2: 创建 5 个目录 + `.gitkeep` 文件；已存在时跳过（幂等）（注：edges/ 目录已移除）
  - [ ] 1.3: 生成 `CLAUDE.md` 骨架（vault 根目录），包含 vault 结构说明和 Skill 使用指南
  - [ ] 1.4: 用 structlog 记录每个目录创建/跳过事件

- [ ] Task 2: Templater 模板文件 (AC: #4, #5, #6)
  - [ ] 2.1: 创建 `canvas-vault/.obsidian/templates/concept.md`，使用 Templater 语法（`<% tp.date.now() %>` 等）填充 frontmatter，包含 `relationships: []` · `lastReview` · `reviewLevel` · `nextReview` 字段
  - [ ] 2.2: 创建 `canvas-vault/.obsidian/templates/exam-board.md`，frontmatter 含 exam 专用字段
  - [ ] 2.3: ~~创建 `canvas-vault/.obsidian/templates/edge.md`~~ **已取消** — 关系数据改为 concept.md frontmatter `relationships[]` 字段存储
  - [ ] 2.4: 确保模板不使用 mock 数据，所有默认值有学术依据（BKT 先验 0.30 来自 Corbett & Anderson 1995）

- [ ] Task 3: 插件检测逻辑 (AC: #2)
  - [ ] 3.1: 在 `VaultInitService` 中实现 `check_required_plugins(vault_path: str) -> List[PluginStatus]`
  - [ ] 3.2: 读取 `.obsidian/community-plugins.json` 检测 4 个强制社区插件 ID：`dataview` / `templater-obsidian` / `quickadd` / `obsidian-meta-bind-plugin`
  - [ ] 3.3: 检测 Obsidian Bases 核心插件是否已启用（读取 `.obsidian/core-plugins.json` 或等价配置）
  - [ ] 3.4: 返回每个插件的安装/启用状态

- [ ] Task 4: 后端启动验证 (AC: #3)
  - [ ] 4.1: 在 `backend/app/services/health_monitor.py` 中扩展或新增 `startup_health_check()` 方法
  - [ ] 4.2: 按 AR1 顺序检测：Neo4j bolt 连接（`bolt://localhost:7691`）→ Ollama bge-m3 模型（`http://localhost:11434`）→ FastAPI 自检 → MCP 工具注册数 == 14
  - [ ] 4.3: 每步返回 `{service, status, latency_ms, error_detail}`
  - [ ] 4.4: 新增 REST endpoint `GET /api/v1/system/startup-check`，返回检测报告

- [ ] Task 5: 安装引导 API (AC: #1, #2, #3)
  - [ ] 5.1: 在 `backend/app/api/v1/endpoints/system.py` 中新增 `POST /api/v1/system/setup-wizard`
  - [ ] 5.2: 编排调用：vault 初始化 → 插件检测 → 启动验证 → 返回综合报告
  - [ ] 5.3: 报告格式：`{vault_ready, plugins: [...], backend: [...], overall_status}`

- [ ] Task 6: 测试 (AC: #1, #2, #3, #4, #5, #6)
  - [ ] 6.1: `backend/tests/unit/test_vault_init_service.py` — 目录创建幂等性、CLAUDE.md 生成
  - [ ] 6.2: `backend/tests/unit/test_vault_templates.py` — 模板 frontmatter 字段完整性验证
  - [ ] 6.3: `backend/tests/unit/test_startup_health_check.py` — 各步骤通过/失败场景

## Dev Notes

- **Service 风格参考**: `backend/app/services/rag_service.py` — structlog、类型标注、docstring 模式
- **Router 风格参考**: `backend/app/api/v1/endpoints/canvas.py` — FastAPI endpoint 结构
- **现有 health endpoint**: `backend/app/api/v1/endpoints/health.py` 已有基础健康检查，startup_health_check 应扩展而非重复
- **BKT 先验**: `mastery_score: 0.30` 来自 Corbett & Anderson (1995) 知识追踪初始先验
- **Templater 语法**: 使用 `<% tp.date.now("YYYY-MM-DD") %>` 而非 Obsidian 原生 `{{date}}`，因为 Templater 功能更丰富
- **structlog**: 项目统一使用 `structlog.get_logger(__name__)`，禁止标准 `logging`
- **Neo4j 端口**: Docker 映射 7687->7691，连接地址 `bolt://localhost:7691`
- **幂等性**: 所有操作必须可重复执行不出错（目录已存在时跳过，文件已存在时不覆盖）
- **复习调度实现**（后端 FSRS 驱动，替代 Spaced Repetition 插件 + 前端硬编码间隔）：
  - **权威源**: 后端 FSRS `update_fsrs()` MCP 计算 `next_review_date` → 写入 frontmatter `nextReview`
  - **前端只读**: Dataview/Bases 读取 frontmatter 展示，不重复计算
  - **reviewLevel emoji**: 后端基于 `mastery_score` 5 档映射：≥0.9 🏆 / 0.7-0.9 🟩 / 0.5-0.7 🟨 / 0.3-0.5 🟧 / <0.3 🔴
  - **Bases 过滤**: `nextReview <= TODAY` 显示待复习概念
  - 来源：FSRS (Free Spaced Repetition Scheduler, ts-fsrs v4, DSR 模型)
- **concept.md 模板 frontmatter 字段**（后端 FSRS 驱动）：
  ```yaml
  # 后端 FSRS 驱动（权威源）
  lastReview: null        # 后端写入
  nextReview: null        # 后端 FSRS 计算写入
  reviewLevel: "🟧"      # 后端基于 mastery_score 计算
  # 后端算法字段
  mastery_score: 0
  bkt_p_mastery: 0.30
  fsrs_stability: null
  fsrs_difficulty: null
  ```
- **[DECISION-CONFIRMED: dashboard-interactive-ui] (2026-04-13)** Dashboard 交互式 UI 方案：
  - **插件栈**: Dataview + QuickAdd + Obsidian Bases (core) + Meta Bind
  - **数据流**: DataviewJS `fetch()` / `requestUrl()` 调后端 REST API（非 FrontmatterWriter，避免 Git 历史污染）
  - **按钮 UX**: Meta Bind Button (`style: primary`) 作为视觉触发器，action 指向 QuickAdd URI
  - **被弃选项**:
    - shabegom/buttons：已弃坑（作者 2023 年找不到接手人）
    - Meta Bind 作过滤控件：Dataview 不响应 frontmatter 变化，价值有限
    - FrontmatterWriter 写 .md：Git 历史会因每次复习而变脏（lefthook auto-commit）
    - Kanban/Emera/Custom CSS Cards：社区案例稀缺或需额外插件
  - **CSS 装饰策略**: `canvas-vault/.obsidian/snippets/dashboard-cards.css` 属 Story 8.0 实施范围，本 Story 仅负责目录 + 模板 + 插件检测。CSS 起点 = kepano/obsidian-minimal cards.scss（100 行）+ Rainbell129 sharetype.css 思路（40 行）+ 自定义（80 行）
  - **调研依据**: Deep Research 报告（12 类方案）+ 3 轮并行 Agent 社区验证
  - 详细实施规范见 Story 8.0（Dashboard 插件栈 + 数据流配置）

### Project Structure Notes

- 新建文件：`backend/app/services/vault_init_service.py`
- 新建文件：`canvas-vault/.obsidian/templates/concept.md`
- 新建文件：`canvas-vault/.obsidian/templates/exam-board.md`
- ~~新建文件：`canvas-vault/.obsidian/templates/edge.md`~~ **已取消**（关系改为 concept.md frontmatter relationships[]）
- 修改文件：`backend/app/services/health_monitor.py`（扩展 startup check）
- 修改文件：`backend/app/api/v1/endpoints/system.py`（新增 setup-wizard endpoint）
- 测试文件：`backend/tests/unit/test_vault_init_service.py`
- 测试文件：`backend/tests/unit/test_vault_templates.py`
- 测试文件：`backend/tests/unit/test_startup_health_check.py`

### References

- [Source: _bmad-output/planning-artifacts/prd.md#FR-SYS-01] — Templater 模板自动生成标准化结构
- [Source: _bmad-output/planning-artifacts/prd.md#FR-SYS-06] — 首次使用安装引导
- [Source: _bmad-output/planning-artifacts/epics.md#Story-1.1] — AC 原文
- [Source: _bmad-output/planning-artifacts/prd.md#AR1] — 后端启动顺序：Neo4j -> Ollama -> FastAPI -> MCP
- [Source: backend/app/services/health_monitor.py] — 现有健康检查逻辑
- [Source: backend/app/api/v1/endpoints/system.py] — 现有系统端点

## UAT Script

> 非技术用户验收脚本

1. **验证 vault 目录结构** (AC: #1)
   - 首次在 Obsidian 中打开 canvas-vault 时，安装引导自动启动
   - 引导完成后，在 Obsidian 文件面板中应该看到 5 个子文件夹：raw、wiki/concepts、wiki/canvases、outputs/exam_boards，以及一个 CLAUDE.md 文件（注：edges/ 目录已取消）
   - 如果缺少任何文件夹，请记录

2. **验证模板创建** (AC: #4, #5, #6)
   - 打开 Obsidian，进入 canvas-vault
   - 使用 Templater 新建一个概念文件，检查文件顶部是否有学习相关字段（mastery_score、errors 等）
   - 使用 Templater 新建一个考察文件，检查文件顶部是否有考察相关字段（type: exam_board、questions 等）
   - 验证 concept.md 模板包含 `relationships: []` 字段（替代独立 edge.md 模板）
   - 验证 concept.md 模板包含 `lastReview` / `reviewLevel` / `nextReview` 复习调度字段
     > User：这里的创建是模板是用 claudian 创建的吗？然后之后我的学习工作流也经常接触到 claudian，所以我需要你结合实际的工作流来给我解释一下

3. **验证插件检测** (AC: #2)
   - 在安装引导报告中，应该能看到 3 个社区插件 + Obsidian Bases 核心插件的状态
   - 如果有插件未安装，报告应该明确指出名称

4. **验证后端连通** (AC: #3)
   - 在 Claudian 中说"帮我检查系统状态"
   - 应该看到 4 个服务的检测结果（Neo4j、Ollama、FastAPI、MCP）
   - 全部绿色表示就绪；红色项会显示具体的修复建议

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-1.1.1 | pytest | `.venv/bin/pytest backend/tests/unit/test_vault_init_service.py -x -q` | 0 failed |
| CP-1.1.2 | pytest | `.venv/bin/pytest backend/tests/unit/test_vault_templates.py -x -q` | 0 failed |
| CP-1.1.3 | pytest | `.venv/bin/pytest backend/tests/unit/test_startup_health_check.py -x -q` | 0 failed |
| CP-1.1.4 | ruff | `ruff check backend/app/services/vault_init_service.py backend/app/services/health_monitor.py` | exit 0 |

## User Feedback & Changes

### Feedback Log
<!-- Users write BMAD-ANNO callouts below -->

### Deviation Notes

**批注处理记录 (2026-04-13)**

1. **插件精简** (User2 line 35): Periodic Notes + Spaced Repetition 移除 → 用 Bases + Dataview Dashboard 替代。社区方案：frontmatter NextReview + Dataviewjs 间隔计算。
2. **extract_node 类型** (User2 line 48): type 由 Templater 模板预设为 "concept"，Claudian 通过 extracted_from 字段追溯来源，空白新窗口读 frontmatter 即可理解上下文。
3. **edge.md 取消** (User2 line 60): 改为 concept.md frontmatter relationships[] 字段。双向链接 + Tag 已足够定义关系。
4. **Claudian 工作流** (User line 142): 模板由 Templater 创建，Claudian 触发 Skill → MCP → Templater 生成文件。
5. **N1: 复习字段权威源** (User 3 line 37): `lastReview`/`nextReview`/`reviewLevel` 由后端 FSRS `update_fsrs()` MCP 计算写入 frontmatter（权威源）。前端 Dataview/Bases 只读展示，不重复计算。reviewLevel emoji 由后端基于 mastery_score 5 档映射（≥0.9 🏆 / 0.7-0.9 🟩 / 0.5-0.7 🟨 / 0.3-0.5 🟧 / <0.3 🔴）。Dashboard UI 方案标记 [DECISION-PENDING: dashboard-interactive-ui]，先社区调研再决定。
6. **N2: Skill 字段联系** (User2 line 73): 确认 `relationships[]` 字段涉及 Skill 更改。`/edge_discuss` Skill 讨论结束后写入当前概念的 frontmatter。`/extract_node` Skill 拉出新节点时更新两端 frontmatter。Claudian Skill 是写入触发者，frontmatter 是持久化存储。
7. **N7: Dashboard UI 决策闭合** (2026-04-13): 经 3 轮并行 Agent 调研（社区成熟度对比 + A/B 方案最终效果验证 + 5 CSS 包实读代码审查），从 5 候选收敛到：Dataview + QuickAdd + Bases + Meta Bind。Meta Bind 仅用于按钮 GUI（不用于过滤控件，因 Dataview 不响应 frontmatter 变化）。数据流走 DataviewJS fetch API（不写 frontmatter，保持 Git 历史干净）。CSS 起点 kepano + Rainbell 混合（~220 行）。详细规范放 Story 8.0，本 Story 层面新增第 4 个插件（Meta Bind）并在 AC #2 + Task 3.2 校验。

## Dev Agent Record

### Agent Model Used
(to be filled by Dev agent)

### Debug Log References

### Completion Notes List

### File List
