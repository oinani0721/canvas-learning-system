# Canvas Learning System - Deep Research 分析报告

> **生成日期**: 2026-04-01 | **分析范围**: 全项目（前端 + 后端 + 遗留代码 + 基础设施）

---

## 一、项目概览

Canvas Learning System 是一款基于 Tauri 2 的 AI 辅助学习桌面应用，融合知识画布、AI 对话教学、间隔重复复习和自动化考试四大核心功能。项目代码量约 **36 万行**，横跨 Python 后端（FastAPI）、TypeScript 前端（React 19）和 Node.js Sidecar（Claude Agent SDK）三个运行时。

### 技术栈一览

| 层 | 技术 | 版本 |
|---|---|---|
| 桌面壳 | Tauri 2 (Rust) | 2.x |
| 前端 | React 19 + TypeScript 5.8 + ReactFlow 12 | — |
| 状态管理 | Zustand 5 + Dexie (IndexedDB) | — |
| AI 引擎 | Claude Agent SDK (Sidecar) / API Key 降级 | 0.2.79 |
| 后端 | FastAPI + Pydantic v2 + LangGraph | — |
| 图数据库 | Neo4j 5.26 Community + APOC | — |
| 向量数据库 | LanceDB (bge-m3, 1024d) | — |
| 时序知识图谱 | Graphiti-core 0.28.2+ | Phase 2/5 |
| 本地 LLM | Ollama (Qwen3 8B + bge-m3) | — |
| 云 AI | LiteLLM → Gemini / OpenAI / Anthropic | — |
| 基础设施 | Docker Compose (8 服务) | v3.8 |

---

## 二、代码规模与结构

### 2.1 代码量分布

| 模块 | 文件数 | 代码行数 | 说明 |
|---|---|---|---|
| frontend/src/ | 55 | ~15,000 | Tauri React 前端 |
| frontend/sidecar/ | 382 | ~77,000 | Agent SDK + node_modules |
| backend/app/ | 178 | ~83,000 | FastAPI 后端核心 |
| src/ (legacy) | 310 | ~186,000 | Agentic RAG + FSRS + Rollback |
| **合计** | **925** | **~361,000** | — |

### 2.2 前端架构

前端采用 **30 个 React 组件 + 4 个 Zustand Store + 12 个 Service** 的架构：

- **4 个 Store** 总计约 1,868 行（canvas 328 / chat 1,125 / exam 234 / mastery 181），chat-store 是最大的单体状态管理文件
- **12 个 Service** 封装了 API 通信、引擎管理、同步、备份、崩溃恢复等横切关注点
- **Outbox 同步模式**：所有 CUD 操作先写 Dexie (IndexedDB)，再由 SyncEngine 异步批量同步到后端，确保离线可用性

**关键文件体量**（前端活跃代码）：

| 文件 | 行数 | 职责 |
|---|---|---|
| App.tsx | 1,220 | 应用入口 + 视图路由 |
| Settings.tsx | 1,137 | 全局设置面板 |
| chat-store.ts | 1,125 | 对话状态管理（最复杂） |
| canvas-store.ts | 328 | 画布 CRUD |

### 2.3 后端架构

后端采用 **Service-Oriented FastAPI** 模式：

- **~155 个 REST 端点**，分布在 17 个路由模块
- **15 个 MCP 工具**，通过 `/mcp` 端点暴露给 Sidecar
- **2 个 WebSocket 端点**（mastery 实时推送 + 智能并行进度）
- **38 个 Service 类**封装业务逻辑，通过依赖注入组合

**后端 Top 5 最大文件**：

| 文件 | 行数 | 职责 |
|---|---|---|
| agent_service.py | 5,713 | LLM 调用逻辑总枢 |
| verification_service.py | 2,905 | 考试验证 + 评分 |
| review_service.py | 2,269 | FSRS 复习调度 |
| neo4j_client.py | 2,021 | 图数据库客户端 |
| agents.py (endpoints) | 2,103 | Agent API 路由 |

### 2.4 遗留模块 (src/)

遗留代码高达 186,000 行，主要包含：

- **agentic_rag/** (19,220 行)：6 路并行检索的 LangGraph StateGraph 管道，是代码库最成熟的模块
- **memory/** (1,335 行)：FSRS 间隔重复算法
- **rollback/** (2,613 行)：回滚引擎
- **canvas_utils.py** (36,779 行)：核心工具函数，体量异常巨大，可能需要拆分重构

---

## 三、MVP 14 项完成度评估

根据 `_decisions/mvp-plan.md` 及用户批注，14 项 MVP 需求当前状态如下：

| # | 功能 | 状态 | 阻塞项 | 用户关切 |
|---|---|---|---|---|
| 1 | 原白板前端设计 | ✅ 已实现 | — | 浅色 UI 未切换到 Catppuccin Mocha 深色主题；颜色仅为个人标记 |
| 2 | 检验白板前端设计 | ✅ 已实现 | — | CognitiveLoadTimer 需移除（已决策抛弃）；考后统计需去掉计时 |
| 3 | 检验白板考察提示词 | 🔗 需验证 | 前后端管道未验证 | 题目质量有待用户试用检验 |
| 4 | 节点 AI 对话 | ⚠️ 需验证 | Windows Sidecar spawn | API Key 降级是否走 CLI Proxy |
| 5 | Tips/Edge/错误写入+检索 | 🔗 需验证 | 端到端未测试 | record_learning_memory 未按 Graphiti 设计；hook 兜底机制缺失 |
| 6 | 检验白板新发现写入 | 🔗 需验证 | — | 拉出节点机制需与原白板对话一致 |
| 7 | Dashboard | ⚠️ 不完整 | Pencil 设计待补 | 缺少 LLM 管理面板；节点 3 层 Profile 跳转功能缺失 |
| 8 | Edge 对话 2 重策略 | ✅ 已实现 | — | 对话蒸馏是 edge 还是节点上下文需确立 |
| 9 | Agentic RAG L1+L2 | ✅ 已实现 | Docker Ollama 模型 | RAG 仍不能正常使用；不同白板需不同索引路径 |
| 10 | 笔记精准检索返回 | ⚠️ 数据未流入 | bge-m3 模型 + vault 索引 | 索引"成功"但实际无笔记片段返回 |
| 11 | 基础 Hybrid Search | ✅ 已实现 | — | — |
| 12 | Claude Code 迁移 | ⚠️ 需验证 | 同 #4 | Claudian 命令注册、session 管理、上下文压缩未解决 |
| 13 | /命令调用提示词模板 | ✅ 已实现 | — | 未完全迁移 Claude Code 所有命令 |
| 14 | 对话拉出节点 | ✅ 已实现 | — | — |

### 完成度统计

- **✅ 已实现**: 7 项 (#1, #2, #8, #9, #11, #13, #14)
- **⚠️/🔗 需验证或修复**: 6 项 (#3, #4, #5, #6, #7, #10)
- **⛔ 阻塞**: 1 项 (Agent 记忆系统 — Graphiti Phase 2 已完成，Phase 4-5 待做)

**MVP 完成度约 50%** — 代码大部分已写完，但端到端管道验证和数据流激活是主要瓶颈。

---

## 四、Graphiti 集成状态（核心关切）

这是项目最关键的技术债之一。经过深度代码审计，现状如下：

### 4.1 真实集成（已完成）

| 组件 | 文件 | 状态 |
|---|---|---|
| GraphitiEpisodeWorker | episode_worker.py (446 行) | ✅ 真实 `graphiti_core.Graphiti` 实例 |
| GeminiEmbedder + GeminiClient | episode_worker.py | ✅ 真实 Gemini 调用 |
| asyncio.Queue 队列 | episode_worker.py | ✅ maxsize=100 异步处理 |
| search_memories Tier 1 | memory_service.py:1230 | ✅ 调用 `worker._graphiti.search()` |
| record_knowledge_entity | memory_service.py:1114 | ✅ 写入 Neo4j + 入队 Graphiti |
| Lifespan 集成 | main.py:259-328 | ✅ 启动初始化 + 优雅关闭 |

### 4.2 已清理的假代码

- ✅ G-FAKE-001 批量重命名完成（17 项核心类从 Graphiti→Neo4j 前缀）
- ✅ graphiti_bridge_service.py 已删除
- ✅ JSON dual-write 已移除
- ✅ 死代码调用链已清理

### 4.3 迁移进度

| Phase | 状态 | 内容 |
|---|---|---|
| Phase 0 | ✅ 完成 | Neo4j 7691 配置、GOOGLE_API_KEY |
| Phase 1 | ✅ 完成 | 死代码移除 |
| Phase 2 | ✅ 完成 | EpisodeWorker 构建 + 集成 |
| Phase 3 | ✅ 完成 | record 系列函数入队到真实 Worker |
| Phase 4 | ⏳ 待做 | 残留命名清理（API 模型名、config 属性） |
| Phase 5 | ⏳ 待做 | search_memories 专用 Graphiti 索引优化 |

### 4.4 搜索架构（三层降级）

```
search_memories(query)
├── Tier 1: graphiti_core.search() [真实语义搜索, 2s 超时]
├── Tier 2: Neo4j fulltext index [全文检索降级]
└── Tier 3: In-memory cache [内存子串匹配兜底]
```

**结论**: Graphiti 的核心读写管道已经是真实的了，但受 Gemini 免费额度限制（10 RPM / 250 RPD），生产环境的吞吐量可能不足。

---

## 五、技术债清单

### 5.1 已知问题追踪 (known-gotchas.md)

| 分类 | 总计 | 已修复 | 保留/延后 | 待修 |
|---|---|---|---|---|
| G-FAKE (假命名) | 5 | 5 | 0 | 0 |
| G-PIPE (管道断裂) | 7 | 5 | 2 | 0 |
| G-TYPE (类型不匹配) | 2 | 2 | 0 | 0 |
| G-ASYNC (异步/竞态) | 2 | 2 | 0 | 0 |
| G-API (合同违规) | 2 | 2 | 0 | 0 |
| G-PERF (性能) | 2 | 1 | 1 | 0 |
| G-SILENT (静默失败) | 2 | 1 | 0 | 1 |
| G-PARAM (参数Bug) | 3 | 3 | 0 | 0 |
| **合计** | **25** | **21** | **3** | **1** |

**治理效果显著**：25 个已知问题中 21 个已修复（84%），仅剩 1 个待修（G-SILENT-001: Review Schedule enrichment_available 标记）。

### 5.2 仍然存在的结构性问题

1. **canvas_utils.py 36,779 行** — 遗留模块中的超级文件，严重违反单一职责原则，需要拆分
2. **BehaviorTracker 331 行完整实现但无调用方** (G-PIPE-002) — 作为 future feature 保留
3. **Phase 3 Agent Graph 660 行被有意禁用** (G-PIPE-004) — 待生产验证后启用
4. **Windows IPC 性能** (G-PERF-002) — 10MB 数据在 Windows 上 200ms vs macOS 5ms，已通过 <100KB 约束缓解
5. **TODO 注释 51 处** — 分布在 22 个文件中，主要涉及多用户支持、RAG 增强、真实数据库连接

### 5.3 前端特有问题

- **浅色/深色主题不一致**：Catppuccin Mocha 深色主题只在局部组件生效，全局未切换
- **CognitiveLoadTimer 组件需移除**：已决策抛弃但代码仍存在
- **chat-store.ts 1,125 行**：作为单文件管理所有对话逻辑，复杂度较高
- **Session 管理不清晰**：Claude SDK session 上下文与节点对话历史的交互设计需要明确

---

## 六、架构优势与风险

### 6.1 架构优势

1. **Outbox 同步模式** — 所有前端数据变更先写 IndexedDB 再异步同步，保证离线可用性和数据一致性
2. **pipeline_token 链式验证** — MCP 工具间强制步骤顺序（generate_question → score_answer → update_fsrs），防止 Agent 跳步
3. **6 路并行 RAG 管道** — Agentic RAG 是代码库最成熟的模块，融合 LanceDB 语义搜索、Neo4j 图搜索、Graphiti 时序搜索等
4. **5 层安全架构** — 从后端算法权威到 Prompt 注入检测到 pipeline_token 验证，安全设计完整
5. **三层搜索降级** — search_memories 从 Graphiti 语义搜索 → Neo4j 全文 → 内存兜底，保证可用性
6. **事件驱动架构** — EventBus 连接 FSRS、Graphiti、RAG 子系统，松耦合

### 6.2 架构风险

| 风险 | 严重度 | 说明 |
|---|---|---|
| Gemini 免费额度瓶颈 | 🔴 高 | 10 RPM / 250 RPD 限制 Graphiti episode 处理吞吐 |
| Windows Sidecar 稳定性 | 🔴 高 | Agent SDK Node.js 进程 spawn 在 Windows 上未验证 |
| RAG 数据流未激活 | 🟡 中 | vault 笔记索引显示成功但实际无数据返回 |
| 遗留代码体量大 | 🟡 中 | src/ 186K 行中大量未被活跃使用的代码 |
| 前端 Session 管理 | 🟡 中 | Claude SDK session 与节点对话历史的交互模型不明确 |
| 上下文压缩缺失 | 🟡 中 | Claude SDK 已支持 1M 上下文但未设计压缩策略 |
| 单体遗留文件 | 🟠 低 | canvas_utils.py 36K 行需要拆分 |

---

## 七、决策执行追踪

项目已记录 **50+ 条决策**，覆盖架构、UI、技术栈、安全、工作流等方面。关键决策执行状态：

### 已确认且已实施

- DE-1~DE-5 前端重构（Tauri+React+ReactFlow+shadcn/ui）
- Agent SDK Sidecar 架构（取代 Mode D）
- 10 条开发纪律（DD-01~DD-10）
- 6 Epic 结构（覆盖 96 FR）
- Neo4j 7691 专用学习数据
- Gemini 全家桶（LLM+Embedder+Reranker）

### 已确认但待验证 (Review PENDING)

- GDR-P0-1~P0-3: 事件传输、工具调用 UI、Observer 触发
- Agent SDK Sidecar Windows spawn 稳定性
- OBS-LINK Obsidian 跳转方案
- DE-4 Docker Shell 管理

### 关键用户反馈（未完全解决）

1. **前端 UI 与设计稿差距大** — 浅色 UI 问题，Catppuccin Mocha 未全局生效
2. **节点 3 层 Profile 跳转** — 错误/疑惑→跳转到当时的对话/考试白板（部分缺失）
3. **疑问节点创建** — 用户手动决定创建（非 AI 自动），但 AI 需归类到正确节点
4. **对话蒸馏定义** — edge 蒸馏 vs 节点上下文蒸馏需确立
5. **Session 管理** — Claude SDK session 上下文 + 节点对话历史的管理界面
6. **Dashboard LLM 管理面板** — 已决策放 Phase 4

---

## 八、依赖与基础设施

### 8.1 依赖规模

| 环境 | 依赖数 |
|---|---|
| 前端 (package.json) | 35 (16 runtime + 19 dev) |
| Sidecar | 1 (@anthropic-ai/claude-agent-sdk) |
| 后端 (requirements.txt) | 158 |

### 8.2 Docker 服务

Docker Compose 定义了 8 个服务：Neo4j (生产)、Neo4j (测试)、FastAPI 后端、LanceDB、Ollama、Claude Dev、CLIProxyAPI 网络、Canvas 网络。

### 8.3 测试基础设施

- **后端**: pytest 配置完整（含 BDD、contract、integration、unit、slow markers）
- **前端**: vitest + @testing-library/react + jsdom
- **pyproject.toml**: 含 Schemathesis (API 模糊测试) + Hypothesis (属性测试)

---

## 九、综合建议

### P0: 立即行动（解除阻塞）

1. **验证 Sidecar Windows spawn** — 这是 #4 和 #12 的共同阻塞项，直接影响 AI 对话核心功能
2. **激活 vault 笔记索引** — 配置 CANVAS_BASE_PATH → 触发 POST /api/v1/canvas-meta/index/vault → 验证搜索返回
3. **Gemini 额度升级** — 免费额度 10 RPM / 250 RPD 严重限制 Graphiti 写入速度，建议升级或使用 Claude Code 的 API

### P1: 端到端管道验证（1-2 天）

4. **启动产品全链路测试** — `docker compose up -d` + `npm run tauri dev` → 逐项验证 14 个 MVP 功能
5. **移除已弃用代码** — CognitiveLoadTimer 组件、ExamSummary 总用时显示
6. **修复 G-SILENT-001** — Review Schedule enrichment_available 标记

### P2: 架构优化（1-2 周）

7. **明确 Session 管理模型** — 定义 Claude SDK session 与节点对话历史的关系，设计上下文压缩策略
8. **全局主题切换** — 将 Catppuccin Mocha 应用到所有组件，或提供浅色/深色切换
9. **canvas_utils.py 拆分** — 36K 行的单体文件需要按职责拆分为多个模块
10. **Graphiti Phase 4-5** — 完成残留命名清理和搜索索引优化

### P3: 长期演进

11. **遗留代码治理** — src/ 186K 行需要评估哪些仍在活跃使用，废弃的应迁移到 _archive
12. **多白板索引隔离** — 不同白板对应不同学科/笔记路径的索引方案
13. **前端 Dashboard 增强** — LLM 管理面板、节点 Profile 跳转（Phase 4 已规划）

---

## 十、总结

Canvas Learning System 是一个**雄心勃勃且技术复杂度极高**的项目，融合了知识图谱、向量检索、间隔重复算法、Agent SDK、RAG 管道等前沿技术。代码量已达 36 万行，后端 155+ API 端点和 15 个 MCP 工具的规模在个人项目中极为少见。

**核心优势**：架构设计成熟（Outbox 同步、pipeline_token 安全链、三层搜索降级），技术债治理有效（25 个 gotchas 中 84% 已修复），决策记录完整（50+ 条）。

**核心风险**：大量功能"代码已写完但端到端未验证"，Sidecar Windows 稳定性未知，Gemini 免费额度限制 Graphiti 吞吐，遗留代码体量巨大。

**建议下一步**：先完成 P0 三项解除阻塞，再用 1-2 天做全链路端到端验证。在代码层面，项目已经具备了 MVP 的骨架，瓶颈在于"让它跑起来"而非"把它写出来"。
