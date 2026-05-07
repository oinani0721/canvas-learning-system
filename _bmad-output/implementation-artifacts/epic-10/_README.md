---
epic_id: "10"
title: "DeepTutor Fork + Canvas 5 大核心 MVP 集成"
prd_id: "canvas-learning-system"
status: "in-progress"
priority: "P0"
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
round_origin: "round-22"
fork_baseline_commit: "9389178"
fork_url: "https://github.com/oinani0721/DeepTutor"
worktree: "feature-deeptutor-canvas-mvp"
mvp_window: "10 days"
start_date: "2026-05-06"
target_complete: "2026-05-16"
---

# Epic-10: DeepTutor Fork + Canvas 5 大核心 MVP 集成

> **决策来源**: Round-22（`_bmad-output/research/round-22-deeptutor-fork-mvp-2026-05-06.md`）+ Round-22 Deep Explore 调研（`_bmad-output/research/round-22-deeptutor-deep-explore-2026-05-06.md`）
>
> **用户最终拍板**（一字不改）: "我是想要舍弃 obsidian，直接把我们 Canvas learning systeam 思想在 deeptutor 实现...我先试一下集成的效果先"

---

## Why（用户痛点 + 选择 fork 路线的根因）

### 用户决定性批注（Agent A 提取，原话锁定）

**D1 功能需求优先（Round-19 L59）**:
> "我是从功能需求出发，我是需要思考 DeepTutor 能不能有条件实现我所需求的功能，然后再以 Canvas learning systeam 源码为参考，我们给 DeepTutor 构建相关的新代码更新"

**D2 取代 Obsidian（Round-18 L805）**:
> "我希望我们的知识库不用上传文件，而是指定直接访问我们的指定文件夹，然后我们和前端 UI 交互可以直接修改到我们的本地文件"

**D3 5 大核心权威定义（Round-20 L222）**:
> "Canvas learning systeam 的核心是原白板，检验白板，个人记忆系统在原白板和检验白板的应用，笔记精确返回系统，以及推测出什么时候该使用检验白板复习的系统"

**D4 Graphiti 贯穿（Round-21 L1085）**:
> "其中我的个人记忆系统的后端 Graphiti 设计就需要深度调研思考...整个闭环必须由 Graphiti 后端贯穿，否则检验白板无法'深刻'考察"

**D5 Fork MVP（Round-22 前言）**: 见上"用户最终拍板"

### 决策演化（4 轮思考）

```
Round-18 (深度改造 11 Gap, 34-45d)
  ↓
Round-19 (Unix CLI 拆分, 22-28d)
  ↓
Round-20 (TutorBot 颠覆, 0.5d POC 验证 file ops)
  ↓
Round-22 (10 天 Fork MVP) ← 当前 Epic-10 起点
```

### 集成必要性（Round-22 Deep Explore 10 Agent 调研收敛）

5 个独立维度调研，全部指向同一结论：**Canvas 5 大核心 100% 必要、0 冗余**。

| Canvas 核心 | DeepTutor 现状 | 集成必要性 |
|---|---|---|
| OriginWhiteboard + wikilink 双链 | AI 推断 + book 内孤立 + 跨 book 不复用 | ⛔ 必要补全 |
| ExamWhiteboard + AutoSCORE | 无 4 维评分 | ⛔ 必要补全 |
| MasteryDashboard (BKT + FSRS) | `is_correct` 二值，无掌握度建模 | ⛔ 必要补全（DeepTutor 自留 `services/canvas/client.py` hook） |
| ErrorCandidate (4 类错误归因) | 无错误归因 | ⛔ 必要补全 |
| Graphiti episodic memory | 覆盖式 markdown 无版本 | ⛔ 必要补全 |
| **Whiteboard UI 主入口** | 无以图为入口的浏览模式 | ⛔ Round-22 原报告漏项，调研补全 |

---

## Goals（10 天 MVP 验证目标）

### 主目标
- **Day 0-10**：完整可用 MVP，5 验证场景全过
- **0 mock**：所有 API 真实连接（Canvas :8011 + DeepTutor :8001）
- **5 大核心全嵌入**：不是 PoC，是 wikilink → quiz → mastery → 错误归因 → 复习推送的完整 E2E

### 5 验证场景（Pass = MVP 成功，Round-22 §四 + Deep Explore 扩展）

| # | 场景 | 通过标准 | Day | Story |
|---|---|---|---|---|
| **S1** | DeepTutor 写 `[[recursion]]` → 自动完成 → 点击跳转 | wikilink 跳转 < 1s | Day 1-2 | 10.2 |
| **S2** | 右键 callout → "Generate Quiz via Canvas ACP" → mastery 更新 | 后端调 Canvas endpoint | Day 4 | 10.4 |
| **S3** | 答题 → AutoSCORE 4 维评分 → Dashboard 显示 | mastery.value 改变 | Day 7 | 10.6 |
| **S4** | Whiteboard 显示节点 + wikilink 边 | ≥10 节点 + 边渲染 | Day 5-6 | 10.5 |
| **S5** | 答错 → 错误日志 → Day 0/3/7 推送 | console 显示 `[REVIEW DUE]` | Day 8 | 10.7 |

---

## Capabilities（功能层级清单）

### 基础层（Day 1-2）
- Wikilink 渲染 + 自动完成（remarkWikilinkPlugin 注入 RichMarkdownRenderer）
- wikilink_proxy 后端（代理 Canvas GraphService）
- 双 Docker Compose（Canvas :8011 + DeepTutor :8001）

### 融合层（Day 3-6）
- CanvasVaultAdapter（NetworkX → Spine JSON，路径 B 绕过 AI）
- Whiteboard 路由（ReactFlow + ChatPanel，方案 Y）
- BlockType Enum 扩展（ORIGIN_WHITEBOARD + EXAM_WHITEBOARD）

### 追踪层（Day 7-10）
- MasteryDashboard Block（BKT/FSRS 接入）
- ExamWhiteboard + ErrorCandidate（AutoSCORE 4 维评分）
- UserNote 现场编辑（contentEditable + 持久化）
- 8 通道 Heartbeat（Day 0/3/7 推送）

---

## Stories 索引（9 个 Story 按 Day 节奏）

| Story ID | 标题 | Day | Status | UAT 验收单 |
|---|---|---|---|---|
| **10.1** | Day 0 Fork & Baseline | Day 0 | ✅ done | `验收单/Story-10.1-*.md` |
| **10.2** | Day 1 Wikilink Frontend Pipeline | Day 1 | ✅ done | `验收单/Story-10.2-*.md` |
| **10.3** | Day 2 Cleanup + Vault Mount | Day 2 | ready-for-dev | `验收单/Story-10.3-*.md` |
| **10.4** | Day 3-4 CanvasVaultAdapter (路径 B) | Day 3-4 | ready-for-dev | `验收单/Story-10.4-*.md` |
| **10.5** | Day 5-6 Whiteboard 路由 + ReactFlow (方案 Y) | Day 5-6 | ready-for-dev | `验收单/Story-10.5-*.md` |
| **10.6** | Day 7 MasteryDashboard Block | Day 7 | ready-for-dev | `验收单/Story-10.6-*.md` |
| **10.7** | Day 8 ExamWhiteboard + ErrorCandidate | Day 8 | ready-for-dev | `验收单/Story-10.7-*.md` |
| **10.8** | Day 9 UserNote 现场编辑 | Day 9 | ready-for-dev | `验收单/Story-10.8-*.md` |
| **10.9** | Day 10 UAT 收官 + go/no-go 决策 | Day 10 | ready-for-dev | `验收单/Story-10.9-*.md` |

---

## Acceptance Criteria（Epic 级 AC）

### AC #1: Wikilink 全链路通

- **Given** DeepTutor fork 启动 + Canvas backend 启动 + 用户笔记含 `[[concept]]` 文本
- **When** 用户在 Co-Writer 或 book 编辑器中查看该笔记
- **Then** `[[concept]]` 渲染为蓝色链接（`<a class="wikilink">`）
- **And** 点击链接跳转到目标笔记 < 1s
- **And** 渲染覆盖至少 9/14 BlockType（含 CalloutBlock 修复后）

### AC #2: 5 验证场景全过

- **Given** Day 10 收官时
- **When** 用户按 UAT 验收单（10.1-10.9）跑测试矩阵
- **Then** S1 wikilink 跳转、S2 ACP quiz、S3 AutoSCORE、S4 Whiteboard 节点、S5 review 推送 5 条**全 PASS**
- **And** 无 mock 服务（所有 API 真实调用）

### AC #3: BlockType Enum 无破裂

- **Given** Day 7-8 BlockType Enum 扩展（MASTERY_DASHBOARD、EXAM_WHITEBOARD、ERROR_CANDIDATE）
- **When** 跑 DeepTutor 现有 test suite (`pytest tests/models/test_blocks.py`)
- **Then** 14 个原 BlockType 仍可用、序列化正常
- **And** 新增 3 个 BlockType 通过 Pydantic validation

### AC #4: 双 Docker 端到端

- **Given** Canvas worktree compose + DeepTutor fork compose
- **When** `docker compose up -d` 同时启动两边
- **Then** `:8011/api/v1/health` 200 + `:8001/` 200 + `:3782/` 200
- **And** CORS preflight 通过（DeepTutor :3782 → Canvas :8011）
- **And** 容器重启后数据持久化（vault md + Neo4j data）

### AC #5: 0 生产债务

- **Given** Day 10 commit `mvp-complete`
- **When** 审查代码 + .env 配置
- **Then** 无硬编码 credentials（全部 .env）
- **And** 无 mock 服务保留
- **And** Day 6 go/no-go 决策已文档化（`DECISION-DAY-6.md` + `DECISION-DAY-10.md`）

### AC #6: Graphiti 闭环贯穿（D4 落地，对抗性审查 H3+H4+M1 升级）

> **新增依据**：用户 D4（Round-21 L1085）"整个闭环必须由 Graphiti 后端贯穿，否则检验白板无法'深刻'考察"。Round-22 二轮对抗性审查（2026-05-07 Claude 5 Agent + ChatGPT GPT-5 Pro 第二意见）发现 D4 在 Epic-10 仅 Story 10.8 一个 Task 写入未读取，升 Epic 级 AC。

- **Given** Day 8 ErrorCandidate 已落地（Story 10.7）+ Day 9 UserNote 已落地（Story 10.8）+ Day 10 复习推送已可触发（Story 10.7 / Heartbeat）
- **When** 用户答错 → ErrorCandidate 写 Graphiti episodic memory（含 `{时间, 概念 ID, 错误类型, 用户批注}`）
- **And** ≥ 24h 后用户触发复习 → 系统多 hop 检索 Graphiti（关联节点 / 历史错题 / 跨概念错误模式）
- **Then** 复习推送 / NodeDetailPanel 显示**关联历史错题摘要**（如 "3 天前你在 X 概念栽过，本次出题关联 Y 概念"）
- **And** 出题（exam_proxy ACP）参数注入历史 episodic 上下文，针对性测试相关概念
- **And** Day 10 UAT 验证场景 S6（新增）：写入 → 等待 → 多 hop 召回 → 针对性出题，全链路通过
- **And** 协同验证两白板的应用：原白板答错的概念 → 检验白板出针对性题（核心 3 "在两白板的应用"语义落地）

> **联动 Story**：Story 10.7（写入 episodic）+ Story 10.8（关联用户批注）+ Story 10.9（UAT S6 验证）

---

## Risks（用户批注风险红线 + Day 5 BlockType 连锁风险）

| # | 风险 | 触发 | 缓解 | 用户红线 |
|---|---|---|---|---|
| **R1** | BlockType Enum patch 触发 30+ Pydantic validation 错误 | Day 7-8 | 分批：Day 7 先加 1 块 → 跑全测试 → Day 8 再加 2 块 | 不能破 quiz 渲染 |
| **R2** | Canvas Docker 起不来（Neo4j 连不上 / 容器名冲突） | Day 0-2 | `host.docker.internal:7691` + `docker rename` 释放冲突容器名 | 双系统要可独立启停 |
| **R3** | DeepTutor 上游 30 天 24 release 中途 breaking | 任何天 | Day 0 打 `mvp-baseline` tag，**MVP 期间不 git pull upstream** | fork 要稳定（NEG-3） |
| **R4** | wikilink_graph_service 期望 obsidiantools vault 布局 | Day 2 | 建假 `.obsidian/` 或 fork 服务放宽检查 | vault 结构不能改 |
| **R5** | CORS 阻塞 DeepTutor frontend(:3782) → Canvas(:8011) | Day 2 | ✅ Day 0 已加 :3782 / :8001 到 CORS_ORIGINS | 实时跨域要通 |
| **R6** | Whiteboard ReactFlow 性能（1000+ 节点） | Day 6 | 2-hop 限制、虚拟滚动 | 不能卡 UI |
| **R7** | CalloutBlock 不走 MarkdownRenderer | Day 2 | 1 行修复（Story 10.3 Task 1） | callout 内 wikilink 要生效 |
| **R8** | UX-3 跨时间错误重现（教育场景生产 near-zero） | Day 7+ | 降级 AC：先做"看到 mastery 趋势"，跨时间错误重现降为 P2 留 Risks | 不强求最高目标 |

---

## Dependencies（前置 + 外部）

### 上游决策依赖
- **Round-15 ~ Round-22**: 决策链完整记录在 `_bmad-output/research/round-1*.md` ~ `round-22-*.md`
- **Round-21 (30.9d)**: Canvas 5 大核心实施完成（FSRS/BKT/AutoSCORE）
- **Round-20**: TutorBot Agent + filesystem.py 已具备 file ops 能力
- **Round-18**: 8 通道推送 + vault 直接访问

### 外部依赖
- **DeepTutor v1.3.7** (commit `9389178`): fork 起点，已 tag `mvp-baseline`
- **Canvas worktree** (此 worktree): `feature-deeptutor-canvas-mvp` 派生自 `feature-obsidian-hybrid-dev` 的 commit `e6b43dc`
- **fork 仓库**: `~/Desktop/canvas/deeptutor-fork/`，分支 `mvp-canvas-integration`，已 commit `23a2853` (Day 1)

### 复用的 Canvas 后端（零改动）
- `backend/app/services/wikilink_graph_service.py` — NetworkX `build_graph()` / `find_neighbors()`
- `backend/app/services/exam_service.py` — ACP 完整流
- `backend/app/services/autoscore.py` — AutoSCORE 4 维评分
- `backend/app/services/mastery_engine.py` — BKT/FSRS 融合
- `backend/app/services/notification_channels.py` — 8 通道推送
- `backend/app/api/v1/endpoints/wikilink.py` — 4 个 wikilink REST endpoint

### 基础设施
- Neo4j 5.26+ (Canvas KG 存储, Bolt :7691, HTTP :7478)
- Docker 29+ + docker-compose 2+
- Node 18 LTS (DeepTutor frontend)
- Python 3.10+ (Canvas + adapter)

---

## 集成方案（已锁定决策，调研收敛）

### 路径 B：CanvasVaultAdapter（绕过 AI）— Day 3-4
- **不**让 DeepTutor AI 推断图，直接用 Canvas vault 结构转 Spine JSON
- **关键 API**: `POST /books/confirm-spine` 接受完整 Spine payload（Agent 2.4 发现）
- **工作量**: ~300 行 Python (CanvasVaultAdapter + CLI)
- **优点**: LLM 成本 0 + 用户结构 100% 保留

### 方案 Y：Whiteboard 独立路由 — Day 5-6
- 新建 `/whiteboard/:id` 路由（不改 `/book`）
- 用 ReactFlow（cp Canvas 代码 + npm install）
- 节点 Neo4j 查询，边按 mastery + fsrs_due 着色
- **工作量**: 18-24h (Day 5-6 可控)
- **不选 Cytoscape 原因**: fork 已装 Cytoscape v3.33.1 但需重写交互；ReactFlow 直接 cp Canvas 已验证代码更快

### CalloutBlock 修复（顺手）— Day 2
- 1 行改 `CalloutBlock.tsx`：`<div>{body}</div>` → `<MarkdownRenderer content={body} />`
- 让 callout 内 `[[wikilink]]` 渲染（Day 1 已激活的 remarkWikilinkPlugin 自动生效）

---

## 决策矩阵（Day 10 后选路）

| 路径 | 触发条件 | 后续投入 |
|---|---|---|
| **A. 继续 fork**（深度集成）| S1-S5 全过 + 5 天主动用 + 想 ship 单一产品 | 4-8 周生产硬化，月度上游同步 |
| **B. 退回独立包**（9/10 维护性）| Fork 脆弱 / 延迟无法接受 | 2-4 周抽出 `deeptutor-canvas` PyPI 包 |
| **C. 混合**（fork lite + 抽核心）| 部分功能 fork 好用 / 部分需独立 | 6-10 周拆分维护 |

**默认决策规则**:
- S1+S2+S3 全过 + 5 天主动用 → **A**
- 用 < 6 天就停了 → **B**
- 5 个核心只用 2 个 → **C**

---

## 用户主权约束（NEG 反对批注落地）

- **NEG-1（Round-12 + 2026-05-07 对抗性审查澄清）**: ❌ 不做 **AI 自动**跨白板关联（不允许 AI 推断或自动建边）；✅ 允许"用户主动浏览全 vault wikilink 全景视图"（Story 10.5 Whiteboard 仅展示**用户已显式写的 wikilink** + 用户创建的边，禁止 AI 自动新增跨白板边）— 旧 Tauri 时代"AI 跨白板自动关联"功能已砍
- **NEG-2（Round-19）**: ❌ 不是"集成 Canvas 模块"，是"参考 Canvas 思想在 DeepTutor 写新代码"
  - 落地体现: Day 1 staging 文件 cp 后必须修 import + visit.SKIP bug，不是直接 cp 即用
- **NEG-3（Round-22）**: ❌ MVP 期间不 git pull upstream（已 tag `mvp-baseline`）
- **NEG-4（Round-12）**: ❌ Graphiti 不替代 wikilink RAG，是事件存储

---

## UX 痛点（落地到具体 Story 的 AC）

- **UX-1（Round-15 L44）批注是核心**: 7 callout 类型必须一等公民 → Story 10.3 + Story 10.7
- **UX-2（Round-17 L50）RAG 必须有基准**: Story 10.4 (路径 B) + Story 10.9 UAT 含基准对比
- **UX-3（Round-15 L33）跨时间错误重现**: 降级为 P2，写入 Risks 而非 AC
- **UX-4（Round-14 L30）Graphiti 同步**: Day 9-10 由 Graphiti 后端贯穿（Day 8 ErrorCandidate 落库 Graphiti episodic）
- **UX-5（Round-15 L91）FSRS 是成熟方案**: Story 10.6 直接复用 Canvas `mastery_engine.py` (FSRS Anki 7 亿条训练验证)
- **UX-6（Round-14 L30）Agent 询问而非替决定**: Story 10.7 ErrorCandidate 4 类错误**用户选**而非 AI 推断

---

## 关联文档

- **决策报告**: `_bmad-output/research/round-22-deeptutor-fork-mvp-2026-05-06.md`（主报告）
- **调研报告**: `_bmad-output/research/round-22-deeptutor-deep-explore-2026-05-06.md`（10 Agent 整合）
- **CURRENT_TASK**: `CURRENT_TASK.md` (Day 1 收官状态 + 恢复锚点)
- **决策批注**: `_bmad-output/决策批注/D17-round22-fork-mvp-2026-05-06.md`
- **fork 仓库**: `~/Desktop/canvas/deeptutor-fork/` (commit `23a2853`, tag `mvp-day-1-patches`)
- **memory**: `decision_round22_fork_mvp.md` (用户决策最高优先级 anchor)

---

## Round-22 二轮修订（2026-05-07 — Day 1 完成后 6 报告深度调研收敛）

> **修订源**: 用户 Day 1 完成后批注 + 5 并行 Agent 深度调研（4 份新报告 + 2 份 Day 0 历史报告交叉引用）

### 新发现（6 项 — 直接影响 Epic-10 spec 解读）

#### F1 ⛔ Guided Learning v1.2.0 已删除（CLI/SDK 报告 §五 关键发现）

DeepTutor v1.2.0 Release Notes 确认 **Guided Learning 模块完全删除**（~5300 行代码）。**Book Engine 是其继任者**（Spine + 14 BlockType 渲染体系）。

**影响**:
- 本 _README §"集成方案" 提到的 Guided Learning 实际为 Book Engine
- Story 10.4 路径 B 的 `POST /books/confirm-spine` API 是 Book Engine 入口（非 GL）
- 所有"AI 推断图谱"语义 = Book Engine 的 Spine 推断（Path Y 绕过它）

#### F2 Math Animator + Visualize 渲染 100% 在 server-side（Desktop 报告 §一/§六）

5 个并行 Agent 验证: Math Animator (Manim+ffmpeg→MP4) + Visualize (5 render_mode SVG/Chart.js/Mermaid/HTML/auto) **必须 server 渲染后客户端展示**。

**影响**:
- CLI/SDK 用户拿到的是文件路径或代码字符串，**不能直接"看到"动画/图表**
- M4 映射对（13 映射中最强）必保留可视化能力 → Story 10.5 Whiteboard 必须能内嵌渲染
- Story 10.9 UAT 必须含 Math/Visualize 视觉验证场景

#### F3 桌面化 100% 可行（Desktop 报告 §四）

Tauri 2.0 vs Electron 决策**已锁定 Electron + AnythingLLM 模式**（59.7k stars 商用先例）：
- **包大小**: 100+ MB（可接受，VS Code 200+ MB 参照）
- **工期**: 1-2 周框架 + 4 周跨平台发布（macOS notarization 含）
- **不选 Tauri**: Rust 学习曲线 + macOS 签名坑 + 工期紧

**影响**:
- Day 11+ 桌面化拆分为 **Epic-11**（不扩展 Epic-10），见本文档末尾"后续路线"

#### F4 Day 2 Vault 接入工作量重估（Day 2 Vault 报告 §四）

原 Story 10.3 spec 0.5d 严重低估。Phase 拆分:
- **Phase A**（2-3h，立即可做）: 0 改动 + manager.py:438 `restrict_to_workspace=False` 已默认开沙箱（实测验证）
- **Phase B**（6-9h，可选升级）: VaultMonitor daemon (~120 行) + DocumentAdder vault_mode 参数 + file lock + atomic rename

**影响**:
- Story 10.3 工作量改为 **1.5-2 day**（推荐拆 10.3a + 10.3b）
- Day 2 不一定全做完 Phase B，Phase A 即可解锁 Day 3+ 工作

#### F5 Chat 6 capability + TutorBot 7 features 双轨并存（Chat vs TutorBot 报告 §三）

DeepTutor 的功能体系:
- **Chat Workspace**（6 capability）: Chat / Deep Solve / Quiz Generation / Deep Research / Math Animator / Visualize
- **TutorBot**（7 features）: Soul Templates / Independent Workspace / Proactive Heartbeat / Full Tool Access / Skill Learning / Multi-Channel / Team & Sub-Agents
- **5 学习场景决策矩阵**确认: Chat 适合"瞬时问题"，TutorBot 适合"长程伴学"

**影响**:
- Canvas 的 5 大核心**通过双轨触达**：白板讲题（Chat Math Animator）+ 长程复习（TutorBot Heartbeat→8 通道推送）
- Story 10.3/10.5/10.8 加 TutorBot 优先注解（哪个 capability 适合哪个 Canvas 核心）
- 不需新增 Story，仅文档批注

#### F6 ReactFlow 选定（CLI/SDK 报告 §四 + Day 0 实测）

Whiteboard 路由（Story 10.5）确认用 ReactFlow（非 Cytoscape）:
- DeepTutor fork 已装 Cytoscape v3.33.1（用于其他场景）
- ReactFlow 直接 cp Canvas worktree 已验证代码（更快）
- 工作量 18-24h（Day 5-6 可控）

---

### 修订映射表（Round-22 → Epic-10 Story）

| Round-22 新发现 | 落地 Story | 修订动作 |
|---|---|---|
| F1 Guided Learning 删除 / Book Engine 继任 | Story 10.4 | spec 文档批注 "API 是 Book Engine" |
| F2 Math/Visualize server-side | Story 10.5 + 10.9 | 10.5 加内嵌渲染 Task；10.9 UAT 加 Math/Visualize 验证场景 |
| F3 桌面化可行 | **Epic-11**（新建，本文档外） | Day 11+ 启动条件（Path A 触发后） |
| F4 Day 2 vault 工作量翻倍 | Story 10.3 | spec 加 Phase A/B 拆分 + VaultMonitor 任务清单 |
| F5 Chat vs TutorBot 双轨 | Story 10.3 / 10.5 / 10.8 | spec 加"推荐路径"注解（哪个 capability 用） |
| F6 ReactFlow 选定 | Story 10.5 | spec 加 ReactFlow 决策依据 |

---

### 后续路线（Epic-11 预案，Day 11+ 触发）

如 Day 10 UAT 选 **Path A（继续 fork）**，启动 Epic-11:

| Story | 标题 | Day | 工作量 |
|---|---|---|---|
| 11.1 | Electron 框架 + Web 包装 | Day 11-12 | ~12h |
| 11.2 | IPC Bridge + FastAPI subprocess | Day 13-14 | ~16h |
| 11.3 | Vault 深度集成 + 渲染验证（Math/Visualize 内嵌） | Day 15-18 | ~28h |
| 11.4 | 跨平台发布（macOS notarize + Win + Linux） + electron-updater | Day 19-22 | ~24h |

**前置条件**: Epic-10 Day 10 UAT 5 验证场景 S1-S5 全 PASS。

详见 `_bmad-output/implementation-artifacts/epic-11/_README.md` 和 `_bmad-output/决策批注/D18-desktop-app-electron-2026-05-07.md`。

---

### Round-22 调研报告索引

| 报告 | 关键贡献 |
|---|---|
| `round-22-deeptutor-fork-mvp-2026-05-06.md` | 主决策报告（D17 锚定） |
| `round-22-deeptutor-deep-explore-2026-05-06.md` | 10 Agent 5 大核心可行性整合 |
| `round-22-day2-vault-access-design-2026-05-06.md` | Day 2 Phase A/B 设计 + VaultMonitor 代码 |
| `round-22-chat-vs-tutorbot-usage-comparison-2026-05-06.md` | Chat 6 vs TutorBot 7 决策矩阵 |
| `round-22-cli-sdk-book-engine-deep-explore-2026-05-07.md` | Guided Learning 删除发现 + Book Engine 继任 |
| `round-22-desktop-app-rendering-deep-explore-2026-05-07.md` | Math/Visualize server-side 验证 + Electron 决策 |

---

*Epic-10 锚定文档。所有 Story 必须引用本文件 + 对应 Round-22 报告章节。*

*二轮修订日期: 2026-05-07 — 6 报告深度调研收敛 + Epic-11 路线确立*
