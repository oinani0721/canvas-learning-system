---
title: "Round-22 对抗性设计审查 — Epic-10 + Epic-11"
date: 2026-05-07
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
scope: "Epic-10 (DeepTutor Fork MVP) + Epic-11 (Electron Desktop App)"
review_type: "adversarial cross-epic design audit"
agents: 5
status: "pending-chatgpt-second-opinion"
trigger: "用户 2026-05-07 要求并行 agent deep explore Epic-10/11 设计冲突 + Round-22 批注审查"
---

# Round-22 对抗性设计审查 — Epic-10 + Epic-11

> **审查目标**：纯设计层冲突探测（不涉及工期/用户原意）。验证 Epic-10/11 spec 在实施时是否会卡在跨 Epic 接缝、内部矛盾或 AC 缺位。
>
> **方法论**：5 Agent 并行 deep explore + Orchestrator 整合
> - Agent 1: Epic-10 设计契约提取（42 AC + 9 Story）
> - Agent 2: Epic-11 设计契约提取（24 AC + 4 Story）
> - Agent 3: Round-22 批注追溯（23 用户原话 + 13 决策链 + 10 NEG + 12 UX）
> - Agent 4: Epic-10/11 冲突探测（12 维度交叉对比）
> - Agent 5: 对抗性反例（Devil's Advocate 5 致命 + 4 漂移 + 5 疑问）

---

## 设计冲突总计

| 严重度 | 数量 | 关键代表 |
|---|---|---|
| 🔴 CRITICAL | 4 | Canvas+Neo4j 失踪 / Next.js mode 矛盾 / MP4 协议断链 / CORS file:// 空白 |
| 🟡 HIGH | 7 | vault 路径 / vault watch / D4 缺位 / 核心 3 无 AC / NEG-1 字面冲突 / 枚举命名 / BlockType 兼容 |
| 🟢 MEDIUM | 5 | UX-10 / UX-3 / NEG-7 / DocumentAdder / Path A 触发 |
| ⚪ LOW | 4 | estimate 漂移 / ORIGIN_WHITEBOARD / 幽灵报告 / desktop 子目录 |
| **总计** | **20** | — |

---

## 🔴 CRITICAL — 实施时会卡住的架构空洞

### S1. Canvas backend + Neo4j 在 Epic-11 完全失踪

| 维度 | Epic-10 | Epic-11 |
|---|---|---|
| 后端服务 | Canvas :8011 + DeepTutor :8001（双 FastAPI） | 仅 spawn `deeptutor.api.main`（1 个 subprocess） |
| 数据库 | Neo4j :7691 + LanceDB | 0 处提及 |
| Dependencies 列表 | Neo4j 5.26+ + Docker 29+ + bge-m3 | electron + fastapi + uvicorn |

**实施后果**：Story 11.2 启动后 fetch `:8011/api/v1/wikilink/build` → 没人监听 → S1-S5 全 fail
**证据**：`epic-11/_README.md:191-205`、`epic-11/11-2-ipc-bridge-fastapi-subprocess.md:51`
**修复路径**：
- **A**：Electron main 进程 spawn 双 FastAPI subprocess（+ Neo4j Java JRE 嵌入或 sqlite 替代重写 Cypher）
- **B**：Canvas backend 合并进 DeepTutor FastAPI（推翻 Story 10.2 wikilink_proxy 架构）
- **C**：Epic-11 保留 Docker compose，Electron 仅 GUI 包装（包大 + 用户机器需装 Docker）

### S2. Next.js `output:"standalone"` vs `output:"export"` 配置不可能并存

- **D18 选 Electron 的核心理由**（`research/round-22-desktop-app-rendering-deep-explore-2026-05-07.md:224`）："**保留 Next.js 完整能力（SSR + API routes）→ npm start 直跑**"
- **Story 11.1 实际方案**：file:// 加载 `out/` 目录（SSG 产物）= 丢 API routes
- **Task 1.2** 同时要求 `.next/standalone/` 和 `out/` 目录存在 = next.config.js 配置层不可能

**证据**：`epic-11/11-1-electron-framework-web-bundling.md:58-59`、Task 1.2-1.3、L138 Dev Notes
**修复**：必须二选一
- 走 standalone：main 进程 spawn `node .next/standalone/server.js` + BrowserWindow 加载 `http://localhost:<dynamic>`（与 D18 一致，Story 11.1 全 Task 重写）
- 走 SSG：审计 DeepTutor 所有 `/api/*` Next.js routes 迁移到 FastAPI（D18 决策依据塌方，Tauri 反而更优）

### S3. MP4 URL 协议在 Epic-10 → Epic-11 迁移空白

- Story 10.5 MathAnimatorPlayer：HTTP（`:8001/api/v1/math-animator/output/:turn_id`）
- Story 11.3 AC #3：`<video src="file:///path/to/math.mp4">`
- **Epic-11 0 个 Task 说明 Story 10.5 的 fetch 怎么迁移**
- file:// 路径需要 main 进程把 subprocess 输出位置（`~/.cache/deeptutor/agent/math_animator/{turn_id}/`）转成 file:// URL 暴露给 renderer——整套链路无设计

**证据**：`epic-10/10-5-day5-6-whiteboard-route.md:222-223`、`epic-11/11-3-vault-integration-rendering.md:67-69`、Task 4.2

### S4. CORS_ORIGINS file:// origin 处理空白

- Epic-10 CORS_ORIGINS：`:3782 / :8001 / :5173 / :tauri.localhost`
- Epic-11 BrowserWindow：`file:///.../out/index.html` → `window.origin = "null"`
- **Canvas backend CORS_ORIGINS 不含 "null"** → fetch :8011 全部被 browser block
- Epic-11 4 Story **0 处提及 CORS**

**修复**：CORS_ORIGINS 加 `null` 或 `app://localhost`（自定义协议）或彻底走 IPC（renderer 不直接 fetch）

---

## 🟡 HIGH — 设计漂移（7 条）

### H1. Vault 路径切换协议跨 Epic 断链

- Epic-10：vault path 通过 `${CANVAS_WORKTREE_PATH}` env var → docker bind mount → 容器内 `/vault` 固定
- Epic-11：用户 fileDialog 选 → `~/.deeptutor-app/vault-path.json` 持久化 → 运行时可变
- **Canvas backend 怎么知道用户切了 vault？Story 11.2 AC #3 只通知 DeepTutor subprocess，没通知 Canvas**

### H2. vault watch 双 watcher 路径冲突

- Epic-10 Phase B：Python `watchdog` daemon (`vault_monitor.py` ~120 行) → 调 `:8011/api/v1/wikilink/build`
- Epic-11 Story 11.3：`useVaultFile` hook → IPC `vault:watch` → 暗示 Node `fs.watch` / `chokidar`
- **Story 11.2 Task 8 列的 4 FastAPI endpoint 不含 watch**，Task 7 让 main 进程"调 FastAPI" → race condition + 双 wikilink_graph rebuild 风险

### H3. D4 "Graphiti 闭环贯穿" 在 Epic 级 AC 缺位

- 用户 D4（Round-21 L1085）："整个闭环必须由 Graphiti 后端贯穿，否则检验白板无法'深刻'考察"
- Epic-10 5 个 Epic 级 AC：**无一条** Graphiti 验证
- Story 10.1-10.7 + 10.9 = 0 个 Graphiti 操作
- Story 10.8 Task 6.3 = 唯一 Graphiti 写入（P1 而非 P0）
- **设计层缺口**：闭环没有 read-after-write 验证（写入但没人查询关联错题）

### H4. 核心 3 "个人记忆系统在两白板的应用" 拆分无 single AC

- 用户 D3 第 3 项原话："个人记忆系统**在原白板和检验白板的应用**"
- Epic-10 拆分：Story 10.6（BKT/FSRS）+ Story 10.8（Graphiti episodic）
- **"在两白板的应用"语义无任何 single AC 体现**——验收时容易漏

### H5. NEG-1 vs Story 10.5 "跨 book 全景视图" 字面冲突

- NEG-1：用户 Round-12 砍"跨白板关联"
- Story 10.5（`10-5:146`）："Whiteboard: 全 vault 跨 book ReactFlow 可交互" / "全 vault 节点关系图"
- **设计层需澄清**：
  - "跨白板关联" = AI 自动推断的语义关系（用户已砍）
  - "跨 book 全景视图" = 用户主动浏览整 vault wikilink 图（不是自动推断）

### H6. ErrorCandidate 4 类枚举命名内部矛盾

- Story 10.7 AC #3 用大写枚举：`PROBLEM_FRAMING / REASONING_FALLACY / KNOWLEDGE_GAP / SUPERFICIAL`（来自 Canvas `error_loop_detector`）
- 通俗化解释段：`misconception / careless / computational / slip`（教育心理学常用）
- **未给映射表**

### H7. BlockType 17 在 Next.js 选定 mode 下渲染契约未审

- Epic-10 加 3 BlockType：MASTERY_DASHBOARD / EXAM_WHITEBOARD / ERROR_CANDIDATE
- Epic-11 0 处审视它们在选定的 Next.js mode 下渲染
- 若走 SSG（Story 11.1 实际方向）→ MasteryDashboard 依赖运行时 fetch → hydration mismatch warning

---

## 🟢 MEDIUM — 设计说明不清（5 条）

| # | 问题 |
|---|---|
| M1 | UX-10 "Graphiti 多段推理"（用户选 Graphiti 核心理由 Round-15 L62）在 Epic-10 仅写入未显式查询多 hop，AC 不体现 |
| M2 | UX-3 跨时间错误重现（Round-15 L33）降级 P2 写入 R8 Risks，但用户原意明确——设计层需要"基础+扩展"路线，不是单纯降级 |
| M3 | NEG-7 图片 RAG 通道用户存疑（Round-12.1 B6），Epic-10 未显式落地，Day 5+ vault 含图片可能误触发 `retrieve_multimodal` |
| M4 | DocumentAdder vault_mode=True 在 Epic-11 是否仍生效（Epic-11 AC #5 验证"无外网请求" ≠ "DeepTutor 内部 KB 不上传"） |
| M5 | Path A 触发条件可观测性：Epic-11 trigger 简化为"5 PASS"，把"用户拍板"闸门隐去——设计层应明示 `DECISION-DAY-10.md` 中 Path A 已勾选 |

---

## ⚪ LOW — 文档/命名不一致（4 条）

| # | 问题 |
|---|---|
| L1 | Story 10.3 estimate `4h` vs Phase A+B 调研 `12-16h`；Story 10.4 estimate `16h` vs 调研 `35-50h` |
| L2 | `ORIGIN_WHITEBOARD` 在 Epic-10 _README Capabilities 提到，Story 10.6/10.7 enum 实际新增是 MASTERY_DASHBOARD/EXAM_WHITEBOARD/ERROR_CANDIDATE |
| L3 | `round-22-deeptutor-fork-mvp-2026-05-06.md` 文件**实际不存在**，但 Epic-10/11 多处引用为锚定源 |
| L4 | fork 仓库 `desktop/` 子目录是 monorepo 子包还是独立仓库？是否会污染 NEG-3 mvp-baseline tag？Story 11.1 Task 2.1 不明 |

---

## Round-22 批注遗漏清单（Agent 3 关键发现）

| 类型 | 用户原话 | 当前 Epic 落地 | 缺口 |
|---|---|---|---|
| **核心 3 拆分** | "个人记忆系统**在原白板和检验白板的应用**"（Round-20 L222） | 拆成 10.6 BKT/FSRS + 10.8 Graphiti | "在两白板的应用"语义无 single AC |
| **UX-3** | "想起原白板内容，再次考察是否会犯类似错误"（Round-15 L33） | 降级 P2 写入 Risks | Day 10 UAT 需用户确认接受降级 |
| **UX-10** | "Graphiti 多段推理能力十分优秀，所以选它"（Round-15 L62） | Story 10.8 仅写入未显式查询多 hop | AC 未体现多 hop 验证 |
| **NEG-7** | "图片 RAG 通道值不值得"（Round-12.1 B6） | Epic-10 未显式落地 | Day 5+ vault 含图片可能误触发 |
| **Round-22 主报告** | 所有 Epic 引用为锚定 | **文件系统不存在** | 文档治理空洞 |

---

## 5 Agent ID（如需 SendMessage 继续追问）

| Agent | ID |
|---|---|
| A1 Epic-10 契约 | `ac2c173f42d61cda2` |
| A2 Epic-11 契约 | `aaedfa4ebb4d544b6` |
| A3 Round-22 追溯 | `a74974e39dd1399d4` |
| A4 冲突探测 | `a629d4f6c4eab8050` |
| A5 对抗性反例 | `a49a17ec712ca190a` |

---

## 立即决策点（待用户拍板）

### 🔴 阻塞 Story 11.1 启动（Epic-11 启动前必须决）

1. **S1 修复方向**：Canvas backend + Neo4j 在 Epic-11 怎么跑？（A/B/C 三选一）
2. **S2 修复方向**：Next.js 走 standalone (SSR) 还是 SSG？

### 🟡 影响 Day 10 UAT 验收完整性

3. **H3 + H4 + M1 补 AC**：D4 闭环 / 核心 3 应用 / UX-10 多段推理是否升 Epic 级 AC？
4. **H5 NEG-1 字面冲突**：Story 10.5 "跨 book 全景视图" 是否等同于 NEG-1 砍掉的"跨白板关联"？

### 🟢 文档治理（低风险但建议处理）

5. **L3 Round-22 主报告幽灵**：补创该文件，或把所有 Epic spec 引用改指向 D17？

---

## 引用文件清单

### Epic 文档
- `_bmad-output/implementation-artifacts/epic-10/_README.md`
- `_bmad-output/implementation-artifacts/epic-10/10-3-day2-cleanup-vault-mount.md`
- `_bmad-output/implementation-artifacts/epic-10/10-4-day3-4-canvas-vault-adapter.md`
- `_bmad-output/implementation-artifacts/epic-10/10-5-day5-6-whiteboard-route.md`
- `_bmad-output/implementation-artifacts/epic-11/_README.md`
- `_bmad-output/implementation-artifacts/epic-11/11-1-electron-framework-web-bundling.md`
- `_bmad-output/implementation-artifacts/epic-11/11-2-ipc-bridge-fastapi-subprocess.md`
- `_bmad-output/implementation-artifacts/epic-11/11-3-vault-integration-rendering.md`
- `_bmad-output/implementation-artifacts/epic-11/11-4-multiplatform-release-autoupdate.md`

### 决策批注
- `_bmad-output/决策批注/D17-round22-fork-mvp-2026-05-06.md`
- `_bmad-output/决策批注/D18-desktop-app-electron-2026-05-07.md`

### Round-22 调研报告
- `_bmad-output/research/round-22-deeptutor-deep-explore-2026-05-06.md`
- `_bmad-output/research/round-22-day2-vault-access-design-2026-05-06.md`
- `_bmad-output/research/round-22-chat-vs-tutorbot-usage-comparison-2026-05-06.md`
- `_bmad-output/research/round-22-cli-sdk-book-engine-deep-explore-2026-05-07.md`
- `_bmad-output/research/round-22-desktop-app-rendering-deep-explore-2026-05-07.md`
- ⚠️ `round-22-deeptutor-fork-mvp-2026-05-06.md` — 引用但**不存在**

### 历史调研（Round-12 ~ Round-21）
- `_bmad-output/research/round-12-graphiti-karpathy-5-conjectures-audit-2026-04-21.md`
- `_bmad-output/research/round-12-1-5-annotations-deep-dive-2026-04-21.md`
- ... （round-13 ~ round-21）

### Memory
- `~/.claude/projects/-Users-Heishing-Desktop-canvas-canvas-learning-system/memory/decision_round22_fork_mvp.md`

---

## 下一步

1. ✅ 本报告 commit（含 plan_id `EPIC1-BMAD-DEV-ASSESS-2026-04-17`）
2. ⏳ ChatGPT Deep Research 第二意见（提示词另存 `chatgpt-prompt-epic-10-11-design-review-2026-05-07.md`）
3. ⏳ 用户拍板 5 个决策点
4. ⏳ 按用户决策更新 Epic-10/11 spec + sprint-status.yaml

*生成日期：2026-05-07 / 报告模型：Claude Opus 4.7（5 并行 Agent + Orchestrator）*
