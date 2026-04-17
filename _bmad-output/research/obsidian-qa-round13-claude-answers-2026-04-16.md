---
title: "Obsidian 翻译问答 Round 13 主答复文件（12 轮 QA 发现 → EPIC 1 Story 落地清单）"
date: 2026-04-16
trigger: "用户要求把 Round 7-12 所有批注转化为可执行 Story 落地"
type: "qa-round13-answers"
status: "awaiting-user-audit"
parent_files:
  - "[[obsidian-qa-round12-claude-answers-2026-04-16]]"
related_plan: "OBSIDIAN-QA-ROUND13-2026-04-16"
round: 13
total_sections: 3
round13_character: "12 轮 QA 发现汇总 → EPIC 1 扩展 Story 1.7-1.13 + 实施优先级 + Story 1.1 先行"
key_finding: "EPIC 1 从 6 个 Story 扩展到 13 个（+7 部署/多 vault gap），总工时 40h → ~72h。Story 1.1 Vault Init 无前置依赖，立即可开始"
---

# Obsidian 翻译问答 Round 13 主答复文件

> **阅读指引**: 本文件是 12 轮 QA（Round 7-12）所有发现的 **Story 落地总表**。
>
> 用户要求: "把所有批注转化为相关 Story 来落地实现"。Round 13 将 40+ 可执行发现整理为 EPIC 1 的 13 个 Story + 实施路线图。

---

## R13-Q1 · EPIC 1 完整 Story 清单（1.1-1.13）

### 原有 Story（1.1-1.6，来自 BMAD 规划，40h）

| Story | 标题 | 工时 | 优先级 | 依赖 | 来源 |
|-------|-----|-----|-------|-----|-----|
| **1.1** | Vault 初始化 + Templater 模板 | 8h | **P0** | — | BMAD Epic 1 |
| **1.2** | Wikilink 图构建与邻居发现 | 12h | P0 | 1.1 | BMAD Epic 1 |
| **1.3** | Wikilink MCP 工具注册（8 tools） | 6h | P0 | 1.2 | BMAD Epic 1 |
| **1.4** | Hotkey 绑定配置（6 commands） | 6h | P1 | 1.1 | BMAD Epic 1 |
| **1.5** | Hotkey 冲突检测 | 4h | P2 | 1.4 | BMAD Epic 1 |
| **1.6** | Git 备份 + KG 索引健康检查 | 4h | P2 | 1.1 | BMAD Epic 1 |

### 新增 Story（1.7-1.13，来自 QA Round 7-12，~32h）

| Story | 标题 | 工时 | 优先级 | 依赖 | QA 来源 |
|-------|-----|-----|-------|-----|--------|
| **1.7** | 根 `.env` + Docker Compose 变量化 | 4h | **P0** | — | R10 Gotcha 1 + R11 .env 方案 + R12 [C1] 修正 |
| **1.8** | Vault Switch Runtime API | 6h | **P0** | 1.7 | R12 修正方案（Claudian 自动检测 → `POST /vault/switch`） |
| **1.9** | LanceDB vault_id 命名空间隔离 | 6h | **P0** | 1.8 | R12 [C4] + [N1]（跨 vault 数据污染修复） |
| **1.10** | 健康端点统一 + Plugin 状态指示 | 4h | P1 | 1.7 | R10 Part D + R12 [I1]（3 级 ready/degraded/unavailable） |
| **1.11** | 配置统一 + 漂移防护 | 3h | P1 | 1.7 | R12 [I3]（root .env → backend/.env → Docker env 三源冲突） |
| **1.12** | MCP 基础设施工具 + DEPLOYMENT_TOOLS 权限 | 5h | P1 | 1.8, 1.10 | R10 选项 2 + R12 [C2]+[N2]（check_backend_health + switch_vault） |
| **1.13** | 部署预检清单 + External Network 条件化 | 4h | P2 | 1.7 | R10 6 Gotchas + R12 [I2]+[I4] |

### EPIC 1 总览

| 维度 | 原始 | 扩展后 |
|-----|------|-------|
| Story 数 | 6 | **13** |
| 总工时 | 40h | **~72h** |
| P0 Story | 3（1.1-1.3） | **6**（+1.7, 1.8, 1.9） |
| P1 Story | 1（1.4） | **4**（+1.10, 1.11, 1.12） |
| P2 Story | 2（1.5-1.6） | **3**（+1.13） |

---

## R13-Q2 · Story 依赖图 + 实施路线

### 依赖关系

```
Story 1.1 (Vault Init)     Story 1.7 (根 .env)
    │                           │
    ├──→ 1.2 (Wikilink)        ├──→ 1.8 (Vault Switch API)
    │     └──→ 1.3 (MCP tools) │     └──→ 1.9 (vault_id 隔离)
    │                           │     └──→ 1.12 (MCP infra tools)
    ├──→ 1.4 (Hotkey)          ├──→ 1.10 (Health 统一)
    │     └──→ 1.5 (冲突检测)  ├──→ 1.11 (Config 统一)
    │                           └──→ 1.13 (部署文档)
    └──→ 1.6 (Git+KG Health)
```

**两条独立链**:
- **左链（业务功能）**: 1.1 → 1.2 → 1.3 → 1.4 → 1.5（+ 1.6 独立分支）
- **右链（部署基础设施）**: 1.7 → 1.8 → 1.9（+ 1.10/1.11/1.12/1.13 独立分支）

**关键洞察**: 1.1 和 1.7 **无互相依赖**，可以并行启动。

### 实施路线图（4 Phase）

| Phase | Story | 工时 | 里程碑 |
|-------|-------|-----|-------|
| **Phase 1**（本周） | **1.1** Vault Init + **1.7** 根 .env | 12h | vault 目录就绪 + Docker 可配置 |
| **Phase 2**（下周） | **1.2** Wikilink 图 + **1.8** Vault Switch API | 18h | 笔记图谱可遍历 + 运行时 vault 切换 |
| **Phase 3** | **1.3** MCP tools + **1.9** vault_id + **1.10** Health | 16h | AI 可调工具 + 数据隔离 + 健康监控 |
| **Phase 4** | 1.4-1.6 + 1.11-1.13 | 26h | Hotkey/冲突/备份 + Config/MCP infra/文档 |

### Story 1.1 先行详情（用户确认立即开始）

**Story 1.1: Vault 初始化 + Templater 模板**（8h, P0, 无前置依赖）

交付物:
1. **VaultInitService**（backend）: 创建 vault 目录结构 `raw/` / `wiki/concepts/` / `wiki/canvases/` / `outputs/exam_boards/`
2. **Templater 模板**: `concept.md`（含 frontmatter: relationships[], lastReview, nextReview, reviewLevel）+ `exam-board.md`
3. **Plugin 检测**: 4 必须（Dataview, Templater, QuickAdd, Meta Bind）+ Obsidian Bases 核心
4. **Backend 启动验证**: Neo4j → Ollama → FastAPI → MCP 14 tools 链路检查
5. **Setup Wizard**: `POST /api/v1/system/setup-wizard`
6. **CLAUDE.md 生成**: vault 根目录自动创建 AI 工作说明

**关键决策（已确认）**:
- `relationships[]` frontmatter 替代独立 edge.md（双向链接 + frontmatter 足够）
- FSRS 驱动 `lastReview` / `nextReview` / `reviewLevel`（后端权威，前端只读）
- reviewLevel emoji: ≥0.9 🏆 / 0.7-0.9 🟩 / 0.5-0.7 🟨 / 0.3-0.5 🟧 / <0.3 🔴
- Dashboard: Dataview + QuickAdd + Obsidian Bases + Meta Bind

**验收标准**:
1. 用户在新 vault 目录下运行 setup → 看到完整目录结构
2. 打开 Obsidian → 4 个必须插件检测通过（绿色状态）
3. 用 Templater 创建 concept.md → frontmatter 正确填充
4. Backend health check 链路 → 所有组件 ready

---

## R13-Q3 · QA Round 7-12 发现与 Story 映射总表

### 完整映射（40+ 发现 → 13 Story）

| Round | 发现 | 状态 | 映射 Story |
|-------|-----|-----|----------|
| **R7** | Graphiti 当前离线（Docker 未运行） | 已知 | 1.7（Docker 配置化）|
| **R7** | LanceDB 6 表架构确认 | 已确认 | 1.9（vault_id 隔离）|
| **R8** | Graphiti 4 读 + 4 写触发路径 | 已确认 | 参考资料（不需新 Story）|
| **R8** | 3 层检索架构（Graphiti + LanceDB + Neo4j FTS） | 已确认 | 1.3（MCP tools 暴露检索）|
| **R9** | 保留 Graphiti 做错误检索（用户选 A） | **已批准** | 1.7（确保 Docker Neo4j 启动）|
| **R9** | 数据量 20-50MB / 冷启动 120-150s | 已确认 | 1.10（健康检查超时设计）|
| **R10** | Gotcha 1: Vault 路径硬编码 | 已确认 | **1.7**（根 .env + 变量化）|
| **R10** | Gotcha 2: CORS app://obsidian.md 未测 | 已确认 | 1.13（部署预检清单）|
| **R10** | Gotcha 3: Ollama Mac native only | 已确认 | 1.13（文档化）|
| **R10** | Gotcha 4: NEO4J_PASSWORD 不一致 | 已确认 | **1.11**（配置统一）|
| **R10** | Gotcha 5: cliproxyapi external network | 已确认 | **1.13**（条件化）|
| **R10** | Gotcha 6: Neo4j 非默认端口 7691/7478 | 已确认 | 1.13（文档化）|
| **R10** | Tauri sidecar 不存在（规格幻觉） | 已确认 | 参考资料 |
| **R10** | D1-D5 待决策 | 部分决定 | 分散在 1.8/1.10/1.11/1.12 |
| **R11** | .env + restart 方案 | **已否定** [C1] | 废弃，改为 1.8 Runtime API |
| **R11** | MCP 可行性 4 证据链 | 已确认 | **1.12**（MCP infra tools）|
| **R12** | [C1] restart 不刷新 env | **承认** | **1.8**（Runtime API 替代）|
| **R12** | [C2] MCP auto-allow 安全缺口 | **承认** | **1.12**（DEPLOYMENT_TOOLS tier）|
| **R12** | [C3] Mode 3 需 PoC 验证 | **承认** | 1.13（PoC 代码已给出）|
| **R12** | [C4] 跨 vault 数据污染 | **承认** | **1.9**（vault_id 命名空间）|
| **R12** | [I1] Health vs Availability 混淆 | **承认** | **1.10**（统一 3 级状态）|
| **R12** | [I2] External network 依赖 | **承认** | **1.13**（条件化）|
| **R12** | [I3] 配置漂移 3 源冲突 | **承认** | **1.11**（统一到根 .env）|
| **R12** | [I4] Bind mount 路径敏感 | **承认** | **1.13**（预检清单）|
| **R12** | [N1] vault_id 一等命名空间 | **采纳** | **1.9** |
| **R12** | [N2] DEPLOYMENT_TOOLS tier | **采纳** | **1.12** |
| **R12** | [N3] Mode 3 PoC | **采纳** | 1.13 |
| **R12** | Claudian 自动检测 vault | **批准** | **1.8** |
| **R12** | canvas_service.py:714 写 vault → :ro 冲突 | 代码审计 | **1.7**（移除 :ro）|

### 未映射 / 延后的发现

| 发现 | 原因 | 何时处理 |
|-----|-----|--------|
| R7 IQ-Q1 熟练度 Frontmatter 存储 | 等 1.1 frontmatter schema 确定 | Phase 2 |
| R7 IQ-Q2 LanceDB 索引粒度 | 等 1.9 vault_id 实现后评估 | Phase 3 |
| D2 Backend 生命周期 | 非关键路径，观察使用后定 | Phase 4+ |
| D3 Frontmatter vs Graphiti 真相源 | 需更多实际使用数据 | Phase 4+ |
| D4 LanceDB 清理策略 | 等 1.9 vault_id 后自然解决 | Phase 3+ |
| D5 MCP 并行调用 | 等 1.12 MCP tools 实现后观察 | Phase 4+ |

---

## Round 13 总结

### 核心产出

**12 轮 QA → 13 个 Story → 4 Phase 路线图**

| 产出 | 数量 |
|-----|-----|
| 可执行发现提取 | 40+ 条 |
| Story 总数 | 13（原 6 + 新 7）|
| 总工时估算 | ~72h |
| P0 Story | 6 个（1.1-1.3 + 1.7-1.9） |
| 立即可开始 | Story 1.1（无前置依赖）|

### 下一步

1. **立即**: 进入 Plan Mode → Story 1.1 Vault Init 实施计划
2. **可选并行**: Story 1.7 根 .env（与 1.1 无依赖，可用 worktree 并行）
3. 用户审计本文件后确认 → 开始写代码

### Obsidian 可导航引用

- `_bmad-output/implementation-artifacts/epic-1/1-1-vault-init-templates.md` — Story 1.1 详细规格
- `_bmad-output/implementation-artifacts/epic-1/1-2-wikilink-graph-build.md` — Story 1.2 规格
- `_bmad-output/implementation-artifacts/epic-1/1-3-wikilink-context-assembly.md` — Story 1.3 规格（Paradigm 2）
- `_decisions/mvp-plan.md` — MVP 14 项清单
- `docs/project-status/gap-analysis.md` — 99 FR + 批注
- `docs/project-status/annotation-tracker.md` — 108 条批注追踪

---

**下一轮触发**: 用户审计完毕 → 进入 Story 1.1 实施 Plan Mode
