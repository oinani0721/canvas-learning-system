# CURRENT_TASK: Canvas Learning System × Obsidian Hybrid（回归路径）

> **前 15 行是 Clear Context 后的恢复锚点 — 必须自包含**

**当前状态**（2026-05-11 续 · 合并 Story 2.2+2.9 T3+T5 ship）:
- ✅ ChatGPT 全链路对抗审查完成（5 Tasks verdict + 3 P0：Multi-Vault 全链路 / 生产默认值 / 修主检索链路），response 归档 `_bmad-output/chatgpt-review-response-2026-05-11.md`
- ✅ **合并 Story 2.2+2.9** spec ship + checklist 全勾 (7 AC + 7 Tasks 除 T0 / T6.2/T6.3 perf)
- ✅ **T1 plugin timeout 降级 done** (`c5e5a92`, 156 frontend tests) + 用户 UAT 通过
- ✅ **T2 backend 基础设施 done** (`6d2c05e`, 75 backend tests)
- ✅ **T3a assembler 渲染 done** (`e0d91c0`, 119 tests)
- ✅ **T3 rerank engine + T5 evidence done** (`549d5f0`, 209/209 unit tests green)
- ✅ **T3+T5 用户 UAT 通过** (2026-05-12)
- ✅ **Q1+Q2+Q3 三领域 P0 完全修复 done** (`de0b4a7`, 245 backend + 173 frontend = 418/418)
- ✅ **ChatGPT v2 对抗审查 prompt 优化 + 跑过** (`d31e399`/`9bc04df`, GitHub URL 精确导航 + 强约束输出 + 内联代码 snippet)
- ✅ **ChatGPT v2 verdict 揭示 3 P0 + 5 新发现 (frontend auth / lancedb vault wiring / review fail-open / metadata 漏扫 / __default__ fallback)** — 我和 audit agent 之前都漏了
- ✅ **Wave-2 hotfix 全闭口 done** (`f018580`, backend 219 + frontend 186 + 4 security 回归测试): P0-1 frontend X-CLS-Internal-Key + P0-2 LanceDB ContextVar wiring + P0-3 真 fail-closed (a/b/c) + cleanup_loop + 4 漏修

**下一步**:
- 用户跑 3 UAT 验收单 (Q1/Q2/Q3 已在 `_bmad-output/验收单/`)
- 可选: 再 round ChatGPT v2 prompt 验证 wave-2 (commit f018580) 是否真闭口
- T0 主链路修复 + RAGAs 基准 (3-5d 独立 session, P0-C)

**8-Session 全 plan（Round-14 用户原话需求 #1#2#3 落地）**:
- S1: Story 2.2 (用户原话 #1) | S2: 2.3 历史误解 | S3: 5.1 BKT MCP (用户原话 #2)
- S4: 5.2 FSRS (用户原话 #3) | S5: 5.3 五信号融合 | S6: 综合 UAT

**关键路径**:
- 本 worktree: `~/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/`
- archive worktree: `~/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-deeptutor-canvas-mvp/`
- 主仓 read-only: `~/Desktop/canvas/canvas-learning-system/`

---

## Round-22 弃用决策（2026-05-08）

### 弃用原因（双重证据）

1. **"内容越多幻觉越严重"**: Liu 2023 (Lost in Middle) + Cuconasu SIGIR 2024 (Power of Noise) + Chroma 2025 (Context Rot) + Karpathy llm-wiki Gist 共同实证。60KB vault scale 应抛弃 RAG 走 Karpathy LLM Wiki 模式（compile once + inline）
2. **"wiki 范式只承载 final state，缺 4 维度"**: Concept Map (Novak 1972) + Spatial Hypertext (Marshall 1995) + TextNet (Trigg 1986) + Tree-of-Thoughts (Wei 2022) 4 学术 framework 共识 — wiki 丢了时间(when) / 空间(where) / 原因(why) / 置信度(how-sure)

### 路径对比

| 路径 | 状态 |
|---|---|
| Round-22 fork MVP（DeepTutor 集成） | ⛔ 弃用 |
| Obsidian Hybrid（回归路径） | ✅ 主线 |
| Tauri v0（更早历史） | 已淘汰 |

### archive 内容指针（DeepTutor worktree 仍保留）

- 17 份 round-22-* 调研报告
- Epic-10 / Epic-11 implementation-artifacts（9 + 4 stories）
- Story 10.1-10.4 验收单 v2.0 双段重写版
- 决策批注 D17（fork mvp）/ D18（desktop electron）/ D19（docker compose）
- adapter 6 文件（在 fork repo `~/Desktop/canvas/deeptutor-fork/adapter/`，可删）
- DeepTutor fork repo（116MB）+ vanilla repo（28MB）— 用户决定是否 rm

---

## 从 DeepTutor worktree 迁移过来的 UAT v3.0 资产

| 文件 | 来源 | 升级内容 |
|---|---|---|
| `_bmad-output/templates/uat-sheet-template.md` | DeepTutor worktree v2 | 双段强制 + 5-Second Test 起手 + "我做X→我看到Y→我感觉Z"句型 + Felt-sense 主观打分 + 5 题自检 + 方法论分层 |
| `_bmad-output/.claude/CLAUDE.md` § DoD-3 | DeepTutor worktree v3.0 | D3-A~D3-E 5 铁律 + 方法论分层（Phase A/B/Day7+）+ 升级版自检清单 |
| `.claude/hooks/uat-double-section-guard.js` | DeepTutor worktree | PostToolUse 自动检测段 4-B 禁词 + felt-sense 软警告 |
| `.claude/settings.json` | DeepTutor worktree | 追加 hook 配置（不覆盖现有 router） |
| `_bmad-output/验收单/_reference/范本-双段-Story-10.4.md` | DeepTutor Story-10.4 v2.0 | 范本（0% 违规率） |

旧版备份: `*.v1.backup.md` / `*.v1.backup.md`

---

## 2026-04-17 历史活跃计划（Obsidian Hybrid 路径）

### EPIC 1 v2 BMAD（17/17 done）
- Story 1.16 批注 hotkey + 7 callout ✅
- Story 1.17 ai-linked-doc + 双链文档 ✅
- Story 1.18 dashboard-mvp ✅
- Story 1.19 configure-whiteboard ✅
- 13 backend stories ✅（commit `4e0c27b` + `43294c3`）

### EPIC 2 智能检索管道（部分 done）
- Story 2.5.X 渐进确认 ✅（D15）
- Story 2.5.Y 隔离硬化 ✅（D16）
- 其余 Stories（含 Story 2.1 AI dialog context injection）待续

### Round-14/15 用户原话需求（Obsidian Hybrid 路径仍适用）

> "我在 obsidian 上是用 obsidian 的 md 文件 然后再加上了 自己定义双向链接 来规划各个节点之间联系" (Round-14)

> "节点的理解程度是如何批判的，我个人更倾向于，我对md 节点内容所打下批注的过程，这个批注则是我的核心的想法也是我后续需要聚焦考察的点" (Round-14)

> "我学习是会以一个 vault 文件夹作为核心，那么我需要 ai 在给我解释讲解题目的时候，能精确返回我储存在笔记库里的笔记片段" (Round-15)

---

## 切回后的 5 件事（按 Agent 3 报告）

| # | 操作 | 时长 |
|---|---|---|
| 1 | 状态确认 (`git status`, `sprint-status.yaml`, `git log -10`) | 5 min |
| 2 | 读 `round-21-canvas-five-core-deeptutor-integration-2026-05-06.md`（92KB 最后一次 Obsidian Hybrid 思路）+ Round-14/15 用户原话批注 | 30 min |
| 3 | 决定下一步 Epic / Story（候选：Epic-3 / Story 2.1 / Story 3.1） | — |
| 4 | docker 清理（推荐 stop+rm deeptutor / vanilla / pocketbase 容器，保留 canvas-backend / neo4j） | 10 min |
| 5 | 删 fork/vanilla repo（用户决定，~144MB 释放） | 5 min |

---

## 已知瑕疵 / 待办

- ⚠️ Obsidian Hybrid worktree 现有 dirty 状态（`.env.example` modified / `round-18-*.md` modified / 12 个 untracked 含 `staging-deeptutor-fork/`）— 切回后先 stash 或清理
- ⚠️ 旧 UAT 模板备份为 `.v1.backup.md`，验证新版无问题后可 rm

---

*恢复锚点 v1.0 - Obsidian Hybrid 回归路径 2026-05-08*
