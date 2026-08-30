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
session id: 01a04881-c815-7ee3-942a-5e28699e753e
--------
user
CARD-G4-9 round-8 复审（静态审阅 + 只读复算，禁改任何文件）。你 round-7 明确裁定「现有 92 条冻结 ledger 可以采信；生成器与 UAT 的纯只读安全声明不可验收」，并列出 1 BLOCKER（大小写别名根，无需竞态）+ 4 项路径 TOCTOU（根外 hardlink 指向隐藏目录内 transcript / 根 retarget / 检查后换父目录 symlink / basename 换 hardlink）+ 1 MEDIUM（非原子写）+ 2 LOW。开发方以 commit f389980c 做了**第二次架构级修复**：
1. 写出路径彻底重构：不再截断任何既有文件。改为「同目录 O_EXCL 新建临时文件 .<name>.census-tmp-<pid> → 写 → fsync → os.replace 原子替换」。全文再无 ftruncate 调用（grep 自证）。开发方主张：O_EXCL 保证写入目标是本进程新建对象，因此把 --out 换成指向恢复源的 hardlink / 父目录 symlink / 大小写别名这一整类绕过全部失效，同时消除崩溃/ENOSPC 留部分台账。
2. containment 判定改 _path_is_within()：从目标逐级向上比较 inode 身份 (st_dev,st_ino)，完全不依赖路径字符串（承认 round-6 用 os.path.normcase 是错误——POSIX 上它是恒等函数）；--out 与输入比较改 os.path.samefile。
3. 扫描受阻（scan_errors/stat_failures 非空）时直接拒绝写出台账 exit 2，而非仅在台账标 unverifiable。
4. lone surrogate 回退移到 json.dumps 后立即 .encode('utf-8') 探测（原异常发生在后续 write，不在 try 内）。
请逐项复核是否闭合，并针对新写出路径设计反例：临时文件名可预测导致的符号链接攻击（攻击者预先创建 .<name>.census-tmp-<pid> 为 symlink）、os.replace 的目标是 symlink 或 hardlink 时的行为、tmp 与目标跨设备、目录权限、并发同 pid、以及 _path_is_within 的循环 symlink/挂载点边界。同时复核台账仍为 92 条 / class 89-2-1 / byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0 / 重复簇 6/29 / unparseable 0 / attribution_conflict 3(no_token)、mode 0600、无 tmp 残留。逐项 CLOSED/NOT-CLOSED + 总裁定 + 新发现分级；若可验收请明确说明。
**Planning audit approach with memory**
**Planning multi-agent adversarial audit**
codex
我会按只读、fail-closed 复审：先恢复 round-7 的精确证据链与审计规程，再把代码静态审阅、写出路径反例、冻结 ledger 独立复算分轨并行；不会修改、生成或清理任何工作区文件。Graphiti / Sequential Thinking 若当前会话未暴露对应 MCP，我会明确记为审计能力限制，不拿缺失工具替代证据。
**Searching MEMORY.md with exact paths**
exec
/bin/zsh -lc 'rg -n -i "CARD-G4-9|round-7|census|ledger|f389980c|card-s5" /Users/Heishing/.codex/memories/MEMORY.md' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
84:- Missing handoff is a hard wait condition, not implied approval. `ps` was sandbox-denied (`operation not permitted`); mark the census unavailable rather than successful. [Task 1]
140:- GOV-01-VERIFIED, Phase-0A, A01, A02, A03, annotation-truth-ledger-v2, AtomicAnnotation, boundary receipt, scanner, [HANDOFF:CODEX-PHASE0A-READY]
144:- “只读” means no repo/index/ref/worktree/OpenSpec writes, scanner/final census, A01/A02 instantiation, private/Vault/network/Graphiti access, or product implementation. Provide ready/blocked status, exact evidence, batch order, and Claude/Codex matrix. [Task 1]
148:- Order: `GOV-01-VERIFIED clean candidate → OpenSpec → schema/checker → A01 boundary receipt → no-cap census/A01 snapshot → A02 seed/replay → ChatGPT blind review → Codex reconciliation → user dispute/waiver → joint A01/A02 completion → A03 candidate → user exact-byte lock`. A01 cannot complete independently of A02. [Task 1]
153:- Expired `pending-user-confirmation` receipt/envelope is not authority. New exact envelope/digest/challenge is needed. The existing `scripts/bmad/scan_feedback.py` did not cover actual output; freeze a new scanner contract/no-write boundary before census. [Task 1]

**Searching filenames for rollout summaries**
exec
/bin/zsh -lc 'rg --files /Users/Heishing/.codex/memories/rollout_summaries | rg -i "card|census|g4|round" | head -80' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
**Searching MEMORY.md for skill path**
exec
/bin/zsh -lc 'rg -n -i -C 4 "canvas-adversarial-audit|adversarial security review|P1-05c" /Users/Heishing/.codex/memories/MEMORY.md' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
30-
31-## Reusable knowledge
32-
33-- In this project family: frontend `frontend/obsidian-plugin/`, backend `backend/app/`, RAG `backend/lib/agentic_rag/`; default backend test is `cd backend && .venv/bin/pytest tests/ -x -q`. The represented CI run `32280954498` had 271 passed/13 skipped but Dependency Audit failed on five vulnerabilities; rulesets/required checks were still unset. Rebuild `CURRENT_TASK.md` from HEAD, Actions, and open facts. [Task 1]
34:- P1-05c evidence still found real vault-admission and LanceDB/orchestrator bypasses; a Graphiti exact-reader helper fix does not prove callers pass the correct group. SnapshotV3 still needs strict schema, bad-cache self-healing, and no ID truncation. [Task 1]
35-- Use official Codex app-server/subagents, Claude Goals/Agent SDK only in permitted phases, and a non-LLM supervisor. Third-party orchestration plugins may notify or show a read-only dashboard but must not control authorization, evidence, or merging. [Task 2]
36-- Permission stages are `ORCH-BOOTSTRAP-PREP-V1` (supervised trusted-root construction), `ORCH-SETUP-V1`, then `ORCH-RUN-V1` (up to 24h). Bootstrap request limits: 6h, 6 builder attempts, one reviewer attempt per role, two heavy tests, 1,500,000 tokens, `no_auto_resume=true`. [Task 2]
37-- Envelope binds only target path, schema hash, construction-contract hash, and `preimage=ABSENT`; the activator creates actual approval-projection SHA, then binds claim/task/result/event. Keep SETUP/RUN claims separate; owner acquires `O_NOFOLLOW|O_CLOEXEC` advisory lock before LLM launch and restart increments epoch/fencing token. Reviewers independently materialize the exact candidate bundle and bind SHA, I/O hashes, command, exit, stdout/stderr, verdict, and limits. [Task 2]
38-
--
151-## Failures and how to do differently
152-
153-- Expired `pending-user-confirmation` receipt/envelope is not authority. New exact envelope/digest/challenge is needed. The existing `scripts/bmad/scan_feedback.py` did not cover actual output; freeze a new scanner contract/no-write boundary before census. [Task 1]
154-
155:# Task Group: Canvas Learning System P1-05/P1-01/P1-08 adversarial security review
156-scope: Read-only, parallel audit of vault admission/indexing, Graphiti quarantine isolation, SnapshotV3, and recovery-anchor closure claims.
157-applies_to: cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output; reuse_rule=revalidate SHA, CI, actual call sites, and live Neo4j state in the target checkout.
158-
159:## Task 1: P1-05c/P1-01/P1-08 parallel adversarial review, closure rejected
160-
161-### rollout_summary_files
162-
163-- rollout_summaries/2026-08-17T01-56-07-ZNCd-agents_guide_and_p1_05c_adversarial_audit.md (cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output, rollout_path=/Users/Heishing/.codex/sessions/2026/08/17/rollout-2026-08-17T09-56-07-01a00d6e-ea40-70a1-a23c-d51342eeeacd.jsonl, updated_at=2026-08-19T17:56:56+00:00, thread_id=01a00d6e-ea40-70a1-a23c-d51342eeeacd, outcome=partial; final read-only verdict)
164-
165-### keywords
166-
167:- P1-05c, P1-05, P1-01, P1-08, check_vault_path, vault_index_orchestrator, LanceDB, Graphiti, DEFAULT_GROUP_ID, SnapshotV3, CURRENT_TASK.md
168-
169-## Task 2: P1-05b five-question adversarial audit, reproducible bypasses
170-
171-### rollout_summary_files
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

**Inspecting memory lines 155-188**
exec
/bin/zsh -lc "nl -ba /Users/Heishing/.codex/memories/MEMORY.md | sed -n '155,188p'; printf '\\nSKILL\\n'; wc -l /Users/Heishing/.codex/memories/skills/canvas-adversarial-audit/SKILL.md; sed -n '1,240p' /Users/Heishing/.codex/memories/skills/canvas-adversarial-audit/SKILL.md" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
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

SKILL
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

**Adding explicit skill announcement**
**Planning repository inspection steps**
codex
我正在采用记忆中的 `canvas-adversarial-audit` 规程，因为本轮正是 Canvas 的对抗性 closure audit；它要求独立证据轨、生产入口反例、`file:line` 可复现证据，以及对未验证关键面的保留。该规程只影响审阅方法，不授权任何写入。
只读 round-8 复审：先锚定 checkout/差异与生产入口，再并行审计写出安全、containment、冻结 ledger，最后由主审独立复核高风险结论并汇总 CLOSED/NOT-CLOSED。
  → 锚定 HEAD、commit f389980c、工作树状态、任务/规则与变更文件
  • 静态审阅原子写出实现并设计/验证指定反例
  • 审阅 _path_is_within 与 samefile 的 symlink/挂载边界
  • 独立只读复算冻结 ledger 的全部数量、分类、权限和残留
  • 交叉复核高风险发现并给出逐项裁定、分级和总裁定
**Planning seamless internal calls**
mcp: sequential-thinking/sequentialthinking started
mcp: sequential-thinking/sequentialthinking (completed)
**Planning streamlined command execution**
exec
/bin/zsh -lc "pwd
git rev-parse --show-toplevel
git rev-parse HEAD
git branch --show-current
git status --short
git show --stat --oneline --decorate --no-renames f389980c
rg --files -g 'AGENTS.md' -g 'CLAUDE.md' -g 'CURRENT_TASK.md' -g '*census*' -g '*ledger*' -g '*CARD-G4-9*' -g '"'!node_modules'"' -g '"'!.git'"'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
85dd1c8fd625759642fa45e483bec52e999efb0a
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
card/s5-census
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
?? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round8.md"
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
f389980c fix(census): G4-9 Codex round-7 架构级修复 — 消除截断动作 [BATCH-2026-08-28-第五批 / CARD-G4-9]
 .../G4-9-DLQ-census-2026-08-28.md"                 |   16 +
 .../G4-9-dlq-ledger-2026-08-28.json"               |    2 +-
 .../G4-9-evidence/grep-selfattest.txt"             |   92 +-
 .../codex-review-CARD-G4-9-round7.md"              | 6543 ++++++++++++++++++++
 ...75census\345\210\206\350\257\212-2026-08-28.md" |   16 +
 backend/scripts/census_dead_letter_episodes.py     |  127 +-
 6 files changed, 6703 insertions(+), 93 deletions(-)
CLAUDE.md
CURRENT_TASK.md
_decisions/CURRENT_TASK.md
canvas-vault/CLAUDE.md
_bmad-output/审查/G4-16-doc-type-census-2026-08-28.md
_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md
_bmad-output/审查/codex-review-CARD-G4-9-round7.md
_bmad-output/审查/codex-review-CARD-G4-9-round8.md
_bmad-output/审查/codex-review-CARD-G4-9-round6.md
_bmad-output/审查/codex-review-CARD-G4-9-round2.md
_bmad-output/审查/r11-evidence-2026-08-17/d2-dead-letter-census.md
_bmad-output/审查/codex-review-CARD-G4-9-round5.md
_bmad-output/审查/2026-08-19-P1-05b-Graphiti污染盘点census报告.md
_bmad-output/审查/G4-9-evidence/census-stderr.txt
_bmad-output/审查/phase0a-annotation-truth/A02-public-ledger-v2.schema.json
_bmad-output/审查/codex-review-CARD-G4-9-round3.md
_bmad-output/审查/codex-review-CARD-G4-9.md
_bmad-output/审查/codex-review-CARD-G4-9-round4.md
backend/scripts/census_graphiti_pollution.py
backend/scripts/census_dead_letter_episodes.py
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md

**Inspecting commit ancestry and logs**
exec
/bin/zsh -lc 'wc -l CLAUDE.md CURRENT_TASK.md _decisions/CURRENT_TASK.md
git log --oneline --decorate -12
git merge-base --is-ancestor f389980c HEAD; git diff --stat f389980c..HEAD
rg -n "CARD-G4-9|G4-9|dead.?letter|DLQ" CURRENT_TASK.md _decisions/CURRENT_TASK.md _bmad-output/implementation-artifacts _bmad-output/planning-artifacts 2>/dev/null' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
     135 CLAUDE.md
     294 CURRENT_TASK.md
     329 _decisions/CURRENT_TASK.md
     758 total
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
85dd1c8f (HEAD -> card/s5-census) docs(census): receipt 补 round-7 commit [BATCH-2026-08-28-第五批 / CARD-G4-9]
f389980c fix(census): G4-9 Codex round-7 架构级修复 — 消除截断动作 [BATCH-2026-08-28-第五批 / CARD-G4-9]
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
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
 .../G4-9-evidence/artifact-commit-receipt.txt"                        | 4 +++-
 1 file changed, 3 insertions(+), 1 deletion(-)
CURRENT_TASK.md:51:- ✅ **用户 8/8 全批**（R9 批注逐字）: ①P0-1 方案先行 ②E-2 快照选 **A**（只存投影安全面+秩数值，MEDIUM-2 悬案定案）③执行序改 Codex 8 步（P0 止血→数据边界→可信基线→证据修复→安全写入基建→分批落地→价值验证→缓行）④审批每轮只递 **6-8 项** ⑤A-2 扩容: mastery 提交前并入 tiktoken 断网兜底（compression.py:46 只捕 ImportError）+ nodes.py:97 timeout 200ms→按实测校准，WT 代码与 MAIN/.gitignore **分 commit** ⑥D-2 先按真实路径重数 DLQ（live=`WT/data/dead_letter_episodes.jsonl` 仅 1 条；`WT/backend/data/` 92 条为陈旧文件）⑦B-2 广度回顾先做**薄版 MVP**（只新增回顾报告文件，零改原白板/YAML，真实板试跑用户说「有帮到」再扩）⑧E-5 Dashboard webUI 入缓行区
_bmad-output/implementation-artifacts/goal-cards/2026-08-27-主goal全量分goal总账.md:34:| G4-9 | DLQ 真实挂载 census 分诊 | 4h | — | 否 | 未来铺路 |
_bmad-output/implementation-artifacts/goal-cards/2026-08-27-主goal全量分goal总账.md:65:| G4-11 | Graphiti rebuild matrix 台账 | 5h | G4-9, 5-ge-1(epic-5a,软—新类型入表) | 是 | 未来铺路 |
_bmad-output/implementation-artifacts/goal-cards/2026-08-27-主goal全量分goal总账.md:94:| G4-10 | DLQ 根因修复与 replay | 6h | G4-9, G4-6 | 是 | 未来铺路 |
_bmad-output/implementation-artifacts/goal-cards/2026-08-27-主goal全量分goal总账.md:105:| G8-3 | /lint 第二批：批注/DLQ/备份 | 5h | G8-2, EXT:G2-VaultScope（跨vault身份子检查的接入前提） | 是 | 防暗坑 |
_bmad-output/implementation-artifacts/goal-cards/2026-08-27-主goal全量分goal总账.md:134:| R-J05 | J05 Graphiti 记忆旅程验收 | 8h | R-RC, 外部:OBJ-04 outbox/DLQ/replay 机制（他切片） | 是 | 发布必需 |
_bmad-output/implementation-artifacts/goal-cards/2026-08-27-主goal全量分goal总账.md:359:#### G4-9 DLQ 真实挂载 census 分诊（4h · wave 1 · 未来铺路）
_bmad-output/implementation-artifacts/goal-cards/2026-08-27-主goal全量分goal总账.md:360:- **计划书锚点**: 计划书 :296「先按真实挂载重新 census」+ :127；实证 backend/data/dead_letter_episodes.jsonl 恰 92 行（worktree 副本，Aug 11 止）
_bmad-output/implementation-artifacts/goal-cards/2026-08-27-主goal全量分goal总账.md:361:- **做什么**: 按真实挂载（live 容器 data 目录，注意 MEMORY 记录的双树拓扑/子挂载遮蔽坑，worktree 副本不可代表现网）重新清点 DLQ；按失败类分诊（schema 错/prompt budget/凭证等）；逐类证明源文本或源指针+SHA 可恢复（DeadLetterStore 已存 episode_body_sha256 前缀）；无正文项登记为不可恢复清单。只读不重放。诚实标注：离日常价值远，属恢复能力地基。
_bmad-output/implementation-artifacts/goal-cards/2026-08-27-主goal全量分goal总账.md:365:#### G4-10 DLQ 根因修复与 replay（6h · wave 3 · 未来铺路）
_bmad-output/implementation-artifacts/goal-cards/2026-08-27-主goal全量分goal总账.md:366:- **计划书锚点**: 计划书 :296 后半 + J05 :604「provider 故障入 outbox/DLQ→replay」
_bmad-output/implementation-artifacts/goal-cards/2026-08-27-主goal全量分goal总账.md:368:- **依赖**: G4-9, G4-6 · **需勘探**: 是
_bmad-output/implementation-artifacts/goal-cards/2026-08-27-主goal全量分goal总账.md:374:- **依赖**: G4-9, 5-ge-1(epic-5a,软—新类型入表) · **需勘探**: 是
_bmad-output/implementation-artifacts/goal-cards/2026-08-27-主goal全量分goal总账.md:397:- **做什么**: 在隔离真实服务环境预演 J04（正命中/无答案/考题隔离/跨 vault 同名攻击，empty 与 degraded/unavailable 可区分）与 J05（批注/对话写入→精确/语义读→重启→provider 故障入 outbox/DLQ→replay→无重复/串 vault）；产出旅程证据草稿（非 RC 正式 manifest，RC 版归 G8/Phase 4）；缺口回填成新卡。
_bmad-output/implementation-artifacts/goal-cards/2026-08-27-主goal全量分goal总账.md:401:> 切片备注: 关键依赖与协调点：(1) epic-5a runtime 主干 5-ge-1~5 全部仍 ready-for-dev 未开工（sprint-status.yaml:611-662 实查），不在本切片内——G4-7 硬依赖 5-ge-1（C-1 契约：episode schema 归其独占，任何 G4 卡禁自造发散 payload）；G4-8/G4-11 软依赖；G4-5 落在 C-3 契约 owner（subject_config.py+group_id_compat.py 已存在）可先行，5-ge-5 facade（graphiti_relation_service.py 实查不存在）落地后消费同一 builder。(2) G4-4 与 G2 切片的 VaultScope resolver 是软依赖（先做参数强制，resolver 落地后对接）；Lance legacy 表回退属 G2 不重切。(3) G4-7 的 event ID 需与 G3 切片的 review event ledger 对齐。勘探实证（本轮亲查）：memory_service.py:593/905 group_id=None 确认在位；recall_at_5 实为 hit@5（run_memory_retrieval_regression.py:15 定义自证）；DLQ 恰 92 行但为 worktree 副本（Aug 11 止），live census 必须按真实挂载（MEMORY 双树拓扑坑）。诚实分级：G4-9/10/11（恢复/重建台账）离用户日常价值远，如实标未来铺路不砍；G4-3 是本切片唯一直接可感卡；建议生产门数字（hit@10≥95% 等）在 G4-14 只报告不宣称，转正由用户裁定。波次汇总：wave1=G4-1/2/6/9/12（第三批后即可开工，互相文件面基本不相交可并行）；wave2=G4-3/4/5/11/13；wave3=G4-7/8/10/14；wave4=G4-15 收口。总量 15 卡约 92h。
_bmad-output/implementation-artifacts/goal-cards/2026-08-27-主goal全量分goal总账.md:651:#### G8-3 /lint 第二批：批注/DLQ/备份（5h · wave 3 · 防暗坑）
_bmad-output/implementation-artifacts/goal-cards/2026-08-27-主goal全量分goal总账.md:652:- **计划书锚点**: 计划书 line 344（批注覆盖/跨vault身份/DLQ/备份可恢复子项）+ line 128（DLQ 无 replay）+ line 158（无来源结论信号）
_bmad-output/implementation-artifacts/goal-cards/2026-08-27-主goal全量分goal总账.md:653:- **做什么**: 在 G8-2 骨架上加：①批注覆盖轻量版——grep 计数 _bmad-output 验收单/审查目录中未答 User： 批注数与最老年龄（按需检索形态，不做 A01/A02 总账）；②DLQ 积压只读露出（Graphiti 死信计数，只报数不 replay）；③备份新鲜度（backups/ 与备份远端最近成功时间）；④recap 报告无来源结论的确定性检查（结论段须带 wikilink，best-effort）。跨 vault 身份检查（Neo4j 无 group_id 节点等）留接口占位，等 G2 VaultScope 落地后接入，本卡不实现。
_bmad-output/implementation-artifacts/goal-cards/2026-08-27-主goal全量分goal总账.md:655:- **完成判据方向**: 四项检查各有 fixture 反例先红后绿；对 live 只读跑一次并存档首份 lint 报告；DLQ/备份检查在服务不可用时报 degraded 而非假 ok（诚实四态）
_bmad-output/implementation-artifacts/goal-cards/2026-08-27-主goal全量分goal总账.md:804:- **计划书锚点**: L604 (J05 硬断言)、L522 (OBJ-04 episode ledger/outbox/DLQ)
_bmad-output/implementation-artifacts/goal-cards/2026-08-27-主goal全量分goal总账.md:805:- **做什么**: 黑盒 E2E：批注/对话写入→精确+语义两路读取→重启后仍可读→模拟 provider 故障使写入落 outbox/DLQ→replay 后无重复、无串 vault。底噪已清（C4 假镜像下线+诚实失败、C6 写侧保护，PARTIAL）；缺口=outbox/DLQ/replay 机制本身（OBJ-04 切片实施）及其旅程级证据。
_bmad-output/implementation-artifacts/goal-cards/2026-08-27-主goal全量分goal总账.md:806:- **依赖**: R-RC, 外部:OBJ-04 outbox/DLQ/replay 机制（他切片） · **需勘探**: 是
_bmad-output/implementation-artifacts/goal-cards/2026-08-27-主goal全量分goal总账.md:807:- **完成判据方向**: 故障注入后写入可在 DLQ 查到且 UI/日志诚实报告；replay 后按 episode id 去重断言 0 重复；跨 vault group_id 隔离查询 0 泄漏；重启前后读取一致；J05/manifest.json 归档。
_bmad-output/implementation-artifacts/goal-cards/2026-08-27-主goal全量分goal总账.md:946:| DLQ 存证基础（sha256 可重放锚点） | PARTIAL | 计划书 :296 + :127 | episode_worker.py:201-225 DeadLetterStore 已存 episode_body_sha256 供未来 replay；back |
_bmad-output/implementation-artifacts/goal-cards/2026-08-27-主goal全量分goal总账.md:985:| J05 Graphiti：假镜像下线与写侧保护 | PARTIAL | L604 (J05)、L522 (OBJ-04) | C4 假 Graphiti 镜像下线+诚实失败信号、C6 memory 写侧保护测试重写（第二批收官）。缺口：outbox/DLQ/replay 机制及重启/故 |
_bmad-output/implementation-artifacts/goal-cards/2026-08-27-主goal全量分goal总账.md:1052:- 并行机会①：G4-10(w3) 依赖全在 w1（G4-9/G4-6）→ 提前 w2，DLQ 根因修复早跑一轮为 G4-15 留缓冲
_bmad-output/implementation-artifacts/goal-cards/2026-08-27-主goal全量分goal总账.md:1061:**裁定**: 有条件通过（PASS WITH FIXES）。切分产物的实证质量总体扎实：抽查 20+ 张卡的 file:line 锚点逐条核验基本属实（install-vault.sh:16 硬编码、outbox 先例、DLQ 92 行、_card_states 单键、facade 不存在、5-ge-1 in-progress、venv 未迁移等全部命中），5 条 DONE 判定全部经得起代码级复核，与 A2 冻结 schema、C-1/C-2/C-3 契约、简化治理路线无方向性冲突，superseded 判定与三批实践证据吻合。但存在 1 处事实性假阴性（G3-1/G3-2 无视已存在的 learning_event_log 事件账，照卡开工会造出计划书明令禁止的第二套账本）和 4 组跨切片双主/多主（A07 README、J 旅程验收、14 天 dogfood、benchmark manifest），这些是并行执行前必须先裁定 owner 的合并型缺陷而非重切型缺陷；另有 2 处 ref 路径/证据位置错误与 3 处卡面判据缺口。修复上述 flag 1-5 后各 wave1 卡可直接开工。
_bmad-output/implementation-artifacts/goal-cards/2026-08-27-主goal全量分goal总账.md:1075:- 【确认|契约面无冲突】canvas_episode.py 在位且 5-ge-1 spec status=in-progress（DEBT-11 属实）；graphiti_relation_service.py 不存在（DEBT-12 属实，wave3 等 DEBT-11 顺序正确）；build_vault_group_id（subject_config.py:212）+ sanitize_group_id_for_graphiti（group_id_compat.py:64）双双在位，C-3 引用无误；G4-7 硬依赖 5-ge-1 符合 C-1 唯一 owner 规则。简化治理路线证据充分：_bmad-output/审查/ 下 codex-review-CARD-* 15+ 份、goal-cards/ 三批档案在位，各切片不切 receipt 卡与用户 2026-08-24 决策一致。G4-6 引 memory_service.py:392/_record_structured_outbox 与 :1380-1400 degraded+outbox、G4-9 引 DLQ 92 行、G3-5/G3-7 引 _card_states[concept_id]（:1017/:1989/:2025/:2092）、G5-3 引 board_manifest_service.py:10 basename 注记、G3-6b 的 why_this_board 全仓 0 命中与 rank_boards:189 —— 逐条实查全部属实。

**Inspecting git diff and verdict lines**
**Designing read-only static counterexamples**
**Preparing to browse official docs**
**Inspecting recent script changes**
exec
/bin/zsh -lc "sed -n '1,180p' CLAUDE.md
sed -n '1,100p' CURRENT_TASK.md
git diff --no-ext-diff --unified=100 f389980c"'^ f389980c -- backend/scripts/census_dead_letter_episodes.py
nl -ba backend/scripts/census_dead_letter_episodes.py | sed -n '"'1,320p'
nl -ba backend/scripts/census_dead_letter_episodes.py | sed -n '321,760p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
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
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
diff --git a/backend/scripts/census_dead_letter_episodes.py b/backend/scripts/census_dead_letter_episodes.py
index 3ea39acb..6f264b74 100644
--- a/backend/scripts/census_dead_letter_episodes.py
+++ b/backend/scripts/census_dead_letter_episodes.py
@@ -1,323 +1,356 @@
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
 
 
+def _path_is_within(target: str, root: str) -> bool:
+    """target 是否落在 root 目录内 —— 逐级向上比较 **inode 身份**。
+
+    round-7 BLOCKER 整改: 不能用路径字符串前缀判断 —— 大小写不敏感卷上
+    ``/Users/x`` 与 ``/users/x`` 的 realpath 字符串不同但 samefile=True，
+    prefix guard 会漏。本实现从 target 逐级取父目录，只要任一级与 root 同
+    (st_dev, st_ino) 即判定在其内；target 尚不存在时上溯到存在的祖先。
+    """
+    try:
+        root_st = os.stat(root)
+    except OSError:
+        return False
+    root_id = (root_st.st_dev, root_st.st_ino)
+    cur = os.path.realpath(target)
+    while True:
+        try:
+            st = os.stat(cur)
+            if (st.st_dev, st.st_ino) == root_id:
+                return True
+        except OSError:
+            pass  # 该级尚不存在（--out 待创建），继续上溯
+        parent = os.path.dirname(cur)
+        if parent == cur:
+            return False
+        cur = parent
+
+
+def _same_file(a: str, b: str) -> bool:
+    """按 inode 身份比较两个路径（不依赖字符串大小写/规范化）。"""
+    try:
+        return os.path.samefile(a, b)
+    except OSError:
+        return False
+
+
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
 
-    root_real = os.path.realpath(transcripts_dir)
-    root_prefix = root_real if root_real.endswith(os.sep) else root_real + os.sep
+    root_str = str(transcripts_dir)
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
-                real = os.path.realpath(candidate)
-                if not real.startswith(root_prefix):
-                    continue  # 目录 symlink 逃逸
+                if not _path_is_within(candidate, root_str):
+                    continue  # 目录 symlink 逃逸（inode 身份判定）
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
     # round-6 BLOCKER② 整改: 验证 fd **保持打开**直到 SQLite 连接建立并复核完毕
     # —— 原实现验证后即关闭，SQLite 按路径重开可被 A→B→A 的 ABA 骗过。
     conn = None
     try:
         st = os.fstat(fd)
         if not stat.S_ISREG(st.st_mode):
             result["verdict"] = "not_regular_file_refused"
             return result, None
         identity = (st.st_dev, st.st_ino)
 
         uri = f"file:{db_path}?mode=ro"
         conn = sqlite3.connect(uri, uri=True)
         # 连接建立后在**持有验证 fd 的同时**复核路径身份
         try:
             recheck = os.stat(db_path)
         except OSError as e:
             result["verdict"] = f"recheck_stat_failed: {e}"
             return result, identity
         if (recheck.st_dev, recheck.st_ino) != identity:
             result["verdict"] = "identity_changed_between_verify_and_open_refused"
             return result, identity
         # 再次 fstat 验证 fd：确认它仍指向同一对象且未被 unlink 替换
         st2 = os.fstat(fd)
         if (st2.st_dev, st2.st_ino) != identity or st2.st_nlink == 0:
             result["verdict"] = "verified_fd_invalidated_refused"
             return result, identity
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
@@ -327,214 +360,212 @@ def probe_qa_metrics(db_path: Path, error_types: list[str]) -> tuple[dict, tuple
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
     # round-6 BLOCKER①② 架构整改: inode 保护集依赖**枚举完整性**（不可列举的
     # 子目录、ABA 换 inode 都能让某个真实源不进集合）。故增加**不依赖枚举**的
     # 路径层防御：--out 的 realpath 不得落在 transcripts 根内、不得等于任一
     # 输入路径。路径层 + inode 层双保险，任一命中即拒绝。
     if args.out:
-        out_real = os.path.realpath(args.out)
-        tr_real = os.path.realpath(args.transcripts_dir)
-        tr_prefix = tr_real if tr_real.endswith(os.sep) else tr_real + os.sep
-        if out_real == tr_real or out_real.startswith(tr_prefix):
+        # round-7 BLOCKER 整改: 用 **inode 身份逐级比较**（_path_is_within），
+        # 不用路径字符串前缀 —— normcase 在 POSIX 上是恒等函数，大小写不敏感
+        # 卷上的别名根（/Users vs /users）realpath 字符串不同但 samefile=True。
+        if _path_is_within(args.out, args.transcripts_dir):
             print(
                 f"--out 落在 transcripts 根内（恢复源区域），无条件拒绝写出: {args.out}",
                 file=sys.stderr,
             )
             return 2
-        input_reals = {os.path.realpath(args.dlq)} | {os.path.realpath(c) for c in args.compare}
-        if args.qa_metrics_db:
-            input_reals.add(os.path.realpath(args.qa_metrics_db))
-        if out_real in input_reals:
-            print(f"--out 与输入文件路径相同（realpath 比较），拒绝写出: {args.out}", file=sys.stderr)
+        input_paths = [args.dlq, *args.compare] + ([args.qa_metrics_db] if args.qa_metrics_db else [])
+        if any(_same_file(args.out, ip) for ip in input_paths):
+            print(f"--out 与输入文件为同一对象（inode 比较），拒绝写出: {args.out}", file=sys.stderr)
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
@@ -608,174 +639,182 @@ def main(argv: list[str] | None = None) -> int:
                 "episode_body_length": rec.get("episode_body_length"),
                 "episode_body_sha256": rec.get("episode_body_sha256"),
                 "inline_state": state,
                 "sha_check": sha_check,
                 "session_token": sess["session_token"],
                 "transcript_paths": sess["transcript_paths"],
                 "transcript_match_count": sess["transcript_match_count"],
                 "attribution_conflict": sess["attribution_conflict"],
                 # round-6 LOW 整改: ledger 自描述冲突原因，G4-10 可区分
                 # 缺 token / token 冲突 / 扫描受阻 / 不可读 / 多命中
                 "attribution_conflict_reason": (
                     "no_token"
                     if sess.get("no_token")
                     else "token_conflict"
                     if sess.get("token_conflict")
                     else "scan_errors"
                     if sess.get("scan_errors")
                     else "stat_failures"
                     if sess.get("stat_failures")
                     else "unreadable_candidates"
                     if sess.get("unreadable_candidates")
                     else "ambiguous_multi_match"
                     if sess["attribution_conflict"]
                     else None
                 ),
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
+    # round-7 整改: 扫描受阻 ⇒ 保护集必然不完整（隐藏目录内的源看不见）。
+    # 仅在台账标 unverifiable 不够 —— 直接拒绝写出，避免在保护集残缺时落盘。
+    scan_blocked = [
+        (k, v.get("scan_errors") or v.get("stat_failures"))
+        for k, v in group_attribution.items()
+        if v.get("scan_errors") or v.get("stat_failures")
+    ]
+    if scan_blocked and args.out:
+        print(
+            f"transcripts 扫描受阻（{len(scan_blocked)} 组），保护集不完整，拒绝写出台账；首例: {scan_blocked[0][1]}",
+            file=sys.stderr,
+        )
+        return 2
+
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
+        out_json.encode("utf-8")  # round-7 LOW: 编码错误必须在写出前暴露
     except (UnicodeEncodeError, ValueError):
-        # round-6 LOW 整改: name/error/group_id 等字段若含 escaped lone surrogate，
-        # ensure_ascii=False 写出会抛错并拒绝整次 census。回退 ensure_ascii=True
-        # （\uXXXX 转义，ASCII 安全）并在台账中显式标注该降级。
+        # name/error/group_id 等字段若含 escaped lone surrogate，UTF-8 写出会抛错。
+        # 回退 ensure_ascii=True（\uXXXX 转义，ASCII 安全）并在台账显式标注。
         ledger["json_encoding_note"] = "ensure_ascii=True fallback: 某字段含无法 UTF-8 编码的字符（lone surrogate）"
         out_json = json.dumps(ledger, ensure_ascii=True, indent=1)
     if args.out:
-        # round-3 整改: 消除 check-then-open TOCTOU。先以 O_NOFOLLOW 打开且
-        # **不带 O_TRUNC**，对**实际 fd** fstat 校验 inode；只有校验通过才
-        # ftruncate。检查与写入作用于同一 fd，检查后被换 symlink/hardlink 无效。
+        # round-7 架构整改: 不再截断既有文件 —— 同目录 O_EXCL 新建临时文件 →
+        # 写 → fsync → os.replace 原子替换。O_EXCL 保证目标是本进程新建的对象，
+        # 因此"把 --out 换成指向恢复源的 hardlink / 父目录 symlink / 大小写别名"
+        # 这一整类绕过全部失效（脚本从不 ftruncate 任何既有 inode）；同时消除
+        # 崩溃/ENOSPC 留下部分台账的风险（round-7 MEDIUM）。
+        out_path = Path(args.out)
+        tmp_path = out_path.with_name(f".{out_path.name}.census-tmp-{os.getpid()}")
         try:
-            fd = os.open(args.out, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
+            tmp_fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
         except OSError as e:
-            print(f"--out 无法安全打开（symlink 或权限）: {args.out} ({e})", file=sys.stderr)
+            print(f"临时台账文件无法新建（O_EXCL）: {tmp_path} ({e})", file=sys.stderr)
             return 2
         try:
-            st = os.fstat(fd)
-            # round-4 MEDIUM 整改: 非常规文件（FIFO/设备/socket）拒绝
-            if not stat.S_ISREG(st.st_mode):
-                print(f"--out 不是常规文件（FIFO/设备/socket），拒绝写出: {args.out}", file=sys.stderr)
-                return 2
-            # round-5 HIGH 整改: 碰撞检查必须**先于** fchmod —— 否则 --out 指向
-            # 受保护的 0644 输入时，会先把只读输入的权限改成 0600 再拒绝。
-            if (st.st_dev, st.st_ino) in protected_ids:
-                print(
-                    f"--out 打开后经 fstat 判定与输入文件同一 inode，拒绝写出（防截断）: {args.out}",
-                    file=sys.stderr,
-                )
-                return 2
-            # 碰撞检查通过后才收紧权限（round-4 LOW: 0o600 只作用于新建）
-            if st.st_mode & 0o077:
-                os.fchmod(fd, 0o600)
-            os.ftruncate(fd, 0)
-            with os.fdopen(fd, "w", encoding="utf-8", closefd=True) as f:
-                fd = -1  # 所有权移交 fdopen
+            with os.fdopen(tmp_fd, "w", encoding="utf-8", closefd=False) as f:
                 f.write(out_json + "\n")
-        finally:
-            if fd >= 0:
-                os.close(fd)
+                f.flush()
+                os.fsync(tmp_fd)
+        except Exception as e:
+            os.close(tmp_fd)
+            os.unlink(tmp_path)
+            print(f"台账写入失败，已清理临时文件: {e}", file=sys.stderr)
+            return 2
+        os.close(tmp_fd)
+        # 原子替换。目标若是恢复源，路径层与 inode 层已在前面拒绝；此处 replace
+        # 只作用于本进程新建的 tmp，不存在"截断别人的文件"这一步。
+        os.replace(tmp_path, out_path)
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
   261	    if not uniq:
   262	        # 无 token: 未做任何归因扫描 —— 不是"确认无源"（round-5 MEDIUM 整改）
   263	        result["attribution_conflict"] = True
   264	        result["no_token"] = True
   265	        return result
   266	
   267	    longest = uniq[-1]
   268	    if any(not longest.startswith(t) for t in uniq[:-1]):
   269	        result["attribution_conflict"] = True
   270	        result["token_conflict"] = True
   271	        return result
   272	    result["session_token"] = longest
   273	
   274	    if walk_errors:
   275	        result["scan_errors"] = walk_errors[:5]
   276	        result["attribution_conflict"] = True
   277	        return result
   278	    if stat_failures:
   279	        result["stat_failures"] = stat_failures[:5]
   280	        result["attribution_conflict"] = True
   281	        return result
   282	    if unreadable:
   283	        result["unreadable_candidates"] = unreadable[:5]
   284	        result["attribution_conflict"] = True
   285	        return result
   286	
   287	    matches = sorted(set(per_token[longest]))
   288	    result["transcript_paths"] = matches
   289	    result["transcript_match_count"] = len(matches)
   290	    if len(matches) == 1:
   291	        result["transcript_exists"] = True
   292	    elif len(matches) > 1:
   293	        result["attribution_conflict"] = True  # ambiguous 多命中，拒绝采信
   294	    return result
   295	
   296	
   297	def probe_qa_metrics(db_path: Path, error_types: list[str]) -> tuple[dict, tuple[int, int] | None]:
   298	    """只读核销 qa_metrics.db（URI mode=ro，无写路径）。返回 (结果, 实际身份)。
   299	
   300	    round-5 BLOCKER②/MEDIUM 整改: 原实现按路径 stat 取身份、SQLite 稍后按路径
   301	    重新打开 —— 两者可能不是同一对象，且无 regular-file/nonblocking 门（FIFO
   302	    会阻塞）。现: fd 打开取 fstat 身份 + S_ISREG 门 → SQLite 打开 → 复核路径
   303	    身份仍等于该身份，不等即拒绝（不采信被换入的对象）。
   304	    """
   305	    result: dict = {"db_path": str(db_path), "opened_readonly": False}
   306	    if not db_path.exists():
   307	        result["verdict"] = "db_missing"
   308	        return result, None
   309	    try:
   310	        fd = os.open(db_path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
   311	    except OSError as e:
   312	        result["verdict"] = f"open_refused: {e}"
   313	        return result, None
   314	    # round-6 BLOCKER② 整改: 验证 fd **保持打开**直到 SQLite 连接建立并复核完毕
   315	    # —— 原实现验证后即关闭，SQLite 按路径重开可被 A→B→A 的 ABA 骗过。
   316	    conn = None
   317	    try:
   318	        st = os.fstat(fd)
   319	        if not stat.S_ISREG(st.st_mode):
   320	            result["verdict"] = "not_regular_file_refused"
   321	            return result, None
   322	        identity = (st.st_dev, st.st_ino)
   323	
   324	        uri = f"file:{db_path}?mode=ro"
   325	        conn = sqlite3.connect(uri, uri=True)
   326	        # 连接建立后在**持有验证 fd 的同时**复核路径身份
   327	        try:
   328	            recheck = os.stat(db_path)
   329	        except OSError as e:
   330	            result["verdict"] = f"recheck_stat_failed: {e}"
   331	            return result, identity
   332	        if (recheck.st_dev, recheck.st_ino) != identity:
   333	            result["verdict"] = "identity_changed_between_verify_and_open_refused"
   334	            return result, identity
   335	        # 再次 fstat 验证 fd：确认它仍指向同一对象且未被 unlink 替换
   336	        st2 = os.fstat(fd)
   337	        if (st2.st_dev, st2.st_ino) != identity or st2.st_nlink == 0:
   338	            result["verdict"] = "verified_fd_invalidated_refused"
   339	            return result, identity
   340	        result["opened_readonly"] = True
   341	        result["file_identity_verified"] = True
   342	        tables = [
   343	            r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
   344	        ]
   345	        result["tables"] = tables
   346	        if "qa_error_logs" in tables:
   347	            total = conn.execute("SELECT COUNT(*) FROM qa_error_logs").fetchone()[0]
   348	            result["qa_error_logs_rows"] = total
   349	            hits = {}
   350	            for et in sorted(set(error_types)):
   351	                hits[et] = conn.execute("SELECT COUNT(*) FROM qa_error_logs WHERE error_type = ?", (et,)).fetchone()[0]
   352	            result["error_type_hits"] = hits
   353	            result["verdict"] = "no_source_rows" if total == 0 else "rows_present_see_hits"
   354	        else:
   355	            result["verdict"] = "qa_error_logs_table_missing"
   356	    finally:
   357	        if conn is not None:
   358	            conn.close()
   359	        os.close(fd)
   360	    return result, identity
   361	
   362	
   363	def snapshot_file(path: Path) -> tuple[bytes, dict, tuple[int, int]]:
   364	    """一次性读全量 bytes；sha/行数/身份全部派生自**同一个 fd**。
   365	
   366	    round-4 BLOCKER② 整改: 原实现按路径 stat 采集保护身份、稍后才按路径读取，
   367	    两步之间对象可被换掉（源侧 TOCTOU）。现改为打开一次 fd → fstat 取身份 →
   368	    从该 fd 读全量，返回的 (st_dev, st_ino) 即**实际被读取对象**的身份。
   369	    """
   370	    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
   371	    try:
   372	        st = os.fstat(fd)
   373	        if not stat.S_ISREG(st.st_mode):
   374	            raise OSError(f"不是常规文件（拒绝 FIFO/设备/目录）: {path}")
   375	        identity = (st.st_dev, st.st_ino)
   376	        chunks = []
   377	        while True:
   378	            block = os.read(fd, 1 << 20)
   379	            if not block:
   380	                break
   381	            chunks.append(block)
   382	        raw = b"".join(chunks)
   383	    finally:
   384	        os.close(fd)
   385	    info = {
   386	        "path": str(path),
   387	        "exists": True,
   388	        # round-3 整改: JSONL 的行分隔符**只有** \n —— splitlines() 会把
   389	        # U+2028/U+2029/裸 CR 也当分隔符，可能把一条 JSON 记录劈成两半。
   390	        # 与 records 同口径按 \n 切分（末尾换行不算空行）。
   391	        "line_count": len(_split_jsonl_lines(raw)),
   392	        "sha256": hashlib.sha256(raw).hexdigest(),
   393	        "mtime_utc": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
   394	        "mtime_note": "mtime 取自读取用 fd 的 fstat；绑定 exact bytes 的是 sha256",
   395	    }
   396	    return raw, info, identity
   397	
   398	
   399	def describe_copy(path: Path) -> tuple[dict, tuple[int, int] | None]:
   400	    """返回 (描述, 实际读取对象身份)；身份用于并入 --out 保护集。"""
   401	    if not path.exists():
   402	        return {"path": str(path), "exists": False}, None
   403	    _, info, identity = snapshot_file(path)
   404	    return info, identity
   405	
   406	
   407	def main(argv: list[str] | None = None) -> int:
   408	    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
   409	    ap.add_argument(
   410	        "--dlq",
   411	        default="data/dead_letter_episodes.jsonl",
   412	        help="DLQ JSONL 路径（census 对 live 挂载运行时传绝对路径）",
   413	    )
   414	    ap.add_argument(
   415	        "--qa-metrics-db",
   416	        default=None,
   417	        help="qa_metrics.db 路径（省略则跳过源指针核销并如实标注 skipped）",
   418	    )
   419	    ap.add_argument(
   420	        "--transcripts-dir",
   421	        default=os.path.expanduser("~/.claude/projects"),
   422	        help="session transcript 根目录（近似恢复源指针核销；不存在则 exit 2 拒诊）",
   423	    )
   424	    ap.add_argument(
   425	        "--compare",
   426	        action="append",
   427	        default=[],
   428	        help="其它 DLQ 副本路径（可重复，产出 sha 对照表）",
   429	    )
   430	    ap.add_argument("--out", default=None, help="台账 JSON 输出路径（省略则打 stdout）")
   431	    args = ap.parse_args(argv)
   432	
   433	    dlq_path = Path(args.dlq)
   434	    if not dlq_path.exists():
   435	        print(f"DLQ 文件不存在: {dlq_path}", file=sys.stderr)
   436	        return 2
   437	
   438	    transcripts_dir = Path(args.transcripts_dir)
   439	    if not transcripts_dir.is_dir():
   440	        print(
   441	            f"transcripts 根目录不存在/不可见: {transcripts_dir} —— 拒绝在源不可见时裁定可恢复性（fail-closed）",
   442	            file=sys.stderr,
   443	        )
   444	        return 2
   445	    # round-2 HIGH-3 整改: 存在但不可读/不可遍历的根（chmod 000）此前 exit 0
   446	    # 并把全部记录假判 unrecoverable —— 同样 fail-closed 拒诊。
   447	    if not os.access(transcripts_dir, os.R_OK | os.X_OK):
   448	        print(
   449	            f"transcripts 根目录不可读/不可遍历: {transcripts_dir} —— 拒绝在源不可见时裁定可恢复性（fail-closed）",
   450	            file=sys.stderr,
   451	        )
   452	        return 2
   453	
   454	    protected_ids: set[tuple[int, int]] = set()
   455	    # round-6 BLOCKER①② 架构整改: inode 保护集依赖**枚举完整性**（不可列举的
   456	    # 子目录、ABA 换 inode 都能让某个真实源不进集合）。故增加**不依赖枚举**的
   457	    # 路径层防御：--out 的 realpath 不得落在 transcripts 根内、不得等于任一
   458	    # 输入路径。路径层 + inode 层双保险，任一命中即拒绝。
   459	    if args.out:
   460	        # round-7 BLOCKER 整改: 用 **inode 身份逐级比较**（_path_is_within），
   461	        # 不用路径字符串前缀 —— normcase 在 POSIX 上是恒等函数，大小写不敏感
   462	        # 卷上的别名根（/Users vs /users）realpath 字符串不同但 samefile=True。
   463	        if _path_is_within(args.out, args.transcripts_dir):
   464	            print(
   465	                f"--out 落在 transcripts 根内（恢复源区域），无条件拒绝写出: {args.out}",
   466	                file=sys.stderr,
   467	            )
   468	            return 2
   469	        input_paths = [args.dlq, *args.compare] + ([args.qa_metrics_db] if args.qa_metrics_db else [])
   470	        if any(_same_file(args.out, ip) for ip in input_paths):
   471	            print(f"--out 与输入文件为同一对象（inode 比较），拒绝写出: {args.out}", file=sys.stderr)
   472	            return 2
   473	
   474	    # --out 碰撞守卫（写前）。round-2 BLOCKER-1 整改: 比较**文件身份**
   475	    # (st_dev, st_ino) 而非 resolve() 字符串 —— 后者对 hardlink 与
   476	    # 大小写不敏感文件系统上的 case-only 别名均失效（Codex 实测截断输入）。
   477	    if args.out:
   478	        out_path = Path(args.out)
   479	        protected_paths = [dlq_path, *(Path(p) for p in args.compare)]
   480	        if args.qa_metrics_db:
   481	            protected_paths.append(Path(args.qa_metrics_db))
   482	        for candidate in protected_paths:
   483	            try:
   484	                cst = candidate.stat()  # 跟随 symlink: 保护的是最终目标身份
   485	                protected_ids.add((cst.st_dev, cst.st_ino))
   486	            except OSError:
   487	                # round-4 整改: stat 失败不再静默吞 —— 无法确认身份即 fail-closed
   488	                print(f"输入文件无法 stat，拒绝继续（无法建立完整保护集）: {candidate}", file=sys.stderr)
   489	                return 2
   490	        # 路径字符串比较作为第二道（输出文件尚不存在时 stat 无身份可比）
   491	        out_resolved = out_path.resolve()
   492	        if out_resolved in {p.resolve() for p in protected_paths}:
   493	            print(f"--out 与输入文件路径重合，拒绝写出（防截断）: {out_resolved}", file=sys.stderr)
   494	            return 2
   495	        if out_path.exists():
   496	            try:
   497	                out_st = out_path.stat()
   498	            except OSError as e:
   499	                print(f"--out 无法 stat，拒绝写出: {out_path} ({e})", file=sys.stderr)
   500	                return 2
   501	            if (out_st.st_dev, out_st.st_ino) in protected_ids:
   502	                print(
   503	                    f"--out 与输入文件为同一 inode（hardlink/大小写别名），拒绝写出（防截断）: {out_path}",
   504	                    file=sys.stderr,
   505	                )
   506	                return 2
   507	
   508	    # BLOCKER-2 整改: 单次读取，records 与头部描述共享同一份 exact bytes
   509	    try:
   510	        raw_bytes, dlq_info, dlq_identity = snapshot_file(dlq_path)
   511	    except OSError as e:
   512	        print(f"DLQ 无法安全读取: {dlq_path} ({e})", file=sys.stderr)
   513	        return 2
   514	    protected_ids.add(dlq_identity)  # 保护的是**实际读取对象**，非路径快照
   515	    raw_lines = _split_jsonl_lines(raw_bytes)
   516	
   517	    records: list[tuple[int, dict]] = []
   518	    unparseable: list[dict] = []
   519	    for line_no, (line, decode_err) in enumerate(raw_lines, start=1):
   520	        if decode_err is not None:
   521	            unparseable.append({"line_no": line_no, "reason": decode_err})
   522	            continue
   523	        if not line.strip():
   524	            unparseable.append({"line_no": line_no, "reason": "blank_line"})
   525	            continue
   526	        try:
   527	            rec = json.loads(line)
   528	        except json.JSONDecodeError as e:
   529	            unparseable.append({"line_no": line_no, "reason": f"json_error: {e}", "excerpt": line[:80]})
   530	            continue
   531	        # round-3 LOW 整改: 合法 JSON 但非对象（null / 数组 / 标量）此前解析成功
   532	        # 却在 rec.get() 处抛 AttributeError 炸掉全量 —— 归入 unparseable。
   533	        if not isinstance(rec, dict):
   534	            unparseable.append(
   535	                {"line_no": line_no, "reason": f"not_a_json_object: {type(rec).__name__}", "excerpt": line[:80]}
   536	            )
   537	            continue
   538	        records.append((line_no, rec))
   539	
   540	    # request_id 分组: (类型名, 值) 复合键；缺失/None → 按 line_no 单条成组
   541	    groups: dict[tuple, list[tuple[int, dict]]] = defaultdict(list)
   542	    for line_no, rec in records:
   543	        rid = rec.get("request_id")
   544	        # round-4 LOW 整改: 不可哈希的 request_id（list/dict）按 line_no 单条成组
   545	        try:
   546	            hash(rid)
   547	            hashable = True
   548	        except TypeError:
   549	            hashable = False
   550	        key = ("__missing__", line_no) if (rid is None or not hashable) else (type(rid).__name__, rid)
   551	        groups[key].append((line_no, rec))
   552	    group_attribution: dict[tuple, dict] = {}
   553	    for key, members in groups.items():
   554	        tokens: list[str] = []
   555	        for _, rec in members:
   556	            tokens.extend(session_tokens(rec.get("name", "")))
   557	        group_attribution[key] = resolve_group_attribution(tokens, transcripts_dir)
   558	
   559	    ledger_records = []
   560	    class_dist: Counter = Counter()
   561	    recover_dist: Counter = Counter()
   562	    inline_dist: Counter = Counter()
   563	    unrecoverable_keys = []
   564	    unverifiable_keys = []
   565	    attribution_conflicts = []
   566	    for line_no, rec in records:
   567	        cls = classify(rec)
   568	        state, sha_check = inline_state(rec)
   569	        rid = rec.get("request_id")
   570	        try:
   571	            hash(rid)
   572	            hashable = True
   573	        except TypeError:
   574	            hashable = False
   575	        key = ("__missing__", line_no) if (rid is None or not hashable) else (type(rid).__name__, rid)
   576	        sess = group_attribution[key]
   577	        if state == "full_verified":
   578	            recover = "byte_exact"
   579	            basis = "inline 正文全量：sha256 重算与声明一致且长度精确匹配"
   580	        elif state != "anomaly" and full_body_verified(rec):
   581	            recover = "byte_exact"
   582	            basis = "episode_body_full 在盘且 sha256+长度双门对账通过（DEAD_LETTER_STORE_FULL_BODY 生产 opt-in 字段）"
   583	        elif sess["attribution_conflict"]:
   584	            # round-5 HIGH 整改: 可见性判定**优先于** anomaly —— 源看不见时
   585	            # 无论 inline 是什么状态，都不能断言"不可恢复"。
   586	            recover = "unverifiable"
   587	            if sess.get("no_token"):
   588	                why = "记录名未携带 session token，未做任何归因扫描"
   589	            elif sess.get("token_conflict"):
   590	                why = "同组多 token 前缀冲突"
   591	            elif sess.get("scan_errors"):
   592	                why = "扫描遍历受阻（不可读子树）"
   593	            elif sess.get("stat_failures"):
   594	                why = "候选 stat 失败"
   595	            elif sess.get("unreadable_candidates"):
   596	                why = "存在不可读候选"
   597	            else:
   598	                why = "transcript 多命中 ambiguous"
   599	            extra = "；inline 亦对不上账（anomaly）" if state == "anomaly" else ""
   600	            basis = f"源可见性不足，拒绝裁定：{why}{extra}。既不宣称可恢复，也不宣称不可恢复（fail-closed）"
   601	        elif state == "anomaly":
   602	            recover = "unrecoverable"
   603	            basis = "inline 对不上账（anomaly：sha/长度与声明不符），且归因扫描完整可见但无可用源"
   604	        elif sess["transcript_exists"]:
   605	            recover = "approximate"
   606	            basis = (
   607	                f"inline 为 200 字符前缀（前缀性质依赖 to_dict()[:200] 生产不变量，sha 无法直接证明）；"
   608	                f"经 request_id 组归因到唯一在盘 transcript {sess['session_token']}"
   609	                f"（归因 ≠ 内容已验证——本工具未读 transcript 内容；G4-10 可重蒸馏/重格式化近似重建，非逐字节保证）"
   610	            )
   611	        else:
   612	            recover = "unrecoverable"
   613	            basis = "inline 截断；归因扫描完整可见（无遍历错误/无不可读候选）但未找到任何在盘上游源"
   614	        class_dist[cls] += 1
   615	        recover_dist[recover] += 1
   616	        inline_dist[state] += 1
   617	        stable_key = {
   618	            "line_no": line_no,
   619	            "sha256_prefix": str(rec.get("episode_body_sha256", ""))[:16],
   620	            "request_id": rid,
   621	        }
   622	        if recover == "unrecoverable":
   623	            unrecoverable_keys.append(stable_key)
   624	        elif recover == "unverifiable":
   625	            unverifiable_keys.append(stable_key)
   626	        if sess["attribution_conflict"]:
   627	            attribution_conflicts.append(stable_key)
   628	        ledger_records.append(
   629	            {
   630	                "stable_key": stable_key,
   631	                "name": str(rec.get("name", ""))[:80],
   632	                "group_id": rec.get("group_id"),
   633	                "source_description": rec.get("source_description"),
   634	                "error_type": rec.get("error_type"),
   635	                "error_excerpt": str(rec.get("error", ""))[:120],
   636	                "failed_at": rec.get("failed_at"),
   637	                "reference_time": rec.get("reference_time"),
   638	                "class": cls,
   639	                "episode_body_length": rec.get("episode_body_length"),
   640	                "episode_body_sha256": rec.get("episode_body_sha256"),
   641	                "inline_state": state,
   642	                "sha_check": sha_check,
   643	                "session_token": sess["session_token"],
   644	                "transcript_paths": sess["transcript_paths"],
   645	                "transcript_match_count": sess["transcript_match_count"],
   646	                "attribution_conflict": sess["attribution_conflict"],
   647	                # round-6 LOW 整改: ledger 自描述冲突原因，G4-10 可区分
   648	                # 缺 token / token 冲突 / 扫描受阻 / 不可读 / 多命中
   649	                "attribution_conflict_reason": (
   650	                    "no_token"
   651	                    if sess.get("no_token")
   652	                    else "token_conflict"
   653	                    if sess.get("token_conflict")
   654	                    else "scan_errors"
   655	                    if sess.get("scan_errors")
   656	                    else "stat_failures"
   657	                    if sess.get("stat_failures")
   658	                    else "unreadable_candidates"
   659	                    if sess.get("unreadable_candidates")
   660	                    else "ambiguous_multi_match"
   661	                    if sess["attribution_conflict"]
   662	                    else None
   663	                ),
   664	                "recoverability": recover,
   665	                "recoverability_basis": basis,
   666	            }
   667	        )
   668	
   669	    # 语义重复簇（同 name + 全文 sha + group_id）——G4-10 重放去重策略依据
   670	    cluster_map: dict[tuple, list[int]] = defaultdict(list)
   671	    for line_no, rec in records:
   672	        cluster_map[
   673	            (str(rec.get("name", "")), str(rec.get("episode_body_sha256", "")), str(rec.get("group_id")))
   674	        ].append(line_no)
   675	    duplicate_clusters = [
   676	        {"name": k[0][:80], "episode_body_sha256": k[1], "group_id": k[2], "line_nos": v, "occurrences": len(v)}
   677	        for k, v in sorted(cluster_map.items(), key=lambda kv: -len(kv[1]))
   678	        if len(v) > 1
   679	    ]
   680	
   681	    compare_infos = []
   682	    for cp in args.compare:
   683	        cinfo, cid = describe_copy(Path(cp))
   684	        compare_infos.append(cinfo)
   685	        if cid is not None:
   686	            protected_ids.add(cid)
   687	
   688	    if args.qa_metrics_db:
   689	        qa_probe, qa_identity = probe_qa_metrics(
   690	            Path(args.qa_metrics_db),
   691	            [str(r.get("error_type", "")) for _, r in records],
   692	        )
   693	        if qa_identity is not None:
   694	            protected_ids.add(qa_identity)  # 保护实际验证过的对象身份
   695	    else:
   696	        qa_probe = {"verdict": "skipped_no_db_arg"}
   697	
   698	    deviation = {
   699	        k: {"expected": EXPECTED_CLASS_DIST.get(k, 0), "actual": class_dist.get(k, 0)}
   700	        for k in sorted(set(class_dist) | set(EXPECTED_CLASS_DIST))
   701	        if EXPECTED_CLASS_DIST.get(k, 0) != class_dist.get(k, 0)
   702	    }
   703	
   704	    ledger = {
   705	        "card": "CARD-G4-9",
   706	        "generated_at": datetime.now(timezone.utc).isoformat(),
   707	        "privacy": "private-only: transcript_paths 含本机用户名与 session UUID，禁止外发/公网发布",
   708	        "stable_key_semantics": (
   709	            "冻结快照（dlq_file.sha256）内的 occurrence key；line_no 在快照内唯一，"
   710	            "sha256_prefix/request_id 为冗余对账维度——非跨文件重排或语义幂等键"
   711	        ),
   712	        "dlq_file": dlq_info,
   713	        "compare_copies": compare_infos,
   714	        "total_lines": len(raw_lines),
   715	        "total_records": len(records),
   716	        "unparseable_lines": unparseable,
   717	        # round-2 LOW 整改: 固定 schema 补零，消费者无需自行补齐缺席键
   718	        "class_distribution": {
   719	            k: class_dist.get(k, 0) for k in ["budget_400", "schema_entity_type", "group_id_format", "unexpected"]
   720	        },
   721	        "expected_class_distribution": EXPECTED_CLASS_DIST,
   722	        "class_deviation": deviation,
   723	        "recoverability_distribution": {
   724	            k: recover_dist.get(k, 0) for k in ["byte_exact", "approximate", "unverifiable", "unrecoverable"]
   725	        },
   726	        "inline_state_distribution": {
   727	            k: inline_dist.get(k, 0) for k in ["full_verified", "truncated_prefix", "anomaly"]
   728	        },
   729	        "unrecoverable_list": unrecoverable_keys,
   730	        "unverifiable_list": unverifiable_keys,
   731	        "attribution_conflicts": attribution_conflicts,
   732	        "duplicate_clusters": duplicate_clusters,
   733	        "qa_metrics_probe": qa_probe,
   734	        "records": ledger_records,
   735	    }
   736	
   737	    # round-3 BLOCKER-1 绕过① 整改: 归因到的 transcript 是恢复源，
   738	    # --out 指向它同样会截断。写出前并入保护集（此时归因已完成）。
   739	    # round-7 整改: 扫描受阻 ⇒ 保护集必然不完整（隐藏目录内的源看不见）。
   740	    # 仅在台账标 unverifiable 不够 —— 直接拒绝写出，避免在保护集残缺时落盘。
   741	    scan_blocked = [
   742	        (k, v.get("scan_errors") or v.get("stat_failures"))
   743	        for k, v in group_attribution.items()
   744	        if v.get("scan_errors") or v.get("stat_failures")
   745	    ]
   746	    if scan_blocked and args.out:
   747	        print(
   748	            f"transcripts 扫描受阻（{len(scan_blocked)} 组），保护集不完整，拒绝写出台账；首例: {scan_blocked[0][1]}",
   749	            file=sys.stderr,
   750	        )
   751	        return 2
   752	
   753	    for sess_info in group_attribution.values():
   754	        for tpath in sess_info.get("all_candidate_paths", []):
   755	            try:
   756	                tst = os.stat(tpath)
   757	                protected_ids.add((tst.st_dev, tst.st_ino))
   758	            except OSError as e:
   759	                # round-5 整改: 候选 stat 失败不再静默吞 —— 保护集不完整即拒绝写出
   760	                print(f"候选源无法 stat，保护集不完整，拒绝写出: {tpath} ({e})", file=sys.stderr)

**Planning targeted script sections extraction**
exec
/bin/zsh -lc "wc -l backend/scripts/census_dead_letter_episodes.py
nl -ba backend/scripts/census_dead_letter_episodes.py | sed -n '1,220p'
nl -ba backend/scripts/census_dead_letter_episodes.py | sed -n '220,407p'
nl -ba backend/scripts/census_dead_letter_episodes.py | sed -n '730,900p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
     820 backend/scripts/census_dead_letter_episodes.py
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
   261	    if not uniq:
   262	        # 无 token: 未做任何归因扫描 —— 不是"确认无源"（round-5 MEDIUM 整改）
   263	        result["attribution_conflict"] = True
   264	        result["no_token"] = True
   265	        return result
   266	
   267	    longest = uniq[-1]
   268	    if any(not longest.startswith(t) for t in uniq[:-1]):
   269	        result["attribution_conflict"] = True
   270	        result["token_conflict"] = True
   271	        return result
   272	    result["session_token"] = longest
   273	
   274	    if walk_errors:
   275	        result["scan_errors"] = walk_errors[:5]
   276	        result["attribution_conflict"] = True
   277	        return result
   278	    if stat_failures:
   279	        result["stat_failures"] = stat_failures[:5]
   280	        result["attribution_conflict"] = True
   281	        return result
   282	    if unreadable:
   283	        result["unreadable_candidates"] = unreadable[:5]
   284	        result["attribution_conflict"] = True
   285	        return result
   286	
   287	    matches = sorted(set(per_token[longest]))
   288	    result["transcript_paths"] = matches
   289	    result["transcript_match_count"] = len(matches)
   290	    if len(matches) == 1:
   291	        result["transcript_exists"] = True
   292	    elif len(matches) > 1:
   293	        result["attribution_conflict"] = True  # ambiguous 多命中，拒绝采信
   294	    return result
   295	
   296	
   297	def probe_qa_metrics(db_path: Path, error_types: list[str]) -> tuple[dict, tuple[int, int] | None]:
   298	    """只读核销 qa_metrics.db（URI mode=ro，无写路径）。返回 (结果, 实际身份)。
   299	
   300	    round-5 BLOCKER②/MEDIUM 整改: 原实现按路径 stat 取身份、SQLite 稍后按路径
   301	    重新打开 —— 两者可能不是同一对象，且无 regular-file/nonblocking 门（FIFO
   302	    会阻塞）。现: fd 打开取 fstat 身份 + S_ISREG 门 → SQLite 打开 → 复核路径
   303	    身份仍等于该身份，不等即拒绝（不采信被换入的对象）。
   304	    """
   305	    result: dict = {"db_path": str(db_path), "opened_readonly": False}
   306	    if not db_path.exists():
   307	        result["verdict"] = "db_missing"
   308	        return result, None
   309	    try:
   310	        fd = os.open(db_path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
   311	    except OSError as e:
   312	        result["verdict"] = f"open_refused: {e}"
   313	        return result, None
   314	    # round-6 BLOCKER② 整改: 验证 fd **保持打开**直到 SQLite 连接建立并复核完毕
   315	    # —— 原实现验证后即关闭，SQLite 按路径重开可被 A→B→A 的 ABA 骗过。
   316	    conn = None
   317	    try:
   318	        st = os.fstat(fd)
   319	        if not stat.S_ISREG(st.st_mode):
   320	            result["verdict"] = "not_regular_file_refused"
   321	            return result, None
   322	        identity = (st.st_dev, st.st_ino)
   323	
   324	        uri = f"file:{db_path}?mode=ro"
   325	        conn = sqlite3.connect(uri, uri=True)
   326	        # 连接建立后在**持有验证 fd 的同时**复核路径身份
   327	        try:
   328	            recheck = os.stat(db_path)
   329	        except OSError as e:
   330	            result["verdict"] = f"recheck_stat_failed: {e}"
   331	            return result, identity
   332	        if (recheck.st_dev, recheck.st_ino) != identity:
   333	            result["verdict"] = "identity_changed_between_verify_and_open_refused"
   334	            return result, identity
   335	        # 再次 fstat 验证 fd：确认它仍指向同一对象且未被 unlink 替换
   336	        st2 = os.fstat(fd)
   337	        if (st2.st_dev, st2.st_ino) != identity or st2.st_nlink == 0:
   338	            result["verdict"] = "verified_fd_invalidated_refused"
   339	            return result, identity
   340	        result["opened_readonly"] = True
   341	        result["file_identity_verified"] = True
   342	        tables = [
   343	            r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
   344	        ]
   345	        result["tables"] = tables
   346	        if "qa_error_logs" in tables:
   347	            total = conn.execute("SELECT COUNT(*) FROM qa_error_logs").fetchone()[0]
   348	            result["qa_error_logs_rows"] = total
   349	            hits = {}
   350	            for et in sorted(set(error_types)):
   351	                hits[et] = conn.execute("SELECT COUNT(*) FROM qa_error_logs WHERE error_type = ?", (et,)).fetchone()[0]
   352	            result["error_type_hits"] = hits
   353	            result["verdict"] = "no_source_rows" if total == 0 else "rows_present_see_hits"
   354	        else:
   355	            result["verdict"] = "qa_error_logs_table_missing"
   356	    finally:
   357	        if conn is not None:
   358	            conn.close()
   359	        os.close(fd)
   360	    return result, identity
   361	
   362	
   363	def snapshot_file(path: Path) -> tuple[bytes, dict, tuple[int, int]]:
   364	    """一次性读全量 bytes；sha/行数/身份全部派生自**同一个 fd**。
   365	
   366	    round-4 BLOCKER② 整改: 原实现按路径 stat 采集保护身份、稍后才按路径读取，
   367	    两步之间对象可被换掉（源侧 TOCTOU）。现改为打开一次 fd → fstat 取身份 →
   368	    从该 fd 读全量，返回的 (st_dev, st_ino) 即**实际被读取对象**的身份。
   369	    """
   370	    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
   371	    try:
   372	        st = os.fstat(fd)
   373	        if not stat.S_ISREG(st.st_mode):
   374	            raise OSError(f"不是常规文件（拒绝 FIFO/设备/目录）: {path}")
   375	        identity = (st.st_dev, st.st_ino)
   376	        chunks = []
   377	        while True:
   378	            block = os.read(fd, 1 << 20)
   379	            if not block:
   380	                break
   381	            chunks.append(block)
   382	        raw = b"".join(chunks)
   383	    finally:
   384	        os.close(fd)
   385	    info = {
   386	        "path": str(path),
   387	        "exists": True,
   388	        # round-3 整改: JSONL 的行分隔符**只有** \n —— splitlines() 会把
   389	        # U+2028/U+2029/裸 CR 也当分隔符，可能把一条 JSON 记录劈成两半。
   390	        # 与 records 同口径按 \n 切分（末尾换行不算空行）。
   391	        "line_count": len(_split_jsonl_lines(raw)),
   392	        "sha256": hashlib.sha256(raw).hexdigest(),
   393	        "mtime_utc": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
   394	        "mtime_note": "mtime 取自读取用 fd 的 fstat；绑定 exact bytes 的是 sha256",
   395	    }
   396	    return raw, info, identity
   397	
   398	
   399	def describe_copy(path: Path) -> tuple[dict, tuple[int, int] | None]:
   400	    """返回 (描述, 实际读取对象身份)；身份用于并入 --out 保护集。"""
   401	    if not path.exists():
   402	        return {"path": str(path), "exists": False}, None
   403	    _, info, identity = snapshot_file(path)
   404	    return info, identity
   405	
   406	
   407	def main(argv: list[str] | None = None) -> int:
   730	        "unverifiable_list": unverifiable_keys,
   731	        "attribution_conflicts": attribution_conflicts,
   732	        "duplicate_clusters": duplicate_clusters,
   733	        "qa_metrics_probe": qa_probe,
   734	        "records": ledger_records,
   735	    }
   736	
   737	    # round-3 BLOCKER-1 绕过① 整改: 归因到的 transcript 是恢复源，
   738	    # --out 指向它同样会截断。写出前并入保护集（此时归因已完成）。
   739	    # round-7 整改: 扫描受阻 ⇒ 保护集必然不完整（隐藏目录内的源看不见）。
   740	    # 仅在台账标 unverifiable 不够 —— 直接拒绝写出，避免在保护集残缺时落盘。
   741	    scan_blocked = [
   742	        (k, v.get("scan_errors") or v.get("stat_failures"))
   743	        for k, v in group_attribution.items()
   744	        if v.get("scan_errors") or v.get("stat_failures")
   745	    ]
   746	    if scan_blocked and args.out:
   747	        print(
   748	            f"transcripts 扫描受阻（{len(scan_blocked)} 组），保护集不完整，拒绝写出台账；首例: {scan_blocked[0][1]}",
   749	            file=sys.stderr,
   750	        )
   751	        return 2
   752	
   753	    for sess_info in group_attribution.values():
   754	        for tpath in sess_info.get("all_candidate_paths", []):
   755	            try:
   756	                tst = os.stat(tpath)
   757	                protected_ids.add((tst.st_dev, tst.st_ino))
   758	            except OSError as e:
   759	                # round-5 整改: 候选 stat 失败不再静默吞 —— 保护集不完整即拒绝写出
   760	                print(f"候选源无法 stat，保护集不完整，拒绝写出: {tpath} ({e})", file=sys.stderr)
   761	                return 2
   762	    for rec_out in ledger_records:
   763	        for tpath in rec_out.get("transcript_paths", []):
   764	            try:
   765	                tst = os.stat(tpath)
   766	                protected_ids.add((tst.st_dev, tst.st_ino))
   767	            except OSError:
   768	                continue
   769	
   770	    try:
   771	        out_json = json.dumps(ledger, ensure_ascii=False, indent=1)
   772	        out_json.encode("utf-8")  # round-7 LOW: 编码错误必须在写出前暴露
   773	    except (UnicodeEncodeError, ValueError):
   774	        # name/error/group_id 等字段若含 escaped lone surrogate，UTF-8 写出会抛错。
   775	        # 回退 ensure_ascii=True（\uXXXX 转义，ASCII 安全）并在台账显式标注。
   776	        ledger["json_encoding_note"] = "ensure_ascii=True fallback: 某字段含无法 UTF-8 编码的字符（lone surrogate）"
   777	        out_json = json.dumps(ledger, ensure_ascii=True, indent=1)
   778	    if args.out:
   779	        # round-7 架构整改: 不再截断既有文件 —— 同目录 O_EXCL 新建临时文件 →
   780	        # 写 → fsync → os.replace 原子替换。O_EXCL 保证目标是本进程新建的对象，
   781	        # 因此"把 --out 换成指向恢复源的 hardlink / 父目录 symlink / 大小写别名"
   782	        # 这一整类绕过全部失效（脚本从不 ftruncate 任何既有 inode）；同时消除
   783	        # 崩溃/ENOSPC 留下部分台账的风险（round-7 MEDIUM）。
   784	        out_path = Path(args.out)
   785	        tmp_path = out_path.with_name(f".{out_path.name}.census-tmp-{os.getpid()}")
   786	        try:
   787	            tmp_fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
   788	        except OSError as e:
   789	            print(f"临时台账文件无法新建（O_EXCL）: {tmp_path} ({e})", file=sys.stderr)
   790	            return 2
   791	        try:
   792	            with os.fdopen(tmp_fd, "w", encoding="utf-8", closefd=False) as f:
   793	                f.write(out_json + "\n")
   794	                f.flush()
   795	                os.fsync(tmp_fd)
   796	        except Exception as e:
   797	            os.close(tmp_fd)
   798	            os.unlink(tmp_path)
   799	            print(f"台账写入失败，已清理临时文件: {e}", file=sys.stderr)
   800	            return 2
   801	        os.close(tmp_fd)
   802	        # 原子替换。目标若是恢复源，路径层与 inode 层已在前面拒绝；此处 replace
   803	        # 只作用于本进程新建的 tmp，不存在"截断别人的文件"这一步。
   804	        os.replace(tmp_path, out_path)
   805	        print(f"台账已写入: {args.out}")
   806	    else:
   807	        print(out_json)
   808	
   809	    print(
   810	        f"census: {len(records)} 条 (+{len(unparseable)} unparseable) | class={dict(class_dist)} | "
   811	        f"recoverability={dict(recover_dist)} | 归因冲突={len(attribution_conflicts)} | "
   812	        f"重复簇={len(duplicate_clusters)} | 偏差={deviation or '无'} | "
   813	        f"qa_metrics 核销={qa_probe.get('verdict')}",
   814	        file=sys.stderr,
   815	    )
   816	    return 0
   817	
   818	
   819	if __name__ == "__main__":
   820	    sys.exit(main())

**Identifying os.replace error handling gaps**
**Exposing os.replace hardlink race condition**
**Revealing os.replace symlink swap risk**
**Assessing os.replace symlink and hardlink risks**
**Identifying race condition in os.replace overwrite**
**Confirming attack requires directory write permission**
**Analyzing symlink retargeting vulnerability**
**Examining os.replace effects on symlinks and hardlinks**
**Evaluating cross-device rename and mount effects**
**Assessing file replace and permission handling**
**Analyzing temp file races and concurrency issues**
**Verifying symlink loop detection within root**
**Verifying root symlink and mount point logic**
**Analyzing bind mount alias effects on root containment**
**Evaluating inode and device ID behavior on bind mounts**
**Assessing inode protection during output writes**
**Verifying final protected_ids usage before writing**
exec
/bin/zsh -lc "rg -n \"protected_ids|tmp_path|os\\.replace|ftruncate|open\\(\" backend/scripts/census_dead_letter_episodes.py
git diff --no-ext-diff --unified=30 f389980c"'^ f389980c -- backend/scripts/census_dead_letter_episodes.py' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
310:        fd = os.open(db_path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
370:    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
454:    protected_ids: set[tuple[int, int]] = set()
485:                protected_ids.add((cst.st_dev, cst.st_ino))
501:            if (out_st.st_dev, out_st.st_ino) in protected_ids:
514:    protected_ids.add(dlq_identity)  # 保护的是**实际读取对象**，非路径快照
686:            protected_ids.add(cid)
694:            protected_ids.add(qa_identity)  # 保护实际验证过的对象身份
757:                protected_ids.add((tst.st_dev, tst.st_ino))
766:                protected_ids.add((tst.st_dev, tst.st_ino))
780:        # 写 → fsync → os.replace 原子替换。O_EXCL 保证目标是本进程新建的对象，
782:        # 这一整类绕过全部失效（脚本从不 ftruncate 任何既有 inode）；同时消除
785:        tmp_path = out_path.with_name(f".{out_path.name}.census-tmp-{os.getpid()}")
787:            tmp_fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
789:            print(f"临时台账文件无法新建（O_EXCL）: {tmp_path} ({e})", file=sys.stderr)
792:            with os.fdopen(tmp_fd, "w", encoding="utf-8", closefd=False) as f:
798:            os.unlink(tmp_path)
804:        os.replace(tmp_path, out_path)
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
diff --git a/backend/scripts/census_dead_letter_episodes.py b/backend/scripts/census_dead_letter_episodes.py
index 3ea39acb..6f264b74 100644
--- a/backend/scripts/census_dead_letter_episodes.py
+++ b/backend/scripts/census_dead_letter_episodes.py
@@ -47,60 +47,95 @@ BATCH-2026-08-28-第五批 / CARD-G4-9（G4-10 replay 的交接台账生成器
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
 
 
+def _path_is_within(target: str, root: str) -> bool:
+    """target 是否落在 root 目录内 —— 逐级向上比较 **inode 身份**。
+
+    round-7 BLOCKER 整改: 不能用路径字符串前缀判断 —— 大小写不敏感卷上
+    ``/Users/x`` 与 ``/users/x`` 的 realpath 字符串不同但 samefile=True，
+    prefix guard 会漏。本实现从 target 逐级取父目录，只要任一级与 root 同
+    (st_dev, st_ino) 即判定在其内；target 尚不存在时上溯到存在的祖先。
+    """
+    try:
+        root_st = os.stat(root)
+    except OSError:
+        return False
+    root_id = (root_st.st_dev, root_st.st_ino)
+    cur = os.path.realpath(target)
+    while True:
+        try:
+            st = os.stat(cur)
+            if (st.st_dev, st.st_ino) == root_id:
+                return True
+        except OSError:
+            pass  # 该级尚不存在（--out 待创建），继续上溯
+        parent = os.path.dirname(cur)
+        if parent == cur:
+            return False
+        cur = parent
+
+
+def _same_file(a: str, b: str) -> bool:
+    """按 inode 身份比较两个路径（不依赖字符串大小写/规范化）。"""
+    try:
+        return os.path.samefile(a, b)
+    except OSError:
+        return False
+
+
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
@@ -159,95 +194,93 @@ def session_tokens(name: object) -> list[str]:
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
 
-    root_real = os.path.realpath(transcripts_dir)
-    root_prefix = root_real if root_real.endswith(os.sep) else root_real + os.sep
+    root_str = str(transcripts_dir)
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
-                real = os.path.realpath(candidate)
-                if not real.startswith(root_prefix):
-                    continue  # 目录 symlink 逃逸
+                if not _path_is_within(candidate, root_str):
+                    continue  # 目录 symlink 逃逸（inode 身份判定）
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
 
@@ -397,74 +430,72 @@ def main(argv: list[str] | None = None) -> int:
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
-        out_real = os.path.realpath(args.out)
-        tr_real = os.path.realpath(args.transcripts_dir)
-        tr_prefix = tr_real if tr_real.endswith(os.sep) else tr_real + os.sep
-        if out_real == tr_real or out_real.startswith(tr_prefix):
+        # round-7 BLOCKER 整改: 用 **inode 身份逐级比较**（_path_is_within），
+        # 不用路径字符串前缀 —— normcase 在 POSIX 上是恒等函数，大小写不敏感
+        # 卷上的别名根（/Users vs /users）realpath 字符串不同但 samefile=True。
+        if _path_is_within(args.out, args.transcripts_dir):
             print(
                 f"--out 落在 transcripts 根内（恢复源区域），无条件拒绝写出: {args.out}",
                 file=sys.stderr,
             )
             return 2
-        input_reals = {os.path.realpath(args.dlq)} | {os.path.realpath(c) for c in args.compare}
-        if args.qa_metrics_db:
-            input_reals.add(os.path.realpath(args.qa_metrics_db))
-        if out_real in input_reals:
-            print(f"--out 与输入文件路径相同（realpath 比较），拒绝写出: {args.out}", file=sys.stderr)
+        input_paths = [args.dlq, *args.compare] + ([args.qa_metrics_db] if args.qa_metrics_db else [])
+        if any(_same_file(args.out, ip) for ip in input_paths):
+            print(f"--out 与输入文件为同一对象（inode 比较），拒绝写出: {args.out}", file=sys.stderr)
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
@@ -678,104 +709,112 @@ def main(argv: list[str] | None = None) -> int:
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
+    # round-7 整改: 扫描受阻 ⇒ 保护集必然不完整（隐藏目录内的源看不见）。
+    # 仅在台账标 unverifiable 不够 —— 直接拒绝写出，避免在保护集残缺时落盘。
+    scan_blocked = [
+        (k, v.get("scan_errors") or v.get("stat_failures"))
+        for k, v in group_attribution.items()
+        if v.get("scan_errors") or v.get("stat_failures")
+    ]
+    if scan_blocked and args.out:
+        print(
+            f"transcripts 扫描受阻（{len(scan_blocked)} 组），保护集不完整，拒绝写出台账；首例: {scan_blocked[0][1]}",
+            file=sys.stderr,
+        )
+        return 2
+
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
+        out_json.encode("utf-8")  # round-7 LOW: 编码错误必须在写出前暴露
     except (UnicodeEncodeError, ValueError):
-        # round-6 LOW 整改: name/error/group_id 等字段若含 escaped lone surrogate，
-        # ensure_ascii=False 写出会抛错并拒绝整次 census。回退 ensure_ascii=True
-        # （\uXXXX 转义，ASCII 安全）并在台账中显式标注该降级。
+        # name/error/group_id 等字段若含 escaped lone surrogate，UTF-8 写出会抛错。
+        # 回退 ensure_ascii=True（\uXXXX 转义，ASCII 安全）并在台账显式标注。
         ledger["json_encoding_note"] = "ensure_ascii=True fallback: 某字段含无法 UTF-8 编码的字符（lone surrogate）"
         out_json = json.dumps(ledger, ensure_ascii=True, indent=1)
     if args.out:
-        # round-3 整改: 消除 check-then-open TOCTOU。先以 O_NOFOLLOW 打开且
-        # **不带 O_TRUNC**，对**实际 fd** fstat 校验 inode；只有校验通过才
-        # ftruncate。检查与写入作用于同一 fd，检查后被换 symlink/hardlink 无效。
+        # round-7 架构整改: 不再截断既有文件 —— 同目录 O_EXCL 新建临时文件 →
+        # 写 → fsync → os.replace 原子替换。O_EXCL 保证目标是本进程新建的对象，
+        # 因此"把 --out 换成指向恢复源的 hardlink / 父目录 symlink / 大小写别名"
+        # 这一整类绕过全部失效（脚本从不 ftruncate 任何既有 inode）；同时消除
+        # 崩溃/ENOSPC 留下部分台账的风险（round-7 MEDIUM）。
+        out_path = Path(args.out)
+        tmp_path = out_path.with_name(f".{out_path.name}.census-tmp-{os.getpid()}")
         try:
-            fd = os.open(args.out, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
+            tmp_fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
         except OSError as e:
-            print(f"--out 无法安全打开（symlink 或权限）: {args.out} ({e})", file=sys.stderr)
+            print(f"临时台账文件无法新建（O_EXCL）: {tmp_path} ({e})", file=sys.stderr)
             return 2
         try:
-            st = os.fstat(fd)
-            # round-4 MEDIUM 整改: 非常规文件（FIFO/设备/socket）拒绝
-            if not stat.S_ISREG(st.st_mode):
-                print(f"--out 不是常规文件（FIFO/设备/socket），拒绝写出: {args.out}", file=sys.stderr)
-                return 2
-            # round-5 HIGH 整改: 碰撞检查必须**先于** fchmod —— 否则 --out 指向
-            # 受保护的 0644 输入时，会先把只读输入的权限改成 0600 再拒绝。
-            if (st.st_dev, st.st_ino) in protected_ids:
-                print(
-                    f"--out 打开后经 fstat 判定与输入文件同一 inode，拒绝写出（防截断）: {args.out}",
-                    file=sys.stderr,
-                )
-                return 2
-            # 碰撞检查通过后才收紧权限（round-4 LOW: 0o600 只作用于新建）
-            if st.st_mode & 0o077:
-                os.fchmod(fd, 0o600)
-            os.ftruncate(fd, 0)
-            with os.fdopen(fd, "w", encoding="utf-8", closefd=True) as f:
-                fd = -1  # 所有权移交 fdopen
+            with os.fdopen(tmp_fd, "w", encoding="utf-8", closefd=False) as f:
                 f.write(out_json + "\n")
-        finally:
-            if fd >= 0:
-                os.close(fd)
+                f.flush()
+                os.fsync(tmp_fd)
+        except Exception as e:
+            os.close(tmp_fd)
+            os.unlink(tmp_path)
+            print(f"台账写入失败，已清理临时文件: {e}", file=sys.stderr)
+            return 2
+        os.close(tmp_fd)
+        # 原子替换。目标若是恢复源，路径层与 inode 层已在前面拒绝；此处 replace
+        # 只作用于本进程新建的 tmp，不存在"截断别人的文件"这一步。
+        os.replace(tmp_path, out_path)
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

**Assessing impact of protected_ids removal**
exec
/bin/zsh -lc 'rg -n "BLOCKER|TOCTOU|MEDIUM|LOW|总裁定|总判|大小写|hardlink|symlink|retarget|ftruncate|92|冻结 ledger|可采信|不可验收|UAT|生成器" _bmad-output/审查/codex-review-CARD-G4-9-round7.md | head -260' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
14:CARD-G4-9 round-7 复审（静态审阅 + 只读复算，禁改任何文件）。你 round-6 裁定 6/9 CLOSED，两项 BLOCKER 揭示了根因：--out 保护集依赖枚举完整性（0333 不可列举目录内的 transcript、QA DB inode ABA 都能挫败它）。开发方接受该判断，做了**架构级修复**并以 commit 5b371253 + 后续 receipt commit 提交：
20:请逐项复核是否闭合，并针对路径层防御设计新反例（如 --out 位于 transcripts 根外但通过 symlink/hardlink 指入根内的文件、transcripts 根本身是 symlink、相对路径与 .. 组合、TOCTOU 把 --out 在检查后换成指入根内的链接）。同时复核台账仍为 92 条 / class 89-2-1 / byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0 / 重复簇 6/29 / unparseable 0 / attribution_conflict 3(no_token)。逐项 CLOSED/NOT-CLOSED + 总裁定 + 新发现分级；若可验收请明确说明。
25:我会按“只读、fail-closed、生产入口优先”复审：先核对当前 checkout/commit 链与 round-6 基线，再分三条并行轨复算代码闭合、证据/receipt、以及 92 条台账与新反例；不会运行会写文件或数据库的命令。Graphiti/Sequential Thinking 若当前环境未暴露，我会在结论里明确记为工具限制。
41:  • 设计并只读验证路径、inode、TOCTOU 新反例
43:  • 交叉核验后给出逐项 CLOSED/NOT-CLOSED 与总裁定
59:92-## Task 1: GOV01 A4 repair/micro chain audit, structurally verified but broader readiness partial
72:106-- rollout_summaries/2026-08-23T10-38-57-0pt3-gov01_cache_prep_r2_read_only_exact_object_audit.md (cwd=/private/tmp/cls-gov01-a4-v1/planning-ro, rollout_path=/Users/Heishing/.codex/sessions/2026/08/23/rollout-2026-08-23T18-38-57-01a02e33-bb2c-7b93-85d0-3c50119edfad.jsonl, updated_at=2026-08-24T11:49:59+00:00, thread_id=01a02e33-bb2c-7b93-85d0-3c50119edfad, outcome=fail; 3 BLOCKER / 2 HIGH)
76:110:- CACHE-PREP-V1, ADOPT.py, live-cache, per-digest claim, restart reconciliation, same-FD readback hash, RENAME_EXCL, O_EXCL, parent fsync, TOCTOU, _cacache/index-v5
88:125:- `O_EXCL` plus `RENAME_EXCL` does not establish unique adopter or crash recovery. R2 found fixed temp `EEXIST` after pre-rename crash, nonsealed post-rename/pre-parent-fsync restart, no durable claim/reconciler, no write-side same-FD readback, and mutation-parent TOCTOU. Therefore `[ROLLUP:CACHE-PREP-V1:S3:R2-TECH] FAIL / BLOCKED`. [Task 2]
152:3. Directly exercise real entrypoints with temporary fixtures where permitted. For path admission include symlink, directory symlink, blacklisted filename in an allowed directory, case variant, and nonexistent path. Assert rejected inputs perform zero open/hash/index/write.
204:    23	- ORCH-BOOTSTRAP-PREP-V1, ORCH-SETUP-V1, ORCH-RUN-V1, non-LLM supervisor, app-server, Agent SDK, approval projection, setup-root-claim-v1, run-activation-claim-v1, O_NOFOLLOW, fencing token, no_auto_resume
218:    37	- Envelope binds only target path, schema hash, construction-contract hash, and `preimage=ABSENT`; the activator creates actual approval-projection SHA, then binds claim/task/result/event. Keep SETUP/RUN claims separate; owner acquires `O_NOFOLLOW|O_CLOEXEC` advisory lock before LLM launch and restart increments epoch/fencing token. Reviewers independently materialize the exact candidate bundle and bind SHA, I/O hashes, command, exit, stdout/stderr, verdict, and limits. [Task 2]
273:    92	## Task 1: GOV01 A4 repair/micro chain audit, structurally verified but broader readiness partial
287:   106	- rollout_summaries/2026-08-23T10-38-57-0pt3-gov01_cache_prep_r2_read_only_exact_object_audit.md (cwd=/private/tmp/cls-gov01-a4-v1/planning-ro, rollout_path=/Users/Heishing/.codex/sessions/2026/08/23/rollout-2026-08-23T18-38-57-01a02e33-bb2c-7b93-85d0-3c50119edfad.jsonl, updated_at=2026-08-24T11:49:59+00:00, thread_id=01a02e33-bb2c-7b93-85d0-3c50119edfad, outcome=fail; 3 BLOCKER / 2 HIGH)
291:   110	- CACHE-PREP-V1, ADOPT.py, live-cache, per-digest claim, restart reconciliation, same-FD readback hash, RENAME_EXCL, O_EXCL, parent fsync, TOCTOU, _cacache/index-v5
306:   125	- `O_EXCL` plus `RENAME_EXCL` does not establish unique adopter or crash recovery. R2 found fixed temp `EEXIST` after pre-rename crash, nonsealed post-rename/pre-parent-fsync restart, no durable claim/reconciler, no write-side same-FD readback, and mutation-parent TOCTOU. Therefore `[ROLLUP:CACHE-PREP-V1:S3:R2-TECH] FAIL / BLOCKED`. [Task 2]
358:   177	- P1-05b, symlink_escape, casefold, vault_backfill, lancedb_client, quarantine__p105b, search_nodes, read_node_tips, manifest-v3, NaN
373:   192	- Green tests hitting source text, helpers, fake clients, `__new__`, or monkeypatches are not closure; pivot to production entrypoints and full stdout/trace. Test `search_nodes`, `read_node_tips`, `read_node_errors`, and `read_node_edge_reasons`. [Task 1][Task 2]
467:67ccebe1 docs(census): G4-9 DLQ真实挂载census分诊 92条台账+挂载真相+三态裁定 [BATCH-2026-08-28-第五批 / CARD-G4-9]
476:fca1bdc4 test(cypher): G2-1 读写契约审计+R1-R5/W1-W5 规则+7692 真库门测试 [BATCH-2026-08-27-第四批 / CARD-G2-1]
496:./_bmad-output/审查/codex-review-CARD-G4-16-round3.md:659:A	"_bmad-output/\351\252\214\346\224\266\345\215\225/UAT-CARD-G4-9-DLQ\347\234\237\345\256\236\346\214\202\350\275\275census\345\210\206\350\257\212-2026-08-28.md"
497:./_bmad-output/审查/codex-review-CARD-G4-16-round3.md:1027:67ccebe1 docs(census): G4-9 DLQ真实挂载census分诊 92条台账+挂载真相+三态裁定 [BATCH-2026-08-28-第五批 / CARD-G4-9]
508:./_bmad-output/审查/codex-review-CARD-G4-16-round4.md:218:A	"_bmad-output/\351\252\214\346\224\266\345\215\225/UAT-CARD-G4-9-DLQ\347\234\237\345\256\236\346\214\202\350\275\275census\345\210\206\350\257\212-2026-08-28.md"
514:./_bmad-output/审查/codex-review-CARD-G4-16-round4.md:1387:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md
517:./_bmad-output/审查/codex-review-CARD-G4-16-round4.md:2686:M	"_bmad-output/\351\252\214\346\224\266\345\215\225/UAT-CARD-G4-9-DLQ\347\234\237\345\256\236\346\214\202\350\275\275census\345\210\206\350\257\212-2026-08-28.md"
520:./_bmad-output/审查/codex-review-CARD-G4-16-round4.md:3861:67ccebe1 docs(census): G4-9 DLQ真实挂载census分诊 92条台账+挂载真相+三态裁定 [BATCH-2026-08-28-第五批 / CARD-G4-9]
523:./backend/scripts/census_dead_letter_episodes.py:4:BATCH-2026-08-28-第五批 / CARD-G4-9（G4-10 replay 的交接台账生成器）。
540:./backend/scripts/census_dead_letter_episodes.py:592:            unrecoverable_keys.append(stable_key)
549:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:94:/bin/zsh -lc "rg -n -i \"CARD-G4-9|G4-9|fce0d8a2|92 条|89-2-1|4-88-0\" /Users/Heishing/.codex/memories/rollout_summaries /Users/Heishing/.codex/memories/MEMORY.md --glob '*.md' --glob '*.jsonl' || true
556:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:131:67ccebe1 docs(census): G4-9 DLQ真实挂载census分诊 92条台账+挂载真相+三态裁定 [BATCH-2026-08-28-第五批 / CARD-G4-9]
557:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:145:rg -n \"BLOCKER-1|HIGH-3|JSONL|framing|非 dict|provenance|PARTIAL|CLOSED|NOT-CLOSED|新发现|总裁定|protected_ids|O_NOFOLLOW|os\\.walk|line_count\" '_bmad-output/审查/codex-review-CARD-G4-9-round3.md' | head -n 240
562:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:156:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md
563:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:160:14:CARD-G4-9 round-3 复审（静态审阅 + 只读复算）。你 round-2 裁定 10/13 CLOSED，三项 NOT-CLOSED：BLOCKER-1（--out 守卫比 resolve 字符串，hardlink 与 case-only 别名绕过截断输入）、HIGH-1（full_body_verified 只核 sha 不核长度且排在 anomaly 分支前，anomaly 记录被判 byte_exact）、HIGH-3（chmod 000 根 exit 0 假判 unrecoverable；glob 跟随 symlink 逃逸出根）；另 3 新 LOW（full_verified 长度范围应 131-180、distribution 省略 0 值键、line_count 数 LF 与 records 的 splitlines 口径不一）。开发方以 commit 73102875 提交整改。请只读复核这 6 项是否闭合：
564:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:186:1214: - **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
566:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:192:1232:+- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
567:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:193:1233:+- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
568:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:213:1937:99:- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
570:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:218:1947:118:- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
571:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:226:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
574:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:231:2148:    12	| HIGH-3 | **NOT-CLOSED** | 不存在根目录已 exit 2；递归唯一命中、多命中冲突、目录伪命中也通过。但“不可见”仍未闭合：存在但 `chmod 000` 的根会 exit 0 并假判 `unrecoverable`。此外 [`glob + os.path.isfile`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:134)跟随 symlink：根内 `.jsonl` symlink 指向根外 `.txt`、以及 symlink 目录逃逸到根外树，均被判唯一来源并进入 `approximate`。 |
576:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:245:2765:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:7:| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
577:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:246:2766:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:8:| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
579:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:248:2768:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:12:| HIGH-3 | **NOT-CLOSED** | 不存在根目录已 exit 2；递归唯一命中、多命中冲突、目录伪命中也通过。但“不可见”仍未闭合：存在但 `chmod 000` 的根会 exit 0 并假判 `unrecoverable`。此外 [`glob + os.path.isfile`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:134)跟随 symlink：根内 `.jsonl` symlink 指向根外 `.txt`、以及 symlink 目录逃逸到根外树，均被判唯一来源并进入 `approximate`。 |
580:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:249:2769:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:14:| MEDIUM-2 | **CLOSED** | [报告 §6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:78)、[ledger duplicate_clusters](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:60)及逐条 `reference_time` 已落地；6 簇全部逐行对账。 |
581:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:250:2772:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:14:CARD-G4-9 round-3 复审（静态审阅 + 只读复算）。你 round-2 裁定 10/13 CLOSED，三项 NOT-CLOSED：BLOCKER-1（--out 守卫比 resolve 字符串，hardlink 与 case-only 别名绕过截断输入）、HIGH-1（full_body_verified 只核 sha 不核长度且排在 anomaly 分支前，anomaly 记录被判 byte_exact）、HIGH-3（chmod 000 根 exit 0 假判 unrecoverable；glob 跟随 symlink 逃逸出根）；另 3 新 LOW（full_verified 长度范围应 131-180、distribution 省略 0 值键、line_count 数 LF 与 records 的 splitlines 口径不一）。开发方以 commit 73102875 提交整改。请只读复核这 6 项是否闭合：
583:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:252:2792:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1232:+- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
584:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:253:2793:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1234:+- **新 LOW ×3**：full_verified 长度范围修正为 131–180；台账 `class_distribution`/`recoverability_distribution` 补零并新增 `inline_state_distribution`（固定 schema，消费者无需补齐缺席键）；`line_count` 改用 `splitlines()` 与 records 同口径（原 `count("\n")` 在 bare CR / U+2028 下会与 records 数不一致）。
586:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:255:2810:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1948:119:- **新 LOW ×3**：full_verified 长度范围修正为 131–180；台账 `class_distribution`/`recoverability_distribution` 补零并新增 `inline_state_distribution`（固定 schema，消费者无需补齐缺席键）；`line_count` 改用 `splitlines()` 与 records 同口径（原 `count("\n")` 在 bare CR / U+2028 下会与 records 数不一致）。
587:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:256:2815:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
588:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:257:2816:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2144:     8	| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
590:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:259:2818:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2148:    12	| HIGH-3 | **NOT-CLOSED** | 不存在根目录已 exit 2；递归唯一命中、多命中冲突、目录伪命中也通过。但“不可见”仍未闭合：存在但 `chmod 000` 的根会 exit 0 并假判 `unrecoverable`。此外 [`glob + os.path.isfile`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:134)跟随 symlink：根内 `.jsonl` symlink 指向根外 `.txt`、以及 symlink 目录逃逸到根外树，均被判唯一来源并进入 `approximate`。 |
591:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:260:2819:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2150:    14	| MEDIUM-2 | **CLOSED** | [报告 §6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:78)、[ledger duplicate_clusters](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:60)及逐条 `reference_time` 已落地；6 簇全部逐行对账。 |
592:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:261:2850:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:61:- **3 新 LOW**：full_verified 长度范围修正 131–180；台账三个 distribution 补零并新增 `inline_state_distribution`；`line_count` 与 records 改用同一 `splitlines()` 口径。
594:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:277:3514:| LOW：distribution 零键 | **CLOSED** | [固定 schema 生成链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:437)与 [ledger](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:43)均包含 `unexpected/anomaly/unrecoverable: 0`，并新增 inline 三态。 |
595:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:282:3534:所以：**冻结的 92 条 ledger 数值可采信；CARD-G4-9 生成器与整卡验收仍被 BLOCKER-1、HIGH-3 阻断。** 本轮未修改仓库或受审数据，未执行破坏性 fixture/G4-10 重放；Graphiti 工具本轮不可用。
597:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:288:3547:| LOW：distribution 零键 | **CLOSED** | [固定 schema 生成链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:437)与 [ledger](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:43)均包含 `unexpected/anomaly/unrecoverable: 0`，并新增 inline 三态。 |
598:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:293:3567:所以：**冻结的 92 条 ledger 数值可采信；CARD-G4-9 生成器与整卡验收仍被 BLOCKER-1、HIGH-3 阻断。** 本轮未修改仓库或受审数据，未执行破坏性 fixture/G4-10 重放；Graphiti 工具本轮不可用。
601:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:340:@@ -52,7 +52,6 @@ BATCH-2026-08-28-第五批 / CARD-G4-9（G4-10 replay 的交接台账生成器
606:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:565:     4	BATCH-2026-08-28-第五批 / CARD-G4-9（G4-10 replay 的交接台账生成器）。
633:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1207:    95	| 负例门（round-2 整改自证） | **hardlink** 指向 DLQ 的 --out → exit 2 + DLQ sha 不变；**case-only 别名**（`DLQ.jsonl`）→ exit 2 + DLQ 完好；**anomaly + episode_body_full 组合**（sha 对但长度 999）→ anomaly/unrecoverable（不再翻案 byte_exact）；**chmod 000 根** → exit 2 拒诊；**symlink 逃逸**（根内 .jsonl → 根外 .txt）→ match_count=0/unrecoverable；正例回归：真实唯一命中仍 approximate |
634:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1211:    99	- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
635:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1213:   101	- **BLOCKER-3（交付物未冻结漂移）**：以本卡 commit 冻结全部交付物 exact bytes（脚本/报告/台账/证据包同 commit）；grep-selfattest 已按最终版行号重生成并内嵌脚本 sha 前缀。
638:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1217:   105	- **MEDIUM-1**：`episode_body_full` 在盘且 sha 对账通过 → byte_exact 采信（现网 0 条，通路已备）。
640:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1230:   118	- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
661:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1642:{"attribution_conflicts_from_records": 0, "class": {"budget_400": 89, "group_id_format": 1, "schema_entity_type": 2}, "duplicate_clusters_from_raw": 6, "duplicate_rows_from_raw": 29, "header_sha_match": true, "inline": {"full_verified": 4, "truncated_prefix": 88}, "ledger_derivation_mismatches": [], "lf_frames": 92, "parsed_records": 92, "raw_unparseable": 0, "recoverability_from_records": {"approximate": 88, "byte_exact": 4}, "source_sha256": "3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590", "transcript_path_metadata": {"missing": 0, "nonregular": 0, "symlink": 0, "unique": 7, "unreadable": 0}}
663:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1961:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:20:--- (4) 写出口（唯一，且经 O_NOFOLLOW+fstat inode 校验后才 ftruncate）:
664:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1962:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:21:517:            fd = os.open(args.out, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
665:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:1963:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:22:529:            os.ftruncate(fd, 0)
684:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:2175:不过生成器仍出现一个无需竞态的截断反例：匹配 transcript 若是“不可读但可写”（如 owner mode `0200`），扫描会把它从 `transcript_paths` 清掉，输出保护集因此漏掉它，而 `--out` 又能按写权限打开并截断。另有扫描错误最终仍被写成 `unrecoverable`，与“拒绝裁定”声明相反。终裁会据此维持阻断。
686:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:2307:| 3. HIGH-3 枚举 | **NOT-CLOSED** | 稳态目录 symlink、`scandir` 错误和 mode `000` 门已有改善。但 unreadable/walk error 设置 conflict 后，主链仍在 [395–397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:395)明确产出 `recoverability=unrecoverable`，直接反驳报告所称“既不宣称不可恢复” [报告:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:143)。此外 `os.walk.onerror` 只覆盖 `scandir`；逐条 `is_dir/stat` 错误可被静默当非候选，[islink→isfile→access→realpath](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:168)仍是路径级竞态。 |
688:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:2344:| 3. HIGH-3 枚举 | **NOT-CLOSED** | 稳态目录 symlink、`scandir` 错误和 mode `000` 门已有改善。但 unreadable/walk error 设置 conflict 后，主链仍在 [395–397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:395)明确产出 `recoverability=unrecoverable`，直接反驳报告所称“既不宣称不可恢复” [报告:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:143)。此外 `os.walk.onerror` 只覆盖 `scandir`；逐条 `is_dir/stat` 错误可被静默当非候选，[islink→isfile→access→realpath](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:168)仍是路径级竞态。 |
690:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:14:CARD-G4-9 round-5 终裁复审（静态审阅 + 只读复算，禁改任何文件）。你 round-4 裁定 1/6 CLOSED，提出 2 BLOCKER / 1 HIGH / 2 MEDIUM / 3 LOW。开发方以 commit d2827a6d + d8d887f2 提交整改，请逐条只读复核：
691:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:22:请对每项设计静态反例判断是否仍可绕过（尤其：保护集完整性、fd 身份与实际读取的绑定、unverifiable 与 unrecoverable 的语义边界、strict decode 的边界）。同时独立复算台账仍为 92 条 / class 89-2-1 / byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0 / 重复簇 6 簇 29 行 / unparseable 0。逐项 CLOSED/NOT-CLOSED + 总裁定（可验收/仍阻断）+ 新发现分级。若已可验收请明确说明；若仍阻断请说明**对一张只读 census 卡**而言该阻断是否与卡面范围相称。
694:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:192:_bmad-output/审查/codex-review-CARD-G4-9-round2.md
699:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:200:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md
708:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:267:M	"_bmad-output/\351\252\214\346\224\266\345\215\225/UAT-CARD-G4-9-DLQ\347\234\237\345\256\236\346\214\202\350\275\275census\345\210\206\350\257\212-2026-08-28.md"
713:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:276:67ccebe1 docs(census): G4-9 DLQ真实挂载census分诊 92条台账+挂载真相+三态裁定 [BATCH-2026-08-28-第五批 / CARD-G4-9]
729:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:870:/bin/zsh -lc "rg -n 'BLOCKER|HIGH|MEDIUM|LOW|CLOSED|NOT-CLOSED|保护集|TOCTOU|UTF-8|unverifiable|unrecoverable|provenance|92|89|29' '_bmad-output/审查/codex-review-CARD-G4-9-round4.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
731:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:882:94:/bin/zsh -lc "rg -n -i \"CARD-G4-9|G4-9|fce0d8a2|92 条|89-2-1|4-88-0\" /Users/Heishing/.codex/memories/rollout_summaries /Users/Heishing/.codex/memories/MEMORY.md --glob '*.md' --glob '*.jsonl' || true
732:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:883:131:67ccebe1 docs(census): G4-9 DLQ真实挂载census分诊 92条台账+挂载真相+三态裁定 [BATCH-2026-08-28-第五批 / CARD-G4-9]
733:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:884:145:rg -n \"BLOCKER-1|HIGH-3|JSONL|framing|非 dict|provenance|PARTIAL|CLOSED|NOT-CLOSED|新发现|总裁定|protected_ids|O_NOFOLLOW|os\\.walk|line_count\" '_bmad-output/审查/codex-review-CARD-G4-9-round3.md' | head -n 240
734:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:885:160:14:CARD-G4-9 round-3 复审（静态审阅 + 只读复算）。你 round-2 裁定 10/13 CLOSED，三项 NOT-CLOSED：BLOCKER-1（--out 守卫比 resolve 字符串，hardlink 与 case-only 别名绕过截断输入）、HIGH-1（full_body_verified 只核 sha 不核长度且排在 anomaly 分支前，anomaly 记录被判 byte_exact）、HIGH-3（chmod 000 根 exit 0 假判 unrecoverable；glob 跟随 symlink 逃逸出根）；另 3 新 LOW（full_verified 长度范围应 131-180、distribution 省略 0 值键、line_count 数 LF 与 records 的 splitlines 口径不一）。开发方以 commit 73102875 提交整改。请只读复核这 6 项是否闭合：
735:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:899:186:1214: - **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
737:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:905:192:1232:+- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
738:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:906:193:1233:+- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
739:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:919:213:1937:99:- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
740:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:923:217:1946:117:- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
741:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:924:218:1947:118:- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
742:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:928:226:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
745:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:933:231:2148:    12	| HIGH-3 | **NOT-CLOSED** | 不存在根目录已 exit 2；递归唯一命中、多命中冲突、目录伪命中也通过。但“不可见”仍未闭合：存在但 `chmod 000` 的根会 exit 0 并假判 `unrecoverable`。此外 [`glob + os.path.isfile`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:134)跟随 symlink：根内 `.jsonl` symlink 指向根外 `.txt`、以及 symlink 目录逃逸到根外树，均被判唯一来源并进入 `approximate`。 |
747:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:944:245:2765:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:7:| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
748:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:945:246:2766:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:8:| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
750:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:947:248:2768:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:12:| HIGH-3 | **NOT-CLOSED** | 不存在根目录已 exit 2；递归唯一命中、多命中冲突、目录伪命中也通过。但“不可见”仍未闭合：存在但 `chmod 000` 的根会 exit 0 并假判 `unrecoverable`。此外 [`glob + os.path.isfile`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:134)跟随 symlink：根内 `.jsonl` symlink 指向根外 `.txt`、以及 symlink 目录逃逸到根外树，均被判唯一来源并进入 `approximate`。 |
751:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:948:249:2769:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:14:| MEDIUM-2 | **CLOSED** | [报告 §6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:78)、[ledger duplicate_clusters](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:60)及逐条 `reference_time` 已落地；6 簇全部逐行对账。 |
752:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:949:250:2772:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:14:CARD-G4-9 round-3 复审（静态审阅 + 只读复算）。你 round-2 裁定 10/13 CLOSED，三项 NOT-CLOSED：BLOCKER-1（--out 守卫比 resolve 字符串，hardlink 与 case-only 别名绕过截断输入）、HIGH-1（full_body_verified 只核 sha 不核长度且排在 anomaly 分支前，anomaly 记录被判 byte_exact）、HIGH-3（chmod 000 根 exit 0 假判 unrecoverable；glob 跟随 symlink 逃逸出根）；另 3 新 LOW（full_verified 长度范围应 131-180、distribution 省略 0 值键、line_count 数 LF 与 records 的 splitlines 口径不一）。开发方以 commit 73102875 提交整改。请只读复核这 6 项是否闭合：
753:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:950:252:2792:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1232:+- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
754:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:951:253:2793:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1234:+- **新 LOW ×3**：full_verified 长度范围修正为 131–180；台账 `class_distribution`/`recoverability_distribution` 补零并新增 `inline_state_distribution`（固定 schema，消费者无需补齐缺席键）；`line_count` 改用 `splitlines()` 与 records 同口径（原 `count("\n")` 在 bare CR / U+2028 下会与 records 数不一致）。
756:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:953:255:2810:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1948:119:- **新 LOW ×3**：full_verified 长度范围修正为 131–180；台账 `class_distribution`/`recoverability_distribution` 补零并新增 `inline_state_distribution`（固定 schema，消费者无需补齐缺席键）；`line_count` 改用 `splitlines()` 与 records 同口径（原 `count("\n")` 在 bare CR / U+2028 下会与 records 数不一致）。
757:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:954:256:2815:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
758:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:955:257:2816:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2144:     8	| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
760:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:957:259:2818:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2148:    12	| HIGH-3 | **NOT-CLOSED** | 不存在根目录已 exit 2；递归唯一命中、多命中冲突、目录伪命中也通过。但“不可见”仍未闭合：存在但 `chmod 000` 的根会 exit 0 并假判 `unrecoverable`。此外 [`glob + os.path.isfile`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:134)跟随 symlink：根内 `.jsonl` symlink 指向根外 `.txt`、以及 symlink 目录逃逸到根外树，均被判唯一来源并进入 `approximate`。 |
761:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:958:260:2819:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2150:    14	| MEDIUM-2 | **CLOSED** | [报告 §6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:78)、[ledger duplicate_clusters](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:60)及逐条 `reference_time` 已落地；6 簇全部逐行对账。 |
762:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:959:261:2850:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:61:- **3 新 LOW**：full_verified 长度范围修正 131–180；台账三个 distribution 补零并新增 `inline_state_distribution`；`line_count` 与 records 改用同一 `splitlines()` 口径。
764:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:968:277:3514:| LOW：distribution 零键 | **CLOSED** | [固定 schema 生成链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:437)与 [ledger](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:43)均包含 `unexpected/anomaly/unrecoverable: 0`，并新增 inline 三态。 |
765:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:972:282:3534:所以：**冻结的 92 条 ledger 数值可采信；CARD-G4-9 生成器与整卡验收仍被 BLOCKER-1、HIGH-3 阻断。** 本轮未修改仓库或受审数据，未执行破坏性 fixture/G4-10 重放；Graphiti 工具本轮不可用。
767:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:978:288:3547:| LOW：distribution 零键 | **CLOSED** | [固定 schema 生成链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:437)与 [ledger](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:43)均包含 `unexpected/anomaly/unrecoverable: 0`，并新增 inline 三态。 |
768:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:982:293:3567:所以：**冻结的 92 条 ledger 数值可采信；CARD-G4-9 生成器与整卡验收仍被 BLOCKER-1、HIGH-3 阻断。** 本轮未修改仓库或受审数据，未执行破坏性 fixture/G4-10 重放；Graphiti 工具本轮不可用。
785:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1090:1207:    95	| 负例门（round-2 整改自证） | **hardlink** 指向 DLQ 的 --out → exit 2 + DLQ sha 不变；**case-only 别名**（`DLQ.jsonl`）→ exit 2 + DLQ 完好；**anomaly + episode_body_full 组合**（sha 对但长度 999）→ anomaly/unrecoverable（不再翻案 byte_exact）；**chmod 000 根** → exit 2 拒诊；**symlink 逃逸**（根内 .jsonl → 根外 .txt）→ match_count=0/unrecoverable；正例回归：真实唯一命中仍 approximate |
786:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1091:1211:    99	- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
787:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1093:1213:   101	- **BLOCKER-3（交付物未冻结漂移）**：以本卡 commit 冻结全部交付物 exact bytes（脚本/报告/台账/证据包同 commit）；grep-selfattest 已按最终版行号重生成并内嵌脚本 sha 前缀。
790:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1097:1217:   105	- **MEDIUM-1**：`episode_body_full` 在盘且 sha 对账通过 → byte_exact 采信（现网 0 条，通路已备）。
792:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1106:1230:   118	- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
805:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1158:1642:{"attribution_conflicts_from_records": 0, "class": {"budget_400": 89, "group_id_format": 1, "schema_entity_type": 2}, "duplicate_clusters_from_raw": 6, "duplicate_rows_from_raw": 29, "header_sha_match": true, "inline": {"full_verified": 4, "truncated_prefix": 88}, "ledger_derivation_mismatches": [], "lf_frames": 92, "parsed_records": 92, "raw_unparseable": 0, "recoverability_from_records": {"approximate": 88, "byte_exact": 4}, "source_sha256": "3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590", "transcript_path_metadata": {"missing": 0, "nonregular": 0, "symlink": 0, "unique": 7, "unreadable": 0}}
806:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1175:1961:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:20:--- (4) 写出口（唯一，且经 O_NOFOLLOW+fstat inode 校验后才 ftruncate）:
807:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1176:1962:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:21:517:            fd = os.open(args.out, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
808:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1177:1963:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:22:529:            os.ftruncate(fd, 0)
815:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1208:2175:不过生成器仍出现一个无需竞态的截断反例：匹配 transcript 若是“不可读但可写”（如 owner mode `0200`），扫描会把它从 `transcript_paths` 清掉，输出保护集因此漏掉它，而 `--out` 又能按写权限打开并截断。另有扫描错误最终仍被写成 `unrecoverable`，与“拒绝裁定”声明相反。终裁会据此维持阻断。
816:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1216:2307:| 3. HIGH-3 枚举 | **NOT-CLOSED** | 稳态目录 symlink、`scandir` 错误和 mode `000` 门已有改善。但 unreadable/walk error 设置 conflict 后，主链仍在 [395–397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:395)明确产出 `recoverability=unrecoverable`，直接反驳报告所称“既不宣称不可恢复” [报告:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:143)。此外 `os.walk.onerror` 只覆盖 `scandir`；逐条 `is_dir/stat` 错误可被静默当非候选，[islink→isfile→access→realpath](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:168)仍是路径级竞态。 |
818:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1235:2344:| 3. HIGH-3 枚举 | **NOT-CLOSED** | 稳态目录 symlink、`scandir` 错误和 mode `000` 门已有改善。但 unreadable/walk error 设置 conflict 后，主链仍在 [395–397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:395)明确产出 `recoverability=unrecoverable`，直接反驳报告所称“既不宣称不可恢复” [报告:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:143)。此外 `os.walk.onerror` 只覆盖 `scandir`；逐条 `is_dir/stat` 错误可被静默当非候选，[islink→isfile→access→realpath](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:168)仍是路径级竞态。 |
827:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1350:| 负例门（round-2 整改自证） | **hardlink** 指向 DLQ 的 --out → exit 2 + DLQ sha 不变；**case-only 别名**（`DLQ.jsonl`）→ exit 2 + DLQ 完好；**anomaly + episode_body_full 组合**（sha 对但长度 999）→ anomaly/unrecoverable（不再翻案 byte_exact）；**chmod 000 根** → exit 2 拒诊；**symlink 逃逸**（根内 .jsonl → 根外 .txt）→ match_count=0/unrecoverable；正例回归：真实唯一命中仍 approximate |
828:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1354:- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
829:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1356:- **BLOCKER-3（交付物未冻结漂移）**：以本卡 commit 冻结全部交付物 exact bytes（脚本/报告/台账/证据包同 commit）；grep-selfattest 已按最终版行号重生成并内嵌脚本 sha 前缀。
832:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1360:- **MEDIUM-1**：`episode_body_full` 在盘且 sha 对账通过 → byte_exact 采信（现网 0 条，通路已备）。
834:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1373:- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
838:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1422:67ccebe1  CARD-G4-9 初版交付（脚本/报告/台账/证据包/round-1 审查/UAT）
842:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1448:CARD-G4-9 round-5 终裁复审（静态审阅 + 只读复算，禁改任何文件）。你 round-4 裁定 1/6 CLOSED，提出 2 BLOCKER / 1 HIGH / 2 MEDIUM / 3 LOW。开发方以 commit d2827a6d + d8d887f2 提交整改，请逐条只读复核：
843:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1456:请对每项设计静态反例判断是否仍可绕过（尤其：保护集完整性、fd 身份与实际读取的绑定、unverifiable 与 unrecoverable 的语义边界、strict decode 的边界）。同时独立复算台账仍为 92 条 / class 89-2-1 / byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0 / 重复簇 6 簇 29 行 / unparseable 0。逐项 CLOSED/NOT-CLOSED + 总裁定（可验收/仍阻断）+ 新发现分级。若已可验收请明确说明；若仍阻断请说明**对一张只读 census 卡**而言该阻断是否与卡面范围相称。
854:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1926:   500	        if recover == "unrecoverable":
855:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:1927:   501	            unrecoverable_keys.append(stable_key)
860:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2099:     4	BATCH-2026-08-28-第五批 / CARD-G4-9（G4-10 replay 的交接台账生成器）。
867:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2281:/bin/zsh -lc "rg -n '不可读但可写|源侧 TOCTOU|不可见终态|非法 UTF-8|字段错型|root_prefix|fchmod|provenance|总裁定|BLOCKER' '_bmad-output/审查/codex-review-CARD-G4-9-round4.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
868:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2288:145:rg -n \"BLOCKER-1|HIGH-3|JSONL|framing|非 dict|provenance|PARTIAL|CLOSED|NOT-CLOSED|新发现|总裁定|protected_ids|O_NOFOLLOW|os\\.walk|line_count\" '_bmad-output/审查/codex-review-CARD-G4-9-round3.md' | head -n 240
869:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2289:160:14:CARD-G4-9 round-3 复审（静态审阅 + 只读复算）。你 round-2 裁定 10/13 CLOSED，三项 NOT-CLOSED：BLOCKER-1（--out 守卫比 resolve 字符串，hardlink 与 case-only 别名绕过截断输入）、HIGH-1（full_body_verified 只核 sha 不核长度且排在 anomaly 分支前，anomaly 记录被判 byte_exact）、HIGH-3（chmod 000 根 exit 0 假判 unrecoverable；glob 跟随 symlink 逃逸出根）；另 3 新 LOW（full_verified 长度范围应 131-180、distribution 省略 0 值键、line_count 数 LF 与 records 的 splitlines 口径不一）。开发方以 commit 73102875 提交整改。请只读复核这 6 项是否闭合：
870:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2298:186:1214: - **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
871:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2305:213:1937:99:- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
872:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2310:226:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
873:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2313:245:2765:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:7:| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
874:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2314:246:2766:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:8:| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
875:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2315:250:2772:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:14:CARD-G4-9 round-3 复审（静态审阅 + 只读复算）。你 round-2 裁定 10/13 CLOSED，三项 NOT-CLOSED：BLOCKER-1（--out 守卫比 resolve 字符串，hardlink 与 case-only 别名绕过截断输入）、HIGH-1（full_body_verified 只核 sha 不核长度且排在 anomaly 分支前，anomaly 记录被判 byte_exact）、HIGH-3（chmod 000 根 exit 0 假判 unrecoverable；glob 跟随 symlink 逃逸出根）；另 3 新 LOW（full_verified 长度范围应 131-180、distribution 省略 0 值键、line_count 数 LF 与 records 的 splitlines 口径不一）。开发方以 commit 73102875 提交整改。请只读复核这 6 项是否闭合：
876:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2316:256:2815:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
877:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2317:257:2816:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2144:     8	| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
878:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2325:282:3534:所以：**冻结的 92 条 ledger 数值可采信；CARD-G4-9 生成器与整卡验收仍被 BLOCKER-1、HIGH-3 阻断。** 本轮未修改仓库或受审数据，未执行破坏性 fixture/G4-10 重放；Graphiti 工具本轮不可用。
879:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2329:293:3567:所以：**冻结的 92 条 ledger 数值可采信；CARD-G4-9 生成器与整卡验收仍被 BLOCKER-1、HIGH-3 阻断。** 本轮未修改仓库或受审数据，未执行破坏性 fixture/G4-10 重放；Graphiti 工具本轮不可用。
880:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2340:1211:    99	- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
881:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2342:1213:   101	- **BLOCKER-3（交付物未冻结漂移）**：以本卡 commit 冻结全部交付物 exact bytes（脚本/报告/台账/证据包同 commit）；grep-selfattest 已按最终版行号重生成并内嵌脚本 sha 前缀。
882:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2351:2175:不过生成器仍出现一个无需竞态的截断反例：匹配 transcript 若是“不可读但可写”（如 owner mode `0200`），扫描会把它从 `transcript_paths` 清掉，输出保护集因此漏掉它，而 `--out` 又能按写权限打开并截断。另有扫描错误最终仍被写成 `unrecoverable`，与“拒绝裁定”声明相反。终裁会据此维持阻断。
884:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2388:  2307	| 3. HIGH-3 枚举 | **NOT-CLOSED** | 稳态目录 symlink、`scandir` 错误和 mode `000` 门已有改善。但 unreadable/walk error 设置 conflict 后，主链仍在 [395–397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:395)明确产出 `recoverability=unrecoverable`，直接反驳报告所称“既不宣称不可恢复” [报告:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:143)。此外 `os.walk.onerror` 只覆盖 `scandir`；逐条 `is_dir/stat` 错误可被静默当非候选，[islink→isfile→access→realpath](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:168)仍是路径级竞态。 |
886:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2425:  2344	| 3. HIGH-3 枚举 | **NOT-CLOSED** | 稳态目录 symlink、`scandir` 错误和 mode `000` 门已有改善。但 unreadable/walk error 设置 conflict 后，主链仍在 [395–397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:395)明确产出 `recoverability=unrecoverable`，直接反驳报告所称“既不宣称不可恢复” [报告:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:143)。此外 `os.walk.onerror` 只覆盖 `scandir`；逐条 `is_dir/stat` 错误可被静默当非候选，[islink→isfile→access→realpath](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:168)仍是路径级竞态。 |
890:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2487:     5	67ccebe1  CARD-G4-9 初版交付（脚本/报告/台账/证据包/round-1 审查/UAT）
891:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2492:    10	d2827a6d  CARD-G4-9 round-4 整改（本 receipt 所描述的 commit）
910:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2954:/bin/zsh -lc "rg -n '0 写|只读|保护|qa_metrics|transcript|92|89|byte_exact|unverifiable|unrecoverable|验收' '_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
911:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2956:6:scope: "BATCH-2026-08-28-第五批 / CARD-G4-9 — live DLQ 92 条只读 census：分类/SHA 对账/可恢复性三态/挂载真相，产出 G4-10 交接台账"
913:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2968:35:| Codex 独立审查 round-1 | **BLOCKED**（3 BLOCKER：--out 可截断输入 / 快照不原子 / 交付物未冻结；3 HIGH：inline 判定 fail-open / request_id 归因传染 / transcript 归因折叠；3 MEDIUM + 4 LOW。同时确认：**当前 92 条数字逐项 0 mismatch**、class/三态/家族计数全对） | `_bmad-output/审查/codex-review-CARD-G4-9.md` |
914:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2969:37:| Codex 复审 round-2 | **仍阻断**（10/13 CLOSED；BLOCKER-1/HIGH-1/HIGH-3 未真正闭合 + 3 新 LOW）。同时独立复算确认：67ccebe1 冻结生效、92 条数字与 6/29 重复簇全部可复算 | `_bmad-output/审查/codex-review-CARD-G4-9-round2.md`（codex 被 cyber 误拦，内容由 stdout 抢救存档） |
915:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2970:40:| round-3 findings 逐条整改 | **6/6 完成**：transcript 并入保护集 / O_NOFOLLOW+fstat 消 TOCTOU / os.walk 替 glob（不跟随目录 symlink+遍历错误显式捕获）/ 不可读候选 fail-closed / JSONL 严格 LF 分帧 / 非 dict 归 unparseable。6 条新反例实测全过、数字第三次不变 | 报告 §7d + `grep-selfattest.txt` |
916:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2971:42:| round-4 findings 逐条整改 | **9/9 完成**：全候选入保护集 / 读侧 fd 身份消源侧 TOCTOU / 新增 unverifiable 第四态 / FIFO 设备门 / strict UTF-8 / 3 条错型与边界 LOW / provenance receipt。5 条新反例实测全过；第四次全量重跑数字仍不变 | 报告 §7e + `grep-selfattest.txt` |
922:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3063:/bin/zsh -lc "nl -ba '_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md' | sed -n '145,175p'; nl -ba '_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md' | sed -n '8,45p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
924:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3086:    10	# UAT · CARD-G4-9 DLQ 真实挂载 census 分诊
926:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3111:    35	| Codex 独立审查 round-1 | **BLOCKED**（3 BLOCKER：--out 可截断输入 / 快照不原子 / 交付物未冻结；3 HIGH：inline 判定 fail-open / request_id 归因传染 / transcript 归因折叠；3 MEDIUM + 4 LOW。同时确认：**当前 92 条数字逐项 0 mismatch**、class/三态/家族计数全对） | `_bmad-output/审查/codex-review-CARD-G4-9.md` |
927:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3113:    37	| Codex 复审 round-2 | **仍阻断**（10/13 CLOSED；BLOCKER-1/HIGH-1/HIGH-3 未真正闭合 + 3 新 LOW）。同时独立复算确认：67ccebe1 冻结生效、92 条数字与 6/29 重复簇全部可复算 | `_bmad-output/审查/codex-review-CARD-G4-9-round2.md`（codex 被 cyber 误拦，内容由 stdout 抢救存档） |
928:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3114:    38	| round-2 findings 逐条整改 | **6/6 完成**：inode 身份守卫封 hardlink+大小写别名 / full_body 长度门+anomaly 前置 / 不可读根 exit 2+symlink 逃逸拒采信 / 3 新 LOW。5 条新负例实测全过、正例无回归、数字仍逐项一致 | 报告 §7/§7c + `grep-selfattest.txt` |
929:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3115:    39	| Codex 复审 round-3 | **仍阻断**（4/6 CLOSED；BLOCKER-1/HIGH-3 判 PARTIAL + 1 新 MEDIUM + 2 新 LOW）。同时确认：HIGH-1 与三条 LOW 已闭合、台账数字有效且与 commit 字节一致 | `_bmad-output/审查/codex-review-CARD-G4-9-round3.md` |
930:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3116:    40	| round-3 findings 逐条整改 | **6/6 完成**：transcript 并入保护集 / O_NOFOLLOW+fstat 消 TOCTOU / os.walk 替 glob（不跟随目录 symlink+遍历错误显式捕获）/ 不可读候选 fail-closed / JSONL 严格 LF 分帧 / 非 dict 归 unparseable。6 条新反例实测全过、数字第三次不变 | 报告 §7d + `grep-selfattest.txt` |
931:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3117:    41	| Codex 复审 round-4 | **仍阻断**（1/6 CLOSED；2 新 BLOCKER + 1 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round4.md` |
932:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3118:    42	| round-4 findings 逐条整改 | **9/9 完成**：全候选入保护集 / 读侧 fd 身份消源侧 TOCTOU / 新增 unverifiable 第四态 / FIFO 设备门 / strict UTF-8 / 3 条错型与边界 LOW / provenance receipt。5 条新反例实测全过；第四次全量重跑数字仍不变 | 报告 §7e + `grep-selfattest.txt` |
938:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3332:总裁定：**仍阻断 / CARD-G4-9 不可验收**。  
941:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3370:这个阻断与“一张只读 census 卡”的范围**完全相称**：报告和 UAT 明确承诺纯只读、零写入，[UAT:13](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:13)。残留反例能直接截断或修改本卡正在保护的恢复源，不是范围外的生产级加固要求。
942:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3377:总裁定：**仍阻断 / CARD-G4-9 不可验收**。  
945:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:3415:这个阻断与“一张只读 census 卡”的范围**完全相称**：报告和 UAT 明确承诺纯只读、零写入，[UAT:13](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:13)。残留反例能直接截断或修改本卡正在保护的恢复源，不是范围外的生产级加固要求。
979:./_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:926:   "attribution_conflict_reason": null,
1046:./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:3:title: "UAT · CARD-G4-9 DLQ 真实挂载 census 分诊（2026-08-28）"
1047:./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:6:scope: "BATCH-2026-08-28-第五批 / CARD-G4-9 — live DLQ 92 条只读 census：分类/SHA 对账/可恢复性三态/挂载真相，产出 G4-10 交接台账"
1048:./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:10:# UAT · CARD-G4-9 DLQ 真实挂载 census 分诊
1049:./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:28:| 脚本只读自证（判据 a） | import 行全 stdlib；neo4j/graphiti/bolt/app. import **0 命中**；`--apply` 定义 **0 命中**；写模式 open 仅台账 `--out` 1 处 | `G4-9-evidence/grep-selfattest.txt` |
1050:./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:35:| Codex 独立审查 round-1 | **BLOCKED**（3 BLOCKER：--out 可截断输入 / 快照不原子 / 交付物未冻结；3 HIGH：inline 判定 fail-open / request_id 归因传染 / transcript 归因折叠；3 MEDIUM + 4 LOW。同时确认：**当前 92 条数字逐项 0 mismatch**、class/三态/家族计数全对） | `_bmad-output/审查/codex-review-CARD-G4-9.md` |
1051:./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:37:| Codex 复审 round-2 | **仍阻断**（10/13 CLOSED；BLOCKER-1/HIGH-1/HIGH-3 未真正闭合 + 3 新 LOW）。同时独立复算确认：67ccebe1 冻结生效、92 条数字与 6/29 重复簇全部可复算 | `_bmad-output/审查/codex-review-CARD-G4-9-round2.md`（codex 被 cyber 误拦，内容由 stdout 抢救存档） |
1052:./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:38:| round-2 findings 逐条整改 | **6/6 完成**：inode 身份守卫封 hardlink+大小写别名 / full_body 长度门+anomaly 前置 / 不可读根 exit 2+symlink 逃逸拒采信 / 3 新 LOW。5 条新负例实测全过、正例无回归、数字仍逐项一致 | 报告 §7/§7c + `grep-selfattest.txt` |
1053:./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:39:| Codex 复审 round-3 | **仍阻断**（4/6 CLOSED；BLOCKER-1/HIGH-3 判 PARTIAL + 1 新 MEDIUM + 2 新 LOW）。同时确认：HIGH-1 与三条 LOW 已闭合、台账数字有效且与 commit 字节一致 | `_bmad-output/审查/codex-review-CARD-G4-9-round3.md` |
1054:./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:40:| round-3 findings 逐条整改 | **6/6 完成**：transcript 并入保护集 / O_NOFOLLOW+fstat 消 TOCTOU / os.walk 替 glob（不跟随目录 symlink+遍历错误显式捕获）/ 不可读候选 fail-closed / JSONL 严格 LF 分帧 / 非 dict 归 unparseable。6 条新反例实测全过、数字第三次不变 | 报告 §7d + `grep-selfattest.txt` |
1055:./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:41:| Codex 复审 round-4 | **仍阻断**（1/6 CLOSED；2 新 BLOCKER + 1 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round4.md` |
1056:./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:42:| round-4 findings 逐条整改 | **9/9 完成**：全候选入保护集 / 读侧 fd 身份消源侧 TOCTOU / 新增 unverifiable 第四态 / FIFO 设备门 / strict UTF-8 / 3 条错型与边界 LOW / provenance receipt。5 条新反例实测全过；第四次全量重跑数字仍不变 | 报告 §7e + `grep-selfattest.txt` |
1057:./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:43:| Codex 复审 round-5 | **仍阻断**（3/8 CLOSED；2 BLOCKER + 2 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round5.md` |
1058:./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:44:| round-5 findings 逐条整改 | **9/9 完成**：先扫描后判定（冲突候选亦入保护集）/ QA DB fd 身份+复核 / 可见性优先于 anomaly / fchmod 后置于碰撞检查 / QA DB 特殊文件门 / no_token 归 unverifiable / 3 条 LOW。6 条新反例实测全过；第五次全量重跑数字仍不变 | 报告 §7f |
1059:./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:45:| Codex 复审 round-6 | **6/9 CLOSED**（visibility 优先/fchmod 顺序/no_token 语义/3 条 LOW 已闭合）；剩 2 BLOCKER + 1 MEDIUM 揭示保护集**依赖枚举完整性**的架构缺陷 + 3 新发现 | `_bmad-output/审查/codex-review-CARD-G4-9-round6.md` |
1060:./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:46:| round-6 findings 整改 | **架构级修复 + 6 项**：新增不依赖枚举的**路径层防御**（--out 禁落 transcripts 根内 / 禁等于任一输入 realpath）、QA DB 验证 fd 保持打开至复核完毕、no_token 亦扫描、证据包重生成、ledger 冲突原因自描述、lone surrogate 回退。反例实测：0333 隐藏目录内 transcript 作 --out → exit 2 完好 | 报告 §7g |
1061:./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:54:- **HIGH-1 inline 判定 fail-open**：sha 匹配但长度不符会误判 full_verified（反例实测）。整改：长度精确匹配门 + 64-hex 合法性门 + anomaly 一律 fail-closed（unrecoverable + 如实 basis）。
1062:./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:56:- **HIGH-3 transcript 归因折叠**：多命中照单全收、目录缺失误判 unrecoverable=88（实测复现）。整改：恰 1 常规文件命中门 + 递归 glob + 目录缺失 exit 2 拒诊。
1063:./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:90:- **把"看不见"说成"不可恢复"**：扫描受阻时仍输出 `unrecoverable`，与报告里"既不宣称不可恢复"自相矛盾。→ 新增第四态 **`unverifiable`**，逐条写明是遍历受阻还是候选不可读。
1064:./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:101:- **anomaly 吞掉了"看不见"**：`anomaly→unrecoverable` 排在可见性判断之前，扫描受阻时仍断言"不可恢复"。→ 判定链改为**可见性优先**。
1065:./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:115:另修：QA DB 的验证 fd 改为**保持打开**到复核完毕（堵 ABA）；`no_token` 分支也扫描（原本完全不扫，候选进不了保护集）；证据包每轮重生成（round-6 指出我的 self-attest 停留在 round-4 的旧 SHA，属实）；台账新增冲突原因自描述。
1066:./_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:125:- `_bmad-output/审查/codex-review-CARD-G4-9.md` — Codex 独立审查存档
1068:./_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt:5:67ccebe1  CARD-G4-9 初版交付（脚本/报告/台账/证据包/round-1 审查/UAT）
1077:./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:92:| grep 自证（import 行全 stdlib；neo4j/graphiti/bolt/app. import 0 命中；`--apply` 定义 0 命中；写模式 open 仅 `--out` 1 处且受路径碰撞守卫保护） | **PASS**（`grep-selfattest.txt`，含守卫在位证明） |
1079:./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:96:| 负例门（round-2 整改自证） | **hardlink** 指向 DLQ 的 --out → exit 2 + DLQ sha 不变；**case-only 别名**（`DLQ.jsonl`）→ exit 2 + DLQ 完好；**anomaly + episode_body_full 组合**（sha 对但长度 999）→ anomaly/unrecoverable（不再翻案 byte_exact）；**chmod 000 根** → exit 2 拒诊；**symlink 逃逸**（根内 .jsonl → 根外 .txt）→ match_count=0/unrecoverable；正例回归：真实唯一命中仍 approximate |
1080:./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:100:- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
1081:./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:102:- **BLOCKER-3（交付物未冻结漂移）**：以本卡 commit 冻结全部交付物 exact bytes（脚本/报告/台账/证据包同 commit）；grep-selfattest 已按最终版行号重生成并内嵌脚本 sha 前缀。
1084:./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:106:- **MEDIUM-1**：`episode_body_full` 在盘且 sha 对账通过 → byte_exact 采信（现网 0 条，通路已备）。
1086:./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:119:- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
1090:./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:174:- **MEDIUM（无 token 未扫描即判不可恢复）**：改为 `unverifiable` + `no_token` 标记（见 HIGH①）。
1092:./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:179:round-5 整改后第五次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变——五轮整改数字全程未变**。
1093:./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:183:round-6 确认 visibility 优先、fchmod 顺序、no_token 语义、三条 LOW 共 6 项 CLOSED，并揭示了一个**架构层面的根因**：
1094:./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:189:- **BLOCKER① 补充修复**：`no_token` 分支原本完全不扫描（`all_candidate_paths=[]`）→ 改为**无论有无 token 都遍历**，所有 `.jsonl` 一律入保护集口径。
1095:./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:190:- **MEDIUM（证据包漂移）**：`grep-selfattest.txt` 曾停留在 round-4 的脚本 SHA 与旧行号、receipt 未含最新 commit——这是我的疏漏。已重生成（内嵌当前脚本 sha256 + 生成时点声明），receipt 随本轮补链。
1096:./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:191:- **LOW ×3**：ledger 新增 `attribution_conflict_reason` 自描述（本次 92 条：`no_token` 3 / 其余 89 无冲突）；`json.dumps` 对 lone surrogate 回退 `ensure_ascii=True` 并显式标注，不再整次 census 拒绝；`stat_failures` 分支保留（Codex 确认非额外绕过，仅基本不可达）。
1097:./_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:193:round-6 整改后第六次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变——六轮整改数字全程未变**。
1098:./_bmad-output/审查/G4-9-evidence/census-stderr.txt:1:census: 92 条 (+0 unparseable) | class={'schema_entity_type': 2, 'group_id_format': 1, 'budget_400': 89} | recoverability={'byte_exact': 4, 'approximate': 88} | 归因冲突=3 | 重复簇=6 | 偏差=无 | qa_metrics 核销=no_source_rows
1100:./_bmad-output/审查/codex-review-CARD-G4-9-round7.md:14:CARD-G4-9 round-7 复审（静态审阅 + 只读复算，禁改任何文件）。你 round-6 裁定 6/9 CLOSED，两项 BLOCKER 揭示了根因：--out 保护集依赖枚举完整性（0333 不可列举目录内的 transcript、QA DB inode ABA 都能挫败它）。开发方接受该判断，做了**架构级修复**并以 commit 5b371253 + 后续 receipt commit 提交：
1105:./_bmad-output/审查/codex-review-CARD-G4-9-round7.md:20:请逐项复核是否闭合，并针对路径层防御设计新反例（如 --out 位于 transcripts 根外但通过 symlink/hardlink 指入根内的文件、transcripts 根本身是 symlink、相对路径与 .. 组合、TOCTOU 把 --out 在检查后换成指入根内的链接）。同时复核台账仍为 92 条 / class 89-2-1 / byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0 / 重复簇 6/29 / unparseable 0 / attribution_conflict 3(no_token)。逐项 CLOSED/NOT-CLOSED + 总裁定 + 新发现分级；若可验收请明确说明。
1107:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:14:CARD-G4-9 round-3 复审（静态审阅 + 只读复算）。你 round-2 裁定 10/13 CLOSED，三项 NOT-CLOSED：BLOCKER-1（--out 守卫比 resolve 字符串，hardlink 与 case-only 别名绕过截断输入）、HIGH-1（full_body_verified 只核 sha 不核长度且排在 anomaly 分支前，anomaly 记录被判 byte_exact）、HIGH-3（chmod 000 根 exit 0 假判 unrecoverable；glob 跟随 symlink 逃逸出根）；另 3 新 LOW（full_verified 长度范围应 131-180、distribution 省略 0 值键、line_count 数 LF 与 records 的 splitlines 口径不一）。开发方以 commit 73102875 提交整改。请只读复核这 6 项是否闭合：
1114:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:614: BATCH-2026-08-28-第五批 / CARD-G4-9（G4-10 replay 的交接台账生成器）。
1120:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:653:-    重算 sha 对账通过则按 byte_exact 采信（Codex round-1 MEDIUM-1 整改）。
1144:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1210:+| 负例门（round-2 整改自证） | **hardlink** 指向 DLQ 的 --out → exit 2 + DLQ sha 不变；**case-only 别名**（`DLQ.jsonl`）→ exit 2 + DLQ 完好；**anomaly + episode_body_full 组合**（sha 对但长度 999）→ anomaly/unrecoverable（不再翻案 byte_exact）；**chmod 000 根** → exit 2 拒诊；**symlink 逃逸**（根内 .jsonl → 根外 .txt）→ match_count=0/unrecoverable；正例回归：真实唯一命中仍 approximate |
1145:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1214: - **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
1146:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1216: - **BLOCKER-3（交付物未冻结漂移）**：以本卡 commit 冻结全部交付物 exact bytes（脚本/报告/台账/证据包同 commit）；grep-selfattest 已按最终版行号重生成并内嵌脚本 sha 前缀。
1149:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1220: - **MEDIUM-1**：`episode_body_full` 在盘且 sha 对账通过 → byte_exact 采信（现网 0 条，通路已备）。
1151:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1233:+- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
1159:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1433:     4	BATCH-2026-08-28-第五批 / CARD-G4-9（G4-10 replay 的交接台账生成器）。
1179:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1935:95:| 负例门（round-2 整改自证） | **hardlink** 指向 DLQ 的 --out → exit 2 + DLQ sha 不变；**case-only 别名**（`DLQ.jsonl`）→ exit 2 + DLQ 完好；**anomaly + episode_body_full 组合**（sha 对但长度 999）→ anomaly/unrecoverable（不再翻案 byte_exact）；**chmod 000 根** → exit 2 拒诊；**symlink 逃逸**（根内 .jsonl → 根外 .txt）→ match_count=0/unrecoverable；正例回归：真实唯一命中仍 approximate |
1180:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1937:99:- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
1183:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1947:118:- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
1188:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2113:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:25:266:    # (st_dev, st_ino) 而非 resolve() 字符串 —— 后者对 hardlink 与
1189:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2114:_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:30:--- (6) fail-closed 门（不可读根 / symlink 逃逸 / anomaly 前置）:
1194:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2130:"_bmad-output/\351\252\214\346\224\266\345\215\225/UAT-CARD-G4-9-DLQ\347\234\237\345\256\236\346\214\202\350\275\275census\345\210\206\350\257\212-2026-08-28.md"
1196:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
1199:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2148:    12	| HIGH-3 | **NOT-CLOSED** | 不存在根目录已 exit 2；递归唯一命中、多命中冲突、目录伪命中也通过。但“不可见”仍未闭合：存在但 `chmod 000` 的根会 exit 0 并假判 `unrecoverable`。此外 [`glob + os.path.isfile`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:134)跟随 symlink：根内 `.jsonl` symlink 指向根外 `.txt`、以及 symlink 目录逃逸到根外树，均被判唯一来源并进入 `approximate`。 |
1201:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2170:    34	- **LOW**：ledger distribution 省略 `unexpected:0`、`anomaly:0`、`unrecoverable:0`，固定 schema 消费者需自行补零。
1210:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2590:   292	            recover = "unrecoverable"
1217:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2765:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:7:| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
1218:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2766:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:8:| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
1220:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2768:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:12:| HIGH-3 | **NOT-CLOSED** | 不存在根目录已 exit 2；递归唯一命中、多命中冲突、目录伪命中也通过。但“不可见”仍未闭合：存在但 `chmod 000` 的根会 exit 0 并假判 `unrecoverable`。此外 [`glob + os.path.isfile`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:134)跟随 symlink：根内 `.jsonl` symlink 指向根外 `.txt`、以及 symlink 目录逃逸到根外树，均被判唯一来源并进入 `approximate`。 |
1221:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2769:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:14:| MEDIUM-2 | **CLOSED** | [报告 §6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:78)、[ledger duplicate_clusters](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:60)及逐条 `reference_time` 已落地；6 簇全部逐行对账。 |
1222:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2772:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:14:CARD-G4-9 round-3 复审（静态审阅 + 只读复算）。你 round-2 裁定 10/13 CLOSED，三项 NOT-CLOSED：BLOCKER-1（--out 守卫比 resolve 字符串，hardlink 与 case-only 别名绕过截断输入）、HIGH-1（full_body_verified 只核 sha 不核长度且排在 anomaly 分支前，anomaly 记录被判 byte_exact）、HIGH-3（chmod 000 根 exit 0 假判 unrecoverable；glob 跟随 symlink 逃逸出根）；另 3 新 LOW（full_verified 长度范围应 131-180、distribution 省略 0 值键、line_count 数 LF 与 records 的 splitlines 口径不一）。开发方以 commit 73102875 提交整改。请只读复核这 6 项是否闭合：
1240:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2790:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1194: 台账逐条携带复合键 `{line_no, sha256_prefix(16 hex), request_id}`。**语义（Codex round-1 LOW-2 修正）**：这是**冻结快照内的 occurrence key**，不是跨文件重排或语义幂等键——台账头部 `dlq_file.sha256`（`3b37460f4215f6ac…`）即快照指纹，`line_no` 在该快照内已单列唯一；`sha256_prefix`（本快照 69 个唯一值，qa_highlight 家族实测同名同 sha 多条）与 `request_id`（仅 25 个唯一值，进程内 contextvars、重启可复用）是**冗余对账/诊断维度**，不是唯一性的必要条件。G4-10 消费前先 diff 头部 sha 即知 DLQ 是否长了新条目；语义级去重不得按本键，须按 `duplicate_clusters` 段（见下）。**语义重复簇（MEDIUM-2 整改）**：按 `{name, episode_body_sha256, group_id}` 聚簇，**6 簇覆盖 29 行**（最大簇 = 同一 session-archive 16 行，`reference_time` 各不相同——同内容反复入队反复超限）。台账 `duplicate_clusters` 段逐簇列 line_nos，records 逐条透传 `reference_time`；G4-10 重放前必须先定去重策略（89 条 budget 修根因后若逐条盲放，将把同内容写入最多 16 遍）。
1241:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2791:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1221: - **MEDIUM-2**：`duplicate_clusters` 段 + 逐条 `reference_time`（见 §6）。
1242:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2792:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1232:+- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
1243:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2793:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1234:+- **新 LOW ×3**：full_verified 长度范围修正为 131–180；台账 `class_distribution`/`recoverability_distribution` 补零并新增 `inline_state_distribution`（固定 schema，消费者无需补齐缺席键）；`line_count` 改用 `splitlines()` 与 records 同口径（原 `count("\n")` 在 bare CR / U+2028 下会与 records 数不一致）。
1257:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2807:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1932:80:台账逐条携带复合键 `{line_no, sha256_prefix(16 hex), request_id}`。**语义（Codex round-1 LOW-2 修正）**：这是**冻结快照内的 occurrence key**，不是跨文件重排或语义幂等键——台账头部 `dlq_file.sha256`（`3b37460f4215f6ac…`）即快照指纹，`line_no` 在该快照内已单列唯一；`sha256_prefix`（本快照 69 个唯一值，qa_highlight 家族实测同名同 sha 多条）与 `request_id`（仅 25 个唯一值，进程内 contextvars、重启可复用）是**冗余对账/诊断维度**，不是唯一性的必要条件。G4-10 消费前先 diff 头部 sha 即知 DLQ 是否长了新条目；语义级去重不得按本键，须按 `duplicate_clusters` 段（见下）。**语义重复簇（MEDIUM-2 整改）**：按 `{name, episode_body_sha256, group_id}` 聚簇，**6 簇覆盖 29 行**（最大簇 = 同一 session-archive 16 行，`reference_time` 各不相同——同内容反复入队反复超限）。台账 `duplicate_clusters` 段逐簇列 line_nos，records 逐条透传 `reference_time`；G4-10 重放前必须先定去重策略（89 条 budget 修根因后若逐条盲放，将把同内容写入最多 16 遍）。
1258:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2808:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1941:106:- **MEDIUM-2**：`duplicate_clusters` 段 + 逐条 `reference_time`（见 §6）。
1260:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2810:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:1948:119:- **新 LOW ×3**：full_verified 长度范围修正为 131–180；台账 `class_distribution`/`recoverability_distribution` 补零并新增 `inline_state_distribution`（固定 schema，消费者无需补齐缺席键）；`line_count` 改用 `splitlines()` 与 records 同口径（原 `count("\n")` 在 bare CR / U+2028 下会与 records 数不一致）。
1265:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2815:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
1266:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2816:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2144:     8	| BLOCKER-2 | **CLOSED** | [`snapshot_file()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:174)仅一次 `read_bytes()`；SHA、LF line_count、records 都从该 `raw_bytes` 派生，最终 header/records 引用同一快照。round-1 的跨时刻混合已消失。 |
1268:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2818:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2148:    12	| HIGH-3 | **NOT-CLOSED** | 不存在根目录已 exit 2；递归唯一命中、多命中冲突、目录伪命中也通过。但“不可见”仍未闭合：存在但 `chmod 000` 的根会 exit 0 并假判 `unrecoverable`。此外 [`glob + os.path.isfile`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:134)跟随 symlink：根内 `.jsonl` symlink 指向根外 `.txt`、以及 symlink 目录逃逸到根外树，均被判唯一来源并进入 `approximate`。 |
1269:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2819:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2150:    14	| MEDIUM-2 | **CLOSED** | [报告 §6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:78)、[ledger duplicate_clusters](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:60)及逐条 `reference_time` 已落地；6 簇全部逐行对账。 |
1279:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2829:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2636:backend/scripts/census_dead_letter_episodes.py:92:    declared_sha = rec.get("episode_body_sha256", "")
1291:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2841:_bmad-output/审查/codex-review-CARD-G4-9.md:15:   [脚本:163](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:163) 接受任意输出路径，[脚本:281](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:281) 以 `"w"` 无条件截断，未做审查目录 allowlist、`samefile`、symlink 或数据目录隔离。
1299:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2849:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:49:- **MEDIUM-1~3**：episode_body_full 采信通路 / duplicate_clusters 6 簇 29 行 + reference_time 透传 / privacy 字段与 private-only 声明。
1300:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2850:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:61:- **3 新 LOW**：full_verified 长度范围修正 131–180；台账三个 distribution 补零并新增 `inline_state_distribution`；`line_count` 与 records 改用同一 `splitlines()` 口径。
1301:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2851:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:67:- `backend/scripts/census_dead_letter_episodes.py` — 唯一代码产物（只读 census 脚本，纯 stdlib）
1307:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2923:    "recoverability_branch": "unrecoverable"
1308:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2928:    "recoverability_branch": "byte_exact"
1315:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:3110:67ccebe1 docs(census): G4-9 DLQ真实挂载census分诊 92条台账+挂载真相+三态裁定 [BATCH-2026-08-28-第五批 / CARD-G4-9]
1319:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:3514:| LOW：distribution 零键 | **CLOSED** | [固定 schema 生成链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:437)与 [ledger](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:43)均包含 `unexpected/anomaly/unrecoverable: 0`，并新增 inline 三态。 |
1321:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:3534:所以：**冻结的 92 条 ledger 数值可采信；CARD-G4-9 生成器与整卡验收仍被 BLOCKER-1、HIGH-3 阻断。** 本轮未修改仓库或受审数据，未执行破坏性 fixture/G4-10 重放；Graphiti 工具本轮不可用。
1323:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:3547:| LOW：distribution 零键 | **CLOSED** | [固定 schema 生成链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:437)与 [ledger](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:43)均包含 `unexpected/anomaly/unrecoverable: 0`，并新增 inline 三态。 |
1325:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:3567:所以：**冻结的 92 条 ledger 数值可采信；CARD-G4-9 生成器与整卡验收仍被 BLOCKER-1、HIGH-3 阻断。** 本轮未修改仓库或受审数据，未执行破坏性 fixture/G4-10 重放；Graphiti 工具本轮不可用。
1329:./_bmad-output/审查/codex-review-CARD-G4-9.md:61:   真实入口只读复现：对当前 92 行传不存在的 transcripts 根，脚本退出 0 并输出 `byte_exact=4 / unrecoverable=88`。这会误导 G4-10 放弃仍可能存在的来源。
1330:./_bmad-output/审查/codex-review-CARD-G4-9.md:67:   `DeadLetterStore` 可保存 full body（[episode_worker.py:252](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/app/services/episode_worker.py:252)），但脚本完全不读取该字段。含可验证 full body、但无 transcript 的记录仍会被判 `unrecoverable`。当前 92 条该字段确为 0，因此不改变本次数字。
1332:./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:14:CARD-G4-9 round-6 复审（静态审阅 + 只读复算，禁改任何文件）。你 round-5 裁定 3/8 CLOSED，提出 2 BLOCKER / 2 HIGH / 2 MEDIUM / 3 LOW，并明确该阻断与只读 census 卡范围相称（因报告/UAT 承诺纯只读零写入，残留反例能截断或修改本卡正在保护的恢复源）——开发方接受该论证并以 commit 4c125f19 提交整改。请逐条只读复核：
1333:./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:15:1. BLOCKER token 冲突/无 token 扫描前早退 → resolve_group_attribution 重写为先扫描后判定：无条件对每个 token 遍历收集候选进 all_candidate_paths（保护集口径），再做 no_token/token_conflict/scan_errors/stat_failures/unreadable/多命中判定；候选 stat 失败改 exit 2。
1335:./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:20:6. MEDIUM 无 token 判不可恢复 → 改 unverifiable + no_token 标记。

**Focusing on last 200 log lines**
exec
/bin/zsh -lc 'tail -260 _bmad-output/审查/codex-review-CARD-G4-9-round7.md' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
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



**Assessing round7 QA DB blockers closure**
**Identifying discrepancies in round7 blocker summaries**
**Highlighting unresolved QA DB issues from round7**
**Reevaluating QA issue severity and evidence validity**
**Analyzing SQLite URI path parsing and mode effects**
**Inspecting ledger file structure and hidden files**
**Planning ledger metadata inspection without cache**
**Implementing Python no-cache JSON parsing**
codex
初步静态阅读已发现一个必须单独核对的边界：`O_EXCL` 确实让“预置同名 symlink”变成拒绝服务而非跟随写入，但它只保护 `open(tmp)` 这一刻；后续 `os.replace(tmp_path, out_path)` 仍重新按路径解析源、目标，且目前不在异常清理区。接下来我会把“既有源不被截断”和“发布对象/落点未被换链”分开裁定，避免把两种性质混为一谈。
exec
/bin/zsh -lc "jq '{dlq_file,total_lines,total_records,unparseable_lines,class_distribution,recoverability_distribution,inline_state_distribution,unrecoverable_list,unverifiable_list,attribution_conflicts,duplicate_clusters,qa_metrics_probe}' '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json'
stat -f 'ledger_mode=%Lp ledger_size=%z ledger_inode=%d:%i' '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json'
shasum -a 256 backend/data/dead_letter_episodes.jsonl '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' backend/scripts/census_dead_letter_episodes.py
rg --files --hidden -g '.*.census-tmp-*' -g '*.census-tmp-*' -g '"'!node_modules'"' -g '"'!.git'"' .
git ls-tree -l HEAD -- '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' backend/data/dead_letter_episodes.jsonl backend/scripts/census_dead_letter_episodes.py
git rev-parse f389980c:backend/scripts/census_dead_letter_episodes.py HEAD:backend/scripts/census_dead_letter_episodes.py f389980c:'_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' HEAD:'_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 13ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
6f264b74fcefe608311895e25f059d7fc34305ea
6f264b74fcefe608311895e25f059d7fc34305ea
9937a25c7af4d2b57dbb4593a50c4ae92189419d
9937a25c7af4d2b57dbb4593a50c4ae92189419d

**Verifying cross-worktree file access**
**Planning ledger metadata verification**
**Assessing ledger file permission discrepancy**
exec
/bin/zsh -lc "rg -n \"只读|零写|read.?only|O_EXCL|atomic|原子|0600|tmp|surrogate|ftruncate|round-7|round-8|f389980c|92|89/2/1|4/88\" '_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md' '_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md' '_bmad-output/审查/G4-9-evidence/grep-selfattest.txt' '_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt'
nl -ba '_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md' | sed -n '1,180p'
nl -ba '_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md' | sed -n '1,250p'
nl -ba '_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt' | sed -n '1,80p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt:15:f389980c  CARD-G4-9 round-7 架构级修复（消除截断动作；本 receipt 当前版所描述的 commit）
_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:1:== CARD-G4-9 只读自证（round-7 整改版）==
_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:3:生成时点: round-7 整改后（随每轮整改重生成）
_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:24:--- (4) ⛔ 无任何截断调用（round-7 架构整改：从不截断既有文件）:
_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:25:grep "os.ftruncate|.truncate(" 命中: 0 ✓（'ftruncate' 字样仅出现在说明注释中，非调用）
_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:26:--- (5) 唯一写出口 = O_EXCL 新建临时文件 → fsync → os.replace 原子替换:
_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:27:779:        # round-7 架构整改: 不再截断既有文件 —— 同目录 O_EXCL 新建临时文件 →
_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:28:780:        # 写 → fsync → os.replace 原子替换。O_EXCL 保证目标是本进程新建的对象，
_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:29:785:        tmp_path = out_path.with_name(f".{out_path.name}.census-tmp-{os.getpid()}")
_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:30:787:            tmp_fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:31:789:            print(f"临时台账文件无法新建（O_EXCL）: {tmp_path} ({e})", file=sys.stderr)
_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:32:795:                os.fsync(tmp_fd)
_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:33:804:        os.replace(tmp_path, out_path)
_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:39:460:        # round-7 BLOCKER 整改: 用 **inode 身份逐级比较**（_path_is_within），
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:6:scope: "BATCH-2026-08-28-第五批 / CARD-G4-9 — live DLQ 92 条只读 census：分类/SHA 对账/可恢复性三态/挂载真相，产出 G4-10 交接台账"
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:13:> 这张卡**没有修任何东西，也没有恢复任何数据**——它是一次"清点尸体"的只读普查：
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:14:> 线上 Graphiti 写入失败后落进死信文件的 92 条记录，逐条查清"是什么死的、还能不能救、去哪里救"，
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:19:1. **92 条死信全部查清、零"待定"**：89 条是"内容太长超过本地模型 16384 token 上限"（未修，根因归 G4-10）；2 条是 5 月 14 日的 schema 冲突、1 条是旧 group_id 冒号格式——这 3 条的根因**当天之后就已修复**，不会再新增。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:27:| 全程零写入（裁判判据 e） | 运行前后 四份 DLQ 文件 + qa_metrics.db 的 sha256 **逐字节不变**（diff 为空 → PASS） | `_bmad-output/审查/G4-9-evidence/shasums-before.txt` / `shasums-after.txt` |
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:28:| 脚本只读自证（判据 a） | import 行全 stdlib；neo4j/graphiti/bolt/app. import **0 命中**；`--apply` 定义 **0 命中**；写模式 open 仅台账 `--out` 1 处 | `G4-9-evidence/grep-selfattest.txt` |
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:29:| live 挂载真相（判据 c） | 容器内 `sha256sum /app/data/dead_letter_episodes.jsonl` = 宿主 live 地址同值（92 行，`3b37460f…`）；compose :206-212 遮蔽史入报告 §1 | `G4-9-evidence/container-sha-check.txt` + 报告 §1 |
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:31:| inline 完整性 + SHA 对账（判据 b） | 92/92 重算 sha256 对账：4 条 full_verified、88 条 truncated_prefix（`to_dict()` 的 `[:200]` 截断，`episode_worker.py:107`）、**0 条 anomaly** | 台账 JSON 逐条 `inline_state`/`sha_check` |
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:32:| 源指针核销（判据 b，qa_metrics.db 只读 mode=ro） | `qa_error_logs` **0 行** → 0/92 可经 qa_metrics.db 溯源（诚实记录）；附加核销：llm_call_logs.db 无正文、outbox 空、episode_body_full 0 条；**有效源指针 = request_id 组内 session 归因 → 7 个 transcript 全部在盘实测存在** | 报告 §4 + 台账 `qa_metrics_probe` |
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:34:| G4-10 稳定键（判据 d） | 逐条复合键 `{line_no, sha256_prefix, request_id}` + 台账头部冻结文件 sha；request_id 92 条仅 25 唯一值的实测证明单列不可作键 | 报告 §6 + 台账 `records[].stable_key` |
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:35:| Codex 独立审查 round-1 | **BLOCKED**（3 BLOCKER：--out 可截断输入 / 快照不原子 / 交付物未冻结；3 HIGH：inline 判定 fail-open / request_id 归因传染 / transcript 归因折叠；3 MEDIUM + 4 LOW。同时确认：**当前 92 条数字逐项 0 mismatch**、class/三态/家族计数全对） | `_bmad-output/审查/codex-review-CARD-G4-9.md` |
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:37:| Codex 复审 round-2 | **仍阻断**（10/13 CLOSED；BLOCKER-1/HIGH-1/HIGH-3 未真正闭合 + 3 新 LOW）。同时独立复算确认：67ccebe1 冻结生效、92 条数字与 6/29 重复簇全部可复算 | `_bmad-output/审查/codex-review-CARD-G4-9-round2.md`（codex 被 cyber 误拦，内容由 stdout 抢救存档） |
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:46:| round-6 findings 整改 | **架构级修复 + 6 项**：新增不依赖枚举的**路径层防御**（--out 禁落 transcripts 根内 / 禁等于任一输入 realpath）、QA DB 验证 fd 保持打开至复核完毕、no_token 亦扫描、证据包重生成、ledger 冲突原因自描述、lone surrogate 回退。反例实测：0333 隐藏目录内 transcript 作 --out → exit 2 完好 | 报告 §7g |
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:47:| Codex 复审 round-7 | **关键裁定分离**："92 条冻结 ledger **可以采信**；生成器与 UAT 的纯只读安全声明不可验收"——卡面 census 判据已满足，阻断全在工具安全承诺侧。1 BLOCKER（大小写别名根，无需竞态）+ 4 项路径 TOCTOU + 1 MEDIUM（非原子写）+ 2 LOW | `_bmad-output/审查/codex-review-CARD-G4-9-round7.md` |
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:48:| round-7 findings 整改 | **架构级第二次修复**：写出改 O_EXCL 临时文件+fsync+os.replace（**全文再无 ftruncate 调用**），五项绕过整类失效；containment 改 inode 逐级比较（normcase 在 POSIX 是恒等函数，我的假设错了）；扫描受阻直接拒绝写出。实测：根外 hardlink 指向根内 transcript 作 --out → 源内容完好 | 报告 §7h |
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:49:| 独立 Workflow 4-agent 复核 | G4-9 数字 agent：92 条重算 **0 mismatch**（class/inline/三态/25 request_id/7 transcript 在盘/台账 sha 全 CONFIRMED，仅 2 处描述区间 REFUTED 已修正）；只读契约 agent：与 Codex 同源的 3 条 blocker（已随上整改） | Workflow wf_737b1a95-20b journal |
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:54:- **BLOCKER-2 快照不原子**：records 与头部 sha 来自两次读取。整改：单次 read_bytes()，头部与逐条同源同字节。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:62:整改后全量重跑：92 条数字与整改前**逐项一致**（4/88/0、89/2/1、冲突 0、unparseable 0）——整改只收紧契约与通用鲁棒性，不改变本次 census 结论。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:73:round-2 整改后再次全量重跑：92 条、4/88/0、89/2/1、6 簇 29 行、shasum 不变——**数字全程未变**。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:79:- **BLOCKER-1 仍 PARTIAL**：① 保护集漏了**归因到的 transcript**——`--out` 指向它会截断恢复源；② check-then-open 的 **TOCTOU** 仍在。→ ① transcript 写前并入保护集；② 改 `O_NOFOLLOW` 打开且**不带 O_TRUNC**，对实际 fd `fstat` 校验后才 `ftruncate`。反例实测：exit 2、transcript 完好。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:84:round-3 整改后第三次全量重跑：**92 条、4/88/0、89/2/1、6/29、shasum 不变——三轮整改数字全程未变**，改的全是通用鲁棒性与路径安全。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:95:round-4 整改后第四次全量重跑：**92 条、4/88/0（unverifiable 0）、89/2/1、6/29、shasum 不变——四轮整改数字全程未变**。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:104:- **`fchmod` 排在碰撞检查之前**：`--out` 指向受保护的只读输入时，会先把它的权限从 644 改成 600 才发现碰撞——字节没丢但输入被改了。→ 碰撞检查前移。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:105:- **其余 5 项**：QA DB 特殊文件门、无 token 归 `unverifiable`、单独换行算 1 空行、strict encode 堵住 lone surrogate 伪造 `full_verified`、`bool` 不再通过长度门。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:107:**一处计数如实变化**：归因冲突 0→3。因为"名字不含 session token"现在被诚实标为"未做归因扫描"，正是那 3 条 callout 记录；它们 inline 全量、不依赖 transcript，仍是可字节级恢复。**三态分布不变**（4/88/0/0）——是标注变诚实，不是结论变化。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:109:round-5 整改后第五次全量重跑：**92 条、4/88/0/0、89/2/1、6/29、shasum 不变——五轮整改数字全程未变**。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:119:round-6 整改后第六次全量重跑：**92 条、4/88/0/0、89/2/1、6/29、shasum 不变——六轮整改数字全程未变**。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:121:## 🔧 Codex round-7 复审整改记录（关键裁定分离 + 架构级第二次修复）
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:123:round-7 把结论分成了两半，这个区分很重要：
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:125:> **「现有 92 条冻结 ledger 可以采信；生成器与 UAT 的纯只读安全声明不可验收。」**
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:127:也就是说：这张卡要交付的 census 结论（92 条的分类、对账、三态、挂载真相、稳定键、运行零写入）**已经过关**；卡住的是"这个脚本作为工具，其只读承诺是否经得起敌意输入"。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:130:- **五项绕过共用一个根源**：它们都依附于"截断一个已存在的文件"这个动作。改成「新建临时文件 → 写 → fsync → 原子替换」后，脚本**全文再没有任何截断调用**，这一整类绕过连同"崩溃留下半个台账"的风险一起消失。实测：拿一个指向恢复源的 hardlink 当 `--out`，台账正常写出，而**源文件内容一个字节没变**。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:133:round-7 整改后第七次全量重跑：**92 条、4/88/0/0、89/2/1、6/29、shasum 不变、台账 0600、无临时文件残留——七轮整改数字全程未变**。
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:137:- `backend/scripts/census_dead_letter_episodes.py` — 唯一代码产物（只读 census 脚本，纯 stdlib）
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:139:- `_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json` — 92 条逐条台账（G4-10 消费）
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:4:> **性质**: 纯只读 census。0 写入、0 重放、0 业务代码改动。唯一代码产物 = `backend/scripts/census_dead_letter_episodes.py`。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:6:> **台账**: `_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json`（92 条逐条，G4-10 消费）
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:18:→ 3b37460f4215f6ac...ef3ba590（92 行）— 与宿主 live 地址逐字节一致
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:23:| **live**（权威） | `…/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl` | **92** | `3b37460f4215f6ac` | 2026-08-11 22:01 (+0800) | 容器 `/app/data` 经 `./backend:/app` 挂载即此文件；census 对象 |
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:28:**compose :206-212 遮蔽史**（本 worktree `docker-compose.yml:206-212`，与 live worktree 同文）：`- ./data:/app/data` 是嵌套 bind，被 `./backend:/app` 父挂载遮蔽——`docker inspect` 记录了它，但容器 `/proc/self/mountinfo` 从不出现，**实际生效的一直是 `backend/data/`**。R11-BATCH2（2026-08-17）已删除该行，理由是遮蔽与否取决于挂载顺序、一次 recreate 就可能翻转，届时 92 行死信会被 1 行的孤儿①覆盖不可见。删除后 `/app/data` 恒等于 `backend/data/`。**证据边界（诚实声明）**：本卡独立实证的是**现状**（容器内 sha 与宿主 live 地址同源、当前 compose 无子挂载行）；"历史上子挂载从未在容器内生效"沿引 compose 注释史与 R11-BATCH2（2026-08-17）当时的 mountinfo 实测记录，本卡未重跑历史 `docker inspect` 独立复证。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:34:92 条，分类与勘探预期**零偏差**：
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:47:`DeadLetterStore.store()` 落盘的 `episode_body` 来自 `EpisodeTask.to_dict()`，后者做 `episode_body[:200]` 截断（`episode_worker.py:107`，"truncate for logging"）；全量正文只有 `DEAD_LETTER_STORE_FULL_BODY` 开启时以 `episode_body_full` 另存——**live 容器该 env 未设置（实测），92 条 `episode_body_full` 均缺席**。逐条重算 sha256(inline) 对账 `episode_body_sha256` 结果：
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:57:## §4 源指针核销（qa_metrics.db，只读 mode=ro）
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:59:- **qa_metrics.db**（live `backend/data/qa_metrics.db`，经 sqlite URI `mode=ro` 打开）：唯一表 `qa_error_logs`（列 category/error_type/source_module/stack_summary/created_at，**无 request_id 列**），**行数 = 0**。按三个 error_type 探查命中均 0。**核销裁定：`no_source_rows` —— qa_metrics.db 对 92 条死信不构成任何源指针，0/92 可经其溯源。**
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:62:  - `backend/data/outbox/`：**空目录**（A7 outbox 只接 enqueue 失败，本 92 条全部是 enqueue 成功、处理失败，不经 outbox）；
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:75:**不可恢复清单（显式成段）**：本次 census 裁定不可恢复条目 **0 条**；三态裁定覆盖 92/92，**"待定"0 条**。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:93:| 容器内 sha 实测 | 92 行、sha 与宿主 live 地址一致（`container-sha-check.txt`） |
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:94:| class 偏差 | 无（89/2/1 与勘探预期一致，脚本 `class_deviation` 字段为空） |
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:101:- **BLOCKER-2（快照不原子）**：DLQ 单次 `read_bytes()`，头部 sha256/line_count 与逐条 records 派生自同一份内存字节；mtime 显式标注为 stat 参考值。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:104:- **HIGH-2（request_id fail-open）**：分组键改 `(类型名, 值)`；缺失/None 按 line_no 单条成组零传染；组内多 token 前缀一致门，冲突记 `attribution_conflict` 拒绝采信（现网 92 条 0 冲突）。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:111:整改后全量重跑：**92 条数字与整改前逐项一致**（class 89/2/1、三态 4/88/0、归因冲突 0、unparseable 0），重复簇 6/29 行与 Codex 独立复算吻合。另有独立 Workflow 4-agent 复核（92 条重算 0 mismatch、7 transcript 在盘实测、台账 sha 一致）交叉确认。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:122:round-2 整改后再次全量重跑：92 条、class 89/2/1、三态 4/88/0、重复簇 6/29、shasum 不变——**数字仍逐项一致**，整改只收紧通用鲁棒性。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:143:- **BLOCKER-1 残留两条绕过**：① `protected_paths` 未含**归因到的 transcript**，`--out=<唯一 transcript>` 会截断恢复源；② check-then-open 的 **TOCTOU** 仍在（检查后、打开前把 --out 换成指向 DLQ 的链接）。**整改**：① 写出前把全部 `transcript_paths` 并入保护集；② 改 `os.open(O_WRONLY|O_CREAT|O_NOFOLLOW)` **不带 O_TRUNC** 打开 → 对**实际 fd** `fstat` 校验 inode → 通过才 `ftruncate`，检查与写入作用于同一 fd，替换攻击无效。反例实测：`--out` 指向唯一 transcript → exit 2、transcript sha 不变。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:149:round-3 整改后第三次全量重跑：92 条、class 89/2/1、三态 4/88/0、重复簇 6/29、shasum 不变——**三轮整改数字全程未变**，改的全是通用鲁棒性与路径安全。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:163:round-4 整改后第四次全量重跑：**92 条、class 89/2/1、三态 4/88/0（unverifiable 0）、重复簇 6/29、shasum 不变——四轮整改数字全程未变**。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:172:- **HIGH②（`fchmod` 先于 protected-id 检查）**：`--out` 指向受保护的 0644 输入时，会**先把只读输入权限改成 0600** 再拒绝——字节没截断但输入已被修改。**整改**：碰撞检查前移到 `fchmod` 之前。实测：mode 644 → 644 不变。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:175:- **LOW ×3**：单独 `b"\n"` 现算 1 个空行（实测 `line_count=1`）；`errors="replace"` 改 **strict encode**（JSON escaped lone surrogate 不能再构造假 `full_verified`）；`bool` 是 `int` 子类 —— `episode_body_length=True` 现被长度门拒绝（实测判 anomaly）。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:177:**归因冲突计数由 0 变为 3（如实说明）**：round-5 起"名字不含 session token"被诚实标记为 `no_token`（未做归因扫描），命中的正是 3 条 `callout_annotation` 记录。它们 inline 正文全量、sha 对账通过，**不依赖 transcript**，故仍判 `byte_exact`——三态分布不变（4/88/0/0），88 条 approximate 仍全部为唯一 transcript 命中。这是标注口径变诚实，不是结论变化。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:179:round-5 整改后第五次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变——五轮整改数字全程未变**。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:191:- **LOW ×3**：ledger 新增 `attribution_conflict_reason` 自描述（本次 92 条：`no_token` 3 / 其余 89 无冲突）；`json.dumps` 对 lone surrogate 回退 `ensure_ascii=True` 并显式标注，不再整次 census 拒绝；`stat_failures` 分支保留（Codex 确认非额外绕过，仅基本不可达）。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:193:round-6 整改后第六次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变——六轮整改数字全程未变**。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:195:## §7h Codex round-7 复审整改记录（关键裁定分离 + 架构级第二次修复）
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:197:round-7 给出了本卡最重要的一次裁定分离：
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:199:> **「现有 92 条冻结 ledger 可以采信；CARD-G4-9 生成器与 UAT 的纯只读安全声明不可验收。」**
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:201:即：卡面的 census 判据（分类/对账/三态/挂载真相/稳定键/shasum 不变）已满足且被独立复算确认；阻断项全部落在"生成器作为工具的只读安全承诺"上。逐条整改：
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:204:- **NOT-CLOSED ×4（根外 hardlink 指向隐藏目录内 transcript / 根 retarget TOCTOU / 检查后换父目录 symlink 或 basename hardlink）+ MEDIUM（非原子写）**：这五项依附于同一个动作——**截断一个已存在的文件**。**架构级修复**：写出改为「同目录 `O_EXCL` 新建临时文件 → 写 → `fsync` → `os.replace` 原子替换」，**全文再无任何 `ftruncate` 调用**。`O_EXCL` 保证写入目标是本进程新建的对象，因此"把 `--out` 换成指向恢复源的 hardlink / 父目录 symlink / 大小写别名"整类绕过失效；`os.replace` 同时消除崩溃/ENOSPC 留下部分台账的风险。实测：根外 hardlink 指向根内 transcript 作 `--out` → 台账正常写出而**源文件内容完好**（`os.replace` 只重绑定该名字，不触碰底层 inode）。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:206:- **LOW（lone surrogate 回退失效）**：异常发生在后续 `write`，不在原 `try` 内。**整改**：`json.dumps` 后立即 `.encode("utf-8")` 探测，编码错误在写出前暴露并回退 `ensure_ascii=True`。
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:209:round-7 整改后第七次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变、台账 mode 0600、无临时文件残留——七轮整改数字全程未变**。
     1	---
     2	type: uat
     3	title: "UAT · CARD-G4-9 DLQ 真实挂载 census 分诊（2026-08-28）"
     4	date: 2026-08-28
     5	status: awaiting_user
     6	scope: "BATCH-2026-08-28-第五批 / CARD-G4-9 — live DLQ 92 条只读 census：分类/SHA 对账/可恢复性三态/挂载真相，产出 G4-10 交接台账"
     7	worktree: "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census"
     8	---
     9	
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
    36	| Codex findings 逐条整改 | **13/13 完成**（见下）；整改版脚本负例门全过；全量重跑数字与整改前逐项一致 | 报告 §7/§7b + 证据包 |
    37	| Codex 复审 round-2 | **仍阻断**（10/13 CLOSED；BLOCKER-1/HIGH-1/HIGH-3 未真正闭合 + 3 新 LOW）。同时独立复算确认：67ccebe1 冻结生效、92 条数字与 6/29 重复簇全部可复算 | `_bmad-output/审查/codex-review-CARD-G4-9-round2.md`（codex 被 cyber 误拦，内容由 stdout 抢救存档） |
    38	| round-2 findings 逐条整改 | **6/6 完成**：inode 身份守卫封 hardlink+大小写别名 / full_body 长度门+anomaly 前置 / 不可读根 exit 2+symlink 逃逸拒采信 / 3 新 LOW。5 条新负例实测全过、正例无回归、数字仍逐项一致 | 报告 §7/§7c + `grep-selfattest.txt` |
    39	| Codex 复审 round-3 | **仍阻断**（4/6 CLOSED；BLOCKER-1/HIGH-3 判 PARTIAL + 1 新 MEDIUM + 2 新 LOW）。同时确认：HIGH-1 与三条 LOW 已闭合、台账数字有效且与 commit 字节一致 | `_bmad-output/审查/codex-review-CARD-G4-9-round3.md` |
    40	| round-3 findings 逐条整改 | **6/6 完成**：transcript 并入保护集 / O_NOFOLLOW+fstat 消 TOCTOU / os.walk 替 glob（不跟随目录 symlink+遍历错误显式捕获）/ 不可读候选 fail-closed / JSONL 严格 LF 分帧 / 非 dict 归 unparseable。6 条新反例实测全过、数字第三次不变 | 报告 §7d + `grep-selfattest.txt` |
    41	| Codex 复审 round-4 | **仍阻断**（1/6 CLOSED；2 新 BLOCKER + 1 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round4.md` |
    42	| round-4 findings 逐条整改 | **9/9 完成**：全候选入保护集 / 读侧 fd 身份消源侧 TOCTOU / 新增 unverifiable 第四态 / FIFO 设备门 / strict UTF-8 / 3 条错型与边界 LOW / provenance receipt。5 条新反例实测全过；第四次全量重跑数字仍不变 | 报告 §7e + `grep-selfattest.txt` |
    43	| Codex 复审 round-5 | **仍阻断**（3/8 CLOSED；2 BLOCKER + 2 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round5.md` |
    44	| round-5 findings 逐条整改 | **9/9 完成**：先扫描后判定（冲突候选亦入保护集）/ QA DB fd 身份+复核 / 可见性优先于 anomaly / fchmod 后置于碰撞检查 / QA DB 特殊文件门 / no_token 归 unverifiable / 3 条 LOW。6 条新反例实测全过；第五次全量重跑数字仍不变 | 报告 §7f |
    45	| Codex 复审 round-6 | **6/9 CLOSED**（visibility 优先/fchmod 顺序/no_token 语义/3 条 LOW 已闭合）；剩 2 BLOCKER + 1 MEDIUM 揭示保护集**依赖枚举完整性**的架构缺陷 + 3 新发现 | `_bmad-output/审查/codex-review-CARD-G4-9-round6.md` |
    46	| round-6 findings 整改 | **架构级修复 + 6 项**：新增不依赖枚举的**路径层防御**（--out 禁落 transcripts 根内 / 禁等于任一输入 realpath）、QA DB 验证 fd 保持打开至复核完毕、no_token 亦扫描、证据包重生成、ledger 冲突原因自描述、lone surrogate 回退。反例实测：0333 隐藏目录内 transcript 作 --out → exit 2 完好 | 报告 §7g |
    47	| Codex 复审 round-7 | **关键裁定分离**："92 条冻结 ledger **可以采信**；生成器与 UAT 的纯只读安全声明不可验收"——卡面 census 判据已满足，阻断全在工具安全承诺侧。1 BLOCKER（大小写别名根，无需竞态）+ 4 项路径 TOCTOU + 1 MEDIUM（非原子写）+ 2 LOW | `_bmad-output/审查/codex-review-CARD-G4-9-round7.md` |
    48	| round-7 findings 整改 | **架构级第二次修复**：写出改 O_EXCL 临时文件+fsync+os.replace（**全文再无 ftruncate 调用**），五项绕过整类失效；containment 改 inode 逐级比较（normcase 在 POSIX 是恒等函数，我的假设错了）；扫描受阻直接拒绝写出。实测：根外 hardlink 指向根内 transcript 作 --out → 源内容完好 | 报告 §7h |
    49	| 独立 Workflow 4-agent 复核 | G4-9 数字 agent：92 条重算 **0 mismatch**（class/inline/三态/25 request_id/7 transcript 在盘/台账 sha 全 CONFIRMED，仅 2 处描述区间 REFUTED 已修正）；只读契约 agent：与 Codex 同源的 3 条 blocker（已随上整改） | Workflow wf_737b1a95-20b journal |
    50	
    51	## 🔧 Codex round-1 整改记录（13/13 关闭，BLOCKED → 整改完毕）
    52	
    53	- **BLOCKER-1 --out 截断风险**：任意 --out 路径 "w" 无守卫，可覆盖 DLQ 自身（双审查独立实测复现）。整改：写前 resolve() 路径碰撞守卫，命中输入集合即 exit 2；负例实测拒绝、DLQ 完好。
    54	- **BLOCKER-2 快照不原子**：records 与头部 sha 来自两次读取。整改：单次 read_bytes()，头部与逐条同源同字节。
    55	- **BLOCKER-3 交付物漂移**：审查期间脚本/报告 sha 变化且未 track。整改：本卡 commit 冻结全部 exact bytes；自证文件内嵌脚本 sha 前缀。
    56	- **HIGH-1 inline 判定 fail-open**：sha 匹配但长度不符会误判 full_verified（反例实测）。整改：长度精确匹配门 + 64-hex 合法性门 + anomaly 一律 fail-closed（unrecoverable + 如实 basis）。
    57	- **HIGH-2 request_id 归因传染**：缺失值合入 "None" 组、跨类型合组、多 token 静默取长。整改：(类型,值) 复合键 + 缺失单条成组 + 前缀一致门（冲突拒采信）。
    58	- **HIGH-3 transcript 归因折叠**：多命中照单全收、目录缺失误判 unrecoverable=88（实测复现）。整改：恰 1 常规文件命中门 + 递归 glob + 目录缺失 exit 2 拒诊。
    59	- **MEDIUM-1~3**：episode_body_full 采信通路 / duplicate_clusters 6 簇 29 行 + reference_time 透传 / privacy 字段与 private-only 声明。
    60	- **LOW-1~4**：两处区间修正（16948–20831、205–8036）/ 稳定键语义重写为"冻结快照 occurrence key" / schema 双处证据（LearningConcept.name + LearningTip.created_at）/ 挂载历史证据边界声明。
    61	
    62	整改后全量重跑：92 条数字与整改前**逐项一致**（4/88/0、89/2/1、冲突 0、unparseable 0）——整改只收紧契约与通用鲁棒性，不改变本次 census 结论。
    63	
    64	## 🔧 Codex round-2 复审整改记录（10/13 CLOSED → 剩 3 项 + 3 新 LOW 全关闭）
    65	
    66	round-2 用真实入口反例证明我 round-1 的三处整改**没有真正闭合**（这正是二轮审查的价值）：
    67	
    68	- **BLOCKER-1 未闭合**：守卫比的是路径字符串，**hardlink 与大小写别名照样截断 DLQ**。→ 改比**文件 inode 身份**；两种绕过实测双双 exit 2、DLQ sha 不变。
    69	- **HIGH-1 未闭合**：`episode_body_full` 分支只核 sha 不核长度且排在 anomaly 之前，**anomaly 记录能翻案成"可字节级恢复"**。→ 加长度门 + 判定顺序改为 anomaly 优先；反例实测翻转。
    70	- **HIGH-3 未闭合**：`chmod 000` 的目录仍 exit 0 并把全部记录**假判不可恢复**；symlink 可指到目录外冒充源。→ 不可读即 exit 2；symlink 与逃逸目标一律不采信；正例（真实唯一命中）无回归。
    71	- **3 新 LOW**：full_verified 长度范围修正 131–180；台账三个 distribution 补零并新增 `inline_state_distribution`；`line_count` 与 records 改用同一 `splitlines()` 口径。
    72	
    73	round-2 整改后再次全量重跑：92 条、4/88/0、89/2/1、6 簇 29 行、shasum 不变——**数字全程未变**。
    74	
    75	## 🔧 Codex round-3 复审整改记录（4/6 CLOSED → 剩 2 项 + 3 新发现全关闭）
    76	
    77	round-3 确认 HIGH-1 与三条 LOW 真正闭合、台账数字有效，又在两项路径安全上找到更深的绕过：
    78	
    79	- **BLOCKER-1 仍 PARTIAL**：① 保护集漏了**归因到的 transcript**——`--out` 指向它会截断恢复源；② check-then-open 的 **TOCTOU** 仍在。→ ① transcript 写前并入保护集；② 改 `O_NOFOLLOW` 打开且**不带 O_TRUNC**，对实际 fd `fstat` 校验后才 `ftruncate`。反例实测：exit 2、transcript 完好。
    80	- **HIGH-3 仍 PARTIAL**：Python 3.14 的 `glob` 在过滤前就已递归、跟随目录 symlink 且**静默吞掉不可读子树错误**；mode 000 的文件仍过 `isfile()` 被当可用源。→ 改 `os.walk(onerror=, followlinks=False)` + `os.access(R_OK)` 门；遍历受阻或有不可读候选一律拒绝裁定。三反例实测 fail-closed。
    81	- **新 MEDIUM（JSONL 分帧）**：`splitlines()` 会把含 U+2028 的合法单行记录劈成两条坏行。→ 严格按 LF 分帧，header 与 records 共用同一函数。
    82	- **新 LOW ×2**：非 dict JSON（`null`/数组）归 unparseable 不再炸全量；报告头补 artifact commit 链。
    83	
    84	round-3 整改后第三次全量重跑：**92 条、4/88/0、89/2/1、6/29、shasum 不变——三轮整改数字全程未变**，改的全是通用鲁棒性与路径安全。
    85	
    86	## 🔧 Codex round-4 复审整改记录（1/6 CLOSED → 9 项全关闭）
    87	
    88	round-4 只认 1 项闭合，用更深的反例推翻其余"闭合"——两条新 BLOCKER 都是真的：
    89	
    90	- **不可读但可写（mode 0200）的 transcript 绕过保护集**：我在"不可读"分支把候选路径清空了，于是它没进保护集，`--out` 指向它照样截断——不需要任何竞态。→ 新增"全候选清单"，无论可读与否一律并入保护集。
    91	- **源侧 TOCTOU**：保护身份按路径 stat 采集、DLQ 稍后才按路径读取，中间可换 inode。→ 改为**从 fd 读取**：打开一次 → `fstat` 取身份 → 从同一 fd 读全量，保护的就是实际读到的那个对象。
    92	- **把"看不见"说成"不可恢复"**：扫描受阻时仍输出 `unrecoverable`，与报告里"既不宣称不可恢复"自相矛盾。→ 新增第四态 **`unverifiable`**，逐条写明是遍历受阻还是候选不可读。
    93	- **其余 5 项**：FIFO/设备节点门（`O_NONBLOCK`+`S_ISREG`）、非法 UTF-8 不再经 replace 冒充有效记录（strict decode）、三条错型与边界 LOW（`name=None`/`request_id=[]`/根为 `/`）、既有输出文件 `fchmod` 收紧（台账现为 `-rw-------`）、provenance 改后置 receipt 绑定精确 commit 链。
    94	
    95	round-4 整改后第四次全量重跑：**92 条、4/88/0（unverifiable 0）、89/2/1、6/29、shasum 不变——四轮整改数字全程未变**。
    96	
    97	## 🔧 Codex round-5 复审整改记录（3/8 CLOSED → 9 项全关闭）
    98	
    99	round-5 继续深挖，两条新 BLOCKER 与两条 HIGH 都成立：
   100	
   101	- **冲突组的候选没进保护集**：token 冲突时我在扫描**之前**就早退了，那些候选从没被看到，`--out` 指向它们照样截断。→ 改成**先扫描后判定**，无论最终是否采信，见到的候选一律进保护集。
   102	- **qa_metrics.db 身份没绑定实际读取**：先按路径 stat、SQLite 稍后按路径重开，中间可换。→ 改 fd 取身份 + 打开后复核身份一致。
   103	- **anomaly 吞掉了"看不见"**：`anomaly→unrecoverable` 排在可见性判断之前，扫描受阻时仍断言"不可恢复"。→ 判定链改为**可见性优先**。
   104	- **`fchmod` 排在碰撞检查之前**：`--out` 指向受保护的只读输入时，会先把它的权限从 644 改成 600 才发现碰撞——字节没丢但输入被改了。→ 碰撞检查前移。
   105	- **其余 5 项**：QA DB 特殊文件门、无 token 归 `unverifiable`、单独换行算 1 空行、strict encode 堵住 lone surrogate 伪造 `full_verified`、`bool` 不再通过长度门。
   106	
   107	**一处计数如实变化**：归因冲突 0→3。因为"名字不含 session token"现在被诚实标为"未做归因扫描"，正是那 3 条 callout 记录；它们 inline 全量、不依赖 transcript，仍是可字节级恢复。**三态分布不变**（4/88/0/0）——是标注变诚实，不是结论变化。
   108	
   109	round-5 整改后第五次全量重跑：**92 条、4/88/0/0、89/2/1、6/29、shasum 不变——五轮整改数字全程未变**。
   110	
   111	## 🔧 Codex round-6 复审整改记录（6/9 CLOSED → 架构级修复）
   112	
   113	round-6 指出了一个我补丁修不掉的根因：**保护集依赖"能不能枚举到"**。不可列举但可穿越的目录（`0333`）里的 transcript，`os.walk` 看不见，就进不了保护集，`--out` 指向它照样截断；QA DB 的 inode 被 A→B→A 换过也一样。
   114	
   115	→ 改为**双层防御**：在 inode 保护集之外，加一层**不依赖枚举**的路径判断——`--out` 的真实路径不得落在 transcripts 根目录内（整个恢复源区域禁写），也不得等于任何输入文件的真实路径。实测：隐藏目录内的 transcript 作 `--out`，inode 保护集根本没看见它，路径层直接拦住，exit 2、文件完好。
   116	
   117	另修：QA DB 的验证 fd 改为**保持打开**到复核完毕（堵 ABA）；`no_token` 分支也扫描（原本完全不扫，候选进不了保护集）；证据包每轮重生成（round-6 指出我的 self-attest 停留在 round-4 的旧 SHA，属实）；台账新增冲突原因自描述。
   118	
   119	round-6 整改后第六次全量重跑：**92 条、4/88/0/0、89/2/1、6/29、shasum 不变——六轮整改数字全程未变**。
   120	
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
   137	- `backend/scripts/census_dead_letter_episodes.py` — 唯一代码产物（只读 census 脚本，纯 stdlib）
   138	- `_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md` — census 报告（挂载真相/分类/三态/交接契约）
   139	- `_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json` — 92 条逐条台账（G4-10 消费）
   140	- `_bmad-output/审查/G4-9-evidence/` — 证据包（shasums ×2、grep 自证、容器 sha 实测、运行日志）
   141	- `_bmad-output/审查/codex-review-CARD-G4-9.md` — Codex 独立审查存档
   142	
   143	## ⏭️ 移交（不在本卡范围）
   144	
   145	- **G4-10**：89 条 budget_400 根因修复（16384 context 超限 → 切块或提 budget）+ 按台账重放；3 条 `vault:default` 旧格式重放前需 group 重映射。
   146	- **DeadLetterStore 全量正文开关**：`DEAD_LETTER_STORE_FULL_BODY` live 未启用是 88 条只剩前缀的直接原因——是否开启（隐私 vs 可恢复性权衡）留 G4-10 连根因一并裁。
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
    33	
    34	92 条，分类与勘探预期**零偏差**：
    35	
    36	| class | 条数 | 预期 | error_type | 错误原文（截断） | 根因与修复状态 |
    37	|---|---|---|---|---|---|
    38	| `budget_400` | **89** | 89 | BadRequestError | `Error code: 400 … 'request (16998 tokens) exceeds the available context size (16384 tokens)' type: exceed_context_size_error` | 本地 LLM 服务 context 16384 上限被超（实测请求 16948–20831 tokens）。**未修复**——根因治理归 G4-10（切块或提 budget） |
    39	| `schema_entity_type` | **2** | 2 | EntityTypeValidationError | `name cannot be used as an attribute for LearningConcept as it is a protected attribute name.` | **已修复**：P0-4（2026-05-14）双处——`entity_types.py:343` `LearningConcept.name`→`concept_name`（行 1）+ `entity_types.py:254` `LearningTip.created_at`→`tip_created_at`（行 2），同型冲突不再发生 |
    40	| `group_id_format` | **1** | 1 | GroupIdValidationError | `group_id "vault:default" must contain only alphanumeric characters, dashes, or underscores` | **已修复**：`group_id_compat.py:64 sanitize_group_id_for_graphiti` 冒号→`__` 物理化已兜（T1 契约），写路径不再直传 D16 冒号格式 |
    41	| `unexpected` | 0 | 0 | — | — | 无偏差需解释 |
    42	
    43	时间分布：3 条 schema/group_id 全部 2026-05-14（P0-4 修复当日之前的失败）；89 条 budget 集中于 2026-08-08 ~ 08-11（8/48/25/8），系 SessionEnd 归档-蒸馏管道对长会话反复触发超限。group_id 分布：`vault:canvas_vault`×89、`vault:default`×3（三条旧格式记录重放时需 group 重映射，见 §6）。
    44	
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
    86	
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
    99	
   100	- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
   101	- **BLOCKER-2（快照不原子）**：DLQ 单次 `read_bytes()`，头部 sha256/line_count 与逐条 records 派生自同一份内存字节；mtime 显式标注为 stat 参考值。
   102	- **BLOCKER-3（交付物未冻结漂移）**：以本卡 commit 冻结全部交付物 exact bytes（脚本/报告/台账/证据包同 commit）；grep-selfattest 已按最终版行号重生成并内嵌脚本 sha 前缀。
   103	- **HIGH-1（inline 判定不 fail-closed）**：full_verified 加长度精确匹配门；truncated_prefix 加 64-hex 合法性门；anomaly 一律 unrecoverable + 如实 basis（不再谎称截断、不再滑入 approximate）。
   104	- **HIGH-2（request_id fail-open）**：分组键改 `(类型名, 值)`；缺失/None 按 line_no 单条成组零传染；组内多 token 前缀一致门，冲突记 `attribution_conflict` 拒绝采信（现网 92 条 0 冲突）。
   105	- **HIGH-3（transcript 归因折叠）**：恰 1 个常规文件命中才算归因（多命中 = ambiguous 拒采信）；glob 改递归下探；transcripts 根缺失整体 exit 2（拒绝产出 unrecoverable 假象）。
   106	- **MEDIUM-1**：`episode_body_full` 在盘且 sha 对账通过 → byte_exact 采信（现网 0 条，通路已备）。
   107	- **MEDIUM-2**：`duplicate_clusters` 段 + 逐条 `reference_time`（见 §6）。
   108	- **MEDIUM-3**：台账头部 privacy 字段 + 本报告 private-only 声明（见 §6）。
   109	- **LOW-1~4**：token 区间 16948–20831、长度区间 205–8036、稳定键语义重写、schema 双处证据、挂载历史证据边界——均已在正文落地。
   110	
   111	整改后全量重跑：**92 条数字与整改前逐项一致**（class 89/2/1、三态 4/88/0、归因冲突 0、unparseable 0），重复簇 6/29 行与 Codex 独立复算吻合。另有独立 Workflow 4-agent 复核（92 条重算 0 mismatch、7 transcript 在盘实测、台账 sha 一致）交叉确认。
   112	
   113	## §7c Codex round-2 复审整改记录（10/13 CLOSED → 剩余 3 项 + 3 新 LOW 全部整改）
   114	
   115	round-2 复审确认 BLOCKER-2/3、HIGH-2、MEDIUM-1~3、LOW-1~4 共 10 项 CLOSED，并抓出 3 项**未真正闭合**（均实测复现）+ 3 条新 LOW：
   116	
   117	- **BLOCKER-1 NOT-CLOSED（hardlink / case-only 别名绕过）**：原守卫比较 `resolve()` **字符串**，hardlink 指向输入、以及大小写不敏感文件系统上的 case-only 别名均绕过并截断输入。**整改**：改为比较**文件身份 `(st_dev, st_ino)`**（对已存在的 --out）+ 保留路径比较作第二道。负例实测：两种绕过均 exit 2、DLQ sha 不变。
   118	- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
   119	- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
   120	- **新 LOW ×3**：full_verified 长度范围修正为 131–180；台账 `class_distribution`/`recoverability_distribution` 补零并新增 `inline_state_distribution`（固定 schema，消费者无需补齐缺席键）；`line_count` 改用 `splitlines()` 与 records 同口径（原 `count("\n")` 在 bare CR / U+2028 下会与 records 数不一致）。
   121	
   122	round-2 整改后再次全量重跑：92 条、class 89/2/1、三态 4/88/0、重复簇 6/29、shasum 不变——**数字仍逐项一致**，整改只收紧通用鲁棒性。
   123	
   124	## §8 复现命令
   125	
   126	```bash
   127	cd .claude/worktrees/card-s5-census
   128	python3 backend/scripts/census_dead_letter_episodes.py \
   129	  --dlq "…/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl" \
   130	  --qa-metrics-db "…/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db" \
   131	  --compare "…/canvas-learning-system/backend/data/dead_letter_episodes.jsonl" \
   132	  --compare "…/feature-obsidian-hybrid-dev/data/dead_letter_episodes.jsonl" \
   133	  --compare "…/canvas-learning-system/data/dead_letter_episodes.jsonl" \
   134	  --out "_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json"
   135	```
   136	
   137	诚实标注（与卡面一致）：本卡离用户日常价值远，属恢复能力地基；未修任何根因，未重放任何条目。
   138	
   139	## §7d Codex round-3 复审整改记录（4/6 CLOSED → 剩 2 项 + 3 新发现全部整改）
   140	
   141	round-3 确认 HIGH-1 与三条 LOW 已 CLOSED、台账数字有效且与 commit 字节一致，两项路径安全判 PARTIAL：
   142	
   143	- **BLOCKER-1 残留两条绕过**：① `protected_paths` 未含**归因到的 transcript**，`--out=<唯一 transcript>` 会截断恢复源；② check-then-open 的 **TOCTOU** 仍在（检查后、打开前把 --out 换成指向 DLQ 的链接）。**整改**：① 写出前把全部 `transcript_paths` 并入保护集；② 改 `os.open(O_WRONLY|O_CREAT|O_NOFOLLOW)` **不带 O_TRUNC** 打开 → 对**实际 fd** `fstat` 校验 inode → 通过才 `ftruncate`，检查与写入作用于同一 fd，替换攻击无效。反例实测：`--out` 指向唯一 transcript → exit 2、transcript sha 不变。
   144	- **HIGH-3 残留**：`glob(recursive=True)` 在 realpath 过滤**之前**已递归遍历（Python 3.14 glob 跟随目录 symlink 且**静默吞掉不可读子树错误**）→ 越根枚举 + "假唯一/假不可恢复"；mode `000` 的 regular transcript 仍过 `isfile()` 被判 approximate。**整改**：改 `os.walk(onerror=..., followlinks=False)`（不跟随目录 symlink、遍历错误显式捕获）+ 候选加 `os.access(R_OK)` 门；遍历受阻或存在不可读候选一律记 `attribution_conflict` 拒绝裁定（既不宣称找到、也不宣称不可恢复）。三条反例实测全部 fail-closed。
   145	- **新 MEDIUM（JSONL framing）**：生产端 `ensure_ascii=False` 可原样写出字符串内的 U+2028，`splitlines()` 会把一条合法单-LF 记录劈成两条坏行。**整改**：新增 `_split_jsonl_lines()` 严格按 LF 分帧，header `line_count` 与 records 共用同一函数。
   146	- **新 LOW（输入 schema）**：合法 JSON 但非对象（`null` / 数组 / 标量）解析成功后在 `rec.get()` 处抛 AttributeError 炸全量。**整改**：非 dict 归 `unparseable`（`not_a_json_object: <type>`），实测两条毒行不影响其余记录。
   147	- **新 LOW（provenance）**：报告头只写起始基线未区分整改 artifact commit —— 已在报告头补三段 commit 链。
   148	
   149	round-3 整改后第三次全量重跑：92 条、class 89/2/1、三态 4/88/0、重复簇 6/29、shasum 不变——**三轮整改数字全程未变**，改的全是通用鲁棒性与路径安全。
   150	
   151	## §7e Codex round-4 复审整改记录（1/6 CLOSED → 全部 9 项整改）
   152	
   153	round-4 只认可 1 项 CLOSED（非 dict JSON 门），并用更深的静态反例推翻了另外 5 项的"闭合"，另提 2 BLOCKER / 1 HIGH / 2 MEDIUM / 3 LOW。逐条整改（全部实测复现→封死）：
   154	
   155	- **BLOCKER①（不可读但可写的 transcript 绕过保护集）**：mode `0200` 的候选在 unreadable 分支被清空 `transcript_paths`，因此不进保护集，`--out` 指向它仍被截断（无需竞态）。**整改**：新增 `all_candidate_paths` 保留**所有见到的候选**（含不可读、含被冲突分支清空的），写出前全部并入保护集。实测：mode 0200 候选作 `--out` → exit 2、文件字节不变。
   156	- **BLOCKER②（源侧 TOCTOU）**：保护身份按**路径** stat 采集、DLQ 稍后才按路径读取，两步间可换入另一 inode → 实际读取对象不在保护集。**整改**：`snapshot_file()` 改为 `os.open(O_RDONLY|O_NOFOLLOW|O_NONBLOCK)` → `fstat` 取身份 + regular-file 门 → **从同一 fd 读全量**，返回的身份即**实际被读取对象**；compare 副本同样以读取身份入保护集；输入 `stat` 失败不再静默吞而是 exit 2。
   157	- **HIGH（不可见被终态化为 unrecoverable）**：扫描受阻/冲突时主链仍产出 `unrecoverable`，与报告"既不宣称不可恢复"自相矛盾。**整改**：引入第四态 **`unverifiable`**（源可见性不足，basis 逐条说明是遍历受阻/不可读候选/归因冲突），distribution 与 `unverifiable_list` 同步。实测：不可读子树 → `unverifiable=1`，不再冒充 unrecoverable。
   158	- **MEDIUM（FIFO/设备节点）**：`--out` 缺 regular-file gate 与 `O_NONBLOCK`。**整改**：`O_NONBLOCK` + `S_ISREG` 双门（读侧同样）。实测：FIFO 作 `--out` → exit 2 且不阻塞。
   159	- **MEDIUM（非法 UTF-8 冒充有效记录）**：`errors="replace"` 把坏字节改写成合法对象。**整改**：`_split_jsonl_lines()` 改**逐行 strict decode**，解码失败归 `unparseable`。实测：`b'{"a":"\xff"}'` → `utf8_decode_error`，records=0。
   160	- **LOW ×3**：dict 内字段错型防御（`name=None` / `request_id=[]` 不可哈希 / `episode_body` 非 str 均不再炸全量，按 line_no 单条成组或判 anomaly）；`transcripts_dir="/"` 的 `//` containment 特例；`0o600` 对**既有**输出文件用 `fchmod` 显式收紧（实测台账 mode 现为 `-rw-------`）。
   161	- **LOW（provenance 自指）**：commit 无法自含己身 SHA，改用后置 `artifact-commit-receipt.txt` 绑定精确链，报告头指向该 receipt。
   162	
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
   194	
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
    13	5b371253  CARD-G4-9 round-6 架构级修复
    14	4ba4f847  receipt 补 round-5/6 链
    15	f389980c  CARD-G4-9 round-7 架构级修复（消除截断动作；本 receipt 当前版所描述的 commit）
    16	
    17	各阶段交付物 blob 可用 git cat-file 复核；台账头部 dlq_file.sha256 为 DLQ 快照指纹。

**Identifying discrepancy in UAT round7 summary**
**Planning detailed commit and ledger inspection**
exec
/bin/zsh -lc 'git diff --no-ext-diff f389980c''^ f389980c -- '"'_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' '_bmad-output/审查/G4-9-evidence/grep-selfattest.txt' '_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md' '_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md'
git show --format=fuller --no-patch f389980c
git status --porcelain=v1" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 3ms:
?? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round8.md"

**Verifying untracked file integrity**
**Designing independent ledger validation algorithm**
**Planning source attribution verification**
**Planning root rescan for duplicates**
**Designing token-based duplicate classification**
exec
/bin/zsh -lc "python3 -B -c '
import collections, hashlib, json, os, re, stat
from pathlib import Path
src=Path(\"/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl\")
ledger_path=Path(\"_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json\")
root=Path(\"/Users/Heishing/.claude/projects\")
raw=src.read_bytes()
chunks=raw[:-1].split(b\"\\n\") if raw.endswith(b\"\\n\") else raw.split(b\"\\n\") if raw else []
records=[]; bad=[]
for idx,b in enumerate(chunks,1):
    try: s=b.decode(\"utf-8\"); obj=json.loads(s)
    except Exception as e: bad.append((idx,type(e).__name__)); continue
    if not isinstance(obj,dict): bad.append((idx,\"not_dict\")); continue
    records.append((idx,obj))
budget=re.compile(r\"exceed_context_size_error|exceeds the available context size\")
sha_re=re.compile(r\""'^[0-9a-f]{64}$")
archive_re=re.compile(r"''^session-archive:([0-9a-fA-F-]+)")
inline_re=re.compile(r"(?<![0-9a-zA-Z_-])session:([0-9a-f-]{5,})")
def cls(x):
    et=x.get("error_type","")
    if not isinstance(et,str): return "unexpected"
    if et=="EntityTypeValidationError": return "schema_entity_type"
    if et=="GroupIdValidationError": return "group_id_format"
    if et=="BadRequestError" and budget.search(str(x.get("error",""))): return "budget_400"
    return "unexpected"
def inline(x):
    body=x.get("episode_body",""); ln=x.get("episode_body_length"); sh=x.get("episode_body_sha256","")
    if not isinstance(body,str): return "anomaly"
    try: enc=body.encode("utf-8")
    except UnicodeEncodeError: return "anomaly"
    goodsha=isinstance(sh,str) and bool(sha_re.fullmatch(sh)); goodln=isinstance(ln,int) and not isinstance(ln,bool)
    if goodsha and goodln and len(body)==ln and hashlib.sha256(enc).hexdigest()==sh: return "full_verified"
    if goodsha and goodln and len(body)==200 and ln>200: return "truncated_prefix"
    return "anomaly"
def full_ok(x):
    v=x.get("episode_body_full"); ln=x.get("episode_body_length"); sh=x.get("episode_body_sha256","")
    if not isinstance(v,str) or not isinstance(sh,str) or not sha_re.fullmatch(sh) or not isinstance(ln,int) or isinstance(ln,bool) or len(v)!=ln: return False
    try: return hashlib.sha256(v.encode("utf-8")).hexdigest()==sh
    except UnicodeEncodeError: return False
def toks(name):
    if not isinstance(name,str): return []
    out=[]; m=archive_re.match(name)
    if m: out.append(m.group(1).lower())
    out += [x.lower() for x in inline_re.findall(name)]
    return out
groups=collections.defaultdict(list)
for n,x in records:
    rid=x.get("request_id")
    try: hash(rid); key=(type(rid).__name__,rid) if rid is not None else ("__missing__",n)
    except TypeError: key=("__missing__",n)
    groups[key].append((n,x))
all_files=[]; walk_errors=[]
def onerr(e): walk_errors.append(type(e).__name__)
for dp,dns,fns in os.walk(root,onerror=onerr,followlinks=False):
    for fn in fns:
        if fn.endswith(".jsonl"): all_files.append(os.path.join(dp,fn))
attrs={}
for key,members in groups.items():
    ts=[]
    for _,x in members: ts += toks(x.get("name",""))
    uniq=sorted(set(ts),key=len); reason=None; matches=[]
    if not uniq: reason="no_token"
    else:
        longest=uniq[-1]
        if any(not longest.startswith(t) for t in uniq[:-1]): reason="token_conflict"
        else:
            for p in all_files:
                if os.path.basename(p).startswith(longest):
                    try:
                        if os.path.islink(p) or not os.path.isfile(p) or not os.access(p,os.R_OK): continue
                    except OSError: continue
                    matches.append(p)
            matches=sorted(set(matches))
            if walk_errors: reason="scan_errors"
            elif len(matches)>1: reason="ambiguous_multi_match"
    attrs[key]=(reason,matches)
class_c=collections.Counter(); inline_c=collections.Counter(); recov_c=collections.Counter(); conflicts=[]; derived=[]
clusters=collections.defaultdict(list)
for n,x in records:
    rid=x.get("request_id")
    try: hash(rid); key=(type(rid).__name__,rid) if rid is not None else ("__missing__",n)
    except TypeError: key=("__missing__",n)
    c=cls(x); ins=inline(x); reason,matches=attrs[key]
    if ins=="full_verified" or (ins!="anomaly" and full_ok(x)): recov="byte_exact"
    elif reason is not None: recov="unverifiable"
    elif ins=="anomaly": recov="unrecoverable"
    elif len(matches)==1: recov="approximate"
    else: recov="unrecoverable"
    class_c[c]+=1; inline_c[ins]+=1; recov_c[recov]+=1
    if reason is not None: conflicts.append((n,reason))
    derived.append((n,c,ins,recov,reason,len(matches)))
    clusters[(str(x.get("name","")),str(x.get("episode_body_sha256","")),str(x.get("group_id")))].append(n)
dups=sorted([v for v in clusters.values() if len(v)>1],key=lambda v:(-len(v),v))
led=json.loads(ledger_path.read_text(encoding="utf-8")); lm=[]
for d,l in zip(derived,led["records"]):
    n,c,ins,recov,reason,mc=d
    got=(l["stable_key"]["line_no"],l["class"],l["inline_state"],l["recoverability"],l.get("attribution_conflict_reason"),l.get("transcript_match_count"))
    exp=(n,c,ins,recov,reason,mc)
    if got!=exp: lm.append((n,exp,got))
summary={"source_exists":src.exists(),"source_size":len(raw),"source_sha256":hashlib.sha256(raw).hexdigest(),"lines":len(chunks),"records":len(records),"unparseable":len(bad),"class":dict(class_c),"inline":dict(inline_c),"recoverability":dict(recov_c),"attribution_conflicts":collections.Counter(x[1] for x in conflicts),"conflict_lines":[x[0] for x in conflicts],"transcript_metadata_only":{"jsonl_seen":len(all_files),"unique_selected":len(set(p for reason,ms in attrs.values() for p in ms if reason is None and len(ms)==1)),"walk_errors":walk_errors},"duplicate_clusters":len(dups),"duplicate_rows":sum(map(len,dups)),"duplicate_sizes":[len(x) for x in dups],"ledger_record_mismatches":len(lm),"ledger_header_source_sha_match":led["dlq_file"]["sha256"]==hashlib.sha256(raw).hexdigest()}
print(json.dumps(summary,ensure_ascii=True,sort_keys=True))
'"' 
stat -f 'source_mode=%Lp source_size=%z source_inode=%d:%i' '/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl'
shasum -a 256 '/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 46ms:
{"attribution_conflicts": {"no_token": 3}, "class": {"budget_400": 89, "group_id_format": 1, "schema_entity_type": 2}, "conflict_lines": [1, 2, 3], "duplicate_clusters": 6, "duplicate_rows": 29, "duplicate_sizes": [16, 4, 3, 2, 2, 2], "inline": {"full_verified": 4, "truncated_prefix": 88}, "ledger_header_source_sha_match": true, "ledger_record_mismatches": 0, "lines": 92, "records": 92, "recoverability": {"approximate": 88, "byte_exact": 4}, "source_exists": true, "source_sha256": "3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590", "source_size": 99915, "transcript_metadata_only": {"jsonl_seen": 3605, "unique_selected": 7, "walk_errors": []}, "unparseable": 0}
source_mode=644 source_size=99915 source_inode=16777230:11179623
3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl

**Verifying absence of temporary files with find**
exec
/bin/zsh -lc "find . -name '*.census-tmp-*' -print
find '_bmad-output/审查' -maxdepth 1 -name '.*.census-tmp-*' -print
find . -name '*.census-tmp-*' -print | wc -l
stat -f 'round8_mode=%Lp round8_size=%z round8_mtime=%Sm' -t '%Y-%m-%dT%H:%M:%S%z' '_bmad-output/审查/codex-review-CARD-G4-9-round8.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 2891ms:
       0
round8_mode=644 round8_size=428004 round8_mtime=2026-08-28T21:19:53+0800

**Planning official docs research**
web search: 
web search: site:docs.python.org/3/library/os.html os.replace os.open O_EXCL O_NOFOLLOW ...
**Planning official docs search**
web search: 
web search: 
**Retrieving Python lines for umask**
web search: 
web search: 
**Evaluating directory fsync impact on atomicity and durability**
**Identifying incomplete cleanup and durability gaps on crash**
**Assessing symlink and stale temp file risks**
**Analyzing TOCTOU exploit scenario**
**Evaluating symlink-based overwrite conditions**
**Confirming source preservation against parent retarget**
**Analyzing root retargeting impact on output paths**
**Identifying TOCTOU risk in root retargeting**
**Evaluating symlink stability and precreation risks**
**Identifying critical symlink vulnerability**
**Confirming hardlink and symlink safety on replace operations**
**Highlighting TOCTOU risk with parent symlink swaps**
**Assessing rename syscall mount race conditions**
**Analyzing mount point rename edge cases**
**Identifying rename fail and concurrency issues**
**Analyzing spawn temp file permissions**
**Identifying temp file cleanup race conditions**
**Confirming regular file creation with flags**
**Implementing safe JSON encoding fallback**
**Detecting dropped scan errors for no-token groups**
**Identifying suppressed error propagation on early return**
**Analyzing candidate stat error handling**
**Evaluating incomplete scan error impacts**
**Identifying TOCTOU risk in file checks**
**Analyzing symlink loop detection**
**Verifying symlink and mount boundary handling**
**Clarifying inode behavior on APFS**
**Identifying rename and mount race conditions**
**Analyzing rename behavior and permission edge cases**
**Evaluating os.replace mount point race**
**Analyzing symlink leaf bypass implications**
**Evaluating symlink handling flaws in path checks**
**Confirming realpath handling with hardlinks and symlinks**
**Verifying symlink and path resolution behavior**
**Planning precise QA discrepancy inspection**
exec
/bin/zsh -lc "rg -n '"'^总裁定|''^## QA DB|URI BLOCKER|验收结论|当前大小写|before/after'"' '_bmad-output/审查/codex-review-CARD-G4-9-round7.md' | tail -40
wc -l '_bmad-output/审查/codex-review-CARD-G4-9-round7.md'
nl -ba '_bmad-output/审查/codex-review-CARD-G4-9-round7.md' | tail -180" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
571:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:226:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
576:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:245:2765:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:7:| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
587:./_bmad-output/审查/codex-review-CARD-G4-9-round4.md:256:2815:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
742:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:928:226:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
747:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:944:245:2765:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:7:| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
757:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:954:256:2815:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
872:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2310:226:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
873:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2313:245:2765:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:7:| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
876:./_bmad-output/审查/codex-review-CARD-G4-9-round5.md:2316:256:2815:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
1196:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
1217:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2765:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:7:| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
1265:./_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2815:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
1383:./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:505:928:226:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
1388:./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:521:944:245:2765:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:7:| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
1398:./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:531:954:256:2815:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
1441:./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:789:2310:226:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
1442:./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:792:2313:245:2765:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:7:| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
1445:./_bmad-output/审查/codex-review-CARD-G4-9-round6.md:795:2316:256:2815:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
1668:./_bmad-output/审查/codex-review-CARD-G4-9-round2.md:7:| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
1799:505:928:226:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
1813:521:944:245:2765:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:7:| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
1821:531:954:256:2815:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
1941:789:2310:226:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
1944:792:2313:245:2765:_bmad-output/审查/codex-review-CARD-G4-9-round2.md:7:| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
1947:795:2316:256:2815:_bmad-output/审查/codex-review-CARD-G4-9-round3.md:2143:     7	| BLOCKER-1 | **NOT-CLOSED** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:234)覆盖了 `--dlq/--compare/--qa-metrics-db`。exact、相对路径、三类 symlink 均 exit 2 且输入未变。但 hardlink 指向三类输入时均 exit 0、对应输入 SHA 改变；当前大小写不敏感文件系统上 case-only DLQ 别名也 exit 0 并截断输入。根因是比较 `resolve()` 字符串而非文件身份，最终仍用 [`open(...,"w")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:392)。检查与打开分离还保留 symlink TOCTOU。 |
3991:总裁定：**仍阻断，CARD-G4-9 round-6 不可验收。**
4055:总裁定：**仍阻断，CARD-G4-9 round-6 不可验收。**
5690:> **证据包**: `_bmad-output/审查/G4-9-evidence/`（shasums before/after、grep 自证、容器内 sha 实测）
6398:总裁定：**仍阻断，CARD-G4-9 round-7 不可验收。**
6429:## QA DB 仍未绑定实际连接对象
6442:此外，round-6 已指出的 URI BLOCKER **完全未修**：[line 291](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:291)仍直接拼接 `file:{db_path}?mode=ro`。SQLite 官方规定普通文件名里的 `?/#` 必须转义，fragment 会被忽略；所以 `/x/qa#tag` 可被解析成另一文件且吞掉 `mode=ro`。[SQLite URI 规则](https://www.sqlite.org/uri.html)、[Python sqlite3 URI 行为](https://docs.python.org/3/library/sqlite3.html#how-to-work-with-sqlite-uris)。
6460:- **BLOCKER**：当前大小写不敏感卷上的 case-only 根别名是无需竞态的实际绕过。
6463:- before/after shasum 与当前 bytes 一致，但静态复审不能证明两份清单真实采集时序。
6467:**验收结论：现有 92 条冻结 ledger 可以采信；CARD-G4-9 生成器与 UAT 的纯只读安全声明不可验收。**
6472:总裁定：**仍阻断，CARD-G4-9 round-7 不可验收。**
6503:## QA DB 仍未绑定实际连接对象
6516:此外，round-6 已指出的 URI BLOCKER **完全未修**：[line 291](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:291)仍直接拼接 `file:{db_path}?mode=ro`。SQLite 官方规定普通文件名里的 `?/#` 必须转义，fragment 会被忽略；所以 `/x/qa#tag` 可被解析成另一文件且吞掉 `mode=ro`。[SQLite URI 规则](https://www.sqlite.org/uri.html)、[Python sqlite3 URI 行为](https://docs.python.org/3/library/sqlite3.html#how-to-work-with-sqlite-uris)。
6534:- **BLOCKER**：当前大小写不敏感卷上的 case-only 根别名是无需竞态的实际绕过。
6537:- before/after shasum 与当前 bytes 一致，但静态复审不能证明两份清单真实采集时序。
6541:**验收结论：现有 92 条冻结 ledger 可以采信；CARD-G4-9 生成器与 UAT 的纯只读安全声明不可验收。**
    6543 _bmad-output/审查/codex-review-CARD-G4-9-round7.md
  6364	**Clarifying search tool limitations**
  6365	**Documenting snapshot and classification details**
  6366	**Identifying new blocker cases**
  6367	**Identifying URI carryover blocker**
  6368	**Designing path symlink matrix**
  6369	**Assessing new path containment blockers**
  6370	**Summarizing rejection with closure recommendations**
  6371	**Planning evaluation of closure hypothesis**
  6372	codex
  6373	交叉核验已收束：冻结台账与 receipt 链是可采信的，但生成器安全闭包仍失败。尤其当前卷上已只读确认 `/Users/.../projects` 与 `/users/.../projects` 是同一目录，而 `realpath` 字符串不同，形成无需竞态的根内写入绕过；QA 的 rename 型 ABA 与 round-6 未修的 URI 问题也仍成立。正在整理最终逐项矩阵与验收边界。
  6374	mcp: sequential-thinking/sequentialthinking started
  6375	mcp: sequential-thinking/sequentialthinking (completed)
  6376	mcp: sequential-thinking/sequentialthinking started
  6377	mcp: sequential-thinking/sequentialthinking (completed)
  6378	**Completing update plan**
  6379	全部只读证据轨与交叉核验完成，结论已收束。
  6380	  ✓ 核对 checkout、commit/receipt 链及 round-6 基线
  6381	  ✓ 静态审阅五项修复及生产入口控制流
  6382	  ✓ 设计并只读验证路径、inode、TOCTOU 新反例
  6383	  ✓ 从原始工件独立复算台账与证据包指标
  6384	  ✓ 交叉核验后给出逐项 CLOSED/NOT-CLOSED 与总裁定
  6385	**Drafting final Chinese citations**
  6386	**Including relevant rollout IDs in citations**
  6387	**Defining base file paths**
  6388	**Summarizing symlink path cases**
  6389	**Planning SQLite URI handling**
  6390	**Identifying ledger table blockers and risks**
  6391	**Confirming macOS case-insensitive file handling**
  6392	**Verifying Path.resolve case behavior on macOS**
  6393	**Analyzing path guard limitation with hardlinks**
  6394	**Confirming output truncation behavior**
  6395	**Planning detailed metric reporting format**
  6396	**Confirming memory skill as guidance**
  6397	codex
  6398	总裁定：**仍阻断，CARD-G4-9 round-7 不可验收。**
  6399	
  6400	冻结台账数字可采信，但生成器的“纯只读、恢复源区域零写入”安全闭包仍失败。按开发方 5 个编号计：**2 CLOSED / 2 NOT-CLOSED / 1 PARTIAL**；拆成 6 个原子声明则是 **3 CLOSED / 3 NOT-CLOSED**。
  6401	
  6402	审阅锚点：`HEAD=4ba4f847fa3ad83d136d3a40fcc5448b25c54ba5`，直接父提交为 `5b3712537ef5be91eda18e2a9eaf2fd3d5e03ef5`。
  6403	
  6404	## 逐项裁定
  6405	
  6406	| 项目 | 裁定 | 结果 |
  6407	|---|---|---|
  6408	| 1. transcripts 路径层防御 | **NOT-CLOSED · BLOCKER** | 一次性 `realpath` 字符串检查仍受 hardlink、大小写别名和父目录换链影响。[路径检查](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:421)；最终仍原路径 `open`/`ftruncate`，[写入入口](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:733)。 |
  6409	| 2. QA DB fd 保持及复核 | **NOT-CLOSED · BLOCKER** | 验证 fd=A 虽保持打开，SQLite 仍按 pathname 另开连接；rename 型 A→B→A 可令连接读 B，而两次复核都看到 A。[QA 打开链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:277)。 |
  6410	| 3. no_token 也遍历 | **CLOSED（狭义）** | 现在先无条件遍历、收集可见 `.jsonl`，再于 no_token 分支返回。[遍历](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:201)。但它不覆盖不可枚举 inode，因此不能补救项目 1。 |
  6411	| 4. self-attest + receipt | **CLOSED（当前仓库内）** | self-attest 内嵌脚本 SHA `533d0d4c…e3585` 与实际一致；脚本/self-attest/ledger 从 `5b371253` 到 HEAD blob 均未变。[self-attest](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:1)、[receipt](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt:12)。 |
  6412	| 5a. attribution_conflict_reason | **CLOSED** | 字段已序列化不同原因；冻结台账三条均为 `no_token`。[生成逻辑](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:616)、[台账实例](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:202)。 |
  6413	| 5b. lone-surrogate 回退 | **NOT-CLOSED · LOW** | `json.dumps(..., ensure_ascii=False)` 会正常返回含 surrogate 的 `str`；异常发生在后续 UTF-8 `write/print`，不在当前 `try` 内。[回退代码](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:725)。`--out` 分支还会先 `ftruncate`，再写出失败。 |
  6414	
  6415	## 路径反例矩阵
  6416	
  6417	| 反例 | 结果 |
  6418	|---|---|
  6419	| 根外稳定 symlink → 根内文件 | **CLOSED**：`realpath` 命中；final symlink 还受 `O_NOFOLLOW` 约束。 |
  6420	| 根外 hardlink → 可枚举 transcript | **CLOSED**：枚举所得 inode 会在最终 `fstat` 命中。 |
  6421	| 根外 hardlink → `0333` 隐藏目录内 transcript | **NOT-CLOSED**：hardlink 的 `realpath` 仍在根外；隐藏 inode 未被枚举，最终可被截断。 |
  6422	| transcripts 根是稳定 symlink | **CLOSED**：两侧稳定 `realpath` 指向相同真实根。 |
  6423	| transcripts 根在检查后 retarget | **NOT-CLOSED**：未持有/复核根目录 fd，检查绑定旧目标，扫描或写入可使用新目标。 |
  6424	| 相对路径与 `..` | **CLOSED**：无竞态、大小写一致时会被正规化。 |
  6425	| 检查后仅把 basename 换成 symlink | **CLOSED**：最终 `O_NOFOLLOW` 拒绝。 |
  6426	| 检查后换父目录 symlink或把 basename 换成 hardlink | **NOT-CLOSED**：`O_NOFOLLOW` 只约束最终 symlink，不约束父组件或 hardlink。 |
  6427	| 大小写别名 | **NOT-CLOSED、无需竞态**：本机只读复算确认 `/Users/Heishing/.claude/projects` 与 `/users/heishing/.claude/projects` `samefile=True`，但两者 `realpath` 字符串不同，现有 prefix guard 返回 `False`。 |
  6428	
  6429	## QA DB 仍未绑定实际连接对象
  6430	
  6431	确定性调度如下：
  6432	
  6433	1. 验证并保持 A 的 fd；
  6434	2. rename A→stash，B→原路径；
  6435	3. `sqlite3.connect()` 打开 B；
  6436	4. B→stashB，A→原路径；
  6437	5. 路径 `stat` 与验证 fd `fstat` 均为 A，且 rename 不会令 A 的 `st_nlink` 变 0；
  6438	6. 查询实际仍来自 B。
  6439	
  6440	因此二次 `fstat` 只证明“验证 fd 仍指向 A”，没有证明 SQLite connection 指向 A。
  6441	
  6442	此外，round-6 已指出的 URI BLOCKER **完全未修**：[line 291](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:291)仍直接拼接 `file:{db_path}?mode=ro`。SQLite 官方规定普通文件名里的 `?/#` 必须转义，fragment 会被忽略；所以 `/x/qa#tag` 可被解析成另一文件且吞掉 `mode=ro`。[SQLite URI 规则](https://www.sqlite.org/uri.html)、[Python sqlite3 URI 行为](https://docs.python.org/3/library/sqlite3.html#how-to-work-with-sqlite-uris)。
  6443	
  6444	## 台账独立复算：PASS
  6445	
  6446	未 import 被审生成器，直接从 live DLQ exact bytes 重写严格 LF/UTF-8/JSON、分类、SHA/长度、分组和聚簇计算：
  6447	
  6448	- SHA-256：`3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590`
  6449	- `99,915 bytes`；92 records；unparseable 0
  6450	- class：`89 / 2 / 1`，unexpected 0
  6451	- recoverability：`byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0`
  6452	- 重复簇：`6 / 29`，大小 `16,4,3,2,2,2`
  6453	- attribution conflict：3，全部 `no_token`、全部为 callout、全部因 inline SHA+长度双门通过而仍属 `byte_exact`
  6454	- 与冻结 ledger 逐条 class/inline/recoverability/reason：`0 mismatch`
  6455	
  6456	汇总与冻结工件一致：[ledger:40](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:40)。
  6457	
  6458	## 新发现与限制
  6459	
  6460	- **BLOCKER**：当前大小写不敏感卷上的 case-only 根别名是无需竞态的实际绕过。
  6461	- **MEDIUM**：`--out` 采用原地 `ftruncate` 后写入，没有临时文件、atomic replace、`fsync` 或并发锁；崩溃、ENOSPC、surrogate 或并发运行可留下空/部分/混写台账。
  6462	- **LOW**：receipt 使用当前仓库唯一可解析的 8 位缩写，不是跨仓可独立验证的完整 40-hex OID。
  6463	- before/after shasum 与当前 bytes 一致，但静态复审不能证明两份清单真实采集时序。
  6464	
  6465	本轮未创建 symlink/hardlink/竞态 fixture，未读取 transcript 正文或 Vault；只读取任务范围内 DLQ exact bytes及 transcript 元数据。工作树仍只有开始前已存在的未跟踪 round-7 文件，未触碰任何文件。`graphiti-canvas` 本环境未暴露，故本轮 Graphiti 搜索明确为不可执行；Sequential Thinking 已完成。
  6466	
  6467	**验收结论：现有 92 条冻结 ledger 可以采信；CARD-G4-9 生成器与 UAT 的纯只读安全声明不可验收。**
  6468	
  6469	
  6470	tokens used
  6471	159,964
  6472	总裁定：**仍阻断，CARD-G4-9 round-7 不可验收。**
  6473	
  6474	冻结台账数字可采信，但生成器的“纯只读、恢复源区域零写入”安全闭包仍失败。按开发方 5 个编号计：**2 CLOSED / 2 NOT-CLOSED / 1 PARTIAL**；拆成 6 个原子声明则是 **3 CLOSED / 3 NOT-CLOSED**。
  6475	
  6476	审阅锚点：`HEAD=4ba4f847fa3ad83d136d3a40fcc5448b25c54ba5`，直接父提交为 `5b3712537ef5be91eda18e2a9eaf2fd3d5e03ef5`。
  6477	
  6478	## 逐项裁定
  6479	
  6480	| 项目 | 裁定 | 结果 |
  6481	|---|---|---|
  6482	| 1. transcripts 路径层防御 | **NOT-CLOSED · BLOCKER** | 一次性 `realpath` 字符串检查仍受 hardlink、大小写别名和父目录换链影响。[路径检查](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:421)；最终仍原路径 `open`/`ftruncate`，[写入入口](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:733)。 |
  6483	| 2. QA DB fd 保持及复核 | **NOT-CLOSED · BLOCKER** | 验证 fd=A 虽保持打开，SQLite 仍按 pathname 另开连接；rename 型 A→B→A 可令连接读 B，而两次复核都看到 A。[QA 打开链](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:277)。 |
  6484	| 3. no_token 也遍历 | **CLOSED（狭义）** | 现在先无条件遍历、收集可见 `.jsonl`，再于 no_token 分支返回。[遍历](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:201)。但它不覆盖不可枚举 inode，因此不能补救项目 1。 |
  6485	| 4. self-attest + receipt | **CLOSED（当前仓库内）** | self-attest 内嵌脚本 SHA `533d0d4c…e3585` 与实际一致；脚本/self-attest/ledger 从 `5b371253` 到 HEAD blob 均未变。[self-attest](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:1)、[receipt](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt:12)。 |
  6486	| 5a. attribution_conflict_reason | **CLOSED** | 字段已序列化不同原因；冻结台账三条均为 `no_token`。[生成逻辑](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:616)、[台账实例](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:202)。 |
  6487	| 5b. lone-surrogate 回退 | **NOT-CLOSED · LOW** | `json.dumps(..., ensure_ascii=False)` 会正常返回含 surrogate 的 `str`；异常发生在后续 UTF-8 `write/print`，不在当前 `try` 内。[回退代码](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:725)。`--out` 分支还会先 `ftruncate`，再写出失败。 |
  6488	
  6489	## 路径反例矩阵
  6490	
  6491	| 反例 | 结果 |
  6492	|---|---|
  6493	| 根外稳定 symlink → 根内文件 | **CLOSED**：`realpath` 命中；final symlink 还受 `O_NOFOLLOW` 约束。 |
  6494	| 根外 hardlink → 可枚举 transcript | **CLOSED**：枚举所得 inode 会在最终 `fstat` 命中。 |
  6495	| 根外 hardlink → `0333` 隐藏目录内 transcript | **NOT-CLOSED**：hardlink 的 `realpath` 仍在根外；隐藏 inode 未被枚举，最终可被截断。 |
  6496	| transcripts 根是稳定 symlink | **CLOSED**：两侧稳定 `realpath` 指向相同真实根。 |
  6497	| transcripts 根在检查后 retarget | **NOT-CLOSED**：未持有/复核根目录 fd，检查绑定旧目标，扫描或写入可使用新目标。 |
  6498	| 相对路径与 `..` | **CLOSED**：无竞态、大小写一致时会被正规化。 |
  6499	| 检查后仅把 basename 换成 symlink | **CLOSED**：最终 `O_NOFOLLOW` 拒绝。 |
  6500	| 检查后换父目录 symlink或把 basename 换成 hardlink | **NOT-CLOSED**：`O_NOFOLLOW` 只约束最终 symlink，不约束父组件或 hardlink。 |
  6501	| 大小写别名 | **NOT-CLOSED、无需竞态**：本机只读复算确认 `/Users/Heishing/.claude/projects` 与 `/users/heishing/.claude/projects` `samefile=True`，但两者 `realpath` 字符串不同，现有 prefix guard 返回 `False`。 |
  6502	
  6503	## QA DB 仍未绑定实际连接对象
  6504	
  6505	确定性调度如下：
  6506	
  6507	1. 验证并保持 A 的 fd；
  6508	2. rename A→stash，B→原路径；
  6509	3. `sqlite3.connect()` 打开 B；
  6510	4. B→stashB，A→原路径；
  6511	5. 路径 `stat` 与验证 fd `fstat` 均为 A，且 rename 不会令 A 的 `st_nlink` 变 0；
  6512	6. 查询实际仍来自 B。
  6513	
  6514	因此二次 `fstat` 只证明“验证 fd 仍指向 A”，没有证明 SQLite connection 指向 A。
  6515	
  6516	此外，round-6 已指出的 URI BLOCKER **完全未修**：[line 291](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:291)仍直接拼接 `file:{db_path}?mode=ro`。SQLite 官方规定普通文件名里的 `?/#` 必须转义，fragment 会被忽略；所以 `/x/qa#tag` 可被解析成另一文件且吞掉 `mode=ro`。[SQLite URI 规则](https://www.sqlite.org/uri.html)、[Python sqlite3 URI 行为](https://docs.python.org/3/library/sqlite3.html#how-to-work-with-sqlite-uris)。
  6517	
  6518	## 台账独立复算：PASS
  6519	
  6520	未 import 被审生成器，直接从 live DLQ exact bytes 重写严格 LF/UTF-8/JSON、分类、SHA/长度、分组和聚簇计算：
  6521	
  6522	- SHA-256：`3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590`
  6523	- `99,915 bytes`；92 records；unparseable 0
  6524	- class：`89 / 2 / 1`，unexpected 0
  6525	- recoverability：`byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0`
  6526	- 重复簇：`6 / 29`，大小 `16,4,3,2,2,2`
  6527	- attribution conflict：3，全部 `no_token`、全部为 callout、全部因 inline SHA+长度双门通过而仍属 `byte_exact`
  6528	- 与冻结 ledger 逐条 class/inline/recoverability/reason：`0 mismatch`
  6529	
  6530	汇总与冻结工件一致：[ledger:40](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:40)。
  6531	
  6532	## 新发现与限制
  6533	
  6534	- **BLOCKER**：当前大小写不敏感卷上的 case-only 根别名是无需竞态的实际绕过。
  6535	- **MEDIUM**：`--out` 采用原地 `ftruncate` 后写入，没有临时文件、atomic replace、`fsync` 或并发锁；崩溃、ENOSPC、surrogate 或并发运行可留下空/部分/混写台账。
  6536	- **LOW**：receipt 使用当前仓库唯一可解析的 8 位缩写，不是跨仓可独立验证的完整 40-hex OID。
  6537	- before/after shasum 与当前 bytes 一致，但静态复审不能证明两份清单真实采集时序。
  6538	
  6539	本轮未创建 symlink/hardlink/竞态 fixture，未读取 transcript 正文或 Vault；只读取任务范围内 DLQ exact bytes及 transcript 元数据。工作树仍只有开始前已存在的未跟踪 round-7 文件，未触碰任何文件。`graphiti-canvas` 本环境未暴露，故本轮 Graphiti 搜索明确为不可执行；Sequential Thinking 已完成。
  6540	
  6541	**验收结论：现有 92 条冻结 ledger 可以采信；CARD-G4-9 生成器与 UAT 的纯只读安全声明不可验收。**
  6542	
  6543	

**Identifying scope anchor conflict in report**
**Highlighting SQLite URI write risk**
web search: 
**Implementing wait after exec deferral**
web search: site:docs.python.org/3/library/sqlite3.html URI mode=ro sqlite3.connect file database
**Planning comprehensive documentation with references**
mcp: sequential-thinking/sequentialthinking started
mcp: sequential-thinking/sequentialthinking (completed)
**Planning static path verification**
**Analyzing static path containment checks**
**Assessing hardlink unlink impact on inode metadata**
**Confirming inode metadata changes violate pure readonly claim**
**Analyzing hardlink metadata effects**
**Evaluating transcript hardlink protections and behaviors**
**Tracing hardlink rename and unlink effects**
**Searching for official unlink semantics**
**Verifying official POSIX unlink/rename**
web search: 
web search: site:pubs.opengroup.org/onlinepubs/9799919799/functions/unlink.html link count last link removed ...
**Auditing file mode handling and Git semantics**
**Verifying ledger integrity and file operation traces**
**Assessing symlink locations without modification**
**Summarizing audit metadata rescan results**
collab: Wait
**Clarifying symlink resolution edge cases**
**Analyzing parent symlink retarget race conditions**
**Distinguishing hardlink swap impact on metadata**
**Assessing inode link count and ctime behavior**
**Clarifying read-only content definition**
collab: Wait
**Planning static anchor and symlink checks**
exec
/bin/zsh -lc "python3 -B -c '
import os
root=\"/Users/Heishing/.claude/projects\"
target=\"/users/heishing/.claude/projects/nonexistent-census-output.json\"
def within(t,r):
    s=os.stat(r); rid=(s.st_dev,s.st_ino); cur=os.path.realpath(t)
    while True:
        try:
            x=os.stat(cur)
            if (x.st_dev,x.st_ino)==rid: return True
        except OSError: pass
        p=os.path.dirname(cur)
        if p==cur: return False
        cur=p
print({\"root_alias_samefile\":os.path.samefile(root,\"/users/heishing/.claude/projects\"),\"realpath_strings_equal\":os.path.realpath(root)==os.path.realpath(\"/users/heishing/.claude/projects\"),\"inode_ancestry_guard\":within(target,root)})
'
mount" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
{'root_alias_samefile': True, 'realpath_strings_equal': False, 'inode_ancestry_guard': True}
/dev/disk3s1s1 on / (apfs, sealed, local, read-only, journaled)
devfs on /dev (devfs, local, nobrowse)
/dev/disk3s6 on /System/Volumes/VM (apfs, local, noexec, journaled, noatime, nobrowse)
/dev/disk3s2 on /System/Volumes/Preboot (apfs, local, journaled, nobrowse)
/dev/disk3s4 on /System/Volumes/Update (apfs, local, journaled, nobrowse)
/dev/disk1s2 on /System/Volumes/xarts (apfs, local, noexec, journaled, noatime, nobrowse)
/dev/disk1s1 on /System/Volumes/iSCPreboot (apfs, local, journaled, nobrowse)
/dev/disk1s3 on /System/Volumes/Hardware (apfs, local, journaled, nobrowse)
/dev/disk3s5 on /System/Volumes/Data (apfs, local, journaled, nobrowse, protect, root data)
map auto_home on /System/Volumes/Data/home (autofs, automounted, nobrowse)
/dev/disk5s1 on /Volumes/Obsidian 1.12.7-universal (apfs, local, nodev, nosuid, read-only, journaled, noowners, quarantine, mounted by Heishing)
/Volumes/Obsidian 1.12.7-universal/Obsidian.app on /private/var/folders/vq/gssw8vy54671lh9nlqc_ft2w0000gn/T/AppTranslocation/2D56C8CD-387B-4728-91FB-0BA981F2FEF5 (nullfs, local, nodev, nosuid, read-only, noowners, quarantine, nobrowse, mounted by Heishing)
/dev/disk2s1 on /System/Volumes/Update/SFR/mnt1 (apfs, local, journaled, nobrowse)
/dev/disk7s1 on /private/tmp/dmg.H9CS6n (apfs, local, nodev, nosuid, read-only, journaled, noowners, nobrowse, mounted by Heishing)
/dev/disk3s1 on /System/Volumes/Update/mnt1 (apfs, sealed, local, journaled, nobrowse)
/dev/disk8s1 on /Volumes/Tavern Deepseek (hfs, local, nodev, nosuid, read-only, noowners, quarantine, mounted by Heishing)
/dev/disk9s1 on /Volumes/Tavern Deepseek 1 (hfs, local, nodev, nosuid, read-only, noowners, quarantine, mounted by Heishing)

**Verifying os.path.isfile error handling**
**Inspecting local Python isfile source**
exec
/bin/zsh -lc "python3 -B -c 'import genericpath, inspect; print(inspect.getsource(genericpath.isfile)); print(inspect.getsource(genericpath.islink))'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
def isfile(path):
    """Test whether a path is a regular file"""
    try:
        st = os.stat(path)
    except (OSError, ValueError):
        return False
    return stat.S_ISREG(st.st_mode)

def islink(path):
    """Test whether a path is a symbolic link"""
    try:
        st = os.lstat(path)
    except (OSError, ValueError, AttributeError):
        return False
    return stat.S_ISLNK(st.st_mode)


**Identifying TOCTOU bug in token handling**
**Clarifying receipt and SHA verification status**
**Confirming receipt absent in initial commit**
**Verifying ledger mode and output directories**
**Assessing concurrency and temp file safety**
**Verifying file and directory permission handling**
**Assessing atomic write safety and cleanup risks**
**Identifying symlink and mount boundary blockers**
**Detecting parent symlink retarget replacement blocker**
**Listing issue severity levels**
**Reconciling and updating issue statuses**
**Confirming scan blocker and surrogate status**
**Verifying source and ledger hash consistency**
**Checking ledger and Git mode differences**
exec
/bin/zsh -lc "nl -ba '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' | sed -n '1,230p'
nl -ba '_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md' | sed -n '23,52p'
nl -ba '_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md' | sed -n '121,136p'
nl -ba '_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md' | sed -n '195,212p'
nl -ba '_bmad-output/审查/G4-9-evidence/grep-selfattest.txt' | sed -n '1,52p'
nl -ba '_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt' | sed -n '10,20p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
     1	{
     2	 "card": "CARD-G4-9",
     3	 "generated_at": "2026-08-28T13:12:17.818410+00:00",
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
    37	| Codex 复审 round-2 | **仍阻断**（10/13 CLOSED；BLOCKER-1/HIGH-1/HIGH-3 未真正闭合 + 3 新 LOW）。同时独立复算确认：67ccebe1 冻结生效、92 条数字与 6/29 重复簇全部可复算 | `_bmad-output/审查/codex-review-CARD-G4-9-round2.md`（codex 被 cyber 误拦，内容由 stdout 抢救存档） |
    38	| round-2 findings 逐条整改 | **6/6 完成**：inode 身份守卫封 hardlink+大小写别名 / full_body 长度门+anomaly 前置 / 不可读根 exit 2+symlink 逃逸拒采信 / 3 新 LOW。5 条新负例实测全过、正例无回归、数字仍逐项一致 | 报告 §7/§7c + `grep-selfattest.txt` |
    39	| Codex 复审 round-3 | **仍阻断**（4/6 CLOSED；BLOCKER-1/HIGH-3 判 PARTIAL + 1 新 MEDIUM + 2 新 LOW）。同时确认：HIGH-1 与三条 LOW 已闭合、台账数字有效且与 commit 字节一致 | `_bmad-output/审查/codex-review-CARD-G4-9-round3.md` |
    40	| round-3 findings 逐条整改 | **6/6 完成**：transcript 并入保护集 / O_NOFOLLOW+fstat 消 TOCTOU / os.walk 替 glob（不跟随目录 symlink+遍历错误显式捕获）/ 不可读候选 fail-closed / JSONL 严格 LF 分帧 / 非 dict 归 unparseable。6 条新反例实测全过、数字第三次不变 | 报告 §7d + `grep-selfattest.txt` |
    41	| Codex 复审 round-4 | **仍阻断**（1/6 CLOSED；2 新 BLOCKER + 1 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round4.md` |
    42	| round-4 findings 逐条整改 | **9/9 完成**：全候选入保护集 / 读侧 fd 身份消源侧 TOCTOU / 新增 unverifiable 第四态 / FIFO 设备门 / strict UTF-8 / 3 条错型与边界 LOW / provenance receipt。5 条新反例实测全过；第四次全量重跑数字仍不变 | 报告 §7e + `grep-selfattest.txt` |
    43	| Codex 复审 round-5 | **仍阻断**（3/8 CLOSED；2 BLOCKER + 2 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round5.md` |
    44	| round-5 findings 逐条整改 | **9/9 完成**：先扫描后判定（冲突候选亦入保护集）/ QA DB fd 身份+复核 / 可见性优先于 anomaly / fchmod 后置于碰撞检查 / QA DB 特殊文件门 / no_token 归 unverifiable / 3 条 LOW。6 条新反例实测全过；第五次全量重跑数字仍不变 | 报告 §7f |
    45	| Codex 复审 round-6 | **6/9 CLOSED**（visibility 优先/fchmod 顺序/no_token 语义/3 条 LOW 已闭合）；剩 2 BLOCKER + 1 MEDIUM 揭示保护集**依赖枚举完整性**的架构缺陷 + 3 新发现 | `_bmad-output/审查/codex-review-CARD-G4-9-round6.md` |
    46	| round-6 findings 整改 | **架构级修复 + 6 项**：新增不依赖枚举的**路径层防御**（--out 禁落 transcripts 根内 / 禁等于任一输入 realpath）、QA DB 验证 fd 保持打开至复核完毕、no_token 亦扫描、证据包重生成、ledger 冲突原因自描述、lone surrogate 回退。反例实测：0333 隐藏目录内 transcript 作 --out → exit 2 完好 | 报告 §7g |
    47	| Codex 复审 round-7 | **关键裁定分离**："92 条冻结 ledger **可以采信**；生成器与 UAT 的纯只读安全声明不可验收"——卡面 census 判据已满足，阻断全在工具安全承诺侧。1 BLOCKER（大小写别名根，无需竞态）+ 4 项路径 TOCTOU + 1 MEDIUM（非原子写）+ 2 LOW | `_bmad-output/审查/codex-review-CARD-G4-9-round7.md` |
    48	| round-7 findings 整改 | **架构级第二次修复**：写出改 O_EXCL 临时文件+fsync+os.replace（**全文再无 ftruncate 调用**），五项绕过整类失效；containment 改 inode 逐级比较（normcase 在 POSIX 是恒等函数，我的假设错了）；扫描受阻直接拒绝写出。实测：根外 hardlink 指向根内 transcript 作 --out → 源内容完好 | 报告 §7h |
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


