---
active_plan: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
active_plan_file: "_bmad-output/research/2026-05-21-sprint-plan-v3.md"
current_sprint: "Sprint v3 · Obsidian Hybrid Day 2"
sprint_progress: "3/27 done (11.1%) — auto-synced"
next_story_id: "INFRA-003"
next_story_title: "docker-compose healthcheck 路径修复"
next_story_files:
  - "backend/docker-compose.yml"
  - "backend/app/interfaces/api/health.py"
last_commit_hash: "d25447e"  # auto-synced; msg: docs(sprint-2): S2-1 V-10 修复规划记录 + BMAD 追踪 (代码已 commit main 
last_commit_hash_alt: "548d14d"  # INFRA-002 装路由
sprint_status_file: "_bmad-output/implementation-artifacts/sprint-status.yaml"
sprint_status_key: "development_status.sprint_v3_obsidian_hybrid"
prd_anchor: "/Users/Heishing/Desktop/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md"
session_handover_sop: "新 session 5 min 启动 — 见正文 §1"
plan_kind: "bmad-implementation"
active_phase: "sprint-v3-day-2-pending"
round: 13
last_updated: "2026-06-01T02:11:48Z"
round10_key_finding: "推荐选项 1 用户手动 docker-compose up + Obsidian Plugin 健康检查（0 代码，符合 Smart Connections/Khoj/Copilot 社区主流）+ 可选选项 2 Claudian MCP tool check_backend_health 自动协调（~50 行 Python）。关键证据：tauri.conf.json 无 sidecar 配置（Tauri 原本也未自动启动），Electron 沙箱禁止 Plugin spawn subprocess，Claudian 是唯一合法自动启动通道"
round9_key_finding: "推荐保留 Graphiti 做错误/学习事件检索 — 时序+关系查询天然匹配 Episode 模型；数据量小（20-50MB）；启动 Docker 2 分钟；Zep AI 社区源码 https://github.com/getzep/graphiti"
round8_key_findings:
  - "LanceDB 6 张表（非仅 canvas_nodes）— vault_notes 就是用户期待的笔记分块检索，R7-Q2 严重遗漏"
  - "Graphiti 4 个读端触发点（retrieve_graphiti / search_memories 3 层融合），R7-Q3 只审了写端"
  - "3 套检索系统: Graphiti + LanceDB + Neo4j Tier-2 全文备用，R7-Q3 遗漏第 3 套"
  - "LanceDB vs Graphiti 分工矩阵（6 场景）基于代码实读，非凭记忆"
round7_key_findings:
  - "Bash 实证: Graphiti 当前未连接（所有 Neo4j 端口 closed）— IQ-1 答 B"
  - "LanceDB 实际存 Canvas 节点对象，非笔记片段（纠正用户假设）"
  - "社区无向量存储熟练度专门方案，推荐 Obsidian frontmatter + Dataview"
  - "Graphiti 存学习事件（对话内容），不存 md 节点内容"
next_round_trigger: "用户跑 Mode 3 PoC（Obsidian Plugin child_process 测试）→ ✅ Mode 3 可行 / ❌ 正式关闭 → Round 13 最终架构定稿"
commit_rule: "文档 commit 必须包含 PLAN-OBSIDIAN-QA-ROUND12-2026-04-16"
round12_main_file: "[[obsidian-qa-round12-claude-answers-2026-04-16]]"
round11_main_file: "[[obsidian-qa-round11-claude-answers-2026-04-16]]"
round10_main_file: "[[obsidian-qa-round10-claude-answers-2026-04-16]]"
round9_main_file: "[[obsidian-qa-round9-claude-answers-2026-04-15]]"
round8_main_file: "[[obsidian-qa-round8-claude-answers-2026-04-15]]"
round7_main_file: "[[obsidian-qa-round7-claude-answers-2026-04-15]]"
round6_main_file: "[[obsidian-qa-round6-claude-answers-2026-04-15]]"
round5_main_file: "[[obsidian-qa-round5-claude-answers-2026-04-15]]"
round4_main_file: "[[obsidian-qa-round4-claude-answers-2026-04-14]]"
round3_main_file: "[[obsidian-qa-round3-claude-answers-2026-04-14]]"
round2_main_file: "[[obsidian-qa-round2-claude-answers-2026-04-14]]"
original_qa_file: "[[obsidian-translation-qa-2026-04-14]]"
round4_character: "从 UX 翻译升级到后端硬核审计 + 增量提问（非直出方案）"
round5_character: "决策 Close-out + 非技术用户通俗化 + Claude Code 压缩算法调研"
round4_agents:
  - "Agent X: 后端功能降级利用率（28 ALIVE / 3 ZOMBIE / 精简 4）"
  - "Agent Y: 检验白板 15 步 + Hot/Warm/Cold 三存储双触发链"
  - "Agent Z: 四路搜索三级分类（L1❌/L2✅/L3🟡/L4🔴）"
round5_agents:
  - "Agent A: Claude Code /compact + 5 方案 SOTA 对比（KVzip/LLMLingua/ACON/RMT/MemGPT）"
  - "Agent B: Q1-Q8 实施方案 + alert_manager 纠正（ACTIVE）+ 3 ZOMBIE 归档脚本"
  - "Agent C: Q4/Q7/Q10 通俗化（账本-图书馆-日记 / 搬家 / 快递驿站登记本）"
integrity_rules_latest: "IC-8（Round 5 新增）— 通俗解释必须具体日常类比 + 外部算法必须 arxiv/官方 URL + 选项答复必须展开实施方案"
evidence_sources_used:
  - "backend/app/services/ 全目录扫描（40+ 文件）"
  - "backend/app/mcp/tools/（MCP 工具集）"
  - "docker-compose.yml + backend/Dockerfile"
  - "docs/known-gotchas.md（32/37 已修，86%）"
  - "backend/tests/（13 检索文件 / 207 test 函数）"
  - "_bmad-output/planning-artifacts/recovered/prd-tauri-original-2ae5897.md"
  - "openspec/specs/agentic-rag + archive"
round3_corrections_count: 7
round3_r3_sections: 18
round4_r4_sections: 4
round4_incremental_questions: 8
round5_r5_sections: 10
round5_user_annotations: 10
round5_key_correction: "alert_manager.py 被 Round 4 误判为 ZOMBIE；Agent B 复核实际 ACTIVE（9 调用方）；真 ZOMBIE 是 fallback_sync_service + extraction_validator + react_agent（2039 行）"
deprecated_docs:
  - "[[canvas-crossdiscipline-tags-v1]]"
  - "[[canvas-index-md-spec-v1]]"
previous_plans:
  - "DASHBOARD-UI-DECISION-v1 (closed 2026-04-13)"
  - "STORY-1-3-PARADIGM-SHIFT-v1 (closed 2026-04-13 commit beb93d0)"
  - "OBSIDIAN-QA-ROUND2-2026-04-14 (closed 2026-04-14, 5 处偏离 Round 3 已纠正)"
  - "OBSIDIAN-QA-ROUND3-2026-04-14 (closed 2026-04-14, 18 R3-Qn section + 18 [A4] 简答完成)"
  - "OBSIDIAN-QA-ROUND4-2026-04-14 (closed 2026-04-15, 4 R4-Qn section + 4 [A5] 追加 + 8 增量提问)"
next_round_trigger: "用户审计 Round 5 后，可能触发 Round 6：(1) Q4 Mastery Store 明示 A/B/C；(2) Q5 是否接受 Claude 推 A 覆盖用户选 B；(3) 批准 KVzip+ACON 压缩迁移；(4) 批准 ZOMBIE 归档脚本执行"
---

# CURRENT_TASK — Sprint v3 接管状态（唯一真相源）

> ⛔ **新 session 启动前 20 行自包含状态卡片** — 不读完整文档即可接续开发
> ⛔ 完成一步后立即更新 checkbox；commit 必含 `active_plan` ID（`EPIC1-BMAD-DEV-ASSESS-2026-04-17`）。

## §0 · v3.0 update — Sprint v3 v3 起步 (2026-05-26 ChatGPT 体系审查后)

⛔ **新 session 优先读此段, §1-§6 是 v3 v1 历史背景**.

### ⭐⭐ 2026-06-01 最新状态 — 新 session 从这里起步 S2-2

**已 commit**:
- ✅ **S2-1 V-10 评分对象漂移修复 → main `bb00ed5`** (backend/app/services/question_registry.py 新建 + exam_tools.py generate_question 存题面×2 + score_answer 回读 + degraded 防污染; test_question_registry.py **8 passed**). worktree 规划记录 `d25447e`

**用户 2026-06-01 三大决策 (已拍板)**:
1. **仓库**: 以 `canvas-learning-system` 为唯一开发仓库 (643 commit/208 py/67 spec). hybrid 仓库是空壳 (1 commit) → **用户授权删除** (`gh repo delete oinani0721/canvas-obsidian-hybrid --yes`, hook 拦了我, 待用户/新 session 跑)
2. **代码主线 = main** (真相源 = main sprint-status, 用 epic-1/2/3 + Epic 6 检验白板编号). worktree 是规划层
3. **下一步 = 在 main 起步 S2-2 Graphiti 个人记忆脊柱** (用户最看重, 当前 main 无人实施)

**⛔ 新 session 起步 S2-2 前必做 (2 个清理)**:
- [~] **restore 删除文件** (frontend/src 已恢复; 剩 866 = docs/838 + frontend/27 + _bmad/1). 完整命令 (hook 拦我, 用户跑): `cd /Users/Heishing/Desktop/canvas/canvas-learning-system && git restore frontend/ docs/ _bmad-output/` — ⚠️ **不要 `git restore .`** (会抹掉别人正在做的 backend M 改动). ⚠️ docs/ 838 是 Tauri 时期文档 (CLAUDE.md 说已迁移 archive/legacy-docs/), **可能是有意清理** — 用户若确认 Tauri docs 要删, 恢复后专门做 deprecation commit; 不确定则全恢复 (无损 HEAD 完整). 别人 backend M (episode_worker/memory_service 等) 保留不碰
- [ ] **删 hybrid 空壳仓库** (gh 缺 delete_repo scope): `gh auth refresh -h github.com -s delete_repo` 再 `gh repo delete oinani0721/canvas-obsidian-hybrid --yes`; 或 GitHub 网页删; 或不管 (空壳 1 commit 无害, 以 canvas-learning-system 为准即可)

**S2-2 起步指引 (在 main 实施)**:
- spec: `worktree _bmad-output/implementation-artifacts/epic-5a-graphiti-runtime/5-ge-1-canvas-graph-episode-v1.md + 5-ge-2-belief-key-version-chain.md`
- 内容: CanvasGraphEpisodeV1 统一事件 schema + edge_type_map 透传 episode_worker + belief_key 版本链 (valid_at/invalid_at) + questions_registry 持久化 (让 S2-1 的 in-memory registry 升级为持久化, 彻底修 V-10 重启丢题)
- ⚠️ main 工作树有别人改动 (956 脏状态 restore 后 + 可能其他) → **精确 git add 只 commit 自己文件** (V-10 已示范)
- ⚠️ main 用 Epic 6 检验白板编号, worktree 用 epic-4/5a → commit message 用 Epic 6 对接 + 标注 worktree spec 来源
- 执行流程: BMAD 追踪 (in-progress → Tasks 打勾 → Dev Agent Record → DoD-3 UAT → review), commit message 承载追踪

**待续 (S2-2 后)**: main↔worktree epic 映射表 + S2-1 收尾 V-08 (wikilink 进出题) + S2-3/4/5

**双审查收敛结论** (Sprint 2 五任务定稿): `_bmad-output/审查/2026-05-27-双审查收敛-Sprint2-执行计划.md` (原白板真 68% / 检验白板 42% / 核心闭环 37.5%; 唯一先手 = Graphiti 记忆脊柱)

### 当前 Sprint 2 v3 状态 (2026-05-26 ChatGPT 体系审查后锁定)

- ✅ **commit c8538d5 已 push origin + backup** (含 5 个 ChatGPT 5 必修新 spec + 体系全图诊断 + 体系审查包)
- ✅ **epic 改名 `epic-5-graphiti-era` → `epic-5a-graphiti-runtime`** (ChatGPT: 它是旧 Epic 5 的上游 runtime, 非替代品)
- ✅ **17 个旧 spec 归档 `archive/`** (13 高确定 supersede/deprecated + 4 候选; ⚠️ 1-4 hotkey ChatGPT 误判, 保留 live)
- ✅ **3 接口契约 + 6 协同硬规则写入 `_bmad-output/.claude/CLAUDE.md`** (C-1 写入唯一 schema / C-2 读取唯一 facade / C-3 group_id 唯一语法链)
- ✅ **开发流程定调**: BMAD spec 格式 (frontmatter/AC/Tasks) + R4 循环手写实施 (不走 bmad-bmm-dev-story skill, Graphiti 精确 schema 手写更稳)
- ✅ **ChatGPT 体系判定 4.5/10**: 该开发的是 5-ge 主干 + 1.16/2.10/LITE-4-3 适配/消费, 不是旧 64 ready-for-dev

### Sprint 2 v3 起步序列 (5 session 并行, Day 5-10)

| Session | 干什么 | 工时 | spec |
|---|---|---:|---|
| **A** UX 收尾 (轻) | NEW-UX-001/002 + LITE-5-7 AC#1 Tauri 残留修 + mvp-plan-obsidian-hybrid.md 重写 | ~4h | sprint_v3_graphiti_era.STORY-NEW-UX-001/002 |
| **B** 核心 (重) | **5-ge-1** CanvasGraphEpisodeV1 + edge_type_map 透传 + 改 episode_worker | 16h | epic-5-graphiti-era/5-ge-1 |
| **C** 时序 (中) | **5-ge-2 → 5-ge-3 → 5-ge-4** belief_key 版本链 + flush + sync production (顺序) | 15h | epic-5-graphiti-era/5-ge-2,3,4 |
| **D** facade (等 B done) | **5-ge-5** GraphitiRelationService facade + 接入 LITE-4-3/5-7 | 3h | epic-5-graphiti-era/5-ge-5 |
| **E** Plugin (中) | callout-sync.ts / wikilink-sync.ts / wikilink-context.ts 改造发 CanvasGraphEpisodeV1 payload | ~10h | (融入 5-ge-1) |

**真并行 = A + B + C + E (4 session), D 等 B done. 41h 总工时, 4 并行 ~10h 实际 wall time.**

### ChatGPT 体系级审查并行进行

- 📦 已 ship 5 个 ChatGPT 必修 spec + 1 README → 可加入审查包
- ⏳ 待 ship: research-pack v3 全图 (76 spec + 5 new + sprint-status + key code + 4 audit 报告)
- 📋 任务书: 见 `_bmad-output/审查/2026-05-26-bmad-spec-体系全图诊断.md` §6

### 5 必修包关键 file paths (Sprint 2 v3 起步必读)

```
_bmad-output/implementation-artifacts/epic-5a-graphiti-runtime/   # ⭐ 已改名 (原 epic-5-graphiti-era)
├── README.md                              # 子 epic 说明 + 5 session mapping
├── 5-ge-1-canvas-graph-episode-v1.md      # Session B (16h) — 波 1
├── 5-ge-2-belief-key-version-chain.md     # Session C (9h) — 波 2
├── 5-ge-3-query-time-flush.md             # Session C (4h) — 波 2
├── 5-ge-4-relationship-sync-production.md # Session C (2h) — 波 2
└── 5-ge-5-graphiti-relation-service-facade.md  # Session D (3h) — 波 3 (等 B done)
```

### Sprint 2 v3 三波次 (ChatGPT 校正, 非纯 5 并行)

```
波一: A (UX/UAT) ‖ B (5-ge-1 schema) ‖ E (1.16/2.10 scaffold, 不锁 payload)
波二: C (5-ge-2/3/4) ‖ E (对齐 5-ge-1 后完成 payload) ‖ A (1.18/1.19 收尾)
波三: D (5-ge-5 facade) → LITE-4-3 (等 2.10+facade) → LITE-5-7 AC#1 patch only
```

硬依赖: B↔E 协议依赖 (E 不能在 B schema 定版前合并 payload) / C↔D 服务依赖 (D 依赖 C belief+flush contract).
**3 接口契约 + 6 硬规则见 `_bmad-output/.claude/CLAUDE.md` §Graphiti Runtime 体系契约**.

### ⚠️ V-07/V-08/V-10/V-11 旧修复方案状态 (重要 — 防新 session 误读)

- ❌ **V-07** `1-16-callout-graphiti-hook` 加 5 字段 — **superseded by 5-ge-1** (callout 走 unified schema)
- ❌ **V-10** `questions_registry` 新表 — **superseded by 5-ge-2** (belief_key 版本链更通用)
- ⚠️ **V-08** `LITE-4-3` 路线 0 wikilink 邻居 — **partial superseded by 5-ge-5 facade** (路线 4 改调 facade)
- ⚠️ **V-11** `LITE-5-6` dual-write — **partial superseded by 5-ge-1** (calibration 走 unified schema)

### 接续上手 5 min 命令

```bash
git pull
cat _bmad-output/审查/2026-05-26-bmad-spec-体系全图诊断.md  # 体系决策依据
cat _bmad-output/implementation-artifacts/epic-5-graphiti-era/README.md  # 5 session mapping
cat _bmad-output/implementation-artifacts/sprint-status.yaml | grep -A 8 "STORY-5-ge-1\|STORY-NEW-UX-001"
# 选 session A/B/C/E 一个起步 (D 等 B done)
```

---

## §1 · 新 session 5 min 启动检查清单

1. ☐ `git status` 干净（或了解 uncommitted 修改）
2. ☐ `git log --oneline -5` 看到 `769d59a`（INFRA-001/004） + `548d14d`（INFRA-002）
   - ⚠️ 若 commit 不在 git log → 当前 worktree 没拉到 chat history 的实施 commit，需用户介入确认
3. ☐ 读 `_bmad-output/implementation-artifacts/sprint-status.yaml::sprint_v3_obsidian_hybrid` 次 ready story = `INFRA-003`
4. ☐ 读当前 Story spec 或 entry，确认**无** `[DEPRECATED]` marker（防新 session 误读旧 spec）
5. ☐ `python3 .scripts/smoke_test.py` PASS（验证 import 闭合）

## §2 · 当前状态（2026-05-24 Sprint v3 BMAD 化完成时）

- ✅ **Sprint 1 Day 1 完成**（3/25 stories done）
  - INFRA-002（app_factory + 18 router 装配）@ commit `548d14d`
  - INFRA-001（grading EventBus 修复）@ commit `769d59a`
  - INFRA-004（pyproject deps）@ commit `769d59a`
- 🟡 **Day 2 待干**（3 stories, 6h）— 下一个 `INFRA-003`
  - INFRA-003（1h, docker healthcheck 修）← **下一个 Story**
  - EXAM-001（3h, /api/v1/exam/grade endpoint）
  - EXAM-002（2h, /api/v1/exam/quick endpoint）
- ⏳ **Day 3-10 计划** 17 stories（含 6 Lite 重编 + WIKILINK-GRAPHITI 新需求）

## §3 · 接下来 8 步开干流程（新 session 第 1 个动作）

1. SessionStart hook 自动注入此前 20 行（已配置 `.claude/hooks/context-inject.js`）
2. 读 `_bmad-output/.claude/CLAUDE.md`（BMAD scope + 硬规则 DD-03/DD-12/DD-13/DD-14）
3. 读 `sprint-status.yaml::sprint_v3_obsidian_hybrid`（25 Story 状态总览）
4. 验证 git log + commit hash 一致（若 mismatch → halt 问用户）
5. 读 next_story_id 的 entry（接通任务）或完整 spec（Lite/新需求）
6. 跑 `python3 .scripts/smoke_test.py`（确保 import 闭合）
7. 开干 Story（e.g., Day 2 第 1 步 INFRA-003 修 docker healthcheck）
8. commit 必含 plan ID：`EPIC1-BMAD-DEV-ASSESS-2026-04-17`（pre-commit hook 强制）

## §4 · BMAD 化进度（本 plan 2026-05-24 执行）

- [x] Step 1: sprint-status.yaml 加 25 Story entry（含 6 Lite + 9 deferred 砍掉清单）
- [x] Step 2: 升级 CURRENT_TASK.md 为新 session 5min 启动模板
- [x] Step 3: update-current-task.py 脚本 + Stop hook 自动化（验证 PASS: next=INFRA-003, progress=3/26, commit=84954f9）
- [x] Step 4a: 7 个旧 spec 加 [DEPRECATED]/[MERGED] marker（防污染高 ROI 5min 完成 — 见 §6 表）
- [ ] Step 4b: 4 个 Lite/新需求完整 spec（~3h，待用户决策今天写 vs 留新 session 自己写）

## §5 · 关键决策（用户 2026-05-22 锁定，新 session 必读）

- **1B**: WIKILINK-GRAPHITI-SYNC 加入 Sprint 2 Day 9（+6h，单向 Lazy+Batch）
- **2A**: 检验白板 11 处误区修正后接受（3 重隔离 + 三路融合 + ZPD 4 级 + canvas_type concept/problem 区分）
- **3A**: 8.3 元认知 2x2 矩阵 sprint 1+2 砍，400+ 题后回头加
- **4B-mixed**: 接通任务 entry-only + Lite/新需求完整 spec（本 BMAD 化 plan 核心）

## §6 · 防污染策略（新 session 防误读旧 spec）

| 旧 spec 路径 | 状态 | 替代 |
|---|---|---|
| `epic-4/4-3-triple-fusion-question-gen.md` | ✅ `[DEPRECATED]` 已标 | `epic-4/LITE-4-3.md`（待写） |
| `epic-5/5-6-calibration-data-voting.md` | ✅ `[DEPRECATED]` 已标 | `epic-5/LITE-5-6.md`（合并 4.9，待写） |
| `epic-4/4-9-calibration-vote-data-sync.md` | ✅ `[MERGED]` 已标 | 并入 `epic-5/LITE-5-6.md` |
| `epic-5/5-7-three-layer-memory-retrieval.md` | ✅ `[DEPRECATED]` 已标 | `epic-5/LITE-5-7.md`（待写） |
| `epic-4/4-11-irt-difficulty-callout-exam.md` | ✅ `[DEPRECATED]` 已标 | sprint-status entry 描述够（IRT 砍） |
| `epic-5/5-4-scoring-chain-integrity.md` | ✅ `[DEPRECATED]` 已标 | sprint-status entry 描述够（顺序调用） |
| `epic-5/5-5-error-classification-dual-write.md` | ✅ `[DEPRECATED]` 已标 | sprint-status entry 描述够（single-write） |

⚠️ **新 session 启动 step 5 必检** — 读 Story spec 时如发现 `[DEPRECATED]`/`[MERGED]` marker → halt + 查 sprint-status 的 `supersedes` 字段找对应 Lite spec 或 entry。

---

## §99 · 历史活跃计划（Sprint v3 之前的 EPIC 1 v2 BMAD 开发，参考留底）

### EPIC 1 v2 BMAD 开发就绪（2026-04-17）
- [x] 前置 1: sprint-status.yaml 更新（旧 v1 归档，新 13 Story 注册为 ready-for-dev）
- [x] 前置 2: 高风险 Story deviation notes 对齐（1.1 dashboard-interactive-ui CONFIRMED / 1.2 paradigm 切换已记录 / 1.3 context-assembly-paradigm CONFIRMED）
- [x] 前置 3: obsidiantools>=0.10 添加到 requirements.txt
- [x] Story 1.7 (root-env-docker-compose) — ✅ review (13/13 tests, all AC satisfied)
- [ ] Story 1.1 (vault-init-templates) — 核心 Story，依赖 1.7 流程经验

### 已闭合 OpenSpec Changes（archived 2026-04-07）
- [x] **fix-rag-faithfulness-and-add-crag-quality-loop**
  - 3 个新 contract 合并进 `openspec/specs/algo-rag/spec.md`（Faithfulness/Fusion/CRAG）
  - 88/88 测试绿（85 baseline + 3 surrogate）
- [x] **fix-rag-transform-and-episode-isolation**
  - 4 个新 algo-memory + 3 个新 algo-rag requirements 合并进主 spec
  - 64/69 tasks（5 deferred 手动 e2e/压测/doc-review）
  - 17 个新单元测试通过，零回归
- [x] **fix-fr-kg-04-schema-drift-and-sync-hardening**
  - 25 个新 requirements 合并进 5 个新主 spec：algo-question(5) / algo-scoring(1) / canvas-sync(12) / llm-safety(5) / verification-service(2)
  - 127/160 tasks（33 deferred 手动 e2e/前端 smoke）
  - 同批 `git rm -r openspec/changes/fr-kg-04-sync-pipeline-fix/`（SUPERSEDED）
- [x] **fix-structlog-caplog-compat**
  - 6 个新 requirements 合并进新主 spec backend-logging
  - structlog ↔ stdlib 双向 bridge 落地，消除 196 个测试失败/error
- [x] **fr-kg-04-isolation-and-retrieval-tightening**（commit e6971d7）
  - 4 reqs added to algo-rag + 1 req to new repo-compliance capability
  - FR-KG-04 读端闭环：Cypher group_id 隔离 + cache key + cross_canvas fail-soft + vault_notes 多 vault + LICENSE 合规
  - 41/43 tasks（2 deferred docs/smoke）
- [x] **fr-kg-04-prompt-injection-and-auth-completion**（commit e6971d7）
  - 3 reqs added to llm-safety
  - LLM 安全闭环：API key 鉴权扩展 + context 降权 + meta 规则 + 50 case 对抗性测试
  - 37/39 tasks（2 deferred commit/PR），6 LLM 安全风险全闭环
- [x] **agentic-rag-l1-llm-router**（commit e6971d7）
  - 创建新 capability agentic-rag（3 reqs）
  - L1 路由 LLM 化：rule-based → Gemini Flash
  - 45/52 tasks（7 deferred 手动 GEMINI_API_KEY 验证）
  - 核心代码已在 commit 3b96e49 落地
  - Archive 时修正 delta header bug：`## MODIFIED → ## ADDED Requirements`

### 仍进行中的 OpenSpec Changes（仅 2 个）
- `review-enrichment-signal-fix` — 3/4 artifacts（缺 design.md），endpoint wiring 是死代码路径需独立 follow-up change
- `trackpad-pan-support` — 3/4 artifacts，specs/ 缺 delta 定义（OpenSpec validation fail），需补 delta

### 唯一待修 known-gotcha
- **G-SILENT-001** endpoint wiring：`backend/app/api/v1/endpoints/review.py:788` `generate_verification_canvas` 需内联 enrichment_available

### 已修复统计（2026-04-07 截止）
- 本 session 累计 commits：51f2057（structlog bridge）+ 0b477f0（archive 3）+ 74a09f3（spec consolidation）+ b50a089/19a111e/221d8a7（test/docs/gitignore）+ e6971d7（archive 3 ready changes）
- 主 spec capabilities：5 → 14（+9 个新 capability：algo-memory / algo-question / algo-scoring / canvas-sync / llm-safety / verification-service / backend-logging / agentic-rag / repo-compliance）
- 测试基线（Stage 2 完成时）：137 failed / 17 errors / 2471 passed（vs pre 202F/87E/2410P，净 +196 改善）
- known-gotchas: 37 总 / 32 已修 / 4 保留 / 1 待修

## 历史活跃计划（已完成或停滞，留作参考）

### 历史 Phase 1 — MagicMock → 真实数据库测试（已结束）

**结束状态**：基础设施全部就位，原始 Step 3 目标文件已被后续 PR 重命名/重构。详见：
- [x] Step 0: docker-compose 添加 neo4j-test 容器（端口 7692）— commit 3a167e9
- [x] Step 1: conftest.py 修复端口 + neo4j_available + neo4j_test_session — commit 3a167e9
- [x] Step 2: DD-03 hard hook (mock-import-guard.js) — commit 0cb8cf8
- [-] Step 3: 原计划的 test_neo4j_client.py / test_graphiti_client.py / test_memory_persistence.py 已被 fix-fr-kg-04 系列 PR 吸收/重命名，不再有独立目标
- 158 个 unit test 文件中 104 个仍在 mock，留给后续根因 A 清理 change（MagicMock → AsyncMock sweep）

## 后续 Phases（不在当前范围）
- Phase 3: MagicMock → AsyncMock sweep（根因 A，~30 min sed 可解决 ~85F+60E）
- Phase 4: pytest-mock 缺失（根因 D，trivial）
- Phase 5: 修复 6 条断裂管道（G-PIPE）
- Phase 6: 功能质量提升（假评分→真 LLM、异常精确化）
- Phase 7: 产品记忆 KA-RAG 接通
