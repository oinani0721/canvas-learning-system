---
decision_ids: ["D17"]
status: "annotated"
date: "2026-05-06"
related_round: "round-22"
related_prd: "_bmad-output/research/round-22-deeptutor-fork-mvp-2026-05-06.md"
related_research: "_bmad-output/research/round-22-deeptutor-deep-explore-2026-05-06.md"
related_epic: "epic-10"
related_stories: ["10.1", "10.2", "10.3", "10.4", "10.5", "10.6", "10.7", "10.8", "10.9"]
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
user_decision: "Fork DeepTutor + 嵌入 Canvas 5 大核心 + 10 天 MVP 验证"
fork_baseline: "9389178"
mvp_window_days: 10
---

# D17: Round-22 DeepTutor Fork MVP 决策

> **Plan ID**: EPIC1-BMAD-DEV-ASSESS-2026-04-17
> **Round**: 22（10-Agent 并行调研：5 数据层 + 5 渲染交互层）
> **决策日期**: 2026-05-06
> **Epic 落地**: epic-10（Story 10.1-10.9）

---

## 决策原文（用户一字不改）

**最终拍板（Round-22 触发）**:
> "我是想要舍弃 obsidian，直接把我们 Canvas learning systeam 思想在 deeptutor 实现，我的批注有列出来哪些 deeptutor 和我们 Canvas learning systeam 的思想和功能相对应，缺少功能我们就参考我们的 Canvas learning systeam 的源码集成。**我先试一下集成的效果先**"

---

## 核心决策点（4 个）

### D17.1 路线选择: Fork DeepTutor

**对比 4 个候选**:
- [ ] 选项 A: Round-18 深度改造 11 Gap (34-45d) — ❌ 太重
- [ ] 选项 B: Round-19 Unix CLI 拆分 (22-28d) — ❌ 拆得过碎
- [ ] 选项 C: Round-22 v1 独立包 (10d) — ❌ 用户反对（要 fork）
- [x] **选项 D: Round-22 v2 Fork DeepTutor (10d) — ✅ 用户最终选择**

**理由**:
- D2（Round-18 L805）: "知识库不用上传文件，直接访问指定文件夹" → fork 让 vault 直接 mount 进 DeepTutor 容器
- D5（Round-22 前言）: "我先试一下集成的效果先" → 10 天 MVP 验证最快路径

### D17.2 集成深度: 5 大核心嵌入

**Canvas 5 大核心**（D3，Round-20 L222 一字不改）:
> "Canvas learning systeam 的核心是原白板，检验白板，个人记忆系统在原白板和检验白板的应用，笔记精确返回系统，以及推测出什么时候该使用检验白板复习的系统，以上 5 点"

**集成必要性**（10-Agent 调研 100% 收敛）:
- [x] OriginWhiteboard + wikilink 双链 — DeepTutor AI 推断图，无用户主权（Agent 1.3 + 2.1）
- [x] ExamWhiteboard + AutoSCORE — DeepTutor `is_correct` 二值，无 4 维评分（Agent 1.4）
- [x] MasteryDashboard (BKT + FSRS) — DeepTutor 完全缺失（Agent 1.4）
- [x] ErrorCandidate (4 类错误归因) — DeepTutor 无错误建模（Agent 1.4）
- [x] Graphiti episodic memory — DeepTutor 覆盖式无版本（Agent 1.2）
- [x] **Whiteboard UI 主入口** — 调研补全：原 Round-22 漏项（Agent 2.5）

### D17.3 实施路径: 路径 B + 方案 Y

**路径 B（CanvasVaultAdapter，Day 3-4）**:
- 关键发现 (Agent 2.4): `POST /books/confirm-spine` API 接受完整 Spine payload
- 绕过 IdeationAgent + SpineSynthesizer (LLM 成本 = 0)
- ~300 行 Python adapter，**不改 fork 内部代码**

**方案 Y（Whiteboard 路由，Day 5-6）**:
- 中等改造 18-24h（与 10 天 MVP 时间表契合）
- ReactFlow（cp Canvas 已验证代码）+ 后端 Neo4j 查询
- 优于方案 X（仅复用 ConceptGraphBlock）和方案 Z（重构 Space 主页 40-50h）

**意外红利**:
- Cytoscape v3.33.1 已装在 fork package.json 但未用（Agent 2.1）— 备选库
- DeepTutor `services/canvas/client.py` 已留 Canvas 集成 hook（Agent 1.4）

### D17.4 时间窗 + 退出策略

**10 天 MVP**:
- Day 0 ✅ Fork & Baseline (Story 10.1)
- Day 1 ✅ Wikilink Frontend (Story 10.2)
- Day 2 Cleanup + Vault Mount (Story 10.3)
- Day 3-4 CanvasVaultAdapter (Story 10.4)
- Day 5-6 Whiteboard 路由 (Story 10.5)
- Day 7 MasteryDashboard (Story 10.6)
- Day 8 ExamWhiteboard + ErrorCandidate (Story 10.7)
- Day 9 UserNote 现场编辑 (Story 10.8)
- Day 10 UAT + 决策 (Story 10.9)

**退出策略（Day 10 决策矩阵）**:
- 5 验证全过 + 主动用 ≥ 5 天 → **Path A** 继续 fork production (4-8 周硬化)
- 任何场景失败 / 主动用 < 6 天 → **Path B** 退回独立包 (2-4 周抽 PyPI 包)
- 仅用 ≤ 3 个核心 → **Path C** 混合 (6-10 周拆分维护)

---

## 用户批注落地（Round-22 之前 23+ 条）

### 决定性批注 (D1-D5)
- [x] D1 功能需求优先 (R-19 L59) → Epic-10 Why 章节核心叙事
- [x] D2 取代 Obsidian (R-18 L805) → Story 10.3 vault 直接挂载
- [x] D3 5 大核心权威 (R-20 L222) → Story 10.4-10.7 全覆盖
- [x] D4 Graphiti 贯穿 (R-21 L1085) → Story 10.8 UserNote 写入 Graphiti
- [x] D5 Fork MVP (R-22) → Story 10.1 fork & baseline

### 功能映射 (M1-M13)
全部 13 条精确映射对落地到对应 Story 的 trace 字段。

### UX 痛点 (UX-1 ~ UX-6)
- [x] UX-1 批注核心 → Story 10.3 (CalloutBlock) + 10.7 (ErrorCandidate) + 10.8 (UserNote)
- [x] UX-2 RAG 基准 → Story 10.4 路径 B（用户结构保留替代 AI 推断）
- [ ] UX-3 跨时间错误重现 → 降级 P2 写入 Risks（学术 near-zero 难度）
- [x] UX-4 Graphiti 同步 → Story 10.8 annotation 写入 episodic memory
- [x] UX-5 FSRS 成熟 → Story 10.6 直接复用 Canvas mastery_engine.py (Anki 7 亿条训练验证)
- [x] UX-6 Agent 询问 → Story 10.7 ErrorCandidate 用户自选 4 类

### 反对/否定 (NEG-1 ~ NEG-4)
- [x] NEG-1 砍跨白板 → Round-22 Round-22 已确认 (Round-12 砍掉)
- [x] NEG-2 参考非复制 → Story 10.2 已实证 (cp + 修 import + visit.SKIP bug)
- [x] NEG-3 不 pull upstream → Story 10.1 已 tag mvp-baseline，MVP 期间冻结
- [x] NEG-4 Graphiti 是事件存储 → Story 10.8 写 episodic 不替代 wikilink RAG

---

## 风险红线 (R1-R8)

| # | 风险 | Story 缓解 | 用户红线 |
|---|---|---|---|
| R1 | BlockType Enum 30+ Pydantic 失败 | 10.6 + 10.7 分批加 (Day 7 加 1 + Day 8 加 2) | 不破 quiz 渲染 |
| R2 | Canvas Docker 起不来 | 10.3 vault 挂载用 host.docker.internal | 双系统独立启停 |
| R3 | DeepTutor 上游 breaking | 10.1 mvp-baseline tag + 不 pull upstream | fork 稳定 |
| R4 | wikilink_graph_service 期望 obsidiantools 布局 | 10.3 建假 .obsidian/ 或放宽检查 | vault 结构不改 |
| R5 | CORS 阻塞 | ✅ Day 0 已加 :3782 :8001 :5173 | 实时跨域 |
| R6 | ReactFlow 性能 1000+ 节点 | 10.5 2-hop 限制 + 虚拟滚动 | 不卡 UI |
| R7 | CalloutBlock 不走 MarkdownRenderer | 10.3 1 行修 | callout 内 wikilink 要生效 |
| R8 | UX-3 跨时间错误重现学术 near-zero | 10.6 降级 P2 | 不强求最高目标 |

---

## 当前状态（2026-05-06 末）

| Story | Status | Evidence |
|---|---|---|
| 10.1 | ✅ done | fork URL + baseline tag + double services healthy |
| 10.2 | ✅ done | fork commit `oinani0721/DeepTutor@23a2853` + tag `mvp-day-1-patches` |
| 10.3 | ready-for-dev | Day 2 待跑 |
| 10.4 | ready-for-dev | Day 3-4 待跑 |
| 10.5 | ready-for-dev | Day 5-6 待跑 |
| 10.6 | ready-for-dev | Day 7 待跑 |
| 10.7 | ready-for-dev | Day 8 待跑 |
| 10.8 | ready-for-dev | Day 9 待跑 |
| 10.9 | ready-for-dev | Day 10 待跑 |

---

## 用户批注区

> [!question]+ 你对 D17 整体决策的批注
>
> Day 10 跑完 5 验证 + 决策矩阵后回填这里。
> 任何路径调整 / 优先级变化 / 痛点补充都批到这里。

---

## 关联文档

- **决策报告**: `_bmad-output/research/round-22-deeptutor-fork-mvp-2026-05-06.md`
- **Deep Explore**: `_bmad-output/research/round-22-deeptutor-deep-explore-2026-05-06.md`
- **Epic 总览**: `_bmad-output/implementation-artifacts/epic-10/_README.md`
- **Stories**: `_bmad-output/implementation-artifacts/epic-10/10-{1..9}-*.md`
- **UAT 验收单**: `_bmad-output/验收单/Story-10.{1..9}-*.md`
- **CURRENT_TASK**: `CURRENT_TASK.md`
- **memory**: `decision_round22_fork_mvp.md`

---

*D17 决策已落地为 Epic-10。等 Day 10 UAT 完成后用户回填批注 + 路径选择 (A/B/C)。*

---

## D17 二轮追加（2026-05-07 — Day 1 完成后 Round-22 6 报告深度调研）

> **追加源**: 用户 Day 1 完成后批注 + 5 并行 Agent 深度调研
> - `round-22-day2-vault-access-design-2026-05-06.md`（Day 2 vault Phase A/B 设计）
> - `round-22-chat-vs-tutorbot-usage-comparison-2026-05-06.md`（Chat 6 vs TutorBot 7 决策矩阵）
> - `round-22-cli-sdk-book-engine-deep-explore-2026-05-07.md`（CLI/SDK 深度探索 + Guided Learning 删除发现）
> - `round-22-desktop-app-rendering-deep-explore-2026-05-07.md`（Math/Visualize server-side 验证 + Tauri vs Electron 决策）

### 6 个 Round-22 期间新发现（Day 0-7 演化）

#### F1 ⛔ Guided Learning v1.2.0 已删除（Book Engine 是继任者）

**调研发现（CLI/SDK 报告 §五）**: DeepTutor v1.2.0 Release Notes 明确删除 Guided Learning 模块（~5300 行）。

**影响**:
- 原 D17 决策"5 大核心嵌入 Guided Learning"应改为"嵌入 Book Engine"
- Story 10.4 路径 B 的 `POST /books/confirm-spine` API 是 Book Engine 入口
- 所有"AI 推断图谱"语义 = Book Engine 的 Spine 推断（Path Y 绕过它）

#### F2 Math Animator + Visualize 渲染 100% 在 server-side

**调研发现（Desktop 报告 §一/§六）**: 5 个并行 Agent 验证:
- Math Animator: Manim+ffmpeg 服务端生成 MP4
- Visualize: 5 render_mode 服务端输出代码字符串，**客户端渲染**

**影响**:
- CLI/SDK 用户拿到的是文件路径或代码，**不能直接"看到"动画/图表**
- M4 映射对（13 映射中最强）必保留可视化能力 → Story 10.5 必须内嵌渲染
- Day 11+ 桌面化（Epic-11）必备：WebView 内嵌视频/图表

#### F3 桌面化 100% 可行（Tauri vs Electron 决策）

**调研发现（Desktop 报告 §四）**:
- **Electron + AnythingLLM 模式**：59.7k stars 商用先例 + macOS notarization 成熟
- **Tauri 2.0 备选**：包小（5-10MB）但 Rust 学习曲线 + macOS 签名坑

**最终选 Electron**:
- 包大可接受（VS Code 200+ MB 参照）
- 工期 1-2 周框架 + 4 周跨平台发布
- Next.js standalone 零改动复用

**影响**:
- Day 11+ 拆分为 **Epic-11**（D18 锚定，本批注为 D17 主体不变）
- Epic-11 4 stories: 11.1 Electron 框架 / 11.2 IPC Bridge / 11.3 Vault 渲染 / 11.4 跨平台发布

#### F4 Day 2 Vault 工作量翻倍（4h → 1.5-2 day）

**调研发现（Day 2 报告 §四）**:
- Phase A（2-3h）: 0 改动 + manager.py:438 `restrict_to_workspace=False` 默认开沙箱
- Phase B（6-9h，可选）: VaultMonitor daemon (~120 行) + DocumentAdder vault_mode + file lock + atomic rename

**影响**:
- Story 10.3 spec estimate_hours=4 严重低估
- 推荐拆为 10.3a（Phase A 必修）+ 10.3b（Phase B 推荐）

#### F5 Chat 6 capability + TutorBot 7 features 双轨并存

**调研发现（Chat vs TutorBot 报告 §三）**:
- Chat Workspace（6 capability）: Chat / Deep Solve / Quiz Generation / Deep Research / Math Animator / Visualize
- TutorBot（7 features）: Soul Templates / Independent Workspace / Proactive Heartbeat / Full Tool Access / Skill Learning / Multi-Channel / Team & Sub-Agents
- **5 学习场景决策矩阵**: Chat 适合"瞬时问题"，TutorBot 适合"长程伴学"

**影响**:
- Canvas 5 大核心**通过双轨触达**: 白板讲题（Chat Math Animator）+ 长程复习（TutorBot 8 通道推送）
- Story 10.3/10.5/10.8 加 TutorBot 优先注解（spec 中"推荐路径"段已落地）
- 不需新增 Story，仅文档批注

#### F6 ReactFlow 选定（CLI/SDK 报告 §四 + Day 0 实测）

**调研验证**: DeepTutor fork 已装 Cytoscape v3.33.1 但**未用**（Agent 2.1 发现）。
- ReactFlow 已在 Canvas 验证（cp Canvas 代码节省时间）
- ReactFlow React 一等公民 + edge 自定义渲染（depends_on 实线 / extends 虚线）

**影响**:
- Story 10.5 Whiteboard 选 ReactFlow（Day 5-6 工作量 18-24h 不变）
- Cytoscape 闲置，Production 阶段再决定

---

### 风险更新（基于新发现）

| # | 新风险 | 触发 | 缓解 |
|---|---|---|---|
| **R9** | Math Animator MP4 生成超时（30s+ Manim 渲染） | Day 5-6 + Day 9 UAT | FastAPI subprocess 后台任务 + 进度条 + Day 6 verify Manim docker image 已含 |
| **R10** | Visualize 5 render_mode 浏览器兼容性 | Day 5-6 | 优先 SVG（最广兼容），Chart.js/Mermaid 用 CDN fallback |
| **R11** | Path A 后桌面化 macOS notarization 流程卡 | Day 22 (Epic-11.4) | Day 19 提前申请 Apple Developer 账号 + notarytool 测试 |

---

### 关联 Epic-11（D18 锚定）

D17 决定**Day 0-10 MVP**（Epic-10）。**Day 11+ 桌面化**由 D18 决策批注独立锚定。

D17 ↔ D18 关系:
- D17 = Round-22 主决策（fork + 5 核心嵌入）
- D18 = Round-22 子决策（Path A 后桌面化路线）
- 两者通过 `related_round: round-22` 链接，但 Epic-11 启动条件是 Epic-10 Day 10 UAT 全 PASS

详见 `_bmad-output/决策批注/D18-desktop-app-electron-2026-05-07.md`。

---

*D17 二轮追加日期: 2026-05-07 — 6 报告深度调研收敛 + Epic-11 路线确立*
