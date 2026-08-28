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
session id: 01a048e0-2dd6-73f0-b7ea-3a65e8a80c89
--------
user
CARD-G4-9 round-13 终裁确认（静态审阅 + 只读复算，禁改任何文件）。你 round-12 给出三层裁定：(a) 92 条冻结 ledger PASS 可验收；(b) 生成器在已声明有界前提下 PASS 可验收；可绑定证据 PASS；仅 (c) 报告与 UAT 声明 FAIL，并明确『无需再改测试、脚本或重生成当前绑定证据』，只列两条必须再做：

1. 报告第 92 行与 UAT 第 13、27、134 行的『0 写入 / 逐次取证 / 输入零改动 / 运行零写入已过关』→ 统一改为『本次留存的 before/after 样本字节或 SHA 相同；不证明读取期间零写入，也不证明每轮均留存证据』。
2. UAT 第 49 行『五项绕过整类失效』→ 改为『「截断某个既有对象」这一具体路径不再存在；不代表所有别名类绕过均已失效』。

开发方以 commit 543e8a34 完成两条（另在报告新增 §7n 记录本轮裁定与整改；判据名由『全程零写入/输入零改动』改为『输入前后终态一致』；UAT 结论段的『运行零写入』亦改为『输入前后终态字节一致』）。

请：
- grep 复核报告与 UAT 中是否仍存在**非引述性**的过强断言（0 写入 / 运行零写入 / 逐次取证 / 每轮取证 / 整类绕过失效 / 所有误用路径 fail-closed / DB 静止当结论）。引述 Codex 历史裁定或整改记录中复述旧措辞的句子不算残留，请区分。
- 确认脚本、测试与绑定证据在 543e8a34 相对 f4112c2c **未被改动**（应仅文档变更）。
- 复核台账仍为 92 条 / class 89-2-1 / byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0 / 重复簇 6/29 / unparseable 0 / attribution_conflict 3(no_token)。

给出**最终裁定**：三层（(a) ledger、(b) 有界前提下的生成器、(c) 报告与 UAT 声明）是否均可验收。若均 PASS，请明确写出『CARD-G4-9 可验收』；若仍阻断，只列必须再做项（不含已移交的 FU-A~FU-D）。
2026-08-28T14:57:28.146278Z ERROR codex_memories_write::phase2: Phase 2 no changes
**Planning audit with memory and tools**
**Inspecting memory-backed adversarial audit skill**
**Verifying commit state and diffs**
codex
我会按只读终裁做三条独立复核：措辞残留、`f4112c2c..543e8a34` 变更边界、92 条台账复算。先读取该项目既有的对抗审计约束与当前 Git 状态，再并行交叉验证；全程不改文件。
  → 读取既有审计约束并确认 checkout、提交与审阅对象
  • 并行复核报告/UAT 过强断言与提交变更边界
  • 从绑定证据只读复算台账全部统计量
  • 交叉核对差异并给出三层最终裁定
**Planning concurrent MEMORY search**
exec
/bin/zsh -lc 'rg -n -i "CARD-G4-9|round-12|card-s5-census|adversarial audit|canvas-adversarial-audit|92 条|92条" /Users/Heishing/.codex/memories/MEMORY.md' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
5:## Task 1: Full-project adversarial audit and productivity direction, partial
169:## Task 2: P1-05b five-question adversarial audit, reproducible bypasses
186:- Related skill: skills/canvas-adversarial-audit/SKILL.md. P1-05/P1-01/P1-08 remained STILL-OPEN; F-02 tombstone filtering and F-05 live resilience were closed. Rejected vault inputs must show zero open/hash/index/write. [Task 1][Task 2]

**Verifying memory and skill usage**
codex
既有记忆索引指向 `canvas-adversarial-audit` 审计流程；我会用它约束证据格式与 fail-closed 判定，并先由主审完整读取该流程。当前会话没有暴露 `graphiti-canvas`，因此无法执行仓库说明里的每轮 Graphiti 查询；这不会替代任何本地证据复算。
exec
/bin/zsh -lc "nl -ba /Users/Heishing/.codex/memories/MEMORY.md | sed -n '155,195p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
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
   189	
   190	## Failures and how to do differently
   191	
   192	- Green tests hitting source text, helpers, fake clients, `__new__`, or monkeypatches are not closure; pivot to production entrypoints and full stdout/trace. Test `search_nodes`, `read_node_tips`, `read_node_errors`, and `read_node_edge_reasons`. [Task 1][Task 2]
   193	- P1-05b did not finish its Q1–Q5 matrix. Collect conclusions first, then deliver per-question findings, P1-05/P1-01/P1-08 comparison, and explicit limits. [Task 2]
   194	
   195	# Task Group: Canvas Learning System repository contributor guide

exec
/bin/zsh -lc 'wc -l /Users/Heishing/.codex/memories/skills/canvas-adversarial-audit/SKILL.md && nl -ba /Users/Heishing/.codex/memories/skills/canvas-adversarial-audit/SKILL.md' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
      50 /Users/Heishing/.codex/memories/skills/canvas-adversarial-audit/SKILL.md
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

**Consolidating memory and skill citations**
mcp: sequential-thinking/sequentialthinking started
mcp: sequential-thinking/sequentialthinking (completed)
**Identifying key files and repo state**
**Executing parallel repo inspection commands**
exec
/bin/zsh -lc 'rg --files -g AGENTS.md -g CURRENT_TASK.md -g *card*g4* -g *CARD*G4* -g *uat* -g *UAT* -g *census* -g *ledger*' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 exited 1 in 0ms:
zsh:1: no matches found: *card*g4*

exec
/bin/zsh -lc 'git show --no-renames --format=fuller --stat 543e8a34' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
commit 543e8a34039ac2737fc4a445f6d45c432db8112e
Author:     oinani0721 <2272104243@qq.com>
AuthorDate: Fri Aug 28 22:57:00 2026 +0800
Commit:     oinani0721 <2272104243@qq.com>
CommitDate: Fri Aug 28 22:57:00 2026 +0800

    docs(census): G4-9 round-12 最后两条措辞整改 [BATCH-2026-08-28-第五批 / CARD-G4-9]
    
    round-12 三层裁定: (a) 92 条冻结 ledger PASS 可验收; (b) 生成器在已声明有界
    前提下 PASS 可验收; 可绑定证据 PASS; 仅 (c) 报告/UAT 声明 FAIL。
    Codex 明示无需再改测试/脚本/证据, 只剩两条措辞:
    1. "0 写入 / 逐次取证 / 输入零改动 / 运行零写入已过关"统一改为"本次留存的
       before/after 样本 SHA 相同; 只证明前后终态字节一致, 不证明读取期间零写入,
       也不证明每轮均留存独立证据"。判据名改为"输入前后终态一致"。
    2. "五项绕过整类失效"改为"『截断某个既有对象』这一具体路径不再存在,
       不代表所有别名类绕过均已失效(lstat→replace 竞态见 FU-B/FU-C)"。
    两条共同点与前十一轮一致: 证据支持的是"前后终态一致"与"某条具体路径消失",
    措辞却写成了"零写入"与"整类失效"。改措辞不改结论 — 台账数字与脚本行为未动。
    本轮无脚本改动, f4112c2c 的 ledger 即最终版: 92/4-88-0-0/89-2-1/6-29。
    
    Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>

 .../G4-9-DLQ-census-2026-08-28.md"                 |   22 +-
 .../codex-review-CARD-G4-9-round12.md"             | 2964 ++++++++++++++++++++
 ...75census\345\210\206\350\257\212-2026-08-28.md" |   10 +-
 3 files changed, 2991 insertions(+), 5 deletions(-)

exec
/bin/zsh -lc 'git rev-parse HEAD "f4112c2c''^{commit}" "543e8a34''^{commit}"' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
9104495b42b305ff726b3cc41b9bb446d2e4e89b
f4112c2ca5e800eda5944d9ad0e6e6bfb0d60ce9
543e8a34039ac2737fc4a445f6d45c432db8112e

exec
/bin/zsh -lc 'git diff --name-status f4112c2c 543e8a34' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
M	"_bmad-output/\345\256\241\346\237\245/G4-9-DLQ-census-2026-08-28.md"
M	"_bmad-output/\345\256\241\346\237\245/G4-9-evidence/artifact-commit-receipt.txt"
A	"_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round12.md"
M	"_bmad-output/\351\252\214\346\224\266\345\215\225/UAT-CARD-G4-9-DLQ\347\234\237\345\256\236\346\214\202\350\275\275census\345\210\206\350\257\212-2026-08-28.md"

exec
/bin/zsh -lc 'git status --short --branch' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
## card/s5-census
?? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G4-9-round13.md"

**Inspecting artifact-commit-receipt changes**
**Analyzing commit 543 and ancestry for evidence**
**Clarifying file count discrepancy in diff stat**
**Inspecting git diff and path encoding**
**Planning multi-agent task spawning with git context**
codex
初步锚定发现两个需要特别核清的点：当前 `HEAD` 是 `9104495b`，不是待裁提交 `543e8a34`；工作树另有一个未跟踪的 round-13 文件。我会完全忽略该未跟踪文件，并直接从 Git 对象读取 `543e8a34`。此外，提交名录显示除报告/UAT外还触及 `G4-9-evidence/artifact-commit-receipt.txt`，需判定它是否属于“绑定证据”及是否只是收据元数据；不能先验地把它当作“仅文档”。
**Locating AGENTS and CURRENT_TASK files**
exec
/bin/zsh -lc 'git -c core.quotePath=false diff --name-status --no-renames f4112c2c 543e8a34' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
M	_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md
M	_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt
A	_bmad-output/审查/codex-review-CARD-G4-9-round12.md
M	_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md

exec
/bin/zsh -lc 'git -c core.quotePath=false diff --numstat --no-renames f4112c2c 543e8a34' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
21	1	_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md
2	1	_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt
2964	0	_bmad-output/审查/codex-review-CARD-G4-9-round12.md
6	4	_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md

exec
/bin/zsh -lc 'git -c core.quotePath=false diff --raw --no-renames f4112c2c 543e8a34' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
:100644 100644 9eaa362f dfe6d5ed M	_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md
:100644 100644 9be8b423 a71e2031 M	_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt
:000000 100644 00000000 170ad9ab A	_bmad-output/审查/codex-review-CARD-G4-9-round12.md
:100644 100644 eece19dc 266b415d M	_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md

exec
/bin/zsh -lc 'git cat-file -p 543e8a34' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
tree d4cb6dc3cc539ca898d761fe48a350dc61db1e85
parent 05c85324656eb7eab2b0d1f51bfe48d22a8dd88c
author oinani0721 <2272104243@qq.com> 1787929020 +0800
committer oinani0721 <2272104243@qq.com> 1787929020 +0800

docs(census): G4-9 round-12 最后两条措辞整改 [BATCH-2026-08-28-第五批 / CARD-G4-9]

round-12 三层裁定: (a) 92 条冻结 ledger PASS 可验收; (b) 生成器在已声明有界
前提下 PASS 可验收; 可绑定证据 PASS; 仅 (c) 报告/UAT 声明 FAIL。
Codex 明示无需再改测试/脚本/证据, 只剩两条措辞:
1. "0 写入 / 逐次取证 / 输入零改动 / 运行零写入已过关"统一改为"本次留存的
   before/after 样本 SHA 相同; 只证明前后终态字节一致, 不证明读取期间零写入,
   也不证明每轮均留存独立证据"。判据名改为"输入前后终态一致"。
2. "五项绕过整类失效"改为"『截断某个既有对象』这一具体路径不再存在,
   不代表所有别名类绕过均已失效(lstat→replace 竞态见 FU-B/FU-C)"。
两条共同点与前十一轮一致: 证据支持的是"前后终态一致"与"某条具体路径消失",
措辞却写成了"零写入"与"整类失效"。改措辞不改结论 — 台账数字与脚本行为未动。
本轮无脚本改动, f4112c2c 的 ledger 即最终版: 92/4-88-0-0/89-2-1/6-29。

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>

exec
/bin/zsh -lc "rg --files -g 'AGENTS.md' -g 'CURRENT_TASK.md' -g 'CLAUDE.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
CLAUDE.md
CURRENT_TASK.md
canvas-vault/CLAUDE.md
_decisions/CURRENT_TASK.md

exec
/bin/zsh -lc "git -c core.quotePath=false ls-tree -r --name-only 543e8a34 | rg -i 'G4-9|census|ledger|manifest|evidence|uat|current_task|agents\\.md"'$'"'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
.bg-shell/manifest.json
CURRENT_TASK.md
_archive/canvas-progress-tracker/obsidian-plugin/manifest.json
_archive/obsidian-canvas-learning/manifest.json
_bmad-archive/code-archive/fusion/evaluator.py
_bmad-output/implementation-artifacts/archive/epic-2__2-9-rag-rerank-and-evidence.md
_bmad-output/implementation-artifacts/epic-2/2-2-and-2-9-merged-rerank-evidence.md
_bmad-output/review/epic-1-uat-guide-2026-04-17.md
_bmad-output/templates/uat-sheet-template.md
_bmad-output/templates/uat-sheet-template.v1.backup.md
_bmad-output/审查/2026-08-19-P1-05b-Graphiti污染盘点census报告.md
_bmad-output/审查/G4-16-doc-type-census-2026-08-28.md
_bmad-output/审查/G4-16-evidence/after-edits.txt
_bmad-output/审查/G4-16-evidence/baseline-before-edits.txt
_bmad-output/审查/G4-16-evidence/doc_type-146-occurrences@37387a86.txt
_bmad-output/审查/G4-16-evidence/live-distribution-and-value-grep.txt
_bmad-output/审查/G4-16-evidence/pytest-after-full-stdout.txt
_bmad-output/审查/G4-16-evidence/pytest-before-full-stdout.txt
_bmad-output/审查/G4-16-evidence/test-run-metadata.txt
_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md
_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json
_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt
_bmad-output/审查/G4-9-evidence/census-stderr.txt
_bmad-output/审查/G4-9-evidence/container-sha-check.txt
_bmad-output/审查/G4-9-evidence/grep-selfattest.txt
_bmad-output/审查/G4-9-evidence/readonly-contract-tests.txt
_bmad-output/审查/G4-9-evidence/shasums-after.txt
_bmad-output/审查/G4-9-evidence/shasums-before.txt
_bmad-output/审查/c5-evidence-2026-08-25/before.txt
_bmad-output/审查/c5-evidence-2026-08-25/check_report_sections.py
_bmad-output/审查/c5-evidence-2026-08-25/fwd-A-cs188.log
_bmad-output/审查/c5-evidence-2026-08-25/fwd-B-eigen.log
_bmad-output/审查/c5-evidence-2026-08-25/fwd-C-61b.log
_bmad-output/审查/c5-evidence-2026-08-25/fwd-D-idempotent.log
_bmad-output/审查/c5-evidence-2026-08-25/fwd-E-fakeboard.log
_bmad-output/审查/c5-evidence-2026-08-25/fwd-F-fallback.log
_bmad-output/审查/c5-evidence-2026-08-25/fwd2-A-cs188.log
_bmad-output/审查/c5-evidence-2026-08-25/fwd2-B-eigen.log
_bmad-output/审查/c5-evidence-2026-08-25/fwd2-C-61b.log
_bmad-output/审查/c5-evidence-2026-08-25/fwd2-F-fallback.log
_bmad-output/审查/c5-evidence-2026-08-25/fwd3-A-cs188.log
_bmad-output/审查/c5-evidence-2026-08-25/fwd3-B-eigen.log
_bmad-output/审查/c5-evidence-2026-08-25/fwd3-C-61b.log
_bmad-output/审查/c5-evidence-2026-08-25/fwd3-F-fallback.log
_bmad-output/审查/c5-evidence-2026-08-25/fwd4-A3-cs188.log
_bmad-output/审查/c5-evidence-2026-08-25/fwd4-B-eigen.log
_bmad-output/审查/c5-evidence-2026-08-25/fwd4-C-61b.log
_bmad-output/审查/c5-evidence-2026-08-25/fwd4-F-fallback.log
_bmad-output/审查/c5-evidence-2026-08-25/fwd5-F-fallback.log
_bmad-output/审查/c5-evidence-2026-08-25/shasum-final-ok-count.txt
_bmad-output/审查/codex-review-CARD-G4-9-round10.md
_bmad-output/审查/codex-review-CARD-G4-9-round11.md
_bmad-output/审查/codex-review-CARD-G4-9-round12.md
_bmad-output/审查/codex-review-CARD-G4-9-round2.md
_bmad-output/审查/codex-review-CARD-G4-9-round3.md
_bmad-output/审查/codex-review-CARD-G4-9-round4.md
_bmad-output/审查/codex-review-CARD-G4-9-round5.md
_bmad-output/审查/codex-review-CARD-G4-9-round6.md
_bmad-output/审查/codex-review-CARD-G4-9-round7.md
_bmad-output/审查/codex-review-CARD-G4-9-round8.md
_bmad-output/审查/codex-review-CARD-G4-9-round9.md
_bmad-output/审查/codex-review-CARD-G4-9.md
_bmad-output/审查/d5-evidence-2026-08-27/D5-结案报告.md
_bmad-output/审查/d5-evidence-2026-08-27/after-check.txt
_bmad-output/审查/d5-evidence-2026-08-27/before.txt
_bmad-output/审查/g1-5-red-green-evidence.txt
_bmad-output/审查/g5-1-evidence/README.md
_bmad-output/审查/g5-1-evidence/final-verdict.txt
_bmad-output/审查/g5-1-evidence/judge_headless_logs.py
_bmad-output/审查/g5-1-evidence/logs-v2-archive/N1.jsonl
_bmad-output/审查/g5-1-evidence/logs-v2-archive/N10.jsonl
_bmad-output/审查/g5-1-evidence/logs-v2-archive/N2.jsonl
_bmad-output/审查/g5-1-evidence/logs-v2-archive/N3.jsonl
_bmad-output/审查/g5-1-evidence/logs-v2-archive/N4.jsonl
_bmad-output/审查/g5-1-evidence/logs-v2-archive/N5.jsonl
_bmad-output/审查/g5-1-evidence/logs-v2-archive/N6.jsonl
_bmad-output/审查/g5-1-evidence/logs-v2-archive/N7.jsonl
_bmad-output/审查/g5-1-evidence/logs-v2-archive/N8.jsonl
_bmad-output/审查/g5-1-evidence/logs-v2-archive/N9.jsonl
_bmad-output/审查/g5-1-evidence/manifests/B1-after.txt
_bmad-output/审查/g5-1-evidence/manifests/B1-before.txt
_bmad-output/审查/g5-1-evidence/manifests/B1-content-diff.txt
_bmad-output/审查/g5-1-evidence/manifests/B1-outputs-after.txt
_bmad-output/审查/g5-1-evidence/manifests/B1-outputs-before.txt
_bmad-output/审查/g5-1-evidence/manifests/B2-after-attempt1.txt
_bmad-output/审查/g5-1-evidence/manifests/B2-after.txt
_bmad-output/审查/g5-1-evidence/manifests/B2-before-attempt1.txt
_bmad-output/审查/g5-1-evidence/manifests/B2-before.txt
_bmad-output/审查/g5-1-evidence/manifests/B2-content-diff.txt
_bmad-output/审查/g5-1-evidence/manifests/B2-outputs-after-attempt1.txt
_bmad-output/审查/g5-1-evidence/manifests/B2-outputs-after.txt
_bmad-output/审查/g5-1-evidence/manifests/B2-outputs-before-attempt1.txt
_bmad-output/审查/g5-1-evidence/manifests/B2-outputs-before.txt
_bmad-output/审查/g5-1-evidence/manifests/N1-after.txt
_bmad-output/审查/g5-1-evidence/manifests/N1-before.txt
_bmad-output/审查/g5-1-evidence/manifests/N1-meta.json
_bmad-output/审查/g5-1-evidence/manifests/N1-outputs-after.txt
_bmad-output/审查/g5-1-evidence/manifests/N1-outputs-before.txt
_bmad-output/审查/g5-1-evidence/manifests/N10-after.txt
_bmad-output/审查/g5-1-evidence/manifests/N10-before.txt
_bmad-output/审查/g5-1-evidence/manifests/N10-meta.json
_bmad-output/审查/g5-1-evidence/manifests/N10-outputs-after.txt
_bmad-output/审查/g5-1-evidence/manifests/N10-outputs-before.txt
_bmad-output/审查/g5-1-evidence/manifests/N2-after.txt
_bmad-output/审查/g5-1-evidence/manifests/N2-before.txt
_bmad-output/审查/g5-1-evidence/manifests/N2-meta.json
_bmad-output/审查/g5-1-evidence/manifests/N2-outputs-after.txt
_bmad-output/审查/g5-1-evidence/manifests/N2-outputs-before.txt
_bmad-output/审查/g5-1-evidence/manifests/N3-after.txt
_bmad-output/审查/g5-1-evidence/manifests/N3-before.txt
_bmad-output/审查/g5-1-evidence/manifests/N3-meta.json
_bmad-output/审查/g5-1-evidence/manifests/N3-outputs-after.txt
_bmad-output/审查/g5-1-evidence/manifests/N3-outputs-before.txt
_bmad-output/审查/g5-1-evidence/manifests/N4-after.txt
_bmad-output/审查/g5-1-evidence/manifests/N4-before.txt
_bmad-output/审查/g5-1-evidence/manifests/N4-meta.json
_bmad-output/审查/g5-1-evidence/manifests/N4-outputs-after.txt
_bmad-output/审查/g5-1-evidence/manifests/N4-outputs-before.txt
_bmad-output/审查/g5-1-evidence/manifests/N5-after.txt
_bmad-output/审查/g5-1-evidence/manifests/N5-before.txt
_bmad-output/审查/g5-1-evidence/manifests/N5-meta.json
_bmad-output/审查/g5-1-evidence/manifests/N5-outputs-after.txt
_bmad-output/审查/g5-1-evidence/manifests/N5-outputs-before.txt
_bmad-output/审查/g5-1-evidence/manifests/N6-after.txt
_bmad-output/审查/g5-1-evidence/manifests/N6-before.txt
_bmad-output/审查/g5-1-evidence/manifests/N6-meta.json
_bmad-output/审查/g5-1-evidence/manifests/N6-outputs-after.txt
_bmad-output/审查/g5-1-evidence/manifests/N6-outputs-before.txt
_bmad-output/审查/g5-1-evidence/manifests/N7-after.txt
_bmad-output/审查/g5-1-evidence/manifests/N7-before.txt
_bmad-output/审查/g5-1-evidence/manifests/N7-meta.json
_bmad-output/审查/g5-1-evidence/manifests/N7-outputs-after.txt
_bmad-output/审查/g5-1-evidence/manifests/N7-outputs-before.txt
_bmad-output/审查/g5-1-evidence/manifests/N8-after.txt
_bmad-output/审查/g5-1-evidence/manifests/N8-before.txt
_bmad-output/审查/g5-1-evidence/manifests/N8-meta.json
_bmad-output/审查/g5-1-evidence/manifests/N8-outputs-after.txt
_bmad-output/审查/g5-1-evidence/manifests/N8-outputs-before.txt
_bmad-output/审查/g5-1-evidence/manifests/N9-after.txt
_bmad-output/审查/g5-1-evidence/manifests/N9-before.txt
_bmad-output/审查/g5-1-evidence/manifests/N9-meta.json
_bmad-output/审查/g5-1-evidence/manifests/N9-outputs-after.txt
_bmad-output/审查/g5-1-evidence/manifests/N9-outputs-before.txt
_bmad-output/审查/g5-1-evidence/mutation-verdict.txt
_bmad-output/审查/g5-1-evidence/mutation_negative_controls.py
_bmad-output/审查/g5-1-evidence/negatives.tsv
_bmad-output/审查/g5-1-evidence/run_headless_negatives.sh
_bmad-output/审查/g5-1-evidence/run_headless_positives.sh
_bmad-output/审查/g5-2-evidence/README.md
_bmad-output/审查/g5-2-evidence/collect_live_baseline.py
_bmad-output/审查/g5-2-evidence/engine-and-products.sha256
_bmad-output/审查/g5-2-evidence/live-full-after.tsv
_bmad-output/审查/g5-2-evidence/live-full-before.tsv
_bmad-output/审查/g5-2-evidence/live-run-log.txt
_bmad-output/审查/g5-2-evidence/live-sha-after.txt
_bmad-output/审查/g5-2-evidence/live-sha-before.txt
_bmad-output/审查/g5-2-evidence/live-stat-after.txt
_bmad-output/审查/g5-2-evidence/live-stat-before.txt
_bmad-output/审查/g5-2-evidence/run_live_evidence.sh
_bmad-output/审查/phase0a-annotation-truth/A01-public-source-manifest-v2.schema.json
_bmad-output/审查/phase0a-annotation-truth/A02-public-ledger-v2.schema.json
_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-private-evidence-v2.schema.json
_bmad-output/审查/r11-evidence-2026-08-17/d1-ci-final-run.txt
_bmad-output/审查/r11-evidence-2026-08-17/d1-ci-gate.md
_bmad-output/审查/r11-evidence-2026-08-17/d2-dead-letter-census.md
_bmad-output/审查/r11-evidence-2026-08-17/e2-snapshot-slimming.json
_bmad-output/审查/r11-evidence-2026-08-17/weights-three-way.json
_bmad-output/研究/2026-06-27-UAT-A批注回复-出题AI与白板层级.md
_bmad-output/验收单/Stage-1-Round-23-阶段1-硬化-UAT-2026-05-08.md
_bmad-output/验收单/Stage-2-Round-23-阶段2-收口-UAT-2026-05-08.md
_bmad-output/验收单/Story-2.2+2.9-FINAL-comprehensive-UAT-2026-05-13.md
_bmad-output/验收单/Story-2.2+2.9-T3-T5-rerank-evidence-2026-05-11.md
_bmad-output/验收单/Story-2.2+2.9-wave-3-mini-UAT-2026-05-12.md
_bmad-output/验收单/Story-2.3-UAT-操作指引-2026-05-13.md
_bmad-output/验收单/Story-DAILY-REVIEW-PUSH-每日复习手机推送-mini-UAT.md
_bmad-output/验收单/Story-FSRS-V2-真实到期调度-mini-UAT.md
_bmad-output/验收单/Story-MEM-FLYWHEEL-记忆飞轮全计划-UAT.md
_bmad-output/验收单/Story-RAG-S0-阶段0止血-mini-UAT.md
_bmad-output/验收单/Story-RAG-S1-索引重写-mini-UAT.md
_bmad-output/验收单/Story-RAG-S2-阶段2-强化fastpath-UAT.md
_bmad-output/验收单/Story-RAG-S2.5-BoardManifest-mini-UAT.md
_bmad-output/验收单/Story-RAG-S2.6-导航改造-mini-UAT.md
_bmad-output/验收单/UAT-CARD-C5-board-recap薄版skill-2026-08-25.md
_bmad-output/验收单/UAT-CARD-C6-memory写侧保护网回收-2026-08-25.md
_bmad-output/验收单/UAT-CARD-G1-4-README诚实止血横幅-2026-08-27.md
_bmad-output/验收单/UAT-CARD-G1-5-README禁夸大机械lint-2026-08-27.md
_bmad-output/验收单/UAT-CARD-G2-1-cypher读写契约审计-2026-08-27.md
_bmad-output/验收单/UAT-CARD-G4-12-检索指标名实修正-2026-08-27.md
_bmad-output/验收单/UAT-CARD-G4-16-doc_type族接线普查-2026-08-28.md
_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md
_bmad-output/验收单/UAT-CARD-G5-1-触发矩阵与负例锁定-2026-08-27.md
_bmad-output/验收单/UAT-CARD-G5-2-拆分建议preview引擎-2026-08-27.md
_bmad-output/验收单/UAT-Multi-Vault-P0-1-vault_id-必填-2026-05-10.md
_bmad-output/验收单/UAT-RAG-P0-白板噪声修复-2026-05-10.md
_bmad-output/验收单/UAT-Study-Question-Skill-2026-05-10.md
_bmad-output/验收单/UAT-整合Dashboard-2026-05-01.md
_bmad-output/验收单/UAT-未验证功能上手验收-2026-07-13.md
_bmad/_config/agent-manifest.csv
_bmad/_config/files-manifest.csv
_bmad/_config/manifest.yaml
_bmad/_config/task-manifest.csv
_bmad/_config/tool-manifest.csv
_bmad/_config/workflow-manifest.csv
_bmad/bmb/workflows/module/steps-b/step-08-agents.md
_bmad/bmb/workflows/module/steps-c/step-05-agents.md
_bmad/bmb/workflows/workflow/steps-c/step-01b-continuation.md
_bmad/tea/workflows/testarch/nfr-assess/steps-c/step-03-gather-evidence.md
_bmad/tea/workflows/testarch/nfr-assess/steps-c/step-04-evaluate-and-score.md
_bmad/tea/workflows/testarch/test-review/steps-c/step-03-quality-evaluation.md
_decisions/CURRENT_TASK.md
backend/app/mcp/tools/board_manifest_tools.py
backend/app/models/board_manifest.py
backend/app/prompts/scoring/faithfulness_evidence_grounding.md
backend/app/prompts/scoring/stage1_evidence.md
backend/app/services/board_manifest_service.py
backend/scripts/census_dead_letter_episodes.py
backend/scripts/census_graphiti_pollution.py
backend/scripts/run_board_manifest_regression.py
backend/tests/fixtures/regression_baselines/board_manifest_baseline.json
backend/tests/fixtures/regression_baselines/board_manifest_baseline_history.jsonl
backend/tests/fixtures/regression_baselines/board_manifest_last_run.json
backend/tests/regression/board_manifest_gold_set.yaml
backend/tests/regression/test_board_manifest_contracts.py
backend/tests/regression/test_census_dead_letter_readonly_contract.py
canvas-vault/.obsidian/plugins/canvas-learning-system/manifest.json
canvas-vault/.obsidian/themes/Underwater/manifest.json
canvas-vault/节点/Characteristic-Equation-for-Eigenvalues.md
canvas-vault/节点/UAT-2.5.X-test.md
docs/_meta/dashboards/uat-queue.md
docs/project-status/fr-exploration/CONNECTS_TO-deprecation-evidence.md
docs/ragas-evaluation.md
docs/stories/story-12.A.6-complete-agents.md
docs/superpowers/plans/2026-04-07-fr-kg-04-a7-deep-research-manifest.md
frontend/obsidian-plugin/manifest.json

exec
/bin/zsh -lc 'git log --graph --decorate --oneline --max-count=12 --all' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
* 9104495b (HEAD -> card/s5-census) docs(census): receipt 补 round-12 commit [BATCH-2026-08-28-第五批 / CARD-G4-9]
* 543e8a34 docs(census): G4-9 round-12 最后两条措辞整改 [BATCH-2026-08-28-第五批 / CARD-G4-9]
* 05c85324 docs(census): receipt 补 round-11 commit [BATCH-2026-08-28-第五批 / CARD-G4-9]
* f4112c2c fix(census): G4-9 round-11 解阻整改 — 残留声明清除 + 测试补强 [BATCH-2026-08-28-第五批 / CARD-G4-9]
* f1828f9f docs(census): receipt 补 round-10 commit [BATCH-2026-08-28-第五批 / CARD-G4-9]
* dfbe70c7 fix(census): G4-9 round-10 解阻整改 — 声明彻底收敛 + 测试如实标注 [BATCH-2026-08-28-第五批 / CARD-G4-9]
* a775f80d docs(census): receipt 补 round-9 commit [BATCH-2026-08-28-第五批 / CARD-G4-9]
* 6b8debee fix(census): G4-9 round-9 名实一致 + 只读契约回归测试 + 声明有界化 [BATCH-2026-08-28-第五批 / CARD-G4-9]
* 2cdf77a4 docs(census): receipt 补 round-8 commit [BATCH-2026-08-28-第五批 / CARD-G4-9]
* af251e4a fix(census): G4-9 Codex round-8 findings 整改 [BATCH-2026-08-28-第五批 / CARD-G4-9]
* 85dd1c8f docs(census): receipt 补 round-7 commit [BATCH-2026-08-28-第五批 / CARD-G4-9]
* f389980c fix(census): G4-9 Codex round-7 架构级修复 — 消除截断动作 [BATCH-2026-08-28-第五批 / CARD-G4-9]

**Clarifying document changes relative to f411**
**Planning inspection of binding evidence in commit 543**
**Reading full file contents at commit 543**
exec
/bin/zsh -lc "git show '543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md' | nl -ba" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
     1	# CARD-G4-9 — DLQ 真实挂载 census 分诊报告
     2	
     3	> **批次**: BATCH-2026-08-28-第五批 / CARD-G4-9（4h · wave 1 · 未来铺路）
     4	> **性质**: 只读 census。0 重放、0 业务代码改动。代码产物 = `backend/scripts/census_dead_letter_episodes.py` + 其只读契约回归测试。
     5	> **只读声明的准确边界（round-9 收敛，见 §7j）**: 本次运行对**本次列出的输入文件**（4 份 DLQ + qa_metrics.db）shasum 前后不变（证据包留有本次 before/after 一对，非九轮各存一对）；回归测试中**每条行为测试各自断言的那个具体场景** fail-closed（17 条跑真实 CLI + 3 条源码静态检查）——这是**逐例证据**，不构成"所有误用路径均 fail-closed"的整体证明。但**不声称**在共享可写目录、并发写者、活跃 SQLite DB 等敌意环境下具备生产级安全——剩余必需项见 §7j 清单。
     6	> **代码基线**: 分析对象锚定 `37387a86`（第五批开工基线）。**本卡交付物 artifact commit 链**：精确 SHA 逐段记录于 `_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt`（commit 无法自含己身 SHA，故用后置 receipt 绑定——Codex round-4 LOW 整改）
     7	> **台账**: `_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json`（92 条逐条，G4-10 消费）
     8	> **证据包**: `_bmad-output/审查/G4-9-evidence/`（shasums before/after、grep 自证、容器内 sha 实测）
     9	> **执行日期**: 2026-08-28
    10	
    11	---
    12	
    13	## §1 挂载真相（live/主仓/孤儿三址 sha 对照 + compose 遮蔽史）
    14	
    15	**live DLQ 的唯一权威地址**是 `feature-obsidian-hybrid-dev` worktree 的 `backend/data/`（双树拓扑：线上容器代码挂载自该 worktree）。容器内实测确认同源：
    16	
    17	```
    18	docker exec canvas-learning-system-backend sha256sum /app/data/dead_letter_episodes.jsonl
    19	→ 3b37460f4215f6ac...ef3ba590（92 行）— 与宿主 live 地址逐字节一致
    20	```
    21	
    22	| 地址 | 路径 | 行数 | sha256 前 16 | mtime | 裁定 |
    23	|---|---|---|---|---|---|
    24	| **live**（权威） | `…/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl` | **92** | `3b37460f4215f6ac` | 2026-08-11 22:01 (+0800) | 容器 `/app/data` 经 `./backend:/app` 挂载即此文件；census 对象 |
    25	| 主仓 | `canvas-learning-system/backend/data/dead_letter_episodes.jsonl` | 685 | `490c903b2f3636e1` | 2026-04-07 | 陈旧副本（部署迁往 worktree 前的历史死信，止于 4 月）；不代表现网 |
    26	| 孤儿① | `…/worktrees/feature-obsidian-hybrid-dev/data/dead_letter_episodes.jsonl` | 1 | `bfb3f6c413aab7dd` | 2026-07-13 | 已删除的 `./data:/app/data` 子挂载目标残留；从未在容器内生效 |
    27	| 孤儿②（附注） | `canvas-learning-system/data/dead_letter_episodes.jsonl` | 4 | `75c5f7593b9b2e99` | 2026-04-06 | 主仓根 `data/` 早期宿主进程 cwd 落点残留 |
    28	
    29	**compose :206-212 遮蔽史**（本 worktree `docker-compose.yml:206-212`，与 live worktree 同文）：`- ./data:/app/data` 是嵌套 bind，被 `./backend:/app` 父挂载遮蔽——`docker inspect` 记录了它，但容器 `/proc/self/mountinfo` 从不出现，**实际生效的一直是 `backend/data/`**。R11-BATCH2（2026-08-17）已删除该行，理由是遮蔽与否取决于挂载顺序、一次 recreate 就可能翻转，届时 92 行死信会被 1 行的孤儿①覆盖不可见。删除后 `/app/data` 恒等于 `backend/data/`。**证据边界（诚实声明）**：本卡独立实证的是**现状**（容器内 sha 与宿主 live 地址同源、当前 compose 无子挂载行）；"历史上子挂载从未在容器内生效"沿引 compose 注释史与 R11-BATCH2（2026-08-17）当时的 mountinfo 实测记录，本卡未重跑历史 `docker inspect` 独立复证。
    30	
    31	**本 worktree（card-s5-census）没有 `backend/data/dead_letter_episodes.jsonl`**——数据文件不入 git，census 一律指向 live 绝对路径运行，未复制任何数据进本 worktree。
    32	
    33	## §2 总量与分类台账（class 分诊）
    34	
    35	92 条，分类与勘探预期**零偏差**：
    36	
    37	| class | 条数 | 预期 | error_type | 错误原文（截断） | 根因与修复状态 |
    38	|---|---|---|---|---|---|
    39	| `budget_400` | **89** | 89 | BadRequestError | `Error code: 400 … 'request (16998 tokens) exceeds the available context size (16384 tokens)' type: exceed_context_size_error` | 本地 LLM 服务 context 16384 上限被超（实测请求 16948–20831 tokens）。**未修复**——根因治理归 G4-10（切块或提 budget） |
    40	| `schema_entity_type` | **2** | 2 | EntityTypeValidationError | `name cannot be used as an attribute for LearningConcept as it is a protected attribute name.` | **已修复**：P0-4（2026-05-14）双处——`entity_types.py:343` `LearningConcept.name`→`concept_name`（行 1）+ `entity_types.py:254` `LearningTip.created_at`→`tip_created_at`（行 2），同型冲突不再发生 |
    41	| `group_id_format` | **1** | 1 | GroupIdValidationError | `group_id "vault:default" must contain only alphanumeric characters, dashes, or underscores` | **已修复**：`group_id_compat.py:64 sanitize_group_id_for_graphiti` 冒号→`__` 物理化已兜（T1 契约），写路径不再直传 D16 冒号格式 |
    42	| `unexpected` | 0 | 0 | — | — | 无偏差需解释 |
    43	
    44	时间分布：3 条 schema/group_id 全部 2026-05-14（P0-4 修复当日之前的失败）；89 条 budget 集中于 2026-08-08 ~ 08-11（8/48/25/8），系 SessionEnd 归档-蒸馏管道对长会话反复触发超限。group_id 分布：`vault:canvas_vault`×89、`vault:default`×3（三条旧格式记录重放时需 group 重映射，见 §6）。
    45	
    46	## §3 inline 完整性 + SHA 对账
    47	
    48	`DeadLetterStore.store()` 落盘的 `episode_body` 来自 `EpisodeTask.to_dict()`，后者做 `episode_body[:200]` 截断（`episode_worker.py:107`，"truncate for logging"）；全量正文只有 `DEAD_LETTER_STORE_FULL_BODY` 开启时以 `episode_body_full` 另存——**live 容器该 env 未设置（实测），92 条 `episode_body_full` 均缺席**。逐条重算 sha256(inline) 对账 `episode_body_sha256` 结果：
    49	
    50	| inline 状态 | 条数 | 判据 |
    51	|---|---|---|
    52	| `full_verified`（内联全量，sha 对账通过） | **4** | 重算值 == 声明值且长度精确匹配（四条正文实为 131/142/150/180 字符，范围 **131–180**，天然未截断；round-2 LOW 修正） |
    53	| `truncated_prefix`（200 字符前缀） | **88** | len(inline)==200、声明 sha 为合法 64-hex 且声明长度 205–8036。**注**：sha 只能证明 inline≠声明全文，"确为前缀"依赖 `to_dict()[:200]` 生产不变量，无法用 sha 直接证明（Codex round-1 HIGH-1 措辞收敛） |
    54	| `anomaly`（对不上账） | **0** | — |
    55	
    56	4 条 full_verified = 3 条 callout（§2 的 schema/group_id 三条）+ 1 条短 qa_highlight（行 74）。
    57	
    58	## §4 源指针核销（qa_metrics.db，源 fd 只读 + 内存副本）
    59	
    60	- **qa_metrics.db**（live `backend/data/qa_metrics.db`；**读法见下**：源文件以 `O_RDONLY|O_NOFOLLOW` 打开、读出字节灌入内存库，**不经路径打开、不使用 URI `mode=ro`**——该旧表述已于 round-9 废弃）：唯一表 `qa_error_logs`（列 category/error_type/source_module/stack_summary/created_at，**无 request_id 列**），**行数 = 0**。按三个 error_type 探查命中均 0。**核销裁定：`no_source_rows` —— qa_metrics.db 对 92 条死信不构成任何源指针，0/92 可经其溯源。**
    61	- 附加核销（超出卡面要求，如实记录以封死"还有别处可捞"的幻想）：
    62	  - `llm_call_logs.db`（同目录）：本卡仅做**一次性人工只读查看 schema**（未纳入脚本探测路径），确认仅 token/延迟/成本指标列，**无 prompt/response 正文**；
    63	  - `backend/data/outbox/`：**空目录**（A7 outbox 只接 enqueue 失败，本 92 条全部是 enqueue 成功、处理失败，不经 outbox）；
    64	  - `episode_body_full`：0 条（§3）。
    65	- **有效源指针只剩一条**：DLQ 记录的 `request_id`（structlog contextvars 捕获的进程内值）把同一次 SessionEnd 归档的 3–5 条 episode 绑成组，组内 `session-archive:<id16>` / `…session:<hex>` 名字携带 session id → `~/.claude/projects/-…-canvas-vault/<session>.jsonl` transcript。**7 个 session 的 transcript 全部在盘实测存在**（90,584–723,950 字节，逐一恰 1 个 glob 命中、常规文件），88/88 条截断记录归因成功、0 条归因冲突。**归因边界（诚实声明）**：归因 = "唯一在盘候选已定位"，≠ "内容已验证"——本卡未读任何 transcript 内容，内容级核验归 G4-10 重建时以 `episode_body_sha256` 对账。
    66	
    67	## §5 可恢复性裁定（三态 + unverifiable 第四态）
    68	
    69	| 三态 | 条数 | 裁定依据 |
    70	|---|---|---|
    71	| **可字节级**（byte_exact） | **4** | inline 正文全量：sha256 重算对账通过**且**长度精确匹配（fail-closed 双门）——重放可逐字节还原 episode |
    72	| **近似**（approximate） | **88** | inline 仅 200 字符前缀，但经 request_id 组归因到在盘 transcript；G4-10 可对 22 条 session-archive 重新格式化 transcript（确定性、可用 `episode_body_sha256` 验证是否达字节级）、对 66 条 qa_highlight(44)/distillation(22) 重跑蒸馏（LLM 非确定性，语义近似、不保证逐字节） |
    73	| **不可恢复**（unrecoverable） | **0** | inline 截断且经完整可见的扫描确认无在盘上游源 |
    74	| **不可核验**（unverifiable，round-4 新增） | **0** | 源可见性不足（扫描受阻/不可读候选/归因冲突）——既不宣称可恢复，也不宣称不可恢复。Codex round-4 指出：把"看不见"终态化为"不可恢复"是不诚实断言，故单列第四态 |
    75	
    76	**不可恢复清单（显式成段）**：本次 census 裁定不可恢复条目 **0 条**；三态裁定覆盖 92/92，**"待定"0 条**。
    77	
    78	诚实边界：`近似` ≠ 已恢复。88 条的实际重建（含 22 条 session-archive 是否能达字节级）是 G4-10 的工作与验收，本卡只交付"上游源在盘、路径已核销"的证据链。transcript 属用户本机 `~/.claude/projects/` 数据，若未来被清理，近似裁定随之失效——台账已逐条记录 transcript 绝对路径供 G4-10 开工时复核。
    79	
    80	## §6 台账稳定键（G4-10 交接契约）
    81	
    82	台账逐条携带复合键 `{line_no, sha256_prefix(16 hex), request_id}`。**语义（Codex round-1 LOW-2 修正）**：这是**冻结快照内的 occurrence key**，不是跨文件重排或语义幂等键——台账头部 `dlq_file.sha256`（`3b37460f4215f6ac…`）即快照指纹，`line_no` 在该快照内已单列唯一；`sha256_prefix`（本快照 69 个唯一值，qa_highlight 家族实测同名同 sha 多条）与 `request_id`（仅 25 个唯一值，进程内 contextvars、重启可复用）是**冗余对账/诊断维度**，不是唯一性的必要条件。G4-10 消费前先 diff 头部 sha 即知 DLQ 是否长了新条目；语义级去重不得按本键，须按 `duplicate_clusters` 段（见下）。**语义重复簇（MEDIUM-2 整改）**：按 `{name, episode_body_sha256, group_id}` 聚簇，**6 簇覆盖 29 行**（最大簇 = 同一 session-archive 16 行，`reference_time` 各不相同——同内容反复入队反复超限）。台账 `duplicate_clusters` 段逐簇列 line_nos，records 逐条透传 `reference_time`；G4-10 重放前必须先定去重策略（89 条 budget 修根因后若逐条盲放，将把同内容写入最多 16 遍）。
    83	
    84	**隐私（MEDIUM-3 整改）**：`transcript_paths` 含本机用户名与完整 session UUID，台账与本报告为 **private-only 工件**（台账头部已带 privacy 字段；仓库纪律 = 不 push 公网远端）。
    85	
    86	逐条另带 `class / inline_state / recoverability / transcript_paths / transcript_match_count / attribution_conflict / error_excerpt / failed_at / reference_time`，G4-10 可直接按 `recoverability` 分桶排重放优先级（建议：4 条 byte_exact 先行——但其中 3 条 group_id 为已弃用 `vault:default`，重放前需按 D16 规约重映射并过 `to_physical_group_id()`；89 条 budget_400 重放前必须先修 context 超限根因，否则原样重放必然复现 400）。
    87	
    88	## §7 裁判证据（整改版脚本重跑）
    89	
    90	| 证据 | 结果 |
    91	|---|---|
    92	| 运行前后 shasum（live/主仓/孤儿①/孤儿② 四份 DLQ + qa_metrics.db） | `diff shasums-before.txt shasums-after.txt` 空 → **本次留存的 before/after 样本 SHA 相同**。⚠️ 该证据只证明**前后终态字节一致**，**不证明**读取期间零写入，也**不证明**每轮均留存了独立证据（仓库只保留最新一对） |
    93	| grep 自证（import 行全 stdlib；neo4j/graphiti/bolt/app. import 0 命中；`--apply` 定义 0 命中；写模式 open 仅 `--out` 1 处且受路径碰撞守卫保护） | **PASS**（`grep-selfattest.txt`，含守卫在位证明） |
    94	| 容器内 sha 实测 | 92 行、sha 与宿主 live 地址一致（`container-sha-check.txt`） |
    95	| class 偏差 | 无（89/2/1 与勘探预期一致，脚本 `class_deviation` 字段为空） |
    96	| 负例门（round-1 整改自证） | `--out`==`--dlq` → exit 2 拒写、DLQ 完好；transcripts 根缺失 → exit 2 拒诊；sha 匹配但长度不符（round-1 HIGH-1 反例①）→ anomaly/unrecoverable；坏 JSON 行/空行 → unparseable 逐行入台账不拒诊 |
    97	| 负例门（round-2 整改自证） | **hardlink** 指向 DLQ 的 --out → exit 2 + DLQ sha 不变；**case-only 别名**（`DLQ.jsonl`）→ exit 2 + DLQ 完好；**anomaly + episode_body_full 组合**（sha 对但长度 999）→ anomaly/unrecoverable（不再翻案 byte_exact）；**chmod 000 根** → exit 2 拒诊；**symlink 逃逸**（根内 .jsonl → 根外 .txt）→ match_count=0/unrecoverable；正例回归：真实唯一命中仍 approximate |
    98	
    99	## §7b Codex round-1 整改记录（BLOCKED → 全项整改）
   100	
   101	- **BLOCKER-1（--out 可截断输入）**：写前 `Path.resolve()` 碰撞守卫（对照 dlq/compare/qa-metrics-db 集合，命中 exit 2；resolve 覆盖 symlink 变体）。负例实测复现拒绝。
   102	- **BLOCKER-2（快照不原子）**：DLQ 单次 `read_bytes()`，头部 sha256/line_count 与逐条 records 派生自同一份内存字节；mtime 显式标注为 stat 参考值。
   103	- **BLOCKER-3（交付物未冻结漂移）**：以本卡 commit 冻结全部交付物 exact bytes（脚本/报告/台账/证据包同 commit）；grep-selfattest 已按最终版行号重生成并内嵌脚本 sha 前缀。
   104	- **HIGH-1（inline 判定不 fail-closed）**：full_verified 加长度精确匹配门；truncated_prefix 加 64-hex 合法性门；anomaly 一律 unrecoverable + 如实 basis（不再谎称截断、不再滑入 approximate）。
   105	- **HIGH-2（request_id fail-open）**：分组键改 `(类型名, 值)`；缺失/None 按 line_no 单条成组零传染；组内多 token 前缀一致门，冲突记 `attribution_conflict` 拒绝采信（现网 92 条 0 冲突）。
   106	- **HIGH-3（transcript 归因折叠）**：恰 1 个常规文件命中才算归因（多命中 = ambiguous 拒采信）；glob 改递归下探；transcripts 根缺失整体 exit 2（拒绝产出 unrecoverable 假象）。
   107	- **MEDIUM-1**：`episode_body_full` 在盘且 sha 对账通过 → byte_exact 采信（现网 0 条，通路已备）。
   108	- **MEDIUM-2**：`duplicate_clusters` 段 + 逐条 `reference_time`（见 §6）。
   109	- **MEDIUM-3**：台账头部 privacy 字段 + 本报告 private-only 声明（见 §6）。
   110	- **LOW-1~4**：token 区间 16948–20831、长度区间 205–8036、稳定键语义重写、schema 双处证据、挂载历史证据边界——均已在正文落地。
   111	
   112	整改后全量重跑：**92 条数字与整改前逐项一致**（class 89/2/1、三态 4/88/0、归因冲突 0、unparseable 0），重复簇 6/29 行与 Codex 独立复算吻合。另有独立 Workflow 4-agent 复核（92 条重算 0 mismatch、7 transcript 在盘实测、台账 sha 一致）交叉确认。
   113	
   114	## §7c Codex round-2 复审整改记录（10/13 CLOSED → 剩余 3 项 + 3 新 LOW 全部整改）
   115	
   116	round-2 复审确认 BLOCKER-2/3、HIGH-2、MEDIUM-1~3、LOW-1~4 共 10 项 CLOSED，并抓出 3 项**未真正闭合**（均实测复现）+ 3 条新 LOW：
   117	
   118	- **BLOCKER-1 NOT-CLOSED（hardlink / case-only 别名绕过）**：原守卫比较 `resolve()` **字符串**，hardlink 指向输入、以及大小写不敏感文件系统上的 case-only 别名均绕过并截断输入。**整改**：改为比较**文件身份 `(st_dev, st_ino)`**（对已存在的 --out）+ 保留路径比较作第二道。负例实测：两种绕过均 exit 2、DLQ sha 不变。
   119	- **HIGH-1 NOT-CLOSED（full_body 分支翻案）**：`full_body_verified()` 只核 sha 不核长度，且排在 anomaly 分支**之前**——`body="abc"/full="abc"/sha 正确/声明长度 999` 被判 byte_exact，直接反驳"anomaly 一律 unrecoverable"。**整改**：full_body 加长度精确门 + 判定顺序改为 `state != "anomaly"` 前置条件。负例实测翻转为 anomaly/unrecoverable。
   120	- **HIGH-3 NOT-CLOSED（不可见根 / symlink 逃逸）**：存在但 `chmod 000` 的根仍 exit 0 并把全部记录假判 unrecoverable；glob+isfile 跟随 symlink，根内 `.jsonl` → 根外 `.txt`、目录 symlink 逃逸均被当唯一来源采信。**整改**：`os.access(R_OK|X_OK)` 不可读即 exit 2；glob 结果拒绝 `islink` 条目并要求 `realpath` 落在根内。两反例实测封死，正例（真实唯一命中）无回归。
   121	- **新 LOW ×3**：full_verified 长度范围修正为 131–180；台账 `class_distribution`/`recoverability_distribution` 补零并新增 `inline_state_distribution`（固定 schema，消费者无需补齐缺席键）；`line_count` 改用 `splitlines()` 与 records 同口径（原 `count("\n")` 在 bare CR / U+2028 下会与 records 数不一致）。
   122	
   123	round-2 整改后再次全量重跑：92 条、class 89/2/1、三态 4/88/0、重复簇 6/29、shasum 不变——**数字仍逐项一致**，整改只收紧通用鲁棒性。
   124	
   125	## §8 复现命令
   126	
   127	```bash
   128	cd .claude/worktrees/card-s5-census
   129	python3 backend/scripts/census_dead_letter_episodes.py \
   130	  --dlq "…/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl" \
   131	  --qa-metrics-db "…/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db" \
   132	  --compare "…/canvas-learning-system/backend/data/dead_letter_episodes.jsonl" \
   133	  --compare "…/feature-obsidian-hybrid-dev/data/dead_letter_episodes.jsonl" \
   134	  --compare "…/canvas-learning-system/data/dead_letter_episodes.jsonl" \
   135	  --out "_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json"
   136	```
   137	
   138	诚实标注（与卡面一致）：本卡离用户日常价值远，属恢复能力地基；未修任何根因，未重放任何条目。
   139	
   140	## §7d Codex round-3 复审整改记录（4/6 CLOSED → 剩 2 项 + 3 新发现全部整改）
   141	
   142	round-3 确认 HIGH-1 与三条 LOW 已 CLOSED、台账数字有效且与 commit 字节一致，两项路径安全判 PARTIAL：
   143	
   144	- **BLOCKER-1 残留两条绕过**：① `protected_paths` 未含**归因到的 transcript**，`--out=<唯一 transcript>` 会截断恢复源；② check-then-open 的 **TOCTOU** 仍在（检查后、打开前把 --out 换成指向 DLQ 的链接）。**整改**：① 写出前把全部 `transcript_paths` 并入保护集；② 改 `os.open(O_WRONLY|O_CREAT|O_NOFOLLOW)` **不带 O_TRUNC** 打开 → 对**实际 fd** `fstat` 校验 inode → 通过才 `ftruncate`，检查与写入作用于同一 fd，替换攻击无效。反例实测：`--out` 指向唯一 transcript → exit 2、transcript sha 不变。
   145	- **HIGH-3 残留**：`glob(recursive=True)` 在 realpath 过滤**之前**已递归遍历（Python 3.14 glob 跟随目录 symlink 且**静默吞掉不可读子树错误**）→ 越根枚举 + "假唯一/假不可恢复"；mode `000` 的 regular transcript 仍过 `isfile()` 被判 approximate。**整改**：改 `os.walk(onerror=..., followlinks=False)`（不跟随目录 symlink、遍历错误显式捕获）+ 候选加 `os.access(R_OK)` 门；遍历受阻或存在不可读候选一律记 `attribution_conflict` 拒绝裁定（既不宣称找到、也不宣称不可恢复）。三条反例实测全部 fail-closed。
   146	- **新 MEDIUM（JSONL framing）**：生产端 `ensure_ascii=False` 可原样写出字符串内的 U+2028，`splitlines()` 会把一条合法单-LF 记录劈成两条坏行。**整改**：新增 `_split_jsonl_lines()` 严格按 LF 分帧，header `line_count` 与 records 共用同一函数。
   147	- **新 LOW（输入 schema）**：合法 JSON 但非对象（`null` / 数组 / 标量）解析成功后在 `rec.get()` 处抛 AttributeError 炸全量。**整改**：非 dict 归 `unparseable`（`not_a_json_object: <type>`），实测两条毒行不影响其余记录。
   148	- **新 LOW（provenance）**：报告头只写起始基线未区分整改 artifact commit —— 已在报告头补三段 commit 链。
   149	
   150	round-3 整改后第三次全量重跑：92 条、class 89/2/1、三态 4/88/0、重复簇 6/29、shasum 不变——**三轮整改数字全程未变**，改的全是通用鲁棒性与路径安全。
   151	
   152	## §7e Codex round-4 复审整改记录（1/6 CLOSED → 全部 9 项整改）
   153	
   154	round-4 只认可 1 项 CLOSED（非 dict JSON 门），并用更深的静态反例推翻了另外 5 项的"闭合"，另提 2 BLOCKER / 1 HIGH / 2 MEDIUM / 3 LOW。逐条整改（全部实测复现→封死）：
   155	
   156	- **BLOCKER①（不可读但可写的 transcript 绕过保护集）**：mode `0200` 的候选在 unreadable 分支被清空 `transcript_paths`，因此不进保护集，`--out` 指向它仍被截断（无需竞态）。**整改**：新增 `all_candidate_paths` 保留**所有见到的候选**（含不可读、含被冲突分支清空的），写出前全部并入保护集。实测：mode 0200 候选作 `--out` → exit 2、文件字节不变。
   157	- **BLOCKER②（源侧 TOCTOU）**：保护身份按**路径** stat 采集、DLQ 稍后才按路径读取，两步间可换入另一 inode → 实际读取对象不在保护集。**整改**：`snapshot_file()` 改为 `os.open(O_RDONLY|O_NOFOLLOW|O_NONBLOCK)` → `fstat` 取身份 + regular-file 门 → **从同一 fd 读全量**，返回的身份即**实际被读取对象**；compare 副本同样以读取身份入保护集；输入 `stat` 失败不再静默吞而是 exit 2。
   158	- **HIGH（不可见被终态化为 unrecoverable）**：扫描受阻/冲突时主链仍产出 `unrecoverable`，与报告"既不宣称不可恢复"自相矛盾。**整改**：引入第四态 **`unverifiable`**（源可见性不足，basis 逐条说明是遍历受阻/不可读候选/归因冲突），distribution 与 `unverifiable_list` 同步。实测：不可读子树 → `unverifiable=1`，不再冒充 unrecoverable。
   159	- **MEDIUM（FIFO/设备节点）**：`--out` 缺 regular-file gate 与 `O_NONBLOCK`。**整改**：`O_NONBLOCK` + `S_ISREG` 双门（读侧同样）。实测：FIFO 作 `--out` → exit 2 且不阻塞。
   160	- **MEDIUM（非法 UTF-8 冒充有效记录）**：`errors="replace"` 把坏字节改写成合法对象。**整改**：`_split_jsonl_lines()` 改**逐行 strict decode**，解码失败归 `unparseable`。实测：`b'{"a":"\xff"}'` → `utf8_decode_error`，records=0。
   161	- **LOW ×3**：dict 内字段错型防御（`name=None` / `request_id=[]` 不可哈希 / `episode_body` 非 str 均不再炸全量，按 line_no 单条成组或判 anomaly）；`transcripts_dir="/"` 的 `//` containment 特例；`0o600` 对**既有**输出文件用 `fchmod` 显式收紧（实测台账 mode 现为 `-rw-------`）。
   162	- **LOW（provenance 自指）**：commit 无法自含己身 SHA，改用后置 `artifact-commit-receipt.txt` 绑定精确链，报告头指向该 receipt。
   163	
   164	round-4 整改后第四次全量重跑：**92 条、class 89/2/1、三态 4/88/0（unverifiable 0）、重复簇 6/29、shasum 不变——四轮整改数字全程未变**。
   165	
   166	## §7f Codex round-5 复审整改记录（3/8 CLOSED → 9 项全部整改）
   167	
   168	round-5 用更深的静态反例继续推翻"闭合"，提出 2 BLOCKER / 2 HIGH / 2 MEDIUM / 3 LOW，逐条整改并实测：
   169	
   170	- **BLOCKER①（token 冲突/无 token 时扫描前早退 → 候选不进保护集）**：`--out` 指向冲突组的候选 transcript 仍可无竞态截断。**整改**：`resolve_group_attribution()` 重写为**先扫描后判定**——无条件为每个 token 扫描收集候选进 `all_candidate_paths`（保护集口径），再做冲突/唯一性判定；候选 `stat` 失败不再 `continue` 吞掉而是 exit 2（保护集不完整即拒绝写出）。实测：冲突候选作 `--out` → exit 2、文件 sha 不变。
   171	- **BLOCKER②（qa_metrics.db 身份未绑定实际读取）**：仍是早期 path-stat + SQLite 稍后按路径重开。**整改**：`probe_qa_metrics()` 改 `os.open(O_RDONLY|O_NOFOLLOW|O_NONBLOCK)` 取 fstat 身份 + `S_ISREG` 门 → SQLite 打开后**复核路径身份仍等于该身份**，不等即 `identity_changed_..._refused`；身份入保护集。本次运行 `file_identity_verified: true`。
   172	- **HIGH①（anomaly 吞掉不可见性）**：`anomaly→unrecoverable` 排在 conflict 判断之前，`anomaly + 扫描受阻` 仍被假终态化。**整改**：判定链改为**可见性优先**——归因不可核验时无论 inline 状态一律 `unverifiable`，basis 逐条写明原因（无 token / token 冲突 / 扫描受阻 / 候选 stat 失败 / 不可读候选 / 多命中 ambiguous），并附注 inline 是否也 anomaly。实测：anomaly+不可读子树 → `unverifiable`。
   173	- **HIGH②（`fchmod` 先于 protected-id 检查）**：`--out` 指向受保护的 0644 输入时，会**先把只读输入权限改成 0600** 再拒绝——字节没截断但输入已被修改。**整改**：碰撞检查前移到 `fchmod` 之前。实测：mode 644 → 644 不变。
   174	- **MEDIUM（QA DB 无特殊文件门）**：随 BLOCKER② 一并加 `S_ISREG` + `O_NONBLOCK`。
   175	- **MEDIUM（无 token 未扫描即判不可恢复）**：改为 `unverifiable` + `no_token` 标记（见 HIGH①）。
   176	- **LOW ×3**：单独 `b"\n"` 现算 1 个空行（实测 `line_count=1`）；`errors="replace"` 改 **strict encode**（JSON escaped lone surrogate 不能再构造假 `full_verified`）；`bool` 是 `int` 子类 —— `episode_body_length=True` 现被长度门拒绝（实测判 anomaly）。
   177	
   178	**归因冲突计数由 0 变为 3（如实说明）**：round-5 起"名字不含 session token"被诚实标记为 `no_token`（未做归因扫描），命中的正是 3 条 `callout_annotation` 记录。它们 inline 正文全量、sha 对账通过，**不依赖 transcript**，故仍判 `byte_exact`——三态分布不变（4/88/0/0），88 条 approximate 仍全部为唯一 transcript 命中。这是标注口径变诚实，不是结论变化。
   179	
   180	round-5 整改后第五次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变——五轮整改数字全程未变**。
   181	
   182	## §7g Codex round-6 复审整改记录（6/9 CLOSED → 架构级修复 + 全部余项）
   183	
   184	round-6 确认 visibility 优先、fchmod 顺序、no_token 语义、三条 LOW 共 6 项 CLOSED，并揭示了一个**架构层面的根因**：
   185	
   186	> 我的 `--out` 保护集依赖**枚举完整性**——只要某个真实源没被 `os.walk` 看到（不可列举但可穿越的 `0333` 子目录），或 inode 被 A→B→A 换过（QA DB 的 ABA），它就不在集合里，`--out` 指向它仍可截断。这不是补丁能修的，是设计缺陷。
   187	
   188	- **BLOCKER①②的架构级修复**：增加**不依赖枚举的路径层防御**——`--out` 的 `realpath` 不得落在 transcripts 根内（恢复源区域整体禁写）、不得等于任一输入路径的 `realpath`。路径层 + inode 层双保险，任一命中即拒。实测：`0333` 隐藏目录内的 transcript 作 `--out` → exit 2、文件完好（inode 保护集根本没看见它，路径层拦住了）。
   189	- **BLOCKER② 补充修复**：QA DB 的验证 fd 原本验证完即关闭、SQLite 再按路径重开（ABA 可绕）。改为**验证 fd 保持打开**直到 SQLite 连接建立并复核完毕，且连接后二次 `fstat` 该 fd 校验身份未变且 `st_nlink != 0`。本次运行 `file_identity_verified: true`。
   190	- **BLOCKER① 补充修复**：`no_token` 分支原本完全不扫描（`all_candidate_paths=[]`）→ 改为**无论有无 token 都遍历**，所有 `.jsonl` 一律入保护集口径。
   191	- **MEDIUM（证据包漂移）**：`grep-selfattest.txt` 曾停留在 round-4 的脚本 SHA 与旧行号、receipt 未含最新 commit——这是我的疏漏。已重生成（内嵌当前脚本 sha256 + 生成时点声明），receipt 随本轮补链。
   192	- **LOW ×3**：ledger 新增 `attribution_conflict_reason` 自描述（本次 92 条：`no_token` 3 / 其余 89 无冲突）；`json.dumps` 对 lone surrogate 回退 `ensure_ascii=True` 并显式标注，不再整次 census 拒绝；`stat_failures` 分支保留（Codex 确认非额外绕过，仅基本不可达）。
   193	
   194	round-6 整改后第六次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变——六轮整改数字全程未变**。
   195	
   196	## §7h Codex round-7 复审整改记录（关键裁定分离 + 架构级第二次修复）
   197	
   198	round-7 给出了本卡最重要的一次裁定分离：
   199	
   200	> **「现有 92 条冻结 ledger 可以采信；CARD-G4-9 生成器与 UAT 的纯只读安全声明不可验收。」**
   201	
   202	即：卡面的 census 判据（分类/对账/三态/挂载真相/稳定键/shasum 不变）已满足且被独立复算确认；阻断项全部落在"生成器作为工具的只读安全承诺"上。逐条整改：
   203	
   204	- **BLOCKER（大小写别名根）**：本机实测 `/Users/Heishing/.claude/projects` 与 `/users/heishing/...` `samefile=True` 但 `realpath` 字符串不同，prefix guard 返回 False——**无需竞态的实际绕过**。我 round-6 用的 `os.path.normcase` 在 POSIX 上是**恒等函数**（假设错误）。**整改**：新增 `_path_is_within()`，从目标逐级向上比较 **inode 身份**，完全不依赖路径字符串；`--out` 与输入文件的比较改 `os.path.samefile`。实测：别名根作 `--out` → exit 2，正例无回归。
   205	- **NOT-CLOSED ×4（根外 hardlink 指向隐藏目录内 transcript / 根 retarget TOCTOU / 检查后换父目录 symlink 或 basename hardlink）+ MEDIUM（非原子写）**：这五项依附于同一个动作——**截断一个已存在的文件**。**架构级修复**：写出改为「同目录 `O_EXCL` 新建临时文件 → 写 → `fsync` → `os.replace` 原子替换」，**全文再无任何 `ftruncate` 调用**。`O_EXCL` 保证写入目标是本进程新建的对象，因此"截断既有对象"这条具体路径消失（三场景各自取证，不声称整类绕过均已失效）；`os.replace` 同时消除崩溃/ENOSPC 留下部分台账的风险。实测：根外 hardlink 指向根内 transcript 作 `--out` → 台账正常写出而**源文件内容完好**（`os.replace` 只重绑定该名字，不触碰底层 inode）。
   206	- **NOT-CLOSED（扫描受阻仅标记不停写）**：扫描受阻 ⇒ 保护集必然不完整。**整改**：`scan_errors`/`stat_failures` 非空时**直接拒绝写出台账**（exit 2），实测不落盘。
   207	- **LOW（lone surrogate 回退失效）**：异常发生在后续 `write`，不在原 `try` 内。**整改**：`json.dumps` 后立即 `.encode("utf-8")` 探测，编码错误在写出前暴露并回退 `ensure_ascii=True`。
   208	- **LOW（receipt 用 8 位缩写）**：如实登记为已知限制（仓库内唯一可解析），未改为 40-hex 以保持 receipt 可读性——列 follow-up。
   209	
   210	round-7 整改后第七次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变、台账 mode 0600、无临时文件残留——七轮整改数字全程未变**。
   211	
   212	## §7i Codex round-8 复审整改记录（裁定分离重申 + 3 BLOCKER 全闭）
   213	
   214	round-8 重申 round-7 的裁定分离，措辞更明确：
   215	
   216	> **可验收：92 条冻结 ledger snapshot。不可验收：当前生成器的一般安全性，以及 UAT 的"纯只读、唯一写出口、整类 TOCTOU 已消失"声明。**
   217	
   218	三条新 BLOCKER 全部属实，逐条整改：
   219	
   220	- **BLOCKER①（SQLite URI 未转义）**：`file:{db_path}?mode=ro` 在路径含 `#` 时，`mode=ro` 会落进被忽略的 URI fragment，SQLite 可能按**默认读写模式**打开——直接反驳"唯一写出口"。
   221	- **BLOCKER②（QA DB 仍按 pathname 打开）**：验证 fd 保持打开也没用，SQLite 另按路径解析，A→B→A 可让 connection 读到 B 而复核看到 A。
   222	- **①②的共同解法**：不再让 SQLite 碰路径——从**已验证的 fd** 读全量字节 → `sqlite3` 内存库 `deserialize()`。URI 转义问题与 ABA **一并消失**，且全程不落任何文件。实测：路径含 `#` 与 `?` 的 DB 正常只读（`read_mode: in_memory_deserialize_from_verified_fd`，16384 bytes）。
   223	- **BLOCKER③（根内末级 symlink）**：POSIX 规定 `rename`/`replace` **不解析末级 symlink**——`--out` 若是根内 symlink 指向根外，`realpath` 判"根外"而放行，但 replace 实际替换的是**根内那个目录项**。**整改**：containment 改用**父目录语义**（`dirname` 在根内即拒），叠加原有末级判定。实测：根内 symlink 作 `--out` → exit 2，symlink 未被替换。
   224	- **HIGH（扫描受阻拒绝不完整）**：no_token/token_conflict 分支在写入 `scan_errors` **之前**就早退；且拒绝条件写作 `scan_blocked and args.out`，**省略 `--out` 走 stdout 即可绕过**。**整改**：早退分支同样记录扫描错误；拒绝条件去掉 `and args.out`。实测：stdout 模式扫描受阻同样 exit 2。
   225	- **MEDIUM（tmp 残留 + 未 fsync 父目录）**：`os.replace` 在 `try` 外，`EXDEV/EBUSY/EACCES/ENOSPC` 会冒泡并留下 tmp。**整改**：replace 纳入 try，异常一律 `unlink` tmp；成功后 `fsync` 父目录使重命名落盘。
   226	
   227	round-8 整改后第八次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变、无 tmp 残留——八轮整改数字全程未变**。
   228	
   229	## §7j Codex round-9 裁定与收敛（声明改为有界，剩余项显式移交）
   230	
   231	round-9 维持分层裁定并给出"达到可验收的最小剩余项"清单。我的处置分两类：
   232	
   233	**已修（本轮完成）**
   234	
   235	- **必需⑤ 名实不符（DD-13 硬伤）**：改用内存 `deserialize` 后，字段仍叫 `opened_readonly`、docstring 仍称 SQLite URI `mode=ro`——**实际只有源 fd 只读，内存连接可写**。已改字段名为 `source_fd_opened_readonly`，docstring 如实说明只读保证的来源（源 fd 只读 + 内存副本与源解耦），补 `PRAGMA query_only=ON` 作纵深防御，并把 QA DB 的 `source_sha256` 写入台账（与证据包 shasum 一致）。
   236	- **必需④ 无测试引用生成器**：新增 `backend/tests/regression/test_census_dead_letter_readonly_contract.py`，把 8 轮审查中被实测封死的 **19 条**反例全部固化（每条注明对应轮次与 finding；覆盖构成如实标注于文件 docstring）。该测试**当场抓出一个真实回归**：round-7 改用 `os.replace` 发布后不再打开 `--out`，`S_ISREG` 门随之丢失，FIFO 会被静默替换成普通文件——已补回文件类型门（`--out` 若已存在且非常规文件、或是 symlink，一律拒绝）。**20 passed**（round-10 又补强了 4 处虚假通过窗口并新增 1 条 malformed DB 用例）。
   237	
   238	**改为有界声明（不再宣称已解决）**
   239	
   240	round-9 的必需①②③（一致性 SQLite 快照、单一稳定 dirfd 发布、tmp/发布者/状态绑定与单写者锁）是把这个**一次性 census 脚本**升级为**生产级并发安全工具**的要求。本卡不做，理由如实记录：本卡场景为单人本机、目录非共享可写；**"DB 静止"与"无并发写者"是操作者提供的前提，不是本卡证明的结论**（0 行 / 固定字节数 / 前后同 SHA 均不能证明读取期间无写者）。**处置方式是收敛声明而非假装达标**——报告头与验收单已删去"纯只读 / 唯一写出口 / 整类 TOCTOU 已消失"这类绝对化措辞，改为"本次运行输入 shasum 前后不变（已取证）+ 对 20+ 类误用路径 fail-closed（测试固化）+ 不声称敌意环境下的生产级安全"。
   241	
   242	**移交 follow-up（G4-10 复用本脚本前必须补齐）**
   243	
   244	| # | 项 | 触发条件 |
   245	|---|---|---|
   246	| FU-A | SQLite 一致性快照（backup API 或要求外部先冻结 DB）+ 显式拒绝 WAL/journal/并发变化 | DB 非静止时 |
   247	| FU-B | 输出发布全程相对同一 `O_DIRECTORY\|O_NOFOLLOW` dirfd（create/replace/fsync/unlink） | 输出目录可能被他人操纵时 |
   248	| FU-C | 不可预测 tmp 名 + 单写者锁/CAS + `published_but_durability_unconfirmed` 状态 + 崩溃残留 reconciliation | 共享可写目录或并发运行时 |
   249	| FU-D | `O_CLOEXEC`、拒绝空 basename、内存库完整性检查 | 建议项（round-9 列为 suggested） |
   250	
   251	round-9 整改后第九次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变、只读契约测试 19 passed——九轮整改数字全程未变**。
   252	
   253	## §7k Codex round-10 裁定与解阻整改
   254	
   255	round-10 首次明确：**「阻断原因不是必需①②③未实现」**——分类处置（修硬伤 + 固化测试 + 收敛声明 + 显式移交）被判定为**原则上可以收口**。剩余阻断项收敛为四条可执行要求，本轮全部完成：
   256	
   257	1. **彻底清除矛盾声明**：脚本模块 docstring 仍写 URI `mode=ro` 与"唯一写出口"（与同文件函数说明自相矛盾），报告 §4 与 UAT 亦仍称 `mode=ro`。已全部改写：模块契约段改述实际读法并新增"安全边界"段（可确证 / 不声称 / 前提三分），报告 §4 标题与正文同步。
   258	2. **修正字段语义**：`source_fd_opened_readonly` 原在 `deserialize` 成功后才置真——DB malformed 时 fd 确已只读打开却返回 false。已移到 fd 打开成功处。**该修正顺带暴露一个真 bug**：`deserialize` 是**延迟验证**，malformed DB 的 `DatabaseError` 在首次 `execute` 时才抛出，而查询段原本只有 `finally` 没有 `except`——**会炸掉整次 census**。已补 `sqlite3.Error` 捕获并记 `query_failed`，新增回归用例锁定。
   259	3. **如实标注测试覆盖**：原称"19 条反例全部固化 / 20+ 类路径"不实。现于测试文件 docstring 与本报告标注真实构成（**17 条行为测试跑真实 CLI + 3 条源码静态检查（弱证据）**，无 mock 无 skip），并修掉 round-10 点名的 4 处**虚假通过窗口**：FIFO 补验"仍是 FIFO 且无 tmp 残留"；扫描受阻补验 stdout 确无台账；坏 JSON 由 `A or B` 弱断言改为逐行精确断言（3 类坏行各一条）；输入不变测试从"DLQ + 单 transcript"扩展到 `--compare`、`--qa-metrics-db` 与根内全部文件。
   260	4. **补可绑定运行证据**：`readonly-contract-tests.txt` 由一行 `19 passed` 改为含精确命令、Python 版本、工作树 HEAD、**被测脚本与测试文件的 git blob**、脚本 sha256、覆盖构成声明与**逐项 PASSED 明细**。
   261	5. **"九次取证"表述收敛**：仓库只保留最新一对 before/after shasum，已改述为"本次留存一对，此前各轮亦逐次核对但未各存一份"。
   262	6. **"DB 静止"改为操作者前提**：0 行 / 固定 sha / 前后同 SHA 本身不能证明读取期间无写者——已在脚本"安全边界"段与本报告显式声明为**前提而非结论**。
   263	
   264	round-10 整改后第十次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变、只读契约测试 20 passed（17 行为 + 3 静态）——十轮整改数字全程未变**。
   265	
   266	**Codex 十轮裁定轨迹（如实留档）**：round-1 BLOCKED → round-2/3 部分闭合 → round-4/5/6 每轮揭示更深层缺陷（其中 round-6 与 round-7 两次触发架构级重做）→ round-7 起稳定为**分层裁定**「92 条冻结 ledger 可采信 / 生成器安全声明不可验收」→ round-10 明确「阻断不再要求补必需①②③，只需清除矛盾声明、修字段语义、如实标注测试覆盖、补可绑定证据」。本轮四条全部完成。
   267	
   268	## §7m Codex round-11 解阻整改（3 条必须再做项全部完成）
   269	
   270	round-11 重申「**无需补必需①②③**」，并把剩余阻断收敛为三条：
   271	
   272	1. **清除残留声明**（DB 静止当事实 / 逐次·运行零写入 / 整类绕过失效 / "20 个测试整体证明路径 fail-closed"）。已逐处改写：
   273	   - 脚本 docstring 中"本卡场景为单人本机、DB 静止（实测 0 行、16384 bytes），故不影响结论"→ 改为"该假定**由操作者保证**（行数为 0、字节数固定、前后 SHA 相同都**不能证明**读取期间没有并发写者）"。
   274	   - "对 20+ 类误用/攻击路径 fail-closed（回归测试固化）"→ 改为"**每条行为测试各自断言的那一个具体场景** fail-closed —— 这是逐例证据，**不构成**'所有误用路径均 fail-closed'的整体证明"。
   275	   - "整类绕过全部失效"→ 改为"'截断某个既有对象'这条**具体路径**不再存在（已就 hardlink / 根内 symlink / FIFO 三场景各自取证）；⚠️ 不等于声称所有别名类绕过已失效——`lstat`→`replace` 竞态等残余见 FU-B/FU-C"。UAT 同处过强表述一并修正。
   276	2. **测试补强**：坏 JSON 用例改为**直接断言原始 `unparseable_lines` 恰为三项**（不经 dict 压缩，避免同 line_no 覆盖掩盖重复条目）再逐条精确断言；输入不变测试加入**非 JSONL sentinel** 文件并覆盖 transcripts 根内**全部常规文件**（原只哈希 `*.jsonl`，与"覆盖根内全部文件"的说法不符）；测试 docstring 改为"**所有行为测试**的断言均针对真实文件系统效果"并补范围声明。
   277	3. **重跑并更新可绑定证据**：`readonly-contract-tests.txt` 已用新 script/test blob 重生成（脚本 blob `87266e09…`、测试 blob `541ec8b3…`，含各自 sha256 与逐项 PASSED 明细）。**20 passed**。
   278	
   279	round-11 整改后第十一次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变——十一轮整改数字全程未变**。
   280	
   281	## §7n Codex round-12 三层裁定与最后两条措辞整改
   282	
   283	round-12 首次给出**三层分别裁定**：
   284	
   285	| 层 | 裁定 | 依据 |
   286	|---|---|---|
   287	| (a) 92 条冻结 ledger | **PASS，可验收** | 从 exact raw DLQ 与 `records[]` 独立复算一致：92 条 / class 89-2-1 / byte_exact 4·approximate 88·unverifiable 0·unrecoverable 0 / 重复簇 6-29 / unparseable 0 / attribution_conflict 3 全为 `no_token` |
   288	| (b) 生成器（已声明有界前提下） | **PASS，可验收** | 前提明确为单人本机、非共享目录、DB 静止由操作者保证；坏 JSON、sentinel 与全部常规文件覆盖、测试范围声明均已补强，**未发现 round-11 所指虚假通过空间** |
   289	| 可绑定证据 | **PASS** | `f4112c2c` tree 中脚本/test blob 确为 `87266e09…`/`541ec8b3…`，独立 SHA-256 与证据一致，20 个 PASSED 名称与测试 blob 的 20 个函数逐项对应 |
   290	| (c) 报告与 UAT 声明 | **FAIL** | DB 静止与逐例测试措辞已收敛，但仍有非引述性过强断言（下述两条） |
   291	
   292	最后两条整改（Codex 明示"无需再改测试、脚本或重生成绑定证据"）：
   293	
   294	1. **"0 写入 / 逐次取证 / 输入零改动"→ 准确表述**：报告 §7 裁判表与 UAT 三处已统一改为"**本次留存的 before/after 样本 SHA 相同**；⚠️ 只证明**前后终态字节一致**，**不证明**读取期间零写入，也**不证明**每轮均留存独立证据（仓库只保留最新一对）"。判据名亦由"全程零写入/输入零改动"改为"**输入前后终态一致**"。
   295	2. **"五项绕过整类失效"→ 具体路径表述**：UAT round-7 行改为"「截断某个既有对象」这一**具体路径**不再存在，**不代表所有别名类绕过均已失效**（`lstat`→`replace` 竞态见 FU-B/FU-C）"。
   296	
   297	这两条的共同点与前十一轮一致：**证据支持的是"前后终态一致"与"某条具体路径消失"，我却写成了"零写入"与"整类失效"**。改的是措辞，不是结论——台账数字与脚本行为均未变动。
   298	
   299	round-12 整改后台账未重跑（本轮无脚本改动，`f4112c2c` 的 ledger 即最终版）：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0——十二轮整改数字全程未变**。

exec
/bin/zsh -lc "git -c core.quotePath=false diff --unified=40 f4112c2c 543e8a34 -- '_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
diff --git a/_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt b/_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt
index 9be8b423..a71e2031 100644
--- a/_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt
+++ b/_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt
@@ -1,21 +1,22 @@
 == CARD-G4-9 / CARD-G4-16 artifact commit receipt ==
 （commit 无法自含己身 SHA，故用本后置 receipt 精确绑定 —— Codex round-4 LOW 整改）
 
 37387a86  第五批开工基线（分析对象锚定 SHA，非本卡产物）
 67ccebe1  CARD-G4-9 初版交付（脚本/报告/台账/证据包/round-1 审查/UAT）
 e7a480eb  CARD-G4-16 初版交付（报告/证据包/两处注释修正/审查/UAT）
 73102875  round-2 findings 整改（两卡）
 fce0d8a2  round-3 findings 整改（两卡）
 94b420ff  CARD-G4-16 round-4 整改（重放 recipe 确定化）
 d2827a6d  CARD-G4-9 round-4 整改
 d8d887f2  本 receipt 首次落盘
 4c125f19  CARD-G4-9 round-5 整改
 5b371253  CARD-G4-9 round-6 架构级修复
 4ba4f847  receipt 补 round-5/6 链
 f389980c  CARD-G4-9 round-7 架构级修复（消除截断动作）
 af251e4a  CARD-G4-9 round-8 整改（QA DB 内存 deserialize / 父目录 containment / stdout 门 / 原子替换清理）
 2cdf77a4  receipt 补 round-8
 6b8debee  CARD-G4-9 round-9 整改（名实一致 / 只读契约回归测试 / 声明有界化）
-dfbe70c7  CARD-G4-9 round-10 解阻整改（矛盾声明全清 / 字段语义 / 测试如实标注 20 passed / 可绑定证据）
+dfbe70c7  CARD-G4-9 round-10 解阻整改（矛盾声明全清 / 字段语义 / 测试如实标注 / 可绑定证据）
+f4112c2c  CARD-G4-9 round-11 解阻整改（残留声明清除 / 坏 JSON 与输入不变测试补强 / 证据绑新 blob）
 
 各阶段交付物 blob 可用 git cat-file 复核；台账头部 dlq_file.sha256 为 DLQ 快照指纹。

exec
/bin/zsh -lc "git show '543e8a34:CURRENT_TASK.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
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
/bin/zsh -lc "git show '543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md' | nl -ba" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
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
    13	> 这张卡**没有修任何东西，也没有恢复任何数据**——它是一次"清点尸体"的只读普查（本次留存的 before/after 样本 SHA 相同——只说明前后终态一致，不证明读取期间零写入；安全边界见文末"诚实边界"段）：
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
    27	| 输入前后终态一致（裁判判据 e） | 运行前后**本次列出的输入**（四份 DLQ + qa_metrics.db）sha256 相同（diff 为空）。⚠️ 边界：这证明**前后终态字节一致**，**不证明**读取期间零写入；证据包只留存本次一对 before/after，**非每轮各存一份** | `_bmad-output/审查/G4-9-evidence/shasums-before.txt` / `shasums-after.txt` |
    28	| 脚本只读自证（判据 a） | import 行全 stdlib；neo4j/graphiti/bolt/app. import **0 命中**；`--apply` 定义 **0 命中**；**全文无任何截断调用**（写出走 O_EXCL 临时文件 + 原子替换） | `G4-9-evidence/grep-selfattest.txt` |
    29	| 只读契约回归测试（round-9 必需项④ + round-10 补强） | **20 passed**：**17 条行为测试**（subprocess 跑真实 CLI + 断言文件系统事实）+ **3 条源码静态检查**（弱证据，如实标注，不替代行为测试）。测试两次抓出真实问题：① 架构改动丢了文件类型门（FIFO 会被静默替换）；② `deserialize` 延迟验证使 malformed DB 炸掉整次 census。round-10 另修掉 4 处虚假通过窗口 | `backend/tests/regression/test_census_dead_letter_readonly_contract.py` |
    30	| live 挂载真相（判据 c） | 容器内 `sha256sum /app/data/dead_letter_episodes.jsonl` = 宿主 live 地址同值（92 行，`3b37460f…`）；compose :206-212 遮蔽史入报告 §1 | `G4-9-evidence/container-sha-check.txt` + 报告 §1 |
    31	| 分类零偏差（判据 b） | budget_400×**89** / schema×**2**（P0-4 已修，`entity_types.py:343`）/ group_id×**1**（sanitize 已兜，`group_id_compat.py:64`）——与勘探预期逐条一致，脚本 `class_deviation` 字段为空 | 台账 JSON `class_distribution` |
    32	| inline 完整性 + SHA 对账（判据 b） | 92/92 重算 sha256 对账：4 条 full_verified、88 条 truncated_prefix（`to_dict()` 的 `[:200]` 截断，`episode_worker.py:107`）、**0 条 anomaly** | 台账 JSON 逐条 `inline_state`/`sha_check` |
    33	| 源指针核销（判据 b，qa_metrics.db 源 fd 只读 + 内存副本） | `qa_error_logs` **0 行** → 0/92 可经 qa_metrics.db 溯源（诚实记录）；附加核销：llm_call_logs.db 无正文、outbox 空、episode_body_full 0 条；**有效源指针 = request_id 组内 session 归因 → 7 个 transcript 全部在盘实测存在** | 报告 §4 + 台账 `qa_metrics_probe` |
    34	| 可恢复性三态（判据 b） | 可字节级 **4** / 近似 **88** / 不可恢复 **0**；不可恢复清单显式成段 0 条、"待定" 0 条 | 报告 §5 + 台账 `recoverability_distribution` |
    35	| G4-10 稳定键（判据 d） | 逐条复合键 `{line_no, sha256_prefix, request_id}` + 台账头部冻结文件 sha；request_id 92 条仅 25 唯一值的实测证明单列不可作键 | 报告 §6 + 台账 `records[].stable_key` |
    36	| Codex 独立审查 round-1 | **BLOCKED**（3 BLOCKER：--out 可截断输入 / 快照不原子 / 交付物未冻结；3 HIGH：inline 判定 fail-open / request_id 归因传染 / transcript 归因折叠；3 MEDIUM + 4 LOW。同时确认：**当前 92 条数字逐项 0 mismatch**、class/三态/家族计数全对） | `_bmad-output/审查/codex-review-CARD-G4-9.md` |
    37	| Codex findings 逐条整改 | **13/13 完成**（见下）；整改版脚本负例门全过；全量重跑数字与整改前逐项一致 | 报告 §7/§7b + 证据包 |
    38	| Codex 复审 round-2 | **仍阻断**（10/13 CLOSED；BLOCKER-1/HIGH-1/HIGH-3 未真正闭合 + 3 新 LOW）。同时独立复算确认：67ccebe1 冻结生效、92 条数字与 6/29 重复簇全部可复算 | `_bmad-output/审查/codex-review-CARD-G4-9-round2.md`（codex 被 cyber 误拦，内容由 stdout 抢救存档） |
    39	| round-2 findings 逐条整改 | **6/6 完成**：inode 身份守卫封 hardlink+大小写别名 / full_body 长度门+anomaly 前置 / 不可读根 exit 2+symlink 逃逸拒采信 / 3 新 LOW。5 条新负例实测全过、正例无回归、数字仍逐项一致 | 报告 §7/§7c + `grep-selfattest.txt` |
    40	| Codex 复审 round-3 | **仍阻断**（4/6 CLOSED；BLOCKER-1/HIGH-3 判 PARTIAL + 1 新 MEDIUM + 2 新 LOW）。同时确认：HIGH-1 与三条 LOW 已闭合、台账数字有效且与 commit 字节一致 | `_bmad-output/审查/codex-review-CARD-G4-9-round3.md` |
    41	| round-3 findings 逐条整改 | **6/6 完成**：transcript 并入保护集 / O_NOFOLLOW+fstat 消 TOCTOU / os.walk 替 glob（不跟随目录 symlink+遍历错误显式捕获）/ 不可读候选 fail-closed / JSONL 严格 LF 分帧 / 非 dict 归 unparseable。6 条新反例实测全过、数字第三次不变 | 报告 §7d + `grep-selfattest.txt` |
    42	| Codex 复审 round-4 | **仍阻断**（1/6 CLOSED；2 新 BLOCKER + 1 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round4.md` |
    43	| round-4 findings 逐条整改 | **9/9 完成**：全候选入保护集 / 读侧 fd 身份消源侧 TOCTOU / 新增 unverifiable 第四态 / FIFO 设备门 / strict UTF-8 / 3 条错型与边界 LOW / provenance receipt。5 条新反例实测全过；第四次全量重跑数字仍不变 | 报告 §7e + `grep-selfattest.txt` |
    44	| Codex 复审 round-5 | **仍阻断**（3/8 CLOSED；2 BLOCKER + 2 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round5.md` |
    45	| round-5 findings 逐条整改 | **9/9 完成**：先扫描后判定（冲突候选亦入保护集）/ QA DB fd 身份+复核 / 可见性优先于 anomaly / fchmod 后置于碰撞检查 / QA DB 特殊文件门 / no_token 归 unverifiable / 3 条 LOW。6 条新反例实测全过；第五次全量重跑数字仍不变 | 报告 §7f |
    46	| Codex 复审 round-6 | **6/9 CLOSED**（visibility 优先/fchmod 顺序/no_token 语义/3 条 LOW 已闭合）；剩 2 BLOCKER + 1 MEDIUM 揭示保护集**依赖枚举完整性**的架构缺陷 + 3 新发现 | `_bmad-output/审查/codex-review-CARD-G4-9-round6.md` |
    47	| round-6 findings 整改 | **架构级修复 + 6 项**：新增不依赖枚举的**路径层防御**（--out 禁落 transcripts 根内 / 禁等于任一输入 realpath）、QA DB 验证 fd 保持打开至复核完毕、no_token 亦扫描、证据包重生成、ledger 冲突原因自描述、lone surrogate 回退。反例实测：0333 隐藏目录内 transcript 作 --out → exit 2 完好 | 报告 §7g |
    48	| Codex 复审 round-7 | **关键裁定分离**："92 条冻结 ledger **可以采信**；生成器与 UAT 的纯只读安全声明不可验收"——卡面 census 判据已满足，阻断全在工具安全承诺侧。1 BLOCKER（大小写别名根，无需竞态）+ 4 项路径 TOCTOU + 1 MEDIUM（非原子写）+ 2 LOW | `_bmad-output/审查/codex-review-CARD-G4-9-round7.md` |
    49	| round-7 findings 整改 | **架构级第二次修复**：写出改 O_EXCL 临时文件+fsync+os.replace（**全文再无 ftruncate 调用**）——「截断某个既有对象」这一**具体路径**不再存在，**不代表所有别名类绕过均已失效**（lstat→replace 竞态见 FU-B/FU-C）；containment 改 inode 逐级比较（normcase 在 POSIX 是恒等函数，我的假设错了）；扫描受阻直接拒绝写出。实测：根外 hardlink 指向根内 transcript 作 --out → 源内容完好 | 报告 §7h |
    50	| Codex 复审 round-8 | 重申裁定分离：**「可验收：92 条冻结 ledger snapshot；不可验收：生成器一般安全性与 UAT 的纯只读声明」**。3 新 BLOCKER（SQLite URI 未转义 #/? / QA DB 仍按 pathname 开可 ABA / 根内末级 symlink 因 rename 不解析而被替换）+ 1 HIGH + 1 MEDIUM | `_bmad-output/审查/codex-review-CARD-G4-9-round8.md` |
    51	| round-8 findings 整改 | **6/6 完成**：QA DB 改「已验证 fd 读字节 → 内存库 deserialize」（URI 转义与 ABA 一并消失，含 #? 路径实测通过）；containment 加父目录语义（POSIX rename 不解析末级 symlink）；扫描受阻去掉 and args.out（stdout 模式亦拒）；replace 纳入 try + fsync 父目录 | 报告 §7i |
    52	| Codex 复审 round-9/10 | round-9 给出「最小剩余项」5 条；round-10 首次明确**「阻断不再要求补必需①②③」**，收敛为 4 条可执行要求：清除矛盾声明 / 修字段语义 / 如实标注测试覆盖 / 补可绑定证据。且十轮均确认 **92 条冻结 ledger 可验收** | `codex-review-CARD-G4-9-round9.md` / `-round10.md` |
    53	| round-10 解阻整改 | **6/6 完成**：脚本+报告+UAT 的 `mode=ro` 与「唯一写出口/全程零写入」矛盾表述全清（残留均为「已废弃」引述）；`source_fd_opened_readonly` 移到 fd 打开处（**顺带修出真 bug**：deserialize 延迟验证使 malformed DB 炸掉整次 census）；测试覆盖如实标注 17 行为+3 静态并修掉 4 处虚假通过窗口；证据补 HEAD/blob/sha256/逐项明细；「九次取证」与「DB 静止」改为准确表述与操作者前提 | 报告 §7k/§7l |
    54	| Codex 复审 round-11 | 重申**无需补必需①②③**；剩余阻断收敛为 3 条：清残留声明 / 坏 JSON 与输入不变测试补强 / 用新 blob 更新证据 | `codex-review-CARD-G4-9-round11.md` |
    55	| round-11 解阻整改 | **3/3 完成**：DB 静止改为操作者前提（0 行·固定字节·同 SHA 均不能证明无并发写者）、"20 类路径 fail-closed"改为逐例证据声明、"整类绕过失效"改为具体路径消失+残余竞态登记；坏 JSON 直接断言原始列表恰 3 项、输入不变测试加非 JSONL sentinel 并覆盖根内全部常规文件；证据绑定新 blob（脚本 87266e09/测试 541ec8b3）。20 passed | 报告 §7m |
    56	| Codex 复审 round-12（三层裁定） | **(a) 92 条冻结 ledger：PASS 可验收**（独立复算逐项一致）；**(b) 生成器在已声明有界前提下：PASS 可验收**（未发现虚假通过空间）；**可绑定证据：PASS**（blob/SHA/20 项名称逐项对应）；**(c) 报告与 UAT 声明：FAIL** —— 仅剩两条过强措辞 | `codex-review-CARD-G4-9-round12.md` |
    57	| round-12 措辞整改 | **2/2 完成**（Codex 明示无需再改测试/脚本/证据）："0 写入·逐次取证·输入零改动"统一改为"本次留存 before/after 样本 SHA 相同；不证明读取期间零写入、不证明每轮各存证据"；"五项绕过整类失效"改为"『截断既有对象』这一具体路径不再存在，不代表所有别名类绕过均已失效" | 报告 §7n |
    58	| 独立 Workflow 4-agent 复核 | G4-9 数字 agent：92 条重算 **0 mismatch**（class/inline/三态/25 request_id/7 transcript 在盘/台账 sha 全 CONFIRMED，仅 2 处描述区间 REFUTED 已修正）；只读契约 agent：与 Codex 同源的 3 条 blocker（已随上整改） | Workflow wf_737b1a95-20b journal |
    59	
    60	## 🔧 Codex round-1 整改记录（13/13 关闭，BLOCKED → 整改完毕）
    61	
    62	- **BLOCKER-1 --out 截断风险**：任意 --out 路径 "w" 无守卫，可覆盖 DLQ 自身（双审查独立实测复现）。整改：写前 resolve() 路径碰撞守卫，命中输入集合即 exit 2；负例实测拒绝、DLQ 完好。
    63	- **BLOCKER-2 快照不原子**：records 与头部 sha 来自两次读取。整改：单次 read_bytes()，头部与逐条同源同字节。
    64	- **BLOCKER-3 交付物漂移**：审查期间脚本/报告 sha 变化且未 track。整改：本卡 commit 冻结全部 exact bytes；自证文件内嵌脚本 sha 前缀。
    65	- **HIGH-1 inline 判定 fail-open**：sha 匹配但长度不符会误判 full_verified（反例实测）。整改：长度精确匹配门 + 64-hex 合法性门 + anomaly 一律 fail-closed（unrecoverable + 如实 basis）。
    66	- **HIGH-2 request_id 归因传染**：缺失值合入 "None" 组、跨类型合组、多 token 静默取长。整改：(类型,值) 复合键 + 缺失单条成组 + 前缀一致门（冲突拒采信）。
    67	- **HIGH-3 transcript 归因折叠**：多命中照单全收、目录缺失误判 unrecoverable=88（实测复现）。整改：恰 1 常规文件命中门 + 递归 glob + 目录缺失 exit 2 拒诊。
    68	- **MEDIUM-1~3**：episode_body_full 采信通路 / duplicate_clusters 6 簇 29 行 + reference_time 透传 / privacy 字段与 private-only 声明。
    69	- **LOW-1~4**：两处区间修正（16948–20831、205–8036）/ 稳定键语义重写为"冻结快照 occurrence key" / schema 双处证据（LearningConcept.name + LearningTip.created_at）/ 挂载历史证据边界声明。
    70	
    71	整改后全量重跑：92 条数字与整改前**逐项一致**（4/88/0、89/2/1、冲突 0、unparseable 0）——整改只收紧契约与通用鲁棒性，不改变本次 census 结论。
    72	
    73	## 🔧 Codex round-2 复审整改记录（10/13 CLOSED → 剩 3 项 + 3 新 LOW 全关闭）
    74	
    75	round-2 用真实入口反例证明我 round-1 的三处整改**没有真正闭合**（这正是二轮审查的价值）：
    76	
    77	- **BLOCKER-1 未闭合**：守卫比的是路径字符串，**hardlink 与大小写别名照样截断 DLQ**。→ 改比**文件 inode 身份**；两种绕过实测双双 exit 2、DLQ sha 不变。
    78	- **HIGH-1 未闭合**：`episode_body_full` 分支只核 sha 不核长度且排在 anomaly 之前，**anomaly 记录能翻案成"可字节级恢复"**。→ 加长度门 + 判定顺序改为 anomaly 优先；反例实测翻转。
    79	- **HIGH-3 未闭合**：`chmod 000` 的目录仍 exit 0 并把全部记录**假判不可恢复**；symlink 可指到目录外冒充源。→ 不可读即 exit 2；symlink 与逃逸目标一律不采信；正例（真实唯一命中）无回归。
    80	- **3 新 LOW**：full_verified 长度范围修正 131–180；台账三个 distribution 补零并新增 `inline_state_distribution`；`line_count` 与 records 改用同一 `splitlines()` 口径。
    81	
    82	round-2 整改后再次全量重跑：92 条、4/88/0、89/2/1、6 簇 29 行、shasum 不变——**数字全程未变**。
    83	
    84	## 🔧 Codex round-3 复审整改记录（4/6 CLOSED → 剩 2 项 + 3 新发现全关闭）
    85	
    86	round-3 确认 HIGH-1 与三条 LOW 真正闭合、台账数字有效，又在两项路径安全上找到更深的绕过：
    87	
    88	- **BLOCKER-1 仍 PARTIAL**：① 保护集漏了**归因到的 transcript**——`--out` 指向它会截断恢复源；② check-then-open 的 **TOCTOU** 仍在。→ ① transcript 写前并入保护集；② 改 `O_NOFOLLOW` 打开且**不带 O_TRUNC**，对实际 fd `fstat` 校验后才 `ftruncate`。反例实测：exit 2、transcript 完好。
    89	- **HIGH-3 仍 PARTIAL**：Python 3.14 的 `glob` 在过滤前就已递归、跟随目录 symlink 且**静默吞掉不可读子树错误**；mode 000 的文件仍过 `isfile()` 被当可用源。→ 改 `os.walk(onerror=, followlinks=False)` + `os.access(R_OK)` 门；遍历受阻或有不可读候选一律拒绝裁定。三反例实测 fail-closed。
    90	- **新 MEDIUM（JSONL 分帧）**：`splitlines()` 会把含 U+2028 的合法单行记录劈成两条坏行。→ 严格按 LF 分帧，header 与 records 共用同一函数。
    91	- **新 LOW ×2**：非 dict JSON（`null`/数组）归 unparseable 不再炸全量；报告头补 artifact commit 链。
    92	
    93	round-3 整改后第三次全量重跑：**92 条、4/88/0、89/2/1、6/29、shasum 不变——三轮整改数字全程未变**，改的全是通用鲁棒性与路径安全。
    94	
    95	## 🔧 Codex round-4 复审整改记录（1/6 CLOSED → 9 项全关闭）
    96	
    97	round-4 只认 1 项闭合，用更深的反例推翻其余"闭合"——两条新 BLOCKER 都是真的：
    98	
    99	- **不可读但可写（mode 0200）的 transcript 绕过保护集**：我在"不可读"分支把候选路径清空了，于是它没进保护集，`--out` 指向它照样截断——不需要任何竞态。→ 新增"全候选清单"，无论可读与否一律并入保护集。
   100	- **源侧 TOCTOU**：保护身份按路径 stat 采集、DLQ 稍后才按路径读取，中间可换 inode。→ 改为**从 fd 读取**：打开一次 → `fstat` 取身份 → 从同一 fd 读全量，保护的就是实际读到的那个对象。
   101	- **把"看不见"说成"不可恢复"**：扫描受阻时仍输出 `unrecoverable`，与报告里"既不宣称不可恢复"自相矛盾。→ 新增第四态 **`unverifiable`**，逐条写明是遍历受阻还是候选不可读。
   102	- **其余 5 项**：FIFO/设备节点门（`O_NONBLOCK`+`S_ISREG`）、非法 UTF-8 不再经 replace 冒充有效记录（strict decode）、三条错型与边界 LOW（`name=None`/`request_id=[]`/根为 `/`）、既有输出文件 `fchmod` 收紧（台账现为 `-rw-------`）、provenance 改后置 receipt 绑定精确 commit 链。
   103	
   104	round-4 整改后第四次全量重跑：**92 条、4/88/0（unverifiable 0）、89/2/1、6/29、shasum 不变——四轮整改数字全程未变**。
   105	
   106	## 🔧 Codex round-5 复审整改记录（3/8 CLOSED → 9 项全关闭）
   107	
   108	round-5 继续深挖，两条新 BLOCKER 与两条 HIGH 都成立：
   109	
   110	- **冲突组的候选没进保护集**：token 冲突时我在扫描**之前**就早退了，那些候选从没被看到，`--out` 指向它们照样截断。→ 改成**先扫描后判定**，无论最终是否采信，见到的候选一律进保护集。
   111	- **qa_metrics.db 身份没绑定实际读取**：先按路径 stat、SQLite 稍后按路径重开，中间可换。→ 改 fd 取身份 + 打开后复核身份一致。
   112	- **anomaly 吞掉了"看不见"**：`anomaly→unrecoverable` 排在可见性判断之前，扫描受阻时仍断言"不可恢复"。→ 判定链改为**可见性优先**。
   113	- **`fchmod` 排在碰撞检查之前**：`--out` 指向受保护的只读输入时，会先把它的权限从 644 改成 600 才发现碰撞——字节没丢但输入被改了。→ 碰撞检查前移。
   114	- **其余 5 项**：QA DB 特殊文件门、无 token 归 `unverifiable`、单独换行算 1 空行、strict encode 堵住 lone surrogate 伪造 `full_verified`、`bool` 不再通过长度门。
   115	
   116	**一处计数如实变化**：归因冲突 0→3。因为"名字不含 session token"现在被诚实标为"未做归因扫描"，正是那 3 条 callout 记录；它们 inline 全量、不依赖 transcript，仍是可字节级恢复。**三态分布不变**（4/88/0/0）——是标注变诚实，不是结论变化。
   117	
   118	round-5 整改后第五次全量重跑：**92 条、4/88/0/0、89/2/1、6/29、shasum 不变——五轮整改数字全程未变**。
   119	
   120	## 🔧 Codex round-6 复审整改记录（6/9 CLOSED → 架构级修复）
   121	
   122	round-6 指出了一个我补丁修不掉的根因：**保护集依赖"能不能枚举到"**。不可列举但可穿越的目录（`0333`）里的 transcript，`os.walk` 看不见，就进不了保护集，`--out` 指向它照样截断；QA DB 的 inode 被 A→B→A 换过也一样。
   123	
   124	→ 改为**双层防御**：在 inode 保护集之外，加一层**不依赖枚举**的路径判断——`--out` 的真实路径不得落在 transcripts 根目录内（整个恢复源区域禁写），也不得等于任何输入文件的真实路径。实测：隐藏目录内的 transcript 作 `--out`，inode 保护集根本没看见它，路径层直接拦住，exit 2、文件完好。
   125	
   126	另修：QA DB 的验证 fd 改为**保持打开**到复核完毕（堵 ABA）；`no_token` 分支也扫描（原本完全不扫，候选进不了保护集）；证据包每轮重生成（round-6 指出我的 self-attest 停留在 round-4 的旧 SHA，属实）；台账新增冲突原因自描述。
   127	
   128	round-6 整改后第六次全量重跑：**92 条、4/88/0/0、89/2/1、6/29、shasum 不变——六轮整改数字全程未变**。
   129	
   130	## 🔧 Codex round-7 复审整改记录（关键裁定分离 + 架构级第二次修复）
   131	
   132	round-7 把结论分成了两半，这个区分很重要：
   133	
   134	> **「现有 92 条冻结 ledger 可以采信；生成器与 UAT 的纯只读安全声明不可验收。」**
   135	
   136	也就是说：这张卡要交付的 census 结论（92 条的分类、对账、三态、挂载真相、稳定键，以及输入前后终态字节一致）**已经过关**；卡住的是"这个脚本作为工具，其只读承诺是否经得起敌意输入"。
   137	
   138	- **一个无需竞态的真实绕过**：大小写不敏感卷上 `/Users/...` 与 `/users/...` 是同一个目录但 realpath 字符串不同，我 round-6 用来防御的 `os.path.normcase` **在 macOS/Linux 上根本是恒等函数**——这是我的知识性错误。改成逐级比较 **inode 身份**，不再依赖任何字符串。
   139	- **五项绕过共用一个根源**：它们都依附于"截断一个已存在的文件"这个动作。改成「新建临时文件 → 写 → fsync → 原子替换」后，脚本**全文再没有任何截断调用**——"截断某个既有对象"这条**具体路径**不复存在，"崩溃留下半个台账"的风险也一并消除。实测：拿一个指向恢复源的 hardlink 当 `--out`，台账正常写出，而**源文件内容一个字节没变**。⚠️ 这**不等于**"所有别名类绕过都已失效"：`lstat`→`replace` 之间仍有竞态窗口，已登记 FU-B/FU-C。
   140	- **扫描受阻不再只是标记**：看不全就意味着保护集不完整，现在直接拒绝写出台账。
   141	
   142	round-7 整改后第七次全量重跑：**92 条、4/88/0/0、89/2/1、6/29、shasum 不变、台账 0600、无临时文件残留——七轮整改数字全程未变**。
   143	
   144	## 🔧 Codex round-8 复审整改记录（裁定分离重申 + 3 BLOCKER 全闭）
   145	
   146	round-8 把结论说得更清楚了：**「可验收：92 条冻结 ledger snapshot。不可验收：生成器的一般安全性，以及验收单里那句"纯只读、唯一写出口、整类 TOCTOU 已消失"」**。
   147	
   148	三条新 BLOCKER 都成立，其中两条有同一个彻底解法：
   149	
   150	- **SQLite 打开方式**：`file:路径?mode=ro` 这种写法，路径里只要有个 `#`，`mode=ro` 就掉进 URI 的 fragment 被忽略，SQLite 可能按默认的**读写模式**打开——这直接推翻"唯一写出口"。而且就算持有验证过的文件描述符，SQLite 还是按路径自己去开，中间被换掉也发现不了。→ 改成从**已验证的文件描述符读出全部字节，灌进内存数据库**。SQLite 从此不碰路径，两个问题一起消失。
   151	- **根内的软链接**：POSIX 规定重命名操作**不跟随末级软链接**。所以 `--out` 如果是恢复源目录里的一个软链接（指向外面），我按"它指向哪"判断会放行，但实际被替换的是**目录里那个链接本身**。→ 判定改看**父目录在不在恢复源里**。
   152	- **stdout 模式漏网**：扫描受阻的拒绝条件我写成了"且指定了 --out"，于是省略 `--out` 就能绕过。→ 去掉该条件。
   153	
   154	round-8 整改后第八次全量重跑：**92 条、4/88/0/0、89/2/1、6/29、shasum 不变、无 tmp 残留——八轮整改数字全程未变**。
   155	
   156	## 📄 交付物清单（全部新增，零业务代码改动）
   157	
   158	- `backend/scripts/census_dead_letter_episodes.py` — 唯一代码产物（只读 census 脚本，纯 stdlib）
   159	- `_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md` — census 报告（挂载真相/分类/三态/交接契约）
   160	- `_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json` — 92 条逐条台账（G4-10 消费）
   161	- `_bmad-output/审查/G4-9-evidence/` — 证据包（shasums ×2、grep 自证、容器 sha 实测、运行日志）
   162	- `_bmad-output/审查/codex-review-CARD-G4-9.md` — Codex 独立审查存档
   163	
   164	## 📐 诚实边界（round-9 收敛，替代原先过强的措辞）
   165	
   166	九轮对抗审查后，Codex 始终维持一个分层裁定：**「92 条冻结台账可以采信；但生成器的一般安全性、以及验收单里"纯只读、唯一写出口、整类 TOCTOU 已消失"这类绝对化声明不可验收」**。
   167	
   168	我接受这个区分，处置是**把声明改准确，而不是假装达标**：
   169	
   170	- **可以确证的**：本次运行对**本次列出的输入文件**（4 份 DLQ + qa_metrics.db）**shasum 前后逐字节不变**（证据包留存本次一对 before/after）；回归测试中**每条行为测试各自断言的那个场景** fail-closed（17 行为 + 3 静态）——**逐例证据，非"所有路径都安全"的整体证明**。
   171	- **前提（非结论）**："DB 静止"由操作者保证——0 行、固定 sha、前后同 SHA 本身**不能证明**读取期间没有并发写者。
   172	- **不再声称的**：在共享可写目录、有并发写者、SQLite DB 正被写入等**敌意环境**下具备生产级安全；也不声称"整类别名绕过已消失"（`lstat`→`replace` 竞态等残余见 FU-B/FU-C）。这类保证需要一致性快照、dirfd 相对发布、单写者锁——是把一次性 census 脚本升级为常驻工具的工作量，不在本卡范围。
   173	- **已登记的**：FU-A~FU-D 四项（报告 §7j），**G4-10 若复用本脚本于活跃 DB 或共享目录，须先补齐**。
   174	
   175	## ⏭️ 移交（不在本卡范围）
   176	
   177	- **G4-10**：89 条 budget_400 根因修复（16384 context 超限 → 切块或提 budget）+ 按台账重放；3 条 `vault:default` 旧格式重放前需 group 重映射。
   178	- **DeadLetterStore 全量正文开关**：`DEAD_LETTER_STORE_FULL_BODY` live 未启用是 88 条只剩前缀的直接原因——是否开启（隐私 vs 可恢复性权衡）留 G4-10 连根因一并裁。

exec
/bin/zsh -lc "git show '543e8a34:CLAUDE.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
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

**Identifying potential overclaim discrepancies**
**Planning comprehensive keyword grep and diff analysis**
exec
/bin/zsh -lc "git -c core.quotePath=false grep -n -I -E '(0[[:space:]]*写入|零写入|无写入|不写入|逐次取证|逐轮取证|每轮取证|每轮.*证据|均留存|整类.*(绕过|失效|消失)|所有.*(误用|路径).*(fail.?closed|安全|失效|消失)|DB.*静止|静止.*DB|全程零|输入零改动|纯只读|只读安全|唯一写出口)' 543e8a34 -- '_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md' '_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:5:> **只读声明的准确边界（round-9 收敛，见 §7j）**: 本次运行对**本次列出的输入文件**（4 份 DLQ + qa_metrics.db）shasum 前后不变（证据包留有本次 before/after 一对，非九轮各存一对）；回归测试中**每条行为测试各自断言的那个具体场景** fail-closed（17 条跑真实 CLI + 3 条源码静态检查）——这是**逐例证据**，不构成"所有误用路径均 fail-closed"的整体证明。但**不声称**在共享可写目录、并发写者、活跃 SQLite DB 等敌意环境下具备生产级安全——剩余必需项见 §7j 清单。
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:92:| 运行前后 shasum（live/主仓/孤儿①/孤儿② 四份 DLQ + qa_metrics.db） | `diff shasums-before.txt shasums-after.txt` 空 → **本次留存的 before/after 样本 SHA 相同**。⚠️ 该证据只证明**前后终态字节一致**，**不证明**读取期间零写入，也**不证明**每轮均留存了独立证据（仓库只保留最新一对） |
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:200:> **「现有 92 条冻结 ledger 可以采信；CARD-G4-9 生成器与 UAT 的纯只读安全声明不可验收。」**
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:202:即：卡面的 census 判据（分类/对账/三态/挂载真相/稳定键/shasum 不变）已满足且被独立复算确认；阻断项全部落在"生成器作为工具的只读安全承诺"上。逐条整改：
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:205:- **NOT-CLOSED ×4（根外 hardlink 指向隐藏目录内 transcript / 根 retarget TOCTOU / 检查后换父目录 symlink 或 basename hardlink）+ MEDIUM（非原子写）**：这五项依附于同一个动作——**截断一个已存在的文件**。**架构级修复**：写出改为「同目录 `O_EXCL` 新建临时文件 → 写 → `fsync` → `os.replace` 原子替换」，**全文再无任何 `ftruncate` 调用**。`O_EXCL` 保证写入目标是本进程新建的对象，因此"截断既有对象"这条具体路径消失（三场景各自取证，不声称整类绕过均已失效）；`os.replace` 同时消除崩溃/ENOSPC 留下部分台账的风险。实测：根外 hardlink 指向根内 transcript 作 `--out` → 台账正常写出而**源文件内容完好**（`os.replace` 只重绑定该名字，不触碰底层 inode）。
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:216:> **可验收：92 条冻结 ledger snapshot。不可验收：当前生成器的一般安全性，以及 UAT 的"纯只读、唯一写出口、整类 TOCTOU 已消失"声明。**
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:220:- **BLOCKER①（SQLite URI 未转义）**：`file:{db_path}?mode=ro` 在路径含 `#` 时，`mode=ro` 会落进被忽略的 URI fragment，SQLite 可能按**默认读写模式**打开——直接反驳"唯一写出口"。
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:240:round-9 的必需①②③（一致性 SQLite 快照、单一稳定 dirfd 发布、tmp/发布者/状态绑定与单写者锁）是把这个**一次性 census 脚本**升级为**生产级并发安全工具**的要求。本卡不做，理由如实记录：本卡场景为单人本机、目录非共享可写；**"DB 静止"与"无并发写者"是操作者提供的前提，不是本卡证明的结论**（0 行 / 固定字节数 / 前后同 SHA 均不能证明读取期间无写者）。**处置方式是收敛声明而非假装达标**——报告头与验收单已删去"纯只读 / 唯一写出口 / 整类 TOCTOU 已消失"这类绝对化措辞，改为"本次运行输入 shasum 前后不变（已取证）+ 对 20+ 类误用路径 fail-closed（测试固化）+ 不声称敌意环境下的生产级安全"。
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:246:| FU-A | SQLite 一致性快照（backup API 或要求外部先冻结 DB）+ 显式拒绝 WAL/journal/并发变化 | DB 非静止时 |
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:257:1. **彻底清除矛盾声明**：脚本模块 docstring 仍写 URI `mode=ro` 与"唯一写出口"（与同文件函数说明自相矛盾），报告 §4 与 UAT 亦仍称 `mode=ro`。已全部改写：模块契约段改述实际读法并新增"安全边界"段（可确证 / 不声称 / 前提三分），报告 §4 标题与正文同步。
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:262:6. **"DB 静止"改为操作者前提**：0 行 / 固定 sha / 前后同 SHA 本身不能证明读取期间无写者——已在脚本"安全边界"段与本报告显式声明为**前提而非结论**。
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:266:**Codex 十轮裁定轨迹（如实留档）**：round-1 BLOCKED → round-2/3 部分闭合 → round-4/5/6 每轮揭示更深层缺陷（其中 round-6 与 round-7 两次触发架构级重做）→ round-7 起稳定为**分层裁定**「92 条冻结 ledger 可采信 / 生成器安全声明不可验收」→ round-10 明确「阻断不再要求补必需①②③，只需清除矛盾声明、修字段语义、如实标注测试覆盖、补可绑定证据」。本轮四条全部完成。
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:272:1. **清除残留声明**（DB 静止当事实 / 逐次·运行零写入 / 整类绕过失效 / "20 个测试整体证明路径 fail-closed"）。已逐处改写：
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:273:   - 脚本 docstring 中"本卡场景为单人本机、DB 静止（实测 0 行、16384 bytes），故不影响结论"→ 改为"该假定**由操作者保证**（行数为 0、字节数固定、前后 SHA 相同都**不能证明**读取期间没有并发写者）"。
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:274:   - "对 20+ 类误用/攻击路径 fail-closed（回归测试固化）"→ 改为"**每条行为测试各自断言的那一个具体场景** fail-closed —— 这是逐例证据，**不构成**'所有误用路径均 fail-closed'的整体证明"。
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:275:   - "整类绕过全部失效"→ 改为"'截断某个既有对象'这条**具体路径**不再存在（已就 hardlink / 根内 symlink / FIFO 三场景各自取证）；⚠️ 不等于声称所有别名类绕过已失效——`lstat`→`replace` 竞态等残余见 FU-B/FU-C"。UAT 同处过强表述一并修正。
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:288:| (b) 生成器（已声明有界前提下） | **PASS，可验收** | 前提明确为单人本机、非共享目录、DB 静止由操作者保证；坏 JSON、sentinel 与全部常规文件覆盖、测试范围声明均已补强，**未发现 round-11 所指虚假通过空间** |
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:290:| (c) 报告与 UAT 声明 | **FAIL** | DB 静止与逐例测试措辞已收敛，但仍有非引述性过强断言（下述两条） |
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:294:1. **"0 写入 / 逐次取证 / 输入零改动"→ 准确表述**：报告 §7 裁判表与 UAT 三处已统一改为"**本次留存的 before/after 样本 SHA 相同**；⚠️ 只证明**前后终态字节一致**，**不证明**读取期间零写入，也**不证明**每轮均留存独立证据（仓库只保留最新一对）"。判据名亦由"全程零写入/输入零改动"改为"**输入前后终态一致**"。
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:295:2. **"五项绕过整类失效"→ 具体路径表述**：UAT round-7 行改为"「截断某个既有对象」这一**具体路径**不再存在，**不代表所有别名类绕过均已失效**（`lstat`→`replace` 竞态见 FU-B/FU-C）"。
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:297:这两条的共同点与前十一轮一致：**证据支持的是"前后终态一致"与"某条具体路径消失"，我却写成了"零写入"与"整类失效"**。改的是措辞，不是结论——台账数字与脚本行为均未变动。
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:13:> 这张卡**没有修任何东西，也没有恢复任何数据**——它是一次"清点尸体"的只读普查（本次留存的 before/after 样本 SHA 相同——只说明前后终态一致，不证明读取期间零写入；安全边界见文末"诚实边界"段）：
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:27:| 输入前后终态一致（裁判判据 e） | 运行前后**本次列出的输入**（四份 DLQ + qa_metrics.db）sha256 相同（diff 为空）。⚠️ 边界：这证明**前后终态字节一致**，**不证明**读取期间零写入；证据包只留存本次一对 before/after，**非每轮各存一份** | `_bmad-output/审查/G4-9-evidence/shasums-before.txt` / `shasums-after.txt` |
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:48:| Codex 复审 round-7 | **关键裁定分离**："92 条冻结 ledger **可以采信**；生成器与 UAT 的纯只读安全声明不可验收"——卡面 census 判据已满足，阻断全在工具安全承诺侧。1 BLOCKER（大小写别名根，无需竞态）+ 4 项路径 TOCTOU + 1 MEDIUM（非原子写）+ 2 LOW | `_bmad-output/审查/codex-review-CARD-G4-9-round7.md` |
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:50:| Codex 复审 round-8 | 重申裁定分离：**「可验收：92 条冻结 ledger snapshot；不可验收：生成器一般安全性与 UAT 的纯只读声明」**。3 新 BLOCKER（SQLite URI 未转义 #/? / QA DB 仍按 pathname 开可 ABA / 根内末级 symlink 因 rename 不解析而被替换）+ 1 HIGH + 1 MEDIUM | `_bmad-output/审查/codex-review-CARD-G4-9-round8.md` |
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:53:| round-10 解阻整改 | **6/6 完成**：脚本+报告+UAT 的 `mode=ro` 与「唯一写出口/全程零写入」矛盾表述全清（残留均为「已废弃」引述）；`source_fd_opened_readonly` 移到 fd 打开处（**顺带修出真 bug**：deserialize 延迟验证使 malformed DB 炸掉整次 census）；测试覆盖如实标注 17 行为+3 静态并修掉 4 处虚假通过窗口；证据补 HEAD/blob/sha256/逐项明细；「九次取证」与「DB 静止」改为准确表述与操作者前提 | 报告 §7k/§7l |
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:55:| round-11 解阻整改 | **3/3 完成**：DB 静止改为操作者前提（0 行·固定字节·同 SHA 均不能证明无并发写者）、"20 类路径 fail-closed"改为逐例证据声明、"整类绕过失效"改为具体路径消失+残余竞态登记；坏 JSON 直接断言原始列表恰 3 项、输入不变测试加非 JSONL sentinel 并覆盖根内全部常规文件；证据绑定新 blob（脚本 87266e09/测试 541ec8b3）。20 passed | 报告 §7m |
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:57:| round-12 措辞整改 | **2/2 完成**（Codex 明示无需再改测试/脚本/证据）："0 写入·逐次取证·输入零改动"统一改为"本次留存 before/after 样本 SHA 相同；不证明读取期间零写入、不证明每轮各存证据"；"五项绕过整类失效"改为"『截断既有对象』这一具体路径不再存在，不代表所有别名类绕过均已失效" | 报告 §7n |
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:134:> **「现有 92 条冻结 ledger 可以采信；生成器与 UAT 的纯只读安全声明不可验收。」**
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:146:round-8 把结论说得更清楚了：**「可验收：92 条冻结 ledger snapshot。不可验收：生成器的一般安全性，以及验收单里那句"纯只读、唯一写出口、整类 TOCTOU 已消失"」**。
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:150:- **SQLite 打开方式**：`file:路径?mode=ro` 这种写法，路径里只要有个 `#`，`mode=ro` 就掉进 URI 的 fragment 被忽略，SQLite 可能按默认的**读写模式**打开——这直接推翻"唯一写出口"。而且就算持有验证过的文件描述符，SQLite 还是按路径自己去开，中间被换掉也发现不了。→ 改成从**已验证的文件描述符读出全部字节，灌进内存数据库**。SQLite 从此不碰路径，两个问题一起消失。
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:166:九轮对抗审查后，Codex 始终维持一个分层裁定：**「92 条冻结台账可以采信；但生成器的一般安全性、以及验收单里"纯只读、唯一写出口、整类 TOCTOU 已消失"这类绝对化声明不可验收」**。
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:170:- **可以确证的**：本次运行对**本次列出的输入文件**（4 份 DLQ + qa_metrics.db）**shasum 前后逐字节不变**（证据包留存本次一对 before/after）；回归测试中**每条行为测试各自断言的那个场景** fail-closed（17 行为 + 3 静态）——**逐例证据，非"所有路径都安全"的整体证明**。
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:171:- **前提（非结论）**："DB 静止"由操作者保证——0 行、固定 sha、前后同 SHA 本身**不能证明**读取期间没有并发写者。
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:172:- **不再声称的**：在共享可写目录、有并发写者、SQLite DB 正被写入等**敌意环境**下具备生产级安全；也不声称"整类别名绕过已消失"（`lstat`→`replace` 竞态等残余见 FU-B/FU-C）。这类保证需要一致性快照、dirfd 相对发布、单写者锁——是把一次性 census 脚本升级为常驻工具的工作量，不在本卡范围。

exec
/bin/zsh -lc "git -c core.quotePath=false grep -n -I -E '(写入|取证|绕过|fail.?closed|静止|终态|before/after|前后.*SHA|前后.*sha|只读)' 543e8a34 -- '_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md' '_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:4:> **性质**: 只读 census。0 重放、0 业务代码改动。代码产物 = `backend/scripts/census_dead_letter_episodes.py` + 其只读契约回归测试。
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:5:> **只读声明的准确边界（round-9 收敛，见 §7j）**: 本次运行对**本次列出的输入文件**（4 份 DLQ + qa_metrics.db）shasum 前后不变（证据包留有本次 before/after 一对，非九轮各存一对）；回归测试中**每条行为测试各自断言的那个具体场景** fail-closed（17 条跑真实 CLI + 3 条源码静态检查）——这是**逐例证据**，不构成"所有误用路径均 fail-closed"的整体证明。但**不声称**在共享可写目录、并发写者、活跃 SQLite DB 等敌意环境下具备生产级安全——剩余必需项见 §7j 清单。
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:8:> **证据包**: `_bmad-output/审查/G4-9-evidence/`（shasums before/after、grep 自证、容器内 sha 实测）
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:58:## §4 源指针核销（qa_metrics.db，源 fd 只读 + 内存副本）
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:62:  - `llm_call_logs.db`（同目录）：本卡仅做**一次性人工只读查看 schema**（未纳入脚本探测路径），确认仅 token/延迟/成本指标列，**无 prompt/response 正文**；
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:71:| **可字节级**（byte_exact） | **4** | inline 正文全量：sha256 重算对账通过**且**长度精确匹配（fail-closed 双门）——重放可逐字节还原 episode |
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:74:| **不可核验**（unverifiable，round-4 新增） | **0** | 源可见性不足（扫描受阻/不可读候选/归因冲突）——既不宣称可恢复，也不宣称不可恢复。Codex round-4 指出：把"看不见"终态化为"不可恢复"是不诚实断言，故单列第四态 |
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:82:台账逐条携带复合键 `{line_no, sha256_prefix(16 hex), request_id}`。**语义（Codex round-1 LOW-2 修正）**：这是**冻结快照内的 occurrence key**，不是跨文件重排或语义幂等键——台账头部 `dlq_file.sha256`（`3b37460f4215f6ac…`）即快照指纹，`line_no` 在该快照内已单列唯一；`sha256_prefix`（本快照 69 个唯一值，qa_highlight 家族实测同名同 sha 多条）与 `request_id`（仅 25 个唯一值，进程内 contextvars、重启可复用）是**冗余对账/诊断维度**，不是唯一性的必要条件。G4-10 消费前先 diff 头部 sha 即知 DLQ 是否长了新条目；语义级去重不得按本键，须按 `duplicate_clusters` 段（见下）。**语义重复簇（MEDIUM-2 整改）**：按 `{name, episode_body_sha256, group_id}` 聚簇，**6 簇覆盖 29 行**（最大簇 = 同一 session-archive 16 行，`reference_time` 各不相同——同内容反复入队反复超限）。台账 `duplicate_clusters` 段逐簇列 line_nos，records 逐条透传 `reference_time`；G4-10 重放前必须先定去重策略（89 条 budget 修根因后若逐条盲放，将把同内容写入最多 16 遍）。
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:92:| 运行前后 shasum（live/主仓/孤儿①/孤儿② 四份 DLQ + qa_metrics.db） | `diff shasums-before.txt shasums-after.txt` 空 → **本次留存的 before/after 样本 SHA 相同**。⚠️ 该证据只证明**前后终态字节一致**，**不证明**读取期间零写入，也**不证明**每轮均留存了独立证据（仓库只保留最新一对） |
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:104:- **HIGH-1（inline 判定不 fail-closed）**：full_verified 加长度精确匹配门；truncated_prefix 加 64-hex 合法性门；anomaly 一律 unrecoverable + 如实 basis（不再谎称截断、不再滑入 approximate）。
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:118:- **BLOCKER-1 NOT-CLOSED（hardlink / case-only 别名绕过）**：原守卫比较 `resolve()` **字符串**，hardlink 指向输入、以及大小写不敏感文件系统上的 case-only 别名均绕过并截断输入。**整改**：改为比较**文件身份 `(st_dev, st_ino)`**（对已存在的 --out）+ 保留路径比较作第二道。负例实测：两种绕过均 exit 2、DLQ sha 不变。
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:144:- **BLOCKER-1 残留两条绕过**：① `protected_paths` 未含**归因到的 transcript**，`--out=<唯一 transcript>` 会截断恢复源；② check-then-open 的 **TOCTOU** 仍在（检查后、打开前把 --out 换成指向 DLQ 的链接）。**整改**：① 写出前把全部 `transcript_paths` 并入保护集；② 改 `os.open(O_WRONLY|O_CREAT|O_NOFOLLOW)` **不带 O_TRUNC** 打开 → 对**实际 fd** `fstat` 校验 inode → 通过才 `ftruncate`，检查与写入作用于同一 fd，替换攻击无效。反例实测：`--out` 指向唯一 transcript → exit 2、transcript sha 不变。
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:145:- **HIGH-3 残留**：`glob(recursive=True)` 在 realpath 过滤**之前**已递归遍历（Python 3.14 glob 跟随目录 symlink 且**静默吞掉不可读子树错误**）→ 越根枚举 + "假唯一/假不可恢复"；mode `000` 的 regular transcript 仍过 `isfile()` 被判 approximate。**整改**：改 `os.walk(onerror=..., followlinks=False)`（不跟随目录 symlink、遍历错误显式捕获）+ 候选加 `os.access(R_OK)` 门；遍历受阻或存在不可读候选一律记 `attribution_conflict` 拒绝裁定（既不宣称找到、也不宣称不可恢复）。三条反例实测全部 fail-closed。
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:156:- **BLOCKER①（不可读但可写的 transcript 绕过保护集）**：mode `0200` 的候选在 unreadable 分支被清空 `transcript_paths`，因此不进保护集，`--out` 指向它仍被截断（无需竞态）。**整改**：新增 `all_candidate_paths` 保留**所有见到的候选**（含不可读、含被冲突分支清空的），写出前全部并入保护集。实测：mode 0200 候选作 `--out` → exit 2、文件字节不变。
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:158:- **HIGH（不可见被终态化为 unrecoverable）**：扫描受阻/冲突时主链仍产出 `unrecoverable`，与报告"既不宣称不可恢复"自相矛盾。**整改**：引入第四态 **`unverifiable`**（源可见性不足，basis 逐条说明是遍历受阻/不可读候选/归因冲突），distribution 与 `unverifiable_list` 同步。实测：不可读子树 → `unverifiable=1`，不再冒充 unrecoverable。
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:172:- **HIGH①（anomaly 吞掉不可见性）**：`anomaly→unrecoverable` 排在 conflict 判断之前，`anomaly + 扫描受阻` 仍被假终态化。**整改**：判定链改为**可见性优先**——归因不可核验时无论 inline 状态一律 `unverifiable`，basis 逐条写明原因（无 token / token 冲突 / 扫描受阻 / 候选 stat 失败 / 不可读候选 / 多命中 ambiguous），并附注 inline 是否也 anomaly。实测：anomaly+不可读子树 → `unverifiable`。
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:173:- **HIGH②（`fchmod` 先于 protected-id 检查）**：`--out` 指向受保护的 0644 输入时，会**先把只读输入权限改成 0600** 再拒绝——字节没截断但输入已被修改。**整改**：碰撞检查前移到 `fchmod` 之前。实测：mode 644 → 644 不变。
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:192:- **LOW ×3**：ledger 新增 `attribution_conflict_reason` 自描述（本次 92 条：`no_token` 3 / 其余 89 无冲突）；`json.dumps` 对 lone surrogate 回退 `ensure_ascii=True` 并显式标注，不再整次 census 拒绝；`stat_failures` 分支保留（Codex 确认非额外绕过，仅基本不可达）。
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:200:> **「现有 92 条冻结 ledger 可以采信；CARD-G4-9 生成器与 UAT 的纯只读安全声明不可验收。」**
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:202:即：卡面的 census 判据（分类/对账/三态/挂载真相/稳定键/shasum 不变）已满足且被独立复算确认；阻断项全部落在"生成器作为工具的只读安全承诺"上。逐条整改：
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:204:- **BLOCKER（大小写别名根）**：本机实测 `/Users/Heishing/.claude/projects` 与 `/users/heishing/...` `samefile=True` 但 `realpath` 字符串不同，prefix guard 返回 False——**无需竞态的实际绕过**。我 round-6 用的 `os.path.normcase` 在 POSIX 上是**恒等函数**（假设错误）。**整改**：新增 `_path_is_within()`，从目标逐级向上比较 **inode 身份**，完全不依赖路径字符串；`--out` 与输入文件的比较改 `os.path.samefile`。实测：别名根作 `--out` → exit 2，正例无回归。
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:205:- **NOT-CLOSED ×4（根外 hardlink 指向隐藏目录内 transcript / 根 retarget TOCTOU / 检查后换父目录 symlink 或 basename hardlink）+ MEDIUM（非原子写）**：这五项依附于同一个动作——**截断一个已存在的文件**。**架构级修复**：写出改为「同目录 `O_EXCL` 新建临时文件 → 写 → `fsync` → `os.replace` 原子替换」，**全文再无任何 `ftruncate` 调用**。`O_EXCL` 保证写入目标是本进程新建的对象，因此"截断既有对象"这条具体路径消失（三场景各自取证，不声称整类绕过均已失效）；`os.replace` 同时消除崩溃/ENOSPC 留下部分台账的风险。实测：根外 hardlink 指向根内 transcript 作 `--out` → 台账正常写出而**源文件内容完好**（`os.replace` 只重绑定该名字，不触碰底层 inode）。
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:216:> **可验收：92 条冻结 ledger snapshot。不可验收：当前生成器的一般安全性，以及 UAT 的"纯只读、唯一写出口、整类 TOCTOU 已消失"声明。**
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:222:- **①②的共同解法**：不再让 SQLite 碰路径——从**已验证的 fd** 读全量字节 → `sqlite3` 内存库 `deserialize()`。URI 转义问题与 ABA **一并消失**，且全程不落任何文件。实测：路径含 `#` 与 `?` 的 DB 正常只读（`read_mode: in_memory_deserialize_from_verified_fd`，16384 bytes）。
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:224:- **HIGH（扫描受阻拒绝不完整）**：no_token/token_conflict 分支在写入 `scan_errors` **之前**就早退；且拒绝条件写作 `scan_blocked and args.out`，**省略 `--out` 走 stdout 即可绕过**。**整改**：早退分支同样记录扫描错误；拒绝条件去掉 `and args.out`。实测：stdout 模式扫描受阻同样 exit 2。
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:235:- **必需⑤ 名实不符（DD-13 硬伤）**：改用内存 `deserialize` 后，字段仍叫 `opened_readonly`、docstring 仍称 SQLite URI `mode=ro`——**实际只有源 fd 只读，内存连接可写**。已改字段名为 `source_fd_opened_readonly`，docstring 如实说明只读保证的来源（源 fd 只读 + 内存副本与源解耦），补 `PRAGMA query_only=ON` 作纵深防御，并把 QA DB 的 `source_sha256` 写入台账（与证据包 shasum 一致）。
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:240:round-9 的必需①②③（一致性 SQLite 快照、单一稳定 dirfd 发布、tmp/发布者/状态绑定与单写者锁）是把这个**一次性 census 脚本**升级为**生产级并发安全工具**的要求。本卡不做，理由如实记录：本卡场景为单人本机、目录非共享可写；**"DB 静止"与"无并发写者"是操作者提供的前提，不是本卡证明的结论**（0 行 / 固定字节数 / 前后同 SHA 均不能证明读取期间无写者）。**处置方式是收敛声明而非假装达标**——报告头与验收单已删去"纯只读 / 唯一写出口 / 整类 TOCTOU 已消失"这类绝对化措辞，改为"本次运行输入 shasum 前后不变（已取证）+ 对 20+ 类误用路径 fail-closed（测试固化）+ 不声称敌意环境下的生产级安全"。
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:246:| FU-A | SQLite 一致性快照（backup API 或要求外部先冻结 DB）+ 显式拒绝 WAL/journal/并发变化 | DB 非静止时 |
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:251:round-9 整改后第九次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变、只读契约测试 19 passed——九轮整改数字全程未变**。
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:258:2. **修正字段语义**：`source_fd_opened_readonly` 原在 `deserialize` 成功后才置真——DB malformed 时 fd 确已只读打开却返回 false。已移到 fd 打开成功处。**该修正顺带暴露一个真 bug**：`deserialize` 是**延迟验证**，malformed DB 的 `DatabaseError` 在首次 `execute` 时才抛出，而查询段原本只有 `finally` 没有 `except`——**会炸掉整次 census**。已补 `sqlite3.Error` 捕获并记 `query_failed`，新增回归用例锁定。
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:261:5. **"九次取证"表述收敛**：仓库只保留最新一对 before/after shasum，已改述为"本次留存一对，此前各轮亦逐次核对但未各存一份"。
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:262:6. **"DB 静止"改为操作者前提**：0 行 / 固定 sha / 前后同 SHA 本身不能证明读取期间无写者——已在脚本"安全边界"段与本报告显式声明为**前提而非结论**。
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:264:round-10 整改后第十次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变、只读契约测试 20 passed（17 行为 + 3 静态）——十轮整改数字全程未变**。
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:272:1. **清除残留声明**（DB 静止当事实 / 逐次·运行零写入 / 整类绕过失效 / "20 个测试整体证明路径 fail-closed"）。已逐处改写：
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:273:   - 脚本 docstring 中"本卡场景为单人本机、DB 静止（实测 0 行、16384 bytes），故不影响结论"→ 改为"该假定**由操作者保证**（行数为 0、字节数固定、前后 SHA 相同都**不能证明**读取期间没有并发写者）"。
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:274:   - "对 20+ 类误用/攻击路径 fail-closed（回归测试固化）"→ 改为"**每条行为测试各自断言的那一个具体场景** fail-closed —— 这是逐例证据，**不构成**'所有误用路径均 fail-closed'的整体证明"。
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:275:   - "整类绕过全部失效"→ 改为"'截断某个既有对象'这条**具体路径**不再存在（已就 hardlink / 根内 symlink / FIFO 三场景各自取证）；⚠️ 不等于声称所有别名类绕过已失效——`lstat`→`replace` 竞态等残余见 FU-B/FU-C"。UAT 同处过强表述一并修正。
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:288:| (b) 生成器（已声明有界前提下） | **PASS，可验收** | 前提明确为单人本机、非共享目录、DB 静止由操作者保证；坏 JSON、sentinel 与全部常规文件覆盖、测试范围声明均已补强，**未发现 round-11 所指虚假通过空间** |
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:290:| (c) 报告与 UAT 声明 | **FAIL** | DB 静止与逐例测试措辞已收敛，但仍有非引述性过强断言（下述两条） |
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:294:1. **"0 写入 / 逐次取证 / 输入零改动"→ 准确表述**：报告 §7 裁判表与 UAT 三处已统一改为"**本次留存的 before/after 样本 SHA 相同**；⚠️ 只证明**前后终态字节一致**，**不证明**读取期间零写入，也**不证明**每轮均留存独立证据（仓库只保留最新一对）"。判据名亦由"全程零写入/输入零改动"改为"**输入前后终态一致**"。
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:295:2. **"五项绕过整类失效"→ 具体路径表述**：UAT round-7 行改为"「截断某个既有对象」这一**具体路径**不再存在，**不代表所有别名类绕过均已失效**（`lstat`→`replace` 竞态见 FU-B/FU-C）"。
543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:297:这两条的共同点与前十一轮一致：**证据支持的是"前后终态一致"与"某条具体路径消失"，我却写成了"零写入"与"整类失效"**。改的是措辞，不是结论——台账数字与脚本行为均未变动。
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:6:scope: "BATCH-2026-08-28-第五批 / CARD-G4-9 — live DLQ 92 条只读 census：分类/SHA 对账/可恢复性三态/挂载真相，产出 G4-10 交接台账"
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:13:> 这张卡**没有修任何东西，也没有恢复任何数据**——它是一次"清点尸体"的只读普查（本次留存的 before/after 样本 SHA 相同——只说明前后终态一致，不证明读取期间零写入；安全边界见文末"诚实边界"段）：
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:14:> 线上 Graphiti 写入失败后落进死信文件的 92 条记录，逐条查清"是什么死的、还能不能救、去哪里救"，
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:27:| 输入前后终态一致（裁判判据 e） | 运行前后**本次列出的输入**（四份 DLQ + qa_metrics.db）sha256 相同（diff 为空）。⚠️ 边界：这证明**前后终态字节一致**，**不证明**读取期间零写入；证据包只留存本次一对 before/after，**非每轮各存一份** | `_bmad-output/审查/G4-9-evidence/shasums-before.txt` / `shasums-after.txt` |
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:28:| 脚本只读自证（判据 a） | import 行全 stdlib；neo4j/graphiti/bolt/app. import **0 命中**；`--apply` 定义 **0 命中**；**全文无任何截断调用**（写出走 O_EXCL 临时文件 + 原子替换） | `G4-9-evidence/grep-selfattest.txt` |
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:29:| 只读契约回归测试（round-9 必需项④ + round-10 补强） | **20 passed**：**17 条行为测试**（subprocess 跑真实 CLI + 断言文件系统事实）+ **3 条源码静态检查**（弱证据，如实标注，不替代行为测试）。测试两次抓出真实问题：① 架构改动丢了文件类型门（FIFO 会被静默替换）；② `deserialize` 延迟验证使 malformed DB 炸掉整次 census。round-10 另修掉 4 处虚假通过窗口 | `backend/tests/regression/test_census_dead_letter_readonly_contract.py` |
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:33:| 源指针核销（判据 b，qa_metrics.db 源 fd 只读 + 内存副本） | `qa_error_logs` **0 行** → 0/92 可经 qa_metrics.db 溯源（诚实记录）；附加核销：llm_call_logs.db 无正文、outbox 空、episode_body_full 0 条；**有效源指针 = request_id 组内 session 归因 → 7 个 transcript 全部在盘实测存在** | 报告 §4 + 台账 `qa_metrics_probe` |
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:41:| round-3 findings 逐条整改 | **6/6 完成**：transcript 并入保护集 / O_NOFOLLOW+fstat 消 TOCTOU / os.walk 替 glob（不跟随目录 symlink+遍历错误显式捕获）/ 不可读候选 fail-closed / JSONL 严格 LF 分帧 / 非 dict 归 unparseable。6 条新反例实测全过、数字第三次不变 | 报告 §7d + `grep-selfattest.txt` |
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:48:| Codex 复审 round-7 | **关键裁定分离**："92 条冻结 ledger **可以采信**；生成器与 UAT 的纯只读安全声明不可验收"——卡面 census 判据已满足，阻断全在工具安全承诺侧。1 BLOCKER（大小写别名根，无需竞态）+ 4 项路径 TOCTOU + 1 MEDIUM（非原子写）+ 2 LOW | `_bmad-output/审查/codex-review-CARD-G4-9-round7.md` |
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:49:| round-7 findings 整改 | **架构级第二次修复**：写出改 O_EXCL 临时文件+fsync+os.replace（**全文再无 ftruncate 调用**）——「截断某个既有对象」这一**具体路径**不再存在，**不代表所有别名类绕过均已失效**（lstat→replace 竞态见 FU-B/FU-C）；containment 改 inode 逐级比较（normcase 在 POSIX 是恒等函数，我的假设错了）；扫描受阻直接拒绝写出。实测：根外 hardlink 指向根内 transcript 作 --out → 源内容完好 | 报告 §7h |
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:50:| Codex 复审 round-8 | 重申裁定分离：**「可验收：92 条冻结 ledger snapshot；不可验收：生成器一般安全性与 UAT 的纯只读声明」**。3 新 BLOCKER（SQLite URI 未转义 #/? / QA DB 仍按 pathname 开可 ABA / 根内末级 symlink 因 rename 不解析而被替换）+ 1 HIGH + 1 MEDIUM | `_bmad-output/审查/codex-review-CARD-G4-9-round8.md` |
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:53:| round-10 解阻整改 | **6/6 完成**：脚本+报告+UAT 的 `mode=ro` 与「唯一写出口/全程零写入」矛盾表述全清（残留均为「已废弃」引述）；`source_fd_opened_readonly` 移到 fd 打开处（**顺带修出真 bug**：deserialize 延迟验证使 malformed DB 炸掉整次 census）；测试覆盖如实标注 17 行为+3 静态并修掉 4 处虚假通过窗口；证据补 HEAD/blob/sha256/逐项明细；「九次取证」与「DB 静止」改为准确表述与操作者前提 | 报告 §7k/§7l |
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:55:| round-11 解阻整改 | **3/3 完成**：DB 静止改为操作者前提（0 行·固定字节·同 SHA 均不能证明无并发写者）、"20 类路径 fail-closed"改为逐例证据声明、"整类绕过失效"改为具体路径消失+残余竞态登记；坏 JSON 直接断言原始列表恰 3 项、输入不变测试加非 JSONL sentinel 并覆盖根内全部常规文件；证据绑定新 blob（脚本 87266e09/测试 541ec8b3）。20 passed | 报告 §7m |
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:57:| round-12 措辞整改 | **2/2 完成**（Codex 明示无需再改测试/脚本/证据）："0 写入·逐次取证·输入零改动"统一改为"本次留存 before/after 样本 SHA 相同；不证明读取期间零写入、不证明每轮各存证据"；"五项绕过整类失效"改为"『截断既有对象』这一具体路径不再存在，不代表所有别名类绕过均已失效" | 报告 §7n |
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:58:| 独立 Workflow 4-agent 复核 | G4-9 数字 agent：92 条重算 **0 mismatch**（class/inline/三态/25 request_id/7 transcript 在盘/台账 sha 全 CONFIRMED，仅 2 处描述区间 REFUTED 已修正）；只读契约 agent：与 Codex 同源的 3 条 blocker（已随上整改） | Workflow wf_737b1a95-20b journal |
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:65:- **HIGH-1 inline 判定 fail-open**：sha 匹配但长度不符会误判 full_verified（反例实测）。整改：长度精确匹配门 + 64-hex 合法性门 + anomaly 一律 fail-closed（unrecoverable + 如实 basis）。
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:77:- **BLOCKER-1 未闭合**：守卫比的是路径字符串，**hardlink 与大小写别名照样截断 DLQ**。→ 改比**文件 inode 身份**；两种绕过实测双双 exit 2、DLQ sha 不变。
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:86:round-3 确认 HIGH-1 与三条 LOW 真正闭合、台账数字有效，又在两项路径安全上找到更深的绕过：
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:89:- **HIGH-3 仍 PARTIAL**：Python 3.14 的 `glob` 在过滤前就已递归、跟随目录 symlink 且**静默吞掉不可读子树错误**；mode 000 的文件仍过 `isfile()` 被当可用源。→ 改 `os.walk(onerror=, followlinks=False)` + `os.access(R_OK)` 门；遍历受阻或有不可读候选一律拒绝裁定。三反例实测 fail-closed。
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:99:- **不可读但可写（mode 0200）的 transcript 绕过保护集**：我在"不可读"分支把候选路径清空了，于是它没进保护集，`--out` 指向它照样截断——不需要任何竞态。→ 新增"全候选清单"，无论可读与否一律并入保护集。
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:113:- **`fchmod` 排在碰撞检查之前**：`--out` 指向受保护的只读输入时，会先把它的权限从 644 改成 600 才发现碰撞——字节没丢但输入被改了。→ 碰撞检查前移。
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:134:> **「现有 92 条冻结 ledger 可以采信；生成器与 UAT 的纯只读安全声明不可验收。」**
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:136:也就是说：这张卡要交付的 census 结论（92 条的分类、对账、三态、挂载真相、稳定键，以及输入前后终态字节一致）**已经过关**；卡住的是"这个脚本作为工具，其只读承诺是否经得起敌意输入"。
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:138:- **一个无需竞态的真实绕过**：大小写不敏感卷上 `/Users/...` 与 `/users/...` 是同一个目录但 realpath 字符串不同，我 round-6 用来防御的 `os.path.normcase` **在 macOS/Linux 上根本是恒等函数**——这是我的知识性错误。改成逐级比较 **inode 身份**，不再依赖任何字符串。
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:139:- **五项绕过共用一个根源**：它们都依附于"截断一个已存在的文件"这个动作。改成「新建临时文件 → 写 → fsync → 原子替换」后，脚本**全文再没有任何截断调用**——"截断某个既有对象"这条**具体路径**不复存在，"崩溃留下半个台账"的风险也一并消除。实测：拿一个指向恢复源的 hardlink 当 `--out`，台账正常写出，而**源文件内容一个字节没变**。⚠️ 这**不等于**"所有别名类绕过都已失效"：`lstat`→`replace` 之间仍有竞态窗口，已登记 FU-B/FU-C。
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:146:round-8 把结论说得更清楚了：**「可验收：92 条冻结 ledger snapshot。不可验收：生成器的一般安全性，以及验收单里那句"纯只读、唯一写出口、整类 TOCTOU 已消失"」**。
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:152:- **stdout 模式漏网**：扫描受阻的拒绝条件我写成了"且指定了 --out"，于是省略 `--out` 就能绕过。→ 去掉该条件。
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:158:- `backend/scripts/census_dead_letter_episodes.py` — 唯一代码产物（只读 census 脚本，纯 stdlib）
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:166:九轮对抗审查后，Codex 始终维持一个分层裁定：**「92 条冻结台账可以采信；但生成器的一般安全性、以及验收单里"纯只读、唯一写出口、整类 TOCTOU 已消失"这类绝对化声明不可验收」**。
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:170:- **可以确证的**：本次运行对**本次列出的输入文件**（4 份 DLQ + qa_metrics.db）**shasum 前后逐字节不变**（证据包留存本次一对 before/after）；回归测试中**每条行为测试各自断言的那个场景** fail-closed（17 行为 + 3 静态）——**逐例证据，非"所有路径都安全"的整体证明**。
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:171:- **前提（非结论）**："DB 静止"由操作者保证——0 行、固定 sha、前后同 SHA 本身**不能证明**读取期间没有并发写者。
543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:172:- **不再声称的**：在共享可写目录、有并发写者、SQLite DB 正被写入等**敌意环境**下具备生产级安全；也不声称"整类别名绕过已消失"（`lstat`→`replace` 竞态等残余见 FU-B/FU-C）。这类保证需要一致性快照、dirfd 相对发布、单写者锁——是把一次性 census 脚本升级为常驻工具的工作量，不在本卡范围。

exec
/bin/zsh -lc "git -c core.quotePath=false diff --unified=8 f4112c2c 543e8a34 -- '_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md' '_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
diff --git a/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md b/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md
index 9eaa362f..dfe6d5ed 100644
--- a/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md
+++ b/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md
@@ -84,17 +84,17 @@ docker exec canvas-learning-system-backend sha256sum /app/data/dead_letter_episo
 **隐私（MEDIUM-3 整改）**：`transcript_paths` 含本机用户名与完整 session UUID，台账与本报告为 **private-only 工件**（台账头部已带 privacy 字段；仓库纪律 = 不 push 公网远端）。
 
 逐条另带 `class / inline_state / recoverability / transcript_paths / transcript_match_count / attribution_conflict / error_excerpt / failed_at / reference_time`，G4-10 可直接按 `recoverability` 分桶排重放优先级（建议：4 条 byte_exact 先行——但其中 3 条 group_id 为已弃用 `vault:default`，重放前需按 D16 规约重映射并过 `to_physical_group_id()`；89 条 budget_400 重放前必须先修 context 超限根因，否则原样重放必然复现 400）。
 
 ## §7 裁判证据（整改版脚本重跑）
 
 | 证据 | 结果 |
 |---|---|
-| 运行前后 shasum（live/主仓/孤儿①/孤儿② 四份 DLQ + qa_metrics.db） | `diff shasums-before.txt shasums-after.txt` 空 → **PASS，0 写入** |
+| 运行前后 shasum（live/主仓/孤儿①/孤儿② 四份 DLQ + qa_metrics.db） | `diff shasums-before.txt shasums-after.txt` 空 → **本次留存的 before/after 样本 SHA 相同**。⚠️ 该证据只证明**前后终态字节一致**，**不证明**读取期间零写入，也**不证明**每轮均留存了独立证据（仓库只保留最新一对） |
 | grep 自证（import 行全 stdlib；neo4j/graphiti/bolt/app. import 0 命中；`--apply` 定义 0 命中；写模式 open 仅 `--out` 1 处且受路径碰撞守卫保护） | **PASS**（`grep-selfattest.txt`，含守卫在位证明） |
 | 容器内 sha 实测 | 92 行、sha 与宿主 live 地址一致（`container-sha-check.txt`） |
 | class 偏差 | 无（89/2/1 与勘探预期一致，脚本 `class_deviation` 字段为空） |
 | 负例门（round-1 整改自证） | `--out`==`--dlq` → exit 2 拒写、DLQ 完好；transcripts 根缺失 → exit 2 拒诊；sha 匹配但长度不符（round-1 HIGH-1 反例①）→ anomaly/unrecoverable；坏 JSON 行/空行 → unparseable 逐行入台账不拒诊 |
 | 负例门（round-2 整改自证） | **hardlink** 指向 DLQ 的 --out → exit 2 + DLQ sha 不变；**case-only 别名**（`DLQ.jsonl`）→ exit 2 + DLQ 完好；**anomaly + episode_body_full 组合**（sha 对但长度 999）→ anomaly/unrecoverable（不再翻案 byte_exact）；**chmod 000 根** → exit 2 拒诊；**symlink 逃逸**（根内 .jsonl → 根外 .txt）→ match_count=0/unrecoverable；正例回归：真实唯一命中仍 approximate |
 
 ## §7b Codex round-1 整改记录（BLOCKED → 全项整改）
 
@@ -272,8 +272,28 @@ round-11 重申「**无需补必需①②③**」，并把剩余阻断收敛为
 1. **清除残留声明**（DB 静止当事实 / 逐次·运行零写入 / 整类绕过失效 / "20 个测试整体证明路径 fail-closed"）。已逐处改写：
    - 脚本 docstring 中"本卡场景为单人本机、DB 静止（实测 0 行、16384 bytes），故不影响结论"→ 改为"该假定**由操作者保证**（行数为 0、字节数固定、前后 SHA 相同都**不能证明**读取期间没有并发写者）"。
    - "对 20+ 类误用/攻击路径 fail-closed（回归测试固化）"→ 改为"**每条行为测试各自断言的那一个具体场景** fail-closed —— 这是逐例证据，**不构成**'所有误用路径均 fail-closed'的整体证明"。
    - "整类绕过全部失效"→ 改为"'截断某个既有对象'这条**具体路径**不再存在（已就 hardlink / 根内 symlink / FIFO 三场景各自取证）；⚠️ 不等于声称所有别名类绕过已失效——`lstat`→`replace` 竞态等残余见 FU-B/FU-C"。UAT 同处过强表述一并修正。
 2. **测试补强**：坏 JSON 用例改为**直接断言原始 `unparseable_lines` 恰为三项**（不经 dict 压缩，避免同 line_no 覆盖掩盖重复条目）再逐条精确断言；输入不变测试加入**非 JSONL sentinel** 文件并覆盖 transcripts 根内**全部常规文件**（原只哈希 `*.jsonl`，与"覆盖根内全部文件"的说法不符）；测试 docstring 改为"**所有行为测试**的断言均针对真实文件系统效果"并补范围声明。
 3. **重跑并更新可绑定证据**：`readonly-contract-tests.txt` 已用新 script/test blob 重生成（脚本 blob `87266e09…`、测试 blob `541ec8b3…`，含各自 sha256 与逐项 PASSED 明细）。**20 passed**。
 
 round-11 整改后第十一次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变——十一轮整改数字全程未变**。
+
+## §7n Codex round-12 三层裁定与最后两条措辞整改
+
+round-12 首次给出**三层分别裁定**：
+
+| 层 | 裁定 | 依据 |
+|---|---|---|
+| (a) 92 条冻结 ledger | **PASS，可验收** | 从 exact raw DLQ 与 `records[]` 独立复算一致：92 条 / class 89-2-1 / byte_exact 4·approximate 88·unverifiable 0·unrecoverable 0 / 重复簇 6-29 / unparseable 0 / attribution_conflict 3 全为 `no_token` |
+| (b) 生成器（已声明有界前提下） | **PASS，可验收** | 前提明确为单人本机、非共享目录、DB 静止由操作者保证；坏 JSON、sentinel 与全部常规文件覆盖、测试范围声明均已补强，**未发现 round-11 所指虚假通过空间** |
+| 可绑定证据 | **PASS** | `f4112c2c` tree 中脚本/test blob 确为 `87266e09…`/`541ec8b3…`，独立 SHA-256 与证据一致，20 个 PASSED 名称与测试 blob 的 20 个函数逐项对应 |
+| (c) 报告与 UAT 声明 | **FAIL** | DB 静止与逐例测试措辞已收敛，但仍有非引述性过强断言（下述两条） |
+
+最后两条整改（Codex 明示"无需再改测试、脚本或重生成绑定证据"）：
+
+1. **"0 写入 / 逐次取证 / 输入零改动"→ 准确表述**：报告 §7 裁判表与 UAT 三处已统一改为"**本次留存的 before/after 样本 SHA 相同**；⚠️ 只证明**前后终态字节一致**，**不证明**读取期间零写入，也**不证明**每轮均留存独立证据（仓库只保留最新一对）"。判据名亦由"全程零写入/输入零改动"改为"**输入前后终态一致**"。
+2. **"五项绕过整类失效"→ 具体路径表述**：UAT round-7 行改为"「截断某个既有对象」这一**具体路径**不再存在，**不代表所有别名类绕过均已失效**（`lstat`→`replace` 竞态见 FU-B/FU-C）"。
+
+这两条的共同点与前十一轮一致：**证据支持的是"前后终态一致"与"某条具体路径消失"，我却写成了"零写入"与"整类失效"**。改的是措辞，不是结论——台账数字与脚本行为均未变动。
+
+round-12 整改后台账未重跑（本轮无脚本改动，`f4112c2c` 的 ledger 即最终版）：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0——十二轮整改数字全程未变**。
diff --git a/_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md b/_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md
index eece19dc..266b415d 100644
--- a/_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md
+++ b/_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md
@@ -5,31 +5,31 @@ date: 2026-08-28
 status: awaiting_user
 scope: "BATCH-2026-08-28-第五批 / CARD-G4-9 — live DLQ 92 条只读 census：分类/SHA 对账/可恢复性三态/挂载真相，产出 G4-10 交接台账"
 worktree: "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census"
 ---
 
 # UAT · CARD-G4-9 DLQ 真实挂载 census 分诊
 
 > [!info]+ 你不需要碰命令行 — 全部技术验证我已代跑（结果见下）
-> 这张卡**没有修任何东西，也没有恢复任何数据**——它是一次"清点尸体"的只读普查（脚本对输入零写入已逐次取证；安全边界见文末"诚实边界"段）：
+> 这张卡**没有修任何东西，也没有恢复任何数据**——它是一次"清点尸体"的只读普查（本次留存的 before/after 样本 SHA 相同——只说明前后终态一致，不证明读取期间零写入；安全边界见文末"诚实边界"段）：
 > 线上 Graphiti 写入失败后落进死信文件的 92 条记录，逐条查清"是什么死的、还能不能救、去哪里救"，
 > 给后续的 G4-10（真正做恢复的卡）留一份带稳定编号的台账。卡面如实标注：离日常使用价值远，属恢复能力地基。
 
 ## 📌 你需要过目的三个结论
 
 1. **92 条死信全部查清、零"待定"**：89 条是"内容太长超过本地模型 16384 token 上限"（未修，根因归 G4-10）；2 条是 5 月 14 日的 schema 冲突、1 条是旧 group_id 冒号格式——这 3 条的根因**当天之后就已修复**，不会再新增。
 2. **一条都不算丢**：4 条正文完整躺在死信文件里（可逐字节恢复）；88 条只存了前 200 字预览，但每一条都顺着线索找回了**唯一**源头会话记录（7 个会话的原始 transcript 全部还在你电脑上）——可近似重建（找到了源头 ≠ 已经恢复，真正重建是 G4-10 的活）。**不可恢复：0 条**。另清点出 6 组重复（29 条是同内容反复入队），G4-10 恢复时会先去重，不会把同一段写 16 遍。
 3. **死信文件的"真身"只有一处**：线上容器读写的是 `feature-obsidian-hybrid-dev` worktree 的 `backend/data/`（容器内实测 sha 一致）；主仓那份 685 行是 4 月的陈旧副本，另有两处孤儿残留——报告里有四址对照表，以后不会再查错文件。
 
 ## ✅ 技术验证（Claude 已代跑）
 
 | 项 | 结果 | 证据 |
 |---|---|---|
-| 输入零改动（裁判判据 e） | 运行前后**本次列出的输入**（四份 DLQ + qa_metrics.db）sha256 **逐字节不变**（diff 为空 → PASS）。注：证据包留存本次一对 before/after，非每轮各存一份 | `_bmad-output/审查/G4-9-evidence/shasums-before.txt` / `shasums-after.txt` |
+| 输入前后终态一致（裁判判据 e） | 运行前后**本次列出的输入**（四份 DLQ + qa_metrics.db）sha256 相同（diff 为空）。⚠️ 边界：这证明**前后终态字节一致**，**不证明**读取期间零写入；证据包只留存本次一对 before/after，**非每轮各存一份** | `_bmad-output/审查/G4-9-evidence/shasums-before.txt` / `shasums-after.txt` |
 | 脚本只读自证（判据 a） | import 行全 stdlib；neo4j/graphiti/bolt/app. import **0 命中**；`--apply` 定义 **0 命中**；**全文无任何截断调用**（写出走 O_EXCL 临时文件 + 原子替换） | `G4-9-evidence/grep-selfattest.txt` |
 | 只读契约回归测试（round-9 必需项④ + round-10 补强） | **20 passed**：**17 条行为测试**（subprocess 跑真实 CLI + 断言文件系统事实）+ **3 条源码静态检查**（弱证据，如实标注，不替代行为测试）。测试两次抓出真实问题：① 架构改动丢了文件类型门（FIFO 会被静默替换）；② `deserialize` 延迟验证使 malformed DB 炸掉整次 census。round-10 另修掉 4 处虚假通过窗口 | `backend/tests/regression/test_census_dead_letter_readonly_contract.py` |
 | live 挂载真相（判据 c） | 容器内 `sha256sum /app/data/dead_letter_episodes.jsonl` = 宿主 live 地址同值（92 行，`3b37460f…`）；compose :206-212 遮蔽史入报告 §1 | `G4-9-evidence/container-sha-check.txt` + 报告 §1 |
 | 分类零偏差（判据 b） | budget_400×**89** / schema×**2**（P0-4 已修，`entity_types.py:343`）/ group_id×**1**（sanitize 已兜，`group_id_compat.py:64`）——与勘探预期逐条一致，脚本 `class_deviation` 字段为空 | 台账 JSON `class_distribution` |
 | inline 完整性 + SHA 对账（判据 b） | 92/92 重算 sha256 对账：4 条 full_verified、88 条 truncated_prefix（`to_dict()` 的 `[:200]` 截断，`episode_worker.py:107`）、**0 条 anomaly** | 台账 JSON 逐条 `inline_state`/`sha_check` |
 | 源指针核销（判据 b，qa_metrics.db 源 fd 只读 + 内存副本） | `qa_error_logs` **0 行** → 0/92 可经 qa_metrics.db 溯源（诚实记录）；附加核销：llm_call_logs.db 无正文、outbox 空、episode_body_full 0 条；**有效源指针 = request_id 组内 session 归因 → 7 个 transcript 全部在盘实测存在** | 报告 §4 + 台账 `qa_metrics_probe` |
 | 可恢复性三态（判据 b） | 可字节级 **4** / 近似 **88** / 不可恢复 **0**；不可恢复清单显式成段 0 条、"待定" 0 条 | 报告 §5 + 台账 `recoverability_distribution` |
 | G4-10 稳定键（判据 d） | 逐条复合键 `{line_no, sha256_prefix, request_id}` + 台账头部冻结文件 sha；request_id 92 条仅 25 唯一值的实测证明单列不可作键 | 报告 §6 + 台账 `records[].stable_key` |
@@ -41,23 +41,25 @@ worktree: "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktre
 | round-3 findings 逐条整改 | **6/6 完成**：transcript 并入保护集 / O_NOFOLLOW+fstat 消 TOCTOU / os.walk 替 glob（不跟随目录 symlink+遍历错误显式捕获）/ 不可读候选 fail-closed / JSONL 严格 LF 分帧 / 非 dict 归 unparseable。6 条新反例实测全过、数字第三次不变 | 报告 §7d + `grep-selfattest.txt` |
 | Codex 复审 round-4 | **仍阻断**（1/6 CLOSED；2 新 BLOCKER + 1 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round4.md` |
 | round-4 findings 逐条整改 | **9/9 完成**：全候选入保护集 / 读侧 fd 身份消源侧 TOCTOU / 新增 unverifiable 第四态 / FIFO 设备门 / strict UTF-8 / 3 条错型与边界 LOW / provenance receipt。5 条新反例实测全过；第四次全量重跑数字仍不变 | 报告 §7e + `grep-selfattest.txt` |
 | Codex 复审 round-5 | **仍阻断**（3/8 CLOSED；2 BLOCKER + 2 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round5.md` |
 | round-5 findings 逐条整改 | **9/9 完成**：先扫描后判定（冲突候选亦入保护集）/ QA DB fd 身份+复核 / 可见性优先于 anomaly / fchmod 后置于碰撞检查 / QA DB 特殊文件门 / no_token 归 unverifiable / 3 条 LOW。6 条新反例实测全过；第五次全量重跑数字仍不变 | 报告 §7f |
 | Codex 复审 round-6 | **6/9 CLOSED**（visibility 优先/fchmod 顺序/no_token 语义/3 条 LOW 已闭合）；剩 2 BLOCKER + 1 MEDIUM 揭示保护集**依赖枚举完整性**的架构缺陷 + 3 新发现 | `_bmad-output/审查/codex-review-CARD-G4-9-round6.md` |
 | round-6 findings 整改 | **架构级修复 + 6 项**：新增不依赖枚举的**路径层防御**（--out 禁落 transcripts 根内 / 禁等于任一输入 realpath）、QA DB 验证 fd 保持打开至复核完毕、no_token 亦扫描、证据包重生成、ledger 冲突原因自描述、lone surrogate 回退。反例实测：0333 隐藏目录内 transcript 作 --out → exit 2 完好 | 报告 §7g |
 | Codex 复审 round-7 | **关键裁定分离**："92 条冻结 ledger **可以采信**；生成器与 UAT 的纯只读安全声明不可验收"——卡面 census 判据已满足，阻断全在工具安全承诺侧。1 BLOCKER（大小写别名根，无需竞态）+ 4 项路径 TOCTOU + 1 MEDIUM（非原子写）+ 2 LOW | `_bmad-output/审查/codex-review-CARD-G4-9-round7.md` |
-| round-7 findings 整改 | **架构级第二次修复**：写出改 O_EXCL 临时文件+fsync+os.replace（**全文再无 ftruncate 调用**），五项绕过整类失效；containment 改 inode 逐级比较（normcase 在 POSIX 是恒等函数，我的假设错了）；扫描受阻直接拒绝写出。实测：根外 hardlink 指向根内 transcript 作 --out → 源内容完好 | 报告 §7h |
+| round-7 findings 整改 | **架构级第二次修复**：写出改 O_EXCL 临时文件+fsync+os.replace（**全文再无 ftruncate 调用**）——「截断某个既有对象」这一**具体路径**不再存在，**不代表所有别名类绕过均已失效**（lstat→replace 竞态见 FU-B/FU-C）；containment 改 inode 逐级比较（normcase 在 POSIX 是恒等函数，我的假设错了）；扫描受阻直接拒绝写出。实测：根外 hardlink 指向根内 transcript 作 --out → 源内容完好 | 报告 §7h |
 | Codex 复审 round-8 | 重申裁定分离：**「可验收：92 条冻结 ledger snapshot；不可验收：生成器一般安全性与 UAT 的纯只读声明」**。3 新 BLOCKER（SQLite URI 未转义 #/? / QA DB 仍按 pathname 开可 ABA / 根内末级 symlink 因 rename 不解析而被替换）+ 1 HIGH + 1 MEDIUM | `_bmad-output/审查/codex-review-CARD-G4-9-round8.md` |
 | round-8 findings 整改 | **6/6 完成**：QA DB 改「已验证 fd 读字节 → 内存库 deserialize」（URI 转义与 ABA 一并消失，含 #? 路径实测通过）；containment 加父目录语义（POSIX rename 不解析末级 symlink）；扫描受阻去掉 and args.out（stdout 模式亦拒）；replace 纳入 try + fsync 父目录 | 报告 §7i |
 | Codex 复审 round-9/10 | round-9 给出「最小剩余项」5 条；round-10 首次明确**「阻断不再要求补必需①②③」**，收敛为 4 条可执行要求：清除矛盾声明 / 修字段语义 / 如实标注测试覆盖 / 补可绑定证据。且十轮均确认 **92 条冻结 ledger 可验收** | `codex-review-CARD-G4-9-round9.md` / `-round10.md` |
 | round-10 解阻整改 | **6/6 完成**：脚本+报告+UAT 的 `mode=ro` 与「唯一写出口/全程零写入」矛盾表述全清（残留均为「已废弃」引述）；`source_fd_opened_readonly` 移到 fd 打开处（**顺带修出真 bug**：deserialize 延迟验证使 malformed DB 炸掉整次 census）；测试覆盖如实标注 17 行为+3 静态并修掉 4 处虚假通过窗口；证据补 HEAD/blob/sha256/逐项明细；「九次取证」与「DB 静止」改为准确表述与操作者前提 | 报告 §7k/§7l |
 | Codex 复审 round-11 | 重申**无需补必需①②③**；剩余阻断收敛为 3 条：清残留声明 / 坏 JSON 与输入不变测试补强 / 用新 blob 更新证据 | `codex-review-CARD-G4-9-round11.md` |
 | round-11 解阻整改 | **3/3 完成**：DB 静止改为操作者前提（0 行·固定字节·同 SHA 均不能证明无并发写者）、"20 类路径 fail-closed"改为逐例证据声明、"整类绕过失效"改为具体路径消失+残余竞态登记；坏 JSON 直接断言原始列表恰 3 项、输入不变测试加非 JSONL sentinel 并覆盖根内全部常规文件；证据绑定新 blob（脚本 87266e09/测试 541ec8b3）。20 passed | 报告 §7m |
+| Codex 复审 round-12（三层裁定） | **(a) 92 条冻结 ledger：PASS 可验收**（独立复算逐项一致）；**(b) 生成器在已声明有界前提下：PASS 可验收**（未发现虚假通过空间）；**可绑定证据：PASS**（blob/SHA/20 项名称逐项对应）；**(c) 报告与 UAT 声明：FAIL** —— 仅剩两条过强措辞 | `codex-review-CARD-G4-9-round12.md` |
+| round-12 措辞整改 | **2/2 完成**（Codex 明示无需再改测试/脚本/证据）："0 写入·逐次取证·输入零改动"统一改为"本次留存 before/after 样本 SHA 相同；不证明读取期间零写入、不证明每轮各存证据"；"五项绕过整类失效"改为"『截断既有对象』这一具体路径不再存在，不代表所有别名类绕过均已失效" | 报告 §7n |
 | 独立 Workflow 4-agent 复核 | G4-9 数字 agent：92 条重算 **0 mismatch**（class/inline/三态/25 request_id/7 transcript 在盘/台账 sha 全 CONFIRMED，仅 2 处描述区间 REFUTED 已修正）；只读契约 agent：与 Codex 同源的 3 条 blocker（已随上整改） | Workflow wf_737b1a95-20b journal |
 
 ## 🔧 Codex round-1 整改记录（13/13 关闭，BLOCKED → 整改完毕）
 
 - **BLOCKER-1 --out 截断风险**：任意 --out 路径 "w" 无守卫，可覆盖 DLQ 自身（双审查独立实测复现）。整改：写前 resolve() 路径碰撞守卫，命中输入集合即 exit 2；负例实测拒绝、DLQ 完好。
 - **BLOCKER-2 快照不原子**：records 与头部 sha 来自两次读取。整改：单次 read_bytes()，头部与逐条同源同字节。
 - **BLOCKER-3 交付物漂移**：审查期间脚本/报告 sha 变化且未 track。整改：本卡 commit 冻结全部 exact bytes；自证文件内嵌脚本 sha 前缀。
 - **HIGH-1 inline 判定 fail-open**：sha 匹配但长度不符会误判 full_verified（反例实测）。整改：长度精确匹配门 + 64-hex 合法性门 + anomaly 一律 fail-closed（unrecoverable + 如实 basis）。
@@ -126,17 +128,17 @@ round-6 指出了一个我补丁修不掉的根因：**保护集依赖"能不能
 round-6 整改后第六次全量重跑：**92 条、4/88/0/0、89/2/1、6/29、shasum 不变——六轮整改数字全程未变**。
 
 ## 🔧 Codex round-7 复审整改记录（关键裁定分离 + 架构级第二次修复）
 
 round-7 把结论分成了两半，这个区分很重要：
 
 > **「现有 92 条冻结 ledger 可以采信；生成器与 UAT 的纯只读安全声明不可验收。」**
 
-也就是说：这张卡要交付的 census 结论（92 条的分类、对账、三态、挂载真相、稳定键、运行零写入）**已经过关**；卡住的是"这个脚本作为工具，其只读承诺是否经得起敌意输入"。
+也就是说：这张卡要交付的 census 结论（92 条的分类、对账、三态、挂载真相、稳定键，以及输入前后终态字节一致）**已经过关**；卡住的是"这个脚本作为工具，其只读承诺是否经得起敌意输入"。
 
 - **一个无需竞态的真实绕过**：大小写不敏感卷上 `/Users/...` 与 `/users/...` 是同一个目录但 realpath 字符串不同，我 round-6 用来防御的 `os.path.normcase` **在 macOS/Linux 上根本是恒等函数**——这是我的知识性错误。改成逐级比较 **inode 身份**，不再依赖任何字符串。
 - **五项绕过共用一个根源**：它们都依附于"截断一个已存在的文件"这个动作。改成「新建临时文件 → 写 → fsync → 原子替换」后，脚本**全文再没有任何截断调用**——"截断某个既有对象"这条**具体路径**不复存在，"崩溃留下半个台账"的风险也一并消除。实测：拿一个指向恢复源的 hardlink 当 `--out`，台账正常写出，而**源文件内容一个字节没变**。⚠️ 这**不等于**"所有别名类绕过都已失效"：`lstat`→`replace` 之间仍有竞态窗口，已登记 FU-B/FU-C。
 - **扫描受阻不再只是标记**：看不全就意味着保护集不完整，现在直接拒绝写出台账。
 
 round-7 整改后第七次全量重跑：**92 条、4/88/0/0、89/2/1、6/29、shasum 不变、台账 0600、无临时文件残留——七轮整改数字全程未变**。
 
 ## 🔧 Codex round-8 复审整改记录（裁定分离重申 + 3 BLOCKER 全闭）

exec
/bin/zsh -lc "git -c core.quotePath=false diff --unified=8 05c85324 543e8a34 -- '_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md' '_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
diff --git a/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md b/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md
index 9eaa362f..dfe6d5ed 100644
--- a/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md
+++ b/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md
@@ -84,17 +84,17 @@ docker exec canvas-learning-system-backend sha256sum /app/data/dead_letter_episo
 **隐私（MEDIUM-3 整改）**：`transcript_paths` 含本机用户名与完整 session UUID，台账与本报告为 **private-only 工件**（台账头部已带 privacy 字段；仓库纪律 = 不 push 公网远端）。
 
 逐条另带 `class / inline_state / recoverability / transcript_paths / transcript_match_count / attribution_conflict / error_excerpt / failed_at / reference_time`，G4-10 可直接按 `recoverability` 分桶排重放优先级（建议：4 条 byte_exact 先行——但其中 3 条 group_id 为已弃用 `vault:default`，重放前需按 D16 规约重映射并过 `to_physical_group_id()`；89 条 budget_400 重放前必须先修 context 超限根因，否则原样重放必然复现 400）。
 
 ## §7 裁判证据（整改版脚本重跑）
 
 | 证据 | 结果 |
 |---|---|
-| 运行前后 shasum（live/主仓/孤儿①/孤儿② 四份 DLQ + qa_metrics.db） | `diff shasums-before.txt shasums-after.txt` 空 → **PASS，0 写入** |
+| 运行前后 shasum（live/主仓/孤儿①/孤儿② 四份 DLQ + qa_metrics.db） | `diff shasums-before.txt shasums-after.txt` 空 → **本次留存的 before/after 样本 SHA 相同**。⚠️ 该证据只证明**前后终态字节一致**，**不证明**读取期间零写入，也**不证明**每轮均留存了独立证据（仓库只保留最新一对） |
 | grep 自证（import 行全 stdlib；neo4j/graphiti/bolt/app. import 0 命中；`--apply` 定义 0 命中；写模式 open 仅 `--out` 1 处且受路径碰撞守卫保护） | **PASS**（`grep-selfattest.txt`，含守卫在位证明） |
 | 容器内 sha 实测 | 92 行、sha 与宿主 live 地址一致（`container-sha-check.txt`） |
 | class 偏差 | 无（89/2/1 与勘探预期一致，脚本 `class_deviation` 字段为空） |
 | 负例门（round-1 整改自证） | `--out`==`--dlq` → exit 2 拒写、DLQ 完好；transcripts 根缺失 → exit 2 拒诊；sha 匹配但长度不符（round-1 HIGH-1 反例①）→ anomaly/unrecoverable；坏 JSON 行/空行 → unparseable 逐行入台账不拒诊 |
 | 负例门（round-2 整改自证） | **hardlink** 指向 DLQ 的 --out → exit 2 + DLQ sha 不变；**case-only 别名**（`DLQ.jsonl`）→ exit 2 + DLQ 完好；**anomaly + episode_body_full 组合**（sha 对但长度 999）→ anomaly/unrecoverable（不再翻案 byte_exact）；**chmod 000 根** → exit 2 拒诊；**symlink 逃逸**（根内 .jsonl → 根外 .txt）→ match_count=0/unrecoverable；正例回归：真实唯一命中仍 approximate |
 
 ## §7b Codex round-1 整改记录（BLOCKED → 全项整改）
 
@@ -272,8 +272,28 @@ round-11 重申「**无需补必需①②③**」，并把剩余阻断收敛为
 1. **清除残留声明**（DB 静止当事实 / 逐次·运行零写入 / 整类绕过失效 / "20 个测试整体证明路径 fail-closed"）。已逐处改写：
    - 脚本 docstring 中"本卡场景为单人本机、DB 静止（实测 0 行、16384 bytes），故不影响结论"→ 改为"该假定**由操作者保证**（行数为 0、字节数固定、前后 SHA 相同都**不能证明**读取期间没有并发写者）"。
    - "对 20+ 类误用/攻击路径 fail-closed（回归测试固化）"→ 改为"**每条行为测试各自断言的那一个具体场景** fail-closed —— 这是逐例证据，**不构成**'所有误用路径均 fail-closed'的整体证明"。
    - "整类绕过全部失效"→ 改为"'截断某个既有对象'这条**具体路径**不再存在（已就 hardlink / 根内 symlink / FIFO 三场景各自取证）；⚠️ 不等于声称所有别名类绕过已失效——`lstat`→`replace` 竞态等残余见 FU-B/FU-C"。UAT 同处过强表述一并修正。
 2. **测试补强**：坏 JSON 用例改为**直接断言原始 `unparseable_lines` 恰为三项**（不经 dict 压缩，避免同 line_no 覆盖掩盖重复条目）再逐条精确断言；输入不变测试加入**非 JSONL sentinel** 文件并覆盖 transcripts 根内**全部常规文件**（原只哈希 `*.jsonl`，与"覆盖根内全部文件"的说法不符）；测试 docstring 改为"**所有行为测试**的断言均针对真实文件系统效果"并补范围声明。
 3. **重跑并更新可绑定证据**：`readonly-contract-tests.txt` 已用新 script/test blob 重生成（脚本 blob `87266e09…`、测试 blob `541ec8b3…`，含各自 sha256 与逐项 PASSED 明细）。**20 passed**。
 
 round-11 整改后第十一次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变——十一轮整改数字全程未变**。
+
+## §7n Codex round-12 三层裁定与最后两条措辞整改
+
+round-12 首次给出**三层分别裁定**：
+
+| 层 | 裁定 | 依据 |
+|---|---|---|
+| (a) 92 条冻结 ledger | **PASS，可验收** | 从 exact raw DLQ 与 `records[]` 独立复算一致：92 条 / class 89-2-1 / byte_exact 4·approximate 88·unverifiable 0·unrecoverable 0 / 重复簇 6-29 / unparseable 0 / attribution_conflict 3 全为 `no_token` |
+| (b) 生成器（已声明有界前提下） | **PASS，可验收** | 前提明确为单人本机、非共享目录、DB 静止由操作者保证；坏 JSON、sentinel 与全部常规文件覆盖、测试范围声明均已补强，**未发现 round-11 所指虚假通过空间** |
+| 可绑定证据 | **PASS** | `f4112c2c` tree 中脚本/test blob 确为 `87266e09…`/`541ec8b3…`，独立 SHA-256 与证据一致，20 个 PASSED 名称与测试 blob 的 20 个函数逐项对应 |
+| (c) 报告与 UAT 声明 | **FAIL** | DB 静止与逐例测试措辞已收敛，但仍有非引述性过强断言（下述两条） |
+
+最后两条整改（Codex 明示"无需再改测试、脚本或重生成绑定证据"）：
+
+1. **"0 写入 / 逐次取证 / 输入零改动"→ 准确表述**：报告 §7 裁判表与 UAT 三处已统一改为"**本次留存的 before/after 样本 SHA 相同**；⚠️ 只证明**前后终态字节一致**，**不证明**读取期间零写入，也**不证明**每轮均留存独立证据（仓库只保留最新一对）"。判据名亦由"全程零写入/输入零改动"改为"**输入前后终态一致**"。
+2. **"五项绕过整类失效"→ 具体路径表述**：UAT round-7 行改为"「截断某个既有对象」这一**具体路径**不再存在，**不代表所有别名类绕过均已失效**（`lstat`→`replace` 竞态见 FU-B/FU-C）"。
+
+这两条的共同点与前十一轮一致：**证据支持的是"前后终态一致"与"某条具体路径消失"，我却写成了"零写入"与"整类失效"**。改的是措辞，不是结论——台账数字与脚本行为均未变动。
+
+round-12 整改后台账未重跑（本轮无脚本改动，`f4112c2c` 的 ledger 即最终版）：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0——十二轮整改数字全程未变**。
diff --git a/_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md b/_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md
index eece19dc..266b415d 100644
--- a/_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md
+++ b/_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md
@@ -5,31 +5,31 @@ date: 2026-08-28
 status: awaiting_user
 scope: "BATCH-2026-08-28-第五批 / CARD-G4-9 — live DLQ 92 条只读 census：分类/SHA 对账/可恢复性三态/挂载真相，产出 G4-10 交接台账"
 worktree: "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census"
 ---
 
 # UAT · CARD-G4-9 DLQ 真实挂载 census 分诊
 
 > [!info]+ 你不需要碰命令行 — 全部技术验证我已代跑（结果见下）
-> 这张卡**没有修任何东西，也没有恢复任何数据**——它是一次"清点尸体"的只读普查（脚本对输入零写入已逐次取证；安全边界见文末"诚实边界"段）：
+> 这张卡**没有修任何东西，也没有恢复任何数据**——它是一次"清点尸体"的只读普查（本次留存的 before/after 样本 SHA 相同——只说明前后终态一致，不证明读取期间零写入；安全边界见文末"诚实边界"段）：
 > 线上 Graphiti 写入失败后落进死信文件的 92 条记录，逐条查清"是什么死的、还能不能救、去哪里救"，
 > 给后续的 G4-10（真正做恢复的卡）留一份带稳定编号的台账。卡面如实标注：离日常使用价值远，属恢复能力地基。
 
 ## 📌 你需要过目的三个结论
 
 1. **92 条死信全部查清、零"待定"**：89 条是"内容太长超过本地模型 16384 token 上限"（未修，根因归 G4-10）；2 条是 5 月 14 日的 schema 冲突、1 条是旧 group_id 冒号格式——这 3 条的根因**当天之后就已修复**，不会再新增。
 2. **一条都不算丢**：4 条正文完整躺在死信文件里（可逐字节恢复）；88 条只存了前 200 字预览，但每一条都顺着线索找回了**唯一**源头会话记录（7 个会话的原始 transcript 全部还在你电脑上）——可近似重建（找到了源头 ≠ 已经恢复，真正重建是 G4-10 的活）。**不可恢复：0 条**。另清点出 6 组重复（29 条是同内容反复入队），G4-10 恢复时会先去重，不会把同一段写 16 遍。
 3. **死信文件的"真身"只有一处**：线上容器读写的是 `feature-obsidian-hybrid-dev` worktree 的 `backend/data/`（容器内实测 sha 一致）；主仓那份 685 行是 4 月的陈旧副本，另有两处孤儿残留——报告里有四址对照表，以后不会再查错文件。
 
 ## ✅ 技术验证（Claude 已代跑）
 
 | 项 | 结果 | 证据 |
 |---|---|---|
-| 输入零改动（裁判判据 e） | 运行前后**本次列出的输入**（四份 DLQ + qa_metrics.db）sha256 **逐字节不变**（diff 为空 → PASS）。注：证据包留存本次一对 before/after，非每轮各存一份 | `_bmad-output/审查/G4-9-evidence/shasums-before.txt` / `shasums-after.txt` |
+| 输入前后终态一致（裁判判据 e） | 运行前后**本次列出的输入**（四份 DLQ + qa_metrics.db）sha256 相同（diff 为空）。⚠️ 边界：这证明**前后终态字节一致**，**不证明**读取期间零写入；证据包只留存本次一对 before/after，**非每轮各存一份** | `_bmad-output/审查/G4-9-evidence/shasums-before.txt` / `shasums-after.txt` |
 | 脚本只读自证（判据 a） | import 行全 stdlib；neo4j/graphiti/bolt/app. import **0 命中**；`--apply` 定义 **0 命中**；**全文无任何截断调用**（写出走 O_EXCL 临时文件 + 原子替换） | `G4-9-evidence/grep-selfattest.txt` |
 | 只读契约回归测试（round-9 必需项④ + round-10 补强） | **20 passed**：**17 条行为测试**（subprocess 跑真实 CLI + 断言文件系统事实）+ **3 条源码静态检查**（弱证据，如实标注，不替代行为测试）。测试两次抓出真实问题：① 架构改动丢了文件类型门（FIFO 会被静默替换）；② `deserialize` 延迟验证使 malformed DB 炸掉整次 census。round-10 另修掉 4 处虚假通过窗口 | `backend/tests/regression/test_census_dead_letter_readonly_contract.py` |
 | live 挂载真相（判据 c） | 容器内 `sha256sum /app/data/dead_letter_episodes.jsonl` = 宿主 live 地址同值（92 行，`3b37460f…`）；compose :206-212 遮蔽史入报告 §1 | `G4-9-evidence/container-sha-check.txt` + 报告 §1 |
 | 分类零偏差（判据 b） | budget_400×**89** / schema×**2**（P0-4 已修，`entity_types.py:343`）/ group_id×**1**（sanitize 已兜，`group_id_compat.py:64`）——与勘探预期逐条一致，脚本 `class_deviation` 字段为空 | 台账 JSON `class_distribution` |
 | inline 完整性 + SHA 对账（判据 b） | 92/92 重算 sha256 对账：4 条 full_verified、88 条 truncated_prefix（`to_dict()` 的 `[:200]` 截断，`episode_worker.py:107`）、**0 条 anomaly** | 台账 JSON 逐条 `inline_state`/`sha_check` |
 | 源指针核销（判据 b，qa_metrics.db 源 fd 只读 + 内存副本） | `qa_error_logs` **0 行** → 0/92 可经 qa_metrics.db 溯源（诚实记录）；附加核销：llm_call_logs.db 无正文、outbox 空、episode_body_full 0 条；**有效源指针 = request_id 组内 session 归因 → 7 个 transcript 全部在盘实测存在** | 报告 §4 + 台账 `qa_metrics_probe` |
 | 可恢复性三态（判据 b） | 可字节级 **4** / 近似 **88** / 不可恢复 **0**；不可恢复清单显式成段 0 条、"待定" 0 条 | 报告 §5 + 台账 `recoverability_distribution` |
 | G4-10 稳定键（判据 d） | 逐条复合键 `{line_no, sha256_prefix, request_id}` + 台账头部冻结文件 sha；request_id 92 条仅 25 唯一值的实测证明单列不可作键 | 报告 §6 + 台账 `records[].stable_key` |
@@ -41,23 +41,25 @@ worktree: "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktre
 | round-3 findings 逐条整改 | **6/6 完成**：transcript 并入保护集 / O_NOFOLLOW+fstat 消 TOCTOU / os.walk 替 glob（不跟随目录 symlink+遍历错误显式捕获）/ 不可读候选 fail-closed / JSONL 严格 LF 分帧 / 非 dict 归 unparseable。6 条新反例实测全过、数字第三次不变 | 报告 §7d + `grep-selfattest.txt` |
 | Codex 复审 round-4 | **仍阻断**（1/6 CLOSED；2 新 BLOCKER + 1 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round4.md` |
 | round-4 findings 逐条整改 | **9/9 完成**：全候选入保护集 / 读侧 fd 身份消源侧 TOCTOU / 新增 unverifiable 第四态 / FIFO 设备门 / strict UTF-8 / 3 条错型与边界 LOW / provenance receipt。5 条新反例实测全过；第四次全量重跑数字仍不变 | 报告 §7e + `grep-selfattest.txt` |
 | Codex 复审 round-5 | **仍阻断**（3/8 CLOSED；2 BLOCKER + 2 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round5.md` |
 | round-5 findings 逐条整改 | **9/9 完成**：先扫描后判定（冲突候选亦入保护集）/ QA DB fd 身份+复核 / 可见性优先于 anomaly / fchmod 后置于碰撞检查 / QA DB 特殊文件门 / no_token 归 unverifiable / 3 条 LOW。6 条新反例实测全过；第五次全量重跑数字仍不变 | 报告 §7f |
 | Codex 复审 round-6 | **6/9 CLOSED**（visibility 优先/fchmod 顺序/no_token 语义/3 条 LOW 已闭合）；剩 2 BLOCKER + 1 MEDIUM 揭示保护集**依赖枚举完整性**的架构缺陷 + 3 新发现 | `_bmad-output/审查/codex-review-CARD-G4-9-round6.md` |
 | round-6 findings 整改 | **架构级修复 + 6 项**：新增不依赖枚举的**路径层防御**（--out 禁落 transcripts 根内 / 禁等于任一输入 realpath）、QA DB 验证 fd 保持打开至复核完毕、no_token 亦扫描、证据包重生成、ledger 冲突原因自描述、lone surrogate 回退。反例实测：0333 隐藏目录内 transcript 作 --out → exit 2 完好 | 报告 §7g |
 | Codex 复审 round-7 | **关键裁定分离**："92 条冻结 ledger **可以采信**；生成器与 UAT 的纯只读安全声明不可验收"——卡面 census 判据已满足，阻断全在工具安全承诺侧。1 BLOCKER（大小写别名根，无需竞态）+ 4 项路径 TOCTOU + 1 MEDIUM（非原子写）+ 2 LOW | `_bmad-output/审查/codex-review-CARD-G4-9-round7.md` |
-| round-7 findings 整改 | **架构级第二次修复**：写出改 O_EXCL 临时文件+fsync+os.replace（**全文再无 ftruncate 调用**），五项绕过整类失效；containment 改 inode 逐级比较（normcase 在 POSIX 是恒等函数，我的假设错了）；扫描受阻直接拒绝写出。实测：根外 hardlink 指向根内 transcript 作 --out → 源内容完好 | 报告 §7h |
+| round-7 findings 整改 | **架构级第二次修复**：写出改 O_EXCL 临时文件+fsync+os.replace（**全文再无 ftruncate 调用**）——「截断某个既有对象」这一**具体路径**不再存在，**不代表所有别名类绕过均已失效**（lstat→replace 竞态见 FU-B/FU-C）；containment 改 inode 逐级比较（normcase 在 POSIX 是恒等函数，我的假设错了）；扫描受阻直接拒绝写出。实测：根外 hardlink 指向根内 transcript 作 --out → 源内容完好 | 报告 §7h |
 | Codex 复审 round-8 | 重申裁定分离：**「可验收：92 条冻结 ledger snapshot；不可验收：生成器一般安全性与 UAT 的纯只读声明」**。3 新 BLOCKER（SQLite URI 未转义 #/? / QA DB 仍按 pathname 开可 ABA / 根内末级 symlink 因 rename 不解析而被替换）+ 1 HIGH + 1 MEDIUM | `_bmad-output/审查/codex-review-CARD-G4-9-round8.md` |
 | round-8 findings 整改 | **6/6 完成**：QA DB 改「已验证 fd 读字节 → 内存库 deserialize」（URI 转义与 ABA 一并消失，含 #? 路径实测通过）；containment 加父目录语义（POSIX rename 不解析末级 symlink）；扫描受阻去掉 and args.out（stdout 模式亦拒）；replace 纳入 try + fsync 父目录 | 报告 §7i |
 | Codex 复审 round-9/10 | round-9 给出「最小剩余项」5 条；round-10 首次明确**「阻断不再要求补必需①②③」**，收敛为 4 条可执行要求：清除矛盾声明 / 修字段语义 / 如实标注测试覆盖 / 补可绑定证据。且十轮均确认 **92 条冻结 ledger 可验收** | `codex-review-CARD-G4-9-round9.md` / `-round10.md` |
 | round-10 解阻整改 | **6/6 完成**：脚本+报告+UAT 的 `mode=ro` 与「唯一写出口/全程零写入」矛盾表述全清（残留均为「已废弃」引述）；`source_fd_opened_readonly` 移到 fd 打开处（**顺带修出真 bug**：deserialize 延迟验证使 malformed DB 炸掉整次 census）；测试覆盖如实标注 17 行为+3 静态并修掉 4 处虚假通过窗口；证据补 HEAD/blob/sha256/逐项明细；「九次取证」与「DB 静止」改为准确表述与操作者前提 | 报告 §7k/§7l |
 | Codex 复审 round-11 | 重申**无需补必需①②③**；剩余阻断收敛为 3 条：清残留声明 / 坏 JSON 与输入不变测试补强 / 用新 blob 更新证据 | `codex-review-CARD-G4-9-round11.md` |
 | round-11 解阻整改 | **3/3 完成**：DB 静止改为操作者前提（0 行·固定字节·同 SHA 均不能证明无并发写者）、"20 类路径 fail-closed"改为逐例证据声明、"整类绕过失效"改为具体路径消失+残余竞态登记；坏 JSON 直接断言原始列表恰 3 项、输入不变测试加非 JSONL sentinel 并覆盖根内全部常规文件；证据绑定新 blob（脚本 87266e09/测试 541ec8b3）。20 passed | 报告 §7m |
+| Codex 复审 round-12（三层裁定） | **(a) 92 条冻结 ledger：PASS 可验收**（独立复算逐项一致）；**(b) 生成器在已声明有界前提下：PASS 可验收**（未发现虚假通过空间）；**可绑定证据：PASS**（blob/SHA/20 项名称逐项对应）；**(c) 报告与 UAT 声明：FAIL** —— 仅剩两条过强措辞 | `codex-review-CARD-G4-9-round12.md` |
+| round-12 措辞整改 | **2/2 完成**（Codex 明示无需再改测试/脚本/证据）："0 写入·逐次取证·输入零改动"统一改为"本次留存 before/after 样本 SHA 相同；不证明读取期间零写入、不证明每轮各存证据"；"五项绕过整类失效"改为"『截断既有对象』这一具体路径不再存在，不代表所有别名类绕过均已失效" | 报告 §7n |
 | 独立 Workflow 4-agent 复核 | G4-9 数字 agent：92 条重算 **0 mismatch**（class/inline/三态/25 request_id/7 transcript 在盘/台账 sha 全 CONFIRMED，仅 2 处描述区间 REFUTED 已修正）；只读契约 agent：与 Codex 同源的 3 条 blocker（已随上整改） | Workflow wf_737b1a95-20b journal |
 
 ## 🔧 Codex round-1 整改记录（13/13 关闭，BLOCKED → 整改完毕）
 
 - **BLOCKER-1 --out 截断风险**：任意 --out 路径 "w" 无守卫，可覆盖 DLQ 自身（双审查独立实测复现）。整改：写前 resolve() 路径碰撞守卫，命中输入集合即 exit 2；负例实测拒绝、DLQ 完好。
 - **BLOCKER-2 快照不原子**：records 与头部 sha 来自两次读取。整改：单次 read_bytes()，头部与逐条同源同字节。
 - **BLOCKER-3 交付物漂移**：审查期间脚本/报告 sha 变化且未 track。整改：本卡 commit 冻结全部 exact bytes；自证文件内嵌脚本 sha 前缀。
 - **HIGH-1 inline 判定 fail-open**：sha 匹配但长度不符会误判 full_verified（反例实测）。整改：长度精确匹配门 + 64-hex 合法性门 + anomaly 一律 fail-closed（unrecoverable + 如实 basis）。
@@ -126,17 +128,17 @@ round-6 指出了一个我补丁修不掉的根因：**保护集依赖"能不能
 round-6 整改后第六次全量重跑：**92 条、4/88/0/0、89/2/1、6/29、shasum 不变——六轮整改数字全程未变**。
 
 ## 🔧 Codex round-7 复审整改记录（关键裁定分离 + 架构级第二次修复）
 
 round-7 把结论分成了两半，这个区分很重要：
 
 > **「现有 92 条冻结 ledger 可以采信；生成器与 UAT 的纯只读安全声明不可验收。」**
 
-也就是说：这张卡要交付的 census 结论（92 条的分类、对账、三态、挂载真相、稳定键、运行零写入）**已经过关**；卡住的是"这个脚本作为工具，其只读承诺是否经得起敌意输入"。
+也就是说：这张卡要交付的 census 结论（92 条的分类、对账、三态、挂载真相、稳定键，以及输入前后终态字节一致）**已经过关**；卡住的是"这个脚本作为工具，其只读承诺是否经得起敌意输入"。
 
 - **一个无需竞态的真实绕过**：大小写不敏感卷上 `/Users/...` 与 `/users/...` 是同一个目录但 realpath 字符串不同，我 round-6 用来防御的 `os.path.normcase` **在 macOS/Linux 上根本是恒等函数**——这是我的知识性错误。改成逐级比较 **inode 身份**，不再依赖任何字符串。
 - **五项绕过共用一个根源**：它们都依附于"截断一个已存在的文件"这个动作。改成「新建临时文件 → 写 → fsync → 原子替换」后，脚本**全文再没有任何截断调用**——"截断某个既有对象"这条**具体路径**不复存在，"崩溃留下半个台账"的风险也一并消除。实测：拿一个指向恢复源的 hardlink 当 `--out`，台账正常写出，而**源文件内容一个字节没变**。⚠️ 这**不等于**"所有别名类绕过都已失效"：`lstat`→`replace` 之间仍有竞态窗口，已登记 FU-B/FU-C。
 - **扫描受阻不再只是标记**：看不全就意味着保护集不完整，现在直接拒绝写出台账。
 
 round-7 整改后第七次全量重跑：**92 条、4/88/0/0、89/2/1、6/29、shasum 不变、台账 0600、无临时文件残留——七轮整改数字全程未变**。
 
 ## 🔧 Codex round-8 复审整改记录（裁定分离重申 + 3 BLOCKER 全闭）

exec
/bin/zsh -lc "git show '543e8a34:CURRENT_TASK.md' | sed -n '1,220p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
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

**Planning targeted git line retrievals**
**Preparing full UAT 1-180 output**
exec
/bin/zsh -lc "git show '543e8a34:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md' | nl -ba | sed -n '1,180p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
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
    13	> 这张卡**没有修任何东西，也没有恢复任何数据**——它是一次"清点尸体"的只读普查（本次留存的 before/after 样本 SHA 相同——只说明前后终态一致，不证明读取期间零写入；安全边界见文末"诚实边界"段）：
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
    27	| 输入前后终态一致（裁判判据 e） | 运行前后**本次列出的输入**（四份 DLQ + qa_metrics.db）sha256 相同（diff 为空）。⚠️ 边界：这证明**前后终态字节一致**，**不证明**读取期间零写入；证据包只留存本次一对 before/after，**非每轮各存一份** | `_bmad-output/审查/G4-9-evidence/shasums-before.txt` / `shasums-after.txt` |
    28	| 脚本只读自证（判据 a） | import 行全 stdlib；neo4j/graphiti/bolt/app. import **0 命中**；`--apply` 定义 **0 命中**；**全文无任何截断调用**（写出走 O_EXCL 临时文件 + 原子替换） | `G4-9-evidence/grep-selfattest.txt` |
    29	| 只读契约回归测试（round-9 必需项④ + round-10 补强） | **20 passed**：**17 条行为测试**（subprocess 跑真实 CLI + 断言文件系统事实）+ **3 条源码静态检查**（弱证据，如实标注，不替代行为测试）。测试两次抓出真实问题：① 架构改动丢了文件类型门（FIFO 会被静默替换）；② `deserialize` 延迟验证使 malformed DB 炸掉整次 census。round-10 另修掉 4 处虚假通过窗口 | `backend/tests/regression/test_census_dead_letter_readonly_contract.py` |
    30	| live 挂载真相（判据 c） | 容器内 `sha256sum /app/data/dead_letter_episodes.jsonl` = 宿主 live 地址同值（92 行，`3b37460f…`）；compose :206-212 遮蔽史入报告 §1 | `G4-9-evidence/container-sha-check.txt` + 报告 §1 |
    31	| 分类零偏差（判据 b） | budget_400×**89** / schema×**2**（P0-4 已修，`entity_types.py:343`）/ group_id×**1**（sanitize 已兜，`group_id_compat.py:64`）——与勘探预期逐条一致，脚本 `class_deviation` 字段为空 | 台账 JSON `class_distribution` |
    32	| inline 完整性 + SHA 对账（判据 b） | 92/92 重算 sha256 对账：4 条 full_verified、88 条 truncated_prefix（`to_dict()` 的 `[:200]` 截断，`episode_worker.py:107`）、**0 条 anomaly** | 台账 JSON 逐条 `inline_state`/`sha_check` |
    33	| 源指针核销（判据 b，qa_metrics.db 源 fd 只读 + 内存副本） | `qa_error_logs` **0 行** → 0/92 可经 qa_metrics.db 溯源（诚实记录）；附加核销：llm_call_logs.db 无正文、outbox 空、episode_body_full 0 条；**有效源指针 = request_id 组内 session 归因 → 7 个 transcript 全部在盘实测存在** | 报告 §4 + 台账 `qa_metrics_probe` |
    34	| 可恢复性三态（判据 b） | 可字节级 **4** / 近似 **88** / 不可恢复 **0**；不可恢复清单显式成段 0 条、"待定" 0 条 | 报告 §5 + 台账 `recoverability_distribution` |
    35	| G4-10 稳定键（判据 d） | 逐条复合键 `{line_no, sha256_prefix, request_id}` + 台账头部冻结文件 sha；request_id 92 条仅 25 唯一值的实测证明单列不可作键 | 报告 §6 + 台账 `records[].stable_key` |
    36	| Codex 独立审查 round-1 | **BLOCKED**（3 BLOCKER：--out 可截断输入 / 快照不原子 / 交付物未冻结；3 HIGH：inline 判定 fail-open / request_id 归因传染 / transcript 归因折叠；3 MEDIUM + 4 LOW。同时确认：**当前 92 条数字逐项 0 mismatch**、class/三态/家族计数全对） | `_bmad-output/审查/codex-review-CARD-G4-9.md` |
    37	| Codex findings 逐条整改 | **13/13 完成**（见下）；整改版脚本负例门全过；全量重跑数字与整改前逐项一致 | 报告 §7/§7b + 证据包 |
    38	| Codex 复审 round-2 | **仍阻断**（10/13 CLOSED；BLOCKER-1/HIGH-1/HIGH-3 未真正闭合 + 3 新 LOW）。同时独立复算确认：67ccebe1 冻结生效、92 条数字与 6/29 重复簇全部可复算 | `_bmad-output/审查/codex-review-CARD-G4-9-round2.md`（codex 被 cyber 误拦，内容由 stdout 抢救存档） |
    39	| round-2 findings 逐条整改 | **6/6 完成**：inode 身份守卫封 hardlink+大小写别名 / full_body 长度门+anomaly 前置 / 不可读根 exit 2+symlink 逃逸拒采信 / 3 新 LOW。5 条新负例实测全过、正例无回归、数字仍逐项一致 | 报告 §7/§7c + `grep-selfattest.txt` |
    40	| Codex 复审 round-3 | **仍阻断**（4/6 CLOSED；BLOCKER-1/HIGH-3 判 PARTIAL + 1 新 MEDIUM + 2 新 LOW）。同时确认：HIGH-1 与三条 LOW 已闭合、台账数字有效且与 commit 字节一致 | `_bmad-output/审查/codex-review-CARD-G4-9-round3.md` |
    41	| round-3 findings 逐条整改 | **6/6 完成**：transcript 并入保护集 / O_NOFOLLOW+fstat 消 TOCTOU / os.walk 替 glob（不跟随目录 symlink+遍历错误显式捕获）/ 不可读候选 fail-closed / JSONL 严格 LF 分帧 / 非 dict 归 unparseable。6 条新反例实测全过、数字第三次不变 | 报告 §7d + `grep-selfattest.txt` |
    42	| Codex 复审 round-4 | **仍阻断**（1/6 CLOSED；2 新 BLOCKER + 1 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round4.md` |
    43	| round-4 findings 逐条整改 | **9/9 完成**：全候选入保护集 / 读侧 fd 身份消源侧 TOCTOU / 新增 unverifiable 第四态 / FIFO 设备门 / strict UTF-8 / 3 条错型与边界 LOW / provenance receipt。5 条新反例实测全过；第四次全量重跑数字仍不变 | 报告 §7e + `grep-selfattest.txt` |
    44	| Codex 复审 round-5 | **仍阻断**（3/8 CLOSED；2 BLOCKER + 2 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round5.md` |
    45	| round-5 findings 逐条整改 | **9/9 完成**：先扫描后判定（冲突候选亦入保护集）/ QA DB fd 身份+复核 / 可见性优先于 anomaly / fchmod 后置于碰撞检查 / QA DB 特殊文件门 / no_token 归 unverifiable / 3 条 LOW。6 条新反例实测全过；第五次全量重跑数字仍不变 | 报告 §7f |
    46	| Codex 复审 round-6 | **6/9 CLOSED**（visibility 优先/fchmod 顺序/no_token 语义/3 条 LOW 已闭合）；剩 2 BLOCKER + 1 MEDIUM 揭示保护集**依赖枚举完整性**的架构缺陷 + 3 新发现 | `_bmad-output/审查/codex-review-CARD-G4-9-round6.md` |
    47	| round-6 findings 整改 | **架构级修复 + 6 项**：新增不依赖枚举的**路径层防御**（--out 禁落 transcripts 根内 / 禁等于任一输入 realpath）、QA DB 验证 fd 保持打开至复核完毕、no_token 亦扫描、证据包重生成、ledger 冲突原因自描述、lone surrogate 回退。反例实测：0333 隐藏目录内 transcript 作 --out → exit 2 完好 | 报告 §7g |
    48	| Codex 复审 round-7 | **关键裁定分离**："92 条冻结 ledger **可以采信**；生成器与 UAT 的纯只读安全声明不可验收"——卡面 census 判据已满足，阻断全在工具安全承诺侧。1 BLOCKER（大小写别名根，无需竞态）+ 4 项路径 TOCTOU + 1 MEDIUM（非原子写）+ 2 LOW | `_bmad-output/审查/codex-review-CARD-G4-9-round7.md` |
    49	| round-7 findings 整改 | **架构级第二次修复**：写出改 O_EXCL 临时文件+fsync+os.replace（**全文再无 ftruncate 调用**）——「截断某个既有对象」这一**具体路径**不再存在，**不代表所有别名类绕过均已失效**（lstat→replace 竞态见 FU-B/FU-C）；containment 改 inode 逐级比较（normcase 在 POSIX 是恒等函数，我的假设错了）；扫描受阻直接拒绝写出。实测：根外 hardlink 指向根内 transcript 作 --out → 源内容完好 | 报告 §7h |
    50	| Codex 复审 round-8 | 重申裁定分离：**「可验收：92 条冻结 ledger snapshot；不可验收：生成器一般安全性与 UAT 的纯只读声明」**。3 新 BLOCKER（SQLite URI 未转义 #/? / QA DB 仍按 pathname 开可 ABA / 根内末级 symlink 因 rename 不解析而被替换）+ 1 HIGH + 1 MEDIUM | `_bmad-output/审查/codex-review-CARD-G4-9-round8.md` |
    51	| round-8 findings 整改 | **6/6 完成**：QA DB 改「已验证 fd 读字节 → 内存库 deserialize」（URI 转义与 ABA 一并消失，含 #? 路径实测通过）；containment 加父目录语义（POSIX rename 不解析末级 symlink）；扫描受阻去掉 and args.out（stdout 模式亦拒）；replace 纳入 try + fsync 父目录 | 报告 §7i |
    52	| Codex 复审 round-9/10 | round-9 给出「最小剩余项」5 条；round-10 首次明确**「阻断不再要求补必需①②③」**，收敛为 4 条可执行要求：清除矛盾声明 / 修字段语义 / 如实标注测试覆盖 / 补可绑定证据。且十轮均确认 **92 条冻结 ledger 可验收** | `codex-review-CARD-G4-9-round9.md` / `-round10.md` |
    53	| round-10 解阻整改 | **6/6 完成**：脚本+报告+UAT 的 `mode=ro` 与「唯一写出口/全程零写入」矛盾表述全清（残留均为「已废弃」引述）；`source_fd_opened_readonly` 移到 fd 打开处（**顺带修出真 bug**：deserialize 延迟验证使 malformed DB 炸掉整次 census）；测试覆盖如实标注 17 行为+3 静态并修掉 4 处虚假通过窗口；证据补 HEAD/blob/sha256/逐项明细；「九次取证」与「DB 静止」改为准确表述与操作者前提 | 报告 §7k/§7l |
    54	| Codex 复审 round-11 | 重申**无需补必需①②③**；剩余阻断收敛为 3 条：清残留声明 / 坏 JSON 与输入不变测试补强 / 用新 blob 更新证据 | `codex-review-CARD-G4-9-round11.md` |
    55	| round-11 解阻整改 | **3/3 完成**：DB 静止改为操作者前提（0 行·固定字节·同 SHA 均不能证明无并发写者）、"20 类路径 fail-closed"改为逐例证据声明、"整类绕过失效"改为具体路径消失+残余竞态登记；坏 JSON 直接断言原始列表恰 3 项、输入不变测试加非 JSONL sentinel 并覆盖根内全部常规文件；证据绑定新 blob（脚本 87266e09/测试 541ec8b3）。20 passed | 报告 §7m |
    56	| Codex 复审 round-12（三层裁定） | **(a) 92 条冻结 ledger：PASS 可验收**（独立复算逐项一致）；**(b) 生成器在已声明有界前提下：PASS 可验收**（未发现虚假通过空间）；**可绑定证据：PASS**（blob/SHA/20 项名称逐项对应）；**(c) 报告与 UAT 声明：FAIL** —— 仅剩两条过强措辞 | `codex-review-CARD-G4-9-round12.md` |
    57	| round-12 措辞整改 | **2/2 完成**（Codex 明示无需再改测试/脚本/证据）："0 写入·逐次取证·输入零改动"统一改为"本次留存 before/after 样本 SHA 相同；不证明读取期间零写入、不证明每轮各存证据"；"五项绕过整类失效"改为"『截断既有对象』这一具体路径不再存在，不代表所有别名类绕过均已失效" | 报告 §7n |
    58	| 独立 Workflow 4-agent 复核 | G4-9 数字 agent：92 条重算 **0 mismatch**（class/inline/三态/25 request_id/7 transcript 在盘/台账 sha 全 CONFIRMED，仅 2 处描述区间 REFUTED 已修正）；只读契约 agent：与 Codex 同源的 3 条 blocker（已随上整改） | Workflow wf_737b1a95-20b journal |
    59	
    60	## 🔧 Codex round-1 整改记录（13/13 关闭，BLOCKED → 整改完毕）
    61	
    62	- **BLOCKER-1 --out 截断风险**：任意 --out 路径 "w" 无守卫，可覆盖 DLQ 自身（双审查独立实测复现）。整改：写前 resolve() 路径碰撞守卫，命中输入集合即 exit 2；负例实测拒绝、DLQ 完好。
    63	- **BLOCKER-2 快照不原子**：records 与头部 sha 来自两次读取。整改：单次 read_bytes()，头部与逐条同源同字节。
    64	- **BLOCKER-3 交付物漂移**：审查期间脚本/报告 sha 变化且未 track。整改：本卡 commit 冻结全部 exact bytes；自证文件内嵌脚本 sha 前缀。
    65	- **HIGH-1 inline 判定 fail-open**：sha 匹配但长度不符会误判 full_verified（反例实测）。整改：长度精确匹配门 + 64-hex 合法性门 + anomaly 一律 fail-closed（unrecoverable + 如实 basis）。
    66	- **HIGH-2 request_id 归因传染**：缺失值合入 "None" 组、跨类型合组、多 token 静默取长。整改：(类型,值) 复合键 + 缺失单条成组 + 前缀一致门（冲突拒采信）。
    67	- **HIGH-3 transcript 归因折叠**：多命中照单全收、目录缺失误判 unrecoverable=88（实测复现）。整改：恰 1 常规文件命中门 + 递归 glob + 目录缺失 exit 2 拒诊。
    68	- **MEDIUM-1~3**：episode_body_full 采信通路 / duplicate_clusters 6 簇 29 行 + reference_time 透传 / privacy 字段与 private-only 声明。
    69	- **LOW-1~4**：两处区间修正（16948–20831、205–8036）/ 稳定键语义重写为"冻结快照 occurrence key" / schema 双处证据（LearningConcept.name + LearningTip.created_at）/ 挂载历史证据边界声明。
    70	
    71	整改后全量重跑：92 条数字与整改前**逐项一致**（4/88/0、89/2/1、冲突 0、unparseable 0）——整改只收紧契约与通用鲁棒性，不改变本次 census 结论。
    72	
    73	## 🔧 Codex round-2 复审整改记录（10/13 CLOSED → 剩 3 项 + 3 新 LOW 全关闭）
    74	
    75	round-2 用真实入口反例证明我 round-1 的三处整改**没有真正闭合**（这正是二轮审查的价值）：
    76	
    77	- **BLOCKER-1 未闭合**：守卫比的是路径字符串，**hardlink 与大小写别名照样截断 DLQ**。→ 改比**文件 inode 身份**；两种绕过实测双双 exit 2、DLQ sha 不变。
    78	- **HIGH-1 未闭合**：`episode_body_full` 分支只核 sha 不核长度且排在 anomaly 之前，**anomaly 记录能翻案成"可字节级恢复"**。→ 加长度门 + 判定顺序改为 anomaly 优先；反例实测翻转。
    79	- **HIGH-3 未闭合**：`chmod 000` 的目录仍 exit 0 并把全部记录**假判不可恢复**；symlink 可指到目录外冒充源。→ 不可读即 exit 2；symlink 与逃逸目标一律不采信；正例（真实唯一命中）无回归。
    80	- **3 新 LOW**：full_verified 长度范围修正 131–180；台账三个 distribution 补零并新增 `inline_state_distribution`；`line_count` 与 records 改用同一 `splitlines()` 口径。
    81	
    82	round-2 整改后再次全量重跑：92 条、4/88/0、89/2/1、6 簇 29 行、shasum 不变——**数字全程未变**。
    83	
    84	## 🔧 Codex round-3 复审整改记录（4/6 CLOSED → 剩 2 项 + 3 新发现全关闭）
    85	
    86	round-3 确认 HIGH-1 与三条 LOW 真正闭合、台账数字有效，又在两项路径安全上找到更深的绕过：
    87	
    88	- **BLOCKER-1 仍 PARTIAL**：① 保护集漏了**归因到的 transcript**——`--out` 指向它会截断恢复源；② check-then-open 的 **TOCTOU** 仍在。→ ① transcript 写前并入保护集；② 改 `O_NOFOLLOW` 打开且**不带 O_TRUNC**，对实际 fd `fstat` 校验后才 `ftruncate`。反例实测：exit 2、transcript 完好。
    89	- **HIGH-3 仍 PARTIAL**：Python 3.14 的 `glob` 在过滤前就已递归、跟随目录 symlink 且**静默吞掉不可读子树错误**；mode 000 的文件仍过 `isfile()` 被当可用源。→ 改 `os.walk(onerror=, followlinks=False)` + `os.access(R_OK)` 门；遍历受阻或有不可读候选一律拒绝裁定。三反例实测 fail-closed。
    90	- **新 MEDIUM（JSONL 分帧）**：`splitlines()` 会把含 U+2028 的合法单行记录劈成两条坏行。→ 严格按 LF 分帧，header 与 records 共用同一函数。
    91	- **新 LOW ×2**：非 dict JSON（`null`/数组）归 unparseable 不再炸全量；报告头补 artifact commit 链。
    92	
    93	round-3 整改后第三次全量重跑：**92 条、4/88/0、89/2/1、6/29、shasum 不变——三轮整改数字全程未变**，改的全是通用鲁棒性与路径安全。
    94	
    95	## 🔧 Codex round-4 复审整改记录（1/6 CLOSED → 9 项全关闭）
    96	
    97	round-4 只认 1 项闭合，用更深的反例推翻其余"闭合"——两条新 BLOCKER 都是真的：
    98	
    99	- **不可读但可写（mode 0200）的 transcript 绕过保护集**：我在"不可读"分支把候选路径清空了，于是它没进保护集，`--out` 指向它照样截断——不需要任何竞态。→ 新增"全候选清单"，无论可读与否一律并入保护集。
   100	- **源侧 TOCTOU**：保护身份按路径 stat 采集、DLQ 稍后才按路径读取，中间可换 inode。→ 改为**从 fd 读取**：打开一次 → `fstat` 取身份 → 从同一 fd 读全量，保护的就是实际读到的那个对象。
   101	- **把"看不见"说成"不可恢复"**：扫描受阻时仍输出 `unrecoverable`，与报告里"既不宣称不可恢复"自相矛盾。→ 新增第四态 **`unverifiable`**，逐条写明是遍历受阻还是候选不可读。
   102	- **其余 5 项**：FIFO/设备节点门（`O_NONBLOCK`+`S_ISREG`）、非法 UTF-8 不再经 replace 冒充有效记录（strict decode）、三条错型与边界 LOW（`name=None`/`request_id=[]`/根为 `/`）、既有输出文件 `fchmod` 收紧（台账现为 `-rw-------`）、provenance 改后置 receipt 绑定精确 commit 链。
   103	
   104	round-4 整改后第四次全量重跑：**92 条、4/88/0（unverifiable 0）、89/2/1、6/29、shasum 不变——四轮整改数字全程未变**。
   105	
   106	## 🔧 Codex round-5 复审整改记录（3/8 CLOSED → 9 项全关闭）
   107	
   108	round-5 继续深挖，两条新 BLOCKER 与两条 HIGH 都成立：
   109	
   110	- **冲突组的候选没进保护集**：token 冲突时我在扫描**之前**就早退了，那些候选从没被看到，`--out` 指向它们照样截断。→ 改成**先扫描后判定**，无论最终是否采信，见到的候选一律进保护集。
   111	- **qa_metrics.db 身份没绑定实际读取**：先按路径 stat、SQLite 稍后按路径重开，中间可换。→ 改 fd 取身份 + 打开后复核身份一致。
   112	- **anomaly 吞掉了"看不见"**：`anomaly→unrecoverable` 排在可见性判断之前，扫描受阻时仍断言"不可恢复"。→ 判定链改为**可见性优先**。
   113	- **`fchmod` 排在碰撞检查之前**：`--out` 指向受保护的只读输入时，会先把它的权限从 644 改成 600 才发现碰撞——字节没丢但输入被改了。→ 碰撞检查前移。
   114	- **其余 5 项**：QA DB 特殊文件门、无 token 归 `unverifiable`、单独换行算 1 空行、strict encode 堵住 lone surrogate 伪造 `full_verified`、`bool` 不再通过长度门。
   115	
   116	**一处计数如实变化**：归因冲突 0→3。因为"名字不含 session token"现在被诚实标为"未做归因扫描"，正是那 3 条 callout 记录；它们 inline 全量、不依赖 transcript，仍是可字节级恢复。**三态分布不变**（4/88/0/0）——是标注变诚实，不是结论变化。
   117	
   118	round-5 整改后第五次全量重跑：**92 条、4/88/0/0、89/2/1、6/29、shasum 不变——五轮整改数字全程未变**。
   119	
   120	## 🔧 Codex round-6 复审整改记录（6/9 CLOSED → 架构级修复）
   121	
   122	round-6 指出了一个我补丁修不掉的根因：**保护集依赖"能不能枚举到"**。不可列举但可穿越的目录（`0333`）里的 transcript，`os.walk` 看不见，就进不了保护集，`--out` 指向它照样截断；QA DB 的 inode 被 A→B→A 换过也一样。
   123	
   124	→ 改为**双层防御**：在 inode 保护集之外，加一层**不依赖枚举**的路径判断——`--out` 的真实路径不得落在 transcripts 根目录内（整个恢复源区域禁写），也不得等于任何输入文件的真实路径。实测：隐藏目录内的 transcript 作 `--out`，inode 保护集根本没看见它，路径层直接拦住，exit 2、文件完好。
   125	
   126	另修：QA DB 的验证 fd 改为**保持打开**到复核完毕（堵 ABA）；`no_token` 分支也扫描（原本完全不扫，候选进不了保护集）；证据包每轮重生成（round-6 指出我的 self-attest 停留在 round-4 的旧 SHA，属实）；台账新增冲突原因自描述。
   127	
   128	round-6 整改后第六次全量重跑：**92 条、4/88/0/0、89/2/1、6/29、shasum 不变——六轮整改数字全程未变**。
   129	
   130	## 🔧 Codex round-7 复审整改记录（关键裁定分离 + 架构级第二次修复）
   131	
   132	round-7 把结论分成了两半，这个区分很重要：
   133	
   134	> **「现有 92 条冻结 ledger 可以采信；生成器与 UAT 的纯只读安全声明不可验收。」**
   135	
   136	也就是说：这张卡要交付的 census 结论（92 条的分类、对账、三态、挂载真相、稳定键，以及输入前后终态字节一致）**已经过关**；卡住的是"这个脚本作为工具，其只读承诺是否经得起敌意输入"。
   137	
   138	- **一个无需竞态的真实绕过**：大小写不敏感卷上 `/Users/...` 与 `/users/...` 是同一个目录但 realpath 字符串不同，我 round-6 用来防御的 `os.path.normcase` **在 macOS/Linux 上根本是恒等函数**——这是我的知识性错误。改成逐级比较 **inode 身份**，不再依赖任何字符串。
   139	- **五项绕过共用一个根源**：它们都依附于"截断一个已存在的文件"这个动作。改成「新建临时文件 → 写 → fsync → 原子替换」后，脚本**全文再没有任何截断调用**——"截断某个既有对象"这条**具体路径**不复存在，"崩溃留下半个台账"的风险也一并消除。实测：拿一个指向恢复源的 hardlink 当 `--out`，台账正常写出，而**源文件内容一个字节没变**。⚠️ 这**不等于**"所有别名类绕过都已失效"：`lstat`→`replace` 之间仍有竞态窗口，已登记 FU-B/FU-C。
   140	- **扫描受阻不再只是标记**：看不全就意味着保护集不完整，现在直接拒绝写出台账。
   141	
   142	round-7 整改后第七次全量重跑：**92 条、4/88/0/0、89/2/1、6/29、shasum 不变、台账 0600、无临时文件残留——七轮整改数字全程未变**。
   143	
   144	## 🔧 Codex round-8 复审整改记录（裁定分离重申 + 3 BLOCKER 全闭）
   145	
   146	round-8 把结论说得更清楚了：**「可验收：92 条冻结 ledger snapshot。不可验收：生成器的一般安全性，以及验收单里那句"纯只读、唯一写出口、整类 TOCTOU 已消失"」**。
   147	
   148	三条新 BLOCKER 都成立，其中两条有同一个彻底解法：
   149	
   150	- **SQLite 打开方式**：`file:路径?mode=ro` 这种写法，路径里只要有个 `#`，`mode=ro` 就掉进 URI 的 fragment 被忽略，SQLite 可能按默认的**读写模式**打开——这直接推翻"唯一写出口"。而且就算持有验证过的文件描述符，SQLite 还是按路径自己去开，中间被换掉也发现不了。→ 改成从**已验证的文件描述符读出全部字节，灌进内存数据库**。SQLite 从此不碰路径，两个问题一起消失。
   151	- **根内的软链接**：POSIX 规定重命名操作**不跟随末级软链接**。所以 `--out` 如果是恢复源目录里的一个软链接（指向外面），我按"它指向哪"判断会放行，但实际被替换的是**目录里那个链接本身**。→ 判定改看**父目录在不在恢复源里**。
   152	- **stdout 模式漏网**：扫描受阻的拒绝条件我写成了"且指定了 --out"，于是省略 `--out` 就能绕过。→ 去掉该条件。
   153	
   154	round-8 整改后第八次全量重跑：**92 条、4/88/0/0、89/2/1、6/29、shasum 不变、无 tmp 残留——八轮整改数字全程未变**。
   155	
   156	## 📄 交付物清单（全部新增，零业务代码改动）
   157	
   158	- `backend/scripts/census_dead_letter_episodes.py` — 唯一代码产物（只读 census 脚本，纯 stdlib）
   159	- `_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md` — census 报告（挂载真相/分类/三态/交接契约）
   160	- `_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json` — 92 条逐条台账（G4-10 消费）
   161	- `_bmad-output/审查/G4-9-evidence/` — 证据包（shasums ×2、grep 自证、容器 sha 实测、运行日志）
   162	- `_bmad-output/审查/codex-review-CARD-G4-9.md` — Codex 独立审查存档
   163	
   164	## 📐 诚实边界（round-9 收敛，替代原先过强的措辞）
   165	
   166	九轮对抗审查后，Codex 始终维持一个分层裁定：**「92 条冻结台账可以采信；但生成器的一般安全性、以及验收单里"纯只读、唯一写出口、整类 TOCTOU 已消失"这类绝对化声明不可验收」**。
   167	
   168	我接受这个区分，处置是**把声明改准确，而不是假装达标**：
   169	
   170	- **可以确证的**：本次运行对**本次列出的输入文件**（4 份 DLQ + qa_metrics.db）**shasum 前后逐字节不变**（证据包留存本次一对 before/after）；回归测试中**每条行为测试各自断言的那个场景** fail-closed（17 行为 + 3 静态）——**逐例证据，非"所有路径都安全"的整体证明**。
   171	- **前提（非结论）**："DB 静止"由操作者保证——0 行、固定 sha、前后同 SHA 本身**不能证明**读取期间没有并发写者。
   172	- **不再声称的**：在共享可写目录、有并发写者、SQLite DB 正被写入等**敌意环境**下具备生产级安全；也不声称"整类别名绕过已消失"（`lstat`→`replace` 竞态等残余见 FU-B/FU-C）。这类保证需要一致性快照、dirfd 相对发布、单写者锁——是把一次性 census 脚本升级为常驻工具的工作量，不在本卡范围。
   173	- **已登记的**：FU-A~FU-D 四项（报告 §7j），**G4-10 若复用本脚本于活跃 DB 或共享目录，须先补齐**。
   174	
   175	## ⏭️ 移交（不在本卡范围）
   176	
   177	- **G4-10**：89 条 budget_400 根因修复（16384 context 超限 → 切块或提 budget）+ 按台账重放；3 条 `vault:default` 旧格式重放前需 group 重映射。
   178	- **DeadLetterStore 全量正文开关**：`DEAD_LETTER_STORE_FULL_BODY` live 未启用是 88 条只剩前缀的直接原因——是否开启（隐私 vs 可恢复性权衡）留 G4-10 连根因一并裁。

exec
/bin/zsh -lc "git show '543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md' | nl -ba | sed -n '190,310p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
   190	- **BLOCKER① 补充修复**：`no_token` 分支原本完全不扫描（`all_candidate_paths=[]`）→ 改为**无论有无 token 都遍历**，所有 `.jsonl` 一律入保护集口径。
   191	- **MEDIUM（证据包漂移）**：`grep-selfattest.txt` 曾停留在 round-4 的脚本 SHA 与旧行号、receipt 未含最新 commit——这是我的疏漏。已重生成（内嵌当前脚本 sha256 + 生成时点声明），receipt 随本轮补链。
   192	- **LOW ×3**：ledger 新增 `attribution_conflict_reason` 自描述（本次 92 条：`no_token` 3 / 其余 89 无冲突）；`json.dumps` 对 lone surrogate 回退 `ensure_ascii=True` 并显式标注，不再整次 census 拒绝；`stat_failures` 分支保留（Codex 确认非额外绕过，仅基本不可达）。
   193	
   194	round-6 整改后第六次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变——六轮整改数字全程未变**。
   195	
   196	## §7h Codex round-7 复审整改记录（关键裁定分离 + 架构级第二次修复）
   197	
   198	round-7 给出了本卡最重要的一次裁定分离：
   199	
   200	> **「现有 92 条冻结 ledger 可以采信；CARD-G4-9 生成器与 UAT 的纯只读安全声明不可验收。」**
   201	
   202	即：卡面的 census 判据（分类/对账/三态/挂载真相/稳定键/shasum 不变）已满足且被独立复算确认；阻断项全部落在"生成器作为工具的只读安全承诺"上。逐条整改：
   203	
   204	- **BLOCKER（大小写别名根）**：本机实测 `/Users/Heishing/.claude/projects` 与 `/users/heishing/...` `samefile=True` 但 `realpath` 字符串不同，prefix guard 返回 False——**无需竞态的实际绕过**。我 round-6 用的 `os.path.normcase` 在 POSIX 上是**恒等函数**（假设错误）。**整改**：新增 `_path_is_within()`，从目标逐级向上比较 **inode 身份**，完全不依赖路径字符串；`--out` 与输入文件的比较改 `os.path.samefile`。实测：别名根作 `--out` → exit 2，正例无回归。
   205	- **NOT-CLOSED ×4（根外 hardlink 指向隐藏目录内 transcript / 根 retarget TOCTOU / 检查后换父目录 symlink 或 basename hardlink）+ MEDIUM（非原子写）**：这五项依附于同一个动作——**截断一个已存在的文件**。**架构级修复**：写出改为「同目录 `O_EXCL` 新建临时文件 → 写 → `fsync` → `os.replace` 原子替换」，**全文再无任何 `ftruncate` 调用**。`O_EXCL` 保证写入目标是本进程新建的对象，因此"截断既有对象"这条具体路径消失（三场景各自取证，不声称整类绕过均已失效）；`os.replace` 同时消除崩溃/ENOSPC 留下部分台账的风险。实测：根外 hardlink 指向根内 transcript 作 `--out` → 台账正常写出而**源文件内容完好**（`os.replace` 只重绑定该名字，不触碰底层 inode）。
   206	- **NOT-CLOSED（扫描受阻仅标记不停写）**：扫描受阻 ⇒ 保护集必然不完整。**整改**：`scan_errors`/`stat_failures` 非空时**直接拒绝写出台账**（exit 2），实测不落盘。
   207	- **LOW（lone surrogate 回退失效）**：异常发生在后续 `write`，不在原 `try` 内。**整改**：`json.dumps` 后立即 `.encode("utf-8")` 探测，编码错误在写出前暴露并回退 `ensure_ascii=True`。
   208	- **LOW（receipt 用 8 位缩写）**：如实登记为已知限制（仓库内唯一可解析），未改为 40-hex 以保持 receipt 可读性——列 follow-up。
   209	
   210	round-7 整改后第七次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变、台账 mode 0600、无临时文件残留——七轮整改数字全程未变**。
   211	
   212	## §7i Codex round-8 复审整改记录（裁定分离重申 + 3 BLOCKER 全闭）
   213	
   214	round-8 重申 round-7 的裁定分离，措辞更明确：
   215	
   216	> **可验收：92 条冻结 ledger snapshot。不可验收：当前生成器的一般安全性，以及 UAT 的"纯只读、唯一写出口、整类 TOCTOU 已消失"声明。**
   217	
   218	三条新 BLOCKER 全部属实，逐条整改：
   219	
   220	- **BLOCKER①（SQLite URI 未转义）**：`file:{db_path}?mode=ro` 在路径含 `#` 时，`mode=ro` 会落进被忽略的 URI fragment，SQLite 可能按**默认读写模式**打开——直接反驳"唯一写出口"。
   221	- **BLOCKER②（QA DB 仍按 pathname 打开）**：验证 fd 保持打开也没用，SQLite 另按路径解析，A→B→A 可让 connection 读到 B 而复核看到 A。
   222	- **①②的共同解法**：不再让 SQLite 碰路径——从**已验证的 fd** 读全量字节 → `sqlite3` 内存库 `deserialize()`。URI 转义问题与 ABA **一并消失**，且全程不落任何文件。实测：路径含 `#` 与 `?` 的 DB 正常只读（`read_mode: in_memory_deserialize_from_verified_fd`，16384 bytes）。
   223	- **BLOCKER③（根内末级 symlink）**：POSIX 规定 `rename`/`replace` **不解析末级 symlink**——`--out` 若是根内 symlink 指向根外，`realpath` 判"根外"而放行，但 replace 实际替换的是**根内那个目录项**。**整改**：containment 改用**父目录语义**（`dirname` 在根内即拒），叠加原有末级判定。实测：根内 symlink 作 `--out` → exit 2，symlink 未被替换。
   224	- **HIGH（扫描受阻拒绝不完整）**：no_token/token_conflict 分支在写入 `scan_errors` **之前**就早退；且拒绝条件写作 `scan_blocked and args.out`，**省略 `--out` 走 stdout 即可绕过**。**整改**：早退分支同样记录扫描错误；拒绝条件去掉 `and args.out`。实测：stdout 模式扫描受阻同样 exit 2。
   225	- **MEDIUM（tmp 残留 + 未 fsync 父目录）**：`os.replace` 在 `try` 外，`EXDEV/EBUSY/EACCES/ENOSPC` 会冒泡并留下 tmp。**整改**：replace 纳入 try，异常一律 `unlink` tmp；成功后 `fsync` 父目录使重命名落盘。
   226	
   227	round-8 整改后第八次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变、无 tmp 残留——八轮整改数字全程未变**。
   228	
   229	## §7j Codex round-9 裁定与收敛（声明改为有界，剩余项显式移交）
   230	
   231	round-9 维持分层裁定并给出"达到可验收的最小剩余项"清单。我的处置分两类：
   232	
   233	**已修（本轮完成）**
   234	
   235	- **必需⑤ 名实不符（DD-13 硬伤）**：改用内存 `deserialize` 后，字段仍叫 `opened_readonly`、docstring 仍称 SQLite URI `mode=ro`——**实际只有源 fd 只读，内存连接可写**。已改字段名为 `source_fd_opened_readonly`，docstring 如实说明只读保证的来源（源 fd 只读 + 内存副本与源解耦），补 `PRAGMA query_only=ON` 作纵深防御，并把 QA DB 的 `source_sha256` 写入台账（与证据包 shasum 一致）。
   236	- **必需④ 无测试引用生成器**：新增 `backend/tests/regression/test_census_dead_letter_readonly_contract.py`，把 8 轮审查中被实测封死的 **19 条**反例全部固化（每条注明对应轮次与 finding；覆盖构成如实标注于文件 docstring）。该测试**当场抓出一个真实回归**：round-7 改用 `os.replace` 发布后不再打开 `--out`，`S_ISREG` 门随之丢失，FIFO 会被静默替换成普通文件——已补回文件类型门（`--out` 若已存在且非常规文件、或是 symlink，一律拒绝）。**20 passed**（round-10 又补强了 4 处虚假通过窗口并新增 1 条 malformed DB 用例）。
   237	
   238	**改为有界声明（不再宣称已解决）**
   239	
   240	round-9 的必需①②③（一致性 SQLite 快照、单一稳定 dirfd 发布、tmp/发布者/状态绑定与单写者锁）是把这个**一次性 census 脚本**升级为**生产级并发安全工具**的要求。本卡不做，理由如实记录：本卡场景为单人本机、目录非共享可写；**"DB 静止"与"无并发写者"是操作者提供的前提，不是本卡证明的结论**（0 行 / 固定字节数 / 前后同 SHA 均不能证明读取期间无写者）。**处置方式是收敛声明而非假装达标**——报告头与验收单已删去"纯只读 / 唯一写出口 / 整类 TOCTOU 已消失"这类绝对化措辞，改为"本次运行输入 shasum 前后不变（已取证）+ 对 20+ 类误用路径 fail-closed（测试固化）+ 不声称敌意环境下的生产级安全"。
   241	
   242	**移交 follow-up（G4-10 复用本脚本前必须补齐）**
   243	
   244	| # | 项 | 触发条件 |
   245	|---|---|---|
   246	| FU-A | SQLite 一致性快照（backup API 或要求外部先冻结 DB）+ 显式拒绝 WAL/journal/并发变化 | DB 非静止时 |
   247	| FU-B | 输出发布全程相对同一 `O_DIRECTORY\|O_NOFOLLOW` dirfd（create/replace/fsync/unlink） | 输出目录可能被他人操纵时 |
   248	| FU-C | 不可预测 tmp 名 + 单写者锁/CAS + `published_but_durability_unconfirmed` 状态 + 崩溃残留 reconciliation | 共享可写目录或并发运行时 |
   249	| FU-D | `O_CLOEXEC`、拒绝空 basename、内存库完整性检查 | 建议项（round-9 列为 suggested） |
   250	
   251	round-9 整改后第九次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变、只读契约测试 19 passed——九轮整改数字全程未变**。
   252	
   253	## §7k Codex round-10 裁定与解阻整改
   254	
   255	round-10 首次明确：**「阻断原因不是必需①②③未实现」**——分类处置（修硬伤 + 固化测试 + 收敛声明 + 显式移交）被判定为**原则上可以收口**。剩余阻断项收敛为四条可执行要求，本轮全部完成：
   256	
   257	1. **彻底清除矛盾声明**：脚本模块 docstring 仍写 URI `mode=ro` 与"唯一写出口"（与同文件函数说明自相矛盾），报告 §4 与 UAT 亦仍称 `mode=ro`。已全部改写：模块契约段改述实际读法并新增"安全边界"段（可确证 / 不声称 / 前提三分），报告 §4 标题与正文同步。
   258	2. **修正字段语义**：`source_fd_opened_readonly` 原在 `deserialize` 成功后才置真——DB malformed 时 fd 确已只读打开却返回 false。已移到 fd 打开成功处。**该修正顺带暴露一个真 bug**：`deserialize` 是**延迟验证**，malformed DB 的 `DatabaseError` 在首次 `execute` 时才抛出，而查询段原本只有 `finally` 没有 `except`——**会炸掉整次 census**。已补 `sqlite3.Error` 捕获并记 `query_failed`，新增回归用例锁定。
   259	3. **如实标注测试覆盖**：原称"19 条反例全部固化 / 20+ 类路径"不实。现于测试文件 docstring 与本报告标注真实构成（**17 条行为测试跑真实 CLI + 3 条源码静态检查（弱证据）**，无 mock 无 skip），并修掉 round-10 点名的 4 处**虚假通过窗口**：FIFO 补验"仍是 FIFO 且无 tmp 残留"；扫描受阻补验 stdout 确无台账；坏 JSON 由 `A or B` 弱断言改为逐行精确断言（3 类坏行各一条）；输入不变测试从"DLQ + 单 transcript"扩展到 `--compare`、`--qa-metrics-db` 与根内全部文件。
   260	4. **补可绑定运行证据**：`readonly-contract-tests.txt` 由一行 `19 passed` 改为含精确命令、Python 版本、工作树 HEAD、**被测脚本与测试文件的 git blob**、脚本 sha256、覆盖构成声明与**逐项 PASSED 明细**。
   261	5. **"九次取证"表述收敛**：仓库只保留最新一对 before/after shasum，已改述为"本次留存一对，此前各轮亦逐次核对但未各存一份"。
   262	6. **"DB 静止"改为操作者前提**：0 行 / 固定 sha / 前后同 SHA 本身不能证明读取期间无写者——已在脚本"安全边界"段与本报告显式声明为**前提而非结论**。
   263	
   264	round-10 整改后第十次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变、只读契约测试 20 passed（17 行为 + 3 静态）——十轮整改数字全程未变**。
   265	
   266	**Codex 十轮裁定轨迹（如实留档）**：round-1 BLOCKED → round-2/3 部分闭合 → round-4/5/6 每轮揭示更深层缺陷（其中 round-6 与 round-7 两次触发架构级重做）→ round-7 起稳定为**分层裁定**「92 条冻结 ledger 可采信 / 生成器安全声明不可验收」→ round-10 明确「阻断不再要求补必需①②③，只需清除矛盾声明、修字段语义、如实标注测试覆盖、补可绑定证据」。本轮四条全部完成。
   267	
   268	## §7m Codex round-11 解阻整改（3 条必须再做项全部完成）
   269	
   270	round-11 重申「**无需补必需①②③**」，并把剩余阻断收敛为三条：
   271	
   272	1. **清除残留声明**（DB 静止当事实 / 逐次·运行零写入 / 整类绕过失效 / "20 个测试整体证明路径 fail-closed"）。已逐处改写：
   273	   - 脚本 docstring 中"本卡场景为单人本机、DB 静止（实测 0 行、16384 bytes），故不影响结论"→ 改为"该假定**由操作者保证**（行数为 0、字节数固定、前后 SHA 相同都**不能证明**读取期间没有并发写者）"。
   274	   - "对 20+ 类误用/攻击路径 fail-closed（回归测试固化）"→ 改为"**每条行为测试各自断言的那一个具体场景** fail-closed —— 这是逐例证据，**不构成**'所有误用路径均 fail-closed'的整体证明"。
   275	   - "整类绕过全部失效"→ 改为"'截断某个既有对象'这条**具体路径**不再存在（已就 hardlink / 根内 symlink / FIFO 三场景各自取证）；⚠️ 不等于声称所有别名类绕过已失效——`lstat`→`replace` 竞态等残余见 FU-B/FU-C"。UAT 同处过强表述一并修正。
   276	2. **测试补强**：坏 JSON 用例改为**直接断言原始 `unparseable_lines` 恰为三项**（不经 dict 压缩，避免同 line_no 覆盖掩盖重复条目）再逐条精确断言；输入不变测试加入**非 JSONL sentinel** 文件并覆盖 transcripts 根内**全部常规文件**（原只哈希 `*.jsonl`，与"覆盖根内全部文件"的说法不符）；测试 docstring 改为"**所有行为测试**的断言均针对真实文件系统效果"并补范围声明。
   277	3. **重跑并更新可绑定证据**：`readonly-contract-tests.txt` 已用新 script/test blob 重生成（脚本 blob `87266e09…`、测试 blob `541ec8b3…`，含各自 sha256 与逐项 PASSED 明细）。**20 passed**。
   278	
   279	round-11 整改后第十一次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变——十一轮整改数字全程未变**。
   280	
   281	## §7n Codex round-12 三层裁定与最后两条措辞整改
   282	
   283	round-12 首次给出**三层分别裁定**：
   284	
   285	| 层 | 裁定 | 依据 |
   286	|---|---|---|
   287	| (a) 92 条冻结 ledger | **PASS，可验收** | 从 exact raw DLQ 与 `records[]` 独立复算一致：92 条 / class 89-2-1 / byte_exact 4·approximate 88·unverifiable 0·unrecoverable 0 / 重复簇 6-29 / unparseable 0 / attribution_conflict 3 全为 `no_token` |
   288	| (b) 生成器（已声明有界前提下） | **PASS，可验收** | 前提明确为单人本机、非共享目录、DB 静止由操作者保证；坏 JSON、sentinel 与全部常规文件覆盖、测试范围声明均已补强，**未发现 round-11 所指虚假通过空间** |
   289	| 可绑定证据 | **PASS** | `f4112c2c` tree 中脚本/test blob 确为 `87266e09…`/`541ec8b3…`，独立 SHA-256 与证据一致，20 个 PASSED 名称与测试 blob 的 20 个函数逐项对应 |
   290	| (c) 报告与 UAT 声明 | **FAIL** | DB 静止与逐例测试措辞已收敛，但仍有非引述性过强断言（下述两条） |
   291	
   292	最后两条整改（Codex 明示"无需再改测试、脚本或重生成绑定证据"）：
   293	
   294	1. **"0 写入 / 逐次取证 / 输入零改动"→ 准确表述**：报告 §7 裁判表与 UAT 三处已统一改为"**本次留存的 before/after 样本 SHA 相同**；⚠️ 只证明**前后终态字节一致**，**不证明**读取期间零写入，也**不证明**每轮均留存独立证据（仓库只保留最新一对）"。判据名亦由"全程零写入/输入零改动"改为"**输入前后终态一致**"。
   295	2. **"五项绕过整类失效"→ 具体路径表述**：UAT round-7 行改为"「截断某个既有对象」这一**具体路径**不再存在，**不代表所有别名类绕过均已失效**（`lstat`→`replace` 竞态见 FU-B/FU-C）"。
   296	
   297	这两条的共同点与前十一轮一致：**证据支持的是"前后终态一致"与"某条具体路径消失"，我却写成了"零写入"与"整类失效"**。改的是措辞，不是结论——台账数字与脚本行为均未变动。
   298	
   299	round-12 整改后台账未重跑（本轮无脚本改动，`f4112c2c` 的 ledger 即最终版）：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0——十二轮整改数字全程未变**。

exec
/bin/zsh -lc "git -c core.quotePath=false diff --unified=3 f4112c2c 543e8a34 -- '_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
diff --git a/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md b/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md
index 9eaa362f..dfe6d5ed 100644
--- a/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md
+++ b/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md
@@ -89,7 +89,7 @@ docker exec canvas-learning-system-backend sha256sum /app/data/dead_letter_episo
 
 | 证据 | 结果 |
 |---|---|
-| 运行前后 shasum（live/主仓/孤儿①/孤儿② 四份 DLQ + qa_metrics.db） | `diff shasums-before.txt shasums-after.txt` 空 → **PASS，0 写入** |
+| 运行前后 shasum（live/主仓/孤儿①/孤儿② 四份 DLQ + qa_metrics.db） | `diff shasums-before.txt shasums-after.txt` 空 → **本次留存的 before/after 样本 SHA 相同**。⚠️ 该证据只证明**前后终态字节一致**，**不证明**读取期间零写入，也**不证明**每轮均留存了独立证据（仓库只保留最新一对） |
 | grep 自证（import 行全 stdlib；neo4j/graphiti/bolt/app. import 0 命中；`--apply` 定义 0 命中；写模式 open 仅 `--out` 1 处且受路径碰撞守卫保护） | **PASS**（`grep-selfattest.txt`，含守卫在位证明） |
 | 容器内 sha 实测 | 92 行、sha 与宿主 live 地址一致（`container-sha-check.txt`） |
 | class 偏差 | 无（89/2/1 与勘探预期一致，脚本 `class_deviation` 字段为空） |
@@ -277,3 +277,23 @@ round-11 重申「**无需补必需①②③**」，并把剩余阻断收敛为
 3. **重跑并更新可绑定证据**：`readonly-contract-tests.txt` 已用新 script/test blob 重生成（脚本 blob `87266e09…`、测试 blob `541ec8b3…`，含各自 sha256 与逐项 PASSED 明细）。**20 passed**。
 
 round-11 整改后第十一次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变——十一轮整改数字全程未变**。
+
+## §7n Codex round-12 三层裁定与最后两条措辞整改
+
+round-12 首次给出**三层分别裁定**：
+
+| 层 | 裁定 | 依据 |
+|---|---|---|
+| (a) 92 条冻结 ledger | **PASS，可验收** | 从 exact raw DLQ 与 `records[]` 独立复算一致：92 条 / class 89-2-1 / byte_exact 4·approximate 88·unverifiable 0·unrecoverable 0 / 重复簇 6-29 / unparseable 0 / attribution_conflict 3 全为 `no_token` |
+| (b) 生成器（已声明有界前提下） | **PASS，可验收** | 前提明确为单人本机、非共享目录、DB 静止由操作者保证；坏 JSON、sentinel 与全部常规文件覆盖、测试范围声明均已补强，**未发现 round-11 所指虚假通过空间** |
+| 可绑定证据 | **PASS** | `f4112c2c` tree 中脚本/test blob 确为 `87266e09…`/`541ec8b3…`，独立 SHA-256 与证据一致，20 个 PASSED 名称与测试 blob 的 20 个函数逐项对应 |
+| (c) 报告与 UAT 声明 | **FAIL** | DB 静止与逐例测试措辞已收敛，但仍有非引述性过强断言（下述两条） |
+
+最后两条整改（Codex 明示"无需再改测试、脚本或重生成绑定证据"）：
+
+1. **"0 写入 / 逐次取证 / 输入零改动"→ 准确表述**：报告 §7 裁判表与 UAT 三处已统一改为"**本次留存的 before/after 样本 SHA 相同**；⚠️ 只证明**前后终态字节一致**，**不证明**读取期间零写入，也**不证明**每轮均留存独立证据（仓库只保留最新一对）"。判据名亦由"全程零写入/输入零改动"改为"**输入前后终态一致**"。
+2. **"五项绕过整类失效"→ 具体路径表述**：UAT round-7 行改为"「截断某个既有对象」这一**具体路径**不再存在，**不代表所有别名类绕过均已失效**（`lstat`→`replace` 竞态见 FU-B/FU-C）"。
+
+这两条的共同点与前十一轮一致：**证据支持的是"前后终态一致"与"某条具体路径消失"，我却写成了"零写入"与"整类失效"**。改的是措辞，不是结论——台账数字与脚本行为均未变动。
+
+round-12 整改后台账未重跑（本轮无脚本改动，`f4112c2c` 的 ledger 即最终版）：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0——十二轮整改数字全程未变**。

exec
/bin/zsh -lc "git -c core.quotePath=false diff --unified=3 f4112c2c 543e8a34 -- '_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
diff --git a/_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md b/_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md
index eece19dc..266b415d 100644
--- a/_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md
+++ b/_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md
@@ -10,7 +10,7 @@ worktree: "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktre
 # UAT · CARD-G4-9 DLQ 真实挂载 census 分诊
 
 > [!info]+ 你不需要碰命令行 — 全部技术验证我已代跑（结果见下）
-> 这张卡**没有修任何东西，也没有恢复任何数据**——它是一次"清点尸体"的只读普查（脚本对输入零写入已逐次取证；安全边界见文末"诚实边界"段）：
+> 这张卡**没有修任何东西，也没有恢复任何数据**——它是一次"清点尸体"的只读普查（本次留存的 before/after 样本 SHA 相同——只说明前后终态一致，不证明读取期间零写入；安全边界见文末"诚实边界"段）：
 > 线上 Graphiti 写入失败后落进死信文件的 92 条记录，逐条查清"是什么死的、还能不能救、去哪里救"，
 > 给后续的 G4-10（真正做恢复的卡）留一份带稳定编号的台账。卡面如实标注：离日常使用价值远，属恢复能力地基。
 
@@ -24,7 +24,7 @@ worktree: "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktre
 
 | 项 | 结果 | 证据 |
 |---|---|---|
-| 输入零改动（裁判判据 e） | 运行前后**本次列出的输入**（四份 DLQ + qa_metrics.db）sha256 **逐字节不变**（diff 为空 → PASS）。注：证据包留存本次一对 before/after，非每轮各存一份 | `_bmad-output/审查/G4-9-evidence/shasums-before.txt` / `shasums-after.txt` |
+| 输入前后终态一致（裁判判据 e） | 运行前后**本次列出的输入**（四份 DLQ + qa_metrics.db）sha256 相同（diff 为空）。⚠️ 边界：这证明**前后终态字节一致**，**不证明**读取期间零写入；证据包只留存本次一对 before/after，**非每轮各存一份** | `_bmad-output/审查/G4-9-evidence/shasums-before.txt` / `shasums-after.txt` |
 | 脚本只读自证（判据 a） | import 行全 stdlib；neo4j/graphiti/bolt/app. import **0 命中**；`--apply` 定义 **0 命中**；**全文无任何截断调用**（写出走 O_EXCL 临时文件 + 原子替换） | `G4-9-evidence/grep-selfattest.txt` |
 | 只读契约回归测试（round-9 必需项④ + round-10 补强） | **20 passed**：**17 条行为测试**（subprocess 跑真实 CLI + 断言文件系统事实）+ **3 条源码静态检查**（弱证据，如实标注，不替代行为测试）。测试两次抓出真实问题：① 架构改动丢了文件类型门（FIFO 会被静默替换）；② `deserialize` 延迟验证使 malformed DB 炸掉整次 census。round-10 另修掉 4 处虚假通过窗口 | `backend/tests/regression/test_census_dead_letter_readonly_contract.py` |
 | live 挂载真相（判据 c） | 容器内 `sha256sum /app/data/dead_letter_episodes.jsonl` = 宿主 live 地址同值（92 行，`3b37460f…`）；compose :206-212 遮蔽史入报告 §1 | `G4-9-evidence/container-sha-check.txt` + 报告 §1 |
@@ -46,13 +46,15 @@ worktree: "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktre
 | Codex 复审 round-6 | **6/9 CLOSED**（visibility 优先/fchmod 顺序/no_token 语义/3 条 LOW 已闭合）；剩 2 BLOCKER + 1 MEDIUM 揭示保护集**依赖枚举完整性**的架构缺陷 + 3 新发现 | `_bmad-output/审查/codex-review-CARD-G4-9-round6.md` |
 | round-6 findings 整改 | **架构级修复 + 6 项**：新增不依赖枚举的**路径层防御**（--out 禁落 transcripts 根内 / 禁等于任一输入 realpath）、QA DB 验证 fd 保持打开至复核完毕、no_token 亦扫描、证据包重生成、ledger 冲突原因自描述、lone surrogate 回退。反例实测：0333 隐藏目录内 transcript 作 --out → exit 2 完好 | 报告 §7g |
 | Codex 复审 round-7 | **关键裁定分离**："92 条冻结 ledger **可以采信**；生成器与 UAT 的纯只读安全声明不可验收"——卡面 census 判据已满足，阻断全在工具安全承诺侧。1 BLOCKER（大小写别名根，无需竞态）+ 4 项路径 TOCTOU + 1 MEDIUM（非原子写）+ 2 LOW | `_bmad-output/审查/codex-review-CARD-G4-9-round7.md` |
-| round-7 findings 整改 | **架构级第二次修复**：写出改 O_EXCL 临时文件+fsync+os.replace（**全文再无 ftruncate 调用**），五项绕过整类失效；containment 改 inode 逐级比较（normcase 在 POSIX 是恒等函数，我的假设错了）；扫描受阻直接拒绝写出。实测：根外 hardlink 指向根内 transcript 作 --out → 源内容完好 | 报告 §7h |
+| round-7 findings 整改 | **架构级第二次修复**：写出改 O_EXCL 临时文件+fsync+os.replace（**全文再无 ftruncate 调用**）——「截断某个既有对象」这一**具体路径**不再存在，**不代表所有别名类绕过均已失效**（lstat→replace 竞态见 FU-B/FU-C）；containment 改 inode 逐级比较（normcase 在 POSIX 是恒等函数，我的假设错了）；扫描受阻直接拒绝写出。实测：根外 hardlink 指向根内 transcript 作 --out → 源内容完好 | 报告 §7h |
 | Codex 复审 round-8 | 重申裁定分离：**「可验收：92 条冻结 ledger snapshot；不可验收：生成器一般安全性与 UAT 的纯只读声明」**。3 新 BLOCKER（SQLite URI 未转义 #/? / QA DB 仍按 pathname 开可 ABA / 根内末级 symlink 因 rename 不解析而被替换）+ 1 HIGH + 1 MEDIUM | `_bmad-output/审查/codex-review-CARD-G4-9-round8.md` |
 | round-8 findings 整改 | **6/6 完成**：QA DB 改「已验证 fd 读字节 → 内存库 deserialize」（URI 转义与 ABA 一并消失，含 #? 路径实测通过）；containment 加父目录语义（POSIX rename 不解析末级 symlink）；扫描受阻去掉 and args.out（stdout 模式亦拒）；replace 纳入 try + fsync 父目录 | 报告 §7i |
 | Codex 复审 round-9/10 | round-9 给出「最小剩余项」5 条；round-10 首次明确**「阻断不再要求补必需①②③」**，收敛为 4 条可执行要求：清除矛盾声明 / 修字段语义 / 如实标注测试覆盖 / 补可绑定证据。且十轮均确认 **92 条冻结 ledger 可验收** | `codex-review-CARD-G4-9-round9.md` / `-round10.md` |
 | round-10 解阻整改 | **6/6 完成**：脚本+报告+UAT 的 `mode=ro` 与「唯一写出口/全程零写入」矛盾表述全清（残留均为「已废弃」引述）；`source_fd_opened_readonly` 移到 fd 打开处（**顺带修出真 bug**：deserialize 延迟验证使 malformed DB 炸掉整次 census）；测试覆盖如实标注 17 行为+3 静态并修掉 4 处虚假通过窗口；证据补 HEAD/blob/sha256/逐项明细；「九次取证」与「DB 静止」改为准确表述与操作者前提 | 报告 §7k/§7l |
 | Codex 复审 round-11 | 重申**无需补必需①②③**；剩余阻断收敛为 3 条：清残留声明 / 坏 JSON 与输入不变测试补强 / 用新 blob 更新证据 | `codex-review-CARD-G4-9-round11.md` |
 | round-11 解阻整改 | **3/3 完成**：DB 静止改为操作者前提（0 行·固定字节·同 SHA 均不能证明无并发写者）、"20 类路径 fail-closed"改为逐例证据声明、"整类绕过失效"改为具体路径消失+残余竞态登记；坏 JSON 直接断言原始列表恰 3 项、输入不变测试加非 JSONL sentinel 并覆盖根内全部常规文件；证据绑定新 blob（脚本 87266e09/测试 541ec8b3）。20 passed | 报告 §7m |
+| Codex 复审 round-12（三层裁定） | **(a) 92 条冻结 ledger：PASS 可验收**（独立复算逐项一致）；**(b) 生成器在已声明有界前提下：PASS 可验收**（未发现虚假通过空间）；**可绑定证据：PASS**（blob/SHA/20 项名称逐项对应）；**(c) 报告与 UAT 声明：FAIL** —— 仅剩两条过强措辞 | `codex-review-CARD-G4-9-round12.md` |
+| round-12 措辞整改 | **2/2 完成**（Codex 明示无需再改测试/脚本/证据）："0 写入·逐次取证·输入零改动"统一改为"本次留存 before/after 样本 SHA 相同；不证明读取期间零写入、不证明每轮各存证据"；"五项绕过整类失效"改为"『截断既有对象』这一具体路径不再存在，不代表所有别名类绕过均已失效" | 报告 §7n |
 | 独立 Workflow 4-agent 复核 | G4-9 数字 agent：92 条重算 **0 mismatch**（class/inline/三态/25 request_id/7 transcript 在盘/台账 sha 全 CONFIRMED，仅 2 处描述区间 REFUTED 已修正）；只读契约 agent：与 Codex 同源的 3 条 blocker（已随上整改） | Workflow wf_737b1a95-20b journal |
 
 ## 🔧 Codex round-1 整改记录（13/13 关闭，BLOCKED → 整改完毕）
@@ -131,7 +133,7 @@ round-7 把结论分成了两半，这个区分很重要：
 
 > **「现有 92 条冻结 ledger 可以采信；生成器与 UAT 的纯只读安全声明不可验收。」**
 
-也就是说：这张卡要交付的 census 结论（92 条的分类、对账、三态、挂载真相、稳定键、运行零写入）**已经过关**；卡住的是"这个脚本作为工具，其只读承诺是否经得起敌意输入"。
+也就是说：这张卡要交付的 census 结论（92 条的分类、对账、三态、挂载真相、稳定键，以及输入前后终态字节一致）**已经过关**；卡住的是"这个脚本作为工具，其只读承诺是否经得起敌意输入"。
 
 - **一个无需竞态的真实绕过**：大小写不敏感卷上 `/Users/...` 与 `/users/...` 是同一个目录但 realpath 字符串不同，我 round-6 用来防御的 `os.path.normcase` **在 macOS/Linux 上根本是恒等函数**——这是我的知识性错误。改成逐级比较 **inode 身份**，不再依赖任何字符串。
 - **五项绕过共用一个根源**：它们都依附于"截断一个已存在的文件"这个动作。改成「新建临时文件 → 写 → fsync → 原子替换」后，脚本**全文再没有任何截断调用**——"截断某个既有对象"这条**具体路径**不复存在，"崩溃留下半个台账"的风险也一并消除。实测：拿一个指向恢复源的 hardlink 当 `--out`，台账正常写出，而**源文件内容一个字节没变**。⚠️ 这**不等于**"所有别名类绕过都已失效"：`lstat`→`replace` 之间仍有竞态窗口，已登记 FU-B/FU-C。

**Analyzing receipt changes between commits**
**Planning focused diff on receipt file**
exec
/bin/zsh -lc "git show 'f4112c2c:_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt' | nl -ba" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
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
    15	f389980c  CARD-G4-9 round-7 架构级修复（消除截断动作）
    16	af251e4a  CARD-G4-9 round-8 整改（QA DB 内存 deserialize / 父目录 containment / stdout 门 / 原子替换清理）
    17	2cdf77a4  receipt 补 round-8
    18	6b8debee  CARD-G4-9 round-9 整改（名实一致 / 只读契约回归测试 / 声明有界化）
    19	dfbe70c7  CARD-G4-9 round-10 解阻整改（矛盾声明全清 / 字段语义 / 测试如实标注 20 passed / 可绑定证据）
    20	
    21	各阶段交付物 blob 可用 git cat-file 复核；台账头部 dlq_file.sha256 为 DLQ 快照指纹。

exec
/bin/zsh -lc "git show '05c85324:_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt' | nl -ba" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
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
    15	f389980c  CARD-G4-9 round-7 架构级修复（消除截断动作）
    16	af251e4a  CARD-G4-9 round-8 整改（QA DB 内存 deserialize / 父目录 containment / stdout 门 / 原子替换清理）
    17	2cdf77a4  receipt 补 round-8
    18	6b8debee  CARD-G4-9 round-9 整改（名实一致 / 只读契约回归测试 / 声明有界化）
    19	dfbe70c7  CARD-G4-9 round-10 解阻整改（矛盾声明全清 / 字段语义 / 测试如实标注 / 可绑定证据）
    20	f4112c2c  CARD-G4-9 round-11 解阻整改（残留声明清除 / 坏 JSON 与输入不变测试补强 / 证据绑新 blob）
    21	
    22	各阶段交付物 blob 可用 git cat-file 复核；台账头部 dlq_file.sha256 为 DLQ 快照指纹。

exec
/bin/zsh -lc "git show '543e8a34:_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt' | nl -ba" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
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
    15	f389980c  CARD-G4-9 round-7 架构级修复（消除截断动作）
    16	af251e4a  CARD-G4-9 round-8 整改（QA DB 内存 deserialize / 父目录 containment / stdout 门 / 原子替换清理）
    17	2cdf77a4  receipt 补 round-8
    18	6b8debee  CARD-G4-9 round-9 整改（名实一致 / 只读契约回归测试 / 声明有界化）
    19	dfbe70c7  CARD-G4-9 round-10 解阻整改（矛盾声明全清 / 字段语义 / 测试如实标注 / 可绑定证据）
    20	f4112c2c  CARD-G4-9 round-11 解阻整改（残留声明清除 / 坏 JSON 与输入不变测试补强 / 证据绑新 blob）
    21	
    22	各阶段交付物 blob 可用 git cat-file 复核；台账头部 dlq_file.sha256 为 DLQ 快照指纹。

exec
/bin/zsh -lc "git -c core.quotePath=false diff --unified=20 05c85324 543e8a34 -- '_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead

exec
/bin/zsh -lc "git -c core.quotePath=false diff --unified=20 f4112c2c 543e8a34 -- '_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
diff --git a/_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt b/_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt
index 9be8b423..a71e2031 100644
--- a/_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt
+++ b/_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt
@@ -1,21 +1,22 @@
 == CARD-G4-9 / CARD-G4-16 artifact commit receipt ==
 （commit 无法自含己身 SHA，故用本后置 receipt 精确绑定 —— Codex round-4 LOW 整改）
 
 37387a86  第五批开工基线（分析对象锚定 SHA，非本卡产物）
 67ccebe1  CARD-G4-9 初版交付（脚本/报告/台账/证据包/round-1 审查/UAT）
 e7a480eb  CARD-G4-16 初版交付（报告/证据包/两处注释修正/审查/UAT）
 73102875  round-2 findings 整改（两卡）
 fce0d8a2  round-3 findings 整改（两卡）
 94b420ff  CARD-G4-16 round-4 整改（重放 recipe 确定化）
 d2827a6d  CARD-G4-9 round-4 整改
 d8d887f2  本 receipt 首次落盘
 4c125f19  CARD-G4-9 round-5 整改
 5b371253  CARD-G4-9 round-6 架构级修复
 4ba4f847  receipt 补 round-5/6 链
 f389980c  CARD-G4-9 round-7 架构级修复（消除截断动作）
 af251e4a  CARD-G4-9 round-8 整改（QA DB 内存 deserialize / 父目录 containment / stdout 门 / 原子替换清理）
 2cdf77a4  receipt 补 round-8
 6b8debee  CARD-G4-9 round-9 整改（名实一致 / 只读契约回归测试 / 声明有界化）
-dfbe70c7  CARD-G4-9 round-10 解阻整改（矛盾声明全清 / 字段语义 / 测试如实标注 20 passed / 可绑定证据）
+dfbe70c7  CARD-G4-9 round-10 解阻整改（矛盾声明全清 / 字段语义 / 测试如实标注 / 可绑定证据）
+f4112c2c  CARD-G4-9 round-11 解阻整改（残留声明清除 / 坏 JSON 与输入不变测试补强 / 证据绑新 blob）
 
 各阶段交付物 blob 可用 git cat-file 复核；台账头部 dlq_file.sha256 为 DLQ 快照指纹。

exec
/bin/zsh -lc "git show '9104495b:_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt' | tail -n 12 | nl -ba" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
     1	4c125f19  CARD-G4-9 round-5 整改
     2	5b371253  CARD-G4-9 round-6 架构级修复
     3	4ba4f847  receipt 补 round-5/6 链
     4	f389980c  CARD-G4-9 round-7 架构级修复（消除截断动作）
     5	af251e4a  CARD-G4-9 round-8 整改（QA DB 内存 deserialize / 父目录 containment / stdout 门 / 原子替换清理）
     6	2cdf77a4  receipt 补 round-8
     7	6b8debee  CARD-G4-9 round-9 整改（名实一致 / 只读契约回归测试 / 声明有界化）
     8	dfbe70c7  CARD-G4-9 round-10 解阻整改（矛盾声明全清 / 字段语义 / 测试如实标注 / 可绑定证据）
     9	f4112c2c  CARD-G4-9 round-11 解阻整改（残留声明清除 / 测试补强 / 证据绑新 blob）
    10	543e8a34  CARD-G4-9 round-12 措辞整改（前后终态一致 / 具体路径而非整类失效）
    11	
    12	各阶段交付物 blob 可用 git cat-file 复核；台账头部 dlq_file.sha256 为 DLQ 快照指纹。

**Confirming no evidence changes in commit**
**Clarifying receipt as documentation metadata**
**Defining precise binding evidence scope**
**Inspecting binding section lines 250-280**
exec
/bin/zsh -lc "git show '543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md' | nl -ba | sed -n '248,302p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
   248	| FU-C | 不可预测 tmp 名 + 单写者锁/CAS + `published_but_durability_unconfirmed` 状态 + 崩溃残留 reconciliation | 共享可写目录或并发运行时 |
   249	| FU-D | `O_CLOEXEC`、拒绝空 basename、内存库完整性检查 | 建议项（round-9 列为 suggested） |
   250	
   251	round-9 整改后第九次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变、只读契约测试 19 passed——九轮整改数字全程未变**。
   252	
   253	## §7k Codex round-10 裁定与解阻整改
   254	
   255	round-10 首次明确：**「阻断原因不是必需①②③未实现」**——分类处置（修硬伤 + 固化测试 + 收敛声明 + 显式移交）被判定为**原则上可以收口**。剩余阻断项收敛为四条可执行要求，本轮全部完成：
   256	
   257	1. **彻底清除矛盾声明**：脚本模块 docstring 仍写 URI `mode=ro` 与"唯一写出口"（与同文件函数说明自相矛盾），报告 §4 与 UAT 亦仍称 `mode=ro`。已全部改写：模块契约段改述实际读法并新增"安全边界"段（可确证 / 不声称 / 前提三分），报告 §4 标题与正文同步。
   258	2. **修正字段语义**：`source_fd_opened_readonly` 原在 `deserialize` 成功后才置真——DB malformed 时 fd 确已只读打开却返回 false。已移到 fd 打开成功处。**该修正顺带暴露一个真 bug**：`deserialize` 是**延迟验证**，malformed DB 的 `DatabaseError` 在首次 `execute` 时才抛出，而查询段原本只有 `finally` 没有 `except`——**会炸掉整次 census**。已补 `sqlite3.Error` 捕获并记 `query_failed`，新增回归用例锁定。
   259	3. **如实标注测试覆盖**：原称"19 条反例全部固化 / 20+ 类路径"不实。现于测试文件 docstring 与本报告标注真实构成（**17 条行为测试跑真实 CLI + 3 条源码静态检查（弱证据）**，无 mock 无 skip），并修掉 round-10 点名的 4 处**虚假通过窗口**：FIFO 补验"仍是 FIFO 且无 tmp 残留"；扫描受阻补验 stdout 确无台账；坏 JSON 由 `A or B` 弱断言改为逐行精确断言（3 类坏行各一条）；输入不变测试从"DLQ + 单 transcript"扩展到 `--compare`、`--qa-metrics-db` 与根内全部文件。
   260	4. **补可绑定运行证据**：`readonly-contract-tests.txt` 由一行 `19 passed` 改为含精确命令、Python 版本、工作树 HEAD、**被测脚本与测试文件的 git blob**、脚本 sha256、覆盖构成声明与**逐项 PASSED 明细**。
   261	5. **"九次取证"表述收敛**：仓库只保留最新一对 before/after shasum，已改述为"本次留存一对，此前各轮亦逐次核对但未各存一份"。
   262	6. **"DB 静止"改为操作者前提**：0 行 / 固定 sha / 前后同 SHA 本身不能证明读取期间无写者——已在脚本"安全边界"段与本报告显式声明为**前提而非结论**。
   263	
   264	round-10 整改后第十次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变、只读契约测试 20 passed（17 行为 + 3 静态）——十轮整改数字全程未变**。
   265	
   266	**Codex 十轮裁定轨迹（如实留档）**：round-1 BLOCKED → round-2/3 部分闭合 → round-4/5/6 每轮揭示更深层缺陷（其中 round-6 与 round-7 两次触发架构级重做）→ round-7 起稳定为**分层裁定**「92 条冻结 ledger 可采信 / 生成器安全声明不可验收」→ round-10 明确「阻断不再要求补必需①②③，只需清除矛盾声明、修字段语义、如实标注测试覆盖、补可绑定证据」。本轮四条全部完成。
   267	
   268	## §7m Codex round-11 解阻整改（3 条必须再做项全部完成）
   269	
   270	round-11 重申「**无需补必需①②③**」，并把剩余阻断收敛为三条：
   271	
   272	1. **清除残留声明**（DB 静止当事实 / 逐次·运行零写入 / 整类绕过失效 / "20 个测试整体证明路径 fail-closed"）。已逐处改写：
   273	   - 脚本 docstring 中"本卡场景为单人本机、DB 静止（实测 0 行、16384 bytes），故不影响结论"→ 改为"该假定**由操作者保证**（行数为 0、字节数固定、前后 SHA 相同都**不能证明**读取期间没有并发写者）"。
   274	   - "对 20+ 类误用/攻击路径 fail-closed（回归测试固化）"→ 改为"**每条行为测试各自断言的那一个具体场景** fail-closed —— 这是逐例证据，**不构成**'所有误用路径均 fail-closed'的整体证明"。
   275	   - "整类绕过全部失效"→ 改为"'截断某个既有对象'这条**具体路径**不再存在（已就 hardlink / 根内 symlink / FIFO 三场景各自取证）；⚠️ 不等于声称所有别名类绕过已失效——`lstat`→`replace` 竞态等残余见 FU-B/FU-C"。UAT 同处过强表述一并修正。
   276	2. **测试补强**：坏 JSON 用例改为**直接断言原始 `unparseable_lines` 恰为三项**（不经 dict 压缩，避免同 line_no 覆盖掩盖重复条目）再逐条精确断言；输入不变测试加入**非 JSONL sentinel** 文件并覆盖 transcripts 根内**全部常规文件**（原只哈希 `*.jsonl`，与"覆盖根内全部文件"的说法不符）；测试 docstring 改为"**所有行为测试**的断言均针对真实文件系统效果"并补范围声明。
   277	3. **重跑并更新可绑定证据**：`readonly-contract-tests.txt` 已用新 script/test blob 重生成（脚本 blob `87266e09…`、测试 blob `541ec8b3…`，含各自 sha256 与逐项 PASSED 明细）。**20 passed**。
   278	
   279	round-11 整改后第十一次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变——十一轮整改数字全程未变**。
   280	
   281	## §7n Codex round-12 三层裁定与最后两条措辞整改
   282	
   283	round-12 首次给出**三层分别裁定**：
   284	
   285	| 层 | 裁定 | 依据 |
   286	|---|---|---|
   287	| (a) 92 条冻结 ledger | **PASS，可验收** | 从 exact raw DLQ 与 `records[]` 独立复算一致：92 条 / class 89-2-1 / byte_exact 4·approximate 88·unverifiable 0·unrecoverable 0 / 重复簇 6-29 / unparseable 0 / attribution_conflict 3 全为 `no_token` |
   288	| (b) 生成器（已声明有界前提下） | **PASS，可验收** | 前提明确为单人本机、非共享目录、DB 静止由操作者保证；坏 JSON、sentinel 与全部常规文件覆盖、测试范围声明均已补强，**未发现 round-11 所指虚假通过空间** |
   289	| 可绑定证据 | **PASS** | `f4112c2c` tree 中脚本/test blob 确为 `87266e09…`/`541ec8b3…`，独立 SHA-256 与证据一致，20 个 PASSED 名称与测试 blob 的 20 个函数逐项对应 |
   290	| (c) 报告与 UAT 声明 | **FAIL** | DB 静止与逐例测试措辞已收敛，但仍有非引述性过强断言（下述两条） |
   291	
   292	最后两条整改（Codex 明示"无需再改测试、脚本或重生成绑定证据"）：
   293	
   294	1. **"0 写入 / 逐次取证 / 输入零改动"→ 准确表述**：报告 §7 裁判表与 UAT 三处已统一改为"**本次留存的 before/after 样本 SHA 相同**；⚠️ 只证明**前后终态字节一致**，**不证明**读取期间零写入，也**不证明**每轮均留存独立证据（仓库只保留最新一对）"。判据名亦由"全程零写入/输入零改动"改为"**输入前后终态一致**"。
   295	2. **"五项绕过整类失效"→ 具体路径表述**：UAT round-7 行改为"「截断某个既有对象」这一**具体路径**不再存在，**不代表所有别名类绕过均已失效**（`lstat`→`replace` 竞态见 FU-B/FU-C）"。
   296	
   297	这两条的共同点与前十一轮一致：**证据支持的是"前后终态一致"与"某条具体路径消失"，我却写成了"零写入"与"整类失效"**。改的是措辞，不是结论——台账数字与脚本行为均未变动。
   298	
   299	round-12 整改后台账未重跑（本轮无脚本改动，`f4112c2c` 的 ledger 即最终版）：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0——十二轮整改数字全程未变**。

exec
/bin/zsh -lc "git -c core.quotePath=false ls-tree -r f4112c2c -- backend/scripts/census_dead_letter_episodes.py backend/tests/regression/test_census_dead_letter_readonly_contract.py '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' '_bmad-output/审查/G4-9-evidence/'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
100644 blob 9ac1beb158804c5deb9d0bc572ea51da730dc709	_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json
100644 blob 9be8b4230ea2744a6c6a94035d129633b8e3a068	_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt
100644 blob 52c0ea5e100efd64d683ab3a46dcbb67da31af7b	_bmad-output/审查/G4-9-evidence/census-stderr.txt
100644 blob d8425a5ae8d90f7c59e1159313083df834ddf63e	_bmad-output/审查/G4-9-evidence/container-sha-check.txt
100644 blob 8d3fd97564d9be79c306784f572bf5b8d69a7fe9	_bmad-output/审查/G4-9-evidence/grep-selfattest.txt
100644 blob a04c0c8fe75ddfbcc68ab0bee5bb57494af8b7cd	_bmad-output/审查/G4-9-evidence/readonly-contract-tests.txt
100644 blob 3de59858e06f21499f7a3b84bd355f3d7a290097	_bmad-output/审查/G4-9-evidence/shasums-after.txt
100644 blob 3de59858e06f21499f7a3b84bd355f3d7a290097	_bmad-output/审查/G4-9-evidence/shasums-before.txt
100644 blob 87266e092777fe45e93dde1dfba6eac197dae527	backend/scripts/census_dead_letter_episodes.py
100644 blob 541ec8b35e9d1fdadff3348d8a43a8d959e08c7c	backend/tests/regression/test_census_dead_letter_readonly_contract.py

exec
/bin/zsh -lc "git -c core.quotePath=false ls-tree -r 543e8a34 -- backend/scripts/census_dead_letter_episodes.py backend/tests/regression/test_census_dead_letter_readonly_contract.py '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' '_bmad-output/审查/G4-9-evidence/'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
exec
/bin/zsh -lc "git -c core.quotePath=false grep -n -I -E '(可绑定证据|binding|绑定证据|readonly-contract-tests|artifact-commit-receipt|87266e09|541ec8b3|f4112c2c)' 543e8a34 -- '_bmad-output/审查/codex-review-CARD-G4-9-round12.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
100644 blob 9ac1beb158804c5deb9d0bc572ea51da730dc709	_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json
100644 blob a71e2031a1768759c67cafecf4a2e7bd94ec2bfe	_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt
100644 blob 52c0ea5e100efd64d683ab3a46dcbb67da31af7b	_bmad-output/审查/G4-9-evidence/census-stderr.txt
100644 blob d8425a5ae8d90f7c59e1159313083df834ddf63e	_bmad-output/审查/G4-9-evidence/container-sha-check.txt
100644 blob 8d3fd97564d9be79c306784f572bf5b8d69a7fe9	_bmad-output/审查/G4-9-evidence/grep-selfattest.txt
100644 blob a04c0c8fe75ddfbcc68ab0bee5bb57494af8b7cd	_bmad-output/审查/G4-9-evidence/readonly-contract-tests.txt
100644 blob 3de59858e06f21499f7a3b84bd355f3d7a290097	_bmad-output/审查/G4-9-evidence/shasums-after.txt
100644 blob 3de59858e06f21499f7a3b84bd355f3d7a290097	_bmad-output/审查/G4-9-evidence/shasums-before.txt
100644 blob 87266e092777fe45e93dde1dfba6eac197dae527	backend/scripts/census_dead_letter_episodes.py
100644 blob 541ec8b35e9d1fdadff3348d8a43a8d959e08c7c	backend/tests/regression/test_census_dead_letter_readonly_contract.py

 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:14:CARD-G4-9 round-12 终确认（静态审阅 + 只读复算，禁改任何文件）。你 round-11 裁定「无需补必需①②③」，剩余阻断收敛为三条必须再做项。开发方以 commit f4112c2c 完成，请逐条确认并给出**最终裁定**：
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:22:3. **可绑定证据**：readonly-contract-tests.txt 已用新 blob 重生成（脚本 blob 87266e09…、测试 blob 541ec8b3…，含各自 sha256、覆盖构成、范围声明、逐项 PASSED 明细）。20 passed。请复核能否独立绑定到 f4112c2c。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:30:我会按三条阻断分别做独立复算，并把“证据文件自述”与“从 `f4112c2c` 对象重新计算所得”严格分开。全程只读、不编辑文件；我也会并行检查过强声明、测试虚假通过空间、证据绑定与 92 条 ledger 统计。先做一次与 round-11 相关的记忆索引核对，再读取当前 checkout 的实际对象。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:31:  → 核对历史裁定索引、仓库规则与 f4112c2c 对象边界
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:59:/bin/zsh -lc 'git diff-tree --no-commit-id --name-status -r f4112c2c' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:64:M	"_bmad-output/\345\256\241\346\237\245/G4-9-evidence/readonly-contract-tests.txt"
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:78:/bin/zsh -lc 'git show --no-ext-diff --format=fuller --stat --summary f4112c2c' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:81:commit f4112c2ca5e800eda5944d9ad0e6e6bfb0d60ce9
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:101:    3. 重跑并更新可绑定证据: 新 script blob 87266e09 / test blob 541ec8b3,
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:109: .../G4-9-evidence/readonly-contract-tests.txt"     |    16 +-
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:131:/bin/zsh -lc 'git show --no-ext-diff --format= --name-only f4112c2c' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:136:"_bmad-output/\345\256\241\346\237\245/G4-9-evidence/readonly-contract-tests.txt"
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:143:/bin/zsh -lc "git ls-tree -r --full-tree f4112c2c | rg 'G4-9|census_dead_letter|UAT-CARD'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:148:100644 blob 9be8b4230ea2744a6c6a94035d129633b8e3a068	"_bmad-output/\345\256\241\346\237\245/G4-9-evidence/artifact-commit-receipt.txt"
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:152:100644 blob a04c0c8fe75ddfbcc68ab0bee5bb57494af8b7cd	"_bmad-output/\345\256\241\346\237\245/G4-9-evidence/readonly-contract-tests.txt"
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:176:100644 blob 87266e092777fe45e93dde1dfba6eac197dae527	backend/scripts/census_dead_letter_episodes.py
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:177:100644 blob 541ec8b35e9d1fdadff3348d8a43a8d959e08c7c	backend/tests/regression/test_census_dead_letter_readonly_contract.py
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:179:**Inspecting commit f4112c2c contents**
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:331:f4112c2c fix(census): G4-9 round-11 解阻整改 — 残留声明清除 + 测试补强 [BATCH-2026-08-28-第五批 / CARD-G4-9]
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:344:/bin/zsh -lc 'git merge-base --is-ancestor f4112c2c HEAD' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:351:已确认一个需要在最终裁定中显式区分的边界：当前 `HEAD` 是后续 receipt commit `05c85324`，被审对象 `f4112c2c` 是其直接祖先。目标脚本与测试在 `f4112c2c` 中的 Git blob 确为 `87266e09…`、`541ec8b3…`；下一步会核对后续 commit 是否只补 receipt，以及证据内容能否反向唯一绑定。当前已有一个与任务无关/未授权的 untracked round-12 文档，我不会读取作为证据，也不会触碰。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:353:/bin/zsh -lc 'git -c core.quotePath=false diff --name-status f4112c2c HEAD' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:356:M	_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:372: _bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt | 3 ++-
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:376:/bin/zsh -lc 'git -c core.quotePath=false diff --no-ext-diff f4112c2c''^ f4112c2c -- backend/scripts/census_dead_letter_episodes.py backend/tests/regression/test_census_dead_letter_readonly_contract.py' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:380:index 2f3fd0a0..87266e09 100644
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:427:index 8131f1f3..541ec8b3 100644
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:478:/bin/zsh -lc 'git -c core.quotePath=false diff --no-ext-diff f4112c2c''^ f4112c2c -- _bmad-output/审查/G4-9-DLQ-census-2026-08-28.md _bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md _bmad-output/审查/G4-9-evidence/readonly-contract-tests.txt' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:491: > **代码基线**: 分析对象锚定 `37387a86`（第五批开工基线）。**本卡交付物 artifact commit 链**：精确 SHA 逐段记录于 `_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt`（commit 无法自含己身 SHA，故用后置 receipt 绑定——Codex round-4 LOW 整改）
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:515: **Codex 十轮裁定轨迹（如实留档）**：round-1 BLOCKED → round-2/3 部分闭合 → round-4/5/6 每轮揭示更深层缺陷（其中 round-6 与 round-7 两次触发架构级重做）→ round-7 起稳定为**分层裁定**「92 条冻结 ledger 可采信 / 生成器安全声明不可验收」→ round-10 明确「阻断不再要求补必需①②③，只需清除矛盾声明、修字段语义、如实标注测试覆盖、补可绑定证据」。本轮四条全部完成。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:526:+3. **重跑并更新可绑定证据**：`readonly-contract-tests.txt` 已用新 script/test blob 重生成（脚本 blob `87266e09…`、测试 blob `541ec8b3…`，含各自 sha256 与逐项 PASSED 明细）。**20 passed**。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:529:diff --git a/_bmad-output/审查/G4-9-evidence/readonly-contract-tests.txt b/_bmad-output/审查/G4-9-evidence/readonly-contract-tests.txt
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:531:--- a/_bmad-output/审查/G4-9-evidence/readonly-contract-tests.txt
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:532:+++ b/_bmad-output/审查/G4-9-evidence/readonly-contract-tests.txt
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:543:+被测脚本 blob: 87266e092777fe45e93dde1dfba6eac197dae527
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:545:+测试文件 blob: 541ec8b35e9d1fdadff3348d8a43a8d959e08c7c
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:566: | Codex 复审 round-9/10 | round-9 给出「最小剩余项」5 条；round-10 首次明确**「阻断不再要求补必需①②③」**，收敛为 4 条可执行要求：清除矛盾声明 / 修字段语义 / 如实标注测试覆盖 / 补可绑定证据。且十轮均确认 **92 条冻结 ledger 可验收** | `codex-review-CARD-G4-9-round9.md` / `-round10.md` |
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:569:+| round-11 解阻整改 | **3/3 完成**：DB 静止改为操作者前提（0 行·固定字节·同 SHA 均不能证明无并发写者）、"20 类路径 fail-closed"改为逐例证据声明、"整类绕过失效"改为具体路径消失+残余竞态登记；坏 JSON 直接断言原始列表恰 3 项、输入不变测试加非 JSONL sentinel 并覆盖根内全部常规文件；证据绑定新 blob（脚本 87266e09/测试 541ec8b3）。20 passed | 报告 §7m |
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:596:**Verifying evidence blob bindings to commits**
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:601:/bin/zsh -lc "git -c core.quotePath=false grep -n -I -E 'DB 静止|数据库静止|无并发写者|并发写者' f4112c2c -- 'backend/scripts/census_dead_letter_episodes.py' '_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md' '_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:603:/bin/zsh -lc "git -c core.quotePath=false grep -n -I -E '整类["'^'"\\n]*(绕过|失效|消失)|所有别名|全部失效|TOCTOU["'^'"\\n]*(消失|失效)' f4112c2c -- 'backend/scripts/census_dead_letter_episodes.py' '_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md' '_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:606:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:5:> **只读声明的准确边界（round-9 收敛，见 §7j）**: 本次运行对**本次列出的输入文件**（4 份 DLQ + qa_metrics.db）shasum 前后不变（证据包留有本次 before/after 一对，非九轮各存一对）；回归测试中**每条行为测试各自断言的那个具体场景** fail-closed（17 条跑真实 CLI + 3 条源码静态检查）——这是**逐例证据**，不构成"所有误用路径均 fail-closed"的整体证明。但**不声称**在共享可写目录、并发写者、活跃 SQLite DB 等敌意环境下具备生产级安全——剩余必需项见 §7j 清单。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:607:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:240:round-9 的必需①②③（一致性 SQLite 快照、单一稳定 dirfd 发布、tmp/发布者/状态绑定与单写者锁）是把这个**一次性 census 脚本**升级为**生产级并发安全工具**的要求。本卡不做，理由如实记录：本卡场景为单人本机、目录非共享可写；**"DB 静止"与"无并发写者"是操作者提供的前提，不是本卡证明的结论**（0 行 / 固定字节数 / 前后同 SHA 均不能证明读取期间无写者）。**处置方式是收敛声明而非假装达标**——报告头与验收单已删去"纯只读 / 唯一写出口 / 整类 TOCTOU 已消失"这类绝对化措辞，改为"本次运行输入 shasum 前后不变（已取证）+ 对 20+ 类误用路径 fail-closed（测试固化）+ 不声称敌意环境下的生产级安全"。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:608:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:262:6. **"DB 静止"改为操作者前提**：0 行 / 固定 sha / 前后同 SHA 本身不能证明读取期间无写者——已在脚本"安全边界"段与本报告显式声明为**前提而非结论**。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:609:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:272:1. **清除残留声明**（DB 静止当事实 / 逐次·运行零写入 / 整类绕过失效 / "20 个测试整体证明路径 fail-closed"）。已逐处改写：
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:610:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:273:   - 脚本 docstring 中"本卡场景为单人本机、DB 静止（实测 0 行、16384 bytes），故不影响结论"→ 改为"该假定**由操作者保证**（行数为 0、字节数固定、前后 SHA 相同都**不能证明**读取期间没有并发写者）"。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:611:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:53:| round-10 解阻整改 | **6/6 完成**：脚本+报告+UAT 的 `mode=ro` 与「唯一写出口/全程零写入」矛盾表述全清（残留均为「已废弃」引述）；`source_fd_opened_readonly` 移到 fd 打开处（**顺带修出真 bug**：deserialize 延迟验证使 malformed DB 炸掉整次 census）；测试覆盖如实标注 17 行为+3 静态并修掉 4 处虚假通过窗口；证据补 HEAD/blob/sha256/逐项明细；「九次取证」与「DB 静止」改为准确表述与操作者前提 | 报告 §7k/§7l |
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:612:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:55:| round-11 解阻整改 | **3/3 完成**：DB 静止改为操作者前提（0 行·固定字节·同 SHA 均不能证明无并发写者）、"20 类路径 fail-closed"改为逐例证据声明、"整类绕过失效"改为具体路径消失+残余竞态登记；坏 JSON 直接断言原始列表恰 3 项、输入不变测试加非 JSONL sentinel 并覆盖根内全部常规文件；证据绑定新 blob（脚本 87266e09/测试 541ec8b3）。20 passed | 报告 §7m |
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:613:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:169:- **前提（非结论）**："DB 静止"由操作者保证——0 行、固定 sha、前后同 SHA 本身**不能证明**读取期间没有并发写者。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:614:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:170:- **不再声称的**：在共享可写目录、有并发写者、SQLite DB 正被写入等**敌意环境**下具备生产级安全；也不声称"整类别名绕过已消失"（`lstat`→`replace` 竞态等残余见 FU-B/FU-C）。这类保证需要一致性快照、dirfd 相对发布、单写者锁——是把一次性 census 脚本升级为常驻工具的工作量，不在本卡范围。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:615:f4112c2c:backend/scripts/census_dead_letter_episodes.py:51:  - **不声称**: 在共享可写目录、存在并发写者、SQLite DB 正被写入等敌意环境下
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:616:f4112c2c:backend/scripts/census_dead_letter_episodes.py:54:  - **前提**: "DB 静止"由操作者保证 —— 0 行 / 固定 sha / 前后同 SHA 本身
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:617:f4112c2c:backend/scripts/census_dead_letter_episodes.py:55:    **不能证明**读取期间没有并发写者。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:618:f4112c2c:backend/scripts/census_dead_letter_episodes.py:331:    journal 旁文件，读到的字节可能是撕裂状态。本卡运行时假定 DB 静止，该假定
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:619:f4112c2c:backend/scripts/census_dead_letter_episodes.py:333:    期间没有并发写者）。若 G4-10 复用本脚本于活跃 DB，须改用 SQLite backup
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:623:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:205:- **NOT-CLOSED ×4（根外 hardlink 指向隐藏目录内 transcript / 根 retarget TOCTOU / 检查后换父目录 symlink 或 basename hardlink）+ MEDIUM（非原子写）**：这五项依附于同一个动作——**截断一个已存在的文件**。**架构级修复**：写出改为「同目录 `O_EXCL` 新建临时文件 → 写 → `fsync` → `os.replace` 原子替换」，**全文再无任何 `ftruncate` 调用**。`O_EXCL` 保证写入目标是本进程新建的对象，因此"截断既有对象"这条具体路径消失（三场景各自取证，不声称整类绕过均已失效）；`os.replace` 同时消除崩溃/ENOSPC 留下部分台账的风险。实测：根外 hardlink 指向根内 transcript 作 `--out` → 台账正常写出而**源文件内容完好**（`os.replace` 只重绑定该名字，不触碰底层 inode）。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:624:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:216:> **可验收：92 条冻结 ledger snapshot。不可验收：当前生成器的一般安全性，以及 UAT 的"纯只读、唯一写出口、整类 TOCTOU 已消失"声明。**
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:625:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:240:round-9 的必需①②③（一致性 SQLite 快照、单一稳定 dirfd 发布、tmp/发布者/状态绑定与单写者锁）是把这个**一次性 census 脚本**升级为**生产级并发安全工具**的要求。本卡不做，理由如实记录：本卡场景为单人本机、目录非共享可写；**"DB 静止"与"无并发写者"是操作者提供的前提，不是本卡证明的结论**（0 行 / 固定字节数 / 前后同 SHA 均不能证明读取期间无写者）。**处置方式是收敛声明而非假装达标**——报告头与验收单已删去"纯只读 / 唯一写出口 / 整类 TOCTOU 已消失"这类绝对化措辞，改为"本次运行输入 shasum 前后不变（已取证）+ 对 20+ 类误用路径 fail-closed（测试固化）+ 不声称敌意环境下的生产级安全"。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:626:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:272:1. **清除残留声明**（DB 静止当事实 / 逐次·运行零写入 / 整类绕过失效 / "20 个测试整体证明路径 fail-closed"）。已逐处改写：
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:627:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:275:   - "整类绕过全部失效"→ 改为"'截断某个既有对象'这条**具体路径**不再存在（已就 hardlink / 根内 symlink / FIFO 三场景各自取证）；⚠️ 不等于声称所有别名类绕过已失效——`lstat`→`replace` 竞态等残余见 FU-B/FU-C"。UAT 同处过强表述一并修正。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:628:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:49:| round-7 findings 整改 | **架构级第二次修复**：写出改 O_EXCL 临时文件+fsync+os.replace（**全文再无 ftruncate 调用**），五项绕过整类失效；containment 改 inode 逐级比较（normcase 在 POSIX 是恒等函数，我的假设错了）；扫描受阻直接拒绝写出。实测：根外 hardlink 指向根内 transcript 作 --out → 源内容完好 | 报告 §7h |
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:629:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:55:| round-11 解阻整改 | **3/3 完成**：DB 静止改为操作者前提（0 行·固定字节·同 SHA 均不能证明无并发写者）、"20 类路径 fail-closed"改为逐例证据声明、"整类绕过失效"改为具体路径消失+残余竞态登记；坏 JSON 直接断言原始列表恰 3 项、输入不变测试加非 JSONL sentinel 并覆盖根内全部常规文件；证据绑定新 blob（脚本 87266e09/测试 541ec8b3）。20 passed | 报告 §7m |
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:630:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:137:- **五项绕过共用一个根源**：它们都依附于"截断一个已存在的文件"这个动作。改成「新建临时文件 → 写 → fsync → 原子替换」后，脚本**全文再没有任何截断调用**——"截断某个既有对象"这条**具体路径**不复存在，"崩溃留下半个台账"的风险也一并消除。实测：拿一个指向恢复源的 hardlink 当 `--out`，台账正常写出，而**源文件内容一个字节没变**。⚠️ 这**不等于**"所有别名类绕过都已失效"：`lstat`→`replace` 之间仍有竞态窗口，已登记 FU-B/FU-C。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:631:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:144:round-8 把结论说得更清楚了：**「可验收：92 条冻结 ledger snapshot。不可验收：生成器的一般安全性，以及验收单里那句"纯只读、唯一写出口、整类 TOCTOU 已消失"」**。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:632:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:164:九轮对抗审查后，Codex 始终维持一个分层裁定：**「92 条冻结台账可以采信；但生成器的一般安全性、以及验收单里"纯只读、唯一写出口、整类 TOCTOU 已消失"这类绝对化声明不可验收」**。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:633:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:170:- **不再声称的**：在共享可写目录、有并发写者、SQLite DB 正被写入等**敌意环境**下具备生产级安全；也不声称"整类别名绕过已消失"（`lstat`→`replace` 竞态等残余见 FU-B/FU-C）。这类保证需要一致性快照、dirfd 相对发布、单写者锁——是把一次性 census 脚本升级为常驻工具的工作量，不在本卡范围。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:634:f4112c2c:backend/scripts/census_dead_letter_episodes.py:841:        # 声称"所有别名类绕过都已失效"—— lstat→replace 竞态等残余见模块
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:637:/bin/zsh -lc "git -c core.quotePath=false grep -n -I -E '运行零写入|全程零写入|逐次["'^'"\\n]*零写入|零写入|0 写入|0写入' f4112c2c -- 'backend/scripts/census_dead_letter_episodes.py' '_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md' '_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:640:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:92:| 运行前后 shasum（live/主仓/孤儿①/孤儿② 四份 DLQ + qa_metrics.db） | `diff shasums-before.txt shasums-after.txt` 空 → **PASS，0 写入** |
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:641:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:272:1. **清除残留声明**（DB 静止当事实 / 逐次·运行零写入 / 整类绕过失效 / "20 个测试整体证明路径 fail-closed"）。已逐处改写：
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:642:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:13:> 这张卡**没有修任何东西，也没有恢复任何数据**——它是一次"清点尸体"的只读普查（脚本对输入零写入已逐次取证；安全边界见文末"诚实边界"段）：
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:643:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:53:| round-10 解阻整改 | **6/6 完成**：脚本+报告+UAT 的 `mode=ro` 与「唯一写出口/全程零写入」矛盾表述全清（残留均为「已废弃」引述）；`source_fd_opened_readonly` 移到 fd 打开处（**顺带修出真 bug**：deserialize 延迟验证使 malformed DB 炸掉整次 census）；测试覆盖如实标注 17 行为+3 静态并修掉 4 处虚假通过窗口；证据补 HEAD/blob/sha256/逐项明细；「九次取证」与「DB 静止」改为准确表述与操作者前提 | 报告 §7k/§7l |
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:644:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:134:也就是说：这张卡要交付的 census 结论（92 条的分类、对账、三态、挂载真相、稳定键、运行零写入）**已经过关**；卡住的是"这个脚本作为工具，其只读承诺是否经得起敌意输入"。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:647:/bin/zsh -lc "git -c core.quotePath=false grep -n -I -E '20\\+?["'^'"\\n]*(误用|攻击|路径)|20 条["'^'"\\n]*(误用|攻击|路径)|fail-closed|所有误用路径' f4112c2c -- 'backend/scripts/census_dead_letter_episodes.py' '_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md' '_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:650:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:5:> **只读声明的准确边界（round-9 收敛，见 §7j）**: 本次运行对**本次列出的输入文件**（4 份 DLQ + qa_metrics.db）shasum 前后不变（证据包留有本次 before/after 一对，非九轮各存一对）；回归测试中**每条行为测试各自断言的那个具体场景** fail-closed（17 条跑真实 CLI + 3 条源码静态检查）——这是**逐例证据**，不构成"所有误用路径均 fail-closed"的整体证明。但**不声称**在共享可写目录、并发写者、活跃 SQLite DB 等敌意环境下具备生产级安全——剩余必需项见 §7j 清单。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:651:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:71:| **可字节级**（byte_exact） | **4** | inline 正文全量：sha256 重算对账通过**且**长度精确匹配（fail-closed 双门）——重放可逐字节还原 episode |
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:652:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:104:- **HIGH-1（inline 判定不 fail-closed）**：full_verified 加长度精确匹配门；truncated_prefix 加 64-hex 合法性门；anomaly 一律 unrecoverable + 如实 basis（不再谎称截断、不再滑入 approximate）。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:653:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:145:- **HIGH-3 残留**：`glob(recursive=True)` 在 realpath 过滤**之前**已递归遍历（Python 3.14 glob 跟随目录 symlink 且**静默吞掉不可读子树错误**）→ 越根枚举 + "假唯一/假不可恢复"；mode `000` 的 regular transcript 仍过 `isfile()` 被判 approximate。**整改**：改 `os.walk(onerror=..., followlinks=False)`（不跟随目录 symlink、遍历错误显式捕获）+ 候选加 `os.access(R_OK)` 门；遍历受阻或存在不可读候选一律记 `attribution_conflict` 拒绝裁定（既不宣称找到、也不宣称不可恢复）。三条反例实测全部 fail-closed。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:654:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:240:round-9 的必需①②③（一致性 SQLite 快照、单一稳定 dirfd 发布、tmp/发布者/状态绑定与单写者锁）是把这个**一次性 census 脚本**升级为**生产级并发安全工具**的要求。本卡不做，理由如实记录：本卡场景为单人本机、目录非共享可写；**"DB 静止"与"无并发写者"是操作者提供的前提，不是本卡证明的结论**（0 行 / 固定字节数 / 前后同 SHA 均不能证明读取期间无写者）。**处置方式是收敛声明而非假装达标**——报告头与验收单已删去"纯只读 / 唯一写出口 / 整类 TOCTOU 已消失"这类绝对化措辞，改为"本次运行输入 shasum 前后不变（已取证）+ 对 20+ 类误用路径 fail-closed（测试固化）+ 不声称敌意环境下的生产级安全"。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:655:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:259:3. **如实标注测试覆盖**：原称"19 条反例全部固化 / 20+ 类路径"不实。现于测试文件 docstring 与本报告标注真实构成（**17 条行为测试跑真实 CLI + 3 条源码静态检查（弱证据）**，无 mock 无 skip），并修掉 round-10 点名的 4 处**虚假通过窗口**：FIFO 补验"仍是 FIFO 且无 tmp 残留"；扫描受阻补验 stdout 确无台账；坏 JSON 由 `A or B` 弱断言改为逐行精确断言（3 类坏行各一条）；输入不变测试从"DLQ + 单 transcript"扩展到 `--compare`、`--qa-metrics-db` 与根内全部文件。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:656:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:272:1. **清除残留声明**（DB 静止当事实 / 逐次·运行零写入 / 整类绕过失效 / "20 个测试整体证明路径 fail-closed"）。已逐处改写：
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:657:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:274:   - "对 20+ 类误用/攻击路径 fail-closed（回归测试固化）"→ 改为"**每条行为测试各自断言的那一个具体场景** fail-closed —— 这是逐例证据，**不构成**'所有误用路径均 fail-closed'的整体证明"。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:658:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:41:| round-3 findings 逐条整改 | **6/6 完成**：transcript 并入保护集 / O_NOFOLLOW+fstat 消 TOCTOU / os.walk 替 glob（不跟随目录 symlink+遍历错误显式捕获）/ 不可读候选 fail-closed / JSONL 严格 LF 分帧 / 非 dict 归 unparseable。6 条新反例实测全过、数字第三次不变 | 报告 §7d + `grep-selfattest.txt` |
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:659:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:55:| round-11 解阻整改 | **3/3 完成**：DB 静止改为操作者前提（0 行·固定字节·同 SHA 均不能证明无并发写者）、"20 类路径 fail-closed"改为逐例证据声明、"整类绕过失效"改为具体路径消失+残余竞态登记；坏 JSON 直接断言原始列表恰 3 项、输入不变测试加非 JSONL sentinel 并覆盖根内全部常规文件；证据绑定新 blob（脚本 87266e09/测试 541ec8b3）。20 passed | 报告 §7m |
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:660:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:63:- **HIGH-1 inline 判定 fail-open**：sha 匹配但长度不符会误判 full_verified（反例实测）。整改：长度精确匹配门 + 64-hex 合法性门 + anomaly 一律 fail-closed（unrecoverable + 如实 basis）。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:661:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:87:- **HIGH-3 仍 PARTIAL**：Python 3.14 的 `glob` 在过滤前就已递归、跟随目录 symlink 且**静默吞掉不可读子树错误**；mode 000 的文件仍过 `isfile()` 被当可用源。→ 改 `os.walk(onerror=, followlinks=False)` + `os.access(R_OK)` 门；遍历受阻或有不可读候选一律拒绝裁定。三反例实测 fail-closed。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:662:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:168:- **可以确证的**：本次运行对**本次列出的输入文件**（4 份 DLQ + qa_metrics.db）**shasum 前后逐字节不变**（证据包留存本次一对 before/after）；回归测试中**每条行为测试各自断言的那个场景** fail-closed（17 行为 + 3 静态）——**逐例证据，非"所有路径都安全"的整体证明**。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:663:f4112c2c:backend/scripts/census_dead_letter_episodes.py:23:判定 fail-closed（Codex round-1 HIGH-1/2/3 整改）:
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:664:f4112c2c:backend/scripts/census_dead_letter_episodes.py:49:    那一个具体场景** fail-closed —— 这是逐例证据，**不构成**"所有误用路径均
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:665:f4112c2c:backend/scripts/census_dead_letter_episodes.py:50:    fail-closed"的整体证明。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:666:f4112c2c:backend/scripts/census_dead_letter_episodes.py:165:    """返回 (inline_state, sha_check)，fail-closed（见模块 docstring）。"""
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:667:f4112c2c:backend/scripts/census_dead_letter_episodes.py:222:    """组级归因，fail-closed。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:668:f4112c2c:backend/scripts/census_dead_letter_episodes.py:407:        # except，会炸掉整次 census。查询段一律 fail-closed 记录不中断。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:669:f4112c2c:backend/scripts/census_dead_letter_episodes.py:492:            f"transcripts 根目录不存在/不可见: {transcripts_dir} —— 拒绝在源不可见时裁定可恢复性（fail-closed）",
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:670:f4112c2c:backend/scripts/census_dead_letter_episodes.py:497:    # 并把全部记录假判 unrecoverable —— 同样 fail-closed 拒诊。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:671:f4112c2c:backend/scripts/census_dead_letter_episodes.py:500:            f"transcripts 根目录不可读/不可遍历: {transcripts_dir} —— 拒绝在源不可见时裁定可恢复性（fail-closed）",
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:672:f4112c2c:backend/scripts/census_dead_letter_episodes.py:543:                # round-4 整改: stat 失败不再静默吞 —— 无法确认身份即 fail-closed
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:673:f4112c2c:backend/scripts/census_dead_letter_episodes.py:656:            basis = f"源可见性不足，拒绝裁定：{why}{extra}。既不宣称可恢复，也不宣称不可恢复（fail-closed）"
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:676:/bin/zsh -lc "git -c core.quotePath=false grep -n -I -E '只读|shasum|SHA["'^'"\\n]*(不变|相同)|逐字节不变|一个字节没变' f4112c2c -- 'backend/scripts/census_dead_letter_episodes.py' '_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md' '_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:679:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:4:> **性质**: 只读 census。0 重放、0 业务代码改动。代码产物 = `backend/scripts/census_dead_letter_episodes.py` + 其只读契约回归测试。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:680:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:5:> **只读声明的准确边界（round-9 收敛，见 §7j）**: 本次运行对**本次列出的输入文件**（4 份 DLQ + qa_metrics.db）shasum 前后不变（证据包留有本次 before/after 一对，非九轮各存一对）；回归测试中**每条行为测试各自断言的那个具体场景** fail-closed（17 条跑真实 CLI + 3 条源码静态检查）——这是**逐例证据**，不构成"所有误用路径均 fail-closed"的整体证明。但**不声称**在共享可写目录、并发写者、活跃 SQLite DB 等敌意环境下具备生产级安全——剩余必需项见 §7j 清单。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:681:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:8:> **证据包**: `_bmad-output/审查/G4-9-evidence/`（shasums before/after、grep 自证、容器内 sha 实测）
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:682:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:58:## §4 源指针核销（qa_metrics.db，源 fd 只读 + 内存副本）
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:683:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:62:  - `llm_call_logs.db`（同目录）：本卡仅做**一次性人工只读查看 schema**（未纳入脚本探测路径），确认仅 token/延迟/成本指标列，**无 prompt/response 正文**；
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:684:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:92:| 运行前后 shasum（live/主仓/孤儿①/孤儿② 四份 DLQ + qa_metrics.db） | `diff shasums-before.txt shasums-after.txt` 空 → **PASS，0 写入** |
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:685:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:123:round-2 整改后再次全量重跑：92 条、class 89/2/1、三态 4/88/0、重复簇 6/29、shasum 不变——**数字仍逐项一致**，整改只收紧通用鲁棒性。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:686:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:150:round-3 整改后第三次全量重跑：92 条、class 89/2/1、三态 4/88/0、重复簇 6/29、shasum 不变——**三轮整改数字全程未变**，改的全是通用鲁棒性与路径安全。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:687:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:164:round-4 整改后第四次全量重跑：**92 条、class 89/2/1、三态 4/88/0（unverifiable 0）、重复簇 6/29、shasum 不变——四轮整改数字全程未变**。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:688:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:173:- **HIGH②（`fchmod` 先于 protected-id 检查）**：`--out` 指向受保护的 0644 输入时，会**先把只读输入权限改成 0600** 再拒绝——字节没截断但输入已被修改。**整改**：碰撞检查前移到 `fchmod` 之前。实测：mode 644 → 644 不变。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:689:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:180:round-5 整改后第五次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变——五轮整改数字全程未变**。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:690:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:194:round-6 整改后第六次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变——六轮整改数字全程未变**。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:691:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:200:> **「现有 92 条冻结 ledger 可以采信；CARD-G4-9 生成器与 UAT 的纯只读安全声明不可验收。」**
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:692:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:202:即：卡面的 census 判据（分类/对账/三态/挂载真相/稳定键/shasum 不变）已满足且被独立复算确认；阻断项全部落在"生成器作为工具的只读安全承诺"上。逐条整改：
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:693:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:210:round-7 整改后第七次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变、台账 mode 0600、无临时文件残留——七轮整改数字全程未变**。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:694:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:216:> **可验收：92 条冻结 ledger snapshot。不可验收：当前生成器的一般安全性，以及 UAT 的"纯只读、唯一写出口、整类 TOCTOU 已消失"声明。**
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:695:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:222:- **①②的共同解法**：不再让 SQLite 碰路径——从**已验证的 fd** 读全量字节 → `sqlite3` 内存库 `deserialize()`。URI 转义问题与 ABA **一并消失**，且全程不落任何文件。实测：路径含 `#` 与 `?` 的 DB 正常只读（`read_mode: in_memory_deserialize_from_verified_fd`，16384 bytes）。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:696:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:227:round-8 整改后第八次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变、无 tmp 残留——八轮整改数字全程未变**。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:697:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:235:- **必需⑤ 名实不符（DD-13 硬伤）**：改用内存 `deserialize` 后，字段仍叫 `opened_readonly`、docstring 仍称 SQLite URI `mode=ro`——**实际只有源 fd 只读，内存连接可写**。已改字段名为 `source_fd_opened_readonly`，docstring 如实说明只读保证的来源（源 fd 只读 + 内存副本与源解耦），补 `PRAGMA query_only=ON` 作纵深防御，并把 QA DB 的 `source_sha256` 写入台账（与证据包 shasum 一致）。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:698:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:240:round-9 的必需①②③（一致性 SQLite 快照、单一稳定 dirfd 发布、tmp/发布者/状态绑定与单写者锁）是把这个**一次性 census 脚本**升级为**生产级并发安全工具**的要求。本卡不做，理由如实记录：本卡场景为单人本机、目录非共享可写；**"DB 静止"与"无并发写者"是操作者提供的前提，不是本卡证明的结论**（0 行 / 固定字节数 / 前后同 SHA 均不能证明读取期间无写者）。**处置方式是收敛声明而非假装达标**——报告头与验收单已删去"纯只读 / 唯一写出口 / 整类 TOCTOU 已消失"这类绝对化措辞，改为"本次运行输入 shasum 前后不变（已取证）+ 对 20+ 类误用路径 fail-closed（测试固化）+ 不声称敌意环境下的生产级安全"。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:699:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:251:round-9 整改后第九次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变、只读契约测试 19 passed——九轮整改数字全程未变**。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:700:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:258:2. **修正字段语义**：`source_fd_opened_readonly` 原在 `deserialize` 成功后才置真——DB malformed 时 fd 确已只读打开却返回 false。已移到 fd 打开成功处。**该修正顺带暴露一个真 bug**：`deserialize` 是**延迟验证**，malformed DB 的 `DatabaseError` 在首次 `execute` 时才抛出，而查询段原本只有 `finally` 没有 `except`——**会炸掉整次 census**。已补 `sqlite3.Error` 捕获并记 `query_failed`，新增回归用例锁定。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:701:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:261:5. **"九次取证"表述收敛**：仓库只保留最新一对 before/after shasum，已改述为"本次留存一对，此前各轮亦逐次核对但未各存一份"。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:702:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:264:round-10 整改后第十次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变、只读契约测试 20 passed（17 行为 + 3 静态）——十轮整改数字全程未变**。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:703:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:273:   - 脚本 docstring 中"本卡场景为单人本机、DB 静止（实测 0 行、16384 bytes），故不影响结论"→ 改为"该假定**由操作者保证**（行数为 0、字节数固定、前后 SHA 相同都**不能证明**读取期间没有并发写者）"。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:704:f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:279:round-11 整改后第十一次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变——十一轮整改数字全程未变**。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:705:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:6:scope: "BATCH-2026-08-28-第五批 / CARD-G4-9 — live DLQ 92 条只读 census：分类/SHA 对账/可恢复性三态/挂载真相，产出 G4-10 交接台账"
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:706:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:13:> 这张卡**没有修任何东西，也没有恢复任何数据**——它是一次"清点尸体"的只读普查（脚本对输入零写入已逐次取证；安全边界见文末"诚实边界"段）：
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:707:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:27:| 输入零改动（裁判判据 e） | 运行前后**本次列出的输入**（四份 DLQ + qa_metrics.db）sha256 **逐字节不变**（diff 为空 → PASS）。注：证据包留存本次一对 before/after，非每轮各存一份 | `_bmad-output/审查/G4-9-evidence/shasums-before.txt` / `shasums-after.txt` |
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:708:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:28:| 脚本只读自证（判据 a） | import 行全 stdlib；neo4j/graphiti/bolt/app. import **0 命中**；`--apply` 定义 **0 命中**；**全文无任何截断调用**（写出走 O_EXCL 临时文件 + 原子替换） | `G4-9-evidence/grep-selfattest.txt` |
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:709:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:29:| 只读契约回归测试（round-9 必需项④ + round-10 补强） | **20 passed**：**17 条行为测试**（subprocess 跑真实 CLI + 断言文件系统事实）+ **3 条源码静态检查**（弱证据，如实标注，不替代行为测试）。测试两次抓出真实问题：① 架构改动丢了文件类型门（FIFO 会被静默替换）；② `deserialize` 延迟验证使 malformed DB 炸掉整次 census。round-10 另修掉 4 处虚假通过窗口 | `backend/tests/regression/test_census_dead_letter_readonly_contract.py` |
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:710:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:33:| 源指针核销（判据 b，qa_metrics.db 源 fd 只读 + 内存副本） | `qa_error_logs` **0 行** → 0/92 可经 qa_metrics.db 溯源（诚实记录）；附加核销：llm_call_logs.db 无正文、outbox 空、episode_body_full 0 条；**有效源指针 = request_id 组内 session 归因 → 7 个 transcript 全部在盘实测存在** | 报告 §4 + 台账 `qa_metrics_probe` |
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:711:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:48:| Codex 复审 round-7 | **关键裁定分离**："92 条冻结 ledger **可以采信**；生成器与 UAT 的纯只读安全声明不可验收"——卡面 census 判据已满足，阻断全在工具安全承诺侧。1 BLOCKER（大小写别名根，无需竞态）+ 4 项路径 TOCTOU + 1 MEDIUM（非原子写）+ 2 LOW | `_bmad-output/审查/codex-review-CARD-G4-9-round7.md` |
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:712:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:50:| Codex 复审 round-8 | 重申裁定分离：**「可验收：92 条冻结 ledger snapshot；不可验收：生成器一般安全性与 UAT 的纯只读声明」**。3 新 BLOCKER（SQLite URI 未转义 #/? / QA DB 仍按 pathname 开可 ABA / 根内末级 symlink 因 rename 不解析而被替换）+ 1 HIGH + 1 MEDIUM | `_bmad-output/审查/codex-review-CARD-G4-9-round8.md` |
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:713:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:55:| round-11 解阻整改 | **3/3 完成**：DB 静止改为操作者前提（0 行·固定字节·同 SHA 均不能证明无并发写者）、"20 类路径 fail-closed"改为逐例证据声明、"整类绕过失效"改为具体路径消失+残余竞态登记；坏 JSON 直接断言原始列表恰 3 项、输入不变测试加非 JSONL sentinel 并覆盖根内全部常规文件；证据绑定新 blob（脚本 87266e09/测试 541ec8b3）。20 passed | 报告 §7m |
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:714:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:56:| 独立 Workflow 4-agent 复核 | G4-9 数字 agent：92 条重算 **0 mismatch**（class/inline/三态/25 request_id/7 transcript 在盘/台账 sha 全 CONFIRMED，仅 2 处描述区间 REFUTED 已修正）；只读契约 agent：与 Codex 同源的 3 条 blocker（已随上整改） | Workflow wf_737b1a95-20b journal |
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:715:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:80:round-2 整改后再次全量重跑：92 条、4/88/0、89/2/1、6 簇 29 行、shasum 不变——**数字全程未变**。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:716:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:91:round-3 整改后第三次全量重跑：**92 条、4/88/0、89/2/1、6/29、shasum 不变——三轮整改数字全程未变**，改的全是通用鲁棒性与路径安全。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:717:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:102:round-4 整改后第四次全量重跑：**92 条、4/88/0（unverifiable 0）、89/2/1、6/29、shasum 不变——四轮整改数字全程未变**。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:718:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:111:- **`fchmod` 排在碰撞检查之前**：`--out` 指向受保护的只读输入时，会先把它的权限从 644 改成 600 才发现碰撞——字节没丢但输入被改了。→ 碰撞检查前移。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:719:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:116:round-5 整改后第五次全量重跑：**92 条、4/88/0/0、89/2/1、6/29、shasum 不变——五轮整改数字全程未变**。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:720:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:126:round-6 整改后第六次全量重跑：**92 条、4/88/0/0、89/2/1、6/29、shasum 不变——六轮整改数字全程未变**。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:721:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:132:> **「现有 92 条冻结 ledger 可以采信；生成器与 UAT 的纯只读安全声明不可验收。」**
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:722:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:134:也就是说：这张卡要交付的 census 结论（92 条的分类、对账、三态、挂载真相、稳定键、运行零写入）**已经过关**；卡住的是"这个脚本作为工具，其只读承诺是否经得起敌意输入"。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:723:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:137:- **五项绕过共用一个根源**：它们都依附于"截断一个已存在的文件"这个动作。改成「新建临时文件 → 写 → fsync → 原子替换」后，脚本**全文再没有任何截断调用**——"截断某个既有对象"这条**具体路径**不复存在，"崩溃留下半个台账"的风险也一并消除。实测：拿一个指向恢复源的 hardlink 当 `--out`，台账正常写出，而**源文件内容一个字节没变**。⚠️ 这**不等于**"所有别名类绕过都已失效"：`lstat`→`replace` 之间仍有竞态窗口，已登记 FU-B/FU-C。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:724:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:140:round-7 整改后第七次全量重跑：**92 条、4/88/0/0、89/2/1、6/29、shasum 不变、台账 0600、无临时文件残留——七轮整改数字全程未变**。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:725:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:144:round-8 把结论说得更清楚了：**「可验收：92 条冻结 ledger snapshot。不可验收：生成器的一般安全性，以及验收单里那句"纯只读、唯一写出口、整类 TOCTOU 已消失"」**。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:726:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:152:round-8 整改后第八次全量重跑：**92 条、4/88/0/0、89/2/1、6/29、shasum 不变、无 tmp 残留——八轮整改数字全程未变**。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:727:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:156:- `backend/scripts/census_dead_letter_episodes.py` — 唯一代码产物（只读 census 脚本，纯 stdlib）
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:728:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:159:- `_bmad-output/审查/G4-9-evidence/` — 证据包（shasums ×2、grep 自证、容器 sha 实测、运行日志）
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:729:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:164:九轮对抗审查后，Codex 始终维持一个分层裁定：**「92 条冻结台账可以采信；但生成器的一般安全性、以及验收单里"纯只读、唯一写出口、整类 TOCTOU 已消失"这类绝对化声明不可验收」**。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:730:f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:168:- **可以确证的**：本次运行对**本次列出的输入文件**（4 份 DLQ + qa_metrics.db）**shasum 前后逐字节不变**（证据包留存本次一对 before/after）；回归测试中**每条行为测试各自断言的那个场景** fail-closed（17 行为 + 3 静态）——**逐例证据，非"所有路径都安全"的整体证明**。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:731:f4112c2c:backend/scripts/census_dead_letter_episodes.py:2:"""CARD-G4-9: dead-letter episodes 只读 census 分诊脚本。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:732:f4112c2c:backend/scripts/census_dead_letter_episodes.py:6:只读契约（grep 可自证 + 运行时守卫）:
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:733:f4112c2c:backend/scripts/census_dead_letter_episodes.py:20:  - DLQ 文件只读一次（bytes），头部 sha256/line_count 与逐条 records 全部
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:734:f4112c2c:backend/scripts/census_dead_letter_episodes.py:47:    运行前后 shasum 逐字节不变（证据包留存本次一对 before/after）；
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:735:f4112c2c:backend/scripts/census_dead_letter_episodes.py:321:    """只读核销 qa_metrics.db。返回 (结果, 实际读取对象身份)。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:736:f4112c2c:backend/scripts/census_dead_letter_episodes.py:323:    ⚠️ **只读语义的准确表述（round-9 必需项⑤，名实一致 DD-13）**：只读保证来自
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:737:f4112c2c:backend/scripts/census_dead_letter_episodes.py:332:    **由操作者保证**（行数为 0、字节数固定、前后 SHA 相同都**不能证明**读取
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:738:f4112c2c:backend/scripts/census_dead_letter_episodes.py:357:        # round-10 整改: 字段语义即"源 fd 是否以只读方式成功打开"——
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:739:f4112c2c:backend/scripts/census_dead_letter_episodes.py:359:        # fd 确实已只读打开，返回 false 属名实不符）。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:740:f4112c2c:backend/scripts/census_dead_letter_episodes.py:387:        # 以匹配"只读核销"的语义 —— 但真正的只读保证来自**源 fd 只读 + 内存
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:746:/bin/zsh -lc "git -c core.quotePath=false show 'f4112c2c:_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md' | nl -ba | sed -n '1,60p;126,176p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:800:    52	| Codex 复审 round-9/10 | round-9 给出「最小剩余项」5 条；round-10 首次明确**「阻断不再要求补必需①②③」**，收敛为 4 条可执行要求：清除矛盾声明 / 修字段语义 / 如实标注测试覆盖 / 补可绑定证据。且十轮均确认 **92 条冻结 ledger 可验收** | `codex-review-CARD-G4-9-round9.md` / `-round10.md` |
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:803:    55	| round-11 解阻整改 | **3/3 完成**：DB 静止改为操作者前提（0 行·固定字节·同 SHA 均不能证明无并发写者）、"20 类路径 fail-closed"改为逐例证据声明、"整类绕过失效"改为具体路径消失+残余竞态登记；坏 JSON 直接断言原始列表恰 3 项、输入不变测试加非 JSONL sentinel 并覆盖根内全部常规文件；证据绑定新 blob（脚本 87266e09/测试 541ec8b3）。20 passed | 报告 §7m |
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:862:/bin/zsh -lc "git -c core.quotePath=false show f4112c2c:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md | nl -ba | sed -n '80,100p;198,246p;252,282p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:943:   260	4. **补可绑定运行证据**：`readonly-contract-tests.txt` 由一行 `19 passed` 改为含精确命令、Python 版本、工作树 HEAD、**被测脚本与测试文件的 git blob**、脚本 sha256、覆盖构成声明与**逐项 PASSED 明细**。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:949:   266	**Codex 十轮裁定轨迹（如实留档）**：round-1 BLOCKED → round-2/3 部分闭合 → round-4/5/6 每轮揭示更深层缺陷（其中 round-6 与 round-7 两次触发架构级重做）→ round-7 起稳定为**分层裁定**「92 条冻结 ledger 可采信 / 生成器安全声明不可验收」→ round-10 明确「阻断不再要求补必需①②③，只需清除矛盾声明、修字段语义、如实标注测试覆盖、补可绑定证据」。本轮四条全部完成。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:960:   277	3. **重跑并更新可绑定证据**：`readonly-contract-tests.txt` 已用新 script/test blob 重生成（脚本 blob `87266e09…`、测试 blob `541ec8b3…`，含各自 sha256 与逐项 PASSED 明细）。**20 passed**。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:965:/bin/zsh -lc 'git -c core.quotePath=false show f4112c2c:_bmad-output/审查/codex-review-CARD-G4-9-round11.md | tail -n 260' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:1120:**Verifying claim evidence and ledger binding**
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:1165:证据文件记录的 parent HEAD `a775f80…` 正是 `dfbe70c7` 的父提交；其中 script blob `2f3fd0a…`、test blob `8131f1f…` 及脚本 SHA-256 均与 `git ls-tree dfbe70c7`/独立哈希一致，因此 exact-byte 绑定成立。[运行证据](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/readonly-contract-tests.txt:1)
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:1180:3. 修改后重新运行测试，并用新 script/test blobs 更新可绑定证据。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:1208:证据文件记录的 parent HEAD `a775f80…` 正是 `dfbe70c7` 的父提交；其中 script blob `2f3fd0a…`、test blob `8131f1f…` 及脚本 SHA-256 均与 `git ls-tree dfbe70c7`/独立哈希一致，因此 exact-byte 绑定成立。[运行证据](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/readonly-contract-tests.txt:1)
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:1223:3. 修改后重新运行测试，并用新 script/test blobs 更新可绑定证据。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:1232:/bin/zsh -lc 'git -c core.quotePath=false show f4112c2c:backend/tests/regression/test_census_dead_letter_readonly_contract.py | nl -ba' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:1629:/bin/zsh -lc "git -c core.quotePath=false show 'f4112c2c:_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' | jq 'keys'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:1656:/bin/zsh -lc "git -c core.quotePath=false show 'f4112c2c:_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' | jq '.records[0] | keys'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:1683:/bin/zsh -lc "git -c core.quotePath=false show 'f4112c2c:_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' | jq '{records:(.records|length), total_lines, total_records, unparseable:(.unparseable_lines|length), class_from_records:(.records|group_by(.class)|map({key:.[0].class,value:length})|from_entries), recoverability_from_records:(.records|group_by(.recoverability)|map({key:.[0].recoverability,value:length})|from_entries), inline_from_records:(.records|group_by(.inline_state)|map({key:.[0].inline_state,value:length})|from_entries), header_class:.class_distribution, header_recoverability:.recoverability_distribution}'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:1719:/bin/zsh -lc "git -c core.quotePath=false show 'f4112c2c:_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' | jq '[.records | sort_by([.name,.episode_body_sha256,.group_id]) | group_by([.name,.episode_body_sha256,.group_id])[] | select(length>1) | {key:[.[0].name,.[0].episode_body_sha256,.[0].group_id], occurrences:length, line_nos:map(.line_no)}] | {clusters:length, rows:(map(.occurrences)|add), data:.}'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:1819:/bin/zsh -lc "git -c core.quotePath=false show 'f4112c2c:_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' | jq '[.records[] | select(.attribution_conflict == true)]'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:1904:/bin/zsh -lc 'git -c core.quotePath=false diff f4112c2c''^ f4112c2c -- _bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:1927:/bin/zsh -lc "git -c core.quotePath=false show 'f4112c2c:_bmad-output/审查/G4-9-evidence/readonly-contract-tests.txt' | nl -ba" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:1934:     5	被测脚本 blob: 87266e092777fe45e93dde1dfba6eac197dae527
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:1936:     7	测试文件 blob: 541ec8b35e9d1fdadff3348d8a43a8d959e08c7c
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:1966:/bin/zsh -lc 'git show f4112c2c:backend/scripts/census_dead_letter_episodes.py | shasum -a 256' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:1972:/bin/zsh -lc 'git show f4112c2c:backend/tests/regression/test_census_dead_letter_readonly_contract.py | shasum -a 256' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:1978:/bin/zsh -lc "git -c core.quotePath=false show 'f4112c2c:_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt' | nl -ba" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:1999:    19	dfbe70c7  CARD-G4-9 round-10 解阻整改（矛盾声明全清 / 字段语义 / 测试如实标注 20 passed / 可绑定证据）
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:2004:/bin/zsh -lc "git show f4112c2c:backend/tests/regression/test_census_dead_letter_readonly_contract.py | rg '"'^def test_'"'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:2029:/bin/zsh -lc "git -c core.quotePath=false show 'HEAD:_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt' | nl -ba" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:2050:    19	dfbe70c7  CARD-G4-9 round-10 解阻整改（矛盾声明全清 / 字段语义 / 测试如实标注 / 可绑定证据）
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:2051:    20	f4112c2c  CARD-G4-9 round-11 解阻整改（残留声明清除 / 坏 JSON 与输入不变测试补强 / 证据绑新 blob）
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:2056:/bin/zsh -lc 'git rev-parse f4112c2c''^' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:2062:**Confirming evidence binding to exact git blobs**
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:2066:/bin/zsh -lc 'git ls-tree f4112c2c -- _bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:2078:/bin/zsh -lc "git show 'f4112c2c:_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' | jq '{
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:2101:/bin/zsh -lc "git show 'f4112c2c:_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' | jq '
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:2197:/bin/zsh -lc "git show 'f4112c2c:_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' | jq '{
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:2230:/bin/zsh -lc "git show f4112c2c:backend/tests/regression/test_census_dead_letter_readonly_contract.py | rg -n -i 'mock|monkeypatch|skip|xfail|patch'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:2236:/bin/zsh -lc "git show f4112c2c:backend/scripts/census_dead_letter_episodes.py | nl -ba | sed -n '1,80p;300,425p;780,900p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:2568:/bin/zsh -lc "git show f4112c2c:backend/scripts/census_dead_letter_episodes.py | rg -n 'argparse|add_argument|def main|if __name__'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:2570:/bin/zsh -lc "git show f4112c2c:backend/scripts/census_dead_letter_episodes.py | rg -n 'open\\(|os\\.open|sqlite3\\.connect|write|replace|unlink|remove|mkdir|fchmod|fsync|truncate|O_[A-Z]+'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:2623:**Verifying exact-byte evidence binding**
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:2780:  ✓ 核对历史裁定索引、仓库规则与 f4112c2c 对象边界
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:2804:**Verifying artifact and commit bindings**
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:2874:其余两轨已闭合：测试补强无新的必需缺口；`readonly-contract-tests.txt` 的 20 个测试名、17/3 构成、两个 blob 与 SHA-256 均能逐项绑定到 `f4112c2c`。92 条 ledger 也已从 `records[]` 与 exact raw DLQ 只读重算：89/2/1、4/88/0/0、6 簇/29 行、unparseable 0、3 个 conflict 全为 `no_token`，全部一致。最终将是“ledger PASS、有限前提下生成器 PASS、UAT/报告 FAIL”。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:2886:/bin/zsh -lc 'git rev-parse f4112c2c''^{tree}' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:2907:  ✓ 核对历史裁定索引、仓库规则与 f4112c2c 对象边界
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:2931:可绑定证据 **PASS**：`f4112c2c` tree 中脚本/test blob 确为 `87266e09…`、`541ec8b3…`；独立 SHA-256 与证据第 5–8 行一致，20 个 PASSED 名称与测试 blob 的 20 个测试函数逐项一致。[运行证据](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/readonly-contract-tests.txt:5) 这是 exact-byte 绑定，不冒充本轮 clean-commit 重跑。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:2939:无需再改测试、脚本或重生成当前绑定证据。全程未修改任何文件。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:2956:可绑定证据 **PASS**：`f4112c2c` tree 中脚本/test blob 确为 `87266e09…`、`541ec8b3…`；独立 SHA-256 与证据第 5–8 行一致，20 个 PASSED 名称与测试 blob 的 20 个测试函数逐项一致。[运行证据](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/readonly-contract-tests.txt:5) 这是 exact-byte 绑定，不冒充本轮 clean-commit 重跑。
543e8a34:_bmad-output/审查/codex-review-CARD-G4-9-round12.md:2964:无需再改测试、脚本或重生成当前绑定证据。全程未修改任何文件。

**Clarifying binding evidence exceptions**
**Planning ledger raw data verification**
**Designing ledger JSON recomputation**
**Inspecting ledger structure with jq**
codex
目前措辞轨未发现新的非引述性过强断言：命中项都已改为“终态相同但不证明期间零写入”、逐例而非全路径、DB 静止仅为操作者前提。变更边界也已缩小：脚本、测试、ledger、`readonly-contract-tests.txt` 及其余运行证据 blob 均一致；跨 `f4112c2c..543e8a34` 唯一额外变化是中间提交 `05c85324` 对后置 receipt 的元数据补录，我会在终裁中单独披露，不把它误称为重生成绑定证据。
exec
/bin/zsh -lc "git show '543e8a34:_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' | jq 'keys'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
[
  "attribution_conflicts",
  "card",
  "class_deviation",
  "class_distribution",
  "compare_copies",
  "dlq_file",
  "duplicate_clusters",
  "expected_class_distribution",
  "generated_at",
  "inline_state_distribution",
  "privacy",
  "qa_metrics_probe",
  "records",
  "recoverability_distribution",
  "stable_key_semantics",
  "total_lines",
  "total_records",
  "unparseable_lines",
  "unrecoverable_list",
  "unverifiable_list"
]

exec
/bin/zsh -lc "git show '543e8a34:_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' | jq '{total_lines,total_records,records_len:(.records|length),unparseable_len:(.unparseable_lines|length),header_class:.class_distribution,derived_class:(.records|group_by(.class)|map({key:.[0].class,value:length})|from_entries),header_inline:.inline_state_distribution,derived_inline:(.records|group_by(.inline_state)|map({key:.[0].inline_state,value:length})|from_entries),header_recoverability:.recoverability_distribution,derived_recoverability:(.records|group_by(.recoverability)|map({key:.[0].recoverability,value:length})|from_entries)}'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
{
  "total_lines": 92,
  "total_records": 92,
  "records_len": 92,
  "unparseable_len": 0,
  "header_class": {
    "budget_400": 89,
    "schema_entity_type": 2,
    "group_id_format": 1,
    "unexpected": 0
  },
  "derived_class": {
    "budget_400": 89,
    "group_id_format": 1,
    "schema_entity_type": 2
  },
  "header_inline": {
    "full_verified": 4,
    "truncated_prefix": 88,
    "anomaly": 0
  },
  "derived_inline": {
    "full_verified": 4,
    "truncated_prefix": 88
  },
  "header_recoverability": {
    "byte_exact": 4,
    "approximate": 88,
    "unverifiable": 0,
    "unrecoverable": 0
  },
  "derived_recoverability": {
    "approximate": 88,
    "byte_exact": 4
  }
}

exec
/bin/zsh -lc "git show '543e8a34:_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' | jq '[.records[] | select(.attribution_conflict == true) | {line_no,name,class,inline_state,recoverability,attribution_conflict_reason,request_id}]'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
[
  {
    "line_no": null,
    "name": "callout_annotation:P0 final 验证",
    "class": "schema_entity_type",
    "inline_state": "full_verified",
    "recoverability": "byte_exact",
    "attribution_conflict_reason": "no_token",
    "request_id": null
  },
  {
    "line_no": null,
    "name": "callout_annotation:递归 base case 概念",
    "class": "schema_entity_type",
    "inline_state": "full_verified",
    "recoverability": "byte_exact",
    "attribution_conflict_reason": "no_token",
    "request_id": null
  },
  {
    "line_no": null,
    "name": "callout_annotation:递归 base case",
    "class": "group_id_format",
    "inline_state": "full_verified",
    "recoverability": "byte_exact",
    "attribution_conflict_reason": "no_token",
    "request_id": null
  }
]

exec
/bin/zsh -lc "git show '543e8a34:_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' | jq '[.records | sort_by([.name,.episode_body_sha256,.group_id]) | group_by([.name,.episode_body_sha256,.group_id])[] | select(length>1) | {name:.[0].name,sha:.[0].episode_body_sha256,group_id:.[0].group_id,occurrences:length,line_nos:map(.line_no)}] | {clusters:length,rows:(map(.occurrences)|add),data:.}'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
{
  "clusters": 6,
  "rows": 29,
  "data": [
    {
      "name": "conversation_distillation:Distilled summary for node session:426ff",
      "sha": "288e4b506e72402e22c8b08fa9608c8dc9e1870ccdd43ed4ab93c95655435064",
      "group_id": "vault:canvas_vault",
      "occurrences": 2,
      "line_nos": [
        null,
        null
      ]
    },
    {
      "name": "conversation_distillation:Distilled summary for node session:426ff",
      "sha": "f9682670197b1339166db46bc7a6b49cca01d745e100568dfdd88b6aa15c6f51",
      "group_id": "vault:canvas_vault",
      "occurrences": 3,
      "line_nos": [
        null,
        null,
        null
      ]
    },
    {
      "name": "qa_highlight:Q: What is the relationship between a co",
      "sha": "04e26b3060192bc9de508b2e75c508fba86553a82bea1e910bc24771c75834b5",
      "group_id": "vault:canvas_vault",
      "occurrences": 2,
      "line_nos": [
        null,
        null
      ]
    },
    {
      "name": "qa_highlight:Q: What is the relationship between a co",
      "sha": "7a830d4e3c5d52fe3699e0065c5ab61ae013eca3dcf6dd79cf246e37fc4d8629",
      "group_id": "vault:canvas_vault",
      "occurrences": 2,
      "line_nos": [
        null,
        null
      ]
    },
    {
      "name": "qa_highlight:Q: What is the relationship between a co",
      "sha": "f22956e79a5a23be64d05cd806fd78773916c5bc40b10f9cfd7d5fda0814e10e",
      "group_id": "vault:canvas_vault",
      "occurrences": 4,
      "line_nos": [
        null,
        null,
        null,
        null
      ]
    },
    {
      "name": "session-archive:426ffbde-15f6-4b",
      "sha": "c93058c9850c6999310e98df9e6ebc26063b96fa6f0649fb1ec6d9d04c88a7fe",
      "group_id": "vault:canvas_vault",
      "occurrences": 16,
      "line_nos": [
        null,
        null,
        null,
        null,
        null,
        null,
        null,
        null,
        null,
        null,
        null,
        null,
        null,
        null,
        null,
        null
      ]
    }
  ]
}

exec
/bin/zsh -lc "git show '543e8a34:_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' | jq '.duplicate_clusters'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
[
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
]

exec
/bin/zsh -lc "git show '543e8a34:_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' | jq '{dlq_file,privacy,qa_metrics_probe}'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
{
  "dlq_file": {
    "path": "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl",
    "exists": true,
    "line_count": 92,
    "sha256": "3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590",
    "mtime_utc": "2026-08-11T14:01:25.808462+00:00",
    "mtime_note": "mtime 取自读取用 fd 的 fstat；绑定 exact bytes 的是 sha256"
  },
  "privacy": "private-only: transcript_paths 含本机用户名与 session UUID，禁止外发/公网发布",
  "qa_metrics_probe": {
    "db_path": "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/qa_metrics.db",
    "source_fd_opened_readonly": true,
    "bytes_read_from_verified_fd": 16384,
    "file_identity_verified": true,
    "read_mode": "in_memory_deserialize_from_verified_fd",
    "source_sha256": "6cb5510dc91cf1c29c7ce6510013238cf83b5eae6305180e6aa9320a957a6a05",
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
/bin/zsh -lc "git show '543e8a34:_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' | shasum -a 256" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
7002edc474cfdfaf8de62e9e04978328dde4905ff6b7c1b440895b52b457efc0  -

exec
/bin/zsh -lc "git ls-tree f4112c2c -- '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' && git ls-tree 543e8a34 -- '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
100644 blob 9ac1beb158804c5deb9d0bc572ea51da730dc709	"_bmad-output/\345\256\241\346\237\245/G4-9-dlq-ledger-2026-08-28.json"
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
100644 blob 9ac1beb158804c5deb9d0bc572ea51da730dc709	"_bmad-output/\345\256\241\346\237\245/G4-9-dlq-ledger-2026-08-28.json"

**Validating stable_key uniqueness and line_no mapping**
exec
/bin/zsh -lc "git show '543e8a34:_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' | jq '.records[0] | keys'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
[
  "attribution_conflict",
  "attribution_conflict_reason",
  "class",
  "episode_body_length",
  "episode_body_sha256",
  "error_excerpt",
  "error_type",
  "failed_at",
  "group_id",
  "inline_state",
  "name",
  "recoverability",
  "recoverability_basis",
  "reference_time",
  "session_token",
  "sha_check",
  "source_description",
  "stable_key",
  "transcript_match_count",
  "transcript_paths"
]

exec
/bin/zsh -lc "git show '543e8a34:_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' | jq '.records[0]'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
{
  "stable_key": {
    "line_no": 1,
    "sha256_prefix": "7e33da5e96e6239f",
    "request_id": "281466113679440"
  },
  "name": "callout_annotation:P0 final 验证",
  "group_id": "vault:default",
  "source_description": "callout-annotation-record",
  "error_type": "EntityTypeValidationError",
  "error_excerpt": "name cannot be used as an attribute for LearningConcept as it is a protected attribute name.",
  "failed_at": "2026-05-14T08:20:15.793508+00:00",
  "reference_time": "2026-05-14T08:20:10.506386+00:00",
  "class": "schema_entity_type",
  "episode_body_length": 180,
  "episode_body_sha256": "7e33da5e96e6239f5584beb0011760bae646b59b09417fb72bd4c5c4b328fea4",
  "inline_state": "full_verified",
  "sha_check": "pass",
  "session_token": null,
  "transcript_paths": [],
  "transcript_match_count": 0,
  "attribution_conflict": true,
  "attribution_conflict_reason": "no_token",
  "recoverability": "byte_exact",
  "recoverability_basis": "inline 正文全量：sha256 重算与声明一致且长度精确匹配"
}

exec
/bin/zsh -lc "git show '543e8a34:_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' | jq '[.records[] | select(.attribution_conflict == true) | {line_no:.stable_key.line_no,name,class,inline_state,recoverability,attribution_conflict_reason,request_id:.stable_key.request_id}]'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
[
  {
    "line_no": 1,
    "name": "callout_annotation:P0 final 验证",
    "class": "schema_entity_type",
    "inline_state": "full_verified",
    "recoverability": "byte_exact",
    "attribution_conflict_reason": "no_token",
    "request_id": "281466113679440"
  },
  {
    "line_no": 2,
    "name": "callout_annotation:递归 base case 概念",
    "class": "schema_entity_type",
    "inline_state": "full_verified",
    "recoverability": "byte_exact",
    "attribution_conflict_reason": "no_token",
    "request_id": "281466014769488"
  },
  {
    "line_no": 3,
    "name": "callout_annotation:递归 base case",
    "class": "group_id_format",
    "inline_state": "full_verified",
    "recoverability": "byte_exact",
    "attribution_conflict_reason": "no_token",
    "request_id": "281466427090256"
  }
]

exec
/bin/zsh -lc "git show '543e8a34:_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' | jq '[.records | sort_by([.name,.episode_body_sha256,.group_id]) | group_by([.name,.episode_body_sha256,.group_id])[] | select(length>1) | {name:.[0].name,sha:.[0].episode_body_sha256,group_id:.[0].group_id,occurrences:length,line_nos:map(.stable_key.line_no)}] | sort_by(-.occurrences,.line_nos[0]) | {clusters:length,rows:(map(.occurrences)|add),data:.}'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
{
  "clusters": 6,
  "rows": 29,
  "data": [
    {
      "name": "session-archive:426ffbde-15f6-4b",
      "sha": "c93058c9850c6999310e98df9e6ebc26063b96fa6f0649fb1ec6d9d04c88a7fe",
      "group_id": "vault:canvas_vault",
      "occurrences": 16,
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
      ]
    },
    {
      "name": "qa_highlight:Q: What is the relationship between a co",
      "sha": "f22956e79a5a23be64d05cd806fd78773916c5bc40b10f9cfd7d5fda0814e10e",
      "group_id": "vault:canvas_vault",
      "occurrences": 4,
      "line_nos": [
        24,
        41,
        78,
        82
      ]
    },
    {
      "name": "conversation_distillation:Distilled summary for node session:426ff",
      "sha": "f9682670197b1339166db46bc7a6b49cca01d745e100568dfdd88b6aa15c6f51",
      "group_id": "vault:canvas_vault",
      "occurrences": 3,
      "line_nos": [
        8,
        12,
        68
      ]
    },
    {
      "name": "qa_highlight:Q: What is the relationship between a co",
      "sha": "7a830d4e3c5d52fe3699e0065c5ab61ae013eca3dcf6dd79cf246e37fc4d8629",
      "group_id": "vault:canvas_vault",
      "occurrences": 2,
      "line_nos": [
        13,
        45
      ]
    },
    {
      "name": "conversation_distillation:Distilled summary for node session:426ff",
      "sha": "288e4b506e72402e22c8b08fa9608c8dc9e1870ccdd43ed4ab93c95655435064",
      "group_id": "vault:canvas_vault",
      "occurrences": 2,
      "line_nos": [
        16,
        64
      ]
    },
    {
      "name": "qa_highlight:Q: What is the relationship between a co",
      "sha": "04e26b3060192bc9de508b2e75c508fba86553a82bea1e910bc24771c75834b5",
      "group_id": "vault:canvas_vault",
      "occurrences": 2,
      "line_nos": [
        37,
        86
      ]
    }
  ]
}

exec
/bin/zsh -lc "git show '543e8a34:_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' | jq '{line_numbers_unique:([.records[].stable_key.line_no]|unique|length),line_min:([.records[].stable_key.line_no]|min),line_max:([.records[].stable_key.line_no]|max),stable_keys_unique:([.records[].stable_key|tojson]|unique|length),conflict_header:.attribution_conflicts,conflict_derived:([.records[]|select(.attribution_conflict==true)]|length),unverifiable_list_len:(.unverifiable_list|length),unrecoverable_list_len:(.unrecoverable_list|length),class_deviation}'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
{
  "line_numbers_unique": 92,
  "line_min": 1,
  "line_max": 92,
  "stable_keys_unique": 92,
  "conflict_header": [
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
  "conflict_derived": 3,
  "unverifiable_list_len": 0,
  "unrecoverable_list_len": 0,
  "class_deviation": {}
}

**Planning exact raw DLQ recomputation**
**Designing read-only raw ledger verification**
**Mapping raw lines to ledger keys**
**Planning JSONL and ledger comparison**
**Designing ledger and raw data integrity checks**
**Planning ledger hash validation and stats extraction**
**Preparing to compare raw and stable keys with jq**
exec
/bin/zsh -lc "wc -l '/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
      92 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl

exec
/bin/zsh -lc "shasum -a 256 '/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl

exec
/bin/zsh -lc "jq -s '.[0] | keys' '/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
[
  "created_at",
  "edge_type_names",
  "entity_type_names",
  "episode_body",
  "episode_body_length",
  "episode_body_sha256",
  "error",
  "error_type",
  "failed_at",
  "group_id",
  "name",
  "reference_time",
  "request_id",
  "retry_count",
  "source_description"
]

exec
/bin/zsh -lc "git show '543e8a34:_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json' | jq --slurpfile raw '/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl' '. as "'$l | {raw_records:($raw|length), stable_key_mismatches:[range(0;($raw|length)) as $i | select(($l.records[$i].stable_key.line_no != ($i+1)) or ($l.records[$i].stable_key.sha256_prefix != ($raw[$i].episode_body_sha256[0:16])) or ($l.records[$i].stable_key.request_id != $raw[$i].request_id)) | ($i+1)], identity_mismatches:[range(0;($raw|length)) as $i | select(($l.records[$i].name != $raw[$i].name) or ($l.records[$i].group_id != $raw[$i].group_id) or ($l.records[$i].episode_body_sha256 != $raw[$i].episode_body_sha256) or ($l.records[$i].error_type != $raw[$i].error_type)) | ($i+1)]}'"'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
{
  "raw_records": 92,
  "stable_key_mismatches": [],
  "identity_mismatches": []
}

**Planning independent episode hashing and classification**
**Analyzing classification and recoverability logic**
**Evaluating read-only JSON generation approach**
**Planning episode body verification**
exec
/bin/zsh -lc "git show '543e8a34:backend/scripts/census_dead_letter_episodes.py' | rg -n '"'^(def|class) |budget_400|schema_entity_type|group_id_format|inline_state|recoverability|attribution_conflict_reason|duplicate_clusters'"'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
30:    台账 recoverability_basis 如实声明。
62:  - reference_time 逐条透传 + duplicate_clusters 段（同 name+sha+group 的
90:EXPECTED_CLASS_DIST = {"budget_400": 89, "schema_entity_type": 2, "group_id_format": 1}
93:def _path_is_within(target: str, root: str) -> bool:
120:def _same_file(a: str, b: str) -> bool:
128:def _split_jsonl_lines(raw: bytes) -> list[tuple[str, str | None]]:
151:def classify(rec: dict) -> str:
156:        return "schema_entity_type"
158:        return "group_id_format"
160:        return "budget_400"
164:def inline_state(rec: dict) -> tuple[str, str]:
165:    """返回 (inline_state, sha_check)，fail-closed（见模块 docstring）。"""
188:def full_body_verified(rec: dict) -> bool:
209:def session_tokens(name: object) -> list[str]:
221:def resolve_group_attribution(tokens: list[str], transcripts_dir: Path) -> dict:
320:def probe_qa_metrics(db_path: Path, error_types: list[str]) -> tuple[dict, tuple[int, int] | None]:
414:def snapshot_file(path: Path) -> tuple[bytes, dict, tuple[int, int]]:
450:def describe_copy(path: Path) -> tuple[dict, tuple[int, int] | None]:
458:def main(argv: list[str] | None = None) -> int:
624:        state, sha_check = inline_state(rec)
697:                "inline_state": state,
705:                "attribution_conflict_reason": (
720:                "recoverability": recover,
721:                "recoverability_basis": basis,
731:    duplicate_clusters = [
775:            k: class_dist.get(k, 0) for k in ["budget_400", "schema_entity_type", "group_id_format", "unexpected"]
779:        "recoverability_distribution": {
782:        "inline_state_distribution": {
788:        "duplicate_clusters": duplicate_clusters,
902:        f"recoverability={dict(recover_dist)} | 归因冲突={len(attribution_conflicts)} | "
903:        f"重复簇={len(duplicate_clusters)} | 偏差={deviation or '无'} | "

exec
/bin/zsh -lc "git show '543e8a34:backend/scripts/census_dead_letter_episodes.py' | nl -ba | sed -n '120,320p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
   120	def _same_file(a: str, b: str) -> bool:
   121	    """按 inode 身份比较两个路径（不依赖字符串大小写/规范化）。"""
   122	    try:
   123	        return os.path.samefile(a, b)
   124	    except OSError:
   125	        return False
   126	
   127	
   128	def _split_jsonl_lines(raw: bytes) -> list[tuple[str, str | None]]:
   129	    """按 JSONL 规范只以 LF 分帧，返回 [(line_text, decode_error_or_None)]。
   130	
   131	    - 不用 splitlines(): U+2028/U+2029/裸 CR 会误分行（round-3）。
   132	    - 逐行 **strict** decode（round-4 MEDIUM 整改）: errors="replace" 会把非法
   133	      UTF-8 静默改写成合法对象，让坏字节冒充有效记录。解码失败的行带错误信息
   134	      返回，由调用方归入 unparseable。
   135	    """
   136	    had_trailing_lf = raw.endswith(b"\n")
   137	    if had_trailing_lf:
   138	        raw = raw[:-1]
   139	    if not raw:
   140	        # round-5 LOW 整改: 单独 b"\n" 是一个空行，不是 0 行
   141	        return [("", None)] if had_trailing_lf else []
   142	    out: list[tuple[str, str | None]] = []
   143	    for chunk in raw.split(b"\n"):
   144	        try:
   145	            out.append((chunk.decode("utf-8"), None))
   146	        except UnicodeDecodeError as e:
   147	            out.append(("", f"utf8_decode_error: {e}"))
   148	    return out
   149	
   150	
   151	def classify(rec: dict) -> str:
   152	    et = rec.get("error_type", "")
   153	    if not isinstance(et, str):
   154	        return "unexpected"
   155	    if et == "EntityTypeValidationError":
   156	        return "schema_entity_type"
   157	    if et == "GroupIdValidationError":
   158	        return "group_id_format"
   159	    if et == "BadRequestError" and _BUDGET_PAT.search(str(rec.get("error", ""))):
   160	        return "budget_400"
   161	    return "unexpected"
   162	
   163	
   164	def inline_state(rec: dict) -> tuple[str, str]:
   165	    """返回 (inline_state, sha_check)，fail-closed（见模块 docstring）。"""
   166	    body = rec.get("episode_body", "")
   167	    if not isinstance(body, str):  # round-4 LOW: episode_body 错型
   168	        return "anomaly", "FAIL"
   169	    declared_len = rec.get("episode_body_length")
   170	    declared_sha = rec.get("episode_body_sha256", "")
   171	    sha_wellformed = isinstance(declared_sha, str) and bool(_SHA256_HEX_PAT.match(declared_sha))
   172	    # round-5 LOW 整改: errors="replace" 会把 JSON escaped lone surrogate
   173	    # (\udXXX) 改写成 replacement char，可被构造出"对得上账"的假 full_verified。
   174	    # 改 strict：无法编码即判 anomaly。
   175	    try:
   176	        body_bytes = body.encode("utf-8")
   177	    except UnicodeEncodeError:
   178	        return "anomaly", "FAIL"
   179	    recomputed = hashlib.sha256(body_bytes).hexdigest()
   180	    len_ok = isinstance(declared_len, int) and not isinstance(declared_len, bool)
   181	    if sha_wellformed and recomputed == declared_sha and len_ok and len(body) == declared_len:
   182	        return "full_verified", "pass"
   183	    if sha_wellformed and len(body) == 200 and len_ok and declared_len > 200:
   184	        return "truncated_prefix", "prefix_only"
   185	    return "anomaly", "FAIL"
   186	
   187	
   188	def full_body_verified(rec: dict) -> bool:
   189	    """episode_body_full 在盘且 sha **与长度**双门对账通过（生产 opt-in 字段，当前 live 0 条）。
   190	
   191	    round-2 HIGH-1 整改: 原实现只核 sha，声明长度矛盾的记录（如 body="abc"
   192	    但 episode_body_length=999）仍被判 byte_exact —— 与 inline 侧同门收紧。
   193	    """
   194	    full = rec.get("episode_body_full")
   195	    declared_sha = rec.get("episode_body_sha256", "")
   196	    declared_len = rec.get("episode_body_length")
   197	    if not isinstance(full, str) or not _SHA256_HEX_PAT.match(str(declared_sha)):
   198	        return False
   199	    # round-5 LOW 整改: bool 是 int 子类 —— episode_body_length=True 会通过长度门
   200	    if not isinstance(declared_len, int) or isinstance(declared_len, bool) or len(full) != declared_len:
   201	        return False
   202	    try:
   203	        full_bytes = full.encode("utf-8")
   204	    except UnicodeEncodeError:
   205	        return False
   206	    return hashlib.sha256(full_bytes).hexdigest() == declared_sha
   207	
   208	
   209	def session_tokens(name: object) -> list[str]:
   210	    """round-4 LOW 整改: name 非 str（None/数字/列表）不再抛异常。"""
   211	    if not isinstance(name, str):
   212	        return []
   213	    tokens = []
   214	    m = _SESSION_ARCHIVE_PAT.match(name)
   215	    if m:
   216	        tokens.append(m.group(1).lower())
   217	    tokens.extend(t.lower() for t in _SESSION_INLINE_PAT.findall(name))
   218	    return tokens
   219	
   220	
   221	def resolve_group_attribution(tokens: list[str], transcripts_dir: Path) -> dict:
   222	    """组级归因，fail-closed。
   223	
   224	    round-5 BLOCKER① 整改: **先扫描后判定**。原实现在 token 冲突/无 token 时
   225	    扫描前早退，导致这些候选从未进入 all_candidate_paths → 不进 --out 保护集
   226	    → 可被无竞态截断。现无条件对每个 token 扫描收集候选（保护集所需），
   227	    再做冲突/唯一性判定。
   228	    """
   229	    result = {
   230	        "session_token": None,
   231	        "transcript_paths": [],
   232	        "transcript_exists": False,
   233	        "transcript_match_count": 0,
   234	        "attribution_conflict": False,
   235	        # 保护集必须覆盖**所有见到的候选**（含不可读、含被冲突分支排除的）
   236	        "all_candidate_paths": [],
   237	    }
   238	    uniq = sorted(set(tokens), key=len)
   239	
   240	    root_str = str(transcripts_dir)
   241	    walk_errors: list[str] = []
   242	
   243	    def _on_walk_error(err: OSError) -> None:
   244	        walk_errors.append(f"{getattr(err, 'filename', '?')}: {err}")
   245	
   246	    # 单次遍历收集**每个 token** 的候选（无条件，供保护集与判定共用）
   247	    per_token: dict[str, list[str]] = {t: [] for t in uniq}
   248	    all_candidates: list[str] = []
   249	    unreadable: list[str] = []
   250	    stat_failures: list[str] = []
   251	    # round-6 整改: **无论有无 token 都遍历** —— no_token 时原实现完全不扫描，
   252	    # all_candidate_paths 为空，该组见不到的候选就进不了保护集。
   253	    for dirpath, _dirnames, filenames in os.walk(transcripts_dir, onerror=_on_walk_error, followlinks=False):
   254	        for fname in filenames:
   255	            if fname.endswith(".jsonl"):
   256	                matched = [t for t in uniq if fname.startswith(t)]
   257	                candidate = os.path.join(dirpath, fname)
   258	                # 候选一律入 all_candidate_paths（保护集口径），再谈可用性
   259	                all_candidates.append(candidate)
   260	                if not matched:
   261	                    continue
   262	                try:
   263	                    if os.path.islink(candidate) or not os.path.isfile(candidate):
   264	                        continue
   265	                except OSError as e:
   266	                    stat_failures.append(f"{candidate}: {e}")
   267	                    continue
   268	                if not os.access(candidate, os.R_OK):
   269	                    unreadable.append(candidate)
   270	                    continue
   271	                if not _path_is_within(candidate, root_str):
   272	                    continue  # 目录 symlink 逃逸（inode 身份判定）
   273	                for t in matched:
   274	                    per_token[t].append(candidate)
   275	    result["all_candidate_paths"] = sorted(set(all_candidates))
   276	
   277	    # round-8 HIGH 整改: 早退分支也必须携带扫描错误 —— 否则 no_token /
   278	    # token_conflict 组的 walk 错误不会进入 scan_blocked 判定。
   279	    if walk_errors:
   280	        result["scan_errors"] = walk_errors[:5]
   281	    if stat_failures:
   282	        result["stat_failures"] = stat_failures[:5]
   283	
   284	    if not uniq:
   285	        # 无 token: 未做任何归因扫描 —— 不是"确认无源"（round-5 MEDIUM 整改）
   286	        result["attribution_conflict"] = True
   287	        result["no_token"] = True
   288	        return result
   289	
   290	    longest = uniq[-1]
   291	    if any(not longest.startswith(t) for t in uniq[:-1]):
   292	        result["attribution_conflict"] = True
   293	        result["token_conflict"] = True
   294	        return result
   295	    result["session_token"] = longest
   296	
   297	    if walk_errors:
   298	        result["scan_errors"] = walk_errors[:5]
   299	        result["attribution_conflict"] = True
   300	        return result
   301	    if stat_failures:
   302	        result["stat_failures"] = stat_failures[:5]
   303	        result["attribution_conflict"] = True
   304	        return result
   305	    if unreadable:
   306	        result["unreadable_candidates"] = unreadable[:5]
   307	        result["attribution_conflict"] = True
   308	        return result
   309	
   310	    matches = sorted(set(per_token[longest]))
   311	    result["transcript_paths"] = matches
   312	    result["transcript_match_count"] = len(matches)
   313	    if len(matches) == 1:
   314	        result["transcript_exists"] = True
   315	    elif len(matches) > 1:
   316	        result["attribution_conflict"] = True  # ambiguous 多命中，拒绝采信
   317	    return result
   318	
   319	
   320	def probe_qa_metrics(db_path: Path, error_types: list[str]) -> tuple[dict, tuple[int, int] | None]:

exec
/bin/zsh -lc "git show '543e8a34:backend/scripts/census_dead_letter_episodes.py' | nl -ba | sed -n '520,790p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
   520	            print(
   521	                f"--out 落在 transcripts 根内（恢复源区域），无条件拒绝写出: {args.out}",
   522	                file=sys.stderr,
   523	            )
   524	            return 2
   525	        input_paths = [args.dlq, *args.compare] + ([args.qa_metrics_db] if args.qa_metrics_db else [])
   526	        if any(_same_file(args.out, ip) for ip in input_paths):
   527	            print(f"--out 与输入文件为同一对象（inode 比较），拒绝写出: {args.out}", file=sys.stderr)
   528	            return 2
   529	
   530	    # --out 碰撞守卫（写前）。round-2 BLOCKER-1 整改: 比较**文件身份**
   531	    # (st_dev, st_ino) 而非 resolve() 字符串 —— 后者对 hardlink 与
   532	    # 大小写不敏感文件系统上的 case-only 别名均失效（Codex 实测截断输入）。
   533	    if args.out:
   534	        out_path = Path(args.out)
   535	        protected_paths = [dlq_path, *(Path(p) for p in args.compare)]
   536	        if args.qa_metrics_db:
   537	            protected_paths.append(Path(args.qa_metrics_db))
   538	        for candidate in protected_paths:
   539	            try:
   540	                cst = candidate.stat()  # 跟随 symlink: 保护的是最终目标身份
   541	                protected_ids.add((cst.st_dev, cst.st_ino))
   542	            except OSError:
   543	                # round-4 整改: stat 失败不再静默吞 —— 无法确认身份即 fail-closed
   544	                print(f"输入文件无法 stat，拒绝继续（无法建立完整保护集）: {candidate}", file=sys.stderr)
   545	                return 2
   546	        # 路径字符串比较作为第二道（输出文件尚不存在时 stat 无身份可比）
   547	        out_resolved = out_path.resolve()
   548	        if out_resolved in {p.resolve() for p in protected_paths}:
   549	            print(f"--out 与输入文件路径重合，拒绝写出（防截断）: {out_resolved}", file=sys.stderr)
   550	            return 2
   551	        if out_path.exists():
   552	            try:
   553	                out_st = out_path.stat()
   554	            except OSError as e:
   555	                print(f"--out 无法 stat，拒绝写出: {out_path} ({e})", file=sys.stderr)
   556	                return 2
   557	            if (out_st.st_dev, out_st.st_ino) in protected_ids:
   558	                print(
   559	                    f"--out 与输入文件为同一 inode（hardlink/大小写别名），拒绝写出（防截断）: {out_path}",
   560	                    file=sys.stderr,
   561	                )
   562	                return 2
   563	
   564	    # BLOCKER-2 整改: 单次读取，records 与头部描述共享同一份 exact bytes
   565	    try:
   566	        raw_bytes, dlq_info, dlq_identity = snapshot_file(dlq_path)
   567	    except OSError as e:
   568	        print(f"DLQ 无法安全读取: {dlq_path} ({e})", file=sys.stderr)
   569	        return 2
   570	    protected_ids.add(dlq_identity)  # 保护的是**实际读取对象**，非路径快照
   571	    raw_lines = _split_jsonl_lines(raw_bytes)
   572	
   573	    records: list[tuple[int, dict]] = []
   574	    unparseable: list[dict] = []
   575	    for line_no, (line, decode_err) in enumerate(raw_lines, start=1):
   576	        if decode_err is not None:
   577	            unparseable.append({"line_no": line_no, "reason": decode_err})
   578	            continue
   579	        if not line.strip():
   580	            unparseable.append({"line_no": line_no, "reason": "blank_line"})
   581	            continue
   582	        try:
   583	            rec = json.loads(line)
   584	        except json.JSONDecodeError as e:
   585	            unparseable.append({"line_no": line_no, "reason": f"json_error: {e}", "excerpt": line[:80]})
   586	            continue
   587	        # round-3 LOW 整改: 合法 JSON 但非对象（null / 数组 / 标量）此前解析成功
   588	        # 却在 rec.get() 处抛 AttributeError 炸掉全量 —— 归入 unparseable。
   589	        if not isinstance(rec, dict):
   590	            unparseable.append(
   591	                {"line_no": line_no, "reason": f"not_a_json_object: {type(rec).__name__}", "excerpt": line[:80]}
   592	            )
   593	            continue
   594	        records.append((line_no, rec))
   595	
   596	    # request_id 分组: (类型名, 值) 复合键；缺失/None → 按 line_no 单条成组
   597	    groups: dict[tuple, list[tuple[int, dict]]] = defaultdict(list)
   598	    for line_no, rec in records:
   599	        rid = rec.get("request_id")
   600	        # round-4 LOW 整改: 不可哈希的 request_id（list/dict）按 line_no 单条成组
   601	        try:
   602	            hash(rid)
   603	            hashable = True
   604	        except TypeError:
   605	            hashable = False
   606	        key = ("__missing__", line_no) if (rid is None or not hashable) else (type(rid).__name__, rid)
   607	        groups[key].append((line_no, rec))
   608	    group_attribution: dict[tuple, dict] = {}
   609	    for key, members in groups.items():
   610	        tokens: list[str] = []
   611	        for _, rec in members:
   612	            tokens.extend(session_tokens(rec.get("name", "")))
   613	        group_attribution[key] = resolve_group_attribution(tokens, transcripts_dir)
   614	
   615	    ledger_records = []
   616	    class_dist: Counter = Counter()
   617	    recover_dist: Counter = Counter()
   618	    inline_dist: Counter = Counter()
   619	    unrecoverable_keys = []
   620	    unverifiable_keys = []
   621	    attribution_conflicts = []
   622	    for line_no, rec in records:
   623	        cls = classify(rec)
   624	        state, sha_check = inline_state(rec)
   625	        rid = rec.get("request_id")
   626	        try:
   627	            hash(rid)
   628	            hashable = True
   629	        except TypeError:
   630	            hashable = False
   631	        key = ("__missing__", line_no) if (rid is None or not hashable) else (type(rid).__name__, rid)
   632	        sess = group_attribution[key]
   633	        if state == "full_verified":
   634	            recover = "byte_exact"
   635	            basis = "inline 正文全量：sha256 重算与声明一致且长度精确匹配"
   636	        elif state != "anomaly" and full_body_verified(rec):
   637	            recover = "byte_exact"
   638	            basis = "episode_body_full 在盘且 sha256+长度双门对账通过（DEAD_LETTER_STORE_FULL_BODY 生产 opt-in 字段）"
   639	        elif sess["attribution_conflict"]:
   640	            # round-5 HIGH 整改: 可见性判定**优先于** anomaly —— 源看不见时
   641	            # 无论 inline 是什么状态，都不能断言"不可恢复"。
   642	            recover = "unverifiable"
   643	            if sess.get("no_token"):
   644	                why = "记录名未携带 session token，未做任何归因扫描"
   645	            elif sess.get("token_conflict"):
   646	                why = "同组多 token 前缀冲突"
   647	            elif sess.get("scan_errors"):
   648	                why = "扫描遍历受阻（不可读子树）"
   649	            elif sess.get("stat_failures"):
   650	                why = "候选 stat 失败"
   651	            elif sess.get("unreadable_candidates"):
   652	                why = "存在不可读候选"
   653	            else:
   654	                why = "transcript 多命中 ambiguous"
   655	            extra = "；inline 亦对不上账（anomaly）" if state == "anomaly" else ""
   656	            basis = f"源可见性不足，拒绝裁定：{why}{extra}。既不宣称可恢复，也不宣称不可恢复（fail-closed）"
   657	        elif state == "anomaly":
   658	            recover = "unrecoverable"
   659	            basis = "inline 对不上账（anomaly：sha/长度与声明不符），且归因扫描完整可见但无可用源"
   660	        elif sess["transcript_exists"]:
   661	            recover = "approximate"
   662	            basis = (
   663	                f"inline 为 200 字符前缀（前缀性质依赖 to_dict()[:200] 生产不变量，sha 无法直接证明）；"
   664	                f"经 request_id 组归因到唯一在盘 transcript {sess['session_token']}"
   665	                f"（归因 ≠ 内容已验证——本工具未读 transcript 内容；G4-10 可重蒸馏/重格式化近似重建，非逐字节保证）"
   666	            )
   667	        else:
   668	            recover = "unrecoverable"
   669	            basis = "inline 截断；归因扫描完整可见（无遍历错误/无不可读候选）但未找到任何在盘上游源"
   670	        class_dist[cls] += 1
   671	        recover_dist[recover] += 1
   672	        inline_dist[state] += 1
   673	        stable_key = {
   674	            "line_no": line_no,
   675	            "sha256_prefix": str(rec.get("episode_body_sha256", ""))[:16],
   676	            "request_id": rid,
   677	        }
   678	        if recover == "unrecoverable":
   679	            unrecoverable_keys.append(stable_key)
   680	        elif recover == "unverifiable":
   681	            unverifiable_keys.append(stable_key)
   682	        if sess["attribution_conflict"]:
   683	            attribution_conflicts.append(stable_key)
   684	        ledger_records.append(
   685	            {
   686	                "stable_key": stable_key,
   687	                "name": str(rec.get("name", ""))[:80],
   688	                "group_id": rec.get("group_id"),
   689	                "source_description": rec.get("source_description"),
   690	                "error_type": rec.get("error_type"),
   691	                "error_excerpt": str(rec.get("error", ""))[:120],
   692	                "failed_at": rec.get("failed_at"),
   693	                "reference_time": rec.get("reference_time"),
   694	                "class": cls,
   695	                "episode_body_length": rec.get("episode_body_length"),
   696	                "episode_body_sha256": rec.get("episode_body_sha256"),
   697	                "inline_state": state,
   698	                "sha_check": sha_check,
   699	                "session_token": sess["session_token"],
   700	                "transcript_paths": sess["transcript_paths"],
   701	                "transcript_match_count": sess["transcript_match_count"],
   702	                "attribution_conflict": sess["attribution_conflict"],
   703	                # round-6 LOW 整改: ledger 自描述冲突原因，G4-10 可区分
   704	                # 缺 token / token 冲突 / 扫描受阻 / 不可读 / 多命中
   705	                "attribution_conflict_reason": (
   706	                    "no_token"
   707	                    if sess.get("no_token")
   708	                    else "token_conflict"
   709	                    if sess.get("token_conflict")
   710	                    else "scan_errors"
   711	                    if sess.get("scan_errors")
   712	                    else "stat_failures"
   713	                    if sess.get("stat_failures")
   714	                    else "unreadable_candidates"
   715	                    if sess.get("unreadable_candidates")
   716	                    else "ambiguous_multi_match"
   717	                    if sess["attribution_conflict"]
   718	                    else None
   719	                ),
   720	                "recoverability": recover,
   721	                "recoverability_basis": basis,
   722	            }
   723	        )
   724	
   725	    # 语义重复簇（同 name + 全文 sha + group_id）——G4-10 重放去重策略依据
   726	    cluster_map: dict[tuple, list[int]] = defaultdict(list)
   727	    for line_no, rec in records:
   728	        cluster_map[
   729	            (str(rec.get("name", "")), str(rec.get("episode_body_sha256", "")), str(rec.get("group_id")))
   730	        ].append(line_no)
   731	    duplicate_clusters = [
   732	        {"name": k[0][:80], "episode_body_sha256": k[1], "group_id": k[2], "line_nos": v, "occurrences": len(v)}
   733	        for k, v in sorted(cluster_map.items(), key=lambda kv: -len(kv[1]))
   734	        if len(v) > 1
   735	    ]
   736	
   737	    compare_infos = []
   738	    for cp in args.compare:
   739	        cinfo, cid = describe_copy(Path(cp))
   740	        compare_infos.append(cinfo)
   741	        if cid is not None:
   742	            protected_ids.add(cid)
   743	
   744	    if args.qa_metrics_db:
   745	        qa_probe, qa_identity = probe_qa_metrics(
   746	            Path(args.qa_metrics_db),
   747	            [str(r.get("error_type", "")) for _, r in records],
   748	        )
   749	        if qa_identity is not None:
   750	            protected_ids.add(qa_identity)  # 保护实际验证过的对象身份
   751	    else:
   752	        qa_probe = {"verdict": "skipped_no_db_arg"}
   753	
   754	    deviation = {
   755	        k: {"expected": EXPECTED_CLASS_DIST.get(k, 0), "actual": class_dist.get(k, 0)}
   756	        for k in sorted(set(class_dist) | set(EXPECTED_CLASS_DIST))
   757	        if EXPECTED_CLASS_DIST.get(k, 0) != class_dist.get(k, 0)
   758	    }
   759	
   760	    ledger = {
   761	        "card": "CARD-G4-9",
   762	        "generated_at": datetime.now(timezone.utc).isoformat(),
   763	        "privacy": "private-only: transcript_paths 含本机用户名与 session UUID，禁止外发/公网发布",
   764	        "stable_key_semantics": (
   765	            "冻结快照（dlq_file.sha256）内的 occurrence key；line_no 在快照内唯一，"
   766	            "sha256_prefix/request_id 为冗余对账维度——非跨文件重排或语义幂等键"
   767	        ),
   768	        "dlq_file": dlq_info,
   769	        "compare_copies": compare_infos,
   770	        "total_lines": len(raw_lines),
   771	        "total_records": len(records),
   772	        "unparseable_lines": unparseable,
   773	        # round-2 LOW 整改: 固定 schema 补零，消费者无需自行补齐缺席键
   774	        "class_distribution": {
   775	            k: class_dist.get(k, 0) for k in ["budget_400", "schema_entity_type", "group_id_format", "unexpected"]
   776	        },
   777	        "expected_class_distribution": EXPECTED_CLASS_DIST,
   778	        "class_deviation": deviation,
   779	        "recoverability_distribution": {
   780	            k: recover_dist.get(k, 0) for k in ["byte_exact", "approximate", "unverifiable", "unrecoverable"]
   781	        },
   782	        "inline_state_distribution": {
   783	            k: inline_dist.get(k, 0) for k in ["full_verified", "truncated_prefix", "anomaly"]
   784	        },
   785	        "unrecoverable_list": unrecoverable_keys,
   786	        "unverifiable_list": unverifiable_keys,
   787	        "attribution_conflicts": attribution_conflicts,
   788	        "duplicate_clusters": duplicate_clusters,
   789	        "qa_metrics_probe": qa_probe,
   790	        "records": ledger_records,

**Planning error type and budget pattern analysis**
**Verifying historical remediation record**
exec
/bin/zsh -lc "git show '543e8a34:backend/scripts/census_dead_letter_episodes.py' | nl -ba | sed -n '80,100p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
    80	from pathlib import Path
    81	
    82	# 分类规则: error_type + error 文本特征 → class
    83	_BUDGET_PAT = re.compile(r"exceed_context_size_error|exceeds the available context size")
    84	# session token: request_id 组内从 name 提取。已知局限（如实声明）: 纯启发式，
    85	# hex 样单词（added/deadbeef）可污染 inline 捕获 —— 下游有前缀一致门 + 恰 1 命中门兜底。
    86	_SESSION_ARCHIVE_PAT = re.compile(r"^session-archive:([0-9a-fA-F-]+)")
    87	_SESSION_INLINE_PAT = re.compile(r"(?<![0-9a-zA-Z_-])session:([0-9a-f-]{5,})")
    88	_SHA256_HEX_PAT = re.compile(r"^[0-9a-f]{64}$")
    89	
    90	EXPECTED_CLASS_DIST = {"budget_400": 89, "schema_entity_type": 2, "group_id_format": 1}
    91	
    92	
    93	def _path_is_within(target: str, root: str) -> bool:
    94	    """target 是否落在 root 目录内 —— 逐级向上比较 **inode 身份**。
    95	
    96	    round-7 BLOCKER 整改: 不能用路径字符串前缀判断 —— 大小写不敏感卷上
    97	    ``/Users/x`` 与 ``/users/x`` 的 realpath 字符串不同但 samefile=True，
    98	    prefix guard 会漏。本实现从 target 逐级取父目录，只要任一级与 root 同
    99	    (st_dev, st_ino) 即判定在其内；target 尚不存在时上溯到存在的祖先。
   100	    """

**Planning session token verification**
**Designing ledger verification script**
**Verifying ledger record consistency**
**Sorting numeric list**
exec
/bin/zsh -lc "python3 -c '
import collections, hashlib, json, os, re, subprocess
from pathlib import Path
raw_path=Path(\"/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl\")
ledger=json.loads(subprocess.check_output([\"git\",\"show\",\"543e8a34:_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json\"]))
raw_bytes=raw_path.read_bytes()
chunks=raw_bytes[:-1].split(b\"\\n\") if raw_bytes.endswith(b\"\\n\") else raw_bytes.split(b\"\\n\")
raw=[json.loads(x.decode(\"utf-8\")) for x in chunks]
budget=re.compile(r\"exceed_context_size_error|exceeds the available context size\")
sha_pat=re.compile(r\""'^[0-9a-f]{64}$")
archive=re.compile(r"''^session-archive:([0-9a-fA-F-]+)")
inline_token=re.compile(r"(?<![0-9a-zA-Z_-])session:([0-9a-f-]{5,})")
def cls(r):
    et=r.get("error_type","")
    if et=="EntityTypeValidationError": return "schema_entity_type"
    if et=="GroupIdValidationError": return "group_id_format"
    if et=="BadRequestError" and budget.search(str(r.get("error",""))): return "budget_400"
    return "unexpected"
def state(r):
    body=r.get("episode_body","")
    dec_len=r.get("episode_body_length")
    dec_sha=r.get("episode_body_sha256","")
    good_sha=isinstance(dec_sha,str) and bool(sha_pat.fullmatch(dec_sha))
    recomputed=hashlib.sha256(body.encode("utf-8")).hexdigest()
    good_len=isinstance(dec_len,int) and not isinstance(dec_len,bool)
    if good_sha and recomputed==dec_sha and good_len and len(body)==dec_len: return ("full_verified","pass")
    if good_sha and len(body)==200 and good_len and dec_len>200: return ("truncated_prefix","prefix_only")
    return ("anomaly","FAIL")
def tokens(name):
    if not isinstance(name,str): return []
    out=[]
    m=archive.match(name)
    if m: out.append(m.group(1).lower())
    out += [x.lower() for x in inline_token.findall(name)]
    return out
classes=collections.Counter()
states=collections.Counter()
mismatches=[]
no_token=[]
clusters=collections.defaultdict(list)
for i,(r,l) in enumerate(zip(raw,ledger["records"]),1):
    c=cls(r); s,sc=state(r)
    classes[c]+=1; states[s]+=1
    clusters[(str(r.get("name","")),str(r.get("episode_body_sha256","")),str(r.get("group_id")))].append(i)
    if not tokens(r.get("name","")): no_token.append(i)
    expected_key={"line_no":i,"sha256_prefix":str(r.get("episode_body_sha256",""))[:16],"request_id":r.get("request_id")}
    if l["class"]!=c or l["inline_state"]!=s or l["sha_check"]!=sc or l["stable_key"]!=expected_key:
        mismatches.append(i)
dups=sorted((len(v) for v in clusters.values() if len(v)>1),reverse=True)
conflict_lines=[l["stable_key"]["line_no"] for l in ledger["records"] if l["attribution_conflict"]]
path_checks=[]
for l in ledger["records"]:
    if l["recoverability"]=="approximate":
        ps=l["transcript_paths"]
        path_checks.append(len(ps)==1 and l["transcript_match_count"]==1 and os.path.isfile(ps[0]) and not os.path.islink(ps[0]))
derived_recovery=collections.Counter(l["recoverability"] for l in ledger["records"])
print(json.dumps({
  "raw_sha256":hashlib.sha256(raw_bytes).hexdigest(),
  "raw_records":len(raw),
  "class_recomputed":dict(classes),
  "inline_recomputed":dict(states),
  "record_mismatches":mismatches,
  "duplicate_cluster_sizes":dups,
  "duplicate_clusters":len(dups),
  "duplicate_rows":sum(dups),
  "no_token_lines":no_token,
  "ledger_conflict_lines":conflict_lines,
  "all_conflict_reasons_no_token":all(l["attribution_conflict_reason"]=="no_token" for l in ledger["records"] if l["attribution_conflict"]),
  "recovery_from_records":dict(derived_recovery),
  "approximate_unique_regular_transcript_checks":sum(path_checks),
  "approximate_checks_total":len(path_checks),
  "unique_transcript_paths":len({p for l in ledger["records"] for p in l["transcript_paths"]})
},ensure_ascii=False,indent=2))
'"'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
{
  "raw_sha256": "3b37460f4215f6ac0ecf9265c3b2ae6da8bcf677257da3f3225f7c29ef3ba590",
  "raw_records": 92,
  "class_recomputed": {
    "schema_entity_type": 2,
    "group_id_format": 1,
    "budget_400": 89
  },
  "inline_recomputed": {
    "full_verified": 4,
    "truncated_prefix": 88
  },
  "record_mismatches": [],
  "duplicate_cluster_sizes": [
    16,
    4,
    3,
    2,
    2,
    2
  ],
  "duplicate_clusters": 6,
  "duplicate_rows": 29,
  "no_token_lines": [
    1,
    2,
    3,
    5,
    6,
    9,
    10,
    13,
    14,
    18,
    20,
    21,
    24,
    25,
    29,
    30,
    31,
    33,
    34,
    37,
    38,
    41,
    42,
    45,
    46,
    49,
    50,
    53,
    54,
    57,
    58,
    61,
    62,
    65,
    66,
    69,
    70,
    73,
    74,
    75,
    78,
    79,
    82,
    83,
    86,
    87,
    90,
    91
  ],
  "ledger_conflict_lines": [
    1,
    2,
    3
  ],
  "all_conflict_reasons_no_token": true,
  "recovery_from_records": {
    "byte_exact": 4,
    "approximate": 88
  },
  "approximate_unique_regular_transcript_checks": 88,
  "approximate_checks_total": 88,
  "unique_transcript_paths": 7
}

**Planning group-level token recomputation**
**Verifying script and test SHA integrity**
**Confirming file consistency with target commit**
exec
/bin/zsh -lc "python3 -c '
import json,re,subprocess,collections
from pathlib import Path
raw_path=Path(\"/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/data/dead_letter_episodes.jsonl\")
raw=[json.loads(x) for x in raw_path.read_text(encoding=\"utf-8\").split(\"\\n\") if x]
ledger=json.loads(subprocess.check_output([\"git\",\"show\",\"543e8a34:_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json\"]))
archive=re.compile(r\""'^session-archive:([0-9a-fA-F-]+)")
inline=re.compile(r"(?<![0-9a-zA-Z_-])session:([0-9a-f-]{5,})")
def toks(name):
  if not isinstance(name,str): return []
  out=[]
  m=archive.match(name)
  if m: out.append(m.group(1).lower())
  out.extend(x.lower() for x in inline.findall(name))
  return out
groups=collections.defaultdict(list)
for i,r in enumerate(raw,1):
  rid=r.get("request_id")
  try: hash(rid); key=(type(rid).__name__,rid) if rid is not None else ("__missing__",i)
  except TypeError: key=("__missing__",i)
  groups[key].append((i,r))
no_token_groups=[]
for members in groups.values():
  ts=[]
  for _,r in members: ts.extend(toks(r.get("name","")))
  if not set(ts): no_token_groups.append([i for i,_ in members])
print(json.dumps({
 "request_groups":len(groups),
 "no_token_groups":no_token_groups,
 "no_token_group_rows":sum(no_token_groups,[]),
 "ledger_conflict_rows":[r["stable_key"]["line_no"] for r in ledger["records"] if r["attribution_conflict"]],
 "ledger_conflict_reasons":sorted(collections.Counter(r["attribution_conflict_reason"] for r in ledger["records"] if r["attribution_conflict"]).items())
},ensure_ascii=False,indent=2))
'"'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
{
  "request_groups": 25,
  "no_token_groups": [
    [
      1
    ],
    [
      2
    ],
    [
      3
    ]
  ],
  "no_token_group_rows": [
    1,
    2,
    3
  ],
  "ledger_conflict_rows": [
    1,
    2,
    3
  ],
  "ledger_conflict_reasons": [
    [
      "no_token",
      3
    ]
  ]
}

**Verifying documentation changes and final pass**
**Confirming receipt-only changes and commit scope**
**Planning SHA256 evidence verification**
exec
/bin/zsh -lc 'git -c core.quotePath=false diff --name-status 543e8a34 HEAD' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
M	_bmad-output/审查/G4-9-evidence/artifact-commit-receipt.txt

exec
/bin/zsh -lc "git show '543e8a34:_bmad-output/审查/G4-9-evidence/readonly-contract-tests.txt' | nl -ba" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
     1	== CARD-G4-9 只读契约回归测试运行证据（round-11 更新：绑定新 blob）==
     2	命令: cd backend && .venv/bin/pytest tests/regression/test_census_dead_letter_readonly_contract.py -v --no-header
     3	Python: Python 3.14.4
     4	工作树 HEAD（本证据生成时）: f1828f9f3936a36a25ac8cc33e3fc1a4ad216af6
     5	被测脚本 blob: 87266e092777fe45e93dde1dfba6eac197dae527
     6	被测脚本 sha256: 8a5599dd71ef54833828c3d778d2a1edbb536833880c1a4572a7f5836404e073
     7	测试文件 blob: 541ec8b35e9d1fdadff3348d8a43a8d959e08c7c
     8	测试文件 sha256: c32eaf1e06cd4d573969bce8848af3943c4a1115db51348888169dc20ebce298
     9	
    10	覆盖构成（如实）: 17 条行为测试（subprocess 跑真实 CLI + 断言文件系统事实）+ 3 条源码静态检查（弱证据，不替代行为测试）。无 mock、无 skip。
    11	⚠️ 范围声明: 每条测试只证明**它自己断言的那个场景** fail-closed；本文件不构成"所有误用路径均 fail-closed"的整体证明。
    12	
    13	--- 逐项结果:
    14	tests/regression/test_census_dead_letter_readonly_contract.py::test_no_truncation_calls_in_source PASSED [  5%]
    15	tests/regression/test_census_dead_letter_readonly_contract.py::test_imports_are_stdlib_only PASSED [ 10%]
    16	tests/regression/test_census_dead_letter_readonly_contract.py::test_no_apply_flag PASSED [ 15%]
    17	tests/regression/test_census_dead_letter_readonly_contract.py::test_out_equal_to_dlq_refused PASSED [ 20%]
    18	tests/regression/test_census_dead_letter_readonly_contract.py::test_out_hardlink_to_dlq_refused PASSED [ 25%]
    19	tests/regression/test_census_dead_letter_readonly_contract.py::test_out_inside_transcripts_root_refused PASSED [ 30%]
    20	tests/regression/test_census_dead_letter_readonly_contract.py::test_out_symlink_inside_root_refused PASSED [ 35%]
    21	tests/regression/test_census_dead_letter_readonly_contract.py::test_out_fifo_refused PASSED [ 40%]
    22	tests/regression/test_census_dead_letter_readonly_contract.py::test_out_hardlink_to_transcript_does_not_damage_source PASSED [ 45%]
    23	tests/regression/test_census_dead_letter_readonly_contract.py::test_missing_transcripts_root_refused PASSED [ 50%]
    24	tests/regression/test_census_dead_letter_readonly_contract.py::test_scan_blocked_refuses_even_without_out PASSED [ 55%]
    25	tests/regression/test_census_dead_letter_readonly_contract.py::test_unreadable_candidate_not_treated_as_source PASSED [ 60%]
    26	tests/regression/test_census_dead_letter_readonly_contract.py::test_anomaly_not_promoted_by_full_body PASSED [ 65%]
    27	tests/regression/test_census_dead_letter_readonly_contract.py::test_bool_length_rejected PASSED [ 70%]
    28	tests/regression/test_census_dead_letter_readonly_contract.py::test_bad_json_line_does_not_kill_census PASSED [ 75%]
    29	tests/regression/test_census_dead_letter_readonly_contract.py::test_invalid_utf8_line_is_unparseable PASSED [ 80%]
    30	tests/regression/test_census_dead_letter_readonly_contract.py::test_lone_lf_counts_as_one_line PASSED [ 85%]
    31	tests/regression/test_census_dead_letter_readonly_contract.py::test_output_is_private_and_no_tmp_left PASSED [ 90%]
    32	tests/regression/test_census_dead_letter_readonly_contract.py::test_inputs_unchanged_after_run PASSED [ 95%]
    33	tests/regression/test_census_dead_letter_readonly_contract.py::test_malformed_qa_db_does_not_abort_census PASSED [100%]
    34	======================= 20 passed, 10 warnings in 2.20s ========================

exec
/bin/zsh -lc "git show '543e8a34:backend/tests/regression/test_census_dead_letter_readonly_contract.py' | shasum -a 256" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
c32eaf1e06cd4d573969bce8848af3943c4a1115db51348888169dc20ebce298  -

exec
/bin/zsh -lc "git show '543e8a34:backend/scripts/census_dead_letter_episodes.py' | shasum -a 256" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
8a5599dd71ef54833828c3d778d2a1edbb536833880c1a4572a7f5836404e073  -

exec
/bin/zsh -lc "git ls-tree HEAD -- '_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md' '_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md' '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
100644 blob dfe6d5ed5fc9f19e9f488451efef2ec8208aade8	"_bmad-output/\345\256\241\346\237\245/G4-9-DLQ-census-2026-08-28.md"
100644 blob 9ac1beb158804c5deb9d0bc572ea51da730dc709	"_bmad-output/\345\256\241\346\237\245/G4-9-dlq-ledger-2026-08-28.json"
100644 blob 266b415d2f4d21fa647b5a541ed8436bc3a248de	"_bmad-output/\351\252\214\346\224\266\345\215\225/UAT-CARD-G4-9-DLQ\347\234\237\345\256\236\346\214\202\350\275\275census\345\210\206\350\257\212-2026-08-28.md"

**Confirming no re-run needed**
2026-08-28T15:04:31.183063Z ERROR codex_core::tools::router: error=timeout_ms must be at least 10000
collab: Wait
**Checking active agents**
**Planning sequential verification steps**
mcp: sequential-thinking/sequentialthinking started
mcp: sequential-thinking/sequentialthinking (completed)
mcp: sequential-thinking/sequentialthinking started
mcp: sequential-thinking/sequentialthinking (completed)
collab: Wait
**Updating plan status**
已固定提交对象并完成措辞与变更边界双轨审计；正在收束台账独立复算与最终交叉核对。
  ✓ 读取既有审计约束并确认 checkout、提交与审阅对象
  ✓ 并行复核报告/UAT 过强断言与提交变更边界
  → 从绑定证据只读复算台账全部统计量
  • 交叉核对差异并给出三层最终裁定
**Inspecting code lines 198-246 for global assertions**
exec
/bin/zsh -lc "git show '543e8a34:_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md' | nl -ba | sed -n '196,248p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
   196	## §7h Codex round-7 复审整改记录（关键裁定分离 + 架构级第二次修复）
   197	
   198	round-7 给出了本卡最重要的一次裁定分离：
   199	
   200	> **「现有 92 条冻结 ledger 可以采信；CARD-G4-9 生成器与 UAT 的纯只读安全声明不可验收。」**
   201	
   202	即：卡面的 census 判据（分类/对账/三态/挂载真相/稳定键/shasum 不变）已满足且被独立复算确认；阻断项全部落在"生成器作为工具的只读安全承诺"上。逐条整改：
   203	
   204	- **BLOCKER（大小写别名根）**：本机实测 `/Users/Heishing/.claude/projects` 与 `/users/heishing/...` `samefile=True` 但 `realpath` 字符串不同，prefix guard 返回 False——**无需竞态的实际绕过**。我 round-6 用的 `os.path.normcase` 在 POSIX 上是**恒等函数**（假设错误）。**整改**：新增 `_path_is_within()`，从目标逐级向上比较 **inode 身份**，完全不依赖路径字符串；`--out` 与输入文件的比较改 `os.path.samefile`。实测：别名根作 `--out` → exit 2，正例无回归。
   205	- **NOT-CLOSED ×4（根外 hardlink 指向隐藏目录内 transcript / 根 retarget TOCTOU / 检查后换父目录 symlink 或 basename hardlink）+ MEDIUM（非原子写）**：这五项依附于同一个动作——**截断一个已存在的文件**。**架构级修复**：写出改为「同目录 `O_EXCL` 新建临时文件 → 写 → `fsync` → `os.replace` 原子替换」，**全文再无任何 `ftruncate` 调用**。`O_EXCL` 保证写入目标是本进程新建的对象，因此"截断既有对象"这条具体路径消失（三场景各自取证，不声称整类绕过均已失效）；`os.replace` 同时消除崩溃/ENOSPC 留下部分台账的风险。实测：根外 hardlink 指向根内 transcript 作 `--out` → 台账正常写出而**源文件内容完好**（`os.replace` 只重绑定该名字，不触碰底层 inode）。
   206	- **NOT-CLOSED（扫描受阻仅标记不停写）**：扫描受阻 ⇒ 保护集必然不完整。**整改**：`scan_errors`/`stat_failures` 非空时**直接拒绝写出台账**（exit 2），实测不落盘。
   207	- **LOW（lone surrogate 回退失效）**：异常发生在后续 `write`，不在原 `try` 内。**整改**：`json.dumps` 后立即 `.encode("utf-8")` 探测，编码错误在写出前暴露并回退 `ensure_ascii=True`。
   208	- **LOW（receipt 用 8 位缩写）**：如实登记为已知限制（仓库内唯一可解析），未改为 40-hex 以保持 receipt 可读性——列 follow-up。
   209	
   210	round-7 整改后第七次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变、台账 mode 0600、无临时文件残留——七轮整改数字全程未变**。
   211	
   212	## §7i Codex round-8 复审整改记录（裁定分离重申 + 3 BLOCKER 全闭）
   213	
   214	round-8 重申 round-7 的裁定分离，措辞更明确：
   215	
   216	> **可验收：92 条冻结 ledger snapshot。不可验收：当前生成器的一般安全性，以及 UAT 的"纯只读、唯一写出口、整类 TOCTOU 已消失"声明。**
   217	
   218	三条新 BLOCKER 全部属实，逐条整改：
   219	
   220	- **BLOCKER①（SQLite URI 未转义）**：`file:{db_path}?mode=ro` 在路径含 `#` 时，`mode=ro` 会落进被忽略的 URI fragment，SQLite 可能按**默认读写模式**打开——直接反驳"唯一写出口"。
   221	- **BLOCKER②（QA DB 仍按 pathname 打开）**：验证 fd 保持打开也没用，SQLite 另按路径解析，A→B→A 可让 connection 读到 B 而复核看到 A。
   222	- **①②的共同解法**：不再让 SQLite 碰路径——从**已验证的 fd** 读全量字节 → `sqlite3` 内存库 `deserialize()`。URI 转义问题与 ABA **一并消失**，且全程不落任何文件。实测：路径含 `#` 与 `?` 的 DB 正常只读（`read_mode: in_memory_deserialize_from_verified_fd`，16384 bytes）。
   223	- **BLOCKER③（根内末级 symlink）**：POSIX 规定 `rename`/`replace` **不解析末级 symlink**——`--out` 若是根内 symlink 指向根外，`realpath` 判"根外"而放行，但 replace 实际替换的是**根内那个目录项**。**整改**：containment 改用**父目录语义**（`dirname` 在根内即拒），叠加原有末级判定。实测：根内 symlink 作 `--out` → exit 2，symlink 未被替换。
   224	- **HIGH（扫描受阻拒绝不完整）**：no_token/token_conflict 分支在写入 `scan_errors` **之前**就早退；且拒绝条件写作 `scan_blocked and args.out`，**省略 `--out` 走 stdout 即可绕过**。**整改**：早退分支同样记录扫描错误；拒绝条件去掉 `and args.out`。实测：stdout 模式扫描受阻同样 exit 2。
   225	- **MEDIUM（tmp 残留 + 未 fsync 父目录）**：`os.replace` 在 `try` 外，`EXDEV/EBUSY/EACCES/ENOSPC` 会冒泡并留下 tmp。**整改**：replace 纳入 try，异常一律 `unlink` tmp；成功后 `fsync` 父目录使重命名落盘。
   226	
   227	round-8 整改后第八次全量重跑：**92 条、class 89/2/1、byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0、重复簇 6/29、unparseable 0、shasum 不变、无 tmp 残留——八轮整改数字全程未变**。
   228	
   229	## §7j Codex round-9 裁定与收敛（声明改为有界，剩余项显式移交）
   230	
   231	round-9 维持分层裁定并给出"达到可验收的最小剩余项"清单。我的处置分两类：
   232	
   233	**已修（本轮完成）**
   234	
   235	- **必需⑤ 名实不符（DD-13 硬伤）**：改用内存 `deserialize` 后，字段仍叫 `opened_readonly`、docstring 仍称 SQLite URI `mode=ro`——**实际只有源 fd 只读，内存连接可写**。已改字段名为 `source_fd_opened_readonly`，docstring 如实说明只读保证的来源（源 fd 只读 + 内存副本与源解耦），补 `PRAGMA query_only=ON` 作纵深防御，并把 QA DB 的 `source_sha256` 写入台账（与证据包 shasum 一致）。
   236	- **必需④ 无测试引用生成器**：新增 `backend/tests/regression/test_census_dead_letter_readonly_contract.py`，把 8 轮审查中被实测封死的 **19 条**反例全部固化（每条注明对应轮次与 finding；覆盖构成如实标注于文件 docstring）。该测试**当场抓出一个真实回归**：round-7 改用 `os.replace` 发布后不再打开 `--out`，`S_ISREG` 门随之丢失，FIFO 会被静默替换成普通文件——已补回文件类型门（`--out` 若已存在且非常规文件、或是 symlink，一律拒绝）。**20 passed**（round-10 又补强了 4 处虚假通过窗口并新增 1 条 malformed DB 用例）。
   237	
   238	**改为有界声明（不再宣称已解决）**
   239	
   240	round-9 的必需①②③（一致性 SQLite 快照、单一稳定 dirfd 发布、tmp/发布者/状态绑定与单写者锁）是把这个**一次性 census 脚本**升级为**生产级并发安全工具**的要求。本卡不做，理由如实记录：本卡场景为单人本机、目录非共享可写；**"DB 静止"与"无并发写者"是操作者提供的前提，不是本卡证明的结论**（0 行 / 固定字节数 / 前后同 SHA 均不能证明读取期间无写者）。**处置方式是收敛声明而非假装达标**——报告头与验收单已删去"纯只读 / 唯一写出口 / 整类 TOCTOU 已消失"这类绝对化措辞，改为"本次运行输入 shasum 前后不变（已取证）+ 对 20+ 类误用路径 fail-closed（测试固化）+ 不声称敌意环境下的生产级安全"。
   241	
   242	**移交 follow-up（G4-10 复用本脚本前必须补齐）**
   243	
   244	| # | 项 | 触发条件 |
   245	|---|---|---|
   246	| FU-A | SQLite 一致性快照（backup API 或要求外部先冻结 DB）+ 显式拒绝 WAL/journal/并发变化 | DB 非静止时 |
   247	| FU-B | 输出发布全程相对同一 `O_DIRECTORY\|O_NOFOLLOW` dirfd（create/replace/fsync/unlink） | 输出目录可能被他人操纵时 |
   248	| FU-C | 不可预测 tmp 名 + 单写者锁/CAS + `published_but_durability_unconfirmed` 状态 + 崩溃残留 reconciliation | 共享可写目录或并发运行时 |

**Clarifying SQLite ingestion ambiguity**
**Verifying historical remediation accuracy**
collab: Wait
collab: Wait
**Verifying memory citations and rollout IDs**
**Finalizing citation entries and preparing ledger links**
exec
/bin/zsh -lc "rg -n '\"(total_lines|total_records|class_distribution|recoverability_distribution|inline_state_distribution|unparseable_lines|attribution_conflicts|duplicate_clusters|unrecoverable_list|unverifiable_list|records)\"' '_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census
 succeeded in 0ms:
40: "total_lines": 92,
41: "total_records": 92,
42: "unparseable_lines": [],
43: "class_distribution": {
55: "recoverability_distribution": {
61: "inline_state_distribution": {
66: "unrecoverable_list": [],
67: "unverifiable_list": [],
68: "attribution_conflicts": [
85: "duplicate_clusters": [
182: "records": [

**Deciding receipt reference strategy**
**Planning concise evidence linking and verdict**
**Clarifying receipt update as non-blocking caveat**
**Clarifying receipt's non-blocking binding role**
**Confirming review scope on commit 543**
mcp: sequential-thinking/sequentialthinking started
mcp: sequential-thinking/sequentialthinking (completed)
**Completing update plan**
codex
三条独立轨已交叉收束：措辞残留为零；脚本/test/ledger/运行绑定证据 exact bytes 均未变；raw DLQ 与 ledger 的 92 条逐记录复算为 0 mismatch，目标统计全部吻合。后置 receipt 的文本补录是唯一范围注记，不改变任何运行或台账证据。
三条独立审计轨与主审复算一致，已满足终裁条件。
  ✓ 读取既有审计约束并确认 checkout、提交与审阅对象
  ✓ 并行复核报告/UAT 过强断言与提交变更边界
  ✓ 从绑定证据只读复算台账全部统计量
  ✓ 交叉核对差异并给出三层最终裁定
**Finalizing pass status and evidence table**
**Detailing binding and ledger evidence references**
**Verifying no overclaims in reports**
**Clarifying commit chain and document changes**
**Confirming attribution conflict resolution**
**Finalizing acceptance phrase formatting**
**Refining citation line ranges**
codex
最终裁定：三层均为 **PASS**。**CARD-G4-9 可验收**。

| 层 | 裁定 | 复核结果 |
|---|---|---|
| (a) 92 条冻结 ledger | **PASS，可验收** | exact raw DLQ SHA-256 为 `3b37460f…ba590`，与 ledger 绑定一致；逐记录复算 0 mismatch |
| (b) 有界前提下的生成器 | **PASS，可验收** | 脚本、测试及可绑定运行证据 exact bytes 未变，round-12 的有界前提与裁定继续成立 |
| (c) 报告与 UAT 声明 | **PASS，可验收** | 两项过强措辞均已消除；未发现新的非引述性残留 |

措辞 grep 结果：

- [报告第 92 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:92) 已限定为 before/after 终态相同，并明确不证明读取期间零写入或每轮留证。
- [UAT](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:13) 第 13、27、49、136 行均已准确收敛；第 134 行是历史 Codex 裁定引述。
- 其余“零写入、逐次取证、整类失效、所有路径 fail-closed、DB 静止”命中均属于历史裁定、整改记录、否定性边界或操作者前提，不是当前过强结论。

变更边界：

- 脚本 blob：`87266e092777fe45e93dde1dfba6eac197dae527`
- 测试 blob：`541ec8b35e9d1fdadff3348d8a43a8d959e08c7c`
- ledger blob：`9ac1beb158804c5deb9d0bc572ea51da730dc709`
- [可绑定运行证据](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/readonly-contract-tests.txt:5) blob：`a04c0c8fe75ddfbcc68ab0bee5bb57494af8b7cd`

上述对象在 `f4112c2c` 与 `543e8a34` 完全一致。需如实注明：区间经过中间提交 `05c85324`，其仅补录了 `artifact-commit-receipt.txt` 的 provenance 文本；这不是脚本、测试或运行证据重生成。`543e8a34` 自身仅改报告/UAT并新增 round-12 审查文档。

[Ledger](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:40) 独立复算：

- 总数 `92`
- class：`89 / 2 / 1`
- recoverability：`byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0`
- 重复簇：`6 / 29`，规模 `[16,4,3,2,2,2]`
- unparseable：`0`
- attribution_conflict：`3`，恰为第 1–3 行，全部 `no_token`

审阅全程只读；未触碰未跟踪的 round-13 文件。


tokens used
156,142
最终裁定：三层均为 **PASS**。**CARD-G4-9 可验收**。

| 层 | 裁定 | 复核结果 |
|---|---|---|
| (a) 92 条冻结 ledger | **PASS，可验收** | exact raw DLQ SHA-256 为 `3b37460f…ba590`，与 ledger 绑定一致；逐记录复算 0 mismatch |
| (b) 有界前提下的生成器 | **PASS，可验收** | 脚本、测试及可绑定运行证据 exact bytes 未变，round-12 的有界前提与裁定继续成立 |
| (c) 报告与 UAT 声明 | **PASS，可验收** | 两项过强措辞均已消除；未发现新的非引述性残留 |

措辞 grep 结果：

- [报告第 92 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:92) 已限定为 before/after 终态相同，并明确不证明读取期间零写入或每轮留证。
- [UAT](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/验收单/UAT-CARD-G4-9-DLQ真实挂载census分诊-2026-08-28.md:13) 第 13、27、49、136 行均已准确收敛；第 134 行是历史 Codex 裁定引述。
- 其余“零写入、逐次取证、整类失效、所有路径 fail-closed、DB 静止”命中均属于历史裁定、整改记录、否定性边界或操作者前提，不是当前过强结论。

变更边界：

- 脚本 blob：`87266e092777fe45e93dde1dfba6eac197dae527`
- 测试 blob：`541ec8b35e9d1fdadff3348d8a43a8d959e08c7c`
- ledger blob：`9ac1beb158804c5deb9d0bc572ea51da730dc709`
- [可绑定运行证据](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/readonly-contract-tests.txt:5) blob：`a04c0c8fe75ddfbcc68ab0bee5bb57494af8b7cd`

上述对象在 `f4112c2c` 与 `543e8a34` 完全一致。需如实注明：区间经过中间提交 `05c85324`，其仅补录了 `artifact-commit-receipt.txt` 的 provenance 文本；这不是脚本、测试或运行证据重生成。`543e8a34` 自身仅改报告/UAT并新增 round-12 审查文档。

[Ledger](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:40) 独立复算：

- 总数 `92`
- class：`89 / 2 / 1`
- recoverability：`byte_exact 4 / approximate 88 / unverifiable 0 / unrecoverable 0`
- 重复簇：`6 / 29`，规模 `[16,4,3,2,2,2]`
- unparseable：`0`
- attribution_conflict：`3`，恰为第 1–3 行，全部 `no_token`

审阅全程只读；未触碰未跟踪的 round-13 文件。


