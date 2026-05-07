---
decision_ids: ["D19"]
status: "annotated"
date: "2026-05-07"
related_round: "round-22"
related_prd: "_bmad-output/research/round-22-deeptutor-fork-mvp-2026-05-06.md"
related_research:
  - "_bmad-output/research/round-22-desktop-db-decision-deep-research-2026-05-07.md"
  - "_bmad-output/research/round-22-chatgpt-dr-prompt-desktop-db-decision-2026-05-07.md"
related_epic: "epic-11"
related_stories: ["11.1", "11.2", "11.3", "11.4"]
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
user_decision: "保留 C+ Docker Compose Supervisor 作为 Epic-11 主交付路径；图存储抽象层重构 + Kuzu spike 单独立项不进 Epic-11"
upstream_decisions: ["D17 (Round-22 fork)", "D18 (Desktop app Electron)"]
---

# D19: Round-22 Desktop App 数据库栈决策（Epic-11 锁定 C+ + Kuzu 后续 spike）

> **Plan ID**: EPIC1-BMAD-DEV-ASSESS-2026-04-17
> **Round**: 22（DR 升级第 1 次，effort=max，仅 GitHub 连接器）
> **决策日期**: 2026-05-07
> **Epic 落地**: epic-11（Story 11.1-11.4 不需修订，仅加 Dev Notes 引用）
> **关联决策**: D17（fork MVP）+ D18（Desktop app Electron）

---

## 问题回顾：能否在不保留 Docker Desktop 前提下交付 Epic-11？

**原问题**（用户 2026-05-07 ChatGPT DR 升级触发）:
> "数据库桌面化决策：Story 11.2 已锁定 'C+ 方案 Docker compose 不嵌 Neo4j'，但需要用户机器装 Docker Desktop（600MB），如要避开 Docker 需重新评估（Agent 5 提的 SQLite + Kuzu 替代方案）— 这是 Epic 11 启动前需要用户拍板的决策点"

**DR 升级触发条件**（BMAD scoped CLAUDE.md，3 条全命中）:
1. ✅ Explore agent 找不到社区先例（5 内部 agent 后仍无定论）
2. ✅ 两个对立技术方案各有论据，无明显胜方（Docker 简单但门槛 / Embedded 用户体验好但迁移成本未知）
3. ✅ 决策影响后续 5+ Story（Epic-11.1 ~ 11.4 + Epic-10 后续路径）

**ChatGPT Deep Research (effort=max) 答案**:
**否，在 5-10 人日 + 500MB 包 + 五大核心保真 + 不重写 Neo4j/Cypher/Graphiti 的硬约束下，不能去掉 Docker Desktop。**

---

## 核心决策（D19）：C+ 主路径 + 图存储抽象层 + Kuzu 后续 spike

### D19.1 主决策（Epic-11 交付路径）

**决策**: 保留 **B5 / C+ 方案**（Electron + Docker Compose Supervisor）作为 Epic-11 的主交付路径。

**与 Story 11.2 现有 spec 关系**: **不需修订核心设计**，仅加 Dev Notes 引用 DR 报告 + 本批注。

**理由（DR 4 条独立得出 + 与 Epic-11 spec 高度 corroborate）**:

1. **代码耦合事实**（DR 实读证据）:
   - `episode_worker.py` 直接构造 `Graphiti(neo4j_uri, neo4j_user, neo4j_password)` — Graphiti 客户端硬编码 Neo4j 风格
   - `neo4j_client.py` 用 `AsyncGraphDatabase.driver(...)` Bolt 直连
   - `memory_service.py` 自动创建 `episode_content` 全文索引（Neo4j DDL）
   - `exam_service.py` 4 段显式 Cypher（exam session 持久化）
   - **共计显式 Cypher 模板下界 10+ 段**（DR 实读已截断保守值）
   - 没有 driver 抽象层，未做 GraphStore 接口

2. **Graphiti 库虽支持 Kuzu/FalkorDB 但仓库代码停留在 Neo4j 风格**:
   - `graphiti-core` 0.28+ PyPI 提供 `kuzu` / `falkordb` extras
   - 我们仓库代码未做 driver 抽象，迁移不是"换 pip extra"级别

3. **B4 内置 Neo4j JVM 服务进程不满足工期 + 包大小**:
   - Neo4j Desktop 含 DBMS/JDK 运行需求
   - Electron 既定 ~150MB + 独立 Python backend + Neo4j/JDK ⇒ 高概率超 500MB
   - PyInstaller onefile 启动时解包慢于 onedir
   - 5-10 人日 + 跨平台签名公证基本不可行

4. **B5/C+ 与既定 spec 自洽**:
   - DR 估算 8-12 人日 = Epic-11 既定 ~80h ✓
   - Story 11.2 已写 Docker Compose Supervisor 设计（AC #1 + Task 1）
   - Story 11.4 已写 entitlements.mac.plist + notarize（AC #6 + Task 1.5）

**信心度**: ⭐⭐⭐⭐⭐（内部 5 agent + 外部 ChatGPT DR 独立 corroborate）

### D19.2 次决策（不进 Epic-11，单独 spike 立项）

**决策**: 把"去 Docker Desktop"从 Epic-11 移出，作为后续 spike 立项。

**Spike 三阶段路线图**（来自 DR 推荐，4-6 + 5-8 = 9-14 人日）:

- **阶段二**：图访问抽象层小重构（4-6 人日，**不换库**）
  - 抽 episode 写入/检索接口
  - 抽 exam session 图持久化接口
  - 抽 learning relationship / review suggestions 接口
  - 升格 `cypher_helpers.py` 的 group_id 语义为数据库无关的过滤契约
  - **目标**：建立 GraphStore / EpisodeStore 适配层边界，统一测试夹具，定义最小兼容契约

- **阶段三**：Kuzu spike（5-8 人日，**只 POC 不承诺上线**）
  - 验证 Graphiti `KuzuDriver` 能否替代当前 `Graphiti(neo4j_uri, ...)` 初始化
  - 验证 review/history/exam 这几段查询能否在 Kuzu 方言下维持语义一致
  - 验证启动体积与首启速度是否明显优于"内置 Neo4j 服务进程"
  - **退出条件**：3 项里 2 项过不了 → 停止 no-Docker 正式化

**Spike 提案文档**: `_bmad-output/research/spike-graph-store-abstraction-roadmap-2026-05-07.md`（本批注同步建立）

**触发条件**: Epic-11 Day 22 完整发布后 + 用户主动需求"减少安装门槛" → 启动 spike 阶段二

### D19.3 关键修正（DR 报告对 prompt 的修正）

> **修正源**: ChatGPT DR 实读后纠错。

**原 prompt 错误**: `round-22-chatgpt-dr-prompt-desktop-db-decision-2026-05-07.md` Tier 1 清单将 `wikilink_graph_service.py` 列为"Neo4j 锁定证据文件"。

**实际现状**: `wikilink_graph_service.py` **完全不依赖 Neo4j**，使用 `obsidiantools` 解析 vault + `networkx.DiGraph()` 构建有向图，所有 2-hop 邻居/路径/提及图都在内存图上计算。

**影响**:
- 多 vault wikilink 链路天然桌面友好，**不阻塞**未来去 Docker
- 阶段二抽象层重构应优先迁出 **Memory / Graphiti / Exam 链**，而不是优先动 wikilink
- 若 spike 失败回退保守路径，wikilink 部分可独立迁出（无 Cypher 依赖）

**未发现 APOC.* 运行期调用**: APOC 仅容器层启用（`NEO4J_PLUGINS=["apoc"]`），目标文件中无显式 `CALL apoc.*`。这降低了 Kuzu 迁移的语义复杂度。

---

## 落地 spec 修订清单（最小变更）

### Story 11.2（IPC Bridge + FastAPI subprocess）

**修订动作**: Dev Notes 段加 D19 + DR 引用，C+ 核心设计不变。

**追加内容（不重写 AC / Task）**:
> ### D19 决策锁定（2026-05-07 DR 升级后）
>
> ChatGPT Deep Research (effort=max) 实读本仓库 Tier 1-5 文件后独立得出与本 spec 一致的结论：保留 C+ Docker Compose Supervisor 是 5-10 人日预算下的最优路径。
>
> - **不需修订 AC / Task**: AC #1 + Task 1 的 Docker Compose Supervisor 设计 = DR 主决策
> - **关键修正记录**: `wikilink_graph_service.py` 不依赖 Neo4j（obsidiantools + NetworkX 内存图），future no-Docker spike 应优先迁 Memory/Graphiti/Exam，而不是 wikilink
> - **后续 spike**: 图访问抽象层 + Kuzu spike 单独立项，不进 Epic-11
> - **关联文档**: `决策批注/D19-desktop-db-stack-2026-05-07.md` + `research/round-22-desktop-db-decision-deep-research-2026-05-07.md`

### sprint-status.yaml

**修订动作**: epic-11 注释段加 D19 + DR 报告路径引用。

**追加内容**:
> 关联决策批注: 决策批注/D17, D18, **D19**（D19 锁定 C+ 主路径 + Kuzu 后续 spike）
> 关联 DR 报告: research/round-22-desktop-db-decision-deep-research-2026-05-07.md

### Spike 提案（不进 Epic-11，仅 backlog candidate）

**新建文件**: `_bmad-output/research/spike-graph-store-abstraction-roadmap-2026-05-07.md`

**内容**: 阶段二（4-6 人日）+ 阶段三（5-8 人日）roadmap + 退出条件 + 触发条件。

---

## 与 D17/D18 决策链衔接

| Decision ID | 锚定 | 与 D19 关系 |
|---|---|---|
| **D17** | Round-22 fork MVP（Epic-10 起点） | ✅ D19 不挑战 D17，仅延续到 Epic-11 数据库层 |
| **D18** | Desktop App Electron + AnythingLLM 模式 | ✅ D19 在 D18 框架内细化数据库栈选择，AnythingLLM 仅工程实践参考（不抄数据流，与 D18 二轮澄清一致） |
| **D19** | Desktop DB Stack — C+ 主路径 + Kuzu 后续 spike | ✅ 本批注锁定 |

---

## 调研痕迹（DR 升级合规）

### Internal Explore agent 调研轮次（5 个并行 agent，2026-05-07 上午）

1. Agent 1: Epic-11 spec 现状审计 → 发现 4 个 CRITICAL 缺口（Recent vaults / 多 vault / macOS Sandbox / D18 误读）
2. Agent 2: Claude/Cursor/VSCode/Obsidian/AnythingLLM folder picker 对比 → 推荐混合 Obsidian + Cursor 模式
3. Agent 3: Electron + macOS Sandbox + chokidar → security-scoped bookmarks 必需
4. Agent 4: AnythingLLM Desktop 实情 → **重大发现**：HTTP upload-and-embed，与 NEG-2 完全冲突 → D18 语义需澄清
5. Agent 5: Electron + Python FastAPI subprocess 集成 → ~80-150 MB PyInstaller bundling，HTTP localhost 通信最稳

### External ChatGPT Deep Research（2026-05-07 下午，effort=max）

- **Prompt**: `_bmad-output/research/round-22-chatgpt-dr-prompt-desktop-db-decision-2026-05-07.md`
- **报告**: `_bmad-output/research/round-22-desktop-db-decision-deep-research-2026-05-07.md`
- **连接器**: GitHub only（按 prompt 约束）
- **方法**: Tier 1-5 文件实读 + 官方文档（Graphiti / Neo4j / Kuzu / Memgraph / Electron / Apple）
- **结论**: 与 internal 5 agent 高度 corroborate，主决策 C+ 不变，新增 Kuzu spike 路径

### 决策追溯锚点

未来若有人质疑 "为什么 Epic-11 还需要 Docker Desktop？"，直接 ref 本批注 + DR 报告即可，**不需要再开调研**。

---

## 待评估的边界条件（次决策触发条件）

如下 4 个条件**任一**满足，触发 D19 重新评估：

1. **用户主动需求降低安装门槛**: 用户在 Epic-11 发布后批注 "Docker 太重了，能不能去掉？"
2. **Graphiti 上游做出 driver 抽象重构**: `graphiti-core` 1.0+ 提供完整 GraphStore 接口，迁移成本断崖式下降
3. **Kuzu 0.x → 1.0 GA**: Kuzu 标记 production-ready + 自定义索引/约束完整支持
4. **Docker Desktop 商业许可改变**: Docker Desktop 对个人/教育用户的免费政策收紧（2026 年监控）

**重新评估流程**: 启动 spike 阶段二（图访问抽象层重构）→ 通过则进入阶段三（Kuzu POC）→ 任一阶段失败回退保守路径。

---

*D19 锁定。下次 Epic-11 启动前用户最终确认。*
