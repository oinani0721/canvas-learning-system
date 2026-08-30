Reading additional input from stdin...
OpenAI Codex v0.147.0
--------
workdir: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
model: gpt-5.6-sol
provider: openai
approval: on-request
sandbox: read-only
reasoning effort: ultra
reasoning summaries: auto
session id: 01a04814-e1ef-7a50-984f-31f7236c88ad
--------
user
CARD-G4-9 round-3 复审（静态审阅 + 只读复算）。你 round-2 裁定 10/13 CLOSED，三项 NOT-CLOSED：BLOCKER-1（--out 守卫比 resolve 字符串，hardlink 与 case-only 别名绕过截断输入）、HIGH-1（full_body_verified 只核 sha 不核长度且排在 anomaly 分支前，anomaly 记录被判 byte_exact）、HIGH-3（chmod 000 根 exit 0 假判 unrecoverable；glob 跟随 symlink 逃逸出根）；另 3 新 LOW（full_verified 长度范围应 131-180、distribution 省略 0 值键、line_count 数 LF 与 records 的 splitlines 口径不一）。开发方以 commit 73102875 提交整改。请只读复核这 6 项是否闭合：
脚本 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py 现改为：(a) 碰撞守卫比较文件身份 (st_dev, st_ino) 并保留 resolve 路径比较；(b) full_body_verified 增加 len(full)==declared_len 门，且判定链改为 state != 'anomaly' 前置；(c) transcripts 根增 os.access(R_OK|X_OK) 检查 exit 2，glob 结果排除 os.path.islink 条目并要求 realpath 落在根内；(d) line_count 改用 splitlines()，class/recoverability distribution 补零并新增 inline_state_distribution。
报告 _bmad-output/审查/G4-9-DLQ-census-2026-08-28.md 新增 §7c 段与 §7 负例门行；台账 _bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json 已用整改版重生成。
请：逐项 CLOSED/NOT-CLOSED（对每项设计静态反例判断是否仍可绕过，如相对路径/大小写/软硬链接组合、判定链其它入口、glob 边界）；独立复算台账仍为 92 条 / class 89-2-1 / 三态 4-88-0 / 重复簇 6 簇 29 行 / full_verified 长度 131-180；给总裁定（可验收/仍阻断）与任何新发现分级。
**Planning read-only audit approach**
**Assessing read-only script execution constraints**
**Verifying availability of custom audit skill**
codex
我会按 round-2 的六个未闭合/新发现逐项做敌对复审，并把“代码门是否成立”和“现有台账是否独立复算一致”分开。全程只读；我会并行检查守卫与路径边界、分类判定链，以及原始记录→台账/报告的数值绑定。
**Investigating memory skill availability and tools**
**Planning sequential memory extraction**
exec
/bin/zsh -lc "rg -n -i 'CARD-G4-9|G4-9|DLQ|dead.?letter|census|round-2|73102875|card-s5-census' /Users/Heishing/.codex/memories/MEMORY.md" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
84:- Missing handoff is a hard wait condition, not implied approval. `ps` was sandbox-denied (`operation not permitted`); mark the census unavailable rather than successful. [Task 1]
144:- “只读” means no repo/index/ref/worktree/OpenSpec writes, scanner/final census, A01/A02 instantiation, private/Vault/network/Graphiti access, or product implementation. Provide ready/blocked status, exact evidence, batch order, and Claude/Codex matrix. [Task 1]
148:- Order: `GOV-01-VERIFIED clean candidate → OpenSpec → schema/checker → A01 boundary receipt → no-cap census/A01 snapshot → A02 seed/replay → ChatGPT blind review → Codex reconciliation → user dispute/waiver → joint A01/A02 completion → A03 candidate → user exact-byte lock`. A01 cannot complete independently of A02. [Task 1]
153:- Expired `pending-user-confirmation` receipt/envelope is not authority. New exact envelope/digest/challenge is needed. The existing `scripts/bmad/scan_feedback.py` did not cover actual output; freeze a new scanner contract/no-write boundary before census. [Task 1]

**Confirming memory citation necessity**
**Reviewing adversarial audit skill usage**
codex
我会沿用该项目既有的 Canvas 敌对审计规程来固定证据口径（生产入口、可复现实例、`file:line`、PASS/PARTIAL/FAIL），但不会访问 Vault、网络或改动任何文件。当前没有可调用的 Graphiti 工具，因此本轮不能执行其搜索协议；这不影响对本地 exact bytes 的只读复算。
**Planning skill file inspection**
exec
/bin/zsh -lc "rg -n -i 'canvas-adversarial-audit|adversarial security review|real-entrypoint' /Users/Heishing/.codex/memories/MEMORY.md" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
155:# Task Group: Canvas Learning System P1-05/P1-01/P1-08 adversarial security review
186:- Related skill: skills/canvas-adversarial-audit/SKILL.md. P1-05/P1-01/P1-08 remained STILL-OPEN; F-02 tombstone filtering and F-05 live resilience were closed. Rejected vault inputs must show zero open/hash/index/write. [Task 1][Task 2]

exec
/bin/zsh -lc "wc -l /Users/Heishing/.codex/memories/skills/canvas-adversarial-audit/SKILL.md && sed -n '1,240p' /Users/Heishing/.codex/memories/skills/canvas-adversarial-audit/SKILL.md" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
      50 /Users/Heishing/.codex/memories/skills/canvas-adversarial-audit/SKILL.md
---
name: canvas-adversarial-audit
description: Conduct a read-only, parallel, evidence-first adversarial audit of Canvas P1 closure claims, especially vault admission, Graphiti quarantine, and SnapshotV3.
argument-hint: "[task-book path or P1 scope]"
user-invocable: false
allowed-tools: Read, Grep, Glob, Bash
---

# Canvas adversarial audit

## When to use

Use for a user-requested adversarial or closure audit in the Canvas Learning System worktree, particularly P1-05/P1-01/P1-08. Do not use to implement fixes, access prohibited raw-vault content, or declare a historical finding current without revalidation.

## Inputs / context to gather

1. Read the task book, `AGENTS.md`, worktree topology, allowed/prohibited paths, and reporting contract.
2. Record checkout SHA, branch, WT/MAIN labels, current `CURRENT_TASK.md`, and requested P1 claims.
3. Identify actual production entrypoints, not merely the tests that claim to cover them.

## Procedure

1. Split independent tracks: vault admission/indexing and tests; Graphiti quarantine/retrieval; SnapshotV3/recovery anchors. Keep the audit read-only.
2. For each claim, build an evidence matrix: claim, `file:line`, adversarial input/state, actual entrypoint/path, observed result, severity, PASS/PARTIAL/FAIL, and limitations.
3. Directly exercise real entrypoints with temporary fixtures where permitted. For path admission include symlink, directory symlink, blacklisted filename in an allowed directory, case variant, and nonexistent path. Assert rejected inputs perform zero open/hash/index/write.
4. For quarantine, test ordinary edge search plus node search and exact-reader paths (`search_nodes`, `read_node_tips`, `read_node_errors`, `read_node_edge_reasons`). Use read-only Neo4j queries and `EXPLAIN` where allowed; distinguish observed metadata exposure from unproven fact-body leakage.
5. For SnapshotV3, test same-generation invalid/future version self-healing, extra fields, strict typing, huge finite values that may produce NaN/Infinity, and identity/length collision boundaries.
6. Compare recovery anchors with machine facts: current HEAD, Actions status, test counts, and unresolved findings. Separate targeted-test results from whole CI.
7. Cross-check high-severity findings independently. Write the final matrix before closure language; explicitly retain `UNVERIFIABLE` items and failed counterexample attempts.

## Efficiency plan

- Start from task-book source handles and `rg` for real call sites; cache the entrypoint map for all tracks.
- Parallelize independent tracks, then have the primary reviewer re-open only high-severity evidence.
- Stop treating a test as evidence once it only hits source text, a helper, fake client, `__new__`, or monkeypatch; pivot to the real entrypoint.

## Pitfalls and fixes

- Green tests but unsafe closure -> tests do not reach production behavior. Add direct entrypoint fixtures and capture full stdout/trace before an assertion.
- `session:` IDs used as provenance -> ID shape alone is not proof. Preserve provenance or report PARTIAL.
- Quarantine count passes -> exact-reader/node-search surfaces may still cross groups. Test those surfaces specifically.
- `CURRENT_TASK.md` says closed but anchors disagree -> rebuild anchors from current HEAD, Actions, and unresolved findings.

## Verification checklist

- Every finding has `file:line`, reproduction, severity, result, and claim-conflict explanation.
- Final report labels WT/MAIN and all verification limits; no prohibited files or raw vault were read.
- Production entrypoints, not only helpers, were tested for each security claim.
- CI status is reported as whole-workflow status, not only passing targeted jobs.
- P1 closure is withheld whenever a reproducible bypass or unverified critical surface remains.

**Planning code line inspections**
exec
/bin/zsh -lc "nl -ba /Users/Heishing/.codex/memories/MEMORY.md | sed -n '150,190p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
   150	
   151	## Failures and how to do differently
   152	
   153	- Expired `pending-user-confirmation` receipt/envelope is not authority. New exact envelope/digest/challenge is needed. The existing `scripts/bmad/scan_feedback.py` did not cover actual output; freeze a new scanner contract/no-write boundary before census. [Task 1]
   154	
   155	# Task Group: Canvas Learning System P1-05/P1-01/P1-08 adversarial security review
   156	scope: Read-only, parallel audit of vault admission/indexing, Graphiti quarantine isolation, SnapshotV3, and recovery-anchor closure claims.
   157	applies_to: cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output; reuse_rule=revalidate SHA, CI, actual call sites, and live Neo4j state in the target checkout.
   158	
   159	## Task 1: P1-05c/P1-01/P1-08 parallel adversarial review, closure rejected
   160	
   161	### rollout_summary_files
   162	
   163	- rollout_summaries/2026-08-17T01-56-07-ZNCd-agents_guide_and_p1_05c_adversarial_audit.md (cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output, rollout_path=/Users/Heishing/.codex/sessions/2026/08/17/rollout-2026-08-17T09-56-07-01a00d6e-ea40-70a1-a23c-d51342eeeacd.jsonl, updated_at=2026-08-19T17:56:56+00:00, thread_id=01a00d6e-ea40-70a1-a23c-d51342eeeacd, outcome=partial; final read-only verdict)
   164	
   165	### keywords
   166	
   167	- P1-05c, P1-05, P1-01, P1-08, check_vault_path, vault_index_orchestrator, LanceDB, Graphiti, DEFAULT_GROUP_ID, SnapshotV3, CURRENT_TASK.md
   168	
   169	## Task 2: P1-05b five-question adversarial audit, reproducible bypasses
   170	
   171	### rollout_summary_files
   172	
   173	- rollout_summaries/2026-08-19T14-44-08-upza-p1_05b_adversarial_review_finds_admission_quarantine_snapsho.md (cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output, rollout_path=/Users/Heishing/.codex/sessions/2026/08/19/rollout-2026-08-19T22-44-08-01a01a7a-c47f-70e2-8e5e-524e1591da78.jsonl, updated_at=2026-08-19T15:12:50+00:00, thread_id=01a01a7a-c47f-70e2-8e5e-524e1591da78, outcome=partial; detailed counterexamples)
   174	
   175	### keywords
   176	
   177	- P1-05b, symlink_escape, casefold, vault_backfill, lancedb_client, quarantine__p105b, search_nodes, read_node_tips, manifest-v3, NaN
   178	
   179	## User preferences
   180	
   181	- “启动并行 agent 进行对抗性审查” -> use independent evidence tracks and cross-check severity; every finding needs `file:line`, reproduction path/result, severity, conflict explanation, PASS/PARTIAL/FAIL, and limits. [Task 1][Task 2]
   182	- Respect read-only task-book boundaries, WT/MAIN labels, explicit `UNVERIFIABLE`, and no raw-vault access; do not fix code in the audit. [Task 1]
   183	
   184	## Reusable knowledge
   185	
   186	- Related skill: skills/canvas-adversarial-audit/SKILL.md. P1-05/P1-01/P1-08 remained STILL-OPEN; F-02 tombstone filtering and F-05 live resilience were closed. Rejected vault inputs must show zero open/hash/index/write. [Task 1][Task 2]
   187	- Reproduced: `vault/raw/escape.md -> /outside/secret.md` was counted by `backfill_vault(..., execute=False)`; case-sensitive `fnmatch` admitted `.CLAUDE/SKILL.md` and `raw/claude.md`. Edge filtering alone was insufficient because exact readers/node search could cross Graphiti groups. [Task 2]
   188	- SnapshotV3 needs invalid/future same-generation self-healing, extra-field, strict-type, huge finite mastery, and identity/length collision coverage. [Task 1][Task 2]
   189	
   190	## Failures and how to do differently

**Planning multi-agent audit workflow**
**Defining read-only agent execution**
按敌对审计规程，将代码门、原始数据复算、报告绑定和最终交叉核验分开；全程只读。
  → 锁定 checkout/commit、范围与 round-3 变更证据
  • 并行审阅六项修复的静态绕过面
  • 从原始 transcripts 独立复算台账指标并核对报告
  • 交叉核验高严重度项并给出逐项与总裁定
**Planning compact internal strategy**
mcp: sequential-thinking/sequentialthinking started
mcp: sequential-thinking/sequentialthinking (completed)
**Planning parallel git and file inspections**
exec
/bin/zsh -lc 'git rev-parse HEAD' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
73102875fdd9837f0d60cf2ed6cf4ea7f6f8c2e5

exec
/bin/zsh -lc 'git show --no-ext-diff --stat --oneline --decorate --no-renames 73102875' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
exec
/bin/zsh -lc "rg --files -g 'AGENTS.md' -g 'CLAUDE.md' -g 'CURRENT_TASK.md' -g '.claude/rules/*.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
73102875 (HEAD -> card/s5-census) fix(census): G4-9/G4-16 Codex round-2 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9 / CARD-G4-16]
 .../G4-16-doc-type-census-2026-08-28.md"           |  21 ++++-
 .../G4-16-evidence/after-edits.txt"                |   2 +-
 .../live-distribution-and-value-grep.txt"          |   6 ++
 .../G4-16-evidence/test-run-metadata.txt"          |  14 ++-
 .../G4-9-DLQ-census-2026-08-28.md"                 |  16 +++-
 .../G4-9-dlq-ledger-2026-08-28.json"               |  13 ++-
 .../G4-9-evidence/grep-selfattest.txt"             |  46 ++++++----
 .../codex-review-CARD-G4-16-round2.md"             |  33 +++++++
 .../codex-review-CARD-G4-9-round2.md"              |  37 ++++++++
 ...\272\277\346\231\256\346\237\245-2026-08-28.md" |  10 ++
 ...75census\345\210\206\350\257\212-2026-08-28.md" |  13 +++
 backend/app/services/supplementary_reranker.py     |   6 +-
 backend/scripts/census_dead_letter_episodes.py     | 101 +++++++++++++++++----
 13 files changed, 264 insertions(+), 54 deletions(-)

 succeeded in 0ms:
CLAUDE.md
CURRENT_TASK.md
canvas-vault/CLAUDE.md
_decisions/CURRENT_TASK.md

exec
/bin/zsh -lc 'git status --short --branch' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
## card/s5-census
?? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-16-round3.md"
?? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round3.md"

**Inspecting CLAUDE.md and diffing files**
codex
已锁定当前 `HEAD=73102875fdd9837f0d60cf2ed6cf4ea7f6f8c2e5`，正是待复审提交。工作树另有两个未跟踪的 round-3 审阅文件；它们不属于本轮证据，我不会读取为结论来源、也不会改动。现在分三轨并行复核。
**Deciding to avoid untracked data**
**Inspecting relevant task rules and diffs**
exec
/bin/zsh -lc "sed -n '1,260p' CLAUDE.md" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
# CLAUDE.md — Canvas Learning System

## 项目

Tauri 2 + React + TypeScript + FastAPI + Neo4j + LanceDB 桌面学习应用。
前端: `frontend/src/`。后端: `backend/app/`。Sidecar: `frontend/sidecar/`。

## 硬规则（Hook exit 2 确定性执行，违反 = 阻断）

1. **DD-03 禁 mock** — 禁止假 API/模拟数据/TODO 空函数。PreToolUse hook 检测 mock 模式并 exit 2 阻断
2. **DD-12 范围约束** — frontend agent 只改 frontend/，backend agent 只改 backend/。PreToolUse hook exit 2 阻断
3. **DD-13 名实一致** — 函数名必须匹配实际行为。PreToolUse hook 检测名称-导入不匹配并 exit 2 阻断
4. **DD-14 追踪链** — Plan 步骤打勾 + commit 含 PLAN-NNN + /clear 前更新 CURRENT_TASK。详见 `.claude/rules/plan-traceability.md`

> 其余 DD 规则详见 `.claude/rules/development-discipline.md`（自动加载）

## 工作流（Boris 模式）

1. **Plan Mode 先行** — 多文件/多技术任务必须先进 Plan Mode（Shift+Tab×2）读代码+提问+产出计划
2. **设计先于代码** — 创建功能前，先问清楚需求，提出 2-3 种方案，用户确认后再写代码
3. **增量提问** — 不确定就问用户。技术决策用用户能听懂的语言解释
4. **验收步骤** — 代码修改后提供最小验收步骤（启动→操作→预期看到什么）

## Graphiti 协议

- **MCP**: `graphiti-canvas`（group_id 命名规约见下方 §Story 2.5.Y）
- **搜索**: 每轮 `search_memory_facts(exclude_invalidated: true)`。需要精确结果时用 `center_node_uuid`
- **记录**: 决策记 `[Decision]`，审查记 `[Code-Review]`，不确定→记录
- **搜索模式**: 默认 `rrf`。审计用 `mmr`(去重)。精确查询用 `cross_encoder`

### Graphiti group_id 命名规约（Story 2.5.Y D16 锁定 2026-05-05）

**新格式（所有新写入必须用此）**:
- `vault:<vault_id>` — 单 vault（`vault:cs_61b` / `vault:数学`）
- `vault:<vault_id>:<subject_id>` — vault 内学科二级（`vault:cs_61b:algorithms`）
- `vault:<vault_id>:<canvas_name>` — vault 内 canvas 二级（`vault:cs_61b:admissibility`）

**构造**: 调 `backend/app/core/subject_config.py::build_vault_group_id(vault_id, subject_id, canvas_path)`

**Cypher 查询防御**: 必须用 `backend/app/utils/cypher_helpers.py::cypher_with_group_filter()`（防忘传 group_id 跨 vault 泄漏）

**已弃用格式**（仅 read-only 兼容历史数据，新写入禁用）:
- `cs188`（config.py 默认，Story 2.5.Y AC #3 改为 deprecated fallback + warning）
- `canvas-dev`（旧 CLAUDE.md 全局默认，已替换）
- `cs_61b:main`（Story 1.9 推断格式，仅历史数据保留）

**迁移**: 旧 group_id 数据由 `backend/scripts/migrate_group_ids.py` 迁移到新格式（Task 6 dry-run 测试就绪）

## MCP 工具

- **Sequential Thinking**: 复杂推理/多步骤/解题 → 必须调用
- **Context7**: 查库/框架/API 文档 → 先查文档再写代码
- **LSP**: 编辑代码后查 diagnostics

## 测试

- 后端: `pytest`（80+ 测试文件已就绪）
- 前端: `vitest` + `@testing-library/react`
- Hook 会在代码编辑后自动运行相关测试

## 已知问题

详见 `docs/known-gotchas.md`（20 条，12 待修）。重点关注:
- G-FAKE: 42+ 假命名函数（名称含 graphiti 但实际调 Neo4j）
- G-PIPE: 6 条断裂管道（已实现但无调用方）

## 风格参考文件

修改代码前先读对应的参考文件：
- 后端 service: `backend/app/services/rag_service.py`
- 后端 router: `backend/app/api/v1/endpoints/canvas.py`
- 前端 state: `frontend/src/stores/chat-store.ts`
- 前端组件: `frontend/src/components/ChatPanel.tsx`

## Bug 修复规则

- 复杂 bug（多文件）必须先分析根因，用户确认方案后再修
- 禁止一次修复混合多个不相关变更
- 修复后必须跑测试：`.venv/bin/pytest tests/ -x -q`
- 批注追踪清单: `docs/project-status/annotation-tracker.md`

## OpenSpec 工作流（Hybrid — CLI 强制结构 + Claude 填内容）

从 2026-04-06 起，所有**新**的 OpenSpec change 必须走 CLI 流程：

1. **创建**：`npx openspec new change <kebab-name>` —— 禁止手动 `mkdir` 或复制现有目录
2. **获取模板**：`npx openspec instructions <artifact-id> --change <name> --json` —— 每个 artifact（proposal/design/specs/tasks）单独跑
3. **填内容**：Claude 按 template + config.yaml 的 context + rules 填文件
4. **校验**：`npx openspec validate <name> --strict` —— 失败即重写
5. **状态**：`npx openspec status --change <name>` —— `Progress: 4/4 artifacts complete` 才算 apply-ready
6. **归档**：`npx openspec archive <name>` —— 禁止 `git mv`，归档命令会自动合并 delta 到主 spec

### Proposal 格式硬约束（CLI schema 要求）

- `## Why`（必需，不能用 `## What & Why` 之类的变体）
- `## What Changes`（必需）
- `## Capabilities`（可选但推荐）
- `## Impact`（可选）

### Specs 格式硬约束

- 每个 capability 一个文件：`specs/<capability>/spec.md`
- Delta 头部：`## ADDED Requirements` / `## MODIFIED Requirements` / `## REMOVED Requirements`
- 每个 requirement 必须至少 1 个 scenario
- Scenario 头部**必须**是 4 个 hashtag（`#### Scenario:`）—— 3 个会静默失败
- 语法：`### Requirement: <name>` + SHALL/MUST 描述 + `#### Scenario: <name>` + WHEN/THEN

### 历史债（legacy changes）

3 个 CLI 安装前手写的 change（`fr-kg-05-recommendation-mvp`, `trackpad-pan-support`, 以及 validate 失败的部分 `fr-kg-04-sync-pipeline-fix`）缺 `specs/` 目录，无法通过 `openspec archive`。这些 change 需要在真正归档前回填 specs，否则 `openspec/specs/` 下的主 spec 永远不累积。

### 为什么是 Hybrid 而不是 Only CLI

CLI 负责**结构 + 校验 + 归档**，Claude 负责**内容写作**。Boris 工作流（Plan → Design → Confirm → Execute）与 CLI 零冲突。

## 锚定文档（Read-Only）

- `/Users/Heishing/Desktop/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md` — PRD v5，唯一真相源
  - Claude 只能 READ，不能 Edit/Write（`pretool-guard.js` hook 强制阻断）
  - 用户手动批注 §12 决策区（D1-D14）
  - 所有 OpenSpec change 和 Claude plan 必须在头部引用对应 § 章节
  - 引用格式：`> **From PRD**: §X [标题] (line YYYY-ZZZZ)`

## 项目文档

- 架构: `docs/architecture.md`
- MVP 刚需: `_decisions/mvp-plan.md`（14 项 + 用户批注）
- 决策索引: `_decisions/decision-log.md`
- 前端组件: `docs/component-inventory-frontend.md`
- 后端 API: `docs/api-contracts-backend.md`
- **Gap Analysis**: `docs/project-status/gap-analysis.md`（99 FR + 用户批注）
- **批注追踪**: `docs/project-status/annotation-tracker.md`（108 条分类追踪）
- **进度报告**: `docs/project-status/s40-progress-report.md`
- **OpenSpec**: `openspec/config.yaml`
- **BMAD 实施**: `_bmad-output/implementation-artifacts/` — Story spec（AC + Tasks）+ 审计报告

exec
/bin/zsh -lc "sed -n '1,240p' CURRENT_TASK.md" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
# CURRENT_TASK: Canvas Learning System × Obsidian Hybrid（回归路径）

> **前 15 行是 Clear Context 后的恢复锚点 — 必须自包含**

**本车道状态**（2026-08-27 · 分支 `card/n5-split` · BATCH-2026-08-27-第四批 车道 5 · **G5-1 + G5-2 双卡 v3（Codex 三/四轮对抗后）待验收**）:
- ✅ CARD-G5-1 触发矩阵 v3：矩阵文档（15 正例含 5 用户逐字 + 10 负例 + 语料覆盖自陈 + §三 待拍板 + **§五 登记簿 4 条**）
  + checker v3 9/9（real_floor 代码锚+归属锚语义分类；18 类变异负控全抓）+ headless 三轮全量重放（judge v3：
  sidecar 绑定/终局唯一/manifest 含 .claude/skills）：**⛔ N4「回顾一下+板名」无斜杠存档 2 采样 1 次真触发 board-recap**
  （最重要发现，直接喂 §三 拍板）+ N6 误触发全局 study-plan（2/2 复现）+ N2 代行写侧 + B2 形式化漂移（存档 5 份 2/3）
- ✅ CARD-G5-2 拆分 preview 引擎 v3：split_preview.py（写侧物理 fail-closed 次序修正+单FD / 目录级 symlink containment /
  slug JS空白集+UTF-16 边界+偏差5声明）+ 裁判 34 条四轮先红后绿（含剥离反事实常驻测试）+ live 全 324 文件全字段
  基线零净差异（set -x 回放+引擎字节绑定, `审查/g5-2-evidence/`）
- Codex：G5-1 三轮（1 轮 3B+4H → 2 轮复核 → 3 轮终核）；G5-2 四轮（cyber误拦→6H→复核→终核）全存档
- 验收单：`验收单/UAT-CARD-G5-{1,2}-*.md`；**不 push**
- ⛔ 待用户：①验收两单 ②拍板 R8 口令取舍（G5-8 前必裁, N4 实证必读）③语料覆盖自陈口径认可（C/D 类无真实触发语,
  总账「各≥3 真实正例」硬门 vs 语料实况的裁决权在用户）④outputs/ 测试产物未入 commit

---

**当前状态**（2026-08-20 · **Codex 四轮拒绝收官 → 九路验证 9/9 CONFIRMED → C1-C4 修复批全部落地，五轮送审就绪** · 最近完成的产品提交 `c154a7f2`(C1 真实入口准入) · PLAN `R11-BATCH2-2026-08-17`。⚠️ 锚点纪律：①不记累计 commit 数 ②不落盘 CI run 号/通过数（连续两轮落盘即过期被抓——CI 状态以 `gh run list --limit 3` 实查为准）③收官状态由外部复核裁定不由施工方自宣）:
- 🔴 **下一步执行顺序（用户 2026-08-19 裁定，逐项独立提交独立验收，禁止合并成大返工）**：
  **① P1-05 第四轮返工（P1-05d）已落地，待五轮终裁** — Codex 四轮（`2026-08-19` 终裁文档）判 F-02/F-05 CLOSED、其余 STILL-OPEN；九路验证（`2026-08-20-Codex四轮终裁-九路验证与C批次方案.md`）9/9 CONFIRMED 含 B3 新回归一条。C 批全部落地：**C2**（`1683328c`：脏 last_examined 投影 None 止血 B3 新回归 · freshness 嵌套错型自愈 · 5 处 ID 切片改丢弃 · _id_ok 写侧过滤同源 · lag_seconds finite · 控制字符全拒）· **C3**（`d39983ce`：conversation_summary caller 显式传 vault 组修恒空 bug · ensure_entity_node 隔离身份拒绝复用）· **C1**（`c154a7f2`：lib 层 _resolves_outside_vault 接 LanceDB 两真实入口 open 前 · orchestrator 裸 fnmatch 换 canon + 扫描产出过 should_index 根除 hash-before-admission + realpath containment · by-node missing→404/path_rejected→422；新 test_real_entrypoint_admission.py 6 条真实入口行为锁）· **C4**（census Q2 中性化+前缀分类）。**遗留**：B4（payload 命名空间/provenance）独立轮 · TOCTOU 换链残余窗口（realpath 判定与 open 非原子，诚实登记）· P1-03/P1-04 押后
  **② P1-01 快照安全 — SnapshotV3+B3+C2 全部落地，⛔ 收官待 Codex 五轮裁定**（四轮三反例已修：同代伪造死区→写侧全量 validate 自愈 · 根[]与嵌套 freshness=[] 双防御 · strict 契约+ID 拒绝不截断+丢条目不丢整包；四轮新发现三洞 V3/V4/V5 已在 C2 闭合并有反例锁）。已知完整性余量（Codex 登记）：同 generation 且 schema 合法的数值篡改可通过 validator——validator 证形状不证来源，归 B4 provenance
  **③ P1-03 + P1-04 合并做**（不许先改 degraded 以后再补测试）— 返回值改明确状态枚举 `ok/empty/degraded/unavailable`，原因写入 `CanvasRAGState` 并验证 API/trace 可见；MemoryService 内部异常返回 `[]` 被判成「真没记忆」的吞噬点必须堵。**验收门**：真实 Neo4j 或真实不可达端点覆盖成功/空结果/故障/fallback 四态；`test_story_2_3_error_reminders.py` 那 5 个相邻失败**属于新链依赖（node 过滤与 schema），不得归为无关旧账**
- ⚠️ **Codex 二轮复核（`_bmad-output/审查/2026-08-19-Codex对抗审查-R11返工反馈进一步复核.md`）判 P1×8 + P2×3。已修 3 条（`0acefe1b`）**：P1-02 我上一轮的 group 层级传错（写基组读子组 overlap=∅，"修复"召回仍恒空）· P1-06 fallback 只挡语法不挡 schema（`[]`→崩溃、`{}`→旧值 5 从 `get_max_references` 默认参数泄漏）· P1-07 部分（4 个新契约锁根本不在 CI，测试清单 5→9 文件）。**剩余未闭合 = ③ P1-03/P1-04（用户裁定押后）+ B4 payload 命名空间（独立一轮）+ P1-07 剩余（5 个未豁免 CVE、required checks）+ P2-01 generation 可倒退；①② 的收官判定权在 Codex 四轮复核**
- 📊 **CI 状态（⛔ 不落盘 run 号/通过数——以 `gh run list --limit 3` 实查为准）**：定性事实=Tests 双版本绿（含本轮 +5 契约文件：snapshot_v3/hostile_env/tombstone/vault_admission/real_entrypoint）· **Dependency Audit 红**（5 个未豁免 CVE，pillow 修复被 moviepy `<12.0` 卡住）→ 整体 failure · branch protection 404 未设置、rulesets 空 — required checks 前提不满足
- ✅ **已交付且经复核确认通过的**：compose 地雷 6 份处置 + 权重三方 md5 一致 · A-9/A-4 索引边界（含根级 casefold 精确排除、深层同名保留）· E-2 快照脱敏投影（缺版本/v1 且结构正常者强制迁移 + 原子发布不产生半截 JSON）· 配置缺文件/语法损坏不再回旧方向性权重 · CI 失败传播（两次远端红灯验证）· D-2 重数 92 条 + 无自动 replay consumer · A-1 语义死链改指 08-02 文档 §施工顺序与工期
- ⚠️ **已知不实表述已撤**：不是「T1-T7 全完成」（E-3 产物丢失，经裁定移出验收范围）· D-2 根因**不是**"16998/正文撑爆"而是 schema/prompt 固定开销拟合截距 ~16861 已超 16384 窗口（分片对 71/89 条无效）· mastery 契约锁现为 **12 条**非 8 条 · 「92 条永久搁浅」应表述为「无自动出口，人工可恢复性未知」（未验证原始来源仍可取）
- 📋 **其它遗留**：~~重写 `test_memory_service_contextvar_leak.py`~~（✅ BATCH-2026-08-25 / CARD-C6 已按 `_vault_scoped_group_id` 新契约语义重写 + collect_ignore 回收 + 入 CI 显式清单）· 全量 tests/ 跑不完的根因（本地串行 1h03m 未完）+ xdist 收集不确定性 · 四个休眠 worktree 的 `docker-compose.yml` 仍为未提交 `M`，待收回 · A-8 授权与 E-3 移出范围仅记录在 `0ff6876c` 新增文档中，**仓库无法独立验证**（Codex 裁为 UNVERIFIABLE，需用户本人确认闭合）· 主仓 `2c5a4683` 混入 `session-end-archive.py`（已裁定不修正历史）
- ⚠️ **开工前必读**：① 动 board manifest 快照时注意 `write_snapshot_if_changed` 内已有 `_project_for_snapshot`，**不要在 `full` dict 上就地改**（`:716` 契约：live 与快照共用同一 state）② mastery 的 `_search_via_memory_service` 是 **vault 级语义补充召回、不是 node 精确读**（Tier1 映射已丢弃 attributes/node_id）；真正的精确读是 `graphiti_memory_reader.py` 的 `read_node_tips`/`read_node_errors`，但需要 `CanvasRAGState` 里没有的真实 node_id ③ 扩 CI 覆盖面前先解决「全量测试跑不完」，别直接加文件

**上一状态**（2026-08-17 · **R10 复审 11 项 (P0×1+P1×6+P2×4) 全部处置完毕 · 收官门解除 · 8 commits + 真实 Neo4j 验收门 6/6 + 证据包落盘** · PLAN `P0-SYNC-ISO-2026-08-17`）:
- ✅ **R10 复审处置全清**（回应文档 `_bmad-output/审查/2026-08-17-R10复审11项发现-处置回应.md`，证据包 `r10-evidence-2026-08-17/`）: P0-01 vault 身份注册表（垃圾输入 422 / 首claim绑定 / 碰撞 409，端点实测四面全过，生产桶已用真名 `canvas-vault` 预注册）· P1-01 commit 后才 ACK（回滚段整段失败）· P1-02 edge 独立事务 · P1-03 exam 空写如实（RETURN 校验+fallback 拒写+ok/partial/error 分级）· P1-04 回滚先建旧后删新+预检 · P1-05 歧义 census blocker · P1-06 读侧五文件 12+ 站点收口（等值 OR `__` 终止前缀，:Subject 元数据 by-design 全局有测试锁）· P2-01 边关系唯一约束（现网约束 3→**5 条**）+ stale 边清理 · P2-02 schema gate（启动验证+确认缺失拦写 503）· P2-03 真实 Neo4j 验收门 `tests/integration/test_sync_real_neo4j_gate.py` **6/6**（双 vault 写删/poisoned-tx/边不连坐真回查/stale/注册表碰撞）· P2-04 JUnit 112 passed + live-state.json + SHA 清单
- Commits: `05cd1512`(核心写侧)/`c9ab31ca`(读侧)/`d8c4ea9c`+`8006d3ed`(迁移加固+集成门，前者 subject 被 commitlint 长度限占位、注解补正)/`7ba4a4b2`(conftest 注册表 stub)。容器已重启，gate 启动日志 `canvas_schema_gate_ok required=3`
- ⚠️ **本轮自曝并修掉**: 单测经真实注册表污染生产注册行（认领成 `canvas_vault`，真插件发 `canvas-vault` 将必 409）→ conftest autouse stub + 现网修正 + 复跑零污染
- 📋 挂账: 插件侧持久化 vault UUID（增强项）· 迁移脚本原子性（gate 已兜底）· verification 两处委托侧 scope · canvas.py:548 显式线程化 group

**上一状态**（2026-08-17 · **P0-1 /sync/batch 跨 vault 隔离 ✅ 全链收官：4 commits + 审查处置 + --apply + 容器重启 + 双 vault E2E 实测通过 + 金集 34/34** · PLAN `P0-SYNC-ISO-2026-08-17`）:
- ✅ **E2E 双 vault 实测全过（2026-08-17 用户批准后执行）**: 同 entity_id 两 vault 各写一份互不覆盖（Neo4j 实查 2 节点各归其组、title 互异）→ vault_a 删除只删自己、vault_b 存活 → 测试数据清零、库回 11 节点原状；缺 vault_id → 422、空白 vault_id → 422 双验证；金集 board manifest 34/34 对照面零回归。`--apply` 已跑（回填 0 行如预期，3 条复合约束 SHOW CONSTRAINTS 在位），容器已重启（挂载确认 /app=worktree backend）
- 🐛 **C4 `79ea0e41` E2E 抓获存量炸弹**: 三条 upsert 的 `SET ... ON CREATE SET` 是非法 Cypher（Story 1.5 原始写法即错！路由无调用方+单测 stub tx.run 从未被真实 Neo4j 校验）→ ON CREATE SET 提到 MERGE 后 + 3 条子句顺序教训锁。**即：/sync/batch 的 upsert 从 Story 1.5 起就没在真实 Neo4j 上成功写入过任何东西**
- ✅ **C1 `32e9e29c` 写侧闭环**: SyncBatchRequest.vault_id 升必填（缺失 422，唯一调用方 DEPRECATED Tauri 前端属预期）; sync.py handler 显式接 resolve 返回值 → `to_physical_group_id` → `process_sync_batch(request, group_id=物理gid)`; 六条 Cypher MERGE/MATCH 键全部变 `{id, group_id}` 复合键（`_delete_board` 级联双侧都带 group）; canvas_projection_sync/exam_service_ext 三方共键同批切换; 新 `test_sync_group_isolation.py` 10 条**行为断言**（红灯先行，检查 run_calls 实际 Cypher+参数，教训锁: wave5 静态断言逃逸）
- ✅ **C2 `496a2147` 迁移件**: `migrations/003` 五段式 + `scripts/migrate_canvas_group_isolation.py`（--dry-run/--apply, ⚠️ 不复用 group_id_migration_service 的 IS NOT NULL 扫描器）+ 11 条脚本测试
- ✅ **现网 dry-run census 已跑（只读）**: NULL 三 label 全 0 / CanvasBoard label 不存在（库里 11 CanvasNode + 9 CANVAS_EDGE 全在 `vault__canvas_vault`）/ **SHOW CONSTRAINTS 为空 = migrations/001 从未在 7691 生效过** → --apply 实际变更 = 纯新建 3 条复合约束，回填是 no-op
- ✅ **零旁路破坏已证**: stash 基线对照，HEAD 与修复后失败集逐条一致（19 条全存量: auth Settings 校验器 / exception P0-2 fail-closed / wave5 tips 静态断言 / projection 旧签名 / qa_38_6×5 / story_38_8×1）
- 🔒 **[Code-Review] 独立对抗审查已收官**: APPROVE-WITH-FIXES；核心修复被证实无漏（六条 Cypher 全带键 / 物理格式链闭合 / 无 cypher_with_group_filter 误用 / 无 ContextVar 依赖 / 全仓无旁路写入点，11 条候选证伪）。F1 HIGH（exam sync-node 边写入空匹配谎报 edge_created=True）+ F2（迁移 edge 回填不继承端点 group）+ F3（空白 vault_id 绕必填）已在 **C3 `ad82529a`** 处置并加行为测试；F4（verify_targeted_exam_chain.py 裸 id MERGE）/ F5（DEPRECATED 前端 sync-engine 无限重试）/ F6（head(collect) 非确定边角）+ **exam sync-node vault_id 必填化（F1 根治）** 挂账 Phase 2
- ⏳ **收尾两步（等用户批）**: ①census 过目后批 `--apply`（实际=纯新建 3 条复合约束，回填 no-op）②**重启 backend 容器**（Dockerfile 无 --reload，代码不重启不生效）→ 双 vault curl 最小验收（两 vault 同 entity_id 写 → 两节点; 删其一 → 另一存活）+ targeting_material_service 出题链正向验证
- 📋 **挂账 Phase 2（按 6-8 项/轮递审批）**: 读侧 10+ 处 group 过滤（recommendation_service:167/176/192/227/242、verification_service:2175/2208 by-name、question_generator:951、cross_subject_bridge:153、subjects.py:64/234）· cypher_with_group_filter() MERGE 适配 · Graphiti 记录本轮 [Decision]/[Code-Review]（本 session 无 graphiti MCP，欠账）

**上一状态**（2026-08-17 · **双外审收官（ChatGPT+Codex 盲评交叉）· 用户 8/8 裁决全批 · 下一步=P0-1 修复方案** · PLAN `CODEX-ABSORB-2026-08-17`）:
- ⛔ **新 session 第一件事**: 进 Plan Mode 为 **P0-1 `/sync/batch` 跨 vault 裸 ID 写删**单独出修复方案（选项: 全部 MATCH/MERGE/DELETE 键补物理 group_id vs 临时禁用路由），用户确认后再实施、不与其他修复混提。证据: `[WT] sync_service.py` 全文 grep group 零命中、:358 裸 `MERGE {id:$entity_id}`、:532-538 按 canvasId 级联 DETACH DELETE、sync.py:101 ContextVar 注入后执行层从不消费。⚠️ `cypher_with_group_filter()` 对 MERGE/CREATE 生成非法语法，禁止机械套用；方案必须含 MATCH/MERGE/DELETE 三类双 vault 隔离测试
- ✅ **用户 8/8 全批**（R9 批注逐字）: ①P0-1 方案先行 ②E-2 快照选 **A**（只存投影安全面+秩数值，MEDIUM-2 悬案定案）③执行序改 Codex 8 步（P0 止血→数据边界→可信基线→证据修复→安全写入基建→分批落地→价值验证→缓行）④审批每轮只递 **6-8 项** ⑤A-2 扩容: mastery 提交前并入 tiktoken 断网兜底（compression.py:46 只捕 ImportError）+ nodes.py:97 timeout 200ms→按实测校准，WT 代码与 MAIN/.gitignore **分 commit** ⑥D-2 先按真实路径重数 DLQ（live=`WT/data/dead_letter_episodes.jsonl` 仅 1 条；`WT/backend/data/` 92 条为陈旧文件）⑦B-2 广度回顾先做**薄版 MVP**（只新增回顾报告文件，零改原白板/YAML，真实板试跑用户说「有帮到」再扩）⑧E-5 Dashboard webUI 入缓行区
- ⛔ **拓扑修正（Codex 发现，已入记忆）**: compose `./data:/app/data` 子挂载**遮蔽** `backend/data/` → 容器内 reference_config 读 `/app/data/…json`（不存在）走 **fallback 旧权重**（videos 1.5/1.4）；权重 split-brain 实为三方（容器 fallback / 宿主脚本新值 / MAIN 旧值）。修复归 8 步序第 3 步「可信基线」
- 未提交变更（有意，对应⑤）: `backend/lib/agentic_rag/mastery_injection.py` 修复 + `backend/tests/unit/test_mastery_injection_memory_contract.py` + `MAIN/.gitignore` raw 行
- 关键文档: Codex 报告 `_bmad-output/审查/2026-08-17-Codex对抗审查-独立裁定报告.md` · 吸收+逐条复核+8 项裁决 `_bmad-output/审查/2026-08-17-Codex裁定-吸收与两家交叉对照.md` · 通俗版+用户批注原文 `_bmad-output/研究/2026-08-17-批注回复-R9-八项裁决通俗解释.md` · 审批单（待按 8 步序重排 + 用户旧批注待合并去重）`_bmad-output/研究/2026-08-16-设计讨论书-待批事项完整汇总-逐项审批单.md` · 事实基线（待按吸收文档 §二 打 5 处补丁）`_bmad-output/研究/2026-08-15-全项目现状核实-设计说的vs代码做的.md`
- 事实勘误随手账: 审批单确认点 ≥29 非 21 · S2.6 mini-UAT 实为 **3 勾 2 未**（非四条待签）· gen_excalidraw_v3.py 不在仓内（仍在 session scratchpad，会丢）· doc_type `primary-record` 族在 TYPE_WEIGHTS **整族未接线**（两种写法均落 0.5 fallback）· `_待处理`/`_archive` 无索引排除规则（→ A-9 必须前置于 B-1/C-1）· 批注格式已到**第五代** `**User ：`/`**User 修正：`

**上一状态**（2026-08-11 · **阶段 2.6 导航改造施工完成 · 金集 34/34 + 协议校验 35/35 + M1-M4 全达标 · 待用户 mini-UAT（3 勾 2 未）** · PLAN `RAG-S2.6-2026-08-11`）:
- ✅ **T0 落点校准**: live vault = `canvas-learning-system/canvas-vault/`（`.env` CANVAS_BASE_PATH，Obsidian/Claudian 实读）；纪律 = **改 live → 定向文件级同步 worktree → 每批末 `diff -rq`**。⛔ 禁整目录同步（worktree vault 缺 CS188/CS189 与 6 张检验白板、却多 TestConceptA/B fixture）。**计划的「5 份 skill 未入 git」前提证伪**：那是 main 分支视角，本分支 8 份早已全部入库（04-17~07-30），裁定门自动消解
- ✅ **T1 backend 两字段**（commit `ec9c6849`）: `pick_hint.pick_rank`（板内**可考察**候选秩，排序键 `(pick_score, node_id)`；⛔ 只覆盖非占位——占位若占掉 rank1 消费侧过滤后就扑空；在 `_carve` 而非 scan 赋秩 → 历史快照降级态也有秩）+ `past_question_digests[].score_scale`（⛔ 不是自由文本槽位：「数字–数字」形状白名单 + 40 字硬截断，不合形状降级定长文案；缺字段 → `1-4 (1=最低) [推定]`，DD-13 不把推断说成声明）。契约 46→52 绿、金集 32→34、全量 regression 393 passed、延迟 6.1/2.6/2.5ms、exam payload 4.63/6.60KB
- ✅ **T2 Concepts 视图化**（commit `487d7851`）: 新 `canvas-vault/.claude/scripts/sync_board_concepts.py`（真相源=节点 `source_board`，零外部依赖，tmp+os.replace 原子写，比对**排除 synced 时间戳**否则 `--check` 永远报漂移）。⛔ 托管区间取**包络**（实测 6 板两种历史形态）且 **sentinel 存在时并进段内游离概念行**——插件 `appendBoardLines`(main.ts:2558) 插在**整段边界前**即落在 END 之外，只取 BEGIN..END 会留重复行（已按插件真实语义写模拟器复验）。写侧三点接线（ai-linked-doc Step7 / configure-whiteboard Step6 / quiz-answer 新 Step4c-bis）+ 模板换 sentinel 空块；⛔ 顺带修真缺口：configure-whiteboard Skill 此前**没给种子写 `source_board`**（plugin 有写、Skill 漏了）。双锁全绿 + doc_count 漂移×2 归零 + 关 Dataview 仍明文可读
- ✅ **T3+T4+T5 八份 skill 接入**（commit `4244c021`）: canonical ROUTING 块 8 份逐字节相同（SHA `06b0167cc02c`），四平面 STRUCTURE/SEMANTIC/CONTENT/EXAM + HARD-NAV-1..4 + 每份 PLANE-BINDING 5 字段。旗舰 start-exam-board Step3 **19-26 次 → 1 次**、Step4.8 **零工具调用**、Step4 折入 calibration 删 Step5 独立 Grep、Step7 回执要求逐行照抄 `pick_rank`（可外部机械比对的锚点）；⛔ DD-13 修正 HARD CONSTRAINT #1 名实（澄清 HARD-21 管语义检索、与结构检索无关）；⛔ FALLBACK inline python 补 `effective()`——考察链是四方里唯一漏掉闲置折旧的一方（用户裁定 3）。configure-whiteboard Step4.2 全库唯一 O(节点数) 全节点 Read 循环 15→5 次；study-question §3.0 / chat-with-context 开场前**条件触发**限域（⛔ HARD-11/17/21 一字未动）；exam-quick/quiz-answer/node-chat 各写明**为什么禁用 STRUCTURE**
- ✅ **验证四层**: 校验器 `check_skill_routing_block.py` **35/35**（C0 全集/C1 逐字节/C2 硬约束齐/C3 绑定自洽/C4 **工具面⇔绑定**/C5 FALLBACK 成对不嵌套）· 探针 `run_skill_navigation_probe.py` **M1-M4 全达标**（⛔ 不模拟 LLM，真 vault 真文件真字节，旧基线取自迁移前 .bak；M1 median 1→0 / M2 median 7.5→1 / CS188 板 **21→1 次**）· 真机 E2E 三板 · **降级路径与主路径逐行相等（三板 1e-6）**
- 🐛 **顺带修的真 bug**: `csm-tutoring-unit-credit` 有 `source_board` 但不在 `## Concepts` ⇒ 2.6 前读 Concepts 选点的 skill **永远考不到它**；T2 从写侧根除后两条路径都能选到（不是只在主路径绕过去）
- ⚠️ **金集 G3 期望值同批改**: 2.5 把 CS 61B `frontmatter_only: ["csm-tutoring-unit-credit"]` 封成期望（「漏记告警必须亮」），T2 根除后归零 → 改 `[]` 并 `--update-baseline --reason`（修复带来的期望变更，非回归）
- ⚠️ **登记 backlog**: worktree 的 `canvas-vault/原白板`、`节点` 是**陈旧副本**，在其上跑迁移会得出对 live 错误的派生值 → 白板内容**不入库**（已回滚 HEAD）；live vault 白板改动保持未提交 + `.bak` 存于 `.claude/cache/rag-s2.6-concepts-backup/` 可回滚。真正修法是把 live 内容同步进 worktree，不在 2.6 范围
- 🔒 **[Code-Review] 三视角独立对抗审查 24 条发现全部处置 + 全部加回归锁**（每条先自行复现再改，未直接采信）:
  - ⛔ **C-H1 真实数据损坏（最严重）**: `managed_region` 取 min..max **包络** ⇒ 用户在 `## Concepts` 段手写的备注/代码块/`---` **被静默删除**（完整触发链已跑通: 手写 → 下次 Cmd+Shift+D 时 plugin 在段尾追加裸行 → 手写内容夹在中间被连坐）→ 重写成 `managed_lines()` **逐行**标记受管行
  - ⛔ **HIGH-1 泄漏**: `score_scale` 形状白名单**只有头锚没尾锚**(`.match()` 无 `$`) ⇒ `1-4 反例 diag(-1,-1)…`（**G6 金集禁串**）整串原样透出 → `fullmatch` + 收紧文法 + 先验形状再截断
  - ⛔ **HIGH-2 静默劫持**: `mastery_a: .inf/.nan` ⇒ nan 比较恒 False 让 Timsort 保持输入序，投毒节点吃掉 `pick_rank=1` 且 `parse_errors` 空；自查另发现 exam JSON 吐**裸 NaN = 非法 JSON** → `_num` 加 `isfinite` 门 + 显式上报 + 秩过滤 + 严格 JSON 断言
  - ⛔ **D-HIGH-1 我自己的方法论错误**: 上一版「降级路径逐行相等」验的是**我修好的路径**——SKILL 的 Grep 当时没取 `last_examined`，闲置折旧在降级态整体失效 → 补字段 + **写脚本从 SKILL 正文抠出 Grep 与 python 直接执行**重验（三板逐字段相等，`idle=16.9d` 是折旧生效的证据）
  - ⛔ **C-M6 已在真 vault 生效**: `mkstemp` 恒 0600 + `os.replace` 继承 ⇒ 6 块白板权限被从 0644 静默改成 0600 → `os.chmod(tmp, 原 mode)` + **已改回并复验不再复发**
  - ⛔ **D-MEDIUM-5 校验器只数信封不看信**: 掏空降级块/改坏 import/新增裸调用/把降级反转成「停止并叫用户起服务」六种腐烂全判绿 → 加 C6(按小节校 HARD-NAV-3)/C7(ast.parse + import 符号存在)/C8(禁中止语义)，**35 → 59 项**
  - 其余: MEDIUM-1 G8 子串判定被 `[推定]` 前缀绕过→改闭集 / MEDIUM-3 SKILL 把 manifest 划进可信面→新增 **HARD-ISO-5b** / D-HIGH-2 降级把占位也编秩致秩号错位→排序前剔除 / D-HIGH-3 反向引用 regex 未 `re.escape` 致含括号节点整批漏检→已修 / D-MEDIUM-4 缺 Concepts 段时 exit 0 还说「已同步」→抛异常+退出码分层 / C-H3 frontmatter 自由文本被逐字写进白板→只认真 wikilink / C-H4 与后端 7 条语义分歧→逐条对齐 / C-H5 批次非原子 / C-M7 无 fsync / C-M9 行尾归一 / C-M10 doc_count 只改首处 / C-M11-13 断链·孤儿·多 sentinel 静默→全改成告警且 `--check` 红 / C-M14 `.bak` 二次覆盖
  - **复验**: 协议校验 35→**59/59** · 全量 regression **425 passed**（393→+32: 契约 46→64 + 新 `test_sync_board_concepts.py` 20 项）· 金集 34/34 · 探针 M1-M4 全达标 · 脚本 `--check` 幂等无告警 · ruff 全绿
- ⚠️ **待用户裁定（我没单方面改）**: 审查 MEDIUM-2 —— `view:"exam"` 调用**本身**把全量禁项原料明文落盘到 `<vault>/.claude/cache/`（真 vault 那份 22KB 快照含 G6 禁串明文，出题 agent 有 Read 权限）。本轮只做 prompt 级 **HARD-NAV-5**（禁读 `.claude/cache/`）+ gitignore；彻底修法二选一: **A** 快照只存投影安全面（代价: 降级态 study 视图丢 tips/errors）/ **B** 快照移出 vault 到 backend 侧（代价: 反转 2.5「落 .claude 双黑名单」的架构决定）
- 📋 **用户 mini-UAT 卡**: `_bmad-output/验收单/Story-RAG-S2.6-导航改造-mini-UAT.md`（DoD-3 七段 + 4-A/4-B 双段，段 4-B 禁词 0 命中 / 4 条全用「我做 X → 我看到 Y → 我感觉 Z」句型；⚠️ 首行提醒 `Cmd+Q` 完全退出重开 Obsidian —— MCP/skill session 缓存 2.5 踩过两次）
- ⏭ **下一步**: 用户 mini-UAT 签字 → **阶段 3**（退役 8765）。2.6 明确不做: structure-navigator 子代理（用户已砍，回退阈值：单次 skill >3 次 manifest 调用或单板 exam JSON 常态 >8KB 则 2.7 重议）/ 批量 candidate 端点（manifest 已是）/ backend `calibration_gap` 字段（折入 skill 抽取器）/ 改前端插件（DD-12）/ 改 `score_scale` 写侧（vault 已有）/ 砍 study-question HARD-11/17/21 / LLM 查询改写 / 1.5 稳定 ID / Neo4j 投影

**上一状态**（2026-08-11 · **阶段 2.5 Board Manifest 施工完成 · 金集 31/31 全绿 · 待用户 mini-UAT** · PLAN `RAG-S2.5-2026-08-10`）:
- ✅ **T0 依赖+迁移**: python-frontmatter 依赖洞首 commit 修复（364d2b39, docker build 验证过）; vault 迁移用户四项签字（删 TestConceptA/B/C + csm-tutoring 归 CS 61B + 考察产物移检验白板 + main 直接 commit 44113f54）→ **14/14 节点全员 source_board, 孤儿清零**; T0.5 特征值 Concepts 实测 3 条定案（Plan agent「空 section」说法证伪）
- ✅ **T1-T3 已 ship**（worktree commits 870ca8f5/55f9421e/bcdde1ad）: board_manifest_service（ManifestDataSource Protocol + mastery 四态归一化 + is_stub + dual_source_gap 窄解析 + pick_hint 内联 decay_beta 1e-9 契约锁）; exam/study 双视图 Pydantic 投影（**exam 禁项=模型结构性缺字段**, live/快照 serve 共用唯一投影点）; 快照三态降级 `.claude/cache/board-manifest/manifest-v1.json`（generation 变更才重写+原子写, live→snapshot→error 诚实申报, 真实环境实测退快照+恢复全过）; HTTP `POST /api/v1/boards/manifest`（prefix=/boards 防 wildcard, require_internal_api_key + vault fail-closed 409）+ MCP `get_board_manifest`（第 6 只读工具, 空 body 防 P16, quarantine 测试 5→6 同步）
- ✅ **T4 金集**: `scripts/run_board_manifest_regression.py` + `board_manifest_gold_set.yaml` 31 条硬禁通道（G1 成员×6/G2 孤儿/G3 gap×3/G4 字段×10/G5 历史×3/G6 泄漏×8 含合成投毒）**宿主+容器双姿势全绿, 基线封版**; 契约测试 41 绿; 全量 regression 381 passed 零旁路破坏; 实测延迟: 列板 104ms/exam 79ms/study 61ms（预算 <300ms）
- 🐛 live 实测抓 bug: BUG-361BD6FC（YAML datetime 透传 tips/error_candidates 炸快照 json.dumps）→ _json_safe 深度清洗+回归锁
- 📋 **用户 mini-UAT 卡**: `_bmad-output/验收单/Story-RAG-S2.5-BoardManifest-mini-UAT.md`（技术三条 Claude 已全部代跑留档, 用户只验 Claudian 产品体验; ⚠️ 宿主改目录名容器 ~10s 才可见=VirtioFS 缓存）
- 🐛 **UAT 两轮实锤两个 MCP 面 bug（已修复+回归锁）**: ① 旧 Claudian session 缓存 5 工具列表（server listChanged:false 不推变更, JSON-RPC 实测 server 侧 6 工具一直在列）→ 用户侧 /mcp 重连即可, 非 bug; ② ⛔ `input: X | None = None` P16 模板让 requestBody 变 anyOf → fastapi-mcp 展不开 properties → **MCP inputSchema 参数全丢**（Claudian 只能无参列板, board_id/view 调不出）→ 改 `Body(default_factory=...)`（该模板只适用空输入模型, check_backend_health 恰好无参才没炸）+ quarantine 新增参数面回归锁; E2E 复验: tools/list 三参数齐 + 带参单板 exam 调用 3 节点/6 历史 + 空参列板 P16 不炸
- 🔒 [Code-Review] 独立对抗审查（E2E 复现式）**3 HIGH / 3 MEDIUM / 5 LOW → 全部处置, 复验 32/32 全绿**: ⛔ H1 orphans 回显通道（source_board 塞定义全文进 exam 视图, 已复现）→ reason 定长枚举文案+raw 截断 120+模型 max_length 门; ⛔ H2 parse_errors 回显（last_examined repr 无界+纯 Python yaml loader str(e) 引用原文行含 correction 禁串）→ _safe_err 去内容化（异常类型+行号）+repr[:80]+模型 200 字门; ⛔ H3 untrusted 标量炸投影（`doc_count: 大约五个`/`title: 2026` → ValidationError 500 整端点含列板）→ _bounded_str 类型归一×7 字段+双暴露面 ValidationError 纵深兜底; M4 digest 吸入相邻 [!feedback]/[!hint] callout（可含正确答案）→ callout 边界终止收集; M6 #heading 锚点+大小写敏感→假孤儿（喂 H1 通道）→ resolve 剥锚点+boards_ci casefold 匹配; M7 金集合成A恒真条件（自比较）→ 改「挖掉 reason 槽位后 0 命中」; M8 禁串无正向对照会静默腐烂→禁串必须仍在 vault 源文件+G5 digest 非空对照（金集 31→32 条）; L 批: 快照 tmp 唯一名防竞态/load 快照 schema 必备键校验/exam_board_count 恒用 full 历史/信封字段统一截断/set_current_subject_id 移到 fail-close 之后。审查确认: 投影穿透 E2E 失败（防线真实）、快照双黑名单成立、serve 路径唯一、pick 数学锁死、无 DD-03 违规。新增回归锁 6 条（契约 77 绿）
- 📌 顺手发现: **8 个未剖析占位节点**（CS188×7+特征值 Eigenvalues-special, is_stub 如实标注）; doc_count 漂移×2（CS 61B 声明1实际2/递归声明0实际1, 归 2.6 写侧）; 金集 shadow 分区已作观察面
- ✅ **UAT 产品体验项第三轮实测通过（待用户签字）**: Claudian 单次带参调用拿全量拆解并直接给学习诊断（beta/score_only 双轨判「板有没有真在用」= manifest 立足点的活证明）
- 📌 **2.5 收尾 backlog（新增 3 条）**: ① digest 裸 score 无量纲标注被消费侧误读成满分（实际 1-4 制 1=最低; 加 score_scale 字段属 exam keyset 契约变更, 走 --update-baseline 流程, 归 2.6）② 选点贪心锁定观察（枢纽 μ 极低时叶子排不上; 注意 Eigenvalues-special 是 stub 本就该跳过）③ Concepts 行内 "(mastery: 0.30)" 快照文案与真值脱节（2.6 写侧视图化处理）
- ⏭ **下一步**: 用户 mini-UAT 签字 → **2.6**（`## Concepts` 写侧视图化 + 8 skill 接入 manifest 替代 Grep 拼图）; 2.5 明确不做: 1.5 稳定 ID（字段已标注 basename_v1）/ Neo4j 投影修复（backlog, Protocol 接口已留）/ 写端点 / exam 承载 misconception / FSRS 字段

**上一状态**（2026-08-10 · **阶段 2 收官 ✅ 用户 UAT 四步全过** · 下一步: 九阶段路线 2.5/2.6 · PLAN `RAG-S2-2026-08-09`）:
- ✅ **阶段 2 UAT 通过（用户实测四步全过 2026-08-10, 记录在卡）**: ①手写优先+dedup+wikilink 7/7 真实 ②vault 外主题零编造（`ce_gate_all_filtered` 标注实锤）③search_notes 与 hook 同源（加权分量纲 0.55-0.60 实证）④检验白板零泄漏（弃答闭环记录/原白板导航均为设计特性非泄漏）。卡: `_bmad-output/验收单/Story-RAG-S2-阶段2-强化fastpath-UAT.md`
- 📌 **UAT 新观察项**: 「特征方程」query 注入 7 条 RL「特征表示」— 中文共词假匹配 CE 门未杀（已知 CE 盲区家族), Claude verifier 层自行绕开转 search_notes; 归 CE 盲区 backlog 追踪
- ✅ **三决策用户已裁定（全采纳推荐项）**: ① **f06/h07 移 shadow**（金集 v2, 58 条; 基线: MRR 0.7889/nDCG 0.7121/交付 84.91%/污染 38.60%/FPR 6%; 红档只剩 f04/z04 真实能力缺口; file_locate 意图路由 backlog, exam_board 任何方案绝不放行）② **f04 扩池不做**（扩池仅 file 级 rank4、+31% 延迟 — 根因段落级召回, backlog 等 chunk 侧补强）③ **[!note] STRIP 维持现状**（census 零误伤实锤）
- ⏭ **下一步**: 九阶段路线（0→1→1.5→**2 ✅**→2.5→2.6→3→4→4.5）进 **2.5/2.6**（开工前重读九阶段路线定义 `_bmad-output/研究/2026-08-02-RAG修复计划-用户审阅版.md` §施工顺序与工期 L93 — A-1 修正于 R11-BATCH2: 原指 `2026-08-09-RAG阶段2-强化fastpath实施计划.md`，该文件存在但仅 36 行、是阶段 2 的单阶段计划，不含九阶段路线，反而把 2.5/2.6/4.5 列入「明确不做」）; 阶段 2 backlog 汇总: CE 盲区类（a01/z02/z05/特征共词）/ f04 段落级召回 / file_locate 意图路由 / extended 分支 taint / MCP top_k 漂移 / tier-2 legacy exam_board / RETRIEVAL_RERANKER_* compose 白名单
- ✅ **T6 验证收尾完成**（17-agent workflow: 4 路验证 + 3 lens 全链路对抗审查 + 逐 finding 证伪）: 金集终验通过 + shadow 空（设计态）; live 实测 9 项全 PASS（hook 四态/MCP confidence/考察隔离/M6 410/refresh-changed 存活/18012 双向可达）; **[!note] STRIP census 实锤零误伤**（206 md 仅 1 处且嵌套 error-candidate 内被 EXTRACT 保留; info/video 55 处全系统模板）; **vq-f04 扩池实测**（50 池 file 级 rank4 但「烘」段落仍不召回, 延迟 +31%）; **vq-f06/h07 结构性死档实锤**（期望文件全 doc_type=whiteboard 被查询侧排除, 反事实去排除 rank1 立即回归, 选项 B>A>C 待用户裁定）
- 🔒 [Code-Review] T6 全链路审查 **8 CONFIRMED / 2 REFUTED → 全部处置**: ⛔ **HARD-ISO live 泄漏**（vault_notes_retriever 默认排除表漏 exam_board, 经无鉴权 /api/v1/rag/query + agents.py 六处可达 → 补齐; react_agent/tool_executor/agent_graph 三条 flag-gated 链同批纵深补齐）; **fts_confirmed 名实颠倒**（_rrf_score 写给所有融合行, dense-only 恒 True/真词法命中反 False → _rrf_fuse 新 _fts_hit 通道标记 + 白名单 + svc 公式改 `_fts_hit and not _fts_only`, 仍遥测-only）; **检索层故障吞噬纵深**（_search_internal 全分支故障 raise 受 enable_fallback 门控[默认 True 调用方行为不变] + open_table 失败 raise + hook singleton 关吞噬/init 失败不缓存 + 空交付文案不再主动断言「检索正常」）; ⛔ **elbow telescoping = 三轮金集 A/B 裁决保留 T4 行为**（审查数学观点成立, 但两种修复均被金集打回: 全量序列 floor → 污染 39.83→57.38%/FPR 8%; dedup 后门前 floor → 48.25%/8%; +1.8pp 命中换不回 +8~17pp 污染 — 门后 telescoping 截断是净正收益保守护栏, 数据与翻案条件锁进 test_gate_thinning_elbow_is_deliberate_t4_behavior）; REFUTED×2: react_agent/agent_graph「拨真即泄漏」不可达（仍随批纵深补齐排除表）; LOW backlog: extended 分支无 taint / MCP top_k 参数漂移 10vs15 / TYPE_WEIGHTS concept 死键
- 📋 **用户 UAT 卡**: `_bmad-output/验收单/Story-RAG-S2-阶段2-强化fastpath-UAT.md`（产品语言 4 步 + ⚠️ 问句/探针分两条消息坑已进模板）
- ⏳ **三个待用户决策**（数据已备齐, 选择题形式问）: ① f06/h07 死档（建议 B 移 shadow 升 version）② f04 扩池（数据: 收益仅 file 级、grade3 不达、+31% 延迟 — 建议 backlog 等 chunk 侧补强）③ [!note] STRIP（数据: 零误伤 — 建议维持现状）
- 金集（审查修复后复验）: 见 baseline history 最新条目; T6 契约锁 15 条 + 链统一 24 条全绿

**上一状态**（2026-08-10 · 阶段 2 T1-T5 已 ship · T6 前 · PLAN `RAG-S2-2026-08-09`）:
- ✅ **T5 链统一+诚实遥测已落地**: MCP `search_notes` fast path 改走共享后处理（`search_supplementary` + `include_content` profile, 生产参数 0.50/0.25）→ hybrid FTS+RRF/加权序/taint(含全文扫描)/空文档检测/源文件 dedup/CE 门在 MCP 链全部生效, score 量纲=加权分; **retrieval_confidence 双面注入**（hook XML 根元素 `confidence="high|medium|low|none"` 离散档 + MCP 顶层 `retrieval_confidence` 字段——⛔ pydantic 模型已声明防 response_model 裁剪; 裸分数不进 prompt 面, `ce_score not in xml` 契约保持）; **hook 降级失明修复**（client未就绪/5s超时/异常/空交付四分支注入 `degraded/reason/confidence` 标注 XML, exam-skill/system-op/短句跳过保持零注入）; **M6 incremental 端点 410 退役**（指引走 `/api/v1/index/refresh-changed`, 照 vault.py P0-3 姿势）; Step 0 vector 回退分支补 exam_board（HARD-ISO 旁路堵死）
- ⛔ **T5 探针定案（勿翻案）**: `fts_confirmed` **不进交付门** — 垃圾 query n01 5条/n03 7条 raw≥0.50 全 fts=True（zh 常用词「节点/删除/平衡」FTS 命中）, 真命中 a01/z05 的 Fundamentals（appended 咖啡段）反而 fts=False → 词法双通道不可分, 只作 confidence 遥测（回归锁已铺）。h08/m04 真命中在 T4 门下已能过（dedup CE 证据合并 ce 0.204/0.027）; a01/z02/z05 仍丢, confidence 已能标注这类丢失
- 🔒 [Code-Review] T5 独立对抗审查 2H/2M/2L → **全修**: HIGH-1 基础设施故障被吞成 ok_empty（fast client `enable_fallback=False` + `_two_tier_search` 两级全败 raise 走 search_failed + `_fast_path_search` embedding 预检恢复阶段0语义, 真实路径回归锁×2）/ HIGH-2 MCP 全文交付但 taint 只扫 300 字 snippet（content 挂载前移进扫描面, 交付面=扫描面）/ MEDIUM-3 tainted 材料 metadata 收窄（doc_type/source_type frontmatter 自由文本不随隔离材料外带）/ MEDIUM-4 enrich-context rerank 后 confidence 失真（摘除不渲染, 重算留待后续）; LOW-6 tier-2 legacy 表无 exam_board 排除 → backlog（env-gate 默认关, 暴露≈0）
- 金集: **全指标持平 T4 基线**（recall 92.73%/MRR 0.7602/nDCG 0.6862/FPR 6%≤8%/交付 81.82%）门禁通过+基线已锁（交付命中持平=预期, Step 4 收复按计划退回遥测-only）; regression 324 绿+新契约 24 条; live 实测: MCP confidence 透出+CE 门生效（h08 只交付 节点/lecture 2 全文）、hook 空交付注入 `count="0" reason="ce_gate_all_filtered" confidence="none"`、非空注入 `confidence="medium"`
- ⏭ **T6 验证收尾**: 金集终验+live 实测+对抗审查+用户 UAT 卡（产品语言; ⚠️ 问句/探针分两条消息的坑写进卡模板）; **待用户决策（勿擅自做）**: vq-f06/h07 whiteboard 排除与金集期望冲突（file_locate 放行 or 修订金集升 version）、vq-f04 扩池≥50（延迟代价）、`[!note]` STRIP 误伤面 census

**上一状态**（2026-08-10 · 阶段 2 T1-T4 已 ship · T5 前 · PLAN `RAG-S2-2026-08-09`）:
- ✅ **T4 dedup+CE 交付门已落地**: 新 `backend/app/services/retrieval_reranker.py`（长活 AsyncClient/MaxP 5×400字窗口/sigmoid/1.5s超时/3败熔断60s/env 链 RETRIEVAL_RERANKER_* 回落 GRAPHITI_RERANKER_BASE_URL）+ svc 接入源文件级 dedup（taint fail-closed 合并+CE 证据拼接）。⛔ **架构定案: CE 是交付判官不是排序器** — 两轮金集校准实证 CE 排序（纯CE/CE×权重）让 raw/ 转录反扑（手写占比 59.5→29/31%），排序保持 T2/T3 加权序；CE 门（floor 0.02，min_relevance=0 时不激活）杀垃圾+放行低 raw 正解（预过滤放宽 0.30，放宽行不占 top_k_max 配额）。金集: recall **92.73%** MRR **0.7602** nDCG **0.6862** 全升、FPR **42→6%**、交付污染 47.6→39.8%、交付 81.82% 持平 T3、rank1/2 同文件重复根治。基线已锁 3 轮（校准轨迹在 history jsonl）
- 🔒 [Code-Review] T4 workflow 审查（45 agent, 3维find+双盲证伪, 21报12实9拦）→ **全修**: HIGH 池挤占（放宽行挤出 raw≥0.50 正解, 修后交付 80→81.82%）/ AttributeError 逃逸契约+绕熔断（畸形200封堵）/ 英文chunk 1200字盲区（MaxP 3→5窗）/ dedup 丢被合并 chunk CE 证据 / 单测隐藏网络依赖 / ce_gate_all_filtered 观测区分 / CancelledError 熔断记账 / 6 条新回归锁（含池饱和等价+半开恢复+XML 不渗漏）。contracts 26+chunk 21 绿, unit svc 55 绿
- ⚠️ T4 已知边界（T5 靶）: CE 盲区类 query 交付丢失（h08「我做过哪些笔记」meta/z02 转述/z05/a01 — CE 分与垃圾区间重叠, 纯 CE 无解 → T5 fts_confirmed+intent 信号收复, `ce_gate_all_filtered` 日志信号已铺好）; vq-f04 需扩池≥50、f06/h07 是 whiteboard 排除与金集期望冲突（用户决策）、z04 稠密召回失败; 代码块原子 chunk >2000 字残余 CE 盲区; RETRIEVAL_RERANKER_* 未进 docker-compose environment 白名单（回落链可用, 加白名单需 recreate）
- 手写占比@10 59.5→33% 与污染@10 24→37% 是 **dedup 度量语义重定义**（同文件×N 刷分终结, top10=10 个不同文件, 手写文件总数决定物理上限 ~35%）— 非质量回退, 基线 reason 已记录

**上一状态**（2026-08-09 · 阶段 2 T1+T2+T3 已 ship（`25dc54a2`+`fcd34953`+`89d51dc9`）· PLAN `RAG-S2-2026-08-09`）:
- ✅ **T3 chunk 改造已落地**（lancedb_client.py 单文件）: 段落级三级切分(段落→句子→子句)+overlap 段落化 / callout 三级分级(EXTRACT question/error/error-candidate 独立成块; STRIP info/video/note+"💬 围绕这个概念讨论"模板标记; KEEP 其余) / 模板样板 section 零 chunk / **考察文件 exam_question_id→exam_board 推断堵题面泄漏**(用户截图 rank3 考察文件已从检索消失, 索引唯一考察文件已转 exam_board) / 短块(<150tok)面包屑只留文件名 / line_start 补 frontmatter 偏移。金集: recall **90.91%**(+1.8pp) 假阳性 **58→42%** 污染@10 24.17% nDCG 0.6415(容差内) 交付 81.82% 持平; vq-a02 咖啡 rank 7→4, vq-a03 rank1 交付 9 条; 基线已锁(history 归档)。契约测试 21 条(组A-F), regression 全绿
- 🔒 [Code-Review] T3 独立对抗审查 0C/1H/2M/5L → **HIGH-1(YAML 解析失败绕过 exam_board 推断=泄漏复活, 已修嗅探兜底)+MEDIUM-1(紧贴 callout 吞批注, 已修断块)+MEDIUM-2(占位误杀, 已收紧)+LOW-4(tiktoken 冷启动, 已降级兜底) 全修**+4 红线测试; 未修 backlog: LOW-1 超长 EXTRACT 降级切分丢 [!question] 标记 / LOW-3 [!note] STRIP 误伤面待 census 复核 / LOW-5 建议 exam-quick.ts frontmatter 标量加引号(前端, 勿混本批)
- ⏭ **T4 dedup+rerank**（下一步）: 源文件级 dedup + 新 retrieval_reranker.py(复用 graphiti/rerank_client 连接池; ⛔512token 超限整请求 500 必须截断 400 字; 1.5-2s 超时回落原分; elbow 迁 sigmoid(logit) 重校准; 假阳性 42% 与 vq-f04/f06/h07/z04 四残留 query 是靶), 接入 supplementary_search_service 归一化后/elbow 前, env RETRIEVAL_RERANKER_BASE_URL 回落 GRAPHITI. T5 链统一+confidence。T6 审查+UAT(问句/探针分两条消息坑进卡模板)
- ⚠️ 金集必须容器内跑 docker exec; force_rebuild 入口 canvas-meta/index/vault + X-CLS-Internal-Key; T1/T2 详情见 git log 与计划文档 `_bmad-output/研究/2026-08-09-RAG阶段2-强化fastpath实施计划.md`

**上一状态**（2026-08-09 · 阶段 1 ✅ 用户完整 UAT 通过）:
- ✅ **阶段 1 索引层验收通过**（测试卡 v2 全项: 新建 0.585/改写 0.648/删除三层清/大文件追加 3min 重索引）; MCP -32602 根治（mount_http+.mcp.json http, `d93631ac`）; 观测加固（相对秒数/逐task/excluded 计数, `a87f04ea`）
- ⛔ **阶段 2 头号靶子实证: chunk 稀释** — 大文件尾部追加异质内容并入 598 字符主导 chunk → 相关度 -0.11~-0.17（独立小文件 0.648, 差 30+ 倍）→ hook 不可见。阶段 2 = chunk 策略 + rerank(18012) + doc_type 权重 + golden set
- 📋 教训入卡: 问句/探针分两条消息（hook 词黑名单）; 语义零重合问法必须先实机校准（0.498 灰区实锤）

**上一状态**（2026-08-03 · 阶段 1 已 ship · PLAN `RAG-S1-2026-08-02`）:
- ⛔ **九阶段路线**（0→1→1.5→2→2.5→2.6→3→4→4.5）; 阶段 1 全落地: `vault_index_orchestrator.py` 统一五原语 + durable per-path pending（JSONL 意图日志+退避重试）+ watchfiles 事件加速 + 60s anti-entropy 扫描 + orphan sweep 收敛 + freshness 遥测
- ✅ **live 实测**: 保存→可检索 **5-6s** / 删除→不可检索 **5s**（SLO 60s）; 索引冻结解除（3604→2174 行 100% 新写, Fundamentals 1→5 chunks, chunks/ 双份冗余清除）; 重启恢复 66 pending 实测; 抓获并根治 6 文件空产出永动循环 + status 端点 9.5s→0.009s
- 🔒 [Code-Review] 0C/4H/6M/7L→**H1-H4+M1-M5 全修**（H1 embed 挂=假成功/H2 短写丢行/H3 DELETE default 抹全 vault 指纹/H4 事件循环阻塞+O(N²) persist/M1 毒文件退避/M3 路径穿越）; M6 增量端点收编+L6 NFC 挂账阶段 2; 契约测试 32 条（四组+5 审查锁）; regression 252 passed
- 📋 **用户 mini-UAT（1 分钟）**: `_bmad-output/验收单/Story-RAG-S1-索引重写-mini-UAT.md` — 改笔记→1 分钟内 Claudian 引用新内容
- ⏭ 阶段 1 后: 1.5 稳定身份 或 2 强化 fast path（rerank/golden set/配比治理）; backlog: M6/L6/传递依赖连坐锁/metadata 每请求新建 client
- 📄 决策链（勿重新推导）: `_bmad-output/审查/2026-08-02-RAG检索设计对抗性审查-三问三答.md` → `…ChatGPT-RAG三P0审查吸收与验证.md` → `…ChatGPT-规模化结构检索终审-吸收与验证.md` → `_bmad-output/研究/2026-08-02-RAG修复计划-用户审阅版.md`
- 🔒 已定裁决: 6 源管道退役出默认链（阶段 4 shadow 定生死）; quality=low 假信号废除; ~~path_map~~/~~configurable~~ 已证伪（正解 async router + `context=`, 属阶段 4）; 三平面架构=frontmatter 唯一可写真相源 / Neo4j 确定性投影 / Graphiti 时间记忆
- ⏭ 阶段 0 后: 阶段 1 索引重写（开工前重读 ChatGPT 第一轮 §四）; 明早 9:05 Bark 推送有机验证勾 `Story-DAILY-REVIEW-PUSH` mini-UAT

**上一状态**（2026-07-31 · 二轮对抗审查 P0 安全收口一二批落地 `7f63f6a3`+P0-3）:
- ✅ **P0-0 端口收口**（四端口绑 127.0.0.1, LAN 拒绝）; **P0-2 MCP 写侧隔离**（19→5 只读, 14 隔离 410+遥测, 31 契约）; **P0-3 去 global vault switch**: /vault/switch 410 隔离（逃生=改 .env ACTIVE_VAULT+compose up, 审查抓出 CANVAS_BASE_PATH 文案错误已修）+ 插件 CTA/下拉下架改只读 + enrich-hook cwd→vault 推导（段名 NFC 匹配, 多命中回退）+ tips 写侧 vault_id 必填 + deploy-vault skill 死端点清理。两轮独立审查 APPROVE-WITH-FIXES 全修
- 📄 审查链: `_bmad-output/审查/2026-07-30-全系统功能状态对抗性审查-三分类报告.md` → `2026-07-31-ChatGPT第二轮对抗审查吸收与代码验证.md`
- ✅ **08-01 launchd 五腿全活**（`6de130d4`）: TCC 根因=plist 须显式 /bin/bash + python3.14 单独 FDA（用户已加 3 条 FDA; brew upgrade python 后 python 条目要重加）; memory-health/neo4j-backup（断 9 天后新 dump）/qwen/reranker/daily-review 全 exit 0; P0-6 恢复演练 ✅（118 节点/214 关系完整）
- ⏳ **P0 余量**: ①用户装 Bark 贴 key（`~/.config/canvas-review/bark.key`, 明早 9:05 无 key 走本地通知 fallback）②P0-5 Tier B 观察期后物理删（+infra_tools.switch_vault 死函数、plugin activeVaultName 死字段）③P1: split-brain 文件路径 vault_id 化（多 vault 激活前必做）
- ⚠️ 存量债: test_vault_id_changes_after_reload 环境依赖失败（stash 实锤非本批）+ 插件 7 个 source-regex 测试失败（HEAD 同挂）

**上一状态**（2026-07-30 · FSRS-V2 真实到期调度全落地，与推送 MVP 同待用户 UAT）:
- ✅ **FSRS v2 上线**: quiz-answer×fsrs_bridge 写 6 个 fsrs_* 字段（py-fsrs 6.3.1, 关 fuzzing）; 推送链 WHEN 化（due 过滤+放假消息）; Dashboard 到期接活; 幽灵调度器/schedule 端点/插件死命令退役（生产 404 实测）; 38 测试绿 + 审查 0 CRITICAL 8 项修复
- 📄 决策: `_bmad-output/研究/2026-07-30-FSRS-v2-D0-决策记录.md`（映射四档 + WHEN/WHAT 分工）; UAT: `_bmad-output/验收单/Story-FSRS-V2-真实到期调度-mini-UAT.md`
- 📋 Tier B 退役移交（未做）: /review/record + fsrs-state + history、MCP mastery 工具、review-suggestions +1 天写死、exam 回退链、WeightCalculator 死方法 — 清单见范围报告 §五

**上一状态**（2026-07-29 · DAILY-REVIEW-PUSH 每日复习手机推送 MVP 代码全落地，待用户 UAT）:
- ✅ ChatGPT 终审 CONDITIONAL GO + 本地模型栈 KEEP（不迁 MLX-VLM 不换 122B）→ 全部修正已吸收: `_bmad-output/审查/2026-07-29-ChatGPT终审吸收与代码验证.md`
- ✅ 修订八步全落地: decay_beta effective/update_after_idle（26 测试绿）+ daily_review_pick/send_bark/daily_review_run + launchd wrapper（稳定路径+TCC 预检）+ 死人开关; 12 场景矩阵全过; 独立 Code-Review 0 CRITICAL 15 项已修
- ✅ live 首跑成功: 今日复习.md 榜首=特征值与特征向量/Fundamentals; launchd 已 bootstrap（当前 TCC 拦, exit 78 有人话诊断）
- ⏳ **用户 UAT 3 步**: 装 Bark 贴 key（写 `~/.config/canvas-review/bark.key`）+ 系统设置 FDA 授权 /bin/bash + 明早 9:05 看横幅 → 验收单 `_bmad-output/验收单/Story-DAILY-REVIEW-PUSH-每日复习手机推送-mini-UAT.md`
- 📋 Backlog: 模型栈加固 H-1~H-6（版本锁/canary attestation/distiller schema）+ H-7 memory-health 宿主迁移 + H-8 孤儿节点回填 + H-9 Bark 加密

---

**历史状态**（2026-05-13 · Session-End · Story 2.3 + ChatGPT-DR Wave-6 安全硬化 7 commits ship）:
- ✅ **Story 2.3 v1.0 ship** (`d9a7164`): historical error reminder, 5 AC, 21 tests, 待用户 UAT (路径 A/B/C 见操作指引)
- ✅ **Wave-5 Stage B followup** (`438666d`): `index.py:delete_vault_index` ContextVar 注入 (3 tests)
- ✅ **ChatGPT-DR Wave-6 安全硬化** (4 commits):
  - `b2b773d` **P0-1** `/memory/extract-conversation` fail-closed + dev bypass opt-in (12 tests)
  - `c9bb6c9` **P0-2** DEBUG=False 默认 + `require_internal_api_key` Branch 2 hardening (13 tests + 3 legacy 改契约)
  - `e5ff53c` **P0-3** Memory API 6 endpoint 加 `require_internal_api_key`
  - `7cc3c1c` **P0-5** source_description schema 对齐 — typed enum + IN list reader + 18 contract tests
- ✅ **Docs** (`cda47a7`): 4 个 session 文档 (UAT 指引 / 全景 / 评估 / ChatGPT prompt)
- ⚠️ **ChatGPT-DR 调研** (2 轮 deep research): Claude FAIL 判定 + 用户核心闭环不可行 (G1-G10 + 5 盲点); ChatGPT 推荐 A+ 路径

**下一步 — Session-Start 锚点**:
- (1) 用户跑 **Story 2.3 UAT** (3 paths: A 现有数据 / B 自然产生 / C 授权 seed) @ `_bmad-output/验收单/Story-2.3-UAT-操作指引-2026-05-13.md`
- (2) 用户读 ChatGPT 报告 Part 4 — **5 个 Claude 漏看盲点** (annotation identity drift / 多存储一致性 / prompt injection in verbatim / 可观察性 evidence trace / 成本队列)
- (3) 下次启动方向 (ChatGPT A+ 推荐): **P0-6 callout→mastery 桥接 (1-2d)** → **P0-7 LanceDB AnnotationDoc 重构 (1-2d)** → **🌟 GOLDEN-PATH demo (3-5d)** — 不要走 P0-4 网络收口 (除非部署到 LAN/共享主机)
- (4) 推迟: **P0-4 MCP loopback + WS 鉴权** (网络收口，本地单机不紧急)
- (5) Story 2.3 通过后启动 Story 5.1 BKT (CURRENT_TASK 8-Session plan S3，但 ChatGPT 警告**优先做 P0-6/7 + GOLDEN-PATH 不要继续横向 Story dev**)

**关键调研产物归档**:
- ChatGPT-DR 安全审查: `_bmad-output/research/2026-05-13-chatgpt-security-audit-INLINE.md`
- ChatGPT-DR 第二轮回答 (verdict + 10 gaps 打分 + 7 Q 回答 + 5 盲点): 见用户 conversation log Part 1-6
- 设计可行性评估: `_bmad-output/验收单/批注回复/2026-05-13-设计可行性评估-用户核心闭环.md`
- 后端运行机制全景 (5 Agent deep explore): `_bmad-output/验收单/批注回复/2026-05-13-User批注-后端运行机制与-Graphiti-全景.md`

**当前状态**（2026-05-12 续 · wave-4 Q3 rollback + SKILL.md native Grep ship）:
- ✅ ChatGPT 全链路对抗审查完成（5 Tasks verdict + 3 P0：Multi-Vault 全链路 / 生产默认值 / 修主检索链路），response 归档 `_bmad-output/chatgpt-review-response-2026-05-11.md`
- ✅ **合并 Story 2.2+2.9** spec ship + checklist 全勾 (7 AC + 7 Tasks 除 T0 / T6.2/T6.3 perf)
- ✅ T1 plugin timeout (`c5e5a92`) + T2 backend (`6d2c05e`) + T3a assembler (`e0d91c0`) + T3+T5 rerank/evidence (`549d5f0`) — 用户 UAT 通过
- ✅ **Q1+Q2 P0 + Wave-2 hotfix 全闭口** (`de0b4a7` → `f018580`,backend 219 + frontend 186 + 4 security 回归)
- ✅ **Wave-3 hotfix done** (`ec58ee0`,W3-1/2/3/4a/4b — metadata redaction / multi-vault 隔离 / lancedb ContextVar / trim auth header)
- ✅ **Wave-4 Q3 rollback + SKILL.md native Grep 改造 done** (`46fc501`,17 files / +70 / -1478):
  - frontend 删除 `canvas:global-search` 命令 + `handleGlobalSearch` + `global-search.ts` helper + 19 测试
  - backend 删除 POST `/api/v1/chat/global-search` endpoint + multi-seed BFS / `additional_seeds` / `TraceItem.seed_origin`
  - `canvas-vault/.claude/skills/study-question/SKILL.md` 加 HARD-21（native Grep 优先）
  - `canvas-vault/.claude/skills/chat-with-context/SKILL.md` 加 HARD-19（native Grep 优先）
  - Q3 验收单标 `status: deprecated`（audit trail 保留）

**下一步**:
- 用户跑 wave-3 mini-UAT（`Story-2.2+2.9-wave-3-mini-UAT-2026-05-12.md`,Step 1 改为 SKILL.md native Grep 验证）
- 用户跑 Q1/Q2 验收单（Q3 已废,改走 wave-3 mini-UAT Step 1）
- T0 主链路修复 + RAGAs 基准（3-5d 独立 session, P0-C）

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

exec
/bin/zsh -lc "sed -n '1,240p' .claude/rules/development-discipline.md" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 exited 1 in 0ms:
sed: .claude/rules/development-discipline.md: No such file or directory

exec
/bin/zsh -lc "sed -n '1,220p' .claude/rules/plan-traceability.md" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 exited 1 in 0ms:
sed: .claude/rules/plan-traceability.md: No such file or directory

**Planning line-level script inspection**
exec
/bin/zsh -lc 'wc -l backend/scripts/census_dead_letter_episodes.py' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
     475 backend/scripts/census_dead_letter_episodes.py

exec
/bin/zsh -lc 'git diff --no-ext-diff --unified=80 73102875''^ 73102875 -- backend/scripts/census_dead_letter_episodes.py' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
diff --git a/backend/scripts/census_dead_letter_episodes.py b/backend/scripts/census_dead_letter_episodes.py
index ea370cb4..a80b4483 100644
--- a/backend/scripts/census_dead_letter_episodes.py
+++ b/backend/scripts/census_dead_letter_episodes.py
@@ -1,410 +1,475 @@
 #!/usr/bin/env python3
 """CARD-G4-9: dead-letter episodes 只读 census 分诊脚本。
 
 BATCH-2026-08-28-第五批 / CARD-G4-9（G4-10 replay 的交接台账生成器）。
 
 只读契约（grep 可自证 + 运行时守卫）:
   - 无 --apply / 无任何写回、重放、删除路径；
   - 不 import neo4j / graphiti / app.*（纯 stdlib），不建立任何数据库/网络连接，
     唯一的 sqlite 访问经 URI ``mode=ro`` 只读打开 qa_metrics.db；
-  - 唯一写出口是 --out 台账 JSON，且写前做路径碰撞守卫（resolve 后与
-    --dlq/--compare/--qa-metrics-db 任一输入重合即拒绝 exit 2，防 "w" 截断
-    输入文件；Codex round-1 BLOCKER-1 整改）。
+  - 唯一写出口是 --out 台账 JSON，写前双重碰撞守卫：resolve() 路径比较 +
+    **文件身份 (st_dev, st_ino) 比较**，与 --dlq/--compare/--qa-metrics-db
+    任一输入重合即 exit 2，防 "w" 截断输入（round-1 BLOCKER-1 + round-2
+    hardlink / 大小写别名绕过整改）。
 
 快照原子性（Codex round-1 BLOCKER-2 整改）:
   - DLQ 文件只读一次（bytes），头部 sha256/line_count 与逐条 records 全部
     派生自同一份内存字节 —— 台账头部声明的 sha 即 records 所来自的 exact bytes。
 
 判定 fail-closed（Codex round-1 HIGH-1/2/3 整改）:
   - inline 三态: full_verified 要求 sha 对账通过 **且** len(body)==声明长度;
     truncated_prefix 要求声明 sha 为格式合法的 64-hex **且** len(body)==200
     且声明长度>200; 其余一律 anomaly。anomaly 不落 approximate —— 裁
     unrecoverable 并显式给 anomaly basis（不谎称"截断前缀"）。
     注: truncated_prefix 无法用 sha 证明 200 字符确为全文前缀 —— 该性质
     依赖 EpisodeTask.to_dict() 的 [:200] 生产不变量（episode_worker.py），
     台账 recoverability_basis 如实声明。
   - request_id 分组: 键为 (类型名, 值)，缺失/None 记录按 line_no 单条成组
     （不与字面 "None" 或跨类型值合组，杜绝跨 session 误归因传染）。
   - session 归因: 组内多 token 必须满足前缀一致（短 token 是最长 token 的
     前缀），否则记 attribution_conflict、拒绝采信任何 transcript；
     transcript glob 命中必须**恰好 1 个常规文件**才算归因成功，多命中记
-    ambiguous 同样拒绝采信；transcripts 根目录不存在时整体 exit 2
-    （拒绝在源不可见时产出 unrecoverable 假象）。
+    ambiguous 同样拒绝采信；transcripts 根**不存在或不可读/不可遍历**
+    （chmod 000）时整体 exit 2（拒绝在源不可见时产出 unrecoverable 假象）；
+    glob 结果拒绝 symlink 条目与逃逸到根外的目标（round-2 HIGH-3 整改）。
   - DLQ 坏 JSON 行不再炸掉全量: 逐行捕获，class=unparseable 保留 line_no
     进台账（分诊工具不能被单行毒药拒诊）。
   - episode_body_full 若在盘（DEAD_LETTER_STORE_FULL_BODY 开启时生产可写):
-    重算 sha 对账通过则按 byte_exact 采信（Codex round-1 MEDIUM-1 整改）。
+    重算 sha **且长度**双门对账通过才按 byte_exact 采信，且 anomaly 记录
+    不得经此分支翻案（round-1 MEDIUM-1 + round-2 HIGH-1 整改）。
 
 逐条产出（G4-10 消费契约）:
   - stable_key: {line_no, sha256_prefix(16 hex), request_id}。语义 =
     **冻结快照内的 occurrence key**（台账头部 dlq_file.sha256 即快照指纹；
     line_no 在该快照内已唯一，另两列为冗余对账/诊断维度）——不是跨文件
     重排或语义幂等键，G4-10 消费前先 diff 头部 sha。
   - reference_time 逐条透传 + duplicate_clusters 段（同 name+sha+group 的
     语义重复簇），G4-10 重放去重策略依据（Codex round-1 MEDIUM-2 整改）。
   - 隐私: transcript_paths 含本机用户名与 session UUID，台账为 private-only
     工件，禁止外发（Codex round-1 MEDIUM-3；仓库为私有仓，纪律=不 push 公网）。
 """
 
 from __future__ import annotations
 
 import argparse
 import glob
 import hashlib
 import json
 import os
 import re
 import sqlite3
 import sys
 from collections import Counter, defaultdict
 from datetime import datetime, timezone
 from pathlib import Path
 
 # 分类规则: error_type + error 文本特征 → class
 _BUDGET_PAT = re.compile(r"exceed_context_size_error|exceeds the available context size")
 # session token: request_id 组内从 name 提取。已知局限（如实声明）: 纯启发式，
 # hex 样单词（added/deadbeef）可污染 inline 捕获 —— 下游有前缀一致门 + 恰 1 命中门兜底。
 _SESSION_ARCHIVE_PAT = re.compile(r"^session-archive:([0-9a-fA-F-]+)")
 _SESSION_INLINE_PAT = re.compile(r"(?<![0-9a-zA-Z_-])session:([0-9a-f-]{5,})")
 _SHA256_HEX_PAT = re.compile(r"^[0-9a-f]{64}$")
 
 EXPECTED_CLASS_DIST = {"budget_400": 89, "schema_entity_type": 2, "group_id_format": 1}
 
 
 def classify(rec: dict) -> str:
     et = rec.get("error_type", "")
     if et == "EntityTypeValidationError":
         return "schema_entity_type"
     if et == "GroupIdValidationError":
         return "group_id_format"
     if et == "BadRequestError" and _BUDGET_PAT.search(rec.get("error", "")):
         return "budget_400"
     return "unexpected"
 
 
 def inline_state(rec: dict) -> tuple[str, str]:
     """返回 (inline_state, sha_check)，fail-closed（见模块 docstring）。"""
     body = rec.get("episode_body", "")
     declared_len = rec.get("episode_body_length")
     declared_sha = rec.get("episode_body_sha256", "")
     sha_wellformed = isinstance(declared_sha, str) and bool(_SHA256_HEX_PAT.match(declared_sha))
     recomputed = hashlib.sha256(body.encode("utf-8", errors="replace")).hexdigest()
     if sha_wellformed and recomputed == declared_sha and len(body) == declared_len:
         return "full_verified", "pass"
     if sha_wellformed and len(body) == 200 and isinstance(declared_len, int) and declared_len > 200:
         return "truncated_prefix", "prefix_only"
     return "anomaly", "FAIL"
 
 
 def full_body_verified(rec: dict) -> bool:
-    """episode_body_full 在盘且 sha 对账通过（生产 opt-in 字段，当前 live 0 条）。"""
+    """episode_body_full 在盘且 sha **与长度**双门对账通过（生产 opt-in 字段，当前 live 0 条）。
+
+    round-2 HIGH-1 整改: 原实现只核 sha，声明长度矛盾的记录（如 body="abc"
+    但 episode_body_length=999）仍被判 byte_exact —— 与 inline 侧同门收紧。
+    """
     full = rec.get("episode_body_full")
     declared_sha = rec.get("episode_body_sha256", "")
+    declared_len = rec.get("episode_body_length")
     if not isinstance(full, str) or not _SHA256_HEX_PAT.match(str(declared_sha)):
         return False
+    if not isinstance(declared_len, int) or len(full) != declared_len:
+        return False
     return hashlib.sha256(full.encode("utf-8", errors="replace")).hexdigest() == declared_sha
 
 
 def session_tokens(name: str) -> list[str]:
     tokens = []
     m = _SESSION_ARCHIVE_PAT.match(name)
     if m:
         tokens.append(m.group(1).lower())
     tokens.extend(t.lower() for t in _SESSION_INLINE_PAT.findall(name))
     return tokens
 
 
 def resolve_group_attribution(tokens: list[str], transcripts_dir: Path) -> dict:
     """组级归因，fail-closed: 前缀一致门 + 恰 1 个常规文件命中门。"""
     result = {
         "session_token": None,
         "transcript_paths": [],
         "transcript_exists": False,
         "transcript_match_count": 0,
         "attribution_conflict": False,
     }
     uniq = sorted(set(tokens), key=len)
     if not uniq:
         return result
     longest = uniq[-1]
     if any(not longest.startswith(t) for t in uniq[:-1]):
         result["attribution_conflict"] = True
         return result
     result["session_token"] = longest
     pattern = str(transcripts_dir / "**" / f"{longest}*.jsonl")
-    matches = sorted(p for p in glob.glob(pattern, recursive=True) if os.path.isfile(p))
+    # round-2 HIGH-3 整改: 拒绝 symlink 条目与逃逸到根外的目标 —— 原实现
+    # 经 glob+isfile 跟随 symlink，根内 .jsonl→根外 .txt 会被当唯一来源采信。
+    root_real = os.path.realpath(transcripts_dir)
+    matches = []
+    for candidate in glob.glob(pattern, recursive=True):
+        if os.path.islink(candidate) or not os.path.isfile(candidate):
+            continue
+        real = os.path.realpath(candidate)
+        if not real.startswith(root_real + os.sep):
+            continue  # 目录 symlink 逃逸
+        matches.append(candidate)
+    matches = sorted(matches)
     result["transcript_paths"] = matches
     result["transcript_match_count"] = len(matches)
     if len(matches) == 1:
         result["transcript_exists"] = True
     elif len(matches) > 1:
         result["attribution_conflict"] = True  # ambiguous 多命中，拒绝采信
     return result
 
 
 def probe_qa_metrics(db_path: Path, error_types: list[str]) -> dict:
     """只读核销 qa_metrics.db 能否作为源指针（URI mode=ro，无写路径）。"""
     result: dict = {"db_path": str(db_path), "opened_readonly": False}
     if not db_path.exists():
         result["verdict"] = "db_missing"
         return result
     uri = f"file:{db_path}?mode=ro"
     conn = sqlite3.connect(uri, uri=True)
     try:
         result["opened_readonly"] = True
         tables = [
             r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
         ]
         result["tables"] = tables
         if "qa_error_logs" in tables:
             total = conn.execute("SELECT COUNT(*) FROM qa_error_logs").fetchone()[0]
             result["qa_error_logs_rows"] = total
             hits = {}
             for et in sorted(set(error_types)):
                 hits[et] = conn.execute("SELECT COUNT(*) FROM qa_error_logs WHERE error_type = ?", (et,)).fetchone()[0]
             result["error_type_hits"] = hits
             result["verdict"] = "no_source_rows" if total == 0 else "rows_present_see_hits"
         else:
             result["verdict"] = "qa_error_logs_table_missing"
     finally:
         conn.close()
     return result
 
 
 def snapshot_file(path: Path) -> tuple[bytes, dict]:
     """一次性读全量 bytes；描述信息（sha/行数/mtime）全部派生自这份 exact bytes。"""
     raw = path.read_bytes()
     info = {
         "path": str(path),
         "exists": True,
-        "line_count": raw.decode("utf-8", errors="replace").count("\n") + (0 if raw.endswith(b"\n") or not raw else 1),
+        # round-2 LOW 整改: 与 records 的 splitlines() 同口径（bare CR / U+2028
+        # 等行分隔符下 count("\n") 会与 records 数不一致）。
+        "line_count": len(raw.decode("utf-8", errors="replace").splitlines()),
         "sha256": hashlib.sha256(raw).hexdigest(),
         "mtime_utc": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(),
         "mtime_note": "mtime 为 stat 快照，仅供参考；绑定 exact bytes 的是 sha256",
     }
     return raw, info
 
 
 def describe_copy(path: Path) -> dict:
     if not path.exists():
         return {"path": str(path), "exists": False}
     _, info = snapshot_file(path)
     return info
 
 
 def main(argv: list[str] | None = None) -> int:
     ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
     ap.add_argument(
         "--dlq",
         default="data/dead_letter_episodes.jsonl",
         help="DLQ JSONL 路径（census 对 live 挂载运行时传绝对路径）",
     )
     ap.add_argument(
         "--qa-metrics-db",
         default=None,
         help="qa_metrics.db 路径（省略则跳过源指针核销并如实标注 skipped）",
     )
     ap.add_argument(
         "--transcripts-dir",
         default=os.path.expanduser("~/.claude/projects"),
         help="session transcript 根目录（近似恢复源指针核销；不存在则 exit 2 拒诊）",
     )
     ap.add_argument(
         "--compare",
         action="append",
         default=[],
         help="其它 DLQ 副本路径（可重复，产出 sha 对照表）",
     )
     ap.add_argument("--out", default=None, help="台账 JSON 输出路径（省略则打 stdout）")
     args = ap.parse_args(argv)
 
     dlq_path = Path(args.dlq)
     if not dlq_path.exists():
         print(f"DLQ 文件不存在: {dlq_path}", file=sys.stderr)
         return 2
 
     transcripts_dir = Path(args.transcripts_dir)
     if not transcripts_dir.is_dir():
         print(
             f"transcripts 根目录不存在/不可见: {transcripts_dir} —— 拒绝在源不可见时裁定可恢复性（fail-closed）",
             file=sys.stderr,
         )
         return 2
+    # round-2 HIGH-3 整改: 存在但不可读/不可遍历的根（chmod 000）此前 exit 0
+    # 并把全部记录假判 unrecoverable —— 同样 fail-closed 拒诊。
+    if not os.access(transcripts_dir, os.R_OK | os.X_OK):
+        print(
+            f"transcripts 根目录不可读/不可遍历: {transcripts_dir} —— 拒绝在源不可见时裁定可恢复性（fail-closed）",
+            file=sys.stderr,
+        )
+        return 2
 
-    # --out 路径碰撞守卫（写前；resolve 覆盖 symlink 变体）
+    # --out 碰撞守卫（写前）。round-2 BLOCKER-1 整改: 比较**文件身份**
+    # (st_dev, st_ino) 而非 resolve() 字符串 —— 后者对 hardlink 与
+    # 大小写不敏感文件系统上的 case-only 别名均失效（Codex 实测截断输入）。
     if args.out:
-        out_resolved = Path(args.out).resolve()
-        protected = {dlq_path.resolve()} | {Path(p).resolve() for p in args.compare}
+        out_path = Path(args.out)
+        protected_paths = [dlq_path, *(Path(p) for p in args.compare)]
         if args.qa_metrics_db:
-            protected.add(Path(args.qa_metrics_db).resolve())
-        if out_resolved in protected:
+            protected_paths.append(Path(args.qa_metrics_db))
+        protected_ids = set()
+        for candidate in protected_paths:
+            try:
+                st = candidate.stat()  # 跟随 symlink: 保护的是最终目标身份
+                protected_ids.add((st.st_dev, st.st_ino))
+            except OSError:
+                continue
+        # 路径字符串比较作为第二道（输出文件尚不存在时 stat 无身份可比）
+        out_resolved = out_path.resolve()
+        if out_resolved in {p.resolve() for p in protected_paths}:
             print(f"--out 与输入文件路径重合，拒绝写出（防截断）: {out_resolved}", file=sys.stderr)
             return 2
+        if out_path.exists():
+            try:
+                out_st = out_path.stat()
+            except OSError as e:
+                print(f"--out 无法 stat，拒绝写出: {out_path} ({e})", file=sys.stderr)
+                return 2
+            if (out_st.st_dev, out_st.st_ino) in protected_ids:
+                print(
+                    f"--out 与输入文件为同一 inode（hardlink/大小写别名），拒绝写出（防截断）: {out_path}",
+                    file=sys.stderr,
+                )
+                return 2
 
     # BLOCKER-2 整改: 单次读取，records 与头部描述共享同一份 exact bytes
     raw_bytes, dlq_info = snapshot_file(dlq_path)
     raw_lines = raw_bytes.decode("utf-8", errors="replace").splitlines()
 
     records: list[tuple[int, dict]] = []
     unparseable: list[dict] = []
     for line_no, line in enumerate(raw_lines, start=1):
         if not line.strip():
             unparseable.append({"line_no": line_no, "reason": "blank_line"})
             continue
         try:
             rec = json.loads(line)
         except json.JSONDecodeError as e:
             unparseable.append({"line_no": line_no, "reason": f"json_error: {e}", "excerpt": line[:80]})
             continue
         records.append((line_no, rec))
 
     # request_id 分组: (类型名, 值) 复合键；缺失/None → 按 line_no 单条成组
     groups: dict[tuple, list[tuple[int, dict]]] = defaultdict(list)
     for line_no, rec in records:
         rid = rec.get("request_id")
         key = ("__missing__", line_no) if rid is None else (type(rid).__name__, rid)
         groups[key].append((line_no, rec))
     group_attribution: dict[tuple, dict] = {}
     for key, members in groups.items():
         tokens: list[str] = []
         for _, rec in members:
             tokens.extend(session_tokens(rec.get("name", "")))
         group_attribution[key] = resolve_group_attribution(tokens, transcripts_dir)
 
     ledger_records = []
     class_dist: Counter = Counter()
     recover_dist: Counter = Counter()
+    inline_dist: Counter = Counter()
     unrecoverable_keys = []
     attribution_conflicts = []
     for line_no, rec in records:
         cls = classify(rec)
         state, sha_check = inline_state(rec)
         rid = rec.get("request_id")
         key = ("__missing__", line_no) if rid is None else (type(rid).__name__, rid)
         sess = group_attribution[key]
         if state == "full_verified":
             recover = "byte_exact"
             basis = "inline 正文全量：sha256 重算与声明一致且长度精确匹配"
-        elif full_body_verified(rec):
+        elif state != "anomaly" and full_body_verified(rec):
+            # round-2 HIGH-1 整改: anomaly 记录不得经 full_body 分支翻案
             recover = "byte_exact"
-            basis = "episode_body_full 在盘且 sha256 对账通过（DEAD_LETTER_STORE_FULL_BODY 生产 opt-in 字段）"
+            basis = "episode_body_full 在盘且 sha256+长度双门对账通过（DEAD_LETTER_STORE_FULL_BODY 生产 opt-in 字段）"
         elif state == "anomaly":
             recover = "unrecoverable"
             basis = "inline 对不上账（anomaly：sha/长度与声明不符），fail-closed 不采信截断前缀假设，也不采信 transcript 归因"
         elif sess["attribution_conflict"]:
             recover = "unrecoverable"
             basis = "session 归因冲突/多命中（fail-closed 拒绝采信任何 transcript），且 inline 仅截断前缀"
         elif sess["transcript_exists"]:
             recover = "approximate"
             basis = (
                 f"inline 为 200 字符前缀（前缀性质依赖 to_dict()[:200] 生产不变量，sha 无法直接证明）；"
                 f"经 request_id 组归因到唯一在盘 transcript {sess['session_token']}"
                 f"（归因 ≠ 内容已验证——本工具未读 transcript 内容；G4-10 可重蒸馏/重格式化近似重建，非逐字节保证）"
             )
         else:
             recover = "unrecoverable"
             basis = "inline 截断且无在盘上游源"
         class_dist[cls] += 1
         recover_dist[recover] += 1
+        inline_dist[state] += 1
         stable_key = {
             "line_no": line_no,
             "sha256_prefix": str(rec.get("episode_body_sha256", ""))[:16],
             "request_id": rid,
         }
         if recover == "unrecoverable":
             unrecoverable_keys.append(stable_key)
         if sess["attribution_conflict"]:
             attribution_conflicts.append(stable_key)
         ledger_records.append(
             {
                 "stable_key": stable_key,
                 "name": rec.get("name", "")[:80],
                 "group_id": rec.get("group_id"),
                 "source_description": rec.get("source_description"),
                 "error_type": rec.get("error_type"),
                 "error_excerpt": rec.get("error", "")[:120],
                 "failed_at": rec.get("failed_at"),
                 "reference_time": rec.get("reference_time"),
                 "class": cls,
                 "episode_body_length": rec.get("episode_body_length"),
                 "episode_body_sha256": rec.get("episode_body_sha256"),
                 "inline_state": state,
                 "sha_check": sha_check,
                 "session_token": sess["session_token"],
                 "transcript_paths": sess["transcript_paths"],
                 "transcript_match_count": sess["transcript_match_count"],
                 "attribution_conflict": sess["attribution_conflict"],
                 "recoverability": recover,
                 "recoverability_basis": basis,
             }
         )
 
     # 语义重复簇（同 name + 全文 sha + group_id）——G4-10 重放去重策略依据
     cluster_map: dict[tuple, list[int]] = defaultdict(list)
     for line_no, rec in records:
         cluster_map[(rec.get("name", ""), rec.get("episode_body_sha256", ""), rec.get("group_id"))].append(line_no)
     duplicate_clusters = [
         {"name": k[0][:80], "episode_body_sha256": k[1], "group_id": k[2], "line_nos": v, "occurrences": len(v)}
         for k, v in sorted(cluster_map.items(), key=lambda kv: -len(kv[1]))
         if len(v) > 1
     ]
 
     qa_probe = (
         probe_qa_metrics(
             Path(args.qa_metrics_db),
             [r.get("error_type", "") for _, r in records],
         )
         if args.qa_metrics_db
         else {"verdict": "skipped_no_db_arg"}
     )
 
     deviation = {
         k: {"expected": EXPECTED_CLASS_DIST.get(k, 0), "actual": class_dist.get(k, 0)}
         for k in sorted(set(class_dist) | set(EXPECTED_CLASS_DIST))
         if EXPECTED_CLASS_DIST.get(k, 0) != class_dist.get(k, 0)
     }
 
     ledger = {
         "card": "CARD-G4-9",
         "generated_at": datetime.now(timezone.utc).isoformat(),
         "privacy": "private-only: transcript_paths 含本机用户名与 session UUID，禁止外发/公网发布",
         "stable_key_semantics": (
             "冻结快照（dlq_file.sha256）内的 occurrence key；line_no 在快照内唯一，"
             "sha256_prefix/request_id 为冗余对账维度——非跨文件重排或语义幂等键"
         ),
         "dlq_file": dlq_info,
         "compare_copies": [describe_copy(Path(p)) for p in args.compare],
         "total_lines": len(raw_lines),
         "total_records": len(records),
         "unparseable_lines": unparseable,
-        "class_distribution": dict(class_dist),
+        # round-2 LOW 整改: 固定 schema 补零，消费者无需自行补齐缺席键
+        "class_distribution": {
+            k: class_dist.get(k, 0) for k in ["budget_400", "schema_entity_type", "group_id_format", "unexpected"]
+        },
         "expected_class_distribution": EXPECTED_CLASS_DIST,
         "class_deviation": deviation,
-        "recoverability_distribution": dict(recover_dist),
+        "recoverability_distribution": {
+            k: recover_dist.get(k, 0) for k in ["byte_exact", "approximate", "unrecoverable"]
+        },
+        "inline_state_distribution": {
+            k: inline_dist.get(k, 0) for k in ["full_verified", "truncated_prefix", "anomaly"]
+        },
         "unrecoverable_list": unrecoverable_keys,
         "attribution_conflicts": attribution_conflicts,
         "duplicate_clusters": duplicate_clusters,
         "qa_metrics_probe": qa_probe,
         "records": ledger_records,
     }
 
     out_json = json.dumps(ledger, ensure_ascii=False, indent=1)
     if args.out:
         with open(args.out, "w", encoding="utf-8") as f:
             f.write(out_json + "\n")
         print(f"台账已写入: {args.out}")
     else:
         print(out_json)
 
     print(
         f"census: {len(records)} 条 (+{len(unparseable)} unparseable) | class={dict(class_dist)} | "
         f"recoverability={dict(recover_dist)} | 归因冲突={len(attribution_conflicts)} | "
         f"重复簇={len(duplicate_clusters)} | 偏差={deviation or '无'} | "
         f"qa_metrics 核销={qa_probe.get('verdict')}",
         file=sys.stderr,
     )
     return 0
 
 
 if __name__ == "__main__":
     sys.exit(main())

exec
/bin/zsh -lc 'git diff --no-ext-diff --unified=60 73102875''^ 73102875 -- '"'_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md' '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
diff --git "a/_bmad-output/\345\256\241\346\237\245/G4-9-DLQ-census-2026-08-28.md" "b/_bmad-output/\345\256\241\346\237\245/G4-9-DLQ-census-2026-08-28.md"
index ff1f71d1..9c64e8e7 100644
--- "a/_bmad-output/\345\256\241\346\237\245/G4-9-DLQ-census-2026-08-28.md"
+++ "b/_bmad-output/\345\256\241\346\237\245/G4-9-DLQ-census-2026-08-28.md"
@@ -1,124 +1,136 @@
 # CARD-G4-9 — DLQ 真实挂载 census 分诊报告
 
 > **批次**: BATCH-2026-08-28-第五批 / CARD-G4-9（4h · wave 1 · 未来铺路）
 > **性质**: 纯只读 census。0 写入、0 重放、0 业务代码改动。唯一代码产物 = `backend/scripts/census_dead_letter_episodes.py`。
 > **代码基线**: worktree `card/s5-census` @ `37387a86`
 > **台账**: `_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json`（92 条逐条，G4-10 消费）
 > **证据包**: `_bmad-output/审查/G4-9-evidence/`（shasums before/after、grep 自证、容器内 sha 实测）
 > **执行日期**: 2026-08-28
 
 ---
 
 ## §1 挂载真相（live/主仓/孤儿三址 sha 对照 + compose 遮蔽史）
 
 **live DLQ 的唯一权威地址**是 `feature-obsidian-hybrid-dev` worktree 的 `backend/data/`（双树拓扑：线上容器代码挂载自该 worktree）。容器内实测确认同源：
 
 ```
 docker exec canvas-learning-system-backend sha256sum /app/data/dead_letter_episodes.jsonl
 → 3b37460f4215f6ac...ef3ba590（92 行）— 与宿主 live 地址逐字节一致
 ```
 
 | 地址 | 路径 | 行数 | sha256 前 16 | mtime | 裁定 |
 |---|---|---|---|---|---|
 | **live**（权威） | `…/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl` | **92** | `3b37460f4215f6ac` | 2026-08-11 22:01 (+0800) | 容器 `/app/data` 经 `./backend:/app` 挂载即此文件；census 对象 |
 | 主仓 | `canvas-learning-system/backend/data/dead_letter_episodes.jsonl` | 685 | `490c903b2f3636e1` | 2026-04-07 | 陈旧副本（部署迁往 worktree 前的历史死信，止于 4 月）；不代表现网 |
 | 孤儿① | `…/worktrees/feature-obsidian-hybrid-dev/data/dead_letter_episodes.jsonl` | 1 | `bfb3f6c413aab7dd` | 2026-07-13 | 已删除的 `./data:/app/data` 子挂载目标残留；从未在容器内生效 |
 | 孤儿②（附注） | `canvas-learning-system/data/dead_letter_episodes.jsonl` | 4 | `75c5f7593b9b2e99` | 2026-04-06 | 主仓根 `data/` 早期宿主进程 cwd 落点残留 |
 
 **compose :206-212 遮蔽史**（本 worktree `docker-compose.yml:206-212`，与 live worktree 同文）：`- ./data:/app/data` 是嵌套 bind，被 `./backend:/app` 父挂载遮蔽——`docker inspect` 记录了它，但容器 `/proc/self/mountinfo` 从不出现，**实际生效的一直是 `backend/data/`**。R11-BATCH2（2026-08-17）已删除该行，理由是遮蔽与否取决于挂载顺序、一次 recreate 就可能翻转，届时 92 行死信会被 1 行的孤儿①覆盖不可见。删除后 `/app/data` 恒等于 `backend/data/`。**证据边界（诚实声明）**：本卡独立实证的是**现状**（容器内 sha 与宿主 live 地址同源、当前 compose 无子挂载行）；"历史上子挂载从未在容器内生效"沿引 compose 注释史与 R11-BATCH2（2026-08-17）当时的 mountinfo 实测记录，本卡未重跑历史 `docker inspect` 独立复证。
 
 **本 worktree（card-s5-census）没有 `backend/data/dead_letter_episodes.jsonl`**——数据文件不入 git，census 一律指向 live 绝对路径运行，未复制任何数据进本 worktree。
 
 ## §2 总量与分类台账（class 分诊）
 
 92 条，分类与勘探预期**零偏差**：
 
 | class | 条数 | 预期 | error_type | 错误原文（截断） | 根因与修复状态 |
 |---|---|---|---|---|---|
 | `budget_400` | **89** | 89 | BadRequestError | `Error code: 400 … 'request (16998 tokens) exceeds the available context size (16384 tokens)' type: exceed_context_size_error` | 本地 LLM 服务 context 16384 上限被超（实测请求 16948–20831 tokens）。**未修复**——根因治理归 G4-10（切块或提 budget） |
 | `schema_entity_type` | **2** | 2 | EntityTypeValidationError | `name cannot be used as an attribute for LearningConcept as it is a protected attribute name.` | **已修复**：P0-4（2026-05-14）双处——`entity_types.py:343` `LearningConcept.name`→`concept_name`（行 1）+ `entity_types.py:254` `LearningTip.created_at`→`tip_created_at`（行 2），同型冲突不再发生 |
 | `group_id_format` | **1** | 1 | GroupIdValidationError | `group_id "vault:default" must contain only alphanumeric characters, dashes, or underscores` | **已修复**：`group_id_compat.py:64 sanitize_group_id_for_graphiti` 冒号→`__` 物理化已兜（T1 契约），写路径不再直传 D16 冒号格式 |
 | `unexpected` | 0 | 0 | — | — | 无偏差需解释 |
 
 时间分布：3 条 schema/group_id 全部 2026-05-14（P0-4 修复当日之前的失败）；89 条 budget 集中于 2026-08-08 ~ 08-11（8/48/25/8），系 SessionEnd 归档-蒸馏管道对长会话反复触发超限。group_id 分布：`vault:canvas_vault`×89、`vault:default`×3（三条旧格式记录重放时需 group 重映射，见 §6）。
 
 ## §3 inline 完整性 + SHA 对账
 
 `DeadLetterStore.store()` 落盘的 `episode_body` 来自 `EpisodeTask.to_dict()`，后者做 `episode_body[:200]` 截断（`episode_worker.py:107`，"truncate for logging"）；全量正文只有 `DEAD_LETTER_STORE_FULL_BODY` 开启时以 `episode_body_full` 另存——**live 容器该 env 未设置（实测），92 条 `episode_body_full` 均缺席**。逐条重算 sha256(inline) 对账 `episode_body_sha256` 结果：
 
 | inline 状态 | 条数 | 判据 |
 |---|---|---|
-| `full_verified`（内联全量，sha 对账通过） | **4** | 重算值 == 声明值（正文 131–200 字符，天然未截断） |
+| `full_verified`（内联全量，sha 对账通过） | **4** | 重算值 == 声明值且长度精确匹配（四条正文实为 131/142/150/180 字符，范围 **131–180**，天然未截断；round-2 LOW 修正） |
 | `truncated_prefix`（200 字符前缀） | **88** | len(inline)==200、声明 sha 为合法 64-hex 且声明长度 205–8036。**注**：sha 只能证明 inline≠声明全文，"确为前缀"依赖 `to_dict()[:200]` 生产不变量，无法用 sha 直接证明（Codex round-1 HIGH-1 措辞收敛） |
 | `anomaly`（对不上账） | **0** | — |
 
 4 条 full_verified = 3 条 callout（§2 的 schema/group_id 三条）+ 1 条短 qa_highlight（行 74）。
 
 ## §4 源指针核销（qa_metrics.db，只读 mode=ro）
 
 - **qa_metrics.db**（live `backend/data/qa_metrics.db`，经 sqlite URI `mode=ro` 打开）：唯一表 `qa_error_logs`（列 category/error_type/source_module/stack_summary/created_at，**无 request_id 列**），**行数 = 0**。按三个 error_type 探查命中均 0。**核销裁定：`no_source_rows` —— qa_metrics.db 对 92 条死信不构成任何源指针，0/92 可经其溯源。**
 - 附加核销（超出卡面要求，如实记录以封死"还有别处可捞"的幻想）：
   - `llm_call_logs.db`（同目录，mode=ro）：仅 token/延迟/成本指标列，**无 prompt/response 正文**；
   - `backend/data/outbox/`：**空目录**（A7 outbox 只接 enqueue 失败，本 92 条全部是 enqueue 成功、处理失败，不经 outbox）；
   - `episode_body_full`：0 条（§3）。
 - **有效源指针只剩一条**：DLQ 记录的 `request_id`（structlog contextvars 捕获的进程内值）把同一次 SessionEnd 归档的 3–5 条 episode 绑成组，组内 `session-archive:<id16>` / `…session:<hex>` 名字携带 session id → `~/.claude/projects/-…-canvas-vault/<session>.jsonl` transcript。**7 个 session 的 transcript 全部在盘实测存在**（90,584–723,950 字节，逐一恰 1 个 glob 命中、常规文件），88/88 条截断记录归因成功、0 条归因冲突。**归因边界（诚实声明）**：归因 = "唯一在盘候选已定位"，≠ "内容已验证"——本卡未读任何 transcript 内容，内容级核验归 G4-10 重建时以 `episode_body_sha256` 对账。
 
 ## §5 可恢复性三态裁定
 
 | 三态 | 条数 | 裁定依据 |
 |---|---|---|
 | **可字节级**（byte_exact） | **4** | inline 正文全量：sha256 重算对账通过**且**长度精确匹配（fail-closed 双门）——重放可逐字节还原 episode |
 | **近似**（approximate） | **88** | inline 仅 200 字符前缀，但经 request_id 组归因到在盘 transcript；G4-10 可对 22 条 session-archive 重新格式化 transcript（确定性、可用 `episode_body_sha256` 验证是否达字节级）、对 66 条 qa_highlight(44)/distillation(22) 重跑蒸馏（LLM 非确定性，语义近似、不保证逐字节） |
 | **不可恢复**（unrecoverable） | **0** | — |
 
 **不可恢复清单（显式成段）**：本次 census 裁定不可恢复条目 **0 条**；三态裁定覆盖 92/92，**"待定"0 条**。
 
 诚实边界：`近似` ≠ 已恢复。88 条的实际重建（含 22 条 session-archive 是否能达字节级）是 G4-10 的工作与验收，本卡只交付"上游源在盘、路径已核销"的证据链。transcript 属用户本机 `~/.claude/projects/` 数据，若未来被清理，近似裁定随之失效——台账已逐条记录 transcript 绝对路径供 G4-10 开工时复核。
 
 ## §6 台账稳定键（G4-10 交接契约）
 
 台账逐条携带复合键 `{line_no, sha256_prefix(16 hex), request_id}`。**语义（Codex round-1 LOW-2 修正）**：这是**冻结快照内的 occurrence key**，不是跨文件重排或语义幂等键——台账头部 `dlq_file.sha256`（`3b37460f4215f6ac…`）即快照指纹，`line_no` 在该快照内已单列唯一；`sha256_prefix`（本快照 69 个唯一值，qa_highlight 家族实测同名同 sha 多条）与 `request_id`（仅 25 个唯一值，进程内 contextvars、重启可复用）是**冗余对账/诊断维度**，不是唯一性的必要条件。G4-10 消费前先 diff 头部 sha 即知 DLQ 是否长了新条目；语义级去重不得按本键，须按 `duplicate_clusters` 段（见下）。**语义重复簇（MEDIUM-2 整改）**：按 `{name, episode_body_sha256, group_id}` 聚簇，**6 簇覆盖 29 行**（最大簇 = 同一 session-archive 16 行，`reference_time` 各不相同——同内容反复入队反复超限）。台账 `duplicate_clusters` 段逐簇列 line_nos，records 逐条透传 `reference_time`；G4-10 重放前必须先定去重策略（89 条 budget 修根因后若逐条盲放，将把同内容写入最多 16 遍）。
 
 **隐私（MEDIUM-3 整改）**：`transcript_paths` 含本机用户名与完整 session UUID，台账与本报告为 **private-only 工件**（台账头部已带 privacy 字段；仓库纪律 = 不 push 公网远端）。
 
 逐条另带 `class / inline_state / recoverability / transcript_paths / transcript_match_count / attribution_conflict / error_excerpt / failed_at / reference_time`，G4-10 可直接按 `recoverability` 分桶排重放优先级（建议：4 条 byte_exact 先行——但其中 3 条 group_id 为已弃用 `vault:default`，重放前需按 D16 规约重映射并过 `to_physical_group_id()`；89 条 budget_400 重放前必须先修 context 超限根因，否则原样重放必然复现 400）。
 
 ## §7 裁判证据（整改版脚本重跑）
 
 | 证据 | 结果 |
 |---|---|
 | 运行前后 shasum（live/主仓/孤儿①/孤儿② 四份 DLQ + qa_metrics.db） | `diff shasums-before.txt shasums-after.txt` 空 → **PASS，0 写入** |
 | grep 自证（import 行全 stdlib；neo4j/graphiti/bolt/app. import 0 命中；`--apply` 定义 0 命中；写模式 open 仅 `--out` 1 处且受路径碰撞守卫保护） | **PASS**（`grep-selfattest.txt`，含守卫在位证明） |
 | 容器内 sha 实测 | 92 行、sha 与宿主 live 地址一致（`container-sha-check.txt`） |
 | class 偏差 | 无（89/2/1 与勘探预期一致，脚本 `class_deviation` 字段为空） |
-| 负例门（整改自证） | `--out`==`--dlq` → exit 2 拒写、DLQ 完好；transcripts 根缺失 → exit 2 拒诊；sha 匹配但长度不符（Codex HIGH-1 反例①）→ anomaly/unrecoverable；坏 JSON 行/空行 → unparseable 逐行入台账不拒诊 |
+| 负例门（round-1 整改自证） | `--out`==`--dlq` → exit 2 拒写、DLQ 完好；transcripts 根缺失 → exit 2 拒诊；sha 匹配但长度不符（round-1 HIGH-1 反例①）→ anomaly/unrecoverable；坏 JSON 行/空行 → unparseable 逐行入台账不拒诊 |
+| 负例门（round-2 整改自证） | **hardlink** 指向 DLQ 的 --out → exit 2 + DLQ sha 不变；**case-only 别名**（`DLQ.jsonl`）→ exit 2 + DLQ 完好；**anomaly + episode_body_full 组合**（sha 对但长度 999）→ anomaly/unrecoverable（不再翻案 byte_exact）；**chmod 000 根** → exit 2 拒诊；**symlink 逃逸**（根内 .jsonl → 根外 .txt）→ match_count=0/unrecoverable；正例回归：真实唯一命中仍 approximate |
 
 ## §7b Codex round-1 整改记录（BLOCKED → 全项整改）
 
 - **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
 - **BLOCKER-2（快照不原子）**：DLQ 单次 `read_bytes()`，头部 sha256/line_count 与逐条 records 派生自同一份内存字节；mtime 显式标注为 stat 参考值。
 - **BLOCKER-3（交付物未冻结漂移）**：以本卡 commit 冻结全部交付物 exact bytes（脚本/报告/台账/证据包同 commit）；grep-selfattest 已按最终版行号重生成并内嵌脚本 sha 前缀。
 - **HIGH-1（inline 判定不 fail-closed）**：full_verified 加长度精确匹配门；truncated_prefix 加 64-hex 合法性门；anomaly 一律 unrecoverable + 如实 basis（不再谎称截断、不再滑入 approximate）。
 - **HIGH-2（request_id fail-open）**：分组键改 `(类型名, 值)`；缺失/None 按 line_no 单条成组零传染；组内多 token 前缀一致门，冲突记 `attribution_conflict` 拒绝采信（现网 92 条 0 冲突）。
 - **HIGH-3（transcript 归因折叠）**：恰 1 个常规文件命中才算归因（多命中 = ambiguous 拒采信）；glob 改递归下探；transcripts 根缺失整体 exit 2（拒绝产出 unrecoverable 假象）。
 - **MEDIUM-1**：`episode_body_full` 在盘且 sha 对账通过 → byte_exact 采信（现网 0 条，通路已备）。
 - **MEDIUM-2**：`duplicate_clusters` 段 + 逐条 `reference_time`（见 §6）。
 - **MEDIUM-3**：台账头部 privacy 字段 + 本报告 private-only 声明（见 §6）。
 - **LOW-1~4**：token 区间 16948–20831、长度区间 205–8036、稳定键语义重写、schema 双处证据、挂载历史证据边界——均已在正文落地。
 
 整改后全量重跑：**92 条数字与整改前逐项一致**（class 89/2/1、三态 4/88/0、归因冲突 0、unparseable 0），重复簇 6/29 行与 Codex 独立复算吻合。另有独立 Workflow 4-agent 复核（92 条重算 0 mismatch、7 transcript 在盘实测、台账 sha 一致）交叉确认。
 
+## §7c Codex round-2 复审整改记录（10/13 CLOSED → 剩余 3 项 + 3 新 LOW 全部整改）
+
+round-2 复审确认 BLOCKER-2/3、HIGH-2、MEDIUM-1~3、LOW-1~4 共 10 项 CLOSED，并抓出 3 项**未真正闭合**（均实测复现）+ 3 条新 LOW：
+
+- **BLOCKER-1 NOT-CLOSED（hardlink / case-only 别名绕过）**：原守卫比较 `resolve()` **字符串**，hardlink 指向输入、以及大小写不敏感文件系统上的 case-only 别名均绕过并截断输入。**整改**：改为比较**文件身份 `(st_dev, st_ino)`**（对已存在的 --out）+ 保留路径比较作第二道。负例实测：两种绕过均 exit 2、DLQ sha 不变。
+- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
+- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
+- **新 LOW ×3**：full_verified 长度范围修正为 131–180；台账 `class_distribution`/`recoverability_distribution` 补零并新增 `inline_state_distribution`（固定 schema，消费者无需补齐缺席键）；`line_count` 改用 `splitlines()` 与 records 同口径（原 `count("\n")` 在 bare CR / U+2028 下会与 records 数不一致）。
+
+round-2 整改后再次全量重跑：92 条、class 89/2/1、三态 4/88/0、重复簇 6/29、shasum 不变——**数字仍逐项一致**，整改只收紧通用鲁棒性。
+
 ## §8 复现命令
 
 ```bash
 cd .claude/worktrees/card-s5-census
 python3 backend/scripts/census_dead_letter_episodes.py \
   --dlq "…/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl" \
   --qa-metrics-db "…/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db" \
   --compare "…/canvas-learning-system/backend/data/dead_letter_episodes.jsonl" \
   --compare "…/feature-obsidian-hybrid-dev/data/dead_letter_episodes.jsonl" \
   --compare "…/canvas-learning-system/data/dead_letter_episodes.jsonl" \
   --out "_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json"
 ```
 
 诚实标注（与卡面一致）：本卡离用户日常价值远，属恢复能力地基；未修任何根因，未重放任何条目。
diff --git "a/_bmad-output/\345\256\241\346\237\245/G4-9-dlq-ledger-2026-08-28.json" "b/_bmad-output/\345\256\241\346\237\245/G4-9-dlq-ledger-2026-08-28.json"
index 6ce5772b..95c2881a 100644
--- "a/_bmad-output/\345\256\241\346\237\245/G4-9-dlq-ledger-2026-08-28.json"
+++ "b/_bmad-output/\345\256\241\346\237\245/G4-9-dlq-ledger-2026-08-28.json"
@@ -1,116 +1,123 @@
 {
  "card": "CARD-G4-9",
- "generated_at": "2026-08-28T09:26:28.851136+00:00",
+ "generated_at": "2026-08-28T11:11:58.320970+00:00",
  "privacy": "private-only: transcript_paths 含本机用户名与 session UUID，禁止外发/公网发布",
  "stable_key_semantics": "冻结快照（dlq_file.sha256）内的 occurrence key；line_no 在快照内唯一，sha256_prefix/request_id 为冗余对账维度——非跨文件重排或语义幂等键",
  "dlq_file": {
   "path": "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl",
   "exists": true,
   "line_count": 92,
   "sha256": "3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590",
   "mtime_utc": "2026-08-11T14:01:25.808462+00:00",
   "mtime_note": "mtime 为 stat 快照，仅供参考；绑定 exact bytes 的是 sha256"
  },
  "compare_copies": [
   {
    "path": "/Users/Heishing/Desktop/canvas/canvas-learning-system/backend/data/dead_letter_episodes.jsonl",
    "exists": true,
    "line_count": 685,
    "sha256": "490c903b2f3636e1d2c4ecb68465cef41ace06f0bd171eb2fb95c03a7b40cb43",
    "mtime_utc": "2026-04-07T11:47:19.585617+00:00",
    "mtime_note": "mtime 为 stat 快照，仅供参考；绑定 exact bytes 的是 sha256"
   },
   {
    "path": "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/data/dead_letter_episodes.jsonl",
    "exists": true,
    "line_count": 1,
    "sha256": "bfb3f6c413aab7dd4c04a25f7575aaaffcfc92fd4e8e8966362609652ac7e310",
    "mtime_utc": "2026-07-13T04:51:14.925282+00:00",
    "mtime_note": "mtime 为 stat 快照，仅供参考；绑定 exact bytes 的是 sha256"
   },
   {
    "path": "/Users/Heishing/Desktop/canvas/canvas-learning-system/data/dead_letter_episodes.jsonl",
    "exists": true,
    "line_count": 4,
    "sha256": "75c5f7593b9b2e99672d0551487b4476552ebd8d33ad25c5f9479683cc61e9c9",
    "mtime_utc": "2026-04-05T23:30:49.019652+00:00",
    "mtime_note": "mtime 为 stat 快照，仅供参考；绑定 exact bytes 的是 sha256"
   }
  ],
  "total_lines": 92,
  "total_records": 92,
  "unparseable_lines": [],
  "class_distribution": {
+  "budget_400": 89,
   "schema_entity_type": 2,
   "group_id_format": 1,
-  "budget_400": 89
+  "unexpected": 0
  },
  "expected_class_distribution": {
   "budget_400": 89,
   "schema_entity_type": 2,
   "group_id_format": 1
  },
  "class_deviation": {},
  "recoverability_distribution": {
   "byte_exact": 4,
-  "approximate": 88
+  "approximate": 88,
+  "unrecoverable": 0
+ },
+ "inline_state_distribution": {
+  "full_verified": 4,
+  "truncated_prefix": 88,
+  "anomaly": 0
  },
  "unrecoverable_list": [],
  "attribution_conflicts": [],
  "duplicate_clusters": [
   {
    "name": "session-archive:426ffbde-15f6-4b",
    "episode_body_sha256": "c93058c9850c6999310e98df9e6ebc26063b96fa6f0649fb1ec6d9d04c88a7fe",
    "group_id": "vault:canvas_vault",
    "line_nos": [
     11,
     15,
     22,
     26,
     32,
     39,
     43,
     47,
     55,
     63,
     67,
     71,
     80,
     84,
     88,
     92
    ],
    "occurrences": 16
   },
   {
    "name": "qa_highlight:Q: What is the relationship between a co",
    "episode_body_sha256": "f22956e79a5a23be64d05cd806fd78773916c5bc40b10f9cfd7d5fda0814e10e",
    "group_id": "vault:canvas_vault",
    "line_nos": [
     24,
     41,
     78,
     82
    ],
    "occurrences": 4
   },
   {
    "name": "conversation_distillation:Distilled summary for node session:426ff",
    "episode_body_sha256": "f9682670197b1339166db46bc7a6b49cca01d745e100568dfdd88b6aa15c6f51",
    "group_id": "vault:canvas_vault",
    "line_nos": [
     8,
     12,
     68
    ],
    "occurrences": 3
   },
   {
    "name": "qa_highlight:Q: What is the relationship between a co",
    "episode_body_sha256": "7a830d4e3c5d52fe3699e0065c5ab61ae013eca3dcf6dd79cf246e37fc4d8629",
    "group_id": "vault:canvas_vault",
    "line_nos": [
     13,
     45
    ],
    "occurrences": 2

exec
/bin/zsh -lc 'git show --no-ext-diff --format=fuller --no-patch 73102875' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
commit 73102875fdd9837f0d60cf2ed6cf4ea7f6f8c2e5
Author:     oinani0721 <2272104243@qq.com>
AuthorDate: Fri Aug 28 19:15:00 2026 +0800
Commit:     oinani0721 <2272104243@qq.com>
CommitDate: Fri Aug 28 19:15:00 2026 +0800

    fix(census): G4-9/G4-16 Codex round-2 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9 / CARD-G4-16]
    
    G4-9(10/13→13/13): --out 守卫改比 inode 身份(封 hardlink+大小写别名绕过)、
    full_body 加长度门且 anomaly 优先(封翻案)、transcripts 根不可读 exit 2 +
    symlink 逃逸拒采信、3 新 LOW(长度范围/distribution 补零/line_count 同口径)。
    5 条新负例实测全过、正例无回归、92 条数字与 4/88/0 逐项不变。
    G4-16(7/10→10/10): 自由值权重加路径条件、§8 摘要与 §1 口径统一、测试
    provenance 补强+历史 stdout 诚实边界、source_type 赋值链修正、reranker
    陈旧算例注记、字面量 grep 降级辅助视图、根脚本行号按 pinned SHA 修正。
    两 py 文件与 37387a86 的 AST 仍全等(注释-only)，落点测试 9 failed/102 passed
    与基线同集合。round-2 审查存档含 cyber 误拦抢救说明。
    
    Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>

**Planning detailed script inspection**
**Analyzing TOCTOU and path alias vulnerabilities**
**Verifying path existence and stat consistency**
**Analyzing symlink and race condition risks**
**Evaluating TOCTOU severity and edge cases**
**Identifying Unicode normalization bypass risk**
**Identifying transcript overwrite vulnerability**
**Evaluating output path scope and access checks**
**Verifying os.access behavior under root**
**Analyzing glob permission edge case**
**Evaluating symlink and path containment checks**
**Confirming symlink loop and path handling**
**Analyzing transcripts directory path handling**
**Evaluating root symlink and length validation nuances**
**Confirming full verification despite length type anomaly**
**Analyzing Unicode encoding impact on hashing**
**Verifying record length and distribution consistency**
**Confirming access to raw DLQ transcripts**
**Verifying ledger-based transcript handling**
exec
/bin/zsh -lc "nl -ba backend/scripts/census_dead_letter_episodes.py | sed -n '1,180p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
     1	#!/usr/bin/env python3
     2	"""CARD-G4-9: dead-letter episodes 只读 census 分诊脚本。
     3	
     4	BATCH-2026-08-28-第五批 / CARD-G4-9（G4-10 replay 的交接台账生成器）。
     5	
     6	只读契约（grep 可自证 + 运行时守卫）:
     7	  - 无 --apply / 无任何写回、重放、删除路径；
     8	  - 不 import neo4j / graphiti / app.*（纯 stdlib），不建立任何数据库/网络连接，
     9	    唯一的 sqlite 访问经 URI ``mode=ro`` 只读打开 qa_metrics.db；
    10	  - 唯一写出口是 --out 台账 JSON，写前双重碰撞守卫：resolve() 路径比较 +
    11	    **文件身份 (st_dev, st_ino) 比较**，与 --dlq/--compare/--qa-metrics-db
    12	    任一输入重合即 exit 2，防 "w" 截断输入（round-1 BLOCKER-1 + round-2
    13	    hardlink / 大小写别名绕过整改）。
    14	
    15	快照原子性（Codex round-1 BLOCKER-2 整改）:
    16	  - DLQ 文件只读一次（bytes），头部 sha256/line_count 与逐条 records 全部
    17	    派生自同一份内存字节 —— 台账头部声明的 sha 即 records 所来自的 exact bytes。
    18	
    19	判定 fail-closed（Codex round-1 HIGH-1/2/3 整改）:
    20	  - inline 三态: full_verified 要求 sha 对账通过 **且** len(body)==声明长度;
    21	    truncated_prefix 要求声明 sha 为格式合法的 64-hex **且** len(body)==200
    22	    且声明长度>200; 其余一律 anomaly。anomaly 不落 approximate —— 裁
    23	    unrecoverable 并显式给 anomaly basis（不谎称"截断前缀"）。
    24	    注: truncated_prefix 无法用 sha 证明 200 字符确为全文前缀 —— 该性质
    25	    依赖 EpisodeTask.to_dict() 的 [:200] 生产不变量（episode_worker.py），
    26	    台账 recoverability_basis 如实声明。
    27	  - request_id 分组: 键为 (类型名, 值)，缺失/None 记录按 line_no 单条成组
    28	    （不与字面 "None" 或跨类型值合组，杜绝跨 session 误归因传染）。
    29	  - session 归因: 组内多 token 必须满足前缀一致（短 token 是最长 token 的
    30	    前缀），否则记 attribution_conflict、拒绝采信任何 transcript；
    31	    transcript glob 命中必须**恰好 1 个常规文件**才算归因成功，多命中记
    32	    ambiguous 同样拒绝采信；transcripts 根**不存在或不可读/不可遍历**
    33	    （chmod 000）时整体 exit 2（拒绝在源不可见时产出 unrecoverable 假象）；
    34	    glob 结果拒绝 symlink 条目与逃逸到根外的目标（round-2 HIGH-3 整改）。
    35	  - DLQ 坏 JSON 行不再炸掉全量: 逐行捕获，class=unparseable 保留 line_no
    36	    进台账（分诊工具不能被单行毒药拒诊）。
    37	  - episode_body_full 若在盘（DEAD_LETTER_STORE_FULL_BODY 开启时生产可写):
    38	    重算 sha **且长度**双门对账通过才按 byte_exact 采信，且 anomaly 记录
    39	    不得经此分支翻案（round-1 MEDIUM-1 + round-2 HIGH-1 整改）。
    40	
    41	逐条产出（G4-10 消费契约）:
    42	  - stable_key: {line_no, sha256_prefix(16 hex), request_id}。语义 =
    43	    **冻结快照内的 occurrence key**（台账头部 dlq_file.sha256 即快照指纹；
    44	    line_no 在该快照内已唯一，另两列为冗余对账/诊断维度）——不是跨文件
    45	    重排或语义幂等键，G4-10 消费前先 diff 头部 sha。
    46	  - reference_time 逐条透传 + duplicate_clusters 段（同 name+sha+group 的
    47	    语义重复簇），G4-10 重放去重策略依据（Codex round-1 MEDIUM-2 整改）。
    48	  - 隐私: transcript_paths 含本机用户名与 session UUID，台账为 private-only
    49	    工件，禁止外发（Codex round-1 MEDIUM-3；仓库为私有仓，纪律=不 push 公网）。
    50	"""
    51	
    52	from __future__ import annotations
    53	
    54	import argparse
    55	import glob
    56	import hashlib
    57	import json
    58	import os
    59	import re
    60	import sqlite3
    61	import sys
    62	from collections import Counter, defaultdict
    63	from datetime import datetime, timezone
    64	from pathlib import Path
    65	
    66	# 分类规则: error_type + error 文本特征 → class
    67	_BUDGET_PAT = re.compile(r"exceed_context_size_error|exceeds the available context size")
    68	# session token: request_id 组内从 name 提取。已知局限（如实声明）: 纯启发式，
    69	# hex 样单词（added/deadbeef）可污染 inline 捕获 —— 下游有前缀一致门 + 恰 1 命中门兜底。
    70	_SESSION_ARCHIVE_PAT = re.compile(r"^session-archive:([0-9a-fA-F-]+)")
    71	_SESSION_INLINE_PAT = re.compile(r"(?<![0-9a-zA-Z_-])session:([0-9a-f-]{5,})")
    72	_SHA256_HEX_PAT = re.compile(r"^[0-9a-f]{64}$")
    73	
    74	EXPECTED_CLASS_DIST = {"budget_400": 89, "schema_entity_type": 2, "group_id_format": 1}
    75	
    76	
    77	def classify(rec: dict) -> str:
    78	    et = rec.get("error_type", "")
    79	    if et == "EntityTypeValidationError":
    80	        return "schema_entity_type"
    81	    if et == "GroupIdValidationError":
    82	        return "group_id_format"
    83	    if et == "BadRequestError" and _BUDGET_PAT.search(rec.get("error", "")):
    84	        return "budget_400"
    85	    return "unexpected"
    86	
    87	
    88	def inline_state(rec: dict) -> tuple[str, str]:
    89	    """返回 (inline_state, sha_check)，fail-closed（见模块 docstring）。"""
    90	    body = rec.get("episode_body", "")
    91	    declared_len = rec.get("episode_body_length")
    92	    declared_sha = rec.get("episode_body_sha256", "")
    93	    sha_wellformed = isinstance(declared_sha, str) and bool(_SHA256_HEX_PAT.match(declared_sha))
    94	    recomputed = hashlib.sha256(body.encode("utf-8", errors="replace")).hexdigest()
    95	    if sha_wellformed and recomputed == declared_sha and len(body) == declared_len:
    96	        return "full_verified", "pass"
    97	    if sha_wellformed and len(body) == 200 and isinstance(declared_len, int) and declared_len > 200:
    98	        return "truncated_prefix", "prefix_only"
    99	    return "anomaly", "FAIL"
   100	
   101	
   102	def full_body_verified(rec: dict) -> bool:
   103	    """episode_body_full 在盘且 sha **与长度**双门对账通过（生产 opt-in 字段，当前 live 0 条）。
   104	
   105	    round-2 HIGH-1 整改: 原实现只核 sha，声明长度矛盾的记录（如 body="abc"
   106	    但 episode_body_length=999）仍被判 byte_exact —— 与 inline 侧同门收紧。
   107	    """
   108	    full = rec.get("episode_body_full")
   109	    declared_sha = rec.get("episode_body_sha256", "")
   110	    declared_len = rec.get("episode_body_length")
   111	    if not isinstance(full, str) or not _SHA256_HEX_PAT.match(str(declared_sha)):
   112	        return False
   113	    if not isinstance(declared_len, int) or len(full) != declared_len:
   114	        return False
   115	    return hashlib.sha256(full.encode("utf-8", errors="replace")).hexdigest() == declared_sha
   116	
   117	
   118	def session_tokens(name: str) -> list[str]:
   119	    tokens = []
   120	    m = _SESSION_ARCHIVE_PAT.match(name)
   121	    if m:
   122	        tokens.append(m.group(1).lower())
   123	    tokens.extend(t.lower() for t in _SESSION_INLINE_PAT.findall(name))
   124	    return tokens
   125	
   126	
   127	def resolve_group_attribution(tokens: list[str], transcripts_dir: Path) -> dict:
   128	    """组级归因，fail-closed: 前缀一致门 + 恰 1 个常规文件命中门。"""
   129	    result = {
   130	        "session_token": None,
   131	        "transcript_paths": [],
   132	        "transcript_exists": False,
   133	        "transcript_match_count": 0,
   134	        "attribution_conflict": False,
   135	    }
   136	    uniq = sorted(set(tokens), key=len)
   137	    if not uniq:
   138	        return result
   139	    longest = uniq[-1]
   140	    if any(not longest.startswith(t) for t in uniq[:-1]):
   141	        result["attribution_conflict"] = True
   142	        return result
   143	    result["session_token"] = longest
   144	    pattern = str(transcripts_dir / "**" / f"{longest}*.jsonl")
   145	    # round-2 HIGH-3 整改: 拒绝 symlink 条目与逃逸到根外的目标 —— 原实现
   146	    # 经 glob+isfile 跟随 symlink，根内 .jsonl→根外 .txt 会被当唯一来源采信。
   147	    root_real = os.path.realpath(transcripts_dir)
   148	    matches = []
   149	    for candidate in glob.glob(pattern, recursive=True):
   150	        if os.path.islink(candidate) or not os.path.isfile(candidate):
   151	            continue
   152	        real = os.path.realpath(candidate)
   153	        if not real.startswith(root_real + os.sep):
   154	            continue  # 目录 symlink 逃逸
   155	        matches.append(candidate)
   156	    matches = sorted(matches)
   157	    result["transcript_paths"] = matches
   158	    result["transcript_match_count"] = len(matches)
   159	    if len(matches) == 1:
   160	        result["transcript_exists"] = True
   161	    elif len(matches) > 1:
   162	        result["attribution_conflict"] = True  # ambiguous 多命中，拒绝采信
   163	    return result
   164	
   165	
   166	def probe_qa_metrics(db_path: Path, error_types: list[str]) -> dict:
   167	    """只读核销 qa_metrics.db 能否作为源指针（URI mode=ro，无写路径）。"""
   168	    result: dict = {"db_path": str(db_path), "opened_readonly": False}
   169	    if not db_path.exists():
   170	        result["verdict"] = "db_missing"
   171	        return result
   172	    uri = f"file:{db_path}?mode=ro"
   173	    conn = sqlite3.connect(uri, uri=True)
   174	    try:
   175	        result["opened_readonly"] = True
   176	        tables = [
   177	            r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
   178	        ]
   179	        result["tables"] = tables
   180	        if "qa_error_logs" in tables:

exec
/bin/zsh -lc "nl -ba backend/scripts/census_dead_letter_episodes.py | sed -n '181,360p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
   181	            total = conn.execute("SELECT COUNT(*) FROM qa_error_logs").fetchone()[0]
   182	            result["qa_error_logs_rows"] = total
   183	            hits = {}
   184	            for et in sorted(set(error_types)):
   185	                hits[et] = conn.execute("SELECT COUNT(*) FROM qa_error_logs WHERE error_type = ?", (et,)).fetchone()[0]
   186	            result["error_type_hits"] = hits
   187	            result["verdict"] = "no_source_rows" if total == 0 else "rows_present_see_hits"
   188	        else:
   189	            result["verdict"] = "qa_error_logs_table_missing"
   190	    finally:
   191	        conn.close()
   192	    return result
   193	
   194	
   195	def snapshot_file(path: Path) -> tuple[bytes, dict]:
   196	    """一次性读全量 bytes；描述信息（sha/行数/mtime）全部派生自这份 exact bytes。"""
   197	    raw = path.read_bytes()
   198	    info = {
   199	        "path": str(path),
   200	        "exists": True,
   201	        # round-2 LOW 整改: 与 records 的 splitlines() 同口径（bare CR / U+2028
   202	        # 等行分隔符下 count("\n") 会与 records 数不一致）。
   203	        "line_count": len(raw.decode("utf-8", errors="replace").splitlines()),
   204	        "sha256": hashlib.sha256(raw).hexdigest(),
   205	        "mtime_utc": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(),
   206	        "mtime_note": "mtime 为 stat 快照，仅供参考；绑定 exact bytes 的是 sha256",
   207	    }
   208	    return raw, info
   209	
   210	
   211	def describe_copy(path: Path) -> dict:
   212	    if not path.exists():
   213	        return {"path": str(path), "exists": False}
   214	    _, info = snapshot_file(path)
   215	    return info
   216	
   217	
   218	def main(argv: list[str] | None = None) -> int:
   219	    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
   220	    ap.add_argument(
   221	        "--dlq",
   222	        default="data/dead_letter_episodes.jsonl",
   223	        help="DLQ JSONL 路径（census 对 live 挂载运行时传绝对路径）",
   224	    )
   225	    ap.add_argument(
   226	        "--qa-metrics-db",
   227	        default=None,
   228	        help="qa_metrics.db 路径（省略则跳过源指针核销并如实标注 skipped）",
   229	    )
   230	    ap.add_argument(
   231	        "--transcripts-dir",
   232	        default=os.path.expanduser("~/.claude/projects"),
   233	        help="session transcript 根目录（近似恢复源指针核销；不存在则 exit 2 拒诊）",
   234	    )
   235	    ap.add_argument(
   236	        "--compare",
   237	        action="append",
   238	        default=[],
   239	        help="其它 DLQ 副本路径（可重复，产出 sha 对照表）",
   240	    )
   241	    ap.add_argument("--out", default=None, help="台账 JSON 输出路径（省略则打 stdout）")
   242	    args = ap.parse_args(argv)
   243	
   244	    dlq_path = Path(args.dlq)
   245	    if not dlq_path.exists():
   246	        print(f"DLQ 文件不存在: {dlq_path}", file=sys.stderr)
   247	        return 2
   248	
   249	    transcripts_dir = Path(args.transcripts_dir)
   250	    if not transcripts_dir.is_dir():
   251	        print(
   252	            f"transcripts 根目录不存在/不可见: {transcripts_dir} —— 拒绝在源不可见时裁定可恢复性（fail-closed）",
   253	            file=sys.stderr,
   254	        )
   255	        return 2
   256	    # round-2 HIGH-3 整改: 存在但不可读/不可遍历的根（chmod 000）此前 exit 0
   257	    # 并把全部记录假判 unrecoverable —— 同样 fail-closed 拒诊。
   258	    if not os.access(transcripts_dir, os.R_OK | os.X_OK):
   259	        print(
   260	            f"transcripts 根目录不可读/不可遍历: {transcripts_dir} —— 拒绝在源不可见时裁定可恢复性（fail-closed）",
   261	            file=sys.stderr,
   262	        )
   263	        return 2
   264	
   265	    # --out 碰撞守卫（写前）。round-2 BLOCKER-1 整改: 比较**文件身份**
   266	    # (st_dev, st_ino) 而非 resolve() 字符串 —— 后者对 hardlink 与
   267	    # 大小写不敏感文件系统上的 case-only 别名均失效（Codex 实测截断输入）。
   268	    if args.out:
   269	        out_path = Path(args.out)
   270	        protected_paths = [dlq_path, *(Path(p) for p in args.compare)]
   271	        if args.qa_metrics_db:
   272	            protected_paths.append(Path(args.qa_metrics_db))
   273	        protected_ids = set()
   274	        for candidate in protected_paths:
   275	            try:
   276	                st = candidate.stat()  # 跟随 symlink: 保护的是最终目标身份
   277	                protected_ids.add((st.st_dev, st.st_ino))
   278	            except OSError:
   279	                continue
   280	        # 路径字符串比较作为第二道（输出文件尚不存在时 stat 无身份可比）
   281	        out_resolved = out_path.resolve()
   282	        if out_resolved in {p.resolve() for p in protected_paths}:
   283	            print(f"--out 与输入文件路径重合，拒绝写出（防截断）: {out_resolved}", file=sys.stderr)
   284	            return 2
   285	        if out_path.exists():
   286	            try:
   287	                out_st = out_path.stat()
   288	            except OSError as e:
   289	                print(f"--out 无法 stat，拒绝写出: {out_path} ({e})", file=sys.stderr)
   290	                return 2
   291	            if (out_st.st_dev, out_st.st_ino) in protected_ids:
   292	                print(
   293	                    f"--out 与输入文件为同一 inode（hardlink/大小写别名），拒绝写出（防截断）: {out_path}",
   294	                    file=sys.stderr,
   295	                )
   296	                return 2
   297	
   298	    # BLOCKER-2 整改: 单次读取，records 与头部描述共享同一份 exact bytes
   299	    raw_bytes, dlq_info = snapshot_file(dlq_path)
   300	    raw_lines = raw_bytes.decode("utf-8", errors="replace").splitlines()
   301	
   302	    records: list[tuple[int, dict]] = []
   303	    unparseable: list[dict] = []
   304	    for line_no, line in enumerate(raw_lines, start=1):
   305	        if not line.strip():
   306	            unparseable.append({"line_no": line_no, "reason": "blank_line"})
   307	            continue
   308	        try:
   309	            rec = json.loads(line)
   310	        except json.JSONDecodeError as e:
   311	            unparseable.append({"line_no": line_no, "reason": f"json_error: {e}", "excerpt": line[:80]})
   312	            continue
   313	        records.append((line_no, rec))
   314	
   315	    # request_id 分组: (类型名, 值) 复合键；缺失/None → 按 line_no 单条成组
   316	    groups: dict[tuple, list[tuple[int, dict]]] = defaultdict(list)
   317	    for line_no, rec in records:
   318	        rid = rec.get("request_id")
   319	        key = ("__missing__", line_no) if rid is None else (type(rid).__name__, rid)
   320	        groups[key].append((line_no, rec))
   321	    group_attribution: dict[tuple, dict] = {}
   322	    for key, members in groups.items():
   323	        tokens: list[str] = []
   324	        for _, rec in members:
   325	            tokens.extend(session_tokens(rec.get("name", "")))
   326	        group_attribution[key] = resolve_group_attribution(tokens, transcripts_dir)
   327	
   328	    ledger_records = []
   329	    class_dist: Counter = Counter()
   330	    recover_dist: Counter = Counter()
   331	    inline_dist: Counter = Counter()
   332	    unrecoverable_keys = []
   333	    attribution_conflicts = []
   334	    for line_no, rec in records:
   335	        cls = classify(rec)
   336	        state, sha_check = inline_state(rec)
   337	        rid = rec.get("request_id")
   338	        key = ("__missing__", line_no) if rid is None else (type(rid).__name__, rid)
   339	        sess = group_attribution[key]
   340	        if state == "full_verified":
   341	            recover = "byte_exact"
   342	            basis = "inline 正文全量：sha256 重算与声明一致且长度精确匹配"
   343	        elif state != "anomaly" and full_body_verified(rec):
   344	            # round-2 HIGH-1 整改: anomaly 记录不得经 full_body 分支翻案
   345	            recover = "byte_exact"
   346	            basis = "episode_body_full 在盘且 sha256+长度双门对账通过（DEAD_LETTER_STORE_FULL_BODY 生产 opt-in 字段）"
   347	        elif state == "anomaly":
   348	            recover = "unrecoverable"
   349	            basis = "inline 对不上账（anomaly：sha/长度与声明不符），fail-closed 不采信截断前缀假设，也不采信 transcript 归因"
   350	        elif sess["attribution_conflict"]:
   351	            recover = "unrecoverable"
   352	            basis = "session 归因冲突/多命中（fail-closed 拒绝采信任何 transcript），且 inline 仅截断前缀"
   353	        elif sess["transcript_exists"]:
   354	            recover = "approximate"
   355	            basis = (
   356	                f"inline 为 200 字符前缀（前缀性质依赖 to_dict()[:200] 生产不变量，sha 无法直接证明）；"
   357	                f"经 request_id 组归因到唯一在盘 transcript {sess['session_token']}"
   358	                f"（归因 ≠ 内容已验证——本工具未读 transcript 内容；G4-10 可重蒸馏/重格式化近似重建，非逐字节保证）"
   359	            )
   360	        else:

exec
/bin/zsh -lc "nl -ba backend/scripts/census_dead_letter_episodes.py | sed -n '361,520p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
   361	            recover = "unrecoverable"
   362	            basis = "inline 截断且无在盘上游源"
   363	        class_dist[cls] += 1
   364	        recover_dist[recover] += 1
   365	        inline_dist[state] += 1
   366	        stable_key = {
   367	            "line_no": line_no,
   368	            "sha256_prefix": str(rec.get("episode_body_sha256", ""))[:16],
   369	            "request_id": rid,
   370	        }
   371	        if recover == "unrecoverable":
   372	            unrecoverable_keys.append(stable_key)
   373	        if sess["attribution_conflict"]:
   374	            attribution_conflicts.append(stable_key)
   375	        ledger_records.append(
   376	            {
   377	                "stable_key": stable_key,
   378	                "name": rec.get("name", "")[:80],
   379	                "group_id": rec.get("group_id"),
   380	                "source_description": rec.get("source_description"),
   381	                "error_type": rec.get("error_type"),
   382	                "error_excerpt": rec.get("error", "")[:120],
   383	                "failed_at": rec.get("failed_at"),
   384	                "reference_time": rec.get("reference_time"),
   385	                "class": cls,
   386	                "episode_body_length": rec.get("episode_body_length"),
   387	                "episode_body_sha256": rec.get("episode_body_sha256"),
   388	                "inline_state": state,
   389	                "sha_check": sha_check,
   390	                "session_token": sess["session_token"],
   391	                "transcript_paths": sess["transcript_paths"],
   392	                "transcript_match_count": sess["transcript_match_count"],
   393	                "attribution_conflict": sess["attribution_conflict"],
   394	                "recoverability": recover,
   395	                "recoverability_basis": basis,
   396	            }
   397	        )
   398	
   399	    # 语义重复簇（同 name + 全文 sha + group_id）——G4-10 重放去重策略依据
   400	    cluster_map: dict[tuple, list[int]] = defaultdict(list)
   401	    for line_no, rec in records:
   402	        cluster_map[(rec.get("name", ""), rec.get("episode_body_sha256", ""), rec.get("group_id"))].append(line_no)
   403	    duplicate_clusters = [
   404	        {"name": k[0][:80], "episode_body_sha256": k[1], "group_id": k[2], "line_nos": v, "occurrences": len(v)}
   405	        for k, v in sorted(cluster_map.items(), key=lambda kv: -len(kv[1]))
   406	        if len(v) > 1
   407	    ]
   408	
   409	    qa_probe = (
   410	        probe_qa_metrics(
   411	            Path(args.qa_metrics_db),
   412	            [r.get("error_type", "") for _, r in records],
   413	        )
   414	        if args.qa_metrics_db
   415	        else {"verdict": "skipped_no_db_arg"}
   416	    )
   417	
   418	    deviation = {
   419	        k: {"expected": EXPECTED_CLASS_DIST.get(k, 0), "actual": class_dist.get(k, 0)}
   420	        for k in sorted(set(class_dist) | set(EXPECTED_CLASS_DIST))
   421	        if EXPECTED_CLASS_DIST.get(k, 0) != class_dist.get(k, 0)
   422	    }
   423	
   424	    ledger = {
   425	        "card": "CARD-G4-9",
   426	        "generated_at": datetime.now(timezone.utc).isoformat(),
   427	        "privacy": "private-only: transcript_paths 含本机用户名与 session UUID，禁止外发/公网发布",
   428	        "stable_key_semantics": (
   429	            "冻结快照（dlq_file.sha256）内的 occurrence key；line_no 在快照内唯一，"
   430	            "sha256_prefix/request_id 为冗余对账维度——非跨文件重排或语义幂等键"
   431	        ),
   432	        "dlq_file": dlq_info,
   433	        "compare_copies": [describe_copy(Path(p)) for p in args.compare],
   434	        "total_lines": len(raw_lines),
   435	        "total_records": len(records),
   436	        "unparseable_lines": unparseable,
   437	        # round-2 LOW 整改: 固定 schema 补零，消费者无需自行补齐缺席键
   438	        "class_distribution": {
   439	            k: class_dist.get(k, 0) for k in ["budget_400", "schema_entity_type", "group_id_format", "unexpected"]
   440	        },
   441	        "expected_class_distribution": EXPECTED_CLASS_DIST,
   442	        "class_deviation": deviation,
   443	        "recoverability_distribution": {
   444	            k: recover_dist.get(k, 0) for k in ["byte_exact", "approximate", "unrecoverable"]
   445	        },
   446	        "inline_state_distribution": {
   447	            k: inline_dist.get(k, 0) for k in ["full_verified", "truncated_prefix", "anomaly"]
   448	        },
   449	        "unrecoverable_list": unrecoverable_keys,
   450	        "attribution_conflicts": attribution_conflicts,
   451	        "duplicate_clusters": duplicate_clusters,
   452	        "qa_metrics_probe": qa_probe,
   453	        "records": ledger_records,
   454	    }
   455	
   456	    out_json = json.dumps(ledger, ensure_ascii=False, indent=1)
   457	    if args.out:
   458	        with open(args.out, "w", encoding="utf-8") as f:
   459	            f.write(out_json + "\n")
   460	        print(f"台账已写入: {args.out}")
   461	    else:
   462	        print(out_json)
   463	
   464	    print(
   465	        f"census: {len(records)} 条 (+{len(unparseable)} unparseable) | class={dict(class_dist)} | "
   466	        f"recoverability={dict(recover_dist)} | 归因冲突={len(attribution_conflicts)} | "
   467	        f"重复簇={len(duplicate_clusters)} | 偏差={deviation or '无'} | "
   468	        f"qa_metrics 核销={qa_probe.get('verdict')}",
   469	        file=sys.stderr,
   470	    )
   471	    return 0
   472	
   473	
   474	if __name__ == "__main__":
   475	    sys.exit(main())

**Identifying JSON scalar bug and TOCTOU risk**
**Investigating static alias symlink bypass**
exec
/bin/zsh -lc "rg -n '§3|§5|§6|§7|§7c|full_verified|131|distribution|line_count|hardlink|case-only|anomaly|chmod|symlink|92 条|6/29|6 簇|负例门' '_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
6:> **台账**: `_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json`（92 条逐条，G4-10 消费）
34:92 条，分类与勘探预期**零偏差**：
43:时间分布：3 条 schema/group_id 全部 2026-05-14（P0-4 修复当日之前的失败）；89 条 budget 集中于 2026-08-08 ~ 08-11（8/48/25/8），系 SessionEnd 归档-蒸馏管道对长会话反复触发超限。group_id 分布：`vault:canvas_vault`×89、`vault:default`×3（三条旧格式记录重放时需 group 重映射，见 §6）。
45:## §3 inline 完整性 + SHA 对账
47:`DeadLetterStore.store()` 落盘的 `episode_body` 来自 `EpisodeTask.to_dict()`，后者做 `episode_body[:200]` 截断（`episode_worker.py:107`，"truncate for logging"）；全量正文只有 `DEAD_LETTER_STORE_FULL_BODY` 开启时以 `episode_body_full` 另存——**live 容器该 env 未设置（实测），92 条 `episode_body_full` 均缺席**。逐条重算 sha256(inline) 对账 `episode_body_sha256` 结果：
51:| `full_verified`（内联全量，sha 对账通过） | **4** | 重算值 == 声明值且长度精确匹配（四条正文实为 131/142/150/180 字符，范围 **131–180**，天然未截断；round-2 LOW 修正） |
53:| `anomaly`（对不上账） | **0** | — |
55:4 条 full_verified = 3 条 callout（§2 的 schema/group_id 三条）+ 1 条短 qa_highlight（行 74）。
59:- **qa_metrics.db**（live `backend/data/qa_metrics.db`，经 sqlite URI `mode=ro` 打开）：唯一表 `qa_error_logs`（列 category/error_type/source_module/stack_summary/created_at，**无 request_id 列**），**行数 = 0**。按三个 error_type 探查命中均 0。**核销裁定：`no_source_rows` —— qa_metrics.db 对 92 条死信不构成任何源指针，0/92 可经其溯源。**
62:  - `backend/data/outbox/`：**空目录**（A7 outbox 只接 enqueue 失败，本 92 条全部是 enqueue 成功、处理失败，不经 outbox）；
63:  - `episode_body_full`：0 条（§3）。
66:## §5 可恢复性三态裁定
78:## §6 台账稳定键（G4-10 交接契约）
80:台账逐条携带复合键 `{line_no, sha256_prefix(16 hex), request_id}`。**语义（Codex round-1 LOW-2 修正）**：这是**冻结快照内的 occurrence key**，不是跨文件重排或语义幂等键——台账头部 `dlq_file.sha256`（`3b37460f4215f6ac…`）即快照指纹，`line_no` 在该快照内已单列唯一；`sha256_prefix`（本快照 69 个唯一值，qa_highlight 家族实测同名同 sha 多条）与 `request_id`（仅 25 个唯一值，进程内 contextvars、重启可复用）是**冗余对账/诊断维度**，不是唯一性的必要条件。G4-10 消费前先 diff 头部 sha 即知 DLQ 是否长了新条目；语义级去重不得按本键，须按 `duplicate_clusters` 段（见下）。**语义重复簇（MEDIUM-2 整改）**：按 `{name, episode_body_sha256, group_id}` 聚簇，**6 簇覆盖 29 行**（最大簇 = 同一 session-archive 16 行，`reference_time` 各不相同——同内容反复入队反复超限）。台账 `duplicate_clusters` 段逐簇列 line_nos，records 逐条透传 `reference_time`；G4-10 重放前必须先定去重策略（89 条 budget 修根因后若逐条盲放，将把同内容写入最多 16 遍）。
86:## §7 裁判证据（整改版脚本重跑）
94:| 负例门（round-1 整改自证） | `--out`==`--dlq` → exit 2 拒写、DLQ 完好；transcripts 根缺失 → exit 2 拒诊；sha 匹配但长度不符（round-1 HIGH-1 反例①）→ anomaly/unrecoverable；坏 JSON 行/空行 → unparseable 逐行入台账不拒诊 |
95:| 负例门（round-2 整改自证） | **hardlink** 指向 DLQ 的 --out → exit 2 + DLQ sha 不变；**case-only 别名**（`DLQ.jsonl`）→ exit 2 + DLQ 完好；**anomaly + episode_body_full 组合**（sha 对但长度 999）→ anomaly/unrecoverable（不再翻案 byte_exact）；**chmod 000 根** → exit 2 拒诊；**symlink 逃逸**（根内 .jsonl → 根外 .txt）→ match_count=0/unrecoverable；正例回归：真实唯一命中仍 approximate |
97:## §7b Codex round-1 整改记录（BLOCKED → 全项整改）
99:- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
100:- **BLOCKER-2（快照不原子）**：DLQ 单次 `read_bytes()`，头部 sha256/line_count 与逐条 records 派生自同一份内存字节；mtime 显式标注为 stat 参考值。
102:- **HIGH-1（inline 判定不 fail-closed）**：full_verified 加长度精确匹配门；truncated_prefix 加 64-hex 合法性门；anomaly 一律 unrecoverable + 如实 basis（不再谎称截断、不再滑入 approximate）。
103:- **HIGH-2（request_id fail-open）**：分组键改 `(类型名, 值)`；缺失/None 按 line_no 单条成组零传染；组内多 token 前缀一致门，冲突记 `attribution_conflict` 拒绝采信（现网 92 条 0 冲突）。
106:- **MEDIUM-2**：`duplicate_clusters` 段 + 逐条 `reference_time`（见 §6）。
107:- **MEDIUM-3**：台账头部 privacy 字段 + 本报告 private-only 声明（见 §6）。
110:整改后全量重跑：**92 条数字与整改前逐项一致**（class 89/2/1、三态 4/88/0、归因冲突 0、unparseable 0），重复簇 6/29 行与 Codex 独立复算吻合。另有独立 Workflow 4-agent 复核（92 条重算 0 mismatch、7 transcript 在盘实测、台账 sha 一致）交叉确认。
112:## §7c Codex round-2 复审整改记录（10/13 CLOSED → 剩余 3 项 + 3 新 LOW 全部整改）
116:- **BLOCKER-1 NOT-CLOSED（hardlink / case-only 别名绕过）**：原守卫比较 `resolve()` **字符串**，hardlink 指向输入、以及大小写不敏感文件系统上的 case-only 别名均绕过并截断输入。**整改**：改为比较**文件身份 `(st_dev, st_ino)`**（对已存在的 --out）+ 保留路径比较作第二道。负例实测：两种绕过均 exit 2、DLQ sha 不变。
117:- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
118:- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
119:- **新 LOW ×3**：full_verified 长度范围修正为 131–180；台账 `class_distribution`/`recoverability_distribution` 补零并新增 `inline_state_distribution`（固定 schema，消费者无需补齐缺席键）；`line_count` 改用 `splitlines()` 与 records 同口径（原 `count("\n")` 在 bare CR / U+2028 下会与 records 数不一致）。
121:round-2 整改后再次全量重跑：92 条、class 89/2/1、三态 4/88/0、重复簇 6/29、shasum 不变——**数字仍逐项一致**，整改只收紧通用鲁棒性。

exec
/bin/zsh -lc "nl -ba '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' | sed -n '1,155p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
     1	{
     2	 "card": "CARD-G4-9",
     3	 "generated_at": "2026-08-28T11:11:58.320970+00:00",
     4	 "privacy": "private-only: transcript_paths 含本机用户名与 session UUID，禁止外发/公网发布",
     5	 "stable_key_semantics": "冻结快照（dlq_file.sha256）内的 occurrence key；line_no 在快照内唯一，sha256_prefix/request_id 为冗余对账维度——非跨文件重排或语义幂等键",
     6	 "dlq_file": {
     7	  "path": "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl",
     8	  "exists": true,
     9	  "line_count": 92,
    10	  "sha256": "3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590",
    11	  "mtime_utc": "2026-08-11T14:01:25.808462+00:00",
    12	  "mtime_note": "mtime 为 stat 快照，仅供参考；绑定 exact bytes 的是 sha256"
    13	 },
    14	 "compare_copies": [
    15	  {
    16	   "path": "/Users/Heishing/Desktop/canvas/canvas-learning-system/backend/data/dead_letter_episodes.jsonl",
    17	   "exists": true,
    18	   "line_count": 685,
    19	   "sha256": "490c903b2f3636e1d2c4ecb68465cef41ace06f0bd171eb2fb95c03a7b40cb43",
    20	   "mtime_utc": "2026-04-07T11:47:19.585617+00:00",
    21	   "mtime_note": "mtime 为 stat 快照，仅供参考；绑定 exact bytes 的是 sha256"
    22	  },
    23	  {
    24	   "path": "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/data/dead_letter_episodes.jsonl",
    25	   "exists": true,
    26	   "line_count": 1,
    27	   "sha256": "bfb3f6c413aab7dd4c04a25f7575aaaffcfc92fd4e8e8966362609652ac7e310",
    28	   "mtime_utc": "2026-07-13T04:51:14.925282+00:00",
    29	   "mtime_note": "mtime 为 stat 快照，仅供参考；绑定 exact bytes 的是 sha256"
    30	  },
    31	  {
    32	   "path": "/Users/Heishing/Desktop/canvas/canvas-learning-system/data/dead_letter_episodes.jsonl",
    33	   "exists": true,
    34	   "line_count": 4,
    35	   "sha256": "75c5f7593b9b2e99672d0551487b4476552ebd8d33ad25c5f9479683cc61e9c9",
    36	   "mtime_utc": "2026-04-05T23:30:49.019652+00:00",
    37	   "mtime_note": "mtime 为 stat 快照，仅供参考；绑定 exact bytes 的是 sha256"
    38	  }
    39	 ],
    40	 "total_lines": 92,
    41	 "total_records": 92,
    42	 "unparseable_lines": [],
    43	 "class_distribution": {
    44	  "budget_400": 89,
    45	  "schema_entity_type": 2,
    46	  "group_id_format": 1,
    47	  "unexpected": 0
    48	 },
    49	 "expected_class_distribution": {
    50	  "budget_400": 89,
    51	  "schema_entity_type": 2,
    52	  "group_id_format": 1
    53	 },
    54	 "class_deviation": {},
    55	 "recoverability_distribution": {
    56	  "byte_exact": 4,
    57	  "approximate": 88,
    58	  "unrecoverable": 0
    59	 },
    60	 "inline_state_distribution": {
    61	  "full_verified": 4,
    62	  "truncated_prefix": 88,
    63	  "anomaly": 0
    64	 },
    65	 "unrecoverable_list": [],
    66	 "attribution_conflicts": [],
    67	 "duplicate_clusters": [
    68	  {
    69	   "name": "session-archive:426ffbde-15f6-4b",
    70	   "episode_body_sha256": "c93058c9850c6999310e98df9e6ebc26063b96fa6f0649fb1ec6d9d04c88a7fe",
    71	   "group_id": "vault:canvas_vault",
    72	   "line_nos": [
    73	    11,
    74	    15,
    75	    22,
    76	    26,
    77	    32,
    78	    39,
    79	    43,
    80	    47,
    81	    55,
    82	    63,
    83	    67,
    84	    71,
    85	    80,
    86	    84,
    87	    88,
    88	    92
    89	   ],
    90	   "occurrences": 16
    91	  },
    92	  {
    93	   "name": "qa_highlight:Q: What is the relationship between a co",
    94	   "episode_body_sha256": "f22956e79a5a23be64d05cd806fd78773916c5bc40b10f9cfd7d5fda0814e10e",
    95	   "group_id": "vault:canvas_vault",
    96	   "line_nos": [
    97	    24,
    98	    41,
    99	    78,
   100	    82
   101	   ],
   102	   "occurrences": 4
   103	  },
   104	  {
   105	   "name": "conversation_distillation:Distilled summary for node session:426ff",
   106	   "episode_body_sha256": "f9682670197b1339166db46bc7a6b49cca01d745e100568dfdd88b6aa15c6f51",
   107	   "group_id": "vault:canvas_vault",
   108	   "line_nos": [
   109	    8,
   110	    12,
   111	    68
   112	   ],
   113	   "occurrences": 3
   114	  },
   115	  {
   116	   "name": "qa_highlight:Q: What is the relationship between a co",
   117	   "episode_body_sha256": "7a830d4e3c5d52fe3699e0065c5ab61ae013eca3dcf6dd79cf246e37fc4d8629",
   118	   "group_id": "vault:canvas_vault",
   119	   "line_nos": [
   120	    13,
   121	    45
   122	   ],
   123	   "occurrences": 2
   124	  },
   125	  {
   126	   "name": "conversation_distillation:Distilled summary for node session:426ff",
   127	   "episode_body_sha256": "288e4b506e72402e22c8b08fa9608c8dc9e1870ccdd43ed4ab93c95655435064",
   128	   "group_id": "vault:canvas_vault",
   129	   "line_nos": [
   130	    16,
   131	    64
   132	   ],
   133	   "occurrences": 2
   134	  },
   135	  {
   136	   "name": "qa_highlight:Q: What is the relationship between a co",
   137	   "episode_body_sha256": "04e26b3060192bc9de508b2e75c508fba86553a82bea1e910bc24771c75834b5",
   138	   "group_id": "vault:canvas_vault",
   139	   "line_nos": [
   140	    37,
   141	    86
   142	   ],
   143	   "occurrences": 2
   144	  }
   145	 ],
   146	 "qa_metrics_probe": {
   147	  "db_path": "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db",
   148	  "opened_readonly": true,
   149	  "tables": [
   150	   "qa_error_logs"
   151	  ],
   152	  "qa_error_logs_rows": 0,
   153	  "error_type_hits": {
   154	   "BadRequestError": 0,
   155	   "EntityTypeValidationError": 0,

exec
/bin/zsh -lc "rg -n 'hardlink|case-only|chmod 000|symlink|anomaly.*full|full_body' '_bmad-output/审查/G4-9-evidence' -g '*.txt' -g '*.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:25:266:    # (st_dev, st_ino) 而非 resolve() 字符串 —— 后者对 hardlink 与
_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:30:--- (6) fail-closed 门（不可读根 / symlink 逃逸 / anomaly 前置）:
_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:33:343:        elif state != "anomaly" and full_body_verified(rec):

exec
/bin/zsh -lc "git ls-tree -r --name-only 73102875 | rg 'G4-9|census_dead_letter|dead_letter_episodes'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
"_bmad-output/\345\256\241\346\237\245/G4-9-DLQ-census-2026-08-28.md"
"_bmad-output/\345\256\241\346\237\245/G4-9-dlq-ledger-2026-08-28.json"
"_bmad-output/\345\256\241\346\237\245/G4-9-evidence/census-stderr.txt"
"_bmad-output/\345\256\241\346\237\245/G4-9-evidence/container-sha-check.txt"
"_bmad-output/\345\256\241\346\237\245/G4-9-evidence/grep-selfattest.txt"
"_bmad-output/\345\256\241\346\237\245/G4-9-evidence/shasums-after.txt"
"_bmad-output/\345\256\241\346\237\245/G4-9-evidence/shasums-before.txt"
"_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round2.md"
"_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9.md"
"_bmad-output/\351\252\214\346\224\266\345\215\225/UAT-CARD-G4-9-DLQ\347\234\237\345\256\236\346\214\202\350\275\275census\345\210\206\350\257\212-2026-08-28.md"
backend/scripts/census_dead_letter_episodes.py

**Identifying missing negative test evidence**
exec
/bin/zsh -lc "nl -ba '_bmad-output/审查/codex-review-CARD-G4-9-round2.md' | sed -n '1,260p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
     1	> **存档说明**: codex exec 完成审查后被 cyber 误拦（exit 1，重定向文件空——MEMORY 已录 codex 三坑之一）。本文件由 task stdout 抢救提取，内容为 Codex round-2 原文（自"总裁定"起至结论段止），未作任何改写。
     2	
     3	总裁定：**仍阻断 / 不可验收**。`67ccebe1` 确实冻结了交付物，92 条数字也可独立复算；但实际只有 **10/13 CLOSED**，`BLOCKER-1`、`HIGH-1`、`HIGH-3` 仍未闭合。
     4	
     5	| 项目 | 裁定 | 复核结果 |
     6	|---|---|---|
     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
     8	| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
     9	| BLOCKER-3 | **CLOSED** | `git show 67ccebe1 --stat` 为 10 个 G4-9 文件、3384 insertions，包含脚本、报告、ledger、证据包、round-1 审查和 UAT。当前 HEAD 为 `e7a480eb`，但全部 G4-9 路径相对 `67ccebe1` diff 为空。关键 blob：script `ea370cb…`、report `ff1f71d…`、ledger `6ce5772…`。 |
    10	| HIGH-1 | **NOT-CLOSED** | round-1 三个反例本身均已翻转为 `anomaly/FAIL → unrecoverable`；非法 64 字符非 hex 也被拒。但新增组合反例：`episode_body="abc"`、`episode_body_full="abc"`、SHA 正确、声明长度 `999`，实际得到 `inline_state=anomaly` 后仍被判 `byte_exact`。原因是 [`full_body_verified()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:99)只核 SHA，不核长度，并在 [anomaly 分支之前](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:285)被采信。这直接反驳报告“anomaly 一律 unrecoverable”。 |
    11	| HIGH-2 | **CLOSED** | missing、显式 `null`、字面 `"None"` 不再合组；数字 `123` 与字符串 `"123"` 分离；非前缀多 token 均 `attribution_conflict=true/unrecoverable`；合法前缀组统一取最长 token。真实入口反例全部通过。 |
    12	| HIGH-3 | **NOT-CLOSED** | 不存在根目录已 exit 2；递归唯一命中、多命中冲突、目录伪命中也通过。但“不可见”仍未闭合：存在但 `chmod 000` 的根会 exit 0 并假判 `unrecoverable`。此外 [`glob + os.path.isfile`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:134)跟随 symlink：根内 `.jsonl` symlink 指向根外 `.txt`、以及 symlink 目录逃逸到根外树，均被判唯一来源并进入 `approximate`。 |
    13	| MEDIUM-1 | **CLOSED（原 finding）** | 已读取 `episode_body_full`，不再完全忽略该生产字段；当前 92 条为 0。其长度门问题已计入 HIGH-1。 |
    14	| MEDIUM-2 | **CLOSED** | [报告 §6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:78)、[ledger duplicate_clusters](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:60)及逐条 `reference_time` 已落地；6 簇全部逐行对账。 |
    15	| MEDIUM-3 | **CLOSED（声明性控制）** | ledger [`privacy`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:4)及报告 private-only 声明已落地。它是纪律标签，不是技术性防外发门。 |
    16	| LOW-1 | **CLOSED** | token 已修为 `16948–20831`，截断记录声明长度修为 `205–8036`。 |
    17	| LOW-2 | **CLOSED** | [`stable_key_semantics`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:5)已明确仅为冻结快照内 occurrence key，不再声称三列缺一不可。 |
    18	| LOW-3 | **CLOSED** | 报告同时补齐 `LearningConcept.name` 与 `LearningTip.created_at` 两处修复证据。 |
    19	| LOW-4 | **CLOSED** | [报告 §1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:28)已区分当前实证和未重新复证的历史 mountinfo，不再把历史断言冒充本轮证明。 |
    20	
    21	重跑数字核验：
    22	
    23	- live DLQ SHA 仍为 `3b37460f…ba590`，与冻结 ledger header 相同。
    24	- 92 行 / 92 records / 0 unparseable。
    25	- inline：`4 full_verified / 88 truncated_prefix / 0 anomaly`。
    26	- recoverability：`4 byte_exact / 88 approximate / 0 unrecoverable`。
    27	- class：`89 budget_400 / 2 schema / 1 group_id / 0 unexpected`。
    28	- duplicate：`6` 簇覆盖 `29` 行，额外 occurrence `23`。
    29	- `reference_time`：92/92 与 raw 对账；所核字段 0 mismatch。
    30	
    31	新增低风险问题：
    32	
    33	- **LOW**：报告称 full_verified 长度 `131–200`，实际四条为 `131/150/180/142`，范围应为 `131–180`。
    34	- **LOW**：ledger distribution 省略 `unexpected:0`、`anomaly:0`、`unrecoverable:0`，固定 schema 消费者需自行补零。
    35	- **LOW**：header line_count 仅数 LF，而 records 使用 `splitlines()`；bare CR/U+2028 输入可出现 header `1`、records `2`。不影响当前标准 LF 的 92 条。
    36	
    37	审查期间未修改仓库或真实数据；破坏性反例只作用于自动清理的临时文件。未读取 transcript 内容。当前会话未提供 `graphiti-canvas`，因此无法执行其 memory search；这不影响上述本地 exact-byte、Git 与真实入口裁定。

**Clarifying TOCTOU status in blocker**
**Confirming TOCTOU causes blocker persistence**
**Assessing case-only alias resolution**
**Designing safe file opening and truncation**
**Assessing directory permission checks for root**
exec
/bin/zsh -lc id in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
uid=501(Heishing) gid=20(staff) groups=20(staff),12(everyone),61(localaccounts),79(_appserverusr),80(admin),81(_appserveradm),33(_appstore),98(_lpadmin),100(_lpoperator),204(_developer),250(_analyticsusers),395(com.apple.access_ftp),398(com.apple.access_screensharing),399(com.apple.access_ssh),400(com.apple.access_remote_ae)

**Evaluating nested unreadable subtree impact**
**Analyzing symlink and path resolution risks**
**Identifying TOCTOU risks in path recording**
**Analyzing symlink and hardlink path containment**
**Evaluating mount points and path normalization effects**
**Planning fail-closed error handling for traversal**
**Assessing full_body verification logic**
**Evaluating prefix validation and anomaly detection**
**Confirming class distribution consistency**
**Planning JSON string parsing approach**
**Designing ledger state recomputation without transcript reading**
**Confirming permission for transcript metadata scanning**
**Planning transcript metadata verification**
**Designing read-only transcript metadata script**
**Refining Python one-liner quoting strategy**
**Planning file grouping and traversal**
**Designing detailed aggregation metrics**
codex
静态首轮已确认：长度门与 anomaly 前置确实落在生产判定链上；三个统计口径也已进入实际 ledger 生成路径。接下来我从 live DLQ 的冻结 SHA 直接重算，不调用 census 脚本，也不把 ledger 当 oracle；transcript 只做文件名/类型/边界元数据核验，不读取正文。
exec
/bin/zsh -lc "python3 -B -c '
import collections
import hashlib
import json
import os
import re
import stat

src = \"/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl\"
root = os.path.expanduser(\"~/.claude/projects\")
raw = open(src, \"rb\").read()
text_data = raw.decode(\"utf-8\", errors=\"replace\")
lines = text_data.splitlines()
records = []
bad = []
for n, line in enumerate(lines, 1):
    if not line.strip():
        bad.append((n, \"blank\"))
        continue
    try:
        value = json.loads(line)
    except json.JSONDecodeError:
        bad.append((n, \"json\"))
        continue
    records.append((n, value))

budget_re = re.compile(\"exceed_context_size_error|exceeds the available context size\")
sha_re = re.compile(\""'^[0-9a-f]{64}$")
archive_re = re.compile("''^session-archive:([0-9a-fA-F-]+)")
inline_re = re.compile("(?<![0-9a-zA-Z_-])session:([0-9a-f-]{5,})")

classes = collections.Counter()
inline_states = collections.Counter()
full_lengths = []
full_body_present = 0
for n, rec in records:
    et = rec.get("error_type", "")
    err = rec.get("error", "")
    if et == "EntityTypeValidationError":
        cls = "schema_entity_type"
    elif et == "GroupIdValidationError":
        cls = "group_id_format"
    elif et == "BadRequestError" and budget_re.search(err):
        cls = "budget_400"
    else:
        cls = "unexpected"
    classes[cls] += 1
    body = rec.get("episode_body", "")
    declared_len = rec.get("episode_body_length")
    declared_sha = rec.get("episode_body_sha256", "")
    digest = hashlib.sha256(body.encode("utf-8", errors="replace")).hexdigest()
    if isinstance(declared_sha, str) and sha_re.fullmatch(declared_sha) and digest == declared_sha and len(body) == declared_len:
        state = "full_verified"
        full_lengths.append(len(body))
    elif isinstance(declared_sha, str) and sha_re.fullmatch(declared_sha) and len(body) == 200 and isinstance(declared_len, int) and declared_len > 200:
        state = "truncated_prefix"
    else:
        state = "anomaly"
    inline_states[state] += 1
    if "episode_body_full" in rec:
        full_body_present += 1

groups = collections.defaultdict(list)
for n, rec in records:
    rid = rec.get("request_id")
    key = ("__missing__", n) if rid is None else (type(rid).__name__, json.dumps(rid, ensure_ascii=False, sort_keys=True) if isinstance(rid, (dict, list)) else rid)
    groups[key].append((n, rec))

walk_errors = []
files = []
root_real = os.path.realpath(root)
for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False, onerror=lambda e: walk_errors.append(type(e).__name__)):
    kept = []
    for d in dirnames:
        p = os.path.join(dirpath, d)
        if not os.path.islink(p):
            kept.append(d)
    dirnames[:] = kept
    for fn in filenames:
        if not fn.endswith(".jsonl"):
            continue
        p = os.path.join(dirpath, fn)
        try:
            st = os.lstat(p)
        except OSError as e:
            walk_errors.append(type(e).__name__)
            continue
        if stat.S_ISLNK(st.st_mode) or not stat.S_ISREG(st.st_mode):
            continue
        real = os.path.realpath(p)
        try:
            contained = os.path.commonpath([root_real, real]) == root_real
        except ValueError:
            contained = False
        if contained:
            files.append((fn, p))

attrib = {}
match_hist = collections.Counter()
for key, members in groups.items():
    tokens = []
    for n, rec in members:
        name = rec.get("name", "")
        m = archive_re.match(name)
        if m:
            tokens.append(m.group(1).lower())
        tokens.extend(t.lower() for t in inline_re.findall(name))
    uniq = sorted(set(tokens), key=len)
    conflict = False
    count = 0
    if uniq:
        longest = uniq[-1]
        if any(not longest.startswith(t) for t in uniq[:-1]):
            conflict = True
        else:
            count = sum(1 for fn, p in files if fn.startswith(longest) and fn.endswith(".jsonl"))
            if count > 1:
                conflict = True
    match_hist[count] += 1
    attrib[key] = (conflict, count)

recovery = collections.Counter()
for n, rec in records:
    body = rec.get("episode_body", "")
    declared_len = rec.get("episode_body_length")
    declared_sha = rec.get("episode_body_sha256", "")
    digest = hashlib.sha256(body.encode("utf-8", errors="replace")).hexdigest()
    if isinstance(declared_sha, str) and sha_re.fullmatch(declared_sha) and digest == declared_sha and len(body) == declared_len:
        state = "full_verified"
    elif isinstance(declared_sha, str) and sha_re.fullmatch(declared_sha) and len(body) == 200 and isinstance(declared_len, int) and declared_len > 200:
        state = "truncated_prefix"
    else:
        state = "anomaly"
    rid = rec.get("request_id")
    key = ("__missing__", n) if rid is None else (type(rid).__name__, json.dumps(rid, ensure_ascii=False, sort_keys=True) if isinstance(rid, (dict, list)) else rid)
    conflict, count = attrib[key]
    if state == "full_verified":
        result = "byte_exact"
    elif state == "anomaly":
        result = "unrecoverable"
    elif conflict:
        result = "unrecoverable"
    elif count == 1:
        result = "approximate"
    else:
        result = "unrecoverable"
    recovery[result] += 1

clusters = collections.defaultdict(list)
for n, rec in records:
    clusters[(rec.get("name", ""), rec.get("episode_body_sha256", ""), rec.get("group_id"))].append(n)
dups = [v for v in clusters.values() if len(v) > 1]

result = {
    "raw_sha256": hashlib.sha256(raw).hexdigest(),
    "raw_bytes": len(raw),
    "splitlines_count": len(lines),
    "lf_derived_count": raw.count(b"'"\\n\") + (0 if raw.endswith(b\"\\n\") or not raw else 1),
    \"records\": len(records),
    \"unparseable\": len(bad),
    \"class_distribution\": dict(sorted(classes.items())),
    \"inline_state_distribution\": dict(sorted(inline_states.items())),
    \"full_verified_lengths\": sorted(full_lengths),
    \"full_verified_range\": [min(full_lengths), max(full_lengths)],
    \"episode_body_full_present\": full_body_present,
    \"transcript_metadata\": {
        \"walk_errors\": walk_errors,
        \"request_groups\": len(groups),
        \"match_count_histogram\": dict(sorted(match_hist.items())),
    },
    \"recoverability_distribution\": dict(sorted(recovery.items())),
    \"duplicate_cluster_count\": len(dups),
    \"duplicate_covered_lines\": sum(len(v) for v in dups),
    \"duplicate_extra_occurrences\": sum(len(v) - 1 for v in dups),
    \"duplicate_cluster_sizes\": sorted((len(v) for v in dups), reverse=True),
}
print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
{
  "class_distribution": {
    "budget_400": 89,
    "group_id_format": 1,
    "schema_entity_type": 2
  },
  "duplicate_cluster_count": 6,
  "duplicate_cluster_sizes": [
    16,
    4,
    3,
    2,
    2,
    2
  ],
  "duplicate_covered_lines": 29,
  "duplicate_extra_occurrences": 23,
  "episode_body_full_present": 0,
  "full_verified_lengths": [
    131,
    142,
    150,
    180
  ],
  "full_verified_range": [
    131,
    180
  ],
  "inline_state_distribution": {
    "full_verified": 4,
    "truncated_prefix": 88
  },
  "lf_derived_count": 92,
  "raw_bytes": 99915,
  "raw_sha256": "3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590",
  "records": 92,
  "recoverability_distribution": {
    "approximate": 88,
    "byte_exact": 4
  },
  "splitlines_count": 92,
  "transcript_metadata": {
    "match_count_histogram": {
      "0": 3,
      "1": 22
    },
    "request_groups": 25,
    "walk_errors": []
  },
  "unparseable": 0
}

**Planning ledger verification and comparison**
**Inspecting episode_worker.py production semantics**
exec
/bin/zsh -lc 'git show 73102875''^:backend/scripts/census_dead_letter_episodes.py | nl -ba | sed -n '"'80,155p;220,315p;400,430p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
    80	    if et == "BadRequestError" and _BUDGET_PAT.search(rec.get("error", "")):
    81	        return "budget_400"
    82	    return "unexpected"
    83	
    84	
    85	def inline_state(rec: dict) -> tuple[str, str]:
    86	    """返回 (inline_state, sha_check)，fail-closed（见模块 docstring）。"""
    87	    body = rec.get("episode_body", "")
    88	    declared_len = rec.get("episode_body_length")
    89	    declared_sha = rec.get("episode_body_sha256", "")
    90	    sha_wellformed = isinstance(declared_sha, str) and bool(_SHA256_HEX_PAT.match(declared_sha))
    91	    recomputed = hashlib.sha256(body.encode("utf-8", errors="replace")).hexdigest()
    92	    if sha_wellformed and recomputed == declared_sha and len(body) == declared_len:
    93	        return "full_verified", "pass"
    94	    if sha_wellformed and len(body) == 200 and isinstance(declared_len, int) and declared_len > 200:
    95	        return "truncated_prefix", "prefix_only"
    96	    return "anomaly", "FAIL"
    97	
    98	
    99	def full_body_verified(rec: dict) -> bool:
   100	    """episode_body_full 在盘且 sha 对账通过（生产 opt-in 字段，当前 live 0 条）。"""
   101	    full = rec.get("episode_body_full")
   102	    declared_sha = rec.get("episode_body_sha256", "")
   103	    if not isinstance(full, str) or not _SHA256_HEX_PAT.match(str(declared_sha)):
   104	        return False
   105	    return hashlib.sha256(full.encode("utf-8", errors="replace")).hexdigest() == declared_sha
   106	
   107	
   108	def session_tokens(name: str) -> list[str]:
   109	    tokens = []
   110	    m = _SESSION_ARCHIVE_PAT.match(name)
   111	    if m:
   112	        tokens.append(m.group(1).lower())
   113	    tokens.extend(t.lower() for t in _SESSION_INLINE_PAT.findall(name))
   114	    return tokens
   115	
   116	
   117	def resolve_group_attribution(tokens: list[str], transcripts_dir: Path) -> dict:
   118	    """组级归因，fail-closed: 前缀一致门 + 恰 1 个常规文件命中门。"""
   119	    result = {
   120	        "session_token": None,
   121	        "transcript_paths": [],
   122	        "transcript_exists": False,
   123	        "transcript_match_count": 0,
   124	        "attribution_conflict": False,
   125	    }
   126	    uniq = sorted(set(tokens), key=len)
   127	    if not uniq:
   128	        return result
   129	    longest = uniq[-1]
   130	    if any(not longest.startswith(t) for t in uniq[:-1]):
   131	        result["attribution_conflict"] = True
   132	        return result
   133	    result["session_token"] = longest
   134	    pattern = str(transcripts_dir / "**" / f"{longest}*.jsonl")
   135	    matches = sorted(p for p in glob.glob(pattern, recursive=True) if os.path.isfile(p))
   136	    result["transcript_paths"] = matches
   137	    result["transcript_match_count"] = len(matches)
   138	    if len(matches) == 1:
   139	        result["transcript_exists"] = True
   140	    elif len(matches) > 1:
   141	        result["attribution_conflict"] = True  # ambiguous 多命中，拒绝采信
   142	    return result
   143	
   144	
   145	def probe_qa_metrics(db_path: Path, error_types: list[str]) -> dict:
   146	    """只读核销 qa_metrics.db 能否作为源指针（URI mode=ro，无写路径）。"""
   147	    result: dict = {"db_path": str(db_path), "opened_readonly": False}
   148	    if not db_path.exists():
   149	        result["verdict"] = "db_missing"
   150	        return result
   151	    uri = f"file:{db_path}?mode=ro"
   152	    conn = sqlite3.connect(uri, uri=True)
   153	    try:
   154	        result["opened_readonly"] = True
   155	        tables = [
   220	
   221	    dlq_path = Path(args.dlq)
   222	    if not dlq_path.exists():
   223	        print(f"DLQ 文件不存在: {dlq_path}", file=sys.stderr)
   224	        return 2
   225	
   226	    transcripts_dir = Path(args.transcripts_dir)
   227	    if not transcripts_dir.is_dir():
   228	        print(
   229	            f"transcripts 根目录不存在/不可见: {transcripts_dir} —— 拒绝在源不可见时裁定可恢复性（fail-closed）",
   230	            file=sys.stderr,
   231	        )
   232	        return 2
   233	
   234	    # --out 路径碰撞守卫（写前；resolve 覆盖 symlink 变体）
   235	    if args.out:
   236	        out_resolved = Path(args.out).resolve()
   237	        protected = {dlq_path.resolve()} | {Path(p).resolve() for p in args.compare}
   238	        if args.qa_metrics_db:
   239	            protected.add(Path(args.qa_metrics_db).resolve())
   240	        if out_resolved in protected:
   241	            print(f"--out 与输入文件路径重合，拒绝写出（防截断）: {out_resolved}", file=sys.stderr)
   242	            return 2
   243	
   244	    # BLOCKER-2 整改: 单次读取，records 与头部描述共享同一份 exact bytes
   245	    raw_bytes, dlq_info = snapshot_file(dlq_path)
   246	    raw_lines = raw_bytes.decode("utf-8", errors="replace").splitlines()
   247	
   248	    records: list[tuple[int, dict]] = []
   249	    unparseable: list[dict] = []
   250	    for line_no, line in enumerate(raw_lines, start=1):
   251	        if not line.strip():
   252	            unparseable.append({"line_no": line_no, "reason": "blank_line"})
   253	            continue
   254	        try:
   255	            rec = json.loads(line)
   256	        except json.JSONDecodeError as e:
   257	            unparseable.append({"line_no": line_no, "reason": f"json_error: {e}", "excerpt": line[:80]})
   258	            continue
   259	        records.append((line_no, rec))
   260	
   261	    # request_id 分组: (类型名, 值) 复合键；缺失/None → 按 line_no 单条成组
   262	    groups: dict[tuple, list[tuple[int, dict]]] = defaultdict(list)
   263	    for line_no, rec in records:
   264	        rid = rec.get("request_id")
   265	        key = ("__missing__", line_no) if rid is None else (type(rid).__name__, rid)
   266	        groups[key].append((line_no, rec))
   267	    group_attribution: dict[tuple, dict] = {}
   268	    for key, members in groups.items():
   269	        tokens: list[str] = []
   270	        for _, rec in members:
   271	            tokens.extend(session_tokens(rec.get("name", "")))
   272	        group_attribution[key] = resolve_group_attribution(tokens, transcripts_dir)
   273	
   274	    ledger_records = []
   275	    class_dist: Counter = Counter()
   276	    recover_dist: Counter = Counter()
   277	    unrecoverable_keys = []
   278	    attribution_conflicts = []
   279	    for line_no, rec in records:
   280	        cls = classify(rec)
   281	        state, sha_check = inline_state(rec)
   282	        rid = rec.get("request_id")
   283	        key = ("__missing__", line_no) if rid is None else (type(rid).__name__, rid)
   284	        sess = group_attribution[key]
   285	        if state == "full_verified":
   286	            recover = "byte_exact"
   287	            basis = "inline 正文全量：sha256 重算与声明一致且长度精确匹配"
   288	        elif full_body_verified(rec):
   289	            recover = "byte_exact"
   290	            basis = "episode_body_full 在盘且 sha256 对账通过（DEAD_LETTER_STORE_FULL_BODY 生产 opt-in 字段）"
   291	        elif state == "anomaly":
   292	            recover = "unrecoverable"
   293	            basis = "inline 对不上账（anomaly：sha/长度与声明不符），fail-closed 不采信截断前缀假设，也不采信 transcript 归因"
   294	        elif sess["attribution_conflict"]:
   295	            recover = "unrecoverable"
   296	            basis = "session 归因冲突/多命中（fail-closed 拒绝采信任何 transcript），且 inline 仅截断前缀"
   297	        elif sess["transcript_exists"]:
   298	            recover = "approximate"
   299	            basis = (
   300	                f"inline 为 200 字符前缀（前缀性质依赖 to_dict()[:200] 生产不变量，sha 无法直接证明）；"
   301	                f"经 request_id 组归因到唯一在盘 transcript {sess['session_token']}"
   302	                f"（归因 ≠ 内容已验证——本工具未读 transcript 内容；G4-10 可重蒸馏/重格式化近似重建，非逐字节保证）"
   303	            )
   304	        else:
   305	            recover = "unrecoverable"
   306	            basis = "inline 截断且无在盘上游源"
   307	        class_dist[cls] += 1
   308	        recover_dist[recover] += 1
   309	        stable_key = {
   310	            "line_no": line_no,
   311	            "sha256_prefix": str(rec.get("episode_body_sha256", ""))[:16],
   312	            "request_id": rid,
   313	        }
   314	        if recover == "unrecoverable":
   315	            unrecoverable_keys.append(stable_key)
   400	        f"census: {len(records)} 条 (+{len(unparseable)} unparseable) | class={dict(class_dist)} | "
   401	        f"recoverability={dict(recover_dist)} | 归因冲突={len(attribution_conflicts)} | "
   402	        f"重复簇={len(duplicate_clusters)} | 偏差={deviation or '无'} | "
   403	        f"qa_metrics 核销={qa_probe.get('verdict')}",
   404	        file=sys.stderr,
   405	    )
   406	    return 0
   407	
   408	
   409	if __name__ == "__main__":
   410	    sys.exit(main())

exec
/bin/zsh -lc "rg -n 'episode_body_full|episode_body_length|episode_body_sha256|episode_body\\[:200\\]|DEAD_LETTER_STORE_FULL_BODY' backend -g '*.py'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
exec
/bin/zsh -lc 'git diff --check 73102875''^ 73102875 -- backend/scripts/census_dead_letter_episodes.py '"'_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md' '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead

 succeeded in 0ms:
backend/scripts/census_dead_letter_episodes.py:37:  - episode_body_full 若在盘（DEAD_LETTER_STORE_FULL_BODY 开启时生产可写):
backend/scripts/census_dead_letter_episodes.py:91:    declared_len = rec.get("episode_body_length")
backend/scripts/census_dead_letter_episodes.py:92:    declared_sha = rec.get("episode_body_sha256", "")
backend/scripts/census_dead_letter_episodes.py:103:    """episode_body_full 在盘且 sha **与长度**双门对账通过（生产 opt-in 字段，当前 live 0 条）。
backend/scripts/census_dead_letter_episodes.py:106:    但 episode_body_length=999）仍被判 byte_exact —— 与 inline 侧同门收紧。
backend/scripts/census_dead_letter_episodes.py:108:    full = rec.get("episode_body_full")
backend/scripts/census_dead_letter_episodes.py:109:    declared_sha = rec.get("episode_body_sha256", "")
backend/scripts/census_dead_letter_episodes.py:110:    declared_len = rec.get("episode_body_length")
backend/scripts/census_dead_letter_episodes.py:346:            basis = "episode_body_full 在盘且 sha256+长度双门对账通过（DEAD_LETTER_STORE_FULL_BODY 生产 opt-in 字段）"
backend/scripts/census_dead_letter_episodes.py:368:            "sha256_prefix": str(rec.get("episode_body_sha256", ""))[:16],
backend/scripts/census_dead_letter_episodes.py:386:                "episode_body_length": rec.get("episode_body_length"),
backend/scripts/census_dead_letter_episodes.py:387:                "episode_body_sha256": rec.get("episode_body_sha256"),
backend/scripts/census_dead_letter_episodes.py:402:        cluster_map[(rec.get("name", ""), rec.get("episode_body_sha256", ""), rec.get("group_id"))].append(line_no)
backend/scripts/census_dead_letter_episodes.py:404:        {"name": k[0][:80], "episode_body_sha256": k[1], "group_id": k[2], "line_nos": v, "occurrences": len(v)}
backend/app/services/episode_worker.py:108:            "episode_body": self.episode_body[:200],  # truncate for logging
backend/app/services/episode_worker.py:213:      - Always store ``episode_body_sha256`` (16-byte hex prefix) so replays can
backend/app/services/episode_worker.py:215:      - Only store ``episode_body_full`` when env ``DEAD_LETTER_STORE_FULL_BODY``
backend/app/services/episode_worker.py:231:        flag = (os.environ.get("DEAD_LETTER_STORE_FULL_BODY") or "").strip().lower()
backend/app/services/episode_worker.py:237:        Privacy: episode_body_full is omitted unless DEAD_LETTER_STORE_FULL_BODY=true.
backend/app/services/episode_worker.py:245:            "episode_body_sha256": body_hash,
backend/app/services/episode_worker.py:246:            "episode_body_length": len(task.episode_body),
backend/app/services/episode_worker.py:254:            record["episode_body_full"] = _redact(task.episode_body)

**Inspecting hash and redaction handling**
exec
/bin/zsh -lc "nl -ba backend/app/services/episode_worker.py | sed -n '88,120p;205,265p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
    88	    request_id: str | None = field(default=None)
    89	    #: 批次5' (MEM-FLYWHEEL): episode 源类型 — "json" 时 worker 以
    90	    #: EpisodeType.json 入图 (受控 schema, 减少本地模型从脏文本猜结构的空间);
    91	    #: None 保持既有行为 (graphiti 默认)。
    92	    source: str | None = field(default=None)
    93	
    94	    @property
    95	    def can_retry(self) -> bool:
    96	        return self.retry_count < self.max_retries
    97	
    98	    @property
    99	    def backoff_seconds(self) -> float:
   100	        """Exponential backoff with full jitter. Cap at 60s."""
   101	        base = 2**self.retry_count
   102	        cap = min(base, 60)
   103	        return random.uniform(0, cap)
   104	
   105	    def to_dict(self) -> dict[str, Any]:
   106	        result = {
   107	            "name": self.name,
   108	            "episode_body": self.episode_body[:200],  # truncate for logging
   109	            "group_id": self.group_id,
   110	            "source_description": self.source_description,
   111	            "reference_time": self.reference_time.isoformat(),
   112	            "retry_count": self.retry_count,
   113	            "created_at": self.created_at.isoformat(),
   114	        }
   115	        if self.request_id is not None:
   116	            result["request_id"] = self.request_id
   117	        # Log type names only (type references are not JSON-serializable)
   118	        if self.entity_types:
   119	            result["entity_type_names"] = list(self.entity_types.keys())
   120	        if self.edge_types:
   205	    Previously this stored the full ``episode_body`` plaintext on every failure,
   206	    which means all content the LLM saw — including potentially PII, student
   207	    answers, system prompts containing instructions, and the rare leaked
   208	    credential — was permanently archived in ``data/dead_letter_episodes.jsonl``.
   209	    Combined with the file being committed to git in some failure modes, this
   210	    is a CWE-532 vector.
   211	
   212	    New default behavior:
   213	      - Always store ``episode_body_sha256`` (16-byte hex prefix) so replays can
   214	        verify content matches without revealing it.
   215	      - Only store ``episode_body_full`` when env ``DEAD_LETTER_STORE_FULL_BODY``
   216	        is set to ``true`` / ``1`` / ``yes`` (opt-in for debugging).
   217	      - When stored, the full body is run through ``_redact`` to scrub obvious
   218	        secret patterns (OpenAI/Google/GitHub/Bearer/JWT).
   219	      - Error messages are truncated to 200 chars and redacted.
   220	      - Logger.error no longer interpolates the raw error string — only the
   221	        type name — so accidentally-leaked secrets in exception messages don't
   222	        end up in the structured log stream either.
   223	    """
   224	
   225	    def __init__(self, file_path: str = "data/dead_letter_episodes.jsonl") -> None:
   226	        self._file_path = Path(file_path)
   227	        self._file_path.parent.mkdir(parents=True, exist_ok=True)
   228	
   229	    @staticmethod
   230	    def _store_full_body_enabled() -> bool:
   231	        flag = (os.environ.get("DEAD_LETTER_STORE_FULL_BODY") or "").strip().lower()
   232	        return flag in ("1", "true", "yes", "on")
   233	
   234	    def store(self, task: EpisodeTask, error: Exception, *, request_id: str | None = None) -> None:
   235	        """Append failed task to JSONL file synchronously (tiny payload, acceptable).
   236	
   237	        Privacy: episode_body_full is omitted unless DEAD_LETTER_STORE_FULL_BODY=true.
   238	        """
   239	        # Always: hash + minimal metadata (safe to keep forever)
   240	        body_bytes = task.episode_body.encode("utf-8", errors="replace")
   241	        body_hash = hashlib.sha256(body_bytes).hexdigest()
   242	
   243	        record = {
   244	            **task.to_dict(),
   245	            "episode_body_sha256": body_hash,
   246	            "episode_body_length": len(task.episode_body),
   247	            "error": _redact(str(error))[:200],
   248	            "error_type": type(error).__name__,
   249	            "failed_at": datetime.now(timezone.utc).isoformat(),
   250	        }
   251	
   252	        # Opt-in: full body (still redacted for known secret patterns)
   253	        if self._store_full_body_enabled():
   254	            record["episode_body_full"] = _redact(task.episode_body)
   255	
   256	        if request_id is not None:
   257	            record["request_id"] = request_id
   258	
   259	        with open(self._file_path, "a", encoding="utf-8") as f:
   260	            f.write(json.dumps(record, ensure_ascii=False) + "\n")
   261	
   262	        # audit-2026-04-07/p1-1: scrub error from logger interpolation. Type
   263	        # name only — full message is in the JSONL record (already redacted).
   264	        logger.error(
   265	            f"Dead-lettered episode: name={task.name}, "

exec
/bin/zsh -lc "rg -n 'census_dead_letter_episodes|full_body_verified|inline_state_distribution|duplicate_clusters' backend/tests tests _bmad-output -g '*.py' -g '*.sh' -g '*.md' -g '*.txt'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:4:> **性质**: 纯只读 census。0 写入、0 重放、0 业务代码改动。唯一代码产物 = `backend/scripts/census_dead_letter_episodes.py`。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:80:台账逐条携带复合键 `{line_no, sha256_prefix(16 hex), request_id}`。**语义（Codex round-1 LOW-2 修正）**：这是**冻结快照内的 occurrence key**，不是跨文件重排或语义幂等键——台账头部 `dlq_file.sha256`（`3b37460f4215f6ac…`）即快照指纹，`line_no` 在该快照内已单列唯一；`sha256_prefix`（本快照 69 个唯一值，qa_highlight 家族实测同名同 sha 多条）与 `request_id`（仅 25 个唯一值，进程内 contextvars、重启可复用）是**冗余对账/诊断维度**，不是唯一性的必要条件。G4-10 消费前先 diff 头部 sha 即知 DLQ 是否长了新条目；语义级去重不得按本键，须按 `duplicate_clusters` 段（见下）。**语义重复簇（MEDIUM-2 整改）**：按 `{name, episode_body_sha256, group_id}` 聚簇，**6 簇覆盖 29 行**（最大簇 = 同一 session-archive 16 行，`reference_time` 各不相同——同内容反复入队反复超限）。台账 `duplicate_clusters` 段逐簇列 line_nos，records 逐条透传 `reference_time`；G4-10 重放前必须先定去重策略（89 条 budget 修根因后若逐条盲放，将把同内容写入最多 16 遍）。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:106:- **MEDIUM-2**：`duplicate_clusters` 段 + 逐条 `reference_time`（见 §6）。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:117:- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:119:- **新 LOW ×3**：full_verified 长度范围修正为 131–180；台账 `class_distribution`/`recoverability_distribution` 补零并新增 `inline_state_distribution`（固定 schema，消费者无需补齐缺席键）；`line_count` 改用 `splitlines()` 与 records 同口径（原 `count("\n")` 在 bare CR / U+2028 下会与 records 数不一致）。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:127:python3 backend/scripts/census_dead_letter_episodes.py \
_bmad-output/审查/codex-review-CARD-G4-9-round2.md:7:| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
_bmad-output/审查/codex-review-CARD-G4-9-round2.md:8:| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
_bmad-output/审查/codex-review-CARD-G4-9-round2.md:10:| HIGH-1 | **NOT-CLOSED** | round-1 三个反例本身均已翻转为 `anomaly/FAIL → unrecoverable`；非法 64 字符非 hex 也被拒。但新增组合反例：`episode_body="abc"`、`episode_body_full="abc"`、SHA 正确、声明长度 `999`，实际得到 `inline_state=anomaly` 后仍被判 `byte_exact`。原因是 [`full_body_verified()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:99)只核 SHA，不核长度，并在 [anomaly 分支之前](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:285)被采信。这直接反驳报告“anomaly 一律 unrecoverable”。 |
_bmad-output/审查/codex-review-CARD-G4-9-round2.md:12:| HIGH-3 | **NOT-CLOSED** | 不存在根目录已 exit 2；递归唯一命中、多命中冲突、目录伪命中也通过。但“不可见”仍未闭合：存在但 `chmod 000` 的根会 exit 0 并假判 `unrecoverable`。此外 [`glob + os.path.isfile`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:134)跟随 symlink：根内 `.jsonl` symlink 指向根外 `.txt`、以及 symlink 目录逃逸到根外树，均被判唯一来源并进入 `approximate`。 |
_bmad-output/审查/codex-review-CARD-G4-9-round2.md:14:| MEDIUM-2 | **CLOSED** | [报告 §6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:78)、[ledger duplicate_clusters](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:60)及逐条 `reference_time` 已落地；6 簇全部逐行对账。 |
_bmad-output/审查/codex-review-CARD-G4-16-round3.md:184: backend/scripts/census_dead_letter_episodes.py     | 101 +++++++++++++++++----
_bmad-output/审查/codex-review-CARD-G4-16-round3.md:662:A	backend/scripts/census_dead_letter_episodes.py
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:14:CARD-G4-9 round-3 复审（静态审阅 + 只读复算）。你 round-2 裁定 10/13 CLOSED，三项 NOT-CLOSED：BLOCKER-1（--out 守卫比 resolve 字符串，hardlink 与 case-only 别名绕过截断输入）、HIGH-1（full_body_verified 只核 sha 不核长度且排在 anomaly 分支前，anomaly 记录被判 byte_exact）、HIGH-3（chmod 000 根 exit 0 假判 unrecoverable；glob 跟随 symlink 逃逸出根）；另 3 新 LOW（full_verified 长度范围应 131-180、distribution 省略 0 值键、line_count 数 LF 与 records 的 splitlines 口径不一）。开发方以 commit 73102875 提交整改。请只读复核这 6 项是否闭合：
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:15:脚本 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py 现改为：(a) 碰撞守卫比较文件身份 (st_dev, st_ino) 并保留 resolve 路径比较；(b) full_body_verified 增加 len(full)==declared_len 门，且判定链改为 state != 'anomaly' 前置；(c) transcripts 根增 os.access(R_OK|X_OK) 检查 exit 2，glob 结果排除 os.path.islink 条目并要求 realpath 落在根内；(d) line_count 改用 splitlines()，class/recoverability distribution 补零并新增 inline_state_distribution。
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:181: backend/scripts/census_dead_letter_episodes.py     | 101 +++++++++++++++++----
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:598:/bin/zsh -lc 'wc -l backend/scripts/census_dead_letter_episodes.py' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:600:     475 backend/scripts/census_dead_letter_episodes.py
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:603:/bin/zsh -lc 'git diff --no-ext-diff --unified=80 73102875''^ 73102875 -- backend/scripts/census_dead_letter_episodes.py' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:606:diff --git a/backend/scripts/census_dead_letter_episodes.py b/backend/scripts/census_dead_letter_episodes.py
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:608:--- a/backend/scripts/census_dead_letter_episodes.py
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:609:+++ b/backend/scripts/census_dead_letter_episodes.py
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:662:   - reference_time 逐条透传 + duplicate_clusters 段（同 name+sha+group 的
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:718: def full_body_verified(rec: dict) -> bool:
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:967:-        elif full_body_verified(rec):
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:968:+        elif state != "anomaly" and full_body_verified(rec):
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1029:     duplicate_clusters = [
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1074:+        "inline_state_distribution": {
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1079:         "duplicate_clusters": duplicate_clusters,
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1095:         f"重复簇={len(duplicate_clusters)} | 偏差={deviation or '无'} | "
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1117: > **性质**: 纯只读 census。0 写入、0 重放、0 业务代码改动。唯一代码产物 = `backend/scripts/census_dead_letter_episodes.py`。
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1194: 台账逐条携带复合键 `{line_no, sha256_prefix(16 hex), request_id}`。**语义（Codex round-1 LOW-2 修正）**：这是**冻结快照内的 occurrence key**，不是跨文件重排或语义幂等键——台账头部 `dlq_file.sha256`（`3b37460f4215f6ac…`）即快照指纹，`line_no` 在该快照内已单列唯一；`sha256_prefix`（本快照 69 个唯一值，qa_highlight 家族实测同名同 sha 多条）与 `request_id`（仅 25 个唯一值，进程内 contextvars、重启可复用）是**冗余对账/诊断维度**，不是唯一性的必要条件。G4-10 消费前先 diff 头部 sha 即知 DLQ 是否长了新条目；语义级去重不得按本键，须按 `duplicate_clusters` 段（见下）。**语义重复簇（MEDIUM-2 整改）**：按 `{name, episode_body_sha256, group_id}` 聚簇，**6 簇覆盖 29 行**（最大簇 = 同一 session-archive 16 行，`reference_time` 各不相同——同内容反复入队反复超限）。台账 `duplicate_clusters` 段逐簇列 line_nos，records 逐条透传 `reference_time`；G4-10 重放前必须先定去重策略（89 条 budget 修根因后若逐条盲放，将把同内容写入最多 16 遍）。
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1221: - **MEDIUM-2**：`duplicate_clusters` 段 + 逐条 `reference_time`（见 §6）。
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1232:+- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1234:+- **新 LOW ×3**：full_verified 长度范围修正为 131–180；台账 `class_distribution`/`recoverability_distribution` 补零并新增 `inline_state_distribution`（固定 schema，消费者无需补齐缺席键）；`line_count` 改用 `splitlines()` 与 records 同口径（原 `count("\n")` 在 bare CR / U+2028 下会与 records 数不一致）。
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1242: python3 backend/scripts/census_dead_letter_episodes.py \
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1319:+ "inline_state_distribution": {
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1326:  "duplicate_clusters": [
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1428:/bin/zsh -lc "nl -ba backend/scripts/census_dead_letter_episodes.py | sed -n '1,180p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1475:    46	  - reference_time 逐条透传 + duplicate_clusters 段（同 name+sha+group 的
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1531:   102	def full_body_verified(rec: dict) -> bool:
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1612:/bin/zsh -lc "nl -ba backend/scripts/census_dead_letter_episodes.py | sed -n '181,360p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1776:   343	        elif state != "anomaly" and full_body_verified(rec):
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1796:/bin/zsh -lc "nl -ba backend/scripts/census_dead_letter_episodes.py | sed -n '361,520p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1840:   403	    duplicate_clusters = [
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1883:   446	        "inline_state_distribution": {
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1888:   451	        "duplicate_clusters": duplicate_clusters,
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1904:   467	        f"重复簇={len(duplicate_clusters)} | 偏差={deviation or '无'} | "
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1932:80:台账逐条携带复合键 `{line_no, sha256_prefix(16 hex), request_id}`。**语义（Codex round-1 LOW-2 修正）**：这是**冻结快照内的 occurrence key**，不是跨文件重排或语义幂等键——台账头部 `dlq_file.sha256`（`3b37460f4215f6ac…`）即快照指纹，`line_no` 在该快照内已单列唯一；`sha256_prefix`（本快照 69 个唯一值，qa_highlight 家族实测同名同 sha 多条）与 `request_id`（仅 25 个唯一值，进程内 contextvars、重启可复用）是**冗余对账/诊断维度**，不是唯一性的必要条件。G4-10 消费前先 diff 头部 sha 即知 DLQ 是否长了新条目；语义级去重不得按本键，须按 `duplicate_clusters` 段（见下）。**语义重复簇（MEDIUM-2 整改）**：按 `{name, episode_body_sha256, group_id}` 聚簇，**6 簇覆盖 29 行**（最大簇 = 同一 session-archive 16 行，`reference_time` 各不相同——同内容反复入队反复超限）。台账 `duplicate_clusters` 段逐簇列 line_nos，records 逐条透传 `reference_time`；G4-10 重放前必须先定去重策略（89 条 budget 修根因后若逐条盲放，将把同内容写入最多 16 遍）。
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1941:106:- **MEDIUM-2**：`duplicate_clusters` 段 + 逐条 `reference_time`（见 §6）。
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1946:117:- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1948:119:- **新 LOW ×3**：full_verified 长度范围修正为 131–180；台账 `class_distribution`/`recoverability_distribution` 补零并新增 `inline_state_distribution`（固定 schema，消费者无需补齐缺席键）；`line_count` 改用 `splitlines()` 与 records 同口径（原 `count("\n")` 在 bare CR / U+2028 下会与 records 数不一致）。
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2013:    60	 "inline_state_distribution": {
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2020:    67	 "duplicate_clusters": [
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2115:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:33:343:        elif state != "anomaly" and full_body_verified(rec):
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2131:backend/scripts/census_dead_letter_episodes.py
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2144:     8	| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2146:    10	| HIGH-1 | **NOT-CLOSED** | round-1 三个反例本身均已翻转为 `anomaly/FAIL → unrecoverable`；非法 64 字符非 hex 也被拒。但新增组合反例：`episode_body="abc"`、`episode_body_full="abc"`、SHA 正确、声明长度 `999`，实际得到 `inline_state=anomaly` 后仍被判 `byte_exact`。原因是 [`full_body_verified()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:99)只核 SHA，不核长度，并在 [anomaly 分支之前](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:285)被采信。这直接反驳报告“anomaly 一律 unrecoverable”。 |
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2148:    12	| HIGH-3 | **NOT-CLOSED** | 不存在根目录已 exit 2；递归唯一命中、多命中冲突、目录伪命中也通过。但“不可见”仍未闭合：存在但 `chmod 000` 的根会 exit 0 并假判 `unrecoverable`。此外 [`glob + os.path.isfile`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:134)跟随 symlink：根内 `.jsonl` symlink 指向根外 `.txt`、以及 symlink 目录逃逸到根外树，均被判唯一来源并进入 `approximate`。 |
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2150:    14	| MEDIUM-2 | **CLOSED** | [报告 §6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:78)、[ledger duplicate_clusters](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:60)及逐条 `reference_time` 已落地；6 簇全部逐行对账。 |
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2366:    \"inline_state_distribution\": dict(sorted(inline_states.items())),
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2412:  "inline_state_distribution": {
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2439:/bin/zsh -lc 'git show 73102875''^:backend/scripts/census_dead_letter_episodes.py | nl -ba | sed -n '"'80,155p;220,315p;400,430p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2461:    99	def full_body_verified(rec: dict) -> bool:
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2586:   288	        elif full_body_verified(rec):
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2616:   402	        f"重复簇={len(duplicate_clusters)} | 偏差={deviation or '无'} | "
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2629:/bin/zsh -lc 'git diff --check 73102875''^ 73102875 -- backend/scripts/census_dead_letter_episodes.py '"'_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md' '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2634:backend/scripts/census_dead_letter_episodes.py:37:  - episode_body_full 若在盘（DEAD_LETTER_STORE_FULL_BODY 开启时生产可写):
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2635:backend/scripts/census_dead_letter_episodes.py:91:    declared_len = rec.get("episode_body_length")
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2636:backend/scripts/census_dead_letter_episodes.py:92:    declared_sha = rec.get("episode_body_sha256", "")
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2637:backend/scripts/census_dead_letter_episodes.py:103:    """episode_body_full 在盘且 sha **与长度**双门对账通过（生产 opt-in 字段，当前 live 0 条）。
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2638:backend/scripts/census_dead_letter_episodes.py:106:    但 episode_body_length=999）仍被判 byte_exact —— 与 inline 侧同门收紧。
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2639:backend/scripts/census_dead_letter_episodes.py:108:    full = rec.get("episode_body_full")
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2640:backend/scripts/census_dead_letter_episodes.py:109:    declared_sha = rec.get("episode_body_sha256", "")
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2641:backend/scripts/census_dead_letter_episodes.py:110:    declared_len = rec.get("episode_body_length")
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2642:backend/scripts/census_dead_letter_episodes.py:346:            basis = "episode_body_full 在盘且 sha256+长度双门对账通过（DEAD_LETTER_STORE_FULL_BODY 生产 opt-in 字段）"
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2643:backend/scripts/census_dead_letter_episodes.py:368:            "sha256_prefix": str(rec.get("episode_body_sha256", ""))[:16],
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2644:backend/scripts/census_dead_letter_episodes.py:386:                "episode_body_length": rec.get("episode_body_length"),
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2645:backend/scripts/census_dead_letter_episodes.py:387:                "episode_body_sha256": rec.get("episode_body_sha256"),
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2646:backend/scripts/census_dead_letter_episodes.py:402:        cluster_map[(rec.get("name", ""), rec.get("episode_body_sha256", ""), rec.get("group_id"))].append(line_no)
_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2647:backend/scripts/census_dead_letter_episodes.py:404:        {"name": k[0][:80], "episode_body_sha256": k[1], "group_id": k[2], "line_nos": v, "occurrences": len(v)}
_bmad-output/审查/codex-review-CARD-G4-9.md:15:   [脚本:163](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:163) 接受任意输出路径，[脚本:281](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:281) 以 `"w"` 无条件截断，未做审查目录 allowlist、`samefile`、symlink 或数据目录隔离。
_bmad-output/审查/codex-review-CARD-G4-9.md:23:   records 在[脚本:171](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:171)首次读取；头部 `dlq_file` 到[脚本:268](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:268)才重新读取，而 `describe_copy()` 又分别计算行数、SHA、mtime（[脚本:130](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:130)）。
_bmad-output/审查/codex-review-CARD-G4-9.md:37:   [脚本:72](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:72)存在三个可复现反例：
_bmad-output/审查/codex-review-CARD-G4-9.md:41:   - 真正 `anomaly` 在[脚本:208](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:208)仍会被改判为 `approximate` 或 `unrecoverable`，basis 还会谎称“inline 截断”。
_bmad-output/审查/codex-review-CARD-G4-9.md:47:   [脚本:181](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:181)用 `str(request_id)` 对整份历史文件分组：
_bmad-output/审查/codex-review-CARD-G4-9.md:59:   [脚本:94](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:94)跨所有 project 目录做前缀 glob；一个或多个候选都算存在，不要求唯一、可读普通文件或内容关联。目录不存在、未挂载或无权限时则直接返回空，并在[脚本:217](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:217)裁为永久性的 `unrecoverable`，而诚实状态应是“未核验/当前源不可见”。
_bmad-output/审查/codex-review-CARD-G4-9.md:71:   独立复算 `{name, full_sha, group_id}`：6 个重复组覆盖 29 行，额外 occurrence 23 个；最大组为同一 session archive 16 行，但 `reference_time` 各不相同。ledger 未标识重复簇，也不携带 `reference_time`（[脚本:229](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:229)）。G4-10 不能仅按 SHA 去重，也不应无策略逐条重放。
_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:33:343:        elif state != "anomaly" and full_body_verified(rec):
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:49:- **MEDIUM-1~3**：episode_body_full 采信通路 / duplicate_clusters 6 簇 29 行 + reference_time 透传 / privacy 字段与 private-only 声明。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:61:- **3 新 LOW**：full_verified 长度范围修正 131–180；台账三个 distribution 补零并新增 `inline_state_distribution`；`line_count` 与 records 改用同一 `splitlines()` 口径。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:67:- `backend/scripts/census_dead_letter_episodes.py` — 唯一代码产物（只读 census 脚本，纯 stdlib）

**Excluding untracked session files**
**Analyzing redaction verification logic**
**Testing full body verification cases**
exec
/bin/zsh -lc "python3 -B -c '
import hashlib
import importlib.util
import json
p = \"backend/scripts/census_dead_letter_episodes.py\"
spec = importlib.util.spec_from_file_location(\"g49_census_review\", p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def verdict(rec):
    state, check = m.inline_state(rec)
    if state == \"full_verified\":
        recover = \"byte_exact\"
    elif state "'!= "anomaly" and m.full_body_verified(rec):
        recover = "byte_exact"
    elif state == "anomaly":
        recover = "unrecoverable"
    else:
        recover = "non_exact"
    return {"inline_state": state, "full_body_verified": m.full_body_verified(rec), "recoverability_branch": recover}

abc_sha = hashlib.sha256(b"abc").hexdigest()
full = "z" * 250
full_sha = hashlib.sha256(full.encode()).hexdigest()
cases = {
    "round2_anomaly_len999": {
        "episode_body": "abc",
        "episode_body_full": "abc",
        "episode_body_sha256": abc_sha,
        "episode_body_length": 999,
    },
    "anomaly_with_independently_valid_full": {
        "episode_body": "bad",
        "episode_body_full": "abc",
        "episode_body_sha256": abc_sha,
        "episode_body_length": 3,
    },
    "truncated_with_valid_full": {
        "episode_body": "x" * 200,
        "episode_body_full": full,
        "episode_body_sha256": full_sha,
        "episode_body_length": 250,
    },
    "inline_full": {
        "episode_body": "abc",
        "episode_body_sha256": abc_sha,
        "episode_body_length": 3,
    },
}
print(json.dumps({k: verdict(v) for k, v in cases.items()}, indent=2, sort_keys=True))
'"'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
{
  "anomaly_with_independently_valid_full": {
    "full_body_verified": true,
    "inline_state": "anomaly",
    "recoverability_branch": "unrecoverable"
  },
  "inline_full": {
    "full_body_verified": false,
    "inline_state": "full_verified",
    "recoverability_branch": "byte_exact"
  },
  "round2_anomaly_len999": {
    "full_body_verified": false,
    "inline_state": "anomaly",
    "recoverability_branch": "unrecoverable"
  },
  "truncated_with_valid_full": {
    "full_body_verified": true,
    "inline_state": "truncated_prefix",
    "recoverability_branch": "byte_exact"
  }
}

**Comparing ledger records with custom command**
exec
/bin/zsh -lc "python3 -B -c '
import collections
import hashlib
import json
import re

src = \"/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl\"
ledger_path = \"_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json\"
raw = open(src, \"rb\").read()
rows = [(n, json.loads(line)) for n, line in enumerate(raw.decode(\"utf-8\", errors=\"replace\").splitlines(), 1) if line.strip()]
ledger = json.load(open(ledger_path, encoding=\"utf-8\"))
budget_re = re.compile(\"exceed_context_size_error|exceeds the available context size\")
sha_re = re.compile(\""'^[0-9a-f]{64}$")

def cls(rec):
    et = rec.get("error_type", "")
    if et == "EntityTypeValidationError":
        return "schema_entity_type"
    if et == "GroupIdValidationError":
        return "group_id_format"
    if et == "BadRequestError" and budget_re.search(rec.get("error", "")):
        return "budget_400"
    return "unexpected"

def inline(rec):
    body = rec.get("episode_body", "")
    declared_len = rec.get("episode_body_length")
    declared_sha = rec.get("episode_body_sha256", "")
    digest = hashlib.sha256(body.encode("utf-8", errors="replace")).hexdigest()
    if isinstance(declared_sha, str) and sha_re.fullmatch(declared_sha) and digest == declared_sha and len(body) == declared_len:
        return "full_verified"
    if isinstance(declared_sha, str) and sha_re.fullmatch(declared_sha) and len(body) == 200 and isinstance(declared_len, int) and declared_len > 200:
        return "truncated_prefix"
    return "anomaly"

mismatch = collections.Counter()
if len(rows) != len(ledger["records"]):
    mismatch["record_count"] += 1
for (n, rec), got in zip(rows, ledger["records"]):
    expected = {
        "line_no": n,
        "sha256_prefix": str(rec.get("episode_body_sha256", ""))[:16],
        "request_id": rec.get("request_id"),
        "name": rec.get("name", "")[:80],
        "group_id": rec.get("group_id"),
        "reference_time": rec.get("reference_time"),
        "class": cls(rec),
        "episode_body_length": rec.get("episode_body_length"),
        "episode_body_sha256": rec.get("episode_body_sha256"),
        "inline_state": inline(rec),
    }
    actual = {
        "line_no": got["stable_key"]["line_no"],
        "sha256_prefix": got["stable_key"]["sha256_prefix"],
        "request_id": got["stable_key"]["request_id"],
        "name": got["name"],
        "group_id": got["group_id"],
        "reference_time": got["reference_time"],
        "class": got["class"],
        "episode_body_length": got["episode_body_length"],
        "episode_body_sha256": got["episode_body_sha256"],
        "inline_state": got["inline_state"],
    }
    for k in expected:
        if expected[k] != actual[k]:
            mismatch[k] += 1

cluster_map = collections.defaultdict(list)
for n, rec in rows:
    cluster_map[(rec.get("name", ""), rec.get("episode_body_sha256", ""), rec.get("group_id"))].append(n)
expected_clusters = sorted(
    [(k[0][:80], k[1], k[2], tuple(v), len(v)) for k, v in cluster_map.items() if len(v) > 1],
    key=lambda x: (-x[4], x[0], x[1], str(x[2])),
)
actual_clusters = sorted(
    [(x["name"], x["episode_body_sha256"], x["group_id"], tuple(x["line_nos"]), x["occurrences"]) for x in ledger["duplicate_clusters"]],
    key=lambda x: (-x[4], x[0], x[1], str(x[2])),
)
out = {
    "ledger_header_sha_matches_raw": ledger["dlq_file"]["sha256"] == hashlib.sha256(raw).hexdigest(),
    "ledger_header_line_count_matches_splitlines": ledger["dlq_file"]["line_count"] == len(raw.decode("utf-8", errors="replace").splitlines()),
    "ledger_total_lines": ledger["total_lines"],
    "ledger_total_records": ledger["total_records"],
    "record_field_mismatches": dict(mismatch),
    "duplicate_clusters_exact_match": expected_clusters == actual_clusters,
    "class_zero_keys": {k: ledger["class_distribution"].get(k, "MISSING") for k in ["budget_400", "schema_entity_type", "group_id_format", "unexpected"]},
    "recoverability_zero_keys": {k: ledger["recoverability_distribution"].get(k, "MISSING") for k in ["byte_exact", "approximate", "unrecoverable"]},
    "inline_zero_keys": {k: ledger["inline_state_distribution"].get(k, "MISSING") for k in ["full_verified", "truncated_prefix", "anomaly"]},
}
print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))
'"'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
{
  "class_zero_keys": {
    "budget_400": 89,
    "group_id_format": 1,
    "schema_entity_type": 2,
    "unexpected": 0
  },
  "duplicate_clusters_exact_match": true,
  "inline_zero_keys": {
    "anomaly": 0,
    "full_verified": 4,
    "truncated_prefix": 88
  },
  "ledger_header_line_count_matches_splitlines": true,
  "ledger_header_sha_matches_raw": true,
  "ledger_total_lines": 92,
  "ledger_total_records": 92,
  "record_field_mismatches": {},
  "recoverability_zero_keys": {
    "approximate": 88,
    "byte_exact": 4,
    "unrecoverable": 0
  }
}

**Restricting transcript content access**
**Inspecting report header discrepancies**
exec
/bin/zsh -lc "nl -ba '_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md' | sed -n '1,32p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
     1	# CARD-G4-9 — DLQ 真实挂载 census 分诊报告
     2	
     3	> **批次**: BATCH-2026-08-28-第五批 / CARD-G4-9（4h · wave 1 · 未来铺路）
     4	> **性质**: 纯只读 census。0 写入、0 重放、0 业务代码改动。唯一代码产物 = `backend/scripts/census_dead_letter_episodes.py`。
     5	> **代码基线**: worktree `card/s5-census` @ `37387a86`
     6	> **台账**: `_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json`（92 条逐条，G4-10 消费）
     7	> **证据包**: `_bmad-output/审查/G4-9-evidence/`（shasums before/after、grep 自证、容器内 sha 实测）
     8	> **执行日期**: 2026-08-28
     9	
    10	---
    11	
    12	## §1 挂载真相（live/主仓/孤儿三址 sha 对照 + compose 遮蔽史）
    13	
    14	**live DLQ 的唯一权威地址**是 `feature-obsidian-hybrid-dev` worktree 的 `backend/data/`（双树拓扑：线上容器代码挂载自该 worktree）。容器内实测确认同源：
    15	
    16	```
    17	docker exec canvas-learning-system-backend sha256sum /app/data/dead_letter_episodes.jsonl
    18	→ 3b37460f4215f6ac...ef3ba590（92 行）— 与宿主 live 地址逐字节一致
    19	```
    20	
    21	| 地址 | 路径 | 行数 | sha256 前 16 | mtime | 裁定 |
    22	|---|---|---|---|---|---|
    23	| **live**（权威） | `…/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl` | **92** | `3b37460f4215f6ac` | 2026-08-11 22:01 (+0800) | 容器 `/app/data` 经 `./backend:/app` 挂载即此文件；census 对象 |
    24	| 主仓 | `canvas-learning-system/backend/data/dead_letter_episodes.jsonl` | 685 | `490c903b2f3636e1` | 2026-04-07 | 陈旧副本（部署迁往 worktree 前的历史死信，止于 4 月）；不代表现网 |
    25	| 孤儿① | `…/worktrees/feature-obsidian-hybrid-dev/data/dead_letter_episodes.jsonl` | 1 | `bfb3f6c413aab7dd` | 2026-07-13 | 已删除的 `./data:/app/data` 子挂载目标残留；从未在容器内生效 |
    26	| 孤儿②（附注） | `canvas-learning-system/data/dead_letter_episodes.jsonl` | 4 | `75c5f7593b9b2e99` | 2026-04-06 | 主仓根 `data/` 早期宿主进程 cwd 落点残留 |
    27	
    28	**compose :206-212 遮蔽史**（本 worktree `docker-compose.yml:206-212`，与 live worktree 同文）：`- ./data:/app/data` 是嵌套 bind，被 `./backend:/app` 父挂载遮蔽——`docker inspect` 记录了它，但容器 `/proc/self/mountinfo` 从不出现，**实际生效的一直是 `backend/data/`**。R11-BATCH2（2026-08-17）已删除该行，理由是遮蔽与否取决于挂载顺序、一次 recreate 就可能翻转，届时 92 行死信会被 1 行的孤儿①覆盖不可见。删除后 `/app/data` 恒等于 `backend/data/`。**证据边界（诚实声明）**：本卡独立实证的是**现状**（容器内 sha 与宿主 live 地址同源、当前 compose 无子挂载行）；"历史上子挂载从未在容器内生效"沿引 compose 注释史与 R11-BATCH2（2026-08-17）当时的 mountinfo 实测记录，本卡未重跑历史 `docker inspect` 独立复证。
    29	
    30	**本 worktree（card-s5-census）没有 `backend/data/dead_letter_episodes.jsonl`**——数据文件不入 git，census 一律指向 live 绝对路径运行，未复制任何数据进本 worktree。
    31	
    32	## §2 总量与分类台账（class 分诊）

**Inspecting commit history for baseline verification**
exec
/bin/zsh -lc "git show -s --format='%H%n%P%n%s%n%ci' 37387a86" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
37387a8662e9dd646fad5628841679d777cb7eae
e8e8d034ca9a2e415aaf09dfda1c6bcf026237b4
ci: fix readme-claims conftest isolation with --noconftest [BATCH-2026-08-27-第四批 / CARD-G1-5]
2026-08-28 05:32:14 +0800

exec
/bin/zsh -lc 'git merge-base --is-ancestor 37387a86 73102875' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead

exec
/bin/zsh -lc 'git log --oneline --decorate --max-count=12' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
73102875 (HEAD -> card/s5-census) fix(census): G4-9/G4-16 Codex round-2 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9 / CARD-G4-16]
e7a480eb docs(census): G4-16 doc_type族接线普查 18文件146行+6取值裁定+注释修正 [BATCH-2026-08-28-第五批 / CARD-G4-16]
67ccebe1 docs(census): G4-9 DLQ真实挂载census分诊 92条台账+挂载真相+三态裁定 [BATCH-2026-08-28-第五批 / CARD-G4-9]
37387a86 (origin/worktree-feature-obsidian-hybrid-dev, backup/worktree-feature-obsidian-hybrid-dev, card/s7-dogfood, card/s6-recap, card/s1-scope) ci: fix readme-claims conftest isolation with --noconftest [BATCH-2026-08-27-第四批 / CARD-G1-5]
e8e8d034 chore: merge card/n6-contract [BATCH-2026-08-27-第四批 / CARD-G2-1 + CARD-G4-12]
aa386819 chore: merge card/n5-split [BATCH-2026-08-27-第四批 / CARD-G5-1 + CARD-G5-2]
9c7281d2 chore: merge card/n4-readme [BATCH-2026-08-27-第四批 / CARD-G1-4 + CARD-G1-5]
81364293 (card/n4-readme) feat: README禁夸大机械lint三档+hook+CI门 [BATCH-2026-08-27-第四批 / CARD-G1-5]
69e0cdcf (card/n5-split) feat(g5-2): board-split只读拆分preview引擎+34条裁判+live零修改取证 [BATCH-2026-08-27-第四批 / CARD-G5-2]
809658cc test(g5-1): 触发矩阵四类正负例+校验器+headless三轮负例回归 [BATCH-2026-08-27-第四批 / CARD-G5-1]
b2803aa4 (card/n6-contract) fix(metrics): G4-12 检索回归指标正名 recall→hit+baseline 键迁移+守卫 [BATCH-2026-08-27-第四批 / CARD-G4-12]
fca1bdc4 test(cypher): G2-1 读写契约审计+R1-R5/W1-W5 规则+7692 真库门测试 [BATCH-2026-08-27-第四批 / CARD-G2-1]

**Assessing code baseline provenance ambiguity**
**Clarifying baseline versus artifact commit**
已锁定 HEAD 与变更；live DLQ 的 SHA/92 records/分类/三态/重复簇/长度范围均由独立实现复算并逐字段对账。剩余是高严重度绕过面的交叉核验。
  ✓ 锁定 checkout/commit、范围与 round-3 变更证据
  → 并行审阅六项修复的静态绕过面
  ✓ 从原始 transcripts 独立复算台账指标并核对报告
  • 交叉核验高严重度项并给出逐项与总裁定
**Analyzing path guards statically**
**Mapping path guard race conditions**
**Identifying output path bypass blocker**
**Reviewing round1 transcript protection**
exec
/bin/zsh -lc "nl -ba '_bmad-output/审查/codex-review-CARD-G4-9.md' | sed -n '1,30p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
     1	总体裁定：**BLOCKED / FAIL**。当前 92 行的统计数字可复算且 ledger 一致，但生成器不满足强只读和精确快照绑定，不能直接交给 G4-10。
     2	
     3	审查结论绑定当前字节：
     4	
     5	- script：`87b6f612…0097d`
     6	- report：`1e1ab071…f6d20`
     7	- ledger：`c090ce35…9082`
     8	- raw DLQ：`3b37460f…ba590`
     9	- WT：`card/s5-census @ 37387a86`
    10	
    11	## BLOCKER
    12	
    13	1. **“只读契约”可被 `--out` 直接突破 — FAIL**
    14	
    15	   [脚本:163](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:163) 接受任意输出路径，[脚本:281](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:281) 以 `"w"` 无条件截断，未做审查目录 allowlist、`samefile`、symlink 或数据目录隔离。
    16	
    17	   静态反例：令 `X` 为 live DLQ，传入 `--dlq X --out X`；脚本先读入 X，随后会用 ledger 覆盖 X。`--out` 同样可指向 `qa_metrics.db` 或其他业务数据文件。报告的“0 写入”及 grep PASS（[报告:4](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:4)、[报告:93](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:93)）只能证明一次约定运行没有改业务数据，不能证明代码契约。
    18	
    19	   SQLite 连接本身使用 `mode=ro` 且只执行 SELECT，这一子项 PASS；危险来自输出文件路径。
    20	
    21	2. **ledger records 与头部源 SHA 不是同一快照 — FAIL**
    22	
    23	   records 在[脚本:171](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:171)首次读取；头部 `dlq_file` 到[脚本:268](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:268)才重新读取，而 `describe_copy()` 又分别计算行数、SHA、mtime（[脚本:130](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:130)）。
    24	
    25	   若 live DLQ 在两次读取间追加或改写，可产出“92 条 records + 93 行文件 SHA”，甚至头部自身的行数、SHA、mtime来自三个状态。G4-10 因而不能确信 stable key 绑定的是头部声明的 exact bytes。
    26	
    27	3. **送审对象未冻结且审查期间实际漂移 — FAIL**
    28	
    29	   首次观察到 script `591593af…`、report `f3ecf974…`；审查中分别变为当前 `87b6f612…`、`1e1ab071…`。三件 G4-9 交付物均为 untracked，报告所列 commit 不能标识其内容。
    30	

**Clarifying output file write restrictions**
**Identifying ledger source overwriting blocker**
**Confirming missing transcript path protection**
**Verifying Python version and glob behavior**
**Identifying glob symlink traversal privacy risk**
**Clarifying transcript usage statement**
**Updating transparency on transcript parsing**
exec
/bin/zsh -lc "python3 -B -c '
import glob
import inspect
import json
import os
print(json.dumps({
  \"python\": __import__(\"sys\").version.split()[0],
  \"_iterdir\": inspect.getsource(glob._iterdir),
  \"_rlistdir\": inspect.getsource(glob._rlistdir),
}, indent=2))
'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
{
  "python": "3.14.4",
  "_iterdir": "def _iterdir(dirname, dir_fd, dironly):\n    try:\n        fd = None\n        fsencode = None\n        if dir_fd is not None:\n            if dirname:\n                fd = arg = os.open(dirname, _dir_open_flags, dir_fd=dir_fd)\n            else:\n                arg = dir_fd\n            if isinstance(dirname, bytes):\n                fsencode = os.fsencode\n        elif dirname:\n            arg = dirname\n        elif isinstance(dirname, bytes):\n            arg = bytes(os.curdir, 'ASCII')\n        else:\n            arg = os.curdir\n        try:\n            with os.scandir(arg) as it:\n                for entry in it:\n                    try:\n                        if not dironly or entry.is_dir():\n                            if fsencode is not None:\n                                yield fsencode(entry.name)\n                            else:\n                                yield entry.name\n                    except OSError:\n                        pass\n        finally:\n            if fd is not None:\n                os.close(fd)\n    except OSError:\n        return\n",
  "_rlistdir": "def _rlistdir(dirname, dir_fd, dironly, include_hidden=False):\n    names = _listdir(dirname, dir_fd, dironly)\n    for x in names:\n        if include_hidden or not _ishidden(x):\n            yield x\n            path = _join(dirname, x) if dirname else x\n            for y in _rlistdir(path, dir_fd, dironly,\n                               include_hidden=include_hidden):\n                yield _join(x, y)\n"
}

**Confirming os.DirEntry.is_dir behavior**
exec
/bin/zsh -lc "python3 -B -c 'import os; print(os.DirEntry.is_dir.__doc__)'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
Return True if the entry is a directory; cached per entry.

**Identifying missing default in signature**
exec
/bin/zsh -lc "python3 -B -c 'import inspect, os; print(inspect.signature(os.DirEntry.is_dir))'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
(self, /, *, follow_symlinks=True)

**Assessing file permission handling and visibility**
**Identifying traversal and unreadable file classification issue**
collab: Wait
**Listing active agents**
**Continuing classification agent queries**
mcp: sequential-thinking/sequentialthinking started
mcp: sequential-thinking/sequentialthinking (completed)
**Verifying class and state distribution consistency**
**Planning classification agent review**
collab: Wait
**Assessing JSON scalar crash impact**
**Weighing new medium DoS relevance**
**Verifying transcript file overwrite risk**
**Identifying transcript output blocker**
**Assessing transcript output path checks**
**Verifying glob error handling robustness**
**Assessing Python glob module referencing**
exec
/bin/zsh -lc "python3 -B -c 'import glob; print(glob.__file__)'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
/opt/homebrew/Cellar/python@3.14/3.14.4_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/glob.py

**Planning line number linking**
exec
/bin/zsh -lc "nl -ba /opt/homebrew/Cellar/python@3.14/3.14.4_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/glob.py | sed -n '172,230p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
   172	    if not dirname or _isdir(dirname, dir_fd):
   173	        yield pattern[:0]
   174	    yield from _rlistdir(dirname, dir_fd, dironly,
   175	                         include_hidden=include_hidden)
   176	
   177	# If dironly is false, yields all file names inside a directory.
   178	# If dironly is true, yields only directory names.
   179	def _iterdir(dirname, dir_fd, dironly):
   180	    try:
   181	        fd = None
   182	        fsencode = None
   183	        if dir_fd is not None:
   184	            if dirname:
   185	                fd = arg = os.open(dirname, _dir_open_flags, dir_fd=dir_fd)
   186	            else:
   187	                arg = dir_fd
   188	            if isinstance(dirname, bytes):
   189	                fsencode = os.fsencode
   190	        elif dirname:
   191	            arg = dirname
   192	        elif isinstance(dirname, bytes):
   193	            arg = bytes(os.curdir, 'ASCII')
   194	        else:
   195	            arg = os.curdir
   196	        try:
   197	            with os.scandir(arg) as it:
   198	                for entry in it:
   199	                    try:
   200	                        if not dironly or entry.is_dir():
   201	                            if fsencode is not None:
   202	                                yield fsencode(entry.name)
   203	                            else:
   204	                                yield entry.name
   205	                    except OSError:
   206	                        pass
   207	        finally:
   208	            if fd is not None:
   209	                os.close(fd)
   210	    except OSError:
   211	        return
   212	
   213	def _listdir(dirname, dir_fd, dironly):
   214	    with contextlib.closing(_iterdir(dirname, dir_fd, dironly)) as it:
   215	        return list(it)
   216	
   217	# Recursively yields relative pathnames inside a literal directory.
   218	def _rlistdir(dirname, dir_fd, dironly, include_hidden=False):
   219	    names = _listdir(dirname, dir_fd, dironly)
   220	    for x in names:
   221	        if include_hidden or not _ishidden(x):
   222	            yield x
   223	            path = _join(dirname, x) if dirname else x
   224	            for y in _rlistdir(path, dir_fd, dironly,
   225	                               include_hidden=include_hidden):
   226	                yield _join(x, y)
   227	
   228	
   229	def _lexists(pathname, dir_fd):
   230	    # Same as os.path.lexists(), but with dir_fd

**Inspecting glob.glob usage and return type**
exec
/bin/zsh -lc "nl -ba /opt/homebrew/Cellar/python@3.14/3.14.4_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/glob.py | sed -n '14,52p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
    14	__all__ = ["glob", "iglob", "escape", "translate"]
    15	
    16	def glob(pathname, *, root_dir=None, dir_fd=None, recursive=False,
    17	        include_hidden=False):
    18	    """Return a list of paths matching a `pathname` pattern.
    19	
    20	    The pattern may contain simple shell-style wildcards a la
    21	    fnmatch. Unlike fnmatch, filenames starting with a
    22	    dot are special cases that are not matched by '*' and '?'
    23	    patterns by default.
    24	
    25	    The order of the returned list is undefined. Sort it if you need a
    26	    particular order.
    27	
    28	    If `root_dir` is not None, it should be a path-like object specifying the
    29	    root directory for searching. It has the same effect as changing the
    30	    current directory before calling it (without actually
    31	    changing it). If pathname is relative, the result will contain
    32	    paths relative to `root_dir`.
    33	
    34	    If `dir_fd` is not None, it should be a file descriptor referring to a
    35	    directory, and paths will then be relative to that directory.
    36	
    37	    If `include_hidden` is true, the patterns '*', '?', '**'  will match hidden
    38	    directories.
    39	
    40	    If `recursive` is true, the pattern '**' will match any files and
    41	    zero or more directories and subdirectories.
    42	    """
    43	    return list(iglob(pathname, root_dir=root_dir, dir_fd=dir_fd, recursive=recursive,
    44	                      include_hidden=include_hidden))
    45	
    46	def iglob(pathname, *, root_dir=None, dir_fd=None, recursive=False,
    47	          include_hidden=False):
    48	    """Return an iterator which yields the paths matching a `pathname` pattern.
    49	
    50	    The pattern may contain simple shell-style wildcards a la
    51	    fnmatch. However, unlike fnmatch, filenames starting with a
    52	    dot are special cases that are not matched by '*' and '?'

**Verifying os.path.isfile behavior**
exec
/bin/zsh -lc "python3 -B -c 'import genericpath; print(genericpath.__file__)'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
/opt/homebrew/Cellar/python@3.14/3.14.4_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/genericpath.py

exec
/bin/zsh -lc "rg -n -A12 '"'^def isfile'"' /opt/homebrew/Cellar/python@3.14/3.14.4_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/genericpath.py" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
36:def isfile(path):
37-    """Test whether a path is a regular file"""
38-    try:
39-        st = os.stat(path)
40-    except (OSError, ValueError):
41-        return False
42-    return stat.S_ISREG(st.st_mode)
43-
44-
45-# Is a path a directory?
46-# This follows symbolic links, so both islink() and isdir()
47-# can be true for the same path on systems that support symlinks
48-def isdir(s):

**Reviewing file identity and untracked logs**
**Confirming untracked file status and citation details**
exec
/bin/zsh -lc "nl -ba /Users/Heishing/.codex/memories/skills/canvas-adversarial-audit/SKILL.md | sed -n '14,50p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
    14	
    15	## Inputs / context to gather
    16	
    17	1. Read the task book, `AGENTS.md`, worktree topology, allowed/prohibited paths, and reporting contract.
    18	2. Record checkout SHA, branch, WT/MAIN labels, current `CURRENT_TASK.md`, and requested P1 claims.
    19	3. Identify actual production entrypoints, not merely the tests that claim to cover them.
    20	
    21	## Procedure
    22	
    23	1. Split independent tracks: vault admission/indexing and tests; Graphiti quarantine/retrieval; SnapshotV3/recovery anchors. Keep the audit read-only.
    24	2. For each claim, build an evidence matrix: claim, `file:line`, adversarial input/state, actual entrypoint/path, observed result, severity, PASS/PARTIAL/FAIL, and limitations.
    25	3. Directly exercise real entrypoints with temporary fixtures where permitted. For path admission include symlink, directory symlink, blacklisted filename in an allowed directory, case variant, and nonexistent path. Assert rejected inputs perform zero open/hash/index/write.
    26	4. For quarantine, test ordinary edge search plus node search and exact-reader paths (`search_nodes`, `read_node_tips`, `read_node_errors`, `read_node_edge_reasons`). Use read-only Neo4j queries and `EXPLAIN` where allowed; distinguish observed metadata exposure from unproven fact-body leakage.
    27	5. For SnapshotV3, test same-generation invalid/future version self-healing, extra fields, strict typing, huge finite values that may produce NaN/Infinity, and identity/length collision boundaries.
    28	6. Compare recovery anchors with machine facts: current HEAD, Actions status, test counts, and unresolved findings. Separate targeted-test results from whole CI.
    29	7. Cross-check high-severity findings independently. Write the final matrix before closure language; explicitly retain `UNVERIFIABLE` items and failed counterexample attempts.
    30	
    31	## Efficiency plan
    32	
    33	- Start from task-book source handles and `rg` for real call sites; cache the entrypoint map for all tracks.
    34	- Parallelize independent tracks, then have the primary reviewer re-open only high-severity evidence.
    35	- Stop treating a test as evidence once it only hits source text, a helper, fake client, `__new__`, or monkeypatch; pivot to the real entrypoint.
    36	
    37	## Pitfalls and fixes
    38	
    39	- Green tests but unsafe closure -> tests do not reach production behavior. Add direct entrypoint fixtures and capture full stdout/trace before an assertion.
    40	- `session:` IDs used as provenance -> ID shape alone is not proof. Preserve provenance or report PARTIAL.
    41	- Quarantine count passes -> exact-reader/node-search surfaces may still cross groups. Test those surfaces specifically.
    42	- `CURRENT_TASK.md` says closed but anchors disagree -> rebuild anchors from current HEAD, Actions, and unresolved findings.
    43	
    44	## Verification checklist
    45	
    46	- Every finding has `file:line`, reproduction, severity, result, and claim-conflict explanation.
    47	- Final report labels WT/MAIN and all verification limits; no prohibited files or raw vault were read.
    48	- Production entrypoints, not only helpers, were tested for each security claim.
    49	- CI status is reported as whole-workflow status, not only passing targeted jobs.
    50	- P1 closure is withheld whenever a reproducible bypass or unverified critical surface remains.

**Planning citation rollout IDs**
**Deciding dual thread ID citations**
collab: Wait
**Assessing JSONL line splitting bug**
**Confirming MEDIUM severity and acceptance impact**
**Planning in-memory validation without writes**
**Verifying JSON output for U+2028 with ensure_ascii=False**
exec
/bin/zsh -lc "python3 -B -c '
import json
record = {\"episode_body\": \"left\\u2028right\", \"error_type\": \"X\"}
wire = json.dumps(record, ensure_ascii=False) + \"\\n\"
parts = wire.splitlines()
print(json.dumps({
    \"wire_is_one_lf_frame\": wire.count(\"\\n\") == 1,
    \"whole_frame_json_valid\": json.loads(wire[:-1]) == record,
    \"splitlines_parts\": len(parts),
    \"parts_individually_valid_json\": [bool((lambda p: (json.loads(p), True))(p)[1]) if False else None for p in []],
    \"part_reprs\": [repr(p) for p in parts],
}, ensure_ascii=True, indent=2))
'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
{
  "wire_is_one_lf_frame": true,
  "whole_frame_json_valid": true,
  "splitlines_parts": 2,
  "parts_individually_valid_json": [],
  "part_reprs": [
    "'{\"episode_body\": \"left'",
    "'right\", \"error_type\": \"X\"}'"
  ]
}

**Analyzing JSON string newline handling**
**Classifying line_count fix and evidence gaps**
**Listing confirmed issues with severity**
**Planning ledger report line gathering**
**Verifying git diff status**
codex
复算已完成：live DLQ SHA 仍是 `3b37460f…ba590`，92 条逐记录字段、三类分布、重复簇与整改版 ledger 均 0 mismatch。路径安全轨则发现“直接样例通过”没有形成完整安全不变量：输出仍有检查—打开竞态，glob 仍会在过滤前跟随目录 symlink 越根扫描，并会静默漏掉不可读子树。
**Verifying git baseline and blobs**
exec
/bin/zsh -lc "git ls-tree 73102875 -- backend/scripts/census_dead_letter_episodes.py '_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md' '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
exec
/bin/zsh -lc "git diff --exit-code 73102875 -- backend/scripts/census_dead_letter_episodes.py '_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md' '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead

 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
100644 blob 9c64e8e792908b4ec049b51882839f47be32926e	"_bmad-output/\345\256\241\346\237\245/G4-9-DLQ-census-2026-08-28.md"
100644 blob 95c2881af6c02bce26fa5076bbdd02813596a3ef	"_bmad-output/\345\256\241\346\237\245/G4-9-dlq-ledger-2026-08-28.json"
100644 blob a80b44839c94aaf24963d8571c38ccb9b675e734	backend/scripts/census_dead_letter_episodes.py

exec
/bin/zsh -lc "git hash-object backend/scripts/census_dead_letter_episodes.py '_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md' '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
a80b44839c94aaf24963d8571c38ccb9b675e734
9c64e8e792908b4ec049b51882839f47be32926e
95c2881af6c02bce26fa5076bbdd02813596a3ef

exec
/bin/zsh -lc 'git status --short --branch' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
## card/s5-census
?? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-16-round3.md"
?? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round3.md"

**Assessing commit artifact matches and issue statuses**
**Clarifying artifact validity versus acceptance**
**Considering inclusion of root containment bug**
**Evaluating low-severity report findings**
**Validating anomaly state handling and type checks**
**Identifying splitlines misuse on JSON strings**
**Validating ledger UTF-8 integrity**
**Confirming transcript readability and linking**
mcp: sequential-thinking/sequentialthinking started
mcp: sequential-thinking/sequentialthinking (completed)
mcp: sequential-thinking/sequentialthinking started
mcp: sequential-thinking/sequentialthinking (completed)
**Updating task plan**
六项均已完成静态反例审阅；高严重度结论由主审重新核对 Python 3.14 glob 实现与生产写/判定入口。数据复算 PASS，但两项路径安全仍 NOT-CLOSED。
  ✓ 锁定 checkout/commit、范围与 round-3 变更证据
  ✓ 并行审阅六项修复的静态绕过面
  ✓ 从原始 transcripts 独立复算台账指标并核对报告
  ✓ 交叉核验高严重度项并给出逐项与总裁定
**Outlining final report structure**
**Summarizing code verification and block status**
**Clarifying low-level issue categorization**
**Clarifying ledger artifact verdict and limitations**
**Documenting transcript parsing and unavailable tools**
**Consolidating glob.py citations**
**Analyzing output file TOCTOU and permissions**
**Updating severity label classifications**
**Analyzing JSON parsing edge case**
**Documenting low-impact evidence ambiguities**
**Refining citation ranges to exclude blanks**
**Verifying rollout citations and output safety**
**Confirming output swap and glob traversal behavior**
**Assessing directory traversal and permissions handling**
**Validating ledger transcript metadata and anomaly states**
**Assessing symlink traversal and filtering**
**Confirming read-only analysis and memory limitations**
codex
总裁定：**仍阻断 / 不可验收**。整改提交 `73102875fdd9837f0d60cf2ed6cf4ea7f6f8c2e5` 与当前文件字节一致，台账数字有效；但六项仅 **4 CLOSED / 2 NOT-CLOSED**。

| 项目 | 裁定 | 复审结果 |
|---|---|---|
| BLOCKER-1 | **NOT-CLOSED / PARTIAL** | 稳定状态下，relative、`..`、case-only、既存 symlink/hardlink 组合已由 [resolve+inode 门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:265)挡住。但仍有两条绕过：① `protected_paths` 不含已被归因的 transcript，直接令 `--out=<唯一 transcript>`，脚本会先判其为恢复源，最后在 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:457)将其截断；② round-2 已指出的 TOCTOU 仍在——检查后、最终打开前将安全输出替换成指向 DLQ 的 symlink/hardlink，即可 `O_TRUNC` 输入。 |
| HIGH-1 | **CLOSED / PASS** | [`full_body_verified()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:102)现有 SHA+严格长度门；[真实判定链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:340)在 full-body 分支前要求 `state != anomaly`。更强反例——full 本身 SHA/长度完全有效，但 inline 不符——仍落 `anomaly → unrecoverable`。无其它调用入口。 |
| HIGH-3 | **NOT-CLOSED / PARTIAL** | 当前用户下根 `chmod 000` 会 exit 2，terminal symlink 和最终落根外的结果也被过滤。但 [`glob.glob(..., recursive=True)`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:144)在 realpath 过滤前已经递归遍历；当前 Python 3.14 的 [`glob.py`](/opt/homebrew/Cellar/python@3.14/3.14.4_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/glob.py:179)会跟随目录 symlink，并静默吞掉不可读子树错误。因此仍可越根枚举；不可读子树会造成“假唯一/假不可恢复”。此外 mode `000` 的唯一 regular transcript 仍能通过 `isfile()`，被判 `approximate`，尽管实际上不可读取。 |
| LOW：长度范围 | **CLOSED** | 报告已改为四值 `131/142/150/180`、范围 `131–180`，[报告 §3](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:45)。 |
| LOW：distribution 零键 | **CLOSED** | [固定 schema 生成链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:437)与 [ledger](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:43)均包含 `unexpected/anomaly/unrecoverable: 0`，并新增 inline 三态。 |
| LOW：line_count 口径 | **CLOSED（原问题）** | header 与 records 都由同一 exact bytes、同一 `decode(...).splitlines()` 派生，[代码](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:195)不再互相矛盾；但引入了下述新 MEDIUM。 |

独立复算结果：

- raw DLQ：99,915 bytes，SHA-256 `3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590`。
- `92` 行 / `92` records / `0` unparseable。
- class：`budget_400 89 / schema_entity_type 2 / group_id_format 1 / unexpected 0`。
- inline：`full_verified 4 / truncated_prefix 88 / anomaly 0`。
- recoverability：`byte_exact 4 / approximate 88 / unrecoverable 0`。
- 重复：`6` 簇覆盖 `29` 行，簇尺寸 `16,4,3,2,2,2`。
- full_verified 长度：`131,142,150,180`。
- 原始记录与 ledger 的 class、inline、recoverability、稳定键、归因、重复簇逐字段 **0 mismatch**；[ledger header](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:6)绑定同一 raw SHA。

新发现：

- **MEDIUM — JSONL framing**：生产端 [`ensure_ascii=False`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/app/services/episode_worker.py:259)可原样输出字符串内的 U+2028；`splitlines()` 会把一个合法的单 LF JSONL record 拆成两条坏行。当前 92 条不受影响，但通用 census 会漏记录。正确口径应按 LF 分帧，而不是 Unicode `splitlines()`。
- **LOW — 输入 schema**：合法 JSON `null`/数组解析成功后会在 `rec.get()` 处异常退出，未被纳入 unparseable。
- **LOW — provenance/evidence**：[报告头](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:5)仍只写起始基线 `37387a86`，未明确区分整改 artifact `73102875`；§7 的 HIGH-1 负例也只隔离验证了长度门，没有单独验证 anomaly 顺序门，尽管代码经更强反例确认正确。

所以：**冻结的 92 条 ledger 数值可采信；CARD-G4-9 生成器与整卡验收仍被 BLOCKER-1、HIGH-3 阻断。** 本轮未修改仓库或受审数据，未执行破坏性 fixture/G4-10 重放；Graphiti 工具本轮不可用。


tokens used
179,222
总裁定：**仍阻断 / 不可验收**。整改提交 `73102875fdd9837f0d60cf2ed6cf4ea7f6f8c2e5` 与当前文件字节一致，台账数字有效；但六项仅 **4 CLOSED / 2 NOT-CLOSED**。

| 项目 | 裁定 | 复审结果 |
|---|---|---|
| BLOCKER-1 | **NOT-CLOSED / PARTIAL** | 稳定状态下，relative、`..`、case-only、既存 symlink/hardlink 组合已由 [resolve+inode 门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:265)挡住。但仍有两条绕过：① `protected_paths` 不含已被归因的 transcript，直接令 `--out=<唯一 transcript>`，脚本会先判其为恢复源，最后在 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:457)将其截断；② round-2 已指出的 TOCTOU 仍在——检查后、最终打开前将安全输出替换成指向 DLQ 的 symlink/hardlink，即可 `O_TRUNC` 输入。 |
| HIGH-1 | **CLOSED / PASS** | [`full_body_verified()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:102)现有 SHA+严格长度门；[真实判定链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:340)在 full-body 分支前要求 `state != anomaly`。更强反例——full 本身 SHA/长度完全有效，但 inline 不符——仍落 `anomaly → unrecoverable`。无其它调用入口。 |
| HIGH-3 | **NOT-CLOSED / PARTIAL** | 当前用户下根 `chmod 000` 会 exit 2，terminal symlink 和最终落根外的结果也被过滤。但 [`glob.glob(..., recursive=True)`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:144)在 realpath 过滤前已经递归遍历；当前 Python 3.14 的 [`glob.py`](/opt/homebrew/Cellar/python@3.14/3.14.4_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/glob.py:179)会跟随目录 symlink，并静默吞掉不可读子树错误。因此仍可越根枚举；不可读子树会造成“假唯一/假不可恢复”。此外 mode `000` 的唯一 regular transcript 仍能通过 `isfile()`，被判 `approximate`，尽管实际上不可读取。 |
| LOW：长度范围 | **CLOSED** | 报告已改为四值 `131/142/150/180`、范围 `131–180`，[报告 §3](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:45)。 |
| LOW：distribution 零键 | **CLOSED** | [固定 schema 生成链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:437)与 [ledger](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:43)均包含 `unexpected/anomaly/unrecoverable: 0`，并新增 inline 三态。 |
| LOW：line_count 口径 | **CLOSED（原问题）** | header 与 records 都由同一 exact bytes、同一 `decode(...).splitlines()` 派生，[代码](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:195)不再互相矛盾；但引入了下述新 MEDIUM。 |

独立复算结果：

- raw DLQ：99,915 bytes，SHA-256 `3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590`。
- `92` 行 / `92` records / `0` unparseable。
- class：`budget_400 89 / schema_entity_type 2 / group_id_format 1 / unexpected 0`。
- inline：`full_verified 4 / truncated_prefix 88 / anomaly 0`。
- recoverability：`byte_exact 4 / approximate 88 / unrecoverable 0`。
- 重复：`6` 簇覆盖 `29` 行，簇尺寸 `16,4,3,2,2,2`。
- full_verified 长度：`131,142,150,180`。
- 原始记录与 ledger 的 class、inline、recoverability、稳定键、归因、重复簇逐字段 **0 mismatch**；[ledger header](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:6)绑定同一 raw SHA。

新发现：

- **MEDIUM — JSONL framing**：生产端 [`ensure_ascii=False`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/app/services/episode_worker.py:259)可原样输出字符串内的 U+2028；`splitlines()` 会把一个合法的单 LF JSONL record 拆成两条坏行。当前 92 条不受影响，但通用 census 会漏记录。正确口径应按 LF 分帧，而不是 Unicode `splitlines()`。
- **LOW — 输入 schema**：合法 JSON `null`/数组解析成功后会在 `rec.get()` 处异常退出，未被纳入 unparseable。
- **LOW — provenance/evidence**：[报告头](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:5)仍只写起始基线 `37387a86`，未明确区分整改 artifact `73102875`；§7 的 HIGH-1 负例也只隔离验证了长度门，没有单独验证 anomaly 顺序门，尽管代码经更强反例确认正确。

所以：**冻结的 92 条 ledger 数值可采信；CARD-G4-9 生成器与整卡验收仍被 BLOCKER-1、HIGH-3 阻断。** 本轮未修改仓库或受审数据，未执行破坏性 fixture/G4-10 重放；Graphiti 工具本轮不可用。


