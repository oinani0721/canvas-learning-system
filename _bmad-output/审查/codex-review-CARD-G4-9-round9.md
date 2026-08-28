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
session id: 01a04897-0af5-7313-b083-690b8d7b7374
--------
user
CARD-G4-9 round-9 复审（静态审阅 + 只读复算，禁改任何文件）。你 round-8 裁定「可验收：92 条冻结 ledger snapshot；不可验收：生成器一般安全性与 UAT 的纯只读声明」，列出 3 BLOCKER + 1 HIGH + 1 MEDIUM。开发方以 commit af251e4a 提交整改：
1. BLOCKER SQLite URI 未转义(#/?) + BLOCKER QA DB 按 pathname 打开可 ABA → 共同解法：probe_qa_metrics 不再让 SQLite 碰路径，改为从已验证 fd（O_RDONLY|O_NOFOLLOW|O_NONBLOCK + fstat + S_ISREG）读全量字节 → sqlite3.connect(':memory:') + conn.deserialize(db_bytes)。ledger 记 read_mode=in_memory_deserialize_from_verified_fd 与 bytes_read_from_verified_fd。
2. BLOCKER 根内末级 symlink（POSIX rename 不解析末级 symlink，realpath 判根外但 replace 替换根内目录项）→ containment 增父目录语义：dirname(abspath(--out)) 若 _path_is_within transcripts 根即拒，叠加原末级判定。
3. HIGH 扫描受阻拒绝不完整（no_token/token_conflict 早退前未记 scan_errors；条件带 and args.out 使 stdout 模式漏网）→ 早退分支同记 scan_errors/stat_failures；拒绝条件去掉 and args.out。
4. MEDIUM tmp 残留 + 未 fsync 父目录 → os.replace 纳入 try，异常一律 unlink tmp；成功后 open 父目录 fsync。
请逐项复核是否闭合，并针对新实现设计反例：conn.deserialize 的内存/大小上限与异常路径、O_NONBLOCK 对普通文件读的语义、父目录 fsync 的 fd 是否可能被换、_path_is_within 对 dirname('.')/相对路径/挂载点/循环 symlink 的边界、tmp 文件名可预测性在 O_EXCL 下的残余风险、以及并发两个进程同 pid 场景。同时复核台账仍为 92 条 / class 89-2-1 / byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0 / 重复簇 6/29 / unparseable 0 / attribution_conflict 3(no_token) / qa read_mode 正确。逐项 CLOSED/NOT-CLOSED + 总裁定 + 新发现分级。若认为生成器安全声明已可验收请明确说明；若仍不可，请给出**你认为达到可验收所必需的最小剩余项清单**（区分必需与建议）。
**Planning detailed read-only audit**
**Reviewing memory for audit skill**
codex
我会按 round-8 的证据标准做一次独立、只读复核：先恢复前轮判据与审计流程，再把代码安全性、异常/并发反例、冻结台账 exact-byte 复算拆成并行轨道。全程不修改文件，也不把开发方自报或测试绿灯当成闭合证据。由于这是典型的 Canvas 对抗复审，我会采用既有的 `canvas-adversarial-audit` 审计规程。
**Starting memory registry search**
exec
/bin/zsh -lc "rg -n -C 3 'CARD-G4-9|round-8|P1 adversarial|canvas-adversarial-audit|ledger snapshot|92 条' /Users/Heishing/.codex/memories/MEMORY.md" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
183-
184-## Reusable knowledge
185-
186:- Related skill: skills/canvas-adversarial-audit/SKILL.md. P1-05/P1-01/P1-08 remained STILL-OPEN; F-02 tombstone filtering and F-05 live resilience were closed. Rejected vault inputs must show zero open/hash/index/write. [Task 1][Task 2]
187-- Reproduced: `vault/raw/escape.md -> /outside/secret.md` was counted by `backfill_vault(..., execute=False)`; case-sensitive `fnmatch` admitted `.CLAUDE/SKILL.md` and `raw/claude.md`. Edge filtering alone was insufficient because exact readers/node search could cross Graphiti groups. [Task 2]
188-- SnapshotV3 needs invalid/future same-generation self-healing, extra-field, strict-type, huge finite mastery, and identity/length collision coverage. [Task 1][Task 2]
189-

exec
/bin/zsh -lc "wc -l /Users/Heishing/.codex/memories/skills/canvas-adversarial-audit/SKILL.md && sed -n '1,260p' /Users/Heishing/.codex/memories/skills/canvas-adversarial-audit/SKILL.md" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
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

**Expanding registry search scope**
exec
/bin/zsh -lc "rg -n -i -C 4 'card.g4.9|g4-9|census|freeze|ledger|attribution_conflict|byte_exact|read_mode|probe_qa_metrics' /Users/Heishing/.codex/memories/MEMORY.md" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
43-- `/goal`, chat approval, or an ordinary agent message is not a control plane. Bootstrap-Prep is not Setup/Run authorization; first present exact challenge, action policy, and root-ABSENT evidence for narrow user approval. [Task 2]
44-- Before activation, verify every model turn/subprocess is terminal and has no writable FD, directory FD, mmap, or inherited handle to activation/claim/lock paths. [Task 2]
45-
46-# Task Group: Canvas Learning System GOV01-A4 gated repair and Recovery-4 lab packaging
47:scope: Exact A4 repository-repair gate and separate isolated Recovery-4 packaging lab. Both outcomes are blocked/partial; lab PASS is not production or freeze approval.
48-applies_to: cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev; reuse_rule=recheck exact base, design handoff, dirty worktree, external receipts, and authority; do not use the lab as a publisher retry or production mutation path.
49-
50-## Task 1: A4 governance repair, safely blocked
51-
52-### rollout_summary_files
53-
54:- rollout_summaries/2026-08-23T07-46-17-9G79-gov01_a4_blocked_recovery4_lab_freeze_review_fail.md (cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev, rollout_path=/Users/Heishing/.codex/sessions/2026/08/23/rollout-2026-08-23T15-46-17-01a02d95-a6b8-7cf3-b775-6b8afa4464db.jsonl, updated_at=2026-08-24T12:24:52+00:00, thread_id=01a02d95-a6b8-7cf3-b775-6b8afa4464db, outcome=partial; no edit/candidate/review)
55-
56-### keywords
57-
58-- GOV01, A4, design-claude.json, A4_DESIGN_DIVERGENCE, WAITING_FOR_A4_DESIGN_HANDOFF, d3167d0655fed91a9b96547c50f6adffb07a0bfe, git ls-files, canvas-vault
59-
60:## Task 2: Recovery-4 isolated lab package, local suite PASS / freeze review FAIL
61-
62-### rollout_summary_files
63-
64:- rollout_summaries/2026-08-23T07-46-17-9G79-gov01_a4_blocked_recovery4_lab_freeze_review_fail.md (cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev, rollout_path=/Users/Heishing/.codex/sessions/2026/08/23/rollout-2026-08-23T15-46-17-01a02d95-a6b8-7cf3-b775-6b8afa4464db.jsonl, updated_at=2026-08-24T12:24:52+00:00, thread_id=01a02d95-a6b8-7cf3-b775-6b8afa4464db, outcome=partial; isolated lab only)
65-
66-### keywords
67-
68:- Recovery-4, no-write sandbox, RENAME_EXCL, freeze readiness, freeze_package.py, ordinal-9595, -I -S -B, fsync, reopen, production_mutation_count
69-
70-## User preferences
71-
72-- The user required “编辑前等待并验证 design-claude.json…否则输出 A4_DESIGN_DIVERGENCE 并停止” -> remain read-only until the exact handoff exists and matches base/verdict/recommendation. [Task 1]
--
80-- Same-filesystem drill preserved source/forensic-destination inode identity; ctime changed and is not a gate. Execution boundary was direct CLT Python `-I -S -B`, isolated env, no real publisher `main()`, no production mutation/retry. [Task 2]
81-
82-## Failures and how to do differently
83-
84:- Missing handoff is a hard wait condition, not implied approval. `ps` was sandbox-denied (`operation not permitted`); mark the census unavailable rather than successful. [Task 1]
85:- Freeze reviewer rejected the lab: missing reproducible full ordinal-9595 input, stdlib origin-byte hashes, exact freeze execution contract/argv/env/cwd enforcement, post-chmod mode proof, and final fsync/reopen/short-write proof. Do not run `freeze_package.py` until a new stable package independently addresses them. [Task 2]
86-- Do not embed private transcript/session paths in public/minimal package artifacts. [Task 2]
87-
88-# Task Group: Canvas Learning System GOV01 exact-object and CACHE-PREP atomicity audit
89-scope: Isolated, read-only verification of GOV01 bundle chains and static exact-object audit of CACHE-PREP-V1 ADOPT/live-cache atomicity.
--
136-- rollout_summaries/2026-08-23T07-48-49-AAp8-phase0a_ready_queue_readonly_governance_audit.md (cwd=/private/tmp/cls-gov01-a4-v1/planning-ro, rollout_path=/Users/Heishing/.codex/sessions/2026/08/23/rollout-2026-08-23T15-48-49-01a02d97-f8f2-74c2-ba02-41c9534f2366.jsonl, updated_at=2026-08-23T08:08:15+00:00, thread_id=01a02d97-f8f2-74c2-ba02-41c9534f2366, outcome=success; handoff only)
137-
138-### keywords
139-
140:- GOV-01-VERIFIED, Phase-0A, A01, A02, A03, annotation-truth-ledger-v2, AtomicAnnotation, boundary receipt, scanner, [HANDOFF:CODEX-PHASE0A-READY]
141-
142-## User preferences
143-
144:- “只读” means no repo/index/ref/worktree/OpenSpec writes, scanner/final census, A01/A02 instantiation, private/Vault/network/Graphiti access, or product implementation. Provide ready/blocked status, exact evidence, batch order, and Claude/Codex matrix. [Task 1]
145-
146-## Reusable knowledge
147-
148:- Order: `GOV-01-VERIFIED clean candidate → OpenSpec → schema/checker → A01 boundary receipt → no-cap census/A01 snapshot → A02 seed/replay → ChatGPT blind review → Codex reconciliation → user dispute/waiver → joint A01/A02 completion → A03 candidate → user exact-byte lock`. A01 cannot complete independently of A02. [Task 1]
149-- Boundary receipt binds SHA/tree, parent/cutoff, roots/planes, parser/normalizer/scanner/exclusion hashes, scope and user-approval commitments, and output allowlist. Truth atoms are versioned `AtomicAnnotation`, not marker counts. [Task 1]
150-
151-## Failures and how to do differently
152-
153:- Expired `pending-user-confirmation` receipt/envelope is not authority. New exact envelope/digest/challenge is needed. The existing `scripts/bmad/scan_feedback.py` did not cover actual output; freeze a new scanner contract/no-write boundary before census. [Task 1]
154-
155-# Task Group: Canvas Learning System P1-05/P1-01/P1-08 adversarial security review
156-scope: Read-only, parallel audit of vault admission/indexing, Graphiti quarantine isolation, SnapshotV3, and recovery-anchor closure claims.
157-applies_to: cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output; reuse_rule=revalidate SHA, CI, actual call sites, and live Neo4j state in the target checkout.

**Clarifying memory citation guidelines**
**Planning metadata search for Graphiti**
**Confirming Graphiti tool unavailability**
**Assessing Graphiti resource availability**
**Preparing sequential thinking tool call**
mcp: sequential-thinking/sequentialthinking started
mcp: sequential-thinking/sequentialthinking (completed)
  → 锁定 checkout、commit af251e4a、round-8→round-9 diff 与生产入口
  • 复核 verified-fd→deserialize、扫描拒绝及异常/资源上限反例
  • 复核 containment、原子发布、tmp 清理、父目录 fsync 与并发反例
  • 从冻结 artifact/exact bytes 独立复算 92 条台账与全部分布
  • 交叉核验高严重度结论，输出 CLOSED/NOT-CLOSED、总裁定和最小剩余项
**Spawning three parallel agents**
**Gathering git state and searching AGENTS.md**
codex
并行审计已启动：一轨专查 SQLite/扫描 fail-closed，一轨专查路径与发布原子性，一轨从现有冻结字节独立复算 ledger。我这边先锁定提交与真实生产入口，并会对所有高严重度结论再亲自复核。当前会话未暴露 `graphiti-canvas.search_memory_facts`，所以该项只能明确记为工具不可用，不能伪称已搜索。
exec
/bin/zsh -lc '"rg" "--files" "-g" "AGENTS.md" "-g" "CLAUDE.md" "-g" "CURRENT_TASK.md" "-g" "*ledger*" "-g" "*census*" "-g" "*g4*" "-g" "*G4*"' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
CURRENT_TASK.md
_decisions/CURRENT_TASK.md
canvas-vault/CLAUDE.md
_bmad-output/审查/G4-12-migration-reconciliation-2026-08-27.txt
_bmad-output/审查/codex-review-CARD-G4-16-round4.md
_bmad-output/审查/2026-08-19-P1-05b-Graphiti污染盘点census报告.md
_bmad-output/审查/codex-review-CARD-G4-12-round2.md
_bmad-output/审查/codex-review-CARD-G4-9-round4.md
_bmad-output/审查/codex-review-CARD-G4-9-round5.md
_bmad-output/审查/G4-9-evidence/census-stderr.txt
_bmad-output/审查/codex-review-CARD-G4-9-round6.md
_bmad-output/审查/codex-review-CARD-G4-9-round2.md
_bmad-output/审查/phase0a-annotation-truth/A02-public-ledger-v2.schema.json
_bmad-output/审查/codex-review-CARD-G4-9-round3.md
_bmad-output/审查/codex-review-CARD-G4-9.md
_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md
_bmad-output/审查/codex-review-CARD-G4-9-round7.md
_bmad-output/审查/codex-review-CARD-G4-12.md
_bmad-output/审查/codex-review-CARD-G4-9-round8.md
_bmad-output/审查/codex-review-CARD-G4-16-round3.md
_bmad-output/审查/codex-review-CARD-G4-16.md
CLAUDE.md
_bmad-output/审查/r11-evidence-2026-08-17/d2-dead-letter-census.md
_bmad-output/审查/G4-16-doc-type-census-2026-08-28.md
_bmad-output/审查/codex-review-CARD-G4-9-round9.md
_bmad-output/审查/codex-review-CARD-G4-16-round2.md
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md
_bmad-output/验收单/UAT-CARD-G4-12-检索指标名实修正-2026-08-27.md
_bmad-output/验收单/UAT-CARD-G4-16-doc_type族接线普查-2026-08-28.md
backend/scripts/census_graphiti_pollution.py
backend/scripts/census_dead_letter_episodes.py

exec
/bin/zsh -lc '"git" "rev-parse" "HEAD"' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
2cdf77a4178b0f8e9736c72eb759ed7b55dc03b6

exec
/bin/zsh -lc '"git" "show" "--no-ext-diff" "--stat" "--oneline" "--decorate" "--summary" "af251e4a"' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
af251e4a fix(census): G4-9 Codex round-8 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9]
 .../G4-9-DLQ-census-2026-08-28.md"                 |   17 +
 .../G4-9-dlq-ledger-2026-08-28.json"               |    4 +-
 .../G4-9-evidence/artifact-commit-receipt.txt"     |    3 +-
 .../G4-9-evidence/grep-selfattest.txt"             |   79 +-
 .../codex-review-CARD-G4-9-round8.md"              | 5230 ++++++++++++++++++++
 ...75census\345\210\206\350\257\212-2026-08-28.md" |   14 +
 backend/scripts/census_dead_letter_episodes.py     |   93 +-
 7 files changed, 5364 insertions(+), 76 deletions(-)
 create mode 100644 "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round8.md"

exec
/bin/zsh -lc '"git" "status" "--short" "--branch"' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
## card/s5-census
?? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round9.md"

**Verifying commit ancestry and preserving untracked file**
**Auditing exact commit changes and parent diff**
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
/bin/zsh -lc "git diff --stat af251e4a..HEAD -- backend/scripts/census_dead_letter_episodes.py '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' '_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead

exec
/bin/zsh -lc 'git log --oneline --decorate -12' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
2cdf77a4 (HEAD -> card/s5-census) docs(census): receipt 补 round-8 commit [BATCH-2026-08-28-第五批 / CARD-G4-9]
af251e4a fix(census): G4-9 Codex round-8 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9]
85dd1c8f docs(census): receipt 补 round-7 commit [BATCH-2026-08-28-第五批 / CARD-G4-9]
f389980c fix(census): G4-9 Codex round-7 架构级修复 — 消除截断动作 [BATCH-2026-08-28-第五批 / CARD-G4-9]
4ba4f847 docs(census): receipt 补 round-5/6 commit 链 [BATCH-2026-08-28-第五批 / CARD-G4-9]
5b371253 fix(census): G4-9 Codex round-6 架构级修复 [BATCH-2026-08-28-第五批 / CARD-G4-9]
4c125f19 fix(census): G4-9 Codex round-5 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9]
d8d887f2 docs(census): 补 artifact commit receipt 绑定精确 SHA 链 [BATCH-2026-08-28-第五批 / CARD-G4-9]
d2827a6d fix(census): G4-9 Codex round-4 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9]
94b420ff fix(census): G4-16 Codex round-4 重放 recipe 确定化 [BATCH-2026-08-28-第五批 / CARD-G4-16]
fce0d8a2 fix(census): G4-9/G4-16 Codex round-3 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9 / CARD-G4-16]
73102875 fix(census): G4-9/G4-16 Codex round-2 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9 / CARD-G4-16]

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
/bin/zsh -lc 'git merge-base --is-ancestor af251e4a HEAD; git rev-list --count af251e4a..HEAD' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
1

**Inspecting commit diff and source lines**
**Prioritizing round8 report inspection over round9**
exec
/bin/zsh -lc "git show --no-ext-diff --format=fuller --find-renames -- backend/scripts/census_dead_letter_episodes.py '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' '_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md' '_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md' af251e4a" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead

exec
/bin/zsh -lc "rg -n -C 4 'BLOCKER|HIGH|MEDIUM|总裁定|最小剩余|不可验收|生成器|UAT|SQLite|symlink|scan_errors|tmp|fsync' '_bmad-output/审查/codex-review-CARD-G4-9-round8.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
10-reasoning summaries: auto
11-session id: 01a04881-c815-7ee3-942a-5e28699e753e
12---------
13-user
14:CARD-G4-9 round-8 复审（静态审阅 + 只读复算，禁改任何文件）。你 round-7 明确裁定「现有 92 条冻结 ledger 可以采信；生成器与 UAT 的纯只读安全声明不可验收」，并列出 1 BLOCKER（大小写别名根，无需竞态）+ 4 项路径 TOCTOU（根外 hardlink 指向隐藏目录内 transcript / 根 retarget / 检查后换父目录 symlink / basename 换 hardlink）+ 1 MEDIUM（非原子写）+ 2 LOW。开发方以 commit f389980c 做了**第二次架构级修复**：
15:1. 写出路径彻底重构：不再截断任何既有文件。改为「同目录 O_EXCL 新建临时文件 .<name>.census-tmp-<pid> → 写 → fsync → os.replace 原子替换」。全文再无 ftruncate 调用（grep 自证）。开发方主张：O_EXCL 保证写入目标是本进程新建对象，因此把 --out 换成指向恢复源的 hardlink / 父目录 symlink / 大小写别名这一整类绕过全部失效，同时消除崩溃/ENOSPC 留部分台账。
16-2. containment 判定改 _path_is_within()：从目标逐级向上比较 inode 身份 (st_dev,st_ino)，完全不依赖路径字符串（承认 round-6 用 os.path.normcase 是错误——POSIX 上它是恒等函数）；--out 与输入比较改 os.path.samefile。
17:3. 扫描受阻（scan_errors/stat_failures 非空）时直接拒绝写出台账 exit 2，而非仅在台账标 unverifiable。
18-4. lone surrogate 回退移到 json.dumps 后立即 .encode('utf-8') 探测（原异常发生在后续 write，不在 try 内）。
19:请逐项复核是否闭合，并针对新写出路径设计反例：临时文件名可预测导致的符号链接攻击（攻击者预先创建 .<name>.census-tmp-<pid> 为 symlink）、os.replace 的目标是 symlink 或 hardlink 时的行为、tmp 与目标跨设备、目录权限、并发同 pid、以及 _path_is_within 的循环 symlink/挂载点边界。同时复核台账仍为 92 条 / class 89-2-1 / byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0 / 重复簇 6/29 / unparseable 0 / attribution_conflict 3(no_token)、mode 0600、无 tmp 残留。逐项 CLOSED/NOT-CLOSED + 总裁定 + 新发现分级；若可验收请明确说明。
20-**Planning audit approach with memory**
21-**Planning multi-agent adversarial audit**
22-codex
23-我会按只读、fail-closed 复审：先恢复 round-7 的精确证据链与审计规程，再把代码静态审阅、写出路径反例、冻结 ledger 独立复算分轨并行；不会修改、生成或清理任何工作区文件。Graphiti / Sequential Thinking 若当前会话未暴露对应 MCP，我会明确记为审计能力限制，不拿缺失工具替代证据。
--
106-   173	- rollout_summaries/2026-08-19T14-44-08-upza-p1_05b_adversarial_review_finds_admission_quarantine_snapsho.md (cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output, rollout_path=/Users/Heishing/.codex/sessions/2026/08/19/rollout-2026-08-19T22-44-08-01a01a7a-c47f-70e2-8e5e-524e1591da78.jsonl, updated_at=2026-08-19T15:12:50+00:00, thread_id=01a01a7a-c47f-70e2-8e5e-524e1591da78, outcome=partial; detailed counterexamples)
107-   174	
108-   175	### keywords
109-   176	
110:   177	- P1-05b, symlink_escape, casefold, vault_backfill, lancedb_client, quarantine__p105b, search_nodes, read_node_tips, manifest-v3, NaN
111-   178	
112-   179	## User preferences
113-   180	
114-   181	- “启动并行 agent 进行对抗性审查” -> use independent evidence tracks and cross-check severity; every finding needs `file:line`, reproduction path/result, severity, conflict explanation, PASS/PARTIAL/FAIL, and limits. [Task 1][Task 2]
--
145-## Procedure
146-
147-1. Split independent tracks: vault admission/indexing and tests; Graphiti quarantine/retrieval; SnapshotV3/recovery anchors. Keep the audit read-only.
148-2. For each claim, build an evidence matrix: claim, `file:line`, adversarial input/state, actual entrypoint/path, observed result, severity, PASS/PARTIAL/FAIL, and limitations.
149:3. Directly exercise real entrypoints with temporary fixtures where permitted. For path admission include symlink, directory symlink, blacklisted filename in an allowed directory, case variant, and nonexistent path. Assert rejected inputs perform zero open/hash/index/write.
150-4. For quarantine, test ordinary edge search plus node search and exact-reader paths (`search_nodes`, `read_node_tips`, `read_node_errors`, `read_node_edge_reasons`). Use read-only Neo4j queries and `EXPLAIN` where allowed; distinguish observed metadata exposure from unproven fact-body leakage.
151-5. For SnapshotV3, test same-generation invalid/future version self-healing, extra fields, strict typing, huge finite values that may produce NaN/Infinity, and identity/length collision boundaries.
152-6. Compare recovery anchors with machine facts: current HEAD, Actions status, test counts, and unresolved findings. Separate targeted-test results from whole CI.
153-7. Cross-check high-severity findings independently. Write the final matrix before closure language; explicitly retain `UNVERIFIABLE` items and failed counterexample attempts.
--
179-我正在采用记忆中的 `canvas-adversarial-audit` 规程，因为本轮正是 Canvas 的对抗性 closure audit；它要求独立证据轨、生产入口反例、`file:line` 可复现证据，以及对未验证关键面的保留。该规程只影响审阅方法，不授权任何写入。
180-只读 round-8 复审：先锚定 checkout/差异与生产入口，再并行审计写出安全、containment、冻结 ledger，最后由主审独立复核高风险结论并汇总 CLOSED/NOT-CLOSED。
181-  → 锚定 HEAD、commit f389980c、工作树状态、任务/规则与变更文件
182-  • 静态审阅原子写出实现并设计/验证指定反例
183:  • 审阅 _path_is_within 与 samefile 的 symlink/挂载边界
184-  • 独立只读复算冻结 ledger 的全部数量、分类、权限和残留
185:  • 交叉复核高风险发现并给出逐项裁定、分级和总裁定
186-**Planning seamless internal calls**
187-mcp: sequential-thinking/sequentialthinking started
188-mcp: sequential-thinking/sequentialthinking (completed)
189-**Planning streamlined command execution**
--
196-git show --stat --oneline --decorate --no-renames f389980c
197-rg --files -g 'AGENTS.md' -g 'CLAUDE.md' -g 'CURRENT_TASK.md' -g '*census*' -g '*ledger*' -g '*CARD-G4-9*' -g '"'!node_modules'"' -g '"'!.git'"'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
198- succeeded in 0ms:
199-/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
200:git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
201-/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
202:git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
203-85dd1c8fd625759642fa45e483bec52e999efb0a
204:git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
205-card/s5-census
206:git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
207-?? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round8.md"
208:git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
209-f389980c fix(census): G4-9 Codex round-7 架构级修复 — 消除截断动作 [BATCH-2026-08-28-第五批 / CARD-G4-9]
210- .../G4-9-DLQ-census-2026-08-28.md"                 |   16 +
211- .../G4-9-dlq-ledger-2026-08-28.json"               |    2 +-
212- .../G4-9-evidence/grep-selfattest.txt"             |   92 +-
--
234-_bmad-output/审查/codex-review-CARD-G4-9.md
235-_bmad-output/审查/codex-review-CARD-G4-9-round4.md
236-backend/scripts/census_graphiti_pollution.py
237-backend/scripts/census_dead_letter_episodes.py
238:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md
239-
240-**Inspecting commit ancestry and logs**
241-exec
242-/bin/zsh -lc 'wc -l CLAUDE.md CURRENT_TASK.md _decisions/CURRENT_TASK.md
--
247-     135 CLAUDE.md
248-     294 CURRENT_TASK.md
249-     329 _decisions/CURRENT_TASK.md
250-     758 total
251:git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
252-85dd1c8f (HEAD -> card/s5-census) docs(census): receipt 补 round-7 commit [BATCH-2026-08-28-第五批 / CARD-G4-9]
253-f389980c fix(census): G4-9 Codex round-7 架构级修复 — 消除截断动作 [BATCH-2026-08-28-第五批 / CARD-G4-9]
254-4ba4f847 docs(census): receipt 补 round-5/6 commit 链 [BATCH-2026-08-28-第五批 / CARD-G4-9]
255-5b371253 fix(census): G4-9 Codex round-6 架构级修复 [BATCH-2026-08-28-第五批 / CARD-G4-9]
--
260-fce0d8a2 fix(census): G4-9/G4-16 Codex round-3 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9 / CARD-G4-16]
261-73102875 fix(census): G4-9/G4-16 Codex round-2 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9 / CARD-G4-16]
262-e7a480eb docs(census): G4-16 doc_type族接线普查 18文件146行+6取值裁定+注释修正 [BATCH-2026-08-28-第五批 / CARD-G4-16]
263-67ccebe1 docs(census): G4-9 DLQ真实挂载census分诊 92条台账+挂载真相+三态裁定 [BATCH-2026-08-28-第五批 / CARD-G4-9]
264:git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
265:git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
266- .../G4-9-evidence/artifact-commit-receipt.txt"                        | 4 +++-
267- 1 file changed, 3 insertions(+), 1 deletion(-)
268:CURRENT_TASK.md:51:- ✅ **用户 8/8 全批**（R9 批注逐字）: ①P0-1 方案先行 ②E-2 快照选 **A**（只存投影安全面+秩数值，MEDIUM-2 悬案定案）③执行序改 Codex 8 步（P0 止血→数据边界→可信基线→证据修复→安全写入基建→分批落地→价值验证→缓行）④审批每轮只递 **6-8 项** ⑤A-2 扩容: mastery 提交前并入 tiktoken 断网兜底（compression.py:46 只捕 ImportError）+ nodes.py:97 timeout 200ms→按实测校准，WT 代码与 MAIN/.gitignore **分 commit** ⑥D-2 先按真实路径重数 DLQ（live=`WT/data/dead_letter_episodes.jsonl` 仅 1 条；`WT/backend/data/` 92 条为陈旧文件）⑦B-2 广度回顾先做**薄版 MVP**（只新增回顾报告文件，零改原白板/YAML，真实板试跑用户说「有帮到」再扩）⑧E-5 Dashboard webUI 入缓行区
269-_bmad-output/implementation-artifacts/goal-cards/2026-08-27-主goal全量分goal总账.md:34:| G4-9 | DLQ 真实挂载 census 分诊 | 4h | — | 否 | 未来铺路 |
270-_bmad-output/implementation-artifacts/goal-cards/2026-08-27-主goal全量分goal总账.md:65:| G4-11 | Graphiti rebuild matrix 台账 | 5h | G4-9, 5-ge-1(epic-5a,软—新类型入表) | 是 | 未来铺路 |
271-_bmad-output/implementation-artifacts/goal-cards/2026-08-27-主goal全量分goal总账.md:94:| G4-10 | DLQ 根因修复与 replay | 6h | G4-9, G4-6 | 是 | 未来铺路 |
272-_bmad-output/implementation-artifacts/goal-cards/2026-08-27-主goal全量分goal总账.md:105:| G8-3 | /lint 第二批：批注/DLQ/备份 | 5h | G8-2, EXT:G2-VaultScope（跨vault身份子检查的接入前提） | 是 | 防暗坑 |
--
448-- ✅ CARD-G5-1 触发矩阵 v3：矩阵文档（15 正例含 5 用户逐字 + 10 负例 + 语料覆盖自陈 + §三 待拍板 + **§五 登记簿 4 条**）
449-  + checker v3 9/9（real_floor 代码锚+归属锚语义分类；18 类变异负控全抓）+ headless 三轮全量重放（judge v3：
450-  sidecar 绑定/终局唯一/manifest 含 .claude/skills）：**⛔ N4「回顾一下+板名」无斜杠存档 2 采样 1 次真触发 board-recap**
451-  （最重要发现，直接喂 §三 拍板）+ N6 误触发全局 study-plan（2/2 复现）+ N2 代行写侧 + B2 形式化漂移（存档 5 份 2/3）
452:- ✅ CARD-G5-2 拆分 preview 引擎 v3：split_preview.py（写侧物理 fail-closed 次序修正+单FD / 目录级 symlink containment /
453-  slug JS空白集+UTF-16 边界+偏差5声明）+ 裁判 34 条四轮先红后绿（含剥离反事实常驻测试）+ live 全 324 文件全字段
454-  基线零净差异（set -x 回放+引擎字节绑定, `审查/g5-2-evidence/`）
455-- Codex：G5-1 三轮（1 轮 3B+4H → 2 轮复核 → 3 轮终核）；G5-2 四轮（cyber误拦→6H→复核→终核）全存档
456:- 验收单：`验收单/UAT-CARD-G5-{1,2}-*.md`；**不 push**
457-- ⛔ 待用户：①验收两单 ②拍板 R8 口令取舍（G5-8 前必裁, N4 实证必读）③语料覆盖自陈口径认可（C/D 类无真实触发语,
458-  总账「各≥3 真实正例」硬门 vs 语料实况的裁决权在用户）④outputs/ 测试产物未入 commit
459-
460----
--
483-- ✅ **C1 `32e9e29c` 写侧闭环**: SyncBatchRequest.vault_id 升必填（缺失 422，唯一调用方 DEPRECATED Tauri 前端属预期）; sync.py handler 显式接 resolve 返回值 → `to_physical_group_id` → `process_sync_batch(request, group_id=物理gid)`; 六条 Cypher MERGE/MATCH 键全部变 `{id, group_id}` 复合键（`_delete_board` 级联双侧都带 group）; canvas_projection_sync/exam_service_ext 三方共键同批切换; 新 `test_sync_group_isolation.py` 10 条**行为断言**（红灯先行，检查 run_calls 实际 Cypher+参数，教训锁: wave5 静态断言逃逸）
484-- ✅ **C2 `496a2147` 迁移件**: `migrations/003` 五段式 + `scripts/migrate_canvas_group_isolation.py`（--dry-run/--apply, ⚠️ 不复用 group_id_migration_service 的 IS NOT NULL 扫描器）+ 11 条脚本测试
485-- ✅ **现网 dry-run census 已跑（只读）**: NULL 三 label 全 0 / CanvasBoard label 不存在（库里 11 CanvasNode + 9 CANVAS_EDGE 全在 `vault__canvas_vault`）/ **SHOW CONSTRAINTS 为空 = migrations/001 从未在 7691 生效过** → --apply 实际变更 = 纯新建 3 条复合约束，回填是 no-op
486-- ✅ **零旁路破坏已证**: stash 基线对照，HEAD 与修复后失败集逐条一致（19 条全存量: auth Settings 校验器 / exception P0-2 fail-closed / wave5 tips 静态断言 / projection 旧签名 / qa_38_6×5 / story_38_8×1）
487:- 🔒 **[Code-Review] 独立对抗审查已收官**: APPROVE-WITH-FIXES；核心修复被证实无漏（六条 Cypher 全带键 / 物理格式链闭合 / 无 cypher_with_group_filter 误用 / 无 ContextVar 依赖 / 全仓无旁路写入点，11 条候选证伪）。F1 HIGH（exam sync-node 边写入空匹配谎报 edge_created=True）+ F2（迁移 edge 回填不继承端点 group）+ F3（空白 vault_id 绕必填）已在 **C3 `ad82529a`** 处置并加行为测试；F4（verify_targeted_exam_chain.py 裸 id MERGE）/ F5（DEPRECATED 前端 sync-engine 无限重试）/ F6（head(collect) 非确定边角）+ **exam sync-node vault_id 必填化（F1 根治）** 挂账 Phase 2
488-- ⏳ **收尾两步（等用户批）**: ①census 过目后批 `--apply`（实际=纯新建 3 条复合约束，回填 no-op）②**重启 backend 容器**（Dockerfile 无 --reload，代码不重启不生效）→ 双 vault curl 最小验收（两 vault 同 entity_id 写 → 两节点; 删其一 → 另一存活）+ targeting_material_service 出题链正向验证
489-- 📋 **挂账 Phase 2（按 6-8 项/轮递审批）**: 读侧 10+ 处 group 过滤（recommendation_service:167/176/192/227/242、verification_service:2175/2208 by-name、question_generator:951、cross_subject_bridge:153、subjects.py:64/234）· cypher_with_group_filter() MERGE 适配 · Graphiti 记录本轮 [Decision]/[Code-Review]（本 session 无 graphiti MCP，欠账）
490-
491-**上一状态**（2026-08-17 · **双外审收官（ChatGPT+Codex 盲评交叉）· 用户 8/8 裁决全批 · 下一步=P0-1 修复方案** · PLAN `CODEX-ABSORB-2026-08-17`）:
492-- ⛔ **新 session 第一件事**: 进 Plan Mode 为 **P0-1 `/sync/batch` 跨 vault 裸 ID 写删**单独出修复方案（选项: 全部 MATCH/MERGE/DELETE 键补物理 group_id vs 临时禁用路由），用户确认后再实施、不与其他修复混提。证据: `[WT] sync_service.py` 全文 grep group 零命中、:358 裸 `MERGE {id:$entity_id}`、:532-538 按 canvasId 级联 DETACH DELETE、sync.py:101 ContextVar 注入后执行层从不消费。⚠️ `cypher_with_group_filter()` 对 MERGE/CREATE 生成非法语法，禁止机械套用；方案必须含 MATCH/MERGE/DELETE 三类双 vault 隔离测试
493:- ✅ **用户 8/8 全批**（R9 批注逐字）: ①P0-1 方案先行 ②E-2 快照选 **A**（只存投影安全面+秩数值，MEDIUM-2 悬案定案）③执行序改 Codex 8 步（P0 止血→数据边界→可信基线→证据修复→安全写入基建→分批落地→价值验证→缓行）④审批每轮只递 **6-8 项** ⑤A-2 扩容: mastery 提交前并入 tiktoken 断网兜底（compression.py:46 只捕 ImportError）+ nodes.py:97 timeout 200ms→按实测校准，WT 代码与 MAIN/.gitignore **分 commit** ⑥D-2 先按真实路径重数 DLQ（live=`WT/data/dead_letter_episodes.jsonl` 仅 1 条；`WT/backend/data/` 92 条为陈旧文件）⑦B-2 广度回顾先做**薄版 MVP**（只新增回顾报告文件，零改原白板/YAML，真实板试跑用户说「有帮到」再扩）⑧E-5 Dashboard webUI 入缓行区
494-- ⛔ **拓扑修正（Codex 发现，已入记忆）**: compose `./data:/app/data` 子挂载**遮蔽** `backend/data/` → 容器内 reference_config 读 `/app/data/…json`（不存在）走 **fallback 旧权重**（videos 1.5/1.4）；权重 split-brain 实为三方（容器 fallback / 宿主脚本新值 / MAIN 旧值）。修复归 8 步序第 3 步「可信基线」
495-- 未提交变更（有意，对应⑤）: `backend/lib/agentic_rag/mastery_injection.py` 修复 + `backend/tests/unit/test_mastery_injection_memory_contract.py` + `MAIN/.gitignore` raw 行
496-- 关键文档: Codex 报告 `_bmad-output/审查/2026-08-17-Codex对抗审查-独立裁定报告.md` · 吸收+逐条复核+8 项裁决 `_bmad-output/审查/2026-08-17-Codex裁定-吸收与两家交叉对照.md` · 通俗版+用户批注原文 `_bmad-output/研究/2026-08-17-批注回复-R9-八项裁决通俗解释.md` · 审批单（待按 8 步序重排 + 用户旧批注待合并去重）`_bmad-output/研究/2026-08-16-设计讨论书-待批事项完整汇总-逐项审批单.md` · 事实基线（待按吸收文档 §二 打 5 处补丁）`_bmad-output/研究/2026-08-15-全项目现状核实-设计说的vs代码做的.md`
497:- 事实勘误随手账: 审批单确认点 ≥29 非 21 · S2.6 mini-UAT 实为 **3 勾 2 未**（非四条待签）· gen_excalidraw_v3.py 不在仓内（仍在 session scratchpad，会丢）· doc_type `primary-record` 族在 TYPE_WEIGHTS **整族未接线**（两种写法均落 0.5 fallback）· `_待处理`/`_archive` 无索引排除规则（→ A-9 必须前置于 B-1/C-1）· 批注格式已到**第五代** `**User ：`/`**User 修正：`
498-
499:**上一状态**（2026-08-11 · **阶段 2.6 导航改造施工完成 · 金集 34/34 + 协议校验 35/35 + M1-M4 全达标 · 待用户 mini-UAT（3 勾 2 未）** · PLAN `RAG-S2.6-2026-08-11`）:
500-- ✅ **T0 落点校准**: live vault = `canvas-learning-system/canvas-vault/`（`.env` CANVAS_BASE_PATH，Obsidian/Claudian 实读）；纪律 = **改 live → 定向文件级同步 worktree → 每批末 `diff -rq`**。⛔ 禁整目录同步（worktree vault 缺 CS188/CS189 与 6 张检验白板、却多 TestConceptA/B fixture）。**计划的「5 份 skill 未入 git」前提证伪**：那是 main 分支视角，本分支 8 份早已全部入库（04-17~07-30），裁定门自动消解
501-- ✅ **T1 backend 两字段**（commit `ec9c6849`）: `pick_hint.pick_rank`（板内**可考察**候选秩，排序键 `(pick_score, node_id)`；⛔ 只覆盖非占位——占位若占掉 rank1 消费侧过滤后就扑空；在 `_carve` 而非 scan 赋秩 → 历史快照降级态也有秩）+ `past_question_digests[].score_scale`（⛔ 不是自由文本槽位：「数字–数字」形状白名单 + 40 字硬截断，不合形状降级定长文案；缺字段 → `1-4 (1=最低) [推定]`，DD-13 不把推断说成声明）。契约 46→52 绿、金集 32→34、全量 regression 393 passed、延迟 6.1/2.6/2.5ms、exam payload 4.63/6.60KB
502:- ✅ **T2 Concepts 视图化**（commit `487d7851`）: 新 `canvas-vault/.claude/scripts/sync_board_concepts.py`（真相源=节点 `source_board`，零外部依赖，tmp+os.replace 原子写，比对**排除 synced 时间戳**否则 `--check` 永远报漂移）。⛔ 托管区间取**包络**（实测 6 板两种历史形态）且 **sentinel 存在时并进段内游离概念行**——插件 `appendBoardLines`(main.ts:2558) 插在**整段边界前**即落在 END 之外，只取 BEGIN..END 会留重复行（已按插件真实语义写模拟器复验）。写侧三点接线（ai-linked-doc Step7 / configure-whiteboard Step6 / quiz-answer 新 Step4c-bis）+ 模板换 sentinel 空块；⛔ 顺带修真缺口：configure-whiteboard Skill 此前**没给种子写 `source_board`**（plugin 有写、Skill 漏了）。双锁全绿 + doc_count 漂移×2 归零 + 关 Dataview 仍明文可读
503-- ✅ **T3+T4+T5 八份 skill 接入**（commit `4244c021`）: canonical ROUTING 块 8 份逐字节相同（SHA `06b0167cc02c`），四平面 STRUCTURE/SEMANTIC/CONTENT/EXAM + HARD-NAV-1..4 + 每份 PLANE-BINDING 5 字段。旗舰 start-exam-board Step3 **19-26 次 → 1 次**、Step4.8 **零工具调用**、Step4 折入 calibration 删 Step5 独立 Grep、Step7 回执要求逐行照抄 `pick_rank`（可外部机械比对的锚点）；⛔ DD-13 修正 HARD CONSTRAINT #1 名实（澄清 HARD-21 管语义检索、与结构检索无关）；⛔ FALLBACK inline python 补 `effective()`——考察链是四方里唯一漏掉闲置折旧的一方（用户裁定 3）。configure-whiteboard Step4.2 全库唯一 O(节点数) 全节点 Read 循环 15→5 次；study-question §3.0 / chat-with-context 开场前**条件触发**限域（⛔ HARD-11/17/21 一字未动）；exam-quick/quiz-answer/node-chat 各写明**为什么禁用 STRUCTURE**
504-- ✅ **验证四层**: 校验器 `check_skill_routing_block.py` **35/35**（C0 全集/C1 逐字节/C2 硬约束齐/C3 绑定自洽/C4 **工具面⇔绑定**/C5 FALLBACK 成对不嵌套）· 探针 `run_skill_navigation_probe.py` **M1-M4 全达标**（⛔ 不模拟 LLM，真 vault 真文件真字节，旧基线取自迁移前 .bak；M1 median 1→0 / M2 median 7.5→1 / CS188 板 **21→1 次**）· 真机 E2E 三板 · **降级路径与主路径逐行相等（三板 1e-6）**
505-- 🐛 **顺带修的真 bug**: `csm-tutoring-unit-credit` 有 `source_board` 但不在 `## Concepts` ⇒ 2.6 前读 Concepts 选点的 skill **永远考不到它**；T2 从写侧根除后两条路径都能选到（不是只在主路径绕过去）
506-- ⚠️ **金集 G3 期望值同批改**: 2.5 把 CS 61B `frontmatter_only: ["csm-tutoring-unit-credit"]` 封成期望（「漏记告警必须亮」），T2 根除后归零 → 改 `[]` 并 `--update-baseline --reason`（修复带来的期望变更，非回归）
507-- ⚠️ **登记 backlog**: worktree 的 `canvas-vault/原白板`、`节点` 是**陈旧副本**，在其上跑迁移会得出对 live 错误的派生值 → 白板内容**不入库**（已回滚 HEAD）；live vault 白板改动保持未提交 + `.bak` 存于 `.claude/cache/rag-s2.6-concepts-backup/` 可回滚。真正修法是把 live 内容同步进 worktree，不在 2.6 范围
508-- 🔒 **[Code-Review] 三视角独立对抗审查 24 条发现全部处置 + 全部加回归锁**（每条先自行复现再改，未直接采信）:
509-  - ⛔ **C-H1 真实数据损坏（最严重）**: `managed_region` 取 min..max **包络** ⇒ 用户在 `## Concepts` 段手写的备注/代码块/`---` **被静默删除**（完整触发链已跑通: 手写 → 下次 Cmd+Shift+D 时 plugin 在段尾追加裸行 → 手写内容夹在中间被连坐）→ 重写成 `managed_lines()` **逐行**标记受管行
510:  - ⛔ **HIGH-1 泄漏**: `score_scale` 形状白名单**只有头锚没尾锚**(`.match()` 无 `$`) ⇒ `1-4 反例 diag(-1,-1)…`（**G6 金集禁串**）整串原样透出 → `fullmatch` + 收紧文法 + 先验形状再截断
511:  - ⛔ **HIGH-2 静默劫持**: `mastery_a: .inf/.nan` ⇒ nan 比较恒 False 让 Timsort 保持输入序，投毒节点吃掉 `pick_rank=1` 且 `parse_errors` 空；自查另发现 exam JSON 吐**裸 NaN = 非法 JSON** → `_num` 加 `isfinite` 门 + 显式上报 + 秩过滤 + 严格 JSON 断言
512:  - ⛔ **D-HIGH-1 我自己的方法论错误**: 上一版「降级路径逐行相等」验的是**我修好的路径**——SKILL 的 Grep 当时没取 `last_examined`，闲置折旧在降级态整体失效 → 补字段 + **写脚本从 SKILL 正文抠出 Grep 与 python 直接执行**重验（三板逐字段相等，`idle=16.9d` 是折旧生效的证据）
513:  - ⛔ **C-M6 已在真 vault 生效**: `mkstemp` 恒 0600 + `os.replace` 继承 ⇒ 6 块白板权限被从 0644 静默改成 0600 → `os.chmod(tmp, 原 mode)` + **已改回并复验不再复发**
514:  - ⛔ **D-MEDIUM-5 校验器只数信封不看信**: 掏空降级块/改坏 import/新增裸调用/把降级反转成「停止并叫用户起服务」六种腐烂全判绿 → 加 C6(按小节校 HARD-NAV-3)/C7(ast.parse + import 符号存在)/C8(禁中止语义)，**35 → 59 项**
515:  - 其余: MEDIUM-1 G8 子串判定被 `[推定]` 前缀绕过→改闭集 / MEDIUM-3 SKILL 把 manifest 划进可信面→新增 **HARD-ISO-5b** / D-HIGH-2 降级把占位也编秩致秩号错位→排序前剔除 / D-HIGH-3 反向引用 regex 未 `re.escape` 致含括号节点整批漏检→已修 / D-MEDIUM-4 缺 Concepts 段时 exit 0 还说「已同步」→抛异常+退出码分层 / C-H3 frontmatter 自由文本被逐字写进白板→只认真 wikilink / C-H4 与后端 7 条语义分歧→逐条对齐 / C-H5 批次非原子 / C-M7 无 fsync / C-M9 行尾归一 / C-M10 doc_count 只改首处 / C-M11-13 断链·孤儿·多 sentinel 静默→全改成告警且 `--check` 红 / C-M14 `.bak` 二次覆盖
516-  - **复验**: 协议校验 35→**59/59** · 全量 regression **425 passed**（393→+32: 契约 46→64 + 新 `test_sync_board_concepts.py` 20 项）· 金集 34/34 · 探针 M1-M4 全达标 · 脚本 `--check` 幂等无告警 · ruff 全绿
517:- ⚠️ **待用户裁定（我没单方面改）**: 审查 MEDIUM-2 —— `view:"exam"` 调用**本身**把全量禁项原料明文落盘到 `<vault>/.claude/cache/`（真 vault 那份 22KB 快照含 G6 禁串明文，出题 agent 有 Read 权限）。本轮只做 prompt 级 **HARD-NAV-5**（禁读 `.claude/cache/`）+ gitignore；彻底修法二选一: **A** 快照只存投影安全面（代价: 降级态 study 视图丢 tips/errors）/ **B** 快照移出 vault 到 backend 侧（代价: 反转 2.5「落 .claude 双黑名单」的架构决定）
518:- 📋 **用户 mini-UAT 卡**: `_bmad-output/验收单/Story-RAG-S2.6-导航改造-mini-UAT.md`（DoD-3 七段 + 4-A/4-B 双段，段 4-B 禁词 0 命中 / 4 条全用「我做 X → 我看到 Y → 我感觉 Z」句型；⚠️ 首行提醒 `Cmd+Q` 完全退出重开 Obsidian —— MCP/skill session 缓存 2.5 踩过两次）
519:- ⏭ **下一步**: 用户 mini-UAT 签字 → **阶段 3**（退役 8765）。2.6 明确不做: structure-navigator 子代理（用户已砍，回退阈值：单次 skill >3 次 manifest 调用或单板 exam JSON 常态 >8KB 则 2.7 重议）/ 批量 candidate 端点（manifest 已是）/ backend `calibration_gap` 字段（折入 skill 抽取器）/ 改前端插件（DD-12）/ 改 `score_scale` 写侧（vault 已有）/ 砍 study-question HARD-11/17/21 / LLM 查询改写 / 1.5 稳定 ID / Neo4j 投影
520-
521:**上一状态**（2026-08-11 · **阶段 2.5 Board Manifest 施工完成 · 金集 31/31 全绿 · 待用户 mini-UAT** · PLAN `RAG-S2.5-2026-08-10`）:
522-- ✅ **T0 依赖+迁移**: python-frontmatter 依赖洞首 commit 修复（364d2b39, docker build 验证过）; vault 迁移用户四项签字（删 TestConceptA/B/C + csm-tutoring 归 CS 61B + 考察产物移检验白板 + main 直接 commit 44113f54）→ **14/14 节点全员 source_board, 孤儿清零**; T0.5 特征值 Concepts 实测 3 条定案（Plan agent「空 section」说法证伪）
523-- ✅ **T1-T3 已 ship**（worktree commits 870ca8f5/55f9421e/bcdde1ad）: board_manifest_service（ManifestDataSource Protocol + mastery 四态归一化 + is_stub + dual_source_gap 窄解析 + pick_hint 内联 decay_beta 1e-9 契约锁）; exam/study 双视图 Pydantic 投影（**exam 禁项=模型结构性缺字段**, live/快照 serve 共用唯一投影点）; 快照三态降级 `.claude/cache/board-manifest/manifest-v1.json`（generation 变更才重写+原子写, live→snapshot→error 诚实申报, 真实环境实测退快照+恢复全过）; HTTP `POST /api/v1/boards/manifest`（prefix=/boards 防 wildcard, require_internal_api_key + vault fail-closed 409）+ MCP `get_board_manifest`（第 6 只读工具, 空 body 防 P16, quarantine 测试 5→6 同步）
524-- ✅ **T4 金集**: `scripts/run_board_manifest_regression.py` + `board_manifest_gold_set.yaml` 31 条硬禁通道（G1 成员×6/G2 孤儿/G3 gap×3/G4 字段×10/G5 历史×3/G6 泄漏×8 含合成投毒）**宿主+容器双姿势全绿, 基线封版**; 契约测试 41 绿; 全量 regression 381 passed 零旁路破坏; 实测延迟: 列板 104ms/exam 79ms/study 61ms（预算 <300ms）
525-- 🐛 live 实测抓 bug: BUG-361BD6FC（YAML datetime 透传 tips/error_candidates 炸快照 json.dumps）→ _json_safe 深度清洗+回归锁
526:- 📋 **用户 mini-UAT 卡**: `_bmad-output/验收单/Story-RAG-S2.5-BoardManifest-mini-UAT.md`（技术三条 Claude 已全部代跑留档, 用户只验 Claudian 产品体验; ⚠️ 宿主改目录名容器 ~10s 才可见=VirtioFS 缓存）
527:- 🐛 **UAT 两轮实锤两个 MCP 面 bug（已修复+回归锁）**: ① 旧 Claudian session 缓存 5 工具列表（server listChanged:false 不推变更, JSON-RPC 实测 server 侧 6 工具一直在列）→ 用户侧 /mcp 重连即可, 非 bug; ② ⛔ `input: X | None = None` P16 模板让 requestBody 变 anyOf → fastapi-mcp 展不开 properties → **MCP inputSchema 参数全丢**（Claudian 只能无参列板, board_id/view 调不出）→ 改 `Body(default_factory=...)`（该模板只适用空输入模型, check_backend_health 恰好无参才没炸）+ quarantine 新增参数面回归锁; E2E 复验: tools/list 三参数齐 + 带参单板 exam 调用 3 节点/6 历史 + 空参列板 P16 不炸
528:- 🔒 [Code-Review] 独立对抗审查（E2E 复现式）**3 HIGH / 3 MEDIUM / 5 LOW → 全部处置, 复验 32/32 全绿**: ⛔ H1 orphans 回显通道（source_board 塞定义全文进 exam 视图, 已复现）→ reason 定长枚举文案+raw 截断 120+模型 max_length 门; ⛔ H2 parse_errors 回显（last_examined repr 无界+纯 Python yaml loader str(e) 引用原文行含 correction 禁串）→ _safe_err 去内容化（异常类型+行号）+repr[:80]+模型 200 字门; ⛔ H3 untrusted 标量炸投影（`doc_count: 大约五个`/`title: 2026` → ValidationError 500 整端点含列板）→ _bounded_str 类型归一×7 字段+双暴露面 ValidationError 纵深兜底; M4 digest 吸入相邻 [!feedback]/[!hint] callout（可含正确答案）→ callout 边界终止收集; M6 #heading 锚点+大小写敏感→假孤儿（喂 H1 通道）→ resolve 剥锚点+boards_ci casefold 匹配; M7 金集合成A恒真条件（自比较）→ 改「挖掉 reason 槽位后 0 命中」; M8 禁串无正向对照会静默腐烂→禁串必须仍在 vault 源文件+G5 digest 非空对照（金集 31→32 条）; L 批: 快照 tmp 唯一名防竞态/load 快照 schema 必备键校验/exam_board_count 恒用 full 历史/信封字段统一截断/set_current_subject_id 移到 fail-close 之后。审查确认: 投影穿透 E2E 失败（防线真实）、快照双黑名单成立、serve 路径唯一、pick 数学锁死、无 DD-03 违规。新增回归锁 6 条（契约 77 绿）
529-- 📌 顺手发现: **8 个未剖析占位节点**（CS188×7+特征值 Eigenvalues-special, is_stub 如实标注）; doc_count 漂移×2（CS 61B 声明1实际2/递归声明0实际1, 归 2.6 写侧）; 金集 shadow 分区已作观察面
530:- ✅ **UAT 产品体验项第三轮实测通过（待用户签字）**: Claudian 单次带参调用拿全量拆解并直接给学习诊断（beta/score_only 双轨判「板有没有真在用」= manifest 立足点的活证明）
531-- 📌 **2.5 收尾 backlog（新增 3 条）**: ① digest 裸 score 无量纲标注被消费侧误读成满分（实际 1-4 制 1=最低; 加 score_scale 字段属 exam keyset 契约变更, 走 --update-baseline 流程, 归 2.6）② 选点贪心锁定观察（枢纽 μ 极低时叶子排不上; 注意 Eigenvalues-special 是 stub 本就该跳过）③ Concepts 行内 "(mastery: 0.30)" 快照文案与真值脱节（2.6 写侧视图化处理）
532:- ⏭ **下一步**: 用户 mini-UAT 签字 → **2.6**（`## Concepts` 写侧视图化 + 8 skill 接入 manifest 替代 Grep 拼图）; 2.5 明确不做: 1.5 稳定 ID（字段已标注 basename_v1）/ Neo4j 投影修复（backlog, Protocol 接口已留）/ 写端点 / exam 承载 misconception / FSRS 字段
533-
534:**上一状态**（2026-08-10 · **阶段 2 收官 ✅ 用户 UAT 四步全过** · 下一步: 九阶段路线 2.5/2.6 · PLAN `RAG-S2-2026-08-09`）:
535:- ✅ **阶段 2 UAT 通过（用户实测四步全过 2026-08-10, 记录在卡）**: ①手写优先+dedup+wikilink 7/7 真实 ②vault 外主题零编造（`ce_gate_all_filtered` 标注实锤）③search_notes 与 hook 同源（加权分量纲 0.55-0.60 实证）④检验白板零泄漏（弃答闭环记录/原白板导航均为设计特性非泄漏）。卡: `_bmad-output/验收单/Story-RAG-S2-阶段2-强化fastpath-UAT.md`
536:- 📌 **UAT 新观察项**: 「特征方程」query 注入 7 条 RL「特征表示」— 中文共词假匹配 CE 门未杀（已知 CE 盲区家族), Claude verifier 层自行绕开转 search_notes; 归 CE 盲区 backlog 追踪
537-- ✅ **三决策用户已裁定（全采纳推荐项）**: ① **f06/h07 移 shadow**（金集 v2, 58 条; 基线: MRR 0.7889/nDCG 0.7121/交付 84.91%/污染 38.60%/FPR 6%; 红档只剩 f04/z04 真实能力缺口; file_locate 意图路由 backlog, exam_board 任何方案绝不放行）② **f04 扩池不做**（扩池仅 file 级 rank4、+31% 延迟 — 根因段落级召回, backlog 等 chunk 侧补强）③ **[!note] STRIP 维持现状**（census 零误伤实锤）
538-- ⏭ **下一步**: 九阶段路线（0→1→1.5→**2 ✅**→2.5→2.6→3→4→4.5）进 **2.5/2.6**（开工前重读九阶段路线定义 `_bmad-output/研究/2026-08-02-RAG修复计划-用户审阅版.md` §施工顺序与工期 L93 — A-1 修正于 R11-BATCH2: 原指 `2026-08-09-RAG阶段2-强化fastpath实施计划.md`，该文件存在但仅 36 行、是阶段 2 的单阶段计划，不含九阶段路线，反而把 2.5/2.6/4.5 列入「明确不做」）; 阶段 2 backlog 汇总: CE 盲区类（a01/z02/z05/特征共词）/ f04 段落级召回 / file_locate 意图路由 / extended 分支 taint / MCP top_k 漂移 / tier-2 legacy exam_board / RETRIEVAL_RERANKER_* compose 白名单
539-- ✅ **T6 验证收尾完成**（17-agent workflow: 4 路验证 + 3 lens 全链路对抗审查 + 逐 finding 证伪）: 金集终验通过 + shadow 空（设计态）; live 实测 9 项全 PASS（hook 四态/MCP confidence/考察隔离/M6 410/refresh-changed 存活/18012 双向可达）; **[!note] STRIP census 实锤零误伤**（206 md 仅 1 处且嵌套 error-candidate 内被 EXTRACT 保留; info/video 55 处全系统模板）; **vq-f04 扩池实测**（50 池 file 级 rank4 但「烘」段落仍不召回, 延迟 +31%）; **vq-f06/h07 结构性死档实锤**（期望文件全 doc_type=whiteboard 被查询侧排除, 反事实去排除 rank1 立即回归, 选项 B>A>C 待用户裁定）
540-- 🔒 [Code-Review] T6 全链路审查 **8 CONFIRMED / 2 REFUTED → 全部处置**: ⛔ **HARD-ISO live 泄漏**（vault_notes_retriever 默认排除表漏 exam_board, 经无鉴权 /api/v1/rag/query + agents.py 六处可达 → 补齐; react_agent/tool_executor/agent_graph 三条 flag-gated 链同批纵深补齐）; **fts_confirmed 名实颠倒**（_rrf_score 写给所有融合行, dense-only 恒 True/真词法命中反 False → _rrf_fuse 新 _fts_hit 通道标记 + 白名单 + svc 公式改 `_fts_hit and not _fts_only`, 仍遥测-only）; **检索层故障吞噬纵深**（_search_internal 全分支故障 raise 受 enable_fallback 门控[默认 True 调用方行为不变] + open_table 失败 raise + hook singleton 关吞噬/init 失败不缓存 + 空交付文案不再主动断言「检索正常」）; ⛔ **elbow telescoping = 三轮金集 A/B 裁决保留 T4 行为**（审查数学观点成立, 但两种修复均被金集打回: 全量序列 floor → 污染 39.83→57.38%/FPR 8%; dedup 后门前 floor → 48.25%/8%; +1.8pp 命中换不回 +8~17pp 污染 — 门后 telescoping 截断是净正收益保守护栏, 数据与翻案条件锁进 test_gate_thinning_elbow_is_deliberate_t4_behavior）; REFUTED×2: react_agent/agent_graph「拨真即泄漏」不可达（仍随批纵深补齐排除表）; LOW backlog: extended 分支无 taint / MCP top_k 参数漂移 10vs15 / TYPE_WEIGHTS concept 死键
541:- 📋 **用户 UAT 卡**: `_bmad-output/验收单/Story-RAG-S2-阶段2-强化fastpath-UAT.md`（产品语言 4 步 + ⚠️ 问句/探针分两条消息坑已进模板）
542-- ⏳ **三个待用户决策**（数据已备齐, 选择题形式问）: ① f06/h07 死档（建议 B 移 shadow 升 version）② f04 扩池（数据: 收益仅 file 级、grade3 不达、+31% 延迟 — 建议 backlog 等 chunk 侧补强）③ [!note] STRIP（数据: 零误伤 — 建议维持现状）
543:git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
544-diff --git a/backend/scripts/census_dead_letter_episodes.py b/backend/scripts/census_dead_letter_episodes.py
545-index 3ea39acb..6f264b74 100644
546---- a/backend/scripts/census_dead_letter_episodes.py
547-+++ b/backend/scripts/census_dead_letter_episodes.py
548-@@ -1,323 +1,356 @@
549- #!/usr/bin/env python3
550- """CARD-G4-9: dead-letter episodes 只读 census 分诊脚本。
551- 
552: BATCH-2026-08-28-第五批 / CARD-G4-9（G4-10 replay 的交接台账生成器）。
553- 
554- 只读契约（grep 可自证 + 运行时守卫）:
555-   - 无 --apply / 无任何写回、重放、删除路径；
556-   - 不 import neo4j / graphiti / app.*（纯 stdlib），不建立任何数据库/网络连接，
557-     唯一的 sqlite 访问经 URI ``mode=ro`` 只读打开 qa_metrics.db；
558-   - 唯一写出口是 --out 台账 JSON，写前双重碰撞守卫：resolve() 路径比较 +
559-     **文件身份 (st_dev, st_ino) 比较**，与 --dlq/--compare/--qa-metrics-db
560:     任一输入重合即 exit 2，防 "w" 截断输入（round-1 BLOCKER-1 + round-2
561-     hardlink / 大小写别名绕过整改）。
562- 
563: 快照原子性（Codex round-1 BLOCKER-2 整改）:
564-   - DLQ 文件只读一次（bytes），头部 sha256/line_count 与逐条 records 全部
565-     派生自同一份内存字节 —— 台账头部声明的 sha 即 records 所来自的 exact bytes。
566- 
567: 判定 fail-closed（Codex round-1 HIGH-1/2/3 整改）:
568-   - inline 三态: full_verified 要求 sha 对账通过 **且** len(body)==声明长度;
569-     truncated_prefix 要求声明 sha 为格式合法的 64-hex **且** len(body)==200
570-     且声明长度>200; 其余一律 anomaly。anomaly 不落 approximate —— 裁
571-     unrecoverable 并显式给 anomaly basis（不谎称"截断前缀"）。
--
578-     前缀），否则记 attribution_conflict、拒绝采信任何 transcript；
579-     transcript glob 命中必须**恰好 1 个常规文件**才算归因成功，多命中记
580-     ambiguous 同样拒绝采信；transcripts 根**不存在或不可读/不可遍历**
581-     （chmod 000）时整体 exit 2（拒绝在源不可见时产出 unrecoverable 假象）；
582:     glob 结果拒绝 symlink 条目与逃逸到根外的目标（round-2 HIGH-3 整改）。
583-   - DLQ 坏 JSON 行不再炸掉全量: 逐行捕获，class=unparseable 保留 line_no
584-     进台账（分诊工具不能被单行毒药拒诊）。
585-   - episode_body_full 若在盘（DEAD_LETTER_STORE_FULL_BODY 开启时生产可写):
586-     重算 sha **且长度**双门对账通过才按 byte_exact 采信，且 anomaly 记录
587:     不得经此分支翻案（round-1 MEDIUM-1 + round-2 HIGH-1 整改）。
588- 
589- 逐条产出（G4-10 消费契约）:
590-   - stable_key: {line_no, sha256_prefix(16 hex), request_id}。语义 =
591-     **冻结快照内的 occurrence key**（台账头部 dlq_file.sha256 即快照指纹；
592-     line_no 在该快照内已唯一，另两列为冗余对账/诊断维度）——不是跨文件
593-     重排或语义幂等键，G4-10 消费前先 diff 头部 sha。
594-   - reference_time 逐条透传 + duplicate_clusters 段（同 name+sha+group 的
595:     语义重复簇），G4-10 重放去重策略依据（Codex round-1 MEDIUM-2 整改）。
596-   - 隐私: transcript_paths 含本机用户名与 session UUID，台账为 private-only
597:     工件，禁止外发（Codex round-1 MEDIUM-3；仓库为私有仓，纪律=不 push 公网）。
598- """
599- 
600- from __future__ import annotations
601- 
--
624- 
625-+def _path_is_within(target: str, root: str) -> bool:
626-+    """target 是否落在 root 目录内 —— 逐级向上比较 **inode 身份**。
627-+
628:+    round-7 BLOCKER 整改: 不能用路径字符串前缀判断 —— 大小写不敏感卷上
629-+    ``/Users/x`` 与 ``/users/x`` 的 realpath 字符串不同但 samefile=True，
630-+    prefix guard 会漏。本实现从 target 逐级取父目录，只要任一级与 root 同
631-+    (st_dev, st_ino) 即判定在其内；target 尚不存在时上溯到存在的祖先。
632-+    """
--
660- def _split_jsonl_lines(raw: bytes) -> list[tuple[str, str | None]]:
661-     """按 JSONL 规范只以 LF 分帧，返回 [(line_text, decode_error_or_None)]。
662- 
663-     - 不用 splitlines(): U+2028/U+2029/裸 CR 会误分行（round-3）。
664:     - 逐行 **strict** decode（round-4 MEDIUM 整改）: errors="replace" 会把非法
665-       UTF-8 静默改写成合法对象，让坏字节冒充有效记录。解码失败的行带错误信息
666-       返回，由调用方归入 unparseable。
667-     """
668-     had_trailing_lf = raw.endswith(b"\n")
--
719- 
720- def full_body_verified(rec: dict) -> bool:
721-     """episode_body_full 在盘且 sha **与长度**双门对账通过（生产 opt-in 字段，当前 live 0 条）。
722- 
723:     round-2 HIGH-1 整改: 原实现只核 sha，声明长度矛盾的记录（如 body="abc"
724-     但 episode_body_length=999）仍被判 byte_exact —— 与 inline 侧同门收紧。
725-     """
726-     full = rec.get("episode_body_full")
727-     declared_sha = rec.get("episode_body_sha256", "")
--
752- 
753- def resolve_group_attribution(tokens: list[str], transcripts_dir: Path) -> dict:
754-     """组级归因，fail-closed。
755- 
756:     round-5 BLOCKER① 整改: **先扫描后判定**。原实现在 token 冲突/无 token 时
757-     扫描前早退，导致这些候选从未进入 all_candidate_paths → 不进 --out 保护集
758-     → 可被无竞态截断。现无条件对每个 token 扫描收集候选（保护集所需），
759-     再做冲突/唯一性判定。
760-     """
--
803-                     unreadable.append(candidate)
804-                     continue
805--                real = os.path.realpath(candidate)
806--                if not real.startswith(root_prefix):
807:-                    continue  # 目录 symlink 逃逸
808-+                if not _path_is_within(candidate, root_str):
809:+                    continue  # 目录 symlink 逃逸（inode 身份判定）
810-                 for t in matched:
811-                     per_token[t].append(candidate)
812-     result["all_candidate_paths"] = sorted(set(all_candidates))
813- 
814-     if not uniq:
815:         # 无 token: 未做任何归因扫描 —— 不是"确认无源"（round-5 MEDIUM 整改）
816-         result["attribution_conflict"] = True
817-         result["no_token"] = True
818-         return result
819- 
--
824-         return result
825-     result["session_token"] = longest
826- 
827-     if walk_errors:
828:         result["scan_errors"] = walk_errors[:5]
829-         result["attribution_conflict"] = True
830-         return result
831-     if stat_failures:
832-         result["stat_failures"] = stat_failures[:5]
--
849- 
850- def probe_qa_metrics(db_path: Path, error_types: list[str]) -> tuple[dict, tuple[int, int] | None]:
851-     """只读核销 qa_metrics.db（URI mode=ro，无写路径）。返回 (结果, 实际身份)。
852- 
853:     round-5 BLOCKER②/MEDIUM 整改: 原实现按路径 stat 取身份、SQLite 稍后按路径
854-     重新打开 —— 两者可能不是同一对象，且无 regular-file/nonblocking 门（FIFO
855:     会阻塞）。现: fd 打开取 fstat 身份 + S_ISREG 门 → SQLite 打开 → 复核路径
856-     身份仍等于该身份，不等即拒绝（不采信被换入的对象）。
857-     """
858-     result: dict = {"db_path": str(db_path), "opened_readonly": False}
859-     if not db_path.exists():
--
863-         fd = os.open(db_path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
864-     except OSError as e:
865-         result["verdict"] = f"open_refused: {e}"
866-         return result, None
867:     # round-6 BLOCKER② 整改: 验证 fd **保持打开**直到 SQLite 连接建立并复核完毕
868:     # —— 原实现验证后即关闭，SQLite 按路径重开可被 A→B→A 的 ABA 骗过。
869-     conn = None
870-     try:
871-         st = os.fstat(fd)
872-         if not stat.S_ISREG(st.st_mode):
--
913- 
914- def snapshot_file(path: Path) -> tuple[bytes, dict, tuple[int, int]]:
915-     """一次性读全量 bytes；sha/行数/身份全部派生自**同一个 fd**。
916- 
917:     round-4 BLOCKER② 整改: 原实现按路径 stat 采集保护身份、稍后才按路径读取，
918-     两步之间对象可被换掉（源侧 TOCTOU）。现改为打开一次 fd → fstat 取身份 →
919-     从该 fd 读全量，返回的 (st_dev, st_ino) 即**实际被读取对象**的身份。
920-     """
921-     fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
--
992-             f"transcripts 根目录不存在/不可见: {transcripts_dir} —— 拒绝在源不可见时裁定可恢复性（fail-closed）",
993-             file=sys.stderr,
994-         )
995-         return 2
996:     # round-2 HIGH-3 整改: 存在但不可读/不可遍历的根（chmod 000）此前 exit 0
997-     # 并把全部记录假判 unrecoverable —— 同样 fail-closed 拒诊。
998-     if not os.access(transcripts_dir, os.R_OK | os.X_OK):
999-         print(
1000-             f"transcripts 根目录不可读/不可遍历: {transcripts_dir} —— 拒绝在源不可见时裁定可恢复性（fail-closed）",
--
1002-         )
1003-         return 2
1004- 
1005-     protected_ids: set[tuple[int, int]] = set()
1006:     # round-6 BLOCKER①② 架构整改: inode 保护集依赖**枚举完整性**（不可列举的
1007-     # 子目录、ABA 换 inode 都能让某个真实源不进集合）。故增加**不依赖枚举**的
1008-     # 路径层防御：--out 的 realpath 不得落在 transcripts 根内、不得等于任一
1009-     # 输入路径。路径层 + inode 层双保险，任一命中即拒绝。
1010-     if args.out:
1011--        out_real = os.path.realpath(args.out)
1012--        tr_real = os.path.realpath(args.transcripts_dir)
1013--        tr_prefix = tr_real if tr_real.endswith(os.sep) else tr_real + os.sep
1014--        if out_real == tr_real or out_real.startswith(tr_prefix):
1015:+        # round-7 BLOCKER 整改: 用 **inode 身份逐级比较**（_path_is_within），
1016-+        # 不用路径字符串前缀 —— normcase 在 POSIX 上是恒等函数，大小写不敏感
1017-+        # 卷上的别名根（/Users vs /users）realpath 字符串不同但 samefile=True。
1018-+        if _path_is_within(args.out, args.transcripts_dir):
1019-             print(
--
1030-+        if any(_same_file(args.out, ip) for ip in input_paths):
1031-+            print(f"--out 与输入文件为同一对象（inode 比较），拒绝写出: {args.out}", file=sys.stderr)
1032-             return 2
1033- 
1034:     # --out 碰撞守卫（写前）。round-2 BLOCKER-1 整改: 比较**文件身份**
1035-     # (st_dev, st_ino) 而非 resolve() 字符串 —— 后者对 hardlink 与
1036-     # 大小写不敏感文件系统上的 case-only 别名均失效（Codex 实测截断输入）。
1037-     if args.out:
1038-         out_path = Path(args.out)
--
1040-         if args.qa_metrics_db:
1041-             protected_paths.append(Path(args.qa_metrics_db))
1042-         for candidate in protected_paths:
1043-             try:
1044:                 cst = candidate.stat()  # 跟随 symlink: 保护的是最终目标身份
1045-                 protected_ids.add((cst.st_dev, cst.st_ino))
1046-             except OSError:
1047-                 # round-4 整改: stat 失败不再静默吞 —— 无法确认身份即 fail-closed
1048-                 print(f"输入文件无法 stat，拒绝继续（无法建立完整保护集）: {candidate}", file=sys.stderr)
--
1064-                     file=sys.stderr,
1065-                 )
1066-                 return 2
1067- 
1068:     # BLOCKER-2 整改: 单次读取，records 与头部描述共享同一份 exact bytes
1069-     try:
1070-         raw_bytes, dlq_info, dlq_identity = snapshot_file(dlq_path)
1071-     except OSError as e:
1072-         print(f"DLQ 无法安全读取: {dlq_path} ({e})", file=sys.stderr)
--
1144-                     "no_token"
1145-                     if sess.get("no_token")
1146-                     else "token_conflict"
1147-                     if sess.get("token_conflict")
1148:                     else "scan_errors"
1149:                     if sess.get("scan_errors")
1150-                     else "stat_failures"
1151-                     if sess.get("stat_failures")
1152-                     else "unreadable_candidates"
1153-                     if sess.get("unreadable_candidates")
--
1227-         "qa_metrics_probe": qa_probe,
1228-         "records": ledger_records,
1229-     }
1230- 
1231:     # round-3 BLOCKER-1 绕过① 整改: 归因到的 transcript 是恢复源，
1232-     # --out 指向它同样会截断。写出前并入保护集（此时归因已完成）。
1233-+    # round-7 整改: 扫描受阻 ⇒ 保护集必然不完整（隐藏目录内的源看不见）。
1234-+    # 仅在台账标 unverifiable 不够 —— 直接拒绝写出，避免在保护集残缺时落盘。
1235-+    scan_blocked = [
1236:+        (k, v.get("scan_errors") or v.get("stat_failures"))
1237-+        for k, v in group_attribution.items()
1238:+        if v.get("scan_errors") or v.get("stat_failures")
1239-+    ]
1240-+    if scan_blocked and args.out:
1241-+        print(
1242-+            f"transcripts 扫描受阻（{len(scan_blocked)} 组），保护集不完整，拒绝写出台账；首例: {scan_blocked[0][1]}",
--
1274-         out_json = json.dumps(ledger, ensure_ascii=True, indent=1)
1275-     if args.out:
1276--        # round-3 整改: 消除 check-then-open TOCTOU。先以 O_NOFOLLOW 打开且
1277--        # **不带 O_TRUNC**，对**实际 fd** fstat 校验 inode；只有校验通过才
1278:-        # ftruncate。检查与写入作用于同一 fd，检查后被换 symlink/hardlink 无效。
1279-+        # round-7 架构整改: 不再截断既有文件 —— 同目录 O_EXCL 新建临时文件 →
1280:+        # 写 → fsync → os.replace 原子替换。O_EXCL 保证目标是本进程新建的对象，
1281:+        # 因此"把 --out 换成指向恢复源的 hardlink / 父目录 symlink / 大小写别名"
1282-+        # 这一整类绕过全部失效（脚本从不 ftruncate 任何既有 inode）；同时消除
1283:+        # 崩溃/ENOSPC 留下部分台账的风险（round-7 MEDIUM）。
1284-+        out_path = Path(args.out)
1285:+        tmp_path = out_path.with_name(f".{out_path.name}.census-tmp-{os.getpid()}")
1286-         try:
1287--            fd = os.open(args.out, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
1288:+            tmp_fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
1289-         except OSError as e:
1290:-            print(f"--out 无法安全打开（symlink 或权限）: {args.out} ({e})", file=sys.stderr)
1291:+            print(f"临时台账文件无法新建（O_EXCL）: {tmp_path} ({e})", file=sys.stderr)
1292-             return 2
1293-         try:
1294--            st = os.fstat(fd)
1295:-            # round-4 MEDIUM 整改: 非常规文件（FIFO/设备/socket）拒绝
1296--            if not stat.S_ISREG(st.st_mode):
1297--                print(f"--out 不是常规文件（FIFO/设备/socket），拒绝写出: {args.out}", file=sys.stderr)
1298--                return 2
1299:-            # round-5 HIGH 整改: 碰撞检查必须**先于** fchmod —— 否则 --out 指向
1300--            # 受保护的 0644 输入时，会先把只读输入的权限改成 0600 再拒绝。
1301--            if (st.st_dev, st.st_ino) in protected_ids:
1302--                print(
1303--                    f"--out 打开后经 fstat 判定与输入文件同一 inode，拒绝写出（防截断）: {args.out}",
--
1309--                os.fchmod(fd, 0o600)
1310--            os.ftruncate(fd, 0)
1311--            with os.fdopen(fd, "w", encoding="utf-8", closefd=True) as f:
1312--                fd = -1  # 所有权移交 fdopen
1313:+            with os.fdopen(tmp_fd, "w", encoding="utf-8", closefd=False) as f:
1314-                 f.write(out_json + "\n")
1315--        finally:
1316--            if fd >= 0:
1317--                os.close(fd)
1318-+                f.flush()
1319:+                os.fsync(tmp_fd)
1320-+        except Exception as e:
1321:+            os.close(tmp_fd)
1322:+            os.unlink(tmp_path)
1323-+            print(f"台账写入失败，已清理临时文件: {e}", file=sys.stderr)
1324-+            return 2
1325:+        os.close(tmp_fd)
1326-+        # 原子替换。目标若是恢复源，路径层与 inode 层已在前面拒绝；此处 replace
1327:+        # 只作用于本进程新建的 tmp，不存在"截断别人的文件"这一步。
1328:+        os.replace(tmp_path, out_path)
1329-         print(f"台账已写入: {args.out}")
1330-     else:
1331-         print(out_json)
1332- 
--
1344-     sys.exit(main())
1345-     1	#!/usr/bin/env python3
1346-     2	"""CARD-G4-9: dead-letter episodes 只读 census 分诊脚本。
1347-     3	
1348:     4	BATCH-2026-08-28-第五批 / CARD-G4-9（G4-10 replay 的交接台账生成器）。
1349-     5	
1350-     6	只读契约（grep 可自证 + 运行时守卫）:
1351-     7	  - 无 --apply / 无任何写回、重放、删除路径；
1352-     8	  - 不 import neo4j / graphiti / app.*（纯 stdlib），不建立任何数据库/网络连接，
1353-     9	    唯一的 sqlite 访问经 URI ``mode=ro`` 只读打开 qa_metrics.db；
1354-    10	  - 唯一写出口是 --out 台账 JSON，写前双重碰撞守卫：resolve() 路径比较 +
1355-    11	    **文件身份 (st_dev, st_ino) 比较**，与 --dlq/--compare/--qa-metrics-db
1356:    12	    任一输入重合即 exit 2，防 "w" 截断输入（round-1 BLOCKER-1 + round-2
1357-    13	    hardlink / 大小写别名绕过整改）。
1358-    14	
1359:    15	快照原子性（Codex round-1 BLOCKER-2 整改）:
1360-    16	  - DLQ 文件只读一次（bytes），头部 sha256/line_count 与逐条 records 全部
1361-    17	    派生自同一份内存字节 —— 台账头部声明的 sha 即 records 所来自的 exact bytes。
1362-    18	
1363:    19	判定 fail-closed（Codex round-1 HIGH-1/2/3 整改）:
1364-    20	  - inline 三态: full_verified 要求 sha 对账通过 **且** len(body)==声明长度;
1365-    21	    truncated_prefix 要求声明 sha 为格式合法的 64-hex **且** len(body)==200
1366-    22	    且声明长度>200; 其余一律 anomaly。anomaly 不落 approximate —— 裁
1367-    23	    unrecoverable 并显式给 anomaly basis（不谎称"截断前缀"）。
--
1374-    30	    前缀），否则记 attribution_conflict、拒绝采信任何 transcript；
1375-    31	    transcript glob 命中必须**恰好 1 个常规文件**才算归因成功，多命中记
1376-    32	    ambiguous 同样拒绝采信；transcripts 根**不存在或不可读/不可遍历**
1377-    33	    （chmod 000）时整体 exit 2（拒绝在源不可见时产出 unrecoverable 假象）；
1378:    34	    glob 结果拒绝 symlink 条目与逃逸到根外的目标（round-2 HIGH-3 整改）。
1379-    35	  - DLQ 坏 JSON 行不再炸掉全量: 逐行捕获，class=unparseable 保留 line_no
1380-    36	    进台账（分诊工具不能被单行毒药拒诊）。
1381-    37	  - episode_body_full 若在盘（DEAD_LETTER_STORE_FULL_BODY 开启时生产可写):
1382-    38	    重算 sha **且长度**双门对账通过才按 byte_exact 采信，且 anomaly 记录
1383:    39	    不得经此分支翻案（round-1 MEDIUM-1 + round-2 HIGH-1 整改）。
1384-    40	
1385-    41	逐条产出（G4-10 消费契约）:
1386-    42	  - stable_key: {line_no, sha256_prefix(16 hex), request_id}。语义 =
1387-    43	    **冻结快照内的 occurrence key**（台账头部 dlq_file.sha256 即快照指纹；
1388-    44	    line_no 在该快照内已唯一，另两列为冗余对账/诊断维度）——不是跨文件
1389-    45	    重排或语义幂等键，G4-10 消费前先 diff 头部 sha。
1390-    46	  - reference_time 逐条透传 + duplicate_clusters 段（同 name+sha+group 的
1391:    47	    语义重复簇），G4-10 重放去重策略依据（Codex round-1 MEDIUM-2 整改）。
1392-    48	  - 隐私: transcript_paths 含本机用户名与 session UUID，台账为 private-only
1393:    49	    工件，禁止外发（Codex round-1 MEDIUM-3；仓库为私有仓，纪律=不 push 公网）。
1394-    50	"""
1395-    51	
1396-    52	from __future__ import annotations
1397-    53	
--
1420-    76	
1421-    77	def _path_is_within(target: str, root: str) -> bool:
1422-    78	    """target 是否落在 root 目录内 —— 逐级向上比较 **inode 身份**。
1423-    79	
1424:    80	    round-7 BLOCKER 整改: 不能用路径字符串前缀判断 —— 大小写不敏感卷上
1425-    81	    ``/Users/x`` 与 ``/users/x`` 的 realpath 字符串不同但 samefile=True，
1426-    82	    prefix guard 会漏。本实现从 target 逐级取父目录，只要任一级与 root 同
1427-    83	    (st_dev, st_ino) 即判定在其内；target 尚不存在时上溯到存在的祖先。
1428-    84	    """
--
1456-   112	def _split_jsonl_lines(raw: bytes) -> list[tuple[str, str | None]]:
1457-   113	    """按 JSONL 规范只以 LF 分帧，返回 [(line_text, decode_error_or_None)]。
1458-   114	
1459-   115	    - 不用 splitlines(): U+2028/U+2029/裸 CR 会误分行（round-3）。
1460:   116	    - 逐行 **strict** decode（round-4 MEDIUM 整改）: errors="replace" 会把非法
1461-   117	      UTF-8 静默改写成合法对象，让坏字节冒充有效记录。解码失败的行带错误信息
1462-   118	      返回，由调用方归入 unparseable。
1463-   119	    """
1464-   120	    had_trailing_lf = raw.endswith(b"\n")
--
1515-   171	
1516-   172	def full_body_verified(rec: dict) -> bool:
1517-   173	    """episode_body_full 在盘且 sha **与长度**双门对账通过（生产 opt-in 字段，当前 live 0 条）。
1518-   174	
1519:   175	    round-2 HIGH-1 整改: 原实现只核 sha，声明长度矛盾的记录（如 body="abc"
1520-   176	    但 episode_body_length=999）仍被判 byte_exact —— 与 inline 侧同门收紧。
1521-   177	    """
1522-   178	    full = rec.get("episode_body_full")
1523-   179	    declared_sha = rec.get("episode_body_sha256", "")
--
1548-   204	
1549-   205	def resolve_group_attribution(tokens: list[str], transcripts_dir: Path) -> dict:
1550-   206	    """组级归因，fail-closed。
1551-   207	
1552:   208	    round-5 BLOCKER① 整改: **先扫描后判定**。原实现在 token 冲突/无 token 时
1553-   209	    扫描前早退，导致这些候选从未进入 all_candidate_paths → 不进 --out 保护集
1554-   210	    → 可被无竞态截断。现无条件对每个 token 扫描收集候选（保护集所需），
1555-   211	    再做冲突/唯一性判定。
1556-   212	    """
--
1596-   252	                if not os.access(candidate, os.R_OK):
1597-   253	                    unreadable.append(candidate)
1598-   254	                    continue
1599-   255	                if not _path_is_within(candidate, root_str):
1600:   256	                    continue  # 目录 symlink 逃逸（inode 身份判定）
1601-   257	                for t in matched:
1602-   258	                    per_token[t].append(candidate)
1603-   259	    result["all_candidate_paths"] = sorted(set(all_candidates))
1604-   260	
1605-   261	    if not uniq:
1606:   262	        # 无 token: 未做任何归因扫描 —— 不是"确认无源"（round-5 MEDIUM 整改）
1607-   263	        result["attribution_conflict"] = True
1608-   264	        result["no_token"] = True
1609-   265	        return result
1610-   266	
--
1615-   271	        return result
1616-   272	    result["session_token"] = longest
1617-   273	
1618-   274	    if walk_errors:
1619:   275	        result["scan_errors"] = walk_errors[:5]
1620-   276	        result["attribution_conflict"] = True
1621-   277	        return result
1622-   278	    if stat_failures:
1623-   279	        result["stat_failures"] = stat_failures[:5]
--
1640-   296	
1641-   297	def probe_qa_metrics(db_path: Path, error_types: list[str]) -> tuple[dict, tuple[int, int] | None]:
1642-   298	    """只读核销 qa_metrics.db（URI mode=ro，无写路径）。返回 (结果, 实际身份)。
1643-   299	
1644:   300	    round-5 BLOCKER②/MEDIUM 整改: 原实现按路径 stat 取身份、SQLite 稍后按路径
1645-   301	    重新打开 —— 两者可能不是同一对象，且无 regular-file/nonblocking 门（FIFO
1646:   302	    会阻塞）。现: fd 打开取 fstat 身份 + S_ISREG 门 → SQLite 打开 → 复核路径
1647-   303	    身份仍等于该身份，不等即拒绝（不采信被换入的对象）。
1648-   304	    """
1649-   305	    result: dict = {"db_path": str(db_path), "opened_readonly": False}
1650-   306	    if not db_path.exists():
--
1654-   310	        fd = os.open(db_path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
1655-   311	    except OSError as e:
1656-   312	        result["verdict"] = f"open_refused: {e}"
1657-   313	        return result, None
1658:   314	    # round-6 BLOCKER② 整改: 验证 fd **保持打开**直到 SQLite 连接建立并复核完毕
1659:   315	    # —— 原实现验证后即关闭，SQLite 按路径重开可被 A→B→A 的 ABA 骗过。
1660-   316	    conn = None
1661-   317	    try:
1662-   318	        st = os.fstat(fd)
1663-   319	        if not stat.S_ISREG(st.st_mode):
--
1706-   362	
1707-   363	def snapshot_file(path: Path) -> tuple[bytes, dict, tuple[int, int]]:
1708-   364	    """一次性读全量 bytes；sha/行数/身份全部派生自**同一个 fd**。
1709-   365	
1710:   366	    round-4 BLOCKER② 整改: 原实现按路径 stat 采集保护身份、稍后才按路径读取，
1711-   367	    两步之间对象可被换掉（源侧 TOCTOU）。现改为打开一次 fd → fstat 取身份 →
1712-   368	    从该 fd 读全量，返回的 (st_dev, st_ino) 即**实际被读取对象**的身份。
1713-   369	    """
1714-   370	    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
--
1785-   441	            f"transcripts 根目录不存在/不可见: {transcripts_dir} —— 拒绝在源不可见时裁定可恢复性（fail-closed）",
1786-   442	            file=sys.stderr,
1787-   443	        )
1788-   444	        return 2
1789:   445	    # round-2 HIGH-3 整改: 存在但不可读/不可遍历的根（chmod 000）此前 exit 0
1790-   446	    # 并把全部记录假判 unrecoverable —— 同样 fail-closed 拒诊。
1791-   447	    if not os.access(transcripts_dir, os.R_OK | os.X_OK):
1792-   448	        print(
1793-   449	            f"transcripts 根目录不可读/不可遍历: {transcripts_dir} —— 拒绝在源不可见时裁定可恢复性（fail-closed）",
--
1795-   451	        )
1796-   452	        return 2
1797-   453	
1798-   454	    protected_ids: set[tuple[int, int]] = set()
1799:   455	    # round-6 BLOCKER①② 架构整改: inode 保护集依赖**枚举完整性**（不可列举的
1800-   456	    # 子目录、ABA 换 inode 都能让某个真实源不进集合）。故增加**不依赖枚举**的
1801-   457	    # 路径层防御：--out 的 realpath 不得落在 transcripts 根内、不得等于任一
1802-   458	    # 输入路径。路径层 + inode 层双保险，任一命中即拒绝。
1803-   459	    if args.out:
1804:   460	        # round-7 BLOCKER 整改: 用 **inode 身份逐级比较**（_path_is_within），
1805-   461	        # 不用路径字符串前缀 —— normcase 在 POSIX 上是恒等函数，大小写不敏感
1806-   462	        # 卷上的别名根（/Users vs /users）realpath 字符串不同但 samefile=True。
1807-   463	        if _path_is_within(args.out, args.transcripts_dir):
1808-   464	            print(
--
1814-   470	        if any(_same_file(args.out, ip) for ip in input_paths):
1815-   471	            print(f"--out 与输入文件为同一对象（inode 比较），拒绝写出: {args.out}", file=sys.stderr)
1816-   472	            return 2
1817-   473	
1818:   474	    # --out 碰撞守卫（写前）。round-2 BLOCKER-1 整改: 比较**文件身份**
1819-   475	    # (st_dev, st_ino) 而非 resolve() 字符串 —— 后者对 hardlink 与
1820-   476	    # 大小写不敏感文件系统上的 case-only 别名均失效（Codex 实测截断输入）。
1821-   477	    if args.out:
1822-   478	        out_path = Path(args.out)
--
1824-   480	        if args.qa_metrics_db:
1825-   481	            protected_paths.append(Path(args.qa_metrics_db))
1826-   482	        for candidate in protected_paths:
1827-   483	            try:
1828:   484	                cst = candidate.stat()  # 跟随 symlink: 保护的是最终目标身份
1829-   485	                protected_ids.add((cst.st_dev, cst.st_ino))
1830-   486	            except OSError:
1831-   487	                # round-4 整改: stat 失败不再静默吞 —— 无法确认身份即 fail-closed
1832-   488	                print(f"输入文件无法 stat，拒绝继续（无法建立完整保护集）: {candidate}", file=sys.stderr)
--
1848-   504	                    file=sys.stderr,
1849-   505	                )
1850-   506	                return 2
1851-   507	
1852:   508	    # BLOCKER-2 整改: 单次读取，records 与头部描述共享同一份 exact bytes
1853-   509	    try:
1854-   510	        raw_bytes, dlq_info, dlq_identity = snapshot_file(dlq_path)
1855-   511	    except OSError as e:
1856-   512	        print(f"DLQ 无法安全读取: {dlq_path} ({e})", file=sys.stderr)
--
1924-   580	        elif state != "anomaly" and full_body_verified(rec):
1925-   581	            recover = "byte_exact"
1926-   582	            basis = "episode_body_full 在盘且 sha256+长度双门对账通过（DEAD_LETTER_STORE_FULL_BODY 生产 opt-in 字段）"
1927-   583	        elif sess["attribution_conflict"]:
1928:   584	            # round-5 HIGH 整改: 可见性判定**优先于** anomaly —— 源看不见时
1929-   585	            # 无论 inline 是什么状态，都不能断言"不可恢复"。
1930-   586	            recover = "unverifiable"
1931-   587	            if sess.get("no_token"):
1932-   588	                why = "记录名未携带 session token，未做任何归因扫描"
1933-   589	            elif sess.get("token_conflict"):
1934-   590	                why = "同组多 token 前缀冲突"
1935:   591	            elif sess.get("scan_errors"):
1936-   592	                why = "扫描遍历受阻（不可读子树）"
1937-   593	            elif sess.get("stat_failures"):
1938-   594	                why = "候选 stat 失败"
1939-   595	            elif sess.get("unreadable_candidates"):
--
1994-   650	                    "no_token"
1995-   651	                    if sess.get("no_token")
1996-   652	                    else "token_conflict"
1997-   653	                    if sess.get("token_conflict")
1998:   654	                    else "scan_errors"
1999:   655	                    if sess.get("scan_errors")
2000-   656	                    else "stat_failures"
2001-   657	                    if sess.get("stat_failures")
2002-   658	                    else "unreadable_candidates"
2003-   659	                    if sess.get("unreadable_candidates")
--
2077-   733	        "qa_metrics_probe": qa_probe,
2078-   734	        "records": ledger_records,
2079-   735	    }
2080-   736	
2081:   737	    # round-3 BLOCKER-1 绕过① 整改: 归因到的 transcript 是恢复源，
2082-   738	    # --out 指向它同样会截断。写出前并入保护集（此时归因已完成）。
2083-   739	    # round-7 整改: 扫描受阻 ⇒ 保护集必然不完整（隐藏目录内的源看不见）。
2084-   740	    # 仅在台账标 unverifiable 不够 —— 直接拒绝写出，避免在保护集残缺时落盘。
2085-   741	    scan_blocked = [
2086:   742	        (k, v.get("scan_errors") or v.get("stat_failures"))
2087-   743	        for k, v in group_attribution.items()
2088:   744	        if v.get("scan_errors") or v.get("stat_failures")
2089-   745	    ]
2090-   746	    if scan_blocked and args.out:
2091-   747	        print(
2092-   748	            f"transcripts 扫描受阻（{len(scan_blocked)} 组），保护集不完整，拒绝写出台账；首例: {scan_blocked[0][1]}",
--
2113-     820 backend/scripts/census_dead_letter_episodes.py
2114-     1	#!/usr/bin/env python3
2115-     2	"""CARD-G4-9: dead-letter episodes 只读 census 分诊脚本。
2116-     3	
2117:     4	BATCH-2026-08-28-第五批 / CARD-G4-9（G4-10 replay 的交接台账生成器）。
2118-     5	
2119-     6	只读契约（grep 可自证 + 运行时守卫）:
2120-     7	  - 无 --apply / 无任何写回、重放、删除路径；
2121-     8	  - 不 import neo4j / graphiti / app.*（纯 stdlib），不建立任何数据库/网络连接，
2122-     9	    唯一的 sqlite 访问经 URI ``mode=ro`` 只读打开 qa_metrics.db；
2123-    10	  - 唯一写出口是 --out 台账 JSON，写前双重碰撞守卫：resolve() 路径比较 +
2124-    11	    **文件身份 (st_dev, st_ino) 比较**，与 --dlq/--compare/--qa-metrics-db
2125:    12	    任一输入重合即 exit 2，防 "w" 截断输入（round-1 BLOCKER-1 + round-2
2126-    13	    hardlink / 大小写别名绕过整改）。
2127-    14	
2128:    15	快照原子性（Codex round-1 BLOCKER-2 整改）:
2129-    16	  - DLQ 文件只读一次（bytes），头部 sha256/line_count 与逐条 records 全部
2130-    17	    派生自同一份内存字节 —— 台账头部声明的 sha 即 records 所来自的 exact bytes。
2131-    18	
2132:    19	判定 fail-closed（Codex round-1 HIGH-1/2/3 整改）:
2133-    20	  - inline 三态: full_verified 要求 sha 对账通过 **且** len(body)==声明长度;
2134-    21	    truncated_prefix 要求声明 sha 为格式合法的 64-hex **且** len(body)==200
2135-    22	    且声明长度>200; 其余一律 anomaly。anomaly 不落 approximate —— 裁
2136-    23	    unrecoverable 并显式给 anomaly basis（不谎称"截断前缀"）。
--
2143-    30	    前缀），否则记 attribution_conflict、拒绝采信任何 transcript；
2144-    31	    transcript glob 命中必须**恰好 1 个常规文件**才算归因成功，多命中记
2145-    32	    ambiguous 同样拒绝采信；transcripts 根**不存在或不可读/不可遍历**
2146-    33	    （chmod 000）时整体 exit 2（拒绝在源不可见时产出 unrecoverable 假象）；
2147:    34	    glob 结果拒绝 symlink 条目与逃逸到根外的目标（round-2 HIGH-3 整改）。
2148-    35	  - DLQ 坏 JSON 行不再炸掉全量: 逐行捕获，class=unparseable 保留 line_no
2149-    36	    进台账（分诊工具不能被单行毒药拒诊）。
2150-    37	  - episode_body_full 若在盘（DEAD_LETTER_STORE_FULL_BODY 开启时生产可写):
2151-    38	    重算 sha **且长度**双门对账通过才按 byte_exact 采信，且 anomaly 记录
2152:    39	    不得经此分支翻案（round-1 MEDIUM-1 + round-2 HIGH-1 整改）。
2153-    40	
2154-    41	逐条产出（G4-10 消费契约）:
2155-    42	  - stable_key: {line_no, sha256_prefix(16 hex), request_id}。语义 =
2156-    43	    **冻结快照内的 occurrence key**（台账头部 dlq_file.sha256 即快照指纹；
2157-    44	    line_no 在该快照内已唯一，另两列为冗余对账/诊断维度）——不是跨文件
2158-    45	    重排或语义幂等键，G4-10 消费前先 diff 头部 sha。
2159-    46	  - reference_time 逐条透传 + duplicate_clusters 段（同 name+sha+group 的
2160:    47	    语义重复簇），G4-10 重放去重策略依据（Codex round-1 MEDIUM-2 整改）。
2161-    48	  - 隐私: transcript_paths 含本机用户名与 session UUID，台账为 private-only
2162:    49	    工件，禁止外发（Codex round-1 MEDIUM-3；仓库为私有仓，纪律=不 push 公网）。
2163-    50	"""
2164-    51	
2165-    52	from __future__ import annotations
2166-    53	
--
2189-    76	
2190-    77	def _path_is_within(target: str, root: str) -> bool:
2191-    78	    """target 是否落在 root 目录内 —— 逐级向上比较 **inode 身份**。
2192-    79	
2193:    80	    round-7 BLOCKER 整改: 不能用路径字符串前缀判断 —— 大小写不敏感卷上
2194-    81	    ``/Users/x`` 与 ``/users/x`` 的 realpath 字符串不同但 samefile=True，
2195-    82	    prefix guard 会漏。本实现从 target 逐级取父目录，只要任一级与 root 同
2196-    83	    (st_dev, st_ino) 即判定在其内；target 尚不存在时上溯到存在的祖先。
2197-    84	    """
--
2225-   112	def _split_jsonl_lines(raw: bytes) -> list[tuple[str, str | None]]:
2226-   113	    """按 JSONL 规范只以 LF 分帧，返回 [(line_text, decode_error_or_None)]。
2227-   114	
2228-   115	    - 不用 splitlines(): U+2028/U+2029/裸 CR 会误分行（round-3）。
2229:   116	    - 逐行 **strict** decode（round-4 MEDIUM 整改）: errors="replace" 会把非法
2230-   117	      UTF-8 静默改写成合法对象，让坏字节冒充有效记录。解码失败的行带错误信息
2231-   118	      返回，由调用方归入 unparseable。
2232-   119	    """
2233-   120	    had_trailing_lf = raw.endswith(b"\n")
--
2284-   171	
2285-   172	def full_body_verified(rec: dict) -> bool:
2286-   173	    """episode_body_full 在盘且 sha **与长度**双门对账通过（生产 opt-in 字段，当前 live 0 条）。
2287-   174	
2288:   175	    round-2 HIGH-1 整改: 原实现只核 sha，声明长度矛盾的记录（如 body="abc"
2289-   176	    但 episode_body_length=999）仍被判 byte_exact —— 与 inline 侧同门收紧。
2290-   177	    """
2291-   178	    full = rec.get("episode_body_full")
2292-   179	    declared_sha = rec.get("episode_body_sha256", "")
--
2317-   204	
2318-   205	def resolve_group_attribution(tokens: list[str], transcripts_dir: Path) -> dict:
2319-   206	    """组级归因，fail-closed。
2320-   207	
2321:   208	    round-5 BLOCKER① 整改: **先扫描后判定**。原实现在 token 冲突/无 token 时
2322-   209	    扫描前早退，导致这些候选从未进入 all_candidate_paths → 不进 --out 保护集
2323-   210	    → 可被无竞态截断。现无条件对每个 token 扫描收集候选（保护集所需），
2324-   211	    再做冲突/唯一性判定。
2325-   212	    """
--
2366-   252	                if not os.access(candidate, os.R_OK):
2367-   253	                    unreadable.append(candidate)
2368-   254	                    continue
2369-   255	                if not _path_is_within(candidate, root_str):
2370:   256	                    continue  # 目录 symlink 逃逸（inode 身份判定）
2371-   257	                for t in matched:
2372-   258	                    per_token[t].append(candidate)
2373-   259	    result["all_candidate_paths"] = sorted(set(all_candidates))
2374-   260	
2375-   261	    if not uniq:
2376:   262	        # 无 token: 未做任何归因扫描 —— 不是"确认无源"（round-5 MEDIUM 整改）
2377-   263	        result["attribution_conflict"] = True
2378-   264	        result["no_token"] = True
2379-   265	        return result
2380-   266	
--
2385-   271	        return result
2386-   272	    result["session_token"] = longest
2387-   273	
2388-   274	    if walk_errors:
2389:   275	        result["scan_errors"] = walk_errors[:5]
2390-   276	        result["attribution_conflict"] = True
2391-   277	        return result
2392-   278	    if stat_failures:
2393-   279	        result["stat_failures"] = stat_failures[:5]
--
2410-   296	
2411-   297	def probe_qa_metrics(db_path: Path, error_types: list[str]) -> tuple[dict, tuple[int, int] | None]:
2412-   298	    """只读核销 qa_metrics.db（URI mode=ro，无写路径）。返回 (结果, 实际身份)。
2413-   299	
2414:   300	    round-5 BLOCKER②/MEDIUM 整改: 原实现按路径 stat 取身份、SQLite 稍后按路径
2415-   301	    重新打开 —— 两者可能不是同一对象，且无 regular-file/nonblocking 门（FIFO
2416:   302	    会阻塞）。现: fd 打开取 fstat 身份 + S_ISREG 门 → SQLite 打开 → 复核路径
2417-   303	    身份仍等于该身份，不等即拒绝（不采信被换入的对象）。
2418-   304	    """
2419-   305	    result: dict = {"db_path": str(db_path), "opened_readonly": False}
2420-   306	    if not db_path.exists():
--
2424-   310	        fd = os.open(db_path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
2425-   311	    except OSError as e:
2426-   312	        result["verdict"] = f"open_refused: {e}"
2427-   313	        return result, None
2428:   314	    # round-6 BLOCKER② 整改: 验证 fd **保持打开**直到 SQLite 连接建立并复核完毕
2429:   315	    # —— 原实现验证后即关闭，SQLite 按路径重开可被 A→B→A 的 ABA 骗过。
2430-   316	    conn = None
2431-   317	    try:
2432-   318	        st = os.fstat(fd)
2433-   319	        if not stat.S_ISREG(st.st_mode):
--
2476-   362	
2477-   363	def snapshot_file(path: Path) -> tuple[bytes, dict, tuple[int, int]]:
2478-   364	    """一次性读全量 bytes；sha/行数/身份全部派生自**同一个 fd**。
2479-   365	
2480:   366	    round-4 BLOCKER② 整改: 原实现按路径 stat 采集保护身份、稍后才按路径读取，
2481-   367	    两步之间对象可被换掉（源侧 TOCTOU）。现改为打开一次 fd → fstat 取身份 →
2482-   368	    从该 fd 读全量，返回的 (st_dev, st_ino) 即**实际被读取对象**的身份。
2483-   369	    """
2484-   370	    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
--
2525-   733	        "qa_metrics_probe": qa_probe,
2526-   734	        "records": ledger_records,
2527-   735	    }
2528-   736	
2529:   737	    # round-3 BLOCKER-1 绕过① 整改: 归因到的 transcript 是恢复源，
2530-   738	    # --out 指向它同样会截断。写出前并入保护集（此时归因已完成）。
2531-   739	    # round-7 整改: 扫描受阻 ⇒ 保护集必然不完整（隐藏目录内的源看不见）。
2532-   740	    # 仅在台账标 unverifiable 不够 —— 直接拒绝写出，避免在保护集残缺时落盘。
2533-   741	    scan_blocked = [
2534:   742	        (k, v.get("scan_errors") or v.get("stat_failures"))
2535-   743	        for k, v in group_attribution.items()
2536:   744	        if v.get("scan_errors") or v.get("stat_failures")
2537-   745	    ]
2538-   746	    if scan_blocked and args.out:
2539-   747	        print(
2540-   748	            f"transcripts 扫描受阻（{len(scan_blocked)} 组），保护集不完整，拒绝写出台账；首例: {scan_blocked[0][1]}",
--
2568-   776	        ledger["json_encoding_note"] = "ensure_ascii=True fallback: 某字段含无法 UTF-8 编码的字符（lone surrogate）"
2569-   777	        out_json = json.dumps(ledger, ensure_ascii=True, indent=1)
2570-   778	    if args.out:
2571-   779	        # round-7 架构整改: 不再截断既有文件 —— 同目录 O_EXCL 新建临时文件 →
2572:   780	        # 写 → fsync → os.replace 原子替换。O_EXCL 保证目标是本进程新建的对象，
2573:   781	        # 因此"把 --out 换成指向恢复源的 hardlink / 父目录 symlink / 大小写别名"
2574-   782	        # 这一整类绕过全部失效（脚本从不 ftruncate 任何既有 inode）；同时消除
2575:   783	        # 崩溃/ENOSPC 留下部分台账的风险（round-7 MEDIUM）。
2576-   784	        out_path = Path(args.out)
2577:   785	        tmp_path = out_path.with_name(f".{out_path.name}.census-tmp-{os.getpid()}")
2578-   786	        try:
2579:   787	            tmp_fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
2580-   788	        except OSError as e:
2581:   789	            print(f"临时台账文件无法新建（O_EXCL）: {tmp_path} ({e})", file=sys.stderr)
2582-   790	            return 2
2583-   791	        try:
2584:   792	            with os.fdopen(tmp_fd, "w", encoding="utf-8", closefd=False) as f:
2585-   793	                f.write(out_json + "\n")
2586-   794	                f.flush()
2587:   795	                os.fsync(tmp_fd)
2588-   796	        except Exception as e:
2589:   797	            os.close(tmp_fd)
2590:   798	            os.unlink(tmp_path)
2591-   799	            print(f"台账写入失败，已清理临时文件: {e}", file=sys.stderr)
2592-   800	            return 2
2593:   801	        os.close(tmp_fd)
2594-   802	        # 原子替换。目标若是恢复源，路径层与 inode 层已在前面拒绝；此处 replace
2595:   803	        # 只作用于本进程新建的 tmp，不存在"截断别人的文件"这一步。
2596:   804	        os.replace(tmp_path, out_path)
2597-   805	        print(f"台账已写入: {args.out}")
2598-   806	    else:
2599-   807	        print(out_json)
2600-   808	
--
2612-   820	    sys.exit(main())
2613-
2614-**Identifying os.replace error handling gaps**
2615-**Exposing os.replace hardlink race condition**
2616:**Revealing os.replace symlink swap risk**
2617:**Assessing os.replace symlink and hardlink risks**
2618-**Identifying race condition in os.replace overwrite**
2619-**Confirming attack requires directory write permission**
2620:**Analyzing symlink retargeting vulnerability**
2621:**Examining os.replace effects on symlinks and hardlinks**
2622-**Evaluating cross-device rename and mount effects**
2623-**Assessing file replace and permission handling**
2624-**Analyzing temp file races and concurrency issues**
2625:**Verifying symlink loop detection within root**
2626:**Verifying root symlink and mount point logic**
2627-**Analyzing bind mount alias effects on root containment**
2628-**Evaluating inode and device ID behavior on bind mounts**
2629-**Assessing inode protection during output writes**
2630-**Verifying final protected_ids usage before writing**
2631-exec
2632:/bin/zsh -lc "rg -n \"protected_ids|tmp_path|os\\.replace|ftruncate|open\\(\" backend/scripts/census_dead_letter_episodes.py
2633-git diff --no-ext-diff --unified=30 f389980c"'^ f389980c -- backend/scripts/census_dead_letter_episodes.py' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
2634- succeeded in 0ms:
2635-310:        fd = os.open(db_path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
2636-370:    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
--
2641-686:            protected_ids.add(cid)
2642-694:            protected_ids.add(qa_identity)  # 保护实际验证过的对象身份
2643-757:                protected_ids.add((tst.st_dev, tst.st_ino))
2644-766:                protected_ids.add((tst.st_dev, tst.st_ino))
2645:780:        # 写 → fsync → os.replace 原子替换。O_EXCL 保证目标是本进程新建的对象，
2646-782:        # 这一整类绕过全部失效（脚本从不 ftruncate 任何既有 inode）；同时消除
2647:785:        tmp_path = out_path.with_name(f".{out_path.name}.census-tmp-{os.getpid()}")
2648:787:            tmp_fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
2649:789:            print(f"临时台账文件无法新建（O_EXCL）: {tmp_path} ({e})", file=sys.stderr)
2650:792:            with os.fdopen(tmp_fd, "w", encoding="utf-8", closefd=False) as f:
2651:798:            os.unlink(tmp_path)
2652:804:        os.replace(tmp_path, out_path)
2653:git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
2654-diff --git a/backend/scripts/census_dead_letter_episodes.py b/backend/scripts/census_dead_letter_episodes.py
2655-index 3ea39acb..6f264b74 100644
2656---- a/backend/scripts/census_dead_letter_episodes.py
2657-+++ b/backend/scripts/census_dead_letter_episodes.py
2658:@@ -47,60 +47,95 @@ BATCH-2026-08-28-第五批 / CARD-G4-9（G4-10 replay 的交接台账生成器
2659:     语义重复簇），G4-10 重放去重策略依据（Codex round-1 MEDIUM-2 整改）。
2660-   - 隐私: transcript_paths 含本机用户名与 session UUID，台账为 private-only
2661:     工件，禁止外发（Codex round-1 MEDIUM-3；仓库为私有仓，纪律=不 push 公网）。
2662- """
2663- 
2664- from __future__ import annotations
2665- 
--
2688- 
2689-+def _path_is_within(target: str, root: str) -> bool:
2690-+    """target 是否落在 root 目录内 —— 逐级向上比较 **inode 身份**。
2691-+
2692:+    round-7 BLOCKER 整改: 不能用路径字符串前缀判断 —— 大小写不敏感卷上
2693-+    ``/Users/x`` 与 ``/users/x`` 的 realpath 字符串不同但 samefile=True，
2694-+    prefix guard 会漏。本实现从 target 逐级取父目录，只要任一级与 root 同
2695-+    (st_dev, st_ino) 即判定在其内；target 尚不存在时上溯到存在的祖先。
2696-+    """
--
2724- def _split_jsonl_lines(raw: bytes) -> list[tuple[str, str | None]]:
2725-     """按 JSONL 规范只以 LF 分帧，返回 [(line_text, decode_error_or_None)]。
2726- 
2727-     - 不用 splitlines(): U+2028/U+2029/裸 CR 会误分行（round-3）。
2728:     - 逐行 **strict** decode（round-4 MEDIUM 整改）: errors="replace" 会把非法
2729-       UTF-8 静默改写成合法对象，让坏字节冒充有效记录。解码失败的行带错误信息
2730-       返回，由调用方归入 unparseable。
2731-     """
2732-     had_trailing_lf = raw.endswith(b"\n")
--
2765- 
2766- def resolve_group_attribution(tokens: list[str], transcripts_dir: Path) -> dict:
2767-     """组级归因，fail-closed。
2768- 
2769:     round-5 BLOCKER① 整改: **先扫描后判定**。原实现在 token 冲突/无 token 时
2770-     扫描前早退，导致这些候选从未进入 all_candidate_paths → 不进 --out 保护集
2771-     → 可被无竞态截断。现无条件对每个 token 扫描收集候选（保护集所需），
2772-     再做冲突/唯一性判定。
2773-     """
--
2816-                     unreadable.append(candidate)
2817-                     continue
2818--                real = os.path.realpath(candidate)
2819--                if not real.startswith(root_prefix):
2820:-                    continue  # 目录 symlink 逃逸
2821-+                if not _path_is_within(candidate, root_str):
2822:+                    continue  # 目录 symlink 逃逸（inode 身份判定）
2823-                 for t in matched:
2824-                     per_token[t].append(candidate)
2825-     result["all_candidate_paths"] = sorted(set(all_candidates))
2826- 
2827-     if not uniq:
2828:         # 无 token: 未做任何归因扫描 —— 不是"确认无源"（round-5 MEDIUM 整改）
2829-         result["attribution_conflict"] = True
2830-         result["no_token"] = True
2831-         return result
2832- 
--
2837-         return result
2838-     result["session_token"] = longest
2839- 
2840-     if walk_errors:
2841:         result["scan_errors"] = walk_errors[:5]
2842-         result["attribution_conflict"] = True
2843-         return result
2844-     if stat_failures:
2845-         result["stat_failures"] = stat_failures[:5]
--
2865-             f"transcripts 根目录不存在/不可见: {transcripts_dir} —— 拒绝在源不可见时裁定可恢复性（fail-closed）",
2866-             file=sys.stderr,
2867-         )
2868-         return 2
2869:     # round-2 HIGH-3 整改: 存在但不可读/不可遍历的根（chmod 000）此前 exit 0
2870-     # 并把全部记录假判 unrecoverable —— 同样 fail-closed 拒诊。
2871-     if not os.access(transcripts_dir, os.R_OK | os.X_OK):
2872-         print(
2873-             f"transcripts 根目录不可读/不可遍历: {transcripts_dir} —— 拒绝在源不可见时裁定可恢复性（fail-closed）",
--
2875-         )
2876-         return 2
2877- 
2878-     protected_ids: set[tuple[int, int]] = set()
2879:     # round-6 BLOCKER①② 架构整改: inode 保护集依赖**枚举完整性**（不可列举的
2880-     # 子目录、ABA 换 inode 都能让某个真实源不进集合）。故增加**不依赖枚举**的
2881-     # 路径层防御：--out 的 realpath 不得落在 transcripts 根内、不得等于任一
2882-     # 输入路径。路径层 + inode 层双保险，任一命中即拒绝。
2883-     if args.out:
2884--        out_real = os.path.realpath(args.out)
2885--        tr_real = os.path.realpath(args.transcripts_dir)
2886--        tr_prefix = tr_real if tr_real.endswith(os.sep) else tr_real + os.sep
2887--        if out_real == tr_real or out_real.startswith(tr_prefix):
2888:+        # round-7 BLOCKER 整改: 用 **inode 身份逐级比较**（_path_is_within），
2889-+        # 不用路径字符串前缀 —— normcase 在 POSIX 上是恒等函数，大小写不敏感
2890-+        # 卷上的别名根（/Users vs /users）realpath 字符串不同但 samefile=True。
2891-+        if _path_is_within(args.out, args.transcripts_dir):
2892-             print(
--
2903-+        if any(_same_file(args.out, ip) for ip in input_paths):
2904-+            print(f"--out 与输入文件为同一对象（inode 比较），拒绝写出: {args.out}", file=sys.stderr)
2905-             return 2
2906- 
2907:     # --out 碰撞守卫（写前）。round-2 BLOCKER-1 整改: 比较**文件身份**
2908-     # (st_dev, st_ino) 而非 resolve() 字符串 —— 后者对 hardlink 与
2909-     # 大小写不敏感文件系统上的 case-only 别名均失效（Codex 实测截断输入）。
2910-     if args.out:
2911-         out_path = Path(args.out)
--
2913-         if args.qa_metrics_db:
2914-             protected_paths.append(Path(args.qa_metrics_db))
2915-         for candidate in protected_paths:
2916-             try:
2917:                 cst = candidate.stat()  # 跟随 symlink: 保护的是最终目标身份
2918-                 protected_ids.add((cst.st_dev, cst.st_ino))
2919-             except OSError:
2920-                 # round-4 整改: stat 失败不再静默吞 —— 无法确认身份即 fail-closed
2921-                 print(f"输入文件无法 stat，拒绝继续（无法建立完整保护集）: {candidate}", file=sys.stderr)
--
2960-         "qa_metrics_probe": qa_probe,
2961-         "records": ledger_records,
2962-     }
2963- 
2964:     # round-3 BLOCKER-1 绕过① 整改: 归因到的 transcript 是恢复源，
2965-     # --out 指向它同样会截断。写出前并入保护集（此时归因已完成）。
2966-+    # round-7 整改: 扫描受阻 ⇒ 保护集必然不完整（隐藏目录内的源看不见）。
2967-+    # 仅在台账标 unverifiable 不够 —— 直接拒绝写出，避免在保护集残缺时落盘。
2968-+    scan_blocked = [
2969:+        (k, v.get("scan_errors") or v.get("stat_failures"))
2970-+        for k, v in group_attribution.items()
2971:+        if v.get("scan_errors") or v.get("stat_failures")
2972-+    ]
2973-+    if scan_blocked and args.out:
2974-+        print(
2975-+            f"transcripts 扫描受阻（{len(scan_blocked)} 组），保护集不完整，拒绝写出台账；首例: {scan_blocked[0][1]}",
--
3007-         out_json = json.dumps(ledger, ensure_ascii=True, indent=1)
3008-     if args.out:
3009--        # round-3 整改: 消除 check-then-open TOCTOU。先以 O_NOFOLLOW 打开且
3010--        # **不带 O_TRUNC**，对**实际 fd** fstat 校验 inode；只有校验通过才
3011:-        # ftruncate。检查与写入作用于同一 fd，检查后被换 symlink/hardlink 无效。
3012-+        # round-7 架构整改: 不再截断既有文件 —— 同目录 O_EXCL 新建临时文件 →
3013:+        # 写 → fsync → os.replace 原子替换。O_EXCL 保证目标是本进程新建的对象，
3014:+        # 因此"把 --out 换成指向恢复源的 hardlink / 父目录 symlink / 大小写别名"
3015-+        # 这一整类绕过全部失效（脚本从不 ftruncate 任何既有 inode）；同时消除
3016:+        # 崩溃/ENOSPC 留下部分台账的风险（round-7 MEDIUM）。
3017-+        out_path = Path(args.out)
3018:+        tmp_path = out_path.with_name(f".{out_path.name}.census-tmp-{os.getpid()}")
3019-         try:
3020--            fd = os.open(args.out, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
3021:+            tmp_fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
3022-         except OSError as e:
3023:-            print(f"--out 无法安全打开（symlink 或权限）: {args.out} ({e})", file=sys.stderr)
3024:+            print(f"临时台账文件无法新建（O_EXCL）: {tmp_path} ({e})", file=sys.stderr)
3025-             return 2
3026-         try:
3027--            st = os.fstat(fd)
3028:-            # round-4 MEDIUM 整改: 非常规文件（FIFO/设备/socket）拒绝
3029--            if not stat.S_ISREG(st.st_mode):
3030--                print(f"--out 不是常规文件（FIFO/设备/socket），拒绝写出: {args.out}", file=sys.stderr)
3031--                return 2
3032:-            # round-5 HIGH 整改: 碰撞检查必须**先于** fchmod —— 否则 --out 指向
3033--            # 受保护的 0644 输入时，会先把只读输入的权限改成 0600 再拒绝。
3034--            if (st.st_dev, st.st_ino) in protected_ids:
3035--                print(
3036--                    f"--out 打开后经 fstat 判定与输入文件同一 inode，拒绝写出（防截断）: {args.out}",
--
3042--                os.fchmod(fd, 0o600)
3043--            os.ftruncate(fd, 0)
3044--            with os.fdopen(fd, "w", encoding="utf-8", closefd=True) as f:
3045--                fd = -1  # 所有权移交 fdopen
3046:+            with os.fdopen(tmp_fd, "w", encoding="utf-8", closefd=False) as f:
3047-                 f.write(out_json + "\n")
3048--        finally:
3049--            if fd >= 0:
3050--                os.close(fd)
3051-+                f.flush()
3052:+                os.fsync(tmp_fd)
3053-+        except Exception as e:
3054:+            os.close(tmp_fd)
3055:+            os.unlink(tmp_path)
3056-+            print(f"台账写入失败，已清理临时文件: {e}", file=sys.stderr)
3057-+            return 2
3058:+        os.close(tmp_fd)
3059-+        # 原子替换。目标若是恢复源，路径层与 inode 层已在前面拒绝；此处 replace
3060:+        # 只作用于本进程新建的 tmp，不存在"截断别人的文件"这一步。
3061:+        os.replace(tmp_path, out_path)
3062-         print(f"台账已写入: {args.out}")
3063-     else:
3064-         print(out_json)
3065- 
--
3077-     sys.exit(main())
3078-
3079-**Assessing impact of protected_ids removal**
3080-exec
3081:/bin/zsh -lc 'rg -n "BLOCKER|TOCTOU|MEDIUM|LOW|总裁定|总判|大小写|hardlink|symlink|retarget|ftruncate|92|冻结 ledger|可采信|不可验收|UAT|生成器" _bmad-output/审查/codex-review-CARD-G4-9-round7.md | head -260' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
3082- succeeded in 0ms:
3083:14:CARD-G4-9 round-7 复审（静态审阅 + 只读复算，禁改任何文件）。你 round-6 裁定 6/9 CLOSED，两项 BLOCKER 揭示了根因：--out 保护集依赖枚举完整性（0333 不可列举目录内的 transcript、QA DB inode ABA 都能挫败它）。开发方接受该判断，做了**架构级修复**并以 commit 5b371253 + 后续 receipt commit 提交：
3084:20:请逐项复核是否闭合，并针对路径层防御设计新反例（如 --out 位于 transcripts 根外但通过 symlink/hardlink 指入根内的文件、transcripts 根本身是 symlink、相对路径与 .. 组合、TOCTOU 把 --out 在检查后换成指入根内的链接）。同时复核台账仍为 92 条 / class 89-2-1 / byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0 / 重复簇 6/29 / unparseable 0 / attribution_conflict 3(no_token)。逐项 CLOSED/NOT-CLOSED + 总裁定 + 新发现分级；若可验收请明确说明。
3085-25:我会按“只读、fail-closed、生产入口优先”复审：先核对当前 checkout/commit 链与 round-6 基线，再分三条并行轨复算代码闭合、证据/receipt、以及 92 条台账与新反例；不会运行会写文件或数据库的命令。Graphiti/Sequential Thinking 若当前环境未暴露，我会在结论里明确记为工具限制。
3086-41:  • 设计并只读验证路径、inode、TOCTOU 新反例
3087:43:  • 交叉核验后给出逐项 CLOSED/NOT-CLOSED 与总裁定
3088-59:92-## Task 1: GOV01 A4 repair/micro chain audit, structurally verified but broader readiness partial
3089:72:106-- rollout_summaries/2026-08-23T10-38-57-0pt3-gov01_cache_prep_r2_read_only_exact_object_audit.md (cwd=/private/tmp/cls-gov01-a4-v1/planning-ro, rollout_path=/Users/Heishing/.codex/sessions/2026/08/23/rollout-2026-08-23T18-38-57-01a02e33-bb2c-7b93-85d0-3c50119edfad.jsonl, updated_at=2026-08-24T11:49:59+00:00, thread_id=01a02e33-bb2c-7b93-85d0-3c50119edfad, outcome=fail; 3 BLOCKER / 2 HIGH)
3090:76:110:- CACHE-PREP-V1, ADOPT.py, live-cache, per-digest claim, restart reconciliation, same-FD readback hash, RENAME_EXCL, O_EXCL, parent fsync, TOCTOU, _cacache/index-v5
3091:88:125:- `O_EXCL` plus `RENAME_EXCL` does not establish unique adopter or crash recovery. R2 found fixed temp `EEXIST` after pre-rename crash, nonsealed post-rename/pre-parent-fsync restart, no durable claim/reconciler, no write-side same-FD readback, and mutation-parent TOCTOU. Therefore `[ROLLUP:CACHE-PREP-V1:S3:R2-TECH] FAIL / BLOCKED`. [Task 2]
3092:152:3. Directly exercise real entrypoints with temporary fixtures where permitted. For path admission include symlink, directory symlink, blacklisted filename in an allowed directory, case variant, and nonexistent path. Assert rejected inputs perform zero open/hash/index/write.
3093-204:    23	- ORCH-BOOTSTRAP-PREP-V1, ORCH-SETUP-V1, ORCH-RUN-V1, non-LLM supervisor, app-server, Agent SDK, approval projection, setup-root-claim-v1, run-activation-claim-v1, O_NOFOLLOW, fencing token, no_auto_resume
3094-218:    37	- Envelope binds only target path, schema hash, construction-contract hash, and `preimage=ABSENT`; the activator creates actual approval-projection SHA, then binds claim/task/result/event. Keep SETUP/RUN claims separate; owner acquires `O_NOFOLLOW|O_CLOEXEC` advisory lock before LLM launch and restart increments epoch/fencing token. Reviewers independently materialize the exact candidate bundle and bind SHA, I/O hashes, command, exit, stdout/stderr, verdict, and limits. [Task 2]
3095-273:    92	## Task 1: GOV01 A4 repair/micro chain audit, structurally verified but broader readiness partial
3096:287:   106	- rollout_summaries/2026-08-23T10-38-57-0pt3-gov01_cache_prep_r2_read_only_exact_object_audit.md (cwd=/private/tmp/cls-gov01-a4-v1/planning-ro, rollout_path=/Users/Heishing/.codex/sessions/2026/08/23/rollout-2026-08-23T18-38-57-01a02e33-bb2c-7b93-85d0-3c50119edfad.jsonl, updated_at=2026-08-24T11:49:59+00:00, thread_id=01a02e33-bb2c-7b93-85d0-3c50119edfad, outcome=fail; 3 BLOCKER / 2 HIGH)
3097:291:   110	- CACHE-PREP-V1, ADOPT.py, live-cache, per-digest claim, restart reconciliation, same-FD readback hash, RENAME_EXCL, O_EXCL, parent fsync, TOCTOU, _cacache/index-v5
3098:306:   125	- `O_EXCL` plus `RENAME_EXCL` does not establish unique adopter or crash recovery. R2 found fixed temp `EEXIST` after pre-rename crash, nonsealed post-rename/pre-parent-fsync restart, no durable claim/reconciler, no write-side same-FD readback, and mutation-parent TOCTOU. Therefore `[ROLLUP:CACHE-PREP-V1:S3:R2-TECH] FAIL / BLOCKED`. [Task 2]
3099:358:   177	- P1-05b, symlink_escape, casefold, vault_backfill, lancedb_client, quarantine__p105b, search_nodes, read_node_tips, manifest-v3, NaN
3100-373:   192	- Green tests hitting source text, helpers, fake clients, `__new__`, or monkeypatches are not closure; pivot to production entrypoints and full stdout/trace. Test `search_nodes`, `read_node_tips`, `read_node_errors`, and `read_node_edge_reasons`. [Task 1][Task 2]
3101-467:67ccebe1 docs(census): G4-9 DLQ真实挂载census分诊 92条台账+挂载真相+三态裁定 [BATCH-2026-08-28-第五批 / CARD-G4-9]
3102-476:fca1bdc4 test(cypher): G2-1 读写契约审计+R1-R5/W1-W5 规则+7692 真库门测试 [BATCH-2026-08-27-第四批 / CARD-G2-1]
3103:496:./_bmad-output/审查/codex-review-CARD-G4-16-round3.md:659:A	"_bmad-output/\351\252\214\346\224\266\345\215\225/UAT-CARD-G4-9-DLQ\347\234\237\345\256\236\346\214\202\350\275\275census\345\210\206\350\257\212-2026-08-28.md"
3104-497:./_bmad-output/审查/codex-review-CARD-G4-16-round3.md:1027:67ccebe1 docs(census): G4-9 DLQ真实挂载census分诊 92条台账+挂载真相+三态裁定 [BATCH-2026-08-28-第五批 / CARD-G4-9]
3105:508:./_bmad-output/审查/codex-review-CARD-G4-16-round4.md:218:A	"_bmad-output/\351\252\214\346\224\266\345\215\225/UAT-CARD-G4-9-DLQ\347\234\237\345\256\236\346\214\202\350\275\275census\345\210\206\350\257\212-2026-08-28.md"
3106:514:./_bmad-output/审查/codex-review-CARD-G4-16-round4.md:1387:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md
3107:517:./_bmad-output/审查/codex-review-CARD-G4-16-round4.md:2686:M	"_bmad-output/\351\252\214\346\224\266\345\215\225/UAT-CARD-G4-9-DLQ\347\234\237\345\256\236\346\214\202\350\275\275census\345\210\206\350\257\212-2026-08-28.md"
3108-520:./_bmad-output/审查/codex-review-CARD-G4-16-round4.md:3861:67ccebe1 docs(census): G4-9 DLQ真实挂载census分诊 92条台账+挂载真相+三态裁定 [BATCH-2026-08-28-第五批 / CARD-G4-9]
3109:523:./backend/scripts/census_dead_letter_episodes.py:4:BATCH-2026-08-28-第五批 / CARD-G4-9（G4-10 replay 的交接台账生成器）。
3110-540:./backend/scripts/census_dead_letter_episodes.py:592:            unrecoverable_keys.append(stable_key)
3111-549:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:94:/bin/zsh -lc "rg -n -i \"CARD-G4-9|G4-9|fce0d8a2|92 条|89-2-1|4-88-0\" /Users/Heishing/.codex/memories/rollout_summaries /Users/Heishing/.codex/memories/MEMORY.md --glob '*.md' --glob '*.jsonl' || true
3112-556:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:131:67ccebe1 docs(census): G4-9 DLQ真实挂载census分诊 92条台账+挂载真相+三态裁定 [BATCH-2026-08-28-第五批 / CARD-G4-9]
3113:557:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:145:rg -n \"BLOCKER-1|HIGH-3|JSONL|framing|非 dict|provenance|PARTIAL|CLOSED|NOT-CLOSED|新发现|总裁定|protected_ids|O_NOFOLLOW|os\\.walk|line_count\" '_bmad-output/审查/codex-review-CARD-G4-9-round3.md' | head -n 240
3114:562:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:156:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md
3115:563:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:160:14:CARD-G4-9 round-3 复审（静态审阅 + 只读复算）。你 round-2 裁定 10/13 CLOSED，三项 NOT-CLOSED：BLOCKER-1（--out 守卫比 resolve 字符串，hardlink 与 case-only 别名绕过截断输入）、HIGH-1（full_body_verified 只核 sha 不核长度且排在 anomaly 分支前，anomaly 记录被判 byte_exact）、HIGH-3（chmod 000 根 exit 0 假判 unrecoverable；glob 跟随 symlink 逃逸出根）；另 3 新 LOW（full_verified 长度范围应 131-180、distribution 省略 0 值键、line_count 数 LF 与 records 的 splitlines 口径不一）。开发方以 commit 73102875 提交整改。请只读复核这 6 项是否闭合：
3116:564:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:186:1214: - **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
3117:566:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:192:1232:+- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
3118:567:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:193:1233:+- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
3119:568:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:213:1937:99:- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
3120:570:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:218:1947:118:- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
3121:571:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:226:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
3122:574:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:231:2148:    12	| HIGH-3 | **NOT-CLOSED** | 不存在根目录已 exit 2；递归唯一命中、多命中冲突、目录伪命中也通过。但“不可见”仍未闭合：存在但 `chmod 000` 的根会 exit 0 并假判 `unrecoverable`。此外 [`glob + os.path.isfile`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:134)跟随 symlink：根内 `.jsonl` symlink 指向根外 `.txt`、以及 symlink 目录逃逸到根外树，均被判唯一来源并进入 `approximate`。 |
3123:576:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:245:2765:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:7:| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
3124:577:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:246:2766:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:8:| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
3125:579:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:248:2768:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:12:| HIGH-3 | **NOT-CLOSED** | 不存在根目录已 exit 2；递归唯一命中、多命中冲突、目录伪命中也通过。但“不可见”仍未闭合：存在但 `chmod 000` 的根会 exit 0 并假判 `unrecoverable`。此外 [`glob + os.path.isfile`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:134)跟随 symlink：根内 `.jsonl` symlink 指向根外 `.txt`、以及 symlink 目录逃逸到根外树，均被判唯一来源并进入 `approximate`。 |
3126:580:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:249:2769:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:14:| MEDIUM-2 | **CLOSED** | [报告 §6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:78)、[ledger duplicate_clusters](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:60)及逐条 `reference_time` 已落地；6 簇全部逐行对账。 |
3127:581:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:250:2772:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:14:CARD-G4-9 round-3 复审（静态审阅 + 只读复算）。你 round-2 裁定 10/13 CLOSED，三项 NOT-CLOSED：BLOCKER-1（--out 守卫比 resolve 字符串，hardlink 与 case-only 别名绕过截断输入）、HIGH-1（full_body_verified 只核 sha 不核长度且排在 anomaly 分支前，anomaly 记录被判 byte_exact）、HIGH-3（chmod 000 根 exit 0 假判 unrecoverable；glob 跟随 symlink 逃逸出根）；另 3 新 LOW（full_verified 长度范围应 131-180、distribution 省略 0 值键、line_count 数 LF 与 records 的 splitlines 口径不一）。开发方以 commit 73102875 提交整改。请只读复核这 6 项是否闭合：
3128:583:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:252:2792:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1232:+- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
3129-584:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:253:2793:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1234:+- **新 LOW ×3**：full_verified 长度范围修正为 131–180；台账 `class_distribution`/`recoverability_distribution` 补零并新增 `inline_state_distribution`（固定 schema，消费者无需补齐缺席键）；`line_count` 改用 `splitlines()` 与 records 同口径（原 `count("\n")` 在 bare CR / U+2028 下会与 records 数不一致）。
3130-586:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:255:2810:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1948:119:- **新 LOW ×3**：full_verified 长度范围修正为 131–180；台账 `class_distribution`/`recoverability_distribution` 补零并新增 `inline_state_distribution`（固定 schema，消费者无需补齐缺席键）；`line_count` 改用 `splitlines()` 与 records 同口径（原 `count("\n")` 在 bare CR / U+2028 下会与 records 数不一致）。
3131:587:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:256:2815:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
3132:588:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:257:2816:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2144:     8	| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
3133:590:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:259:2818:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2148:    12	| HIGH-3 | **NOT-CLOSED** | 不存在根目录已 exit 2；递归唯一命中、多命中冲突、目录伪命中也通过。但“不可见”仍未闭合：存在但 `chmod 000` 的根会 exit 0 并假判 `unrecoverable`。此外 [`glob + os.path.isfile`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:134)跟随 symlink：根内 `.jsonl` symlink 指向根外 `.txt`、以及 symlink 目录逃逸到根外树，均被判唯一来源并进入 `approximate`。 |
3134:591:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:260:2819:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2150:    14	| MEDIUM-2 | **CLOSED** | [报告 §6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:78)、[ledger duplicate_clusters](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:60)及逐条 `reference_time` 已落地；6 簇全部逐行对账。 |
3135:592:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:261:2850:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:61:- **3 新 LOW**：full_verified 长度范围修正 131–180；台账三个 distribution 补零并新增 `inline_state_distribution`；`line_count` 与 records 改用同一 `splitlines()` 口径。
3136-594:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:277:3514:| LOW：distribution 零键 | **CLOSED** | [固定 schema 生成链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:437)与 [ledger](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:43)均包含 `unexpected/anomaly/unrecoverable: 0`，并新增 inline 三态。 |
3137:595:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:282:3534:所以：**冻结的 92 条 ledger 数值可采信；CARD-G4-9 生成器与整卡验收仍被 BLOCKER-1、HIGH-3 阻断。** 本轮未修改仓库或受审数据，未执行破坏性 fixture/G4-10 重放；Graphiti 工具本轮不可用。
3138-597:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:288:3547:| LOW：distribution 零键 | **CLOSED** | [固定 schema 生成链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:437)与 [ledger](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:43)均包含 `unexpected/anomaly/unrecoverable: 0`，并新增 inline 三态。 |
3139:598:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:293:3567:所以：**冻结的 92 条 ledger 数值可采信；CARD-G4-9 生成器与整卡验收仍被 BLOCKER-1、HIGH-3 阻断。** 本轮未修改仓库或受审数据，未执行破坏性 fixture/G4-10 重放；Graphiti 工具本轮不可用。
3140:601:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:340:@@ -52,7 +52,6 @@ BATCH-2026-08-28-第五批 / CARD-G4-9（G4-10 replay 的交接台账生成器
3141:606:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:565:     4	BATCH-2026-08-28-第五批 / CARD-G4-9（G4-10 replay 的交接台账生成器）。
3142:633:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1207:    95	| 负例门（round-2 整改自证） | **hardlink** 指向 DLQ 的 --out → exit 2 + DLQ sha 不变；**case-only 别名**（`DLQ.jsonl`）→ exit 2 + DLQ 完好；**anomaly + episode_body_full 组合**（sha 对但长度 999）→ anomaly/unrecoverable（不再翻案 byte_exact）；**chmod 000 根** → exit 2 拒诊；**symlink 逃逸**（根内 .jsonl → 根外 .txt）→ match_count=0/unrecoverable；正例回归：真实唯一命中仍 approximate |
3143:634:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1211:    99	- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
3144:635:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1213:   101	- **BLOCKER-3（交付物未冻结漂移）**：以本卡 commit 冻结全部交付物 exact bytes（脚本/报告/台账/证据包同 commit）；grep-selfattest 已按最终版行号重生成并内嵌脚本 sha 前缀。
3145:638:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1217:   105	- **MEDIUM-1**：`episode_body_full` 在盘且 sha 对账通过 → byte_exact 采信（现网 0 条，通路已备）。
3146:640:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1230:   118	- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
3147:661:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1642:{"attribution_conflicts_from_records": 0, "class": {"budget_400": 89, "group_id_format": 1, "schema_entity_type": 2}, "duplicate_clusters_from_raw": 6, "duplicate_rows_from_raw": 29, "header_sha_match": true, "inline": {"full_verified": 4, "truncated_prefix": 88}, "ledger_derivation_mismatches": [], "lf_frames": 92, "parsed_records": 92, "raw_unparseable": 0, "recoverability_from_records": {"approximate": 88, "byte_exact": 4}, "source_sha256": "3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590", "transcript_path_metadata": {"missing": 0, "nonregular": 0, "symlink": 0, "unique": 7, "unreadable": 0}}
3148-663:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1961:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:20:--- (4) 写出口（唯一，且经 O_NOFOLLOW+fstat inode 校验后才 ftruncate）:
3149-664:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1962:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:21:517:            fd = os.open(args.out, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
3150-665:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1963:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:22:529:            os.ftruncate(fd, 0)
3151:684:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:2175:不过生成器仍出现一个无需竞态的截断反例：匹配 transcript 若是“不可读但可写”（如 owner mode `0200`），扫描会把它从 `transcript_paths` 清掉，输出保护集因此漏掉它，而 `--out` 又能按写权限打开并截断。另有扫描错误最终仍被写成 `unrecoverable`，与“拒绝裁定”声明相反。终裁会据此维持阻断。
3152:686:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:2307:| 3. HIGH-3 枚举 | **NOT-CLOSED** | 稳态目录 symlink、`scandir` 错误和 mode `000` 门已有改善。但 unreadable/walk error 设置 conflict 后，主链仍在 [395–397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:395)明确产出 `recoverability=unrecoverable`，直接反驳报告所称“既不宣称不可恢复” [报告:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:143)。此外 `os.walk.onerror` 只覆盖 `scandir`；逐条 `is_dir/stat` 错误可被静默当非候选，[islink→isfile→access→realpath](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:168)仍是路径级竞态。 |
3153:688:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:2344:| 3. HIGH-3 枚举 | **NOT-CLOSED** | 稳态目录 symlink、`scandir` 错误和 mode `000` 门已有改善。但 unreadable/walk error 设置 conflict 后，主链仍在 [395–397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:395)明确产出 `recoverability=unrecoverable`，直接反驳报告所称“既不宣称不可恢复” [报告:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:143)。此外 `os.walk.onerror` 只覆盖 `scandir`；逐条 `is_dir/stat` 错误可被静默当非候选，[islink→isfile→access→realpath](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:168)仍是路径级竞态。 |
3154:690:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:14:CARD-G4-9 round-5 终裁复审（静态审阅 + 只读复算，禁改任何文件）。你 round-4 裁定 1/6 CLOSED，提出 2 BLOCKER / 1 HIGH / 2 MEDIUM / 3 LOW。开发方以 commit d2827a6d + d8d887f2 提交整改，请逐条只读复核：
3155:691:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:22:请对每项设计静态反例判断是否仍可绕过（尤其：保护集完整性、fd 身份与实际读取的绑定、unverifiable 与 unrecoverable 的语义边界、strict decode 的边界）。同时独立复算台账仍为 92 条 / class 89-2-1 / byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0 / 重复簇 6 簇 29 行 / unparseable 0。逐项 CLOSED/NOT-CLOSED + 总裁定（可验收/仍阻断）+ 新发现分级。若已可验收请明确说明；若仍阻断请说明**对一张只读 census 卡**而言该阻断是否与卡面范围相称。
3156-694:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:192:_bmad-output/审查/codex-review-CARD-G4-9-round2.md
3157:699:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:200:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md
3158:708:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:267:M	"_bmad-output/\351\252\214\346\224\266\345\215\225/UAT-CARD-G4-9-DLQ\347\234\237\345\256\236\346\214\202\350\275\275census\345\210\206\350\257\212-2026-08-28.md"
3159-713:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:276:67ccebe1 docs(census): G4-9 DLQ真实挂载census分诊 92条台账+挂载真相+三态裁定 [BATCH-2026-08-28-第五批 / CARD-G4-9]
3160:729:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:870:/bin/zsh -lc "rg -n 'BLOCKER|HIGH|MEDIUM|LOW|CLOSED|NOT-CLOSED|保护集|TOCTOU|UTF-8|unverifiable|unrecoverable|provenance|92|89|29' '_bmad-output/审查/codex-review-CARD-G4-9-round4.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
3161-731:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:882:94:/bin/zsh -lc "rg -n -i \"CARD-G4-9|G4-9|fce0d8a2|92 条|89-2-1|4-88-0\" /Users/Heishing/.codex/memories/rollout_summaries /Users/Heishing/.codex/memories/MEMORY.md --glob '*.md' --glob '*.jsonl' || true
3162-732:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:883:131:67ccebe1 docs(census): G4-9 DLQ真实挂载census分诊 92条台账+挂载真相+三态裁定 [BATCH-2026-08-28-第五批 / CARD-G4-9]
3163:733:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:884:145:rg -n \"BLOCKER-1|HIGH-3|JSONL|framing|非 dict|provenance|PARTIAL|CLOSED|NOT-CLOSED|新发现|总裁定|protected_ids|O_NOFOLLOW|os\\.walk|line_count\" '_bmad-output/审查/codex-review-CARD-G4-9-round3.md' | head -n 240
3164:734:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:885:160:14:CARD-G4-9 round-3 复审（静态审阅 + 只读复算）。你 round-2 裁定 10/13 CLOSED，三项 NOT-CLOSED：BLOCKER-1（--out 守卫比 resolve 字符串，hardlink 与 case-only 别名绕过截断输入）、HIGH-1（full_body_verified 只核 sha 不核长度且排在 anomaly 分支前，anomaly 记录被判 byte_exact）、HIGH-3（chmod 000 根 exit 0 假判 unrecoverable；glob 跟随 symlink 逃逸出根）；另 3 新 LOW（full_verified 长度范围应 131-180、distribution 省略 0 值键、line_count 数 LF 与 records 的 splitlines 口径不一）。开发方以 commit 73102875 提交整改。请只读复核这 6 项是否闭合：
3165:735:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:899:186:1214: - **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
3166:737:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:905:192:1232:+- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
3167:738:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:906:193:1233:+- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
3168:739:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:919:213:1937:99:- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
3169:740:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:923:217:1946:117:- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
3170:741:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:924:218:1947:118:- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
3171:742:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:928:226:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
3172:745:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:933:231:2148:    12	| HIGH-3 | **NOT-CLOSED** | 不存在根目录已 exit 2；递归唯一命中、多命中冲突、目录伪命中也通过。但“不可见”仍未闭合：存在但 `chmod 000` 的根会 exit 0 并假判 `unrecoverable`。此外 [`glob + os.path.isfile`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:134)跟随 symlink：根内 `.jsonl` symlink 指向根外 `.txt`、以及 symlink 目录逃逸到根外树，均被判唯一来源并进入 `approximate`。 |
3173:747:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:944:245:2765:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:7:| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
3174:748:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:945:246:2766:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:8:| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
3175:750:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:947:248:2768:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:12:| HIGH-3 | **NOT-CLOSED** | 不存在根目录已 exit 2；递归唯一命中、多命中冲突、目录伪命中也通过。但“不可见”仍未闭合：存在但 `chmod 000` 的根会 exit 0 并假判 `unrecoverable`。此外 [`glob + os.path.isfile`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:134)跟随 symlink：根内 `.jsonl` symlink 指向根外 `.txt`、以及 symlink 目录逃逸到根外树，均被判唯一来源并进入 `approximate`。 |
3176:751:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:948:249:2769:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:14:| MEDIUM-2 | **CLOSED** | [报告 §6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:78)、[ledger duplicate_clusters](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:60)及逐条 `reference_time` 已落地；6 簇全部逐行对账。 |
3177:752:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:949:250:2772:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:14:CARD-G4-9 round-3 复审（静态审阅 + 只读复算）。你 round-2 裁定 10/13 CLOSED，三项 NOT-CLOSED：BLOCKER-1（--out 守卫比 resolve 字符串，hardlink 与 case-only 别名绕过截断输入）、HIGH-1（full_body_verified 只核 sha 不核长度且排在 anomaly 分支前，anomaly 记录被判 byte_exact）、HIGH-3（chmod 000 根 exit 0 假判 unrecoverable；glob 跟随 symlink 逃逸出根）；另 3 新 LOW（full_verified 长度范围应 131-180、distribution 省略 0 值键、line_count 数 LF 与 records 的 splitlines 口径不一）。开发方以 commit 73102875 提交整改。请只读复核这 6 项是否闭合：
3178:753:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:950:252:2792:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1232:+- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
3179-754:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:951:253:2793:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1234:+- **新 LOW ×3**：full_verified 长度范围修正为 131–180；台账 `class_distribution`/`recoverability_distribution` 补零并新增 `inline_state_distribution`（固定 schema，消费者无需补齐缺席键）；`line_count` 改用 `splitlines()` 与 records 同口径（原 `count("\n")` 在 bare CR / U+2028 下会与 records 数不一致）。
3180-756:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:953:255:2810:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1948:119:- **新 LOW ×3**：full_verified 长度范围修正为 131–180；台账 `class_distribution`/`recoverability_distribution` 补零并新增 `inline_state_distribution`（固定 schema，消费者无需补齐缺席键）；`line_count` 改用 `splitlines()` 与 records 同口径（原 `count("\n")` 在 bare CR / U+2028 下会与 records 数不一致）。
3181:757:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:954:256:2815:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
3182:758:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:955:257:2816:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2144:     8	| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
3183:760:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:957:259:2818:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2148:    12	| HIGH-3 | **NOT-CLOSED** | 不存在根目录已 exit 2；递归唯一命中、多命中冲突、目录伪命中也通过。但“不可见”仍未闭合：存在但 `chmod 000` 的根会 exit 0 并假判 `unrecoverable`。此外 [`glob + os.path.isfile`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:134)跟随 symlink：根内 `.jsonl` symlink 指向根外 `.txt`、以及 symlink 目录逃逸到根外树，均被判唯一来源并进入 `approximate`。 |
3184:761:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:958:260:2819:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2150:    14	| MEDIUM-2 | **CLOSED** | [报告 §6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:78)、[ledger duplicate_clusters](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:60)及逐条 `reference_time` 已落地；6 簇全部逐行对账。 |
3185:762:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:959:261:2850:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:61:- **3 新 LOW**：full_verified 长度范围修正 131–180；台账三个 distribution 补零并新增 `inline_state_distribution`；`line_count` 与 records 改用同一 `splitlines()` 口径。
3186-764:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:968:277:3514:| LOW：distribution 零键 | **CLOSED** | [固定 schema 生成链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:437)与 [ledger](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:43)均包含 `unexpected/anomaly/unrecoverable: 0`，并新增 inline 三态。 |
3187:765:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:972:282:3534:所以：**冻结的 92 条 ledger 数值可采信；CARD-G4-9 生成器与整卡验收仍被 BLOCKER-1、HIGH-3 阻断。** 本轮未修改仓库或受审数据，未执行破坏性 fixture/G4-10 重放；Graphiti 工具本轮不可用。
3188-767:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:978:288:3547:| LOW：distribution 零键 | **CLOSED** | [固定 schema 生成链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:437)与 [ledger](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:43)均包含 `unexpected/anomaly/unrecoverable: 0`，并新增 inline 三态。 |
3189:768:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:982:293:3567:所以：**冻结的 92 条 ledger 数值可采信；CARD-G4-9 生成器与整卡验收仍被 BLOCKER-1、HIGH-3 阻断。** 本轮未修改仓库或受审数据，未执行破坏性 fixture/G4-10 重放；Graphiti 工具本轮不可用。
3190:785:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1090:1207:    95	| 负例门（round-2 整改自证） | **hardlink** 指向 DLQ 的 --out → exit 2 + DLQ sha 不变；**case-only 别名**（`DLQ.jsonl`）→ exit 2 + DLQ 完好；**anomaly + episode_body_full 组合**（sha 对但长度 999）→ anomaly/unrecoverable（不再翻案 byte_exact）；**chmod 000 根** → exit 2 拒诊；**symlink 逃逸**（根内 .jsonl → 根外 .txt）→ match_count=0/unrecoverable；正例回归：真实唯一命中仍 approximate |
3191:786:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1091:1211:    99	- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
3192:787:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1093:1213:   101	- **BLOCKER-3（交付物未冻结漂移）**：以本卡 commit 冻结全部交付物 exact bytes（脚本/报告/台账/证据包同 commit）；grep-selfattest 已按最终版行号重生成并内嵌脚本 sha 前缀。
3193:790:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1097:1217:   105	- **MEDIUM-1**：`episode_body_full` 在盘且 sha 对账通过 → byte_exact 采信（现网 0 条，通路已备）。
3194:792:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1106:1230:   118	- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
3195:805:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1158:1642:{"attribution_conflicts_from_records": 0, "class": {"budget_400": 89, "group_id_format": 1, "schema_entity_type": 2}, "duplicate_clusters_from_raw": 6, "duplicate_rows_from_raw": 29, "header_sha_match": true, "inline": {"full_verified": 4, "truncated_prefix": 88}, "ledger_derivation_mismatches": [], "lf_frames": 92, "parsed_records": 92, "raw_unparseable": 0, "recoverability_from_records": {"approximate": 88, "byte_exact": 4}, "source_sha256": "3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590", "transcript_path_metadata": {"missing": 0, "nonregular": 0, "symlink": 0, "unique": 7, "unreadable": 0}}
3196-806:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1175:1961:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:20:--- (4) 写出口（唯一，且经 O_NOFOLLOW+fstat inode 校验后才 ftruncate）:
3197-807:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1176:1962:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:21:517:            fd = os.open(args.out, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
3198-808:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1177:1963:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:22:529:            os.ftruncate(fd, 0)
3199:815:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1208:2175:不过生成器仍出现一个无需竞态的截断反例：匹配 transcript 若是“不可读但可写”（如 owner mode `0200`），扫描会把它从 `transcript_paths` 清掉，输出保护集因此漏掉它，而 `--out` 又能按写权限打开并截断。另有扫描错误最终仍被写成 `unrecoverable`，与“拒绝裁定”声明相反。终裁会据此维持阻断。
3200:816:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1216:2307:| 3. HIGH-3 枚举 | **NOT-CLOSED** | 稳态目录 symlink、`scandir` 错误和 mode `000` 门已有改善。但 unreadable/walk error 设置 conflict 后，主链仍在 [395–397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:395)明确产出 `recoverability=unrecoverable`，直接反驳报告所称“既不宣称不可恢复” [报告:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:143)。此外 `os.walk.onerror` 只覆盖 `scandir`；逐条 `is_dir/stat` 错误可被静默当非候选，[islink→isfile→access→realpath](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:168)仍是路径级竞态。 |
3201:818:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1235:2344:| 3. HIGH-3 枚举 | **NOT-CLOSED** | 稳态目录 symlink、`scandir` 错误和 mode `000` 门已有改善。但 unreadable/walk error 设置 conflict 后，主链仍在 [395–397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:395)明确产出 `recoverability=unrecoverable`，直接反驳报告所称“既不宣称不可恢复” [报告:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:143)。此外 `os.walk.onerror` 只覆盖 `scandir`；逐条 `is_dir/stat` 错误可被静默当非候选，[islink→isfile→access→realpath](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:168)仍是路径级竞态。 |
3202:827:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1350:| 负例门（round-2 整改自证） | **hardlink** 指向 DLQ 的 --out → exit 2 + DLQ sha 不变；**case-only 别名**（`DLQ.jsonl`）→ exit 2 + DLQ 完好；**anomaly + episode_body_full 组合**（sha 对但长度 999）→ anomaly/unrecoverable（不再翻案 byte_exact）；**chmod 000 根** → exit 2 拒诊；**symlink 逃逸**（根内 .jsonl → 根外 .txt）→ match_count=0/unrecoverable；正例回归：真实唯一命中仍 approximate |
3203:828:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1354:- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
3204:829:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1356:- **BLOCKER-3（交付物未冻结漂移）**：以本卡 commit 冻结全部交付物 exact bytes（脚本/报告/台账/证据包同 commit）；grep-selfattest 已按最终版行号重生成并内嵌脚本 sha 前缀。
3205:832:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1360:- **MEDIUM-1**：`episode_body_full` 在盘且 sha 对账通过 → byte_exact 采信（现网 0 条，通路已备）。
3206:834:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1373:- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
3207:838:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1422:67ccebe1  CARD-G4-9 初版交付（脚本/报告/台账/证据包/round-1 审查/UAT）
3208:842:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1448:CARD-G4-9 round-5 终裁复审（静态审阅 + 只读复算，禁改任何文件）。你 round-4 裁定 1/6 CLOSED，提出 2 BLOCKER / 1 HIGH / 2 MEDIUM / 3 LOW。开发方以 commit d2827a6d + d8d887f2 提交整改，请逐条只读复核：
3209:843:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1456:请对每项设计静态反例判断是否仍可绕过（尤其：保护集完整性、fd 身份与实际读取的绑定、unverifiable 与 unrecoverable 的语义边界、strict decode 的边界）。同时独立复算台账仍为 92 条 / class 89-2-1 / byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0 / 重复簇 6 簇 29 行 / unparseable 0。逐项 CLOSED/NOT-CLOSED + 总裁定（可验收/仍阻断）+ 新发现分级。若已可验收请明确说明；若仍阻断请说明**对一张只读 census 卡**而言该阻断是否与卡面范围相称。
3210-854:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1926:   500	        if recover == "unrecoverable":
3211-855:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1927:   501	            unrecoverable_keys.append(stable_key)
3212:860:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2099:     4	BATCH-2026-08-28-第五批 / CARD-G4-9（G4-10 replay 的交接台账生成器）。
3213:867:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2281:/bin/zsh -lc "rg -n '不可读但可写|源侧 TOCTOU|不可见终态|非法 UTF-8|字段错型|root_prefix|fchmod|provenance|总裁定|BLOCKER' '_bmad-output/审查/codex-review-CARD-G4-9-round4.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
3214:868:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2288:145:rg -n \"BLOCKER-1|HIGH-3|JSONL|framing|非 dict|provenance|PARTIAL|CLOSED|NOT-CLOSED|新发现|总裁定|protected_ids|O_NOFOLLOW|os\\.walk|line_count\" '_bmad-output/审查/codex-review-CARD-G4-9-round3.md' | head -n 240
3215:869:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2289:160:14:CARD-G4-9 round-3 复审（静态审阅 + 只读复算）。你 round-2 裁定 10/13 CLOSED，三项 NOT-CLOSED：BLOCKER-1（--out 守卫比 resolve 字符串，hardlink 与 case-only 别名绕过截断输入）、HIGH-1（full_body_verified 只核 sha 不核长度且排在 anomaly 分支前，anomaly 记录被判 byte_exact）、HIGH-3（chmod 000 根 exit 0 假判 unrecoverable；glob 跟随 symlink 逃逸出根）；另 3 新 LOW（full_verified 长度范围应 131-180、distribution 省略 0 值键、line_count 数 LF 与 records 的 splitlines 口径不一）。开发方以 commit 73102875 提交整改。请只读复核这 6 项是否闭合：
3216:870:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2298:186:1214: - **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
3217:871:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2305:213:1937:99:- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
3218:872:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2310:226:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
3219:873:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2313:245:2765:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:7:| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
3220:874:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2314:246:2766:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:8:| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
3221:875:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2315:250:2772:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:14:CARD-G4-9 round-3 复审（静态审阅 + 只读复算）。你 round-2 裁定 10/13 CLOSED，三项 NOT-CLOSED：BLOCKER-1（--out 守卫比 resolve 字符串，hardlink 与 case-only 别名绕过截断输入）、HIGH-1（full_body_verified 只核 sha 不核长度且排在 anomaly 分支前，anomaly 记录被判 byte_exact）、HIGH-3（chmod 000 根 exit 0 假判 unrecoverable；glob 跟随 symlink 逃逸出根）；另 3 新 LOW（full_verified 长度范围应 131-180、distribution 省略 0 值键、line_count 数 LF 与 records 的 splitlines 口径不一）。开发方以 commit 73102875 提交整改。请只读复核这 6 项是否闭合：
3222:876:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2316:256:2815:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
3223:877:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2317:257:2816:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2144:     8	| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
3224:878:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2325:282:3534:所以：**冻结的 92 条 ledger 数值可采信；CARD-G4-9 生成器与整卡验收仍被 BLOCKER-1、HIGH-3 阻断。** 本轮未修改仓库或受审数据，未执行破坏性 fixture/G4-10 重放；Graphiti 工具本轮不可用。
3225:879:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2329:293:3567:所以：**冻结的 92 条 ledger 数值可采信；CARD-G4-9 生成器与整卡验收仍被 BLOCKER-1、HIGH-3 阻断。** 本轮未修改仓库或受审数据，未执行破坏性 fixture/G4-10 重放；Graphiti 工具本轮不可用。
3226:880:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2340:1211:    99	- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
3227:881:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2342:1213:   101	- **BLOCKER-3（交付物未冻结漂移）**：以本卡 commit 冻结全部交付物 exact bytes（脚本/报告/台账/证据包同 commit）；grep-selfattest 已按最终版行号重生成并内嵌脚本 sha 前缀。
3228:882:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2351:2175:不过生成器仍出现一个无需竞态的截断反例：匹配 transcript 若是“不可读但可写”（如 owner mode `0200`），扫描会把它从 `transcript_paths` 清掉，输出保护集因此漏掉它，而 `--out` 又能按写权限打开并截断。另有扫描错误最终仍被写成 `unrecoverable`，与“拒绝裁定”声明相反。终裁会据此维持阻断。
3229:884:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2388:  2307	| 3. HIGH-3 枚举 | **NOT-CLOSED** | 稳态目录 symlink、`scandir` 错误和 mode `000` 门已有改善。但 unreadable/walk error 设置 conflict 后，主链仍在 [395–397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:395)明确产出 `recoverability=unrecoverable`，直接反驳报告所称“既不宣称不可恢复” [报告:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:143)。此外 `os.walk.onerror` 只覆盖 `scandir`；逐条 `is_dir/stat` 错误可被静默当非候选，[islink→isfile→access→realpath](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:168)仍是路径级竞态。 |
3230:886:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2425:  2344	| 3. HIGH-3 枚举 | **NOT-CLOSED** | 稳态目录 symlink、`scandir` 错误和 mode `000` 门已有改善。但 unreadable/walk error 设置 conflict 后，主链仍在 [395–397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:395)明确产出 `recoverability=unrecoverable`，直接反驳报告所称“既不宣称不可恢复” [报告:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:143)。此外 `os.walk.onerror` 只覆盖 `scandir`；逐条 `is_dir/stat` 错误可被静默当非候选，[islink→isfile→access→realpath](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:168)仍是路径级竞态。 |
3231:890:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2487:     5	67ccebe1  CARD-G4-9 初版交付（脚本/报告/台账/证据包/round-1 审查/UAT）
3232-891:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2492:    10	d2827a6d  CARD-G4-9 round-4 整改（本 receipt 所描述的 commit）
3233:910:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2954:/bin/zsh -lc "rg -n '0 写|只读|保护|qa_metrics|transcript|92|89|byte_exact|unverifiable|unrecoverable|验收' '_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
3234-911:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2956:6:scope: "BATCH-2026-08-28-第五批 / CARD-G4-9 — live DLQ 92 条只读 census：分类/SHA 对账/可恢复性三态/挂载真相，产出 G4-10 交接台账"
3235:913:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2968:35:| Codex 独立审查 round-1 | **BLOCKED**（3 BLOCKER：--out 可截断输入 / 快照不原子 / 交付物未冻结；3 HIGH：inline 判定 fail-open / request_id 归因传染 / transcript 归因折叠；3 MEDIUM + 4 LOW。同时确认：**当前 92 条数字逐项 0 mismatch**、class/三态/家族计数全对） | `_bmad-output/审查/codex-review-CARD-G4-9.md` |
3236:914:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2969:37:| Codex 复审 round-2 | **仍阻断**（10/13 CLOSED；BLOCKER-1/HIGH-1/HIGH-3 未真正闭合 + 3 新 LOW）。同时独立复算确认：67ccebe1 冻结生效、92 条数字与 6/29 重复簇全部可复算 | `_bmad-output/审查/codex-review-CARD-G4-9-round2.md`（codex 被 cyber 误拦，内容由 stdout 抢救存档） |
3237:915:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2970:40:| round-3 findings 逐条整改 | **6/6 完成**：transcript 并入保护集 / O_NOFOLLOW+fstat 消 TOCTOU / os.walk 替 glob（不跟随目录 symlink+遍历错误显式捕获）/ 不可读候选 fail-closed / JSONL 严格 LF 分帧 / 非 dict 归 unparseable。6 条新反例实测全过、数字第三次不变 | 报告 §7d + `grep-selfattest.txt` |
3238-916:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2971:42:| round-4 findings 逐条整改 | **9/9 完成**：全候选入保护集 / 读侧 fd 身份消源侧 TOCTOU / 新增 unverifiable 第四态 / FIFO 设备门 / strict UTF-8 / 3 条错型与边界 LOW / provenance receipt。5 条新反例实测全过；第四次全量重跑数字仍不变 | 报告 §7e + `grep-selfattest.txt` |
3239:922:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3063:/bin/zsh -lc "nl -ba '_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md' | sed -n '145,175p'; nl -ba '_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md' | sed -n '8,45p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
3240:924:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3086:    10	# UAT · CARD-G4-9 DLQ 真实挂载 census 分诊
3241:926:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3111:    35	| Codex 独立审查 round-1 | **BLOCKED**（3 BLOCKER：--out 可截断输入 / 快照不原子 / 交付物未冻结；3 HIGH：inline 判定 fail-open / request_id 归因传染 / transcript 归因折叠；3 MEDIUM + 4 LOW。同时确认：**当前 92 条数字逐项 0 mismatch**、class/三态/家族计数全对） | `_bmad-output/审查/codex-review-CARD-G4-9.md` |
3242:927:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3113:    37	| Codex 复审 round-2 | **仍阻断**（10/13 CLOSED；BLOCKER-1/HIGH-1/HIGH-3 未真正闭合 + 3 新 LOW）。同时独立复算确认：67ccebe1 冻结生效、92 条数字与 6/29 重复簇全部可复算 | `_bmad-output/审查/codex-review-CARD-G4-9-round2.md`（codex 被 cyber 误拦，内容由 stdout 抢救存档） |
3243:928:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3114:    38	| round-2 findings 逐条整改 | **6/6 完成**：inode 身份守卫封 hardlink+大小写别名 / full_body 长度门+anomaly 前置 / 不可读根 exit 2+symlink 逃逸拒采信 / 3 新 LOW。5 条新负例实测全过、正例无回归、数字仍逐项一致 | 报告 §7/§7c + `grep-selfattest.txt` |
3244:929:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3115:    39	| Codex 复审 round-3 | **仍阻断**（4/6 CLOSED；BLOCKER-1/HIGH-3 判 PARTIAL + 1 新 MEDIUM + 2 新 LOW）。同时确认：HIGH-1 与三条 LOW 已闭合、台账数字有效且与 commit 字节一致 | `_bmad-output/审查/codex-review-CARD-G4-9-round3.md` |
3245:930:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3116:    40	| round-3 findings 逐条整改 | **6/6 完成**：transcript 并入保护集 / O_NOFOLLOW+fstat 消 TOCTOU / os.walk 替 glob（不跟随目录 symlink+遍历错误显式捕获）/ 不可读候选 fail-closed / JSONL 严格 LF 分帧 / 非 dict 归 unparseable。6 条新反例实测全过、数字第三次不变 | 报告 §7d + `grep-selfattest.txt` |
3246:931:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3117:    41	| Codex 复审 round-4 | **仍阻断**（1/6 CLOSED；2 新 BLOCKER + 1 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round4.md` |
3247-932:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3118:    42	| round-4 findings 逐条整改 | **9/9 完成**：全候选入保护集 / 读侧 fd 身份消源侧 TOCTOU / 新增 unverifiable 第四态 / FIFO 设备门 / strict UTF-8 / 3 条错型与边界 LOW / provenance receipt。5 条新反例实测全过；第四次全量重跑数字仍不变 | 报告 §7e + `grep-selfattest.txt` |
3248:938:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3332:总裁定：**仍阻断 / CARD-G4-9 不可验收**。  
3249:941:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3370:这个阻断与“一张只读 census 卡”的范围**完全相称**：报告和 UAT 明确承诺纯只读、零写入，[UAT:13](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:13)。残留反例能直接截断或修改本卡正在保护的恢复源，不是范围外的生产级加固要求。
3250:942:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3377:总裁定：**仍阻断 / CARD-G4-9 不可验收**。  
3251:945:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3415:这个阻断与“一张只读 census 卡”的范围**完全相称**：报告和 UAT 明确承诺纯只读、零写入，[UAT:13](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:13)。残留反例能直接截断或修改本卡正在保护的恢复源，不是范围外的生产级加固要求。
3252-979:./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:926:   "attribution_conflict_reason": null,
3253:1046:./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:3:title: "UAT · CARD-G4-9 DLQ 真实挂载 census 分诊（2026-08-28）"
3254:1047:./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:6:scope: "BATCH-2026-08-28-第五批 / CARD-G4-9 — live DLQ 92 条只读 census：分类/SHA 对账/可恢复性三态/挂载真相，产出 G4-10 交接台账"
3255:1048:./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:10:# UAT · CARD-G4-9 DLQ 真实挂载 census 分诊
3256:1049:./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:28:| 脚本只读自证（判据 a） | import 行全 stdlib；neo4j/graphiti/bolt/app. import **0 命中**；`--apply` 定义 **0 命中**；写模式 open 仅台账 `--out` 1 处 | `G4-9-evidence/grep-selfattest.txt` |
3257:1050:./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:35:| Codex 独立审查 round-1 | **BLOCKED**（3 BLOCKER：--out 可截断输入 / 快照不原子 / 交付物未冻结；3 HIGH：inline 判定 fail-open / request_id 归因传染 / transcript 归因折叠；3 MEDIUM + 4 LOW。同时确认：**当前 92 条数字逐项 0 mismatch**、class/三态/家族计数全对） | `_bmad-output/审查/codex-review-CARD-G4-9.md` |
3258:1051:./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:37:| Codex 复审 round-2 | **仍阻断**（10/13 CLOSED；BLOCKER-1/HIGH-1/HIGH-3 未真正闭合 + 3 新 LOW）。同时独立复算确认：67ccebe1 冻结生效、92 条数字与 6/29 重复簇全部可复算 | `_bmad-output/审查/codex-review-CARD-G4-9-round2.md`（codex 被 cyber 误拦，内容由 stdout 抢救存档） |
3259:1052:./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:38:| round-2 findings 逐条整改 | **6/6 完成**：inode 身份守卫封 hardlink+大小写别名 / full_body 长度门+anomaly 前置 / 不可读根 exit 2+symlink 逃逸拒采信 / 3 新 LOW。5 条新负例实测全过、正例无回归、数字仍逐项一致 | 报告 §7/§7c + `grep-selfattest.txt` |
3260:1053:./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:39:| Codex 复审 round-3 | **仍阻断**（4/6 CLOSED；BLOCKER-1/HIGH-3 判 PARTIAL + 1 新 MEDIUM + 2 新 LOW）。同时确认：HIGH-1 与三条 LOW 已闭合、台账数字有效且与 commit 字节一致 | `_bmad-output/审查/codex-review-CARD-G4-9-round3.md` |
3261:1054:./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:40:| round-3 findings 逐条整改 | **6/6 完成**：transcript 并入保护集 / O_NOFOLLOW+fstat 消 TOCTOU / os.walk 替 glob（不跟随目录 symlink+遍历错误显式捕获）/ 不可读候选 fail-closed / JSONL 严格 LF 分帧 / 非 dict 归 unparseable。6 条新反例实测全过、数字第三次不变 | 报告 §7d + `grep-selfattest.txt` |
3262:1055:./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:41:| Codex 复审 round-4 | **仍阻断**（1/6 CLOSED；2 新 BLOCKER + 1 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round4.md` |
3263:1056:./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:42:| round-4 findings 逐条整改 | **9/9 完成**：全候选入保护集 / 读侧 fd 身份消源侧 TOCTOU / 新增 unverifiable 第四态 / FIFO 设备门 / strict UTF-8 / 3 条错型与边界 LOW / provenance receipt。5 条新反例实测全过；第四次全量重跑数字仍不变 | 报告 §7e + `grep-selfattest.txt` |
3264:1057:./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:43:| Codex 复审 round-5 | **仍阻断**（3/8 CLOSED；2 BLOCKER + 2 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round5.md` |
3265:1058:./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:44:| round-5 findings 逐条整改 | **9/9 完成**：先扫描后判定（冲突候选亦入保护集）/ QA DB fd 身份+复核 / 可见性优先于 anomaly / fchmod 后置于碰撞检查 / QA DB 特殊文件门 / no_token 归 unverifiable / 3 条 LOW。6 条新反例实测全过；第五次全量重跑数字仍不变 | 报告 §7f |
3266:1059:./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:45:| Codex 复审 round-6 | **6/9 CLOSED**（visibility 优先/fchmod 顺序/no_token 语义/3 条 LOW 已闭合）；剩 2 BLOCKER + 1 MEDIUM 揭示保护集**依赖枚举完整性**的架构缺陷 + 3 新发现 | `_bmad-output/审查/codex-review-CARD-G4-9-round6.md` |
3267:1060:./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:46:| round-6 findings 整改 | **架构级修复 + 6 项**：新增不依赖枚举的**路径层防御**（--out 禁落 transcripts 根内 / 禁等于任一输入 realpath）、QA DB 验证 fd 保持打开至复核完毕、no_token 亦扫描、证据包重生成、ledger 冲突原因自描述、lone surrogate 回退。反例实测：0333 隐藏目录内 transcript 作 --out → exit 2 完好 | 报告 §7g |
3268:1061:./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:54:- **HIGH-1 inline 判定 fail-open**：sha 匹配但长度不符会误判 full_verified（反例实测）。整改：长度精确匹配门 + 64-hex 合法性门 + anomaly 一律 fail-closed（unrecoverable + 如实 basis）。
3269:1062:./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:56:- **HIGH-3 transcript 归因折叠**：多命中照单全收、目录缺失误判 unrecoverable=88（实测复现）。整改：恰 1 常规文件命中门 + 递归 glob + 目录缺失 exit 2 拒诊。
3270:1063:./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:90:- **把"看不见"说成"不可恢复"**：扫描受阻时仍输出 `unrecoverable`，与报告里"既不宣称不可恢复"自相矛盾。→ 新增第四态 **`unverifiable`**，逐条写明是遍历受阻还是候选不可读。
3271:1064:./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:101:- **anomaly 吞掉了"看不见"**：`anomaly→unrecoverable` 排在可见性判断之前，扫描受阻时仍断言"不可恢复"。→ 判定链改为**可见性优先**。
3272:1065:./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:115:另修：QA DB 的验证 fd 改为**保持打开**到复核完毕（堵 ABA）；`no_token` 分支也扫描（原本完全不扫，候选进不了保护集）；证据包每轮重生成（round-6 指出我的 self-attest 停留在 round-4 的旧 SHA，属实）；台账新增冲突原因自描述。
3273:1066:./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:125:- `_bmad-output/审查/codex-review-CARD-G4-9.md` — Codex 独立审查存档
3274:1068:./_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt:5:67ccebe1  CARD-G4-9 初版交付（脚本/报告/台账/证据包/round-1 审查/UAT）
3275-1077:./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:92:| grep 自证（import 行全 stdlib；neo4j/graphiti/bolt/app. import 0 命中；`--apply` 定义 0 命中；写模式 open 仅 `--out` 1 处且受路径碰撞守卫保护） | **PASS**（`grep-selfattest.txt`，含守卫在位证明） |
3276:1079:./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:96:| 负例门（round-2 整改自证） | **hardlink** 指向 DLQ 的 --out → exit 2 + DLQ sha 不变；**case-only 别名**（`DLQ.jsonl`）→ exit 2 + DLQ 完好；**anomaly + episode_body_full 组合**（sha 对但长度 999）→ anomaly/unrecoverable（不再翻案 byte_exact）；**chmod 000 根** → exit 2 拒诊；**symlink 逃逸**（根内 .jsonl → 根外 .txt）→ match_count=0/unrecoverable；正例回归：真实唯一命中仍 approximate |
3277:1080:./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:100:- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
3278:1081:./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:102:- **BLOCKER-3（交付物未冻结漂移）**：以本卡 commit 冻结全部交付物 exact bytes（脚本/报告/台账/证据包同 commit）；grep-selfattest 已按最终版行号重生成并内嵌脚本 sha 前缀。
3279:1084:./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:106:- **MEDIUM-1**：`episode_body_full` 在盘且 sha 对账通过 → byte_exact 采信（现网 0 条，通路已备）。
3280:1086:./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:119:- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
3281:1090:./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:174:- **MEDIUM（无 token 未扫描即判不可恢复）**：改为 `unverifiable` + `no_token` 标记（见 HIGH①）。
3282-1092:./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:179:round-5 整改后第五次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变——五轮整改数字全程未变**。
3283-1093:./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:183:round-6 确认 visibility 优先、fchmod 顺序、no_token 语义、三条 LOW 共 6 项 CLOSED，并揭示了一个**架构层面的根因**：
3284:1094:./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:189:- **BLOCKER① 补充修复**：`no_token` 分支原本完全不扫描（`all_candidate_paths=[]`）→ 改为**无论有无 token 都遍历**，所有 `.jsonl` 一律入保护集口径。
3285:1095:./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:190:- **MEDIUM（证据包漂移）**：`grep-selfattest.txt` 曾停留在 round-4 的脚本 SHA 与旧行号、receipt 未含最新 commit——这是我的疏漏。已重生成（内嵌当前脚本 sha256 + 生成时点声明），receipt 随本轮补链。
3286-1096:./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:191:- **LOW ×3**：ledger 新增 `attribution_conflict_reason` 自描述（本次 92 条：`no_token` 3 / 其余 89 无冲突）；`json.dumps` 对 lone surrogate 回退 `ensure_ascii=True` 并显式标注，不再整次 census 拒绝；`stat_failures` 分支保留（Codex 确认非额外绕过，仅基本不可达）。
3287-1097:./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:193:round-6 整改后第六次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变——六轮整改数字全程未变**。
3288-1098:./_bmad-output/审查/G4-9-evidence/census-stderr.txt:1:census: 92 条 (+0 unparseable) | class={'schema_entity_type': 2, 'group_id_format': 1, 'budget_400': 89} | recoverability={'byte_exact': 4, 'approximate': 88} | 归因冲突=3 | 重复簇=6 | 偏差=无 | qa_metrics 核销=no_source_rows
3289:1100:./_bmad-output/审查/codex-review-CARD-G4-9-round7.md:14:CARD-G4-9 round-7 复审（静态审阅 + 只读复算，禁改任何文件）。你 round-6 裁定 6/9 CLOSED，两项 BLOCKER 揭示了根因：--out 保护集依赖枚举完整性（0333 不可列举目录内的 transcript、QA DB inode ABA 都能挫败它）。开发方接受该判断，做了**架构级修复**并以 commit 5b371253 + 后续 receipt commit 提交：
3290:1105:./_bmad-output/审查/codex-review-CARD-G4-9-round7.md:20:请逐项复核是否闭合，并针对路径层防御设计新反例（如 --out 位于 transcripts 根外但通过 symlink/hardlink 指入根内的文件、transcripts 根本身是 symlink、相对路径与 .. 组合、TOCTOU 把 --out 在检查后换成指入根内的链接）。同时复核台账仍为 92 条 / class 89-2-1 / byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0 / 重复簇 6/29 / unparseable 0 / attribution_conflict 3(no_token)。逐项 CLOSED/NOT-CLOSED + 总裁定 + 新发现分级；若可验收请明确说明。
3291:1107:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:14:CARD-G4-9 round-3 复审（静态审阅 + 只读复算）。你 round-2 裁定 10/13 CLOSED，三项 NOT-CLOSED：BLOCKER-1（--out 守卫比 resolve 字符串，hardlink 与 case-only 别名绕过截断输入）、HIGH-1（full_body_verified 只核 sha 不核长度且排在 anomaly 分支前，anomaly 记录被判 byte_exact）、HIGH-3（chmod 000 根 exit 0 假判 unrecoverable；glob 跟随 symlink 逃逸出根）；另 3 新 LOW（full_verified 长度范围应 131-180、distribution 省略 0 值键、line_count 数 LF 与 records 的 splitlines 口径不一）。开发方以 commit 73102875 提交整改。请只读复核这 6 项是否闭合：
3292:1114:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:614: BATCH-2026-08-28-第五批 / CARD-G4-9（G4-10 replay 的交接台账生成器）。
3293:1120:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:653:-    重算 sha 对账通过则按 byte_exact 采信（Codex round-1 MEDIUM-1 整改）。
3294:1144:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1210:+| 负例门（round-2 整改自证） | **hardlink** 指向 DLQ 的 --out → exit 2 + DLQ sha 不变；**case-only 别名**（`DLQ.jsonl`）→ exit 2 + DLQ 完好；**anomaly + episode_body_full 组合**（sha 对但长度 999）→ anomaly/unrecoverable（不再翻案 byte_exact）；**chmod 000 根** → exit 2 拒诊；**symlink 逃逸**（根内 .jsonl → 根外 .txt）→ match_count=0/unrecoverable；正例回归：真实唯一命中仍 approximate |
3295:1145:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1214: - **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
3296:1146:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1216: - **BLOCKER-3（交付物未冻结漂移）**：以本卡 commit 冻结全部交付物 exact bytes（脚本/报告/台账/证据包同 commit）；grep-selfattest 已按最终版行号重生成并内嵌脚本 sha 前缀。
3297:1149:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1220: - **MEDIUM-1**：`episode_body_full` 在盘且 sha 对账通过 → byte_exact 采信（现网 0 条，通路已备）。
3298:1151:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1233:+- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
3299:1159:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1433:     4	BATCH-2026-08-28-第五批 / CARD-G4-9（G4-10 replay 的交接台账生成器）。
3300:1179:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1935:95:| 负例门（round-2 整改自证） | **hardlink** 指向 DLQ 的 --out → exit 2 + DLQ sha 不变；**case-only 别名**（`DLQ.jsonl`）→ exit 2 + DLQ 完好；**anomaly + episode_body_full 组合**（sha 对但长度 999）→ anomaly/unrecoverable（不再翻案 byte_exact）；**chmod 000 根** → exit 2 拒诊；**symlink 逃逸**（根内 .jsonl → 根外 .txt）→ match_count=0/unrecoverable；正例回归：真实唯一命中仍 approximate |
3301:1180:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1937:99:- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
3302:1183:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1947:118:- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
3303-1188:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2113:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:25:266:    # (st_dev, st_ino) 而非 resolve() 字符串 —— 后者对 hardlink 与
3304:1189:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2114:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:30:--- (6) fail-closed 门（不可读根 / symlink 逃逸 / anomaly 前置）:
3305:1194:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2130:"_bmad-output/\351\252\214\346\224\266\345\215\225/UAT-CARD-G4-9-DLQ\347\234\237\345\256\236\346\214\202\350\275\275census\345\210\206\350\257\212-2026-08-28.md"
3306:1196:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
3307:1199:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2148:    12	| HIGH-3 | **NOT-CLOSED** | 不存在根目录已 exit 2；递归唯一命中、多命中冲突、目录伪命中也通过。但“不可见”仍未闭合：存在但 `chmod 000` 的根会 exit 0 并假判 `unrecoverable`。此外 [`glob + os.path.isfile`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:134)跟随 symlink：根内 `.jsonl` symlink 指向根外 `.txt`、以及 symlink 目录逃逸到根外树，均被判唯一来源并进入 `approximate`。 |
3308-1201:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2170:    34	- **LOW**：ledger distribution 省略 `unexpected:0`、`anomaly:0`、`unrecoverable:0`，固定 schema 消费者需自行补零。
3309-1210:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2590:   292	            recover = "unrecoverable"
3310:1217:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2765:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:7:| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
3311:1218:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2766:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:8:| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
3312:1220:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2768:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:12:| HIGH-3 | **NOT-CLOSED** | 不存在根目录已 exit 2；递归唯一命中、多命中冲突、目录伪命中也通过。但“不可见”仍未闭合：存在但 `chmod 000` 的根会 exit 0 并假判 `unrecoverable`。此外 [`glob + os.path.isfile`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:134)跟随 symlink：根内 `.jsonl` symlink 指向根外 `.txt`、以及 symlink 目录逃逸到根外树，均被判唯一来源并进入 `approximate`。 |
3313:1221:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2769:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:14:| MEDIUM-2 | **CLOSED** | [报告 §6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:78)、[ledger duplicate_clusters](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:60)及逐条 `reference_time` 已落地；6 簇全部逐行对账。 |
3314:1222:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2772:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:14:CARD-G4-9 round-3 复审（静态审阅 + 只读复算）。你 round-2 裁定 10/13 CLOSED，三项 NOT-CLOSED：BLOCKER-1（--out 守卫比 resolve 字符串，hardlink 与 case-only 别名绕过截断输入）、HIGH-1（full_body_verified 只核 sha 不核长度且排在 anomaly 分支前，anomaly 记录被判 byte_exact）、HIGH-3（chmod 000 根 exit 0 假判 unrecoverable；glob 跟随 symlink 逃逸出根）；另 3 新 LOW（full_verified 长度范围应 131-180、distribution 省略 0 值键、line_count 数 LF 与 records 的 splitlines 口径不一）。开发方以 commit 73102875 提交整改。请只读复核这 6 项是否闭合：
3315:1240:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2790:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1194: 台账逐条携带复合键 `{line_no, sha256_prefix(16 hex), request_id}`。**语义（Codex round-1 LOW-2 修正）**：这是**冻结快照内的 occurrence key**，不是跨文件重排或语义幂等键——台账头部 `dlq_file.sha256`（`3b37460f4215f6ac…`）即快照指纹，`line_no` 在该快照内已单列唯一；`sha256_prefix`（本快照 69 个唯一值，qa_highlight 家族实测同名同 sha 多条）与 `request_id`（仅 25 个唯一值，进程内 contextvars、重启可复用）是**冗余对账/诊断维度**，不是唯一性的必要条件。G4-10 消费前先 diff 头部 sha 即知 DLQ 是否长了新条目；语义级去重不得按本键，须按 `duplicate_clusters` 段（见下）。**语义重复簇（MEDIUM-2 整改）**：按 `{name, episode_body_sha256, group_id}` 聚簇，**6 簇覆盖 29 行**（最大簇 = 同一 session-archive 16 行，`reference_time` 各不相同——同内容反复入队反复超限）。台账 `duplicate_clusters` 段逐簇列 line_nos，records 逐条透传 `reference_time`；G4-10 重放前必须先定去重策略（89 条 budget 修根因后若逐条盲放，将把同内容写入最多 16 遍）。
3316:1241:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2791:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1221: - **MEDIUM-2**：`duplicate_clusters` 段 + 逐条 `reference_time`（见 §6）。
3317:1242:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2792:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1232:+- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
3318-1243:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2793:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1234:+- **新 LOW ×3**：full_verified 长度范围修正为 131–180；台账 `class_distribution`/`recoverability_distribution` 补零并新增 `inline_state_distribution`（固定 schema，消费者无需补齐缺席键）；`line_count` 改用 `splitlines()` 与 records 同口径（原 `count("\n")` 在 bare CR / U+2028 下会与 records 数不一致）。
3319:1257:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2807:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1932:80:台账逐条携带复合键 `{line_no, sha256_prefix(16 hex), request_id}`。**语义（Codex round-1 LOW-2 修正）**：这是**冻结快照内的 occurrence key**，不是跨文件重排或语义幂等键——台账头部 `dlq_file.sha256`（`3b37460f4215f6ac…`）即快照指纹，`line_no` 在该快照内已单列唯一；`sha256_prefix`（本快照 69 个唯一值，qa_highlight 家族实测同名同 sha 多条）与 `request_id`（仅 25 个唯一值，进程内 contextvars、重启可复用）是**冗余对账/诊断维度**，不是唯一性的必要条件。G4-10 消费前先 diff 头部 sha 即知 DLQ 是否长了新条目；语义级去重不得按本键，须按 `duplicate_clusters` 段（见下）。**语义重复簇（MEDIUM-2 整改）**：按 `{name, episode_body_sha256, group_id}` 聚簇，**6 簇覆盖 29 行**（最大簇 = 同一 session-archive 16 行，`reference_time` 各不相同——同内容反复入队反复超限）。台账 `duplicate_clusters` 段逐簇列 line_nos，records 逐条透传 `reference_time`；G4-10 重放前必须先定去重策略（89 条 budget 修根因后若逐条盲放，将把同内容写入最多 16 遍）。
3320:1258:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2808:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1941:106:- **MEDIUM-2**：`duplicate_clusters` 段 + 逐条 `reference_time`（见 §6）。
3321-1260:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2810:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1948:119:- **新 LOW ×3**：full_verified 长度范围修正为 131–180；台账 `class_distribution`/`recoverability_distribution` 补零并新增 `inline_state_distribution`（固定 schema，消费者无需补齐缺席键）；`line_count` 改用 `splitlines()` 与 records 同口径（原 `count("\n")` 在 bare CR / U+2028 下会与 records 数不一致）。
3322:1265:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2815:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
3323:1266:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2816:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2144:     8	| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
3324:1268:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2818:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2148:    12	| HIGH-3 | **NOT-CLOSED** | 不存在根目录已 exit 2；递归唯一命中、多命中冲突、目录伪命中也通过。但“不可见”仍未闭合：存在但 `chmod 000` 的根会 exit 0 并假判 `unrecoverable`。此外 [`glob + os.path.isfile`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:134)跟随 symlink：根内 `.jsonl` symlink 指向根外 `.txt`、以及 symlink 目录逃逸到根外树，均被判唯一来源并进入 `approximate`。 |
3325:1269:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2819:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2150:    14	| MEDIUM-2 | **CLOSED** | [报告 §6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:78)、[ledger duplicate_clusters](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:60)及逐条 `reference_time` 已落地；6 簇全部逐行对账。 |
3326-1279:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2829:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2636:backend/scripts/census_dead_letter_episodes.py:92:    declared_sha = rec.get("episode_body_sha256", "")
3327:1291:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2841:_bmad-output/审查/codex-review-CARD-G4-9.md:15:   [脚本:163](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:163) 接受任意输出路径，[脚本:281](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:281) 以 `"w"` 无条件截断，未做审查目录 allowlist、`samefile`、symlink 或数据目录隔离。
3328:1299:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2849:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:49:- **MEDIUM-1~3**：episode_body_full 采信通路 / duplicate_clusters 6 簇 29 行 + reference_time 透传 / privacy 字段与 private-only 声明。
3329:1300:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2850:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:61:- **3 新 LOW**：full_verified 长度范围修正 131–180；台账三个 distribution 补零并新增 `inline_state_distribution`；`line_count` 与 records 改用同一 `splitlines()` 口径。
3330:1301:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2851:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:67:- `backend/scripts/census_dead_letter_episodes.py` — 唯一代码产物（只读 census 脚本，纯 stdlib）
3331-1307:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2923:    "recoverability_branch": "unrecoverable"
3332-1308:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2928:    "recoverability_branch": "byte_exact"
3333-1315:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:3110:67ccebe1 docs(census): G4-9 DLQ真实挂载census分诊 92条台账+挂载真相+三态裁定 [BATCH-2026-08-28-第五批 / CARD-G4-9]
3334-1319:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:3514:| LOW：distribution 零键 | **CLOSED** | [固定 schema 生成链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:437)与 [ledger](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:43)均包含 `unexpected/anomaly/unrecoverable: 0`，并新增 inline 三态。 |
3335:1321:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:3534:所以：**冻结的 92 条 ledger 数值可采信；CARD-G4-9 生成器与整卡验收仍被 BLOCKER-1、HIGH-3 阻断。** 本轮未修改仓库或受审数据，未执行破坏性 fixture/G4-10 重放；Graphiti 工具本轮不可用。
3336-1323:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:3547:| LOW：distribution 零键 | **CLOSED** | [固定 schema 生成链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:437)与 [ledger](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:43)均包含 `unexpected/anomaly/unrecoverable: 0`，并新增 inline 三态。 |
3337:1325:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:3567:所以：**冻结的 92 条 ledger 数值可采信；CARD-G4-9 生成器与整卡验收仍被 BLOCKER-1、HIGH-3 阻断。** 本轮未修改仓库或受审数据，未执行破坏性 fixture/G4-10 重放；Graphiti 工具本轮不可用。
3338-1329:./_bmad-output/审查/codex-review-CARD-G4-9.md:61:   真实入口只读复现：对当前 92 行传不存在的 transcripts 根，脚本退出 0 并输出 `byte_exact=4 / unrecoverable=88`。这会误导 G4-10 放弃仍可能存在的来源。
3339-1330:./_bmad-output/审查/codex-review-CARD-G4-9.md:67:   `DeadLetterStore` 可保存 full body（[episode_worker.py:252](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/app/services/episode_worker.py:252)），但脚本完全不读取该字段。含可验证 full body、但无 transcript 的记录仍会被判 `unrecoverable`。当前 92 条该字段确为 0，因此不改变本次数字。
3340:1332:./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:14:CARD-G4-9 round-6 复审（静态审阅 + 只读复算，禁改任何文件）。你 round-5 裁定 3/8 CLOSED，提出 2 BLOCKER / 2 HIGH / 2 MEDIUM / 3 LOW，并明确该阻断与只读 census 卡范围相称（因报告/UAT 承诺纯只读零写入，残留反例能截断或修改本卡正在保护的恢复源）——开发方接受该论证并以 commit 4c125f19 提交整改。请逐条只读复核：
3341:1333:./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:15:1. BLOCKER token 冲突/无 token 扫描前早退 → resolve_group_attribution 重写为先扫描后判定：无条件对每个 token 遍历收集候选进 all_candidate_paths（保护集口径），再做 no_token/token_conflict/scan_errors/stat_failures/unreadable/多命中判定；候选 stat 失败改 exit 2。
3342:1335:./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:20:6. MEDIUM 无 token 判不可恢复 → 改 unverifiable + no_token 标记。
3343-
3344-**Focusing on last 200 log lines**
3345-exec
3346-/bin/zsh -lc 'tail -260 _bmad-output/审查/codex-review-CARD-G4-9-round7.md' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
--
3360-   265	   "group_id": "vault:canvas_vault",
3361-   266	   "source_description": "canvas_learning:conversation_distillation",
3362-
3363-exec
3364:/bin/zsh -lc "nl -ba '_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md' | sed -n '180,200p'; nl -ba '_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md' | sed -n '105,120p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
3365- succeeded in 0ms:
3366-   180	
3367-   181	## §7g Codex round-6 复审整改记录（6/9 CLOSED → 架构级修复 + 全部余项）
3368-   182	
3369-   183	round-6 确认 visibility 优先、fchmod 顺序、no_token 语义、三条 LOW 共 6 项 CLOSED，并揭示了一个**架构层面的根因**：
3370-   184	
3371-   185	> 我的 `--out` 保护集依赖**枚举完整性**——只要某个真实源没被 `os.walk` 看到（不可列举但可穿越的 `0333` 子目录），或 inode 被 A→B→A 换过（QA DB 的 ABA），它就不在集合里，`--out` 指向它仍可截断。这不是补丁能修的，是设计缺陷。
3372-   186	
3373:   187	- **BLOCKER①②的架构级修复**：增加**不依赖枚举的路径层防御**——`--out` 的 `realpath` 不得落在 transcripts 根内（恢复源区域整体禁写）、不得等于任一输入路径的 `realpath`。路径层 + inode 层双保险，任一命中即拒。实测：`0333` 隐藏目录内的 transcript 作 `--out` → exit 2、文件完好（inode 保护集根本没看见它，路径层拦住了）。
3374:   188	- **BLOCKER② 补充修复**：QA DB 的验证 fd 原本验证完即关闭、SQLite 再按路径重开（ABA 可绕）。改为**验证 fd 保持打开**直到 SQLite 连接建立并复核完毕，且连接后二次 `fstat` 该 fd 校验身份未变且 `st_nlink != 0`。本次运行 `file_identity_verified: true`。
3375:   189	- **BLOCKER① 补充修复**：`no_token` 分支原本完全不扫描（`all_candidate_paths=[]`）→ 改为**无论有无 token 都遍历**，所有 `.jsonl` 一律入保护集口径。
3376:   190	- **MEDIUM（证据包漂移）**：`grep-selfattest.txt` 曾停留在 round-4 的脚本 SHA 与旧行号、receipt 未含最新 commit——这是我的疏漏。已重生成（内嵌当前脚本 sha256 + 生成时点声明），receipt 随本轮补链。
3377-   191	- **LOW ×3**：ledger 新增 `attribution_conflict_reason` 自描述（本次 92 条：`no_token` 3 / 其余 89 无冲突）；`json.dumps` 对 lone surrogate 回退 `ensure_ascii=True` 并显式标注，不再整次 census 拒绝；`stat_failures` 分支保留（Codex 确认非额外绕过，仅基本不可达）。
3378-   192	
3379-   193	round-6 整改后第六次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变——六轮整改数字全程未变**。
3380-   105	**一处计数如实变化**：归因冲突 0→3。因为"名字不含 session token"现在被诚实标为"未做归因扫描"，正是那 3 条 callout 记录；它们 inline 全量、不依赖 transcript，仍是可字节级恢复。**三态分布不变**（4/88/0/0）——是标注变诚实，不是结论变化。
--
3396-
3397-exec
3398-/bin/zsh -lc "git rev-parse 5b371253:backend/scripts/census_dead_letter_episodes.py HEAD:backend/scripts/census_dead_letter_episodes.py 5b371253:'_bmad-output/审查/G4-9-evidence/grep-selfattest.txt' HEAD:'_bmad-output/审查/G4-9-evidence/grep-selfattest.txt' 5b371253:'_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' HEAD:'_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
3399- succeeded in 0ms:
3400:git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
3401-3ea39acbdb8fedc08e0576f4dcf6b2ef4cf164eb
3402-3ea39acbdb8fedc08e0576f4dcf6b2ef4cf164eb
3403-7007e4cf371842273fe524677a2f54fc2a690b22
3404-7007e4cf371842273fe524677a2f54fc2a690b22
--
3407-
3408-exec
3409-/bin/zsh -lc 'git merge-base --is-ancestor 4c125f19 5b371253' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
3410- succeeded in 0ms:
3411:git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
3412-
3413-exec
3414-/bin/zsh -lc 'git status --porcelain=v1' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
3415- succeeded in 0ms:
3416:git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
3417-?? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round7.md"
3418-
3419-**Planning verification of official web docs**
3420-web search: 
--
3428-**Clarifying search tool limitations**
3429-**Documenting snapshot and classification details**
3430-**Identifying new blocker cases**
3431-**Identifying URI carryover blocker**
3432:**Designing path symlink matrix**
3433-**Assessing new path containment blockers**
3434-**Summarizing rejection with closure recommendations**
3435-**Planning evaluation of closure hypothesis**
3436-codex
3437:交叉核验已收束：冻结台账与 receipt 链是可采信的，但生成器安全闭包仍失败。尤其当前卷上已只读确认 `/Users/.../projects` 与 `/users/.../projects` 是同一目录，而 `realpath` 字符串不同，形成无需竞态的根内写入绕过；QA 的 rename 型 ABA 与 round-6 未修的 URI 问题也仍成立。正在整理最终逐项矩阵与验收边界。
3438-mcp: sequential-thinking/sequentialthinking started
3439-mcp: sequential-thinking/sequentialthinking (completed)
3440-mcp: sequential-thinking/sequentialthinking started
3441-mcp: sequential-thinking/sequentialthinking (completed)
--
3444-  ✓ 核对 checkout、commit/receipt 链及 round-6 基线
3445-  ✓ 静态审阅五项修复及生产入口控制流
3446-  ✓ 设计并只读验证路径、inode、TOCTOU 新反例
3447-  ✓ 从原始工件独立复算台账与证据包指标
3448:  ✓ 交叉核验后给出逐项 CLOSED/NOT-CLOSED 与总裁定
3449-**Drafting final Chinese citations**
3450-**Including relevant rollout IDs in citations**
3451-**Defining base file paths**
3452:**Summarizing symlink path cases**
3453:**Planning SQLite URI handling**
3454-**Identifying ledger table blockers and risks**
3455-**Confirming macOS case-insensitive file handling**
3456-**Verifying Path.resolve case behavior on macOS**
3457-**Analyzing path guard limitation with hardlinks**
3458-**Confirming output truncation behavior**
3459-**Planning detailed metric reporting format**
3460-**Confirming memory skill as guidance**
3461-codex
3462:总裁定：**仍阻断，CARD-G4-9 round-7 不可验收。**
3463-
3464:冻结台账数字可采信，但生成器的“纯只读、恢复源区域零写入”安全闭包仍失败。按开发方 5 个编号计：**2 CLOSED / 2 NOT-CLOSED / 1 PARTIAL**；拆成 6 个原子声明则是 **3 CLOSED / 3 NOT-CLOSED**。
3465-
3466-审阅锚点：`HEAD=4ba4f847fa3ad83d136d3a40fcc5448b25c54ba5`，直接父提交为 `5b3712537ef5be91eda18e2a9eaf2fd3d5e03ef5`。
3467-
3468-## 逐项裁定
3469-
3470-| 项目 | 裁定 | 结果 |
3471-|---|---|---|
3472:| 1. transcripts 路径层防御 | **NOT-CLOSED · BLOCKER** | 一次性 `realpath` 字符串检查仍受 hardlink、大小写别名和父目录换链影响。[路径检查](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:421)；最终仍原路径 `open`/`ftruncate`，[写入入口](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:733)。 |
3473:| 2. QA DB fd 保持及复核 | **NOT-CLOSED · BLOCKER** | 验证 fd=A 虽保持打开，SQLite 仍按 pathname 另开连接；rename 型 A→B→A 可令连接读 B，而两次复核都看到 A。[QA 打开链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:277)。 |
3474-| 3. no_token 也遍历 | **CLOSED（狭义）** | 现在先无条件遍历、收集可见 `.jsonl`，再于 no_token 分支返回。[遍历](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:201)。但它不覆盖不可枚举 inode，因此不能补救项目 1。 |
3475-| 4. self-attest + receipt | **CLOSED（当前仓库内）** | self-attest 内嵌脚本 SHA `533d0d4c…e3585` 与实际一致；脚本/self-attest/ledger 从 `5b371253` 到 HEAD blob 均未变。[self-attest](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:1)、[receipt](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt:12)。 |
3476-| 5a. attribution_conflict_reason | **CLOSED** | 字段已序列化不同原因；冻结台账三条均为 `no_token`。[生成逻辑](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:616)、[台账实例](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:202)。 |
3477-| 5b. lone-surrogate 回退 | **NOT-CLOSED · LOW** | `json.dumps(..., ensure_ascii=False)` 会正常返回含 surrogate 的 `str`；异常发生在后续 UTF-8 `write/print`，不在当前 `try` 内。[回退代码](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:725)。`--out` 分支还会先 `ftruncate`，再写出失败。 |
--
3479-## 路径反例矩阵
3480-
3481-| 反例 | 结果 |
3482-|---|---|
3483:| 根外稳定 symlink → 根内文件 | **CLOSED**：`realpath` 命中；final symlink 还受 `O_NOFOLLOW` 约束。 |
3484-| 根外 hardlink → 可枚举 transcript | **CLOSED**：枚举所得 inode 会在最终 `fstat` 命中。 |
3485-| 根外 hardlink → `0333` 隐藏目录内 transcript | **NOT-CLOSED**：hardlink 的 `realpath` 仍在根外；隐藏 inode 未被枚举，最终可被截断。 |
3486:| transcripts 根是稳定 symlink | **CLOSED**：两侧稳定 `realpath` 指向相同真实根。 |
3487-| transcripts 根在检查后 retarget | **NOT-CLOSED**：未持有/复核根目录 fd，检查绑定旧目标，扫描或写入可使用新目标。 |
3488-| 相对路径与 `..` | **CLOSED**：无竞态、大小写一致时会被正规化。 |
3489:| 检查后仅把 basename 换成 symlink | **CLOSED**：最终 `O_NOFOLLOW` 拒绝。 |
3490:| 检查后换父目录 symlink或把 basename 换成 hardlink | **NOT-CLOSED**：`O_NOFOLLOW` 只约束最终 symlink，不约束父组件或 hardlink。 |
3491-| 大小写别名 | **NOT-CLOSED、无需竞态**：本机只读复算确认 `/Users/Heishing/.claude/projects` 与 `/users/heishing/.claude/projects` `samefile=True`，但两者 `realpath` 字符串不同，现有 prefix guard 返回 `False`。 |
3492-
3493-## QA DB 仍未绑定实际连接对象
3494-
--
3500-4. B→stashB，A→原路径；
3501-5. 路径 `stat` 与验证 fd `fstat` 均为 A，且 rename 不会令 A 的 `st_nlink` 变 0；
3502-6. 查询实际仍来自 B。
3503-
3504:因此二次 `fstat` 只证明“验证 fd 仍指向 A”，没有证明 SQLite connection 指向 A。
3505-
3506:此外，round-6 已指出的 URI BLOCKER **完全未修**：[line 291](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:291)仍直接拼接 `file:{db_path}?mode=ro`。SQLite 官方规定普通文件名里的 `?/#` 必须转义，fragment 会被忽略；所以 `/x/qa#tag` 可被解析成另一文件且吞掉 `mode=ro`。[SQLite URI 规则](https://www.sqlite.org/uri.html)、[Python sqlite3 URI 行为](https://docs.python.org/3/library/sqlite3.html#how-to-work-with-sqlite-uris)。
3507-
3508-## 台账独立复算：PASS
3509-
3510:未 import 被审生成器，直接从 live DLQ exact bytes 重写严格 LF/UTF-8/JSON、分类、SHA/长度、分组和聚簇计算：
3511-
3512-- SHA-256：`3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590`
3513-- `99,915 bytes`；92 records；unparseable 0
3514-- class：`89 / 2 / 1`，unexpected 0
--
3520-汇总与冻结工件一致：[ledger:40](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:40)。
3521-
3522-## 新发现与限制
3523-
3524:- **BLOCKER**：当前大小写不敏感卷上的 case-only 根别名是无需竞态的实际绕过。
3525:- **MEDIUM**：`--out` 采用原地 `ftruncate` 后写入，没有临时文件、atomic replace、`fsync` 或并发锁；崩溃、ENOSPC、surrogate 或并发运行可留下空/部分/混写台账。
3526-- **LOW**：receipt 使用当前仓库唯一可解析的 8 位缩写，不是跨仓可独立验证的完整 40-hex OID。
3527-- before/after shasum 与当前 bytes 一致，但静态复审不能证明两份清单真实采集时序。
3528-
3529:本轮未创建 symlink/hardlink/竞态 fixture，未读取 transcript 正文或 Vault；只读取任务范围内 DLQ exact bytes及 transcript 元数据。工作树仍只有开始前已存在的未跟踪 round-7 文件，未触碰任何文件。`graphiti-canvas` 本环境未暴露，故本轮 Graphiti 搜索明确为不可执行；Sequential Thinking 已完成。
3530-
3531:**验收结论：现有 92 条冻结 ledger 可以采信；CARD-G4-9 生成器与 UAT 的纯只读安全声明不可验收。**
3532-
3533-
3534-tokens used
3535-159,964
3536:总裁定：**仍阻断，CARD-G4-9 round-7 不可验收。**
3537-
3538:冻结台账数字可采信，但生成器的“纯只读、恢复源区域零写入”安全闭包仍失败。按开发方 5 个编号计：**2 CLOSED / 2 NOT-CLOSED / 1 PARTIAL**；拆成 6 个原子声明则是 **3 CLOSED / 3 NOT-CLOSED**。
3539-
3540-审阅锚点：`HEAD=4ba4f847fa3ad83d136d3a40fcc5448b25c54ba5`，直接父提交为 `5b3712537ef5be91eda18e2a9eaf2fd3d5e03ef5`。
3541-
3542-## 逐项裁定
3543-
3544-| 项目 | 裁定 | 结果 |
3545-|---|---|---|
3546:| 1. transcripts 路径层防御 | **NOT-CLOSED · BLOCKER** | 一次性 `realpath` 字符串检查仍受 hardlink、大小写别名和父目录换链影响。[路径检查](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:421)；最终仍原路径 `open`/`ftruncate`，[写入入口](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:733)。 |
3547:| 2. QA DB fd 保持及复核 | **NOT-CLOSED · BLOCKER** | 验证 fd=A 虽保持打开，SQLite 仍按 pathname 另开连接；rename 型 A→B→A 可令连接读 B，而两次复核都看到 A。[QA 打开链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:277)。 |
3548-| 3. no_token 也遍历 | **CLOSED（狭义）** | 现在先无条件遍历、收集可见 `.jsonl`，再于 no_token 分支返回。[遍历](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:201)。但它不覆盖不可枚举 inode，因此不能补救项目 1。 |
3549-| 4. self-attest + receipt | **CLOSED（当前仓库内）** | self-attest 内嵌脚本 SHA `533d0d4c…e3585` 与实际一致；脚本/self-attest/ledger 从 `5b371253` 到 HEAD blob 均未变。[self-attest](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:1)、[receipt](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt:12)。 |
3550-| 5a. attribution_conflict_reason | **CLOSED** | 字段已序列化不同原因；冻结台账三条均为 `no_token`。[生成逻辑](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:616)、[台账实例](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:202)。 |
3551-| 5b. lone-surrogate 回退 | **NOT-CLOSED · LOW** | `json.dumps(..., ensure_ascii=False)` 会正常返回含 surrogate 的 `str`；异常发生在后续 UTF-8 `write/print`，不在当前 `try` 内。[回退代码](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:725)。`--out` 分支还会先 `ftruncate`，再写出失败。 |
--
3553-## 路径反例矩阵
3554-
3555-| 反例 | 结果 |
3556-|---|---|
3557:| 根外稳定 symlink → 根内文件 | **CLOSED**：`realpath` 命中；final symlink 还受 `O_NOFOLLOW` 约束。 |
3558-| 根外 hardlink → 可枚举 transcript | **CLOSED**：枚举所得 inode 会在最终 `fstat` 命中。 |
3559-| 根外 hardlink → `0333` 隐藏目录内 transcript | **NOT-CLOSED**：hardlink 的 `realpath` 仍在根外；隐藏 inode 未被枚举，最终可被截断。 |
3560:| transcripts 根是稳定 symlink | **CLOSED**：两侧稳定 `realpath` 指向相同真实根。 |
3561-| transcripts 根在检查后 retarget | **NOT-CLOSED**：未持有/复核根目录 fd，检查绑定旧目标，扫描或写入可使用新目标。 |
3562-| 相对路径与 `..` | **CLOSED**：无竞态、大小写一致时会被正规化。 |
3563:| 检查后仅把 basename 换成 symlink | **CLOSED**：最终 `O_NOFOLLOW` 拒绝。 |
3564:| 检查后换父目录 symlink或把 basename 换成 hardlink | **NOT-CLOSED**：`O_NOFOLLOW` 只约束最终 symlink，不约束父组件或 hardlink。 |
3565-| 大小写别名 | **NOT-CLOSED、无需竞态**：本机只读复算确认 `/Users/Heishing/.claude/projects` 与 `/users/heishing/.claude/projects` `samefile=True`，但两者 `realpath` 字符串不同，现有 prefix guard 返回 `False`。 |
3566-
3567-## QA DB 仍未绑定实际连接对象
3568-
--
3574-4. B→stashB，A→原路径；
3575-5. 路径 `stat` 与验证 fd `fstat` 均为 A，且 rename 不会令 A 的 `st_nlink` 变 0；
3576-6. 查询实际仍来自 B。
3577-
3578:因此二次 `fstat` 只证明“验证 fd 仍指向 A”，没有证明 SQLite connection 指向 A。
3579-
3580:此外，round-6 已指出的 URI BLOCKER **完全未修**：[line 291](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:291)仍直接拼接 `file:{db_path}?mode=ro`。SQLite 官方规定普通文件名里的 `?/#` 必须转义，fragment 会被忽略；所以 `/x/qa#tag` 可被解析成另一文件且吞掉 `mode=ro`。[SQLite URI 规则](https://www.sqlite.org/uri.html)、[Python sqlite3 URI 行为](https://docs.python.org/3/library/sqlite3.html#how-to-work-with-sqlite-uris)。
3581-
3582-## 台账独立复算：PASS
3583-
3584:未 import 被审生成器，直接从 live DLQ exact bytes 重写严格 LF/UTF-8/JSON、分类、SHA/长度、分组和聚簇计算：
3585-
3586-- SHA-256：`3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590`
3587-- `99,915 bytes`；92 records；unparseable 0
3588-- class：`89 / 2 / 1`，unexpected 0
--
3594-汇总与冻结工件一致：[ledger:40](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:40)。
3595-
3596-## 新发现与限制
3597-
3598:- **BLOCKER**：当前大小写不敏感卷上的 case-only 根别名是无需竞态的实际绕过。
3599:- **MEDIUM**：`--out` 采用原地 `ftruncate` 后写入，没有临时文件、atomic replace、`fsync` 或并发锁；崩溃、ENOSPC、surrogate 或并发运行可留下空/部分/混写台账。
3600-- **LOW**：receipt 使用当前仓库唯一可解析的 8 位缩写，不是跨仓可独立验证的完整 40-hex OID。
3601-- before/after shasum 与当前 bytes 一致，但静态复审不能证明两份清单真实采集时序。
3602-
3603:本轮未创建 symlink/hardlink/竞态 fixture，未读取 transcript 正文或 Vault；只读取任务范围内 DLQ exact bytes及 transcript 元数据。工作树仍只有开始前已存在的未跟踪 round-7 文件，未触碰任何文件。`graphiti-canvas` 本环境未暴露，故本轮 Graphiti 搜索明确为不可执行；Sequential Thinking 已完成。
3604-
3605:**验收结论：现有 92 条冻结 ledger 可以采信；CARD-G4-9 生成器与 UAT 的纯只读安全声明不可验收。**
3606-
3607-
3608-
3609-**Assessing round7 QA DB blockers closure**
3610-**Identifying discrepancies in round7 blocker summaries**
3611-**Highlighting unresolved QA DB issues from round7**
3612-**Reevaluating QA issue severity and evidence validity**
3613:**Analyzing SQLite URI path parsing and mode effects**
3614-**Inspecting ledger file structure and hidden files**
3615-**Planning ledger metadata inspection without cache**
3616-**Implementing Python no-cache JSON parsing**
3617-codex
3618:初步静态阅读已发现一个必须单独核对的边界：`O_EXCL` 确实让“预置同名 symlink”变成拒绝服务而非跟随写入，但它只保护 `open(tmp)` 这一刻；后续 `os.replace(tmp_path, out_path)` 仍重新按路径解析源、目标，且目前不在异常清理区。接下来我会把“既有源不被截断”和“发布对象/落点未被换链”分开裁定，避免把两种性质混为一谈。
3619-exec
3620-/bin/zsh -lc "jq '{dlq_file,total_lines,total_records,unparseable_lines,class_distribution,recoverability_distribution,inline_state_distribution,unrecoverable_list,unverifiable_list,attribution_conflicts,duplicate_clusters,qa_metrics_probe}' '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json'
3621-stat -f 'ledger_mode=%Lp ledger_size=%z ledger_inode=%d:%i' '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json'
3622-shasum -a 256 backend/data/dead_letter_episodes.jsonl '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' backend/scripts/census_dead_letter_episodes.py
3623:rg --files --hidden -g '.*.census-tmp-*' -g '*.census-tmp-*' -g '"'!node_modules'"' -g '"'!.git'"' .
3624-git ls-tree -l HEAD -- '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' backend/data/dead_letter_episodes.jsonl backend/scripts/census_dead_letter_episodes.py
3625-git rev-parse f389980c:backend/scripts/census_dead_letter_episodes.py HEAD:backend/scripts/census_dead_letter_episodes.py f389980c:'_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' HEAD:'_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
3626- succeeded in 13ms:
3627:git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
3628-6f264b74fcefe608311895e25f059d7fc34305ea
3629-6f264b74fcefe608311895e25f059d7fc34305ea
3630-9937a25c7af4d2b57dbb4593a50c4ae92189419d
3631-9937a25c7af4d2b57dbb4593a50c4ae92189419d
--
3633-**Verifying cross-worktree file access**
3634-**Planning ledger metadata verification**
3635-**Assessing ledger file permission discrepancy**
3636-exec
3637:/bin/zsh -lc "rg -n \"只读|零写|read.?only|O_EXCL|atomic|原子|0600|tmp|surrogate|ftruncate|round-7|round-8|f389980c|92|89/2/1|4/88\" '_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md' '_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md' '_bmad-output/审查/G4-9-evidence/grep-selfattest.txt' '_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt'
3638:nl -ba '_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md' | sed -n '1,180p'
3639-nl -ba '_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md' | sed -n '1,250p'
3640-nl -ba '_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt' | sed -n '1,80p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
3641- succeeded in 0ms:
3642-_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt:15:f389980c  CARD-G4-9 round-7 架构级修复（消除截断动作；本 receipt 当前版所描述的 commit）
3643-_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:1:== CARD-G4-9 只读自证（round-7 整改版）==
3644-_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:3:生成时点: round-7 整改后（随每轮整改重生成）
3645-_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:24:--- (4) ⛔ 无任何截断调用（round-7 架构整改：从不截断既有文件）:
3646-_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:25:grep "os.ftruncate|.truncate(" 命中: 0 ✓（'ftruncate' 字样仅出现在说明注释中，非调用）
3647:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:26:--- (5) 唯一写出口 = O_EXCL 新建临时文件 → fsync → os.replace 原子替换:
3648-_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:27:779:        # round-7 架构整改: 不再截断既有文件 —— 同目录 O_EXCL 新建临时文件 →
3649:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:28:780:        # 写 → fsync → os.replace 原子替换。O_EXCL 保证目标是本进程新建的对象，
3650:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:29:785:        tmp_path = out_path.with_name(f".{out_path.name}.census-tmp-{os.getpid()}")
3651:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:30:787:            tmp_fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
3652:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:31:789:            print(f"临时台账文件无法新建（O_EXCL）: {tmp_path} ({e})", file=sys.stderr)
3653:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:32:795:                os.fsync(tmp_fd)
3654:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:33:804:        os.replace(tmp_path, out_path)
3655:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:39:460:        # round-7 BLOCKER 整改: 用 **inode 身份逐级比较**（_path_is_within），
3656:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:6:scope: "BATCH-2026-08-28-第五批 / CARD-G4-9 — live DLQ 92 条只读 census：分类/SHA 对账/可恢复性三态/挂载真相，产出 G4-10 交接台账"
3657:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:13:> 这张卡**没有修任何东西，也没有恢复任何数据**——它是一次"清点尸体"的只读普查：
3658:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:14:> 线上 Graphiti 写入失败后落进死信文件的 92 条记录，逐条查清"是什么死的、还能不能救、去哪里救"，
3659:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:19:1. **92 条死信全部查清、零"待定"**：89 条是"内容太长超过本地模型 16384 token 上限"（未修，根因归 G4-10）；2 条是 5 月 14 日的 schema 冲突、1 条是旧 group_id 冒号格式——这 3 条的根因**当天之后就已修复**，不会再新增。
3660:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:27:| 全程零写入（裁判判据 e） | 运行前后 四份 DLQ 文件 + qa_metrics.db 的 sha256 **逐字节不变**（diff 为空 → PASS） | `_bmad-output/审查/G4-9-evidence/shasums-before.txt` / `shasums-after.txt` |
3661:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:28:| 脚本只读自证（判据 a） | import 行全 stdlib；neo4j/graphiti/bolt/app. import **0 命中**；`--apply` 定义 **0 命中**；写模式 open 仅台账 `--out` 1 处 | `G4-9-evidence/grep-selfattest.txt` |
3662:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:29:| live 挂载真相（判据 c） | 容器内 `sha256sum /app/data/dead_letter_episodes.jsonl` = 宿主 live 地址同值（92 行，`3b37460f…`）；compose :206-212 遮蔽史入报告 §1 | `G4-9-evidence/container-sha-check.txt` + 报告 §1 |
3663:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:31:| inline 完整性 + SHA 对账（判据 b） | 92/92 重算 sha256 对账：4 条 full_verified、88 条 truncated_prefix（`to_dict()` 的 `[:200]` 截断，`episode_worker.py:107`）、**0 条 anomaly** | 台账 JSON 逐条 `inline_state`/`sha_check` |
3664:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:32:| 源指针核销（判据 b，qa_metrics.db 只读 mode=ro） | `qa_error_logs` **0 行** → 0/92 可经 qa_metrics.db 溯源（诚实记录）；附加核销：llm_call_logs.db 无正文、outbox 空、episode_body_full 0 条；**有效源指针 = request_id 组内 session 归因 → 7 个 transcript 全部在盘实测存在** | 报告 §4 + 台账 `qa_metrics_probe` |
3665:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:34:| G4-10 稳定键（判据 d） | 逐条复合键 `{line_no, sha256_prefix, request_id}` + 台账头部冻结文件 sha；request_id 92 条仅 25 唯一值的实测证明单列不可作键 | 报告 §6 + 台账 `records[].stable_key` |
3666:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:35:| Codex 独立审查 round-1 | **BLOCKED**（3 BLOCKER：--out 可截断输入 / 快照不原子 / 交付物未冻结；3 HIGH：inline 判定 fail-open / request_id 归因传染 / transcript 归因折叠；3 MEDIUM + 4 LOW。同时确认：**当前 92 条数字逐项 0 mismatch**、class/三态/家族计数全对） | `_bmad-output/审查/codex-review-CARD-G4-9.md` |
3667:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:37:| Codex 复审 round-2 | **仍阻断**（10/13 CLOSED；BLOCKER-1/HIGH-1/HIGH-3 未真正闭合 + 3 新 LOW）。同时独立复算确认：67ccebe1 冻结生效、92 条数字与 6/29 重复簇全部可复算 | `_bmad-output/审查/codex-review-CARD-G4-9-round2.md`（codex 被 cyber 误拦，内容由 stdout 抢救存档） |
3668:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:46:| round-6 findings 整改 | **架构级修复 + 6 项**：新增不依赖枚举的**路径层防御**（--out 禁落 transcripts 根内 / 禁等于任一输入 realpath）、QA DB 验证 fd 保持打开至复核完毕、no_token 亦扫描、证据包重生成、ledger 冲突原因自描述、lone surrogate 回退。反例实测：0333 隐藏目录内 transcript 作 --out → exit 2 完好 | 报告 §7g |
3669:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:47:| Codex 复审 round-7 | **关键裁定分离**："92 条冻结 ledger **可以采信**；生成器与 UAT 的纯只读安全声明不可验收"——卡面 census 判据已满足，阻断全在工具安全承诺侧。1 BLOCKER（大小写别名根，无需竞态）+ 4 项路径 TOCTOU + 1 MEDIUM（非原子写）+ 2 LOW | `_bmad-output/审查/codex-review-CARD-G4-9-round7.md` |
3670:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:48:| round-7 findings 整改 | **架构级第二次修复**：写出改 O_EXCL 临时文件+fsync+os.replace（**全文再无 ftruncate 调用**），五项绕过整类失效；containment 改 inode 逐级比较（normcase 在 POSIX 是恒等函数，我的假设错了）；扫描受阻直接拒绝写出。实测：根外 hardlink 指向根内 transcript 作 --out → 源内容完好 | 报告 §7h |
3671:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:49:| 独立 Workflow 4-agent 复核 | G4-9 数字 agent：92 条重算 **0 mismatch**（class/inline/三态/25 request_id/7 transcript 在盘/台账 sha 全 CONFIRMED，仅 2 处描述区间 REFUTED 已修正）；只读契约 agent：与 Codex 同源的 3 条 blocker（已随上整改） | Workflow wf_737b1a95-20b journal |
3672:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:54:- **BLOCKER-2 快照不原子**：records 与头部 sha 来自两次读取。整改：单次 read_bytes()，头部与逐条同源同字节。
3673:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:62:整改后全量重跑：92 条数字与整改前**逐项一致**（4/88/0、89/2/1、冲突 0、unparseable 0）——整改只收紧契约与通用鲁棒性，不改变本次 census 结论。
3674:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:73:round-2 整改后再次全量重跑：92 条、4/88/0、89/2/1、6 簇 29 行、shasum 不变——**数字全程未变**。
3675:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:79:- **BLOCKER-1 仍 PARTIAL**：① 保护集漏了**归因到的 transcript**——`--out` 指向它会截断恢复源；② check-then-open 的 **TOCTOU** 仍在。→ ① transcript 写前并入保护集；② 改 `O_NOFOLLOW` 打开且**不带 O_TRUNC**，对实际 fd `fstat` 校验后才 `ftruncate`。反例实测：exit 2、transcript 完好。
3676:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:84:round-3 整改后第三次全量重跑：**92 条、4/88/0、89/2/1、6/29、shasum 不变——三轮整改数字全程未变**，改的全是通用鲁棒性与路径安全。
3677:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:95:round-4 整改后第四次全量重跑：**92 条、4/88/0（unverifiable 0）、89/2/1、6/29、shasum 不变——四轮整改数字全程未变**。
3678:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:104:- **`fchmod` 排在碰撞检查之前**：`--out` 指向受保护的只读输入时，会先把它的权限从 644 改成 600 才发现碰撞——字节没丢但输入被改了。→ 碰撞检查前移。
3679:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:105:- **其余 5 项**：QA DB 特殊文件门、无 token 归 `unverifiable`、单独换行算 1 空行、strict encode 堵住 lone surrogate 伪造 `full_verified`、`bool` 不再通过长度门。
3680:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:107:**一处计数如实变化**：归因冲突 0→3。因为"名字不含 session token"现在被诚实标为"未做归因扫描"，正是那 3 条 callout 记录；它们 inline 全量、不依赖 transcript，仍是可字节级恢复。**三态分布不变**（4/88/0/0）——是标注变诚实，不是结论变化。
3681:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:109:round-5 整改后第五次全量重跑：**92 条、4/88/0/0、89/2/1、6/29、shasum 不变——五轮整改数字全程未变**。
3682:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:119:round-6 整改后第六次全量重跑：**92 条、4/88/0/0、89/2/1、6/29、shasum 不变——六轮整改数字全程未变**。
3683:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:121:## 🔧 Codex round-7 复审整改记录（关键裁定分离 + 架构级第二次修复）
3684:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:123:round-7 把结论分成了两半，这个区分很重要：
3685:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:125:> **「现有 92 条冻结 ledger 可以采信；生成器与 UAT 的纯只读安全声明不可验收。」**
3686:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:127:也就是说：这张卡要交付的 census 结论（92 条的分类、对账、三态、挂载真相、稳定键、运行零写入）**已经过关**；卡住的是"这个脚本作为工具，其只读承诺是否经得起敌意输入"。
3687:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:130:- **五项绕过共用一个根源**：它们都依附于"截断一个已存在的文件"这个动作。改成「新建临时文件 → 写 → fsync → 原子替换」后，脚本**全文再没有任何截断调用**，这一整类绕过连同"崩溃留下半个台账"的风险一起消失。实测：拿一个指向恢复源的 hardlink 当 `--out`，台账正常写出，而**源文件内容一个字节没变**。
3688:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:133:round-7 整改后第七次全量重跑：**92 条、4/88/0/0、89/2/1、6/29、shasum 不变、台账 0600、无临时文件残留——七轮整改数字全程未变**。
3689:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:137:- `backend/scripts/census_dead_letter_episodes.py` — 唯一代码产物（只读 census 脚本，纯 stdlib）
3690:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:139:- `_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json` — 92 条逐条台账（G4-10 消费）
3691-_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:4:> **性质**: 纯只读 census。0 写入、0 重放、0 业务代码改动。唯一代码产物 = `backend/scripts/census_dead_letter_episodes.py`。
3692-_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:6:> **台账**: `_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json`（92 条逐条，G4-10 消费）
3693-_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:18:→ 3b37460f4215f6ac...ef3ba590（92 行）— 与宿主 live 地址逐字节一致
3694-_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:23:| **live**（权威） | `…/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl` | **92** | `3b37460f4215f6ac` | 2026-08-11 22:01 (+0800) | 容器 `/app/data` 经 `./backend:/app` 挂载即此文件；census 对象 |
--
3700-_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:62:  - `backend/data/outbox/`：**空目录**（A7 outbox 只接 enqueue 失败，本 92 条全部是 enqueue 成功、处理失败，不经 outbox）；
3701-_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:75:**不可恢复清单（显式成段）**：本次 census 裁定不可恢复条目 **0 条**；三态裁定覆盖 92/92，**"待定"0 条**。
3702-_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:93:| 容器内 sha 实测 | 92 行、sha 与宿主 live 地址一致（`container-sha-check.txt`） |
3703-_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:94:| class 偏差 | 无（89/2/1 与勘探预期一致，脚本 `class_deviation` 字段为空） |
3704:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:101:- **BLOCKER-2（快照不原子）**：DLQ 单次 `read_bytes()`，头部 sha256/line_count 与逐条 records 派生自同一份内存字节；mtime 显式标注为 stat 参考值。
3705:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:104:- **HIGH-2（request_id fail-open）**：分组键改 `(类型名, 值)`；缺失/None 按 line_no 单条成组零传染；组内多 token 前缀一致门，冲突记 `attribution_conflict` 拒绝采信（现网 92 条 0 冲突）。
3706-_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:111:整改后全量重跑：**92 条数字与整改前逐项一致**（class 89/2/1、三态 4/88/0、归因冲突 0、unparseable 0），重复簇 6/29 行与 Codex 独立复算吻合。另有独立 Workflow 4-agent 复核（92 条重算 0 mismatch、7 transcript 在盘实测、台账 sha 一致）交叉确认。
3707-_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:122:round-2 整改后再次全量重跑：92 条、class 89/2/1、三态 4/88/0、重复簇 6/29、shasum 不变——**数字仍逐项一致**，整改只收紧通用鲁棒性。
3708:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:143:- **BLOCKER-1 残留两条绕过**：① `protected_paths` 未含**归因到的 transcript**，`--out=<唯一 transcript>` 会截断恢复源；② check-then-open 的 **TOCTOU** 仍在（检查后、打开前把 --out 换成指向 DLQ 的链接）。**整改**：① 写出前把全部 `transcript_paths` 并入保护集；② 改 `os.open(O_WRONLY|O_CREAT|O_NOFOLLOW)` **不带 O_TRUNC** 打开 → 对**实际 fd** `fstat` 校验 inode → 通过才 `ftruncate`，检查与写入作用于同一 fd，替换攻击无效。反例实测：`--out` 指向唯一 transcript → exit 2、transcript sha 不变。
3709-_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:149:round-3 整改后第三次全量重跑：92 条、class 89/2/1、三态 4/88/0、重复簇 6/29、shasum 不变——**三轮整改数字全程未变**，改的全是通用鲁棒性与路径安全。
3710-_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:163:round-4 整改后第四次全量重跑：**92 条、class 89/2/1、三态 4/88/0（unverifiable 0）、重复簇 6/29、shasum 不变——四轮整改数字全程未变**。
3711:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:172:- **HIGH②（`fchmod` 先于 protected-id 检查）**：`--out` 指向受保护的 0644 输入时，会**先把只读输入权限改成 0600** 再拒绝——字节没截断但输入已被修改。**整改**：碰撞检查前移到 `fchmod` 之前。实测：mode 644 → 644 不变。
3712-_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:175:- **LOW ×3**：单独 `b"\n"` 现算 1 个空行（实测 `line_count=1`）；`errors="replace"` 改 **strict encode**（JSON escaped lone surrogate 不能再构造假 `full_verified`）；`bool` 是 `int` 子类 —— `episode_body_length=True` 现被长度门拒绝（实测判 anomaly）。
3713-_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:177:**归因冲突计数由 0 变为 3（如实说明）**：round-5 起"名字不含 session token"被诚实标记为 `no_token`（未做归因扫描），命中的正是 3 条 `callout_annotation` 记录。它们 inline 正文全量、sha 对账通过，**不依赖 transcript**，故仍判 `byte_exact`——三态分布不变（4/88/0/0），88 条 approximate 仍全部为唯一 transcript 命中。这是标注口径变诚实，不是结论变化。
3714-_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:179:round-5 整改后第五次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变——五轮整改数字全程未变**。
3715-_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:191:- **LOW ×3**：ledger 新增 `attribution_conflict_reason` 自描述（本次 92 条：`no_token` 3 / 其余 89 无冲突）；`json.dumps` 对 lone surrogate 回退 `ensure_ascii=True` 并显式标注，不再整次 census 拒绝；`stat_failures` 分支保留（Codex 确认非额外绕过，仅基本不可达）。
3716-_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:193:round-6 整改后第六次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变——六轮整改数字全程未变**。
3717-_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:195:## §7h Codex round-7 复审整改记录（关键裁定分离 + 架构级第二次修复）
3718-_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:197:round-7 给出了本卡最重要的一次裁定分离：
3719:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:199:> **「现有 92 条冻结 ledger 可以采信；CARD-G4-9 生成器与 UAT 的纯只读安全声明不可验收。」**
3720:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:201:即：卡面的 census 判据（分类/对账/三态/挂载真相/稳定键/shasum 不变）已满足且被独立复算确认；阻断项全部落在"生成器作为工具的只读安全承诺"上。逐条整改：
3721:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:204:- **NOT-CLOSED ×4（根外 hardlink 指向隐藏目录内 transcript / 根 retarget TOCTOU / 检查后换父目录 symlink 或 basename hardlink）+ MEDIUM（非原子写）**：这五项依附于同一个动作——**截断一个已存在的文件**。**架构级修复**：写出改为「同目录 `O_EXCL` 新建临时文件 → 写 → `fsync` → `os.replace` 原子替换」，**全文再无任何 `ftruncate` 调用**。`O_EXCL` 保证写入目标是本进程新建的对象，因此"把 `--out` 换成指向恢复源的 hardlink / 父目录 symlink / 大小写别名"整类绕过失效；`os.replace` 同时消除崩溃/ENOSPC 留下部分台账的风险。实测：根外 hardlink 指向根内 transcript 作 `--out` → 台账正常写出而**源文件内容完好**（`os.replace` 只重绑定该名字，不触碰底层 inode）。
3722-_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:206:- **LOW（lone surrogate 回退失效）**：异常发生在后续 `write`，不在原 `try` 内。**整改**：`json.dumps` 后立即 `.encode("utf-8")` 探测，编码错误在写出前暴露并回退 `ensure_ascii=True`。
3723-_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:209:round-7 整改后第七次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变、台账 mode 0600、无临时文件残留——七轮整改数字全程未变**。
3724-     1	---
3725-     2	type: uat
3726:     3	title: "UAT · CARD-G4-9 DLQ 真实挂载 census 分诊（2026-08-28）"
3727-     4	date: 2026-08-28
3728-     5	status: awaiting_user
3729-     6	scope: "BATCH-2026-08-28-第五批 / CARD-G4-9 — live DLQ 92 条只读 census：分类/SHA 对账/可恢复性三态/挂载真相，产出 G4-10 交接台账"
3730-     7	worktree: "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census"
3731-     8	---
3732-     9	
3733:    10	# UAT · CARD-G4-9 DLQ 真实挂载 census 分诊
3734-    11	
3735-    12	> [!info]+ 你不需要碰命令行 — 全部技术验证我已代跑（结果见下）
3736-    13	> 这张卡**没有修任何东西，也没有恢复任何数据**——它是一次"清点尸体"的只读普查：
3737-    14	> 线上 Graphiti 写入失败后落进死信文件的 92 条记录，逐条查清"是什么死的、还能不能救、去哪里救"，
--
3754-    31	| inline 完整性 + SHA 对账（判据 b） | 92/92 重算 sha256 对账：4 条 full_verified、88 条 truncated_prefix（`to_dict()` 的 `[:200]` 截断，`episode_worker.py:107`）、**0 条 anomaly** | 台账 JSON 逐条 `inline_state`/`sha_check` |
3755-    32	| 源指针核销（判据 b，qa_metrics.db 只读 mode=ro） | `qa_error_logs` **0 行** → 0/92 可经 qa_metrics.db 溯源（诚实记录）；附加核销：llm_call_logs.db 无正文、outbox 空、episode_body_full 0 条；**有效源指针 = request_id 组内 session 归因 → 7 个 transcript 全部在盘实测存在** | 报告 §4 + 台账 `qa_metrics_probe` |
3756-    33	| 可恢复性三态（判据 b） | 可字节级 **4** / 近似 **88** / 不可恢复 **0**；不可恢复清单显式成段 0 条、"待定" 0 条 | 报告 §5 + 台账 `recoverability_distribution` |
3757-    34	| G4-10 稳定键（判据 d） | 逐条复合键 `{line_no, sha256_prefix, request_id}` + 台账头部冻结文件 sha；request_id 92 条仅 25 唯一值的实测证明单列不可作键 | 报告 §6 + 台账 `records[].stable_key` |
3758:    35	| Codex 独立审查 round-1 | **BLOCKED**（3 BLOCKER：--out 可截断输入 / 快照不原子 / 交付物未冻结；3 HIGH：inline 判定 fail-open / request_id 归因传染 / transcript 归因折叠；3 MEDIUM + 4 LOW。同时确认：**当前 92 条数字逐项 0 mismatch**、class/三态/家族计数全对） | `_bmad-output/审查/codex-review-CARD-G4-9.md` |
3759-    36	| Codex findings 逐条整改 | **13/13 完成**（见下）；整改版脚本负例门全过；全量重跑数字与整改前逐项一致 | 报告 §7/§7b + 证据包 |
3760:    37	| Codex 复审 round-2 | **仍阻断**（10/13 CLOSED；BLOCKER-1/HIGH-1/HIGH-3 未真正闭合 + 3 新 LOW）。同时独立复算确认：67ccebe1 冻结生效、92 条数字与 6/29 重复簇全部可复算 | `_bmad-output/审查/codex-review-CARD-G4-9-round2.md`（codex 被 cyber 误拦，内容由 stdout 抢救存档） |
3761:    38	| round-2 findings 逐条整改 | **6/6 完成**：inode 身份守卫封 hardlink+大小写别名 / full_body 长度门+anomaly 前置 / 不可读根 exit 2+symlink 逃逸拒采信 / 3 新 LOW。5 条新负例实测全过、正例无回归、数字仍逐项一致 | 报告 §7/§7c + `grep-selfattest.txt` |
3762:    39	| Codex 复审 round-3 | **仍阻断**（4/6 CLOSED；BLOCKER-1/HIGH-3 判 PARTIAL + 1 新 MEDIUM + 2 新 LOW）。同时确认：HIGH-1 与三条 LOW 已闭合、台账数字有效且与 commit 字节一致 | `_bmad-output/审查/codex-review-CARD-G4-9-round3.md` |
3763:    40	| round-3 findings 逐条整改 | **6/6 完成**：transcript 并入保护集 / O_NOFOLLOW+fstat 消 TOCTOU / os.walk 替 glob（不跟随目录 symlink+遍历错误显式捕获）/ 不可读候选 fail-closed / JSONL 严格 LF 分帧 / 非 dict 归 unparseable。6 条新反例实测全过、数字第三次不变 | 报告 §7d + `grep-selfattest.txt` |
3764:    41	| Codex 复审 round-4 | **仍阻断**（1/6 CLOSED；2 新 BLOCKER + 1 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round4.md` |
3765-    42	| round-4 findings 逐条整改 | **9/9 完成**：全候选入保护集 / 读侧 fd 身份消源侧 TOCTOU / 新增 unverifiable 第四态 / FIFO 设备门 / strict UTF-8 / 3 条错型与边界 LOW / provenance receipt。5 条新反例实测全过；第四次全量重跑数字仍不变 | 报告 §7e + `grep-selfattest.txt` |
3766:    43	| Codex 复审 round-5 | **仍阻断**（3/8 CLOSED；2 BLOCKER + 2 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round5.md` |
3767-    44	| round-5 findings 逐条整改 | **9/9 完成**：先扫描后判定（冲突候选亦入保护集）/ QA DB fd 身份+复核 / 可见性优先于 anomaly / fchmod 后置于碰撞检查 / QA DB 特殊文件门 / no_token 归 unverifiable / 3 条 LOW。6 条新反例实测全过；第五次全量重跑数字仍不变 | 报告 §7f |
3768:    45	| Codex 复审 round-6 | **6/9 CLOSED**（visibility 优先/fchmod 顺序/no_token 语义/3 条 LOW 已闭合）；剩 2 BLOCKER + 1 MEDIUM 揭示保护集**依赖枚举完整性**的架构缺陷 + 3 新发现 | `_bmad-output/审查/codex-review-CARD-G4-9-round6.md` |
3769-    46	| round-6 findings 整改 | **架构级修复 + 6 项**：新增不依赖枚举的**路径层防御**（--out 禁落 transcripts 根内 / 禁等于任一输入 realpath）、QA DB 验证 fd 保持打开至复核完毕、no_token 亦扫描、证据包重生成、ledger 冲突原因自描述、lone surrogate 回退。反例实测：0333 隐藏目录内 transcript 作 --out → exit 2 完好 | 报告 §7g |
3770:    47	| Codex 复审 round-7 | **关键裁定分离**："92 条冻结 ledger **可以采信**；生成器与 UAT 的纯只读安全声明不可验收"——卡面 census 判据已满足，阻断全在工具安全承诺侧。1 BLOCKER（大小写别名根，无需竞态）+ 4 项路径 TOCTOU + 1 MEDIUM（非原子写）+ 2 LOW | `_bmad-output/审查/codex-review-CARD-G4-9-round7.md` |
3771:    48	| round-7 findings 整改 | **架构级第二次修复**：写出改 O_EXCL 临时文件+fsync+os.replace（**全文再无 ftruncate 调用**），五项绕过整类失效；containment 改 inode 逐级比较（normcase 在 POSIX 是恒等函数，我的假设错了）；扫描受阻直接拒绝写出。实测：根外 hardlink 指向根内 transcript 作 --out → 源内容完好 | 报告 §7h |
3772-    49	| 独立 Workflow 4-agent 复核 | G4-9 数字 agent：92 条重算 **0 mismatch**（class/inline/三态/25 request_id/7 transcript 在盘/台账 sha 全 CONFIRMED，仅 2 处描述区间 REFUTED 已修正）；只读契约 agent：与 Codex 同源的 3 条 blocker（已随上整改） | Workflow wf_737b1a95-20b journal |
3773-    50	
3774-    51	## 🔧 Codex round-1 整改记录（13/13 关闭，BLOCKED → 整改完毕）
3775-    52	
3776:    53	- **BLOCKER-1 --out 截断风险**：任意 --out 路径 "w" 无守卫，可覆盖 DLQ 自身（双审查独立实测复现）。整改：写前 resolve() 路径碰撞守卫，命中输入集合即 exit 2；负例实测拒绝、DLQ 完好。
3777:    54	- **BLOCKER-2 快照不原子**：records 与头部 sha 来自两次读取。整改：单次 read_bytes()，头部与逐条同源同字节。
3778:    55	- **BLOCKER-3 交付物漂移**：审查期间脚本/报告 sha 变化且未 track。整改：本卡 commit 冻结全部 exact bytes；自证文件内嵌脚本 sha 前缀。
3779:    56	- **HIGH-1 inline 判定 fail-open**：sha 匹配但长度不符会误判 full_verified（反例实测）。整改：长度精确匹配门 + 64-hex 合法性门 + anomaly 一律 fail-closed（unrecoverable + 如实 basis）。
3780:    57	- **HIGH-2 request_id 归因传染**：缺失值合入 "None" 组、跨类型合组、多 token 静默取长。整改：(类型,值) 复合键 + 缺失单条成组 + 前缀一致门（冲突拒采信）。
3781:    58	- **HIGH-3 transcript 归因折叠**：多命中照单全收、目录缺失误判 unrecoverable=88（实测复现）。整改：恰 1 常规文件命中门 + 递归 glob + 目录缺失 exit 2 拒诊。
3782:    59	- **MEDIUM-1~3**：episode_body_full 采信通路 / duplicate_clusters 6 簇 29 行 + reference_time 透传 / privacy 字段与 private-only 声明。
3783-    60	- **LOW-1~4**：两处区间修正（16948–20831、205–8036）/ 稳定键语义重写为"冻结快照 occurrence key" / schema 双处证据（LearningConcept.name + LearningTip.created_at）/ 挂载历史证据边界声明。
3784-    61	
3785-    62	整改后全量重跑：92 条数字与整改前**逐项一致**（4/88/0、89/2/1、冲突 0、unparseable 0）——整改只收紧契约与通用鲁棒性，不改变本次 census 结论。
3786-    63	
3787-    64	## 🔧 Codex round-2 复审整改记录（10/13 CLOSED → 剩 3 项 + 3 新 LOW 全关闭）
3788-    65	
3789-    66	round-2 用真实入口反例证明我 round-1 的三处整改**没有真正闭合**（这正是二轮审查的价值）：
3790-    67	
3791:    68	- **BLOCKER-1 未闭合**：守卫比的是路径字符串，**hardlink 与大小写别名照样截断 DLQ**。→ 改比**文件 inode 身份**；两种绕过实测双双 exit 2、DLQ sha 不变。
3792:    69	- **HIGH-1 未闭合**：`episode_body_full` 分支只核 sha 不核长度且排在 anomaly 之前，**anomaly 记录能翻案成"可字节级恢复"**。→ 加长度门 + 判定顺序改为 anomaly 优先；反例实测翻转。
3793:    70	- **HIGH-3 未闭合**：`chmod 000` 的目录仍 exit 0 并把全部记录**假判不可恢复**；symlink 可指到目录外冒充源。→ 不可读即 exit 2；symlink 与逃逸目标一律不采信；正例（真实唯一命中）无回归。
3794-    71	- **3 新 LOW**：full_verified 长度范围修正 131–180；台账三个 distribution 补零并新增 `inline_state_distribution`；`line_count` 与 records 改用同一 `splitlines()` 口径。
3795-    72	
3796-    73	round-2 整改后再次全量重跑：92 条、4/88/0、89/2/1、6 簇 29 行、shasum 不变——**数字全程未变**。
3797-    74	
3798-    75	## 🔧 Codex round-3 复审整改记录（4/6 CLOSED → 剩 2 项 + 3 新发现全关闭）
3799-    76	
3800:    77	round-3 确认 HIGH-1 与三条 LOW 真正闭合、台账数字有效，又在两项路径安全上找到更深的绕过：
3801-    78	
3802:    79	- **BLOCKER-1 仍 PARTIAL**：① 保护集漏了**归因到的 transcript**——`--out` 指向它会截断恢复源；② check-then-open 的 **TOCTOU** 仍在。→ ① transcript 写前并入保护集；② 改 `O_NOFOLLOW` 打开且**不带 O_TRUNC**，对实际 fd `fstat` 校验后才 `ftruncate`。反例实测：exit 2、transcript 完好。
3803:    80	- **HIGH-3 仍 PARTIAL**：Python 3.14 的 `glob` 在过滤前就已递归、跟随目录 symlink 且**静默吞掉不可读子树错误**；mode 000 的文件仍过 `isfile()` 被当可用源。→ 改 `os.walk(onerror=, followlinks=False)` + `os.access(R_OK)` 门；遍历受阻或有不可读候选一律拒绝裁定。三反例实测 fail-closed。
3804:    81	- **新 MEDIUM（JSONL 分帧）**：`splitlines()` 会把含 U+2028 的合法单行记录劈成两条坏行。→ 严格按 LF 分帧，header 与 records 共用同一函数。
3805-    82	- **新 LOW ×2**：非 dict JSON（`null`/数组）归 unparseable 不再炸全量；报告头补 artifact commit 链。
3806-    83	
3807-    84	round-3 整改后第三次全量重跑：**92 条、4/88/0、89/2/1、6/29、shasum 不变——三轮整改数字全程未变**，改的全是通用鲁棒性与路径安全。
3808-    85	
3809-    86	## 🔧 Codex round-4 复审整改记录（1/6 CLOSED → 9 项全关闭）
3810-    87	
3811:    88	round-4 只认 1 项闭合，用更深的反例推翻其余"闭合"——两条新 BLOCKER 都是真的：
3812-    89	
3813-    90	- **不可读但可写（mode 0200）的 transcript 绕过保护集**：我在"不可读"分支把候选路径清空了，于是它没进保护集，`--out` 指向它照样截断——不需要任何竞态。→ 新增"全候选清单"，无论可读与否一律并入保护集。
3814-    91	- **源侧 TOCTOU**：保护身份按路径 stat 采集、DLQ 稍后才按路径读取，中间可换 inode。→ 改为**从 fd 读取**：打开一次 → `fstat` 取身份 → 从同一 fd 读全量，保护的就是实际读到的那个对象。
3815-    92	- **把"看不见"说成"不可恢复"**：扫描受阻时仍输出 `unrecoverable`，与报告里"既不宣称不可恢复"自相矛盾。→ 新增第四态 **`unverifiable`**，逐条写明是遍历受阻还是候选不可读。
--
3818-    95	round-4 整改后第四次全量重跑：**92 条、4/88/0（unverifiable 0）、89/2/1、6/29、shasum 不变——四轮整改数字全程未变**。
3819-    96	
3820-    97	## 🔧 Codex round-5 复审整改记录（3/8 CLOSED → 9 项全关闭）
3821-    98	
3822:    99	round-5 继续深挖，两条新 BLOCKER 与两条 HIGH 都成立：
3823-   100	
3824-   101	- **冲突组的候选没进保护集**：token 冲突时我在扫描**之前**就早退了，那些候选从没被看到，`--out` 指向它们照样截断。→ 改成**先扫描后判定**，无论最终是否采信，见到的候选一律进保护集。
3825:   102	- **qa_metrics.db 身份没绑定实际读取**：先按路径 stat、SQLite 稍后按路径重开，中间可换。→ 改 fd 取身份 + 打开后复核身份一致。
3826-   103	- **anomaly 吞掉了"看不见"**：`anomaly→unrecoverable` 排在可见性判断之前，扫描受阻时仍断言"不可恢复"。→ 判定链改为**可见性优先**。
3827-   104	- **`fchmod` 排在碰撞检查之前**：`--out` 指向受保护的只读输入时，会先把它的权限从 644 改成 600 才发现碰撞——字节没丢但输入被改了。→ 碰撞检查前移。
3828-   105	- **其余 5 项**：QA DB 特殊文件门、无 token 归 `unverifiable`、单独换行算 1 空行、strict encode 堵住 lone surrogate 伪造 `full_verified`、`bool` 不再通过长度门。
3829-   106	
--
3844-   121	## 🔧 Codex round-7 复审整改记录（关键裁定分离 + 架构级第二次修复）
3845-   122	
3846-   123	round-7 把结论分成了两半，这个区分很重要：
3847-   124	
3848:   125	> **「现有 92 条冻结 ledger 可以采信；生成器与 UAT 的纯只读安全声明不可验收。」**
3849-   126	
3850-   127	也就是说：这张卡要交付的 census 结论（92 条的分类、对账、三态、挂载真相、稳定键、运行零写入）**已经过关**；卡住的是"这个脚本作为工具，其只读承诺是否经得起敌意输入"。
3851-   128	
3852-   129	- **一个无需竞态的真实绕过**：大小写不敏感卷上 `/Users/...` 与 `/users/...` 是同一个目录但 realpath 字符串不同，我 round-6 用来防御的 `os.path.normcase` **在 macOS/Linux 上根本是恒等函数**——这是我的知识性错误。改成逐级比较 **inode 身份**，不再依赖任何字符串。
3853:   130	- **五项绕过共用一个根源**：它们都依附于"截断一个已存在的文件"这个动作。改成「新建临时文件 → 写 → fsync → 原子替换」后，脚本**全文再没有任何截断调用**，这一整类绕过连同"崩溃留下半个台账"的风险一起消失。实测：拿一个指向恢复源的 hardlink 当 `--out`，台账正常写出，而**源文件内容一个字节没变**。
3854-   131	- **扫描受阻不再只是标记**：看不全就意味着保护集不完整，现在直接拒绝写出台账。
3855-   132	
3856-   133	round-7 整改后第七次全量重跑：**92 条、4/88/0/0、89/2/1、6/29、shasum 不变、台账 0600、无临时文件残留——七轮整改数字全程未变**。
3857-   134	
--
3917-    48	
3918-    49	| inline 状态 | 条数 | 判据 |
3919-    50	|---|---|---|
3920-    51	| `full_verified`（内联全量，sha 对账通过） | **4** | 重算值 == 声明值且长度精确匹配（四条正文实为 131/142/150/180 字符，范围 **131–180**，天然未截断；round-2 LOW 修正） |
3921:    52	| `truncated_prefix`（200 字符前缀） | **88** | len(inline)==200、声明 sha 为合法 64-hex 且声明长度 205–8036。**注**：sha 只能证明 inline≠声明全文，"确为前缀"依赖 `to_dict()[:200]` 生产不变量，无法用 sha 直接证明（Codex round-1 HIGH-1 措辞收敛） |
3922-    53	| `anomaly`（对不上账） | **0** | — |
3923-    54	
3924-    55	4 条 full_verified = 3 条 callout（§2 的 schema/group_id 三条）+ 1 条短 qa_highlight（行 74）。
3925-    56	
--
3946-    77	诚实边界：`近似` ≠ 已恢复。88 条的实际重建（含 22 条 session-archive 是否能达字节级）是 G4-10 的工作与验收，本卡只交付"上游源在盘、路径已核销"的证据链。transcript 属用户本机 `~/.claude/projects/` 数据，若未来被清理，近似裁定随之失效——台账已逐条记录 transcript 绝对路径供 G4-10 开工时复核。
3947-    78	
3948-    79	## §6 台账稳定键（G4-10 交接契约）
3949-    80	
3950:    81	台账逐条携带复合键 `{line_no, sha256_prefix(16 hex), request_id}`。**语义（Codex round-1 LOW-2 修正）**：这是**冻结快照内的 occurrence key**，不是跨文件重排或语义幂等键——台账头部 `dlq_file.sha256`（`3b37460f4215f6ac…`）即快照指纹，`line_no` 在该快照内已单列唯一；`sha256_prefix`（本快照 69 个唯一值，qa_highlight 家族实测同名同 sha 多条）与 `request_id`（仅 25 个唯一值，进程内 contextvars、重启可复用）是**冗余对账/诊断维度**，不是唯一性的必要条件。G4-10 消费前先 diff 头部 sha 即知 DLQ 是否长了新条目；语义级去重不得按本键，须按 `duplicate_clusters` 段（见下）。**语义重复簇（MEDIUM-2 整改）**：按 `{name, episode_body_sha256, group_id}` 聚簇，**6 簇覆盖 29 行**（最大簇 = 同一 session-archive 16 行，`reference_time` 各不相同——同内容反复入队反复超限）。台账 `duplicate_clusters` 段逐簇列 line_nos，records 逐条透传 `reference_time`；G4-10 重放前必须先定去重策略（89 条 budget 修根因后若逐条盲放，将把同内容写入最多 16 遍）。
3951-    82	
3952:    83	**隐私（MEDIUM-3 整改）**：`transcript_paths` 含本机用户名与完整 session UUID，台账与本报告为 **private-only 工件**（台账头部已带 privacy 字段；仓库纪律 = 不 push 公网远端）。
3953-    84	
3954-    85	逐条另带 `class / inline_state / recoverability / transcript_paths / transcript_match_count / attribution_conflict / error_excerpt / failed_at / reference_time`，G4-10 可直接按 `recoverability` 分桶排重放优先级（建议：4 条 byte_exact 先行——但其中 3 条 group_id 为已弃用 `vault:default`，重放前需按 D16 规约重映射并过 `to_physical_group_id()`；89 条 budget_400 重放前必须先修 context 超限根因，否则原样重放必然复现 400）。
3955-    86	
3956-    87	## §7 裁判证据（整改版脚本重跑）
--
3960-    91	| 运行前后 shasum（live/主仓/孤儿①/孤儿② 四份 DLQ + qa_metrics.db） | `diff shasums-before.txt shasums-after.txt` 空 → **PASS，0 写入** |
3961-    92	| grep 自证（import 行全 stdlib；neo4j/graphiti/bolt/app. import 0 命中；`--apply` 定义 0 命中；写模式 open 仅 `--out` 1 处且受路径碰撞守卫保护） | **PASS**（`grep-selfattest.txt`，含守卫在位证明） |
3962-    93	| 容器内 sha 实测 | 92 行、sha 与宿主 live 地址一致（`container-sha-check.txt`） |
3963-    94	| class 偏差 | 无（89/2/1 与勘探预期一致，脚本 `class_deviation` 字段为空） |
3964:    95	| 负例门（round-1 整改自证） | `--out`==`--dlq` → exit 2 拒写、DLQ 完好；transcripts 根缺失 → exit 2 拒诊；sha 匹配但长度不符（round-1 HIGH-1 反例①）→ anomaly/unrecoverable；坏 JSON 行/空行 → unparseable 逐行入台账不拒诊 |
3965:    96	| 负例门（round-2 整改自证） | **hardlink** 指向 DLQ 的 --out → exit 2 + DLQ sha 不变；**case-only 别名**（`DLQ.jsonl`）→ exit 2 + DLQ 完好；**anomaly + episode_body_full 组合**（sha 对但长度 999）→ anomaly/unrecoverable（不再翻案 byte_exact）；**chmod 000 根** → exit 2 拒诊；**symlink 逃逸**（根内 .jsonl → 根外 .txt）→ match_count=0/unrecoverable；正例回归：真实唯一命中仍 approximate |
3966-    97	
3967-    98	## §7b Codex round-1 整改记录（BLOCKED → 全项整改）
3968-    99	
3969:   100	- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
3970:   101	- **BLOCKER-2（快照不原子）**：DLQ 单次 `read_bytes()`，头部 sha256/line_count 与逐条 records 派生自同一份内存字节；mtime 显式标注为 stat 参考值。
3971:   102	- **BLOCKER-3（交付物未冻结漂移）**：以本卡 commit 冻结全部交付物 exact bytes（脚本/报告/台账/证据包同 commit）；grep-selfattest 已按最终版行号重生成并内嵌脚本 sha 前缀。
3972:   103	- **HIGH-1（inline 判定不 fail-closed）**：full_verified 加长度精确匹配门；truncated_prefix 加 64-hex 合法性门；anomaly 一律 unrecoverable + 如实 basis（不再谎称截断、不再滑入 approximate）。
3973:   104	- **HIGH-2（request_id fail-open）**：分组键改 `(类型名, 值)`；缺失/None 按 line_no 单条成组零传染；组内多 token 前缀一致门，冲突记 `attribution_conflict` 拒绝采信（现网 92 条 0 冲突）。
3974:   105	- **HIGH-3（transcript 归因折叠）**：恰 1 个常规文件命中才算归因（多命中 = ambiguous 拒采信）；glob 改递归下探；transcripts 根缺失整体 exit 2（拒绝产出 unrecoverable 假象）。
3975:   106	- **MEDIUM-1**：`episode_body_full` 在盘且 sha 对账通过 → byte_exact 采信（现网 0 条，通路已备）。
3976:   107	- **MEDIUM-2**：`duplicate_clusters` 段 + 逐条 `reference_time`（见 §6）。
3977:   108	- **MEDIUM-3**：台账头部 privacy 字段 + 本报告 private-only 声明（见 §6）。
3978-   109	- **LOW-1~4**：token 区间 16948–20831、长度区间 205–8036、稳定键语义重写、schema 双处证据、挂载历史证据边界——均已在正文落地。
3979-   110	
3980-   111	整改后全量重跑：**92 条数字与整改前逐项一致**（class 89/2/1、三态 4/88/0、归因冲突 0、unparseable 0），重复簇 6/29 行与 Codex 独立复算吻合。另有独立 Workflow 4-agent 复核（92 条重算 0 mismatch、7 transcript 在盘实测、台账 sha 一致）交叉确认。
3981-   112	
3982-   113	## §7c Codex round-2 复审整改记录（10/13 CLOSED → 剩余 3 项 + 3 新 LOW 全部整改）
3983-   114	
3984:   115	round-2 复审确认 BLOCKER-2/3、HIGH-2、MEDIUM-1~3、LOW-1~4 共 10 项 CLOSED，并抓出 3 项**未真正闭合**（均实测复现）+ 3 条新 LOW：
3985-   116	
3986:   117	- **BLOCKER-1 NOT-CLOSED（hardlink / case-only 别名绕过）**：原守卫比较 `resolve()` **字符串**，hardlink 指向输入、以及大小写不敏感文件系统上的 case-only 别名均绕过并截断输入。**整改**：改为比较**文件身份 `(st_dev, st_ino)`**（对已存在的 --out）+ 保留路径比较作第二道。负例实测：两种绕过均 exit 2、DLQ sha 不变。
3987:   118	- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
3988:   119	- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
3989-   120	- **新 LOW ×3**：full_verified 长度范围修正为 131–180；台账 `class_distribution`/`recoverability_distribution` 补零并新增 `inline_state_distribution`（固定 schema，消费者无需补齐缺席键）；`line_count` 改用 `splitlines()` 与 records 同口径（原 `count("\n")` 在 bare CR / U+2028 下会与 records 数不一致）。
3990-   121	
3991-   122	round-2 整改后再次全量重跑：92 条、class 89/2/1、三态 4/88/0、重复簇 6/29、shasum 不变——**数字仍逐项一致**，整改只收紧通用鲁棒性。
3992-   123	
--
4006-   137	诚实标注（与卡面一致）：本卡离用户日常价值远，属恢复能力地基；未修任何根因，未重放任何条目。
4007-   138	
4008-   139	## §7d Codex round-3 复审整改记录（4/6 CLOSED → 剩 2 项 + 3 新发现全部整改）
4009-   140	
4010:   141	round-3 确认 HIGH-1 与三条 LOW 已 CLOSED、台账数字有效且与 commit 字节一致，两项路径安全判 PARTIAL：
4011-   142	
4012:   143	- **BLOCKER-1 残留两条绕过**：① `protected_paths` 未含**归因到的 transcript**，`--out=<唯一 transcript>` 会截断恢复源；② check-then-open 的 **TOCTOU** 仍在（检查后、打开前把 --out 换成指向 DLQ 的链接）。**整改**：① 写出前把全部 `transcript_paths` 并入保护集；② 改 `os.open(O_WRONLY|O_CREAT|O_NOFOLLOW)` **不带 O_TRUNC** 打开 → 对**实际 fd** `fstat` 校验 inode → 通过才 `ftruncate`，检查与写入作用于同一 fd，替换攻击无效。反例实测：`--out` 指向唯一 transcript → exit 2、transcript sha 不变。
4013:   144	- **HIGH-3 残留**：`glob(recursive=True)` 在 realpath 过滤**之前**已递归遍历（Python 3.14 glob 跟随目录 symlink 且**静默吞掉不可读子树错误**）→ 越根枚举 + "假唯一/假不可恢复"；mode `000` 的 regular transcript 仍过 `isfile()` 被判 approximate。**整改**：改 `os.walk(onerror=..., followlinks=False)`（不跟随目录 symlink、遍历错误显式捕获）+ 候选加 `os.access(R_OK)` 门；遍历受阻或存在不可读候选一律记 `attribution_conflict` 拒绝裁定（既不宣称找到、也不宣称不可恢复）。三条反例实测全部 fail-closed。
4014:   145	- **新 MEDIUM（JSONL framing）**：生产端 `ensure_ascii=False` 可原样写出字符串内的 U+2028，`splitlines()` 会把一条合法单-LF 记录劈成两条坏行。**整改**：新增 `_split_jsonl_lines()` 严格按 LF 分帧，header `line_count` 与 records 共用同一函数。
4015-   146	- **新 LOW（输入 schema）**：合法 JSON 但非对象（`null` / 数组 / 标量）解析成功后在 `rec.get()` 处抛 AttributeError 炸全量。**整改**：非 dict 归 `unparseable`（`not_a_json_object: <type>`），实测两条毒行不影响其余记录。
4016-   147	- **新 LOW（provenance）**：报告头只写起始基线未区分整改 artifact commit —— 已在报告头补三段 commit 链。
4017-   148	
4018-   149	round-3 整改后第三次全量重跑：92 条、class 89/2/1、三态 4/88/0、重复簇 6/29、shasum 不变——**三轮整改数字全程未变**，改的全是通用鲁棒性与路径安全。
4019-   150	
4020-   151	## §7e Codex round-4 复审整改记录（1/6 CLOSED → 全部 9 项整改）
4021-   152	
4022:   153	round-4 只认可 1 项 CLOSED（非 dict JSON 门），并用更深的静态反例推翻了另外 5 项的"闭合"，另提 2 BLOCKER / 1 HIGH / 2 MEDIUM / 3 LOW。逐条整改（全部实测复现→封死）：
4023-   154	
4024:   155	- **BLOCKER①（不可读但可写的 transcript 绕过保护集）**：mode `0200` 的候选在 unreadable 分支被清空 `transcript_paths`，因此不进保护集，`--out` 指向它仍被截断（无需竞态）。**整改**：新增 `all_candidate_paths` 保留**所有见到的候选**（含不可读、含被冲突分支清空的），写出前全部并入保护集。实测：mode 0200 候选作 `--out` → exit 2、文件字节不变。
4025:   156	- **BLOCKER②（源侧 TOCTOU）**：保护身份按**路径** stat 采集、DLQ 稍后才按路径读取，两步间可换入另一 inode → 实际读取对象不在保护集。**整改**：`snapshot_file()` 改为 `os.open(O_RDONLY|O_NOFOLLOW|O_NONBLOCK)` → `fstat` 取身份 + regular-file 门 → **从同一 fd 读全量**，返回的身份即**实际被读取对象**；compare 副本同样以读取身份入保护集；输入 `stat` 失败不再静默吞而是 exit 2。
4026:   157	- **HIGH（不可见被终态化为 unrecoverable）**：扫描受阻/冲突时主链仍产出 `unrecoverable`，与报告"既不宣称不可恢复"自相矛盾。**整改**：引入第四态 **`unverifiable`**（源可见性不足，basis 逐条说明是遍历受阻/不可读候选/归因冲突），distribution 与 `unverifiable_list` 同步。实测：不可读子树 → `unverifiable=1`，不再冒充 unrecoverable。
4027:   158	- **MEDIUM（FIFO/设备节点）**：`--out` 缺 regular-file gate 与 `O_NONBLOCK`。**整改**：`O_NONBLOCK` + `S_ISREG` 双门（读侧同样）。实测：FIFO 作 `--out` → exit 2 且不阻塞。
4028:   159	- **MEDIUM（非法 UTF-8 冒充有效记录）**：`errors="replace"` 把坏字节改写成合法对象。**整改**：`_split_jsonl_lines()` 改**逐行 strict decode**，解码失败归 `unparseable`。实测：`b'{"a":"\xff"}'` → `utf8_decode_error`，records=0。
4029-   160	- **LOW ×3**：dict 内字段错型防御（`name=None` / `request_id=[]` 不可哈希 / `episode_body` 非 str 均不再炸全量，按 line_no 单条成组或判 anomaly）；`transcripts_dir="/"` 的 `//` containment 特例；`0o600` 对**既有**输出文件用 `fchmod` 显式收紧（实测台账 mode 现为 `-rw-------`）。
4030-   161	- **LOW（provenance 自指）**：commit 无法自含己身 SHA，改用后置 `artifact-commit-receipt.txt` 绑定精确链，报告头指向该 receipt。
4031-   162	
4032-   163	round-4 整改后第四次全量重跑：**92 条、class 89/2/1、三态 4/88/0（unverifiable 0）、重复簇 6/29、shasum 不变——四轮整改数字全程未变**。
4033-   164	
4034-   165	## §7f Codex round-5 复审整改记录（3/8 CLOSED → 9 项全部整改）
4035-   166	
4036:   167	round-5 用更深的静态反例继续推翻"闭合"，提出 2 BLOCKER / 2 HIGH / 2 MEDIUM / 3 LOW，逐条整改并实测：
4037-   168	
4038:   169	- **BLOCKER①（token 冲突/无 token 时扫描前早退 → 候选不进保护集）**：`--out` 指向冲突组的候选 transcript 仍可无竞态截断。**整改**：`resolve_group_attribution()` 重写为**先扫描后判定**——无条件为每个 token 扫描收集候选进 `all_candidate_paths`（保护集口径），再做冲突/唯一性判定；候选 `stat` 失败不再 `continue` 吞掉而是 exit 2（保护集不完整即拒绝写出）。实测：冲突候选作 `--out` → exit 2、文件 sha 不变。
4039:   170	- **BLOCKER②（qa_metrics.db 身份未绑定实际读取）**：仍是早期 path-stat + SQLite 稍后按路径重开。**整改**：`probe_qa_metrics()` 改 `os.open(O_RDONLY|O_NOFOLLOW|O_NONBLOCK)` 取 fstat 身份 + `S_ISREG` 门 → SQLite 打开后**复核路径身份仍等于该身份**，不等即 `identity_changed_..._refused`；身份入保护集。本次运行 `file_identity_verified: true`。
4040:   171	- **HIGH①（anomaly 吞掉不可见性）**：`anomaly→unrecoverable` 排在 conflict 判断之前，`anomaly + 扫描受阻` 仍被假终态化。**整改**：判定链改为**可见性优先**——归因不可核验时无论 inline 状态一律 `unverifiable`，basis 逐条写明原因（无 token / token 冲突 / 扫描受阻 / 候选 stat 失败 / 不可读候选 / 多命中 ambiguous），并附注 inline 是否也 anomaly。实测：anomaly+不可读子树 → `unverifiable`。
4041:   172	- **HIGH②（`fchmod` 先于 protected-id 检查）**：`--out` 指向受保护的 0644 输入时，会**先把只读输入权限改成 0600** 再拒绝——字节没截断但输入已被修改。**整改**：碰撞检查前移到 `fchmod` 之前。实测：mode 644 → 644 不变。
4042:   173	- **MEDIUM（QA DB 无特殊文件门）**：随 BLOCKER② 一并加 `S_ISREG` + `O_NONBLOCK`。
4043:   174	- **MEDIUM（无 token 未扫描即判不可恢复）**：改为 `unverifiable` + `no_token` 标记（见 HIGH①）。
4044-   175	- **LOW ×3**：单独 `b"\n"` 现算 1 个空行（实测 `line_count=1`）；`errors="replace"` 改 **strict encode**（JSON escaped lone surrogate 不能再构造假 `full_verified`）；`bool` 是 `int` 子类 —— `episode_body_length=True` 现被长度门拒绝（实测判 anomaly）。
4045-   176	
4046-   177	**归因冲突计数由 0 变为 3（如实说明）**：round-5 起"名字不含 session token"被诚实标记为 `no_token`（未做归因扫描），命中的正是 3 条 `callout_annotation` 记录。它们 inline 正文全量、sha 对账通过，**不依赖 transcript**，故仍判 `byte_exact`——三态分布不变（4/88/0/0），88 条 approximate 仍全部为唯一 transcript 命中。这是标注口径变诚实，不是结论变化。
4047-   178	
--
4052-   183	round-6 确认 visibility 优先、fchmod 顺序、no_token 语义、三条 LOW 共 6 项 CLOSED，并揭示了一个**架构层面的根因**：
4053-   184	
4054-   185	> 我的 `--out` 保护集依赖**枚举完整性**——只要某个真实源没被 `os.walk` 看到（不可列举但可穿越的 `0333` 子目录），或 inode 被 A→B→A 换过（QA DB 的 ABA），它就不在集合里，`--out` 指向它仍可截断。这不是补丁能修的，是设计缺陷。
4055-   186	
4056:   187	- **BLOCKER①②的架构级修复**：增加**不依赖枚举的路径层防御**——`--out` 的 `realpath` 不得落在 transcripts 根内（恢复源区域整体禁写）、不得等于任一输入路径的 `realpath`。路径层 + inode 层双保险，任一命中即拒。实测：`0333` 隐藏目录内的 transcript 作 `--out` → exit 2、文件完好（inode 保护集根本没看见它，路径层拦住了）。
4057:   188	- **BLOCKER② 补充修复**：QA DB 的验证 fd 原本验证完即关闭、SQLite 再按路径重开（ABA 可绕）。改为**验证 fd 保持打开**直到 SQLite 连接建立并复核完毕，且连接后二次 `fstat` 该 fd 校验身份未变且 `st_nlink != 0`。本次运行 `file_identity_verified: true`。
4058:   189	- **BLOCKER① 补充修复**：`no_token` 分支原本完全不扫描（`all_candidate_paths=[]`）→ 改为**无论有无 token 都遍历**，所有 `.jsonl` 一律入保护集口径。
4059:   190	- **MEDIUM（证据包漂移）**：`grep-selfattest.txt` 曾停留在 round-4 的脚本 SHA 与旧行号、receipt 未含最新 commit——这是我的疏漏。已重生成（内嵌当前脚本 sha256 + 生成时点声明），receipt 随本轮补链。
4060-   191	- **LOW ×3**：ledger 新增 `attribution_conflict_reason` 自描述（本次 92 条：`no_token` 3 / 其余 89 无冲突）；`json.dumps` 对 lone surrogate 回退 `ensure_ascii=True` 并显式标注，不再整次 census 拒绝；`stat_failures` 分支保留（Codex 确认非额外绕过，仅基本不可达）。
4061-   192	
4062-   193	round-6 整改后第六次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变——六轮整改数字全程未变**。
4063-   194	
4064-   195	## §7h Codex round-7 复审整改记录（关键裁定分离 + 架构级第二次修复）
4065-   196	
4066-   197	round-7 给出了本卡最重要的一次裁定分离：
4067-   198	
4068:   199	> **「现有 92 条冻结 ledger 可以采信；CARD-G4-9 生成器与 UAT 的纯只读安全声明不可验收。」**
4069-   200	
4070:   201	即：卡面的 census 判据（分类/对账/三态/挂载真相/稳定键/shasum 不变）已满足且被独立复算确认；阻断项全部落在"生成器作为工具的只读安全承诺"上。逐条整改：
4071-   202	
4072:   203	- **BLOCKER（大小写别名根）**：本机实测 `/Users/Heishing/.claude/projects` 与 `/users/heishing/...` `samefile=True` 但 `realpath` 字符串不同，prefix guard 返回 False——**无需竞态的实际绕过**。我 round-6 用的 `os.path.normcase` 在 POSIX 上是**恒等函数**（假设错误）。**整改**：新增 `_path_is_within()`，从目标逐级向上比较 **inode 身份**，完全不依赖路径字符串；`--out` 与输入文件的比较改 `os.path.samefile`。实测：别名根作 `--out` → exit 2，正例无回归。
4073:   204	- **NOT-CLOSED ×4（根外 hardlink 指向隐藏目录内 transcript / 根 retarget TOCTOU / 检查后换父目录 symlink 或 basename hardlink）+ MEDIUM（非原子写）**：这五项依附于同一个动作——**截断一个已存在的文件**。**架构级修复**：写出改为「同目录 `O_EXCL` 新建临时文件 → 写 → `fsync` → `os.replace` 原子替换」，**全文再无任何 `ftruncate` 调用**。`O_EXCL` 保证写入目标是本进程新建的对象，因此"把 `--out` 换成指向恢复源的 hardlink / 父目录 symlink / 大小写别名"整类绕过失效；`os.replace` 同时消除崩溃/ENOSPC 留下部分台账的风险。实测：根外 hardlink 指向根内 transcript 作 `--out` → 台账正常写出而**源文件内容完好**（`os.replace` 只重绑定该名字，不触碰底层 inode）。
4074:   205	- **NOT-CLOSED（扫描受阻仅标记不停写）**：扫描受阻 ⇒ 保护集必然不完整。**整改**：`scan_errors`/`stat_failures` 非空时**直接拒绝写出台账**（exit 2），实测不落盘。
4075-   206	- **LOW（lone surrogate 回退失效）**：异常发生在后续 `write`，不在原 `try` 内。**整改**：`json.dumps` 后立即 `.encode("utf-8")` 探测，编码错误在写出前暴露并回退 `ensure_ascii=True`。
4076-   207	- **LOW（receipt 用 8 位缩写）**：如实登记为已知限制（仓库内唯一可解析），未改为 40-hex 以保持 receipt 可读性——列 follow-up。
4077-   208	
4078-   209	round-7 整改后第七次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变、台账 mode 0600、无临时文件残留——七轮整改数字全程未变**。
4079-     1	== CARD-G4-9 / CARD-G4-16 artifact commit receipt ==
4080-     2	（commit 无法自含己身 SHA，故用本后置 receipt 精确绑定 —— Codex round-4 LOW 整改）
4081-     3	
4082-     4	37387a86  第五批开工基线（分析对象锚定 SHA，非本卡产物）
4083:     5	67ccebe1  CARD-G4-9 初版交付（脚本/报告/台账/证据包/round-1 审查/UAT）
4084:     6	e7a480eb  CARD-G4-16 初版交付（报告/证据包/两处注释修正/审查/UAT）
4085-     7	73102875  round-2 findings 整改（两卡）
4086-     8	fce0d8a2  round-3 findings 整改（两卡）
4087-     9	94b420ff  CARD-G4-16 round-4 整改（重放 recipe 确定化）
4088-    10	d2827a6d  CARD-G4-9 round-4 整改
--
4093-    15	f389980c  CARD-G4-9 round-7 架构级修复（消除截断动作；本 receipt 当前版所描述的 commit）
4094-    16	
4095-    17	各阶段交付物 blob 可用 git cat-file 复核；台账头部 dlq_file.sha256 为 DLQ 快照指纹。
4096-
4097:**Identifying discrepancy in UAT round7 summary**
4098-**Planning detailed commit and ledger inspection**
4099-exec
4100:/bin/zsh -lc 'git diff --no-ext-diff f389980c''^ f389980c -- '"'_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' '_bmad-output/审查/G4-9-evidence/grep-selfattest.txt' '_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md' '_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md'
4101-git show --format=fuller --no-patch f389980c
4102-git status --porcelain=v1" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
4103- succeeded in 3ms:
4104-?? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round8.md"
--
4181-                        if os.path.islink(p) or not os.path.isfile(p) or not os.access(p,os.R_OK): continue
4182-                    except OSError: continue
4183-                    matches.append(p)
4184-            matches=sorted(set(matches))
4185:            if walk_errors: reason="scan_errors"
4186-            elif len(matches)>1: reason="ambiguous_multi_match"
4187-    attrs[key]=(reason,matches)
4188-class_c=collections.Counter(); inline_c=collections.Counter(); recov_c=collections.Counter(); conflicts=[]; derived=[]
4189-clusters=collections.defaultdict(list)
--
4219-3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl
4220-
4221-**Verifying absence of temporary files with find**
4222-exec
4223:/bin/zsh -lc "find . -name '*.census-tmp-*' -print
4224:find '_bmad-output/审查' -maxdepth 1 -name '.*.census-tmp-*' -print
4225:find . -name '*.census-tmp-*' -print | wc -l
4226-stat -f 'round8_mode=%Lp round8_size=%z round8_mtime=%Sm' -t '%Y-%m-%dT%H:%M:%S%z' '_bmad-output/审查/codex-review-CARD-G4-9-round8.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
4227- succeeded in 2891ms:
4228-       0
4229-round8_mode=644 round8_size=428004 round8_mtime=2026-08-28T21:19:53+0800
--
4236-web search: 
4237-**Retrieving Python lines for umask**
4238-web search: 
4239-web search: 
4240:**Evaluating directory fsync impact on atomicity and durability**
4241-**Identifying incomplete cleanup and durability gaps on crash**
4242:**Assessing symlink and stale temp file risks**
4243-**Analyzing TOCTOU exploit scenario**
4244:**Evaluating symlink-based overwrite conditions**
4245-**Confirming source preservation against parent retarget**
4246-**Analyzing root retargeting impact on output paths**
4247-**Identifying TOCTOU risk in root retargeting**
4248:**Evaluating symlink stability and precreation risks**
4249:**Identifying critical symlink vulnerability**
4250:**Confirming hardlink and symlink safety on replace operations**
4251:**Highlighting TOCTOU risk with parent symlink swaps**
4252-**Assessing rename syscall mount race conditions**
4253-**Analyzing mount point rename edge cases**
4254-**Identifying rename fail and concurrency issues**
4255-**Analyzing spawn temp file permissions**
--
4260-**Identifying suppressed error propagation on early return**
4261-**Analyzing candidate stat error handling**
4262-**Evaluating incomplete scan error impacts**
4263-**Identifying TOCTOU risk in file checks**
4264:**Analyzing symlink loop detection**
4265:**Verifying symlink and mount boundary handling**
4266-**Clarifying inode behavior on APFS**
4267-**Identifying rename and mount race conditions**
4268-**Analyzing rename behavior and permission edge cases**
4269-**Evaluating os.replace mount point race**
4270:**Analyzing symlink leaf bypass implications**
4271:**Evaluating symlink handling flaws in path checks**
4272:**Confirming realpath handling with hardlinks and symlinks**
4273:**Verifying symlink and path resolution behavior**
4274-**Planning precise QA discrepancy inspection**
4275-exec
4276:/bin/zsh -lc "rg -n '"'^总裁定|''^## QA DB|URI BLOCKER|验收结论|当前大小写|before/after'"' '_bmad-output/审查/codex-review-CARD-G4-9-round7.md' | tail -40
4277-wc -l '_bmad-output/审查/codex-review-CARD-G4-9-round7.md'
4278-nl -ba '_bmad-output/审查/codex-review-CARD-G4-9-round7.md' | tail -180" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
4279- succeeded in 0ms:
4280:571:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:226:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
4281:576:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:245:2765:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:7:| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
4282:587:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:256:2815:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
4283:742:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:928:226:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
4284:747:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:944:245:2765:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:7:| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
4285:757:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:954:256:2815:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
4286:872:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2310:226:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
4287:873:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2313:245:2765:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:7:| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
4288:876:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2316:256:2815:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
4289:1196:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
4290:1217:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2765:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:7:| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
4291:1265:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2815:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
4292:1383:./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:505:928:226:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
4293:1388:./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:521:944:245:2765:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:7:| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
4294:1398:./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:531:954:256:2815:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
4295:1441:./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:789:2310:226:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
4296:1442:./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:792:2313:245:2765:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:7:| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
4297:1445:./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:795:2316:256:2815:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
4298:1668:./_bmad-output/审查/codex-review-CARD-G4-9-round2.md:7:| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
4299:1799:505:928:226:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
4300:1813:521:944:245:2765:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:7:| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
4301:1821:531:954:256:2815:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
4302:1941:789:2310:226:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
4303:1944:792:2313:245:2765:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:7:| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
4304:1947:795:2316:256:2815:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
4305:3991:总裁定：**仍阻断，CARD-G4-9 round-6 不可验收。**
4306:4055:总裁定：**仍阻断，CARD-G4-9 round-6 不可验收。**
4307-5690:> **证据包**: `_bmad-output/审查/G4-9-evidence/`（shasums before/after、grep 自证、容器内 sha 实测）
4308:6398:总裁定：**仍阻断，CARD-G4-9 round-7 不可验收。**
4309-6429:## QA DB 仍未绑定实际连接对象
4310:6442:此外，round-6 已指出的 URI BLOCKER **完全未修**：[line 291](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:291)仍直接拼接 `file:{db_path}?mode=ro`。SQLite 官方规定普通文件名里的 `?/#` 必须转义，fragment 会被忽略；所以 `/x/qa#tag` 可被解析成另一文件且吞掉 `mode=ro`。[SQLite URI 规则](https://www.sqlite.org/uri.html)、[Python sqlite3 URI 行为](https://docs.python.org/3/library/sqlite3.html#how-to-work-with-sqlite-uris)。
4311:6460:- **BLOCKER**：当前大小写不敏感卷上的 case-only 根别名是无需竞态的实际绕过。
4312-6463:- before/after shasum 与当前 bytes 一致，但静态复审不能证明两份清单真实采集时序。
4313:6467:**验收结论：现有 92 条冻结 ledger 可以采信；CARD-G4-9 生成器与 UAT 的纯只读安全声明不可验收。**
4314:6472:总裁定：**仍阻断，CARD-G4-9 round-7 不可验收。**
4315-6503:## QA DB 仍未绑定实际连接对象
4316:6516:此外，round-6 已指出的 URI BLOCKER **完全未修**：[line 291](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:291)仍直接拼接 `file:{db_path}?mode=ro`。SQLite 官方规定普通文件名里的 `?/#` 必须转义，fragment 会被忽略；所以 `/x/qa#tag` 可被解析成另一文件且吞掉 `mode=ro`。[SQLite URI 规则](https://www.sqlite.org/uri.html)、[Python sqlite3 URI 行为](https://docs.python.org/3/library/sqlite3.html#how-to-work-with-sqlite-uris)。
4317:6534:- **BLOCKER**：当前大小写不敏感卷上的 case-only 根别名是无需竞态的实际绕过。
4318-6537:- before/after shasum 与当前 bytes 一致，但静态复审不能证明两份清单真实采集时序。
4319:6541:**验收结论：现有 92 条冻结 ledger 可以采信；CARD-G4-9 生成器与 UAT 的纯只读安全声明不可验收。**
4320-    6543 _bmad-output/审查/codex-review-CARD-G4-9-round7.md
4321-  6364	**Clarifying search tool limitations**
4322-  6365	**Documenting snapshot and classification details**
4323-  6366	**Identifying new blocker cases**
4324-  6367	**Identifying URI carryover blocker**
4325:  6368	**Designing path symlink matrix**
4326-  6369	**Assessing new path containment blockers**
4327-  6370	**Summarizing rejection with closure recommendations**
4328-  6371	**Planning evaluation of closure hypothesis**
4329-  6372	codex
4330:  6373	交叉核验已收束：冻结台账与 receipt 链是可采信的，但生成器安全闭包仍失败。尤其当前卷上已只读确认 `/Users/.../projects` 与 `/users/.../projects` 是同一目录，而 `realpath` 字符串不同，形成无需竞态的根内写入绕过；QA 的 rename 型 ABA 与 round-6 未修的 URI 问题也仍成立。正在整理最终逐项矩阵与验收边界。
4331-  6374	mcp: sequential-thinking/sequentialthinking started
4332-  6375	mcp: sequential-thinking/sequentialthinking (completed)
4333-  6376	mcp: sequential-thinking/sequentialthinking started
4334-  6377	mcp: sequential-thinking/sequentialthinking (completed)
--
4337-  6380	  ✓ 核对 checkout、commit/receipt 链及 round-6 基线
4338-  6381	  ✓ 静态审阅五项修复及生产入口控制流
4339-  6382	  ✓ 设计并只读验证路径、inode、TOCTOU 新反例
4340-  6383	  ✓ 从原始工件独立复算台账与证据包指标
4341:  6384	  ✓ 交叉核验后给出逐项 CLOSED/NOT-CLOSED 与总裁定
4342-  6385	**Drafting final Chinese citations**
4343-  6386	**Including relevant rollout IDs in citations**
4344-  6387	**Defining base file paths**
4345:  6388	**Summarizing symlink path cases**
4346:  6389	**Planning SQLite URI handling**
4347-  6390	**Identifying ledger table blockers and risks**
4348-  6391	**Confirming macOS case-insensitive file handling**
4349-  6392	**Verifying Path.resolve case behavior on macOS**
4350-  6393	**Analyzing path guard limitation with hardlinks**
4351-  6394	**Confirming output truncation behavior**
4352-  6395	**Planning detailed metric reporting format**
4353-  6396	**Confirming memory skill as guidance**
4354-  6397	codex
4355:  6398	总裁定：**仍阻断，CARD-G4-9 round-7 不可验收。**
4356-  6399	
4357:  6400	冻结台账数字可采信，但生成器的“纯只读、恢复源区域零写入”安全闭包仍失败。按开发方 5 个编号计：**2 CLOSED / 2 NOT-CLOSED / 1 PARTIAL**；拆成 6 个原子声明则是 **3 CLOSED / 3 NOT-CLOSED**。
4358-  6401	
4359-  6402	审阅锚点：`HEAD=4ba4f847fa3ad83d136d3a40fcc5448b25c54ba5`，直接父提交为 `5b3712537ef5be91eda18e2a9eaf2fd3d5e03ef5`。
4360-  6403	
4361-  6404	## 逐项裁定
4362-  6405	
4363-  6406	| 项目 | 裁定 | 结果 |
4364-  6407	|---|---|---|
4365:  6408	| 1. transcripts 路径层防御 | **NOT-CLOSED · BLOCKER** | 一次性 `realpath` 字符串检查仍受 hardlink、大小写别名和父目录换链影响。[路径检查](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:421)；最终仍原路径 `open`/`ftruncate`，[写入入口](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:733)。 |
4366:  6409	| 2. QA DB fd 保持及复核 | **NOT-CLOSED · BLOCKER** | 验证 fd=A 虽保持打开，SQLite 仍按 pathname 另开连接；rename 型 A→B→A 可令连接读 B，而两次复核都看到 A。[QA 打开链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:277)。 |
4367-  6410	| 3. no_token 也遍历 | **CLOSED（狭义）** | 现在先无条件遍历、收集可见 `.jsonl`，再于 no_token 分支返回。[遍历](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:201)。但它不覆盖不可枚举 inode，因此不能补救项目 1。 |
4368-  6411	| 4. self-attest + receipt | **CLOSED（当前仓库内）** | self-attest 内嵌脚本 SHA `533d0d4c…e3585` 与实际一致；脚本/self-attest/ledger 从 `5b371253` 到 HEAD blob 均未变。[self-attest](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:1)、[receipt](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt:12)。 |
4369-  6412	| 5a. attribution_conflict_reason | **CLOSED** | 字段已序列化不同原因；冻结台账三条均为 `no_token`。[生成逻辑](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:616)、[台账实例](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:202)。 |
4370-  6413	| 5b. lone-surrogate 回退 | **NOT-CLOSED · LOW** | `json.dumps(..., ensure_ascii=False)` 会正常返回含 surrogate 的 `str`；异常发生在后续 UTF-8 `write/print`，不在当前 `try` 内。[回退代码](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:725)。`--out` 分支还会先 `ftruncate`，再写出失败。 |
--
4372-  6415	## 路径反例矩阵
4373-  6416	
4374-  6417	| 反例 | 结果 |
4375-  6418	|---|---|
4376:  6419	| 根外稳定 symlink → 根内文件 | **CLOSED**：`realpath` 命中；final symlink 还受 `O_NOFOLLOW` 约束。 |
4377-  6420	| 根外 hardlink → 可枚举 transcript | **CLOSED**：枚举所得 inode 会在最终 `fstat` 命中。 |
4378-  6421	| 根外 hardlink → `0333` 隐藏目录内 transcript | **NOT-CLOSED**：hardlink 的 `realpath` 仍在根外；隐藏 inode 未被枚举，最终可被截断。 |
4379:  6422	| transcripts 根是稳定 symlink | **CLOSED**：两侧稳定 `realpath` 指向相同真实根。 |
4380-  6423	| transcripts 根在检查后 retarget | **NOT-CLOSED**：未持有/复核根目录 fd，检查绑定旧目标，扫描或写入可使用新目标。 |
4381-  6424	| 相对路径与 `..` | **CLOSED**：无竞态、大小写一致时会被正规化。 |
4382:  6425	| 检查后仅把 basename 换成 symlink | **CLOSED**：最终 `O_NOFOLLOW` 拒绝。 |
4383:  6426	| 检查后换父目录 symlink或把 basename 换成 hardlink | **NOT-CLOSED**：`O_NOFOLLOW` 只约束最终 symlink，不约束父组件或 hardlink。 |
4384-  6427	| 大小写别名 | **NOT-CLOSED、无需竞态**：本机只读复算确认 `/Users/Heishing/.claude/projects` 与 `/users/heishing/.claude/projects` `samefile=True`，但两者 `realpath` 字符串不同，现有 prefix guard 返回 `False`。 |
4385-  6428	
4386-  6429	## QA DB 仍未绑定实际连接对象
4387-  6430	
--
4393-  6436	4. B→stashB，A→原路径；
4394-  6437	5. 路径 `stat` 与验证 fd `fstat` 均为 A，且 rename 不会令 A 的 `st_nlink` 变 0；
4395-  6438	6. 查询实际仍来自 B。
4396-  6439	
4397:  6440	因此二次 `fstat` 只证明“验证 fd 仍指向 A”，没有证明 SQLite connection 指向 A。
4398-  6441	
4399:  6442	此外，round-6 已指出的 URI BLOCKER **完全未修**：[line 291](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:291)仍直接拼接 `file:{db_path}?mode=ro`。SQLite 官方规定普通文件名里的 `?/#` 必须转义，fragment 会被忽略；所以 `/x/qa#tag` 可被解析成另一文件且吞掉 `mode=ro`。[SQLite URI 规则](https://www.sqlite.org/uri.html)、[Python sqlite3 URI 行为](https://docs.python.org/3/library/sqlite3.html#how-to-work-with-sqlite-uris)。
4400-  6443	
4401-  6444	## 台账独立复算：PASS
4402-  6445	
4403:  6446	未 import 被审生成器，直接从 live DLQ exact bytes 重写严格 LF/UTF-8/JSON、分类、SHA/长度、分组和聚簇计算：
4404-  6447	
4405-  6448	- SHA-256：`3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590`
4406-  6449	- `99,915 bytes`；92 records；unparseable 0
4407-  6450	- class：`89 / 2 / 1`，unexpected 0
--
4413-  6456	汇总与冻结工件一致：[ledger:40](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:40)。
4414-  6457	
4415-  6458	## 新发现与限制
4416-  6459	
4417:  6460	- **BLOCKER**：当前大小写不敏感卷上的 case-only 根别名是无需竞态的实际绕过。
4418:  6461	- **MEDIUM**：`--out` 采用原地 `ftruncate` 后写入，没有临时文件、atomic replace、`fsync` 或并发锁；崩溃、ENOSPC、surrogate 或并发运行可留下空/部分/混写台账。
4419-  6462	- **LOW**：receipt 使用当前仓库唯一可解析的 8 位缩写，不是跨仓可独立验证的完整 40-hex OID。
4420-  6463	- before/after shasum 与当前 bytes 一致，但静态复审不能证明两份清单真实采集时序。
4421-  6464	
4422:  6465	本轮未创建 symlink/hardlink/竞态 fixture，未读取 transcript 正文或 Vault；只读取任务范围内 DLQ exact bytes及 transcript 元数据。工作树仍只有开始前已存在的未跟踪 round-7 文件，未触碰任何文件。`graphiti-canvas` 本环境未暴露，故本轮 Graphiti 搜索明确为不可执行；Sequential Thinking 已完成。
4423-  6466	
4424:  6467	**验收结论：现有 92 条冻结 ledger 可以采信；CARD-G4-9 生成器与 UAT 的纯只读安全声明不可验收。**
4425-  6468	
4426-  6469	
4427-  6470	tokens used
4428-  6471	159,964
4429:  6472	总裁定：**仍阻断，CARD-G4-9 round-7 不可验收。**
4430-  6473	
4431:  6474	冻结台账数字可采信，但生成器的“纯只读、恢复源区域零写入”安全闭包仍失败。按开发方 5 个编号计：**2 CLOSED / 2 NOT-CLOSED / 1 PARTIAL**；拆成 6 个原子声明则是 **3 CLOSED / 3 NOT-CLOSED**。
4432-  6475	
4433-  6476	审阅锚点：`HEAD=4ba4f847fa3ad83d136d3a40fcc5448b25c54ba5`，直接父提交为 `5b3712537ef5be91eda18e2a9eaf2fd3d5e03ef5`。
4434-  6477	
4435-  6478	## 逐项裁定
4436-  6479	
4437-  6480	| 项目 | 裁定 | 结果 |
4438-  6481	|---|---|---|
4439:  6482	| 1. transcripts 路径层防御 | **NOT-CLOSED · BLOCKER** | 一次性 `realpath` 字符串检查仍受 hardlink、大小写别名和父目录换链影响。[路径检查](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:421)；最终仍原路径 `open`/`ftruncate`，[写入入口](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:733)。 |
4440:  6483	| 2. QA DB fd 保持及复核 | **NOT-CLOSED · BLOCKER** | 验证 fd=A 虽保持打开，SQLite 仍按 pathname 另开连接；rename 型 A→B→A 可令连接读 B，而两次复核都看到 A。[QA 打开链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:277)。 |
4441-  6484	| 3. no_token 也遍历 | **CLOSED（狭义）** | 现在先无条件遍历、收集可见 `.jsonl`，再于 no_token 分支返回。[遍历](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:201)。但它不覆盖不可枚举 inode，因此不能补救项目 1。 |
4442-  6485	| 4. self-attest + receipt | **CLOSED（当前仓库内）** | self-attest 内嵌脚本 SHA `533d0d4c…e3585` 与实际一致；脚本/self-attest/ledger 从 `5b371253` 到 HEAD blob 均未变。[self-attest](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:1)、[receipt](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt:12)。 |
4443-  6486	| 5a. attribution_conflict_reason | **CLOSED** | 字段已序列化不同原因；冻结台账三条均为 `no_token`。[生成逻辑](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:616)、[台账实例](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:202)。 |
4444-  6487	| 5b. lone-surrogate 回退 | **NOT-CLOSED · LOW** | `json.dumps(..., ensure_ascii=False)` 会正常返回含 surrogate 的 `str`；异常发生在后续 UTF-8 `write/print`，不在当前 `try` 内。[回退代码](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:725)。`--out` 分支还会先 `ftruncate`，再写出失败。 |
--
4446-  6489	## 路径反例矩阵
4447-  6490	
4448-  6491	| 反例 | 结果 |
4449-  6492	|---|---|
4450:  6493	| 根外稳定 symlink → 根内文件 | **CLOSED**：`realpath` 命中；final symlink 还受 `O_NOFOLLOW` 约束。 |
4451-  6494	| 根外 hardlink → 可枚举 transcript | **CLOSED**：枚举所得 inode 会在最终 `fstat` 命中。 |
4452-  6495	| 根外 hardlink → `0333` 隐藏目录内 transcript | **NOT-CLOSED**：hardlink 的 `realpath` 仍在根外；隐藏 inode 未被枚举，最终可被截断。 |
4453:  6496	| transcripts 根是稳定 symlink | **CLOSED**：两侧稳定 `realpath` 指向相同真实根。 |
4454-  6497	| transcripts 根在检查后 retarget | **NOT-CLOSED**：未持有/复核根目录 fd，检查绑定旧目标，扫描或写入可使用新目标。 |
4455-  6498	| 相对路径与 `..` | **CLOSED**：无竞态、大小写一致时会被正规化。 |
4456:  6499	| 检查后仅把 basename 换成 symlink | **CLOSED**：最终 `O_NOFOLLOW` 拒绝。 |
4457:  6500	| 检查后换父目录 symlink或把 basename 换成 hardlink | **NOT-CLOSED**：`O_NOFOLLOW` 只约束最终 symlink，不约束父组件或 hardlink。 |
4458-  6501	| 大小写别名 | **NOT-CLOSED、无需竞态**：本机只读复算确认 `/Users/Heishing/.claude/projects` 与 `/users/heishing/.claude/projects` `samefile=True`，但两者 `realpath` 字符串不同，现有 prefix guard 返回 `False`。 |
4459-  6502	
4460-  6503	## QA DB 仍未绑定实际连接对象
4461-  6504	
--
4467-  6510	4. B→stashB，A→原路径；
4468-  6511	5. 路径 `stat` 与验证 fd `fstat` 均为 A，且 rename 不会令 A 的 `st_nlink` 变 0；
4469-  6512	6. 查询实际仍来自 B。
4470-  6513	
4471:  6514	因此二次 `fstat` 只证明“验证 fd 仍指向 A”，没有证明 SQLite connection 指向 A。
4472-  6515	
4473:  6516	此外，round-6 已指出的 URI BLOCKER **完全未修**：[line 291](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:291)仍直接拼接 `file:{db_path}?mode=ro`。SQLite 官方规定普通文件名里的 `?/#` 必须转义，fragment 会被忽略；所以 `/x/qa#tag` 可被解析成另一文件且吞掉 `mode=ro`。[SQLite URI 规则](https://www.sqlite.org/uri.html)、[Python sqlite3 URI 行为](https://docs.python.org/3/library/sqlite3.html#how-to-work-with-sqlite-uris)。
4474-  6517	
4475-  6518	## 台账独立复算：PASS
4476-  6519	
4477:  6520	未 import 被审生成器，直接从 live DLQ exact bytes 重写严格 LF/UTF-8/JSON、分类、SHA/长度、分组和聚簇计算：
4478-  6521	
4479-  6522	- SHA-256：`3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590`
4480-  6523	- `99,915 bytes`；92 records；unparseable 0
4481-  6524	- class：`89 / 2 / 1`，unexpected 0
--
4487-  6530	汇总与冻结工件一致：[ledger:40](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:40)。
4488-  6531	
4489-  6532	## 新发现与限制
4490-  6533	
4491:  6534	- **BLOCKER**：当前大小写不敏感卷上的 case-only 根别名是无需竞态的实际绕过。
4492:  6535	- **MEDIUM**：`--out` 采用原地 `ftruncate` 后写入，没有临时文件、atomic replace、`fsync` 或并发锁；崩溃、ENOSPC、surrogate 或并发运行可留下空/部分/混写台账。
4493-  6536	- **LOW**：receipt 使用当前仓库唯一可解析的 8 位缩写，不是跨仓可独立验证的完整 40-hex OID。
4494-  6537	- before/after shasum 与当前 bytes 一致，但静态复审不能证明两份清单真实采集时序。
4495-  6538	
4496:  6539	本轮未创建 symlink/hardlink/竞态 fixture，未读取 transcript 正文或 Vault；只读取任务范围内 DLQ exact bytes及 transcript 元数据。工作树仍只有开始前已存在的未跟踪 round-7 文件，未触碰任何文件。`graphiti-canvas` 本环境未暴露，故本轮 Graphiti 搜索明确为不可执行；Sequential Thinking 已完成。
4497-  6540	
4498:  6541	**验收结论：现有 92 条冻结 ledger 可以采信；CARD-G4-9 生成器与 UAT 的纯只读安全声明不可验收。**
4499-  6542	
4500-  6543	
4501-
4502-**Identifying scope anchor conflict in report**
4503:**Highlighting SQLite URI write risk**
4504-web search: 
4505-**Implementing wait after exec deferral**
4506-web search: site:docs.python.org/3/library/sqlite3.html URI mode=ro sqlite3.connect file database
4507-**Planning comprehensive documentation with references**
--
4519-web search: 
4520-web search: site:pubs.opengroup.org/onlinepubs/9799919799/functions/unlink.html link count last link removed ...
4521-**Auditing file mode handling and Git semantics**
4522-**Verifying ledger integrity and file operation traces**
4523:**Assessing symlink locations without modification**
4524-**Summarizing audit metadata rescan results**
4525-collab: Wait
4526:**Clarifying symlink resolution edge cases**
4527:**Analyzing parent symlink retarget race conditions**
4528-**Distinguishing hardlink swap impact on metadata**
4529-**Assessing inode link count and ctime behavior**
4530-**Clarifying read-only content definition**
4531-collab: Wait
4532:**Planning static anchor and symlink checks**
4533-exec
4534-/bin/zsh -lc "python3 -B -c '
4535-import os
4536-root=\"/Users/Heishing/.claude/projects\"
--
4562-map auto_home on /System/Volumes/Data/home (autofs, automounted, nobrowse)
4563-/dev/disk5s1 on /Volumes/Obsidian 1.12.7-universal (apfs, local, nodev, nosuid, read-only, journaled, noowners, quarantine, mounted by Heishing)
4564-/Volumes/Obsidian 1.12.7-universal/Obsidian.app on /private/var/folders/vq/gssw8vy54671lh9nlqc_ft2w0000gn/T/AppTranslocation/2D56C8CD-387B-4728-91FB-0BA981F2FEF5 (nullfs, local, nodev, nosuid, read-only, noowners, quarantine, nobrowse, mounted by Heishing)
4565-/dev/disk2s1 on /System/Volumes/Update/SFR/mnt1 (apfs, local, journaled, nobrowse)
4566:/dev/disk7s1 on /private/tmp/dmg.H9CS6n (apfs, local, nodev, nosuid, read-only, journaled, noowners, nobrowse, mounted by Heishing)
4567-/dev/disk3s1 on /System/Volumes/Update/mnt1 (apfs, sealed, local, journaled, nobrowse)
4568-/dev/disk8s1 on /Volumes/Tavern Deepseek (hfs, local, nodev, nosuid, read-only, noowners, quarantine, mounted by Heishing)
4569-/dev/disk9s1 on /Volumes/Tavern Deepseek 1 (hfs, local, nodev, nosuid, read-only, noowners, quarantine, mounted by Heishing)
4570-
--
4596-**Verifying ledger mode and output directories**
4597-**Assessing concurrency and temp file safety**
4598-**Verifying file and directory permission handling**
4599-**Assessing atomic write safety and cleanup risks**
4600:**Identifying symlink and mount boundary blockers**
4601:**Detecting parent symlink retarget replacement blocker**
4602-**Listing issue severity levels**
4603-**Reconciling and updating issue statuses**
4604-**Confirming scan blocker and surrogate status**
4605-**Verifying source and ledger hash consistency**
4606-**Checking ledger and Git mode differences**
4607-exec
4608-/bin/zsh -lc "nl -ba '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' | sed -n '1,230p'
4609:nl -ba '_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md' | sed -n '23,52p'
4610:nl -ba '_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md' | sed -n '121,136p'
4611-nl -ba '_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md' | sed -n '195,212p'
4612-nl -ba '_bmad-output/审查/G4-9-evidence/grep-selfattest.txt' | sed -n '1,52p'
4613-nl -ba '_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt' | sed -n '10,20p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
4614- succeeded in 0ms:
--
4853-    31	| inline 完整性 + SHA 对账（判据 b） | 92/92 重算 sha256 对账：4 条 full_verified、88 条 truncated_prefix（`to_dict()` 的 `[:200]` 截断，`episode_worker.py:107`）、**0 条 anomaly** | 台账 JSON 逐条 `inline_state`/`sha_check` |
4854-    32	| 源指针核销（判据 b，qa_metrics.db 只读 mode=ro） | `qa_error_logs` **0 行** → 0/92 可经 qa_metrics.db 溯源（诚实记录）；附加核销：llm_call_logs.db 无正文、outbox 空、episode_body_full 0 条；**有效源指针 = request_id 组内 session 归因 → 7 个 transcript 全部在盘实测存在** | 报告 §4 + 台账 `qa_metrics_probe` |
4855-    33	| 可恢复性三态（判据 b） | 可字节级 **4** / 近似 **88** / 不可恢复 **0**；不可恢复清单显式成段 0 条、"待定" 0 条 | 报告 §5 + 台账 `recoverability_distribution` |
4856-    34	| G4-10 稳定键（判据 d） | 逐条复合键 `{line_no, sha256_prefix, request_id}` + 台账头部冻结文件 sha；request_id 92 条仅 25 唯一值的实测证明单列不可作键 | 报告 §6 + 台账 `records[].stable_key` |
4857:    35	| Codex 独立审查 round-1 | **BLOCKED**（3 BLOCKER：--out 可截断输入 / 快照不原子 / 交付物未冻结；3 HIGH：inline 判定 fail-open / request_id 归因传染 / transcript 归因折叠；3 MEDIUM + 4 LOW。同时确认：**当前 92 条数字逐项 0 mismatch**、class/三态/家族计数全对） | `_bmad-output/审查/codex-review-CARD-G4-9.md` |
4858-    36	| Codex findings 逐条整改 | **13/13 完成**（见下）；整改版脚本负例门全过；全量重跑数字与整改前逐项一致 | 报告 §7/§7b + 证据包 |
4859:    37	| Codex 复审 round-2 | **仍阻断**（10/13 CLOSED；BLOCKER-1/HIGH-1/HIGH-3 未真正闭合 + 3 新 LOW）。同时独立复算确认：67ccebe1 冻结生效、92 条数字与 6/29 重复簇全部可复算 | `_bmad-output/审查/codex-review-CARD-G4-9-round2.md`（codex 被 cyber 误拦，内容由 stdout 抢救存档） |
4860:    38	| round-2 findings 逐条整改 | **6/6 完成**：inode 身份守卫封 hardlink+大小写别名 / full_body 长度门+anomaly 前置 / 不可读根 exit 2+symlink 逃逸拒采信 / 3 新 LOW。5 条新负例实测全过、正例无回归、数字仍逐项一致 | 报告 §7/§7c + `grep-selfattest.txt` |
4861:    39	| Codex 复审 round-3 | **仍阻断**（4/6 CLOSED；BLOCKER-1/HIGH-3 判 PARTIAL + 1 新 MEDIUM + 2 新 LOW）。同时确认：HIGH-1 与三条 LOW 已闭合、台账数字有效且与 commit 字节一致 | `_bmad-output/审查/codex-review-CARD-G4-9-round3.md` |
4862:    40	| round-3 findings 逐条整改 | **6/6 完成**：transcript 并入保护集 / O_NOFOLLOW+fstat 消 TOCTOU / os.walk 替 glob（不跟随目录 symlink+遍历错误显式捕获）/ 不可读候选 fail-closed / JSONL 严格 LF 分帧 / 非 dict 归 unparseable。6 条新反例实测全过、数字第三次不变 | 报告 §7d + `grep-selfattest.txt` |
4863:    41	| Codex 复审 round-4 | **仍阻断**（1/6 CLOSED；2 新 BLOCKER + 1 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round4.md` |
4864-    42	| round-4 findings 逐条整改 | **9/9 完成**：全候选入保护集 / 读侧 fd 身份消源侧 TOCTOU / 新增 unverifiable 第四态 / FIFO 设备门 / strict UTF-8 / 3 条错型与边界 LOW / provenance receipt。5 条新反例实测全过；第四次全量重跑数字仍不变 | 报告 §7e + `grep-selfattest.txt` |
4865:    43	| Codex 复审 round-5 | **仍阻断**（3/8 CLOSED；2 BLOCKER + 2 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round5.md` |
4866-    44	| round-5 findings 逐条整改 | **9/9 完成**：先扫描后判定（冲突候选亦入保护集）/ QA DB fd 身份+复核 / 可见性优先于 anomaly / fchmod 后置于碰撞检查 / QA DB 特殊文件门 / no_token 归 unverifiable / 3 条 LOW。6 条新反例实测全过；第五次全量重跑数字仍不变 | 报告 §7f |
4867:    45	| Codex 复审 round-6 | **6/9 CLOSED**（visibility 优先/fchmod 顺序/no_token 语义/3 条 LOW 已闭合）；剩 2 BLOCKER + 1 MEDIUM 揭示保护集**依赖枚举完整性**的架构缺陷 + 3 新发现 | `_bmad-output/审查/codex-review-CARD-G4-9-round6.md` |
4868-    46	| round-6 findings 整改 | **架构级修复 + 6 项**：新增不依赖枚举的**路径层防御**（--out 禁落 transcripts 根内 / 禁等于任一输入 realpath）、QA DB 验证 fd 保持打开至复核完毕、no_token 亦扫描、证据包重生成、ledger 冲突原因自描述、lone surrogate 回退。反例实测：0333 隐藏目录内 transcript 作 --out → exit 2 完好 | 报告 §7g |
4869:    47	| Codex 复审 round-7 | **关键裁定分离**："92 条冻结 ledger **可以采信**；生成器与 UAT 的纯只读安全声明不可验收"——卡面 census 判据已满足，阻断全在工具安全承诺侧。1 BLOCKER（大小写别名根，无需竞态）+ 4 项路径 TOCTOU + 1 MEDIUM（非原子写）+ 2 LOW | `_bmad-output/审查/codex-review-CARD-G4-9-round7.md` |
4870:    48	| round-7 findings 整改 | **架构级第二次修复**：写出改 O_EXCL 临时文件+fsync+os.replace（**全文再无 ftruncate 调用**），五项绕过整类失效；containment 改 inode 逐级比较（normcase 在 POSIX 是恒等函数，我的假设错了）；扫描受阻直接拒绝写出。实测：根外 hardlink 指向根内 transcript 作 --out → 源内容完好 | 报告 §7h |
4871-    49	| 独立 Workflow 4-agent 复核 | G4-9 数字 agent：92 条重算 **0 mismatch**（class/inline/三态/25 request_id/7 transcript 在盘/台账 sha 全 CONFIRMED，仅 2 处描述区间 REFUTED 已修正）；只读契约 agent：与 Codex 同源的 3 条 blocker（已随上整改） | Workflow wf_737b1a95-20b journal |
4872-    50	
4873-    51	## 🔧 Codex round-1 整改记录（13/13 关闭，BLOCKED → 整改完毕）
4874-    52	
4875-   121	## 🔧 Codex round-7 复审整改记录（关键裁定分离 + 架构级第二次修复）
4876-   122	
4877-   123	round-7 把结论分成了两半，这个区分很重要：
4878-   124	
4879:   125	> **「现有 92 条冻结 ledger 可以采信；生成器与 UAT 的纯只读安全声明不可验收。」**
4880-   126	
4881-   127	也就是说：这张卡要交付的 census 结论（92 条的分类、对账、三态、挂载真相、稳定键、运行零写入）**已经过关**；卡住的是"这个脚本作为工具，其只读承诺是否经得起敌意输入"。
4882-   128	
4883-   129	- **一个无需竞态的真实绕过**：大小写不敏感卷上 `/Users/...` 与 `/users/...` 是同一个目录但 realpath 字符串不同，我 round-6 用来防御的 `os.path.normcase` **在 macOS/Linux 上根本是恒等函数**——这是我的知识性错误。改成逐级比较 **inode 身份**，不再依赖任何字符串。
4884:   130	- **五项绕过共用一个根源**：它们都依附于"截断一个已存在的文件"这个动作。改成「新建临时文件 → 写 → fsync → 原子替换」后，脚本**全文再没有任何截断调用**，这一整类绕过连同"崩溃留下半个台账"的风险一起消失。实测：拿一个指向恢复源的 hardlink 当 `--out`，台账正常写出，而**源文件内容一个字节没变**。
4885-   131	- **扫描受阻不再只是标记**：看不全就意味着保护集不完整，现在直接拒绝写出台账。
4886-   132	
4887-   133	round-7 整改后第七次全量重跑：**92 条、4/88/0/0、89/2/1、6/29、shasum 不变、台账 0600、无临时文件残留——七轮整改数字全程未变**。
4888-   134	
--
4891-   195	## §7h Codex round-7 复审整改记录（关键裁定分离 + 架构级第二次修复）
4892-   196	
4893-   197	round-7 给出了本卡最重要的一次裁定分离：
4894-   198	
4895:   199	> **「现有 92 条冻结 ledger 可以采信；CARD-G4-9 生成器与 UAT 的纯只读安全声明不可验收。」**
4896-   200	
4897:   201	即：卡面的 census 判据（分类/对账/三态/挂载真相/稳定键/shasum 不变）已满足且被独立复算确认；阻断项全部落在"生成器作为工具的只读安全承诺"上。逐条整改：
4898-   202	
4899:   203	- **BLOCKER（大小写别名根）**：本机实测 `/Users/Heishing/.claude/projects` 与 `/users/heishing/...` `samefile=True` 但 `realpath` 字符串不同，prefix guard 返回 False——**无需竞态的实际绕过**。我 round-6 用的 `os.path.normcase` 在 POSIX 上是**恒等函数**（假设错误）。**整改**：新增 `_path_is_within()`，从目标逐级向上比较 **inode 身份**，完全不依赖路径字符串；`--out` 与输入文件的比较改 `os.path.samefile`。实测：别名根作 `--out` → exit 2，正例无回归。
4900:   204	- **NOT-CLOSED ×4（根外 hardlink 指向隐藏目录内 transcript / 根 retarget TOCTOU / 检查后换父目录 symlink 或 basename hardlink）+ MEDIUM（非原子写）**：这五项依附于同一个动作——**截断一个已存在的文件**。**架构级修复**：写出改为「同目录 `O_EXCL` 新建临时文件 → 写 → `fsync` → `os.replace` 原子替换」，**全文再无任何 `ftruncate` 调用**。`O_EXCL` 保证写入目标是本进程新建的对象，因此"把 `--out` 换成指向恢复源的 hardlink / 父目录 symlink / 大小写别名"整类绕过失效；`os.replace` 同时消除崩溃/ENOSPC 留下部分台账的风险。实测：根外 hardlink 指向根内 transcript 作 `--out` → 台账正常写出而**源文件内容完好**（`os.replace` 只重绑定该名字，不触碰底层 inode）。
4901:   205	- **NOT-CLOSED（扫描受阻仅标记不停写）**：扫描受阻 ⇒ 保护集必然不完整。**整改**：`scan_errors`/`stat_failures` 非空时**直接拒绝写出台账**（exit 2），实测不落盘。
4902-   206	- **LOW（lone surrogate 回退失效）**：异常发生在后续 `write`，不在原 `try` 内。**整改**：`json.dumps` 后立即 `.encode("utf-8")` 探测，编码错误在写出前暴露并回退 `ensure_ascii=True`。
4903-   207	- **LOW（receipt 用 8 位缩写）**：如实登记为已知限制（仓库内唯一可解析），未改为 40-hex 以保持 receipt 可读性——列 follow-up。
4904-   208	
4905-   209	round-7 整改后第七次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变、台账 mode 0600、无临时文件残留——七轮整改数字全程未变**。
--
4927-    22	0
4928-    23	0 ✓
4929-    24	--- (4) ⛔ 无任何截断调用（round-7 架构整改：从不截断既有文件）:
4930-    25	grep "os.ftruncate|.truncate(" 命中: 0 ✓（'ftruncate' 字样仅出现在说明注释中，非调用）
4931:    26	--- (5) 唯一写出口 = O_EXCL 新建临时文件 → fsync → os.replace 原子替换:
4932-    27	779:        # round-7 架构整改: 不再截断既有文件 —— 同目录 O_EXCL 新建临时文件 →
4933:    28	780:        # 写 → fsync → os.replace 原子替换。O_EXCL 保证目标是本进程新建的对象，
4934:    29	785:        tmp_path = out_path.with_name(f".{out_path.name}.census-tmp-{os.getpid()}")
4935:    30	787:            tmp_fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
4936:    31	789:            print(f"临时台账文件无法新建（O_EXCL）: {tmp_path} ({e})", file=sys.stderr)
4937:    32	795:                os.fsync(tmp_fd)
4938:    33	804:        os.replace(tmp_path, out_path)
4939-    34	--- (6) 恢复源禁写区判定（inode 身份逐级比较，不依赖路径字符串）:
4940-    35	77:def _path_is_within(target: str, root: str) -> bool:
4941-    36	104:def _same_file(a: str, b: str) -> bool:
4942-    37	255:                if not _path_is_within(candidate, root_str):
4943-    38	457:    # 路径层防御：--out 的 realpath 不得落在 transcripts 根内、不得等于任一
4944:    39	460:        # round-7 BLOCKER 整改: 用 **inode 身份逐级比较**（_path_is_within），
4945-    40	463:        if _path_is_within(args.out, args.transcripts_dir):
4946-    41	465:                f"--out 落在 transcripts 根内（恢复源区域），无条件拒绝写出: {args.out}",
4947-    42	470:        if any(_same_file(args.out, ip) for ip in input_paths):
4948-    43	--- (7) 读侧身份绑定 + 扫描完整性前提:
--
4997-    21	## Procedure
4998-    22	
4999-    23	1. Split independent tracks: vault admission/indexing and tests; Graphiti quarantine/retrieval; SnapshotV3/recovery anchors. Keep the audit read-only.
5000-    24	2. For each claim, build an evidence matrix: claim, `file:line`, adversarial input/state, actual entrypoint/path, observed result, severity, PASS/PARTIAL/FAIL, and limitations.
5001:    25	3. Directly exercise real entrypoints with temporary fixtures where permitted. For path admission include symlink, directory symlink, blacklisted filename in an allowed directory, case variant, and nonexistent path. Assert rejected inputs perform zero open/hash/index/write.
5002-    26	4. For quarantine, test ordinary edge search plus node search and exact-reader paths (`search_nodes`, `read_node_tips`, `read_node_errors`, `read_node_edge_reasons`). Use read-only Neo4j queries and `EXPLAIN` where allowed; distinguish observed metadata exposure from unproven fact-body leakage.
5003-    27	5. For SnapshotV3, test same-generation invalid/future version self-healing, extra fields, strict typing, huge finite values that may produce NaN/Infinity, and identity/length collision boundaries.
5004-    28	6. Compare recovery anchors with machine facts: current HEAD, Actions status, test counts, and unresolved findings. Separate targeted-test results from whole CI.
5005-    29	7. Cross-check high-severity findings independently. Write the final matrix before closure language; explicitly retain `UNVERIFIABLE` items and failed counterexample attempts.
--
5043-mcp: sequential-thinking/sequentialthinking started
5044-mcp: sequential-thinking/sequentialthinking (completed)
5045-**Confirming completion of update plan**
5046-codex
5047:三轨结果一致：冻结 snapshot 本身仍是 PASS；生成器 closure 不是。最强的无竞态反例不是预置 tmp symlink（它会被 `O_EXCL` 安全拒绝），而是“恢复根内的末级 symlink 指向根外”：containment 因 `realpath` 判成根外，`os.replace` 却替换 symlink 本身，于是仍在恢复根内发生写入。另有 scan-error 早退吞错与 round-7 文件中未被本次提交处理的 QA SQLite 两项旧阻断。
5048-只读静态审阅、官方语义核对、三轨交叉审计及冻结 ledger exact-byte 复算均已完成；未修改或创建工作区文件。
5049-  ✓ 锚定 HEAD、commit f389980c、工作树状态、任务/规则与变更文件
5050-  ✓ 静态审阅原子写出实现并设计/验证指定反例
5051:  ✓ 审阅 _path_is_within 与 samefile 的 symlink/挂载边界
5052-  ✓ 独立只读复算冻结 ledger 的全部数量、分类、权限和残留
5053:  ✓ 交叉复核高风险发现并给出逐项裁定、分级和总裁定
5054-**Verifying final git status**
5055-exec
5056-/bin/zsh -lc "git status --porcelain=v1
5057-git rev-parse HEAD
5058:find . -name '*.census-tmp-*' -print | wc -l
5059-stat -f 'ledger_mode=%Lp ledger_size=%z ledger_nlink=%l' '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
5060- succeeded in 429ms:
5061-       0
5062-ledger_mode=600 ledger_size=142411 ledger_nlink=1
--
5074-**Noting power-loss durability limitation**
5075-**Clarifying commit anchoring and metrics**
5076-**Planning detailed audit report structure**
5077-**Confirming stable samefile function behavior**
5078:**Assessing symlink and hardlink risk matrix**
5079:**Planning SQLite citation inclusion**
5080-**Documenting file operation references**
5081-**Clarifying ledger acceptance criteria**
5082-codex
5083:总裁定：**round-8 仍阻断，不可验收生成器与 UAT 的“纯只读安全”声明；现有 92 条冻结 ledger 可以验收并继续采信。**
5084-
5085-审阅锚点：`HEAD=85dd1c8fd625759642fa45e483bec52e999efb0a`，修复提交 `f389980c4cee093294e4888e8341861a1d656e57`；脚本与 ledger 在两者间 blob 完全相同。
5086-
5087-## 逐项裁定
5088-
5089-| 修复声明 | 裁定 | 依据 |
5090-|---|---|---|
5091-| 全文不再截断既有文件 | **CLOSED（狭义）** | 确认无 `ftruncate/O_TRUNC` 调用；实际写入先以 `O_CREAT\|O_EXCL` 创建新 inode。[写出链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:778) |
5092:| 因此 hardlink/symlink/父目录换链整类攻击全部失效 | **NOT-CLOSED** | `O_EXCL` 只绑定创建时的 fd；[os.replace](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:804)再次解析 tmp 与目标 pathname。 |
5093-| 大小写别名根 | **CLOSED（namespace 稳定时）** | 本机只读复算仍为 `samefile=True / realpath 字符串不同`，新 inode 祖先比较正确返回 within。[实现](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:77) |
5094:| containment 整体闭合 | **NOT-CLOSED · BLOCKER** | 根内末级 symlink 指向根外时，`realpath(target)`判根外；但 rename/replace 操作 symlink 本身，于是仍在恢复根内创建 tmp 并替换目录项。POSIX 明确规定 rename 不解析末级 symlink。[POSIX rename](https://pubs.opengroup.org/onlinepubs/9799919799/functions/rename.html) |
5095:| 扫描受阻必 exit 2 | **NOT-CLOSED · HIGH** | no-token/token-conflict 在写入 `scan_errors/stat_failures` 前提前返回，[line 261](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:261)；而且拒绝条件是 `scan_blocked and args.out`，stdout 模式仍输出 ledger、exit 0。[line 741](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:741) |
5096-| lone-surrogate 回退 | **CLOSED** | `json.dumps` 后立即 strict UTF-8 encode 探测，异常进入 `ensure_ascii=True` 回退。[line 770](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:770) |
5097:| 原子写消除半截 ledger | **CLOSED（成功 replace 时）** | file flush+fsync 后 replace，成功发布原子且目标不会呈现半写内容。[Python os.replace](https://docs.python.org/3/library/os.html#os.replace) |
5098:| 崩溃/ENOSPC/权限错误均无 tmp 残留 | **NOT-CLOSED · MEDIUM** | `os.replace` 在 try 外；`EXDEV/EBUSY/EACCES/ENOSPC` 会直接冒泡并留下 tmp，且未 fsync 父目录。 |
5099-
5100-## 指定反例结果
5101-
5102:- **预置可预测 tmp symlink**：安全面 **CLOSED**。`O_EXCL` 遇任何既有 symlink/FIFO/文件都会失败，不跟随写入；但构成稳定 DoS，PID 重用或崩溃遗留会阻断后续运行。
5103-
5104:- **tmp 打开后换名**：**NOT-CLOSED · HIGH**。攻击者可在写入 fd 后 unlink/rebind 可预测 tmp 名；写和 fsync 仍落在原 fd，但 `os.replace(tmp_path, out_path)`会发布攻击者替换进去的文件、symlink 或 hardlink。
5105-
5106:- **目标是 symlink**：replace 覆盖 symlink 本身，不改 referent；但这正导致“根内 symlink → 根外”的无竞态 containment 绕过。
5107-
5108-- **目标是 hardlink**：正文 bytes 不变，但替换该目录项会减少受保护 inode 的 link count，因此“内容未变”成立，“纯只读零元数据修改”不成立。POSIX 明确要求移除 hardlink 时递减 link count。[POSIX unlink](https://pubs.opengroup.org/onlinepubs/9699919799/functions/unlink.html)
5109-
5110:- **父目录 symlink retarget**：单独 retarget 通常使 tmp 源路径消失并报错；若在新目标目录预置可预测 tmp 名，则 replace 可覆盖新的目标目录项，故组合攻击仍 **NOT-CLOSED**。
5111-
5112-- **跨设备/挂载点**：稳定同父目录时不会跨设备；挂载或父目录切换可产生 `EXDEV/EBUSY`，目前未捕获。将 transcripts 的某个子目录 bind/nullfs 到根外 alias 时，inode 祖先链不会经过 transcripts 根，形成无需竞态的 mount-alias 绕过。
5113-
5114:- **目录权限**：创建 tmp 失败能 exit 2；创建成功后因 sticky bit、ACL、immutable 或权限变化导致 replace 失败时，异常未清理。
5115-
5116-- **并发同 PID**：同时 open 时一方成功、一方 `EEXIST`；第一方 replace 后，同 PID 后续调用又可成功并最后覆盖。不会混写，但没有序列化或唯一发布者。
5117-
5118:- **循环 symlink**：稳定根循环会在 `is_dir` 阶段拒绝，祖先循环通常在 tmp open 时 `ELOOP`；但 `realpath(strict=False)`不是 fail-closed namespace 绑定，循环解除或 retarget 仍落入上述 TOCTOU。
5119-
5120:旧四项按“纯只读”口径：隐藏 transcript hardlink **NOT-CLOSED（link-count 元数据）**；根 retarget **NOT-CLOSED**；父 symlink retarget **NOT-CLOSED（与预置 tmp 组合）**；basename hardlink **NOT-CLOSED（字节安全但元数据被改）**。
5121-
5122-## 仍被遗漏的 round-7 阻断
5123-
5124:精确的 round-7 文件其实还裁定了 QA DB 的 rename 型 A→B→A 与 URI 问题，[round-7:6408](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/codex-review-CARD-G4-9-round7.md:6408)；但 UAT 将其摘要成“1 BLOCKER + 路径项”，[UAT:47](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:47)，且 `f389980c` 未修改 QA 打开链：
5125-
5126:- **BLOCKER**：`file:{db_path}?mode=ro` 未转义 `?/#`。如路径含 `#`，`mode=ro` 会落入被忽略的 fragment，SQLite 可能按默认读写/创建模式打开另一个文件，直接反驳“唯一写出口”。[代码](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:324)、[SQLite URI 规则](https://www.sqlite.org/uri.html)、[Python sqlite3 URI](https://docs.python.org/3/library/sqlite3.html#how-to-work-with-sqlite-uris)
5127-
5128:- **HIGH/BLOCKER**：验证 fd=A 保持打开，但 SQLite 仍另按 pathname 打开；A→B→A 调度可使 connection 读取 B，而复核仍看到 A。[QA 打开链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:297)
5129-
5130-## 冻结 ledger 复算：PASS
5131-
5132:从 live DLQ exact bytes 独立解析、分类、哈希、分组和聚簇，未 import 被审生成器：
5133-
5134-| 项目 | 只读复算 |
5135-|---|---|
5136-| 源对象 | 99,915 bytes；SHA-256 `3b37460f…ef3ba590`，与 [ledger header](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:6)一致 |
--
5140-| attribution | 3，全部 `no_token`，均为 inline byte-exact |
5141-| 重复簇 | 6 簇 / 29 行；大小 `16,4,3,2,2,2` |
5142-| 逐条对账 | class/inline/recoverability/reason 0 mismatch |
5143-| ledger 文件 | SHA-256 `ea4b9007…c78a88`；当前 mode `0600`、nlink 1 |
5144:| tmp 残留 | 0 |
5145-
5146-主审只遍历了 transcript 文件名/状态元数据，未读取正文；当前仍得到 7 个唯一指针、无 walk error。`0600` 是当前工作树事实，但 Git tree 只保存 `100644`，因此不是跨 checkout 可冻结的权限属性。
5147-
5148-所以最终边界很明确：
5149-
5150-- **可验收：92 条冻结 ledger snapshot。**
5151:- **不可验收：当前生成器的一般安全性，以及 UAT 的“纯只读、唯一写出口、整类 TOCTOU 已消失”声明。**
5152-
5153-本轮未修改、创建或删除任何文件；开始与结束均只有预先存在的未跟踪 round-8 文档。`graphiti-canvas` 未在本会话暴露，故无法执行规定的 Graphiti 搜索；Sequential Thinking 已完成。
5154-
5155-
5156-tokens used
5157-238,732
5158:总裁定：**round-8 仍阻断，不可验收生成器与 UAT 的“纯只读安全”声明；现有 92 条冻结 ledger 可以验收并继续采信。**
5159-
5160-审阅锚点：`HEAD=85dd1c8fd625759642fa45e483bec52e999efb0a`，修复提交 `f389980c4cee093294e4888e8341861a1d656e57`；脚本与 ledger 在两者间 blob 完全相同。
5161-
5162-## 逐项裁定
5163-
5164-| 修复声明 | 裁定 | 依据 |
5165-|---|---|---|
5166-| 全文不再截断既有文件 | **CLOSED（狭义）** | 确认无 `ftruncate/O_TRUNC` 调用；实际写入先以 `O_CREAT\|O_EXCL` 创建新 inode。[写出链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:778) |
5167:| 因此 hardlink/symlink/父目录换链整类攻击全部失效 | **NOT-CLOSED** | `O_EXCL` 只绑定创建时的 fd；[os.replace](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:804)再次解析 tmp 与目标 pathname。 |
5168-| 大小写别名根 | **CLOSED（namespace 稳定时）** | 本机只读复算仍为 `samefile=True / realpath 字符串不同`，新 inode 祖先比较正确返回 within。[实现](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:77) |
5169:| containment 整体闭合 | **NOT-CLOSED · BLOCKER** | 根内末级 symlink 指向根外时，`realpath(target)`判根外；但 rename/replace 操作 symlink 本身，于是仍在恢复根内创建 tmp 并替换目录项。POSIX 明确规定 rename 不解析末级 symlink。[POSIX rename](https://pubs.opengroup.org/onlinepubs/9799919799/functions/rename.html) |
5170:| 扫描受阻必 exit 2 | **NOT-CLOSED · HIGH** | no-token/token-conflict 在写入 `scan_errors/stat_failures` 前提前返回，[line 261](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:261)；而且拒绝条件是 `scan_blocked and args.out`，stdout 模式仍输出 ledger、exit 0。[line 741](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:741) |
5171-| lone-surrogate 回退 | **CLOSED** | `json.dumps` 后立即 strict UTF-8 encode 探测，异常进入 `ensure_ascii=True` 回退。[line 770](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:770) |
5172:| 原子写消除半截 ledger | **CLOSED（成功 replace 时）** | file flush+fsync 后 replace，成功发布原子且目标不会呈现半写内容。[Python os.replace](https://docs.python.org/3/library/os.html#os.replace) |
5173:| 崩溃/ENOSPC/权限错误均无 tmp 残留 | **NOT-CLOSED · MEDIUM** | `os.replace` 在 try 外；`EXDEV/EBUSY/EACCES/ENOSPC` 会直接冒泡并留下 tmp，且未 fsync 父目录。 |
5174-
5175-## 指定反例结果
5176-
5177:- **预置可预测 tmp symlink**：安全面 **CLOSED**。`O_EXCL` 遇任何既有 symlink/FIFO/文件都会失败，不跟随写入；但构成稳定 DoS，PID 重用或崩溃遗留会阻断后续运行。
5178-
5179:- **tmp 打开后换名**：**NOT-CLOSED · HIGH**。攻击者可在写入 fd 后 unlink/rebind 可预测 tmp 名；写和 fsync 仍落在原 fd，但 `os.replace(tmp_path, out_path)`会发布攻击者替换进去的文件、symlink 或 hardlink。
5180-
5181:- **目标是 symlink**：replace 覆盖 symlink 本身，不改 referent；但这正导致“根内 symlink → 根外”的无竞态 containment 绕过。
5182-
5183-- **目标是 hardlink**：正文 bytes 不变，但替换该目录项会减少受保护 inode 的 link count，因此“内容未变”成立，“纯只读零元数据修改”不成立。POSIX 明确要求移除 hardlink 时递减 link count。[POSIX unlink](https://pubs.opengroup.org/onlinepubs/9699919799/functions/unlink.html)
5184-
5185:- **父目录 symlink retarget**：单独 retarget 通常使 tmp 源路径消失并报错；若在新目标目录预置可预测 tmp 名，则 replace 可覆盖新的目标目录项，故组合攻击仍 **NOT-CLOSED**。
5186-
5187-- **跨设备/挂载点**：稳定同父目录时不会跨设备；挂载或父目录切换可产生 `EXDEV/EBUSY`，目前未捕获。将 transcripts 的某个子目录 bind/nullfs 到根外 alias 时，inode 祖先链不会经过 transcripts 根，形成无需竞态的 mount-alias 绕过。
5188-
5189:- **目录权限**：创建 tmp 失败能 exit 2；创建成功后因 sticky bit、ACL、immutable 或权限变化导致 replace 失败时，异常未清理。
5190-
5191-- **并发同 PID**：同时 open 时一方成功、一方 `EEXIST`；第一方 replace 后，同 PID 后续调用又可成功并最后覆盖。不会混写，但没有序列化或唯一发布者。
5192-
5193:- **循环 symlink**：稳定根循环会在 `is_dir` 阶段拒绝，祖先循环通常在 tmp open 时 `ELOOP`；但 `realpath(strict=False)`不是 fail-closed namespace 绑定，循环解除或 retarget 仍落入上述 TOCTOU。
5194-
5195:旧四项按“纯只读”口径：隐藏 transcript hardlink **NOT-CLOSED（link-count 元数据）**；根 retarget **NOT-CLOSED**；父 symlink retarget **NOT-CLOSED（与预置 tmp 组合）**；basename hardlink **NOT-CLOSED（字节安全但元数据被改）**。
5196-
5197-## 仍被遗漏的 round-7 阻断
5198-
5199:精确的 round-7 文件其实还裁定了 QA DB 的 rename 型 A→B→A 与 URI 问题，[round-7:6408](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/codex-review-CARD-G4-9-round7.md:6408)；但 UAT 将其摘要成“1 BLOCKER + 路径项”，[UAT:47](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:47)，且 `f389980c` 未修改 QA 打开链：
5200-
5201:- **BLOCKER**：`file:{db_path}?mode=ro` 未转义 `?/#`。如路径含 `#`，`mode=ro` 会落入被忽略的 fragment，SQLite 可能按默认读写/创建模式打开另一个文件，直接反驳“唯一写出口”。[代码](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:324)、[SQLite URI 规则](https://www.sqlite.org/uri.html)、[Python sqlite3 URI](https://docs.python.org/3/library/sqlite3.html#how-to-work-with-sqlite-uris)
5202-
5203:- **HIGH/BLOCKER**：验证 fd=A 保持打开，但 SQLite 仍另按 pathname 打开；A→B→A 调度可使 connection 读取 B，而复核仍看到 A。[QA 打开链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:297)
5204-
5205-## 冻结 ledger 复算：PASS
5206-
5207:从 live DLQ exact bytes 独立解析、分类、哈希、分组和聚簇，未 import 被审生成器：
5208-
5209-| 项目 | 只读复算 |
5210-|---|---|
5211-| 源对象 | 99,915 bytes；SHA-256 `3b37460f…ef3ba590`，与 [ledger header](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:6)一致 |
--
5215-| attribution | 3，全部 `no_token`，均为 inline byte-exact |
5216-| 重复簇 | 6 簇 / 29 行；大小 `16,4,3,2,2,2` |
5217-| 逐条对账 | class/inline/recoverability/reason 0 mismatch |
5218-| ledger 文件 | SHA-256 `ea4b9007…c78a88`；当前 mode `0600`、nlink 1 |
5219:| tmp 残留 | 0 |
5220-
5221-主审只遍历了 transcript 文件名/状态元数据，未读取正文；当前仍得到 7 个唯一指针、无 walk error。`0600` 是当前工作树事实，但 Git tree 只保存 `100644`，因此不是跨 checkout 可冻结的权限属性。
5222-
5223-所以最终边界很明确：
5224-
5225-- **可验收：92 条冻结 ledger snapshot。**
5226:- **不可验收：当前生成器的一般安全性，以及 UAT 的“纯只读、唯一写出口、整类 TOCTOU 已消失”声明。**
5227-
5228-本轮未修改、创建或删除任何文件；开始与结束均只有预先存在的未跟踪 round-8 文档。`graphiti-canvas` 未在本会话暴露，故无法执行规定的 Graphiti 搜索；Sequential Thinking 已完成。
5229-
5230-

exec
/bin/zsh -lc "wc -l backend/scripts/census_dead_letter_episodes.py '_bmad-output/审查/codex-review-CARD-G4-9-round8.md' '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json'; shasum -a 256 backend/scripts/census_dead_letter_episodes.py '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' '_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
     849 backend/scripts/census_dead_letter_episodes.py
    5230 _bmad-output/审查/codex-review-CARD-G4-9-round8.md
    2753 _bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json
    8832 total
478332860a15f9294681c33702a5df4af7bff9a8fefb05e91abefe865d0e68e1  backend/scripts/census_dead_letter_episodes.py
b8f042c6d3aca8db8216c77a1ca9ad891436b1bda485218b4f6e970395a6c287  _bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json
f5a9d21c6fbd9efa7a71687b67e429ebb644579cbe35d3475d6d511a10d9d542  _bmad-output/审查/G4-9-DLQ-census-2026-08-28.md

exec
/bin/zsh -lc "rg -n 'def (probe_qa_metrics|_path_is_within|main|write|publish)|deserialize|O_NONBLOCK|O_NOFOLLOW|scan_errors|stat_failures|os\\.replace|fsync|tmp|attribution_conflict|read_mode|bytes_read_from_verified_fd' backend/scripts/census_dead_letter_episodes.py backend/tests tests 2>/dev/null" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
backend/scripts/census_dead_letter_episodes.py:30:    前缀），否则记 attribution_conflict、拒绝采信任何 transcript；
backend/scripts/census_dead_letter_episodes.py:77:def _path_is_within(target: str, root: str) -> bool:
backend/scripts/census_dead_letter_episodes.py:218:        "attribution_conflict": False,
backend/scripts/census_dead_letter_episodes.py:234:    stat_failures: list[str] = []
backend/scripts/census_dead_letter_episodes.py:250:                    stat_failures.append(f"{candidate}: {e}")
backend/scripts/census_dead_letter_episodes.py:264:        result["scan_errors"] = walk_errors[:5]
backend/scripts/census_dead_letter_episodes.py:265:    if stat_failures:
backend/scripts/census_dead_letter_episodes.py:266:        result["stat_failures"] = stat_failures[:5]
backend/scripts/census_dead_letter_episodes.py:270:        result["attribution_conflict"] = True
backend/scripts/census_dead_letter_episodes.py:276:        result["attribution_conflict"] = True
backend/scripts/census_dead_letter_episodes.py:282:        result["scan_errors"] = walk_errors[:5]
backend/scripts/census_dead_letter_episodes.py:283:        result["attribution_conflict"] = True
backend/scripts/census_dead_letter_episodes.py:285:    if stat_failures:
backend/scripts/census_dead_letter_episodes.py:286:        result["stat_failures"] = stat_failures[:5]
backend/scripts/census_dead_letter_episodes.py:287:        result["attribution_conflict"] = True
backend/scripts/census_dead_letter_episodes.py:291:        result["attribution_conflict"] = True
backend/scripts/census_dead_letter_episodes.py:300:        result["attribution_conflict"] = True  # ambiguous 多命中，拒绝采信
backend/scripts/census_dead_letter_episodes.py:304:def probe_qa_metrics(db_path: Path, error_types: list[str]) -> tuple[dict, tuple[int, int] | None]:
backend/scripts/census_dead_letter_episodes.py:311:    ``deserialize``：全程不经路径、不落任何文件，两个问题一并消失。
backend/scripts/census_dead_letter_episodes.py:318:        fd = os.open(db_path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
backend/scripts/census_dead_letter_episodes.py:335:        result["bytes_read_from_verified_fd"] = len(db_bytes)
backend/scripts/census_dead_letter_episodes.py:342:        conn.deserialize(db_bytes)
backend/scripts/census_dead_letter_episodes.py:344:        result["verdict"] = f"deserialize_failed: {str(e)[:80]}"
backend/scripts/census_dead_letter_episodes.py:352:        result["read_mode"] = "in_memory_deserialize_from_verified_fd"
backend/scripts/census_dead_letter_episodes.py:379:    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
backend/scripts/census_dead_letter_episodes.py:416:def main(argv: list[str] | None = None) -> int:
backend/scripts/census_dead_letter_episodes.py:579:    attribution_conflicts = []
backend/scripts/census_dead_letter_episodes.py:597:        elif sess["attribution_conflict"]:
backend/scripts/census_dead_letter_episodes.py:605:            elif sess.get("scan_errors"):
backend/scripts/census_dead_letter_episodes.py:607:            elif sess.get("stat_failures"):
backend/scripts/census_dead_letter_episodes.py:640:        if sess["attribution_conflict"]:
backend/scripts/census_dead_letter_episodes.py:641:            attribution_conflicts.append(stable_key)
backend/scripts/census_dead_letter_episodes.py:660:                "attribution_conflict": sess["attribution_conflict"],
backend/scripts/census_dead_letter_episodes.py:663:                "attribution_conflict_reason": (
backend/scripts/census_dead_letter_episodes.py:668:                    else "scan_errors"
backend/scripts/census_dead_letter_episodes.py:669:                    if sess.get("scan_errors")
backend/scripts/census_dead_letter_episodes.py:670:                    else "stat_failures"
backend/scripts/census_dead_letter_episodes.py:671:                    if sess.get("stat_failures")
backend/scripts/census_dead_letter_episodes.py:675:                    if sess["attribution_conflict"]
backend/scripts/census_dead_letter_episodes.py:745:        "attribution_conflicts": attribution_conflicts,
backend/scripts/census_dead_letter_episodes.py:756:        (k, v.get("scan_errors") or v.get("stat_failures"))
backend/scripts/census_dead_letter_episodes.py:758:        if v.get("scan_errors") or v.get("stat_failures")
backend/scripts/census_dead_letter_episodes.py:796:        # 写 → fsync → os.replace 原子替换。O_EXCL 保证目标是本进程新建的对象，
backend/scripts/census_dead_letter_episodes.py:801:        tmp_path = out_path.with_name(f".{out_path.name}.census-tmp-{os.getpid()}")
backend/scripts/census_dead_letter_episodes.py:803:            tmp_fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
backend/scripts/census_dead_letter_episodes.py:805:            print(f"临时台账文件无法新建（O_EXCL）: {tmp_path} ({e})", file=sys.stderr)
backend/scripts/census_dead_letter_episodes.py:808:            with os.fdopen(tmp_fd, "w", encoding="utf-8", closefd=False) as f:
backend/scripts/census_dead_letter_episodes.py:811:                os.fsync(tmp_fd)
backend/scripts/census_dead_letter_episodes.py:813:            os.close(tmp_fd)
backend/scripts/census_dead_letter_episodes.py:814:            os.unlink(tmp_path)
backend/scripts/census_dead_letter_episodes.py:817:        os.close(tmp_fd)
backend/scripts/census_dead_letter_episodes.py:818:        # 原子替换 + 父目录 fsync（round-8 MEDIUM 整改：replace 纳入 try，
backend/scripts/census_dead_letter_episodes.py:819:        # EXDEV/EBUSY/EACCES/ENOSPC 等异常一律清理 tmp 不留残留）。
backend/scripts/census_dead_letter_episodes.py:821:            os.replace(tmp_path, out_path)
backend/scripts/census_dead_letter_episodes.py:824:                os.fsync(dir_fd)
backend/scripts/census_dead_letter_episodes.py:829:                os.unlink(tmp_path)
backend/scripts/census_dead_letter_episodes.py:840:        f"recoverability={dict(recover_dist)} | 归因冲突={len(attribution_conflicts)} | "
tests/test_generate_file_index.py:34:    def test_scan_source_files_basic(self, mock_root, tmp_path):
tests/test_generate_file_index.py:36:        mock_root.__truediv__ = lambda self, x: tmp_path / x
tests/test_generate_file_index.py:39:        src_dir = tmp_path / "src"
tests/test_generate_file_index.py:46:            with patch('generate_file_index.PROJECT_ROOT', tmp_path):
tests/test_generate_file_index.py:53:    def test_scan_filters_by_extension(self, mock_root, tmp_path):
tests/test_generate_file_index.py:55:        src_dir = tmp_path / "src"
tests/test_generate_file_index.py:62:            with patch('generate_file_index.PROJECT_ROOT', tmp_path):
tests/test_generate_file_index.py:71:    def test_scan_ignores_patterns(self, mock_root, tmp_path):
tests/test_generate_file_index.py:73:        src_dir = tmp_path / "src"
tests/test_generate_file_index.py:87:            with patch('generate_file_index.PROJECT_ROOT', tmp_path):
tests/test_generate_file_index.py:97:    def test_scan_calculates_relative_paths(self, mock_root, tmp_path):
tests/test_generate_file_index.py:99:        src_dir = tmp_path / "src" / "nested"
tests/test_generate_file_index.py:104:            with patch('generate_file_index.PROJECT_ROOT', tmp_path):
tests/test_generate_file_index.py:110:            assert not any(str(tmp_path) in f for f in nested_files)
tests/test_generate_file_index.py:113:    def test_scan_empty_directory(self, mock_root, tmp_path):
tests/test_generate_file_index.py:115:        src_dir = tmp_path / "src"
tests/test_generate_file_index.py:120:            with patch('generate_file_index.PROJECT_ROOT', tmp_path):
tests/test_generate_file_index.py:135:    def test_extract_openapi_endpoints_basic(self, mock_root, tmp_path, sample_openapi_spec):
tests/test_generate_file_index.py:137:        spec_file = tmp_path / "specs" / "api" / "canvas-api.openapi.yml"
tests/test_generate_file_index.py:143:            with patch('generate_file_index.PROJECT_ROOT', tmp_path):
tests/test_generate_file_index.py:150:    def test_extract_openapi_endpoints_methods(self, mock_root, tmp_path, sample_openapi_spec):
tests/test_generate_file_index.py:152:        spec_file = tmp_path / "specs" / "api" / "canvas-api.openapi.yml"
tests/test_generate_file_index.py:158:            with patch('generate_file_index.PROJECT_ROOT', tmp_path):
tests/test_generate_file_index.py:166:    def test_extract_openapi_operation_ids(self, mock_root, tmp_path, sample_openapi_spec):
tests/test_generate_file_index.py:168:        spec_file = tmp_path / "specs" / "api" / "canvas-api.openapi.yml"
tests/test_generate_file_index.py:174:            with patch('generate_file_index.PROJECT_ROOT', tmp_path):
tests/test_generate_file_index.py:182:    def test_extract_openapi_nonexistent_file(self, mock_root, tmp_path):
tests/test_generate_file_index.py:185:            with patch('generate_file_index.PROJECT_ROOT', tmp_path):
tests/test_generate_file_index.py:199:    def test_extract_json_schemas_basic(self, mock_root, tmp_path, sample_json_schema):
tests/test_generate_file_index.py:201:        schema_dir = tmp_path / "specs" / "data"
tests/test_generate_file_index.py:208:            with patch('generate_file_index.PROJECT_ROOT', tmp_path):
tests/test_generate_file_index.py:215:    def test_extract_json_schemas_metadata(self, mock_root, tmp_path, sample_json_schema):
tests/test_generate_file_index.py:217:        schema_dir = tmp_path / "specs" / "data"
tests/test_generate_file_index.py:224:            with patch('generate_file_index.PROJECT_ROOT', tmp_path):
tests/test_generate_file_index.py:233:    def test_extract_multiple_schemas(self, mock_root, tmp_path, sample_json_schema):
tests/test_generate_file_index.py:235:        schema_dir = tmp_path / "specs" / "data"
tests/test_generate_file_index.py:247:            with patch('generate_file_index.PROJECT_ROOT', tmp_path):
tests/test_generate_file_index.py:346:    def test_output_file_encoding(self, tmp_path):
tests/test_generate_file_index.py:348:        output_file = tmp_path / "index.md"
tests/test_generate_file_index.py:356:    def test_output_directory_creation(self, tmp_path):
tests/test_generate_file_index.py:358:        output_file = tmp_path / "nested" / "dir" / "index.md"
tests/bdd/test_canvas_operations.py:425:def write_and_read_canvas(canvas_context):
tests/performance/test_optimization_benchmark.py:40:def temp_canvas_dir(tmp_path):
tests/performance/test_optimization_benchmark.py:42:    canvas_dir = tmp_path / "test_canvas"
tests/performance/test_optimization_benchmark.py:102:        async def write(self, path, data):
tests/performance/test_optimization_benchmark.py:290:        temp_file = canvas_file.with_suffix(".tmp")
tests/performance/test_optimization_benchmark.py:297:        os.replace(temp_file, canvas_file)
backend/tests/test_cors_exception.py:130:def main_app_client():
tests/load/test_monitoring_under_load.py:631:        async def writer():
backend/tests/test_episode_worker_preflight.py:36:async def test_initialize_graphiti_preflight_fails(monkeypatch, tmp_path):
backend/tests/test_episode_worker_preflight.py:68:        maxsize=1, dead_letter_path=str(tmp_path / "dlq.jsonl")
backend/tests/test_episode_worker_preflight.py:85:async def test_initialize_graphiti_preflight_timeout(monkeypatch, tmp_path):
backend/tests/test_episode_worker_preflight.py:104:        maxsize=1, dead_letter_path=str(tmp_path / "dlq2.jsonl")
tests/planning/test_snapshot_planning.py:40:    def test_create_snapshot_with_timestamp(self, tmp_path):
backend/tests/test_canvas_name_normalize.py:26:        with tempfile.TemporaryDirectory() as tmpdir:
backend/tests/test_canvas_name_normalize.py:27:            yield Path(tmpdir)
backend/tests/test_canvas_name_normalize.py:245:        with tempfile.TemporaryDirectory() as tmpdir:
backend/tests/test_canvas_name_normalize.py:246:            yield Path(tmpdir)
backend/tests/test_debug.py:28:def test_bug_tracker(tmp_path: Path) -> Generator[BugTracker, None, None]:
backend/tests/test_debug.py:35:    log_path = tmp_path / "test_bug_log.jsonl"
backend/tests/e2e/test_intelligent_parallel.py:92:        tmp_path: Path,
backend/tests/e2e/test_intelligent_parallel.py:106:        test_settings.CANVAS_BASE_PATH = str(tmp_path)
backend/tests/e2e/test_intelligent_parallel.py:129:                canvas_relative_path = str(test_canvas_10_nodes.relative_to(tmp_path))
backend/tests/e2e/test_intelligent_parallel.py:223:        tmp_path: Path,
backend/tests/e2e/test_intelligent_parallel.py:231:        test_settings.CANVAS_BASE_PATH = str(tmp_path)
backend/tests/e2e/test_intelligent_parallel.py:243:                canvas_relative_path = str(test_canvas_10_nodes.relative_to(tmp_path))
backend/tests/e2e/test_intelligent_parallel.py:280:        tmp_path: Path,
backend/tests/e2e/test_intelligent_parallel.py:296:        test_settings.CANVAS_BASE_PATH = str(tmp_path)
backend/tests/e2e/test_intelligent_parallel.py:335:                canvas_relative_path = str(test_canvas_20_nodes.relative_to(tmp_path))
backend/tests/e2e/test_intelligent_parallel.py:385:        tmp_path: Path,
backend/tests/e2e/test_intelligent_parallel.py:393:        test_settings.CANVAS_BASE_PATH = str(tmp_path)
backend/tests/e2e/test_intelligent_parallel.py:415:                canvas_relative_path = str(test_canvas_10_nodes.relative_to(tmp_path))
backend/tests/e2e/test_intelligent_parallel.py:477:        tmp_path: Path,
backend/tests/e2e/test_intelligent_parallel.py:493:        test_settings.CANVAS_BASE_PATH = str(tmp_path)
backend/tests/e2e/test_intelligent_parallel.py:550:                    test_canvas_with_failing_node.relative_to(tmp_path)
backend/tests/e2e/test_intelligent_parallel.py:758:        tmp_path: Path,
backend/tests/e2e/test_intelligent_parallel.py:768:        test_settings.CANVAS_BASE_PATH = str(tmp_path)
backend/tests/e2e/test_intelligent_parallel.py:790:                canvas_relative_path = str(test_canvas_100_nodes.relative_to(tmp_path))
backend/tests/e2e/test_intelligent_parallel.py:866:        tmp_path: Path,
backend/tests/e2e/test_intelligent_parallel.py:876:        test_settings.CANVAS_BASE_PATH = str(tmp_path)
backend/tests/e2e/test_intelligent_parallel.py:926:                canvas_relative_path = str(test_canvas_20_nodes.relative_to(tmp_path))
tests/planning/test_planning_utils.py:36:    def test_read_file_utf8(self, tmp_path):
tests/planning/test_planning_utils.py:38:        file_path = tmp_path / "test.md"
tests/planning/test_planning_utils.py:45:    def test_read_file_gbk_fallback(self, tmp_path):
tests/planning/test_planning_utils.py:47:        file_path = tmp_path / "test_gbk.txt"
tests/planning/test_planning_utils.py:54:    def test_write_file_creates_directories(self, tmp_path):
tests/planning/test_planning_utils.py:56:        file_path = tmp_path / "nested" / "dir" / "test.txt"
tests/planning/test_planning_utils.py:64:    def test_compute_file_hash_consistency(self, tmp_path):
tests/planning/test_planning_utils.py:66:        file1 = tmp_path / "file1.txt"
tests/planning/test_planning_utils.py:67:        file2 = tmp_path / "file2.txt"
tests/planning/test_planning_utils.py:79:    def test_compute_file_hash_empty_file(self, tmp_path):
tests/planning/test_planning_utils.py:81:        empty_file = tmp_path / "empty.txt"
tests/planning/test_planning_utils.py:87:    def test_compute_file_hash_nonexistent_file(self, tmp_path):
tests/planning/test_planning_utils.py:89:        nonexistent = tmp_path / "does_not_exist.txt"
tests/planning/test_planning_utils.py:165:    def test_get_version_from_frontmatter(self, tmp_path):
tests/planning/test_planning_utils.py:167:        file_path = tmp_path / "versioned.md"
tests/planning/test_planning_utils.py:178:    def test_get_version_from_frontmatter_missing(self, tmp_path):
tests/planning/test_planning_utils.py:180:        file_path = tmp_path / "no_version.md"
tests/planning/test_planning_utils.py:199:    def test_read_openapi_spec(self, tmp_path, sample_openapi_spec):
tests/planning/test_planning_utils.py:202:        file_path = tmp_path / "api.yml"
tests/planning/test_planning_utils.py:210:    def test_get_openapi_version(self, tmp_path, sample_openapi_spec):
tests/planning/test_planning_utils.py:213:        file_path = tmp_path / "api.yml"
tests/planning/test_planning_utils.py:227:    def test_get_openapi_version_nonexistent(self, tmp_path):
tests/planning/test_planning_utils.py:229:        nonexistent = tmp_path / "does_not_exist.yml"
tests/planning/test_planning_utils.py:290:    def test_get_next_iteration_number_first(self, mock_dir, tmp_path):
tests/planning/test_planning_utils.py:292:        mock_dir.return_value = tmp_path / "snapshots"
tests/planning/test_planning_utils.py:298:    def test_get_next_iteration_number_increment(self, mock_dir, tmp_path):
tests/planning/test_planning_utils.py:300:        snapshots_dir = tmp_path / "snapshots"
tests/planning/test_planning_utils.py:310:    def test_get_iteration_snapshot_path(self, mock_dir, tmp_path):
tests/planning/test_planning_utils.py:312:        mock_dir.return_value = tmp_path / "snapshots"
tests/planning/test_planning_utils.py:318:    def test_load_snapshot(self, mock_path, tmp_path, sample_snapshot):
tests/planning/test_planning_utils.py:320:        snapshot_file = tmp_path / "iteration-001.json"
tests/planning/test_planning_utils.py:330:    def test_load_snapshot_nonexistent(self, mock_path, tmp_path):
tests/planning/test_planning_utils.py:332:        mock_path.return_value = tmp_path / "does_not_exist.json"
tests/planning/test_planning_utils.py:338:    def test_save_snapshot(self, mock_path, tmp_path, sample_snapshot, capsys):
tests/planning/test_planning_utils.py:340:        snapshot_file = tmp_path / "snapshots" / "iteration-001.json"
tests/planning/test_planning_utils.py:351:    def test_save_snapshot_creates_directory(self, mock_path, tmp_path, sample_snapshot):
tests/planning/test_planning_utils.py:353:        snapshot_file = tmp_path / "nested" / "dir" / "iteration-001.json"
tests/planning/test_planning_utils.py:426:    def test_load_validation_rules(self, mock_dir, tmp_path, sample_validation_rules):
tests/planning/test_planning_utils.py:429:        validators_dir = tmp_path / "validators"
tests/planning/test_planning_utils.py:441:    def test_load_validation_rules_not_found(self, mock_dir, tmp_path):
tests/planning/test_planning_utils.py:443:        mock_dir.return_value = tmp_path / "validators"
tests/planning/test_planning_utils.py:514:    def test_compute_hash_binary_file(self, tmp_path):
tests/planning/test_planning_utils.py:516:        binary_file = tmp_path / "binary.bin"
backend/tests/test_alert_manager.py:332:    def test_load_rules_from_valid_yaml(self, tmp_path):
backend/tests/test_alert_manager.py:345:        yaml_file = tmp_path / "alerts.yaml"
backend/tests/e2e/test_epic36_endpoints.py:30:def canvas_dir_with_edges(tmp_path: Path) -> Path:
backend/tests/e2e/test_epic36_endpoints.py:32:    canvas_dir = tmp_path / "canvases"
backend/tests/integration/test_verification_service_di_completeness.py:106:        settings.canvas_base_path = "/tmp/test-canvas"
backend/tests/integration/test_verification_service_di_completeness.py:158:        settings.canvas_base_path = "/tmp/test"
backend/tests/e2e/test_epic33_batch_pipeline.py:83:def canvas_dir(tmp_path):
backend/tests/e2e/test_epic33_batch_pipeline.py:85:    d = tmp_path / "canvases"
backend/tests/integration/test_memory_graphiti_integration.py:33:    with tempfile.TemporaryDirectory() as tmpdir:
backend/tests/integration/test_memory_graphiti_integration.py:34:        storage_path = Path(tmpdir) / "test_learning_memories.json"
tests/planning/conftest.py:20:def temp_project_dir(tmp_path):
tests/planning/conftest.py:22:    project_dir = tmp_path / "test_project"
backend/tests/integration/test_qa_pipeline_health.py:30:    async def test_difficulty_evaluation_feeds_health(self, tmp_path):
backend/tests/integration/test_qa_pipeline_health.py:31:        db_path = str(tmp_path / "test_health.db")
backend/tests/integration/test_qa_pipeline_health.py:50:    async def test_low_match_rate_triggers_unhealthy(self, tmp_path):
backend/tests/integration/test_qa_pipeline_health.py:51:        db_path = str(tmp_path / "test_low.db")
backend/tests/integration/test_qa_pipeline_health.py:83:    async def test_extraction_stats_reflect_annotations(self, tmp_path):
backend/tests/integration/test_qa_pipeline_health.py:84:        db_path = str(tmp_path / "test_ext.db")
backend/tests/integration/test_qa_pipeline_health.py:124:    async def test_mixed_errors_aggregate(self, tmp_path):
backend/tests/integration/test_qa_pipeline_health.py:125:        db_path = str(tmp_path / "test_agg.db")
backend/tests/test_resource_monitor.py:44:        paths = ["/", "/tmp"]
backend/tests/test_resource_monitor.py:94:        assert "/tmp" in custom_monitor.disk_paths
backend/tests/integration/test_context_enrichment_file_nodes.py:24:def mock_canvas_service(tmp_path):
backend/tests/integration/test_context_enrichment_file_nodes.py:27:    service.canvas_base_path = str(tmp_path)
backend/tests/integration/test_context_enrichment_file_nodes.py:32:def test_vault(tmp_path):
backend/tests/integration/test_context_enrichment_file_nodes.py:35:    oral_file = tmp_path / "explanations" / "oral-explanation.md"
backend/tests/integration/test_context_enrichment_file_nodes.py:45:    deep_file = tmp_path / "deep-dive.md"
backend/tests/integration/test_context_enrichment_file_nodes.py:51:    return tmp_path
backend/tests/integration/test_epic12e_integration.py:246:    def temp_dir(self, tmp_path):
backend/tests/integration/test_epic12e_integration.py:248:        return tmp_path
backend/tests/integration/test_epic12e_integration.py:637:    def temp_dir(self, tmp_path):
backend/tests/integration/test_epic12e_integration.py:639:        return tmp_path
backend/tests/e2e/test_review_generate.py:21:def review_canvas_dir(tmp_path: Path) -> Path:
backend/tests/e2e/test_review_generate.py:59:    canvas_file = tmp_path / "test-algo.canvas"
backend/tests/e2e/test_review_generate.py:63:    return tmp_path
backend/tests/integration/test_canvas_memory_integration.py:45:def temp_canvas_dir(tmp_path):
backend/tests/integration/test_canvas_memory_integration.py:60:    canvas_file = tmp_path / "test-canvas.canvas"
backend/tests/integration/test_canvas_memory_integration.py:68:    canvas2_file = tmp_path / "concurrent-canvas.canvas"
backend/tests/integration/test_canvas_memory_integration.py:71:    return tmp_path
backend/tests/integration/test_cypher_contract_gate.py:109:async def gate_client(tmp_path):
backend/tests/integration/test_cypher_contract_gate.py:112:    storage_path 指向 tmp_path: 万一触发 JSON fallback 也不污染
backend/tests/integration/test_cypher_contract_gate.py:122:        storage_path=tmp_path / "gate_fallback.json",
tests/integration/test_commit_gate_e2e.py:37:    def setup_gate(self, tmp_path):
tests/integration/test_commit_gate_e2e.py:39:        worktree = tmp_path / "worktree"
tests/integration/test_commit_gate_e2e.py:41:        base = tmp_path / "base"
tests/integration/test_commit_gate_e2e.py:49:        audit_log_path = tmp_path / "e2e-audit.jsonl"
backend/tests/integration/test_edge_bulk_neo4j_sync.py:82:async def canvas_service_with_real_neo4j(tmp_path):
backend/tests/integration/test_edge_bulk_neo4j_sync.py:92:        canvas_base_path=str(tmp_path), memory_client=memory_service
backend/tests/integration/test_edge_bulk_neo4j_sync.py:117:        tmp_path,
backend/tests/integration/test_edge_bulk_neo4j_sync.py:122:        canvas_path = tmp_path / "integration_50.canvas"
backend/tests/integration/test_edge_bulk_neo4j_sync.py:147:        self, canvas_service_with_real_neo4j, neo4j_client, tmp_path
backend/tests/integration/test_edge_bulk_neo4j_sync.py:164:        canvas_path = tmp_path / "idempotent_test.canvas"
backend/tests/integration/test_edge_bulk_neo4j_sync.py:196:        self, canvas_service_with_real_neo4j, tmp_path, sample_canvas_100_edges
backend/tests/integration/test_edge_bulk_neo4j_sync.py:200:        canvas_path = tmp_path / "perf_100.canvas"
backend/tests/integration/test_edge_bulk_neo4j_sync.py:226:        self, canvas_service_with_real_neo4j, neo4j_client, tmp_path
backend/tests/integration/test_edge_bulk_neo4j_sync.py:254:        canvas_path = tmp_path / "partial_failure.canvas"
tests/integration/test_commit_gate.py:34:    def test_log_creates_jsonl_entry(self, tmp_path):
tests/integration/test_commit_gate.py:36:        log_path = tmp_path / "test-audit.jsonl"
tests/integration/test_commit_gate.py:54:    def test_log_appends_multiple_entries(self, tmp_path):
tests/integration/test_commit_gate.py:56:        log_path = tmp_path / "test-audit.jsonl"
tests/integration/test_commit_gate.py:72:    def test_initialization_with_paths(self, tmp_path):
tests/integration/test_commit_gate.py:74:        worktree = tmp_path / "worktree"
tests/integration/test_commit_gate.py:76:        base = tmp_path / "base"
tests/integration/test_commit_gate.py:85:    def test_initialization_default_base_path(self, tmp_path):
tests/integration/test_commit_gate.py:88:        base = tmp_path / "project"
tests/integration/test_commit_gate.py:105:    def gate_with_files(self, tmp_path):
tests/integration/test_commit_gate.py:107:        worktree = tmp_path / "worktree"
tests/integration/test_commit_gate.py:109:        base = tmp_path / "base"
tests/integration/test_commit_gate.py:160:    async def test_g3_passes_with_passing_tests(self, tmp_path):
tests/integration/test_commit_gate.py:162:        worktree = tmp_path / "worktree"
tests/integration/test_commit_gate.py:165:        gate = CommitGate("15.1", worktree, base_path=tmp_path)
tests/integration/test_commit_gate.py:180:    async def test_g3_fails_with_failing_tests(self, tmp_path):
tests/integration/test_commit_gate.py:182:        worktree = tmp_path / "worktree"
tests/integration/test_commit_gate.py:185:        gate = CommitGate("15.1", worktree, base_path=tmp_path)
tests/integration/test_commit_gate.py:204:    async def test_g4_passes_with_pass_verdict(self, tmp_path):
tests/integration/test_commit_gate.py:206:        worktree = tmp_path / "worktree"
tests/integration/test_commit_gate.py:209:        gate = CommitGate("15.1", worktree, base_path=tmp_path)
tests/integration/test_commit_gate.py:224:    async def test_g4_fails_with_fail_verdict(self, tmp_path):
tests/integration/test_commit_gate.py:226:        worktree = tmp_path / "worktree"
tests/integration/test_commit_gate.py:229:        gate = CommitGate("15.1", worktree, base_path=tmp_path)
tests/integration/test_commit_gate.py:248:    async def test_g5_passes_with_real_execution(self, tmp_path):
tests/integration/test_commit_gate.py:250:        worktree = tmp_path / "worktree"
tests/integration/test_commit_gate.py:253:        gate = CommitGate("15.1", worktree, base_path=tmp_path)
tests/integration/test_commit_gate.py:271:    async def test_g5_fails_with_synthetic_dev(self, tmp_path):
tests/integration/test_commit_gate.py:273:        worktree = tmp_path / "worktree"
tests/integration/test_commit_gate.py:276:        gate = CommitGate("15.1", worktree, base_path=tmp_path)
tests/integration/test_commit_gate.py:298:    def mock_gate(self, tmp_path):
tests/integration/test_commit_gate.py:300:        worktree = tmp_path / "worktree"
tests/integration/test_commit_gate.py:302:        base = tmp_path / "base"
tests/integration/test_commit_gate.py:419:    async def test_audit_log_created_on_gate_execution(self, tmp_path):
tests/integration/test_commit_gate.py:421:        worktree = tmp_path / "worktree"
tests/integration/test_commit_gate.py:423:        base = tmp_path / "base"
tests/integration/test_commit_gate.py:427:        log_path = tmp_path / "audit.jsonl"
backend/tests/integration/test_batch_processing.py:65:def test_canvas_file(tmp_path: Path, test_canvas_data: dict) -> Path:
backend/tests/integration/test_batch_processing.py:67:    canvas_dir = tmp_path / "笔记库"
backend/tests/integration/test_batch_processing.py:156:        tmp_path: Path,
backend/tests/integration/test_batch_processing.py:433:        tmp_path: Path,
backend/tests/integration/test_batch_processing.py:444:        service = IntelligentGroupingService(canvas_base_path=str(tmp_path))
backend/tests/integration/test_batch_processing.py:448:            canvas_path=str(test_canvas_file.relative_to(tmp_path)),
backend/tests/integration/test_batch_processing.py:468:        tmp_path: Path,
backend/tests/integration/test_batch_processing.py:506:        canvas_dir = tmp_path / "笔记库"
backend/tests/integration/test_batch_processing.py:513:        service = IntelligentGroupingService(canvas_base_path=str(tmp_path))
backend/tests/integration/test_batch_processing.py:515:            canvas_path=str(canvas_file.relative_to(tmp_path)),
backend/tests/unit/test_epic32_p0_fixes.py:99:    def test_load_card_states_empty_when_no_file(self, tmp_path):
backend/tests/unit/test_epic32_p0_fixes.py:103:            tmp_path / "nonexistent.json",
backend/tests/unit/test_epic32_p0_fixes.py:110:    def test_load_card_states_from_file(self, tmp_path):
backend/tests/unit/test_epic32_p0_fixes.py:113:        json_file = tmp_path / "fsrs_card_states.json"
backend/tests/unit/test_epic32_p0_fixes.py:123:    def test_load_card_states_handles_corrupt_file(self, tmp_path):
backend/tests/unit/test_epic32_p0_fixes.py:125:        json_file = tmp_path / "fsrs_card_states.json"
backend/tests/unit/test_epic32_p0_fixes.py:136:        self, tmp_path, mock_canvas_service, mock_task_manager
backend/tests/unit/test_epic32_p0_fixes.py:139:        json_file = tmp_path / "fsrs_card_states.json"
backend/tests/unit/test_epic32_p0_fixes.py:160:        self, tmp_path, mock_canvas_service, mock_task_manager
backend/tests/unit/test_epic32_p0_fixes.py:163:        json_file = tmp_path / "fsrs_card_states.json"
backend/tests/integration/test_epic33_di_completeness.py:53:    settings.canvas_base_path = "/tmp/test-canvas"
backend/tests/regression/test_fsrs_legacy_state_zero.py:12:  - 读取层 (deserialize_card): legacy state:0 → State.Learning(1)（官方
backend/tests/regression/test_fsrs_legacy_state_zero.py:74:# ── 读取层: canonical legacy New 全链（deserialize → 真实复习 → serialize） ──
backend/tests/regression/test_fsrs_legacy_state_zero.py:77:def test_canonical_legacy_new_deserialize_review_serialize_full_chain():
backend/tests/regression/test_fsrs_legacy_state_zero.py:83:    card = manager.deserialize_card(json.dumps(CANONICAL_LEGACY_NEW))
backend/tests/regression/test_fsrs_legacy_state_zero.py:105:        card = manager.deserialize_card(
backend/tests/regression/test_fsrs_legacy_state_zero.py:130:def test_deserialize_valid_states_unchanged():
backend/tests/regression/test_fsrs_legacy_state_zero.py:136:        card = manager.deserialize_card(json.dumps({"state": raw, "stability": 0.0}))
backend/tests/regression/test_fsrs_legacy_state_zero.py:145:    card = manager.deserialize_card(json.dumps({"state": 0, "reps": 2}))
backend/tests/regression/test_fsrs_legacy_state_zero.py:190:    create_card / serialize / deserialize(0) / card_to_state 全部无 0。"""
backend/tests/regression/test_fsrs_legacy_state_zero.py:204:legacy = m.deserialize_card('{"state": 0, "stability": 0.0, "reps": 2}')
backend/tests/conftest.py:260:def isolate_card_states_file(tmp_path):
backend/tests/conftest.py:261:    """Isolate fsrs_card_states.json to tmp_path to prevent test data pollution.
backend/tests/conftest.py:268:    tmp_file = tmp_path / "fsrs_card_states.json"
backend/tests/conftest.py:269:    with patch("app.services.review_service._CARD_STATES_FILE", tmp_file):
backend/tests/conftest.py:270:        yield tmp_file
backend/tests/conftest.py:374:    with tempfile.TemporaryDirectory() as tmpdir:
backend/tests/conftest.py:375:        yield Path(tmpdir)
backend/tests/unit/test_cost_tracker.py:11:    async def tracker(self, tmp_path):
backend/tests/unit/test_cost_tracker.py:12:        db_path = str(tmp_path / "test_llm_logs.db")
backend/tests/integration/test_error_extraction_e2e.py:34:async def test_e2e_dialog_to_frontmatter_full_pipeline(tmp_path):
backend/tests/integration/test_error_extraction_e2e.py:44:    node_file = tmp_path / "admissibility.md"
backend/tests/integration/test_error_extraction_e2e.py:136:async def test_e2e_dialog_no_errors_no_writes(tmp_path):
backend/tests/integration/test_error_extraction_e2e.py:138:    node_file = tmp_path / "ok-node.md"
backend/tests/integration/test_error_extraction_e2e.py:167:async def test_e2e_record_error_mcp_tool_full_pipeline(tmp_path, monkeypatch):
backend/tests/integration/test_error_extraction_e2e.py:177:    vault_root = tmp_path / "vault"
backend/tests/integration/test_error_extraction_e2e.py:258:    tmp_path, monkeypatch
backend/tests/integration/test_error_extraction_e2e.py:261:    vault_root = tmp_path / "vault"
backend/tests/integration/test_error_extraction_e2e.py:311:    tmp_path, monkeypatch
backend/tests/integration/test_error_extraction_e2e.py:314:    vault_root = tmp_path / "vault"
backend/tests/e2e/test_review_fsrs_degradation.py:93:def isolate_card_states(tmp_path):
backend/tests/e2e/test_review_fsrs_degradation.py:94:    """Isolate card states file to tmp_path."""
backend/tests/e2e/test_review_fsrs_degradation.py:95:    tmp_file = tmp_path / "fsrs_card_states.json"
backend/tests/e2e/test_review_fsrs_degradation.py:96:    with patch("app.services.review_service._CARD_STATES_FILE", tmp_file):
backend/tests/e2e/test_review_fsrs_degradation.py:97:        yield tmp_file
backend/tests/integration/test_story_2_5_chatgpt_round2_p0.py:101:def test_resolve_rejects_absolute_path_outside_vault(tmp_path, monkeypatch):
backend/tests/integration/test_story_2_5_chatgpt_round2_p0.py:103:    vault_root = tmp_path / "vault"
backend/tests/integration/test_story_2_5_chatgpt_round2_p0.py:109:    outside = tmp_path / "outside" / "secret.md"
backend/tests/integration/test_story_2_5_chatgpt_round2_p0.py:129:def test_resolve_rejects_dotdot_escape(tmp_path, monkeypatch):
backend/tests/integration/test_story_2_5_chatgpt_round2_p0.py:131:    vault_root = tmp_path / "vault"
backend/tests/integration/test_story_2_5_chatgpt_round2_p0.py:133:    (tmp_path / "secret.md").write_text("secret", encoding="utf-8")
backend/tests/integration/test_story_2_5_chatgpt_round2_p0.py:146:def test_resolve_prefers_节点_subdir(tmp_path, monkeypatch):
backend/tests/integration/test_story_2_5_chatgpt_round2_p0.py:148:    vault_root = tmp_path / "vault"
backend/tests/integration/test_story_2_5_chatgpt_round2_p0.py:170:def test_resolve_accepts_relative_with_md_suffix(tmp_path, monkeypatch):
backend/tests/integration/test_story_2_5_chatgpt_round2_p0.py:172:    vault_root = tmp_path / "vault"
backend/tests/integration/test_story_2_5_chatgpt_round2_p0.py:196:async def test_post_turn_extract_endpoint_pipeline(tmp_path):
backend/tests/integration/test_story_2_5_chatgpt_round2_p0.py:205:    nodes_dir = tmp_path / "节点"
backend/tests/integration/test_story_2_5_chatgpt_round2_p0.py:636:    tmp_path, monkeypatch
backend/tests/integration/test_review_generate_api.py:72:    with tempfile.TemporaryDirectory() as tmpdir:
backend/tests/integration/test_review_generate_api.py:73:        canvas_path = os.path.join(tmpdir, "离散数学.canvas")
backend/tests/integration/test_review_generate_api.py:76:        yield tmpdir
backend/tests/integration/test_agent_canvas_param.py:51:    with tempfile.TemporaryDirectory() as tmpdir:
backend/tests/integration/test_agent_canvas_param.py:52:        base_path = Path(tmpdir)
tests/unit/test_workflow_enforcer.py:40:    with tempfile.TemporaryDirectory() as tmpdir:
tests/unit/test_workflow_enforcer.py:41:        base = Path(tmpdir)
backend/tests/integration/test_neo4j_client_real.py:83:    async def test_driver_fallback_on_wrong_credentials(self, tmp_path):
backend/tests/integration/test_neo4j_client_real.py:85:        fallback_path = tmp_path / "fallback.json"
backend/tests/integration/test_story_38_7_ac4_degraded_mode.py:29:        self, tmp_path
backend/tests/integration/test_story_38_7_ac4_degraded_mode.py:37:        canvas_dir = tmp_path / "canvases"
backend/tests/integration/test_story_38_7_ac4_degraded_mode.py:44:        svc._fallback_file_path = tmp_path / "canvas_events_fallback.json"
backend/tests/integration/test_story_38_7_ac4_degraded_mode.py:61:    async def test_canvas_crud_skips_memory_when_dual_write_disabled(self, tmp_path):
backend/tests/integration/test_story_38_7_ac4_degraded_mode.py:68:        canvas_dir = tmp_path / "canvases"
backend/tests/integration/test_story_38_7_ac4_degraded_mode.py:75:        svc._fallback_file_path = tmp_path / "canvas_events_fallback.json"
backend/tests/integration/test_story_38_7_ac4_degraded_mode.py:88:    def test_record_failed_write_creates_jsonl(self, tmp_path):
backend/tests/integration/test_story_38_7_ac4_degraded_mode.py:93:        failed_file = tmp_path / "failed_writes.jsonl"
backend/tests/e2e/test_epic36_integration.py:48:    async def test_edge_creation_triggers_sync(self, tmp_path):
backend/tests/e2e/test_epic36_integration.py:57:        canvas_dir = tmp_path / "canvases"
backend/tests/e2e/test_epic36_integration.py:117:        service = CanvasService(canvas_base_path="/tmp/test")
backend/tests/e2e/test_epic36_integration.py:153:        service = CanvasService(canvas_base_path="/tmp/test")
backend/tests/e2e/test_epic36_integration.py:184:        service = CanvasService(canvas_base_path="/tmp/test")
backend/tests/e2e/test_epic36_integration.py:209:    async def test_edge_sync_graceful_with_neo4j_down(self, tmp_path):
backend/tests/e2e/test_epic36_integration.py:217:        service = CanvasService(canvas_base_path="/tmp/test")
backend/tests/e2e/test_epic36_integration.py:226:        dl_path = tmp_path / "failed_edge_syncs.jsonl"
backend/tests/test_rollback_diff.py:62:        self, client: TestClient, mock_snapshot_with_data, tmp_path
backend/tests/test_rollback_diff.py:66:        canvas_file = tmp_path / "test.canvas"
backend/tests/test_rollback_diff.py:76:                tmp_path,
backend/tests/test_rollback_diff.py:85:        self, client: TestClient, mock_snapshot_with_data, tmp_path
backend/tests/test_rollback_diff.py:93:        canvas_file = tmp_path / "test.canvas"
backend/tests/test_rollback_diff.py:103:                tmp_path,
backend/tests/test_rollback_diff.py:119:        self, client: TestClient, mock_snapshot_with_data, tmp_path
backend/tests/test_rollback_diff.py:122:        canvas_file = tmp_path / "test.canvas"
backend/tests/test_rollback_diff.py:132:                tmp_path,
backend/tests/test_rollback_diff.py:146:        self, client: TestClient, mock_snapshot_with_data, tmp_path
backend/tests/test_rollback_diff.py:149:        canvas_file = tmp_path / "test.canvas"
backend/tests/test_rollback_diff.py:159:                tmp_path,
backend/tests/test_rollback_diff.py:195:        self, client: TestClient, mock_snapshot_with_data, tmp_path
backend/tests/test_rollback_diff.py:199:        canvas_file = tmp_path / "test.canvas"
backend/tests/test_rollback_diff.py:209:                tmp_path,
backend/tests/test_rollback_diff.py:221:    def test_get_diff_detects_added_nodes(self, client: TestClient, tmp_path):
backend/tests/test_rollback_diff.py:234:        canvas_file = tmp_path / "test.canvas"
backend/tests/test_rollback_diff.py:248:                tmp_path,
backend/tests/test_rollback_diff.py:261:        self, client: TestClient, mock_snapshot_with_data, tmp_path
backend/tests/test_rollback_diff.py:265:        canvas_file = tmp_path / "test.canvas"
backend/tests/test_rollback_diff.py:281:                tmp_path,
backend/tests/test_rollback_diff.py:299:        self, client: TestClient, mock_snapshot_with_data, tmp_path
backend/tests/test_rollback_diff.py:303:        canvas_file = tmp_path / "test.canvas"
backend/tests/test_rollback_diff.py:316:                tmp_path,
backend/tests/test_rollback_diff.py:327:    def test_get_diff_detects_added_edges(self, client: TestClient, tmp_path):
backend/tests/test_rollback_diff.py:342:        canvas_file = tmp_path / "test.canvas"
backend/tests/test_rollback_diff.py:356:                tmp_path,
backend/tests/integration/test_llm_stats_api.py:23:    async def seeded_tracker(self, tmp_path):
backend/tests/integration/test_llm_stats_api.py:24:        db_path = str(tmp_path / "test_api_llm_logs.db")
backend/tests/integration/test_llm_stats_api.py:132:    async def logger_and_tracker(self, tmp_path):
backend/tests/integration/test_llm_stats_api.py:133:        db_path = str(tmp_path / "e2e_llm_logs.db")
backend/tests/integration/test_llm_stats_api.py:226:    async def test_stop_flushes_remaining_buffer(self, tmp_path):
backend/tests/integration/test_llm_stats_api.py:228:        db_path = str(tmp_path / "stop_flush.db")
tests/unit/test_prd_parser.py:36:    with tempfile.TemporaryDirectory() as tmpdir:
tests/unit/test_prd_parser.py:37:        base = Path(tmpdir)
backend/tests/integration/test_story_38_7_ac3_restart_survival.py:139:    async def test_lancedb_pending_recovery_on_restart(self, tmp_path):
backend/tests/integration/test_story_38_7_ac3_restart_survival.py:147:        pending_file = tmp_path / "lancedb_pending_index.jsonl"
backend/tests/integration/test_story_38_7_ac3_restart_survival.py:157:        result = await svc.recover_pending(str(tmp_path))
backend/tests/integration/test_story_38_7_ac3_restart_survival.py:160:        svc._do_index.assert_awaited_once_with("math-101", str(tmp_path))
tests/test_lancedb_poc_synthetic.py:383:    def test_basic_crud_operations(self, tmp_path):
tests/test_lancedb_poc_synthetic.py:386:        db = lancedb.connect(str(tmp_path / "test_db"))
tests/test_lancedb_poc_synthetic.py:406:    def test_connection_persistence(self, tmp_path):
tests/test_lancedb_poc_synthetic.py:409:        db_path = str(tmp_path / "persist_db")
backend/tests/e2e/conftest.py:174:def test_canvas_10_nodes(tmp_path: Path) -> Path:
backend/tests/e2e/conftest.py:183:        tmp_path: pytest temporary directory fixture
backend/tests/e2e/conftest.py:205:    canvas_dir = tmp_path / "test_vault"
backend/tests/e2e/conftest.py:217:def test_canvas_20_nodes(tmp_path: Path) -> Path:
backend/tests/e2e/conftest.py:242:    canvas_dir = tmp_path / "test_vault"
backend/tests/e2e/conftest.py:254:def test_canvas_100_nodes(tmp_path: Path) -> Path:
backend/tests/e2e/conftest.py:261:        tmp_path: pytest temporary directory fixture
backend/tests/e2e/conftest.py:283:    canvas_dir = tmp_path / "test_vault"
backend/tests/e2e/conftest.py:295:def test_canvas_with_failing_node(tmp_path: Path) -> Path:
backend/tests/e2e/conftest.py:334:    canvas_dir = tmp_path / "test_vault"
backend/tests/e2e/conftest.py:373:async def e2e_async_client(tmp_path: Path) -> AsyncGenerator[AsyncClient, None]:
backend/tests/e2e/conftest.py:380:    # Override settings to use tmp_path as canvas base
backend/tests/e2e/conftest.py:383:        settings.CANVAS_BASE_PATH = str(tmp_path)
backend/tests/integration/test_2_5_x_e2e.py:57:def _make_test_node(tmp_path):
backend/tests/integration/test_2_5_x_e2e.py:59:    nodes = tmp_path / "节点"
backend/tests/integration/test_2_5_x_e2e.py:74:async def test_e2e_full_accept_flow(tmp_path):
backend/tests/integration/test_2_5_x_e2e.py:76:    f = _make_test_node(tmp_path)
backend/tests/integration/test_2_5_x_e2e.py:132:async def test_e2e_accept_with_edits(tmp_path):
backend/tests/integration/test_2_5_x_e2e.py:134:    f = _make_test_node(tmp_path)
backend/tests/integration/test_2_5_x_e2e.py:169:async def test_e2e_dismiss_path_no_errors_written(tmp_path):
backend/tests/integration/test_2_5_x_e2e.py:171:    f = _make_test_node(tmp_path)
backend/tests/integration/test_2_5_x_e2e.py:194:async def test_e2e_dispute_path_writes_reason(tmp_path):
backend/tests/integration/test_2_5_x_e2e.py:196:    f = _make_test_node(tmp_path)
backend/tests/integration/test_2_5_x_e2e.py:223:async def test_e2e_session_id_accumulates_across_sessions(tmp_path):
backend/tests/integration/test_2_5_x_e2e.py:225:    f = _make_test_node(tmp_path)
backend/tests/integration/test_2_5_x_e2e.py:257:async def test_e2e_expired_old_pending_after_30_days(tmp_path):
backend/tests/integration/test_2_5_x_e2e.py:259:    f = _make_test_node(tmp_path)
backend/tests/integration/test_2_5_x_e2e.py:279:        tmp_path, expiry_days=30, now=future_now
backend/tests/integration/test_2_5_x_e2e.py:296:async def test_e2e_rebuild_graphiti_from_accepted_errors(tmp_path):
backend/tests/integration/test_2_5_x_e2e.py:298:    f = _make_test_node(tmp_path)
backend/tests/integration/test_2_5_x_e2e.py:317:            tmp_path, group_id="vault:cs_61b", dry_run=False
backend/tests/integration/test_2_5_x_e2e.py:328:async def test_e2e_rebuild_graphiti_dry_run_no_writes(tmp_path):
backend/tests/integration/test_2_5_x_e2e.py:330:    f = _make_test_node(tmp_path)
backend/tests/integration/test_2_5_x_e2e.py:347:            tmp_path, group_id="vault:cs_61b", dry_run=True
backend/tests/integration/test_2_5_x_e2e.py:361:async def test_e2e_double_accept_rejected_idempotency(tmp_path):
backend/tests/integration/test_2_5_x_e2e.py:365:    f = _make_test_node(tmp_path)
backend/tests/integration/test_2_5_x_e2e.py:385:async def test_e2e_dismiss_then_accept_rejected(tmp_path):
backend/tests/integration/test_2_5_x_e2e.py:389:    f = _make_test_node(tmp_path)
backend/tests/integration/test_verification_interactive_e2e.py:80:    with tempfile.TemporaryDirectory() as tmpdir:
backend/tests/integration/test_verification_interactive_e2e.py:81:        canvas_path = os.path.join(tmpdir, "离散数学.canvas")
backend/tests/integration/test_verification_interactive_e2e.py:84:        yield tmpdir
backend/tests/integration/test_story_38_7_ac2_learning_flow.py:28:    async def test_canvas_add_node_triggers_lancedb_index(self, tmp_path):
backend/tests/integration/test_story_38_7_ac2_learning_flow.py:35:        canvas_dir = tmp_path / "canvases"
backend/tests/integration/test_story_38_7_ac2_learning_flow.py:58:    async def test_canvas_update_node_triggers_lancedb_index(self, tmp_path):
backend/tests/integration/test_story_38_7_ac2_learning_flow.py:65:        canvas_dir = tmp_path / "canvases"
backend/tests/integration/test_story_38_7_ac2_learning_flow.py:101:            svc.schedule_index("test-canvas", "/tmp/canvases")
backend/tests/regression/test_targeting_material_isolation.py:20:def _write_node_md(tmp_path, node_id: str, front: str) -> None:
backend/tests/regression/test_targeting_material_isolation.py:21:    (tmp_path / f"{node_id}.md").write_text(f"---\n{front}---\n\n正文\n", encoding="utf-8")
backend/tests/regression/test_targeting_material_isolation.py:24:def _patch_md_dir(monkeypatch, tmp_path):
backend/tests/regression/test_targeting_material_isolation.py:28:        lambda nid: p if (p := tmp_path / f"{nid}.md").exists() else None,
backend/tests/regression/test_targeting_material_isolation.py:35:def test_errors_without_group_id_rejected(monkeypatch, tmp_path):
backend/tests/regression/test_targeting_material_isolation.py:38:        tmp_path,
backend/tests/regression/test_targeting_material_isolation.py:42:    _patch_md_dir(monkeypatch, tmp_path)
backend/tests/regression/test_targeting_material_isolation.py:46:def test_errors_with_matching_group_id_accepted(monkeypatch, tmp_path):
backend/tests/regression/test_targeting_material_isolation.py:48:        tmp_path,
backend/tests/regression/test_targeting_material_isolation.py:52:    _patch_md_dir(monkeypatch, tmp_path)
backend/tests/regression/test_targeting_material_isolation.py:56:def test_errors_with_foreign_group_id_rejected(monkeypatch, tmp_path):
backend/tests/regression/test_targeting_material_isolation.py:58:        tmp_path,
backend/tests/regression/test_targeting_material_isolation.py:62:    _patch_md_dir(monkeypatch, tmp_path)
backend/tests/regression/test_targeting_material_isolation.py:66:def test_tips_error_channel_still_works(monkeypatch, tmp_path):
backend/tests/regression/test_targeting_material_isolation.py:69:        tmp_path,
backend/tests/regression/test_targeting_material_isolation.py:73:    _patch_md_dir(monkeypatch, tmp_path)
backend/tests/regression/test_targeting_material_isolation.py:77:def test_misconception_preferred_over_description(monkeypatch, tmp_path):
backend/tests/regression/test_targeting_material_isolation.py:80:        tmp_path,
backend/tests/regression/test_targeting_material_isolation.py:85:    _patch_md_dir(monkeypatch, tmp_path)
backend/tests/regression/test_targeting_material_isolation.py:129:async def test_degraded_no_neighbor_errors(monkeypatch, tmp_path):
backend/tests/regression/test_targeting_material_isolation.py:130:    _patch_md_dir(monkeypatch, tmp_path)  # 邻居 md 不存在 → 无素材
backend/tests/regression/test_targeting_material_isolation.py:145:async def test_happy_path_not_degraded(monkeypatch, tmp_path):
backend/tests/regression/test_targeting_material_isolation.py:147:        tmp_path,
backend/tests/regression/test_targeting_material_isolation.py:151:    _patch_md_dir(monkeypatch, tmp_path)
backend/tests/regression/test_targeting_material_isolation.py:168:def test_disputed_candidate_text_excluded(monkeypatch, tmp_path):
backend/tests/regression/test_targeting_material_isolation.py:171:        tmp_path,
backend/tests/regression/test_targeting_material_isolation.py:177:    _patch_md_dir(monkeypatch, tmp_path)
backend/tests/regression/test_targeting_material_isolation.py:181:def test_non_disputed_candidate_does_not_block(monkeypatch, tmp_path):
backend/tests/regression/test_targeting_material_isolation.py:184:        tmp_path,
backend/tests/regression/test_targeting_material_isolation.py:189:    _patch_md_dir(monkeypatch, tmp_path)
backend/tests/regression/test_targeting_material_isolation.py:196:def test_disputed_fuzzy_variant_excluded(monkeypatch, tmp_path):
backend/tests/regression/test_targeting_material_isolation.py:199:        tmp_path,
backend/tests/regression/test_targeting_material_isolation.py:204:    _patch_md_dir(monkeypatch, tmp_path)
backend/tests/regression/test_targeting_material_isolation.py:208:def test_unrelated_text_not_fuzzy_excluded(monkeypatch, tmp_path):
backend/tests/regression/test_targeting_material_isolation.py:211:        tmp_path,
backend/tests/regression/test_targeting_material_isolation.py:216:    _patch_md_dir(monkeypatch, tmp_path)
backend/tests/integration/test_story_38_7_ac5_recovery_and_cross_story.py:34:    async def test_recover_failed_writes_replays_entries(self, tmp_path):
backend/tests/integration/test_story_38_7_ac5_recovery_and_cross_story.py:39:        failed_file = tmp_path / "failed_writes.jsonl"
backend/tests/integration/test_story_38_7_ac5_recovery_and_cross_story.py:74:    async def test_recover_failed_writes_keeps_still_pending(self, tmp_path):
backend/tests/integration/test_story_38_7_ac5_recovery_and_cross_story.py:78:        failed_file = tmp_path / "failed_writes.jsonl"
backend/tests/integration/test_story_38_7_ac5_recovery_and_cross_story.py:128:    async def test_lancedb_recover_pending_with_partial_failure(self, tmp_path):
backend/tests/integration/test_story_38_7_ac5_recovery_and_cross_story.py:136:        pending_file = tmp_path / "lancedb_pending_index.jsonl"
backend/tests/integration/test_story_38_7_ac5_recovery_and_cross_story.py:158:        result = await svc.recover_pending(str(tmp_path))
backend/tests/integration/test_story_38_7_ac5_recovery_and_cross_story.py:194:            tmp_file = f.name
backend/tests/integration/test_story_38_7_ac5_recovery_and_cross_story.py:198:                "app.services.memory_service.FAILED_WRITES_FILE", Path(tmp_file)
backend/tests/integration/test_story_38_7_ac5_recovery_and_cross_story.py:205:            Path(tmp_file).unlink(missing_ok=True)
backend/tests/integration/test_story_38_7_ac5_recovery_and_cross_story.py:242:    async def test_full_flow_canvas_to_history(self, tmp_path):
backend/tests/integration/test_story_38_7_ac5_recovery_and_cross_story.py:249:        canvas_dir = tmp_path / "canvases"
backend/tests/integration/test_story_38_7_ac5_recovery_and_cross_story.py:263:        canvas_svc._fallback_file_path = tmp_path / "fallback.json"
backend/tests/integration/test_multi_vault_isolation.py:387:    def test_errors_accept_candidate_vault_scoped(self, tmp_path):
backend/tests/integration/test_multi_vault_isolation.py:418:        captured_file = tmp_path / "X.md"
backend/tests/integration/test_canvas_edge_sync_real.py:107:    async def test_sync_edge_creates_relationship_in_neo4j(self, tmp_path):
backend/tests/integration/test_canvas_edge_sync_real.py:117:                canvas_base_path=str(tmp_path),
backend/tests/integration/test_canvas_edge_sync_real.py:144:    async def test_sync_edge_without_memory_client(self, tmp_path):
backend/tests/integration/test_canvas_edge_sync_real.py:146:        service = CanvasService(canvas_base_path=str(tmp_path), memory_client=None)
backend/tests/integration/test_canvas_edge_sync_real.py:157:    async def test_sync_edge_with_optional_label(self, tmp_path):
backend/tests/integration/test_canvas_edge_sync_real.py:167:                canvas_base_path=str(tmp_path),
backend/tests/integration/test_canvas_edge_sync_real.py:198:    async def test_add_edge_persists_to_canvas_and_neo4j(self, tmp_path):
backend/tests/integration/test_canvas_edge_sync_real.py:207:            canvas_path = tmp_path / "test.canvas"
backend/tests/integration/test_canvas_edge_sync_real.py:230:                canvas_base_path=str(tmp_path),
backend/tests/integration/test_canvas_edge_sync_real.py:268:    async def test_add_edge_returns_immediately_fire_and_forget(self, tmp_path):
backend/tests/integration/test_canvas_edge_sync_real.py:277:            canvas_path = tmp_path / "test.canvas"
backend/tests/integration/test_canvas_edge_sync_real.py:300:                canvas_base_path=str(tmp_path),
backend/tests/integration/test_canvas_edge_sync_real.py:328:    async def test_add_edge_succeeds_when_neo4j_unavailable(self, tmp_path):
backend/tests/integration/test_canvas_edge_sync_real.py:331:        canvas_path = tmp_path / "test.canvas"
backend/tests/integration/test_canvas_edge_sync_real.py:341:        service = CanvasService(canvas_base_path=str(tmp_path), memory_client=None)
backend/tests/regression/test_reference_config_fallback_contract.py:46:def test_reads_real_config_when_present(monkeypatch, tmp_path):
backend/tests/regression/test_reference_config_fallback_contract.py:48:    cfg = tmp_path / "reference_priority.json"
backend/tests/regression/test_reference_config_fallback_contract.py:75:def test_missing_file_degrades_to_neutral_not_legacy_weights(monkeypatch, tmp_path):
backend/tests/regression/test_reference_config_fallback_contract.py:77:    _point_config_at(monkeypatch, tmp_path / "does-not-exist.json")
backend/tests/regression/test_reference_config_fallback_contract.py:85:def test_missing_file_logs_error_not_silence(monkeypatch, tmp_path, caplog):
backend/tests/regression/test_reference_config_fallback_contract.py:87:    _point_config_at(monkeypatch, tmp_path / "does-not-exist.json")
backend/tests/regression/test_reference_config_fallback_contract.py:100:def test_corrupt_json_degrades_to_neutral(monkeypatch, tmp_path):
backend/tests/regression/test_reference_config_fallback_contract.py:102:    cfg = tmp_path / "reference_priority.json"
backend/tests/regression/test_reference_config_fallback_contract.py:113:def test_fallback_never_ranks_videos_above_handwritten(monkeypatch, tmp_path):
backend/tests/regression/test_reference_config_fallback_contract.py:120:        ("missing", tmp_path / "nope.json"),
backend/tests/regression/test_reference_config_fallback_contract.py:121:        ("corrupt", tmp_path / "bad.json"),
backend/tests/regression/test_reference_config_fallback_contract.py:137:def test_no_legacy_weight_literals_remain_in_module(monkeypatch, tmp_path):
backend/tests/regression/test_reference_config_fallback_contract.py:172:def test_malformed_schema_degrades_neutrally_without_crashing(monkeypatch, tmp_path, label, content):
backend/tests/regression/test_reference_config_fallback_contract.py:179:    cfg = tmp_path / "reference_priority.json"
backend/tests/regression/test_reference_config_fallback_contract.py:191:def test_get_max_references_never_falls_back_to_legacy_five(monkeypatch, tmp_path):
backend/tests/regression/test_reference_config_fallback_contract.py:203:def test_valid_config_still_accepted_after_validator(monkeypatch, tmp_path):
backend/tests/regression/test_reference_config_fallback_contract.py:205:    cfg = tmp_path / "reference_priority.json"
backend/tests/regression/test_reference_config_fallback_contract.py:228:def test_apply_source_priority_is_identity_under_neutral_fallback(monkeypatch, tmp_path):
backend/tests/regression/test_reference_config_fallback_contract.py:230:    _point_config_at(monkeypatch, tmp_path / "absent.json")
backend/tests/integration/test_edge_neo4j_sync.py:51:def canvas_service(memory_service, tmp_path):
backend/tests/integration/test_edge_neo4j_sync.py:55:    return CanvasService(canvas_base_path=str(tmp_path), memory_client=memory_service)
backend/tests/integration/test_edge_neo4j_sync.py:59:def sample_canvas_file(tmp_path):
backend/tests/integration/test_edge_neo4j_sync.py:80:    canvas_path = tmp_path / "integration_test.canvas"
backend/tests/integration/test_edge_neo4j_sync.py:134:async def test_canvas_operation_succeeds_without_neo4j(tmp_path):
backend/tests/integration/test_edge_neo4j_sync.py:169:    canvas_path = tmp_path / "fail_test.canvas"
backend/tests/integration/test_edge_neo4j_sync.py:173:    service = CanvasService(canvas_base_path=str(tmp_path), memory_client=mock_memory)
backend/tests/integration/test_edge_neo4j_sync.py:262:    memory_service, tmp_path, neo4j_client
backend/tests/integration/test_edge_neo4j_sync.py:278:    chinese_dir = tmp_path / "笔记库" / "离散数学"
backend/tests/integration/test_edge_neo4j_sync.py:284:        canvas_base_path=str(tmp_path), memory_client=memory_service
backend/tests/integration/test_multimodal_real_persistence.py:41:def real_storage_dir(tmp_path):
backend/tests/integration/test_multimodal_real_persistence.py:42:    """使用 tmp_path 创建真实临时目录，不使用 mock.
backend/tests/integration/test_multimodal_real_persistence.py:46:    storage = tmp_path / ".canvas-learning" / "multimodal"
backend/tests/integration/test_story_30_21_real_integration.py:419:async def test_json_fallback_data_persistence(tmp_path):
backend/tests/integration/test_story_30_21_real_integration.py:430:    json_storage = tmp_path / "neo4j_memory.json"
backend/tests/integration/test_story_30_21_real_integration.py:492:async def test_json_fallback_warning_log(tmp_path, caplog):
backend/tests/integration/test_story_30_21_real_integration.py:501:    json_storage = tmp_path / "neo4j_fallback_log.json"
backend/tests/integration/test_story_30_21_real_integration.py:533:async def test_json_fallback_event_queryable(tmp_path):
backend/tests/integration/test_story_30_21_real_integration.py:542:    json_storage = tmp_path / "neo4j_query.json"
backend/tests/unit/test_story_38_5_canvas_crud_degradation.py:34:    async def test_trigger_event_writes_json_when_memory_client_none(self, tmp_path):
backend/tests/unit/test_story_38_5_canvas_crud_degradation.py:43:        fallback_file = tmp_path / "canvas_events_fallback.json"
backend/tests/unit/test_story_38_5_canvas_crud_degradation.py:44:        service = CanvasService(canvas_base_path=str(tmp_path), memory_client=None)
backend/tests/unit/test_story_38_5_canvas_crud_degradation.py:68:    async def test_no_fallback_file_when_dual_write_disabled(self, tmp_path):
backend/tests/unit/test_story_38_5_canvas_crud_degradation.py:78:        fallback_file = tmp_path / "canvas_events_fallback.json"
backend/tests/unit/test_story_38_5_canvas_crud_degradation.py:79:        service = CanvasService(canvas_base_path=str(tmp_path), memory_client=None)
backend/tests/unit/test_story_38_5_canvas_crud_degradation.py:96:    async def test_crud_add_node_succeeds_when_memory_client_none(self, tmp_path):
backend/tests/unit/test_story_38_5_canvas_crud_degradation.py:106:        canvas_file = tmp_path / "test.canvas"
backend/tests/unit/test_story_38_5_canvas_crud_degradation.py:109:        service = CanvasService(canvas_base_path=str(tmp_path), memory_client=None)
backend/tests/unit/test_story_38_5_canvas_crud_degradation.py:126:    async def test_edge_sync_writes_json_when_neo4j_none(self, tmp_path):
backend/tests/unit/test_story_38_5_canvas_crud_degradation.py:134:        fallback_file = tmp_path / "canvas_events_fallback.json"
backend/tests/unit/test_story_38_5_canvas_crud_degradation.py:139:            canvas_base_path=str(tmp_path), memory_client=mock_memory
backend/tests/unit/test_story_38_5_canvas_crud_degradation.py:159:    async def test_trigger_event_fallback_when_record_temporal_raises(self, tmp_path):
backend/tests/unit/test_story_38_5_canvas_crud_degradation.py:168:        fallback_file = tmp_path / "canvas_events_fallback.json"
backend/tests/unit/test_story_38_5_canvas_crud_degradation.py:175:            canvas_base_path=str(tmp_path), memory_client=mock_memory
backend/tests/unit/test_story_38_5_canvas_crud_degradation.py:201:    async def test_trigger_event_fallback_when_neo4j_slow_timeout(self, tmp_path):
backend/tests/unit/test_story_38_5_canvas_crud_degradation.py:212:        fallback_file = tmp_path / "canvas_events_fallback.json"
backend/tests/unit/test_story_38_5_canvas_crud_degradation.py:222:            canvas_base_path=str(tmp_path), memory_client=mock_memory
backend/tests/integration/test_dual_write_consistency.py:149:        self, real_neo4j_client, test_event_data, tmp_path
backend/tests/integration/test_dual_write_consistency.py:163:        json_file = tmp_path / "test_learning_memories.json"
backend/tests/integration/test_dual_write_consistency.py:266:        self, test_event_data, tmp_path
backend/tests/integration/test_dual_write_consistency.py:288:        json_file = tmp_path / "test_memories.json"
backend/tests/integration/test_dual_write_consistency.py:330:    async def test_graphiti_write_retry_mechanism(self, tmp_path):
backend/tests/integration/test_dual_write_consistency.py:386:    async def test_graphiti_write_max_retries_exceeded(self, tmp_path):
backend/tests/integration/test_dual_write_consistency.py:519:        async def write_event(concept: str, index: int):
backend/tests/integration/test_story_38_7_qa_supplement.py:170:        self, tmp_path
backend/tests/integration/test_story_38_7_qa_supplement.py:178:        canvas_dir = tmp_path / "canvases"
backend/tests/integration/test_story_38_7_qa_supplement.py:185:        svc._fallback_file_path = tmp_path / "canvas_events_fallback.json"
backend/tests/integration/test_story_38_7_qa_supplement.py:224:    def test_failed_write_contains_all_required_fields(self, tmp_path):
backend/tests/integration/test_story_38_7_qa_supplement.py:231:        failed_file = tmp_path / "failed_writes.jsonl"
backend/tests/integration/test_story_38_7_qa_supplement.py:267:    def test_multiple_failed_writes_are_appended_not_overwritten(self, tmp_path):
backend/tests/integration/test_story_38_7_qa_supplement.py:273:        failed_file = tmp_path / "failed_writes.jsonl"
backend/tests/unit/test_candidate_expiry_service.py:139:async def test_expire_old_pending_candidate_marked_expired(tmp_path):
backend/tests/unit/test_candidate_expiry_service.py:141:    nodes = tmp_path / "节点"
backend/tests/unit/test_candidate_expiry_service.py:153:        tmp_path, expiry_days=30, now=now
backend/tests/unit/test_candidate_expiry_service.py:170:async def test_expire_recent_pending_not_changed(tmp_path):
backend/tests/unit/test_candidate_expiry_service.py:172:    nodes = tmp_path / "节点"
backend/tests/unit/test_candidate_expiry_service.py:182:        tmp_path, expiry_days=30, now=now
backend/tests/unit/test_candidate_expiry_service.py:193:async def test_expire_skips_terminal_status(tmp_path):
backend/tests/unit/test_candidate_expiry_service.py:195:    nodes = tmp_path / "节点"
backend/tests/unit/test_candidate_expiry_service.py:210:        tmp_path, expiry_days=30, now=now
backend/tests/unit/test_candidate_expiry_service.py:222:async def test_expire_idempotent_second_run_no_change(tmp_path):
backend/tests/unit/test_candidate_expiry_service.py:224:    nodes = tmp_path / "节点"
backend/tests/unit/test_candidate_expiry_service.py:232:    stats1 = await expire_pending_candidates(tmp_path, expiry_days=30, now=now)
backend/tests/unit/test_candidate_expiry_service.py:236:    stats2 = await expire_pending_candidates(tmp_path, expiry_days=30, now=now)
backend/tests/unit/test_candidate_expiry_service.py:242:async def test_expire_mixed_pending_keeps_recent_expires_old(tmp_path):
backend/tests/unit/test_candidate_expiry_service.py:244:    nodes = tmp_path / "节点"
backend/tests/unit/test_candidate_expiry_service.py:256:    stats = await expire_pending_candidates(tmp_path, expiry_days=30, now=now)
backend/tests/unit/test_candidate_expiry_service.py:267:async def test_expire_no_candidates_in_file_skipped(tmp_path):
backend/tests/unit/test_candidate_expiry_service.py:269:    nodes = tmp_path / "节点"
backend/tests/unit/test_candidate_expiry_service.py:275:    stats = await expire_pending_candidates(tmp_path, expiry_days=30, now=now)
backend/tests/unit/test_candidate_expiry_service.py:283:async def test_expire_vault_not_exist_returns_empty(tmp_path):
backend/tests/unit/test_candidate_expiry_service.py:286:        tmp_path / "missing", expiry_days=30
backend/tests/unit/test_candidate_expiry_service.py:293:async def test_expire_no_created_at_field_skipped(tmp_path):
backend/tests/unit/test_candidate_expiry_service.py:295:    nodes = tmp_path / "节点"
backend/tests/unit/test_candidate_expiry_service.py:301:    stats = await expire_pending_candidates(tmp_path, expiry_days=30, now=now)
backend/tests/unit/test_candidate_expiry_service.py:308:async def test_expire_only_writes_when_changes_exist(tmp_path):
backend/tests/unit/test_candidate_expiry_service.py:310:    nodes = tmp_path / "节点"
backend/tests/unit/test_candidate_expiry_service.py:323:    await expire_pending_candidates(tmp_path, expiry_days=30, now=now)
backend/tests/unit/test_candidate_expiry_service.py:331:async def test_expire_multiple_files_processed_independently(tmp_path):
backend/tests/unit/test_candidate_expiry_service.py:333:    nodes = tmp_path / "节点"
backend/tests/unit/test_candidate_expiry_service.py:345:    stats = await expire_pending_candidates(tmp_path, expiry_days=30, now=now)
backend/tests/unit/test_candidate_expiry_service.py:363:async def test_expire_stats_includes_cutoff_iso(tmp_path):
backend/tests/unit/test_candidate_expiry_service.py:365:    nodes = tmp_path / "节点"
backend/tests/unit/test_candidate_expiry_service.py:370:    stats = await expire_pending_candidates(tmp_path, expiry_days=30, now=now)
backend/tests/unit/test_candidate_writer.py:52:def _make_md_with_frontmatter(tmp_path, body: str = "# Body\n") -> "Path":
backend/tests/unit/test_candidate_writer.py:54:    f = tmp_path / "test_node.md"
backend/tests/unit/test_candidate_writer.py:71:def test_candidate_writes_to_error_candidates_array(tmp_path):
backend/tests/unit/test_candidate_writer.py:73:    f = _make_md_with_frontmatter(tmp_path)
backend/tests/unit/test_candidate_writer.py:118:def test_candidate_writes_optional_metadata_fields(tmp_path):
backend/tests/unit/test_candidate_writer.py:120:    f = _make_md_with_frontmatter(tmp_path)
backend/tests/unit/test_candidate_writer.py:142:def test_candidate_optional_metadata_defaults_to_none_or_empty(tmp_path):
backend/tests/unit/test_candidate_writer.py:144:    f = _make_md_with_frontmatter(tmp_path)
backend/tests/unit/test_candidate_writer.py:164:def test_candidate_dedupe_updates_existing_not_append(tmp_path):
backend/tests/unit/test_candidate_writer.py:166:    f = _make_md_with_frontmatter(tmp_path)
backend/tests/unit/test_candidate_writer.py:192:def test_candidate_dedupe_hash_excludes_session_id(tmp_path):
backend/tests/unit/test_candidate_writer.py:194:    f = _make_md_with_frontmatter(tmp_path)
backend/tests/unit/test_candidate_writer.py:221:def test_candidate_dedupe_takes_max_confidence(tmp_path):
backend/tests/unit/test_candidate_writer.py:223:    f = _make_md_with_frontmatter(tmp_path)
backend/tests/unit/test_candidate_writer.py:240:def test_candidate_different_descriptions_append_separately(tmp_path):
backend/tests/unit/test_candidate_writer.py:242:    f = _make_md_with_frontmatter(tmp_path)
backend/tests/unit/test_candidate_writer.py:264:async def test_dual_mode_default_is_candidate_only(tmp_path):
backend/tests/unit/test_candidate_writer.py:266:    f = _make_md_with_frontmatter(tmp_path)
backend/tests/unit/test_candidate_writer.py:281:async def test_dual_mode_candidate_only_writes_candidates_not_errors(tmp_path):
backend/tests/unit/test_candidate_writer.py:283:    f = _make_md_with_frontmatter(tmp_path)
backend/tests/unit/test_candidate_writer.py:299:async def test_dual_mode_candidate_only_does_not_call_graphiti(tmp_path):
backend/tests/unit/test_candidate_writer.py:301:    f = _make_md_with_frontmatter(tmp_path)
backend/tests/unit/test_candidate_writer.py:319:async def test_dual_mode_write_confirmed_legacy_behavior(tmp_path):
backend/tests/unit/test_candidate_writer.py:321:    f = _make_md_with_frontmatter(tmp_path)
backend/tests/unit/test_candidate_writer.py:355:async def test_dual_mode_write_confirmed_returns_error_id_not_candidate_id(tmp_path):
backend/tests/unit/test_candidate_writer.py:357:    f = _make_md_with_frontmatter(tmp_path)
backend/tests/unit/test_candidate_writer.py:370:async def test_dual_mode_candidate_only_returns_candidate_id_not_error_id(tmp_path):
backend/tests/unit/test_candidate_writer.py:372:    f = _make_md_with_frontmatter(tmp_path)
backend/tests/unit/test_candidate_writer.py:389:async def test_async_wrapper_uses_per_file_lock(tmp_path):
backend/tests/unit/test_candidate_writer.py:391:    f = _make_md_with_frontmatter(tmp_path)
backend/tests/unit/test_candidate_writer.py:410:def test_candidate_file_not_found_returns_false(tmp_path):
backend/tests/unit/test_candidate_writer.py:412:    f = tmp_path / "missing.md"  # 不创建
backend/tests/unit/test_candidate_writer.py:422:def test_candidate_appends_to_existing_errors_array_independently(tmp_path):
backend/tests/unit/test_candidate_writer.py:424:    f = tmp_path / "node.md"
backend/tests/regression/test_rag_stage1_index_contracts.py:5:# 组 C SLO (真 LanceDB tmp 库): 新增/修改/删除/停机补齐 一轮 reconcile 内生效
backend/tests/regression/test_rag_stage1_index_contracts.py:8:# 测试基建: LanceDB 用 tmp_path 真库 (vault_id="testvault" 显式隔离);
backend/tests/regression/test_rag_stage1_index_contracts.py:29:def tmp_vault(tmp_path):
backend/tests/regression/test_rag_stage1_index_contracts.py:31:    vault = tmp_path / "vault"
backend/tests/regression/test_rag_stage1_index_contracts.py:44:def orch(tmp_vault, tmp_path, monkeypatch):
backend/tests/regression/test_rag_stage1_index_contracts.py:45:    """Orchestrator wired to a REAL LanceDB in tmp_path with a test-double
backend/tests/regression/test_rag_stage1_index_contracts.py:51:    client = LanceDBClient(db_path=str(tmp_path / "db"), vault_id="testvault")
backend/tests/regression/test_rag_stage1_index_contracts.py:54:    o = VaultIndexOrchestrator(vault_path=str(tmp_vault))
backend/tests/regression/test_rag_stage1_index_contracts.py:56:    o._pending_file = tmp_path / "pending.jsonl"
backend/tests/regression/test_rag_stage1_index_contracts.py:95:async def test_a3_event_during_inflight_marks_dirty_and_replays(orch, tmp_vault):
backend/tests/regression/test_rag_stage1_index_contracts.py:96:    _write_note(tmp_vault, "节点/a.md", "# A\n\nv1")
backend/tests/regression/test_rag_stage1_index_contracts.py:112:async def test_a4_pending_survives_restart(orch, tmp_vault, tmp_path):
backend/tests/regression/test_rag_stage1_index_contracts.py:117:    fresh = VaultIndexOrchestrator(vault_path=str(tmp_vault))
backend/tests/regression/test_rag_stage1_index_contracts.py:118:    fresh._pending_file = tmp_path / "pending.jsonl"
backend/tests/regression/test_rag_stage1_index_contracts.py:146:async def test_a8_delete_op_clears_chunks_and_fingerprint(orch, tmp_vault):
backend/tests/regression/test_rag_stage1_index_contracts.py:147:    _write_note(tmp_vault, "节点/a.md", "# A\n\n内容一二三")
backend/tests/regression/test_rag_stage1_index_contracts.py:159:async def test_a9_rename_leaves_no_ghost_chunks(orch, tmp_vault):
backend/tests/regression/test_rag_stage1_index_contracts.py:160:    p = _write_note(tmp_vault, "节点/old.md", "# Old\n\n同一份内容")
backend/tests/regression/test_rag_stage1_index_contracts.py:165:    p.rename(tmp_vault / "节点" / "new.md")
backend/tests/regression/test_rag_stage1_index_contracts.py:190:async def test_a13_empty_output_files_do_not_loop_forever(orch, tmp_vault):
backend/tests/regression/test_rag_stage1_index_contracts.py:193:    _write_note(tmp_vault, "节点/empty.md", "")
backend/tests/regression/test_rag_stage1_index_contracts.py:203:    _write_note(tmp_vault, "节点/shrink.md", "# S\n\n有内容")
backend/tests/regression/test_rag_stage1_index_contracts.py:207:    _write_note(tmp_vault, "节点/shrink.md", "")
backend/tests/regression/test_rag_stage1_index_contracts.py:296:async def test_c1_new_file_searchable_after_one_reconcile(orch, tmp_vault):
backend/tests/regression/test_rag_stage1_index_contracts.py:297:    _write_note(tmp_vault, "节点/特征值.md", "# 特征值\n\nAv = λv 的缩放因子")
backend/tests/regression/test_rag_stage1_index_contracts.py:304:async def test_c2_modified_file_content_updates(orch, tmp_vault):
backend/tests/regression/test_rag_stage1_index_contracts.py:305:    _write_note(tmp_vault, "节点/a.md", "# A\n\n旧内容")
backend/tests/regression/test_rag_stage1_index_contracts.py:309:    _write_note(tmp_vault, "节点/a.md", "# A\n\n新内容已经替换")
backend/tests/regression/test_rag_stage1_index_contracts.py:322:async def test_c3_deleted_file_not_searchable(orch, tmp_vault):
backend/tests/regression/test_rag_stage1_index_contracts.py:323:    p = _write_note(tmp_vault, "节点/a.md", "# A\n\n内容")
backend/tests/regression/test_rag_stage1_index_contracts.py:335:async def test_c4_startup_reconciliation_catches_offline_changes(orch, tmp_vault, tmp_path):
backend/tests/regression/test_rag_stage1_index_contracts.py:337:    _write_note(tmp_vault, "节点/downtime.md", "# 停机期间新增\n\n内容")
backend/tests/regression/test_rag_stage1_index_contracts.py:339:    fresh = VaultIndexOrchestrator(vault_path=str(tmp_vault))
backend/tests/regression/test_rag_stage1_index_contracts.py:341:    fresh._pending_file = tmp_path / "pending2.jsonl"
backend/tests/regression/test_rag_stage1_index_contracts.py:353:async def test_d1_batch_write_rebuilds_fts_once(orch, tmp_vault, monkeypatch):
backend/tests/regression/test_rag_stage1_index_contracts.py:363:    _write_note(tmp_vault, "节点/a.md", "# A\n\n甲")
backend/tests/regression/test_rag_stage1_index_contracts.py:364:    _write_note(tmp_vault, "节点/b.md", "# B\n\n乙")
backend/tests/regression/test_rag_stage1_index_contracts.py:371:async def test_d2_refresh_changed_reaches_lancedb(orch, tmp_vault, monkeypatch):
backend/tests/regression/test_rag_stage1_index_contracts.py:381:    _write_note(tmp_vault, "节点/via_endpoint.md", "# E\n\n经端点入库")
backend/tests/regression/test_rag_stage1_index_contracts.py:397:async def test_d4_resolve_prefers_prefixed_table(orch, tmp_vault):
backend/tests/regression/test_rag_stage1_index_contracts.py:398:    _write_note(tmp_vault, "节点/a.md", "# A\n\n内容")
backend/tests/regression/test_rag_stage1_index_contracts.py:405:async def test_d6_orphan_sweep_purges_rows_blacklisted_after_indexing(orch, tmp_vault, monkeypatch):
backend/tests/regression/test_rag_stage1_index_contracts.py:409:    _write_note(tmp_vault, "旧目录/legacy.md", "# L\n\n入库时还合法的内容")
backend/tests/regression/test_rag_stage1_index_contracts.py:421:async def test_d5_incremental_endpoint_enforces_blacklist(orch, tmp_vault):
backend/tests/regression/test_rag_stage1_index_contracts.py:424:    _write_note(tmp_vault, "检验白板/exam.md", "# 考题\n\n答案不许回流")
backend/tests/regression/test_rag_stage1_index_contracts.py:426:        file_path=str(tmp_vault / "检验白板" / "exam.md"),
backend/tests/regression/test_rag_stage1_index_contracts.py:428:        vault_path=str(tmp_vault),
backend/tests/regression/test_rag_stage1_index_contracts.py:439:async def test_e1_embed_outage_is_loud_not_silent_success(orch, tmp_vault, monkeypatch):
backend/tests/regression/test_rag_stage1_index_contracts.py:453:    _write_note(tmp_vault, "节点/a.md", "# A\n\n内容")
backend/tests/regression/test_rag_stage1_index_contracts.py:465:async def test_e2_short_write_never_commits_fingerprint(orch, tmp_vault, monkeypatch):
backend/tests/regression/test_rag_stage1_index_contracts.py:475:    _write_note(tmp_vault, "节点/a.md", "# A\n\n内容")
backend/tests/regression/test_rag_stage1_index_contracts.py:493:async def test_e4_backoff_survives_reconcile_but_user_event_resets(orch, tmp_vault, monkeypatch):
backend/tests/regression/test_daily_review_run.py:35:def _vault(tmp_path, nodes: dict, name: str = "vault") -> Path:
backend/tests/regression/test_daily_review_run.py:36:    vault = tmp_path / name
backend/tests/regression/test_daily_review_run.py:46:def _patch_runner(monkeypatch, vault, tmp_path):
backend/tests/regression/test_daily_review_run.py:48:    fixture 只注入 BACKUPS 一处 — 所有 state/log 写入随之进 tmp, 防写真实
backend/tests/regression/test_daily_review_run.py:49:    backups/。逐用例检查: 本文件所有落盘路径均经 VAULT (tmp) 或 BACKUPS (tmp)。"""
backend/tests/regression/test_daily_review_run.py:51:    monkeypatch.setattr(runner, "BACKUPS", tmp_path / "backups")
backend/tests/regression/test_daily_review_run.py:69:def test_node_change_invalidates_same_day_cache(tmp_path, monkeypatch):
backend/tests/regression/test_daily_review_run.py:70:    vault = _vault(tmp_path, {"甲": _node()})
backend/tests/regression/test_daily_review_run.py:71:    _patch_runner(monkeypatch, vault, tmp_path)
backend/tests/regression/test_daily_review_run.py:92:def test_unchanged_pool_still_cached(tmp_path, monkeypatch):
backend/tests/regression/test_daily_review_run.py:93:    vault = _vault(tmp_path, {"甲": _node()})
backend/tests/regression/test_daily_review_run.py:94:    _patch_runner(monkeypatch, vault, tmp_path)
backend/tests/regression/test_daily_review_run.py:109:def test_rescan_keeps_same_day_push_skip_done(tmp_path, monkeypatch, capsys):
backend/tests/regression/test_daily_review_run.py:110:    vault = _vault(tmp_path, {"甲": _node()})
backend/tests/regression/test_daily_review_run.py:111:    _patch_runner(monkeypatch, vault, tmp_path)
backend/tests/regression/test_daily_review_run.py:151:def test_infile_update_alone_triggers_rescan(tmp_path, monkeypatch):
backend/tests/regression/test_daily_review_run.py:154:    vault = _vault(tmp_path, {"甲": _node()})
backend/tests/regression/test_daily_review_run.py:155:    _patch_runner(monkeypatch, vault, tmp_path)
backend/tests/regression/test_daily_review_run.py:167:def test_deletion_via_dir_mtime_triggers_rescan(tmp_path, monkeypatch):
backend/tests/regression/test_daily_review_run.py:170:    vault = _vault(tmp_path, {"甲": _node(), "乙": _node()})
backend/tests/regression/test_daily_review_run.py:171:    _patch_runner(monkeypatch, vault, tmp_path)
backend/tests/regression/test_daily_review_run.py:189:def test_write_during_scan_window_not_lost(tmp_path, monkeypatch):
backend/tests/regression/test_daily_review_run.py:193:    vault = _vault(tmp_path, {"甲": _node()})
backend/tests/regression/test_daily_review_run.py:194:    _patch_runner(monkeypatch, vault, tmp_path)
backend/tests/regression/test_daily_review_run.py:225:def test_time_crossing_future_due_invalidates_cache(tmp_path, monkeypatch):
backend/tests/regression/test_daily_review_run.py:227:        tmp_path,
backend/tests/regression/test_daily_review_run.py:230:    _patch_runner(monkeypatch, vault, tmp_path)
backend/tests/regression/test_daily_review_run.py:267:def test_rescan_does_not_touch_board_last_recommended(tmp_path, monkeypatch):
backend/tests/regression/test_daily_review_run.py:268:    vault = _vault(tmp_path, {"a甲": _node(board="A板")})
backend/tests/regression/test_daily_review_run.py:269:    _patch_runner(monkeypatch, vault, tmp_path)
backend/tests/regression/test_daily_review_run.py:291:def test_two_vaults_same_day_push_and_state_isolated(tmp_path, monkeypatch, capsys):
backend/tests/regression/test_daily_review_run.py:299:    vault_a = _vault(tmp_path, {"甲": _node()}, name="vaultA")
backend/tests/regression/test_daily_review_run.py:300:    vault_b = _vault(tmp_path, {"乙": _node()}, name="vaultB")
backend/tests/regression/test_daily_review_run.py:301:    monkeypatch.setattr(runner, "BACKUPS", tmp_path / "backups")
backend/tests/regression/test_daily_review_run.py:334:    state_a = tmp_path / "backups" / "daily-review.vaultA.state.json"
backend/tests/regression/test_daily_review_run.py:335:    state_b = tmp_path / "backups" / "daily-review.vaultB.state.json"
backend/tests/regression/test_daily_review_run.py:351:    log_text = (tmp_path / "backups" / "daily-review.log").read_text(encoding="utf-8")
backend/tests/regression/test_daily_review_run.py:355:def test_payload_carries_top_level_vault_id(tmp_path, monkeypatch):
backend/tests/regression/test_daily_review_run.py:358:    vault = _vault(tmp_path, {"甲": _node()}, name="vaultA")
backend/tests/regression/test_daily_review_run.py:359:    _patch_runner(monkeypatch, vault, tmp_path)
backend/tests/regression/test_daily_review_run.py:373:def _capture_bark_request(monkeypatch, tmp_path) -> dict:
backend/tests/regression/test_daily_review_run.py:377:    key_file = tmp_path / "bark.key"
backend/tests/regression/test_daily_review_run.py:402:def test_send_bark_composes_vault_scoped_id_and_group(tmp_path, monkeypatch):
backend/tests/regression/test_daily_review_run.py:403:    captured = _capture_bark_request(monkeypatch, tmp_path)
backend/tests/regression/test_daily_review_run.py:413:def test_send_bark_without_vault_id_keeps_legacy_shape(tmp_path, monkeypatch):
backend/tests/regression/test_daily_review_run.py:415:    captured = _capture_bark_request(monkeypatch, tmp_path)
backend/tests/regression/test_daily_review_run.py:442:    assert vault_key("/tmp/x/canvas-vault/") == "canvas-vault"
backend/tests/regression/test_daily_review_run.py:448:def _old_state_fixture(tmp_path) -> Path:
backend/tests/regression/test_daily_review_run.py:449:    backups = tmp_path / "backups"
backend/tests/regression/test_daily_review_run.py:465:def test_migrate_dry_run_writes_nothing(tmp_path, monkeypatch, capsys):
backend/tests/regression/test_daily_review_run.py:466:    backups = _old_state_fixture(tmp_path)
backend/tests/regression/test_daily_review_run.py:477:def test_migrate_apply_keeps_bak_and_refuses_overwrite(tmp_path, monkeypatch, capsys):
backend/tests/regression/test_daily_review_run.py:478:    backups = _old_state_fixture(tmp_path)
backend/tests/regression/test_daily_review_run.py:495:def test_migrate_symlink_vault_arg_matches_runner_key(tmp_path, monkeypatch):
backend/tests/regression/test_daily_review_run.py:498:    backups = _old_state_fixture(tmp_path)
backend/tests/regression/test_daily_review_run.py:499:    real = _vault(tmp_path, {"甲": _node()}, name="真库")
backend/tests/regression/test_daily_review_run.py:500:    link = tmp_path / "alias"
backend/tests/regression/test_daily_review_run.py:510:def test_migrate_crlf_state_byte_identical_and_idempotent(tmp_path, monkeypatch, capsys):
backend/tests/regression/test_daily_review_run.py:513:    backups = tmp_path / "backups"
backend/tests/regression/test_daily_review_run.py:526:def test_migrate_refuses_non_dict_state(tmp_path, monkeypatch, capsys):
backend/tests/regression/test_daily_review_run.py:529:    backups = tmp_path / "backups"
backend/tests/regression/test_daily_review_run.py:539:def test_migrate_refuses_overwriting_existing_bak(tmp_path, monkeypatch):
backend/tests/regression/test_daily_review_run.py:542:    backups = _old_state_fixture(tmp_path)
backend/tests/regression/test_daily_review_run.py:551:def test_migrate_interrupted_states_have_explicit_exits(tmp_path, monkeypatch, capsys):
backend/tests/regression/test_daily_review_run.py:555:    backups = tmp_path / "backups"
backend/tests/regression/test_daily_review_run.py:576:def test_migrate_preplanted_symlink_target_not_overwritten(tmp_path, monkeypatch):
backend/tests/regression/test_daily_review_run.py:580:    backups = _old_state_fixture(tmp_path)
backend/tests/regression/test_daily_review_run.py:581:    hijack_target = tmp_path / "劫持目标.json"  # 不存在 → 悬空 symlink 过得了 exists 预检
backend/tests/regression/test_sync_board_concepts.py:4:契约测试用 sys.path import 真相源, 在 tmp vault 上跑真实读写。
backend/tests/regression/test_sync_board_concepts.py:12:  M6 权限 0644→0600 / M7 无 fsync / M9 行尾归一 / M10 doc_count 只改首处
backend/tests/regression/test_sync_board_concepts.py:45:def vault(tmp_path: Path) -> Path:
backend/tests/regression/test_sync_board_concepts.py:46:    v = tmp_path / "vault"
backend/tests/regression/test_projection_sync_ghost_edges.py:13:def _make_vault(tmp_path: Path) -> Path:
backend/tests/regression/test_projection_sync_ghost_edges.py:14:    vault = tmp_path / "vault"
backend/tests/regression/test_projection_sync_ghost_edges.py:32:async def test_broken_frontmatter_protects_old_edges(tmp_path):
backend/tests/regression/test_projection_sync_ghost_edges.py:34:    vault = _make_vault(tmp_path)
backend/tests/regression/test_projection_sync_ghost_edges.py:49:async def test_missing_relationships_field_not_protected(tmp_path):
backend/tests/regression/test_projection_sync_ghost_edges.py:51:    vault = _make_vault(tmp_path)
backend/tests/regression/test_projection_sync_ghost_edges.py:58:async def test_merge_failure_edge_still_alive(tmp_path):
backend/tests/regression/test_projection_sync_ghost_edges.py:60:    vault = _make_vault(tmp_path)
backend/tests/regression/test_all_index_entrypoints_hostile_env.py:376:async def test_entrypoint_by_node_rejects_hostile_paths(hostile_vault, tmp_path):
backend/tests/regression/test_all_index_entrypoints_hostile_env.py:383:    real_outside = tmp_path / "real.md"
backend/tests/regression/test_all_index_entrypoints_hostile_env.py:434:def test_entrypoint_error_rebuild_root_fallback_rejected(tmp_path):
backend/tests/regression/test_all_index_entrypoints_hostile_env.py:438:    (tmp_path / "x.md").write_text("x", encoding="utf-8")
backend/tests/regression/test_all_index_entrypoints_hostile_env.py:440:    assert _scan_vault_md_files(tmp_path) == []
backend/tests/regression/test_all_index_entrypoints_hostile_env.py:447:async def test_ancestor_dotdir_vault_not_zeroed_out(tmp_path):
backend/tests/regression/test_all_index_entrypoints_hostile_env.py:454:    vault = tmp_path / ".dotdir" / "vault"
backend/tests/unit/test_bug_tracker.py:133:    def test_log_error_creates_directory(self, tmp_path: Path):
backend/tests/unit/test_bug_tracker.py:139:        log_path = tmp_path / "nested" / "dir" / "bug_log.jsonl"
backend/tests/unit/test_bug_tracker.py:151:    def test_log_error_creates_file(self, tmp_path: Path):
backend/tests/unit/test_bug_tracker.py:157:        log_path = tmp_path / "test_bug_log.jsonl"
backend/tests/unit/test_bug_tracker.py:168:    def test_log_error_appends_jsonl(self, tmp_path: Path):
backend/tests/unit/test_bug_tracker.py:174:        log_path = tmp_path / "test.jsonl"
backend/tests/unit/test_bug_tracker.py:193:    def test_log_error_bug_id_format(self, tmp_path: Path):
backend/tests/unit/test_bug_tracker.py:199:        log_path = tmp_path / "test.jsonl"
backend/tests/unit/test_bug_tracker.py:222:    def test_log_error_captures_stack_trace(self, tmp_path: Path):
backend/tests/unit/test_bug_tracker.py:228:        log_path = tmp_path / "test.jsonl"
backend/tests/unit/test_bug_tracker.py:243:    def test_log_error_captures_request_params(self, tmp_path: Path):
backend/tests/unit/test_bug_tracker.py:249:        log_path = tmp_path / "test.jsonl"
backend/tests/unit/test_bug_tracker.py:269:    def test_log_error_with_user_action(self, tmp_path: Path):
backend/tests/unit/test_bug_tracker.py:271:        log_path = tmp_path / "test.jsonl"
backend/tests/unit/test_bug_tracker.py:286:    def test_get_recent_bugs_empty_file(self, tmp_path: Path):
backend/tests/unit/test_bug_tracker.py:292:        log_path = tmp_path / "nonexistent.jsonl"
backend/tests/unit/test_bug_tracker.py:299:    def test_get_recent_bugs_returns_records(self, tmp_path: Path):
backend/tests/unit/test_bug_tracker.py:305:        log_path = tmp_path / "test.jsonl"
backend/tests/unit/test_bug_tracker.py:317:    def test_get_recent_bugs_limit(self, tmp_path: Path):
backend/tests/unit/test_bug_tracker.py:323:        log_path = tmp_path / "test.jsonl"
backend/tests/unit/test_bug_tracker.py:335:    def test_get_recent_bugs_newest_first(self, tmp_path: Path):
backend/tests/unit/test_bug_tracker.py:341:        log_path = tmp_path / "test.jsonl"
backend/tests/unit/test_bug_tracker.py:356:    def test_get_recent_bugs_default_limit(self, tmp_path: Path):
backend/tests/unit/test_bug_tracker.py:362:        log_path = tmp_path / "test.jsonl"
backend/tests/unit/test_bug_tracker.py:374:    def test_get_recent_bugs_handles_malformed_lines(self, tmp_path: Path):
backend/tests/unit/test_bug_tracker.py:376:        log_path = tmp_path / "test.jsonl"
backend/tests/unit/test_bug_tracker.py:396:    def test_clear_log(self, tmp_path: Path):
backend/tests/unit/test_bug_tracker.py:398:        log_path = tmp_path / "test.jsonl"
backend/tests/unit/test_bug_tracker.py:411:    def test_clear_log_nonexistent_file(self, tmp_path: Path):
backend/tests/unit/test_bug_tracker.py:413:        log_path = tmp_path / "nonexistent.jsonl"
backend/tests/regression/test_fsrs_new_card_none_serialization.py:52:def review_service(tmp_path, monkeypatch):
backend/tests/regression/test_fsrs_new_card_none_serialization.py:56:    仅将卡片状态持久化文件重定向到 tmp_path（测试卫生，真实文件 I/O 仍然发生）。
backend/tests/regression/test_fsrs_new_card_none_serialization.py:61:        rs_module, "_CARD_STATES_FILE", tmp_path / "fsrs_card_states.json"
backend/tests/regression/test_fsrs_new_card_none_serialization.py:68:        canvas_service=CanvasService(canvas_base_path=str(tmp_path)),
backend/tests/regression/test_fsrs_new_card_none_serialization.py:97:    restored = fsrs_manager.deserialize_card(card_json)
backend/tests/regression/test_fsrs_new_card_none_serialization.py:114:    restored = fsrs_manager.deserialize_card(fsrs_manager.serialize_card(card))
backend/tests/regression/test_vault_skip_files_scope_contract.py:130:def test_full_scan_and_single_file_agree(tmp_path):
backend/tests/regression/test_learning_event_log.py:12:def _patch_path(monkeypatch, tmp_path):
backend/tests/regression/test_learning_event_log.py:13:    monkeypatch.setattr(ev, "_log_path", lambda: tmp_path / "learning_events.jsonl")
backend/tests/regression/test_learning_event_log.py:16:def test_append_writes_full_schema(monkeypatch, tmp_path):
backend/tests/regression/test_learning_event_log.py:17:    _patch_path(monkeypatch, tmp_path)
backend/tests/regression/test_learning_event_log.py:25:    rec = json.loads((tmp_path / "learning_events.jsonl").read_text().strip())
backend/tests/regression/test_learning_event_log.py:40:def test_idempotent_by_event_id(monkeypatch, tmp_path):
backend/tests/regression/test_learning_event_log.py:41:    _patch_path(monkeypatch, tmp_path)
backend/tests/regression/test_learning_event_log.py:44:    lines = (tmp_path / "learning_events.jsonl").read_text().strip().splitlines()
backend/tests/regression/test_learning_event_log.py:48:def test_unknown_event_type_rejected(monkeypatch, tmp_path):
backend/tests/regression/test_learning_event_log.py:49:    _patch_path(monkeypatch, tmp_path)
backend/tests/regression/test_learning_event_log.py:51:    assert not (tmp_path / "learning_events.jsonl").exists()
backend/tests/regression/test_learning_event_log.py:54:def test_empty_event_id_rejected(monkeypatch, tmp_path):
backend/tests/regression/test_learning_event_log.py:55:    _patch_path(monkeypatch, tmp_path)
backend/tests/regression/test_learning_event_log.py:59:def test_effective_at_can_backfill(monkeypatch, tmp_path):
backend/tests/regression/test_learning_event_log.py:61:    _patch_path(monkeypatch, tmp_path)
backend/tests/regression/test_learning_event_log.py:67:    rec = json.loads((tmp_path / "learning_events.jsonl").read_text().strip())
backend/tests/regression/test_rag_stage2_t6_verification_contracts.py:218:    client = LanceDBClient(db_path="/tmp/nonexistent-t6-test", enable_fallback=enable_fallback)
backend/tests/unit/test_extraction_validator.py:19:async def validator(tmp_path):
backend/tests/unit/test_extraction_validator.py:20:    db_path = str(tmp_path / "test_extraction.db")
backend/tests/unit/test_extraction_validator.py:33:    async def test_store_basic_record(self, tmp_path):
backend/tests/unit/test_extraction_validator.py:34:        v = ExtractionValidator(str(tmp_path / "test.db"))
backend/tests/unit/test_extraction_validator.py:50:    async def test_store_tip_record(self, tmp_path):
backend/tests/unit/test_extraction_validator.py:51:        v = ExtractionValidator(str(tmp_path / "test.db"))
backend/tests/unit/test_extraction_validator.py:70:    async def test_annotate_correct(self, tmp_path):
backend/tests/unit/test_extraction_validator.py:71:        v = ExtractionValidator(str(tmp_path / "test.db"))
backend/tests/unit/test_extraction_validator.py:88:    async def test_annotate_incorrect(self, tmp_path):
backend/tests/unit/test_extraction_validator.py:89:        v = ExtractionValidator(str(tmp_path / "test.db"))
backend/tests/unit/test_extraction_validator.py:101:    async def test_annotate_partial(self, tmp_path):
backend/tests/unit/test_extraction_validator.py:102:        v = ExtractionValidator(str(tmp_path / "test.db"))
backend/tests/unit/test_extraction_validator.py:114:    async def test_annotate_invalid_value(self, tmp_path):
backend/tests/unit/test_extraction_validator.py:115:        v = ExtractionValidator(str(tmp_path / "test.db"))
backend/tests/unit/test_extraction_validator.py:127:    async def test_annotate_nonexistent_record(self, tmp_path):
backend/tests/unit/test_extraction_validator.py:128:        v = ExtractionValidator(str(tmp_path / "test.db"))
backend/tests/unit/test_extraction_validator.py:141:    async def test_empty_query(self, tmp_path):
backend/tests/unit/test_extraction_validator.py:142:        v = ExtractionValidator(str(tmp_path / "test.db"))
backend/tests/unit/test_extraction_validator.py:149:    async def test_pagination(self, tmp_path):
backend/tests/unit/test_extraction_validator.py:150:        v = ExtractionValidator(str(tmp_path / "test.db"))
backend/tests/unit/test_extraction_validator.py:169:    async def test_type_filter(self, tmp_path):
backend/tests/unit/test_extraction_validator.py:170:        v = ExtractionValidator(str(tmp_path / "test.db"))
backend/tests/unit/test_extraction_validator.py:189:    async def test_stats_empty(self, tmp_path):
backend/tests/unit/test_extraction_validator.py:190:        v = ExtractionValidator(str(tmp_path / "test.db"))
backend/tests/unit/test_extraction_validator.py:197:    async def test_stats_with_annotations(self, tmp_path):
backend/tests/unit/test_extraction_validator.py:198:        v = ExtractionValidator(str(tmp_path / "test.db"))
backend/tests/regression/test_snapshot_v3_contract.py:44:def vault(tmp_path: Path) -> Path:
backend/tests/regression/test_snapshot_v3_contract.py:45:    v = tmp_path / "vault"
backend/tests/regression/test_daily_review_pick.py:23:def _build(tmp_path, nodes: dict, blr: dict | None = None, now: datetime = NOW):
backend/tests/regression/test_daily_review_pick.py:24:    vault = tmp_path / f"vault{next(_seq)}"  # 同一测试可多次调用, 各建独立 vault
backend/tests/regression/test_daily_review_pick.py:38:def test_pathological_last_examined_does_not_kill_run(tmp_path):
backend/tests/regression/test_daily_review_pick.py:41:        tmp_path,
backend/tests/regression/test_daily_review_pick.py:51:def test_wikilink_board_normalization(tmp_path):
backend/tests/regression/test_daily_review_pick.py:52:    payload, ranked = _build(tmp_path, {"甲": _node(board="我的板")})
backend/tests/regression/test_daily_review_pick.py:57:def test_placeholder_node_skipped_empty_notification(tmp_path):
backend/tests/regression/test_daily_review_pick.py:59:        tmp_path,
backend/tests/regression/test_daily_review_pick.py:68:def test_tiebreak_prefers_least_recently_recommended(tmp_path):
backend/tests/regression/test_daily_review_pick.py:70:    _, ranked = _build(tmp_path, nodes, blr={"A板": "2026-07-29"})
backend/tests/regression/test_daily_review_pick.py:72:    _, ranked2 = _build(tmp_path, nodes)
backend/tests/regression/test_daily_review_pick.py:76:def test_negative_mastery_counted_corrupt_not_silent(tmp_path):
backend/tests/regression/test_daily_review_pick.py:79:        tmp_path,
backend/tests/regression/test_daily_review_pick.py:87:def test_bom_frontmatter_tolerated(tmp_path):
backend/tests/regression/test_daily_review_pick.py:89:        tmp_path,
backend/tests/regression/test_daily_review_pick.py:100:def test_future_due_board_gets_rest_notification(tmp_path):
backend/tests/regression/test_daily_review_pick.py:103:        tmp_path,
backend/tests/regression/test_daily_review_pick.py:114:def test_due_filter_beats_pick_within_board(tmp_path):
backend/tests/regression/test_daily_review_pick.py:117:        tmp_path,
backend/tests/regression/test_daily_review_pick.py:127:def test_no_fsrs_field_means_new_card_due_now(tmp_path):
backend/tests/regression/test_daily_review_pick.py:129:    payload, ranked = _build(tmp_path, {"存量": _node()})
backend/tests/regression/test_daily_review_pick.py:133:def test_unassigned_nodes_named_in_md(tmp_path):
backend/tests/regression/test_daily_review_pick.py:136:        tmp_path,
backend/tests/regression/test_daily_review_pick.py:151:def test_projection_v3_due_nodes_and_ineligible_buckets(tmp_path):
backend/tests/regression/test_daily_review_pick.py:164:        tmp_path,
backend/tests/regression/test_daily_review_pick.py:206:def test_projection_v3_purely_additive_keeps_v2_contract(tmp_path):
backend/tests/regression/test_daily_review_pick.py:211:    payload, ranked = _build(tmp_path, {"存量": _node()})
backend/tests/regression/test_daily_review_pick.py:251:def test_nonfinite_pick_goes_corrupt_not_nan_json(tmp_path):
backend/tests/regression/test_daily_review_pick.py:257:        tmp_path,
backend/tests/regression/test_daily_review_pick.py:270:def test_due_boundary_survives_local_timezone_now(tmp_path):
backend/tests/regression/test_daily_review_pick.py:275:        tmp_path,
backend/tests/regression/test_daily_review_pick.py:286:def test_projection_v3_empty_vault_keeps_contract_keys(tmp_path):
backend/tests/regression/test_daily_review_pick.py:288:    payload, ranked = _build(tmp_path, {})
backend/tests/unit/test_agent_service_user_understanding.py:40:        with tempfile.TemporaryDirectory() as tmpdir:
backend/tests/unit/test_agent_service_user_understanding.py:41:            yield tmpdir
backend/tests/regression/test_board_manifest_contracts.py:8:惯例对齐 test_daily_review_pick / test_rag_stage2_*: tmp_path 造 vault, 零网络。
backend/tests/regression/test_board_manifest_contracts.py:59:def vault(tmp_path: Path) -> Path:
backend/tests/regression/test_board_manifest_contracts.py:60:    v = tmp_path / "vault"
backend/tests/regression/test_board_manifest_contracts.py:845:    assert snap.exists() and not snap.with_name(snap.name + ".tmp").exists()
backend/tests/regression/test_real_entrypoint_admission.py:27:def escape_vault(tmp_path, monkeypatch):
backend/tests/regression/test_real_entrypoint_admission.py:30:    vault = tmp_path / "vault"
backend/tests/regression/test_real_entrypoint_admission.py:35:    outside = tmp_path / "outside_secret.md"
backend/tests/regression/test_real_entrypoint_admission.py:56:async def test_real_single_file_entry_rejects_outside_symlink(escape_vault, tmp_path):
backend/tests/regression/test_real_entrypoint_admission.py:60:    db_dir = tmp_path / "db_single"
backend/tests/regression/test_real_entrypoint_admission.py:73:async def test_real_full_scan_entry_rejects_symlink_and_case_variant(escape_vault, tmp_path, monkeypatch):
backend/tests/regression/test_real_entrypoint_admission.py:79:    db_dir = tmp_path / "db_full"
backend/tests/test_notification_channels.py:76:def temp_log_path(tmp_path: Path) -> Path:
backend/tests/test_notification_channels.py:78:    return tmp_path / "alerts.log"
backend/tests/test_notification_channels.py:173:        tmp_path: Path,
backend/tests/test_notification_channels.py:176:        nested_path = tmp_path / "nested" / "dir" / "alerts.log"
backend/tests/test_notification_channels.py:185:    async def test_send_handles_write_error(self, sample_alert: Alert, tmp_path: Path):
backend/tests/test_notification_channels.py:188:        log_path = tmp_path / "alerts.log"
backend/tests/test_notification_channels.py:392:    def test_create_with_custom_log_path(self, tmp_path: Path):
backend/tests/test_notification_channels.py:394:        custom_path = str(tmp_path / "custom_alerts.log")
backend/tests/regression/test_p03_vault_isolation.py:22:def vaults_root(tmp_path, monkeypatch):
backend/tests/regression/test_p03_vault_isolation.py:25:        (tmp_path / name / ".obsidian").mkdir(parents=True)
backend/tests/regression/test_p03_vault_isolation.py:26:    (tmp_path / "not-a-vault").mkdir()
backend/tests/regression/test_p03_vault_isolation.py:30:    monkeypatch.setattr(config_module, "get_settings", lambda: _FakeSettings(str(tmp_path)))
backend/tests/regression/test_p03_vault_isolation.py:31:    return tmp_path
backend/tests/unit/test_vault_switch.py:15:def _obsidian_vault(tmp_path):
backend/tests/unit/test_vault_switch.py:17:    vault = tmp_path / "test-vault"
backend/tests/unit/test_vault_switch.py:24:def _second_vault(tmp_path):
backend/tests/unit/test_vault_switch.py:25:    vault = tmp_path / "second-vault"
backend/tests/unit/test_vault_switch.py:32:def _non_vault(tmp_path):
backend/tests/unit/test_vault_switch.py:34:    d = tmp_path / "not-a-vault"
backend/tests/unit/test_vault_switch.py:145:    def test_yaml_vault_id_takes_precedence(self, tmp_path, monkeypatch):
backend/tests/unit/test_vault_switch.py:148:        vault_dir = tmp_path / "test-vault"
backend/tests/unit/test_vault_switch.py:166:    def test_fallback_to_active_vault_when_yaml_missing(self, tmp_path, monkeypatch):
backend/tests/unit/test_vault_switch.py:168:        vault_dir = tmp_path / "test-vault-no-yaml"
backend/tests/unit/test_vault_switch.py:180:    def test_fallback_when_yaml_lacks_vault_id_field(self, tmp_path, monkeypatch):
backend/tests/unit/test_vault_switch.py:182:        vault_dir = tmp_path / "legacy-vault"
backend/tests/unit/test_vault_switch.py:199:    def test_chinese_vault_id_in_yaml_preserved(self, tmp_path, monkeypatch):
backend/tests/unit/test_vault_switch.py:201:        vault_dir = tmp_path / "chinese-vault"
backend/tests/unit/test_vault_switch.py:218:    def test_invalid_yaml_silently_falls_back(self, tmp_path, monkeypatch):
backend/tests/unit/test_vault_switch.py:220:        vault_dir = tmp_path / "broken-yaml-vault"
backend/tests/unit/test_security_p0_vulnerabilities.py:301:        with tempfile.TemporaryDirectory() as tmpdir:
backend/tests/unit/test_security_p0_vulnerabilities.py:302:            vault = PathlibPath(tmpdir)
backend/tests/unit/test_vault_admission.py:17:def vault(tmp_path) -> Path:
backend/tests/unit/test_vault_admission.py:18:    root = tmp_path / "vault"
backend/tests/unit/test_vault_admission.py:54:def test_symlink_escape(vault, tmp_path):
backend/tests/unit/test_vault_admission.py:55:    outside = tmp_path / "outside.md"
backend/tests/unit/test_vault_admission.py:86:def test_ancestor_dotdir_immunity(tmp_path):
backend/tests/unit/test_vault_admission.py:88:    root = tmp_path / ".claude" / "worktrees" / "wt" / "vault"
backend/tests/unit/test_card_state_concurrent_write.py:31:    The mock supports create_card, deserialize_card, review_card,
backend/tests/unit/test_card_state_concurrent_write.py:45:    mgr.deserialize_card.return_value = mock_card
backend/tests/unit/test_card_state_concurrent_write.py:176:            f"Card state should deserialize to dict, got {type(parsed)}"
backend/tests/unit/test_check_readme_claims.py:223:def test_canonical_positive_per_rule(tmp_path: Path, rule_id: str, sentence: str) -> None:
backend/tests/unit/test_check_readme_claims.py:225:    _write_readme(tmp_path, sentence + "\n")
backend/tests/unit/test_check_readme_claims.py:226:    hits = _hits(tmp_path)
backend/tests/unit/test_check_readme_claims.py:229:    assert _enforce(tmp_path) == 1
backend/tests/unit/test_check_readme_claims.py:230:    assert _report(tmp_path) == 0  # report 是信息档, 永远 0
backend/tests/unit/test_check_readme_claims.py:234:def test_near_miss_negative_zero_hit(tmp_path: Path, sentence: str) -> None:
backend/tests/unit/test_check_readme_claims.py:236:    _write_readme(tmp_path, sentence + "\n")
backend/tests/unit/test_check_readme_claims.py:237:    assert _hits(tmp_path) == []
backend/tests/unit/test_check_readme_claims.py:238:    assert _enforce(tmp_path) == 0
backend/tests/unit/test_check_readme_claims.py:244:def test_escape_conditions(tmp_path: Path) -> None:
backend/tests/unit/test_check_readme_claims.py:246:    _init_repo(tmp_path, "placeholder\n")
backend/tests/unit/test_check_readme_claims.py:247:    evidence = tmp_path / "docs" / "evidence" / "deploy.md"
backend/tests/unit/test_check_readme_claims.py:250:    _git(tmp_path, "add", "docs/evidence/deploy.md")
backend/tests/unit/test_check_readme_claims.py:253:    _write_readme(tmp_path, "The deploy chain is production-ready [C1:E3](docs/evidence/deploy.md).\n")
backend/tests/unit/test_check_readme_claims.py:254:    assert _enforce(tmp_path) == 0
backend/tests/unit/test_check_readme_claims.py:255:    hits = _hits(tmp_path)
backend/tests/unit/test_check_readme_claims.py:279:        _write_readme(tmp_path, bad)
backend/tests/unit/test_check_readme_claims.py:280:        assert _enforce(tmp_path) == 1, f"应拒绝逃逸: {bad!r}"
backend/tests/unit/test_check_readme_claims.py:283:    (tmp_path / "docs" / "evidence" / "untracked.md").write_text("x\n", encoding="utf-8")
backend/tests/unit/test_check_readme_claims.py:284:    _write_readme(tmp_path, "production-ready [C1:E3](docs/evidence/untracked.md).\n")
backend/tests/unit/test_check_readme_claims.py:285:    assert _enforce(tmp_path) == 1
backend/tests/unit/test_check_readme_claims.py:288:    (tmp_path / "docs" / "evidence" / "ita.md").write_text("x\n", encoding="utf-8")
backend/tests/unit/test_check_readme_claims.py:289:    _git(tmp_path, "add", "-N", "docs/evidence/ita.md")
backend/tests/unit/test_check_readme_claims.py:290:    _write_readme(tmp_path, "production-ready [C1:E3](docs/evidence/ita.md).\n")
backend/tests/unit/test_check_readme_claims.py:291:    assert _enforce(tmp_path) == 1
backend/tests/unit/test_check_readme_claims.py:294:    (tmp_path / "docs" / "evidence" / "empty.md").write_text("", encoding="utf-8")
backend/tests/unit/test_check_readme_claims.py:295:    _git(tmp_path, "add", "docs/evidence/empty.md")
backend/tests/unit/test_check_readme_claims.py:296:    _write_readme(tmp_path, "production-ready [C1:E3](docs/evidence/empty.md).\n")
backend/tests/unit/test_check_readme_claims.py:297:    assert _enforce(tmp_path) == 1
backend/tests/unit/test_check_readme_claims.py:300:def test_hard_forbidden_never_escapes(tmp_path: Path) -> None:
backend/tests/unit/test_check_readme_claims.py:302:    _init_repo(tmp_path, "placeholder\n")
backend/tests/unit/test_check_readme_claims.py:303:    (tmp_path / "bench.md").write_text("bench\n", encoding="utf-8")
backend/tests/unit/test_check_readme_claims.py:304:    _git(tmp_path, "add", "bench.md")
backend/tests/unit/test_check_readme_claims.py:305:    _write_readme(tmp_path, "Our retrieval recall@5 reached 0.92 [C6:E4](bench.md).\n")
backend/tests/unit/test_check_readme_claims.py:306:    assert _enforce(tmp_path) == 1
backend/tests/unit/test_check_readme_claims.py:307:    hits = _hits(tmp_path)
backend/tests/unit/test_check_readme_claims.py:313:def test_hard_forbidden_immune_to_legacy_at_engine_level(tmp_path: Path) -> None:
backend/tests/unit/test_check_readme_claims.py:316:    _write_readme(tmp_path, line + "\n")
backend/tests/unit/test_check_readme_claims.py:328:    hits = crc.scan_lines("README.md", [(1, line)], cfg, tmp_path, all_lines=all_lines)
backend/tests/unit/test_check_readme_claims.py:336:def _mutated_rules(tmp_path: Path, mutate) -> Path:
backend/tests/unit/test_check_readme_claims.py:339:    out = tmp_path / "mutated.yaml"
backend/tests/unit/test_check_readme_claims.py:378:def test_any_yaml_mutation_is_error_not_green(tmp_path: Path, mutate) -> None:
backend/tests/unit/test_check_readme_claims.py:380:    mutated = _mutated_rules(tmp_path, mutate)
backend/tests/unit/test_check_readme_claims.py:381:    _write_readme(tmp_path, "The system is production-ready.\n")
backend/tests/unit/test_check_readme_claims.py:382:    assert crc.main(["--enforce", "--root", str(tmp_path), "--rules", str(mutated)]) == 2
backend/tests/unit/test_check_readme_claims.py:393:def test_bad_root_and_missing_rules_exit_2(tmp_path: Path) -> None:
backend/tests/unit/test_check_readme_claims.py:395:    assert crc.main(["--report", "--root", str(tmp_path / "ghost"), "--rules", str(REAL_RULES)]) == 2
backend/tests/unit/test_check_readme_claims.py:396:    _write_readme(tmp_path, "hello\n")
backend/tests/unit/test_check_readme_claims.py:397:    assert crc.main(["--report", "--root", str(tmp_path), "--rules", str(tmp_path / "nope.yaml")]) == 2
backend/tests/unit/test_check_readme_claims.py:399:    empty = tmp_path / "no-readme"
backend/tests/unit/test_check_readme_claims.py:404:def test_files_outside_scan_paths_are_never_scanned(tmp_path: Path) -> None:
backend/tests/unit/test_check_readme_claims.py:406:    _write_readme(tmp_path, "An honest readme.\n")
backend/tests/unit/test_check_readme_claims.py:407:    (tmp_path / "docs").mkdir()
backend/tests/unit/test_check_readme_claims.py:408:    (tmp_path / "docs" / "hype.md").write_text(
backend/tests/unit/test_check_readme_claims.py:411:    assert _enforce(tmp_path) == 0
backend/tests/unit/test_check_readme_claims.py:412:    assert _hits(tmp_path) == []
backend/tests/unit/test_check_readme_claims.py:423:def test_legacy_context_fingerprint_and_quota(tmp_path: Path) -> None:
backend/tests/unit/test_check_readme_claims.py:439:    hits = crc.scan_lines("README.md", numbered, cfg, tmp_path, all_lines=all_lines)
backend/tests/unit/test_check_readme_claims.py:445:    hits2 = crc.scan_lines("README.md", list(enumerate(moved, start=1)), cfg, tmp_path, all_lines=moved)
backend/tests/unit/test_check_readme_claims.py:449:def test_legacy_moved_out_of_anchor_loses_grandfather(tmp_path: Path) -> None:
backend/tests/unit/test_check_readme_claims.py:451:    _write_readme(tmp_path, LEGACY_AGENT_LINES[2] + "\n")
backend/tests/unit/test_check_readme_claims.py:452:    hits = _hits(tmp_path)
backend/tests/unit/test_check_readme_claims.py:454:    assert _enforce(tmp_path) == 1
backend/tests/unit/test_check_readme_claims.py:460:def test_staged_diff_scans_only_added_lines(tmp_path: Path) -> None:
backend/tests/unit/test_check_readme_claims.py:462:    _init_repo(tmp_path, "### 14 Specialized AI Agents\n")
backend/tests/unit/test_check_readme_claims.py:464:    _write_readme(tmp_path, "### 14 Specialized AI Agents\nThis fork is production-ready.\n")
backend/tests/unit/test_check_readme_claims.py:465:    _git(tmp_path, "add", "README.md")
backend/tests/unit/test_check_readme_claims.py:466:    assert crc.main(["--staged-diff", "--root", str(tmp_path), "--rules", str(REAL_RULES)]) == 1
backend/tests/unit/test_check_readme_claims.py:468:    _write_readme(tmp_path, "### 14 Specialized AI Agents\n一行诚实的部署说明。\n")
backend/tests/unit/test_check_readme_claims.py:469:    _git(tmp_path, "add", "README.md")
backend/tests/unit/test_check_readme_claims.py:470:    assert crc.main(["--staged-diff", "--root", str(tmp_path), "--rules", str(REAL_RULES)]) == 0
backend/tests/unit/test_check_readme_claims.py:473:def test_staged_added_lines_never_get_legacy(tmp_path: Path) -> None:
backend/tests/unit/test_check_readme_claims.py:475:    _init_repo(tmp_path, "start\n")
backend/tests/unit/test_check_readme_claims.py:476:    _write_readme(tmp_path, "start\n" + LEGACY_AGENT_LINES[2] + "\n")
backend/tests/unit/test_check_readme_claims.py:477:    _git(tmp_path, "add", "README.md")
backend/tests/unit/test_check_readme_claims.py:478:    assert crc.main(["--staged-diff", "--root", str(tmp_path), "--rules", str(REAL_RULES)]) == 1
backend/tests/unit/test_check_readme_claims.py:481:def test_staged_diff_hostile_content_and_git_config(tmp_path: Path) -> None:
backend/tests/unit/test_check_readme_claims.py:483:    _init_repo(tmp_path, "start\n")
backend/tests/unit/test_check_readme_claims.py:484:    _git(tmp_path, "config", "diff.noprefix", "true")
backend/tests/unit/test_check_readme_claims.py:485:    _git(tmp_path, "config", "diff.mnemonicPrefix", "true")
backend/tests/unit/test_check_readme_claims.py:486:    _git(tmp_path, "config", "color.ui", "always")
backend/tests/unit/test_check_readme_claims.py:487:    _write_readme(tmp_path, "start\n++ totally production-ready\n")
backend/tests/unit/test_check_readme_claims.py:488:    _git(tmp_path, "add", "README.md")
backend/tests/unit/test_check_readme_claims.py:489:    assert crc.main(["--staged-diff", "--root", str(tmp_path), "--rules", str(REAL_RULES)]) == 1
backend/tests/unit/test_check_readme_claims.py:492:    (tmp_path / ".gitattributes").write_text("README.md -diff\n", encoding="utf-8")
backend/tests/unit/test_check_readme_claims.py:493:    _git(tmp_path, "add", ".gitattributes")
backend/tests/unit/test_check_readme_claims.py:494:    assert crc.main(["--staged-diff", "--root", str(tmp_path), "--rules", str(REAL_RULES)]) == 1
backend/tests/unit/test_check_readme_claims.py:497:def test_staged_diff_unicode_line_separator_not_evaded(tmp_path: Path) -> None:
backend/tests/unit/test_check_readme_claims.py:499:    _init_repo(tmp_path, "start\n")
backend/tests/unit/test_check_readme_claims.py:500:    _write_readme(tmp_path, "start\nprefix\u2028our recall@5 reached 0.9\n")
backend/tests/unit/test_check_readme_claims.py:501:    _git(tmp_path, "add", "README.md")
backend/tests/unit/test_check_readme_claims.py:502:    assert crc.main(["--staged-diff", "--root", str(tmp_path), "--rules", str(REAL_RULES)]) == 1
backend/tests/unit/test_check_readme_claims.py:505:def test_staged_deletion_of_scan_target_refused(tmp_path: Path) -> None:
backend/tests/unit/test_check_readme_claims.py:507:    _init_repo(tmp_path, "start\n")
backend/tests/unit/test_check_readme_claims.py:508:    _git(tmp_path, "rm", "--cached", "-q", "README.md")
backend/tests/unit/test_check_readme_claims.py:509:    assert crc.main(["--staged-diff", "--root", str(tmp_path), "--rules", str(REAL_RULES)]) == 2
backend/tests/unit/test_check_readme_claims.py:512:def test_staged_diff_root_must_be_toplevel(tmp_path: Path) -> None:
backend/tests/unit/test_check_readme_claims.py:514:    _init_repo(tmp_path, "start\n")
backend/tests/unit/test_check_readme_claims.py:515:    sub = tmp_path / "sub"
backend/tests/unit/test_check_readme_claims.py:537:def test_g1_4_banner_is_zero_hit(tmp_path: Path) -> None:
backend/tests/unit/test_check_readme_claims.py:539:    _write_readme(tmp_path, G1_4_BANNER_TEXT)
backend/tests/unit/test_check_readme_claims.py:540:    assert _hits(tmp_path) == []
backend/tests/unit/test_check_readme_claims.py:541:    assert _enforce(tmp_path) == 0
backend/tests/unit/test_difficulty_matcher.py:103:    def _make_matcher(self, tmp_path: str) -> DifficultyMatcher:
backend/tests/unit/test_difficulty_matcher.py:104:        db_path = os.path.join(tmp_path, "test_matcher.db")
backend/tests/unit/test_difficulty_matcher.py:107:    def test_empty_window_stats(self, tmp_path):
backend/tests/unit/test_difficulty_matcher.py:108:        matcher = self._make_matcher(str(tmp_path))
backend/tests/unit/test_difficulty_matcher.py:115:    def test_window_tracks_matches(self, tmp_path):
backend/tests/unit/test_difficulty_matcher.py:116:        matcher = self._make_matcher(str(tmp_path))
backend/tests/unit/test_difficulty_matcher.py:129:    def test_below_threshold_not_healthy(self, tmp_path):
backend/tests/unit/test_difficulty_matcher.py:130:        matcher = self._make_matcher(str(tmp_path))
backend/tests/unit/test_difficulty_matcher.py:140:    def test_window_size_capped(self, tmp_path):
backend/tests/unit/test_difficulty_matcher.py:141:        matcher = self._make_matcher(str(tmp_path))
backend/tests/unit/test_difficulty_matcher.py:160:    async def test_evaluate_persists_and_updates_window(self, tmp_path):
backend/tests/unit/test_difficulty_matcher.py:161:        db_path = str(tmp_path / "test_eval.db")
backend/tests/unit/test_difficulty_matcher.py:187:    async def test_evaluate_unmatched(self, tmp_path):
backend/tests/unit/test_difficulty_matcher.py:188:        db_path = str(tmp_path / "test_eval2.db")
backend/tests/unit/test_difficulty_matcher.py:207:    async def test_hydration_from_db(self, tmp_path):
backend/tests/unit/test_difficulty_matcher.py:209:        db_path = str(tmp_path / "test_hydrate.db")
backend/tests/unit/test_qa_38_6_scoring_reliability_extra.py:48:    async def test_timeout_triggers_record_failed_write(self, tmp_path):
backend/tests/unit/test_qa_38_6_scoring_reliability_extra.py:50:        fallback_file = tmp_path / "data" / "failed_writes.jsonl"
backend/tests/unit/test_qa_38_6_scoring_reliability_extra.py:79:    async def test_exception_triggers_record_failed_write(self, tmp_path):
backend/tests/unit/test_qa_38_6_scoring_reliability_extra.py:81:        fallback_file = tmp_path / "data" / "failed_writes.jsonl"
backend/tests/unit/test_qa_38_6_scoring_reliability_extra.py:105:    def test_concurrent_writes_all_recorded(self, tmp_path):
backend/tests/unit/test_qa_38_6_scoring_reliability_extra.py:107:        fallback_file = tmp_path / "data" / "failed_writes.jsonl"
backend/tests/unit/test_qa_38_6_scoring_reliability_extra.py:128:    def test_record_creates_parent_directory(self, tmp_path):
backend/tests/unit/test_qa_38_6_scoring_reliability_extra.py:130:        deep_path = tmp_path / "a" / "b" / "c" / "failed_writes.jsonl"
backend/tests/unit/test_qa_38_6_scoring_reliability_extra.py:160:    async def test_recover_empty_file(self, memory_service, tmp_path):
backend/tests/unit/test_qa_38_6_scoring_reliability_extra.py:162:        fallback_file = tmp_path / "failed_writes.jsonl"
backend/tests/unit/test_qa_38_6_scoring_reliability_extra.py:174:    async def test_recover_whitespace_only_file(self, memory_service, tmp_path):
backend/tests/unit/test_qa_38_6_scoring_reliability_extra.py:176:        fallback_file = tmp_path / "failed_writes.jsonl"
backend/tests/unit/test_qa_38_6_scoring_reliability_extra.py:188:    async def test_recover_all_malformed(self, memory_service, tmp_path):
backend/tests/unit/test_qa_38_6_scoring_reliability_extra.py:190:        fallback_file = tmp_path / "failed_writes.jsonl"
backend/tests/unit/test_qa_38_6_scoring_reliability_extra.py:223:    def test_load_failed_scores_skips_malformed(self, tmp_path):
backend/tests/unit/test_qa_38_6_scoring_reliability_extra.py:225:        fallback_file = tmp_path / "failed_writes.jsonl"
backend/tests/unit/test_qa_38_6_scoring_reliability_extra.py:252:    async def test_merged_view_sort_newest_first(self, memory_service, tmp_path):
backend/tests/unit/test_qa_38_6_scoring_reliability_extra.py:254:        fallback_file = tmp_path / "failed_writes.jsonl"
backend/tests/unit/test_qa_38_6_scoring_reliability_extra.py:300:    def test_load_failed_scores_empty_file(self, tmp_path):
backend/tests/unit/test_qa_38_6_scoring_reliability_extra.py:302:        fallback_file = tmp_path / "failed_writes.jsonl"
backend/tests/unit/test_qa_38_6_scoring_reliability_extra.py:324:    async def test_full_cycle_fail_record_recover_merge(self, tmp_path):
backend/tests/unit/test_qa_38_6_scoring_reliability_extra.py:331:        fallback_file = tmp_path / "data" / "failed_writes.jsonl"
backend/tests/unit/test_qa_38_6_scoring_reliability_extra.py:369:    async def test_full_cycle_recovery_fails_then_merge(self, tmp_path):
backend/tests/unit/test_qa_38_6_scoring_reliability_extra.py:376:        fallback_file = tmp_path / "data" / "failed_writes.jsonl"
backend/tests/unit/test_candidate_service.py:38:    tmp_path,
backend/tests/unit/test_candidate_service.py:46:    f = tmp_path / "node.md"
backend/tests/unit/test_candidate_service.py:91:async def test_accept_candidate_default_status_accepted(tmp_path):
backend/tests/unit/test_candidate_service.py:93:    f = _md_with_pending_candidate(tmp_path)
backend/tests/unit/test_candidate_service.py:127:async def test_accept_candidate_with_edits_status_edited(tmp_path):
backend/tests/unit/test_candidate_service.py:129:    f = _md_with_pending_candidate(tmp_path)
backend/tests/unit/test_candidate_service.py:154:async def test_accept_candidate_not_found_returns_404(tmp_path):
backend/tests/unit/test_candidate_service.py:156:    f = _md_with_pending_candidate(tmp_path, candidate_id="real-id")
backend/tests/unit/test_candidate_service.py:168:async def test_accept_candidate_already_accepted_returns_422(tmp_path):
backend/tests/unit/test_candidate_service.py:170:    f = _md_with_pending_candidate(tmp_path)
backend/tests/unit/test_candidate_service.py:183:async def test_accept_candidate_dedupe_into_existing_error(tmp_path):
backend/tests/unit/test_candidate_service.py:185:    f = tmp_path / "node.md"
backend/tests/unit/test_candidate_service.py:254:async def test_accept_candidate_file_not_found_returns_404(tmp_path):
backend/tests/unit/test_candidate_service.py:256:    missing = tmp_path / "missing.md"
backend/tests/unit/test_candidate_service.py:264:    tmp_path,
backend/tests/unit/test_candidate_service.py:267:    f = _md_with_pending_candidate(tmp_path)
backend/tests/unit/test_candidate_service.py:289:async def test_dismiss_candidate_sets_status_dismissed(tmp_path):
backend/tests/unit/test_candidate_service.py:291:    f = _md_with_pending_candidate(tmp_path)
backend/tests/unit/test_candidate_service.py:309:async def test_dismiss_candidate_not_found_returns_404(tmp_path):
backend/tests/unit/test_candidate_service.py:310:    f = _md_with_pending_candidate(tmp_path)
backend/tests/unit/test_candidate_service.py:317:async def test_dismiss_candidate_already_terminal_returns_422(tmp_path):
backend/tests/unit/test_candidate_service.py:319:    f = _md_with_pending_candidate(tmp_path)
backend/tests/unit/test_candidate_service.py:333:async def test_dispute_candidate_writes_reason(tmp_path):
backend/tests/unit/test_candidate_service.py:335:    f = _md_with_pending_candidate(tmp_path)
backend/tests/unit/test_candidate_service.py:356:async def test_dispute_candidate_empty_reason_returns_422(tmp_path):
backend/tests/unit/test_candidate_service.py:358:    f = _md_with_pending_candidate(tmp_path)
backend/tests/unit/test_candidate_service.py:367:async def test_dispute_candidate_whitespace_reason_returns_422(tmp_path):
backend/tests/unit/test_candidate_service.py:369:    f = _md_with_pending_candidate(tmp_path)
backend/tests/unit/test_candidate_service.py:378:async def test_dispute_candidate_not_found_returns_404(tmp_path):
backend/tests/unit/test_candidate_service.py:379:    f = _md_with_pending_candidate(tmp_path)
backend/tests/unit/test_story_38_1_review_fixes.py:40:                await svc._do_index("test", "/tmp")
backend/tests/unit/test_story_38_1_review_fixes.py:49:        with tempfile.TemporaryDirectory() as tmpdir:
backend/tests/unit/test_story_38_1_review_fixes.py:58:            canvas_file = Path(tmpdir) / "my_canvas.canvas"
backend/tests/unit/test_story_38_1_review_fixes.py:83:                    result = await svc._do_index("my_canvas", tmpdir)
backend/tests/unit/test_story_38_1_review_fixes.py:104:        with tempfile.TemporaryDirectory() as tmpdir:
backend/tests/unit/test_story_38_1_review_fixes.py:122:                        await svc._do_index("nonexistent_canvas", tmpdir)
backend/tests/unit/test_story_38_1_review_fixes.py:153:            await svc._debounced_index("canvas_a", "/tmp")
backend/tests/unit/test_story_38_1_review_fixes.py:182:                await svc._do_index("test", "/tmp")
backend/tests/unit/test_story_38_1_review_fixes.py:200:        with tempfile.TemporaryDirectory() as tmpdir:
backend/tests/unit/test_story_38_1_review_fixes.py:216:            canvas_path = Path(tmpdir) / "test.canvas"
backend/tests/unit/test_story_38_1_review_fixes.py:219:            svc = CanvasService(canvas_base_path=tmpdir)
backend/tests/unit/test_story_38_1_review_fixes.py:229:                    "test", tmpdir, trigger_node_id=node_id
backend/tests/unit/test_story_38_1_ac3_startup_recovery.py:35:            tempfile.TemporaryDirectory() as tmpdir,
backend/tests/unit/test_story_38_1_ac3_startup_recovery.py:43:            svc._pending_file = Path(tmpdir) / "nonexistent.jsonl"
backend/tests/unit/test_story_38_1_ac3_startup_recovery.py:45:            result = await svc.recover_pending("/tmp/canvas")
backend/tests/unit/test_story_38_1_ac3_startup_recovery.py:58:            tempfile.TemporaryDirectory() as tmpdir,
backend/tests/unit/test_story_38_1_ac3_startup_recovery.py:66:            svc._pending_file = Path(tmpdir) / "pending.jsonl"
backend/tests/unit/test_story_38_1_ac3_startup_recovery.py:89:            result = await svc.recover_pending("/tmp/canvas")
backend/tests/unit/test_story_38_1_ac3_startup_recovery.py:108:            tempfile.TemporaryDirectory() as tmpdir,
backend/tests/unit/test_story_38_1_ac3_startup_recovery.py:116:            svc._pending_file = Path(tmpdir) / "pending.jsonl"
backend/tests/unit/test_story_38_1_ac3_startup_recovery.py:147:            result = await svc.recover_pending("/tmp/canvas")
backend/tests/unit/test_story_38_1_ac3_startup_recovery.py:167:            tempfile.TemporaryDirectory() as tmpdir,
backend/tests/unit/test_story_38_1_ac3_startup_recovery.py:175:            svc._pending_file = Path(tmpdir) / "pending.jsonl"
backend/tests/unit/test_story_38_1_ac3_startup_recovery.py:197:            result = await svc.recover_pending("/tmp/canvas")
backend/tests/unit/test_story_38_1_ac3_startup_recovery.py:212:            tempfile.TemporaryDirectory() as tmpdir,
backend/tests/unit/test_story_38_1_ac3_startup_recovery.py:220:            svc._pending_file = Path(tmpdir) / "pending.jsonl"
backend/tests/unit/test_story_38_1_ac3_startup_recovery.py:237:                await svc.recover_pending("/tmp/canvas")
backend/tests/unit/test_story_38_1_ac3_startup_recovery.py:311:            svc.schedule_index("canvas_a", "/tmp")
backend/tests/unit/test_story_38_1_ac3_startup_recovery.py:312:            svc.schedule_index("canvas_b", "/tmp")
backend/tests/unit/test_canvas_service_concurrency.py:35:    with tempfile.TemporaryDirectory() as tmpdir:
backend/tests/unit/test_canvas_service_concurrency.py:36:        yield Path(tmpdir)
backend/tests/unit/test_story_38_3_fsrs_init_guarantee.py:57:    mock.deserialize_card.return_value = fake_card
backend/tests/unit/test_story_38_3_fsrs_init_guarantee.py:117:        # Make deserialize_card raise to test error path after auto-creation
backend/tests/unit/test_story_38_3_fsrs_init_guarantee.py:207:        # Reset mock to verify deserialize is called on second query (not create)
backend/tests/unit/test_story_38_3_fsrs_init_guarantee.py:231:        # deserialize should be called with existing data
backend/tests/unit/test_story_38_3_fsrs_init_guarantee.py:232:        mock_fsrs_manager.deserialize_card.assert_called_with('{"existing": true}')
backend/tests/skills/test_split_preview.py:18:fixtures 全部在 tmp_path 程序化构造 (NFD 文件名进 git 会被平台归一化搅浑,
backend/tests/skills/test_split_preview.py:107:    tmp_path: Path, board: str, concepts: list[str], seed_files: dict[str, str], extra_nodes: list[str] = ()
backend/tests/skills/test_split_preview.py:109:    vault = tmp_path / "vault"
backend/tests/skills/test_split_preview.py:193:    def _vault(self, tmp_path, extra_nodes):
backend/tests/skills/test_split_preview.py:195:            tmp_path,
backend/tests/skills/test_split_preview.py:202:    def test_conflict_resolves_with_suffix(self, tmp_path):
backend/tests/skills/test_split_preview.py:203:        vault = self._vault(tmp_path, extra_nodes=["代理-(Agent)-的定义"])
backend/tests/skills/test_split_preview.py:204:        out = tmp_path / "out"
backend/tests/skills/test_split_preview.py:212:    def test_nine_plus_conflicts_marked_unresolvable(self, tmp_path):
backend/tests/skills/test_split_preview.py:214:        vault = self._vault(tmp_path, extra_nodes=[base] + [f"{base}_{i}" for i in range(2, 10)])
backend/tests/skills/test_split_preview.py:215:        out = tmp_path / "out"
backend/tests/skills/test_split_preview.py:226:    def test_callout_marks_overlap(self, tmp_path):
backend/tests/skills/test_split_preview.py:228:            tmp_path,
backend/tests/skills/test_split_preview.py:233:        out = tmp_path / "out"
backend/tests/skills/test_split_preview.py:249:    def test_nfd_pool_file_still_conflicts_with_nfc_candidate(self, tmp_path):
backend/tests/skills/test_split_preview.py:260:            tmp_path,
backend/tests/skills/test_split_preview.py:266:        out = tmp_path / "out"
backend/tests/skills/test_split_preview.py:277:    def test_pure_scaffold_board_yields_zero_and_honest_note(self, tmp_path):
backend/tests/skills/test_split_preview.py:278:        vault = make_vault(tmp_path, "空板", concepts=[], seed_files={})
backend/tests/skills/test_split_preview.py:279:        out = tmp_path / "out"
backend/tests/skills/test_split_preview.py:288:    def test_link_line_hr_and_multiline_comment_not_content(self, tmp_path):
backend/tests/skills/test_split_preview.py:299:        vault = make_vault(tmp_path, "板B", concepts=[], seed_files={})
backend/tests/skills/test_split_preview.py:301:        out = tmp_path / "out"
backend/tests/skills/test_split_preview.py:307:    def test_seed_without_subsections_falls_back_to_whole_doc(self, tmp_path):
backend/tests/skills/test_split_preview.py:318:            tmp_path,
backend/tests/skills/test_split_preview.py:323:        out = tmp_path / "out"
backend/tests/skills/test_split_preview.py:331:    def test_fence_and_recent_activity_headings_not_candidates(self, tmp_path):
backend/tests/skills/test_split_preview.py:333:            tmp_path,
backend/tests/skills/test_split_preview.py:338:        out = tmp_path / "out"
backend/tests/skills/test_split_preview.py:349:    def test_two_runs_byte_identical(self, tmp_path):
backend/tests/skills/test_split_preview.py:351:            tmp_path,
backend/tests/skills/test_split_preview.py:356:        out1, out2 = tmp_path / "out1", tmp_path / "out2"
backend/tests/skills/test_split_preview.py:369:    def test_over_threshold_truncates_in_document_order(self, tmp_path):
backend/tests/skills/test_split_preview.py:377:            tmp_path,
backend/tests/skills/test_split_preview.py:382:        out = tmp_path / "out"
backend/tests/skills/test_split_preview.py:405:    def test_vault_untouched_when_outdir_external(self, tmp_path):
backend/tests/skills/test_split_preview.py:407:            tmp_path,
backend/tests/skills/test_split_preview.py:425:        out = tmp_path / "external-out"
backend/tests/skills/test_split_preview.py:431:    def test_board_name_containment_rejects_specifically(self, tmp_path):
backend/tests/skills/test_split_preview.py:434:        vault = make_vault(tmp_path, "板A", concepts=[], seed_files={})
backend/tests/skills/test_split_preview.py:435:        out = tmp_path / "out"
backend/tests/skills/test_split_preview.py:445:    def test_evil_seed_member_skipped_not_read(self, tmp_path):
backend/tests/skills/test_split_preview.py:448:        secret = tmp_path / "outside-secret.md"
backend/tests/skills/test_split_preview.py:454:            tmp_path,
backend/tests/skills/test_split_preview.py:459:        out = tmp_path / "out"
backend/tests/skills/test_split_preview.py:470:    def test_symlink_seed_skipped(self, tmp_path):
backend/tests/skills/test_split_preview.py:471:        outside = tmp_path / "outside-note.md"
backend/tests/skills/test_split_preview.py:476:        vault = make_vault(tmp_path, "板A", concepts=["[[节点/链接种子]] — 种子 · 掌握度 — · 未考"], seed_files={})
backend/tests/skills/test_split_preview.py:478:        out = tmp_path / "out"
backend/tests/skills/test_split_preview.py:485:    def test_outdir_ancestor_symlink_rejected_with_zero_write(self, tmp_path):
backend/tests/skills/test_split_preview.py:488:        vault = make_vault(tmp_path, "板A", concepts=[], seed_files={})
backend/tests/skills/test_split_preview.py:489:        real = tmp_path / "real-dir"
backend/tests/skills/test_split_preview.py:491:        link = tmp_path / "link-dir"
backend/tests/skills/test_split_preview.py:498:    def test_vault_content_dir_symlink_rejected(self, tmp_path):
backend/tests/skills/test_split_preview.py:501:        outside = tmp_path / "outside-nodes"
backend/tests/skills/test_split_preview.py:507:        vault = make_vault(tmp_path, "板A", concepts=["[[节点/外部种子]] — 种子 · 掌握度 — · 未考"], seed_files={})
backend/tests/skills/test_split_preview.py:510:        real_nodes = tmp_path / "moved-nodes"
backend/tests/skills/test_split_preview.py:513:        r = run_cli(vault, "板A", tmp_path / "out")
backend/tests/skills/test_split_preview.py:516:    def test_hardlinked_target_rejected(self, tmp_path):
backend/tests/skills/test_split_preview.py:520:        vault = make_vault(tmp_path, "板A", concepts=[], seed_files={})
backend/tests/skills/test_split_preview.py:521:        out = tmp_path / "out"
backend/tests/skills/test_split_preview.py:525:        _os.link(target, tmp_path / "elsewhere.json")
backend/tests/skills/test_split_preview.py:529:    def test_symlink_target_file_rejected(self, tmp_path):
backend/tests/skills/test_split_preview.py:530:        vault = make_vault(tmp_path, "板A", concepts=[], seed_files={})
backend/tests/skills/test_split_preview.py:531:        out = tmp_path / "out"
backend/tests/skills/test_split_preview.py:533:        victim = tmp_path / "victim.json"
backend/tests/skills/test_split_preview.py:552:    def _run(self, tmp_path, board_body_extra: str):
backend/tests/skills/test_split_preview.py:553:        vault = make_vault(tmp_path, "板X", concepts=[], seed_files={})
backend/tests/skills/test_split_preview.py:556:        out = tmp_path / "out"
backend/tests/skills/test_split_preview.py:560:    def test_rich_section_inside_auto_pair_not_candidate(self, tmp_path):
backend/tests/skills/test_split_preview.py:562:        data = self._run(tmp_path, extra)
backend/tests/skills/test_split_preview.py:565:    def test_rich_section_inside_fence_not_candidate(self, tmp_path):
backend/tests/skills/test_split_preview.py:567:        data = self._run(tmp_path, extra)
backend/tests/skills/test_split_preview.py:570:    def test_rich_section_under_recent_activity_not_candidate(self, tmp_path):
backend/tests/skills/test_split_preview.py:572:        data = self._run(tmp_path, extra)
backend/tests/skills/test_split_preview.py:575:    def test_rich_section_inside_html_comment_not_candidate_and_no_truncation(self, tmp_path):
backend/tests/skills/test_split_preview.py:584:        data = self._run(tmp_path, extra)
backend/tests/skills/test_split_preview.py:591:    def test_derived_callout_inside_fence_not_overlap_evidence(self, tmp_path):
backend/tests/skills/test_split_preview.py:598:        data = self._run(tmp_path, extra)
backend/tests/skills/test_split_preview.py:627:    def test_nine_plus_conflict_gets_no_executable_diff(self, tmp_path):
backend/tests/skills/test_split_preview.py:632:            tmp_path,
backend/tests/skills/test_split_preview.py:638:        out = tmp_path / "out"
backend/tests/skills/test_split_preview.py:696:    def test_md_contains_display_only_diff_with_disclaimer(self, tmp_path):
backend/tests/skills/test_split_preview.py:698:            tmp_path,
backend/tests/skills/test_split_preview.py:703:        out = tmp_path / "out"
backend/tests/unit/test_story_38_3_edge_cases.py:53:    mock.deserialize_card.return_value = FakeCard()
backend/tests/unit/test_story_38_3_edge_cases.py:132:    async def test_deserialize_failure_after_persistence_load(
backend/tests/unit/test_story_38_3_edge_cases.py:135:        """When deserialize_card fails on persisted data, error reason returned."""
backend/tests/unit/test_story_38_3_edge_cases.py:137:        mock_fsrs_manager.deserialize_card.side_effect = ValueError("invalid JSON")
backend/tests/unit/test_error_writer.py:5:- Task 4.5: 原子写入 (临时文件 + os.replace)
backend/tests/unit/test_error_writer.py:52:def test_frontmatter_appends_to_existing_errors_list(tmp_path):
backend/tests/unit/test_error_writer.py:54:    f = tmp_path / "node.md"
backend/tests/unit/test_error_writer.py:83:def test_frontmatter_creates_errors_list_when_missing(tmp_path):
backend/tests/unit/test_error_writer.py:85:    f = tmp_path / "node.md"
backend/tests/unit/test_error_writer.py:104:def test_frontmatter_preserves_body_unchanged(tmp_path):
backend/tests/unit/test_error_writer.py:106:    f = tmp_path / "node.md"
backend/tests/unit/test_error_writer.py:115:def test_frontmatter_file_not_found_returns_false(tmp_path):
backend/tests/unit/test_error_writer.py:117:    f = tmp_path / "missing.md"
backend/tests/unit/test_error_writer.py:123:def test_frontmatter_atomic_no_temp_left_on_success(tmp_path):
backend/tests/unit/test_error_writer.py:125:    f = tmp_path / "node.md"
backend/tests/unit/test_error_writer.py:130:    leftover = list(tmp_path.glob(".node.md.tmp*"))
backend/tests/unit/test_error_writer.py:134:def test_frontmatter_double_label_fields_present(tmp_path):
backend/tests/unit/test_error_writer.py:136:    f = tmp_path / "node.md"
backend/tests/unit/test_error_writer.py:245:async def test_dual_write_frontmatter_success_graphiti_scheduled(tmp_path):
backend/tests/unit/test_error_writer.py:247:    f = tmp_path / "node.md"
backend/tests/unit/test_error_writer.py:268:async def test_dual_write_skips_graphiti_when_frontmatter_fails(tmp_path):
backend/tests/unit/test_error_writer.py:270:    missing = tmp_path / "missing.md"
backend/tests/unit/test_error_writer.py:290:async def test_dual_write_sync_mode_returns_graphiti_status(tmp_path):
backend/tests/unit/test_error_writer.py:292:    f = tmp_path / "node.md"
backend/tests/unit/test_error_writer.py:320:async def test_concurrent_writes_no_data_loss(tmp_path):
backend/tests/unit/test_error_writer.py:329:    f = tmp_path / "concurrent.md"
backend/tests/unit/test_error_writer.py:369:def test_frontmatter_dedupe_same_error_updates_seen_count(tmp_path):
backend/tests/unit/test_error_writer.py:371:    f = tmp_path / "dedupe.md"
backend/tests/unit/test_error_writer.py:392:def test_frontmatter_legacy_remedy_field_present(tmp_path):
backend/tests/unit/test_error_writer.py:394:    f = tmp_path / "node.md"
backend/tests/unit/test_error_writer.py:410:async def test_dual_write_sync_mode_graphiti_failed(tmp_path):
backend/tests/unit/test_error_writer.py:412:    f = tmp_path / "node.md"
backend/tests/unit/test_subject_resolver.py:31:def sample_config_yaml(tmp_path):
backend/tests/unit/test_subject_resolver.py:50:    config_path = tmp_path / "subject_mapping.yaml"
backend/tests/unit/test_subject_resolver.py:63:def empty_resolver(tmp_path):
backend/tests/unit/test_subject_resolver.py:65:    config_path = tmp_path / "empty_config.yaml"
backend/tests/unit/test_subject_resolver.py:274:    def test_load_nonexistent_config_returns_defaults(self, tmp_path):
backend/tests/unit/test_subject_resolver.py:277:            config_path=str(tmp_path / "nonexistent.yaml"),
backend/tests/unit/test_subject_resolver.py:284:    def test_load_empty_config_returns_defaults(self, tmp_path):
backend/tests/unit/test_subject_resolver.py:286:        config_path = tmp_path / "empty.yaml"
backend/tests/unit/test_agents_multimodal.py:70:    async def test_load_existing_png_image(self, tmp_path: Path):
backend/tests/unit/test_agents_multimodal.py:76:        test_image = tmp_path / "test.png"
backend/tests/unit/test_agents_multimodal.py:95:    async def test_load_existing_jpg_image(self, tmp_path: Path):
backend/tests/unit/test_agents_multimodal.py:439:        test_image = tmp_path / "test.jpg"
backend/tests/unit/test_agents_multimodal.py:486:    async def test_skip_unsupported_format(self, tmp_path: Path):
backend/tests/unit/test_agents_multimodal.py:489:        test_file = tmp_path / "test.bmp"
backend/tests/unit/test_agents_multimodal.py:505:    async def test_skip_large_image(self, tmp_path: Path):
backend/tests/unit/test_agents_multimodal.py:508:        large_file = tmp_path / "large.png"
backend/tests/unit/test_agents_multimodal.py:524:    async def test_limit_max_images(self, tmp_path: Path):
backend/tests/unit/test_agents_multimodal.py:533:            test_image = tmp_path / f"test{i}.png"
backend/tests/unit/test_agents_multimodal.py:549:    async def test_return_base64_data(self, tmp_path: Path):
backend/tests/unit/test_agents_multimodal.py:554:        test_image = tmp_path / "test.png"
backend/tests/unit/test_agents_multimodal.py:573:    async def test_mixed_valid_and_invalid_refs(self, tmp_path: Path):
backend/tests/unit/test_agents_multimodal.py:578:        valid_image = tmp_path / "valid.png"
backend/tests/unit/test_agents_multimodal.py:615:    async def test_permission_error_skipped(self, tmp_path: Path):
backend/tests/unit/test_agents_multimodal.py:621:            test_file = tmp_path / "test.png"
backend/tests/unit/test_agents_multimodal.py:637:    async def test_os_error_skipped(self, tmp_path: Path):
backend/tests/unit/test_agents_multimodal.py:642:            test_file = tmp_path / "test.png"
backend/tests/unit/test_agents_multimodal.py:661:    async def test_webp_mime_type_detection(self, tmp_path: Path):
backend/tests/unit/test_agents_multimodal.py:665:        test_image = tmp_path / "test.webp"
backend/tests/unit/test_agents_multimodal.py:682:    async def test_gif_mime_type_detection(self, tmp_path: Path):
backend/tests/unit/test_agents_multimodal.py:686:        test_image = tmp_path / "test.gif"
backend/tests/unit/test_canvas_projection_sync.py:66:async def test_sync_writes_edge_with_reason_as_label(tmp_path, monkeypatch):
backend/tests/unit/test_canvas_projection_sync.py:72:        tmp_path,
backend/tests/unit/test_canvas_projection_sync.py:83:    result = await svc.sync(str(tmp_path), execute=True)
backend/tests/unit/test_canvas_projection_sync.py:102:async def test_sync_falls_back_to_type_when_no_description(tmp_path, monkeypatch):
backend/tests/unit/test_canvas_projection_sync.py:107:        tmp_path,
backend/tests/unit/test_canvas_projection_sync.py:111:    await svc.sync(str(tmp_path), execute=True)
backend/tests/unit/test_canvas_projection_sync.py:116:async def test_sync_skips_md_without_relationships(tmp_path, monkeypatch):
backend/tests/unit/test_canvas_projection_sync.py:120:    _write_node_md(tmp_path, "plain", "---\ntype: concept\n---\n\n无 relationships。\n")
backend/tests/unit/test_canvas_projection_sync.py:121:    _write_node_md(tmp_path, "noyaml", "# 纯 markdown 无 frontmatter\n")
backend/tests/unit/test_canvas_projection_sync.py:122:    result = await svc.sync(str(tmp_path), execute=True)
backend/tests/unit/test_canvas_projection_sync.py:127:async def test_sync_skips_self_loop_and_empty_target(tmp_path, monkeypatch):
backend/tests/unit/test_canvas_projection_sync.py:132:        tmp_path,
backend/tests/unit/test_canvas_projection_sync.py:144:    result = await svc.sync(str(tmp_path), execute=True)
backend/tests/unit/test_canvas_projection_sync.py:149:async def test_sync_multiple_relationships_one_node(tmp_path, monkeypatch):
backend/tests/unit/test_canvas_projection_sync.py:154:        tmp_path,
backend/tests/unit/test_canvas_projection_sync.py:162:    result = await svc.sync(str(tmp_path), execute=True)
backend/tests/unit/test_canvas_projection_sync.py:177:async def test_merge_edge_deterministic_id(tmp_path, monkeypatch):
backend/tests/api/v1/endpoints/test_metadata_subject_mapping.py:27:def test_config_path(tmp_path):
backend/tests/api/v1/endpoints/test_metadata_subject_mapping.py:41:    config_path = tmp_path / "test_subject_mapping.yaml"
backend/tests/unit/test_degraded_flag_propagation.py:36:def temp_canvas_dir(tmp_path: Path) -> Path:
backend/tests/unit/test_degraded_flag_propagation.py:73:    canvas_file = tmp_path / "test.canvas"
backend/tests/unit/test_degraded_flag_propagation.py:77:    return tmp_path
backend/tests/unit/test_wave5_stageb_continued_vault_id_injection.py:214:        req = BuildRequest(vault_path="/tmp/x", vault_id="数学")
backend/tests/unit/test_epic36_gap_coverage.py:48:    mock_canvas_service.canvas_base_path = "/tmp/test"
backend/tests/unit/test_vault_switch_coordinator.py:28:        result = await coordinator.switch("/tmp/v", "v", noop)
backend/tests/unit/test_vault_switch_coordinator.py:38:        await coordinator.switch("/tmp/a", "a", noop)
backend/tests/unit/test_vault_switch_coordinator.py:39:        result = await coordinator.switch("/tmp/b", "b", noop)
backend/tests/unit/test_vault_switch_coordinator.py:49:            await coordinator.switch("/tmp/x", "x", fail)
backend/tests/unit/test_vault_switch_coordinator.py:74:        task = asyncio.create_task(coordinator.switch("/tmp/a", "a", slow_switch))
backend/tests/unit/test_vault_switch_coordinator.py:78:            await coordinator.switch("/tmp/b", "b", slow_switch)
backend/tests/unit/test_audit_guardian.py:17:def guardian(tmp_path, monkeypatch):
backend/tests/unit/test_audit_guardian.py:18:    """Create a fresh AuditGuardian with log directed to tmp_path."""
backend/tests/unit/test_audit_guardian.py:19:    log_file = tmp_path / "audit.jsonl"
backend/tests/unit/test_audit_guardian.py:21:    monkeypatch.setattr("app.audit.guardian.AUDIT_LOG_DIR", tmp_path)
backend/tests/unit/test_audit_guardian.py:27:def read_log(tmp_path):
backend/tests/unit/test_audit_guardian.py:32:        log_file = tmp_path / "audit.jsonl"
backend/tests/unit/test_context_enrichment_get_node_content.py:61:    def test_file_node_reads_file_content(self, tmp_path):
backend/tests/unit/test_context_enrichment_get_node_content.py:64:        test_file = tmp_path / "notes" / "oral-explanation.md"
backend/tests/unit/test_context_enrichment_get_node_content.py:77:        result = get_node_content(node, str(tmp_path))
backend/tests/unit/test_context_enrichment_get_node_content.py:81:    def test_file_node_chinese_content(self, tmp_path):
backend/tests/unit/test_context_enrichment_get_node_content.py:83:        test_file = tmp_path / "笔记" / "测试文件.md"
backend/tests/unit/test_context_enrichment_get_node_content.py:94:        result = get_node_content(node, str(tmp_path))
backend/tests/unit/test_context_enrichment_get_node_content.py:98:    def test_file_node_not_found(self, tmp_path):
backend/tests/unit/test_context_enrichment_get_node_content.py:107:        result = get_node_content(node, str(tmp_path))
backend/tests/unit/test_context_enrichment_get_node_content.py:122:    def test_file_node_permission_error(self, tmp_path):
backend/tests/unit/test_context_enrichment_get_node_content.py:136:            result = get_node_content(node, str(tmp_path))
backend/tests/unit/test_context_enrichment_get_node_content.py:235:    def test_file_node_with_windows_path(self, tmp_path):
backend/tests/unit/test_context_enrichment_get_node_content.py:238:        test_file = tmp_path / "folder" / "file.md"
backend/tests/unit/test_context_enrichment_get_node_content.py:249:        result = get_node_content(node, str(tmp_path))
backend/tests/unit/test_vault_init_service.py:13:def vault_dir(tmp_path: Path) -> Path:
backend/tests/unit/test_vault_init_service.py:14:    return tmp_path / "test-vault"
backend/tests/unit/test_mock_degradation_transparency.py:572:        self, verification_service, tmp_path
backend/tests/unit/test_mock_degradation_transparency.py:575:        # Pin base to a fresh subdirectory inside tmp_path to ensure we have
backend/tests/unit/test_mock_degradation_transparency.py:577:        base = tmp_path / "vault"
backend/tests/unit/test_mock_degradation_transparency.py:582:        outside = str(tmp_path / "evil.canvas")
backend/tests/unit/test_mock_degradation_transparency.py:586:    def test_resolve_rejects_non_canvas_suffix(self, verification_service, tmp_path):
backend/tests/unit/test_mock_degradation_transparency.py:589:        verification_service._canvas_base_path = str(tmp_path)
backend/tests/unit/test_mock_degradation_transparency.py:590:        evil = str(tmp_path / "evil.sh")
backend/tests/unit/test_mock_degradation_transparency.py:595:        self, verification_service, tmp_path
backend/tests/unit/test_mock_degradation_transparency.py:598:        verification_service._canvas_base_path = str(tmp_path)
backend/tests/unit/test_mock_degradation_transparency.py:600:        sub = tmp_path / "Math"
backend/tests/unit/test_mock_degradation_transparency.py:608:        assert str(tmp_path) in result
backend/tests/unit/test_mock_degradation_transparency.py:610:    def test_resolve_strips_double_canvas_suffix(self, verification_service, tmp_path):
backend/tests/unit/test_mock_degradation_transparency.py:612:        verification_service._canvas_base_path = str(tmp_path)
backend/tests/unit/test_mock_degradation_transparency.py:613:        (tmp_path / "test.canvas").write_text("{}")
backend/tests/unit/test_canvas_memory_trigger.py:36:def temp_canvas_dir(tmp_path):
backend/tests/unit/test_canvas_memory_trigger.py:44:    canvas_file = tmp_path / "test-canvas.canvas"
backend/tests/unit/test_canvas_memory_trigger.py:46:    return tmp_path
backend/tests/unit/test_qa_38_5_fallback_extra.py:25:    async def test_multiple_events_append_to_fallback(self, tmp_path):
backend/tests/unit/test_qa_38_5_fallback_extra.py:30:        fallback_file = tmp_path / "canvas_events_fallback.json"
backend/tests/unit/test_qa_38_5_fallback_extra.py:31:        service = CanvasService(canvas_base_path=str(tmp_path), memory_client=None)
backend/tests/unit/test_qa_38_5_fallback_extra.py:53:    async def test_corrupted_json_file_is_overwritten(self, tmp_path):
backend/tests/unit/test_qa_38_5_fallback_extra.py:58:        fallback_file = tmp_path / "canvas_events_fallback.json"
backend/tests/unit/test_qa_38_5_fallback_extra.py:61:        service = CanvasService(canvas_base_path=str(tmp_path), memory_client=None)
backend/tests/unit/test_qa_38_5_fallback_extra.py:82:    async def test_fallback_count_matches_event_count(self, tmp_path):
backend/tests/unit/test_qa_38_5_fallback_extra.py:87:        fallback_file = tmp_path / "canvas_events_fallback.json"
backend/tests/unit/test_qa_38_5_fallback_extra.py:88:        service = CanvasService(canvas_base_path=str(tmp_path), memory_client=None)
backend/tests/unit/test_qa_38_5_fallback_extra.py:89:        # [Review M1] Set fallback path to tmp_path and reset count for clean test
backend/tests/unit/test_qa_38_5_fallback_extra.py:114:    async def test_is_fallback_active_false_then_true(self, tmp_path):
backend/tests/unit/test_qa_38_5_fallback_extra.py:119:        fallback_file = tmp_path / "canvas_events_fallback.json"
backend/tests/unit/test_qa_38_5_fallback_extra.py:120:        service = CanvasService(canvas_base_path=str(tmp_path), memory_client=None)
backend/tests/unit/test_qa_38_5_fallback_extra.py:121:        # [Review M1] Set fallback path to tmp_path and reset count for clean test
backend/tests/unit/test_qa_38_5_fallback_extra.py:142:    def test_try_fallback_write_noop_when_disabled(self, tmp_path):
backend/tests/unit/test_qa_38_5_fallback_extra.py:147:        fallback_file = tmp_path / "canvas_events_fallback.json"
backend/tests/unit/test_qa_38_5_fallback_extra.py:148:        service = CanvasService(canvas_base_path=str(tmp_path), memory_client=None)
backend/tests/unit/test_qa_38_5_fallback_extra.py:149:        # [Review M1] Set fallback path to tmp_path and reset count for clean test
backend/tests/unit/test_qa_38_5_fallback_extra.py:168:    async def test_event_contains_timestamp_and_session_id(self, tmp_path):
backend/tests/unit/test_qa_38_5_fallback_extra.py:173:        fallback_file = tmp_path / "canvas_events_fallback.json"
backend/tests/unit/test_qa_38_5_fallback_extra.py:174:        service = CanvasService(canvas_base_path=str(tmp_path), memory_client=None)
backend/tests/unit/test_qa_38_5_fallback_extra.py:198:    async def test_edge_sync_fallback_includes_from_to_node_ids(self, tmp_path):
backend/tests/unit/test_qa_38_5_fallback_extra.py:202:        fallback_file = tmp_path / "canvas_events_fallback.json"
backend/tests/unit/test_qa_38_5_fallback_extra.py:207:            canvas_base_path=str(tmp_path), memory_client=mock_memory
backend/tests/unit/test_review_service_error_handling.py:79:                            "tmp_file",
backend/tests/unit/test_mastery_engine_fsrs.py:46:    mgr.deserialize_card.return_value = reviewed_card
backend/tests/unit/test_mastery_engine_fsrs.py:80:    def test_subsequent_review_deserializes(self, engine_with_fsrs, stub_fsrs):
backend/tests/unit/test_mastery_engine_fsrs.py:88:        stub_fsrs.deserialize_card.assert_called_once()
backend/tests/unit/test_fsrs_manager.py:268:    def test_deserialize_card_returns_card(self, fsrs_manager, reviewed_card):
backend/tests/unit/test_fsrs_manager.py:269:        """Test deserialize_card returns Card object."""
backend/tests/unit/test_fsrs_manager.py:274:        restored_card = fsrs_manager.deserialize_card(json_str)
backend/tests/unit/test_fsrs_manager.py:283:    def test_serialize_deserialize_roundtrip(self, fsrs_manager, reviewed_card):
backend/tests/unit/test_fsrs_manager.py:291:        restored_card = fsrs_manager.deserialize_card(json_str)
backend/tests/unit/test_ttlcache_transparency.py:22:            svc = VerificationService(canvas_base_path="/tmp")
backend/tests/unit/test_ttlcache_transparency.py:34:        svc = VerificationService(canvas_base_path="/tmp")
backend/tests/unit/test_ttlcache_transparency.py:49:        svc = VerificationService(canvas_base_path="/tmp")
backend/tests/unit/test_ttlcache_transparency.py:64:        svc = VerificationService(canvas_base_path="/tmp")
backend/tests/unit/test_ttlcache_transparency.py:79:        svc = VerificationService(canvas_base_path="/tmp")
backend/tests/unit/test_ttlcache_transparency.py:94:        svc = VerificationService(canvas_base_path="/tmp")
backend/tests/unit/test_ttlcache_transparency.py:109:        svc = VerificationService(canvas_base_path="/tmp")
backend/tests/unit/test_ttlcache_transparency.py:140:        svc = VerificationService(canvas_base_path="/tmp")
backend/tests/unit/test_ttlcache_transparency.py:169:        svc = VerificationService(canvas_base_path="/tmp")
backend/tests/unit/test_ttlcache_transparency.py:195:        svc = VerificationService(canvas_base_path="/tmp")
backend/tests/unit/test_story_38_1_ac2_failure_handling.py:49:                await svc._do_index_with_retry("test_canvas", "/tmp/canvas")
backend/tests/unit/test_story_38_1_ac2_failure_handling.py:79:                await svc._debounced_index("my_canvas", "/tmp/canvas")
backend/tests/unit/test_story_38_1_ac2_failure_handling.py:101:        with tempfile.TemporaryDirectory() as tmpdir:
backend/tests/unit/test_story_38_1_ac2_failure_handling.py:108:                svc._pending_file = Path(tmpdir) / "pending.jsonl"
backend/tests/unit/test_story_38_1_ac2_failure_handling.py:131:        with tempfile.TemporaryDirectory() as tmpdir:
backend/tests/unit/test_story_38_1_ac2_failure_handling.py:133:            canvas_path = Path(tmpdir) / "test.canvas"
backend/tests/unit/test_story_38_1_ac2_failure_handling.py:140:            svc = CanvasService(canvas_base_path=tmpdir)
backend/tests/unit/test_canvas_edge_sync.py:33:def canvas_service_with_memory(mock_memory_client, tmp_path):
backend/tests/unit/test_canvas_edge_sync.py:36:        canvas_base_path=str(tmp_path), memory_client=mock_memory_client
backend/tests/unit/test_canvas_edge_sync.py:80:    async def test_sync_edge_without_memory_client(self, tmp_path):
backend/tests/unit/test_canvas_edge_sync.py:82:        service = CanvasService(canvas_base_path=str(tmp_path), memory_client=None)
backend/tests/unit/test_canvas_edge_sync.py:94:    async def test_sync_edge_without_neo4j_in_memory_client(self, tmp_path):
backend/tests/unit/test_canvas_edge_sync.py:99:            canvas_base_path=str(tmp_path), memory_client=memory_client
backend/tests/unit/test_canvas_edge_sync.py:142:        tmp_path,
backend/tests/unit/test_canvas_edge_sync.py:148:        canvas_path = tmp_path / "test.canvas"
backend/tests/unit/test_canvas_edge_sync.py:182:        tmp_path,
backend/tests/unit/test_canvas_edge_sync.py:189:        canvas_path = tmp_path / "test.canvas"
backend/tests/unit/test_canvas_edge_sync.py:217:        tmp_path,
backend/tests/unit/test_canvas_edge_sync.py:223:        canvas_path = tmp_path / "test.canvas"
backend/tests/unit/test_frontmatter_signals.py:18:def vault(tmp_path, monkeypatch):
backend/tests/unit/test_frontmatter_signals.py:20:    (tmp_path / "节点").mkdir()
backend/tests/unit/test_frontmatter_signals.py:21:    monkeypatch.setattr(fs.settings, "CANVAS_BASE_PATH", str(tmp_path), raising=False)
backend/tests/unit/test_frontmatter_signals.py:22:    return tmp_path
backend/tests/unit/test_story_38_6_scoring_reliability.py:73:    def test_record_failed_write_creates_file(self, tmp_path):
backend/tests/unit/test_story_38_6_scoring_reliability.py:75:        fallback_file = tmp_path / "data" / "failed_writes.jsonl"
backend/tests/unit/test_story_38_6_scoring_reliability.py:102:    def test_record_failed_write_appends(self, tmp_path):
backend/tests/unit/test_story_38_6_scoring_reliability.py:104:        fallback_file = tmp_path / "data" / "failed_writes.jsonl"
backend/tests/unit/test_story_38_6_scoring_reliability.py:117:    def test_record_failed_write_with_none_score(self, tmp_path):
backend/tests/unit/test_story_38_6_scoring_reliability.py:119:        fallback_file = tmp_path / "data" / "failed_writes.jsonl"
backend/tests/unit/test_story_38_6_scoring_reliability.py:159:    async def test_recover_successful_replay(self, memory_service, tmp_path):
backend/tests/unit/test_story_38_6_scoring_reliability.py:161:        fallback_file = tmp_path / "failed_writes.jsonl"
backend/tests/unit/test_story_38_6_scoring_reliability.py:184:    async def test_recover_partial_failure(self, memory_service, tmp_path):
backend/tests/unit/test_story_38_6_scoring_reliability.py:186:        fallback_file = tmp_path / "failed_writes.jsonl"
backend/tests/unit/test_story_38_6_scoring_reliability.py:232:    async def test_recover_malformed_entries_preserved(self, memory_service, tmp_path):
backend/tests/unit/test_story_38_6_scoring_reliability.py:234:        fallback_file = tmp_path / "failed_writes.jsonl"
backend/tests/unit/test_story_38_6_scoring_reliability.py:285:    def test_load_failed_scores_with_entries(self, memory_service, tmp_path):
backend/tests/unit/test_story_38_6_scoring_reliability.py:287:        fallback_file = tmp_path / "failed_writes.jsonl"
backend/tests/unit/test_story_38_6_scoring_reliability.py:311:        self, memory_service, tmp_path
backend/tests/unit/test_story_38_6_scoring_reliability.py:314:        fallback_file = tmp_path / "failed_writes.jsonl"
backend/tests/unit/test_story_38_6_scoring_reliability.py:348:    async def test_get_learning_history_deduplicates(self, memory_service, tmp_path):
backend/tests/unit/test_story_38_6_scoring_reliability.py:350:        fallback_file = tmp_path / "failed_writes.jsonl"
backend/tests/unit/test_vault_backfill.py:73:def _make_vault(tmp_path):
backend/tests/unit/test_vault_backfill.py:74:    (tmp_path / "节点").mkdir()
backend/tests/unit/test_vault_backfill.py:75:    (tmp_path / "节点" / "recursion.md").write_text(
backend/tests/unit/test_vault_backfill.py:87:    (tmp_path / "节点" / "plain.md").write_text("无批注", encoding="utf-8")
backend/tests/unit/test_vault_backfill.py:88:    return tmp_path
backend/tests/unit/test_vault_backfill.py:91:async def test_dry_run_counts_without_writing(tmp_path, monkeypatch):
backend/tests/unit/test_vault_backfill.py:92:    vault = _make_vault(tmp_path)
backend/tests/unit/test_vault_backfill.py:109:async def test_execute_calls_writers(tmp_path, monkeypatch):
backend/tests/unit/test_vault_backfill.py:110:    vault = _make_vault(tmp_path)
backend/tests/unit/test_a7_honest_failure.py:92:async def test_recover_replays_structured_entry(service, monkeypatch, tmp_path):
backend/tests/unit/test_a7_honest_failure.py:94:    f = tmp_path / "failed.jsonl"
backend/tests/unit/test_a7_honest_failure.py:125:    service, monkeypatch, tmp_path
backend/tests/unit/test_a7_honest_failure.py:128:    f = tmp_path / "failed.jsonl"
backend/tests/unit/test_neo4j_client.py:94:    def temp_storage_path(self, tmp_path):
backend/tests/unit/test_neo4j_client.py:96:        return tmp_path / "test_neo4j_memory.json"
backend/tests/unit/test_neo4j_client.py:244:    async def test_driver_initialization_fallback_on_failure(self, tmp_path):
backend/tests/unit/test_neo4j_client.py:246:        storage_path = tmp_path / "fallback_test.json"
backend/tests/unit/test_neo4j_client.py:306:    async def test_health_check_json_fallback(self, tmp_path):
backend/tests/unit/test_neo4j_client.py:308:        storage_path = tmp_path / "health_test.json"
backend/tests/unit/test_neo4j_client.py:374:    async def test_fallback_after_max_retries(self, tmp_path):
backend/tests/unit/test_neo4j_client.py:376:        storage_path = tmp_path / "retry_fallback.json"
backend/tests/unit/test_neo4j_client.py:419:    async def test_metrics_tracking(self, tmp_path):
backend/tests/unit/test_neo4j_client.py:421:        storage_path = tmp_path / "metrics_test.json"
backend/tests/unit/test_neo4j_client.py:437:    async def test_latency_warning(self, tmp_path, caplog):
backend/tests/unit/test_neo4j_client.py:441:        storage_path = tmp_path / "latency_test.json"
backend/tests/unit/test_neo4j_client.py:520:    async def test_cleanup_json_fallback(self, tmp_path):
backend/tests/unit/test_neo4j_client.py:522:        storage_path = tmp_path / "cleanup_test.json"
backend/tests/unit/test_prompt_registry.py:34:def sample_prompt_dir(tmp_path: Path) -> Path:
backend/tests/unit/test_prompt_registry.py:36:    prompts_dir = tmp_path / "prompts"
backend/tests/unit/test_prompt_registry.py:107:    def test_load_all_nonexistent_dir_raises(self, tmp_path: Path):
backend/tests/unit/test_prompt_registry.py:109:        registry = PromptRegistry(prompts_dir=tmp_path / "nonexistent")
backend/tests/unit/test_prompt_registry.py:113:    def test_load_all_empty_dir(self, tmp_path: Path):
backend/tests/unit/test_prompt_registry.py:115:        empty_dir = tmp_path / "empty_prompts"
backend/tests/unit/test_prompt_registry.py:121:    def test_load_all_skips_non_matching_files(self, tmp_path: Path):
backend/tests/unit/test_prompt_registry.py:123:        prompts_dir = tmp_path / "prompts"
backend/tests/unit/test_prompt_registry.py:132:    def test_load_empty_file_raises(self, tmp_path: Path):
backend/tests/unit/test_prompt_registry.py:134:        prompts_dir = tmp_path / "prompts"
backend/tests/unit/test_prompt_registry.py:141:    def test_load_missing_metadata_raises(self, tmp_path: Path):
backend/tests/unit/test_prompt_registry.py:143:        prompts_dir = tmp_path / "prompts"
backend/tests/unit/test_story_30_24_boundary.py:346:    async def test_batch_neo4j_failure_records_to_failed_writes(self, tmp_path):
backend/tests/unit/test_story_30_24_boundary.py:350:        failed_writes_file = tmp_path / "failed_writes.jsonl"
backend/tests/unit/test_story_30_24_boundary.py:383:    async def test_cleanup_flushes_pending_writes(self, tmp_path):
backend/tests/unit/test_story_30_24_boundary.py:403:        failed_writes_file = tmp_path / "failed_writes.jsonl"
backend/tests/unit/test_story_30_24_boundary.py:423:    async def test_failed_writes_record_completeness(self, tmp_path):
backend/tests/unit/test_story_30_24_boundary.py:442:        failed_writes_file = tmp_path / "failed_writes.jsonl"
backend/tests/unit/test_story_30_24_boundary.py:492:    def test_verify_script_exits_nonzero_when_file_not_found(self, tmp_path):
backend/tests/unit/test_story_30_24_boundary.py:494:        result = self._run_verify({"OBSIDIAN_VAULT": str(tmp_path)})
backend/tests/unit/test_story_30_24_boundary.py:499:    def test_verify_script_exits_nonzero_when_stale(self, tmp_path):
backend/tests/unit/test_story_30_24_boundary.py:502:        plugin_dir = tmp_path / ".obsidian" / "plugins" / "canvas-review-system"
backend/tests/unit/test_story_30_24_boundary.py:509:        result = self._run_verify({"OBSIDIAN_VAULT": str(tmp_path)})
backend/tests/unit/test_story_30_24_boundary.py:513:    def test_verify_script_exits_zero_when_fresh(self, tmp_path):
backend/tests/unit/test_story_30_24_boundary.py:516:        plugin_dir = tmp_path / ".obsidian" / "plugins" / "canvas-review-system"
backend/tests/unit/test_story_30_24_boundary.py:521:        result = self._run_verify({"OBSIDIAN_VAULT": str(tmp_path)})
backend/tests/unit/test_fsrs_state_query.py:191:    def _isolate_card_states_file(self, tmp_path, monkeypatch):
backend/tests/unit/test_fsrs_state_query.py:193:        card-states file to tmp so tests never write backend/data/."""
backend/tests/unit/test_fsrs_state_query.py:197:            rs_module, "_CARD_STATES_FILE", tmp_path / "fsrs_card_states.json"
backend/tests/unit/test_canvas_edge_bulk_sync.py:39:def canvas_service_with_memory(mock_memory_client, tmp_path):
backend/tests/unit/test_canvas_edge_bulk_sync.py:42:        canvas_base_path=str(tmp_path), memory_client=mock_memory_client
backend/tests/unit/test_canvas_edge_bulk_sync.py:99:        tmp_path,
backend/tests/unit/test_canvas_edge_bulk_sync.py:104:        canvas_path = tmp_path / "test.canvas"
backend/tests/unit/test_canvas_edge_bulk_sync.py:126:        tmp_path,
backend/tests/unit/test_canvas_edge_bulk_sync.py:131:        canvas_path = tmp_path / "empty.canvas"
backend/tests/unit/test_canvas_edge_bulk_sync.py:152:        tmp_path,
backend/tests/unit/test_canvas_edge_bulk_sync.py:157:        canvas_path = tmp_path / "partial.canvas"
backend/tests/unit/test_canvas_edge_bulk_sync.py:184:        self, canvas_service_with_memory, mock_memory_client, tmp_path
backend/tests/unit/test_canvas_edge_bulk_sync.py:204:        canvas_path = tmp_path / "concurrent.canvas"
backend/tests/unit/test_canvas_edge_bulk_sync.py:235:        self, tmp_path, sample_canvas_with_edges
backend/tests/unit/test_canvas_edge_bulk_sync.py:238:        service = CanvasService(canvas_base_path=str(tmp_path), memory_client=None)
backend/tests/unit/test_canvas_edge_bulk_sync.py:239:        canvas_path = tmp_path / "no_memory.canvas"
backend/tests/unit/test_canvas_edge_bulk_sync.py:256:        self, canvas_service_with_memory, mock_memory_client, tmp_path
backend/tests/unit/test_canvas_edge_bulk_sync.py:276:        canvas_path = tmp_path / "gather_test.canvas"
backend/tests/unit/test_canvas_edge_bulk_sync.py:312:        tmp_path,
backend/tests/unit/test_canvas_edge_bulk_sync.py:317:        canvas_path = tmp_path / "format_test.canvas"
backend/tests/unit/test_canvas_edge_bulk_sync.py:348:        tmp_path,
backend/tests/unit/test_canvas_edge_bulk_sync.py:353:        canvas_path = tmp_path / "idempotent.canvas"
backend/tests/unit/test_canvas_edge_bulk_sync.py:370:        self, canvas_service_with_memory, mock_memory_client, tmp_path
backend/tests/unit/test_canvas_edge_bulk_sync.py:390:        canvas_path = tmp_path / "performance.canvas"
backend/tests/unit/test_wikilink_context_service.py:389:def test_resolve_vault_md_path_rejects_outside_vault(tmp_path):
backend/tests/unit/test_wikilink_context_service.py:393:    vault = tmp_path / "vault"
backend/tests/unit/test_wikilink_context_service.py:400:    outside = tmp_path / "outside.md"
backend/tests/unit/test_wikilink_context_service.py:407:def test_resolve_vault_md_path_rejects_dotdot_escape(tmp_path):
backend/tests/unit/test_wikilink_context_service.py:411:    vault = tmp_path / "vault"
backend/tests/unit/test_wikilink_context_service.py:413:    target = tmp_path / "secret.md"
backend/tests/unit/test_wikilink_context_service.py:420:def test_resolve_vault_md_path_rejects_non_md(tmp_path):
backend/tests/unit/test_wikilink_context_service.py:424:    vault = tmp_path / "vault"
backend/tests/unit/test_wikilink_context_service.py:432:def test_resolve_vault_md_path_rejects_oversized(tmp_path):
backend/tests/unit/test_wikilink_context_service.py:439:    vault = tmp_path / "vault"
backend/tests/unit/test_review_overview.py:4:真实文件 fixture: tmp_path 里建真 vault 目录 (.obsidian + outputs/今日复习.json
backend/tests/unit/test_review_overview.py:90:def overview_env(tmp_path):
backend/tests/unit/test_review_overview.py:91:    """VAULTS_ROOT 指向 tmp 的真实 Settings。
backend/tests/unit/test_review_overview.py:113:        reload_settings(overrides={"VAULTS_ROOT": str(tmp_path), "ACTIVE_VAULT": "vault-a"})
backend/tests/unit/test_review_overview.py:117:        yield tmp_path, TestClient(app)
backend/tests/unit/test_wikilink_graph_service.py:10:def vault_with_links(tmp_path):
backend/tests/unit/test_wikilink_graph_service.py:12:    (tmp_path / "A.md").write_text(
backend/tests/unit/test_wikilink_graph_service.py:15:    (tmp_path / "B.md").write_text(
backend/tests/unit/test_wikilink_graph_service.py:18:    (tmp_path / "C.md").write_text("# C\nLinks back to [[A]]\n")
backend/tests/unit/test_wikilink_graph_service.py:19:    (tmp_path / "D.md").write_text("# D\nNo outgoing links\n")
backend/tests/unit/test_wikilink_graph_service.py:20:    (tmp_path / "orphan.md").write_text("# Orphan\nNo links at all\n")
backend/tests/unit/test_wikilink_graph_service.py:21:    return tmp_path
backend/tests/unit/test_wikilink_graph_service.py:234:    def vault_a(self, tmp_path):
backend/tests/unit/test_wikilink_graph_service.py:235:        vault = tmp_path / "vault_a"
backend/tests/unit/test_wikilink_graph_service.py:242:    def vault_b(self, tmp_path):
backend/tests/unit/test_wikilink_graph_service.py:243:        vault = tmp_path / "vault_b"
backend/tests/unit/test_wikilink_graph_service.py:504:    def lazy_vault(self, tmp_path):
backend/tests/unit/test_wikilink_graph_service.py:506:        vault = tmp_path / "vault_lazy"
backend/tests/unit/test_wikilink_graph_service.py:636:    def test_returns_none_when_no_match(self, monkeypatch, tmp_path):
backend/tests/unit/test_wikilink_graph_service.py:641:        empty_root = tmp_path / "empty_vaults_root"
backend/tests/unit/test_wikilink_graph_service.py:658:    def test_resolves_via_vaults_root_match(self, monkeypatch, tmp_path):
backend/tests/unit/test_wikilink_graph_service.py:663:        vaults_root = tmp_path / "vaults_root"
backend/tests/unit/test_wikilink_graph_service.py:688:    def test_falls_back_to_active_vault_for_default_key(self, monkeypatch, tmp_path):
backend/tests/unit/test_wikilink_graph_service.py:692:        vault_dir = tmp_path / "active_vault"
backend/tests/unit/test_wikilink_graph_service.py:697:            VAULTS_ROOT = str(tmp_path)
backend/tests/unit/test_error_aggregator.py:107:    async def test_record_and_aggregate(self, tmp_path):
backend/tests/unit/test_error_aggregator.py:108:        db_path = str(tmp_path / "test_errors.db")
backend/tests/unit/test_error_aggregator.py:135:    async def test_empty_aggregation(self, tmp_path):
backend/tests/unit/test_error_aggregator.py:136:        db_path = str(tmp_path / "test_empty.db")
backend/tests/unit/test_error_aggregator.py:147:    async def test_multiple_same_category(self, tmp_path):
backend/tests/unit/test_error_aggregator.py:148:        db_path = str(tmp_path / "test_multi.db")
backend/tests/unit/test_story_38_8_fallback_sync.py:47:def tmp_failed_writes(tmp_path):
backend/tests/unit/test_story_38_8_fallback_sync.py:49:    f = tmp_path / "failed_writes.jsonl"
backend/tests/unit/test_story_38_8_fallback_sync.py:54:def tmp_canvas_events(tmp_path):
backend/tests/unit/test_story_38_8_fallback_sync.py:56:    f = tmp_path / "canvas_events_fallback.json"
backend/tests/unit/test_story_38_8_fallback_sync.py:61:def tmp_learning_memories(tmp_path):
backend/tests/unit/test_story_38_8_fallback_sync.py:63:    f = tmp_path / "learning_memories.json"
backend/tests/unit/test_story_38_8_fallback_sync.py:68:def tmp_checkpoint(tmp_path):
backend/tests/unit/test_story_38_8_fallback_sync.py:70:    return tmp_path / "sync_checkpoint.json"
backend/tests/unit/test_story_38_8_fallback_sync.py:74:    tmp_failed_writes, tmp_canvas_events, tmp_learning_memories, tmp_checkpoint
backend/tests/unit/test_story_38_8_fallback_sync.py:78:        "FAILED_WRITES_FILE": tmp_failed_writes,
backend/tests/unit/test_story_38_8_fallback_sync.py:79:        "CANVAS_EVENTS_FALLBACK_FILE": tmp_canvas_events,
backend/tests/unit/test_story_38_8_fallback_sync.py:80:        "LEARNING_MEMORIES_FILE": tmp_learning_memories,
backend/tests/unit/test_story_38_8_fallback_sync.py:81:        "SYNC_CHECKPOINT_FILE": tmp_checkpoint,
backend/tests/unit/test_story_38_8_fallback_sync.py:86:def write_jsonl(path: Path, entries: list):
backend/tests/unit/test_story_38_8_fallback_sync.py:119:        tmp_failed_writes,
backend/tests/unit/test_story_38_8_fallback_sync.py:120:        tmp_canvas_events,
backend/tests/unit/test_story_38_8_fallback_sync.py:121:        tmp_learning_memories,
backend/tests/unit/test_story_38_8_fallback_sync.py:122:        tmp_path,
backend/tests/unit/test_story_38_8_fallback_sync.py:145:        write_jsonl(tmp_failed_writes, entries)
backend/tests/unit/test_story_38_8_fallback_sync.py:148:            tmp_failed_writes,
backend/tests/unit/test_story_38_8_fallback_sync.py:149:            tmp_canvas_events,
backend/tests/unit/test_story_38_8_fallback_sync.py:150:            tmp_learning_memories,
backend/tests/unit/test_story_38_8_fallback_sync.py:151:            tmp_path / "sync_checkpoint.json",
backend/tests/unit/test_story_38_8_fallback_sync.py:166:        tmp_failed_writes,
backend/tests/unit/test_story_38_8_fallback_sync.py:167:        tmp_canvas_events,
backend/tests/unit/test_story_38_8_fallback_sync.py:168:        tmp_learning_memories,
backend/tests/unit/test_story_38_8_fallback_sync.py:169:        tmp_path,
backend/tests/unit/test_story_38_8_fallback_sync.py:190:        tmp_canvas_events.write_text(
backend/tests/unit/test_story_38_8_fallback_sync.py:195:            tmp_failed_writes,
backend/tests/unit/test_story_38_8_fallback_sync.py:196:            tmp_canvas_events,
backend/tests/unit/test_story_38_8_fallback_sync.py:197:            tmp_learning_memories,
backend/tests/unit/test_story_38_8_fallback_sync.py:198:            tmp_path / "sync_checkpoint.json",
backend/tests/unit/test_story_38_8_fallback_sync.py:211:        tmp_failed_writes,
backend/tests/unit/test_story_38_8_fallback_sync.py:212:        tmp_canvas_events,
backend/tests/unit/test_story_38_8_fallback_sync.py:213:        tmp_learning_memories,
backend/tests/unit/test_story_38_8_fallback_sync.py:214:        tmp_path,
backend/tests/unit/test_story_38_8_fallback_sync.py:229:        tmp_canvas_events.write_text(
backend/tests/unit/test_story_38_8_fallback_sync.py:234:            tmp_failed_writes,
backend/tests/unit/test_story_38_8_fallback_sync.py:235:            tmp_canvas_events,
backend/tests/unit/test_story_38_8_fallback_sync.py:236:            tmp_learning_memories,
backend/tests/unit/test_story_38_8_fallback_sync.py:237:            tmp_path / "sync_checkpoint.json",
backend/tests/unit/test_story_38_8_fallback_sync.py:250:        tmp_failed_writes,
backend/tests/unit/test_story_38_8_fallback_sync.py:251:        tmp_canvas_events,
backend/tests/unit/test_story_38_8_fallback_sync.py:252:        tmp_learning_memories,
backend/tests/unit/test_story_38_8_fallback_sync.py:253:        tmp_path,
backend/tests/unit/test_story_38_8_fallback_sync.py:277:        tmp_learning_memories.write_text(
backend/tests/unit/test_story_38_8_fallback_sync.py:282:            tmp_failed_writes,
backend/tests/unit/test_story_38_8_fallback_sync.py:283:            tmp_canvas_events,
backend/tests/unit/test_story_38_8_fallback_sync.py:284:            tmp_learning_memories,
backend/tests/unit/test_story_38_8_fallback_sync.py:285:            tmp_path / "sync_checkpoint.json",
backend/tests/unit/test_story_38_8_fallback_sync.py:305:        tmp_canvas_events,
backend/tests/unit/test_story_38_8_fallback_sync.py:306:        tmp_failed_writes,
backend/tests/unit/test_story_38_8_fallback_sync.py:307:        tmp_learning_memories,
backend/tests/unit/test_story_38_8_fallback_sync.py:308:        tmp_path,
backend/tests/unit/test_story_38_8_fallback_sync.py:329:        tmp_canvas_events.write_text(
backend/tests/unit/test_story_38_8_fallback_sync.py:343:            tmp_failed_writes,
backend/tests/unit/test_story_38_8_fallback_sync.py:344:            tmp_canvas_events,
backend/tests/unit/test_story_38_8_fallback_sync.py:345:            tmp_learning_memories,
backend/tests/unit/test_story_38_8_fallback_sync.py:346:            tmp_path / "sync_checkpoint.json",
backend/tests/unit/test_story_38_8_fallback_sync.py:368:        tmp_failed_writes,
backend/tests/unit/test_story_38_8_fallback_sync.py:369:        tmp_canvas_events,
backend/tests/unit/test_story_38_8_fallback_sync.py:370:        tmp_learning_memories,
backend/tests/unit/test_story_38_8_fallback_sync.py:371:        tmp_path,
backend/tests/unit/test_story_38_8_fallback_sync.py:384:        write_jsonl(tmp_failed_writes, [entry, entry])
backend/tests/unit/test_story_38_8_fallback_sync.py:387:            tmp_failed_writes,
backend/tests/unit/test_story_38_8_fallback_sync.py:388:            tmp_canvas_events,
backend/tests/unit/test_story_38_8_fallback_sync.py:389:            tmp_learning_memories,
backend/tests/unit/test_story_38_8_fallback_sync.py:390:            tmp_path / "sync_checkpoint.json",
backend/tests/unit/test_story_38_8_fallback_sync.py:433:        tmp_failed_writes,
backend/tests/unit/test_story_38_8_fallback_sync.py:434:        tmp_canvas_events,
backend/tests/unit/test_story_38_8_fallback_sync.py:435:        tmp_learning_memories,
backend/tests/unit/test_story_38_8_fallback_sync.py:436:        tmp_path,
backend/tests/unit/test_story_38_8_fallback_sync.py:452:        write_jsonl(tmp_failed_writes, entries)
backend/tests/unit/test_story_38_8_fallback_sync.py:454:        checkpoint_path = tmp_path / "sync_checkpoint.json"
backend/tests/unit/test_story_38_8_fallback_sync.py:456:            tmp_failed_writes,
backend/tests/unit/test_story_38_8_fallback_sync.py:457:            tmp_canvas_events,
backend/tests/unit/test_story_38_8_fallback_sync.py:458:            tmp_learning_memories,
backend/tests/unit/test_story_38_8_fallback_sync.py:482:        tmp_failed_writes,
backend/tests/unit/test_story_38_8_fallback_sync.py:483:        tmp_canvas_events,
backend/tests/unit/test_story_38_8_fallback_sync.py:484:        tmp_learning_memories,
backend/tests/unit/test_story_38_8_fallback_sync.py:485:        tmp_path,
backend/tests/unit/test_story_38_8_fallback_sync.py:500:        write_jsonl(tmp_failed_writes, entries)
backend/tests/unit/test_story_38_8_fallback_sync.py:503:        checkpoint_path = tmp_path / "sync_checkpoint.json"
backend/tests/unit/test_story_38_8_fallback_sync.py:510:            tmp_failed_writes,
backend/tests/unit/test_story_38_8_fallback_sync.py:511:            tmp_canvas_events,
backend/tests/unit/test_story_38_8_fallback_sync.py:512:            tmp_learning_memories,
backend/tests/unit/test_story_38_8_fallback_sync.py:527:        tmp_failed_writes,
backend/tests/unit/test_story_38_8_fallback_sync.py:528:        tmp_canvas_events,
backend/tests/unit/test_story_38_8_fallback_sync.py:529:        tmp_learning_memories,
backend/tests/unit/test_story_38_8_fallback_sync.py:530:        tmp_path,
backend/tests/unit/test_story_38_8_fallback_sync.py:544:        write_jsonl(tmp_failed_writes, entries)
backend/tests/unit/test_story_38_8_fallback_sync.py:546:        checkpoint_path = tmp_path / "sync_checkpoint.json"
backend/tests/unit/test_story_38_8_fallback_sync.py:548:            tmp_failed_writes,
backend/tests/unit/test_story_38_8_fallback_sync.py:549:            tmp_canvas_events,
backend/tests/unit/test_story_38_8_fallback_sync.py:550:            tmp_learning_memories,
backend/tests/unit/test_story_38_8_fallback_sync.py:680:        tmp_failed_writes,
backend/tests/unit/test_story_38_8_fallback_sync.py:681:        tmp_canvas_events,
backend/tests/unit/test_story_38_8_fallback_sync.py:682:        tmp_learning_memories,
backend/tests/unit/test_story_38_8_fallback_sync.py:683:        tmp_path,
backend/tests/unit/test_story_38_8_fallback_sync.py:697:        write_jsonl(tmp_failed_writes, entries)
backend/tests/unit/test_story_38_8_fallback_sync.py:700:            tmp_failed_writes,
backend/tests/unit/test_story_38_8_fallback_sync.py:701:            tmp_canvas_events,
backend/tests/unit/test_story_38_8_fallback_sync.py:702:            tmp_learning_memories,
backend/tests/unit/test_story_38_8_fallback_sync.py:703:            tmp_path / "sync_checkpoint.json",
backend/tests/unit/test_story_38_8_fallback_sync.py:709:        assert not tmp_failed_writes.exists()
backend/tests/unit/test_story_38_8_fallback_sync.py:711:        synced_files = list(tmp_failed_writes.parent.glob("*.synced.*"))
backend/tests/unit/test_story_38_8_fallback_sync.py:719:        tmp_failed_writes,
backend/tests/unit/test_story_38_8_fallback_sync.py:720:        tmp_canvas_events,
backend/tests/unit/test_story_38_8_fallback_sync.py:721:        tmp_learning_memories,
backend/tests/unit/test_story_38_8_fallback_sync.py:722:        tmp_path,
backend/tests/unit/test_story_38_8_fallback_sync.py:735:        tmp_canvas_events.write_text(
backend/tests/unit/test_story_38_8_fallback_sync.py:740:            tmp_failed_writes,
backend/tests/unit/test_story_38_8_fallback_sync.py:741:            tmp_canvas_events,
backend/tests/unit/test_story_38_8_fallback_sync.py:742:            tmp_learning_memories,
backend/tests/unit/test_story_38_8_fallback_sync.py:743:            tmp_path / "sync_checkpoint.json",
backend/tests/unit/test_story_38_8_fallback_sync.py:748:        assert not tmp_canvas_events.exists()
backend/tests/unit/test_story_38_8_fallback_sync.py:755:        tmp_failed_writes,
backend/tests/unit/test_story_38_8_fallback_sync.py:756:        tmp_canvas_events,
backend/tests/unit/test_story_38_8_fallback_sync.py:757:        tmp_learning_memories,
backend/tests/unit/test_story_38_8_fallback_sync.py:758:        tmp_path,
backend/tests/unit/test_story_38_8_fallback_sync.py:774:        tmp_learning_memories.write_text(
backend/tests/unit/test_story_38_8_fallback_sync.py:779:            tmp_failed_writes,
backend/tests/unit/test_story_38_8_fallback_sync.py:780:            tmp_canvas_events,
backend/tests/unit/test_story_38_8_fallback_sync.py:781:            tmp_learning_memories,
backend/tests/unit/test_story_38_8_fallback_sync.py:782:            tmp_path / "sync_checkpoint.json",
backend/tests/unit/test_story_38_8_fallback_sync.py:788:        assert tmp_learning_memories.exists()
backend/tests/unit/test_story_38_8_fallback_sync.py:790:    def test_old_synced_files_cleaned_up(self, tmp_path):
backend/tests/unit/test_story_38_8_fallback_sync.py:795:            tmp_path / f"failed_writes.synced.{old_date.strftime('%Y-%m-%d-%H%M%S')}"
backend/tests/unit/test_story_38_8_fallback_sync.py:800:        old_legacy = tmp_path / f"failed_writes.synced.{old_date.strftime('%Y-%m-%d')}"
backend/tests/unit/test_story_38_8_fallback_sync.py:805:            tmp_path
backend/tests/unit/test_story_38_8_fallback_sync.py:810:        FallbackSyncService._cleanup_old_synced_files(tmp_path, "failed_writes")
backend/tests/unit/test_story_38_8_fallback_sync.py:821:        tmp_failed_writes,
backend/tests/unit/test_story_38_8_fallback_sync.py:822:        tmp_canvas_events,
backend/tests/unit/test_story_38_8_fallback_sync.py:823:        tmp_learning_memories,
backend/tests/unit/test_story_38_8_fallback_sync.py:824:        tmp_path,
backend/tests/unit/test_story_38_8_fallback_sync.py:848:        write_jsonl(tmp_failed_writes, entries)
backend/tests/unit/test_story_38_8_fallback_sync.py:862:            tmp_failed_writes,
backend/tests/unit/test_story_38_8_fallback_sync.py:863:            tmp_canvas_events,
backend/tests/unit/test_story_38_8_fallback_sync.py:864:            tmp_learning_memories,
backend/tests/unit/test_story_38_8_fallback_sync.py:865:            tmp_path / "sync_checkpoint.json",
backend/tests/unit/test_story_38_8_fallback_sync.py:874:        assert tmp_failed_writes.exists()
backend/tests/unit/test_story_38_8_fallback_sync.py:875:        remaining = tmp_failed_writes.read_text(encoding="utf-8").strip().splitlines()
backend/tests/unit/test_story_38_8_fallback_sync.py:894:        tmp_failed_writes,
backend/tests/unit/test_story_38_8_fallback_sync.py:895:        tmp_canvas_events,
backend/tests/unit/test_story_38_8_fallback_sync.py:896:        tmp_learning_memories,
backend/tests/unit/test_story_38_8_fallback_sync.py:897:        tmp_path,
backend/tests/unit/test_story_38_8_fallback_sync.py:900:        tmp_failed_writes.write_text("", encoding="utf-8")
backend/tests/unit/test_story_38_8_fallback_sync.py:901:        tmp_canvas_events.write_text("[]", encoding="utf-8")
backend/tests/unit/test_story_38_8_fallback_sync.py:902:        tmp_learning_memories.write_text(
backend/tests/unit/test_story_38_8_fallback_sync.py:907:            tmp_failed_writes,
backend/tests/unit/test_story_38_8_fallback_sync.py:908:            tmp_canvas_events,
backend/tests/unit/test_story_38_8_fallback_sync.py:909:            tmp_learning_memories,
backend/tests/unit/test_story_38_8_fallback_sync.py:910:            tmp_path / "sync_checkpoint.json",
backend/tests/unit/test_story_38_8_fallback_sync.py:924:        tmp_path,
backend/tests/unit/test_story_38_8_fallback_sync.py:928:            tmp_path / "nope.jsonl",
backend/tests/unit/test_story_38_8_fallback_sync.py:929:            tmp_path / "nope.json",
backend/tests/unit/test_story_38_8_fallback_sync.py:930:            tmp_path / "nope2.json",
backend/tests/unit/test_story_38_8_fallback_sync.py:931:            tmp_path / "sync_checkpoint.json",
backend/tests/unit/test_story_38_8_fallback_sync.py:945:        tmp_failed_writes,
backend/tests/unit/test_story_38_8_fallback_sync.py:946:        tmp_canvas_events,
backend/tests/unit/test_story_38_8_fallback_sync.py:947:        tmp_learning_memories,
backend/tests/unit/test_story_38_8_fallback_sync.py:948:        tmp_path,
backend/tests/unit/test_story_38_8_fallback_sync.py:952:        tmp_failed_writes.write_text(content, encoding="utf-8")
backend/tests/unit/test_story_38_8_fallback_sync.py:955:            tmp_failed_writes,
backend/tests/unit/test_story_38_8_fallback_sync.py:956:            tmp_canvas_events,
backend/tests/unit/test_story_38_8_fallback_sync.py:957:            tmp_learning_memories,
backend/tests/unit/test_story_38_8_fallback_sync.py:958:            tmp_path / "sync_checkpoint.json",
backend/tests/unit/test_story_38_8_fallback_sync.py:972:        tmp_failed_writes,
backend/tests/unit/test_story_38_8_fallback_sync.py:973:        tmp_canvas_events,
backend/tests/unit/test_story_38_8_fallback_sync.py:974:        tmp_learning_memories,
backend/tests/unit/test_story_38_8_fallback_sync.py:975:        tmp_path,
backend/tests/unit/test_story_38_8_fallback_sync.py:978:        tmp_canvas_events.write_text("NOT JSON", encoding="utf-8")
backend/tests/unit/test_story_38_8_fallback_sync.py:981:            tmp_failed_writes,
backend/tests/unit/test_story_38_8_fallback_sync.py:982:            tmp_canvas_events,
backend/tests/unit/test_story_38_8_fallback_sync.py:983:            tmp_learning_memories,
backend/tests/unit/test_story_38_8_fallback_sync.py:984:            tmp_path / "sync_checkpoint.json",
backend/tests/unit/test_story_38_8_fallback_sync.py:996:        tmp_failed_writes,
backend/tests/unit/test_story_38_8_fallback_sync.py:997:        tmp_canvas_events,
backend/tests/unit/test_story_38_8_fallback_sync.py:998:        tmp_learning_memories,
backend/tests/unit/test_story_38_8_fallback_sync.py:999:        tmp_path,
backend/tests/unit/test_story_38_8_fallback_sync.py:1003:        tmp_canvas_events.write_text("CORRUPT", encoding="utf-8")
backend/tests/unit/test_story_38_8_fallback_sync.py:1017:        tmp_learning_memories.write_text(
backend/tests/unit/test_story_38_8_fallback_sync.py:1022:            tmp_failed_writes,
backend/tests/unit/test_story_38_8_fallback_sync.py:1023:            tmp_canvas_events,
backend/tests/unit/test_story_38_8_fallback_sync.py:1024:            tmp_learning_memories,
backend/tests/unit/test_story_38_8_fallback_sync.py:1025:            tmp_path / "sync_checkpoint.json",
backend/tests/unit/test_story_38_1_ac1_auto_trigger.py:80:            svc.schedule_index("test_canvas", "/tmp/canvas")
backend/tests/unit/test_story_38_1_ac1_auto_trigger.py:105:            svc.schedule_index("test_canvas", "/tmp/canvas")
backend/tests/unit/test_story_38_1_ac1_auto_trigger.py:124:            svc.schedule_index("test_canvas", "/tmp/canvas")
backend/tests/unit/test_story_38_1_ac1_auto_trigger.py:127:            svc.schedule_index("test_canvas", "/tmp/canvas")
backend/tests/unit/test_story_38_1_ac1_auto_trigger.py:154:        with tempfile.TemporaryDirectory() as tmpdir:
backend/tests/unit/test_story_38_1_ac1_auto_trigger.py:156:            canvas_file = Path(tmpdir) / "test.canvas"
backend/tests/unit/test_story_38_1_ac1_auto_trigger.py:160:            svc = CanvasService(canvas_base_path=tmpdir)
backend/tests/unit/test_story_38_1_ac1_auto_trigger.py:177:                    "test", tmpdir, trigger_node_id=result["id"]
backend/tests/unit/test_story_38_1_ac1_auto_trigger.py:189:        with tempfile.TemporaryDirectory() as tmpdir:
backend/tests/unit/test_story_38_1_ac1_auto_trigger.py:206:            canvas_file = Path(tmpdir) / "test.canvas"
backend/tests/unit/test_story_38_1_ac1_auto_trigger.py:209:            svc = CanvasService(canvas_base_path=tmpdir)
backend/tests/unit/test_story_38_1_ac1_auto_trigger.py:222:                    "test", tmpdir, trigger_node_id=node_id
backend/tests/unit/test_story_38_1_ac1_auto_trigger.py:233:        svc = CanvasService(canvas_base_path="/tmp/test")
backend/tests/unit/test_failure_observability.py:99:    def test_write_edge_sync_dead_letter(self, tmp_path):
backend/tests/unit/test_failure_observability.py:101:        dl_path = tmp_path / "failed_edge_syncs.jsonl"
backend/tests/unit/test_failure_observability.py:120:    def test_write_dual_write_dead_letter(self, tmp_path):
backend/tests/unit/test_failure_observability.py:122:        dl_path = tmp_path / "failed_dual_writes.jsonl"
backend/tests/unit/test_failure_observability.py:136:    def test_dead_letter_append_mode(self, tmp_path):
backend/tests/unit/test_failure_observability.py:138:        dl_path = tmp_path / "test.jsonl"
backend/tests/unit/test_failure_observability.py:146:    def test_dead_letter_creates_parent_directory(self, tmp_path):
backend/tests/unit/test_failure_observability.py:148:        dl_path = tmp_path / "sub" / "dir" / "test.jsonl"
backend/tests/unit/test_failure_observability.py:152:    def test_dead_letter_survives_utf8(self, tmp_path):
backend/tests/unit/test_failure_observability.py:154:        dl_path = tmp_path / "test.jsonl"
backend/tests/unit/test_failure_observability.py:180:        service = CanvasService(canvas_base_path="/tmp/test")
backend/tests/unit/test_failure_observability.py:202:    async def test_edge_sync_failure_writes_dead_letter(self, tmp_path):
backend/tests/unit/test_failure_observability.py:206:        service = CanvasService(canvas_base_path="/tmp/test")
backend/tests/unit/test_failure_observability.py:215:        dl_path = tmp_path / "failed_edge_syncs.jsonl"
backend/tests/unit/test_failure_observability.py:234:        service = CanvasService(canvas_base_path="/tmp/test")
backend/tests/unit/test_failure_observability.py:322:    async def test_dual_write_retry_failure_writes_dead_letter(self, tmp_path):
backend/tests/unit/test_failure_observability.py:338:        dl_path = tmp_path / "failed_dual_writes.jsonl"
backend/tests/unit/test_failure_observability.py:480:    def test_write_dead_letter_with_request_id(self, tmp_path):
backend/tests/unit/test_failure_observability.py:482:        dl_path = tmp_path / "test.jsonl"
backend/tests/unit/test_failure_observability.py:493:    def test_write_dead_letter_without_request_id_omits_field(self, tmp_path):
backend/tests/unit/test_failure_observability.py:495:        dl_path = tmp_path / "test.jsonl"
backend/tests/unit/test_failure_observability.py:500:    def test_dead_letter_store_includes_request_id(self, tmp_path):
backend/tests/unit/test_failure_observability.py:504:        store = DeadLetterStore(str(tmp_path / "dl.jsonl"))
backend/tests/unit/test_failure_observability.py:513:        entry = json.loads((tmp_path / "dl.jsonl").read_text(encoding="utf-8").strip())
backend/tests/unit/test_failure_observability.py:516:    def test_dead_letter_store_omits_request_id_when_none(self, tmp_path):
backend/tests/unit/test_failure_observability.py:520:        store = DeadLetterStore(str(tmp_path / "dl.jsonl"))
backend/tests/unit/test_failure_observability.py:528:        entry = json.loads((tmp_path / "dl.jsonl").read_text(encoding="utf-8").strip())
backend/tests/unit/test_startup_health_check.py:56:            "/api/v1/system/setup-wizard", json={"vault_path": "/tmp/test-vault"}
backend/tests/unit/test_startup_health_check.py:62:            "/api/v1/system/setup-wizard", json={"vault_path": "/tmp/test-vault-wizard"}
backend/tests/unit/test_migrate_neo4j_data.py:199:    def test_dry_run_does_not_modify_file(self, tmp_path):
backend/tests/unit/test_migrate_neo4j_data.py:202:        source = tmp_path / "test.json"
backend/tests/unit/test_migrate_neo4j_data.py:211:    def test_dry_run_no_backup_created(self, tmp_path):
backend/tests/unit/test_migrate_neo4j_data.py:214:        source = tmp_path / "test.json"
backend/tests/unit/test_migrate_neo4j_data.py:219:        backup_files = list(tmp_path.glob("*.bak*"))
backend/tests/unit/test_migrate_neo4j_data.py:222:    def test_migration_creates_backup(self, tmp_path):
backend/tests/unit/test_migrate_neo4j_data.py:225:        source = tmp_path / "test.json"
backend/tests/unit/test_migrate_neo4j_data.py:230:        backup_files = list(tmp_path.glob("*.bak*"))
backend/tests/unit/test_migrate_neo4j_data.py:233:    def test_migration_preserves_valid_data(self, tmp_path):
backend/tests/unit/test_migrate_neo4j_data.py:236:        source = tmp_path / "test.json"
backend/tests/unit/test_migrate_neo4j_data.py:244:    def test_migration_writes_utf8(self, tmp_path):
backend/tests/unit/test_migrate_neo4j_data.py:247:        source = tmp_path / "test.json"
backend/tests/unit/test_migrate_neo4j_data.py:259:    def test_source_not_found_exits(self, tmp_path):
backend/tests/unit/test_migrate_neo4j_data.py:261:        fake_path = tmp_path / "nonexistent.json"
backend/tests/unit/test_migrate_neo4j_data.py:268:    def test_invalid_json_exits(self, tmp_path):
backend/tests/unit/test_migrate_neo4j_data.py:270:        source = tmp_path / "bad.json"
backend/tests/unit/test_migrate_neo4j_data.py:278:    def test_migration_returns_fixed_data(self, tmp_path):
backend/tests/unit/test_migrate_neo4j_data.py:281:        source = tmp_path / "test.json"
backend/tests/unit/test_multimodal_path_security.py:22:def tmp_storage(tmp_path):
backend/tests/unit/test_multimodal_path_security.py:25:        (tmp_path / subdir).mkdir()
backend/tests/unit/test_multimodal_path_security.py:26:    return tmp_path
backend/tests/unit/test_multimodal_path_security.py:30:def service(tmp_storage):
backend/tests/unit/test_multimodal_path_security.py:31:    """Create a fresh MultimodalService with tmp storage."""
backend/tests/unit/test_multimodal_path_security.py:33:    svc = MultimodalService(storage_base_path=str(tmp_storage))
backend/tests/unit/test_multimodal_path_security.py:49:    def test_valid_path_within_storage(self, service, tmp_storage):
backend/tests/unit/test_multimodal_path_security.py:51:        file_path = Path(tmp_storage) / "image" / "20260209_abc123.png"
backend/tests/unit/test_multimodal_path_security.py:55:    def test_path_traversal_unix_style(self, service, tmp_storage):
backend/tests/unit/test_multimodal_path_security.py:57:        file_path = Path(tmp_storage) / "image" / "../../etc/passwd"
backend/tests/unit/test_multimodal_path_security.py:61:    def test_path_traversal_windows_style(self, service, tmp_storage):
backend/tests/unit/test_multimodal_path_security.py:63:        file_path = Path(tmp_storage) / "image" / "..\\..\\windows\\system32\\config"
backend/tests/unit/test_multimodal_path_security.py:67:    def test_path_traversal_deep_nested(self, service, tmp_storage):
backend/tests/unit/test_multimodal_path_security.py:69:        file_path = Path(tmp_storage) / "image" / "../../../../../../../tmp/evil"
backend/tests/unit/test_multimodal_path_security.py:73:    def test_path_traversal_mixed(self, service, tmp_storage):
backend/tests/unit/test_multimodal_path_security.py:75:        file_path = Path(tmp_storage) / "image" / "normal/../../../evil.txt"
backend/tests/unit/test_multimodal_path_security.py:79:    def test_path_within_subdirectory(self, service, tmp_storage):
backend/tests/unit/test_multimodal_path_security.py:81:        file_path = Path(tmp_storage) / "pdf" / "20260209_doc.pdf"
backend/tests/unit/test_multimodal_path_security.py:85:    def test_error_code_is_path_traversal(self, service, tmp_storage):
backend/tests/unit/test_multimodal_path_security.py:87:        file_path = Path(tmp_storage) / "image" / "../../etc/passwd"
backend/tests/unit/test_multimodal_path_security.py:111:            "../../../../../../../tmp/evil",
backend/tests/unit/test_multimodal_path_security.py:136:    async def test_upload_file_calls_validate_safe_path(self, service, tmp_storage):
backend/tests/unit/test_multimodal_path_security.py:227:    def test_validate_safe_path_real_blocks_crafted_path(self, service, tmp_storage):
backend/tests/unit/test_multimodal_path_security.py:229:        evil_path = Path(tmp_storage) / "image" / "../../etc/passwd"
backend/tests/unit/test_multimodal_path_security.py:235:        self, service, tmp_storage
backend/tests/unit/test_config_drift.py:10:    def test_parses_simple(self, tmp_path):
backend/tests/unit/test_config_drift.py:13:        f = tmp_path / ".env"
backend/tests/unit/test_config_drift.py:43:    def test_no_drift(self, tmp_path):
backend/tests/unit/test_config_drift.py:46:        root = tmp_path / "root.env"
backend/tests/unit/test_config_drift.py:47:        backend = tmp_path / "backend.env"
backend/tests/unit/test_config_drift.py:55:    def test_drift_detected(self, tmp_path):
backend/tests/unit/test_config_drift.py:58:        root = tmp_path / "root.env"
backend/tests/unit/test_config_drift.py:59:        backend = tmp_path / "backend.env"
backend/tests/unit/test_config_drift.py:67:    def test_missing_in_backend(self, tmp_path):
backend/tests/unit/test_config_drift.py:70:        root = tmp_path / "root.env"
backend/tests/unit/test_config_drift.py:71:        backend = tmp_path / "backend.env"
backend/tests/unit/test_markdown_image_extractor.py:235:    async def test_resolve_vault_relative_path(self, extractor, tmp_path):
backend/tests/unit/test_markdown_image_extractor.py:238:        images_dir = tmp_path / "images"
backend/tests/unit/test_markdown_image_extractor.py:244:        resolved = await extractor.resolve_paths(refs, tmp_path)
backend/tests/unit/test_markdown_image_extractor.py:251:    async def test_resolve_canvas_relative_path(self, extractor, tmp_path):
backend/tests/unit/test_markdown_image_extractor.py:254:        canvas_dir = tmp_path / "notes" / "math"
backend/tests/unit/test_markdown_image_extractor.py:263:            refs, vault_path=tmp_path, canvas_dir=canvas_dir
backend/tests/unit/test_markdown_image_extractor.py:271:    async def test_resolve_nonexistent_path(self, extractor, tmp_path):
backend/tests/unit/test_markdown_image_extractor.py:274:        resolved = await extractor.resolve_paths(refs, tmp_path)
backend/tests/unit/test_markdown_image_extractor.py:281:    async def test_resolve_multiple_paths(self, extractor, tmp_path):
backend/tests/unit/test_markdown_image_extractor.py:284:        img1 = tmp_path / "img1.png"
backend/tests/unit/test_markdown_image_extractor.py:286:        img2 = tmp_path / "img2.png"
backend/tests/unit/test_markdown_image_extractor.py:294:        resolved = await extractor.resolve_paths(refs, tmp_path)
backend/tests/unit/test_error_rebuild_service.py:98:def test_scan_vault_md_files_uses_节点_dir(tmp_path):
backend/tests/unit/test_error_rebuild_service.py:100:    nodes_dir = tmp_path / "节点"
backend/tests/unit/test_error_rebuild_service.py:104:    (tmp_path / "Dashboard.md").write_text("ignored", encoding="utf-8")
backend/tests/unit/test_error_rebuild_service.py:106:    files = _scan_vault_md_files(tmp_path)
backend/tests/unit/test_error_rebuild_service.py:112:def test_scan_vault_md_files_fallback_to_root(tmp_path):
backend/tests/unit/test_error_rebuild_service.py:119:    (tmp_path / "x.md").write_text("x", encoding="utf-8")
backend/tests/unit/test_error_rebuild_service.py:120:    (tmp_path / "y.md").write_text("y", encoding="utf-8")
backend/tests/unit/test_error_rebuild_service.py:122:    files = _scan_vault_md_files(tmp_path)
backend/tests/unit/test_error_rebuild_service.py:132:async def test_rebuild_dry_run_counts_only_no_graphiti_call(tmp_path):
backend/tests/unit/test_error_rebuild_service.py:134:    nodes = tmp_path / "节点"
backend/tests/unit/test_error_rebuild_service.py:146:        stats = await rebuild_graphiti_from_frontmatter(tmp_path, group_id="vault:cs_61b", dry_run=True)
backend/tests/unit/test_error_rebuild_service.py:157:async def test_rebuild_actual_writes_each_error_to_graphiti(tmp_path):
backend/tests/unit/test_error_rebuild_service.py:159:    nodes = tmp_path / "节点"
backend/tests/unit/test_error_rebuild_service.py:170:        stats = await rebuild_graphiti_from_frontmatter(tmp_path, group_id="vault:cs_61b", dry_run=False)
backend/tests/unit/test_error_rebuild_service.py:185:async def test_rebuild_graphiti_failure_records_in_failures_list(tmp_path):
backend/tests/unit/test_error_rebuild_service.py:187:    nodes = tmp_path / "节点"
backend/tests/unit/test_error_rebuild_service.py:199:        stats = await rebuild_graphiti_from_frontmatter(tmp_path, group_id="vault:cs_61b", dry_run=False)
backend/tests/unit/test_error_rebuild_service.py:209:async def test_rebuild_graphiti_exception_recorded_not_raised(tmp_path):
backend/tests/unit/test_error_rebuild_service.py:211:    nodes = tmp_path / "节点"
backend/tests/unit/test_error_rebuild_service.py:219:        stats = await rebuild_graphiti_from_frontmatter(tmp_path, group_id="vault:cs_61b", dry_run=False)
backend/tests/unit/test_error_rebuild_service.py:227:async def test_rebuild_corrupted_frontmatter_skipped(tmp_path):
backend/tests/unit/test_error_rebuild_service.py:229:    nodes = tmp_path / "节点"
backend/tests/unit/test_error_rebuild_service.py:240:        stats = await rebuild_graphiti_from_frontmatter(tmp_path, group_id="vault:cs_61b", dry_run=False)
backend/tests/unit/test_error_rebuild_service.py:250:async def test_rebuild_no_errors_in_frontmatter_just_scanned(tmp_path):
backend/tests/unit/test_error_rebuild_service.py:252:    nodes = tmp_path / "节点"
backend/tests/unit/test_error_rebuild_service.py:260:        stats = await rebuild_graphiti_from_frontmatter(tmp_path, group_id="vault:cs_61b", dry_run=False)
backend/tests/unit/test_error_rebuild_service.py:269:async def test_rebuild_vault_root_not_exist_returns_empty(tmp_path):
backend/tests/unit/test_error_rebuild_service.py:271:    fake_vault = tmp_path / "missing"
backend/tests/unit/test_error_rebuild_service.py:278:async def test_rebuild_node_id_uses_vault_relative_path(tmp_path):
backend/tests/unit/test_error_rebuild_service.py:280:    nodes = tmp_path / "节点"
backend/tests/unit/test_error_rebuild_service.py:288:        await rebuild_graphiti_from_frontmatter(tmp_path, group_id="vault:cs_61b", dry_run=False)
backend/tests/unit/test_error_rebuild_service.py:296:async def test_rebuild_returns_elapsed_ms(tmp_path):
backend/tests/unit/test_error_rebuild_service.py:298:    nodes = tmp_path / "节点"
backend/tests/unit/test_error_rebuild_service.py:306:        stats = await rebuild_graphiti_from_frontmatter(tmp_path, group_id="vault:cs_61b", dry_run=False)
backend/tests/unit/test_kg_health.py:9:    def test_creates_gitignore(self, tmp_path):
backend/tests/unit/test_kg_health.py:13:        svc._ensure_gitignore(tmp_path)
backend/tests/unit/test_kg_health.py:14:        gi = tmp_path / ".gitignore"
backend/tests/unit/test_kg_health.py:21:    def test_does_not_overwrite_existing(self, tmp_path):
backend/tests/unit/test_kg_health.py:22:        gi = tmp_path / ".gitignore"
backend/tests/unit/test_kg_health.py:26:        VaultInitService._ensure_gitignore(tmp_path)
backend/tests/unit/test_kg_health.py:31:    def test_detects_installed(self, tmp_path):
backend/tests/unit/test_kg_health.py:34:        (tmp_path / ".obsidian" / "plugins" / "obsidian-git").mkdir(parents=True)
backend/tests/unit/test_kg_health.py:35:        assert VaultInitService.has_git_plugin(str(tmp_path)) is True
backend/tests/unit/test_kg_health.py:37:    def test_not_installed(self, tmp_path):
backend/tests/unit/test_kg_health.py:40:        assert VaultInitService.has_git_plugin(str(tmp_path)) is False
backend/tests/unit/test_multimodal_fixes.py:28:def tmp_storage(tmp_path):
backend/tests/unit/test_multimodal_fixes.py:30:    return str(tmp_path)
backend/tests/unit/test_multimodal_fixes.py:34:def service(tmp_storage):
backend/tests/unit/test_multimodal_fixes.py:35:    """Create a fresh MultimodalService with tmp storage."""
backend/tests/unit/test_multimodal_fixes.py:37:    svc = MultimodalService(storage_base_path=tmp_storage)
backend/tests/unit/test_multimodal_fixes.py:53:    async def test_upload_creates_index_file(self, service, tmp_storage):
backend/tests/unit/test_multimodal_fixes.py:58:        img_path = Path(tmp_storage) / "image"
backend/tests/unit/test_multimodal_fixes.py:71:        index_path = Path(tmp_storage) / "content_index.json"
backend/tests/unit/test_multimodal_fixes.py:81:    async def test_persistence_survives_restart(self, tmp_storage):
backend/tests/unit/test_multimodal_fixes.py:84:        svc1 = MultimodalService(storage_base_path=tmp_storage)
backend/tests/unit/test_multimodal_fixes.py:98:        svc2 = MultimodalService(storage_base_path=tmp_storage)
backend/tests/unit/test_multimodal_fixes.py:105:    async def test_delete_updates_index(self, service, tmp_storage):
backend/tests/unit/test_multimodal_fixes.py:121:        index_path = Path(tmp_storage) / "content_index.json"
backend/tests/unit/test_multimodal_fixes.py:128:    async def test_update_persists(self, service, tmp_storage):
backend/tests/unit/test_multimodal_fixes.py:149:        index_path = Path(tmp_storage) / "content_index.json"
backend/tests/unit/test_multimodal_fixes.py:153:    def test_no_multimodal_store_logs_warning(self, tmp_storage, caplog):
backend/tests/unit/test_multimodal_fixes.py:158:            svc = MultimodalService(storage_base_path=tmp_storage)
backend/tests/unit/test_multimodal_fixes.py:174:    async def test_thumbnail_generated_for_image(self, service, tmp_storage):
backend/tests/unit/test_multimodal_fixes.py:211:    async def test_thumbnail_not_generated_for_pdf(self, service, tmp_storage):
backend/tests/unit/test_multimodal_fixes.py:227:    async def test_thumbnail_failure_does_not_block_upload(self, service, tmp_storage):
backend/tests/unit/test_multimodal_fixes.py:287:    async def test_text_fallback_sets_search_mode_text(self, service, tmp_storage):
backend/tests/unit/test_multimodal_fixes.py:311:    async def test_text_fallback_logs_warning(self, service, tmp_storage, caplog):
backend/tests/unit/test_multimodal_fixes.py:431:    async def test_service_health_with_store_returns_full(self, tmp_storage):
backend/tests/unit/test_multimodal_fixes.py:442:            storage_base_path=tmp_storage,

**Refining git and ripgrep commands**
exec
/bin/zsh -lc "rg -n '"'^(def |class |if __name__)|deserialize|O_NONBLOCK|O_NOFOLLOW|scan_errors|stat_failures|os'"\\.replace|fsync|census-tmp|_path_is_within|read_mode|bytes_read_from_verified_fd' backend/scripts/census_dead_letter_episodes.py" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
77:def _path_is_within(target: str, root: str) -> bool:
104:def _same_file(a: str, b: str) -> bool:
112:def _split_jsonl_lines(raw: bytes) -> list[tuple[str, str | None]]:
135:def classify(rec: dict) -> str:
148:def inline_state(rec: dict) -> tuple[str, str]:
172:def full_body_verified(rec: dict) -> bool:
193:def session_tokens(name: object) -> list[str]:
205:def resolve_group_attribution(tokens: list[str], transcripts_dir: Path) -> dict:
234:    stat_failures: list[str] = []
250:                    stat_failures.append(f"{candidate}: {e}")
255:                if not _path_is_within(candidate, root_str):
264:        result["scan_errors"] = walk_errors[:5]
265:    if stat_failures:
266:        result["stat_failures"] = stat_failures[:5]
282:        result["scan_errors"] = walk_errors[:5]
285:    if stat_failures:
286:        result["stat_failures"] = stat_failures[:5]
304:def probe_qa_metrics(db_path: Path, error_types: list[str]) -> tuple[dict, tuple[int, int] | None]:
311:    ``deserialize``：全程不经路径、不落任何文件，两个问题一并消失。
318:        fd = os.open(db_path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
335:        result["bytes_read_from_verified_fd"] = len(db_bytes)
342:        conn.deserialize(db_bytes)
344:        result["verdict"] = f"deserialize_failed: {str(e)[:80]}"
352:        result["read_mode"] = "in_memory_deserialize_from_verified_fd"
372:def snapshot_file(path: Path) -> tuple[bytes, dict, tuple[int, int]]:
379:    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
408:def describe_copy(path: Path) -> tuple[dict, tuple[int, int] | None]:
416:def main(argv: list[str] | None = None) -> int:
469:        # round-7 BLOCKER 整改: 用 **inode 身份逐级比较**（_path_is_within），
477:        if _path_is_within(out_parent, args.transcripts_dir) or _path_is_within(args.out, args.transcripts_dir):
605:            elif sess.get("scan_errors"):
607:            elif sess.get("stat_failures"):
668:                    else "scan_errors"
669:                    if sess.get("scan_errors")
670:                    else "stat_failures"
671:                    if sess.get("stat_failures")
756:        (k, v.get("scan_errors") or v.get("stat_failures"))
758:        if v.get("scan_errors") or v.get("stat_failures")
796:        # 写 → fsync → os.replace 原子替换。O_EXCL 保证目标是本进程新建的对象，
801:        tmp_path = out_path.with_name(f".{out_path.name}.census-tmp-{os.getpid()}")
803:            tmp_fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
811:                os.fsync(tmp_fd)
818:        # 原子替换 + 父目录 fsync（round-8 MEDIUM 整改：replace 纳入 try，
821:            os.replace(tmp_path, out_path)
824:                os.fsync(dir_fd)
848:if __name__ == "__main__":

exec
/bin/zsh -lc "git show --no-ext-diff --format=fuller af251e4a -- backend/scripts/census_dead_letter_episodes.py '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' '_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md' '_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
commit af251e4a1a8b2c99e3f171d153642bd02d856f99
Author:     oinani0721 <2272104243@qq.com>
AuthorDate: Fri Aug 28 21:37:06 2026 +0800
Commit:     oinani0721 <2272104243@qq.com>
CommitDate: Fri Aug 28 21:37:06 2026 +0800

    fix(census): G4-9 Codex round-8 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9]
    
    round-8 重申裁定分离: 可验收=92 条冻结 ledger snapshot; 不可验收=生成器一般
    安全性与 UAT 的纯只读声明。3 BLOCKER 全闭:
    1. SQLite URI 未转义: file:path?mode=ro 在路径含 # 时 mode=ro 落入 fragment
       被忽略, SQLite 可能按默认读写模式打开(反驳唯一写出口)。
    2. QA DB 仍按 pathname 打开: 验证 fd 保持打开也无用, A→B→A 可让 connection
       读到 B 而复核看到 A。
       1+2 共同解法: 从已验证 fd 读全量字节 → sqlite3 内存库 deserialize,
       全程不经路径, URI 转义与 ABA 一并消失。实测含 #? 路径正常只读。
    3. 根内末级 symlink: POSIX rename 不解析末级 symlink, --out 若是根内 symlink
       指向根外则 realpath 判根外放行, 但 replace 替换的是根内目录项。
       整改: containment 加父目录语义(dirname 在根内即拒)。实测 exit 2 且 symlink 未被替换。
    HIGH 扫描受阻拒绝不完整: no_token/token_conflict 早退前未记 scan_errors;
       且条件写作 scan_blocked and args.out, 省略 --out 走 stdout 即可绕过。
       整改: 早退分支同记扫描错误 + 去掉 and args.out。实测 stdout 模式亦 exit 2。
    MEDIUM tmp 残留: os.replace 在 try 外, EXDEV/ENOSPC 冒泡留 tmp 且未 fsync
       父目录。整改: replace 纳入 try, 异常一律 unlink tmp; 成功后 fsync 父目录。
    第八次全量重跑 92/4-88-0-0/89-2-1/6-29/shasum 不变/无 tmp 残留。
    
    Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>

diff --git "a/_bmad-output/\345\256\241\346\237\245/G4-9-DLQ-census-2026-08-28.md" "b/_bmad-output/\345\256\241\346\237\245/G4-9-DLQ-census-2026-08-28.md"
index 5b2b00dc..f61605aa 100644
--- "a/_bmad-output/\345\256\241\346\237\245/G4-9-DLQ-census-2026-08-28.md"
+++ "b/_bmad-output/\345\256\241\346\237\245/G4-9-DLQ-census-2026-08-28.md"
@@ -207,3 +207,20 @@ round-7 给出了本卡最重要的一次裁定分离：
 - **LOW（receipt 用 8 位缩写）**：如实登记为已知限制（仓库内唯一可解析），未改为 40-hex 以保持 receipt 可读性——列 follow-up。
 
 round-7 整改后第七次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变、台账 mode 0600、无临时文件残留——七轮整改数字全程未变**。
+
+## §7i Codex round-8 复审整改记录（裁定分离重申 + 3 BLOCKER 全闭）
+
+round-8 重申 round-7 的裁定分离，措辞更明确：
+
+> **可验收：92 条冻结 ledger snapshot。不可验收：当前生成器的一般安全性，以及 UAT 的"纯只读、唯一写出口、整类 TOCTOU 已消失"声明。**
+
+三条新 BLOCKER 全部属实，逐条整改：
+
+- **BLOCKER①（SQLite URI 未转义）**：`file:{db_path}?mode=ro` 在路径含 `#` 时，`mode=ro` 会落进被忽略的 URI fragment，SQLite 可能按**默认读写模式**打开——直接反驳"唯一写出口"。
+- **BLOCKER②（QA DB 仍按 pathname 打开）**：验证 fd 保持打开也没用，SQLite 另按路径解析，A→B→A 可让 connection 读到 B 而复核看到 A。
+- **①②的共同解法**：不再让 SQLite 碰路径——从**已验证的 fd** 读全量字节 → `sqlite3` 内存库 `deserialize()`。URI 转义问题与 ABA **一并消失**，且全程不落任何文件。实测：路径含 `#` 与 `?` 的 DB 正常只读（`read_mode: in_memory_deserialize_from_verified_fd`，16384 bytes）。
+- **BLOCKER③（根内末级 symlink）**：POSIX 规定 `rename`/`replace` **不解析末级 symlink**——`--out` 若是根内 symlink 指向根外，`realpath` 判"根外"而放行，但 replace 实际替换的是**根内那个目录项**。**整改**：containment 改用**父目录语义**（`dirname` 在根内即拒），叠加原有末级判定。实测：根内 symlink 作 `--out` → exit 2，symlink 未被替换。
+- **HIGH（扫描受阻拒绝不完整）**：no_token/token_conflict 分支在写入 `scan_errors` **之前**就早退；且拒绝条件写作 `scan_blocked and args.out`，**省略 `--out` 走 stdout 即可绕过**。**整改**：早退分支同样记录扫描错误；拒绝条件去掉 `and args.out`。实测：stdout 模式扫描受阻同样 exit 2。
+- **MEDIUM（tmp 残留 + 未 fsync 父目录）**：`os.replace` 在 `try` 外，`EXDEV/EBUSY/EACCES/ENOSPC` 会冒泡并留下 tmp。**整改**：replace 纳入 try，异常一律 `unlink` tmp；成功后 `fsync` 父目录使重命名落盘。
+
+round-8 整改后第八次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变、无 tmp 残留——八轮整改数字全程未变**。
diff --git "a/_bmad-output/\345\256\241\346\237\245/G4-9-dlq-ledger-2026-08-28.json" "b/_bmad-output/\345\256\241\346\237\245/G4-9-dlq-ledger-2026-08-28.json"
index 9937a25c..43eb4b7a 100644
--- "a/_bmad-output/\345\256\241\346\237\245/G4-9-dlq-ledger-2026-08-28.json"
+++ "b/_bmad-output/\345\256\241\346\237\245/G4-9-dlq-ledger-2026-08-28.json"
@@ -1,6 +1,6 @@
 {
  "card": "CARD-G4-9",
- "generated_at": "2026-08-28T13:12:17.818410+00:00",
+ "generated_at": "2026-08-28T13:35:50.981742+00:00",
  "privacy": "private-only: transcript_paths 含本机用户名与 session UUID，禁止外发/公网发布",
  "stable_key_semantics": "冻结快照（dlq_file.sha256）内的 occurrence key；line_no 在快照内唯一，sha256_prefix/request_id 为冗余对账维度——非跨文件重排或语义幂等键",
  "dlq_file": {
@@ -164,7 +164,9 @@
  "qa_metrics_probe": {
   "db_path": "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db",
   "opened_readonly": true,
+  "bytes_read_from_verified_fd": 16384,
   "file_identity_verified": true,
+  "read_mode": "in_memory_deserialize_from_verified_fd",
   "tables": [
    "qa_error_logs"
   ],
diff --git "a/_bmad-output/\351\252\214\346\224\266\345\215\225/UAT-CARD-G4-9-DLQ\347\234\237\345\256\236\346\214\202\350\275\275census\345\210\206\350\257\212-2026-08-28.md" "b/_bmad-output/\351\252\214\346\224\266\345\215\225/UAT-CARD-G4-9-DLQ\347\234\237\345\256\236\346\214\202\350\275\275census\345\210\206\350\257\212-2026-08-28.md"
index 1b7c65f4..347fc347 100644
--- "a/_bmad-output/\351\252\214\346\224\266\345\215\225/UAT-CARD-G4-9-DLQ\347\234\237\345\256\236\346\214\202\350\275\275census\345\210\206\350\257\212-2026-08-28.md"
+++ "b/_bmad-output/\351\252\214\346\224\266\345\215\225/UAT-CARD-G4-9-DLQ\347\234\237\345\256\236\346\214\202\350\275\275census\345\210\206\350\257\212-2026-08-28.md"
@@ -46,6 +46,8 @@ worktree: "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktre
 | round-6 findings 整改 | **架构级修复 + 6 项**：新增不依赖枚举的**路径层防御**（--out 禁落 transcripts 根内 / 禁等于任一输入 realpath）、QA DB 验证 fd 保持打开至复核完毕、no_token 亦扫描、证据包重生成、ledger 冲突原因自描述、lone surrogate 回退。反例实测：0333 隐藏目录内 transcript 作 --out → exit 2 完好 | 报告 §7g |
 | Codex 复审 round-7 | **关键裁定分离**："92 条冻结 ledger **可以采信**；生成器与 UAT 的纯只读安全声明不可验收"——卡面 census 判据已满足，阻断全在工具安全承诺侧。1 BLOCKER（大小写别名根，无需竞态）+ 4 项路径 TOCTOU + 1 MEDIUM（非原子写）+ 2 LOW | `_bmad-output/审查/codex-review-CARD-G4-9-round7.md` |
 | round-7 findings 整改 | **架构级第二次修复**：写出改 O_EXCL 临时文件+fsync+os.replace（**全文再无 ftruncate 调用**），五项绕过整类失效；containment 改 inode 逐级比较（normcase 在 POSIX 是恒等函数，我的假设错了）；扫描受阻直接拒绝写出。实测：根外 hardlink 指向根内 transcript 作 --out → 源内容完好 | 报告 §7h |
+| Codex 复审 round-8 | 重申裁定分离：**「可验收：92 条冻结 ledger snapshot；不可验收：生成器一般安全性与 UAT 的纯只读声明」**。3 新 BLOCKER（SQLite URI 未转义 #/? / QA DB 仍按 pathname 开可 ABA / 根内末级 symlink 因 rename 不解析而被替换）+ 1 HIGH + 1 MEDIUM | `_bmad-output/审查/codex-review-CARD-G4-9-round8.md` |
+| round-8 findings 整改 | **6/6 完成**：QA DB 改「已验证 fd 读字节 → 内存库 deserialize」（URI 转义与 ABA 一并消失，含 #? 路径实测通过）；containment 加父目录语义（POSIX rename 不解析末级 symlink）；扫描受阻去掉 and args.out（stdout 模式亦拒）；replace 纳入 try + fsync 父目录 | 报告 §7i |
 | 独立 Workflow 4-agent 复核 | G4-9 数字 agent：92 条重算 **0 mismatch**（class/inline/三态/25 request_id/7 transcript 在盘/台账 sha 全 CONFIRMED，仅 2 处描述区间 REFUTED 已修正）；只读契约 agent：与 Codex 同源的 3 条 blocker（已随上整改） | Workflow wf_737b1a95-20b journal |
 
 ## 🔧 Codex round-1 整改记录（13/13 关闭，BLOCKED → 整改完毕）
@@ -132,6 +134,18 @@ round-7 把结论分成了两半，这个区分很重要：
 
 round-7 整改后第七次全量重跑：**92 条、4/88/0/0、89/2/1、6/29、shasum 不变、台账 0600、无临时文件残留——七轮整改数字全程未变**。
 
+## 🔧 Codex round-8 复审整改记录（裁定分离重申 + 3 BLOCKER 全闭）
+
+round-8 把结论说得更清楚了：**「可验收：92 条冻结 ledger snapshot。不可验收：生成器的一般安全性，以及验收单里那句"纯只读、唯一写出口、整类 TOCTOU 已消失"」**。
+
+三条新 BLOCKER 都成立，其中两条有同一个彻底解法：
+
+- **SQLite 打开方式**：`file:路径?mode=ro` 这种写法，路径里只要有个 `#`，`mode=ro` 就掉进 URI 的 fragment 被忽略，SQLite 可能按默认的**读写模式**打开——这直接推翻"唯一写出口"。而且就算持有验证过的文件描述符，SQLite 还是按路径自己去开，中间被换掉也发现不了。→ 改成从**已验证的文件描述符读出全部字节，灌进内存数据库**。SQLite 从此不碰路径，两个问题一起消失。
+- **根内的软链接**：POSIX 规定重命名操作**不跟随末级软链接**。所以 `--out` 如果是恢复源目录里的一个软链接（指向外面），我按"它指向哪"判断会放行，但实际被替换的是**目录里那个链接本身**。→ 判定改看**父目录在不在恢复源里**。
+- **stdout 模式漏网**：扫描受阻的拒绝条件我写成了"且指定了 --out"，于是省略 `--out` 就能绕过。→ 去掉该条件。
+
+round-8 整改后第八次全量重跑：**92 条、4/88/0/0、89/2/1、6/29、shasum 不变、无 tmp 残留——八轮整改数字全程未变**。
+
 ## 📄 交付物清单（全部新增，零业务代码改动）
 
 - `backend/scripts/census_dead_letter_episodes.py` — 唯一代码产物（只读 census 脚本，纯 stdlib）
diff --git a/backend/scripts/census_dead_letter_episodes.py b/backend/scripts/census_dead_letter_episodes.py
index 6f264b74..957529ec 100644
--- a/backend/scripts/census_dead_letter_episodes.py
+++ b/backend/scripts/census_dead_letter_episodes.py
@@ -258,6 +258,13 @@ def resolve_group_attribution(tokens: list[str], transcripts_dir: Path) -> dict:
                     per_token[t].append(candidate)
     result["all_candidate_paths"] = sorted(set(all_candidates))
 
+    # round-8 HIGH 整改: 早退分支也必须携带扫描错误 —— 否则 no_token /
+    # token_conflict 组的 walk 错误不会进入 scan_blocked 判定。
+    if walk_errors:
+        result["scan_errors"] = walk_errors[:5]
+    if stat_failures:
+        result["stat_failures"] = stat_failures[:5]
+
     if not uniq:
         # 无 token: 未做任何归因扫描 —— 不是"确认无源"（round-5 MEDIUM 整改）
         result["attribution_conflict"] = True
@@ -295,12 +302,13 @@ def resolve_group_attribution(tokens: list[str], transcripts_dir: Path) -> dict:
 
 
 def probe_qa_metrics(db_path: Path, error_types: list[str]) -> tuple[dict, tuple[int, int] | None]:
-    """只读核销 qa_metrics.db（URI mode=ro，无写路径）。返回 (结果, 实际身份)。
+    """只读核销 qa_metrics.db。返回 (结果, 实际读取对象身份)。
 
-    round-5 BLOCKER②/MEDIUM 整改: 原实现按路径 stat 取身份、SQLite 稍后按路径
-    重新打开 —— 两者可能不是同一对象，且无 regular-file/nonblocking 门（FIFO
-    会阻塞）。现: fd 打开取 fstat 身份 + S_ISREG 门 → SQLite 打开 → 复核路径
-    身份仍等于该身份，不等即拒绝（不采信被换入的对象）。
+    round-8 BLOCKER①② 整改: 不再让 SQLite 按 **路径** 打开 —— 那既有 URI 转义
+    问题（路径含 ``?``/``#`` 时 ``mode=ro`` 会落进被忽略的 fragment，SQLite 可能
+    按默认读写模式打开），又有 A→B→A 的 ABA（验证 fd 是 A，connection 却可能读
+    到 B）。改为从**已验证的 fd** 读全量字节 → ``sqlite3`` 内存库
+    ``deserialize``：全程不经路径、不落任何文件，两个问题一并消失。
     """
     result: dict = {"db_path": str(db_path), "opened_readonly": False}
     if not db_path.exists():
@@ -311,34 +319,37 @@ def probe_qa_metrics(db_path: Path, error_types: list[str]) -> tuple[dict, tuple
     except OSError as e:
         result["verdict"] = f"open_refused: {e}"
         return result, None
-    # round-6 BLOCKER② 整改: 验证 fd **保持打开**直到 SQLite 连接建立并复核完毕
-    # —— 原实现验证后即关闭，SQLite 按路径重开可被 A→B→A 的 ABA 骗过。
-    conn = None
     try:
         st = os.fstat(fd)
         if not stat.S_ISREG(st.st_mode):
             result["verdict"] = "not_regular_file_refused"
             return result, None
         identity = (st.st_dev, st.st_ino)
+        chunks = []
+        while True:
+            block = os.read(fd, 1 << 20)
+            if not block:
+                break
+            chunks.append(block)
+        db_bytes = b"".join(chunks)
+        result["bytes_read_from_verified_fd"] = len(db_bytes)
+    finally:
+        os.close(fd)
 
-        uri = f"file:{db_path}?mode=ro"
-        conn = sqlite3.connect(uri, uri=True)
-        # 连接建立后在**持有验证 fd 的同时**复核路径身份
-        try:
-            recheck = os.stat(db_path)
-        except OSError as e:
-            result["verdict"] = f"recheck_stat_failed: {e}"
-            return result, identity
-        if (recheck.st_dev, recheck.st_ino) != identity:
-            result["verdict"] = "identity_changed_between_verify_and_open_refused"
-            return result, identity
-        # 再次 fstat 验证 fd：确认它仍指向同一对象且未被 unlink 替换
-        st2 = os.fstat(fd)
-        if (st2.st_dev, st2.st_ino) != identity or st2.st_nlink == 0:
-            result["verdict"] = "verified_fd_invalidated_refused"
-            return result, identity
+    conn = None
+    try:
+        conn = sqlite3.connect(":memory:")
+        conn.deserialize(db_bytes)
+    except Exception as e:  # noqa: BLE001 — 非法/加密 DB 如实记录，不中断 census
+        result["verdict"] = f"deserialize_failed: {str(e)[:80]}"
+        if conn is not None:
+            conn.close()
+        return result, identity
+
+    try:
         result["opened_readonly"] = True
         result["file_identity_verified"] = True
+        result["read_mode"] = "in_memory_deserialize_from_verified_fd"
         tables = [
             r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
         ]
@@ -354,9 +365,7 @@ def probe_qa_metrics(db_path: Path, error_types: list[str]) -> tuple[dict, tuple
         else:
             result["verdict"] = "qa_error_logs_table_missing"
     finally:
-        if conn is not None:
-            conn.close()
-        os.close(fd)
+        conn.close()
     return result, identity
 
 
@@ -460,7 +469,12 @@ def main(argv: list[str] | None = None) -> int:
         # round-7 BLOCKER 整改: 用 **inode 身份逐级比较**（_path_is_within），
         # 不用路径字符串前缀 —— normcase 在 POSIX 上是恒等函数，大小写不敏感
         # 卷上的别名根（/Users vs /users）realpath 字符串不同但 samefile=True。
-        if _path_is_within(args.out, args.transcripts_dir):
+        # round-8 BLOCKER③ 整改: rename/replace **不解析末级 symlink**（POSIX），
+        # 故 --out 若是根内的 symlink（指向根外），realpath 会判"根外"而放行，
+        # 但 replace 实际替换的是根内那个目录项。判定改用**父目录**语义 +
+        # lstat 末级：父目录在根内 → 拒绝；末级本身是 symlink 也按其所在目录判。
+        out_parent = os.path.dirname(os.path.abspath(args.out)) or "."
+        if _path_is_within(out_parent, args.transcripts_dir) or _path_is_within(args.out, args.transcripts_dir):
             print(
                 f"--out 落在 transcripts 根内（恢复源区域），无条件拒绝写出: {args.out}",
                 file=sys.stderr,
@@ -743,7 +757,9 @@ def main(argv: list[str] | None = None) -> int:
         for k, v in group_attribution.items()
         if v.get("scan_errors") or v.get("stat_failures")
     ]
-    if scan_blocked and args.out:
+    # round-8 HIGH 整改: 去掉 `and args.out` —— stdout 模式同样不得在保护集
+    # 残缺时输出台账（否则 --out 省略即绕过该门）。
+    if scan_blocked:
         print(
             f"transcripts 扫描受阻（{len(scan_blocked)} 组），保护集不完整，拒绝写出台账；首例: {scan_blocked[0][1]}",
             file=sys.stderr,
@@ -799,9 +815,22 @@ def main(argv: list[str] | None = None) -> int:
             print(f"台账写入失败，已清理临时文件: {e}", file=sys.stderr)
             return 2
         os.close(tmp_fd)
-        # 原子替换。目标若是恢复源，路径层与 inode 层已在前面拒绝；此处 replace
-        # 只作用于本进程新建的 tmp，不存在"截断别人的文件"这一步。
-        os.replace(tmp_path, out_path)
+        # 原子替换 + 父目录 fsync（round-8 MEDIUM 整改：replace 纳入 try，
+        # EXDEV/EBUSY/EACCES/ENOSPC 等异常一律清理 tmp 不留残留）。
+        try:
+            os.replace(tmp_path, out_path)
+            dir_fd = os.open(out_path.parent, os.O_RDONLY)
+            try:
+                os.fsync(dir_fd)
+            finally:
+                os.close(dir_fd)
+        except OSError as e:
+            try:
+                os.unlink(tmp_path)
+            except OSError:
+                pass
+            print(f"台账原子替换失败，已清理临时文件: {e}", file=sys.stderr)
+            return 2
         print(f"台账已写入: {args.out}")
     else:
         print(out_json)

exec
/bin/zsh -lc "tail -n 360 '_bmad-output/审查/codex-review-CARD-G4-9-round8.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
    49	| 独立 Workflow 4-agent 复核 | G4-9 数字 agent：92 条重算 **0 mismatch**（class/inline/三态/25 request_id/7 transcript 在盘/台账 sha 全 CONFIRMED，仅 2 处描述区间 REFUTED 已修正）；只读契约 agent：与 Codex 同源的 3 条 blocker（已随上整改） | Workflow wf_737b1a95-20b journal |
    50	
    51	## 🔧 Codex round-1 整改记录（13/13 关闭，BLOCKED → 整改完毕）
    52	
   121	## 🔧 Codex round-7 复审整改记录（关键裁定分离 + 架构级第二次修复）
   122	
   123	round-7 把结论分成了两半，这个区分很重要：
   124	
   125	> **「现有 92 条冻结 ledger 可以采信；生成器与 UAT 的纯只读安全声明不可验收。」**
   126	
   127	也就是说：这张卡要交付的 census 结论（92 条的分类、对账、三态、挂载真相、稳定键、运行零写入）**已经过关**；卡住的是"这个脚本作为工具，其只读承诺是否经得起敌意输入"。
   128	
   129	- **一个无需竞态的真实绕过**：大小写不敏感卷上 `/Users/...` 与 `/users/...` 是同一个目录但 realpath 字符串不同，我 round-6 用来防御的 `os.path.normcase` **在 macOS/Linux 上根本是恒等函数**——这是我的知识性错误。改成逐级比较 **inode 身份**，不再依赖任何字符串。
   130	- **五项绕过共用一个根源**：它们都依附于"截断一个已存在的文件"这个动作。改成「新建临时文件 → 写 → fsync → 原子替换」后，脚本**全文再没有任何截断调用**，这一整类绕过连同"崩溃留下半个台账"的风险一起消失。实测：拿一个指向恢复源的 hardlink 当 `--out`，台账正常写出，而**源文件内容一个字节没变**。
   131	- **扫描受阻不再只是标记**：看不全就意味着保护集不完整，现在直接拒绝写出台账。
   132	
   133	round-7 整改后第七次全量重跑：**92 条、4/88/0/0、89/2/1、6/29、shasum 不变、台账 0600、无临时文件残留——七轮整改数字全程未变**。
   134	
   135	## 📄 交付物清单（全部新增，零业务代码改动）
   136	
   195	## §7h Codex round-7 复审整改记录（关键裁定分离 + 架构级第二次修复）
   196	
   197	round-7 给出了本卡最重要的一次裁定分离：
   198	
   199	> **「现有 92 条冻结 ledger 可以采信；CARD-G4-9 生成器与 UAT 的纯只读安全声明不可验收。」**
   200	
   201	即：卡面的 census 判据（分类/对账/三态/挂载真相/稳定键/shasum 不变）已满足且被独立复算确认；阻断项全部落在"生成器作为工具的只读安全承诺"上。逐条整改：
   202	
   203	- **BLOCKER（大小写别名根）**：本机实测 `/Users/Heishing/.claude/projects` 与 `/users/heishing/...` `samefile=True` 但 `realpath` 字符串不同，prefix guard 返回 False——**无需竞态的实际绕过**。我 round-6 用的 `os.path.normcase` 在 POSIX 上是**恒等函数**（假设错误）。**整改**：新增 `_path_is_within()`，从目标逐级向上比较 **inode 身份**，完全不依赖路径字符串；`--out` 与输入文件的比较改 `os.path.samefile`。实测：别名根作 `--out` → exit 2，正例无回归。
   204	- **NOT-CLOSED ×4（根外 hardlink 指向隐藏目录内 transcript / 根 retarget TOCTOU / 检查后换父目录 symlink 或 basename hardlink）+ MEDIUM（非原子写）**：这五项依附于同一个动作——**截断一个已存在的文件**。**架构级修复**：写出改为「同目录 `O_EXCL` 新建临时文件 → 写 → `fsync` → `os.replace` 原子替换」，**全文再无任何 `ftruncate` 调用**。`O_EXCL` 保证写入目标是本进程新建的对象，因此"把 `--out` 换成指向恢复源的 hardlink / 父目录 symlink / 大小写别名"整类绕过失效；`os.replace` 同时消除崩溃/ENOSPC 留下部分台账的风险。实测：根外 hardlink 指向根内 transcript 作 `--out` → 台账正常写出而**源文件内容完好**（`os.replace` 只重绑定该名字，不触碰底层 inode）。
   205	- **NOT-CLOSED（扫描受阻仅标记不停写）**：扫描受阻 ⇒ 保护集必然不完整。**整改**：`scan_errors`/`stat_failures` 非空时**直接拒绝写出台账**（exit 2），实测不落盘。
   206	- **LOW（lone surrogate 回退失效）**：异常发生在后续 `write`，不在原 `try` 内。**整改**：`json.dumps` 后立即 `.encode("utf-8")` 探测，编码错误在写出前暴露并回退 `ensure_ascii=True`。
   207	- **LOW（receipt 用 8 位缩写）**：如实登记为已知限制（仓库内唯一可解析），未改为 40-hex 以保持 receipt 可读性——列 follow-up。
   208	
   209	round-7 整改后第七次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变、台账 mode 0600、无临时文件残留——七轮整改数字全程未变**。
     1	== CARD-G4-9 只读自证（round-7 整改版）==
     2	脚本 sha256: 810e01b0eeacb5fca8beef863c68ac4f4e77bd596465db07e82502c6bb44481d
     3	生成时点: round-7 整改后（随每轮整改重生成）
     4	
     5	--- (1) 全部 import 行（应只有 stdlib）:
     6	52:from __future__ import annotations
     7	54:import argparse
     8	55:import hashlib
     9	56:import json
    10	57:import os
    11	58:import re
    12	59:import sqlite3
    13	60:import stat
    14	61:import sys
    15	62:from collections import Counter, defaultdict
    16	63:from datetime import datetime, timezone
    17	64:from pathlib import Path
    18	--- (2) neo4j/graphiti/bolt/app. 在 import 行的命中（应 0）:
    19	0
    20	0 ✓
    21	--- (3) --apply 定义（应 0）:
    22	0
    23	0 ✓
    24	--- (4) ⛔ 无任何截断调用（round-7 架构整改：从不截断既有文件）:
    25	grep "os.ftruncate|.truncate(" 命中: 0 ✓（'ftruncate' 字样仅出现在说明注释中，非调用）
    26	--- (5) 唯一写出口 = O_EXCL 新建临时文件 → fsync → os.replace 原子替换:
    27	779:        # round-7 架构整改: 不再截断既有文件 —— 同目录 O_EXCL 新建临时文件 →
    28	780:        # 写 → fsync → os.replace 原子替换。O_EXCL 保证目标是本进程新建的对象，
    29	785:        tmp_path = out_path.with_name(f".{out_path.name}.census-tmp-{os.getpid()}")
    30	787:            tmp_fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    31	789:            print(f"临时台账文件无法新建（O_EXCL）: {tmp_path} ({e})", file=sys.stderr)
    32	795:                os.fsync(tmp_fd)
    33	804:        os.replace(tmp_path, out_path)
    34	--- (6) 恢复源禁写区判定（inode 身份逐级比较，不依赖路径字符串）:
    35	77:def _path_is_within(target: str, root: str) -> bool:
    36	104:def _same_file(a: str, b: str) -> bool:
    37	255:                if not _path_is_within(candidate, root_str):
    38	457:    # 路径层防御：--out 的 realpath 不得落在 transcripts 根内、不得等于任一
    39	460:        # round-7 BLOCKER 整改: 用 **inode 身份逐级比较**（_path_is_within），
    40	463:        if _path_is_within(args.out, args.transcripts_dir):
    41	465:                f"--out 落在 transcripts 根内（恢复源区域），无条件拒绝写出: {args.out}",
    42	470:        if any(_same_file(args.out, ip) for ip in input_paths):
    43	--- (7) 读侧身份绑定 + 扫描完整性前提:
    44	310:        fd = os.open(db_path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    45	322:        identity = (st.st_dev, st.st_ino)
    46	338:            result["verdict"] = "verified_fd_invalidated_refused"
    47	370:    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    48	375:        identity = (st.st_dev, st.st_ino)
    49	748:            f"transcripts 扫描受阻（{len(scan_blocked)} 组），保护集不完整，拒绝写出台账；首例: {scan_blocked[0][1]}",
    50	760:                print(f"候选源无法 stat，保护集不完整，拒绝写出: {tpath} ({e})", file=sys.stderr)
    51	--- (8) fail-closed 判定门:
    52	131:            out.append(("", f"utf8_decode_error: {e}"))
    10	d2827a6d  CARD-G4-9 round-4 整改
    11	d8d887f2  本 receipt 首次落盘
    12	4c125f19  CARD-G4-9 round-5 整改
    13	5b371253  CARD-G4-9 round-6 架构级修复
    14	4ba4f847  receipt 补 round-5/6 链
    15	f389980c  CARD-G4-9 round-7 架构级修复（消除截断动作；本 receipt 当前版所描述的 commit）
    16	
    17	各阶段交付物 blob 可用 git cat-file 复核；台账头部 dlq_file.sha256 为 DLQ 快照指纹。

**Reviewing output handling on scan block**
**Identifying incomplete scan block handling**
**Identifying path-based write vulnerability**
**Assessing file permission privacy risks**
**Questioning unique write claim validity**
**Planning final memory citation and append**
exec
/bin/zsh -lc "nl -ba /Users/Heishing/.codex/memories/skills/canvas-adversarial-audit/SKILL.md | sed -n '1,55p'
nl -ba /Users/Heishing/.codex/memories/MEMORY.md | sed -n '179,188p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
     1	---
     2	name: canvas-adversarial-audit
     3	description: Conduct a read-only, parallel, evidence-first adversarial audit of Canvas P1 closure claims, especially vault admission, Graphiti quarantine, and SnapshotV3.
     4	argument-hint: "[task-book path or P1 scope]"
     5	user-invocable: false
     6	allowed-tools: Read, Grep, Glob, Bash
     7	---
     8	
     9	# Canvas adversarial audit
    10	
    11	## When to use
    12	
    13	Use for a user-requested adversarial or closure audit in the Canvas Learning System worktree, particularly P1-05/P1-01/P1-08. Do not use to implement fixes, access prohibited raw-vault content, or declare a historical finding current without revalidation.
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

**Integrating rollout IDs from memory and skill**
mcp: sequential-thinking/sequentialthinking started
mcp: sequential-thinking/sequentialthinking (completed)
mcp: sequential-thinking/sequentialthinking started
mcp: sequential-thinking/sequentialthinking (completed)
mcp: sequential-thinking/sequentialthinking started
mcp: sequential-thinking/sequentialthinking (completed)
**Confirming completion of update plan**
codex
三轨结果一致：冻结 snapshot 本身仍是 PASS；生成器 closure 不是。最强的无竞态反例不是预置 tmp symlink（它会被 `O_EXCL` 安全拒绝），而是“恢复根内的末级 symlink 指向根外”：containment 因 `realpath` 判成根外，`os.replace` 却替换 symlink 本身，于是仍在恢复根内发生写入。另有 scan-error 早退吞错与 round-7 文件中未被本次提交处理的 QA SQLite 两项旧阻断。
只读静态审阅、官方语义核对、三轨交叉审计及冻结 ledger exact-byte 复算均已完成；未修改或创建工作区文件。
  ✓ 锚定 HEAD、commit f389980c、工作树状态、任务/规则与变更文件
  ✓ 静态审阅原子写出实现并设计/验证指定反例
  ✓ 审阅 _path_is_within 与 samefile 的 symlink/挂载边界
  ✓ 独立只读复算冻结 ledger 的全部数量、分类、权限和残留
  ✓ 交叉复核高风险发现并给出逐项裁定、分级和总裁定
**Verifying final git status**
exec
/bin/zsh -lc "git status --porcelain=v1
git rev-parse HEAD
find . -name '*.census-tmp-*' -print | wc -l
stat -f 'ledger_mode=%Lp ledger_size=%z ledger_nlink=%l' '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 429ms:
       0
ledger_mode=600 ledger_size=142411 ledger_nlink=1

**Organizing final verdict and anchors**
**Detailing claim closure statuses**
**Summarizing counterexample scenarios**
**Identifying blocker severity issues**
**Classifying severity levels and citing sources**
**Confirming source path validity and citation approach**
**Classifying acceptance status per item**
**Explaining link count decrement behavior**
**Verifying inode differences during replacement**
**Analyzing bind mount inode handling**
**Noting power-loss durability limitation**
**Clarifying commit anchoring and metrics**
**Planning detailed audit report structure**
**Confirming stable samefile function behavior**
**Assessing symlink and hardlink risk matrix**
**Planning SQLite citation inclusion**
**Documenting file operation references**
**Clarifying ledger acceptance criteria**
codex
总裁定：**round-8 仍阻断，不可验收生成器与 UAT 的“纯只读安全”声明；现有 92 条冻结 ledger 可以验收并继续采信。**

审阅锚点：`HEAD=85dd1c8fd625759642fa45e483bec52e999efb0a`，修复提交 `f389980c4cee093294e4888e8341861a1d656e57`；脚本与 ledger 在两者间 blob 完全相同。

## 逐项裁定

| 修复声明 | 裁定 | 依据 |
|---|---|---|
| 全文不再截断既有文件 | **CLOSED（狭义）** | 确认无 `ftruncate/O_TRUNC` 调用；实际写入先以 `O_CREAT\|O_EXCL` 创建新 inode。[写出链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:778) |
| 因此 hardlink/symlink/父目录换链整类攻击全部失效 | **NOT-CLOSED** | `O_EXCL` 只绑定创建时的 fd；[os.replace](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:804)再次解析 tmp 与目标 pathname。 |
| 大小写别名根 | **CLOSED（namespace 稳定时）** | 本机只读复算仍为 `samefile=True / realpath 字符串不同`，新 inode 祖先比较正确返回 within。[实现](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:77) |
| containment 整体闭合 | **NOT-CLOSED · BLOCKER** | 根内末级 symlink 指向根外时，`realpath(target)`判根外；但 rename/replace 操作 symlink 本身，于是仍在恢复根内创建 tmp 并替换目录项。POSIX 明确规定 rename 不解析末级 symlink。[POSIX rename](https://pubs.opengroup.org/onlinepubs/9799919799/functions/rename.html) |
| 扫描受阻必 exit 2 | **NOT-CLOSED · HIGH** | no-token/token-conflict 在写入 `scan_errors/stat_failures` 前提前返回，[line 261](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:261)；而且拒绝条件是 `scan_blocked and args.out`，stdout 模式仍输出 ledger、exit 0。[line 741](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:741) |
| lone-surrogate 回退 | **CLOSED** | `json.dumps` 后立即 strict UTF-8 encode 探测，异常进入 `ensure_ascii=True` 回退。[line 770](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:770) |
| 原子写消除半截 ledger | **CLOSED（成功 replace 时）** | file flush+fsync 后 replace，成功发布原子且目标不会呈现半写内容。[Python os.replace](https://docs.python.org/3/library/os.html#os.replace) |
| 崩溃/ENOSPC/权限错误均无 tmp 残留 | **NOT-CLOSED · MEDIUM** | `os.replace` 在 try 外；`EXDEV/EBUSY/EACCES/ENOSPC` 会直接冒泡并留下 tmp，且未 fsync 父目录。 |

## 指定反例结果

- **预置可预测 tmp symlink**：安全面 **CLOSED**。`O_EXCL` 遇任何既有 symlink/FIFO/文件都会失败，不跟随写入；但构成稳定 DoS，PID 重用或崩溃遗留会阻断后续运行。

- **tmp 打开后换名**：**NOT-CLOSED · HIGH**。攻击者可在写入 fd 后 unlink/rebind 可预测 tmp 名；写和 fsync 仍落在原 fd，但 `os.replace(tmp_path, out_path)`会发布攻击者替换进去的文件、symlink 或 hardlink。

- **目标是 symlink**：replace 覆盖 symlink 本身，不改 referent；但这正导致“根内 symlink → 根外”的无竞态 containment 绕过。

- **目标是 hardlink**：正文 bytes 不变，但替换该目录项会减少受保护 inode 的 link count，因此“内容未变”成立，“纯只读零元数据修改”不成立。POSIX 明确要求移除 hardlink 时递减 link count。[POSIX unlink](https://pubs.opengroup.org/onlinepubs/9699919799/functions/unlink.html)

- **父目录 symlink retarget**：单独 retarget 通常使 tmp 源路径消失并报错；若在新目标目录预置可预测 tmp 名，则 replace 可覆盖新的目标目录项，故组合攻击仍 **NOT-CLOSED**。

- **跨设备/挂载点**：稳定同父目录时不会跨设备；挂载或父目录切换可产生 `EXDEV/EBUSY`，目前未捕获。将 transcripts 的某个子目录 bind/nullfs 到根外 alias 时，inode 祖先链不会经过 transcripts 根，形成无需竞态的 mount-alias 绕过。

- **目录权限**：创建 tmp 失败能 exit 2；创建成功后因 sticky bit、ACL、immutable 或权限变化导致 replace 失败时，异常未清理。

- **并发同 PID**：同时 open 时一方成功、一方 `EEXIST`；第一方 replace 后，同 PID 后续调用又可成功并最后覆盖。不会混写，但没有序列化或唯一发布者。

- **循环 symlink**：稳定根循环会在 `is_dir` 阶段拒绝，祖先循环通常在 tmp open 时 `ELOOP`；但 `realpath(strict=False)`不是 fail-closed namespace 绑定，循环解除或 retarget 仍落入上述 TOCTOU。

旧四项按“纯只读”口径：隐藏 transcript hardlink **NOT-CLOSED（link-count 元数据）**；根 retarget **NOT-CLOSED**；父 symlink retarget **NOT-CLOSED（与预置 tmp 组合）**；basename hardlink **NOT-CLOSED（字节安全但元数据被改）**。

## 仍被遗漏的 round-7 阻断

精确的 round-7 文件其实还裁定了 QA DB 的 rename 型 A→B→A 与 URI 问题，[round-7:6408](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/codex-review-CARD-G4-9-round7.md:6408)；但 UAT 将其摘要成“1 BLOCKER + 路径项”，[UAT:47](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:47)，且 `f389980c` 未修改 QA 打开链：

- **BLOCKER**：`file:{db_path}?mode=ro` 未转义 `?/#`。如路径含 `#`，`mode=ro` 会落入被忽略的 fragment，SQLite 可能按默认读写/创建模式打开另一个文件，直接反驳“唯一写出口”。[代码](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:324)、[SQLite URI 规则](https://www.sqlite.org/uri.html)、[Python sqlite3 URI](https://docs.python.org/3/library/sqlite3.html#how-to-work-with-sqlite-uris)

- **HIGH/BLOCKER**：验证 fd=A 保持打开，但 SQLite 仍另按 pathname 打开；A→B→A 调度可使 connection 读取 B，而复核仍看到 A。[QA 打开链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:297)

## 冻结 ledger 复算：PASS

从 live DLQ exact bytes 独立解析、分类、哈希、分组和聚簇，未 import 被审生成器：

| 项目 | 只读复算 |
|---|---|
| 源对象 | 99,915 bytes；SHA-256 `3b37460f…ef3ba590`，与 [ledger header](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:6)一致 |
| 总量 / parse | 92 / unparseable 0 |
| class | 89 / 2 / 1，unexpected 0 |
| recoverability | byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0 |
| attribution | 3，全部 `no_token`，均为 inline byte-exact |
| 重复簇 | 6 簇 / 29 行；大小 `16,4,3,2,2,2` |
| 逐条对账 | class/inline/recoverability/reason 0 mismatch |
| ledger 文件 | SHA-256 `ea4b9007…c78a88`；当前 mode `0600`、nlink 1 |
| tmp 残留 | 0 |

主审只遍历了 transcript 文件名/状态元数据，未读取正文；当前仍得到 7 个唯一指针、无 walk error。`0600` 是当前工作树事实，但 Git tree 只保存 `100644`，因此不是跨 checkout 可冻结的权限属性。

所以最终边界很明确：

- **可验收：92 条冻结 ledger snapshot。**
- **不可验收：当前生成器的一般安全性，以及 UAT 的“纯只读、唯一写出口、整类 TOCTOU 已消失”声明。**

本轮未修改、创建或删除任何文件；开始与结束均只有预先存在的未跟踪 round-8 文档。`graphiti-canvas` 未在本会话暴露，故无法执行规定的 Graphiti 搜索；Sequential Thinking 已完成。


tokens used
238,732
总裁定：**round-8 仍阻断，不可验收生成器与 UAT 的“纯只读安全”声明；现有 92 条冻结 ledger 可以验收并继续采信。**

审阅锚点：`HEAD=85dd1c8fd625759642fa45e483bec52e999efb0a`，修复提交 `f389980c4cee093294e4888e8341861a1d656e57`；脚本与 ledger 在两者间 blob 完全相同。

## 逐项裁定

| 修复声明 | 裁定 | 依据 |
|---|---|---|
| 全文不再截断既有文件 | **CLOSED（狭义）** | 确认无 `ftruncate/O_TRUNC` 调用；实际写入先以 `O_CREAT\|O_EXCL` 创建新 inode。[写出链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:778) |
| 因此 hardlink/symlink/父目录换链整类攻击全部失效 | **NOT-CLOSED** | `O_EXCL` 只绑定创建时的 fd；[os.replace](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:804)再次解析 tmp 与目标 pathname。 |
| 大小写别名根 | **CLOSED（namespace 稳定时）** | 本机只读复算仍为 `samefile=True / realpath 字符串不同`，新 inode 祖先比较正确返回 within。[实现](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:77) |
| containment 整体闭合 | **NOT-CLOSED · BLOCKER** | 根内末级 symlink 指向根外时，`realpath(target)`判根外；但 rename/replace 操作 symlink 本身，于是仍在恢复根内创建 tmp 并替换目录项。POSIX 明确规定 rename 不解析末级 symlink。[POSIX rename](https://pubs.opengroup.org/onlinepubs/9799919799/functions/rename.html) |
| 扫描受阻必 exit 2 | **NOT-CLOSED · HIGH** | no-token/token-conflict 在写入 `scan_errors/stat_failures` 前提前返回，[line 261](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:261)；而且拒绝条件是 `scan_blocked and args.out`，stdout 模式仍输出 ledger、exit 0。[line 741](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:741) |
| lone-surrogate 回退 | **CLOSED** | `json.dumps` 后立即 strict UTF-8 encode 探测，异常进入 `ensure_ascii=True` 回退。[line 770](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:770) |
| 原子写消除半截 ledger | **CLOSED（成功 replace 时）** | file flush+fsync 后 replace，成功发布原子且目标不会呈现半写内容。[Python os.replace](https://docs.python.org/3/library/os.html#os.replace) |
| 崩溃/ENOSPC/权限错误均无 tmp 残留 | **NOT-CLOSED · MEDIUM** | `os.replace` 在 try 外；`EXDEV/EBUSY/EACCES/ENOSPC` 会直接冒泡并留下 tmp，且未 fsync 父目录。 |

## 指定反例结果

- **预置可预测 tmp symlink**：安全面 **CLOSED**。`O_EXCL` 遇任何既有 symlink/FIFO/文件都会失败，不跟随写入；但构成稳定 DoS，PID 重用或崩溃遗留会阻断后续运行。

- **tmp 打开后换名**：**NOT-CLOSED · HIGH**。攻击者可在写入 fd 后 unlink/rebind 可预测 tmp 名；写和 fsync 仍落在原 fd，但 `os.replace(tmp_path, out_path)`会发布攻击者替换进去的文件、symlink 或 hardlink。

- **目标是 symlink**：replace 覆盖 symlink 本身，不改 referent；但这正导致“根内 symlink → 根外”的无竞态 containment 绕过。

- **目标是 hardlink**：正文 bytes 不变，但替换该目录项会减少受保护 inode 的 link count，因此“内容未变”成立，“纯只读零元数据修改”不成立。POSIX 明确要求移除 hardlink 时递减 link count。[POSIX unlink](https://pubs.opengroup.org/onlinepubs/9699919799/functions/unlink.html)

- **父目录 symlink retarget**：单独 retarget 通常使 tmp 源路径消失并报错；若在新目标目录预置可预测 tmp 名，则 replace 可覆盖新的目标目录项，故组合攻击仍 **NOT-CLOSED**。

- **跨设备/挂载点**：稳定同父目录时不会跨设备；挂载或父目录切换可产生 `EXDEV/EBUSY`，目前未捕获。将 transcripts 的某个子目录 bind/nullfs 到根外 alias 时，inode 祖先链不会经过 transcripts 根，形成无需竞态的 mount-alias 绕过。

- **目录权限**：创建 tmp 失败能 exit 2；创建成功后因 sticky bit、ACL、immutable 或权限变化导致 replace 失败时，异常未清理。

- **并发同 PID**：同时 open 时一方成功、一方 `EEXIST`；第一方 replace 后，同 PID 后续调用又可成功并最后覆盖。不会混写，但没有序列化或唯一发布者。

- **循环 symlink**：稳定根循环会在 `is_dir` 阶段拒绝，祖先循环通常在 tmp open 时 `ELOOP`；但 `realpath(strict=False)`不是 fail-closed namespace 绑定，循环解除或 retarget 仍落入上述 TOCTOU。

旧四项按“纯只读”口径：隐藏 transcript hardlink **NOT-CLOSED（link-count 元数据）**；根 retarget **NOT-CLOSED**；父 symlink retarget **NOT-CLOSED（与预置 tmp 组合）**；basename hardlink **NOT-CLOSED（字节安全但元数据被改）**。

## 仍被遗漏的 round-7 阻断

精确的 round-7 文件其实还裁定了 QA DB 的 rename 型 A→B→A 与 URI 问题，[round-7:6408](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/codex-review-CARD-G4-9-round7.md:6408)；但 UAT 将其摘要成“1 BLOCKER + 路径项”，[UAT:47](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:47)，且 `f389980c` 未修改 QA 打开链：

- **BLOCKER**：`file:{db_path}?mode=ro` 未转义 `?/#`。如路径含 `#`，`mode=ro` 会落入被忽略的 fragment，SQLite 可能按默认读写/创建模式打开另一个文件，直接反驳“唯一写出口”。[代码](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:324)、[SQLite URI 规则](https://www.sqlite.org/uri.html)、[Python sqlite3 URI](https://docs.python.org/3/library/sqlite3.html#how-to-work-with-sqlite-uris)

- **HIGH/BLOCKER**：验证 fd=A 保持打开，但 SQLite 仍另按 pathname 打开；A→B→A 调度可使 connection 读取 B，而复核仍看到 A。[QA 打开链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:297)

## 冻结 ledger 复算：PASS

从 live DLQ exact bytes 独立解析、分类、哈希、分组和聚簇，未 import 被审生成器：

| 项目 | 只读复算 |
|---|---|
| 源对象 | 99,915 bytes；SHA-256 `3b37460f…ef3ba590`，与 [ledger header](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:6)一致 |
| 总量 / parse | 92 / unparseable 0 |
| class | 89 / 2 / 1，unexpected 0 |
| recoverability | byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0 |
| attribution | 3，全部 `no_token`，均为 inline byte-exact |
| 重复簇 | 6 簇 / 29 行；大小 `16,4,3,2,2,2` |
| 逐条对账 | class/inline/recoverability/reason 0 mismatch |
| ledger 文件 | SHA-256 `ea4b9007…c78a88`；当前 mode `0600`、nlink 1 |
| tmp 残留 | 0 |

主审只遍历了 transcript 文件名/状态元数据，未读取正文；当前仍得到 7 个唯一指针、无 walk error。`0600` 是当前工作树事实，但 Git tree 只保存 `100644`，因此不是跨 checkout 可冻结的权限属性。

所以最终边界很明确：

- **可验收：92 条冻结 ledger snapshot。**
- **不可验收：当前生成器的一般安全性，以及 UAT 的“纯只读、唯一写出口、整类 TOCTOU 已消失”声明。**

本轮未修改、创建或删除任何文件；开始与结束均只有预先存在的未跟踪 round-8 文档。`graphiti-canvas` 未在本会话暴露，故无法执行规定的 Graphiti 搜索；Sequential Thinking 已完成。



**Inspecting critical script sections**
exec
/bin/zsh -lc "nl -ba backend/scripts/census_dead_letter_episodes.py | sed -n '60,130p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
    60	import stat
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
    77	def _path_is_within(target: str, root: str) -> bool:
    78	    """target 是否落在 root 目录内 —— 逐级向上比较 **inode 身份**。
    79	
    80	    round-7 BLOCKER 整改: 不能用路径字符串前缀判断 —— 大小写不敏感卷上
    81	    ``/Users/x`` 与 ``/users/x`` 的 realpath 字符串不同但 samefile=True，
    82	    prefix guard 会漏。本实现从 target 逐级取父目录，只要任一级与 root 同
    83	    (st_dev, st_ino) 即判定在其内；target 尚不存在时上溯到存在的祖先。
    84	    """
    85	    try:
    86	        root_st = os.stat(root)
    87	    except OSError:
    88	        return False
    89	    root_id = (root_st.st_dev, root_st.st_ino)
    90	    cur = os.path.realpath(target)
    91	    while True:
    92	        try:
    93	            st = os.stat(cur)
    94	            if (st.st_dev, st.st_ino) == root_id:
    95	                return True
    96	        except OSError:
    97	            pass  # 该级尚不存在（--out 待创建），继续上溯
    98	        parent = os.path.dirname(cur)
    99	        if parent == cur:
   100	            return False
   101	        cur = parent
   102	
   103	
   104	def _same_file(a: str, b: str) -> bool:
   105	    """按 inode 身份比较两个路径（不依赖字符串大小写/规范化）。"""
   106	    try:
   107	        return os.path.samefile(a, b)
   108	    except OSError:
   109	        return False
   110	
   111	
   112	def _split_jsonl_lines(raw: bytes) -> list[tuple[str, str | None]]:
   113	    """按 JSONL 规范只以 LF 分帧，返回 [(line_text, decode_error_or_None)]。
   114	
   115	    - 不用 splitlines(): U+2028/U+2029/裸 CR 会误分行（round-3）。
   116	    - 逐行 **strict** decode（round-4 MEDIUM 整改）: errors="replace" 会把非法
   117	      UTF-8 静默改写成合法对象，让坏字节冒充有效记录。解码失败的行带错误信息
   118	      返回，由调用方归入 unparseable。
   119	    """
   120	    had_trailing_lf = raw.endswith(b"\n")
   121	    if had_trailing_lf:
   122	        raw = raw[:-1]
   123	    if not raw:
   124	        # round-5 LOW 整改: 单独 b"\n" 是一个空行，不是 0 行
   125	        return [("", None)] if had_trailing_lf else []
   126	    out: list[tuple[str, str | None]] = []
   127	    for chunk in raw.split(b"\n"):
   128	        try:
   129	            out.append((chunk.decode("utf-8"), None))
   130	        except UnicodeDecodeError as e:

exec
/bin/zsh -lc "nl -ba backend/scripts/census_dead_letter_episodes.py | sed -n '580,785p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
   580	    for line_no, rec in records:
   581	        cls = classify(rec)
   582	        state, sha_check = inline_state(rec)
   583	        rid = rec.get("request_id")
   584	        try:
   585	            hash(rid)
   586	            hashable = True
   587	        except TypeError:
   588	            hashable = False
   589	        key = ("__missing__", line_no) if (rid is None or not hashable) else (type(rid).__name__, rid)
   590	        sess = group_attribution[key]
   591	        if state == "full_verified":
   592	            recover = "byte_exact"
   593	            basis = "inline 正文全量：sha256 重算与声明一致且长度精确匹配"
   594	        elif state != "anomaly" and full_body_verified(rec):
   595	            recover = "byte_exact"
   596	            basis = "episode_body_full 在盘且 sha256+长度双门对账通过（DEAD_LETTER_STORE_FULL_BODY 生产 opt-in 字段）"
   597	        elif sess["attribution_conflict"]:
   598	            # round-5 HIGH 整改: 可见性判定**优先于** anomaly —— 源看不见时
   599	            # 无论 inline 是什么状态，都不能断言"不可恢复"。
   600	            recover = "unverifiable"
   601	            if sess.get("no_token"):
   602	                why = "记录名未携带 session token，未做任何归因扫描"
   603	            elif sess.get("token_conflict"):
   604	                why = "同组多 token 前缀冲突"
   605	            elif sess.get("scan_errors"):
   606	                why = "扫描遍历受阻（不可读子树）"
   607	            elif sess.get("stat_failures"):
   608	                why = "候选 stat 失败"
   609	            elif sess.get("unreadable_candidates"):
   610	                why = "存在不可读候选"
   611	            else:
   612	                why = "transcript 多命中 ambiguous"
   613	            extra = "；inline 亦对不上账（anomaly）" if state == "anomaly" else ""
   614	            basis = f"源可见性不足，拒绝裁定：{why}{extra}。既不宣称可恢复，也不宣称不可恢复（fail-closed）"
   615	        elif state == "anomaly":
   616	            recover = "unrecoverable"
   617	            basis = "inline 对不上账（anomaly：sha/长度与声明不符），且归因扫描完整可见但无可用源"
   618	        elif sess["transcript_exists"]:
   619	            recover = "approximate"
   620	            basis = (
   621	                f"inline 为 200 字符前缀（前缀性质依赖 to_dict()[:200] 生产不变量，sha 无法直接证明）；"
   622	                f"经 request_id 组归因到唯一在盘 transcript {sess['session_token']}"
   623	                f"（归因 ≠ 内容已验证——本工具未读 transcript 内容；G4-10 可重蒸馏/重格式化近似重建，非逐字节保证）"
   624	            )
   625	        else:
   626	            recover = "unrecoverable"
   627	            basis = "inline 截断；归因扫描完整可见（无遍历错误/无不可读候选）但未找到任何在盘上游源"
   628	        class_dist[cls] += 1
   629	        recover_dist[recover] += 1
   630	        inline_dist[state] += 1
   631	        stable_key = {
   632	            "line_no": line_no,
   633	            "sha256_prefix": str(rec.get("episode_body_sha256", ""))[:16],
   634	            "request_id": rid,
   635	        }
   636	        if recover == "unrecoverable":
   637	            unrecoverable_keys.append(stable_key)
   638	        elif recover == "unverifiable":
   639	            unverifiable_keys.append(stable_key)
   640	        if sess["attribution_conflict"]:
   641	            attribution_conflicts.append(stable_key)
   642	        ledger_records.append(
   643	            {
   644	                "stable_key": stable_key,
   645	                "name": str(rec.get("name", ""))[:80],
   646	                "group_id": rec.get("group_id"),
   647	                "source_description": rec.get("source_description"),
   648	                "error_type": rec.get("error_type"),
   649	                "error_excerpt": str(rec.get("error", ""))[:120],
   650	                "failed_at": rec.get("failed_at"),
   651	                "reference_time": rec.get("reference_time"),
   652	                "class": cls,
   653	                "episode_body_length": rec.get("episode_body_length"),
   654	                "episode_body_sha256": rec.get("episode_body_sha256"),
   655	                "inline_state": state,
   656	                "sha_check": sha_check,
   657	                "session_token": sess["session_token"],
   658	                "transcript_paths": sess["transcript_paths"],
   659	                "transcript_match_count": sess["transcript_match_count"],
   660	                "attribution_conflict": sess["attribution_conflict"],
   661	                # round-6 LOW 整改: ledger 自描述冲突原因，G4-10 可区分
   662	                # 缺 token / token 冲突 / 扫描受阻 / 不可读 / 多命中
   663	                "attribution_conflict_reason": (
   664	                    "no_token"
   665	                    if sess.get("no_token")
   666	                    else "token_conflict"
   667	                    if sess.get("token_conflict")
   668	                    else "scan_errors"
   669	                    if sess.get("scan_errors")
   670	                    else "stat_failures"
   671	                    if sess.get("stat_failures")
   672	                    else "unreadable_candidates"
   673	                    if sess.get("unreadable_candidates")
   674	                    else "ambiguous_multi_match"
   675	                    if sess["attribution_conflict"]
   676	                    else None
   677	                ),
   678	                "recoverability": recover,
   679	                "recoverability_basis": basis,
   680	            }
   681	        )
   682	
   683	    # 语义重复簇（同 name + 全文 sha + group_id）——G4-10 重放去重策略依据
   684	    cluster_map: dict[tuple, list[int]] = defaultdict(list)
   685	    for line_no, rec in records:
   686	        cluster_map[
   687	            (str(rec.get("name", "")), str(rec.get("episode_body_sha256", "")), str(rec.get("group_id")))
   688	        ].append(line_no)
   689	    duplicate_clusters = [
   690	        {"name": k[0][:80], "episode_body_sha256": k[1], "group_id": k[2], "line_nos": v, "occurrences": len(v)}
   691	        for k, v in sorted(cluster_map.items(), key=lambda kv: -len(kv[1]))
   692	        if len(v) > 1
   693	    ]
   694	
   695	    compare_infos = []
   696	    for cp in args.compare:
   697	        cinfo, cid = describe_copy(Path(cp))
   698	        compare_infos.append(cinfo)
   699	        if cid is not None:
   700	            protected_ids.add(cid)
   701	
   702	    if args.qa_metrics_db:
   703	        qa_probe, qa_identity = probe_qa_metrics(
   704	            Path(args.qa_metrics_db),
   705	            [str(r.get("error_type", "")) for _, r in records],
   706	        )
   707	        if qa_identity is not None:
   708	            protected_ids.add(qa_identity)  # 保护实际验证过的对象身份
   709	    else:
   710	        qa_probe = {"verdict": "skipped_no_db_arg"}
   711	
   712	    deviation = {
   713	        k: {"expected": EXPECTED_CLASS_DIST.get(k, 0), "actual": class_dist.get(k, 0)}
   714	        for k in sorted(set(class_dist) | set(EXPECTED_CLASS_DIST))
   715	        if EXPECTED_CLASS_DIST.get(k, 0) != class_dist.get(k, 0)
   716	    }
   717	
   718	    ledger = {
   719	        "card": "CARD-G4-9",
   720	        "generated_at": datetime.now(timezone.utc).isoformat(),
   721	        "privacy": "private-only: transcript_paths 含本机用户名与 session UUID，禁止外发/公网发布",
   722	        "stable_key_semantics": (
   723	            "冻结快照（dlq_file.sha256）内的 occurrence key；line_no 在快照内唯一，"
   724	            "sha256_prefix/request_id 为冗余对账维度——非跨文件重排或语义幂等键"
   725	        ),
   726	        "dlq_file": dlq_info,
   727	        "compare_copies": compare_infos,
   728	        "total_lines": len(raw_lines),
   729	        "total_records": len(records),
   730	        "unparseable_lines": unparseable,
   731	        # round-2 LOW 整改: 固定 schema 补零，消费者无需自行补齐缺席键
   732	        "class_distribution": {
   733	            k: class_dist.get(k, 0) for k in ["budget_400", "schema_entity_type", "group_id_format", "unexpected"]
   734	        },
   735	        "expected_class_distribution": EXPECTED_CLASS_DIST,
   736	        "class_deviation": deviation,
   737	        "recoverability_distribution": {
   738	            k: recover_dist.get(k, 0) for k in ["byte_exact", "approximate", "unverifiable", "unrecoverable"]
   739	        },
   740	        "inline_state_distribution": {
   741	            k: inline_dist.get(k, 0) for k in ["full_verified", "truncated_prefix", "anomaly"]
   742	        },
   743	        "unrecoverable_list": unrecoverable_keys,
   744	        "unverifiable_list": unverifiable_keys,
   745	        "attribution_conflicts": attribution_conflicts,
   746	        "duplicate_clusters": duplicate_clusters,
   747	        "qa_metrics_probe": qa_probe,
   748	        "records": ledger_records,
   749	    }
   750	
   751	    # round-3 BLOCKER-1 绕过① 整改: 归因到的 transcript 是恢复源，
   752	    # --out 指向它同样会截断。写出前并入保护集（此时归因已完成）。
   753	    # round-7 整改: 扫描受阻 ⇒ 保护集必然不完整（隐藏目录内的源看不见）。
   754	    # 仅在台账标 unverifiable 不够 —— 直接拒绝写出，避免在保护集残缺时落盘。
   755	    scan_blocked = [
   756	        (k, v.get("scan_errors") or v.get("stat_failures"))
   757	        for k, v in group_attribution.items()
   758	        if v.get("scan_errors") or v.get("stat_failures")
   759	    ]
   760	    # round-8 HIGH 整改: 去掉 `and args.out` —— stdout 模式同样不得在保护集
   761	    # 残缺时输出台账（否则 --out 省略即绕过该门）。
   762	    if scan_blocked:
   763	        print(
   764	            f"transcripts 扫描受阻（{len(scan_blocked)} 组），保护集不完整，拒绝写出台账；首例: {scan_blocked[0][1]}",
   765	            file=sys.stderr,
   766	        )
   767	        return 2
   768	
   769	    for sess_info in group_attribution.values():
   770	        for tpath in sess_info.get("all_candidate_paths", []):
   771	            try:
   772	                tst = os.stat(tpath)
   773	                protected_ids.add((tst.st_dev, tst.st_ino))
   774	            except OSError as e:
   775	                # round-5 整改: 候选 stat 失败不再静默吞 —— 保护集不完整即拒绝写出
   776	                print(f"候选源无法 stat，保护集不完整，拒绝写出: {tpath} ({e})", file=sys.stderr)
   777	                return 2
   778	    for rec_out in ledger_records:
   779	        for tpath in rec_out.get("transcript_paths", []):
   780	            try:
   781	                tst = os.stat(tpath)
   782	                protected_ids.add((tst.st_dev, tst.st_ino))
   783	            except OSError:
   784	                continue
   785	

exec
/bin/zsh -lc "nl -ba backend/scripts/census_dead_letter_episodes.py | sed -n '190,375p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
   190	    return hashlib.sha256(full_bytes).hexdigest() == declared_sha
   191	
   192	
   193	def session_tokens(name: object) -> list[str]:
   194	    """round-4 LOW 整改: name 非 str（None/数字/列表）不再抛异常。"""
   195	    if not isinstance(name, str):
   196	        return []
   197	    tokens = []
   198	    m = _SESSION_ARCHIVE_PAT.match(name)
   199	    if m:
   200	        tokens.append(m.group(1).lower())
   201	    tokens.extend(t.lower() for t in _SESSION_INLINE_PAT.findall(name))
   202	    return tokens
   203	
   204	
   205	def resolve_group_attribution(tokens: list[str], transcripts_dir: Path) -> dict:
   206	    """组级归因，fail-closed。
   207	
   208	    round-5 BLOCKER① 整改: **先扫描后判定**。原实现在 token 冲突/无 token 时
   209	    扫描前早退，导致这些候选从未进入 all_candidate_paths → 不进 --out 保护集
   210	    → 可被无竞态截断。现无条件对每个 token 扫描收集候选（保护集所需），
   211	    再做冲突/唯一性判定。
   212	    """
   213	    result = {
   214	        "session_token": None,
   215	        "transcript_paths": [],
   216	        "transcript_exists": False,
   217	        "transcript_match_count": 0,
   218	        "attribution_conflict": False,
   219	        # 保护集必须覆盖**所有见到的候选**（含不可读、含被冲突分支排除的）
   220	        "all_candidate_paths": [],
   221	    }
   222	    uniq = sorted(set(tokens), key=len)
   223	
   224	    root_str = str(transcripts_dir)
   225	    walk_errors: list[str] = []
   226	
   227	    def _on_walk_error(err: OSError) -> None:
   228	        walk_errors.append(f"{getattr(err, 'filename', '?')}: {err}")
   229	
   230	    # 单次遍历收集**每个 token** 的候选（无条件，供保护集与判定共用）
   231	    per_token: dict[str, list[str]] = {t: [] for t in uniq}
   232	    all_candidates: list[str] = []
   233	    unreadable: list[str] = []
   234	    stat_failures: list[str] = []
   235	    # round-6 整改: **无论有无 token 都遍历** —— no_token 时原实现完全不扫描，
   236	    # all_candidate_paths 为空，该组见不到的候选就进不了保护集。
   237	    for dirpath, _dirnames, filenames in os.walk(transcripts_dir, onerror=_on_walk_error, followlinks=False):
   238	        for fname in filenames:
   239	            if fname.endswith(".jsonl"):
   240	                matched = [t for t in uniq if fname.startswith(t)]
   241	                candidate = os.path.join(dirpath, fname)
   242	                # 候选一律入 all_candidate_paths（保护集口径），再谈可用性
   243	                all_candidates.append(candidate)
   244	                if not matched:
   245	                    continue
   246	                try:
   247	                    if os.path.islink(candidate) or not os.path.isfile(candidate):
   248	                        continue
   249	                except OSError as e:
   250	                    stat_failures.append(f"{candidate}: {e}")
   251	                    continue
   252	                if not os.access(candidate, os.R_OK):
   253	                    unreadable.append(candidate)
   254	                    continue
   255	                if not _path_is_within(candidate, root_str):
   256	                    continue  # 目录 symlink 逃逸（inode 身份判定）
   257	                for t in matched:
   258	                    per_token[t].append(candidate)
   259	    result["all_candidate_paths"] = sorted(set(all_candidates))
   260	
   261	    # round-8 HIGH 整改: 早退分支也必须携带扫描错误 —— 否则 no_token /
   262	    # token_conflict 组的 walk 错误不会进入 scan_blocked 判定。
   263	    if walk_errors:
   264	        result["scan_errors"] = walk_errors[:5]
   265	    if stat_failures:
   266	        result["stat_failures"] = stat_failures[:5]
   267	
   268	    if not uniq:
   269	        # 无 token: 未做任何归因扫描 —— 不是"确认无源"（round-5 MEDIUM 整改）
   270	        result["attribution_conflict"] = True
   271	        result["no_token"] = True
   272	        return result
   273	
   274	    longest = uniq[-1]
   275	    if any(not longest.startswith(t) for t in uniq[:-1]):
   276	        result["attribution_conflict"] = True
   277	        result["token_conflict"] = True
   278	        return result
   279	    result["session_token"] = longest
   280	
   281	    if walk_errors:
   282	        result["scan_errors"] = walk_errors[:5]
   283	        result["attribution_conflict"] = True
   284	        return result
   285	    if stat_failures:
   286	        result["stat_failures"] = stat_failures[:5]
   287	        result["attribution_conflict"] = True
   288	        return result
   289	    if unreadable:
   290	        result["unreadable_candidates"] = unreadable[:5]
   291	        result["attribution_conflict"] = True
   292	        return result
   293	
   294	    matches = sorted(set(per_token[longest]))
   295	    result["transcript_paths"] = matches
   296	    result["transcript_match_count"] = len(matches)
   297	    if len(matches) == 1:
   298	        result["transcript_exists"] = True
   299	    elif len(matches) > 1:
   300	        result["attribution_conflict"] = True  # ambiguous 多命中，拒绝采信
   301	    return result
   302	
   303	
   304	def probe_qa_metrics(db_path: Path, error_types: list[str]) -> tuple[dict, tuple[int, int] | None]:
   305	    """只读核销 qa_metrics.db。返回 (结果, 实际读取对象身份)。
   306	
   307	    round-8 BLOCKER①② 整改: 不再让 SQLite 按 **路径** 打开 —— 那既有 URI 转义
   308	    问题（路径含 ``?``/``#`` 时 ``mode=ro`` 会落进被忽略的 fragment，SQLite 可能
   309	    按默认读写模式打开），又有 A→B→A 的 ABA（验证 fd 是 A，connection 却可能读
   310	    到 B）。改为从**已验证的 fd** 读全量字节 → ``sqlite3`` 内存库
   311	    ``deserialize``：全程不经路径、不落任何文件，两个问题一并消失。
   312	    """
   313	    result: dict = {"db_path": str(db_path), "opened_readonly": False}
   314	    if not db_path.exists():
   315	        result["verdict"] = "db_missing"
   316	        return result, None
   317	    try:
   318	        fd = os.open(db_path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
   319	    except OSError as e:
   320	        result["verdict"] = f"open_refused: {e}"
   321	        return result, None
   322	    try:
   323	        st = os.fstat(fd)
   324	        if not stat.S_ISREG(st.st_mode):
   325	            result["verdict"] = "not_regular_file_refused"
   326	            return result, None
   327	        identity = (st.st_dev, st.st_ino)
   328	        chunks = []
   329	        while True:
   330	            block = os.read(fd, 1 << 20)
   331	            if not block:
   332	                break
   333	            chunks.append(block)
   334	        db_bytes = b"".join(chunks)
   335	        result["bytes_read_from_verified_fd"] = len(db_bytes)
   336	    finally:
   337	        os.close(fd)
   338	
   339	    conn = None
   340	    try:
   341	        conn = sqlite3.connect(":memory:")
   342	        conn.deserialize(db_bytes)
   343	    except Exception as e:  # noqa: BLE001 — 非法/加密 DB 如实记录，不中断 census
   344	        result["verdict"] = f"deserialize_failed: {str(e)[:80]}"
   345	        if conn is not None:
   346	            conn.close()
   347	        return result, identity
   348	
   349	    try:
   350	        result["opened_readonly"] = True
   351	        result["file_identity_verified"] = True
   352	        result["read_mode"] = "in_memory_deserialize_from_verified_fd"
   353	        tables = [
   354	            r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
   355	        ]
   356	        result["tables"] = tables
   357	        if "qa_error_logs" in tables:
   358	            total = conn.execute("SELECT COUNT(*) FROM qa_error_logs").fetchone()[0]
   359	            result["qa_error_logs_rows"] = total
   360	            hits = {}
   361	            for et in sorted(set(error_types)):
   362	                hits[et] = conn.execute("SELECT COUNT(*) FROM qa_error_logs WHERE error_type = ?", (et,)).fetchone()[0]
   363	            result["error_type_hits"] = hits
   364	            result["verdict"] = "no_source_rows" if total == 0 else "rows_present_see_hits"
   365	        else:
   366	            result["verdict"] = "qa_error_logs_table_missing"
   367	    finally:
   368	        conn.close()
   369	    return result, identity
   370	
   371	
   372	def snapshot_file(path: Path) -> tuple[bytes, dict, tuple[int, int]]:
   373	    """一次性读全量 bytes；sha/行数/身份全部派生自**同一个 fd**。
   374	
   375	    round-4 BLOCKER② 整改: 原实现按路径 stat 采集保护身份、稍后才按路径读取，

exec
/bin/zsh -lc "nl -ba backend/scripts/census_dead_letter_episodes.py | sed -n '785,849p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
   785	
   786	    try:
   787	        out_json = json.dumps(ledger, ensure_ascii=False, indent=1)
   788	        out_json.encode("utf-8")  # round-7 LOW: 编码错误必须在写出前暴露
   789	    except (UnicodeEncodeError, ValueError):
   790	        # name/error/group_id 等字段若含 escaped lone surrogate，UTF-8 写出会抛错。
   791	        # 回退 ensure_ascii=True（\uXXXX 转义，ASCII 安全）并在台账显式标注。
   792	        ledger["json_encoding_note"] = "ensure_ascii=True fallback: 某字段含无法 UTF-8 编码的字符（lone surrogate）"
   793	        out_json = json.dumps(ledger, ensure_ascii=True, indent=1)
   794	    if args.out:
   795	        # round-7 架构整改: 不再截断既有文件 —— 同目录 O_EXCL 新建临时文件 →
   796	        # 写 → fsync → os.replace 原子替换。O_EXCL 保证目标是本进程新建的对象，
   797	        # 因此"把 --out 换成指向恢复源的 hardlink / 父目录 symlink / 大小写别名"
   798	        # 这一整类绕过全部失效（脚本从不 ftruncate 任何既有 inode）；同时消除
   799	        # 崩溃/ENOSPC 留下部分台账的风险（round-7 MEDIUM）。
   800	        out_path = Path(args.out)
   801	        tmp_path = out_path.with_name(f".{out_path.name}.census-tmp-{os.getpid()}")
   802	        try:
   803	            tmp_fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
   804	        except OSError as e:
   805	            print(f"临时台账文件无法新建（O_EXCL）: {tmp_path} ({e})", file=sys.stderr)
   806	            return 2
   807	        try:
   808	            with os.fdopen(tmp_fd, "w", encoding="utf-8", closefd=False) as f:
   809	                f.write(out_json + "\n")
   810	                f.flush()
   811	                os.fsync(tmp_fd)
   812	        except Exception as e:
   813	            os.close(tmp_fd)
   814	            os.unlink(tmp_path)
   815	            print(f"台账写入失败，已清理临时文件: {e}", file=sys.stderr)
   816	            return 2
   817	        os.close(tmp_fd)
   818	        # 原子替换 + 父目录 fsync（round-8 MEDIUM 整改：replace 纳入 try，
   819	        # EXDEV/EBUSY/EACCES/ENOSPC 等异常一律清理 tmp 不留残留）。
   820	        try:
   821	            os.replace(tmp_path, out_path)
   822	            dir_fd = os.open(out_path.parent, os.O_RDONLY)
   823	            try:
   824	                os.fsync(dir_fd)
   825	            finally:
   826	                os.close(dir_fd)
   827	        except OSError as e:
   828	            try:
   829	                os.unlink(tmp_path)
   830	            except OSError:
   831	                pass
   832	            print(f"台账原子替换失败，已清理临时文件: {e}", file=sys.stderr)
   833	            return 2
   834	        print(f"台账已写入: {args.out}")
   835	    else:
   836	        print(out_json)
   837	
   838	    print(
   839	        f"census: {len(records)} 条 (+{len(unparseable)} unparseable) | class={dict(class_dist)} | "
   840	        f"recoverability={dict(recover_dist)} | 归因冲突={len(attribution_conflicts)} | "
   841	        f"重复簇={len(duplicate_clusters)} | 偏差={deviation or '无'} | "
   842	        f"qa_metrics 核销={qa_probe.get('verdict')}",
   843	        file=sys.stderr,
   844	    )
   845	    return 0
   846	
   847	
   848	if __name__ == "__main__":
   849	    sys.exit(main())

exec
/bin/zsh -lc "nl -ba backend/scripts/census_dead_letter_episodes.py | sed -n '416,520p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
   416	def main(argv: list[str] | None = None) -> int:
   417	    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
   418	    ap.add_argument(
   419	        "--dlq",
   420	        default="data/dead_letter_episodes.jsonl",
   421	        help="DLQ JSONL 路径（census 对 live 挂载运行时传绝对路径）",
   422	    )
   423	    ap.add_argument(
   424	        "--qa-metrics-db",
   425	        default=None,
   426	        help="qa_metrics.db 路径（省略则跳过源指针核销并如实标注 skipped）",
   427	    )
   428	    ap.add_argument(
   429	        "--transcripts-dir",
   430	        default=os.path.expanduser("~/.claude/projects"),
   431	        help="session transcript 根目录（近似恢复源指针核销；不存在则 exit 2 拒诊）",
   432	    )
   433	    ap.add_argument(
   434	        "--compare",
   435	        action="append",
   436	        default=[],
   437	        help="其它 DLQ 副本路径（可重复，产出 sha 对照表）",
   438	    )
   439	    ap.add_argument("--out", default=None, help="台账 JSON 输出路径（省略则打 stdout）")
   440	    args = ap.parse_args(argv)
   441	
   442	    dlq_path = Path(args.dlq)
   443	    if not dlq_path.exists():
   444	        print(f"DLQ 文件不存在: {dlq_path}", file=sys.stderr)
   445	        return 2
   446	
   447	    transcripts_dir = Path(args.transcripts_dir)
   448	    if not transcripts_dir.is_dir():
   449	        print(
   450	            f"transcripts 根目录不存在/不可见: {transcripts_dir} —— 拒绝在源不可见时裁定可恢复性（fail-closed）",
   451	            file=sys.stderr,
   452	        )
   453	        return 2
   454	    # round-2 HIGH-3 整改: 存在但不可读/不可遍历的根（chmod 000）此前 exit 0
   455	    # 并把全部记录假判 unrecoverable —— 同样 fail-closed 拒诊。
   456	    if not os.access(transcripts_dir, os.R_OK | os.X_OK):
   457	        print(
   458	            f"transcripts 根目录不可读/不可遍历: {transcripts_dir} —— 拒绝在源不可见时裁定可恢复性（fail-closed）",
   459	            file=sys.stderr,
   460	        )
   461	        return 2
   462	
   463	    protected_ids: set[tuple[int, int]] = set()
   464	    # round-6 BLOCKER①② 架构整改: inode 保护集依赖**枚举完整性**（不可列举的
   465	    # 子目录、ABA 换 inode 都能让某个真实源不进集合）。故增加**不依赖枚举**的
   466	    # 路径层防御：--out 的 realpath 不得落在 transcripts 根内、不得等于任一
   467	    # 输入路径。路径层 + inode 层双保险，任一命中即拒绝。
   468	    if args.out:
   469	        # round-7 BLOCKER 整改: 用 **inode 身份逐级比较**（_path_is_within），
   470	        # 不用路径字符串前缀 —— normcase 在 POSIX 上是恒等函数，大小写不敏感
   471	        # 卷上的别名根（/Users vs /users）realpath 字符串不同但 samefile=True。
   472	        # round-8 BLOCKER③ 整改: rename/replace **不解析末级 symlink**（POSIX），
   473	        # 故 --out 若是根内的 symlink（指向根外），realpath 会判"根外"而放行，
   474	        # 但 replace 实际替换的是根内那个目录项。判定改用**父目录**语义 +
   475	        # lstat 末级：父目录在根内 → 拒绝；末级本身是 symlink 也按其所在目录判。
   476	        out_parent = os.path.dirname(os.path.abspath(args.out)) or "."
   477	        if _path_is_within(out_parent, args.transcripts_dir) or _path_is_within(args.out, args.transcripts_dir):
   478	            print(
   479	                f"--out 落在 transcripts 根内（恢复源区域），无条件拒绝写出: {args.out}",
   480	                file=sys.stderr,
   481	            )
   482	            return 2
   483	        input_paths = [args.dlq, *args.compare] + ([args.qa_metrics_db] if args.qa_metrics_db else [])
   484	        if any(_same_file(args.out, ip) for ip in input_paths):
   485	            print(f"--out 与输入文件为同一对象（inode 比较），拒绝写出: {args.out}", file=sys.stderr)
   486	            return 2
   487	
   488	    # --out 碰撞守卫（写前）。round-2 BLOCKER-1 整改: 比较**文件身份**
   489	    # (st_dev, st_ino) 而非 resolve() 字符串 —— 后者对 hardlink 与
   490	    # 大小写不敏感文件系统上的 case-only 别名均失效（Codex 实测截断输入）。
   491	    if args.out:
   492	        out_path = Path(args.out)
   493	        protected_paths = [dlq_path, *(Path(p) for p in args.compare)]
   494	        if args.qa_metrics_db:
   495	            protected_paths.append(Path(args.qa_metrics_db))
   496	        for candidate in protected_paths:
   497	            try:
   498	                cst = candidate.stat()  # 跟随 symlink: 保护的是最终目标身份
   499	                protected_ids.add((cst.st_dev, cst.st_ino))
   500	            except OSError:
   501	                # round-4 整改: stat 失败不再静默吞 —— 无法确认身份即 fail-closed
   502	                print(f"输入文件无法 stat，拒绝继续（无法建立完整保护集）: {candidate}", file=sys.stderr)
   503	                return 2
   504	        # 路径字符串比较作为第二道（输出文件尚不存在时 stat 无身份可比）
   505	        out_resolved = out_path.resolve()
   506	        if out_resolved in {p.resolve() for p in protected_paths}:
   507	            print(f"--out 与输入文件路径重合，拒绝写出（防截断）: {out_resolved}", file=sys.stderr)
   508	            return 2
   509	        if out_path.exists():
   510	            try:
   511	                out_st = out_path.stat()
   512	            except OSError as e:
   513	                print(f"--out 无法 stat，拒绝写出: {out_path} ({e})", file=sys.stderr)
   514	                return 2
   515	            if (out_st.st_dev, out_st.st_ino) in protected_ids:
   516	                print(
   517	                    f"--out 与输入文件为同一 inode（hardlink/大小写别名），拒绝写出（防截断）: {out_path}",
   518	                    file=sys.stderr,
   519	                )
   520	                return 2

**Analyzing memory risk in probe_qa_metrics**
**Investigating SQLite deserialize memory limits**
**Assessing directory fd consistency after replace**
**Identifying atomic replace fsync failure risk**
**Clarifying post-publish fsync error semantics**
**Identifying residual temp file race risk**
**Reviewing prior tmp race severity classification**
**Clarifying tmp filename risk under O_EXCL**
**Analyzing concurrency risks with temp files**
**Tracing path validation and mount point checks**
**Identifying lexical path check limitations with bind mounts**
**Analyzing mount alias and bind mount impacts**
**Evaluating mount alias path traversal risks**
**Assessing realpath behavior with symlink loops**
**Analyzing TOCTOU risks in root containment checks**
**Planning read-only in-memory testing approach**
**Planning read-only ledger parsing**
**Planning safe ledger and DB inspection**
**Initiating ledger query for metrics**
**Planning file comparison and summary extraction**
exec
/bin/zsh -lc "jq '{generated_at, dlq_file, total_lines,total_records,unparseable_lines,class_distribution,recoverability_distribution,inline_state_distribution, attribution_conflict_count:(.attribution_conflicts|length), attribution_reason_counts:(.records|map(select(.attribution_conflict))|group_by(.attribution_conflict_reason)|map({reason:.[0].attribution_conflict_reason,count:length})),duplicate_cluster_count:(.duplicate_clusters|length), duplicate_occurrence_sum:(.duplicate_clusters|map(.occurrences)|add), duplicate_sizes:(.duplicate_clusters|map(.occurrences)),qa_metrics_probe}' '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
{
  "generated_at": "2026-08-28T13:35:50.981742+00:00",
  "dlq_file": {
    "path": "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl",
    "exists": true,
    "line_count": 92,
    "sha256": "3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590",
    "mtime_utc": "2026-08-11T14:01:25.808462+00:00",
    "mtime_note": "mtime 取自读取用 fd 的 fstat；绑定 exact bytes 的是 sha256"
  },
  "total_lines": 92,
  "total_records": 92,
  "unparseable_lines": [],
  "class_distribution": {
    "budget_400": 89,
    "schema_entity_type": 2,
    "group_id_format": 1,
    "unexpected": 0
  },
  "recoverability_distribution": {
    "byte_exact": 4,
    "approximate": 88,
    "unverifiable": 0,
    "unrecoverable": 0
  },
  "inline_state_distribution": {
    "full_verified": 4,
    "truncated_prefix": 88,
    "anomaly": 0
  },
  "attribution_conflict_count": 3,
  "attribution_reason_counts": [
    {
      "reason": "no_token",
      "count": 3
    }
  ],
  "duplicate_cluster_count": 6,
  "duplicate_occurrence_sum": 29,
  "duplicate_sizes": [
    16,
    4,
    3,
    2,
    2,
    2
  ],
  "qa_metrics_probe": {
    "db_path": "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db",
    "opened_readonly": true,
    "bytes_read_from_verified_fd": 16384,
    "file_identity_verified": true,
    "read_mode": "in_memory_deserialize_from_verified_fd",
    "tables": [
      "qa_error_logs"
    ],
    "qa_error_logs_rows": 0,
    "error_type_hits": {
      "BadRequestError": 0,
      "EntityTypeValidationError": 0,
      "GroupIdValidationError": 0
    },
    "verdict": "no_source_rows"
  }
}

exec
/bin/zsh -lc "stat -f 'ledger mode=%Lp size=%z nlink=%l inode=%i' '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json'; find . -name '*.census-tmp-*' -print; git rev-parse 'af251e4a:_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json'; git rev-parse 'HEAD:_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json'; git rev-parse 'af251e4a:backend/scripts/census_dead_letter_episodes.py'; git rev-parse 'HEAD:backend/scripts/census_dead_letter_episodes.py'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 963ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
43eb4b7a8b05ed04b1f4df0584f6770cb533c82b
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
43eb4b7a8b05ed04b1f4df0584f6770cb533c82b
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
957529ec13afde86039db95a0a0622ea691f7f23
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
957529ec13afde86039db95a0a0622ea691f7f23

**Designing independent ledger recomputation**
**Planning read-only ledger parsing script**
**Inspecting classification function logic**
exec
/bin/zsh -lc "nl -ba backend/scripts/census_dead_letter_episodes.py | sed -n '130,205p'; nl -ba backend/scripts/census_dead_letter_episodes.py | sed -n '520,580p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
   130	        except UnicodeDecodeError as e:
   131	            out.append(("", f"utf8_decode_error: {e}"))
   132	    return out
   133	
   134	
   135	def classify(rec: dict) -> str:
   136	    et = rec.get("error_type", "")
   137	    if not isinstance(et, str):
   138	        return "unexpected"
   139	    if et == "EntityTypeValidationError":
   140	        return "schema_entity_type"
   141	    if et == "GroupIdValidationError":
   142	        return "group_id_format"
   143	    if et == "BadRequestError" and _BUDGET_PAT.search(str(rec.get("error", ""))):
   144	        return "budget_400"
   145	    return "unexpected"
   146	
   147	
   148	def inline_state(rec: dict) -> tuple[str, str]:
   149	    """返回 (inline_state, sha_check)，fail-closed（见模块 docstring）。"""
   150	    body = rec.get("episode_body", "")
   151	    if not isinstance(body, str):  # round-4 LOW: episode_body 错型
   152	        return "anomaly", "FAIL"
   153	    declared_len = rec.get("episode_body_length")
   154	    declared_sha = rec.get("episode_body_sha256", "")
   155	    sha_wellformed = isinstance(declared_sha, str) and bool(_SHA256_HEX_PAT.match(declared_sha))
   156	    # round-5 LOW 整改: errors="replace" 会把 JSON escaped lone surrogate
   157	    # (\udXXX) 改写成 replacement char，可被构造出"对得上账"的假 full_verified。
   158	    # 改 strict：无法编码即判 anomaly。
   159	    try:
   160	        body_bytes = body.encode("utf-8")
   161	    except UnicodeEncodeError:
   162	        return "anomaly", "FAIL"
   163	    recomputed = hashlib.sha256(body_bytes).hexdigest()
   164	    len_ok = isinstance(declared_len, int) and not isinstance(declared_len, bool)
   165	    if sha_wellformed and recomputed == declared_sha and len_ok and len(body) == declared_len:
   166	        return "full_verified", "pass"
   167	    if sha_wellformed and len(body) == 200 and len_ok and declared_len > 200:
   168	        return "truncated_prefix", "prefix_only"
   169	    return "anomaly", "FAIL"
   170	
   171	
   172	def full_body_verified(rec: dict) -> bool:
   173	    """episode_body_full 在盘且 sha **与长度**双门对账通过（生产 opt-in 字段，当前 live 0 条）。
   174	
   175	    round-2 HIGH-1 整改: 原实现只核 sha，声明长度矛盾的记录（如 body="abc"
   176	    但 episode_body_length=999）仍被判 byte_exact —— 与 inline 侧同门收紧。
   177	    """
   178	    full = rec.get("episode_body_full")
   179	    declared_sha = rec.get("episode_body_sha256", "")
   180	    declared_len = rec.get("episode_body_length")
   181	    if not isinstance(full, str) or not _SHA256_HEX_PAT.match(str(declared_sha)):
   182	        return False
   183	    # round-5 LOW 整改: bool 是 int 子类 —— episode_body_length=True 会通过长度门
   184	    if not isinstance(declared_len, int) or isinstance(declared_len, bool) or len(full) != declared_len:
   185	        return False
   186	    try:
   187	        full_bytes = full.encode("utf-8")
   188	    except UnicodeEncodeError:
   189	        return False
   190	    return hashlib.sha256(full_bytes).hexdigest() == declared_sha
   191	
   192	
   193	def session_tokens(name: object) -> list[str]:
   194	    """round-4 LOW 整改: name 非 str（None/数字/列表）不再抛异常。"""
   195	    if not isinstance(name, str):
   196	        return []
   197	    tokens = []
   198	    m = _SESSION_ARCHIVE_PAT.match(name)
   199	    if m:
   200	        tokens.append(m.group(1).lower())
   201	    tokens.extend(t.lower() for t in _SESSION_INLINE_PAT.findall(name))
   202	    return tokens
   203	
   204	
   205	def resolve_group_attribution(tokens: list[str], transcripts_dir: Path) -> dict:
   520	                return 2
   521	
   522	    # BLOCKER-2 整改: 单次读取，records 与头部描述共享同一份 exact bytes
   523	    try:
   524	        raw_bytes, dlq_info, dlq_identity = snapshot_file(dlq_path)
   525	    except OSError as e:
   526	        print(f"DLQ 无法安全读取: {dlq_path} ({e})", file=sys.stderr)
   527	        return 2
   528	    protected_ids.add(dlq_identity)  # 保护的是**实际读取对象**，非路径快照
   529	    raw_lines = _split_jsonl_lines(raw_bytes)
   530	
   531	    records: list[tuple[int, dict]] = []
   532	    unparseable: list[dict] = []
   533	    for line_no, (line, decode_err) in enumerate(raw_lines, start=1):
   534	        if decode_err is not None:
   535	            unparseable.append({"line_no": line_no, "reason": decode_err})
   536	            continue
   537	        if not line.strip():
   538	            unparseable.append({"line_no": line_no, "reason": "blank_line"})
   539	            continue
   540	        try:
   541	            rec = json.loads(line)
   542	        except json.JSONDecodeError as e:
   543	            unparseable.append({"line_no": line_no, "reason": f"json_error: {e}", "excerpt": line[:80]})
   544	            continue
   545	        # round-3 LOW 整改: 合法 JSON 但非对象（null / 数组 / 标量）此前解析成功
   546	        # 却在 rec.get() 处抛 AttributeError 炸掉全量 —— 归入 unparseable。
   547	        if not isinstance(rec, dict):
   548	            unparseable.append(
   549	                {"line_no": line_no, "reason": f"not_a_json_object: {type(rec).__name__}", "excerpt": line[:80]}
   550	            )
   551	            continue
   552	        records.append((line_no, rec))
   553	
   554	    # request_id 分组: (类型名, 值) 复合键；缺失/None → 按 line_no 单条成组
   555	    groups: dict[tuple, list[tuple[int, dict]]] = defaultdict(list)
   556	    for line_no, rec in records:
   557	        rid = rec.get("request_id")
   558	        # round-4 LOW 整改: 不可哈希的 request_id（list/dict）按 line_no 单条成组
   559	        try:
   560	            hash(rid)
   561	            hashable = True
   562	        except TypeError:
   563	            hashable = False
   564	        key = ("__missing__", line_no) if (rid is None or not hashable) else (type(rid).__name__, rid)
   565	        groups[key].append((line_no, rec))
   566	    group_attribution: dict[tuple, dict] = {}
   567	    for key, members in groups.items():
   568	        tokens: list[str] = []
   569	        for _, rec in members:
   570	            tokens.extend(session_tokens(rec.get("name", "")))
   571	        group_attribution[key] = resolve_group_attribution(tokens, transcripts_dir)
   572	
   573	    ledger_records = []
   574	    class_dist: Counter = Counter()
   575	    recover_dist: Counter = Counter()
   576	    inline_dist: Counter = Counter()
   577	    unrecoverable_keys = []
   578	    unverifiable_keys = []
   579	    attribution_conflicts = []
   580	    for line_no, rec in records:

**Planning ledger and UAT verification**
exec
/bin/zsh -lc "rg -n -C 3 '纯只读|唯一写|TOCTOU|只写|read_mode|bytes_read|安全|验收|92 条冻结|round-8' '_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md' '_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md' '_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt-13-5b371253  CARD-G4-9 round-6 架构级修复
_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt-14-4ba4f847  receipt 补 round-5/6 链
_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt-15-f389980c  CARD-G4-9 round-7 架构级修复（消除截断动作）
_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt:16:af251e4a  CARD-G4-9 round-8 整改（QA DB 内存 deserialize / 父目录 containment / stdout 门 / 原子替换清理）
_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt-17-
_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt-18-各阶段交付物 blob 可用 git cat-file 复核；台账头部 dlq_file.sha256 为 DLQ 快照指纹。
--
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-37-| Codex 复审 round-2 | **仍阻断**（10/13 CLOSED；BLOCKER-1/HIGH-1/HIGH-3 未真正闭合 + 3 新 LOW）。同时独立复算确认：67ccebe1 冻结生效、92 条数字与 6/29 重复簇全部可复算 | `_bmad-output/审查/codex-review-CARD-G4-9-round2.md`（codex 被 cyber 误拦，内容由 stdout 抢救存档） |
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-38-| round-2 findings 逐条整改 | **6/6 完成**：inode 身份守卫封 hardlink+大小写别名 / full_body 长度门+anomaly 前置 / 不可读根 exit 2+symlink 逃逸拒采信 / 3 新 LOW。5 条新负例实测全过、正例无回归、数字仍逐项一致 | 报告 §7/§7c + `grep-selfattest.txt` |
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-39-| Codex 复审 round-3 | **仍阻断**（4/6 CLOSED；BLOCKER-1/HIGH-3 判 PARTIAL + 1 新 MEDIUM + 2 新 LOW）。同时确认：HIGH-1 与三条 LOW 已闭合、台账数字有效且与 commit 字节一致 | `_bmad-output/审查/codex-review-CARD-G4-9-round3.md` |
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:40:| round-3 findings 逐条整改 | **6/6 完成**：transcript 并入保护集 / O_NOFOLLOW+fstat 消 TOCTOU / os.walk 替 glob（不跟随目录 symlink+遍历错误显式捕获）/ 不可读候选 fail-closed / JSONL 严格 LF 分帧 / 非 dict 归 unparseable。6 条新反例实测全过、数字第三次不变 | 报告 §7d + `grep-selfattest.txt` |
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-41-| Codex 复审 round-4 | **仍阻断**（1/6 CLOSED；2 新 BLOCKER + 1 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round4.md` |
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:42:| round-4 findings 逐条整改 | **9/9 完成**：全候选入保护集 / 读侧 fd 身份消源侧 TOCTOU / 新增 unverifiable 第四态 / FIFO 设备门 / strict UTF-8 / 3 条错型与边界 LOW / provenance receipt。5 条新反例实测全过；第四次全量重跑数字仍不变 | 报告 §7e + `grep-selfattest.txt` |
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-43-| Codex 复审 round-5 | **仍阻断**（3/8 CLOSED；2 BLOCKER + 2 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round5.md` |
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-44-| round-5 findings 逐条整改 | **9/9 完成**：先扫描后判定（冲突候选亦入保护集）/ QA DB fd 身份+复核 / 可见性优先于 anomaly / fchmod 后置于碰撞检查 / QA DB 特殊文件门 / no_token 归 unverifiable / 3 条 LOW。6 条新反例实测全过；第五次全量重跑数字仍不变 | 报告 §7f |
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-45-| Codex 复审 round-6 | **6/9 CLOSED**（visibility 优先/fchmod 顺序/no_token 语义/3 条 LOW 已闭合）；剩 2 BLOCKER + 1 MEDIUM 揭示保护集**依赖枚举完整性**的架构缺陷 + 3 新发现 | `_bmad-output/审查/codex-review-CARD-G4-9-round6.md` |
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-46-| round-6 findings 整改 | **架构级修复 + 6 项**：新增不依赖枚举的**路径层防御**（--out 禁落 transcripts 根内 / 禁等于任一输入 realpath）、QA DB 验证 fd 保持打开至复核完毕、no_token 亦扫描、证据包重生成、ledger 冲突原因自描述、lone surrogate 回退。反例实测：0333 隐藏目录内 transcript 作 --out → exit 2 完好 | 报告 §7g |
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:47:| Codex 复审 round-7 | **关键裁定分离**："92 条冻结 ledger **可以采信**；生成器与 UAT 的纯只读安全声明不可验收"——卡面 census 判据已满足，阻断全在工具安全承诺侧。1 BLOCKER（大小写别名根，无需竞态）+ 4 项路径 TOCTOU + 1 MEDIUM（非原子写）+ 2 LOW | `_bmad-output/审查/codex-review-CARD-G4-9-round7.md` |
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-48-| round-7 findings 整改 | **架构级第二次修复**：写出改 O_EXCL 临时文件+fsync+os.replace（**全文再无 ftruncate 调用**），五项绕过整类失效；containment 改 inode 逐级比较（normcase 在 POSIX 是恒等函数，我的假设错了）；扫描受阻直接拒绝写出。实测：根外 hardlink 指向根内 transcript 作 --out → 源内容完好 | 报告 §7h |
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:49:| Codex 复审 round-8 | 重申裁定分离：**「可验收：92 条冻结 ledger snapshot；不可验收：生成器一般安全性与 UAT 的纯只读声明」**。3 新 BLOCKER（SQLite URI 未转义 #/? / QA DB 仍按 pathname 开可 ABA / 根内末级 symlink 因 rename 不解析而被替换）+ 1 HIGH + 1 MEDIUM | `_bmad-output/审查/codex-review-CARD-G4-9-round8.md` |
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:50:| round-8 findings 整改 | **6/6 完成**：QA DB 改「已验证 fd 读字节 → 内存库 deserialize」（URI 转义与 ABA 一并消失，含 #? 路径实测通过）；containment 加父目录语义（POSIX rename 不解析末级 symlink）；扫描受阻去掉 and args.out（stdout 模式亦拒）；replace 纳入 try + fsync 父目录 | 报告 §7i |
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-51-| 独立 Workflow 4-agent 复核 | G4-9 数字 agent：92 条重算 **0 mismatch**（class/inline/三态/25 request_id/7 transcript 在盘/台账 sha 全 CONFIRMED，仅 2 处描述区间 REFUTED 已修正）；只读契约 agent：与 Codex 同源的 3 条 blocker（已随上整改） | Workflow wf_737b1a95-20b journal |
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-52-
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-53-## 🔧 Codex round-1 整改记录（13/13 关闭，BLOCKED → 整改完毕）
--
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-76-
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-77-## 🔧 Codex round-3 复审整改记录（4/6 CLOSED → 剩 2 项 + 3 新发现全关闭）
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-78-
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:79:round-3 确认 HIGH-1 与三条 LOW 真正闭合、台账数字有效，又在两项路径安全上找到更深的绕过：
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-80-
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:81:- **BLOCKER-1 仍 PARTIAL**：① 保护集漏了**归因到的 transcript**——`--out` 指向它会截断恢复源；② check-then-open 的 **TOCTOU** 仍在。→ ① transcript 写前并入保护集；② 改 `O_NOFOLLOW` 打开且**不带 O_TRUNC**，对实际 fd `fstat` 校验后才 `ftruncate`。反例实测：exit 2、transcript 完好。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-82-- **HIGH-3 仍 PARTIAL**：Python 3.14 的 `glob` 在过滤前就已递归、跟随目录 symlink 且**静默吞掉不可读子树错误**；mode 000 的文件仍过 `isfile()` 被当可用源。→ 改 `os.walk(onerror=, followlinks=False)` + `os.access(R_OK)` 门；遍历受阻或有不可读候选一律拒绝裁定。三反例实测 fail-closed。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-83-- **新 MEDIUM（JSONL 分帧）**：`splitlines()` 会把含 U+2028 的合法单行记录劈成两条坏行。→ 严格按 LF 分帧，header 与 records 共用同一函数。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-84-- **新 LOW ×2**：非 dict JSON（`null`/数组）归 unparseable 不再炸全量；报告头补 artifact commit 链。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-85-
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:86:round-3 整改后第三次全量重跑：**92 条、4/88/0、89/2/1、6/29、shasum 不变——三轮整改数字全程未变**，改的全是通用鲁棒性与路径安全。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-87-
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-88-## 🔧 Codex round-4 复审整改记录（1/6 CLOSED → 9 项全关闭）
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-89-
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-90-round-4 只认 1 项闭合，用更深的反例推翻其余"闭合"——两条新 BLOCKER 都是真的：
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-91-
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-92-- **不可读但可写（mode 0200）的 transcript 绕过保护集**：我在"不可读"分支把候选路径清空了，于是它没进保护集，`--out` 指向它照样截断——不需要任何竞态。→ 新增"全候选清单"，无论可读与否一律并入保护集。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:93:- **源侧 TOCTOU**：保护身份按路径 stat 采集、DLQ 稍后才按路径读取，中间可换 inode。→ 改为**从 fd 读取**：打开一次 → `fstat` 取身份 → 从同一 fd 读全量，保护的就是实际读到的那个对象。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-94-- **把"看不见"说成"不可恢复"**：扫描受阻时仍输出 `unrecoverable`，与报告里"既不宣称不可恢复"自相矛盾。→ 新增第四态 **`unverifiable`**，逐条写明是遍历受阻还是候选不可读。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-95-- **其余 5 项**：FIFO/设备节点门（`O_NONBLOCK`+`S_ISREG`）、非法 UTF-8 不再经 replace 冒充有效记录（strict decode）、三条错型与边界 LOW（`name=None`/`request_id=[]`/根为 `/`）、既有输出文件 `fchmod` 收紧（台账现为 `-rw-------`）、provenance 改后置 receipt 绑定精确 commit 链。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-96-
--
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-124-
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-125-round-7 把结论分成了两半，这个区分很重要：
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-126-
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:127:> **「现有 92 条冻结 ledger 可以采信；生成器与 UAT 的纯只读安全声明不可验收。」**
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-128-
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-129-也就是说：这张卡要交付的 census 结论（92 条的分类、对账、三态、挂载真相、稳定键、运行零写入）**已经过关**；卡住的是"这个脚本作为工具，其只读承诺是否经得起敌意输入"。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-130-
--
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-134-
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-135-round-7 整改后第七次全量重跑：**92 条、4/88/0/0、89/2/1、6/29、shasum 不变、台账 0600、无临时文件残留——七轮整改数字全程未变**。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-136-
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:137:## 🔧 Codex round-8 复审整改记录（裁定分离重申 + 3 BLOCKER 全闭）
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-138-
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:139:round-8 把结论说得更清楚了：**「可验收：92 条冻结 ledger snapshot。不可验收：生成器的一般安全性，以及验收单里那句"纯只读、唯一写出口、整类 TOCTOU 已消失"」**。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-140-
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-141-三条新 BLOCKER 都成立，其中两条有同一个彻底解法：
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-142-
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:143:- **SQLite 打开方式**：`file:路径?mode=ro` 这种写法，路径里只要有个 `#`，`mode=ro` 就掉进 URI 的 fragment 被忽略，SQLite 可能按默认的**读写模式**打开——这直接推翻"唯一写出口"。而且就算持有验证过的文件描述符，SQLite 还是按路径自己去开，中间被换掉也发现不了。→ 改成从**已验证的文件描述符读出全部字节，灌进内存数据库**。SQLite 从此不碰路径，两个问题一起消失。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-144-- **根内的软链接**：POSIX 规定重命名操作**不跟随末级软链接**。所以 `--out` 如果是恢复源目录里的一个软链接（指向外面），我按"它指向哪"判断会放行，但实际被替换的是**目录里那个链接本身**。→ 判定改看**父目录在不在恢复源里**。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-145-- **stdout 模式漏网**：扫描受阻的拒绝条件我写成了"且指定了 --out"，于是省略 `--out` 就能绕过。→ 去掉该条件。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-146-
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:147:round-8 整改后第八次全量重跑：**92 条、4/88/0/0、89/2/1、6/29、shasum 不变、无 tmp 残留——八轮整改数字全程未变**。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-148-
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-149-## 📄 交付物清单（全部新增，零业务代码改动）
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md-150-
--
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-1-# CARD-G4-9 — DLQ 真实挂载 census 分诊报告
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-2-
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-3-> **批次**: BATCH-2026-08-28-第五批 / CARD-G4-9（4h · wave 1 · 未来铺路）
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:4:> **性质**: 纯只读 census。0 写入、0 重放、0 业务代码改动。唯一代码产物 = `backend/scripts/census_dead_letter_episodes.py`。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-5-> **代码基线**: 分析对象锚定 `37387a86`（第五批开工基线）。**本卡交付物 artifact commit 链**：精确 SHA 逐段记录于 `_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt`（commit 无法自含己身 SHA，故用后置 receipt 绑定——Codex round-4 LOW 整改）
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-6-> **台账**: `_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json`（92 条逐条，G4-10 消费）
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-7-> **证据包**: `_bmad-output/审查/G4-9-evidence/`（shasums before/after、grep 自证、容器内 sha 实测）
--
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-74-
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-75-**不可恢复清单（显式成段）**：本次 census 裁定不可恢复条目 **0 条**；三态裁定覆盖 92/92，**"待定"0 条**。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-76-
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:77:诚实边界：`近似` ≠ 已恢复。88 条的实际重建（含 22 条 session-archive 是否能达字节级）是 G4-10 的工作与验收，本卡只交付"上游源在盘、路径已核销"的证据链。transcript 属用户本机 `~/.claude/projects/` 数据，若未来被清理，近似裁定随之失效——台账已逐条记录 transcript 绝对路径供 G4-10 开工时复核。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-78-
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-79-## §6 台账稳定键（G4-10 交接契约）
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-80-
--
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-138-
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-139-## §7d Codex round-3 复审整改记录（4/6 CLOSED → 剩 2 项 + 3 新发现全部整改）
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-140-
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:141:round-3 确认 HIGH-1 与三条 LOW 已 CLOSED、台账数字有效且与 commit 字节一致，两项路径安全判 PARTIAL：
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-142-
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:143:- **BLOCKER-1 残留两条绕过**：① `protected_paths` 未含**归因到的 transcript**，`--out=<唯一 transcript>` 会截断恢复源；② check-then-open 的 **TOCTOU** 仍在（检查后、打开前把 --out 换成指向 DLQ 的链接）。**整改**：① 写出前把全部 `transcript_paths` 并入保护集；② 改 `os.open(O_WRONLY|O_CREAT|O_NOFOLLOW)` **不带 O_TRUNC** 打开 → 对**实际 fd** `fstat` 校验 inode → 通过才 `ftruncate`，检查与写入作用于同一 fd，替换攻击无效。反例实测：`--out` 指向唯一 transcript → exit 2、transcript sha 不变。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-144-- **HIGH-3 残留**：`glob(recursive=True)` 在 realpath 过滤**之前**已递归遍历（Python 3.14 glob 跟随目录 symlink 且**静默吞掉不可读子树错误**）→ 越根枚举 + "假唯一/假不可恢复"；mode `000` 的 regular transcript 仍过 `isfile()` 被判 approximate。**整改**：改 `os.walk(onerror=..., followlinks=False)`（不跟随目录 symlink、遍历错误显式捕获）+ 候选加 `os.access(R_OK)` 门；遍历受阻或存在不可读候选一律记 `attribution_conflict` 拒绝裁定（既不宣称找到、也不宣称不可恢复）。三条反例实测全部 fail-closed。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-145-- **新 MEDIUM（JSONL framing）**：生产端 `ensure_ascii=False` 可原样写出字符串内的 U+2028，`splitlines()` 会把一条合法单-LF 记录劈成两条坏行。**整改**：新增 `_split_jsonl_lines()` 严格按 LF 分帧，header `line_count` 与 records 共用同一函数。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-146-- **新 LOW（输入 schema）**：合法 JSON 但非对象（`null` / 数组 / 标量）解析成功后在 `rec.get()` 处抛 AttributeError 炸全量。**整改**：非 dict 归 `unparseable`（`not_a_json_object: <type>`），实测两条毒行不影响其余记录。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:147:- **新 LOW（provenance）**：报告头只写起始基线未区分整改 artifact commit —— 已在报告头补三段 commit 链。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-148-
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:149:round-3 整改后第三次全量重跑：92 条、class 89/2/1、三态 4/88/0、重复簇 6/29、shasum 不变——**三轮整改数字全程未变**，改的全是通用鲁棒性与路径安全。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-150-
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-151-## §7e Codex round-4 复审整改记录（1/6 CLOSED → 全部 9 项整改）
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-152-
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-153-round-4 只认可 1 项 CLOSED（非 dict JSON 门），并用更深的静态反例推翻了另外 5 项的"闭合"，另提 2 BLOCKER / 1 HIGH / 2 MEDIUM / 3 LOW。逐条整改（全部实测复现→封死）：
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-154-
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-155-- **BLOCKER①（不可读但可写的 transcript 绕过保护集）**：mode `0200` 的候选在 unreadable 分支被清空 `transcript_paths`，因此不进保护集，`--out` 指向它仍被截断（无需竞态）。**整改**：新增 `all_candidate_paths` 保留**所有见到的候选**（含不可读、含被冲突分支清空的），写出前全部并入保护集。实测：mode 0200 候选作 `--out` → exit 2、文件字节不变。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:156:- **BLOCKER②（源侧 TOCTOU）**：保护身份按**路径** stat 采集、DLQ 稍后才按路径读取，两步间可换入另一 inode → 实际读取对象不在保护集。**整改**：`snapshot_file()` 改为 `os.open(O_RDONLY|O_NOFOLLOW|O_NONBLOCK)` → `fstat` 取身份 + regular-file 门 → **从同一 fd 读全量**，返回的身份即**实际被读取对象**；compare 副本同样以读取身份入保护集；输入 `stat` 失败不再静默吞而是 exit 2。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-157-- **HIGH（不可见被终态化为 unrecoverable）**：扫描受阻/冲突时主链仍产出 `unrecoverable`，与报告"既不宣称不可恢复"自相矛盾。**整改**：引入第四态 **`unverifiable`**（源可见性不足，basis 逐条说明是遍历受阻/不可读候选/归因冲突），distribution 与 `unverifiable_list` 同步。实测：不可读子树 → `unverifiable=1`，不再冒充 unrecoverable。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-158-- **MEDIUM（FIFO/设备节点）**：`--out` 缺 regular-file gate 与 `O_NONBLOCK`。**整改**：`O_NONBLOCK` + `S_ISREG` 双门（读侧同样）。实测：FIFO 作 `--out` → exit 2 且不阻塞。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-159-- **MEDIUM（非法 UTF-8 冒充有效记录）**：`errors="replace"` 把坏字节改写成合法对象。**整改**：`_split_jsonl_lines()` 改**逐行 strict decode**，解码失败归 `unparseable`。实测：`b'{"a":"\xff"}'` → `utf8_decode_error`，records=0。
--
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-196-
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-197-round-7 给出了本卡最重要的一次裁定分离：
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-198-
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:199:> **「现有 92 条冻结 ledger 可以采信；CARD-G4-9 生成器与 UAT 的纯只读安全声明不可验收。」**
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-200-
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:201:即：卡面的 census 判据（分类/对账/三态/挂载真相/稳定键/shasum 不变）已满足且被独立复算确认；阻断项全部落在"生成器作为工具的只读安全承诺"上。逐条整改：
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-202-
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-203-- **BLOCKER（大小写别名根）**：本机实测 `/Users/Heishing/.claude/projects` 与 `/users/heishing/...` `samefile=True` 但 `realpath` 字符串不同，prefix guard 返回 False——**无需竞态的实际绕过**。我 round-6 用的 `os.path.normcase` 在 POSIX 上是**恒等函数**（假设错误）。**整改**：新增 `_path_is_within()`，从目标逐级向上比较 **inode 身份**，完全不依赖路径字符串；`--out` 与输入文件的比较改 `os.path.samefile`。实测：别名根作 `--out` → exit 2，正例无回归。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:204:- **NOT-CLOSED ×4（根外 hardlink 指向隐藏目录内 transcript / 根 retarget TOCTOU / 检查后换父目录 symlink 或 basename hardlink）+ MEDIUM（非原子写）**：这五项依附于同一个动作——**截断一个已存在的文件**。**架构级修复**：写出改为「同目录 `O_EXCL` 新建临时文件 → 写 → `fsync` → `os.replace` 原子替换」，**全文再无任何 `ftruncate` 调用**。`O_EXCL` 保证写入目标是本进程新建的对象，因此"把 `--out` 换成指向恢复源的 hardlink / 父目录 symlink / 大小写别名"整类绕过失效；`os.replace` 同时消除崩溃/ENOSPC 留下部分台账的风险。实测：根外 hardlink 指向根内 transcript 作 `--out` → 台账正常写出而**源文件内容完好**（`os.replace` 只重绑定该名字，不触碰底层 inode）。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-205-- **NOT-CLOSED（扫描受阻仅标记不停写）**：扫描受阻 ⇒ 保护集必然不完整。**整改**：`scan_errors`/`stat_failures` 非空时**直接拒绝写出台账**（exit 2），实测不落盘。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-206-- **LOW（lone surrogate 回退失效）**：异常发生在后续 `write`，不在原 `try` 内。**整改**：`json.dumps` 后立即 `.encode("utf-8")` 探测，编码错误在写出前暴露并回退 `ensure_ascii=True`。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-207-- **LOW（receipt 用 8 位缩写）**：如实登记为已知限制（仓库内唯一可解析），未改为 40-hex 以保持 receipt 可读性——列 follow-up。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-208-
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-209-round-7 整改后第七次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变、台账 mode 0600、无临时文件残留——七轮整改数字全程未变**。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-210-
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:211:## §7i Codex round-8 复审整改记录（裁定分离重申 + 3 BLOCKER 全闭）
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-212-
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:213:round-8 重申 round-7 的裁定分离，措辞更明确：
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-214-
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:215:> **可验收：92 条冻结 ledger snapshot。不可验收：当前生成器的一般安全性，以及 UAT 的"纯只读、唯一写出口、整类 TOCTOU 已消失"声明。**
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-216-
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-217-三条新 BLOCKER 全部属实，逐条整改：
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-218-
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:219:- **BLOCKER①（SQLite URI 未转义）**：`file:{db_path}?mode=ro` 在路径含 `#` 时，`mode=ro` 会落进被忽略的 URI fragment，SQLite 可能按**默认读写模式**打开——直接反驳"唯一写出口"。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-220-- **BLOCKER②（QA DB 仍按 pathname 打开）**：验证 fd 保持打开也没用，SQLite 另按路径解析，A→B→A 可让 connection 读到 B 而复核看到 A。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:221:- **①②的共同解法**：不再让 SQLite 碰路径——从**已验证的 fd** 读全量字节 → `sqlite3` 内存库 `deserialize()`。URI 转义问题与 ABA **一并消失**，且全程不落任何文件。实测：路径含 `#` 与 `?` 的 DB 正常只读（`read_mode: in_memory_deserialize_from_verified_fd`，16384 bytes）。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-222-- **BLOCKER③（根内末级 symlink）**：POSIX 规定 `rename`/`replace` **不解析末级 symlink**——`--out` 若是根内 symlink 指向根外，`realpath` 判"根外"而放行，但 replace 实际替换的是**根内那个目录项**。**整改**：containment 改用**父目录语义**（`dirname` 在根内即拒），叠加原有末级判定。实测：根内 symlink 作 `--out` → exit 2，symlink 未被替换。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-223-- **HIGH（扫描受阻拒绝不完整）**：no_token/token_conflict 分支在写入 `scan_errors` **之前**就早退；且拒绝条件写作 `scan_blocked and args.out`，**省略 `--out` 走 stdout 即可绕过**。**整改**：早退分支同样记录扫描错误；拒绝条件去掉 `and args.out`。实测：stdout 模式扫描受阻同样 exit 2。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-224-- **MEDIUM（tmp 残留 + 未 fsync 父目录）**：`os.replace` 在 `try` 外，`EXDEV/EBUSY/EACCES/ENOSPC` 会冒泡并留下 tmp。**整改**：replace 纳入 try，异常一律 `unlink` tmp；成功后 `fsync` 父目录使重命名落盘。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md-225-
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:226:round-8 整改后第八次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变、无 tmp 残留——八轮整改数字全程未变**。

**Analyzing SQLite deserialize atomicity risks**
**Evaluating exception handling in SQLite queries**
**Confirming read-only source with writable memory DB**
**Assessing SQLite virtual table and WAL implications**
**Identifying WAL-related database snapshot issues**
**Designing WAL mode detection and rejection**
**Assessing SQLite deserialize error handling**
**Planning local SQLite version inspection**
codex
目前能确认：`af251e4a` 是当前 HEAD 的直接祖先，后续 `2cdf77a4` 只补 receipt；脚本与 ledger blob 在两者间完全相同。前三项表面修补已进入真实入口，但发布链仍没有把“检查过的父目录 / 写过的 tmp inode / 实际 replace 的名字”绑定成同一组对象；我正在把这一点与 deserialize 的资源和一致性边界分开定级。
exec
/bin/zsh -lc "python3 -I -S -B -c 'import sqlite3,sys; print(sys.version); print(\"sqlite\",sqlite3.sqlite_version); print(sqlite3.Connection.deserialize.__doc__); print(\"limits\", sqlite3.SQLITE_LIMIT_LENGTH, sqlite3.connect(\":memory:\").getlimit(sqlite3.SQLITE_LIMIT_LENGTH))'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
3.14.4 (main, Apr  7 2026, 13:13:20) [Clang 21.0.0 (clang-2100.0.123.102)]
sqlite 3.53.0
Load a serialized database.

  data
    The serialized database content.
  name
    Which database to reopen with the deserialization.

The deserialize interface causes the database connection to disconnect from the
target database, and then reopen it as an in-memory database based on the given
serialized data.

The deserialize interface will fail with SQLITE_BUSY if the database is
currently in a read transaction or is involved in a backup operation.
limits 0 1000000000

**Testing SQLite deserialize with length limits**
**Designing Python here-doc command workaround**
**Confirming shell single-quote usage**
exec
/bin/zsh -lc "python3 -I -S -B -c 'exec(\"\"\"import sqlite3
src=sqlite3.connect(\":memory:\")
src.execute(\"create table qa_error_logs(error_type text)\")
data=src.serialize()
print(\"serialized_len\",len(data))
for label,payload,limit in [(\"valid\",data,None),(\"invalid_4k\",b\"X\"*4096,None),(\"limit_below\",data,len(data)-1),(\"empty\",b\"\",None)]:
    c=sqlite3.connect(\":memory:\")
    if limit is not None:
        print(label,\"old_limit\",c.setlimit(sqlite3.SQLITE_LIMIT_LENGTH,limit),\"new_limit\",c.getlimit(sqlite3.SQLITE_LIMIT_LENGTH))
    try:
        c.deserialize(payload)
        print(label,\"deserialize=ok\")
        try:
            print(label,\"schema_query=\",c.execute(\"select name from sqlite_master\").fetchall())
        except BaseException as e:
            print(label,\"query_exc\",type(e).__name__,str(e))
    except BaseException as e:
        print(label,\"deserialize_exc\",type(e).__name__,str(e))
    finally:
        c.close()
\"\"\")'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
serialized_len 8192
valid deserialize=ok
valid schema_query= [('qa_error_logs',)]
invalid_4k deserialize=ok
invalid_4k query_exc DatabaseError file is not a database
limit_below old_limit 1000000000 new_limit 8191
limit_below deserialize=ok
limit_below schema_query= [('qa_error_logs',)]
empty deserialize_exc MemoryError 

**Investigating SQLite deserialize limits**
**Planning official SQLite docs query**
web search: 
web search: site:docs.python.org/3/library/sqlite3.html Connection.deserialize database data too large MemoryError ...
**Adjusting output parsing method**
web search: 
web search: https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.deserialize
**Locating deserialize references in Python docs**
web search: 
web search: 'deserialize(data'
**Inspecting QA DB header and WAL files**
exec
/bin/zsh -lc "stat -f 'qa mode=%Lp size=%z nlink=%l dev=%d ino=%i mtime=%m' '/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db'; shasum -a 256 '/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db'; od -An -t u1 -j 18 -N 2 '/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db'; ls -ld '/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db' '/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db-wal' '/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db-shm' '/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db-journal' 2>&1" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 exited 1 in 0ms:
qa mode=644 size=16384 nlink=1 dev=16777230 ino=18698919 mtime=1786758939
6cb5510dc91cf1c29c7ce6510013238cf83b5eae6305180e6aa9320a957a6a05  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db
            1   1                                                        

ls: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db-journal: No such file or directory
ls: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db-shm: No such file or directory
ls: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db-wal: No such file or directory
-rw-r--r--  1 Heishing  staff  16384 Aug 15 09:55 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db

**Verifying O_NONBLOCK behavior on regular files**
**Analyzing file read memory overhead and race conditions**
web search: 
web search: site:github.com/python/cpython Modules/_sqlite/connection.c pysqlite_connection_deserialize PyMem_Malloc ...
**Planning precise code search**
web search: 
web search: 'pysqlite_connection_deserialize_impl'
**Searching for serialize.c file**
web search: 
web search: site:github.com/python/cpython/Modules/_sqlite "Connection.deserialize" "sqlite3_deserialize" ...
**Planning raw URL access for source**
web search: 
web search: https://raw.githubusercontent.com/python/cpython/v3.14.4/Modules/_sqlite/connection.c
**Planning code search for Deserialize**
web search: 
web search: 'Deserialize a database'
**Confirming unbounded SQLite deserialize memory usage**
**Planning POSIX O_NONBLOCK verification**
web search: 
web search: site:pubs.opengroup.org/onlinepubs/9799919799 O_NONBLOCK regular file no effect open read ...
**Verifying Git diff and updating plan**
已确认 af251e4a 为 HEAD 的直接祖先，2cdf77a4 仅更新 receipt；被审脚本与 ledger 两个 blob 未漂移，生产入口已定位。
  ✓ 锁定 checkout、commit af251e4a、round-8→round-9 diff 与生产入口
  → 复核 verified-fd→deserialize、扫描拒绝及异常/资源上限反例
  • 复核 containment、原子发布、tmp 清理、父目录 fsync 与并发反例
  • 从冻结 artifact/exact bytes 独立复算 92 条台账与全部分布
  • 交叉核验高严重度结论，输出 CLOSED/NOT-CLOSED、总裁定和最小剩余项
**Auditing output checks and snapshot functions**
**Detailing secure temporary file creation**
**Requiring trusted parent directory for output**
**Assessing concurrent DB read-write risks**
**Verifying snapshot integrity under concurrent writes**
**Planning safe SQLite snapshot via read transaction**
**Assessing SQLite snapshot verification approach**
**Evaluating locking strategies for snapshot consistency**
**Identifying partial read risk in live DLQ snapshot**
**Inspecting top document lines 1-60**
**Verifying inode metadata effects on readonly status**
**Assessing hardlink unlinking impact on output safety**
**Planning output restriction to trusted root**
**Analyzing file descriptor cleanup edge cases**
**Assessing file write durability and path validation nuances**
**Highlighting macOS bind mount alias risk**
**Analyzing temp file concurrency risks**
**Evaluating output file collision and atomicity risks**
**Assessing atomic rename and inode binding limitations**
**Assessing minimal safety requirements and test necessity**
**Reviewing ledger integrity and data consistency**
exec
/bin/zsh -lc "nl -ba '_bmad-output/审查/G4-9-evidence/shasums-after.txt' | sed -n '1,12p'; nl -ba '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' | sed -n '1,185p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
     1	3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl
     2	490c903b2f3636e1d2c4ecb68465cef41ace06f0bd171eb2fb95c03a7b40cb43  /Users/Heishing/Desktop/canvas/canvas-learning-system/backend/data/dead_letter_episodes.jsonl
     3	bfb3f6c413aab7dd4c04a25f7575aaaffcfc92fd4e8e8966362609652ac7e310  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/data/dead_letter_episodes.jsonl
     4	75c5f7593b9b2e99672d0551487b4476552ebd8d33ad25c5f9479683cc61e9c9  /Users/Heishing/Desktop/canvas/canvas-learning-system/data/dead_letter_episodes.jsonl
     5	6cb5510dc91cf1c29c7ce6510013238cf83b5eae6305180e6aa9320a957a6a05  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db
     1	{
     2	 "card": "CARD-G4-9",
     3	 "generated_at": "2026-08-28T13:35:50.981742+00:00",
     4	 "privacy": "private-only: transcript_paths 含本机用户名与 session UUID，禁止外发/公网发布",
     5	 "stable_key_semantics": "冻结快照（dlq_file.sha256）内的 occurrence key；line_no 在快照内唯一，sha256_prefix/request_id 为冗余对账维度——非跨文件重排或语义幂等键",
     6	 "dlq_file": {
     7	  "path": "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl",
     8	  "exists": true,
     9	  "line_count": 92,
    10	  "sha256": "3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590",
    11	  "mtime_utc": "2026-08-11T14:01:25.808462+00:00",
    12	  "mtime_note": "mtime 取自读取用 fd 的 fstat；绑定 exact bytes 的是 sha256"
    13	 },
    14	 "compare_copies": [
    15	  {
    16	   "path": "/Users/Heishing/Desktop/canvas/canvas-learning-system/backend/data/dead_letter_episodes.jsonl",
    17	   "exists": true,
    18	   "line_count": 685,
    19	   "sha256": "490c903b2f3636e1d2c4ecb68465cef41ace06f0bd171eb2fb95c03a7b40cb43",
    20	   "mtime_utc": "2026-04-07T11:47:19.585617+00:00",
    21	   "mtime_note": "mtime 取自读取用 fd 的 fstat；绑定 exact bytes 的是 sha256"
    22	  },
    23	  {
    24	   "path": "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/data/dead_letter_episodes.jsonl",
    25	   "exists": true,
    26	   "line_count": 1,
    27	   "sha256": "bfb3f6c413aab7dd4c04a25f7575aaaffcfc92fd4e8e8966362609652ac7e310",
    28	   "mtime_utc": "2026-07-13T04:51:14.925282+00:00",
    29	   "mtime_note": "mtime 取自读取用 fd 的 fstat；绑定 exact bytes 的是 sha256"
    30	  },
    31	  {
    32	   "path": "/Users/Heishing/Desktop/canvas/canvas-learning-system/data/dead_letter_episodes.jsonl",
    33	   "exists": true,
    34	   "line_count": 4,
    35	   "sha256": "75c5f7593b9b2e99672d0551487b4476552ebd8d33ad25c5f9479683cc61e9c9",
    36	   "mtime_utc": "2026-04-05T23:30:49.019652+00:00",
    37	   "mtime_note": "mtime 取自读取用 fd 的 fstat；绑定 exact bytes 的是 sha256"
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
    58	  "unverifiable": 0,
    59	  "unrecoverable": 0
    60	 },
    61	 "inline_state_distribution": {
    62	  "full_verified": 4,
    63	  "truncated_prefix": 88,
    64	  "anomaly": 0
    65	 },
    66	 "unrecoverable_list": [],
    67	 "unverifiable_list": [],
    68	 "attribution_conflicts": [
    69	  {
    70	   "line_no": 1,
    71	   "sha256_prefix": "7e33da5e96e6239f",
    72	   "request_id": "281466113679440"
    73	  },
    74	  {
    75	   "line_no": 2,
    76	   "sha256_prefix": "b91bf262cadab596",
    77	   "request_id": "281466014769488"
    78	  },
    79	  {
    80	   "line_no": 3,
    81	   "sha256_prefix": "55b1b793b99778eb",
    82	   "request_id": "281466427090256"
    83	  }
    84	 ],
    85	 "duplicate_clusters": [
    86	  {
    87	   "name": "session-archive:426ffbde-15f6-4b",
    88	   "episode_body_sha256": "c93058c9850c6999310e98df9e6ebc26063b96fa6f0649fb1ec6d9d04c88a7fe",
    89	   "group_id": "vault:canvas_vault",
    90	   "line_nos": [
    91	    11,
    92	    15,
    93	    22,
    94	    26,
    95	    32,
    96	    39,
    97	    43,
    98	    47,
    99	    55,
   100	    63,
   101	    67,
   102	    71,
   103	    80,
   104	    84,
   105	    88,
   106	    92
   107	   ],
   108	   "occurrences": 16
   109	  },
   110	  {
   111	   "name": "qa_highlight:Q: What is the relationship between a co",
   112	   "episode_body_sha256": "f22956e79a5a23be64d05cd806fd78773916c5bc40b10f9cfd7d5fda0814e10e",
   113	   "group_id": "vault:canvas_vault",
   114	   "line_nos": [
   115	    24,
   116	    41,
   117	    78,
   118	    82
   119	   ],
   120	   "occurrences": 4
   121	  },
   122	  {
   123	   "name": "conversation_distillation:Distilled summary for node session:426ff",
   124	   "episode_body_sha256": "f9682670197b1339166db46bc7a6b49cca01d745e100568dfdd88b6aa15c6f51",
   125	   "group_id": "vault:canvas_vault",
   126	   "line_nos": [
   127	    8,
   128	    12,
   129	    68
   130	   ],
   131	   "occurrences": 3
   132	  },
   133	  {
   134	   "name": "qa_highlight:Q: What is the relationship between a co",
   135	   "episode_body_sha256": "7a830d4e3c5d52fe3699e0065c5ab61ae013eca3dcf6dd79cf246e37fc4d8629",
   136	   "group_id": "vault:canvas_vault",
   137	   "line_nos": [
   138	    13,
   139	    45
   140	   ],
   141	   "occurrences": 2
   142	  },
   143	  {
   144	   "name": "conversation_distillation:Distilled summary for node session:426ff",
   145	   "episode_body_sha256": "288e4b506e72402e22c8b08fa9608c8dc9e1870ccdd43ed4ab93c95655435064",
   146	   "group_id": "vault:canvas_vault",
   147	   "line_nos": [
   148	    16,
   149	    64
   150	   ],
   151	   "occurrences": 2
   152	  },
   153	  {
   154	   "name": "qa_highlight:Q: What is the relationship between a co",
   155	   "episode_body_sha256": "04e26b3060192bc9de508b2e75c508fba86553a82bea1e910bc24771c75834b5",
   156	   "group_id": "vault:canvas_vault",
   157	   "line_nos": [
   158	    37,
   159	    86
   160	   ],
   161	   "occurrences": 2
   162	  }
   163	 ],
   164	 "qa_metrics_probe": {
   165	  "db_path": "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db",
   166	  "opened_readonly": true,
   167	  "bytes_read_from_verified_fd": 16384,
   168	  "file_identity_verified": true,
   169	  "read_mode": "in_memory_deserialize_from_verified_fd",
   170	  "tables": [
   171	   "qa_error_logs"
   172	  ],
   173	  "qa_error_logs_rows": 0,
   174	  "error_type_hits": {
   175	   "BadRequestError": 0,
   176	   "EntityTypeValidationError": 0,
   177	   "GroupIdValidationError": 0
   178	  },
   179	  "verdict": "no_source_rows"
   180	 },
   181	 "records": [
   182	  {
   183	   "stable_key": {
   184	    "line_no": 1,
   185	    "sha256_prefix": "7e33da5e96e6239f",

**Inspecting top stale document statements**
exec
/bin/zsh -lc "nl -ba backend/scripts/census_dead_letter_episodes.py | sed -n '1,62p'; nl -ba '_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md' | sed -n '20,36p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
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
    55	import hashlib
    56	import json
    57	import os
    58	import re
    59	import sqlite3
    60	import stat
    61	import sys
    62	from collections import Counter, defaultdict
    20	2. **一条都不算丢**：4 条正文完整躺在死信文件里（可逐字节恢复）；88 条只存了前 200 字预览，但每一条都顺着线索找回了**唯一**源头会话记录（7 个会话的原始 transcript 全部还在你电脑上）——可近似重建（找到了源头 ≠ 已经恢复，真正重建是 G4-10 的活）。**不可恢复：0 条**。另清点出 6 组重复（29 条是同内容反复入队），G4-10 恢复时会先去重，不会把同一段写 16 遍。
    21	3. **死信文件的"真身"只有一处**：线上容器读写的是 `feature-obsidian-hybrid-dev` worktree 的 `backend/data/`（容器内实测 sha 一致）；主仓那份 685 行是 4 月的陈旧副本，另有两处孤儿残留——报告里有四址对照表，以后不会再查错文件。
    22	
    23	## ✅ 技术验证（Claude 已代跑）
    24	
    25	| 项 | 结果 | 证据 |
    26	|---|---|---|
    27	| 全程零写入（裁判判据 e） | 运行前后 四份 DLQ 文件 + qa_metrics.db 的 sha256 **逐字节不变**（diff 为空 → PASS） | `_bmad-output/审查/G4-9-evidence/shasums-before.txt` / `shasums-after.txt` |
    28	| 脚本只读自证（判据 a） | import 行全 stdlib；neo4j/graphiti/bolt/app. import **0 命中**；`--apply` 定义 **0 命中**；写模式 open 仅台账 `--out` 1 处 | `G4-9-evidence/grep-selfattest.txt` |
    29	| live 挂载真相（判据 c） | 容器内 `sha256sum /app/data/dead_letter_episodes.jsonl` = 宿主 live 地址同值（92 行，`3b37460f…`）；compose :206-212 遮蔽史入报告 §1 | `G4-9-evidence/container-sha-check.txt` + 报告 §1 |
    30	| 分类零偏差（判据 b） | budget_400×**89** / schema×**2**（P0-4 已修，`entity_types.py:343`）/ group_id×**1**（sanitize 已兜，`group_id_compat.py:64`）——与勘探预期逐条一致，脚本 `class_deviation` 字段为空 | 台账 JSON `class_distribution` |
    31	| inline 完整性 + SHA 对账（判据 b） | 92/92 重算 sha256 对账：4 条 full_verified、88 条 truncated_prefix（`to_dict()` 的 `[:200]` 截断，`episode_worker.py:107`）、**0 条 anomaly** | 台账 JSON 逐条 `inline_state`/`sha_check` |
    32	| 源指针核销（判据 b，qa_metrics.db 只读 mode=ro） | `qa_error_logs` **0 行** → 0/92 可经 qa_metrics.db 溯源（诚实记录）；附加核销：llm_call_logs.db 无正文、outbox 空、episode_body_full 0 条；**有效源指针 = request_id 组内 session 归因 → 7 个 transcript 全部在盘实测存在** | 报告 §4 + 台账 `qa_metrics_probe` |
    33	| 可恢复性三态（判据 b） | 可字节级 **4** / 近似 **88** / 不可恢复 **0**；不可恢复清单显式成段 0 条、"待定" 0 条 | 报告 §5 + 台账 `recoverability_distribution` |
    34	| G4-10 稳定键（判据 d） | 逐条复合键 `{line_no, sha256_prefix, request_id}` + 台账头部冻结文件 sha；request_id 92 条仅 25 唯一值的实测证明单列不可作键 | 报告 §6 + 台账 `records[].stable_key` |
    35	| Codex 独立审查 round-1 | **BLOCKED**（3 BLOCKER：--out 可截断输入 / 快照不原子 / 交付物未冻结；3 HIGH：inline 判定 fail-open / request_id 归因传染 / transcript 归因折叠；3 MEDIUM + 4 LOW。同时确认：**当前 92 条数字逐项 0 mismatch**、class/三态/家族计数全对） | `_bmad-output/审查/codex-review-CARD-G4-9.md` |
    36	| Codex findings 逐条整改 | **13/13 完成**（见下）；整改版脚本负例门全过；全量重跑数字与整改前逐项一致 | 报告 §7/§7b + 证据包 |

**Refining read-only mode documentation**
**Categorizing claim correction requirement**
collab: Wait
**Analyzing SQLite read correctness and size handling risks**
**Enforcing SQLite DB size limits and improving error handling**
**Reviewing SQLite query exception handling**
**Verifying database image integrity**
**Clarifying file identity verification limits**
**Confirming unreadable candidate handling**
**Identifying no_token stat failure behavior**
**Confirming fail-closed candidate rejection logic**
**Fixing leaf symlink root rejection**
**Correcting SQLite memory limit claim**
**Confirming SQLite deserialize behavior and exceptions**
**Planning matched-size database construction**
**Planning efficient batch insertion**
exec
/bin/zsh -lc "python3 -I -S -B -c 'exec(\"\"\"import sqlite3, hashlib
def image(tag):
    c=sqlite3.connect(\":memory:\")
    c.execute(\"pragma page_size=4096\")
    c.execute(\"create table qa_error_logs(id integer primary key, error_type text, pad text)\")
    c.executemany(\"insert into qa_error_logs(error_type,pad) values (?,?)\", ((tag, \"x\"*160) for _ in range(30000)))
    c.commit()
    b=c.serialize()
    c.close()
    return b
a=image(\"A\")
b=image(\"B\")
cut=1<<20
h=a[:cut]+b[cut:]
c=sqlite3.connect(\":memory:\")
c.deserialize(h)
print(\"sizes\",len(a),len(b),len(h),\"same\",len(a)==len(b))
print(\"quick_check\",c.execute(\"pragma quick_check\").fetchone()[0])
print(\"counts\",c.execute(\"select error_type,count(*) from qa_error_logs group by error_type order by error_type\").fetchall())
print(\"hashes\",hashlib.sha256(a).hexdigest()[:16],hashlib.sha256(b).hexdigest()[:16],hashlib.sha256(h).hexdigest()[:16])
c.close()
\"\"\")'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
sizes 5365760 5365760 5365760 same True
quick_check ok
counts [('A', 5842), ('B', 24158)]
hashes 4e7e5e9638bbab9b c747f8e17acac5bb 55e64749ce593630

**Verifying file operation consistency**
web search: 
web search: site:pubs.opengroup.org/onlinepubs/9799919799/functions/rename.html rename symbolic link final component ...
**Planning SQLite WAL clarification and git diff inspection**
mcp: sequential-thinking/sequentialthinking started
mcp: sequential-thinking/sequentialthinking (completed)
**Defining severity taxonomy and blockers**
**Classifying new versus retained findings**
**Clarifying unresolved findings as open**
**Assessing severity of data issues**
**Identifying security and integrity vulnerabilities**
**Analyzing mount alias race condition**
**Analyzing directory fd stability after rename**
**Identifying unsafe cleanup risks after os.replace failure**
**Exposing concurrency issue in tmp cleanup**
**Analyzing PID temp file concurrency issues**
**Evaluating tmp file concurrency and fsync behavior**
**Noting cwd effects on parent directory handling**
**Clarifying EXDEV handling and containment edges**
**Analyzing path resolution and mount point behaviors**
**Verifying output parent accessibility and ledger state**
**Comparing artifact receipts between commits**
exec
/bin/zsh -lc "git show 'af251e4a:_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt' | nl -ba | tail -n 8; nl -ba '_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt' | tail -n 8" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
    11	d8d887f2  本 receipt 首次落盘
    12	4c125f19  CARD-G4-9 round-5 整改
    13	5b371253  CARD-G4-9 round-6 架构级修复
    14	4ba4f847  receipt 补 round-5/6 链
    15	f389980c  CARD-G4-9 round-7 架构级修复（消除截断动作）
    16	<next>    CARD-G4-9 round-8 整改（QA DB 内存 deserialize / 父目录 containment / stdout 门 / 原子替换清理）
    17	
    18	各阶段交付物 blob 可用 git cat-file 复核；台账头部 dlq_file.sha256 为 DLQ 快照指纹。
    11	d8d887f2  本 receipt 首次落盘
    12	4c125f19  CARD-G4-9 round-5 整改
    13	5b371253  CARD-G4-9 round-6 架构级修复
    14	4ba4f847  receipt 补 round-5/6 链
    15	f389980c  CARD-G4-9 round-7 架构级修复（消除截断动作）
    16	af251e4a  CARD-G4-9 round-8 整改（QA DB 内存 deserialize / 父目录 containment / stdout 门 / 原子替换清理）
    17	
    18	各阶段交付物 blob 可用 git cat-file 复核；台账头部 dlq_file.sha256 为 DLQ 快照指纹。

**Verifying absence of specific tests**
exec
/bin/zsh -lc "git grep -n -E 'census_dead_letter_episodes|probe_qa_metrics|_path_is_within|census-tmp' af251e4a -- backend/tests tests 2>/dev/null || true" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
**Evaluating test requirements and Context7 usage**
**Planning independent ledger verification script**
**Validating agent ledger results and citations**
**Deciding citation standards and verdict wording**
**Summarizing acceptance criteria and required fixes**
**Defining generator fail-closed behavior**
**Designing reliable output directory binding**
**Implementing concurrency and crash state handling**
**Drafting minimal truthful doc requirements**
**Defining minimal required acceptance groups**
**Confirming original fixes ensure closure**
**Assessing tmp cleanup and fsync issues**
**Verifying temp residue absence and planning citation extraction**
**Confirming precise citation line ranges**
**Setting memory and skill read-only**
exec
/bin/zsh -lc "nl -ba /Users/Heishing/.codex/memories/MEMORY.md | sed -n '181,188p'; nl -ba /Users/Heishing/.codex/memories/skills/canvas-adversarial-audit/SKILL.md | sed -n '14,41p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
   181	- “启动并行 agent 进行对抗性审查” -> use independent evidence tracks and cross-check severity; every finding needs `file:line`, reproduction path/result, severity, conflict explanation, PASS/PARTIAL/FAIL, and limits. [Task 1][Task 2]
   182	- Respect read-only task-book boundaries, WT/MAIN labels, explicit `UNVERIFIABLE`, and no raw-vault access; do not fix code in the audit. [Task 1]
   183	
   184	## Reusable knowledge
   185	
   186	- Related skill: skills/canvas-adversarial-audit/SKILL.md. P1-05/P1-01/P1-08 remained STILL-OPEN; F-02 tombstone filtering and F-05 live resilience were closed. Rejected vault inputs must show zero open/hash/index/write. [Task 1][Task 2]
   187	- Reproduced: `vault/raw/escape.md -> /outside/secret.md` was counted by `backfill_vault(..., execute=False)`; case-sensitive `fnmatch` admitted `.CLAUDE/SKILL.md` and `raw/claude.md`. Edge filtering alone was insufficient because exact readers/node search could cross Graphiti groups. [Task 2]
   188	- SnapshotV3 needs invalid/future same-generation self-healing, extra-field, strict-type, huge finite mastery, and identity/length collision coverage. [Task 1][Task 2]
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

**Finalizing update plan and cross-checking severity**
mcp: sequential-thinking/sequentialthinking started
mcp: sequential-thinking/sequentialthinking (completed)
**Assessing memory overhead in deserialization**
**Analyzing memory retention and snapshot consistency**
**Highlighting code crash risk and integrity check limits**
**Analyzing symlink behavior impact**
**Evaluating TOCTOU and atime update risks**
**Confirming atime updates not critical**
**Verifying SQLite in-memory connection behavior**
**Confirming read-only UAT status and untracked files**
**Planning detailed Chinese summary structure**
**Drafting explicit closed status labels**
**Categorizing closure status for fix items**
**Identifying uncaught schema query error**
**Assessing file operation inconsistencies**
**Identifying unresolved path and temp file issues**
**Grading findings by severity levels**
**Classifying new versus retained findings**
**Summarizing ledger file analysis**
**Implementing strict file handling safeguards**
**Designing temp file identity and recovery**
**Evaluating test execution constraints**
**Verifying clean repository state**
codex
交叉核验已经收敛：冻结数据面仍是 0 mismatch；真正阻断安全声明的是对象绑定而不是那 92 条数字。一个纯内存反例已独立复现：两个同长合法 SQLite 镜像按脚本的 1 MiB 边界拼接后，`quick_check=ok`，却同时读出 A/B 两组行——证明“verified fd”并不等于一致的数据库时间点快照。
exec
/bin/zsh -lc "git status --short --branch; git rev-parse HEAD; git diff --stat af251e4a..HEAD; shasum -a 256 backend/scripts/census_dead_letter_episodes.py '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json'; find . -name '*.census-tmp-*' -print; stat -f 'ledger_mode=%Lp ledger_size=%z ledger_nlink=%l' '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 1088ms:
 .../\345\256\241\346\237\245/G4-9-evidence/artifact-commit-receipt.txt" | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
478332860a15f9294681c33702a5df4af7bff9a8fefb05e91abefe865d0e68e1  backend/scripts/census_dead_letter_episodes.py
b8f042c6d3aca8db8216c77a1ca9ad891436b1bda485218b4f6e970395a6c287  _bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json
ledger_mode=600 ledger_size=142508 ledger_nlink=1

**Confirming plan steps completion**
三条独立轨道已完成并由主审复核：QA/path/scan 安全、publication/containment、ledger exact-byte 复算。开始汇总分层裁定与最小剩余项。
  ✓ 锁定 checkout、commit af251e4a、round-8→round-9 diff 与生产入口
  ✓ 复核 verified-fd→deserialize、扫描拒绝及异常/资源上限反例
  ✓ 复核 containment、原子发布、tmp 清理、父目录 fsync 与并发反例
  ✓ 从冻结 artifact/exact bytes 独立复算 92 条台账与全部分布
  → 交叉核验高严重度结论，输出 CLOSED/NOT-CLOSED、总裁定和最小剩余项
mcp: sequential-thinking/sequentialthinking started
mcp: sequential-thinking/sequentialthinking (completed)
mcp: sequential-thinking/sequentialthinking started
mcp: sequential-thinking/sequentialthinking (completed)
**Completing update plan**
高严重度反例、exact-byte 复算、checkout/工作树终态均已交叉确认；审计结论与最小验收门已形成。
  ✓ 锁定 checkout、commit af251e4a、round-8→round-9 diff 与生产入口
  ✓ 复核 verified-fd→deserialize、扫描拒绝及异常/资源上限反例
  ✓ 复核 containment、原子发布、tmp 清理、父目录 fsync 与并发反例
  ✓ 从冻结 artifact/exact bytes 独立复算 92 条台账与全部分布
  ✓ 交叉核验高严重度结论，输出 CLOSED/NOT-CLOSED、总裁定和最小剩余项
**Analyzing symlink retargeting vulnerability**
**Confirming race condition in rename replace**
**Verifying path containment with nested mounts**
**Verifying output path error handling**
**Documenting file link mappings and citations**
**Clarifying memory search limitations and fix classification**
**Evaluating partial fix status and issue severity**
**Adjusting document formatting for tables**
codex
总裁定：**分层结论不变。**

- **可验收**：92 条冻结 ledger snapshot，独立 exact-byte 复算全部一致。
- **不可验收**：生成器的一般安全性，以及 UAT 的“纯只读、唯一写出口、整类 TOCTOU 已消失”声明。
- `af251e4a` 的前三项狭义整改已闭合；tmp/发布/持久化整改仅部分闭合，并有新的 QA 一致性缺口。

审阅锚点：目标提交 `af251e4a1a8b2c99e3f171d153642bd02d856f99`；当前 `HEAD=2cdf77a4` 仅补 receipt，脚本和 ledger blob 与目标提交完全相同。

## 整改逐项复核

| 整改项 | 裁定 | 关键证据 |
|---|---|---|
| SQLite URI `#/?` 未转义 | **CLOSED** | SQLite 只收到 `":memory:"`；用户 pathname 不再进入 URI。[QA 入口](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:304) |
| pathname A→B→A | **CLOSED（路径对象层）** | `O_RDONLY\|O_NOFOLLOW\|O_NONBLOCK → fstat/S_ISREG → 同 fd 读 bytes → deserialize`，[读取链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:318)。后续 pathname 换链不再改变 SQLite 的输入 inode。 |
| 根内末级 symlink | **CLOSED（namespace 稳定时）** | `dirname(abspath(out))` 在根内会于创建 tmp 前拒绝。[containment](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:476) |
| no_token/token_conflict 吞扫描错误 | **CLOSED** | 两个早退前已复制 `scan_errors/stat_failures`。[扫描分支](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:261) |
| stdout 绕过 | **CLOSED** | `scan_blocked` 无 `args.out` 条件直接 return 2，早于 stdout。[拒绝门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:755) |
| replace 异常清 tmp + parent fsync | **PARTIAL，整体 NOT-CLOSED** | replace 已纳入 try，也调用了 fsync；但 tmp、目标和 parent 仍分别按可变 pathname 重解析，且 fsync 发生在发布之后。[发布链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:801) |

## 指定反例结果

- **`deserialize` 一致性：NOT-CLOSED · HIGH。** verified fd 只绑定 inode，不产生数据库时间点快照。独立纯内存复现：两个同长 `5,365,760` 字节、各 30,000 行的合法 DB，按代码的 1 MiB 读取边界拼接后，`deserialize` 成功、`PRAGMA quick_check=ok`，却得到 `A=5,842 / B=24,158`，不属于任一源状态。同 inode 原地写即可产生可信外观的混合 QA 结论。

- **大小/内存：NOT-CLOSED · MEDIUM。** 没有 `st_size` 或累计读取上限；`chunks + join + CPython deserialize copy` 峰值至少约三份数据库字节。CPython 3.14.4 仅先检查 `len(data) <= 2^63-1`，随后按完整大小分配并复制，并无业务可用的输入上限。[CPython 实现](https://github.com/python/cpython/blob/v3.14.4/Modules/_sqlite/connection.c#L2191-L2206)

- **异常路径：NOT-CLOSED · MEDIUM。** 本机实测 4096 字节 garbage 可先 `deserialize_ok`，随后 `sqlite_master` 查询才抛 `DatabaseError`；当前查询段只有 `finally`，异常会逃逸。空 bytes 在 deserialize 阶段产生无消息 `MemoryError`。WAL header `2/2` 同样在使用时失败；SQLite 明确说明反序列化输入不应处于 WAL mode。[SQLite deserialize](https://www.sqlite.org/c3ref/deserialize.html)

- **`O_NONBLOCK` 普通文件：CLOSED／无新增缺陷。** 它不会提供异步或一致快照语义；普通文件仍按常规方式读取。其作用只是避免 FIFO/device 在 `fstat` 前阻塞，随后 `S_ISREG` 再拒绝特殊文件。[POSIX open](https://pubs.opengroup.org/onlinepubs/9799919799/functions/open.html)

- **parent fsync fd：NOT-CLOSED · HIGH。** fd 一旦成功打开便不会被后续换名“换掉”；问题是代码在 replace 后才按 pathname 打开它，可能一开始就打开了错误目录。若 replace 已成功而 parent open/fsync 失败，输出已经发布，却返回 2 并打印“原子替换失败、已清理”——执行状态与报告不一致。

- **父目录 retarget：NOT-CLOSED · BLOCKER（保留项）。** containment、tmp create、replace、parent fsync 四阶段均重新解析 pathname。父目录在检查后被换入 transcripts 子树，并在新目录预置同名 tmp，即可让 replace 修改恢复源区域。POSIX 提供 `renameat`/directory fd 正是为消除此类路径竞态。[POSIX rename](https://pubs.opengroup.org/onlinepubs/9799919799/functions/rename.html)

- **相对路径 / `dirname('.')`：稳定 namespace 下 CLOSED。** `abspath + realpath` 能正确处理 `ledger.json`、`./ledger.json`、`a/../ledger.json`。但 `--out .` 或 `/` 最终在 `Path.with_name()` 抛未捕获 `ValueError`，为 **LOW**。

- **挂载点：PARTIAL。** 词法上位于 transcripts 根内的普通挂载路径仍会命中根；但若 transcripts 的某个子目录被 bind/nullfs 到根外 alias，alias 的祖先 inode 不含 transcripts 根，无竞态即可绕过，故一般 containment **NOT-CLOSED · BLOCKER**。

- **循环 symlink：PARTIAL。** 稳定循环通常在 `is_dir`/open 阶段以 `ELOOP` 拒绝，不会写；解除或 retarget 循环仍归入上述 pathname TOCTOU。

- **可预测 tmp + `O_EXCL`：PARTIAL。** 预置 symlink 不会被跟随写入，狭义攻击 **CLOSED**；但可造成稳定 DoS。更严重的是 tmp 打开后可被 unlink/rebind：fd 写入 inode A，`os.replace(tmp_path, out)`却可能发布 inode B，仍为 **HIGH**。

- **两个进程同 PID：NOT-CLOSED。** 同时创建时一方 `EEXIST`；第一方 replace 后名字释放，第二方又可创建并最终 last-writer-wins。不同 PID 本来就能并行发布；跨 PID namespace 共享卷可出现同 PID。没有唯一发布者、锁或 CAS。

- **异常清理：NOT-CLOSED · MEDIUM。** `unlink` 失败被吞、清理目录未 fsync、SIGKILL/掉电仍可留 tmp；父目录被换后，清理还可能删除错误目录中的同名对象。

## 冻结 ledger 独立复算

没有调用生成器，也没有读取 transcript 正文。

| 项目 | 独立结果 |
|---|---|
| ledger | 142,508 bytes；SHA-256 `b8f042c6…95a6c287`；当前 mode `0600`、nlink 1 |
| live DLQ | 99,915 bytes；SHA-256 `3b37460f…ef3ba590`，与 [ledger header](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:6)一致 |
| records / unparseable | **92 / 0** |
| class | **89 / 2 / 1**，unexpected 0 |
| recoverability | **byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0** |
| attribution | **3**，全部 `no_token` |
| duplicates | **6 簇 / 29 条**；簇大小 `16,4,3,2,2,2` |
| 逐条对账 | stable key、class、inline、recoverability、冲突原因、transcript match count：**0 mismatch** |
| QA DB | 16,384 bytes；SHA-256 `6cb5510d…957a6a05`；header `1/1`、当前无 WAL/SHM/journal；`qa_error_logs=0` |
| QA ledger 字段 | `read_mode=in_memory_deserialize_from_verified_fd`、`bytes_read_from_verified_fd=16384` 均正确，[QA 段](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:164) |
| tmp 残留 | **0** |

QA SHA 不在 ledger 自身，只在 [shasums evidence](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/shasums-after.txt:5)；本次现态已复核，但 ledger 单文件并不能长期自证 QA exact bytes。

## 达到可验收的最小剩余项

必需：

1. **一致、有限的 QA snapshot**：使用身份绑定的 SQLite read transaction/backup 语义，或只接受外部已冻结、digest-bound、quiescent 的 DB；raw fd 分块读不能算数据库快照。显式拒绝 WAL/journal/并发变化，设置读取上限，所有 read/join/deserialize/query 异常统一 fail-closed。
2. **单一稳定目录对象发布**：输出 parent 在检查前以 `O_DIRECTORY|O_NOFOLLOW` 打开并验证；create/replace/unlink/fsync 全部相对同一个 dirfd。对 mount alias 要么检测拒绝，要么把输出限制到受信、不可换链的专用根。
3. **绑定 tmp、发布者与状态**：可信私有目录、不可预测或 unnamed tmp、same-FD readback hash；单写者锁/CAS；明确 `tmp durable → published → parent durable`，fsync 失败必须报告 `published_but_durability_unconfirmed`，并有崩溃残留 reconciliation。
4. **真实入口验收证据**：提交覆盖混合 DB、WAL、malformed/oversize、parent retarget、mount alias、tmp rebind、同/不同 PID、replace/fsync/unlink 故障的生产 `main()` 测试。当前仓库没有任何测试引用该生成器。
5. **修正声明**：脚本与 [UAT](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:32) 仍写 SQLite URI `mode=ro`；实际只有源 fd 为只读，内存连接可写。应改字段为 `source_fd_opened_readonly`，并把 QA SHA 写入 ledger。

建议：

- 内存连接设置 `PRAGMA query_only=ON`，并运行完整性检查；但 `quick_check` 不能替代一致快照。
- 增加 `O_CLOEXEC`、显式拒绝空 basename、随机 tmp 名。
- 随机名或 `O_EXCL` 单独都不足以解决共享可写目录中的名字重绑。

本轮未修改、创建或删除任何文件；开始和结束均只有预先存在的未跟踪 round-9 文档。`graphiti-canvas` 未在本会话暴露，无法执行其 memory search；Sequential Thinking 已完成。


tokens used
245,706
总裁定：**分层结论不变。**

- **可验收**：92 条冻结 ledger snapshot，独立 exact-byte 复算全部一致。
- **不可验收**：生成器的一般安全性，以及 UAT 的“纯只读、唯一写出口、整类 TOCTOU 已消失”声明。
- `af251e4a` 的前三项狭义整改已闭合；tmp/发布/持久化整改仅部分闭合，并有新的 QA 一致性缺口。

审阅锚点：目标提交 `af251e4a1a8b2c99e3f171d153642bd02d856f99`；当前 `HEAD=2cdf77a4` 仅补 receipt，脚本和 ledger blob 与目标提交完全相同。

## 整改逐项复核

| 整改项 | 裁定 | 关键证据 |
|---|---|---|
| SQLite URI `#/?` 未转义 | **CLOSED** | SQLite 只收到 `":memory:"`；用户 pathname 不再进入 URI。[QA 入口](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:304) |
| pathname A→B→A | **CLOSED（路径对象层）** | `O_RDONLY\|O_NOFOLLOW\|O_NONBLOCK → fstat/S_ISREG → 同 fd 读 bytes → deserialize`，[读取链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:318)。后续 pathname 换链不再改变 SQLite 的输入 inode。 |
| 根内末级 symlink | **CLOSED（namespace 稳定时）** | `dirname(abspath(out))` 在根内会于创建 tmp 前拒绝。[containment](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:476) |
| no_token/token_conflict 吞扫描错误 | **CLOSED** | 两个早退前已复制 `scan_errors/stat_failures`。[扫描分支](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:261) |
| stdout 绕过 | **CLOSED** | `scan_blocked` 无 `args.out` 条件直接 return 2，早于 stdout。[拒绝门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:755) |
| replace 异常清 tmp + parent fsync | **PARTIAL，整体 NOT-CLOSED** | replace 已纳入 try，也调用了 fsync；但 tmp、目标和 parent 仍分别按可变 pathname 重解析，且 fsync 发生在发布之后。[发布链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:801) |

## 指定反例结果

- **`deserialize` 一致性：NOT-CLOSED · HIGH。** verified fd 只绑定 inode，不产生数据库时间点快照。独立纯内存复现：两个同长 `5,365,760` 字节、各 30,000 行的合法 DB，按代码的 1 MiB 读取边界拼接后，`deserialize` 成功、`PRAGMA quick_check=ok`，却得到 `A=5,842 / B=24,158`，不属于任一源状态。同 inode 原地写即可产生可信外观的混合 QA 结论。

- **大小/内存：NOT-CLOSED · MEDIUM。** 没有 `st_size` 或累计读取上限；`chunks + join + CPython deserialize copy` 峰值至少约三份数据库字节。CPython 3.14.4 仅先检查 `len(data) <= 2^63-1`，随后按完整大小分配并复制，并无业务可用的输入上限。[CPython 实现](https://github.com/python/cpython/blob/v3.14.4/Modules/_sqlite/connection.c#L2191-L2206)

- **异常路径：NOT-CLOSED · MEDIUM。** 本机实测 4096 字节 garbage 可先 `deserialize_ok`，随后 `sqlite_master` 查询才抛 `DatabaseError`；当前查询段只有 `finally`，异常会逃逸。空 bytes 在 deserialize 阶段产生无消息 `MemoryError`。WAL header `2/2` 同样在使用时失败；SQLite 明确说明反序列化输入不应处于 WAL mode。[SQLite deserialize](https://www.sqlite.org/c3ref/deserialize.html)

- **`O_NONBLOCK` 普通文件：CLOSED／无新增缺陷。** 它不会提供异步或一致快照语义；普通文件仍按常规方式读取。其作用只是避免 FIFO/device 在 `fstat` 前阻塞，随后 `S_ISREG` 再拒绝特殊文件。[POSIX open](https://pubs.opengroup.org/onlinepubs/9799919799/functions/open.html)

- **parent fsync fd：NOT-CLOSED · HIGH。** fd 一旦成功打开便不会被后续换名“换掉”；问题是代码在 replace 后才按 pathname 打开它，可能一开始就打开了错误目录。若 replace 已成功而 parent open/fsync 失败，输出已经发布，却返回 2 并打印“原子替换失败、已清理”——执行状态与报告不一致。

- **父目录 retarget：NOT-CLOSED · BLOCKER（保留项）。** containment、tmp create、replace、parent fsync 四阶段均重新解析 pathname。父目录在检查后被换入 transcripts 子树，并在新目录预置同名 tmp，即可让 replace 修改恢复源区域。POSIX 提供 `renameat`/directory fd 正是为消除此类路径竞态。[POSIX rename](https://pubs.opengroup.org/onlinepubs/9799919799/functions/rename.html)

- **相对路径 / `dirname('.')`：稳定 namespace 下 CLOSED。** `abspath + realpath` 能正确处理 `ledger.json`、`./ledger.json`、`a/../ledger.json`。但 `--out .` 或 `/` 最终在 `Path.with_name()` 抛未捕获 `ValueError`，为 **LOW**。

- **挂载点：PARTIAL。** 词法上位于 transcripts 根内的普通挂载路径仍会命中根；但若 transcripts 的某个子目录被 bind/nullfs 到根外 alias，alias 的祖先 inode 不含 transcripts 根，无竞态即可绕过，故一般 containment **NOT-CLOSED · BLOCKER**。

- **循环 symlink：PARTIAL。** 稳定循环通常在 `is_dir`/open 阶段以 `ELOOP` 拒绝，不会写；解除或 retarget 循环仍归入上述 pathname TOCTOU。

- **可预测 tmp + `O_EXCL`：PARTIAL。** 预置 symlink 不会被跟随写入，狭义攻击 **CLOSED**；但可造成稳定 DoS。更严重的是 tmp 打开后可被 unlink/rebind：fd 写入 inode A，`os.replace(tmp_path, out)`却可能发布 inode B，仍为 **HIGH**。

- **两个进程同 PID：NOT-CLOSED。** 同时创建时一方 `EEXIST`；第一方 replace 后名字释放，第二方又可创建并最终 last-writer-wins。不同 PID 本来就能并行发布；跨 PID namespace 共享卷可出现同 PID。没有唯一发布者、锁或 CAS。

- **异常清理：NOT-CLOSED · MEDIUM。** `unlink` 失败被吞、清理目录未 fsync、SIGKILL/掉电仍可留 tmp；父目录被换后，清理还可能删除错误目录中的同名对象。

## 冻结 ledger 独立复算

没有调用生成器，也没有读取 transcript 正文。

| 项目 | 独立结果 |
|---|---|
| ledger | 142,508 bytes；SHA-256 `b8f042c6…95a6c287`；当前 mode `0600`、nlink 1 |
| live DLQ | 99,915 bytes；SHA-256 `3b37460f…ef3ba590`，与 [ledger header](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:6)一致 |
| records / unparseable | **92 / 0** |
| class | **89 / 2 / 1**，unexpected 0 |
| recoverability | **byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0** |
| attribution | **3**，全部 `no_token` |
| duplicates | **6 簇 / 29 条**；簇大小 `16,4,3,2,2,2` |
| 逐条对账 | stable key、class、inline、recoverability、冲突原因、transcript match count：**0 mismatch** |
| QA DB | 16,384 bytes；SHA-256 `6cb5510d…957a6a05`；header `1/1`、当前无 WAL/SHM/journal；`qa_error_logs=0` |
| QA ledger 字段 | `read_mode=in_memory_deserialize_from_verified_fd`、`bytes_read_from_verified_fd=16384` 均正确，[QA 段](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:164) |
| tmp 残留 | **0** |

QA SHA 不在 ledger 自身，只在 [shasums evidence](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/shasums-after.txt:5)；本次现态已复核，但 ledger 单文件并不能长期自证 QA exact bytes。

## 达到可验收的最小剩余项

必需：

1. **一致、有限的 QA snapshot**：使用身份绑定的 SQLite read transaction/backup 语义，或只接受外部已冻结、digest-bound、quiescent 的 DB；raw fd 分块读不能算数据库快照。显式拒绝 WAL/journal/并发变化，设置读取上限，所有 read/join/deserialize/query 异常统一 fail-closed。
2. **单一稳定目录对象发布**：输出 parent 在检查前以 `O_DIRECTORY|O_NOFOLLOW` 打开并验证；create/replace/unlink/fsync 全部相对同一个 dirfd。对 mount alias 要么检测拒绝，要么把输出限制到受信、不可换链的专用根。
3. **绑定 tmp、发布者与状态**：可信私有目录、不可预测或 unnamed tmp、same-FD readback hash；单写者锁/CAS；明确 `tmp durable → published → parent durable`，fsync 失败必须报告 `published_but_durability_unconfirmed`，并有崩溃残留 reconciliation。
4. **真实入口验收证据**：提交覆盖混合 DB、WAL、malformed/oversize、parent retarget、mount alias、tmp rebind、同/不同 PID、replace/fsync/unlink 故障的生产 `main()` 测试。当前仓库没有任何测试引用该生成器。
5. **修正声明**：脚本与 [UAT](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:32) 仍写 SQLite URI `mode=ro`；实际只有源 fd 为只读，内存连接可写。应改字段为 `source_fd_opened_readonly`，并把 QA SHA 写入 ledger。

建议：

- 内存连接设置 `PRAGMA query_only=ON`，并运行完整性检查；但 `quick_check` 不能替代一致快照。
- 增加 `O_CLOEXEC`、显式拒绝空 basename、随机 tmp 名。
- 随机名或 `O_EXCL` 单独都不足以解决共享可写目录中的名字重绑。

本轮未修改、创建或删除任何文件；开始和结束均只有预先存在的未跟踪 round-9 文档。`graphiti-canvas` 未在本会话暴露，无法执行其 memory search；Sequential Thinking 已完成。


