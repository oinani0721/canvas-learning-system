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
session id: 01a048eb-c5da-75b3-8a23-94664edbc030
--------
user
CARD-G4-16 round-5 终裁确认（静态审阅 + 只读复算，禁改任何文件）。你 round-4 裁定 6/7 CLOSED，唯一 NOT-CLOSED 是 MEDIUM-5『测试 provenance 的重放 recipe 不确定』——metadata 保留 <out> / <同两文件> 占位符（原样 zsh -n exit 1），after 绑定会漂移的 HEAD。开发方以 commit 94b420ff 整改：
1. _bmad-output/审查/G4-16-evidence/test-run-metadata.txt 的四条命令改为**字面可粘贴形式**（绝对路径、无占位符），逐条 zsh -n 通过；③ 归一化 diff 已实证复跑为空。
2. after 的运行树绑定**固定 commit 73102875**（并附证：两个 py 文件在 73102875 与 fce0d8a2 之间 git diff 为空、blob 同为 73579b22，故绑定固定 SHA 与捕获时状态一致）。
3. 补『复跑后 git checkout HEAD 恢复』步骤，避免残留。
4. 两条 LOW 如实标注：『完整 traceback』实为 pytest.ini 配置下的 --tb=short 输出（已在 metadata 注明）；live-distribution-and-value-grep.txt 为格式化展示而非原始 stdout（已在文件顶部声明为启发式辅助视图）。

请复核：(a) 四条命令是否真的可原样复跑（zsh -n + 语义）；(b) 运行树绑定是否确定（73102875 与后续 commit 对这两个 py 文件确无差异）；(c) 两份完整 stdout 与 metadata 声明是否自洽、归一化是否掩盖实质差异；(d) 铁律复验：git diff 37387a86..HEAD 对 backend/app/services/supplementary_reranker.py 与 supplementary_search_service.py 是否仍为注释-only（无属性 AST 相等）、exam_board/whiteboard 隔离面零改动、落点测试 before/after 失败节点集合仍相同；(e) 报告 _bmad-output/审查/G4-16-doc-type-census-2026-08-28.md 的 18 文件 146 行枚举（pinned git grep @37387a86）与六取值裁定是否仍与代码实况一致。

给出最终裁定：**CARD-G4-16 是否可验收**。若可请明确写出『CARD-G4-16 可验收』；若仍阻断只列必须再做项。
**Planning extensive read-only audit**
**Planning multi-track static audit**
**Inspecting all tools for graphiti**
codex
我会按终裁标准做独立只读复算，不把 round-4 结论或开发方自述当作证据。先核对历史审计规程与仓库边界，再并行审查：重放命令/固定 SHA、stdout 与归一化、铁律隔离面、18 文件 146 行 census；全程不改文件。
**Searching for graph-related tools**
**Noting Graphiti tool unavailability**
**Planning read-only memory recall**
exec
/bin/zsh -lc 'rg -n -i "CARD-G4-16|G4-16|doc-type census|round-4|73102875|94b420ff|37387a86|supplementary_reranker|supplementary_search_service" /Users/Heishing/.codex/memories/MEMORY.md' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 exited 1 in 0ms:
**Searching MEMORY.md for audit terms**
exec
/bin/zsh -lc 'rg -n -i "canvas-adversarial-audit|adversarial|exact-object|annotation-truth|evidence-first|read-only" /Users/Heishing/.codex/memories/MEMORY.md' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
2:scope: Evidence-first audit of project readiness plus a bounded 24-hour writer/reviewer orchestration design. The frozen runbook supports only a Bootstrap-Prep authorization request, not execution.
5:## Task 1: Full-project adversarial audit and productivity direction, partial
9:- rollout_summaries/2026-08-19T18-23-31-2Aoh-canvas_learning_system_adversarial_audit_and_24h_orchestrati.md (cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output, rollout_path=/Users/Heishing/.codex/sessions/2026/08/20/rollout-2026-08-20T02-23-31-01a01b43-9daa-7ef1-8e35-587f59df3ec1.jsonl, updated_at=2026-08-24T13:41:20+00:00, thread_id=01a01b43-9daa-7ef1-8e35-587f59df3ec1, outcome=partial; audit and plan only)
19:- rollout_summaries/2026-08-19T18-23-31-2Aoh-canvas_learning_system_adversarial_audit_and_24h_orchestrati.md (cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output, rollout_path=/Users/Heishing/.codex/sessions/2026/08/20/rollout-2026-08-20T02-23-31-01a01b43-9daa-7ef1-8e35-587f59df3ec1.jsonl, updated_at=2026-08-24T13:41:20+00:00, thread_id=01a01b43-9daa-7ef1-8e35-587f59df3ec1, outcome=success; PASS_FOR_BOOTSTRAP_PREP_REQUEST only)
35:- Use official Codex app-server/subagents, Claude Goals/Agent SDK only in permitted phases, and a non-LLM supervisor. Third-party orchestration plugins may notify or show a read-only dashboard but must not control authorization, evidence, or merging. [Task 2]
72:- The user required “编辑前等待并验证 design-claude.json…否则输出 A4_DESIGN_DIVERGENCE 并停止” -> remain read-only until the exact handoff exists and matches base/verdict/recommendation. [Task 1]
88:# Task Group: Canvas Learning System GOV01 exact-object and CACHE-PREP atomicity audit
89:scope: Isolated, read-only verification of GOV01 bundle chains and static exact-object audit of CACHE-PREP-V1 ADOPT/live-cache atomicity.
128:# Task Group: Canvas Learning System Phase 0A annotation-truth governance ready queue
129:scope: Read-only, fail-closed planning for GOV-01-VERIFIED and A01→A02→A03. It is a governance handoff, not execution authority.
140:- GOV-01-VERIFIED, Phase-0A, A01, A02, A03, annotation-truth-ledger-v2, AtomicAnnotation, boundary receipt, scanner, [HANDOFF:CODEX-PHASE0A-READY]
155:# Task Group: Canvas Learning System P1-05/P1-01/P1-08 adversarial security review
156:scope: Read-only, parallel audit of vault admission/indexing, Graphiti quarantine isolation, SnapshotV3, and recovery-anchor closure claims.
159:## Task 1: P1-05c/P1-01/P1-08 parallel adversarial review, closure rejected
163:- rollout_summaries/2026-08-17T01-56-07-ZNCd-agents_guide_and_p1_05c_adversarial_audit.md (cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output, rollout_path=/Users/Heishing/.codex/sessions/2026/08/17/rollout-2026-08-17T09-56-07-01a00d6e-ea40-70a1-a23c-d51342eeeacd.jsonl, updated_at=2026-08-19T17:56:56+00:00, thread_id=01a00d6e-ea40-70a1-a23c-d51342eeeacd, outcome=partial; final read-only verdict)
169:## Task 2: P1-05b five-question adversarial audit, reproducible bypasses
173:- rollout_summaries/2026-08-19T14-44-08-upza-p1_05b_adversarial_review_finds_admission_quarantine_snapsho.md (cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output, rollout_path=/Users/Heishing/.codex/sessions/2026/08/19/rollout-2026-08-19T22-44-08-01a01a7a-c47f-70e2-8e5e-524e1591da78.jsonl, updated_at=2026-08-19T15:12:50+00:00, thread_id=01a01a7a-c47f-70e2-8e5e-524e1591da78, outcome=partial; detailed counterexamples)
182:- Respect read-only task-book boundaries, WT/MAIN labels, explicit `UNVERIFIABLE`, and no raw-vault access; do not fix code in the audit. [Task 1]
186:- Related skill: skills/canvas-adversarial-audit/SKILL.md. P1-05/P1-01/P1-08 remained STILL-OPEN; F-02 tombstone filtering and F-05 live resilience were closed. Rejected vault inputs must show zero open/hash/index/write. [Task 1][Task 2]
203:- rollout_summaries/2026-08-17T01-56-07-ZNCd-agents_guide_and_p1_05c_adversarial_audit.md (cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output, rollout_path=/Users/Heishing/.codex/sessions/2026/08/17/rollout-2026-08-17T09-56-07-01a00d6e-ea40-70a1-a23c-d51342eeeacd.jsonl, updated_at=2026-08-19T17:56:56+00:00, thread_id=01a00d6e-ea40-70a1-a23c-d51342eeeacd, outcome=success)

**Reviewing SKILL.md for usage explanation**
codex
我将沿用记忆库中的 Canvas 对抗审计规程，因为这次是闭环终裁：结论必须来自固定对象、可复现命令与生产落点证据，并明确区分报告声明和独立复算。该规程只会收紧取证，不会扩展范围或产生写入。当前会话未暴露 `graphiti-canvas` 的 `search_memory_facts` 工具；我会记录这一工具可用性限制，但继续用本地固定提交证据完成审阅。
exec
/bin/zsh -lc "sed -n '155,190p' /Users/Heishing/.codex/memories/MEMORY.md && wc -l /Users/Heishing/.codex/memories/skills/canvas-adversarial-audit/SKILL.md && sed -n '1,240p' /Users/Heishing/.codex/memories/skills/canvas-adversarial-audit/SKILL.md" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
# Task Group: Canvas Learning System P1-05/P1-01/P1-08 adversarial security review
scope: Read-only, parallel audit of vault admission/indexing, Graphiti quarantine isolation, SnapshotV3, and recovery-anchor closure claims.
applies_to: cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output; reuse_rule=revalidate SHA, CI, actual call sites, and live Neo4j state in the target checkout.

## Task 1: P1-05c/P1-01/P1-08 parallel adversarial review, closure rejected

### rollout_summary_files

- rollout_summaries/2026-08-17T01-56-07-ZNCd-agents_guide_and_p1_05c_adversarial_audit.md (cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output, rollout_path=/Users/Heishing/.codex/sessions/2026/08/17/rollout-2026-08-17T09-56-07-01a00d6e-ea40-70a1-a23c-d51342eeeacd.jsonl, updated_at=2026-08-19T17:56:56+00:00, thread_id=01a00d6e-ea40-70a1-a23c-d51342eeeacd, outcome=partial; final read-only verdict)

### keywords

- P1-05c, P1-05, P1-01, P1-08, check_vault_path, vault_index_orchestrator, LanceDB, Graphiti, DEFAULT_GROUP_ID, SnapshotV3, CURRENT_TASK.md

## Task 2: P1-05b five-question adversarial audit, reproducible bypasses

### rollout_summary_files

- rollout_summaries/2026-08-19T14-44-08-upza-p1_05b_adversarial_review_finds_admission_quarantine_snapsho.md (cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output, rollout_path=/Users/Heishing/.codex/sessions/2026/08/19/rollout-2026-08-19T22-44-08-01a01a7a-c47f-70e2-8e5e-524e1591da78.jsonl, updated_at=2026-08-19T15:12:50+00:00, thread_id=01a01a7a-c47f-70e2-8e5e-524e1591da78, outcome=partial; detailed counterexamples)

### keywords

- P1-05b, symlink_escape, casefold, vault_backfill, lancedb_client, quarantine__p105b, search_nodes, read_node_tips, manifest-v3, NaN

## User preferences

- “启动并行 agent 进行对抗性审查” -> use independent evidence tracks and cross-check severity; every finding needs `file:line`, reproduction path/result, severity, conflict explanation, PASS/PARTIAL/FAIL, and limits. [Task 1][Task 2]
- Respect read-only task-book boundaries, WT/MAIN labels, explicit `UNVERIFIABLE`, and no raw-vault access; do not fix code in the audit. [Task 1]

## Reusable knowledge

- Related skill: skills/canvas-adversarial-audit/SKILL.md. P1-05/P1-01/P1-08 remained STILL-OPEN; F-02 tombstone filtering and F-05 live resilience were closed. Rejected vault inputs must show zero open/hash/index/write. [Task 1][Task 2]
- Reproduced: `vault/raw/escape.md -> /outside/secret.md` was counted by `backfill_vault(..., execute=False)`; case-sensitive `fnmatch` admitted `.CLAUDE/SKILL.md` and `raw/claude.md`. Edge filtering alone was insufficient because exact readers/node search could cross Graphiti groups. [Task 2]
- SnapshotV3 needs invalid/future same-generation self-healing, extra-field, strict-type, huge finite mastery, and identity/length collision coverage. [Task 1][Task 2]

## Failures and how to do differently
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

**Preparing repository inspection and delegation**
**Gathering baseline repository information**
只读终裁；四条独立证据轨并行，最后由主审交叉复算关键闭环。
  → 固定 checkout、提交对象、审计边界与证据文件清单
  • 复核四条 replay recipe 的 zsh 语法、语义与固定 SHA 绑定
  • 复核 stdout、metadata、归一化差异与失败节点集合
  • 复核注释-only、AST、隔离面和 18 文件 146 行 census/六取值
  • 交叉核验所有结论并给出唯一终裁
mcp: sequential-thinking/sequentialthinking started
mcp: sequential-thinking/sequentialthinking (completed)
exec
/bin/zsh -lc "pwd; git status --short --branch; git rev-parse HEAD; git log --oneline --decorate -12; rg --files -g 'AGENTS.md' -g '"'!node_modules'"' -g '"'!frontend/node_modules'"'; rg --files _bmad-output/审查/G4-16-evidence; ls -l _bmad-output/审查/G4-16-evidence _bmad-output/审查/G4-16-doc-type-census-2026-08-28.md" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
## card/s5-census
?? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-16-round5.md"
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
5e9e90b01d5515bc341dd9058f8c7242c9a692e4
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
5e9e90b0 (HEAD -> card/s5-census) docs(census): G4-9 Codex round-13 终裁 — 三层全 PASS 可验收 [BATCH-2026-08-28-第五批 / CARD-G4-9]
9104495b docs(census): receipt 补 round-12 commit [BATCH-2026-08-28-第五批 / CARD-G4-9]
543e8a34 docs(census): G4-9 round-12 最后两条措辞整改 [BATCH-2026-08-28-第五批 / CARD-G4-9]
05c85324 docs(census): receipt 补 round-11 commit [BATCH-2026-08-28-第五批 / CARD-G4-9]
f4112c2c fix(census): G4-9 round-11 解阻整改 — 残留声明清除 + 测试补强 [BATCH-2026-08-28-第五批 / CARD-G4-9]
f1828f9f docs(census): receipt 补 round-10 commit [BATCH-2026-08-28-第五批 / CARD-G4-9]
dfbe70c7 fix(census): G4-9 round-10 解阻整改 — 声明彻底收敛 + 测试如实标注 [BATCH-2026-08-28-第五批 / CARD-G4-9]
a775f80d docs(census): receipt 补 round-9 commit [BATCH-2026-08-28-第五批 / CARD-G4-9]
6b8debee fix(census): G4-9 round-9 名实一致 + 只读契约回归测试 + 声明有界化 [BATCH-2026-08-28-第五批 / CARD-G4-9]
2cdf77a4 docs(census): receipt 补 round-8 commit [BATCH-2026-08-28-第五批 / CARD-G4-9]
af251e4a fix(census): G4-9 Codex round-8 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9]
85dd1c8f docs(census): receipt 补 round-7 commit [BATCH-2026-08-28-第五批 / CARD-G4-9]
_bmad-output/审查/G4-16-evidence/live-distribution-and-value-grep.txt
_bmad-output/审查/G4-16-evidence/baseline-before-edits.txt
_bmad-output/审查/G4-16-evidence/test-run-metadata.txt
_bmad-output/审查/G4-16-evidence/pytest-before-full-stdout.txt
_bmad-output/审查/G4-16-evidence/after-edits.txt
_bmad-output/审查/G4-16-evidence/pytest-after-full-stdout.txt
_bmad-output/审查/G4-16-evidence/doc_type-146-occurrences@37387a86.txt
-rw-r--r--@ 1 Heishing  staff  21930 Aug 28 19:46 _bmad-output/审查/G4-16-doc-type-census-2026-08-28.md

_bmad-output/审查/G4-16-evidence:
total 128
-rw-r--r--@ 1 Heishing  staff   1124 Aug 28 19:14 after-edits.txt
-rw-r--r--@ 1 Heishing  staff   1124 Aug 28 17:07 baseline-before-edits.txt
-rw-r--r--@ 1 Heishing  staff  19403 Aug 28 17:32 doc_type-146-occurrences@37387a86.txt
-rw-r--r--@ 1 Heishing  wheel   1509 Aug 28 19:28 live-distribution-and-value-grep.txt
-rw-r--r--@ 1 Heishing  staff   9957 Aug 28 19:27 pytest-after-full-stdout.txt
-rw-r--r--@ 1 Heishing  staff   9957 Aug 28 19:27 pytest-before-full-stdout.txt
-rw-r--r--@ 1 Heishing  staff   4399 Aug 28 19:45 test-run-metadata.txt

**Planning read-only agent subtasks**
**Assessing read-only command simulation**
**Planning environment for no-write testing**
**Evaluating non-mutating test replay options**
**Planning read-only test verification via git pipes**
**Planning full metadata report inspection**
codex
基线已固定：当前 checkout 为 `5e9e90b0`，且已有一个与本轮同名的未跟踪 review 文件；它在我开始前就存在，我不会读取、覆盖或清理。三个并行轨已启动，我在主轨独立复算注释-only/AST、隔离面与提交链，并会复开关键证据做交叉确认。
exec
/bin/zsh -lc 'nl -ba _bmad-output/审查/G4-16-evidence/test-run-metadata.txt; nl -ba _bmad-output/审查/G4-16-doc-type-census-2026-08-28.md' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
     1	== G4-16 落点测试完整 provenance（round-4 整改：命令字面可粘贴复跑 + 运行树绑定固定 commit）==
     2	
     3	背景：round-1/2 只存 FAILED 节点摘要；round-3 判定"历史 stdout 不可事后补造"属实，故
     4	重做了一次可复验完整捕获；round-4 指出重放 recipe 仍含占位符且 after 绑定漂移的 HEAD。
     5	本版命令**全部字面、无占位符、绑定固定 commit**，可原样粘贴复跑（zsh -n 已校验）。
     6	
     7	--- 运行树绑定（关键：两个 py 文件在 73102875 与 fce0d8a2 之间字节未变，blob 同为 73579b22）
     8	before 文件版本 commit: 37387a86（第五批开工基线）
     9	after  文件版本 commit: 73102875（捕获当时的 HEAD；其后 fce0d8a2 未触碰这两个文件，git diff 为空）
    10	Python: Python 3.14.4
    11	pytest 配置: backend/pytest.ini（含 addopts，故实际输出为 --tb=short 形式的完整失败节
    12	  报告，非 --tb=long；"完整"指未经 grep 过滤地保存了该配置下的全部 stdout+stderr）
    13	
    14	--- ① before 捕获（可原样粘贴复跑）
    15	cd "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census" && git checkout 37387a86 -- backend/app/services/supplementary_reranker.py backend/app/services/supplementary_search_service.py && cd backend && .venv/bin/pytest tests/unit/test_supplementary_reranker.py tests/unit/test_supplementary_search_service.py -q --no-header > "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-evidence/pytest-before-full-stdout.txt" 2>&1; echo "exit_code=$?" >> "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-evidence/pytest-before-full-stdout.txt"
    16	
    17	--- ② after 捕获（可原样粘贴复跑）
    18	cd "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census" && git checkout 73102875 -- backend/app/services/supplementary_reranker.py backend/app/services/supplementary_search_service.py && cd backend && .venv/bin/pytest tests/unit/test_supplementary_reranker.py tests/unit/test_supplementary_search_service.py -q --no-header > "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-evidence/pytest-after-full-stdout.txt" 2>&1; echo "exit_code=$?" >> "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-evidence/pytest-after-full-stdout.txt"
    19	
    20	--- ③ 归一化对照（可原样粘贴复跑；两条规则=内存地址与耗时）
    21	diff <(sed -E 's/0x[0-9a-f]+/0xADDR/g; s/in [0-9]+\.[0-9]+s/in T.TTs/g' "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-evidence/pytest-before-full-stdout.txt") <(sed -E 's/0x[0-9a-f]+/0xADDR/g; s/in [0-9]+\.[0-9]+s/in T.TTs/g' "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-evidence/pytest-after-full-stdout.txt")
    22	
    23	--- ④ 复跑后请恢复工作区（避免留下 checkout 残留）
    24	cd "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census" && git checkout HEAD -- backend/app/services/supplementary_reranker.py backend/app/services/supplementary_search_service.py
    25	
    26	--- 产物指纹
    27	pytest-before-full-stdout.txt sha256: 42d94922339a0fdb2799017bbf0b1ad02293d3dd1cfa1d91c6fd0a19313109c5
    28	pytest-after-full-stdout.txt  sha256: 4303b0df29b66ef7ef4219626882f3e7c7bde8fd448d6ba350553dab532236cd
    29	两文件 blob: reranker 37387a86=3d8275269213 → 73102875=73579b22f7a5
    30	             search   37387a86=17440e21c01b → 73102875=5ff331040905
    31	两次 exit_code 均为 1（9 条既有失败）；grep 摘要版另存 baseline-before-edits.txt / after-edits.txt
    32	
    33	--- 对照结论
    34	③ 的 diff 为空：两份完整输出经归一化后**逐字节相同**（Codex round-4 独立复算：归一化后双方
    35	均 9912 bytes、sha256 03e576078dbc5c854b1db7695c1a654195afa69f52f5212d79577e491fde84e8）。
    36	未归一化时的全部差异 = 9 处 CPython 对象地址 + 耗时 0.47s→0.45s，与代码语义无关。
    37	即：注释-only 修改对测试输出零影响，9 failed / 102 passed 逐条同节点同顺序。
    38	
    39	--- 既有失败根因（不在本卡范围，归 FU-2）
    40	翻转源 commit fcd34953（RAG-S2 T2 权重方向翻转），测试断言未同步。
     1	# CARD-G4-16 — doc_type 族接线普查与裁定报告
     2	
     3	> **批次**: BATCH-2026-08-28-第五批 / CARD-G4-16（2h · wave 1 · 防暗坑）
     4	> **锚点**: 计划书 L69（§2.3 STILL-OPEN 前半「doc_type 整族未接线」）——G4-12 已收该行后半"指标名实不符"，本卡收 doc_type 消费链本体
     5	> **代码基线**: worktree `card/s5-census` @ **`37387a86`**（全部 file:line 以此 SHA 为准；config.py 同时在他卡编辑面上，行号会漂移——复核请先 checkout 此 SHA）
     6	> **证据包**: `_bmad-output/审查/G4-16-evidence/`（146 行 grep 清单、落点测试 before/after、live 分布实测）
     7	> **执行日期**: 2026-08-28
     8	
     9	---
    10	
    11	## §1 枚举口径与总量
    12	
    13	`git grep -n "doc_type" 37387a86 -- "backend/*.py"` → **18 文件 146 行**（逐行清单：证据包 `doc_type-146-occurrences@37387a86.txt`；**必须用 pinned git grep 复核**——工作树裸 `grep -rn backend` 会扫入 `backend/.venv` 得 30 文件 198 行，Codex round-1 MEDIUM-5）。与勘探预告完全一致。
    14	
    15	**范围声明（Codex round-1 HIGH-4）**：本 census 的对象是 **backend/*.py 中 LanceDB `vault_notes` 行级 `doc_type` 字段**。仓库根 `scripts/migrate_story_frontmatter.py:62` 写 `doc_type: story`、`scripts/sync_links.py:63/:85` 消费 story/epic（行号已按 pinned 37387a86 复核，round-2 LOW 修正）——那是 **BMAD 文档 frontmatter 的同名异物命名空间**，不入 LanceDB、不与本字段互通，不在本卡值域表内（如实登记防混淆）。
    16	
    17	**18 文件角色分布**（行数 = doc_type 出现行数）：
    18	
    19	| 角色 | 文件 | 行数 |
    20	|---|---|---|
    21	| **写侧（唯一写入方）** | `lib/agentic_rag/clients/lancedb_client.py` | 69 |
    22	| 生产消费·检索服务 | `app/services/supplementary_search_service.py` | 5 |
    23	| 生产消费·检索器 | `lib/agentic_rag/retrievers/vault_notes_retriever.py` | 13 |
    24	| 生产消费·隔离面 | `app/services/tool_executor.py` / `app/services/react_agent.py` / `lib/agentic_rag/agent_graph.py` | 3 / 2 / 1 |
    25	| 生产消费·MCP | `app/mcp/tools/note_search_tools.py` | 2 |
    26	| 注释引用（本卡修正对象） | `app/services/supplementary_reranker.py` | 1 |
    27	| 配置/文档注释 | `app/config.py`（:48-50 双层防御注释）/ `app/api/v1/endpoints/metadata.py`（:569 docstring） | 2 / 1 |
    28	| 回归裁判脚本 | `scripts/run_vault_retrieval_regression.py`（:134/:143 污染硬禁类型判定） | 3 |
    29	| 测试契约（7 文件） | `test_rag_p0_doc_type_filter`(20) / `test_rag_stage2_chain_unify_contracts`(9) / `test_rag_stage2_chunk_contracts`(7) / `test_rag_stage2_t6_verification_contracts`(4) / `test_immutable_skip_dirs_contract`(2) / `test_rag_stage2_rerank_contracts`(1) / `test_rag_stage0_contracts`(1) | 44 |
    30	
    31	**写入方论证（Codex round-1 MEDIUM-3/LOW-1 修订）**：`vault_notes` 表的**显式值生产者恰两处**，均在 `lancedb_client.py`——批量索引路径（:1773-1777 推导 → :1795 metadata + :1818 SQL 列）与单文件更新路径（:2058-2062 推导 → :2078 + :2101），两路共用同一推导规则：`frontmatter.type` **直通**（:2740 lower/strip，无白名单——`whiteboard` 即由此直通入库，:2767 只是消费该值做样板剥离，不是推断点）→ 检验白板推断 `exam_board`（:2756）→ 路径启发 `video_transcript`（`_is_video_transcript`）→ 默认 `"note"`。此外存在**通用 sink**：公共 `add_documents()`（:3615）可无校验透传调用方传入的任意 `doc_type`（含 Chroma 迁移脚本内嵌 metadata_json 路径）——静态未发现当前有第三方经此向 `vault_notes` 写第三种值，但"唯一"须限定为"两显式生产者 + 通用 sink 无校验"。多模态 image_ocr 写路径（:1279-1293）**不含 doc_type 字段**——读侧空串回退的真实来源之一。
    32	
    33	## §2 live 分布实测（容器内只读）
    34	
    35	`docker exec` 容器内 lancedb 只读扫描 `canvas_vault_vault_notes`（2203 行，2026-08-28）：
    36	
    37	```
    38	video_transcript 2001 (90.8%) | concept 117 | note 69 | whiteboard 16 | exam_board 0 | 空/自由值 0
    39	```
    40	
    41	## §3 消费链实测
    42	
    43	- **排除过滤（真实消费主链）**：`exclude_doc_types=["whiteboard","exam_board"]` 于 react_agent:115/:124、tool_executor:112/:122、agent_graph:208、supplementary_search_service:834/:849 显式传入，vault_notes_retriever:82 为默认值——共 7 处显式 + 1 处默认，SQL `NOT IN` 落到 lancedb doc_type 列。**边界（Codex round-1 MEDIUM-4）**：该隔离只覆盖默认 Tier-1 路径——`ENABLE_LANCEDB_TIER2_FALLBACK`（默认关闭）开启后 legacy tier-2 直查裸 `vault_notes` 无 doc_type WHERE（supplementary_search_service.py:863），"在库但检索不可见"仅在默认配置下成立（登记 FU-5）。这是检验白板信息隔离（Karpicke 主动回忆）的**读侧第二层防御**（第一层 = config.py 目录黑名单，:48-50 注释如实记录"验收单/_待处理 无 doc_type，单层防御"）。
    44	- **正向过滤（休眠 API）**：`vault_notes_retriever` 的 `doc_type: List[str]` 参数（:100/:143/:191）生产调用 **0 处**（仅 test_rag_p0_doc_type_filter 锁 `_build_where_filters` 契约）——注释自述"未来出题链定向取材 opt-in"，属预留接口非死代码（测试在位防漂移）。
    45	- **material dict 透传（Codex round-1 HIGH-1 修订）**：supplementary_search_service:975 读 `metadata.doc_type`（"" 回退）→ :1047 进 material dict。**生产消费方存在**：MCP `note_search_tools._material_to_item` 的 clean 分支把 `doc_type` 列入 signal_keys 透传进 `NoteResultItem.metadata` 对外输出（note_search_tools.py:289/:385；tainted 分支按契约剔除，test_rag_stage2_chain_unify_contracts:265 锁定）——是**纯透传**（无分支/加权逻辑），此前报告与注释称"0 生产读取方"过强，已修正。原 :1044-1045 注释声称"doc_type=按类型加权与断言用"仍为**名实不符**：加权实际按材料 `source_type` 在 `rerank()` 内 `weights.get` 完成（`get_type_weight` 仅测试调用，Codex round-1 MEDIUM-2 修订），与 doc_type 无关。
    46	- **裁判消费**：run_vault_retrieval_regression:134/:143 以 doc_type ∈ 硬禁集（whiteboard/exam_board 类）判定检索污染——回归门真实消费方。
    47	
    48	## §4 六取值逐个裁定（接线 / 死值）
    49	
    50	| # | 取值 | 写侧 | live 行数 | 读侧消费 | **裁定** |
    51	|---|---|---|---|---|---|
    52	| 1 | `note` | 默认值 + frontmatter（:1773/:2058） | 69 | 不在排除集 → 可检索；测试契约锁定 | **接线** |
    53	| 2 | `video_transcript` | 路径启发（:1774/:2059） | 2001 | 同上；且与并行 source_type=video_transcript 一起驱动 rerank 权重 | **接线** |
    54	| 3 | `whiteboard` | frontmatter `type: whiteboard` 直通（:2740；:2767 仅消费做样板剥离，LOW-1 修订） | 16 | exclude 集 7+1 处消费（隔离第二层）；默认 Tier-1 下在库但检索不可见 = 设计行为（Tier-2 flag 例外见 §3/FU-5） | **接线** |
    55	| 4 | `exam_board` | 检验白板推断（:2756） | 0 | exclude 集同上。live 0 行原因（Codex round-1 HIGH-2 指出原归因不完整，本轮实测坐实）：exam-quick 考察文件写向**可索引**的 `节点/考察-*.md`（exam-quick.ts:39/:75，目录黑名单不拦）——live vault 实测该形态文件 **0 个**；`检验白板/` 目录唯一 1 个 md 则被目录黑名单拦截。0 行 = "无考察文件存在 + 黑名单拦检验白板目录"两因叠加，非纯黑名单 | **接线**（0 行原因已实测坐实，非死值） |
    56	| 5 | `concept` | frontmatter `type: concept` 直通 | 117 | 入库真实 + MCP metadata 透传在位；但**无按 "concept" 特化分支的读侧**——自称消费方 `TYPE_WEIGHTS["concept"]` 实为 **source_type 键**，indexer 永不写 source_type="concept" → **直接 lookup 不可达**；concept 材料命中的权重键由**路径启发的 source_type 独立决定**（普通路径→note 1.0，/videos/ 下→video_transcript 0.75），与 doc_type 无关；聚合面 `get_filter_threshold()` 消费全表 values()（chat.py:428 生产调用），concept=1.0 非最小值、当前不影响阈值（Codex round-1 HIGH-3/MEDIUM-1 修订） | **值接线；权重键=直接 lookup 不可达、聚合可达但非决定项**（注释已修正保键；删键列 FU-1） |
    57	| 6 | 空串/自由值 | image_ocr 路径缺字段 + frontmatter 任意小写串直通（:2740 无白名单；note_search_tools:276 注释自认无枚举校验） | 0 | 读侧 "" 回退（:975）后仅影响透传与 doc_type 过滤；**权重不受影响也不由 doc_type 决定**——source_type 恒独立有值且**按路径二分**：自由值笔记在普通路径→note 1.0、在 `/videos/` 下→video_transcript 0.75；image_ocr 行→0.6（非 DEFAULT 0.5）。（round-1 HIGH-3 + round-2 HIGH-3 修订：原"自由值→note 1.0"的无条件表述已加路径条件） | **值域未闭合**（live 暂 0 行；白名单校验列 FU-3，口径依 G8-1） |
    58	
    59	**grep 复核 0 未裁定残留**：146 行中除上表六值与字段名本身的出现外，无其他 doc_type 取值字面量（TYPE_WEIGHTS 的 lecture_notes/discussion 等 6 个 PRD 档位是 **source_type** 前向兼容键、注释已自述 forward-compat，不属 doc_type 值域；test fixture 的 "lecture"/"discussion" 仅锁 `_build_where_filters` SQL 拼接契约）。
    60	
    61	## §5 ≤1h 轻量处置（本卡完成，注释-only，零行为改动）
    62	
    63	1. `supplementary_reranker.py` `TYPE_WEIGHTS["concept"]`：原注释"派生概念节点 (doc_type=concept) → 用户手写, 最高"名实不符（该键按 source_type 匹配、直接 lookup 永不命中）。**保守方案：改注释保键**——终版注释（经 Codex round-1 修订）如实声明：直接 lookup 不可达（生产加权 = rerank() 内 weights.get，get_type_weight 仅测试调用）、doc_type=concept 笔记的 source_type 由路径启发独立决定（note 或 video_transcript）、聚合面 get_filter_threshold() 可达但 concept=1.0 当前非决定值；删键裁定列 FU-1。
    64	2. `supplementary_search_service.py` :1044 区注释：删去"doc_type=按类型加权与断言用"的错误声明，终版（经 Codex round-1 修订）改为："doc_type 不参与加权（加权按 source_type 走权重表）；生产消费 = MCP note_search_tools 将 clean 材料 doc_type 透传进输出 metadata（纯透传无分支）；另有测试契约锁定 + 定向取材预留"。
    65	
    66	## §6 落点测试 before/after（裁判判据）
    67	
    68	两个落点测试文件 = `tests/unit/test_supplementary_reranker.py` + `tests/unit/test_supplementary_search_service.py`。
    69	
    70	- **基线（动手前存档）**：**9 failed / 102 passed**（`G4-16-evidence/baseline-before-edits.txt`）——全部 9 条在 reranker 文件：TypeWeightsIndexerTransition×2 + TestFilterFloor×4 + TestFilterFloorTaintExclusion×3；search_service 文件 0 失败。勘探预告"约 10 个既有失败"，实测 9，偏差 1 条按实测为准。
    71	- **处置后**：**9 failed / 102 passed**，FAILED 清单逐条 diff 为空 → **零新增失败 PASS**（`after-edits.txt`）。
    72	- ruff check + format 两文件全过。
    73	- **证据绑定（round-1 MEDIUM-5 → round-3 实质闭合）**：round-1/2 只存 FAILED 节点摘要，Codex round-3 判定"历史 stdout 不可事后补造"属实——故本轮**重做了一次可复验的完整捕获**取代历史摘要：用 `git checkout 37387a86 -- <两文件>` 把文件切回基线版**真实重跑**（`pytest-before-full-stdout.txt`，完整 stdout+traceback+exit_code=1），再 `git checkout HEAD -- <两文件>` 重跑（`pytest-after-full-stdout.txt`）。两份完整输出经**内存地址与耗时归一化后逐字节相同**（未归一化时的全部差异 = CPython 对象地址与 pytest 耗时）。metadata 记录两次命令、两文件 blob、Python 版本、两份产物 sha256。
    74	- **取值字面量证据（round-2 新 MEDIUM → round-3 补完）**：`live-distribution-and-value-grep.txt` 的字面量 grep 是**启发式辅助视图**（含 `"doc_type"`/`"file_path"` 等假阳性，非精确全集）；六值全集的权威依据是 §1/§4 的逐点人工裁定 + pinned 146 行清单。round-3 整改：两条生成命令改为**无占位符、可直接复跑**（docker 一行式 + `git grep` pinned 37387a86，`zsh -n` 语法校验通过），扫描结果随文件重新实跑落盘。
    75	
    76	**9 条既有失败根因方向**（登记入 FU-2，本卡不修）：测试仍按 2026-05-12 设计断言 `note→0.7 中档`（test :579 docstring 自述），而 RAG-S2 T2（2026-08-09）已把 note/concept 翻转为 1.0（权重方向"手写最高"）且 rerank_score 计算随之变化 → FilterFloor 族的 0.42 过滤阈值场景不再触发。属"生产权重翻转未同步测试"的陈债（Codex 独立溯源到翻转 commit `fcd34953`，并确认 floor 用例修法应调输入使 floor 继续触发、不应放宽预期），与本卡注释修正无关（before/after 失败节点全等自证）。
    77	
    78	## §7 follow-up 登记（超出本卡预算项，显式移交）
    79	
    80	| # | 事项 | 建议归属 |
    81	|---|---|---|
    82	| FU-1 | `TYPE_WEIGHTS["concept"]` 删键：**非绝对死键**（get_filter_threshold 聚合消费全表 values()，chat.py:428）——删键前须断言阈值不漂移 + 补"concept 材料按 source_type 命中权重"回归断言 | 检索质量后续卡（与 FU-2 同修最经济） |
    83	| FU-2 | 落点测试 9 条既有失败：按 RAG-S2 T2 翻转后的权重表重写断言（或裁定翻转错误回滚——需检索质量数据裁决，本卡无权代裁） | 检索质量后续卡 |
    84	| FU-3 | doc_type 枚举白名单校验（写侧 :2740 frontmatter 直通 + note_search_tools 无枚举）：**枚举口径依 G8-1 raw/wiki/schema 角色台账定版后落地**，本卡不代 G8-1 冻结值域 | G8-1 及其后续 |
    85	| FU-4 | image_ocr 写路径补 doc_type 字段（当前缺字段 → 读侧空串回退），随 FU-3 白名单一并定值 | 同 FU-3 |
    86	| FU-5 | `ENABLE_LANCEDB_TIER2_FALLBACK`（默认关）开启后 tier-2 直查绕过 doc_type 排除（supplementary_search_service.py:863）——检验白板隔离在该配置下失效，需补 tier-2 侧 WHERE 或在 flag 文档标注隔离代价 | 隔离面后续卡（本卡铁律禁改隔离面，仅登记） |
    87	
    88	## §8 G8-1 台账对齐条目（软依赖注记）
    89	
    90	供 G8-1 收录：`doc_type` = LanceDB 行级**文档角色** schema 字段；权威值域现状 = {note, video_transcript, whiteboard, exam_board, concept} + 未闭合 frontmatter 直通面；写入方 = lancedb_client **两显式生产者**（批量/单文件）+ `add_documents()` 无校验通用 sink（round-2 MEDIUM-3：摘要与 §1 口径统一，不得退回"唯一"）；消费主链 = 检验白板隔离排除集 + 回归污染裁判；与 source_type（内容来源形态：note/video_transcript/image_ocr/neighbor_expansion）**字段职责与赋值链分离**（doc_type 主要来自 frontmatter 直通+推断；source_type 在 vault 笔记索引路径为路径启发二分 note/video_transcript，另有 image_ocr 的**显式赋值**与 neighbor_expansion 的**运行期赋值**——round-2 修正"纯路径启发"的不实表述；二者共享 `_is_video_transcript` 但互不复制取值），G4-16 前的注释曾将二者混同（已修正）。命名与取值最终口径以 G8-1 台账为准。
    91	
    92	## §9 Codex round-1 整改记录（FAIL → 全项整改）
    93	
    94	Codex round-1 终裁 FAIL（0 BLOCKER / 4 HIGH / 5 MEDIUM / 1 LOW），同时确认：两文件与 HEAD 的无属性 AST 完全相等（注释-only 铁律 PASS）、隔离面零改动 PASS、9 条既有失败根因归因 PASS（溯源 `fcd34953`）、pinned git grep 18/146 复算 PASS。逐条整改：
    95	
    96	- **HIGH-1（遗漏 MCP 生产消费方）**：§3 与 supplementary_search_service 注释改为如实声明 note_search_tools:289/:385 透传消费；"0 生产读取方"表述撤回。
    97	- **HIGH-2（exam_board live=0 归因）**：本轮补实测——live vault `节点/考察-*.md` 实存 0 个 + `检验白板/` 唯一 1 md 被黑名单拦截，两因叠加坐实（§4 行 4 重写，UNVERIFIED 消除）。
    98	- **HIGH-3（六值表混同 doc_type/source_type）**：concept/空串/image_ocr 三处行为结论按 source_type 独立决定改写（§4 行 5/6 + reranker 注释重写）。
    99	- **HIGH-4（根 scripts/ 命名空间）**：§1 增范围声明，BMAD frontmatter `doc_type: story` 同名异物如实登记。
   100	- **MEDIUM-1（非绝对死键）**：get_filter_threshold 聚合可达入注释与 FU-1；裁定改"直接 lookup 不可达、聚合可达非决定项"。
   101	- **MEDIUM-2（get_type_weight 调用链）**：注释与报告改为 rerank() 内 weights.get 为生产路径。
   102	- **MEDIUM-3（通用 sink）**：§1 写入方论证改"两显式生产者 + add_documents 无校验 sink"。
   103	- **MEDIUM-4（Tier-2 旁路）**：§3 边界声明 + FU-5 登记（本卡铁律禁改隔离面）。
   104	- **MEDIUM-5（可复验性）**：枚举命令改 pinned git grep（工作树裸 grep 会扫 .venv 得 30/198 的陷阱已写明）；证据包补 test-run-metadata.txt。
   105	- **LOW-1（whiteboard 来源行号）**：:2740 直通为写侧来源，:2767 为消费点（§1/§4 修正）。
   106	
   107	整改后复跑落点测试：9 failed / 102 passed，失败节点与基线逐条相同——注释修订不改任何行为。
   108	
   109	## §10 Codex round-2 复审整改记录（7/10 CLOSED → 剩余 3 项 + 4 新发现全部整改）
   110	
   111	round-2 确认 HIGH-1/2/4、MEDIUM-1/2/4、LOW-1 共 7 项 CLOSED，并独立复跑坐实三条铁律（AST 全等注释-only、隔离面零改动、9 failed/102 passed 与基线同集合同顺序）。未闭合 3 项 + 新发现 4 条，逐条整改：
   112	
   113	- **HIGH-3 NOT-CLOSED（自由值权重表述仍无条件）**：§4 行 6 曾写"自由值→note 1.0"，但 `/videos/` 下 `type: foo` 的 source_type 按路径变为 video_transcript（0.75）。**整改**：加路径条件二分表述。
   114	- **MEDIUM-3 NOT-CLOSED（§8 摘要自相矛盾）**：§1 已写"两生产者 + 通用 sink"，§8 移交摘要却退回"写入方唯一（双路径）"。**整改**：§8 口径与 §1 统一。
   115	- **MEDIUM-5 NOT-CLOSED（测试 provenance 不足）**：metadata 缺过滤管道说明与 blob 摘要，且 10 行摘要不是所列命令的直接产物。**整改**：metadata 补过滤管道、pytest.ini 影响、源 blob 摘要、exit code；同时**如实声明**两次历史运行的完整 stdout 无法事后补造，可复验的是当前 HEAD 复跑同结果。
   116	- **新 MEDIUM（source_type "纯路径启发"不实）**：image_ocr 为显式赋值、neighbor_expansion 为运行期赋值。§8 已修正。
   117	- **新 MEDIUM（reranker:196 陈旧注释）**：floor 兜底注释仍写 `note=0.7 / 0.5×0.7=0.35` 的历史算例。**整改**：加注 fcd34953 翻转后 note=1.0、该算例为历史情形、floor 机制仍生效、测试重写归 FU-2（仍为注释-only）。
   118	- **新 MEDIUM（字面量 grep 证据假阳性）**：§6 已降级其为启发式辅助视图并补生成命令。
   119	- **新 LOW（根脚本行号）**：按 pinned SHA 修正为 migrate:62 / sync:63/:85。
   120	
   121	## §11 Codex round-3 复审整改记录（5/7 CLOSED → 剩 2 项实质闭合）
   122	
   123	round-3 裁定 5 CLOSED（自由值路径条件 / §8 摘要口径 / source_type 赋值链 / reranker 陈旧算例 / 根脚本行号），三条行为铁律复验通过（AST 全等注释-only、隔离面零改动、失败节点集合相同），阻断点收敛为**证据可复验性**两项：
   124	
   125	- **MEDIUM-5 测试 provenance**：round-3 指出"当前复跑不能补造历史证据"——完全正确。**整改思路改变**：不再试图为历史运行补 provenance，而是**重做一次可复验的完整对照**——把两文件用 git 对象切回 37387a86 真实重跑得 before，切回 HEAD 重跑得 after，两份完整 stdout（含 traceback、exit_code）归一化内存地址与耗时后**逐字节相同**。证据从"声明"变为"可复跑复算"。
   126	- **live/value-grep 命令可执行性**：`<lancedb…>` 占位符 + `zsh -n` 报 unmatched quote + 裸 grep 未绑定 SHA。**整改**：两条命令改写为无占位符完整形式（docker 一行式；`git grep` pinned 37387a86），`zsh -n` 校验通过，结果随文件重新实跑。
   127	
   128	## §12 Codex round-4 复审整改记录（6/7 CLOSED → 剩 1 项闭合）
   129	
   130	round-4 裁定 6/7 CLOSED（含 live/value-grep 命令一项经其**真实复跑成功**转 CLOSED），并独立复算确认：两份 stdout 与 metadata 声明自洽（各 109 行/9957 bytes/111 collected/9 failed/102 passed/exit_code=1）；**归一化未掩盖实质差异**——原始 diff 只有 9 处 CPython 对象地址与 `0.47s→0.45s`，仅应用声明的两条规则后双方均 9912 bytes、sha256 `03e57607…84e8` byte-equal。
   131	
   132	剩余一项及整改：
   133	
   134	- **MEDIUM-5 重放 recipe 不确定 → CLOSED**：metadata 仍保留 `<out>` / `<同两文件>` 占位符（原样 `zsh -n` exit 1），且 after 绑定会漂移的 `HEAD`。**整改**：四条命令全部改为**字面可粘贴形式**（绝对路径、无占位符，逐条 `zsh -n` 通过，③ 归一化 diff 已实证复跑为空），after 的运行树绑定**固定 commit `73102875`**（并附证：两个 py 文件在 `73102875` 与 `fce0d8a2` 之间 `git diff` 为空、blob 同为 `73579b22`，故绑定固定 SHA 与捕获时状态一致）；另补 `git checkout HEAD` 恢复步骤避免复跑残留。
   135	- **新 LOW（"完整 traceback"措辞）**：实为 `pytest.ini` 配置下的 `--tb=short` 输出。→ metadata 已改为"未经 grep 过滤地保存了该配置下的全部 stdout+stderr"并注明 tb 形式。
   136	- **新 LOW（live 证据为格式化展示）**：不阻断，已在该文件顶部声明为"启发式辅助视图 + 结果随文件实跑落盘"，数值/字面量同集经 round-4 复跑确认。

**Investigating metadata and report inconsistencies**
**Clarifying blob consistency and preparing commit analysis**
**Assessing exam_board isolation surface changes**
**Filtering files for rounds 1-4**
exec
/bin/zsh -lc "rg --files _bmad-output/审查 | rg -i 'G4-16'; git log --all --oneline --decorate --topo-order -- _bmad-output/审查/G4-16-evidence/test-run-metadata.txt _bmad-output/审查/G4-16-doc-type-census-2026-08-28.md backend/app/services/supplementary_reranker.py backend/app/services/supplementary_search_service.py; git show --stat --oneline --decorate 94b420ff; git show --name-status --format=fuller 94b420ff" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 108ms:
94b420ff fix(census): G4-16 Codex round-4 重放 recipe 确定化 [BATCH-2026-08-28-第五批 / CARD-G4-16]
fce0d8a2 fix(census): G4-9/G4-16 Codex round-3 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9 / CARD-G4-16]
73102875 fix(census): G4-9/G4-16 Codex round-2 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9 / CARD-G4-16]
e7a480eb docs(census): G4-16 doc_type族接线普查 18文件146行+6取值裁定+注释修正 [BATCH-2026-08-28-第五批 / CARD-G4-16]
28581fff fix(rag): 阶段 2 T6 验证收尾 — HARD-ISO 泄漏封堵 + 审查 findings 处置 (RAG-S2-2026-08-09)
f0934044 feat(rag): 阶段 2 T5 — 链统一 + retrieval_confidence + 降级可见 (RAG-S2-2026-08-09)
5e11ee22 feat(rag): 阶段 2 T4 — 源文件级 dedup + CE 交付门 (RAG-S2-2026-08-09)
fcd34953 feat(rag): 阶段 2 T2 快修批 — 权重方向翻转 + confidence 地基 + 隔离收口 (RAG-S2-2026-08-09)
f9971f2a fix(rag): R1 根因二+三 检索精确性三连修 — 语义过滤终于真实工作 (EPIC1-BMAD-DEV-ASSESS-2026-04-17)
ab1a5d0a fix(backend): P0 批次一 B1+R2+R1+B2 评分复活+隔离+检索止血+tips落桶 (EPIC1-BMAD-DEV-ASSESS-2026-04-17)
79da7460 feat(2.2+2.9 wave-5 stage-c): backend p1 hardening + 跨 vault isolation integration test
ec58ee01 fix(2.2+2.9 wave-3): chatgpt v4 verdict p1 follow-up + claude self-audit f1+f3
f0185804 fix(2.2+2.9 wave-2): chatgpt v2 verdict hotfix p0+p1 全闭口
de0b4a7a fix(2.2+2.9 q1+q2+q3): hotfix 3 领域 p0 + uat + chatgpt prompt
549d5f0d feat(2.2+2.9 T3+T5): rerank engine (type+query+hub) + relationship evidence
c0172693 chore(auto-sync): 6 files, metadata.py
ecf16f2c fix(phase-a0.5): l hook 鉴权 + n subjectresolver 规范 + p supplementary taint 扫描
aef95be7 fix(phase-a0): 修 j pattern 失配 + i tier-2 fallback 0.85 致命止血
c3c06ebd fix(phase-a-t1.6): wikilink anchor 用 raw heading 字面 + display 用 clean 版
275a201f fix(phase-a-t1.5): wikilink 跳转修复 — chunks 派生路径回写 + heading 不 over-strip
98dbc2d6 feat(phase-a-t1.4): rag-as-tool 重构 — claude read 验证 + 动态 top_k + 空文档过滤
01329e75 fix(story-2.2): phase A 5+1 hardening — singleton + ListTablesResponse + 顶级 mount
1a3106c8 fix(story-2.2): phase A hardening — timeout + tier-2 fallback for legacy index
3bb746e5 feat(story-2.2): phase A ship — search_vault_notes MCP 集成 + 三档降级
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
94b420ff fix(census): G4-16 Codex round-4 重放 recipe 确定化 [BATCH-2026-08-28-第五批 / CARD-G4-16]
 .../G4-16-doc-type-census-2026-08-28.md"           |   10 +
 .../G4-16-evidence/test-run-metadata.txt"          |   72 +-
 .../codex-review-CARD-G4-16-round4.md"             | 4936 ++++++++++++++++++++
 ...\272\277\346\231\256\346\237\245-2026-08-28.md" |    2 +
 4 files changed, 4988 insertions(+), 32 deletions(-)
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
commit 94b420ffe63a291b5c20387b07ccda51d0addfd9
Author:     oinani0721 <2272104243@qq.com>
AuthorDate: Fri Aug 28 19:46:21 2026 +0800
Commit:     oinani0721 <2272104243@qq.com>
CommitDate: Fri Aug 28 19:46:21 2026 +0800

    fix(census): G4-16 Codex round-4 重放 recipe 确定化 [BATCH-2026-08-28-第五批 / CARD-G4-16]
    
    round-4 裁定 6/7 CLOSED（含 live/value-grep 经其真实复跑转 CLOSED），并独立
    复算确认归一化未掩盖实质差异（原始 diff 仅 9 处内存地址+耗时；归一化后双方
    9912 bytes sha256 相同 byte-equal）。剩 1 项 MEDIUM-5 整改：test-run-metadata
    四条命令改为字面可粘贴（无占位符，逐条 zsh -n 通过，归一化 diff 已实证复跑
    为空），after 运行树绑定固定 commit 73102875 并附两 py 文件 73102875↔fce0d8a2
    零 diff 佐证；补复跑后恢复步骤；两条措辞 LOW（--tb=short 口径、live 证据为
    格式化展示）一并如实标注。
    
    Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>

M	"_bmad-output/\345\256\241\346\237\245/G4-16-doc-type-census-2026-08-28.md"
M	"_bmad-output/\345\256\241\346\237\245/G4-16-evidence/test-run-metadata.txt"
A	"_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-16-round4.md"
M	"_bmad-output/\351\252\214\346\224\266\345\215\225/UAT-CARD-G4-16-doc_type\346\227\217\346\216\245\347\272\277\346\231\256\346\237\245-2026-08-28.md"

**Planning code diff and AST comparison**
**Designing shell-based AST comparison**
exec
/bin/zsh -lc 'git merge-base --is-ancestor 37387a86 HEAD; echo base_to_head_ancestor_exit=$?; git merge-base --is-ancestor 73102875 HEAD; echo after_to_head_ancestor_exit=$?; git merge-base --is-ancestor 94b420ff HEAD; echo fix_to_head_ancestor_exit=$?; git diff --numstat 37387a86..HEAD -- backend/app/services/supplementary_reranker.py backend/app/services/supplementary_search_service.py; git diff --no-ext-diff --no-textconv --unified=80 37387a86..HEAD -- backend/app/services/supplementary_reranker.py backend/app/services/supplementary_search_service.py; for p in backend/app/services/supplementary_reranker.py backend/app/services/supplementary_search_service.py; do echo "$p"; git rev-parse 37387a86:"$p"; git rev-parse HEAD:"$p"; done' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
base_to_head_ancestor_exit=0
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
after_to_head_ancestor_exit=0
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
fix_to_head_ancestor_exit=0
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
13	3	backend/app/services/supplementary_reranker.py
5	1	backend/app/services/supplementary_search_service.py
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
diff --git a/backend/app/services/supplementary_reranker.py b/backend/app/services/supplementary_reranker.py
index 3d827526..73579b22 100644
--- a/backend/app/services/supplementary_reranker.py
+++ b/backend/app/services/supplementary_reranker.py
@@ -1,257 +1,267 @@
 """Story 2.2+2.9 (merged) Task 3 — 补充材料精排引擎.
 
 PRD §4.1.1 (line 3707-3877): 邻居 / supplementary 候选 N 条 → final_score 综合排序.
 
 Phase 演进（rerank() 签名保持稳定）:
 - T3b (done): TYPE_WEIGHTS + relevance × type_weight 基础排序
 - T3c (本提交): query_overlap 加权 (BM25 via rerank_service)
 - T3d (待续): hub_penalty 衰减 (wikilink_graph_service.get_degree_stats)
 - T3.7+ (待续): chat.py endpoint 把 user_question + mode 传 enrich
 
 当前 final_score 公式:
   final_score = relevance × type_weight + query_overlap × query_overlap_weight
 
 未来 T3d 起:
   final_score = relevance × type_weight + query_overlap × query_overlap_weight - hub_penalty
 
 来源对照（避免膨胀）:
 - type weight: PRD §4.1.1 + Story 2.2 AC #3
 - hub penalty: Story 2.9 AC #2 (log(degree / median + 1))
 - query overlap: Story 2.9 AC #1 (BM25 lexical + 可选 cosine)
 """
 
 from __future__ import annotations
 
 import math
 from typing import Any
 
 import structlog
 
 logger = structlog.get_logger(__name__)
 
 
 # ═══════════════════════════════════════════════════════════════════════════════
 # Type weight table (PRD §4.1.1, frozen 2026-05-11)
 # ═══════════════════════════════════════════════════════════════════════════════
 
 # P0-A 过渡映射 (2026-05-12 hotfix): indexer 当前实际写入的 source_type
 # (lancedb_client.py:1444/1644) 只有 {note, video_transcript, image_ocr}, PRD §4.1.1
 # 6 档分类 (lecture_notes / discussion / ...) 是 indexer 升级目标。如果只保留 PRD
 # 6 keys, 所有真实数据 fallback 到 DEFAULT_TYPE_WEIGHT=0.5 → P0-B filter 0.42 几乎
 # 全删材料。解法: 表里同时包含 PRD 6 档 (forward compat, indexer 升级后立刻可用)
 # 加 indexer 当前真实 3 类 (过渡兜底)。indexer 升级到 PRD 6 档后, 过渡 3 类自然
 # 失去命中, 行为优雅退化。
 TYPE_WEIGHTS: dict[str, float] = {
     # PRD §4.1.1 frozen 2026-05-11 (forward compat for indexer 升级)
     "lecture_notes": 1.0,
     "discussion": 0.9,
     "exam_review": 0.85,
     "wiki_concepts": 0.8,
     "chat_session": 0.7,
     "raw_notes": 0.6,
     # P0-A 过渡 (indexer 升级到 PRD 6 档前的实际命中映射, 2026-05-12 hotfix):
     # RAG-S2 T2 (2026-08-09) 权重方向翻转: 旧值 video_transcript 0.9 > note 0.7
     # 把转录排在手写笔记之上, 与用户初衷相反 (开工基线 handwritten_share
     # @10 = 0.17%)。翻转: 手写/概念笔记最高, 转录居中。
-    "concept": 1.0,  # 派生概念节点 (doc_type=concept) → 用户手写, 最高
+    # G4-16 census (2026-08-28, Codex round-1 修订): 直接 lookup 不可达键 —
+    # 加权按材料 source_type 匹配 (生产路径 = rerank() 内 weights.get;
+    # get_type_weight 仅测试调用), 而 indexer 写入的 source_type 只有
+    # note/video_transcript/image_ocr (运行期另有 neighbor_expansion), 永不产
+    # "concept"; doc_type=concept 笔记的 source_type 由路径启发独立决定
+    # (note 或 video_transcript), 与 doc_type 无关。聚合面 get_filter_threshold()
+    # 消费全表 values() (chat.py 生产调用), concept=1.0 非最小值故当前不影响
+    # 阈值。保守保键防误删, 删键裁定列 follow-up。
+    "concept": 1.0,
     "note": 1.0,  # 普通 vault 笔记 → 用户手写, 最高
     "video_transcript": 0.75,  # 视频 transcript → 素材层, 低于手写
     "image_ocr": 0.6,  # OCR 出来的图片文字 → 同 raw_notes 低档 (准确度有限)
 }
 
 # Unknown / None / empty source_type fallback. Below all canonical (min 0.6) so
 # unknown data surfaces visibly in trace.included.type_weight rather than
 # silently being treated as a canonical category.
 DEFAULT_TYPE_WEIGHT: float = 0.5
 
 
 def get_type_weight(source_type: str | None) -> float:
     """Map source_type to type weight (PRD §4.1.1).
 
     None / empty / unknown values fall back to DEFAULT_TYPE_WEIGHT.
     """
     if not source_type:
         return DEFAULT_TYPE_WEIGHT
     return TYPE_WEIGHTS.get(source_type, DEFAULT_TYPE_WEIGHT)
 
 
 # ═══════════════════════════════════════════════════════════════════════════════
 # Rerank engine (Phase T3b — type weight only; future phases extend final_score)
 # ═══════════════════════════════════════════════════════════════════════════════
 
 
 # Story 2.2 AC #4: "user_question 无时走 Phase 1 默认排序"
 # → query=None / query="" / mode!="solve" 时 query_overlap=0, 仅用 type_weight
 DEFAULT_QUERY_OVERLAP_WEIGHT: float = 0.3
 
 
 def compute_hub_penalty(degree: int, median_degree: float) -> float:
     """Story 2.9 AC #2: hub_penalty = log(degree / median + 1).
 
     Edge cases:
     - degree <= 0 → 0 (孤立节点不该被惩罚)
     - median_degree <= 0 → 0 (空图或单节点图,无 hub 概念)
 
     Formula uses natural log; degree=median yields ln(2)≈0.69, degree=2×median
     yields ln(3)≈1.10. Caller decide whether to apply scale factor.
     """
     if degree <= 0 or median_degree <= 0:
         return 0.0
     return math.log(degree / median_degree + 1.0)
 
 
 # Story 2.2 AC #4 T3.9 filter: 最终 rerank_score 低于
 # (0.70 × min_canonical_type_weight) 的材料不显示。
 DEFAULT_FILTER_QUALITY_RATIO: float = 0.70
 
 
 def get_filter_threshold(quality_ratio: float = DEFAULT_FILTER_QUALITY_RATIO) -> float:
     """T3.9 filter threshold = quality_ratio × min(TYPE_WEIGHTS.values()).
 
     DEFAULT_TYPE_WEIGHT 不参与计算（DEFAULT 表示"未知"应该被压低，
     threshold 用 canonical 最低 raw_notes=0.6 作为可接受质量下限）。
     """
     return quality_ratio * min(TYPE_WEIGHTS.values())
 
 
 def rerank(
     materials: list[dict[str, Any]],
     *,
     query: str | None = None,
     query_overlap_weight: float = DEFAULT_QUERY_OVERLAP_WEIGHT,
     median_degree: float = 0.0,
     type_weights: dict[str, float] | None = None,
     min_score_threshold: float | None = None,
     top_k: int | None = None,
     min_keep: int = 3,
 ) -> list[dict[str, Any]]:
     """Phase T3b+T3c+T3d+T3.9+T3.10: full final_score formula (Story 2.2 AC #4 / 2.9 AC #1+#2).
 
     final_score = relevance × type_weight + query_overlap × query_overlap_weight - hub_penalty
 
     Each material is augmented in-place with four fields (consumed by TraceItem):
     - `rerank_score`: float, the final ordering score
     - `type_weight`: float, weight applied based on `source_type`
     - `query_overlap`: float in [0,1], BM25-normalized lexical overlap
     - `hub_penalty`: float >= 0, log(degree/median + 1) when material has `degree` field
 
     Pipeline order (T3.9 + T3.10 sequence): score → sort → filter → truncate. Sort
     first so threshold cut applies to globally ranked candidates; filter before
     truncate so a high-quality #6 isn't lost behind a marginal-quality #5.
 
     Tie-break: 完全相同 rerank_score 时按 `title` 字典序升序（确定性输出，
     Story 2.2 AC #4 "score 相同 fallback 字典序"）。
 
     Args:
         materials: candidate dicts，至少含 `score` (float, [0,1])、
             `source_type` (str | None)；可选 `degree` (int, 用于 hub_penalty)
         query: user question string. None / 空 → query_overlap=0
         query_overlap_weight: query_overlap 加权系数（默认 0.3，PRD §4.1.1）
         median_degree: degree 基线（来自 wikilink_graph_service.get_degree_stats()
             的 `median`）。0 → hub_penalty 全部为 0（小 vault 场景）
         type_weights: 覆盖默认 TYPE_WEIGHTS（仅测试 / 实验用）
         min_score_threshold: T3.9 filter — 过滤 rerank_score < 此值的材料
             （None = 不过滤；典型值 get_filter_threshold() = 0.42）
         top_k: T3.10 — 截取前 N 条（None = 不截断；典型 Top 5）
         min_keep: P0-B floor — filter 后剩 < min_keep 条 OR 删掉 > 80% candidates
             时, 兜底放弃 filter (改返回未 filter 的 sorted list, 仍 top_k 截断),
             并在第 1 条材料注入 `filter_floor_triggered=True` 供 logger 观测.
             min_keep=0 关闭兜底.
 
     Returns:
         重排后的 list（已 in-place sort + 字段注入；过滤+截断的可能是新 list）
     """
     if not materials:
         return []
 
     weights = type_weights if type_weights is not None else TYPE_WEIGHTS
 
     query_overlaps = _compute_query_overlap(materials, query)
 
     for m, query_overlap in zip(materials, query_overlaps):
         relevance = float(m.get("score", 0.0))
         source_type = m.get("source_type") or ""
         type_weight = weights.get(source_type, DEFAULT_TYPE_WEIGHT)
         degree = int(m.get("degree", 0))
         hub_pen = compute_hub_penalty(degree, median_degree)
 
         m["type_weight"] = type_weight
         m["query_overlap"] = query_overlap
         m["hub_penalty"] = hub_pen
         m["rerank_score"] = relevance * type_weight + query_overlap * query_overlap_weight - hub_pen
 
     materials.sort(
         key=lambda m: (-m["rerank_score"], str(m.get("title", ""))),
     )
 
     # P0-B (2026-05-12 hotfix): 过滤 floor 兜底.
-    # 当 indexer 未升级到 PRD 6 档时, real-world 数据 source_type="note" 命中过渡
-    # 表 0.7, 典型 relevance ~0.5 → final ~0.35 < filter_threshold 0.42 → 全删.
+    # 当时 source_type="note" 命中过渡表 0.7, 典型 relevance ~0.5 → final ~0.35
+    # < filter_threshold 0.42 → 全删。(G4-16 census 2026-08-28 注记: RAG-S2 T2
+    # fcd34953 已把 note 翻转为 1.0, 该算例是历史情形; floor 机制本身仍在生效,
+    # 相关既有失败测试的重写归 FU-2。)
     # 用户原话: "不硬编码 5 条, 把有用的都提供给我"
     # → filter 后剩 < min_keep 或删 > 80% 候选, 视为 threshold 误杀, 自动降级为
     #   不过滤但仍 top_k 截断, 第 1 条注入 filter_floor_triggered=True 供 logger
     #   观察以便调阈值. floor=0 关闭兜底 (现有测试 + 显式 opt-out).
     #
     # P0-3b (2026-05-12 hotfix, ChatGPT v2 fail-closed real): 即使 floor_triggered,
     # 也必须过滤 taint ∈ {review, quarantine} 的材料. floor 初衷是 "保护边缘
     # candidate 不被全删", 但 review/quarantine 是安全审查决定的污染标记, 不应
     # 因 floor 而 backdoor 入选 (兜底也不能让可疑材料绕过审查).
     if min_score_threshold is not None:
         kept = [m for m in materials if m["rerank_score"] >= min_score_threshold]
         n_pre = len(materials)
         n_post = len(kept)
         floor_triggered = False
         if min_keep > 0 and n_pre > 0:
             kill_ratio = 1.0 - (n_post / n_pre)
             if n_post < min_keep or kill_ratio > 0.80:
                 floor_triggered = True
         if floor_triggered:
             logger.warning(
                 "[Rerank] filter_floor_triggered",
                 pre=n_pre,
                 post=n_post,
                 threshold=round(min_score_threshold, 3),
                 min_keep=min_keep,
             )
             # P0-3b: floor 仍 fail-closed 过滤 review/quarantine 材料
             materials = [m for m in materials if m.get("taint") not in {"review", "quarantine"}]
             # 标记兜底, 仍走 top_k
             if materials:
                 materials[0]["filter_floor_triggered"] = True
         else:
             materials = kept
 
     if top_k is not None and top_k >= 0:
         return materials[:top_k]
     return materials
 
 
 def _compute_query_overlap(
     materials: list[dict[str, Any]],
     query: str | None,
 ) -> list[float]:
     """BM25-based query overlap, normalized [0,1] for combine.
 
     Combines title + snippet as the document text (title carries highest signal
     weight via lexical overlap; snippet adds body context).
     """
     if not query or not query.strip():
         return [0.0] * len(materials)
 
     try:
         from app.services.rerank_service import bm25_scores, normalize_to_unit
     except ImportError:
         logger.warning("[Rerank] rerank_service unavailable, skipping query_overlap")
         return [0.0] * len(materials)
 
     docs = [
         " ".join(
             filter(
                 None,
                 [str(m.get("title", "")), str(m.get("snippet", ""))],
             )
         )
         for m in materials
     ]
     raw = bm25_scores(query, docs)
     return normalize_to_unit(raw)
diff --git a/backend/app/services/supplementary_search_service.py b/backend/app/services/supplementary_search_service.py
index 17440e21..5ff33104 100644
--- a/backend/app/services/supplementary_search_service.py
+++ b/backend/app/services/supplementary_search_service.py
@@ -965,94 +965,98 @@ def _normalize_material(raw: dict[str, Any]) -> dict[str, Any]:
 
     复用 react_agent._format_results 的字段提取逻辑（Story 2.1 dad9ed7 通过 ChatGPT 8/10 审计）。
     """
     metadata = raw.get("metadata") or {}
     score = float(raw.get("score", 0.0))
     content = raw.get("content", "") or ""
     # RAG-S2 T2 (2026-08-09): confidence 地基三字段透传 —
     # raw_score(未加权语义分, 权重污染后可回算真实相关度) +
     # rrf/fts 融合信号(区分双通道确认 vs dense-only, 此前 convert 层丢弃)。
     raw_score = raw.get("_raw_score")
     doc_type = metadata.get("doc_type", "") or raw.get("doc_type", "") or ""
     # RAG-S2 T6 审查修复 (2026-08-10): 双通道确认改用 _fts_hit — 旧公式
     # bool(_rrf_score) 名实颠倒: _rrf_score 写给所有融合行 (含 dense-only
     # 甚至 FTS 分支整个挂掉的批次), dense-only 恒 True、真词法命中
     # (FTS-only) 反而 False。现语义 = 出现在 FTS 通道 且 非 FTS-only
     # (vector 亦命中) = 真·双通道确认。仍只做 confidence 遥测, 不进交付门。
     fts_confirmed = bool(metadata.get("_fts_hit")) and not metadata.get("_fts_only")
 
     # 优先 metadata.canvas_file（新 schema），fallback 到顶层 canvas_file（老 schema / tier-2）
     canvas_file = metadata.get("canvas_file", "") or raw.get("canvas_file", "") or ""
     heading = ""
     source_type = "note"
     meta_json_str = metadata.get("metadata_json", "")
     if isinstance(meta_json_str, str) and meta_json_str:
         try:
             meta_parsed = json.loads(meta_json_str)
             if not canvas_file:
                 canvas_file = meta_parsed.get("file_path", "") or ""
             heading = meta_parsed.get("heading", "") or ""
             source_type = meta_parsed.get("source_type", "note") or "note"
         except json.JSONDecodeError:
             pass
 
     # 2026-05-09 P0 fix: chunks/merged.md 派生路径回写到原文件
     canvas_file = _resolve_chunks_to_source_file(canvas_file)
     file_display = canvas_file[:-3] if canvas_file.endswith(".md") else canvas_file
 
     # 2026-05-09 wikilink 跳转修复 (3 agent 实测确认):
     # ⛔ heading anchor 必须**字面 100% 匹配** vault 内文档的 heading
     # - 文档真实 heading: "6.4.1 解决局部最优陷阱的方法 [59:00]()-[01:00]()"
     # - 之前 over-strip [time]() 后剩 "6.4.1 ... 方法 -" → Obsidian 找不到 → 仅跳文件不滚动
     # → heading 字面完整保留（含视频 timestamp 残留），display text 才做清洗供视觉简洁
     raw_heading = heading or ""  # 保留 LanceDB 索引时的原始 heading 字面（与文档一致）
     display_heading = raw_heading
     if display_heading:
         # display text (用户视觉) 仅做清洗：去 [time]() / [[wikilink]] / 末尾空白
         display_heading = re.sub(r"\[\[.*?\]\]", "", display_heading).strip()
         display_heading = re.sub(r"\[.*?\]\(.*?\)", "", display_heading).strip()
         display_heading = re.sub(r"\s+-\s*$", "", display_heading).strip()  # 末尾 ` -` 残留
         display_heading = re.sub(r"^\s+|\s+$", "", display_heading)
     heading = raw_heading  # ⭐ wikilink anchor 用字面 raw heading（保跳转）
 
     # 2026-05-09 wikilink 拼接: anchor 用 raw heading 字面匹配文档，display 用 clean 简洁视觉
     # ⛔ wikilink heading anchor 含 `[time]()` 时 Obsidian wikilink parser 行为未公开
     # 业界备选 (Smart Connections / Khoj): 用 markdown link `[display](file.md#heading)`
     # 当前先试 wikilink 字面 anchor 路径，如 Obsidian 解析仍失败再切 markdown link
     display_text = display_heading or heading or ""
     if file_display and heading and heading != file_display:
         wikilink = f"[[{file_display}#{heading}|{display_text}]]"
         title = display_text
     elif file_display:
         wikilink = f"[[{file_display}]]"
         title = file_display.split("/")[-1]
     else:
         doc_id = raw.get("doc_id", "") or ""
         wikilink = f"[Doc: {doc_id}]" if doc_id else "[unknown]"
         title = doc_id or "未命名片段"
 
     snippet = content[:300]
     if len(content) > 300:
         snippet += "..."
 
     return {
         "title": title,
         "wikilink": wikilink,
         "snippet": snippet,
         "score": score,
         "source_path": canvas_file,
         "source_type": source_type,
         # RAG-S2 T2: confidence 地基 (raw_score=未加权语义分 /
-        # doc_type=按类型加权与断言用 / fts_confirmed=双通道确认)
+        # fts_confirmed=双通道确认)。G4-16 census (2026-08-28, Codex round-1
+        # 修订): doc_type 不参与加权 — 加权按材料 source_type 走
+        # supplementary_reranker 权重表 (rerank() 内 weights.get)。本字段的
+        # 生产消费 = MCP note_search_tools 将 clean 材料的 doc_type 透传进
+        # 输出 metadata (纯透传无分支/加权); 另有测试契约锁定 + 定向取材预留。
         "raw_score": raw_score,
         "doc_type": doc_type,
         "fts_confirmed": fts_confirmed,
     }
 
 
 def _xml_escape(text: str) -> str:
     """最小 XML 安全转义（防止 vault 笔记内容里的 `<` / `&` 破坏 XML 解析）。"""
     if not isinstance(text, str):
         text = str(text)
     return (
         text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("\n", " ")
     )
backend/app/services/supplementary_reranker.py
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
3d82752692135f4352c3094f0d268f6370fb984e
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
73579b22f7a54bc1b3bc4e4e4230c6eadb235b56
backend/app/services/supplementary_search_service.py
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
17440e21c01bcbef5f1abe4f31328f8fd71ad741
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
5ff331040905dda9c8a7c46fc329bc1af56acea4

**Planning AST comparison via subprocess**
**Implementing AST hash command**
exec
/bin/zsh -lc 'for p in backend/app/services/supplementary_reranker.py backend/app/services/supplementary_search_service.py; do echo "$p"; git show 37387a86:"$p" | PYTHONDONTWRITEBYTECODE=1 backend/.venv/bin/python -c '"'import ast,hashlib,sys; tree=ast.parse(sys.stdin.read()); print(hashlib.sha256(ast.dump(tree, include_attributes=False).encode()).hexdigest())'; git show HEAD:\""'$p" | PYTHONDONTWRITEBYTECODE=1 backend/.venv/bin/python -c '"'import ast,hashlib,sys; tree=ast.parse(sys.stdin.read()); print(hashlib.sha256(ast.dump(tree, include_attributes=False).encode()).hexdigest())'; done" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 35ms:
03e79eeabbdfcc1c43087efe5396b171ea622d5bfeed61d8707a5f20c935603a

**Searching round4 review for keywords**
exec
/bin/zsh -lc 'rg -n "隔离面|注释-only|AST|exam_board|whiteboard|失败节点|铁律|37387a86" _bmad-output/审查/codex-review-CARD-G4-16-round4.md | head -n 240; nl -ba _bmad-output/审查/codex-review-CARD-G4-16-round4.md | tail -n 180' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
15:1. MEDIUM-5 测试 provenance → 不再为历史运行辩护，改为**重做可复验完整捕获**：git checkout 37387a86 -- 两个 py 文件后真实重跑得 pytest-before-full-stdout.txt（完整 stdout+traceback+exit_code），再 git checkout HEAD -- 两文件重跑得 pytest-after-full-stdout.txt；两份归一化内存地址(0x…→0xADDR)与耗时后逐字节相同。证据包 test-run-metadata.txt 记录两次命令、两文件 blob、Python 版本、两份产物 sha256。请复核：该做法是否真正提供可复验证据；两份 stdout 与 metadata 声明是否自洽；归一化口径是否掩盖了实质差异（请自己对两份文件做归一化 diff 验证）。
16:2. live-distribution-and-value-grep.txt 命令可执行性 → 两条命令改为无占位符完整形式（docker 一行式 + git grep pinned 37387a86），zsh -n 校验通过，结果随文件重新实跑。请复核命令是否真能复跑出文件所载结果、是否仍有占位符/引号问题/未绑定 SHA。
17:同时复验铁律：git diff 37387a86..HEAD 对 backend/app/services/supplementary_reranker.py 与 supplementary_search_service.py 仍为注释-only（无属性 AST 相等）；隔离面零改动；报告 _bmad-output/审查/G4-16-doc-type-census-2026-08-28.md 的 §1/§4/§8 结论与代码实况一致。逐项 CLOSED/NOT-CLOSED + 总裁定（可验收/仍阻断）+ 新发现分级。若认为已可验收请明确说明。
21:我会按终裁口径做三条独立只读复算：测试 provenance 与归一化 diff、两条 live 命令的实际复跑、代码/隔离面/报告一致性。这里会采用既有的 Canvas 对抗审计流程，因为它要求从原始对象和生产命令自行复算，而不是采信整改报告的自述；全程不改文件。
24:/bin/zsh -lc 'rg -n -i "CARD-G4-16|G4-16|doc-type-census|adversarial audit|canvas-adversarial-audit|round-3|37387a86|fce0d8a2" /Users/Heishing/.codex/memories/MEMORY.md' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
136:  • 复验注释-only、隔离面及报告 §1/§4/§8
176:    三条行为铁律经 round-3 独立复验通过。
181:/bin/zsh -lc '"git" "cat-file" "-t" "37387a86"' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
193:/bin/zsh -lc '"git" "diff" "--name-status" "37387a86..HEAD"' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
199:A	"_bmad-output/\345\256\241\346\237\245/G4-16-evidence/doc_type-146-occurrences@37387a86.txt"
520:_bmad-output/审查/G4-16-evidence/doc_type-146-occurrences@37387a86.txt
864:_bmad-output/implementation-artifacts/epic-1/1-19-configure-whiteboard-skill.md
1447:_bmad-output/验收单/Story-1.19-configure-whiteboard.md
1729:对象已冻结：当前 `HEAD=fce0d8a2800768a039f0aa05de7a5504d79f63d8`，基线 `37387a86` 可解析为 commit。工作树已有两份无关的未跟踪 round-4 审查稿；我会把它们视为用户/其他流程资产，不读取为证明、不修改，也不让它们影响裁定。
1795:/bin/zsh -lc 'wc -c -l "_bmad-output/审查/G4-16-evidence/doc_type-146-occurrences@37387a86.txt" && shasum -a 256 "_bmad-output/审查/G4-16-evidence/doc_type-146-occurrences@37387a86.txt" && git ls-tree HEAD -- "_bmad-output/审查/G4-16-evidence/doc_type-146-occurrences@37387a86.txt"' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
1797:     146   19403 _bmad-output/审查/G4-16-evidence/doc_type-146-occurrences@37387a86.txt
1798:94b01dc363643020c5bb2f476767eaad88d5b3fb0a32985f5fc2466f5c32c1cd  _bmad-output/审查/G4-16-evidence/doc_type-146-occurrences@37387a86.txt
1800:100644 blob 2a78fc47c5f09a60f6c080f2c3dafe424370cbee	"_bmad-output/\345\256\241\346\237\245/G4-16-evidence/doc_type-146-occurrences@37387a86.txt"
1810:     5	before 不是回忆，而是把两个 py 文件用 git 对象切回 37387a86 版后真实重跑的结果。
1815:    10	--- before 捕获（两文件切至 37387a86 版）:
1816:    11	  git checkout 37387a86 -- backend/app/services/supplementary_reranker.py backend/app/services/supplementary_search_service.py
1826:    21	  reranker:       37387a86=3d8275269213  HEAD=73579b22f7a5
1827:    22	  search_service: 37387a86=17440e21c01b  HEAD=5ff331040905
1834:    29	  即：注释-only 修改对测试输出零影响，9 failed / 102 passed 逐条同节点同顺序。
2069:     2	锚定 SHA: 37387a86 | 生成于 2026-08-28
2076:     9	doc_type distribution: {'video_transcript': 2001, 'concept': 117, 'note': 69, 'whiteboard': 16}
2078:    11	--- ② 字面量启发式扫描（pinned 到 37387a86，不受工作区/.venv 影响）:
2079:    12	git grep -h "doc_type" 37387a86 -- "backend/app/*.py" "backend/lib/*.py" | grep -oE "[\"'][a-z_]+[\"']" | sort | uniq -c | sort -rn
2083:    16	报告 §1/§4 的逐点人工裁定 + pinned 146 行清单（doc_type-146-occurrences@37387a86.txt）。
2087:    20	  10 "whiteboard"
2088:    21	  10 "exam_board"
2097:    30	   1 'whiteboard'
2107:     5	> **代码基线**: worktree `card/s5-census` @ **`37387a86`**（全部 file:line 以此 SHA 为准；config.py 同时在他卡编辑面上，行号会漂移——复核请先 checkout 此 SHA）
2115:    13	`git grep -n "doc_type" 37387a86 -- "backend/*.py"` → **18 文件 146 行**（逐行清单：证据包 `doc_type-146-occurrences@37387a86.txt`；**必须用 pinned git grep 复核**——工作树裸 `grep -rn backend` 会扫入 `backend/.venv` 得 30 文件 198 行，Codex round-1 MEDIUM-5）。与勘探预告完全一致。
2117:    15	**范围声明（Codex round-1 HIGH-4）**：本 census 的对象是 **backend/*.py 中 LanceDB `vault_notes` 行级 `doc_type` 字段**。仓库根 `scripts/migrate_story_frontmatter.py:62` 写 `doc_type: story`、`scripts/sync_links.py:63/:85` 消费 story/epic（行号已按 pinned 37387a86 复核，round-2 LOW 修正）——那是 **BMAD 文档 frontmatter 的同名异物命名空间**，不入 LanceDB、不与本字段互通，不在本卡值域表内（如实登记防混淆）。
2126:    24	| 生产消费·隔离面 | `app/services/tool_executor.py` / `app/services/react_agent.py` / `lib/agentic_rag/agent_graph.py` | 3 / 2 / 1 |
2133:    31	**写入方论证（Codex round-1 MEDIUM-3/LOW-1 修订）**：`vault_notes` 表的**显式值生产者恰两处**，均在 `lancedb_client.py`——批量索引路径（:1773-1777 推导 → :1795 metadata + :1818 SQL 列）与单文件更新路径（:2058-2062 推导 → :2078 + :2101），两路共用同一推导规则：`frontmatter.type` **直通**（:2740 lower/strip，无白名单——`whiteboard` 即由此直通入库，:2767 只是消费该值做样板剥离，不是推断点）→ 检验白板推断 `exam_board`（:2756）→ 路径启发 `video_transcript`（`_is_video_transcript`）→ 默认 `"note"`。此外存在**通用 sink**：公共 `add_documents()`（:3615）可无校验透传调用方传入的任意 `doc_type`（含 Chroma 迁移脚本内嵌 metadata_json 路径）——静态未发现当前有第三方经此向 `vault_notes` 写第三种值，但"唯一"须限定为"两显式生产者 + 通用 sink 无校验"。多模态 image_ocr 写路径（:1279-1293）**不含 doc_type 字段**——读侧空串回退的真实来源之一。
2140:    38	video_transcript 2001 (90.8%) | concept 117 | note 69 | whiteboard 16 | exam_board 0 | 空/自由值 0
2145:    43	- **排除过滤（真实消费主链）**：`exclude_doc_types=["whiteboard","exam_board"]` 于 react_agent:115/:124、tool_executor:112/:122、agent_graph:208、supplementary_search_service:834/:849 显式传入，vault_notes_retriever:82 为默认值——共 7 处显式 + 1 处默认，SQL `NOT IN` 落到 lancedb doc_type 列。**边界（Codex round-1 MEDIUM-4）**：该隔离只覆盖默认 Tier-1 路径——`ENABLE_LANCEDB_TIER2_FALLBACK`（默认关闭）开启后 legacy tier-2 直查裸 `vault_notes` 无 doc_type WHERE（supplementary_search_service.py:863），"在库但检索不可见"仅在默认配置下成立（登记 FU-5）。这是检验白板信息隔离（Karpicke 主动回忆）的**读侧第二层防御**（第一层 = config.py 目录黑名单，:48-50 注释如实记录"验收单/_待处理 无 doc_type，单层防御"）。
2148:    46	- **裁判消费**：run_vault_retrieval_regression:134/:143 以 doc_type ∈ 硬禁集（whiteboard/exam_board 类）判定检索污染——回归门真实消费方。
2156:    54	| 3 | `whiteboard` | frontmatter `type: whiteboard` 直通（:2740；:2767 仅消费做样板剥离，LOW-1 修订） | 16 | exclude 集 7+1 处消费（隔离第二层）；默认 Tier-1 下在库但检索不可见 = 设计行为（Tier-2 flag 例外见 §3/FU-5） | **接线** |
2157:    55	| 4 | `exam_board` | 检验白板推断（:2756） | 0 | exclude 集同上。live 0 行原因（Codex round-1 HIGH-2 指出原归因不完整，本轮实测坐实）：exam-quick 考察文件写向**可索引**的 `节点/考察-*.md`（exam-quick.ts:39/:75，目录黑名单不拦）——live vault 实测该形态文件 **0 个**；`检验白板/` 目录唯一 1 个 md 则被目录黑名单拦截。0 行 = "无考察文件存在 + 黑名单拦检验白板目录"两因叠加，非纯黑名单 | **接线**（0 行原因已实测坐实，非死值） |
2163:    61	## §5 ≤1h 轻量处置（本卡完成，注释-only，零行为改动）
2175:    73	- **证据绑定（round-1 MEDIUM-5 → round-3 实质闭合）**：round-1/2 只存 FAILED 节点摘要，Codex round-3 判定"历史 stdout 不可事后补造"属实——故本轮**重做了一次可复验的完整捕获**取代历史摘要：用 `git checkout 37387a86 -- <两文件>` 把文件切回基线版**真实重跑**（`pytest-before-full-stdout.txt`，完整 stdout+traceback+exit_code=1），再 `git checkout HEAD -- <两文件>` 重跑（`pytest-after-full-stdout.txt`）。两份完整输出经**内存地址与耗时归一化后逐字节相同**（未归一化时的全部差异 = CPython 对象地址与 pytest 耗时）。metadata 记录两次命令、两文件 blob、Python 版本、两份产物 sha256。
2176:    74	- **取值字面量证据（round-2 新 MEDIUM → round-3 补完）**：`live-distribution-and-value-grep.txt` 的字面量 grep 是**启发式辅助视图**（含 `"doc_type"`/`"file_path"` 等假阳性，非精确全集）；六值全集的权威依据是 §1/§4 的逐点人工裁定 + pinned 146 行清单。round-3 整改：两条生成命令改为**无占位符、可直接复跑**（docker 一行式 + `git grep` pinned 37387a86，`zsh -n` 语法校验通过），扫描结果随文件重新实跑落盘。
2178:    76	**9 条既有失败根因方向**（登记入 FU-2，本卡不修）：测试仍按 2026-05-12 设计断言 `note→0.7 中档`（test :579 docstring 自述），而 RAG-S2 T2（2026-08-09）已把 note/concept 翻转为 1.0（权重方向"手写最高"）且 rerank_score 计算随之变化 → FilterFloor 族的 0.42 过滤阈值场景不再触发。属"生产权重翻转未同步测试"的陈债（Codex 独立溯源到翻转 commit `fcd34953`，并确认 floor 用例修法应调输入使 floor 继续触发、不应放宽预期），与本卡注释修正无关（before/after 失败节点全等自证）。
2188:    86	| FU-5 | `ENABLE_LANCEDB_TIER2_FALLBACK`（默认关）开启后 tier-2 直查绕过 doc_type 排除（supplementary_search_service.py:863）——检验白板隔离在该配置下失效，需补 tier-2 侧 WHERE 或在 flag 文档标注隔离代价 | 隔离面后续卡（本卡铁律禁改隔离面，仅登记） |
2192:    90	供 G8-1 收录：`doc_type` = LanceDB 行级**文档角色** schema 字段；权威值域现状 = {note, video_transcript, whiteboard, exam_board, concept} + 未闭合 frontmatter 直通面；写入方 = lancedb_client **两显式生产者**（批量/单文件）+ `add_documents()` 无校验通用 sink（round-2 MEDIUM-3：摘要与 §1 口径统一，不得退回"唯一"）；消费主链 = 检验白板隔离排除集 + 回归污染裁判；与 source_type（内容来源形态：note/video_transcript/image_ocr/neighbor_expansion）**字段职责与赋值链分离**（doc_type 主要来自 frontmatter 直通+推断；source_type 在 vault 笔记索引路径为路径启发二分 note/video_transcript，另有 image_ocr 的**显式赋值**与 neighbor_expansion 的**运行期赋值**——round-2 修正"纯路径启发"的不实表述；二者共享 `_is_video_transcript` 但互不复制取值），G4-16 前的注释曾将二者混同（已修正）。命名与取值最终口径以 G8-1 台账为准。
2196:    94	Codex round-1 终裁 FAIL（0 BLOCKER / 4 HIGH / 5 MEDIUM / 1 LOW），同时确认：两文件与 HEAD 的无属性 AST 完全相等（注释-only 铁律 PASS）、隔离面零改动 PASS、9 条既有失败根因归因 PASS（溯源 `fcd34953`）、pinned git grep 18/146 复算 PASS。逐条整改：
2199:    97	- **HIGH-2（exam_board live=0 归因）**：本轮补实测——live vault `节点/考察-*.md` 实存 0 个 + `检验白板/` 唯一 1 md 被黑名单拦截，两因叠加坐实（§4 行 4 重写，UNVERIFIED 消除）。
2205:   103	- **MEDIUM-4（Tier-2 旁路）**：§3 边界声明 + FU-5 登记（本卡铁律禁改隔离面）。
2207:   105	- **LOW-1（whiteboard 来源行号）**：:2740 直通为写侧来源，:2767 为消费点（§1/§4 修正）。
2209:   107	整改后复跑落点测试：9 failed / 102 passed，失败节点与基线逐条相同——注释修订不改任何行为。
2213:   111	round-2 确认 HIGH-1/2/4、MEDIUM-1/2/4、LOW-1 共 7 项 CLOSED，并独立复跑坐实三条铁律（AST 全等注释-only、隔离面零改动、9 failed/102 passed 与基线同集合同顺序）。未闭合 3 项 + 新发现 4 条，逐条整改：
2219:   117	- **新 MEDIUM（reranker:196 陈旧注释）**：floor 兜底注释仍写 `note=0.7 / 0.5×0.7=0.35` 的历史算例。**整改**：加注 fcd34953 翻转后 note=1.0、该算例为历史情形、floor 机制仍生效、测试重写归 FU-2（仍为注释-only）。
2225:   123	round-3 裁定 5 CLOSED（自由值路径条件 / §8 摘要口径 / source_type 赋值链 / reranker 陈旧算例 / 根脚本行号），三条行为铁律复验通过（AST 全等注释-only、隔离面零改动、失败节点集合相同），阻断点收敛为**证据可复验性**两项：
2227:   125	- **MEDIUM-5 测试 provenance**：round-3 指出"当前复跑不能补造历史证据"——完全正确。**整改思路改变**：不再试图为历史运行补 provenance，而是**重做一次可复验的完整对照**——把两文件用 git 对象切回 37387a86 真实重跑得 before，切回 HEAD 重跑得 after，两份完整 stdout（含 traceback、exit_code）归一化内存地址与耗时后**逐字节相同**。证据从"声明"变为"可复跑复算"。
2228:   126	- **live/value-grep 命令可执行性**：`<lancedb…>` 占位符 + `zsh -n` 报 unmatched quote + 裸 grep 未绑定 SHA。**整改**：两条命令改写为无占位符完整形式（docker 一行式；`git grep` pinned 37387a86），`zsh -n` 校验通过，结果随文件重新实跑。
2234:15:请只读复核这 7 项是否闭合（报告 _bmad-output/审查/G4-16-doc-type-census-2026-08-28.md 含新增 §10 段；证据包 _bmad-output/审查/G4-16-evidence/ 三个文件已更新；backend/app/services/supplementary_reranker.py 的 floor 注释已加注）。同时复验铁律：git diff 37387a86..HEAD 对两个 py 文件仍为注释-only（无属性 AST 相等）、隔离面零改动、落点测试 before/after 失败节点集合仍相同。逐项 CLOSED/NOT-CLOSED + 总裁定（可验收/仍阻断）+ 新发现分级。
2235:19:我会按只读、fail-closed 的 round-3 复审执行：先加载既有审计规程与 Graphiti 记忆，再并行核验 7 项整改、Python 注释-only/隔离面、以及 before/after 失败节点集合；不会修改文件或重跑任何会污染工作树的命令。最终会给出逐项 `CLOSED/NOT-CLOSED`、可复现证据、总裁定和新增发现分级。
2245:288:    86	- 🔒 [Code-Review] 独立对抗审查（E2E 复现式）**3 HIGH / 3 MEDIUM / 5 LOW → 全部处置, 复验 32/32 全绿**: ⛔ H1 orphans 回显通道（source_board 塞定义全文进 exam 视图, 已复现）→ reason 定长枚举文案+raw 截断 120+模型 max_length 门; ⛔ H2 parse_errors 回显（last_examined repr 无界+纯 Python yaml loader str(e) 引用原文行含 correction 禁串）→ _safe_err 去内容化（异常类型+行号）+repr[:80]+模型 200 字门; ⛔ H3 untrusted 标量炸投影（`doc_count: 大约五个`/`title: 2026` → ValidationError 500 整端点含列板）→ _bounded_str 类型归一×7 字段+双暴露面 ValidationError 纵深兜底; M4 digest 吸入相邻 [!feedback]/[!hint] callout（可含正确答案）→ callout 边界终止收集; M6 #heading 锚点+大小写敏感→假孤儿（喂 H1 通道）→ resolve 剥锚点+boards_ci casefold 匹配; M7 金集合成A恒真条件（自比较）→ 改「挖掉 reason 槽位后 0 命中」; M8 禁串无正向对照会静默腐烂→禁串必须仍在 vault 源文件+G5 digest 非空对照（金集 31→32 条）; L 批: 快照 tmp 唯一名防竞态/load 快照 schema 必备键校验/exam_board_count 恒用 full 历史/信封字段统一截断/set_current_subject_id 移到 fail-close 之后。审查确认: 投影穿透 E2E 失败（防线真实）、快照双黑名单成立、serve 路径唯一、pick 数学锁死、无 DD-03 违规。新增回归锁 6 条（契约 77 绿）
2248:666:/bin/zsh -lc "wc -l '_bmad-output/审查/G4-16-doc-type-census-2026-08-28.md' '_bmad-output/审查/G4-16-evidence/doc_type-146-occurrences@37387a86.txt' '_bmad-output/审查/G4-16-evidence/after-edits.txt' '_bmad-output/审查/G4-16-evidence/test-run-metadata.txt' '_bmad-output/审查/G4-16-evidence/baseline-before-edits.txt' '_bmad-output/审查/G4-16-evidence/live-distribution-and-value-grep.txt' 'backend/app/services/supplementary_reranker.py' 'backend/app/services/supplementary_search_service.py'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
2250:679:/bin/zsh -lc "shasum -a 256 '_bmad-output/审查/G4-16-doc-type-census-2026-08-28.md' '_bmad-output/审查/G4-16-evidence/doc_type-146-occurrences@37387a86.txt' '_bmad-output/审查/G4-16-evidence/after-edits.txt' '_bmad-output/审查/G4-16-evidence/test-run-metadata.txt' '_bmad-output/审查/G4-16-evidence/baseline-before-edits.txt' '_bmad-output/审查/G4-16-evidence/live-distribution-and-value-grep.txt' 'backend/app/services/supplementary_reranker.py' 'backend/app/services/supplementary_search_service.py'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
2252:691:/bin/zsh -lc "git ls-tree -r HEAD -- '_bmad-output/审查/G4-16-doc-type-census-2026-08-28.md' '_bmad-output/审查/G4-16-evidence/doc_type-146-occurrences@37387a86.txt' '_bmad-output/审查/G4-16-evidence/after-edits.txt' '_bmad-output/审查/G4-16-evidence/test-run-metadata.txt' '_bmad-output/审查/G4-16-evidence/baseline-before-edits.txt' '_bmad-output/审查/G4-16-evidence/live-distribution-and-value-grep.txt' 'backend/app/services/supplementary_reranker.py' 'backend/app/services/supplementary_search_service.py'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
2254:719:    13	`git grep -n "doc_type" 37387a86 -- "backend/*.py"` → **18 文件 146 行**（逐行清单：证据包 `doc_type-146-occurrences@37387a86.txt`；**必须用 pinned git grep 复核**——工作树裸 `grep -rn backend` 会扫入 `backend/.venv` 得 30 文件 198 行，Codex round-1 MEDIUM-5）。与勘探预告完全一致。
2259:817:   111	round-2 确认 HIGH-1/2/4、MEDIUM-1/2/4、LOW-1 共 7 项 CLOSED，并独立复跑坐实三条铁律（AST 全等注释-only、隔离面零改动、9 failed/102 passed 与基线同集合同顺序）。未闭合 3 项 + 新发现 4 条，逐条整改：
2276:914:    14	| MEDIUM-5 | **NOT-CLOSED** | pinned grep 已闭合：精确重放为 **18 文件/146 行**，与 [清单](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-evidence/doc_type-146-occurrences@37387a86.txt:1) 逐字节相等。但 [metadata:2](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-evidence/test-run-metadata.txt:2) 仍无两次完整 stdout/traceback、exit code、时间戳、before/after 源 blob/digest。结合 [pytest.ini:19](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/pytest.ini:19)，所列命令不会直接产生现有仅 10 行的摘要，过滤过程也未记录。 |
2277:915:    15	| LOW-1 | **CLOSED** | 已正确区分 [frontmatter 直通:2740](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/lib/agentic_rag/clients/lancedb_client.py:2740) 与 [whiteboard 消费:2767](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/lib/agentic_rag/clients/lancedb_client.py:2767)。 |
2278:919:    19	- **CLOSED**：`e7a480eb^ → e7a480eb` 两个 Python 文件均为无属性 AST 全等，diff 只有 `#` 注释。
2280:921:    21	- **CLOSED**：[baseline](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-evidence/baseline-before-edits.txt:1) 与 [after](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-evidence/after-edits.txt:1) 的 9 个失败节点顺序及集合完全相同；仅耗时 `0.47s/0.50s` 不同。
2287:1180: `git grep -n "doc_type" 37387a86 -- "backend/*.py"` → **18 文件 146 行**（逐行清单：证据包 `doc_type-146-occurrences@37387a86.txt`；**必须用 pinned git grep 复核**——工作树裸 `grep -rn backend` 会扫入 `backend/.venv` 得 30 文件 198 行，Codex round-1 MEDIUM-5）。与勘探预告完全一致。
2288:1226:-- **证据绑定补强（Codex round-1 MEDIUM-5）**：证据包新增 `test-run-metadata.txt`（精确 pytest 命令 / venv Python 版本 / HEAD sha / 失败节点集合 diff 说明——before/after 失败节点逐条相同，仅耗时行不同）。
2293:1266:+round-2 确认 HIGH-1/2/4、MEDIUM-1/2/4、LOW-1 共 7 项 CLOSED，并独立复跑坐实三条铁律（AST 全等注释-only、隔离面零改动、9 failed/102 passed 与基线同集合同顺序）。未闭合 3 项 + 新发现 4 条，逐条整改：
2306:2662:当前交叉结果已收敛为：5 项文本/代码整改真实闭合，2 项证据整改仍未闭合。尤其 `live-distribution-and-value-grep.txt:4` 所谓生成命令经 `zsh -n` 直接报 `unmatched '`，`:3` 还是 `<…>` 占位符；因此“补了生成命令”并不成立。两条 Python 铁律与当前测试失败集则已独立复算通过。
2310:2718:总裁定：**仍阻断，不可验收。** `73102875` 对 7 项完成 **5 CLOSED / 2 NOT-CLOSED**。三项行为铁律均复验通过；阻断点仍是证据可复验性，不是代码行为回归。
2316:2727:| live/value-grep 命令与假阳性 | **NOT-CLOSED** | [evidence:5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-evidence/live-distribution-and-value-grep.txt:5) 已承认假阳性并降级；但 `:3` 仍是 `<lancedb…>` 占位符，`:4` 经 `zsh -n` 得 exit `1: unmatched '`，且裸 grep 未绑定 `:2` 声称的 `37387a86`。 |
2320:2747:总裁定：**仍阻断，不可验收。** `73102875` 对 7 项完成 **5 CLOSED / 2 NOT-CLOSED**。三项行为铁律均复验通过；阻断点仍是证据可复验性，不是代码行为回归。
2326:2756:| live/value-grep 命令与假阳性 | **NOT-CLOSED** | [evidence:5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-evidence/live-distribution-and-value-grep.txt:5) 已承认假阳性并降级；但 `:3` 仍是 `<lancedb…>` 占位符，`:4` 经 `zsh -n` 得 exit `1: unmatched '`，且裸 grep 未绑定 `:2` 声称的 `37387a86`。 |
2336:     2	锚定 SHA: 37387a86 | 生成于 2026-08-28
2343:     9	doc_type distribution: {'video_transcript': 2001, 'concept': 117, 'note': 69, 'whiteboard': 16}
2345:    11	--- ② 字面量启发式扫描（pinned 到 37387a86，不受工作区/.venv 影响）:
2346:    12	git grep -h "doc_type" 37387a86 -- "backend/app/*.py" "backend/lib/*.py" | grep -oE "[\"'][a-z_]+[\"']" | sort | uniq -c | sort -rn
2350:    16	报告 §1/§4 的逐点人工裁定 + pinned 146 行清单（doc_type-146-occurrences@37387a86.txt）。
2354:    20	  10 "whiteboard"
2355:    21	  10 "exam_board"
2364:    30	   1 'whiteboard'
2374:     5	> **代码基线**: worktree `card/s5-census` @ **`37387a86`**（全部 file:line 以此 SHA 为准；config.py 同时在他卡编辑面上，行号会漂移——复核请先 checkout 此 SHA）
2382:    13	`git grep -n "doc_type" 37387a86 -- "backend/*.py"` → **18 文件 146 行**（逐行清单：证据包 `doc_type-146-occurrences@37387a86.txt`；**必须用 pinned git grep 复核**——工作树裸 `grep -rn backend` 会扫入 `backend/.venv` 得 30 文件 198 行，Codex round-1 MEDIUM-5）。与勘探预告完全一致。
2384:    15	**范围声明（Codex round-1 HIGH-4）**：本 census 的对象是 **backend/*.py 中 LanceDB `vault_notes` 行级 `doc_type` 字段**。仓库根 `scripts/migrate_story_frontmatter.py:62` 写 `doc_type: story`、`scripts/sync_links.py:63/:85` 消费 story/epic（行号已按 pinned 37387a86 复核，round-2 LOW 修正）——那是 **BMAD 文档 frontmatter 的同名异物命名空间**，不入 LanceDB、不与本字段互通，不在本卡值域表内（如实登记防混淆）。
2393:    24	| 生产消费·隔离面 | `app/services/tool_executor.py` / `app/services/react_agent.py` / `lib/agentic_rag/agent_graph.py` | 3 / 2 / 1 |
2400:    31	**写入方论证（Codex round-1 MEDIUM-3/LOW-1 修订）**：`vault_notes` 表的**显式值生产者恰两处**，均在 `lancedb_client.py`——批量索引路径（:1773-1777 推导 → :1795 metadata + :1818 SQL 列）与单文件更新路径（:2058-2062 推导 → :2078 + :2101），两路共用同一推导规则：`frontmatter.type` **直通**（:2740 lower/strip，无白名单——`whiteboard` 即由此直通入库，:2767 只是消费该值做样板剥离，不是推断点）→ 检验白板推断 `exam_board`（:2756）→ 路径启发 `video_transcript`（`_is_video_transcript`）→ 默认 `"note"`。此外存在**通用 sink**：公共 `add_documents()`（:3615）可无校验透传调用方传入的任意 `doc_type`（含 Chroma 迁移脚本内嵌 metadata_json 路径）——静态未发现当前有第三方经此向 `vault_notes` 写第三种值，但"唯一"须限定为"两显式生产者 + 通用 sink 无校验"。多模态 image_ocr 写路径（:1279-1293）**不含 doc_type 字段**——读侧空串回退的真实来源之一。
2407:    38	video_transcript 2001 (90.8%) | concept 117 | note 69 | whiteboard 16 | exam_board 0 | 空/自由值 0
2412:    43	- **排除过滤（真实消费主链）**：`exclude_doc_types=["whiteboard","exam_board"]` 于 react_agent:115/:124、tool_executor:112/:122、agent_graph:208、supplementary_search_service:834/:849 显式传入，vault_notes_retriever:82 为默认值——共 7 处显式 + 1 处默认，SQL `NOT IN` 落到 lancedb doc_type 列。**边界（Codex round-1 MEDIUM-4）**：该隔离只覆盖默认 Tier-1 路径——`ENABLE_LANCEDB_TIER2_FALLBACK`（默认关闭）开启后 legacy tier-2 直查裸 `vault_notes` 无 doc_type WHERE（supplementary_search_service.py:863），"在库但检索不可见"仅在默认配置下成立（登记 FU-5）。这是检验白板信息隔离（Karpicke 主动回忆）的**读侧第二层防御**（第一层 = config.py 目录黑名单，:48-50 注释如实记录"验收单/_待处理 无 doc_type，单层防御"）。
2415:    46	- **裁判消费**：run_vault_retrieval_regression:134/:143 以 doc_type ∈ 硬禁集（whiteboard/exam_board 类）判定检索污染——回归门真实消费方。
2423:    54	| 3 | `whiteboard` | frontmatter `type: whiteboard` 直通（:2740；:2767 仅消费做样板剥离，LOW-1 修订） | 16 | exclude 集 7+1 处消费（隔离第二层）；默认 Tier-1 下在库但检索不可见 = 设计行为（Tier-2 flag 例外见 §3/FU-5） | **接线** |
2424:    55	| 4 | `exam_board` | 检验白板推断（:2756） | 0 | exclude 集同上。live 0 行原因（Codex round-1 HIGH-2 指出原归因不完整，本轮实测坐实）：exam-quick 考察文件写向**可索引**的 `节点/考察-*.md`（exam-quick.ts:39/:75，目录黑名单不拦）——live vault 实测该形态文件 **0 个**；`检验白板/` 目录唯一 1 个 md 则被目录黑名单拦截。0 行 = "无考察文件存在 + 黑名单拦检验白板目录"两因叠加，非纯黑名单 | **接线**（0 行原因已实测坐实，非死值） |
2430:    61	## §5 ≤1h 轻量处置（本卡完成，注释-only，零行为改动）
2442:    73	- **证据绑定（round-1 MEDIUM-5 → round-3 实质闭合）**：round-1/2 只存 FAILED 节点摘要，Codex round-3 判定"历史 stdout 不可事后补造"属实——故本轮**重做了一次可复验的完整捕获**取代历史摘要：用 `git checkout 37387a86 -- <两文件>` 把文件切回基线版**真实重跑**（`pytest-before-full-stdout.txt`，完整 stdout+traceback+exit_code=1），再 `git checkout HEAD -- <两文件>` 重跑（`pytest-after-full-stdout.txt`）。两份完整输出经**内存地址与耗时归一化后逐字节相同**（未归一化时的全部差异 = CPython 对象地址与 pytest 耗时）。metadata 记录两次命令、两文件 blob、Python 版本、两份产物 sha256。
2443:    74	- **取值字面量证据（round-2 新 MEDIUM → round-3 补完）**：`live-distribution-and-value-grep.txt` 的字面量 grep 是**启发式辅助视图**（含 `"doc_type"`/`"file_path"` 等假阳性，非精确全集）；六值全集的权威依据是 §1/§4 的逐点人工裁定 + pinned 146 行清单。round-3 整改：两条生成命令改为**无占位符、可直接复跑**（docker 一行式 + `git grep` pinned 37387a86，`zsh -n` 语法校验通过），扫描结果随文件重新实跑落盘。
2445:    76	**9 条既有失败根因方向**（登记入 FU-2，本卡不修）：测试仍按 2026-05-12 设计断言 `note→0.7 中档`（test :579 docstring 自述），而 RAG-S2 T2（2026-08-09）已把 note/concept 翻转为 1.0（权重方向"手写最高"）且 rerank_score 计算随之变化 → FilterFloor 族的 0.42 过滤阈值场景不再触发。属"生产权重翻转未同步测试"的陈债（Codex 独立溯源到翻转 commit `fcd34953`，并确认 floor 用例修法应调输入使 floor 继续触发、不应放宽预期），与本卡注释修正无关（before/after 失败节点全等自证）。
2455:    86	| FU-5 | `ENABLE_LANCEDB_TIER2_FALLBACK`（默认关）开启后 tier-2 直查绕过 doc_type 排除（supplementary_search_service.py:863）——检验白板隔离在该配置下失效，需补 tier-2 侧 WHERE 或在 flag 文档标注隔离代价 | 隔离面后续卡（本卡铁律禁改隔离面，仅登记） |
2459:    90	供 G8-1 收录：`doc_type` = LanceDB 行级**文档角色** schema 字段；权威值域现状 = {note, video_transcript, whiteboard, exam_board, concept} + 未闭合 frontmatter 直通面；写入方 = lancedb_client **两显式生产者**（批量/单文件）+ `add_documents()` 无校验通用 sink（round-2 MEDIUM-3：摘要与 §1 口径统一，不得退回"唯一"）；消费主链 = 检验白板隔离排除集 + 回归污染裁判；与 source_type（内容来源形态：note/video_transcript/image_ocr/neighbor_expansion）**字段职责与赋值链分离**（doc_type 主要来自 frontmatter 直通+推断；source_type 在 vault 笔记索引路径为路径启发二分 note/video_transcript，另有 image_ocr 的**显式赋值**与 neighbor_expansion 的**运行期赋值**——round-2 修正"纯路径启发"的不实表述；二者共享 `_is_video_transcript` 但互不复制取值），G4-16 前的注释曾将二者混同（已修正）。命名与取值最终口径以 G8-1 台账为准。
2463:    94	Codex round-1 终裁 FAIL（0 BLOCKER / 4 HIGH / 5 MEDIUM / 1 LOW），同时确认：两文件与 HEAD 的无属性 AST 完全相等（注释-only 铁律 PASS）、隔离面零改动 PASS、9 条既有失败根因归因 PASS（溯源 `fcd34953`）、pinned git grep 18/146 复算 PASS。逐条整改：
2466:    97	- **HIGH-2（exam_board live=0 归因）**：本轮补实测——live vault `节点/考察-*.md` 实存 0 个 + `检验白板/` 唯一 1 md 被黑名单拦截，两因叠加坐实（§4 行 4 重写，UNVERIFIED 消除）。
2472:   103	- **MEDIUM-4（Tier-2 旁路）**：§3 边界声明 + FU-5 登记（本卡铁律禁改隔离面）。
2474:   105	- **LOW-1（whiteboard 来源行号）**：:2740 直通为写侧来源，:2767 为消费点（§1/§4 修正）。
2476:   107	整改后复跑落点测试：9 failed / 102 passed，失败节点与基线逐条相同——注释修订不改任何行为。
2480:   111	round-2 确认 HIGH-1/2/4、MEDIUM-1/2/4、LOW-1 共 7 项 CLOSED，并独立复跑坐实三条铁律（AST 全等注释-only、隔离面零改动、9 failed/102 passed 与基线同集合同顺序）。未闭合 3 项 + 新发现 4 条，逐条整改：
2486:   117	- **新 MEDIUM（reranker:196 陈旧注释）**：floor 兜底注释仍写 `note=0.7 / 0.5×0.7=0.35` 的历史算例。**整改**：加注 fcd34953 翻转后 note=1.0、该算例为历史情形、floor 机制仍生效、测试重写归 FU-2（仍为注释-only）。
2492:   123	round-3 裁定 5 CLOSED（自由值路径条件 / §8 摘要口径 / source_type 赋值链 / reranker 陈旧算例 / 根脚本行号），三条行为铁律复验通过（AST 全等注释-only、隔离面零改动、失败节点集合相同），阻断点收敛为**证据可复验性**两项：
2494:   125	- **MEDIUM-5 测试 provenance**：round-3 指出"当前复跑不能补造历史证据"——完全正确。**整改思路改变**：不再试图为历史运行补 provenance，而是**重做一次可复验的完整对照**——把两文件用 git 对象切回 37387a86 真实重跑得 before，切回 HEAD 重跑得 after，两份完整 stdout（含 traceback、exit_code）归一化内存地址与耗时后**逐字节相同**。证据从"声明"变为"可复跑复算"。
2495:   126	- **live/value-grep 命令可执行性**：`<lancedb…>` 占位符 + `zsh -n` 报 unmatched quote + 裸 grep 未绑定 SHA。**整改**：两条命令改写为无占位符完整形式（docker 一行式；`git grep` pinned 37387a86），`zsh -n` 校验通过，结果随文件重新实跑。
2506:/bin/zsh -lc "git grep -h \"doc_type\" 37387a86 -- \"backend/app/*.py\" \"backend/lib/*.py\" | grep -oE \"[\\\"'][a-z_]+[\\\"']\" | sort | uniq -c | sort -rn" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
2510:  10 "whiteboard"
2511:  10 "exam_board"
2515:   1 'whiteboard'
2530:{'video_transcript': 2001, 'concept': 117, 'note': 69, 'whiteboard': 16}
2617:/bin/zsh -lc 'git rev-parse "37387a86:backend/app/services/supplementary_reranker.py"' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
2629:/bin/zsh -lc 'git rev-parse "37387a86:backend/app/services/supplementary_search_service.py"' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
2646:/bin/zsh -lc 'git merge-base --is-ancestor 37387a86 HEAD' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
2719:/bin/zsh -lc "LC_ALL=C git grep -h \"doc_type\" 37387a86 -- \"backend/app/*.py\" \"backend/lib/*.py\" | LC_ALL=C grep -oE \"[\\\"'][a-z_]+[\\\"']\" | LC_ALL=C sort | LC_ALL=C uniq -c | LC_ALL=C sort -rn" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
2723:  10 "whiteboard"
2724:  10 "exam_board"
2728:   1 'whiteboard'
2737:/bin/zsh -lc "LC_ALL=C.UTF-8 git grep -h \"doc_type\" 37387a86 -- \"backend/app/*.py\" \"backend/lib/*.py\" | LC_ALL=C.UTF-8 grep -oE \"[\\\"'][a-z_]+[\\\"']\" | LC_ALL=C.UTF-8 sort | LC_ALL=C.UTF-8 uniq -c | LC_ALL=C.UTF-8 sort -rn" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
2741:  10 "whiteboard"
2742:  10 "exam_board"
2746:   1 'whiteboard'
2755:/bin/zsh -lc "LC_ALL=en_US.UTF-8 git grep -h \"doc_type\" 37387a86 -- \"backend/app/*.py\" \"backend/lib/*.py\" | LC_ALL=en_US.UTF-8 grep -oE \"[\\\"'][a-z_]+[\\\"']\" | LC_ALL=en_US.UTF-8 sort | LC_ALL=en_US.UTF-8 uniq -c | LC_ALL=en_US.UTF-8 sort -rn" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
2759:  10 "whiteboard"
2760:  10 "exam_board"
2769:   1 'whiteboard'
2775:/bin/zsh -lc 'git grep -n "doc_type" 37387a86 -- "backend/*.py" | shasum -a 256' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
2781:/bin/zsh -lc "git grep -n \"doc_type\" 37387a86 -- \"backend/*.py\" | awk -F: '{print "'$1}'"' | sort -u | wc -l && git grep -n \"doc_type\" 37387a86 -- \"backend/*.py\" | wc -l" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
2790:/bin/zsh -lc "git grep -n \"doc_type\" 37387a86 -- \"backend/*.py\" | sed -n '1,3p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
2793:37387a86:backend/app/api/v1/endpoints/metadata.py:569:            Use after RAG-P0 schema changes (e.g. adding doc_type column) to
2794:37387a86:backend/app/config.py:48:#:   - 检验白板: 双层 —— 目录黑名单 + 读侧 exclude_doc_types=["whiteboard","exam_board"]
2795:37387a86:backend/app/config.py:50:#:   - 验收单 / _待处理 / _archive: **单层** —— frontmatter 无 doc_type,
2799:/bin/zsh -lc 'git grep -n "doc_type" 37387a86 -- "backend/*.py" | cut -d: -f2 | sort -u | wc -l' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
2805:**Designing AST-based comment-only diff detection**
2807:/bin/zsh -lc 'git diff --no-ext-diff --unified=8 37387a86..HEAD -- "backend/app/services/supplementary_reranker.py"' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
2866:/bin/zsh -lc 'git diff --numstat 37387a86..HEAD -- "backend/app/services/supplementary_reranker.py"' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
2872:/bin/zsh -lc 'git diff --no-ext-diff --unified=8 37387a86..HEAD -- "backend/app/services/supplementary_search_service.py"' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
2904:/bin/zsh -lc 'git diff --numstat 37387a86..HEAD -- "backend/app/services/supplementary_search_service.py"' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
2916: print(p,\"ast_equal=\"+str(da==db),\"base_ast_sha256=\"+hashlib.sha256(da.encode()).hexdigest(),\"head_ast_sha256=\"+hashlib.sha256(db.encode()).hexdigest())' 37387a86 backend/app/services/supplementary_reranker.py backend/app/services/supplementary_search_service.py" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
2927:/bin/zsh -lc 'git diff --name-status 37387a86..HEAD -- "backend/app/config.py" "backend/app/services/react_agent.py" "backend/app/services/tool_executor.py" "backend/lib/agentic_rag/agent_graph.py" "backend/lib/agentic_rag/retrievers/vault_notes_retriever.py" "backend/app/services/supplementary_search_service.py"' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
2933:/bin/zsh -lc 'git diff -U0 37387a86..HEAD -- backend/app/services/supplementary_search_service.py | rg -n "''^[+-].*(exclude_doc_types|ENABLE_LANCEDB_TIER2_FALLBACK|vault_notes|WHERE|doc_type)"' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
2945:429:    "验收单",  # 同为信息隔离面, 且实测只有单层防御 (读侧 doc_type 不挡)
2976:2686:        # 携带 doc_type=whiteboard 仍被检索默认排除) — 此处不再无差别剥离。
2977:2711:        section 不产 chunk + 考察文件 doc_type 推断 exam_board + 行号补 frontmatter 偏移。
2982:2756:                fm_doc_type = "exam_board"
2984:2767:        if fm_doc_type == "whiteboard":
3032:backend/lib/agentic_rag/agent_graph.py:208:                    exclude_doc_types=["whiteboard", "exam_board"],
3043:backend/app/services/supplementary_search_service.py:834:            exclude_doc_types=["whiteboard", "exam_board"],
3045:backend/app/services/supplementary_search_service.py:849:                exclude_doc_types=["whiteboard", "exam_board"],
3059:backend/app/services/tool_executor.py:112:                exclude_doc_types=["whiteboard", "exam_board"],
3061:backend/app/services/tool_executor.py:122:                    exclude_doc_types=["whiteboard", "exam_board"],
3067:backend/lib/agentic_rag/retrievers/vault_notes_retriever.py:78:    # exam_board — 本 retriever 是 LangGraph 管道 retrieve_vault_notes 节点
3068:backend/lib/agentic_rag/retrievers/vault_notes_retriever.py:82:    default_exclude_doc_types: List[str] = field(default_factory=lambda: ["whiteboard", "exam_board"])
3101:backend/app/services/react_agent.py:115:            exclude_doc_types=["whiteboard", "exam_board"],
3103:backend/app/services/react_agent.py:124:                exclude_doc_types=["whiteboard", "exam_board"],
3157:/bin/zsh -lc 'git grep -n "doc_type" 37387a86 -- "backend/*.py" | cut -d: -f2 | sort | uniq -c | sort -rn' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
3327:  2753	                # = 信息隔离旁路 (Karpicke d=1.50)。推断 exam_board 后, hook 链与
3330:  2756	                fm_doc_type = "exam_board"
3334:  2760	        # RAG-P0 A4 (2026-05-10): whiteboard differential chunking.
3338:  2764	        # no real semantic value. After A3 default exclude, whiteboard chunks
3341:  2767	        if fm_doc_type == "whiteboard":
3342:  2768	            body = LanceDBClient._strip_whiteboard_boilerplate(body)
3522:   822	    # RAG-P0 A3 (2026-05-10): default exclude whiteboard. MOC/index whiteboards
3531:   831	            # R3 第二层防御 (2026-07-12): exam_board 加入查询侧排除 — 索引黑名单
3534:   834	            exclude_doc_types=["whiteboard", "exam_board"],
3546:   846	                # RAG-S2 T5 (2026-08-10): 回退分支此前漏排 exam_board — hybrid
3549:   849	                exclude_doc_types=["whiteboard", "exam_board"],
3808:/bin/zsh -lc "nl -ba backend/pytest.ini | sed -n '1,40p' && git diff --quiet 37387a86..HEAD -- backend/pytest.ini backend/tests/unit/test_supplementary_reranker.py backend/tests/unit/test_supplementary_search_service.py; print -r -- diff_exit="'$?' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
3855:/bin/zsh -lc 'git log --oneline --decorate 37387a86..HEAD' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
3863:**Verifying report artifact with AST**
4152:backend/lib/agentic_rag/retrievers/vault_notes_retriever.py:78:    # exam_board — 本 retriever 是 LangGraph 管道 retrieve_vault_notes 节点
4246:/bin/zsh -lc "set -o pipefail; git grep -h \"doc_type\" 37387a86 -- \"backend/app/*.py\" \"backend/lib/*.py\" | grep -oE \"[\\\"'][a-z_]+[\\\"']\" | sort | uniq -c | sort -rn >/dev/null; print -r -- pipeline_exit="'$? stages=${pipestatus[*]}' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
4253:/bin/zsh -lc "git rev-parse --verify '37387a86"'^{commit}'"' && git rev-parse --disambiguate=37387a86 && git rev-parse --disambiguate=73579b22f7a5 && git rev-parse --disambiguate=5ff331040905" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
4256:37387a8662e9dd646fad5628841679d777cb7eae
4258:37387a8662e9dd646fad5628841679d777cb7eae
4430:- ✅ **T2 Concepts 视图化**（commit `487d7851`）: 新 `canvas-vault/.claude/scripts/sync_board_concepts.py`（真相源=节点 `source_board`，零外部依赖，tmp+os.replace 原子写，比对**排除 synced 时间戳**否则 `--check` 永远报漂移）。⛔ 托管区间取**包络**（实测 6 板两种历史形态）且 **sentinel 存在时并进段内游离概念行**——插件 `appendBoardLines`(main.ts:2558) 插在**整段边界前**即落在 END 之外，只取 BEGIN..END 会留重复行（已按插件真实语义写模拟器复验）。写侧三点接线（ai-linked-doc Step7 / configure-whiteboard Step6 / quiz-answer 新 Step4c-bis）+ 模板换 sentinel 空块；⛔ 顺带修真缺口：configure-whiteboard Skill 此前**没给种子写 `source_board`**（plugin 有写、Skill 漏了）。双锁全绿 + doc_count 漂移×2 归零 + 关 Dataview 仍明文可读
4431:- ✅ **T3+T4+T5 八份 skill 接入**（commit `4244c021`）: canonical ROUTING 块 8 份逐字节相同（SHA `06b0167cc02c`），四平面 STRUCTURE/SEMANTIC/CONTENT/EXAM + HARD-NAV-1..4 + 每份 PLANE-BINDING 5 字段。旗舰 start-exam-board Step3 **19-26 次 → 1 次**、Step4.8 **零工具调用**、Step4 折入 calibration 删 Step5 独立 Grep、Step7 回执要求逐行照抄 `pick_rank`（可外部机械比对的锚点）；⛔ DD-13 修正 HARD CONSTRAINT #1 名实（澄清 HARD-21 管语义检索、与结构检索无关）；⛔ FALLBACK inline python 补 `effective()`——考察链是四方里唯一漏掉闲置折旧的一方（用户裁定 3）。configure-whiteboard Step4.2 全库唯一 O(节点数) 全节点 Read 循环 15→5 次；study-question §3.0 / chat-with-context 开场前**条件触发**限域（⛔ HARD-11/17/21 一字未动）；exam-quick/quiz-answer/node-chat 各写明**为什么禁用 STRUCTURE**
4456:- 🔒 [Code-Review] 独立对抗审查（E2E 复现式）**3 HIGH / 3 MEDIUM / 5 LOW → 全部处置, 复验 32/32 全绿**: ⛔ H1 orphans 回显通道（source_board 塞定义全文进 exam 视图, 已复现）→ reason 定长枚举文案+raw 截断 120+模型 max_length 门; ⛔ H2 parse_errors 回显（last_examined repr 无界+纯 Python yaml loader str(e) 引用原文行含 correction 禁串）→ _safe_err 去内容化（异常类型+行号）+repr[:80]+模型 200 字门; ⛔ H3 untrusted 标量炸投影（`doc_count: 大约五个`/`title: 2026` → ValidationError 500 整端点含列板）→ _bounded_str 类型归一×7 字段+双暴露面 ValidationError 纵深兜底; M4 digest 吸入相邻 [!feedback]/[!hint] callout（可含正确答案）→ callout 边界终止收集; M6 #heading 锚点+大小写敏感→假孤儿（喂 H1 通道）→ resolve 剥锚点+boards_ci casefold 匹配; M7 金集合成A恒真条件（自比较）→ 改「挖掉 reason 槽位后 0 命中」; M8 禁串无正向对照会静默腐烂→禁串必须仍在 vault 源文件+G5 digest 非空对照（金集 31→32 条）; L 批: 快照 tmp 唯一名防竞态/load 快照 schema 必备键校验/exam_board_count 恒用 full 历史/信封字段统一截断/set_current_subject_id 移到 fail-close 之后。审查确认: 投影穿透 E2E 失败（防线真实）、快照双黑名单成立、serve 路径唯一、pick 数学锁死、无 DD-03 违规。新增回归锁 6 条（契约 77 绿）
4465:- ✅ **三决策用户已裁定（全采纳推荐项）**: ① **f06/h07 移 shadow**（金集 v2, 58 条; 基线: MRR 0.7889/nDCG 0.7121/交付 84.91%/污染 38.60%/FPR 6%; 红档只剩 f04/z04 真实能力缺口; file_locate 意图路由 backlog, exam_board 任何方案绝不放行）② **f04 扩池不做**（扩池仅 file 级 rank4、+31% 延迟 — 根因段落级召回, backlog 等 chunk 侧补强）③ **[!note] STRIP 维持现状**（census 零误伤实锤）
4466:- ⏭ **下一步**: 九阶段路线（0→1→1.5→**2 ✅**→2.5→2.6→3→4→4.5）进 **2.5/2.6**（开工前重读九阶段路线定义 `_bmad-output/研究/2026-08-02-RAG修复计划-用户审阅版.md` §施工顺序与工期 L93 — A-1 修正于 R11-BATCH2: 原指 `2026-08-09-RAG阶段2-强化fastpath实施计划.md`，该文件存在但仅 36 行、是阶段 2 的单阶段计划，不含九阶段路线，反而把 2.5/2.6/4.5 列入「明确不做」）; 阶段 2 backlog 汇总: CE 盲区类（a01/z02/z05/特征共词）/ f04 段落级召回 / file_locate 意图路由 / extended 分支 taint / MCP top_k 漂移 / tier-2 legacy exam_board / RETRIEVAL_RERANKER_* compose 白名单
4467:- ✅ **T6 验证收尾完成**（17-agent workflow: 4 路验证 + 3 lens 全链路对抗审查 + 逐 finding 证伪）: 金集终验通过 + shadow 空（设计态）; live 实测 9 项全 PASS（hook 四态/MCP confidence/考察隔离/M6 410/refresh-changed 存活/18012 双向可达）; **[!note] STRIP census 实锤零误伤**（206 md 仅 1 处且嵌套 error-candidate 内被 EXTRACT 保留; info/video 55 处全系统模板）; **vq-f04 扩池实测**（50 池 file 级 rank4 但「烘」段落仍不召回, 延迟 +31%）; **vq-f06/h07 结构性死档实锤**（期望文件全 doc_type=whiteboard 被查询侧排除, 反事实去排除 rank1 立即回归, 选项 B>A>C 待用户裁定）
4468:- 🔒 [Code-Review] T6 全链路审查 **8 CONFIRMED / 2 REFUTED → 全部处置**: ⛔ **HARD-ISO live 泄漏**（vault_notes_retriever 默认排除表漏 exam_board, 经无鉴权 /api/v1/rag/query + agents.py 六处可达 → 补齐; react_agent/tool_executor/agent_graph 三条 flag-gated 链同批纵深补齐）; **fts_confirmed 名实颠倒**（_rrf_score 写给所有融合行, dense-only 恒 True/真词法命中反 False → _rrf_fuse 新 _fts_hit 通道标记 + 白名单 + svc 公式改 `_fts_hit and not _fts_only`, 仍遥测-only）; **检索层故障吞噬纵深**（_search_internal 全分支故障 raise 受 enable_fallback 门控[默认 True 调用方行为不变] + open_table 失败 raise + hook singleton 关吞噬/init 失败不缓存 + 空交付文案不再主动断言「检索正常」）; ⛔ **elbow telescoping = 三轮金集 A/B 裁决保留 T4 行为**（审查数学观点成立, 但两种修复均被金集打回: 全量序列 floor → 污染 39.83→57.38%/FPR 8%; dedup 后门前 floor → 48.25%/8%; +1.8pp 命中换不回 +8~17pp 污染 — 门后 telescoping 截断是净正收益保守护栏, 数据与翻案条件锁进 test_gate_thinning_elbow_is_deliberate_t4_behavior）; REFUTED×2: react_agent/agent_graph「拨真即泄漏」不可达（仍随批纵深补齐排除表）; LOW backlog: extended 分支无 taint / MCP top_k 参数漂移 10vs15 / TYPE_WEIGHTS concept 死键
4474:- ✅ **T5 链统一+诚实遥测已落地**: MCP `search_notes` fast path 改走共享后处理（`search_supplementary` + `include_content` profile, 生产参数 0.50/0.25）→ hybrid FTS+RRF/加权序/taint(含全文扫描)/空文档检测/源文件 dedup/CE 门在 MCP 链全部生效, score 量纲=加权分; **retrieval_confidence 双面注入**（hook XML 根元素 `confidence="high|medium|low|none"` 离散档 + MCP 顶层 `retrieval_confidence` 字段——⛔ pydantic 模型已声明防 response_model 裁剪; 裸分数不进 prompt 面, `ce_score not in xml` 契约保持）; **hook 降级失明修复**（client未就绪/5s超时/异常/空交付四分支注入 `degraded/reason/confidence` 标注 XML, exam-skill/system-op/短句跳过保持零注入）; **M6 incremental 端点 410 退役**（指引走 `/api/v1/index/refresh-changed`, 照 vault.py P0-3 姿势）; Step 0 vector 回退分支补 exam_board（HARD-ISO 旁路堵死）
4476:- 🔒 [Code-Review] T5 独立对抗审查 2H/2M/2L → **全修**: HIGH-1 基础设施故障被吞成 ok_empty（fast client `enable_fallback=False` + `_two_tier_search` 两级全败 raise 走 search_failed + `_fast_path_search` embedding 预检恢复阶段0语义, 真实路径回归锁×2）/ HIGH-2 MCP 全文交付但 taint 只扫 300 字 snippet（content 挂载前移进扫描面, 交付面=扫描面）/ MEDIUM-3 tainted 材料 metadata 收窄（doc_type/source_type frontmatter 自由文本不随隔离材料外带）/ MEDIUM-4 enrich-context rerank 后 confidence 失真（摘除不渲染, 重算留待后续）; LOW-6 tier-2 legacy 表无 exam_board 排除 → backlog（env-gate 默认关, 暴露≈0）
4478:- ⏭ **T6 验证收尾**: 金集终验+live 实测+对抗审查+用户 UAT 卡（产品语言; ⚠️ 问句/探针分两条消息的坑写进卡模板）; **待用户决策（勿擅自做）**: vq-f06/h07 whiteboard 排除与金集期望冲突（file_locate 放行 or 修订金集升 version）、vq-f04 扩池≥50（延迟代价）、`[!note]` STRIP 误伤面 census
4483:- ⚠️ T4 已知边界（T5 靶）: CE 盲区类 query 交付丢失（h08「我做过哪些笔记」meta/z02 转述/z05/a01 — CE 分与垃圾区间重叠, 纯 CE 无解 → T5 fts_confirmed+intent 信号收复, `ce_gate_all_filtered` 日志信号已铺好）; vq-f04 需扩池≥50、f06/h07 是 whiteboard 排除与金集期望冲突（用户决策）、z04 稠密召回失败; 代码块原子 chunk >2000 字残余 CE 盲区; RETRIEVAL_RERANKER_* 未进 docker-compose environment 白名单（回落链可用, 加白名单需 recreate）
4487:- ✅ **T3 chunk 改造已落地**（lancedb_client.py 单文件）: 段落级三级切分(段落→句子→子句)+overlap 段落化 / callout 三级分级(EXTRACT question/error/error-candidate 独立成块; STRIP info/video/note+"💬 围绕这个概念讨论"模板标记; KEEP 其余) / 模板样板 section 零 chunk / **考察文件 exam_question_id→exam_board 推断堵题面泄漏**(用户截图 rank3 考察文件已从检索消失, 索引唯一考察文件已转 exam_board) / 短块(<150tok)面包屑只留文件名 / line_start 补 frontmatter 偏移。金集: recall **90.91%**(+1.8pp) 假阳性 **58→42%** 污染@10 24.17% nDCG 0.6415(容差内) 交付 81.82% 持平; vq-a02 咖啡 rank 7→4, vq-a03 rank1 交付 9 条; 基线已锁(history 归档)。契约测试 21 条(组A-F), regression 全绿
4488:- 🔒 [Code-Review] T3 独立对抗审查 0C/1H/2M/5L → **HIGH-1(YAML 解析失败绕过 exam_board 推断=泄漏复活, 已修嗅探兜底)+MEDIUM-1(紧贴 callout 吞批注, 已修断块)+MEDIUM-2(占位误杀, 已收紧)+LOW-4(tiktoken 冷启动, 已降级兜底) 全修**+4 红线测试; 未修 backlog: LOW-1 超长 EXTRACT 降级切分丢 [!question] 标记 / LOW-3 [!note] STRIP 误伤面待 census 复核 / LOW-5 建议 exam-quick.ts frontmatter 标量加引号(前端, 勿混本批)
4605:batch2_progress: "A1 done(2026-07-23): 衰减Beta后验落地 — 单一真相源 canvas-vault/.claude/scripts/decay_beta.py(γ=0.9, 先验Beta(0.9,2.1), FLOOR=0.05防退化—单测抓到连续同质满分下b→0致σ=0) + quiz-answer写分段替换EMA(mastery_a/b状态量+legacy等效样本量3迁移+幂等保持) + start-exam-board选点段(pick=μ−σ静态python, 未考先验自动优先, 破P3死循环) + 7条数学性质单测(σ单调/状态跳变10次内恢复/纯Beta对照/迁移/选点/钳制) + 端到端实测(迁移0.4→0.54→幂等→0.64) + 已部署主仓vault现场。A2-A4+线2+线3 done(2026-07-23): A2弃答通道(quiz-answer弃答词≤10字符→grade_norm=0+abandoned:true+疑问归纳, 真空答案才拒) A3增量归纳(done板新疑问仅归纳不重评分, incr python段) A4题目去重(start-exam-board Step4.8回读历史白板+HARD-DEDUP变体铁律; quiz-answer写attempt_count/last_examined) ∥ 线2 search_memories确定性触发(chat-with-context HARD-20+node-chat硬约束7+vault CLAUDE.md, 回忆式提问必查图谱禁编造) ∥ 线3 RAG三死因修复(agentic_rag GraphitiClient: 死因1裸构造缺key→复用worker本地栈实例; 死因2 canvas_file当group_id→_resolve_group_ids正规推导+物理化; 死因3 200ms超时→读2s/写30s解耦) + 顺手补 search_error_memories 本体(BUG-32DB6194 现网500→200, /enrich-context端到端通, 139ms)。验证: G0门禁5指标零回退+regression 115passed+vault文件已部署主仓。批次2'全清。批次3'反馈闭环 done(2026-07-23): P14a蒸馏classify返回值不再丢弃→classify_with_pedagogy+write_error_dual(candidate_only)落候选区 + P14b post-turn-extract切candidate_only(当年注释说切没切,AI抽错误绕候选区直写errors[]两个月) / dispute三件套齐: 不入图(状态机已有)+出题排除(targeting按disputed文本拦截errors[]/tips[])+可追溯(candidate_disputed事件=suppression log) / calibration最小消费者(start-exam-board校准差≥0.3→强制辨析反例题型,幻觉性掌握识别) / learning_events.jsonl(app/services/learning_event_log.py, vault根append-only, 幂等键+版本+双时间戳+8类白名单, 写点: 蒸馏candidate_created+accept+dispute+session_archived+quiz answer_scored/abandoned+exam_created; node_derived留批次4')。heredoc缩进炸弹修复(A3/选点段列表缩进会致IndentationError,ast抽验抓到,全部顶格化)。验证: G0门禁零回退+regression 123passed+SKILL已部署。批次4' done(2026-07-23): R4 CJK analyzer(listAvailableAnalyzers实证cjk可用→4索引重建ONLINE, ensure_fulltext_index同步防回退, DDL存档rebuild_fulltext_cjk.cypher) / 检索束(term_aliases.py中英双向术语表+expand_query拼接式单次查询, recall@5 59.09%→68.18%+9pt, mem-05/11「代理→agent」被救活, 基线已重固化) / 3-1理解快照随边(ai-linked-doc relationships[]写derived_at+source_mastery_at_derivation+confusion, sync透传入CANVAS_EDGE) / 3-2投影边ON CREATE created_at+targeting邻居改时间倒序 / 3-3幽灵边对账(sync收尾把不在活集合的frontmatter边软失效invalidated_at, 复活自动撤标, targeting过滤失效边; 边身份source→type→target已合规reason走属性更新) / node_derived事件(ai-linked-doc单行模板实测通)。验证: G0门禁零回退+regression 129passed+SKILL已部署。MEM-FLYWHEEL 批次0→G0→1'→2'→3'→4' 全部完成。下一步: 后续轨道(C0分叉合并/C1管道修复/C3 BKT-FSRS五信号融合)或用户UAT实操验收整轮"
4824:**Verifying zero changes in isolation files and AST**
4835:  ✓ 复验注释-only、隔离面及报告 §1/§4/§8
4859:  ✓ 复验注释-only、隔离面及报告 §1/§4/§8
4876:| reranker 陈旧 floor 注释 | **CLOSED** | 现注释已正确标为历史算例；行为 AST 未变。 |
4886:其他铁律均通过：
4888:- 两个目标 Python 文件的无属性 AST 完全相等：reranker AST SHA `18aae6e0…`，search AST SHA `03e79eea…`；diff 仅注释。
4912:| reranker 陈旧 floor 注释 | **CLOSED** | 现注释已正确标为历史算例；行为 AST 未变。 |
4922:其他铁律均通过：
4924:- 两个目标 Python 文件的无属性 AST 完全相等：reranker AST SHA `18aae6e0…`，search AST SHA `03e79eea…`；diff 仅注释。
  4757	├── 5-ge-3-query-time-flush.md             # Session C (4h) — 波 2
  4758	├── 5-ge-4-relationship-sync-production.md # Session C (2h) — 波 2
  4759	└── 5-ge-5-graphiti-relation-service-facade.md  # Session D (3h) — 波 3 (等 B done)
  4760	```
  4761	
  4762	### Sprint 2 v3 三波次 (ChatGPT 校正, 非纯 5 并行)
  4763	
  4764	```
  4765	波一: A (UX/UAT) ‖ B (5-ge-1 schema) ‖ E (1.16/2.10 scaffold, 不锁 payload)
  4766	波二: C (5-ge-2/3/4) ‖ E (对齐 5-ge-1 后完成 payload) ‖ A (1.18/1.19 收尾)
  4767	波三: D (5-ge-5 facade) → LITE-4-3 (等 2.10+facade) → LITE-5-7 AC#1 patch only
  4768	```
  4769	
  4770	硬依赖: B↔E 协议依赖 (E 不能在 B schema 定版前合并 payload) / C↔D 服务依赖 (D 依赖 C belief+flush contract).
  4771	**3 接口契约 + 6 硬规则见 `_bmad-output/.claude/CLAUDE.md` §Graphiti Runtime 体系契约**.
  4772	
  4773	### ⚠️ V-07/V-08/V-10/V-11 旧修复方案状态 (重要 — 防新 session 误读)
  4774	
  4775	- ❌ **V-07** `1-16-callout-graphiti-hook` 加 5 字段 — **superseded by 5-ge-1** (callout 走 unified schema)
  4776	- ❌ **V-10** `questions_registry` 新表 — **superseded by 5-ge-2** (belief_key 版本链更通用)
  4777	- ⚠️ **V-08** `LITE-4-3` 路线 0 wikilink 邻居 — **partial superseded by 5-ge-5 facade** (路线 4 改调 facade)
  4778	- ⚠️ **V-11** `LITE-5-6` dual-write — **partial superseded by 5-ge-1** (calibration 走 unified schema)
  4779	
  4780	### 接续上手 5 min 命令
  4781	
  4782	```bash
  4783	git pull
  4784	cat _bmad-output/审查/2026-05-26-bmad-spec-体系全图诊断.md  # 体系决策依据
  4785	cat _bmad-output/implementation-artifacts/epic-5-graphiti-era/README.md  # 5 session mapping
  4786	cat _bmad-output/implementation-artifacts/sprint-status.yaml | grep -A 8 "STORY-5-ge-1\|STORY-NEW-UX-001"
  4787	# 选 session A/B/C/E 一个起步 (D 等 B done)
  4788	```
  4789	
  4790	---
  4791	
  4792	## §1 · 新 session 5 min 启动检查清单
  4793	
  4794	1. ☐ `git status` 干净（或了解 uncommitted 修改）
  4795	2. ☐ `git log --oneline -5` 看到 `769d59a`（INFRA-001/004） + `548d14d`（INFRA-002）
  4796	   - ⚠️ 若 commit 不在 git log → 当前 worktree 没拉到 chat history 的实施 commit，需用户介入确认
  4797	3. ☐ 读 `_bmad-output/implementation-artifacts/sprint-status.yaml::sprint_v3_obsidian_hybrid` 次 ready story = `INFRA-003`
  4798	4. ☐ 读当前 Story spec 或 entry，确认**无** `[DEPRECATED]` marker（防新 session 误读旧 spec）
  4799	5. ☐ `python3 .scripts/smoke_test.py` PASS（验证 import 闭合）
  4800	
  4801	## §2 · 当前状态（2026-05-24 Sprint v3 BMAD 化完成时）
  4802	
  4803	- ✅ **Sprint 1 Day 1 完成**（3/25 stories done）
  4804	  - INFRA-002（app_factory + 18 router 装配）@ commit `548d14d`
  4805	  - INFRA-001（grading EventBus 修复）@ commit `769d59a`
  4806	  - INFRA-004（pyproject deps）@ commit `769d59a`
  4807	- 🟡 **Day 2 待干**（3 stories, 6h）— 下一个 `INFRA-003`
  4808	  - INFRA-003（1h, docker healthcheck 修）← **下一个 Story**
  4809	  - EXAM-001（3h, /api/v1/exam/grade endpoint）
  4810	  - EXAM-002（2h, /api/v1/exam/quick endpoint）
  4811	- ⏳ **Day 3-10 计划** 17 stories（含 6 Lite 重编 + WIKILINK-GRAPHITI 新需求）
  4812	
  4813	## §3 · 接下来 8 步开干流程（新 session 第 1 个动作）
  4814	
  4815	
  4816	**Noting stale CURRENT_TASK traceability issue**
  4817	**Identifying potential DD14 commit message violation**
  4818	**Verifying plan ID format in commit**
  4819	**Verifying git status accuracy**
  4820	**Assessing report metadata accuracy**
  4821	**Confirming incomplete acceptance status**
  4822	**Compiling closure status table for seven items**
  4823	**Planning detailed linked line citations with concise labels**
  4824	**Verifying zero changes in isolation files and AST**
  4825	**Clarifying isolation modification terminology**
  4826	**Summarizing section code and data matches**
  4827	2026-08-28T11:42:44.530390Z ERROR codex_core::tools::router: error=timeout_ms must be at least 10000
  4828	collab: Wait
  4829	**Searching for get_type_weight call sites**
  4830	**Updating plan status**
  4831	三条只读证据轨及主审交叉复算完成；代码/报告与 live 命令通过，测试输出内容通过，但 metadata 的精确复跑 recipe 仍有占位符和漂移 HEAD，正在汇总终裁。
  4832	  ✓ 冻结 HEAD、工作树、证据文件与基线对象
  4833	  ✓ 复算测试 provenance、完整捕获与归一化 byte diff
  4834	  ✓ 解析并实际复跑 live-distribution/value-grep 两条命令
  4835	  ✓ 复验注释-only、隔离面及报告 §1/§4/§8
  4836	  → 交叉核验后输出逐项终裁、新发现与限制
  4837	mcp: sequential-thinking/sequentialthinking started
  4838	mcp: sequential-thinking/sequentialthinking (completed)
  4839	mcp: sequential-thinking/sequentialthinking started
  4840	mcp: sequential-thinking/sequentialthinking (completed)
  4841	**Adding final git status check**
  4842	exec
  4843	/bin/zsh -lc 'git status --short --branch && git diff --quiet; print -r -- tracked_worktree_diff_exit=$? && git diff --cached --quiet; print -r -- index_diff_exit=$?' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
  4844	 succeeded in 0ms:
  4845	git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
  4846	## card/s5-census
  4847	?? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-16-round4.md"
  4848	?? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round4.md"
  4849	git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
  4850	tracked_worktree_diff_exit=0
  4851	git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
  4852	index_diff_exit=0
  4853	
  4854	**Planning update strategy**
  4855	终裁证据矩阵已交叉核验完成；全程无 tracked/index 修改。
  4856	  ✓ 冻结 HEAD、工作树、证据文件与基线对象
  4857	  ✓ 复算测试 provenance、完整捕获与归一化 byte diff
  4858	  ✓ 解析并实际复跑 live-distribution/value-grep 两条命令
  4859	  ✓ 复验注释-only、隔离面及报告 §1/§4/§8
  4860	  ✓ 交叉核验后输出逐项终裁、新发现与限制
  4861	**Outlining final summary structure**
  4862	**Compiling citation details and item status**
  4863	**Verifying commit artifact integrity**
  4864	**Classifying new findings and limitations**
  4865	**Noting pytest rerun omission for report**
  4866	codex
  4867	总裁定：**6/7 CLOSED，仍阻断，不可验收。**  
  4868	`fce0d8a2800768a039f0aa05de7a5504d79f63d8` 的代码、归一化结果和 live 命令均基本成立；唯一未闭合项仍是 **MEDIUM-5 的确定性重放 provenance**。
  4869	
  4870	| 项目 | 终裁 | 依据 |
  4871	|---|---|---|
  4872	| HIGH-3 自由值路径条件 | **CLOSED** | [报告 §4](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-doc-type-census-2026-08-28.md:57) 与 `source_type` 路径二分代码一致。 |
  4873	| MEDIUM-3 写侧摘要 | **CLOSED** | [§1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-doc-type-census-2026-08-28.md:31) 和 [§8](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-doc-type-census-2026-08-28.md:90) 均为“两显式生产者 + 无校验通用 sink”，与 [add_documents](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/lib/agentic_rag/clients/lancedb_client.py:3615) 一致。 |
  4874	| MEDIUM-5 测试 provenance | **NOT-CLOSED** | stdout 工件有效，但 metadata 没有可原样复跑的两条精确命令。 |
  4875	| `source_type` 非纯路径启发 | **CLOSED** | image OCR 显式赋值及 neighbor runtime 赋值均与 [§8](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-doc-type-census-2026-08-28.md:90) 一致。 |
  4876	| reranker 陈旧 floor 注释 | **CLOSED** | 现注释已正确标为历史算例；行为 AST 未变。 |
  4877	| live/value-grep 命令 | **CLOSED** | 两条命令 `zsh -n` 均为 0，Docker 与 pinned grep 均真实复跑成功。 |
  4878	| 根 scripts 行号 | **CLOSED** | `migrate:62`、`sync:63/:85` 均复核正确。 |
  4879	
  4880	MEDIUM-5 的分层结果：
  4881	
  4882	- **PASS：产物和声明自洽。** 两份 SHA-256 与 [metadata](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-evidence/test-run-metadata.txt:13) 相符；均为 109 行、9957 bytes、111 collected、9 failed/102 passed、`exit_code=1`。
  4883	- **PASS：归一化没有掩盖实质差异。** 原始 diff 只有 9 处 CPython 对象地址和 `0.47s→0.45s`。仅应用声明的两条规则后，双方均为 9912 bytes、SHA-256 `03e576078dbc5c854b1db7695c1a654195afa69f52f5212d79577e491fde84e8`，byte-equal。
  4884	- **FAIL：重放 recipe 仍不确定。** [metadata:8](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-evidence/test-run-metadata.txt:8) 保留 `<out>`，`:16` 保留 `<同两文件>`；两行原样 `zsh -n` 都 exit 1。after 还使用会漂移的 `HEAD`，没有绑定完整运行 commit/tree。blob 前缀足以人工重建，但不等于文件所称的“记录两次命令”。
  4885	
  4886	其他铁律均通过：
  4887	
  4888	- 两个目标 Python 文件的无属性 AST 完全相等：reranker AST SHA `18aae6e0…`，search AST SHA `03e79eea…`；diff 仅注释。
  4889	- 隔离逻辑零行为改动；`exclude_doc_types`、Tier-2 边界和 SQL `NOT IN` 均未变。
  4890	- §1 pinned grep 独立得到 **18 文件/146 行**，与清单 SHA-256 `94b01dc3…` 逐字节一致；§4 live 分布复跑仍为 `2203 = 2001/117/69/16`；§8 与真实赋值链一致。
  4891	
  4892	新发现：**BLOCKER 0 / HIGH 0 / MEDIUM 1 / LOW 2**。
  4893	
  4894	- **MEDIUM，阻断，归并 MEDIUM-5**：命令模板不可执行且运行树未固定。
  4895	- **LOW**：“完整 traceback”实际是完整保存 pytest 配置的 `--tb=short` 输出。
  4896	- **LOW**：[live 证据](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-evidence/live-distribution-and-value-grep.txt:5) 是格式化展示而非原始 stdout；Docker 行增加标签，grep 的并列项顺序受 locale 影响，但数值/字面量同集，不阻断。
  4897	
  4898	全程未修改 tracked 文件或 index；两份既存未跟踪 round-4 稿件保持未触碰。`graphiti-canvas` 本轮未暴露，因此无法执行 Graphiti 搜索；本裁定基于本地 Git 对象、代码、证据 bytes 和只读 Docker 查询。
  4899	
  4900	
  4901	tokens used
  4902	170,933
  4903	总裁定：**6/7 CLOSED，仍阻断，不可验收。**  
  4904	`fce0d8a2800768a039f0aa05de7a5504d79f63d8` 的代码、归一化结果和 live 命令均基本成立；唯一未闭合项仍是 **MEDIUM-5 的确定性重放 provenance**。
  4905	
  4906	| 项目 | 终裁 | 依据 |
  4907	|---|---|---|
  4908	| HIGH-3 自由值路径条件 | **CLOSED** | [报告 §4](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-doc-type-census-2026-08-28.md:57) 与 `source_type` 路径二分代码一致。 |
  4909	| MEDIUM-3 写侧摘要 | **CLOSED** | [§1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-doc-type-census-2026-08-28.md:31) 和 [§8](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-doc-type-census-2026-08-28.md:90) 均为“两显式生产者 + 无校验通用 sink”，与 [add_documents](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/lib/agentic_rag/clients/lancedb_client.py:3615) 一致。 |
  4910	| MEDIUM-5 测试 provenance | **NOT-CLOSED** | stdout 工件有效，但 metadata 没有可原样复跑的两条精确命令。 |
  4911	| `source_type` 非纯路径启发 | **CLOSED** | image OCR 显式赋值及 neighbor runtime 赋值均与 [§8](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-doc-type-census-2026-08-28.md:90) 一致。 |
  4912	| reranker 陈旧 floor 注释 | **CLOSED** | 现注释已正确标为历史算例；行为 AST 未变。 |
  4913	| live/value-grep 命令 | **CLOSED** | 两条命令 `zsh -n` 均为 0，Docker 与 pinned grep 均真实复跑成功。 |
  4914	| 根 scripts 行号 | **CLOSED** | `migrate:62`、`sync:63/:85` 均复核正确。 |
  4915	
  4916	MEDIUM-5 的分层结果：
  4917	
  4918	- **PASS：产物和声明自洽。** 两份 SHA-256 与 [metadata](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-evidence/test-run-metadata.txt:13) 相符；均为 109 行、9957 bytes、111 collected、9 failed/102 passed、`exit_code=1`。
  4919	- **PASS：归一化没有掩盖实质差异。** 原始 diff 只有 9 处 CPython 对象地址和 `0.47s→0.45s`。仅应用声明的两条规则后，双方均为 9912 bytes、SHA-256 `03e576078dbc5c854b1db7695c1a654195afa69f52f5212d79577e491fde84e8`，byte-equal。
  4920	- **FAIL：重放 recipe 仍不确定。** [metadata:8](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-evidence/test-run-metadata.txt:8) 保留 `<out>`，`:16` 保留 `<同两文件>`；两行原样 `zsh -n` 都 exit 1。after 还使用会漂移的 `HEAD`，没有绑定完整运行 commit/tree。blob 前缀足以人工重建，但不等于文件所称的“记录两次命令”。
  4921	
  4922	其他铁律均通过：
  4923	
  4924	- 两个目标 Python 文件的无属性 AST 完全相等：reranker AST SHA `18aae6e0…`，search AST SHA `03e79eea…`；diff 仅注释。
  4925	- 隔离逻辑零行为改动；`exclude_doc_types`、Tier-2 边界和 SQL `NOT IN` 均未变。
  4926	- §1 pinned grep 独立得到 **18 文件/146 行**，与清单 SHA-256 `94b01dc3…` 逐字节一致；§4 live 分布复跑仍为 `2203 = 2001/117/69/16`；§8 与真实赋值链一致。
  4927	
  4928	新发现：**BLOCKER 0 / HIGH 0 / MEDIUM 1 / LOW 2**。
  4929	
  4930	- **MEDIUM，阻断，归并 MEDIUM-5**：命令模板不可执行且运行树未固定。
  4931	- **LOW**：“完整 traceback”实际是完整保存 pytest 配置的 `--tb=short` 输出。
  4932	- **LOW**：[live 证据](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-evidence/live-distribution-and-value-grep.txt:5) 是格式化展示而非原始 stdout；Docker 行增加标签，grep 的并列项顺序受 locale 影响，但数值/字面量同集，不阻断。
  4933	
  4934	全程未修改 tracked 文件或 index；两份既存未跟踪 round-4 稿件保持未触碰。`graphiti-canvas` 本轮未暴露，因此无法执行 Graphiti 搜索；本裁定基于本地 Git 对象、代码、证据 bytes 和只读 Docker 查询。
  4935	
  4936	

**Planning file isolation inspection**
exec
/bin/zsh -lc 'rg -n "git.*diff.*lancedb_client|git.*diff.*tool_executor|git.*diff.*react_agent|git.*diff.*agent_graph|git.*diff.*vault_notes_retriever|isolation|exclude_doc_types|NOT IN" _bmad-output/审查/codex-review-CARD-G4-16-round4.md | tail -n 200' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
35:scope: Read-only, parallel audit of vault admission/indexing, Graphiti quarantine isolation, SnapshotV3, and recovery-anchor closure claims.
367:backend/tests/regression/test_targeting_material_isolation.py
384:backend/tests/regression/test_p03_vault_isolation.py
682:backend/scripts/migrate_canvas_group_isolation.py
861:_bmad-output/implementation-artifacts/epic-1/1-9-lancedb-vault-id-isolation.md
893:backend/tests/integration/test_subject_isolation_neo4j.py
950:backend/tests/integration/test_multi_vault_isolation.py
961:backend/tests/integration/test_learning_context_group_isolation.py
978:_bmad-output/implementation-artifacts/epic-4/4-1-exam-isolation-anti-nesting.md
1015:_bmad-output/implementation-artifacts/epic-2/2-5-y-isolation-hardening-subject-config-reuse.md
1055:backend/tests/unit/test_lancedb_vault_isolation.py
1058:backend/tests/unit/test_exam_sync_node_group_isolation.py
1072:backend/tests/unit/test_subjects_group_isolation.py
1077:backend/tests/unit/test_subject_isolation.py
1115:backend/tests/unit/test_enrich_context_vault_isolation.py
1147:backend/tests/unit/test_migrate_canvas_group_isolation.py
1182:backend/tests/unit/test_sync_group_isolation.py
1216:backend/tests/unit/test_lancedb_isolation_assertions.py
1228:backend/tests/unit/test_cross_subject_bridge_group_isolation.py
1279:_bmad-output/research/chatgpt-deep-research-story-2.5-sovereignty-isolation-2026-05-04.md
1291:_bmad-output/research/chatgpt-round2-reply-story-2.5-sovereignty-isolation-2026-05-04.md
1309:_bmad-output/research/chatgpt-round2-cross-check-story-2.5-sovereignty-isolation-2026-05-04.md
1324:backend/migrations/003_canvas_group_isolation.cypher
1411:_bmad-output/验收单/Story-2.5.Y-isolation-hardening.md
2145:    43	- **排除过滤（真实消费主链）**：`exclude_doc_types=["whiteboard","exam_board"]` 于 react_agent:115/:124、tool_executor:112/:122、agent_graph:208、supplementary_search_service:834/:849 显式传入，vault_notes_retriever:82 为默认值——共 7 处显式 + 1 处默认，SQL `NOT IN` 落到 lancedb doc_type 列。**边界（Codex round-1 MEDIUM-4）**：该隔离只覆盖默认 Tier-1 路径——`ENABLE_LANCEDB_TIER2_FALLBACK`（默认关闭）开启后 legacy tier-2 直查裸 `vault_notes` 无 doc_type WHERE（supplementary_search_service.py:863），"在库但检索不可见"仅在默认配置下成立（登记 FU-5）。这是检验白板信息隔离（Karpicke 主动回忆）的**读侧第二层防御**（第一层 = config.py 目录黑名单，:48-50 注释如实记录"验收单/_待处理 无 doc_type，单层防御"）。
2279:920:    20	- **CLOSED**：隔离相关文件零改动；search service 的 `exclude_doc_types` 与 Tier-2 代码也未变。
2412:    43	- **排除过滤（真实消费主链）**：`exclude_doc_types=["whiteboard","exam_board"]` 于 react_agent:115/:124、tool_executor:112/:122、agent_graph:208、supplementary_search_service:834/:849 显式传入，vault_notes_retriever:82 为默认值——共 7 处显式 + 1 处默认，SQL `NOT IN` 落到 lancedb doc_type 列。**边界（Codex round-1 MEDIUM-4）**：该隔离只覆盖默认 Tier-1 路径——`ENABLE_LANCEDB_TIER2_FALLBACK`（默认关闭）开启后 legacy tier-2 直查裸 `vault_notes` 无 doc_type WHERE（supplementary_search_service.py:863），"在库但检索不可见"仅在默认配置下成立（登记 FU-5）。这是检验白板信息隔离（Karpicke 主动回忆）的**读侧第二层防御**（第一层 = config.py 目录黑名单，:48-50 注释如实记录"验收单/_待处理 无 doc_type，单层防御"）。
2794:37387a86:backend/app/config.py:48:#:   - 检验白板: 双层 —— 目录黑名单 + 读侧 exclude_doc_types=["whiteboard","exam_board"]
2925:**Planning isolation scope definition**
2927:/bin/zsh -lc 'git diff --name-status 37387a86..HEAD -- "backend/app/config.py" "backend/app/services/react_agent.py" "backend/app/services/tool_executor.py" "backend/lib/agentic_rag/agent_graph.py" "backend/lib/agentic_rag/retrievers/vault_notes_retriever.py" "backend/app/services/supplementary_search_service.py"' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
2933:/bin/zsh -lc 'git diff -U0 37387a86..HEAD -- backend/app/services/supplementary_search_service.py | rg -n "''^[+-].*(exclude_doc_types|ENABLE_LANCEDB_TIER2_FALLBACK|vault_notes|WHERE|doc_type)"' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
2940:**Verifying isolation zero changes and test baselines**
2981:2754:                # MCP 链现有的 doc_type NOT IN (...) 排除自动生效; 文件仍在索引,
2989:2981:        exclude_doc_types: Optional[List[str]] = None,
2991:3038:                    exclude_doc_types=exclude_doc_types,
2993:3104:        exclude_doc_types: Optional[List[str]] = None,
2996:3117:        - exclude_doc_types param → 'doc_type' column NOT IN (exclude mode)
3003:3139:        if exclude_doc_types:
3004:3140:            quoted = ", ".join(f"'{self._escape_sql(t)}'" for t in exclude_doc_types)
3005:3141:            clauses.append(f"(doc_type NOT IN ({quoted}) OR doc_type IS NULL)")
3007:3163:        exclude_doc_types: Optional[List[str]] = None,
3010:3191:            exclude_doc_types=exclude_doc_types,
3029:/bin/zsh -lc 'rg -n "exclude_doc_types|ENABLE_LANCEDB_TIER2_FALLBACK|vault_notes" backend/app/services/react_agent.py backend/app/services/tool_executor.py backend/lib/agentic_rag/agent_graph.py backend/lib/agentic_rag/retrievers/vault_notes_retriever.py backend/app/services/supplementary_search_service.py' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
3032:backend/lib/agentic_rag/agent_graph.py:208:                    exclude_doc_types=["whiteboard", "exam_board"],
3043:backend/app/services/supplementary_search_service.py:834:            exclude_doc_types=["whiteboard", "exam_board"],
3045:backend/app/services/supplementary_search_service.py:849:                exclude_doc_types=["whiteboard", "exam_board"],
3059:backend/app/services/tool_executor.py:112:                exclude_doc_types=["whiteboard", "exam_board"],
3061:backend/app/services/tool_executor.py:122:                    exclude_doc_types=["whiteboard", "exam_board"],
3064:backend/lib/agentic_rag/retrievers/vault_notes_retriever.py:66:        default_exclude_doc_types: RAG-P0 A3 (2026-05-10) — default exclude
3065:backend/lib/agentic_rag/retrievers/vault_notes_retriever.py:69:            queries. Pass exclude_doc_types=[] at call site to opt in.
3068:backend/lib/agentic_rag/retrievers/vault_notes_retriever.py:82:    default_exclude_doc_types: List[str] = field(default_factory=lambda: ["whiteboard", "exam_board"])
3069:backend/lib/agentic_rag/retrievers/vault_notes_retriever.py:101:        exclude_doc_types: Optional[List[str]] = None,
3072:backend/lib/agentic_rag/retrievers/vault_notes_retriever.py:144:        exclude_doc_types: Optional[List[str]] = None,
3074:backend/lib/agentic_rag/retrievers/vault_notes_retriever.py:179:            # RAG-P0 A3: caller's exclude_doc_types wins; fall back to
3075:backend/lib/agentic_rag/retrievers/vault_notes_retriever.py:181:            # Pass exclude_doc_types=[] explicitly to opt OUT of filtering.
3076:backend/lib/agentic_rag/retrievers/vault_notes_retriever.py:183:                exclude_doc_types if exclude_doc_types is not None else list(self.config.default_exclude_doc_types)
3078:backend/lib/agentic_rag/retrievers/vault_notes_retriever.py:192:                    exclude_doc_types=effective_exclude,
3101:backend/app/services/react_agent.py:115:            exclude_doc_types=["whiteboard", "exam_board"],
3103:backend/app/services/react_agent.py:124:                exclude_doc_types=["whiteboard", "exam_board"],
3328:  2754	                # MCP 链现有的 doc_type NOT IN (...) 排除自动生效; 文件仍在索引,
3534:   834	            exclude_doc_types=["whiteboard", "exam_board"],
3549:   849	                exclude_doc_types=["whiteboard", "exam_board"],
4270:   156	scope: Read-only, parallel audit of vault admission/indexing, Graphiti quarantine isolation, SnapshotV3, and recovery-anchor closure claims.
4411:- ✅ **C1 `32e9e29c` 写侧闭环**: SyncBatchRequest.vault_id 升必填（缺失 422，唯一调用方 DEPRECATED Tauri 前端属预期）; sync.py handler 显式接 resolve 返回值 → `to_physical_group_id` → `process_sync_batch(request, group_id=物理gid)`; 六条 Cypher MERGE/MATCH 键全部变 `{id, group_id}` 复合键（`_delete_board` 级联双侧都带 group）; canvas_projection_sync/exam_service_ext 三方共键同批切换; 新 `test_sync_group_isolation.py` 10 条**行为断言**（红灯先行，检查 run_calls 实际 Cypher+参数，教训锁: wave5 静态断言逃逸）
4412:- ✅ **C2 `496a2147` 迁移件**: `migrations/003` 五段式 + `scripts/migrate_canvas_group_isolation.py`（--dry-run/--apply, ⚠️ 不复用 group_id_migration_service 的 IS NOT NULL 扫描器）+ 11 条脚本测试
4824:**Verifying zero changes in isolation files and AST**
4825:**Clarifying isolation modification terminology**
4889:- 隔离逻辑零行为改动；`exclude_doc_types`、Tier-2 边界和 SQL `NOT IN` 均未变。
4925:- 隔离逻辑零行为改动；`exclude_doc_types`、Tier-2 边界和 SQL `NOT IN` 均未变。

**Inspecting output around line 2920-2945**
exec
/bin/zsh -lc "nl -ba _bmad-output/审查/codex-review-CARD-G4-16-round4.md | sed -n '2910,2960p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
  2910	/bin/zsh -lc "python3 -c 'import ast,hashlib,subprocess,sys; base=sys.argv[1]; paths=sys.argv[2:];
  2911	for p in paths:
  2912	 a=subprocess.check_output([\"git\",\"show\",f\"{base}:{p}\"])
  2913	 b=subprocess.check_output([\"git\",\"show\",f\"HEAD:{p}\"])
  2914	 da=ast.dump(ast.parse(a,filename=f\"{base}:{p}\"),include_attributes=False)
  2915	 db=ast.dump(ast.parse(b,filename=f\"HEAD:{p}\"),include_attributes=False)
  2916	 print(p,\"ast_equal=\"+str(da==db),\"base_ast_sha256=\"+hashlib.sha256(da.encode()).hexdigest(),\"head_ast_sha256=\"+hashlib.sha256(db.encode()).hexdigest())' 37387a86 backend/app/services/supplementary_reranker.py backend/app/services/supplementary_search_service.py" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
  2917	 succeeded in 0ms:
  2918	git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
  2919	git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
  2920	git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
  2921	git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
  2922	backend/app/services/supplementary_reranker.py ast_equal=True base_ast_sha256=18aae6e0a003d5282b3a6cdfc6ad30da6d4c7a46693f43305fbc31d9ab9cb288 head_ast_sha256=18aae6e0a003d5282b3a6cdfc6ad30da6d4c7a46693f43305fbc31d9ab9cb288
  2923	backend/app/services/supplementary_search_service.py ast_equal=True base_ast_sha256=03e79eeabbdfcc1c43087efe5396b171ea622d5bfeed61d8707a5f20c935603a head_ast_sha256=03e79eeabbdfcc1c43087efe5396b171ea622d5bfeed61d8707a5f20c935603a
  2924	
  2925	**Planning isolation scope definition**
  2926	exec
  2927	/bin/zsh -lc 'git diff --name-status 37387a86..HEAD -- "backend/app/config.py" "backend/app/services/react_agent.py" "backend/app/services/tool_executor.py" "backend/lib/agentic_rag/agent_graph.py" "backend/lib/agentic_rag/retrievers/vault_notes_retriever.py" "backend/app/services/supplementary_search_service.py"' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
  2928	 succeeded in 0ms:
  2929	git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
  2930	M	backend/app/services/supplementary_search_service.py
  2931	
  2932	exec
  2933	/bin/zsh -lc 'git diff -U0 37387a86..HEAD -- backend/app/services/supplementary_search_service.py | rg -n "''^[+-].*(exclude_doc_types|ENABLE_LANCEDB_TIER2_FALLBACK|vault_notes|WHERE|doc_type)"' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
  2934	 succeeded in 0ms:
  2935	git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
  2936	6:-        # doc_type=按类型加权与断言用 / fts_confirmed=双通道确认)
  2937	8:+        # 修订): doc_type 不参与加权 — 加权按材料 source_type 走
  2938	10:+        # 生产消费 = MCP note_search_tools 将 clean 材料的 doc_type 透传进
  2939	
  2940	**Verifying isolation zero changes and test baselines**
  2941	**Verifying code consistency with current line references**
  2942	exec
  2943	/bin/zsh -lc 'rg -n "frontmatter.*type|_infer_doc_type|doc_type|source_type.*image_ocr|neighbor_expansion|def add_documents|_is_video_transcript" backend/lib/agentic_rag/clients/lancedb_client.py' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
  2944	 succeeded in 0ms:
  2945	429:    "验收单",  # 同为信息隔离面, 且实测只有单层防御 (读侧 doc_type 不挡)
  2946	1215:        vectorizes with bge-m3, writes to LanceDB with source_type="image_ocr".
  2947	1273:            "source_type": "image_ocr",
  2948	1290:            "source_type": "image_ocr",
  2949	1771:                # RAG-P0 A1: doc_type — frontmatter.type wins; video_transcript
  2950	1772:                # path overrides only when frontmatter has no explicit type.
  2951	1773:                fm_doc_type = chunk.get("doc_type", "note") or "note"
  2952	1774:                if fm_doc_type == "note" and LanceDBClient._is_video_transcript(chunk["file_path"]):
  2953	1775:                    final_doc_type = "video_transcript"
  2954	1777:                    final_doc_type = fm_doc_type
  2955	1788:                        "video_transcript" if LanceDBClient._is_video_transcript(chunk["file_path"]) else "note"
  2956	1794:                    # RAG-P0 A1: doc_type for source-aware filter/rerank
  2957	1795:                    "doc_type": final_doc_type,
  2958	1798:                if LanceDBClient._is_video_transcript(chunk["file_path"]):
  2959	1817:                    # RAG-P0 A1: doc_type column for SQL where-clause filtering
  2960	1818:                    "doc_type": final_doc_type,

**Re-running isolation scope comparison**
exec
/bin/zsh -lc 'git diff --name-status 37387a86..HEAD -- backend/app/config.py backend/app/services/react_agent.py backend/app/services/tool_executor.py backend/lib/agentic_rag/agent_graph.py backend/lib/agentic_rag/retrievers/vault_notes_retriever.py backend/app/services/supplementary_search_service.py; git diff -U0 37387a86..HEAD -- backend/app/services/supplementary_search_service.py | rg -n "''^[+-].*(exclude_doc_types|ENABLE_LANCEDB_TIER2_FALLBACK|vault_notes|WHERE|doc_type)" || true; rg -n "exclude_doc_types|ENABLE_LANCEDB_TIER2_FALLBACK|NOT IN" backend/app/config.py backend/app/services/react_agent.py backend/app/services/tool_executor.py backend/lib/agentic_rag/agent_graph.py backend/lib/agentic_rag/retrievers/vault_notes_retriever.py backend/app/services/supplementary_search_service.py backend/lib/agentic_rag/clients/lancedb_client.py' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
M	backend/app/services/supplementary_search_service.py
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
6:-        # doc_type=按类型加权与断言用 / fts_confirmed=双通道确认)
8:+        # 修订): doc_type 不参与加权 — 加权按材料 source_type 走
10:+        # 生产消费 = MCP note_search_tools 将 clean 材料的 doc_type 透传进
backend/app/services/supplementary_search_service.py:69:# single-vault legacy can opt-in with ``ENABLE_LANCEDB_TIER2_FALLBACK=true``.
backend/app/services/supplementary_search_service.py:73:    """Return True only if ENABLE_LANCEDB_TIER2_FALLBACK env var is truthy.
backend/app/services/supplementary_search_service.py:77:    can opt-in with ``ENABLE_LANCEDB_TIER2_FALLBACK=true``.
backend/app/services/supplementary_search_service.py:79:    val = os.environ.get("ENABLE_LANCEDB_TIER2_FALLBACK", "false").strip().lower()
backend/app/services/supplementary_search_service.py:834:            exclude_doc_types=["whiteboard", "exam_board"],
backend/app/services/supplementary_search_service.py:849:                exclude_doc_types=["whiteboard", "exam_board"],
backend/app/services/supplementary_search_service.py:866:    # legacy can opt-in with ENABLE_LANCEDB_TIER2_FALLBACK=true.
backend/app/services/supplementary_search_service.py:881:            "(ENABLE_LANCEDB_TIER2_FALLBACK=true); cross-vault leak risk if residual "
backend/lib/agentic_rag/retrievers/vault_notes_retriever.py:66:        default_exclude_doc_types: RAG-P0 A3 (2026-05-10) — default exclude
backend/lib/agentic_rag/retrievers/vault_notes_retriever.py:69:            queries. Pass exclude_doc_types=[] at call site to opt in.
backend/lib/agentic_rag/retrievers/vault_notes_retriever.py:82:    default_exclude_doc_types: List[str] = field(default_factory=lambda: ["whiteboard", "exam_board"])
backend/lib/agentic_rag/retrievers/vault_notes_retriever.py:101:        exclude_doc_types: Optional[List[str]] = None,
backend/lib/agentic_rag/retrievers/vault_notes_retriever.py:144:        exclude_doc_types: Optional[List[str]] = None,
backend/lib/agentic_rag/retrievers/vault_notes_retriever.py:179:            # RAG-P0 A3: caller's exclude_doc_types wins; fall back to
backend/lib/agentic_rag/retrievers/vault_notes_retriever.py:181:            # Pass exclude_doc_types=[] explicitly to opt OUT of filtering.
backend/lib/agentic_rag/retrievers/vault_notes_retriever.py:183:                exclude_doc_types if exclude_doc_types is not None else list(self.config.default_exclude_doc_types)
backend/lib/agentic_rag/retrievers/vault_notes_retriever.py:192:                    exclude_doc_types=effective_exclude,
backend/app/services/tool_executor.py:112:                exclude_doc_types=["whiteboard", "exam_board"],
backend/app/services/tool_executor.py:122:                    exclude_doc_types=["whiteboard", "exam_board"],
backend/lib/agentic_rag/agent_graph.py:208:                    exclude_doc_types=["whiteboard", "exam_board"],
backend/app/config.py:48:#:   - 检验白板: 双层 —— 目录黑名单 + 读侧 exclude_doc_types=["whiteboard","exam_board"]
backend/app/services/react_agent.py:115:            exclude_doc_types=["whiteboard", "exam_board"],
backend/app/services/react_agent.py:124:                exclude_doc_types=["whiteboard", "exam_board"],
backend/lib/agentic_rag/clients/lancedb_client.py:2754:                # MCP 链现有的 doc_type NOT IN (...) 排除自动生效; 文件仍在索引,
backend/lib/agentic_rag/clients/lancedb_client.py:2981:        exclude_doc_types: Optional[List[str]] = None,
backend/lib/agentic_rag/clients/lancedb_client.py:3038:                    exclude_doc_types=exclude_doc_types,
backend/lib/agentic_rag/clients/lancedb_client.py:3104:        exclude_doc_types: Optional[List[str]] = None,
backend/lib/agentic_rag/clients/lancedb_client.py:3117:        - exclude_doc_types param → 'doc_type' column NOT IN (exclude mode)
backend/lib/agentic_rag/clients/lancedb_client.py:3139:        if exclude_doc_types:
backend/lib/agentic_rag/clients/lancedb_client.py:3140:            quoted = ", ".join(f"'{self._escape_sql(t)}'" for t in exclude_doc_types)
backend/lib/agentic_rag/clients/lancedb_client.py:3141:            clauses.append(f"(doc_type NOT IN ({quoted}) OR doc_type IS NULL)")
backend/lib/agentic_rag/clients/lancedb_client.py:3163:        exclude_doc_types: Optional[List[str]] = None,
backend/lib/agentic_rag/clients/lancedb_client.py:3191:            exclude_doc_types=exclude_doc_types,

**Assessing isolation surface for diffs**
**Planning diff analysis for whiteboard files**
exec
/bin/zsh -lc "echo baseline_py_literal_paths; git grep -l -E '[\"'\"'](whiteboard|exam_board)[\"'\"']' 37387a86 -- 'backend/*.py' | sort; echo head_py_literal_paths; git grep -l -E '[\"'\"'](whiteboard|exam_board)[\"'\"']' HEAD -- 'backend/*.py' | sort; echo changed_union_paths; git diff --name-status 37387a86..HEAD -- "'$( { git grep -l -E '"'[\"'\"'](whiteboard|exam_board)[\"'\"']' 37387a86 -- 'backend/*.py'; git grep -l -E '[\"'\"'](whiteboard|exam_board)[\"'\"']' HEAD -- 'backend/*.py'; } | sed 's/"'^[''^:]*://'"' | sort -u )" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 exited 1 in 0ms:
zsh:1: unmatched "
zsh:1: unmatched "

**Refining git grep command and output parsing**
exec
/bin/zsh -lc "echo baseline_py_paths; git grep -l -E 'whiteboard|exam_board' 37387a86 -- 'backend/*.py' | sort; echo head_py_paths; git grep -l -E 'whiteboard|exam_board' HEAD -- 'backend/*.py' | sort" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
baseline_py_paths
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
37387a86:backend/app/api/v1/endpoints/tips.py
37387a86:backend/app/config.py
37387a86:backend/app/mcp/server.py
37387a86:backend/app/models/board_manifest.py
37387a86:backend/app/models/exam_models.py
37387a86:backend/app/models/snapshot_v3.py
37387a86:backend/app/services/board_manifest_service.py
37387a86:backend/app/services/exam_service_ext.py
37387a86:backend/app/services/react_agent.py
37387a86:backend/app/services/supplementary_search_service.py
37387a86:backend/app/services/tool_executor.py
37387a86:backend/app/services/vault_init_service.py
37387a86:backend/lib/agentic_rag/agent_graph.py
37387a86:backend/lib/agentic_rag/clients/lancedb_client.py
37387a86:backend/lib/agentic_rag/retrievers/vault_notes_retriever.py
37387a86:backend/scripts/check_skill_routing_block.py
37387a86:backend/scripts/run_board_manifest_regression.py
37387a86:backend/scripts/run_vault_retrieval_regression.py
37387a86:backend/tests/regression/test_board_manifest_contracts.py
37387a86:backend/tests/regression/test_immutable_skip_dirs_contract.py
37387a86:backend/tests/regression/test_rag_stage2_chain_unify_contracts.py
37387a86:backend/tests/regression/test_rag_stage2_chunk_contracts.py
37387a86:backend/tests/regression/test_rag_stage2_t6_verification_contracts.py
37387a86:backend/tests/regression/test_snapshot_v3_contract.py
37387a86:backend/tests/regression/test_sync_board_concepts.py
37387a86:backend/tests/skills/test_split_preview.py
37387a86:backend/tests/unit/test_rag_p0_doc_type_filter.py
37387a86:backend/tests/unit/test_supplementary_search_service.py
37387a86:backend/tests/unit/test_vault_init_service.py
37387a86:backend/tests/unit/test_vault_templates.py
head_py_paths
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
HEAD:backend/app/api/v1/endpoints/tips.py
HEAD:backend/app/config.py
HEAD:backend/app/mcp/server.py
HEAD:backend/app/models/board_manifest.py
HEAD:backend/app/models/exam_models.py
HEAD:backend/app/models/snapshot_v3.py
HEAD:backend/app/services/board_manifest_service.py
HEAD:backend/app/services/exam_service_ext.py
HEAD:backend/app/services/react_agent.py
HEAD:backend/app/services/supplementary_search_service.py
HEAD:backend/app/services/tool_executor.py
HEAD:backend/app/services/vault_init_service.py
HEAD:backend/lib/agentic_rag/agent_graph.py
HEAD:backend/lib/agentic_rag/clients/lancedb_client.py
HEAD:backend/lib/agentic_rag/retrievers/vault_notes_retriever.py
HEAD:backend/scripts/check_skill_routing_block.py
HEAD:backend/scripts/run_board_manifest_regression.py
HEAD:backend/scripts/run_vault_retrieval_regression.py
HEAD:backend/tests/regression/test_board_manifest_contracts.py
HEAD:backend/tests/regression/test_immutable_skip_dirs_contract.py
HEAD:backend/tests/regression/test_rag_stage2_chain_unify_contracts.py
HEAD:backend/tests/regression/test_rag_stage2_chunk_contracts.py
HEAD:backend/tests/regression/test_rag_stage2_t6_verification_contracts.py
HEAD:backend/tests/regression/test_snapshot_v3_contract.py
HEAD:backend/tests/regression/test_sync_board_concepts.py
HEAD:backend/tests/skills/test_split_preview.py
HEAD:backend/tests/unit/test_rag_p0_doc_type_filter.py
HEAD:backend/tests/unit/test_supplementary_search_service.py
HEAD:backend/tests/unit/test_vault_init_service.py
HEAD:backend/tests/unit/test_vault_templates.py

**Planning git diff with grep-filtered paths**
exec
/bin/zsh -lc 'git diff --name-status 37387a86..HEAD -- $(git grep -l -E '"'whiteboard|exam_board' 37387a86 -- 'backend/*.py' | sed 's/"'^[''^:]*://'"')" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
M	backend/app/services/supplementary_search_service.py

**Confirming zero behavior changes in isolation code**
**Planning safe read-only command validation**
exec
/bin/zsh -lc 'i=0; while IFS= read -r cmd; do i=$((i+1)); zsh -n -c "$cmd"; rc=$?; print -r -- "command_$i zsh_n_exit=$rc"; done < <(sed -n '"'15p;18p;21p;24p' _bmad-output/审查/G4-16-evidence/test-run-metadata.txt)" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
command_1 zsh_n_exit=0
command_2 zsh_n_exit=0
command_3 zsh_n_exit=0
command_4 zsh_n_exit=0

**Identifying critical test binding issue**
**Analyzing partial file checkout risks**
**Inspecting commit changes for test stability**
**Investigating commit/tree binding issue**
**Assessing test environment reproducibility criteria**
**Verifying git checkout effects on index**
**Identifying shell command execution bug**
**Verifying git checkout effects and commit binding**
exec
/bin/zsh -lc 'for c in 73102875 fce0d8a2 94b420ff HEAD; do echo "$c $(git rev-parse "$c''^{commit}")"; for p in backend/app/services/supplementary_reranker.py backend/app/services/supplementary_search_service.py; do git rev-parse "$c:$p"; done; done; git diff --quiet 73102875..fce0d8a2 -- backend/app/services/supplementary_reranker.py backend/app/services/supplementary_search_service.py; echo diff_731_fce_two_files_exit=$?; git diff --quiet 73102875..94b420ff -- backend/app/services/supplementary_reranker.py backend/app/services/supplementary_search_service.py; echo diff_731_94b_two_files_exit=$?; git diff --quiet 73102875..HEAD -- backend/app/services/supplementary_reranker.py backend/app/services/supplementary_search_service.py; echo diff_731_head_two_files_exit=$?' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 18ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
diff_731_94b_two_files_exit=0
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
diff_731_head_two_files_exit=0

**Evaluating metadata discrepancy impact**
**Planning detailed report value audit**
exec
/bin/zsh -lc "git grep -n 'doc_type' 37387a86 -- 'backend/*.py' | diff -u - _bmad-output/审查/G4-16-evidence/doc_type-146-occurrences@37387a86.txt; echo pinned_evidence_diff_exit="'$?; git grep -n '"'doc_type' 37387a86 -- 'backend/*.py' | wc -l; git grep -l 'doc_type' 37387a86 -- 'backend/*.py' | wc -l; git grep -n 'doc_type' 37387a86 -- 'backend/*.py' | sed -E 's/"'^[''^:]+:([''^:]+):.*/'"\\1/' | sort | uniq -c | sort -k2" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
diff: -: Operation not permitted
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
pinned_evidence_diff_exit=2
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
     146
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
      18
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
   1 backend/app/api/v1/endpoints/metadata.py
   2 backend/app/config.py
   2 backend/app/mcp/tools/note_search_tools.py
   2 backend/app/services/react_agent.py
   1 backend/app/services/supplementary_reranker.py
   5 backend/app/services/supplementary_search_service.py
   3 backend/app/services/tool_executor.py
   1 backend/lib/agentic_rag/agent_graph.py
  69 backend/lib/agentic_rag/clients/lancedb_client.py
  13 backend/lib/agentic_rag/retrievers/vault_notes_retriever.py
   3 backend/scripts/run_vault_retrieval_regression.py
   2 backend/tests/regression/test_immutable_skip_dirs_contract.py
   1 backend/tests/regression/test_rag_stage0_contracts.py
   9 backend/tests/regression/test_rag_stage2_chain_unify_contracts.py
   7 backend/tests/regression/test_rag_stage2_chunk_contracts.py
   1 backend/tests/regression/test_rag_stage2_rerank_contracts.py
   4 backend/tests/regression/test_rag_stage2_t6_verification_contracts.py
  20 backend/tests/unit/test_rag_p0_doc_type_filter.py

**Assessing sandbox impact on diff stdin**
exec
/bin/zsh -lc "git grep -n 'doc_type' 37387a86 -- 'backend/*.py' | shasum -a 256; shasum -a 256 _bmad-output/审查/G4-16-evidence/doc_type-146-occurrences@37387a86.txt; git grep -n 'doc_type' 37387a86 -- 'backend/*.py' | wc -c; wc -c _bmad-output/审查/G4-16-evidence/doc_type-146-occurrences@37387a86.txt" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
94b01dc363643020c5bb2f476767eaad88d5b3fb0a32985f5fc2466f5c32c1cd  -
94b01dc363643020c5bb2f476767eaad88d5b3fb0a32985f5fc2466f5c32c1cd  _bmad-output/审查/G4-16-evidence/doc_type-146-occurrences@37387a86.txt
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
   19403
   19403 _bmad-output/审查/G4-16-evidence/doc_type-146-occurrences@37387a86.txt

**Listing relevant code inspection lines**
**Capturing baseline code snapshots**
exec
/bin/zsh -lc "for spec in 'backend/lib/agentic_rag/clients/lancedb_client.py:1260,1305' 'backend/lib/agentic_rag/clients/lancedb_client.py:1760,1830' 'backend/lib/agentic_rag/clients/lancedb_client.py:2045,2110' 'backend/lib/agentic_rag/clients/lancedb_client.py:2725,2785' 'backend/lib/agentic_rag/clients/lancedb_client.py:2965,3205' 'backend/lib/agentic_rag/clients/lancedb_client.py:3595,3655'; do p="'${spec%%:*}; range=${spec#*:}; a=${range%,*}; b=${range#*,}; echo "$p lines $a-$b @37387a86"; git show 37387a86:"$p" | nl -ba | sed -n "${a},${b}p"; done' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
backend/lib/agentic_rag/clients/lancedb_client.py lines 1260-1305 @37387a86
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
  1260	        try:
  1261	            vec_result = await self._vectorizer.vectorize_text(combined_text)
  1262	        except Exception as e:
  1263	            if LOGURU_ENABLED:
  1264	                logger.error(f"[IMAGE-INDEX] Vectorization failed for node {node_id}: {e}")
  1265	            return 0
  1266	
  1267	        # Build document
  1268	        content_type = ocr_result.get("content_type", "text")
  1269	        chunk_id = hashlib.md5(f"image_ocr:{node_id}:{combined_text[:100]}".encode()).hexdigest()
  1270	        metadata = {
  1271	            "file_path": image_path,
  1272	            "source": "image_ocr",
  1273	            "source_type": "image_ocr",
  1274	            "node_id": node_id,
  1275	            "content_type": content_type,
  1276	            "subject": subject,
  1277	        }
  1278	
  1279	        doc = {
  1280	            "doc_id": f"img_{chunk_id}",
  1281	            "content": combined_text,
  1282	            "vector": vec_result.vector,
  1283	            "canvas_file": image_path,
  1284	            "node_id": node_id,
  1285	            "node_type": "image_ocr",
  1286	            "color": "",
  1287	            "x": 0,
  1288	            "y": 0,
  1289	            "subject": subject,
  1290	            "source_type": "image_ocr",
  1291	            "timestamp": datetime.now().isoformat(),
  1292	            "metadata_json": json.dumps(metadata, ensure_ascii=False),
  1293	        }
  1294	
  1295	        # Delete old image OCR data for this node
  1296	        if self._db is not None:
  1297	            try:
  1298	                # T3 根治 (2026-07-10): 每次 open_table, 不读缓存句柄
  1299	                try:
  1300	                    tbl = self._db.open_table(table_name)
  1301	                    self._tables_cache[table_name] = tbl
  1302	                except Exception:
  1303	                    tbl = None
  1304	
  1305	                if tbl is not None:
backend/lib/agentic_rag/clients/lancedb_client.py lines 1760-1830 @37387a86
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
  1760	                    if LOGURU_ENABLED:
  1761	                        logger.error(f"Vectorization failed for {rel_path}: {e}")
  1762	                    continue
  1763	
  1764	            # Build documents
  1765	            documents = []
  1766	            for chunk, vec_result in zip(chunks, vectorized):
  1767	                chunk_id = hashlib.md5(
  1768	                    f"{chunk['file_path']}:{chunk.get('heading', '')}:{chunk['content'][:100]}".encode()
  1769	                ).hexdigest()
  1770	
  1771	                # RAG-P0 A1: doc_type — frontmatter.type wins; video_transcript
  1772	                # path overrides only when frontmatter has no explicit type.
  1773	                fm_doc_type = chunk.get("doc_type", "note") or "note"
  1774	                if fm_doc_type == "note" and LanceDBClient._is_video_transcript(chunk["file_path"]):
  1775	                    final_doc_type = "video_transcript"
  1776	                else:
  1777	                    final_doc_type = fm_doc_type
  1778	
  1779	                metadata = {
  1780	                    "file_path": chunk["file_path"],
  1781	                    "heading": chunk.get("heading", ""),
  1782	                    "heading_path": chunk.get("heading_path", []),
  1783	                    "line_start": chunk.get("line_start"),
  1784	                    "line_end": chunk.get("line_end"),
  1785	                    "source": "vault_note",
  1786	                    "subject": subject,
  1787	                    "source_type": (
  1788	                        "video_transcript" if LanceDBClient._is_video_transcript(chunk["file_path"]) else "note"
  1789	                    ),
  1790	                    # Story 2.8: Frontmatter metadata
  1791	                    "course": chunk.get("course", ""),
  1792	                    "tags_str": chunk.get("tags_str", ""),
  1793	                    "category": chunk.get("category", ""),
  1794	                    # RAG-P0 A1: doc_type for source-aware filter/rerank
  1795	                    "doc_type": final_doc_type,
  1796	                }
  1797	
  1798	                if LanceDBClient._is_video_transcript(chunk["file_path"]):
  1799	                    ts_info = LanceDBClient._extract_timestamps_from_section(chunk.get("heading", ""), chunk["content"])
  1800	                    metadata.update(ts_info)
  1801	
  1802	                doc = {
  1803	                    "doc_id": f"vault_{chunk_id}",
  1804	                    "content": chunk["content"],
  1805	                    "vector": vec_result.vector,
  1806	                    "canvas_file": chunk["file_path"],
  1807	                    "node_id": "",
  1808	                    "node_type": "vault_note",
  1809	                    "color": "",
  1810	                    "x": 0,
  1811	                    "y": 0,
  1812	                    "subject": subject or "",
  1813	                    # Story 2.8: Frontmatter columns
  1814	                    "course": chunk.get("course", ""),
  1815	                    "tags_str": chunk.get("tags_str", ""),
  1816	                    "category": chunk.get("category", ""),
  1817	                    # RAG-P0 A1: doc_type column for SQL where-clause filtering
  1818	                    "doc_type": final_doc_type,
  1819	                    "timestamp": datetime.now().isoformat(),
  1820	                    "metadata_json": json.dumps(metadata, ensure_ascii=False),
  1821	                }
  1822	                documents.append(doc)
  1823	
  1824	            # Story 2.7 AC-2: delete-before-insert
  1825	            self._delete_file_chunks(table_name, rel_path)
  1826	
  1827	            # Insert new chunks
  1828	            chunk_count = await self.add_documents(table_name, documents)
  1829	            total_chunks_indexed += chunk_count
  1830	
backend/lib/agentic_rag/clients/lancedb_client.py lines 2045-2110 @37387a86
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
  2045	            )
  2046	
  2047	        # Build documents
  2048	        documents = []
  2049	        for chunk, vec_result in zip(chunks, vectorized):
  2050	            if not vec_result.vector:
  2051	                continue
  2052	
  2053	            chunk_id = hashlib.md5(
  2054	                f"{chunk['file_path']}:{chunk.get('heading', '')}:{chunk['content'][:100]}".encode()
  2055	            ).hexdigest()
  2056	
  2057	            # RAG-P0 A1: doc_type — frontmatter.type wins over path heuristic
  2058	            fm_doc_type_2 = chunk.get("doc_type", "note") or "note"
  2059	            if fm_doc_type_2 == "note" and LanceDBClient._is_video_transcript(file_path):
  2060	                final_doc_type_2 = "video_transcript"
  2061	            else:
  2062	                final_doc_type_2 = fm_doc_type_2
  2063	
  2064	            metadata = {
  2065	                "file_path": chunk.get("file_path", rel_path),
  2066	                "heading": chunk.get("heading", ""),
  2067	                "heading_path": chunk.get("heading_path", []),
  2068	                "line_start": chunk.get("line_start", 0),
  2069	                "line_end": chunk.get("line_end", 0),
  2070	                "source": "vault_note",
  2071	                "subject": subject,
  2072	                "source_type": ("video_transcript" if LanceDBClient._is_video_transcript(file_path) else "note"),
  2073	                # Story 2.8: Frontmatter metadata
  2074	                "course": chunk.get("course", ""),
  2075	                "tags_str": chunk.get("tags_str", ""),
  2076	                "category": chunk.get("category", ""),
  2077	                # RAG-P0 A1: doc_type for source-aware filter/rerank
  2078	                "doc_type": final_doc_type_2,
  2079	            }
  2080	
  2081	            if LanceDBClient._is_video_transcript(file_path):
  2082	                ts_info = LanceDBClient._extract_timestamps_from_section(chunk.get("heading", ""), chunk["content"])
  2083	                metadata.update(ts_info)
  2084	
  2085	            doc = {
  2086	                "doc_id": f"vault_{chunk_id}",
  2087	                "content": chunk["content"],
  2088	                "vector": vec_result.vector,
  2089	                "canvas_file": chunk.get("file_path", rel_path),
  2090	                "node_id": "",
  2091	                "node_type": "vault_note",
  2092	                "color": "",
  2093	                "x": 0,
  2094	                "y": 0,
  2095	                "subject": subject or "",
  2096	                # Story 2.8: Frontmatter columns
  2097	                "course": chunk.get("course", ""),
  2098	                "tags_str": chunk.get("tags_str", ""),
  2099	                "category": chunk.get("category", ""),
  2100	                # RAG-P0 A1: doc_type column for SQL where-clause filtering
  2101	                "doc_type": final_doc_type_2,
  2102	                "timestamp": datetime.now().isoformat(),
  2103	                "metadata_json": json.dumps(metadata, ensure_ascii=False),
  2104	            }
  2105	            documents.append(doc)
  2106	
  2107	        # Story 2.7 AC-2: delete-before-insert
  2108	        self._delete_file_chunks(table_name, rel_path)
  2109	
  2110	        count = await self.add_documents(table_name, documents)
backend/lib/agentic_rag/clients/lancedb_client.py lines 2725-2785 @37387a86
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
  2725	        # Story 2.8: Parse frontmatter before chunking
  2726	        frontmatter, body = LanceDBClient._parse_frontmatter(content)
  2727	        # RAG-S2 T3 Step5 (bug②, 2026-08-09): line_start/line_end 旧值基于
  2728	        # frontmatter 剥离后的 body 计数, 引用行锚定整体偏移 (实测偏一个
  2729	        # frontmatter 的行数)。body 是 content 的后缀, 换行数差 = 被剥离的行数。
  2730	        fm_line_offset = content.count("\n") - body.count("\n")
  2731	        fm_course = str(frontmatter.get("course", ""))
  2732	        fm_tags_raw = frontmatter.get("tags", [])
  2733	        if isinstance(fm_tags_raw, list):
  2734	            fm_tags_str = ",".join(str(t) for t in fm_tags_raw)
  2735	        else:
  2736	            fm_tags_str = str(fm_tags_raw)
  2737	        fm_category = str(frontmatter.get("category", ""))
  2738	        # RAG-P0 A1 (2026-05-10): doc_type from frontmatter.type, default 'note'.
  2739	        # Drives source-aware filter/rerank — see _build_where_filters.
  2740	        fm_doc_type = str(frontmatter.get("type", "") or "").lower().strip()
  2741	        if not fm_doc_type:
  2742	            has_exam_key = "exam_question_id" in frontmatter
  2743	            if not frontmatter and content.startswith("---"):
  2744	                # Code-Review HIGH-1 (2026-08-09): YAML 解析失败时 fm={} —
  2745	                # 生产者 exam-quick.ts 写裸标量, 概念名含 YAML 指示符即炸
  2746	                # safe_load, 题面泄漏在该路径复活。对原文头部嗅探键名兜底
  2747	                # (误判方向保守: 最坏是普通笔记被检索链排除, 信息隔离不破)。
  2748	                has_exam_key = bool(re.search(r"(?m)^exam_question_id\s*:", content[:2000]))
  2749	            if has_exam_key:
  2750	                # RAG-S2 T3 Step1 (2026-08-09): 检验白板考察文件 (节点/考察-*.md)
  2751	                # 的 frontmatter 只有 exam_question_id/source_concept/exam_status,
  2752	                # 没有 type: 字段 → 旧 fallback "note" 让完整题面以最高权重入索引
  2753	                # = 信息隔离旁路 (Karpicke d=1.50)。推断 exam_board 后, hook 链与
  2754	                # MCP 链现有的 doc_type NOT IN (...) 排除自动生效; 文件仍在索引,
  2755	                # 未来出题链可定向取。显式 type: 仍最优先。
  2756	                fm_doc_type = "exam_board"
  2757	            else:
  2758	                fm_doc_type = "note"
  2759	
  2760	        # RAG-P0 A4 (2026-05-10): whiteboard differential chunking.
  2761	        # Strip dataviewjs/HTML comments/callouts/Recent Activity before
  2762	        # heading split — these chunks otherwise rank highly via bge-m3 because
  2763	        # they contain learning-domain keywords (节点/wikilink/Concepts) but
  2764	        # no real semantic value. After A3 default exclude, whiteboard chunks
  2765	        # don't surface in search anyway, but stripping here also saves
  2766	        # LanceDB storage and force_rebuild time.
  2767	        if fm_doc_type == "whiteboard":
  2768	            body = LanceDBClient._strip_whiteboard_boilerplate(body)
  2769	            # If nothing remains beyond the H1 title, skip the file entirely
  2770	            # (heading-only chunks have no embedding value).
  2771	            body_after_h1 = re.sub(r"\A\s*#\s+[^\n]+\n*", "", body, count=1).strip()
  2772	            if not body_after_h1:
  2773	                return []
  2774	
  2775	        heading_pattern = re.compile(r"^(#{1,4})\s+(.+)$")
  2776	        chunks = []
  2777	        # Use body (frontmatter stripped) for chunking
  2778	        lines = body.split("\n")
  2779	
  2780	        # Extract filename without extension for breadcrumb root
  2781	        filename = file_path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
  2782	        if filename.endswith(".md"):
  2783	            filename = filename[:-3]
  2784	
  2785	        # Heading stack: list of (level, title) for breadcrumb tracking
backend/lib/agentic_rag/clients/lancedb_client.py lines 2965-3205 @37387a86
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
  2965	                logger.error(f"Failed to read canvas file {canvas_path}: {e}")
  2966	            return []
  2967	
  2968	    async def search(
  2969	        self,
  2970	        query: str,
  2971	        table_name: str = "canvas_nodes",
  2972	        canvas_file: Optional[str] = None,
  2973	        subject: Optional[str] = None,
  2974	        num_results: int = 10,
  2975	        metric: str = "cosine",
  2976	        query_type: str = "hybrid",
  2977	        course_id: Optional[str] = None,
  2978	        tags: Optional[List[str]] = None,
  2979	        rrf_k: int = 60,
  2980	        doc_type: Optional[List[str]] = None,
  2981	        exclude_doc_types: Optional[List[str]] = None,
  2982	    ) -> List[Dict[str, Any]]:
  2983	        """
  2984	        向量搜索
  2985	
  2986	        ✅ Story 12.2 AC 2.2: 向量检索接口
  2987	        ✅ Story 12.2 AC 2.3: P95 < 400ms
  2988	        ✅ Story 12.2 AC 2.4: 结果转换
  2989	        ✅ Story 2.4: Hybrid 为默认模式 + 课程/标签过滤
  2990	
  2991	        Hybrid search strategy (Story 2.4):
  2992	        - Dense branch: bge-m3 1024d cosine similarity
  2993	        - FTS branch: Tantivy FTS on jieba-tokenized content (content_tokenized column)
  2994	        - Fusion: Reciprocal Rank Fusion (RRF, k=60)
  2995	        - Degradation: FTS unavailable → Dense-only; both fail → empty results
  2996	        - Note: FTS+jieba serves as sparse vector substitute (LanceDB has no native
  2997	          sparse vector column; Tantivy BM25 provides equivalent term-matching capability)
  2998	
  2999	        Args:
  3000	            query: 搜索查询 (文本或向量)
  3001	            table_name: 表名
  3002	            canvas_file: Canvas文件路径(用于过滤)
  3003	            subject: 学科标识(用于学科隔离过滤)
  3004	            num_results: 返回结果数量
  3005	            metric: 距离度量 ("cosine" 或 "L2")
  3006	            query_type: 搜索类型 ("vector" 或 "hybrid"). hybrid使用向量+FTS+RRF融合
  3007	            course_id: 课程ID (maps to 'course' column, 用于按课程过滤搜索范围)
  3008	            tags: 标签列表 (maps to 'tags_str' column, 用于按标签过滤, OR 匹配)
  3009	            rrf_k: RRF fusion k parameter (Story 2.11 configurable, default 60)
  3010	
  3011	        Returns:
  3012	            List[SearchResult]: 标准化的搜索结果
  3013	        """
  3014	        table_name = self.resolve_table_name(table_name)
  3015	        start_time = time.perf_counter()
  3016	
  3017	        if not self._initialized:
  3018	            await self.initialize()
  3019	
  3020	        try:
  3021	            # ✅ AC 2.3: 设置超时
  3022	            timeout_seconds = self.timeout_ms / 1000.0
  3023	
  3024	            # 执行搜索
  3025	            results = await asyncio.wait_for(
  3026	                self._search_internal(
  3027	                    query=query,
  3028	                    table_name=table_name,
  3029	                    canvas_file=canvas_file,
  3030	                    subject=subject,
  3031	                    num_results=num_results,
  3032	                    metric=metric,
  3033	                    query_type=query_type,
  3034	                    course_id=course_id,
  3035	                    tags=tags,
  3036	                    rrf_k=rrf_k,
  3037	                    doc_type=doc_type,
  3038	                    exclude_doc_types=exclude_doc_types,
  3039	                ),
  3040	                timeout=timeout_seconds,
  3041	            )
  3042	
  3043	            latency_ms = (time.perf_counter() - start_time) * 1000
  3044	
  3045	            if LOGURU_ENABLED:
  3046	                logger.debug(
  3047	                    f"LanceDBClient.search: "
  3048	                    f"query='{query[:50] if isinstance(query, str) else 'vector'}...', "
  3049	                    f"table={table_name}, "
  3050	                    f"results={len(results)}, "
  3051	                    f"latency={latency_ms:.2f}ms"
  3052	                )
  3053	
  3054	            # ✅ AC 2.3: 检查性能
  3055	            if latency_ms > 400:
  3056	                if LOGURU_ENABLED:
  3057	                    logger.warning(f"LanceDB search exceeded 400ms: {latency_ms:.2f}ms")
  3058	
  3059	            return results
  3060	
  3061	        except asyncio.TimeoutError:
  3062	            if LOGURU_ENABLED:
  3063	                logger.warning(f"LanceDBClient.search timeout ({self.timeout_ms}ms)")
  3064	
  3065	            if self.enable_fallback:
  3066	                return []
  3067	            else:
  3068	                raise
  3069	
  3070	        except Exception as e:
  3071	            if LOGURU_ENABLED:
  3072	                logger.error(f"LanceDBClient.search error: {e}")
  3073	
  3074	            if self.enable_fallback:
  3075	                return []
  3076	            else:
  3077	                raise
  3078	
  3079	    @staticmethod
  3080	    def _escape_sql(value: str) -> str:
  3081	        """Escape single quotes for SQL WHERE clauses to prevent injection."""
  3082	        return value.replace("'", "''")
  3083	
  3084	    @staticmethod
  3085	    def _escape_like(value: str) -> str:
  3086	        """
  3087	        Story 2-8 H4: Escape LIKE wildcards (% and _) in addition to single quotes.
  3088	
  3089	        When a value is used inside a LIKE pattern, literal '%' and '_' characters
  3090	        must be escaped to prevent unintended wildcard matching.
  3091	        """
  3092	        escaped = value.replace("'", "''")
  3093	        escaped = escaped.replace("%", "\\%")
  3094	        escaped = escaped.replace("_", "\\_")
  3095	        return escaped
  3096	
  3097	    def _build_where_filters(
  3098	        self,
  3099	        canvas_file: Optional[str] = None,
  3100	        subject: Optional[str] = None,
  3101	        course_id: Optional[str] = None,
  3102	        tags: Optional[List[str]] = None,
  3103	        doc_type: Optional[List[str]] = None,
  3104	        exclude_doc_types: Optional[List[str]] = None,
  3105	    ) -> List[str]:
  3106	        """
  3107	        Story 2.4 AC-5 + RAG-P0 A2: SQL WHERE filter clauses for LanceDB queries.
  3108	
  3109	        Supports canvas_file, subject, course_id (maps to 'course' column),
  3110	        tags (maps to 'tags_str' column, OR matching via LIKE), and source-aware
  3111	        doc_type include/exclude filtering (RAG-P0 A2, 2026-05-10).
  3112	
  3113	        Column mapping:
  3114	        - course_id param → 'course' column
  3115	        - tags param → 'tags_str' column (comma-separated tags from frontmatter)
  3116	        - doc_type param → 'doc_type' column IN (include mode)
  3117	        - exclude_doc_types param → 'doc_type' column NOT IN (exclude mode)
  3118	        """
  3119	        clauses: List[str] = []
  3120	        if canvas_file:
  3121	            clauses.append(f"canvas_file = '{self._escape_sql(canvas_file)}'")
  3122	        if subject:
  3123	            clauses.append(f"subject = '{self._escape_sql(subject)}'")
  3124	        if course_id:
  3125	            clauses.append(f"course = '{self._escape_sql(course_id)}'")
  3126	        if tags:
  3127	            # Story 2-8 H4: Use _escape_like for LIKE patterns to escape % and _
  3128	            tag_conditions = " OR ".join(f"tags_str LIKE '%{self._escape_like(tag)}%'" for tag in tags)
  3129	            clauses.append(f"({tag_conditions})")
  3130	        # RAG-P0 A2: doc_type include/exclude. Pre-A1 rows lack the column;
  3131	        # we use IS NULL fallback so legacy data degrades to "treat as note"
  3132	        # rather than disappearing from result sets.
  3133	        if doc_type:
  3134	            quoted = ", ".join(f"'{self._escape_sql(t)}'" for t in doc_type)
  3135	            if "note" in doc_type:
  3136	                clauses.append(f"(doc_type IN ({quoted}) OR doc_type IS NULL)")
  3137	            else:
  3138	                clauses.append(f"doc_type IN ({quoted})")
  3139	        if exclude_doc_types:
  3140	            quoted = ", ".join(f"'{self._escape_sql(t)}'" for t in exclude_doc_types)
  3141	            clauses.append(f"(doc_type NOT IN ({quoted}) OR doc_type IS NULL)")
  3142	        return clauses
  3143	
  3144	    def _apply_where_clauses(self, search_query, clauses: List[str]):
  3145	        """Apply a list of WHERE clauses to a LanceDB search query."""
  3146	        for clause in clauses:
  3147	            search_query = search_query.where(clause)
  3148	        return search_query
  3149	
  3150	    async def _search_internal(
  3151	        self,
  3152	        query: str,
  3153	        table_name: str,
  3154	        canvas_file: Optional[str],
  3155	        subject: Optional[str],
  3156	        num_results: int,
  3157	        metric: str,
  3158	        query_type: str = "hybrid",
  3159	        course_id: Optional[str] = None,
  3160	        tags: Optional[List[str]] = None,
  3161	        rrf_k: int = 60,
  3162	        doc_type: Optional[List[str]] = None,
  3163	        exclude_doc_types: Optional[List[str]] = None,
  3164	    ) -> List[Dict[str, Any]]:
  3165	        """内部搜索实现 (Story 2.4 + RAG-P0 A2: hybrid + course/tags + doc_type filter)"""
  3166	        if self._db is None:
  3167	            return []
  3168	
  3169	        # 获取表
  3170	        # T3 根治 (2026-07-10): 每次 open_table, 不读缓存句柄 — rebuild 后
  3171	        # 旧句柄指向已删 dataset, enrich 静默空 (原靠重启容器绕过)
  3172	        try:
  3173	            table = self._db.open_table(table_name)
  3174	            self._tables_cache[table_name] = table
  3175	        except Exception as e:
  3176	            if LOGURU_ENABLED:
  3177	                logger.debug(f"Table {table_name} not found: {e}")
  3178	            # RAG-S2 T6 审查修复 (2026-08-10): 表打不开是基础设施故障不是
  3179	            # 合法空 — raise 让 search() 外层 enable_fallback 门决定吞或抛
  3180	            # (enable_fallback=True 调用方在外层照旧吞成 [], 行为不变;
  3181	            # False 的调用方 [MCP fast/hook singleton] 得到诚实 error)。
  3182	            raise RuntimeError(f"open_table('{table_name}') failed: {e}") from e
  3183	
  3184	        # Story 2.4 AC-5 + RAG-P0 A2: Build pre-filter clauses
  3185	        where_clauses = self._build_where_filters(
  3186	            canvas_file=canvas_file,
  3187	            subject=subject,
  3188	            course_id=course_id,
  3189	            tags=tags,
  3190	            doc_type=doc_type,
  3191	            exclude_doc_types=exclude_doc_types,
  3192	        )
  3193	
  3194	        # RAG-P0 A5 v2 schema guard (2026-05-11) — drop clauses referencing
  3195	        # columns not present in this table's schema. Without this, LanceDB
  3196	        # raises LanceError(Schema): No field named X → entire branch fails
  3197	        # silently (try/except below returns []). Legacy tables (vault_notes,
  3198	        # canvas_vault_vault_notes pre-RAG-P0) lack the 'doc_type' column;
  3199	        # the IS NULL fallback in _build_where_filters does NOT help because
  3200	        # IS NULL still requires the column to exist in the schema.
  3201	        try:
  3202	            schema_columns = {f.name for f in table.schema}
  3203	            missing_in_schema = []
  3204	            for col in ("doc_type", "course", "tags_str"):
  3205	                if col not in schema_columns:
backend/lib/agentic_rag/clients/lancedb_client.py lines 3595-3655 @37387a86
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
  3595	            # 准备数据
  3596	            data = []
  3597	            for doc in documents:
  3598	                # canvas_file: check top-level first (index_vault_notes),
  3599	                # then metadata dict (legacy callers)
  3600	                canvas_file = doc.get("canvas_file") or doc.get("metadata", {}).get("canvas_file", "") or ""
  3601	
  3602	                content = doc.get("content", "")
  3603	                lance_doc = {
  3604	                    "doc_id": doc.get("doc_id"),
  3605	                    "content": content,
  3606	                    # Story 2.4: jieba 预分词后的内容，供 FTS 索引使用
  3607	                    "content_tokenized": _jieba_tokenize(content),
  3608	                    "vector": doc.get("vector") or doc.get("embedding"),
  3609	                    "canvas_file": canvas_file,
  3610	                    "timestamp": doc.get("timestamp") or datetime.now().isoformat(),
  3611	                }
  3612	
  3613	                # Passthrough extra fields (node_id, node_type, color, x, y, subject, etc.)
  3614	                # so that index_vault_notes / index_single_file schema is preserved
  3615	                for key in (
  3616	                    "node_id",
  3617	                    "node_type",
  3618	                    "color",
  3619	                    "x",
  3620	                    "y",
  3621	                    "subject",
  3622	                    "course_id",
  3623	                    "tags",
  3624	                    # Story 2.8: Frontmatter metadata columns
  3625	                    "course",
  3626	                    "tags_str",
  3627	                    "category",
  3628	                    # Story 2.9: Image OCR source type
  3629	                    "source_type",
  3630	                    # RAG-P0 A1: doc_type column
  3631	                    "doc_type",
  3632	                ):
  3633	                    if key in doc:
  3634	                        lance_doc[key] = doc[key]
  3635	
  3636	                # metadata_json: use top-level if present (index_vault_notes),
  3637	                # else serialize metadata dict
  3638	                if doc.get("metadata_json"):
  3639	                    lance_doc["metadata_json"] = doc["metadata_json"]
  3640	                elif "metadata" in doc:
  3641	                    import json
  3642	
  3643	                    lance_doc["metadata_json"] = json.dumps(doc["metadata"], ensure_ascii=False)
  3644	
  3645	                data.append(lance_doc)
  3646	
  3647	            # Story 2.3 Task 6: Check vector dimension mismatch before insert
  3648	            # T3 根治 (2026-07-10): 守卫改为 db 权威存在性 (缓存命中 ≠ 表存在)
  3649	            if data and table_name in self._db.table_names():
  3650	                sample_vector = data[0].get("vector")
  3651	                if sample_vector is not None:
  3652	                    self._check_and_fix_dimension_mismatch(table_name, len(sample_vector))
  3653	
  3654	            # 检查表是否存在
  3655	            # T3 根治 (2026-07-10): 存在性用 table_names() 权威判断, 不再以

**Verifying six-value categorization accuracy**
**Planning exhaustive doc_type value scan**
exec
/bin/zsh -lc 'nl -ba _bmad-output/审查/G4-16-evidence/doc_type-146-occurrences@37387a86.txt' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
     1	37387a86:backend/app/api/v1/endpoints/metadata.py:569:            Use after RAG-P0 schema changes (e.g. adding doc_type column) to
     2	37387a86:backend/app/config.py:48:#:   - 检验白板: 双层 —— 目录黑名单 + 读侧 exclude_doc_types=["whiteboard","exam_board"]
     3	37387a86:backend/app/config.py:50:#:   - 验收单 / _待处理 / _archive: **单层** —— frontmatter 无 doc_type,
     4	37387a86:backend/app/mcp/tools/note_search_tools.py:276:    # doc_type/source_type 来自 frontmatter 自由文本 (仅 lower/strip 无枚举
     5	37387a86:backend/app/mcp/tools/note_search_tools.py:291:            "doc_type",
     6	37387a86:backend/app/services/react_agent.py:115:            exclude_doc_types=["whiteboard", "exam_board"],
     7	37387a86:backend/app/services/react_agent.py:124:                exclude_doc_types=["whiteboard", "exam_board"],
     8	37387a86:backend/app/services/supplementary_reranker.py:56:    "concept": 1.0,  # 派生概念节点 (doc_type=concept) → 用户手写, 最高
     9	37387a86:backend/app/services/supplementary_search_service.py:834:            exclude_doc_types=["whiteboard", "exam_board"],
    10	37387a86:backend/app/services/supplementary_search_service.py:849:                exclude_doc_types=["whiteboard", "exam_board"],
    11	37387a86:backend/app/services/supplementary_search_service.py:975:    doc_type = metadata.get("doc_type", "") or raw.get("doc_type", "") or ""
    12	37387a86:backend/app/services/supplementary_search_service.py:1045:        # doc_type=按类型加权与断言用 / fts_confirmed=双通道确认)
    13	37387a86:backend/app/services/supplementary_search_service.py:1047:        "doc_type": doc_type,
    14	37387a86:backend/app/services/tool_executor.py:97:        RAG-P0 A3 (2026-05-10): default exclude doc_type='whiteboard' so that
    15	37387a86:backend/app/services/tool_executor.py:112:                exclude_doc_types=["whiteboard", "exam_board"],
    16	37387a86:backend/app/services/tool_executor.py:122:                    exclude_doc_types=["whiteboard", "exam_board"],
    17	37387a86:backend/lib/agentic_rag/agent_graph.py:208:                    exclude_doc_types=["whiteboard", "exam_board"],
    18	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:429:    "验收单",  # 同为信息隔离面, 且实测只有单层防御 (读侧 doc_type 不挡)
    19	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:1771:                # RAG-P0 A1: doc_type — frontmatter.type wins; video_transcript
    20	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:1773:                fm_doc_type = chunk.get("doc_type", "note") or "note"
    21	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:1774:                if fm_doc_type == "note" and LanceDBClient._is_video_transcript(chunk["file_path"]):
    22	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:1775:                    final_doc_type = "video_transcript"
    23	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:1777:                    final_doc_type = fm_doc_type
    24	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:1794:                    # RAG-P0 A1: doc_type for source-aware filter/rerank
    25	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:1795:                    "doc_type": final_doc_type,
    26	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:1817:                    # RAG-P0 A1: doc_type column for SQL where-clause filtering
    27	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:1818:                    "doc_type": final_doc_type,
    28	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:2057:            # RAG-P0 A1: doc_type — frontmatter.type wins over path heuristic
    29	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:2058:            fm_doc_type_2 = chunk.get("doc_type", "note") or "note"
    30	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:2059:            if fm_doc_type_2 == "note" and LanceDBClient._is_video_transcript(file_path):
    31	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:2060:                final_doc_type_2 = "video_transcript"
    32	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:2062:                final_doc_type_2 = fm_doc_type_2
    33	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:2077:                # RAG-P0 A1: doc_type for source-aware filter/rerank
    34	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:2078:                "doc_type": final_doc_type_2,
    35	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:2100:                # RAG-P0 A1: doc_type column for SQL where-clause filtering
    36	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:2101:                "doc_type": final_doc_type_2,
    37	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:2583:        RAG-S2 T3 Step3: Obsidian callout 三级分级器 — 对所有 doc_type 生效。
    38	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:2686:        # 携带 doc_type=whiteboard 仍被检索默认排除) — 此处不再无差别剥离。
    39	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:2711:        section 不产 chunk + 考察文件 doc_type 推断 exam_board + 行号补 frontmatter 偏移。
    40	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:2738:        # RAG-P0 A1 (2026-05-10): doc_type from frontmatter.type, default 'note'.
    41	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:2740:        fm_doc_type = str(frontmatter.get("type", "") or "").lower().strip()
    42	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:2741:        if not fm_doc_type:
    43	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:2754:                # MCP 链现有的 doc_type NOT IN (...) 排除自动生效; 文件仍在索引,
    44	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:2756:                fm_doc_type = "exam_board"
    45	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:2758:                fm_doc_type = "note"
    46	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:2767:        if fm_doc_type == "whiteboard":
    47	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:2835:                        # RAG-P0 A1: doc_type for source-aware filtering
    48	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:2836:                        "doc_type": fm_doc_type,
    49	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:2980:        doc_type: Optional[List[str]] = None,
    50	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:2981:        exclude_doc_types: Optional[List[str]] = None,
    51	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:3037:                    doc_type=doc_type,
    52	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:3038:                    exclude_doc_types=exclude_doc_types,
    53	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:3103:        doc_type: Optional[List[str]] = None,
    54	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:3104:        exclude_doc_types: Optional[List[str]] = None,
    55	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:3111:        doc_type include/exclude filtering (RAG-P0 A2, 2026-05-10).
    56	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:3116:        - doc_type param → 'doc_type' column IN (include mode)
    57	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:3117:        - exclude_doc_types param → 'doc_type' column NOT IN (exclude mode)
    58	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:3130:        # RAG-P0 A2: doc_type include/exclude. Pre-A1 rows lack the column;
    59	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:3133:        if doc_type:
    60	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:3134:            quoted = ", ".join(f"'{self._escape_sql(t)}'" for t in doc_type)
    61	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:3135:            if "note" in doc_type:
    62	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:3136:                clauses.append(f"(doc_type IN ({quoted}) OR doc_type IS NULL)")
    63	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:3138:                clauses.append(f"doc_type IN ({quoted})")
    64	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:3139:        if exclude_doc_types:
    65	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:3140:            quoted = ", ".join(f"'{self._escape_sql(t)}'" for t in exclude_doc_types)
    66	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:3141:            clauses.append(f"(doc_type NOT IN ({quoted}) OR doc_type IS NULL)")
    67	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:3162:        doc_type: Optional[List[str]] = None,
    68	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:3163:        exclude_doc_types: Optional[List[str]] = None,
    69	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:3165:        """内部搜索实现 (Story 2.4 + RAG-P0 A2: hybrid + course/tags + doc_type filter)"""
    70	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:3190:            doc_type=doc_type,
    71	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:3191:            exclude_doc_types=exclude_doc_types,
    72	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:3198:        # canvas_vault_vault_notes pre-RAG-P0) lack the 'doc_type' column;
    73	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:3204:            for col in ("doc_type", "course", "tags_str"):
    74	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:3471:                # RAG-P0 A1: doc_type for source-aware filter/rerank
    75	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:3472:                "doc_type",
    76	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:3516:          - missing 'doc_type' column (RAG-P0 A1 added this column;
    77	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:3544:            # RAG-P0 A5: detect missing doc_type column on pre-A1 tables.
    78	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:3546:            # tables with empty doc_type values still register as compliant.
    79	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:3547:            doc_type_missing = False
    80	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:3550:                doc_type_missing = "doc_type" not in col_names
    81	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:3554:                doc_type_missing = "doc_type" not in rows
    82	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:3556:            if not dim_mismatch and not doc_type_missing:
    83	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:3564:                if doc_type_missing:
    84	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:3565:                    reasons.append("missing 'doc_type' column (pre-RAG-P0)")
    85	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:3630:                    # RAG-P0 A1: doc_type column
    86	37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:3631:                    "doc_type",
    87	37387a86:backend/lib/agentic_rag/retrievers/vault_notes_retriever.py:66:        default_exclude_doc_types: RAG-P0 A3 (2026-05-10) — default exclude
    88	37387a86:backend/lib/agentic_rag/retrievers/vault_notes_retriever.py:69:            queries. Pass exclude_doc_types=[] at call site to opt in.
    89	37387a86:backend/lib/agentic_rag/retrievers/vault_notes_retriever.py:81:    # 查询侧排除表对齐; 未来出题链定向取材传显式 doc_type 即可 opt-in。
    90	37387a86:backend/lib/agentic_rag/retrievers/vault_notes_retriever.py:82:    default_exclude_doc_types: List[str] = field(default_factory=lambda: ["whiteboard", "exam_board"])
    91	37387a86:backend/lib/agentic_rag/retrievers/vault_notes_retriever.py:100:        doc_type: Optional[List[str]] = None,
    92	37387a86:backend/lib/agentic_rag/retrievers/vault_notes_retriever.py:101:        exclude_doc_types: Optional[List[str]] = None,
    93	37387a86:backend/lib/agentic_rag/retrievers/vault_notes_retriever.py:143:        doc_type: Optional[List[str]] = None,
    94	37387a86:backend/lib/agentic_rag/retrievers/vault_notes_retriever.py:144:        exclude_doc_types: Optional[List[str]] = None,
    95	37387a86:backend/lib/agentic_rag/retrievers/vault_notes_retriever.py:179:            # RAG-P0 A3: caller's exclude_doc_types wins; fall back to
    96	37387a86:backend/lib/agentic_rag/retrievers/vault_notes_retriever.py:181:            # Pass exclude_doc_types=[] explicitly to opt OUT of filtering.
    97	37387a86:backend/lib/agentic_rag/retrievers/vault_notes_retriever.py:183:                exclude_doc_types if exclude_doc_types is not None else list(self.config.default_exclude_doc_types)
    98	37387a86:backend/lib/agentic_rag/retrievers/vault_notes_retriever.py:191:                    doc_type=doc_type,
    99	37387a86:backend/lib/agentic_rag/retrievers/vault_notes_retriever.py:192:                    exclude_doc_types=effective_exclude,
   100	37387a86:backend/scripts/run_vault_retrieval_regression.py:134:    return str(m.get("doc_type", "")) in set(cfg_contam.get("doc_types", []))
   101	37387a86:backend/scripts/run_vault_retrieval_regression.py:143:    if str(m.get("doc_type", "")) in set(forb.get("doc_types", [])):
   102	37387a86:backend/scripts/run_vault_retrieval_regression.py:144:        out.append(f"doc_type {m.get('doc_type')!r} 属硬禁类型 (path={path!r})")
   103	37387a86:backend/tests/regression/test_immutable_skip_dirs_contract.py:14:  - 检验白板：双层 —— 目录黑名单 + 读侧 exclude_doc_types（靠 frontmatter
   104	37387a86:backend/tests/regression/test_immutable_skip_dirs_contract.py:16:  - 验收单 / _待处理 / _archive：**单层** —— frontmatter 无 doc_type，读侧不挡，
   105	37387a86:backend/tests/regression/test_rag_stage0_contracts.py:41:                "doc_type": "concept",
   106	37387a86:backend/tests/regression/test_rag_stage2_chain_unify_contracts.py:43:def _raw_row(path, raw_score, content="真实学习内容。" * 10, fts=False, doc_type="concept"):
   107	37387a86:backend/tests/regression/test_rag_stage2_chain_unify_contracts.py:44:    metadata = {"canvas_file": path, "doc_type": doc_type, "_rrf_score": 0.032}
   108	37387a86:backend/tests/regression/test_rag_stage2_chain_unify_contracts.py:163:    (旧 MCP 直查靠 where 子句, 现走 client.search exclude_doc_types)。"""
   109	37387a86:backend/tests/regression/test_rag_stage2_chain_unify_contracts.py:180:    assert "exam_board" in captured.get("exclude_doc_types", []), "HARD-ISO: MCP 链必须排除考题白板"
   110	37387a86:backend/tests/regression/test_rag_stage2_chain_unify_contracts.py:249:    且 metadata 只留数值/布尔信号 (doc_type 等自由文本被丢弃)。"""
   111	37387a86:backend/tests/regression/test_rag_stage2_chain_unify_contracts.py:265:    assert "doc_type" not in item["metadata"]
   112	37387a86:backend/tests/regression/test_rag_stage2_chain_unify_contracts.py:488:    """hybrid 异常回退 vector-only 时 exclude_doc_types 必须含 exam_board —
   113	37387a86:backend/tests/regression/test_rag_stage2_chain_unify_contracts.py:505:    assert "exam_board" in calls[1].get("exclude_doc_types", []), "回退分支漏排 exam_board = 隔离旁路回归"
   114	37387a86:backend/tests/regression/test_rag_stage2_chain_unify_contracts.py:506:    assert "whiteboard" in calls[1].get("exclude_doc_types", [])
   115	37387a86:backend/tests/regression/test_rag_stage2_chunk_contracts.py:3:# 组 A doc_type 推断: 考察文件 (exam_question_id, 无 type:) → exam_board;
   116	37387a86:backend/tests/regression/test_rag_stage2_chunk_contracts.py:39:# 组 A — doc_type 推断（T3 Step1 堵题面泄漏）
   117	37387a86:backend/tests/regression/test_rag_stage2_chunk_contracts.py:47:    doc_type NOT IN ('whiteboard','exam_board') 排除拦不住 = 信息隔离旁路。
   118	37387a86:backend/tests/regression/test_rag_stage2_chunk_contracts.py:59:    assert {c["doc_type"] for c in chunks} == {"exam_board"}
   119	37387a86:backend/tests/regression/test_rag_stage2_chunk_contracts.py:65:    assert {c["doc_type"] for c in chunks} == {"concept"}
   120	37387a86:backend/tests/regression/test_rag_stage2_chunk_contracts.py:71:    assert {c["doc_type"] for c in chunks} == {"note"}
   121	37387a86:backend/tests/regression/test_rag_stage2_chunk_contracts.py:290:    assert {c["doc_type"] for c in chunks} == {"exam_board"}, "YAML 失败路径不得回落 note"
   122	37387a86:backend/tests/regression/test_rag_stage2_rerank_contracts.py:297:        "metadata": {"canvas_file": path, "doc_type": "concept"},
   123	37387a86:backend/tests/regression/test_rag_stage2_t6_verification_contracts.py:39:    metadata = {"canvas_file": path, "doc_type": "concept", "_rrf_score": 0.032}
   124	37387a86:backend/tests/regression/test_rag_stage2_t6_verification_contracts.py:295:    excludes = VaultNotesRetrieverConfig().default_exclude_doc_types
   125	37387a86:backend/tests/regression/test_rag_stage2_t6_verification_contracts.py:318:        assert "exam_board" in kw.get("exclude_doc_types", []), "react agent 链不得成为题面泄漏通道"
   126	37387a86:backend/tests/regression/test_rag_stage2_t6_verification_contracts.py:339:        assert "exam_board" in kw.get("exclude_doc_types", [])
   127	37387a86:backend/tests/unit/test_rag_p0_doc_type_filter.py:2:RAG-P0 (2026-05-10) — A1+A2+A4 doc_type filtering & whiteboard boilerplate stripping.
   128	37387a86:backend/tests/unit/test_rag_p0_doc_type_filter.py:5:- A1: frontmatter.type → metadata.doc_type / doc.doc_type column (source-aware filter input)
   129	37387a86:backend/tests/unit/test_rag_p0_doc_type_filter.py:6:- A2: _build_where_filters supports doc_type IN / NOT IN with NULL fallback for legacy rows
   130	37387a86:backend/tests/unit/test_rag_p0_doc_type_filter.py:21:# A1 — doc_type extracted from frontmatter, defaults to 'note'
   131	37387a86:backend/tests/unit/test_rag_p0_doc_type_filter.py:25:def test_split_md_by_heading_extracts_doc_type_whiteboard():
   132	37387a86:backend/tests/unit/test_rag_p0_doc_type_filter.py:43:        assert c["doc_type"] == "whiteboard"
   133	37387a86:backend/tests/unit/test_rag_p0_doc_type_filter.py:46:def test_split_md_by_heading_extracts_doc_type_default_note():
   134	37387a86:backend/tests/unit/test_rag_p0_doc_type_filter.py:57:    assert all(c["doc_type"] == "note" for c in chunks)
   135	37387a86:backend/tests/unit/test_rag_p0_doc_type_filter.py:64:    assert all(c["doc_type"] == "note" for c in chunks)
   136	37387a86:backend/tests/unit/test_rag_p0_doc_type_filter.py:68:# A2 — _build_where_filters source-aware doc_type SQL generation
   137	37387a86:backend/tests/unit/test_rag_p0_doc_type_filter.py:78:    clauses = _client()._build_where_filters(exclude_doc_types=["whiteboard"])
   138	37387a86:backend/tests/unit/test_rag_p0_doc_type_filter.py:80:        "doc_type NOT IN ('whiteboard')" in c and "doc_type IS NULL" in c
   139	37387a86:backend/tests/unit/test_rag_p0_doc_type_filter.py:86:    clauses = _client()._build_where_filters(doc_type=["note"])
   140	37387a86:backend/tests/unit/test_rag_p0_doc_type_filter.py:88:        "doc_type IN ('note')" in c and "doc_type IS NULL" in c for c in clauses
   141	37387a86:backend/tests/unit/test_rag_p0_doc_type_filter.py:93:    clauses = _client()._build_where_filters(doc_type=["lecture", "discussion"])
   142	37387a86:backend/tests/unit/test_rag_p0_doc_type_filter.py:95:    assert "doc_type IN ('lecture', 'discussion')" in sql
   143	37387a86:backend/tests/unit/test_rag_p0_doc_type_filter.py:105:        exclude_doc_types=["whiteboard"],
   144	37387a86:backend/tests/unit/test_rag_p0_doc_type_filter.py:110:    assert "doc_type NOT IN" in sql
   145	37387a86:backend/tests/unit/test_rag_p0_doc_type_filter.py:113:def test_where_filters_no_doc_type_param_unchanged():
   146	37387a86:backend/tests/unit/test_rag_p0_doc_type_filter.py:116:    assert "doc_type" not in sql, "absent doc_type/exclude_doc_types → no clause"

**Verifying image_ocr table usage**
exec
/bin/zsh -lc "git show 37387a86:backend/lib/agentic_rag/clients/lancedb_client.py | nl -ba | sed -n '1160,1325p'; git show 37387a86:backend/lib/agentic_rag/clients/lancedb_client.py | nl -ba | sed -n '3400,3595p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
  1160	        # Drop main table
  1161	        try:
  1162	            self._db.drop_table(table_name, ignore_missing=True)
  1163	            self._tables_cache.pop(table_name, None)
  1164	        except Exception:
  1165	            pass
  1166	
  1167	        if LOGURU_ENABLED:
  1168	            logger.info(f"[REBUILD] Dropped tables '{table_name}' and '{fp_table}', starting full rebuild")
  1169	
  1170	        # Re-index all files via index_vault_notes with force_rebuild
  1171	        total_chunks = await self.index_vault_notes(
  1172	            vault_path=vault_path,
  1173	            table_name=table_name,
  1174	            max_tokens=max_tokens,
  1175	            overlap_tokens=overlap_tokens,
  1176	            subject=subject,
  1177	            force_rebuild=True,
  1178	            progress_callback=progress_callback,
  1179	        )
  1180	
  1181	        duration_ms = (time.perf_counter() - start_time) * 1000
  1182	
  1183	        # Count files
  1184	        skip_dirs = [".obsidian", ".git", ".trash", "node_modules"]
  1185	        total_files = 0
  1186	        for _root, dirs, files in os.walk(vault_path):
  1187	            dirs[:] = [d for d in dirs if d not in skip_dirs]
  1188	            total_files += sum(1 for f in files if f.endswith(".md"))
  1189	
  1190	        if LOGURU_ENABLED:
  1191	            logger.info(f"[REBUILD] Complete: {total_files} files, {total_chunks} chunks in {duration_ms:.0f}ms")
  1192	
  1193	        return {
  1194	            "total_files": total_files,
  1195	            "total_chunks": total_chunks,
  1196	            "duration_ms": round(duration_ms),
  1197	        }
  1198	
  1199	    # =========================================================================
  1200	    # Story 2.9: Image OCR Content Indexing
  1201	    # =========================================================================
  1202	
  1203	    async def index_image_content(
  1204	        self,
  1205	        node_id: str,
  1206	        image_path: str,
  1207	        ocr_result: Dict[str, Any],
  1208	        table_name: str = "vault_notes",
  1209	        subject: str = "",
  1210	    ) -> int:
  1211	        """
  1212	        Story 2.9 AC-2: Index OCR-extracted image content via the text indexing pipeline.
  1213	
  1214	        Combines OCR text + summary + concepts into indexable text,
  1215	        vectorizes with bge-m3, writes to LanceDB with source_type="image_ocr".
  1216	        Uses delete-before-insert by node_id.
  1217	
  1218	        Args:
  1219	            node_id: Canvas node ID of the image.
  1220	            image_path: Path to the original image file.
  1221	            ocr_result: Structured OCR result dict with keys:
  1222	                text, content_type, summary, concepts.
  1223	            table_name: Target LanceDB table.
  1224	            subject: Subject tag for isolation.
  1225	
  1226	        Returns:
  1227	            Number of chunks indexed.
  1228	        """
  1229	        table_name = self.resolve_table_name(table_name)
  1230	        import hashlib
  1231	
  1232	        if not self._initialized:
  1233	            await self.initialize()
  1234	
  1235	        await self._init_vectorizer()
  1236	        if self._vectorizer is None:
  1237	            if LOGURU_ENABLED:
  1238	                logger.warning("Vectorizer not available, skipping image content indexing")
  1239	            return 0
  1240	
  1241	        # Build indexable text from OCR result
  1242	        text_parts = []
  1243	        ocr_text = ocr_result.get("text", "")
  1244	        if ocr_text:
  1245	            text_parts.append(ocr_text)
  1246	        summary = ocr_result.get("summary", "")
  1247	        if summary:
  1248	            text_parts.append(f"[摘要] {summary}")
  1249	        concepts = ocr_result.get("concepts", [])
  1250	        if concepts:
  1251	            text_parts.append(f"[核心概念] {', '.join(concepts)}")
  1252	
  1253	        combined_text = "\n".join(text_parts)
  1254	        if not combined_text.strip():
  1255	            if LOGURU_ENABLED:
  1256	                logger.debug(f"[IMAGE-INDEX] No text content from OCR for node {node_id}")
  1257	            return 0
  1258	
  1259	        # Vectorize
  1260	        try:
  1261	            vec_result = await self._vectorizer.vectorize_text(combined_text)
  1262	        except Exception as e:
  1263	            if LOGURU_ENABLED:
  1264	                logger.error(f"[IMAGE-INDEX] Vectorization failed for node {node_id}: {e}")
  1265	            return 0
  1266	
  1267	        # Build document
  1268	        content_type = ocr_result.get("content_type", "text")
  1269	        chunk_id = hashlib.md5(f"image_ocr:{node_id}:{combined_text[:100]}".encode()).hexdigest()
  1270	        metadata = {
  1271	            "file_path": image_path,
  1272	            "source": "image_ocr",
  1273	            "source_type": "image_ocr",
  1274	            "node_id": node_id,
  1275	            "content_type": content_type,
  1276	            "subject": subject,
  1277	        }
  1278	
  1279	        doc = {
  1280	            "doc_id": f"img_{chunk_id}",
  1281	            "content": combined_text,
  1282	            "vector": vec_result.vector,
  1283	            "canvas_file": image_path,
  1284	            "node_id": node_id,
  1285	            "node_type": "image_ocr",
  1286	            "color": "",
  1287	            "x": 0,
  1288	            "y": 0,
  1289	            "subject": subject,
  1290	            "source_type": "image_ocr",
  1291	            "timestamp": datetime.now().isoformat(),
  1292	            "metadata_json": json.dumps(metadata, ensure_ascii=False),
  1293	        }
  1294	
  1295	        # Delete old image OCR data for this node
  1296	        if self._db is not None:
  1297	            try:
  1298	                # T3 根治 (2026-07-10): 每次 open_table, 不读缓存句柄
  1299	                try:
  1300	                    tbl = self._db.open_table(table_name)
  1301	                    self._tables_cache[table_name] = tbl
  1302	                except Exception:
  1303	                    tbl = None
  1304	
  1305	                if tbl is not None:
  1306	                    escaped_node = node_id.replace("'", "''")
  1307	                    try:
  1308	                        tbl.delete(f"node_id = '{escaped_node}'")
  1309	                    except Exception:
  1310	                        pass
  1311	            except Exception:
  1312	                pass
  1313	
  1314	        count = await self.add_documents(table_name, [doc])
  1315	
  1316	        # Story 2.4: Rebuild FTS index for hybrid search support
  1317	        if count > 0:
  1318	            self._rebuild_fts_index(table_name)
  1319	
  1320	        if LOGURU_ENABLED:
  1321	            logger.info(
  1322	                f"[IMAGE-INDEX] Indexed {count} chunks for node {node_id} "
  1323	                f"(text={len(ocr_text)} chars, type={content_type})"
  1324	            )
  1325	
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
  3400	            doc = doc_map[doc_id].copy()
  3401	            doc["_rrf_score"] = rrf_score
  3402	            # _distance 保留通道原始值 (vector=cosine 距离 / FTS-only=0.35);
  3403	            # 极端兜底: 两边都没有 _distance 时给中性值防 KeyError
  3404	            if doc.get("_distance") is None:
  3405	                doc["_distance"] = 0.5
  3406	            results.append(doc)
  3407	        return results
  3408	
  3409	    def _convert_to_search_results(
  3410	        self, raw_results: List[Dict[str, Any]], canvas_file: Optional[str] = None
  3411	    ) -> List[Dict[str, Any]]:
  3412	        """
  3413	        转换LanceDB结果为标准SearchResult格式
  3414	
  3415	        ✅ Story 12.2 AC 2.4: 结果转换
  3416	
  3417	        SearchResult格式:
  3418	        {
  3419	            "doc_id": str,
  3420	            "content": str,
  3421	            "score": float,
  3422	            "metadata": {
  3423	                "source": "lancedb",
  3424	                "timestamp": str,
  3425	                "canvas_file": str|None
  3426	            }
  3427	        }
  3428	        """
  3429	        search_results = []
  3430	
  3431	        for i, item in enumerate(raw_results):
  3432	            # 提取内容
  3433	            content = item.get("content") or item.get("text") or item.get("document") or ""
  3434	
  3435	            # 生成文档ID
  3436	            doc_id = item.get("doc_id") or item.get("id") or f"lancedb_{i}"
  3437	            if not doc_id.startswith("lancedb_"):
  3438	                doc_id = f"lancedb_{doc_id}"
  3439	
  3440	            # 计算分数 (LanceDB返回_distance, 需要转换为相似度)
  3441	            distance = item.get("_distance") or item.get("distance") or 0.0
  3442	            # 余弦距离转相似度: score = 1 / (1 + distance)
  3443	            # 或者: score = 1 - distance (如果distance在[0,1]范围)
  3444	            if distance >= 0:
  3445	                score = 1.0 / (1.0 + distance)
  3446	            else:
  3447	                score = 0.0
  3448	
  3449	            # 构建metadata
  3450	            metadata = {
  3451	                "source": "lancedb",
  3452	                "timestamp": datetime.now().isoformat(),
  3453	                "canvas_file": item.get("canvas_file") or canvas_file,
  3454	                "original_distance": distance,
  3455	            }
  3456	
  3457	            # 复制其他metadata字段
  3458	            for key in [
  3459	                "concept",
  3460	                "agent_type",
  3461	                "node_id",
  3462	                "metadata_json",
  3463	                # Story 2.8: Frontmatter / scope metadata
  3464	                "course",
  3465	                "tags_str",
  3466	                "category",
  3467	                # Story 2.9: Image OCR source type
  3468	                "source_type",
  3469	                # Story 2.8: Neighbor expansion marker
  3470	                "_source_type",
  3471	                # RAG-P0 A1: doc_type for source-aware filter/rerank
  3472	                "doc_type",
  3473	                # RAG-S2 T2 (2026-08-09): retrieval_confidence 地基 — RRF 融合
  3474	                # 信号此前被本白名单丢弃, 下游无法区分「双通道确认」与
  3475	                # 「dense-only 命中」(confidence 最强的一维, 零成本透传)。
  3476	                "_rrf_score",
  3477	                "_fts_only",
  3478	                # RAG-S2 T6: FTS 通道成员资格 (fts_confirmed 名实修复) —
  3479	                # _rrf_score 不承载通道信息, 双通道判定改用 _fts_hit
  3480	                "_fts_hit",
  3481	            ]:
  3482	                if key in item:
  3483	                    metadata[key] = item[key]
  3484	
  3485	            # Story 2.8/2.9: Propagate source_type to top-level metadata
  3486	            if "_source_type" in item:
  3487	                metadata["source_type"] = item["_source_type"]
  3488	            elif "source_type" in item:
  3489	                metadata["source_type"] = item["source_type"]
  3490	
  3491	            search_results.append(
  3492	                {
  3493	                    "doc_id": doc_id,
  3494	                    "content": content,
  3495	                    "score": score,
  3496	                    "metadata": metadata,
  3497	                }
  3498	            )
  3499	
  3500	        return search_results
  3501	
  3502	    def set_embedder(self, embedder):
  3503	        """
  3504	        设置嵌入器
  3505	
  3506	        Args:
  3507	            embedder: 异步函数 async def embed(text: str) -> List[float]
  3508	        """
  3509	        self._embedder = embedder
  3510	
  3511	    def _check_and_fix_dimension_mismatch(self, table_name: str, new_vector_dim: int) -> bool:
  3512	        """
  3513	        Story 2.3 Task 6 + RAG-P0 A5 (2026-05-10): Detect schema drift and
  3514	        auto drop+recreate. Triggers on:
  3515	          - vector dimension mismatch (e.g. 384d → 1024d on bge-m3 upgrade)
  3516	          - missing 'doc_type' column (RAG-P0 A1 added this column;
  3517	            pre-A1 tables lack it and would reject inserts that include it)
  3518	
  3519	        Args:
  3520	            table_name: LanceDB table name.
  3521	            new_vector_dim: Expected vector dimension (e.g. 1024 for bge-m3).
  3522	
  3523	        Returns:
  3524	            True if the table was dropped (caller should create new). False
  3525	            if schema matches or table doesn't exist.
  3526	        """
  3527	        if self._db is None:
  3528	            return False
  3529	
  3530	        try:
  3531	            # T3 根治 (2026-07-10): 存在性/句柄都以 db 为准, 不读缓存
  3532	            if table_name not in self._db.table_names():
  3533	                return False
  3534	            tbl = self._db.open_table(table_name)
  3535	            # Sample first row to inspect vector dimension
  3536	            rows = tbl.head(1).to_pydict()
  3537	            vectors = rows.get("vector", [])
  3538	            if not vectors or len(vectors) == 0:
  3539	                return False
  3540	
  3541	            existing_dim = len(vectors[0])
  3542	            dim_mismatch = existing_dim != new_vector_dim
  3543	
  3544	            # RAG-P0 A5: detect missing doc_type column on pre-A1 tables.
  3545	            # Use schema reflection rather than row-level inspection so that
  3546	            # tables with empty doc_type values still register as compliant.
  3547	            doc_type_missing = False
  3548	            try:
  3549	                col_names = set(tbl.schema.names)
  3550	                doc_type_missing = "doc_type" not in col_names
  3551	            except Exception:
  3552	                # Schema reflection failure is non-fatal — fall back to
  3553	                # row inspection
  3554	                doc_type_missing = "doc_type" not in rows
  3555	
  3556	            if not dim_mismatch and not doc_type_missing:
  3557	                return False
  3558	
  3559	            # Schema drift detected — drop table
  3560	            if LOGURU_ENABLED:
  3561	                reasons = []
  3562	                if dim_mismatch:
  3563	                    reasons.append(f"vector dim {existing_dim}!={new_vector_dim}")
  3564	                if doc_type_missing:
  3565	                    reasons.append("missing 'doc_type' column (pre-RAG-P0)")
  3566	                logger.warning(
  3567	                    f"[SCHEMA] Drift in '{table_name}': {', '.join(reasons)}. Dropping table for recreation."
  3568	                )
  3569	
  3570	            self._db.drop_table(table_name, ignore_missing=True)
  3571	            self._tables_cache.pop(table_name, None)
  3572	            return True
  3573	
  3574	        except Exception as e:
  3575	            if LOGURU_ENABLED:
  3576	                logger.debug(f"[SCHEMA] Schema check failed for '{table_name}': {e}")
  3577	            return False
  3578	
  3579	    async def add_documents(self, table_name: str, documents: List[Dict[str, Any]]) -> int:
  3580	        """
  3581	        添加文档到表
  3582	
  3583	        Args:
  3584	            table_name: 表名
  3585	            documents: 文档列表，每个包含 doc_id, content, vector, metadata
  3586	
  3587	        Returns:
  3588	            添加的文档数量
  3589	        """
  3590	        table_name = self.resolve_table_name(table_name)
  3591	        if self._db is None:
  3592	            return 0
  3593	
  3594	        try:
  3595	            # 准备数据

**Inspecting retriever handling of missing doc_type**
exec
/bin/zsh -lc "for spec in 'backend/lib/agentic_rag/retrievers/vault_notes_retriever.py:55,205' 'backend/app/services/supplementary_search_service.py:805,900' 'backend/app/services/supplementary_search_service.py:950,1060' 'backend/app/mcp/tools/note_search_tools.py:250,410' 'backend/app/services/supplementary_reranker.py:35,120' 'backend/app/services/supplementary_reranker.py:145,220' 'backend/app/api/v1/endpoints/chat.py:400,450' 'backend/scripts/run_vault_retrieval_regression.py:115,155'; do p="'${spec%%:*}; range=${spec#*:}; a=${range%,*}; b=${range#*,}; echo "$p lines $a-$b @37387a86"; git show 37387a86:"$p" | nl -ba | sed -n "${a},${b}p"; done' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
backend/lib/agentic_rag/retrievers/vault_notes_retriever.py lines 55-205 @37387a86
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
    55	@dataclass
    56	class VaultNotesRetrieverConfig:
    57	    """
    58	    VaultNotesRetriever配置
    59	
    60	    Attributes:
    61	        top_k: 返回结果数量 (默认10)
    62	        min_score: 最小相关度阈值 (默认0.3)
    63	        timeout_ms: 检索超时毫秒数 (默认500)
    64	        vault_notes_table: LanceDB表名
    65	        enable_cache: 是否启用缓存
    66	        default_exclude_doc_types: RAG-P0 A3 (2026-05-10) — default exclude
    67	            ['whiteboard'] so MOC/index whiteboards (mostly boilerplate
    68	            dataviewjs/callout templates) don't pollute solving / concept
    69	            queries. Pass exclude_doc_types=[] at call site to opt in.
    70	    """
    71	
    72	    top_k: int = 10
    73	    min_score: float = 0.3
    74	    timeout_ms: int = 500
    75	    vault_notes_table: str = "vault_notes"
    76	    enable_cache: bool = True
    77	    # RAG-S2 T6 审查修复 (2026-08-10, HARD-ISO): 此前只排 whiteboard 漏
    78	    # exam_board — 本 retriever 是 LangGraph 管道 retrieve_vault_notes 节点
    79	    # 的默认口径, 经无鉴权的 /api/v1/rag/query 与 agents.py 六处可达, 是
    80	    # live 泄漏通道 (T6 对抗审查实锤)。与 supplementary_search_service
    81	    # 查询侧排除表对齐; 未来出题链定向取材传显式 doc_type 即可 opt-in。
    82	    default_exclude_doc_types: List[str] = field(default_factory=lambda: ["whiteboard", "exam_board"])
    83	
    84	
    85	# ============================================================
    86	# Protocol for dependency injection
    87	# ============================================================
    88	
    89	
    90	class LanceDBClientProtocol(Protocol):
    91	    """Protocol for LanceDB client dependency injection."""
    92	
    93	    async def search(
    94	        self,
    95	        query: str,
    96	        table_name: str,
    97	        canvas_file: Optional[str] = None,
    98	        num_results: int = 10,
    99	        metric: str = "cosine",
   100	        doc_type: Optional[List[str]] = None,
   101	        exclude_doc_types: Optional[List[str]] = None,
   102	    ) -> List[Dict[str, Any]]:
   103	        """Search for similar vectors."""
   104	        ...
   105	
   106	
   107	# ============================================================
   108	# VaultNotesService
   109	# ============================================================
   110	
   111	
   112	class VaultNotesService:
   113	    """
   114	    Vault 笔记检索服务
   115	
   116	    从 LanceDB vault_notes 表中检索与查询相关的 .md 笔记段落。
   117	
   118	    Usage:
   119	        service = VaultNotesService(lancedb_client)
   120	        results = await service.search("A* admissible heuristic")
   121	    """
   122	
   123	    DEFAULT_TABLE = "vault_notes"
   124	
   125	    def __init__(
   126	        self,
   127	        lancedb_client: LanceDBClientProtocol,
   128	        config: Optional[VaultNotesRetrieverConfig] = None,
   129	    ):
   130	        self.lancedb = lancedb_client
   131	        self.config = config or VaultNotesRetrieverConfig()
   132	        self._initialized = False
   133	
   134	    async def initialize(self) -> bool:
   135	        self._initialized = True
   136	        return True
   137	
   138	    async def search(
   139	        self,
   140	        query: str,
   141	        num_results: int = 10,
   142	        group_id: Optional[str] = None,
   143	        doc_type: Optional[List[str]] = None,
   144	        exclude_doc_types: Optional[List[str]] = None,
   145	    ) -> List[Dict[str, Any]]:
   146	        """
   147	        搜索 vault 笔记内容
   148	
   149	        Args:
   150	            query: 搜索查询
   151	            num_results: 返回结果数量
   152	            group_id: Subject isolation namespace.  When ``None`` (default),
   153	                results are returned unchanged — single-vault assumption,
   154	                backward compatible with existing callers. When provided,
   155	                results are filtered using a **common-note downgrade** rule:
   156	                a row SURVIVES if its ``metadata.subject_id`` (or the nested
   157	                ``metadata.metadata_json.subject_id``) either equals the
   158	                requested ``group_id`` OR is ``None``. Rows with ``None``
   159	                subject_id are treated as **common / 通用主题 notes** that
   160	                join every group's result set. This avoids collapsing the
   161	                filter to an empty list under the current ingestion paths
   162	                that do not yet backfill ``subject_id`` for every document.
   163	                This is an isolation Phase 4 placeholder for the multi-vault
   164	                future; once vault_notes ingestion starts writing subject_id
   165	                consistently, the common-note downgrade becomes a minority
   166	                path and the filter becomes load-bearing for non-common rows.
   167	
   168	        Returns:
   169	            List[SearchResult]: 笔记检索结果，每个包含 source="vault_note"
   170	        """
   171	        start_time = time.perf_counter()
   172	
   173	        if not self._initialized:
   174	            await self.initialize()
   175	
   176	        try:
   177	            timeout_seconds = self.config.timeout_ms / 1000.0
   178	
   179	            # RAG-P0 A3: caller's exclude_doc_types wins; fall back to
   180	            # config default (whiteboard) when caller didn't pass anything.
   181	            # Pass exclude_doc_types=[] explicitly to opt OUT of filtering.
   182	            effective_exclude = (
   183	                exclude_doc_types if exclude_doc_types is not None else list(self.config.default_exclude_doc_types)
   184	            )
   185	
   186	            results = await asyncio.wait_for(
   187	                self.lancedb.search(
   188	                    query=query,
   189	                    table_name=self.config.vault_notes_table,
   190	                    num_results=num_results,
   191	                    doc_type=doc_type,
   192	                    exclude_doc_types=effective_exclude,
   193	                ),
   194	                timeout=timeout_seconds,
   195	            )
   196	
   197	            # 添加来源标注 + 解析 metadata_json
   198	            for r in results:
   199	                if "metadata" not in r:
   200	                    r["metadata"] = {}
   201	                r["metadata"]["source"] = "vault_note"
   202	
   203	                # Parse metadata_json for structured fields
   204	                metadata_json_str = r["metadata"].get("metadata_json")
   205	                if metadata_json_str and isinstance(metadata_json_str, str):
backend/app/services/supplementary_search_service.py lines 805-900 @37387a86
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
   805	    return True
   806	
   807	
   808	async def _two_tier_search(
   809	    client: Any,
   810	    query: str,
   811	    num_results: int,
   812	) -> list[dict[str, Any]]:
   813	    """先查 vault_id 隔离的 prefix 表（Story 1.9 主路径），空则 fallback 到 unprefixed 老索引。
   814	
   815	    Tier 1: client.search() 含 resolve_table_name 把 'vault_notes' 加 vault_id 前缀
   816	            （如 'canvas_vault_vault_notes'）。多 vault 切换时各自隔离，正确的主路径。
   817	    Tier 2: 直接 _db.open_table('vault_notes')（unprefixed），FTS 优先 + vector fallback。
   818	            兼容 Story 1.9 vault_id 隔离机制 land 前建立的老索引。
   819	            tier-2 命中时记 logger.warning 提醒 Ops 重建索引。
   820	    """
   821	    # ── Tier 1 ── prefix-resolved（Story 1.9 主路径，多 vault 隔离）
   822	    # RAG-P0 A3 (2026-05-10): default exclude whiteboard. MOC/index whiteboards
   823	    # carry mostly dataviewjs/callout boilerplate that pollutes solving queries.
   824	    results: list[dict[str, Any]] = []
   825	    try:
   826	        results = await client.search(
   827	            query=query,
   828	            table_name="vault_notes",
   829	            num_results=num_results,
   830	            query_type="hybrid",
   831	            # R3 第二层防御 (2026-07-12): exam_board 加入查询侧排除 — 索引黑名单
   832	            # 是单层防御 (incremental/index_single_file 曾有旁路), 考题万一入库
   833	            # 也在查询层拦住, 信息隔离 (d=1.50) 不再靠单点
   834	            exclude_doc_types=["whiteboard", "exam_board"],
   835	        )
   836	    except Exception as e:  # noqa: BLE001  T5 审查 HIGH-1: 任何异常都走 vector 回退
   837	        logger.warning(
   838	            "[SupplementarySearch] tier-1 hybrid 失败，回退到 vector-only",
   839	            error=str(e)[:120],
   840	        )
   841	        try:
   842	            results = await client.search(
   843	                query=query,
   844	                table_name="vault_notes",
   845	                num_results=num_results,
   846	                # RAG-S2 T5 (2026-08-10): 回退分支此前漏排 exam_board — hybrid
   847	                # 异常时 vector-only 路径成了考题隔离 (HARD-ISO) 的旁路, 与
   848	                # Tier-1 口径对齐。
   849	                exclude_doc_types=["whiteboard", "exam_board"],
   850	            )
   851	        except Exception as e2:  # noqa: BLE001
   852	            # T5 审查 HIGH-1: 两级都异常 = 基础设施故障, 不得吞成 [] —
   853	            # 旧行为会让上层判成 empty_index (degraded=False), MCP 面报
   854	            # ok_empty、hook 面标「检索正常但无材料」, 阶段 0 契约 3
   855	            # (健康空 ≠ 故障) 被打穿。包成 RuntimeError 走 search_failed
   856	            # 降级通道 (search_supplementary 只捕 RuntimeError/Connection/
   857	            # ValueError, 裸 re-raise 会逃逸破坏"内部全降级不外抛"契约)。
   858	            raise RuntimeError(f"tier-1 search failed (hybrid+vector): {str(e2)[:80]}") from e2
   859	
   860	    if results:
   861	        return results
   862	
   863	    # Wave-5 Stage C P1-9 (ChatGPT v4) — Tier-2 fallback gated by env var.
   864	    # Default production: skip tier-2 to prevent cross-vault leak via legacy
   865	    # unprefixed table (residual Story 1.9 升级前老索引). Dev / single-vault
   866	    # legacy can opt-in with ENABLE_LANCEDB_TIER2_FALLBACK=true.
   867	    if not _enable_tier2_fallback():
   868	        return []
   869	
   870	    # Tier-2 enabled — emit warning so Ops sees we're running in legacy mode.
   871	    try:
   872	        _active_vault_id = ""
   873	        try:
   874	            from app.config import get_settings as _gs
   875	
   876	            _active_vault_id = getattr(_gs(), "vault_id", "") or ""
   877	        except Exception:  # noqa: BLE001  config 缺失时不阻断 fallback
   878	            _active_vault_id = ""
   879	        logger.warning(
   880	            "[SupplementarySearch] tier-2 fallback enabled — single-vault legacy mode "
   881	            "(ENABLE_LANCEDB_TIER2_FALLBACK=true); cross-vault leak risk if residual "
   882	            "unprefixed vault_notes carries other vaults' data",
   883	            vault_id=_active_vault_id,
   884	            query=query[:60],
   885	        )
   886	    except Exception:  # noqa: BLE001  日志失败不阻断
   887	        pass
   888	
   889	    # ── Tier 2 ── unprefixed legacy table（兼容老索引；Story 1.9 升级前的数据）
   890	    try:
   891	        if not (hasattr(client, "_db") and client._db is not None):
   892	            return []
   893	        list_tables_fn = (
   894	            client._db.list_tables if hasattr(client._db, "list_tables") else getattr(client._db, "table_names", None)
   895	        )
   896	        if list_tables_fn is None:
   897	            return []
   898	        tables_raw = list_tables_fn()
   899	        # LanceDB ≥ 0.x 返回 ListTablesResponse(tables=[...], page_token=None)
   900	        # 旧版 / table_names() 返回 plain list — 兼容两者
backend/app/services/supplementary_search_service.py lines 950-1060 @37387a86
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
   950	                    "is_legacy_fallback": True,  # 顶层标志，方便下游 filter
   951	                    "degraded": True,
   952	                }
   953	            )
   954	        return normalized
   955	    except Exception as e:  # noqa: BLE001  tier-2 失败也不抛，让上层走 empty_index 降级
   956	        logger.warning(
   957	            "[SupplementarySearch] tier-2 fallback 失败",
   958	            error=str(e)[:120],
   959	        )
   960	        return []
   961	
   962	
   963	def _normalize_material(raw: dict[str, Any]) -> dict[str, Any]:
   964	    """LanceDB raw 行 → Phase A material dict（title / snippet / wikilink / score / source_path）。
   965	
   966	    复用 react_agent._format_results 的字段提取逻辑（Story 2.1 dad9ed7 通过 ChatGPT 8/10 审计）。
   967	    """
   968	    metadata = raw.get("metadata") or {}
   969	    score = float(raw.get("score", 0.0))
   970	    content = raw.get("content", "") or ""
   971	    # RAG-S2 T2 (2026-08-09): confidence 地基三字段透传 —
   972	    # raw_score(未加权语义分, 权重污染后可回算真实相关度) +
   973	    # rrf/fts 融合信号(区分双通道确认 vs dense-only, 此前 convert 层丢弃)。
   974	    raw_score = raw.get("_raw_score")
   975	    doc_type = metadata.get("doc_type", "") or raw.get("doc_type", "") or ""
   976	    # RAG-S2 T6 审查修复 (2026-08-10): 双通道确认改用 _fts_hit — 旧公式
   977	    # bool(_rrf_score) 名实颠倒: _rrf_score 写给所有融合行 (含 dense-only
   978	    # 甚至 FTS 分支整个挂掉的批次), dense-only 恒 True、真词法命中
   979	    # (FTS-only) 反而 False。现语义 = 出现在 FTS 通道 且 非 FTS-only
   980	    # (vector 亦命中) = 真·双通道确认。仍只做 confidence 遥测, 不进交付门。
   981	    fts_confirmed = bool(metadata.get("_fts_hit")) and not metadata.get("_fts_only")
   982	
   983	    # 优先 metadata.canvas_file（新 schema），fallback 到顶层 canvas_file（老 schema / tier-2）
   984	    canvas_file = metadata.get("canvas_file", "") or raw.get("canvas_file", "") or ""
   985	    heading = ""
   986	    source_type = "note"
   987	    meta_json_str = metadata.get("metadata_json", "")
   988	    if isinstance(meta_json_str, str) and meta_json_str:
   989	        try:
   990	            meta_parsed = json.loads(meta_json_str)
   991	            if not canvas_file:
   992	                canvas_file = meta_parsed.get("file_path", "") or ""
   993	            heading = meta_parsed.get("heading", "") or ""
   994	            source_type = meta_parsed.get("source_type", "note") or "note"
   995	        except json.JSONDecodeError:
   996	            pass
   997	
   998	    # 2026-05-09 P0 fix: chunks/merged.md 派生路径回写到原文件
   999	    canvas_file = _resolve_chunks_to_source_file(canvas_file)
  1000	    file_display = canvas_file[:-3] if canvas_file.endswith(".md") else canvas_file
  1001	
  1002	    # 2026-05-09 wikilink 跳转修复 (3 agent 实测确认):
  1003	    # ⛔ heading anchor 必须**字面 100% 匹配** vault 内文档的 heading
  1004	    # - 文档真实 heading: "6.4.1 解决局部最优陷阱的方法 [59:00]()-[01:00]()"
  1005	    # - 之前 over-strip [time]() 后剩 "6.4.1 ... 方法 -" → Obsidian 找不到 → 仅跳文件不滚动
  1006	    # → heading 字面完整保留（含视频 timestamp 残留），display text 才做清洗供视觉简洁
  1007	    raw_heading = heading or ""  # 保留 LanceDB 索引时的原始 heading 字面（与文档一致）
  1008	    display_heading = raw_heading
  1009	    if display_heading:
  1010	        # display text (用户视觉) 仅做清洗：去 [time]() / [[wikilink]] / 末尾空白
  1011	        display_heading = re.sub(r"\[\[.*?\]\]", "", display_heading).strip()
  1012	        display_heading = re.sub(r"\[.*?\]\(.*?\)", "", display_heading).strip()
  1013	        display_heading = re.sub(r"\s+-\s*$", "", display_heading).strip()  # 末尾 ` -` 残留
  1014	        display_heading = re.sub(r"^\s+|\s+$", "", display_heading)
  1015	    heading = raw_heading  # ⭐ wikilink anchor 用字面 raw heading（保跳转）
  1016	
  1017	    # 2026-05-09 wikilink 拼接: anchor 用 raw heading 字面匹配文档，display 用 clean 简洁视觉
  1018	    # ⛔ wikilink heading anchor 含 `[time]()` 时 Obsidian wikilink parser 行为未公开
  1019	    # 业界备选 (Smart Connections / Khoj): 用 markdown link `[display](file.md#heading)`
  1020	    # 当前先试 wikilink 字面 anchor 路径，如 Obsidian 解析仍失败再切 markdown link
  1021	    display_text = display_heading or heading or ""
  1022	    if file_display and heading and heading != file_display:
  1023	        wikilink = f"[[{file_display}#{heading}|{display_text}]]"
  1024	        title = display_text
  1025	    elif file_display:
  1026	        wikilink = f"[[{file_display}]]"
  1027	        title = file_display.split("/")[-1]
  1028	    else:
  1029	        doc_id = raw.get("doc_id", "") or ""
  1030	        wikilink = f"[Doc: {doc_id}]" if doc_id else "[unknown]"
  1031	        title = doc_id or "未命名片段"
  1032	
  1033	    snippet = content[:300]
  1034	    if len(content) > 300:
  1035	        snippet += "..."
  1036	
  1037	    return {
  1038	        "title": title,
  1039	        "wikilink": wikilink,
  1040	        "snippet": snippet,
  1041	        "score": score,
  1042	        "source_path": canvas_file,
  1043	        "source_type": source_type,
  1044	        # RAG-S2 T2: confidence 地基 (raw_score=未加权语义分 /
  1045	        # doc_type=按类型加权与断言用 / fts_confirmed=双通道确认)
  1046	        "raw_score": raw_score,
  1047	        "doc_type": doc_type,
  1048	        "fts_confirmed": fts_confirmed,
  1049	    }
  1050	
  1051	
  1052	def _xml_escape(text: str) -> str:
  1053	    """最小 XML 安全转义（防止 vault 笔记内容里的 `<` / `&` 破坏 XML 解析）。"""
  1054	    if not isinstance(text, str):
  1055	        text = str(text)
  1056	    return (
  1057	        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("\n", " ")
  1058	    )
backend/app/mcp/tools/note_search_tools.py lines 250-410 @37387a86
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
   250	    quarantine 时正文与 title/wikilink/source_path 一律 placeholder — 否则
   251	    MCP 面成为 prompt injection 的绕行通道。ce_score/raw_score 等内部量纲
   252	    走 per-result metadata 搭车 (MCP 是工具面不是 prompt 面, 无 XML 契约)。
   253	    """
   254	    taint = m.get("taint", "clean")
   255	    injection_risk = float(m.get("injection_risk", 0.0) or 0.0)
   256	    if taint == "quarantine":
   257	        content = (
   258	            "[QUARANTINED — content blocked due to suspected prompt injection. "
   259	            "Use Read tool on source_path to verify if needed.]"
   260	        )
   261	        title = f"[QUARANTINED: tainted title (risk={injection_risk:.2f})]"
   262	        wikilink = "[QUARANTINED]"
   263	        file_path = "[QUARANTINED]"
   264	    elif taint == "review":
   265	        content = f"[REDACTED: suspicious content (risk={injection_risk:.2f}); open source_path manually to verify]"
   266	        title = f"[REDACTED: tainted title (risk={injection_risk:.2f})]"
   267	        wikilink = "[REDACTED]"
   268	        file_path = "[REDACTED]"
   269	    else:
   270	        content = str(m.get("content") or m.get("snippet") or "")
   271	        title = str(m.get("title", ""))
   272	        wikilink = str(m.get("wikilink", ""))
   273	        file_path = str(m.get("source_path", ""))
   274	
   275	    # T5 审查 MEDIUM-3: 非 clean 材料的 metadata 只保留数值/布尔信号 —
   276	    # doc_type/source_type 来自 frontmatter 自由文本 (仅 lower/strip 无枚举
   277	    # 校验), 攻击者可把 payload 埋 `type:` 字段, 遮蔽只盖 content/title/
   278	    # wikilink/file_path 时 metadata 成漏网面。
   279	    if taint != "clean":
   280	        signal_keys = (
   281	            "raw_score",
   282	            "fts_confirmed",
   283	            "ce_score",
   284	            "injection_risk",
   285	            "is_link_list_chunk",
   286	            "is_legacy_fallback",
   287	        )
   288	    else:
   289	        signal_keys = (
   290	            "raw_score",
   291	            "doc_type",
   292	            "fts_confirmed",
   293	            "ce_score",
   294	            "injection_risk",
   295	            "source_type",
   296	            "is_link_list_chunk",
   297	            "is_legacy_fallback",
   298	        )
   299	    metadata: Dict[str, Any] = {k: m[k] for k in signal_keys if m.get(k) is not None}
   300	    metadata["taint"] = taint
   301	    metadata["title"] = title
   302	    metadata["wikilink"] = wikilink
   303	
   304	    return NoteResultItem(
   305	        content=content,
   306	        file_path=file_path,
   307	        relevance_score=float(m.get("score") or 0.0),
   308	        source="lancedb_fast",
   309	        metadata=metadata,
   310	    )
   311	
   312	
   313	# ═══════════════════════════════════════════════════════════════════════════════
   314	# Tool Implementation
   315	# ═══════════════════════════════════════════════════════════════════════════════
   316	
   317	
   318	async def search_notes(
   319	    query: str,
   320	    canvas_file: Optional[str] = None,
   321	    subject_id: Optional[str] = None,
   322	    max_results: int = 10,
   323	    cross_subject: bool = False,
   324	    fusion_strategy: Optional[str] = None,
   325	) -> Dict[str, Any]:
   326	    """
   327	    Search user's Vault notes.
   328	
   329	    Default ("fast"): direct LanceDB + BGE-M3 vector search over vault_notes.
   330	    This is the path that has actually served every result since 2026-05-11.
   331	
   332	    Extended (RAG_EXTENDED_MODE env, stage-4 shadow evaluation only): the full
   333	    LangGraph multi-source pipeline. If it returns empty, the fast path still
   334	    delivers and execution_mode is reported as "fallback".
   335	
   336	    Args:
   337	        query: Natural language search query.
   338	        canvas_file: Optional canvas file for scoping (extended mode only).
   339	        subject_id: Optional subject for isolation (extended mode only).
   340	        max_results: Maximum results to return.
   341	        cross_subject: Whether to expand to related subjects (extended mode only).
   342	        fusion_strategy: Override fusion strategy (extended mode only).
   343	
   344	    Returns:
   345	        Dict with results, execution_mode, source_status, status.
   346	    """
   347	    extended_mode = _extended_mode_enabled()
   348	    execution_mode = "extended" if extended_mode else "fast"
   349	    try:
   350	        items: List[NoteResultItem] = []
   351	        confidence: Optional[Dict[str, Any]] = None
   352	
   353	        if extended_mode:
   354	            # Stage-4 shadow evaluation only — retired from the default chain
   355	            # (RAG-S0-2026-08-02). Known-dead as of retirement: 0/5 channels.
   356	            from app.services.rag_service import get_rag_service
   357	
   358	            rag_service = get_rag_service()
   359	            raw_results: List[Dict[str, Any]] = []
   360	            try:
   361	                rag_result = await rag_service.query(
   362	                    query=query,
   363	                    canvas_file=canvas_file,
   364	                    subject_id=subject_id,
   365	                    cross_subject=cross_subject,
   366	                    fusion_strategy=fusion_strategy,
   367	                )
   368	                raw_results = rag_result.get("reranked_results") or rag_result.get("results") or []
   369	            except Exception as pipeline_exc:
   370	                logger.error(
   371	                    f"[search_notes] extended pipeline failed: {pipeline_exc}",
   372	                    exc_info=True,
   373	                )
   374	                raw_results = []
   375	
   376	            if raw_results:
   377	                items = [_legacy_row_to_item(r) for r in raw_results[:max_results]]
   378	            else:
   379	                logger.warning("[search_notes] extended pipeline returned 0; falling back to shared fast path")
   380	                # Declare BEFORE the await: if the fast path itself fails
   381	                # here, the error must be attributed to "fallback", not to
   382	                # the pipeline — stage-4 shadow evaluation depends on this.
   383	                execution_mode = "fallback"
   384	                supp_result = await _fast_path_search(query, max_results)
   385	                items = [_material_to_item(m) for m in supp_result.get("materials", [])]
   386	                confidence = supp_result.get("confidence")
   387	        else:
   388	            supp_result = await _fast_path_search(query, max_results)
   389	            items = [_material_to_item(m) for m in supp_result.get("materials", [])]
   390	            confidence = supp_result.get("confidence")
   391	
   392	        source_status = "ok_nonempty" if items else "ok_empty"
   393	
   394	        logger.info(
   395	            f"[F2] search_notes: query='{query[:50]}' results={len(items)} "
   396	            f"mode={execution_mode} source_status={source_status} "
   397	            f"confidence={(confidence or {}).get('level')}"
   398	        )
   399	
   400	        return NoteSearchOutput(
   401	            query=query,
   402	            results=items,
   403	            total_count=len(items),
   404	            execution_mode=execution_mode,
   405	            source_status=source_status,
   406	            status="ok",
   407	            retrieval_confidence=confidence,
   408	        ).model_dump()
   409	
   410	    except Exception as e:
backend/app/services/supplementary_reranker.py lines 35-120 @37387a86
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
    35	# ═══════════════════════════════════════════════════════════════════════════════
    36	
    37	# P0-A 过渡映射 (2026-05-12 hotfix): indexer 当前实际写入的 source_type
    38	# (lancedb_client.py:1444/1644) 只有 {note, video_transcript, image_ocr}, PRD §4.1.1
    39	# 6 档分类 (lecture_notes / discussion / ...) 是 indexer 升级目标。如果只保留 PRD
    40	# 6 keys, 所有真实数据 fallback 到 DEFAULT_TYPE_WEIGHT=0.5 → P0-B filter 0.42 几乎
    41	# 全删材料。解法: 表里同时包含 PRD 6 档 (forward compat, indexer 升级后立刻可用)
    42	# 加 indexer 当前真实 3 类 (过渡兜底)。indexer 升级到 PRD 6 档后, 过渡 3 类自然
    43	# 失去命中, 行为优雅退化。
    44	TYPE_WEIGHTS: dict[str, float] = {
    45	    # PRD §4.1.1 frozen 2026-05-11 (forward compat for indexer 升级)
    46	    "lecture_notes": 1.0,
    47	    "discussion": 0.9,
    48	    "exam_review": 0.85,
    49	    "wiki_concepts": 0.8,
    50	    "chat_session": 0.7,
    51	    "raw_notes": 0.6,
    52	    # P0-A 过渡 (indexer 升级到 PRD 6 档前的实际命中映射, 2026-05-12 hotfix):
    53	    # RAG-S2 T2 (2026-08-09) 权重方向翻转: 旧值 video_transcript 0.9 > note 0.7
    54	    # 把转录排在手写笔记之上, 与用户初衷相反 (开工基线 handwritten_share
    55	    # @10 = 0.17%)。翻转: 手写/概念笔记最高, 转录居中。
    56	    "concept": 1.0,  # 派生概念节点 (doc_type=concept) → 用户手写, 最高
    57	    "note": 1.0,  # 普通 vault 笔记 → 用户手写, 最高
    58	    "video_transcript": 0.75,  # 视频 transcript → 素材层, 低于手写
    59	    "image_ocr": 0.6,  # OCR 出来的图片文字 → 同 raw_notes 低档 (准确度有限)
    60	}
    61	
    62	# Unknown / None / empty source_type fallback. Below all canonical (min 0.6) so
    63	# unknown data surfaces visibly in trace.included.type_weight rather than
    64	# silently being treated as a canonical category.
    65	DEFAULT_TYPE_WEIGHT: float = 0.5
    66	
    67	
    68	def get_type_weight(source_type: str | None) -> float:
    69	    """Map source_type to type weight (PRD §4.1.1).
    70	
    71	    None / empty / unknown values fall back to DEFAULT_TYPE_WEIGHT.
    72	    """
    73	    if not source_type:
    74	        return DEFAULT_TYPE_WEIGHT
    75	    return TYPE_WEIGHTS.get(source_type, DEFAULT_TYPE_WEIGHT)
    76	
    77	
    78	# ═══════════════════════════════════════════════════════════════════════════════
    79	# Rerank engine (Phase T3b — type weight only; future phases extend final_score)
    80	# ═══════════════════════════════════════════════════════════════════════════════
    81	
    82	
    83	# Story 2.2 AC #4: "user_question 无时走 Phase 1 默认排序"
    84	# → query=None / query="" / mode!="solve" 时 query_overlap=0, 仅用 type_weight
    85	DEFAULT_QUERY_OVERLAP_WEIGHT: float = 0.3
    86	
    87	
    88	def compute_hub_penalty(degree: int, median_degree: float) -> float:
    89	    """Story 2.9 AC #2: hub_penalty = log(degree / median + 1).
    90	
    91	    Edge cases:
    92	    - degree <= 0 → 0 (孤立节点不该被惩罚)
    93	    - median_degree <= 0 → 0 (空图或单节点图,无 hub 概念)
    94	
    95	    Formula uses natural log; degree=median yields ln(2)≈0.69, degree=2×median
    96	    yields ln(3)≈1.10. Caller decide whether to apply scale factor.
    97	    """
    98	    if degree <= 0 or median_degree <= 0:
    99	        return 0.0
   100	    return math.log(degree / median_degree + 1.0)
   101	
   102	
   103	# Story 2.2 AC #4 T3.9 filter: 最终 rerank_score 低于
   104	# (0.70 × min_canonical_type_weight) 的材料不显示。
   105	DEFAULT_FILTER_QUALITY_RATIO: float = 0.70
   106	
   107	
   108	def get_filter_threshold(quality_ratio: float = DEFAULT_FILTER_QUALITY_RATIO) -> float:
   109	    """T3.9 filter threshold = quality_ratio × min(TYPE_WEIGHTS.values()).
   110	
   111	    DEFAULT_TYPE_WEIGHT 不参与计算（DEFAULT 表示"未知"应该被压低，
   112	    threshold 用 canonical 最低 raw_notes=0.6 作为可接受质量下限）。
   113	    """
   114	    return quality_ratio * min(TYPE_WEIGHTS.values())
   115	
   116	
   117	def rerank(
   118	    materials: list[dict[str, Any]],
   119	    *,
   120	    query: str | None = None,
backend/app/services/supplementary_reranker.py lines 145-220 @37387a86
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
   145	    Args:
   146	        materials: candidate dicts，至少含 `score` (float, [0,1])、
   147	            `source_type` (str | None)；可选 `degree` (int, 用于 hub_penalty)
   148	        query: user question string. None / 空 → query_overlap=0
   149	        query_overlap_weight: query_overlap 加权系数（默认 0.3，PRD §4.1.1）
   150	        median_degree: degree 基线（来自 wikilink_graph_service.get_degree_stats()
   151	            的 `median`）。0 → hub_penalty 全部为 0（小 vault 场景）
   152	        type_weights: 覆盖默认 TYPE_WEIGHTS（仅测试 / 实验用）
   153	        min_score_threshold: T3.9 filter — 过滤 rerank_score < 此值的材料
   154	            （None = 不过滤；典型值 get_filter_threshold() = 0.42）
   155	        top_k: T3.10 — 截取前 N 条（None = 不截断；典型 Top 5）
   156	        min_keep: P0-B floor — filter 后剩 < min_keep 条 OR 删掉 > 80% candidates
   157	            时, 兜底放弃 filter (改返回未 filter 的 sorted list, 仍 top_k 截断),
   158	            并在第 1 条材料注入 `filter_floor_triggered=True` 供 logger 观测.
   159	            min_keep=0 关闭兜底.
   160	
   161	    Returns:
   162	        重排后的 list（已 in-place sort + 字段注入；过滤+截断的可能是新 list）
   163	    """
   164	    if not materials:
   165	        return []
   166	
   167	    weights = type_weights if type_weights is not None else TYPE_WEIGHTS
   168	
   169	    query_overlaps = _compute_query_overlap(materials, query)
   170	
   171	    for m, query_overlap in zip(materials, query_overlaps):
   172	        relevance = float(m.get("score", 0.0))
   173	        source_type = m.get("source_type") or ""
   174	        type_weight = weights.get(source_type, DEFAULT_TYPE_WEIGHT)
   175	        degree = int(m.get("degree", 0))
   176	        hub_pen = compute_hub_penalty(degree, median_degree)
   177	
   178	        m["type_weight"] = type_weight
   179	        m["query_overlap"] = query_overlap
   180	        m["hub_penalty"] = hub_pen
   181	        m["rerank_score"] = relevance * type_weight + query_overlap * query_overlap_weight - hub_pen
   182	
   183	    materials.sort(
   184	        key=lambda m: (-m["rerank_score"], str(m.get("title", ""))),
   185	    )
   186	
   187	    # P0-B (2026-05-12 hotfix): 过滤 floor 兜底.
   188	    # 当 indexer 未升级到 PRD 6 档时, real-world 数据 source_type="note" 命中过渡
   189	    # 表 0.7, 典型 relevance ~0.5 → final ~0.35 < filter_threshold 0.42 → 全删.
   190	    # 用户原话: "不硬编码 5 条, 把有用的都提供给我"
   191	    # → filter 后剩 < min_keep 或删 > 80% 候选, 视为 threshold 误杀, 自动降级为
   192	    #   不过滤但仍 top_k 截断, 第 1 条注入 filter_floor_triggered=True 供 logger
   193	    #   观察以便调阈值. floor=0 关闭兜底 (现有测试 + 显式 opt-out).
   194	    #
   195	    # P0-3b (2026-05-12 hotfix, ChatGPT v2 fail-closed real): 即使 floor_triggered,
   196	    # 也必须过滤 taint ∈ {review, quarantine} 的材料. floor 初衷是 "保护边缘
   197	    # candidate 不被全删", 但 review/quarantine 是安全审查决定的污染标记, 不应
   198	    # 因 floor 而 backdoor 入选 (兜底也不能让可疑材料绕过审查).
   199	    if min_score_threshold is not None:
   200	        kept = [m for m in materials if m["rerank_score"] >= min_score_threshold]
   201	        n_pre = len(materials)
   202	        n_post = len(kept)
   203	        floor_triggered = False
   204	        if min_keep > 0 and n_pre > 0:
   205	            kill_ratio = 1.0 - (n_post / n_pre)
   206	            if n_post < min_keep or kill_ratio > 0.80:
   207	                floor_triggered = True
   208	        if floor_triggered:
   209	            logger.warning(
   210	                "[Rerank] filter_floor_triggered",
   211	                pre=n_pre,
   212	                post=n_post,
   213	                threshold=round(min_score_threshold, 3),
   214	                min_keep=min_keep,
   215	            )
   216	            # P0-3b: floor 仍 fail-closed 过滤 review/quarantine 材料
   217	            materials = [m for m in materials if m.get("taint") not in {"review", "quarantine"}]
   218	            # 标记兜底, 仍走 top_k
   219	            if materials:
   220	                materials[0]["filter_floor_triggered"] = True
backend/app/api/v1/endpoints/chat.py lines 400-450 @37387a86
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
   400	            # P0-C (2026-05-12 hotfix): 冷启 30s 内 singleton 仍 None,
   401	            # 直接读会立即 fallback lancedb_unavailable, 用户冷启首问也拿不到补充材料.
   402	            # 改走 lazy init 路径 (5s budget) — 若已 ready 立即返回, 未 ready 时
   403	            # 给 5s 窗口尝试触发 init (init 真要 60s+ 走 timeout 自然降级).
   404	            # 5s 是 hook/answer 模式延迟预算的合理上限.
   405	            lancedb_client = await _get_supp_lancedb_client(init_timeout=5.0)
   406	            node_title = Path(req.node_path).stem
   407	            supp_query = f"{node_title} {req.user_question}".strip()
   408	            supp_result = await search_supplementary(
   409	                query=supp_query,
   410	                lancedb_client=lancedb_client,
   411	                # 2026-05-09 RAG-as-tool 范式重构：用户原话"不硬编码 5 条，把有用的都提供"
   412	                # → top_k_max 大召回 + elbow_cut 动态截断（业界推荐 vs 硬编码 top_k）
   413	                # → Claude 用 Read tool 真核实是 verifier（candidate generator + verifier 分离）
   414	                top_k_max=supp_top_k_max,
   415	                # R1 止血 (2026-07-12): _rrf_fuse 不再覆盖 _distance, score 恢复
   416	                # 真实语义幅度 (1/(1+cosine_d))。0.50 = 主仓 3604 chunks 真机校准:
   417	                # 相关查询 0.51-0.65 / 零相关 0.45-0.49, 分界干净。
   418	                min_relevance=0.50,
   419	                # R1 (2026-07-12): 0.05→0.25 — elbow 作用在 source_priority 加权分上,
   420	                # 权重跨度 (0.3~1.5) 造成的 gap 不是语义悬崖 (真机: 0.72→0.50 的
   421	                # 权重差把正确命中误砍); 真语义悬崖 (>0.25) 仍触发
   422	                elbow_drop_threshold=0.25,
   423	                hard_cap=supp_hard_cap,
   424	            )
   425	            # Story 2.2+2.9 T3.7-T3.10 (2026-05-11) — query-aware rerank
   426	            # final_score = relevance × type_weight + query_overlap × 0.3 - hub_penalty
   427	            # 顺序: score → sort → filter(0.42) → truncate(top 5)
   428	            from app.services.supplementary_reranker import (
   429	                get_filter_threshold,
   430	                rerank,
   431	            )
   432	            from app.services.wikilink_graph_service import (
   433	                get_wikilink_graph_service,
   434	            )
   435	
   436	            graph_svc = get_wikilink_graph_service()
   437	            if graph_svc.is_built:
   438	                degree_stats = graph_svc.get_degree_stats()
   439	                median_degree = float(degree_stats.get("median", 0.0))
   440	                # 用 source_path 反查 degree (best-effort, basename fallback 已内置)
   441	                for m in supp_result.get("materials", []):
   442	                    sp = m.get("source_path", "")
   443	                    if sp:
   444	                        m["degree"] = graph_svc.get_degree(sp)
   445	            else:
   446	                median_degree = 0.0
   447	
   448	            pre_rerank_count = len(supp_result.get("materials", []))
   449	            supp_result["materials"] = rerank(
   450	                supp_result.get("materials", []),
backend/scripts/run_vault_retrieval_regression.py lines 115-155 @37387a86
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
   115	    """结果对 expect_hit 的分级: file+contains 全中→声明 grade;
   116	    仅 file 中→min(grade,2) (段落不确定)。取所有匹配的最高值。"""
   117	    path_n = norm_text(m.get("source_path", ""))
   118	    snip_n = norm_text(material_text(m))
   119	    best = 0
   120	    for e in expects:
   121	        if norm_text(e["file"]) not in path_n:
   122	            continue
   123	        g = int(e.get("grade", 2))
   124	        if e.get("contains") and norm_text(e["contains"]) not in snip_n:
   125	            g = min(g, 2)
   126	        best = max(best, g)
   127	    return best
   128	
   129	
   130	def is_contaminated(m: dict, cfg_contam: dict) -> bool:
   131	    path = str(m.get("source_path", ""))
   132	    if any(fnmatch.fnmatch(path, g) or path.startswith(g.rstrip("*")) for g in cfg_contam.get("path_globs", [])):
   133	        return True
   134	    return str(m.get("doc_type", "")) in set(cfg_contam.get("doc_types", []))
   135	
   136	
   137	def forbidden_violations(m: dict, forb: dict) -> list:
   138	    path = str(m.get("source_path", ""))
   139	    out = []
   140	    for g in forb.get("path_globs", []):
   141	        if fnmatch.fnmatch(path, g) or path.startswith(g.rstrip("*")):
   142	            out.append(f"path {path!r} 命中硬禁 glob {g!r}")
   143	    if str(m.get("doc_type", "")) in set(forb.get("doc_types", [])):
   144	        out.append(f"doc_type {m.get('doc_type')!r} 属硬禁类型 (path={path!r})")
   145	    text_n = norm_text(material_text(m))
   146	    for marker in forb.get("markers", []):
   147	        if norm_text(marker) in text_n:
   148	            out.append(f"命中硬禁标记 {marker!r} (path={path!r})")
   149	    return out
   150	
   151	
   152	def ndcg_at_k(grades: list, declared: list, k: int) -> float:
   153	    """nDCG@k: gain=2^grade-1。IDCG 用金集声明的 grade 降序 (补 0)。"""
   154	    dcg = sum((2**g - 1) / math.log2(i + 2) for i, g in enumerate(grades[:k]))
   155	    ideal = sorted((int(e.get("grade", 2)) for e in declared), reverse=True)

exec
/bin/zsh -lc "git show 37387a86:backend/app/mcp/tools/note_search_tools.py | nl -ba | sed -n '265,310p'; git show 37387a86:backend/app/api/v1/endpoints/chat.py | nl -ba | sed -n '445,470p'; git grep -n 'get_type_weight' 37387a86 -- 'backend/*.py'; git grep -n 'neighbor_expansion' 37387a86 -- 'backend/*.py'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
   265	        content = f"[REDACTED: suspicious content (risk={injection_risk:.2f}); open source_path manually to verify]"
   266	        title = f"[REDACTED: tainted title (risk={injection_risk:.2f})]"
   267	        wikilink = "[REDACTED]"
   268	        file_path = "[REDACTED]"
   269	    else:
   270	        content = str(m.get("content") or m.get("snippet") or "")
   271	        title = str(m.get("title", ""))
   272	        wikilink = str(m.get("wikilink", ""))
   273	        file_path = str(m.get("source_path", ""))
   274	
   275	    # T5 审查 MEDIUM-3: 非 clean 材料的 metadata 只保留数值/布尔信号 —
   276	    # doc_type/source_type 来自 frontmatter 自由文本 (仅 lower/strip 无枚举
   277	    # 校验), 攻击者可把 payload 埋 `type:` 字段, 遮蔽只盖 content/title/
   278	    # wikilink/file_path 时 metadata 成漏网面。
   279	    if taint != "clean":
   280	        signal_keys = (
   281	            "raw_score",
   282	            "fts_confirmed",
   283	            "ce_score",
   284	            "injection_risk",
   285	            "is_link_list_chunk",
   286	            "is_legacy_fallback",
   287	        )
   288	    else:
   289	        signal_keys = (
   290	            "raw_score",
   291	            "doc_type",
   292	            "fts_confirmed",
   293	            "ce_score",
   294	            "injection_risk",
   295	            "source_type",
   296	            "is_link_list_chunk",
   297	            "is_legacy_fallback",
   298	        )
   299	    metadata: Dict[str, Any] = {k: m[k] for k in signal_keys if m.get(k) is not None}
   300	    metadata["taint"] = taint
   301	    metadata["title"] = title
   302	    metadata["wikilink"] = wikilink
   303	
   304	    return NoteResultItem(
   305	        content=content,
   306	        file_path=file_path,
   307	        relevance_score=float(m.get("score") or 0.0),
   308	        source="lancedb_fast",
   309	        metadata=metadata,
   310	    )
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
   445	            else:
   446	                median_degree = 0.0
   447	
   448	            pre_rerank_count = len(supp_result.get("materials", []))
   449	            supp_result["materials"] = rerank(
   450	                supp_result.get("materials", []),
   451	                query=req.user_question,
   452	                median_degree=median_degree,
   453	                min_score_threshold=get_filter_threshold(),
   454	                top_k=5,
   455	            )
   456	            post_rerank_count = len(supp_result["materials"])
   457	            logger.info(
   458	                "[Story-2.2+2.9-T3] rerank 完成",
   459	                pre=pre_rerank_count,
   460	                post=post_rerank_count,
   461	                filter_threshold=round(get_filter_threshold(), 3),
   462	                median_degree=median_degree,
   463	                query=req.user_question[:60] if req.user_question else None,
   464	            )
   465	
   466	            # T5 审查 MEDIUM-4: confidence 是按 rerank 前的 top1 算的 —
   467	            # supplementary_reranker 重排/过滤/截断后可能已把被背书的材料
   468	            # 删掉 (hub_penalty), 陈旧 level 会为没交付的材料背书。摘掉让
   469	            # XML 不渲染 confidence attr (向后兼容分支), 诚实优先; 本端点
   470	            # 按 rerank 后重算留待后续。hook 面无 rerank, 不受影响。
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
37387a86:backend/app/services/supplementary_reranker.py:68:def get_type_weight(source_type: str | None) -> float:
37387a86:backend/tests/unit/test_supplementary_reranker.py:51:        from app.services.supplementary_reranker import get_type_weight
37387a86:backend/tests/unit/test_supplementary_reranker.py:53:        assert get_type_weight("lecture_notes") == 1.0
37387a86:backend/tests/unit/test_supplementary_reranker.py:54:        assert get_type_weight("raw_notes") == 0.6
37387a86:backend/tests/unit/test_supplementary_reranker.py:59:            get_type_weight,
37387a86:backend/tests/unit/test_supplementary_reranker.py:62:        assert get_type_weight(None) == DEFAULT_TYPE_WEIGHT
37387a86:backend/tests/unit/test_supplementary_reranker.py:67:            get_type_weight,
37387a86:backend/tests/unit/test_supplementary_reranker.py:70:        assert get_type_weight("") == DEFAULT_TYPE_WEIGHT
37387a86:backend/tests/unit/test_supplementary_reranker.py:75:            get_type_weight,
37387a86:backend/tests/unit/test_supplementary_reranker.py:81:        assert get_type_weight("totally_unknown_xyz") == DEFAULT_TYPE_WEIGHT
37387a86:backend/tests/unit/test_supplementary_reranker.py:82:        assert get_type_weight("foobar") == DEFAULT_TYPE_WEIGHT
37387a86:backend/tests/unit/test_supplementary_reranker.py:583:            get_type_weight,
37387a86:backend/tests/unit/test_supplementary_reranker.py:586:        w = get_type_weight("note")
37387a86:backend/tests/unit/test_supplementary_reranker.py:591:        from app.services.supplementary_reranker import get_type_weight
37387a86:backend/tests/unit/test_supplementary_reranker.py:594:        assert get_type_weight("video_transcript") == 0.9
37387a86:backend/tests/unit/test_supplementary_reranker.py:597:        from app.services.supplementary_reranker import get_type_weight
37387a86:backend/tests/unit/test_supplementary_reranker.py:600:        assert get_type_weight("image_ocr") == 0.6
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:2214:        Neighbor chunks get decayed scores and source_type="neighbor_expansion".
37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:2264:                        neighbor_doc["_source_type"] = "neighbor_expansion"
37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:2274:                fr["metadata"]["source_type"] = "neighbor_expansion"
37387a86:backend/lib/agentic_rag/config.py:175:    neighbor_expansion_enabled: bool  # Wiki-links 邻居扩展 (默认 True)
37387a86:backend/lib/agentic_rag/config.py:255:    neighbor_expansion_enabled=True,
37387a86:backend/lib/agentic_rag/config.py:357:        "neighbor_expansion_enabled",

**Clarifying rerank weight source attribution**
**Planning adversarial audit for source_type concept**
exec
/bin/zsh -lc "git grep -n -E 'source_type.{0,30}concept|concept.{0,30}source_type' 37387a86 -- 'backend/*.py'; git grep -n -E 'add_documents\\(' 37387a86 -- 'backend/*.py'; git grep -n -E 'doc_type.{0,40}(note|video_transcript|whiteboard|exam_board|concept)|(\"note\"|\"video_transcript\"|\"whiteboard\"|\"exam_board\"|\"concept\").{0,40}doc_type' 37387a86 -- 'backend/*.py'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
37387a86:backend/tests/unit/test_supplementary_reranker.py:300:                "source_type": "wiki_concepts",
37387a86:backend/tests/unit/test_supplementary_reranker.py:306:                "source_type": "wiki_concepts",
37387a86:backend/tests/unit/test_supplementary_reranker.py:402:            "source_type": "wiki_concepts",
37387a86:backend/tests/unit/test_supplementary_reranker.py:416:            "source_type": "wiki_concepts",
37387a86:backend/tests/unit/test_supplementary_reranker.py:435:                "source_type": "wiki_concepts",
37387a86:backend/tests/unit/test_supplementary_reranker.py:441:                "source_type": "wiki_concepts",
37387a86:backend/tests/unit/test_supplementary_reranker.py:453:        m = {"score": 0.5, "source_type": "wiki_concepts", "title": "X"}
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:1314:        count = await self.add_documents(table_name, [doc])
37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:1562:        count = await self.add_documents(table_name, documents)
37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:1828:            chunk_count = await self.add_documents(table_name, documents)
37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:2110:        count = await self.add_documents(table_name, documents)
37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:3579:    async def add_documents(self, table_name: str, documents: List[Dict[str, Any]]) -> int:
37387a86:backend/lib/agentic_rag/storage/multimodal_store.py:155:        await self.lancedb_client.add_documents(
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
37387a86:backend/app/config.py:48:#:   - 检验白板: 双层 —— 目录黑名单 + 读侧 exclude_doc_types=["whiteboard","exam_board"]
37387a86:backend/app/services/react_agent.py:115:            exclude_doc_types=["whiteboard", "exam_board"],
37387a86:backend/app/services/react_agent.py:124:                exclude_doc_types=["whiteboard", "exam_board"],
37387a86:backend/app/services/supplementary_reranker.py:56:    "concept": 1.0,  # 派生概念节点 (doc_type=concept) → 用户手写, 最高
37387a86:backend/app/services/supplementary_search_service.py:834:            exclude_doc_types=["whiteboard", "exam_board"],
37387a86:backend/app/services/supplementary_search_service.py:849:                exclude_doc_types=["whiteboard", "exam_board"],
37387a86:backend/app/services/tool_executor.py:97:        RAG-P0 A3 (2026-05-10): default exclude doc_type='whiteboard' so that
37387a86:backend/app/services/tool_executor.py:112:                exclude_doc_types=["whiteboard", "exam_board"],
37387a86:backend/app/services/tool_executor.py:122:                    exclude_doc_types=["whiteboard", "exam_board"],
37387a86:backend/lib/agentic_rag/agent_graph.py:208:                    exclude_doc_types=["whiteboard", "exam_board"],
37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:1771:                # RAG-P0 A1: doc_type — frontmatter.type wins; video_transcript
37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:1773:                fm_doc_type = chunk.get("doc_type", "note") or "note"
37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:1774:                if fm_doc_type == "note" and LanceDBClient._is_video_transcript(chunk["file_path"]):
37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:1775:                    final_doc_type = "video_transcript"
37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:2058:            fm_doc_type_2 = chunk.get("doc_type", "note") or "note"
37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:2059:            if fm_doc_type_2 == "note" and LanceDBClient._is_video_transcript(file_path):
37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:2060:                final_doc_type_2 = "video_transcript"
37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:2686:        # 携带 doc_type=whiteboard 仍被检索默认排除) — 此处不再无差别剥离。
37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:2711:        section 不产 chunk + 考察文件 doc_type 推断 exam_board + 行号补 frontmatter 偏移。
37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:2738:        # RAG-P0 A1 (2026-05-10): doc_type from frontmatter.type, default 'note'.
37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:2756:                fm_doc_type = "exam_board"
37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:2758:                fm_doc_type = "note"
37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:2767:        if fm_doc_type == "whiteboard":
37387a86:backend/lib/agentic_rag/clients/lancedb_client.py:3135:            if "note" in doc_type:
37387a86:backend/tests/regression/test_rag_stage0_contracts.py:41:                "doc_type": "concept",
37387a86:backend/tests/regression/test_rag_stage2_chain_unify_contracts.py:43:def _raw_row(path, raw_score, content="真实学习内容。" * 10, fts=False, doc_type="concept"):
37387a86:backend/tests/regression/test_rag_stage2_chain_unify_contracts.py:180:    assert "exam_board" in captured.get("exclude_doc_types", []), "HARD-ISO: MCP 链必须排除考题白板"
37387a86:backend/tests/regression/test_rag_stage2_chain_unify_contracts.py:488:    """hybrid 异常回退 vector-only 时 exclude_doc_types 必须含 exam_board —
37387a86:backend/tests/regression/test_rag_stage2_chain_unify_contracts.py:505:    assert "exam_board" in calls[1].get("exclude_doc_types", []), "回退分支漏排 exam_board = 隔离旁路回归"
37387a86:backend/tests/regression/test_rag_stage2_chain_unify_contracts.py:506:    assert "whiteboard" in calls[1].get("exclude_doc_types", [])
37387a86:backend/tests/regression/test_rag_stage2_chunk_contracts.py:3:# 组 A doc_type 推断: 考察文件 (exam_question_id, 无 type:) → exam_board;
37387a86:backend/tests/regression/test_rag_stage2_chunk_contracts.py:47:    doc_type NOT IN ('whiteboard','exam_board') 排除拦不住 = 信息隔离旁路。
37387a86:backend/tests/regression/test_rag_stage2_chunk_contracts.py:59:    assert {c["doc_type"] for c in chunks} == {"exam_board"}
37387a86:backend/tests/regression/test_rag_stage2_chunk_contracts.py:65:    assert {c["doc_type"] for c in chunks} == {"concept"}
37387a86:backend/tests/regression/test_rag_stage2_chunk_contracts.py:71:    assert {c["doc_type"] for c in chunks} == {"note"}
37387a86:backend/tests/regression/test_rag_stage2_chunk_contracts.py:290:    assert {c["doc_type"] for c in chunks} == {"exam_board"}, "YAML 失败路径不得回落 note"
37387a86:backend/tests/regression/test_rag_stage2_rerank_contracts.py:297:        "metadata": {"canvas_file": path, "doc_type": "concept"},
37387a86:backend/tests/regression/test_rag_stage2_t6_verification_contracts.py:39:    metadata = {"canvas_file": path, "doc_type": "concept", "_rrf_score": 0.032}
37387a86:backend/tests/regression/test_rag_stage2_t6_verification_contracts.py:318:        assert "exam_board" in kw.get("exclude_doc_types", []), "react agent 链不得成为题面泄漏通道"
37387a86:backend/tests/regression/test_rag_stage2_t6_verification_contracts.py:339:        assert "exam_board" in kw.get("exclude_doc_types", [])
37387a86:backend/tests/unit/test_rag_p0_doc_type_filter.py:2:RAG-P0 (2026-05-10) — A1+A2+A4 doc_type filtering & whiteboard boilerplate stripping.
37387a86:backend/tests/unit/test_rag_p0_doc_type_filter.py:25:def test_split_md_by_heading_extracts_doc_type_whiteboard():
37387a86:backend/tests/unit/test_rag_p0_doc_type_filter.py:43:        assert c["doc_type"] == "whiteboard"
37387a86:backend/tests/unit/test_rag_p0_doc_type_filter.py:46:def test_split_md_by_heading_extracts_doc_type_default_note():
37387a86:backend/tests/unit/test_rag_p0_doc_type_filter.py:57:    assert all(c["doc_type"] == "note" for c in chunks)
37387a86:backend/tests/unit/test_rag_p0_doc_type_filter.py:64:    assert all(c["doc_type"] == "note" for c in chunks)
37387a86:backend/tests/unit/test_rag_p0_doc_type_filter.py:78:    clauses = _client()._build_where_filters(exclude_doc_types=["whiteboard"])
37387a86:backend/tests/unit/test_rag_p0_doc_type_filter.py:80:        "doc_type NOT IN ('whiteboard')" in c and "doc_type IS NULL" in c
37387a86:backend/tests/unit/test_rag_p0_doc_type_filter.py:86:    clauses = _client()._build_where_filters(doc_type=["note"])
37387a86:backend/tests/unit/test_rag_p0_doc_type_filter.py:88:        "doc_type IN ('note')" in c and "doc_type IS NULL" in c for c in clauses
37387a86:backend/tests/unit/test_rag_p0_doc_type_filter.py:105:        exclude_doc_types=["whiteboard"],

**Inspecting multimodal_store data handling**
**Analyzing commit chronology and metadata**
exec
/bin/zsh -lc 'git show --name-status --format=fuller fce0d8a2; git show --name-status --format=fuller 73102875; git diff --name-status 73102875..fce0d8a2 -- backend/pytest.ini backend/tests/unit/test_supplementary_reranker.py backend/tests/unit/test_supplementary_search_service.py backend/conftest.py backend/tests/conftest.py backend/app/services/supplementary_reranker.py backend/app/services/supplementary_search_service.py' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
commit fce0d8a2800768a039f0aa05de7a5504d79f63d8
Author:     oinani0721 <2272104243@qq.com>
AuthorDate: Fri Aug 28 19:32:38 2026 +0800
Commit:     oinani0721 <2272104243@qq.com>
CommitDate: Fri Aug 28 19:32:38 2026 +0800

    fix(census): G4-9/G4-16 Codex round-3 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9 / CARD-G4-16]
    
    G4-9(4/6→6/6): transcript 并入 --out 保护集(防截断恢复源)、O_NOFOLLOW+
    fstat 消 check-then-open TOCTOU、os.walk 替 glob(不跟随目录 symlink+遍历
    错误显式捕获)、不可读候选 os.access 门 fail-closed、JSONL 严格 LF 分帧
    (splitlines 会被 U+2028 劈行)、非 dict JSON 归 unparseable、报告头补
    artifact commit 链。6 条新反例实测全过；第三次全量重跑 92 条/4-88-0/
    89-2-1/6-29/shasum 不变——三轮整改数字全程未变。
    G4-16(5/7→7/7): 测试 provenance 从声明改为可复验完整捕获(git 切基线版
    真实重跑 before + 切 HEAD 重跑 after, 完整 stdout 归一化后逐字节相同);
    grep 证据命令去占位符+绑定 pinned SHA+zsh -n 校验通过。
    三条行为铁律经 round-3 独立复验通过。
    
    Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>

M	"_bmad-output/\345\256\241\346\237\245/G4-16-doc-type-census-2026-08-28.md"
M	"_bmad-output/\345\256\241\346\237\245/G4-16-evidence/live-distribution-and-value-grep.txt"
A	"_bmad-output/\345\256\241\346\237\245/G4-16-evidence/pytest-after-full-stdout.txt"
A	"_bmad-output/\345\256\241\346\237\245/G4-16-evidence/pytest-before-full-stdout.txt"
M	"_bmad-output/\345\256\241\346\237\245/G4-16-evidence/test-run-metadata.txt"
M	"_bmad-output/\345\256\241\346\237\245/G4-9-DLQ-census-2026-08-28.md"
M	"_bmad-output/\345\256\241\346\237\245/G4-9-dlq-ledger-2026-08-28.json"
M	"_bmad-output/\345\256\241\346\237\245/G4-9-evidence/grep-selfattest.txt"
A	"_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-16-round3.md"
A	"_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round3.md"
M	"_bmad-output/\351\252\214\346\224\266\345\215\225/UAT-CARD-G4-16-doc_type\346\227\217\346\216\245\347\272\277\346\231\256\346\237\245-2026-08-28.md"
M	"_bmad-output/\351\252\214\346\224\266\345\215\225/UAT-CARD-G4-9-DLQ\347\234\237\345\256\236\346\214\202\350\275\275census\345\210\206\350\257\212-2026-08-28.md"
M	backend/scripts/census_dead_letter_episodes.py
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

M	"_bmad-output/\345\256\241\346\237\245/G4-16-doc-type-census-2026-08-28.md"
M	"_bmad-output/\345\256\241\346\237\245/G4-16-evidence/after-edits.txt"
M	"_bmad-output/\345\256\241\346\237\245/G4-16-evidence/live-distribution-and-value-grep.txt"
M	"_bmad-output/\345\256\241\346\237\245/G4-16-evidence/test-run-metadata.txt"
M	"_bmad-output/\345\256\241\346\237\245/G4-9-DLQ-census-2026-08-28.md"
M	"_bmad-output/\345\256\241\346\237\245/G4-9-dlq-ledger-2026-08-28.json"
M	"_bmad-output/\345\256\241\346\237\245/G4-9-evidence/grep-selfattest.txt"
A	"_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-16-round2.md"
A	"_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round2.md"
M	"_bmad-output/\351\252\214\346\224\266\345\215\225/UAT-CARD-G4-16-doc_type\346\227\217\346\216\245\347\272\277\346\231\256\346\237\245-2026-08-28.md"
M	"_bmad-output/\351\252\214\346\224\266\345\215\225/UAT-CARD-G4-9-DLQ\347\234\237\345\256\236\346\214\202\350\275\275census\345\210\206\350\257\212-2026-08-28.md"
M	backend/app/services/supplementary_reranker.py
M	backend/scripts/census_dead_letter_episodes.py
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead

**Verifying backend script changes since 731**
exec
/bin/zsh -lc 'git diff --name-status 73102875..HEAD -- backend; git diff --name-status 73102875..HEAD -- backend/pytest.ini backend/tests/unit/test_supplementary_reranker.py backend/tests/unit/test_supplementary_search_service.py backend/tests/conftest.py backend/conftest.py backend/app/services/supplementary_reranker.py backend/app/services/supplementary_search_service.py' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
M	backend/scripts/census_dead_letter_episodes.py
A	backend/tests/regression/test_census_dead_letter_readonly_contract.py
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead

**Verifying metadata for placeholders**
**Planning read-only rerun with diff**
exec
/bin/zsh -lc "diff <(sed -E 's/0x[0-9a-f]+/0xADDR/g; s/in [0-9]+\\.[0-9]+s/in T.TTs/g' _bmad-output/审查/G4-16-evidence/pytest-before-full-stdout.txt) <(sed -E 's/0x[0-9a-f]+/0xADDR/g; s/in [0-9]+\\.[0-9]+s/in T.TTs/g' _bmad-output/审查/G4-16-evidence/pytest-after-full-stdout.txt); echo normalized_diff_exit="'$?; for f in _bmad-output/审查/G4-16-evidence/pytest-before-full-stdout.txt _bmad-output/审查/G4-16-evidence/pytest-after-full-stdout.txt; do wc -lc "$f"; shasum -a 256 "$f"; sed -E '"'s/0x[0-9a-f]+/0xADDR/g; s/in [0-9]+\\.[0-9]+s/in T.TTs/g' \""'$f" | wc -c; sed -E '"'s/0x[0-9a-f]+/0xADDR/g; s/in [0-9]+\\.[0-9]+s/in T.TTs/g' \""'$f" | shasum -a 256; done; diff -u _bmad-output/审查/G4-16-evidence/pytest-before-full-stdout.txt _bmad-output/审查/G4-16-evidence/pytest-after-full-stdout.txt | sed -n '"'1,220p'; echo raw_diff_pipeline_exit="'${pipestatus[1]}' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
diff: /dev/fd/11: Operation not permitted
normalized_diff_exit=2
     109    9957 _bmad-output/审查/G4-16-evidence/pytest-before-full-stdout.txt
42d94922339a0fdb2799017bbf0b1ad02293d3dd1cfa1d91c6fd0a19313109c5  _bmad-output/审查/G4-16-evidence/pytest-before-full-stdout.txt
    9912
03e576078dbc5c854b1db7695c1a654195afa69f52f5212d79577e491fde84e8  -
     109    9957 _bmad-output/审查/G4-16-evidence/pytest-after-full-stdout.txt
4303b0df29b66ef7ef4219626882f3e7c7bde8fd448d6ba350553dab532236cd  _bmad-output/审查/G4-16-evidence/pytest-after-full-stdout.txt
    9912
03e576078dbc5c854b1db7695c1a654195afa69f52f5212d79577e491fde84e8  -
--- _bmad-output/审查/G4-16-evidence/pytest-before-full-stdout.txt	2026-08-28 19:27:03
+++ _bmad-output/审查/G4-16-evidence/pytest-after-full-stdout.txt	2026-08-28 19:27:24
@@ -15,13 +15,13 @@
 tests/unit/test_supplementary_reranker.py:594: in test_indexer_video_transcript_mapped_to_canonical
     assert get_type_weight("video_transcript") == 0.9
 E   AssertionError: assert 0.75 == 0.9
-E    +  where 0.75 = <function get_type_weight at 0x17accf7f0>('video_transcript')
+E    +  where 0.75 = <function get_type_weight at 0x1387577f0>('video_transcript')
 __________ TestFilterFloor.test_floor_triggered_marks_first_material ___________
 tests/unit/test_supplementary_reranker.py:653: in test_floor_triggered_marks_first_material
     assert result[0].get("filter_floor_triggered") is True
 E   AssertionError: assert None is True
-E    +  where None = <built-in method get of dict object at 0x17af2e0c0>('filter_floor_triggered')
-E    +    where <built-in method get of dict object at 0x17af2e0c0> = {'hub_penalty': 0.0, 'query_overlap': 0.0, 'rerank_score': 0.5, 'score': 0.5, ...}.get
+E    +  where None = <built-in method get of dict object at 0x1389b6ac0>('filter_floor_triggered')
+E    +    where <built-in method get of dict object at 0x1389b6ac0> = {'hub_penalty': 0.0, 'query_overlap': 0.0, 'rerank_score': 0.5, 'score': 0.5, ...}.get
 ______________ TestFilterFloor.test_min_keep_zero_disables_floor _______________
 tests/unit/test_supplementary_reranker.py:684: in test_min_keep_zero_disables_floor
     assert len(result) == 0
@@ -31,14 +31,14 @@
 tests/unit/test_supplementary_reranker.py:698: in test_floor_triggered_when_kill_ratio_high
     assert result[0].get("filter_floor_triggered") is True
 E   AssertionError: assert None is True
-E    +  where None = <built-in method get of dict object at 0x17aefd700>('filter_floor_triggered')
-E    +    where <built-in method get of dict object at 0x17aefd700> = {'hub_penalty': 0.0, 'query_overlap': 0.0, 'rerank_score': 0.5, 'score': 0.5, ...}.get
+E    +  where None = <built-in method get of dict object at 0x13897e280>('filter_floor_triggered')
+E    +    where <built-in method get of dict object at 0x13897e280> = {'hub_penalty': 0.0, 'query_overlap': 0.0, 'rerank_score': 0.5, 'score': 0.5, ...}.get
 _______________ TestFilterFloor.test_floor_still_respects_top_k ________________
 tests/unit/test_supplementary_reranker.py:710: in test_floor_still_respects_top_k
     assert result[0].get("filter_floor_triggered") is True
 E   AssertionError: assert None is True
-E    +  where None = <built-in method get of dict object at 0x17af18e40>('filter_floor_triggered')
-E    +    where <built-in method get of dict object at 0x17af18e40> = {'hub_penalty': 0.0, 'query_overlap': 0.0, 'rerank_score': 0.5, 'score': 0.5, ...}.get
+E    +  where None = <built-in method get of dict object at 0x1389a3f80>('filter_floor_triggered')
+E    +    where <built-in method get of dict object at 0x1389a3f80> = {'hub_penalty': 0.0, 'query_overlap': 0.0, 'rerank_score': 0.5, 'score': 0.5, ...}.get
 ___ TestFilterFloorTaintExclusion.test_min_keep_floor_excludes_review_taint ____
 tests/unit/test_supplementary_reranker.py:752: in test_min_keep_floor_excludes_review_taint
     assert len(result) == 2
@@ -48,8 +48,8 @@
 tests/unit/test_supplementary_reranker.py:795: in test_floor_no_taint_field_treated_as_clean
     assert result[0].get("filter_floor_triggered") is True
 E   AssertionError: assert None is True
-E    +  where None = <built-in method get of dict object at 0x17af11940>('filter_floor_triggered')
-E    +    where <built-in method get of dict object at 0x17af11940> = {'hub_penalty': 0.0, 'query_overlap': 0.0, 'rerank_score': 0.5, 'score': 0.5, ...}.get
+E    +  where None = <built-in method get of dict object at 0x13898b440>('filter_floor_triggered')
+E    +    where <built-in method get of dict object at 0x13898b440> = {'hub_penalty': 0.0, 'query_overlap': 0.0, 'rerank_score': 0.5, 'score': 0.5, ...}.get
 ____ TestFilterFloorTaintExclusion.test_floor_all_review_returns_empty_list ____
 tests/unit/test_supplementary_reranker.py:813: in test_floor_all_review_returns_empty_list
     assert len(result) == 0
@@ -105,5 +105,5 @@
 FAILED tests/unit/test_supplementary_reranker.py::TestFilterFloorTaintExclusion::test_min_keep_floor_excludes_review_taint
 FAILED tests/unit/test_supplementary_reranker.py::TestFilterFloorTaintExclusion::test_floor_no_taint_field_treated_as_clean
 FAILED tests/unit/test_supplementary_reranker.py::TestFilterFloorTaintExclusion::test_floor_all_review_returns_empty_list
-================== 9 failed, 102 passed, 10 warnings in 0.47s ==================
+================== 9 failed, 102 passed, 10 warnings in 0.45s ==================
 exit_code=1
raw_diff_pipeline_exit=1

**Identifying sandbox restrictions blocking process substitution**
**Planning escalated rerun to bypass sandbox**
exec
/bin/zsh -lc "diff <(sed -E 's/0x[0-9a-f]+/0xADDR/g; s/in [0-9]+\\.[0-9]+s/in T.TTs/g' _bmad-output/审查/G4-16-evidence/pytest-before-full-stdout.txt) <(sed -E 's/0x[0-9a-f]+/0xADDR/g; s/in [0-9]+\\.[0-9]+s/in T.TTs/g' _bmad-output/审查/G4-16-evidence/pytest-after-full-stdout.txt); echo normalized_diff_exit="'$?' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
normalized_diff_exit=0

**Extracting and diffing stdout lines**
exec
/bin/zsh -lc 'nl -ba _bmad-output/审查/G4-16-evidence/pytest-before-full-stdout.txt; nl -ba _bmad-output/审查/G4-16-evidence/pytest-after-full-stdout.txt; nl -ba _bmad-output/审查/G4-16-evidence/baseline-before-edits.txt; nl -ba _bmad-output/审查/G4-16-evidence/after-edits.txt; nl -ba _bmad-output/审查/G4-16-evidence/live-distribution-and-value-grep.txt' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
     1	============================= test session starts ==============================
     2	collected 111 items
     3	
     4	tests/unit/test_supplementary_reranker.py .............................. [ 27%]
     5	............FF...F.FFFF.FF                                               [ 50%]
     6	tests/unit/test_supplementary_search_service.py ........................ [ 72%]
     7	...............................                                          [100%]
     8	
     9	=================================== FAILURES ===================================
    10	____ TestTypeWeightsIndexerTransition.test_indexer_note_mapped_to_canonical ____
    11	tests/unit/test_supplementary_reranker.py:587: in test_indexer_note_mapped_to_canonical
    12	    assert w == 0.7
    13	E   assert 1.0 == 0.7
    14	_ TestTypeWeightsIndexerTransition.test_indexer_video_transcript_mapped_to_canonical _
    15	tests/unit/test_supplementary_reranker.py:594: in test_indexer_video_transcript_mapped_to_canonical
    16	    assert get_type_weight("video_transcript") == 0.9
    17	E   AssertionError: assert 0.75 == 0.9
    18	E    +  where 0.75 = <function get_type_weight at 0x17accf7f0>('video_transcript')
    19	__________ TestFilterFloor.test_floor_triggered_marks_first_material ___________
    20	tests/unit/test_supplementary_reranker.py:653: in test_floor_triggered_marks_first_material
    21	    assert result[0].get("filter_floor_triggered") is True
    22	E   AssertionError: assert None is True
    23	E    +  where None = <built-in method get of dict object at 0x17af2e0c0>('filter_floor_triggered')
    24	E    +    where <built-in method get of dict object at 0x17af2e0c0> = {'hub_penalty': 0.0, 'query_overlap': 0.0, 'rerank_score': 0.5, 'score': 0.5, ...}.get
    25	______________ TestFilterFloor.test_min_keep_zero_disables_floor _______________
    26	tests/unit/test_supplementary_reranker.py:684: in test_min_keep_zero_disables_floor
    27	    assert len(result) == 0
    28	E   AssertionError: assert 5 == 0
    29	E    +  where 5 = len([{'hub_penalty': 0.0, 'query_overlap': 0.0, 'rerank_score': 0.5, 'score': 0.5, ...}, {'hub_penalty': 0.0, 'query_overl...nk_score': 0.5, 'score': 0.5, ...}, {'hub_penalty': 0.0, 'query_overlap': 0.0, 'rerank_score': 0.5, 'score': 0.5, ...}])
    30	__________ TestFilterFloor.test_floor_triggered_when_kill_ratio_high ___________
    31	tests/unit/test_supplementary_reranker.py:698: in test_floor_triggered_when_kill_ratio_high
    32	    assert result[0].get("filter_floor_triggered") is True
    33	E   AssertionError: assert None is True
    34	E    +  where None = <built-in method get of dict object at 0x17aefd700>('filter_floor_triggered')
    35	E    +    where <built-in method get of dict object at 0x17aefd700> = {'hub_penalty': 0.0, 'query_overlap': 0.0, 'rerank_score': 0.5, 'score': 0.5, ...}.get
    36	_______________ TestFilterFloor.test_floor_still_respects_top_k ________________
    37	tests/unit/test_supplementary_reranker.py:710: in test_floor_still_respects_top_k
    38	    assert result[0].get("filter_floor_triggered") is True
    39	E   AssertionError: assert None is True
    40	E    +  where None = <built-in method get of dict object at 0x17af18e40>('filter_floor_triggered')
    41	E    +    where <built-in method get of dict object at 0x17af18e40> = {'hub_penalty': 0.0, 'query_overlap': 0.0, 'rerank_score': 0.5, 'score': 0.5, ...}.get
    42	___ TestFilterFloorTaintExclusion.test_min_keep_floor_excludes_review_taint ____
    43	tests/unit/test_supplementary_reranker.py:752: in test_min_keep_floor_excludes_review_taint
    44	    assert len(result) == 2
    45	E   AssertionError: assert 3 == 2
    46	E    +  where 3 = len([{'hub_penalty': 0.0, 'query_overlap': 0.0, 'rerank_score': 0.5, 'score': 0.5, ...}, {'hub_penalty': 0.0, 'query_overl... 0.5, 'score': 0.5, ...}, {'hub_penalty': 0.0, 'injection_risk': 0.55, 'query_overlap': 0.0, 'rerank_score': 0.5, ...}])
    47	___ TestFilterFloorTaintExclusion.test_floor_no_taint_field_treated_as_clean ___
    48	tests/unit/test_supplementary_reranker.py:795: in test_floor_no_taint_field_treated_as_clean
    49	    assert result[0].get("filter_floor_triggered") is True
    50	E   AssertionError: assert None is True
    51	E    +  where None = <built-in method get of dict object at 0x17af11940>('filter_floor_triggered')
    52	E    +    where <built-in method get of dict object at 0x17af11940> = {'hub_penalty': 0.0, 'query_overlap': 0.0, 'rerank_score': 0.5, 'score': 0.5, ...}.get
    53	____ TestFilterFloorTaintExclusion.test_floor_all_review_returns_empty_list ____
    54	tests/unit/test_supplementary_reranker.py:813: in test_floor_all_review_returns_empty_list
    55	    assert len(result) == 0
    56	E   AssertionError: assert 5 == 0
    57	E    +  where 5 = len([{'hub_penalty': 0.0, 'injection_risk': 0.6, 'query_overlap': 0.0, 'rerank_score': 0.5, ...}, {'hub_penalty': 0.0, 'in...'rerank_score': 0.5, ...}, {'hub_penalty': 0.0, 'injection_risk': 0.6, 'query_overlap': 0.0, 'rerank_score': 0.5, ...}])
    58	=============================== warnings summary ===============================
    59	.venv/lib/python3.14/site-packages/google/genai/types.py:43
    60	  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/.venv/lib/python3.14/site-packages/google/genai/types.py:43: DeprecationWarning: '_UnionGenericAlias' is deprecated and slated for removal in Python 3.17
    61	    VersionedUnionType = Union[builtin_types.UnionType, _UnionGenericAlias]
    62	
    63	.venv/lib/python3.14/site-packages/langchain_core/_api/deprecation.py:25
    64	  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/.venv/lib/python3.14/site-packages/langchain_core/_api/deprecation.py:25: UserWarning: Core Pydantic V1 functionality isn't compatible with Python 3.14 or greater.
    65	    from pydantic.v1.fields import FieldInfo as FieldInfoV1
    66	
    67	.venv/lib/python3.14/site-packages/graphiti_core/driver/search_interface/search_interface.py:22
    68	  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/.venv/lib/python3.14/site-packages/graphiti_core/driver/search_interface/search_interface.py:22: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    69	    class SearchInterface(BaseModel):
    70	
    71	.venv/lib/python3.14/site-packages/jieba/_compat.py:18
    72	  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/.venv/lib/python3.14/site-packages/jieba/_compat.py:18: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
    73	    import pkg_resources
    74	
    75	<frozen importlib._bootstrap>:491
    76	  <frozen importlib._bootstrap>:491: DeprecationWarning: builtin type SwigPyPacked has no __module__ attribute
    77	
    78	<frozen importlib._bootstrap>:491
    79	  <frozen importlib._bootstrap>:491: DeprecationWarning: builtin type SwigPyObject has no __module__ attribute
    80	
    81	app/api/v1/endpoints/chat.py:803
    82	  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/app/api/v1/endpoints/chat.py:803: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    83	    class HookEnrichRequest(BaseModel):
    84	
    85	app/api/v1/endpoints/metadata.py:147
    86	  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/app/api/v1/endpoints/metadata.py:147: FastAPIDeprecationWarning: `example` has been deprecated, please use `examples` instead
    87	    canvas_path: str = Query(
    88	
    89	app/api/v1/endpoints/metadata.py:218
    90	  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/app/api/v1/endpoints/metadata.py:218: FastAPIDeprecationWarning: `example` has been deprecated, please use `examples` instead
    91	    canvas_path: str = Query(..., description="Canvas file path", example="Math 54/离散数学.canvas"),
    92	
    93	.venv/lib/python3.14/site-packages/pydantic/_internal/_generate_schema.py:2356
    94	  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/.venv/lib/python3.14/site-packages/pydantic/_internal/_generate_schema.py:2356: PydanticDeprecatedSince211: The `__get_pydantic_core_schema__` method of the `BaseModel` class is deprecated. If you are calling `super().__get_pydantic_core_schema__` when overriding the method on a Pydantic model, consider using `handler(source)` instead. However, note that overriding this method on models can lead to unexpected side effects. Deprecated in Pydantic V2.11 to be removed in V3.0.
    95	    schema = annotation_get_schema(source, get_inner_schema)
    96	
    97	-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
    98	=========================== short test summary info ============================
    99	FAILED tests/unit/test_supplementary_reranker.py::TestTypeWeightsIndexerTransition::test_indexer_note_mapped_to_canonical
   100	FAILED tests/unit/test_supplementary_reranker.py::TestTypeWeightsIndexerTransition::test_indexer_video_transcript_mapped_to_canonical
   101	FAILED tests/unit/test_supplementary_reranker.py::TestFilterFloor::test_floor_triggered_marks_first_material
   102	FAILED tests/unit/test_supplementary_reranker.py::TestFilterFloor::test_min_keep_zero_disables_floor
   103	FAILED tests/unit/test_supplementary_reranker.py::TestFilterFloor::test_floor_triggered_when_kill_ratio_high
   104	FAILED tests/unit/test_supplementary_reranker.py::TestFilterFloor::test_floor_still_respects_top_k
   105	FAILED tests/unit/test_supplementary_reranker.py::TestFilterFloorTaintExclusion::test_min_keep_floor_excludes_review_taint
   106	FAILED tests/unit/test_supplementary_reranker.py::TestFilterFloorTaintExclusion::test_floor_no_taint_field_treated_as_clean
   107	FAILED tests/unit/test_supplementary_reranker.py::TestFilterFloorTaintExclusion::test_floor_all_review_returns_empty_list
   108	================== 9 failed, 102 passed, 10 warnings in 0.47s ==================
   109	exit_code=1
     1	============================= test session starts ==============================
     2	collected 111 items
     3	
     4	tests/unit/test_supplementary_reranker.py .............................. [ 27%]
     5	............FF...F.FFFF.FF                                               [ 50%]
     6	tests/unit/test_supplementary_search_service.py ........................ [ 72%]
     7	...............................                                          [100%]
     8	
     9	=================================== FAILURES ===================================
    10	____ TestTypeWeightsIndexerTransition.test_indexer_note_mapped_to_canonical ____
    11	tests/unit/test_supplementary_reranker.py:587: in test_indexer_note_mapped_to_canonical
    12	    assert w == 0.7
    13	E   assert 1.0 == 0.7
    14	_ TestTypeWeightsIndexerTransition.test_indexer_video_transcript_mapped_to_canonical _
    15	tests/unit/test_supplementary_reranker.py:594: in test_indexer_video_transcript_mapped_to_canonical
    16	    assert get_type_weight("video_transcript") == 0.9
    17	E   AssertionError: assert 0.75 == 0.9
    18	E    +  where 0.75 = <function get_type_weight at 0x1387577f0>('video_transcript')
    19	__________ TestFilterFloor.test_floor_triggered_marks_first_material ___________
    20	tests/unit/test_supplementary_reranker.py:653: in test_floor_triggered_marks_first_material
    21	    assert result[0].get("filter_floor_triggered") is True
    22	E   AssertionError: assert None is True
    23	E    +  where None = <built-in method get of dict object at 0x1389b6ac0>('filter_floor_triggered')
    24	E    +    where <built-in method get of dict object at 0x1389b6ac0> = {'hub_penalty': 0.0, 'query_overlap': 0.0, 'rerank_score': 0.5, 'score': 0.5, ...}.get
    25	______________ TestFilterFloor.test_min_keep_zero_disables_floor _______________
    26	tests/unit/test_supplementary_reranker.py:684: in test_min_keep_zero_disables_floor
    27	    assert len(result) == 0
    28	E   AssertionError: assert 5 == 0
    29	E    +  where 5 = len([{'hub_penalty': 0.0, 'query_overlap': 0.0, 'rerank_score': 0.5, 'score': 0.5, ...}, {'hub_penalty': 0.0, 'query_overl...nk_score': 0.5, 'score': 0.5, ...}, {'hub_penalty': 0.0, 'query_overlap': 0.0, 'rerank_score': 0.5, 'score': 0.5, ...}])
    30	__________ TestFilterFloor.test_floor_triggered_when_kill_ratio_high ___________
    31	tests/unit/test_supplementary_reranker.py:698: in test_floor_triggered_when_kill_ratio_high
    32	    assert result[0].get("filter_floor_triggered") is True
    33	E   AssertionError: assert None is True
    34	E    +  where None = <built-in method get of dict object at 0x13897e280>('filter_floor_triggered')
    35	E    +    where <built-in method get of dict object at 0x13897e280> = {'hub_penalty': 0.0, 'query_overlap': 0.0, 'rerank_score': 0.5, 'score': 0.5, ...}.get
    36	_______________ TestFilterFloor.test_floor_still_respects_top_k ________________
    37	tests/unit/test_supplementary_reranker.py:710: in test_floor_still_respects_top_k
    38	    assert result[0].get("filter_floor_triggered") is True
    39	E   AssertionError: assert None is True
    40	E    +  where None = <built-in method get of dict object at 0x1389a3f80>('filter_floor_triggered')
    41	E    +    where <built-in method get of dict object at 0x1389a3f80> = {'hub_penalty': 0.0, 'query_overlap': 0.0, 'rerank_score': 0.5, 'score': 0.5, ...}.get
    42	___ TestFilterFloorTaintExclusion.test_min_keep_floor_excludes_review_taint ____
    43	tests/unit/test_supplementary_reranker.py:752: in test_min_keep_floor_excludes_review_taint
    44	    assert len(result) == 2
    45	E   AssertionError: assert 3 == 2
    46	E    +  where 3 = len([{'hub_penalty': 0.0, 'query_overlap': 0.0, 'rerank_score': 0.5, 'score': 0.5, ...}, {'hub_penalty': 0.0, 'query_overl... 0.5, 'score': 0.5, ...}, {'hub_penalty': 0.0, 'injection_risk': 0.55, 'query_overlap': 0.0, 'rerank_score': 0.5, ...}])
    47	___ TestFilterFloorTaintExclusion.test_floor_no_taint_field_treated_as_clean ___
    48	tests/unit/test_supplementary_reranker.py:795: in test_floor_no_taint_field_treated_as_clean
    49	    assert result[0].get("filter_floor_triggered") is True
    50	E   AssertionError: assert None is True
    51	E    +  where None = <built-in method get of dict object at 0x13898b440>('filter_floor_triggered')
    52	E    +    where <built-in method get of dict object at 0x13898b440> = {'hub_penalty': 0.0, 'query_overlap': 0.0, 'rerank_score': 0.5, 'score': 0.5, ...}.get
    53	____ TestFilterFloorTaintExclusion.test_floor_all_review_returns_empty_list ____
    54	tests/unit/test_supplementary_reranker.py:813: in test_floor_all_review_returns_empty_list
    55	    assert len(result) == 0
    56	E   AssertionError: assert 5 == 0
    57	E    +  where 5 = len([{'hub_penalty': 0.0, 'injection_risk': 0.6, 'query_overlap': 0.0, 'rerank_score': 0.5, ...}, {'hub_penalty': 0.0, 'in...'rerank_score': 0.5, ...}, {'hub_penalty': 0.0, 'injection_risk': 0.6, 'query_overlap': 0.0, 'rerank_score': 0.5, ...}])
    58	=============================== warnings summary ===============================
    59	.venv/lib/python3.14/site-packages/google/genai/types.py:43
    60	  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/.venv/lib/python3.14/site-packages/google/genai/types.py:43: DeprecationWarning: '_UnionGenericAlias' is deprecated and slated for removal in Python 3.17
    61	    VersionedUnionType = Union[builtin_types.UnionType, _UnionGenericAlias]
    62	
    63	.venv/lib/python3.14/site-packages/langchain_core/_api/deprecation.py:25
    64	  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/.venv/lib/python3.14/site-packages/langchain_core/_api/deprecation.py:25: UserWarning: Core Pydantic V1 functionality isn't compatible with Python 3.14 or greater.
    65	    from pydantic.v1.fields import FieldInfo as FieldInfoV1
    66	
    67	.venv/lib/python3.14/site-packages/graphiti_core/driver/search_interface/search_interface.py:22
    68	  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/.venv/lib/python3.14/site-packages/graphiti_core/driver/search_interface/search_interface.py:22: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    69	    class SearchInterface(BaseModel):
    70	
    71	.venv/lib/python3.14/site-packages/jieba/_compat.py:18
    72	  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/.venv/lib/python3.14/site-packages/jieba/_compat.py:18: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
    73	    import pkg_resources
    74	
    75	<frozen importlib._bootstrap>:491
    76	  <frozen importlib._bootstrap>:491: DeprecationWarning: builtin type SwigPyPacked has no __module__ attribute
    77	
    78	<frozen importlib._bootstrap>:491
    79	  <frozen importlib._bootstrap>:491: DeprecationWarning: builtin type SwigPyObject has no __module__ attribute
    80	
    81	app/api/v1/endpoints/chat.py:803
    82	  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/app/api/v1/endpoints/chat.py:803: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    83	    class HookEnrichRequest(BaseModel):
    84	
    85	app/api/v1/endpoints/metadata.py:147
    86	  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/app/api/v1/endpoints/metadata.py:147: FastAPIDeprecationWarning: `example` has been deprecated, please use `examples` instead
    87	    canvas_path: str = Query(
    88	
    89	app/api/v1/endpoints/metadata.py:218
    90	  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/app/api/v1/endpoints/metadata.py:218: FastAPIDeprecationWarning: `example` has been deprecated, please use `examples` instead
    91	    canvas_path: str = Query(..., description="Canvas file path", example="Math 54/离散数学.canvas"),
    92	
    93	.venv/lib/python3.14/site-packages/pydantic/_internal/_generate_schema.py:2356
    94	  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/.venv/lib/python3.14/site-packages/pydantic/_internal/_generate_schema.py:2356: PydanticDeprecatedSince211: The `__get_pydantic_core_schema__` method of the `BaseModel` class is deprecated. If you are calling `super().__get_pydantic_core_schema__` when overriding the method on a Pydantic model, consider using `handler(source)` instead. However, note that overriding this method on models can lead to unexpected side effects. Deprecated in Pydantic V2.11 to be removed in V3.0.
    95	    schema = annotation_get_schema(source, get_inner_schema)
    96	
    97	-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
    98	=========================== short test summary info ============================
    99	FAILED tests/unit/test_supplementary_reranker.py::TestTypeWeightsIndexerTransition::test_indexer_note_mapped_to_canonical
   100	FAILED tests/unit/test_supplementary_reranker.py::TestTypeWeightsIndexerTransition::test_indexer_video_transcript_mapped_to_canonical
   101	FAILED tests/unit/test_supplementary_reranker.py::TestFilterFloor::test_floor_triggered_marks_first_material
   102	FAILED tests/unit/test_supplementary_reranker.py::TestFilterFloor::test_min_keep_zero_disables_floor
   103	FAILED tests/unit/test_supplementary_reranker.py::TestFilterFloor::test_floor_triggered_when_kill_ratio_high
   104	FAILED tests/unit/test_supplementary_reranker.py::TestFilterFloor::test_floor_still_respects_top_k
   105	FAILED tests/unit/test_supplementary_reranker.py::TestFilterFloorTaintExclusion::test_min_keep_floor_excludes_review_taint
   106	FAILED tests/unit/test_supplementary_reranker.py::TestFilterFloorTaintExclusion::test_floor_no_taint_field_treated_as_clean
   107	FAILED tests/unit/test_supplementary_reranker.py::TestFilterFloorTaintExclusion::test_floor_all_review_returns_empty_list
   108	================== 9 failed, 102 passed, 10 warnings in 0.45s ==================
   109	exit_code=1
     1	FAILED tests/unit/test_supplementary_reranker.py::TestTypeWeightsIndexerTransition::test_indexer_note_mapped_to_canonical
     2	FAILED tests/unit/test_supplementary_reranker.py::TestTypeWeightsIndexerTransition::test_indexer_video_transcript_mapped_to_canonical
     3	FAILED tests/unit/test_supplementary_reranker.py::TestFilterFloor::test_floor_triggered_marks_first_material
     4	FAILED tests/unit/test_supplementary_reranker.py::TestFilterFloor::test_min_keep_zero_disables_floor
     5	FAILED tests/unit/test_supplementary_reranker.py::TestFilterFloor::test_floor_triggered_when_kill_ratio_high
     6	FAILED tests/unit/test_supplementary_reranker.py::TestFilterFloor::test_floor_still_respects_top_k
     7	FAILED tests/unit/test_supplementary_reranker.py::TestFilterFloorTaintExclusion::test_min_keep_floor_excludes_review_taint
     8	FAILED tests/unit/test_supplementary_reranker.py::TestFilterFloorTaintExclusion::test_floor_no_taint_field_treated_as_clean
     9	FAILED tests/unit/test_supplementary_reranker.py::TestFilterFloorTaintExclusion::test_floor_all_review_returns_empty_list
    10	================== 9 failed, 102 passed, 10 warnings in 0.47s ==================
     1	FAILED tests/unit/test_supplementary_reranker.py::TestTypeWeightsIndexerTransition::test_indexer_note_mapped_to_canonical
     2	FAILED tests/unit/test_supplementary_reranker.py::TestTypeWeightsIndexerTransition::test_indexer_video_transcript_mapped_to_canonical
     3	FAILED tests/unit/test_supplementary_reranker.py::TestFilterFloor::test_floor_triggered_marks_first_material
     4	FAILED tests/unit/test_supplementary_reranker.py::TestFilterFloor::test_min_keep_zero_disables_floor
     5	FAILED tests/unit/test_supplementary_reranker.py::TestFilterFloor::test_floor_triggered_when_kill_ratio_high
     6	FAILED tests/unit/test_supplementary_reranker.py::TestFilterFloor::test_floor_still_respects_top_k
     7	FAILED tests/unit/test_supplementary_reranker.py::TestFilterFloorTaintExclusion::test_min_keep_floor_excludes_review_taint
     8	FAILED tests/unit/test_supplementary_reranker.py::TestFilterFloorTaintExclusion::test_floor_no_taint_field_treated_as_clean
     9	FAILED tests/unit/test_supplementary_reranker.py::TestFilterFloorTaintExclusion::test_floor_all_review_returns_empty_list
    10	================== 9 failed, 102 passed, 10 warnings in 0.53s ==================
     1	== doc_type 取值分布与字面量证据（round-3 整改：命令可执行、无占位符、绑定 pinned SHA）==
     2	锚定 SHA: 37387a86 | 生成于 2026-08-28
     3	
     4	--- ① live LanceDB 分布（容器内只读，命令完整可复跑）:
     5	docker exec canvas-learning-system-backend python3 -c "import lancedb, collections; db = lancedb.connect('/lancedb'); tbl = db.open_table('canvas_vault_vault_notes'); df = tbl.to_pandas(); print('rows:', len(df)); print(dict(sorted(collections.Counter(df['doc_type'].fillna('<null>').tolist()).items(), key=lambda x: -x[1])))"
     6	
     7	结果（2026-08-28 实测）:
     8	rows: 2203
     9	doc_type distribution: {'video_transcript': 2001, 'concept': 117, 'note': 69, 'whiteboard': 16}
    10	
    11	--- ② 字面量启发式扫描（pinned 到 37387a86，不受工作区/.venv 影响）:
    12	git grep -h "doc_type" 37387a86 -- "backend/app/*.py" "backend/lib/*.py" | grep -oE "[\"'][a-z_]+[\"']" | sort | uniq -c | sort -rn
    13	
    14	⚠️ 口径声明（round-2/round-3 整改）: ② 是**启发式辅助视图**，输出含 "doc_type"/"file_path"
    15	等字段名假阳性，**不是取值字面量全集的权威证据**。六值全集的权威依据 =
    16	报告 §1/§4 的逐点人工裁定 + pinned 146 行清单（doc_type-146-occurrences@37387a86.txt）。
    17	
    18	结果（本文件生成时实跑，见下）:
    19	  16 "doc_type"
    20	  10 "whiteboard"
    21	  10 "exam_board"
    22	   8 "note"
    23	   5 'doc_type'
    24	   2 "video_transcript"
    25	   1 "type"
    26	   1 "tags_str"
    27	   1 "file_path"
    28	   1 "course"
    29	   1 "concept"
    30	   1 'whiteboard'
    31	   1 'note'

**Verifying baseline and full summary differences**
**Confirming pytest traceback configuration**
exec
/bin/zsh -lc "nl -ba backend/pytest.ini | sed -n '1,120p'; git show 73102875:backend/pytest.ini | shasum -a 256; shasum -a 256 backend/pytest.ini; git diff --quiet 73102875..HEAD -- backend/pytest.ini backend/tests/unit/test_supplementary_reranker.py backend/tests/unit/test_supplementary_search_service.py backend/tests/conftest.py backend/conftest.py; echo replay_support_diff_731_head_exit="'$?' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
     1	[pytest]
     2	# Canvas Learning System - pytest Configuration
     3	# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: testing)
     4	# [Source: docs/architecture/coding-standards.md#测试规范]
     5	# [Source: ADR-008 - Testing Framework pytest]
     6	
     7	# Test file patterns
     8	testpaths = tests
     9	python_files = test_*.py
    10	python_classes = Test*
    11	python_functions = test_*
    12	
    13	# asyncio mode for async tests
    14	asyncio_mode = auto
    15	
    16	# Output verbosity (coverage moved to scripts/coverage-check.sh, not in default addopts)
    17	# Reason: --cov-fail-under=85 caused every pytest invocation (including hooks) to fail
    18	# at 23.4% actual coverage. Run coverage separately: pytest --cov=app --cov-fail-under=30
    19	addopts =
    20	    -v
    21	    --tb=short
    22	
    23	# Parallel testing with pytest-xdist (use -n auto for automatic CPU detection)
    24	# Run with: pytest -n auto
    25	# Note: Not enabled by default to avoid issues with shared fixtures
    26	
    27	# Markers
    28	# [Source: docs/stories/33.8.story.md - Task 8.3]
    29	markers =
    30	    smoke: fast boot/health verification (< 5s, PostToolUse Tier 1)
    31	    slow: marks tests as slow (deselect with '-m "not slow"')
    32	    integration: marks tests as integration tests
    33	    contract: marks tests as contract/schema tests
    34	    e2e: marks tests as end-to-end tests (Story 33.8)
    35	    performance: marks tests as performance benchmarks (Story 33.8)
    36	    websocket: marks tests requiring WebSocket connections (Story 33.8)
    37	    p0: marks P0 blocker tests (core functionality)
    38	    p1: marks P1 high priority tests
    39	    bdd: behavior-driven development tests (pytest-bdd)
    40	    p2: marks P2 medium priority tests
    41	    real_neo4j: marks tests that need the dedicated Neo4j test container (port 7692)
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
33b694bfd90d6d870374b495625e6d372732dd748f57ae1ffd887ba9a0676514  -
33b694bfd90d6d870374b495625e6d372732dd748f57ae1ffd887ba9a0676514  backend/pytest.ini
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
replay_support_diff_731_head_exit=0

**Calculating failed node sets without grep**
exec
/bin/zsh -lc 'for f in _bmad-output/审查/G4-16-evidence/pytest-before-full-stdout.txt _bmad-output/审查/G4-16-evidence/pytest-after-full-stdout.txt _bmad-output/审查/G4-16-evidence/baseline-before-edits.txt _bmad-output/审查/G4-16-evidence/after-edits.txt; do echo "$f"; sed -n '"'s/"'^FAILED //p'"' \""'$f" | sed '"'s/[[:space:]].*"'$//'"' | wc -l; sed -n 's/"'^FAILED //p'"' \""'$f" | sed '"'s/[[:space:]].*"'$//'"' | shasum -a 256; done" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
_bmad-output/审查/G4-16-evidence/pytest-before-full-stdout.txt
       9
26fb79e02d4e069b5eddf3150f70e143d65d926dbabbcb59d88cbf2935928268  -
_bmad-output/审查/G4-16-evidence/pytest-after-full-stdout.txt
       9
26fb79e02d4e069b5eddf3150f70e143d65d926dbabbcb59d88cbf2935928268  -
_bmad-output/审查/G4-16-evidence/baseline-before-edits.txt
       9
26fb79e02d4e069b5eddf3150f70e143d65d926dbabbcb59d88cbf2935928268  -
_bmad-output/审查/G4-16-evidence/after-edits.txt
       9
26fb79e02d4e069b5eddf3150f70e143d65d926dbabbcb59d88cbf2935928268  -

**Assessing test run side effects**
**Verifying git checkout and pyc handling**
exec
/bin/zsh -lc 'test -d /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census; echo root_dir_exit=$?; test -x backend/.venv/bin/pytest; echo pytest_executable_exit=$?; backend/.venv/bin/python --version; git cat-file -e 37387a86''^{commit}; echo base_commit_exit=$?; git cat-file -e 73102875''^{commit}; echo after_commit_exit=$?' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
root_dir_exit=0
pytest_executable_exit=0
Python 3.14.4
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
base_commit_exit=0
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
after_commit_exit=0

**Verifying commit 94 presence and report file consistency**
exec
/bin/zsh -lc 'git diff --name-status 94b420ff..HEAD -- _bmad-output/审查/G4-16-doc-type-census-2026-08-28.md _bmad-output/审查/G4-16-evidence; git log --oneline 94b420ff..HEAD -- _bmad-output/审查/G4-16-doc-type-census-2026-08-28.md _bmad-output/审查/G4-16-evidence' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead

**Verifying file format disclosure**
**Assessing final low severity acceptance**
**Confirming live file unchanged formatting**
**Verifying command output consistency**
**Evaluating Docker command impact and code accuracy**
**Confirming stable codebase alignment**
**Verifying pytest output behavior**
**Confirming codebase consistency and readiness**
**Waiting for agent replay response**
codex
目前关键复算均指向闭合：四条 recipe 的 `zsh -n` 都为 0；命令③在沙箱外按字面只读执行 `diff` 为 0；两个目标文件在 `73102875`、`fce0d8a2`、`94b420ff` 与当前 HEAD 的 blob 均各自不变。两份 stdout 的原始差异也已逐块检查，只有 9 处对象地址和耗时。仍在收口两个措辞级细节：`73579b22` 只属于 reranker（search 是 `5ff33104`），以及 live 文件对“格式化展示”的声明是否足够明确；它们目前都不像验收阻断。
**Gathering exact line citations**
exec
/bin/zsh -lc "nl -ba /Users/Heishing/.codex/memories/MEMORY.md | sed -n '176,188p'; nl -ba /Users/Heishing/.codex/memories/skills/canvas-adversarial-audit/SKILL.md | sed -n '1,50p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
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

**Verifying rollout ID inclusion and memory references**
**Confirming local memory sufficiency for audit**
**Clarifying audit scope and command effects**
**Confirming static review and restore precondition**
**Planning final stdout agent**
collab: Wait
**Preparing finalization message**
**Verifying clean git status and unchanged files**
exec
/bin/zsh -lc 'git status --short --branch; git diff --quiet; echo tracked_diff_exit=$?; git diff --cached --quiet; echo index_diff_exit=$?; for p in backend/app/services/supplementary_reranker.py backend/app/services/supplementary_search_service.py; do echo "$p"; git hash-object "$p"; git rev-parse HEAD:"$p"; done' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
## card/s5-census
?? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-16-round5.md"
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
tracked_diff_exit=0
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
index_diff_exit=0
backend/app/services/supplementary_reranker.py
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
73579b22f7a54bc1b3bc4e4e4230c6eadb235b56
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
73579b22f7a54bc1b3bc4e4e4230c6eadb235b56
backend/app/services/supplementary_search_service.py
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
5ff331040905dda9c8a7c46fc329bc1af56acea4
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
5ff331040905dda9c8a7c46fc329bc1af56acea4

**Planning final verification approach**
**Evaluating command execution semantics**
**Assessing commit consistency and command effects**
**Verifying backend source and test changes**
**Confirming test output consistency and metadata**
**Identifying labeling inconsistency risk**
**Verifying heuristic annotation accuracy**
**Clarifying low issue acceptance criteria**
**Updating test label to reproduction pair**
**Verifying live data consistency**
**Assessing live data verification constraints**
**Confirming report scope and limits**
**Confirming command execution status**
四条证据轨与主审交叉复算完成；MEDIUM-5 已闭合，铁律与 pinned census 均通过，仅余两个不阻断的措辞 LOW。
  ✓ 固定 checkout、提交对象、审计边界与证据文件清单
  ✓ 复核四条 replay recipe 的 zsh 语法、语义与固定 SHA 绑定
  ✓ 复核 stdout、metadata、归一化差异与失败节点集合
  ✓ 复核注释-only、AST、隔离面和 18 文件 146 行 census/六取值
  ✓ 交叉核验所有结论并给出唯一终裁
**Planning detailed audit report structure**
**Summarizing audit evidence with exact findings**
**Clarifying inclusion of low-level caveats**
**Deciding acceptance criteria for low findings**
**Noting graphiti-canvas unavailability and citing skills**
**Confirming citation strategy and file references**
**Refining final audit report formatting and content**
**Clarifying replay execution terminology**
**Confirming no Graphiti claims used**
**Planning exact Chinese phrase usage**
codex
最终裁定：**CARD-G4-16 可验收**。唯一阻断项 MEDIUM-5 已 CLOSED，无必须再做项。

- (a) **PASS**：四条命令 [metadata:15/18/21/24](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-evidence/test-run-metadata.txt:15) 的 `zsh -n` 均为 0，无占位符；③按字面只读执行，`diff` exit 0。
- (b) **PASS**：`73102875..fce0d8a2`、`73102875..HEAD` 对两目标文件均零差异。稳定 blob 分别为 reranker `73579b22…`、search `5ff33104…`。
- (c) **PASS**：两份 stdout 各 109 行、9957 bytes，均为 111 collected、9 failed/102 passed、exit 1；失败节点集合完全相同。原始差异仅 9 处对象地址及 `0.47s→0.45s`；归一化后均为 9912 bytes、SHA-256 `03e57607…84e8`。`--tb=short` 声明与 [pytest.ini:19](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/pytest.ini:19) 一致。
- (d) **PASS**：`37387a86..HEAD` 仅改注释；两个文件无属性 AST SHA 分别保持 `18aae6e0…`、`03e79eea…`。`whiteboard/exam_board` 排除链、Tier-2 边界及 SQL `NOT IN` 均无行为变化。
- (e) **PASS**：pinned `git grep` 独立得到 18 文件/146 行，与证据逐字节相同，SHA-256 `94b01dc3…`；[报告六类裁定](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-doc-type-census-2026-08-28.md:48) 与 `37387a86` 代码一致。当前 HEAD 因新增注释为 18/148，但报告明确绑定基线，因此不构成漂移。

仅余两个非阻断 LOW：metadata 第 7 行的单数 blob 措辞不精确；[live 文件:14](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-evidence/live-distribution-and-value-grep.txt:14) 已声明②为启发式，但未明确写出“结果经过格式化”。二者均不影响权威证据或验收。

遵守只读边界：未执行会写入的①②④，未修改 tracked/index；既存未跟踪 round-5 文件未触碰。`graphiti-canvas` 本会话未暴露，裁定未依赖 Graphiti 自述。


tokens used
201,393
最终裁定：**CARD-G4-16 可验收**。唯一阻断项 MEDIUM-5 已 CLOSED，无必须再做项。

- (a) **PASS**：四条命令 [metadata:15/18/21/24](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-evidence/test-run-metadata.txt:15) 的 `zsh -n` 均为 0，无占位符；③按字面只读执行，`diff` exit 0。
- (b) **PASS**：`73102875..fce0d8a2`、`73102875..HEAD` 对两目标文件均零差异。稳定 blob 分别为 reranker `73579b22…`、search `5ff33104…`。
- (c) **PASS**：两份 stdout 各 109 行、9957 bytes，均为 111 collected、9 failed/102 passed、exit 1；失败节点集合完全相同。原始差异仅 9 处对象地址及 `0.47s→0.45s`；归一化后均为 9912 bytes、SHA-256 `03e57607…84e8`。`--tb=short` 声明与 [pytest.ini:19](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/pytest.ini:19) 一致。
- (d) **PASS**：`37387a86..HEAD` 仅改注释；两个文件无属性 AST SHA 分别保持 `18aae6e0…`、`03e79eea…`。`whiteboard/exam_board` 排除链、Tier-2 边界及 SQL `NOT IN` 均无行为变化。
- (e) **PASS**：pinned `git grep` 独立得到 18 文件/146 行，与证据逐字节相同，SHA-256 `94b01dc3…`；[报告六类裁定](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-doc-type-census-2026-08-28.md:48) 与 `37387a86` 代码一致。当前 HEAD 因新增注释为 18/148，但报告明确绑定基线，因此不构成漂移。

仅余两个非阻断 LOW：metadata 第 7 行的单数 blob 措辞不精确；[live 文件:14](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-evidence/live-distribution-and-value-grep.txt:14) 已声明②为启发式，但未明确写出“结果经过格式化”。二者均不影响权威证据或验收。

遵守只读边界：未执行会写入的①②④，未修改 tracked/index；既存未跟踪 round-5 文件未触碰。`graphiti-canvas` 本会话未暴露，裁定未依赖 Graphiti 自述。


