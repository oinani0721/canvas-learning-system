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
session id: 01a0486b-0c60-7281-bde2-b9c3cec54576
--------
user
CARD-G4-9 round-7 复审（静态审阅 + 只读复算，禁改任何文件）。你 round-6 裁定 6/9 CLOSED，两项 BLOCKER 揭示了根因：--out 保护集依赖枚举完整性（0333 不可列举目录内的 transcript、QA DB inode ABA 都能挫败它）。开发方接受该判断，做了**架构级修复**并以 commit 5b371253 + 后续 receipt commit 提交：
1. 新增**不依赖枚举的路径层防御**（main() 开头，早于任何读取）：--out 的 realpath 若等于 transcripts 根或落在其下 → 无条件 exit 2（恢复源区域整体禁写）；--out 的 realpath 若等于 --dlq/--compare/--qa-metrics-db 任一 realpath → exit 2。与既有 inode 层构成双保险。
2. QA DB 验证 fd 改为**保持打开**至 SQLite 连接建立并复核完毕（原为验证后即关闭），连接后二次 fstat 校验身份未变且 st_nlink != 0。
3. no_token 分支改为**也遍历**（原 if uniq 完全不扫描，候选进不了 all_candidate_paths）。
4. 证据包 grep-selfattest.txt 重生成（内嵌当前脚本 sha256 + 生成时点声明）；receipt 补至当前 commit 链。
5. ledger 新增 attribution_conflict_reason 自描述；json.dumps 对 lone surrogate 回退 ensure_ascii=True 并标注。
请逐项复核是否闭合，并针对路径层防御设计新反例（如 --out 位于 transcripts 根外但通过 symlink/hardlink 指入根内的文件、transcripts 根本身是 symlink、相对路径与 .. 组合、TOCTOU 把 --out 在检查后换成指入根内的链接）。同时复核台账仍为 92 条 / class 89-2-1 / byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0 / 重复簇 6/29 / unparseable 0 / attribution_conflict 3(no_token)。逐项 CLOSED/NOT-CLOSED + 总裁定 + 新发现分级；若可验收请明确说明。
**Planning read-only repository audit**
**Assessing available tools and memory for audit**
**Enforcing strict read-only execution**
codex
我会按“只读、fail-closed、生产入口优先”复审：先核对当前 checkout/commit 链与 round-6 基线，再分三条并行轨复算代码闭合、证据/receipt、以及 92 条台账与新反例；不会运行会写文件或数据库的命令。Graphiti/Sequential Thinking 若当前环境未暴露，我会在结论里明确记为工具限制。
**Planning tool usage and memory pass**
**Planning concurrent execution of commands**
exec
/bin/zsh -lc "rg -n -i 'CARD-G4-9|round-6|card-s5-census|census|annotation-truth' /Users/Heishing/.codex/memories/MEMORY.md" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
84:- Missing handoff is a hard wait condition, not implied approval. `ps` was sandbox-denied (`operation not permitted`); mark the census unavailable rather than successful. [Task 1]
128:# Task Group: Canvas Learning System Phase 0A annotation-truth governance ready queue
140:- GOV-01-VERIFIED, Phase-0A, A01, A02, A03, annotation-truth-ledger-v2, AtomicAnnotation, boundary receipt, scanner, [HANDOFF:CODEX-PHASE0A-READY]
144:- “只读” means no repo/index/ref/worktree/OpenSpec writes, scanner/final census, A01/A02 instantiation, private/Vault/network/Graphiti access, or product implementation. Provide ready/blocked status, exact evidence, batch order, and Claude/Codex matrix. [Task 1]
148:- Order: `GOV-01-VERIFIED clean candidate → OpenSpec → schema/checker → A01 boundary receipt → no-cap census/A01 snapshot → A02 seed/replay → ChatGPT blind review → Codex reconciliation → user dispute/waiver → joint A01/A02 completion → A03 candidate → user exact-byte lock`. A01 cannot complete independently of A02. [Task 1]
153:- Expired `pending-user-confirmation` receipt/envelope is not authority. New exact envelope/digest/challenge is needed. The existing `scripts/bmad/scan_feedback.py` did not cover actual output; freeze a new scanner contract/no-write boundary before census. [Task 1]

Round-7 只读复审按独立证据链推进；不执行任何会修改文件或数据库的命令。
  → 核对 checkout、commit/receipt 链及 round-6 基线
  • 静态审阅五项修复及生产入口控制流
  • 设计并只读验证路径、inode、TOCTOU 新反例
  • 从原始工件独立复算台账与证据包指标
  • 交叉核验后给出逐项 CLOSED/NOT-CLOSED 与总裁定
mcp: sequential-thinking/sequentialthinking started
mcp: sequential-thinking/sequentialthinking (completed)
**Searching audit and governance references**
exec
/bin/zsh -lc "rg -n -C 5 'canvas-adversarial-audit|adversarial security review|exact-object|CACHE-PREP' /Users/Heishing/.codex/memories/MEMORY.md" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
83-
84-- Missing handoff is a hard wait condition, not implied approval. `ps` was sandbox-denied (`operation not permitted`); mark the census unavailable rather than successful. [Task 1]
85-- Freeze reviewer rejected the lab: missing reproducible full ordinal-9595 input, stdlib origin-byte hashes, exact freeze execution contract/argv/env/cwd enforcement, post-chmod mode proof, and final fsync/reopen/short-write proof. Do not run `freeze_package.py` until a new stable package independently addresses them. [Task 2]
86-- Do not embed private transcript/session paths in public/minimal package artifacts. [Task 2]
87-
88:# Task Group: Canvas Learning System GOV01 exact-object and CACHE-PREP atomicity audit
89:scope: Isolated, read-only verification of GOV01 bundle chains and static exact-object audit of CACHE-PREP-V1 ADOPT/live-cache atomicity.
90-applies_to: cwd=/private/tmp/cls-gov01-a4-v1/planning-ro; reuse_rule=recompute every bundle, manifest, commit/tree/blob, source range, and authorization in an isolated inspection repo; do not run production/FETCH/ADOPT modes or access real cache/Vault/network.
91-
92-## Task 1: GOV01 A4 repair/micro chain audit, structurally verified but broader readiness partial
93-
94-### rollout_summary_files
--
97-
98-### keywords
99-
100-- GOV01-A4, d3167d06, c1990df5, 2cf9cbf0, git bundle verify, exact bytes, isolated bare repo, review binding, canvas-vault
101-
102:## Task 2: CACHE-PREP-V1 ADOPT/live-cache atomicity R2, FAIL / BLOCKED
103-
104-### rollout_summary_files
105-
106-- rollout_summaries/2026-08-23T10-38-57-0pt3-gov01_cache_prep_r2_read_only_exact_object_audit.md (cwd=/private/tmp/cls-gov01-a4-v1/planning-ro, rollout_path=/Users/Heishing/.codex/sessions/2026/08/23/rollout-2026-08-23T18-38-57-01a02e33-bb2c-7b93-85d0-3c50119edfad.jsonl, updated_at=2026-08-24T11:49:59+00:00, thread_id=01a02e33-bb2c-7b93-85d0-3c50119edfad, outcome=fail; 3 BLOCKER / 2 HIGH)
107-
108-### keywords
109-
110:- CACHE-PREP-V1, ADOPT.py, live-cache, per-digest claim, restart reconciliation, same-FD readback hash, RENAME_EXCL, O_EXCL, parent fsync, TOCTOU, _cacache/index-v5
111-
112-## User preferences
113-
114-- For an “独立、只读审查”, do not trust W0, Claude, or a tainted publication manifest: recompute handoff bundle, manifest, exact bytes, Git range, and bindings; report exact `file:line`, severity, PASS/PARTIAL/FAIL. [Task 1][Task 2]
115-- No production mode, private/Vault/key/cache/state reads, network, fixtures, repository writes, or Git-history changes. [Task 1][Task 2]
--
120-- Static ADOPT/LIVE code had FD-relative anchoring/nofollow, owner/mode/nlink checks, no-overwrite, file/parent fsync, and offline no-network/index/lifecycle closure for ADOPT/LIVE. Candidate-wide zero-network is invalid because FETCH contains HTTPS code. [Task 2]
121-- Required closure: persistent per-digest adopter claim/journal and restart reconciliation; valid-existing/invalid-existing/missing branches; same-FD write/readback hash; post-open parent/ancestor identity checks through rename; no-replace publication and parent durability seal; bounded `scandir` enumeration and durable partial-mutation/residue evidence on unexpected exceptions. [Task 2]
122-
123-## Failures and how to do differently
124-
125:- `O_EXCL` plus `RENAME_EXCL` does not establish unique adopter or crash recovery. R2 found fixed temp `EEXIST` after pre-rename crash, nonsealed post-rename/pre-parent-fsync restart, no durable claim/reconciler, no write-side same-FD readback, and mutation-parent TOCTOU. Therefore `[ROLLUP:CACHE-PREP-V1:S3:R2-TECH] FAIL / BLOCKED`. [Task 2]
126-- Do not infer cache-object adoption from direct-SRI admission or node_modules protections. [Task 2]
127-
128-# Task Group: Canvas Learning System Phase 0A annotation-truth governance ready queue
129-scope: Read-only, fail-closed planning for GOV-01-VERIFIED and A01→A02→A03. It is a governance handoff, not execution authority.
130-applies_to: cwd=/private/tmp/cls-gov01-a4-v1/planning-ro; reuse_rule=revalidate commit, envelope, receipts, OpenSpec, scanner/checker contracts, and user authorization before acting.
--
150-
151-## Failures and how to do differently
152-
153-- Expired `pending-user-confirmation` receipt/envelope is not authority. New exact envelope/digest/challenge is needed. The existing `scripts/bmad/scan_feedback.py` did not cover actual output; freeze a new scanner contract/no-write boundary before census. [Task 1]
154-
155:# Task Group: Canvas Learning System P1-05/P1-01/P1-08 adversarial security review
156-scope: Read-only, parallel audit of vault admission/indexing, Graphiti quarantine isolation, SnapshotV3, and recovery-anchor closure claims.
157-applies_to: cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output; reuse_rule=revalidate SHA, CI, actual call sites, and live Neo4j state in the target checkout.
158-
159-## Task 1: P1-05c/P1-01/P1-08 parallel adversarial review, closure rejected
160-
--
181-- “启动并行 agent 进行对抗性审查” -> use independent evidence tracks and cross-check severity; every finding needs `file:line`, reproduction path/result, severity, conflict explanation, PASS/PARTIAL/FAIL, and limits. [Task 1][Task 2]
182-- Respect read-only task-book boundaries, WT/MAIN labels, explicit `UNVERIFIABLE`, and no raw-vault access; do not fix code in the audit. [Task 1]
183-
184-## Reusable knowledge
185-
186:- Related skill: skills/canvas-adversarial-audit/SKILL.md. P1-05/P1-01/P1-08 remained STILL-OPEN; F-02 tombstone filtering and F-05 live resilience were closed. Rejected vault inputs must show zero open/hash/index/write. [Task 1][Task 2]
187-- Reproduced: `vault/raw/escape.md -> /outside/secret.md` was counted by `backfill_vault(..., execute=False)`; case-sensitive `fnmatch` admitted `.CLAUDE/SKILL.md` and `raw/claude.md`. Edge filtering alone was insufficient because exact readers/node search could cross Graphiti groups. [Task 2]
188-- SnapshotV3 needs invalid/future same-generation self-healing, extra-field, strict-type, huge finite mastery, and identity/length collision coverage. [Task 1][Task 2]
189-
190-## Failures and how to do differently
191-

**Inspecting memory audit procedure**
**Spawning subagents for inspection**
codex
我已确认当前环境有 Sequential Thinking，但没有暴露 `graphiti-canvas` 搜索接口；因此会执行前者，并把 Graphiti 本轮搜索记为不可执行而不是伪称已完成。现在启动三条相互独立的只读轨：生产代码/控制流、路径与 inode 对抗、台账与 receipt 精确复算。
**Evaluating shell command restrictions**
**Planning parallel repository data retrieval**
exec
/bin/zsh -lc 'cat /Users/Heishing/.codex/memories/skills/canvas-adversarial-audit/SKILL.md' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
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

exec
/bin/zsh -lc 'nl -ba /Users/Heishing/.codex/memories/MEMORY.md' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
     1	# Task Group: Canvas Learning System long-running cross-model orchestration and productivity governance
     2	scope: Evidence-first audit of project readiness plus a bounded 24-hour writer/reviewer orchestration design. The frozen runbook supports only a Bootstrap-Prep authorization request, not execution.
     3	applies_to: cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output; reuse_rule=revalidate checkout, SHA, CI, unresolved findings, and current authorization before reuse; never treat this historical runbook as permission to create roots, clones, or run agents.
     4	
     5	## Task 1: Full-project adversarial audit and productivity direction, partial
     6	
     7	### rollout_summary_files
     8	
     9	- rollout_summaries/2026-08-19T18-23-31-2Aoh-canvas_learning_system_adversarial_audit_and_24h_orchestrati.md (cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output, rollout_path=/Users/Heishing/.codex/sessions/2026/08/20/rollout-2026-08-20T02-23-31-01a01b43-9daa-7ef1-8e35-587f59df3ec1.jsonl, updated_at=2026-08-24T13:41:20+00:00, thread_id=01a01b43-9daa-7ef1-8e35-587f59df3ec1, outcome=partial; audit and plan only)
    10	
    11	### keywords
    12	
    13	- Canvas Learning System, multi-vault, RAG, Graphiti, FSRS, Excalidraw, Karpathy, vault admission, SnapshotV3, CURRENT_TASK.md, 32280954498
    14	
    15	## Task 2: 24-hour cross-model orchestration authorization design, success / request-only
    16	
    17	### rollout_summary_files
    18	
    19	- rollout_summaries/2026-08-19T18-23-31-2Aoh-canvas_learning_system_adversarial_audit_and_24h_orchestrati.md (cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output, rollout_path=/Users/Heishing/.codex/sessions/2026/08/20/rollout-2026-08-20T02-23-31-01a01b43-9daa-7ef1-8e35-587f59df3ec1.jsonl, updated_at=2026-08-24T13:41:20+00:00, thread_id=01a01b43-9daa-7ef1-8e35-587f59df3ec1, outcome=success; PASS_FOR_BOOTSTRAP_PREP_REQUEST only)
    20	
    21	### keywords
    22	
    23	- ORCH-BOOTSTRAP-PREP-V1, ORCH-SETUP-V1, ORCH-RUN-V1, non-LLM supervisor, app-server, Agent SDK, approval projection, setup-root-claim-v1, run-activation-claim-v1, O_NOFOLLOW, fencing token, no_auto_resume
    24	
    25	## User preferences
    26	
    27	- When asking for “对抗性审查并且修复” and “使用并行 agent workflow”, expect independent evidence tracks with gaps, priorities, and exit gates; distinguish decisions, implementation, tests, and user acceptance. [Task 1]
    28	- For long-running repair, the user does not want several manual iTerm sessions or model overreach: use a supervisor, dependency gates, leases, crash recovery, human gates, and stop rules; a model saying “Goal achieved” is not completion. [Task 2]
    29	- The approved execution order was “先止血、数据边界、可信基线、安全写入基建、分批落地、价值验证、缓行”; Dashboard Web UI is deferred and a broad review MVP should be output-only. [Task 1]
    30	
    31	## Reusable knowledge
    32	
    33	- In this project family: frontend `frontend/obsidian-plugin/`, backend `backend/app/`, RAG `backend/lib/agentic_rag/`; default backend test is `cd backend && .venv/bin/pytest tests/ -x -q`. The represented CI run `32280954498` had 271 passed/13 skipped but Dependency Audit failed on five vulnerabilities; rulesets/required checks were still unset. Rebuild `CURRENT_TASK.md` from HEAD, Actions, and open facts. [Task 1]
    34	- P1-05c evidence still found real vault-admission and LanceDB/orchestrator bypasses; a Graphiti exact-reader helper fix does not prove callers pass the correct group. SnapshotV3 still needs strict schema, bad-cache self-healing, and no ID truncation. [Task 1]
    35	- Use official Codex app-server/subagents, Claude Goals/Agent SDK only in permitted phases, and a non-LLM supervisor. Third-party orchestration plugins may notify or show a read-only dashboard but must not control authorization, evidence, or merging. [Task 2]
    36	- Permission stages are `ORCH-BOOTSTRAP-PREP-V1` (supervised trusted-root construction), `ORCH-SETUP-V1`, then `ORCH-RUN-V1` (up to 24h). Bootstrap request limits: 6h, 6 builder attempts, one reviewer attempt per role, two heavy tests, 1,500,000 tokens, `no_auto_resume=true`. [Task 2]
    37	- Envelope binds only target path, schema hash, construction-contract hash, and `preimage=ABSENT`; the activator creates actual approval-projection SHA, then binds claim/task/result/event. Keep SETUP/RUN claims separate; owner acquires `O_NOFOLLOW|O_CLOEXEC` advisory lock before LLM launch and restart increments epoch/fencing token. Reviewers independently materialize the exact candidate bundle and bind SHA, I/O hashes, command, exit, stdout/stderr, verdict, and limits. [Task 2]
    38	
    39	## Failures and how to do differently
    40	
    41	- Host-path configuration can disagree with Docker: `./data:/app/data` masked `/app/backend/data`, creating fallback and host/main-repo split-brain. Inspect compose mounts as well as host paths. [Task 1]
    42	- Green mocks/helpers/source-string assertions are not production closure. Test real entrypoints, temporary real storage/Neo4j when authorized, and cold-cache/offline behavior. [Task 1]
    43	- `/goal`, chat approval, or an ordinary agent message is not a control plane. Bootstrap-Prep is not Setup/Run authorization; first present exact challenge, action policy, and root-ABSENT evidence for narrow user approval. [Task 2]
    44	- Before activation, verify every model turn/subprocess is terminal and has no writable FD, directory FD, mmap, or inherited handle to activation/claim/lock paths. [Task 2]
    45	
    46	# Task Group: Canvas Learning System GOV01-A4 gated repair and Recovery-4 lab packaging
    47	scope: Exact A4 repository-repair gate and separate isolated Recovery-4 packaging lab. Both outcomes are blocked/partial; lab PASS is not production or freeze approval.
    48	applies_to: cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev; reuse_rule=recheck exact base, design handoff, dirty worktree, external receipts, and authority; do not use the lab as a publisher retry or production mutation path.
    49	
    50	## Task 1: A4 governance repair, safely blocked
    51	
    52	### rollout_summary_files
    53	
    54	- rollout_summaries/2026-08-23T07-46-17-9G79-gov01_a4_blocked_recovery4_lab_freeze_review_fail.md (cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev, rollout_path=/Users/Heishing/.codex/sessions/2026/08/23/rollout-2026-08-23T15-46-17-01a02d95-a6b8-7cf3-b775-6b8afa4464db.jsonl, updated_at=2026-08-24T12:24:52+00:00, thread_id=01a02d95-a6b8-7cf3-b775-6b8afa4464db, outcome=partial; no edit/candidate/review)
    55	
    56	### keywords
    57	
    58	- GOV01, A4, design-claude.json, A4_DESIGN_DIVERGENCE, WAITING_FOR_A4_DESIGN_HANDOFF, d3167d0655fed91a9b96547c50f6adffb07a0bfe, git ls-files, canvas-vault
    59	
    60	## Task 2: Recovery-4 isolated lab package, local suite PASS / freeze review FAIL
    61	
    62	### rollout_summary_files
    63	
    64	- rollout_summaries/2026-08-23T07-46-17-9G79-gov01_a4_blocked_recovery4_lab_freeze_review_fail.md (cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev, rollout_path=/Users/Heishing/.codex/sessions/2026/08/23/rollout-2026-08-23T15-46-17-01a02d95-a6b8-7cf3-b775-6b8afa4464db.jsonl, updated_at=2026-08-24T12:24:52+00:00, thread_id=01a02d95-a6b8-7cf3-b775-6b8afa4464db, outcome=partial; isolated lab only)
    65	
    66	### keywords
    67	
    68	- Recovery-4, no-write sandbox, RENAME_EXCL, freeze readiness, freeze_package.py, ordinal-9595, -I -S -B, fsync, reopen, production_mutation_count
    69	
    70	## User preferences
    71	
    72	- The user required “编辑前等待并验证 design-claude.json…否则输出 A4_DESIGN_DIVERGENCE 并停止” -> remain read-only until the exact handoff exists and matches base/verdict/recommendation. [Task 1]
    73	- Preserve unrelated dirty/untracked state, Vault sandbox denial, and fatal stderr; never clean, normalize, broaden permissions, edit `.gitignore`, or suppress warnings. Claude FAIL needs a fresh candidate SHA, and stop at `WAIT_USER_GEN_APPROVAL` without `generate/acquire/verify`. [Task 1]
    74	- Dry-run/lab evidence must not be called production execution; retain failed lab iterations rather than overwriting them. [Task 2]
    75	
    76	## Reusable knowledge
    77	
    78	- Preflight found `HEAD=d3167d0655fed91a9b96547c50f6adffb07a0bfe`, no staged changes, and extensive unrelated dirty state. The absent required path was `/private/tmp/cls-gov01-a4-v1/handoff/design-claude.json`; existing templates retain `:(exclude)canvas-vault` and `:(exclude)canvas-vault/**`. Requested A4 scope was only `--exclude=/canvas-vault/` in `git ls-files --others --exclude-standard`. [Task 1]
    79	- Recovery-4 final internal suite: 11 pure tests, 7 fault cases, zero-mutation native sandbox, same-filesystem `RENAME_EXCL`/fsync/reopen PASS, 12 AST and 16 strict canonical JSON files, and zero residue. Darwin allowed socket FD creation before I/O, while network I/O was zero and `network*` denied; report that distinction accurately. [Task 2]
    80	- Same-filesystem drill preserved source/forensic-destination inode identity; ctime changed and is not a gate. Execution boundary was direct CLT Python `-I -S -B`, isolated env, no real publisher `main()`, no production mutation/retry. [Task 2]
    81	
    82	## Failures and how to do differently
    83	
    84	- Missing handoff is a hard wait condition, not implied approval. `ps` was sandbox-denied (`operation not permitted`); mark the census unavailable rather than successful. [Task 1]
    85	- Freeze reviewer rejected the lab: missing reproducible full ordinal-9595 input, stdlib origin-byte hashes, exact freeze execution contract/argv/env/cwd enforcement, post-chmod mode proof, and final fsync/reopen/short-write proof. Do not run `freeze_package.py` until a new stable package independently addresses them. [Task 2]
    86	- Do not embed private transcript/session paths in public/minimal package artifacts. [Task 2]
    87	
    88	# Task Group: Canvas Learning System GOV01 exact-object and CACHE-PREP atomicity audit
    89	scope: Isolated, read-only verification of GOV01 bundle chains and static exact-object audit of CACHE-PREP-V1 ADOPT/live-cache atomicity.
    90	applies_to: cwd=/private/tmp/cls-gov01-a4-v1/planning-ro; reuse_rule=recompute every bundle, manifest, commit/tree/blob, source range, and authorization in an isolated inspection repo; do not run production/FETCH/ADOPT modes or access real cache/Vault/network.
    91	
    92	## Task 1: GOV01 A4 repair/micro chain audit, structurally verified but broader readiness partial
    93	
    94	### rollout_summary_files
    95	
    96	- rollout_summaries/2026-08-23T10-38-57-0pt3-gov01_cache_prep_r2_read_only_exact_object_audit.md (cwd=/private/tmp/cls-gov01-a4-v1/planning-ro, rollout_path=/Users/Heishing/.codex/sessions/2026/08/23/rollout-2026-08-23T18-38-57-01a02e33-bb2c-7b93-85d0-3c50119edfad.jsonl, updated_at=2026-08-24T11:49:59+00:00, thread_id=01a02e33-bb2c-7b93-85d0-3c50119edfad, outcome=partial; exact chain verified)
    97	
    98	### keywords
    99	
   100	- GOV01-A4, d3167d06, c1990df5, 2cf9cbf0, git bundle verify, exact bytes, isolated bare repo, review binding, canvas-vault
   101	
   102	## Task 2: CACHE-PREP-V1 ADOPT/live-cache atomicity R2, FAIL / BLOCKED
   103	
   104	### rollout_summary_files
   105	
   106	- rollout_summaries/2026-08-23T10-38-57-0pt3-gov01_cache_prep_r2_read_only_exact_object_audit.md (cwd=/private/tmp/cls-gov01-a4-v1/planning-ro, rollout_path=/Users/Heishing/.codex/sessions/2026/08/23/rollout-2026-08-23T18-38-57-01a02e33-bb2c-7b93-85d0-3c50119edfad.jsonl, updated_at=2026-08-24T11:49:59+00:00, thread_id=01a02e33-bb2c-7b93-85d0-3c50119edfad, outcome=fail; 3 BLOCKER / 2 HIGH)
   107	
   108	### keywords
   109	
   110	- CACHE-PREP-V1, ADOPT.py, live-cache, per-digest claim, restart reconciliation, same-FD readback hash, RENAME_EXCL, O_EXCL, parent fsync, TOCTOU, _cacache/index-v5
   111	
   112	## User preferences
   113	
   114	- For an “独立、只读审查”, do not trust W0, Claude, or a tainted publication manifest: recompute handoff bundle, manifest, exact bytes, Git range, and bindings; report exact `file:line`, severity, PASS/PARTIAL/FAIL. [Task 1][Task 2]
   115	- No production mode, private/Vault/key/cache/state reads, network, fixtures, repository writes, or Git-history changes. [Task 1][Task 2]
   116	
   117	## Reusable knowledge
   118	
   119	- If incremental `git bundle verify` fails in the original worktree because its prerequisite object is absent, seed an isolated bare repo with parent then child bundles. The verified chain was `d3167d06 -> c1990df5395267058a8ec74e415a2ae646d3c261 -> 2cf9cbf0f73479805d4d413fd72829ff825b38bf`; `c1990df5` changed six A4 files, while `2cf9cbf0` adds one generation-envelope JSON. A content-equivalent amended tree still needs fresh review binding. [Task 1]
   120	- Static ADOPT/LIVE code had FD-relative anchoring/nofollow, owner/mode/nlink checks, no-overwrite, file/parent fsync, and offline no-network/index/lifecycle closure for ADOPT/LIVE. Candidate-wide zero-network is invalid because FETCH contains HTTPS code. [Task 2]
   121	- Required closure: persistent per-digest adopter claim/journal and restart reconciliation; valid-existing/invalid-existing/missing branches; same-FD write/readback hash; post-open parent/ancestor identity checks through rename; no-replace publication and parent durability seal; bounded `scandir` enumeration and durable partial-mutation/residue evidence on unexpected exceptions. [Task 2]
   122	
   123	## Failures and how to do differently
   124	
   125	- `O_EXCL` plus `RENAME_EXCL` does not establish unique adopter or crash recovery. R2 found fixed temp `EEXIST` after pre-rename crash, nonsealed post-rename/pre-parent-fsync restart, no durable claim/reconciler, no write-side same-FD readback, and mutation-parent TOCTOU. Therefore `[ROLLUP:CACHE-PREP-V1:S3:R2-TECH] FAIL / BLOCKED`. [Task 2]
   126	- Do not infer cache-object adoption from direct-SRI admission or node_modules protections. [Task 2]
   127	
   128	# Task Group: Canvas Learning System Phase 0A annotation-truth governance ready queue
   129	scope: Read-only, fail-closed planning for GOV-01-VERIFIED and A01→A02→A03. It is a governance handoff, not execution authority.
   130	applies_to: cwd=/private/tmp/cls-gov01-a4-v1/planning-ro; reuse_rule=revalidate commit, envelope, receipts, OpenSpec, scanner/checker contracts, and user authorization before acting.
   131	
   132	## Task 1: Phase 0A ready-queue audit, handoff delivered while execution blocked
   133	
   134	### rollout_summary_files
   135	
   136	- rollout_summaries/2026-08-23T07-48-49-AAp8-phase0a_ready_queue_readonly_governance_audit.md (cwd=/private/tmp/cls-gov01-a4-v1/planning-ro, rollout_path=/Users/Heishing/.codex/sessions/2026/08/23/rollout-2026-08-23T15-48-49-01a02d97-f8f2-74c2-ba02-41c9534f2366.jsonl, updated_at=2026-08-23T08:08:15+00:00, thread_id=01a02d97-f8f2-74c2-ba02-41c9534f2366, outcome=success; handoff only)
   137	
   138	### keywords
   139	
   140	- GOV-01-VERIFIED, Phase-0A, A01, A02, A03, annotation-truth-ledger-v2, AtomicAnnotation, boundary receipt, scanner, [HANDOFF:CODEX-PHASE0A-READY]
   141	
   142	## User preferences
   143	
   144	- “只读” means no repo/index/ref/worktree/OpenSpec writes, scanner/final census, A01/A02 instantiation, private/Vault/network/Graphiti access, or product implementation. Provide ready/blocked status, exact evidence, batch order, and Claude/Codex matrix. [Task 1]
   145	
   146	## Reusable knowledge
   147	
   148	- Order: `GOV-01-VERIFIED clean candidate → OpenSpec → schema/checker → A01 boundary receipt → no-cap census/A01 snapshot → A02 seed/replay → ChatGPT blind review → Codex reconciliation → user dispute/waiver → joint A01/A02 completion → A03 candidate → user exact-byte lock`. A01 cannot complete independently of A02. [Task 1]
   149	- Boundary receipt binds SHA/tree, parent/cutoff, roots/planes, parser/normalizer/scanner/exclusion hashes, scope and user-approval commitments, and output allowlist. Truth atoms are versioned `AtomicAnnotation`, not marker counts. [Task 1]
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
   191	
   192	- Green tests hitting source text, helpers, fake clients, `__new__`, or monkeypatches are not closure; pivot to production entrypoints and full stdout/trace. Test `search_nodes`, `read_node_tips`, `read_node_errors`, and `read_node_edge_reasons`. [Task 1][Task 2]
   193	- P1-05b did not finish its Q1–Q5 matrix. Collect conclusions first, then deliver per-question findings, P1-05/P1-01/P1-08 comparison, and explicit limits. [Task 2]
   194	
   195	# Task Group: Canvas Learning System repository contributor guide
   196	scope: Write a concise, repository-specific AGENTS.md without disturbing a dirty worktree.
   197	applies_to: cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output; reuse_rule=recheck architecture, existing AGENTS.md, and commands in the target checkout.
   198	
   199	## Task 1: Create AGENTS.md, completed
   200	
   201	### rollout_summary_files
   202	
   203	- rollout_summaries/2026-08-17T01-56-07-ZNCd-agents_guide_and_p1_05c_adversarial_audit.md (cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output, rollout_path=/Users/Heishing/.codex/sessions/2026/08/17/rollout-2026-08-17T09-56-07-01a00d6e-ea40-70a1-a23c-d51342eeeacd.jsonl, updated_at=2026-08-19T17:56:56+00:00, thread_id=01a00d6e-ea40-70a1-a23c-d51342eeeacd, outcome=success)
   204	
   205	### keywords
   206	
   207	- AGENTS.md, frontend/obsidian-plugin, backend/app, agentic_rag, backend/tests, verify:spec, lefthook
   208	
   209	## User preferences
   210	
   211	- Check whether `AGENTS.md` exists and do not overwrite it; requested output was 200–400 words, repository-specific, with descriptive headings and actionable commands. [Task 1]
   212	
   213	## Reusable knowledge
   214	
   215	- Represented architecture: active frontend `frontend/obsidian-plugin/`; deprecated `frontend/src/`, `frontend/src-tauri/`, `frontend/sidecar/`; backend `backend/app/`; RAG `backend/lib/agentic_rag/`; tests `backend/tests/`. Commands: `npm --prefix frontend/obsidian-plugin test`, `cd backend && .venv/bin/pytest tests/ -x -q`, `npm run verify:spec`, `npx lefthook run pre-commit`. [Task 1]
   216	
   217	## Failures and how to do differently
   218	
   219	- Run `wc -w AGENTS.md`; first draft was 417 words, above the 200–400 request. [Task 1]
   220	
   221	# Task Group: Shadowrocket VLESS + Reality proxy troubleshooting
   222	scope: Client-first diagnosis of a Shadowrocket VLESS + Reality node failure.
   223	applies_to: cwd=/Users/Heishing; reuse_rule=reuse only the sequence with current redacted node fields and error/log; never treat a share link as proof of server health.
   224	
   225	## Task 1: Shadowrocket VLESS node failure diagnosis, incomplete
   226	
   227	### rollout_summary_files
   228	
   229	- rollout_summaries/2026-08-16T18-47-23-yw81-shadowrocket_vless_reality_node_diagnosis_incomplete.md (cwd=/Users/Heishing, rollout_path=/Users/Heishing/.codex/sessions/2026/08/17/rollout-2026-08-17T02-47-23-01a00be6-62b3-7762-bc36-391ad3de1661.jsonl, updated_at=2026-08-16T18:50:21+00:00, thread_id=01a00be6-62b3-7762-bc36-391ad3de1661, outcome=fail; guardrail)
   230	
   231	### keywords
   232	
   233	- Shadowrocket, VLESS, Reality, XTLS-Vision, pbk, sid, fingerprint=chrome, client-logs, DNS, TCP 443
   234	
   235	## User preferences
   236	
   237	- “这个是 shadowrocket 的代理” -> start with Shadowrocket configuration, Reality/VLESS compatibility, and a concrete error/log. [Task 1]
   238	
   239	## Reusable knowledge
   240	
   241	- Triage redacted address/port, UUID, `pbk`, `sid`, SNI/peer, transport, fingerprint, then DNS/TCP; use symptoms to separate field mismatch, network block, Reality handshake, or outage. Redact UUIDs, credentials, and full share links. [Task 1]
   242	
   243	## Failures and how to do differently
   244	
   245	- Placeholder commands without parsed fields, logs, or connectivity do not diagnose it. Request redacted inputs rather than inventing a conclusion. [Task 1]
   246	
   247	# Task Group: Codex self-knowledge and settings questions
   248	scope: Brief Chinese answers about Codex settings/capabilities when official evidence is unavailable.
   249	applies_to: cwd=/Users/Heishing; reuse_rule=recheck local product environment or official documentation; this evidence does not prove an option exists.
   250	
   251	## Task 1: Codex reasoning intensity adjustability, unverified
   252	
   253	### rollout_summary_files
   254	
   255	- rollout_summaries/2026-08-16T18-27-54-PUxl-codex_thinking_intensity_docs_blocked.md (cwd=/Users/Heishing, rollout_path=/Users/Heishing/.codex/sessions/2026/08/17/rollout-2026-08-17T02-27-54-01a00bd4-8cbc-7223-a319-9556ced486fb.jsonl, updated_at=2026-08-16T18:33:02+00:00, thread_id=01a00bd4-8cbc-7223-a319-9556ced486fb, outcome=partial; docs blocked)
   256	
   257	### keywords
   258	
   259	- Codex, reasoning effort, thinking intensity, official docs, 403, Forbidden, Chinese
   260	
   261	## User preferences
   262	
   263	- For “你目前的思考强度可以调整吗”, answer similar self-knowledge/settings questions directly and briefly in Chinese. [Task 1]
   264	
   265	## Reusable knowledge
   266	
   267	- The represented evidence did not verify direct user configuration of reasoning intensity. [Task 1]
   268	
   269	## Failures and how to do differently
   270	
   271	- On official `403 Forbidden`, state that verification is unavailable; do not repeatedly request the same blocked source. [Task 1]

exec
/bin/zsh -lc 'git log --oneline --decorate -20' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
4ba4f847 (HEAD -> card/s5-census) docs(census): receipt 补 round-5/6 commit 链 [BATCH-2026-08-28-第五批 / CARD-G4-9]
5b371253 fix(census): G4-9 Codex round-6 架构级修复 [BATCH-2026-08-28-第五批 / CARD-G4-9]
4c125f19 fix(census): G4-9 Codex round-5 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9]
d8d887f2 docs(census): 补 artifact commit receipt 绑定精确 SHA 链 [BATCH-2026-08-28-第五批 / CARD-G4-9]
d2827a6d fix(census): G4-9 Codex round-4 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9]
94b420ff fix(census): G4-16 Codex round-4 重放 recipe 确定化 [BATCH-2026-08-28-第五批 / CARD-G4-16]
fce0d8a2 fix(census): G4-9/G4-16 Codex round-3 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9 / CARD-G4-16]
73102875 fix(census): G4-9/G4-16 Codex round-2 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9 / CARD-G4-16]
e7a480eb docs(census): G4-16 doc_type族接线普查 18文件146行+6取值裁定+注释修正 [BATCH-2026-08-28-第五批 / CARD-G4-16]
67ccebe1 docs(census): G4-9 DLQ真实挂载census分诊 92条台账+挂载真相+三态裁定 [BATCH-2026-08-28-第五批 / CARD-G4-9]
37387a86 (origin/worktree-feature-obsidian-hybrid-dev, backup/worktree-feature-obsidian-hybrid-dev, card/s6-recap, card/s1-scope) ci: fix readme-claims conftest isolation with --noconftest [BATCH-2026-08-27-第四批 / CARD-G1-5]
e8e8d034 chore: merge card/n6-contract [BATCH-2026-08-27-第四批 / CARD-G2-1 + CARD-G4-12]
aa386819 chore: merge card/n5-split [BATCH-2026-08-27-第四批 / CARD-G5-1 + CARD-G5-2]
9c7281d2 chore: merge card/n4-readme [BATCH-2026-08-27-第四批 / CARD-G1-4 + CARD-G1-5]
81364293 (card/n4-readme) feat: README禁夸大机械lint三档+hook+CI门 [BATCH-2026-08-27-第四批 / CARD-G1-5]
69e0cdcf (card/n5-split) feat(g5-2): board-split只读拆分preview引擎+34条裁判+live零修改取证 [BATCH-2026-08-27-第四批 / CARD-G5-2]
809658cc test(g5-1): 触发矩阵四类正负例+校验器+headless三轮负例回归 [BATCH-2026-08-27-第四批 / CARD-G5-1]
b2803aa4 (card/n6-contract) fix(metrics): G4-12 检索回归指标正名 recall→hit+baseline 键迁移+守卫 [BATCH-2026-08-27-第四批 / CARD-G4-12]
fca1bdc4 test(cypher): G2-1 读写契约审计+R1-R5/W1-W5 规则+7692 真库门测试 [BATCH-2026-08-27-第四批 / CARD-G2-1]
0204d2eb docs: README 诚实止血横幅+5处漂移标注(纯新增) [BATCH-2026-08-27-第四批 / CARD-G1-4]

exec
/bin/zsh -lc 'git status --short --branch' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
## card/s5-census
?? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round7.md"

exec
/bin/zsh -lc "rg -n -i --hidden --glob '"'!.git/**'"' 'CARD-G4-9|grep-selfattest|attribution_conflict_reason|qa-metrics-db|no_token|byte_exact|unrecoverable' ." in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
./_bmad-output/审查/codex-review-CARD-G4-16-round3.md:152:?? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round3.md"
./_bmad-output/审查/codex-review-CARD-G4-16-round3.md:171:73102875 (HEAD -> card/s5-census) fix(census): G4-9/G4-16 Codex round-2 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9 / CARD-G4-16]
./_bmad-output/审查/codex-review-CARD-G4-16-round3.md:178: .../G4-9-evidence/grep-selfattest.txt"             |  46 ++++++----
./_bmad-output/审查/codex-review-CARD-G4-16-round3.md:180: .../codex-review-CARD-G4-9-round2.md"              |  37 ++++++++
./_bmad-output/审查/codex-review-CARD-G4-16-round3.md:651:A	"_bmad-output/\345\256\241\346\237\245/G4-9-evidence/grep-selfattest.txt"
./_bmad-output/审查/codex-review-CARD-G4-16-round3.md:656:A	"_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round2.md"
./_bmad-output/审查/codex-review-CARD-G4-16-round3.md:657:A	"_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9.md"
./_bmad-output/审查/codex-review-CARD-G4-16-round3.md:659:A	"_bmad-output/\351\252\214\346\224\266\345\215\225/UAT-CARD-G4-9-DLQ\347\234\237\345\256\236\346\214\202\350\275\275census\345\210\206\350\257\212-2026-08-28.md"
./_bmad-output/审查/codex-review-CARD-G4-16-round3.md:1027:67ccebe1 docs(census): G4-9 DLQ真实挂载census分诊 92条台账+挂载真相+三态裁定 [BATCH-2026-08-28-第五批 / CARD-G4-9]
./_bmad-output/审查/codex-review-CARD-G4-16-round3.md:1029:73102875 (HEAD -> card/s5-census) fix(census): G4-9/G4-16 Codex round-2 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9 / CARD-G4-16]
./_bmad-output/审查/codex-review-CARD-G4-16-round3.md:1151:    fix(census): G4-9/G4-16 Codex round-2 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9 / CARD-G4-16]
./_bmad-output/审查/codex-review-CARD-G4-16-round3.md:2507:?? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round3.md"
./_bmad-output/审查/codex-review-CARD-G4-16-round3.md:2694:?? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round3.md"
./_bmad-output/审查/codex-review-CARD-G4-16-round4.md:147:?? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round4.md"
./_bmad-output/审查/codex-review-CARD-G4-16-round4.md:165:    fix(census): G4-9/G4-16 Codex round-3 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9 / CARD-G4-16]
./_bmad-output/审查/codex-review-CARD-G4-16-round4.md:208:A	"_bmad-output/\345\256\241\346\237\245/G4-9-evidence/grep-selfattest.txt"
./_bmad-output/审查/codex-review-CARD-G4-16-round4.md:214:A	"_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round2.md"
./_bmad-output/审查/codex-review-CARD-G4-16-round4.md:215:A	"_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round3.md"
./_bmad-output/审查/codex-review-CARD-G4-16-round4.md:216:A	"_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9.md"
./_bmad-output/审查/codex-review-CARD-G4-16-round4.md:218:A	"_bmad-output/\351\252\214\346\224\266\345\215\225/UAT-CARD-G4-9-DLQ\347\234\237\345\256\236\346\214\202\350\275\275census\345\210\206\350\257\212-2026-08-28.md"
./_bmad-output/审查/codex-review-CARD-G4-16-round4.md:325:_bmad-output/审查/codex-review-CARD-G4-9-round4.md
./_bmad-output/审查/codex-review-CARD-G4-16-round4.md:344:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt
./_bmad-output/审查/codex-review-CARD-G4-16-round4.md:533:_bmad-output/审查/codex-review-CARD-G4-9-round2.md
./_bmad-output/审查/codex-review-CARD-G4-16-round4.md:578:_bmad-output/审查/codex-review-CARD-G4-9-round3.md
./_bmad-output/审查/codex-review-CARD-G4-16-round4.md:580:_bmad-output/审查/codex-review-CARD-G4-9.md
./_bmad-output/审查/codex-review-CARD-G4-16-round4.md:1387:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md
./_bmad-output/审查/codex-review-CARD-G4-16-round4.md:2682:M	"_bmad-output/\345\256\241\346\237\245/G4-9-evidence/grep-selfattest.txt"
./_bmad-output/审查/codex-review-CARD-G4-16-round4.md:2684:A	"_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round3.md"
./_bmad-output/审查/codex-review-CARD-G4-16-round4.md:2686:M	"_bmad-output/\351\252\214\346\224\266\345\215\225/UAT-CARD-G4-9-DLQ\347\234\237\345\256\236\346\214\202\350\275\275census\345\210\206\350\257\212-2026-08-28.md"
./_bmad-output/审查/codex-review-CARD-G4-16-round4.md:3858:fce0d8a2 (HEAD -> card/s5-census) fix(census): G4-9/G4-16 Codex round-3 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9 / CARD-G4-16]
./_bmad-output/审查/codex-review-CARD-G4-16-round4.md:3859:73102875 fix(census): G4-9/G4-16 Codex round-2 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9 / CARD-G4-16]
./_bmad-output/审查/codex-review-CARD-G4-16-round4.md:3861:67ccebe1 docs(census): G4-9 DLQ真实挂载census分诊 92条台账+挂载真相+三态裁定 [BATCH-2026-08-28-第五批 / CARD-G4-9]
./_bmad-output/审查/codex-review-CARD-G4-16-round4.md:4848:?? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round4.md"
./backend/scripts/census_dead_letter_episodes.py:2:"""CARD-G4-9: dead-letter episodes 只读 census 分诊脚本。
./backend/scripts/census_dead_letter_episodes.py:4:BATCH-2026-08-28-第五批 / CARD-G4-9（G4-10 replay 的交接台账生成器）。
./backend/scripts/census_dead_letter_episodes.py:11:    **文件身份 (st_dev, st_ino) 比较**，与 --dlq/--compare/--qa-metrics-db
./backend/scripts/census_dead_letter_episodes.py:23:    unrecoverable 并显式给 anomaly basis（不谎称"截断前缀"）。
./backend/scripts/census_dead_letter_episodes.py:33:    （chmod 000）时整体 exit 2（拒绝在源不可见时产出 unrecoverable 假象）；
./backend/scripts/census_dead_letter_episodes.py:38:    重算 sha **且长度**双门对账通过才按 byte_exact 采信，且 anomaly 记录
./backend/scripts/census_dead_letter_episodes.py:141:    但 episode_body_length=999）仍被判 byte_exact —— 与 inline 侧同门收紧。
./backend/scripts/census_dead_letter_episodes.py:201:    # round-6 整改: **无论有无 token 都遍历** —— no_token 时原实现完全不扫描，
./backend/scripts/census_dead_letter_episodes.py:231:        result["no_token"] = True
./backend/scripts/census_dead_letter_episodes.py:382:        "--qa-metrics-db",
./backend/scripts/census_dead_letter_episodes.py:413:    # 并把全部记录假判 unrecoverable —— 同样 fail-closed 拒诊。
./backend/scripts/census_dead_letter_episodes.py:532:    unrecoverable_keys = []
./backend/scripts/census_dead_letter_episodes.py:547:            recover = "byte_exact"
./backend/scripts/census_dead_letter_episodes.py:550:            recover = "byte_exact"
./backend/scripts/census_dead_letter_episodes.py:556:            if sess.get("no_token"):
./backend/scripts/census_dead_letter_episodes.py:571:            recover = "unrecoverable"
./backend/scripts/census_dead_letter_episodes.py:581:            recover = "unrecoverable"
./backend/scripts/census_dead_letter_episodes.py:591:        if recover == "unrecoverable":
./backend/scripts/census_dead_letter_episodes.py:592:            unrecoverable_keys.append(stable_key)
./backend/scripts/census_dead_letter_episodes.py:618:                "attribution_conflict_reason": (
./backend/scripts/census_dead_letter_episodes.py:619:                    "no_token"
./backend/scripts/census_dead_letter_episodes.py:620:                    if sess.get("no_token")
./backend/scripts/census_dead_letter_episodes.py:674:        "card": "CARD-G4-9",
./backend/scripts/census_dead_letter_episodes.py:693:            k: recover_dist.get(k, 0) for k in ["byte_exact", "approximate", "unverifiable", "unrecoverable"]
./backend/scripts/census_dead_letter_episodes.py:698:        "unrecoverable_list": unrecoverable_keys,
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:14:CARD-G4-9 round-4 终裁复审（静态审阅 + 只读复算，禁改任何文件）。你 round-3 裁定 4/6 CLOSED，两项 PARTIAL + 3 新发现。开发方以 commit fce0d8a2 提交整改，请只读复核这 6 项：
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:27:/bin/zsh -lc "rg -n -i \"CARD-G4-9|G4-9|round-3|fce0d8a2|DLQ ledger|adversarial\" /Users/Heishing/.codex/memories/MEMORY.md && sed -n '1,260p' /Users/Heishing/.codex/memories/skills/canvas-adversarial-audit/SKILL.md" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:94:/bin/zsh -lc "rg -n -i \"CARD-G4-9|G4-9|fce0d8a2|92 条|89-2-1|4-88-0\" /Users/Heishing/.codex/memories/rollout_summaries /Users/Heishing/.codex/memories/MEMORY.md --glob '*.md' --glob '*.jsonl' || true
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:106:?? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round4.md"
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:112:fce0d8a2 (HEAD -> card/s5-census) fix(census): G4-9/G4-16 Codex round-3 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9 / CARD-G4-16]
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:120: .../G4-9-evidence/grep-selfattest.txt"             |   58 +-
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:122: .../codex-review-CARD-G4-9-round3.md"              | 3569 ++++++++++++++++++++
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:128:fce0d8a2 (HEAD -> card/s5-census) fix(census): G4-9/G4-16 Codex round-3 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9 / CARD-G4-16]
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:129:73102875 fix(census): G4-9/G4-16 Codex round-2 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9 / CARD-G4-16]
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:131:67ccebe1 docs(census): G4-9 DLQ真实挂载census分诊 92条台账+挂载真相+三态裁定 [BATCH-2026-08-28-第五批 / CARD-G4-9]
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:145:rg -n \"BLOCKER-1|HIGH-3|JSONL|framing|非 dict|provenance|PARTIAL|CLOSED|NOT-CLOSED|新发现|总裁定|protected_ids|O_NOFOLLOW|os\\.walk|line_count\" '_bmad-output/审查/codex-review-CARD-G4-9-round3.md' | head -n 240
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:152:_bmad-output/审查/codex-review-CARD-G4-9-round2.md
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:153:_bmad-output/审查/codex-review-CARD-G4-9-round3.md
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:154:_bmad-output/审查/codex-review-CARD-G4-9-round4.md
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:155:_bmad-output/审查/codex-review-CARD-G4-9.md
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:156:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:160:14:CARD-G4-9 round-3 复审（静态审阅 + 只读复算）。你 round-2 裁定 10/13 CLOSED，三项 NOT-CLOSED：BLOCKER-1（--out 守卫比 resolve 字符串，hardlink 与 case-only 别名绕过截断输入）、HIGH-1（full_body_verified 只核 sha 不核长度且排在 anomaly 分支前，anomaly 记录被判 byte_exact）、HIGH-3（chmod 000 根 exit 0 假判 unrecoverable；glob 跟随 symlink 逃逸出根）；另 3 新 LOW（full_verified 长度范围应 131-180、distribution 省略 0 值键、line_count 数 LF 与 records 的 splitlines 口径不一）。开发方以 commit 73102875 提交整改。请只读复核这 6 项是否闭合：
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:186:1214: - **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:188:1219: - **HIGH-3（transcript 归因折叠）**：恰 1 个常规文件命中才算归因（多命中 = ambiguous 拒采信）；glob 改递归下探；transcripts 根缺失整体 exit 2（拒绝产出 unrecoverable 假象）。
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:192:1232:+- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:193:1233:+- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:213:1937:99:- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:217:1946:117:- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:218:1947:118:- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:226:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:229:2146:    10	| HIGH-1 | **NOT-CLOSED** | round-1 三个反例本身均已翻转为 `anomaly/FAIL → unrecoverable`；非法 64 字符非 hex 也被拒。但新增组合反例：`episode_body="abc"`、`episode_body_full="abc"`、SHA 正确、声明长度 `999`，实际得到 `inline_state=anomaly` 后仍被判 `byte_exact`。原因是 [`full_body_verified()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:99)只核 SHA，不核长度，并在 [anomaly 分支之前](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:285)被采信。这直接反驳报告“anomaly 一律 unrecoverable”。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:230:2147:    11	| HIGH-2 | **CLOSED** | missing、显式 `null`、字面 `"None"` 不再合组；数字 `123` 与字符串 `"123"` 分离；非前缀多 token 均 `attribution_conflict=true/unrecoverable`；合法前缀组统一取最长 token。真实入口反例全部通过。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:231:2148:    12	| HIGH-3 | **NOT-CLOSED** | 不存在根目录已 exit 2；递归唯一命中、多命中冲突、目录伪命中也通过。但“不可见”仍未闭合：存在但 `chmod 000` 的根会 exit 0 并假判 `unrecoverable`。此外 [`glob + os.path.isfile`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:134)跟随 symlink：根内 `.jsonl` symlink 指向根外 `.txt`、以及 symlink 目录逃逸到根外树，均被判唯一来源并进入 `approximate`。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:243:2762:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:117:- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:245:2765:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:7:| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:246:2766:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:8:| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:247:2767:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:10:| HIGH-1 | **NOT-CLOSED** | round-1 三个反例本身均已翻转为 `anomaly/FAIL → unrecoverable`；非法 64 字符非 hex 也被拒。但新增组合反例：`episode_body="abc"`、`episode_body_full="abc"`、SHA 正确、声明长度 `999`，实际得到 `inline_state=anomaly` 后仍被判 `byte_exact`。原因是 [`full_body_verified()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:99)只核 SHA，不核长度，并在 [anomaly 分支之前](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:285)被采信。这直接反驳报告“anomaly 一律 unrecoverable”。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:248:2768:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:12:| HIGH-3 | **NOT-CLOSED** | 不存在根目录已 exit 2；递归唯一命中、多命中冲突、目录伪命中也通过。但“不可见”仍未闭合：存在但 `chmod 000` 的根会 exit 0 并假判 `unrecoverable`。此外 [`glob + os.path.isfile`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:134)跟随 symlink：根内 `.jsonl` symlink 指向根外 `.txt`、以及 symlink 目录逃逸到根外树，均被判唯一来源并进入 `approximate`。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:249:2769:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:14:| MEDIUM-2 | **CLOSED** | [报告 §6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:78)、[ledger duplicate_clusters](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:60)及逐条 `reference_time` 已落地；6 簇全部逐行对账。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:250:2772:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:14:CARD-G4-9 round-3 复审（静态审阅 + 只读复算）。你 round-2 裁定 10/13 CLOSED，三项 NOT-CLOSED：BLOCKER-1（--out 守卫比 resolve 字符串，hardlink 与 case-only 别名绕过截断输入）、HIGH-1（full_body_verified 只核 sha 不核长度且排在 anomaly 分支前，anomaly 记录被判 byte_exact）、HIGH-3（chmod 000 根 exit 0 假判 unrecoverable；glob 跟随 symlink 逃逸出根）；另 3 新 LOW（full_verified 长度范围应 131-180、distribution 省略 0 值键、line_count 数 LF 与 records 的 splitlines 口径不一）。开发方以 commit 73102875 提交整改。请只读复核这 6 项是否闭合：
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:251:2773:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:15:脚本 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py 现改为：(a) 碰撞守卫比较文件身份 (st_dev, st_ino) 并保留 resolve 路径比较；(b) full_body_verified 增加 len(full)==declared_len 门，且判定链改为 state != 'anomaly' 前置；(c) transcripts 根增 os.access(R_OK|X_OK) 检查 exit 2，glob 结果排除 os.path.islink 条目并要求 realpath 落在根内；(d) line_count 改用 splitlines()，class/recoverability distribution 补零并新增 inline_state_distribution。
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:252:2792:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1232:+- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:253:2793:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1234:+- **新 LOW ×3**：full_verified 长度范围修正为 131–180；台账 `class_distribution`/`recoverability_distribution` 补零并新增 `inline_state_distribution`（固定 schema，消费者无需补齐缺席键）；`line_count` 改用 `splitlines()` 与 records 同口径（原 `count("\n")` 在 bare CR / U+2028 下会与 records 数不一致）。
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:254:2809:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1946:117:- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:255:2810:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1948:119:- **新 LOW ×3**：full_verified 长度范围修正为 131–180；台账 `class_distribution`/`recoverability_distribution` 补零并新增 `inline_state_distribution`（固定 schema，消费者无需补齐缺席键）；`line_count` 改用 `splitlines()` 与 records 同口径（原 `count("\n")` 在 bare CR / U+2028 下会与 records 数不一致）。
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:256:2815:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:257:2816:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2144:     8	| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:258:2817:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2146:    10	| HIGH-1 | **NOT-CLOSED** | round-1 三个反例本身均已翻转为 `anomaly/FAIL → unrecoverable`；非法 64 字符非 hex 也被拒。但新增组合反例：`episode_body="abc"`、`episode_body_full="abc"`、SHA 正确、声明长度 `999`，实际得到 `inline_state=anomaly` 后仍被判 `byte_exact`。原因是 [`full_body_verified()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:99)只核 SHA，不核长度，并在 [anomaly 分支之前](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:285)被采信。这直接反驳报告“anomaly 一律 unrecoverable”。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:259:2818:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2148:    12	| HIGH-3 | **NOT-CLOSED** | 不存在根目录已 exit 2；递归唯一命中、多命中冲突、目录伪命中也通过。但“不可见”仍未闭合：存在但 `chmod 000` 的根会 exit 0 并假判 `unrecoverable`。此外 [`glob + os.path.isfile`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:134)跟随 symlink：根内 `.jsonl` symlink 指向根外 `.txt`、以及 symlink 目录逃逸到根外树，均被判唯一来源并进入 `approximate`。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:260:2819:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2150:    14	| MEDIUM-2 | **CLOSED** | [报告 §6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:78)、[ledger duplicate_clusters](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:60)及逐条 `reference_time` 已落地；6 簇全部逐行对账。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:261:2850:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:61:- **3 新 LOW**：full_verified 长度范围修正 131–180；台账三个 distribution 补零并新增 `inline_state_distribution`；`line_count` 与 records 改用同一 `splitlines()` 口径。
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:274:3511:| HIGH-1 | **CLOSED / PASS** | [`full_body_verified()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:102)现有 SHA+严格长度门；[真实判定链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:340)在 full-body 分支前要求 `state != anomaly`。更强反例——full 本身 SHA/长度完全有效，但 inline 不符——仍落 `anomaly → unrecoverable`。无其它调用入口。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:277:3514:| LOW：distribution 零键 | **CLOSED** | [固定 schema 生成链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:437)与 [ledger](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:43)均包含 `unexpected/anomaly/unrecoverable: 0`，并新增 inline 三态。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:282:3534:所以：**冻结的 92 条 ledger 数值可采信；CARD-G4-9 生成器与整卡验收仍被 BLOCKER-1、HIGH-3 阻断。** 本轮未修改仓库或受审数据，未执行破坏性 fixture/G4-10 重放；Graphiti 工具本轮不可用。
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:285:3544:| HIGH-1 | **CLOSED / PASS** | [`full_body_verified()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:102)现有 SHA+严格长度门；[真实判定链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:340)在 full-body 分支前要求 `state != anomaly`。更强反例——full 本身 SHA/长度完全有效，但 inline 不符——仍落 `anomaly → unrecoverable`。无其它调用入口。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:288:3547:| LOW：distribution 零键 | **CLOSED** | [固定 schema 生成链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:437)与 [ledger](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:43)均包含 `unexpected/anomaly/unrecoverable: 0`，并新增 inline 三态。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:293:3567:所以：**冻结的 92 条 ledger 数值可采信；CARD-G4-9 生成器与整卡验收仍被 BLOCKER-1、HIGH-3 阻断。** 本轮未修改仓库或受审数据，未执行破坏性 fixture/G4-10 重放；Graphiti 工具本轮不可用。
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:301: > **批次**: BATCH-2026-08-28-第五批 / CARD-G4-9（4h · wave 1 · 未来铺路）
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:330:  "card": "CARD-G4-9",
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:340:@@ -52,7 +52,6 @@ BATCH-2026-08-28-第五批 / CARD-G4-9（G4-10 replay 的交接台账生成器
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:373:+    # 会把"没搜到"与"搜不了"混为一谈，产出假 unrecoverable。遍历出错即 fail-closed。
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:559:nl -ba CURRENT_TASK.md | rg -n -C 5 'CARD-G4-9|G4-9' || true
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:560:nl -ba _decisions/CURRENT_TASK.md | rg -n -C 5 'CARD-G4-9|G4-9' || true" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:563:     2	"""CARD-G4-9: dead-letter episodes 只读 census 分诊脚本。
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:565:     4	BATCH-2026-08-28-第五批 / CARD-G4-9（G4-10 replay 的交接台账生成器）。
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:572:    11	    **文件身份 (st_dev, st_ino) 比较**，与 --dlq/--compare/--qa-metrics-db
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:584:    23	    unrecoverable 并显式给 anomaly basis（不谎称"截断前缀"）。
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:594:    33	    （chmod 000）时整体 exit 2（拒绝在源不可见时产出 unrecoverable 假象）；
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:599:    38	    重算 sha **且长度**双门对账通过才按 byte_exact 采信，且 anomaly 记录
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:674:   113	    但 episode_body_length=999）仍被判 byte_exact —— 与 inline 侧同门收紧。
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:715:   154	    # 会把"没搜到"与"搜不了"混为一谈，产出假 unrecoverable。遍历出错即 fail-closed。
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:825:   264	        "--qa-metrics-db",
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:856:   295	    # 并把全部记录假判 unrecoverable —— 同样 fail-closed 拒诊。
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:938:   377	    unrecoverable_keys = []
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:947:   386	            recover = "byte_exact"
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:951:   390	            recover = "byte_exact"
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:954:   393	            recover = "unrecoverable"
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:957:   396	            recover = "unrecoverable"
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:967:   406	            recover = "unrecoverable"
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:977:   416	        if recover == "unrecoverable":
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:978:   417	            unrecoverable_keys.append(stable_key)
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1031:   470	        "card": "CARD-G4-9",
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1050:   489	            k: recover_dist.get(k, 0) for k in ["byte_exact", "approximate", "unrecoverable"]
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1055:   494	        "unrecoverable_list": unrecoverable_keys,
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1113:     1	# CARD-G4-9 — DLQ 真实挂载 census 分诊报告
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1115:     3	> **批次**: BATCH-2026-08-28-第五批 / CARD-G4-9（4h · wave 1 · 未来铺路）
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1182:    70	| **可字节级**（byte_exact） | **4** | inline 正文全量：sha256 重算对账通过**且**长度精确匹配（fail-closed 双门）——重放可逐字节还原 episode |
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1184:    72	| **不可恢复**（unrecoverable） | **0** | — |
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1196:    84	逐条另带 `class / inline_state / recoverability / transcript_paths / transcript_match_count / attribution_conflict / error_excerpt / failed_at / reference_time`，G4-10 可直接按 `recoverability` 分桶排重放优先级（建议：4 条 byte_exact 先行——但其中 3 条 group_id 为已弃用 `vault:default`，重放前需按 D16 规约重映射并过 `to_physical_group_id()`；89 条 budget_400 重放前必须先修 context 超限根因，否则原样重放必然复现 400）。
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1203:    91	| grep 自证（import 行全 stdlib；neo4j/graphiti/bolt/app. import 0 命中；`--apply` 定义 0 命中；写模式 open 仅 `--out` 1 处且受路径碰撞守卫保护） | **PASS**（`grep-selfattest.txt`，含守卫在位证明） |
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1206:    94	| 负例门（round-1 整改自证） | `--out`==`--dlq` → exit 2 拒写、DLQ 完好；transcripts 根缺失 → exit 2 拒诊；sha 匹配但长度不符（round-1 HIGH-1 反例①）→ anomaly/unrecoverable；坏 JSON 行/空行 → unparseable 逐行入台账不拒诊 |
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1207:    95	| 负例门（round-2 整改自证） | **hardlink** 指向 DLQ 的 --out → exit 2 + DLQ sha 不变；**case-only 别名**（`DLQ.jsonl`）→ exit 2 + DLQ 完好；**anomaly + episode_body_full 组合**（sha 对但长度 999）→ anomaly/unrecoverable（不再翻案 byte_exact）；**chmod 000 根** → exit 2 拒诊；**symlink 逃逸**（根内 .jsonl → 根外 .txt）→ match_count=0/unrecoverable；正例回归：真实唯一命中仍 approximate |
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1211:    99	- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1213:   101	- **BLOCKER-3（交付物未冻结漂移）**：以本卡 commit 冻结全部交付物 exact bytes（脚本/报告/台账/证据包同 commit）；grep-selfattest 已按最终版行号重生成并内嵌脚本 sha 前缀。
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1214:   102	- **HIGH-1（inline 判定不 fail-closed）**：full_verified 加长度精确匹配门；truncated_prefix 加 64-hex 合法性门；anomaly 一律 unrecoverable + 如实 basis（不再谎称截断、不再滑入 approximate）。
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1216:   104	- **HIGH-3（transcript 归因折叠）**：恰 1 个常规文件命中才算归因（多命中 = ambiguous 拒采信）；glob 改递归下探；transcripts 根缺失整体 exit 2（拒绝产出 unrecoverable 假象）。
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1217:   105	- **MEDIUM-1**：`episode_body_full` 在盘且 sha 对账通过 → byte_exact 采信（现网 0 条，通路已备）。
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1229:   117	- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1230:   118	- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1241:   129	  --qa-metrics-db "…/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db" \
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1296:   377	    unrecoverable_keys = []
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1305:   386	            recover = "byte_exact"
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1309:   390	            recover = "byte_exact"
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1312:   393	            recover = "unrecoverable"
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1315:   396	            recover = "unrecoverable"
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1325:   406	            recover = "unrecoverable"
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1335:   416	        if recover == "unrecoverable":
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1336:   417	            unrecoverable_keys.append(stable_key)
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1389:   470	        "card": "CARD-G4-9",
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1408:   489	            k: recover_dist.get(k, 0) for k in ["byte_exact", "approximate", "unrecoverable"]
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1413:   494	        "unrecoverable_list": unrecoverable_keys,
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1470:     1	# CARD-G4-9 — DLQ 真实挂载 census 分诊报告
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1472:     3	> **批次**: BATCH-2026-08-28-第五批 / CARD-G4-9（4h · wave 1 · 未来铺路）
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1489:    fix(census): G4-9/G4-16 Codex round-3 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9 / CARD-G4-16]
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1522:/bin/zsh -lc "jq '{card,generated_at,dlq_file,total_lines,total_records,unparseable_lines,class_distribution,recoverability_distribution,inline_state_distribution,unrecoverable_count:(.unrecoverable_list|length),attribution_conflict_count:(.attribution_conflicts|length),duplicate_cluster_count:(.duplicate_clusters|length),duplicate_cluster_rows:([.duplicate_clusters[].occurrences]|add),record_count:(.records|length)}' '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json'
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1528:  "card": "CARD-G4-9",
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1548:    "byte_exact": 4,
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1550:    "unrecoverable": 0
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1557:  "unrecoverable_count": 0,
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1642:{"attribution_conflicts_from_records": 0, "class": {"budget_400": 89, "group_id_format": 1, "schema_entity_type": 2}, "duplicate_clusters_from_raw": 6, "duplicate_rows_from_raw": 29, "header_sha_match": true, "inline": {"full_verified": 4, "truncated_prefix": 88}, "ledger_derivation_mismatches": [], "lf_frames": 92, "parsed_records": 92, "raw_unparseable": 0, "recoverability_from_records": {"approximate": 88, "byte_exact": 4}, "source_sha256": "3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590", "transcript_path_metadata": {"missing": 0, "nonregular": 0, "symlink": 0, "unique": 7, "unreadable": 0}}
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1960:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:1:== CARD-G4-9 只读自证（round-3 整改版, 4f776f23efe2fdb4…） ==
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1961:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:20:--- (4) 写出口（唯一，且经 O_NOFOLLOW+fstat inode 校验后才 ftruncate）:
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1962:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:21:517:            fd = os.open(args.out, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1963:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:22:529:            os.ftruncate(fd, 0)
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1964:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:31:156:    walk_errors: list[str] = []
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1965:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:32:159:        walk_errors.append(f"{getattr(err, 'filename', '?')}: {err}")
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1966:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:33:162:    unreadable: list[str] = []
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1967:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:35:171:            # 不是可用恢复源，计入 unreadable 而非命中（fail-closed）。
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1968:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:37:173:                unreadable.append(candidate)
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1969:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:38:180:    if unreadable:
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1970:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:39:182:        result["unreadable_candidates"] = unreadable[:5]
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1971:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:40:187:    if walk_errors:
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1972:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:41:189:        result["scan_errors"] = walk_errors[:5]
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1977:sed -n '1,80p' '_bmad-output/审查/G4-9-evidence/grep-selfattest.txt'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1980:== CARD-G4-9 只读自证（round-3 整改版, 4f776f23efe2fdb4…） ==
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:2049:**Identifying unrecoverable attribution_conflict handling**
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:2059:rg -n '\"class_distribution\"|\"recoverability_distribution\"|\"inline_state_distribution\"|\"unrecoverable_list\"|\"attribution_conflicts\"|\"duplicate_clusters\"|\"records\"' '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:2062:     2	 "card": "CARD-G4-9",
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:2116:    56	  "byte_exact": 4,
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:2118:    58	  "unrecoverable": 0
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:2125:    65	 "unrecoverable_list": [],
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:2154:65: "unrecoverable_list": [],
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:2175:不过生成器仍出现一个无需竞态的截断反例：匹配 transcript 若是“不可读但可写”（如 owner mode `0200`），扫描会把它从 `transcript_paths` 清掉，输出保护集因此漏掉它，而 `--out` 又能按写权限打开并截断。另有扫描错误最终仍被写成 `unrecoverable`，与“拒绝裁定”声明相反。终裁会据此维持阻断。
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:2185:?? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round4.md"
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:2307:| 3. HIGH-3 枚举 | **NOT-CLOSED** | 稳态目录 symlink、`scandir` 错误和 mode `000` 门已有改善。但 unreadable/walk error 设置 conflict 后，主链仍在 [395–397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:395)明确产出 `recoverability=unrecoverable`，直接反驳报告所称“既不宣称不可恢复” [报告:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:143)。此外 `os.walk.onerror` 只覆盖 `scandir`；逐条 `is_dir/stat` 错误可被静默当非候选，[islink→isfile→access→realpath](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:168)仍是路径级竞态。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:2316:- **HIGH**：扫描不可见性仍被终态化为 `unrecoverable`。
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:2344:| 3. HIGH-3 枚举 | **NOT-CLOSED** | 稳态目录 symlink、`scandir` 错误和 mode `000` 门已有改善。但 unreadable/walk error 设置 conflict 后，主链仍在 [395–397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:395)明确产出 `recoverability=unrecoverable`，直接反驳报告所称“既不宣称不可恢复” [报告:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:143)。此外 `os.walk.onerror` 只覆盖 `scandir`；逐条 `is_dir/stat` 错误可被静默当非候选，[islink→isfile→access→realpath](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:168)仍是路径级竞态。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:2353:- **HIGH**：扫描不可见性仍被终态化为 `unrecoverable`。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:14:CARD-G4-9 round-5 终裁复审（静态审阅 + 只读复算，禁改任何文件）。你 round-4 裁定 1/6 CLOSED，提出 2 BLOCKER / 1 HIGH / 2 MEDIUM / 3 LOW。开发方以 commit d2827a6d + d8d887f2 提交整改，请逐条只读复核：
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:22:请对每项设计静态反例判断是否仍可绕过（尤其：保护集完整性、fd 身份与实际读取的绑定、unverifiable 与 unrecoverable 的语义边界、strict decode 的边界）。同时独立复算台账仍为 92 条 / class 89-2-1 / byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0 / 重复簇 6 簇 29 行 / unparseable 0。逐项 CLOSED/NOT-CLOSED + 总裁定（可验收/仍阻断）+ 新发现分级。若已可验收请明确说明；若仍阻断请说明**对一张只读 census 卡**而言该阻断是否与卡面范围相称。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:30:/bin/zsh -lc "rg -n -C 3 'CARD-G4-9|G4-9|census|round-4|adversarial|canvas-adversarial-audit' /Users/Heishing/.codex/memories/MEMORY.md" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:176:  → 锁定 HEAD、提交链、工作树状态、CARD-G4-9 报告与生产入口
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:192:_bmad-output/审查/codex-review-CARD-G4-9-round2.md
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:193:_bmad-output/审查/codex-review-CARD-G4-9-round3.md
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:194:_bmad-output/审查/codex-review-CARD-G4-9-round4.md
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:195:_bmad-output/审查/codex-review-CARD-G4-9-round5.md
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:196:_bmad-output/审查/codex-review-CARD-G4-9.md
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:200:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:215:    fix(census): G4-9 Codex round-4 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9]
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:221:    unrecoverable(与报告既不宣称不可恢复对齐)。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:233: .../G4-9-evidence/grep-selfattest.txt"             |   71 +-
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:234: .../codex-review-CARD-G4-9-round4.md"              | 2372 ++++++++++++++++++++
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:238: create mode 100644 "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round4.md"
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:246:    docs(census): 补 artifact commit receipt 绑定精确 SHA 链 [BATCH-2026-08-28-第五批 / CARD-G4-9]
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:265:M	"_bmad-output/\345\256\241\346\237\245/G4-9-evidence/grep-selfattest.txt"
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:266:A	"_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round4.md"
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:267:M	"_bmad-output/\351\252\214\346\224\266\345\215\225/UAT-CARD-G4-9-DLQ\347\234\237\345\256\236\346\214\202\350\275\275census\345\210\206\350\257\212-2026-08-28.md"
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:270:d8d887f2 (HEAD -> card/s5-census) docs(census): 补 artifact commit receipt 绑定精确 SHA 链 [BATCH-2026-08-28-第五批 / CARD-G4-9]
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:271:d2827a6d fix(census): G4-9 Codex round-4 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9]
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:273:fce0d8a2 fix(census): G4-9/G4-16 Codex round-3 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9 / CARD-G4-16]
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:274:73102875 fix(census): G4-9/G4-16 Codex round-2 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9 / CARD-G4-16]
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:276:67ccebe1 docs(census): G4-9 DLQ真实挂载census分诊 92条台账+挂载真相+三态裁定 [BATCH-2026-08-28-第五批 / CARD-G4-9]
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:285:? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round5.md"
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:781:/bin/zsh -lc "rg -n 'def snapshot_file|def resolve_group_attribution|all_candidate_paths|protected_ids|unverifiable|unrecoverable|_split_jsonl_lines|root_prefix|fchmod|O_NONBLOCK|S_ISREG|request_id|episode_body|name' backend/scripts/census_dead_letter_episodes.py" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:783:23:    unrecoverable 并显式给 anomaly basis（不谎称"截断前缀"）。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:785:33:    （chmod 000）时整体 exit 2（拒绝在源不可见时产出 unrecoverable 假象）；
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:796:131:    但 episode_body_length=999）仍被判 byte_exact —— 与 inline 侧同门收紧。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:807:179:    # 会把"没搜到"与"搜不了"混为一谈，产出假 unrecoverable。遍历出错即 fail-closed。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:821:345:    # 并把全部记录假判 unrecoverable —— 同样 fail-closed 拒诊。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:833:443:    unrecoverable_keys = []
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:838:465:            recover = "unrecoverable"
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:839:469:            # 终态化为 unrecoverable 是不诚实的断言 —— 单列 unverifiable。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:842:490:            recover = "unrecoverable"
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:845:500:        if recover == "unrecoverable":
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:846:501:            unrecoverable_keys.append(stable_key)
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:857:584:            k: recover_dist.get(k, 0) for k in ["byte_exact", "approximate", "unverifiable", "unrecoverable"]
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:858:589:        "unrecoverable_list": unrecoverable_keys,
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:870:/bin/zsh -lc "rg -n 'BLOCKER|HIGH|MEDIUM|LOW|CLOSED|NOT-CLOSED|保护集|TOCTOU|UTF-8|unverifiable|unrecoverable|provenance|92|89|29' '_bmad-output/审查/codex-review-CARD-G4-9-round4.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:873:14:CARD-G4-9 round-4 终裁复审（静态审阅 + 只读复算，禁改任何文件）。你 round-3 裁定 4/6 CLOSED，两项 PARTIAL + 3 新发现。开发方以 commit fce0d8a2 提交整改，请只读复核这 6 项：
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:882:94:/bin/zsh -lc "rg -n -i \"CARD-G4-9|G4-9|fce0d8a2|92 条|89-2-1|4-88-0\" /Users/Heishing/.codex/memories/rollout_summaries /Users/Heishing/.codex/memories/MEMORY.md --glob '*.md' --glob '*.jsonl' || true
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:883:131:67ccebe1 docs(census): G4-9 DLQ真实挂载census分诊 92条台账+挂载真相+三态裁定 [BATCH-2026-08-28-第五批 / CARD-G4-9]
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:884:145:rg -n \"BLOCKER-1|HIGH-3|JSONL|framing|非 dict|provenance|PARTIAL|CLOSED|NOT-CLOSED|新发现|总裁定|protected_ids|O_NOFOLLOW|os\\.walk|line_count\" '_bmad-output/审查/codex-review-CARD-G4-9-round3.md' | head -n 240
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:885:160:14:CARD-G4-9 round-3 复审（静态审阅 + 只读复算）。你 round-2 裁定 10/13 CLOSED，三项 NOT-CLOSED：BLOCKER-1（--out 守卫比 resolve 字符串，hardlink 与 case-only 别名绕过截断输入）、HIGH-1（full_body_verified 只核 sha 不核长度且排在 anomaly 分支前，anomaly 记录被判 byte_exact）、HIGH-3（chmod 000 根 exit 0 假判 unrecoverable；glob 跟随 symlink 逃逸出根）；另 3 新 LOW（full_verified 长度范围应 131-180、distribution 省略 0 值键、line_count 数 LF 与 records 的 splitlines 口径不一）。开发方以 commit 73102875 提交整改。请只读复核这 6 项是否闭合：
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:899:186:1214: - **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:901:188:1219: - **HIGH-3（transcript 归因折叠）**：恰 1 个常规文件命中才算归因（多命中 = ambiguous 拒采信）；glob 改递归下探；transcripts 根缺失整体 exit 2（拒绝产出 unrecoverable 假象）。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:905:192:1232:+- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:906:193:1233:+- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:919:213:1937:99:- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:923:217:1946:117:- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:924:218:1947:118:- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:928:226:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:931:229:2146:    10	| HIGH-1 | **NOT-CLOSED** | round-1 三个反例本身均已翻转为 `anomaly/FAIL → unrecoverable`；非法 64 字符非 hex 也被拒。但新增组合反例：`episode_body="abc"`、`episode_body_full="abc"`、SHA 正确、声明长度 `999`，实际得到 `inline_state=anomaly` 后仍被判 `byte_exact`。原因是 [`full_body_verified()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:99)只核 SHA，不核长度，并在 [anomaly 分支之前](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:285)被采信。这直接反驳报告“anomaly 一律 unrecoverable”。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:932:230:2147:    11	| HIGH-2 | **CLOSED** | missing、显式 `null`、字面 `"None"` 不再合组；数字 `123` 与字符串 `"123"` 分离；非前缀多 token 均 `attribution_conflict=true/unrecoverable`；合法前缀组统一取最长 token。真实入口反例全部通过。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:933:231:2148:    12	| HIGH-3 | **NOT-CLOSED** | 不存在根目录已 exit 2；递归唯一命中、多命中冲突、目录伪命中也通过。但“不可见”仍未闭合：存在但 `chmod 000` 的根会 exit 0 并假判 `unrecoverable`。此外 [`glob + os.path.isfile`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:134)跟随 symlink：根内 `.jsonl` symlink 指向根外 `.txt`、以及 symlink 目录逃逸到根外树，均被判唯一来源并进入 `approximate`。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:942:243:2762:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:117:- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:944:245:2765:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:7:| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:945:246:2766:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:8:| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:946:247:2767:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:10:| HIGH-1 | **NOT-CLOSED** | round-1 三个反例本身均已翻转为 `anomaly/FAIL → unrecoverable`；非法 64 字符非 hex 也被拒。但新增组合反例：`episode_body="abc"`、`episode_body_full="abc"`、SHA 正确、声明长度 `999`，实际得到 `inline_state=anomaly` 后仍被判 `byte_exact`。原因是 [`full_body_verified()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:99)只核 SHA，不核长度，并在 [anomaly 分支之前](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:285)被采信。这直接反驳报告“anomaly 一律 unrecoverable”。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:947:248:2768:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:12:| HIGH-3 | **NOT-CLOSED** | 不存在根目录已 exit 2；递归唯一命中、多命中冲突、目录伪命中也通过。但“不可见”仍未闭合：存在但 `chmod 000` 的根会 exit 0 并假判 `unrecoverable`。此外 [`glob + os.path.isfile`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:134)跟随 symlink：根内 `.jsonl` symlink 指向根外 `.txt`、以及 symlink 目录逃逸到根外树，均被判唯一来源并进入 `approximate`。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:948:249:2769:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:14:| MEDIUM-2 | **CLOSED** | [报告 §6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:78)、[ledger duplicate_clusters](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:60)及逐条 `reference_time` 已落地；6 簇全部逐行对账。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:949:250:2772:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:14:CARD-G4-9 round-3 复审（静态审阅 + 只读复算）。你 round-2 裁定 10/13 CLOSED，三项 NOT-CLOSED：BLOCKER-1（--out 守卫比 resolve 字符串，hardlink 与 case-only 别名绕过截断输入）、HIGH-1（full_body_verified 只核 sha 不核长度且排在 anomaly 分支前，anomaly 记录被判 byte_exact）、HIGH-3（chmod 000 根 exit 0 假判 unrecoverable；glob 跟随 symlink 逃逸出根）；另 3 新 LOW（full_verified 长度范围应 131-180、distribution 省略 0 值键、line_count 数 LF 与 records 的 splitlines 口径不一）。开发方以 commit 73102875 提交整改。请只读复核这 6 项是否闭合：
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:950:252:2792:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1232:+- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:951:253:2793:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1234:+- **新 LOW ×3**：full_verified 长度范围修正为 131–180；台账 `class_distribution`/`recoverability_distribution` 补零并新增 `inline_state_distribution`（固定 schema，消费者无需补齐缺席键）；`line_count` 改用 `splitlines()` 与 records 同口径（原 `count("\n")` 在 bare CR / U+2028 下会与 records 数不一致）。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:952:254:2809:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1946:117:- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:953:255:2810:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1948:119:- **新 LOW ×3**：full_verified 长度范围修正为 131–180；台账 `class_distribution`/`recoverability_distribution` 补零并新增 `inline_state_distribution`（固定 schema，消费者无需补齐缺席键）；`line_count` 改用 `splitlines()` 与 records 同口径（原 `count("\n")` 在 bare CR / U+2028 下会与 records 数不一致）。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:954:256:2815:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:955:257:2816:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2144:     8	| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:956:258:2817:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2146:    10	| HIGH-1 | **NOT-CLOSED** | round-1 三个反例本身均已翻转为 `anomaly/FAIL → unrecoverable`；非法 64 字符非 hex 也被拒。但新增组合反例：`episode_body="abc"`、`episode_body_full="abc"`、SHA 正确、声明长度 `999`，实际得到 `inline_state=anomaly` 后仍被判 `byte_exact`。原因是 [`full_body_verified()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:99)只核 SHA，不核长度，并在 [anomaly 分支之前](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:285)被采信。这直接反驳报告“anomaly 一律 unrecoverable”。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:957:259:2818:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2148:    12	| HIGH-3 | **NOT-CLOSED** | 不存在根目录已 exit 2；递归唯一命中、多命中冲突、目录伪命中也通过。但“不可见”仍未闭合：存在但 `chmod 000` 的根会 exit 0 并假判 `unrecoverable`。此外 [`glob + os.path.isfile`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:134)跟随 symlink：根内 `.jsonl` symlink 指向根外 `.txt`、以及 symlink 目录逃逸到根外树，均被判唯一来源并进入 `approximate`。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:958:260:2819:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2150:    14	| MEDIUM-2 | **CLOSED** | [报告 §6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:78)、[ledger duplicate_clusters](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:60)及逐条 `reference_time` 已落地；6 簇全部逐行对账。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:959:261:2850:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:61:- **3 新 LOW**：full_verified 长度范围修正 131–180；台账三个 distribution 补零并新增 `inline_state_distribution`；`line_count` 与 records 改用同一 `splitlines()` 口径。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:965:274:3511:| HIGH-1 | **CLOSED / PASS** | [`full_body_verified()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:102)现有 SHA+严格长度门；[真实判定链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:340)在 full-body 分支前要求 `state != anomaly`。更强反例——full 本身 SHA/长度完全有效，但 inline 不符——仍落 `anomaly → unrecoverable`。无其它调用入口。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:968:277:3514:| LOW：distribution 零键 | **CLOSED** | [固定 schema 生成链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:437)与 [ledger](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:43)均包含 `unexpected/anomaly/unrecoverable: 0`，并新增 inline 三态。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:972:282:3534:所以：**冻结的 92 条 ledger 数值可采信；CARD-G4-9 生成器与整卡验收仍被 BLOCKER-1、HIGH-3 阻断。** 本轮未修改仓库或受审数据，未执行破坏性 fixture/G4-10 重放；Graphiti 工具本轮不可用。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:975:285:3544:| HIGH-1 | **CLOSED / PASS** | [`full_body_verified()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:102)现有 SHA+严格长度门；[真实判定链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:340)在 full-body 分支前要求 `state != anomaly`。更强反例——full 本身 SHA/长度完全有效，但 inline 不符——仍落 `anomaly → unrecoverable`。无其它调用入口。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:978:288:3547:| LOW：distribution 零键 | **CLOSED** | [固定 schema 生成链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:437)与 [ledger](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:43)均包含 `unexpected/anomaly/unrecoverable: 0`，并新增 inline 三态。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:982:293:3567:所以：**冻结的 92 条 ledger 数值可采信；CARD-G4-9 生成器与整卡验收仍被 BLOCKER-1、HIGH-3 阻断。** 本轮未修改仓库或受审数据，未执行破坏性 fixture/G4-10 重放；Graphiti 工具本轮不可用。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:997:373:+    # 会把"没搜到"与"搜不了"混为一谈，产出假 unrecoverable。遍历出错即 fail-closed。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1016:584:    23	    unrecoverable 并显式给 anomaly basis（不谎称"截断前缀"）。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1018:594:    33	    （chmod 000）时整体 exit 2（拒绝在源不可见时产出 unrecoverable 假象）；
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1030:715:   154	    # 会把"没搜到"与"搜不了"混为一谈，产出假 unrecoverable。遍历出错即 fail-closed。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1041:856:   295	    # 并把全部记录假判 unrecoverable —— 同样 fail-closed 拒诊。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1050:938:   377	    unrecoverable_keys = []
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1053:954:   393	            recover = "unrecoverable"
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1054:957:   396	            recover = "unrecoverable"
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1055:967:   406	            recover = "unrecoverable"
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1056:977:   416	        if recover == "unrecoverable":
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1057:978:   417	            unrecoverable_keys.append(stable_key)
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1060:1050:   489	            k: recover_dist.get(k, 0) for k in ["byte_exact", "approximate", "unrecoverable"]
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1062:1055:   494	        "unrecoverable_list": unrecoverable_keys,
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1081:1184:    72	| **不可恢复**（unrecoverable） | **0** | — |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1085:1196:    84	逐条另带 `class / inline_state / recoverability / transcript_paths / transcript_match_count / attribution_conflict / error_excerpt / failed_at / reference_time`，G4-10 可直接按 `recoverability` 分桶排重放优先级（建议：4 条 byte_exact 先行——但其中 3 条 group_id 为已弃用 `vault:default`，重放前需按 D16 规约重映射并过 `to_physical_group_id()`；89 条 budget_400 重放前必须先修 context 超限根因，否则原样重放必然复现 400）。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1089:1206:    94	| 负例门（round-1 整改自证） | `--out`==`--dlq` → exit 2 拒写、DLQ 完好；transcripts 根缺失 → exit 2 拒诊；sha 匹配但长度不符（round-1 HIGH-1 反例①）→ anomaly/unrecoverable；坏 JSON 行/空行 → unparseable 逐行入台账不拒诊 |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1090:1207:    95	| 负例门（round-2 整改自证） | **hardlink** 指向 DLQ 的 --out → exit 2 + DLQ sha 不变；**case-only 别名**（`DLQ.jsonl`）→ exit 2 + DLQ 完好；**anomaly + episode_body_full 组合**（sha 对但长度 999）→ anomaly/unrecoverable（不再翻案 byte_exact）；**chmod 000 根** → exit 2 拒诊；**symlink 逃逸**（根内 .jsonl → 根外 .txt）→ match_count=0/unrecoverable；正例回归：真实唯一命中仍 approximate |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1091:1211:    99	- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1093:1213:   101	- **BLOCKER-3（交付物未冻结漂移）**：以本卡 commit 冻结全部交付物 exact bytes（脚本/报告/台账/证据包同 commit）；grep-selfattest 已按最终版行号重生成并内嵌脚本 sha 前缀。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1094:1214:   102	- **HIGH-1（inline 判定不 fail-closed）**：full_verified 加长度精确匹配门；truncated_prefix 加 64-hex 合法性门；anomaly 一律 unrecoverable + 如实 basis（不再谎称截断、不再滑入 approximate）。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1096:1216:   104	- **HIGH-3（transcript 归因折叠）**：恰 1 个常规文件命中才算归因（多命中 = ambiguous 拒采信）；glob 改递归下探；transcripts 根缺失整体 exit 2（拒绝产出 unrecoverable 假象）。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1097:1217:   105	- **MEDIUM-1**：`episode_body_full` 在盘且 sha 对账通过 → byte_exact 采信（现网 0 条，通路已备）。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1105:1229:   117	- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1106:1230:   118	- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1109:1241:   129	  --qa-metrics-db "…/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db" \
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1119:1296:   377	    unrecoverable_keys = []
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1122:1312:   393	            recover = "unrecoverable"
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1123:1315:   396	            recover = "unrecoverable"
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1124:1325:   406	            recover = "unrecoverable"
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1125:1335:   416	        if recover == "unrecoverable":
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1126:1336:   417	            unrecoverable_keys.append(stable_key)
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1129:1408:   489	            k: recover_dist.get(k, 0) for k in ["byte_exact", "approximate", "unrecoverable"]
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1131:1413:   494	        "unrecoverable_list": unrecoverable_keys,
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1145:1522:/bin/zsh -lc "jq '{card,generated_at,dlq_file,total_lines,total_records,unparseable_lines,class_distribution,recoverability_distribution,inline_state_distribution,unrecoverable_count:(.unrecoverable_list|length),attribution_conflict_count:(.attribution_conflicts|length),duplicate_cluster_count:(.duplicate_clusters|length),duplicate_cluster_rows:([.duplicate_clusters[].occurrences]|add),record_count:(.records|length)}' '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json'
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1151:1550:    "unrecoverable": 0
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1152:1557:  "unrecoverable_count": 0,
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1158:1642:{"attribution_conflicts_from_records": 0, "class": {"budget_400": 89, "group_id_format": 1, "schema_entity_type": 2}, "duplicate_clusters_from_raw": 6, "duplicate_rows_from_raw": 29, "header_sha_match": true, "inline": {"full_verified": 4, "truncated_prefix": 88}, "ledger_derivation_mismatches": [], "lf_frames": 92, "parsed_records": 92, "raw_unparseable": 0, "recoverability_from_records": {"approximate": 88, "byte_exact": 4}, "source_sha256": "3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590", "transcript_path_metadata": {"missing": 0, "nonregular": 0, "symlink": 0, "unique": 7, "unreadable": 0}}
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1175:1961:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:20:--- (4) 写出口（唯一，且经 O_NOFOLLOW+fstat inode 校验后才 ftruncate）:
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1176:1962:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:21:517:            fd = os.open(args.out, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1177:1963:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:22:529:            os.ftruncate(fd, 0)
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1178:1972:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:41:189:        result["scan_errors"] = walk_errors[:5]
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1188:2049:**Identifying unrecoverable attribution_conflict handling**
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1189:2059:rg -n '\"class_distribution\"|\"recoverability_distribution\"|\"inline_state_distribution\"|\"unrecoverable_list\"|\"attribution_conflicts\"|\"duplicate_clusters\"|\"records\"' '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1199:2118:    58	  "unrecoverable": 0
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1200:2125:    65	 "unrecoverable_list": [],
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1203:2154:65: "unrecoverable_list": [],
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1208:2175:不过生成器仍出现一个无需竞态的截断反例：匹配 transcript 若是“不可读但可写”（如 owner mode `0200`），扫描会把它从 `transcript_paths` 清掉，输出保护集因此漏掉它，而 `--out` 又能按写权限打开并截断。另有扫描错误最终仍被写成 `unrecoverable`，与“拒绝裁定”声明相反。终裁会据此维持阻断。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1216:2307:| 3. HIGH-3 枚举 | **NOT-CLOSED** | 稳态目录 symlink、`scandir` 错误和 mode `000` 门已有改善。但 unreadable/walk error 设置 conflict 后，主链仍在 [395–397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:395)明确产出 `recoverability=unrecoverable`，直接反驳报告所称“既不宣称不可恢复” [报告:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:143)。此外 `os.walk.onerror` 只覆盖 `scandir`；逐条 `is_dir/stat` 错误可被静默当非候选，[islink→isfile→access→realpath](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:168)仍是路径级竞态。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1222:2316:- **HIGH**：扫描不可见性仍被终态化为 `unrecoverable`。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1235:2344:| 3. HIGH-3 枚举 | **NOT-CLOSED** | 稳态目录 symlink、`scandir` 错误和 mode `000` 门已有改善。但 unreadable/walk error 设置 conflict 后，主链仍在 [395–397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:395)明确产出 `recoverability=unrecoverable`，直接反驳报告所称“既不宣称不可恢复” [报告:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:143)。此外 `os.walk.onerror` 只覆盖 `scandir`；逐条 `is_dir/stat` 错误可被静默当非候选，[islink→isfile→access→realpath](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:168)仍是路径级竞态。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1241:2353:- **HIGH**：扫描不可见性仍被终态化为 `unrecoverable`。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1255:# CARD-G4-9 — DLQ 真实挂载 census 分诊报告
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1257:> **批次**: BATCH-2026-08-28-第五批 / CARD-G4-9（4h · wave 1 · 未来铺路）
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1324:| **可字节级**（byte_exact） | **4** | inline 正文全量：sha256 重算对账通过**且**长度精确匹配（fail-closed 双门）——重放可逐字节还原 episode |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1326:| **不可恢复**（unrecoverable） | **0** | inline 截断且经完整可见的扫描确认无在盘上游源 |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1339:逐条另带 `class / inline_state / recoverability / transcript_paths / transcript_match_count / attribution_conflict / error_excerpt / failed_at / reference_time`，G4-10 可直接按 `recoverability` 分桶排重放优先级（建议：4 条 byte_exact 先行——但其中 3 条 group_id 为已弃用 `vault:default`，重放前需按 D16 规约重映射并过 `to_physical_group_id()`；89 条 budget_400 重放前必须先修 context 超限根因，否则原样重放必然复现 400）。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1346:| grep 自证（import 行全 stdlib；neo4j/graphiti/bolt/app. import 0 命中；`--apply` 定义 0 命中；写模式 open 仅 `--out` 1 处且受路径碰撞守卫保护） | **PASS**（`grep-selfattest.txt`，含守卫在位证明） |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1349:| 负例门（round-1 整改自证） | `--out`==`--dlq` → exit 2 拒写、DLQ 完好；transcripts 根缺失 → exit 2 拒诊；sha 匹配但长度不符（round-1 HIGH-1 反例①）→ anomaly/unrecoverable；坏 JSON 行/空行 → unparseable 逐行入台账不拒诊 |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1350:| 负例门（round-2 整改自证） | **hardlink** 指向 DLQ 的 --out → exit 2 + DLQ sha 不变；**case-only 别名**（`DLQ.jsonl`）→ exit 2 + DLQ 完好；**anomaly + episode_body_full 组合**（sha 对但长度 999）→ anomaly/unrecoverable（不再翻案 byte_exact）；**chmod 000 根** → exit 2 拒诊；**symlink 逃逸**（根内 .jsonl → 根外 .txt）→ match_count=0/unrecoverable；正例回归：真实唯一命中仍 approximate |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1354:- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1356:- **BLOCKER-3（交付物未冻结漂移）**：以本卡 commit 冻结全部交付物 exact bytes（脚本/报告/台账/证据包同 commit）；grep-selfattest 已按最终版行号重生成并内嵌脚本 sha 前缀。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1357:- **HIGH-1（inline 判定不 fail-closed）**：full_verified 加长度精确匹配门；truncated_prefix 加 64-hex 合法性门；anomaly 一律 unrecoverable + 如实 basis（不再谎称截断、不再滑入 approximate）。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1359:- **HIGH-3（transcript 归因折叠）**：恰 1 个常规文件命中才算归因（多命中 = ambiguous 拒采信）；glob 改递归下探；transcripts 根缺失整体 exit 2（拒绝产出 unrecoverable 假象）。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1360:- **MEDIUM-1**：`episode_body_full` 在盘且 sha 对账通过 → byte_exact 采信（现网 0 条，通路已备）。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1372:- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1373:- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1384:  --qa-metrics-db "…/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db" \
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1411:- **HIGH（不可见被终态化为 unrecoverable）**：扫描受阻/冲突时主链仍产出 `unrecoverable`，与报告"既不宣称不可恢复"自相矛盾。**整改**：引入第四态 **`unverifiable`**（源可见性不足，basis 逐条说明是遍历受阻/不可读候选/归因冲突），distribution 与 `unverifiable_list` 同步。实测：不可读子树 → `unverifiable=1`，不再冒充 unrecoverable。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1418:== CARD-G4-9 / CARD-G4-16 artifact commit receipt ==
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1422:67ccebe1  CARD-G4-9 初版交付（脚本/报告/台账/证据包/round-1 审查/UAT）
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1427:d2827a6d  CARD-G4-9 round-4 整改（本 receipt 所描述的 commit）
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1432:/bin/zsh -lc "wc -c '_bmad-output/审查/codex-review-CARD-G4-9-round5.md' && sed -n '1,160p' '_bmad-output/审查/codex-review-CARD-G4-9-round5.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1434:   22875 _bmad-output/审查/codex-review-CARD-G4-9-round5.md
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1448:CARD-G4-9 round-5 终裁复审（静态审阅 + 只读复算，禁改任何文件）。你 round-4 裁定 1/6 CLOSED，提出 2 BLOCKER / 1 HIGH / 2 MEDIUM / 3 LOW。开发方以 commit d2827a6d + d8d887f2 提交整改，请逐条只读复核：
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1456:请对每项设计静态反例判断是否仍可绕过（尤其：保护集完整性、fd 身份与实际读取的绑定、unverifiable 与 unrecoverable 的语义边界、strict decode 的边界）。同时独立复算台账仍为 92 条 / class 89-2-1 / byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0 / 重复簇 6 簇 29 行 / unparseable 0。逐项 CLOSED/NOT-CLOSED + 总裁定（可验收/仍阻断）+ 新发现分级。若已可验收请明确说明；若仍阻断请说明**对一张只读 census 卡**而言该阻断是否与卡面范围相称。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1464:/bin/zsh -lc "rg -n -C 3 'CARD-G4-9|G4-9|census|round-4|adversarial|canvas-adversarial-audit' /Users/Heishing/.codex/memories/MEMORY.md" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1599:已锁定：当前分支 `card/s5-census`，HEAD 正是 `d8d887f29377…`，其父为整改提交 `d2827a6d…`。工作树在审阅开始时已有一个未跟踪的 `codex-review-CARD-G4-9-round5.md`（看起来是外部会话记录）；我只读、不触碰，也不会把它当作提交证据。接下来以已提交 blob 和原始台账输入为准。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1738:   314	        "--qa-metrics-db",
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1769:   345	    # 并把全部记录假判 unrecoverable —— 同样 fail-closed 拒诊。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1869:   443	    unrecoverable_keys = []
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1884:   458	            recover = "byte_exact"
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1888:   462	            recover = "byte_exact"
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1891:   465	            recover = "unrecoverable"
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1895:   469	            # 终态化为 unrecoverable 是不诚实的断言 —— 单列 unverifiable。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1916:   490	            recover = "unrecoverable"
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1926:   500	        if recover == "unrecoverable":
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1927:   501	            unrecoverable_keys.append(stable_key)
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1995:   565	        "card": "CARD-G4-9",
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2014:   584	            k: recover_dist.get(k, 0) for k in ["byte_exact", "approximate", "unverifiable", "unrecoverable"]
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2019:   589	        "unrecoverable_list": unrecoverable_keys,
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2097:     2	"""CARD-G4-9: dead-letter episodes 只读 census 分诊脚本。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2099:     4	BATCH-2026-08-28-第五批 / CARD-G4-9（G4-10 replay 的交接台账生成器）。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2106:    11	    **文件身份 (st_dev, st_ino) 比较**，与 --dlq/--compare/--qa-metrics-db
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2118:    23	    unrecoverable 并显式给 anomaly basis（不谎称"截断前缀"）。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2128:    33	    （chmod 000）时整体 exit 2（拒绝在源不可见时产出 unrecoverable 假象）；
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2133:    38	    重算 sha **且长度**双门对账通过才按 byte_exact 采信，且 anomaly 记录
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2226:   131	    但 episode_body_length=999）仍被判 byte_exact —— 与 inline 侧同门收紧。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2274:   179	    # 会把"没搜到"与"搜不了"混为一谈，产出假 unrecoverable。遍历出错即 fail-closed。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2281:/bin/zsh -lc "rg -n '不可读但可写|源侧 TOCTOU|不可见终态|非法 UTF-8|字段错型|root_prefix|fchmod|provenance|总裁定|BLOCKER' '_bmad-output/审查/codex-review-CARD-G4-9-round4.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2288:145:rg -n \"BLOCKER-1|HIGH-3|JSONL|framing|非 dict|provenance|PARTIAL|CLOSED|NOT-CLOSED|新发现|总裁定|protected_ids|O_NOFOLLOW|os\\.walk|line_count\" '_bmad-output/审查/codex-review-CARD-G4-9-round3.md' | head -n 240
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2289:160:14:CARD-G4-9 round-3 复审（静态审阅 + 只读复算）。你 round-2 裁定 10/13 CLOSED，三项 NOT-CLOSED：BLOCKER-1（--out 守卫比 resolve 字符串，hardlink 与 case-only 别名绕过截断输入）、HIGH-1（full_body_verified 只核 sha 不核长度且排在 anomaly 分支前，anomaly 记录被判 byte_exact）、HIGH-3（chmod 000 根 exit 0 假判 unrecoverable；glob 跟随 symlink 逃逸出根）；另 3 新 LOW（full_verified 长度范围应 131-180、distribution 省略 0 值键、line_count 数 LF 与 records 的 splitlines 口径不一）。开发方以 commit 73102875 提交整改。请只读复核这 6 项是否闭合：
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2298:186:1214: - **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2305:213:1937:99:- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2310:226:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2313:245:2765:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:7:| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2314:246:2766:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:8:| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2315:250:2772:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:14:CARD-G4-9 round-3 复审（静态审阅 + 只读复算）。你 round-2 裁定 10/13 CLOSED，三项 NOT-CLOSED：BLOCKER-1（--out 守卫比 resolve 字符串，hardlink 与 case-only 别名绕过截断输入）、HIGH-1（full_body_verified 只核 sha 不核长度且排在 anomaly 分支前，anomaly 记录被判 byte_exact）、HIGH-3（chmod 000 根 exit 0 假判 unrecoverable；glob 跟随 symlink 逃逸出根）；另 3 新 LOW（full_verified 长度范围应 131-180、distribution 省略 0 值键、line_count 数 LF 与 records 的 splitlines 口径不一）。开发方以 commit 73102875 提交整改。请只读复核这 6 项是否闭合：
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2316:256:2815:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2317:257:2816:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2144:     8	| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2325:282:3534:所以：**冻结的 92 条 ledger 数值可采信；CARD-G4-9 生成器与整卡验收仍被 BLOCKER-1、HIGH-3 阻断。** 本轮未修改仓库或受审数据，未执行破坏性 fixture/G4-10 重放；Graphiti 工具本轮不可用。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2329:293:3567:所以：**冻结的 92 条 ledger 数值可采信；CARD-G4-9 生成器与整卡验收仍被 BLOCKER-1、HIGH-3 阻断。** 本轮未修改仓库或受审数据，未执行破坏性 fixture/G4-10 重放；Graphiti 工具本轮不可用。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2340:1211:    99	- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2342:1213:   101	- **BLOCKER-3（交付物未冻结漂移）**：以本卡 commit 冻结全部交付物 exact bytes（脚本/报告/台账/证据包同 commit）；grep-selfattest 已按最终版行号重生成并内嵌脚本 sha 前缀。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2351:2175:不过生成器仍出现一个无需竞态的截断反例：匹配 transcript 若是“不可读但可写”（如 owner mode `0200`），扫描会把它从 `transcript_paths` 清掉，输出保护集因此漏掉它，而 `--out` 又能按写权限打开并截断。另有扫描错误最终仍被写成 `unrecoverable`，与“拒绝裁定”声明相反。终裁会据此维持阻断。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2369:/bin/zsh -lc "nl -ba '_bmad-output/审查/codex-review-CARD-G4-9-round4.md' | sed -n '2290,2365p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2388:  2307	| 3. HIGH-3 枚举 | **NOT-CLOSED** | 稳态目录 symlink、`scandir` 错误和 mode `000` 门已有改善。但 unreadable/walk error 设置 conflict 后，主链仍在 [395–397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:395)明确产出 `recoverability=unrecoverable`，直接反驳报告所称“既不宣称不可恢复” [报告:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:143)。此外 `os.walk.onerror` 只覆盖 `scandir`；逐条 `is_dir/stat` 错误可被静默当非候选，[islink→isfile→access→realpath](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:168)仍是路径级竞态。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2397:  2316	- **HIGH**：扫描不可见性仍被终态化为 `unrecoverable`。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2425:  2344	| 3. HIGH-3 枚举 | **NOT-CLOSED** | 稳态目录 symlink、`scandir` 错误和 mode `000` 门已有改善。但 unreadable/walk error 设置 conflict 后，主链仍在 [395–397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:395)明确产出 `recoverability=unrecoverable`，直接反驳报告所称“既不宣称不可恢复” [报告:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:143)。此外 `os.walk.onerror` 只覆盖 `scandir`；逐条 `is_dir/stat` 错误可被静默当非候选，[islink→isfile→access→realpath](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:168)仍是路径级竞态。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2434:  2353	- **HIGH**：扫描不可见性仍被终态化为 `unrecoverable`。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2457:**Evaluating anomaly unrecoverable versus unverifiable states**
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2483:     1	== CARD-G4-9 / CARD-G4-16 artifact commit receipt ==
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2487:     5	67ccebe1  CARD-G4-9 初版交付（脚本/报告/台账/证据包/round-1 审查/UAT）
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2492:    10	d2827a6d  CARD-G4-9 round-4 整改（本 receipt 所描述的 commit）
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2499:     1	# CARD-G4-9 — DLQ 真实挂载 census 分诊报告
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2501:     3	> **批次**: BATCH-2026-08-28-第五批 / CARD-G4-9（4h · wave 1 · 未来铺路）
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2575:/bin/zsh -lc "jq '{dlq_file,total_lines,total_records,class_distribution,recoverability_distribution,inline_state_distribution,unparseable_count:(.unparseable_lines|length),duplicate_cluster_count:(.duplicate_clusters|length),duplicate_cluster_rows:([.duplicate_clusters[].occurrences]|add),attribution_conflict_count:(.attribution_conflicts|length),unrecoverable_count:(.unrecoverable_list|length),unverifiable_count:(.unverifiable_list|length),qa_metrics_probe}' '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2595:    "byte_exact": 4,
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2598:    "unrecoverable": 0
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2609:  "unrecoverable_count": 0,
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2749:        attr[k]=("no_token",0)
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2750:        summary["no_token_groups"]+=1
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2780:        rr="byte_exact"
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2781:    elif ast in ("token_conflict","unverifiable","no_token"):
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2784:        rr="unrecoverable"
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2788:        rr="unrecoverable"
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2811:    "no_token_groups": 3,
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2831:    "byte_exact": 4
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2853:     2	 "card": "CARD-G4-9",
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2907:    56	  "byte_exact": 4,
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2910:    59	  "unrecoverable": 0
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2917:    66	 "unrecoverable_list": [],
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2954:/bin/zsh -lc "rg -n '0 写|只读|保护|qa_metrics|transcript|92|89|byte_exact|unverifiable|unrecoverable|验收' '_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2956:6:scope: "BATCH-2026-08-28-第五批 / CARD-G4-9 — live DLQ 92 条只读 census：分类/SHA 对账/可恢复性三态/挂载真相，产出 G4-10 交接台账"
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2962:28:| 脚本只读自证（判据 a） | import 行全 stdlib；neo4j/graphiti/bolt/app. import **0 命中**；`--apply` 定义 **0 命中**；写模式 open 仅台账 `--out` 1 处 | `G4-9-evidence/grep-selfattest.txt` |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2968:35:| Codex 独立审查 round-1 | **BLOCKED**（3 BLOCKER：--out 可截断输入 / 快照不原子 / 交付物未冻结；3 HIGH：inline 判定 fail-open / request_id 归因传染 / transcript 归因折叠；3 MEDIUM + 4 LOW。同时确认：**当前 92 条数字逐项 0 mismatch**、class/三态/家族计数全对） | `_bmad-output/审查/codex-review-CARD-G4-9.md` |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2969:37:| Codex 复审 round-2 | **仍阻断**（10/13 CLOSED；BLOCKER-1/HIGH-1/HIGH-3 未真正闭合 + 3 新 LOW）。同时独立复算确认：67ccebe1 冻结生效、92 条数字与 6/29 重复簇全部可复算 | `_bmad-output/审查/codex-review-CARD-G4-9-round2.md`（codex 被 cyber 误拦，内容由 stdout 抢救存档） |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2970:40:| round-3 findings 逐条整改 | **6/6 完成**：transcript 并入保护集 / O_NOFOLLOW+fstat 消 TOCTOU / os.walk 替 glob（不跟随目录 symlink+遍历错误显式捕获）/ 不可读候选 fail-closed / JSONL 严格 LF 分帧 / 非 dict 归 unparseable。6 条新反例实测全过、数字第三次不变 | 报告 §7d + `grep-selfattest.txt` |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2971:42:| round-4 findings 逐条整改 | **9/9 完成**：全候选入保护集 / 读侧 fd 身份消源侧 TOCTOU / 新增 unverifiable 第四态 / FIFO 设备门 / strict UTF-8 / 3 条错型与边界 LOW / provenance receipt。5 条新反例实测全过；第四次全量重跑数字仍不变 | 报告 §7e + `grep-selfattest.txt` |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2973:50:- **HIGH-1 inline 判定 fail-open**：sha 匹配但长度不符会误判 full_verified（反例实测）。整改：长度精确匹配门 + 64-hex 合法性门 + anomaly 一律 fail-closed（unrecoverable + 如实 basis）。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2974:52:- **HIGH-3 transcript 归因折叠**：多命中照单全收、目录缺失误判 unrecoverable=88（实测复现）。整改：恰 1 常规文件命中门 + 递归 glob + 目录缺失 exit 2 拒诊。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2981:86:- **把"看不见"说成"不可恢复"**：扫描受阻时仍输出 `unrecoverable`，与报告里"既不宣称不可恢复"自相矛盾。→ 新增第四态 **`unverifiable`**，逐条写明是遍历受阻还是候选不可读。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2988:/bin/zsh -lc "rg -n '\"total_lines\"|\"total_records\"|\"unparseable_lines\"|\"class_distribution\"|\"recoverability_distribution\"|\"inline_state_distribution\"|\"unrecoverable_list\"|\"unverifiable_list\"|\"duplicate_clusters\"' '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2996:66: "unrecoverable_list": [],
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3063:/bin/zsh -lc "nl -ba '_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md' | sed -n '145,175p'; nl -ba '_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md' | sed -n '8,45p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3077:   157	- **HIGH（不可见被终态化为 unrecoverable）**：扫描受阻/冲突时主链仍产出 `unrecoverable`，与报告"既不宣称不可恢复"自相矛盾。**整改**：引入第四态 **`unverifiable`**（源可见性不足，basis 逐条说明是遍历受阻/不可读候选/归因冲突），distribution 与 `unverifiable_list` 同步。实测：不可读子树 → `unverifiable=1`，不再冒充 unrecoverable。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3086:    10	# UAT · CARD-G4-9 DLQ 真实挂载 census 分诊
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3104:    28	| 脚本只读自证（判据 a） | import 行全 stdlib；neo4j/graphiti/bolt/app. import **0 命中**；`--apply` 定义 **0 命中**；写模式 open 仅台账 `--out` 1 处 | `G4-9-evidence/grep-selfattest.txt` |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3111:    35	| Codex 独立审查 round-1 | **BLOCKED**（3 BLOCKER：--out 可截断输入 / 快照不原子 / 交付物未冻结；3 HIGH：inline 判定 fail-open / request_id 归因传染 / transcript 归因折叠；3 MEDIUM + 4 LOW。同时确认：**当前 92 条数字逐项 0 mismatch**、class/三态/家族计数全对） | `_bmad-output/审查/codex-review-CARD-G4-9.md` |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3113:    37	| Codex 复审 round-2 | **仍阻断**（10/13 CLOSED；BLOCKER-1/HIGH-1/HIGH-3 未真正闭合 + 3 新 LOW）。同时独立复算确认：67ccebe1 冻结生效、92 条数字与 6/29 重复簇全部可复算 | `_bmad-output/审查/codex-review-CARD-G4-9-round2.md`（codex 被 cyber 误拦，内容由 stdout 抢救存档） |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3114:    38	| round-2 findings 逐条整改 | **6/6 完成**：inode 身份守卫封 hardlink+大小写别名 / full_body 长度门+anomaly 前置 / 不可读根 exit 2+symlink 逃逸拒采信 / 3 新 LOW。5 条新负例实测全过、正例无回归、数字仍逐项一致 | 报告 §7/§7c + `grep-selfattest.txt` |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3115:    39	| Codex 复审 round-3 | **仍阻断**（4/6 CLOSED；BLOCKER-1/HIGH-3 判 PARTIAL + 1 新 MEDIUM + 2 新 LOW）。同时确认：HIGH-1 与三条 LOW 已闭合、台账数字有效且与 commit 字节一致 | `_bmad-output/审查/codex-review-CARD-G4-9-round3.md` |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3116:    40	| round-3 findings 逐条整改 | **6/6 完成**：transcript 并入保护集 / O_NOFOLLOW+fstat 消 TOCTOU / os.walk 替 glob（不跟随目录 symlink+遍历错误显式捕获）/ 不可读候选 fail-closed / JSONL 严格 LF 分帧 / 非 dict 归 unparseable。6 条新反例实测全过、数字第三次不变 | 报告 §7d + `grep-selfattest.txt` |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3117:    41	| Codex 复审 round-4 | **仍阻断**（1/6 CLOSED；2 新 BLOCKER + 1 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round4.md` |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3118:    42	| round-4 findings 逐条整改 | **9/9 完成**：全候选入保护集 / 读侧 fd 身份消源侧 TOCTOU / 新增 unverifiable 第四态 / FIFO 设备门 / strict UTF-8 / 3 条错型与边界 LOW / provenance receipt。5 条新反例实测全过；第四次全量重跑数字仍不变 | 报告 §7e + `grep-selfattest.txt` |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3135:  ✓ 锁定 HEAD、提交链、工作树状态、CARD-G4-9 报告与生产入口
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3149:/bin/zsh -lc "rg -n -C 2 'round-4|mode 0200|utf8|FIFO|unverifiable|fchmod|wrong|request_id|all_candidate|snapshot_file' '_bmad-output/审查/G4-9-evidence/grep-selfattest.txt'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3151:1:== CARD-G4-9 只读自证（round-4 整改版, f27531b8a50f035d…） ==
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3315:? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round5.md"
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3322:  ✓ 锁定 HEAD、提交链、工作树状态、CARD-G4-9 报告与生产入口
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3332:总裁定：**仍阻断 / CARD-G4-9 不可验收**。  
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3341:| 3. `unverifiable` 四态 | **NOT-CLOSED · HIGH** | distribution/list 同步已实现。但 `anomaly→unrecoverable` 位于 conflict 判断之前，[script:464](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:464)：`anomaly + 扫描受阻/不可读/归因冲突` 仍被假终态化。另无 token 时未扫描即返回，truncated 记录随后被称为“无在盘源”，也应是 `unverifiable`。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3356:- byte_exact **4**；approximate **88**；unverifiable **0**；unrecoverable **0**
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3370:这个阻断与“一张只读 census 卡”的范围**完全相称**：报告和 UAT 明确承诺纯只读、零写入，[UAT:13](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:13)。残留反例能直接截断或修改本卡正在保护的恢复源，不是范围外的生产级加固要求。
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3377:总裁定：**仍阻断 / CARD-G4-9 不可验收**。  
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3386:| 3. `unverifiable` 四态 | **NOT-CLOSED · HIGH** | distribution/list 同步已实现。但 `anomaly→unrecoverable` 位于 conflict 判断之前，[script:464](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:464)：`anomaly + 扫描受阻/不可读/归因冲突` 仍被假终态化。另无 token 时未扫描即返回，truncated 记录随后被称为“无在盘源”，也应是 `unverifiable`。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3401:- byte_exact **4**；approximate **88**；unverifiable **0**；unrecoverable **0**
./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3415:这个阻断与“一张只读 census 卡”的范围**完全相称**：报告和 UAT 明确承诺纯只读、零写入，[UAT:13](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:13)。残留反例能直接截断或修改本卡正在保护的恢复源，不是范围外的生产级加固要求。
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:2: "card": "CARD-G4-9",
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:56:  "byte_exact": 4,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:59:  "unrecoverable": 0
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:66: "unrecoverable_list": [],
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:202:   "attribution_conflict_reason": "no_token",
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:203:   "recoverability": "byte_exact",
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:228:   "attribution_conflict_reason": "no_token",
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:229:   "recoverability": "byte_exact",
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:254:   "attribution_conflict_reason": "no_token",
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:255:   "recoverability": "byte_exact",
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:282:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:310:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:338:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:366:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:394:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:422:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:450:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:478:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:506:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:534:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:562:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:590:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:618:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:646:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:674:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:702:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:730:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:758:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:786:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:814:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:842:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:870:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:898:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:926:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:954:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:982:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:1010:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:1038:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:1066:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:1094:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:1122:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:1150:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:1178:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:1206:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:1234:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:1262:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:1290:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:1318:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:1346:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:1374:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:1402:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:1430:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:1458:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:1486:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:1514:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:1542:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:1570:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:1598:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:1626:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:1654:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:1682:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:1710:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:1738:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:1766:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:1794:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:1822:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:1850:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:1878:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:1906:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:1934:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:1962:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:1990:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:2018:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:2046:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:2074:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:2102:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:2130:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:2158:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:2186:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:2214:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:2242:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:2243:   "recoverability": "byte_exact",
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:2270:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:2298:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:2326:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:2354:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:2382:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:2410:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:2438:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:2466:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:2494:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:2522:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:2550:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:2578:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:2606:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:2634:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:2662:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:2690:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:2718:   "attribution_conflict_reason": null,
./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:2746:   "attribution_conflict_reason": null,
./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:3:title: "UAT · CARD-G4-9 DLQ 真实挂载 census 分诊（2026-08-28）"
./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:6:scope: "BATCH-2026-08-28-第五批 / CARD-G4-9 — live DLQ 92 条只读 census：分类/SHA 对账/可恢复性三态/挂载真相，产出 G4-10 交接台账"
./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:10:# UAT · CARD-G4-9 DLQ 真实挂载 census 分诊
./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:28:| 脚本只读自证（判据 a） | import 行全 stdlib；neo4j/graphiti/bolt/app. import **0 命中**；`--apply` 定义 **0 命中**；写模式 open 仅台账 `--out` 1 处 | `G4-9-evidence/grep-selfattest.txt` |
./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:35:| Codex 独立审查 round-1 | **BLOCKED**（3 BLOCKER：--out 可截断输入 / 快照不原子 / 交付物未冻结；3 HIGH：inline 判定 fail-open / request_id 归因传染 / transcript 归因折叠；3 MEDIUM + 4 LOW。同时确认：**当前 92 条数字逐项 0 mismatch**、class/三态/家族计数全对） | `_bmad-output/审查/codex-review-CARD-G4-9.md` |
./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:37:| Codex 复审 round-2 | **仍阻断**（10/13 CLOSED；BLOCKER-1/HIGH-1/HIGH-3 未真正闭合 + 3 新 LOW）。同时独立复算确认：67ccebe1 冻结生效、92 条数字与 6/29 重复簇全部可复算 | `_bmad-output/审查/codex-review-CARD-G4-9-round2.md`（codex 被 cyber 误拦，内容由 stdout 抢救存档） |
./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:38:| round-2 findings 逐条整改 | **6/6 完成**：inode 身份守卫封 hardlink+大小写别名 / full_body 长度门+anomaly 前置 / 不可读根 exit 2+symlink 逃逸拒采信 / 3 新 LOW。5 条新负例实测全过、正例无回归、数字仍逐项一致 | 报告 §7/§7c + `grep-selfattest.txt` |
./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:39:| Codex 复审 round-3 | **仍阻断**（4/6 CLOSED；BLOCKER-1/HIGH-3 判 PARTIAL + 1 新 MEDIUM + 2 新 LOW）。同时确认：HIGH-1 与三条 LOW 已闭合、台账数字有效且与 commit 字节一致 | `_bmad-output/审查/codex-review-CARD-G4-9-round3.md` |
./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:40:| round-3 findings 逐条整改 | **6/6 完成**：transcript 并入保护集 / O_NOFOLLOW+fstat 消 TOCTOU / os.walk 替 glob（不跟随目录 symlink+遍历错误显式捕获）/ 不可读候选 fail-closed / JSONL 严格 LF 分帧 / 非 dict 归 unparseable。6 条新反例实测全过、数字第三次不变 | 报告 §7d + `grep-selfattest.txt` |
./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:41:| Codex 复审 round-4 | **仍阻断**（1/6 CLOSED；2 新 BLOCKER + 1 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round4.md` |
./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:42:| round-4 findings 逐条整改 | **9/9 完成**：全候选入保护集 / 读侧 fd 身份消源侧 TOCTOU / 新增 unverifiable 第四态 / FIFO 设备门 / strict UTF-8 / 3 条错型与边界 LOW / provenance receipt。5 条新反例实测全过；第四次全量重跑数字仍不变 | 报告 §7e + `grep-selfattest.txt` |
./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:43:| Codex 复审 round-5 | **仍阻断**（3/8 CLOSED；2 BLOCKER + 2 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round5.md` |
./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:44:| round-5 findings 逐条整改 | **9/9 完成**：先扫描后判定（冲突候选亦入保护集）/ QA DB fd 身份+复核 / 可见性优先于 anomaly / fchmod 后置于碰撞检查 / QA DB 特殊文件门 / no_token 归 unverifiable / 3 条 LOW。6 条新反例实测全过；第五次全量重跑数字仍不变 | 报告 §7f |
./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:45:| Codex 复审 round-6 | **6/9 CLOSED**（visibility 优先/fchmod 顺序/no_token 语义/3 条 LOW 已闭合）；剩 2 BLOCKER + 1 MEDIUM 揭示保护集**依赖枚举完整性**的架构缺陷 + 3 新发现 | `_bmad-output/审查/codex-review-CARD-G4-9-round6.md` |
./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:46:| round-6 findings 整改 | **架构级修复 + 6 项**：新增不依赖枚举的**路径层防御**（--out 禁落 transcripts 根内 / 禁等于任一输入 realpath）、QA DB 验证 fd 保持打开至复核完毕、no_token 亦扫描、证据包重生成、ledger 冲突原因自描述、lone surrogate 回退。反例实测：0333 隐藏目录内 transcript 作 --out → exit 2 完好 | 报告 §7g |
./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:54:- **HIGH-1 inline 判定 fail-open**：sha 匹配但长度不符会误判 full_verified（反例实测）。整改：长度精确匹配门 + 64-hex 合法性门 + anomaly 一律 fail-closed（unrecoverable + 如实 basis）。
./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:56:- **HIGH-3 transcript 归因折叠**：多命中照单全收、目录缺失误判 unrecoverable=88（实测复现）。整改：恰 1 常规文件命中门 + 递归 glob + 目录缺失 exit 2 拒诊。
./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:90:- **把"看不见"说成"不可恢复"**：扫描受阻时仍输出 `unrecoverable`，与报告里"既不宣称不可恢复"自相矛盾。→ 新增第四态 **`unverifiable`**，逐条写明是遍历受阻还是候选不可读。
./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:101:- **anomaly 吞掉了"看不见"**：`anomaly→unrecoverable` 排在可见性判断之前，扫描受阻时仍断言"不可恢复"。→ 判定链改为**可见性优先**。
./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:115:另修：QA DB 的验证 fd 改为**保持打开**到复核完毕（堵 ABA）；`no_token` 分支也扫描（原本完全不扫，候选进不了保护集）；证据包每轮重生成（round-6 指出我的 self-attest 停留在 round-4 的旧 SHA，属实）；台账新增冲突原因自描述。
./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:125:- `_bmad-output/审查/codex-review-CARD-G4-9.md` — Codex 独立审查存档
./_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt:1:== CARD-G4-9 / CARD-G4-16 artifact commit receipt ==
./_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt:5:67ccebe1  CARD-G4-9 初版交付（脚本/报告/台账/证据包/round-1 审查/UAT）
./_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt:10:d2827a6d  CARD-G4-9 round-4 整改
./_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt:12:4c125f19  CARD-G4-9 round-5 整改
./_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt:13:5b371253  CARD-G4-9 round-6 架构级修复（本 receipt 当前版所描述的 commit）
./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:1:# CARD-G4-9 — DLQ 真实挂载 census 分诊报告
./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:3:> **批次**: BATCH-2026-08-28-第五批 / CARD-G4-9（4h · wave 1 · 未来铺路）
./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:70:| **可字节级**（byte_exact） | **4** | inline 正文全量：sha256 重算对账通过**且**长度精确匹配（fail-closed 双门）——重放可逐字节还原 episode |
./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:72:| **不可恢复**（unrecoverable） | **0** | inline 截断且经完整可见的扫描确认无在盘上游源 |
./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:85:逐条另带 `class / inline_state / recoverability / transcript_paths / transcript_match_count / attribution_conflict / error_excerpt / failed_at / reference_time`，G4-10 可直接按 `recoverability` 分桶排重放优先级（建议：4 条 byte_exact 先行——但其中 3 条 group_id 为已弃用 `vault:default`，重放前需按 D16 规约重映射并过 `to_physical_group_id()`；89 条 budget_400 重放前必须先修 context 超限根因，否则原样重放必然复现 400）。
./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:92:| grep 自证（import 行全 stdlib；neo4j/graphiti/bolt/app. import 0 命中；`--apply` 定义 0 命中；写模式 open 仅 `--out` 1 处且受路径碰撞守卫保护） | **PASS**（`grep-selfattest.txt`，含守卫在位证明） |
./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:95:| 负例门（round-1 整改自证） | `--out`==`--dlq` → exit 2 拒写、DLQ 完好；transcripts 根缺失 → exit 2 拒诊；sha 匹配但长度不符（round-1 HIGH-1 反例①）→ anomaly/unrecoverable；坏 JSON 行/空行 → unparseable 逐行入台账不拒诊 |
./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:96:| 负例门（round-2 整改自证） | **hardlink** 指向 DLQ 的 --out → exit 2 + DLQ sha 不变；**case-only 别名**（`DLQ.jsonl`）→ exit 2 + DLQ 完好；**anomaly + episode_body_full 组合**（sha 对但长度 999）→ anomaly/unrecoverable（不再翻案 byte_exact）；**chmod 000 根** → exit 2 拒诊；**symlink 逃逸**（根内 .jsonl → 根外 .txt）→ match_count=0/unrecoverable；正例回归：真实唯一命中仍 approximate |
./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:100:- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:102:- **BLOCKER-3（交付物未冻结漂移）**：以本卡 commit 冻结全部交付物 exact bytes（脚本/报告/台账/证据包同 commit）；grep-selfattest 已按最终版行号重生成并内嵌脚本 sha 前缀。
./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:103:- **HIGH-1（inline 判定不 fail-closed）**：full_verified 加长度精确匹配门；truncated_prefix 加 64-hex 合法性门；anomaly 一律 unrecoverable + 如实 basis（不再谎称截断、不再滑入 approximate）。
./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:105:- **HIGH-3（transcript 归因折叠）**：恰 1 个常规文件命中才算归因（多命中 = ambiguous 拒采信）；glob 改递归下探；transcripts 根缺失整体 exit 2（拒绝产出 unrecoverable 假象）。
./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:106:- **MEDIUM-1**：`episode_body_full` 在盘且 sha 对账通过 → byte_exact 采信（现网 0 条，通路已备）。
./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:118:- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:119:- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:130:  --qa-metrics-db "…/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db" \
./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:157:- **HIGH（不可见被终态化为 unrecoverable）**：扫描受阻/冲突时主链仍产出 `unrecoverable`，与报告"既不宣称不可恢复"自相矛盾。**整改**：引入第四态 **`unverifiable`**（源可见性不足，basis 逐条说明是遍历受阻/不可读候选/归因冲突），distribution 与 `unverifiable_list` 同步。实测：不可读子树 → `unverifiable=1`，不再冒充 unrecoverable。
./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:171:- **HIGH①（anomaly 吞掉不可见性）**：`anomaly→unrecoverable` 排在 conflict 判断之前，`anomaly + 扫描受阻` 仍被假终态化。**整改**：判定链改为**可见性优先**——归因不可核验时无论 inline 状态一律 `unverifiable`，basis 逐条写明原因（无 token / token 冲突 / 扫描受阻 / 候选 stat 失败 / 不可读候选 / 多命中 ambiguous），并附注 inline 是否也 anomaly。实测：anomaly+不可读子树 → `unverifiable`。
./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:174:- **MEDIUM（无 token 未扫描即判不可恢复）**：改为 `unverifiable` + `no_token` 标记（见 HIGH①）。
./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:177:**归因冲突计数由 0 变为 3（如实说明）**：round-5 起"名字不含 session token"被诚实标记为 `no_token`（未做归因扫描），命中的正是 3 条 `callout_annotation` 记录。它们 inline 正文全量、sha 对账通过，**不依赖 transcript**，故仍判 `byte_exact`——三态分布不变（4/88/0/0），88 条 approximate 仍全部为唯一 transcript 命中。这是标注口径变诚实，不是结论变化。
./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:179:round-5 整改后第五次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变——五轮整改数字全程未变**。
./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:183:round-6 确认 visibility 优先、fchmod 顺序、no_token 语义、三条 LOW 共 6 项 CLOSED，并揭示了一个**架构层面的根因**：
./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:189:- **BLOCKER① 补充修复**：`no_token` 分支原本完全不扫描（`all_candidate_paths=[]`）→ 改为**无论有无 token 都遍历**，所有 `.jsonl` 一律入保护集口径。
./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:190:- **MEDIUM（证据包漂移）**：`grep-selfattest.txt` 曾停留在 round-4 的脚本 SHA 与旧行号、receipt 未含最新 commit——这是我的疏漏。已重生成（内嵌当前脚本 sha256 + 生成时点声明），receipt 随本轮补链。
./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:191:- **LOW ×3**：ledger 新增 `attribution_conflict_reason` 自描述（本次 92 条：`no_token` 3 / 其余 89 无冲突）；`json.dumps` 对 lone surrogate 回退 `ensure_ascii=True` 并显式标注，不再整次 census 拒绝；`stat_failures` 分支保留（Codex 确认非额外绕过，仅基本不可达）。
./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:193:round-6 整改后第六次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变——六轮整改数字全程未变**。
./_bmad-output/审查/G4-9-evidence/census-stderr.txt:1:census: 92 条 (+0 unparseable) | class={'schema_entity_type': 2, 'group_id_format': 1, 'budget_400': 89} | recoverability={'byte_exact': 4, 'approximate': 88} | 归因冲突=3 | 重复簇=6 | 偏差=无 | qa_metrics 核销=no_source_rows
./_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:1:== CARD-G4-9 只读自证（round-6 整改版）==
./_bmad-output/审查/codex-review-CARD-G4-9-round7.md:14:CARD-G4-9 round-7 复审（静态审阅 + 只读复算，禁改任何文件）。你 round-6 裁定 6/9 CLOSED，两项 BLOCKER 揭示了根因：--out 保护集依赖枚举完整性（0333 不可列举目录内的 transcript、QA DB inode ABA 都能挫败它）。开发方接受该判断，做了**架构级修复**并以 commit 5b371253 + 后续 receipt commit 提交：
./_bmad-output/审查/codex-review-CARD-G4-9-round7.md:15:1. 新增**不依赖枚举的路径层防御**（main() 开头，早于任何读取）：--out 的 realpath 若等于 transcripts 根或落在其下 → 无条件 exit 2（恢复源区域整体禁写）；--out 的 realpath 若等于 --dlq/--compare/--qa-metrics-db 任一 realpath → exit 2。与既有 inode 层构成双保险。
./_bmad-output/审查/codex-review-CARD-G4-9-round7.md:17:3. no_token 分支改为**也遍历**（原 if uniq 完全不扫描，候选进不了 all_candidate_paths）。
./_bmad-output/审查/codex-review-CARD-G4-9-round7.md:18:4. 证据包 grep-selfattest.txt 重生成（内嵌当前脚本 sha256 + 生成时点声明）；receipt 补至当前 commit 链。
./_bmad-output/审查/codex-review-CARD-G4-9-round7.md:19:5. ledger 新增 attribution_conflict_reason 自描述；json.dumps 对 lone surrogate 回退 ensure_ascii=True 并标注。
./_bmad-output/审查/codex-review-CARD-G4-9-round7.md:20:请逐项复核是否闭合，并针对路径层防御设计新反例（如 --out 位于 transcripts 根外但通过 symlink/hardlink 指入根内的文件、transcripts 根本身是 symlink、相对路径与 .. 组合、TOCTOU 把 --out 在检查后换成指入根内的链接）。同时复核台账仍为 92 条 / class 89-2-1 / byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0 / 重复簇 6/29 / unparseable 0 / attribution_conflict 3(no_token)。逐项 CLOSED/NOT-CLOSED + 总裁定 + 新发现分级；若可验收请明确说明。
./_bmad-output/审查/codex-review-CARD-G4-9-round7.md:29:/bin/zsh -lc "rg -n -i 'CARD-G4-9|round-6|card-s5-census|census|annotation-truth' /Users/Heishing/.codex/memories/MEMORY.md" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:14:CARD-G4-9 round-3 复审（静态审阅 + 只读复算）。你 round-2 裁定 10/13 CLOSED，三项 NOT-CLOSED：BLOCKER-1（--out 守卫比 resolve 字符串，hardlink 与 case-only 别名绕过截断输入）、HIGH-1（full_body_verified 只核 sha 不核长度且排在 anomaly 分支前，anomaly 记录被判 byte_exact）、HIGH-3（chmod 000 根 exit 0 假判 unrecoverable；glob 跟随 symlink 逃逸出根）；另 3 新 LOW（full_verified 长度范围应 131-180、distribution 省略 0 值键、line_count 数 LF 与 records 的 splitlines 口径不一）。开发方以 commit 73102875 提交整改。请只读复核这 6 项是否闭合：
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:26:/bin/zsh -lc "rg -n -i 'CARD-G4-9|G4-9|DLQ|dead.?letter|census|round-2|73102875|card-s5-census' /Users/Heishing/.codex/memories/MEMORY.md" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:168:73102875 (HEAD -> card/s5-census) fix(census): G4-9/G4-16 Codex round-2 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9 / CARD-G4-16]
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:175: .../G4-9-evidence/grep-selfattest.txt"             |  46 ++++++----
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:177: .../codex-review-CARD-G4-9-round2.md"              |  37 ++++++++
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:196:?? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round3.md"
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:612: """CARD-G4-9: dead-letter episodes 只读 census 分诊脚本。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:614: BATCH-2026-08-28-第五批 / CARD-G4-9（G4-10 replay 的交接台账生成器）。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:621:-    --dlq/--compare/--qa-metrics-db 任一输入重合即拒绝 exit 2，防 "w" 截断
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:624:+    **文件身份 (st_dev, st_ino) 比较**，与 --dlq/--compare/--qa-metrics-db
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:636:     unrecoverable 并显式给 anomaly basis（不谎称"截断前缀"）。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:646:-    （拒绝在源不可见时产出 unrecoverable 假象）。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:648:+    （chmod 000）时整体 exit 2（拒绝在源不可见时产出 unrecoverable 假象）；
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:653:-    重算 sha 对账通过则按 byte_exact 采信（Codex round-1 MEDIUM-1 整改）。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:654:+    重算 sha **且长度**双门对账通过才按 byte_exact 采信，且 anomaly 记录
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:723:+    但 episode_body_length=999）仍被判 byte_exact —— 与 inline 侧同门收紧。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:845:         "--qa-metrics-db",
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:876:+    # 并把全部记录假判 unrecoverable —— 同样 fail-closed 拒诊。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:956:     unrecoverable_keys = []
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:965:             recover = "byte_exact"
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:970:             recover = "byte_exact"
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:974:             recover = "unrecoverable"
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:977:             recover = "unrecoverable"
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:987:             recover = "unrecoverable"
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:997:         if recover == "unrecoverable":
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:998:             unrecoverable_keys.append(stable_key)
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1051:         "card": "CARD-G4-9",
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1072:+            k: recover_dist.get(k, 0) for k in ["byte_exact", "approximate", "unrecoverable"]
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1077:         "unrecoverable_list": unrecoverable_keys,
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1114: # CARD-G4-9 — DLQ 真实挂载 census 分诊报告
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1116: > **批次**: BATCH-2026-08-28-第五批 / CARD-G4-9（4h · wave 1 · 未来铺路）
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1184: | **可字节级**（byte_exact） | **4** | inline 正文全量：sha256 重算对账通过**且**长度精确匹配（fail-closed 双门）——重放可逐字节还原 episode |
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1186: | **不可恢复**（unrecoverable） | **0** | — |
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1198: 逐条另带 `class / inline_state / recoverability / transcript_paths / transcript_match_count / attribution_conflict / error_excerpt / failed_at / reference_time`，G4-10 可直接按 `recoverability` 分桶排重放优先级（建议：4 条 byte_exact 先行——但其中 3 条 group_id 为已弃用 `vault:default`，重放前需按 D16 规约重映射并过 `to_physical_group_id()`；89 条 budget_400 重放前必须先修 context 超限根因，否则原样重放必然复现 400）。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1205: | grep 自证（import 行全 stdlib；neo4j/graphiti/bolt/app. import 0 命中；`--apply` 定义 0 命中；写模式 open 仅 `--out` 1 处且受路径碰撞守卫保护） | **PASS**（`grep-selfattest.txt`，含守卫在位证明） |
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1208:-| 负例门（整改自证） | `--out`==`--dlq` → exit 2 拒写、DLQ 完好；transcripts 根缺失 → exit 2 拒诊；sha 匹配但长度不符（Codex HIGH-1 反例①）→ anomaly/unrecoverable；坏 JSON 行/空行 → unparseable 逐行入台账不拒诊 |
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1209:+| 负例门（round-1 整改自证） | `--out`==`--dlq` → exit 2 拒写、DLQ 完好；transcripts 根缺失 → exit 2 拒诊；sha 匹配但长度不符（round-1 HIGH-1 反例①）→ anomaly/unrecoverable；坏 JSON 行/空行 → unparseable 逐行入台账不拒诊 |
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1210:+| 负例门（round-2 整改自证） | **hardlink** 指向 DLQ 的 --out → exit 2 + DLQ sha 不变；**case-only 别名**（`DLQ.jsonl`）→ exit 2 + DLQ 完好；**anomaly + episode_body_full 组合**（sha 对但长度 999）→ anomaly/unrecoverable（不再翻案 byte_exact）；**chmod 000 根** → exit 2 拒诊；**symlink 逃逸**（根内 .jsonl → 根外 .txt）→ match_count=0/unrecoverable；正例回归：真实唯一命中仍 approximate |
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1214: - **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1216: - **BLOCKER-3（交付物未冻结漂移）**：以本卡 commit 冻结全部交付物 exact bytes（脚本/报告/台账/证据包同 commit）；grep-selfattest 已按最终版行号重生成并内嵌脚本 sha 前缀。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1217: - **HIGH-1（inline 判定不 fail-closed）**：full_verified 加长度精确匹配门；truncated_prefix 加 64-hex 合法性门；anomaly 一律 unrecoverable + 如实 basis（不再谎称截断、不再滑入 approximate）。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1219: - **HIGH-3（transcript 归因折叠）**：恰 1 个常规文件命中才算归因（多命中 = ambiguous 拒采信）；glob 改递归下探；transcripts 根缺失整体 exit 2（拒绝产出 unrecoverable 假象）。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1220: - **MEDIUM-1**：`episode_body_full` 在盘且 sha 对账通过 → byte_exact 采信（现网 0 条，通路已备）。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1232:+- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1233:+- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1244:   --qa-metrics-db "…/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db" \
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1258:  "card": "CARD-G4-9",
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1314:   "byte_exact": 4,
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1317:+  "unrecoverable": 0
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1324:  "unrecoverable_list": [],
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1394:    fix(census): G4-9/G4-16 Codex round-2 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9 / CARD-G4-16]
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1431:     2	"""CARD-G4-9: dead-letter episodes 只读 census 分诊脚本。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1433:     4	BATCH-2026-08-28-第五批 / CARD-G4-9（G4-10 replay 的交接台账生成器）。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1440:    11	    **文件身份 (st_dev, st_ino) 比较**，与 --dlq/--compare/--qa-metrics-db
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1452:    23	    unrecoverable 并显式给 anomaly basis（不谎称"截断前缀"）。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1462:    33	    （chmod 000）时整体 exit 2（拒绝在源不可见时产出 unrecoverable 假象）；
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1467:    38	    重算 sha **且长度**双门对账通过才按 byte_exact 采信，且 anomaly 记录
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1535:   106	    但 episode_body_length=999）仍被判 byte_exact —— 与 inline 侧同门收紧。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1659:   226	        "--qa-metrics-db",
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1690:   257	    # 并把全部记录假判 unrecoverable —— 同样 fail-closed 拒诊。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1765:   332	    unrecoverable_keys = []
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1774:   341	            recover = "byte_exact"
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1778:   345	            recover = "byte_exact"
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1781:   348	            recover = "unrecoverable"
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1784:   351	            recover = "unrecoverable"
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1798:   361	            recover = "unrecoverable"
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1808:   371	        if recover == "unrecoverable":
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1809:   372	            unrecoverable_keys.append(stable_key)
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1862:   425	        "card": "CARD-G4-9",
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1881:   444	            k: recover_dist.get(k, 0) for k in ["byte_exact", "approximate", "unrecoverable"]
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1886:   449	        "unrecoverable_list": unrecoverable_keys,
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1934:94:| 负例门（round-1 整改自证） | `--out`==`--dlq` → exit 2 拒写、DLQ 完好；transcripts 根缺失 → exit 2 拒诊；sha 匹配但长度不符（round-1 HIGH-1 反例①）→ anomaly/unrecoverable；坏 JSON 行/空行 → unparseable 逐行入台账不拒诊 |
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1935:95:| 负例门（round-2 整改自证） | **hardlink** 指向 DLQ 的 --out → exit 2 + DLQ sha 不变；**case-only 别名**（`DLQ.jsonl`）→ exit 2 + DLQ 完好；**anomaly + episode_body_full 组合**（sha 对但长度 999）→ anomaly/unrecoverable（不再翻案 byte_exact）；**chmod 000 根** → exit 2 拒诊；**symlink 逃逸**（根内 .jsonl → 根外 .txt）→ match_count=0/unrecoverable；正例回归：真实唯一命中仍 approximate |
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1937:99:- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1939:102:- **HIGH-1（inline 判定不 fail-closed）**：full_verified 加长度精确匹配门；truncated_prefix 加 64-hex 合法性门；anomaly 一律 unrecoverable + 如实 basis（不再谎称截断、不再滑入 approximate）。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1946:117:- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1947:118:- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1955:     2	 "card": "CARD-G4-9",
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2009:    56	  "byte_exact": 4,
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2011:    58	  "unrecoverable": 0
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2018:    65	 "unrecoverable_list": [],
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2113:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:25:266:    # (st_dev, st_ino) 而非 resolve() 字符串 —— 后者对 hardlink 与
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2114:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:30:--- (6) fail-closed 门（不可读根 / symlink 逃逸 / anomaly 前置）:
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2115:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:33:343:        elif state != "anomaly" and full_body_verified(rec):
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2125:"_bmad-output/\345\256\241\346\237\245/G4-9-evidence/grep-selfattest.txt"
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2128:"_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round2.md"
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2129:"_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9.md"
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2130:"_bmad-output/\351\252\214\346\224\266\345\215\225/UAT-CARD-G4-9-DLQ\347\234\237\345\256\236\346\214\202\350\275\275census\345\210\206\350\257\212-2026-08-28.md"
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2135:/bin/zsh -lc "nl -ba '_bmad-output/审查/codex-review-CARD-G4-9-round2.md' | sed -n '1,260p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2146:    10	| HIGH-1 | **NOT-CLOSED** | round-1 三个反例本身均已翻转为 `anomaly/FAIL → unrecoverable`；非法 64 字符非 hex 也被拒。但新增组合反例：`episode_body="abc"`、`episode_body_full="abc"`、SHA 正确、声明长度 `999`，实际得到 `inline_state=anomaly` 后仍被判 `byte_exact`。原因是 [`full_body_verified()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:99)只核 SHA，不核长度，并在 [anomaly 分支之前](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:285)被采信。这直接反驳报告“anomaly 一律 unrecoverable”。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2147:    11	| HIGH-2 | **CLOSED** | missing、显式 `null`、字面 `"None"` 不再合组；数字 `123` 与字符串 `"123"` 分离；非前缀多 token 均 `attribution_conflict=true/unrecoverable`；合法前缀组统一取最长 token。真实入口反例全部通过。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2148:    12	| HIGH-3 | **NOT-CLOSED** | 不存在根目录已 exit 2；递归唯一命中、多命中冲突、目录伪命中也通过。但“不可见”仍未闭合：存在但 `chmod 000` 的根会 exit 0 并假判 `unrecoverable`。此外 [`glob + os.path.isfile`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:134)跟随 symlink：根内 `.jsonl` symlink 指向根外 `.txt`、以及 symlink 目录逃逸到根外树，均被判唯一来源并进入 `approximate`。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2162:    26	- recoverability：`4 byte_exact / 88 approximate / 0 unrecoverable`。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2170:    34	- **LOW**：ledger distribution 省略 `unexpected:0`、`anomaly:0`、`unrecoverable:0`，固定 schema 消费者需自行补零。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2342:        result = "byte_exact"
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2344:        result = "unrecoverable"
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2346:        result = "unrecoverable"
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2350:        result = "unrecoverable"
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2422:    "byte_exact": 4
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2575:   277	    unrecoverable_keys = []
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2584:   286	            recover = "byte_exact"
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2587:   289	            recover = "byte_exact"
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2590:   292	            recover = "unrecoverable"
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2593:   295	            recover = "unrecoverable"
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2603:   305	            recover = "unrecoverable"
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2612:   314	        if recover == "unrecoverable":
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2613:   315	            unrecoverable_keys.append(stable_key)
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2638:backend/scripts/census_dead_letter_episodes.py:106:    但 episode_body_length=999）仍被判 byte_exact —— 与 inline 侧同门收紧。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2762:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:117:- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2765:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:7:| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2766:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:8:| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2767:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:10:| HIGH-1 | **NOT-CLOSED** | round-1 三个反例本身均已翻转为 `anomaly/FAIL → unrecoverable`；非法 64 字符非 hex 也被拒。但新增组合反例：`episode_body="abc"`、`episode_body_full="abc"`、SHA 正确、声明长度 `999`，实际得到 `inline_state=anomaly` 后仍被判 `byte_exact`。原因是 [`full_body_verified()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:99)只核 SHA，不核长度，并在 [anomaly 分支之前](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:285)被采信。这直接反驳报告“anomaly 一律 unrecoverable”。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2768:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:12:| HIGH-3 | **NOT-CLOSED** | 不存在根目录已 exit 2；递归唯一命中、多命中冲突、目录伪命中也通过。但“不可见”仍未闭合：存在但 `chmod 000` 的根会 exit 0 并假判 `unrecoverable`。此外 [`glob + os.path.isfile`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:134)跟随 symlink：根内 `.jsonl` symlink 指向根外 `.txt`、以及 symlink 目录逃逸到根外树，均被判唯一来源并进入 `approximate`。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2769:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:14:| MEDIUM-2 | **CLOSED** | [报告 §6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:78)、[ledger duplicate_clusters](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:60)及逐条 `reference_time` 已落地；6 簇全部逐行对账。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2772:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:14:CARD-G4-9 round-3 复审（静态审阅 + 只读复算）。你 round-2 裁定 10/13 CLOSED，三项 NOT-CLOSED：BLOCKER-1（--out 守卫比 resolve 字符串，hardlink 与 case-only 别名绕过截断输入）、HIGH-1（full_body_verified 只核 sha 不核长度且排在 anomaly 分支前，anomaly 记录被判 byte_exact）、HIGH-3（chmod 000 根 exit 0 假判 unrecoverable；glob 跟随 symlink 逃逸出根）；另 3 新 LOW（full_verified 长度范围应 131-180、distribution 省略 0 值键、line_count 数 LF 与 records 的 splitlines 口径不一）。开发方以 commit 73102875 提交整改。请只读复核这 6 项是否闭合：
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2773:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:15:脚本 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py 现改为：(a) 碰撞守卫比较文件身份 (st_dev, st_ino) 并保留 resolve 路径比较；(b) full_body_verified 增加 len(full)==declared_len 门，且判定链改为 state != 'anomaly' 前置；(c) transcripts 根增 os.access(R_OK|X_OK) 检查 exit 2，glob 结果排除 os.path.islink 条目并要求 realpath 落在根内；(d) line_count 改用 splitlines()，class/recoverability distribution 补零并新增 inline_state_distribution。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2774:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:181: backend/scripts/census_dead_letter_episodes.py     | 101 +++++++++++++++++----
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2775:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:598:/bin/zsh -lc 'wc -l backend/scripts/census_dead_letter_episodes.py' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2776:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:600:     475 backend/scripts/census_dead_letter_episodes.py
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2777:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:603:/bin/zsh -lc 'git diff --no-ext-diff --unified=80 73102875''^ 73102875 -- backend/scripts/census_dead_letter_episodes.py' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2778:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:606:diff --git a/backend/scripts/census_dead_letter_episodes.py b/backend/scripts/census_dead_letter_episodes.py
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2779:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:608:--- a/backend/scripts/census_dead_letter_episodes.py
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2780:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:609:+++ b/backend/scripts/census_dead_letter_episodes.py
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2781:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:662:   - reference_time 逐条透传 + duplicate_clusters 段（同 name+sha+group 的
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2782:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:718: def full_body_verified(rec: dict) -> bool:
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2783:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:967:-        elif full_body_verified(rec):
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2784:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:968:+        elif state != "anomaly" and full_body_verified(rec):
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2785:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1029:     duplicate_clusters = [
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2786:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1074:+        "inline_state_distribution": {
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2787:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1079:         "duplicate_clusters": duplicate_clusters,
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2788:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1095:         f"重复簇={len(duplicate_clusters)} | 偏差={deviation or '无'} | "
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2789:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1117: > **性质**: 纯只读 census。0 写入、0 重放、0 业务代码改动。唯一代码产物 = `backend/scripts/census_dead_letter_episodes.py`。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2790:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1194: 台账逐条携带复合键 `{line_no, sha256_prefix(16 hex), request_id}`。**语义（Codex round-1 LOW-2 修正）**：这是**冻结快照内的 occurrence key**，不是跨文件重排或语义幂等键——台账头部 `dlq_file.sha256`（`3b37460f4215f6ac…`）即快照指纹，`line_no` 在该快照内已单列唯一；`sha256_prefix`（本快照 69 个唯一值，qa_highlight 家族实测同名同 sha 多条）与 `request_id`（仅 25 个唯一值，进程内 contextvars、重启可复用）是**冗余对账/诊断维度**，不是唯一性的必要条件。G4-10 消费前先 diff 头部 sha 即知 DLQ 是否长了新条目；语义级去重不得按本键，须按 `duplicate_clusters` 段（见下）。**语义重复簇（MEDIUM-2 整改）**：按 `{name, episode_body_sha256, group_id}` 聚簇，**6 簇覆盖 29 行**（最大簇 = 同一 session-archive 16 行，`reference_time` 各不相同——同内容反复入队反复超限）。台账 `duplicate_clusters` 段逐簇列 line_nos，records 逐条透传 `reference_time`；G4-10 重放前必须先定去重策略（89 条 budget 修根因后若逐条盲放，将把同内容写入最多 16 遍）。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2791:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1221: - **MEDIUM-2**：`duplicate_clusters` 段 + 逐条 `reference_time`（见 §6）。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2792:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1232:+- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2793:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1234:+- **新 LOW ×3**：full_verified 长度范围修正为 131–180；台账 `class_distribution`/`recoverability_distribution` 补零并新增 `inline_state_distribution`（固定 schema，消费者无需补齐缺席键）；`line_count` 改用 `splitlines()` 与 records 同口径（原 `count("\n")` 在 bare CR / U+2028 下会与 records 数不一致）。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2794:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1242: python3 backend/scripts/census_dead_letter_episodes.py \
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2795:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1319:+ "inline_state_distribution": {
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2796:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1326:  "duplicate_clusters": [
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2797:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1428:/bin/zsh -lc "nl -ba backend/scripts/census_dead_letter_episodes.py | sed -n '1,180p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2798:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1475:    46	  - reference_time 逐条透传 + duplicate_clusters 段（同 name+sha+group 的
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2799:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1531:   102	def full_body_verified(rec: dict) -> bool:
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2800:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1612:/bin/zsh -lc "nl -ba backend/scripts/census_dead_letter_episodes.py | sed -n '181,360p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2801:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1776:   343	        elif state != "anomaly" and full_body_verified(rec):
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2802:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1796:/bin/zsh -lc "nl -ba backend/scripts/census_dead_letter_episodes.py | sed -n '361,520p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2803:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1840:   403	    duplicate_clusters = [
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2804:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1883:   446	        "inline_state_distribution": {
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2805:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1888:   451	        "duplicate_clusters": duplicate_clusters,
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2806:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1904:   467	        f"重复簇={len(duplicate_clusters)} | 偏差={deviation or '无'} | "
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2807:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1932:80:台账逐条携带复合键 `{line_no, sha256_prefix(16 hex), request_id}`。**语义（Codex round-1 LOW-2 修正）**：这是**冻结快照内的 occurrence key**，不是跨文件重排或语义幂等键——台账头部 `dlq_file.sha256`（`3b37460f4215f6ac…`）即快照指纹，`line_no` 在该快照内已单列唯一；`sha256_prefix`（本快照 69 个唯一值，qa_highlight 家族实测同名同 sha 多条）与 `request_id`（仅 25 个唯一值，进程内 contextvars、重启可复用）是**冗余对账/诊断维度**，不是唯一性的必要条件。G4-10 消费前先 diff 头部 sha 即知 DLQ 是否长了新条目；语义级去重不得按本键，须按 `duplicate_clusters` 段（见下）。**语义重复簇（MEDIUM-2 整改）**：按 `{name, episode_body_sha256, group_id}` 聚簇，**6 簇覆盖 29 行**（最大簇 = 同一 session-archive 16 行，`reference_time` 各不相同——同内容反复入队反复超限）。台账 `duplicate_clusters` 段逐簇列 line_nos，records 逐条透传 `reference_time`；G4-10 重放前必须先定去重策略（89 条 budget 修根因后若逐条盲放，将把同内容写入最多 16 遍）。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2808:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1941:106:- **MEDIUM-2**：`duplicate_clusters` 段 + 逐条 `reference_time`（见 §6）。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2809:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1946:117:- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2810:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1948:119:- **新 LOW ×3**：full_verified 长度范围修正为 131–180；台账 `class_distribution`/`recoverability_distribution` 补零并新增 `inline_state_distribution`（固定 schema，消费者无需补齐缺席键）；`line_count` 改用 `splitlines()` 与 records 同口径（原 `count("\n")` 在 bare CR / U+2028 下会与 records 数不一致）。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2811:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2013:    60	 "inline_state_distribution": {
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2812:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2020:    67	 "duplicate_clusters": [
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2813:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2115:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:33:343:        elif state != "anomaly" and full_body_verified(rec):
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2814:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2131:backend/scripts/census_dead_letter_episodes.py
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2815:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2816:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2144:     8	| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2817:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2146:    10	| HIGH-1 | **NOT-CLOSED** | round-1 三个反例本身均已翻转为 `anomaly/FAIL → unrecoverable`；非法 64 字符非 hex 也被拒。但新增组合反例：`episode_body="abc"`、`episode_body_full="abc"`、SHA 正确、声明长度 `999`，实际得到 `inline_state=anomaly` 后仍被判 `byte_exact`。原因是 [`full_body_verified()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:99)只核 SHA，不核长度，并在 [anomaly 分支之前](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:285)被采信。这直接反驳报告“anomaly 一律 unrecoverable”。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2818:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2148:    12	| HIGH-3 | **NOT-CLOSED** | 不存在根目录已 exit 2；递归唯一命中、多命中冲突、目录伪命中也通过。但“不可见”仍未闭合：存在但 `chmod 000` 的根会 exit 0 并假判 `unrecoverable`。此外 [`glob + os.path.isfile`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:134)跟随 symlink：根内 `.jsonl` symlink 指向根外 `.txt`、以及 symlink 目录逃逸到根外树，均被判唯一来源并进入 `approximate`。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2819:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2150:    14	| MEDIUM-2 | **CLOSED** | [报告 §6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:78)、[ledger duplicate_clusters](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:60)及逐条 `reference_time` 已落地；6 簇全部逐行对账。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2820:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2366:    \"inline_state_distribution\": dict(sorted(inline_states.items())),
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2821:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2412:  "inline_state_distribution": {
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2822:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2439:/bin/zsh -lc 'git show 73102875''^:backend/scripts/census_dead_letter_episodes.py | nl -ba | sed -n '"'80,155p;220,315p;400,430p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2823:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2461:    99	def full_body_verified(rec: dict) -> bool:
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2824:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2586:   288	        elif full_body_verified(rec):
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2825:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2616:   402	        f"重复簇={len(duplicate_clusters)} | 偏差={deviation or '无'} | "
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2826:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2629:/bin/zsh -lc 'git diff --check 73102875''^ 73102875 -- backend/scripts/census_dead_letter_episodes.py '"'_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md' '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2827:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2634:backend/scripts/census_dead_letter_episodes.py:37:  - episode_body_full 若在盘（DEAD_LETTER_STORE_FULL_BODY 开启时生产可写):
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2828:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2635:backend/scripts/census_dead_letter_episodes.py:91:    declared_len = rec.get("episode_body_length")
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2829:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2636:backend/scripts/census_dead_letter_episodes.py:92:    declared_sha = rec.get("episode_body_sha256", "")
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2830:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2637:backend/scripts/census_dead_letter_episodes.py:103:    """episode_body_full 在盘且 sha **与长度**双门对账通过（生产 opt-in 字段，当前 live 0 条）。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2831:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2638:backend/scripts/census_dead_letter_episodes.py:106:    但 episode_body_length=999）仍被判 byte_exact —— 与 inline 侧同门收紧。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2832:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2639:backend/scripts/census_dead_letter_episodes.py:108:    full = rec.get("episode_body_full")
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2833:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2640:backend/scripts/census_dead_letter_episodes.py:109:    declared_sha = rec.get("episode_body_sha256", "")
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2834:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2641:backend/scripts/census_dead_letter_episodes.py:110:    declared_len = rec.get("episode_body_length")
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2835:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2642:backend/scripts/census_dead_letter_episodes.py:346:            basis = "episode_body_full 在盘且 sha256+长度双门对账通过（DEAD_LETTER_STORE_FULL_BODY 生产 opt-in 字段）"
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2836:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2643:backend/scripts/census_dead_letter_episodes.py:368:            "sha256_prefix": str(rec.get("episode_body_sha256", ""))[:16],
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2837:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2644:backend/scripts/census_dead_letter_episodes.py:386:                "episode_body_length": rec.get("episode_body_length"),
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2838:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2645:backend/scripts/census_dead_letter_episodes.py:387:                "episode_body_sha256": rec.get("episode_body_sha256"),
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2839:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2646:backend/scripts/census_dead_letter_episodes.py:402:        cluster_map[(rec.get("name", ""), rec.get("episode_body_sha256", ""), rec.get("group_id"))].append(line_no)
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2840:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2647:backend/scripts/census_dead_letter_episodes.py:404:        {"name": k[0][:80], "episode_body_sha256": k[1], "group_id": k[2], "line_nos": v, "occurrences": len(v)}
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2841:_bmad-output/审查/codex-review-CARD-G4-9.md:15:   [脚本:163](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:163) 接受任意输出路径，[脚本:281](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:281) 以 `"w"` 无条件截断，未做审查目录 allowlist、`samefile`、symlink 或数据目录隔离。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2842:_bmad-output/审查/codex-review-CARD-G4-9.md:23:   records 在[脚本:171](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:171)首次读取；头部 `dlq_file` 到[脚本:268](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:268)才重新读取，而 `describe_copy()` 又分别计算行数、SHA、mtime（[脚本:130](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:130)）。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2843:_bmad-output/审查/codex-review-CARD-G4-9.md:37:   [脚本:72](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:72)存在三个可复现反例：
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2844:_bmad-output/审查/codex-review-CARD-G4-9.md:41:   - 真正 `anomaly` 在[脚本:208](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:208)仍会被改判为 `approximate` 或 `unrecoverable`，basis 还会谎称“inline 截断”。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2845:_bmad-output/审查/codex-review-CARD-G4-9.md:47:   [脚本:181](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:181)用 `str(request_id)` 对整份历史文件分组：
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2846:_bmad-output/审查/codex-review-CARD-G4-9.md:59:   [脚本:94](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:94)跨所有 project 目录做前缀 glob；一个或多个候选都算存在，不要求唯一、可读普通文件或内容关联。目录不存在、未挂载或无权限时则直接返回空，并在[脚本:217](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:217)裁为永久性的 `unrecoverable`，而诚实状态应是“未核验/当前源不可见”。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2847:_bmad-output/审查/codex-review-CARD-G4-9.md:71:   独立复算 `{name, full_sha, group_id}`：6 个重复组覆盖 29 行，额外 occurrence 23 个；最大组为同一 session archive 16 行，但 `reference_time` 各不相同。ledger 未标识重复簇，也不携带 `reference_time`（[脚本:229](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:229)）。G4-10 不能仅按 SHA 去重，也不应无策略逐条重放。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2848:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:33:343:        elif state != "anomaly" and full_body_verified(rec):
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2849:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:49:- **MEDIUM-1~3**：episode_body_full 采信通路 / duplicate_clusters 6 簇 29 行 + reference_time 透传 / privacy 字段与 private-only 声明。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2850:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:61:- **3 新 LOW**：full_verified 长度范围修正 131–180；台账三个 distribution 补零并新增 `inline_state_distribution`；`line_count` 与 records 改用同一 `splitlines()` 口径。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2851:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:67:- `backend/scripts/census_dead_letter_episodes.py` — 唯一代码产物（只读 census 脚本，纯 stdlib）
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2869:        recover = \"byte_exact\"
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2871:        recover = "byte_exact"
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2873:        recover = "unrecoverable"
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2913:    "recoverability_branch": "unrecoverable"
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2918:    "recoverability_branch": "byte_exact"
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2923:    "recoverability_branch": "unrecoverable"
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2928:    "recoverability_branch": "byte_exact"
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:3020:    "recoverability_zero_keys": {k: ledger["recoverability_distribution"].get(k, "MISSING") for k in ["byte_exact", "approximate", "unrecoverable"]},
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:3046:    "byte_exact": 4,
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:3047:    "unrecoverable": 0
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:3056:     1	# CARD-G4-9 — DLQ 真实挂载 census 分诊报告
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:3058:     3	> **批次**: BATCH-2026-08-28-第五批 / CARD-G4-9（4h · wave 1 · 未来铺路）
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:3108:73102875 (HEAD -> card/s5-census) fix(census): G4-9/G4-16 Codex round-2 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9 / CARD-G4-16]
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:3110:67ccebe1 docs(census): G4-9 DLQ真实挂载census分诊 92条台账+挂载真相+三态裁定 [BATCH-2026-08-28-第五批 / CARD-G4-9]
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:3133:/bin/zsh -lc "nl -ba '_bmad-output/审查/codex-review-CARD-G4-9.md' | sed -n '1,30p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:3468:?? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round3.md"
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:3511:| HIGH-1 | **CLOSED / PASS** | [`full_body_verified()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:102)现有 SHA+严格长度门；[真实判定链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:340)在 full-body 分支前要求 `state != anomaly`。更强反例——full 本身 SHA/长度完全有效，但 inline 不符——仍落 `anomaly → unrecoverable`。无其它调用入口。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:3514:| LOW：distribution 零键 | **CLOSED** | [固定 schema 生成链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:437)与 [ledger](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:43)均包含 `unexpected/anomaly/unrecoverable: 0`，并新增 inline 三态。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:3523:- recoverability：`byte_exact 4 / approximate 88 / unrecoverable 0`。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:3534:所以：**冻结的 92 条 ledger 数值可采信；CARD-G4-9 生成器与整卡验收仍被 BLOCKER-1、HIGH-3 阻断。** 本轮未修改仓库或受审数据，未执行破坏性 fixture/G4-10 重放；Graphiti 工具本轮不可用。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:3544:| HIGH-1 | **CLOSED / PASS** | [`full_body_verified()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:102)现有 SHA+严格长度门；[真实判定链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:340)在 full-body 分支前要求 `state != anomaly`。更强反例——full 本身 SHA/长度完全有效，但 inline 不符——仍落 `anomaly → unrecoverable`。无其它调用入口。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:3547:| LOW：distribution 零键 | **CLOSED** | [固定 schema 生成链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:437)与 [ledger](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:43)均包含 `unexpected/anomaly/unrecoverable: 0`，并新增 inline 三态。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:3556:- recoverability：`byte_exact 4 / approximate 88 / unrecoverable 0`。
./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:3567:所以：**冻结的 92 条 ledger 数值可采信；CARD-G4-9 生成器与整卡验收仍被 BLOCKER-1、HIGH-3 阻断。** 本轮未修改仓库或受审数据，未执行破坏性 fixture/G4-10 重放；Graphiti 工具本轮不可用。
./_bmad-output/审查/codex-review-CARD-G4-9.md:31:   旧证据仍称写入口位于 L291（[grep-selfattest:21](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:21)），当前已在 L282，证明 evidence/ledger 不再绑定当前脚本。当前报告还在漂移中把错误的 `16/72` 修成了正确的 `22/66`；该旧错误不再算当前 finding，但漂移本身阻断验收。
./_bmad-output/审查/codex-review-CARD-G4-9.md:41:   - 真正 `anomaly` 在[脚本:208](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:208)仍会被改判为 `approximate` 或 `unrecoverable`，basis 还会谎称“inline 截断”。
./_bmad-output/审查/codex-review-CARD-G4-9.md:59:   [脚本:94](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:94)跨所有 project 目录做前缀 glob；一个或多个候选都算存在，不要求唯一、可读普通文件或内容关联。目录不存在、未挂载或无权限时则直接返回空，并在[脚本:217](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:217)裁为永久性的 `unrecoverable`，而诚实状态应是“未核验/当前源不可见”。
./_bmad-output/审查/codex-review-CARD-G4-9.md:61:   真实入口只读复现：对当前 92 行传不存在的 transcripts 根，脚本退出 0 并输出 `byte_exact=4 / unrecoverable=88`。这会误导 G4-10 放弃仍可能存在的来源。
./_bmad-output/审查/codex-review-CARD-G4-9.md:67:   `DeadLetterStore` 可保存 full body（[episode_worker.py:252](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/app/services/episode_worker.py:252)），但脚本完全不读取该字段。含可验证 full body、但无 transcript 的记录仍会被判 `unrecoverable`。当前 92 条该字段确为 0，因此不改变本次数字。
./_bmad-output/审查/codex-review-CARD-G4-9.md:103:- 当前三态：`4 byte_exact / 88 approximate / 0 unrecoverable`。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:14:CARD-G4-9 round-6 复审（静态审阅 + 只读复算，禁改任何文件）。你 round-5 裁定 3/8 CLOSED，提出 2 BLOCKER / 2 HIGH / 2 MEDIUM / 3 LOW，并明确该阻断与只读 census 卡范围相称（因报告/UAT 承诺纯只读零写入，残留反例能截断或修改本卡正在保护的恢复源）——开发方接受该论证并以 commit 4c125f19 提交整改。请逐条只读复核：
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:15:1. BLOCKER token 冲突/无 token 扫描前早退 → resolve_group_attribution 重写为先扫描后判定：无条件对每个 token 遍历收集候选进 all_candidate_paths（保护集口径），再做 no_token/token_conflict/scan_errors/stat_failures/unreadable/多命中判定；候选 stat 失败改 exit 2。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:17:3. HIGH anomaly 吞不可见性 → 判定链改可见性优先：attribution_conflict 分支置于 anomaly 之前，一律 unverifiable，basis 区分 no_token/token_conflict/scan_errors/stat_failures/unreadable/ambiguous 并附注 inline 是否 anomaly。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:20:6. MEDIUM 无 token 判不可恢复 → 改 unverifiable + no_token 标记。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:22:请对每项设计静态反例判断是否仍可绕过。同时复核台账数字：92 条 / class 89-2-1 / byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0 / 重复簇 6/29 / unparseable 0；并核对新出现的 attribution_conflict=3（3 条 callout_annotation 无 session token，判 no_token 但因 inline 全量仍 byte_exact）——该口径变化是否诚实且自洽。逐项 CLOSED/NOT-CLOSED + 总裁定 + 新发现分级；若可验收请明确说明。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:28:CARD-G4-9 round-6 只读复审：以提交对象、生产入口和独立复算为证据，禁止文件修改。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:41:/bin/zsh -lc "rg -n -i 'CARD-G4-9|round-5|census|attribution_conflict|qa_metrics|resolve_group_attribution|4c125f19' /Users/Heishing/.codex/memories/MEMORY.md" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:232:    fix(census): G4-9 Codex round-5 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9]
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:240:    2 MEDIUM: QA DB 特殊文件门; 无 token 归 unverifiable 而非 unrecoverable。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:244:    归因冲突 0→3 系 no_token 标注变诚实(3 条 callout 仍 byte_exact), 三态不变。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:261:A	"_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round5.md"
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:262:M	"_bmad-output/\351\252\214\346\224\266\345\215\225/UAT-CARD-G4-9-DLQ\347\234\237\345\256\236\346\214\202\350\275\275census\345\210\206\350\257\212-2026-08-28.md"
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:270:?? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round6.md"
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:276:4c125f19 (HEAD -> card/s5-census) fix(census): G4-9 Codex round-5 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9]
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:280: .../codex-review-CARD-G4-9-round5.md"              | 3419 ++++++++++++++++++++
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:286:/bin/zsh -lc "rg --files -g 'AGENTS.md' -g 'CURRENT_TASK.md' -g '*CARD-G4-9*' -g '*card*g4*' -g '*census*' -g '*qa_metrics*'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:293:_bmad-output/审查/codex-review-CARD-G4-9-round4.md
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:294:_bmad-output/审查/codex-review-CARD-G4-9-round5.md
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:296:_bmad-output/审查/codex-review-CARD-G4-9.md
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:298:_bmad-output/审查/codex-review-CARD-G4-9-round3.md
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:299:_bmad-output/审查/codex-review-CARD-G4-9-round6.md
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:300:_bmad-output/审查/codex-review-CARD-G4-9-round2.md
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:301:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:309:/bin/zsh -lc 'wc -l backend/scripts/census_dead_letter_episodes.py _bmad-output/审查/codex-review-CARD-G4-9-round5.md _bmad-output/审查/G4-9-DLQ-census-2026-08-28.md _bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:312:    3419 _bmad-output/审查/codex-review-CARD-G4-9-round5.md
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:318:/bin/zsh -lc "rg -n '"'^def |''^class |resolve_group_attribution|probe_qa_metrics|fchmod|protected_ids|attribution_conflict|full_verified|empty|bool|anomaly|unverifiable|unrecoverable'"' backend/scripts/census_dead_letter_episodes.py" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:322:23:    unrecoverable 并显式给 anomaly basis（不谎称"截断前缀"）。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:324:33:    （chmod 000）时整体 exit 2（拒绝在源不可见时产出 unrecoverable 假象）；
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:325:38:    重算 sha **且长度**双门对账通过才按 byte_exact 采信，且 anomaly 记录
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:353:406:    # 并把全部记录假判 unrecoverable —— 同样 fail-closed 拒诊。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:359:504:    unrecoverable_keys = []
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:369:543:            recover = "unrecoverable"
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:371:553:            recover = "unrecoverable"
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:372:563:        if recover == "unrecoverable":
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:373:564:            unrecoverable_keys.append(stable_key)
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:382:648:            k: recover_dist.get(k, 0) for k in ["byte_exact", "approximate", "unverifiable", "unrecoverable"]
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:384:653:        "unrecoverable_list": unrecoverable_keys,
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:395:/bin/zsh -lc "rg -n '"'^#{1,4} |BLOCKER|HIGH|MEDIUM|LOW|3/8|总裁定|CLOSED|NOT-CLOSED'"' _bmad-output/审查/codex-review-CARD-G4-9-round5.md" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:397:14:CARD-G4-9 round-5 终裁复审（静态审阅 + 只读复算，禁改任何文件）。你 round-4 裁定 1/6 CLOSED，提出 2 BLOCKER / 1 HIGH / 2 MEDIUM / 3 LOW。开发方以 commit d2827a6d + d8d887f2 提交整改，请逐条只读复核：
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:405:22:请对每项设计静态反例判断是否仍可绕过（尤其：保护集完整性、fd 身份与实际读取的绑定、unverifiable 与 unrecoverable 的语义边界、strict decode 的边界）。同时独立复算台账仍为 92 条 / class 89-2-1 / byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0 / 重复簇 6 簇 29 行 / unparseable 0。逐项 CLOSED/NOT-CLOSED + 总裁定（可验收/仍阻断）+ 新发现分级。若已可验收请明确说明；若仍阻断请说明**对一张只读 census 卡**而言该阻断是否与卡面范围相称。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:462:870:/bin/zsh -lc "rg -n 'BLOCKER|HIGH|MEDIUM|LOW|CLOSED|NOT-CLOSED|保护集|TOCTOU|UTF-8|unverifiable|unrecoverable|provenance|92|89|29' '_bmad-output/审查/codex-review-CARD-G4-9-round4.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:463:873:14:CARD-G4-9 round-4 终裁复审（静态审阅 + 只读复算，禁改任何文件）。你 round-3 裁定 4/6 CLOSED，两项 PARTIAL + 3 新发现。开发方以 commit fce0d8a2 提交整改，请只读复核这 6 项：
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:471:884:145:rg -n \"BLOCKER-1|HIGH-3|JSONL|framing|非 dict|provenance|PARTIAL|CLOSED|NOT-CLOSED|新发现|总裁定|protected_ids|O_NOFOLLOW|os\\.walk|line_count\" '_bmad-output/审查/codex-review-CARD-G4-9-round3.md' | head -n 240
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:472:885:160:14:CARD-G4-9 round-3 复审（静态审阅 + 只读复算）。你 round-2 裁定 10/13 CLOSED，三项 NOT-CLOSED：BLOCKER-1（--out 守卫比 resolve 字符串，hardlink 与 case-only 别名绕过截断输入）、HIGH-1（full_body_verified 只核 sha 不核长度且排在 anomaly 分支前，anomaly 记录被判 byte_exact）、HIGH-3（chmod 000 根 exit 0 假判 unrecoverable；glob 跟随 symlink 逃逸出根）；另 3 新 LOW（full_verified 长度范围应 131-180、distribution 省略 0 值键、line_count 数 LF 与 records 的 splitlines 口径不一）。开发方以 commit 73102875 提交整改。请只读复核这 6 项是否闭合：
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:482:899:186:1214: - **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:484:901:188:1219: - **HIGH-3（transcript 归因折叠）**：恰 1 个常规文件命中才算归因（多命中 = ambiguous 拒采信）；glob 改递归下探；transcripts 根缺失整体 exit 2（拒绝产出 unrecoverable 假象）。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:488:905:192:1232:+- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:489:906:193:1233:+- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:497:919:213:1937:99:- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:501:923:217:1946:117:- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:502:924:218:1947:118:- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:505:928:226:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:508:931:229:2146:    10	| HIGH-1 | **NOT-CLOSED** | round-1 三个反例本身均已翻转为 `anomaly/FAIL → unrecoverable`；非法 64 字符非 hex 也被拒。但新增组合反例：`episode_body="abc"`、`episode_body_full="abc"`、SHA 正确、声明长度 `999`，实际得到 `inline_state=anomaly` 后仍被判 `byte_exact`。原因是 [`full_body_verified()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:99)只核 SHA，不核长度，并在 [anomaly 分支之前](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:285)被采信。这直接反驳报告“anomaly 一律 unrecoverable”。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:509:932:230:2147:    11	| HIGH-2 | **CLOSED** | missing、显式 `null`、字面 `"None"` 不再合组；数字 `123` 与字符串 `"123"` 分离；非前缀多 token 均 `attribution_conflict=true/unrecoverable`；合法前缀组统一取最长 token。真实入口反例全部通过。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:510:933:231:2148:    12	| HIGH-3 | **NOT-CLOSED** | 不存在根目录已 exit 2；递归唯一命中、多命中冲突、目录伪命中也通过。但“不可见”仍未闭合：存在但 `chmod 000` 的根会 exit 0 并假判 `unrecoverable`。此外 [`glob + os.path.isfile`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:134)跟随 symlink：根内 `.jsonl` symlink 指向根外 `.txt`、以及 symlink 目录逃逸到根外树，均被判唯一来源并进入 `approximate`。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:519:942:243:2762:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:117:- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:521:944:245:2765:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:7:| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:522:945:246:2766:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:8:| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:523:946:247:2767:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:10:| HIGH-1 | **NOT-CLOSED** | round-1 三个反例本身均已翻转为 `anomaly/FAIL → unrecoverable`；非法 64 字符非 hex 也被拒。但新增组合反例：`episode_body="abc"`、`episode_body_full="abc"`、SHA 正确、声明长度 `999`，实际得到 `inline_state=anomaly` 后仍被判 `byte_exact`。原因是 [`full_body_verified()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:99)只核 SHA，不核长度，并在 [anomaly 分支之前](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:285)被采信。这直接反驳报告“anomaly 一律 unrecoverable”。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:524:947:248:2768:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:12:| HIGH-3 | **NOT-CLOSED** | 不存在根目录已 exit 2；递归唯一命中、多命中冲突、目录伪命中也通过。但“不可见”仍未闭合：存在但 `chmod 000` 的根会 exit 0 并假判 `unrecoverable`。此外 [`glob + os.path.isfile`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:134)跟随 symlink：根内 `.jsonl` symlink 指向根外 `.txt`、以及 symlink 目录逃逸到根外树，均被判唯一来源并进入 `approximate`。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:525:948:249:2769:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:14:| MEDIUM-2 | **CLOSED** | [报告 §6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:78)、[ledger duplicate_clusters](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:60)及逐条 `reference_time` 已落地；6 簇全部逐行对账。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:526:949:250:2772:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:14:CARD-G4-9 round-3 复审（静态审阅 + 只读复算）。你 round-2 裁定 10/13 CLOSED，三项 NOT-CLOSED：BLOCKER-1（--out 守卫比 resolve 字符串，hardlink 与 case-only 别名绕过截断输入）、HIGH-1（full_body_verified 只核 sha 不核长度且排在 anomaly 分支前，anomaly 记录被判 byte_exact）、HIGH-3（chmod 000 根 exit 0 假判 unrecoverable；glob 跟随 symlink 逃逸出根）；另 3 新 LOW（full_verified 长度范围应 131-180、distribution 省略 0 值键、line_count 数 LF 与 records 的 splitlines 口径不一）。开发方以 commit 73102875 提交整改。请只读复核这 6 项是否闭合：
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:527:950:252:2792:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1232:+- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:528:951:253:2793:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1234:+- **新 LOW ×3**：full_verified 长度范围修正为 131–180；台账 `class_distribution`/`recoverability_distribution` 补零并新增 `inline_state_distribution`（固定 schema，消费者无需补齐缺席键）；`line_count` 改用 `splitlines()` 与 records 同口径（原 `count("\n")` 在 bare CR / U+2028 下会与 records 数不一致）。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:529:952:254:2809:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1946:117:- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:530:953:255:2810:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1948:119:- **新 LOW ×3**：full_verified 长度范围修正为 131–180；台账 `class_distribution`/`recoverability_distribution` 补零并新增 `inline_state_distribution`（固定 schema，消费者无需补齐缺席键）；`line_count` 改用 `splitlines()` 与 records 同口径（原 `count("\n")` 在 bare CR / U+2028 下会与 records 数不一致）。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:531:954:256:2815:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:532:955:257:2816:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2144:     8	| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:533:956:258:2817:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2146:    10	| HIGH-1 | **NOT-CLOSED** | round-1 三个反例本身均已翻转为 `anomaly/FAIL → unrecoverable`；非法 64 字符非 hex 也被拒。但新增组合反例：`episode_body="abc"`、`episode_body_full="abc"`、SHA 正确、声明长度 `999`，实际得到 `inline_state=anomaly` 后仍被判 `byte_exact`。原因是 [`full_body_verified()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:99)只核 SHA，不核长度，并在 [anomaly 分支之前](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:285)被采信。这直接反驳报告“anomaly 一律 unrecoverable”。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:534:957:259:2818:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2148:    12	| HIGH-3 | **NOT-CLOSED** | 不存在根目录已 exit 2；递归唯一命中、多命中冲突、目录伪命中也通过。但“不可见”仍未闭合：存在但 `chmod 000` 的根会 exit 0 并假判 `unrecoverable`。此外 [`glob + os.path.isfile`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:134)跟随 symlink：根内 `.jsonl` symlink 指向根外 `.txt`、以及 symlink 目录逃逸到根外树，均被判唯一来源并进入 `approximate`。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:535:958:260:2819:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2150:    14	| MEDIUM-2 | **CLOSED** | [报告 §6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:78)、[ledger duplicate_clusters](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:60)及逐条 `reference_time` 已落地；6 簇全部逐行对账。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:536:959:261:2850:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:61:- **3 新 LOW**：full_verified 长度范围修正 131–180；台账三个 distribution 补零并新增 `inline_state_distribution`；`line_count` 与 records 改用同一 `splitlines()` 口径。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:540:965:274:3511:| HIGH-1 | **CLOSED / PASS** | [`full_body_verified()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:102)现有 SHA+严格长度门；[真实判定链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:340)在 full-body 分支前要求 `state != anomaly`。更强反例——full 本身 SHA/长度完全有效，但 inline 不符——仍落 `anomaly → unrecoverable`。无其它调用入口。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:543:968:277:3514:| LOW：distribution 零键 | **CLOSED** | [固定 schema 生成链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:437)与 [ledger](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:43)均包含 `unexpected/anomaly/unrecoverable: 0`，并新增 inline 三态。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:547:972:282:3534:所以：**冻结的 92 条 ledger 数值可采信；CARD-G4-9 生成器与整卡验收仍被 BLOCKER-1、HIGH-3 阻断。** 本轮未修改仓库或受审数据，未执行破坏性 fixture/G4-10 重放；Graphiti 工具本轮不可用。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:550:975:285:3544:| HIGH-1 | **CLOSED / PASS** | [`full_body_verified()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:102)现有 SHA+严格长度门；[真实判定链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:340)在 full-body 分支前要求 `state != anomaly`。更强反例——full 本身 SHA/长度完全有效，但 inline 不符——仍落 `anomaly → unrecoverable`。无其它调用入口。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:553:978:288:3547:| LOW：distribution 零键 | **CLOSED** | [固定 schema 生成链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:437)与 [ledger](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:43)均包含 `unexpected/anomaly/unrecoverable: 0`，并新增 inline 三态。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:557:982:293:3567:所以：**冻结的 92 条 ledger 数值可采信；CARD-G4-9 生成器与整卡验收仍被 BLOCKER-1、HIGH-3 阻断。** 本轮未修改仓库或受审数据，未执行破坏性 fixture/G4-10 重放；Graphiti 工具本轮不可用。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:596:1089:1206:    94	| 负例门（round-1 整改自证） | `--out`==`--dlq` → exit 2 拒写、DLQ 完好；transcripts 根缺失 → exit 2 拒诊；sha 匹配但长度不符（round-1 HIGH-1 反例①）→ anomaly/unrecoverable；坏 JSON 行/空行 → unparseable 逐行入台账不拒诊 |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:597:1091:1211:    99	- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:599:1093:1213:   101	- **BLOCKER-3（交付物未冻结漂移）**：以本卡 commit 冻结全部交付物 exact bytes（脚本/报告/台账/证据包同 commit）；grep-selfattest 已按最终版行号重生成并内嵌脚本 sha 前缀。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:600:1094:1214:   102	- **HIGH-1（inline 判定不 fail-closed）**：full_verified 加长度精确匹配门；truncated_prefix 加 64-hex 合法性门；anomaly 一律 unrecoverable + 如实 basis（不再谎称截断、不再滑入 approximate）。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:602:1096:1216:   104	- **HIGH-3（transcript 归因折叠）**：恰 1 个常规文件命中才算归因（多命中 = ambiguous 拒采信）；glob 改递归下探；transcripts 根缺失整体 exit 2（拒绝产出 unrecoverable 假象）。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:603:1097:1217:   105	- **MEDIUM-1**：`episode_body_full` 在盘且 sha 对账通过 → byte_exact 采信（现网 0 条，通路已备）。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:610:1105:1229:   117	- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:611:1106:1230:   118	- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:638:1175:1961:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:20:--- (4) 写出口（唯一，且经 O_NOFOLLOW+fstat inode 校验后才 ftruncate）:
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:639:1176:1962:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:21:517:            fd = os.open(args.out, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:645:1216:2307:| 3. HIGH-3 枚举 | **NOT-CLOSED** | 稳态目录 symlink、`scandir` 错误和 mode `000` 门已有改善。但 unreadable/walk error 设置 conflict 后，主链仍在 [395–397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:395)明确产出 `recoverability=unrecoverable`，直接反驳报告所称“既不宣称不可恢复” [报告:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:143)。此外 `os.walk.onerror` 只覆盖 `scandir`；逐条 `is_dir/stat` 错误可被静默当非候选，[islink→isfile→access→realpath](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:168)仍是路径级竞态。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:651:1222:2316:- **HIGH**：扫描不可见性仍被终态化为 `unrecoverable`。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:660:1235:2344:| 3. HIGH-3 枚举 | **NOT-CLOSED** | 稳态目录 symlink、`scandir` 错误和 mode `000` 门已有改善。但 unreadable/walk error 设置 conflict 后，主链仍在 [395–397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:395)明确产出 `recoverability=unrecoverable`，直接反驳报告所称“既不宣称不可恢复” [报告:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:143)。此外 `os.walk.onerror` 只覆盖 `scandir`；逐条 `is_dir/stat` 错误可被静默当非候选，[islink→isfile→access→realpath](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:168)仍是路径级竞态。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:666:1241:2353:- **HIGH**：扫描不可见性仍被终态化为 `unrecoverable`。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:672:1255:# CARD-G4-9 — DLQ 真实挂载 census 分诊报告
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:685:1349:| 负例门（round-1 整改自证） | `--out`==`--dlq` → exit 2 拒写、DLQ 完好；transcripts 根缺失 → exit 2 拒诊；sha 匹配但长度不符（round-1 HIGH-1 反例①）→ anomaly/unrecoverable；坏 JSON 行/空行 → unparseable 逐行入台账不拒诊 |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:687:1354:- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:689:1356:- **BLOCKER-3（交付物未冻结漂移）**：以本卡 commit 冻结全部交付物 exact bytes（脚本/报告/台账/证据包同 commit）；grep-selfattest 已按最终版行号重生成并内嵌脚本 sha 前缀。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:690:1357:- **HIGH-1（inline 判定不 fail-closed）**：full_verified 加长度精确匹配门；truncated_prefix 加 64-hex 合法性门；anomaly 一律 unrecoverable + 如实 basis（不再谎称截断、不再滑入 approximate）。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:692:1359:- **HIGH-3（transcript 归因折叠）**：恰 1 个常规文件命中才算归因（多命中 = ambiguous 拒采信）；glob 改递归下探；transcripts 根缺失整体 exit 2（拒绝产出 unrecoverable 假象）。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:693:1360:- **MEDIUM-1**：`episode_body_full` 在盘且 sha 对账通过 → byte_exact 采信（现网 0 条，通路已备）。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:700:1372:- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:701:1373:- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:715:1411:- **HIGH（不可见被终态化为 unrecoverable）**：扫描受阻/冲突时主链仍产出 `unrecoverable`，与报告"既不宣称不可恢复"自相矛盾。**整改**：引入第四态 **`unverifiable`**（源可见性不足，basis 逐条说明是遍历受阻/不可读候选/归因冲突），distribution 与 `unverifiable_list` 同步。实测：不可读子树 → `unverifiable=1`，不再冒充 unrecoverable。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:721:1448:CARD-G4-9 round-5 终裁复审（静态审阅 + 只读复算，禁改任何文件）。你 round-4 裁定 1/6 CLOSED，提出 2 BLOCKER / 1 HIGH / 2 MEDIUM / 3 LOW。开发方以 commit d2827a6d + d8d887f2 提交整改，请逐条只读复核：
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:729:1456:请对每项设计静态反例判断是否仍可绕过（尤其：保护集完整性、fd 身份与实际读取的绑定、unverifiable 与 unrecoverable 的语义边界、strict decode 的边界）。同时独立复算台账仍为 92 条 / class 89-2-1 / byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0 / 重复簇 6 簇 29 行 / unparseable 0。逐项 CLOSED/NOT-CLOSED + 总裁定（可验收/仍阻断）+ 新发现分级。若已可验收请明确说明；若仍阻断请说明**对一张只读 census 卡**而言该阻断是否与卡面范围相称。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:765:2281:/bin/zsh -lc "rg -n '不可读但可写|源侧 TOCTOU|不可见终态|非法 UTF-8|字段错型|root_prefix|fchmod|provenance|总裁定|BLOCKER' '_bmad-output/审查/codex-review-CARD-G4-9-round4.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:770:2288:145:rg -n \"BLOCKER-1|HIGH-3|JSONL|framing|非 dict|provenance|PARTIAL|CLOSED|NOT-CLOSED|新发现|总裁定|protected_ids|O_NOFOLLOW|os\\.walk|line_count\" '_bmad-output/审查/codex-review-CARD-G4-9-round3.md' | head -n 240
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:771:2289:160:14:CARD-G4-9 round-3 复审（静态审阅 + 只读复算）。你 round-2 裁定 10/13 CLOSED，三项 NOT-CLOSED：BLOCKER-1（--out 守卫比 resolve 字符串，hardlink 与 case-only 别名绕过截断输入）、HIGH-1（full_body_verified 只核 sha 不核长度且排在 anomaly 分支前，anomaly 记录被判 byte_exact）、HIGH-3（chmod 000 根 exit 0 假判 unrecoverable；glob 跟随 symlink 逃逸出根）；另 3 新 LOW（full_verified 长度范围应 131-180、distribution 省略 0 值键、line_count 数 LF 与 records 的 splitlines 口径不一）。开发方以 commit 73102875 提交整改。请只读复核这 6 项是否闭合：
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:778:2298:186:1214: - **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:784:2305:213:1937:99:- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:789:2310:226:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:792:2313:245:2765:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:7:| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:793:2314:246:2766:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:8:| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:794:2315:250:2772:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:14:CARD-G4-9 round-3 复审（静态审阅 + 只读复算）。你 round-2 裁定 10/13 CLOSED，三项 NOT-CLOSED：BLOCKER-1（--out 守卫比 resolve 字符串，hardlink 与 case-only 别名绕过截断输入）、HIGH-1（full_body_verified 只核 sha 不核长度且排在 anomaly 分支前，anomaly 记录被判 byte_exact）、HIGH-3（chmod 000 根 exit 0 假判 unrecoverable；glob 跟随 symlink 逃逸出根）；另 3 新 LOW（full_verified 长度范围应 131-180、distribution 省略 0 值键、line_count 数 LF 与 records 的 splitlines 口径不一）。开发方以 commit 73102875 提交整改。请只读复核这 6 项是否闭合：
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:795:2316:256:2815:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:796:2317:257:2816:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2144:     8	| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:802:2325:282:3534:所以：**冻结的 92 条 ledger 数值可采信；CARD-G4-9 生成器与整卡验收仍被 BLOCKER-1、HIGH-3 阻断。** 本轮未修改仓库或受审数据，未执行破坏性 fixture/G4-10 重放；Graphiti 工具本轮不可用。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:806:2329:293:3567:所以：**冻结的 92 条 ledger 数值可采信；CARD-G4-9 生成器与整卡验收仍被 BLOCKER-1、HIGH-3 阻断。** 本轮未修改仓库或受审数据，未执行破坏性 fixture/G4-10 重放；Graphiti 工具本轮不可用。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:817:2340:1211:    99	- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:819:2342:1213:   101	- **BLOCKER-3（交付物未冻结漂移）**：以本卡 commit 冻结全部交付物 exact bytes（脚本/报告/台账/证据包同 commit）；grep-selfattest 已按最终版行号重生成并内嵌脚本 sha 前缀。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:841:2388:  2307	| 3. HIGH-3 枚举 | **NOT-CLOSED** | 稳态目录 symlink、`scandir` 错误和 mode `000` 门已有改善。但 unreadable/walk error 设置 conflict 后，主链仍在 [395–397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:395)明确产出 `recoverability=unrecoverable`，直接反驳报告所称“既不宣称不可恢复” [报告:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:143)。此外 `os.walk.onerror` 只覆盖 `scandir`；逐条 `is_dir/stat` 错误可被静默当非候选，[islink→isfile→access→realpath](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:168)仍是路径级竞态。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:847:2397:  2316	- **HIGH**：扫描不可见性仍被终态化为 `unrecoverable`。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:856:2425:  2344	| 3. HIGH-3 枚举 | **NOT-CLOSED** | 稳态目录 symlink、`scandir` 错误和 mode `000` 门已有改善。但 unreadable/walk error 设置 conflict 后，主链仍在 [395–397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:395)明确产出 `recoverability=unrecoverable`，直接反驳报告所称“既不宣称不可恢复” [报告:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:143)。此外 `os.walk.onerror` 只覆盖 `scandir`；逐条 `is_dir/stat` 错误可被静默当非候选，[islink→isfile→access→realpath](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:168)仍是路径级竞态。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:862:2434:  2353	- **HIGH**：扫描不可见性仍被终态化为 `unrecoverable`。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:870:2968:35:| Codex 独立审查 round-1 | **BLOCKED**（3 BLOCKER：--out 可截断输入 / 快照不原子 / 交付物未冻结；3 HIGH：inline 判定 fail-open / request_id 归因传染 / transcript 归因折叠；3 MEDIUM + 4 LOW。同时确认：**当前 92 条数字逐项 0 mismatch**、class/三态/家族计数全对） | `_bmad-output/审查/codex-review-CARD-G4-9.md` |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:871:2969:37:| Codex 复审 round-2 | **仍阻断**（10/13 CLOSED；BLOCKER-1/HIGH-1/HIGH-3 未真正闭合 + 3 新 LOW）。同时独立复算确认：67ccebe1 冻结生效、92 条数字与 6/29 重复簇全部可复算 | `_bmad-output/审查/codex-review-CARD-G4-9-round2.md`（codex 被 cyber 误拦，内容由 stdout 抢救存档） |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:872:2970:40:| round-3 findings 逐条整改 | **6/6 完成**：transcript 并入保护集 / O_NOFOLLOW+fstat 消 TOCTOU / os.walk 替 glob（不跟随目录 symlink+遍历错误显式捕获）/ 不可读候选 fail-closed / JSONL 严格 LF 分帧 / 非 dict 归 unparseable。6 条新反例实测全过、数字第三次不变 | 报告 §7d + `grep-selfattest.txt` |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:873:2971:42:| round-4 findings 逐条整改 | **9/9 完成**：全候选入保护集 / 读侧 fd 身份消源侧 TOCTOU / 新增 unverifiable 第四态 / FIFO 设备门 / strict UTF-8 / 3 条错型与边界 LOW / provenance receipt。5 条新反例实测全过；第四次全量重跑数字仍不变 | 报告 §7e + `grep-selfattest.txt` |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:874:2973:50:- **HIGH-1 inline 判定 fail-open**：sha 匹配但长度不符会误判 full_verified（反例实测）。整改：长度精确匹配门 + 64-hex 合法性门 + anomaly 一律 fail-closed（unrecoverable + 如实 basis）。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:875:2974:52:- **HIGH-3 transcript 归因折叠**：多命中照单全收、目录缺失误判 unrecoverable=88（实测复现）。整改：恰 1 常规文件命中门 + 递归 glob + 目录缺失 exit 2 拒诊。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:884:3077:   157	- **HIGH（不可见被终态化为 unrecoverable）**：扫描受阻/冲突时主链仍产出 `unrecoverable`，与报告"既不宣称不可恢复"自相矛盾。**整改**：引入第四态 **`unverifiable`**（源可见性不足，basis 逐条说明是遍历受阻/不可读候选/归因冲突），distribution 与 `unverifiable_list` 同步。实测：不可读子树 → `unverifiable=1`，不再冒充 unrecoverable。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:889:3111:    35	| Codex 独立审查 round-1 | **BLOCKED**（3 BLOCKER：--out 可截断输入 / 快照不原子 / 交付物未冻结；3 HIGH：inline 判定 fail-open / request_id 归因传染 / transcript 归因折叠；3 MEDIUM + 4 LOW。同时确认：**当前 92 条数字逐项 0 mismatch**、class/三态/家族计数全对） | `_bmad-output/审查/codex-review-CARD-G4-9.md` |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:890:3113:    37	| Codex 复审 round-2 | **仍阻断**（10/13 CLOSED；BLOCKER-1/HIGH-1/HIGH-3 未真正闭合 + 3 新 LOW）。同时独立复算确认：67ccebe1 冻结生效、92 条数字与 6/29 重复簇全部可复算 | `_bmad-output/审查/codex-review-CARD-G4-9-round2.md`（codex 被 cyber 误拦，内容由 stdout 抢救存档） |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:891:3114:    38	| round-2 findings 逐条整改 | **6/6 完成**：inode 身份守卫封 hardlink+大小写别名 / full_body 长度门+anomaly 前置 / 不可读根 exit 2+symlink 逃逸拒采信 / 3 新 LOW。5 条新负例实测全过、正例无回归、数字仍逐项一致 | 报告 §7/§7c + `grep-selfattest.txt` |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:892:3115:    39	| Codex 复审 round-3 | **仍阻断**（4/6 CLOSED；BLOCKER-1/HIGH-3 判 PARTIAL + 1 新 MEDIUM + 2 新 LOW）。同时确认：HIGH-1 与三条 LOW 已闭合、台账数字有效且与 commit 字节一致 | `_bmad-output/审查/codex-review-CARD-G4-9-round3.md` |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:893:3116:    40	| round-3 findings 逐条整改 | **6/6 完成**：transcript 并入保护集 / O_NOFOLLOW+fstat 消 TOCTOU / os.walk 替 glob（不跟随目录 symlink+遍历错误显式捕获）/ 不可读候选 fail-closed / JSONL 严格 LF 分帧 / 非 dict 归 unparseable。6 条新反例实测全过、数字第三次不变 | 报告 §7d + `grep-selfattest.txt` |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:894:3117:    41	| Codex 复审 round-4 | **仍阻断**（1/6 CLOSED；2 新 BLOCKER + 1 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round4.md` |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:895:3118:    42	| round-4 findings 逐条整改 | **9/9 完成**：全候选入保护集 / 读侧 fd 身份消源侧 TOCTOU / 新增 unverifiable 第四态 / FIFO 设备门 / strict UTF-8 / 3 条错型与边界 LOW / provenance receipt。5 条新反例实测全过；第四次全量重跑数字仍不变 | 报告 §7e + `grep-selfattest.txt` |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:900:3332:总裁定：**仍阻断 / CARD-G4-9 不可验收**。  
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:904:3341:| 3. `unverifiable` 四态 | **NOT-CLOSED · HIGH** | distribution/list 同步已实现。但 `anomaly→unrecoverable` 位于 conflict 判断之前，[script:464](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:464)：`anomaly + 扫描受阻/不可读/归因冲突` 仍被假终态化。另无 token 时未扫描即返回，truncated 记录随后被称为“无在盘源”，也应是 `unverifiable`。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:918:3377:总裁定：**仍阻断 / CARD-G4-9 不可验收**。  
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:922:3386:| 3. `unverifiable` 四态 | **NOT-CLOSED · HIGH** | distribution/list 同步已实现。但 `anomaly→unrecoverable` 位于 conflict 判断之前，[script:464](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:464)：`anomaly + 扫描受阻/不可读/归因冲突` 仍被假终态化。另无 token 时未扫描即返回，truncated 记录随后被称为“无在盘源”，也应是 `unverifiable`。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:945:@@ -5,335 +5,396 @@ BATCH-2026-08-28-第五批 / CARD-G4-9（G4-10 replay 的交接台账生成器
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:952:     **文件身份 (st_dev, st_ino) 比较**，与 --dlq/--compare/--qa-metrics-db
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:964:     unrecoverable 并显式给 anomaly basis（不谎称"截断前缀"）。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:974:     （chmod 000）时整体 exit 2（拒绝在源不可见时产出 unrecoverable 假象）；
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:979:     重算 sha **且长度**双门对账通过才按 byte_exact 采信，且 anomaly 记录
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:1087:     但 episode_body_length=999）仍被判 byte_exact —— 与 inline 侧同门收紧。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:1150:-    # 会把"没搜到"与"搜不了"混为一谈，产出假 unrecoverable。遍历出错即 fail-closed。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:1222:+        result["no_token"] = True
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:1373:         "--qa-metrics-db",
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:1462:     unrecoverable_keys = []
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:1477:             recover = "byte_exact"
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:1481:             recover = "byte_exact"
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:1484:-            recover = "unrecoverable"
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:1488:-            # 终态化为 unrecoverable 是不诚实的断言 —— 单列 unverifiable。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:1503:+            if sess.get("no_token"):
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:1518:+            recover = "unrecoverable"
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:1528:             recover = "unrecoverable"
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:1539:         if recover == "unrecoverable":
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:1540:             unrecoverable_keys.append(stable_key)
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:1611:         "card": "CARD-G4-9",
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:1630:             k: recover_dist.get(k, 0) for k in ["byte_exact", "approximate", "unverifiable", "unrecoverable"]
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:1635:         "unrecoverable_list": unrecoverable_keys,
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:1719:/bin/zsh -lc "stat -f '%N size=%z mtime=%Sm' -t '%Y-%m-%dT%H:%M:%S%z' _bmad-output/审查/codex-review-CARD-G4-9-round6.md" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:1721:_bmad-output/审查/codex-review-CARD-G4-9-round6.md size=24600 mtime=2026-08-28T20:27:15+0800
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:1772:   375	        "--qa-metrics-db",
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:1803:   406	    # 并把全部记录假判 unrecoverable —— 同样 fail-closed 拒诊。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:1901:   504	    unrecoverable_keys = []
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:1916:   519	            recover = "byte_exact"
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:1919:   522	            recover = "byte_exact"
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:1925:   528	            if sess.get("no_token"):
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:1940:   543	            recover = "unrecoverable"
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:1950:   553	            recover = "unrecoverable"
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:1960:   563	        if recover == "unrecoverable":
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:1961:   564	            unrecoverable_keys.append(stable_key)
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2026:   629	        "card": "CARD-G4-9",
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2045:   648	            k: recover_dist.get(k, 0) for k in ["byte_exact", "approximate", "unverifiable", "unrecoverable"]
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2050:   653	        "unrecoverable_list": unrecoverable_keys,
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2207:   141	    但 episode_body_length=999）仍被判 byte_exact —— 与 inline 侧同门收紧。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2297:   231	        result["no_token"] = True
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2418:**Questioning conflict with byte_exact output**
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2426:/bin/zsh -lc "rg -n -C 3 '92|89|byte_exact|approximate|unverifiable|unrecoverable|重复簇|归因冲突|no_token|callout_annotation|只读|零写入|qa_metrics|transcript' _bmad-output/审查/G4-9-DLQ-census-2026-08-28.md" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2429:  "card": "CARD-G4-9",
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2475:    "byte_exact": 4,
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2478:    "unrecoverable": 0
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2506:1-# CARD-G4-9 — DLQ 真实挂载 census 分诊报告
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2508:3-> **批次**: BATCH-2026-08-28-第五批 / CARD-G4-9（4h · wave 1 · 未来铺路）
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2569:70:| **可字节级**（byte_exact） | **4** | inline 正文全量：sha256 重算对账通过**且**长度精确匹配（fail-closed 双门）——重放可逐字节还原 episode |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2571:72:| **不可恢复**（unrecoverable） | **0** | inline 截断且经完整可见的扫描确认无在盘上游源 |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2584:85:逐条另带 `class / inline_state / recoverability / transcript_paths / transcript_match_count / attribution_conflict / error_excerpt / failed_at / reference_time`，G4-10 可直接按 `recoverability` 分桶排重放优先级（建议：4 条 byte_exact 先行——但其中 3 条 group_id 为已弃用 `vault:default`，重放前需按 D16 规约重映射并过 `to_physical_group_id()`；89 条 budget_400 重放前必须先修 context 超限根因，否则原样重放必然复现 400）。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2591:92-| grep 自证（import 行全 stdlib；neo4j/graphiti/bolt/app. import 0 命中；`--apply` 定义 0 命中；写模式 open 仅 `--out` 1 处且受路径碰撞守卫保护） | **PASS**（`grep-selfattest.txt`，含守卫在位证明） |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2594:95:| 负例门（round-1 整改自证） | `--out`==`--dlq` → exit 2 拒写、DLQ 完好；transcripts 根缺失 → exit 2 拒诊；sha 匹配但长度不符（round-1 HIGH-1 反例①）→ anomaly/unrecoverable；坏 JSON 行/空行 → unparseable 逐行入台账不拒诊 |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2595:96:| 负例门（round-2 整改自证） | **hardlink** 指向 DLQ 的 --out → exit 2 + DLQ sha 不变；**case-only 别名**（`DLQ.jsonl`）→ exit 2 + DLQ 完好；**anomaly + episode_body_full 组合**（sha 对但长度 999）→ anomaly/unrecoverable（不再翻案 byte_exact）；**chmod 000 根** → exit 2 拒诊；**symlink 逃逸**（根内 .jsonl → 根外 .txt）→ match_count=0/unrecoverable；正例回归：真实唯一命中仍 approximate |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2599:100-- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2601:102-- **BLOCKER-3（交付物未冻结漂移）**：以本卡 commit 冻结全部交付物 exact bytes（脚本/报告/台账/证据包同 commit）；grep-selfattest 已按最终版行号重生成并内嵌脚本 sha 前缀。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2602:103:- **HIGH-1（inline 判定不 fail-closed）**：full_verified 加长度精确匹配门；truncated_prefix 加 64-hex 合法性门；anomaly 一律 unrecoverable + 如实 basis（不再谎称截断、不再滑入 approximate）。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2604:105:- **HIGH-3（transcript 归因折叠）**：恰 1 个常规文件命中才算归因（多命中 = ambiguous 拒采信）；glob 改递归下探；transcripts 根缺失整体 exit 2（拒绝产出 unrecoverable 假象）。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2605:106:- **MEDIUM-1**：`episode_body_full` 在盘且 sha 对账通过 → byte_exact 采信（现网 0 条，通路已备）。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2617:118:- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2618:119:- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2629:130:  --qa-metrics-db "…/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db" \
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2651:157:- **HIGH（不可见被终态化为 unrecoverable）**：扫描受阻/冲突时主链仍产出 `unrecoverable`，与报告"既不宣称不可恢复"自相矛盾。**整改**：引入第四态 **`unverifiable`**（源可见性不足，basis 逐条说明是遍历受阻/不可读候选/归因冲突），distribution 与 `unverifiable_list` 同步。实测：不可读子树 → `unverifiable=1`，不再冒充 unrecoverable。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2665:171:- **HIGH①（anomaly 吞掉不可见性）**：`anomaly→unrecoverable` 排在 conflict 判断之前，`anomaly + 扫描受阻` 仍被假终态化。**整改**：判定链改为**可见性优先**——归因不可核验时无论 inline 状态一律 `unverifiable`，basis 逐条写明原因（无 token / token 冲突 / 扫描受阻 / 候选 stat 失败 / 不可读候选 / 多命中 ambiguous），并附注 inline 是否也 anomaly。实测：anomaly+不可读子树 → `unverifiable`。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2668:174:- **MEDIUM（无 token 未扫描即判不可恢复）**：改为 `unverifiable` + `no_token` 标记（见 HIGH①）。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2671:177:**归因冲突计数由 0 变为 3（如实说明）**：round-5 起"名字不含 session token"被诚实标记为 `no_token`（未做归因扫描），命中的正是 3 条 `callout_annotation` 记录。它们 inline 正文全量、sha 对账通过，**不依赖 transcript**，故仍判 `byte_exact`——三态分布不变（4/88/0/0），88 条 approximate 仍全部为唯一 transcript 命中。这是标注口径变诚实，不是结论变化。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2673:179:round-5 整改后第五次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变——五轮整改数字全程未变**。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2676:/bin/zsh -lc "rg -n -C 3 '92|89|byte_exact|approximate|unverifiable|unrecoverable|重复簇|归因冲突|no_token|callout_annotation|只读|零写入|qa_metrics|transcript|写入' _bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2678:3-title: "UAT · CARD-G4-9 DLQ 真实挂载 census 分诊（2026-08-28）"
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2681:6:scope: "BATCH-2026-08-28-第五批 / CARD-G4-9 — live DLQ 92 条只读 census：分类/SHA 对账/可恢复性三态/挂载真相，产出 G4-10 交接台账"
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2685:10-# UAT · CARD-G4-9 DLQ 真实挂载 census 分诊
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2703:28:| 脚本只读自证（判据 a） | import 行全 stdlib；neo4j/graphiti/bolt/app. import **0 命中**；`--apply` 定义 **0 命中**；写模式 open 仅台账 `--out` 1 处 | `G4-9-evidence/grep-selfattest.txt` |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2710:35:| Codex 独立审查 round-1 | **BLOCKED**（3 BLOCKER：--out 可截断输入 / 快照不原子 / 交付物未冻结；3 HIGH：inline 判定 fail-open / request_id 归因传染 / transcript 归因折叠；3 MEDIUM + 4 LOW。同时确认：**当前 92 条数字逐项 0 mismatch**、class/三态/家族计数全对） | `_bmad-output/审查/codex-review-CARD-G4-9.md` |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2712:37:| Codex 复审 round-2 | **仍阻断**（10/13 CLOSED；BLOCKER-1/HIGH-1/HIGH-3 未真正闭合 + 3 新 LOW）。同时独立复算确认：67ccebe1 冻结生效、92 条数字与 6/29 重复簇全部可复算 | `_bmad-output/审查/codex-review-CARD-G4-9-round2.md`（codex 被 cyber 误拦，内容由 stdout 抢救存档） |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2713:38-| round-2 findings 逐条整改 | **6/6 完成**：inode 身份守卫封 hardlink+大小写别名 / full_body 长度门+anomaly 前置 / 不可读根 exit 2+symlink 逃逸拒采信 / 3 新 LOW。5 条新负例实测全过、正例无回归、数字仍逐项一致 | 报告 §7/§7c + `grep-selfattest.txt` |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2714:39-| Codex 复审 round-3 | **仍阻断**（4/6 CLOSED；BLOCKER-1/HIGH-3 判 PARTIAL + 1 新 MEDIUM + 2 新 LOW）。同时确认：HIGH-1 与三条 LOW 已闭合、台账数字有效且与 commit 字节一致 | `_bmad-output/审查/codex-review-CARD-G4-9-round3.md` |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2715:40:| round-3 findings 逐条整改 | **6/6 完成**：transcript 并入保护集 / O_NOFOLLOW+fstat 消 TOCTOU / os.walk 替 glob（不跟随目录 symlink+遍历错误显式捕获）/ 不可读候选 fail-closed / JSONL 严格 LF 分帧 / 非 dict 归 unparseable。6 条新反例实测全过、数字第三次不变 | 报告 §7d + `grep-selfattest.txt` |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2716:41-| Codex 复审 round-4 | **仍阻断**（1/6 CLOSED；2 新 BLOCKER + 1 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round4.md` |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2717:42:| round-4 findings 逐条整改 | **9/9 完成**：全候选入保护集 / 读侧 fd 身份消源侧 TOCTOU / 新增 unverifiable 第四态 / FIFO 设备门 / strict UTF-8 / 3 条错型与边界 LOW / provenance receipt。5 条新反例实测全过；第四次全量重跑数字仍不变 | 报告 §7e + `grep-selfattest.txt` |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2718:43-| Codex 复审 round-5 | **仍阻断**（3/8 CLOSED；2 BLOCKER + 2 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round5.md` |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2719:44:| round-5 findings 逐条整改 | **9/9 完成**：先扫描后判定（冲突候选亦入保护集）/ QA DB fd 身份+复核 / 可见性优先于 anomaly / fchmod 后置于碰撞检查 / QA DB 特殊文件门 / no_token 归 unverifiable / 3 条 LOW。6 条新反例实测全过；第五次全量重跑数字仍不变 | 报告 §7f |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2727:52:- **HIGH-1 inline 判定 fail-open**：sha 匹配但长度不符会误判 full_verified（反例实测）。整改：长度精确匹配门 + 64-hex 合法性门 + anomaly 一律 fail-closed（unrecoverable + 如实 basis）。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2729:54:- **HIGH-3 transcript 归因折叠**：多命中照单全收、目录缺失误判 unrecoverable=88（实测复现）。整改：恰 1 常规文件命中门 + 递归 glob + 目录缺失 exit 2 拒诊。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2760:88:- **把"看不见"说成"不可恢复"**：扫描受阻时仍输出 `unrecoverable`，与报告里"既不宣称不可恢复"自相矛盾。→ 新增第四态 **`unverifiable`**，逐条写明是遍历受阻还是候选不可读。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2771:99:- **anomaly 吞掉了"看不见"**：`anomaly→unrecoverable` 排在可见性判断之前，扫描受阻时仍断言"不可恢复"。→ 判定链改为**可见性优先**。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2785:113-- `_bmad-output/审查/codex-review-CARD-G4-9.md` — Codex 独立审查存档
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2798:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2817:    "recoverability": "byte_exact",
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2831:    "recoverability": "byte_exact",
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2845:    "recoverability": "byte_exact",
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2859:/bin/zsh -lc 'git diff --no-ext-diff --unified=5 4c125f19''^ 4c125f19 -- _bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2861:     1	== CARD-G4-9 / CARD-G4-16 artifact commit receipt ==
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2865:     5	67ccebe1  CARD-G4-9 初版交付（脚本/报告/台账/证据包/round-1 审查/UAT）
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2870:    10	d2827a6d  CARD-G4-9 round-4 整改（本 receipt 所描述的 commit）
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2876:diff --git "a/_bmad-output/\351\252\214\346\224\266\345\215\225/UAT-CARD-G4-9-DLQ\347\234\237\345\256\236\346\214\202\350\275\275census\345\210\206\350\257\212-2026-08-28.md" "b/_bmad-output/\351\252\214\346\224\266\345\215\225/UAT-CARD-G4-9-DLQ\347\234\237\345\256\236\346\214\202\350\275\275census\345\210\206\350\257\212-2026-08-28.md"
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2878:--- "a/_bmad-output/\351\252\214\346\224\266\345\215\225/UAT-CARD-G4-9-DLQ\347\234\237\345\256\236\346\214\202\350\275\275census\345\210\206\350\257\212-2026-08-28.md"
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2879:+++ "b/_bmad-output/\351\252\214\346\224\266\345\215\225/UAT-CARD-G4-9-DLQ\347\234\237\345\256\236\346\214\202\350\275\275census\345\210\206\350\257\212-2026-08-28.md"
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2881: | round-2 findings 逐条整改 | **6/6 完成**：inode 身份守卫封 hardlink+大小写别名 / full_body 长度门+anomaly 前置 / 不可读根 exit 2+symlink 逃逸拒采信 / 3 新 LOW。5 条新负例实测全过、正例无回归、数字仍逐项一致 | 报告 §7/§7c + `grep-selfattest.txt` |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2882: | Codex 复审 round-3 | **仍阻断**（4/6 CLOSED；BLOCKER-1/HIGH-3 判 PARTIAL + 1 新 MEDIUM + 2 新 LOW）。同时确认：HIGH-1 与三条 LOW 已闭合、台账数字有效且与 commit 字节一致 | `_bmad-output/审查/codex-review-CARD-G4-9-round3.md` |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2883: | round-3 findings 逐条整改 | **6/6 完成**：transcript 并入保护集 / O_NOFOLLOW+fstat 消 TOCTOU / os.walk 替 glob（不跟随目录 symlink+遍历错误显式捕获）/ 不可读候选 fail-closed / JSONL 严格 LF 分帧 / 非 dict 归 unparseable。6 条新反例实测全过、数字第三次不变 | 报告 §7d + `grep-selfattest.txt` |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2884: | Codex 复审 round-4 | **仍阻断**（1/6 CLOSED；2 新 BLOCKER + 1 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round4.md` |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2885: | round-4 findings 逐条整改 | **9/9 完成**：全候选入保护集 / 读侧 fd 身份消源侧 TOCTOU / 新增 unverifiable 第四态 / FIFO 设备门 / strict UTF-8 / 3 条错型与边界 LOW / provenance receipt。5 条新反例实测全过；第四次全量重跑数字仍不变 | 报告 §7e + `grep-selfattest.txt` |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2886:+| Codex 复审 round-5 | **仍阻断**（3/8 CLOSED；2 BLOCKER + 2 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round5.md` |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2887:+| round-5 findings 逐条整改 | **9/9 完成**：先扫描后判定（冲突候选亦入保护集）/ QA DB fd 身份+复核 / 可见性优先于 anomaly / fchmod 后置于碰撞检查 / QA DB 特殊文件门 / no_token 归 unverifiable / 3 条 LOW。6 条新反例实测全过；第五次全量重跑数字仍不变 | 报告 §7f |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2894: - **把"看不见"说成"不可恢复"**：扫描受阻时仍输出 `unrecoverable`，与报告里"既不宣称不可恢复"自相矛盾。→ 新增第四态 **`unverifiable`**，逐条写明是遍历受阻还是候选不可读。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2905:+- **anomaly 吞掉了"看不见"**：`anomaly→unrecoverable` 排在可见性判断之前，扫描受阻时仍断言"不可恢复"。→ 判定链改为**可见性优先**。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2940:+- **HIGH①（anomaly 吞掉不可见性）**：`anomaly→unrecoverable` 排在 conflict 判断之前，`anomaly + 扫描受阻` 仍被假终态化。**整改**：判定链改为**可见性优先**——归因不可核验时无论 inline 状态一律 `unverifiable`，basis 逐条写明原因（无 token / token 冲突 / 扫描受阻 / 候选 stat 失败 / 不可读候选 / 多命中 ambiguous），并附注 inline 是否也 anomaly。实测：anomaly+不可读子树 → `unverifiable`。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2943:+- **MEDIUM（无 token 未扫描即判不可恢复）**：改为 `unverifiable` + `no_token` 标记（见 HIGH①）。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2946:+**归因冲突计数由 0 变为 3（如实说明）**：round-5 起"名字不含 session token"被诚实标记为 `no_token`（未做归因扫描），命中的正是 3 条 `callout_annotation` 记录。它们 inline 正文全量、sha 对账通过，**不依赖 transcript**，故仍判 `byte_exact`——三态分布不变（4/88/0/0），88 条 approximate 仍全部为唯一 transcript 命中。这是标注口径变诚实，不是结论变化。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2948:+round-5 整改后第五次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变——五轮整改数字全程未变**。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2965:/bin/zsh -lc "git diff --no-ext-diff --name-status 4c125f19 -- . ':(exclude)_bmad-output/审查/codex-review-CARD-G4-9-round6.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2979:  "card": "CARD-G4-9",
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:2991:  "unrecoverable_list": [],
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3036:    "recoverability": "byte_exact",
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3049:    "recoverability": "byte_exact",
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3062:    "recoverability": "byte_exact",
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3073:d8d887f2 docs(census): 补 artifact commit receipt 绑定精确 SHA 链 [BATCH-2026-08-28-第五批 / CARD-G4-9]
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3074:4c125f19 (HEAD -> card/s5-census) fix(census): G4-9 Codex round-5 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9]
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3081:d8d887f2 docs(census): 补 artifact commit receipt 绑定精确 SHA 链 [BATCH-2026-08-28-第五批 / CARD-G4-9]
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3088:/bin/zsh -lc "nl -ba _bmad-output/审查/G4-9-evidence/grep-selfattest.txt | sed -n '1,140p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3090:     1	== CARD-G4-9 只读自证（round-4 整改版, f27531b8a50f035d…） ==
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3142:/bin/zsh -lc 'nl -ba _bmad-output/审查/G4-9-evidence/census-stderr.txt && shasum -a 256 backend/scripts/census_dead_letter_episodes.py _bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json _bmad-output/审查/G4-9-evidence/grep-selfattest.txt' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3144:     1	census: 92 条 (+0 unparseable) | class={'schema_entity_type': 2, 'group_id_format': 1, 'budget_400': 89} | recoverability={'byte_exact': 4, 'approximate': 88} | 归因冲突=3 | 重复簇=6 | 偏差=无 | qa_metrics 核销=no_source_rows
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3147:8fc715f585f827c25771b039e20d2865175803bb9c55d08bdd55412c0052c6b5  _bmad-output/审查/G4-9-evidence/grep-selfattest.txt
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3204:/bin/zsh -lc "nl -ba _bmad-output/审查/codex-review-CARD-G4-9-round5.md | sed -n '3300,3420p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3221:  3315	? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round5.md"
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3228:  3322	  ✓ 锁定 HEAD、提交链、工作树状态、CARD-G4-9 报告与生产入口
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3238:  3332	总裁定：**仍阻断 / CARD-G4-9 不可验收**。  
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3247:  3341	| 3. `unverifiable` 四态 | **NOT-CLOSED · HIGH** | distribution/list 同步已实现。但 `anomaly→unrecoverable` 位于 conflict 判断之前，[script:464](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:464)：`anomaly + 扫描受阻/不可读/归因冲突` 仍被假终态化。另无 token 时未扫描即返回，truncated 记录随后被称为“无在盘源”，也应是 `unverifiable`。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3262:  3356	- byte_exact **4**；approximate **88**；unverifiable **0**；unrecoverable **0**
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3276:  3370	这个阻断与“一张只读 census 卡”的范围**完全相称**：报告和 UAT 明确承诺纯只读、零写入，[UAT:13](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:13)。残留反例能直接截断或修改本卡正在保护的恢复源，不是范围外的生产级加固要求。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3283:  3377	总裁定：**仍阻断 / CARD-G4-9 不可验收**。  
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3292:  3386	| 3. `unverifiable` 四态 | **NOT-CLOSED · HIGH** | distribution/list 同步已实现。但 `anomaly→unrecoverable` 位于 conflict 判断之前，[script:464](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:464)：`anomaly + 扫描受阻/不可读/归因冲突` 仍被假终态化。另无 token 时未扫描即返回，truncated 记录随后被称为“无在盘源”，也应是 `unverifiable`。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3307:  3401	- byte_exact **4**；approximate **88**；unverifiable **0**；unrecoverable **0**
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3321:  3415	这个阻断与“一张只读 census 卡”的范围**完全相称**：报告和 UAT 明确承诺纯只读、零写入，[UAT:13](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:13)。残留反例能直接截断或修改本卡正在保护的恢复源，不是范围外的生产级加固要求。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3404:no_token_lines = [n for n, r in records if not tokens(r.get("name", ""))]
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3447:    "no_token_lines": no_token_lines,
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3548:no_token_lines = [n for n, r in records if not tokens(r.get("name", ""))]
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3586:    "no_token_lines": no_token_lines,
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3597:{"approximate_internal_contract_rows": 88, "bytes": 99915, "class": {"budget_400": 89, "group_id_format": 1, "schema_entity_type": 2}, "duplicate_clusters": 6, "duplicate_occurrences": 29, "duplicate_sizes": [16, 4, 3, 2, 2, 2], "inline": {"full_verified": 4, "truncated_prefix": 88}, "ledger_attribution_conflicts": 3, "ledger_record_mismatches": [], "ledger_recoverability": {"approximate": 88, "byte_exact": 4, "unrecoverable": 0, "unverifiable": 0}, "ledger_sha_matches_source": true, "lf_frames": 92, "no_token_lines": [1, 2, 3, 5, 6, 9, 10, 13, 14, 18, 20, 21, 24, 25, 29, 30, 31, 33, 34, 37, 38, 41, 42, 45, 46, 49, 50, 53, 54, 57, 58, 61, 62, 65, 66, 69, 70, 73, 74, 75, 78, 79, 82, 83, 86, 87, 90, 91], "records": 92, "request_groups": 25, "sha256": "3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590", "token_prefix_conflict_groups": 0, "unparseable": 0}
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3599:**Revising no_token_lines grouping logic**
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3632:no_token=[]
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3638:        no_token.extend(nums)
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3641:print(json.dumps({"group_no_token_record_lines":sorted(no_token),"group_token_conflict_record_lines":sorted(conflict),"no_token_records":len(no_token),"conflict_records":len(conflict)}))
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3644:{"group_no_token_record_lines": [1, 2, 3], "group_token_conflict_record_lines": [], "no_token_records": 3, "conflict_records": 0}
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3666:33:    （chmod 000）时整体 exit 2（拒绝在源不可见时产出 unrecoverable 假象）；
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3719:/bin/zsh -lc "python3 -B -c 'import runpy,json; from pathlib import Path; m=runpy.run_path(\"backend/scripts/census_dead_letter_episodes.py\"); f=m[\"resolve_group_attribution\"]; a=f([\"board\",\"vault\"],Path(\".\")); b=f([],Path(\".\")); print(json.dumps({\"conflict\":{\"token_conflict\":a.get(\"token_conflict\"),\"all_candidate_count\":len(a[\"all_candidate_paths\"]),\"scan_errors\":len(a.get(\"scan_errors\",[]))},\"no_token\":{\"no_token\":b.get(\"no_token\"),\"all_candidate_count\":len(b[\"all_candidate_paths\"])}}))'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3721:{"conflict": {"token_conflict": true, "all_candidate_count": 2, "scan_errors": 0}, "no_token": {"no_token": true, "all_candidate_count": 0}}
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3725:**Investigating missing no_token marker**
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3726:**Clarifying no_token recoverability logic**
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3727:**Resolving no_token status and JSON encoding issues**
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3793:    56	  "byte_exact": 4,
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3796:    59	  "unrecoverable": 0
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3803:    66	 "unrecoverable_list": [],
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3920:/bin/zsh -lc "nl -ba _bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md | sed -n '10,35p;40,46p;93,106p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3922:    10	# UAT · CARD-G4-9 DLQ 真实挂载 census 分诊
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3940:    28	| 脚本只读自证（判据 a） | import 行全 stdlib；neo4j/graphiti/bolt/app. import **0 命中**；`--apply` 定义 **0 命中**；写模式 open 仅台账 `--out` 1 处 | `G4-9-evidence/grep-selfattest.txt` |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3947:    35	| Codex 独立审查 round-1 | **BLOCKED**（3 BLOCKER：--out 可截断输入 / 快照不原子 / 交付物未冻结；3 HIGH：inline 判定 fail-open / request_id 归因传染 / transcript 归因折叠；3 MEDIUM + 4 LOW。同时确认：**当前 92 条数字逐项 0 mismatch**、class/三态/家族计数全对） | `_bmad-output/审查/codex-review-CARD-G4-9.md` |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3948:    40	| round-3 findings 逐条整改 | **6/6 完成**：transcript 并入保护集 / O_NOFOLLOW+fstat 消 TOCTOU / os.walk 替 glob（不跟随目录 symlink+遍历错误显式捕获）/ 不可读候选 fail-closed / JSONL 严格 LF 分帧 / 非 dict 归 unparseable。6 条新反例实测全过、数字第三次不变 | 报告 §7d + `grep-selfattest.txt` |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3949:    41	| Codex 复审 round-4 | **仍阻断**（1/6 CLOSED；2 新 BLOCKER + 1 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round4.md` |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3950:    42	| round-4 findings 逐条整改 | **9/9 完成**：全候选入保护集 / 读侧 fd 身份消源侧 TOCTOU / 新增 unverifiable 第四态 / FIFO 设备门 / strict UTF-8 / 3 条错型与边界 LOW / provenance receipt。5 条新反例实测全过；第四次全量重跑数字仍不变 | 报告 §7e + `grep-selfattest.txt` |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3951:    43	| Codex 复审 round-5 | **仍阻断**（3/8 CLOSED；2 BLOCKER + 2 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round5.md` |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3952:    44	| round-5 findings 逐条整改 | **9/9 完成**：先扫描后判定（冲突候选亦入保护集）/ QA DB fd 身份+复核 / 可见性优先于 anomaly / fchmod 后置于碰撞检查 / QA DB 特殊文件门 / no_token 归 unverifiable / 3 条 LOW。6 条新反例实测全过；第五次全量重跑数字仍不变 | 报告 §7f |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3961:    99	- **anomaly 吞掉了"看不见"**：`anomaly→unrecoverable` 排在可见性判断之前，扫描受阻时仍断言"不可恢复"。→ 判定链改为**可见性优先**。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3973:     1	# CARD-G4-9 — DLQ 真实挂载 census 分诊报告
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:3975:     3	> **批次**: BATCH-2026-08-28-第五批 / CARD-G4-9（4h · wave 1 · 未来铺路）
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:4008:    70	| **可字节级**（byte_exact） | **4** | inline 正文全量：sha256 重算对账通过**且**长度精确匹配（fail-closed 双门）——重放可逐字节还原 episode |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:4010:    72	| **不可恢复**（unrecoverable） | **0** | inline 截断且经完整可见的扫描确认无在盘上游源 |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:4023:    85	逐条另带 `class / inline_state / recoverability / transcript_paths / transcript_match_count / attribution_conflict / error_excerpt / failed_at / reference_time`，G4-10 可直接按 `recoverability` 分桶排重放优先级（建议：4 条 byte_exact 先行——但其中 3 条 group_id 为已弃用 `vault:default`，重放前需按 D16 规约重映射并过 `to_physical_group_id()`；89 条 budget_400 重放前必须先修 context 超限根因，否则原样重放必然复现 400）。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:4029:    92	| grep 自证（import 行全 stdlib；neo4j/graphiti/bolt/app. import 0 命中；`--apply` 定义 0 命中；写模式 open 仅 `--out` 1 处且受路径碰撞守卫保护） | **PASS**（`grep-selfattest.txt`，含守卫在位证明） |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:4032:    95	| 负例门（round-1 整改自证） | `--out`==`--dlq` → exit 2 拒写、DLQ 完好；transcripts 根缺失 → exit 2 拒诊；sha 匹配但长度不符（round-1 HIGH-1 反例①）→ anomaly/unrecoverable；坏 JSON 行/空行 → unparseable 逐行入台账不拒诊 |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:4033:    96	| 负例门（round-2 整改自证） | **hardlink** 指向 DLQ 的 --out → exit 2 + DLQ sha 不变；**case-only 别名**（`DLQ.jsonl`）→ exit 2 + DLQ 完好；**anomaly + episode_body_full 组合**（sha 对但长度 999）→ anomaly/unrecoverable（不再翻案 byte_exact）；**chmod 000 根** → exit 2 拒诊；**symlink 逃逸**（根内 .jsonl → 根外 .txt）→ match_count=0/unrecoverable；正例回归：真实唯一命中仍 approximate |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:4044:   171	- **HIGH①（anomaly 吞掉不可见性）**：`anomaly→unrecoverable` 排在 conflict 判断之前，`anomaly + 扫描受阻` 仍被假终态化。**整改**：判定链改为**可见性优先**——归因不可核验时无论 inline 状态一律 `unverifiable`，basis 逐条写明原因（无 token / token 冲突 / 扫描受阻 / 候选 stat 失败 / 不可读候选 / 多命中 ambiguous），并附注 inline 是否也 anomaly。实测：anomaly+不可读子树 → `unverifiable`。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:4047:   174	- **MEDIUM（无 token 未扫描即判不可恢复）**：改为 `unverifiable` + `no_token` 标记（见 HIGH①）。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:4050:   177	**归因冲突计数由 0 变为 3（如实说明）**：round-5 起"名字不含 session token"被诚实标记为 `no_token`（未做归因扫描），命中的正是 3 条 `callout_annotation` 记录。它们 inline 正文全量、sha 对账通过，**不依赖 transcript**，故仍判 `byte_exact`——三态分布不变（4/88/0/0），88 条 approximate 仍全部为唯一 transcript 命中。这是标注口径变诚实，不是结论变化。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:4052:   179	round-5 整改后第五次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变——五轮整改数字全程未变**。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:4081:   202	   "recoverability": "byte_exact",
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:4106:   227	   "recoverability": "byte_exact",
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:4131:   252	   "recoverability": "byte_exact",
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:4376:/bin/zsh -lc "stat -f '%N size=%z mtime=%Sm' -t '%Y-%m-%dT%H:%M:%S%z' _bmad-output/审查/codex-review-CARD-G4-9-round6.md" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:4378:_bmad-output/审查/codex-review-CARD-G4-9-round6.md size=425092 mtime=2026-08-28T20:43:00+0800
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:4396:?? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round6.md"
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:4422:**Clarifying no_token conflict artifact meaning**
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:4434:总裁定：**仍阻断，CARD-G4-9 round-6 不可验收。**
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:4448:| 3. visibility 优先于 anomaly | **CLOSED** | byte-exact 两支之后，`attribution_conflict→unverifiable` 已位于 `anomaly→unrecoverable` 前：[exact](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:518)、[conflict](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:524)、[anomaly](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:542)。exact 先行是合理例外，因为不依赖 transcript。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:4451:| 6. no_token→unverifiable | **CLOSED（行为）** | 非 byte-exact 的 no-token 记录会进入 `unverifiable`；full-verified/no-token 仍为 byte-exact，语义正确。[no_token](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:228)。但 `no_token` 未写入 ledger，见下方 LOW。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:4476:- recoverability：4 byte_exact / 88 approximate / 0 unverifiable / 0 unrecoverable
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:4484:`attribution_conflict=3` 与 `byte_exact=4 / unverifiable=0` **诚实且自洽**：独立分组确认只有行 1–3 的组完全无 token；它们正是三个 callout，且 inline SHA+长度双门通过，[ledger:179](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:179)。归因不可用与正文已能逐字节恢复是两个独立维度。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:4488:- **MEDIUM — 证据包漂移**：`grep-selfattest.txt` 仍标注 round-4、旧脚本 SHA `f275…` 和旧行号，[evidence:1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:1)；receipt 只记录到 `d2827a6d`，[receipt:10](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt:10)，未绑定当前 `4c125f19`。报告/UAT 对“当前证据包”的声明不成立。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:4489:- **LOW — ledger 不自描述**：`no_token` 仅存在于内存；记录只序列化笼统的 `attribution_conflict=true`，无法区分缺 token、token 冲突或多命中。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:4498:总裁定：**仍阻断，CARD-G4-9 round-6 不可验收。**
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:4512:| 3. visibility 优先于 anomaly | **CLOSED** | byte-exact 两支之后，`attribution_conflict→unverifiable` 已位于 `anomaly→unrecoverable` 前：[exact](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:518)、[conflict](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:524)、[anomaly](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:542)。exact 先行是合理例外，因为不依赖 transcript。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:4515:| 6. no_token→unverifiable | **CLOSED（行为）** | 非 byte-exact 的 no-token 记录会进入 `unverifiable`；full-verified/no-token 仍为 byte-exact，语义正确。[no_token](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:228)。但 `no_token` 未写入 ledger，见下方 LOW。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:4540:- recoverability：4 byte_exact / 88 approximate / 0 unverifiable / 0 unrecoverable
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:4548:`attribution_conflict=3` 与 `byte_exact=4 / unverifiable=0` **诚实且自洽**：独立分组确认只有行 1–3 的组完全无 token；它们正是三个 callout，且 inline SHA+长度双门通过，[ledger:179](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:179)。归因不可用与正文已能逐字节恢复是两个独立维度。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:4552:- **MEDIUM — 证据包漂移**：`grep-selfattest.txt` 仍标注 round-4、旧脚本 SHA `f275…` 和旧行号，[evidence:1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:1)；receipt 只记录到 `d2827a6d`，[receipt:10](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt:10)，未绑定当前 `4c125f19`。报告/UAT 对“当前证据包”的声明不成立。
./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:4553:- **LOW — ledger 不自描述**：`no_token` 仅存在于内存；记录只序列化笼统的 `attribution_conflict=true`，无法区分缺 token、token 冲突或多命中。
./_bmad-output/审查/codex-review-CARD-G4-9-round2.md:7:| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round2.md:10:| HIGH-1 | **NOT-CLOSED** | round-1 三个反例本身均已翻转为 `anomaly/FAIL → unrecoverable`；非法 64 字符非 hex 也被拒。但新增组合反例：`episode_body="abc"`、`episode_body_full="abc"`、SHA 正确、声明长度 `999`，实际得到 `inline_state=anomaly` 后仍被判 `byte_exact`。原因是 [`full_body_verified()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:99)只核 SHA，不核长度，并在 [anomaly 分支之前](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:285)被采信。这直接反驳报告“anomaly 一律 unrecoverable”。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round2.md:11:| HIGH-2 | **CLOSED** | missing、显式 `null`、字面 `"None"` 不再合组；数字 `123` 与字符串 `"123"` 分离；非前缀多 token 均 `attribution_conflict=true/unrecoverable`；合法前缀组统一取最长 token。真实入口反例全部通过。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round2.md:12:| HIGH-3 | **NOT-CLOSED** | 不存在根目录已 exit 2；递归唯一命中、多命中冲突、目录伪命中也通过。但“不可见”仍未闭合：存在但 `chmod 000` 的根会 exit 0 并假判 `unrecoverable`。此外 [`glob + os.path.isfile`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:134)跟随 symlink：根内 `.jsonl` symlink 指向根外 `.txt`、以及 symlink 目录逃逸到根外树，均被判唯一来源并进入 `approximate`。 |
./_bmad-output/审查/codex-review-CARD-G4-9-round2.md:26:- recoverability：`4 byte_exact / 88 approximate / 0 unrecoverable`。
./_bmad-output/审查/codex-review-CARD-G4-9-round2.md:34:- **LOW**：ledger distribution 省略 `unexpected:0`、`anomaly:0`、`unrecoverable:0`，固定 schema 消费者需自行补零。

**Preserving untracked user file**
**Analyzing round6 review files and diffs**
exec
/bin/zsh -lc "rg --files '_bmad-output/审查' | rg 'CARD-G4-9|G4-9-evidence'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
_bmad-output/审查/codex-review-CARD-G4-9-round6.md
_bmad-output/审查/codex-review-CARD-G4-9-round2.md
_bmad-output/审查/codex-review-CARD-G4-9-round5.md
_bmad-output/审查/codex-review-CARD-G4-9-round4.md
_bmad-output/审查/codex-review-CARD-G4-9-round7.md
_bmad-output/审查/codex-review-CARD-G4-9.md
_bmad-output/审查/codex-review-CARD-G4-9-round3.md
_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt
_bmad-output/审查/G4-9-evidence/shasums-after.txt
_bmad-output/审查/G4-9-evidence/container-sha-check.txt
_bmad-output/审查/G4-9-evidence/census-stderr.txt
_bmad-output/审查/G4-9-evidence/shasums-before.txt
_bmad-output/审查/G4-9-evidence/grep-selfattest.txt

exec
/bin/zsh -lc 'git show --stat --summary --format=fuller 5b371253' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
commit 5b3712537ef5be91eda18e2a9eaf2fd3d5e03ef5
Author:     oinani0721 <2272104243@qq.com>
AuthorDate: Fri Aug 28 20:49:01 2026 +0800
Commit:     oinani0721 <2272104243@qq.com>
CommitDate: Fri Aug 28 20:49:01 2026 +0800

    fix(census): G4-9 Codex round-6 架构级修复 [BATCH-2026-08-28-第五批 / CARD-G4-9]
    
    根因: --out 保护集依赖枚举完整性 — 不可列举但可穿越目录(0333)内的 transcript
    os.walk 看不见即进不了保护集; QA DB inode ABA 同理。补丁修不掉, 是设计缺陷。
    架构修复: 增加不依赖枚举的路径层防御 — --out realpath 禁落 transcripts 根内
    (恢复源区域整体禁写) + 禁等于任一输入 realpath; 路径层与 inode 层双保险。
    另修: QA DB 验证 fd 保持打开至 SQLite 复核完毕(堵 ABA)+连接后二次 fstat 校验
    nlink; no_token 分支亦遍历(原完全不扫描, 候选进不了保护集); 证据包重生成
    (round-6 指出 self-attest 停留 round-4 旧 SHA, 属实); ledger 新增
    attribution_conflict_reason 自描述; json.dumps 对 lone surrogate 回退
    ensure_ascii=True 并标注, 不再整次拒绝。
    反例实测: 0333 隐藏目录内 transcript 作 --out → exit 2 且文件完好。
    第六次全量重跑 92/4-88-0-0/89-2-1/6-29/shasum 不变。
    
    Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>

 .../G4-9-DLQ-census-2026-08-28.md"                 |   14 +
 .../G4-9-dlq-ledger-2026-08-28.json"               |   94 +-
 .../G4-9-evidence/grep-selfattest.txt"             |   79 +-
 .../codex-review-CARD-G4-9-round6.md"              | 4559 ++++++++++++++++++++
 ...75census\345\210\206\350\257\212-2026-08-28.md" |   12 +
 backend/scripts/census_dead_letter_episodes.py     |   82 +-
 6 files changed, 4795 insertions(+), 45 deletions(-)
 create mode 100644 "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round6.md"

exec
/bin/zsh -lc 'git show --stat --summary --format=fuller 4ba4f847' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
commit 4ba4f847fa3ad83d136d3a40fcc5448b25c54ba5
Author:     oinani0721 <2272104243@qq.com>
AuthorDate: Fri Aug 28 20:49:03 2026 +0800
Commit:     oinani0721 <2272104243@qq.com>
CommitDate: Fri Aug 28 20:49:03 2026 +0800

    docs(census): receipt 补 round-5/6 commit 链 [BATCH-2026-08-28-第五批 / CARD-G4-9]
    
    Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>

 .../G4-9-evidence/artifact-commit-receipt.txt"                       | 5 ++++-
 1 file changed, 4 insertions(+), 1 deletion(-)

exec
/bin/zsh -lc "rg -n '6/9|BLOCKER|CLOSED|NOT-CLOSED|总裁定|新发现|--out|ABA|0333|no_token|surrogate' '_bmad-output/审查/codex-review-CARD-G4-9-round6.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
14:CARD-G4-9 round-6 复审（静态审阅 + 只读复算，禁改任何文件）。你 round-5 裁定 3/8 CLOSED，提出 2 BLOCKER / 2 HIGH / 2 MEDIUM / 3 LOW，并明确该阻断与只读 census 卡范围相称（因报告/UAT 承诺纯只读零写入，残留反例能截断或修改本卡正在保护的恢复源）——开发方接受该论证并以 commit 4c125f19 提交整改。请逐条只读复核：
15:1. BLOCKER token 冲突/无 token 扫描前早退 → resolve_group_attribution 重写为先扫描后判定：无条件对每个 token 遍历收集候选进 all_candidate_paths（保护集口径），再做 no_token/token_conflict/scan_errors/stat_failures/unreadable/多命中判定；候选 stat 失败改 exit 2。
16:2. BLOCKER qa_metrics.db 身份未绑定 → probe_qa_metrics 改 os.open(O_RDONLY|O_NOFOLLOW|O_NONBLOCK) 取 fstat 身份 + S_ISREG 门 → SQLite 打开后复核 os.stat 身份仍等于该身份，不等则 identity_changed_..._refused；身份入 protected_ids。
17:3. HIGH anomaly 吞不可见性 → 判定链改可见性优先：attribution_conflict 分支置于 anomaly 之前，一律 unverifiable，basis 区分 no_token/token_conflict/scan_errors/stat_failures/unreadable/ambiguous 并附注 inline 是否 anomaly。
20:6. MEDIUM 无 token 判不可恢复 → 改 unverifiable + no_token 标记。
21:7. LOW ×3 → 单独 LF 算 1 空行；inline/full_body 改 strict encode（堵 escaped lone surrogate 伪造 full_verified）；bool 排除出长度门。
22:请对每项设计静态反例判断是否仍可绕过。同时复核台账数字：92 条 / class 89-2-1 / byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0 / 重复簇 6/29 / unparseable 0；并核对新出现的 attribution_conflict=3（3 条 callout_annotation 无 session token，判 no_token 但因 inline 全量仍 byte_exact）——该口径变化是否诚实且自洽。逐项 CLOSED/NOT-CLOSED + 总裁定 + 新发现分级；若可验收请明确说明。
26:我会把本轮作为严格只读复审：先锁定 `4c125f19` 的实际 diff 与生产入口，再分三条独立证据链复核安全反例、QA DB 身份绑定、台账精确复算；全程不改文件，也不把现有测试结论当作证明。最终会逐项给出 `CLOSED/NOT-CLOSED`、可复现证据和验收边界。
33:  • 汇总 CLOSED/NOT-CLOSED、新发现分级与最终验收裁定
234:    2 BLOCKER: resolve_group_attribution 改先扫描后判定(token 冲突/无 token 的
241:    3 LOW: 单独 LF 算 1 空行; strict encode 堵 lone surrogate 伪造 full_verified;
244:    归因冲突 0→3 系 no_token 标注变诚实(3 条 callout 仍 byte_exact), 三态不变。
389:696:            # round-5 HIGH 整改: 碰撞检查必须**先于** fchmod —— 否则 --out 指向
395:/bin/zsh -lc "rg -n '"'^#{1,4} |BLOCKER|HIGH|MEDIUM|LOW|3/8|总裁定|CLOSED|NOT-CLOSED'"' _bmad-output/审查/codex-review-CARD-G4-9-round5.md" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
397:14:CARD-G4-9 round-5 终裁复审（静态审阅 + 只读复算，禁改任何文件）。你 round-4 裁定 1/6 CLOSED，提出 2 BLOCKER / 1 HIGH / 2 MEDIUM / 3 LOW。开发方以 commit d2827a6d + d8d887f2 提交整改，请逐条只读复核：
398:15:1. BLOCKER 不可读但可写 transcript 绕过保护集 → resolve_group_attribution 新增 all_candidate_paths（保留所有见到的候选，含 unreadable 与被冲突分支清空的），main() 写出前遍历 group_attribution 全部并入 protected_ids。
399:16:2. BLOCKER 源侧 TOCTOU → snapshot_file() 改 os.open(O_RDONLY|O_NOFOLLOW|O_NONBLOCK) → fstat 取 (st_dev,st_ino) + S_ISREG 门 → 从同一 fd os.read 全量，返回身份即实际读取对象，DLQ 与 compare 副本均以该身份入 protected_ids；输入 stat 失败改 exit 2 不再静默吞。
401:18:4. MEDIUM FIFO/设备 → --out 与读侧均加 S_ISREG + O_NONBLOCK。
405:22:请对每项设计静态反例判断是否仍可绕过（尤其：保护集完整性、fd 身份与实际读取的绑定、unverifiable 与 unrecoverable 的语义边界、strict decode 的边界）。同时独立复算台账仍为 92 条 / class 89-2-1 / byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0 / 重复簇 6 簇 29 行 / unparseable 0。逐项 CLOSED/NOT-CLOSED + 总裁定（可验收/仍阻断）+ 新发现分级。若已可验收请明确说明；若仍阻断请说明**对一张只读 census 卡**而言该阻断是否与卡面范围相称。
413:217:    2 BLOCKER: 全候选(含 mode 0200 不可读但可写)并入 --out 保护集; snapshot_file
416:222:    2 MEDIUM: --out 与读侧均加 S_ISREG+O_NONBLOCK 门(FIFO/设备); JSONL 逐行
422:320:  **① P1-05 第四轮返工（P1-05d）已落地，待五轮终裁** — Codex 四轮（`2026-08-19` 终裁文档）判 F-02/F-05 CLOSED、其余 STILL-OPEN；九路验证（`2026-08-20-Codex四轮终裁-九路验证与C批次方案.md`）9/9 CONFIRMED 含 B3 新回归一条。C 批全部落地：**C2**（`1683328c`：脏 last_examined 投影 None 止血 B3 新回归 · freshness 嵌套错型自愈 · 5 处 ID 切片改丢弃 · _id_ok 写侧过滤同源 · lag_seconds finite · 控制字符全拒）· **C3**（`d39983ce`：conversation_summary caller 显式传 vault 组修恒空 bug · ensure_entity_node 隔离身份拒绝复用）· **C1**（`c154a7f2`：lib 层 _resolves_outside_vault 接 LanceDB 两真实入口 open 前 · orchestrator 裸 fnmatch 换 canon + 扫描产出过 should_index 根除 hash-before-admission + realpath containment · by-node missing→404/path_rejected→422；新 test_real_entrypoint_admission.py 6 条真实入口行为锁）· **C4**（census Q2 中性化+前缀分类）。**遗留**：B4（payload 命名空间/provenance）独立轮 · TOCTOU 换链残余窗口（realpath 判定与 open 非原子，诚实登记）· P1-03/P1-04 押后
462:870:/bin/zsh -lc "rg -n 'BLOCKER|HIGH|MEDIUM|LOW|CLOSED|NOT-CLOSED|保护集|TOCTOU|UTF-8|unverifiable|unrecoverable|provenance|92|89|29' '_bmad-output/审查/codex-review-CARD-G4-9-round4.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
463:873:14:CARD-G4-9 round-4 终裁复审（静态审阅 + 只读复算，禁改任何文件）。你 round-3 裁定 4/6 CLOSED，两项 PARTIAL + 3 新发现。开发方以 commit fce0d8a2 提交整改，请只读复核这 6 项：
464:874:15:1. BLOCKER-1 绕过①（--out 指向已归因 transcript 会截断恢复源）→ 现在写出前把全部 records[].transcript_paths 的 (st_dev,st_ino) 并入 protected_ids。
465:875:16:2. BLOCKER-1 绕过②（check-then-open TOCTOU）→ 现在改 os.open(O_WRONLY|O_CREAT|O_NOFOLLOW) 不带 O_TRUNC 打开，对实际 fd 做 os.fstat 校验 inode 是否落在 protected_ids，通过后才 os.ftruncate(fd,0) 并 os.fdopen 写。请判断该顺序是否真正消除 TOCTOU，并找剩余绕过（如 O_NOFOLLOW 对中间路径组件、fd 竞争、非常规文件如 FIFO/设备）。
470:880:21:同时独立复算台账 _bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json 仍为 92 条 / class 89-2-1 / 三态 4-88-0 / 重复簇 6 簇 29 行 / 归因冲突 0 / unparseable 0。逐项 CLOSED/NOT-CLOSED + 总裁定（可验收/仍阻断）+ 任何新发现分级。若认为已可验收请明确说明。
471:884:145:rg -n \"BLOCKER-1|HIGH-3|JSONL|framing|非 dict|provenance|PARTIAL|CLOSED|NOT-CLOSED|新发现|总裁定|protected_ids|O_NOFOLLOW|os\\.walk|line_count\" '_bmad-output/审查/codex-review-CARD-G4-9-round3.md' | head -n 240
472:885:160:14:CARD-G4-9 round-3 复审（静态审阅 + 只读复算）。你 round-2 裁定 10/13 CLOSED，三项 NOT-CLOSED：BLOCKER-1（--out 守卫比 resolve 字符串，hardlink 与 case-only 别名绕过截断输入）、HIGH-1（full_body_verified 只核 sha 不核长度且排在 anomaly 分支前，anomaly 记录被判 byte_exact）、HIGH-3（chmod 000 根 exit 0 假判 unrecoverable；glob 跟随 symlink 逃逸出根）；另 3 新 LOW（full_verified 长度范围应 131-180、distribution 省略 0 值键、line_count 数 LF 与 records 的 splitlines 口径不一）。开发方以 commit 73102875 提交整改。请只读复核这 6 项是否闭合：
473:886:162:17:请：逐项 CLOSED/NOT-CLOSED（对每项设计静态反例判断是否仍可绕过，如相对路径/大小写/软硬链接组合、判定链其它入口、glob 边界）；独立复算台账仍为 92 条 / class 89-2-1 / 三态 4-88-0 / 重复簇 6 簇 29 行 / full_verified 长度 131-180；给总裁定（可验收/仍阻断）与任何新发现分级。
474:888:169:366:  **① P1-05 第四轮返工（P1-05d）已落地，待五轮终裁** — Codex 四轮（`2026-08-19` 终裁文档）判 F-02/F-05 CLOSED、其余 STILL-OPEN；九路验证（`2026-08-20-Codex四轮终裁-九路验证与C批次方案.md`）9/9 CONFIRMED 含 B3 新回归一条。C 批全部落地：**C2**（`1683328c`：脏 last_examined 投影 None 止血 B3 新回归 · freshness 嵌套错型自愈 · 5 处 ID 切片改丢弃 · _id_ok 写侧过滤同源 · lag_seconds finite · 控制字符全拒）· **C3**（`d39983ce`：conversation_summary caller 显式传 vault 组修恒空 bug · ensure_entity_node 隔离身份拒绝复用）· **C1**（`c154a7f2`：lib 层 _resolves_outside_vault 接 LanceDB 两真实入口 open 前 · orchestrator 裸 fnmatch 换 canon + 扫描产出过 should_index 根除 hash-before-admission + realpath containment · by-node missing→404/path_rejected→422；新 test_real_entrypoint_admission.py 6 条真实入口行为锁）· **C4**（census Q2 中性化+前缀分类）。**遗留**：B4（payload 命名空间/provenance）独立轮 · TOCTOU 换链残余窗口（realpath 判定与 open 非原子，诚实登记）· P1-03/P1-04 押后
476:891:173:622:-    输入文件；Codex round-1 BLOCKER-1 整改）。
477:892:174:625:+    任一输入重合即 exit 2，防 "w" 截断输入（round-1 BLOCKER-1 + round-2
481:897:182:885:+    # --out 碰撞守卫（写前）。round-2 BLOCKER-1 整改: 比较**文件身份**
482:899:186:1214: - **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
483:900:187:1215: - **BLOCKER-2（快照不原子）**：DLQ 单次 `read_bytes()`，头部 sha256/line_count 与逐条 records 派生自同一份内存字节；mtime 显式标注为 stat 参考值。
485:902:189:1227:+## §7c Codex round-2 复审整改记录（10/13 CLOSED → 剩余 3 项 + 3 新 LOW 全部整改）
486:903:190:1229:+round-2 复审确认 BLOCKER-2/3、HIGH-2、MEDIUM-1~3、LOW-1~4 共 10 项 CLOSED，并抓出 3 项**未真正闭合**（均实测复现）+ 3 条新 LOW：
487:904:191:1231:+- **BLOCKER-1 NOT-CLOSED（hardlink / case-only 别名绕过）**：原守卫比较 `resolve()` **字符串**，hardlink 指向输入、以及大小写不敏感文件系统上的 case-only 别名均绕过并截断输入。**整改**：改为比较**文件身份 `(st_dev, st_ino)`**（对已存在的 --out）+ 保留路径比较作第二道。负例实测：两种绕过均 exit 2、DLQ sha 不变。
488:905:192:1232:+- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
489:906:193:1233:+- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
492:912:201:1441:    12	    任一输入重合即 exit 2，防 "w" 截断输入（round-1 BLOCKER-1 + round-2
496:916:208:1698:   265	    # --out 碰撞守卫（写前）。round-2 BLOCKER-1 整改: 比较**文件身份**
497:919:213:1937:99:- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
498:920:214:1938:100:- **BLOCKER-2（快照不原子）**：DLQ 单次 `read_bytes()`，头部 sha256/line_count 与逐条 records 派生自同一份内存字节；mtime 显式标注为 stat 参考值。
499:921:215:1944:112:## §7c Codex round-2 复审整改记录（10/13 CLOSED → 剩余 3 项 + 3 新 LOW 全部整改）
500:922:216:1945:116:- **BLOCKER-1 NOT-CLOSED（hardlink / case-only 别名绕过）**：原守卫比较 `resolve()` **字符串**，hardlink 指向输入、以及大小写不敏感文件系统上的 case-only 别名均绕过并截断输入。**整改**：改为比较**文件身份 `(st_dev, st_ino)`**（对已存在的 --out）+ 保留路径比较作第二道。负例实测：两种绕过均 exit 2、DLQ sha 不变。
501:923:217:1946:117:- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
502:924:218:1947:118:- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
504:927:225:2139:     3	总裁定：**仍阻断 / 不可验收**。`67ccebe1` 确实冻结了交付物，92 条数字也可独立复算；但实际只有 **10/13 CLOSED**，`BLOCKER-1`、`HIGH-1`、`HIGH-3` 仍未闭合。
505:928:226:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
506:929:227:2144:     8	| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
507:930:228:2145:     9	| BLOCKER-3 | **CLOSED** | `git show 67ccebe1 --stat` 为 10 个 G4-9 文件、3384 insertions，包含脚本、报告、ledger、证据包、round-1 审查和 UAT。当前 HEAD 为 `e7a480eb`，但全部 G4-9 路径相对 `67ccebe1` diff 为空。关键 blob：script `ea370cb…`、report `ff1f71d…`、ledger `6ce5772…`。 |
508:931:229:2146:    10	| HIGH-1 | **NOT-CLOSED** | round-1 三个反例本身均已翻转为 `anomaly/FAIL → unrecoverable`；非法 64 字符非 hex 也被拒。但新增组合反例：`episode_body="abc"`、`episode_body_full="abc"`、SHA 正确、声明长度 `999`，实际得到 `inline_state=anomaly` 后仍被判 `byte_exact`。原因是 [`full_body_verified()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:99)只核 SHA，不核长度，并在 [anomaly 分支之前](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:285)被采信。这直接反驳报告“anomaly 一律 unrecoverable”。 |
509:932:230:2147:    11	| HIGH-2 | **CLOSED** | missing、显式 `null`、字面 `"None"` 不再合组；数字 `123` 与字符串 `"123"` 分离；非前缀多 token 均 `attribution_conflict=true/unrecoverable`；合法前缀组统一取最长 token。真实入口反例全部通过。 |
510:933:231:2148:    12	| HIGH-3 | **NOT-CLOSED** | 不存在根目录已 exit 2；递归唯一命中、多命中冲突、目录伪命中也通过。但“不可见”仍未闭合：存在但 `chmod 000` 的根会 exit 0 并假判 `unrecoverable`。此外 [`glob + os.path.isfile`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:134)跟随 symlink：根内 `.jsonl` symlink 指向根外 `.txt`、以及 symlink 目录逃逸到根外树，均被判唯一来源并进入 `approximate`。 |
511:934:232:2149:    13	| MEDIUM-1 | **CLOSED（原 finding）** | 已读取 `episode_body_full`，不再完全忽略该生产字段；当前 92 条为 0。其长度门问题已计入 HIGH-1。 |
512:935:233:2150:    14	| MEDIUM-2 | **CLOSED** | [报告 §6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:78)、[ledger duplicate_clusters](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:60)及逐条 `reference_time` 已落地；6 簇全部逐行对账。 |
513:936:234:2151:    15	| MEDIUM-3 | **CLOSED（声明性控制）** | ledger [`privacy`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:4)及报告 private-only 声明已落地。它是纪律标签，不是技术性防外发门。 |
514:937:235:2152:    16	| LOW-1 | **CLOSED** | token 已修为 `16948–20831`，截断记录声明长度修为 `205–8036`。 |
515:938:236:2153:    17	| LOW-2 | **CLOSED** | [`stable_key_semantics`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:5)已明确仅为冻结快照内 occurrence key，不再声称三列缺一不可。 |
516:939:237:2154:    18	| LOW-3 | **CLOSED** | 报告同时补齐 `LearningConcept.name` 与 `LearningTip.created_at` 两处修复证据。 |
517:940:238:2155:    19	| LOW-4 | **CLOSED** | [报告 §1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:28)已区分当前实证和未重新复证的历史 mountinfo，不再把历史断言冒充本轮证明。 |
519:942:243:2762:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:117:- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
521:944:245:2765:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:7:| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
522:945:246:2766:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:8:| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
523:946:247:2767:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:10:| HIGH-1 | **NOT-CLOSED** | round-1 三个反例本身均已翻转为 `anomaly/FAIL → unrecoverable`；非法 64 字符非 hex 也被拒。但新增组合反例：`episode_body="abc"`、`episode_body_full="abc"`、SHA 正确、声明长度 `999`，实际得到 `inline_state=anomaly` 后仍被判 `byte_exact`。原因是 [`full_body_verified()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:99)只核 SHA，不核长度，并在 [anomaly 分支之前](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:285)被采信。这直接反驳报告“anomaly 一律 unrecoverable”。 |
524:947:248:2768:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:12:| HIGH-3 | **NOT-CLOSED** | 不存在根目录已 exit 2；递归唯一命中、多命中冲突、目录伪命中也通过。但“不可见”仍未闭合：存在但 `chmod 000` 的根会 exit 0 并假判 `unrecoverable`。此外 [`glob + os.path.isfile`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:134)跟随 symlink：根内 `.jsonl` symlink 指向根外 `.txt`、以及 symlink 目录逃逸到根外树，均被判唯一来源并进入 `approximate`。 |
525:948:249:2769:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:14:| MEDIUM-2 | **CLOSED** | [报告 §6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:78)、[ledger duplicate_clusters](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:60)及逐条 `reference_time` 已落地；6 簇全部逐行对账。 |
526:949:250:2772:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:14:CARD-G4-9 round-3 复审（静态审阅 + 只读复算）。你 round-2 裁定 10/13 CLOSED，三项 NOT-CLOSED：BLOCKER-1（--out 守卫比 resolve 字符串，hardlink 与 case-only 别名绕过截断输入）、HIGH-1（full_body_verified 只核 sha 不核长度且排在 anomaly 分支前，anomaly 记录被判 byte_exact）、HIGH-3（chmod 000 根 exit 0 假判 unrecoverable；glob 跟随 symlink 逃逸出根）；另 3 新 LOW（full_verified 长度范围应 131-180、distribution 省略 0 值键、line_count 数 LF 与 records 的 splitlines 口径不一）。开发方以 commit 73102875 提交整改。请只读复核这 6 项是否闭合：
527:950:252:2792:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1232:+- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
529:952:254:2809:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1946:117:- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
531:954:256:2815:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
532:955:257:2816:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2144:     8	| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
533:956:258:2817:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2146:    10	| HIGH-1 | **NOT-CLOSED** | round-1 三个反例本身均已翻转为 `anomaly/FAIL → unrecoverable`；非法 64 字符非 hex 也被拒。但新增组合反例：`episode_body="abc"`、`episode_body_full="abc"`、SHA 正确、声明长度 `999`，实际得到 `inline_state=anomaly` 后仍被判 `byte_exact`。原因是 [`full_body_verified()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:99)只核 SHA，不核长度，并在 [anomaly 分支之前](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:285)被采信。这直接反驳报告“anomaly 一律 unrecoverable”。 |
534:957:259:2818:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2148:    12	| HIGH-3 | **NOT-CLOSED** | 不存在根目录已 exit 2；递归唯一命中、多命中冲突、目录伪命中也通过。但“不可见”仍未闭合：存在但 `chmod 000` 的根会 exit 0 并假判 `unrecoverable`。此外 [`glob + os.path.isfile`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:134)跟随 symlink：根内 `.jsonl` symlink 指向根外 `.txt`、以及 symlink 目录逃逸到根外树，均被判唯一来源并进入 `approximate`。 |
535:958:260:2819:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2150:    14	| MEDIUM-2 | **CLOSED** | [报告 §6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:78)、[ledger duplicate_clusters](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:60)及逐条 `reference_time` 已落地；6 簇全部逐行对账。 |
537:962:270:3483:六项均已完成静态反例审阅；高严重度结论由主审重新核对 Python 3.14 glob 实现与生产写/判定入口。数据复算 PASS，但两项路径安全仍 NOT-CLOSED。
538:963:272:3506:总裁定：**仍阻断 / 不可验收**。整改提交 `73102875fdd9837f0d60cf2ed6cf4ea7f6f8c2e5` 与当前文件字节一致，台账数字有效；但六项仅 **4 CLOSED / 2 NOT-CLOSED**。
539:964:273:3510:| BLOCKER-1 | **NOT-CLOSED / PARTIAL** | 稳定状态下，relative、`..`、case-only、既存 symlink/hardlink 组合已由 [resolve+inode 门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:265)挡住。但仍有两条绕过：① `protected_paths` 不含已被归因的 transcript，直接令 `--out=<唯一 transcript>`，脚本会先判其为恢复源，最后在 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:457)将其截断；② round-2 已指出的 TOCTOU 仍在——检查后、最终打开前将安全输出替换成指向 DLQ 的 symlink/hardlink，即可 `O_TRUNC` 输入。 |
540:965:274:3511:| HIGH-1 | **CLOSED / PASS** | [`full_body_verified()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:102)现有 SHA+严格长度门；[真实判定链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:340)在 full-body 分支前要求 `state != anomaly`。更强反例——full 本身 SHA/长度完全有效，但 inline 不符——仍落 `anomaly → unrecoverable`。无其它调用入口。 |
541:966:275:3512:| HIGH-3 | **NOT-CLOSED / PARTIAL** | 当前用户下根 `chmod 000` 会 exit 2，terminal symlink 和最终落根外的结果也被过滤。但 [`glob.glob(..., recursive=True)`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:144)在 realpath 过滤前已经递归遍历；当前 Python 3.14 的 [`glob.py`](/opt/homebrew/Cellar/python@3.14/3.14.4_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/glob.py:179)会跟随目录 symlink，并静默吞掉不可读子树错误。因此仍可越根枚举；不可读子树会造成“假唯一/假不可恢复”。此外 mode `000` 的唯一 regular transcript 仍能通过 `isfile()`，被判 `approximate`，尽管实际上不可读取。 |
542:967:276:3513:| LOW：长度范围 | **CLOSED** | 报告已改为四值 `131/142/150/180`、范围 `131–180`，[报告 §3](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:45)。 |
543:968:277:3514:| LOW：distribution 零键 | **CLOSED** | [固定 schema 生成链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:437)与 [ledger](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:43)均包含 `unexpected/anomaly/unrecoverable: 0`，并新增 inline 三态。 |
544:969:278:3515:| LOW：line_count 口径 | **CLOSED（原问题）** | header 与 records 都由同一 exact bytes、同一 `decode(...).splitlines()` 派生，[代码](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:195)不再互相矛盾；但引入了下述新 MEDIUM。 |
547:972:282:3534:所以：**冻结的 92 条 ledger 数值可采信；CARD-G4-9 生成器与整卡验收仍被 BLOCKER-1、HIGH-3 阻断。** 本轮未修改仓库或受审数据，未执行破坏性 fixture/G4-10 重放；Graphiti 工具本轮不可用。
548:973:283:3539:总裁定：**仍阻断 / 不可验收**。整改提交 `73102875fdd9837f0d60cf2ed6cf4ea7f6f8c2e5` 与当前文件字节一致，台账数字有效；但六项仅 **4 CLOSED / 2 NOT-CLOSED**。
549:974:284:3543:| BLOCKER-1 | **NOT-CLOSED / PARTIAL** | 稳定状态下，relative、`..`、case-only、既存 symlink/hardlink 组合已由 [resolve+inode 门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:265)挡住。但仍有两条绕过：① `protected_paths` 不含已被归因的 transcript，直接令 `--out=<唯一 transcript>`，脚本会先判其为恢复源，最后在 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:457)将其截断；② round-2 已指出的 TOCTOU 仍在——检查后、最终打开前将安全输出替换成指向 DLQ 的 symlink/hardlink，即可 `O_TRUNC` 输入。 |
550:975:285:3544:| HIGH-1 | **CLOSED / PASS** | [`full_body_verified()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:102)现有 SHA+严格长度门；[真实判定链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:340)在 full-body 分支前要求 `state != anomaly`。更强反例——full 本身 SHA/长度完全有效，但 inline 不符——仍落 `anomaly → unrecoverable`。无其它调用入口。 |
551:976:286:3545:| HIGH-3 | **NOT-CLOSED / PARTIAL** | 当前用户下根 `chmod 000` 会 exit 2，terminal symlink 和最终落根外的结果也被过滤。但 [`glob.glob(..., recursive=True)`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:144)在 realpath 过滤前已经递归遍历；当前 Python 3.14 的 [`glob.py`](/opt/homebrew/Cellar/python@3.14/3.14.4_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/glob.py:179)会跟随目录 symlink，并静默吞掉不可读子树错误。因此仍可越根枚举；不可读子树会造成“假唯一/假不可恢复”。此外 mode `000` 的唯一 regular transcript 仍能通过 `isfile()`，被判 `approximate`，尽管实际上不可读取。 |
552:977:287:3546:| LOW：长度范围 | **CLOSED** | 报告已改为四值 `131/142/150/180`、范围 `131–180`，[报告 §3](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:45)。 |
553:978:288:3547:| LOW：distribution 零键 | **CLOSED** | [固定 schema 生成链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:437)与 [ledger](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:43)均包含 `unexpected/anomaly/unrecoverable: 0`，并新增 inline 三态。 |
554:979:289:3548:| LOW：line_count 口径 | **CLOSED（原问题）** | header 与 records 都由同一 exact bytes、同一 `decode(...).splitlines()` 派生，[代码](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:195)不再互相矛盾；但引入了下述新 MEDIUM。 |
557:982:293:3567:所以：**冻结的 92 条 ledger 数值可采信；CARD-G4-9 生成器与整卡验收仍被 BLOCKER-1、HIGH-3 阻断。** 本轮未修改仓库或受审数据，未执行破坏性 fixture/G4-10 重放；Graphiti 工具本轮不可用。
558:984:313:+## §7d Codex round-3 复审整改记录（4/6 CLOSED → 剩 2 项 + 3 新发现全部整改）
559:985:315:+round-3 确认 HIGH-1 与三条 LOW 已 CLOSED、台账数字有效且与 commit 字节一致，两项路径安全判 PARTIAL：
560:986:317:+- **BLOCKER-1 残留两条绕过**：① `protected_paths` 未含**归因到的 transcript**，`--out=<唯一 transcript>` 会截断恢复源；② check-then-open 的 **TOCTOU** 仍在（检查后、打开前把 --out 换成指向 DLQ 的链接）。**整改**：① 写出前把全部 `transcript_paths` 并入保护集；② 改 `os.open(O_WRONLY|O_CREAT|O_NOFOLLOW)` **不带 O_TRUNC** 打开 → 对**实际 fd** `fstat` 校验 inode → 通过才 `ftruncate`，检查与写入作用于同一 fd，替换攻击无效。反例实测：`--out` 指向唯一 transcript → exit 2、transcript sha 不变。
568:1000:442:     # --out 碰撞守卫（写前）。round-2 BLOCKER-1 整改: 比较**文件身份**
569:1002:455:     # BLOCKER-2 整改: 单次读取，records 与头部描述共享同一份 exact bytes
571:1004:480:+    # round-3 BLOCKER-1 绕过① 整改: 归因到的 transcript 是恢复源，
574:1013:573:    12	    任一输入重合即 exit 2，防 "w" 截断输入（round-1 BLOCKER-1 + round-2
575:1014:576:    15	快照原子性（Codex round-1 BLOCKER-2 整改）:
584:1046:865:   304	    # --out 碰撞守卫（写前）。round-2 BLOCKER-1 整改: 比较**文件身份**
585:1048:897:   336	    # BLOCKER-2 整改: 单次读取，records 与头部描述共享同一份 exact bytes
589:1063:1062:   501	    # round-3 BLOCKER-1 绕过① 整改: 归因到的 transcript 是恢复源，
596:1089:1206:    94	| 负例门（round-1 整改自证） | `--out`==`--dlq` → exit 2 拒写、DLQ 完好；transcripts 根缺失 → exit 2 拒诊；sha 匹配但长度不符（round-1 HIGH-1 反例①）→ anomaly/unrecoverable；坏 JSON 行/空行 → unparseable 逐行入台账不拒诊 |
597:1091:1211:    99	- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
598:1092:1212:   100	- **BLOCKER-2（快照不原子）**：DLQ 单次 `read_bytes()`，头部 sha256/line_count 与逐条 records 派生自同一份内存字节；mtime 显式标注为 stat 参考值。
599:1093:1213:   101	- **BLOCKER-3（交付物未冻结漂移）**：以本卡 commit 冻结全部交付物 exact bytes（脚本/报告/台账/证据包同 commit）；grep-selfattest 已按最终版行号重生成并内嵌脚本 sha 前缀。
607:1102:1224:   112	## §7c Codex round-2 复审整改记录（10/13 CLOSED → 剩余 3 项 + 3 新 LOW 全部整改）
608:1103:1226:   114	round-2 复审确认 BLOCKER-2/3、HIGH-2、MEDIUM-1~3、LOW-1~4 共 10 项 CLOSED，并抓出 3 项**未真正闭合**（均实测复现）+ 3 条新 LOW：
609:1104:1228:   116	- **BLOCKER-1 NOT-CLOSED（hardlink / case-only 别名绕过）**：原守卫比较 `resolve()` **字符串**，hardlink 指向输入、以及大小写不敏感文件系统上的 case-only 别名均绕过并截断输入。**整改**：改为比较**文件身份 `(st_dev, st_ino)`**（对已存在的 --out）+ 保留路径比较作第二道。负例实测：两种绕过均 exit 2、DLQ sha 不变。
610:1105:1229:   117	- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
611:1106:1230:   118	- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
613:1110:1250:   138	## §7d Codex round-3 复审整改记录（4/6 CLOSED → 剩 2 项 + 3 新发现全部整改）
614:1111:1252:   140	round-3 确认 HIGH-1 与三条 LOW 已 CLOSED、台账数字有效且与 commit 字节一致，两项路径安全判 PARTIAL：
615:1112:1254:   142	- **BLOCKER-1 残留两条绕过**：① `protected_paths` 未含**归因到的 transcript**，`--out=<唯一 transcript>` 会截断恢复源；② check-then-open 的 **TOCTOU** 仍在（检查后、打开前把 --out 换成指向 DLQ 的链接）。**整改**：① 写出前把全部 `transcript_paths` 并入保护集；② 改 `os.open(O_WRONLY|O_CREAT|O_NOFOLLOW)` **不带 O_TRUNC** 打开 → 对**实际 fd** `fstat` 校验 inode → 通过才 `ftruncate`，检查与写入作用于同一 fd，替换攻击无效。反例实测：`--out` 指向唯一 transcript → exit 2、transcript sha 不变。
623:1132:1420:   501	    # round-3 BLOCKER-1 绕过① 整改: 归因到的 transcript 是恢复源，
626:1138:1491:    G4-9(4/6→6/6): transcript 并入 --out 保护集(防截断恢复源)、O_NOFOLLOW+
633:1169:1954:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:138:## §7d Codex round-3 复审整改记录（4/6 CLOSED → 剩 2 项 + 3 新发现全部整改）
634:1170:1955:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:140:round-3 确认 HIGH-1 与三条 LOW 已 CLOSED、台账数字有效且与 commit 字节一致，两项路径安全判 PARTIAL：
635:1171:1956:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:142:- **BLOCKER-1 残留两条绕过**：① `protected_paths` 未含**归因到的 transcript**，`--out=<唯一 transcript>` 会截断恢复源；② check-then-open 的 **TOCTOU** 仍在（检查后、打开前把 --out 换成指向 DLQ 的链接）。**整改**：① 写出前把全部 `transcript_paths` 并入保护集；② 改 `os.open(O_WRONLY|O_CREAT|O_NOFOLLOW)` **不带 O_TRUNC** 打开 → 对**实际 fd** `fstat` 校验 inode → 通过才 `ftruncate`，检查与写入作用于同一 fd，替换攻击无效。反例实测：`--out` 指向唯一 transcript → exit 2、transcript sha 不变。
642:1213:2301:总裁定：**仍阻断 / 不可验收**。六项仅 **1/6 CLOSED**。冻结台账的数字本身可采信，但生成器仍存在可截断恢复源的 BLOCKER，不能据此接受 CARD‑G4‑9。
643:1214:2305:| 1. transcript 纳入保护集 | **NOT-CLOSED / PARTIAL** | 稳定状态下，[保护循环](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:503)确实覆盖当前 89 个路径引用、7 个唯一 inode。但不可读候选会在 [180–186](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:180)清空 `transcript_paths`，因此不进入保护集。owner mode `0200` 的匹配 transcript 不可读但可写，`--out` 指向它时仍能在 [517–529](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:517)被截断；无需竞态。另 `stat` 失败被 [直接吞掉](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:506)，也不是“全部并入”的 fail-closed 实现。 |
644:1215:2306:| 2. fd 上校验 TOCTOU | **NOT-CLOSED / PARTIAL** | `open` 不带 `O_TRUNC`，随后同一 fd 上 `fstat→ftruncate`，确实封住了最终组件换链及稳定 protected inode/hardlink；外部进程不能重新绑定本进程 fd，未发现 fd-number 竞争。但源身份早在 [312–317](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:312)按路径采集，DLQ 到 [337](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:337)才读取。静态调度 `protected=A → 将 inode B 换入 DLQ → snapshot 读取 B → --out hardlink B → fstat 不命中 A → truncate B` 仍可截断本次实际读取源。`O_NOFOLLOW` 也只保护最终组件；中间 symlink 可重定向至未保护对象。 |
645:1216:2307:| 3. HIGH-3 枚举 | **NOT-CLOSED** | 稳态目录 symlink、`scandir` 错误和 mode `000` 门已有改善。但 unreadable/walk error 设置 conflict 后，主链仍在 [395–397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:395)明确产出 `recoverability=unrecoverable`，直接反驳报告所称“既不宣称不可恢复” [报告:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:143)。此外 `os.walk.onerror` 只覆盖 `scandir`；逐条 `is_dir/stat` 错误可被静默当非候选，[islink→isfile→access→realpath](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:168)仍是路径级竞态。 |
646:1217:2308:| 4. JSONL framing | **NOT-CLOSED / PARTIAL** | U+2028、裸 CR 误分帧已修，header 与 records 共用 helper。但 [`_split_jsonl_lines()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:76)有 `b"\n" → []`，把一条非法空白行静默算成零行；`decode(errors="replace")` 还会把非法 UTF‑8 `b'{"a":"\\xff"}\n'` 改写成合法对象而非 unparseable。 |
647:1218:2309:| 5. 非 dict JSON | **CLOSED** | [`isinstance(rec, dict)` 门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:351)位于任何 `.get()` 和 `records.append()` 前；`null`、数组、标量均进入 `unparseable`。 |
648:1219:2310:| 6. provenance | **NOT-CLOSED（LOW）** | Git 实际 ancestry 与三个受审 blob 均能绑定到 `fce0d8a2`；但[报告头](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:5)只写 `67ccebe1 → 73102875 → 本次 round-3 整改 commit`，没有字面 `fce0d8a2`。由于 commit 不能自包含自身 SHA，需用后置 receipt/tag/manifest 明确绑定，不能以模糊代称冒充精确三段链。 |
649:1220:2314:- **BLOCKER**：不可读但可写 transcript 可绕过保护集并被截断。
650:1221:2315:- **BLOCKER**：protected source identity 与实际读取对象未绑定，源侧 TOCTOU 仍在。
657:1232:2338:总裁定：**仍阻断 / 不可验收**。六项仅 **1/6 CLOSED**。冻结台账的数字本身可采信，但生成器仍存在可截断恢复源的 BLOCKER，不能据此接受 CARD‑G4‑9。
658:1233:2342:| 1. transcript 纳入保护集 | **NOT-CLOSED / PARTIAL** | 稳定状态下，[保护循环](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:503)确实覆盖当前 89 个路径引用、7 个唯一 inode。但不可读候选会在 [180–186](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:180)清空 `transcript_paths`，因此不进入保护集。owner mode `0200` 的匹配 transcript 不可读但可写，`--out` 指向它时仍能在 [517–529](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:517)被截断；无需竞态。另 `stat` 失败被 [直接吞掉](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:506)，也不是“全部并入”的 fail-closed 实现。 |
659:1234:2343:| 2. fd 上校验 TOCTOU | **NOT-CLOSED / PARTIAL** | `open` 不带 `O_TRUNC`，随后同一 fd 上 `fstat→ftruncate`，确实封住了最终组件换链及稳定 protected inode/hardlink；外部进程不能重新绑定本进程 fd，未发现 fd-number 竞争。但源身份早在 [312–317](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:312)按路径采集，DLQ 到 [337](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:337)才读取。静态调度 `protected=A → 将 inode B 换入 DLQ → snapshot 读取 B → --out hardlink B → fstat 不命中 A → truncate B` 仍可截断本次实际读取源。`O_NOFOLLOW` 也只保护最终组件；中间 symlink 可重定向至未保护对象。 |
660:1235:2344:| 3. HIGH-3 枚举 | **NOT-CLOSED** | 稳态目录 symlink、`scandir` 错误和 mode `000` 门已有改善。但 unreadable/walk error 设置 conflict 后，主链仍在 [395–397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:395)明确产出 `recoverability=unrecoverable`，直接反驳报告所称“既不宣称不可恢复” [报告:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:143)。此外 `os.walk.onerror` 只覆盖 `scandir`；逐条 `is_dir/stat` 错误可被静默当非候选，[islink→isfile→access→realpath](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:168)仍是路径级竞态。 |
661:1236:2345:| 4. JSONL framing | **NOT-CLOSED / PARTIAL** | U+2028、裸 CR 误分帧已修，header 与 records 共用 helper。但 [`_split_jsonl_lines()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:76)有 `b"\n" → []`，把一条非法空白行静默算成零行；`decode(errors="replace")` 还会把非法 UTF‑8 `b'{"a":"\\xff"}\n'` 改写成合法对象而非 unparseable。 |
662:1237:2346:| 5. 非 dict JSON | **CLOSED** | [`isinstance(rec, dict)` 门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:351)位于任何 `.get()` 和 `records.append()` 前；`null`、数组、标量均进入 `unparseable`。 |
663:1238:2347:| 6. provenance | **NOT-CLOSED（LOW）** | Git 实际 ancestry 与三个受审 blob 均能绑定到 `fce0d8a2`；但[报告头](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:5)只写 `67ccebe1 → 73102875 → 本次 round-3 整改 commit`，没有字面 `fce0d8a2`。由于 commit 不能自包含自身 SHA，需用后置 receipt/tag/manifest 明确绑定，不能以模糊代称冒充精确三段链。 |
664:1239:2351:- **BLOCKER**：不可读但可写 transcript 可绕过保护集并被截断。
665:1240:2352:- **BLOCKER**：protected source identity 与实际读取对象未绑定，源侧 TOCTOU 仍在。
685:1349:| 负例门（round-1 整改自证） | `--out`==`--dlq` → exit 2 拒写、DLQ 完好；transcripts 根缺失 → exit 2 拒诊；sha 匹配但长度不符（round-1 HIGH-1 反例①）→ anomaly/unrecoverable；坏 JSON 行/空行 → unparseable 逐行入台账不拒诊 |
687:1354:- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
688:1355:- **BLOCKER-2（快照不原子）**：DLQ 单次 `read_bytes()`，头部 sha256/line_count 与逐条 records 派生自同一份内存字节；mtime 显式标注为 stat 参考值。
689:1356:- **BLOCKER-3（交付物未冻结漂移）**：以本卡 commit 冻结全部交付物 exact bytes（脚本/报告/台账/证据包同 commit）；grep-selfattest 已按最终版行号重生成并内嵌脚本 sha 前缀。
697:1367:## §7c Codex round-2 复审整改记录（10/13 CLOSED → 剩余 3 项 + 3 新 LOW 全部整改）
698:1369:round-2 复审确认 BLOCKER-2/3、HIGH-2、MEDIUM-1~3、LOW-1~4 共 10 项 CLOSED，并抓出 3 项**未真正闭合**（均实测复现）+ 3 条新 LOW：
699:1371:- **BLOCKER-1 NOT-CLOSED（hardlink / case-only 别名绕过）**：原守卫比较 `resolve()` **字符串**，hardlink 指向输入、以及大小写不敏感文件系统上的 case-only 别名均绕过并截断输入。**整改**：改为比较**文件身份 `(st_dev, st_ino)`**（对已存在的 --out）+ 保留路径比较作第二道。负例实测：两种绕过均 exit 2、DLQ sha 不变。
700:1372:- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
701:1373:- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
704:1393:## §7d Codex round-3 复审整改记录（4/6 CLOSED → 剩 2 项 + 3 新发现全部整改）
705:1395:round-3 确认 HIGH-1 与三条 LOW 已 CLOSED、台账数字有效且与 commit 字节一致，两项路径安全判 PARTIAL：
706:1397:- **BLOCKER-1 残留两条绕过**：① `protected_paths` 未含**归因到的 transcript**，`--out=<唯一 transcript>` 会截断恢复源；② check-then-open 的 **TOCTOU** 仍在（检查后、打开前把 --out 换成指向 DLQ 的链接）。**整改**：① 写出前把全部 `transcript_paths` 并入保护集；② 改 `os.open(O_WRONLY|O_CREAT|O_NOFOLLOW)` **不带 O_TRUNC** 打开 → 对**实际 fd** `fstat` 校验 inode → 通过才 `ftruncate`，检查与写入作用于同一 fd，替换攻击无效。反例实测：`--out` 指向唯一 transcript → exit 2、transcript sha 不变。
711:1405:## §7e Codex round-4 复审整改记录（1/6 CLOSED → 全部 9 项整改）
712:1407:round-4 只认可 1 项 CLOSED（非 dict JSON 门），并用更深的静态反例推翻了另外 5 项的"闭合"，另提 2 BLOCKER / 1 HIGH / 2 MEDIUM / 3 LOW。逐条整改（全部实测复现→封死）：
713:1409:- **BLOCKER①（不可读但可写的 transcript 绕过保护集）**：mode `0200` 的候选在 unreadable 分支被清空 `transcript_paths`，因此不进保护集，`--out` 指向它仍被截断（无需竞态）。**整改**：新增 `all_candidate_paths` 保留**所有见到的候选**（含不可读、含被冲突分支清空的），写出前全部并入保护集。实测：mode 0200 候选作 `--out` → exit 2、文件字节不变。
714:1410:- **BLOCKER②（源侧 TOCTOU）**：保护身份按**路径** stat 采集、DLQ 稍后才按路径读取，两步间可换入另一 inode → 实际读取对象不在保护集。**整改**：`snapshot_file()` 改为 `os.open(O_RDONLY|O_NOFOLLOW|O_NONBLOCK)` → `fstat` 取身份 + regular-file 门 → **从同一 fd 读全量**，返回的身份即**实际被读取对象**；compare 副本同样以读取身份入保护集；输入 `stat` 失败不再静默吞而是 exit 2。
716:1412:- **MEDIUM（FIFO/设备节点）**：`--out` 缺 regular-file gate 与 `O_NONBLOCK`。**整改**：`O_NONBLOCK` + `S_ISREG` 双门（读侧同样）。实测：FIFO 作 `--out` → exit 2 且不阻塞。
721:1448:CARD-G4-9 round-5 终裁复审（静态审阅 + 只读复算，禁改任何文件）。你 round-4 裁定 1/6 CLOSED，提出 2 BLOCKER / 1 HIGH / 2 MEDIUM / 3 LOW。开发方以 commit d2827a6d + d8d887f2 提交整改，请逐条只读复核：
722:1449:1. BLOCKER 不可读但可写 transcript 绕过保护集 → resolve_group_attribution 新增 all_candidate_paths（保留所有见到的候选，含 unreadable 与被冲突分支清空的），main() 写出前遍历 group_attribution 全部并入 protected_ids。
723:1450:2. BLOCKER 源侧 TOCTOU → snapshot_file() 改 os.open(O_RDONLY|O_NOFOLLOW|O_NONBLOCK) → fstat 取 (st_dev,st_ino) + S_ISREG 门 → 从同一 fd os.read 全量，返回身份即实际读取对象，DLQ 与 compare 副本均以该身份入 protected_ids；输入 stat 失败改 exit 2 不再静默吞。
725:1452:4. MEDIUM FIFO/设备 → --out 与读侧均加 S_ISREG + O_NONBLOCK。
729:1456:请对每项设计静态反例判断是否仍可绕过（尤其：保护集完整性、fd 身份与实际读取的绑定、unverifiable 与 unrecoverable 的语义边界、strict decode 的边界）。同时独立复算台账仍为 92 条 / class 89-2-1 / byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0 / 重复簇 6 簇 29 行 / unparseable 0。逐项 CLOSED/NOT-CLOSED + 总裁定（可验收/仍阻断）+ 新发现分级。若已可验收请明确说明；若仍阻断请说明**对一张只读 census 卡**而言该阻断是否与卡面范围相称。
737:1689:   265	    round-4 BLOCKER② 整改: 原实现按路径 stat 采集保护身份、稍后才按路径读取，
740:1778:   354	    # --out 碰撞守卫（写前）。round-2 BLOCKER-1 整改: 比较**文件身份**
741:1814:   388	    # BLOCKER-2 整改: 单次读取，records 与头部描述共享同一份 exact bytes
747:2027:   597	    # round-3 BLOCKER-1 绕过① 整改: 归因到的 transcript 是恢复源，
752:2107:    12	    任一输入重合即 exit 2，防 "w" 截断输入（round-1 BLOCKER-1 + round-2
753:2110:    15	快照原子性（Codex round-1 BLOCKER-2 整改）:
763:2258:   163	        # round-4 BLOCKER① 整改: 保护集必须覆盖**所有见到的候选**（含不可读、
765:2281:/bin/zsh -lc "rg -n '不可读但可写|源侧 TOCTOU|不可见终态|非法 UTF-8|字段错型|root_prefix|fchmod|provenance|总裁定|BLOCKER' '_bmad-output/审查/codex-review-CARD-G4-9-round4.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
766:2283:15:1. BLOCKER-1 绕过①（--out 指向已归因 transcript 会截断恢复源）→ 现在写出前把全部 records[].transcript_paths 的 (st_dev,st_ino) 并入 protected_ids。
767:2284:16:2. BLOCKER-1 绕过②（check-then-open TOCTOU）→ 现在改 os.open(O_WRONLY|O_CREAT|O_NOFOLLOW) 不带 O_TRUNC 打开，对实际 fd 做 os.fstat 校验 inode 是否落在 protected_ids，通过后才 os.ftruncate(fd,0) 并 os.fdopen 写。请判断该顺序是否真正消除 TOCTOU，并找剩余绕过（如 O_NOFOLLOW 对中间路径组件、fd 竞争、非常规文件如 FIFO/设备）。
769:2286:21:同时独立复算台账 _bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json 仍为 92 条 / class 89-2-1 / 三态 4-88-0 / 重复簇 6 簇 29 行 / 归因冲突 0 / unparseable 0。逐项 CLOSED/NOT-CLOSED + 总裁定（可验收/仍阻断）+ 任何新发现分级。若认为已可验收请明确说明。
770:2288:145:rg -n \"BLOCKER-1|HIGH-3|JSONL|framing|非 dict|provenance|PARTIAL|CLOSED|NOT-CLOSED|新发现|总裁定|protected_ids|O_NOFOLLOW|os\\.walk|line_count\" '_bmad-output/审查/codex-review-CARD-G4-9-round3.md' | head -n 240
771:2289:160:14:CARD-G4-9 round-3 复审（静态审阅 + 只读复算）。你 round-2 裁定 10/13 CLOSED，三项 NOT-CLOSED：BLOCKER-1（--out 守卫比 resolve 字符串，hardlink 与 case-only 别名绕过截断输入）、HIGH-1（full_body_verified 只核 sha 不核长度且排在 anomaly 分支前，anomaly 记录被判 byte_exact）、HIGH-3（chmod 000 根 exit 0 假判 unrecoverable；glob 跟随 symlink 逃逸出根）；另 3 新 LOW（full_verified 长度范围应 131-180、distribution 省略 0 值键、line_count 数 LF 与 records 的 splitlines 口径不一）。开发方以 commit 73102875 提交整改。请只读复核这 6 项是否闭合：
772:2290:162:17:请：逐项 CLOSED/NOT-CLOSED（对每项设计静态反例判断是否仍可绕过，如相对路径/大小写/软硬链接组合、判定链其它入口、glob 边界）；独立复算台账仍为 92 条 / class 89-2-1 / 三态 4-88-0 / 重复簇 6 簇 29 行 / full_verified 长度 131-180；给总裁定（可验收/仍阻断）与任何新发现分级。
773:2292:168:151:  • 交叉核验高严重度项并给出逐项与总裁定
774:2293:169:366:  **① P1-05 第四轮返工（P1-05d）已落地，待五轮终裁** — Codex 四轮（`2026-08-19` 终裁文档）判 F-02/F-05 CLOSED、其余 STILL-OPEN；九路验证（`2026-08-20-Codex四轮终裁-九路验证与C批次方案.md`）9/9 CONFIRMED 含 B3 新回归一条。C 批全部落地：**C2**（`1683328c`：脏 last_examined 投影 None 止血 B3 新回归 · freshness 嵌套错型自愈 · 5 处 ID 切片改丢弃 · _id_ok 写侧过滤同源 · lag_seconds finite · 控制字符全拒）· **C3**（`d39983ce`：conversation_summary caller 显式传 vault 组修恒空 bug · ensure_entity_node 隔离身份拒绝复用）· **C1**（`c154a7f2`：lib 层 _resolves_outside_vault 接 LanceDB 两真实入口 open 前 · orchestrator 裸 fnmatch 换 canon + 扫描产出过 should_index 根除 hash-before-admission + realpath containment · by-node missing→404/path_rejected→422；新 test_real_entrypoint_admission.py 6 条真实入口行为锁）· **C4**（census Q2 中性化+前缀分类）。**遗留**：B4（payload 命名空间/provenance）独立轮 · TOCTOU 换链残余窗口（realpath 判定与 open 非原子，诚实登记）· P1-03/P1-04 押后
775:2295:173:622:-    输入文件；Codex round-1 BLOCKER-1 整改）。
776:2296:174:625:+    任一输入重合即 exit 2，防 "w" 截断输入（round-1 BLOCKER-1 + round-2
777:2297:182:885:+    # --out 碰撞守卫（写前）。round-2 BLOCKER-1 整改: 比较**文件身份**
778:2298:186:1214: - **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
779:2299:187:1215: - **BLOCKER-2（快照不原子）**：DLQ 单次 `read_bytes()`，头部 sha256/line_count 与逐条 records 派生自同一份内存字节；mtime 显式标注为 stat 参考值。
780:2300:190:1229:+round-2 复审确认 BLOCKER-2/3、HIGH-2、MEDIUM-1~3、LOW-1~4 共 10 项 CLOSED，并抓出 3 项**未真正闭合**（均实测复现）+ 3 条新 LOW：
781:2301:191:1231:+- **BLOCKER-1 NOT-CLOSED（hardlink / case-only 别名绕过）**：原守卫比较 `resolve()` **字符串**，hardlink 指向输入、以及大小写不敏感文件系统上的 case-only 别名均绕过并截断输入。**整改**：改为比较**文件身份 `(st_dev, st_ino)`**（对已存在的 --out）+ 保留路径比较作第二道。负例实测：两种绕过均 exit 2、DLQ sha 不变。
782:2303:201:1441:    12	    任一输入重合即 exit 2，防 "w" 截断输入（round-1 BLOCKER-1 + round-2
783:2304:208:1698:   265	    # --out 碰撞守卫（写前）。round-2 BLOCKER-1 整改: 比较**文件身份**
784:2305:213:1937:99:- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
785:2306:214:1938:100:- **BLOCKER-2（快照不原子）**：DLQ 单次 `read_bytes()`，头部 sha256/line_count 与逐条 records 派生自同一份内存字节；mtime 显式标注为 stat 参考值。
786:2307:216:1945:116:- **BLOCKER-1 NOT-CLOSED（hardlink / case-only 别名绕过）**：原守卫比较 `resolve()` **字符串**，hardlink 指向输入、以及大小写不敏感文件系统上的 case-only 别名均绕过并截断输入。**整改**：改为比较**文件身份 `(st_dev, st_ino)`**（对已存在的 --out）+ 保留路径比较作第二道。负例实测：两种绕过均 exit 2、DLQ sha 不变。
787:2308:224:2137:     1	> **存档说明**: codex exec 完成审查后被 cyber 误拦（exit 1，重定向文件空——MEMORY 已录 codex 三坑之一）。本文件由 task stdout 抢救提取，内容为 Codex round-2 原文（自"总裁定"起至结论段止），未作任何改写。
788:2309:225:2139:     3	总裁定：**仍阻断 / 不可验收**。`67ccebe1` 确实冻结了交付物，92 条数字也可独立复算；但实际只有 **10/13 CLOSED**，`BLOCKER-1`、`HIGH-1`、`HIGH-3` 仍未闭合。
789:2310:226:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
790:2311:227:2144:     8	| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
791:2312:228:2145:     9	| BLOCKER-3 | **CLOSED** | `git show 67ccebe1 --stat` 为 10 个 G4-9 文件、3384 insertions，包含脚本、报告、ledger、证据包、round-1 审查和 UAT。当前 HEAD 为 `e7a480eb`，但全部 G4-9 路径相对 `67ccebe1` diff 为空。关键 blob：script `ea370cb…`、report `ff1f71d…`、ledger `6ce5772…`。 |
792:2313:245:2765:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:7:| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
793:2314:246:2766:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:8:| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
794:2315:250:2772:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:14:CARD-G4-9 round-3 复审（静态审阅 + 只读复算）。你 round-2 裁定 10/13 CLOSED，三项 NOT-CLOSED：BLOCKER-1（--out 守卫比 resolve 字符串，hardlink 与 case-only 别名绕过截断输入）、HIGH-1（full_body_verified 只核 sha 不核长度且排在 anomaly 分支前，anomaly 记录被判 byte_exact）、HIGH-3（chmod 000 根 exit 0 假判 unrecoverable；glob 跟随 symlink 逃逸出根）；另 3 新 LOW（full_verified 长度范围应 131-180、distribution 省略 0 值键、line_count 数 LF 与 records 的 splitlines 口径不一）。开发方以 commit 73102875 提交整改。请只读复核这 6 项是否闭合：
795:2316:256:2815:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
796:2317:257:2816:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2144:     8	| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
797:2319:265:3127:  • 交叉核验高严重度项并给出逐项与总裁定
798:2321:271:3487:  ✓ 交叉核验高严重度项并给出逐项与总裁定
799:2322:272:3506:总裁定：**仍阻断 / 不可验收**。整改提交 `73102875fdd9837f0d60cf2ed6cf4ea7f6f8c2e5` 与当前文件字节一致，台账数字有效；但六项仅 **4 CLOSED / 2 NOT-CLOSED**。
800:2323:273:3510:| BLOCKER-1 | **NOT-CLOSED / PARTIAL** | 稳定状态下，relative、`..`、case-only、既存 symlink/hardlink 组合已由 [resolve+inode 门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:265)挡住。但仍有两条绕过：① `protected_paths` 不含已被归因的 transcript，直接令 `--out=<唯一 transcript>`，脚本会先判其为恢复源，最后在 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:457)将其截断；② round-2 已指出的 TOCTOU 仍在——检查后、最终打开前将安全输出替换成指向 DLQ 的 symlink/hardlink，即可 `O_TRUNC` 输入。 |
802:2325:282:3534:所以：**冻结的 92 条 ledger 数值可采信；CARD-G4-9 生成器与整卡验收仍被 BLOCKER-1、HIGH-3 阻断。** 本轮未修改仓库或受审数据，未执行破坏性 fixture/G4-10 重放；Graphiti 工具本轮不可用。
803:2326:283:3539:总裁定：**仍阻断 / 不可验收**。整改提交 `73102875fdd9837f0d60cf2ed6cf4ea7f6f8c2e5` 与当前文件字节一致，台账数字有效；但六项仅 **4 CLOSED / 2 NOT-CLOSED**。
804:2327:284:3543:| BLOCKER-1 | **NOT-CLOSED / PARTIAL** | 稳定状态下，relative、`..`、case-only、既存 symlink/hardlink 组合已由 [resolve+inode 门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:265)挡住。但仍有两条绕过：① `protected_paths` 不含已被归因的 transcript，直接令 `--out=<唯一 transcript>`，脚本会先判其为恢复源，最后在 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:457)将其截断；② round-2 已指出的 TOCTOU 仍在——检查后、最终打开前将安全输出替换成指向 DLQ 的 symlink/hardlink，即可 `O_TRUNC` 输入。 |
806:2329:293:3567:所以：**冻结的 92 条 ledger 数值可采信；CARD-G4-9 生成器与整卡验收仍被 BLOCKER-1、HIGH-3 阻断。** 本轮未修改仓库或受审数据，未执行破坏性 fixture/G4-10 重放；Graphiti 工具本轮不可用。
807:2330:317:+- **BLOCKER-1 残留两条绕过**：① `protected_paths` 未含**归因到的 transcript**，`--out=<唯一 transcript>` 会截断恢复源；② check-then-open 的 **TOCTOU** 仍在（检查后、打开前把 --out 换成指向 DLQ 的链接）。**整改**：① 写出前把全部 `transcript_paths` 并入保护集；② 改 `os.open(O_WRONLY|O_CREAT|O_NOFOLLOW)` **不带 O_TRUNC** 打开 → 对**实际 fd** `fstat` 校验 inode → 通过才 `ftruncate`，检查与写入作用于同一 fd，替换攻击无效。反例实测：`--out` 指向唯一 transcript → exit 2、transcript sha 不变。
809:2332:442:     # --out 碰撞守卫（写前）。round-2 BLOCKER-1 整改: 比较**文件身份**
810:2333:455:     # BLOCKER-2 整改: 单次读取，records 与头部描述共享同一份 exact bytes
811:2334:480:+    # round-3 BLOCKER-1 绕过① 整改: 归因到的 transcript 是恢复源，
812:2335:573:    12	    任一输入重合即 exit 2，防 "w" 截断输入（round-1 BLOCKER-1 + round-2
813:2336:576:    15	快照原子性（Codex round-1 BLOCKER-2 整改）:
814:2337:865:   304	    # --out 碰撞守卫（写前）。round-2 BLOCKER-1 整改: 比较**文件身份**
815:2338:897:   336	    # BLOCKER-2 整改: 单次读取，records 与头部描述共享同一份 exact bytes
816:2339:1062:   501	    # round-3 BLOCKER-1 绕过① 整改: 归因到的 transcript 是恢复源，
817:2340:1211:    99	- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
818:2341:1212:   100	- **BLOCKER-2（快照不原子）**：DLQ 单次 `read_bytes()`，头部 sha256/line_count 与逐条 records 派生自同一份内存字节；mtime 显式标注为 stat 参考值。
819:2342:1213:   101	- **BLOCKER-3（交付物未冻结漂移）**：以本卡 commit 冻结全部交付物 exact bytes（脚本/报告/台账/证据包同 commit）；grep-selfattest 已按最终版行号重生成并内嵌脚本 sha 前缀。
820:2343:1226:   114	round-2 复审确认 BLOCKER-2/3、HIGH-2、MEDIUM-1~3、LOW-1~4 共 10 项 CLOSED，并抓出 3 项**未真正闭合**（均实测复现）+ 3 条新 LOW：
821:2344:1228:   116	- **BLOCKER-1 NOT-CLOSED（hardlink / case-only 别名绕过）**：原守卫比较 `resolve()` **字符串**，hardlink 指向输入、以及大小写不敏感文件系统上的 case-only 别名均绕过并截断输入。**整改**：改为比较**文件身份 `(st_dev, st_ino)`**（对已存在的 --out）+ 保留路径比较作第二道。负例实测：两种绕过均 exit 2、DLQ sha 不变。
822:2345:1254:   142	- **BLOCKER-1 残留两条绕过**：① `protected_paths` 未含**归因到的 transcript**，`--out=<唯一 transcript>` 会截断恢复源；② check-then-open 的 **TOCTOU** 仍在（检查后、打开前把 --out 换成指向 DLQ 的链接）。**整改**：① 写出前把全部 `transcript_paths` 并入保护集；② 改 `os.open(O_WRONLY|O_CREAT|O_NOFOLLOW)` **不带 O_TRUNC** 打开 → 对**实际 fd** `fstat` 校验 inode → 通过才 `ftruncate`，检查与写入作用于同一 fd，替换攻击无效。反例实测：`--out` 指向唯一 transcript → exit 2、transcript sha 不变。
824:2347:1420:   501	    # round-3 BLOCKER-1 绕过① 整改: 归因到的 transcript 是恢复源，
825:2349:1956:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:142:- **BLOCKER-1 残留两条绕过**：① `protected_paths` 未含**归因到的 transcript**，`--out=<唯一 transcript>` 会截断恢复源；② check-then-open 的 **TOCTOU** 仍在（检查后、打开前把 --out 换成指向 DLQ 的链接）。**整改**：① 写出前把全部 `transcript_paths` 并入保护集；② 改 `os.open(O_WRONLY|O_CREAT|O_NOFOLLOW)` **不带 O_TRUNC** 打开 → 对**实际 fd** `fstat` 校验 inode → 通过才 `ftruncate`，检查与写入作用于同一 fd，替换攻击无效。反例实测：`--out` 指向唯一 transcript → exit 2、transcript sha 不变。
826:2354:2301:总裁定：**仍阻断 / 不可验收**。六项仅 **1/6 CLOSED**。冻结台账的数字本身可采信，但生成器仍存在可截断恢复源的 BLOCKER，不能据此接受 CARD‑G4‑9。
827:2355:2305:| 1. transcript 纳入保护集 | **NOT-CLOSED / PARTIAL** | 稳定状态下，[保护循环](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:503)确实覆盖当前 89 个路径引用、7 个唯一 inode。但不可读候选会在 [180–186](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:180)清空 `transcript_paths`，因此不进入保护集。owner mode `0200` 的匹配 transcript 不可读但可写，`--out` 指向它时仍能在 [517–529](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:517)被截断；无需竞态。另 `stat` 失败被 [直接吞掉](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:506)，也不是“全部并入”的 fail-closed 实现。 |
828:2356:2310:| 6. provenance | **NOT-CLOSED（LOW）** | Git 实际 ancestry 与三个受审 blob 均能绑定到 `fce0d8a2`；但[报告头](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:5)只写 `67ccebe1 → 73102875 → 本次 round-3 整改 commit`，没有字面 `fce0d8a2`。由于 commit 不能自包含自身 SHA，需用后置 receipt/tag/manifest 明确绑定，不能以模糊代称冒充精确三段链。 |
829:2357:2314:- **BLOCKER**：不可读但可写 transcript 可绕过保护集并被截断。
830:2358:2315:- **BLOCKER**：protected source identity 与实际读取对象未绑定，源侧 TOCTOU 仍在。
832:2360:2338:总裁定：**仍阻断 / 不可验收**。六项仅 **1/6 CLOSED**。冻结台账的数字本身可采信，但生成器仍存在可截断恢复源的 BLOCKER，不能据此接受 CARD‑G4‑9。
833:2361:2342:| 1. transcript 纳入保护集 | **NOT-CLOSED / PARTIAL** | 稳定状态下，[保护循环](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:503)确实覆盖当前 89 个路径引用、7 个唯一 inode。但不可读候选会在 [180–186](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:180)清空 `transcript_paths`，因此不进入保护集。owner mode `0200` 的匹配 transcript 不可读但可写，`--out` 指向它时仍能在 [517–529](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:517)被截断；无需竞态。另 `stat` 失败被 [直接吞掉](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:506)，也不是“全部并入”的 fail-closed 实现。 |
834:2362:2347:| 6. provenance | **NOT-CLOSED（LOW）** | Git 实际 ancestry 与三个受审 blob 均能绑定到 `fce0d8a2`；但[报告头](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:5)只写 `67ccebe1 → 73102875 → 本次 round-3 整改 commit`，没有字面 `fce0d8a2`。由于 commit 不能自包含自身 SHA，需用后置 receipt/tag/manifest 明确绑定，不能以模糊代称冒充精确三段链。 |
835:2363:2351:- **BLOCKER**：不可读但可写 transcript 可绕过保护集并被截断。
836:2364:2352:- **BLOCKER**：protected source identity 与实际读取对象未绑定，源侧 TOCTOU 仍在。
838:2382:  2301	总裁定：**仍阻断 / 不可验收**。六项仅 **1/6 CLOSED**。冻结台账的数字本身可采信，但生成器仍存在可截断恢复源的 BLOCKER，不能据此接受 CARD‑G4‑9。
839:2386:  2305	| 1. transcript 纳入保护集 | **NOT-CLOSED / PARTIAL** | 稳定状态下，[保护循环](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:503)确实覆盖当前 89 个路径引用、7 个唯一 inode。但不可读候选会在 [180–186](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:180)清空 `transcript_paths`，因此不进入保护集。owner mode `0200` 的匹配 transcript 不可读但可写，`--out` 指向它时仍能在 [517–529](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:517)被截断；无需竞态。另 `stat` 失败被 [直接吞掉](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:506)，也不是“全部并入”的 fail-closed 实现。 |
840:2387:  2306	| 2. fd 上校验 TOCTOU | **NOT-CLOSED / PARTIAL** | `open` 不带 `O_TRUNC`，随后同一 fd 上 `fstat→ftruncate`，确实封住了最终组件换链及稳定 protected inode/hardlink；外部进程不能重新绑定本进程 fd，未发现 fd-number 竞争。但源身份早在 [312–317](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:312)按路径采集，DLQ 到 [337](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:337)才读取。静态调度 `protected=A → 将 inode B 换入 DLQ → snapshot 读取 B → --out hardlink B → fstat 不命中 A → truncate B` 仍可截断本次实际读取源。`O_NOFOLLOW` 也只保护最终组件；中间 symlink 可重定向至未保护对象。 |
841:2388:  2307	| 3. HIGH-3 枚举 | **NOT-CLOSED** | 稳态目录 symlink、`scandir` 错误和 mode `000` 门已有改善。但 unreadable/walk error 设置 conflict 后，主链仍在 [395–397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:395)明确产出 `recoverability=unrecoverable`，直接反驳报告所称“既不宣称不可恢复” [报告:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:143)。此外 `os.walk.onerror` 只覆盖 `scandir`；逐条 `is_dir/stat` 错误可被静默当非候选，[islink→isfile→access→realpath](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:168)仍是路径级竞态。 |
842:2389:  2308	| 4. JSONL framing | **NOT-CLOSED / PARTIAL** | U+2028、裸 CR 误分帧已修，header 与 records 共用 helper。但 [`_split_jsonl_lines()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:76)有 `b"\n" → []`，把一条非法空白行静默算成零行；`decode(errors="replace")` 还会把非法 UTF‑8 `b'{"a":"\\xff"}\n'` 改写成合法对象而非 unparseable。 |
843:2390:  2309	| 5. 非 dict JSON | **CLOSED** | [`isinstance(rec, dict)` 门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:351)位于任何 `.get()` 和 `records.append()` 前；`null`、数组、标量均进入 `unparseable`。 |
844:2391:  2310	| 6. provenance | **NOT-CLOSED（LOW）** | Git 实际 ancestry 与三个受审 blob 均能绑定到 `fce0d8a2`；但[报告头](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:5)只写 `67ccebe1 → 73102875 → 本次 round-3 整改 commit`，没有字面 `fce0d8a2`。由于 commit 不能自包含自身 SHA，需用后置 receipt/tag/manifest 明确绑定，不能以模糊代称冒充精确三段链。 |
845:2395:  2314	- **BLOCKER**：不可读但可写 transcript 可绕过保护集并被截断。
846:2396:  2315	- **BLOCKER**：protected source identity 与实际读取对象未绑定，源侧 TOCTOU 仍在。
853:2419:  2338	总裁定：**仍阻断 / 不可验收**。六项仅 **1/6 CLOSED**。冻结台账的数字本身可采信，但生成器仍存在可截断恢复源的 BLOCKER，不能据此接受 CARD‑G4‑9。
854:2423:  2342	| 1. transcript 纳入保护集 | **NOT-CLOSED / PARTIAL** | 稳定状态下，[保护循环](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:503)确实覆盖当前 89 个路径引用、7 个唯一 inode。但不可读候选会在 [180–186](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:180)清空 `transcript_paths`，因此不进入保护集。owner mode `0200` 的匹配 transcript 不可读但可写，`--out` 指向它时仍能在 [517–529](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:517)被截断；无需竞态。另 `stat` 失败被 [直接吞掉](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:506)，也不是“全部并入”的 fail-closed 实现。 |
855:2424:  2343	| 2. fd 上校验 TOCTOU | **NOT-CLOSED / PARTIAL** | `open` 不带 `O_TRUNC`，随后同一 fd 上 `fstat→ftruncate`，确实封住了最终组件换链及稳定 protected inode/hardlink；外部进程不能重新绑定本进程 fd，未发现 fd-number 竞争。但源身份早在 [312–317](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:312)按路径采集，DLQ 到 [337](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:337)才读取。静态调度 `protected=A → 将 inode B 换入 DLQ → snapshot 读取 B → --out hardlink B → fstat 不命中 A → truncate B` 仍可截断本次实际读取源。`O_NOFOLLOW` 也只保护最终组件；中间 symlink 可重定向至未保护对象。 |
856:2425:  2344	| 3. HIGH-3 枚举 | **NOT-CLOSED** | 稳态目录 symlink、`scandir` 错误和 mode `000` 门已有改善。但 unreadable/walk error 设置 conflict 后，主链仍在 [395–397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:395)明确产出 `recoverability=unrecoverable`，直接反驳报告所称“既不宣称不可恢复” [报告:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:143)。此外 `os.walk.onerror` 只覆盖 `scandir`；逐条 `is_dir/stat` 错误可被静默当非候选，[islink→isfile→access→realpath](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:168)仍是路径级竞态。 |
857:2426:  2345	| 4. JSONL framing | **NOT-CLOSED / PARTIAL** | U+2028、裸 CR 误分帧已修，header 与 records 共用 helper。但 [`_split_jsonl_lines()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:76)有 `b"\n" → []`，把一条非法空白行静默算成零行；`decode(errors="replace")` 还会把非法 UTF‑8 `b'{"a":"\\xff"}\n'` 改写成合法对象而非 unparseable。 |
858:2427:  2346	| 5. 非 dict JSON | **CLOSED** | [`isinstance(rec, dict)` 门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:351)位于任何 `.get()` 和 `records.append()` 前；`null`、数组、标量均进入 `unparseable`。 |
859:2428:  2347	| 6. provenance | **NOT-CLOSED（LOW）** | Git 实际 ancestry 与三个受审 blob 均能绑定到 `fce0d8a2`；但[报告头](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:5)只写 `67ccebe1 → 73102875 → 本次 round-3 整改 commit`，没有字面 `fce0d8a2`。由于 commit 不能自包含自身 SHA，需用后置 receipt/tag/manifest 明确绑定，不能以模糊代称冒充精确三段链。 |
860:2432:  2351	- **BLOCKER**：不可读但可写 transcript 可绕过保护集并被截断。
861:2433:  2352	- **BLOCKER**：protected source identity 与实际读取对象未绑定，源侧 TOCTOU 仍在。
870:2968:35:| Codex 独立审查 round-1 | **BLOCKED**（3 BLOCKER：--out 可截断输入 / 快照不原子 / 交付物未冻结；3 HIGH：inline 判定 fail-open / request_id 归因传染 / transcript 归因折叠；3 MEDIUM + 4 LOW。同时确认：**当前 92 条数字逐项 0 mismatch**、class/三态/家族计数全对） | `_bmad-output/审查/codex-review-CARD-G4-9.md` |
871:2969:37:| Codex 复审 round-2 | **仍阻断**（10/13 CLOSED；BLOCKER-1/HIGH-1/HIGH-3 未真正闭合 + 3 新 LOW）。同时独立复算确认：67ccebe1 冻结生效、92 条数字与 6/29 重复簇全部可复算 | `_bmad-output/审查/codex-review-CARD-G4-9-round2.md`（codex 被 cyber 误拦，内容由 stdout 抢救存档） |
876:2977:73:- **BLOCKER-1 仍 PARTIAL**：① 保护集漏了**归因到的 transcript**——`--out` 指向它会截断恢复源；② check-then-open 的 **TOCTOU** 仍在。→ ① transcript 写前并入保护集；② 改 `O_NOFOLLOW` 打开且**不带 O_TRUNC**，对实际 fd `fstat` 校验后才 `ftruncate`。反例实测：exit 2、transcript 完好。
880:3071:   151	## §7e Codex round-4 复审整改记录（1/6 CLOSED → 全部 9 项整改）
881:3073:   153	round-4 只认可 1 项 CLOSED（非 dict JSON 门），并用更深的静态反例推翻了另外 5 项的"闭合"，另提 2 BLOCKER / 1 HIGH / 2 MEDIUM / 3 LOW。逐条整改（全部实测复现→封死）：
882:3075:   155	- **BLOCKER①（不可读但可写的 transcript 绕过保护集）**：mode `0200` 的候选在 unreadable 分支被清空 `transcript_paths`，因此不进保护集，`--out` 指向它仍被截断（无需竞态）。**整改**：新增 `all_candidate_paths` 保留**所有见到的候选**（含不可读、含被冲突分支清空的），写出前全部并入保护集。实测：mode 0200 候选作 `--out` → exit 2、文件字节不变。
883:3076:   156	- **BLOCKER②（源侧 TOCTOU）**：保护身份按**路径** stat 采集、DLQ 稍后才按路径读取，两步间可换入另一 inode → 实际读取对象不在保护集。**整改**：`snapshot_file()` 改为 `os.open(O_RDONLY|O_NOFOLLOW|O_NONBLOCK)` → `fstat` 取身份 + regular-file 门 → **从同一 fd 读全量**，返回的身份即**实际被读取对象**；compare 副本同样以读取身份入保护集；输入 `stat` 失败不再静默吞而是 exit 2。
885:3078:   158	- **MEDIUM（FIFO/设备节点）**：`--out` 缺 regular-file gate 与 `O_NONBLOCK`。**整改**：`O_NONBLOCK` + `S_ISREG` 双门（读侧同样）。实测：FIFO 作 `--out` → exit 2 且不阻塞。
889:3111:    35	| Codex 独立审查 round-1 | **BLOCKED**（3 BLOCKER：--out 可截断输入 / 快照不原子 / 交付物未冻结；3 HIGH：inline 判定 fail-open / request_id 归因传染 / transcript 归因折叠；3 MEDIUM + 4 LOW。同时确认：**当前 92 条数字逐项 0 mismatch**、class/三态/家族计数全对） | `_bmad-output/审查/codex-review-CARD-G4-9.md` |
890:3113:    37	| Codex 复审 round-2 | **仍阻断**（10/13 CLOSED；BLOCKER-1/HIGH-1/HIGH-3 未真正闭合 + 3 新 LOW）。同时独立复算确认：67ccebe1 冻结生效、92 条数字与 6/29 重复簇全部可复算 | `_bmad-output/审查/codex-review-CARD-G4-9-round2.md`（codex 被 cyber 误拦，内容由 stdout 抢救存档） |
892:3115:    39	| Codex 复审 round-3 | **仍阻断**（4/6 CLOSED；BLOCKER-1/HIGH-3 判 PARTIAL + 1 新 MEDIUM + 2 新 LOW）。同时确认：HIGH-1 与三条 LOW 已闭合、台账数字有效且与 commit 字节一致 | `_bmad-output/审查/codex-review-CARD-G4-9-round3.md` |
894:3117:    41	| Codex 复审 round-4 | **仍阻断**（1/6 CLOSED；2 新 BLOCKER + 1 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round4.md` |
900:3332:总裁定：**仍阻断 / CARD-G4-9 不可验收**。  
902:3339:| 1. transcript 全候选保护 | **NOT-CLOSED · BLOCKER** | 多 token 非前缀一致时在扫描前直接返回，[script:168](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:168)，此时 `all_candidate_paths=[]`。同一 `request_id` 含 `session:aaaaa`、`session:bbbbb`，`--out` 指向 `aaaaa….jsonl`，不会进入 [保护循环:599](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:599)，最终仍可在 [ftruncate:639](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:639)截断。无需竞态。不可列举但可穿越的子目录也有同类绕过；后置 transcript `stat` 失败仍被 `continue` 吞掉。 |
903:3340:| 2. 源侧 fd 身份绑定 | **NOT-CLOSED / PARTIAL · BLOCKER** | DLQ/compare 的狭义修复已 CLOSED：同一 fd `open→fstat→read→identity`，[snapshot:262](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:262)、[DLQ:389](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:389)、[compare:542](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:542)。但 `qa_metrics_db` 仍是早期 path-stat、稍后 SQLite 按路径重新打开，[probe:233](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:233)。可令 stat 看到 inode A、SQLite 实际读取换入的 B、`--out` 为 B 的 hardlink，最终 B 不在保护集并被截断。 |
904:3341:| 3. `unverifiable` 四态 | **NOT-CLOSED · HIGH** | distribution/list 同步已实现。但 `anomaly→unrecoverable` 位于 conflict 判断之前，[script:464](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:464)：`anomaly + 扫描受阻/不可读/归因冲突` 仍被假终态化。另无 token 时未扫描即返回，truncated 记录随后被称为“无在盘源”，也应是 `unverifiable`。 |
905:3342:| 4. FIFO/设备门 | **NOT-CLOSED / PARTIAL · MEDIUM** | DLQ、compare、`--out` 的 `O_NONBLOCK + S_ISREG` 已 CLOSED，[读侧:269](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:269)、[写侧:620](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:620)。但 QA DB 读侧仍直接进入 SQLite，无 regular-file/nonblocking 门，FIFO 仍可能阻塞。 |
906:3343:| 5. 非法 UTF-8 | **CLOSED（原项）** | 逐 LF frame strict decode，并在调用方归 `unparseable`，[splitter:77](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:77)、[caller:399](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:399)。只读验证坏字节得到 1 frame + decode error。 |
907:3344:| 6a. 三个指定字段错型 | **CLOSED** | `name`、不可哈希 `request_id`、非字符串 `episode_body` 均不再炸全量，[name:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:143)、[request_id:423](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:423)、[body:111](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:111)。 |
908:3345:| 6b. 根 `/` containment | **CLOSED** | `root_prefix` 对 `/` 保持 `/`，非根补尾斜杠，[script:203](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:203)。 |
909:3346:| 6c. 既有输出 `fchmod 0600` | **NOT-CLOSED · HIGH** | `fchmod` 在 protected-inode 拒绝之前，[script:630](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:630)。`--out` 指向已保护的 `0644` transcript 时，会先把源权限改成 `0600`，再发现碰撞并 exit 2。字节虽未截断，但只读输入已被修改。 |
910:3347:| 7. provenance receipt | **CLOSED（仓库内）** | 报告头已指向 receipt，[report:5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:5)；receipt 链与 Git ancestry 一致，[receipt:4](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt:4)。LOW 限制：记录的是当前仓库内唯一可解析的 8-hex 缩写，不是独立于仓库的完整 40-hex OID。 |
912:3362:### 新发现/残留边界
913:3364:- **BLOCKER**：token-conflict 扫描前早退，仍可无竞态截断 transcript。
914:3365:- **BLOCKER**：QA DB 实际读取身份未绑定。
917:3368:- **LOW**：单独 `b"\n"` 仍被算作 0 行；escaped lone surrogate 可借 `errors="replace"` 构造 `full_verified`；`episode_body_length=True/1.0` 也可通过长度门。
918:3377:总裁定：**仍阻断 / CARD-G4-9 不可验收**。  
920:3384:| 1. transcript 全候选保护 | **NOT-CLOSED · BLOCKER** | 多 token 非前缀一致时在扫描前直接返回，[script:168](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:168)，此时 `all_candidate_paths=[]`。同一 `request_id` 含 `session:aaaaa`、`session:bbbbb`，`--out` 指向 `aaaaa….jsonl`，不会进入 [保护循环:599](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:599)，最终仍可在 [ftruncate:639](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:639)截断。无需竞态。不可列举但可穿越的子目录也有同类绕过；后置 transcript `stat` 失败仍被 `continue` 吞掉。 |
921:3385:| 2. 源侧 fd 身份绑定 | **NOT-CLOSED / PARTIAL · BLOCKER** | DLQ/compare 的狭义修复已 CLOSED：同一 fd `open→fstat→read→identity`，[snapshot:262](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:262)、[DLQ:389](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:389)、[compare:542](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:542)。但 `qa_metrics_db` 仍是早期 path-stat、稍后 SQLite 按路径重新打开，[probe:233](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:233)。可令 stat 看到 inode A、SQLite 实际读取换入的 B、`--out` 为 B 的 hardlink，最终 B 不在保护集并被截断。 |
922:3386:| 3. `unverifiable` 四态 | **NOT-CLOSED · HIGH** | distribution/list 同步已实现。但 `anomaly→unrecoverable` 位于 conflict 判断之前，[script:464](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:464)：`anomaly + 扫描受阻/不可读/归因冲突` 仍被假终态化。另无 token 时未扫描即返回，truncated 记录随后被称为“无在盘源”，也应是 `unverifiable`。 |
923:3387:| 4. FIFO/设备门 | **NOT-CLOSED / PARTIAL · MEDIUM** | DLQ、compare、`--out` 的 `O_NONBLOCK + S_ISREG` 已 CLOSED，[读侧:269](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:269)、[写侧:620](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:620)。但 QA DB 读侧仍直接进入 SQLite，无 regular-file/nonblocking 门，FIFO 仍可能阻塞。 |
924:3388:| 5. 非法 UTF-8 | **CLOSED（原项）** | 逐 LF frame strict decode，并在调用方归 `unparseable`，[splitter:77](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:77)、[caller:399](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:399)。只读验证坏字节得到 1 frame + decode error。 |
925:3389:| 6a. 三个指定字段错型 | **CLOSED** | `name`、不可哈希 `request_id`、非字符串 `episode_body` 均不再炸全量，[name:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:143)、[request_id:423](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:423)、[body:111](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:111)。 |
926:3390:| 6b. 根 `/` containment | **CLOSED** | `root_prefix` 对 `/` 保持 `/`，非根补尾斜杠，[script:203](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:203)。 |
927:3391:| 6c. 既有输出 `fchmod 0600` | **NOT-CLOSED · HIGH** | `fchmod` 在 protected-inode 拒绝之前，[script:630](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:630)。`--out` 指向已保护的 `0644` transcript 时，会先把源权限改成 `0600`，再发现碰撞并 exit 2。字节虽未截断，但只读输入已被修改。 |
928:3392:| 7. provenance receipt | **CLOSED（仓库内）** | 报告头已指向 receipt，[report:5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:5)；receipt 链与 Git ancestry 一致，[receipt:4](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt:4)。LOW 限制：记录的是当前仓库内唯一可解析的 8-hex 缩写，不是独立于仓库的完整 40-hex OID。 |
930:3407:### 新发现/残留边界
931:3409:- **BLOCKER**：token-conflict 扫描前早退，仍可无竞态截断 transcript。
932:3410:- **BLOCKER**：QA DB 实际读取身份未绑定。
935:3413:- **LOW**：单独 `b"\n"` 仍被算作 0 行；escaped lone surrogate 可借 `errors="replace"` 构造 `full_verified`；`episode_body_length=True/1.0` 也可通过长度门。
951:   - 唯一写出口是 --out 台账 JSON，写前双重碰撞守卫：resolve() 路径比较 +
953:     任一输入重合即 exit 2，防 "w" 截断输入（round-1 BLOCKER-1 + round-2
956: 快照原子性（Codex round-1 BLOCKER-2 整改）:
1066:+    # round-5 LOW 整改: errors="replace" 会把 JSON escaped lone surrogate
1122:+    round-5 BLOCKER① 整改: **先扫描后判定**。原实现在 token 冲突/无 token 时
1123:+    扫描前早退，导致这些候选从未进入 all_candidate_paths → 不进 --out 保护集
1133:-        # round-4 BLOCKER① 整改: 保护集必须覆盖**所有见到的候选**（含不可读、
1135:-        # 不进保护集，--out 指向它仍会被截断。
1222:+        result["no_token"] = True
1263:+    round-5 BLOCKER②/MEDIUM 整改: 原实现按路径 stat 取身份、SQLite 稍后按路径
1324:     round-4 BLOCKER② 整改: 原实现按路径 stat 采集保护身份、稍后才按路径读取，
1358:     """返回 (描述, 实际读取对象身份)；身份用于并入 --out 保护集。"""
1388:     ap.add_argument("--out", default=None, help="台账 JSON 输出路径（省略则打 stdout）")
1402:                     f"--out 与输入文件为同一 inode（hardlink/大小写别名），拒绝写出（防截断）: {out_path}",
1407:     # BLOCKER-2 整改: 单次读取，records 与头部描述共享同一份 exact bytes
1503:+            if sess.get("no_token"):
1643:     # round-3 BLOCKER-1 绕过① 整改: 归因到的 transcript 是恢复源，
1644:     # --out 指向它同样会截断。写出前并入保护集（此时归因已完成）。
1672:             print(f"--out 无法安全打开（symlink 或权限）: {args.out} ({e})", file=sys.stderr)
1678:                 print(f"--out 不是常规文件（FIFO/设备/socket），拒绝写出: {args.out}", file=sys.stderr)
1683:+            # round-5 HIGH 整改: 碰撞检查必须**先于** fchmod —— 否则 --out 指向
1687:                     f"--out 打开后经 fstat 判定与输入文件同一 inode，拒绝写出（防截断）: {args.out}",
1757:   360	    """返回 (描述, 实际读取对象身份)；身份用于并入 --out 保护集。"""
1787:   390	    ap.add_argument("--out", default=None, help="台账 JSON 输出路径（省略则打 stdout）")
1812:   415	    # --out 碰撞守卫（写前）。round-2 BLOCKER-1 整改: 比较**文件身份**
1831:   434	            print(f"--out 与输入文件路径重合，拒绝写出（防截断）: {out_resolved}", file=sys.stderr)
1837:   440	                print(f"--out 无法 stat，拒绝写出: {out_path} ({e})", file=sys.stderr)
1841:   444	                    f"--out 与输入文件为同一 inode（hardlink/大小写别名），拒绝写出（防截断）: {out_path}",
1846:   449	    # BLOCKER-2 整改: 单次读取，records 与头部描述共享同一份 exact bytes
1925:   528	            if sess.get("no_token"):
2058:   661	    # round-3 BLOCKER-1 绕过① 整改: 归因到的 transcript 是恢复源，
2059:   662	    # --out 指向它同样会截断。写出前并入保护集（此时归因已完成）。
2085:   688	            print(f"--out 无法安全打开（symlink 或权限）: {args.out} ({e})", file=sys.stderr)
2091:   694	                print(f"--out 不是常规文件（FIFO/设备/socket），拒绝写出: {args.out}", file=sys.stderr)
2093:   696	            # round-5 HIGH 整改: 碰撞检查必须**先于** fchmod —— 否则 --out 指向
2097:   700	                    f"--out 打开后经 fstat 判定与输入文件同一 inode，拒绝写出（防截断）: {args.out}",
2187:   121	    # round-5 LOW 整改: errors="replace" 会把 JSON escaped lone surrogate
2239:   173	    round-5 BLOCKER① 整改: **先扫描后判定**。原实现在 token 冲突/无 token 时
2240:   174	    扫描前早退，导致这些候选从未进入 all_candidate_paths → 不进 --out 保护集
2297:   231	        result["no_token"] = True
2333:   267	    round-5 BLOCKER②/MEDIUM 整改: 原实现按路径 stat 取身份、SQLite 稍后按路径
2392:   326	    round-4 BLOCKER② 整改: 原实现按路径 stat 采集保护身份、稍后才按路径读取，
2398:**Analyzing SQLite ABA race vulnerability**
2422:初步静态路径已锁定：八项声明大多确实落在生产脚本，而不是只改报告。不过 QA DB 的实现存在一个关键待证点——验证 fd 在 SQLite 按路径打开前已关闭，且“身份变化拒绝”目前只是探针 verdict，主流程仍继续写出；我正在用实际控制流判断这是否仍留下原 BLOCKER 的截断路径。同时也在检查 transcript 扫描失败是否真的会阻止写出，而不只是改成 `unverifiable`。
2426:/bin/zsh -lc "rg -n -C 3 '92|89|byte_exact|approximate|unverifiable|unrecoverable|重复簇|归因冲突|no_token|callout_annotation|只读|零写入|qa_metrics|transcript' _bmad-output/审查/G4-9-DLQ-census-2026-08-28.md" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
2591:92-| grep 自证（import 行全 stdlib；neo4j/graphiti/bolt/app. import 0 命中；`--apply` 定义 0 命中；写模式 open 仅 `--out` 1 处且受路径碰撞守卫保护） | **PASS**（`grep-selfattest.txt`，含守卫在位证明） |
2594:95:| 负例门（round-1 整改自证） | `--out`==`--dlq` → exit 2 拒写、DLQ 完好；transcripts 根缺失 → exit 2 拒诊；sha 匹配但长度不符（round-1 HIGH-1 反例①）→ anomaly/unrecoverable；坏 JSON 行/空行 → unparseable 逐行入台账不拒诊 |
2595:96:| 负例门（round-2 整改自证） | **hardlink** 指向 DLQ 的 --out → exit 2 + DLQ sha 不变；**case-only 别名**（`DLQ.jsonl`）→ exit 2 + DLQ 完好；**anomaly + episode_body_full 组合**（sha 对但长度 999）→ anomaly/unrecoverable（不再翻案 byte_exact）；**chmod 000 根** → exit 2 拒诊；**symlink 逃逸**（根内 .jsonl → 根外 .txt）→ match_count=0/unrecoverable；正例回归：真实唯一命中仍 approximate |
2599:100-- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
2600:101-- **BLOCKER-2（快照不原子）**：DLQ 单次 `read_bytes()`，头部 sha256/line_count 与逐条 records 派生自同一份内存字节；mtime 显式标注为 stat 参考值。
2601:102-- **BLOCKER-3（交付物未冻结漂移）**：以本卡 commit 冻结全部交付物 exact bytes（脚本/报告/台账/证据包同 commit）；grep-selfattest 已按最终版行号重生成并内嵌脚本 sha 前缀。
2612:113-## §7c Codex round-2 复审整改记录（10/13 CLOSED → 剩余 3 项 + 3 新 LOW 全部整改）
2614:115-round-2 复审确认 BLOCKER-2/3、HIGH-2、MEDIUM-1~3、LOW-1~4 共 10 项 CLOSED，并抓出 3 项**未真正闭合**（均实测复现）+ 3 条新 LOW：
2616:117-- **BLOCKER-1 NOT-CLOSED（hardlink / case-only 别名绕过）**：原守卫比较 `resolve()` **字符串**，hardlink 指向输入、以及大小写不敏感文件系统上的 case-only 别名均绕过并截断输入。**整改**：改为比较**文件身份 `(st_dev, st_ino)`**（对已存在的 --out）+ 保留路径比较作第二道。负例实测：两种绕过均 exit 2、DLQ sha 不变。
2617:118:- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
2618:119:- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
2635:141-round-3 确认 HIGH-1 与三条 LOW 已 CLOSED、台账数字有效且与 commit 字节一致，两项路径安全判 PARTIAL：
2637:143:- **BLOCKER-1 残留两条绕过**：① `protected_paths` 未含**归因到的 transcript**，`--out=<唯一 transcript>` 会截断恢复源；② check-then-open 的 **TOCTOU** 仍在（检查后、打开前把 --out 换成指向 DLQ 的链接）。**整改**：① 写出前把全部 `transcript_paths` 并入保护集；② 改 `os.open(O_WRONLY|O_CREAT|O_NOFOLLOW)` **不带 O_TRUNC** 打开 → 对**实际 fd** `fstat` 校验 inode → 通过才 `ftruncate`，检查与写入作用于同一 fd，替换攻击无效。反例实测：`--out` 指向唯一 transcript → exit 2、transcript sha 不变。
2645:151-## §7e Codex round-4 复审整改记录（1/6 CLOSED → 全部 9 项整改）
2647:153-round-4 只认可 1 项 CLOSED（非 dict JSON 门），并用更深的静态反例推翻了另外 5 项的"闭合"，另提 2 BLOCKER / 1 HIGH / 2 MEDIUM / 3 LOW。逐条整改（全部实测复现→封死）：
2649:155:- **BLOCKER①（不可读但可写的 transcript 绕过保护集）**：mode `0200` 的候选在 unreadable 分支被清空 `transcript_paths`，因此不进保护集，`--out` 指向它仍被截断（无需竞态）。**整改**：新增 `all_candidate_paths` 保留**所有见到的候选**（含不可读、含被冲突分支清空的），写出前全部并入保护集。实测：mode 0200 候选作 `--out` → exit 2、文件字节不变。
2650:156-- **BLOCKER②（源侧 TOCTOU）**：保护身份按**路径** stat 采集、DLQ 稍后才按路径读取，两步间可换入另一 inode → 实际读取对象不在保护集。**整改**：`snapshot_file()` 改为 `os.open(O_RDONLY|O_NOFOLLOW|O_NONBLOCK)` → `fstat` 取身份 + regular-file 门 → **从同一 fd 读全量**，返回的身份即**实际被读取对象**；compare 副本同样以读取身份入保护集；输入 `stat` 失败不再静默吞而是 exit 2。
2652:158-- **MEDIUM（FIFO/设备节点）**：`--out` 缺 regular-file gate 与 `O_NONBLOCK`。**整改**：`O_NONBLOCK` + `S_ISREG` 双门（读侧同样）。实测：FIFO 作 `--out` → exit 2 且不阻塞。
2659:165-## §7f Codex round-5 复审整改记录（3/8 CLOSED → 9 项全部整改）
2661:167-round-5 用更深的静态反例继续推翻"闭合"，提出 2 BLOCKER / 2 HIGH / 2 MEDIUM / 3 LOW，逐条整改并实测：
2663:169:- **BLOCKER①（token 冲突/无 token 时扫描前早退 → 候选不进保护集）**：`--out` 指向冲突组的候选 transcript 仍可无竞态截断。**整改**：`resolve_group_attribution()` 重写为**先扫描后判定**——无条件为每个 token 扫描收集候选进 `all_candidate_paths`（保护集口径），再做冲突/唯一性判定；候选 `stat` 失败不再 `continue` 吞掉而是 exit 2（保护集不完整即拒绝写出）。实测：冲突候选作 `--out` → exit 2、文件 sha 不变。
2664:170:- **BLOCKER②（qa_metrics.db 身份未绑定实际读取）**：仍是早期 path-stat + SQLite 稍后按路径重开。**整改**：`probe_qa_metrics()` 改 `os.open(O_RDONLY|O_NOFOLLOW|O_NONBLOCK)` 取 fstat 身份 + `S_ISREG` 门 → SQLite 打开后**复核路径身份仍等于该身份**，不等即 `identity_changed_..._refused`；身份入保护集。本次运行 `file_identity_verified: true`。
2666:172:- **HIGH②（`fchmod` 先于 protected-id 检查）**：`--out` 指向受保护的 0644 输入时，会**先把只读输入权限改成 0600** 再拒绝——字节没截断但输入已被修改。**整改**：碰撞检查前移到 `fchmod` 之前。实测：mode 644 → 644 不变。
2667:173-- **MEDIUM（QA DB 无特殊文件门）**：随 BLOCKER② 一并加 `S_ISREG` + `O_NONBLOCK`。
2668:174:- **MEDIUM（无 token 未扫描即判不可恢复）**：改为 `unverifiable` + `no_token` 标记（见 HIGH①）。
2669:175-- **LOW ×3**：单独 `b"\n"` 现算 1 个空行（实测 `line_count=1`）；`errors="replace"` 改 **strict encode**（JSON escaped lone surrogate 不能再构造假 `full_verified`）；`bool` 是 `int` 子类 —— `episode_body_length=True` 现被长度门拒绝（实测判 anomaly）。
2671:177:**归因冲突计数由 0 变为 3（如实说明）**：round-5 起"名字不含 session token"被诚实标记为 `no_token`（未做归因扫描），命中的正是 3 条 `callout_annotation` 记录。它们 inline 正文全量、sha 对账通过，**不依赖 transcript**，故仍判 `byte_exact`——三态分布不变（4/88/0/0），88 条 approximate 仍全部为唯一 transcript 命中。这是标注口径变诚实，不是结论变化。
2676:/bin/zsh -lc "rg -n -C 3 '92|89|byte_exact|approximate|unverifiable|unrecoverable|重复簇|归因冲突|no_token|callout_annotation|只读|零写入|qa_metrics|transcript|写入' _bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
2703:28:| 脚本只读自证（判据 a） | import 行全 stdlib；neo4j/graphiti/bolt/app. import **0 命中**；`--apply` 定义 **0 命中**；写模式 open 仅台账 `--out` 1 处 | `G4-9-evidence/grep-selfattest.txt` |
2710:35:| Codex 独立审查 round-1 | **BLOCKED**（3 BLOCKER：--out 可截断输入 / 快照不原子 / 交付物未冻结；3 HIGH：inline 判定 fail-open / request_id 归因传染 / transcript 归因折叠；3 MEDIUM + 4 LOW。同时确认：**当前 92 条数字逐项 0 mismatch**、class/三态/家族计数全对） | `_bmad-output/审查/codex-review-CARD-G4-9.md` |
2712:37:| Codex 复审 round-2 | **仍阻断**（10/13 CLOSED；BLOCKER-1/HIGH-1/HIGH-3 未真正闭合 + 3 新 LOW）。同时独立复算确认：67ccebe1 冻结生效、92 条数字与 6/29 重复簇全部可复算 | `_bmad-output/审查/codex-review-CARD-G4-9-round2.md`（codex 被 cyber 误拦，内容由 stdout 抢救存档） |
2714:39-| Codex 复审 round-3 | **仍阻断**（4/6 CLOSED；BLOCKER-1/HIGH-3 判 PARTIAL + 1 新 MEDIUM + 2 新 LOW）。同时确认：HIGH-1 与三条 LOW 已闭合、台账数字有效且与 commit 字节一致 | `_bmad-output/审查/codex-review-CARD-G4-9-round3.md` |
2716:41-| Codex 复审 round-4 | **仍阻断**（1/6 CLOSED；2 新 BLOCKER + 1 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round4.md` |
2718:43-| Codex 复审 round-5 | **仍阻断**（3/8 CLOSED；2 BLOCKER + 2 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round5.md` |
2719:44:| round-5 findings 逐条整改 | **9/9 完成**：先扫描后判定（冲突候选亦入保护集）/ QA DB fd 身份+复核 / 可见性优先于 anomaly / fchmod 后置于碰撞检查 / QA DB 特殊文件门 / no_token 归 unverifiable / 3 条 LOW。6 条新反例实测全过；第五次全量重跑数字仍不变 | 报告 §7f |
2724:49-- **BLOCKER-1 --out 截断风险**：任意 --out 路径 "w" 无守卫，可覆盖 DLQ 自身（双审查独立实测复现）。整改：写前 resolve() 路径碰撞守卫，命中输入集合即 exit 2；负例实测拒绝、DLQ 完好。
2725:50-- **BLOCKER-2 快照不原子**：records 与头部 sha 来自两次读取。整改：单次 read_bytes()，头部与逐条同源同字节。
2726:51-- **BLOCKER-3 交付物漂移**：审查期间脚本/报告 sha 变化且未 track。整改：本卡 commit 冻结全部 exact bytes；自证文件内嵌脚本 sha 前缀。
2735:60-## 🔧 Codex round-2 复审整改记录（10/13 CLOSED → 剩 3 项 + 3 新 LOW 全关闭）
2743:71-## 🔧 Codex round-3 复审整改记录（4/6 CLOSED → 剩 2 项 + 3 新发现全关闭）
2747:75:- **BLOCKER-1 仍 PARTIAL**：① 保护集漏了**归因到的 transcript**——`--out` 指向它会截断恢复源；② check-then-open 的 **TOCTOU** 仍在。→ ① transcript 写前并入保护集；② 改 `O_NOFOLLOW` 打开且**不带 O_TRUNC**，对实际 fd `fstat` 校验后才 `ftruncate`。反例实测：exit 2、transcript 完好。
2754:82-## 🔧 Codex round-4 复审整改记录（1/6 CLOSED → 9 项全关闭）
2756:84-round-4 只认 1 项闭合，用更深的反例推翻其余"闭合"——两条新 BLOCKER 都是真的：
2758:86:- **不可读但可写（mode 0200）的 transcript 绕过保护集**：我在"不可读"分支把候选路径清空了，于是它没进保护集，`--out` 指向它照样截断——不需要任何竞态。→ 新增"全候选清单"，无论可读与否一律并入保护集。
2765:93-## 🔧 Codex round-5 复审整改记录（3/8 CLOSED → 9 项全关闭）
2767:95-round-5 继续深挖，两条新 BLOCKER 与两条 HIGH 都成立：
2769:97-- **冲突组的候选没进保护集**：token 冲突时我在扫描**之前**就早退了，那些候选从没被看到，`--out` 指向它们照样截断。→ 改成**先扫描后判定**，无论最终是否采信，见到的候选一律进保护集。
2772:100:- **`fchmod` 排在碰撞检查之前**：`--out` 指向受保护的只读输入时，会先把它的权限从 644 改成 600 才发现碰撞——字节没丢但输入被改了。→ 碰撞检查前移。
2773:101:- **其余 5 项**：QA DB 特殊文件门、无 token 归 `unverifiable`、单独换行算 1 空行、strict encode 堵住 lone surrogate 伪造 `full_verified`、`bool` 不再通过长度门。
2882: | Codex 复审 round-3 | **仍阻断**（4/6 CLOSED；BLOCKER-1/HIGH-3 判 PARTIAL + 1 新 MEDIUM + 2 新 LOW）。同时确认：HIGH-1 与三条 LOW 已闭合、台账数字有效且与 commit 字节一致 | `_bmad-output/审查/codex-review-CARD-G4-9-round3.md` |
2884: | Codex 复审 round-4 | **仍阻断**（1/6 CLOSED；2 新 BLOCKER + 1 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round4.md` |
2886:+| Codex 复审 round-5 | **仍阻断**（3/8 CLOSED；2 BLOCKER + 2 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round5.md` |
2887:+| round-5 findings 逐条整改 | **9/9 完成**：先扫描后判定（冲突候选亦入保护集）/ QA DB fd 身份+复核 / 可见性优先于 anomaly / fchmod 后置于碰撞检查 / QA DB 特殊文件门 / no_token 归 unverifiable / 3 条 LOW。6 条新反例实测全过；第五次全量重跑数字仍不变 | 报告 §7f |
2892: - **BLOCKER-1 --out 截断风险**：任意 --out 路径 "w" 无守卫，可覆盖 DLQ 自身（双审查独立实测复现）。整改：写前 resolve() 路径碰撞守卫，命中输入集合即 exit 2；负例实测拒绝、DLQ 完好。
2899:+## 🔧 Codex round-5 复审整改记录（3/8 CLOSED → 9 项全关闭）
2901:+round-5 继续深挖，两条新 BLOCKER 与两条 HIGH 都成立：
2903:+- **冲突组的候选没进保护集**：token 冲突时我在扫描**之前**就早退了，那些候选从没被看到，`--out` 指向它们照样截断。→ 改成**先扫描后判定**，无论最终是否采信，见到的候选一律进保护集。
2906:+- **`fchmod` 排在碰撞检查之前**：`--out` 指向受保护的只读输入时，会先把它的权限从 644 改成 600 才发现碰撞——字节没丢但输入被改了。→ 碰撞检查前移。
2907:+- **其余 5 项**：QA DB 特殊文件门、无 token 归 `unverifiable`、单独换行算 1 空行、strict encode 堵住 lone surrogate 伪造 `full_verified`、`bool` 不再通过长度门。
2927:@@ -159,5 +159,21 @@ round-4 只认可 1 项 CLOSED（非 dict JSON 门），并用更深的静态反
2934:+## §7f Codex round-5 复审整改记录（3/8 CLOSED → 9 项全部整改）
2936:+round-5 用更深的静态反例继续推翻"闭合"，提出 2 BLOCKER / 2 HIGH / 2 MEDIUM / 3 LOW，逐条整改并实测：
2938:+- **BLOCKER①（token 冲突/无 token 时扫描前早退 → 候选不进保护集）**：`--out` 指向冲突组的候选 transcript 仍可无竞态截断。**整改**：`resolve_group_attribution()` 重写为**先扫描后判定**——无条件为每个 token 扫描收集候选进 `all_candidate_paths`（保护集口径），再做冲突/唯一性判定；候选 `stat` 失败不再 `continue` 吞掉而是 exit 2（保护集不完整即拒绝写出）。实测：冲突候选作 `--out` → exit 2、文件 sha 不变。
2939:+- **BLOCKER②（qa_metrics.db 身份未绑定实际读取）**：仍是早期 path-stat + SQLite 稍后按路径重开。**整改**：`probe_qa_metrics()` 改 `os.open(O_RDONLY|O_NOFOLLOW|O_NONBLOCK)` 取 fstat 身份 + `S_ISREG` 门 → SQLite 打开后**复核路径身份仍等于该身份**，不等即 `identity_changed_..._refused`；身份入保护集。本次运行 `file_identity_verified: true`。
2941:+- **HIGH②（`fchmod` 先于 protected-id 检查）**：`--out` 指向受保护的 0644 输入时，会**先把只读输入权限改成 0600** 再拒绝——字节没截断但输入已被修改。**整改**：碰撞检查前移到 `fchmod` 之前。实测：mode 644 → 644 不变。
2942:+- **MEDIUM（QA DB 无特殊文件门）**：随 BLOCKER② 一并加 `S_ISREG` + `O_NONBLOCK`。
2943:+- **MEDIUM（无 token 未扫描即判不可恢复）**：改为 `unverifiable` + `no_token` 标记（见 HIGH①）。
2944:+- **LOW ×3**：单独 `b"\n"` 现算 1 个空行（实测 `line_count=1`）；`errors="replace"` 改 **strict encode**（JSON escaped lone surrogate 不能再构造假 `full_verified`）；`bool` 是 `int` 子类 —— `episode_body_length=True` 现被长度门拒绝（实测判 anomaly）。
2946:+**归因冲突计数由 0 变为 3（如实说明）**：round-5 起"名字不含 session token"被诚实标记为 `no_token`（未做归因扫描），命中的正是 3 条 `callout_annotation` 记录。它们 inline 正文全量、sha 对账通过，**不依赖 transcript**，故仍判 `byte_exact`——三态分布不变（4/88/0/0），88 条 approximate 仍全部为唯一 transcript 命中。这是标注口径变诚实，不是结论变化。
3189:**Noting new lone surrogate crash risk**
3231:  3325	  ✓ 交叉验证反例、分级新发现并给出逐项终裁
3238:  3332	总裁定：**仍阻断 / CARD-G4-9 不可验收**。  
3245:  3339	| 1. transcript 全候选保护 | **NOT-CLOSED · BLOCKER** | 多 token 非前缀一致时在扫描前直接返回，[script:168](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:168)，此时 `all_candidate_paths=[]`。同一 `request_id` 含 `session:aaaaa`、`session:bbbbb`，`--out` 指向 `aaaaa….jsonl`，不会进入 [保护循环:599](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:599)，最终仍可在 [ftruncate:639](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:639)截断。无需竞态。不可列举但可穿越的子目录也有同类绕过；后置 transcript `stat` 失败仍被 `continue` 吞掉。 |
3246:  3340	| 2. 源侧 fd 身份绑定 | **NOT-CLOSED / PARTIAL · BLOCKER** | DLQ/compare 的狭义修复已 CLOSED：同一 fd `open→fstat→read→identity`，[snapshot:262](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:262)、[DLQ:389](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:389)、[compare:542](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:542)。但 `qa_metrics_db` 仍是早期 path-stat、稍后 SQLite 按路径重新打开，[probe:233](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:233)。可令 stat 看到 inode A、SQLite 实际读取换入的 B、`--out` 为 B 的 hardlink，最终 B 不在保护集并被截断。 |
3247:  3341	| 3. `unverifiable` 四态 | **NOT-CLOSED · HIGH** | distribution/list 同步已实现。但 `anomaly→unrecoverable` 位于 conflict 判断之前，[script:464](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:464)：`anomaly + 扫描受阻/不可读/归因冲突` 仍被假终态化。另无 token 时未扫描即返回，truncated 记录随后被称为“无在盘源”，也应是 `unverifiable`。 |
3248:  3342	| 4. FIFO/设备门 | **NOT-CLOSED / PARTIAL · MEDIUM** | DLQ、compare、`--out` 的 `O_NONBLOCK + S_ISREG` 已 CLOSED，[读侧:269](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:269)、[写侧:620](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:620)。但 QA DB 读侧仍直接进入 SQLite，无 regular-file/nonblocking 门，FIFO 仍可能阻塞。 |
3249:  3343	| 5. 非法 UTF-8 | **CLOSED（原项）** | 逐 LF frame strict decode，并在调用方归 `unparseable`，[splitter:77](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:77)、[caller:399](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:399)。只读验证坏字节得到 1 frame + decode error。 |
3250:  3344	| 6a. 三个指定字段错型 | **CLOSED** | `name`、不可哈希 `request_id`、非字符串 `episode_body` 均不再炸全量，[name:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:143)、[request_id:423](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:423)、[body:111](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:111)。 |
3251:  3345	| 6b. 根 `/` containment | **CLOSED** | `root_prefix` 对 `/` 保持 `/`，非根补尾斜杠，[script:203](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:203)。 |
3252:  3346	| 6c. 既有输出 `fchmod 0600` | **NOT-CLOSED · HIGH** | `fchmod` 在 protected-inode 拒绝之前，[script:630](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:630)。`--out` 指向已保护的 `0644` transcript 时，会先把源权限改成 `0600`，再发现碰撞并 exit 2。字节虽未截断，但只读输入已被修改。 |
3253:  3347	| 7. provenance receipt | **CLOSED（仓库内）** | 报告头已指向 receipt，[report:5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:5)；receipt 链与 Git ancestry 一致，[receipt:4](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt:4)。LOW 限制：记录的是当前仓库内唯一可解析的 8-hex 缩写，不是独立于仓库的完整 40-hex OID。 |
3268:  3362	### 新发现/残留边界
3270:  3364	- **BLOCKER**：token-conflict 扫描前早退，仍可无竞态截断 transcript。
3271:  3365	- **BLOCKER**：QA DB 实际读取身份未绑定。
3274:  3368	- **LOW**：单独 `b"\n"` 仍被算作 0 行；escaped lone surrogate 可借 `errors="replace"` 构造 `full_verified`；`episode_body_length=True/1.0` 也可通过长度门。
3283:  3377	总裁定：**仍阻断 / CARD-G4-9 不可验收**。  
3290:  3384	| 1. transcript 全候选保护 | **NOT-CLOSED · BLOCKER** | 多 token 非前缀一致时在扫描前直接返回，[script:168](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:168)，此时 `all_candidate_paths=[]`。同一 `request_id` 含 `session:aaaaa`、`session:bbbbb`，`--out` 指向 `aaaaa….jsonl`，不会进入 [保护循环:599](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:599)，最终仍可在 [ftruncate:639](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:639)截断。无需竞态。不可列举但可穿越的子目录也有同类绕过；后置 transcript `stat` 失败仍被 `continue` 吞掉。 |
3291:  3385	| 2. 源侧 fd 身份绑定 | **NOT-CLOSED / PARTIAL · BLOCKER** | DLQ/compare 的狭义修复已 CLOSED：同一 fd `open→fstat→read→identity`，[snapshot:262](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:262)、[DLQ:389](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:389)、[compare:542](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:542)。但 `qa_metrics_db` 仍是早期 path-stat、稍后 SQLite 按路径重新打开，[probe:233](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:233)。可令 stat 看到 inode A、SQLite 实际读取换入的 B、`--out` 为 B 的 hardlink，最终 B 不在保护集并被截断。 |
3292:  3386	| 3. `unverifiable` 四态 | **NOT-CLOSED · HIGH** | distribution/list 同步已实现。但 `anomaly→unrecoverable` 位于 conflict 判断之前，[script:464](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:464)：`anomaly + 扫描受阻/不可读/归因冲突` 仍被假终态化。另无 token 时未扫描即返回，truncated 记录随后被称为“无在盘源”，也应是 `unverifiable`。 |
3293:  3387	| 4. FIFO/设备门 | **NOT-CLOSED / PARTIAL · MEDIUM** | DLQ、compare、`--out` 的 `O_NONBLOCK + S_ISREG` 已 CLOSED，[读侧:269](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:269)、[写侧:620](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:620)。但 QA DB 读侧仍直接进入 SQLite，无 regular-file/nonblocking 门，FIFO 仍可能阻塞。 |
3294:  3388	| 5. 非法 UTF-8 | **CLOSED（原项）** | 逐 LF frame strict decode，并在调用方归 `unparseable`，[splitter:77](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:77)、[caller:399](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:399)。只读验证坏字节得到 1 frame + decode error。 |
3295:  3389	| 6a. 三个指定字段错型 | **CLOSED** | `name`、不可哈希 `request_id`、非字符串 `episode_body` 均不再炸全量，[name:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:143)、[request_id:423](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:423)、[body:111](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:111)。 |
3296:  3390	| 6b. 根 `/` containment | **CLOSED** | `root_prefix` 对 `/` 保持 `/`，非根补尾斜杠，[script:203](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:203)。 |
3297:  3391	| 6c. 既有输出 `fchmod 0600` | **NOT-CLOSED · HIGH** | `fchmod` 在 protected-inode 拒绝之前，[script:630](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:630)。`--out` 指向已保护的 `0644` transcript 时，会先把源权限改成 `0600`，再发现碰撞并 exit 2。字节虽未截断，但只读输入已被修改。 |
3298:  3392	| 7. provenance receipt | **CLOSED（仓库内）** | 报告头已指向 receipt，[report:5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:5)；receipt 链与 Git ancestry 一致，[receipt:4](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt:4)。LOW 限制：记录的是当前仓库内唯一可解析的 8-hex 缩写，不是独立于仓库的完整 40-hex OID。 |
3313:  3407	### 新发现/残留边界
3315:  3409	- **BLOCKER**：token-conflict 扫描前早退，仍可无竞态截断 transcript。
3316:  3410	- **BLOCKER**：QA DB 实际读取身份未绑定。
3319:  3413	- **LOW**：单独 `b"\n"` 仍被算作 0 行；escaped lone surrogate 可借 `errors="replace"` 构造 `full_verified`；`episode_body_length=True/1.0` 也可通过长度门。
3404:no_token_lines = [n for n, r in records if not tokens(r.get("name", ""))]
3447:    "no_token_lines": no_token_lines,
3548:no_token_lines = [n for n, r in records if not tokens(r.get("name", ""))]
3586:    "no_token_lines": no_token_lines,
3597:{"approximate_internal_contract_rows": 88, "bytes": 99915, "class": {"budget_400": 89, "group_id_format": 1, "schema_entity_type": 2}, "duplicate_clusters": 6, "duplicate_occurrences": 29, "duplicate_sizes": [16, 4, 3, 2, 2, 2], "inline": {"full_verified": 4, "truncated_prefix": 88}, "ledger_attribution_conflicts": 3, "ledger_record_mismatches": [], "ledger_recoverability": {"approximate": 88, "byte_exact": 4, "unrecoverable": 0, "unverifiable": 0}, "ledger_sha_matches_source": true, "lf_frames": 92, "no_token_lines": [1, 2, 3, 5, 6, 9, 10, 13, 14, 18, 20, 21, 24, 25, 29, 30, 31, 33, 34, 37, 38, 41, 42, 45, 46, 49, 50, 53, 54, 57, 58, 61, 62, 65, 66, 69, 70, 73, 74, 75, 78, 79, 82, 83, 86, 87, 90, 91], "records": 92, "request_groups": 25, "sha256": "3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590", "token_prefix_conflict_groups": 0, "unparseable": 0}
3599:**Revising no_token_lines grouping logic**
3632:no_token=[]
3638:        no_token.extend(nums)
3641:print(json.dumps({"group_no_token_record_lines":sorted(no_token),"group_token_conflict_record_lines":sorted(conflict),"no_token_records":len(no_token),"conflict_records":len(conflict)}))
3644:{"group_no_token_record_lines": [1, 2, 3], "group_token_conflict_record_lines": [], "no_token_records": 3, "conflict_records": 0}
3647:**Testing JSON surrogate pair handling**
3668:121:    # round-5 LOW 整改: errors="replace" 会把 JSON escaped lone surrogate
3686:696:            # round-5 HIGH 整改: 碰撞检查必须**先于** fchmod —— 否则 --out 指向
3719:/bin/zsh -lc "python3 -B -c 'import runpy,json; from pathlib import Path; m=runpy.run_path(\"backend/scripts/census_dead_letter_episodes.py\"); f=m[\"resolve_group_attribution\"]; a=f([\"board\",\"vault\"],Path(\".\")); b=f([],Path(\".\")); print(json.dumps({\"conflict\":{\"token_conflict\":a.get(\"token_conflict\"),\"all_candidate_count\":len(a[\"all_candidate_paths\"]),\"scan_errors\":len(a.get(\"scan_errors\",[]))},\"no_token\":{\"no_token\":b.get(\"no_token\"),\"all_candidate_count\":len(b[\"all_candidate_paths\"])}}))'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
3721:{"conflict": {"token_conflict": true, "all_candidate_count": 2, "scan_errors": 0}, "no_token": {"no_token": true, "all_candidate_count": 0}}
3725:**Investigating missing no_token marker**
3726:**Clarifying no_token recoverability logic**
3727:**Resolving no_token status and JSON encoding issues**
3940:    28	| 脚本只读自证（判据 a） | import 行全 stdlib；neo4j/graphiti/bolt/app. import **0 命中**；`--apply` 定义 **0 命中**；写模式 open 仅台账 `--out` 1 处 | `G4-9-evidence/grep-selfattest.txt` |
3947:    35	| Codex 独立审查 round-1 | **BLOCKED**（3 BLOCKER：--out 可截断输入 / 快照不原子 / 交付物未冻结；3 HIGH：inline 判定 fail-open / request_id 归因传染 / transcript 归因折叠；3 MEDIUM + 4 LOW。同时确认：**当前 92 条数字逐项 0 mismatch**、class/三态/家族计数全对） | `_bmad-output/审查/codex-review-CARD-G4-9.md` |
3949:    41	| Codex 复审 round-4 | **仍阻断**（1/6 CLOSED；2 新 BLOCKER + 1 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round4.md` |
3951:    43	| Codex 复审 round-5 | **仍阻断**（3/8 CLOSED；2 BLOCKER + 2 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round5.md` |
3952:    44	| round-5 findings 逐条整改 | **9/9 完成**：先扫描后判定（冲突候选亦入保护集）/ QA DB fd 身份+复核 / 可见性优先于 anomaly / fchmod 后置于碰撞检查 / QA DB 特殊文件门 / no_token 归 unverifiable / 3 条 LOW。6 条新反例实测全过；第五次全量重跑数字仍不变 | 报告 §7f |
3955:    93	## 🔧 Codex round-5 复审整改记录（3/8 CLOSED → 9 项全关闭）
3957:    95	round-5 继续深挖，两条新 BLOCKER 与两条 HIGH 都成立：
3959:    97	- **冲突组的候选没进保护集**：token 冲突时我在扫描**之前**就早退了，那些候选从没被看到，`--out` 指向它们照样截断。→ 改成**先扫描后判定**，无论最终是否采信，见到的候选一律进保护集。
3962:   100	- **`fchmod` 排在碰撞检查之前**：`--out` 指向受保护的只读输入时，会先把它的权限从 644 改成 600 才发现碰撞——字节没丢但输入被改了。→ 碰撞检查前移。
3963:   101	- **其余 5 项**：QA DB 特殊文件门、无 token 归 `unverifiable`、单独换行算 1 空行、strict encode 堵住 lone surrogate 伪造 `full_verified`、`bool` 不再通过长度门。
4029:    92	| grep 自证（import 行全 stdlib；neo4j/graphiti/bolt/app. import 0 命中；`--apply` 定义 0 命中；写模式 open 仅 `--out` 1 处且受路径碰撞守卫保护） | **PASS**（`grep-selfattest.txt`，含守卫在位证明） |
4032:    95	| 负例门（round-1 整改自证） | `--out`==`--dlq` → exit 2 拒写、DLQ 完好；transcripts 根缺失 → exit 2 拒诊；sha 匹配但长度不符（round-1 HIGH-1 反例①）→ anomaly/unrecoverable；坏 JSON 行/空行 → unparseable 逐行入台账不拒诊 |
4033:    96	| 负例门（round-2 整改自证） | **hardlink** 指向 DLQ 的 --out → exit 2 + DLQ sha 不变；**case-only 别名**（`DLQ.jsonl`）→ exit 2 + DLQ 完好；**anomaly + episode_body_full 组合**（sha 对但长度 999）→ anomaly/unrecoverable（不再翻案 byte_exact）；**chmod 000 根** → exit 2 拒诊；**symlink 逃逸**（根内 .jsonl → 根外 .txt）→ match_count=0/unrecoverable；正例回归：真实唯一命中仍 approximate |
4038:   165	## §7f Codex round-5 复审整改记录（3/8 CLOSED → 9 项全部整改）
4040:   167	round-5 用更深的静态反例继续推翻"闭合"，提出 2 BLOCKER / 2 HIGH / 2 MEDIUM / 3 LOW，逐条整改并实测：
4042:   169	- **BLOCKER①（token 冲突/无 token 时扫描前早退 → 候选不进保护集）**：`--out` 指向冲突组的候选 transcript 仍可无竞态截断。**整改**：`resolve_group_attribution()` 重写为**先扫描后判定**——无条件为每个 token 扫描收集候选进 `all_candidate_paths`（保护集口径），再做冲突/唯一性判定；候选 `stat` 失败不再 `continue` 吞掉而是 exit 2（保护集不完整即拒绝写出）。实测：冲突候选作 `--out` → exit 2、文件 sha 不变。
4043:   170	- **BLOCKER②（qa_metrics.db 身份未绑定实际读取）**：仍是早期 path-stat + SQLite 稍后按路径重开。**整改**：`probe_qa_metrics()` 改 `os.open(O_RDONLY|O_NOFOLLOW|O_NONBLOCK)` 取 fstat 身份 + `S_ISREG` 门 → SQLite 打开后**复核路径身份仍等于该身份**，不等即 `identity_changed_..._refused`；身份入保护集。本次运行 `file_identity_verified: true`。
4045:   172	- **HIGH②（`fchmod` 先于 protected-id 检查）**：`--out` 指向受保护的 0644 输入时，会**先把只读输入权限改成 0600** 再拒绝——字节没截断但输入已被修改。**整改**：碰撞检查前移到 `fchmod` 之前。实测：mode 644 → 644 不变。
4046:   173	- **MEDIUM（QA DB 无特殊文件门）**：随 BLOCKER② 一并加 `S_ISREG` + `O_NONBLOCK`。
4047:   174	- **MEDIUM（无 token 未扫描即判不可恢复）**：改为 `unverifiable` + `no_token` 标记（见 HIGH①）。
4048:   175	- **LOW ×3**：单独 `b"\n"` 现算 1 个空行（实测 `line_count=1`）；`errors="replace"` 改 **strict encode**（JSON escaped lone surrogate 不能再构造假 `full_verified`）；`bool` 是 `int` 子类 —— `episode_body_length=True` 现被长度门拒绝（实测判 anomaly）。
4050:   177	**归因冲突计数由 0 变为 3（如实说明）**：round-5 起"名字不含 session token"被诚实标记为 `no_token`（未做归因扫描），命中的正是 3 条 `callout_annotation` 记录。它们 inline 正文全量、sha 对账通过，**不依赖 transcript**，故仍判 `byte_exact`——三态分布不变（4/88/0/0），88 条 approximate 仍全部为唯一 transcript 命中。这是标注口径变诚实，不是结论变化。
4161:**Assessing JSON output surrogate risks**
4411:复核已收束：冻结台账的 exact-byte 数字成立，但生成器的只读安全闭包仍失败。当前逐项为 6/9 狭义整改 CLOSED、3/9 NOT-CLOSED；两个残留路径都能触达报告/UAT 明确承诺的“零写入”，因此不是范围外加固。接下来只整理终裁，不会写审查文件。
4417:  ✓ 汇总 CLOSED/NOT-CLOSED、新发现分级与最终验收裁定
4422:**Clarifying no_token conflict artifact meaning**
4434:总裁定：**仍阻断，CARD-G4-9 round-6 不可验收。**
4439:- **生成器只读安全闭包 FAIL**：仍有 2 个 BLOCKER，能违反报告/UAT 的“纯只读、零写入”承诺。
4440:- 按 7 个顶层整改计为 **4/7 CLOSED**；把 LOW×3 拆开则为 **6/9 CLOSED**。
4446:| 1. token 冲突/无 token 先扫描 | **NOT-CLOSED · BLOCKER** | 可枚举 token-conflict 候选确会先进入保护集；但扫描受阻只标 `unverifiable`，不会停止写出。根可读、子目录 `0333`（不可列举但可按名穿越）、其中存在匹配 transcript `T` 时，`os.walk` 只能记录错误，`T` 不进保护集，`--out=T` 最终仍可被打开并截断。[扫描入口](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:201)、[scan_errors 判定](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:241)、[保护循环](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:663)、[输出打开](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:686)。无 token 时 `if uniq` 仍完全不扫描，`all_candidate_paths=[]`。 |
4447:| 2. QA DB 身份绑定 | **NOT-CLOSED · BLOCKER** | 验证 fd 在 [line 288](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:288) 已关闭；SQLite 随后按路径另开，[后置 `os.stat(path)`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:295)并不能证明连接打开的是同一 inode。A→B→A 的 ABA 可通过；`protected_ids` 仍只加入 A，[line 618](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:618)。 |
4448:| 3. visibility 优先于 anomaly | **CLOSED** | byte-exact 两支之后，`attribution_conflict→unverifiable` 已位于 `anomaly→unrecoverable` 前：[exact](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:518)、[conflict](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:524)、[anomaly](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:542)。exact 先行是合理例外，因为不依赖 transcript。 |
4449:| 4. fchmod 顺序 | **CLOSED（局部）** | 实际顺序为碰撞检查 [698](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:698) → `fchmod` [706](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:706) → `ftruncate` [707](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:707)。但它不能补救项目 1/2 导致的保护集漏项。 |
4450:| 5. QA DB 特殊文件门 | **NOT-CLOSED / PARTIAL · MEDIUM** | 第一次 `O_NONBLOCK+S_ISREG` 能拒绝稳定 FIFO/设备；但 fd 随即关闭，SQLite 第二次按路径打开没有这些门。regular→FIFO/symlink 替换仍可绕过并在 `connect()` 内阻塞。 |
4451:| 6. no_token→unverifiable | **CLOSED（行为）** | 非 byte-exact 的 no-token 记录会进入 `unverifiable`；full-verified/no-token 仍为 byte-exact，语义正确。[no_token](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:228)。但 `no_token` 未写入 ledger，见下方 LOW。 |
4452:| 7a. 单独 LF | **CLOSED** | 纯内存复算：`b""→0`、`b"\n"→1`、`b"\n\n"→2`、`b"{}\n"→1`。[实现](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:85)。 |
4453:| 7b. strict encode | **CLOSED（原反例）** | lone `U+D800` 配旧 replace-hash 现为 `anomaly/FAIL`，full-body 为 `False`；正常 emoji 正控仍通过。[inline](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:124)、[full-body](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:151)。 |
4454:| 7c. bool 长度门 | **CLOSED** | `True/False/1.0` 均被拒，整数 `1` 正控通过。[inline 门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:129)、[full-body 门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:148)。 |
4456:### QA DB 新的确定性 BLOCKER
4466:这是无需竞态的零写入反例，足以单独维持 BLOCKER。
4486:### 其他新发现
4489:- **LOW — ledger 不自描述**：`no_token` 仅存在于内存；记录只序列化笼统的 `attribution_conflict=true`，无法区分缺 token、token 冲突或多命中。
4490:- **LOW — 其余字段 surrogate DoS**：strict encode 只覆盖 body/full-body；`name/error/group_id` 等若含 escaped lone surrogate，`ensure_ascii=False` 的 UTF-8 写出仍会抛错并拒绝整次 census。
4498:总裁定：**仍阻断，CARD-G4-9 round-6 不可验收。**
4503:- **生成器只读安全闭包 FAIL**：仍有 2 个 BLOCKER，能违反报告/UAT 的“纯只读、零写入”承诺。
4504:- 按 7 个顶层整改计为 **4/7 CLOSED**；把 LOW×3 拆开则为 **6/9 CLOSED**。
4510:| 1. token 冲突/无 token 先扫描 | **NOT-CLOSED · BLOCKER** | 可枚举 token-conflict 候选确会先进入保护集；但扫描受阻只标 `unverifiable`，不会停止写出。根可读、子目录 `0333`（不可列举但可按名穿越）、其中存在匹配 transcript `T` 时，`os.walk` 只能记录错误，`T` 不进保护集，`--out=T` 最终仍可被打开并截断。[扫描入口](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:201)、[scan_errors 判定](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:241)、[保护循环](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:663)、[输出打开](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:686)。无 token 时 `if uniq` 仍完全不扫描，`all_candidate_paths=[]`。 |
4511:| 2. QA DB 身份绑定 | **NOT-CLOSED · BLOCKER** | 验证 fd 在 [line 288](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:288) 已关闭；SQLite 随后按路径另开，[后置 `os.stat(path)`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:295)并不能证明连接打开的是同一 inode。A→B→A 的 ABA 可通过；`protected_ids` 仍只加入 A，[line 618](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:618)。 |
4512:| 3. visibility 优先于 anomaly | **CLOSED** | byte-exact 两支之后，`attribution_conflict→unverifiable` 已位于 `anomaly→unrecoverable` 前：[exact](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:518)、[conflict](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:524)、[anomaly](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:542)。exact 先行是合理例外，因为不依赖 transcript。 |
4513:| 4. fchmod 顺序 | **CLOSED（局部）** | 实际顺序为碰撞检查 [698](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:698) → `fchmod` [706](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:706) → `ftruncate` [707](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:707)。但它不能补救项目 1/2 导致的保护集漏项。 |
4514:| 5. QA DB 特殊文件门 | **NOT-CLOSED / PARTIAL · MEDIUM** | 第一次 `O_NONBLOCK+S_ISREG` 能拒绝稳定 FIFO/设备；但 fd 随即关闭，SQLite 第二次按路径打开没有这些门。regular→FIFO/symlink 替换仍可绕过并在 `connect()` 内阻塞。 |
4515:| 6. no_token→unverifiable | **CLOSED（行为）** | 非 byte-exact 的 no-token 记录会进入 `unverifiable`；full-verified/no-token 仍为 byte-exact，语义正确。[no_token](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:228)。但 `no_token` 未写入 ledger，见下方 LOW。 |
4516:| 7a. 单独 LF | **CLOSED** | 纯内存复算：`b""→0`、`b"\n"→1`、`b"\n\n"→2`、`b"{}\n"→1`。[实现](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:85)。 |
4517:| 7b. strict encode | **CLOSED（原反例）** | lone `U+D800` 配旧 replace-hash 现为 `anomaly/FAIL`，full-body 为 `False`；正常 emoji 正控仍通过。[inline](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:124)、[full-body](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:151)。 |
4518:| 7c. bool 长度门 | **CLOSED** | `True/False/1.0` 均被拒，整数 `1` 正控通过。[inline 门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:129)、[full-body 门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:148)。 |
4520:### QA DB 新的确定性 BLOCKER
4530:这是无需竞态的零写入反例，足以单独维持 BLOCKER。
4550:### 其他新发现
4553:- **LOW — ledger 不自描述**：`no_token` 仅存在于内存；记录只序列化笼统的 `attribution_conflict=true`，无法区分缺 token、token 冲突或多命中。
4554:- **LOW — 其余字段 surrogate DoS**：strict encode 只覆盖 body/full-body；`name/error/group_id` 等若含 escaped lone surrogate，`ensure_ascii=False` 的 UTF-8 写出仍会抛错并拒绝整次 census。

exec
/bin/zsh -lc 'git diff --name-status 4c125f19..HEAD' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
M	"_bmad-output/\345\256\241\346\237\245/G4-9-DLQ-census-2026-08-28.md"
M	"_bmad-output/\345\256\241\346\237\245/G4-9-dlq-ledger-2026-08-28.json"
M	"_bmad-output/\345\256\241\346\237\245/G4-9-evidence/artifact-commit-receipt.txt"
M	"_bmad-output/\345\256\241\346\237\245/G4-9-evidence/grep-selfattest.txt"
A	"_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round6.md"
M	"_bmad-output/\351\252\214\346\224\266\345\215\225/UAT-CARD-G4-9-DLQ\347\234\237\345\256\236\346\214\202\350\275\275census\345\210\206\350\257\212-2026-08-28.md"
M	backend/scripts/census_dead_letter_episodes.py

exec
/bin/zsh -lc 'nl -ba backend/scripts/census_dead_letter_episodes.py' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
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
   201	    # round-6 整改: **无论有无 token 都遍历** —— no_token 时原实现完全不扫描，
   202	    # all_candidate_paths 为空，该组见不到的候选就进不了保护集。
   203	    for dirpath, _dirnames, filenames in os.walk(transcripts_dir, onerror=_on_walk_error, followlinks=False):
   204	        for fname in filenames:
   205	            if fname.endswith(".jsonl"):
   206	                matched = [t for t in uniq if fname.startswith(t)]
   207	                candidate = os.path.join(dirpath, fname)
   208	                # 候选一律入 all_candidate_paths（保护集口径），再谈可用性
   209	                all_candidates.append(candidate)
   210	                if not matched:
   211	                    continue
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
   281	    # round-6 BLOCKER② 整改: 验证 fd **保持打开**直到 SQLite 连接建立并复核完毕
   282	    # —— 原实现验证后即关闭，SQLite 按路径重开可被 A→B→A 的 ABA 骗过。
   283	    conn = None
   284	    try:
   285	        st = os.fstat(fd)
   286	        if not stat.S_ISREG(st.st_mode):
   287	            result["verdict"] = "not_regular_file_refused"
   288	            return result, None
   289	        identity = (st.st_dev, st.st_ino)
   290	
   291	        uri = f"file:{db_path}?mode=ro"
   292	        conn = sqlite3.connect(uri, uri=True)
   293	        # 连接建立后在**持有验证 fd 的同时**复核路径身份
   294	        try:
   295	            recheck = os.stat(db_path)
   296	        except OSError as e:
   297	            result["verdict"] = f"recheck_stat_failed: {e}"
   298	            return result, identity
   299	        if (recheck.st_dev, recheck.st_ino) != identity:
   300	            result["verdict"] = "identity_changed_between_verify_and_open_refused"
   301	            return result, identity
   302	        # 再次 fstat 验证 fd：确认它仍指向同一对象且未被 unlink 替换
   303	        st2 = os.fstat(fd)
   304	        if (st2.st_dev, st2.st_ino) != identity or st2.st_nlink == 0:
   305	            result["verdict"] = "verified_fd_invalidated_refused"
   306	            return result, identity
   307	        result["opened_readonly"] = True
   308	        result["file_identity_verified"] = True
   309	        tables = [
   310	            r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
   311	        ]
   312	        result["tables"] = tables
   313	        if "qa_error_logs" in tables:
   314	            total = conn.execute("SELECT COUNT(*) FROM qa_error_logs").fetchone()[0]
   315	            result["qa_error_logs_rows"] = total
   316	            hits = {}
   317	            for et in sorted(set(error_types)):
   318	                hits[et] = conn.execute("SELECT COUNT(*) FROM qa_error_logs WHERE error_type = ?", (et,)).fetchone()[0]
   319	            result["error_type_hits"] = hits
   320	            result["verdict"] = "no_source_rows" if total == 0 else "rows_present_see_hits"
   321	        else:
   322	            result["verdict"] = "qa_error_logs_table_missing"
   323	    finally:
   324	        if conn is not None:
   325	            conn.close()
   326	        os.close(fd)
   327	    return result, identity
   328	
   329	
   330	def snapshot_file(path: Path) -> tuple[bytes, dict, tuple[int, int]]:
   331	    """一次性读全量 bytes；sha/行数/身份全部派生自**同一个 fd**。
   332	
   333	    round-4 BLOCKER② 整改: 原实现按路径 stat 采集保护身份、稍后才按路径读取，
   334	    两步之间对象可被换掉（源侧 TOCTOU）。现改为打开一次 fd → fstat 取身份 →
   335	    从该 fd 读全量，返回的 (st_dev, st_ino) 即**实际被读取对象**的身份。
   336	    """
   337	    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
   338	    try:
   339	        st = os.fstat(fd)
   340	        if not stat.S_ISREG(st.st_mode):
   341	            raise OSError(f"不是常规文件（拒绝 FIFO/设备/目录）: {path}")
   342	        identity = (st.st_dev, st.st_ino)
   343	        chunks = []
   344	        while True:
   345	            block = os.read(fd, 1 << 20)
   346	            if not block:
   347	                break
   348	            chunks.append(block)
   349	        raw = b"".join(chunks)
   350	    finally:
   351	        os.close(fd)
   352	    info = {
   353	        "path": str(path),
   354	        "exists": True,
   355	        # round-3 整改: JSONL 的行分隔符**只有** \n —— splitlines() 会把
   356	        # U+2028/U+2029/裸 CR 也当分隔符，可能把一条 JSON 记录劈成两半。
   357	        # 与 records 同口径按 \n 切分（末尾换行不算空行）。
   358	        "line_count": len(_split_jsonl_lines(raw)),
   359	        "sha256": hashlib.sha256(raw).hexdigest(),
   360	        "mtime_utc": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
   361	        "mtime_note": "mtime 取自读取用 fd 的 fstat；绑定 exact bytes 的是 sha256",
   362	    }
   363	    return raw, info, identity
   364	
   365	
   366	def describe_copy(path: Path) -> tuple[dict, tuple[int, int] | None]:
   367	    """返回 (描述, 实际读取对象身份)；身份用于并入 --out 保护集。"""
   368	    if not path.exists():
   369	        return {"path": str(path), "exists": False}, None
   370	    _, info, identity = snapshot_file(path)
   371	    return info, identity
   372	
   373	
   374	def main(argv: list[str] | None = None) -> int:
   375	    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
   376	    ap.add_argument(
   377	        "--dlq",
   378	        default="data/dead_letter_episodes.jsonl",
   379	        help="DLQ JSONL 路径（census 对 live 挂载运行时传绝对路径）",
   380	    )
   381	    ap.add_argument(
   382	        "--qa-metrics-db",
   383	        default=None,
   384	        help="qa_metrics.db 路径（省略则跳过源指针核销并如实标注 skipped）",
   385	    )
   386	    ap.add_argument(
   387	        "--transcripts-dir",
   388	        default=os.path.expanduser("~/.claude/projects"),
   389	        help="session transcript 根目录（近似恢复源指针核销；不存在则 exit 2 拒诊）",
   390	    )
   391	    ap.add_argument(
   392	        "--compare",
   393	        action="append",
   394	        default=[],
   395	        help="其它 DLQ 副本路径（可重复，产出 sha 对照表）",
   396	    )
   397	    ap.add_argument("--out", default=None, help="台账 JSON 输出路径（省略则打 stdout）")
   398	    args = ap.parse_args(argv)
   399	
   400	    dlq_path = Path(args.dlq)
   401	    if not dlq_path.exists():
   402	        print(f"DLQ 文件不存在: {dlq_path}", file=sys.stderr)
   403	        return 2
   404	
   405	    transcripts_dir = Path(args.transcripts_dir)
   406	    if not transcripts_dir.is_dir():
   407	        print(
   408	            f"transcripts 根目录不存在/不可见: {transcripts_dir} —— 拒绝在源不可见时裁定可恢复性（fail-closed）",
   409	            file=sys.stderr,
   410	        )
   411	        return 2
   412	    # round-2 HIGH-3 整改: 存在但不可读/不可遍历的根（chmod 000）此前 exit 0
   413	    # 并把全部记录假判 unrecoverable —— 同样 fail-closed 拒诊。
   414	    if not os.access(transcripts_dir, os.R_OK | os.X_OK):
   415	        print(
   416	            f"transcripts 根目录不可读/不可遍历: {transcripts_dir} —— 拒绝在源不可见时裁定可恢复性（fail-closed）",
   417	            file=sys.stderr,
   418	        )
   419	        return 2
   420	
   421	    protected_ids: set[tuple[int, int]] = set()
   422	    # round-6 BLOCKER①② 架构整改: inode 保护集依赖**枚举完整性**（不可列举的
   423	    # 子目录、ABA 换 inode 都能让某个真实源不进集合）。故增加**不依赖枚举**的
   424	    # 路径层防御：--out 的 realpath 不得落在 transcripts 根内、不得等于任一
   425	    # 输入路径。路径层 + inode 层双保险，任一命中即拒绝。
   426	    if args.out:
   427	        out_real = os.path.realpath(args.out)
   428	        tr_real = os.path.realpath(args.transcripts_dir)
   429	        tr_prefix = tr_real if tr_real.endswith(os.sep) else tr_real + os.sep
   430	        if out_real == tr_real or out_real.startswith(tr_prefix):
   431	            print(
   432	                f"--out 落在 transcripts 根内（恢复源区域），无条件拒绝写出: {args.out}",
   433	                file=sys.stderr,
   434	            )
   435	            return 2
   436	        input_reals = {os.path.realpath(args.dlq)} | {os.path.realpath(c) for c in args.compare}
   437	        if args.qa_metrics_db:
   438	            input_reals.add(os.path.realpath(args.qa_metrics_db))
   439	        if out_real in input_reals:
   440	            print(f"--out 与输入文件路径相同（realpath 比较），拒绝写出: {args.out}", file=sys.stderr)
   441	            return 2
   442	
   443	    # --out 碰撞守卫（写前）。round-2 BLOCKER-1 整改: 比较**文件身份**
   444	    # (st_dev, st_ino) 而非 resolve() 字符串 —— 后者对 hardlink 与
   445	    # 大小写不敏感文件系统上的 case-only 别名均失效（Codex 实测截断输入）。
   446	    if args.out:
   447	        out_path = Path(args.out)
   448	        protected_paths = [dlq_path, *(Path(p) for p in args.compare)]
   449	        if args.qa_metrics_db:
   450	            protected_paths.append(Path(args.qa_metrics_db))
   451	        for candidate in protected_paths:
   452	            try:
   453	                cst = candidate.stat()  # 跟随 symlink: 保护的是最终目标身份
   454	                protected_ids.add((cst.st_dev, cst.st_ino))
   455	            except OSError:
   456	                # round-4 整改: stat 失败不再静默吞 —— 无法确认身份即 fail-closed
   457	                print(f"输入文件无法 stat，拒绝继续（无法建立完整保护集）: {candidate}", file=sys.stderr)
   458	                return 2
   459	        # 路径字符串比较作为第二道（输出文件尚不存在时 stat 无身份可比）
   460	        out_resolved = out_path.resolve()
   461	        if out_resolved in {p.resolve() for p in protected_paths}:
   462	            print(f"--out 与输入文件路径重合，拒绝写出（防截断）: {out_resolved}", file=sys.stderr)
   463	            return 2
   464	        if out_path.exists():
   465	            try:
   466	                out_st = out_path.stat()
   467	            except OSError as e:
   468	                print(f"--out 无法 stat，拒绝写出: {out_path} ({e})", file=sys.stderr)
   469	                return 2
   470	            if (out_st.st_dev, out_st.st_ino) in protected_ids:
   471	                print(
   472	                    f"--out 与输入文件为同一 inode（hardlink/大小写别名），拒绝写出（防截断）: {out_path}",
   473	                    file=sys.stderr,
   474	                )
   475	                return 2
   476	
   477	    # BLOCKER-2 整改: 单次读取，records 与头部描述共享同一份 exact bytes
   478	    try:
   479	        raw_bytes, dlq_info, dlq_identity = snapshot_file(dlq_path)
   480	    except OSError as e:
   481	        print(f"DLQ 无法安全读取: {dlq_path} ({e})", file=sys.stderr)
   482	        return 2
   483	    protected_ids.add(dlq_identity)  # 保护的是**实际读取对象**，非路径快照
   484	    raw_lines = _split_jsonl_lines(raw_bytes)
   485	
   486	    records: list[tuple[int, dict]] = []
   487	    unparseable: list[dict] = []
   488	    for line_no, (line, decode_err) in enumerate(raw_lines, start=1):
   489	        if decode_err is not None:
   490	            unparseable.append({"line_no": line_no, "reason": decode_err})
   491	            continue
   492	        if not line.strip():
   493	            unparseable.append({"line_no": line_no, "reason": "blank_line"})
   494	            continue
   495	        try:
   496	            rec = json.loads(line)
   497	        except json.JSONDecodeError as e:
   498	            unparseable.append({"line_no": line_no, "reason": f"json_error: {e}", "excerpt": line[:80]})
   499	            continue
   500	        # round-3 LOW 整改: 合法 JSON 但非对象（null / 数组 / 标量）此前解析成功
   501	        # 却在 rec.get() 处抛 AttributeError 炸掉全量 —— 归入 unparseable。
   502	        if not isinstance(rec, dict):
   503	            unparseable.append(
   504	                {"line_no": line_no, "reason": f"not_a_json_object: {type(rec).__name__}", "excerpt": line[:80]}
   505	            )
   506	            continue
   507	        records.append((line_no, rec))
   508	
   509	    # request_id 分组: (类型名, 值) 复合键；缺失/None → 按 line_no 单条成组
   510	    groups: dict[tuple, list[tuple[int, dict]]] = defaultdict(list)
   511	    for line_no, rec in records:
   512	        rid = rec.get("request_id")
   513	        # round-4 LOW 整改: 不可哈希的 request_id（list/dict）按 line_no 单条成组
   514	        try:
   515	            hash(rid)
   516	            hashable = True
   517	        except TypeError:
   518	            hashable = False
   519	        key = ("__missing__", line_no) if (rid is None or not hashable) else (type(rid).__name__, rid)
   520	        groups[key].append((line_no, rec))
   521	    group_attribution: dict[tuple, dict] = {}
   522	    for key, members in groups.items():
   523	        tokens: list[str] = []
   524	        for _, rec in members:
   525	            tokens.extend(session_tokens(rec.get("name", "")))
   526	        group_attribution[key] = resolve_group_attribution(tokens, transcripts_dir)
   527	
   528	    ledger_records = []
   529	    class_dist: Counter = Counter()
   530	    recover_dist: Counter = Counter()
   531	    inline_dist: Counter = Counter()
   532	    unrecoverable_keys = []
   533	    unverifiable_keys = []
   534	    attribution_conflicts = []
   535	    for line_no, rec in records:
   536	        cls = classify(rec)
   537	        state, sha_check = inline_state(rec)
   538	        rid = rec.get("request_id")
   539	        try:
   540	            hash(rid)
   541	            hashable = True
   542	        except TypeError:
   543	            hashable = False
   544	        key = ("__missing__", line_no) if (rid is None or not hashable) else (type(rid).__name__, rid)
   545	        sess = group_attribution[key]
   546	        if state == "full_verified":
   547	            recover = "byte_exact"
   548	            basis = "inline 正文全量：sha256 重算与声明一致且长度精确匹配"
   549	        elif state != "anomaly" and full_body_verified(rec):
   550	            recover = "byte_exact"
   551	            basis = "episode_body_full 在盘且 sha256+长度双门对账通过（DEAD_LETTER_STORE_FULL_BODY 生产 opt-in 字段）"
   552	        elif sess["attribution_conflict"]:
   553	            # round-5 HIGH 整改: 可见性判定**优先于** anomaly —— 源看不见时
   554	            # 无论 inline 是什么状态，都不能断言"不可恢复"。
   555	            recover = "unverifiable"
   556	            if sess.get("no_token"):
   557	                why = "记录名未携带 session token，未做任何归因扫描"
   558	            elif sess.get("token_conflict"):
   559	                why = "同组多 token 前缀冲突"
   560	            elif sess.get("scan_errors"):
   561	                why = "扫描遍历受阻（不可读子树）"
   562	            elif sess.get("stat_failures"):
   563	                why = "候选 stat 失败"
   564	            elif sess.get("unreadable_candidates"):
   565	                why = "存在不可读候选"
   566	            else:
   567	                why = "transcript 多命中 ambiguous"
   568	            extra = "；inline 亦对不上账（anomaly）" if state == "anomaly" else ""
   569	            basis = f"源可见性不足，拒绝裁定：{why}{extra}。既不宣称可恢复，也不宣称不可恢复（fail-closed）"
   570	        elif state == "anomaly":
   571	            recover = "unrecoverable"
   572	            basis = "inline 对不上账（anomaly：sha/长度与声明不符），且归因扫描完整可见但无可用源"
   573	        elif sess["transcript_exists"]:
   574	            recover = "approximate"
   575	            basis = (
   576	                f"inline 为 200 字符前缀（前缀性质依赖 to_dict()[:200] 生产不变量，sha 无法直接证明）；"
   577	                f"经 request_id 组归因到唯一在盘 transcript {sess['session_token']}"
   578	                f"（归因 ≠ 内容已验证——本工具未读 transcript 内容；G4-10 可重蒸馏/重格式化近似重建，非逐字节保证）"
   579	            )
   580	        else:
   581	            recover = "unrecoverable"
   582	            basis = "inline 截断；归因扫描完整可见（无遍历错误/无不可读候选）但未找到任何在盘上游源"
   583	        class_dist[cls] += 1
   584	        recover_dist[recover] += 1
   585	        inline_dist[state] += 1
   586	        stable_key = {
   587	            "line_no": line_no,
   588	            "sha256_prefix": str(rec.get("episode_body_sha256", ""))[:16],
   589	            "request_id": rid,
   590	        }
   591	        if recover == "unrecoverable":
   592	            unrecoverable_keys.append(stable_key)
   593	        elif recover == "unverifiable":
   594	            unverifiable_keys.append(stable_key)
   595	        if sess["attribution_conflict"]:
   596	            attribution_conflicts.append(stable_key)
   597	        ledger_records.append(
   598	            {
   599	                "stable_key": stable_key,
   600	                "name": str(rec.get("name", ""))[:80],
   601	                "group_id": rec.get("group_id"),
   602	                "source_description": rec.get("source_description"),
   603	                "error_type": rec.get("error_type"),
   604	                "error_excerpt": str(rec.get("error", ""))[:120],
   605	                "failed_at": rec.get("failed_at"),
   606	                "reference_time": rec.get("reference_time"),
   607	                "class": cls,
   608	                "episode_body_length": rec.get("episode_body_length"),
   609	                "episode_body_sha256": rec.get("episode_body_sha256"),
   610	                "inline_state": state,
   611	                "sha_check": sha_check,
   612	                "session_token": sess["session_token"],
   613	                "transcript_paths": sess["transcript_paths"],
   614	                "transcript_match_count": sess["transcript_match_count"],
   615	                "attribution_conflict": sess["attribution_conflict"],
   616	                # round-6 LOW 整改: ledger 自描述冲突原因，G4-10 可区分
   617	                # 缺 token / token 冲突 / 扫描受阻 / 不可读 / 多命中
   618	                "attribution_conflict_reason": (
   619	                    "no_token"
   620	                    if sess.get("no_token")
   621	                    else "token_conflict"
   622	                    if sess.get("token_conflict")
   623	                    else "scan_errors"
   624	                    if sess.get("scan_errors")
   625	                    else "stat_failures"
   626	                    if sess.get("stat_failures")
   627	                    else "unreadable_candidates"
   628	                    if sess.get("unreadable_candidates")
   629	                    else "ambiguous_multi_match"
   630	                    if sess["attribution_conflict"]
   631	                    else None
   632	                ),
   633	                "recoverability": recover,
   634	                "recoverability_basis": basis,
   635	            }
   636	        )
   637	
   638	    # 语义重复簇（同 name + 全文 sha + group_id）——G4-10 重放去重策略依据
   639	    cluster_map: dict[tuple, list[int]] = defaultdict(list)
   640	    for line_no, rec in records:
   641	        cluster_map[
   642	            (str(rec.get("name", "")), str(rec.get("episode_body_sha256", "")), str(rec.get("group_id")))
   643	        ].append(line_no)
   644	    duplicate_clusters = [
   645	        {"name": k[0][:80], "episode_body_sha256": k[1], "group_id": k[2], "line_nos": v, "occurrences": len(v)}
   646	        for k, v in sorted(cluster_map.items(), key=lambda kv: -len(kv[1]))
   647	        if len(v) > 1
   648	    ]
   649	
   650	    compare_infos = []
   651	    for cp in args.compare:
   652	        cinfo, cid = describe_copy(Path(cp))
   653	        compare_infos.append(cinfo)
   654	        if cid is not None:
   655	            protected_ids.add(cid)
   656	
   657	    if args.qa_metrics_db:
   658	        qa_probe, qa_identity = probe_qa_metrics(
   659	            Path(args.qa_metrics_db),
   660	            [str(r.get("error_type", "")) for _, r in records],
   661	        )
   662	        if qa_identity is not None:
   663	            protected_ids.add(qa_identity)  # 保护实际验证过的对象身份
   664	    else:
   665	        qa_probe = {"verdict": "skipped_no_db_arg"}
   666	
   667	    deviation = {
   668	        k: {"expected": EXPECTED_CLASS_DIST.get(k, 0), "actual": class_dist.get(k, 0)}
   669	        for k in sorted(set(class_dist) | set(EXPECTED_CLASS_DIST))
   670	        if EXPECTED_CLASS_DIST.get(k, 0) != class_dist.get(k, 0)
   671	    }
   672	
   673	    ledger = {
   674	        "card": "CARD-G4-9",
   675	        "generated_at": datetime.now(timezone.utc).isoformat(),
   676	        "privacy": "private-only: transcript_paths 含本机用户名与 session UUID，禁止外发/公网发布",
   677	        "stable_key_semantics": (
   678	            "冻结快照（dlq_file.sha256）内的 occurrence key；line_no 在快照内唯一，"
   679	            "sha256_prefix/request_id 为冗余对账维度——非跨文件重排或语义幂等键"
   680	        ),
   681	        "dlq_file": dlq_info,
   682	        "compare_copies": compare_infos,
   683	        "total_lines": len(raw_lines),
   684	        "total_records": len(records),
   685	        "unparseable_lines": unparseable,
   686	        # round-2 LOW 整改: 固定 schema 补零，消费者无需自行补齐缺席键
   687	        "class_distribution": {
   688	            k: class_dist.get(k, 0) for k in ["budget_400", "schema_entity_type", "group_id_format", "unexpected"]
   689	        },
   690	        "expected_class_distribution": EXPECTED_CLASS_DIST,
   691	        "class_deviation": deviation,
   692	        "recoverability_distribution": {
   693	            k: recover_dist.get(k, 0) for k in ["byte_exact", "approximate", "unverifiable", "unrecoverable"]
   694	        },
   695	        "inline_state_distribution": {
   696	            k: inline_dist.get(k, 0) for k in ["full_verified", "truncated_prefix", "anomaly"]
   697	        },
   698	        "unrecoverable_list": unrecoverable_keys,
   699	        "unverifiable_list": unverifiable_keys,
   700	        "attribution_conflicts": attribution_conflicts,
   701	        "duplicate_clusters": duplicate_clusters,
   702	        "qa_metrics_probe": qa_probe,
   703	        "records": ledger_records,
   704	    }
   705	
   706	    # round-3 BLOCKER-1 绕过① 整改: 归因到的 transcript 是恢复源，
   707	    # --out 指向它同样会截断。写出前并入保护集（此时归因已完成）。
   708	    for sess_info in group_attribution.values():
   709	        for tpath in sess_info.get("all_candidate_paths", []):
   710	            try:
   711	                tst = os.stat(tpath)
   712	                protected_ids.add((tst.st_dev, tst.st_ino))
   713	            except OSError as e:
   714	                # round-5 整改: 候选 stat 失败不再静默吞 —— 保护集不完整即拒绝写出
   715	                print(f"候选源无法 stat，保护集不完整，拒绝写出: {tpath} ({e})", file=sys.stderr)
   716	                return 2
   717	    for rec_out in ledger_records:
   718	        for tpath in rec_out.get("transcript_paths", []):
   719	            try:
   720	                tst = os.stat(tpath)
   721	                protected_ids.add((tst.st_dev, tst.st_ino))
   722	            except OSError:
   723	                continue
   724	
   725	    try:
   726	        out_json = json.dumps(ledger, ensure_ascii=False, indent=1)
   727	    except (UnicodeEncodeError, ValueError):
   728	        # round-6 LOW 整改: name/error/group_id 等字段若含 escaped lone surrogate，
   729	        # ensure_ascii=False 写出会抛错并拒绝整次 census。回退 ensure_ascii=True
   730	        # （\uXXXX 转义，ASCII 安全）并在台账中显式标注该降级。
   731	        ledger["json_encoding_note"] = "ensure_ascii=True fallback: 某字段含无法 UTF-8 编码的字符（lone surrogate）"
   732	        out_json = json.dumps(ledger, ensure_ascii=True, indent=1)
   733	    if args.out:
   734	        # round-3 整改: 消除 check-then-open TOCTOU。先以 O_NOFOLLOW 打开且
   735	        # **不带 O_TRUNC**，对**实际 fd** fstat 校验 inode；只有校验通过才
   736	        # ftruncate。检查与写入作用于同一 fd，检查后被换 symlink/hardlink 无效。
   737	        try:
   738	            fd = os.open(args.out, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
   739	        except OSError as e:
   740	            print(f"--out 无法安全打开（symlink 或权限）: {args.out} ({e})", file=sys.stderr)
   741	            return 2
   742	        try:
   743	            st = os.fstat(fd)
   744	            # round-4 MEDIUM 整改: 非常规文件（FIFO/设备/socket）拒绝
   745	            if not stat.S_ISREG(st.st_mode):
   746	                print(f"--out 不是常规文件（FIFO/设备/socket），拒绝写出: {args.out}", file=sys.stderr)
   747	                return 2
   748	            # round-5 HIGH 整改: 碰撞检查必须**先于** fchmod —— 否则 --out 指向
   749	            # 受保护的 0644 输入时，会先把只读输入的权限改成 0600 再拒绝。
   750	            if (st.st_dev, st.st_ino) in protected_ids:
   751	                print(
   752	                    f"--out 打开后经 fstat 判定与输入文件同一 inode，拒绝写出（防截断）: {args.out}",
   753	                    file=sys.stderr,
   754	                )
   755	                return 2
   756	            # 碰撞检查通过后才收紧权限（round-4 LOW: 0o600 只作用于新建）
   757	            if st.st_mode & 0o077:
   758	                os.fchmod(fd, 0o600)
   759	            os.ftruncate(fd, 0)
   760	            with os.fdopen(fd, "w", encoding="utf-8", closefd=True) as f:
   761	                fd = -1  # 所有权移交 fdopen
   762	                f.write(out_json + "\n")
   763	        finally:
   764	            if fd >= 0:
   765	                os.close(fd)
   766	        print(f"台账已写入: {args.out}")
   767	    else:
   768	        print(out_json)
   769	
   770	    print(
   771	        f"census: {len(records)} 条 (+{len(unparseable)} unparseable) | class={dict(class_dist)} | "
   772	        f"recoverability={dict(recover_dist)} | 归因冲突={len(attribution_conflicts)} | "
   773	        f"重复簇={len(duplicate_clusters)} | 偏差={deviation or '无'} | "
   774	        f"qa_metrics 核销={qa_probe.get('verdict')}",
   775	        file=sys.stderr,
   776	    )
   777	    return 0
   778	
   779	
   780	if __name__ == "__main__":
   781	    sys.exit(main())

exec
/bin/zsh -lc "stat -f '%N|mode=%Sp|dev=%d|ino=%i|nlink=%l|size=%z' backend/scripts/census_dead_letter_episodes.py '_bmad-output/审查/G4-9-evidence/grep-selfattest.txt'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
backend/scripts/census_dead_letter_episodes.py|mode=-rw-r--r--|dev=16777230|ino=23060568|nlink=1|size=37213
_bmad-output/审查/G4-9-evidence/grep-selfattest.txt|mode=-rw-r--r--|dev=16777230|ino=22958315|nlink=1|size=3844

**Inspecting round6 file for final lines**
**Extracting script ranges and listing artifacts**
exec
/bin/zsh -lc "sed -n '150,270p' backend/scripts/census_dead_letter_episodes.py" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
exec
/bin/zsh -lc "sed -n '700,770p' backend/scripts/census_dead_letter_episodes.py" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
exec
/bin/zsh -lc "sed -n '360,475p' backend/scripts/census_dead_letter_episodes.py" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
exec
/bin/zsh -lc 'git diff --unified=50 4c125f19 5b371253 -- backend/scripts/census_dead_letter_episodes.py' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
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
            except OSError as e:
                # round-5 整改: 候选 stat 失败不再静默吞 —— 保护集不完整即拒绝写出
                print(f"候选源无法 stat，保护集不完整，拒绝写出: {tpath} ({e})", file=sys.stderr)
                return 2
    for rec_out in ledger_records:
        for tpath in rec_out.get("transcript_paths", []):
            try:
                tst = os.stat(tpath)
                protected_ids.add((tst.st_dev, tst.st_ino))
            except OSError:
                continue

    try:
        out_json = json.dumps(ledger, ensure_ascii=False, indent=1)
    except (UnicodeEncodeError, ValueError):
        # round-6 LOW 整改: name/error/group_id 等字段若含 escaped lone surrogate，
        # ensure_ascii=False 写出会抛错并拒绝整次 census。回退 ensure_ascii=True
        # （\uXXXX 转义，ASCII 安全）并在台账中显式标注该降级。
        ledger["json_encoding_note"] = "ensure_ascii=True fallback: 某字段含无法 UTF-8 编码的字符（lone surrogate）"
        out_json = json.dumps(ledger, ensure_ascii=True, indent=1)
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
            # round-5 HIGH 整改: 碰撞检查必须**先于** fchmod —— 否则 --out 指向
            # 受保护的 0644 输入时，会先把只读输入的权限改成 0600 再拒绝。
            if (st.st_dev, st.st_ino) in protected_ids:
                print(
                    f"--out 打开后经 fstat 判定与输入文件同一 inode，拒绝写出（防截断）: {args.out}",
                    file=sys.stderr,
                )
                return 2
            # 碰撞检查通过后才收紧权限（round-4 LOW: 0o600 只作用于新建）
            if st.st_mode & 0o077:
                os.fchmod(fd, 0o600)
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

 succeeded in 0ms:
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
            f"transcripts 根目录不存在/不可见: {transcripts_dir} —— 拒绝在源不可见时裁定可恢复性（fail-closed）",
            file=sys.stderr,
        )
        return 2
    # round-2 HIGH-3 整改: 存在但不可读/不可遍历的根（chmod 000）此前 exit 0
    # 并把全部记录假判 unrecoverable —— 同样 fail-closed 拒诊。
    if not os.access(transcripts_dir, os.R_OK | os.X_OK):
        print(
            f"transcripts 根目录不可读/不可遍历: {transcripts_dir} —— 拒绝在源不可见时裁定可恢复性（fail-closed）",
            file=sys.stderr,
        )
        return 2

    protected_ids: set[tuple[int, int]] = set()
    # round-6 BLOCKER①② 架构整改: inode 保护集依赖**枚举完整性**（不可列举的
    # 子目录、ABA 换 inode 都能让某个真实源不进集合）。故增加**不依赖枚举**的
    # 路径层防御：--out 的 realpath 不得落在 transcripts 根内、不得等于任一
    # 输入路径。路径层 + inode 层双保险，任一命中即拒绝。
    if args.out:
        out_real = os.path.realpath(args.out)
        tr_real = os.path.realpath(args.transcripts_dir)
        tr_prefix = tr_real if tr_real.endswith(os.sep) else tr_real + os.sep
        if out_real == tr_real or out_real.startswith(tr_prefix):
            print(
                f"--out 落在 transcripts 根内（恢复源区域），无条件拒绝写出: {args.out}",
                file=sys.stderr,
            )
            return 2
        input_reals = {os.path.realpath(args.dlq)} | {os.path.realpath(c) for c in args.compare}
        if args.qa_metrics_db:
            input_reals.add(os.path.realpath(args.qa_metrics_db))
        if out_real in input_reals:
            print(f"--out 与输入文件路径相同（realpath 比较），拒绝写出: {args.out}", file=sys.stderr)
            return 2

    # --out 碰撞守卫（写前）。round-2 BLOCKER-1 整改: 比较**文件身份**
    # (st_dev, st_ino) 而非 resolve() 字符串 —— 后者对 hardlink 与
    # 大小写不敏感文件系统上的 case-only 别名均失效（Codex 实测截断输入）。
    if args.out:
        out_path = Path(args.out)
        protected_paths = [dlq_path, *(Path(p) for p in args.compare)]
        if args.qa_metrics_db:
            protected_paths.append(Path(args.qa_metrics_db))
        for candidate in protected_paths:
            try:
                cst = candidate.stat()  # 跟随 symlink: 保护的是最终目标身份
                protected_ids.add((cst.st_dev, cst.st_ino))
            except OSError:
                # round-4 整改: stat 失败不再静默吞 —— 无法确认身份即 fail-closed
                print(f"输入文件无法 stat，拒绝继续（无法建立完整保护集）: {candidate}", file=sys.stderr)
                return 2
        # 路径字符串比较作为第二道（输出文件尚不存在时 stat 无身份可比）
        out_resolved = out_path.resolve()
        if out_resolved in {p.resolve() for p in protected_paths}:
            print(f"--out 与输入文件路径重合，拒绝写出（防截断）: {out_resolved}", file=sys.stderr)
            return 2
        if out_path.exists():
            try:
                out_st = out_path.stat()
            except OSError as e:
                print(f"--out 无法 stat，拒绝写出: {out_path} ({e})", file=sys.stderr)
                return 2
            if (out_st.st_dev, out_st.st_ino) in protected_ids:
                print(
                    f"--out 与输入文件为同一 inode（hardlink/大小写别名），拒绝写出（防截断）: {out_path}",
                    file=sys.stderr,
                )
                return 2

 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
diff --git a/backend/scripts/census_dead_letter_episodes.py b/backend/scripts/census_dead_letter_episodes.py
index c1c1346b..3ea39acb 100644
--- a/backend/scripts/census_dead_letter_episodes.py
+++ b/backend/scripts/census_dead_letter_episodes.py
@@ -151,314 +151,342 @@ def full_body_verified(rec: dict) -> bool:
     try:
         full_bytes = full.encode("utf-8")
     except UnicodeEncodeError:
         return False
     return hashlib.sha256(full_bytes).hexdigest() == declared_sha
 
 
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
     """组级归因，fail-closed。
 
     round-5 BLOCKER① 整改: **先扫描后判定**。原实现在 token 冲突/无 token 时
     扫描前早退，导致这些候选从未进入 all_candidate_paths → 不进 --out 保护集
     → 可被无竞态截断。现无条件对每个 token 扫描收集候选（保护集所需），
     再做冲突/唯一性判定。
     """
     result = {
         "session_token": None,
         "transcript_paths": [],
         "transcript_exists": False,
         "transcript_match_count": 0,
         "attribution_conflict": False,
         # 保护集必须覆盖**所有见到的候选**（含不可读、含被冲突分支排除的）
         "all_candidate_paths": [],
     }
     uniq = sorted(set(tokens), key=len)
 
     root_real = os.path.realpath(transcripts_dir)
     root_prefix = root_real if root_real.endswith(os.sep) else root_real + os.sep
     walk_errors: list[str] = []
 
     def _on_walk_error(err: OSError) -> None:
         walk_errors.append(f"{getattr(err, 'filename', '?')}: {err}")
 
     # 单次遍历收集**每个 token** 的候选（无条件，供保护集与判定共用）
     per_token: dict[str, list[str]] = {t: [] for t in uniq}
     all_candidates: list[str] = []
     unreadable: list[str] = []
     stat_failures: list[str] = []
-    if uniq:
-        for dirpath, _dirnames, filenames in os.walk(transcripts_dir, onerror=_on_walk_error, followlinks=False):
-            for fname in filenames:
-                if not fname.endswith(".jsonl"):
-                    continue
+    # round-6 整改: **无论有无 token 都遍历** —— no_token 时原实现完全不扫描，
+    # all_candidate_paths 为空，该组见不到的候选就进不了保护集。
+    for dirpath, _dirnames, filenames in os.walk(transcripts_dir, onerror=_on_walk_error, followlinks=False):
+        for fname in filenames:
+            if fname.endswith(".jsonl"):
                 matched = [t for t in uniq if fname.startswith(t)]
-                if not matched:
-                    continue
                 candidate = os.path.join(dirpath, fname)
                 # 候选一律入 all_candidate_paths（保护集口径），再谈可用性
                 all_candidates.append(candidate)
+                if not matched:
+                    continue
                 try:
                     if os.path.islink(candidate) or not os.path.isfile(candidate):
                         continue
                 except OSError as e:
                     stat_failures.append(f"{candidate}: {e}")
                     continue
                 if not os.access(candidate, os.R_OK):
                     unreadable.append(candidate)
                     continue
                 real = os.path.realpath(candidate)
                 if not real.startswith(root_prefix):
                     continue  # 目录 symlink 逃逸
                 for t in matched:
                     per_token[t].append(candidate)
     result["all_candidate_paths"] = sorted(set(all_candidates))
 
     if not uniq:
         # 无 token: 未做任何归因扫描 —— 不是"确认无源"（round-5 MEDIUM 整改）
         result["attribution_conflict"] = True
         result["no_token"] = True
         return result
 
     longest = uniq[-1]
     if any(not longest.startswith(t) for t in uniq[:-1]):
         result["attribution_conflict"] = True
         result["token_conflict"] = True
         return result
     result["session_token"] = longest
 
     if walk_errors:
         result["scan_errors"] = walk_errors[:5]
         result["attribution_conflict"] = True
         return result
     if stat_failures:
         result["stat_failures"] = stat_failures[:5]
         result["attribution_conflict"] = True
         return result
     if unreadable:
         result["unreadable_candidates"] = unreadable[:5]
         result["attribution_conflict"] = True
         return result
 
     matches = sorted(set(per_token[longest]))
     result["transcript_paths"] = matches
     result["transcript_match_count"] = len(matches)
     if len(matches) == 1:
         result["transcript_exists"] = True
     elif len(matches) > 1:
         result["attribution_conflict"] = True  # ambiguous 多命中，拒绝采信
     return result
 
 
 def probe_qa_metrics(db_path: Path, error_types: list[str]) -> tuple[dict, tuple[int, int] | None]:
     """只读核销 qa_metrics.db（URI mode=ro，无写路径）。返回 (结果, 实际身份)。
 
     round-5 BLOCKER②/MEDIUM 整改: 原实现按路径 stat 取身份、SQLite 稍后按路径
     重新打开 —— 两者可能不是同一对象，且无 regular-file/nonblocking 门（FIFO
     会阻塞）。现: fd 打开取 fstat 身份 + S_ISREG 门 → SQLite 打开 → 复核路径
     身份仍等于该身份，不等即拒绝（不采信被换入的对象）。
     """
     result: dict = {"db_path": str(db_path), "opened_readonly": False}
     if not db_path.exists():
         result["verdict"] = "db_missing"
         return result, None
     try:
         fd = os.open(db_path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
     except OSError as e:
         result["verdict"] = f"open_refused: {e}"
         return result, None
+    # round-6 BLOCKER② 整改: 验证 fd **保持打开**直到 SQLite 连接建立并复核完毕
+    # —— 原实现验证后即关闭，SQLite 按路径重开可被 A→B→A 的 ABA 骗过。
+    conn = None
     try:
         st = os.fstat(fd)
         if not stat.S_ISREG(st.st_mode):
             result["verdict"] = "not_regular_file_refused"
             return result, None
         identity = (st.st_dev, st.st_ino)
-    finally:
-        os.close(fd)
 
-    uri = f"file:{db_path}?mode=ro"
-    conn = sqlite3.connect(uri, uri=True)
-    try:
-        # 复核 SQLite 实际打开的路径身份仍是我们验证过的对象
+        uri = f"file:{db_path}?mode=ro"
+        conn = sqlite3.connect(uri, uri=True)
+        # 连接建立后在**持有验证 fd 的同时**复核路径身份
         try:
             recheck = os.stat(db_path)
         except OSError as e:
             result["verdict"] = f"recheck_stat_failed: {e}"
             return result, identity
         if (recheck.st_dev, recheck.st_ino) != identity:
             result["verdict"] = "identity_changed_between_verify_and_open_refused"
             return result, identity
+        # 再次 fstat 验证 fd：确认它仍指向同一对象且未被 unlink 替换
+        st2 = os.fstat(fd)
+        if (st2.st_dev, st2.st_ino) != identity or st2.st_nlink == 0:
+            result["verdict"] = "verified_fd_invalidated_refused"
+            return result, identity
         result["opened_readonly"] = True
         result["file_identity_verified"] = True
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
-        conn.close()
+        if conn is not None:
+            conn.close()
+        os.close(fd)
     return result, identity
 
 
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
             f"transcripts 根目录不存在/不可见: {transcripts_dir} —— 拒绝在源不可见时裁定可恢复性（fail-closed）",
             file=sys.stderr,
         )
         return 2
     # round-2 HIGH-3 整改: 存在但不可读/不可遍历的根（chmod 000）此前 exit 0
     # 并把全部记录假判 unrecoverable —— 同样 fail-closed 拒诊。
     if not os.access(transcripts_dir, os.R_OK | os.X_OK):
         print(
             f"transcripts 根目录不可读/不可遍历: {transcripts_dir} —— 拒绝在源不可见时裁定可恢复性（fail-closed）",
             file=sys.stderr,
         )
         return 2
 
     protected_ids: set[tuple[int, int]] = set()
+    # round-6 BLOCKER①② 架构整改: inode 保护集依赖**枚举完整性**（不可列举的
+    # 子目录、ABA 换 inode 都能让某个真实源不进集合）。故增加**不依赖枚举**的
+    # 路径层防御：--out 的 realpath 不得落在 transcripts 根内、不得等于任一
+    # 输入路径。路径层 + inode 层双保险，任一命中即拒绝。
+    if args.out:
+        out_real = os.path.realpath(args.out)
+        tr_real = os.path.realpath(args.transcripts_dir)
+        tr_prefix = tr_real if tr_real.endswith(os.sep) else tr_real + os.sep
+        if out_real == tr_real or out_real.startswith(tr_prefix):
+            print(
+                f"--out 落在 transcripts 根内（恢复源区域），无条件拒绝写出: {args.out}",
+                file=sys.stderr,
+            )
+            return 2
+        input_reals = {os.path.realpath(args.dlq)} | {os.path.realpath(c) for c in args.compare}
+        if args.qa_metrics_db:
+            input_reals.add(os.path.realpath(args.qa_metrics_db))
+        if out_real in input_reals:
+            print(f"--out 与输入文件路径相同（realpath 比较），拒绝写出: {args.out}", file=sys.stderr)
+            return 2
+
     # --out 碰撞守卫（写前）。round-2 BLOCKER-1 整改: 比较**文件身份**
     # (st_dev, st_ino) 而非 resolve() 字符串 —— 后者对 hardlink 与
     # 大小写不敏感文件系统上的 case-only 别名均失效（Codex 实测截断输入）。
     if args.out:
         out_path = Path(args.out)
         protected_paths = [dlq_path, *(Path(p) for p in args.compare)]
         if args.qa_metrics_db:
             protected_paths.append(Path(args.qa_metrics_db))
         for candidate in protected_paths:
             try:
                 cst = candidate.stat()  # 跟随 symlink: 保护的是最终目标身份
                 protected_ids.add((cst.st_dev, cst.st_ino))
             except OSError:
                 # round-4 整改: stat 失败不再静默吞 —— 无法确认身份即 fail-closed
                 print(f"输入文件无法 stat，拒绝继续（无法建立完整保护集）: {candidate}", file=sys.stderr)
                 return 2
         # 路径字符串比较作为第二道（输出文件尚不存在时 stat 无身份可比）
         out_resolved = out_path.resolve()
         if out_resolved in {p.resolve() for p in protected_paths}:
             print(f"--out 与输入文件路径重合，拒绝写出（防截断）: {out_resolved}", file=sys.stderr)
             return 2
         if out_path.exists():
             try:
                 out_st = out_path.stat()
             except OSError as e:
                 print(f"--out 无法 stat，拒绝写出: {out_path} ({e})", file=sys.stderr)
                 return 2
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
@@ -538,192 +566,216 @@ def main(argv: list[str] | None = None) -> int:
             else:
                 why = "transcript 多命中 ambiguous"
             extra = "；inline 亦对不上账（anomaly）" if state == "anomaly" else ""
             basis = f"源可见性不足，拒绝裁定：{why}{extra}。既不宣称可恢复，也不宣称不可恢复（fail-closed）"
         elif state == "anomaly":
             recover = "unrecoverable"
             basis = "inline 对不上账（anomaly：sha/长度与声明不符），且归因扫描完整可见但无可用源"
         elif sess["transcript_exists"]:
             recover = "approximate"
             basis = (
                 f"inline 为 200 字符前缀（前缀性质依赖 to_dict()[:200] 生产不变量，sha 无法直接证明）；"
                 f"经 request_id 组归因到唯一在盘 transcript {sess['session_token']}"
                 f"（归因 ≠ 内容已验证——本工具未读 transcript 内容；G4-10 可重蒸馏/重格式化近似重建，非逐字节保证）"
             )
         else:
             recover = "unrecoverable"
             basis = "inline 截断；归因扫描完整可见（无遍历错误/无不可读候选）但未找到任何在盘上游源"
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
+                # round-6 LOW 整改: ledger 自描述冲突原因，G4-10 可区分
+                # 缺 token / token 冲突 / 扫描受阻 / 不可读 / 多命中
+                "attribution_conflict_reason": (
+                    "no_token"
+                    if sess.get("no_token")
+                    else "token_conflict"
+                    if sess.get("token_conflict")
+                    else "scan_errors"
+                    if sess.get("scan_errors")
+                    else "stat_failures"
+                    if sess.get("stat_failures")
+                    else "unreadable_candidates"
+                    if sess.get("unreadable_candidates")
+                    else "ambiguous_multi_match"
+                    if sess["attribution_conflict"]
+                    else None
+                ),
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
 
     if args.qa_metrics_db:
         qa_probe, qa_identity = probe_qa_metrics(
             Path(args.qa_metrics_db),
             [str(r.get("error_type", "")) for _, r in records],
         )
         if qa_identity is not None:
             protected_ids.add(qa_identity)  # 保护实际验证过的对象身份
     else:
         qa_probe = {"verdict": "skipped_no_db_arg"}
 
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
             except OSError as e:
                 # round-5 整改: 候选 stat 失败不再静默吞 —— 保护集不完整即拒绝写出
                 print(f"候选源无法 stat，保护集不完整，拒绝写出: {tpath} ({e})", file=sys.stderr)
                 return 2
     for rec_out in ledger_records:
         for tpath in rec_out.get("transcript_paths", []):
             try:
                 tst = os.stat(tpath)
                 protected_ids.add((tst.st_dev, tst.st_ino))
             except OSError:
                 continue
 
-    out_json = json.dumps(ledger, ensure_ascii=False, indent=1)
+    try:
+        out_json = json.dumps(ledger, ensure_ascii=False, indent=1)
+    except (UnicodeEncodeError, ValueError):
+        # round-6 LOW 整改: name/error/group_id 等字段若含 escaped lone surrogate，
+        # ensure_ascii=False 写出会抛错并拒绝整次 census。回退 ensure_ascii=True
+        # （\uXXXX 转义，ASCII 安全）并在台账中显式标注该降级。
+        ledger["json_encoding_note"] = "ensure_ascii=True fallback: 某字段含无法 UTF-8 编码的字符（lone surrogate）"
+        out_json = json.dumps(ledger, ensure_ascii=True, indent=1)
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
             # round-5 HIGH 整改: 碰撞检查必须**先于** fchmod —— 否则 --out 指向
             # 受保护的 0644 输入时，会先把只读输入的权限改成 0600 再拒绝。
             if (st.st_dev, st.st_ino) in protected_ids:
                 print(
                     f"--out 打开后经 fstat 判定与输入文件同一 inode，拒绝写出（防截断）: {args.out}",
                     file=sys.stderr,
                 )
                 return 2
             # 碰撞检查通过后才收紧权限（round-4 LOW: 0o600 只作用于新建）
             if st.st_mode & 0o077:
                 os.fchmod(fd, 0o600)
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

 succeeded in 0ms:
        return False
    try:
        full_bytes = full.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return hashlib.sha256(full_bytes).hexdigest() == declared_sha


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
    """组级归因，fail-closed。

    round-5 BLOCKER① 整改: **先扫描后判定**。原实现在 token 冲突/无 token 时
    扫描前早退，导致这些候选从未进入 all_candidate_paths → 不进 --out 保护集
    → 可被无竞态截断。现无条件对每个 token 扫描收集候选（保护集所需），
    再做冲突/唯一性判定。
    """
    result = {
        "session_token": None,
        "transcript_paths": [],
        "transcript_exists": False,
        "transcript_match_count": 0,
        "attribution_conflict": False,
        # 保护集必须覆盖**所有见到的候选**（含不可读、含被冲突分支排除的）
        "all_candidate_paths": [],
    }
    uniq = sorted(set(tokens), key=len)

    root_real = os.path.realpath(transcripts_dir)
    root_prefix = root_real if root_real.endswith(os.sep) else root_real + os.sep
    walk_errors: list[str] = []

    def _on_walk_error(err: OSError) -> None:
        walk_errors.append(f"{getattr(err, 'filename', '?')}: {err}")

    # 单次遍历收集**每个 token** 的候选（无条件，供保护集与判定共用）
    per_token: dict[str, list[str]] = {t: [] for t in uniq}
    all_candidates: list[str] = []
    unreadable: list[str] = []
    stat_failures: list[str] = []
    # round-6 整改: **无论有无 token 都遍历** —— no_token 时原实现完全不扫描，
    # all_candidate_paths 为空，该组见不到的候选就进不了保护集。
    for dirpath, _dirnames, filenames in os.walk(transcripts_dir, onerror=_on_walk_error, followlinks=False):
        for fname in filenames:
            if fname.endswith(".jsonl"):
                matched = [t for t in uniq if fname.startswith(t)]
                candidate = os.path.join(dirpath, fname)
                # 候选一律入 all_candidate_paths（保护集口径），再谈可用性
                all_candidates.append(candidate)
                if not matched:
                    continue
                try:
                    if os.path.islink(candidate) or not os.path.isfile(candidate):
                        continue
                except OSError as e:
                    stat_failures.append(f"{candidate}: {e}")
                    continue
                if not os.access(candidate, os.R_OK):
                    unreadable.append(candidate)
                    continue
                real = os.path.realpath(candidate)
                if not real.startswith(root_prefix):
                    continue  # 目录 symlink 逃逸
                for t in matched:
                    per_token[t].append(candidate)
    result["all_candidate_paths"] = sorted(set(all_candidates))

    if not uniq:
        # 无 token: 未做任何归因扫描 —— 不是"确认无源"（round-5 MEDIUM 整改）
        result["attribution_conflict"] = True
        result["no_token"] = True
        return result

    longest = uniq[-1]
    if any(not longest.startswith(t) for t in uniq[:-1]):
        result["attribution_conflict"] = True
        result["token_conflict"] = True
        return result
    result["session_token"] = longest

    if walk_errors:
        result["scan_errors"] = walk_errors[:5]
        result["attribution_conflict"] = True
        return result
    if stat_failures:
        result["stat_failures"] = stat_failures[:5]
        result["attribution_conflict"] = True
        return result
    if unreadable:
        result["unreadable_candidates"] = unreadable[:5]
        result["attribution_conflict"] = True
        return result

    matches = sorted(set(per_token[longest]))
    result["transcript_paths"] = matches
    result["transcript_match_count"] = len(matches)
    if len(matches) == 1:
        result["transcript_exists"] = True
    elif len(matches) > 1:
        result["attribution_conflict"] = True  # ambiguous 多命中，拒绝采信
    return result


def probe_qa_metrics(db_path: Path, error_types: list[str]) -> tuple[dict, tuple[int, int] | None]:
    """只读核销 qa_metrics.db（URI mode=ro，无写路径）。返回 (结果, 实际身份)。

    round-5 BLOCKER②/MEDIUM 整改: 原实现按路径 stat 取身份、SQLite 稍后按路径
    重新打开 —— 两者可能不是同一对象，且无 regular-file/nonblocking 门（FIFO
    会阻塞）。现: fd 打开取 fstat 身份 + S_ISREG 门 → SQLite 打开 → 复核路径
    身份仍等于该身份，不等即拒绝（不采信被换入的对象）。

exec
/bin/zsh -lc "tail -n 140 '_bmad-output/审查/codex-review-CARD-G4-9-round6.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
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



exec
/bin/zsh -lc "nl -ba '_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
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
    10	d2827a6d  CARD-G4-9 round-4 整改
    11	d8d887f2  本 receipt 首次落盘
    12	4c125f19  CARD-G4-9 round-5 整改
    13	5b371253  CARD-G4-9 round-6 架构级修复（本 receipt 当前版所描述的 commit）
    14	
    15	各阶段交付物 blob 可用 git cat-file 复核；台账头部 dlq_file.sha256 为 DLQ 快照指纹。

exec
/bin/zsh -lc "nl -ba '_bmad-output/审查/G4-9-evidence/grep-selfattest.txt'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
     1	== CARD-G4-9 只读自证（round-6 整改版）==
     2	脚本 sha256: 533d0d4ce6da9ace21e19e2ccd55844b1b5ffa6f8f292b8ed0695956ff9e3585
     3	生成时点: round-6 整改后（本文件随每轮整改重生成——round-6 MEDIUM 指出过漂移）
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
    24	--- (4) 唯一写出口（os.fdopen；其余 open 全为读）:
    25	760:            with os.fdopen(fd, "w", encoding="utf-8", closefd=True) as f:
    26	--- (5) --out 双层防御 · 路径层（不依赖枚举完整性，round-6 架构整改）:
    27	424:    # 路径层防御：--out 的 realpath 不得落在 transcripts 根内、不得等于任一
    28	427:        out_real = os.path.realpath(args.out)
    29	430:        if out_real == tr_real or out_real.startswith(tr_prefix):
    30	432:                f"--out 落在 transcripts 根内（恢复源区域），无条件拒绝写出: {args.out}",
    31	439:        if out_real in input_reals:
    32	440:            print(f"--out 与输入文件路径相同（realpath 比较），拒绝写出: {args.out}", file=sys.stderr)
    33	--- (6) --out 双层防御 · inode 层（O_NOFOLLOW+O_NONBLOCK → fstat → S_ISREG → 碰撞检查 → fchmod → ftruncate）:
    34	269:    会阻塞）。现: fd 打开取 fstat 身份 + S_ISREG 门 → SQLite 打开 → 复核路径
    35	286:        if not stat.S_ISREG(st.st_mode):
    36	340:        if not stat.S_ISREG(st.st_mode):
    37	470:            if (out_st.st_dev, out_st.st_ino) in protected_ids:
    38	738:            fd = os.open(args.out, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    39	745:            if not stat.S_ISREG(st.st_mode):
    40	750:            if (st.st_dev, st.st_ino) in protected_ids:
    41	758:                os.fchmod(fd, 0o600)
    42	759:            os.ftruncate(fd, 0)
    43	--- (7) 读侧身份绑定（实际读取对象入保护集；QA DB 验证 fd 保持打开至复核完毕）:
    44	277:        fd = os.open(db_path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    45	289:        identity = (st.st_dev, st.st_ino)
    46	305:            result["verdict"] = "verified_fd_invalidated_refused"
    47	337:    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    48	342:        identity = (st.st_dev, st.st_ino)
    49	454:                protected_ids.add((cst.st_dev, cst.st_ino))
    50	483:    protected_ids.add(dlq_identity)  # 保护的是**实际读取对象**，非路径快照
    51	655:            protected_ids.add(cid)
    52	663:            protected_ids.add(qa_identity)  # 保护实际验证过的对象身份
    53	712:                protected_ids.add((tst.st_dev, tst.st_ino))
    54	721:                protected_ids.add((tst.st_dev, tst.st_ino))
    55	--- (8) fail-closed 判定门:
    56	96:            out.append(("", f"utf8_decode_error: {e}"))
    57	126:    except UnicodeEncodeError:
    58	129:    len_ok = isinstance(declared_len, int) and not isinstance(declared_len, bool)
    59	149:    if not isinstance(declared_len, int) or isinstance(declared_len, bool) or len(full) != declared_len:
    60	153:    except UnicodeEncodeError:
    61	213:                    if os.path.islink(candidate) or not os.path.isfile(candidate):
    62	218:                if not os.access(candidate, os.R_OK):
    63	230:        result["attribution_conflict"] = True
    64	236:        result["attribution_conflict"] = True
    65	243:        result["attribution_conflict"] = True
    66	247:        result["attribution_conflict"] = True
    67	251:        result["attribution_conflict"] = True
    68	260:        result["attribution_conflict"] = True  # ambiguous 多命中，拒绝采信
    69	414:    if not os.access(transcripts_dir, os.R_OK | os.X_OK):

exec
/bin/zsh -lc "sed -n '1,180p' '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
{
 "card": "CARD-G4-9",
 "generated_at": "2026-08-28T12:47:55.648376+00:00",
 "privacy": "private-only: transcript_paths 含本机用户名与 session UUID，禁止外发/公网发布",
 "stable_key_semantics": "冻结快照（dlq_file.sha256）内的 occurrence key；line_no 在快照内唯一，sha256_prefix/request_id 为冗余对账维度——非跨文件重排或语义幂等键",
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
 "expected_class_distribution": {
  "budget_400": 89,
  "schema_entity_type": 2,
  "group_id_format": 1
 },
 "class_deviation": {},
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
 "unrecoverable_list": [],
 "unverifiable_list": [],
 "attribution_conflicts": [
  {
   "line_no": 1,
   "sha256_prefix": "7e33da5e96e6239f",
   "request_id": "281466113679440"
  },
  {
   "line_no": 2,
   "sha256_prefix": "b91bf262cadab596",
   "request_id": "281466014769488"
  },
  {
   "line_no": 3,
   "sha256_prefix": "55b1b793b99778eb",
   "request_id": "281466427090256"
  }
 ],
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
  },
  {
   "name": "conversation_distillation:Distilled summary for node session:426ff",
   "episode_body_sha256": "288e4b506e72402e22c8b08fa9608c8dc9e1870ccdd43ed4ab93c95655435064",
   "group_id": "vault:canvas_vault",
   "line_nos": [
    16,
    64
   ],
   "occurrences": 2
  },
  {
   "name": "qa_highlight:Q: What is the relationship between a co",
   "episode_body_sha256": "04e26b3060192bc9de508b2e75c508fba86553a82bea1e910bc24771c75834b5",
   "group_id": "vault:canvas_vault",
   "line_nos": [
    37,
    86
   ],
   "occurrences": 2
  }
 ],
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
 },
 "records": [
  {

exec
/bin/zsh -lc "shasum -a 256 backend/scripts/census_dead_letter_episodes.py '_bmad-output/审查/G4-9-evidence/grep-selfattest.txt' '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' '_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
533d0d4ce6da9ace21e19e2ccd55844b1b5ffa6f8f292b8ed0695956ff9e3585  backend/scripts/census_dead_letter_episodes.py
78337970dd26b96da707c75c55debcb482e253bf6ace9f905c7fc697142f407a  _bmad-output/审查/G4-9-evidence/grep-selfattest.txt
7eb35b53d021f1497cf253a8656b2f67c60680aeece87f0ce174ad35f323cc9b  _bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json
b269372f64018660f80d645cc9ae673c6744f7a31661bb661b13f2174af745a7  _bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt

**Identifying TOCTOU vulnerability in output open**
**Analyzing symlink and hardlink TOCTOU bypass scenarios**
**Confirming hardlink protection gap remains**
**Assessing output path security risks**
**Examining file descriptor and rename race conditions**
**Evaluating inode verification via /proc and /dev/fd**
**Evaluating SQLite deserialization and locking challenges**
**Analyzing unresolved QA DB URI encoding blocker**
**Planning grep extraction for QA DB summary**
**Inspecting no_token scan behavior**
**Analyzing lone surrogate JSON encoding issue**
**Confirming UTF-8 print error on lone surrogates**
**Verifying commit hash consistency**
**Assessing read permissions for ledger recompute**
**Restricting recompute to ledger data**
**Confirming authorized ledger recompute scope**
**Planning read-only static path analysis**
**Verifying script syntax without writes**
**Planning memory and skill line citations**
**Deciding on browsing official SQLite docs**
**Planning targeted web searches for SQLite and Python docs**
exec
/bin/zsh -lc "wc -l '_bmad-output/审查/codex-review-CARD-G4-9-round6.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
    4559 _bmad-output/审查/codex-review-CARD-G4-9-round6.md

exec
/bin/zsh -lc "awk 'NR>=4450 {printf \"%6d\\t%s\\n\", NR, "'$0}'"' '_bmad-output/审查/codex-review-CARD-G4-9-round6.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
  4450	| 5. QA DB 特殊文件门 | **NOT-CLOSED / PARTIAL · MEDIUM** | 第一次 `O_NONBLOCK+S_ISREG` 能拒绝稳定 FIFO/设备；但 fd 随即关闭，SQLite 第二次按路径打开没有这些门。regular→FIFO/symlink 替换仍可绕过并在 `connect()` 内阻塞。 |
  4451	| 6. no_token→unverifiable | **CLOSED（行为）** | 非 byte-exact 的 no-token 记录会进入 `unverifiable`；full-verified/no-token 仍为 byte-exact，语义正确。[no_token](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:228)。但 `no_token` 未写入 ledger，见下方 LOW。 |
  4452	| 7a. 单独 LF | **CLOSED** | 纯内存复算：`b""→0`、`b"\n"→1`、`b"\n\n"→2`、`b"{}\n"→1`。[实现](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:85)。 |
  4453	| 7b. strict encode | **CLOSED（原反例）** | lone `U+D800` 配旧 replace-hash 现为 `anomaly/FAIL`，full-body 为 `False`；正常 emoji 正控仍通过。[inline](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:124)、[full-body](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:151)。 |
  4454	| 7c. bool 长度门 | **CLOSED** | `True/False/1.0` 均被拒，整数 `1` 正控通过。[inline 门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:129)、[full-body 门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:148)。 |
  4455	
  4456	### QA DB 新的确定性 BLOCKER
  4457	
  4458	[line 290](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:290)直接拼接：
  4459	
  4460	```python
  4461	uri = f"file:{db_path}?mode=ro"
  4462	```
  4463	
  4464	合法文件名中的 `?`/`#` 未转义。例如验证对象是 `/x/qa#tag`，SQLite URI 实际 path 是 `/x/qa`，`#tag?mode=ro` 被当作 fragment 忽略；这不仅打开不同对象，还丢失 `mode=ro`，可能隐式创建数据库。SQLite 官方要求把普通文件名中的 `?/#` 转义，并规定 fragment 被忽略；Python `connect()` 默认可创建不存在的数据库。[SQLite URI 规则](https://sqlite.org/uri.html#the_uri_path)、[Python sqlite3.connect](https://docs.python.org/3/library/sqlite3.html#sqlite3.connect)。
  4465	
  4466	这是无需竞态的零写入反例，足以单独维持 BLOCKER。
  4467	
  4468	### 台账独立复算
  4469	
  4470	未把生成器当 oracle，直接从 live DLQ exact bytes 重写分帧、分类、SHA/长度、分组和聚簇算法：
  4471	
  4472	- SHA-256：`3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590`
  4473	- `99,915 bytes`；92 records；unparseable 0
  4474	- class：`89 / 2 / 1`
  4475	- inline：4 full_verified / 88 truncated / 0 anomaly
  4476	- recoverability：4 byte_exact / 88 approximate / 0 unverifiable / 0 unrecoverable
  4477	- 重复簇：6/29，簇大小 `16,4,3,2,2,2`
  4478	- 与提交 ledger 的逐条 class/inline/SHA 状态：0 mismatch
  4479	- 7 个 session token 当前各恰好 1 个 regular、可读、非 symlink transcript；仅检查元数据，未读正文
  4480	- QA DB 当前只读复查仍为 `qa_error_logs=0`，查询后 SHA 不变且未产生 sidecar
  4481	
  4482	汇总可见于 [ledger:40](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:40)。
  4483	
  4484	`attribution_conflict=3` 与 `byte_exact=4 / unverifiable=0` **诚实且自洽**：独立分组确认只有行 1–3 的组完全无 token；它们正是三个 callout，且 inline SHA+长度双门通过，[ledger:179](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:179)。归因不可用与正文已能逐字节恢复是两个独立维度。
  4485	
  4486	### 其他新发现
  4487	
  4488	- **MEDIUM — 证据包漂移**：`grep-selfattest.txt` 仍标注 round-4、旧脚本 SHA `f275…` 和旧行号，[evidence:1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:1)；receipt 只记录到 `d2827a6d`，[receipt:10](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt:10)，未绑定当前 `4c125f19`。报告/UAT 对“当前证据包”的声明不成立。
  4489	- **LOW — ledger 不自描述**：`no_token` 仅存在于内存；记录只序列化笼统的 `attribution_conflict=true`，无法区分缺 token、token 冲突或多命中。
  4490	- **LOW — 其余字段 surrogate DoS**：strict encode 只覆盖 body/full-body；`name/error/group_id` 等若含 escaped lone surrogate，`ensure_ascii=False` 的 UTF-8 写出仍会抛错并拒绝整次 census。
  4491	- **LOW — `stat_failures` basis 基本不可达**：`os.path.islink/isfile` 通常把 stat 的 `OSError` 转为 `False`，不会进入 [except 分支](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:212)。枚举到的候选最终仍会在后置 stat 失败时 exit 2，因此不是额外截断绕过。
  4492	
  4493	审阅锚定 `HEAD=4c125f19dd6b189c7dcdfa3bff686cbd494a11cc`。没有 tracked diff，也未创建临时 fixture、未读 transcript 正文或 Vault。`graphiti-canvas` 与 Context7 本轮未暴露；Sequential Thinking 已执行，SQLite 语义改用官方文档核对。开始前已存在的未跟踪 round-6 会话记录由环境记录器持续增长；我未写入、删除或清理它。
  4494	
  4495	
  4496	tokens used
  4497	202,210
  4498	总裁定：**仍阻断，CARD-G4-9 round-6 不可验收。**
  4499	
  4500	结论需拆开：
  4501	
  4502	- **冻结台账数字 PASS**：92 条 ledger 可以采信。
  4503	- **生成器只读安全闭包 FAIL**：仍有 2 个 BLOCKER，能违反报告/UAT 的“纯只读、零写入”承诺。
  4504	- 按 7 个顶层整改计为 **4/7 CLOSED**；把 LOW×3 拆开则为 **6/9 CLOSED**。
  4505	
  4506	### 逐项裁定
  4507	
  4508	| 整改项 | 裁定 | 复核结果 |
  4509	|---|---|---|
  4510	| 1. token 冲突/无 token 先扫描 | **NOT-CLOSED · BLOCKER** | 可枚举 token-conflict 候选确会先进入保护集；但扫描受阻只标 `unverifiable`，不会停止写出。根可读、子目录 `0333`（不可列举但可按名穿越）、其中存在匹配 transcript `T` 时，`os.walk` 只能记录错误，`T` 不进保护集，`--out=T` 最终仍可被打开并截断。[扫描入口](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:201)、[scan_errors 判定](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:241)、[保护循环](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:663)、[输出打开](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:686)。无 token 时 `if uniq` 仍完全不扫描，`all_candidate_paths=[]`。 |
  4511	| 2. QA DB 身份绑定 | **NOT-CLOSED · BLOCKER** | 验证 fd 在 [line 288](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:288) 已关闭；SQLite 随后按路径另开，[后置 `os.stat(path)`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:295)并不能证明连接打开的是同一 inode。A→B→A 的 ABA 可通过；`protected_ids` 仍只加入 A，[line 618](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:618)。 |
  4512	| 3. visibility 优先于 anomaly | **CLOSED** | byte-exact 两支之后，`attribution_conflict→unverifiable` 已位于 `anomaly→unrecoverable` 前：[exact](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:518)、[conflict](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:524)、[anomaly](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:542)。exact 先行是合理例外，因为不依赖 transcript。 |
  4513	| 4. fchmod 顺序 | **CLOSED（局部）** | 实际顺序为碰撞检查 [698](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:698) → `fchmod` [706](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:706) → `ftruncate` [707](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:707)。但它不能补救项目 1/2 导致的保护集漏项。 |
  4514	| 5. QA DB 特殊文件门 | **NOT-CLOSED / PARTIAL · MEDIUM** | 第一次 `O_NONBLOCK+S_ISREG` 能拒绝稳定 FIFO/设备；但 fd 随即关闭，SQLite 第二次按路径打开没有这些门。regular→FIFO/symlink 替换仍可绕过并在 `connect()` 内阻塞。 |
  4515	| 6. no_token→unverifiable | **CLOSED（行为）** | 非 byte-exact 的 no-token 记录会进入 `unverifiable`；full-verified/no-token 仍为 byte-exact，语义正确。[no_token](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:228)。但 `no_token` 未写入 ledger，见下方 LOW。 |
  4516	| 7a. 单独 LF | **CLOSED** | 纯内存复算：`b""→0`、`b"\n"→1`、`b"\n\n"→2`、`b"{}\n"→1`。[实现](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:85)。 |
  4517	| 7b. strict encode | **CLOSED（原反例）** | lone `U+D800` 配旧 replace-hash 现为 `anomaly/FAIL`，full-body 为 `False`；正常 emoji 正控仍通过。[inline](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:124)、[full-body](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:151)。 |
  4518	| 7c. bool 长度门 | **CLOSED** | `True/False/1.0` 均被拒，整数 `1` 正控通过。[inline 门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:129)、[full-body 门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:148)。 |
  4519	
  4520	### QA DB 新的确定性 BLOCKER
  4521	
  4522	[line 290](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:290)直接拼接：
  4523	
  4524	```python
  4525	uri = f"file:{db_path}?mode=ro"
  4526	```
  4527	
  4528	合法文件名中的 `?`/`#` 未转义。例如验证对象是 `/x/qa#tag`，SQLite URI 实际 path 是 `/x/qa`，`#tag?mode=ro` 被当作 fragment 忽略；这不仅打开不同对象，还丢失 `mode=ro`，可能隐式创建数据库。SQLite 官方要求把普通文件名中的 `?/#` 转义，并规定 fragment 被忽略；Python `connect()` 默认可创建不存在的数据库。[SQLite URI 规则](https://sqlite.org/uri.html#the_uri_path)、[Python sqlite3.connect](https://docs.python.org/3/library/sqlite3.html#sqlite3.connect)。
  4529	
  4530	这是无需竞态的零写入反例，足以单独维持 BLOCKER。
  4531	
  4532	### 台账独立复算
  4533	
  4534	未把生成器当 oracle，直接从 live DLQ exact bytes 重写分帧、分类、SHA/长度、分组和聚簇算法：
  4535	
  4536	- SHA-256：`3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590`
  4537	- `99,915 bytes`；92 records；unparseable 0
  4538	- class：`89 / 2 / 1`
  4539	- inline：4 full_verified / 88 truncated / 0 anomaly
  4540	- recoverability：4 byte_exact / 88 approximate / 0 unverifiable / 0 unrecoverable
  4541	- 重复簇：6/29，簇大小 `16,4,3,2,2,2`
  4542	- 与提交 ledger 的逐条 class/inline/SHA 状态：0 mismatch
  4543	- 7 个 session token 当前各恰好 1 个 regular、可读、非 symlink transcript；仅检查元数据，未读正文
  4544	- QA DB 当前只读复查仍为 `qa_error_logs=0`，查询后 SHA 不变且未产生 sidecar
  4545	
  4546	汇总可见于 [ledger:40](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:40)。
  4547	
  4548	`attribution_conflict=3` 与 `byte_exact=4 / unverifiable=0` **诚实且自洽**：独立分组确认只有行 1–3 的组完全无 token；它们正是三个 callout，且 inline SHA+长度双门通过，[ledger:179](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:179)。归因不可用与正文已能逐字节恢复是两个独立维度。
  4549	
  4550	### 其他新发现
  4551	
  4552	- **MEDIUM — 证据包漂移**：`grep-selfattest.txt` 仍标注 round-4、旧脚本 SHA `f275…` 和旧行号，[evidence:1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:1)；receipt 只记录到 `d2827a6d`，[receipt:10](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt:10)，未绑定当前 `4c125f19`。报告/UAT 对“当前证据包”的声明不成立。
  4553	- **LOW — ledger 不自描述**：`no_token` 仅存在于内存；记录只序列化笼统的 `attribution_conflict=true`，无法区分缺 token、token 冲突或多命中。
  4554	- **LOW — 其余字段 surrogate DoS**：strict encode 只覆盖 body/full-body；`name/error/group_id` 等若含 escaped lone surrogate，`ensure_ascii=False` 的 UTF-8 写出仍会抛错并拒绝整次 census。
  4555	- **LOW — `stat_failures` basis 基本不可达**：`os.path.islink/isfile` 通常把 stat 的 `OSError` 转为 `False`，不会进入 [except 分支](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:212)。枚举到的候选最终仍会在后置 stat 失败时 exit 2，因此不是额外截断绕过。
  4556	
  4557	审阅锚定 `HEAD=4c125f19dd6b189c7dcdfa3bff686cbd494a11cc`。没有 tracked diff，也未创建临时 fixture、未读 transcript 正文或 Vault。`graphiti-canvas` 与 Context7 本轮未暴露；Sequential Thinking 已执行，SQLite 语义改用官方文档核对。开始前已存在的未跟踪 round-6 会话记录由环境记录器持续增长；我未写入、删除或清理它。
  4558	
  4559	

exec
/bin/zsh -lc "rg -n '"'^总裁定|''^### QA DB 新的|''^### 其他新发现|''^### 台账独立复算|''^### 逐项'"' '_bmad-output/审查/codex-review-CARD-G4-9-round6.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
4434:总裁定：**仍阻断，CARD-G4-9 round-6 不可验收。**
4442:### 逐项裁定
4456:### QA DB 新的确定性 BLOCKER
4468:### 台账独立复算
4486:### 其他新发现
4498:总裁定：**仍阻断，CARD-G4-9 round-6 不可验收。**
4506:### 逐项裁定
4520:### QA DB 新的确定性 BLOCKER
4532:### 台账独立复算
4550:### 其他新发现

exec
/bin/zsh -lc "rg --files -g 'AGENTS.md' -g 'CLAUDE.md' -g 'CURRENT_TASK.md' -g '.claude/rules/*.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
CLAUDE.md
CURRENT_TASK.md
canvas-vault/CLAUDE.md
_decisions/CURRENT_TASK.md

exec
/bin/zsh -lc 'git show HEAD:CURRENT_TASK.md' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
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

exec
/bin/zsh -lc 'git rev-parse HEAD HEAD''^{tree} HEAD''^ HEAD''^''^' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
4ba4f847fa3ad83d136d3a40fcc5448b25c54ba5
28563f85a75699237ced191eae5908cb04d164b6
5b3712537ef5be91eda18e2a9eaf2fd3d5e03ef5
4c125f19dd6b189c7dcdfa3bff686cbd494a11cc

**Confirming required URI blocker retention**
mcp: sequential-thinking/sequentialthinking started
mcp: sequential-thinking/sequentialthinking (completed)
**Planning JSON and SQLite probe strategies**
**Planning readlink and hashing verification**
codex
第一轮静态交叉已出现三个必须保留的风险：根外 hardlink、检查后中间目录 symlink 换链、以及 QA DB 的 rename 型 ABA；此外 round-6 明确提出的 SQLite URI `?/#` 未转义问题在当前 diff 中没有整改。下一步我会用纯内存探针确认 surrogate 行为，并从冻结 DLQ exact bytes（只输出聚合，不泄露正文）独立重算台账。
exec
/bin/zsh -lc "sed -n '1,160p' backend/scripts/census_dead_letter_episodes.py" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
#!/usr/bin/env python3
"""CARD-G4-9: dead-letter episodes 只读 census 分诊脚本。

BATCH-2026-08-28-第五批 / CARD-G4-9（G4-10 replay 的交接台账生成器）。

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
    had_trailing_lf = raw.endswith(b"\n")
    if had_trailing_lf:
        raw = raw[:-1]
    if not raw:
        # round-5 LOW 整改: 单独 b"\n" 是一个空行，不是 0 行
        return [("", None)] if had_trailing_lf else []
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
    # round-5 LOW 整改: errors="replace" 会把 JSON escaped lone surrogate
    # (\udXXX) 改写成 replacement char，可被构造出"对得上账"的假 full_verified。
    # 改 strict：无法编码即判 anomaly。
    try:
        body_bytes = body.encode("utf-8")
    except UnicodeEncodeError:
        return "anomaly", "FAIL"
    recomputed = hashlib.sha256(body_bytes).hexdigest()
    len_ok = isinstance(declared_len, int) and not isinstance(declared_len, bool)
    if sha_wellformed and recomputed == declared_sha and len_ok and len(body) == declared_len:
        return "full_verified", "pass"
    if sha_wellformed and len(body) == 200 and len_ok and declared_len > 200:
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
    # round-5 LOW 整改: bool 是 int 子类 —— episode_body_length=True 会通过长度门
    if not isinstance(declared_len, int) or isinstance(declared_len, bool) or len(full) != declared_len:
        return False
    try:
        full_bytes = full.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return hashlib.sha256(full_bytes).hexdigest() == declared_sha


def session_tokens(name: object) -> list[str]:
    """round-4 LOW 整改: name 非 str（None/数字/列表）不再抛异常。"""
    if not isinstance(name, str):

exec
/bin/zsh -lc 'git cat-file -p HEAD''^{commit}' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
tree 28563f85a75699237ced191eae5908cb04d164b6
parent 5b3712537ef5be91eda18e2a9eaf2fd3d5e03ef5
author oinani0721 <2272104243@qq.com> 1787921343 +0800
committer oinani0721 <2272104243@qq.com> 1787921343 +0800

docs(census): receipt 补 round-5/6 commit 链 [BATCH-2026-08-28-第五批 / CARD-G4-9]

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>

exec
/bin/zsh -lc "shasum -a 256 '/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl

exec
/bin/zsh -lc "nl -ba backend/scripts/census_dead_letter_episodes.py | sed -n '195,320p;400,475p;610,770p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
   195	
   196	    # 单次遍历收集**每个 token** 的候选（无条件，供保护集与判定共用）
   197	    per_token: dict[str, list[str]] = {t: [] for t in uniq}
   198	    all_candidates: list[str] = []
   199	    unreadable: list[str] = []
   200	    stat_failures: list[str] = []
   201	    # round-6 整改: **无论有无 token 都遍历** —— no_token 时原实现完全不扫描，
   202	    # all_candidate_paths 为空，该组见不到的候选就进不了保护集。
   203	    for dirpath, _dirnames, filenames in os.walk(transcripts_dir, onerror=_on_walk_error, followlinks=False):
   204	        for fname in filenames:
   205	            if fname.endswith(".jsonl"):
   206	                matched = [t for t in uniq if fname.startswith(t)]
   207	                candidate = os.path.join(dirpath, fname)
   208	                # 候选一律入 all_candidate_paths（保护集口径），再谈可用性
   209	                all_candidates.append(candidate)
   210	                if not matched:
   211	                    continue
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
   281	    # round-6 BLOCKER② 整改: 验证 fd **保持打开**直到 SQLite 连接建立并复核完毕
   282	    # —— 原实现验证后即关闭，SQLite 按路径重开可被 A→B→A 的 ABA 骗过。
   283	    conn = None
   284	    try:
   285	        st = os.fstat(fd)
   286	        if not stat.S_ISREG(st.st_mode):
   287	            result["verdict"] = "not_regular_file_refused"
   288	            return result, None
   289	        identity = (st.st_dev, st.st_ino)
   290	
   291	        uri = f"file:{db_path}?mode=ro"
   292	        conn = sqlite3.connect(uri, uri=True)
   293	        # 连接建立后在**持有验证 fd 的同时**复核路径身份
   294	        try:
   295	            recheck = os.stat(db_path)
   296	        except OSError as e:
   297	            result["verdict"] = f"recheck_stat_failed: {e}"
   298	            return result, identity
   299	        if (recheck.st_dev, recheck.st_ino) != identity:
   300	            result["verdict"] = "identity_changed_between_verify_and_open_refused"
   301	            return result, identity
   302	        # 再次 fstat 验证 fd：确认它仍指向同一对象且未被 unlink 替换
   303	        st2 = os.fstat(fd)
   304	        if (st2.st_dev, st2.st_ino) != identity or st2.st_nlink == 0:
   305	            result["verdict"] = "verified_fd_invalidated_refused"
   306	            return result, identity
   307	        result["opened_readonly"] = True
   308	        result["file_identity_verified"] = True
   309	        tables = [
   310	            r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
   311	        ]
   312	        result["tables"] = tables
   313	        if "qa_error_logs" in tables:
   314	            total = conn.execute("SELECT COUNT(*) FROM qa_error_logs").fetchone()[0]
   315	            result["qa_error_logs_rows"] = total
   316	            hits = {}
   317	            for et in sorted(set(error_types)):
   318	                hits[et] = conn.execute("SELECT COUNT(*) FROM qa_error_logs WHERE error_type = ?", (et,)).fetchone()[0]
   319	            result["error_type_hits"] = hits
   320	            result["verdict"] = "no_source_rows" if total == 0 else "rows_present_see_hits"
   400	    dlq_path = Path(args.dlq)
   401	    if not dlq_path.exists():
   402	        print(f"DLQ 文件不存在: {dlq_path}", file=sys.stderr)
   403	        return 2
   404	
   405	    transcripts_dir = Path(args.transcripts_dir)
   406	    if not transcripts_dir.is_dir():
   407	        print(
   408	            f"transcripts 根目录不存在/不可见: {transcripts_dir} —— 拒绝在源不可见时裁定可恢复性（fail-closed）",
   409	            file=sys.stderr,
   410	        )
   411	        return 2
   412	    # round-2 HIGH-3 整改: 存在但不可读/不可遍历的根（chmod 000）此前 exit 0
   413	    # 并把全部记录假判 unrecoverable —— 同样 fail-closed 拒诊。
   414	    if not os.access(transcripts_dir, os.R_OK | os.X_OK):
   415	        print(
   416	            f"transcripts 根目录不可读/不可遍历: {transcripts_dir} —— 拒绝在源不可见时裁定可恢复性（fail-closed）",
   417	            file=sys.stderr,
   418	        )
   419	        return 2
   420	
   421	    protected_ids: set[tuple[int, int]] = set()
   422	    # round-6 BLOCKER①② 架构整改: inode 保护集依赖**枚举完整性**（不可列举的
   423	    # 子目录、ABA 换 inode 都能让某个真实源不进集合）。故增加**不依赖枚举**的
   424	    # 路径层防御：--out 的 realpath 不得落在 transcripts 根内、不得等于任一
   425	    # 输入路径。路径层 + inode 层双保险，任一命中即拒绝。
   426	    if args.out:
   427	        out_real = os.path.realpath(args.out)
   428	        tr_real = os.path.realpath(args.transcripts_dir)
   429	        tr_prefix = tr_real if tr_real.endswith(os.sep) else tr_real + os.sep
   430	        if out_real == tr_real or out_real.startswith(tr_prefix):
   431	            print(
   432	                f"--out 落在 transcripts 根内（恢复源区域），无条件拒绝写出: {args.out}",
   433	                file=sys.stderr,
   434	            )
   435	            return 2
   436	        input_reals = {os.path.realpath(args.dlq)} | {os.path.realpath(c) for c in args.compare}
   437	        if args.qa_metrics_db:
   438	            input_reals.add(os.path.realpath(args.qa_metrics_db))
   439	        if out_real in input_reals:
   440	            print(f"--out 与输入文件路径相同（realpath 比较），拒绝写出: {args.out}", file=sys.stderr)
   441	            return 2
   442	
   443	    # --out 碰撞守卫（写前）。round-2 BLOCKER-1 整改: 比较**文件身份**
   444	    # (st_dev, st_ino) 而非 resolve() 字符串 —— 后者对 hardlink 与
   445	    # 大小写不敏感文件系统上的 case-only 别名均失效（Codex 实测截断输入）。
   446	    if args.out:
   447	        out_path = Path(args.out)
   448	        protected_paths = [dlq_path, *(Path(p) for p in args.compare)]
   449	        if args.qa_metrics_db:
   450	            protected_paths.append(Path(args.qa_metrics_db))
   451	        for candidate in protected_paths:
   452	            try:
   453	                cst = candidate.stat()  # 跟随 symlink: 保护的是最终目标身份
   454	                protected_ids.add((cst.st_dev, cst.st_ino))
   455	            except OSError:
   456	                # round-4 整改: stat 失败不再静默吞 —— 无法确认身份即 fail-closed
   457	                print(f"输入文件无法 stat，拒绝继续（无法建立完整保护集）: {candidate}", file=sys.stderr)
   458	                return 2
   459	        # 路径字符串比较作为第二道（输出文件尚不存在时 stat 无身份可比）
   460	        out_resolved = out_path.resolve()
   461	        if out_resolved in {p.resolve() for p in protected_paths}:
   462	            print(f"--out 与输入文件路径重合，拒绝写出（防截断）: {out_resolved}", file=sys.stderr)
   463	            return 2
   464	        if out_path.exists():
   465	            try:
   466	                out_st = out_path.stat()
   467	            except OSError as e:
   468	                print(f"--out 无法 stat，拒绝写出: {out_path} ({e})", file=sys.stderr)
   469	                return 2
   470	            if (out_st.st_dev, out_st.st_ino) in protected_ids:
   471	                print(
   472	                    f"--out 与输入文件为同一 inode（hardlink/大小写别名），拒绝写出（防截断）: {out_path}",
   473	                    file=sys.stderr,
   474	                )
   475	                return 2
   610	                "inline_state": state,
   611	                "sha_check": sha_check,
   612	                "session_token": sess["session_token"],
   613	                "transcript_paths": sess["transcript_paths"],
   614	                "transcript_match_count": sess["transcript_match_count"],
   615	                "attribution_conflict": sess["attribution_conflict"],
   616	                # round-6 LOW 整改: ledger 自描述冲突原因，G4-10 可区分
   617	                # 缺 token / token 冲突 / 扫描受阻 / 不可读 / 多命中
   618	                "attribution_conflict_reason": (
   619	                    "no_token"
   620	                    if sess.get("no_token")
   621	                    else "token_conflict"
   622	                    if sess.get("token_conflict")
   623	                    else "scan_errors"
   624	                    if sess.get("scan_errors")
   625	                    else "stat_failures"
   626	                    if sess.get("stat_failures")
   627	                    else "unreadable_candidates"
   628	                    if sess.get("unreadable_candidates")
   629	                    else "ambiguous_multi_match"
   630	                    if sess["attribution_conflict"]
   631	                    else None
   632	                ),
   633	                "recoverability": recover,
   634	                "recoverability_basis": basis,
   635	            }
   636	        )
   637	
   638	    # 语义重复簇（同 name + 全文 sha + group_id）——G4-10 重放去重策略依据
   639	    cluster_map: dict[tuple, list[int]] = defaultdict(list)
   640	    for line_no, rec in records:
   641	        cluster_map[
   642	            (str(rec.get("name", "")), str(rec.get("episode_body_sha256", "")), str(rec.get("group_id")))
   643	        ].append(line_no)
   644	    duplicate_clusters = [
   645	        {"name": k[0][:80], "episode_body_sha256": k[1], "group_id": k[2], "line_nos": v, "occurrences": len(v)}
   646	        for k, v in sorted(cluster_map.items(), key=lambda kv: -len(kv[1]))
   647	        if len(v) > 1
   648	    ]
   649	
   650	    compare_infos = []
   651	    for cp in args.compare:
   652	        cinfo, cid = describe_copy(Path(cp))
   653	        compare_infos.append(cinfo)
   654	        if cid is not None:
   655	            protected_ids.add(cid)
   656	
   657	    if args.qa_metrics_db:
   658	        qa_probe, qa_identity = probe_qa_metrics(
   659	            Path(args.qa_metrics_db),
   660	            [str(r.get("error_type", "")) for _, r in records],
   661	        )
   662	        if qa_identity is not None:
   663	            protected_ids.add(qa_identity)  # 保护实际验证过的对象身份
   664	    else:
   665	        qa_probe = {"verdict": "skipped_no_db_arg"}
   666	
   667	    deviation = {
   668	        k: {"expected": EXPECTED_CLASS_DIST.get(k, 0), "actual": class_dist.get(k, 0)}
   669	        for k in sorted(set(class_dist) | set(EXPECTED_CLASS_DIST))
   670	        if EXPECTED_CLASS_DIST.get(k, 0) != class_dist.get(k, 0)
   671	    }
   672	
   673	    ledger = {
   674	        "card": "CARD-G4-9",
   675	        "generated_at": datetime.now(timezone.utc).isoformat(),
   676	        "privacy": "private-only: transcript_paths 含本机用户名与 session UUID，禁止外发/公网发布",
   677	        "stable_key_semantics": (
   678	            "冻结快照（dlq_file.sha256）内的 occurrence key；line_no 在快照内唯一，"
   679	            "sha256_prefix/request_id 为冗余对账维度——非跨文件重排或语义幂等键"
   680	        ),
   681	        "dlq_file": dlq_info,
   682	        "compare_copies": compare_infos,
   683	        "total_lines": len(raw_lines),
   684	        "total_records": len(records),
   685	        "unparseable_lines": unparseable,
   686	        # round-2 LOW 整改: 固定 schema 补零，消费者无需自行补齐缺席键
   687	        "class_distribution": {
   688	            k: class_dist.get(k, 0) for k in ["budget_400", "schema_entity_type", "group_id_format", "unexpected"]
   689	        },
   690	        "expected_class_distribution": EXPECTED_CLASS_DIST,
   691	        "class_deviation": deviation,
   692	        "recoverability_distribution": {
   693	            k: recover_dist.get(k, 0) for k in ["byte_exact", "approximate", "unverifiable", "unrecoverable"]
   694	        },
   695	        "inline_state_distribution": {
   696	            k: inline_dist.get(k, 0) for k in ["full_verified", "truncated_prefix", "anomaly"]
   697	        },
   698	        "unrecoverable_list": unrecoverable_keys,
   699	        "unverifiable_list": unverifiable_keys,
   700	        "attribution_conflicts": attribution_conflicts,
   701	        "duplicate_clusters": duplicate_clusters,
   702	        "qa_metrics_probe": qa_probe,
   703	        "records": ledger_records,
   704	    }
   705	
   706	    # round-3 BLOCKER-1 绕过① 整改: 归因到的 transcript 是恢复源，
   707	    # --out 指向它同样会截断。写出前并入保护集（此时归因已完成）。
   708	    for sess_info in group_attribution.values():
   709	        for tpath in sess_info.get("all_candidate_paths", []):
   710	            try:
   711	                tst = os.stat(tpath)
   712	                protected_ids.add((tst.st_dev, tst.st_ino))
   713	            except OSError as e:
   714	                # round-5 整改: 候选 stat 失败不再静默吞 —— 保护集不完整即拒绝写出
   715	                print(f"候选源无法 stat，保护集不完整，拒绝写出: {tpath} ({e})", file=sys.stderr)
   716	                return 2
   717	    for rec_out in ledger_records:
   718	        for tpath in rec_out.get("transcript_paths", []):
   719	            try:
   720	                tst = os.stat(tpath)
   721	                protected_ids.add((tst.st_dev, tst.st_ino))
   722	            except OSError:
   723	                continue
   724	
   725	    try:
   726	        out_json = json.dumps(ledger, ensure_ascii=False, indent=1)
   727	    except (UnicodeEncodeError, ValueError):
   728	        # round-6 LOW 整改: name/error/group_id 等字段若含 escaped lone surrogate，
   729	        # ensure_ascii=False 写出会抛错并拒绝整次 census。回退 ensure_ascii=True
   730	        # （\uXXXX 转义，ASCII 安全）并在台账中显式标注该降级。
   731	        ledger["json_encoding_note"] = "ensure_ascii=True fallback: 某字段含无法 UTF-8 编码的字符（lone surrogate）"
   732	        out_json = json.dumps(ledger, ensure_ascii=True, indent=1)
   733	    if args.out:
   734	        # round-3 整改: 消除 check-then-open TOCTOU。先以 O_NOFOLLOW 打开且
   735	        # **不带 O_TRUNC**，对**实际 fd** fstat 校验 inode；只有校验通过才
   736	        # ftruncate。检查与写入作用于同一 fd，检查后被换 symlink/hardlink 无效。
   737	        try:
   738	            fd = os.open(args.out, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
   739	        except OSError as e:
   740	            print(f"--out 无法安全打开（symlink 或权限）: {args.out} ({e})", file=sys.stderr)
   741	            return 2
   742	        try:
   743	            st = os.fstat(fd)
   744	            # round-4 MEDIUM 整改: 非常规文件（FIFO/设备/socket）拒绝
   745	            if not stat.S_ISREG(st.st_mode):
   746	                print(f"--out 不是常规文件（FIFO/设备/socket），拒绝写出: {args.out}", file=sys.stderr)
   747	                return 2
   748	            # round-5 HIGH 整改: 碰撞检查必须**先于** fchmod —— 否则 --out 指向
   749	            # 受保护的 0644 输入时，会先把只读输入的权限改成 0600 再拒绝。
   750	            if (st.st_dev, st.st_ino) in protected_ids:
   751	                print(
   752	                    f"--out 打开后经 fstat 判定与输入文件同一 inode，拒绝写出（防截断）: {args.out}",
   753	                    file=sys.stderr,
   754	                )
   755	                return 2
   756	            # 碰撞检查通过后才收紧权限（round-4 LOW: 0o600 只作用于新建）
   757	            if st.st_mode & 0o077:
   758	                os.fchmod(fd, 0o600)
   759	            os.ftruncate(fd, 0)
   760	            with os.fdopen(fd, "w", encoding="utf-8", closefd=True) as f:
   761	                fd = -1  # 所有权移交 fdopen
   762	                f.write(out_json + "\n")
   763	        finally:
   764	            if fd >= 0:
   765	                os.close(fd)
   766	        print(f"台账已写入: {args.out}")
   767	    else:
   768	        print(out_json)
   769	
   770	    print(

exec
/bin/zsh -lc "python3 -B -c 'import json; s=json.dumps({\"x\":\"\\ud800\"}, ensure_ascii=False); print(repr(s)); print(\"dumps_returned_surrogate=\", any(0xD800 <= ord(c) <= 0xDFFF for c in s));
try: s.encode(\"utf-8\"); print(\"utf8_encode=PASS\")
except UnicodeEncodeError as e: print(\"utf8_encode=UnicodeEncodeError\", e.start, e.end)'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
'{"x": "\ud800"}'
dumps_returned_surrogate= True
utf8_encode=UnicodeEncodeError 7 8

exec
/bin/zsh -lc "python3 -B -c 'import json, hashlib, collections, pathlib
src=pathlib.Path(\"/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl\")
led=pathlib.Path(\"_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json\")
raw=src.read_bytes(); chunks=raw.split(b\"\\n\"); chunks=chunks[:-1] if chunks and chunks[-1]==b\"\" else chunks
parsed=[]; bad=[]
for i,b in enumerate(chunks,1):
 try:
  s=b.decode(\"utf-8\",errors=\"strict\"); o=json.loads(s)
  if not isinstance(o,dict): raise TypeError(type(o).__name__)
  parsed.append((i,o))
 except Exception as e: bad.append((i,type(e).__name__))
def cls(r):
 et=r.get(\"error_type\")
 if et==\"EntityTypeValidationError\": return \"schema_entity_type\"
 if et==\"GroupIdValidationError\": return \"group_id_format\"
 if et==\"BadRequestError\" and \"maximum allowed\" in str(r.get(\"error\",\"\")): return \"budget_400\"
 return \"unexpected\"
def inline(r):
 b=r.get(\"episode_body\"); n=r.get(\"episode_body_length\"); h=r.get(\"episode_body_sha256\")
 if not isinstance(b,str): return \"anomaly\"
 try: bb=b.encode(\"utf-8\")
 except UnicodeEncodeError: return \"anomaly\"
 okn=isinstance(n,int) and not isinstance(n,bool)
 if len(b)<200 and okn and len(b)==n and hashlib.sha256(bb).hexdigest()==h: return \"full_verified\"
 if len(b)==200 and okn and n>=200: return \"truncated_prefix\"
 return \"anomaly\"
C=collections.Counter(cls(r) for _,r in parsed); I=collections.Counter(inline(r) for _,r in parsed)
K=collections.defaultdict(list)
for i,r in parsed: K[(str(r.get(\"name\",\"\")),str(r.get(\"episode_body_sha256\",\"\")),str(r.get(\"group_id\")))].append(i)
dups=sorted((len(v) for v in K.values() if len(v)>1),reverse=True)
L=json.loads(led.read_text(\"utf-8\")); mism=[]
for (i,r),q in zip(parsed,L[\"records\"]):
 if q[\"stable_key\"][\"line_no\"]"'!=i or q["class"]!=cls(r) or q["inline_state"]!=inline(r): mism.append(i)
recd=collections.Counter(q["recoverability"] for q in L["records"]); reasons=collections.Counter(q.get("attribution_conflict_reason") for q in L["records"] if q.get("attribution_conflict"))
print({"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),"framed":len(chunks),"records":len(parsed),"unparseable":len(bad),"class":dict(C),"inline":dict(I),"duplicate_clusters":len(dups),"duplicate_occurrences":sum(dups),"cluster_sizes":dups,"ledger_mismatch":mism,"ledger_recoverability":dict(recd),"ledger_conflicts":sum(1 for q in L["records"] if q.get("attribution_conflict")),"conflict_reasons":dict(reasons)})'"'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
{'sha256': '3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590', 'bytes': 99915, 'framed': 92, 'records': 92, 'unparseable': 0, 'class': {'schema_entity_type': 2, 'group_id_format': 1, 'unexpected': 89}, 'inline': {'full_verified': 4, 'truncated_prefix': 88}, 'duplicate_clusters': 6, 'duplicate_occurrences': 29, 'cluster_sizes': [16, 4, 3, 2, 2, 2], 'ledger_mismatch': [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92], 'ledger_recoverability': {'byte_exact': 4, 'approximate': 88}, 'ledger_conflicts': 3, 'conflict_reasons': {'no_token': 3}}

**Refactoring classifier with regex substrings**
**Designing token extraction and verification**
**Verifying git blob and commit hashes**
**Verifying line references with hashes**
**Assessing output encoding failure impact**
**Confirming LOW severity fallback issue**
**Verifying macOS case-only alias behavior**
**Identifying case alias as new path blocker**
**Assessing hardlink swap vulnerability**
**Analyzing TOCTOU risks with symlinks**
**Evaluating symlink and hardlink handling edge cases**
**Confirming broken symlink handling and loop prevention**
**Analyzing snapshot and output path consistency**
**Assessing SQLite connection inode race conditions**
**Identifying race condition in output hardlink handling**
**Verifying path normalization and prefix checks**
**Planning independent ledger recomputation and token analysis**
**Preparing to run Python process without bytecode creation**
**Assessing SQLite mode implications on selfattest**
**Confirming selfattest freshness closed**
exec
/bin/zsh -lc "nl -ba '_bmad-output/审查/G4-9-evidence/shasums-before.txt' && nl -ba '_bmad-output/审查/G4-9-evidence/shasums-after.txt'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
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
/bin/zsh -lc "python3 -B -c 'import os
pairs=[(\"/Users\",\"/users\"),(\"/Users/Heishing/.claude/projects\",\"/users/heishing/.claude/projects\")]
for a,b in pairs: print({\"a\":a,\"b\":b,\"samefile\":os.path.samefile(a,b),\"real_a\":os.path.realpath(a),\"real_b\":os.path.realpath(b),\"string_equal\":os.path.realpath(a)==os.path.realpath(b)})
tr=os.path.realpath(\"/Users/Heishing/.claude/projects\"); out=os.path.realpath(\"/users/heishing/.claude/projects/CARD-G4-9-nonexistent.jsonl\"); prefix=tr if tr.endswith(os.sep) else tr+os.sep; print({\"tr_real\":tr,\"out_real\":out,\"guard_blocks\":out==tr or out.startswith(prefix)})'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
{'a': '/Users', 'b': '/users', 'samefile': True, 'real_a': '/Users', 'real_b': '/users', 'string_equal': False}
{'a': '/Users/Heishing/.claude/projects', 'b': '/users/heishing/.claude/projects', 'samefile': True, 'real_a': '/Users/Heishing/.claude/projects', 'real_b': '/users/heishing/.claude/projects', 'string_equal': False}
{'tr_real': '/Users/Heishing/.claude/projects', 'out_real': '/users/heishing/.claude/projects/CARD-G4-9-nonexistent.jsonl', 'guard_blocks': False}

exec
/bin/zsh -lc 'nl -ba /Users/Heishing/.codex/memories/skills/canvas-adversarial-audit/SKILL.md' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
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

exec
/bin/zsh -lc 'git diff --name-status 5b371253..HEAD && git rev-list --first-parent --oneline 37387a86..HEAD' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
M	"_bmad-output/\345\256\241\346\237\245/G4-9-evidence/artifact-commit-receipt.txt"
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
4ba4f847 docs(census): receipt 补 round-5/6 commit 链 [BATCH-2026-08-28-第五批 / CARD-G4-9]
5b371253 fix(census): G4-9 Codex round-6 架构级修复 [BATCH-2026-08-28-第五批 / CARD-G4-9]
4c125f19 fix(census): G4-9 Codex round-5 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9]
d8d887f2 docs(census): 补 artifact commit receipt 绑定精确 SHA 链 [BATCH-2026-08-28-第五批 / CARD-G4-9]
d2827a6d fix(census): G4-9 Codex round-4 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9]
94b420ff fix(census): G4-16 Codex round-4 重放 recipe 确定化 [BATCH-2026-08-28-第五批 / CARD-G4-16]
fce0d8a2 fix(census): G4-9/G4-16 Codex round-3 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9 / CARD-G4-16]
73102875 fix(census): G4-9/G4-16 Codex round-2 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9 / CARD-G4-16]
e7a480eb docs(census): G4-16 doc_type族接线普查 18文件146行+6取值裁定+注释修正 [BATCH-2026-08-28-第五批 / CARD-G4-16]
67ccebe1 docs(census): G4-9 DLQ真实挂载census分诊 92条台账+挂载真相+三态裁定 [BATCH-2026-08-28-第五批 / CARD-G4-9]

exec
/bin/zsh -lc "python3 -B -c 'import json,hashlib,collections,pathlib,re,os,stat
src=pathlib.Path(\"/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl\")
led=json.loads(pathlib.Path(\"_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json\").read_text(\"utf-8\"))
raw=src.read_bytes(); bs=raw[:-1].split(b\"\\n\") if raw.endswith(b\"\\n\") else raw.split(b\"\\n\") if raw else []
rows=[]; bad=[]
for i,b in enumerate(bs,1):
 try:
  x=json.loads(b.decode(\"utf-8\",\"strict\")); assert isinstance(x,dict); rows.append((i,x))
 except Exception as e: bad.append((i,type(e).__name__))
budget=re.compile(r\"exceed_context_size_error|exceeds the available context size\")
arch=re.compile(r\""'^session-archive:([0-9a-fA-F-]+)"); inlinepat=re.compile(r"(?<![0-9a-zA-Z_-])session:([0-9a-f-]{5,})")
hex64=re.compile(r"''^[0-9a-f]{64}$")
def classify(r):
 e=r.get("error_type","")
 if e=="EntityTypeValidationError": return "schema_entity_type"
 if e=="GroupIdValidationError": return "group_id_format"
 if e=="BadRequestError" and budget.search(str(r.get("error",""))): return "budget_400"
 return "unexpected"
def state(r):
 b=r.get("episode_body",""); n=r.get("episode_body_length"); h=r.get("episode_body_sha256","")
 if not isinstance(b,str): return "anomaly"
 try: bb=b.encode("utf-8")
 except UnicodeEncodeError: return "anomaly"
 goodh=isinstance(h,str) and bool(hex64.fullmatch(h)); goodn=isinstance(n,int) and not isinstance(n,bool)
 if goodh and hashlib.sha256(bb).hexdigest()==h and goodn and len(b)==n: return "full_verified"
 if goodh and len(b)==200 and goodn and n>200: return "truncated_prefix"
 return "anomaly"
def fullok(r):
 f=r.get("episode_body_full"); n=r.get("episode_body_length"); h=r.get("episode_body_sha256","")
 if not isinstance(f,str) or not isinstance(n,int) or isinstance(n,bool) or len(f)!=n or not isinstance(h,str) or not hex64.fullmatch(h): return False
 try: return hashlib.sha256(f.encode("utf-8")).hexdigest()==h
 except UnicodeEncodeError: return False
def key(i,r):
 v=r.get("request_id")
 try: hash(v); return (type(v).__name__,v) if v is not None else ("__missing__",i)
 except TypeError: return ("__missing__",i)
def toks(name):
 if not isinstance(name,str): return []
 out=[]; m=arch.match(name)
 if m: out.append(m.group(1).lower())
 out += [z.lower() for z in inlinepat.findall(name)]; return out
groups=collections.defaultdict(list)
for i,r in rows: groups[key(i,r)].append((i,r))
root="/Users/Heishing/.claude/projects"; rr=os.path.realpath(root); rp=rr+os.sep if not rr.endswith(os.sep) else rr
files=[]; walkerr=[]
for dp,dn,fn in os.walk(root,onerror=lambda e:walkerr.append(type(e).__name__),followlinks=False):
 for f in fn:
  if f.endswith(".jsonl"): files.append(os.path.join(dp,f))
attrs={}
for k,members in groups.items():
 u=sorted(set(z for _,r in members for z in toks(r.get("name",""))),key=len)
 if not u: attrs[k]=(True,"no_token",False)
 elif any(not u[-1].startswith(z) for z in u[:-1]): attrs[k]=(True,"token_conflict",False)
 else:
  cand=[]
  for p in files:
   if os.path.basename(p).startswith(u[-1]) and not os.path.islink(p) and os.path.isfile(p) and os.access(p,os.R_OK) and os.path.realpath(p).startswith(rp): cand.append(p)
  attrs[k]=(len(set(cand))>1,"ambiguous_multi_match" if len(set(cand))>1 else None,len(set(cand))==1)
C=collections.Counter(); I=collections.Counter(); R=collections.Counter(); A=[]; detail=[]
for i,r in rows:
 c=classify(r); s=state(r); conflict,reason,exists=attrs[key(i,r)]
 if s=="full_verified" or (s!="anomaly" and fullok(r)): rec="byte_exact"
 elif conflict: rec="unverifiable"
 elif s=="anomaly": rec="unrecoverable"
 elif exists: rec="approximate"
 else: rec="unrecoverable"
 C[c]+=1; I[s]+=1; R[rec]+=1
 if conflict: A.append((i,reason,str(r.get("name","")).startswith("callout_annotation")))
 detail.append((i,c,s,rec,reason if conflict else None))
D=collections.defaultdict(list)
for i,r in rows:D[(str(r.get("name","")),str(r.get("episode_body_sha256","")),str(r.get("group_id")))].append(i)
sizes=sorted([len(v) for v in D.values() if len(v)>1],reverse=True)
mm=[]
for q,d in zip(led["records"],detail):
 i,c,s,rec,reason=d
 if (q["stable_key"]["line_no"],q["class"],q["inline_state"],q["recoverability"],q.get("attribution_conflict_reason"))!=(i,c,s,rec,reason): mm.append(i)
print({"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),"records":len(rows),"unparseable":len(bad),"class":dict(C),"inline":dict(I),"recoverability":dict(R),"duplicate_clusters":len(sizes),"duplicate_occurrences":sum(sizes),"sizes":sizes,"conflicts":len(A),"conflict_reasons":dict(collections.Counter(x[1] for x in A)),"conflict_callout_count":sum(x[2] for x in A),"walk_errors":walkerr,"metadata_jsonl_count":len(files),"ledger_row_mismatches":mm})'"'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
{'sha256': '3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590', 'bytes': 99915, 'records': 92, 'unparseable': 0, 'class': {'schema_entity_type': 2, 'group_id_format': 1, 'budget_400': 89}, 'inline': {'full_verified': 4, 'truncated_prefix': 88}, 'recoverability': {'byte_exact': 4, 'approximate': 88}, 'duplicate_clusters': 6, 'duplicate_occurrences': 29, 'sizes': [16, 4, 3, 2, 2, 2], 'conflicts': 3, 'conflict_reasons': {'no_token': 3}, 'conflict_callout_count': 3, 'walk_errors': [], 'metadata_jsonl_count': 3604, 'ledger_row_mismatches': []}

**Verifying output path permissions**
**Assessing case alias and symlink bypasses**
**Confirming TOCTOU race conditions**
**Assessing atomicity concerns with hardlink usage**
**Reviewing UAT claims on output atomicity**
**Prioritizing unresolved BLOCKER issue**
web search: 
web search: site:sqlite.org/uri.html URI filename fragment question mark hash mode=ro SQLite ...
**Examining docs claims for output atomicity**
exec
/bin/zsh -lc "sed -n '1,180p' '_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
# CARD-G4-9 — DLQ 真实挂载 census 分诊报告

> **批次**: BATCH-2026-08-28-第五批 / CARD-G4-9（4h · wave 1 · 未来铺路）
> **性质**: 纯只读 census。0 写入、0 重放、0 业务代码改动。唯一代码产物 = `backend/scripts/census_dead_letter_episodes.py`。
> **代码基线**: 分析对象锚定 `37387a86`（第五批开工基线）。**本卡交付物 artifact commit 链**：精确 SHA 逐段记录于 `_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt`（commit 无法自含己身 SHA，故用后置 receipt 绑定——Codex round-4 LOW 整改）
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
| `full_verified`（内联全量，sha 对账通过） | **4** | 重算值 == 声明值且长度精确匹配（四条正文实为 131/142/150/180 字符，范围 **131–180**，天然未截断；round-2 LOW 修正） |
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

## §5 可恢复性裁定（三态 + unverifiable 第四态）

| 三态 | 条数 | 裁定依据 |
|---|---|---|
| **可字节级**（byte_exact） | **4** | inline 正文全量：sha256 重算对账通过**且**长度精确匹配（fail-closed 双门）——重放可逐字节还原 episode |
| **近似**（approximate） | **88** | inline 仅 200 字符前缀，但经 request_id 组归因到在盘 transcript；G4-10 可对 22 条 session-archive 重新格式化 transcript（确定性、可用 `episode_body_sha256` 验证是否达字节级）、对 66 条 qa_highlight(44)/distillation(22) 重跑蒸馏（LLM 非确定性，语义近似、不保证逐字节） |
| **不可恢复**（unrecoverable） | **0** | inline 截断且经完整可见的扫描确认无在盘上游源 |
| **不可核验**（unverifiable，round-4 新增） | **0** | 源可见性不足（扫描受阻/不可读候选/归因冲突）——既不宣称可恢复，也不宣称不可恢复。Codex round-4 指出：把"看不见"终态化为"不可恢复"是不诚实断言，故单列第四态 |

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
| 负例门（round-1 整改自证） | `--out`==`--dlq` → exit 2 拒写、DLQ 完好；transcripts 根缺失 → exit 2 拒诊；sha 匹配但长度不符（round-1 HIGH-1 反例①）→ anomaly/unrecoverable；坏 JSON 行/空行 → unparseable 逐行入台账不拒诊 |
| 负例门（round-2 整改自证） | **hardlink** 指向 DLQ 的 --out → exit 2 + DLQ sha 不变；**case-only 别名**（`DLQ.jsonl`）→ exit 2 + DLQ 完好；**anomaly + episode_body_full 组合**（sha 对但长度 999）→ anomaly/unrecoverable（不再翻案 byte_exact）；**chmod 000 根** → exit 2 拒诊；**symlink 逃逸**（根内 .jsonl → 根外 .txt）→ match_count=0/unrecoverable；正例回归：真实唯一命中仍 approximate |

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

## §7c Codex round-2 复审整改记录（10/13 CLOSED → 剩余 3 项 + 3 新 LOW 全部整改）

round-2 复审确认 BLOCKER-2/3、HIGH-2、MEDIUM-1~3、LOW-1~4 共 10 项 CLOSED，并抓出 3 项**未真正闭合**（均实测复现）+ 3 条新 LOW：

- **BLOCKER-1 NOT-CLOSED（hardlink / case-only 别名绕过）**：原守卫比较 `resolve()` **字符串**，hardlink 指向输入、以及大小写不敏感文件系统上的 case-only 别名均绕过并截断输入。**整改**：改为比较**文件身份 `(st_dev, st_ino)`**（对已存在的 --out）+ 保留路径比较作第二道。负例实测：两种绕过均 exit 2、DLQ sha 不变。
- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
- **新 LOW ×3**：full_verified 长度范围修正为 131–180；台账 `class_distribution`/`recoverability_distribution` 补零并新增 `inline_state_distribution`（固定 schema，消费者无需补齐缺席键）；`line_count` 改用 `splitlines()` 与 records 同口径（原 `count("\n")` 在 bare CR / U+2028 下会与 records 数不一致）。

round-2 整改后再次全量重跑：92 条、class 89/2/1、三态 4/88/0、重复簇 6/29、shasum 不变——**数字仍逐项一致**，整改只收紧通用鲁棒性。

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

## §7d Codex round-3 复审整改记录（4/6 CLOSED → 剩 2 项 + 3 新发现全部整改）

round-3 确认 HIGH-1 与三条 LOW 已 CLOSED、台账数字有效且与 commit 字节一致，两项路径安全判 PARTIAL：

- **BLOCKER-1 残留两条绕过**：① `protected_paths` 未含**归因到的 transcript**，`--out=<唯一 transcript>` 会截断恢复源；② check-then-open 的 **TOCTOU** 仍在（检查后、打开前把 --out 换成指向 DLQ 的链接）。**整改**：① 写出前把全部 `transcript_paths` 并入保护集；② 改 `os.open(O_WRONLY|O_CREAT|O_NOFOLLOW)` **不带 O_TRUNC** 打开 → 对**实际 fd** `fstat` 校验 inode → 通过才 `ftruncate`，检查与写入作用于同一 fd，替换攻击无效。反例实测：`--out` 指向唯一 transcript → exit 2、transcript sha 不变。
- **HIGH-3 残留**：`glob(recursive=True)` 在 realpath 过滤**之前**已递归遍历（Python 3.14 glob 跟随目录 symlink 且**静默吞掉不可读子树错误**）→ 越根枚举 + "假唯一/假不可恢复"；mode `000` 的 regular transcript 仍过 `isfile()` 被判 approximate。**整改**：改 `os.walk(onerror=..., followlinks=False)`（不跟随目录 symlink、遍历错误显式捕获）+ 候选加 `os.access(R_OK)` 门；遍历受阻或存在不可读候选一律记 `attribution_conflict` 拒绝裁定（既不宣称找到、也不宣称不可恢复）。三条反例实测全部 fail-closed。
- **新 MEDIUM（JSONL framing）**：生产端 `ensure_ascii=False` 可原样写出字符串内的 U+2028，`splitlines()` 会把一条合法单-LF 记录劈成两条坏行。**整改**：新增 `_split_jsonl_lines()` 严格按 LF 分帧，header `line_count` 与 records 共用同一函数。
- **新 LOW（输入 schema）**：合法 JSON 但非对象（`null` / 数组 / 标量）解析成功后在 `rec.get()` 处抛 AttributeError 炸全量。**整改**：非 dict 归 `unparseable`（`not_a_json_object: <type>`），实测两条毒行不影响其余记录。
- **新 LOW（provenance）**：报告头只写起始基线未区分整改 artifact commit —— 已在报告头补三段 commit 链。

round-3 整改后第三次全量重跑：92 条、class 89/2/1、三态 4/88/0、重复簇 6/29、shasum 不变——**三轮整改数字全程未变**，改的全是通用鲁棒性与路径安全。

## §7e Codex round-4 复审整改记录（1/6 CLOSED → 全部 9 项整改）

round-4 只认可 1 项 CLOSED（非 dict JSON 门），并用更深的静态反例推翻了另外 5 项的"闭合"，另提 2 BLOCKER / 1 HIGH / 2 MEDIUM / 3 LOW。逐条整改（全部实测复现→封死）：

- **BLOCKER①（不可读但可写的 transcript 绕过保护集）**：mode `0200` 的候选在 unreadable 分支被清空 `transcript_paths`，因此不进保护集，`--out` 指向它仍被截断（无需竞态）。**整改**：新增 `all_candidate_paths` 保留**所有见到的候选**（含不可读、含被冲突分支清空的），写出前全部并入保护集。实测：mode 0200 候选作 `--out` → exit 2、文件字节不变。
- **BLOCKER②（源侧 TOCTOU）**：保护身份按**路径** stat 采集、DLQ 稍后才按路径读取，两步间可换入另一 inode → 实际读取对象不在保护集。**整改**：`snapshot_file()` 改为 `os.open(O_RDONLY|O_NOFOLLOW|O_NONBLOCK)` → `fstat` 取身份 + regular-file 门 → **从同一 fd 读全量**，返回的身份即**实际被读取对象**；compare 副本同样以读取身份入保护集；输入 `stat` 失败不再静默吞而是 exit 2。
- **HIGH（不可见被终态化为 unrecoverable）**：扫描受阻/冲突时主链仍产出 `unrecoverable`，与报告"既不宣称不可恢复"自相矛盾。**整改**：引入第四态 **`unverifiable`**（源可见性不足，basis 逐条说明是遍历受阻/不可读候选/归因冲突），distribution 与 `unverifiable_list` 同步。实测：不可读子树 → `unverifiable=1`，不再冒充 unrecoverable。
- **MEDIUM（FIFO/设备节点）**：`--out` 缺 regular-file gate 与 `O_NONBLOCK`。**整改**：`O_NONBLOCK` + `S_ISREG` 双门（读侧同样）。实测：FIFO 作 `--out` → exit 2 且不阻塞。
- **MEDIUM（非法 UTF-8 冒充有效记录）**：`errors="replace"` 把坏字节改写成合法对象。**整改**：`_split_jsonl_lines()` 改**逐行 strict decode**，解码失败归 `unparseable`。实测：`b'{"a":"\xff"}'` → `utf8_decode_error`，records=0。
- **LOW ×3**：dict 内字段错型防御（`name=None` / `request_id=[]` 不可哈希 / `episode_body` 非 str 均不再炸全量，按 line_no 单条成组或判 anomaly）；`transcripts_dir="/"` 的 `//` containment 特例；`0o600` 对**既有**输出文件用 `fchmod` 显式收紧（实测台账 mode 现为 `-rw-------`）。
- **LOW（provenance 自指）**：commit 无法自含己身 SHA，改用后置 `artifact-commit-receipt.txt` 绑定精确链，报告头指向该 receipt。

round-4 整改后第四次全量重跑：**92 条、class 89/2/1、三态 4/88/0（unverifiable 0）、重复簇 6/29、shasum 不变——四轮整改数字全程未变**。

## §7f Codex round-5 复审整改记录（3/8 CLOSED → 9 项全部整改）

round-5 用更深的静态反例继续推翻"闭合"，提出 2 BLOCKER / 2 HIGH / 2 MEDIUM / 3 LOW，逐条整改并实测：

- **BLOCKER①（token 冲突/无 token 时扫描前早退 → 候选不进保护集）**：`--out` 指向冲突组的候选 transcript 仍可无竞态截断。**整改**：`resolve_group_attribution()` 重写为**先扫描后判定**——无条件为每个 token 扫描收集候选进 `all_candidate_paths`（保护集口径），再做冲突/唯一性判定；候选 `stat` 失败不再 `continue` 吞掉而是 exit 2（保护集不完整即拒绝写出）。实测：冲突候选作 `--out` → exit 2、文件 sha 不变。
- **BLOCKER②（qa_metrics.db 身份未绑定实际读取）**：仍是早期 path-stat + SQLite 稍后按路径重开。**整改**：`probe_qa_metrics()` 改 `os.open(O_RDONLY|O_NOFOLLOW|O_NONBLOCK)` 取 fstat 身份 + `S_ISREG` 门 → SQLite 打开后**复核路径身份仍等于该身份**，不等即 `identity_changed_..._refused`；身份入保护集。本次运行 `file_identity_verified: true`。
- **HIGH①（anomaly 吞掉不可见性）**：`anomaly→unrecoverable` 排在 conflict 判断之前，`anomaly + 扫描受阻` 仍被假终态化。**整改**：判定链改为**可见性优先**——归因不可核验时无论 inline 状态一律 `unverifiable`，basis 逐条写明原因（无 token / token 冲突 / 扫描受阻 / 候选 stat 失败 / 不可读候选 / 多命中 ambiguous），并附注 inline 是否也 anomaly。实测：anomaly+不可读子树 → `unverifiable`。
- **HIGH②（`fchmod` 先于 protected-id 检查）**：`--out` 指向受保护的 0644 输入时，会**先把只读输入权限改成 0600** 再拒绝——字节没截断但输入已被修改。**整改**：碰撞检查前移到 `fchmod` 之前。实测：mode 644 → 644 不变。
- **MEDIUM（QA DB 无特殊文件门）**：随 BLOCKER② 一并加 `S_ISREG` + `O_NONBLOCK`。
- **MEDIUM（无 token 未扫描即判不可恢复）**：改为 `unverifiable` + `no_token` 标记（见 HIGH①）。
- **LOW ×3**：单独 `b"\n"` 现算 1 个空行（实测 `line_count=1`）；`errors="replace"` 改 **strict encode**（JSON escaped lone surrogate 不能再构造假 `full_verified`）；`bool` 是 `int` 子类 —— `episode_body_length=True` 现被长度门拒绝（实测判 anomaly）。

**归因冲突计数由 0 变为 3（如实说明）**：round-5 起"名字不含 session token"被诚实标记为 `no_token`（未做归因扫描），命中的正是 3 条 `callout_annotation` 记录。它们 inline 正文全量、sha 对账通过，**不依赖 transcript**，故仍判 `byte_exact`——三态分布不变（4/88/0/0），88 条 approximate 仍全部为唯一 transcript 命中。这是标注口径变诚实，不是结论变化。

round-5 整改后第五次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变——五轮整改数字全程未变**。


exec
/bin/zsh -lc "rg -n '原子|atomic|fsync|零写|只读|--out|完整|截断|崩溃|临时文件' '_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md' '_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:6:scope: "BATCH-2026-08-28-第五批 / CARD-G4-9 — live DLQ 92 条只读 census：分类/SHA 对账/可恢复性三态/挂载真相，产出 G4-10 交接台账"
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:13:> 这张卡**没有修任何东西，也没有恢复任何数据**——它是一次"清点尸体"的只读普查：
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:20:2. **一条都不算丢**：4 条正文完整躺在死信文件里（可逐字节恢复）；88 条只存了前 200 字预览，但每一条都顺着线索找回了**唯一**源头会话记录（7 个会话的原始 transcript 全部还在你电脑上）——可近似重建（找到了源头 ≠ 已经恢复，真正重建是 G4-10 的活）。**不可恢复：0 条**。另清点出 6 组重复（29 条是同内容反复入队），G4-10 恢复时会先去重，不会把同一段写 16 遍。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:27:| 全程零写入（裁判判据 e） | 运行前后 四份 DLQ 文件 + qa_metrics.db 的 sha256 **逐字节不变**（diff 为空 → PASS） | `_bmad-output/审查/G4-9-evidence/shasums-before.txt` / `shasums-after.txt` |
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:28:| 脚本只读自证（判据 a） | import 行全 stdlib；neo4j/graphiti/bolt/app. import **0 命中**；`--apply` 定义 **0 命中**；写模式 open 仅台账 `--out` 1 处 | `G4-9-evidence/grep-selfattest.txt` |
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:31:| inline 完整性 + SHA 对账（判据 b） | 92/92 重算 sha256 对账：4 条 full_verified、88 条 truncated_prefix（`to_dict()` 的 `[:200]` 截断，`episode_worker.py:107`）、**0 条 anomaly** | 台账 JSON 逐条 `inline_state`/`sha_check` |
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:32:| 源指针核销（判据 b，qa_metrics.db 只读 mode=ro） | `qa_error_logs` **0 行** → 0/92 可经 qa_metrics.db 溯源（诚实记录）；附加核销：llm_call_logs.db 无正文、outbox 空、episode_body_full 0 条；**有效源指针 = request_id 组内 session 归因 → 7 个 transcript 全部在盘实测存在** | 报告 §4 + 台账 `qa_metrics_probe` |
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:35:| Codex 独立审查 round-1 | **BLOCKED**（3 BLOCKER：--out 可截断输入 / 快照不原子 / 交付物未冻结；3 HIGH：inline 判定 fail-open / request_id 归因传染 / transcript 归因折叠；3 MEDIUM + 4 LOW。同时确认：**当前 92 条数字逐项 0 mismatch**、class/三态/家族计数全对） | `_bmad-output/审查/codex-review-CARD-G4-9.md` |
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:45:| Codex 复审 round-6 | **6/9 CLOSED**（visibility 优先/fchmod 顺序/no_token 语义/3 条 LOW 已闭合）；剩 2 BLOCKER + 1 MEDIUM 揭示保护集**依赖枚举完整性**的架构缺陷 + 3 新发现 | `_bmad-output/审查/codex-review-CARD-G4-9-round6.md` |
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:46:| round-6 findings 整改 | **架构级修复 + 6 项**：新增不依赖枚举的**路径层防御**（--out 禁落 transcripts 根内 / 禁等于任一输入 realpath）、QA DB 验证 fd 保持打开至复核完毕、no_token 亦扫描、证据包重生成、ledger 冲突原因自描述、lone surrogate 回退。反例实测：0333 隐藏目录内 transcript 作 --out → exit 2 完好 | 报告 §7g |
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:47:| 独立 Workflow 4-agent 复核 | G4-9 数字 agent：92 条重算 **0 mismatch**（class/inline/三态/25 request_id/7 transcript 在盘/台账 sha 全 CONFIRMED，仅 2 处描述区间 REFUTED 已修正）；只读契约 agent：与 Codex 同源的 3 条 blocker（已随上整改） | Workflow wf_737b1a95-20b journal |
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:51:- **BLOCKER-1 --out 截断风险**：任意 --out 路径 "w" 无守卫，可覆盖 DLQ 自身（双审查独立实测复现）。整改：写前 resolve() 路径碰撞守卫，命中输入集合即 exit 2；负例实测拒绝、DLQ 完好。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:52:- **BLOCKER-2 快照不原子**：records 与头部 sha 来自两次读取。整改：单次 read_bytes()，头部与逐条同源同字节。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:66:- **BLOCKER-1 未闭合**：守卫比的是路径字符串，**hardlink 与大小写别名照样截断 DLQ**。→ 改比**文件 inode 身份**；两种绕过实测双双 exit 2、DLQ sha 不变。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:77:- **BLOCKER-1 仍 PARTIAL**：① 保护集漏了**归因到的 transcript**——`--out` 指向它会截断恢复源；② check-then-open 的 **TOCTOU** 仍在。→ ① transcript 写前并入保护集；② 改 `O_NOFOLLOW` 打开且**不带 O_TRUNC**，对实际 fd `fstat` 校验后才 `ftruncate`。反例实测：exit 2、transcript 完好。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:88:- **不可读但可写（mode 0200）的 transcript 绕过保护集**：我在"不可读"分支把候选路径清空了，于是它没进保护集，`--out` 指向它照样截断——不需要任何竞态。→ 新增"全候选清单"，无论可读与否一律并入保护集。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:99:- **冲突组的候选没进保护集**：token 冲突时我在扫描**之前**就早退了，那些候选从没被看到，`--out` 指向它们照样截断。→ 改成**先扫描后判定**，无论最终是否采信，见到的候选一律进保护集。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:102:- **`fchmod` 排在碰撞检查之前**：`--out` 指向受保护的只读输入时，会先把它的权限从 644 改成 600 才发现碰撞——字节没丢但输入被改了。→ 碰撞检查前移。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:111:round-6 指出了一个我补丁修不掉的根因：**保护集依赖"能不能枚举到"**。不可列举但可穿越的目录（`0333`）里的 transcript，`os.walk` 看不见，就进不了保护集，`--out` 指向它照样截断；QA DB 的 inode 被 A→B→A 换过也一样。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:113:→ 改为**双层防御**：在 inode 保护集之外，加一层**不依赖枚举**的路径判断——`--out` 的真实路径不得落在 transcripts 根目录内（整个恢复源区域禁写），也不得等于任何输入文件的真实路径。实测：隐藏目录内的 transcript 作 `--out`，inode 保护集根本没看见它，路径层直接拦住，exit 2、文件完好。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:121:- `backend/scripts/census_dead_letter_episodes.py` — 唯一代码产物（只读 census 脚本，纯 stdlib）
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:4:> **性质**: 纯只读 census。0 写入、0 重放、0 业务代码改动。唯一代码产物 = `backend/scripts/census_dead_letter_episodes.py`。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:36:| class | 条数 | 预期 | error_type | 错误原文（截断） | 根因与修复状态 |
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:45:## §3 inline 完整性 + SHA 对账
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:47:`DeadLetterStore.store()` 落盘的 `episode_body` 来自 `EpisodeTask.to_dict()`，后者做 `episode_body[:200]` 截断（`episode_worker.py:107`，"truncate for logging"）；全量正文只有 `DEAD_LETTER_STORE_FULL_BODY` 开启时以 `episode_body_full` 另存——**live 容器该 env 未设置（实测），92 条 `episode_body_full` 均缺席**。逐条重算 sha256(inline) 对账 `episode_body_sha256` 结果：
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:51:| `full_verified`（内联全量，sha 对账通过） | **4** | 重算值 == 声明值且长度精确匹配（四条正文实为 131/142/150/180 字符，范围 **131–180**，天然未截断；round-2 LOW 修正） |
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:57:## §4 源指针核销（qa_metrics.db，只读 mode=ro）
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:64:- **有效源指针只剩一条**：DLQ 记录的 `request_id`（structlog contextvars 捕获的进程内值）把同一次 SessionEnd 归档的 3–5 条 episode 绑成组，组内 `session-archive:<id16>` / `…session:<hex>` 名字携带 session id → `~/.claude/projects/-…-canvas-vault/<session>.jsonl` transcript。**7 个 session 的 transcript 全部在盘实测存在**（90,584–723,950 字节，逐一恰 1 个 glob 命中、常规文件），88/88 条截断记录归因成功、0 条归因冲突。**归因边界（诚实声明）**：归因 = "唯一在盘候选已定位"，≠ "内容已验证"——本卡未读任何 transcript 内容，内容级核验归 G4-10 重建时以 `episode_body_sha256` 对账。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:72:| **不可恢复**（unrecoverable） | **0** | inline 截断且经完整可见的扫描确认无在盘上游源 |
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:83:**隐私（MEDIUM-3 整改）**：`transcript_paths` 含本机用户名与完整 session UUID，台账与本报告为 **private-only 工件**（台账头部已带 privacy 字段；仓库纪律 = 不 push 公网远端）。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:92:| grep 自证（import 行全 stdlib；neo4j/graphiti/bolt/app. import 0 命中；`--apply` 定义 0 命中；写模式 open 仅 `--out` 1 处且受路径碰撞守卫保护） | **PASS**（`grep-selfattest.txt`，含守卫在位证明） |
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:95:| 负例门（round-1 整改自证） | `--out`==`--dlq` → exit 2 拒写、DLQ 完好；transcripts 根缺失 → exit 2 拒诊；sha 匹配但长度不符（round-1 HIGH-1 反例①）→ anomaly/unrecoverable；坏 JSON 行/空行 → unparseable 逐行入台账不拒诊 |
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:96:| 负例门（round-2 整改自证） | **hardlink** 指向 DLQ 的 --out → exit 2 + DLQ sha 不变；**case-only 别名**（`DLQ.jsonl`）→ exit 2 + DLQ 完好；**anomaly + episode_body_full 组合**（sha 对但长度 999）→ anomaly/unrecoverable（不再翻案 byte_exact）；**chmod 000 根** → exit 2 拒诊；**symlink 逃逸**（根内 .jsonl → 根外 .txt）→ match_count=0/unrecoverable；正例回归：真实唯一命中仍 approximate |
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:100:- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:101:- **BLOCKER-2（快照不原子）**：DLQ 单次 `read_bytes()`，头部 sha256/line_count 与逐条 records 派生自同一份内存字节；mtime 显式标注为 stat 参考值。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:103:- **HIGH-1（inline 判定不 fail-closed）**：full_verified 加长度精确匹配门；truncated_prefix 加 64-hex 合法性门；anomaly 一律 unrecoverable + 如实 basis（不再谎称截断、不再滑入 approximate）。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:117:- **BLOCKER-1 NOT-CLOSED（hardlink / case-only 别名绕过）**：原守卫比较 `resolve()` **字符串**，hardlink 指向输入、以及大小写不敏感文件系统上的 case-only 别名均绕过并截断输入。**整改**：改为比较**文件身份 `(st_dev, st_ino)`**（对已存在的 --out）+ 保留路径比较作第二道。负例实测：两种绕过均 exit 2、DLQ sha 不变。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:134:  --out "_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json"
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:143:- **BLOCKER-1 残留两条绕过**：① `protected_paths` 未含**归因到的 transcript**，`--out=<唯一 transcript>` 会截断恢复源；② check-then-open 的 **TOCTOU** 仍在（检查后、打开前把 --out 换成指向 DLQ 的链接）。**整改**：① 写出前把全部 `transcript_paths` 并入保护集；② 改 `os.open(O_WRONLY|O_CREAT|O_NOFOLLOW)` **不带 O_TRUNC** 打开 → 对**实际 fd** `fstat` 校验 inode → 通过才 `ftruncate`，检查与写入作用于同一 fd，替换攻击无效。反例实测：`--out` 指向唯一 transcript → exit 2、transcript sha 不变。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:155:- **BLOCKER①（不可读但可写的 transcript 绕过保护集）**：mode `0200` 的候选在 unreadable 分支被清空 `transcript_paths`，因此不进保护集，`--out` 指向它仍被截断（无需竞态）。**整改**：新增 `all_candidate_paths` 保留**所有见到的候选**（含不可读、含被冲突分支清空的），写出前全部并入保护集。实测：mode 0200 候选作 `--out` → exit 2、文件字节不变。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:158:- **MEDIUM（FIFO/设备节点）**：`--out` 缺 regular-file gate 与 `O_NONBLOCK`。**整改**：`O_NONBLOCK` + `S_ISREG` 双门（读侧同样）。实测：FIFO 作 `--out` → exit 2 且不阻塞。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:169:- **BLOCKER①（token 冲突/无 token 时扫描前早退 → 候选不进保护集）**：`--out` 指向冲突组的候选 transcript 仍可无竞态截断。**整改**：`resolve_group_attribution()` 重写为**先扫描后判定**——无条件为每个 token 扫描收集候选进 `all_candidate_paths`（保护集口径），再做冲突/唯一性判定；候选 `stat` 失败不再 `continue` 吞掉而是 exit 2（保护集不完整即拒绝写出）。实测：冲突候选作 `--out` → exit 2、文件 sha 不变。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:172:- **HIGH②（`fchmod` 先于 protected-id 检查）**：`--out` 指向受保护的 0644 输入时，会**先把只读输入权限改成 0600** 再拒绝——字节没截断但输入已被修改。**整改**：碰撞检查前移到 `fchmod` 之前。实测：mode 644 → 644 不变。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:185:> 我的 `--out` 保护集依赖**枚举完整性**——只要某个真实源没被 `os.walk` 看到（不可列举但可穿越的 `0333` 子目录），或 inode 被 A→B→A 换过（QA DB 的 ABA），它就不在集合里，`--out` 指向它仍可截断。这不是补丁能修的，是设计缺陷。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:187:- **BLOCKER①②的架构级修复**：增加**不依赖枚举的路径层防御**——`--out` 的 `realpath` 不得落在 transcripts 根内（恢复源区域整体禁写）、不得等于任一输入路径的 `realpath`。路径层 + inode 层双保险，任一命中即拒。实测：`0333` 隐藏目录内的 transcript 作 `--out` → exit 2、文件完好（inode 保护集根本没看见它，路径层拦住了）。

exec
/bin/zsh -lc "sed -n '1,200p' '_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
---
type: uat
title: "UAT · CARD-G4-9 DLQ 真实挂载 census 分诊（2026-08-28）"
date: 2026-08-28
status: awaiting_user
scope: "BATCH-2026-08-28-第五批 / CARD-G4-9 — live DLQ 92 条只读 census：分类/SHA 对账/可恢复性三态/挂载真相，产出 G4-10 交接台账"
worktree: "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census"
---

# UAT · CARD-G4-9 DLQ 真实挂载 census 分诊

> [!info]+ 你不需要碰命令行 — 全部技术验证我已代跑（结果见下）
> 这张卡**没有修任何东西，也没有恢复任何数据**——它是一次"清点尸体"的只读普查：
> 线上 Graphiti 写入失败后落进死信文件的 92 条记录，逐条查清"是什么死的、还能不能救、去哪里救"，
> 给后续的 G4-10（真正做恢复的卡）留一份带稳定编号的台账。卡面如实标注：离日常使用价值远，属恢复能力地基。

## 📌 你需要过目的三个结论

1. **92 条死信全部查清、零"待定"**：89 条是"内容太长超过本地模型 16384 token 上限"（未修，根因归 G4-10）；2 条是 5 月 14 日的 schema 冲突、1 条是旧 group_id 冒号格式——这 3 条的根因**当天之后就已修复**，不会再新增。
2. **一条都不算丢**：4 条正文完整躺在死信文件里（可逐字节恢复）；88 条只存了前 200 字预览，但每一条都顺着线索找回了**唯一**源头会话记录（7 个会话的原始 transcript 全部还在你电脑上）——可近似重建（找到了源头 ≠ 已经恢复，真正重建是 G4-10 的活）。**不可恢复：0 条**。另清点出 6 组重复（29 条是同内容反复入队），G4-10 恢复时会先去重，不会把同一段写 16 遍。
3. **死信文件的"真身"只有一处**：线上容器读写的是 `feature-obsidian-hybrid-dev` worktree 的 `backend/data/`（容器内实测 sha 一致）；主仓那份 685 行是 4 月的陈旧副本，另有两处孤儿残留——报告里有四址对照表，以后不会再查错文件。

## ✅ 技术验证（Claude 已代跑）

| 项 | 结果 | 证据 |
|---|---|---|
| 全程零写入（裁判判据 e） | 运行前后 四份 DLQ 文件 + qa_metrics.db 的 sha256 **逐字节不变**（diff 为空 → PASS） | `_bmad-output/审查/G4-9-evidence/shasums-before.txt` / `shasums-after.txt` |
| 脚本只读自证（判据 a） | import 行全 stdlib；neo4j/graphiti/bolt/app. import **0 命中**；`--apply` 定义 **0 命中**；写模式 open 仅台账 `--out` 1 处 | `G4-9-evidence/grep-selfattest.txt` |
| live 挂载真相（判据 c） | 容器内 `sha256sum /app/data/dead_letter_episodes.jsonl` = 宿主 live 地址同值（92 行，`3b37460f…`）；compose :206-212 遮蔽史入报告 §1 | `G4-9-evidence/container-sha-check.txt` + 报告 §1 |
| 分类零偏差（判据 b） | budget_400×**89** / schema×**2**（P0-4 已修，`entity_types.py:343`）/ group_id×**1**（sanitize 已兜，`group_id_compat.py:64`）——与勘探预期逐条一致，脚本 `class_deviation` 字段为空 | 台账 JSON `class_distribution` |
| inline 完整性 + SHA 对账（判据 b） | 92/92 重算 sha256 对账：4 条 full_verified、88 条 truncated_prefix（`to_dict()` 的 `[:200]` 截断，`episode_worker.py:107`）、**0 条 anomaly** | 台账 JSON 逐条 `inline_state`/`sha_check` |
| 源指针核销（判据 b，qa_metrics.db 只读 mode=ro） | `qa_error_logs` **0 行** → 0/92 可经 qa_metrics.db 溯源（诚实记录）；附加核销：llm_call_logs.db 无正文、outbox 空、episode_body_full 0 条；**有效源指针 = request_id 组内 session 归因 → 7 个 transcript 全部在盘实测存在** | 报告 §4 + 台账 `qa_metrics_probe` |
| 可恢复性三态（判据 b） | 可字节级 **4** / 近似 **88** / 不可恢复 **0**；不可恢复清单显式成段 0 条、"待定" 0 条 | 报告 §5 + 台账 `recoverability_distribution` |
| G4-10 稳定键（判据 d） | 逐条复合键 `{line_no, sha256_prefix, request_id}` + 台账头部冻结文件 sha；request_id 92 条仅 25 唯一值的实测证明单列不可作键 | 报告 §6 + 台账 `records[].stable_key` |
| Codex 独立审查 round-1 | **BLOCKED**（3 BLOCKER：--out 可截断输入 / 快照不原子 / 交付物未冻结；3 HIGH：inline 判定 fail-open / request_id 归因传染 / transcript 归因折叠；3 MEDIUM + 4 LOW。同时确认：**当前 92 条数字逐项 0 mismatch**、class/三态/家族计数全对） | `_bmad-output/审查/codex-review-CARD-G4-9.md` |
| Codex findings 逐条整改 | **13/13 完成**（见下）；整改版脚本负例门全过；全量重跑数字与整改前逐项一致 | 报告 §7/§7b + 证据包 |
| Codex 复审 round-2 | **仍阻断**（10/13 CLOSED；BLOCKER-1/HIGH-1/HIGH-3 未真正闭合 + 3 新 LOW）。同时独立复算确认：67ccebe1 冻结生效、92 条数字与 6/29 重复簇全部可复算 | `_bmad-output/审查/codex-review-CARD-G4-9-round2.md`（codex 被 cyber 误拦，内容由 stdout 抢救存档） |
| round-2 findings 逐条整改 | **6/6 完成**：inode 身份守卫封 hardlink+大小写别名 / full_body 长度门+anomaly 前置 / 不可读根 exit 2+symlink 逃逸拒采信 / 3 新 LOW。5 条新负例实测全过、正例无回归、数字仍逐项一致 | 报告 §7/§7c + `grep-selfattest.txt` |
| Codex 复审 round-3 | **仍阻断**（4/6 CLOSED；BLOCKER-1/HIGH-3 判 PARTIAL + 1 新 MEDIUM + 2 新 LOW）。同时确认：HIGH-1 与三条 LOW 已闭合、台账数字有效且与 commit 字节一致 | `_bmad-output/审查/codex-review-CARD-G4-9-round3.md` |
| round-3 findings 逐条整改 | **6/6 完成**：transcript 并入保护集 / O_NOFOLLOW+fstat 消 TOCTOU / os.walk 替 glob（不跟随目录 symlink+遍历错误显式捕获）/ 不可读候选 fail-closed / JSONL 严格 LF 分帧 / 非 dict 归 unparseable。6 条新反例实测全过、数字第三次不变 | 报告 §7d + `grep-selfattest.txt` |
| Codex 复审 round-4 | **仍阻断**（1/6 CLOSED；2 新 BLOCKER + 1 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round4.md` |
| round-4 findings 逐条整改 | **9/9 完成**：全候选入保护集 / 读侧 fd 身份消源侧 TOCTOU / 新增 unverifiable 第四态 / FIFO 设备门 / strict UTF-8 / 3 条错型与边界 LOW / provenance receipt。5 条新反例实测全过；第四次全量重跑数字仍不变 | 报告 §7e + `grep-selfattest.txt` |
| Codex 复审 round-5 | **仍阻断**（3/8 CLOSED；2 BLOCKER + 2 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round5.md` |
| round-5 findings 逐条整改 | **9/9 完成**：先扫描后判定（冲突候选亦入保护集）/ QA DB fd 身份+复核 / 可见性优先于 anomaly / fchmod 后置于碰撞检查 / QA DB 特殊文件门 / no_token 归 unverifiable / 3 条 LOW。6 条新反例实测全过；第五次全量重跑数字仍不变 | 报告 §7f |
| Codex 复审 round-6 | **6/9 CLOSED**（visibility 优先/fchmod 顺序/no_token 语义/3 条 LOW 已闭合）；剩 2 BLOCKER + 1 MEDIUM 揭示保护集**依赖枚举完整性**的架构缺陷 + 3 新发现 | `_bmad-output/审查/codex-review-CARD-G4-9-round6.md` |
| round-6 findings 整改 | **架构级修复 + 6 项**：新增不依赖枚举的**路径层防御**（--out 禁落 transcripts 根内 / 禁等于任一输入 realpath）、QA DB 验证 fd 保持打开至复核完毕、no_token 亦扫描、证据包重生成、ledger 冲突原因自描述、lone surrogate 回退。反例实测：0333 隐藏目录内 transcript 作 --out → exit 2 完好 | 报告 §7g |
| 独立 Workflow 4-agent 复核 | G4-9 数字 agent：92 条重算 **0 mismatch**（class/inline/三态/25 request_id/7 transcript 在盘/台账 sha 全 CONFIRMED，仅 2 处描述区间 REFUTED 已修正）；只读契约 agent：与 Codex 同源的 3 条 blocker（已随上整改） | Workflow wf_737b1a95-20b journal |

## 🔧 Codex round-1 整改记录（13/13 关闭，BLOCKED → 整改完毕）

- **BLOCKER-1 --out 截断风险**：任意 --out 路径 "w" 无守卫，可覆盖 DLQ 自身（双审查独立实测复现）。整改：写前 resolve() 路径碰撞守卫，命中输入集合即 exit 2；负例实测拒绝、DLQ 完好。
- **BLOCKER-2 快照不原子**：records 与头部 sha 来自两次读取。整改：单次 read_bytes()，头部与逐条同源同字节。
- **BLOCKER-3 交付物漂移**：审查期间脚本/报告 sha 变化且未 track。整改：本卡 commit 冻结全部 exact bytes；自证文件内嵌脚本 sha 前缀。
- **HIGH-1 inline 判定 fail-open**：sha 匹配但长度不符会误判 full_verified（反例实测）。整改：长度精确匹配门 + 64-hex 合法性门 + anomaly 一律 fail-closed（unrecoverable + 如实 basis）。
- **HIGH-2 request_id 归因传染**：缺失值合入 "None" 组、跨类型合组、多 token 静默取长。整改：(类型,值) 复合键 + 缺失单条成组 + 前缀一致门（冲突拒采信）。
- **HIGH-3 transcript 归因折叠**：多命中照单全收、目录缺失误判 unrecoverable=88（实测复现）。整改：恰 1 常规文件命中门 + 递归 glob + 目录缺失 exit 2 拒诊。
- **MEDIUM-1~3**：episode_body_full 采信通路 / duplicate_clusters 6 簇 29 行 + reference_time 透传 / privacy 字段与 private-only 声明。
- **LOW-1~4**：两处区间修正（16948–20831、205–8036）/ 稳定键语义重写为"冻结快照 occurrence key" / schema 双处证据（LearningConcept.name + LearningTip.created_at）/ 挂载历史证据边界声明。

整改后全量重跑：92 条数字与整改前**逐项一致**（4/88/0、89/2/1、冲突 0、unparseable 0）——整改只收紧契约与通用鲁棒性，不改变本次 census 结论。

## 🔧 Codex round-2 复审整改记录（10/13 CLOSED → 剩 3 项 + 3 新 LOW 全关闭）

round-2 用真实入口反例证明我 round-1 的三处整改**没有真正闭合**（这正是二轮审查的价值）：

- **BLOCKER-1 未闭合**：守卫比的是路径字符串，**hardlink 与大小写别名照样截断 DLQ**。→ 改比**文件 inode 身份**；两种绕过实测双双 exit 2、DLQ sha 不变。
- **HIGH-1 未闭合**：`episode_body_full` 分支只核 sha 不核长度且排在 anomaly 之前，**anomaly 记录能翻案成"可字节级恢复"**。→ 加长度门 + 判定顺序改为 anomaly 优先；反例实测翻转。
- **HIGH-3 未闭合**：`chmod 000` 的目录仍 exit 0 并把全部记录**假判不可恢复**；symlink 可指到目录外冒充源。→ 不可读即 exit 2；symlink 与逃逸目标一律不采信；正例（真实唯一命中）无回归。
- **3 新 LOW**：full_verified 长度范围修正 131–180；台账三个 distribution 补零并新增 `inline_state_distribution`；`line_count` 与 records 改用同一 `splitlines()` 口径。

round-2 整改后再次全量重跑：92 条、4/88/0、89/2/1、6 簇 29 行、shasum 不变——**数字全程未变**。

## 🔧 Codex round-3 复审整改记录（4/6 CLOSED → 剩 2 项 + 3 新发现全关闭）

round-3 确认 HIGH-1 与三条 LOW 真正闭合、台账数字有效，又在两项路径安全上找到更深的绕过：

- **BLOCKER-1 仍 PARTIAL**：① 保护集漏了**归因到的 transcript**——`--out` 指向它会截断恢复源；② check-then-open 的 **TOCTOU** 仍在。→ ① transcript 写前并入保护集；② 改 `O_NOFOLLOW` 打开且**不带 O_TRUNC**，对实际 fd `fstat` 校验后才 `ftruncate`。反例实测：exit 2、transcript 完好。
- **HIGH-3 仍 PARTIAL**：Python 3.14 的 `glob` 在过滤前就已递归、跟随目录 symlink 且**静默吞掉不可读子树错误**；mode 000 的文件仍过 `isfile()` 被当可用源。→ 改 `os.walk(onerror=, followlinks=False)` + `os.access(R_OK)` 门；遍历受阻或有不可读候选一律拒绝裁定。三反例实测 fail-closed。
- **新 MEDIUM（JSONL 分帧）**：`splitlines()` 会把含 U+2028 的合法单行记录劈成两条坏行。→ 严格按 LF 分帧，header 与 records 共用同一函数。
- **新 LOW ×2**：非 dict JSON（`null`/数组）归 unparseable 不再炸全量；报告头补 artifact commit 链。

round-3 整改后第三次全量重跑：**92 条、4/88/0、89/2/1、6/29、shasum 不变——三轮整改数字全程未变**，改的全是通用鲁棒性与路径安全。

## 🔧 Codex round-4 复审整改记录（1/6 CLOSED → 9 项全关闭）

round-4 只认 1 项闭合，用更深的反例推翻其余"闭合"——两条新 BLOCKER 都是真的：

- **不可读但可写（mode 0200）的 transcript 绕过保护集**：我在"不可读"分支把候选路径清空了，于是它没进保护集，`--out` 指向它照样截断——不需要任何竞态。→ 新增"全候选清单"，无论可读与否一律并入保护集。
- **源侧 TOCTOU**：保护身份按路径 stat 采集、DLQ 稍后才按路径读取，中间可换 inode。→ 改为**从 fd 读取**：打开一次 → `fstat` 取身份 → 从同一 fd 读全量，保护的就是实际读到的那个对象。
- **把"看不见"说成"不可恢复"**：扫描受阻时仍输出 `unrecoverable`，与报告里"既不宣称不可恢复"自相矛盾。→ 新增第四态 **`unverifiable`**，逐条写明是遍历受阻还是候选不可读。
- **其余 5 项**：FIFO/设备节点门（`O_NONBLOCK`+`S_ISREG`）、非法 UTF-8 不再经 replace 冒充有效记录（strict decode）、三条错型与边界 LOW（`name=None`/`request_id=[]`/根为 `/`）、既有输出文件 `fchmod` 收紧（台账现为 `-rw-------`）、provenance 改后置 receipt 绑定精确 commit 链。

round-4 整改后第四次全量重跑：**92 条、4/88/0（unverifiable 0）、89/2/1、6/29、shasum 不变——四轮整改数字全程未变**。

## 🔧 Codex round-5 复审整改记录（3/8 CLOSED → 9 项全关闭）

round-5 继续深挖，两条新 BLOCKER 与两条 HIGH 都成立：

- **冲突组的候选没进保护集**：token 冲突时我在扫描**之前**就早退了，那些候选从没被看到，`--out` 指向它们照样截断。→ 改成**先扫描后判定**，无论最终是否采信，见到的候选一律进保护集。
- **qa_metrics.db 身份没绑定实际读取**：先按路径 stat、SQLite 稍后按路径重开，中间可换。→ 改 fd 取身份 + 打开后复核身份一致。
- **anomaly 吞掉了"看不见"**：`anomaly→unrecoverable` 排在可见性判断之前，扫描受阻时仍断言"不可恢复"。→ 判定链改为**可见性优先**。
- **`fchmod` 排在碰撞检查之前**：`--out` 指向受保护的只读输入时，会先把它的权限从 644 改成 600 才发现碰撞——字节没丢但输入被改了。→ 碰撞检查前移。
- **其余 5 项**：QA DB 特殊文件门、无 token 归 `unverifiable`、单独换行算 1 空行、strict encode 堵住 lone surrogate 伪造 `full_verified`、`bool` 不再通过长度门。

**一处计数如实变化**：归因冲突 0→3。因为"名字不含 session token"现在被诚实标为"未做归因扫描"，正是那 3 条 callout 记录；它们 inline 全量、不依赖 transcript，仍是可字节级恢复。**三态分布不变**（4/88/0/0）——是标注变诚实，不是结论变化。

round-5 整改后第五次全量重跑：**92 条、4/88/0/0、89/2/1、6/29、shasum 不变——五轮整改数字全程未变**。

## 🔧 Codex round-6 复审整改记录（6/9 CLOSED → 架构级修复）

round-6 指出了一个我补丁修不掉的根因：**保护集依赖"能不能枚举到"**。不可列举但可穿越的目录（`0333`）里的 transcript，`os.walk` 看不见，就进不了保护集，`--out` 指向它照样截断；QA DB 的 inode 被 A→B→A 换过也一样。

→ 改为**双层防御**：在 inode 保护集之外，加一层**不依赖枚举**的路径判断——`--out` 的真实路径不得落在 transcripts 根目录内（整个恢复源区域禁写），也不得等于任何输入文件的真实路径。实测：隐藏目录内的 transcript 作 `--out`，inode 保护集根本没看见它，路径层直接拦住，exit 2、文件完好。

另修：QA DB 的验证 fd 改为**保持打开**到复核完毕（堵 ABA）；`no_token` 分支也扫描（原本完全不扫，候选进不了保护集）；证据包每轮重生成（round-6 指出我的 self-attest 停留在 round-4 的旧 SHA，属实）；台账新增冲突原因自描述。

round-6 整改后第六次全量重跑：**92 条、4/88/0/0、89/2/1、6/29、shasum 不变——六轮整改数字全程未变**。

## 📄 交付物清单（全部新增，零业务代码改动）

- `backend/scripts/census_dead_letter_episodes.py` — 唯一代码产物（只读 census 脚本，纯 stdlib）
- `_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md` — census 报告（挂载真相/分类/三态/交接契约）
- `_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json` — 92 条逐条台账（G4-10 消费）
- `_bmad-output/审查/G4-9-evidence/` — 证据包（shasums ×2、grep 自证、容器 sha 实测、运行日志）
- `_bmad-output/审查/codex-review-CARD-G4-9.md` — Codex 独立审查存档

## ⏭️ 移交（不在本卡范围）

- **G4-10**：89 条 budget_400 根因修复（16384 context 超限 → 切块或提 budget）+ 按台账重放；3 条 `vault:default` 旧格式重放前需 group 重映射。
- **DeadLetterStore 全量正文开关**：`DEAD_LETTER_STORE_FULL_BODY` live 未启用是 88 条只剩前缀的直接原因——是否开启（隐私 vs 可恢复性权衡）留 G4-10 连根因一并裁。

exec
/bin/zsh -lc 'git status --short --branch' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
## card/s5-census
?? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round7.md"

exec
/bin/zsh -lc "python3 -B -c 'import ast,pathlib; p=pathlib.Path(\"backend/scripts/census_dead_letter_episodes.py\"); ast.parse(p.read_bytes(),filename=str(p)); print(\"ast_parse=PASS\")'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
ast_parse=PASS

exec
/bin/zsh -lc "python3 -B -c 'import ast,pathlib; p=pathlib.Path(\"backend/scripts/census_dead_letter_episodes.py\"); t=ast.parse(p.read_bytes()); imports=[]; applies=[]; opens=[]
for n in ast.walk(t):
 if isinstance(n,(ast.Import,ast.ImportFrom)): imports.append(ast.unparse(n))
 if isinstance(n,ast.Call):
  try: f=ast.unparse(n.func)
  except Exception: f=\"?\"
  if f in {\"open\",\"os.open\",\"os.fdopen\",\"sqlite3.connect\"}: opens.append((n.lineno,f,ast.unparse(n)))
  if any(isinstance(a,ast.Constant) and a.value==\"--apply\" for a in n.args): applies.append(n.lineno)
print({\"imports\":imports,\"apply_defs\":applies,\"open_calls\":opens})'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
{'imports': ['from __future__ import annotations', 'import argparse', 'import hashlib', 'import json', 'import os', 'import re', 'import sqlite3', 'import stat', 'import sys', 'from collections import Counter, defaultdict', 'from datetime import datetime, timezone', 'from pathlib import Path'], 'apply_defs': [], 'open_calls': [(337, 'os.open', 'os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)'), (277, 'os.open', 'os.open(db_path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)'), (292, 'sqlite3.connect', 'sqlite3.connect(uri, uri=True)'), (738, 'os.open', 'os.open(args.out, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 384)'), (760, 'os.fdopen', "os.fdopen(fd, 'w', encoding='utf-8', closefd=True)")]}

**Assessing output integrity severity**
**Evaluating publication integrity and conflict handling**
**Identifying minor attribution reason limitation**
**Analyzing SQLite connection race conditions**
**Evaluating SQLite sidecar creation and path escaping**
**Planning update strategy**
checkout/commit、五项代码、路径反例、ledger/receipt 已完成独立复算；当前进行最终交叉核验与严重度归并。
  ✓ 核对 checkout、commit/receipt 链及 round-6 基线
  ✓ 静态审阅五项修复及生产入口控制流
  ✓ 设计并只读验证路径、inode、TOCTOU 新反例
  ✓ 从原始工件独立复算台账与证据包指标
  → 交叉核验后给出逐项 CLOSED/NOT-CLOSED 与总裁定
mcp: sequential-thinking/sequentialthinking started
mcp: sequential-thinking/sequentialthinking (completed)
**Planning local man page retrieval for O_NOFOLLOW**
**Verifying ledger and script line references**
**Validating hardlink creation under OS constraints**
**Confirming symlink and hardlink detection**
**Analyzing TOCTOU symlink and hardlink bypasses**
**Reviewing closure of issues**
**Separating reason and surrogate items**
**Clarifying blocker counts and assertion statuses**
**Highlighting carry-over URI blocker**
**Analyzing SQLite URI mode parsing**
**Categorizing blockers and semantic issues**
**Highlighting receipt SHA abbreviation limitation**
**Closing issue #4 with limitations**
**Confirming ledger 92 class attributes**
exec
/bin/zsh -lc "nl -ba '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' | sed -n '1,115p;188,266p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
     1	{
     2	 "card": "CARD-G4-9",
     3	 "generated_at": "2026-08-28T12:47:55.648376+00:00",
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
   202	   "attribution_conflict_reason": "no_token",
   203	   "recoverability": "byte_exact",
   204	   "recoverability_basis": "inline 正文全量：sha256 重算与声明一致且长度精确匹配"
   205	  },
   206	  {
   207	   "stable_key": {
   208	    "line_no": 2,
   209	    "sha256_prefix": "b91bf262cadab596",
   210	    "request_id": "281466014769488"
   211	   },
   212	   "name": "callout_annotation:递归 base case 概念",
   213	   "group_id": "vault:default",
   214	   "source_description": "callout-annotation-record",
   215	   "error_type": "EntityTypeValidationError",
   216	   "error_excerpt": "created_at cannot be used as an attribute for LearningTip as it is a protected attribute name.",
   217	   "failed_at": "2026-05-14T08:25:15.775179+00:00",
   218	   "reference_time": "2026-05-14T08:25:06.180046+00:00",
   219	   "class": "schema_entity_type",
   220	   "episode_body_length": 150,
   221	   "episode_body_sha256": "b91bf262cadab596d55224b87c96af09b28025996b0040883b58a025cf2ebd4a",
   222	   "inline_state": "full_verified",
   223	   "sha_check": "pass",
   224	   "session_token": null,
   225	   "transcript_paths": [],
   226	   "transcript_match_count": 0,
   227	   "attribution_conflict": true,
   228	   "attribution_conflict_reason": "no_token",
   229	   "recoverability": "byte_exact",
   230	   "recoverability_basis": "inline 正文全量：sha256 重算与声明一致且长度精确匹配"
   231	  },
   232	  {
   233	   "stable_key": {
   234	    "line_no": 3,
   235	    "sha256_prefix": "55b1b793b99778eb",
   236	    "request_id": "281466427090256"
   237	   },
   238	   "name": "callout_annotation:递归 base case",
   239	   "group_id": "vault:default",
   240	   "source_description": "callout-annotation-record",
   241	   "error_type": "GroupIdValidationError",
   242	   "error_excerpt": "group_id \"vault:default\" must contain only alphanumeric characters, dashes, or underscores",
   243	   "failed_at": "2026-05-14T08:31:54.970785+00:00",
   244	   "reference_time": "2026-05-14T08:31:50.054921+00:00",
   245	   "class": "group_id_format",
   246	   "episode_body_length": 131,
   247	   "episode_body_sha256": "55b1b793b99778eb0c117b65ad14e4a77dd045d4f50163c0274054b6adaf4da2",
   248	   "inline_state": "full_verified",
   249	   "sha_check": "pass",
   250	   "session_token": null,
   251	   "transcript_paths": [],
   252	   "transcript_match_count": 0,
   253	   "attribution_conflict": true,
   254	   "attribution_conflict_reason": "no_token",
   255	   "recoverability": "byte_exact",
   256	   "recoverability_basis": "inline 正文全量：sha256 重算与声明一致且长度精确匹配"
   257	  },
   258	  {
   259	   "stable_key": {
   260	    "line_no": 4,
   261	    "sha256_prefix": "89199bd0eeb62ce2",
   262	    "request_id": "281466685033808"
   263	   },
   264	   "name": "conversation_distillation:Distilled summary for node session:e8eff",
   265	   "group_id": "vault:canvas_vault",
   266	   "source_description": "canvas_learning:conversation_distillation",

exec
/bin/zsh -lc "nl -ba '_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md' | sed -n '180,200p'; nl -ba '_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md' | sed -n '105,120p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
   180	
   181	## §7g Codex round-6 复审整改记录（6/9 CLOSED → 架构级修复 + 全部余项）
   182	
   183	round-6 确认 visibility 优先、fchmod 顺序、no_token 语义、三条 LOW 共 6 项 CLOSED，并揭示了一个**架构层面的根因**：
   184	
   185	> 我的 `--out` 保护集依赖**枚举完整性**——只要某个真实源没被 `os.walk` 看到（不可列举但可穿越的 `0333` 子目录），或 inode 被 A→B→A 换过（QA DB 的 ABA），它就不在集合里，`--out` 指向它仍可截断。这不是补丁能修的，是设计缺陷。
   186	
   187	- **BLOCKER①②的架构级修复**：增加**不依赖枚举的路径层防御**——`--out` 的 `realpath` 不得落在 transcripts 根内（恢复源区域整体禁写）、不得等于任一输入路径的 `realpath`。路径层 + inode 层双保险，任一命中即拒。实测：`0333` 隐藏目录内的 transcript 作 `--out` → exit 2、文件完好（inode 保护集根本没看见它，路径层拦住了）。
   188	- **BLOCKER② 补充修复**：QA DB 的验证 fd 原本验证完即关闭、SQLite 再按路径重开（ABA 可绕）。改为**验证 fd 保持打开**直到 SQLite 连接建立并复核完毕，且连接后二次 `fstat` 该 fd 校验身份未变且 `st_nlink != 0`。本次运行 `file_identity_verified: true`。
   189	- **BLOCKER① 补充修复**：`no_token` 分支原本完全不扫描（`all_candidate_paths=[]`）→ 改为**无论有无 token 都遍历**，所有 `.jsonl` 一律入保护集口径。
   190	- **MEDIUM（证据包漂移）**：`grep-selfattest.txt` 曾停留在 round-4 的脚本 SHA 与旧行号、receipt 未含最新 commit——这是我的疏漏。已重生成（内嵌当前脚本 sha256 + 生成时点声明），receipt 随本轮补链。
   191	- **LOW ×3**：ledger 新增 `attribution_conflict_reason` 自描述（本次 92 条：`no_token` 3 / 其余 89 无冲突）；`json.dumps` 对 lone surrogate 回退 `ensure_ascii=True` 并显式标注，不再整次 census 拒绝；`stat_failures` 分支保留（Codex 确认非额外绕过，仅基本不可达）。
   192	
   193	round-6 整改后第六次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变——六轮整改数字全程未变**。
   105	**一处计数如实变化**：归因冲突 0→3。因为"名字不含 session token"现在被诚实标为"未做归因扫描"，正是那 3 条 callout 记录；它们 inline 全量、不依赖 transcript，仍是可字节级恢复。**三态分布不变**（4/88/0/0）——是标注变诚实，不是结论变化。
   106	
   107	round-5 整改后第五次全量重跑：**92 条、4/88/0/0、89/2/1、6/29、shasum 不变——五轮整改数字全程未变**。
   108	
   109	## 🔧 Codex round-6 复审整改记录（6/9 CLOSED → 架构级修复）
   110	
   111	round-6 指出了一个我补丁修不掉的根因：**保护集依赖"能不能枚举到"**。不可列举但可穿越的目录（`0333`）里的 transcript，`os.walk` 看不见，就进不了保护集，`--out` 指向它照样截断；QA DB 的 inode 被 A→B→A 换过也一样。
   112	
   113	→ 改为**双层防御**：在 inode 保护集之外，加一层**不依赖枚举**的路径判断——`--out` 的真实路径不得落在 transcripts 根目录内（整个恢复源区域禁写），也不得等于任何输入文件的真实路径。实测：隐藏目录内的 transcript 作 `--out`，inode 保护集根本没看见它，路径层直接拦住，exit 2、文件完好。
   114	
   115	另修：QA DB 的验证 fd 改为**保持打开**到复核完毕（堵 ABA）；`no_token` 分支也扫描（原本完全不扫，候选进不了保护集）；证据包每轮重生成（round-6 指出我的 self-attest 停留在 round-4 的旧 SHA，属实）；台账新增冲突原因自描述。
   116	
   117	round-6 整改后第六次全量重跑：**92 条、4/88/0/0、89/2/1、6/29、shasum 不变——六轮整改数字全程未变**。
   118	
   119	## 📄 交付物清单（全部新增，零业务代码改动）
   120	

exec
/bin/zsh -lc "git rev-parse 5b371253:backend/scripts/census_dead_letter_episodes.py HEAD:backend/scripts/census_dead_letter_episodes.py 5b371253:'_bmad-output/审查/G4-9-evidence/grep-selfattest.txt' HEAD:'_bmad-output/审查/G4-9-evidence/grep-selfattest.txt' 5b371253:'_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' HEAD:'_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
3ea39acbdb8fedc08e0576f4dcf6b2ef4cf164eb
3ea39acbdb8fedc08e0576f4dcf6b2ef4cf164eb
7007e4cf371842273fe524677a2f54fc2a690b22
7007e4cf371842273fe524677a2f54fc2a690b22
5e4adfceacb53b1f766ace11cbcc5932fc2e6d71
5e4adfceacb53b1f766ace11cbcc5932fc2e6d71

exec
/bin/zsh -lc 'git merge-base --is-ancestor 4c125f19 5b371253' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead

exec
/bin/zsh -lc 'git status --porcelain=v1' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
?? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round7.md"

**Planning verification of official web docs**
web search: 
web search: 
2026-08-28T13:01:43.827605Z ERROR codex_models_manager::manager: failed to refresh available models: timeout waiting for child process to exit
2026-08-28T13:04:48.831060Z ERROR codex_models_manager::manager: failed to refresh available models: timeout waiting for child process to exit
ERROR: Reconnecting... 2/5
ERROR: Reconnecting... 3/5
ERROR: Reconnecting... 4/5
ERROR: Reconnecting... 5/5
**Clarifying search tool limitations**
**Documenting snapshot and classification details**
**Identifying new blocker cases**
**Identifying URI carryover blocker**
**Designing path symlink matrix**
**Assessing new path containment blockers**
**Summarizing rejection with closure recommendations**
**Planning evaluation of closure hypothesis**
codex
交叉核验已收束：冻结台账与 receipt 链是可采信的，但生成器安全闭包仍失败。尤其当前卷上已只读确认 `/Users/.../projects` 与 `/users/.../projects` 是同一目录，而 `realpath` 字符串不同，形成无需竞态的根内写入绕过；QA 的 rename 型 ABA 与 round-6 未修的 URI 问题也仍成立。正在整理最终逐项矩阵与验收边界。
mcp: sequential-thinking/sequentialthinking started
mcp: sequential-thinking/sequentialthinking (completed)
mcp: sequential-thinking/sequentialthinking started
mcp: sequential-thinking/sequentialthinking (completed)
**Completing update plan**
全部只读证据轨与交叉核验完成，结论已收束。
  ✓ 核对 checkout、commit/receipt 链及 round-6 基线
  ✓ 静态审阅五项修复及生产入口控制流
  ✓ 设计并只读验证路径、inode、TOCTOU 新反例
  ✓ 从原始工件独立复算台账与证据包指标
  ✓ 交叉核验后给出逐项 CLOSED/NOT-CLOSED 与总裁定
**Drafting final Chinese citations**
**Including relevant rollout IDs in citations**
**Defining base file paths**
**Summarizing symlink path cases**
**Planning SQLite URI handling**
**Identifying ledger table blockers and risks**
**Confirming macOS case-insensitive file handling**
**Verifying Path.resolve case behavior on macOS**
**Analyzing path guard limitation with hardlinks**
**Confirming output truncation behavior**
**Planning detailed metric reporting format**
**Confirming memory skill as guidance**
codex
总裁定：**仍阻断，CARD-G4-9 round-7 不可验收。**

冻结台账数字可采信，但生成器的“纯只读、恢复源区域零写入”安全闭包仍失败。按开发方 5 个编号计：**2 CLOSED / 2 NOT-CLOSED / 1 PARTIAL**；拆成 6 个原子声明则是 **3 CLOSED / 3 NOT-CLOSED**。

审阅锚点：`HEAD=4ba4f847fa3ad83d136d3a40fcc5448b25c54ba5`，直接父提交为 `5b3712537ef5be91eda18e2a9eaf2fd3d5e03ef5`。

## 逐项裁定

| 项目 | 裁定 | 结果 |
|---|---|---|
| 1. transcripts 路径层防御 | **NOT-CLOSED · BLOCKER** | 一次性 `realpath` 字符串检查仍受 hardlink、大小写别名和父目录换链影响。[路径检查](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:421)；最终仍原路径 `open`/`ftruncate`，[写入入口](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:733)。 |
| 2. QA DB fd 保持及复核 | **NOT-CLOSED · BLOCKER** | 验证 fd=A 虽保持打开，SQLite 仍按 pathname 另开连接；rename 型 A→B→A 可令连接读 B，而两次复核都看到 A。[QA 打开链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:277)。 |
| 3. no_token 也遍历 | **CLOSED（狭义）** | 现在先无条件遍历、收集可见 `.jsonl`，再于 no_token 分支返回。[遍历](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:201)。但它不覆盖不可枚举 inode，因此不能补救项目 1。 |
| 4. self-attest + receipt | **CLOSED（当前仓库内）** | self-attest 内嵌脚本 SHA `533d0d4c…e3585` 与实际一致；脚本/self-attest/ledger 从 `5b371253` 到 HEAD blob 均未变。[self-attest](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:1)、[receipt](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt:12)。 |
| 5a. attribution_conflict_reason | **CLOSED** | 字段已序列化不同原因；冻结台账三条均为 `no_token`。[生成逻辑](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:616)、[台账实例](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:202)。 |
| 5b. lone-surrogate 回退 | **NOT-CLOSED · LOW** | `json.dumps(..., ensure_ascii=False)` 会正常返回含 surrogate 的 `str`；异常发生在后续 UTF-8 `write/print`，不在当前 `try` 内。[回退代码](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:725)。`--out` 分支还会先 `ftruncate`，再写出失败。 |

## 路径反例矩阵

| 反例 | 结果 |
|---|---|
| 根外稳定 symlink → 根内文件 | **CLOSED**：`realpath` 命中；final symlink 还受 `O_NOFOLLOW` 约束。 |
| 根外 hardlink → 可枚举 transcript | **CLOSED**：枚举所得 inode 会在最终 `fstat` 命中。 |
| 根外 hardlink → `0333` 隐藏目录内 transcript | **NOT-CLOSED**：hardlink 的 `realpath` 仍在根外；隐藏 inode 未被枚举，最终可被截断。 |
| transcripts 根是稳定 symlink | **CLOSED**：两侧稳定 `realpath` 指向相同真实根。 |
| transcripts 根在检查后 retarget | **NOT-CLOSED**：未持有/复核根目录 fd，检查绑定旧目标，扫描或写入可使用新目标。 |
| 相对路径与 `..` | **CLOSED**：无竞态、大小写一致时会被正规化。 |
| 检查后仅把 basename 换成 symlink | **CLOSED**：最终 `O_NOFOLLOW` 拒绝。 |
| 检查后换父目录 symlink或把 basename 换成 hardlink | **NOT-CLOSED**：`O_NOFOLLOW` 只约束最终 symlink，不约束父组件或 hardlink。 |
| 大小写别名 | **NOT-CLOSED、无需竞态**：本机只读复算确认 `/Users/Heishing/.claude/projects` 与 `/users/heishing/.claude/projects` `samefile=True`，但两者 `realpath` 字符串不同，现有 prefix guard 返回 `False`。 |

## QA DB 仍未绑定实际连接对象

确定性调度如下：

1. 验证并保持 A 的 fd；
2. rename A→stash，B→原路径；
3. `sqlite3.connect()` 打开 B；
4. B→stashB，A→原路径；
5. 路径 `stat` 与验证 fd `fstat` 均为 A，且 rename 不会令 A 的 `st_nlink` 变 0；
6. 查询实际仍来自 B。

因此二次 `fstat` 只证明“验证 fd 仍指向 A”，没有证明 SQLite connection 指向 A。

此外，round-6 已指出的 URI BLOCKER **完全未修**：[line 291](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:291)仍直接拼接 `file:{db_path}?mode=ro`。SQLite 官方规定普通文件名里的 `?/#` 必须转义，fragment 会被忽略；所以 `/x/qa#tag` 可被解析成另一文件且吞掉 `mode=ro`。[SQLite URI 规则](https://www.sqlite.org/uri.html)、[Python sqlite3 URI 行为](https://docs.python.org/3/library/sqlite3.html#how-to-work-with-sqlite-uris)。

## 台账独立复算：PASS

未 import 被审生成器，直接从 live DLQ exact bytes 重写严格 LF/UTF-8/JSON、分类、SHA/长度、分组和聚簇计算：

- SHA-256：`3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590`
- `99,915 bytes`；92 records；unparseable 0
- class：`89 / 2 / 1`，unexpected 0
- recoverability：`byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0`
- 重复簇：`6 / 29`，大小 `16,4,3,2,2,2`
- attribution conflict：3，全部 `no_token`、全部为 callout、全部因 inline SHA+长度双门通过而仍属 `byte_exact`
- 与冻结 ledger 逐条 class/inline/recoverability/reason：`0 mismatch`

汇总与冻结工件一致：[ledger:40](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:40)。

## 新发现与限制

- **BLOCKER**：当前大小写不敏感卷上的 case-only 根别名是无需竞态的实际绕过。
- **MEDIUM**：`--out` 采用原地 `ftruncate` 后写入，没有临时文件、atomic replace、`fsync` 或并发锁；崩溃、ENOSPC、surrogate 或并发运行可留下空/部分/混写台账。
- **LOW**：receipt 使用当前仓库唯一可解析的 8 位缩写，不是跨仓可独立验证的完整 40-hex OID。
- before/after shasum 与当前 bytes 一致，但静态复审不能证明两份清单真实采集时序。

本轮未创建 symlink/hardlink/竞态 fixture，未读取 transcript 正文或 Vault；只读取任务范围内 DLQ exact bytes及 transcript 元数据。工作树仍只有开始前已存在的未跟踪 round-7 文件，未触碰任何文件。`graphiti-canvas` 本环境未暴露，故本轮 Graphiti 搜索明确为不可执行；Sequential Thinking 已完成。

**验收结论：现有 92 条冻结 ledger 可以采信；CARD-G4-9 生成器与 UAT 的纯只读安全声明不可验收。**


tokens used
159,964
总裁定：**仍阻断，CARD-G4-9 round-7 不可验收。**

冻结台账数字可采信，但生成器的“纯只读、恢复源区域零写入”安全闭包仍失败。按开发方 5 个编号计：**2 CLOSED / 2 NOT-CLOSED / 1 PARTIAL**；拆成 6 个原子声明则是 **3 CLOSED / 3 NOT-CLOSED**。

审阅锚点：`HEAD=4ba4f847fa3ad83d136d3a40fcc5448b25c54ba5`，直接父提交为 `5b3712537ef5be91eda18e2a9eaf2fd3d5e03ef5`。

## 逐项裁定

| 项目 | 裁定 | 结果 |
|---|---|---|
| 1. transcripts 路径层防御 | **NOT-CLOSED · BLOCKER** | 一次性 `realpath` 字符串检查仍受 hardlink、大小写别名和父目录换链影响。[路径检查](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:421)；最终仍原路径 `open`/`ftruncate`，[写入入口](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:733)。 |
| 2. QA DB fd 保持及复核 | **NOT-CLOSED · BLOCKER** | 验证 fd=A 虽保持打开，SQLite 仍按 pathname 另开连接；rename 型 A→B→A 可令连接读 B，而两次复核都看到 A。[QA 打开链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:277)。 |
| 3. no_token 也遍历 | **CLOSED（狭义）** | 现在先无条件遍历、收集可见 `.jsonl`，再于 no_token 分支返回。[遍历](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:201)。但它不覆盖不可枚举 inode，因此不能补救项目 1。 |
| 4. self-attest + receipt | **CLOSED（当前仓库内）** | self-attest 内嵌脚本 SHA `533d0d4c…e3585` 与实际一致；脚本/self-attest/ledger 从 `5b371253` 到 HEAD blob 均未变。[self-attest](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:1)、[receipt](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt:12)。 |
| 5a. attribution_conflict_reason | **CLOSED** | 字段已序列化不同原因；冻结台账三条均为 `no_token`。[生成逻辑](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:616)、[台账实例](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:202)。 |
| 5b. lone-surrogate 回退 | **NOT-CLOSED · LOW** | `json.dumps(..., ensure_ascii=False)` 会正常返回含 surrogate 的 `str`；异常发生在后续 UTF-8 `write/print`，不在当前 `try` 内。[回退代码](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:725)。`--out` 分支还会先 `ftruncate`，再写出失败。 |

## 路径反例矩阵

| 反例 | 结果 |
|---|---|
| 根外稳定 symlink → 根内文件 | **CLOSED**：`realpath` 命中；final symlink 还受 `O_NOFOLLOW` 约束。 |
| 根外 hardlink → 可枚举 transcript | **CLOSED**：枚举所得 inode 会在最终 `fstat` 命中。 |
| 根外 hardlink → `0333` 隐藏目录内 transcript | **NOT-CLOSED**：hardlink 的 `realpath` 仍在根外；隐藏 inode 未被枚举，最终可被截断。 |
| transcripts 根是稳定 symlink | **CLOSED**：两侧稳定 `realpath` 指向相同真实根。 |
| transcripts 根在检查后 retarget | **NOT-CLOSED**：未持有/复核根目录 fd，检查绑定旧目标，扫描或写入可使用新目标。 |
| 相对路径与 `..` | **CLOSED**：无竞态、大小写一致时会被正规化。 |
| 检查后仅把 basename 换成 symlink | **CLOSED**：最终 `O_NOFOLLOW` 拒绝。 |
| 检查后换父目录 symlink或把 basename 换成 hardlink | **NOT-CLOSED**：`O_NOFOLLOW` 只约束最终 symlink，不约束父组件或 hardlink。 |
| 大小写别名 | **NOT-CLOSED、无需竞态**：本机只读复算确认 `/Users/Heishing/.claude/projects` 与 `/users/heishing/.claude/projects` `samefile=True`，但两者 `realpath` 字符串不同，现有 prefix guard 返回 `False`。 |

## QA DB 仍未绑定实际连接对象

确定性调度如下：

1. 验证并保持 A 的 fd；
2. rename A→stash，B→原路径；
3. `sqlite3.connect()` 打开 B；
4. B→stashB，A→原路径；
5. 路径 `stat` 与验证 fd `fstat` 均为 A，且 rename 不会令 A 的 `st_nlink` 变 0；
6. 查询实际仍来自 B。

因此二次 `fstat` 只证明“验证 fd 仍指向 A”，没有证明 SQLite connection 指向 A。

此外，round-6 已指出的 URI BLOCKER **完全未修**：[line 291](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:291)仍直接拼接 `file:{db_path}?mode=ro`。SQLite 官方规定普通文件名里的 `?/#` 必须转义，fragment 会被忽略；所以 `/x/qa#tag` 可被解析成另一文件且吞掉 `mode=ro`。[SQLite URI 规则](https://www.sqlite.org/uri.html)、[Python sqlite3 URI 行为](https://docs.python.org/3/library/sqlite3.html#how-to-work-with-sqlite-uris)。

## 台账独立复算：PASS

未 import 被审生成器，直接从 live DLQ exact bytes 重写严格 LF/UTF-8/JSON、分类、SHA/长度、分组和聚簇计算：

- SHA-256：`3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590`
- `99,915 bytes`；92 records；unparseable 0
- class：`89 / 2 / 1`，unexpected 0
- recoverability：`byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0`
- 重复簇：`6 / 29`，大小 `16,4,3,2,2,2`
- attribution conflict：3，全部 `no_token`、全部为 callout、全部因 inline SHA+长度双门通过而仍属 `byte_exact`
- 与冻结 ledger 逐条 class/inline/recoverability/reason：`0 mismatch`

汇总与冻结工件一致：[ledger:40](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:40)。

## 新发现与限制

- **BLOCKER**：当前大小写不敏感卷上的 case-only 根别名是无需竞态的实际绕过。
- **MEDIUM**：`--out` 采用原地 `ftruncate` 后写入，没有临时文件、atomic replace、`fsync` 或并发锁；崩溃、ENOSPC、surrogate 或并发运行可留下空/部分/混写台账。
- **LOW**：receipt 使用当前仓库唯一可解析的 8 位缩写，不是跨仓可独立验证的完整 40-hex OID。
- before/after shasum 与当前 bytes 一致，但静态复审不能证明两份清单真实采集时序。

本轮未创建 symlink/hardlink/竞态 fixture，未读取 transcript 正文或 Vault；只读取任务范围内 DLQ exact bytes及 transcript 元数据。工作树仍只有开始前已存在的未跟踪 round-7 文件，未触碰任何文件。`graphiti-canvas` 本环境未暴露，故本轮 Graphiti 搜索明确为不可执行；Sequential Thinking 已完成。

**验收结论：现有 92 条冻结 ledger 可以采信；CARD-G4-9 生成器与 UAT 的纯只读安全声明不可验收。**


