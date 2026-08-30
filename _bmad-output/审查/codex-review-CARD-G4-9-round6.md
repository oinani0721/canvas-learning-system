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
session id: 01a04854-b174-7322-845c-03a6bda66b21
--------
user
CARD-G4-9 round-6 复审（静态审阅 + 只读复算，禁改任何文件）。你 round-5 裁定 3/8 CLOSED，提出 2 BLOCKER / 2 HIGH / 2 MEDIUM / 3 LOW，并明确该阻断与只读 census 卡范围相称（因报告/UAT 承诺纯只读零写入，残留反例能截断或修改本卡正在保护的恢复源）——开发方接受该论证并以 commit 4c125f19 提交整改。请逐条只读复核：
1. BLOCKER token 冲突/无 token 扫描前早退 → resolve_group_attribution 重写为先扫描后判定：无条件对每个 token 遍历收集候选进 all_candidate_paths（保护集口径），再做 no_token/token_conflict/scan_errors/stat_failures/unreadable/多命中判定；候选 stat 失败改 exit 2。
2. BLOCKER qa_metrics.db 身份未绑定 → probe_qa_metrics 改 os.open(O_RDONLY|O_NOFOLLOW|O_NONBLOCK) 取 fstat 身份 + S_ISREG 门 → SQLite 打开后复核 os.stat 身份仍等于该身份，不等则 identity_changed_..._refused；身份入 protected_ids。
3. HIGH anomaly 吞不可见性 → 判定链改可见性优先：attribution_conflict 分支置于 anomaly 之前，一律 unverifiable，basis 区分 no_token/token_conflict/scan_errors/stat_failures/unreadable/ambiguous 并附注 inline 是否 anomaly。
4. HIGH fchmod 先于碰撞检查 → 碰撞检查前移至 fchmod 之前。
5. MEDIUM QA DB 特殊文件门 → 随 #2 加 S_ISREG+O_NONBLOCK。
6. MEDIUM 无 token 判不可恢复 → 改 unverifiable + no_token 标记。
7. LOW ×3 → 单独 LF 算 1 空行；inline/full_body 改 strict encode（堵 escaped lone surrogate 伪造 full_verified）；bool 排除出长度门。
请对每项设计静态反例判断是否仍可绕过。同时复核台账数字：92 条 / class 89-2-1 / byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0 / 重复簇 6/29 / unparseable 0；并核对新出现的 attribution_conflict=3（3 条 callout_annotation 无 session token，判 no_token 但因 inline 全量仍 byte_exact）——该口径变化是否诚实且自洽。逐项 CLOSED/NOT-CLOSED + 总裁定 + 新发现分级；若可验收请明确说明。
**Planning read-only audit strategy**
**Verifying hidden skills and audit tools**
codex
我会把本轮作为严格只读复审：先锁定 `4c125f19` 的实际 diff 与生产入口，再分三条独立证据链复核安全反例、QA DB 身份绑定、台账精确复算；全程不改文件，也不把现有测试结论当作证明。最终会逐项给出 `CLOSED/NOT-CLOSED`、可复现证据和验收边界。
**Planning parallel tool discovery and update**
CARD-G4-9 round-6 只读复审：以提交对象、生产入口和独立复算为证据，禁止文件修改。
  → 读取既有审计记忆与 Graphiti 事实，锁定 round-5 判项和审阅边界
  • 核验 4c125f19 diff 与八类整改的生产入口语义
  • 设计并执行只读静态反例/隔离复算，逐项判定可绕过性
  • 从源数据独立复算 92 条台账、分类、精度、冲突与重复簇
  • 汇总 CLOSED/NOT-CLOSED、新发现分级与最终验收裁定
**Investigating codebase memory recall tools**
**Planning memory-based schema recall**
**Planning memory retrieval strategy**
**Planning parallel memory search commands**
codex
当前会话未暴露 `graphiti-canvas.search_memory_facts`，所以我无法伪称已执行该协议；我会用已提供的项目记忆检索作只读替代，并把这个工具缺口列入审阅限制。现在先对 round-5 证据与本次八项声明建立可证伪检查矩阵。
exec
/bin/zsh -lc "rg -n -i 'CARD-G4-9|round-5|census|attribution_conflict|qa_metrics|resolve_group_attribution|4c125f19' /Users/Heishing/.codex/memories/MEMORY.md" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
84:- Missing handoff is a hard wait condition, not implied approval. `ps` was sandbox-denied (`operation not permitted`); mark the census unavailable rather than successful. [Task 1]
144:- “只读” means no repo/index/ref/worktree/OpenSpec writes, scanner/final census, A01/A02 instantiation, private/Vault/network/Graphiti access, or product implementation. Provide ready/blocked status, exact evidence, batch order, and Claude/Codex matrix. [Task 1]
148:- Order: `GOV-01-VERIFIED clean candidate → OpenSpec → schema/checker → A01 boundary receipt → no-cap census/A01 snapshot → A02 seed/replay → ChatGPT blind review → Codex reconciliation → user dispute/waiver → joint A01/A02 completion → A03 candidate → user exact-byte lock`. A01 cannot complete independently of A02. [Task 1]
153:- Expired `pending-user-confirmation` receipt/envelope is not authority. New exact envelope/digest/challenge is needed. The existing `scripts/bmad/scan_feedback.py` did not cover actual output; freeze a new scanner contract/no-write boundary before census. [Task 1]

mcp: codebase-memory/brief started
mcp: codebase-memory/brief (completed)
mcp: codebase-memory/recall started
mcp: codebase-memory/recall (completed)
mcp: sequential-thinking/sequentialthinking started
mcp: sequential-thinking/sequentialthinking (completed)
**Searching memory around canvas-adversarial-audit**
exec
/bin/zsh -lc "rg -n -i -C 4 'canvas-adversarial-audit|adversarial|exact-byte|no-write boundary|annotation-truth' /Users/Heishing/.codex/memories/MEMORY.md" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
1-# Task Group: Canvas Learning System long-running cross-model orchestration and productivity governance
2-scope: Evidence-first audit of project readiness plus a bounded 24-hour writer/reviewer orchestration design. The frozen runbook supports only a Bootstrap-Prep authorization request, not execution.
3-applies_to: cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output; reuse_rule=revalidate checkout, SHA, CI, unresolved findings, and current authorization before reuse; never treat this historical runbook as permission to create roots, clones, or run agents.
4-
5:## Task 1: Full-project adversarial audit and productivity direction, partial
6-
7-### rollout_summary_files
8-
9:- rollout_summaries/2026-08-19T18-23-31-2Aoh-canvas_learning_system_adversarial_audit_and_24h_orchestrati.md (cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output, rollout_path=/Users/Heishing/.codex/sessions/2026/08/20/rollout-2026-08-20T02-23-31-01a01b43-9daa-7ef1-8e35-587f59df3ec1.jsonl, updated_at=2026-08-24T13:41:20+00:00, thread_id=01a01b43-9daa-7ef1-8e35-587f59df3ec1, outcome=partial; audit and plan only)
10-
11-### keywords
12-
13-- Canvas Learning System, multi-vault, RAG, Graphiti, FSRS, Excalidraw, Karpathy, vault admission, SnapshotV3, CURRENT_TASK.md, 32280954498
--
15-## Task 2: 24-hour cross-model orchestration authorization design, success / request-only
16-
17-### rollout_summary_files
18-
19:- rollout_summaries/2026-08-19T18-23-31-2Aoh-canvas_learning_system_adversarial_audit_and_24h_orchestrati.md (cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output, rollout_path=/Users/Heishing/.codex/sessions/2026/08/20/rollout-2026-08-20T02-23-31-01a01b43-9daa-7ef1-8e35-587f59df3ec1.jsonl, updated_at=2026-08-24T13:41:20+00:00, thread_id=01a01b43-9daa-7ef1-8e35-587f59df3ec1, outcome=success; PASS_FOR_BOOTSTRAP_PREP_REQUEST only)
20-
21-### keywords
22-
23-- ORCH-BOOTSTRAP-PREP-V1, ORCH-SETUP-V1, ORCH-RUN-V1, non-LLM supervisor, app-server, Agent SDK, approval projection, setup-root-claim-v1, run-activation-claim-v1, O_NOFOLLOW, fencing token, no_auto_resume
--
124-
125-- `O_EXCL` plus `RENAME_EXCL` does not establish unique adopter or crash recovery. R2 found fixed temp `EEXIST` after pre-rename crash, nonsealed post-rename/pre-parent-fsync restart, no durable claim/reconciler, no write-side same-FD readback, and mutation-parent TOCTOU. Therefore `[ROLLUP:CACHE-PREP-V1:S3:R2-TECH] FAIL / BLOCKED`. [Task 2]
126-- Do not infer cache-object adoption from direct-SRI admission or node_modules protections. [Task 2]
127-
128:# Task Group: Canvas Learning System Phase 0A annotation-truth governance ready queue
129-scope: Read-only, fail-closed planning for GOV-01-VERIFIED and A01→A02→A03. It is a governance handoff, not execution authority.
130-applies_to: cwd=/private/tmp/cls-gov01-a4-v1/planning-ro; reuse_rule=revalidate commit, envelope, receipts, OpenSpec, scanner/checker contracts, and user authorization before acting.
131-
132-## Task 1: Phase 0A ready-queue audit, handoff delivered while execution blocked
--
136-- rollout_summaries/2026-08-23T07-48-49-AAp8-phase0a_ready_queue_readonly_governance_audit.md (cwd=/private/tmp/cls-gov01-a4-v1/planning-ro, rollout_path=/Users/Heishing/.codex/sessions/2026/08/23/rollout-2026-08-23T15-48-49-01a02d97-f8f2-74c2-ba02-41c9534f2366.jsonl, updated_at=2026-08-23T08:08:15+00:00, thread_id=01a02d97-f8f2-74c2-ba02-41c9534f2366, outcome=success; handoff only)
137-
138-### keywords
139-
140:- GOV-01-VERIFIED, Phase-0A, A01, A02, A03, annotation-truth-ledger-v2, AtomicAnnotation, boundary receipt, scanner, [HANDOFF:CODEX-PHASE0A-READY]
141-
142-## User preferences
143-
144-- “只读” means no repo/index/ref/worktree/OpenSpec writes, scanner/final census, A01/A02 instantiation, private/Vault/network/Graphiti access, or product implementation. Provide ready/blocked status, exact evidence, batch order, and Claude/Codex matrix. [Task 1]
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
155:# Task Group: Canvas Learning System P1-05/P1-01/P1-08 adversarial security review
156-scope: Read-only, parallel audit of vault admission/indexing, Graphiti quarantine isolation, SnapshotV3, and recovery-anchor closure claims.
157-applies_to: cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output; reuse_rule=revalidate SHA, CI, actual call sites, and live Neo4j state in the target checkout.
158-
159:## Task 1: P1-05c/P1-01/P1-08 parallel adversarial review, closure rejected
160-
161-### rollout_summary_files
162-
163:- rollout_summaries/2026-08-17T01-56-07-ZNCd-agents_guide_and_p1_05c_adversarial_audit.md (cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output, rollout_path=/Users/Heishing/.codex/sessions/2026/08/17/rollout-2026-08-17T09-56-07-01a00d6e-ea40-70a1-a23c-d51342eeeacd.jsonl, updated_at=2026-08-19T17:56:56+00:00, thread_id=01a00d6e-ea40-70a1-a23c-d51342eeeacd, outcome=partial; final read-only verdict)
164-
165-### keywords
166-
167-- P1-05c, P1-05, P1-01, P1-08, check_vault_path, vault_index_orchestrator, LanceDB, Graphiti, DEFAULT_GROUP_ID, SnapshotV3, CURRENT_TASK.md
168-
169:## Task 2: P1-05b five-question adversarial audit, reproducible bypasses
170-
171-### rollout_summary_files
172-
173:- rollout_summaries/2026-08-19T14-44-08-upza-p1_05b_adversarial_review_finds_admission_quarantine_snapsho.md (cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output, rollout_path=/Users/Heishing/.codex/sessions/2026/08/19/rollout-2026-08-19T22-44-08-01a01a7a-c47f-70e2-8e5e-524e1591da78.jsonl, updated_at=2026-08-19T15:12:50+00:00, thread_id=01a01a7a-c47f-70e2-8e5e-524e1591da78, outcome=partial; detailed counterexamples)
174-
175-### keywords
176-
177-- P1-05b, symlink_escape, casefold, vault_backfill, lancedb_client, quarantine__p105b, search_nodes, read_node_tips, manifest-v3, NaN
--
182-- Respect read-only task-book boundaries, WT/MAIN labels, explicit `UNVERIFIABLE`, and no raw-vault access; do not fix code in the audit. [Task 1]
183-
184-## Reusable knowledge
185-
186:- Related skill: skills/canvas-adversarial-audit/SKILL.md. P1-05/P1-01/P1-08 remained STILL-OPEN; F-02 tombstone filtering and F-05 live resilience were closed. Rejected vault inputs must show zero open/hash/index/write. [Task 1][Task 2]
187-- Reproduced: `vault/raw/escape.md -> /outside/secret.md` was counted by `backfill_vault(..., execute=False)`; case-sensitive `fnmatch` admitted `.CLAUDE/SKILL.md` and `raw/claude.md`. Edge filtering alone was insufficient because exact readers/node search could cross Graphiti groups. [Task 2]
188-- SnapshotV3 needs invalid/future same-generation self-healing, extra-field, strict-type, huge finite mastery, and identity/length collision coverage. [Task 1][Task 2]
189-
190-## Failures and how to do differently
--
199-## Task 1: Create AGENTS.md, completed
200-
201-### rollout_summary_files
202-
203:- rollout_summaries/2026-08-17T01-56-07-ZNCd-agents_guide_and_p1_05c_adversarial_audit.md (cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output, rollout_path=/Users/Heishing/.codex/sessions/2026/08/17/rollout-2026-08-17T09-56-07-01a00d6e-ea40-70a1-a23c-d51342eeeacd.jsonl, updated_at=2026-08-19T17:56:56+00:00, thread_id=01a00d6e-ea40-70a1-a23c-d51342eeeacd, outcome=success)
204-
205-### keywords
206-
207-- AGENTS.md, frontend/obsidian-plugin, backend/app, agentic_rag, backend/tests, verify:spec, lefthook

**Inspecting memory skill file contents**
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

**Assigning concrete inspection tasks**
**Delegating parallel audit tasks**
codex
我已加载既有对抗审阅清单：本轮会坚持“生产入口、最小反例、`file:line`、独立高危复核”，并明确保留 `UNVERIFIABLE`。接下来并行检查三块：归因/可见性、SQLite 身份/发布顺序、台账与三项低风险口径；我会同时核对提交对象和汇总生成链。
**Planning parallel git inspections**
exec
/bin/zsh -lc 'git rev-parse HEAD' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
4c125f19dd6b189c7dcdfa3bff686cbd494a11cc

exec
/bin/zsh -lc 'git show --no-ext-diff --format=fuller --no-patch 4c125f19' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
commit 4c125f19dd6b189c7dcdfa3bff686cbd494a11cc
Author:     oinani0721 <2272104243@qq.com>
AuthorDate: Fri Aug 28 20:24:20 2026 +0800
Commit:     oinani0721 <2272104243@qq.com>
CommitDate: Fri Aug 28 20:24:20 2026 +0800

    fix(census): G4-9 Codex round-5 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9]
    
    2 BLOCKER: resolve_group_attribution 改先扫描后判定(token 冲突/无 token 的
    候选亦入 all_candidate_paths→保护集; 候选 stat 失败 exit 2 不再吞);
    probe_qa_metrics 改 fd 取身份+S_ISREG 门+SQLite 打开后复核身份一致。
    2 HIGH: 判定链改可见性优先(归因不可核验一律 unverifiable, 无论 inline 是否
    anomaly, basis 逐条写明原因); fchmod 后置于 protected-id 碰撞检查(原顺序会
    先把只读输入权限从 644 改 600 再拒绝)。
    2 MEDIUM: QA DB 特殊文件门; 无 token 归 unverifiable 而非 unrecoverable。
    3 LOW: 单独 LF 算 1 空行; strict encode 堵 lone surrogate 伪造 full_verified;
    bool(int 子类)不再通过长度门。
    6 条新反例实测全过。第五次全量重跑 92/4-88-0-0/89-2-1/6-29/shasum 不变;
    归因冲突 0→3 系 no_token 标注变诚实(3 条 callout 仍 byte_exact), 三态不变。
    
    Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>

exec
/bin/zsh -lc 'git rev-parse 4c125f19''^' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
d8d887f29377b8babc49f5dda0d4c4ba01168ad3

exec
/bin/zsh -lc 'git diff-tree --no-commit-id --name-status -r 4c125f19' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
M	"_bmad-output/\345\256\241\346\237\245/G4-9-DLQ-census-2026-08-28.md"
M	"_bmad-output/\345\256\241\346\237\245/G4-9-dlq-ledger-2026-08-28.json"
M	"_bmad-output/\345\256\241\346\237\245/G4-9-evidence/census-stderr.txt"
A	"_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round5.md"
M	"_bmad-output/\351\252\214\346\224\266\345\215\225/UAT-CARD-G4-9-DLQ\347\234\237\345\256\236\346\214\202\350\275\275census\345\210\206\350\257\212-2026-08-28.md"
M	backend/scripts/census_dead_letter_episodes.py

exec
/bin/zsh -lc 'git status --short --branch' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
## card/s5-census
?? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round6.md"

exec
/bin/zsh -lc 'git show --stat --oneline --decorate --no-renames 4c125f19' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
4c125f19 (HEAD -> card/s5-census) fix(census): G4-9 Codex round-5 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9]
 .../G4-9-DLQ-census-2026-08-28.md"                 |   16 +
 .../G4-9-dlq-ledger-2026-08-28.json"               |   27 +-
 .../G4-9-evidence/census-stderr.txt"               |    2 +-
 .../codex-review-CARD-G4-9-round5.md"              | 3419 ++++++++++++++++++++
 ...75census\345\210\206\350\257\212-2026-08-28.md" |   16 +
 backend/scripts/census_dead_letter_episodes.py     |  240 +-
 6 files changed, 3628 insertions(+), 92 deletions(-)

exec
/bin/zsh -lc "rg --files -g 'AGENTS.md' -g 'CURRENT_TASK.md' -g '*CARD-G4-9*' -g '*card*g4*' -g '*census*' -g '*qa_metrics*'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
CURRENT_TASK.md
_decisions/CURRENT_TASK.md
_bmad-output/审查/2026-08-19-P1-05b-Graphiti污染盘点census报告.md
_bmad-output/审查/r11-evidence-2026-08-17/d2-dead-letter-census.md
_bmad-output/审查/G4-16-doc-type-census-2026-08-28.md
_bmad-output/审查/codex-review-CARD-G4-9-round4.md
_bmad-output/审查/codex-review-CARD-G4-9-round5.md
_bmad-output/审查/G4-9-evidence/census-stderr.txt
_bmad-output/审查/codex-review-CARD-G4-9.md
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md
_bmad-output/审查/codex-review-CARD-G4-9-round3.md
_bmad-output/审查/codex-review-CARD-G4-9-round6.md
_bmad-output/审查/codex-review-CARD-G4-9-round2.md
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md
backend/scripts/census_graphiti_pollution.py
backend/scripts/census_dead_letter_episodes.py

**Identifying untracked review file presence**
**Checking review file creation time**
**Planning detailed script inspection**
exec
/bin/zsh -lc 'wc -l backend/scripts/census_dead_letter_episodes.py _bmad-output/审查/codex-review-CARD-G4-9-round5.md _bmad-output/审查/G4-9-DLQ-census-2026-08-28.md _bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
     729 backend/scripts/census_dead_letter_episodes.py
    3419 _bmad-output/审查/codex-review-CARD-G4-9-round5.md
     179 _bmad-output/审查/G4-9-DLQ-census-2026-08-28.md
    2659 _bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json
    6986 total

exec
/bin/zsh -lc "rg -n '"'^def |''^class |resolve_group_attribution|probe_qa_metrics|fchmod|protected_ids|attribution_conflict|full_verified|empty|bool|anomaly|unverifiable|unrecoverable'"' backend/scripts/census_dead_letter_episodes.py" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
20:  - inline 三态: full_verified 要求 sha 对账通过 **且** len(body)==声明长度;
22:    且声明长度>200; 其余一律 anomaly。anomaly 不落 approximate —— 裁
23:    unrecoverable 并显式给 anomaly basis（不谎称"截断前缀"）。
30:    前缀），否则记 attribution_conflict、拒绝采信任何 transcript；
33:    （chmod 000）时整体 exit 2（拒绝在源不可见时产出 unrecoverable 假象）；
38:    重算 sha **且长度**双门对账通过才按 byte_exact 采信，且 anomaly 记录
77:def _split_jsonl_lines(raw: bytes) -> list[tuple[str, str | None]]:
100:def classify(rec: dict) -> str:
113:def inline_state(rec: dict) -> tuple[str, str]:
117:        return "anomaly", "FAIL"
120:    sha_wellformed = isinstance(declared_sha, str) and bool(_SHA256_HEX_PAT.match(declared_sha))
122:    # (\udXXX) 改写成 replacement char，可被构造出"对得上账"的假 full_verified。
123:    # 改 strict：无法编码即判 anomaly。
127:        return "anomaly", "FAIL"
129:    len_ok = isinstance(declared_len, int) and not isinstance(declared_len, bool)
131:        return "full_verified", "pass"
134:    return "anomaly", "FAIL"
137:def full_body_verified(rec: dict) -> bool:
148:    # round-5 LOW 整改: bool 是 int 子类 —— episode_body_length=True 会通过长度门
149:    if not isinstance(declared_len, int) or isinstance(declared_len, bool) or len(full) != declared_len:
158:def session_tokens(name: object) -> list[str]:
170:def resolve_group_attribution(tokens: list[str], transcripts_dir: Path) -> dict:
183:        "attribution_conflict": False,
230:        result["attribution_conflict"] = True
236:        result["attribution_conflict"] = True
243:        result["attribution_conflict"] = True
247:        result["attribution_conflict"] = True
251:        result["attribution_conflict"] = True
260:        result["attribution_conflict"] = True  # ambiguous 多命中，拒绝采信
264:def probe_qa_metrics(db_path: Path, error_types: list[str]) -> tuple[dict, tuple[int, int] | None]:
323:def snapshot_file(path: Path) -> tuple[bytes, dict, tuple[int, int]]:
359:def describe_copy(path: Path) -> tuple[dict, tuple[int, int] | None]:
367:def main(argv: list[str] | None = None) -> int:
406:    # 并把全部记录假判 unrecoverable —— 同样 fail-closed 拒诊。
414:    protected_ids: set[tuple[int, int]] = set()
426:                protected_ids.add((cst.st_dev, cst.st_ino))
442:            if (out_st.st_dev, out_st.st_ino) in protected_ids:
455:    protected_ids.add(dlq_identity)  # 保护的是**实际读取对象**，非路径快照
498:        group_attribution[key] = resolve_group_attribution(tokens, transcripts_dir)
504:    unrecoverable_keys = []
505:    unverifiable_keys = []
506:    attribution_conflicts = []
518:        if state == "full_verified":
521:        elif state != "anomaly" and full_body_verified(rec):
524:        elif sess["attribution_conflict"]:
525:            # round-5 HIGH 整改: 可见性判定**优先于** anomaly —— 源看不见时
527:            recover = "unverifiable"
540:            extra = "；inline 亦对不上账（anomaly）" if state == "anomaly" else ""
542:        elif state == "anomaly":
543:            recover = "unrecoverable"
544:            basis = "inline 对不上账（anomaly：sha/长度与声明不符），且归因扫描完整可见但无可用源"
553:            recover = "unrecoverable"
563:        if recover == "unrecoverable":
564:            unrecoverable_keys.append(stable_key)
565:        elif recover == "unverifiable":
566:            unverifiable_keys.append(stable_key)
567:        if sess["attribution_conflict"]:
568:            attribution_conflicts.append(stable_key)
587:                "attribution_conflict": sess["attribution_conflict"],
610:            protected_ids.add(cid)
613:        qa_probe, qa_identity = probe_qa_metrics(
618:            protected_ids.add(qa_identity)  # 保护实际验证过的对象身份
648:            k: recover_dist.get(k, 0) for k in ["byte_exact", "approximate", "unverifiable", "unrecoverable"]
651:            k: inline_dist.get(k, 0) for k in ["full_verified", "truncated_prefix", "anomaly"]
653:        "unrecoverable_list": unrecoverable_keys,
654:        "unverifiable_list": unverifiable_keys,
655:        "attribution_conflicts": attribution_conflicts,
667:                protected_ids.add((tst.st_dev, tst.st_ino))
676:                protected_ids.add((tst.st_dev, tst.st_ino))
696:            # round-5 HIGH 整改: 碰撞检查必须**先于** fchmod —— 否则 --out 指向
698:            if (st.st_dev, st.st_ino) in protected_ids:
706:                os.fchmod(fd, 0o600)
720:        f"recoverability={dict(recover_dist)} | 归因冲突={len(attribution_conflicts)} | "

exec
/bin/zsh -lc "rg -n '"'^#{1,4} |BLOCKER|HIGH|MEDIUM|LOW|3/8|总裁定|CLOSED|NOT-CLOSED'"' _bmad-output/审查/codex-review-CARD-G4-9-round5.md" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
14:CARD-G4-9 round-5 终裁复审（静态审阅 + 只读复算，禁改任何文件）。你 round-4 裁定 1/6 CLOSED，提出 2 BLOCKER / 1 HIGH / 2 MEDIUM / 3 LOW。开发方以 commit d2827a6d + d8d887f2 提交整改，请逐条只读复核：
15:1. BLOCKER 不可读但可写 transcript 绕过保护集 → resolve_group_attribution 新增 all_candidate_paths（保留所有见到的候选，含 unreadable 与被冲突分支清空的），main() 写出前遍历 group_attribution 全部并入 protected_ids。
16:2. BLOCKER 源侧 TOCTOU → snapshot_file() 改 os.open(O_RDONLY|O_NOFOLLOW|O_NONBLOCK) → fstat 取 (st_dev,st_ino) + S_ISREG 门 → 从同一 fd os.read 全量，返回身份即实际读取对象，DLQ 与 compare 副本均以该身份入 protected_ids；输入 stat 失败改 exit 2 不再静默吞。
17:3. HIGH 不可见终态化 → 新增第四态 unverifiable（扫描受阻/不可读候选/归因冲突），recoverability_distribution 与 unverifiable_list 同步，basis 逐条说明原因。
18:4. MEDIUM FIFO/设备 → --out 与读侧均加 S_ISREG + O_NONBLOCK。
19:5. MEDIUM 非法 UTF-8 → _split_jsonl_lines 改逐行 strict decode，失败归 unparseable。
20:6. LOW ×3 → 字段错型防御（name 非 str / request_id 不可哈希 / episode_body 非 str）、根为 '/' 的 containment 特例（root_prefix）、既有输出 fchmod 0600。
21:7. LOW provenance → 后置 receipt _bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt 记录精确 SHA 链，报告头指向它。
22:请对每项设计静态反例判断是否仍可绕过（尤其：保护集完整性、fd 身份与实际读取的绑定、unverifiable 与 unrecoverable 的语义边界、strict decode 的边界）。同时独立复算台账仍为 92 条 / class 89-2-1 / byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0 / 重复簇 6 簇 29 行 / unparseable 0。逐项 CLOSED/NOT-CLOSED + 总裁定（可验收/仍阻断）+ 新发现分级。若已可验收请明确说明；若仍阻断请说明**对一张只读 census 卡**而言该阻断是否与卡面范围相称。
128:# Canvas adversarial audit
130:## When to use
134:## Inputs / context to gather
140:## Procedure
150:## Efficiency plan
156:## Pitfalls and fixes
163:## Verification checklist
217:    2 BLOCKER: 全候选(含 mode 0200 不可读但可写)并入 --out 保护集; snapshot_file
218:    改 fd 读取(O_RDONLY|O_NOFOLLOW|O_NONBLOCK → fstat 取身份 → 同 fd 读全量),
220:    1 HIGH: 新增 unverifiable 第四态 — 扫描受阻/不可读候选/归因冲突不再终态化为
222:    2 MEDIUM: --out 与读侧均加 S_ISREG+O_NONBLOCK 门(FIFO/设备); JSONL 逐行
224:    3 LOW: 字段错型防御(name=None/request_id 不可哈希/episode_body 非 str);
248:    Codex round-4 LOW: commit 无法自含己身 SHA，报告头的模糊代称不能冒充精确
283:# branch.oid d8d887f29377b8babc49f5dda0d4c4ba01168ad3
284:# branch.head card/s5-census
299:# CURRENT_TASK: Canvas Learning System × Obsidian Hybrid（回归路径）
320:  **① P1-05 第四轮返工（P1-05d）已落地，待五轮终裁** — Codex 四轮（`2026-08-19` 终裁文档）判 F-02/F-05 CLOSED、其余 STILL-OPEN；九路验证（`2026-08-20-Codex四轮终裁-九路验证与C批次方案.md`）9/9 CONFIRMED 含 B3 新回归一条。C 批全部落地：**C2**（`1683328c`：脏 last_examined 投影 None 止血 B3 新回归 · freshness 嵌套错型自愈 · 5 处 ID 切片改丢弃 · _id_ok 写侧过滤同源 · lag_seconds finite · 控制字符全拒）· **C3**（`d39983ce`：conversation_summary caller 显式传 vault 组修恒空 bug · ensure_entity_node 隔离身份拒绝复用）· **C1**（`c154a7f2`：lib 层 _resolves_outside_vault 接 LanceDB 两真实入口 open 前 · orchestrator 裸 fnmatch 换 canon + 扫描产出过 should_index 根除 hash-before-admission + realpath containment · by-node missing→404/path_rejected→422；新 test_real_entrypoint_admission.py 6 条真实入口行为锁）· **C4**（census Q2 中性化+前缀分类）。**遗留**：B4（payload 命名空间/provenance）独立轮 · TOCTOU 换链残余窗口（realpath 判定与 open 非原子，诚实登记）· P1-03/P1-04 押后
343:- 🔒 **[Code-Review] 独立对抗审查已收官**: APPROVE-WITH-FIXES；核心修复被证实无漏（六条 Cypher 全带键 / 物理格式链闭合 / 无 cypher_with_group_filter 误用 / 无 ContextVar 依赖 / 全仓无旁路写入点，11 条候选证伪）。F1 HIGH（exam sync-node 边写入空匹配谎报 edge_created=True）+ F2（迁移 edge 回填不继承端点 group）+ F3（空白 vault_id 绕必填）已在 **C3 `ad82529a`** 处置并加行为测试；F4（verify_targeted_exam_chain.py 裸 id MERGE）/ F5（DEPRECATED 前端 sync-engine 无限重试）/ F6（head(collect) 非确定边角）+ **exam sync-node vault_id 必填化（F1 根治）** 挂账 Phase 2
349:- ✅ **用户 8/8 全批**（R9 批注逐字）: ①P0-1 方案先行 ②E-2 快照选 **A**（只存投影安全面+秩数值，MEDIUM-2 悬案定案）③执行序改 Codex 8 步（P0 止血→数据边界→可信基线→证据修复→安全写入基建→分批落地→价值验证→缓行）④审批每轮只递 **6-8 项** ⑤A-2 扩容: mastery 提交前并入 tiktoken 断网兜底（compression.py:46 只捕 ImportError）+ nodes.py:97 timeout 200ms→按实测校准，WT 代码与 MAIN/.gitignore **分 commit** ⑥D-2 先按真实路径重数 DLQ（live=`WT/data/dead_letter_episodes.jsonl` 仅 1 条；`WT/backend/data/` 92 条为陈旧文件）⑦B-2 广度回顾先做**薄版 MVP**（只新增回顾报告文件，零改原白板/YAML，真实板试跑用户说「有帮到」再扩）⑧E-5 Dashboard webUI 入缓行区
366:  - ⛔ **HIGH-1 泄漏**: `score_scale` 形状白名单**只有头锚没尾锚**(`.match()` 无 `$`) ⇒ `1-4 反例 diag(-1,-1)…`（**G6 金集禁串**）整串原样透出 → `fullmatch` + 收紧文法 + 先验形状再截断
367:  - ⛔ **HIGH-2 静默劫持**: `mastery_a: .inf/.nan` ⇒ nan 比较恒 False 让 Timsort 保持输入序，投毒节点吃掉 `pick_rank=1` 且 `parse_errors` 空；自查另发现 exam JSON 吐**裸 NaN = 非法 JSON** → `_num` 加 `isfinite` 门 + 显式上报 + 秩过滤 + 严格 JSON 断言
368:  - ⛔ **D-HIGH-1 我自己的方法论错误**: 上一版「降级路径逐行相等」验的是**我修好的路径**——SKILL 的 Grep 当时没取 `last_examined`，闲置折旧在降级态整体失效 → 补字段 + **写脚本从 SKILL 正文抠出 Grep 与 python 直接执行**重验（三板逐字段相等，`idle=16.9d` 是折旧生效的证据）
370:  - ⛔ **D-MEDIUM-5 校验器只数信封不看信**: 掏空降级块/改坏 import/新增裸调用/把降级反转成「停止并叫用户起服务」六种腐烂全判绿 → 加 C6(按小节校 HARD-NAV-3)/C7(ast.parse + import 符号存在)/C8(禁中止语义)，**35 → 59 项**
371:  - 其余: MEDIUM-1 G8 子串判定被 `[推定]` 前缀绕过→改闭集 / MEDIUM-3 SKILL 把 manifest 划进可信面→新增 **HARD-ISO-5b** / D-HIGH-2 降级把占位也编秩致秩号错位→排序前剔除 / D-HIGH-3 反向引用 regex 未 `re.escape` 致含括号节点整批漏检→已修 / D-MEDIUM-4 缺 Concepts 段时 exit 0 还说「已同步」→抛异常+退出码分层 / C-H3 frontmatter 自由文本被逐字写进白板→只认真 wikilink / C-H4 与后端 7 条语义分歧→逐条对齐 / C-H5 批次非原子 / C-M7 无 fsync / C-M9 行尾归一 / C-M10 doc_count 只改首处 / C-M11-13 断链·孤儿·多 sentinel 静默→全改成告警且 `--check` 红 / C-M14 `.bak` 二次覆盖
373:- ⚠️ **待用户裁定（我没单方面改）**: 审查 MEDIUM-2 —— `view:"exam"` 调用**本身**把全量禁项原料明文落盘到 `<vault>/.claude/cache/`（真 vault 那份 22KB 快照含 G6 禁串明文，出题 agent 有 Read 权限）。本轮只做 prompt 级 **HARD-NAV-5**（禁读 `.claude/cache/`）+ gitignore；彻底修法二选一: **A** 快照只存投影安全面（代价: 降级态 study 视图丢 tips/errors）/ **B** 快照移出 vault 到 backend 侧（代价: 反转 2.5「落 .claude 双黑名单」的架构决定）
384:- 🔒 [Code-Review] 独立对抗审查（E2E 复现式）**3 HIGH / 3 MEDIUM / 5 LOW → 全部处置, 复验 32/32 全绿**: ⛔ H1 orphans 回显通道（source_board 塞定义全文进 exam 视图, 已复现）→ reason 定长枚举文案+raw 截断 120+模型 max_length 门; ⛔ H2 parse_errors 回显（last_examined repr 无界+纯 Python yaml loader str(e) 引用原文行含 correction 禁串）→ _safe_err 去内容化（异常类型+行号）+repr[:80]+模型 200 字门; ⛔ H3 untrusted 标量炸投影（`doc_count: 大约五个`/`title: 2026` → ValidationError 500 整端点含列板）→ _bounded_str 类型归一×7 字段+双暴露面 ValidationError 纵深兜底; M4 digest 吸入相邻 [!feedback]/[!hint] callout（可含正确答案）→ callout 边界终止收集; M6 #heading 锚点+大小写敏感→假孤儿（喂 H1 通道）→ resolve 剥锚点+boards_ci casefold 匹配; M7 金集合成A恒真条件（自比较）→ 改「挖掉 reason 槽位后 0 命中」; M8 禁串无正向对照会静默腐烂→禁串必须仍在 vault 源文件+G5 digest 非空对照（金集 31→32 条）; L 批: 快照 tmp 唯一名防竞态/load 快照 schema 必备键校验/exam_board_count 恒用 full 历史/信封字段统一截断/set_current_subject_id 移到 fail-close 之后。审查确认: 投影穿透 E2E 失败（防线真实）、快照双黑名单成立、serve 路径唯一、pick 数学锁死、无 DD-03 违规。新增回归锁 6 条（契约 77 绿）
396:- 🔒 [Code-Review] T6 全链路审查 **8 CONFIRMED / 2 REFUTED → 全部处置**: ⛔ **HARD-ISO live 泄漏**（vault_notes_retriever 默认排除表漏 exam_board, 经无鉴权 /api/v1/rag/query + agents.py 六处可达 → 补齐; react_agent/tool_executor/agent_graph 三条 flag-gated 链同批纵深补齐）; **fts_confirmed 名实颠倒**（_rrf_score 写给所有融合行, dense-only 恒 True/真词法命中反 False → _rrf_fuse 新 _fts_hit 通道标记 + 白名单 + svc 公式改 `_fts_hit and not _fts_only`, 仍遥测-only）; **检索层故障吞噬纵深**（_search_internal 全分支故障 raise 受 enable_fallback 门控[默认 True 调用方行为不变] + open_table 失败 raise + hook singleton 关吞噬/init 失败不缓存 + 空交付文案不再主动断言「检索正常」）; ⛔ **elbow telescoping = 三轮金集 A/B 裁决保留 T4 行为**（审查数学观点成立, 但两种修复均被金集打回: 全量序列 floor → 污染 39.83→57.38%/FPR 8%; dedup 后门前 floor → 48.25%/8%; +1.8pp 命中换不回 +8~17pp 污染 — 门后 telescoping 截断是净正收益保守护栏, 数据与翻案条件锁进 test_gate_thinning_elbow_is_deliberate_t4_behavior）; REFUTED×2: react_agent/agent_graph「拨真即泄漏」不可达（仍随批纵深补齐排除表）; LOW backlog: extended 分支无 taint / MCP top_k 参数漂移 10vs15 / TYPE_WEIGHTS concept 死键
404:- 🔒 [Code-Review] T5 独立对抗审查 2H/2M/2L → **全修**: HIGH-1 基础设施故障被吞成 ok_empty（fast client `enable_fallback=False` + `_two_tier_search` 两级全败 raise 走 search_failed + `_fast_path_search` embedding 预检恢复阶段0语义, 真实路径回归锁×2）/ HIGH-2 MCP 全文交付但 taint 只扫 300 字 snippet（content 挂载前移进扫描面, 交付面=扫描面）/ MEDIUM-3 tainted 材料 metadata 收窄（doc_type/source_type frontmatter 自由文本不随隔离材料外带）/ MEDIUM-4 enrich-context rerank 后 confidence 失真（摘除不渲染, 重算留待后续）; LOW-6 tier-2 legacy 表无 exam_board 排除 → backlog（env-gate 默认关, 暴露≈0）
410:- 🔒 [Code-Review] T4 workflow 审查（45 agent, 3维find+双盲证伪, 21报12实9拦）→ **全修**: HIGH 池挤占（放宽行挤出 raw≥0.50 正解, 修后交付 80→81.82%）/ AttributeError 逃逸契约+绕熔断（畸形200封堵）/ 英文chunk 1200字盲区（MaxP 3→5窗）/ dedup 丢被合并 chunk CE 证据 / 单测隐藏网络依赖 / ce_gate_all_filtered 观测区分 / CancelledError 熔断记账 / 6 条新回归锁（含池饱和等价+半开恢复+XML 不渗漏）。contracts 26+chunk 21 绿, unit svc 55 绿
416:- 🔒 [Code-Review] T3 独立对抗审查 0C/1H/2M/5L → **HIGH-1(YAML 解析失败绕过 exam_board 推断=泄漏复活, 已修嗅探兜底)+MEDIUM-1(紧贴 callout 吞批注, 已修断块)+MEDIUM-2(占位误杀, 已收紧)+LOW-4(tiktoken 冷启动, 已降级兜底) 全修**+4 红线测试; 未修 backlog: LOW-1 超长 EXTRACT 降级切分丢 [!question] 标记 / LOW-3 [!note] STRIP 误伤面待 census 复核 / LOW-5 建议 exam-quick.ts frontmatter 标量加引号(前端, 勿混本批)
509:## Round-22 弃用决策（2026-05-08）
511:### 弃用原因（双重证据）
516:### 路径对比
524:### archive 内容指针（DeepTutor worktree 仍保留）
535:## 从 DeepTutor worktree 迁移过来的 UAT v3.0 资产
633:# CURRENT_TASK — Sprint v3 接管状态（唯一真相源）
638:## §0 · v3.0 update — Sprint v3 v3 起步 (2026-05-26 ChatGPT 体系审查后)
642:### ⭐⭐ 2026-06-01 最新状态 — 新 session 从这里起步 S2-2
667:### 当前 Sprint 2 v3 状态 (2026-05-26 ChatGPT 体系审查后锁定)
676:### Sprint 2 v3 起步序列 (5 session 并行, Day 5-10)
688:### ChatGPT 体系级审查并行进行
694:### 5 必修包关键 file paths (Sprint 2 v3 起步必读)
706:### Sprint 2 v3 三波次 (ChatGPT 校正, 非纯 5 并行)
717:### ⚠️ V-07/V-08/V-10/V-11 旧修复方案状态 (重要 — 防新 session 误读)
724:### 接续上手 5 min 命令
731:# 选 session A/B/C/E 一个起步 (D 等 B done)
736:## §1 · 新 session 5 min 启动检查清单
745:## §2 · 当前状态（2026-05-24 Sprint v3 BMAD 化完成时）
757:## §3 · 接下来 8 步开干流程（新 session 第 1 个动作）
768:## §4 · BMAD 化进度（本 plan 2026-05-24 执行）
776:## §5 · 关键决策（用户 2026-05-22 锁定，新 session 必读）
792:114:    if not isinstance(body, str):  # round-4 LOW: episode_body 错型
801:144:    """round-4 LOW 整改: name 非 str（None/数字/列表）不再抛异常。"""
818:269:    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
830:424:        # round-4 LOW 整改: 不可哈希的 request_id（list/dict）按 line_no 单条成组
863:620:            fd = os.open(args.out, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
870:/bin/zsh -lc "rg -n 'BLOCKER|HIGH|MEDIUM|LOW|CLOSED|NOT-CLOSED|保护集|TOCTOU|UTF-8|unverifiable|unrecoverable|provenance|92|89|29' '_bmad-output/审查/codex-review-CARD-G4-9-round4.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
873:14:CARD-G4-9 round-4 终裁复审（静态审阅 + 只读复算，禁改任何文件）。你 round-3 裁定 4/6 CLOSED，两项 PARTIAL + 3 新发现。开发方以 commit fce0d8a2 提交整改，请只读复核这 6 项：
874:15:1. BLOCKER-1 绕过①（--out 指向已归因 transcript 会截断恢复源）→ 现在写出前把全部 records[].transcript_paths 的 (st_dev,st_ino) 并入 protected_ids。
875:16:2. BLOCKER-1 绕过②（check-then-open TOCTOU）→ 现在改 os.open(O_WRONLY|O_CREAT|O_NOFOLLOW) 不带 O_TRUNC 打开，对实际 fd 做 os.fstat 校验 inode 是否落在 protected_ids，通过后才 os.ftruncate(fd,0) 并 os.fdopen 写。请判断该顺序是否真正消除 TOCTOU，并找剩余绕过（如 O_NOFOLLOW 对中间路径组件、fd 竞争、非常规文件如 FIFO/设备）。
876:17:3. HIGH-3（glob 越根枚举 + 静默吞不可读子树 + mode 000 文件过 isfile）→ 现在改 os.walk(onerror=收集错误, followlinks=False) 手动匹配前缀，候选加 os.access(R_OK) 门，遍历错误或存在不可读候选一律 attribution_conflict + 清空 transcript_paths + 拒绝裁定。
877:18:4. 新 MEDIUM（JSONL framing）→ 新增 _split_jsonl_lines() 严格按 LF 分帧，header line_count 与 records 共用。
878:19:5. 新 LOW（非 dict JSON 炸全量）→ 非 dict 归 unparseable。
879:20:6. 新 LOW（provenance）→ 报告头补 artifact commit 链 67ccebe1→73102875→fce0d8a2。
880:21:同时独立复算台账 _bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json 仍为 92 条 / class 89-2-1 / 三态 4-88-0 / 重复簇 6 簇 29 行 / 归因冲突 0 / unparseable 0。逐项 CLOSED/NOT-CLOSED + 总裁定（可验收/仍阻断）+ 任何新发现分级。若认为已可验收请明确说明。
884:145:rg -n \"BLOCKER-1|HIGH-3|JSONL|framing|非 dict|provenance|PARTIAL|CLOSED|NOT-CLOSED|新发现|总裁定|protected_ids|O_NOFOLLOW|os\\.walk|line_count\" '_bmad-output/审查/codex-review-CARD-G4-9-round3.md' | head -n 240
885:160:14:CARD-G4-9 round-3 复审（静态审阅 + 只读复算）。你 round-2 裁定 10/13 CLOSED，三项 NOT-CLOSED：BLOCKER-1（--out 守卫比 resolve 字符串，hardlink 与 case-only 别名绕过截断输入）、HIGH-1（full_body_verified 只核 sha 不核长度且排在 anomaly 分支前，anomaly 记录被判 byte_exact）、HIGH-3（chmod 000 根 exit 0 假判 unrecoverable；glob 跟随 symlink 逃逸出根）；另 3 新 LOW（full_verified 长度范围应 131-180、distribution 省略 0 值键、line_count 数 LF 与 records 的 splitlines 口径不一）。开发方以 commit 73102875 提交整改。请只读复核这 6 项是否闭合：
886:162:17:请：逐项 CLOSED/NOT-CLOSED（对每项设计静态反例判断是否仍可绕过，如相对路径/大小写/软硬链接组合、判定链其它入口、glob 边界）；独立复算台账仍为 92 条 / class 89-2-1 / 三态 4-88-0 / 重复簇 6 簇 29 行 / full_verified 长度 131-180；给总裁定（可验收/仍阻断）与任何新发现分级。
888:169:366:  **① P1-05 第四轮返工（P1-05d）已落地，待五轮终裁** — Codex 四轮（`2026-08-19` 终裁文档）判 F-02/F-05 CLOSED、其余 STILL-OPEN；九路验证（`2026-08-20-Codex四轮终裁-九路验证与C批次方案.md`）9/9 CONFIRMED 含 B3 新回归一条。C 批全部落地：**C2**（`1683328c`：脏 last_examined 投影 None 止血 B3 新回归 · freshness 嵌套错型自愈 · 5 处 ID 切片改丢弃 · _id_ok 写侧过滤同源 · lag_seconds finite · 控制字符全拒）· **C3**（`d39983ce`：conversation_summary caller 显式传 vault 组修恒空 bug · ensure_entity_node 隔离身份拒绝复用）· **C1**（`c154a7f2`：lib 层 _resolves_outside_vault 接 LanceDB 两真实入口 open 前 · orchestrator 裸 fnmatch 换 canon + 扫描产出过 should_index 根除 hash-before-admission + realpath containment · by-node missing→404/path_rejected→422；新 test_real_entrypoint_admission.py 6 条真实入口行为锁）· **C4**（census Q2 中性化+前缀分类）。**遗留**：B4（payload 命名空间/provenance）独立轮 · TOCTOU 换链残余窗口（realpath 判定与 open 非原子，诚实登记）· P1-03/P1-04 押后
890:171:417:  - 其余: MEDIUM-1 G8 子串判定被 `[推定]` 前缀绕过→改闭集 / MEDIUM-3 SKILL 把 manifest 划进可信面→新增 **HARD-ISO-5b** / D-HIGH-2 降级把占位也编秩致秩号错位→排序前剔除 / D-HIGH-3 反向引用 regex 未 `re.escape` 致含括号节点整批漏检→已修 / D-MEDIUM-4 缺 Concepts 段时 exit 0 还说「已同步」→抛异常+退出码分层 / C-H3 frontmatter 自由文本被逐字写进白板→只认真 wikilink / C-H4 与后端 7 条语义分歧→逐条对齐 / C-H5 批次非原子 / C-M7 无 fsync / C-M9 行尾归一 / C-M10 doc_count 只改首处 / C-M11-13 断链·孤儿·多 sentinel 静默→全改成告警且 `--check` 红 / C-M14 `.bak` 二次覆盖
891:173:622:-    输入文件；Codex round-1 BLOCKER-1 整改）。
892:174:625:+    任一输入重合即 exit 2，防 "w" 截断输入（round-1 BLOCKER-1 + round-2
894:176:649:+    glob 结果拒绝 symlink 条目与逃逸到根外的目标（round-2 HIGH-3 整改）。
895:177:763:+    # round-2 HIGH-3 整改: 拒绝 symlink 条目与逃逸到根外的目标 —— 原实现
896:181:875:+    # round-2 HIGH-3 整改: 存在但不可读/不可遍历的根（chmod 000）此前 exit 0
897:182:885:+    # --out 碰撞守卫（写前）。round-2 BLOCKER-1 整改: 比较**文件身份**
899:186:1214: - **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
900:187:1215: - **BLOCKER-2（快照不原子）**：DLQ 单次 `read_bytes()`，头部 sha256/line_count 与逐条 records 派生自同一份内存字节；mtime 显式标注为 stat 参考值。
901:188:1219: - **HIGH-3（transcript 归因折叠）**：恰 1 个常规文件命中才算归因（多命中 = ambiguous 拒采信）；glob 改递归下探；transcripts 根缺失整体 exit 2（拒绝产出 unrecoverable 假象）。
902:189:1227:+## §7c Codex round-2 复审整改记录（10/13 CLOSED → 剩余 3 项 + 3 新 LOW 全部整改）
903:190:1229:+round-2 复审确认 BLOCKER-2/3、HIGH-2、MEDIUM-1~3、LOW-1~4 共 10 项 CLOSED，并抓出 3 项**未真正闭合**（均实测复现）+ 3 条新 LOW：
904:191:1231:+- **BLOCKER-1 NOT-CLOSED（hardlink / case-only 别名绕过）**：原守卫比较 `resolve()` **字符串**，hardlink 指向输入、以及大小写不敏感文件系统上的 case-only 别名均绕过并截断输入。**整改**：改为比较**文件身份 `(st_dev, st_ino)`**（对已存在的 --out）+ 保留路径比较作第二道。负例实测：两种绕过均 exit 2、DLQ sha 不变。
905:192:1232:+- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
906:193:1233:+- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
907:194:1234:+- **新 LOW ×3**：full_verified 长度范围修正为 131–180；台账 `class_distribution`/`recoverability_distribution` 补零并新增 `inline_state_distribution`（固定 schema，消费者无需补齐缺席键）；`line_count` 改用 `splitlines()` 与 records 同口径（原 `count("\n")` 在 bare CR / U+2028 下会与 records 数不一致）。
910:199:1398:    symlink 逃逸拒采信、3 新 LOW(长度范围/distribution 补零/line_count 同口径)。
912:201:1441:    12	    任一输入重合即 exit 2，防 "w" 截断输入（round-1 BLOCKER-1 + round-2
913:203:1463:    34	    glob 结果拒绝 symlink 条目与逃逸到根外的目标（round-2 HIGH-3 整改）。
914:204:1574:   145	    # round-2 HIGH-3 整改: 拒绝 symlink 条目与逃逸到根外的目标 —— 原实现
915:207:1689:   256	    # round-2 HIGH-3 整改: 存在但不可读/不可遍历的根（chmod 000）此前 exit 0
916:208:1698:   265	    # --out 碰撞守卫（写前）。round-2 BLOCKER-1 整改: 比较**文件身份**
919:213:1937:99:- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
920:214:1938:100:- **BLOCKER-2（快照不原子）**：DLQ 单次 `read_bytes()`，头部 sha256/line_count 与逐条 records 派生自同一份内存字节；mtime 显式标注为 stat 参考值。
921:215:1944:112:## §7c Codex round-2 复审整改记录（10/13 CLOSED → 剩余 3 项 + 3 新 LOW 全部整改）
922:216:1945:116:- **BLOCKER-1 NOT-CLOSED（hardlink / case-only 别名绕过）**：原守卫比较 `resolve()` **字符串**，hardlink 指向输入、以及大小写不敏感文件系统上的 case-only 别名均绕过并截断输入。**整改**：改为比较**文件身份 `(st_dev, st_ino)`**（对已存在的 --out）+ 保留路径比较作第二道。负例实测：两种绕过均 exit 2、DLQ sha 不变。
923:217:1946:117:- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
924:218:1947:118:- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
925:219:1948:119:- **新 LOW ×3**：full_verified 长度范围修正为 131–180；台账 `class_distribution`/`recoverability_distribution` 补零并新增 `inline_state_distribution`（固定 schema，消费者无需补齐缺席键）；`line_count` 改用 `splitlines()` 与 records 同口径（原 `count("\n")` 在 bare CR / U+2028 下会与 records 数不一致）。
927:225:2139:     3	总裁定：**仍阻断 / 不可验收**。`67ccebe1` 确实冻结了交付物，92 条数字也可独立复算；但实际只有 **10/13 CLOSED**，`BLOCKER-1`、`HIGH-1`、`HIGH-3` 仍未闭合。
928:226:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
929:227:2144:     8	| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
930:228:2145:     9	| BLOCKER-3 | **CLOSED** | `git show 67ccebe1 --stat` 为 10 个 G4-9 文件、3384 insertions，包含脚本、报告、ledger、证据包、round-1 审查和 UAT。当前 HEAD 为 `e7a480eb`，但全部 G4-9 路径相对 `67ccebe1` diff 为空。关键 blob：script `ea370cb…`、report `ff1f71d…`、ledger `6ce5772…`。 |
931:229:2146:    10	| HIGH-1 | **NOT-CLOSED** | round-1 三个反例本身均已翻转为 `anomaly/FAIL → unrecoverable`；非法 64 字符非 hex 也被拒。但新增组合反例：`episode_body="abc"`、`episode_body_full="abc"`、SHA 正确、声明长度 `999`，实际得到 `inline_state=anomaly` 后仍被判 `byte_exact`。原因是 [`full_body_verified()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:99)只核 SHA，不核长度，并在 [anomaly 分支之前](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:285)被采信。这直接反驳报告“anomaly 一律 unrecoverable”。 |
932:230:2147:    11	| HIGH-2 | **CLOSED** | missing、显式 `null`、字面 `"None"` 不再合组；数字 `123` 与字符串 `"123"` 分离；非前缀多 token 均 `attribution_conflict=true/unrecoverable`；合法前缀组统一取最长 token。真实入口反例全部通过。 |
933:231:2148:    12	| HIGH-3 | **NOT-CLOSED** | 不存在根目录已 exit 2；递归唯一命中、多命中冲突、目录伪命中也通过。但“不可见”仍未闭合：存在但 `chmod 000` 的根会 exit 0 并假判 `unrecoverable`。此外 [`glob + os.path.isfile`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:134)跟随 symlink：根内 `.jsonl` symlink 指向根外 `.txt`、以及 symlink 目录逃逸到根外树，均被判唯一来源并进入 `approximate`。 |
934:232:2149:    13	| MEDIUM-1 | **CLOSED（原 finding）** | 已读取 `episode_body_full`，不再完全忽略该生产字段；当前 92 条为 0。其长度门问题已计入 HIGH-1。 |
935:233:2150:    14	| MEDIUM-2 | **CLOSED** | [报告 §6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:78)、[ledger duplicate_clusters](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:60)及逐条 `reference_time` 已落地；6 簇全部逐行对账。 |
936:234:2151:    15	| MEDIUM-3 | **CLOSED（声明性控制）** | ledger [`privacy`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:4)及报告 private-only 声明已落地。它是纪律标签，不是技术性防外发门。 |
937:235:2152:    16	| LOW-1 | **CLOSED** | token 已修为 `16948–20831`，截断记录声明长度修为 `205–8036`。 |
938:236:2153:    17	| LOW-2 | **CLOSED** | [`stable_key_semantics`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:5)已明确仅为冻结快照内 occurrence key，不再声称三列缺一不可。 |
939:237:2154:    18	| LOW-3 | **CLOSED** | 报告同时补齐 `LearningConcept.name` 与 `LearningTip.created_at` 两处修复证据。 |
940:238:2155:    19	| LOW-4 | **CLOSED** | [报告 §1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:28)已区分当前实证和未重新复证的历史 mountinfo，不再把历史断言冒充本轮证明。 |
941:239:2171:    35	- **LOW**：header line_count 仅数 LF，而 records 使用 `splitlines()`；bare CR/U+2028 输入可出现 header `1`、records `2`。不影响当前标准 LF 的 92 条。
942:243:2762:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:117:- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
943:244:2763:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:119:- **新 LOW ×3**：full_verified 长度范围修正为 131–180；台账 `class_distribution`/`recoverability_distribution` 补零并新增 `inline_state_distribution`（固定 schema，消费者无需补齐缺席键）；`line_count` 改用 `splitlines()` 与 records 同口径（原 `count("\n")` 在 bare CR / U+2028 下会与 records 数不一致）。
944:245:2765:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:7:| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
945:246:2766:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:8:| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
946:247:2767:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:10:| HIGH-1 | **NOT-CLOSED** | round-1 三个反例本身均已翻转为 `anomaly/FAIL → unrecoverable`；非法 64 字符非 hex 也被拒。但新增组合反例：`episode_body="abc"`、`episode_body_full="abc"`、SHA 正确、声明长度 `999`，实际得到 `inline_state=anomaly` 后仍被判 `byte_exact`。原因是 [`full_body_verified()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:99)只核 SHA，不核长度，并在 [anomaly 分支之前](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:285)被采信。这直接反驳报告“anomaly 一律 unrecoverable”。 |
947:248:2768:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:12:| HIGH-3 | **NOT-CLOSED** | 不存在根目录已 exit 2；递归唯一命中、多命中冲突、目录伪命中也通过。但“不可见”仍未闭合：存在但 `chmod 000` 的根会 exit 0 并假判 `unrecoverable`。此外 [`glob + os.path.isfile`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:134)跟随 symlink：根内 `.jsonl` symlink 指向根外 `.txt`、以及 symlink 目录逃逸到根外树，均被判唯一来源并进入 `approximate`。 |
948:249:2769:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:14:| MEDIUM-2 | **CLOSED** | [报告 §6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:78)、[ledger duplicate_clusters](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:60)及逐条 `reference_time` 已落地；6 簇全部逐行对账。 |
949:250:2772:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:14:CARD-G4-9 round-3 复审（静态审阅 + 只读复算）。你 round-2 裁定 10/13 CLOSED，三项 NOT-CLOSED：BLOCKER-1（--out 守卫比 resolve 字符串，hardlink 与 case-only 别名绕过截断输入）、HIGH-1（full_body_verified 只核 sha 不核长度且排在 anomaly 分支前，anomaly 记录被判 byte_exact）、HIGH-3（chmod 000 根 exit 0 假判 unrecoverable；glob 跟随 symlink 逃逸出根）；另 3 新 LOW（full_verified 长度范围应 131-180、distribution 省略 0 值键、line_count 数 LF 与 records 的 splitlines 口径不一）。开发方以 commit 73102875 提交整改。请只读复核这 6 项是否闭合：
950:252:2792:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1232:+- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
951:253:2793:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1234:+- **新 LOW ×3**：full_verified 长度范围修正为 131–180；台账 `class_distribution`/`recoverability_distribution` 补零并新增 `inline_state_distribution`（固定 schema，消费者无需补齐缺席键）；`line_count` 改用 `splitlines()` 与 records 同口径（原 `count("\n")` 在 bare CR / U+2028 下会与 records 数不一致）。
952:254:2809:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1946:117:- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
953:255:2810:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1948:119:- **新 LOW ×3**：full_verified 长度范围修正为 131–180；台账 `class_distribution`/`recoverability_distribution` 补零并新增 `inline_state_distribution`（固定 schema，消费者无需补齐缺席键）；`line_count` 改用 `splitlines()` 与 records 同口径（原 `count("\n")` 在 bare CR / U+2028 下会与 records 数不一致）。
954:256:2815:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
955:257:2816:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2144:     8	| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
956:258:2817:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2146:    10	| HIGH-1 | **NOT-CLOSED** | round-1 三个反例本身均已翻转为 `anomaly/FAIL → unrecoverable`；非法 64 字符非 hex 也被拒。但新增组合反例：`episode_body="abc"`、`episode_body_full="abc"`、SHA 正确、声明长度 `999`，实际得到 `inline_state=anomaly` 后仍被判 `byte_exact`。原因是 [`full_body_verified()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:99)只核 SHA，不核长度，并在 [anomaly 分支之前](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:285)被采信。这直接反驳报告“anomaly 一律 unrecoverable”。 |
957:259:2818:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2148:    12	| HIGH-3 | **NOT-CLOSED** | 不存在根目录已 exit 2；递归唯一命中、多命中冲突、目录伪命中也通过。但“不可见”仍未闭合：存在但 `chmod 000` 的根会 exit 0 并假判 `unrecoverable`。此外 [`glob + os.path.isfile`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:134)跟随 symlink：根内 `.jsonl` symlink 指向根外 `.txt`、以及 symlink 目录逃逸到根外树，均被判唯一来源并进入 `approximate`。 |
958:260:2819:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2150:    14	| MEDIUM-2 | **CLOSED** | [报告 §6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:78)、[ledger duplicate_clusters](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:60)及逐条 `reference_time` 已落地；6 簇全部逐行对账。 |
959:261:2850:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:61:- **3 新 LOW**：full_verified 长度范围修正 131–180；台账三个 distribution 补零并新增 `inline_state_distribution`；`line_count` 与 records 改用同一 `splitlines()` 口径。
962:270:3483:六项均已完成静态反例审阅；高严重度结论由主审重新核对 Python 3.14 glob 实现与生产写/判定入口。数据复算 PASS，但两项路径安全仍 NOT-CLOSED。
963:272:3506:总裁定：**仍阻断 / 不可验收**。整改提交 `73102875fdd9837f0d60cf2ed6cf4ea7f6f8c2e5` 与当前文件字节一致，台账数字有效；但六项仅 **4 CLOSED / 2 NOT-CLOSED**。
964:273:3510:| BLOCKER-1 | **NOT-CLOSED / PARTIAL** | 稳定状态下，relative、`..`、case-only、既存 symlink/hardlink 组合已由 [resolve+inode 门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:265)挡住。但仍有两条绕过：① `protected_paths` 不含已被归因的 transcript，直接令 `--out=<唯一 transcript>`，脚本会先判其为恢复源，最后在 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:457)将其截断；② round-2 已指出的 TOCTOU 仍在——检查后、最终打开前将安全输出替换成指向 DLQ 的 symlink/hardlink，即可 `O_TRUNC` 输入。 |
965:274:3511:| HIGH-1 | **CLOSED / PASS** | [`full_body_verified()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:102)现有 SHA+严格长度门；[真实判定链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:340)在 full-body 分支前要求 `state != anomaly`。更强反例——full 本身 SHA/长度完全有效，但 inline 不符——仍落 `anomaly → unrecoverable`。无其它调用入口。 |
966:275:3512:| HIGH-3 | **NOT-CLOSED / PARTIAL** | 当前用户下根 `chmod 000` 会 exit 2，terminal symlink 和最终落根外的结果也被过滤。但 [`glob.glob(..., recursive=True)`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:144)在 realpath 过滤前已经递归遍历；当前 Python 3.14 的 [`glob.py`](/opt/homebrew/Cellar/python@3.14/3.14.4_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/glob.py:179)会跟随目录 symlink，并静默吞掉不可读子树错误。因此仍可越根枚举；不可读子树会造成“假唯一/假不可恢复”。此外 mode `000` 的唯一 regular transcript 仍能通过 `isfile()`，被判 `approximate`，尽管实际上不可读取。 |
967:276:3513:| LOW：长度范围 | **CLOSED** | 报告已改为四值 `131/142/150/180`、范围 `131–180`，[报告 §3](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:45)。 |
968:277:3514:| LOW：distribution 零键 | **CLOSED** | [固定 schema 生成链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:437)与 [ledger](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:43)均包含 `unexpected/anomaly/unrecoverable: 0`，并新增 inline 三态。 |
969:278:3515:| LOW：line_count 口径 | **CLOSED（原问题）** | header 与 records 都由同一 exact bytes、同一 `decode(...).splitlines()` 派生，[代码](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:195)不再互相矛盾；但引入了下述新 MEDIUM。 |
970:280:3530:- **MEDIUM — JSONL framing**：生产端 [`ensure_ascii=False`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/app/services/episode_worker.py:259)可原样输出字符串内的 U+2028；`splitlines()` 会把一个合法的单 LF JSONL record 拆成两条坏行。当前 92 条不受影响，但通用 census 会漏记录。正确口径应按 LF 分帧，而不是 Unicode `splitlines()`。
971:281:3532:- **LOW — provenance/evidence**：[报告头](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:5)仍只写起始基线 `37387a86`，未明确区分整改 artifact `73102875`；§7 的 HIGH-1 负例也只隔离验证了长度门，没有单独验证 anomaly 顺序门，尽管代码经更强反例确认正确。
972:282:3534:所以：**冻结的 92 条 ledger 数值可采信；CARD-G4-9 生成器与整卡验收仍被 BLOCKER-1、HIGH-3 阻断。** 本轮未修改仓库或受审数据，未执行破坏性 fixture/G4-10 重放；Graphiti 工具本轮不可用。
973:283:3539:总裁定：**仍阻断 / 不可验收**。整改提交 `73102875fdd9837f0d60cf2ed6cf4ea7f6f8c2e5` 与当前文件字节一致，台账数字有效；但六项仅 **4 CLOSED / 2 NOT-CLOSED**。
974:284:3543:| BLOCKER-1 | **NOT-CLOSED / PARTIAL** | 稳定状态下，relative、`..`、case-only、既存 symlink/hardlink 组合已由 [resolve+inode 门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:265)挡住。但仍有两条绕过：① `protected_paths` 不含已被归因的 transcript，直接令 `--out=<唯一 transcript>`，脚本会先判其为恢复源，最后在 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:457)将其截断；② round-2 已指出的 TOCTOU 仍在——检查后、最终打开前将安全输出替换成指向 DLQ 的 symlink/hardlink，即可 `O_TRUNC` 输入。 |
975:285:3544:| HIGH-1 | **CLOSED / PASS** | [`full_body_verified()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:102)现有 SHA+严格长度门；[真实判定链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:340)在 full-body 分支前要求 `state != anomaly`。更强反例——full 本身 SHA/长度完全有效，但 inline 不符——仍落 `anomaly → unrecoverable`。无其它调用入口。 |
976:286:3545:| HIGH-3 | **NOT-CLOSED / PARTIAL** | 当前用户下根 `chmod 000` 会 exit 2，terminal symlink 和最终落根外的结果也被过滤。但 [`glob.glob(..., recursive=True)`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:144)在 realpath 过滤前已经递归遍历；当前 Python 3.14 的 [`glob.py`](/opt/homebrew/Cellar/python@3.14/3.14.4_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/glob.py:179)会跟随目录 symlink，并静默吞掉不可读子树错误。因此仍可越根枚举；不可读子树会造成“假唯一/假不可恢复”。此外 mode `000` 的唯一 regular transcript 仍能通过 `isfile()`，被判 `approximate`，尽管实际上不可读取。 |
977:287:3546:| LOW：长度范围 | **CLOSED** | 报告已改为四值 `131/142/150/180`、范围 `131–180`，[报告 §3](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:45)。 |
978:288:3547:| LOW：distribution 零键 | **CLOSED** | [固定 schema 生成链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:437)与 [ledger](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:43)均包含 `unexpected/anomaly/unrecoverable: 0`，并新增 inline 三态。 |
979:289:3548:| LOW：line_count 口径 | **CLOSED（原问题）** | header 与 records 都由同一 exact bytes、同一 `decode(...).splitlines()` 派生，[代码](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:195)不再互相矛盾；但引入了下述新 MEDIUM。 |
980:291:3563:- **MEDIUM — JSONL framing**：生产端 [`ensure_ascii=False`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/app/services/episode_worker.py:259)可原样输出字符串内的 U+2028；`splitlines()` 会把一个合法的单 LF JSONL record 拆成两条坏行。当前 92 条不受影响，但通用 census 会漏记录。正确口径应按 LF 分帧，而不是 Unicode `splitlines()`。
981:292:3565:- **LOW — provenance/evidence**：[报告头](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:5)仍只写起始基线 `37387a86`，未明确区分整改 artifact `73102875`；§7 的 HIGH-1 负例也只隔离验证了长度门，没有单独验证 anomaly 顺序门，尽管代码经更强反例确认正确。
982:293:3567:所以：**冻结的 92 条 ledger 数值可采信；CARD-G4-9 生成器与整卡验收仍被 BLOCKER-1、HIGH-3 阻断。** 本轮未修改仓库或受审数据，未执行破坏性 fixture/G4-10 重放；Graphiti 工具本轮不可用。
984:313:+## §7d Codex round-3 复审整改记录（4/6 CLOSED → 剩 2 项 + 3 新发现全部整改）
985:315:+round-3 确认 HIGH-1 与三条 LOW 已 CLOSED、台账数字有效且与 commit 字节一致，两项路径安全判 PARTIAL：
986:317:+- **BLOCKER-1 残留两条绕过**：① `protected_paths` 未含**归因到的 transcript**，`--out=<唯一 transcript>` 会截断恢复源；② check-then-open 的 **TOCTOU** 仍在（检查后、打开前把 --out 换成指向 DLQ 的链接）。**整改**：① 写出前把全部 `transcript_paths` 并入保护集；② 改 `os.open(O_WRONLY|O_CREAT|O_NOFOLLOW)` **不带 O_TRUNC** 打开 → 对**实际 fd** `fstat` 校验 inode → 通过才 `ftruncate`，检查与写入作用于同一 fd，替换攻击无效。反例实测：`--out` 指向唯一 transcript → exit 2、transcript sha 不变。
987:318:+- **HIGH-3 残留**：`glob(recursive=True)` 在 realpath 过滤**之前**已递归遍历（Python 3.14 glob 跟随目录 symlink 且**静默吞掉不可读子树错误**）→ 越根枚举 + "假唯一/假不可恢复"；mode `000` 的 regular transcript 仍过 `isfile()` 被判 approximate。**整改**：改 `os.walk(onerror=..., followlinks=False)`（不跟随目录 symlink、遍历错误显式捕获）+ 候选加 `os.access(R_OK)` 门；遍历受阻或存在不可读候选一律记 `attribution_conflict` 拒绝裁定（既不宣称找到、也不宣称不可恢复）。三条反例实测全部 fail-closed。
988:319:+- **新 MEDIUM（JSONL framing）**：生产端 `ensure_ascii=False` 可原样写出字符串内的 U+2028，`splitlines()` 会把一条合法单-LF 记录劈成两条坏行。**整改**：新增 `_split_jsonl_lines()` 严格按 LF 分帧，header `line_count` 与 records 共用同一函数。
989:320:+- **新 LOW（输入 schema）**：合法 JSON 但非对象（`null` / 数组 / 标量）解析成功后在 `rec.get()` 处抛 AttributeError 炸全量。**整改**：非 dict 归 `unparseable`（`not_a_json_object: <type>`），实测两条毒行不影响其余记录。
990:321:+- **新 LOW（provenance）**：报告头只写起始基线未区分整改 artifact commit —— 已在报告头补三段 commit 链。
995:368:-    # round-2 HIGH-3 整改: 拒绝 symlink 条目与逃逸到根外的目标 —— 原实现
996:370:+    # round-2 HIGH-3: 拒绝 symlink 条目与逃逸到根外的目标（glob 会跟随 symlink，
998:427:-        # round-2 LOW 整改: 与 records 的 splitlines() 同口径（bare CR / U+2028
1000:442:     # --out 碰撞守卫（写前）。round-2 BLOCKER-1 整改: 比较**文件身份**
1002:455:     # BLOCKER-2 整改: 单次读取，records 与头部描述共享同一份 exact bytes
1003:466:+        # round-3 LOW 整改: 合法 JSON 但非对象（null / 数组 / 标量）此前解析成功
1004:480:+    # round-3 BLOCKER-1 绕过① 整改: 归因到的 transcript 是恢复源，
1006:494:+        # round-3 整改: 消除 check-then-open TOCTOU。先以 O_NOFOLLOW 打开且
1007:498:+            fd = os.open(args.out, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
1013:573:    12	    任一输入重合即 exit 2，防 "w" 截断输入（round-1 BLOCKER-1 + round-2
1014:576:    15	快照原子性（Codex round-1 BLOCKER-2 整改）:
1015:580:    19	判定 fail-closed（Codex round-1 HIGH-1/2/3 整改）:
1019:595:    34	    glob 结果拒绝 symlink 条目与逃逸到根外的目标（round-2 HIGH-3 整改）。
1020:600:    39	    不得经此分支翻案（round-1 MEDIUM-1 + round-2 HIGH-1 整改）。
1021:608:    47	    语义重复簇），G4-10 重放去重策略依据（Codex round-1 MEDIUM-2 整改）。
1022:610:    49	    工件，禁止外发（Codex round-1 MEDIUM-3；仓库为私有仓，纪律=不 push 公网）。
1027:673:   112	    round-2 HIGH-1 整改: 原实现只核 sha，声明长度矛盾的记录（如 body="abc"
1029:712:   151	    # round-2 HIGH-3: 拒绝 symlink 条目与逃逸到根外的目标（glob 会跟随 symlink，
1040:855:   294	    # round-2 HIGH-3 整改: 存在但不可读/不可遍历的根（chmod 000）此前 exit 0
1046:865:   304	    # --out 碰撞守卫（写前）。round-2 BLOCKER-1 整改: 比较**文件身份**
1048:897:   336	    # BLOCKER-2 整改: 单次读取，records 与头部描述共享同一份 exact bytes
1049:912:   351	        # round-3 LOW 整改: 合法 JSON 但非对象（null / 数组 / 标量）此前解析成功
1051:950:   389	            # round-2 HIGH-1 整改: anomaly 记录不得经 full_body 分支翻案
1059:1043:   482	        # round-2 LOW 整改: 固定 schema 补零，消费者无需自行补齐缺席键
1063:1062:   501	    # round-3 BLOCKER-1 绕过① 整改: 归因到的 transcript 是恢复源，
1065:1074:   513	        # round-3 整改: 消除 check-then-open TOCTOU。先以 O_NOFOLLOW 打开且
1066:1078:   517	            fd = os.open(args.out, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
1077:1163:    51	| `full_verified`（内联全量，sha 对账通过） | **4** | 重算值 == 声明值且长度精确匹配（四条正文实为 131/142/150/180 字符，范围 **131–180**，天然未截断；round-2 LOW 修正） |
1078:1164:    52	| `truncated_prefix`（200 字符前缀） | **88** | len(inline)==200、声明 sha 为合法 64-hex 且声明长度 205–8036。**注**：sha 只能证明 inline≠声明全文，"确为前缀"依赖 `to_dict()[:200]` 生产不变量，无法用 sha 直接证明（Codex round-1 HIGH-1 措辞收敛） |
1083:1192:    80	台账逐条携带复合键 `{line_no, sha256_prefix(16 hex), request_id}`。**语义（Codex round-1 LOW-2 修正）**：这是**冻结快照内的 occurrence key**，不是跨文件重排或语义幂等键——台账头部 `dlq_file.sha256`（`3b37460f4215f6ac…`）即快照指纹，`line_no` 在该快照内已单列唯一；`sha256_prefix`（本快照 69 个唯一值，qa_highlight 家族实测同名同 sha 多条）与 `request_id`（仅 25 个唯一值，进程内 contextvars、重启可复用）是**冗余对账/诊断维度**，不是唯一性的必要条件。G4-10 消费前先 diff 头部 sha 即知 DLQ 是否长了新条目；语义级去重不得按本键，须按 `duplicate_clusters` 段（见下）。**语义重复簇（MEDIUM-2 整改）**：按 `{name, episode_body_sha256, group_id}` 聚簇，**6 簇覆盖 29 行**（最大簇 = 同一 session-archive 16 行，`reference_time` 各不相同——同内容反复入队反复超限）。台账 `duplicate_clusters` 段逐簇列 line_nos，records 逐条透传 `reference_time`；G4-10 重放前必须先定去重策略（89 条 budget 修根因后若逐条盲放，将把同内容写入最多 16 遍）。
1084:1194:    82	**隐私（MEDIUM-3 整改）**：`transcript_paths` 含本机用户名与完整 session UUID，台账与本报告为 **private-only 工件**（台账头部已带 privacy 字段；仓库纪律 = 不 push 公网远端）。
1089:1206:    94	| 负例门（round-1 整改自证） | `--out`==`--dlq` → exit 2 拒写、DLQ 完好；transcripts 根缺失 → exit 2 拒诊；sha 匹配但长度不符（round-1 HIGH-1 反例①）→ anomaly/unrecoverable；坏 JSON 行/空行 → unparseable 逐行入台账不拒诊 |
1091:1211:    99	- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
1092:1212:   100	- **BLOCKER-2（快照不原子）**：DLQ 单次 `read_bytes()`，头部 sha256/line_count 与逐条 records 派生自同一份内存字节；mtime 显式标注为 stat 参考值。
1093:1213:   101	- **BLOCKER-3（交付物未冻结漂移）**：以本卡 commit 冻结全部交付物 exact bytes（脚本/报告/台账/证据包同 commit）；grep-selfattest 已按最终版行号重生成并内嵌脚本 sha 前缀。
1094:1214:   102	- **HIGH-1（inline 判定不 fail-closed）**：full_verified 加长度精确匹配门；truncated_prefix 加 64-hex 合法性门；anomaly 一律 unrecoverable + 如实 basis（不再谎称截断、不再滑入 approximate）。
1095:1215:   103	- **HIGH-2（request_id fail-open）**：分组键改 `(类型名, 值)`；缺失/None 按 line_no 单条成组零传染；组内多 token 前缀一致门，冲突记 `attribution_conflict` 拒绝采信（现网 92 条 0 冲突）。
1096:1216:   104	- **HIGH-3（transcript 归因折叠）**：恰 1 个常规文件命中才算归因（多命中 = ambiguous 拒采信）；glob 改递归下探；transcripts 根缺失整体 exit 2（拒绝产出 unrecoverable 假象）。
1097:1217:   105	- **MEDIUM-1**：`episode_body_full` 在盘且 sha 对账通过 → byte_exact 采信（现网 0 条，通路已备）。
1098:1218:   106	- **MEDIUM-2**：`duplicate_clusters` 段 + 逐条 `reference_time`（见 §6）。
1099:1219:   107	- **MEDIUM-3**：台账头部 privacy 字段 + 本报告 private-only 声明（见 §6）。
1100:1220:   108	- **LOW-1~4**：token 区间 16948–20831、长度区间 205–8036、稳定键语义重写、schema 双处证据、挂载历史证据边界——均已在正文落地。
1102:1224:   112	## §7c Codex round-2 复审整改记录（10/13 CLOSED → 剩余 3 项 + 3 新 LOW 全部整改）
1103:1226:   114	round-2 复审确认 BLOCKER-2/3、HIGH-2、MEDIUM-1~3、LOW-1~4 共 10 项 CLOSED，并抓出 3 项**未真正闭合**（均实测复现）+ 3 条新 LOW：
1104:1228:   116	- **BLOCKER-1 NOT-CLOSED（hardlink / case-only 别名绕过）**：原守卫比较 `resolve()` **字符串**，hardlink 指向输入、以及大小写不敏感文件系统上的 case-only 别名均绕过并截断输入。**整改**：改为比较**文件身份 `(st_dev, st_ino)`**（对已存在的 --out）+ 保留路径比较作第二道。负例实测：两种绕过均 exit 2、DLQ sha 不变。
1105:1229:   117	- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
1106:1230:   118	- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
1107:1231:   119	- **新 LOW ×3**：full_verified 长度范围修正为 131–180；台账 `class_distribution`/`recoverability_distribution` 补零并新增 `inline_state_distribution`（固定 schema，消费者无需补齐缺席键）；`line_count` 改用 `splitlines()` 与 records 同口径（原 `count("\n")` 在 bare CR / U+2028 下会与 records 数不一致）。
1110:1250:   138	## §7d Codex round-3 复审整改记录（4/6 CLOSED → 剩 2 项 + 3 新发现全部整改）
1111:1252:   140	round-3 确认 HIGH-1 与三条 LOW 已 CLOSED、台账数字有效且与 commit 字节一致，两项路径安全判 PARTIAL：
1112:1254:   142	- **BLOCKER-1 残留两条绕过**：① `protected_paths` 未含**归因到的 transcript**，`--out=<唯一 transcript>` 会截断恢复源；② check-then-open 的 **TOCTOU** 仍在（检查后、打开前把 --out 换成指向 DLQ 的链接）。**整改**：① 写出前把全部 `transcript_paths` 并入保护集；② 改 `os.open(O_WRONLY|O_CREAT|O_NOFOLLOW)` **不带 O_TRUNC** 打开 → 对**实际 fd** `fstat` 校验 inode → 通过才 `ftruncate`，检查与写入作用于同一 fd，替换攻击无效。反例实测：`--out` 指向唯一 transcript → exit 2、transcript sha 不变。
1113:1255:   143	- **HIGH-3 残留**：`glob(recursive=True)` 在 realpath 过滤**之前**已递归遍历（Python 3.14 glob 跟随目录 symlink 且**静默吞掉不可读子树错误**）→ 越根枚举 + "假唯一/假不可恢复"；mode `000` 的 regular transcript 仍过 `isfile()` 被判 approximate。**整改**：改 `os.walk(onerror=..., followlinks=False)`（不跟随目录 symlink、遍历错误显式捕获）+ 候选加 `os.access(R_OK)` 门；遍历受阻或存在不可读候选一律记 `attribution_conflict` 拒绝裁定（既不宣称找到、也不宣称不可恢复）。三条反例实测全部 fail-closed。
1114:1256:   144	- **新 MEDIUM（JSONL framing）**：生产端 `ensure_ascii=False` 可原样写出字符串内的 U+2028，`splitlines()` 会把一条合法单-LF 记录劈成两条坏行。**整改**：新增 `_split_jsonl_lines()` 严格按 LF 分帧，header `line_count` 与 records 共用同一函数。
1115:1257:   145	- **新 LOW（输入 schema）**：合法 JSON 但非对象（`null` / 数组 / 标量）解析成功后在 `rec.get()` 处抛 AttributeError 炸全量。**整改**：非 dict 归 `unparseable`（`not_a_json_object: <type>`），实测两条毒行不影响其余记录。
1116:1258:   146	- **新 LOW（provenance）**：报告头只写起始基线未区分整改 artifact commit —— 已在报告头补三段 commit 链。
1118:1270:   351	        # round-3 LOW 整改: 合法 JSON 但非对象（null / 数组 / 标量）此前解析成功
1120:1308:   389	            # round-2 HIGH-1 整改: anomaly 记录不得经 full_body 分支翻案
1128:1401:   482	        # round-2 LOW 整改: 固定 schema 补零，消费者无需自行补齐缺席键
1132:1420:   501	    # round-3 BLOCKER-1 绕过① 整改: 归因到的 transcript 是恢复源，
1134:1432:   513	        # round-3 整改: 消除 check-then-open TOCTOU。先以 O_NOFOLLOW 打开且
1135:1436:   517	            fd = os.open(args.out, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
1138:1491:    G4-9(4/6→6/6): transcript 并入 --out 保护集(防截断恢复源)、O_NOFOLLOW+
1160:1682:**Reviewing open syscall O_NOFOLLOW docs**
1161:1709:python3 -B -c 'import os,stat; print(\"O_NOFOLLOW\",getattr(os,\"O_NOFOLLOW\",None)); print(\"O_NONBLOCK\",os.O_NONBLOCK); print(\"regular_gate_in_source\", \"S_ISREG\" in open(\"backend/scripts/census_dead_letter_episodes.py\",encoding=\"utf-8\").read())'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
1162:1721:O_NOFOLLOW 256
1165:1910:/bin/zsh -lc "man 2 open | col -b | rg -n -C 3 'O_NOFOLLOW|FIFO|named pipe|O_NONBLOCK' | head -n 160" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
1167:1950:/bin/zsh -lc "rg -n -i \"round-3|transcript.*out|O_NOFOLLOW|fstat|ftruncate|FIFO|device|intermediate|walk_error|unreadable|U\\+2028|not_a_json_object|non.dict|单空|blank\" '_bmad-output/审查/G4-9-evidence' '_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md' | head -n 280" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
1168:1953:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:119:- **新 LOW ×3**：full_verified 长度范围修正为 131–180；台账 `class_distribution`/`recoverability_distribution` 补零并新增 `inline_state_distribution`（固定 schema，消费者无需补齐缺席键）；`line_count` 改用 `splitlines()` 与 records 同口径（原 `count("\n")` 在 bare CR / U+2028 下会与 records 数不一致）。
1169:1954:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:138:## §7d Codex round-3 复审整改记录（4/6 CLOSED → 剩 2 项 + 3 新发现全部整改）
1170:1955:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:140:round-3 确认 HIGH-1 与三条 LOW 已 CLOSED、台账数字有效且与 commit 字节一致，两项路径安全判 PARTIAL：
1171:1956:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:142:- **BLOCKER-1 残留两条绕过**：① `protected_paths` 未含**归因到的 transcript**，`--out=<唯一 transcript>` 会截断恢复源；② check-then-open 的 **TOCTOU** 仍在（检查后、打开前把 --out 换成指向 DLQ 的链接）。**整改**：① 写出前把全部 `transcript_paths` 并入保护集；② 改 `os.open(O_WRONLY|O_CREAT|O_NOFOLLOW)` **不带 O_TRUNC** 打开 → 对**实际 fd** `fstat` 校验 inode → 通过才 `ftruncate`，检查与写入作用于同一 fd，替换攻击无效。反例实测：`--out` 指向唯一 transcript → exit 2、transcript sha 不变。
1172:1957:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:144:- **新 MEDIUM（JSONL framing）**：生产端 `ensure_ascii=False` 可原样写出字符串内的 U+2028，`splitlines()` 会把一条合法单-LF 记录劈成两条坏行。**整改**：新增 `_split_jsonl_lines()` 严格按 LF 分帧，header `line_count` 与 records 共用同一函数。
1173:1958:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:145:- **新 LOW（输入 schema）**：合法 JSON 但非对象（`null` / 数组 / 标量）解析成功后在 `rec.get()` 处抛 AttributeError 炸全量。**整改**：非 dict 归 `unparseable`（`not_a_json_object: <type>`），实测两条毒行不影响其余记录。
1175:1961:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:20:--- (4) 写出口（唯一，且经 O_NOFOLLOW+fstat inode 校验后才 ftruncate）:
1176:1962:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:21:517:            fd = os.open(args.out, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
1179:1999:--- (4) 写出口（唯一，且经 O_NOFOLLOW+fstat inode 校验后才 ftruncate）:
1180:2000:517:            fd = os.open(args.out, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
1213:2301:总裁定：**仍阻断 / 不可验收**。六项仅 **1/6 CLOSED**。冻结台账的数字本身可采信，但生成器仍存在可截断恢复源的 BLOCKER，不能据此接受 CARD‑G4‑9。
1214:2305:| 1. transcript 纳入保护集 | **NOT-CLOSED / PARTIAL** | 稳定状态下，[保护循环](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:503)确实覆盖当前 89 个路径引用、7 个唯一 inode。但不可读候选会在 [180–186](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:180)清空 `transcript_paths`，因此不进入保护集。owner mode `0200` 的匹配 transcript 不可读但可写，`--out` 指向它时仍能在 [517–529](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:517)被截断；无需竞态。另 `stat` 失败被 [直接吞掉](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:506)，也不是“全部并入”的 fail-closed 实现。 |
1215:2306:| 2. fd 上校验 TOCTOU | **NOT-CLOSED / PARTIAL** | `open` 不带 `O_TRUNC`，随后同一 fd 上 `fstat→ftruncate`，确实封住了最终组件换链及稳定 protected inode/hardlink；外部进程不能重新绑定本进程 fd，未发现 fd-number 竞争。但源身份早在 [312–317](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:312)按路径采集，DLQ 到 [337](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:337)才读取。静态调度 `protected=A → 将 inode B 换入 DLQ → snapshot 读取 B → --out hardlink B → fstat 不命中 A → truncate B` 仍可截断本次实际读取源。`O_NOFOLLOW` 也只保护最终组件；中间 symlink 可重定向至未保护对象。 |
1216:2307:| 3. HIGH-3 枚举 | **NOT-CLOSED** | 稳态目录 symlink、`scandir` 错误和 mode `000` 门已有改善。但 unreadable/walk error 设置 conflict 后，主链仍在 [395–397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:395)明确产出 `recoverability=unrecoverable`，直接反驳报告所称“既不宣称不可恢复” [报告:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:143)。此外 `os.walk.onerror` 只覆盖 `scandir`；逐条 `is_dir/stat` 错误可被静默当非候选，[islink→isfile→access→realpath](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:168)仍是路径级竞态。 |
1217:2308:| 4. JSONL framing | **NOT-CLOSED / PARTIAL** | U+2028、裸 CR 误分帧已修，header 与 records 共用 helper。但 [`_split_jsonl_lines()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:76)有 `b"\n" → []`，把一条非法空白行静默算成零行；`decode(errors="replace")` 还会把非法 UTF‑8 `b'{"a":"\\xff"}\n'` 改写成合法对象而非 unparseable。 |
1218:2309:| 5. 非 dict JSON | **CLOSED** | [`isinstance(rec, dict)` 门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:351)位于任何 `.get()` 和 `records.append()` 前；`null`、数组、标量均进入 `unparseable`。 |
1219:2310:| 6. provenance | **NOT-CLOSED（LOW）** | Git 实际 ancestry 与三个受审 blob 均能绑定到 `fce0d8a2`；但[报告头](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:5)只写 `67ccebe1 → 73102875 → 本次 round-3 整改 commit`，没有字面 `fce0d8a2`。由于 commit 不能自包含自身 SHA，需用后置 receipt/tag/manifest 明确绑定，不能以模糊代称冒充精确三段链。 |
1220:2314:- **BLOCKER**：不可读但可写 transcript 可绕过保护集并被截断。
1221:2315:- **BLOCKER**：protected source identity 与实际读取对象未绑定，源侧 TOCTOU 仍在。
1222:2316:- **HIGH**：扫描不可见性仍被终态化为 `unrecoverable`。
1223:2317:- **MEDIUM**：缺少 regular-file gate 和 `O_NONBLOCK`；FIFO 可在 `fstat` 前阻塞，设备节点进入平台相关 `ftruncate`。
1224:2318:- **MEDIUM**：非法 UTF‑8经 replacement 后可被当作有效记录。
1225:2319:- **LOW**：合法 dict 内字段错型仍可炸全量，例如 `request_id=[]`、`name=None`、`episode_body=None`。
1226:2320:- **LOW**：`transcripts_dir="/"` 时 `root_real + os.sep == "//"`，合法子项均无法通过 containment。
1227:2321:- **LOW**：`0o600` 只作用于新建输出，覆盖既有 `0644` private-only ledger 不会收紧权限。
1232:2338:总裁定：**仍阻断 / 不可验收**。六项仅 **1/6 CLOSED**。冻结台账的数字本身可采信，但生成器仍存在可截断恢复源的 BLOCKER，不能据此接受 CARD‑G4‑9。
1233:2342:| 1. transcript 纳入保护集 | **NOT-CLOSED / PARTIAL** | 稳定状态下，[保护循环](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:503)确实覆盖当前 89 个路径引用、7 个唯一 inode。但不可读候选会在 [180–186](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:180)清空 `transcript_paths`，因此不进入保护集。owner mode `0200` 的匹配 transcript 不可读但可写，`--out` 指向它时仍能在 [517–529](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:517)被截断；无需竞态。另 `stat` 失败被 [直接吞掉](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:506)，也不是“全部并入”的 fail-closed 实现。 |
1234:2343:| 2. fd 上校验 TOCTOU | **NOT-CLOSED / PARTIAL** | `open` 不带 `O_TRUNC`，随后同一 fd 上 `fstat→ftruncate`，确实封住了最终组件换链及稳定 protected inode/hardlink；外部进程不能重新绑定本进程 fd，未发现 fd-number 竞争。但源身份早在 [312–317](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:312)按路径采集，DLQ 到 [337](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:337)才读取。静态调度 `protected=A → 将 inode B 换入 DLQ → snapshot 读取 B → --out hardlink B → fstat 不命中 A → truncate B` 仍可截断本次实际读取源。`O_NOFOLLOW` 也只保护最终组件；中间 symlink 可重定向至未保护对象。 |
1235:2344:| 3. HIGH-3 枚举 | **NOT-CLOSED** | 稳态目录 symlink、`scandir` 错误和 mode `000` 门已有改善。但 unreadable/walk error 设置 conflict 后，主链仍在 [395–397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:395)明确产出 `recoverability=unrecoverable`，直接反驳报告所称“既不宣称不可恢复” [报告:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:143)。此外 `os.walk.onerror` 只覆盖 `scandir`；逐条 `is_dir/stat` 错误可被静默当非候选，[islink→isfile→access→realpath](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:168)仍是路径级竞态。 |
1236:2345:| 4. JSONL framing | **NOT-CLOSED / PARTIAL** | U+2028、裸 CR 误分帧已修，header 与 records 共用 helper。但 [`_split_jsonl_lines()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:76)有 `b"\n" → []`，把一条非法空白行静默算成零行；`decode(errors="replace")` 还会把非法 UTF‑8 `b'{"a":"\\xff"}\n'` 改写成合法对象而非 unparseable。 |
1237:2346:| 5. 非 dict JSON | **CLOSED** | [`isinstance(rec, dict)` 门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:351)位于任何 `.get()` 和 `records.append()` 前；`null`、数组、标量均进入 `unparseable`。 |
1238:2347:| 6. provenance | **NOT-CLOSED（LOW）** | Git 实际 ancestry 与三个受审 blob 均能绑定到 `fce0d8a2`；但[报告头](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:5)只写 `67ccebe1 → 73102875 → 本次 round-3 整改 commit`，没有字面 `fce0d8a2`。由于 commit 不能自包含自身 SHA，需用后置 receipt/tag/manifest 明确绑定，不能以模糊代称冒充精确三段链。 |
1239:2351:- **BLOCKER**：不可读但可写 transcript 可绕过保护集并被截断。
1240:2352:- **BLOCKER**：protected source identity 与实际读取对象未绑定，源侧 TOCTOU 仍在。
1241:2353:- **HIGH**：扫描不可见性仍被终态化为 `unrecoverable`。
1242:2354:- **MEDIUM**：缺少 regular-file gate 和 `O_NONBLOCK`；FIFO 可在 `fstat` 前阻塞，设备节点进入平台相关 `ftruncate`。
1243:2355:- **MEDIUM**：非法 UTF‑8经 replacement 后可被当作有效记录。
1244:2356:- **LOW**：合法 dict 内字段错型仍可炸全量，例如 `request_id=[]`、`name=None`、`episode_body=None`。
1245:2357:- **LOW**：`transcripts_dir="/"` 时 `root_real + os.sep == "//"`，合法子项均无法通过 containment。
1246:2358:- **LOW**：`0o600` 只作用于新建输出，覆盖既有 `0644` private-only ledger 不会收紧权限。
1255:# CARD-G4-9 — DLQ 真实挂载 census 分诊报告
1259:> **代码基线**: 分析对象锚定 `37387a86`（第五批开工基线）。**本卡交付物 artifact commit 链**：精确 SHA 逐段记录于 `_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt`（commit 无法自含己身 SHA，故用后置 receipt 绑定——Codex round-4 LOW 整改）
1266:## §1 挂载真相（live/主仓/孤儿三址 sha 对照 + compose 遮蔽史）
1286:## §2 总量与分类台账（class 分诊）
1299:## §3 inline 完整性 + SHA 对账
1305:| `full_verified`（内联全量，sha 对账通过） | **4** | 重算值 == 声明值且长度精确匹配（四条正文实为 131/142/150/180 字符，范围 **131–180**，天然未截断；round-2 LOW 修正） |
1306:| `truncated_prefix`（200 字符前缀） | **88** | len(inline)==200、声明 sha 为合法 64-hex 且声明长度 205–8036。**注**：sha 只能证明 inline≠声明全文，"确为前缀"依赖 `to_dict()[:200]` 生产不变量，无法用 sha 直接证明（Codex round-1 HIGH-1 措辞收敛） |
1311:## §4 源指针核销（qa_metrics.db，只读 mode=ro）
1320:## §5 可恢复性裁定（三态 + unverifiable 第四态）
1333:## §6 台账稳定键（G4-10 交接契约）
1335:台账逐条携带复合键 `{line_no, sha256_prefix(16 hex), request_id}`。**语义（Codex round-1 LOW-2 修正）**：这是**冻结快照内的 occurrence key**，不是跨文件重排或语义幂等键——台账头部 `dlq_file.sha256`（`3b37460f4215f6ac…`）即快照指纹，`line_no` 在该快照内已单列唯一；`sha256_prefix`（本快照 69 个唯一值，qa_highlight 家族实测同名同 sha 多条）与 `request_id`（仅 25 个唯一值，进程内 contextvars、重启可复用）是**冗余对账/诊断维度**，不是唯一性的必要条件。G4-10 消费前先 diff 头部 sha 即知 DLQ 是否长了新条目；语义级去重不得按本键，须按 `duplicate_clusters` 段（见下）。**语义重复簇（MEDIUM-2 整改）**：按 `{name, episode_body_sha256, group_id}` 聚簇，**6 簇覆盖 29 行**（最大簇 = 同一 session-archive 16 行，`reference_time` 各不相同——同内容反复入队反复超限）。台账 `duplicate_clusters` 段逐簇列 line_nos，records 逐条透传 `reference_time`；G4-10 重放前必须先定去重策略（89 条 budget 修根因后若逐条盲放，将把同内容写入最多 16 遍）。
1337:**隐私（MEDIUM-3 整改）**：`transcript_paths` 含本机用户名与完整 session UUID，台账与本报告为 **private-only 工件**（台账头部已带 privacy 字段；仓库纪律 = 不 push 公网远端）。
1341:## §7 裁判证据（整改版脚本重跑）
1349:| 负例门（round-1 整改自证） | `--out`==`--dlq` → exit 2 拒写、DLQ 完好；transcripts 根缺失 → exit 2 拒诊；sha 匹配但长度不符（round-1 HIGH-1 反例①）→ anomaly/unrecoverable；坏 JSON 行/空行 → unparseable 逐行入台账不拒诊 |
1352:## §7b Codex round-1 整改记录（BLOCKED → 全项整改）
1354:- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
1355:- **BLOCKER-2（快照不原子）**：DLQ 单次 `read_bytes()`，头部 sha256/line_count 与逐条 records 派生自同一份内存字节；mtime 显式标注为 stat 参考值。
1356:- **BLOCKER-3（交付物未冻结漂移）**：以本卡 commit 冻结全部交付物 exact bytes（脚本/报告/台账/证据包同 commit）；grep-selfattest 已按最终版行号重生成并内嵌脚本 sha 前缀。
1357:- **HIGH-1（inline 判定不 fail-closed）**：full_verified 加长度精确匹配门；truncated_prefix 加 64-hex 合法性门；anomaly 一律 unrecoverable + 如实 basis（不再谎称截断、不再滑入 approximate）。
1358:- **HIGH-2（request_id fail-open）**：分组键改 `(类型名, 值)`；缺失/None 按 line_no 单条成组零传染；组内多 token 前缀一致门，冲突记 `attribution_conflict` 拒绝采信（现网 92 条 0 冲突）。
1359:- **HIGH-3（transcript 归因折叠）**：恰 1 个常规文件命中才算归因（多命中 = ambiguous 拒采信）；glob 改递归下探；transcripts 根缺失整体 exit 2（拒绝产出 unrecoverable 假象）。
1360:- **MEDIUM-1**：`episode_body_full` 在盘且 sha 对账通过 → byte_exact 采信（现网 0 条，通路已备）。
1361:- **MEDIUM-2**：`duplicate_clusters` 段 + 逐条 `reference_time`（见 §6）。
1362:- **MEDIUM-3**：台账头部 privacy 字段 + 本报告 private-only 声明（见 §6）。
1363:- **LOW-1~4**：token 区间 16948–20831、长度区间 205–8036、稳定键语义重写、schema 双处证据、挂载历史证据边界——均已在正文落地。
1367:## §7c Codex round-2 复审整改记录（10/13 CLOSED → 剩余 3 项 + 3 新 LOW 全部整改）
1369:round-2 复审确认 BLOCKER-2/3、HIGH-2、MEDIUM-1~3、LOW-1~4 共 10 项 CLOSED，并抓出 3 项**未真正闭合**（均实测复现）+ 3 条新 LOW：
1371:- **BLOCKER-1 NOT-CLOSED（hardlink / case-only 别名绕过）**：原守卫比较 `resolve()` **字符串**，hardlink 指向输入、以及大小写不敏感文件系统上的 case-only 别名均绕过并截断输入。**整改**：改为比较**文件身份 `(st_dev, st_ino)`**（对已存在的 --out）+ 保留路径比较作第二道。负例实测：两种绕过均 exit 2、DLQ sha 不变。
1372:- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
1373:- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
1374:- **新 LOW ×3**：full_verified 长度范围修正为 131–180；台账 `class_distribution`/`recoverability_distribution` 补零并新增 `inline_state_distribution`（固定 schema，消费者无需补齐缺席键）；`line_count` 改用 `splitlines()` 与 records 同口径（原 `count("\n")` 在 bare CR / U+2028 下会与 records 数不一致）。
1378:## §8 复现命令
1393:## §7d Codex round-3 复审整改记录（4/6 CLOSED → 剩 2 项 + 3 新发现全部整改）
1395:round-3 确认 HIGH-1 与三条 LOW 已 CLOSED、台账数字有效且与 commit 字节一致，两项路径安全判 PARTIAL：
1397:- **BLOCKER-1 残留两条绕过**：① `protected_paths` 未含**归因到的 transcript**，`--out=<唯一 transcript>` 会截断恢复源；② check-then-open 的 **TOCTOU** 仍在（检查后、打开前把 --out 换成指向 DLQ 的链接）。**整改**：① 写出前把全部 `transcript_paths` 并入保护集；② 改 `os.open(O_WRONLY|O_CREAT|O_NOFOLLOW)` **不带 O_TRUNC** 打开 → 对**实际 fd** `fstat` 校验 inode → 通过才 `ftruncate`，检查与写入作用于同一 fd，替换攻击无效。反例实测：`--out` 指向唯一 transcript → exit 2、transcript sha 不变。
1398:- **HIGH-3 残留**：`glob(recursive=True)` 在 realpath 过滤**之前**已递归遍历（Python 3.14 glob 跟随目录 symlink 且**静默吞掉不可读子树错误**）→ 越根枚举 + "假唯一/假不可恢复"；mode `000` 的 regular transcript 仍过 `isfile()` 被判 approximate。**整改**：改 `os.walk(onerror=..., followlinks=False)`（不跟随目录 symlink、遍历错误显式捕获）+ 候选加 `os.access(R_OK)` 门；遍历受阻或存在不可读候选一律记 `attribution_conflict` 拒绝裁定（既不宣称找到、也不宣称不可恢复）。三条反例实测全部 fail-closed。
1399:- **新 MEDIUM（JSONL framing）**：生产端 `ensure_ascii=False` 可原样写出字符串内的 U+2028，`splitlines()` 会把一条合法单-LF 记录劈成两条坏行。**整改**：新增 `_split_jsonl_lines()` 严格按 LF 分帧，header `line_count` 与 records 共用同一函数。
1400:- **新 LOW（输入 schema）**：合法 JSON 但非对象（`null` / 数组 / 标量）解析成功后在 `rec.get()` 处抛 AttributeError 炸全量。**整改**：非 dict 归 `unparseable`（`not_a_json_object: <type>`），实测两条毒行不影响其余记录。
1401:- **新 LOW（provenance）**：报告头只写起始基线未区分整改 artifact commit —— 已在报告头补三段 commit 链。
1405:## §7e Codex round-4 复审整改记录（1/6 CLOSED → 全部 9 项整改）
1407:round-4 只认可 1 项 CLOSED（非 dict JSON 门），并用更深的静态反例推翻了另外 5 项的"闭合"，另提 2 BLOCKER / 1 HIGH / 2 MEDIUM / 3 LOW。逐条整改（全部实测复现→封死）：
1409:- **BLOCKER①（不可读但可写的 transcript 绕过保护集）**：mode `0200` 的候选在 unreadable 分支被清空 `transcript_paths`，因此不进保护集，`--out` 指向它仍被截断（无需竞态）。**整改**：新增 `all_candidate_paths` 保留**所有见到的候选**（含不可读、含被冲突分支清空的），写出前全部并入保护集。实测：mode 0200 候选作 `--out` → exit 2、文件字节不变。
1410:- **BLOCKER②（源侧 TOCTOU）**：保护身份按**路径** stat 采集、DLQ 稍后才按路径读取，两步间可换入另一 inode → 实际读取对象不在保护集。**整改**：`snapshot_file()` 改为 `os.open(O_RDONLY|O_NOFOLLOW|O_NONBLOCK)` → `fstat` 取身份 + regular-file 门 → **从同一 fd 读全量**，返回的身份即**实际被读取对象**；compare 副本同样以读取身份入保护集；输入 `stat` 失败不再静默吞而是 exit 2。
1411:- **HIGH（不可见被终态化为 unrecoverable）**：扫描受阻/冲突时主链仍产出 `unrecoverable`，与报告"既不宣称不可恢复"自相矛盾。**整改**：引入第四态 **`unverifiable`**（源可见性不足，basis 逐条说明是遍历受阻/不可读候选/归因冲突），distribution 与 `unverifiable_list` 同步。实测：不可读子树 → `unverifiable=1`，不再冒充 unrecoverable。
1412:- **MEDIUM（FIFO/设备节点）**：`--out` 缺 regular-file gate 与 `O_NONBLOCK`。**整改**：`O_NONBLOCK` + `S_ISREG` 双门（读侧同样）。实测：FIFO 作 `--out` → exit 2 且不阻塞。
1413:- **MEDIUM（非法 UTF-8 冒充有效记录）**：`errors="replace"` 把坏字节改写成合法对象。**整改**：`_split_jsonl_lines()` 改**逐行 strict decode**，解码失败归 `unparseable`。实测：`b'{"a":"\xff"}'` → `utf8_decode_error`，records=0。
1414:- **LOW ×3**：dict 内字段错型防御（`name=None` / `request_id=[]` 不可哈希 / `episode_body` 非 str 均不再炸全量，按 line_no 单条成组或判 anomaly）；`transcripts_dir="/"` 的 `//` containment 特例；`0o600` 对**既有**输出文件用 `fchmod` 显式收紧（实测台账 mode 现为 `-rw-------`）。
1415:- **LOW（provenance 自指）**：commit 无法自含己身 SHA，改用后置 `artifact-commit-receipt.txt` 绑定精确链，报告头指向该 receipt。
1419:（commit 无法自含己身 SHA，故用本后置 receipt 精确绑定 —— Codex round-4 LOW 整改）
1448:CARD-G4-9 round-5 终裁复审（静态审阅 + 只读复算，禁改任何文件）。你 round-4 裁定 1/6 CLOSED，提出 2 BLOCKER / 1 HIGH / 2 MEDIUM / 3 LOW。开发方以 commit d2827a6d + d8d887f2 提交整改，请逐条只读复核：
1449:1. BLOCKER 不可读但可写 transcript 绕过保护集 → resolve_group_attribution 新增 all_candidate_paths（保留所有见到的候选，含 unreadable 与被冲突分支清空的），main() 写出前遍历 group_attribution 全部并入 protected_ids。
1450:2. BLOCKER 源侧 TOCTOU → snapshot_file() 改 os.open(O_RDONLY|O_NOFOLLOW|O_NONBLOCK) → fstat 取 (st_dev,st_ino) + S_ISREG 门 → 从同一 fd os.read 全量，返回身份即实际读取对象，DLQ 与 compare 副本均以该身份入 protected_ids；输入 stat 失败改 exit 2 不再静默吞。
1451:3. HIGH 不可见终态化 → 新增第四态 unverifiable（扫描受阻/不可读候选/归因冲突），recoverability_distribution 与 unverifiable_list 同步，basis 逐条说明原因。
1452:4. MEDIUM FIFO/设备 → --out 与读侧均加 S_ISREG + O_NONBLOCK。
1453:5. MEDIUM 非法 UTF-8 → _split_jsonl_lines 改逐行 strict decode，失败归 unparseable。
1454:6. LOW ×3 → 字段错型防御（name 非 str / request_id 不可哈希 / episode_body 非 str）、根为 '/' 的 containment 特例（root_prefix）、既有输出 fchmod 0600。
1455:7. LOW provenance → 后置 receipt _bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt 记录精确 SHA 链，报告头指向它。
1456:请对每项设计静态反例判断是否仍可绕过（尤其：保护集完整性、fd 身份与实际读取的绑定、unverifiable 与 unrecoverable 的语义边界、strict decode 的边界）。同时独立复算台账仍为 92 条 / class 89-2-1 / byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0 / 重复簇 6 簇 29 行 / unparseable 0。逐项 CLOSED/NOT-CLOSED + 总裁定（可验收/仍阻断）+ 新发现分级。若已可验收请明确说明；若仍阻断请说明**对一张只读 census 卡**而言该阻断是否与卡面范围相称。
1562:# Canvas adversarial audit
1564:## When to use
1568:## Inputs / context to gather
1574:## Procedure
1584:## Efficiency plan
1590:## Pitfalls and fixes
1627:   203	            # round-4 LOW 整改: root="/" 时 root_real+sep=="//" 会让合法子项全假
1689:   265	    round-4 BLOCKER② 整改: 原实现按路径 stat 采集保护身份、稍后才按路径读取，
1693:   269	    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
1768:   344	    # round-2 HIGH-3 整改: 存在但不可读/不可遍历的根（chmod 000）此前 exit 0
1778:   354	    # --out 碰撞守卫（写前）。round-2 BLOCKER-1 整改: 比较**文件身份**
1814:   388	    # BLOCKER-2 整改: 单次读取，records 与头部描述共享同一份 exact bytes
1837:   411	        # round-3 LOW 整改: 合法 JSON 但非对象（null / 数组 / 标量）此前解析成功
1850:   424	        # round-4 LOW 整改: 不可哈希的 request_id（list/dict）按 line_no 单条成组
1887:   461	            # round-2 HIGH-1 整改: anomaly 记录不得经 full_body 分支翻案
1894:   468	            # round-4 HIGH 整改: 归因冲突/多命中/扫描受阻 ≠ "源不存在"。
2007:   577	        # round-2 LOW 整改: 固定 schema 补零，消费者无需自行补齐缺席键
2027:   597	    # round-3 BLOCKER-1 绕过① 整改: 归因到的 transcript 是恢复源，
2046:   616	        # round-3 整改: 消除 check-then-open TOCTOU。先以 O_NOFOLLOW 打开且
2050:   620	            fd = os.open(args.out, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
2056:   626	            # round-4 MEDIUM 整改: 非常规文件（FIFO/设备/socket）拒绝
2060:   630	            # round-4 LOW 整改: 0o600 只作用于新建 —— 既有文件显式收紧
2107:    12	    任一输入重合即 exit 2，防 "w" 截断输入（round-1 BLOCKER-1 + round-2
2110:    15	快照原子性（Codex round-1 BLOCKER-2 整改）:
2114:    19	判定 fail-closed（Codex round-1 HIGH-1/2/3 整改）:
2129:    34	    glob 结果拒绝 symlink 条目与逃逸到根外的目标（round-2 HIGH-3 整改）。
2134:    39	    不得经此分支翻案（round-1 MEDIUM-1 + round-2 HIGH-1 整改）。
2142:    47	    语义重复簇），G4-10 重放去重策略依据（Codex round-1 MEDIUM-2 整改）。
2144:    49	    工件，禁止外发（Codex round-1 MEDIUM-3；仓库为私有仓，纪律=不 push 公网）。
2176:    81	    - 逐行 **strict** decode（round-4 MEDIUM 整改）: errors="replace" 会把非法
2209:   114	    if not isinstance(body, str):  # round-4 LOW: episode_body 错型
2225:   130	    round-2 HIGH-1 整改: 原实现只核 sha，声明长度矛盾的记录（如 body="abc"
2239:   144	    """round-4 LOW 整改: name 非 str（None/数字/列表）不再抛异常。"""
2258:   163	        # round-4 BLOCKER① 整改: 保护集必须覆盖**所有见到的候选**（含不可读、
2271:   176	    # round-2 HIGH-3: 拒绝 symlink 条目与逃逸到根外的目标（glob 会跟随 symlink，
2281:/bin/zsh -lc "rg -n '不可读但可写|源侧 TOCTOU|不可见终态|非法 UTF-8|字段错型|root_prefix|fchmod|provenance|总裁定|BLOCKER' '_bmad-output/审查/codex-review-CARD-G4-9-round4.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
2283:15:1. BLOCKER-1 绕过①（--out 指向已归因 transcript 会截断恢复源）→ 现在写出前把全部 records[].transcript_paths 的 (st_dev,st_ino) 并入 protected_ids。
2284:16:2. BLOCKER-1 绕过②（check-then-open TOCTOU）→ 现在改 os.open(O_WRONLY|O_CREAT|O_NOFOLLOW) 不带 O_TRUNC 打开，对实际 fd 做 os.fstat 校验 inode 是否落在 protected_ids，通过后才 os.ftruncate(fd,0) 并 os.fdopen 写。请判断该顺序是否真正消除 TOCTOU，并找剩余绕过（如 O_NOFOLLOW 对中间路径组件、fd 竞争、非常规文件如 FIFO/设备）。
2285:20:6. 新 LOW（provenance）→ 报告头补 artifact commit 链 67ccebe1→73102875→fce0d8a2。
2286:21:同时独立复算台账 _bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json 仍为 92 条 / class 89-2-1 / 三态 4-88-0 / 重复簇 6 簇 29 行 / 归因冲突 0 / unparseable 0。逐项 CLOSED/NOT-CLOSED + 总裁定（可验收/仍阻断）+ 任何新发现分级。若认为已可验收请明确说明。
2288:145:rg -n \"BLOCKER-1|HIGH-3|JSONL|framing|非 dict|provenance|PARTIAL|CLOSED|NOT-CLOSED|新发现|总裁定|protected_ids|O_NOFOLLOW|os\\.walk|line_count\" '_bmad-output/审查/codex-review-CARD-G4-9-round3.md' | head -n 240
2289:160:14:CARD-G4-9 round-3 复审（静态审阅 + 只读复算）。你 round-2 裁定 10/13 CLOSED，三项 NOT-CLOSED：BLOCKER-1（--out 守卫比 resolve 字符串，hardlink 与 case-only 别名绕过截断输入）、HIGH-1（full_body_verified 只核 sha 不核长度且排在 anomaly 分支前，anomaly 记录被判 byte_exact）、HIGH-3（chmod 000 根 exit 0 假判 unrecoverable；glob 跟随 symlink 逃逸出根）；另 3 新 LOW（full_verified 长度范围应 131-180、distribution 省略 0 值键、line_count 数 LF 与 records 的 splitlines 口径不一）。开发方以 commit 73102875 提交整改。请只读复核这 6 项是否闭合：
2290:162:17:请：逐项 CLOSED/NOT-CLOSED（对每项设计静态反例判断是否仍可绕过，如相对路径/大小写/软硬链接组合、判定链其它入口、glob 边界）；独立复算台账仍为 92 条 / class 89-2-1 / 三态 4-88-0 / 重复簇 6 簇 29 行 / full_verified 长度 131-180；给总裁定（可验收/仍阻断）与任何新发现分级。
2292:168:151:  • 交叉核验高严重度项并给出逐项与总裁定
2293:169:366:  **① P1-05 第四轮返工（P1-05d）已落地，待五轮终裁** — Codex 四轮（`2026-08-19` 终裁文档）判 F-02/F-05 CLOSED、其余 STILL-OPEN；九路验证（`2026-08-20-Codex四轮终裁-九路验证与C批次方案.md`）9/9 CONFIRMED 含 B3 新回归一条。C 批全部落地：**C2**（`1683328c`：脏 last_examined 投影 None 止血 B3 新回归 · freshness 嵌套错型自愈 · 5 处 ID 切片改丢弃 · _id_ok 写侧过滤同源 · lag_seconds finite · 控制字符全拒）· **C3**（`d39983ce`：conversation_summary caller 显式传 vault 组修恒空 bug · ensure_entity_node 隔离身份拒绝复用）· **C1**（`c154a7f2`：lib 层 _resolves_outside_vault 接 LanceDB 两真实入口 open 前 · orchestrator 裸 fnmatch 换 canon + 扫描产出过 should_index 根除 hash-before-admission + realpath containment · by-node missing→404/path_rejected→422；新 test_real_entrypoint_admission.py 6 条真实入口行为锁）· **C4**（census Q2 中性化+前缀分类）。**遗留**：B4（payload 命名空间/provenance）独立轮 · TOCTOU 换链残余窗口（realpath 判定与 open 非原子，诚实登记）· P1-03/P1-04 押后
2295:173:622:-    输入文件；Codex round-1 BLOCKER-1 整改）。
2296:174:625:+    任一输入重合即 exit 2，防 "w" 截断输入（round-1 BLOCKER-1 + round-2
2297:182:885:+    # --out 碰撞守卫（写前）。round-2 BLOCKER-1 整改: 比较**文件身份**
2298:186:1214: - **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
2299:187:1215: - **BLOCKER-2（快照不原子）**：DLQ 单次 `read_bytes()`，头部 sha256/line_count 与逐条 records 派生自同一份内存字节；mtime 显式标注为 stat 参考值。
2300:190:1229:+round-2 复审确认 BLOCKER-2/3、HIGH-2、MEDIUM-1~3、LOW-1~4 共 10 项 CLOSED，并抓出 3 项**未真正闭合**（均实测复现）+ 3 条新 LOW：
2301:191:1231:+- **BLOCKER-1 NOT-CLOSED（hardlink / case-only 别名绕过）**：原守卫比较 `resolve()` **字符串**，hardlink 指向输入、以及大小写不敏感文件系统上的 case-only 别名均绕过并截断输入。**整改**：改为比较**文件身份 `(st_dev, st_ino)`**（对已存在的 --out）+ 保留路径比较作第二道。负例实测：两种绕过均 exit 2、DLQ sha 不变。
2303:201:1441:    12	    任一输入重合即 exit 2，防 "w" 截断输入（round-1 BLOCKER-1 + round-2
2304:208:1698:   265	    # --out 碰撞守卫（写前）。round-2 BLOCKER-1 整改: 比较**文件身份**
2305:213:1937:99:- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
2306:214:1938:100:- **BLOCKER-2（快照不原子）**：DLQ 单次 `read_bytes()`，头部 sha256/line_count 与逐条 records 派生自同一份内存字节；mtime 显式标注为 stat 参考值。
2307:216:1945:116:- **BLOCKER-1 NOT-CLOSED（hardlink / case-only 别名绕过）**：原守卫比较 `resolve()` **字符串**，hardlink 指向输入、以及大小写不敏感文件系统上的 case-only 别名均绕过并截断输入。**整改**：改为比较**文件身份 `(st_dev, st_ino)`**（对已存在的 --out）+ 保留路径比较作第二道。负例实测：两种绕过均 exit 2、DLQ sha 不变。
2308:224:2137:     1	> **存档说明**: codex exec 完成审查后被 cyber 误拦（exit 1，重定向文件空——MEMORY 已录 codex 三坑之一）。本文件由 task stdout 抢救提取，内容为 Codex round-2 原文（自"总裁定"起至结论段止），未作任何改写。
2309:225:2139:     3	总裁定：**仍阻断 / 不可验收**。`67ccebe1` 确实冻结了交付物，92 条数字也可独立复算；但实际只有 **10/13 CLOSED**，`BLOCKER-1`、`HIGH-1`、`HIGH-3` 仍未闭合。
2310:226:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
2311:227:2144:     8	| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
2312:228:2145:     9	| BLOCKER-3 | **CLOSED** | `git show 67ccebe1 --stat` 为 10 个 G4-9 文件、3384 insertions，包含脚本、报告、ledger、证据包、round-1 审查和 UAT。当前 HEAD 为 `e7a480eb`，但全部 G4-9 路径相对 `67ccebe1` diff 为空。关键 blob：script `ea370cb…`、report `ff1f71d…`、ledger `6ce5772…`。 |
2313:245:2765:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:7:| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
2314:246:2766:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:8:| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
2315:250:2772:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:14:CARD-G4-9 round-3 复审（静态审阅 + 只读复算）。你 round-2 裁定 10/13 CLOSED，三项 NOT-CLOSED：BLOCKER-1（--out 守卫比 resolve 字符串，hardlink 与 case-only 别名绕过截断输入）、HIGH-1（full_body_verified 只核 sha 不核长度且排在 anomaly 分支前，anomaly 记录被判 byte_exact）、HIGH-3（chmod 000 根 exit 0 假判 unrecoverable；glob 跟随 symlink 逃逸出根）；另 3 新 LOW（full_verified 长度范围应 131-180、distribution 省略 0 值键、line_count 数 LF 与 records 的 splitlines 口径不一）。开发方以 commit 73102875 提交整改。请只读复核这 6 项是否闭合：
2316:256:2815:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
2317:257:2816:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2144:     8	| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
2319:265:3127:  • 交叉核验高严重度项并给出逐项与总裁定
2321:271:3487:  ✓ 交叉核验高严重度项并给出逐项与总裁定
2322:272:3506:总裁定：**仍阻断 / 不可验收**。整改提交 `73102875fdd9837f0d60cf2ed6cf4ea7f6f8c2e5` 与当前文件字节一致，台账数字有效；但六项仅 **4 CLOSED / 2 NOT-CLOSED**。
2323:273:3510:| BLOCKER-1 | **NOT-CLOSED / PARTIAL** | 稳定状态下，relative、`..`、case-only、既存 symlink/hardlink 组合已由 [resolve+inode 门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:265)挡住。但仍有两条绕过：① `protected_paths` 不含已被归因的 transcript，直接令 `--out=<唯一 transcript>`，脚本会先判其为恢复源，最后在 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:457)将其截断；② round-2 已指出的 TOCTOU 仍在——检查后、最终打开前将安全输出替换成指向 DLQ 的 symlink/hardlink，即可 `O_TRUNC` 输入。 |
2324:281:3532:- **LOW — provenance/evidence**：[报告头](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:5)仍只写起始基线 `37387a86`，未明确区分整改 artifact `73102875`；§7 的 HIGH-1 负例也只隔离验证了长度门，没有单独验证 anomaly 顺序门，尽管代码经更强反例确认正确。
2325:282:3534:所以：**冻结的 92 条 ledger 数值可采信；CARD-G4-9 生成器与整卡验收仍被 BLOCKER-1、HIGH-3 阻断。** 本轮未修改仓库或受审数据，未执行破坏性 fixture/G4-10 重放；Graphiti 工具本轮不可用。
2326:283:3539:总裁定：**仍阻断 / 不可验收**。整改提交 `73102875fdd9837f0d60cf2ed6cf4ea7f6f8c2e5` 与当前文件字节一致，台账数字有效；但六项仅 **4 CLOSED / 2 NOT-CLOSED**。
2327:284:3543:| BLOCKER-1 | **NOT-CLOSED / PARTIAL** | 稳定状态下，relative、`..`、case-only、既存 symlink/hardlink 组合已由 [resolve+inode 门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:265)挡住。但仍有两条绕过：① `protected_paths` 不含已被归因的 transcript，直接令 `--out=<唯一 transcript>`，脚本会先判其为恢复源，最后在 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:457)将其截断；② round-2 已指出的 TOCTOU 仍在——检查后、最终打开前将安全输出替换成指向 DLQ 的 symlink/hardlink，即可 `O_TRUNC` 输入。 |
2328:292:3565:- **LOW — provenance/evidence**：[报告头](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:5)仍只写起始基线 `37387a86`，未明确区分整改 artifact `73102875`；§7 的 HIGH-1 负例也只隔离验证了长度门，没有单独验证 anomaly 顺序门，尽管代码经更强反例确认正确。
2329:293:3567:所以：**冻结的 92 条 ledger 数值可采信；CARD-G4-9 生成器与整卡验收仍被 BLOCKER-1、HIGH-3 阻断。** 本轮未修改仓库或受审数据，未执行破坏性 fixture/G4-10 重放；Graphiti 工具本轮不可用。
2330:317:+- **BLOCKER-1 残留两条绕过**：① `protected_paths` 未含**归因到的 transcript**，`--out=<唯一 transcript>` 会截断恢复源；② check-then-open 的 **TOCTOU** 仍在（检查后、打开前把 --out 换成指向 DLQ 的链接）。**整改**：① 写出前把全部 `transcript_paths` 并入保护集；② 改 `os.open(O_WRONLY|O_CREAT|O_NOFOLLOW)` **不带 O_TRUNC** 打开 → 对**实际 fd** `fstat` 校验 inode → 通过才 `ftruncate`，检查与写入作用于同一 fd，替换攻击无效。反例实测：`--out` 指向唯一 transcript → exit 2、transcript sha 不变。
2331:321:+- **新 LOW（provenance）**：报告头只写起始基线未区分整改 artifact commit —— 已在报告头补三段 commit 链。
2332:442:     # --out 碰撞守卫（写前）。round-2 BLOCKER-1 整改: 比较**文件身份**
2333:455:     # BLOCKER-2 整改: 单次读取，records 与头部描述共享同一份 exact bytes
2334:480:+    # round-3 BLOCKER-1 绕过① 整改: 归因到的 transcript 是恢复源，
2335:573:    12	    任一输入重合即 exit 2，防 "w" 截断输入（round-1 BLOCKER-1 + round-2
2336:576:    15	快照原子性（Codex round-1 BLOCKER-2 整改）:
2337:865:   304	    # --out 碰撞守卫（写前）。round-2 BLOCKER-1 整改: 比较**文件身份**
2338:897:   336	    # BLOCKER-2 整改: 单次读取，records 与头部描述共享同一份 exact bytes
2339:1062:   501	    # round-3 BLOCKER-1 绕过① 整改: 归因到的 transcript 是恢复源，
2340:1211:    99	- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
2341:1212:   100	- **BLOCKER-2（快照不原子）**：DLQ 单次 `read_bytes()`，头部 sha256/line_count 与逐条 records 派生自同一份内存字节；mtime 显式标注为 stat 参考值。
2342:1213:   101	- **BLOCKER-3（交付物未冻结漂移）**：以本卡 commit 冻结全部交付物 exact bytes（脚本/报告/台账/证据包同 commit）；grep-selfattest 已按最终版行号重生成并内嵌脚本 sha 前缀。
2343:1226:   114	round-2 复审确认 BLOCKER-2/3、HIGH-2、MEDIUM-1~3、LOW-1~4 共 10 项 CLOSED，并抓出 3 项**未真正闭合**（均实测复现）+ 3 条新 LOW：
2344:1228:   116	- **BLOCKER-1 NOT-CLOSED（hardlink / case-only 别名绕过）**：原守卫比较 `resolve()` **字符串**，hardlink 指向输入、以及大小写不敏感文件系统上的 case-only 别名均绕过并截断输入。**整改**：改为比较**文件身份 `(st_dev, st_ino)`**（对已存在的 --out）+ 保留路径比较作第二道。负例实测：两种绕过均 exit 2、DLQ sha 不变。
2345:1254:   142	- **BLOCKER-1 残留两条绕过**：① `protected_paths` 未含**归因到的 transcript**，`--out=<唯一 transcript>` 会截断恢复源；② check-then-open 的 **TOCTOU** 仍在（检查后、打开前把 --out 换成指向 DLQ 的链接）。**整改**：① 写出前把全部 `transcript_paths` 并入保护集；② 改 `os.open(O_WRONLY|O_CREAT|O_NOFOLLOW)` **不带 O_TRUNC** 打开 → 对**实际 fd** `fstat` 校验 inode → 通过才 `ftruncate`，检查与写入作用于同一 fd，替换攻击无效。反例实测：`--out` 指向唯一 transcript → exit 2、transcript sha 不变。
2346:1258:   146	- **新 LOW（provenance）**：报告头只写起始基线未区分整改 artifact commit —— 已在报告头补三段 commit 链。
2347:1420:   501	    # round-3 BLOCKER-1 绕过① 整改: 归因到的 transcript 是恢复源，
2349:1956:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:142:- **BLOCKER-1 残留两条绕过**：① `protected_paths` 未含**归因到的 transcript**，`--out=<唯一 transcript>` 会截断恢复源；② check-then-open 的 **TOCTOU** 仍在（检查后、打开前把 --out 换成指向 DLQ 的链接）。**整改**：① 写出前把全部 `transcript_paths` 并入保护集；② 改 `os.open(O_WRONLY|O_CREAT|O_NOFOLLOW)` **不带 O_TRUNC** 打开 → 对**实际 fd** `fstat` 校验 inode → 通过才 `ftruncate`，检查与写入作用于同一 fd，替换攻击无效。反例实测：`--out` 指向唯一 transcript → exit 2、transcript sha 不变。
2354:2301:总裁定：**仍阻断 / 不可验收**。六项仅 **1/6 CLOSED**。冻结台账的数字本身可采信，但生成器仍存在可截断恢复源的 BLOCKER，不能据此接受 CARD‑G4‑9。
2355:2305:| 1. transcript 纳入保护集 | **NOT-CLOSED / PARTIAL** | 稳定状态下，[保护循环](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:503)确实覆盖当前 89 个路径引用、7 个唯一 inode。但不可读候选会在 [180–186](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:180)清空 `transcript_paths`，因此不进入保护集。owner mode `0200` 的匹配 transcript 不可读但可写，`--out` 指向它时仍能在 [517–529](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:517)被截断；无需竞态。另 `stat` 失败被 [直接吞掉](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:506)，也不是“全部并入”的 fail-closed 实现。 |
2356:2310:| 6. provenance | **NOT-CLOSED（LOW）** | Git 实际 ancestry 与三个受审 blob 均能绑定到 `fce0d8a2`；但[报告头](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:5)只写 `67ccebe1 → 73102875 → 本次 round-3 整改 commit`，没有字面 `fce0d8a2`。由于 commit 不能自包含自身 SHA，需用后置 receipt/tag/manifest 明确绑定，不能以模糊代称冒充精确三段链。 |
2357:2314:- **BLOCKER**：不可读但可写 transcript 可绕过保护集并被截断。
2358:2315:- **BLOCKER**：protected source identity 与实际读取对象未绑定，源侧 TOCTOU 仍在。
2359:2319:- **LOW**：合法 dict 内字段错型仍可炸全量，例如 `request_id=[]`、`name=None`、`episode_body=None`。
2360:2338:总裁定：**仍阻断 / 不可验收**。六项仅 **1/6 CLOSED**。冻结台账的数字本身可采信，但生成器仍存在可截断恢复源的 BLOCKER，不能据此接受 CARD‑G4‑9。
2361:2342:| 1. transcript 纳入保护集 | **NOT-CLOSED / PARTIAL** | 稳定状态下，[保护循环](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:503)确实覆盖当前 89 个路径引用、7 个唯一 inode。但不可读候选会在 [180–186](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:180)清空 `transcript_paths`，因此不进入保护集。owner mode `0200` 的匹配 transcript 不可读但可写，`--out` 指向它时仍能在 [517–529](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:517)被截断；无需竞态。另 `stat` 失败被 [直接吞掉](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:506)，也不是“全部并入”的 fail-closed 实现。 |
2362:2347:| 6. provenance | **NOT-CLOSED（LOW）** | Git 实际 ancestry 与三个受审 blob 均能绑定到 `fce0d8a2`；但[报告头](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:5)只写 `67ccebe1 → 73102875 → 本次 round-3 整改 commit`，没有字面 `fce0d8a2`。由于 commit 不能自包含自身 SHA，需用后置 receipt/tag/manifest 明确绑定，不能以模糊代称冒充精确三段链。 |
2363:2351:- **BLOCKER**：不可读但可写 transcript 可绕过保护集并被截断。
2364:2352:- **BLOCKER**：protected source identity 与实际读取对象未绑定，源侧 TOCTOU 仍在。
2365:2356:- **LOW**：合法 dict 内字段错型仍可炸全量，例如 `request_id=[]`、`name=None`、`episode_body=None`。
2382:  2301	总裁定：**仍阻断 / 不可验收**。六项仅 **1/6 CLOSED**。冻结台账的数字本身可采信，但生成器仍存在可截断恢复源的 BLOCKER，不能据此接受 CARD‑G4‑9。
2386:  2305	| 1. transcript 纳入保护集 | **NOT-CLOSED / PARTIAL** | 稳定状态下，[保护循环](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:503)确实覆盖当前 89 个路径引用、7 个唯一 inode。但不可读候选会在 [180–186](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:180)清空 `transcript_paths`，因此不进入保护集。owner mode `0200` 的匹配 transcript 不可读但可写，`--out` 指向它时仍能在 [517–529](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:517)被截断；无需竞态。另 `stat` 失败被 [直接吞掉](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:506)，也不是“全部并入”的 fail-closed 实现。 |
2387:  2306	| 2. fd 上校验 TOCTOU | **NOT-CLOSED / PARTIAL** | `open` 不带 `O_TRUNC`，随后同一 fd 上 `fstat→ftruncate`，确实封住了最终组件换链及稳定 protected inode/hardlink；外部进程不能重新绑定本进程 fd，未发现 fd-number 竞争。但源身份早在 [312–317](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:312)按路径采集，DLQ 到 [337](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:337)才读取。静态调度 `protected=A → 将 inode B 换入 DLQ → snapshot 读取 B → --out hardlink B → fstat 不命中 A → truncate B` 仍可截断本次实际读取源。`O_NOFOLLOW` 也只保护最终组件；中间 symlink 可重定向至未保护对象。 |
2388:  2307	| 3. HIGH-3 枚举 | **NOT-CLOSED** | 稳态目录 symlink、`scandir` 错误和 mode `000` 门已有改善。但 unreadable/walk error 设置 conflict 后，主链仍在 [395–397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:395)明确产出 `recoverability=unrecoverable`，直接反驳报告所称“既不宣称不可恢复” [报告:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:143)。此外 `os.walk.onerror` 只覆盖 `scandir`；逐条 `is_dir/stat` 错误可被静默当非候选，[islink→isfile→access→realpath](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:168)仍是路径级竞态。 |
2389:  2308	| 4. JSONL framing | **NOT-CLOSED / PARTIAL** | U+2028、裸 CR 误分帧已修，header 与 records 共用 helper。但 [`_split_jsonl_lines()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:76)有 `b"\n" → []`，把一条非法空白行静默算成零行；`decode(errors="replace")` 还会把非法 UTF‑8 `b'{"a":"\\xff"}\n'` 改写成合法对象而非 unparseable。 |
2390:  2309	| 5. 非 dict JSON | **CLOSED** | [`isinstance(rec, dict)` 门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:351)位于任何 `.get()` 和 `records.append()` 前；`null`、数组、标量均进入 `unparseable`。 |
2391:  2310	| 6. provenance | **NOT-CLOSED（LOW）** | Git 实际 ancestry 与三个受审 blob 均能绑定到 `fce0d8a2`；但[报告头](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:5)只写 `67ccebe1 → 73102875 → 本次 round-3 整改 commit`，没有字面 `fce0d8a2`。由于 commit 不能自包含自身 SHA，需用后置 receipt/tag/manifest 明确绑定，不能以模糊代称冒充精确三段链。 |
2395:  2314	- **BLOCKER**：不可读但可写 transcript 可绕过保护集并被截断。
2396:  2315	- **BLOCKER**：protected source identity 与实际读取对象未绑定，源侧 TOCTOU 仍在。
2397:  2316	- **HIGH**：扫描不可见性仍被终态化为 `unrecoverable`。
2398:  2317	- **MEDIUM**：缺少 regular-file gate 和 `O_NONBLOCK`；FIFO 可在 `fstat` 前阻塞，设备节点进入平台相关 `ftruncate`。
2399:  2318	- **MEDIUM**：非法 UTF‑8经 replacement 后可被当作有效记录。
2400:  2319	- **LOW**：合法 dict 内字段错型仍可炸全量，例如 `request_id=[]`、`name=None`、`episode_body=None`。
2401:  2320	- **LOW**：`transcripts_dir="/"` 时 `root_real + os.sep == "//"`，合法子项均无法通过 containment。
2402:  2321	- **LOW**：`0o600` 只作用于新建输出，覆盖既有 `0644` private-only ledger 不会收紧权限。
2419:  2338	总裁定：**仍阻断 / 不可验收**。六项仅 **1/6 CLOSED**。冻结台账的数字本身可采信，但生成器仍存在可截断恢复源的 BLOCKER，不能据此接受 CARD‑G4‑9。
2423:  2342	| 1. transcript 纳入保护集 | **NOT-CLOSED / PARTIAL** | 稳定状态下，[保护循环](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:503)确实覆盖当前 89 个路径引用、7 个唯一 inode。但不可读候选会在 [180–186](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:180)清空 `transcript_paths`，因此不进入保护集。owner mode `0200` 的匹配 transcript 不可读但可写，`--out` 指向它时仍能在 [517–529](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:517)被截断；无需竞态。另 `stat` 失败被 [直接吞掉](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:506)，也不是“全部并入”的 fail-closed 实现。 |
2424:  2343	| 2. fd 上校验 TOCTOU | **NOT-CLOSED / PARTIAL** | `open` 不带 `O_TRUNC`，随后同一 fd 上 `fstat→ftruncate`，确实封住了最终组件换链及稳定 protected inode/hardlink；外部进程不能重新绑定本进程 fd，未发现 fd-number 竞争。但源身份早在 [312–317](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:312)按路径采集，DLQ 到 [337](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:337)才读取。静态调度 `protected=A → 将 inode B 换入 DLQ → snapshot 读取 B → --out hardlink B → fstat 不命中 A → truncate B` 仍可截断本次实际读取源。`O_NOFOLLOW` 也只保护最终组件；中间 symlink 可重定向至未保护对象。 |
2425:  2344	| 3. HIGH-3 枚举 | **NOT-CLOSED** | 稳态目录 symlink、`scandir` 错误和 mode `000` 门已有改善。但 unreadable/walk error 设置 conflict 后，主链仍在 [395–397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:395)明确产出 `recoverability=unrecoverable`，直接反驳报告所称“既不宣称不可恢复” [报告:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:143)。此外 `os.walk.onerror` 只覆盖 `scandir`；逐条 `is_dir/stat` 错误可被静默当非候选，[islink→isfile→access→realpath](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:168)仍是路径级竞态。 |
2426:  2345	| 4. JSONL framing | **NOT-CLOSED / PARTIAL** | U+2028、裸 CR 误分帧已修，header 与 records 共用 helper。但 [`_split_jsonl_lines()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:76)有 `b"\n" → []`，把一条非法空白行静默算成零行；`decode(errors="replace")` 还会把非法 UTF‑8 `b'{"a":"\\xff"}\n'` 改写成合法对象而非 unparseable。 |
2427:  2346	| 5. 非 dict JSON | **CLOSED** | [`isinstance(rec, dict)` 门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:351)位于任何 `.get()` 和 `records.append()` 前；`null`、数组、标量均进入 `unparseable`。 |
2428:  2347	| 6. provenance | **NOT-CLOSED（LOW）** | Git 实际 ancestry 与三个受审 blob 均能绑定到 `fce0d8a2`；但[报告头](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:5)只写 `67ccebe1 → 73102875 → 本次 round-3 整改 commit`，没有字面 `fce0d8a2`。由于 commit 不能自包含自身 SHA，需用后置 receipt/tag/manifest 明确绑定，不能以模糊代称冒充精确三段链。 |
2432:  2351	- **BLOCKER**：不可读但可写 transcript 可绕过保护集并被截断。
2433:  2352	- **BLOCKER**：protected source identity 与实际读取对象未绑定，源侧 TOCTOU 仍在。
2434:  2353	- **HIGH**：扫描不可见性仍被终态化为 `unrecoverable`。
2435:  2354	- **MEDIUM**：缺少 regular-file gate 和 `O_NONBLOCK`；FIFO 可在 `fstat` 前阻塞，设备节点进入平台相关 `ftruncate`。
2436:  2355	- **MEDIUM**：非法 UTF‑8经 replacement 后可被当作有效记录。
2437:  2356	- **LOW**：合法 dict 内字段错型仍可炸全量，例如 `request_id=[]`、`name=None`、`episode_body=None`。
2438:  2357	- **LOW**：`transcripts_dir="/"` 时 `root_real + os.sep == "//"`，合法子项均无法通过 containment。
2439:  2358	- **LOW**：`0o600` 只作用于新建输出，覆盖既有 `0644` private-only ledger 不会收紧权限。
2484:     2	（commit 无法自含己身 SHA，故用本后置 receipt 精确绑定 —— Codex round-4 LOW 整改）
2503:     5	> **代码基线**: 分析对象锚定 `37387a86`（第五批开工基线）。**本卡交付物 artifact commit 链**：精确 SHA 逐段记录于 `_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt`（commit 无法自含己身 SHA，故用后置 receipt 绑定——Codex round-4 LOW 整改）
2968:35:| Codex 独立审查 round-1 | **BLOCKED**（3 BLOCKER：--out 可截断输入 / 快照不原子 / 交付物未冻结；3 HIGH：inline 判定 fail-open / request_id 归因传染 / transcript 归因折叠；3 MEDIUM + 4 LOW。同时确认：**当前 92 条数字逐项 0 mismatch**、class/三态/家族计数全对） | `_bmad-output/审查/codex-review-CARD-G4-9.md` |
2969:37:| Codex 复审 round-2 | **仍阻断**（10/13 CLOSED；BLOCKER-1/HIGH-1/HIGH-3 未真正闭合 + 3 新 LOW）。同时独立复算确认：67ccebe1 冻结生效、92 条数字与 6/29 重复簇全部可复算 | `_bmad-output/审查/codex-review-CARD-G4-9-round2.md`（codex 被 cyber 误拦，内容由 stdout 抢救存档） |
2970:40:| round-3 findings 逐条整改 | **6/6 完成**：transcript 并入保护集 / O_NOFOLLOW+fstat 消 TOCTOU / os.walk 替 glob（不跟随目录 symlink+遍历错误显式捕获）/ 不可读候选 fail-closed / JSONL 严格 LF 分帧 / 非 dict 归 unparseable。6 条新反例实测全过、数字第三次不变 | 报告 §7d + `grep-selfattest.txt` |
2971:42:| round-4 findings 逐条整改 | **9/9 完成**：全候选入保护集 / 读侧 fd 身份消源侧 TOCTOU / 新增 unverifiable 第四态 / FIFO 设备门 / strict UTF-8 / 3 条错型与边界 LOW / provenance receipt。5 条新反例实测全过；第四次全量重跑数字仍不变 | 报告 §7e + `grep-selfattest.txt` |
2973:50:- **HIGH-1 inline 判定 fail-open**：sha 匹配但长度不符会误判 full_verified（反例实测）。整改：长度精确匹配门 + 64-hex 合法性门 + anomaly 一律 fail-closed（unrecoverable + 如实 basis）。
2974:52:- **HIGH-3 transcript 归因折叠**：多命中照单全收、目录缺失误判 unrecoverable=88（实测复现）。整改：恰 1 常规文件命中门 + 递归 glob + 目录缺失 exit 2 拒诊。
2977:73:- **BLOCKER-1 仍 PARTIAL**：① 保护集漏了**归因到的 transcript**——`--out` 指向它会截断恢复源；② check-then-open 的 **TOCTOU** 仍在。→ ① transcript 写前并入保护集；② 改 `O_NOFOLLOW` 打开且**不带 O_TRUNC**，对实际 fd `fstat` 校验后才 `ftruncate`。反例实测：exit 2、transcript 完好。
3065:   145	- **新 MEDIUM（JSONL framing）**：生产端 `ensure_ascii=False` 可原样写出字符串内的 U+2028，`splitlines()` 会把一条合法单-LF 记录劈成两条坏行。**整改**：新增 `_split_jsonl_lines()` 严格按 LF 分帧，header `line_count` 与 records 共用同一函数。
3066:   146	- **新 LOW（输入 schema）**：合法 JSON 但非对象（`null` / 数组 / 标量）解析成功后在 `rec.get()` 处抛 AttributeError 炸全量。**整改**：非 dict 归 `unparseable`（`not_a_json_object: <type>`），实测两条毒行不影响其余记录。
3067:   147	- **新 LOW（provenance）**：报告头只写起始基线未区分整改 artifact commit —— 已在报告头补三段 commit 链。
3071:   151	## §7e Codex round-4 复审整改记录（1/6 CLOSED → 全部 9 项整改）
3073:   153	round-4 只认可 1 项 CLOSED（非 dict JSON 门），并用更深的静态反例推翻了另外 5 项的"闭合"，另提 2 BLOCKER / 1 HIGH / 2 MEDIUM / 3 LOW。逐条整改（全部实测复现→封死）：
3075:   155	- **BLOCKER①（不可读但可写的 transcript 绕过保护集）**：mode `0200` 的候选在 unreadable 分支被清空 `transcript_paths`，因此不进保护集，`--out` 指向它仍被截断（无需竞态）。**整改**：新增 `all_candidate_paths` 保留**所有见到的候选**（含不可读、含被冲突分支清空的），写出前全部并入保护集。实测：mode 0200 候选作 `--out` → exit 2、文件字节不变。
3076:   156	- **BLOCKER②（源侧 TOCTOU）**：保护身份按**路径** stat 采集、DLQ 稍后才按路径读取，两步间可换入另一 inode → 实际读取对象不在保护集。**整改**：`snapshot_file()` 改为 `os.open(O_RDONLY|O_NOFOLLOW|O_NONBLOCK)` → `fstat` 取身份 + regular-file 门 → **从同一 fd 读全量**，返回的身份即**实际被读取对象**；compare 副本同样以读取身份入保护集；输入 `stat` 失败不再静默吞而是 exit 2。
3077:   157	- **HIGH（不可见被终态化为 unrecoverable）**：扫描受阻/冲突时主链仍产出 `unrecoverable`，与报告"既不宣称不可恢复"自相矛盾。**整改**：引入第四态 **`unverifiable`**（源可见性不足，basis 逐条说明是遍历受阻/不可读候选/归因冲突），distribution 与 `unverifiable_list` 同步。实测：不可读子树 → `unverifiable=1`，不再冒充 unrecoverable。
3078:   158	- **MEDIUM（FIFO/设备节点）**：`--out` 缺 regular-file gate 与 `O_NONBLOCK`。**整改**：`O_NONBLOCK` + `S_ISREG` 双门（读侧同样）。实测：FIFO 作 `--out` → exit 2 且不阻塞。
3079:   159	- **MEDIUM（非法 UTF-8 冒充有效记录）**：`errors="replace"` 把坏字节改写成合法对象。**整改**：`_split_jsonl_lines()` 改**逐行 strict decode**，解码失败归 `unparseable`。实测：`b'{"a":"\xff"}'` → `utf8_decode_error`，records=0。
3080:   160	- **LOW ×3**：dict 内字段错型防御（`name=None` / `request_id=[]` 不可哈希 / `episode_body` 非 str 均不再炸全量，按 line_no 单条成组或判 anomaly）；`transcripts_dir="/"` 的 `//` containment 特例；`0o600` 对**既有**输出文件用 `fchmod` 显式收紧（实测台账 mode 现为 `-rw-------`）。
3081:   161	- **LOW（provenance 自指）**：commit 无法自含己身 SHA，改用后置 `artifact-commit-receipt.txt` 绑定精确链，报告头指向该 receipt。
3111:    35	| Codex 独立审查 round-1 | **BLOCKED**（3 BLOCKER：--out 可截断输入 / 快照不原子 / 交付物未冻结；3 HIGH：inline 判定 fail-open / request_id 归因传染 / transcript 归因折叠；3 MEDIUM + 4 LOW。同时确认：**当前 92 条数字逐项 0 mismatch**、class/三态/家族计数全对） | `_bmad-output/审查/codex-review-CARD-G4-9.md` |
3113:    37	| Codex 复审 round-2 | **仍阻断**（10/13 CLOSED；BLOCKER-1/HIGH-1/HIGH-3 未真正闭合 + 3 新 LOW）。同时独立复算确认：67ccebe1 冻结生效、92 条数字与 6/29 重复簇全部可复算 | `_bmad-output/审查/codex-review-CARD-G4-9-round2.md`（codex 被 cyber 误拦，内容由 stdout 抢救存档） |
3114:    38	| round-2 findings 逐条整改 | **6/6 完成**：inode 身份守卫封 hardlink+大小写别名 / full_body 长度门+anomaly 前置 / 不可读根 exit 2+symlink 逃逸拒采信 / 3 新 LOW。5 条新负例实测全过、正例无回归、数字仍逐项一致 | 报告 §7/§7c + `grep-selfattest.txt` |
3115:    39	| Codex 复审 round-3 | **仍阻断**（4/6 CLOSED；BLOCKER-1/HIGH-3 判 PARTIAL + 1 新 MEDIUM + 2 新 LOW）。同时确认：HIGH-1 与三条 LOW 已闭合、台账数字有效且与 commit 字节一致 | `_bmad-output/审查/codex-review-CARD-G4-9-round3.md` |
3116:    40	| round-3 findings 逐条整改 | **6/6 完成**：transcript 并入保护集 / O_NOFOLLOW+fstat 消 TOCTOU / os.walk 替 glob（不跟随目录 symlink+遍历错误显式捕获）/ 不可读候选 fail-closed / JSONL 严格 LF 分帧 / 非 dict 归 unparseable。6 条新反例实测全过、数字第三次不变 | 报告 §7d + `grep-selfattest.txt` |
3117:    41	| Codex 复审 round-4 | **仍阻断**（1/6 CLOSED；2 新 BLOCKER + 1 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round4.md` |
3118:    42	| round-4 findings 逐条整改 | **9/9 完成**：全候选入保护集 / 读侧 fd 身份消源侧 TOCTOU / 新增 unverifiable 第四态 / FIFO 设备门 / strict UTF-8 / 3 条错型与边界 LOW / provenance receipt。5 条新反例实测全过；第四次全量重跑数字仍不变 | 报告 §7e + `grep-selfattest.txt` |
3157:21:--- (4) 唯一写出口 + 其安全门（O_NOFOLLOW/O_NONBLOCK → fstat → S_ISREG → inode 校验 → fchmod → ftruncate）:
3159:23-620:            fd = os.open(args.out, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
3313:# branch.oid d8d887f29377b8babc49f5dda0d4c4ba01168ad3
3314:# branch.head card/s5-census
3332:总裁定：**仍阻断 / CARD-G4-9 不可验收**。  
3335:### 逐项终裁
3339:| 1. transcript 全候选保护 | **NOT-CLOSED · BLOCKER** | 多 token 非前缀一致时在扫描前直接返回，[script:168](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:168)，此时 `all_candidate_paths=[]`。同一 `request_id` 含 `session:aaaaa`、`session:bbbbb`，`--out` 指向 `aaaaa….jsonl`，不会进入 [保护循环:599](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:599)，最终仍可在 [ftruncate:639](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:639)截断。无需竞态。不可列举但可穿越的子目录也有同类绕过；后置 transcript `stat` 失败仍被 `continue` 吞掉。 |
3340:| 2. 源侧 fd 身份绑定 | **NOT-CLOSED / PARTIAL · BLOCKER** | DLQ/compare 的狭义修复已 CLOSED：同一 fd `open→fstat→read→identity`，[snapshot:262](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:262)、[DLQ:389](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:389)、[compare:542](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:542)。但 `qa_metrics_db` 仍是早期 path-stat、稍后 SQLite 按路径重新打开，[probe:233](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:233)。可令 stat 看到 inode A、SQLite 实际读取换入的 B、`--out` 为 B 的 hardlink，最终 B 不在保护集并被截断。 |
3341:| 3. `unverifiable` 四态 | **NOT-CLOSED · HIGH** | distribution/list 同步已实现。但 `anomaly→unrecoverable` 位于 conflict 判断之前，[script:464](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:464)：`anomaly + 扫描受阻/不可读/归因冲突` 仍被假终态化。另无 token 时未扫描即返回，truncated 记录随后被称为“无在盘源”，也应是 `unverifiable`。 |
3342:| 4. FIFO/设备门 | **NOT-CLOSED / PARTIAL · MEDIUM** | DLQ、compare、`--out` 的 `O_NONBLOCK + S_ISREG` 已 CLOSED，[读侧:269](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:269)、[写侧:620](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:620)。但 QA DB 读侧仍直接进入 SQLite，无 regular-file/nonblocking 门，FIFO 仍可能阻塞。 |
3343:| 5. 非法 UTF-8 | **CLOSED（原项）** | 逐 LF frame strict decode，并在调用方归 `unparseable`，[splitter:77](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:77)、[caller:399](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:399)。只读验证坏字节得到 1 frame + decode error。 |
3344:| 6a. 三个指定字段错型 | **CLOSED** | `name`、不可哈希 `request_id`、非字符串 `episode_body` 均不再炸全量，[name:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:143)、[request_id:423](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:423)、[body:111](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:111)。 |
3345:| 6b. 根 `/` containment | **CLOSED** | `root_prefix` 对 `/` 保持 `/`，非根补尾斜杠，[script:203](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:203)。 |
3346:| 6c. 既有输出 `fchmod 0600` | **NOT-CLOSED · HIGH** | `fchmod` 在 protected-inode 拒绝之前，[script:630](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:630)。`--out` 指向已保护的 `0644` transcript 时，会先把源权限改成 `0600`，再发现碰撞并 exit 2。字节虽未截断，但只读输入已被修改。 |
3347:| 7. provenance receipt | **CLOSED（仓库内）** | 报告头已指向 receipt，[report:5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:5)；receipt 链与 Git ancestry 一致，[receipt:4](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt:4)。LOW 限制：记录的是当前仓库内唯一可解析的 8-hex 缩写，不是独立于仓库的完整 40-hex OID。 |
3349:### 独立复算
3362:### 新发现/残留边界
3364:- **BLOCKER**：token-conflict 扫描前早退，仍可无竞态截断 transcript。
3365:- **BLOCKER**：QA DB 实际读取身份未绑定。
3366:- **HIGH**：`fchmod` 先于 protected-id 检查；`anomaly` 吞掉不可见性。
3367:- **MEDIUM**：QA DB 特殊文件门缺失；无 token 未扫描即判不可恢复。
3368:- **LOW**：单独 `b"\n"` 仍被算作 0 行；escaped lone surrogate 可借 `errors="replace"` 构造 `full_verified`；`episode_body_length=True/1.0` 也可通过长度门。
3377:总裁定：**仍阻断 / CARD-G4-9 不可验收**。  
3380:### 逐项终裁
3384:| 1. transcript 全候选保护 | **NOT-CLOSED · BLOCKER** | 多 token 非前缀一致时在扫描前直接返回，[script:168](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:168)，此时 `all_candidate_paths=[]`。同一 `request_id` 含 `session:aaaaa`、`session:bbbbb`，`--out` 指向 `aaaaa….jsonl`，不会进入 [保护循环:599](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:599)，最终仍可在 [ftruncate:639](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:639)截断。无需竞态。不可列举但可穿越的子目录也有同类绕过；后置 transcript `stat` 失败仍被 `continue` 吞掉。 |
3385:| 2. 源侧 fd 身份绑定 | **NOT-CLOSED / PARTIAL · BLOCKER** | DLQ/compare 的狭义修复已 CLOSED：同一 fd `open→fstat→read→identity`，[snapshot:262](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:262)、[DLQ:389](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:389)、[compare:542](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:542)。但 `qa_metrics_db` 仍是早期 path-stat、稍后 SQLite 按路径重新打开，[probe:233](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:233)。可令 stat 看到 inode A、SQLite 实际读取换入的 B、`--out` 为 B 的 hardlink，最终 B 不在保护集并被截断。 |
3386:| 3. `unverifiable` 四态 | **NOT-CLOSED · HIGH** | distribution/list 同步已实现。但 `anomaly→unrecoverable` 位于 conflict 判断之前，[script:464](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:464)：`anomaly + 扫描受阻/不可读/归因冲突` 仍被假终态化。另无 token 时未扫描即返回，truncated 记录随后被称为“无在盘源”，也应是 `unverifiable`。 |
3387:| 4. FIFO/设备门 | **NOT-CLOSED / PARTIAL · MEDIUM** | DLQ、compare、`--out` 的 `O_NONBLOCK + S_ISREG` 已 CLOSED，[读侧:269](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:269)、[写侧:620](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:620)。但 QA DB 读侧仍直接进入 SQLite，无 regular-file/nonblocking 门，FIFO 仍可能阻塞。 |
3388:| 5. 非法 UTF-8 | **CLOSED（原项）** | 逐 LF frame strict decode，并在调用方归 `unparseable`，[splitter:77](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:77)、[caller:399](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:399)。只读验证坏字节得到 1 frame + decode error。 |
3389:| 6a. 三个指定字段错型 | **CLOSED** | `name`、不可哈希 `request_id`、非字符串 `episode_body` 均不再炸全量，[name:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:143)、[request_id:423](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:423)、[body:111](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:111)。 |
3390:| 6b. 根 `/` containment | **CLOSED** | `root_prefix` 对 `/` 保持 `/`，非根补尾斜杠，[script:203](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:203)。 |
3391:| 6c. 既有输出 `fchmod 0600` | **NOT-CLOSED · HIGH** | `fchmod` 在 protected-inode 拒绝之前，[script:630](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:630)。`--out` 指向已保护的 `0644` transcript 时，会先把源权限改成 `0600`，再发现碰撞并 exit 2。字节虽未截断，但只读输入已被修改。 |
3392:| 7. provenance receipt | **CLOSED（仓库内）** | 报告头已指向 receipt，[report:5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:5)；receipt 链与 Git ancestry 一致，[receipt:4](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt:4)。LOW 限制：记录的是当前仓库内唯一可解析的 8-hex 缩写，不是独立于仓库的完整 40-hex OID。 |
3394:### 独立复算
3407:### 新发现/残留边界
3409:- **BLOCKER**：token-conflict 扫描前早退，仍可无竞态截断 transcript。
3410:- **BLOCKER**：QA DB 实际读取身份未绑定。
3411:- **HIGH**：`fchmod` 先于 protected-id 检查；`anomaly` 吞掉不可见性。
3412:- **MEDIUM**：QA DB 特殊文件门缺失；无 token 未扫描即判不可恢复。
3413:- **LOW**：单独 `b"\n"` 仍被算作 0 行；escaped lone surrogate 可借 `errors="replace"` 构造 `full_verified`；`episode_body_length=True/1.0` 也可通过长度门。

exec
/bin/zsh -lc 'git diff --no-ext-diff --unified=80 4c125f19''^ 4c125f19 -- backend/scripts/census_dead_letter_episodes.py' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
diff --git a/backend/scripts/census_dead_letter_episodes.py b/backend/scripts/census_dead_letter_episodes.py
index e493c12a..c1c1346b 100644
--- a/backend/scripts/census_dead_letter_episodes.py
+++ b/backend/scripts/census_dead_letter_episodes.py
@@ -5,335 +5,396 @@ BATCH-2026-08-28-第五批 / CARD-G4-9（G4-10 replay 的交接台账生成器
 
 只读契约（grep 可自证 + 运行时守卫）:
   - 无 --apply / 无任何写回、重放、删除路径；
   - 不 import neo4j / graphiti / app.*（纯 stdlib），不建立任何数据库/网络连接，
     唯一的 sqlite 访问经 URI ``mode=ro`` 只读打开 qa_metrics.db；
   - 唯一写出口是 --out 台账 JSON，写前双重碰撞守卫：resolve() 路径比较 +
     **文件身份 (st_dev, st_ino) 比较**，与 --dlq/--compare/--qa-metrics-db
     任一输入重合即 exit 2，防 "w" 截断输入（round-1 BLOCKER-1 + round-2
     hardlink / 大小写别名绕过整改）。
 
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
     ambiguous 同样拒绝采信；transcripts 根**不存在或不可读/不可遍历**
     （chmod 000）时整体 exit 2（拒绝在源不可见时产出 unrecoverable 假象）；
     glob 结果拒绝 symlink 条目与逃逸到根外的目标（round-2 HIGH-3 整改）。
   - DLQ 坏 JSON 行不再炸掉全量: 逐行捕获，class=unparseable 保留 line_no
     进台账（分诊工具不能被单行毒药拒诊）。
   - episode_body_full 若在盘（DEAD_LETTER_STORE_FULL_BODY 开启时生产可写):
     重算 sha **且长度**双门对账通过才按 byte_exact 采信，且 anomaly 记录
     不得经此分支翻案（round-1 MEDIUM-1 + round-2 HIGH-1 整改）。
 
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
 import hashlib
 import json
 import os
 import re
 import sqlite3
 import stat
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
 
 
 def _split_jsonl_lines(raw: bytes) -> list[tuple[str, str | None]]:
     """按 JSONL 规范只以 LF 分帧，返回 [(line_text, decode_error_or_None)]。
 
     - 不用 splitlines(): U+2028/U+2029/裸 CR 会误分行（round-3）。
     - 逐行 **strict** decode（round-4 MEDIUM 整改）: errors="replace" 会把非法
       UTF-8 静默改写成合法对象，让坏字节冒充有效记录。解码失败的行带错误信息
       返回，由调用方归入 unparseable。
     """
-    if raw.endswith(b"\n"):
+    had_trailing_lf = raw.endswith(b"\n")
+    if had_trailing_lf:
         raw = raw[:-1]
     if not raw:
-        return []
+        # round-5 LOW 整改: 单独 b"\n" 是一个空行，不是 0 行
+        return [("", None)] if had_trailing_lf else []
     out: list[tuple[str, str | None]] = []
     for chunk in raw.split(b"\n"):
         try:
             out.append((chunk.decode("utf-8"), None))
         except UnicodeDecodeError as e:
             out.append(("", f"utf8_decode_error: {e}"))
     return out
 
 
 def classify(rec: dict) -> str:
     et = rec.get("error_type", "")
     if not isinstance(et, str):
         return "unexpected"
     if et == "EntityTypeValidationError":
         return "schema_entity_type"
     if et == "GroupIdValidationError":
         return "group_id_format"
     if et == "BadRequestError" and _BUDGET_PAT.search(str(rec.get("error", ""))):
         return "budget_400"
     return "unexpected"
 
 
 def inline_state(rec: dict) -> tuple[str, str]:
     """返回 (inline_state, sha_check)，fail-closed（见模块 docstring）。"""
     body = rec.get("episode_body", "")
     if not isinstance(body, str):  # round-4 LOW: episode_body 错型
         return "anomaly", "FAIL"
     declared_len = rec.get("episode_body_length")
     declared_sha = rec.get("episode_body_sha256", "")
     sha_wellformed = isinstance(declared_sha, str) and bool(_SHA256_HEX_PAT.match(declared_sha))
-    recomputed = hashlib.sha256(body.encode("utf-8", errors="replace")).hexdigest()
-    if sha_wellformed and recomputed == declared_sha and len(body) == declared_len:
+    # round-5 LOW 整改: errors="replace" 会把 JSON escaped lone surrogate
+    # (\udXXX) 改写成 replacement char，可被构造出"对得上账"的假 full_verified。
+    # 改 strict：无法编码即判 anomaly。
+    try:
+        body_bytes = body.encode("utf-8")
+    except UnicodeEncodeError:
+        return "anomaly", "FAIL"
+    recomputed = hashlib.sha256(body_bytes).hexdigest()
+    len_ok = isinstance(declared_len, int) and not isinstance(declared_len, bool)
+    if sha_wellformed and recomputed == declared_sha and len_ok and len(body) == declared_len:
         return "full_verified", "pass"
-    if sha_wellformed and len(body) == 200 and isinstance(declared_len, int) and declared_len > 200:
+    if sha_wellformed and len(body) == 200 and len_ok and declared_len > 200:
         return "truncated_prefix", "prefix_only"
     return "anomaly", "FAIL"
 
 
 def full_body_verified(rec: dict) -> bool:
     """episode_body_full 在盘且 sha **与长度**双门对账通过（生产 opt-in 字段，当前 live 0 条）。
 
     round-2 HIGH-1 整改: 原实现只核 sha，声明长度矛盾的记录（如 body="abc"
     但 episode_body_length=999）仍被判 byte_exact —— 与 inline 侧同门收紧。
     """
     full = rec.get("episode_body_full")
     declared_sha = rec.get("episode_body_sha256", "")
     declared_len = rec.get("episode_body_length")
     if not isinstance(full, str) or not _SHA256_HEX_PAT.match(str(declared_sha)):
         return False
-    if not isinstance(declared_len, int) or len(full) != declared_len:
+    # round-5 LOW 整改: bool 是 int 子类 —— episode_body_length=True 会通过长度门
+    if not isinstance(declared_len, int) or isinstance(declared_len, bool) or len(full) != declared_len:
+        return False
+    try:
+        full_bytes = full.encode("utf-8")
+    except UnicodeEncodeError:
         return False
-    return hashlib.sha256(full.encode("utf-8", errors="replace")).hexdigest() == declared_sha
+    return hashlib.sha256(full_bytes).hexdigest() == declared_sha
 
 
 def session_tokens(name: object) -> list[str]:
     """round-4 LOW 整改: name 非 str（None/数字/列表）不再抛异常。"""
     if not isinstance(name, str):
         return []
     tokens = []
     m = _SESSION_ARCHIVE_PAT.match(name)
     if m:
         tokens.append(m.group(1).lower())
     tokens.extend(t.lower() for t in _SESSION_INLINE_PAT.findall(name))
     return tokens
 
 
 def resolve_group_attribution(tokens: list[str], transcripts_dir: Path) -> dict:
-    """组级归因，fail-closed: 前缀一致门 + 恰 1 个常规文件命中门。"""
+    """组级归因，fail-closed。
+
+    round-5 BLOCKER① 整改: **先扫描后判定**。原实现在 token 冲突/无 token 时
+    扫描前早退，导致这些候选从未进入 all_candidate_paths → 不进 --out 保护集
+    → 可被无竞态截断。现无条件对每个 token 扫描收集候选（保护集所需），
+    再做冲突/唯一性判定。
+    """
     result = {
         "session_token": None,
         "transcript_paths": [],
         "transcript_exists": False,
         "transcript_match_count": 0,
         "attribution_conflict": False,
-        # round-4 BLOCKER① 整改: 保护集必须覆盖**所有见到的候选**（含不可读、
-        # 含被冲突分支清空的）—— 否则 mode 0200（不可读但可写）的 transcript
-        # 不进保护集，--out 指向它仍会被截断。
+        # 保护集必须覆盖**所有见到的候选**（含不可读、含被冲突分支排除的）
         "all_candidate_paths": [],
     }
     uniq = sorted(set(tokens), key=len)
-    if not uniq:
-        return result
-    longest = uniq[-1]
-    if any(not longest.startswith(t) for t in uniq[:-1]):
-        result["attribution_conflict"] = True
-        return result
-    result["session_token"] = longest
-    # round-2 HIGH-3: 拒绝 symlink 条目与逃逸到根外的目标（glob 会跟随 symlink，
-    # 根内 .jsonl→根外 .txt 曾被当唯一来源采信）。
-    # round-3 整改: 改 os.walk(onerror=) —— glob 对不可读的中间目录**静默跳过**，
-    # 会把"没搜到"与"搜不了"混为一谈，产出假 unrecoverable。遍历出错即 fail-closed。
+
     root_real = os.path.realpath(transcripts_dir)
+    root_prefix = root_real if root_real.endswith(os.sep) else root_real + os.sep
     walk_errors: list[str] = []
 
     def _on_walk_error(err: OSError) -> None:
         walk_errors.append(f"{getattr(err, 'filename', '?')}: {err}")
 
-    matches = []
-    unreadable: list[str] = []
+    # 单次遍历收集**每个 token** 的候选（无条件，供保护集与判定共用）
+    per_token: dict[str, list[str]] = {t: [] for t in uniq}
     all_candidates: list[str] = []
-    for dirpath, dirnames, filenames in os.walk(transcripts_dir, onerror=_on_walk_error, followlinks=False):
-        for fname in filenames:
-            if not (fname.startswith(longest) and fname.endswith(".jsonl")):
-                continue
-            candidate = os.path.join(dirpath, fname)
-            if os.path.islink(candidate) or not os.path.isfile(candidate):
-                continue
-            # round-3 整改: isfile() 对 mode 000 仍为 True —— 不可读的文件
-            # 不是可用恢复源，计入 unreadable 而非命中（fail-closed）。
-            all_candidates.append(candidate)
-            if not os.access(candidate, os.R_OK):
-                unreadable.append(candidate)
-                continue
-            real = os.path.realpath(candidate)
-            # round-4 LOW 整改: root="/" 时 root_real+sep=="//" 会让合法子项全假
-            root_prefix = root_real if root_real.endswith(os.sep) else root_real + os.sep
-            if not real.startswith(root_prefix):
-                continue  # 目录 symlink 逃逸
-            matches.append(candidate)
-    matches = sorted(matches)
-    result["all_candidate_paths"] = sorted(all_candidates)
-    if unreadable:
-        # 存在同名但不可读的候选 —— 源不完全可见，拒绝据此裁定
-        result["unreadable_candidates"] = unreadable[:5]
+    unreadable: list[str] = []
+    stat_failures: list[str] = []
+    if uniq:
+        for dirpath, _dirnames, filenames in os.walk(transcripts_dir, onerror=_on_walk_error, followlinks=False):
+            for fname in filenames:
+                if not fname.endswith(".jsonl"):
+                    continue
+                matched = [t for t in uniq if fname.startswith(t)]
+                if not matched:
+                    continue
+                candidate = os.path.join(dirpath, fname)
+                # 候选一律入 all_candidate_paths（保护集口径），再谈可用性
+                all_candidates.append(candidate)
+                try:
+                    if os.path.islink(candidate) or not os.path.isfile(candidate):
+                        continue
+                except OSError as e:
+                    stat_failures.append(f"{candidate}: {e}")
+                    continue
+                if not os.access(candidate, os.R_OK):
+                    unreadable.append(candidate)
+                    continue
+                real = os.path.realpath(candidate)
+                if not real.startswith(root_prefix):
+                    continue  # 目录 symlink 逃逸
+                for t in matched:
+                    per_token[t].append(candidate)
+    result["all_candidate_paths"] = sorted(set(all_candidates))
+
+    if not uniq:
+        # 无 token: 未做任何归因扫描 —— 不是"确认无源"（round-5 MEDIUM 整改）
         result["attribution_conflict"] = True
-        result["transcript_paths"] = []
-        result["transcript_match_count"] = 0
+        result["no_token"] = True
         return result
+
+    longest = uniq[-1]
+    if any(not longest.startswith(t) for t in uniq[:-1]):
+        result["attribution_conflict"] = True
+        result["token_conflict"] = True
+        return result
+    result["session_token"] = longest
+
     if walk_errors:
-        # 源不完全可见 —— 拒绝据此裁定（既不宣称找到，也不宣称不可恢复）
         result["scan_errors"] = walk_errors[:5]
         result["attribution_conflict"] = True
-        result["transcript_paths"] = []
-        result["transcript_match_count"] = 0
         return result
+    if stat_failures:
+        result["stat_failures"] = stat_failures[:5]
+        result["attribution_conflict"] = True
+        return result
+    if unreadable:
+        result["unreadable_candidates"] = unreadable[:5]
+        result["attribution_conflict"] = True
+        return result
+
+    matches = sorted(set(per_token[longest]))
     result["transcript_paths"] = matches
     result["transcript_match_count"] = len(matches)
     if len(matches) == 1:
         result["transcript_exists"] = True
     elif len(matches) > 1:
         result["attribution_conflict"] = True  # ambiguous 多命中，拒绝采信
     return result
 
 
-def probe_qa_metrics(db_path: Path, error_types: list[str]) -> dict:
-    """只读核销 qa_metrics.db 能否作为源指针（URI mode=ro，无写路径）。"""
+def probe_qa_metrics(db_path: Path, error_types: list[str]) -> tuple[dict, tuple[int, int] | None]:
+    """只读核销 qa_metrics.db（URI mode=ro，无写路径）。返回 (结果, 实际身份)。
+
+    round-5 BLOCKER②/MEDIUM 整改: 原实现按路径 stat 取身份、SQLite 稍后按路径
+    重新打开 —— 两者可能不是同一对象，且无 regular-file/nonblocking 门（FIFO
+    会阻塞）。现: fd 打开取 fstat 身份 + S_ISREG 门 → SQLite 打开 → 复核路径
+    身份仍等于该身份，不等即拒绝（不采信被换入的对象）。
+    """
     result: dict = {"db_path": str(db_path), "opened_readonly": False}
     if not db_path.exists():
         result["verdict"] = "db_missing"
-        return result
+        return result, None
+    try:
+        fd = os.open(db_path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
+    except OSError as e:
+        result["verdict"] = f"open_refused: {e}"
+        return result, None
+    try:
+        st = os.fstat(fd)
+        if not stat.S_ISREG(st.st_mode):
+            result["verdict"] = "not_regular_file_refused"
+            return result, None
+        identity = (st.st_dev, st.st_ino)
+    finally:
+        os.close(fd)
+
     uri = f"file:{db_path}?mode=ro"
     conn = sqlite3.connect(uri, uri=True)
     try:
+        # 复核 SQLite 实际打开的路径身份仍是我们验证过的对象
+        try:
+            recheck = os.stat(db_path)
+        except OSError as e:
+            result["verdict"] = f"recheck_stat_failed: {e}"
+            return result, identity
+        if (recheck.st_dev, recheck.st_ino) != identity:
+            result["verdict"] = "identity_changed_between_verify_and_open_refused"
+            return result, identity
         result["opened_readonly"] = True
+        result["file_identity_verified"] = True
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
-    return result
+    return result, identity
 
 
 def snapshot_file(path: Path) -> tuple[bytes, dict, tuple[int, int]]:
     """一次性读全量 bytes；sha/行数/身份全部派生自**同一个 fd**。
 
     round-4 BLOCKER② 整改: 原实现按路径 stat 采集保护身份、稍后才按路径读取，
     两步之间对象可被换掉（源侧 TOCTOU）。现改为打开一次 fd → fstat 取身份 →
     从该 fd 读全量，返回的 (st_dev, st_ino) 即**实际被读取对象**的身份。
     """
     fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
     try:
         st = os.fstat(fd)
         if not stat.S_ISREG(st.st_mode):
             raise OSError(f"不是常规文件（拒绝 FIFO/设备/目录）: {path}")
         identity = (st.st_dev, st.st_ino)
         chunks = []
         while True:
             block = os.read(fd, 1 << 20)
             if not block:
                 break
             chunks.append(block)
         raw = b"".join(chunks)
     finally:
         os.close(fd)
     info = {
         "path": str(path),
         "exists": True,
         # round-3 整改: JSONL 的行分隔符**只有** \n —— splitlines() 会把
         # U+2028/U+2029/裸 CR 也当分隔符，可能把一条 JSON 记录劈成两半。
         # 与 records 同口径按 \n 切分（末尾换行不算空行）。
         "line_count": len(_split_jsonl_lines(raw)),
         "sha256": hashlib.sha256(raw).hexdigest(),
         "mtime_utc": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
         "mtime_note": "mtime 取自读取用 fd 的 fstat；绑定 exact bytes 的是 sha256",
     }
     return raw, info, identity
 
 
 def describe_copy(path: Path) -> tuple[dict, tuple[int, int] | None]:
     """返回 (描述, 实际读取对象身份)；身份用于并入 --out 保护集。"""
     if not path.exists():
         return {"path": str(path), "exists": False}, None
     _, info, identity = snapshot_file(path)
     return info, identity
 
 
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
@@ -381,281 +442,288 @@ def main(argv: list[str] | None = None) -> int:
             if (out_st.st_dev, out_st.st_ino) in protected_ids:
                 print(
                     f"--out 与输入文件为同一 inode（hardlink/大小写别名），拒绝写出（防截断）: {out_path}",
                     file=sys.stderr,
                 )
                 return 2
 
     # BLOCKER-2 整改: 单次读取，records 与头部描述共享同一份 exact bytes
     try:
         raw_bytes, dlq_info, dlq_identity = snapshot_file(dlq_path)
     except OSError as e:
         print(f"DLQ 无法安全读取: {dlq_path} ({e})", file=sys.stderr)
         return 2
     protected_ids.add(dlq_identity)  # 保护的是**实际读取对象**，非路径快照
     raw_lines = _split_jsonl_lines(raw_bytes)
 
     records: list[tuple[int, dict]] = []
     unparseable: list[dict] = []
     for line_no, (line, decode_err) in enumerate(raw_lines, start=1):
         if decode_err is not None:
             unparseable.append({"line_no": line_no, "reason": decode_err})
             continue
         if not line.strip():
             unparseable.append({"line_no": line_no, "reason": "blank_line"})
             continue
         try:
             rec = json.loads(line)
         except json.JSONDecodeError as e:
             unparseable.append({"line_no": line_no, "reason": f"json_error: {e}", "excerpt": line[:80]})
             continue
         # round-3 LOW 整改: 合法 JSON 但非对象（null / 数组 / 标量）此前解析成功
         # 却在 rec.get() 处抛 AttributeError 炸掉全量 —— 归入 unparseable。
         if not isinstance(rec, dict):
             unparseable.append(
                 {"line_no": line_no, "reason": f"not_a_json_object: {type(rec).__name__}", "excerpt": line[:80]}
             )
             continue
         records.append((line_no, rec))
 
     # request_id 分组: (类型名, 值) 复合键；缺失/None → 按 line_no 单条成组
     groups: dict[tuple, list[tuple[int, dict]]] = defaultdict(list)
     for line_no, rec in records:
         rid = rec.get("request_id")
         # round-4 LOW 整改: 不可哈希的 request_id（list/dict）按 line_no 单条成组
         try:
             hash(rid)
             hashable = True
         except TypeError:
             hashable = False
         key = ("__missing__", line_no) if (rid is None or not hashable) else (type(rid).__name__, rid)
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
     inline_dist: Counter = Counter()
     unrecoverable_keys = []
     unverifiable_keys = []
     attribution_conflicts = []
     for line_no, rec in records:
         cls = classify(rec)
         state, sha_check = inline_state(rec)
         rid = rec.get("request_id")
         try:
             hash(rid)
             hashable = True
         except TypeError:
             hashable = False
         key = ("__missing__", line_no) if (rid is None or not hashable) else (type(rid).__name__, rid)
         sess = group_attribution[key]
         if state == "full_verified":
             recover = "byte_exact"
             basis = "inline 正文全量：sha256 重算与声明一致且长度精确匹配"
         elif state != "anomaly" and full_body_verified(rec):
-            # round-2 HIGH-1 整改: anomaly 记录不得经 full_body 分支翻案
             recover = "byte_exact"
             basis = "episode_body_full 在盘且 sha256+长度双门对账通过（DEAD_LETTER_STORE_FULL_BODY 生产 opt-in 字段）"
-        elif state == "anomaly":
-            recover = "unrecoverable"
-            basis = "inline 对不上账（anomaly：sha/长度与声明不符），fail-closed 不采信截断前缀假设，也不采信 transcript 归因"
         elif sess["attribution_conflict"]:
-            # round-4 HIGH 整改: 归因冲突/多命中/扫描受阻 ≠ "源不存在"。
-            # 终态化为 unrecoverable 是不诚实的断言 —— 单列 unverifiable。
+            # round-5 HIGH 整改: 可见性判定**优先于** anomaly —— 源看不见时
+            # 无论 inline 是什么状态，都不能断言"不可恢复"。
             recover = "unverifiable"
-            basis = (
-                "源可见性不足，拒绝裁定："
-                + (
-                    "扫描遍历受阻（不可读子树）"
-                    if sess.get("scan_errors")
-                    else "存在不可读候选"
-                    if sess.get("unreadable_candidates")
-                    else "多 token 前缀冲突或 transcript 多命中 ambiguous"
-                )
-                + "。既不宣称可恢复，也不宣称不可恢复（fail-closed）"
-            )
+            if sess.get("no_token"):
+                why = "记录名未携带 session token，未做任何归因扫描"
+            elif sess.get("token_conflict"):
+                why = "同组多 token 前缀冲突"
+            elif sess.get("scan_errors"):
+                why = "扫描遍历受阻（不可读子树）"
+            elif sess.get("stat_failures"):
+                why = "候选 stat 失败"
+            elif sess.get("unreadable_candidates"):
+                why = "存在不可读候选"
+            else:
+                why = "transcript 多命中 ambiguous"
+            extra = "；inline 亦对不上账（anomaly）" if state == "anomaly" else ""
+            basis = f"源可见性不足，拒绝裁定：{why}{extra}。既不宣称可恢复，也不宣称不可恢复（fail-closed）"
+        elif state == "anomaly":
+            recover = "unrecoverable"
+            basis = "inline 对不上账（anomaly：sha/长度与声明不符），且归因扫描完整可见但无可用源"
         elif sess["transcript_exists"]:
             recover = "approximate"
             basis = (
                 f"inline 为 200 字符前缀（前缀性质依赖 to_dict()[:200] 生产不变量，sha 无法直接证明）；"
                 f"经 request_id 组归因到唯一在盘 transcript {sess['session_token']}"
                 f"（归因 ≠ 内容已验证——本工具未读 transcript 内容；G4-10 可重蒸馏/重格式化近似重建，非逐字节保证）"
             )
         else:
             recover = "unrecoverable"
-            basis = "inline 截断且无在盘上游源"
+            basis = "inline 截断；归因扫描完整可见（无遍历错误/无不可读候选）但未找到任何在盘上游源"
         class_dist[cls] += 1
         recover_dist[recover] += 1
         inline_dist[state] += 1
         stable_key = {
             "line_no": line_no,
             "sha256_prefix": str(rec.get("episode_body_sha256", ""))[:16],
             "request_id": rid,
         }
         if recover == "unrecoverable":
             unrecoverable_keys.append(stable_key)
         elif recover == "unverifiable":
             unverifiable_keys.append(stable_key)
         if sess["attribution_conflict"]:
             attribution_conflicts.append(stable_key)
         ledger_records.append(
             {
                 "stable_key": stable_key,
                 "name": str(rec.get("name", ""))[:80],
                 "group_id": rec.get("group_id"),
                 "source_description": rec.get("source_description"),
                 "error_type": rec.get("error_type"),
                 "error_excerpt": str(rec.get("error", ""))[:120],
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
         cluster_map[
             (str(rec.get("name", "")), str(rec.get("episode_body_sha256", "")), str(rec.get("group_id")))
         ].append(line_no)
     duplicate_clusters = [
         {"name": k[0][:80], "episode_body_sha256": k[1], "group_id": k[2], "line_nos": v, "occurrences": len(v)}
         for k, v in sorted(cluster_map.items(), key=lambda kv: -len(kv[1]))
         if len(v) > 1
     ]
 
     compare_infos = []
     for cp in args.compare:
         cinfo, cid = describe_copy(Path(cp))
         compare_infos.append(cinfo)
         if cid is not None:
             protected_ids.add(cid)
 
-    qa_probe = (
-        probe_qa_metrics(
+    if args.qa_metrics_db:
+        qa_probe, qa_identity = probe_qa_metrics(
             Path(args.qa_metrics_db),
-            [r.get("error_type", "") for _, r in records],
+            [str(r.get("error_type", "")) for _, r in records],
         )
-        if args.qa_metrics_db
-        else {"verdict": "skipped_no_db_arg"}
-    )
+        if qa_identity is not None:
+            protected_ids.add(qa_identity)  # 保护实际验证过的对象身份
+    else:
+        qa_probe = {"verdict": "skipped_no_db_arg"}
 
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
         "compare_copies": compare_infos,
         "total_lines": len(raw_lines),
         "total_records": len(records),
         "unparseable_lines": unparseable,
         # round-2 LOW 整改: 固定 schema 补零，消费者无需自行补齐缺席键
         "class_distribution": {
             k: class_dist.get(k, 0) for k in ["budget_400", "schema_entity_type", "group_id_format", "unexpected"]
         },
         "expected_class_distribution": EXPECTED_CLASS_DIST,
         "class_deviation": deviation,
         "recoverability_distribution": {
             k: recover_dist.get(k, 0) for k in ["byte_exact", "approximate", "unverifiable", "unrecoverable"]
         },
         "inline_state_distribution": {
             k: inline_dist.get(k, 0) for k in ["full_verified", "truncated_prefix", "anomaly"]
         },
         "unrecoverable_list": unrecoverable_keys,
         "unverifiable_list": unverifiable_keys,
         "attribution_conflicts": attribution_conflicts,
         "duplicate_clusters": duplicate_clusters,
         "qa_metrics_probe": qa_probe,
         "records": ledger_records,
     }
 
     # round-3 BLOCKER-1 绕过① 整改: 归因到的 transcript 是恢复源，
     # --out 指向它同样会截断。写出前并入保护集（此时归因已完成）。
     for sess_info in group_attribution.values():
         for tpath in sess_info.get("all_candidate_paths", []):
             try:
                 tst = os.stat(tpath)
                 protected_ids.add((tst.st_dev, tst.st_ino))
-            except OSError:
-                continue
+            except OSError as e:
+                # round-5 整改: 候选 stat 失败不再静默吞 —— 保护集不完整即拒绝写出
+                print(f"候选源无法 stat，保护集不完整，拒绝写出: {tpath} ({e})", file=sys.stderr)
+                return 2
     for rec_out in ledger_records:
         for tpath in rec_out.get("transcript_paths", []):
             try:
                 tst = os.stat(tpath)
                 protected_ids.add((tst.st_dev, tst.st_ino))
             except OSError:
                 continue
 
     out_json = json.dumps(ledger, ensure_ascii=False, indent=1)
     if args.out:
         # round-3 整改: 消除 check-then-open TOCTOU。先以 O_NOFOLLOW 打开且
         # **不带 O_TRUNC**，对**实际 fd** fstat 校验 inode；只有校验通过才
         # ftruncate。检查与写入作用于同一 fd，检查后被换 symlink/hardlink 无效。
         try:
             fd = os.open(args.out, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
         except OSError as e:
             print(f"--out 无法安全打开（symlink 或权限）: {args.out} ({e})", file=sys.stderr)
             return 2
         try:
             st = os.fstat(fd)
             # round-4 MEDIUM 整改: 非常规文件（FIFO/设备/socket）拒绝
             if not stat.S_ISREG(st.st_mode):
                 print(f"--out 不是常规文件（FIFO/设备/socket），拒绝写出: {args.out}", file=sys.stderr)
                 return 2
-            # round-4 LOW 整改: 0o600 只作用于新建 —— 既有文件显式收紧
-            if st.st_mode & 0o077:
-                os.fchmod(fd, 0o600)
+            # round-5 HIGH 整改: 碰撞检查必须**先于** fchmod —— 否则 --out 指向
+            # 受保护的 0644 输入时，会先把只读输入的权限改成 0600 再拒绝。
             if (st.st_dev, st.st_ino) in protected_ids:
                 print(
                     f"--out 打开后经 fstat 判定与输入文件同一 inode，拒绝写出（防截断）: {args.out}",
                     file=sys.stderr,
                 )
                 return 2
+            # 碰撞检查通过后才收紧权限（round-4 LOW: 0o600 只作用于新建）
+            if st.st_mode & 0o077:
+                os.fchmod(fd, 0o600)
             os.ftruncate(fd, 0)
             with os.fdopen(fd, "w", encoding="utf-8", closefd=True) as f:
                 fd = -1  # 所有权移交 fdopen
                 f.write(out_json + "\n")
         finally:
             if fd >= 0:
                 os.close(fd)
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
/bin/zsh -lc "stat -f '%N size=%z mtime=%Sm' -t '%Y-%m-%dT%H:%M:%S%z' _bmad-output/审查/codex-review-CARD-G4-9-round6.md" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
_bmad-output/审查/codex-review-CARD-G4-9-round6.md size=24600 mtime=2026-08-28T20:27:15+0800

**Planning detailed code inspection**
exec
/bin/zsh -lc "nl -ba backend/scripts/census_dead_letter_episodes.py | sed -n '330,729p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
   330	    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
   331	    try:
   332	        st = os.fstat(fd)
   333	        if not stat.S_ISREG(st.st_mode):
   334	            raise OSError(f"不是常规文件（拒绝 FIFO/设备/目录）: {path}")
   335	        identity = (st.st_dev, st.st_ino)
   336	        chunks = []
   337	        while True:
   338	            block = os.read(fd, 1 << 20)
   339	            if not block:
   340	                break
   341	            chunks.append(block)
   342	        raw = b"".join(chunks)
   343	    finally:
   344	        os.close(fd)
   345	    info = {
   346	        "path": str(path),
   347	        "exists": True,
   348	        # round-3 整改: JSONL 的行分隔符**只有** \n —— splitlines() 会把
   349	        # U+2028/U+2029/裸 CR 也当分隔符，可能把一条 JSON 记录劈成两半。
   350	        # 与 records 同口径按 \n 切分（末尾换行不算空行）。
   351	        "line_count": len(_split_jsonl_lines(raw)),
   352	        "sha256": hashlib.sha256(raw).hexdigest(),
   353	        "mtime_utc": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
   354	        "mtime_note": "mtime 取自读取用 fd 的 fstat；绑定 exact bytes 的是 sha256",
   355	    }
   356	    return raw, info, identity
   357	
   358	
   359	def describe_copy(path: Path) -> tuple[dict, tuple[int, int] | None]:
   360	    """返回 (描述, 实际读取对象身份)；身份用于并入 --out 保护集。"""
   361	    if not path.exists():
   362	        return {"path": str(path), "exists": False}, None
   363	    _, info, identity = snapshot_file(path)
   364	    return info, identity
   365	
   366	
   367	def main(argv: list[str] | None = None) -> int:
   368	    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
   369	    ap.add_argument(
   370	        "--dlq",
   371	        default="data/dead_letter_episodes.jsonl",
   372	        help="DLQ JSONL 路径（census 对 live 挂载运行时传绝对路径）",
   373	    )
   374	    ap.add_argument(
   375	        "--qa-metrics-db",
   376	        default=None,
   377	        help="qa_metrics.db 路径（省略则跳过源指针核销并如实标注 skipped）",
   378	    )
   379	    ap.add_argument(
   380	        "--transcripts-dir",
   381	        default=os.path.expanduser("~/.claude/projects"),
   382	        help="session transcript 根目录（近似恢复源指针核销；不存在则 exit 2 拒诊）",
   383	    )
   384	    ap.add_argument(
   385	        "--compare",
   386	        action="append",
   387	        default=[],
   388	        help="其它 DLQ 副本路径（可重复，产出 sha 对照表）",
   389	    )
   390	    ap.add_argument("--out", default=None, help="台账 JSON 输出路径（省略则打 stdout）")
   391	    args = ap.parse_args(argv)
   392	
   393	    dlq_path = Path(args.dlq)
   394	    if not dlq_path.exists():
   395	        print(f"DLQ 文件不存在: {dlq_path}", file=sys.stderr)
   396	        return 2
   397	
   398	    transcripts_dir = Path(args.transcripts_dir)
   399	    if not transcripts_dir.is_dir():
   400	        print(
   401	            f"transcripts 根目录不存在/不可见: {transcripts_dir} —— 拒绝在源不可见时裁定可恢复性（fail-closed）",
   402	            file=sys.stderr,
   403	        )
   404	        return 2
   405	    # round-2 HIGH-3 整改: 存在但不可读/不可遍历的根（chmod 000）此前 exit 0
   406	    # 并把全部记录假判 unrecoverable —— 同样 fail-closed 拒诊。
   407	    if not os.access(transcripts_dir, os.R_OK | os.X_OK):
   408	        print(
   409	            f"transcripts 根目录不可读/不可遍历: {transcripts_dir} —— 拒绝在源不可见时裁定可恢复性（fail-closed）",
   410	            file=sys.stderr,
   411	        )
   412	        return 2
   413	
   414	    protected_ids: set[tuple[int, int]] = set()
   415	    # --out 碰撞守卫（写前）。round-2 BLOCKER-1 整改: 比较**文件身份**
   416	    # (st_dev, st_ino) 而非 resolve() 字符串 —— 后者对 hardlink 与
   417	    # 大小写不敏感文件系统上的 case-only 别名均失效（Codex 实测截断输入）。
   418	    if args.out:
   419	        out_path = Path(args.out)
   420	        protected_paths = [dlq_path, *(Path(p) for p in args.compare)]
   421	        if args.qa_metrics_db:
   422	            protected_paths.append(Path(args.qa_metrics_db))
   423	        for candidate in protected_paths:
   424	            try:
   425	                cst = candidate.stat()  # 跟随 symlink: 保护的是最终目标身份
   426	                protected_ids.add((cst.st_dev, cst.st_ino))
   427	            except OSError:
   428	                # round-4 整改: stat 失败不再静默吞 —— 无法确认身份即 fail-closed
   429	                print(f"输入文件无法 stat，拒绝继续（无法建立完整保护集）: {candidate}", file=sys.stderr)
   430	                return 2
   431	        # 路径字符串比较作为第二道（输出文件尚不存在时 stat 无身份可比）
   432	        out_resolved = out_path.resolve()
   433	        if out_resolved in {p.resolve() for p in protected_paths}:
   434	            print(f"--out 与输入文件路径重合，拒绝写出（防截断）: {out_resolved}", file=sys.stderr)
   435	            return 2
   436	        if out_path.exists():
   437	            try:
   438	                out_st = out_path.stat()
   439	            except OSError as e:
   440	                print(f"--out 无法 stat，拒绝写出: {out_path} ({e})", file=sys.stderr)
   441	                return 2
   442	            if (out_st.st_dev, out_st.st_ino) in protected_ids:
   443	                print(
   444	                    f"--out 与输入文件为同一 inode（hardlink/大小写别名），拒绝写出（防截断）: {out_path}",
   445	                    file=sys.stderr,
   446	                )
   447	                return 2
   448	
   449	    # BLOCKER-2 整改: 单次读取，records 与头部描述共享同一份 exact bytes
   450	    try:
   451	        raw_bytes, dlq_info, dlq_identity = snapshot_file(dlq_path)
   452	    except OSError as e:
   453	        print(f"DLQ 无法安全读取: {dlq_path} ({e})", file=sys.stderr)
   454	        return 2
   455	    protected_ids.add(dlq_identity)  # 保护的是**实际读取对象**，非路径快照
   456	    raw_lines = _split_jsonl_lines(raw_bytes)
   457	
   458	    records: list[tuple[int, dict]] = []
   459	    unparseable: list[dict] = []
   460	    for line_no, (line, decode_err) in enumerate(raw_lines, start=1):
   461	        if decode_err is not None:
   462	            unparseable.append({"line_no": line_no, "reason": decode_err})
   463	            continue
   464	        if not line.strip():
   465	            unparseable.append({"line_no": line_no, "reason": "blank_line"})
   466	            continue
   467	        try:
   468	            rec = json.loads(line)
   469	        except json.JSONDecodeError as e:
   470	            unparseable.append({"line_no": line_no, "reason": f"json_error: {e}", "excerpt": line[:80]})
   471	            continue
   472	        # round-3 LOW 整改: 合法 JSON 但非对象（null / 数组 / 标量）此前解析成功
   473	        # 却在 rec.get() 处抛 AttributeError 炸掉全量 —— 归入 unparseable。
   474	        if not isinstance(rec, dict):
   475	            unparseable.append(
   476	                {"line_no": line_no, "reason": f"not_a_json_object: {type(rec).__name__}", "excerpt": line[:80]}
   477	            )
   478	            continue
   479	        records.append((line_no, rec))
   480	
   481	    # request_id 分组: (类型名, 值) 复合键；缺失/None → 按 line_no 单条成组
   482	    groups: dict[tuple, list[tuple[int, dict]]] = defaultdict(list)
   483	    for line_no, rec in records:
   484	        rid = rec.get("request_id")
   485	        # round-4 LOW 整改: 不可哈希的 request_id（list/dict）按 line_no 单条成组
   486	        try:
   487	            hash(rid)
   488	            hashable = True
   489	        except TypeError:
   490	            hashable = False
   491	        key = ("__missing__", line_no) if (rid is None or not hashable) else (type(rid).__name__, rid)
   492	        groups[key].append((line_no, rec))
   493	    group_attribution: dict[tuple, dict] = {}
   494	    for key, members in groups.items():
   495	        tokens: list[str] = []
   496	        for _, rec in members:
   497	            tokens.extend(session_tokens(rec.get("name", "")))
   498	        group_attribution[key] = resolve_group_attribution(tokens, transcripts_dir)
   499	
   500	    ledger_records = []
   501	    class_dist: Counter = Counter()
   502	    recover_dist: Counter = Counter()
   503	    inline_dist: Counter = Counter()
   504	    unrecoverable_keys = []
   505	    unverifiable_keys = []
   506	    attribution_conflicts = []
   507	    for line_no, rec in records:
   508	        cls = classify(rec)
   509	        state, sha_check = inline_state(rec)
   510	        rid = rec.get("request_id")
   511	        try:
   512	            hash(rid)
   513	            hashable = True
   514	        except TypeError:
   515	            hashable = False
   516	        key = ("__missing__", line_no) if (rid is None or not hashable) else (type(rid).__name__, rid)
   517	        sess = group_attribution[key]
   518	        if state == "full_verified":
   519	            recover = "byte_exact"
   520	            basis = "inline 正文全量：sha256 重算与声明一致且长度精确匹配"
   521	        elif state != "anomaly" and full_body_verified(rec):
   522	            recover = "byte_exact"
   523	            basis = "episode_body_full 在盘且 sha256+长度双门对账通过（DEAD_LETTER_STORE_FULL_BODY 生产 opt-in 字段）"
   524	        elif sess["attribution_conflict"]:
   525	            # round-5 HIGH 整改: 可见性判定**优先于** anomaly —— 源看不见时
   526	            # 无论 inline 是什么状态，都不能断言"不可恢复"。
   527	            recover = "unverifiable"
   528	            if sess.get("no_token"):
   529	                why = "记录名未携带 session token，未做任何归因扫描"
   530	            elif sess.get("token_conflict"):
   531	                why = "同组多 token 前缀冲突"
   532	            elif sess.get("scan_errors"):
   533	                why = "扫描遍历受阻（不可读子树）"
   534	            elif sess.get("stat_failures"):
   535	                why = "候选 stat 失败"
   536	            elif sess.get("unreadable_candidates"):
   537	                why = "存在不可读候选"
   538	            else:
   539	                why = "transcript 多命中 ambiguous"
   540	            extra = "；inline 亦对不上账（anomaly）" if state == "anomaly" else ""
   541	            basis = f"源可见性不足，拒绝裁定：{why}{extra}。既不宣称可恢复，也不宣称不可恢复（fail-closed）"
   542	        elif state == "anomaly":
   543	            recover = "unrecoverable"
   544	            basis = "inline 对不上账（anomaly：sha/长度与声明不符），且归因扫描完整可见但无可用源"
   545	        elif sess["transcript_exists"]:
   546	            recover = "approximate"
   547	            basis = (
   548	                f"inline 为 200 字符前缀（前缀性质依赖 to_dict()[:200] 生产不变量，sha 无法直接证明）；"
   549	                f"经 request_id 组归因到唯一在盘 transcript {sess['session_token']}"
   550	                f"（归因 ≠ 内容已验证——本工具未读 transcript 内容；G4-10 可重蒸馏/重格式化近似重建，非逐字节保证）"
   551	            )
   552	        else:
   553	            recover = "unrecoverable"
   554	            basis = "inline 截断；归因扫描完整可见（无遍历错误/无不可读候选）但未找到任何在盘上游源"
   555	        class_dist[cls] += 1
   556	        recover_dist[recover] += 1
   557	        inline_dist[state] += 1
   558	        stable_key = {
   559	            "line_no": line_no,
   560	            "sha256_prefix": str(rec.get("episode_body_sha256", ""))[:16],
   561	            "request_id": rid,
   562	        }
   563	        if recover == "unrecoverable":
   564	            unrecoverable_keys.append(stable_key)
   565	        elif recover == "unverifiable":
   566	            unverifiable_keys.append(stable_key)
   567	        if sess["attribution_conflict"]:
   568	            attribution_conflicts.append(stable_key)
   569	        ledger_records.append(
   570	            {
   571	                "stable_key": stable_key,
   572	                "name": str(rec.get("name", ""))[:80],
   573	                "group_id": rec.get("group_id"),
   574	                "source_description": rec.get("source_description"),
   575	                "error_type": rec.get("error_type"),
   576	                "error_excerpt": str(rec.get("error", ""))[:120],
   577	                "failed_at": rec.get("failed_at"),
   578	                "reference_time": rec.get("reference_time"),
   579	                "class": cls,
   580	                "episode_body_length": rec.get("episode_body_length"),
   581	                "episode_body_sha256": rec.get("episode_body_sha256"),
   582	                "inline_state": state,
   583	                "sha_check": sha_check,
   584	                "session_token": sess["session_token"],
   585	                "transcript_paths": sess["transcript_paths"],
   586	                "transcript_match_count": sess["transcript_match_count"],
   587	                "attribution_conflict": sess["attribution_conflict"],
   588	                "recoverability": recover,
   589	                "recoverability_basis": basis,
   590	            }
   591	        )
   592	
   593	    # 语义重复簇（同 name + 全文 sha + group_id）——G4-10 重放去重策略依据
   594	    cluster_map: dict[tuple, list[int]] = defaultdict(list)
   595	    for line_no, rec in records:
   596	        cluster_map[
   597	            (str(rec.get("name", "")), str(rec.get("episode_body_sha256", "")), str(rec.get("group_id")))
   598	        ].append(line_no)
   599	    duplicate_clusters = [
   600	        {"name": k[0][:80], "episode_body_sha256": k[1], "group_id": k[2], "line_nos": v, "occurrences": len(v)}
   601	        for k, v in sorted(cluster_map.items(), key=lambda kv: -len(kv[1]))
   602	        if len(v) > 1
   603	    ]
   604	
   605	    compare_infos = []
   606	    for cp in args.compare:
   607	        cinfo, cid = describe_copy(Path(cp))
   608	        compare_infos.append(cinfo)
   609	        if cid is not None:
   610	            protected_ids.add(cid)
   611	
   612	    if args.qa_metrics_db:
   613	        qa_probe, qa_identity = probe_qa_metrics(
   614	            Path(args.qa_metrics_db),
   615	            [str(r.get("error_type", "")) for _, r in records],
   616	        )
   617	        if qa_identity is not None:
   618	            protected_ids.add(qa_identity)  # 保护实际验证过的对象身份
   619	    else:
   620	        qa_probe = {"verdict": "skipped_no_db_arg"}
   621	
   622	    deviation = {
   623	        k: {"expected": EXPECTED_CLASS_DIST.get(k, 0), "actual": class_dist.get(k, 0)}
   624	        for k in sorted(set(class_dist) | set(EXPECTED_CLASS_DIST))
   625	        if EXPECTED_CLASS_DIST.get(k, 0) != class_dist.get(k, 0)
   626	    }
   627	
   628	    ledger = {
   629	        "card": "CARD-G4-9",
   630	        "generated_at": datetime.now(timezone.utc).isoformat(),
   631	        "privacy": "private-only: transcript_paths 含本机用户名与 session UUID，禁止外发/公网发布",
   632	        "stable_key_semantics": (
   633	            "冻结快照（dlq_file.sha256）内的 occurrence key；line_no 在快照内唯一，"
   634	            "sha256_prefix/request_id 为冗余对账维度——非跨文件重排或语义幂等键"
   635	        ),
   636	        "dlq_file": dlq_info,
   637	        "compare_copies": compare_infos,
   638	        "total_lines": len(raw_lines),
   639	        "total_records": len(records),
   640	        "unparseable_lines": unparseable,
   641	        # round-2 LOW 整改: 固定 schema 补零，消费者无需自行补齐缺席键
   642	        "class_distribution": {
   643	            k: class_dist.get(k, 0) for k in ["budget_400", "schema_entity_type", "group_id_format", "unexpected"]
   644	        },
   645	        "expected_class_distribution": EXPECTED_CLASS_DIST,
   646	        "class_deviation": deviation,
   647	        "recoverability_distribution": {
   648	            k: recover_dist.get(k, 0) for k in ["byte_exact", "approximate", "unverifiable", "unrecoverable"]
   649	        },
   650	        "inline_state_distribution": {
   651	            k: inline_dist.get(k, 0) for k in ["full_verified", "truncated_prefix", "anomaly"]
   652	        },
   653	        "unrecoverable_list": unrecoverable_keys,
   654	        "unverifiable_list": unverifiable_keys,
   655	        "attribution_conflicts": attribution_conflicts,
   656	        "duplicate_clusters": duplicate_clusters,
   657	        "qa_metrics_probe": qa_probe,
   658	        "records": ledger_records,
   659	    }
   660	
   661	    # round-3 BLOCKER-1 绕过① 整改: 归因到的 transcript 是恢复源，
   662	    # --out 指向它同样会截断。写出前并入保护集（此时归因已完成）。
   663	    for sess_info in group_attribution.values():
   664	        for tpath in sess_info.get("all_candidate_paths", []):
   665	            try:
   666	                tst = os.stat(tpath)
   667	                protected_ids.add((tst.st_dev, tst.st_ino))
   668	            except OSError as e:
   669	                # round-5 整改: 候选 stat 失败不再静默吞 —— 保护集不完整即拒绝写出
   670	                print(f"候选源无法 stat，保护集不完整，拒绝写出: {tpath} ({e})", file=sys.stderr)
   671	                return 2
   672	    for rec_out in ledger_records:
   673	        for tpath in rec_out.get("transcript_paths", []):
   674	            try:
   675	                tst = os.stat(tpath)
   676	                protected_ids.add((tst.st_dev, tst.st_ino))
   677	            except OSError:
   678	                continue
   679	
   680	    out_json = json.dumps(ledger, ensure_ascii=False, indent=1)
   681	    if args.out:
   682	        # round-3 整改: 消除 check-then-open TOCTOU。先以 O_NOFOLLOW 打开且
   683	        # **不带 O_TRUNC**，对**实际 fd** fstat 校验 inode；只有校验通过才
   684	        # ftruncate。检查与写入作用于同一 fd，检查后被换 symlink/hardlink 无效。
   685	        try:
   686	            fd = os.open(args.out, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
   687	        except OSError as e:
   688	            print(f"--out 无法安全打开（symlink 或权限）: {args.out} ({e})", file=sys.stderr)
   689	            return 2
   690	        try:
   691	            st = os.fstat(fd)
   692	            # round-4 MEDIUM 整改: 非常规文件（FIFO/设备/socket）拒绝
   693	            if not stat.S_ISREG(st.st_mode):
   694	                print(f"--out 不是常规文件（FIFO/设备/socket），拒绝写出: {args.out}", file=sys.stderr)
   695	                return 2
   696	            # round-5 HIGH 整改: 碰撞检查必须**先于** fchmod —— 否则 --out 指向
   697	            # 受保护的 0644 输入时，会先把只读输入的权限改成 0600 再拒绝。
   698	            if (st.st_dev, st.st_ino) in protected_ids:
   699	                print(
   700	                    f"--out 打开后经 fstat 判定与输入文件同一 inode，拒绝写出（防截断）: {args.out}",
   701	                    file=sys.stderr,
   702	                )
   703	                return 2
   704	            # 碰撞检查通过后才收紧权限（round-4 LOW: 0o600 只作用于新建）
   705	            if st.st_mode & 0o077:
   706	                os.fchmod(fd, 0o600)
   707	            os.ftruncate(fd, 0)
   708	            with os.fdopen(fd, "w", encoding="utf-8", closefd=True) as f:
   709	                fd = -1  # 所有权移交 fdopen
   710	                f.write(out_json + "\n")
   711	        finally:
   712	            if fd >= 0:
   713	                os.close(fd)
   714	        print(f"台账已写入: {args.out}")
   715	    else:
   716	        print(out_json)
   717	
   718	    print(
   719	        f"census: {len(records)} 条 (+{len(unparseable)} unparseable) | class={dict(class_dist)} | "
   720	        f"recoverability={dict(recover_dist)} | 归因冲突={len(attribution_conflicts)} | "
   721	        f"重复簇={len(duplicate_clusters)} | 偏差={deviation or '无'} | "
   722	        f"qa_metrics 核销={qa_probe.get('verdict')}",
   723	        file=sys.stderr,
   724	    )
   725	    return 0
   726	
   727	
   728	if __name__ == "__main__":
   729	    sys.exit(main())

exec
/bin/zsh -lc "nl -ba backend/scripts/census_dead_letter_episodes.py | sed -n '65,330p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
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
    77	def _split_jsonl_lines(raw: bytes) -> list[tuple[str, str | None]]:
    78	    """按 JSONL 规范只以 LF 分帧，返回 [(line_text, decode_error_or_None)]。
    79	
    80	    - 不用 splitlines(): U+2028/U+2029/裸 CR 会误分行（round-3）。
    81	    - 逐行 **strict** decode（round-4 MEDIUM 整改）: errors="replace" 会把非法
    82	      UTF-8 静默改写成合法对象，让坏字节冒充有效记录。解码失败的行带错误信息
    83	      返回，由调用方归入 unparseable。
    84	    """
    85	    had_trailing_lf = raw.endswith(b"\n")
    86	    if had_trailing_lf:
    87	        raw = raw[:-1]
    88	    if not raw:
    89	        # round-5 LOW 整改: 单独 b"\n" 是一个空行，不是 0 行
    90	        return [("", None)] if had_trailing_lf else []
    91	    out: list[tuple[str, str | None]] = []
    92	    for chunk in raw.split(b"\n"):
    93	        try:
    94	            out.append((chunk.decode("utf-8"), None))
    95	        except UnicodeDecodeError as e:
    96	            out.append(("", f"utf8_decode_error: {e}"))
    97	    return out
    98	
    99	
   100	def classify(rec: dict) -> str:
   101	    et = rec.get("error_type", "")
   102	    if not isinstance(et, str):
   103	        return "unexpected"
   104	    if et == "EntityTypeValidationError":
   105	        return "schema_entity_type"
   106	    if et == "GroupIdValidationError":
   107	        return "group_id_format"
   108	    if et == "BadRequestError" and _BUDGET_PAT.search(str(rec.get("error", ""))):
   109	        return "budget_400"
   110	    return "unexpected"
   111	
   112	
   113	def inline_state(rec: dict) -> tuple[str, str]:
   114	    """返回 (inline_state, sha_check)，fail-closed（见模块 docstring）。"""
   115	    body = rec.get("episode_body", "")
   116	    if not isinstance(body, str):  # round-4 LOW: episode_body 错型
   117	        return "anomaly", "FAIL"
   118	    declared_len = rec.get("episode_body_length")
   119	    declared_sha = rec.get("episode_body_sha256", "")
   120	    sha_wellformed = isinstance(declared_sha, str) and bool(_SHA256_HEX_PAT.match(declared_sha))
   121	    # round-5 LOW 整改: errors="replace" 会把 JSON escaped lone surrogate
   122	    # (\udXXX) 改写成 replacement char，可被构造出"对得上账"的假 full_verified。
   123	    # 改 strict：无法编码即判 anomaly。
   124	    try:
   125	        body_bytes = body.encode("utf-8")
   126	    except UnicodeEncodeError:
   127	        return "anomaly", "FAIL"
   128	    recomputed = hashlib.sha256(body_bytes).hexdigest()
   129	    len_ok = isinstance(declared_len, int) and not isinstance(declared_len, bool)
   130	    if sha_wellformed and recomputed == declared_sha and len_ok and len(body) == declared_len:
   131	        return "full_verified", "pass"
   132	    if sha_wellformed and len(body) == 200 and len_ok and declared_len > 200:
   133	        return "truncated_prefix", "prefix_only"
   134	    return "anomaly", "FAIL"
   135	
   136	
   137	def full_body_verified(rec: dict) -> bool:
   138	    """episode_body_full 在盘且 sha **与长度**双门对账通过（生产 opt-in 字段，当前 live 0 条）。
   139	
   140	    round-2 HIGH-1 整改: 原实现只核 sha，声明长度矛盾的记录（如 body="abc"
   141	    但 episode_body_length=999）仍被判 byte_exact —— 与 inline 侧同门收紧。
   142	    """
   143	    full = rec.get("episode_body_full")
   144	    declared_sha = rec.get("episode_body_sha256", "")
   145	    declared_len = rec.get("episode_body_length")
   146	    if not isinstance(full, str) or not _SHA256_HEX_PAT.match(str(declared_sha)):
   147	        return False
   148	    # round-5 LOW 整改: bool 是 int 子类 —— episode_body_length=True 会通过长度门
   149	    if not isinstance(declared_len, int) or isinstance(declared_len, bool) or len(full) != declared_len:
   150	        return False
   151	    try:
   152	        full_bytes = full.encode("utf-8")
   153	    except UnicodeEncodeError:
   154	        return False
   155	    return hashlib.sha256(full_bytes).hexdigest() == declared_sha
   156	
   157	
   158	def session_tokens(name: object) -> list[str]:
   159	    """round-4 LOW 整改: name 非 str（None/数字/列表）不再抛异常。"""
   160	    if not isinstance(name, str):
   161	        return []
   162	    tokens = []
   163	    m = _SESSION_ARCHIVE_PAT.match(name)
   164	    if m:
   165	        tokens.append(m.group(1).lower())
   166	    tokens.extend(t.lower() for t in _SESSION_INLINE_PAT.findall(name))
   167	    return tokens
   168	
   169	
   170	def resolve_group_attribution(tokens: list[str], transcripts_dir: Path) -> dict:
   171	    """组级归因，fail-closed。
   172	
   173	    round-5 BLOCKER① 整改: **先扫描后判定**。原实现在 token 冲突/无 token 时
   174	    扫描前早退，导致这些候选从未进入 all_candidate_paths → 不进 --out 保护集
   175	    → 可被无竞态截断。现无条件对每个 token 扫描收集候选（保护集所需），
   176	    再做冲突/唯一性判定。
   177	    """
   178	    result = {
   179	        "session_token": None,
   180	        "transcript_paths": [],
   181	        "transcript_exists": False,
   182	        "transcript_match_count": 0,
   183	        "attribution_conflict": False,
   184	        # 保护集必须覆盖**所有见到的候选**（含不可读、含被冲突分支排除的）
   185	        "all_candidate_paths": [],
   186	    }
   187	    uniq = sorted(set(tokens), key=len)
   188	
   189	    root_real = os.path.realpath(transcripts_dir)
   190	    root_prefix = root_real if root_real.endswith(os.sep) else root_real + os.sep
   191	    walk_errors: list[str] = []
   192	
   193	    def _on_walk_error(err: OSError) -> None:
   194	        walk_errors.append(f"{getattr(err, 'filename', '?')}: {err}")
   195	
   196	    # 单次遍历收集**每个 token** 的候选（无条件，供保护集与判定共用）
   197	    per_token: dict[str, list[str]] = {t: [] for t in uniq}
   198	    all_candidates: list[str] = []
   199	    unreadable: list[str] = []
   200	    stat_failures: list[str] = []
   201	    if uniq:
   202	        for dirpath, _dirnames, filenames in os.walk(transcripts_dir, onerror=_on_walk_error, followlinks=False):
   203	            for fname in filenames:
   204	                if not fname.endswith(".jsonl"):
   205	                    continue
   206	                matched = [t for t in uniq if fname.startswith(t)]
   207	                if not matched:
   208	                    continue
   209	                candidate = os.path.join(dirpath, fname)
   210	                # 候选一律入 all_candidate_paths（保护集口径），再谈可用性
   211	                all_candidates.append(candidate)
   212	                try:
   213	                    if os.path.islink(candidate) or not os.path.isfile(candidate):
   214	                        continue
   215	                except OSError as e:
   216	                    stat_failures.append(f"{candidate}: {e}")
   217	                    continue
   218	                if not os.access(candidate, os.R_OK):
   219	                    unreadable.append(candidate)
   220	                    continue
   221	                real = os.path.realpath(candidate)
   222	                if not real.startswith(root_prefix):
   223	                    continue  # 目录 symlink 逃逸
   224	                for t in matched:
   225	                    per_token[t].append(candidate)
   226	    result["all_candidate_paths"] = sorted(set(all_candidates))
   227	
   228	    if not uniq:
   229	        # 无 token: 未做任何归因扫描 —— 不是"确认无源"（round-5 MEDIUM 整改）
   230	        result["attribution_conflict"] = True
   231	        result["no_token"] = True
   232	        return result
   233	
   234	    longest = uniq[-1]
   235	    if any(not longest.startswith(t) for t in uniq[:-1]):
   236	        result["attribution_conflict"] = True
   237	        result["token_conflict"] = True
   238	        return result
   239	    result["session_token"] = longest
   240	
   241	    if walk_errors:
   242	        result["scan_errors"] = walk_errors[:5]
   243	        result["attribution_conflict"] = True
   244	        return result
   245	    if stat_failures:
   246	        result["stat_failures"] = stat_failures[:5]
   247	        result["attribution_conflict"] = True
   248	        return result
   249	    if unreadable:
   250	        result["unreadable_candidates"] = unreadable[:5]
   251	        result["attribution_conflict"] = True
   252	        return result
   253	
   254	    matches = sorted(set(per_token[longest]))
   255	    result["transcript_paths"] = matches
   256	    result["transcript_match_count"] = len(matches)
   257	    if len(matches) == 1:
   258	        result["transcript_exists"] = True
   259	    elif len(matches) > 1:
   260	        result["attribution_conflict"] = True  # ambiguous 多命中，拒绝采信
   261	    return result
   262	
   263	
   264	def probe_qa_metrics(db_path: Path, error_types: list[str]) -> tuple[dict, tuple[int, int] | None]:
   265	    """只读核销 qa_metrics.db（URI mode=ro，无写路径）。返回 (结果, 实际身份)。
   266	
   267	    round-5 BLOCKER②/MEDIUM 整改: 原实现按路径 stat 取身份、SQLite 稍后按路径
   268	    重新打开 —— 两者可能不是同一对象，且无 regular-file/nonblocking 门（FIFO
   269	    会阻塞）。现: fd 打开取 fstat 身份 + S_ISREG 门 → SQLite 打开 → 复核路径
   270	    身份仍等于该身份，不等即拒绝（不采信被换入的对象）。
   271	    """
   272	    result: dict = {"db_path": str(db_path), "opened_readonly": False}
   273	    if not db_path.exists():
   274	        result["verdict"] = "db_missing"
   275	        return result, None
   276	    try:
   277	        fd = os.open(db_path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
   278	    except OSError as e:
   279	        result["verdict"] = f"open_refused: {e}"
   280	        return result, None
   281	    try:
   282	        st = os.fstat(fd)
   283	        if not stat.S_ISREG(st.st_mode):
   284	            result["verdict"] = "not_regular_file_refused"
   285	            return result, None
   286	        identity = (st.st_dev, st.st_ino)
   287	    finally:
   288	        os.close(fd)
   289	
   290	    uri = f"file:{db_path}?mode=ro"
   291	    conn = sqlite3.connect(uri, uri=True)
   292	    try:
   293	        # 复核 SQLite 实际打开的路径身份仍是我们验证过的对象
   294	        try:
   295	            recheck = os.stat(db_path)
   296	        except OSError as e:
   297	            result["verdict"] = f"recheck_stat_failed: {e}"
   298	            return result, identity
   299	        if (recheck.st_dev, recheck.st_ino) != identity:
   300	            result["verdict"] = "identity_changed_between_verify_and_open_refused"
   301	            return result, identity
   302	        result["opened_readonly"] = True
   303	        result["file_identity_verified"] = True
   304	        tables = [
   305	            r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
   306	        ]
   307	        result["tables"] = tables
   308	        if "qa_error_logs" in tables:
   309	            total = conn.execute("SELECT COUNT(*) FROM qa_error_logs").fetchone()[0]
   310	            result["qa_error_logs_rows"] = total
   311	            hits = {}
   312	            for et in sorted(set(error_types)):
   313	                hits[et] = conn.execute("SELECT COUNT(*) FROM qa_error_logs WHERE error_type = ?", (et,)).fetchone()[0]
   314	            result["error_type_hits"] = hits
   315	            result["verdict"] = "no_source_rows" if total == 0 else "rows_present_see_hits"
   316	        else:
   317	            result["verdict"] = "qa_error_logs_table_missing"
   318	    finally:
   319	        conn.close()
   320	    return result, identity
   321	
   322	
   323	def snapshot_file(path: Path) -> tuple[bytes, dict, tuple[int, int]]:
   324	    """一次性读全量 bytes；sha/行数/身份全部派生自**同一个 fd**。
   325	
   326	    round-4 BLOCKER② 整改: 原实现按路径 stat 采集保护身份、稍后才按路径读取，
   327	    两步之间对象可被换掉（源侧 TOCTOU）。现改为打开一次 fd → fstat 取身份 →
   328	    从该 fd 读全量，返回的 (st_dev, st_ino) 即**实际被读取对象**的身份。
   329	    """
   330	    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)

**Analyzing SQLite ABA race vulnerability**
**Evaluating SQLite race condition mitigation**
**Planning race condition reproduction strategy**
**Analyzing SQLite identity handling risks**
**Identifying race condition allowing output overwrite**
**Confirming output truncation despite identity mismatch**
**Verifying SQLite connection locking behavior**
**Assessing WAL file truncation risk**
**Clarifying QA metrics DB sidecar relevance**
**Analyzing token resolution limitations**
**Evaluating transcript protection without tokens**
**Inspecting no-write contract and output path**
**Verifying token conflict handling and symlink protection**
**Analyzing TOCTOU risks in file stat protection**
**Evaluating race conditions in output path handling**
**Analyzing inode replacement and recovery implications**
**Assessing symlink handling and stat error detection**
**Verifying error handling order and exit conditions**
**Identifying token conflict impact on error handling**
**Analyzing residual blocker in scan error handling**
**Questioning conflict with byte_exact output**
**Assessing attribution_conflict accuracy**
**Planning ledger JSON analysis with jq**
codex
初步静态路径已锁定：八项声明大多确实落在生产脚本，而不是只改报告。不过 QA DB 的实现存在一个关键待证点——验证 fd 在 SQLite 按路径打开前已关闭，且“身份变化拒绝”目前只是探针 verdict，主流程仍继续写出；我正在用实际控制流判断这是否仍留下原 BLOCKER 的截断路径。同时也在检查 transcript 扫描失败是否真的会阻止写出，而不只是改成 `unverifiable`。
exec
/bin/zsh -lc "jq '{card,generated_at,dlq_file,compare_copies,total_lines,total_records,unparseable_lines,class_distribution,recoverability_distribution,inline_state_distribution,attribution_conflict_count:(.attribution_conflicts|length),duplicate_cluster_count:(.duplicate_clusters|length),duplicate_occurrences:([.duplicate_clusters[].occurrences]|add),qa_metrics_probe}' _bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
exec
/bin/zsh -lc "rg -n -C 3 '92|89|byte_exact|approximate|unverifiable|unrecoverable|重复簇|归因冲突|no_token|callout_annotation|只读|零写入|qa_metrics|transcript' _bmad-output/审查/G4-9-DLQ-census-2026-08-28.md" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
{
  "card": "CARD-G4-9",
  "generated_at": "2026-08-28T12:23:16.503247+00:00",
  "dlq_file": {
    "path": "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl",
    "exists": true,
    "line_count": 92,
    "sha256": "3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590",
    "mtime_utc": "2026-08-11T14:01:25.808462+00:00",
    "mtime_note": "mtime 取自读取用 fd 的 fstat；绑定 exact bytes 的是 sha256"
  },
  "compare_copies": [
    {
      "path": "/Users/Heishing/Desktop/canvas/canvas-learning-system/backend/data/dead_letter_episodes.jsonl",
      "exists": true,
      "line_count": 685,
      "sha256": "490c903b2f3636e1d2c4ecb68465cef41ace06f0bd171eb2fb95c03a7b40cb43",
      "mtime_utc": "2026-04-07T11:47:19.585617+00:00",
      "mtime_note": "mtime 取自读取用 fd 的 fstat；绑定 exact bytes 的是 sha256"
    },
    {
      "path": "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/data/dead_letter_episodes.jsonl",
      "exists": true,
      "line_count": 1,
      "sha256": "bfb3f6c413aab7dd4c04a25f7575aaaffcfc92fd4e8e8966362609652ac7e310",
      "mtime_utc": "2026-07-13T04:51:14.925282+00:00",
      "mtime_note": "mtime 取自读取用 fd 的 fstat；绑定 exact bytes 的是 sha256"
    },
    {
      "path": "/Users/Heishing/Desktop/canvas/canvas-learning-system/data/dead_letter_episodes.jsonl",
      "exists": true,
      "line_count": 4,
      "sha256": "75c5f7593b9b2e99672d0551487b4476552ebd8d33ad25c5f9479683cc61e9c9",
      "mtime_utc": "2026-04-05T23:30:49.019652+00:00",
      "mtime_note": "mtime 取自读取用 fd 的 fstat；绑定 exact bytes 的是 sha256"
    }
  ],
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
  "duplicate_cluster_count": 6,
  "duplicate_occurrences": 29,
  "qa_metrics_probe": {
    "db_path": "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db",
    "opened_readonly": true,
    "file_identity_verified": true,
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

 succeeded in 0ms:
1-# CARD-G4-9 — DLQ 真实挂载 census 分诊报告
2-
3-> **批次**: BATCH-2026-08-28-第五批 / CARD-G4-9（4h · wave 1 · 未来铺路）
4:> **性质**: 纯只读 census。0 写入、0 重放、0 业务代码改动。唯一代码产物 = `backend/scripts/census_dead_letter_episodes.py`。
5-> **代码基线**: 分析对象锚定 `37387a86`（第五批开工基线）。**本卡交付物 artifact commit 链**：精确 SHA 逐段记录于 `_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt`（commit 无法自含己身 SHA，故用后置 receipt 绑定——Codex round-4 LOW 整改）
6:> **台账**: `_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json`（92 条逐条，G4-10 消费）
7-> **证据包**: `_bmad-output/审查/G4-9-evidence/`（shasums before/after、grep 自证、容器内 sha 实测）
8-> **执行日期**: 2026-08-28
9-
--
15-
16-```
17-docker exec canvas-learning-system-backend sha256sum /app/data/dead_letter_episodes.jsonl
18:→ 3b37460f4215f6ac...ef3ba590（92 行）— 与宿主 live 地址逐字节一致
19-```
20-
21-| 地址 | 路径 | 行数 | sha256 前 16 | mtime | 裁定 |
22-|---|---|---|---|---|---|
23:| **live**（权威） | `…/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl` | **92** | `3b37460f4215f6ac` | 2026-08-11 22:01 (+0800) | 容器 `/app/data` 经 `./backend:/app` 挂载即此文件；census 对象 |
24-| 主仓 | `canvas-learning-system/backend/data/dead_letter_episodes.jsonl` | 685 | `490c903b2f3636e1` | 2026-04-07 | 陈旧副本（部署迁往 worktree 前的历史死信，止于 4 月）；不代表现网 |
25-| 孤儿① | `…/worktrees/feature-obsidian-hybrid-dev/data/dead_letter_episodes.jsonl` | 1 | `bfb3f6c413aab7dd` | 2026-07-13 | 已删除的 `./data:/app/data` 子挂载目标残留；从未在容器内生效 |
26-| 孤儿②（附注） | `canvas-learning-system/data/dead_letter_episodes.jsonl` | 4 | `75c5f7593b9b2e99` | 2026-04-06 | 主仓根 `data/` 早期宿主进程 cwd 落点残留 |
27-
28:**compose :206-212 遮蔽史**（本 worktree `docker-compose.yml:206-212`，与 live worktree 同文）：`- ./data:/app/data` 是嵌套 bind，被 `./backend:/app` 父挂载遮蔽——`docker inspect` 记录了它，但容器 `/proc/self/mountinfo` 从不出现，**实际生效的一直是 `backend/data/`**。R11-BATCH2（2026-08-17）已删除该行，理由是遮蔽与否取决于挂载顺序、一次 recreate 就可能翻转，届时 92 行死信会被 1 行的孤儿①覆盖不可见。删除后 `/app/data` 恒等于 `backend/data/`。**证据边界（诚实声明）**：本卡独立实证的是**现状**（容器内 sha 与宿主 live 地址同源、当前 compose 无子挂载行）；"历史上子挂载从未在容器内生效"沿引 compose 注释史与 R11-BATCH2（2026-08-17）当时的 mountinfo 实测记录，本卡未重跑历史 `docker inspect` 独立复证。
29-
30-**本 worktree（card-s5-census）没有 `backend/data/dead_letter_episodes.jsonl`**——数据文件不入 git，census 一律指向 live 绝对路径运行，未复制任何数据进本 worktree。
31-
32-## §2 总量与分类台账（class 分诊）
33-
34:92 条，分类与勘探预期**零偏差**：
35-
36-| class | 条数 | 预期 | error_type | 错误原文（截断） | 根因与修复状态 |
37-|---|---|---|---|---|---|
38:| `budget_400` | **89** | 89 | BadRequestError | `Error code: 400 … 'request (16998 tokens) exceeds the available context size (16384 tokens)' type: exceed_context_size_error` | 本地 LLM 服务 context 16384 上限被超（实测请求 16948–20831 tokens）。**未修复**——根因治理归 G4-10（切块或提 budget） |
39-| `schema_entity_type` | **2** | 2 | EntityTypeValidationError | `name cannot be used as an attribute for LearningConcept as it is a protected attribute name.` | **已修复**：P0-4（2026-05-14）双处——`entity_types.py:343` `LearningConcept.name`→`concept_name`（行 1）+ `entity_types.py:254` `LearningTip.created_at`→`tip_created_at`（行 2），同型冲突不再发生 |
40-| `group_id_format` | **1** | 1 | GroupIdValidationError | `group_id "vault:default" must contain only alphanumeric characters, dashes, or underscores` | **已修复**：`group_id_compat.py:64 sanitize_group_id_for_graphiti` 冒号→`__` 物理化已兜（T1 契约），写路径不再直传 D16 冒号格式 |
41-| `unexpected` | 0 | 0 | — | — | 无偏差需解释 |
42-
43:时间分布：3 条 schema/group_id 全部 2026-05-14（P0-4 修复当日之前的失败）；89 条 budget 集中于 2026-08-08 ~ 08-11（8/48/25/8），系 SessionEnd 归档-蒸馏管道对长会话反复触发超限。group_id 分布：`vault:canvas_vault`×89、`vault:default`×3（三条旧格式记录重放时需 group 重映射，见 §6）。
44-
45-## §3 inline 完整性 + SHA 对账
46-
47:`DeadLetterStore.store()` 落盘的 `episode_body` 来自 `EpisodeTask.to_dict()`，后者做 `episode_body[:200]` 截断（`episode_worker.py:107`，"truncate for logging"）；全量正文只有 `DEAD_LETTER_STORE_FULL_BODY` 开启时以 `episode_body_full` 另存——**live 容器该 env 未设置（实测），92 条 `episode_body_full` 均缺席**。逐条重算 sha256(inline) 对账 `episode_body_sha256` 结果：
48-
49-| inline 状态 | 条数 | 判据 |
50-|---|---|---|
--
54-
55-4 条 full_verified = 3 条 callout（§2 的 schema/group_id 三条）+ 1 条短 qa_highlight（行 74）。
56-
57:## §4 源指针核销（qa_metrics.db，只读 mode=ro）
58-
59:- **qa_metrics.db**（live `backend/data/qa_metrics.db`，经 sqlite URI `mode=ro` 打开）：唯一表 `qa_error_logs`（列 category/error_type/source_module/stack_summary/created_at，**无 request_id 列**），**行数 = 0**。按三个 error_type 探查命中均 0。**核销裁定：`no_source_rows` —— qa_metrics.db 对 92 条死信不构成任何源指针，0/92 可经其溯源。**
60-- 附加核销（超出卡面要求，如实记录以封死"还有别处可捞"的幻想）：
61-  - `llm_call_logs.db`（同目录，mode=ro）：仅 token/延迟/成本指标列，**无 prompt/response 正文**；
62:  - `backend/data/outbox/`：**空目录**（A7 outbox 只接 enqueue 失败，本 92 条全部是 enqueue 成功、处理失败，不经 outbox）；
63-  - `episode_body_full`：0 条（§3）。
64:- **有效源指针只剩一条**：DLQ 记录的 `request_id`（structlog contextvars 捕获的进程内值）把同一次 SessionEnd 归档的 3–5 条 episode 绑成组，组内 `session-archive:<id16>` / `…session:<hex>` 名字携带 session id → `~/.claude/projects/-…-canvas-vault/<session>.jsonl` transcript。**7 个 session 的 transcript 全部在盘实测存在**（90,584–723,950 字节，逐一恰 1 个 glob 命中、常规文件），88/88 条截断记录归因成功、0 条归因冲突。**归因边界（诚实声明）**：归因 = "唯一在盘候选已定位"，≠ "内容已验证"——本卡未读任何 transcript 内容，内容级核验归 G4-10 重建时以 `episode_body_sha256` 对账。
65-
66:## §5 可恢复性裁定（三态 + unverifiable 第四态）
67-
68-| 三态 | 条数 | 裁定依据 |
69-|---|---|---|
70:| **可字节级**（byte_exact） | **4** | inline 正文全量：sha256 重算对账通过**且**长度精确匹配（fail-closed 双门）——重放可逐字节还原 episode |
71:| **近似**（approximate） | **88** | inline 仅 200 字符前缀，但经 request_id 组归因到在盘 transcript；G4-10 可对 22 条 session-archive 重新格式化 transcript（确定性、可用 `episode_body_sha256` 验证是否达字节级）、对 66 条 qa_highlight(44)/distillation(22) 重跑蒸馏（LLM 非确定性，语义近似、不保证逐字节） |
72:| **不可恢复**（unrecoverable） | **0** | inline 截断且经完整可见的扫描确认无在盘上游源 |
73:| **不可核验**（unverifiable，round-4 新增） | **0** | 源可见性不足（扫描受阻/不可读候选/归因冲突）——既不宣称可恢复，也不宣称不可恢复。Codex round-4 指出：把"看不见"终态化为"不可恢复"是不诚实断言，故单列第四态 |
74-
75:**不可恢复清单（显式成段）**：本次 census 裁定不可恢复条目 **0 条**；三态裁定覆盖 92/92，**"待定"0 条**。
76-
77:诚实边界：`近似` ≠ 已恢复。88 条的实际重建（含 22 条 session-archive 是否能达字节级）是 G4-10 的工作与验收，本卡只交付"上游源在盘、路径已核销"的证据链。transcript 属用户本机 `~/.claude/projects/` 数据，若未来被清理，近似裁定随之失效——台账已逐条记录 transcript 绝对路径供 G4-10 开工时复核。
78-
79-## §6 台账稳定键（G4-10 交接契约）
80-
81:台账逐条携带复合键 `{line_no, sha256_prefix(16 hex), request_id}`。**语义（Codex round-1 LOW-2 修正）**：这是**冻结快照内的 occurrence key**，不是跨文件重排或语义幂等键——台账头部 `dlq_file.sha256`（`3b37460f4215f6ac…`）即快照指纹，`line_no` 在该快照内已单列唯一；`sha256_prefix`（本快照 69 个唯一值，qa_highlight 家族实测同名同 sha 多条）与 `request_id`（仅 25 个唯一值，进程内 contextvars、重启可复用）是**冗余对账/诊断维度**，不是唯一性的必要条件。G4-10 消费前先 diff 头部 sha 即知 DLQ 是否长了新条目；语义级去重不得按本键，须按 `duplicate_clusters` 段（见下）。**语义重复簇（MEDIUM-2 整改）**：按 `{name, episode_body_sha256, group_id}` 聚簇，**6 簇覆盖 29 行**（最大簇 = 同一 session-archive 16 行，`reference_time` 各不相同——同内容反复入队反复超限）。台账 `duplicate_clusters` 段逐簇列 line_nos，records 逐条透传 `reference_time`；G4-10 重放前必须先定去重策略（89 条 budget 修根因后若逐条盲放，将把同内容写入最多 16 遍）。
82-
83:**隐私（MEDIUM-3 整改）**：`transcript_paths` 含本机用户名与完整 session UUID，台账与本报告为 **private-only 工件**（台账头部已带 privacy 字段；仓库纪律 = 不 push 公网远端）。
84-
85:逐条另带 `class / inline_state / recoverability / transcript_paths / transcript_match_count / attribution_conflict / error_excerpt / failed_at / reference_time`，G4-10 可直接按 `recoverability` 分桶排重放优先级（建议：4 条 byte_exact 先行——但其中 3 条 group_id 为已弃用 `vault:default`，重放前需按 D16 规约重映射并过 `to_physical_group_id()`；89 条 budget_400 重放前必须先修 context 超限根因，否则原样重放必然复现 400）。
86-
87-## §7 裁判证据（整改版脚本重跑）
88-
89-| 证据 | 结果 |
90-|---|---|
91:| 运行前后 shasum（live/主仓/孤儿①/孤儿② 四份 DLQ + qa_metrics.db） | `diff shasums-before.txt shasums-after.txt` 空 → **PASS，0 写入** |
92-| grep 自证（import 行全 stdlib；neo4j/graphiti/bolt/app. import 0 命中；`--apply` 定义 0 命中；写模式 open 仅 `--out` 1 处且受路径碰撞守卫保护） | **PASS**（`grep-selfattest.txt`，含守卫在位证明） |
93:| 容器内 sha 实测 | 92 行、sha 与宿主 live 地址一致（`container-sha-check.txt`） |
94:| class 偏差 | 无（89/2/1 与勘探预期一致，脚本 `class_deviation` 字段为空） |
95:| 负例门（round-1 整改自证） | `--out`==`--dlq` → exit 2 拒写、DLQ 完好；transcripts 根缺失 → exit 2 拒诊；sha 匹配但长度不符（round-1 HIGH-1 反例①）→ anomaly/unrecoverable；坏 JSON 行/空行 → unparseable 逐行入台账不拒诊 |
96:| 负例门（round-2 整改自证） | **hardlink** 指向 DLQ 的 --out → exit 2 + DLQ sha 不变；**case-only 别名**（`DLQ.jsonl`）→ exit 2 + DLQ 完好；**anomaly + episode_body_full 组合**（sha 对但长度 999）→ anomaly/unrecoverable（不再翻案 byte_exact）；**chmod 000 根** → exit 2 拒诊；**symlink 逃逸**（根内 .jsonl → 根外 .txt）→ match_count=0/unrecoverable；正例回归：真实唯一命中仍 approximate |
97-
98-## §7b Codex round-1 整改记录（BLOCKED → 全项整改）
99-
100-- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
101-- **BLOCKER-2（快照不原子）**：DLQ 单次 `read_bytes()`，头部 sha256/line_count 与逐条 records 派生自同一份内存字节；mtime 显式标注为 stat 参考值。
102-- **BLOCKER-3（交付物未冻结漂移）**：以本卡 commit 冻结全部交付物 exact bytes（脚本/报告/台账/证据包同 commit）；grep-selfattest 已按最终版行号重生成并内嵌脚本 sha 前缀。
103:- **HIGH-1（inline 判定不 fail-closed）**：full_verified 加长度精确匹配门；truncated_prefix 加 64-hex 合法性门；anomaly 一律 unrecoverable + 如实 basis（不再谎称截断、不再滑入 approximate）。
104:- **HIGH-2（request_id fail-open）**：分组键改 `(类型名, 值)`；缺失/None 按 line_no 单条成组零传染；组内多 token 前缀一致门，冲突记 `attribution_conflict` 拒绝采信（现网 92 条 0 冲突）。
105:- **HIGH-3（transcript 归因折叠）**：恰 1 个常规文件命中才算归因（多命中 = ambiguous 拒采信）；glob 改递归下探；transcripts 根缺失整体 exit 2（拒绝产出 unrecoverable 假象）。
106:- **MEDIUM-1**：`episode_body_full` 在盘且 sha 对账通过 → byte_exact 采信（现网 0 条，通路已备）。
107-- **MEDIUM-2**：`duplicate_clusters` 段 + 逐条 `reference_time`（见 §6）。
108-- **MEDIUM-3**：台账头部 privacy 字段 + 本报告 private-only 声明（见 §6）。
109-- **LOW-1~4**：token 区间 16948–20831、长度区间 205–8036、稳定键语义重写、schema 双处证据、挂载历史证据边界——均已在正文落地。
110-
111:整改后全量重跑：**92 条数字与整改前逐项一致**（class 89/2/1、三态 4/88/0、归因冲突 0、unparseable 0），重复簇 6/29 行与 Codex 独立复算吻合。另有独立 Workflow 4-agent 复核（92 条重算 0 mismatch、7 transcript 在盘实测、台账 sha 一致）交叉确认。
112-
113-## §7c Codex round-2 复审整改记录（10/13 CLOSED → 剩余 3 项 + 3 新 LOW 全部整改）
114-
115-round-2 复审确认 BLOCKER-2/3、HIGH-2、MEDIUM-1~3、LOW-1~4 共 10 项 CLOSED，并抓出 3 项**未真正闭合**（均实测复现）+ 3 条新 LOW：
116-
117-- **BLOCKER-1 NOT-CLOSED（hardlink / case-only 别名绕过）**：原守卫比较 `resolve()` **字符串**，hardlink 指向输入、以及大小写不敏感文件系统上的 case-only 别名均绕过并截断输入。**整改**：改为比较**文件身份 `(st_dev, st_ino)`**（对已存在的 --out）+ 保留路径比较作第二道。负例实测：两种绕过均 exit 2、DLQ sha 不变。
118:- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
119:- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
120-- **新 LOW ×3**：full_verified 长度范围修正为 131–180；台账 `class_distribution`/`recoverability_distribution` 补零并新增 `inline_state_distribution`（固定 schema，消费者无需补齐缺席键）；`line_count` 改用 `splitlines()` 与 records 同口径（原 `count("\n")` 在 bare CR / U+2028 下会与 records 数不一致）。
121-
122:round-2 整改后再次全量重跑：92 条、class 89/2/1、三态 4/88/0、重复簇 6/29、shasum 不变——**数字仍逐项一致**，整改只收紧通用鲁棒性。
123-
124-## §8 复现命令
125-
--
127-cd .claude/worktrees/card-s5-census
128-python3 backend/scripts/census_dead_letter_episodes.py \
129-  --dlq "…/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl" \
130:  --qa-metrics-db "…/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db" \
131-  --compare "…/canvas-learning-system/backend/data/dead_letter_episodes.jsonl" \
132-  --compare "…/feature-obsidian-hybrid-dev/data/dead_letter_episodes.jsonl" \
133-  --compare "…/canvas-learning-system/data/dead_letter_episodes.jsonl" \
--
140-
141-round-3 确认 HIGH-1 与三条 LOW 已 CLOSED、台账数字有效且与 commit 字节一致，两项路径安全判 PARTIAL：
142-
143:- **BLOCKER-1 残留两条绕过**：① `protected_paths` 未含**归因到的 transcript**，`--out=<唯一 transcript>` 会截断恢复源；② check-then-open 的 **TOCTOU** 仍在（检查后、打开前把 --out 换成指向 DLQ 的链接）。**整改**：① 写出前把全部 `transcript_paths` 并入保护集；② 改 `os.open(O_WRONLY|O_CREAT|O_NOFOLLOW)` **不带 O_TRUNC** 打开 → 对**实际 fd** `fstat` 校验 inode → 通过才 `ftruncate`，检查与写入作用于同一 fd，替换攻击无效。反例实测：`--out` 指向唯一 transcript → exit 2、transcript sha 不变。
144:- **HIGH-3 残留**：`glob(recursive=True)` 在 realpath 过滤**之前**已递归遍历（Python 3.14 glob 跟随目录 symlink 且**静默吞掉不可读子树错误**）→ 越根枚举 + "假唯一/假不可恢复"；mode `000` 的 regular transcript 仍过 `isfile()` 被判 approximate。**整改**：改 `os.walk(onerror=..., followlinks=False)`（不跟随目录 symlink、遍历错误显式捕获）+ 候选加 `os.access(R_OK)` 门；遍历受阻或存在不可读候选一律记 `attribution_conflict` 拒绝裁定（既不宣称找到、也不宣称不可恢复）。三条反例实测全部 fail-closed。
145-- **新 MEDIUM（JSONL framing）**：生产端 `ensure_ascii=False` 可原样写出字符串内的 U+2028，`splitlines()` 会把一条合法单-LF 记录劈成两条坏行。**整改**：新增 `_split_jsonl_lines()` 严格按 LF 分帧，header `line_count` 与 records 共用同一函数。
146-- **新 LOW（输入 schema）**：合法 JSON 但非对象（`null` / 数组 / 标量）解析成功后在 `rec.get()` 处抛 AttributeError 炸全量。**整改**：非 dict 归 `unparseable`（`not_a_json_object: <type>`），实测两条毒行不影响其余记录。
147-- **新 LOW（provenance）**：报告头只写起始基线未区分整改 artifact commit —— 已在报告头补三段 commit 链。
148-
149:round-3 整改后第三次全量重跑：92 条、class 89/2/1、三态 4/88/0、重复簇 6/29、shasum 不变——**三轮整改数字全程未变**，改的全是通用鲁棒性与路径安全。
150-
151-## §7e Codex round-4 复审整改记录（1/6 CLOSED → 全部 9 项整改）
152-
153-round-4 只认可 1 项 CLOSED（非 dict JSON 门），并用更深的静态反例推翻了另外 5 项的"闭合"，另提 2 BLOCKER / 1 HIGH / 2 MEDIUM / 3 LOW。逐条整改（全部实测复现→封死）：
154-
155:- **BLOCKER①（不可读但可写的 transcript 绕过保护集）**：mode `0200` 的候选在 unreadable 分支被清空 `transcript_paths`，因此不进保护集，`--out` 指向它仍被截断（无需竞态）。**整改**：新增 `all_candidate_paths` 保留**所有见到的候选**（含不可读、含被冲突分支清空的），写出前全部并入保护集。实测：mode 0200 候选作 `--out` → exit 2、文件字节不变。
156-- **BLOCKER②（源侧 TOCTOU）**：保护身份按**路径** stat 采集、DLQ 稍后才按路径读取，两步间可换入另一 inode → 实际读取对象不在保护集。**整改**：`snapshot_file()` 改为 `os.open(O_RDONLY|O_NOFOLLOW|O_NONBLOCK)` → `fstat` 取身份 + regular-file 门 → **从同一 fd 读全量**，返回的身份即**实际被读取对象**；compare 副本同样以读取身份入保护集；输入 `stat` 失败不再静默吞而是 exit 2。
157:- **HIGH（不可见被终态化为 unrecoverable）**：扫描受阻/冲突时主链仍产出 `unrecoverable`，与报告"既不宣称不可恢复"自相矛盾。**整改**：引入第四态 **`unverifiable`**（源可见性不足，basis 逐条说明是遍历受阻/不可读候选/归因冲突），distribution 与 `unverifiable_list` 同步。实测：不可读子树 → `unverifiable=1`，不再冒充 unrecoverable。
158-- **MEDIUM（FIFO/设备节点）**：`--out` 缺 regular-file gate 与 `O_NONBLOCK`。**整改**：`O_NONBLOCK` + `S_ISREG` 双门（读侧同样）。实测：FIFO 作 `--out` → exit 2 且不阻塞。
159-- **MEDIUM（非法 UTF-8 冒充有效记录）**：`errors="replace"` 把坏字节改写成合法对象。**整改**：`_split_jsonl_lines()` 改**逐行 strict decode**，解码失败归 `unparseable`。实测：`b'{"a":"\xff"}'` → `utf8_decode_error`，records=0。
160:- **LOW ×3**：dict 内字段错型防御（`name=None` / `request_id=[]` 不可哈希 / `episode_body` 非 str 均不再炸全量，按 line_no 单条成组或判 anomaly）；`transcripts_dir="/"` 的 `//` containment 特例；`0o600` 对**既有**输出文件用 `fchmod` 显式收紧（实测台账 mode 现为 `-rw-------`）。
161-- **LOW（provenance 自指）**：commit 无法自含己身 SHA，改用后置 `artifact-commit-receipt.txt` 绑定精确链，报告头指向该 receipt。
162-
163:round-4 整改后第四次全量重跑：**92 条、class 89/2/1、三态 4/88/0（unverifiable 0）、重复簇 6/29、shasum 不变——四轮整改数字全程未变**。
164-
165-## §7f Codex round-5 复审整改记录（3/8 CLOSED → 9 项全部整改）
166-
167-round-5 用更深的静态反例继续推翻"闭合"，提出 2 BLOCKER / 2 HIGH / 2 MEDIUM / 3 LOW，逐条整改并实测：
168-
169:- **BLOCKER①（token 冲突/无 token 时扫描前早退 → 候选不进保护集）**：`--out` 指向冲突组的候选 transcript 仍可无竞态截断。**整改**：`resolve_group_attribution()` 重写为**先扫描后判定**——无条件为每个 token 扫描收集候选进 `all_candidate_paths`（保护集口径），再做冲突/唯一性判定；候选 `stat` 失败不再 `continue` 吞掉而是 exit 2（保护集不完整即拒绝写出）。实测：冲突候选作 `--out` → exit 2、文件 sha 不变。
170:- **BLOCKER②（qa_metrics.db 身份未绑定实际读取）**：仍是早期 path-stat + SQLite 稍后按路径重开。**整改**：`probe_qa_metrics()` 改 `os.open(O_RDONLY|O_NOFOLLOW|O_NONBLOCK)` 取 fstat 身份 + `S_ISREG` 门 → SQLite 打开后**复核路径身份仍等于该身份**，不等即 `identity_changed_..._refused`；身份入保护集。本次运行 `file_identity_verified: true`。
171:- **HIGH①（anomaly 吞掉不可见性）**：`anomaly→unrecoverable` 排在 conflict 判断之前，`anomaly + 扫描受阻` 仍被假终态化。**整改**：判定链改为**可见性优先**——归因不可核验时无论 inline 状态一律 `unverifiable`，basis 逐条写明原因（无 token / token 冲突 / 扫描受阻 / 候选 stat 失败 / 不可读候选 / 多命中 ambiguous），并附注 inline 是否也 anomaly。实测：anomaly+不可读子树 → `unverifiable`。
172:- **HIGH②（`fchmod` 先于 protected-id 检查）**：`--out` 指向受保护的 0644 输入时，会**先把只读输入权限改成 0600** 再拒绝——字节没截断但输入已被修改。**整改**：碰撞检查前移到 `fchmod` 之前。实测：mode 644 → 644 不变。
173-- **MEDIUM（QA DB 无特殊文件门）**：随 BLOCKER② 一并加 `S_ISREG` + `O_NONBLOCK`。
174:- **MEDIUM（无 token 未扫描即判不可恢复）**：改为 `unverifiable` + `no_token` 标记（见 HIGH①）。
175-- **LOW ×3**：单独 `b"\n"` 现算 1 个空行（实测 `line_count=1`）；`errors="replace"` 改 **strict encode**（JSON escaped lone surrogate 不能再构造假 `full_verified`）；`bool` 是 `int` 子类 —— `episode_body_length=True` 现被长度门拒绝（实测判 anomaly）。
176-
177:**归因冲突计数由 0 变为 3（如实说明）**：round-5 起"名字不含 session token"被诚实标记为 `no_token`（未做归因扫描），命中的正是 3 条 `callout_annotation` 记录。它们 inline 正文全量、sha 对账通过，**不依赖 transcript**，故仍判 `byte_exact`——三态分布不变（4/88/0/0），88 条 approximate 仍全部为唯一 transcript 命中。这是标注口径变诚实，不是结论变化。
178-
179:round-5 整改后第五次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变——五轮整改数字全程未变**。

exec
/bin/zsh -lc "rg -n -C 3 '92|89|byte_exact|approximate|unverifiable|unrecoverable|重复簇|归因冲突|no_token|callout_annotation|只读|零写入|qa_metrics|transcript|写入' _bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
3-title: "UAT · CARD-G4-9 DLQ 真实挂载 census 分诊（2026-08-28）"
4-date: 2026-08-28
5-status: awaiting_user
6:scope: "BATCH-2026-08-28-第五批 / CARD-G4-9 — live DLQ 92 条只读 census：分类/SHA 对账/可恢复性三态/挂载真相，产出 G4-10 交接台账"
7-worktree: "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census"
8----
9-
10-# UAT · CARD-G4-9 DLQ 真实挂载 census 分诊
11-
12-> [!info]+ 你不需要碰命令行 — 全部技术验证我已代跑（结果见下）
13:> 这张卡**没有修任何东西，也没有恢复任何数据**——它是一次"清点尸体"的只读普查：
14:> 线上 Graphiti 写入失败后落进死信文件的 92 条记录，逐条查清"是什么死的、还能不能救、去哪里救"，
15-> 给后续的 G4-10（真正做恢复的卡）留一份带稳定编号的台账。卡面如实标注：离日常使用价值远，属恢复能力地基。
16-
17-## 📌 你需要过目的三个结论
18-
19:1. **92 条死信全部查清、零"待定"**：89 条是"内容太长超过本地模型 16384 token 上限"（未修，根因归 G4-10）；2 条是 5 月 14 日的 schema 冲突、1 条是旧 group_id 冒号格式——这 3 条的根因**当天之后就已修复**，不会再新增。
20:2. **一条都不算丢**：4 条正文完整躺在死信文件里（可逐字节恢复）；88 条只存了前 200 字预览，但每一条都顺着线索找回了**唯一**源头会话记录（7 个会话的原始 transcript 全部还在你电脑上）——可近似重建（找到了源头 ≠ 已经恢复，真正重建是 G4-10 的活）。**不可恢复：0 条**。另清点出 6 组重复（29 条是同内容反复入队），G4-10 恢复时会先去重，不会把同一段写 16 遍。
21-3. **死信文件的"真身"只有一处**：线上容器读写的是 `feature-obsidian-hybrid-dev` worktree 的 `backend/data/`（容器内实测 sha 一致）；主仓那份 685 行是 4 月的陈旧副本，另有两处孤儿残留——报告里有四址对照表，以后不会再查错文件。
22-
23-## ✅ 技术验证（Claude 已代跑）
24-
25-| 项 | 结果 | 证据 |
26-|---|---|---|
27:| 全程零写入（裁判判据 e） | 运行前后 四份 DLQ 文件 + qa_metrics.db 的 sha256 **逐字节不变**（diff 为空 → PASS） | `_bmad-output/审查/G4-9-evidence/shasums-before.txt` / `shasums-after.txt` |
28:| 脚本只读自证（判据 a） | import 行全 stdlib；neo4j/graphiti/bolt/app. import **0 命中**；`--apply` 定义 **0 命中**；写模式 open 仅台账 `--out` 1 处 | `G4-9-evidence/grep-selfattest.txt` |
29:| live 挂载真相（判据 c） | 容器内 `sha256sum /app/data/dead_letter_episodes.jsonl` = 宿主 live 地址同值（92 行，`3b37460f…`）；compose :206-212 遮蔽史入报告 §1 | `G4-9-evidence/container-sha-check.txt` + 报告 §1 |
30:| 分类零偏差（判据 b） | budget_400×**89** / schema×**2**（P0-4 已修，`entity_types.py:343`）/ group_id×**1**（sanitize 已兜，`group_id_compat.py:64`）——与勘探预期逐条一致，脚本 `class_deviation` 字段为空 | 台账 JSON `class_distribution` |
31:| inline 完整性 + SHA 对账（判据 b） | 92/92 重算 sha256 对账：4 条 full_verified、88 条 truncated_prefix（`to_dict()` 的 `[:200]` 截断，`episode_worker.py:107`）、**0 条 anomaly** | 台账 JSON 逐条 `inline_state`/`sha_check` |
32:| 源指针核销（判据 b，qa_metrics.db 只读 mode=ro） | `qa_error_logs` **0 行** → 0/92 可经 qa_metrics.db 溯源（诚实记录）；附加核销：llm_call_logs.db 无正文、outbox 空、episode_body_full 0 条；**有效源指针 = request_id 组内 session 归因 → 7 个 transcript 全部在盘实测存在** | 报告 §4 + 台账 `qa_metrics_probe` |
33-| 可恢复性三态（判据 b） | 可字节级 **4** / 近似 **88** / 不可恢复 **0**；不可恢复清单显式成段 0 条、"待定" 0 条 | 报告 §5 + 台账 `recoverability_distribution` |
34:| G4-10 稳定键（判据 d） | 逐条复合键 `{line_no, sha256_prefix, request_id}` + 台账头部冻结文件 sha；request_id 92 条仅 25 唯一值的实测证明单列不可作键 | 报告 §6 + 台账 `records[].stable_key` |
35:| Codex 独立审查 round-1 | **BLOCKED**（3 BLOCKER：--out 可截断输入 / 快照不原子 / 交付物未冻结；3 HIGH：inline 判定 fail-open / request_id 归因传染 / transcript 归因折叠；3 MEDIUM + 4 LOW。同时确认：**当前 92 条数字逐项 0 mismatch**、class/三态/家族计数全对） | `_bmad-output/审查/codex-review-CARD-G4-9.md` |
36-| Codex findings 逐条整改 | **13/13 完成**（见下）；整改版脚本负例门全过；全量重跑数字与整改前逐项一致 | 报告 §7/§7b + 证据包 |
37:| Codex 复审 round-2 | **仍阻断**（10/13 CLOSED；BLOCKER-1/HIGH-1/HIGH-3 未真正闭合 + 3 新 LOW）。同时独立复算确认：67ccebe1 冻结生效、92 条数字与 6/29 重复簇全部可复算 | `_bmad-output/审查/codex-review-CARD-G4-9-round2.md`（codex 被 cyber 误拦，内容由 stdout 抢救存档） |
38-| round-2 findings 逐条整改 | **6/6 完成**：inode 身份守卫封 hardlink+大小写别名 / full_body 长度门+anomaly 前置 / 不可读根 exit 2+symlink 逃逸拒采信 / 3 新 LOW。5 条新负例实测全过、正例无回归、数字仍逐项一致 | 报告 §7/§7c + `grep-selfattest.txt` |
39-| Codex 复审 round-3 | **仍阻断**（4/6 CLOSED；BLOCKER-1/HIGH-3 判 PARTIAL + 1 新 MEDIUM + 2 新 LOW）。同时确认：HIGH-1 与三条 LOW 已闭合、台账数字有效且与 commit 字节一致 | `_bmad-output/审查/codex-review-CARD-G4-9-round3.md` |
40:| round-3 findings 逐条整改 | **6/6 完成**：transcript 并入保护集 / O_NOFOLLOW+fstat 消 TOCTOU / os.walk 替 glob（不跟随目录 symlink+遍历错误显式捕获）/ 不可读候选 fail-closed / JSONL 严格 LF 分帧 / 非 dict 归 unparseable。6 条新反例实测全过、数字第三次不变 | 报告 §7d + `grep-selfattest.txt` |
41-| Codex 复审 round-4 | **仍阻断**（1/6 CLOSED；2 新 BLOCKER + 1 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round4.md` |
42:| round-4 findings 逐条整改 | **9/9 完成**：全候选入保护集 / 读侧 fd 身份消源侧 TOCTOU / 新增 unverifiable 第四态 / FIFO 设备门 / strict UTF-8 / 3 条错型与边界 LOW / provenance receipt。5 条新反例实测全过；第四次全量重跑数字仍不变 | 报告 §7e + `grep-selfattest.txt` |
43-| Codex 复审 round-5 | **仍阻断**（3/8 CLOSED；2 BLOCKER + 2 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round5.md` |
44:| round-5 findings 逐条整改 | **9/9 完成**：先扫描后判定（冲突候选亦入保护集）/ QA DB fd 身份+复核 / 可见性优先于 anomaly / fchmod 后置于碰撞检查 / QA DB 特殊文件门 / no_token 归 unverifiable / 3 条 LOW。6 条新反例实测全过；第五次全量重跑数字仍不变 | 报告 §7f |
45:| 独立 Workflow 4-agent 复核 | G4-9 数字 agent：92 条重算 **0 mismatch**（class/inline/三态/25 request_id/7 transcript 在盘/台账 sha 全 CONFIRMED，仅 2 处描述区间 REFUTED 已修正）；只读契约 agent：与 Codex 同源的 3 条 blocker（已随上整改） | Workflow wf_737b1a95-20b journal |
46-
47-## 🔧 Codex round-1 整改记录（13/13 关闭，BLOCKED → 整改完毕）
48-
49-- **BLOCKER-1 --out 截断风险**：任意 --out 路径 "w" 无守卫，可覆盖 DLQ 自身（双审查独立实测复现）。整改：写前 resolve() 路径碰撞守卫，命中输入集合即 exit 2；负例实测拒绝、DLQ 完好。
50-- **BLOCKER-2 快照不原子**：records 与头部 sha 来自两次读取。整改：单次 read_bytes()，头部与逐条同源同字节。
51-- **BLOCKER-3 交付物漂移**：审查期间脚本/报告 sha 变化且未 track。整改：本卡 commit 冻结全部 exact bytes；自证文件内嵌脚本 sha 前缀。
52:- **HIGH-1 inline 判定 fail-open**：sha 匹配但长度不符会误判 full_verified（反例实测）。整改：长度精确匹配门 + 64-hex 合法性门 + anomaly 一律 fail-closed（unrecoverable + 如实 basis）。
53-- **HIGH-2 request_id 归因传染**：缺失值合入 "None" 组、跨类型合组、多 token 静默取长。整改：(类型,值) 复合键 + 缺失单条成组 + 前缀一致门（冲突拒采信）。
54:- **HIGH-3 transcript 归因折叠**：多命中照单全收、目录缺失误判 unrecoverable=88（实测复现）。整改：恰 1 常规文件命中门 + 递归 glob + 目录缺失 exit 2 拒诊。
55-- **MEDIUM-1~3**：episode_body_full 采信通路 / duplicate_clusters 6 簇 29 行 + reference_time 透传 / privacy 字段与 private-only 声明。
56-- **LOW-1~4**：两处区间修正（16948–20831、205–8036）/ 稳定键语义重写为"冻结快照 occurrence key" / schema 双处证据（LearningConcept.name + LearningTip.created_at）/ 挂载历史证据边界声明。
57-
58:整改后全量重跑：92 条数字与整改前**逐项一致**（4/88/0、89/2/1、冲突 0、unparseable 0）——整改只收紧契约与通用鲁棒性，不改变本次 census 结论。
59-
60-## 🔧 Codex round-2 复审整改记录（10/13 CLOSED → 剩 3 项 + 3 新 LOW 全关闭）
61-
--
66-- **HIGH-3 未闭合**：`chmod 000` 的目录仍 exit 0 并把全部记录**假判不可恢复**；symlink 可指到目录外冒充源。→ 不可读即 exit 2；symlink 与逃逸目标一律不采信；正例（真实唯一命中）无回归。
67-- **3 新 LOW**：full_verified 长度范围修正 131–180；台账三个 distribution 补零并新增 `inline_state_distribution`；`line_count` 与 records 改用同一 `splitlines()` 口径。
68-
69:round-2 整改后再次全量重跑：92 条、4/88/0、89/2/1、6 簇 29 行、shasum 不变——**数字全程未变**。
70-
71-## 🔧 Codex round-3 复审整改记录（4/6 CLOSED → 剩 2 项 + 3 新发现全关闭）
72-
73-round-3 确认 HIGH-1 与三条 LOW 真正闭合、台账数字有效，又在两项路径安全上找到更深的绕过：
74-
75:- **BLOCKER-1 仍 PARTIAL**：① 保护集漏了**归因到的 transcript**——`--out` 指向它会截断恢复源；② check-then-open 的 **TOCTOU** 仍在。→ ① transcript 写前并入保护集；② 改 `O_NOFOLLOW` 打开且**不带 O_TRUNC**，对实际 fd `fstat` 校验后才 `ftruncate`。反例实测：exit 2、transcript 完好。
76-- **HIGH-3 仍 PARTIAL**：Python 3.14 的 `glob` 在过滤前就已递归、跟随目录 symlink 且**静默吞掉不可读子树错误**；mode 000 的文件仍过 `isfile()` 被当可用源。→ 改 `os.walk(onerror=, followlinks=False)` + `os.access(R_OK)` 门；遍历受阻或有不可读候选一律拒绝裁定。三反例实测 fail-closed。
77-- **新 MEDIUM（JSONL 分帧）**：`splitlines()` 会把含 U+2028 的合法单行记录劈成两条坏行。→ 严格按 LF 分帧，header 与 records 共用同一函数。
78-- **新 LOW ×2**：非 dict JSON（`null`/数组）归 unparseable 不再炸全量；报告头补 artifact commit 链。
79-
80:round-3 整改后第三次全量重跑：**92 条、4/88/0、89/2/1、6/29、shasum 不变——三轮整改数字全程未变**，改的全是通用鲁棒性与路径安全。
81-
82-## 🔧 Codex round-4 复审整改记录（1/6 CLOSED → 9 项全关闭）
83-
84-round-4 只认 1 项闭合，用更深的反例推翻其余"闭合"——两条新 BLOCKER 都是真的：
85-
86:- **不可读但可写（mode 0200）的 transcript 绕过保护集**：我在"不可读"分支把候选路径清空了，于是它没进保护集，`--out` 指向它照样截断——不需要任何竞态。→ 新增"全候选清单"，无论可读与否一律并入保护集。
87-- **源侧 TOCTOU**：保护身份按路径 stat 采集、DLQ 稍后才按路径读取，中间可换 inode。→ 改为**从 fd 读取**：打开一次 → `fstat` 取身份 → 从同一 fd 读全量，保护的就是实际读到的那个对象。
88:- **把"看不见"说成"不可恢复"**：扫描受阻时仍输出 `unrecoverable`，与报告里"既不宣称不可恢复"自相矛盾。→ 新增第四态 **`unverifiable`**，逐条写明是遍历受阻还是候选不可读。
89-- **其余 5 项**：FIFO/设备节点门（`O_NONBLOCK`+`S_ISREG`）、非法 UTF-8 不再经 replace 冒充有效记录（strict decode）、三条错型与边界 LOW（`name=None`/`request_id=[]`/根为 `/`）、既有输出文件 `fchmod` 收紧（台账现为 `-rw-------`）、provenance 改后置 receipt 绑定精确 commit 链。
90-
91:round-4 整改后第四次全量重跑：**92 条、4/88/0（unverifiable 0）、89/2/1、6/29、shasum 不变——四轮整改数字全程未变**。
92-
93-## 🔧 Codex round-5 复审整改记录（3/8 CLOSED → 9 项全关闭）
94-
95-round-5 继续深挖，两条新 BLOCKER 与两条 HIGH 都成立：
96-
97-- **冲突组的候选没进保护集**：token 冲突时我在扫描**之前**就早退了，那些候选从没被看到，`--out` 指向它们照样截断。→ 改成**先扫描后判定**，无论最终是否采信，见到的候选一律进保护集。
98:- **qa_metrics.db 身份没绑定实际读取**：先按路径 stat、SQLite 稍后按路径重开，中间可换。→ 改 fd 取身份 + 打开后复核身份一致。
99:- **anomaly 吞掉了"看不见"**：`anomaly→unrecoverable` 排在可见性判断之前，扫描受阻时仍断言"不可恢复"。→ 判定链改为**可见性优先**。
100:- **`fchmod` 排在碰撞检查之前**：`--out` 指向受保护的只读输入时，会先把它的权限从 644 改成 600 才发现碰撞——字节没丢但输入被改了。→ 碰撞检查前移。
101:- **其余 5 项**：QA DB 特殊文件门、无 token 归 `unverifiable`、单独换行算 1 空行、strict encode 堵住 lone surrogate 伪造 `full_verified`、`bool` 不再通过长度门。
102-
103:**一处计数如实变化**：归因冲突 0→3。因为"名字不含 session token"现在被诚实标为"未做归因扫描"，正是那 3 条 callout 记录；它们 inline 全量、不依赖 transcript，仍是可字节级恢复。**三态分布不变**（4/88/0/0）——是标注变诚实，不是结论变化。
104-
105:round-5 整改后第五次全量重跑：**92 条、4/88/0/0、89/2/1、6/29、shasum 不变——五轮整改数字全程未变**。
106-
107-## 📄 交付物清单（全部新增，零业务代码改动）
108-
109:- `backend/scripts/census_dead_letter_episodes.py` — 唯一代码产物（只读 census 脚本，纯 stdlib）
110-- `_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md` — census 报告（挂载真相/分类/三态/交接契约）
111:- `_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json` — 92 条逐条台账（G4-10 消费）
112-- `_bmad-output/审查/G4-9-evidence/` — 证据包（shasums ×2、grep 自证、容器 sha 实测、运行日志）
113-- `_bmad-output/审查/codex-review-CARD-G4-9.md` — Codex 独立审查存档
114-
115-## ⏭️ 移交（不在本卡范围）
116-
117:- **G4-10**：89 条 budget_400 根因修复（16384 context 超限 → 切块或提 budget）+ 按台账重放；3 条 `vault:default` 旧格式重放前需 group 重映射。
118-- **DeadLetterStore 全量正文开关**：`DEAD_LETTER_STORE_FULL_BODY` live 未启用是 88 条只剩前缀的直接原因——是否开启（隐私 vs 可恢复性权衡）留 G4-10 连根因一并裁。

exec
/bin/zsh -lc 'find _bmad-output/审查/G4-9-evidence -maxdepth 2 -type f -print | sort' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt
_bmad-output/审查/G4-9-evidence/census-stderr.txt
_bmad-output/审查/G4-9-evidence/container-sha-check.txt
_bmad-output/审查/G4-9-evidence/grep-selfattest.txt
_bmad-output/审查/G4-9-evidence/shasums-after.txt
_bmad-output/审查/G4-9-evidence/shasums-before.txt

exec
/bin/zsh -lc "jq '[.records[] | select(.attribution_conflict==true) | {stable_key,name,inline_state,sha_check,session_token,transcript_match_count,recoverability,recoverability_basis}]' _bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
[
  {
    "stable_key": {
      "line_no": 1,
      "sha256_prefix": "7e33da5e96e6239f",
      "request_id": "281466113679440"
    },
    "name": "callout_annotation:P0 final 验证",
    "inline_state": "full_verified",
    "sha_check": "pass",
    "session_token": null,
    "transcript_match_count": 0,
    "recoverability": "byte_exact",
    "recoverability_basis": "inline 正文全量：sha256 重算与声明一致且长度精确匹配"
  },
  {
    "stable_key": {
      "line_no": 2,
      "sha256_prefix": "b91bf262cadab596",
      "request_id": "281466014769488"
    },
    "name": "callout_annotation:递归 base case 概念",
    "inline_state": "full_verified",
    "sha_check": "pass",
    "session_token": null,
    "transcript_match_count": 0,
    "recoverability": "byte_exact",
    "recoverability_basis": "inline 正文全量：sha256 重算与声明一致且长度精确匹配"
  },
  {
    "stable_key": {
      "line_no": 3,
      "sha256_prefix": "55b1b793b99778eb",
      "request_id": "281466427090256"
    },
    "name": "callout_annotation:递归 base case",
    "inline_state": "full_verified",
    "sha_check": "pass",
    "session_token": null,
    "transcript_match_count": 0,
    "recoverability": "byte_exact",
    "recoverability_basis": "inline 正文全量：sha256 重算与声明一致且长度精确匹配"
  }
]

**Identifying internal attribution conflict discrepancy**
**Assessing sandbox access for live DLQ recalculation**
**Testing metadata access for ledger recompute**
**Planning source inspection using shell and jq**
**Analyzing artifact timestamp and diff for ledger**
**Validating artifact provenance and commit chain**
exec
/bin/zsh -lc 'nl -ba _bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
exec
/bin/zsh -lc 'git diff --no-ext-diff --unified=5 4c125f19''^ 4c125f19 -- _bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
     1	== CARD-G4-9 / CARD-G4-16 artifact commit receipt ==
     2	（commit 无法自含己身 SHA，故用本后置 receipt 精确绑定 —— Codex round-4 LOW 整改）
     3	
     4	37387a86  第五批开工基线（分析对象锚定 SHA，非本卡产物）
     5	67ccebe1  CARD-G4-9 初版交付（脚本/报告/台账/证据包/round-1 审查/UAT）
     6	e7a480eb  CARD-G4-16 初版交付（报告/证据包/两处注释修正/审查/UAT）
     7	73102875  round-2 findings 整改（两卡）
     8	fce0d8a2  round-3 findings 整改（两卡）
     9	94b420ff  CARD-G4-16 round-4 整改（重放 recipe 确定化）
    10	d2827a6d  CARD-G4-9 round-4 整改（本 receipt 所描述的 commit）
    11	
    12	各阶段交付物 blob 可用 git cat-file 复核；台账头部 dlq_file.sha256 为 DLQ 快照指纹。

 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
diff --git "a/_bmad-output/\351\252\214\346\224\266\345\215\225/UAT-CARD-G4-9-DLQ\347\234\237\345\256\236\346\214\202\350\275\275census\345\210\206\350\257\212-2026-08-28.md" "b/_bmad-output/\351\252\214\346\224\266\345\215\225/UAT-CARD-G4-9-DLQ\347\234\237\345\256\236\346\214\202\350\275\275census\345\210\206\350\257\212-2026-08-28.md"
index aa6c9392..4a182918 100644
--- "a/_bmad-output/\351\252\214\346\224\266\345\215\225/UAT-CARD-G4-9-DLQ\347\234\237\345\256\236\346\214\202\350\275\275census\345\210\206\350\257\212-2026-08-28.md"
+++ "b/_bmad-output/\351\252\214\346\224\266\345\215\225/UAT-CARD-G4-9-DLQ\347\234\237\345\256\236\346\214\202\350\275\275census\345\210\206\350\257\212-2026-08-28.md"
@@ -38,10 +38,12 @@ worktree: "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktre
 | round-2 findings 逐条整改 | **6/6 完成**：inode 身份守卫封 hardlink+大小写别名 / full_body 长度门+anomaly 前置 / 不可读根 exit 2+symlink 逃逸拒采信 / 3 新 LOW。5 条新负例实测全过、正例无回归、数字仍逐项一致 | 报告 §7/§7c + `grep-selfattest.txt` |
 | Codex 复审 round-3 | **仍阻断**（4/6 CLOSED；BLOCKER-1/HIGH-3 判 PARTIAL + 1 新 MEDIUM + 2 新 LOW）。同时确认：HIGH-1 与三条 LOW 已闭合、台账数字有效且与 commit 字节一致 | `_bmad-output/审查/codex-review-CARD-G4-9-round3.md` |
 | round-3 findings 逐条整改 | **6/6 完成**：transcript 并入保护集 / O_NOFOLLOW+fstat 消 TOCTOU / os.walk 替 glob（不跟随目录 symlink+遍历错误显式捕获）/ 不可读候选 fail-closed / JSONL 严格 LF 分帧 / 非 dict 归 unparseable。6 条新反例实测全过、数字第三次不变 | 报告 §7d + `grep-selfattest.txt` |
 | Codex 复审 round-4 | **仍阻断**（1/6 CLOSED；2 新 BLOCKER + 1 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round4.md` |
 | round-4 findings 逐条整改 | **9/9 完成**：全候选入保护集 / 读侧 fd 身份消源侧 TOCTOU / 新增 unverifiable 第四态 / FIFO 设备门 / strict UTF-8 / 3 条错型与边界 LOW / provenance receipt。5 条新反例实测全过；第四次全量重跑数字仍不变 | 报告 §7e + `grep-selfattest.txt` |
+| Codex 复审 round-5 | **仍阻断**（3/8 CLOSED；2 BLOCKER + 2 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round5.md` |
+| round-5 findings 逐条整改 | **9/9 完成**：先扫描后判定（冲突候选亦入保护集）/ QA DB fd 身份+复核 / 可见性优先于 anomaly / fchmod 后置于碰撞检查 / QA DB 特殊文件门 / no_token 归 unverifiable / 3 条 LOW。6 条新反例实测全过；第五次全量重跑数字仍不变 | 报告 §7f |
 | 独立 Workflow 4-agent 复核 | G4-9 数字 agent：92 条重算 **0 mismatch**（class/inline/三态/25 request_id/7 transcript 在盘/台账 sha 全 CONFIRMED，仅 2 处描述区间 REFUTED 已修正）；只读契约 agent：与 Codex 同源的 3 条 blocker（已随上整改） | Workflow wf_737b1a95-20b journal |
 
 ## 🔧 Codex round-1 整改记录（13/13 关闭，BLOCKED → 整改完毕）
 
 - **BLOCKER-1 --out 截断风险**：任意 --out 路径 "w" 无守卫，可覆盖 DLQ 自身（双审查独立实测复现）。整改：写前 resolve() 路径碰撞守卫，命中输入集合即 exit 2；负例实测拒绝、DLQ 完好。
@@ -86,10 +88,24 @@ round-4 只认 1 项闭合，用更深的反例推翻其余"闭合"——两条
 - **把"看不见"说成"不可恢复"**：扫描受阻时仍输出 `unrecoverable`，与报告里"既不宣称不可恢复"自相矛盾。→ 新增第四态 **`unverifiable`**，逐条写明是遍历受阻还是候选不可读。
 - **其余 5 项**：FIFO/设备节点门（`O_NONBLOCK`+`S_ISREG`）、非法 UTF-8 不再经 replace 冒充有效记录（strict decode）、三条错型与边界 LOW（`name=None`/`request_id=[]`/根为 `/`）、既有输出文件 `fchmod` 收紧（台账现为 `-rw-------`）、provenance 改后置 receipt 绑定精确 commit 链。
 
 round-4 整改后第四次全量重跑：**92 条、4/88/0（unverifiable 0）、89/2/1、6/29、shasum 不变——四轮整改数字全程未变**。
 
+## 🔧 Codex round-5 复审整改记录（3/8 CLOSED → 9 项全关闭）
+
+round-5 继续深挖，两条新 BLOCKER 与两条 HIGH 都成立：
+
+- **冲突组的候选没进保护集**：token 冲突时我在扫描**之前**就早退了，那些候选从没被看到，`--out` 指向它们照样截断。→ 改成**先扫描后判定**，无论最终是否采信，见到的候选一律进保护集。
+- **qa_metrics.db 身份没绑定实际读取**：先按路径 stat、SQLite 稍后按路径重开，中间可换。→ 改 fd 取身份 + 打开后复核身份一致。
+- **anomaly 吞掉了"看不见"**：`anomaly→unrecoverable` 排在可见性判断之前，扫描受阻时仍断言"不可恢复"。→ 判定链改为**可见性优先**。
+- **`fchmod` 排在碰撞检查之前**：`--out` 指向受保护的只读输入时，会先把它的权限从 644 改成 600 才发现碰撞——字节没丢但输入被改了。→ 碰撞检查前移。
+- **其余 5 项**：QA DB 特殊文件门、无 token 归 `unverifiable`、单独换行算 1 空行、strict encode 堵住 lone surrogate 伪造 `full_verified`、`bool` 不再通过长度门。
+
+**一处计数如实变化**：归因冲突 0→3。因为"名字不含 session token"现在被诚实标为"未做归因扫描"，正是那 3 条 callout 记录；它们 inline 全量、不依赖 transcript，仍是可字节级恢复。**三态分布不变**（4/88/0/0）——是标注变诚实，不是结论变化。
+
+round-5 整改后第五次全量重跑：**92 条、4/88/0/0、89/2/1、6/29、shasum 不变——五轮整改数字全程未变**。
+
 ## 📄 交付物清单（全部新增，零业务代码改动）
 
 - `backend/scripts/census_dead_letter_episodes.py` — 唯一代码产物（只读 census 脚本，纯 stdlib）
 - `_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md` — census 报告（挂载真相/分类/三态/交接契约）
 - `_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json` — 92 条逐条台账（G4-10 消费）

exec
/bin/zsh -lc 'git diff --no-ext-diff --unified=5 4c125f19''^ 4c125f19 -- _bmad-output/审查/G4-9-DLQ-census-2026-08-28.md' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
diff --git "a/_bmad-output/\345\256\241\346\237\245/G4-9-DLQ-census-2026-08-28.md" "b/_bmad-output/\345\256\241\346\237\245/G4-9-DLQ-census-2026-08-28.md"
index 2df3b06b..465e63b6 100644
--- "a/_bmad-output/\345\256\241\346\237\245/G4-9-DLQ-census-2026-08-28.md"
+++ "b/_bmad-output/\345\256\241\346\237\245/G4-9-DLQ-census-2026-08-28.md"
@@ -159,5 +159,21 @@ round-4 只认可 1 项 CLOSED（非 dict JSON 门），并用更深的静态反
 - **MEDIUM（非法 UTF-8 冒充有效记录）**：`errors="replace"` 把坏字节改写成合法对象。**整改**：`_split_jsonl_lines()` 改**逐行 strict decode**，解码失败归 `unparseable`。实测：`b'{"a":"\xff"}'` → `utf8_decode_error`，records=0。
 - **LOW ×3**：dict 内字段错型防御（`name=None` / `request_id=[]` 不可哈希 / `episode_body` 非 str 均不再炸全量，按 line_no 单条成组或判 anomaly）；`transcripts_dir="/"` 的 `//` containment 特例；`0o600` 对**既有**输出文件用 `fchmod` 显式收紧（实测台账 mode 现为 `-rw-------`）。
 - **LOW（provenance 自指）**：commit 无法自含己身 SHA，改用后置 `artifact-commit-receipt.txt` 绑定精确链，报告头指向该 receipt。
 
 round-4 整改后第四次全量重跑：**92 条、class 89/2/1、三态 4/88/0（unverifiable 0）、重复簇 6/29、shasum 不变——四轮整改数字全程未变**。
+
+## §7f Codex round-5 复审整改记录（3/8 CLOSED → 9 项全部整改）
+
+round-5 用更深的静态反例继续推翻"闭合"，提出 2 BLOCKER / 2 HIGH / 2 MEDIUM / 3 LOW，逐条整改并实测：
+
+- **BLOCKER①（token 冲突/无 token 时扫描前早退 → 候选不进保护集）**：`--out` 指向冲突组的候选 transcript 仍可无竞态截断。**整改**：`resolve_group_attribution()` 重写为**先扫描后判定**——无条件为每个 token 扫描收集候选进 `all_candidate_paths`（保护集口径），再做冲突/唯一性判定；候选 `stat` 失败不再 `continue` 吞掉而是 exit 2（保护集不完整即拒绝写出）。实测：冲突候选作 `--out` → exit 2、文件 sha 不变。
+- **BLOCKER②（qa_metrics.db 身份未绑定实际读取）**：仍是早期 path-stat + SQLite 稍后按路径重开。**整改**：`probe_qa_metrics()` 改 `os.open(O_RDONLY|O_NOFOLLOW|O_NONBLOCK)` 取 fstat 身份 + `S_ISREG` 门 → SQLite 打开后**复核路径身份仍等于该身份**，不等即 `identity_changed_..._refused`；身份入保护集。本次运行 `file_identity_verified: true`。
+- **HIGH①（anomaly 吞掉不可见性）**：`anomaly→unrecoverable` 排在 conflict 判断之前，`anomaly + 扫描受阻` 仍被假终态化。**整改**：判定链改为**可见性优先**——归因不可核验时无论 inline 状态一律 `unverifiable`，basis 逐条写明原因（无 token / token 冲突 / 扫描受阻 / 候选 stat 失败 / 不可读候选 / 多命中 ambiguous），并附注 inline 是否也 anomaly。实测：anomaly+不可读子树 → `unverifiable`。
+- **HIGH②（`fchmod` 先于 protected-id 检查）**：`--out` 指向受保护的 0644 输入时，会**先把只读输入权限改成 0600** 再拒绝——字节没截断但输入已被修改。**整改**：碰撞检查前移到 `fchmod` 之前。实测：mode 644 → 644 不变。
+- **MEDIUM（QA DB 无特殊文件门）**：随 BLOCKER② 一并加 `S_ISREG` + `O_NONBLOCK`。
+- **MEDIUM（无 token 未扫描即判不可恢复）**：改为 `unverifiable` + `no_token` 标记（见 HIGH①）。
+- **LOW ×3**：单独 `b"\n"` 现算 1 个空行（实测 `line_count=1`）；`errors="replace"` 改 **strict encode**（JSON escaped lone surrogate 不能再构造假 `full_verified`）；`bool` 是 `int` 子类 —— `episode_body_length=True` 现被长度门拒绝（实测判 anomaly）。
+
+**归因冲突计数由 0 变为 3（如实说明）**：round-5 起"名字不含 session token"被诚实标记为 `no_token`（未做归因扫描），命中的正是 3 条 `callout_annotation` 记录。它们 inline 正文全量、sha 对账通过，**不依赖 transcript**，故仍判 `byte_exact`——三态分布不变（4/88/0/0），88 条 approximate 仍全部为唯一 transcript 命中。这是标注口径变诚实，不是结论变化。
+
+round-5 整改后第五次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变——五轮整改数字全程未变**。

exec
/bin/zsh -lc 'nl -ba _bmad-output/审查/G4-9-evidence/shasums-before.txt && nl -ba _bmad-output/审查/G4-9-evidence/shasums-after.txt' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
     1	3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl
     2	490c903b2f3636e1d2c4ecb68465cef41ace06f0bd171eb2fb95c03a7b40cb43  /Users/Heishing/Desktop/canvas/canvas-learning-system/backend/data/dead_letter_episodes.jsonl
     3	bfb3f6c413aab7dd4c04a25f7575aaaffcfc92fd4e8e8966362609652ac7e310  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/data/dead_letter_episodes.jsonl
     4	75c5f7593b9b2e99672d0551487b4476552ebd8d33ad25c5f9479683cc61e9c9  /Users/Heishing/Desktop/canvas/canvas-learning-system/data/dead_letter_episodes.jsonl
     5	6cb5510dc91cf1c29c7ce6510013238cf83b5eae6305180e6aa9320a957a6a05  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db
     1	3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl
     2	490c903b2f3636e1d2c4ecb68465cef41ace06f0bd171eb2fb95c03a7b40cb43  /Users/Heishing/Desktop/canvas/canvas-learning-system/backend/data/dead_letter_episodes.jsonl
     3	bfb3f6c413aab7dd4c04a25f7575aaaffcfc92fd4e8e8966362609652ac7e310  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/data/dead_letter_episodes.jsonl
     4	75c5f7593b9b2e99672d0551487b4476552ebd8d33ad25c5f9479683cc61e9c9  /Users/Heishing/Desktop/canvas/canvas-learning-system/data/dead_letter_episodes.jsonl
     5	6cb5510dc91cf1c29c7ce6510013238cf83b5eae6305180e6aa9320a957a6a05  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db

exec
/bin/zsh -lc "git diff --no-ext-diff --name-status 4c125f19 -- . ':(exclude)_bmad-output/审查/codex-review-CARD-G4-9-round6.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead

exec
/bin/zsh -lc 'git diff --no-ext-diff --unified=5 4c125f19''^ 4c125f19 -- _bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
diff --git "a/_bmad-output/\345\256\241\346\237\245/G4-9-dlq-ledger-2026-08-28.json" "b/_bmad-output/\345\256\241\346\237\245/G4-9-dlq-ledger-2026-08-28.json"
index ec0e2b7a..d29df0a7 100644
--- "a/_bmad-output/\345\256\241\346\237\245/G4-9-dlq-ledger-2026-08-28.json"
+++ "b/_bmad-output/\345\256\241\346\237\245/G4-9-dlq-ledger-2026-08-28.json"
@@ -1,8 +1,8 @@
 {
  "card": "CARD-G4-9",
- "generated_at": "2026-08-28T11:53:47.688306+00:00",
+ "generated_at": "2026-08-28T12:23:16.503247+00:00",
  "privacy": "private-only: transcript_paths 含本机用户名与 session UUID，禁止外发/公网发布",
  "stable_key_semantics": "冻结快照（dlq_file.sha256）内的 occurrence key；line_no 在快照内唯一，sha256_prefix/request_id 为冗余对账维度——非跨文件重排或语义幂等键",
  "dlq_file": {
   "path": "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl",
   "exists": true,
@@ -63,11 +63,27 @@
   "truncated_prefix": 88,
   "anomaly": 0
  },
  "unrecoverable_list": [],
  "unverifiable_list": [],
- "attribution_conflicts": [],
+ "attribution_conflicts": [
+  {
+   "line_no": 1,
+   "sha256_prefix": "7e33da5e96e6239f",
+   "request_id": "281466113679440"
+  },
+  {
+   "line_no": 2,
+   "sha256_prefix": "b91bf262cadab596",
+   "request_id": "281466014769488"
+  },
+  {
+   "line_no": 3,
+   "sha256_prefix": "55b1b793b99778eb",
+   "request_id": "281466427090256"
+  }
+ ],
  "duplicate_clusters": [
   {
    "name": "session-archive:426ffbde-15f6-4b",
    "episode_body_sha256": "c93058c9850c6999310e98df9e6ebc26063b96fa6f0649fb1ec6d9d04c88a7fe",
    "group_id": "vault:canvas_vault",
@@ -146,10 +162,11 @@
   }
  ],
  "qa_metrics_probe": {
   "db_path": "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db",
   "opened_readonly": true,
+  "file_identity_verified": true,
   "tables": [
    "qa_error_logs"
   ],
   "qa_error_logs_rows": 0,
   "error_type_hits": {
@@ -179,11 +196,11 @@
    "inline_state": "full_verified",
    "sha_check": "pass",
    "session_token": null,
    "transcript_paths": [],
    "transcript_match_count": 0,
-   "attribution_conflict": false,
+   "attribution_conflict": true,
    "recoverability": "byte_exact",
    "recoverability_basis": "inline 正文全量：sha256 重算与声明一致且长度精确匹配"
   },
   {
    "stable_key": {
@@ -204,11 +221,11 @@
    "inline_state": "full_verified",
    "sha_check": "pass",
    "session_token": null,
    "transcript_paths": [],
    "transcript_match_count": 0,
-   "attribution_conflict": false,
+   "attribution_conflict": true,
    "recoverability": "byte_exact",
    "recoverability_basis": "inline 正文全量：sha256 重算与声明一致且长度精确匹配"
   },
   {
    "stable_key": {
@@ -229,11 +246,11 @@
    "inline_state": "full_verified",
    "sha_check": "pass",
    "session_token": null,
    "transcript_paths": [],
    "transcript_match_count": 0,
-   "attribution_conflict": false,
+   "attribution_conflict": true,
    "recoverability": "byte_exact",
    "recoverability_basis": "inline 正文全量：sha256 重算与声明一致且长度精确匹配"
   },
   {
    "stable_key": {

**Inspecting commit ancestry for provenance issue**
exec
/bin/zsh -lc 'git log --oneline --decorate --reverse d2827a6d..4c125f19' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
d8d887f2 docs(census): 补 artifact commit receipt 绑定精确 SHA 链 [BATCH-2026-08-28-第五批 / CARD-G4-9]
4c125f19 (HEAD -> card/s5-census) fix(census): G4-9 Codex round-5 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9]

**Checking commit d8d diff for receipt addition**
exec
/bin/zsh -lc 'git show --stat --oneline d8d887f2 && git show --no-ext-diff --format= -- _bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt d8d887f2' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
d8d887f2 docs(census): 补 artifact commit receipt 绑定精确 SHA 链 [BATCH-2026-08-28-第五批 / CARD-G4-9]
 .../G4-9-evidence/artifact-commit-receipt.txt"               | 12 ++++++++++++
 1 file changed, 12 insertions(+)
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead

**Identifying stale receipt and provenance concerns**
exec
/bin/zsh -lc "nl -ba _bmad-output/审查/G4-9-evidence/grep-selfattest.txt | sed -n '1,140p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
     1	== CARD-G4-9 只读自证（round-4 整改版, f27531b8a50f035d…） ==
     2	--- (1) 全部 import 行（应只有 stdlib）:
     3	52:from __future__ import annotations
     4	54:import argparse
     5	55:import hashlib
     6	56:import json
     7	57:import os
     8	58:import re
     9	59:import sqlite3
    10	60:import stat
    11	61:import sys
    12	62:from collections import Counter, defaultdict
    13	63:from datetime import datetime, timezone
    14	64:from pathlib import Path
    15	--- (2) neo4j/graphiti/bolt/app. 在 import 行的命中（应 0）:
    16	0
    17	0 ✓
    18	--- (3) --apply 定义（应 0）:
    19	0
    20	0 ✓
    21	--- (4) 唯一写出口 + 其安全门（O_NOFOLLOW/O_NONBLOCK → fstat → S_ISREG → inode 校验 → fchmod → ftruncate）:
    22	272:        if not stat.S_ISREG(st.st_mode):
    23	620:            fd = os.open(args.out, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    24	627:            if not stat.S_ISREG(st.st_mode):
    25	632:                os.fchmod(fd, 0o600)
    26	639:            os.ftruncate(fd, 0)
    27	640:            with os.fdopen(fd, "w", encoding="utf-8", closefd=True) as f:
    28	--- (5) 读侧同门（实际读取对象身份入保护集）:
    29	269:    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    30	274:        identity = (st.st_dev, st.st_ino)
    31	365:                protected_ids.add((cst.st_dev, cst.st_ino))
    32	394:    protected_ids.add(dlq_identity)  # 保护的是**实际读取对象**，非路径快照
    33	547:            protected_ids.add(cid)
    34	603:                protected_ids.add((tst.st_dev, tst.st_ino))
    35	610:                protected_ids.add((tst.st_dev, tst.st_ino))
    36	--- (6) fail-closed 判定门:
    37	94:            out.append(("", f"utf8_decode_error: {e}"))
    38	181:    walk_errors: list[str] = []
    39	184:        walk_errors.append(f"{getattr(err, 'filename', '?')}: {err}")
    40	187:    unreadable: list[str] = []
    41	194:            if os.path.islink(candidate) or not os.path.isfile(candidate):
    42	197:            # 不是可用恢复源，计入 unreadable 而非命中（fail-closed）。
    43	199:            if not os.access(candidate, os.R_OK):
    44	200:                unreadable.append(candidate)
    45	210:    if unreadable:
    46	212:        result["unreadable_candidates"] = unreadable[:5]
    47	217:    if walk_errors:
    48	219:        result["scan_errors"] = walk_errors[:5]

**Identifying stale evidence and hash mismatches**
**Classifying risk as medium due to stale evidence**
exec
/bin/zsh -lc 'nl -ba _bmad-output/审查/G4-9-evidence/census-stderr.txt && shasum -a 256 backend/scripts/census_dead_letter_episodes.py _bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json _bmad-output/审查/G4-9-evidence/grep-selfattest.txt' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
     1	census: 92 条 (+0 unparseable) | class={'schema_entity_type': 2, 'group_id_format': 1, 'budget_400': 89} | recoverability={'byte_exact': 4, 'approximate': 88} | 归因冲突=3 | 重复簇=6 | 偏差=无 | qa_metrics 核销=no_source_rows
cc2ff9662dbf52d34049e4cf1af934ee1118adf6d3d2467a129294949c69e7be  backend/scripts/census_dead_letter_episodes.py
33705008b7121022f2e876e74d5acde2fcdd983dbb7c1e1749adf82f24287b4e  _bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json
8fc715f585f827c25771b039e20d2865175803bb9c55d08bdd55412c0052c6b5  _bmad-output/审查/G4-9-evidence/grep-selfattest.txt

**Planning read-only function testing**
**Enforcing no file writes policy**
**Planning in-memory Python execution without cache**
exec
/bin/zsh -lc "wc -l -c '/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl' '/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
      92   99915 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl
       8   16384 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db
     100  116299 total

exec
/bin/zsh -lc "shasum -a 256 '/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl' '/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl
6cb5510dc91cf1c29c7ce6510013238cf83b5eae6305180e6aa9320a957a6a05  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db

exec
/bin/zsh -lc "stat -f '%N dev=%d inode=%i mode=%Sp size=%z' '/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl' '/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl dev=16777230 inode=11179623 mode=-rw-r--r-- size=99915
/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db dev=16777230 inode=18698919 mode=-rw-r--r-- size=16384

**Analyzing SQLite URI path parsing**
**Assessing SQLite connection race conditions**
**Assessing SQLite URI query race conditions**
**Identifying deterministic blocker in URI parsing**
**Assessing SQLite read-only WAL sidecar handling**
exec
/bin/zsh -lc "find /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data -maxdepth 1 -name 'qa_metrics.db*' -exec stat -f '%N dev=%d inode=%i mode=%Sp size=%z' {} \\;" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db dev=16777230 inode=18698919 mode=-rw-r--r-- size=16384

**Analyzing newline semantics in _split_jsonl_lines**
**Verifying type checks and encoding anomalies**
**Planning SQLite URI parser testing**
**Assessing directory execute-only permissions on macOS**
**Identifying directory symlink traversal vulnerability**
**Confirming hidden candidate exclusion despite symlink protection**
**Identifying SQLite readonly mode parsing flaw**
**Confirming SQLite URI fragment handling flaw**
**Noting new lone surrogate crash risk**
2026-08-28T12:35:27.592180Z ERROR codex_core::tools::router: error=timeout_ms must be at least 10000
**Inspecting Context7 tool**
**Planning official docs browsing**
codex
第二条 QA 风险已经收束成无需竞态的静态反例：`file:{db_path}?mode=ro` 没有 URI 转义，合法文件名中的 `?`/`#` 会让 SQLite 实际打开另一路径，甚至丢失 `mode=ro`。我会用 SQLite/Python 官方文档核对这一解析语义；这一步只读联网，不接触项目或私人数据。项目要求的 Context7 当前同样未提供。
web search: 
web search: https://sqlite.org/uri.html#the_uri_path
**Planning independent read-only version checks**
**Designing inline Python ledger analysis script**
**Validating ledger record counts without private data**
**Assessing transcript metadata access permissions**
**Verifying transcript match count via metadata**
**Reviewing round5 audit scope**
exec
/bin/zsh -lc "nl -ba _bmad-output/审查/codex-review-CARD-G4-9-round5.md | sed -n '3300,3420p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
  3300	**Planning episode_body_length testing**
  3301	exec
  3302	/bin/zsh -lc "python3 -B -c 'import importlib.util,hashlib,json; p=\"backend/scripts/census_dead_letter_episodes.py\"; s=importlib.util.spec_from_file_location(\"census_ro4\",p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); body=\"x\"; sha=hashlib.sha256(body.encode()).hexdigest(); print(json.dumps({\"bool_len\":m.inline_state({\"episode_body\":body,\"episode_body_length\":True,\"episode_body_sha256\":sha}),\"float_len\":m.inline_state({\"episode_body\":body,\"episode_body_length\":1.0,\"episode_body_sha256\":sha})}))'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
  3303	 succeeded in 0ms:
  3304	{"bool_len": ["full_verified", "pass"], "float_len": ["full_verified", "pass"]}
  3305	
  3306	**Assessing read-only database access risks**
  3307	codex
  3308	复算结果已经与提交台账逐字段对齐：live DLQ 仍是 `99,915 bytes / SHA-256 3b37460f…ba590`，92 个 LF 帧全部为 dict，分类、四态、重复簇均 0 mismatch。关键分离是：这份冻结 ledger 可采信，但生成器的“只读保护闭包”仍未成立。
  3309	exec
  3310	/bin/zsh -lc "git status --porcelain=v2 --branch && git diff --quiet HEAD -- backend/scripts/census_dead_letter_episodes.py '_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md' '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' '_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
  3311	 succeeded in 0ms:
  3312	git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
  3313	# branch.oid d8d887f29377b8babc49f5dda0d4c4ba01168ad3
  3314	# branch.head card/s5-census
  3315	? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round5.md"
  3316	git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
  3317	
  3318	mcp: sequential-thinking/sequentialthinking started
  3319	mcp: sequential-thinking/sequentialthinking (completed)
  3320	**Finishing update plan**
  3321	高危反例已由独立轨交叉确认，台账 exact-bytes 复算完成；终裁与分级已形成。
  3322	  ✓ 锁定 HEAD、提交链、工作树状态、CARD-G4-9 报告与生产入口
  3323	  ✓ 并行复核保护集、fd 快照、四态语义、解析/类型/输出/provenance
  3324	  ✓ 从原始材料独立复算 92 条台账与重复簇
  3325	  ✓ 交叉验证反例、分级新发现并给出逐项终裁
  3326	**Drafting Chinese final verdict with evidence table**
  3327	**Summarizing detailed verdicts with line references and statuses**
  3328	**Labeling anomaly semantics and scope**
  3329	**Finalizing verification boundaries and formatting**
  3330	**Confirming link formatting and citation status**
  3331	codex
  3332	总裁定：**仍阻断 / CARD-G4-9 不可验收**。  
  3333	但结论必须拆开：**冻结的 92 条 ledger 数字 PASS；通用生成器的只读安全闭包 FAIL。**
  3334	
  3335	### 逐项终裁
  3336	
  3337	| 整改项 | 裁定 | 静态反例与证据 |
  3338	|---|---|---|
  3339	| 1. transcript 全候选保护 | **NOT-CLOSED · BLOCKER** | 多 token 非前缀一致时在扫描前直接返回，[script:168](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:168)，此时 `all_candidate_paths=[]`。同一 `request_id` 含 `session:aaaaa`、`session:bbbbb`，`--out` 指向 `aaaaa….jsonl`，不会进入 [保护循环:599](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:599)，最终仍可在 [ftruncate:639](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:639)截断。无需竞态。不可列举但可穿越的子目录也有同类绕过；后置 transcript `stat` 失败仍被 `continue` 吞掉。 |
  3340	| 2. 源侧 fd 身份绑定 | **NOT-CLOSED / PARTIAL · BLOCKER** | DLQ/compare 的狭义修复已 CLOSED：同一 fd `open→fstat→read→identity`，[snapshot:262](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:262)、[DLQ:389](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:389)、[compare:542](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:542)。但 `qa_metrics_db` 仍是早期 path-stat、稍后 SQLite 按路径重新打开，[probe:233](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:233)。可令 stat 看到 inode A、SQLite 实际读取换入的 B、`--out` 为 B 的 hardlink，最终 B 不在保护集并被截断。 |
  3341	| 3. `unverifiable` 四态 | **NOT-CLOSED · HIGH** | distribution/list 同步已实现。但 `anomaly→unrecoverable` 位于 conflict 判断之前，[script:464](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:464)：`anomaly + 扫描受阻/不可读/归因冲突` 仍被假终态化。另无 token 时未扫描即返回，truncated 记录随后被称为“无在盘源”，也应是 `unverifiable`。 |
  3342	| 4. FIFO/设备门 | **NOT-CLOSED / PARTIAL · MEDIUM** | DLQ、compare、`--out` 的 `O_NONBLOCK + S_ISREG` 已 CLOSED，[读侧:269](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:269)、[写侧:620](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:620)。但 QA DB 读侧仍直接进入 SQLite，无 regular-file/nonblocking 门，FIFO 仍可能阻塞。 |
  3343	| 5. 非法 UTF-8 | **CLOSED（原项）** | 逐 LF frame strict decode，并在调用方归 `unparseable`，[splitter:77](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:77)、[caller:399](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:399)。只读验证坏字节得到 1 frame + decode error。 |
  3344	| 6a. 三个指定字段错型 | **CLOSED** | `name`、不可哈希 `request_id`、非字符串 `episode_body` 均不再炸全量，[name:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:143)、[request_id:423](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:423)、[body:111](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:111)。 |
  3345	| 6b. 根 `/` containment | **CLOSED** | `root_prefix` 对 `/` 保持 `/`，非根补尾斜杠，[script:203](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:203)。 |
  3346	| 6c. 既有输出 `fchmod 0600` | **NOT-CLOSED · HIGH** | `fchmod` 在 protected-inode 拒绝之前，[script:630](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:630)。`--out` 指向已保护的 `0644` transcript 时，会先把源权限改成 `0600`，再发现碰撞并 exit 2。字节虽未截断，但只读输入已被修改。 |
  3347	| 7. provenance receipt | **CLOSED（仓库内）** | 报告头已指向 receipt，[report:5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:5)；receipt 链与 Git ancestry 一致，[receipt:4](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt:4)。LOW 限制：记录的是当前仓库内唯一可解析的 8-hex 缩写，不是独立于仓库的完整 40-hex OID。 |
  3348	
  3349	### 独立复算
  3350	
  3351	未 import 受审生成器作为 oracle；直接对 live DLQ exact bytes 重新分帧、解码、分类、SHA/长度核对、分组和聚簇：
  3352	
  3353	- `99,915 bytes`，92 LF，SHA-256 `3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590`
  3354	- 92 records；unparseable **0**
  3355	- class：**89 / 2 / 1**
  3356	- byte_exact **4**；approximate **88**；unverifiable **0**；unrecoverable **0**
  3357	- 重复簇：**6 簇 / 29 行**
  3358	- 与提交 ledger 的逐条 `class/inline_state/recoverability`：**0 mismatch**
  3359	
  3360	提交摘要见 [ledger:40](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:40)，重复簇见 [ledger:69](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:69)。当前 7 个唯一 transcript inode 均为 regular、非 symlink、mode `0600`；未读取 transcript 正文。
  3361	
  3362	### 新发现/残留边界
  3363	
  3364	- **BLOCKER**：token-conflict 扫描前早退，仍可无竞态截断 transcript。
  3365	- **BLOCKER**：QA DB 实际读取身份未绑定。
  3366	- **HIGH**：`fchmod` 先于 protected-id 检查；`anomaly` 吞掉不可见性。
  3367	- **MEDIUM**：QA DB 特殊文件门缺失；无 token 未扫描即判不可恢复。
  3368	- **LOW**：单独 `b"\n"` 仍被算作 0 行；escaped lone surrogate 可借 `errors="replace"` 构造 `full_verified`；`episode_body_length=True/1.0` 也可通过长度门。
  3369	
  3370	这个阻断与“一张只读 census 卡”的范围**完全相称**：报告和 UAT 明确承诺纯只读、零写入，[UAT:13](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:13)。残留反例能直接截断或修改本卡正在保护的恢复源，不是范围外的生产级加固要求。
  3371	
  3372	审阅锚定 HEAD `d8d887f29377b8babc49f5dda0d4c4ba01168ad3`，父提交为 `d2827a6d…`；四个受审 tracked artifact 与 HEAD 一致。本轮未修改任何文件、未创建写入 fixture；工作树原有未跟踪 round-5 会话记录。Graphiti MCP 本轮不可用，不影响本地 exact-byte 复算。
  3373	
  3374	
  3375	tokens used
  3376	160,320
  3377	总裁定：**仍阻断 / CARD-G4-9 不可验收**。  
  3378	但结论必须拆开：**冻结的 92 条 ledger 数字 PASS；通用生成器的只读安全闭包 FAIL。**
  3379	
  3380	### 逐项终裁
  3381	
  3382	| 整改项 | 裁定 | 静态反例与证据 |
  3383	|---|---|---|
  3384	| 1. transcript 全候选保护 | **NOT-CLOSED · BLOCKER** | 多 token 非前缀一致时在扫描前直接返回，[script:168](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:168)，此时 `all_candidate_paths=[]`。同一 `request_id` 含 `session:aaaaa`、`session:bbbbb`，`--out` 指向 `aaaaa….jsonl`，不会进入 [保护循环:599](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:599)，最终仍可在 [ftruncate:639](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:639)截断。无需竞态。不可列举但可穿越的子目录也有同类绕过；后置 transcript `stat` 失败仍被 `continue` 吞掉。 |
  3385	| 2. 源侧 fd 身份绑定 | **NOT-CLOSED / PARTIAL · BLOCKER** | DLQ/compare 的狭义修复已 CLOSED：同一 fd `open→fstat→read→identity`，[snapshot:262](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:262)、[DLQ:389](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:389)、[compare:542](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:542)。但 `qa_metrics_db` 仍是早期 path-stat、稍后 SQLite 按路径重新打开，[probe:233](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:233)。可令 stat 看到 inode A、SQLite 实际读取换入的 B、`--out` 为 B 的 hardlink，最终 B 不在保护集并被截断。 |
  3386	| 3. `unverifiable` 四态 | **NOT-CLOSED · HIGH** | distribution/list 同步已实现。但 `anomaly→unrecoverable` 位于 conflict 判断之前，[script:464](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:464)：`anomaly + 扫描受阻/不可读/归因冲突` 仍被假终态化。另无 token 时未扫描即返回，truncated 记录随后被称为“无在盘源”，也应是 `unverifiable`。 |
  3387	| 4. FIFO/设备门 | **NOT-CLOSED / PARTIAL · MEDIUM** | DLQ、compare、`--out` 的 `O_NONBLOCK + S_ISREG` 已 CLOSED，[读侧:269](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:269)、[写侧:620](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:620)。但 QA DB 读侧仍直接进入 SQLite，无 regular-file/nonblocking 门，FIFO 仍可能阻塞。 |
  3388	| 5. 非法 UTF-8 | **CLOSED（原项）** | 逐 LF frame strict decode，并在调用方归 `unparseable`，[splitter:77](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:77)、[caller:399](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:399)。只读验证坏字节得到 1 frame + decode error。 |
  3389	| 6a. 三个指定字段错型 | **CLOSED** | `name`、不可哈希 `request_id`、非字符串 `episode_body` 均不再炸全量，[name:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:143)、[request_id:423](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:423)、[body:111](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:111)。 |
  3390	| 6b. 根 `/` containment | **CLOSED** | `root_prefix` 对 `/` 保持 `/`，非根补尾斜杠，[script:203](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:203)。 |
  3391	| 6c. 既有输出 `fchmod 0600` | **NOT-CLOSED · HIGH** | `fchmod` 在 protected-inode 拒绝之前，[script:630](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:630)。`--out` 指向已保护的 `0644` transcript 时，会先把源权限改成 `0600`，再发现碰撞并 exit 2。字节虽未截断，但只读输入已被修改。 |
  3392	| 7. provenance receipt | **CLOSED（仓库内）** | 报告头已指向 receipt，[report:5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:5)；receipt 链与 Git ancestry 一致，[receipt:4](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt:4)。LOW 限制：记录的是当前仓库内唯一可解析的 8-hex 缩写，不是独立于仓库的完整 40-hex OID。 |
  3393	
  3394	### 独立复算
  3395	
  3396	未 import 受审生成器作为 oracle；直接对 live DLQ exact bytes 重新分帧、解码、分类、SHA/长度核对、分组和聚簇：
  3397	
  3398	- `99,915 bytes`，92 LF，SHA-256 `3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590`
  3399	- 92 records；unparseable **0**
  3400	- class：**89 / 2 / 1**
  3401	- byte_exact **4**；approximate **88**；unverifiable **0**；unrecoverable **0**
  3402	- 重复簇：**6 簇 / 29 行**
  3403	- 与提交 ledger 的逐条 `class/inline_state/recoverability`：**0 mismatch**
  3404	
  3405	提交摘要见 [ledger:40](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:40)，重复簇见 [ledger:69](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:69)。当前 7 个唯一 transcript inode 均为 regular、非 symlink、mode `0600`；未读取 transcript 正文。
  3406	
  3407	### 新发现/残留边界
  3408	
  3409	- **BLOCKER**：token-conflict 扫描前早退，仍可无竞态截断 transcript。
  3410	- **BLOCKER**：QA DB 实际读取身份未绑定。
  3411	- **HIGH**：`fchmod` 先于 protected-id 检查；`anomaly` 吞掉不可见性。
  3412	- **MEDIUM**：QA DB 特殊文件门缺失；无 token 未扫描即判不可恢复。
  3413	- **LOW**：单独 `b"\n"` 仍被算作 0 行；escaped lone surrogate 可借 `errors="replace"` 构造 `full_verified`；`episode_body_length=True/1.0` 也可通过长度门。
  3414	
  3415	这个阻断与“一张只读 census 卡”的范围**完全相称**：报告和 UAT 明确承诺纯只读、零写入，[UAT:13](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:13)。残留反例能直接截断或修改本卡正在保护的恢复源，不是范围外的生产级加固要求。
  3416	
  3417	审阅锚定 HEAD `d8d887f29377b8babc49f5dda0d4c4ba01168ad3`，父提交为 `d2827a6d…`；四个受审 tracked artifact 与 HEAD 一致。本轮未修改任何文件、未创建写入 fixture；工作树原有未跟踪 round-5 会话记录。Graphiti MCP 本轮不可用，不影响本地 exact-byte 复算。
  3418	
  3419	

**Planning ledger metadata verification**
**Planning metadata-only ledger validation**
**Confirming ledger path existence via metadata**
**Designing safe subprocess command execution**
**Planning inline Python ledger verification**
exec
/bin/zsh -lc "python3 -B -c 'exec(\"\"\"
import collections
import hashlib
import json
import re
from pathlib import Path

src = Path(\"/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl\")
ledger_path = Path(\"_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json\")
raw = src.read_bytes()
chunks = raw.split(b\"\\n\")
if raw.endswith(b\"\\n\"):
    chunks.pop()
records = []
bad = []
for n, chunk in enumerate(chunks, 1):
    try:
        obj = json.loads(chunk.decode(\"utf-8\"))
        if not isinstance(obj, dict):
            raise TypeError(type(obj).__name__)
        records.append((n, obj))
    except Exception as exc:
        bad.append((n, type(exc).__name__))

budget = re.compile(r\"exceed_context_size_error|exceeds the available context size\")
archive = re.compile(r\""'^session-archive:([0-9a-fA-F-]+)")
inline_tok = re.compile(r"(?<![0-9a-zA-Z_-])session:([0-9a-f-]{5,})")
sha_pat = re.compile(r"''^[0-9a-f]{64}$")

def cls(rec):
    et = rec.get("error_type", "")
    if et == "EntityTypeValidationError":
        return "schema_entity_type"
    if et == "GroupIdValidationError":
        return "group_id_format"
    if et == "BadRequestError" and budget.search(str(rec.get("error", ""))):
        return "budget_400"
    return "unexpected"

def state(rec):
    body = rec.get("episode_body", "")
    declared_len = rec.get("episode_body_length")
    declared_sha = rec.get("episode_body_sha256", "")
    if not isinstance(body, str):
        return "anomaly"
    try:
        digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    except UnicodeEncodeError:
        return "anomaly"
    length_typed = isinstance(declared_len, int) and not isinstance(declared_len, bool)
    wellformed = isinstance(declared_sha, str) and sha_pat.fullmatch(declared_sha) is not None
    if wellformed and digest == declared_sha and length_typed and len(body) == declared_len:
        return "full_verified"
    if wellformed and len(body) == 200 and length_typed and declared_len > 200:
        return "truncated_prefix"
    return "anomaly"

def tokens(name):
    if not isinstance(name, str):
        return []
    out = []
    match = archive.match(name)
    if match:
        out.append(match.group(1).lower())
    out.extend(x.lower() for x in inline_tok.findall(name))
    return out

class_dist = collections.Counter(cls(r) for _, r in records)
state_dist = collections.Counter(state(r) for _, r in records)
clusters = collections.Counter((str(r.get("name", "")), str(r.get("episode_body_sha256", "")), str(r.get("group_id"))) for _, r in records)
dup_sizes = sorted((v for v in clusters.values() if v > 1), reverse=True)
no_token_lines = [n for n, r in records if not tokens(r.get("name", ""))]

groups = collections.defaultdict(list)
for n, r in records:
    rid = r.get("request_id")
    try:
        hash(rid)
        key = ("missing", n) if rid is None else (type(rid).__name__, rid)
    except TypeError:
        key = ("missing", n)
    groups[key].extend(tokens(r.get("name", "")))
group_conflicts = 0
for toks in groups.values():
    uniq = sorted(set(toks), key=len)
    if uniq and any(not uniq[-1].startswith(t) for t in uniq[:-1]):
        group_conflicts += 1

ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
mismatch = []
for (n, rec), saved in zip(records, ledger["records"]):
    expected = (cls(rec), state(rec), "pass" if state(rec) == "full_verified" else ("prefix_only" if state(rec) == "truncated_prefix" else "FAIL"))
    actual = (saved["class"], saved["inline_state"], saved["sha_check"])
    if expected != actual or saved["stable_key"]["line_no"] != n:
        mismatch.append(n)
approx_internal = sum(
    1 for x in ledger["records"]
    if x["recoverability"] == "approximate"
    and x["inline_state"] == "truncated_prefix"
    and x["transcript_match_count"] == 1
    and len(x["transcript_paths"]) == 1
    and x["attribution_conflict"] is False
)
print(json.dumps({
    "sha256": hashlib.sha256(raw).hexdigest(),
    "bytes": len(raw),
    "lf_frames": len(chunks),
    "records": len(records),
    "unparseable": len(bad),
    "class": dict(class_dist),
    "inline": dict(state_dist),
    "duplicate_clusters": len(dup_sizes),
    "duplicate_occurrences": sum(dup_sizes),
    "duplicate_sizes": dup_sizes,
    "no_token_lines": no_token_lines,
    "request_groups": len(groups),
    "token_prefix_conflict_groups": group_conflicts,
    "ledger_record_mismatches": mismatch,
    "ledger_recoverability": ledger["recoverability_distribution"],
    "ledger_attribution_conflicts": len(ledger["attribution_conflicts"]),
    "approximate_internal_contract_rows": approx_internal,
    "ledger_sha_matches_source": ledger["dlq_file"]["sha256"] == hashlib.sha256(raw).hexdigest()
}, ensure_ascii=True, sort_keys=True))
""")'"'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 exited 1 in 0ms:
Traceback (most recent call last):
  File "<string>", line 1, in <module>
    exec("""
    ~~~~^^^^
    import collections
    ^^^^^^^^^^^^^^^^^^
    ...<120 lines>...
    }, ensure_ascii=True, sort_keys=True))
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    """)
    ^^^^
  File "<string>", line 11
    chunks = raw.split(b"
                       ^
SyntaxError: unterminated string literal (detected at line 11)

**Fixing newline parsing with bytes delimiter**
exec
/bin/zsh -lc "python3 -B -c 'exec(\"\"\"
import collections
import hashlib
import json
import re
from pathlib import Path

src = Path(\"/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl\")
ledger_path = Path(\"_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json\")
raw = src.read_bytes()
lf = bytes([10])
chunks = raw.split(lf)
if raw.endswith(lf):
    chunks.pop()
records = []
bad = []
for n, chunk in enumerate(chunks, 1):
    try:
        obj = json.loads(chunk.decode(\"utf-8\"))
        if not isinstance(obj, dict):
            raise TypeError(type(obj).__name__)
        records.append((n, obj))
    except Exception as exc:
        bad.append((n, type(exc).__name__))

budget = re.compile(r\"exceed_context_size_error|exceeds the available context size\")
archive = re.compile(r\""'^session-archive:([0-9a-fA-F-]+)")
inline_tok = re.compile(r"(?<![0-9a-zA-Z_-])session:([0-9a-f-]{5,})")
sha_pat = re.compile(r"''^[0-9a-f]{64}$")

def cls(rec):
    et = rec.get("error_type", "")
    if et == "EntityTypeValidationError":
        return "schema_entity_type"
    if et == "GroupIdValidationError":
        return "group_id_format"
    if et == "BadRequestError" and budget.search(str(rec.get("error", ""))):
        return "budget_400"
    return "unexpected"

def state(rec):
    body = rec.get("episode_body", "")
    declared_len = rec.get("episode_body_length")
    declared_sha = rec.get("episode_body_sha256", "")
    if not isinstance(body, str):
        return "anomaly"
    try:
        digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    except UnicodeEncodeError:
        return "anomaly"
    typed = isinstance(declared_len, int) and not isinstance(declared_len, bool)
    wellformed = isinstance(declared_sha, str) and sha_pat.fullmatch(declared_sha) is not None
    if wellformed and digest == declared_sha and typed and len(body) == declared_len:
        return "full_verified"
    if wellformed and len(body) == 200 and typed and declared_len > 200:
        return "truncated_prefix"
    return "anomaly"

def tokens(name):
    if not isinstance(name, str):
        return []
    out = []
    match = archive.match(name)
    if match:
        out.append(match.group(1).lower())
    out.extend(x.lower() for x in inline_tok.findall(name))
    return out

class_dist = collections.Counter(cls(r) for _, r in records)
state_dist = collections.Counter(state(r) for _, r in records)
clusters = collections.Counter((str(r.get("name", "")), str(r.get("episode_body_sha256", "")), str(r.get("group_id"))) for _, r in records)
dup_sizes = sorted((v for v in clusters.values() if v > 1), reverse=True)
no_token_lines = [n for n, r in records if not tokens(r.get("name", ""))]

groups = collections.defaultdict(list)
for n, r in records:
    rid = r.get("request_id")
    try:
        hash(rid)
        key = ("missing", n) if rid is None else (type(rid).__name__, rid)
    except TypeError:
        key = ("missing", n)
    groups[key].extend(tokens(r.get("name", "")))
group_conflicts = 0
for toks in groups.values():
    uniq = sorted(set(toks), key=len)
    if uniq and any(not uniq[-1].startswith(t) for t in uniq[:-1]):
        group_conflicts += 1

ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
mismatch = []
for (n, rec), saved in zip(records, ledger["records"]):
    st = state(rec)
    expected = (cls(rec), st, "pass" if st == "full_verified" else ("prefix_only" if st == "truncated_prefix" else "FAIL"))
    actual = (saved["class"], saved["inline_state"], saved["sha_check"])
    if expected != actual or saved["stable_key"]["line_no"] != n:
        mismatch.append(n)
approx_internal = sum(1 for x in ledger["records"] if x["recoverability"] == "approximate" and x["inline_state"] == "truncated_prefix" and x["transcript_match_count"] == 1 and len(x["transcript_paths"]) == 1 and x["attribution_conflict"] is False)
digest = hashlib.sha256(raw).hexdigest()
print(json.dumps({
    "sha256": digest,
    "bytes": len(raw),
    "lf_frames": len(chunks),
    "records": len(records),
    "unparseable": len(bad),
    "class": dict(class_dist),
    "inline": dict(state_dist),
    "duplicate_clusters": len(dup_sizes),
    "duplicate_occurrences": sum(dup_sizes),
    "duplicate_sizes": dup_sizes,
    "no_token_lines": no_token_lines,
    "request_groups": len(groups),
    "token_prefix_conflict_groups": group_conflicts,
    "ledger_record_mismatches": mismatch,
    "ledger_recoverability": ledger["recoverability_distribution"],
    "ledger_attribution_conflicts": len(ledger["attribution_conflicts"]),
    "approximate_internal_contract_rows": approx_internal,
    "ledger_sha_matches_source": ledger["dlq_file"]["sha256"] == digest
}, ensure_ascii=True, sort_keys=True))
""")'"'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
{"approximate_internal_contract_rows": 88, "bytes": 99915, "class": {"budget_400": 89, "group_id_format": 1, "schema_entity_type": 2}, "duplicate_clusters": 6, "duplicate_occurrences": 29, "duplicate_sizes": [16, 4, 3, 2, 2, 2], "inline": {"full_verified": 4, "truncated_prefix": 88}, "ledger_attribution_conflicts": 3, "ledger_record_mismatches": [], "ledger_recoverability": {"approximate": 88, "byte_exact": 4, "unrecoverable": 0, "unverifiable": 0}, "ledger_sha_matches_source": true, "lf_frames": 92, "no_token_lines": [1, 2, 3, 5, 6, 9, 10, 13, 14, 18, 20, 21, 24, 25, 29, 30, 31, 33, 34, 37, 38, 41, 42, 45, 46, 49, 50, 53, 54, 57, 58, 61, 62, 65, 66, 69, 70, 73, 74, 75, 78, 79, 82, 83, 86, 87, 90, 91], "records": 92, "request_groups": 25, "sha256": "3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590", "token_prefix_conflict_groups": 0, "unparseable": 0}

**Revising no_token_lines grouping logic**
**Verifying attribution conflict counts**
exec
/bin/zsh -lc "python3 -B -c 'exec(\"\"\"
import json
import re
from collections import defaultdict
from pathlib import Path
raw=Path(\"/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl\").read_bytes()
lines=raw.split(bytes([10]))
if raw.endswith(bytes([10])):
    lines.pop()
records=[(i,json.loads(x.decode(\"utf-8\"))) for i,x in enumerate(lines,1)]
archive=re.compile(r\""'^session-archive:([0-9a-fA-F-]+)")
inline=re.compile(r"(?<![0-9a-zA-Z_-])session:([0-9a-f-]{5,})")
def toks(name):
    if not isinstance(name,str):
        return []
    out=[]
    m=archive.match(name)
    if m:
        out.append(m.group(1).lower())
    out.extend(x.lower() for x in inline.findall(name))
    return out
groups=defaultdict(list)
for n,r in records:
    rid=r.get("request_id")
    try:
        hash(rid)
        key=("missing",n) if rid is None else (type(rid).__name__,rid)
    except TypeError:
        key=("missing",n)
    groups[key].append((n,r))
no_token=[]
conflict=[]
for members in groups.values():
    ts=sorted(set(t for _,r in members for t in toks(r.get("name",""))),key=len)
    nums=[n for n,_ in members]
    if not ts:
        no_token.extend(nums)
    elif any(not ts[-1].startswith(t) for t in ts[:-1]):
        conflict.extend(nums)
print(json.dumps({"group_no_token_record_lines":sorted(no_token),"group_token_conflict_record_lines":sorted(conflict),"no_token_records":len(no_token),"conflict_records":len(conflict)}))
""")'"'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
{"group_no_token_record_lines": [1, 2, 3], "group_token_conflict_record_lines": [], "no_token_records": 3, "conflict_records": 0}

**Planning internal output corrections**
**Testing JSON surrogate pair handling**
exec
/bin/zsh -lc "python3 -B -c 'import runpy,hashlib,json; m=runpy.run_path(\"backend/scripts/census_dead_letter_episodes.py\"); split=m[\"_split_jsonl_lines\"]; inline=m[\"inline_state\"]; full=m[\"full_body_verified\"]; lone=json.loads(\"\"\\\\ud800\"\"); old_sha=hashlib.sha256(lone.encode(\"utf-8\",errors=\"replace\")).hexdigest(); emoji=json.loads(\"\"\\\\ud83d\\\\ude00\"\"); emoji_sha=hashlib.sha256(emoji.encode(\"utf-8\")).hexdigest(); xsha=hashlib.sha256(b\"x\").hexdigest(); out={\"split_counts\":{\"empty\":len(split(b\"\")),\"lf\":len(split(bytes([10]))),\"lf_lf\":len(split(bytes([10,10]))),\"object_lf\":len(split(b\"{}\"+bytes([10]))),\"object_lf_lf\":len(split(b\"{}\"+bytes([10,10])))},\"lf_reason\":split(bytes([10]))[0],\"lone_inline\":inline({\"episode_body\":lone,\"episode_body_length\":1,\"episode_body_sha256\":old_sha}),\"lone_full\":full({\"episode_body_full\":lone,\"episode_body_length\":1,\"episode_body_sha256\":old_sha}),\"emoji_inline\":inline({\"episode_body\":emoji,\"episode_body_length\":1,\"episode_body_sha256\":emoji_sha}),\"typed_lengths\":{\"bool\":inline({\"episode_body\":\"x\",\"episode_body_length\":True,\"episode_body_sha256\":xsha}),\"float\":inline({\"episode_body\":\"x\",\"episode_body_length\":1.0,\"episode_body_sha256\":xsha}),\"int\":inline({\"episode_body\":\"x\",\"episode_body_length\":1,\"episode_body_sha256\":xsha})}}; print(json.dumps(out,ensure_ascii=True,sort_keys=True))'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 exited 1 in 0ms:
  File "<string>", line 1
    import runpy,hashlib,json; m=runpy.run_path("backend/scripts/census_dead_letter_episodes.py"); split=m["_split_jsonl_lines"]; inline=m["inline_state"]; full=m["full_body_verified"]; lone=json.loads(""\\ud800""); old_sha=hashlib.sha256(lone.encode("utf-8",errors="replace")).hexdigest(); emoji=json.loads(""\\ud83d\\ude00""); emoji_sha=hashlib.sha256(emoji.encode("utf-8")).hexdigest(); xsha=hashlib.sha256(b"x").hexdigest(); out={"split_counts":{"empty":len(split(b"")),"lf":len(split(bytes([10]))),"lf_lf":len(split(bytes([10,10]))),"object_lf":len(split(b"{}"+bytes([10]))),"object_lf_lf":len(split(b"{}"+bytes([10,10])))},"lf_reason":split(bytes([10]))[0],"lone_inline":inline({"episode_body":lone,"episode_body_length":1,"episode_body_sha256":old_sha}),"lone_full":full({"episode_body_full":lone,"episode_body_length":1,"episode_body_sha256":old_sha}),"emoji_inline":inline({"episode_body":emoji,"episode_body_length":1,"episode_body_sha256":emoji_sha}),"typed_lengths":{"bool":inline({"episode_body":"x","episode_body_length":True,"episode_body_sha256":xsha}),"float":inline({"episode_body":"x","episode_body_length":1.0,"episode_body_sha256":xsha}),"int":inline({"episode_body":"x","episode_body_length":1,"episode_body_sha256":xsha})}}; print(json.dumps(out,ensure_ascii=True,sort_keys=True))
                                                                                                                                                                                                             ^
SyntaxError: unexpected character after line continuation character

**Fixing shell quoting with direct char usage**
exec
/bin/zsh -lc "python3 -B -c 'import runpy,hashlib,json; m=runpy.run_path(\"backend/scripts/census_dead_letter_episodes.py\"); split=m[\"_split_jsonl_lines\"]; inline=m[\"inline_state\"]; full=m[\"full_body_verified\"]; lone=chr(0xD800); old_sha=hashlib.sha256(lone.encode(\"utf-8\",errors=\"replace\")).hexdigest(); emoji=chr(0x1F600); emoji_sha=hashlib.sha256(emoji.encode(\"utf-8\")).hexdigest(); xsha=hashlib.sha256(b\"x\").hexdigest(); out={\"split_counts\":{\"empty\":len(split(b\"\")),\"lf\":len(split(bytes([10]))),\"lf_lf\":len(split(bytes([10,10]))),\"object_lf\":len(split(b\"{}\"+bytes([10]))),\"object_lf_lf\":len(split(b\"{}\"+bytes([10,10])))},\"lf_reason\":split(bytes([10]))[0],\"lone_inline\":inline({\"episode_body\":lone,\"episode_body_length\":1,\"episode_body_sha256\":old_sha}),\"lone_full\":full({\"episode_body_full\":lone,\"episode_body_length\":1,\"episode_body_sha256\":old_sha}),\"emoji_inline\":inline({\"episode_body\":emoji,\"episode_body_length\":1,\"episode_body_sha256\":emoji_sha}),\"typed_lengths\":{\"bool\":inline({\"episode_body\":\"x\",\"episode_body_length\":True,\"episode_body_sha256\":xsha}),\"float\":inline({\"episode_body\":\"x\",\"episode_body_length\":1.0,\"episode_body_sha256\":xsha}),\"int\":inline({\"episode_body\":\"x\",\"episode_body_length\":1,\"episode_body_sha256\":xsha})}}; print(json.dumps(out,ensure_ascii=True,sort_keys=True))'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
{"emoji_inline": ["full_verified", "pass"], "lf_reason": ["", null], "lone_full": false, "lone_inline": ["anomaly", "FAIL"], "split_counts": {"empty": 0, "lf": 1, "lf_lf": 2, "object_lf": 1, "object_lf_lf": 2}, "typed_lengths": {"bool": ["anomaly", "FAIL"], "float": ["anomaly", "FAIL"], "int": ["full_verified", "pass"]}}

**Planning comprehensive file access audit**
exec
/bin/zsh -lc "rg -n '\\b(open|connect|execute|write|fchmod|chmod|ftruncate|truncate|unlink|remove|rename|replace|mkdir|touch)\\b|os\\.(open|write|fchmod|chmod|ftruncate|unlink|remove|rename|replace|mkdir)|Path\\(' backend/scripts/census_dead_letter_episodes.py" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
33:    （chmod 000）时整体 exit 2（拒绝在源不可见时产出 unrecoverable 假象）；
81:    - 逐行 **strict** decode（round-4 MEDIUM 整改）: errors="replace" 会把非法
121:    # round-5 LOW 整改: errors="replace" 会把 JSON escaped lone surrogate
277:        fd = os.open(db_path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
291:    conn = sqlite3.connect(uri, uri=True)
305:            r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
309:            total = conn.execute("SELECT COUNT(*) FROM qa_error_logs").fetchone()[0]
313:                hits[et] = conn.execute("SELECT COUNT(*) FROM qa_error_logs WHERE error_type = ?", (et,)).fetchone()[0]
330:    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
393:    dlq_path = Path(args.dlq)
398:    transcripts_dir = Path(args.transcripts_dir)
405:    # round-2 HIGH-3 整改: 存在但不可读/不可遍历的根（chmod 000）此前 exit 0
419:        out_path = Path(args.out)
420:        protected_paths = [dlq_path, *(Path(p) for p in args.compare)]
422:            protected_paths.append(Path(args.qa_metrics_db))
607:        cinfo, cid = describe_copy(Path(cp))
614:            Path(args.qa_metrics_db),
682:        # round-3 整改: 消除 check-then-open TOCTOU。先以 O_NOFOLLOW 打开且
684:        # ftruncate。检查与写入作用于同一 fd，检查后被换 symlink/hardlink 无效。
686:            fd = os.open(args.out, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
696:            # round-5 HIGH 整改: 碰撞检查必须**先于** fchmod —— 否则 --out 指向
706:                os.fchmod(fd, 0o600)
707:            os.ftruncate(fd, 0)
710:                f.write(out_json + "\n")

**Assessing output write and collision timing**
**Evaluating device open side effects and QA path races**
**Analyzing QA path alias and SQLite side effects**
**Investigating SQLite URI decoding issue**
**Planning sequential tool calls for analysis**
mcp: sequential-thinking/sequentialthinking started
mcp: sequential-thinking/sequentialthinking (completed)
**Listing .jsonl files under worktree**
exec
/bin/zsh -lc "rg --files -g '*.jsonl' | sed -n '1,80p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
scripts/fixtures/synthetic_fusion_sample.jsonl
_bmad-output/审查/g5-1-evidence/logs-v2-archive/N9.jsonl
_bmad-output/审查/g5-1-evidence/logs-v2-archive/N8.jsonl
_bmad-output/审查/g5-1-evidence/logs-v2-archive/N10.jsonl
_bmad-output/审查/g5-1-evidence/logs-v2-archive/N7.jsonl
_bmad-output/审查/g5-1-evidence/logs-v2-archive/N6.jsonl
_bmad-output/审查/g5-1-evidence/logs-v2-archive/N3.jsonl
_bmad-output/审查/g5-1-evidence/logs-v2-archive/N4.jsonl
_bmad-output/审查/g5-1-evidence/logs-v2-archive/N1.jsonl
_bmad-output/审查/g5-1-evidence/logs-v2-archive/N2.jsonl
_bmad-output/审查/g5-1-evidence/logs-v2-archive/N5.jsonl
backend/tests/fixtures/regression_baselines/board_manifest_baseline_history.jsonl
backend/tests/fixtures/regression_baselines/vault_retrieval_baseline_history.jsonl
backend/tests/fixtures/regression_baselines/memory_retrieval_baseline_history.jsonl

**Analyzing token matching for filenames**
exec
/bin/zsh -lc "python3 -B -c 'import runpy,json; from pathlib import Path; m=runpy.run_path(\"backend/scripts/census_dead_letter_episodes.py\"); f=m[\"resolve_group_attribution\"]; a=f([\"board\",\"vault\"],Path(\".\")); b=f([],Path(\".\")); print(json.dumps({\"conflict\":{\"token_conflict\":a.get(\"token_conflict\"),\"all_candidate_count\":len(a[\"all_candidate_paths\"]),\"scan_errors\":len(a.get(\"scan_errors\",[]))},\"no_token\":{\"no_token\":b.get(\"no_token\"),\"all_candidate_count\":len(b[\"all_candidate_paths\"])}}))'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 695ms:
{"conflict": {"token_conflict": true, "all_candidate_count": 2, "scan_errors": 0}, "no_token": {"no_token": true, "all_candidate_count": 0}}

**Analyzing static scan error handling**
**Tracing stat_failures and race conditions**
**Investigating missing no_token marker**
**Clarifying no_token recoverability logic**
**Resolving no_token status and JSON encoding issues**
**Verifying SHA field type and comparison**
**Planning ledger metadata verification**
**Evaluating metadata access permissions**
**Designing read-only path verification**
**Testing exec_command sandbox access**
exec
/bin/zsh -lc "python3 -B -c 'import json,os,stat; from pathlib import Path; d=json.loads(Path(\"_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json\").read_text()); ps=sorted({p for r in d[\"records\"] if r[\"recoverability\"]==\"approximate\" for p in r[\"transcript_paths\"]}); rows=[]; 
for p in ps:
 s=os.lstat(p); rows.append((stat.S_ISREG(s.st_mode),stat.S_ISLNK(s.st_mode),os.access(p,os.R_OK),(s.st_dev,s.st_ino),stat.S_IMODE(s.st_mode)))
print(json.dumps({\"unique_declared_paths\":len(ps),\"all_regular\":all(x[0] for x in rows),\"any_symlink\":any(x[1] for x in rows),\"all_readable\":all(x[2] for x in rows),\"unique_inodes\":len({x[3] for x in rows}),\"modes\":sorted({oct(x[4]) for x in rows})}))'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
{"unique_declared_paths": 7, "all_regular": true, "any_symlink": false, "all_readable": true, "unique_inodes": 7, "modes": ["0o600"]}

**Planning read-only database verification**
**Executing read-only SQLite queries**
exec
/bin/zsh -lc "python3 -B -c 'import sqlite3,json; p=\"/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db\"; c=sqlite3.connect(\"file:\"+p+\"?mode=ro\",uri=True); c.execute(\"PRAGMA query_only=ON\"); tables=[r[0] for r in c.execute(\"SELECT name FROM sqlite_master WHERE type=\\\"table\\\" AND name NOT LIKE \\\"sqlite_%\\\"\")]; total=c.execute(\"SELECT COUNT(*) FROM qa_error_logs\").fetchone()[0] if \"qa_error_logs\" in tables else None; hits={x:c.execute(\"SELECT COUNT(*) FROM qa_error_logs WHERE error_type=?\",(x,)).fetchone()[0] for x in [\"BadRequestError\",\"EntityTypeValidationError\",\"GroupIdValidationError\"]} if total is not None else {}; c.close(); print(json.dumps({\"tables\":tables,\"rows\":total,\"hits\":hits},sort_keys=True))'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
{"hits": {"BadRequestError": 0, "EntityTypeValidationError": 0, "GroupIdValidationError": 0}, "rows": 0, "tables": ["qa_error_logs"]}

**Verifying hash and sidecars**
exec
/bin/zsh -lc 'shasum -a 256 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
6cb5510dc91cf1c29c7ce6510013238cf83b5eae6305180e6aa9320a957a6a05  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db

exec
/bin/zsh -lc "find /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data -maxdepth 1 -name 'qa_metrics.db*' -print" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db

**Inspecting item1 UAT wording and verifying file status**
**Summarizing fix status and plan verification**
**Clarifying closure counts and scan limitations**
**Analyzing artifact evidence discrepancies**
**Assessing evidence provenance staleness**
**Flagging contradictory report assertions**
**Evaluating stat failure handling**
**Assessing unreachable stat_failure code and test claims**
**Flagging missing test evidence**
**Mapping code references to lines**
exec
/bin/zsh -lc "nl -ba _bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json | sed -n '35,180p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
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
   167	  "file_identity_verified": true,
   168	  "tables": [
   169	   "qa_error_logs"
   170	  ],
   171	  "qa_error_logs_rows": 0,
   172	  "error_type_hits": {
   173	   "BadRequestError": 0,
   174	   "EntityTypeValidationError": 0,
   175	   "GroupIdValidationError": 0
   176	  },
   177	  "verdict": "no_source_rows"
   178	 },
   179	 "records": [
   180	  {

exec
/bin/zsh -lc "nl -ba _bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md | sed -n '10,35p;40,46p;93,106p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
    10	# UAT · CARD-G4-9 DLQ 真实挂载 census 分诊
    11	
    12	> [!info]+ 你不需要碰命令行 — 全部技术验证我已代跑（结果见下）
    13	> 这张卡**没有修任何东西，也没有恢复任何数据**——它是一次"清点尸体"的只读普查：
    14	> 线上 Graphiti 写入失败后落进死信文件的 92 条记录，逐条查清"是什么死的、还能不能救、去哪里救"，
    15	> 给后续的 G4-10（真正做恢复的卡）留一份带稳定编号的台账。卡面如实标注：离日常使用价值远，属恢复能力地基。
    16	
    17	## 📌 你需要过目的三个结论
    18	
    19	1. **92 条死信全部查清、零"待定"**：89 条是"内容太长超过本地模型 16384 token 上限"（未修，根因归 G4-10）；2 条是 5 月 14 日的 schema 冲突、1 条是旧 group_id 冒号格式——这 3 条的根因**当天之后就已修复**，不会再新增。
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
    40	| round-3 findings 逐条整改 | **6/6 完成**：transcript 并入保护集 / O_NOFOLLOW+fstat 消 TOCTOU / os.walk 替 glob（不跟随目录 symlink+遍历错误显式捕获）/ 不可读候选 fail-closed / JSONL 严格 LF 分帧 / 非 dict 归 unparseable。6 条新反例实测全过、数字第三次不变 | 报告 §7d + `grep-selfattest.txt` |
    41	| Codex 复审 round-4 | **仍阻断**（1/6 CLOSED；2 新 BLOCKER + 1 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round4.md` |
    42	| round-4 findings 逐条整改 | **9/9 完成**：全候选入保护集 / 读侧 fd 身份消源侧 TOCTOU / 新增 unverifiable 第四态 / FIFO 设备门 / strict UTF-8 / 3 条错型与边界 LOW / provenance receipt。5 条新反例实测全过；第四次全量重跑数字仍不变 | 报告 §7e + `grep-selfattest.txt` |
    43	| Codex 复审 round-5 | **仍阻断**（3/8 CLOSED；2 BLOCKER + 2 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round5.md` |
    44	| round-5 findings 逐条整改 | **9/9 完成**：先扫描后判定（冲突候选亦入保护集）/ QA DB fd 身份+复核 / 可见性优先于 anomaly / fchmod 后置于碰撞检查 / QA DB 特殊文件门 / no_token 归 unverifiable / 3 条 LOW。6 条新反例实测全过；第五次全量重跑数字仍不变 | 报告 §7f |
    45	| 独立 Workflow 4-agent 复核 | G4-9 数字 agent：92 条重算 **0 mismatch**（class/inline/三态/25 request_id/7 transcript 在盘/台账 sha 全 CONFIRMED，仅 2 处描述区间 REFUTED 已修正）；只读契约 agent：与 Codex 同源的 3 条 blocker（已随上整改） | Workflow wf_737b1a95-20b journal |
    46	
    93	## 🔧 Codex round-5 复审整改记录（3/8 CLOSED → 9 项全关闭）
    94	
    95	round-5 继续深挖，两条新 BLOCKER 与两条 HIGH 都成立：
    96	
    97	- **冲突组的候选没进保护集**：token 冲突时我在扫描**之前**就早退了，那些候选从没被看到，`--out` 指向它们照样截断。→ 改成**先扫描后判定**，无论最终是否采信，见到的候选一律进保护集。
    98	- **qa_metrics.db 身份没绑定实际读取**：先按路径 stat、SQLite 稍后按路径重开，中间可换。→ 改 fd 取身份 + 打开后复核身份一致。
    99	- **anomaly 吞掉了"看不见"**：`anomaly→unrecoverable` 排在可见性判断之前，扫描受阻时仍断言"不可恢复"。→ 判定链改为**可见性优先**。
   100	- **`fchmod` 排在碰撞检查之前**：`--out` 指向受保护的只读输入时，会先把它的权限从 644 改成 600 才发现碰撞——字节没丢但输入被改了。→ 碰撞检查前移。
   101	- **其余 5 项**：QA DB 特殊文件门、无 token 归 `unverifiable`、单独换行算 1 空行、strict encode 堵住 lone surrogate 伪造 `full_verified`、`bool` 不再通过长度门。
   102	
   103	**一处计数如实变化**：归因冲突 0→3。因为"名字不含 session token"现在被诚实标为"未做归因扫描"，正是那 3 条 callout 记录；它们 inline 全量、不依赖 transcript，仍是可字节级恢复。**三态分布不变**（4/88/0/0）——是标注变诚实，不是结论变化。
   104	
   105	round-5 整改后第五次全量重跑：**92 条、4/88/0/0、89/2/1、6/29、shasum 不变——五轮整改数字全程未变**。
   106	

exec
/bin/zsh -lc "nl -ba _bmad-output/审查/G4-9-DLQ-census-2026-08-28.md | sed -n '1,10p;45,85p;87,98p;163,179p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
     1	# CARD-G4-9 — DLQ 真实挂载 census 分诊报告
     2	
     3	> **批次**: BATCH-2026-08-28-第五批 / CARD-G4-9（4h · wave 1 · 未来铺路）
     4	> **性质**: 纯只读 census。0 写入、0 重放、0 业务代码改动。唯一代码产物 = `backend/scripts/census_dead_letter_episodes.py`。
     5	> **代码基线**: 分析对象锚定 `37387a86`（第五批开工基线）。**本卡交付物 artifact commit 链**：精确 SHA 逐段记录于 `_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt`（commit 无法自含己身 SHA，故用后置 receipt 绑定——Codex round-4 LOW 整改）
     6	> **台账**: `_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json`（92 条逐条，G4-10 消费）
     7	> **证据包**: `_bmad-output/审查/G4-9-evidence/`（shasums before/after、grep 自证、容器内 sha 实测）
     8	> **执行日期**: 2026-08-28
     9	
    10	---
    45	## §3 inline 完整性 + SHA 对账
    46	
    47	`DeadLetterStore.store()` 落盘的 `episode_body` 来自 `EpisodeTask.to_dict()`，后者做 `episode_body[:200]` 截断（`episode_worker.py:107`，"truncate for logging"）；全量正文只有 `DEAD_LETTER_STORE_FULL_BODY` 开启时以 `episode_body_full` 另存——**live 容器该 env 未设置（实测），92 条 `episode_body_full` 均缺席**。逐条重算 sha256(inline) 对账 `episode_body_sha256` 结果：
    48	
    49	| inline 状态 | 条数 | 判据 |
    50	|---|---|---|
    51	| `full_verified`（内联全量，sha 对账通过） | **4** | 重算值 == 声明值且长度精确匹配（四条正文实为 131/142/150/180 字符，范围 **131–180**，天然未截断；round-2 LOW 修正） |
    52	| `truncated_prefix`（200 字符前缀） | **88** | len(inline)==200、声明 sha 为合法 64-hex 且声明长度 205–8036。**注**：sha 只能证明 inline≠声明全文，"确为前缀"依赖 `to_dict()[:200]` 生产不变量，无法用 sha 直接证明（Codex round-1 HIGH-1 措辞收敛） |
    53	| `anomaly`（对不上账） | **0** | — |
    54	
    55	4 条 full_verified = 3 条 callout（§2 的 schema/group_id 三条）+ 1 条短 qa_highlight（行 74）。
    56	
    57	## §4 源指针核销（qa_metrics.db，只读 mode=ro）
    58	
    59	- **qa_metrics.db**（live `backend/data/qa_metrics.db`，经 sqlite URI `mode=ro` 打开）：唯一表 `qa_error_logs`（列 category/error_type/source_module/stack_summary/created_at，**无 request_id 列**），**行数 = 0**。按三个 error_type 探查命中均 0。**核销裁定：`no_source_rows` —— qa_metrics.db 对 92 条死信不构成任何源指针，0/92 可经其溯源。**
    60	- 附加核销（超出卡面要求，如实记录以封死"还有别处可捞"的幻想）：
    61	  - `llm_call_logs.db`（同目录，mode=ro）：仅 token/延迟/成本指标列，**无 prompt/response 正文**；
    62	  - `backend/data/outbox/`：**空目录**（A7 outbox 只接 enqueue 失败，本 92 条全部是 enqueue 成功、处理失败，不经 outbox）；
    63	  - `episode_body_full`：0 条（§3）。
    64	- **有效源指针只剩一条**：DLQ 记录的 `request_id`（structlog contextvars 捕获的进程内值）把同一次 SessionEnd 归档的 3–5 条 episode 绑成组，组内 `session-archive:<id16>` / `…session:<hex>` 名字携带 session id → `~/.claude/projects/-…-canvas-vault/<session>.jsonl` transcript。**7 个 session 的 transcript 全部在盘实测存在**（90,584–723,950 字节，逐一恰 1 个 glob 命中、常规文件），88/88 条截断记录归因成功、0 条归因冲突。**归因边界（诚实声明）**：归因 = "唯一在盘候选已定位"，≠ "内容已验证"——本卡未读任何 transcript 内容，内容级核验归 G4-10 重建时以 `episode_body_sha256` 对账。
    65	
    66	## §5 可恢复性裁定（三态 + unverifiable 第四态）
    67	
    68	| 三态 | 条数 | 裁定依据 |
    69	|---|---|---|
    70	| **可字节级**（byte_exact） | **4** | inline 正文全量：sha256 重算对账通过**且**长度精确匹配（fail-closed 双门）——重放可逐字节还原 episode |
    71	| **近似**（approximate） | **88** | inline 仅 200 字符前缀，但经 request_id 组归因到在盘 transcript；G4-10 可对 22 条 session-archive 重新格式化 transcript（确定性、可用 `episode_body_sha256` 验证是否达字节级）、对 66 条 qa_highlight(44)/distillation(22) 重跑蒸馏（LLM 非确定性，语义近似、不保证逐字节） |
    72	| **不可恢复**（unrecoverable） | **0** | inline 截断且经完整可见的扫描确认无在盘上游源 |
    73	| **不可核验**（unverifiable，round-4 新增） | **0** | 源可见性不足（扫描受阻/不可读候选/归因冲突）——既不宣称可恢复，也不宣称不可恢复。Codex round-4 指出：把"看不见"终态化为"不可恢复"是不诚实断言，故单列第四态 |
    74	
    75	**不可恢复清单（显式成段）**：本次 census 裁定不可恢复条目 **0 条**；三态裁定覆盖 92/92，**"待定"0 条**。
    76	
    77	诚实边界：`近似` ≠ 已恢复。88 条的实际重建（含 22 条 session-archive 是否能达字节级）是 G4-10 的工作与验收，本卡只交付"上游源在盘、路径已核销"的证据链。transcript 属用户本机 `~/.claude/projects/` 数据，若未来被清理，近似裁定随之失效——台账已逐条记录 transcript 绝对路径供 G4-10 开工时复核。
    78	
    79	## §6 台账稳定键（G4-10 交接契约）
    80	
    81	台账逐条携带复合键 `{line_no, sha256_prefix(16 hex), request_id}`。**语义（Codex round-1 LOW-2 修正）**：这是**冻结快照内的 occurrence key**，不是跨文件重排或语义幂等键——台账头部 `dlq_file.sha256`（`3b37460f4215f6ac…`）即快照指纹，`line_no` 在该快照内已单列唯一；`sha256_prefix`（本快照 69 个唯一值，qa_highlight 家族实测同名同 sha 多条）与 `request_id`（仅 25 个唯一值，进程内 contextvars、重启可复用）是**冗余对账/诊断维度**，不是唯一性的必要条件。G4-10 消费前先 diff 头部 sha 即知 DLQ 是否长了新条目；语义级去重不得按本键，须按 `duplicate_clusters` 段（见下）。**语义重复簇（MEDIUM-2 整改）**：按 `{name, episode_body_sha256, group_id}` 聚簇，**6 簇覆盖 29 行**（最大簇 = 同一 session-archive 16 行，`reference_time` 各不相同——同内容反复入队反复超限）。台账 `duplicate_clusters` 段逐簇列 line_nos，records 逐条透传 `reference_time`；G4-10 重放前必须先定去重策略（89 条 budget 修根因后若逐条盲放，将把同内容写入最多 16 遍）。
    82	
    83	**隐私（MEDIUM-3 整改）**：`transcript_paths` 含本机用户名与完整 session UUID，台账与本报告为 **private-only 工件**（台账头部已带 privacy 字段；仓库纪律 = 不 push 公网远端）。
    84	
    85	逐条另带 `class / inline_state / recoverability / transcript_paths / transcript_match_count / attribution_conflict / error_excerpt / failed_at / reference_time`，G4-10 可直接按 `recoverability` 分桶排重放优先级（建议：4 条 byte_exact 先行——但其中 3 条 group_id 为已弃用 `vault:default`，重放前需按 D16 规约重映射并过 `to_physical_group_id()`；89 条 budget_400 重放前必须先修 context 超限根因，否则原样重放必然复现 400）。
    87	## §7 裁判证据（整改版脚本重跑）
    88	
    89	| 证据 | 结果 |
    90	|---|---|
    91	| 运行前后 shasum（live/主仓/孤儿①/孤儿② 四份 DLQ + qa_metrics.db） | `diff shasums-before.txt shasums-after.txt` 空 → **PASS，0 写入** |
    92	| grep 自证（import 行全 stdlib；neo4j/graphiti/bolt/app. import 0 命中；`--apply` 定义 0 命中；写模式 open 仅 `--out` 1 处且受路径碰撞守卫保护） | **PASS**（`grep-selfattest.txt`，含守卫在位证明） |
    93	| 容器内 sha 实测 | 92 行、sha 与宿主 live 地址一致（`container-sha-check.txt`） |
    94	| class 偏差 | 无（89/2/1 与勘探预期一致，脚本 `class_deviation` 字段为空） |
    95	| 负例门（round-1 整改自证） | `--out`==`--dlq` → exit 2 拒写、DLQ 完好；transcripts 根缺失 → exit 2 拒诊；sha 匹配但长度不符（round-1 HIGH-1 反例①）→ anomaly/unrecoverable；坏 JSON 行/空行 → unparseable 逐行入台账不拒诊 |
    96	| 负例门（round-2 整改自证） | **hardlink** 指向 DLQ 的 --out → exit 2 + DLQ sha 不变；**case-only 别名**（`DLQ.jsonl`）→ exit 2 + DLQ 完好；**anomaly + episode_body_full 组合**（sha 对但长度 999）→ anomaly/unrecoverable（不再翻案 byte_exact）；**chmod 000 根** → exit 2 拒诊；**symlink 逃逸**（根内 .jsonl → 根外 .txt）→ match_count=0/unrecoverable；正例回归：真实唯一命中仍 approximate |
    97	
    98	## §7b Codex round-1 整改记录（BLOCKED → 全项整改）
   163	round-4 整改后第四次全量重跑：**92 条、class 89/2/1、三态 4/88/0（unverifiable 0）、重复簇 6/29、shasum 不变——四轮整改数字全程未变**。
   164	
   165	## §7f Codex round-5 复审整改记录（3/8 CLOSED → 9 项全部整改）
   166	
   167	round-5 用更深的静态反例继续推翻"闭合"，提出 2 BLOCKER / 2 HIGH / 2 MEDIUM / 3 LOW，逐条整改并实测：
   168	
   169	- **BLOCKER①（token 冲突/无 token 时扫描前早退 → 候选不进保护集）**：`--out` 指向冲突组的候选 transcript 仍可无竞态截断。**整改**：`resolve_group_attribution()` 重写为**先扫描后判定**——无条件为每个 token 扫描收集候选进 `all_candidate_paths`（保护集口径），再做冲突/唯一性判定；候选 `stat` 失败不再 `continue` 吞掉而是 exit 2（保护集不完整即拒绝写出）。实测：冲突候选作 `--out` → exit 2、文件 sha 不变。
   170	- **BLOCKER②（qa_metrics.db 身份未绑定实际读取）**：仍是早期 path-stat + SQLite 稍后按路径重开。**整改**：`probe_qa_metrics()` 改 `os.open(O_RDONLY|O_NOFOLLOW|O_NONBLOCK)` 取 fstat 身份 + `S_ISREG` 门 → SQLite 打开后**复核路径身份仍等于该身份**，不等即 `identity_changed_..._refused`；身份入保护集。本次运行 `file_identity_verified: true`。
   171	- **HIGH①（anomaly 吞掉不可见性）**：`anomaly→unrecoverable` 排在 conflict 判断之前，`anomaly + 扫描受阻` 仍被假终态化。**整改**：判定链改为**可见性优先**——归因不可核验时无论 inline 状态一律 `unverifiable`，basis 逐条写明原因（无 token / token 冲突 / 扫描受阻 / 候选 stat 失败 / 不可读候选 / 多命中 ambiguous），并附注 inline 是否也 anomaly。实测：anomaly+不可读子树 → `unverifiable`。
   172	- **HIGH②（`fchmod` 先于 protected-id 检查）**：`--out` 指向受保护的 0644 输入时，会**先把只读输入权限改成 0600** 再拒绝——字节没截断但输入已被修改。**整改**：碰撞检查前移到 `fchmod` 之前。实测：mode 644 → 644 不变。
   173	- **MEDIUM（QA DB 无特殊文件门）**：随 BLOCKER② 一并加 `S_ISREG` + `O_NONBLOCK`。
   174	- **MEDIUM（无 token 未扫描即判不可恢复）**：改为 `unverifiable` + `no_token` 标记（见 HIGH①）。
   175	- **LOW ×3**：单独 `b"\n"` 现算 1 个空行（实测 `line_count=1`）；`errors="replace"` 改 **strict encode**（JSON escaped lone surrogate 不能再构造假 `full_verified`）；`bool` 是 `int` 子类 —— `episode_body_length=True` 现被长度门拒绝（实测判 anomaly）。
   176	
   177	**归因冲突计数由 0 变为 3（如实说明）**：round-5 起"名字不含 session token"被诚实标记为 `no_token`（未做归因扫描），命中的正是 3 条 `callout_annotation` 记录。它们 inline 正文全量、sha 对账通过，**不依赖 transcript**，故仍判 `byte_exact`——三态分布不变（4/88/0/0），88 条 approximate 仍全部为唯一 transcript 命中。这是标注口径变诚实，不是结论变化。
   178	
   179	round-5 整改后第五次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变——五轮整改数字全程未变**。

**Planning ledger record extraction range**
exec
/bin/zsh -lc "nl -ba _bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json | sed -n '179,270p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
   179	 "records": [
   180	  {
   181	   "stable_key": {
   182	    "line_no": 1,
   183	    "sha256_prefix": "7e33da5e96e6239f",
   184	    "request_id": "281466113679440"
   185	   },
   186	   "name": "callout_annotation:P0 final 验证",
   187	   "group_id": "vault:default",
   188	   "source_description": "callout-annotation-record",
   189	   "error_type": "EntityTypeValidationError",
   190	   "error_excerpt": "name cannot be used as an attribute for LearningConcept as it is a protected attribute name.",
   191	   "failed_at": "2026-05-14T08:20:15.793508+00:00",
   192	   "reference_time": "2026-05-14T08:20:10.506386+00:00",
   193	   "class": "schema_entity_type",
   194	   "episode_body_length": 180,
   195	   "episode_body_sha256": "7e33da5e96e6239f5584beb0011760bae646b59b09417fb72bd4c5c4b328fea4",
   196	   "inline_state": "full_verified",
   197	   "sha_check": "pass",
   198	   "session_token": null,
   199	   "transcript_paths": [],
   200	   "transcript_match_count": 0,
   201	   "attribution_conflict": true,
   202	   "recoverability": "byte_exact",
   203	   "recoverability_basis": "inline 正文全量：sha256 重算与声明一致且长度精确匹配"
   204	  },
   205	  {
   206	   "stable_key": {
   207	    "line_no": 2,
   208	    "sha256_prefix": "b91bf262cadab596",
   209	    "request_id": "281466014769488"
   210	   },
   211	   "name": "callout_annotation:递归 base case 概念",
   212	   "group_id": "vault:default",
   213	   "source_description": "callout-annotation-record",
   214	   "error_type": "EntityTypeValidationError",
   215	   "error_excerpt": "created_at cannot be used as an attribute for LearningTip as it is a protected attribute name.",
   216	   "failed_at": "2026-05-14T08:25:15.775179+00:00",
   217	   "reference_time": "2026-05-14T08:25:06.180046+00:00",
   218	   "class": "schema_entity_type",
   219	   "episode_body_length": 150,
   220	   "episode_body_sha256": "b91bf262cadab596d55224b87c96af09b28025996b0040883b58a025cf2ebd4a",
   221	   "inline_state": "full_verified",
   222	   "sha_check": "pass",
   223	   "session_token": null,
   224	   "transcript_paths": [],
   225	   "transcript_match_count": 0,
   226	   "attribution_conflict": true,
   227	   "recoverability": "byte_exact",
   228	   "recoverability_basis": "inline 正文全量：sha256 重算与声明一致且长度精确匹配"
   229	  },
   230	  {
   231	   "stable_key": {
   232	    "line_no": 3,
   233	    "sha256_prefix": "55b1b793b99778eb",
   234	    "request_id": "281466427090256"
   235	   },
   236	   "name": "callout_annotation:递归 base case",
   237	   "group_id": "vault:default",
   238	   "source_description": "callout-annotation-record",
   239	   "error_type": "GroupIdValidationError",
   240	   "error_excerpt": "group_id \"vault:default\" must contain only alphanumeric characters, dashes, or underscores",
   241	   "failed_at": "2026-05-14T08:31:54.970785+00:00",
   242	   "reference_time": "2026-05-14T08:31:50.054921+00:00",
   243	   "class": "group_id_format",
   244	   "episode_body_length": 131,
   245	   "episode_body_sha256": "55b1b793b99778eb0c117b65ad14e4a77dd045d4f50163c0274054b6adaf4da2",
   246	   "inline_state": "full_verified",
   247	   "sha_check": "pass",
   248	   "session_token": null,
   249	   "transcript_paths": [],
   250	   "transcript_match_count": 0,
   251	   "attribution_conflict": true,
   252	   "recoverability": "byte_exact",
   253	   "recoverability_basis": "inline 正文全量：sha256 重算与声明一致且长度精确匹配"
   254	  },
   255	  {
   256	   "stable_key": {
   257	    "line_no": 4,
   258	    "sha256_prefix": "89199bd0eeb62ce2",
   259	    "request_id": "281466685033808"
   260	   },
   261	   "name": "conversation_distillation:Distilled summary for node session:e8eff",
   262	   "group_id": "vault:canvas_vault",
   263	   "source_description": "canvas_learning:conversation_distillation",
   264	   "error_type": "BadRequestError",
   265	   "error_excerpt": "Error code: 400 - {'error': {'code': 400, 'message': 'request (16998 tokens) exceeds the available context size (16384 t",
   266	   "failed_at": "2026-08-08T20:51:14.997406+00:00",
   267	   "reference_time": "2026-08-08T20:49:23.667531+00:00",
   268	   "class": "budget_400",
   269	   "episode_body_length": 443,
   270	   "episode_body_sha256": "89199bd0eeb62ce297ffd2e2df6df339fa6a1cd6e111b2c37cf0574cf7cdacd8",

**Verifying artifact commit integrity**
**Confirming hash origin and stale evidence**
**Analyzing SQLite connection identity handling**
**Analyzing identity verdict logic**
**Evaluating output file handling and FIFO behavior**
**Identifying blocking FIFO open causing hang**
**Analyzing directory permission effects on traversal**
**Identifying unresolved token conflict and scan error issues**
**Confirming verification logic and file operation order**
**Verifying file mode and encoding checks**
**Assessing JSON output surrogate risks**
**Verifying ledger source and permissions**
**Planning ledger path re-globbing**
**Designing token-based file counting**
**Executing token match count scan**
exec
/bin/zsh -lc "python3 -B -c 'import json,os,stat; from pathlib import Path; d=json.loads(Path(\"_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json\").read_text()); ts=sorted({r[\"session_token\"] for r in d[\"records\"] if r[\"recoverability\"]==\"approximate\"}); root=Path.home()/\".claude\"/\"projects\"; counts={t:0 for t in ts}; errors=[]; 
def onerr(e): errors.append(type(e).__name__)
for dp,dn,fns in os.walk(root,onerror=onerr,followlinks=False):
 for fn in fns:
  if not fn.endswith(\".jsonl\"): continue
  for t in ts:
   if fn.startswith(t):
    p=os.path.join(dp,fn)
    try:
     s=os.lstat(p)
     if stat.S_ISREG(s.st_mode) and not stat.S_ISLNK(s.st_mode) and os.access(p,os.R_OK): counts[t]+=1
    except OSError as e: errors.append(type(e).__name__)
print(json.dumps({\"token_count\":len(ts),\"match_count_distribution\":{str(k):list(counts.values()).count(k) for k in sorted(set(counts.values()))},\"scan_errors\":errors}))'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 47ms:
{"token_count": 7, "match_count_distribution": {"1": 7}, "scan_errors": []}

**Verifying group counts and line consistency**
**Checking QA database and source consistency**
exec
/bin/zsh -lc "rg -n 'episode_body.*\\[:200\\]|episode_body_full|DEAD_LETTER_STORE_FULL_BODY' backend/app backend | sed -n '1,120p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
backend/scripts/census_dead_letter_episodes.py:37:  - episode_body_full 若在盘（DEAD_LETTER_STORE_FULL_BODY 开启时生产可写):
backend/scripts/census_dead_letter_episodes.py:138:    """episode_body_full 在盘且 sha **与长度**双门对账通过（生产 opt-in 字段，当前 live 0 条）。
backend/scripts/census_dead_letter_episodes.py:143:    full = rec.get("episode_body_full")
backend/scripts/census_dead_letter_episodes.py:523:            basis = "episode_body_full 在盘且 sha256+长度双门对账通过（DEAD_LETTER_STORE_FULL_BODY 生产 opt-in 字段）"
backend/app/services/episode_worker.py:108:            "episode_body": self.episode_body[:200],  # truncate for logging
backend/app/services/episode_worker.py:215:      - Only store ``episode_body_full`` when env ``DEAD_LETTER_STORE_FULL_BODY``
backend/app/services/episode_worker.py:231:        flag = (os.environ.get("DEAD_LETTER_STORE_FULL_BODY") or "").strip().lower()
backend/app/services/episode_worker.py:237:        Privacy: episode_body_full is omitted unless DEAD_LETTER_STORE_FULL_BODY=true.
backend/app/services/episode_worker.py:254:            record["episode_body_full"] = _redact(task.episode_body)
backend/app/services/episode_worker.py:108:            "episode_body": self.episode_body[:200],  # truncate for logging
backend/app/services/episode_worker.py:215:      - Only store ``episode_body_full`` when env ``DEAD_LETTER_STORE_FULL_BODY``
backend/app/services/episode_worker.py:231:        flag = (os.environ.get("DEAD_LETTER_STORE_FULL_BODY") or "").strip().lower()
backend/app/services/episode_worker.py:237:        Privacy: episode_body_full is omitted unless DEAD_LETTER_STORE_FULL_BODY=true.
backend/app/services/episode_worker.py:254:            record["episode_body_full"] = _redact(task.episode_body)

**Verifying SHA and length derivation**
exec
/bin/zsh -lc "nl -ba backend/app/services/episode_worker.py | sed -n '90,115p;205,260p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
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

**Identifying hash encoding and redaction issues**
**Preparing precise memory and skill citations**
exec
/bin/zsh -lc "nl -ba /Users/Heishing/.codex/memories/MEMORY.md | sed -n '155,188p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
exec
/bin/zsh -lc "nl -ba /Users/Heishing/.codex/memories/skills/canvas-adversarial-audit/SKILL.md | sed -n '12,50p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
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

 succeeded in 0ms:
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

**Clarifying citation rules for MEMORY and skill ranges**
**Planning final git diff and mtime check**
exec
/bin/zsh -lc "stat -f '%N size=%z mtime=%Sm' -t '%Y-%m-%dT%H:%M:%S%z' _bmad-output/审查/codex-review-CARD-G4-9-round6.md" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
_bmad-output/审查/codex-review-CARD-G4-9-round6.md size=425092 mtime=2026-08-28T20:43:00+0800

exec
/bin/zsh -lc 'git rev-parse HEAD' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
4c125f19dd6b189c7dcdfa3bff686cbd494a11cc

exec
/bin/zsh -lc 'git diff --no-ext-diff --stat' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead

exec
/bin/zsh -lc 'git status --short --branch' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
## card/s5-census
?? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round6.md"

**Detecting unexpected file growth**
**Identifying automatic session transcript logging**
**Verifying no tracked file modifications**
mcp: sequential-thinking/sequentialthinking started
mcp: sequential-thinking/sequentialthinking (completed)
mcp: sequential-thinking/sequentialthinking started
mcp: sequential-thinking/sequentialthinking (completed)
**Assessing stale receipt severity**
**Classifying new and residual findings**
mcp: sequential-thinking/sequentialthinking started
mcp: sequential-thinking/sequentialthinking (completed)
**Completing update plan**
codex
复核已收束：冻结台账的 exact-byte 数字成立，但生成器的只读安全闭包仍失败。当前逐项为 6/9 狭义整改 CLOSED、3/9 NOT-CLOSED；两个残留路径都能触达报告/UAT 明确承诺的“零写入”，因此不是范围外加固。接下来只整理终裁，不会写审查文件。
已完成 commit/生产入口静态复核、高危交叉验证、live exact-byte 台账复算与证据一致性检查；全程未主动修改文件。
  ✓ 读取既有审计记忆与 Graphiti 事实，锁定 round-5 判项和审阅边界
  ✓ 核验 4c125f19 diff 与八类整改的生产入口语义
  ✓ 设计并执行只读静态反例/隔离复算，逐项判定可绕过性
  ✓ 从源数据独立复算 92 条台账、分类、精度、冲突与重复簇
  ✓ 汇总 CLOSED/NOT-CLOSED、新发现分级与最终验收裁定
**Planning final Chinese summary structure**
**Detailing blocker statuses with code citations**
**Analyzing os.walk enumeration failure implications**
**Confirming SQLite default open mode is read-write-create**
**Clarifying no_token conflict artifact meaning**
**Clarifying attribution_conflict categories**
**Including stat_failures rationale and severity summary**
**Confirming no file edits detected**
**Clarifying automatic session capture growth**
**Flagging no file modification compliance**
**Designing local link formatting with Chinese segments**
**Clarifying link and label formatting rules**
**Summarizing audit closure and severity counts**
**Noting attribution conflict handling**
**Planning memory citation strategy**
codex
总裁定：**仍阻断，CARD-G4-9 round-6 不可验收。**

结论需拆开：

- **冻结台账数字 PASS**：92 条 ledger 可以采信。
- **生成器只读安全闭包 FAIL**：仍有 2 个 BLOCKER，能违反报告/UAT 的“纯只读、零写入”承诺。
- 按 7 个顶层整改计为 **4/7 CLOSED**；把 LOW×3 拆开则为 **6/9 CLOSED**。

### 逐项裁定

| 整改项 | 裁定 | 复核结果 |
|---|---|---|
| 1. token 冲突/无 token 先扫描 | **NOT-CLOSED · BLOCKER** | 可枚举 token-conflict 候选确会先进入保护集；但扫描受阻只标 `unverifiable`，不会停止写出。根可读、子目录 `0333`（不可列举但可按名穿越）、其中存在匹配 transcript `T` 时，`os.walk` 只能记录错误，`T` 不进保护集，`--out=T` 最终仍可被打开并截断。[扫描入口](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:201)、[scan_errors 判定](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:241)、[保护循环](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:663)、[输出打开](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:686)。无 token 时 `if uniq` 仍完全不扫描，`all_candidate_paths=[]`。 |
| 2. QA DB 身份绑定 | **NOT-CLOSED · BLOCKER** | 验证 fd 在 [line 288](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:288) 已关闭；SQLite 随后按路径另开，[后置 `os.stat(path)`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:295)并不能证明连接打开的是同一 inode。A→B→A 的 ABA 可通过；`protected_ids` 仍只加入 A，[line 618](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:618)。 |
| 3. visibility 优先于 anomaly | **CLOSED** | byte-exact 两支之后，`attribution_conflict→unverifiable` 已位于 `anomaly→unrecoverable` 前：[exact](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:518)、[conflict](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:524)、[anomaly](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:542)。exact 先行是合理例外，因为不依赖 transcript。 |
| 4. fchmod 顺序 | **CLOSED（局部）** | 实际顺序为碰撞检查 [698](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:698) → `fchmod` [706](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:706) → `ftruncate` [707](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:707)。但它不能补救项目 1/2 导致的保护集漏项。 |
| 5. QA DB 特殊文件门 | **NOT-CLOSED / PARTIAL · MEDIUM** | 第一次 `O_NONBLOCK+S_ISREG` 能拒绝稳定 FIFO/设备；但 fd 随即关闭，SQLite 第二次按路径打开没有这些门。regular→FIFO/symlink 替换仍可绕过并在 `connect()` 内阻塞。 |
| 6. no_token→unverifiable | **CLOSED（行为）** | 非 byte-exact 的 no-token 记录会进入 `unverifiable`；full-verified/no-token 仍为 byte-exact，语义正确。[no_token](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:228)。但 `no_token` 未写入 ledger，见下方 LOW。 |
| 7a. 单独 LF | **CLOSED** | 纯内存复算：`b""→0`、`b"\n"→1`、`b"\n\n"→2`、`b"{}\n"→1`。[实现](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:85)。 |
| 7b. strict encode | **CLOSED（原反例）** | lone `U+D800` 配旧 replace-hash 现为 `anomaly/FAIL`，full-body 为 `False`；正常 emoji 正控仍通过。[inline](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:124)、[full-body](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:151)。 |
| 7c. bool 长度门 | **CLOSED** | `True/False/1.0` 均被拒，整数 `1` 正控通过。[inline 门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:129)、[full-body 门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:148)。 |

### QA DB 新的确定性 BLOCKER

[line 290](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:290)直接拼接：

```python
uri = f"file:{db_path}?mode=ro"
```

合法文件名中的 `?`/`#` 未转义。例如验证对象是 `/x/qa#tag`，SQLite URI 实际 path 是 `/x/qa`，`#tag?mode=ro` 被当作 fragment 忽略；这不仅打开不同对象，还丢失 `mode=ro`，可能隐式创建数据库。SQLite 官方要求把普通文件名中的 `?/#` 转义，并规定 fragment 被忽略；Python `connect()` 默认可创建不存在的数据库。[SQLite URI 规则](https://sqlite.org/uri.html#the_uri_path)、[Python sqlite3.connect](https://docs.python.org/3/library/sqlite3.html#sqlite3.connect)。

这是无需竞态的零写入反例，足以单独维持 BLOCKER。

### 台账独立复算

未把生成器当 oracle，直接从 live DLQ exact bytes 重写分帧、分类、SHA/长度、分组和聚簇算法：

- SHA-256：`3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590`
- `99,915 bytes`；92 records；unparseable 0
- class：`89 / 2 / 1`
- inline：4 full_verified / 88 truncated / 0 anomaly
- recoverability：4 byte_exact / 88 approximate / 0 unverifiable / 0 unrecoverable
- 重复簇：6/29，簇大小 `16,4,3,2,2,2`
- 与提交 ledger 的逐条 class/inline/SHA 状态：0 mismatch
- 7 个 session token 当前各恰好 1 个 regular、可读、非 symlink transcript；仅检查元数据，未读正文
- QA DB 当前只读复查仍为 `qa_error_logs=0`，查询后 SHA 不变且未产生 sidecar

汇总可见于 [ledger:40](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:40)。

`attribution_conflict=3` 与 `byte_exact=4 / unverifiable=0` **诚实且自洽**：独立分组确认只有行 1–3 的组完全无 token；它们正是三个 callout，且 inline SHA+长度双门通过，[ledger:179](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:179)。归因不可用与正文已能逐字节恢复是两个独立维度。

### 其他新发现

- **MEDIUM — 证据包漂移**：`grep-selfattest.txt` 仍标注 round-4、旧脚本 SHA `f275…` 和旧行号，[evidence:1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:1)；receipt 只记录到 `d2827a6d`，[receipt:10](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt:10)，未绑定当前 `4c125f19`。报告/UAT 对“当前证据包”的声明不成立。
- **LOW — ledger 不自描述**：`no_token` 仅存在于内存；记录只序列化笼统的 `attribution_conflict=true`，无法区分缺 token、token 冲突或多命中。
- **LOW — 其余字段 surrogate DoS**：strict encode 只覆盖 body/full-body；`name/error/group_id` 等若含 escaped lone surrogate，`ensure_ascii=False` 的 UTF-8 写出仍会抛错并拒绝整次 census。
- **LOW — `stat_failures` basis 基本不可达**：`os.path.islink/isfile` 通常把 stat 的 `OSError` 转为 `False`，不会进入 [except 分支](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:212)。枚举到的候选最终仍会在后置 stat 失败时 exit 2，因此不是额外截断绕过。

审阅锚定 `HEAD=4c125f19dd6b189c7dcdfa3bff686cbd494a11cc`。没有 tracked diff，也未创建临时 fixture、未读 transcript 正文或 Vault。`graphiti-canvas` 与 Context7 本轮未暴露；Sequential Thinking 已执行，SQLite 语义改用官方文档核对。开始前已存在的未跟踪 round-6 会话记录由环境记录器持续增长；我未写入、删除或清理它。


tokens used
202,210
总裁定：**仍阻断，CARD-G4-9 round-6 不可验收。**

结论需拆开：

- **冻结台账数字 PASS**：92 条 ledger 可以采信。
- **生成器只读安全闭包 FAIL**：仍有 2 个 BLOCKER，能违反报告/UAT 的“纯只读、零写入”承诺。
- 按 7 个顶层整改计为 **4/7 CLOSED**；把 LOW×3 拆开则为 **6/9 CLOSED**。

### 逐项裁定

| 整改项 | 裁定 | 复核结果 |
|---|---|---|
| 1. token 冲突/无 token 先扫描 | **NOT-CLOSED · BLOCKER** | 可枚举 token-conflict 候选确会先进入保护集；但扫描受阻只标 `unverifiable`，不会停止写出。根可读、子目录 `0333`（不可列举但可按名穿越）、其中存在匹配 transcript `T` 时，`os.walk` 只能记录错误，`T` 不进保护集，`--out=T` 最终仍可被打开并截断。[扫描入口](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:201)、[scan_errors 判定](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:241)、[保护循环](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:663)、[输出打开](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:686)。无 token 时 `if uniq` 仍完全不扫描，`all_candidate_paths=[]`。 |
| 2. QA DB 身份绑定 | **NOT-CLOSED · BLOCKER** | 验证 fd 在 [line 288](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:288) 已关闭；SQLite 随后按路径另开，[后置 `os.stat(path)`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:295)并不能证明连接打开的是同一 inode。A→B→A 的 ABA 可通过；`protected_ids` 仍只加入 A，[line 618](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:618)。 |
| 3. visibility 优先于 anomaly | **CLOSED** | byte-exact 两支之后，`attribution_conflict→unverifiable` 已位于 `anomaly→unrecoverable` 前：[exact](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:518)、[conflict](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:524)、[anomaly](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:542)。exact 先行是合理例外，因为不依赖 transcript。 |
| 4. fchmod 顺序 | **CLOSED（局部）** | 实际顺序为碰撞检查 [698](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:698) → `fchmod` [706](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:706) → `ftruncate` [707](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:707)。但它不能补救项目 1/2 导致的保护集漏项。 |
| 5. QA DB 特殊文件门 | **NOT-CLOSED / PARTIAL · MEDIUM** | 第一次 `O_NONBLOCK+S_ISREG` 能拒绝稳定 FIFO/设备；但 fd 随即关闭，SQLite 第二次按路径打开没有这些门。regular→FIFO/symlink 替换仍可绕过并在 `connect()` 内阻塞。 |
| 6. no_token→unverifiable | **CLOSED（行为）** | 非 byte-exact 的 no-token 记录会进入 `unverifiable`；full-verified/no-token 仍为 byte-exact，语义正确。[no_token](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:228)。但 `no_token` 未写入 ledger，见下方 LOW。 |
| 7a. 单独 LF | **CLOSED** | 纯内存复算：`b""→0`、`b"\n"→1`、`b"\n\n"→2`、`b"{}\n"→1`。[实现](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:85)。 |
| 7b. strict encode | **CLOSED（原反例）** | lone `U+D800` 配旧 replace-hash 现为 `anomaly/FAIL`，full-body 为 `False`；正常 emoji 正控仍通过。[inline](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:124)、[full-body](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:151)。 |
| 7c. bool 长度门 | **CLOSED** | `True/False/1.0` 均被拒，整数 `1` 正控通过。[inline 门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:129)、[full-body 门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:148)。 |

### QA DB 新的确定性 BLOCKER

[line 290](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:290)直接拼接：

```python
uri = f"file:{db_path}?mode=ro"
```

合法文件名中的 `?`/`#` 未转义。例如验证对象是 `/x/qa#tag`，SQLite URI 实际 path 是 `/x/qa`，`#tag?mode=ro` 被当作 fragment 忽略；这不仅打开不同对象，还丢失 `mode=ro`，可能隐式创建数据库。SQLite 官方要求把普通文件名中的 `?/#` 转义，并规定 fragment 被忽略；Python `connect()` 默认可创建不存在的数据库。[SQLite URI 规则](https://sqlite.org/uri.html#the_uri_path)、[Python sqlite3.connect](https://docs.python.org/3/library/sqlite3.html#sqlite3.connect)。

这是无需竞态的零写入反例，足以单独维持 BLOCKER。

### 台账独立复算

未把生成器当 oracle，直接从 live DLQ exact bytes 重写分帧、分类、SHA/长度、分组和聚簇算法：

- SHA-256：`3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590`
- `99,915 bytes`；92 records；unparseable 0
- class：`89 / 2 / 1`
- inline：4 full_verified / 88 truncated / 0 anomaly
- recoverability：4 byte_exact / 88 approximate / 0 unverifiable / 0 unrecoverable
- 重复簇：6/29，簇大小 `16,4,3,2,2,2`
- 与提交 ledger 的逐条 class/inline/SHA 状态：0 mismatch
- 7 个 session token 当前各恰好 1 个 regular、可读、非 symlink transcript；仅检查元数据，未读正文
- QA DB 当前只读复查仍为 `qa_error_logs=0`，查询后 SHA 不变且未产生 sidecar

汇总可见于 [ledger:40](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:40)。

`attribution_conflict=3` 与 `byte_exact=4 / unverifiable=0` **诚实且自洽**：独立分组确认只有行 1–3 的组完全无 token；它们正是三个 callout，且 inline SHA+长度双门通过，[ledger:179](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:179)。归因不可用与正文已能逐字节恢复是两个独立维度。

### 其他新发现

- **MEDIUM — 证据包漂移**：`grep-selfattest.txt` 仍标注 round-4、旧脚本 SHA `f275…` 和旧行号，[evidence:1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:1)；receipt 只记录到 `d2827a6d`，[receipt:10](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt:10)，未绑定当前 `4c125f19`。报告/UAT 对“当前证据包”的声明不成立。
- **LOW — ledger 不自描述**：`no_token` 仅存在于内存；记录只序列化笼统的 `attribution_conflict=true`，无法区分缺 token、token 冲突或多命中。
- **LOW — 其余字段 surrogate DoS**：strict encode 只覆盖 body/full-body；`name/error/group_id` 等若含 escaped lone surrogate，`ensure_ascii=False` 的 UTF-8 写出仍会抛错并拒绝整次 census。
- **LOW — `stat_failures` basis 基本不可达**：`os.path.islink/isfile` 通常把 stat 的 `OSError` 转为 `False`，不会进入 [except 分支](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:212)。枚举到的候选最终仍会在后置 stat 失败时 exit 2，因此不是额外截断绕过。

审阅锚定 `HEAD=4c125f19dd6b189c7dcdfa3bff686cbd494a11cc`。没有 tracked diff，也未创建临时 fixture、未读 transcript 正文或 Vault。`graphiti-canvas` 与 Context7 本轮未暴露；Sequential Thinking 已执行，SQLite 语义改用官方文档核对。开始前已存在的未跟踪 round-6 会话记录由环境记录器持续增长；我未写入、删除或清理它。


