Reading additional input from stdin...
OpenAI Codex v0.147.0
--------
workdir: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
model: gpt-5.6-sol
provider: openai
approval: on-request
sandbox: read-only
reasoning effort: ultra
reasoning summaries: auto
session id: 01a03510-72c5-7413-8206-1f8c4f20efea
--------
user
你是独立代码审查者。读 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-08-24-第一批小goal卡-复习闭环.md 的 CARD-A3 节，然后 git diff worktree-feature-obsidian-hybrid-dev...HEAD 审查本改动（当天重学卡刷新）：缓存失效条件是否正确且充分（mtime 门、目录 mtime、扫描起点回拨）、push 去重是否被每小时重扫击穿（skip-done / Bark 同 id）、board_last_recommended tie-break 语义是否被重扫路径污染、schema v3 是否真的零改动只消费、plist 12 档与推送窗口的配合、测试是否真锁定行为、有无引入回归。输出 BLOCKER/HIGH/MEDIUM 分级 finding 清单，没有就写 PASS
**Planning independent code review approach**
**Inspecting available skills and memory references**
codex
我会按独立、只读审计执行：先锁定 CARD-A3 的验收语义与改动边界，再把缓存/重扫语义、推送去重/窗口、schema/plist、测试与回归拆成并行证据链；只报告可复现的 BLOCKER/HIGH/MEDIUM，不改代码。
**Noting missing Graphiti tool and updating plan**
  → 读取 CARD-A3、仓库审查规则与相关历史审计记忆，固定验收标准和改动范围
  • 并行审查缓存/重扫/tie-break 与推送去重/plist/schema 路径
  • 审查测试覆盖并运行最小针对性验证与回归检查
  • 交叉复核证据，输出按 BLOCKER/HIGH/MEDIUM 分级的独立结论
mcp: sequential-thinking/sequentialthinking started
mcp: sequential-thinking/sequentialthinking (completed)
**Searching memory for CARD-A3**
exec
/bin/zsh -lc 'rg -n -i "CARD-A3|当天重学|relearn|goal.card|缓存失效|board_last_recommended|Bark|plist" /Users/Heishing/.codex/memories/MEMORY.md' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 exited 1 in 0ms:
**Inspecting canvas audit memory**
exec
/bin/zsh -lc 'rg -n -i "adversarial audit|独立.*审查|canvas-adversarial|goal-cards|feature-obsidian-hybrid-dev" /Users/Heishing/.codex/memories/MEMORY.md' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
3:applies_to: cwd=/private/tmp/cls-cache-prep-v1/writer (initial cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev); reuse_rule=reuse the verification and fail-closed method for a newly authorized candidate only; never amend, rename, delete, rebuild, or retry the represented candidate/temp bundle without explicit recovery authority.
9:- rollout_summaries/2026-08-23T07-46-17-9G79-cache_prep_v1_candidate_frozen_publication_blocked.md (cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev, rollout_path=/Users/Heishing/.codex/sessions/2026/08/23/rollout-2026-08-23T15-46-17-01a02d95-a6b8-7cf3-b775-6b8afa4464db.jsonl, updated_at=2026-08-24T00:53:10+00:00, thread_id=01a02d95-a6b8-7cf3-b775-6b8afa4464db, outcome=partial; frozen local candidate, BLOCKED publication)
108:applies_to: cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output; reuse_rule=reuse the audit method and source handles for the same project family, but revalidate findings, SHA, CI, and live Neo4j state in the target checkout.
114:- rollout_summaries/2026-08-17T01-56-07-ZNCd-agents_guide_and_p1_05c_adversarial_audit.md (cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output, rollout_path=/Users/Heishing/.codex/sessions/2026/08/17/rollout-2026-08-17T09-56-07-01a00d6e-ea40-70a1-a23c-d51342eeeacd.jsonl, updated_at=2026-08-19T17:56:56+00:00, thread_id=01a00d6e-ea40-70a1-a23c-d51342eeeacd, outcome=partial; final read-only verdict)
120:## Task 2: P1-05b five-question adversarial audit, reproducible bypasses
124:- rollout_summaries/2026-08-19T14-44-08-upza-p1_05b_adversarial_review_finds_admission_quarantine_snapsho.md (cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output, rollout_path=/Users/Heishing/.codex/sessions/2026/08/19/rollout-2026-08-19T22-44-08-01a01a7a-c47f-70e2-8e5e-524e1591da78.jsonl, updated_at=2026-08-19T15:12:50+00:00, thread_id=01a01a7a-c47f-70e2-8e5e-524e1591da78, outcome=partial; detailed counterexamples, final report unfinished)
138:- Related skill: skills/canvas-adversarial-audit/SKILL.md. [Task 1][Task 2]
151:applies_to: cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output; reuse_rule=recheck repository layout and existing AGENTS.md in the target checkout before reusing commands or architecture claims.
157:- rollout_summaries/2026-08-17T01-56-07-ZNCd-agents_guide_and_p1_05c_adversarial_audit.md (cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output, rollout_path=/Users/Heishing/.codex/sessions/2026/08/17/rollout-2026-08-17T09-56-07-01a00d6e-ea40-70a1-a23c-d51342eeeacd.jsonl, updated_at=2026-08-19T17:56:56+00:00, thread_id=01a00d6e-ea40-70a1-a23c-d51342eeeacd, outcome=success)

**Inspecting skill usage in audit method**
codex
我在复用该项目既有的 Canvas 对抗审计规程来约束证据格式（独立复算、真实入口、file:line、失败即闭合），但会在当前 checkout 重新验证，绝不沿用旧结论。仓库要求的 Graphiti MCP 本轮未暴露，已记录为验证限制；本地代码审查继续。
exec
/bin/zsh -lc "sed -n '108,142p' /Users/Heishing/.codex/memories/MEMORY.md && sed -n '1,260p' /Users/Heishing/.codex/memories/skills/canvas-adversarial-audit/SKILL.md" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
applies_to: cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output; reuse_rule=reuse the audit method and source handles for the same project family, but revalidate findings, SHA, CI, and live Neo4j state in the target checkout.

## Task 1: P1-05c/P1-01/P1-08 parallel adversarial review, closure rejected

### rollout_summary_files

- rollout_summaries/2026-08-17T01-56-07-ZNCd-agents_guide_and_p1_05c_adversarial_audit.md (cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output, rollout_path=/Users/Heishing/.codex/sessions/2026/08/17/rollout-2026-08-17T09-56-07-01a00d6e-ea40-70a1-a23c-d51342eeeacd.jsonl, updated_at=2026-08-19T17:56:56+00:00, thread_id=01a00d6e-ea40-70a1-a23c-d51342eeeacd, outcome=partial; final read-only verdict)

### keywords

- P1-05c, P1-05, P1-01, P1-08, DD-03, check_vault_path, vault_index_orchestrator, LanceDB, Graphiti, DEFAULT_GROUP_ID, SnapshotV3, CURRENT_TASK.md, Dependency Audit, 32280954498

## Task 2: P1-05b five-question adversarial audit, reproducible bypasses

### rollout_summary_files

- rollout_summaries/2026-08-19T14-44-08-upza-p1_05b_adversarial_review_finds_admission_quarantine_snapsho.md (cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output, rollout_path=/Users/Heishing/.codex/sessions/2026/08/19/rollout-2026-08-19T22-44-08-01a01a7a-c47f-70e2-8e5e-524e1591da78.jsonl, updated_at=2026-08-19T15:12:50+00:00, thread_id=01a01a7a-c47f-70e2-8e5e-524e1591da78, outcome=partial; detailed counterexamples, final report unfinished)

### keywords

- P1-05b, hostile-env, symlink_escape, casefold, vault_backfill, lancedb_client, quarantine__p105b, get_by_node_uuid, node_name_and_summary, pick_eligible, manifest-v3, NaN, CURRENT_TASK

## User preferences

- When requesting an audit, the user asked: “启动并行 agent 进行对抗性审查” -> decompose independent evidence tracks, cross-check high-severity findings, and do not treat green tests as closure. [Task 1][Task 2]
- Require code rather than documentation evidence: each finding needs `file:line`, reproducible input/state → path → result chain, severity, conflict explanation, PASS/PARTIAL/FAIL, and stated limits. [Task 2]
- Respect task-book boundaries: read-only work, WT/MAIN labels, explicit `UNVERIFIABLE`, no raw-vault access, and structured delivery; do not fix product code during audit. [Task 1]

## Reusable knowledge

- Related skill: skills/canvas-adversarial-audit/SKILL.md. [Task 1][Task 2]
- Latest represented verdict: P1-05/P1-01/P1-08 were STILL-OPEN; F-02 tombstone filtering and F-05 live resilience were closed. Audit actual entrypoints: rejected vault paths must cause zero open/hash/index/write. [Task 1][Task 2]
- Reproduced: `vault/raw/escape.md -> /outside/secret.md` was counted by `backfill_vault(..., execute=False)`; case-sensitive `fnmatch` admitted `.CLAUDE/SKILL.md` and `raw/claude.md`. Graphiti edge filtering alone was insufficient because exact readers/node search could cross groups. [Task 1][Task 2]
- SnapshotV3 needs same-generation invalid/future-version self-healing, extra-field, strict-type, huge finite mastery, and identity/length collision coverage. Regenerate `CURRENT_TASK.md` from HEAD, Actions, and actual open items; targeted Python success was not whole-CI success. [Task 1]

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

**Locating CARD-A3 section in feature worktree**
**Planning parallel commands for file and git inspection**
exec
/bin/zsh -lc 'rg -n -C 4 "CARD-A3|当天重学卡|重学卡刷新" "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-08-24-第一批小goal卡-复习闭环.md"' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
20-| 卡 | 一句话说明 | 修完你能感觉到什么 | 预计 |
21-|---|---|---|---|
22-| **A1 新概念排程静默失效** | 每个**新**概念的智能排程（FSRS）其实从来没生效过——底层库返回空值，代码一碰就崩，然后悄悄退回最笨的固定间隔法，你完全看不出来 | 新学的概念开始按记忆科学排复习间隔，而不是死板的固定天数 | 约 5 小时 |
23-| **A2 到期数字打架** | Dashboard 说今天到期 13 个，每日推荐说 6 个——实测确认两边用了两套完全不同的算法（连"哪些节点算数"都不一致） | 所有地方显示同一个数字，并且能看到"8 个还没剖析的节点"单独列出来，不再糊在一起 | 约 5 小时 |
24:| **A3 当天重学卡消失** | 答错的卡本该 1/10 分钟后重新出现，但系统每天早上 9:05 只算一次、缓存一整天——答错的卡要等到**第二天**才回来 | 答错的卡当天就会重新出现在复习清单里（每小时刷新一次） | 约 5 小时 |
25-| **B1 质量门红灯** | 自动检查发现 5 个图像库安全漏洞挡住了质量门；根因是一个**从来没人用过**的视频处理依赖把图像库锁在了旧版本 | 质量门变绿，以后每次改动都有真实的自动把关 | 约 3 小时 |
26-| **E0 夜间车道准备** | 修一个卡住自动测试的孤儿文件 + 写好夜间运行手册（Codex 审查环境已确认就绪，不用装任何东西） | 夜间自动推进的前提条件齐了 | 约 2.5 小时 |
27-
28-### 并行安排（三条车道）
29-
30-```
31:车道 1（串行链）:  A2 到期数字打架  →  A3 当天重学卡    ← A3 要用 A2 定好的数据格式，必须排队
32-车道 2（独立）:    A1 新概念排程                        ← 和谁都不冲突，可同时跑
33-车道 3（独立）:    B1 质量门 + E0 夜间准备               ← 和谁都不冲突，可同时跑
34-```
35-
--
82-- **完成判据（机械)**: parity 测试覆盖全部 5 类分歧节点，断言 due_nodes 明细==期望集合、数字与明细自洽、schema_version==3；`grep -c "schedCnt\|newCnt" canvas-vault/Dashboard.md` == 0 且 `grep -c "今日复习.json"` ≥1；live 冒烟两处数字一致。
83-- **风险**: schema v3 必须纯加性（daily_review_run.py 推送链消费同一 JSON，改坏=Bark 推送断）；Dashboard.md 双副本必须同步部署（memory 已有 worktree vault 陈旧副本教训）；dv.io.load 失败需降级文案；**产品语义决策点见上方"拍板 1"**。
84-- **并行**: 与 A1/B1/E0 并行安全；**与 A3 在 daily_review_pick.py + 回归测试文件上有真实冲突 → A2 先行（schema owner），A3 串行其后只消费不改 schema**。
85-
86:### CARD-A3: 当天重学卡刷新（串行于 A2 之后）
87-
88-- **确认状态**: CONFIRMED（launchd plist 全天仅 9:05 一档；`daily_review_run.py:85-112 ensure_payload` 同日 sha 匹配即复用，现网日志实证 `generate:cached push:skip-done`；quiz-answer 写侧全链 grep 零失效触发点；fsrs 6.3.1 实测 learning_steps=(60s,600s) 全落当天）
89-- **方案**: ①ensure_payload 缓存条件放宽——当天已生成后，若 `节点/*.md` 最大 mtime > payload mtime 则重扫（push 去重由 last_push_accepted_date 天然保证）；②plist StartCalendarInterval 改数组 9:05–21:00 每小时一档（重扫必须周期性——只做写侧一次性触发的话，due=now+1min 的卡在重生成瞬间仍未到期，缺陷只是位移）。
90-- **改动文件**: `scripts/daily_review_run.py`、`scripts/launchd/com.canvas.daily-review.plist`、新增 `backend/tests/regression/test_daily_review_run.py`；部署侧 `~/Library/LaunchAgents/` 重装（**破坏性操作，动手前单独向用户确认**）
--
183-
184-**A3（车道 1 第二棒，A2 合并进 worktree-feature-obsidian-hybrid-dev 后才创建 worktree 开工）：**
185-
186-```
187:/goal 完成 CARD-A3：当天重学卡刷新。必读卡片档案：/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-08-24-第一批小goal卡-复习闭环.md 的 CARD-A3 节。前置检查：git merge-base --is-ancestor 确认 A2 的 commit 已在本分支，schema_version==3 已存在，否则 STOP 并报告。完成条件（AND）：
188-(1) scripts/daily_review_run.py 的 ensure_payload：当天已生成后，若 节点/*.md 最大 mtime > payload mtime 则重扫；重扫路径不更新 board_last_recommended（防污染 tie-break）；只消费 A2 的 schema v3，不改 schema。
189-(2) scripts/launchd/com.canvas.daily-review.plist：StartCalendarInterval 改数组，9:05 起至 21:00 每小时一档；plutil -lint 通过。只改仓库副本——~/Library/LaunchAgents/ 的重装属破坏性部署，写入验收单"待用户确认"一节，你不执行。
190-(3) 新增 backend/tests/regression/test_daily_review_run.py 三场景（节点变动→"new"且含该节点 / 无变动→"cached" / 重扫后 push 仍 skip-done），先红后绿；只 assert dict 不 assert md 文本。
191-(4) 裁判命令：cd backend && .venv/bin/pytest tests/regression/test_daily_review_run.py tests/regression/test_daily_review_pick.py -q 全绿；grep -c "<key>Hour</key>" scripts/launchd/com.canvas.daily-review.plist ≥2。
192:(5) Codex 交叉审查（同 A1 模式，换成 CARD-A3，重点审：缓存失效条件、push 去重、tie-break 语义）存 _bmad-output/审查/codex-review-CARD-A3.md，处理完 BLOCKER/HIGH。
193:(6) 小白验收单 ship（含 launchd 重装待确认节）。(7) git commit 含 "BATCH-2026-08-24-复习闭环 / CARD-A3"；不 push。
194-硬边界：不改 daily_review_pick.py 的 due 判定与 schema（A2 已定）；不碰 fsrs_bridge.py；不执行 launchctl。
195-```
196-
197-### 3.4 每张卡的生命周期（统一）

exec
/bin/zsh -lc "rg --files -g 'AGENTS.md' -g 'CURRENT_TASK.md' -g '.claude/rules/*.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
_decisions/CURRENT_TASK.md
CURRENT_TASK.md

exec
/bin/zsh -lc 'git status --short --branch' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
exec
/bin/zsh -lc 'git diff --stat worktree-feature-obsidian-hybrid-dev...HEAD && git diff --name-status worktree-feature-obsidian-hybrid-dev...HEAD' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
## card/a3-relearn
?? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-A3.md"
?? backups/
?? "canvas-vault/outputs/\344\273\212\346\227\245\345\244\215\344\271\240.json"
?? "canvas-vault/outputs/\344\273\212\346\227\245\345\244\215\344\271\240.md"

 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
 backend/tests/regression/test_daily_review_run.py | 235 ++++++++++++++++++++++
 scripts/daily_review_run.py                       |  45 ++++-
 scripts/launchd/com.canvas.daily-review.plist     |  83 +++++++-
 3 files changed, 353 insertions(+), 10 deletions(-)
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
A	backend/tests/regression/test_daily_review_run.py
M	scripts/daily_review_run.py
M	scripts/launchd/com.canvas.daily-review.plist

exec
/bin/zsh -lc 'git merge-base worktree-feature-obsidian-hybrid-dev HEAD && git rev-parse HEAD && git rev-parse worktree-feature-obsidian-hybrid-dev && git log --oneline --decorate --no-merges worktree-feature-obsidian-hybrid-dev..HEAD' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
f6a426b35d7324f73caf147018ab200770987b17
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
346448b7e7af5a49c2278e8e7e5bcd6c41c60390
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
f6a426b35d7324f73caf147018ab200770987b17
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
346448b7 (HEAD -> card/a3-relearn) fix(review): same-day relearn card refresh via mtime cache invalidation

**Reviewing CARD A3 section lines 86-110**
**Planning agent tasks and spawning**
**Preparing CARD section and diffs**
exec
/bin/zsh -lc "nl -ba \"/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-08-24-第一批小goal卡-复习闭环.md\" | sed -n '86,105p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
    86	### CARD-A3: 当天重学卡刷新（串行于 A2 之后）
    87	
    88	- **确认状态**: CONFIRMED（launchd plist 全天仅 9:05 一档；`daily_review_run.py:85-112 ensure_payload` 同日 sha 匹配即复用，现网日志实证 `generate:cached push:skip-done`；quiz-answer 写侧全链 grep 零失效触发点；fsrs 6.3.1 实测 learning_steps=(60s,600s) 全落当天）
    89	- **方案**: ①ensure_payload 缓存条件放宽——当天已生成后，若 `节点/*.md` 最大 mtime > payload mtime 则重扫（push 去重由 last_push_accepted_date 天然保证）；②plist StartCalendarInterval 改数组 9:05–21:00 每小时一档（重扫必须周期性——只做写侧一次性触发的话，due=now+1min 的卡在重生成瞬间仍未到期，缺陷只是位移）。
    90	- **改动文件**: `scripts/daily_review_run.py`、`scripts/launchd/com.canvas.daily-review.plist`、新增 `backend/tests/regression/test_daily_review_run.py`；部署侧 `~/Library/LaunchAgents/` 重装（**破坏性操作，动手前单独向用户确认**）
    91	- **完成判据（机械）**: 三场景测试（节点变动后 ensure_payload 返回 "new" 且含该节点 / 无变动仍 "cached" / 重扫后 push 仍 skip-done）+ `plutil -lint` 通过 + plist Hour 键 ≥2 档。测试只 assert dict 不 assert md 文本（与 A2 解耦）。
    92	- **风险**: board_last_recommended 只在首次生成时更新（重扫路径不写，防污染 tie-break 语义）；每小时触发放大 wrapper 双副本 preflight 的暴露频率（是暴露不是引入）；Bark 通知同 id 覆盖靠 skip-done 门守住（场景 3 锁死）。
    93	- **并行**: 依赖 A2 的 schema v3 先落地；与 A1/B1/E0 零交集。
    94	
    95	### CARD-B1: CI Dependency Audit 修复（方案 A 已预验证）
    96	
    97	- **确认状态**: CONFIRMED（gh run 32288541098 实查 + 本地 pip-audit 2.10.0 逐字复现：5 个 pillow 11.3.0 CVE，Fix=12.3.0，均不在 13 条豁免内）
    98	- **根因链**: `requirements.txt:158 moviepy>=1.0.3` 钉死 `pillow<12.0`；moviepy 是**零调用方死管道**（唯一 import 在 video_processor.py:26，try/except 守护，全仓无外部调用方）；pillow 真实调用面是 multimodal 缩略图链（`multimodal_service.py:300-311` 等），必须保留并升级。
    99	- **方案 A（已在 scratchpad 预验证 0 finding）**: requirements.txt 删 moviepy + 显式加 `pillow>=12.3.0`；test.yml 删全部 13 条 --ignore-vuln（满足"不能只扩大 ignore 清单"，且正好执行豁免注释 L180 自己写的复查条款）；豁免注释块改写为决策记录而非裸删。
   100	- **完成判据（机械）**: ①本地 `pip-audit -r backend/requirements.txt`（零豁免参数）输出 `No known vulnerabilities found`；②重装 venv 后 CI 白名单 14 测试文件 + test_multimodal_fixes.py 0 fail（验证 pillow 11→12 无 API 断裂；若 `Image.LANCZOS` 别名被移除则改 `Image.Resampling.LANCZOS`）；③push 后该 commit 的 run 四 job 全 ✓。
   101	- **风险**: 移除 moviepy 后视频管道从"装了没人用"变"未装"（graceful degradation 已在位，known-gotchas.md 记一条）；删光豁免后 audit 变全裸门，未来无关新 CVE 会再红（这是该门设计意图）。
   102	- **并行**: 与所有卡零交集，完全并行。push 动作放白天由用户知情时执行，夜间车道不 push。
   103	
   104	### CARD-E0: 夜间车道准备（环境盘点已完成大半）
   105	

exec
/bin/zsh -lc 'git diff --find-renames --find-copies --unified=100 worktree-feature-obsidian-hybrid-dev...HEAD -- scripts/daily_review_run.py scripts/launchd/com.canvas.daily-review.plist' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
diff --git a/scripts/daily_review_run.py b/scripts/daily_review_run.py
index 4dc943cc..86365f81 100755
--- a/scripts/daily_review_run.py
+++ b/scripts/daily_review_run.py
@@ -1,186 +1,223 @@
 #!/usr/bin/env python3
 """每日复习推送编排 runner (DAILY-REVIEW-PUSH-2026-07-29, 终审 A4/A7 硬化版)。
 
 顺序铁律: md/json 先落盘(保底) → 窗口内 Bark → 失败 osascript 兜底。
 壳层 daily-review-push.sh 只负责 mkdir 锁 + 固定解释器; 业务全在此处
 (可 --now 注入时间跑 12 场景验收矩阵)。
 
 终审修正落点:
   A4: 时间门 9:05 ≤ 本地时间 < 21:00 (RunAtLoad 早触发只生成不推;
       唤醒补跑窗口内补推; 过窗只落盘) · state JSON 原子写 (os.replace)
       · last_push_accepted_date 命名 (HTTP 成功仅证明服务端接受)
   A7: payload 持久化 今日复习.json (生成成功推送失败 → 补跑只补推送)
       · osascript 走 argv (板名注入免疫) · 损坏 state 隔离重建不炸
 """
 
 from __future__ import annotations
 
 import argparse
 import hashlib
 import json
 import os
 import subprocess
 import sys
+import time
 from datetime import datetime, time as dtime, timezone
 from pathlib import Path
 
 sys.path.insert(0, str(Path(__file__).resolve().parent))
 import send_bark  # noqa: E402
 
 REPO = Path(os.environ.get("CANVAS_REPO", "/Users/Heishing/Desktop/canvas/canvas-learning-system"))
 # VAULT-SYNC (2026-08-02): 默认值仅作兜底 — 生产链由 wrapper 从 .env
 # ACTIVE_VAULT 解析后经 --vault 传入, 与后端同源 (换 vault 只改 .env 一处)
 VAULT = REPO / "canvas-vault"
 STATE = REPO / "backups" / "daily-review.state.json"
 LOG = REPO / "backups" / "daily-review.log"
 
 PUSH_WINDOW = (dtime(9, 5), dtime(21, 0))
 
 APPLESCRIPT = (
     "on run argv\n"
     "    display notification (item 2 of argv) with title (item 1 of argv)\n"
     "end run\n"
 )
 
 
 def _now(arg: str | None) -> datetime:
     if arg:
         dt = datetime.fromisoformat(arg.replace("Z", "+00:00"))
         return dt if dt.tzinfo else dt.astimezone()
     return datetime.now(timezone.utc)
 
 
 def load_state() -> dict:
     if not STATE.exists():
         return {"schema_version": 1, "board_last_recommended": {}}
     try:
         st = json.loads(STATE.read_text(encoding="utf-8"))
         st.setdefault("board_last_recommended", {})
         return st
     except (json.JSONDecodeError, OSError):
         quarantine = STATE.with_name(
             STATE.name + ".corrupt-" + datetime.now().strftime("%Y%m%dT%H%M%S"))
         try:
             os.replace(STATE, quarantine)
         except OSError:
             pass
         print(f"[runner] state 损坏, 已隔离到 {quarantine.name}, 重建", file=sys.stderr)
         return {"schema_version": 1, "board_last_recommended": {}}
 
 
 def save_state(st: dict):
     STATE.parent.mkdir(parents=True, exist_ok=True)
     tmp = STATE.with_suffix(".tmp")
     tmp.write_text(json.dumps(st, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
     os.replace(tmp, STATE)
 
 
 def log_line(msg: str):
     LOG.parent.mkdir(parents=True, exist_ok=True)
     stamp = datetime.now().astimezone().strftime("%F %T")
     with open(LOG, "a", encoding="utf-8") as f:
         f.write(f"[{stamp}] {msg}\n")
 
 
+def _nodes_max_mtime(vault: Path) -> float:
+    """节点池最新改动时间 (CARD-A3 缓存失效判据)。
+
+    文件 mtime 抓原地更新 (quiz 写 fsrs_due 不动目录), 目录 mtime 抓
+    增删改名 (不留文件 mtime); 误报代价只是一次幂等重扫。保 mtime 的
+    还原类操作 (rsync -a / Time Machine) 不在本判据覆盖面内。
+    """
+    pool = vault / "节点"
+    latest = 0.0
+    for p in pool.glob("*.md"):
+        try:
+            latest = max(latest, p.stat().st_mtime)
+        except OSError:
+            continue  # 迭代间隙被删: 殿后的目录 stat 捕获该变动
+    try:
+        # 目录 stat 殿后取样 — 迭代期间发生的删除也已反映在目录 mtime 里
+        latest = max(latest, pool.stat().st_mtime)
+    except OSError:
+        return 0.0  # 节点池不存在: 不因 mtime 失效, 保持旧缓存语义
+    return latest
+
+
 def ensure_payload(st: dict, now: datetime, today: str) -> tuple[dict | None, str]:
-    """当日 payload: 没有才生成 (生成过则复用 — 补跑只补推送)。"""
+    """当日 payload: 没有才生成 (生成过则复用 — 补跑只补推送)。
+
+    CARD-A3 (BATCH-2026-08-24-复习闭环): 复用多一道门 — 节点池比 payload
+    新 (quiz 写侧刚更新 fsrs_due / 新增重学卡) 则同日重扫, 否则当天到期的
+    重学卡永远进不了投影。push 去重不在此处: last_push_accepted_date 天然
+    保证同日只推一次。
+    """
     payload_path = VAULT / "outputs" / "今日复习.json"
-    if st.get("last_generate_date") == today and payload_path.exists():
+    first_gen_today = st.get("last_generate_date") != today
+    if not first_gen_today and payload_path.exists():
         try:
             raw = payload_path.read_text(encoding="utf-8")
             # sha 校验 (Code-Review L3): 外部改动/半写的 payload 不复用, 重新生成
             if hashlib.sha256(raw.encode("utf-8")).hexdigest() == st.get("payload_sha256"):
-                return json.loads(raw), "cached"
+                if _nodes_max_mtime(VAULT) <= payload_path.stat().st_mtime:
+                    return json.loads(raw), "cached"
         except (json.JSONDecodeError, OSError):
             pass  # 落盘 payload 损坏 → 重新生成
 
     import daily_review_pick as picker
 
+    scan_started = time.time()
     payload, ranked = picker.build_payload(
         VAULT, now, st["board_last_recommended"], picker.load_decay(VAULT))
     out = VAULT / "outputs"
     out.mkdir(parents=True, exist_ok=True)
     picker.atomic_write(out / "今日复习.md", picker.render_md(payload, ranked))
     raw = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
     picker.atomic_write(payload_path, raw)
+    # mtime 门基准回拨到扫描起点: 扫描-落盘窗口内落地的写侧更新, 其 mtime
+    # 必然 > 基准, 下一轮触发重扫捞回 (否则该更新当天静默丢失, 无日志可查)
+    os.utime(payload_path, (scan_started, scan_started))
 
     st["last_generate_date"] = today
     st["payload_sha256"] = hashlib.sha256(raw.encode("utf-8")).hexdigest()
-    if ranked:
+    if ranked and first_gen_today:
+        # CARD-A3: 重扫路径不写 — tie-break 的「上次被推荐日期」是天级轮转
+        # 语义, 重扫换榜也补写会把第二个板标成「今天推荐过」, 污染后续排序
         st["board_last_recommended"][ranked[0]["board"]] = today
     save_state(st)
     return payload, "new"
 
 
 def osascript_fallback(noti: dict) -> bool:
     try:
         r = subprocess.run(
             ["/usr/bin/osascript", "-", noti["title"], noti["body"]],
             input=APPLESCRIPT, text=True, capture_output=True, timeout=15,
         )
         return r.returncode == 0
     except (OSError, subprocess.TimeoutExpired):
         return False
 
 
 def main() -> int:
     global VAULT
     ap = argparse.ArgumentParser(description="每日复习推送编排")
     ap.add_argument("--now", help="ISO 时间覆盖 (12 场景验收矩阵用)")
     ap.add_argument("--vault", help="活 vault 路径 (wrapper 从 .env ACTIVE_VAULT 解析传入; 缺省回退 canvas-vault)")
     args = ap.parse_args()
 
     if args.vault:
         VAULT = Path(args.vault)
 
     now = _now(args.now)
     local = now.astimezone()
     today = local.date().isoformat()
     st = load_state()
 
     try:
         payload, gen = ensure_payload(st, now, today)
     except Exception as e:  # 生成失败 = 无保底, 唯一的非 0 退出
         log_line(f"generate:FAILED err={type(e).__name__}:{str(e)[:120]}")
         print(f"[runner] 生成失败: {e}", file=sys.stderr)
         return 1
 
     noti = (payload or {}).get("notification")
     push, fallback = "-", "-"
     if not noti:
         push = "skip-empty"  # 无板可推 (全占位/空 vault): md 已如实落盘
     elif st.get("last_push_accepted_date") == today:
         push = "skip-done"
     elif not (PUSH_WINDOW[0] <= local.time() < PUSH_WINDOW[1]):
         push = "skip-window"  # RunAtLoad 早触发 / 21:00 后唤醒: 只落盘
     else:
         rc = send_bark.send(noti)
         if rc == 0:
             st["last_push_accepted_date"] = today
             st["last_result"], st["last_error"] = "pushed", ""
             save_state(st)
             push = "accepted"
         else:
             push = "skip-nokey" if rc == 2 else "failed"
             if rc != 2:
                 st["last_result"] = "generated_push_failed"
                 st["last_error"] = "bark-send"
             # 本地兜底每日一次 (Code-Review L1 去重门); 无 key 也提醒一条
             # (Code-Review H1: key 配好前不能一切静默)
             if st.get("last_local_notify_date") != today:
                 local_noti = noti if rc != 2 else {
                     "title": "📚 今日复习已生成",
                     "body": noti["body"] + "（Bark 未配置，仅本地提醒）",
                 }
                 fallback = "ok" if osascript_fallback(local_noti) else "fail"
                 if fallback == "ok":
                     st["last_local_notify_date"] = today
             save_state(st)
 
     log_line(f"generate:{gen} push:{push} fallback:{fallback}")
     print(f"[runner] generate:{gen} push:{push} fallback:{fallback}")
     return 0
 
 
 if __name__ == "__main__":
     sys.exit(main())
diff --git a/scripts/launchd/com.canvas.daily-review.plist b/scripts/launchd/com.canvas.daily-review.plist
index 75913deb..c34fe0b0 100644
--- a/scripts/launchd/com.canvas.daily-review.plist
+++ b/scripts/launchd/com.canvas.daily-review.plist
@@ -1,31 +1,102 @@
 <?xml version="1.0" encoding="UTF-8"?>
 <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
 <plist version="1.0">
 <dict>
 	<key>EnvironmentVariables</key>
 	<dict>
 		<key>PATH</key>
 		<string>/usr/bin:/bin:/usr/sbin:/sbin</string>
 	</dict>
 	<key>Label</key>
 	<string>com.canvas.daily-review</string>
 	<key>ProgramArguments</key>
 	<array>
 		<string>/bin/bash</string>
 		<string>/Users/Heishing/Library/Application Support/CanvasReview/bin/daily-review-wrapper.sh</string>
 	</array>
 	<key>RunAtLoad</key>
 	<true/>
 	<key>StandardErrorPath</key>
 	<string>/Users/Heishing/Library/Logs/canvas-daily-review.err.log</string>
 	<key>StandardOutPath</key>
 	<string>/Users/Heishing/Library/Logs/canvas-daily-review.log</string>
+	<!-- CARD-A3: 每小时一档 9:05-20:05, 全部落在推送窗 [9:05,21:00) 内。
+	     每小时触发是为了重扫当天新到期的重学卡 (ensure_payload mtime 门),
+	     同日重复推送由 last_push_accepted_date 去重 (skip-done)。 -->
 	<key>StartCalendarInterval</key>
-	<dict>
-		<key>Hour</key>
-		<integer>9</integer>
-		<key>Minute</key>
-		<integer>5</integer>
-	</dict>
+	<array>
+		<dict>
+			<key>Hour</key>
+			<integer>9</integer>
+			<key>Minute</key>
+			<integer>5</integer>
+		</dict>
+		<dict>
+			<key>Hour</key>
+			<integer>10</integer>
+			<key>Minute</key>
+			<integer>5</integer>
+		</dict>
+		<dict>
+			<key>Hour</key>
+			<integer>11</integer>
+			<key>Minute</key>
+			<integer>5</integer>
+		</dict>
+		<dict>
+			<key>Hour</key>
+			<integer>12</integer>
+			<key>Minute</key>
+			<integer>5</integer>
+		</dict>
+		<dict>
+			<key>Hour</key>
+			<integer>13</integer>
+			<key>Minute</key>
+			<integer>5</integer>
+		</dict>
+		<dict>
+			<key>Hour</key>
+			<integer>14</integer>
+			<key>Minute</key>
+			<integer>5</integer>
+		</dict>
+		<dict>
+			<key>Hour</key>
+			<integer>15</integer>
+			<key>Minute</key>
+			<integer>5</integer>
+		</dict>
+		<dict>
+			<key>Hour</key>
+			<integer>16</integer>
+			<key>Minute</key>
+			<integer>5</integer>
+		</dict>
+		<dict>
+			<key>Hour</key>
+			<integer>17</integer>
+			<key>Minute</key>
+			<integer>5</integer>
+		</dict>
+		<dict>
+			<key>Hour</key>
+			<integer>18</integer>
+			<key>Minute</key>
+			<integer>5</integer>
+		</dict>
+		<dict>
+			<key>Hour</key>
+			<integer>19</integer>
+			<key>Minute</key>
+			<integer>5</integer>
+		</dict>
+		<dict>
+			<key>Hour</key>
+			<integer>20</integer>
+			<key>Minute</key>
+			<integer>5</integer>
+		</dict>
+	</array>
 </dict>
 </plist>

exec
/bin/zsh -lc 'git diff --find-renames --find-copies --unified=80 worktree-feature-obsidian-hybrid-dev...HEAD -- backend/tests/regression/test_daily_review_run.py' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
diff --git a/backend/tests/regression/test_daily_review_run.py b/backend/tests/regression/test_daily_review_run.py
new file mode 100644
index 00000000..48413518
--- /dev/null
+++ b/backend/tests/regression/test_daily_review_run.py
@@ -0,0 +1,235 @@
+"""daily_review_run 当天重学卡刷新 (CARD-A3, BATCH-2026-08-24-复习闭环)。
+
+ensure_payload 缓存失效三场景锁定: 当天已生成后, 节点池比 payload 新
+(quiz 写侧刚更新 fsrs_due / 新增节点) 必须重扫; 无变动仍复用; 重扫后
+同日推送去重 (skip-done) 与 tie-break 语义 (board_last_recommended
+只在首次生成时写) 不被破坏。
+
+只 assert dict / 状态 / runner 状态行, 不 assert 今日复习.md 渲染文本
+(与 A2 渲染层解耦)。mtime 全部 os.utime 显式钉死, 不依赖墙钟顺序。
+"""
+
+import os
+import shutil
+import sys
+from datetime import datetime, timezone
+from pathlib import Path
+
+WT = Path(__file__).resolve().parents[3]
+sys.path.insert(0, str(WT / "scripts"))
+
+import daily_review_run as runner  # noqa: E402
+
+NOW = datetime(2026, 7, 30, 2, 0, tzinfo=timezone.utc)
+TODAY = "2026-07-30"
+BASE = 1_700_000_000  # 人工 mtime 基准: 只比大小, 绝对值无意义
+
+
+def _node(board="普通板", extra=""):
+    return f'---\ntype: concept\nsource_board: "[[原白板/{board}]]"\n{extra}---\n真实内容。\n'
+
+
+def _vault(tmp_path, nodes: dict) -> Path:
+    vault = tmp_path / "vault"
+    scripts = vault / ".claude" / "scripts"
+    scripts.mkdir(parents=True)
+    (vault / "节点").mkdir()
+    shutil.copy(WT / "canvas-vault" / ".claude" / "scripts" / "decay_beta.py", scripts)
+    for name, content in nodes.items():
+        (vault / "节点" / f"{name}.md").write_text(content, encoding="utf-8")
+    return vault
+
+
+def _patch_runner(monkeypatch, vault, tmp_path):
+    monkeypatch.setattr(runner, "VAULT", vault)
+    monkeypatch.setattr(runner, "STATE", tmp_path / "backups" / "daily-review.state.json")
+    monkeypatch.setattr(runner, "LOG", tmp_path / "backups" / "daily-review.log")
+
+
+def _set_mtime(path: Path, ts: float):
+    os.utime(path, (ts, ts))
+
+
+def _pin_pool_older_than_payload(vault: Path, payload_ts: float):
+    """把 节点/ 目录与现有节点文件全部钉到 payload 之前 (无变动基线)。"""
+    for p in (vault / "节点").glob("*.md"):
+        _set_mtime(p, payload_ts - 100)
+    _set_mtime(vault / "节点", payload_ts - 100)
+    _set_mtime(vault / "outputs" / "今日复习.json", payload_ts)
+
+
+# ── 场景 1: 节点变动 → 同日缓存失效, 重扫结果含该节点 ──
+
+
+def test_node_change_invalidates_same_day_cache(tmp_path, monkeypatch):
+    vault = _vault(tmp_path, {"甲": _node()})
+    _patch_runner(monkeypatch, vault, tmp_path)
+    st = runner.load_state()
+    payload1, gen1 = runner.ensure_payload(st, NOW, TODAY)
+    assert gen1 == "new"
+    assert {d["node"] for d in payload1["due_nodes"]} == {"甲"}
+
+    # 写侧模拟: 当天考完甲后新增重学卡乙 (新卡无 fsrs_due = 即刻到期)
+    (vault / "节点" / "乙.md").write_text(_node(), encoding="utf-8")
+    _pin_pool_older_than_payload(vault, BASE)
+    _set_mtime(vault / "节点" / "乙.md", BASE + 200)
+    _set_mtime(vault / "节点", BASE + 200)
+
+    payload2, gen2 = runner.ensure_payload(st, NOW, TODAY)
+    assert gen2 == "new", "节点池比 payload 新时必须重扫, 不得整日复用早晨快照"
+    assert "乙" in {d["node"] for d in payload2["due_nodes"]}
+    assert payload2["schema_version"] == 3  # 只消费 A2 的 v3, 不改 schema
+
+
+# ── 场景 2: 无变动 → 仍走缓存 (每小时触发不得变成每小时全量重扫) ──
+
+
+def test_unchanged_pool_still_cached(tmp_path, monkeypatch):
+    vault = _vault(tmp_path, {"甲": _node()})
+    _patch_runner(monkeypatch, vault, tmp_path)
+    st = runner.load_state()
+    payload1, gen1 = runner.ensure_payload(st, NOW, TODAY)
+    assert gen1 == "new"
+
+    _pin_pool_older_than_payload(vault, BASE)
+
+    payload2, gen2 = runner.ensure_payload(st, NOW, TODAY)
+    assert gen2 == "cached"
+    assert payload2 == payload1  # 复用的是同一份落盘 payload
+
+
+# ── 场景 3: 重扫后同日推送仍 skip-done (Bark 同 id 去重门不被重扫击穿) ──
+
+
+def test_rescan_keeps_same_day_push_skip_done(tmp_path, monkeypatch, capsys):
+    vault = _vault(tmp_path, {"甲": _node()})
+    _patch_runner(monkeypatch, vault, tmp_path)
+    now_arg = "2026-07-30T10:00:00+08:00"
+    # today 按 runner 同一变换推导 (机器时区无关): skip-done 门在窗口门之前
+    today = datetime.fromisoformat(now_arg).astimezone().date().isoformat()
+
+    st = runner.load_state()
+    _, gen1 = runner.ensure_payload(st, datetime.fromisoformat(now_arg), today)
+    assert gen1 == "new"
+    st["last_push_accepted_date"] = today  # 早晨那次推送已被服务端接受
+    runner.save_state(st)
+
+    (vault / "节点" / "乙.md").write_text(_node(), encoding="utf-8")
+    _pin_pool_older_than_payload(vault, BASE)
+    _set_mtime(vault / "节点" / "乙.md", BASE + 200)
+    _set_mtime(vault / "节点", BASE + 200)
+
+    # 哨兵而非 mock: 该路径下 send 被调用即测试失败 (同日去重门失守)
+    def _sentinel(noti):
+        raise AssertionError("同日已推送后, 重扫不得再次触发 Bark 发送")
+
+    monkeypatch.setattr(runner.send_bark, "send", _sentinel)
+    monkeypatch.setattr(
+        sys,
+        "argv",
+        ["daily_review_run.py", "--now", now_arg, "--vault", str(vault)],
+    )
+    assert runner.main() == 0
+    out = capsys.readouterr().out
+    assert "generate:new" in out, "重扫必须真的发生 (否则本场景空转)"
+    assert "push:skip-done" in out
+
+    st2 = runner.load_state()
+    assert st2["last_push_accepted_date"] == today
+    assert st2["last_generate_date"] == today
+
+
+# ── 内审 HIGH (mutation 缺口): 两条 mtime 失效通道各自单独锁定 ──
+# 场景 1/3 同时钉文件+目录 mtime, 任一通道被删测试仍绿; 以下两测各锁一半。
+
+
+def test_infile_update_alone_triggers_rescan(tmp_path, monkeypatch):
+    """只有文件 mtime 变、目录 mtime 钉旧 (APFS 原地更新 fsrs_due 的
+    真实形态 — quiz 写侧头号生产场景) 也必须失效缓存。"""
+    vault = _vault(tmp_path, {"甲": _node()})
+    _patch_runner(monkeypatch, vault, tmp_path)
+    st = runner.load_state()
+    _, gen1 = runner.ensure_payload(st, NOW, TODAY)
+    assert gen1 == "new"
+
+    _pin_pool_older_than_payload(vault, BASE)
+    _set_mtime(vault / "节点" / "甲.md", BASE + 200)  # 只 bump 文件, 目录不动
+
+    _, gen2 = runner.ensure_payload(st, NOW, TODAY)
+    assert gen2 == "new", "原地更新节点内容 (目录 mtime 不变) 必须触发重扫"
+
+
+def test_deletion_via_dir_mtime_triggers_rescan(tmp_path, monkeypatch):
+    """删除节点不留文件 mtime、只改目录 mtime, 也必须失效缓存,
+    且被删节点从投影消失 (否则被删节点整天霸占推荐)。"""
+    vault = _vault(tmp_path, {"甲": _node(), "乙": _node()})
+    _patch_runner(monkeypatch, vault, tmp_path)
+    st = runner.load_state()
+    payload1, gen1 = runner.ensure_payload(st, NOW, TODAY)
+    assert gen1 == "new"
+    assert {d["node"] for d in payload1["due_nodes"]} == {"甲", "乙"}
+
+    (vault / "节点" / "乙.md").unlink()
+    _pin_pool_older_than_payload(vault, BASE)
+    _set_mtime(vault / "节点", BASE + 200)  # 只 bump 目录 (删除的真实形态)
+
+    payload2, gen2 = runner.ensure_payload(st, NOW, TODAY)
+    assert gen2 == "new"
+    assert {d["node"] for d in payload2["due_nodes"]} == {"甲"}
+
+
+# ── 内审 MEDIUM (实测复现): 扫描-落盘窗口内的写侧更新不得整天丢失 ──
+
+
+def test_write_during_scan_window_not_lost(tmp_path, monkeypatch):
+    """写侧恰在扫描完成后、payload 落盘前落地一张重学卡: 该卡 mtime 早于
+    payload 落盘时刻, 若以落盘时刻为基准则整天 cached 丢卡。基准必须是
+    扫描起点。真实 build_payload 照常执行, 仅在其返回后注入竞态写入。"""
+    vault = _vault(tmp_path, {"甲": _node()})
+    _patch_runner(monkeypatch, vault, tmp_path)
+    st = runner.load_state()
+
+    import daily_review_pick as picker
+
+    real_build = picker.build_payload
+    fired = []
+
+    def _race_build(*args, **kwargs):
+        result = real_build(*args, **kwargs)
+        if not fired:  # 只在首轮注入一次
+            fired.append(1)
+            (vault / "节点" / "竞态.md").write_text(_node(), encoding="utf-8")
+        return result
+
+    monkeypatch.setattr(picker, "build_payload", _race_build)
+    payload1, gen1 = runner.ensure_payload(st, NOW, TODAY)
+    assert gen1 == "new"
+    assert "竞态" not in {d["node"] for d in payload1["due_nodes"]}  # 首轮扫描没看到它
+
+    payload2, gen2 = runner.ensure_payload(st, NOW, TODAY)
+    assert gen2 == "new", "竞态窗口内落地的节点必须在下一轮触发重扫, 不得整天 cached"
+    assert "竞态" in {d["node"] for d in payload2["due_nodes"]}
+
+
+# ── tie-break 守卫: 重扫路径不写 board_last_recommended (卡片风险条目) ──
+
+
+def test_rescan_does_not_touch_board_last_recommended(tmp_path, monkeypatch):
+    vault = _vault(tmp_path, {"a甲": _node(board="A板")})
+    _patch_runner(monkeypatch, vault, tmp_path)
+    st = runner.load_state()
+    _, gen1 = runner.ensure_payload(st, NOW, TODAY)
+    assert gen1 == "new"
+    assert st["board_last_recommended"] == {"A板": TODAY}
+
+    # 新增 B 板节点后重扫: 同分 tie-break 下 B 板 (从未被推荐) 会登顶
+    (vault / "节点" / "b乙.md").write_text(_node(board="B板"), encoding="utf-8")
+    _pin_pool_older_than_payload(vault, BASE)
+    _set_mtime(vault / "节点" / "b乙.md", BASE + 200)
+    _set_mtime(vault / "节点", BASE + 200)
+
+    payload2, gen2 = runner.ensure_payload(st, NOW, TODAY)
+    assert gen2 == "new"
+    assert payload2["top_boards"][0]["board"] == "B板"
+    # 核心: 重扫换榜也不得把 B板 标成「今天推荐过」— 天级轮转语义只属于首扫
+    assert st["board_last_recommended"] == {"A板": TODAY}

**Analyzing file modification time discrepancies**
**Evaluating directory deletion impact on cache**
**Confirming card due time triggers rescans**
**Identifying flaw in hourly rescan logic**
**Planning test reproduction for rescan flaw**
**Verifying first generation logic consistency**
**Inspecting notification ID and concurrency lock**
codex
第一条核心反例已浮现，我正在用真实排程数据验证：若答错发生在整点任务前不足 10 分钟，本小时重扫可能早于 `fsrs_due`，随后 mtime 标记被“消费”，后续小时又走缓存——这会让 10 分钟重学卡仍消失到次日。接下来会确认生产解析与测试是否覆盖该时序，而不是只看新增即刻到期节点。
exec
/bin/zsh -lc "nl -ba scripts/daily_review_pick.py | sed -n '1,420p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
     1	#!/usr/bin/env python3
     2	"""每日复习选板 (DAILY-REVIEW-PUSH-2026-07-29, ChatGPT 终审 A3 修正版)。
     3	
     4	扫 vault 节点/*.md frontmatter → 衰减 Beta 读时时效 pick → 板级 min 聚合
     5	→ outputs/今日复习.md (人读) + outputs/今日复习.json (推送 payload, 终审 A7:
     6	stdout 是瞬时数据, 推送失败补跑必须有持久化 payload)。
     7	
     8	schema v3 (CARD-A2, BATCH-2026-08-24-复习闭环): 本 JSON 是全系统到期口径
     9	唯一裁判 — Dashboard.md 直接 dv.io.load 消费 due_nodes 明细 + ineligible
    10	分桶 (占位符待剖析积压单独成桶), 不再独立重算。v2→v3 纯加性, 推送链
    11	(daily_review_run/send_bark 只读 notification) 被动兼容。
    12	
    13	三态兼容 (live 实测 18 节点: 新字段 1 / 仅旧 10 / 无字段 7):
    14	  mastery_a/b (+last_examined) → effective() 闲置折扣后 pick
    15	  仅 mastery_score             → from_legacy() 均值继承低置信
    16	  无字段                       → 先验 Beta(0.9,2.1), 从未考 σ 大自动优先
    17	
    18	终审 A3 三修正:
    19	  1. eligibility 与 start-exam-board 同规则 — 含「你的 1-2 句精准定义」
    20	     占位符的未剖析节点跳过 (否则推荐无法出题的节点到手机)
    21	  2. 输出命令绑定 node <top_node> — start-exam-board 自己重选点时不含
    22	     闲置折扣, 不绑定会出现「通知说考 A 实际考 B」
    23	  3. min() 并列 tie-break: 板上次被推荐日期(久者先) → 最老 last_examined
    24	     → 板名 (防启动期先验板按扫描顺序永久霸榜)
    25	
    26	依赖: 仅 stdlib + vault 内 decay_beta.py (launchd 环境无 pip 包可假设)。
    27	"""
    28	
    29	from __future__ import annotations
    30	
    31	import argparse
    32	import json
    33	import math
    34	import os
    35	import re
    36	import sys
    37	from datetime import datetime, timezone
    38	from pathlib import Path
    39	
    40	#: 与 start-exam-board SKILL Step 3 完全同一条占位符规则 (终审 A3)
    41	PLACEHOLDER = "你的 1-2 句精准定义"
    42	
    43	#: 生产数据污染标记 (对齐 memory-health.sh 批次1'⑥ 审计清单) — 不推测试节点。
    44	#: ⚠ 只匹配文件名: 真实节点 frontmatter 可能引用测试会话 id (live 实测
    45	#: Fundamentals 的 error_candidates 含 m3-e2e-sessionend-test, 按全文匹配会误杀)
    46	TEST_MARKERS = ("TestConcept", "UAT-2.5", "m3-e2e")
    47	
    48	#: [Decision-FSRS-2] WHEN/WHAT 分工 (FSRS-V2-2026-07-30):
    49	#: FSRS 管 WHEN — fsrs_due 决定今天谁到期, 无字段 = New 卡即刻到期;
    50	#: 衰减 Beta 管 WHAT — 到期集合内按 pick=μ−σ 排序。
    51	#: 本文件保持纯 stdlib: 只做 UTC 定长字符串日期比较, 不 import fsrs。
    52	
    53	#: Bark 通知标题上限 (方案规范: ≤20 全角字符)
    54	TITLE_LIMIT = 20
    55	
    56	
    57	def _aware(s: str) -> datetime:
    58	    dt = datetime.fromisoformat(str(s).strip().replace("Z", "+00:00"))
    59	    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    60	
    61	
    62	def _fm_num(fm: str, key: str):
    63	    # 容负号 (Code-Review L5): mastery_a: -3 应进 corrupt 分支而非静默当无字段
    64	    m = re.search(rf'^{key}:\s*"?(-?[0-9]*\.?[0-9]+)"?\s*$', fm, re.M)
    65	    return float(m.group(1)) if m else None
    66	
    67	
    68	def _fm_str(fm: str, key: str):
    69	    m = re.search(rf'^{key}:\s*"?([^"\n]+?)"?\s*$', fm, re.M)
    70	    return m.group(1).strip() if m else None
    71	
    72	
    73	def _board_name(raw: str | None):
    74	    """source_board 归一化 → 板名 (live 数据实为 wikilink '[[原白板/X]]')。"""
    75	    if not raw:
    76	        return None
    77	    name = raw.strip()
    78	    if name.startswith("[[") and name.endswith("]]"):
    79	        name = name[2:-2]
    80	    name = name.split("|")[0]                 # [[path|alias]] 取 path
    81	    name = name.rsplit("/", 1)[-1].strip()    # 原白板/X → X
    82	    return name or None
    83	
    84	
    85	def scan_nodes(vault: Path, now: datetime, decay):
    86	    """扫描 节点/ 池 → (nodes, stats, ineligible)。逐节点容错: 单个脏节点不崩全轮。
    87	
    88	    ineligible 分桶 (schema v3, CARD-A2): 被跳过的节点按原因点名, 不再只有
    89	    计数 — Dashboard 消费 placeholder 桶显示"待剖析积压"。
    90	    """
    91	    stats = {"new": 0, "legacy": 0, "none": 0, "ineligible": 0, "test_excluded": 0, "corrupt": 0}
    92	    ineligible = {"placeholder": [], "test_excluded": [], "corrupt": []}
    93	    now_z = now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    94	    nodes = []
    95	    for path in sorted((vault / "节点").glob("*.md")):
    96	        stem = path.stem
    97	        try:
    98	            text = path.read_text(encoding="utf-8")
    99	        except OSError as e:
   100	            stats["corrupt"] += 1
   101	            ineligible["corrupt"].append(stem)
   102	            print(f"[pick] 读取失败跳过 {stem}: {e}", file=sys.stderr)
   103	            continue
   104	        if any(mk in stem for mk in TEST_MARKERS):
   105	            stats["test_excluded"] += 1
   106	            ineligible["test_excluded"].append(stem)
   107	            continue
   108	        m = re.match(r"^﻿?---\r?\n(.*?)\r?\n---\r?\n?(.*)$", text, re.S)
   109	        fm, body = (m.group(1), m.group(2)) if m else ("", text)
   110	        if PLACEHOLDER in body:
   111	            stats["ineligible"] += 1
   112	            ineligible["placeholder"].append(stem)
   113	            continue
   114	
   115	        a_raw, b_raw = _fm_num(fm, "mastery_a"), _fm_num(fm, "mastery_b")
   116	        legacy = next(
   117	            (v for k in ("mastery_score", "mastery", "mastery_level")
   118	             if (v := _fm_num(fm, k)) is not None),
   119	            None,
   120	        )
   121	        if a_raw is not None and b_raw is not None:
   122	            a, b, state = a_raw, b_raw, "new"
   123	        elif legacy is not None:
   124	            a, b = decay.from_legacy(legacy)
   125	            state = "legacy"
   126	        else:
   127	            a, b, state = decay.PRIOR_A, decay.PRIOR_B, "none"
   128	        stats[state] += 1
   129	
   130	        last_exam = _fm_str(fm, "last_examined")
   131	        idle_days = None
   132	        if last_exam:
   133	            try:
   134	                idle_days = max(0.0, (now - _aware(last_exam)).total_seconds() / 86400.0)
   135	            except ValueError:
   136	                print(f"[pick] last_examined 无法解析, 按从未考: {stem}", file=sys.stderr)
   137	                last_exam = None
   138	        try:
   139	            # pick_score 也在 try 内 (Code-Review M2): 除零/溢出同属脏数据
   140	            a_eff, b_eff = decay.effective(a, b, idle_days or 0.0)
   141	            pick = decay.pick_score(a_eff, b_eff)
   142	        except (ValueError, ZeroDivisionError, OverflowError) as e:
   143	            stats["corrupt"] += 1
   144	            ineligible["corrupt"].append(stem)
   145	            print(f"[pick] Beta 参数损坏跳过 {stem}: {e}", file=sys.stderr)
   146	            continue
   147	        if not math.isfinite(pick):
   148	            # Codex-A2 H1: 巨值 mastery 让 pick 静默算成 NaN/inf 不抛异常 —
   149	            # v3 起每个到期节点的 pick 都进 JSON, 单个 NaN = 全文件非法。
   150	            # 与其余脏数据同语义: 进 corrupt 桶, 不崩全轮。
   151	            stats["corrupt"] += 1
   152	            ineligible["corrupt"].append(stem)
   153	            print(f"[pick] Beta 参数溢出跳过 {stem}: pick={pick}", file=sys.stderr)
   154	            continue
   155	
   156	        fsrs_due = _fm_str(fm, "fsrs_due") or ""
   157	        due_fail_open = False
   158	        # Code-Review M2: Obsidian Properties 面板可能把 datetime 重新序列化成
   159	        # 带偏移格式, 词法比较会反向误判「永不到期」。非规范格式 fail-open
   160	        # 视同到期 (与 New 语义一致), 不静默消失。
   161	        # Codex-A2 M2: 形状正确但日历非法 (如月份 13) 词法比较会误判成未来,
   162	        # 同样 fail-open — 脏值策略统一为一条。
   163	        if fsrs_due:
   164	            due_ok = bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", fsrs_due))
   165	            if due_ok:
   166	                try:
   167	                    datetime.strptime(fsrs_due, "%Y-%m-%dT%H:%M:%SZ")
   168	                except ValueError:
   169	                    due_ok = False
   170	            if not due_ok:
   171	                print(f"[pick] fsrs_due 非规范格式, 视同到期: {stem} ({fsrs_due})", file=sys.stderr)
   172	                fsrs_due = ""
   173	                due_fail_open = True
   174	        nodes.append({
   175	            "node": stem,
   176	            "board": _board_name(_fm_str(fm, "source_board")),
   177	            "state": state,
   178	            "pick": pick,
   179	            "idle_days": idle_days,          # None = 从未考
   180	            "last_examined": last_exam or "",
   181	            "fsrs_due": fsrs_due,
   182	            "due_now": (not fsrs_due) or fsrs_due <= now_z,  # 无字段 = New 即刻到期
   183	            "due_fail_open": due_fail_open,
   184	            "difficulty": _fm_str(fm, "fsrs_difficulty") or "",
   185	        })
   186	    return nodes, stats, ineligible
   187	
   188	
   189	def rank_boards(nodes, board_last_recommended: dict):
   190	    """板级聚合: priority = min(pick), 终审 A3 tie-break。"""
   191	    boards: dict[str, list] = {}
   192	    unassigned = []
   193	    for n in nodes:
   194	        if not n["board"]:
   195	            unassigned.append(n["node"])
   196	            continue
   197	        boards.setdefault(n["board"], []).append(n)
   198	
   199	    ranked, upcoming = [], []
   200	    for board, members in boards.items():
   201	        due = [n for n in members if n["due_now"]]
   202	        if not due:
   203	            # WHEN: 全员未到期 → 不进推荐榜, 记最近的未来到期 (F1 放假语义)
   204	            nxt = min(members, key=lambda n: n["fsrs_due"])
   205	            upcoming.append({"board": board, "next_due": nxt["fsrs_due"], "node": nxt["node"]})
   206	            continue
   207	        top = min(due, key=lambda n: n["pick"])   # WHAT: 到期集合内衰减 Beta 排序
   208	        ranked.append({
   209	            "board": board,
   210	            "top_node": top["node"],
   211	            "priority": round(top["pick"], 4),
   212	            "pending": len(due),                   # 到期即待复习 (Decision-FSRS-2)
   213	            "idle_days": (None if top["idle_days"] is None else int(top["idle_days"])),
   214	            "difficulty": top["difficulty"],
   215	            "next_due": min((n["fsrs_due"] for n in members if not n["due_now"]), default=""),
   216	            "_tie": (
   217	                round(top["pick"], 8),
   218	                board_last_recommended.get(board, ""),   # 空串 = 从未被推荐, 排最前
   219	                min(n["last_examined"] for n in due),    # 空串 = 有从未考节点, 排最前
   220	                board,
   221	            ),
   222	        })
   223	    ranked.sort(key=lambda r: r["_tie"])
   224	    for r in ranked:
   225	        del r["_tie"]
   226	    upcoming.sort(key=lambda u: u["next_due"])
   227	    return ranked, upcoming, unassigned
   228	
   229	
   230	def _title(board: str) -> str:
   231	    prefix = "📚 今日复习 · "
   232	    room = TITLE_LIMIT - len(prefix)
   233	    return prefix + (board if len(board) <= room else board[: room - 1] + "…")
   234	
   235	
   236	def _body(top: dict) -> str:
   237	    idle = "从未考察" if top["idle_days"] is None else f"已闲置 {top['idle_days']} 天"
   238	    if top["pending"] >= 2:
   239	        return f"{top['top_node']} 等 {top['pending']} 节点待巩固 · {idle}"
   240	    return f"{top['top_node']} 待巩固 · {idle}"
   241	
   242	
   243	def build_payload(vault: Path, now: datetime, board_last_recommended: dict, decay):
   244	    nodes, stats, ineligible = scan_nodes(vault, now, decay)
   245	    ranked, upcoming, unassigned = rank_boards(nodes, board_last_recommended)
   246	    stats["unassigned"] = len(unassigned)
   247	    # v3 (CARD-A2): due_nodes 明细与 stats 数字同源派生 — 自洽靠构造保证,
   248	    # 本投影是全系统到期口径唯一裁判 (Dashboard 只消费不重算)
   249	    due_rows = [
   250	        {
   251	            "node": n["node"],
   252	            "board": n["board"],
   253	            "state": n["state"],
   254	            "pick": round(n["pick"], 4),
   255	            "fsrs_due": n["fsrs_due"],           # 空串 = 新卡即刻到期
   256	            # Codex-A2 M1: 消费方须能区分真新卡与 fail-open 的脏日期卡
   257	            "due_reason": ("malformed" if n["due_fail_open"]
   258	                           else ("scheduled" if n["fsrs_due"] else "new")),
   259	            "last_examined": n["last_examined"],
   260	            "difficulty": n["difficulty"],
   261	        }
   262	        for n in nodes if n["board"] and n["due_now"]
   263	    ]
   264	    stats["due_nodes"] = len(due_rows)
   265	    stats["future_nodes"] = sum(1 for n in nodes if n["board"] and not n["due_now"])
   266	    payload = {
   267	        "unassigned_nodes": unassigned,  # Code-Review M3: 点名而非只给数字
   268	        "schema_version": 3,             # v3: +due_nodes 明细 +ineligible 分桶
   269	        #                                  (纯加性; v2: FSRS WHEN 化 upcoming/due 语义)
   270	        "date": now.astimezone().date().isoformat(),
   271	        "generated_at": now.astimezone().isoformat(timespec="seconds"),
   272	        "top_boards": ranked[:3],
   273	        "upcoming": upcoming[:3],
   274	        "due_nodes": due_rows,
   275	        "ineligible": ineligible,
   276	        "stats": stats,
   277	        "notification": None,
   278	    }
   279	    day_id = f"canvas-review-{payload['date']}"
   280	    if ranked:
   281	        payload["notification"] = {
   282	            "title": _title(ranked[0]["board"]),
   283	            "body": _body(ranked[0]),
   284	            "group": "canvas复习",
   285	            "id": day_id,
   286	        }
   287	    elif upcoming:
   288	        # F1 放假语义: 有调度中的板但今天零到期 → 诚实说不用复习
   289	        nxt = upcoming[0]
   290	        payload["notification"] = {
   291	            "title": "📚 今日无到期节点",
   292	            "body": f"按计划推进，休息一天 · 最近到期 {nxt['board']} · {nxt['next_due'][:10]}",
   293	            "group": "canvas复习",
   294	            "id": day_id,
   295	        }
   296	    return payload, ranked
   297	
   298	
   299	def render_md(payload, ranked) -> str:
   300	    s = payload["stats"]
   301	    lines = [
   302	        f"# 今日复习 · {payload['date']}",
   303	        "",
   304	        f"> 生成 {payload['generated_at']} · 到期={s['due_nodes']} / 未到期={s['future_nodes']}（不含未归板）"
   305	        f" · 节点状态: new={s['new']} / legacy={s['legacy']}"
   306	        f" / 无字段={s['none']} / 未剖析跳过={s['ineligible']} / 测试排除={s['test_excluded']}"
   307	        f" / 未归板={s['unassigned']} / 损坏={s['corrupt']}",
   308	        "",
   309	        "| 板 | 优先分 | 到期待复习 | 最该考 | 难度 | 闲置 | 板内下次到期 |",
   310	        "|---|---|---|---|---|---|---|",
   311	    ]
   312	    for r in ranked:
   313	        idle = "从未考" if r["idle_days"] is None else f"{r['idle_days']} 天"
   314	        nxt = r["next_due"][:10] if r["next_due"] else "-"
   315	        diff = r["difficulty"] or "-"
   316	        lines.append(
   317	            f"| {r['board']} | {r['priority']} | {r['pending']} | {r['top_node']} | {diff} | {idle} | {nxt} |"
   318	        )
   319	    if payload.get("upcoming"):
   320	        for u in payload["upcoming"]:
   321	            lines.append(f"| {u['board']} | - | 0（未到期） | - | - | - | {u['next_due'][:10]} |")
   322	    if ranked:
   323	        lines += ["", "## 一键开考（整行复制到 Claudian）", ""]
   324	        for r in ranked:
   325	            lines.append(f"- `/start-exam-board from {r['board']} node {r['top_node']}`")
   326	    else:
   327	        lines += ["", "> ✅ 今日无到期节点，休息一天。"]
   328	    if payload.get("unassigned_nodes"):
   329	        lines += ["", "> ⚠ 未归板节点（无 source_board，不参与推荐）: "
   330	                  + "、".join(payload["unassigned_nodes"])]
   331	    lines += [
   332	        "",
   333	        "> WHEN=FSRS 到期（无 fsrs_due 字段 = 新卡即刻到期）；WHAT=到期集合内按 μ−σ 排序",
   334	        "> （含闲置回升，证据质量半衰期 69 天）。未剖析占位节点已跳过；命令已绑定最该考节点。",
   335	    ]
   336	    return "\n".join(lines) + "\n"
   337	
   338	
   339	def atomic_write(path: Path, content: str):
   340	    tmp = path.with_suffix(path.suffix + ".tmp")
   341	    tmp.write_text(content, encoding="utf-8")
   342	    os.replace(tmp, path)
   343	
   344	
   345	def load_decay(vault: Path):
   346	    sys.path.insert(0, str(vault / ".claude" / "scripts"))
   347	    import decay_beta
   348	    return decay_beta
   349	
   350	
   351	def main():
   352	    ap = argparse.ArgumentParser(description="每日复习选板")
   353	    ap.add_argument("--vault", required=True)
   354	    ap.add_argument("--state", help="daily-review.state.json (只读, 取 board_last_recommended)")
   355	    ap.add_argument("--now", help="ISO 时间覆盖 (测试用)")
   356	    ap.add_argument("--write", action="store_true", help="写 outputs/今日复习.md+json")
   357	    args = ap.parse_args()
   358	
   359	    vault = Path(args.vault)
   360	    # 裸时间当本地时区, 与 daily_review_run.py 语义统一 (Code-Review L6)
   361	    if args.now:
   362	        dt = datetime.fromisoformat(args.now.replace("Z", "+00:00"))
   363	        now = dt if dt.tzinfo else dt.astimezone()
   364	    else:
   365	        now = datetime.now(timezone.utc)
   366	    blr = {}
   367	    if args.state and Path(args.state).exists():
   368	        try:
   369	            blr = json.loads(Path(args.state).read_text(encoding="utf-8")).get(
   370	                "board_last_recommended", {})
   371	        except (json.JSONDecodeError, OSError):
   372	            pass  # state 损坏由 runner 处置, 选点侧降级为无记录
   373	
   374	    payload, ranked = build_payload(vault, now, blr, load_decay(vault))
   375	    if args.write:
   376	        out = vault / "outputs"
   377	        out.mkdir(parents=True, exist_ok=True)
   378	        atomic_write(out / "今日复习.md", render_md(payload, ranked))
   379	        atomic_write(out / "今日复习.json",
   380	                     json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
   381	    print(json.dumps(payload, ensure_ascii=False))
   382	
   383	
   384	if __name__ == "__main__":
   385	    main()

exec
/bin/zsh -lc "nl -ba scripts/send_bark.py | sed -n '1,320p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
     1	#!/usr/bin/env python3
     2	"""Bark 推送器 (DAILY-REVIEW-PUSH-2026-07-29, 终审 A5 硬化版)。
     3	
     4	安全契约:
     5	  - key 只存 ~/.config/canvas-review/bark.key (600), 不进 URL/argv/日志
     6	  - POST https://api.day.app/push JSON body (非 GET 路径拼接 — 免 URL
     7	    编码地雷 + 免板名进进程参数)
     8	  - 同日稳定 notification id → Bark 端幂等更新 (本地 at-least-once +
     9	    服务端同 id 覆盖, 终审 A4 网络 exactly-once 的正解)
    10	  - 内容形态: 明文具体板名 (用户 2026-07-29 拍板; E2E 加密进 backlog)
    11	
    12	退出码: 0 = 服务端明确接受 (HTTP 200 且 body code==200)
    13	        2 = 未配置 key (跳过, 不算错)
    14	        1 = 发送失败 (调用方走 osascript 兜底)
    15	"""
    16	
    17	from __future__ import annotations
    18	
    19	import argparse
    20	import json
    21	import os
    22	import re
    23	import sys
    24	import time
    25	import urllib.error
    26	import urllib.request
    27	from pathlib import Path
    28	
    29	KEY_FILE = Path(
    30	    os.environ.get("BARK_KEY_FILE")
    31	    or Path.home() / ".config" / "canvas-review" / "bark.key"
    32	)
    33	DEFAULT_SERVER = "https://api.day.app"
    34	TIMEOUT_S = 10
    35	RETRIES = 2
    36	
    37	
    38	def load_key() -> tuple[str, str] | None:
    39	    """读 key 文件 → (server, device_key)。兼容整段 URL 或裸 key。
    40	
    41	    Code-Review L4: 格式不合法 (贴了裸域名/空串) 按未配置处理并给具体
    42	    提示, 不进重试循环报误导性的 net= 错误。
    43	    """
    44	    if not KEY_FILE.exists():
    45	        print("bark skip(未配置) — 写入 ~/.config/canvas-review/bark.key 后启用")
    46	        return None
    47	    raw = KEY_FILE.read_text(encoding="utf-8").strip().rstrip("/")
    48	    if raw.startswith("http"):
    49	        server, _, key = raw.rpartition("/")
    50	    else:
    51	        server, key = DEFAULT_SERVER, raw
    52	    if not re.fullmatch(r"[A-Za-z0-9_-]{8,64}", key) or not server.startswith("http"):
    53	        print("bark skip(key格式不合法 — 应为 Bark app 复制的推送 key)")
    54	        return None
    55	    return (server, key)
    56	
    57	
    58	def send(notification: dict) -> int:
    59	    cfg = load_key()
    60	    if cfg is None:
    61	        return 2
    62	    server, device_key = cfg
    63	    body = json.dumps(
    64	        {
    65	            "device_key": device_key,
    66	            "title": notification["title"],
    67	            "body": notification["body"],
    68	            "group": notification.get("group", "canvas复习"),
    69	            "id": notification["id"],
    70	        },
    71	        ensure_ascii=False,
    72	    ).encode("utf-8")
    73	
    74	    last_err = "unknown"
    75	    for attempt in range(1 + RETRIES):
    76	        if attempt:
    77	            time.sleep(2 * attempt)
    78	        req = urllib.request.Request(
    79	            f"{server}/push", data=body,
    80	            headers={"Content-Type": "application/json; charset=utf-8"},
    81	            method="POST",
    82	        )
    83	        try:
    84	            with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
    85	                http = resp.status
    86	                try:
    87	                    code = json.loads(resp.read().decode("utf-8")).get("code")
    88	                except (json.JSONDecodeError, UnicodeDecodeError):
    89	                    code = None
    90	            if http == 200 and code == 200:
    91	                print(f"bark accepted http={http} code={code}")
    92	                return 0
    93	            last_err = f"http={http} code={code}"
    94	        except urllib.error.HTTPError as e:
    95	            last_err = f"http={e.code}"
    96	        except (urllib.error.URLError, TimeoutError, OSError) as e:
    97	            last_err = f"net={type(e).__name__}"
    98	    print(f"bark failed {last_err}")  # 永不打印 key/URL
    99	    return 1
   100	
   101	
   102	def main():
   103	    ap = argparse.ArgumentParser(description="Bark 推送 (payload 不进命令行)")
   104	    ap.add_argument("--payload", required=True, help="今日复习.json 路径")
   105	    args = ap.parse_args()
   106	    payload = json.loads(Path(args.payload).read_text(encoding="utf-8"))
   107	    noti = payload.get("notification")
   108	    if not noti:
   109	        print("bark skip(无可推内容)")
   110	        return 2
   111	    return send(noti)
   112	
   113	
   114	if __name__ == "__main__":
   115	    sys.exit(main())

exec
/bin/zsh -lc "rg -n \"def build_payload|def scan|fsrs_due|board_last_recommended|notification|bark|id\\\"|last_push_accepted_date|daily_review_run|daily-review\" scripts canvas-vault/.claude/scripts backend/app frontend/src --glob '*.py' --glob '*.sh' --glob '*.ts' --glob '*.tsx'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
backend/app/dependencies.py:1133:    "resolve_subject_id",  # Story 1.9: per-request subject resolution
canvas-vault/.claude/scripts/sync_board_concepts.py:143:    __slots__ = ("node_id", "role", "derived_from", "mastery", "attempts", "is_stub")
canvas-vault/.claude/scripts/sync_board_concepts.py:206:def scan_members(vault: Path) -> tuple[dict[str, list[Member]], list[str]]:
scripts/daily_review_run.py:5:壳层 daily-review-push.sh 只负责 mkdir 锁 + 固定解释器; 业务全在此处
scripts/daily_review_run.py:11:      · last_push_accepted_date 命名 (HTTP 成功仅证明服务端接受)
scripts/daily_review_run.py:29:import send_bark  # noqa: E402
scripts/daily_review_run.py:35:STATE = REPO / "backups" / "daily-review.state.json"
scripts/daily_review_run.py:36:LOG = REPO / "backups" / "daily-review.log"
scripts/daily_review_run.py:42:    "    display notification (item 2 of argv) with title (item 1 of argv)\n"
scripts/daily_review_run.py:56:        return {"schema_version": 1, "board_last_recommended": {}}
scripts/daily_review_run.py:59:        st.setdefault("board_last_recommended", {})
scripts/daily_review_run.py:69:        return {"schema_version": 1, "board_last_recommended": {}}
scripts/daily_review_run.py:89:    文件 mtime 抓原地更新 (quiz 写 fsrs_due 不动目录), 目录 mtime 抓
scripts/daily_review_run.py:112:    新 (quiz 写侧刚更新 fsrs_due / 新增重学卡) 则同日重扫, 否则当天到期的
scripts/daily_review_run.py:113:    重学卡永远进不了投影。push 去重不在此处: last_push_accepted_date 天然
scripts/daily_review_run.py:132:        VAULT, now, st["board_last_recommended"], picker.load_decay(VAULT))
scripts/daily_review_run.py:147:        st["board_last_recommended"][ranked[0]["board"]] = today
scripts/daily_review_run.py:185:    noti = (payload or {}).get("notification")
scripts/daily_review_run.py:189:    elif st.get("last_push_accepted_date") == today:
scripts/daily_review_run.py:194:        rc = send_bark.send(noti)
scripts/daily_review_run.py:196:            st["last_push_accepted_date"] = today
scripts/daily_review_run.py:204:                st["last_error"] = "bark-send"
canvas-vault/.claude/scripts/fsrs_bridge.py:5:frontmatter 字段 (fsrs_due/state/step/stability/difficulty/last_review)。
canvas-vault/.claude/scripts/fsrs_bridge.py:45:    "fsrs_due", "fsrs_state", "fsrs_step",
canvas-vault/.claude/scripts/fsrs_bridge.py:89:    if fields.get("fsrs_due"):
canvas-vault/.claude/scripts/fsrs_bridge.py:96:            due=_aware(fields["fsrs_due"]),
canvas-vault/.claude/scripts/fsrs_bridge.py:106:        "fsrs_due": _iso(card.due),
backend/app/services/websocket_manager.py:350:                "session_id": oldest_id,
backend/app/services/websocket_manager.py:355:                "session_id": newest_id,
scripts/sprint/update-current-task.py:55:    return data.get("development_status", {}).get("sprint_v3_obsidian_hybrid", {}) or {}
scripts/sprint/update-current-task.py:149:        frontmatter = _replace_field(frontmatter, "next_story_id", next_id)
scripts/send_bark.py:5:  - key 只存 ~/.config/canvas-review/bark.key (600), 不进 URL/argv/日志
scripts/send_bark.py:8:  - 同日稳定 notification id → Bark 端幂等更新 (本地 at-least-once +
scripts/send_bark.py:31:    or Path.home() / ".config" / "canvas-review" / "bark.key"
scripts/send_bark.py:45:        print("bark skip(未配置) — 写入 ~/.config/canvas-review/bark.key 后启用")
scripts/send_bark.py:53:        print("bark skip(key格式不合法 — 应为 Bark app 复制的推送 key)")
scripts/send_bark.py:58:def send(notification: dict) -> int:
scripts/send_bark.py:66:            "title": notification["title"],
scripts/send_bark.py:67:            "body": notification["body"],
scripts/send_bark.py:68:            "group": notification.get("group", "canvas复习"),
scripts/send_bark.py:69:            "id": notification["id"],
scripts/send_bark.py:91:                print(f"bark accepted http={http} code={code}")
scripts/send_bark.py:98:    print(f"bark failed {last_err}")  # 永不打印 key/URL
scripts/send_bark.py:107:    noti = payload.get("notification")
scripts/send_bark.py:109:        print("bark skip(无可推内容)")
backend/app/services/board_manifest_service.py:472:                "target_node_id": resolve_node_id(rel.get("target")),
backend/app/services/board_manifest_service.py:480:            "target_node_id": resolve_node_id(derived_from),
backend/app/services/board_manifest_service.py:525:def scan_vault(
backend/app/services/board_manifest_service.py:563:            "board_id": stem,
backend/app/services/board_manifest_service.py:590:                {"path": f"{NODE_DIR}/{path.name}", "error": mastery_err, "error_code": "mastery_invalid"}
backend/app/services/board_manifest_service.py:602:                    "error_code": "last_examined_invalid",
backend/app/services/board_manifest_service.py:616:            "node_id": stem,
backend/app/services/board_manifest_service.py:655:                    "node_id": stem,
backend/app/services/board_manifest_service.py:669:                    "node_id": stem,
backend/app/services/board_manifest_service.py:694:                    "exam_board_id": path.stem,
backend/app/services/board_manifest_service.py:695:                    "board_id": linked_board,
backend/app/services/board_manifest_service.py:704:                qid = str(q.get("id") or "").lower()[:40]
backend/app/services/board_manifest_service.py:706:                    "exam_board_id": path.stem,
backend/app/services/board_manifest_service.py:707:                    "qid": qid or None,
backend/app/services/board_manifest_service.py:716:                        if member["node_id"] == concept:
backend/app/services/board_manifest_service.py:777:        key=lambda m: (m["pick_hint"]["pick_score"], m["node_id"]),
backend/app/services/board_manifest_service.py:779:    rank_by_id = {m["node_id"]: i for i, m in enumerate(ranked, start=1)}
backend/app/services/board_manifest_service.py:786:        out.append({**m, "pick_hint": {**hint, "pick_rank": rank_by_id.get(m["node_id"])}})
backend/app/services/board_manifest_service.py:838:                "board_id": b["board_id"],
backend/app/services/board_manifest_service.py:845:                "exam_board_count": sum(1 for e in full["exam_history"] if e["board_id"] == b["board_id"]),
backend/app/services/board_manifest_service.py:864:    member_ids = {m["node_id"] for m in members}
backend/app/services/board_manifest_service.py:868:        "board_id": b["board_id"],
backend/app/services/board_manifest_service.py:879:        "concepts_only": [{"node_id": c, "exists": c in node_stems} for c in concepts if c not in member_ids],
backend/app/services/board_manifest_service.py:882:    result["exam_history"] = [e for e in exam_history if e["board_id"] == board_id]
backend/app/services/board_manifest_service.py:916:#:   v3 = allowlist 严格模型 (models/snapshot_v3.py, extra="forbid") —
frontend/src/services/claude-engine.ts:21: *         -> stdin: {"cmd":"query","id":"req-1","prompt":"...","resume":"session-id",...}
frontend/src/services/claude-engine.ts:22: *         -> stdout: {"id":"req-1","type":"text","text":"Hello"}
backend/app/services/scoring_faithfulness.py:507:        "node_id",
backend/app/services/scoring_faithfulness.py:508:        "exam_id",
backend/app/services/scoring_faithfulness.py:534:            node_id=getattr(autoscore_result, "node_id", ""),
backend/app/services/scoring_faithfulness.py:535:            exam_id=getattr(autoscore_result, "exam_id", ""),
scripts/harness/story_harness.py:174:            "story_id": story_id,
scripts/harness/story_harness.py:223:            "story_id": story_id,
scripts/harness/harness_progress.py:92:            "session_id": self.session_id,
scripts/harness/harness_progress.py:93:            "epic_id": self.epic_id,
scripts/harness/harness_progress.py:113:            session_id=data.get("session_id", ""),
scripts/harness/harness_progress.py:114:            epic_id=data.get("epic_id", ""),
scripts/harness/harness_progress.py:262:            "epic_id": self.epic_id,
backend/app/services/tool_executor.py:233:            doc_id = result.get("doc_id", "")
backend/app/services/event_bus.py:348:            "event_id": event.event_id,
backend/app/services/event_bus.py:398:                        event_id=entry["event_id"] + "_recovery",
backend/app/services/candidate_service.py:149:        if isinstance(cand, dict) and cand.get("id") == candidate_id:
backend/app/services/candidate_service.py:293:        node_id_for_dedupe = candidate.get("node_id") or ""
backend/app/services/candidate_service.py:319:            error_id = existing.get("id") or error_id
backend/app/services/candidate_service.py:320:            existing["id"] = error_id
backend/app/services/candidate_service.py:328:                "id": error_id,
backend/app/services/candidate_service.py:350:                "from_candidate_id": candidate_id,
scripts/ablation_fusion_weights.py:400:                    node_id=str(obj.get("node_id", f"row-{line_num}")),
frontend/src/services/api-client.ts:401:   *   "node_id": "abc-123",
backend/app/services/intelligent_grouping_service.py:395:                            if node["id"] == node_id:
backend/app/services/intelligent_grouping_service.py:434:            cluster_id = cluster.get("id", f"cluster-{i + 1}")
scripts/spec-tools/pre-commit-spec-sync.sh:84:CONSISTENCY_RESULT=$(python scripts/spec-tools/validate-spec-consistency.py --json 2>/dev/null || echo '{"summary":{"is_valid":true}}')
backend/app/services/review_service.py:181:            "task_id": self.task_id,
backend/app/services/review_service.py:413:            "task_id": task_id,
backend/app/services/review_service.py:631:            eligible_ids = {n.get("id") for n in eligible_nodes}
backend/app/services/review_service.py:636:                    and node.get("id") not in eligible_ids
backend/app/services/review_service.py:640:                    eligible_ids.add(node.get("id"))
backend/app/services/review_service.py:682:                {"id": node.get("id", ""), "name": node.get("text", "")}
backend/app/services/review_service.py:701:                node for node in eligible_nodes if node.get("id", "") in selected_ids
backend/app/services/review_service.py:837:                        "concept_id": concept_id,
backend/app/services/review_service.py:851:                    "concept_id": concept_id,
backend/app/services/review_service.py:897:            "concept_id": concept_id,
backend/app/services/review_service.py:1031:                    "concept_id": concept_id,
backend/app/services/review_service.py:1082:            "concept_id": concept_id,
backend/app/services/review_service.py:1193:                            "concept_id": memory.get(
backend/app/services/review_service.py:1194:                                "concept_id", memory.get("id", "")
backend/app/services/review_service.py:1259:                            "concept_id": key,
backend/app/services/review_service.py:1449:                    "id": f"review_{mode}_{datetime.now(timezone.utc).strftime('%Y%m%d')}",
backend/app/config.py:786:                explicit_vault_id = config.get("vault_id")
backend/app/services/conversation_archive.py:124:                nid = meta.get("node_id", "")
backend/app/services/conversation_archive.py:538:                ep_node_id = item.get("node_id") or item.get("metadata", {}).get(
backend/app/services/conversation_archive.py:539:                    "node_id", ""
backend/app/services/conversation_archive.py:605:                    "node_id": node_id,
backend/app/services/verification_service.py:498:            "session_id": self.session_id,
backend/app/services/verification_service.py:672:                "session_id": str,
backend/app/services/verification_service.py:727:            "session_id": session_id,
backend/app/services/verification_service.py:774:            "session_id": session_id,
backend/app/services/verification_service.py:841:                        "session_id": session_id,
backend/app/services/verification_service.py:1091:        return {"status": "paused", "session_id": session_id}
backend/app/services/verification_service.py:1144:            "session_id": session_id,
backend/app/services/verification_service.py:1172:            "session_id": session_id,
backend/app/services/verification_service.py:1342:            if node_ids and node.get("id") not in node_ids:
backend/app/services/verification_service.py:2902:                    "id": f"verification_{concept}",
scripts/migrate_story_frontmatter.py:30:    "story_id": re.compile(r"\*\*Story\s*ID[:\s]*\*\*\s*(\S+)", re.IGNORECASE),
scripts/migrate_story_frontmatter.py:31:    "epic_id": re.compile(r"\*\*Epic[:\s]*\*\*\s*(\S+)", re.IGNORECASE),
scripts/migrate_story_frontmatter.py:94:        if not fields.get("story_id"):
scripts/migrate_story_frontmatter.py:97:                fields["story_id"] = sid_match.group(1)
scripts/migrate_story_frontmatter.py:99:        if not fields.get("epic_id") and epic_num is not None:
scripts/migrate_story_frontmatter.py:100:            fields["epic_id"] = f"EPIC-{epic_num}"
backend/app/services/candidate_callout.py:96:    cid = candidate.get("id") or ""
backend/app/services/agent_routing_engine.py:514:                "node_id": request.node_id,
backend/app/services/memory_service.py:152:            "concept_id": self.concept_id,
backend/app/services/memory_service.py:289:                            e.get("user_id"),
backend/app/services/memory_service.py:296:                        user_id = record.get("user_id")
backend/app/services/memory_service.py:310:                            "episode_id": f"recovered-{idx}-{user_id or 'unknown'}-{record.get('concept_id') or 'unknown'}",
backend/app/services/memory_service.py:311:                            "user_id": user_id,
backend/app/services/memory_service.py:313:                            "concept_id": record.get("concept_id"),
backend/app/services/memory_service.py:316:                            "group_id": desanitize_group_id_from_graphiti(record.get("group_id") or ""),
backend/app/services/memory_service.py:367:            request_id=_ctx.get("request_id"),
backend/app/services/memory_service.py:479:                "episode_id": episode_id,
backend/app/services/memory_service.py:482:                "user_id": user_id,
backend/app/services/memory_service.py:484:                "node_id": node_id,
backend/app/services/memory_service.py:492:                "group_id": group_id,
backend/app/services/memory_service.py:497:                (i for i, ep in enumerate(self._episodes) if ep.get("episode_id") == episode_id),
backend/app/services/memory_service.py:503:                    input_summary={"concept": concept, "episode_id": episode_id},
backend/app/services/memory_service.py:620:        memory_episodes = [e for e in self._episodes if e.get("user_id") == user_id]
backend/app/services/memory_service.py:627:            memory_episodes = [e for e in memory_episodes if e.get("group_id", "") == group_id]
backend/app/services/memory_service.py:651:            existing_keys = {(e.get("node_id", ""), e.get("timestamp", "")) for e in episodes}
backend/app/services/memory_service.py:653:                key = (me.get("node_id", ""), me.get("timestamp", ""))
backend/app/services/memory_service.py:670:                failed_scores = [fs for fs in failed_scores if fs.get("user_id", "") == user_id]
backend/app/services/memory_service.py:695:            existing_keys = {(e.get("node_id", ""), e.get("timestamp", "")) for e in episodes}
backend/app/services/memory_service.py:697:                key = (fs.get("node_id", ""), fs.get("timestamp", ""))
backend/app/services/memory_service.py:748:                    "user_id": record.get("user_id"),
backend/app/services/memory_service.py:764:            "concept_id": concept_id,
backend/app/services/memory_service.py:1054:                required_fields = ["event_type", "timestamp", "canvas_path", "node_id"]
backend/app/services/memory_service.py:1062:                    node_id=event["node_id"],
backend/app/services/memory_service.py:1067:                    "episode_id": episode_id,
backend/app/services/memory_service.py:1071:                    "node_id": event["node_id"],
backend/app/services/memory_service.py:1078:                    (i for i, ep in enumerate(self._episodes) if ep.get("episode_id") == episode_id),
backend/app/services/memory_service.py:1090:                    "episode_id": episode_id,
backend/app/services/memory_service.py:1091:                    "user_id": "batch_user",
backend/app/services/memory_service.py:1093:                    "node_id": event["node_id"],
backend/app/services/memory_service.py:1149:                            "episode_id": eid,
backend/app/services/memory_service.py:1221:            dict: {"entity_id": str, "status": "written"|"enqueued"|"degraded"}.
backend/app/services/memory_service.py:1236:            "episode_id": entity_id,
backend/app/services/memory_service.py:1239:            "node_id": meta.get("node_id", ""),
backend/app/services/memory_service.py:1241:            "group_id": resolved_group_id,
backend/app/services/memory_service.py:1259:        node_id_for_exam = meta.get("node_id", "")
backend/app/services/memory_service.py:1304:                            annotation_id=meta.get("annotation_id") or None,
backend/app/services/memory_service.py:1337:                        target = meta.get("target_node_id", "")
backend/app/services/memory_service.py:1392:                            "group_id": resolved_group_id,
backend/app/services/memory_service.py:1400:                        meta.get("node_id", ""),
backend/app/services/memory_service.py:1404:        return {"entity_id": entity_id, "status": status}
backend/app/services/memory_service.py:1587:                        "episode_id": getattr(edge, "uuid", ""),
backend/app/services/memory_service.py:1596:                        "group_id": group_id or "",
backend/app/services/memory_service.py:1610:                        "episode_id": getattr(node, "uuid", ""),
backend/app/services/memory_service.py:1619:                        "group_id": group_id or "",
backend/app/services/memory_service.py:1659:                        "episode_id": getattr(r, "uuid", ""),
backend/app/services/memory_service.py:1668:                        "group_id": group_id or "",
backend/app/services/memory_service.py:1703:                gid = str(data.get("gid") or "")
backend/app/services/memory_service.py:1860:                        "episode_id": node.get("episode_id", ""),
backend/app/services/memory_service.py:1866:                        "group_id": desanitize_group_id_from_graphiti(node.get("group_id", "")),
backend/app/services/memory_service.py:1867:                        "node_id": node.get("node_id", ""),
backend/app/services/memory_service.py:1940:            ep_id = ep.get("episode_id", "")
backend/app/services/memory_service.py:1950:            ep_id = ep.get("episode_id", "")
backend/app/services/memory_service.py:1962:            if group_id and episode.get("group_id", "") != group_id:
backend/app/services/memory_service.py:1964:            ep_id = episode.get("episode_id", "")
backend/app/services/memory_service.py:1968:                str(episode.get(field, "")) for field in ("content", "episode_type", "node_id", "concept")
backend/app/services/memory_service.py:2042:                    "source_session": str(h.get("group_id") or ""),
backend/app/services/memory_service.py:2043:                    "_episode_id": str(h.get("episode_id") or ""),
backend/app/services/memory_service.py:2044:                    "_node_id": node_id,
backend/app/services/memory_service.py:2091:            "event_id": event_id,
backend/app/services/memory_service.py:2092:            "session_id": session_id,
backend/app/services/memory_service.py:2096:            "node_id": node_id,
backend/app/services/memory_service.py:2097:            "edge_id": edge_id,
backend/app/services/memory_service.py:2112:                        "episode_id": event_id,
backend/app/services/memory_service.py:2113:                        "user_id": session_id,
backend/app/services/memory_service.py:2115:                        "node_id": node_id or "",
backend/app/services/memory_service.py:2224:                        group_id=entry.get("group_id"),
backend/app/services/memory_service.py:2234:                concept = entry.get("concept", "") or entry.get("concept_id", "unknown")
backend/app/services/memory_service.py:2300:                            "node_id": entry.get("concept_id", ""),
backend/app/services/memory_service.py:2301:                            "concept": entry.get("concept", "") or entry.get("concept_id", ""),
backend/app/services/memory_service.py:2303:                            "user_id": entry.get("user_id", ""),  # S34 fix: include for filtering
backend/app/utils/cypher_helpers.py:85:        ... async def scan_all_group_ids(driver):
backend/app/utils/cypher_helpers.py:125:        (modified_query, params) — params 含 {"group_id": <value>} 供 tx.run(query, **params) 用
backend/app/utils/cypher_helpers.py:143:        >>> "AND n.group_id = $group_id" in q
backend/app/utils/cypher_helpers.py:152:    filter_clause = f"{where_keyword} {node_alias}.group_id = $group_id"
backend/app/utils/cypher_helpers.py:185:    return modified, {"group_id": group_id}
backend/app/services/react_agent.py:112:            query_type="hybrid",
backend/app/services/react_agent.py:643:            doc_id = result.get("doc_id", "")
backend/app/graphiti/identity_registry.py:65:            current_gid = getattr(node, "group_id", None)
backend/app/graphiti/identity_registry.py:84:                attributes={"node_id": node_id},
scripts/validate-cleanup.py:75:        "story_id": story_id,
backend/app/middleware/error_handler.py:89:            request_id = getattr(request.state, "request_id", "unknown")
backend/app/middleware/error_handler.py:109:            request_id = getattr(request.state, "request_id", "unknown")
scripts/validate_agent_yaml.py:127:        "valid": True,
scripts/validate_agent_yaml.py:133:        result["valid"] = False
scripts/validate_agent_yaml.py:148:            result["valid"] = False
scripts/validate_agent_yaml.py:198:        if not result["valid"]:
scripts/validate_agent_yaml.py:202:            result["valid"] = False
scripts/validate_agent_yaml.py:222:        if result["valid"] and not result["warnings"]:
scripts/validate_agent_yaml.py:223:            print("  ✅ Valid")
backend/app/services/background_task_manager.py:63:            "task_id": self.task_id,
backend/app/services/learning_context_service.py:53:        "node_id": node_id,
backend/app/services/learning_context_service.py:142:            ep_node_id = episode.get("node_id") or episode.get("metadata", {}).get(
backend/app/services/learning_context_service.py:143:                "node_id", ""
backend/app/services/learning_context_service.py:332:        "node_id": node_id,
scripts/verify-adr-coverage.py:84:    def scan_existing_adrs(self) -> Dict[str, Dict]:
backend/app/services/graphiti_memory_reader.py:87:        if (e.attributes or {}).get("source") == "relation" and (e.attributes or {}).get("node_id") == node_id
backend/app/middleware/llm_call_logger.py:180:        "request_id",
backend/app/middleware/llm_call_logger.py:389:                    rid = metadata.get("request_id")
backend/app/services/cross_subject_bridge.py:170:            all_subject_ids = [r["id"] for r in records if r.get("id")]
scripts/test-a11-end-to-end.py:308:        return [{"id": nid} for nid in PRIMARY_NODE_IDS]
backend/app/services/fallback_sync_service.py:324:        concept = entry.get("concept") or entry.get("concept_id", "")
backend/app/services/fallback_sync_service.py:373:                concept_id = entry.get("concept_id", concept)
backend/app/services/fallback_sync_service.py:391:        node_id = event.get("node_id")
backend/app/services/fallback_sync_service.py:392:        edge_id = event.get("edge_id")
backend/app/services/fallback_sync_service.py:407:                from_node = event.get("from_node_id", "")
backend/app/services/fallback_sync_service.py:408:                to_node = event.get("to_node_id", "")
scripts/memory-health.sh:70:RSTATE="$REPO/backups/daily-review.state.json"
scripts/memory-health.sh:80:if st.get("last_push_accepted_date", "") >= yesterday:
backend/app/services/graphiti_belief_service.py:315:                "uuid": e.uuid,
backend/app/services/graphiti_belief_service.py:355:        group_id=metadata.get("group_id") or getattr(task, "group_id", ""),
backend/app/services/graphiti_belief_service.py:358:        node_id=metadata.get("node_id"),
backend/app/services/graphiti_belief_service.py:359:        source_node_id=metadata.get("source_node_id"),
backend/app/services/graphiti_belief_service.py:360:        target_node_id=metadata.get("target_node_id"),
backend/app/api/v1/endpoints/exam_quick.py:129:        "node_id": req.node_id,
backend/app/api/v1/endpoints/exam_quick.py:130:        "vault_id": req.vault_id,
backend/app/main.py:68:from app.services.notification_channels import create_default_dispatcher  # noqa: E402
backend/app/main.py:124:    notification_dispatcher = create_default_dispatcher()
backend/app/main.py:127:        notification_dispatcher=notification_dispatcher,
backend/app/main.py:725:                request_id=getattr(request.state, "request_id", None),
backend/app/main.py:741:                    "bug_id": bug_id,  # ✅ Story 21.5.5 AC-1: 返回 bug_id
backend/app/core/failure_counters.py:108:        entry["edge_id"] = edge_id
backend/app/core/failure_counters.py:112:        entry["episode_id"] = episode_id
backend/app/core/failure_counters.py:116:        entry["request_id"] = request_id
backend/app/exceptions/canvas_exceptions.py:144:            details=details or {"node_id": node_id, "canvas_name": canvas_name},
backend/app/exceptions/canvas_exceptions.py:157:        >>> raise ValidationError("Invalid node color", field="color", value="invalid")
backend/app/exceptions/canvas_exceptions.py:234:            error_details["node_id"] = node_id
backend/app/services/rollback_service.py:417:        snap_nodes = {n["id"]: n for n in snapshot_data.get("nodes", [])}
backend/app/services/rollback_service.py:418:        curr_nodes = {n["id"]: n for n in current_data.get("nodes", [])}
backend/app/services/rollback_service.py:420:        snap_edges = {e["id"]: e for e in snapshot_data.get("edges", [])}
backend/app/services/rollback_service.py:421:        curr_edges = {e["id"]: e for e in current_data.get("edges", [])}
backend/app/services/rollback_service.py:432:                        "id": node_id,
backend/app/services/rollback_service.py:440:                        "id": node_id,
backend/app/services/rollback_service.py:458:                        "id": node_id,
backend/app/services/rollback_service.py:472:                        "id": edge_id,
backend/app/services/rollback_service.py:482:                        "id": edge_id,
backend/app/api/v1/endpoints/canvas.py:83:                    id=n["id"],
backend/app/api/v1/endpoints/canvas.py:96:            logger.warning("Skipping malformed node %s: %s", n.get("id"), exc)
backend/app/api/v1/endpoints/canvas.py:107:                    id=e["id"],
backend/app/api/v1/endpoints/canvas.py:116:            logger.warning("Skipping malformed edge %s: %s", e.get("id"), exc)
backend/app/api/v1/endpoints/canvas.py:123:        id=d["id"],
backend/app/api/v1/endpoints/canvas.py:139:        id=d["id"],
backend/app/services/mastery_store.py:86:        props["group_id"] = group_id
backend/app/services/mastery_store.py:525:            nid = r["node_id"] if isinstance(r, dict) else r.data()["node_id"]
backend/app/services/candidate_expiry_service.py:180:                        candidate_id=cand.get("id"),
backend/app/services/candidate_expiry_service.py:189:                            candidate_id=cand.get("id"),
backend/app/services/candidate_expiry_service.py:196:                        candidate_id=cand.get("id"),
scripts/bmad/scan_feedback.py:115:        data["id"] = anno_id
scripts/bmad/scan_feedback.py:137:def scan(
scripts/bmad/scan_feedback.py:201:        anno_id = r.get("id", "unknown")
scripts/bmad/scan_feedback.py:218:                    {"id": anno_id, "error": str(exc), "_raw": r},
backend/app/middleware/logging_middleware.py:183:    request_id = getattr(request.state, "request_id", "unknown")
backend/app/services/agent_service.py:122:            "concept_id": concept_id,
backend/app/services/agent_service.py:199:            "node_id": self.node_id,
backend/app/services/agent_service.py:206:            "bug_id": self.bug_id,
backend/app/services/agent_service.py:832:            "source_node_id": source_node_id,
backend/app/services/agent_service.py:836:            "bug_id": bug_id,
backend/app/services/agent_service.py:844:                "id": error_node_id,
backend/app/services/agent_service.py:856:                "id": f"edge-error-{uuid.uuid4().hex[:8]}",
backend/app/services/agent_service.py:868:        "source_node_id": source_node_id,
backend/app/services/agent_service.py:872:        "bug_id": bug_id,
backend/app/services/agent_service.py:926:            "node_id": node_id,
backend/app/services/agent_service.py:1077:        "id": personal_node_id,
backend/app/services/agent_service.py:1110:        "id": f"edge-personal-{uuid.uuid4().hex[:8]}",
backend/app/services/agent_service.py:1229:        "id": f"edge-{uuid.uuid4().hex[:8]}",
backend/app/services/agent_service.py:2193:        params = {"query_text": content[:100], "group_id": effective_group_id}
backend/app/services/agent_service.py:2820:                    extra={"bug_id": bug_id, "error_type": error_type.value},
backend/app/services/agent_service.py:2836:                        "bug_id": bug_id,
backend/app/services/agent_service.py:2855:                    extra={"bug_id": bug_id, "error_type": error_type.value},
backend/app/services/agent_service.py:2870:                    extra={"bug_id": bug_id, "error_type": error_type.value},
backend/app/services/agent_service.py:2886:                        "bug_id": bug_id,
backend/app/services/agent_service.py:2913:                    extra={"bug_id": bug_id, "error_type": error_type.value},
backend/app/services/agent_service.py:3016:                    extra={"bug_id": bug_id, "error_type": error_type.value},
backend/app/services/agent_service.py:3859:                        "id": question_node_id,
backend/app/services/agent_service.py:3873:                        "id": f"edge-basic-{uuid.uuid4().hex[:8]}",
backend/app/services/agent_service.py:3896:            "node_id": node_id,
backend/app/services/agent_service.py:3979:                        "id": question_node_id,
backend/app/services/agent_service.py:3993:                        "id": f"edge-deep-{uuid.uuid4().hex[:8]}",
backend/app/services/agent_service.py:4016:            "node_id": node_id,
backend/app/services/agent_service.py:4042:            {"scores": [{"node_id": ..., "accuracy": ..., ...}]}
backend/app/services/agent_service.py:4232:                    "node_id": node_id,
backend/app/services/agent_service.py:4264:                            if node.get("id") == node_id:
backend/app/services/agent_service.py:4322:        nodes = {n["id"]: n for n in canvas_data.get("nodes", [])}
backend/app/services/agent_service.py:4393:        nodes = {n["id"]: n for n in canvas_data.get("nodes", [])}
backend/app/services/agent_service.py:4483:                    (n for n in canvas_data.get("nodes", []) if n.get("id") == node_id),
backend/app/services/agent_service.py:4636:                    "node_id": node_id,
backend/app/services/agent_service.py:4746:                        "id": explain_node_id,
backend/app/services/agent_service.py:4762:                        "id": edge1_id,
backend/app/services/agent_service.py:4781:                            "id": yellow_node_id,
backend/app/services/agent_service.py:4799:                            "id": edge2_id,
backend/app/services/agent_service.py:4848:                        "id": created_node_id,
backend/app/services/agent_service.py:4868:                        "id": edge1_id,
backend/app/services/agent_service.py:4885:                            "id": yellow_node_id,
backend/app/services/agent_service.py:4903:                            "id": edge2_id,
backend/app/services/agent_service.py:4962:            "node_id": node_id,
backend/app/services/agent_service.py:4965:            "created_node_id": created_node_id,  # ✅ Required by ExplainResponse
backend/app/services/agent_service.py:5399:                    "id": node_id,
backend/app/services/agent_service.py:5469:                        "id": question_node_id,
backend/app/services/agent_service.py:5483:                        "id": f"edge-vq-{uuid.uuid4().hex[:8]}",
backend/app/services/agent_service.py:5643:                        "id": question_node_id,
backend/app/services/agent_service.py:5657:                        "id": f"edge-qd-{uuid.uuid4().hex[:8]}",
backend/app/core/decision_tracker.py:11:        input_summary={"node_id": node_id, "score": score},
backend/app/core/decision_tracker.py:49:        request_id = ctx.get("request_id", "unknown")
backend/app/core/decision_tracker.py:53:        story_id = ctx.get("current_story_id")
backend/app/core/decision_tracker.py:57:        "decision_id": decision_id,
backend/app/core/decision_tracker.py:62:        "request_id": request_id,
backend/app/core/decision_tracker.py:65:        extra["story_id"] = story_id
backend/app/services/episode_worker.py:109:            "group_id": self.group_id,
backend/app/services/episode_worker.py:116:            result["request_id"] = self.request_id
backend/app/services/episode_worker.py:257:            record["request_id"] = request_id
backend/app/services/episode_worker.py:601:            "group_id": semantic_group_id(sanitize_group_id_for_graphiti(task.group_id)),
backend/app/services/intelligent_parallel_service.py:219:                        "group_id": g.group_id,
backend/app/services/intelligent_parallel_service.py:364:                group_id = g_meta.get("group_id", "unknown")
backend/app/services/intelligent_parallel_service.py:560:                if node.get("id") == node_id:
backend/app/services/conversation_distiller.py:384:                        "node_id": node_id,
backend/app/services/conversation_distiller.py:399:                        "tip_id": str(uuid.uuid4()),
backend/app/services/conversation_distiller.py:403:                        "node_id": node_id,
backend/app/services/conversation_distiller.py:443:                        cand_id = dual.get("candidate_id")
backend/app/services/conversation_distiller.py:468:                        "node_id": node_id,
backend/app/api/v1/endpoints/traces.py:41:                    if entry.get("request_id") == request_id:
backend/app/api/v1/endpoints/traces.py:53:    description="Aggregate all log file entries matching the given request_id",
backend/app/api/v1/endpoints/traces.py:68:        "request_id": request_id,
backend/app/services/context_enrichment_service.py:60:    node_id = node.get("id", "unknown")
backend/app/services/context_enrichment_service.py:580:                    "id": node.get("id"),
backend/app/services/context_enrichment_service.py:646:        nodes = {n.get("id"): n for n in canvas_data.get("nodes", [])}
backend/app/services/context_enrichment_service.py:893:                adj.node.get("id") for adj in adjacent if adj.node.get("id")
backend/app/services/wikilink_parser.py:137:                    invalid_reason="empty_block_id",
backend/app/models/agent_routing_models.py:75:            "node_id": self.node_id,
scripts/launchd/daily-review-wrapper.sh:12:BOOTLOG="$HOME/Library/Logs/canvas-daily-review.boot.log"
scripts/launchd/daily-review-wrapper.sh:37:head -c 1 "$WT/scripts/daily-review-push.sh" >/dev/null 2>&1 \
scripts/launchd/daily-review-wrapper.sh:47:exec "$WT/scripts/daily-review-push.sh" --vault "$VAULT" "$@"
backend/app/services/health_monitor.py:224:                    threshold="All parameters valid",
backend/app/services/health_monitor.py:231:                value="all valid",
backend/app/services/health_monitor.py:232:                threshold="All parameters valid",
backend/app/services/health_monitor.py:239:                threshold="All parameters valid",
backend/app/api/v1/endpoints/errors.py:125:    candidate_id: str = Field(..., description="error_candidates[].id")
backend/app/api/v1/endpoints/errors.py:139:    candidate_id: str = Field(..., description="error_candidates[].id")
backend/app/services/notification_channels.py:11:- Obsidian SSE notifications
backend/app/services/notification_channels.py:37:    """Abstract base class for notification channels.
backend/app/services/notification_channels.py:41:    All notification channels must implement the send() method.
backend/app/services/notification_channels.py:46:        """Send notification for an alert event.
backend/app/services/notification_channels.py:53:            bool: True if notification was sent successfully
backend/app/services/notification_channels.py:65:    """Console logging notification channel.
backend/app/services/notification_channels.py:76:        """Send notification via structlog.
backend/app/services/notification_channels.py:107:    """File logging notification channel.
backend/app/services/notification_channels.py:120:        """Initialize file notification channel.
backend/app/services/notification_channels.py:129:        """Write notification to log file.
backend/app/services/notification_channels.py:150:                "file_notification.failed",
backend/app/services/notification_channels.py:164:    """Obsidian plugin SSE notification channel.
backend/app/services/notification_channels.py:176:        """Initialize Obsidian notification channel.
backend/app/services/notification_channels.py:184:        """Send notification via SSE broadcast.
backend/app/services/notification_channels.py:195:                "obsidian_notification.skipped",
backend/app/services/notification_channels.py:210:                "obsidian_notification.failed",
backend/app/services/notification_channels.py:224:    """Webhook notification channel.
backend/app/services/notification_channels.py:234:        """Initialize webhook notification channel.
backend/app/services/notification_channels.py:244:        """Send notification via HTTP POST.
backend/app/services/notification_channels.py:268:            logger.error("webhook_notification.httpx_not_installed")
backend/app/services/notification_channels.py:272:                "webhook_notification.failed",
backend/app/services/notification_channels.py:288:    Routes alert events to all configured notification channels.
backend/app/services/notification_channels.py:303:        """Initialize notification dispatcher.
backend/app/services/notification_channels.py:306:            channels: List of notification channels to dispatch to
backend/app/services/notification_channels.py:325:                    "notification_dispatch.failed",
backend/app/services/notification_channels.py:342:    """Create notification dispatcher with default channels.
backend/app/services/notification_channels.py:352:        sse_manager: Optional SSE connection manager for Obsidian notifications
backend/app/services/notification_channels.py:353:        log_path: Path for file notifications
backend/app/services/notification_channels.py:367:        "notification_dispatcher.created",
backend/app/models/intelligent_parallel_models.py:311:        alias="session_id",
backend/app/models/intelligent_parallel_models.py:410:        alias="session_id",
backend/app/services/error_rebuild_service.py:211:            err_id = err_record.get("id")
scripts/lib/planning_utils.py:428:def scan_planning_files() -> Dict[str, List[Path]]:
backend/app/core/subject_config.py:30:    "current_subject_id", default=DEFAULT_SUBJECT_ID
backend/app/core/subject_config.py:90:                        "id": rec.get("id", ""),
backend/app/core/subject_config.py:404:        ``("AND n.subjectId = $subject_id", {"subject_id": "math"})``
backend/app/core/subject_config.py:410:        f"AND {node_alias}.subjectId = $subject_id",
backend/app/core/subject_config.py:411:        {"subject_id": subject_id},
backend/app/services/archive_scheduler.py:198:                    nid = item.get("node_id")
backend/app/services/archive_scheduler.py:202:                            nid = meta.get("node_id")
scripts/finalize-iteration.py:129:            print_status("Source citations valid", "success")
scripts/finalize-iteration.py:153:            print_status("Content consistency valid", "success")
backend/app/api/v1/endpoints/archive.py:226:                        and metadata.get("node_id") == node_id
backend/app/models/metadata_models.py:62:                "group_id": "math54:离散数学",
backend/app/models/metadata_models.py:143:                "vault_id": "cs_61b",
backend/app/models/metadata_models.py:177:                "group_id": "math54:离散数学",
backend/app/models/metadata_models.py:292:                "group_id": "math54:离散数学",
backend/app/services/alert_manager.py:11:- Alert notification dispatch
backend/app/services/alert_manager.py:32:    from .notification_channels import NotificationDispatcher
backend/app/services/alert_manager.py:65:    - FIRING: Alert triggered, notifications sent
backend/app/services/alert_manager.py:138:            "id": self.id,
backend/app/services/alert_manager.py:177:        notification_dispatcher: "NotificationDispatcher",
backend/app/services/alert_manager.py:184:            notification_dispatcher: Dispatcher for sending notifications
backend/app/services/alert_manager.py:188:        self.notification_dispatcher = notification_dispatcher
backend/app/services/alert_manager.py:437:        """Fire an alert and send notifications.
backend/app/services/alert_manager.py:453:        await self.notification_dispatcher.dispatch(alert, "fired")
backend/app/services/alert_manager.py:456:        """Resolve an alert and send notifications.
backend/app/services/alert_manager.py:469:        await self.notification_dispatcher.dispatch(alert, "resolved")
scripts/validate-source-citations.py:149:                issues.append("Context7 type specified but missing library_id")
scripts/validate-source-citations.py:375:      {{"type": "context7", "library_id": "/org/project", "topic": "topic"}},
backend/app/services/targeting_material_service.py:102:            err_group = str(err.get("group_id") or "").strip()
backend/app/services/targeting_material_service.py:189:        data for rec in records if (data := rec if isinstance(rec, dict) else rec.data()).get("neighbor_id")
backend/app/services/targeting_material_service.py:198:        neighbor_id = str(data.get("neighbor_id") or "")
scripts/lib/breaking_change_detector.py:157:                    'migration': f"Existing data without '{field}' will become invalid"
backend/app/api/v1/endpoints/debug.py:43:                            "bug_id": "BUG-A1B2C3D4",
backend/app/api/v1/endpoints/debug.py:80:                "bug_id": "BUG-A1B2C3D4",
backend/app/api/v1/endpoints/debug.py:170:    operation_id="get_bug_by_id",
backend/app/api/v1/endpoints/debug.py:177:                        "bug_id": "BUG-A1B2C3D4",
backend/app/services/conversation_inheritance.py:80:        neighbor_node_id = rec.get("node_id") or neighbor_name
backend/app/services/topic_clustering.py:174:                "id": group_id,
backend/app/services/topic_clustering.py:201:                        "group_id": group_id,
backend/app/services/learning_event_log.py:92:                "event_id": event_id,
backend/app/services/learning_event_log.py:95:                "node_id": node_id,
scripts/sync_links.py:65:        sid = fm.get("story_id", "")
scripts/sync_links.py:69:                "epic_id": fm.get("epic_id", ""),
scripts/sync_links.py:70:                "prd_id": fm.get("prd_id", ""),
scripts/sync_links.py:86:                eid = fm.get("epic_id", "")
scripts/sync_links.py:101:        eid = data.get("epic_id", "")
scripts/sync_links.py:116:        eid = data.get("epic_id", "")
scripts/sync_links.py:151:    eid = data.get("epic_id", "")
scripts/sync_links.py:155:    prd_id = data.get("prd_id", "")
backend/app/services/event_handlers.py:44:    node_id = payload.get("node_id")
backend/app/services/event_handlers.py:46:    session_id = payload.get("session_id")
backend/app/services/event_handlers.py:78:            "node_id": node_id,
backend/app/services/event_handlers.py:79:            "session_id": session_id,
backend/app/services/event_handlers.py:90:            "node_id": node_id,
backend/app/services/event_handlers.py:91:            "session_id": session_id,
backend/app/services/event_handlers.py:113:    node_id = payload.get("node_id")
backend/app/services/event_handlers.py:114:    session_id = payload.get("session_id")
backend/app/services/event_handlers.py:143:            "node_id": node_id,
backend/app/services/event_handlers.py:144:            "session_id": session_id,
backend/app/services/event_handlers.py:171:    node_id = payload.get("node_id")
backend/app/services/event_handlers.py:183:            "node_id": node_id,
backend/app/services/event_handlers.py:184:            "session_id": payload.get("session_id"),
backend/app/services/event_handlers.py:209:    node_id = payload.get("node_id")
backend/app/services/event_handlers.py:212:    session_id = payload.get("session_id", "")
backend/app/services/event_handlers.py:250:    node_id = payload.get("node_id")
backend/app/services/event_handlers.py:253:    user_id = payload.get("user_id", "default")
backend/app/services/event_handlers.py:259:        logger.warning("handle_memory_write_requested: missing node_id")
backend/app/services/event_handlers.py:294:    node_id = payload.get("node_id")
backend/app/services/event_handlers.py:295:    session_id = payload.get("session_id", "")
backend/app/services/event_handlers.py:304:    group_id = payload.get("group_id", DEFAULT_GROUP_ID)
backend/app/services/event_handlers.py:317:            "node_id": node_id,
backend/app/services/event_handlers.py:318:            "session_id": session_id,
backend/app/services/event_handlers.py:345:    node_id = payload.get("node_id")
backend/app/services/event_handlers.py:377:    node_id = payload.get("node_id")
backend/app/clients/neo4j_edge_client.py:291:                        "doc_id": r.get("node_id", ""),
backend/app/clients/neo4j_edge_client.py:296:                            "group_id": r.get("group_id"),
backend/app/clients/neo4j_edge_client.py:379:                    "doc_id": r.get("node_id", ""),
backend/app/clients/neo4j_edge_client.py:384:                        "group_id": r.get("group_id"),
backend/app/clients/neo4j_edge_client.py:440:                    "node_id": r.get("node_id", ""),
backend/app/clients/neo4j_edge_client.py:469:            edge_id = edge.get("id", f"edge-{from_node}-{to_node}")
backend/app/clients/neo4j_edge_client.py:529:                            edge_id=edge.get("id"),
backend/app/clients/neo4j_edge_client.py:845:                "node_id": memory.node_id,
backend/app/clients/neo4j_edge_client.py:898:            if node_id and memory.get("node_id") != node_id:
backend/app/clients/neo4j_edge_client.py:958:            if node_id and memory.get("node_id") != node_id:
backend/app/models/canvas_events.py:105:                "event_id": "550e8400-e29b-41d4-a716-446655440000",
backend/app/models/canvas_events.py:106:                "session_id": "session_abc123",
backend/app/models/canvas_events.py:110:                "node_id": "node_xyz789",
backend/app/models/canvas_events.py:251:        return self.payload.get("node_id")
backend/app/models/canvas_events.py:255:        return self.payload.get("session_id")
backend/app/api/v1/endpoints/rag.py:69:                "subject_id": "math",
backend/app/api/v1/endpoints/rag.py:148:                        "doc_id": "node-123",
backend/app/api/v1/endpoints/rag.py:156:                        "id": "mm-001",
backend/app/api/v1/endpoints/rag.py:281:                    doc_id=r.get("doc_id", ""),
backend/app/api/v1/endpoints/rag.py:290:                    id=mm.get("id", ""),
scripts/daily_review_pick.py:11:(daily_review_run/send_bark 只读 notification) 被动兼容。
scripts/daily_review_pick.py:49:#: FSRS 管 WHEN — fsrs_due 决定今天谁到期, 无字段 = New 卡即刻到期;
scripts/daily_review_pick.py:85:def scan_nodes(vault: Path, now: datetime, decay):
scripts/daily_review_pick.py:156:        fsrs_due = _fm_str(fm, "fsrs_due") or ""
scripts/daily_review_pick.py:163:        if fsrs_due:
scripts/daily_review_pick.py:164:            due_ok = bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", fsrs_due))
scripts/daily_review_pick.py:167:                    datetime.strptime(fsrs_due, "%Y-%m-%dT%H:%M:%SZ")
scripts/daily_review_pick.py:171:                print(f"[pick] fsrs_due 非规范格式, 视同到期: {stem} ({fsrs_due})", file=sys.stderr)
scripts/daily_review_pick.py:172:                fsrs_due = ""
scripts/daily_review_pick.py:181:            "fsrs_due": fsrs_due,
scripts/daily_review_pick.py:182:            "due_now": (not fsrs_due) or fsrs_due <= now_z,  # 无字段 = New 即刻到期
scripts/daily_review_pick.py:189:def rank_boards(nodes, board_last_recommended: dict):
scripts/daily_review_pick.py:204:            nxt = min(members, key=lambda n: n["fsrs_due"])
scripts/daily_review_pick.py:205:            upcoming.append({"board": board, "next_due": nxt["fsrs_due"], "node": nxt["node"]})
scripts/daily_review_pick.py:215:            "next_due": min((n["fsrs_due"] for n in members if not n["due_now"]), default=""),
scripts/daily_review_pick.py:218:                board_last_recommended.get(board, ""),   # 空串 = 从未被推荐, 排最前
scripts/daily_review_pick.py:243:def build_payload(vault: Path, now: datetime, board_last_recommended: dict, decay):
scripts/daily_review_pick.py:245:    ranked, upcoming, unassigned = rank_boards(nodes, board_last_recommended)
scripts/daily_review_pick.py:255:            "fsrs_due": n["fsrs_due"],           # 空串 = 新卡即刻到期
scripts/daily_review_pick.py:258:                           else ("scheduled" if n["fsrs_due"] else "new")),
scripts/daily_review_pick.py:277:        "notification": None,
scripts/daily_review_pick.py:281:        payload["notification"] = {
scripts/daily_review_pick.py:285:            "id": day_id,
scripts/daily_review_pick.py:290:        payload["notification"] = {
scripts/daily_review_pick.py:294:            "id": day_id,
scripts/daily_review_pick.py:333:        "> WHEN=FSRS 到期（无 fsrs_due 字段 = 新卡即刻到期）；WHAT=到期集合内按 μ−σ 排序",
scripts/daily_review_pick.py:354:    ap.add_argument("--state", help="daily-review.state.json (只读, 取 board_last_recommended)")
scripts/daily_review_pick.py:360:    # 裸时间当本地时区, 与 daily_review_run.py 语义统一 (Code-Review L6)
scripts/daily_review_pick.py:370:                "board_last_recommended", {})
backend/app/services/exam_service_ext.py:492:                "node_id": request.node_id,
backend/app/services/exam_service_ext.py:493:                "question_id": request.question_id,
backend/app/services/exam_service_ext.py:685:            record_id = data.get("id", request.exam_id)
backend/app/services/exam_service_ext.py:823:            exam_id=data.get("exam_id", exam_id),
backend/app/services/exam_service_ext.py:824:            source_canvas_id=data.get("source_canvas_id", ""),
backend/app/services/multimodal_service.py:590:            "id": content_id,
backend/app/services/multimodal_service.py:593:            "related_concept_id": related_concept_id,
backend/app/services/multimodal_service.py:734:            "id": content_id,
backend/app/services/multimodal_service.py:737:            "related_concept_id": request.related_concept_id,
backend/app/services/multimodal_service.py:794:                id=data["id"],
backend/app/services/multimodal_service.py:797:                related_concept_id=data["related_concept_id"],
backend/app/services/multimodal_service.py:888:            id=data["id"],
backend/app/services/multimodal_service.py:891:            related_concept_id=data["related_concept_id"],
backend/app/services/multimodal_service.py:991:            if (not concept_id or data["related_concept_id"] == concept_id)
backend/app/services/multimodal_service.py:997:                id=data["id"],
backend/app/services/multimodal_service.py:1000:                related_concept_id=data["related_concept_id"],
backend/app/services/multimodal_service.py:1135:            id=data["id"],
backend/app/services/multimodal_service.py:1142:            conceptId=data.get("related_concept_id"),
backend/app/services/multimodal_service.py:1222:            if data["id"] in seen_ids:
backend/app/services/multimodal_service.py:1224:            if data["related_concept_id"] != concept_id:
backend/app/services/multimodal_service.py:1482:                                "id": content.id,
backend/app/services/multimodal_service.py:1487:                                "related_concept_id": content.related_concept_id,
backend/app/services/multimodal_service.py:1508:                                        "id": content.id,
backend/app/services/multimodal_service.py:1513:                                        "related_concept_id": content.related_concept_id,
backend/app/services/group_id_migration_service.py:195:        old = rec.get("gid") or rec.get("group_id") or ""
backend/app/domains/infra/gateway.py:10:       error_aggregator, notification_channels, prompt_registry,
backend/app/domains/infra/gateway.py:47:from app.services.notification_channels import create_default_dispatcher
backend/app/models/snapshot_v3.py:1:"""P1-05b SnapshotV3 — 磁盘快照的 allowlist 严格模型 (extra="forbid")。
backend/app/models/snapshot_v3.py:4:  - 本模块 (SnapshotV3*):  磁盘读写层。extra="forbid" — 任何新增字段必须显式
backend/app/models/snapshot_v3.py:47:    "mastery_invalid",
backend/app/models/snapshot_v3.py:48:    "last_examined_invalid",
backend/app/models/snapshot_v3.py:56:    "mastery_invalid": "mastery 字段无效 (非有限数值或非正), 按未评估处理",
backend/app/models/snapshot_v3.py:57:    "last_examined_invalid": "last_examined 无法解析, 按从未考",
backend/app/models/snapshot_v3.py:125:    model_config = ConfigDict(extra="forbid", strict=True)
backend/app/models/snapshot_v3.py:143:    _id = field_validator("target_node_id")(classmethod(lambda cls, v: _require_id_like(v)))
backend/app/models/snapshot_v3.py:157:    _id = field_validator("exam_board_id", "qid")(classmethod(lambda cls, v: _require_id_like(v)))
backend/app/models/snapshot_v3.py:175:    _id = field_validator("node_id", "source_note")(classmethod(lambda cls, v: _require_id_like(v)))
backend/app/models/snapshot_v3.py:187:    _id = field_validator("board_id")(classmethod(lambda cls, v: _require_id_like(v)))
backend/app/models/snapshot_v3.py:205:    _id = field_validator("node_id")(classmethod(lambda cls, v: _require_id_like(v)))
backend/app/models/snapshot_v3.py:216:    _id = field_validator("exam_board_id", "board_id", "selected_node")(classmethod(lambda cls, v: _require_id_like(v)))
backend/app/models/snapshot_v3.py:289:                        "node_id": m.node_id,
backend/app/models/snapshot_v3.py:297:                                "target_node_id": m.relation.target_node_id,
backend/app/models/snapshot_v3.py:323:                "board_id": board.board_id,
backend/app/models/snapshot_v3.py:338:                    "node_id": o.node_id,
backend/app/models/snapshot_v3.py:362:        _tgt = str(relation["target_node_id"]) if relation.get("target_node_id") else None
backend/app/models/snapshot_v3.py:367:            "target_node_id": _tgt,
backend/app/models/snapshot_v3.py:373:        if not isinstance(d, dict) or not d.get("exam_board_id"):
backend/app/models/snapshot_v3.py:375:        if len(str(d["exam_board_id"])) > _ID_MAX:
backend/app/models/snapshot_v3.py:379:                "exam_board_id": str(d["exam_board_id"]),
backend/app/models/snapshot_v3.py:381:                "qid": (str(d["qid"]) if d.get("qid") and len(str(d["qid"])) <= 40 else None),
backend/app/models/snapshot_v3.py:390:        "node_id": m["node_id"],
backend/app/models/snapshot_v3.py:430:            "board_id": str(bid),
backend/app/models/snapshot_v3.py:440:                if isinstance(m, dict) and _id_ok(m.get("node_id"))
backend/app/models/snapshot_v3.py:445:        if not isinstance(o, dict) or not _id_ok(o.get("node_id")):
backend/app/models/snapshot_v3.py:450:        orphans_out.append({"node_id": o["node_id"], "reason": slug})
backend/app/models/snapshot_v3.py:461:        if not isinstance(e, dict) or not e.get("exam_board_id"):
backend/app/models/snapshot_v3.py:463:        if len(str(e["exam_board_id"])) > _ID_MAX:
backend/app/models/snapshot_v3.py:467:                "exam_board_id": str(e["exam_board_id"]),
backend/app/models/snapshot_v3.py:468:                "board_id": (str(e["board_id"]) if e.get("board_id") and len(str(e["board_id"])) <= _ID_MAX else None),
scripts/migrate_chromadb_to_lancedb.py:212:                        "doc_id": results["ids"][i],
scripts/migrate_chromadb_to_lancedb.py:302:                        "doc_id": doc["doc_id"],
scripts/migrate_chromadb_to_lancedb.py:459:                            "doc_id": doc_id,
scripts/migrate_chromadb_to_lancedb.py:470:                            "doc_id": doc_id,
scripts/migrate_chromadb_to_lancedb.py:482:                            "doc_id": doc_id,
scripts/migrate_chromadb_to_lancedb.py:498:                            "doc_id": doc_id,
scripts/migrate_chromadb_to_lancedb.py:509:                        "doc_id": doc_id,
scripts/migrate_chromadb_to_lancedb.py:740:                    "doc_id": doc_id,
scripts/migrate_chromadb_to_lancedb.py:744:                    "node_id": metadata.get("node_id", ""),
scripts/migrate_chromadb_to_lancedb.py:799:                doc_id=doc["doc_id"],
scripts/migrate_chromadb_to_lancedb.py:862:                        "doc_id": doc_id,
scripts/migrate_chromadb_to_lancedb.py:877:                        "doc_id": doc_id,
backend/app/services/batch_orchestrator.py:149:            "task_id": self.session_id,
backend/app/services/batch_orchestrator.py:581:                "group_id": group.group_id,
backend/app/services/batch_orchestrator.py:758:                        "node_id": node_id,
backend/app/services/batch_orchestrator.py:798:                        "node_id": node_id,
backend/app/services/batch_orchestrator.py:833:                    "node_id": node_id,
backend/app/services/batch_orchestrator.py:894:                if node.get("id") == node_id:
backend/app/services/batch_orchestrator.py:1107:                            "node_id": nr.node_id,
backend/app/services/batch_orchestrator.py:1115:                            "node_id": nr.node_id,
backend/app/services/batch_orchestrator.py:1122:                    "group_id": gr.group_id,
backend/app/services/batch_orchestrator.py:1136:            "task_id": session_id,
backend/app/api/v1/endpoints/subjects.py:74:        ``{"group_id": 物理等值参数, "group_prefix": 物理前缀 + '__'}`` —
backend/app/api/v1/endpoints/subjects.py:99:    return {"group_id": physical, "group_prefix": f"{physical}__"}
backend/app/api/v1/endpoints/subjects.py:154:            id=rec["id"],
backend/app/api/v1/endpoints/subjects.py:293:    params: dict = {"subject_id": subject_id}
backend/app/api/v1/endpoints/subjects.py:334:        id=record["id"],
backend/app/api/v1/endpoints/subjects.py:390:            "subject_id": subject_id,
backend/app/core/exception_handlers.py:61:    request_id = getattr(request.state, "request_id", "unknown")
backend/app/core/exception_handlers.py:106:    request_id = getattr(request.state, "request_id", "unknown")
backend/app/core/exception_handlers.py:156:    request_id = getattr(request.state, "request_id", "unknown")
backend/app/core/exception_handlers.py:223:    request_id = getattr(request.state, "request_id", "unknown")
backend/app/core/exception_handlers.py:264:        "bug_id": bug_id,  # 用于用户反馈和问题追踪
backend/app/clients/neo4j_client.py:533:        user = next((u for u in self._data["users"] if u["id"] == user_id), None)
backend/app/clients/neo4j_client.py:535:            user = {"id": user_id, "created_at": datetime.now().isoformat()}
backend/app/clients/neo4j_client.py:545:                "id": concept_id,
backend/app/clients/neo4j_client.py:548:                "group_id": group_id,
backend/app/clients/neo4j_client.py:552:            concept_node["group_id"] = group_id
backend/app/clients/neo4j_client.py:562:                if r["user_id"] == user_id and r["concept_name"] == concept
backend/app/clients/neo4j_client.py:574:                rel["group_id"] = group_id
backend/app/clients/neo4j_client.py:578:                "id": f"learned-{len(self._data['relationships']) + 1}",
backend/app/clients/neo4j_client.py:579:                "user_id": user_id,
backend/app/clients/neo4j_client.py:580:                "concept_id": concept_node["id"],
backend/app/clients/neo4j_client.py:586:                "group_id": group_id,
backend/app/clients/neo4j_client.py:625:            if rel["user_id"] != user_id:
backend/app/clients/neo4j_client.py:641:                                "id": rel.get("concept_id", ""),
backend/app/clients/neo4j_client.py:648:                                "concept_id": concept.get("id", ""),
backend/app/clients/neo4j_client.py:680:            if user_id and rel["user_id"] != user_id:
backend/app/clients/neo4j_client.py:682:            if concept_id and rel.get("concept_id") != concept_id:
backend/app/clients/neo4j_client.py:687:                    "user_id": rel["user_id"],
backend/app/clients/neo4j_client.py:689:                    "concept_id": rel.get("concept_id"),
backend/app/clients/neo4j_client.py:762:        user_id = data.get("user_id", "unknown")
backend/app/clients/neo4j_client.py:765:        group_id = data.get("group_id")
backend/app/clients/neo4j_client.py:963:            if isinstance(record, dict) and record.get("group_id"):
backend/app/clients/neo4j_client.py:964:                record["group_id"] = desanitize_group_id_from_graphiti(
backend/app/clients/neo4j_client.py:965:                    record["group_id"]
backend/app/clients/neo4j_client.py:989:            if rel.get("user_id") != user_id:
backend/app/clients/neo4j_client.py:1018:                stored_gid = rel.get("group_id") or ""
backend/app/clients/neo4j_client.py:1028:                    "user_id": rel.get("user_id"),
backend/app/clients/neo4j_client.py:1030:                    "concept_id": rel.get("concept_id"),
backend/app/clients/neo4j_client.py:1035:                    "group_id": desanitize_group_id_from_graphiti(
backend/app/clients/neo4j_client.py:1036:                        rel.get("group_id") or ""
backend/app/clients/neo4j_client.py:1218:                rel.get("concept_id") == concept_id
backend/app/clients/neo4j_client.py:1220:                or rel.get("node_id") == concept_id
backend/app/clients/neo4j_client.py:1232:                record.get("concept_id") == concept_id
backend/app/clients/neo4j_client.py:1233:                or record.get("node_id") == concept_id
backend/app/clients/neo4j_client.py:1275:                    "concept_id": concept_id,
backend/app/clients/neo4j_client.py:1437:                if a.get("association_id") == association_id
backend/app/clients/neo4j_client.py:1457:                "association_id": association_id,
backend/app/clients/neo4j_client.py:1665:            a for a in associations if a.get("association_id") != association_id
backend/app/clients/neo4j_client.py:1777:            if assoc.get("association_id") == association_id:
backend/app/clients/neo4j_client.py:1999:                    "user_id": rel.get("user_id"),
backend/app/clients/neo4j_client.py:2001:                    "concept_id": rel.get("concept_id"),
backend/app/clients/neo4j_client.py:2004:                    "group_id": rel.get("group_id"),
backend/app/services/weight_calculator.py:92:            concept_id = concept.get("id", "")
backend/app/services/weight_calculator.py:136:            concept_id = record.get("concept_id") or record.get("node_id")
backend/app/services/weight_calculator.py:218:            concept_id=concept.get("id", ""),
scripts/generate-file-index.py:34:def scan_source_files():
scripts/generate-file-index.py:79:                    "operation_id": operation_id,
backend/app/services/mastery_engine.py:91:                    default_group_id=data.get("default_group_id", "default"),
backend/app/services/mastery_engine.py:196:                "concept_id": concept.concept_id,
backend/app/services/mastery_engine.py:492:                "concept_id": concept.concept_id,
backend/app/services/mastery_engine.py:650:        fsrs_due_date = None
backend/app/services/mastery_engine.py:657:                        fsrs_due_date = due.isoformat()
backend/app/services/mastery_engine.py:659:                        fsrs_due_date = due
backend/app/services/mastery_engine.py:685:            "concept_id": concept.concept_id,
backend/app/services/mastery_engine.py:694:            "fsrs_due_date": fsrs_due_date,
scripts/install-vault.sh:125:check "vault 配置 yaml"          'grep -q "vault_id" "$TARGET/.canvas-config.yaml"'
backend/app/services/graphiti_structured_writer.py:140:        attributes={**attributes, "node_id": node_id},
backend/app/services/graphiti_structured_writer.py:180:            "annotation_id": annotation_id or None,
backend/app/services/graphiti_structured_writer.py:280:            "node_id": source_node_id,  # 读侧按持有方 node 精确查
backend/app/services/graphiti_structured_writer.py:328:        aid = attrs.get("annotation_id")
backend/app/api/v1/endpoints/vault.py:140:                "error": "vaults_root_invalid",
backend/app/models/sync_models.py:91:            source = payload.get("source_node_id") or payload.get("sourceNodeId")
backend/app/models/sync_models.py:92:            target = payload.get("target_node_id") or payload.get("targetNodeId")
backend/app/models/sync_models.py:153:    @field_validator("vault_id")
backend/app/models/sync_models.py:176:    operation_id: str = Field(..., description="Matches the request operation_id")
backend/app/models/sync_models.py:183:    entity_id: str | None = Field(default=None, description="Echo of the request op's entity_id")
backend/app/services/difficulty_matcher.py:347:                    "node_id": node_id,
backend/app/services/sync_service.py:548:        source_node_id = payload.get("source_node_id") or payload.get("sourceNodeId")
backend/app/services/sync_service.py:549:        target_node_id = payload.get("target_node_id") or payload.get("targetNodeId")
scripts/trace/locate_by_bug.py:38:            if record.get("bug_id") == bug_id:
scripts/trace/locate_by_bug.py:54:            if record.get("request_id") == request_id:
scripts/trace/locate_by_bug.py:71:    request_id = bug.get("request_id", "")
scripts/trace/locate_by_bug.py:74:    story_id = bug.get("story_id") or infer_story_from_endpoint(bug.get("endpoint", ""))
scripts/trace/locate_by_bug.py:85:            "bug_id": bug.get("bug_id"),
scripts/trace/locate_by_bug.py:90:            "request_id": request_id,
scripts/trace/locate_by_bug.py:91:            "story_id": story_id,
scripts/trace/locate_by_bug.py:95:                "decision_id": d.get("decision_id"),
backend/app/api/v1/endpoints/context.py:145:        node_name=tier1_raw.get("node_name", ctx.get("node_id", "")),
backend/app/api/v1/endpoints/context.py:157:        node_id=ctx.get("node_id", ""),
backend/app/services/canvas_service.py:148:                "node_id": node_id,
backend/app/services/canvas_service.py:149:                "edge_id": edge_id,
backend/app/services/canvas_service.py:151:                "session_id": self._session_id,
backend/app/services/canvas_service.py:554:                request_id=_ctx.get("request_id"),
backend/app/services/canvas_service.py:614:                        edge_id=edge["id"],
backend/app/services/canvas_service.py:793:        node_id = node_data.get("id") or str(uuid.uuid4())[:8]
backend/app/services/canvas_service.py:794:        new_node = {"id": node_id, **node_data}
backend/app/services/canvas_service.py:817:            node_id=new_node["id"],
backend/app/services/canvas_service.py:822:        self._trigger_lancedb_index(canvas_name, node_id=new_node["id"])
backend/app/services/canvas_service.py:852:            if node.get("id") == node_id:
backend/app/services/canvas_service.py:854:                updated_node = {**node, **node_data, "id": node_id}
backend/app/services/canvas_service.py:893:            n for n in canvas_data["nodes"] if n.get("id") != node_id
backend/app/services/canvas_service.py:951:        edge_id = edge_data.get("id") or str(uuid.uuid4())[:8]
backend/app/services/canvas_service.py:952:        new_edge = {"id": edge_id, **edge_data}
backend/app/services/canvas_service.py:964:            edge_id=new_edge["id"],
backend/app/services/canvas_service.py:978:                    edge_id=new_edge["id"],
backend/app/services/canvas_service.py:1012:            e for e in canvas_data.get("edges", []) if e.get("id") != edge_id
backend/app/services/canvas_service.py:1105:                    if node.get("id") == node_id:
backend/app/models/common.py:83:                    "details": {"field": "node_id", "reason": "Invalid format"},
scripts/daily-review-push.sh:4:# 固定解释器调 runner。业务逻辑全在 daily_review_run.py (--now 可测)。
scripts/daily-review-push.sh:9:LOCK="$REPO/backups/.daily-review.lock"
scripts/daily-review-push.sh:31:"$PY" "$WT/scripts/daily_review_run.py" "$@"
backend/app/services/exam_service.py:454:                id=data.get("uuid", ""),
backend/app/services/exam_service.py:455:                source_canvas_id=data.get("source_board_id", ""),
backend/app/services/exam_service.py:461:                target_node_id=data.get("target_node_id") or None,
backend/app/services/exam_service.py:462:                current_node_id=data.get("current_node_id") or None,
backend/app/models/memory_schemas.py:72:                "user_id": "user-123",
backend/app/models/memory_schemas.py:74:                "node_id": "node-abc123",
backend/app/models/memory_schemas.py:79:                "vault_id": "cs_61b",
backend/app/models/memory_schemas.py:101:            "example": {"episode_id": "episode-a1b2c3d4e5f67890", "status": "created"}
backend/app/models/memory_schemas.py:155:                        "episode_id": "episode-a1b2c3d4e5f67890",
backend/app/models/memory_schemas.py:156:                        "user_id": "user-123",
backend/app/models/memory_schemas.py:158:                        "node_id": "node-abc123",
backend/app/models/memory_schemas.py:225:                "concept_id": "concept-123",
backend/app/models/memory_schemas.py:230:                        "user_id": "user-123",
backend/app/models/memory_schemas.py:408:                        "node_id": "b33c50660173e5d3",
backend/app/models/memory_schemas.py:503:                "concept_id": "concept-123",
scripts/trace/build_story_file_map.py:40:def scan_story_files() -> dict[str, list[str]]:
scripts/trace/build_story_file_map.py:56:def scan_git_trailers() -> dict[str, set[str]]:
backend/app/models/session_models.py:101:            "node_id": self.node_id,
backend/app/models/session_models.py:161:            "session_id": self.session_id,
backend/app/services/supplementary_search_service.py:830:            query_type="hybrid",
backend/app/services/supplementary_search_service.py:876:            _active_vault_id = getattr(_gs(), "vault_id", "") or ""
backend/app/services/supplementary_search_service.py:944:                    "doc_id": str(row.get("doc_id", "") or ""),
backend/app/services/supplementary_search_service.py:1029:        doc_id = raw.get("doc_id", "") or ""
backend/app/services/error_writer.py:95:        "id": candidate_id,
backend/app/services/error_writer.py:101:        "node_id": node_id,
backend/app/services/error_writer.py:102:        "session_id": session_id,
backend/app/services/error_writer.py:103:        "group_id": group_id,
backend/app/services/error_writer.py:211:            existing_id = existing.get("id") or candidate_id or str(uuid.uuid4())
backend/app/services/error_writer.py:212:            existing["id"] = existing_id
backend/app/services/error_writer.py:406:            existing_id = existing.get("id") or error_id or str(uuid.uuid4())
backend/app/services/error_writer.py:407:            existing["id"] = existing_id
backend/app/services/error_writer.py:420:                "id": error_id,
backend/app/services/error_writer.py:563:                    hint="Story 2.5.Y AC #3: 调用方应通过 ContextVar 或参数传入 group_id",
backend/app/services/error_writer.py:577:        "misconception_id": error_id,  # Story 2.5 HIGH#10 fix — 与 frontmatter id 关联
backend/app/services/error_writer.py:586:        "node_id": node_id,
backend/app/services/error_writer.py:587:        "session_id": session_id,
backend/app/services/error_writer.py:685:          "candidate_id": str | None,
backend/app/services/error_writer.py:692:          "error_id": str | None,
backend/app/services/error_writer.py:712:                "candidate_id": None,
backend/app/services/error_writer.py:718:            "candidate_id": candidate_id,
backend/app/services/error_writer.py:731:            "error_id": None,
backend/app/services/error_writer.py:747:            "error_id": error_id,
backend/app/services/error_writer.py:757:        "error_id": error_id,
backend/app/services/recommendation_service.py:149:        unconnected_ids = [n["id"] for n in unconnected]
backend/app/services/recommendation_service.py:258:                            source_node_id=rec["source_id"],
backend/app/services/recommendation_service.py:259:                            target_node_id=rec["target_id"],
backend/app/services/recommendation_service.py:280:                titles[rec["id"]] = rec.get("title") or "未命名"
backend/app/services/recommendation_service.py:351:                                source_node_id=nodes[i]["id"],
backend/app/services/recommendation_service.py:352:                                target_node_id=nodes[j]["id"],
backend/app/services/recommendation_service.py:389:                            source_node_id=nodes[i]["id"],
backend/app/services/recommendation_service.py:390:                            target_node_id=nodes[j]["id"],
backend/app/services/lancedb_index_service.py:391:                entry["trigger_node_id"] = trigger_node_id
backend/app/models/schemas.py:148:                "association_id": "cca-a1b2c3d4e5f6",
backend/app/api/v1/endpoints/chat.py:711:            err_id = dual.get("candidate_id") or dual.get("error_id")
backend/app/services/question_generator.py:184:        valid_nodes = [(node, node.get("id", "")) for node in nodes]
backend/app/services/question_generator.py:1207:            node_id = node.get("id", "")
scripts/validate-merge-ready.py:101:        "story_id": story_id,
backend/app/api/v1/endpoints/tips.py:235:            tip_id = metadata.get("tip_id")
backend/app/api/v1/endpoints/tips.py:236:            if metadata.get("node_id") == node_id and tip_id:
backend/app/api/v1/endpoints/tips.py:304:                "tip_id": tip_id,
backend/app/api/v1/endpoints/tips.py:308:                "node_id": request.node_id,
backend/app/api/v1/endpoints/tips.py:309:                "annotation_id": request.annotation_id,
backend/app/api/v1/endpoints/tips.py:356:                "node_id": request.source_node_id,
backend/app/api/v1/endpoints/tips.py:357:                "target_node_id": request.target_node_id,
backend/app/api/v1/endpoints/tips.py:460:                        "tip_id": tip_id,
backend/app/api/v1/endpoints/tips.py:465:                        "node_id": request.node_id,
backend/app/api/v1/endpoints/tips.py:466:                        "annotation_id": callout.annotation_id,
backend/app/api/v1/endpoints/tips.py:600:                "node_id": request.node_id,
backend/app/api/v1/endpoints/tips.py:601:                "callout_id": request.callout_id,
backend/app/models/subject_models.py:72:                "id": "subj_a1b2c3",
scripts/test-agent-endpoint.py:76:    "node_id": "test-node-001",
scripts/test-agent-endpoint.py:135:            bug_id = data.get("bug_id", "")
backend/app/models/mastery_state.py:114:            "mastery_concept_id": self.concept_id,
backend/app/models/mastery_state.py:152:            concept_id=props.get("mastery_concept_id", props.get("name", "")),
backend/app/mcp/pipeline_token.py:100:            "sid": session_id,
backend/app/mcp/pipeline_token.py:101:            "nid": node_id,
backend/app/mcp/pipeline_token.py:106:            payload["qid"] = question_id
backend/app/mcp/pipeline_token.py:192:            session_id=payload.get("sid", ""),
backend/app/mcp/pipeline_token.py:193:            node_id=payload.get("nid", ""),
backend/app/mcp/pipeline_token.py:196:            question_id=payload.get("qid"),
backend/app/models/rollback.py:76:                "id": "550e8400-e29b-41d4-a716-446655440000",
backend/app/models/rollback.py:80:                "user_id": "system",
backend/app/models/rollback.py:83:                    "after": {"id": "node1", "text": "逆否命题", "color": "1"},
backend/app/models/rollback.py:89:                    "agent_id": "basic-decomposition",
backend/app/models/rollback.py:90:                    "request_id": "req-123",
backend/app/models/rollback.py:120:                        "id": "550e8400-e29b-41d4-a716-446655440000",
backend/app/models/rollback.py:124:                        "user_id": "system",
backend/app/models/rollback.py:127:                            "after": {"id": "node1", "text": "逆否命题"},
backend/app/models/rollback.py:133:                            "agent_id": "basic-decomposition",
backend/app/models/rollback.py:134:                            "request_id": None,
backend/app/api/v1/endpoints/agents.py:460:        if node.get("id") == node_id:
backend/app/api/v1/endpoints/agents.py:710:                "node_id": node_id,
backend/app/api/v1/endpoints/agents.py:1092:                    node_id=score_data.get("node_id", ""),
backend/app/api/v1/endpoints/agents.py:1114:                node_id=score_data.get("node_id", first_node_id),
backend/app/api/v1/endpoints/agents.py:1363:            created_node_id=result.get("created_node_id", ""),
backend/app/api/v1/endpoints/agents.py:1733:                source_node_id=q.get("source_node_id", request.node_id),
backend/app/api/v1/endpoints/index.py:113:    return {"vault_id": vault_id, "tables_dropped": dropped}
backend/app/api/v1/endpoints/intelligent_parallel.py:402:                    "details": {"session_id": session_id},
backend/app/api/v1/endpoints/intelligent_parallel.py:484:                    "details": {"session_id": session_id},
backend/app/api/v1/endpoints/intelligent_parallel.py:497:                "details": {"session_id": session_id},
backend/app/api/v1/endpoints/intelligent_parallel.py:572:                    "node_id": request.node_id,
backend/app/api/v1/endpoints/profile.py:69:    fsrs_due_date: Optional[str] = None
backend/app/api/v1/endpoints/profile.py:172:            fsrs_due_date=None,
backend/app/api/v1/endpoints/profile.py:196:        fsrs_due_date=resp.get("fsrs_due_date"),
backend/app/api/v1/endpoints/profile.py:249:                    tip_id=data.get("tip_id", ""),
backend/app/api/v1/endpoints/profile.py:256:                    source_canvas_id=data.get("source_canvas_id") or None,
backend/app/api/v1/endpoints/profile.py:257:                    source_node_id=data.get("source_node_id") or None,
backend/app/api/v1/endpoints/profile.py:319:                    source_canvas_id=data.get("source_canvas_id") or None,
backend/app/api/v1/endpoints/profile.py:320:                    source_node_id=data.get("source_node_id") or None,
scripts/daemon/post_process_hook.py:294:        "--story-id",
scripts/daemon/post_process_hook.py:308:        "--session-id",
scripts/daemon/linear_session_spawner.py:113:  "story_id": "{story_id}",
scripts/daemon/linear_progress.py:173:            "session_id": self.session_id,
scripts/daemon/linear_progress.py:174:            "daemon_pid": self.daemon_pid,
scripts/daemon/linear_progress.py:192:            session_id=data.get("session_id", ""),
scripts/daemon/linear_progress.py:193:            daemon_pid=data.get("daemon_pid"),
backend/app/mcp/tools/memory_tools.py:286:            "node_id": node_id,
backend/app/mcp/tools/memory_tools.py:287:            "session_id": session_id,
backend/app/mcp/tools/memory_tools.py:413:                "node_id": node_id,
backend/app/mcp/tools/memory_tools.py:416:                "source_session_id": source_session_id,
backend/app/mcp/tools/memory_tools.py:417:                "source_canvas_id": source_canvas_id,
scripts/daemon/worktree_scanner.py:56:    def scan(self) -> List[WorktreeInfo]:
backend/app/mcp/tools/error_tools.py:231:            misconception_id = dual_result.get("error_id")
scripts/daemon/story_file_updater.py:32:            "story_id": self.story_id,
scripts/daemon/story_file_updater.py:381:        story_id = result.get("story_id", "unknown")
scripts/daemon/story_file_updater.py:437:        "story_id": "12.5",
scripts/daemon/qa_spawner.py:42:            "story_id": self.story_id,
scripts/daemon/qa_gate_generator.py:29:            "story_id": self.story_id,
scripts/daemon/qa_gate_generator.py:169:                    "id": f"ISSUE-{i+1:03d}",
scripts/daemon/qa_gate_generator.py:176:                    "id": f"ISSUE-{i+1:03d}",
scripts/daemon/qa_gate_generator.py:360:        "story_id": "12.5",
backend/app/mcp/tools/conversation_tools.py:163:                "archive_id": archive_id,
backend/app/mcp/tools/conversation_tools.py:164:                "node_id": node_id,
backend/app/mcp/tools/conversation_tools.py:165:                "session_id": session_id,
backend/app/mcp/tools/conversation_tools.py:254:                "id": exam_node_id,
backend/app/mcp/tools/conversation_tools.py:270:                "id": edge_id,
backend/app/mcp/tools/conversation_tools.py:288:                    "exam_node_id": exam_node_id,
backend/app/mcp/tools/conversation_tools.py:289:                    "source_node_id": source_node_id,
backend/app/mcp/tools/conversation_tools.py:290:                    "canvas_id": canvas_id,
backend/app/mcp/tools/conversation_tools.py:291:                    "edge_id": edge_id,
backend/app/api/v1/endpoints/review.py:106:# frontmatter fsrs_due (写侧 quiz-answer × fsrs_bridge, 读侧 daily_review_pick)。
backend/app/api/v1/endpoints/review.py:269:        nodes_to_review: List of canvas node dicts (must have "id" and "text")
backend/app/api/v1/endpoints/review.py:290:            node_id = node.get("id", "")
backend/app/api/v1/endpoints/review.py:416:            node_id = node.get("id", "")
backend/app/api/v1/endpoints/review.py:424:                "id": node_id,
backend/app/api/v1/endpoints/review.py:456:                src_id = q.get("source_node_id", "")
backend/app/api/v1/endpoints/review.py:553:        return [n for n in source_nodes if n.get("id") in node_id_set]
backend/app/api/v1/endpoints/review.py:699:                        concept_id=review.get("concept_id", ""),
backend/app/api/v1/endpoints/review.py:849:            if not (n.get("id") in difficulty_map and difficulty_map[n.get("id")].is_mastered)
backend/app/api/v1/endpoints/review.py:912:            "id": group_id,
backend/app/api/v1/endpoints/review.py:934:            source_id = source_node.get("id", "")
backend/app/api/v1/endpoints/review.py:953:                "id": question_node_id,
backend/app/api/v1/endpoints/review.py:967:                "id": answer_node_id,
backend/app/api/v1/endpoints/review.py:980:                "id": _generate_node_id(),
backend/app/api/v1/endpoints/review.py:1327:                    question_id=record.get("question_id", ""),
backend/app/api/v1/endpoints/review.py:1505:            session_id=progress_dict["session_id"],
backend/app/api/v1/endpoints/review.py:1717:            session_id=result["session_id"],
backend/app/api/v1/endpoints/review.py:1792:            session_id=progress_data["session_id"],
backend/app/mcp/tools/exam_tools.py:523:                        "node_id": node_id,
backend/app/mcp/tools/exam_tools.py:524:                        "session_id": session_id,
backend/app/mcp/tools/exam_tools.py:647:                            n.get("id"): n for n in canvas_data.get("nodes", [])
scripts/daemon/tests/test_story_file_updater.py:28:            "story_id": "15.1",
scripts/daemon/tests/test_story_file_updater.py:271:        assert d["story_id"] == "15.1"
backend/app/api/v1/endpoints/monitoring.py:59:                "id": "abc123def456",
backend/app/api/v1/endpoints/mastery_ws.py:18:    "node_id": "abc-123",
backend/app/api/v1/endpoints/mastery_ws.py:126:            "node_id": payload.get("node_id", ""),
backend/app/api/v1/endpoints/exam.py:324:    return {"exam_id": exam_id, "elapsed_minutes": elapsed_minutes, "message": message}
backend/app/api/v1/endpoints/rollback.py:281:        id=entry["id"],
backend/app/api/v1/endpoints/rollback.py:285:        last_operation_id=entry.get("last_operation_id"),
backend/app/api/v1/endpoints/rollback.py:624:    snapshot_nodes = {n.get("id"): n for n in snapshot_data.get("nodes", [])}
backend/app/api/v1/endpoints/rollback.py:625:    current_nodes = {n.get("id"): n for n in current_data.get("nodes", [])}
backend/app/api/v1/endpoints/rollback.py:636:                    "id": node_id,
backend/app/api/v1/endpoints/rollback.py:647:                    "id": node_id,
backend/app/api/v1/endpoints/rollback.py:670:                    "id": node_id,
backend/app/api/v1/endpoints/rollback.py:677:    snapshot_edges = {e.get("id"): e for e in snapshot_data.get("edges", [])}
backend/app/api/v1/endpoints/rollback.py:678:    current_edges = {e.get("id"): e for e in current_data.get("edges", [])}
backend/app/api/v1/endpoints/rollback.py:688:                    "id": edge_id,
backend/app/api/v1/endpoints/rollback.py:699:                    "id": edge_id,
backend/app/api/v1/system.py:466:                    "id": p.plugin_id,
backend/app/api/v1/system.py:1088:        "data": {"status": "ok", "record_id": record_id, "annotation": body.annotation},
backend/app/api/v1/system.py:1159:        "data": {"status": "deleted", "record_id": record_id},
backend/app/api/v1/system.py:1194:        "data": {"status": "ok", "record_id": record_id, "annotation": None},
backend/app/api/v1/endpoints/mastery.py:255:                "node_id": concept.concept_id,
backend/app/api/v1/endpoints/mastery.py:539:        "node_id": concept_id,
scripts/daemon/tests/test_post_process_hook.py:25:            "story_id": "15.1",
scripts/daemon/tests/test_post_process_hook.py:166:        assert data["story_id"] == "15.1"
scripts/daemon/tests/test_post_process_hook.py:349:        assert d["story_id"] == "15.1"
scripts/daemon/tests/test_post_process_hook.py:350:        assert d["session_id"] == "test"
scripts/daemon/tests/test_post_process_hook.py:405:                "story_id": "15.1",
backend/app/api/v1/endpoints/edges.py:109:                "record_id": record_id,
backend/app/api/v1/endpoints/edges.py:110:                "edge_id": rationale.edge_id,
backend/app/api/v1/endpoints/edges.py:111:                "source_node_id": rationale.source_node_id,
backend/app/api/v1/endpoints/edges.py:112:                "target_node_id": rationale.target_node_id,
backend/app/api/v1/endpoints/edges.py:123:                "group_id": to_physical_group_id(resolved_group_id),
backend/app/api/v1/endpoints/edges.py:173:            "record_id": record_id,
backend/app/api/v1/endpoints/edges.py:174:            "edge_id": rationale.edge_id,
backend/app/api/v1/endpoints/edges.py:175:            "source_node_id": rationale.source_node_id,
backend/app/api/v1/endpoints/edges.py:176:            "target_node_id": rationale.target_node_id,
scripts/daemon/tests/test_qa_gate_generator.py:30:            "story_id": "12.5",
scripts/daemon/tests/test_qa_gate_generator.py:57:            "story_id": "12.6",
scripts/daemon/tests/test_qa_gate_generator.py:70:            "story_id": "12.7",
scripts/daemon/tests/test_qa_gate_generator.py:243:            bad_result = {"invalid": "data"}
scripts/daemon/tests/test_qa_gate_generator.py:267:            "story_id": "12.8",
scripts/daemon/tests/test_qa_gate_generator.py:283:            "story_id": "12.9",
scripts/daemon/tests/test_qa_gate_generator.py:340:        assert d["story_id"] == "12.5"
backend/app/api/v1/endpoints/exam_sessions.py:59:    source_node: str = Field(description="错误来源节点 id")
backend/app/api/v1/endpoints/exam_sessions.py:151:        board_filter = "AND e.source_board_id = $board_id"
backend/app/api/v1/endpoints/exam_sessions.py:170:    params: dict = {"group_id": group_id}
backend/app/api/v1/endpoints/exam_sessions.py:172:        params["board_id"] = board_id
backend/app/api/v1/endpoints/exam_sessions.py:182:                    id=data.get("id", ""),
backend/app/api/v1/endpoints/exam_sessions.py:183:                    source_board_id=data.get("source_board_id", ""),
backend/app/api/v1/endpoints/memory.py:258:                episode_id=item.get("episode_id") or "",
backend/app/api/v1/endpoints/memory.py:259:                user_id=item.get("user_id") or "",
backend/app/api/v1/endpoints/memory.py:261:                node_id=item.get("node_id") or "",
backend/app/api/v1/endpoints/memory.py:397:                concept_id=s.get("concept_id", ""),
backend/app/api/v1/endpoints/memory.py:485:                "node_id": event.node_id,
backend/app/api/v1/endpoints/memory.py:666:                    "node_id": request.node_id,
backend/app/api/v1/endpoints/memory.py:679:                    "node_id": request.node_id,
backend/app/api/v1/endpoints/memory.py:822:                "group_id": resolved_group_id,

exec
/bin/zsh -lc "rg -n -C 5 \"daily_review_run|flock|mkdir|lock|ACTIVE_VAULT|launchd\" scripts --glob '*.sh' --glob '*.py' --glob '*.plist'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
scripts/verify-sdd-coverage.py-452-**Report generated by**: scripts/verify-sdd-coverage.py
scripts/verify-sdd-coverage.py-453-**Reference**: Section 16.5.1 of planning document
scripts/verify-sdd-coverage.py-454-"""
scripts/verify-sdd-coverage.py-455-
scripts/verify-sdd-coverage.py-456-        if output_path:
scripts/verify-sdd-coverage.py:457:            output_path.parent.mkdir(parents=True, exist_ok=True)
scripts/verify-sdd-coverage.py-458-            with open(output_path, 'w', encoding='utf-8') as f:
scripts/verify-sdd-coverage.py-459-                f.write(report)
scripts/verify-sdd-coverage.py-460-            print(f"\nReport saved to: {output_path}")
scripts/verify-sdd-coverage.py-461-
scripts/verify-sdd-coverage.py-462-        return report
--
scripts/shard-architecture.py-51-    path = Path(filepath)
scripts/shard-architecture.py-52-    content = path.read_text(encoding='utf-8')
scripts/shard-architecture.py-53-
scripts/shard-architecture.py-54-    base_name = path.stem
scripts/shard-architecture.py-55-    shard_dir = Path(output_dir) / base_name.lower()
scripts/shard-architecture.py:56:    shard_dir.mkdir(parents=True, exist_ok=True)
scripts/shard-architecture.py-57-
scripts/shard-architecture.py-58-    sections = extract_sections(content)
scripts/shard-architecture.py-59-
scripts/shard-architecture.py-60-    # Group small sections together
scripts/shard-architecture.py-61-    shards = []
--
scripts/daily_review_run.py-1-#!/usr/bin/env python3
scripts/daily_review_run.py-2-"""每日复习推送编排 runner (DAILY-REVIEW-PUSH-2026-07-29, 终审 A4/A7 硬化版)。
scripts/daily_review_run.py-3-
scripts/daily_review_run.py-4-顺序铁律: md/json 先落盘(保底) → 窗口内 Bark → 失败 osascript 兜底。
scripts/daily_review_run.py:5:壳层 daily-review-push.sh 只负责 mkdir 锁 + 固定解释器; 业务全在此处
scripts/daily_review_run.py-6-(可 --now 注入时间跑 12 场景验收矩阵)。
scripts/daily_review_run.py-7-
scripts/daily_review_run.py-8-终审修正落点:
scripts/daily_review_run.py-9-  A4: 时间门 9:05 ≤ 本地时间 < 21:00 (RunAtLoad 早触发只生成不推;
scripts/daily_review_run.py-10-      唤醒补跑窗口内补推; 过窗只落盘) · state JSON 原子写 (os.replace)
--
scripts/daily_review_run.py-28-sys.path.insert(0, str(Path(__file__).resolve().parent))
scripts/daily_review_run.py-29-import send_bark  # noqa: E402
scripts/daily_review_run.py-30-
scripts/daily_review_run.py-31-REPO = Path(os.environ.get("CANVAS_REPO", "/Users/Heishing/Desktop/canvas/canvas-learning-system"))
scripts/daily_review_run.py-32-# VAULT-SYNC (2026-08-02): 默认值仅作兜底 — 生产链由 wrapper 从 .env
scripts/daily_review_run.py:33:# ACTIVE_VAULT 解析后经 --vault 传入, 与后端同源 (换 vault 只改 .env 一处)
scripts/daily_review_run.py-34-VAULT = REPO / "canvas-vault"
scripts/daily_review_run.py-35-STATE = REPO / "backups" / "daily-review.state.json"
scripts/daily_review_run.py-36-LOG = REPO / "backups" / "daily-review.log"
scripts/daily_review_run.py-37-
scripts/daily_review_run.py-38-PUSH_WINDOW = (dtime(9, 5), dtime(21, 0))
--
scripts/daily_review_run.py-68-        print(f"[runner] state 损坏, 已隔离到 {quarantine.name}, 重建", file=sys.stderr)
scripts/daily_review_run.py-69-        return {"schema_version": 1, "board_last_recommended": {}}
scripts/daily_review_run.py-70-
scripts/daily_review_run.py-71-
scripts/daily_review_run.py-72-def save_state(st: dict):
scripts/daily_review_run.py:73:    STATE.parent.mkdir(parents=True, exist_ok=True)
scripts/daily_review_run.py-74-    tmp = STATE.with_suffix(".tmp")
scripts/daily_review_run.py-75-    tmp.write_text(json.dumps(st, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
scripts/daily_review_run.py-76-    os.replace(tmp, STATE)
scripts/daily_review_run.py-77-
scripts/daily_review_run.py-78-
scripts/daily_review_run.py-79-def log_line(msg: str):
scripts/daily_review_run.py:80:    LOG.parent.mkdir(parents=True, exist_ok=True)
scripts/daily_review_run.py-81-    stamp = datetime.now().astimezone().strftime("%F %T")
scripts/daily_review_run.py-82-    with open(LOG, "a", encoding="utf-8") as f:
scripts/daily_review_run.py-83-        f.write(f"[{stamp}] {msg}\n")
scripts/daily_review_run.py-84-
scripts/daily_review_run.py-85-
--
scripts/daily_review_run.py-129-
scripts/daily_review_run.py-130-    scan_started = time.time()
scripts/daily_review_run.py-131-    payload, ranked = picker.build_payload(
scripts/daily_review_run.py-132-        VAULT, now, st["board_last_recommended"], picker.load_decay(VAULT))
scripts/daily_review_run.py-133-    out = VAULT / "outputs"
scripts/daily_review_run.py:134:    out.mkdir(parents=True, exist_ok=True)
scripts/daily_review_run.py-135-    picker.atomic_write(out / "今日复习.md", picker.render_md(payload, ranked))
scripts/daily_review_run.py-136-    raw = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
scripts/daily_review_run.py-137-    picker.atomic_write(payload_path, raw)
scripts/daily_review_run.py-138-    # mtime 门基准回拨到扫描起点: 扫描-落盘窗口内落地的写侧更新, 其 mtime
scripts/daily_review_run.py-139-    # 必然 > 基准, 下一轮触发重扫捞回 (否则该更新当天静默丢失, 无日志可查)
--
scripts/daily_review_run.py-162-
scripts/daily_review_run.py-163-def main() -> int:
scripts/daily_review_run.py-164-    global VAULT
scripts/daily_review_run.py-165-    ap = argparse.ArgumentParser(description="每日复习推送编排")
scripts/daily_review_run.py-166-    ap.add_argument("--now", help="ISO 时间覆盖 (12 场景验收矩阵用)")
scripts/daily_review_run.py:167:    ap.add_argument("--vault", help="活 vault 路径 (wrapper 从 .env ACTIVE_VAULT 解析传入; 缺省回退 canvas-vault)")
scripts/daily_review_run.py-168-    args = ap.parse_args()
scripts/daily_review_run.py-169-
scripts/daily_review_run.py-170-    if args.vault:
scripts/daily_review_run.py-171-        VAULT = Path(args.vault)
scripts/daily_review_run.py-172-
--
scripts/backup-neo4j.sh-13-CONTAINER="canvas-learning-system-neo4j"
scripts/backup-neo4j.sh-14-IMAGE="neo4j:5.26-community"
scripts/backup-neo4j.sh-15-STAMP="$(date +%Y%m%d-%H%M%S)"
scripts/backup-neo4j.sh-16-LOG="$BACKUP_DIR/backup.log"
scripts/backup-neo4j.sh-17-
scripts/backup-neo4j.sh:18:mkdir -p "$BACKUP_DIR"
scripts/backup-neo4j.sh-19-
scripts/backup-neo4j.sh-20-if ! docker info >/dev/null 2>&1; then
scripts/backup-neo4j.sh-21-    echo "[$(date '+%F %T')] SKIP: docker daemon 不可用" >> "$LOG"
scripts/backup-neo4j.sh-22-    exit 0
scripts/backup-neo4j.sh-23-fi
--
scripts/extract-sdd-requirements.py-376-        return md
scripts/extract-sdd-requirements.py-377-
scripts/extract-sdd-requirements.py-378-    def save_index(self, output_file: Path):
scripts/extract-sdd-requirements.py-379-        """保存索引到文件"""
scripts/extract-sdd-requirements.py-380-        # 确保输出目录存在
scripts/extract-sdd-requirements.py:381:        output_file.parent.mkdir(parents=True, exist_ok=True)
scripts/extract-sdd-requirements.py-382-
scripts/extract-sdd-requirements.py-383-        md_content = self.generate_index_markdown()
scripts/extract-sdd-requirements.py-384-
scripts/extract-sdd-requirements.py-385-        with open(output_file, 'w', encoding='utf-8') as f:
scripts/extract-sdd-requirements.py-386-            f.write(md_content)
--
scripts/spec-tools/export-openapi.py-43-    schema["info"]["x-generated-at"] = datetime.now(timezone.utc).isoformat()
scripts/spec-tools/export-openapi.py-44-    schema["info"]["x-generator"] = "Canvas Learning System OpenAPI Exporter"
scripts/spec-tools/export-openapi.py-45-
scripts/spec-tools/export-openapi.py-46-    # Ensure output directory exists
scripts/spec-tools/export-openapi.py-47-    output = Path(output_path)
scripts/spec-tools/export-openapi.py:48:    output.parent.mkdir(parents=True, exist_ok=True)
scripts/spec-tools/export-openapi.py-49-
scripts/spec-tools/export-openapi.py-50-    if format_type == "yaml":
scripts/spec-tools/export-openapi.py-51-        try:
scripts/spec-tools/export-openapi.py-52-            import yaml
scripts/spec-tools/export-openapi.py-53-            with open(output, "w", encoding="utf-8") as f:
--
scripts/spec-tools/export-json-schemas.py-149-    Export all Pydantic models to JSON Schema files.
scripts/spec-tools/export-json-schemas.py-150-
scripts/spec-tools/export-json-schemas.py-151-    Returns:
scripts/spec-tools/export-json-schemas.py-152-        Tuple of (success_count, error_count, results)
scripts/spec-tools/export-json-schemas.py-153-    """
scripts/spec-tools/export-json-schemas.py:154:    output_dir.mkdir(parents=True, exist_ok=True)
scripts/spec-tools/export-json-schemas.py-155-
scripts/spec-tools/export-json-schemas.py-156-    discovered = discover_pydantic_models()
scripts/spec-tools/export-json-schemas.py-157-    success = 0
scripts/spec-tools/export-json-schemas.py-158-    errors = 0
scripts/spec-tools/export-json-schemas.py-159-    results = []
--
scripts/spec-tools/api-reality-dashboard.py-248-    if args.compare:
scripts/spec-tools/api-reality-dashboard.py-249-        compare_with_epic(spec, args.compare)
scripts/spec-tools/api-reality-dashboard.py-250-    elif args.export:
scripts/spec-tools/api-reality-dashboard.py-251-        md_content = export_markdown(spec)
scripts/spec-tools/api-reality-dashboard.py-252-        output_path = PROJECT_ROOT / "docs" / "api" / "API-REALITY-DASHBOARD.md"
scripts/spec-tools/api-reality-dashboard.py:253:        output_path.parent.mkdir(parents=True, exist_ok=True)
scripts/spec-tools/api-reality-dashboard.py-254-        output_path.write_text(md_content, encoding='utf-8')
scripts/spec-tools/api-reality-dashboard.py-255-        print(f"  {color(f'Exported to {output_path}', Colors.GREEN)}")
scripts/spec-tools/api-reality-dashboard.py-256-    else:
scripts/spec-tools/api-reality-dashboard.py-257-        print_dashboard(spec)
scripts/spec-tools/api-reality-dashboard.py-258-
--
scripts/spec-tools/finalize-iteration.py-169-def update_changelog(project_root: Path, story_id: Optional[str], changes: str) -> bool:
scripts/spec-tools/finalize-iteration.py-170-    """Update API changelog"""
scripts/spec-tools/finalize-iteration.py-171-    changelog_path = project_root / "specs" / "api" / "versions" / "CHANGELOG.md"
scripts/spec-tools/finalize-iteration.py-172-
scripts/spec-tools/finalize-iteration.py-173-    if not changelog_path.parent.exists():
scripts/spec-tools/finalize-iteration.py:174:        changelog_path.parent.mkdir(parents=True, exist_ok=True)
scripts/spec-tools/finalize-iteration.py-175-
scripts/spec-tools/finalize-iteration.py-176-    today = datetime.now().strftime("%Y-%m-%d")
scripts/spec-tools/finalize-iteration.py-177-
scripts/spec-tools/finalize-iteration.py-178-    entry = f"""
scripts/spec-tools/finalize-iteration.py-179-## [{today}] - Story {story_id or 'N/A'}
--
scripts/verify-adr-coverage.py-415-**Report generated by**: scripts/verify-adr-coverage.py
scripts/verify-adr-coverage.py-416-**Reference**: Section 16.5.2 of planning document
scripts/verify-adr-coverage.py-417-"""
scripts/verify-adr-coverage.py-418-
scripts/verify-adr-coverage.py-419-        if output_path:
scripts/verify-adr-coverage.py:420:            output_path.parent.mkdir(parents=True, exist_ok=True)
scripts/verify-adr-coverage.py-421-            with open(output_path, 'w', encoding='utf-8') as f:
scripts/verify-adr-coverage.py-422-                f.write(report)
scripts/verify-adr-coverage.py-423-            print(f"\nReport saved to: {output_path}")
scripts/verify-adr-coverage.py-424-
scripts/verify-adr-coverage.py-425-        return report
--
scripts/memory-health.sh-4-set -uo pipefail
scripts/memory-health.sh-5-
scripts/memory-health.sh-6-REPO="/Users/Heishing/Desktop/canvas/canvas-learning-system"
scripts/memory-health.sh-7-WT="$REPO/.claude/worktrees/feature-obsidian-hybrid-dev"
scripts/memory-health.sh-8-OUT="$REPO/backups/memory-health.log"
scripts/memory-health.sh:9:mkdir -p "$(dirname "$OUT")"
scripts/memory-health.sh-10-
scripts/memory-health.sh-11-probe() { curl -s -m 3 "$1" >/dev/null 2>&1 && echo "✅" || echo "❌"; }
scripts/memory-health.sh-12-
scripts/memory-health.sh-13-neo4j=$(probe "http://localhost:7478")
scripts/memory-health.sh-14-backend=$(probe "http://localhost:8011/api/v1/health")
--
scripts/deploy_epic12.py-119-def check_lancedb() -> bool:
scripts/deploy_epic12.py-120-    """检查LanceDB"""
scripts/deploy_epic12.py-121-    try:
scripts/deploy_epic12.py-122-        import lancedb
scripts/deploy_epic12.py-123-        path = os.environ.get("LANCEDB_PATH", "./data/lancedb")
scripts/deploy_epic12.py:124:        Path(path).mkdir(parents=True, exist_ok=True)
scripts/deploy_epic12.py-125-        db = lancedb.connect(path)
scripts/deploy_epic12.py-126-        print_ok(f"LanceDB: Ready ({path})")
scripts/deploy_epic12.py-127-        return True
scripts/deploy_epic12.py-128-    except Exception as e:
scripts/deploy_epic12.py-129-        print_error(f"LanceDB: {e}")
--
scripts/deploy_epic12.py-233-        "./logs",
scripts/deploy_epic12.py-234-        "./backups"
scripts/deploy_epic12.py-235-    ]
scripts/deploy_epic12.py-236-
scripts/deploy_epic12.py-237-    for dir_path in directories:
scripts/deploy_epic12.py:238:        Path(dir_path).mkdir(parents=True, exist_ok=True)
scripts/deploy_epic12.py-239-
scripts/deploy_epic12.py-240-    print_ok("Data directories created")
scripts/deploy_epic12.py-241-    return True
scripts/deploy_epic12.py-242-
scripts/deploy_epic12.py-243-
--
scripts/validate-iteration.py-433-```
scripts/validate-iteration.py-434-"""
scripts/validate-iteration.py-435-        sections.append({"title": "Recommendations", "content": rec_content})
scripts/validate-iteration.py-436-    elif result.has_warnings():
scripts/validate-iteration.py-437-        rec_content = """
scripts/validate-iteration.py:438:🟡 **Warnings Found**: Review recommended, but not blocking.
scripts/validate-iteration.py-439-
scripts/validate-iteration.py-440-**Suggested Actions**:
scripts/validate-iteration.py-441-1. Review all warnings
scripts/validate-iteration.py-442-2. Address concerns or document reasons for ignoring
scripts/validate-iteration.py-443-3. Proceed with caution
--
scripts/daily_review_pick.py-6-stdout 是瞬时数据, 推送失败补跑必须有持久化 payload)。
scripts/daily_review_pick.py-7-
scripts/daily_review_pick.py-8-schema v3 (CARD-A2, BATCH-2026-08-24-复习闭环): 本 JSON 是全系统到期口径
scripts/daily_review_pick.py-9-唯一裁判 — Dashboard.md 直接 dv.io.load 消费 due_nodes 明细 + ineligible
scripts/daily_review_pick.py-10-分桶 (占位符待剖析积压单独成桶), 不再独立重算。v2→v3 纯加性, 推送链
scripts/daily_review_pick.py:11:(daily_review_run/send_bark 只读 notification) 被动兼容。
scripts/daily_review_pick.py-12-
scripts/daily_review_pick.py-13-三态兼容 (live 实测 18 节点: 新字段 1 / 仅旧 10 / 无字段 7):
scripts/daily_review_pick.py-14-  mastery_a/b (+last_examined) → effective() 闲置折扣后 pick
scripts/daily_review_pick.py-15-  仅 mastery_score             → from_legacy() 均值继承低置信
scripts/daily_review_pick.py-16-  无字段                       → 先验 Beta(0.9,2.1), 从未考 σ 大自动优先
--
scripts/daily_review_pick.py-21-  2. 输出命令绑定 node <top_node> — start-exam-board 自己重选点时不含
scripts/daily_review_pick.py-22-     闲置折扣, 不绑定会出现「通知说考 A 实际考 B」
scripts/daily_review_pick.py-23-  3. min() 并列 tie-break: 板上次被推荐日期(久者先) → 最老 last_examined
scripts/daily_review_pick.py-24-     → 板名 (防启动期先验板按扫描顺序永久霸榜)
scripts/daily_review_pick.py-25-
scripts/daily_review_pick.py:26:依赖: 仅 stdlib + vault 内 decay_beta.py (launchd 环境无 pip 包可假设)。
scripts/daily_review_pick.py-27-"""
scripts/daily_review_pick.py-28-
scripts/daily_review_pick.py-29-from __future__ import annotations
scripts/daily_review_pick.py-30-
scripts/daily_review_pick.py-31-import argparse
--
scripts/daily_review_pick.py-355-    ap.add_argument("--now", help="ISO 时间覆盖 (测试用)")
scripts/daily_review_pick.py-356-    ap.add_argument("--write", action="store_true", help="写 outputs/今日复习.md+json")
scripts/daily_review_pick.py-357-    args = ap.parse_args()
scripts/daily_review_pick.py-358-
scripts/daily_review_pick.py-359-    vault = Path(args.vault)
scripts/daily_review_pick.py:360:    # 裸时间当本地时区, 与 daily_review_run.py 语义统一 (Code-Review L6)
scripts/daily_review_pick.py-361-    if args.now:
scripts/daily_review_pick.py-362-        dt = datetime.fromisoformat(args.now.replace("Z", "+00:00"))
scripts/daily_review_pick.py-363-        now = dt if dt.tzinfo else dt.astimezone()
scripts/daily_review_pick.py-364-    else:
scripts/daily_review_pick.py-365-        now = datetime.now(timezone.utc)
--
scripts/daily_review_pick.py-372-            pass  # state 损坏由 runner 处置, 选点侧降级为无记录
scripts/daily_review_pick.py-373-
scripts/daily_review_pick.py-374-    payload, ranked = build_payload(vault, now, blr, load_decay(vault))
scripts/daily_review_pick.py-375-    if args.write:
scripts/daily_review_pick.py-376-        out = vault / "outputs"
scripts/daily_review_pick.py:377:        out.mkdir(parents=True, exist_ok=True)
scripts/daily_review_pick.py-378-        atomic_write(out / "今日复习.md", render_md(payload, ranked))
scripts/daily_review_pick.py-379-        atomic_write(out / "今日复习.json",
scripts/daily_review_pick.py-380-                     json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
scripts/daily_review_pick.py-381-    print(json.dumps(payload, ensure_ascii=False))
scripts/daily_review_pick.py-382-
--
scripts/validate-story-status-yaml-sync.py-9-Usage:
scripts/validate-story-status-yaml-sync.py-10-    python scripts/validate-story-status-yaml-sync.py
scripts/validate-story-status-yaml-sync.py-11-
scripts/validate-story-status-yaml-sync.py-12-Exit codes:
scripts/validate-story-status-yaml-sync.py-13-    0 - Validation passed
scripts/validate-story-status-yaml-sync.py:14:    1 - Validation failed (warnings only, does not block)
scripts/validate-story-status-yaml-sync.py-15-"""
scripts/validate-story-status-yaml-sync.py-16-
scripts/validate-story-status-yaml-sync.py-17-import re
scripts/validate-story-status-yaml-sync.py-18-import sys
scripts/validate-story-status-yaml-sync.py-19-import subprocess
--
scripts/validate-story-status-yaml-sync.py-42-    'in development': 'in-progress',
scripts/validate-story-status-yaml-sync.py-43-    '🔄 in development': 'in-progress',
scripts/validate-story-status-yaml-sync.py-44-    'review': 'ready-for-review',
scripts/validate-story-status-yaml-sync.py-45-    'ready for review': 'ready-for-review',
scripts/validate-story-status-yaml-sync.py-46-    'in review': 'in-review',
scripts/validate-story-status-yaml-sync.py:47:    'blocked': 'blocked',
scripts/validate-story-status-yaml-sync.py-48-}
scripts/validate-story-status-yaml-sync.py-49-
scripts/validate-story-status-yaml-sync.py-50-
scripts/validate-story-status-yaml-sync.py-51-def get_staged_files() -> list:
scripts/validate-story-status-yaml-sync.py-52-    """Get list of staged files from git."""
--
scripts/validate-story-status-yaml-sync.py-187-        print("\n   Story status should be synced to YAML when Story files change.")
scripts/validate-story-status-yaml-sync.py-188-        print("   Consider running: scripts/validate-story-status-sync.ps1")
scripts/validate-story-status-yaml-sync.py-189-        print("\n   To include YAML in this commit:")
scripts/validate-story-status-yaml-sync.py-190-        print(f"   git add {YAML_PATH}")
scripts/validate-story-status-yaml-sync.py-191-        print("\n   To skip this check: git commit --no-verify")
scripts/validate-story-status-yaml-sync.py:192:        # Warning only, don't block
scripts/validate-story-status-yaml-sync.py-193-        return 0
scripts/validate-story-status-yaml-sync.py-194-
scripts/validate-story-status-yaml-sync.py-195-    print("\n✅ Both story files and YAML are staged - checking consistency...")
scripts/validate-story-status-yaml-sync.py-196-
scripts/validate-story-status-yaml-sync.py-197-    # Load YAML statuses
--
scripts/validate-story-status-yaml-sync.py-220-    if mismatches:
scripts/validate-story-status-yaml-sync.py-221-        print("\n❌ Status mismatches found:")
scripts/validate-story-status-yaml-sync.py-222-        for m in mismatches:
scripts/validate-story-status-yaml-sync.py-223-            print(f"   {m['story_id']}: file='{m['file_status']}' vs yaml='{m['yaml_status']}'")
scripts/validate-story-status-yaml-sync.py-224-        print("\n   Please ensure Story file and YAML statuses match.")
scripts/validate-story-status-yaml-sync.py:225:        # Warning only, don't block
scripts/validate-story-status-yaml-sync.py-226-        return 0
scripts/validate-story-status-yaml-sync.py-227-
scripts/validate-story-status-yaml-sync.py-228-    print("\n✅ Validation passed - statuses are consistent")
scripts/validate-story-status-yaml-sync.py-229-    return 0
scripts/validate-story-status-yaml-sync.py-230-
--
scripts/sync-env.sh-25-  NEO4J_PASSWORD
scripts/sync-env.sh-26-  NEO4J_HTTP_PORT
scripts/sync-env.sh-27-  NEO4J_BOLT_PORT
scripts/sync-env.sh-28-  CANVAS_BASE_PATH
scripts/sync-env.sh-29-  VAULTS_ROOT
scripts/sync-env.sh:30:  ACTIVE_VAULT
scripts/sync-env.sh-31-  OLLAMA_HOST
scripts/sync-env.sh-32-  CORS_ORIGINS
scripts/sync-env.sh-33-  DEBUG
scripts/sync-env.sh-34-)
scripts/sync-env.sh-35-
--
scripts/validate_agent_yaml.py-112-    for section in required_sections:
scripts/validate_agent_yaml.py-113-        if f'# {section}' not in content and f'## {section}' not in content:
scripts/validate_agent_yaml.py-114-            warnings.append(f"Missing section: {section}")
scripts/validate_agent_yaml.py-115-
scripts/validate_agent_yaml.py-116-    # 检查代码块闭合
scripts/validate_agent_yaml.py:117:    code_blocks = content.count('```')
scripts/validate_agent_yaml.py:118:    if code_blocks % 2 != 0:
scripts/validate_agent_yaml.py:119:        warnings.append("Unclosed code block (odd number of ```)")
scripts/validate_agent_yaml.py-120-
scripts/validate_agent_yaml.py-121-    return warnings
scripts/validate_agent_yaml.py-122-
scripts/validate_agent_yaml.py-123-def validate_agent_file(file_path: Path) -> Dict:
scripts/validate_agent_yaml.py-124-    """验证Agent文件"""
--
scripts/daily-review-push.sh-1-#!/usr/bin/env bash
scripts/daily-review-push.sh-2-# 每日复习推送 — 编排壳 (DAILY-REVIEW-PUSH-2026-07-29)。
scripts/daily-review-push.sh:3:# 只做两件事: mkdir 互斥锁 (终审 A7: 手工/kickstart/定时可能重叠) +
scripts/daily-review-push.sh:4:# 固定解释器调 runner。业务逻辑全在 daily_review_run.py (--now 可测)。
scripts/daily-review-push.sh-5-set -uo pipefail
scripts/daily-review-push.sh-6-
scripts/daily-review-push.sh-7-REPO="/Users/Heishing/Desktop/canvas/canvas-learning-system"
scripts/daily-review-push.sh-8-WT="$REPO/.claude/worktrees/feature-obsidian-hybrid-dev"
scripts/daily-review-push.sh:9:LOCK="$REPO/backups/.daily-review.lock"
scripts/daily-review-push.sh-10-
scripts/daily-review-push.sh:11:mkdir -p "$REPO/backups"
scripts/daily-review-push.sh:12:if ! mkdir "$LOCK" 2>/dev/null; then
scripts/daily-review-push.sh-13-    # 陈旧锁恢复 (Code-Review M5): 断电/SIGKILL 会留下锁目录, 不处理则
scripts/daily-review-push.sh-14-    # 之后每天 "skip: already running" 且 exit 0 永久静默。mtime 超 6h
scripts/daily-review-push.sh-15-    # 视为死锁夺回 (单次运行实测秒级, 6h 余量极大)。
scripts/daily-review-push.sh-16-    if [ -n "$(find "$LOCK" -maxdepth 0 -mmin +360 2>/dev/null)" ]; then
scripts/daily-review-push.sh:17:        echo "stale lock (>6h), reclaiming" >&2
scripts/daily-review-push.sh-18-        rmdir "$LOCK" 2>/dev/null || true
scripts/daily-review-push.sh-19-    fi
scripts/daily-review-push.sh:20:    if ! mkdir "$LOCK" 2>/dev/null; then
scripts/daily-review-push.sh-21-        echo "skip: already running" >&2
scripts/daily-review-push.sh-22-        exit 0
scripts/daily-review-push.sh-23-    fi
scripts/daily-review-push.sh-24-fi
scripts/daily-review-push.sh-25-# 不用 exec — exec 会替换进程使 trap 失效, 锁永不释放
scripts/daily-review-push.sh-26-trap 'rmdir "$LOCK" 2>/dev/null || true' EXIT INT TERM
scripts/daily-review-push.sh-27-
scripts/daily-review-push.sh-28-PY="$WT/backend/.venv/bin/python"
scripts/daily-review-push.sh-29-[ -x "$PY" ] || PY="/usr/bin/python3"   # venv 缺失兜底 (runner 仅 stdlib)
scripts/daily-review-push.sh-30-
scripts/daily-review-push.sh:31:"$PY" "$WT/scripts/daily_review_run.py" "$@"
--
scripts/daemon/status_watcher.py-52-        self.debounce_seconds = debounce_seconds
scripts/daemon/status_watcher.py-53-
scripts/daemon/status_watcher.py-54-        # Track state
scripts/daemon/status_watcher.py-55-        self._last_event_time: Dict[str, float] = {}
scripts/daemon/status_watcher.py-56-        self._already_triggered: Set[str] = set()
scripts/daemon/status_watcher.py:57:        self._lock = threading.Lock()
scripts/daemon/status_watcher.py-58-
scripts/daemon/status_watcher.py-59-    def on_modified(self, event):
scripts/daemon/status_watcher.py-60-        """Handle file modification events."""
scripts/daemon/status_watcher.py-61-        if event.is_directory:
scripts/daemon/status_watcher.py-62-            return
--
scripts/daemon/status_watcher.py-81-        story_id = self._find_story_for_path(modified_path)
scripts/daemon/status_watcher.py-82-        if story_id is None:
scripts/daemon/status_watcher.py-83-            return
scripts/daemon/status_watcher.py-84-
scripts/daemon/status_watcher.py-85-        # Debounce rapid modifications
scripts/daemon/status_watcher.py:86:        with self._lock:
scripts/daemon/status_watcher.py-87-            now = time.time()
scripts/daemon/status_watcher.py-88-            last_time = self._last_event_time.get(story_id, 0)
scripts/daemon/status_watcher.py-89-
scripts/daemon/status_watcher.py-90-            if now - last_time < self.debounce_seconds:
scripts/daemon/status_watcher.py-91-                return
--
scripts/daemon/status_watcher.py-115-        """Check if status is dev-complete and trigger callback."""
scripts/daemon/status_watcher.py-116-        try:
scripts/daemon/status_watcher.py-117-            status = self._read_status_file(status_path)
scripts/daemon/status_watcher.py-118-
scripts/daemon/status_watcher.py-119-            if status.get('status') == 'dev-complete':
scripts/daemon/status_watcher.py:120:                with self._lock:
scripts/daemon/status_watcher.py-121-                    if story_id in self._already_triggered:
scripts/daemon/status_watcher.py-122-                        return  # Already triggered, skip
scripts/daemon/status_watcher.py-123-                    self._already_triggered.add(story_id)
scripts/daemon/status_watcher.py-124-
scripts/daemon/status_watcher.py-125-                # Get worktree path (parent of status file)
--
scripts/daemon/status_watcher.py-152-
scripts/daemon/status_watcher.py-153-        return result
scripts/daemon/status_watcher.py-154-
scripts/daemon/status_watcher.py-155-    def reset_trigger(self, story_id: str):
scripts/daemon/status_watcher.py-156-        """Reset the trigger state for a story (allows re-triggering)."""
scripts/daemon/status_watcher.py:157:        with self._lock:
scripts/daemon/status_watcher.py-158-            self._already_triggered.discard(story_id)
scripts/daemon/status_watcher.py-159-            self._last_event_time.pop(story_id, None)
scripts/daemon/status_watcher.py-160-
scripts/daemon/status_watcher.py-161-
scripts/daemon/status_watcher.py-162-class StatusWatcher:
--
scripts/lib/breaking_change_detector.py-39-    SCHEMA_REMOVED = "schema_removed"
scripts/lib/breaking_change_detector.py-40-
scripts/lib/breaking_change_detector.py-41-
scripts/lib/breaking_change_detector.py-42-class ChangeSeverity(Enum):
scripts/lib/breaking_change_detector.py-43-    """变更严重程度"""
scripts/lib/breaking_change_detector.py:44:    ERROR = "error"      # Breaking change, blocks commit
scripts/lib/breaking_change_detector.py-45-    WARNING = "warning"  # Potentially breaking, needs review
scripts/lib/breaking_change_detector.py-46-    INFO = "info"        # Informational, backward compatible
scripts/lib/breaking_change_detector.py-47-
scripts/lib/breaking_change_detector.py-48-
scripts/lib/breaking_change_detector.py-49-class BreakingChangeDetector:
--
scripts/lib/breaking_change_detector.py-357-        if args.output:
scripts/lib/breaking_change_detector.py-358-            output_path = Path(args.output)
scripts/lib/breaking_change_detector.py-359-        else:
scripts/lib/breaking_change_detector.py-360-            output_path = project_root / "docs" / "specs" / "breaking-changes-report.md"
scripts/lib/breaking_change_detector.py-361-
scripts/lib/breaking_change_detector.py:362:        output_path.parent.mkdir(parents=True, exist_ok=True)
scripts/lib/breaking_change_detector.py-363-        with open(output_path, 'w', encoding='utf-8') as f:
scripts/lib/breaking_change_detector.py-364-            f.write(report)
scripts/lib/breaking_change_detector.py-365-        print(f"\nReport saved to: {output_path}")
scripts/lib/breaking_change_detector.py-366-
scripts/lib/breaking_change_detector.py-367-    return 1 if detector.has_breaking_changes() else 0
--
scripts/install-vault.sh-7-#
scripts/install-vault.sh-8-# 用法:
scripts/install-vault.sh-9-#   scripts/install-vault.sh <vault-name> [--subject <学科>] [--activate]
scripts/install-vault.sh-10-#                            [--vaults-root <dir>] [--source <vault-dir>]
scripts/install-vault.sh-11-#                            [--env-file <path>]
scripts/install-vault.sh:12:#   --activate: 把 .env ACTIVE_VAULT 切到新 vault (之后需 docker compose up -d backend)
scripts/install-vault.sh-13-#   缺省只部署不激活 — 可先建多个 vault 再选一个激活。
scripts/install-vault.sh-14-set -euo pipefail
scripts/install-vault.sh-15-
scripts/install-vault.sh-16-REPO="/Users/Heishing/Desktop/canvas/canvas-learning-system"
scripts/install-vault.sh-17-WT="$REPO/.claude/worktrees/feature-obsidian-hybrid-dev"
--
scripts/install-vault.sh-41-    -*|*/*|*..*|*'|'*|*'&'*|*'"'*|*"'"*|*$'\n'*|*$'\t'*)
scripts/install-vault.sh-42-        echo "❌ vault 名含非法字符 (不允许: 开头-、/、..、|、&、引号、换行): $VAULT_NAME" >&2
scripts/install-vault.sh-43-        exit 64 ;;
scripts/install-vault.sh-44-esac
scripts/install-vault.sh-45-
scripts/install-vault.sh:46:# 模板源: 缺省从 .env ACTIVE_VAULT + .env 宿主侧 VAULTS_ROOT 解析活 vault
scripts/install-vault.sh-47-# (与推送 VAULT-SYNC 同一逻辑)。注意源解析独立于 --vaults-root (那是目标根,
scripts/install-vault.sh-48-# 测试场景会指向 scratch 目录, 模板源不能跟着跑偏)。
scripts/install-vault.sh-49-if [ -z "$SOURCE" ]; then
scripts/install-vault.sh-50-    # 审查 M2: || true 防 set -e 在 .env 缺失/缺行时静默死亡, 让回退值生效
scripts/install-vault.sh:51:    AV=$(grep -E '^ACTIVE_VAULT=' "$ENV_FILE" 2>/dev/null | tail -1 | cut -d= -f2- | tr -d '"' | tr -d "'" || true)
scripts/install-vault.sh-52-    SRC_ROOT=$(grep -E '^VAULTS_ROOT=' "$ENV_FILE" 2>/dev/null | tail -1 | cut -d= -f2- | tr -d '"' | tr -d "'" || true)
scripts/install-vault.sh-53-    SOURCE="${SRC_ROOT:-$REPO}/${AV:-canvas-vault}"
scripts/install-vault.sh-54-fi
scripts/install-vault.sh-55-TARGET="$VAULTS_ROOT/$VAULT_NAME"
scripts/install-vault.sh-56-
--
scripts/install-vault.sh-69-# workspace.json (会话状态)、.canvas-config.yaml (按 vault 重新生成)
scripts/install-vault.sh-70-
scripts/install-vault.sh-71-echo "📦 部署 Canvas Learning System → $TARGET"
scripts/install-vault.sh-72-echo "   模板源: $SOURCE"
scripts/install-vault.sh-73-
scripts/install-vault.sh:74:for d in "${SKELETON_DIRS[@]}"; do mkdir -p "$TARGET/$d"; done
scripts/install-vault.sh:75:mkdir -p "$TARGET/.claude" "$TARGET/.obsidian/plugins"
scripts/install-vault.sh-76-
scripts/install-vault.sh-77-for item in "${CLAUDE_ITEMS[@]}"; do
scripts/install-vault.sh-78-    if [ -e "$SOURCE/.claude/$item" ]; then
scripts/install-vault.sh-79-        cp -R "$SOURCE/.claude/$item" "$TARGET/.claude/$item"
scripts/install-vault.sh-80-    else
--
scripts/install-vault.sh-135-if [ "$ACTIVATE" = 1 ] && [ -n "$ENV_VROOT" ] && [ "$VAULTS_ROOT" != "$ENV_VROOT" ]; then
scripts/install-vault.sh-136-    echo "   ⛔ 目标根 ($VAULTS_ROOT) ≠ .env VAULTS_ROOT ($ENV_VROOT) — 容器看不见此 vault, 跳过激活"
scripts/install-vault.sh-137-    ACTIVATE=0
scripts/install-vault.sh-138-fi
scripts/install-vault.sh-139-if [ "$ACTIVATE" = 1 ]; then
scripts/install-vault.sh:140:    if grep -qE '^ACTIVE_VAULT=' "$ENV_FILE"; then
scripts/install-vault.sh:141:        sed -i '' "s|^ACTIVE_VAULT=.*|ACTIVE_VAULT=$VAULT_NAME|" "$ENV_FILE"
scripts/install-vault.sh-142-    else
scripts/install-vault.sh:143:        printf '\nACTIVE_VAULT=%s\n' "$VAULT_NAME" >> "$ENV_FILE"
scripts/install-vault.sh-144-    fi
scripts/install-vault.sh:145:    check "已激活 (.env ACTIVE_VAULT)" 'grep -qF "ACTIVE_VAULT=$VAULT_NAME" "$ENV_FILE"'
scripts/install-vault.sh-146-    NEXT_ACTIVATE="⚠️ 生效需重启后端: docker compose up -d backend"
scripts/install-vault.sh-147-else
scripts/install-vault.sh:148:    NEXT_ACTIVATE="激活: scripts/install-vault.sh 加 --activate, 或手改 .env ACTIVE_VAULT=$VAULT_NAME 后 docker compose up -d backend"
scripts/install-vault.sh-149-fi
scripts/install-vault.sh-150-
scripts/install-vault.sh-151-echo ""
scripts/install-vault.sh-152-echo "═══ 结果: $PASS 项通过 / $FAIL 项失败 ═══"
scripts/install-vault.sh-153-echo "📋 后续步骤:"
--
scripts/launchd/daily-review-wrapper.sh-1-#!/usr/bin/env bash
scripts/launchd/daily-review-wrapper.sh:2:# 每日复习推送 launchd 入口 wrapper (DAILY-REVIEW-PUSH-2026-07-29, 终审 A6)。
scripts/launchd/daily-review-wrapper.sh:3:# 安装位置: ~/Library/Application Support/CanvasReview/bin/ — launchd 只指向
scripts/launchd/daily-review-wrapper.sh-4-# 这个稳定路径, worktree 移动/清理不再让任务永久失效 (memory-health 6 天
scripts/launchd/daily-review-wrapper.sh-5-# 停摆教训的结构性修复)。本文件是 git 追踪的源码副本, 改动后需重新 cp 安装。
scripts/launchd/daily-review-wrapper.sh-6-set -uo pipefail
scripts/launchd/daily-review-wrapper.sh-7-
scripts/launchd/daily-review-wrapper.sh-8-export PATH="/usr/bin:/bin:/usr/sbin:/sbin"
scripts/launchd/daily-review-wrapper.sh-9-export HOME="${HOME:-/Users/Heishing}"
scripts/launchd/daily-review-wrapper.sh-10-export LANG="zh_CN.UTF-8"
scripts/launchd/daily-review-wrapper.sh-11-
scripts/launchd/daily-review-wrapper.sh-12-BOOTLOG="$HOME/Library/Logs/canvas-daily-review.boot.log"
scripts/launchd/daily-review-wrapper.sh:13:# 第一行探针: 连 ~/Library 都写不了 = launchd 环境彻底异常
scripts/launchd/daily-review-wrapper.sh-14-echo "[$(date '+%F %T')] wrapper start" >> "$BOOTLOG"
scripts/launchd/daily-review-wrapper.sh-15-
scripts/launchd/daily-review-wrapper.sh-16-REPO="/Users/Heishing/Desktop/canvas/canvas-learning-system"
scripts/launchd/daily-review-wrapper.sh-17-WT="$REPO/.claude/worktrees/feature-obsidian-hybrid-dev"
scripts/launchd/daily-review-wrapper.sh-18-
scripts/launchd/daily-review-wrapper.sh-19-fail() { echo "[$(date '+%F %T')] PREFLIGHT-FAIL: $1" >> "$BOOTLOG"; exit 78; }
scripts/launchd/daily-review-wrapper.sh-20-
scripts/launchd/daily-review-wrapper.sh:21:# VAULT-SYNC (2026-08-02 用户拍板): 推送 vault 与 .env ACTIVE_VAULT 同源 —
scripts/launchd/daily-review-wrapper.sh-22-# P0-3 确立「vault 由部署期 .env 固定」后, 推送链不再独立写死, 换 vault
scripts/launchd/daily-review-wrapper.sh-23-# 只改 .env 一处, 后端/skills/推送全部跟走。解析失败回退 canvas-vault
scripts/launchd/daily-review-wrapper.sh-24-# (与旧行为一致); VAULTS_ROOT 取 .env 宿主侧值, 缺省回退主仓根。
scripts/launchd/daily-review-wrapper.sh-25-ENV_FILE="$WT/.env"
scripts/launchd/daily-review-wrapper.sh:26:ACTIVE_VAULT=$(grep -E '^ACTIVE_VAULT=' "$ENV_FILE" 2>/dev/null | tail -1 | cut -d= -f2- | tr -d '"' | tr -d "'")
scripts/launchd/daily-review-wrapper.sh-27-VAULTS_ROOT_HOST=$(grep -E '^VAULTS_ROOT=' "$ENV_FILE" 2>/dev/null | tail -1 | cut -d= -f2- | tr -d '"' | tr -d "'")
scripts/launchd/daily-review-wrapper.sh:28:VAULT="${VAULTS_ROOT_HOST:-$REPO}/${ACTIVE_VAULT:-canvas-vault}"
scripts/launchd/daily-review-wrapper.sh:29:echo "[$(date '+%F %T')] vault=$VAULT (ACTIVE_VAULT=${ACTIVE_VAULT:-<fallback>})" >> "$BOOTLOG"
scripts/launchd/daily-review-wrapper.sh-30-
scripts/launchd/daily-review-wrapper.sh-31-# TCC preflight: Desktop 路径受 TCC 管辖。⚠ 必须真实读取 — [ -r ] 走 access()
scripts/launchd/daily-review-wrapper.sh-32-# 在 TCC 域内会假通过 (2026-07-29 实测: 测试全过但 exec 仍 Operation not
scripts/launchd/daily-review-wrapper.sh-33-# permitted), 只有 ls/head 这类真 I/O 才探得出来
scripts/launchd/daily-review-wrapper.sh-34-ls "$VAULT/节点" >/dev/null 2>&1 \
scripts/launchd/daily-review-wrapper.sh-35-    || fail "vault_not_readable_tcc — 系统设置→隐私与安全性→完全磁盘访问→给 /bin/bash 开启"
scripts/launchd/daily-review-wrapper.sh:36:mkdir -p "$REPO/backups" 2>/dev/null || fail "backups_not_writable_tcc"
scripts/launchd/daily-review-wrapper.sh-37-head -c 1 "$WT/scripts/daily-review-push.sh" >/dev/null 2>&1 \
scripts/launchd/daily-review-wrapper.sh-38-    || fail "repo_script_unreadable_tcc_or_missing — TCC 未授权或 worktree 被清理"
scripts/launchd/daily-review-wrapper.sh-39-# 双副本一致性 (Code-Review M4 + FSRS-V2 H1): runner/quiz-answer 用的是
scripts/launchd/daily-review-wrapper.sh-40-# 活 vault 里的副本, worktree 改了忘 cp 会造成静默行为漂移
scripts/launchd/daily-review-wrapper.sh-41-for f in decay_beta.py fsrs_bridge.py; do
--
scripts/diff-openapi.py-640-    report = generate_diff_report(diff, report_spec1_path, spec2_path)
scripts/diff-openapi.py-641-
scripts/diff-openapi.py-642-    # 输出报告
scripts/diff-openapi.py-643-    if args.output:
scripts/diff-openapi.py-644-        output_path = Path(args.output)
scripts/diff-openapi.py:645:        output_path.parent.mkdir(parents=True, exist_ok=True)
scripts/diff-openapi.py-646-        with open(output_path, 'w', encoding='utf-8') as f:
scripts/diff-openapi.py-647-            f.write(report)
scripts/diff-openapi.py-648-        print_status(f"Report saved to: {output_path}", "success")
scripts/diff-openapi.py-649-    else:
scripts/diff-openapi.py-650-        print("\n" + report)
--
scripts/validate-story-sdd-adr.py-157-    """主函数"""
scripts/validate-story-sdd-adr.py-158-    print("=" * 60)
scripts/validate-story-sdd-adr.py-159-    print("[VALIDATE] Story SDD/ADR Section Validator")
scripts/validate-story-sdd-adr.py-160-    print("=" * 60)
scripts/validate-story-sdd-adr.py-161-    print(f"  Legacy threshold: Epic < {LEGACY_EPIC_THRESHOLD} (warnings only)")
scripts/validate-story-sdd-adr.py:162:    print(f"  Enforced: Epic >= {LEGACY_EPIC_THRESHOLD} (errors block commit)")
scripts/validate-story-sdd-adr.py-163-    print()
scripts/validate-story-sdd-adr.py-164-
scripts/validate-story-sdd-adr.py-165-    # Get story files from arguments or find all
scripts/validate-story-sdd-adr.py-166-    if len(sys.argv) > 1:
scripts/validate-story-sdd-adr.py-167-        # Files passed as arguments (from pre-commit)
--
scripts/lib/planning_utils.py-49-        with open(file_path, 'r', encoding='gbk') as f:
scripts/lib/planning_utils.py-50-            return f.read()
scripts/lib/planning_utils.py-51-
scripts/lib/planning_utils.py-52-def write_file(file_path: Path, content: str):
scripts/lib/planning_utils.py-53-    """安全写入文件"""
scripts/lib/planning_utils.py:54:    file_path.parent.mkdir(parents=True, exist_ok=True)
scripts/lib/planning_utils.py-55-    with open(file_path, 'w', encoding='utf-8') as f:
scripts/lib/planning_utils.py-56-        f.write(content)
scripts/lib/planning_utils.py-57-
scripts/lib/planning_utils.py-58-def compute_file_hash(file_path: Path) -> str:
scripts/lib/planning_utils.py-59-    """计算文件的SHA-256 hash"""
--
scripts/lib/planning_utils.py-238-
scripts/lib/planning_utils.py-239-    Returns:
scripts/lib/planning_utils.py-240-        Path: 保存的文件路径
scripts/lib/planning_utils.py-241-    """
scripts/lib/planning_utils.py-242-    path = get_iteration_snapshot_path(iteration_num)
scripts/lib/planning_utils.py:243:    path.parent.mkdir(parents=True, exist_ok=True)
scripts/lib/planning_utils.py-244-
scripts/lib/planning_utils.py-245-    with open(path, 'w', encoding='utf-8') as f:
scripts/lib/planning_utils.py-246-        json.dump(snapshot, f, indent=2, ensure_ascii=False)
scripts/lib/planning_utils.py-247-
scripts/lib/planning_utils.py-248-    print(f"✅ Snapshot saved: {path}")
--
scripts/snapshot_planning.py-226-    snapshot = create_snapshot(iteration_num=args.iteration)
scripts/snapshot_planning.py-227-
scripts/snapshot_planning.py-228-    # 保存snapshot
scripts/snapshot_planning.py-229-    if args.output:
scripts/snapshot_planning.py-230-        output_path = Path(args.output)
scripts/snapshot_planning.py:231:        output_path.parent.mkdir(parents=True, exist_ok=True)
scripts/snapshot_planning.py-232-        with open(output_path, 'w', encoding='utf-8') as f:
scripts/snapshot_planning.py-233-            json.dump(snapshot, f, indent=2, ensure_ascii=False)
scripts/snapshot_planning.py-234-        print_status(f"Snapshot saved to: {output_path}", "success")
scripts/snapshot_planning.py-235-    else:
scripts/snapshot_planning.py-236-        save_snapshot(snapshot, snapshot["iteration"])
--
scripts/validate-workflow-gate.py-12-Usage (as pre-commit hook):
scripts/validate-workflow-gate.py-13-    python scripts/validate-workflow-gate.py
scripts/validate-workflow-gate.py-14-
scripts/validate-workflow-gate.py-15-Exit codes:
scripts/validate-workflow-gate.py-16-    0: All validations passed
scripts/validate-workflow-gate.py:17:    1: Validation failed, commit blocked
scripts/validate-workflow-gate.py-18-
scripts/validate-workflow-gate.py-19-Author: Canvas Learning System Team
scripts/validate-workflow-gate.py-20-Version: 1.0.0
scripts/validate-workflow-gate.py-21-Created: 2025-12-11
scripts/validate-workflow-gate.py-22-"""
--
scripts/validate-workflow-gate.py-145-    """
scripts/validate-workflow-gate.py-146-    Main entry point for pre-commit hook.
scripts/validate-workflow-gate.py-147-
scripts/validate-workflow-gate.py-148-    Returns:
scripts/validate-workflow-gate.py-149-        0 if all validations passed
scripts/validate-workflow-gate.py:150:        1 if any validation failed (blocks commit)
scripts/validate-workflow-gate.py-151-    """
scripts/validate-workflow-gate.py-152-    print_header()
scripts/validate-workflow-gate.py-153-
scripts/validate-workflow-gate.py-154-    # Get staged files
scripts/validate-workflow-gate.py-155-    staged_files = get_staged_files()
--
scripts/sync_links.py-6-and idempotently upserts a `## Relations` section at the end of each file.
scripts/sync_links.py-7-
scripts/sync_links.py-8-Dimensions:
scripts/sync_links.py-9-  1. Story → Epic (upward: epic_id field)
scripts/sync_links.py-10-  2. Epic → Story list (downward: auto-fill child_stories)
scripts/sync_links.py:11:  3. Story ↔ Story (horizontal: depends_on / blocks)
scripts/sync_links.py-12-  4. Story ↔ PRD / Decision / Bug (cross-cutting: prd_id, trace.decisions, trace.bugs)
scripts/sync_links.py-13-
scripts/sync_links.py-14-Usage:
scripts/sync_links.py-15-  python scripts/sync_links.py              # full sync
scripts/sync_links.py-16-  python scripts/sync_links.py --validate   # validate only, no writes
--
scripts/sync_links.py-67-            index[sid] = {
scripts/sync_links.py-68-                "path": story_file,
scripts/sync_links.py-69-                "epic_id": fm.get("epic_id", ""),
scripts/sync_links.py-70-                "prd_id": fm.get("prd_id", ""),
scripts/sync_links.py-71-                "depends_on": fm.get("depends_on", []) or [],
scripts/sync_links.py:72:                "blocks": fm.get("blocks", []) or [],
scripts/sync_links.py-73-                "decisions": (fm.get("trace", {}) or {}).get("decisions", []) or [],
scripts/sync_links.py-74-                "bugs": (fm.get("trace", {}) or {}).get("bugs", []) or [],
scripts/sync_links.py-75-            }
scripts/sync_links.py-76-    return index
scripts/sync_links.py-77-
--
scripts/sync_links.py-119-
scripts/sync_links.py-120-        for dep in data.get("depends_on", []):
scripts/sync_links.py-121-            if str(dep) not in story_index:
scripts/sync_links.py-122-                errors.append(f"BROKEN_DEP: Story {sid} depends_on {dep} which doesn't exist")
scripts/sync_links.py-123-
scripts/sync_links.py:124:        for blk in data.get("blocks", []):
scripts/sync_links.py-125-            if str(blk) not in story_index:
scripts/sync_links.py:126:                errors.append(f"BROKEN_BLOCK: Story {sid} blocks {blk} which doesn't exist")
scripts/sync_links.py-127-
scripts/sync_links.py-128-    dep_graph: dict[str, set[str]] = {}
scripts/sync_links.py-129-    for sid, data in story_index.items():
scripts/sync_links.py-130-        dep_graph[sid] = {str(d) for d in data.get("depends_on", [])}
scripts/sync_links.py-131-
--
scripts/sync_links.py-159-    deps = data.get("depends_on", [])
scripts/sync_links.py-160-    if deps:
scripts/sync_links.py-161-        dep_links = ", ".join(f"[[{d}]]" for d in deps)
scripts/sync_links.py-162-        lines.append(f"- Depends on: {dep_links}")
scripts/sync_links.py-163-
scripts/sync_links.py:164:    blocks = data.get("blocks", [])
scripts/sync_links.py:165:    if blocks:
scripts/sync_links.py:166:        blk_links = ", ".join(f"[[{b}]]" for b in blocks)
scripts/sync_links.py:167:        lines.append(f"- Blocks: {blk_links}")
scripts/sync_links.py-168-
scripts/sync_links.py-169-    decisions = data.get("decisions", [])
scripts/sync_links.py-170-    if decisions:
scripts/sync_links.py-171-        dec_links = ", ".join(f"[[{d}]]" for d in decisions)
scripts/sync_links.py-172-        lines.append(f"- Decisions: {dec_links}")
--
scripts/sync_links.py-223-
scripts/sync_links.py-224-    return stats
scripts/sync_links.py-225-
scripts/sync_links.py-226-
scripts/sync_links.py-227-def write_errors(errors: list[str]) -> None:
scripts/sync_links.py:228:    META_DIR.mkdir(parents=True, exist_ok=True)
scripts/sync_links.py-229-    content = "# Link Validation Errors\n\n"
scripts/sync_links.py-230-    if not errors:
scripts/sync_links.py-231-        content += "No errors found.\n"
scripts/sync_links.py-232-    else:
scripts/sync_links.py-233-        for e in errors:
scripts/sync_links.py-234-            content += f"- {e}\n"
scripts/sync_links.py-235-    LINK_ERRORS_FILE.write_text(content, encoding="utf-8")
scripts/sync_links.py-236-
scripts/sync_links.py-237-
scripts/sync_links.py-238-def write_report(stats: dict, error_count: int) -> None:
scripts/sync_links.py:239:    META_DIR.mkdir(parents=True, exist_ok=True)
scripts/sync_links.py-240-    content = "# Sync Report\n\n"
scripts/sync_links.py-241-    content += f"- Stories synced: {stats.get('stories_synced', 0)}\n"
scripts/sync_links.py-242-    content += f"- Epics synced: {stats.get('epics_synced', 0)}\n"
scripts/sync_links.py-243-    content += f"- Skipped (unchanged): {stats.get('skipped', 0)}\n"
scripts/sync_links.py-244-    content += f"- Validation errors: {error_count}\n"
--
scripts/trace/build_story_file_map.py-111-def main() -> None:
scripts/trace/build_story_file_map.py-112-    parser = argparse.ArgumentParser()
scripts/trace/build_story_file_map.py-113-    parser.add_argument("--all", action="store_true", help="Full rebuild")
scripts/trace/build_story_file_map.py-114-    parser.parse_args()
scripts/trace/build_story_file_map.py-115-
scripts/trace/build_story_file_map.py:116:    INDEX_DIR.mkdir(parents=True, exist_ok=True)
scripts/trace/build_story_file_map.py-117-    index = build_index()
scripts/trace/build_story_file_map.py-118-
scripts/trace/build_story_file_map.py-119-    INDEX_FILE.write_text(
scripts/trace/build_story_file_map.py-120-        yaml.dump(
scripts/trace/build_story_file_map.py-121-            {"generated": "build_story_file_map.py", "stories": index},
--
scripts/validate-content-consistency.py-379-        print(f"  Found {len(self.conflicts)} inconsistencies")
scripts/validate-content-consistency.py-380-        print()
scripts/validate-content-consistency.py-381-
scripts/validate-content-consistency.py-382-        # 判断结果
scripts/validate-content-consistency.py-383-        # 只有required_mismatch是阻止性冲突，field_missing作为警告
scripts/validate-content-consistency.py:384:        blocking_conflicts = [c for c in self.conflicts if c['type'] == 'required_mismatch']
scripts/validate-content-consistency.py-385-        warning_conflicts = [c for c in self.conflicts if c['type'] == 'field_missing']
scripts/validate-content-consistency.py:386:        passed = len(blocking_conflicts) == 0
scripts/validate-content-consistency.py-387-
scripts/validate-content-consistency.py-388-        # 打印结果
scripts/validate-content-consistency.py-389-        print("=" * 60)
scripts/validate-content-consistency.py-390-        if passed:
scripts/validate-content-consistency.py-391-            if warning_conflicts:
scripts/validate-content-consistency.py-392-                print("[PASS] Content Consistency Validation Passed (with warnings)")
scripts/validate-content-consistency.py:393:                print(f"\nWarnings ({len(warning_conflicts)} field_missing issues - non-blocking):")
scripts/validate-content-consistency.py-394-                for conflict in warning_conflicts[:3]:
scripts/validate-content-consistency.py-395-                    print(f"  - {conflict['model']}.{conflict['field']}: {conflict['type']}")
scripts/validate-content-consistency.py-396-                if len(warning_conflicts) > 3:
scripts/validate-content-consistency.py-397-                    print(f"  ... and {len(warning_conflicts) - 3} more")
scripts/validate-content-consistency.py-398-            else:
scripts/validate-content-consistency.py-399-                print("[PASS] Content Consistency Validation Passed")
scripts/validate-content-consistency.py-400-        else:
scripts/validate-content-consistency.py-401-            print("[FAIL] Content Consistency Validation Failed")
scripts/validate-content-consistency.py:402:            print(f"\nBlocking errors ({len(blocking_conflicts)} required_mismatch issues):")
scripts/validate-content-consistency.py:403:            for conflict in blocking_conflicts[:5]:
scripts/validate-content-consistency.py-404-                print(f"  - {conflict['model']}.{conflict['field']}: {conflict['type']}")
scripts/validate-content-consistency.py-405-                print(f"    {conflict['sources']}")
scripts/validate-content-consistency.py-406-                print(f"    Recommendation: {conflict['recommendation']}")
scripts/validate-content-consistency.py:407:            if len(blocking_conflicts) > 5:
scripts/validate-content-consistency.py:408:                print(f"  ... and {len(blocking_conflicts) - 5} more")
scripts/validate-content-consistency.py-409-
scripts/validate-content-consistency.py-410-        print("=" * 60)
scripts/validate-content-consistency.py-411-
scripts/validate-content-consistency.py-412-        return passed, self.conflicts
scripts/validate-content-consistency.py-413-
--
scripts/validate-content-consistency.py-501-**Report generated by**: scripts/validate-content-consistency.py
scripts/validate-content-consistency.py-502-**Reference**: Section 16.5.4 of planning document
scripts/validate-content-consistency.py-503-"""
scripts/validate-content-consistency.py-504-
scripts/validate-content-consistency.py-505-        if output_path:
scripts/validate-content-consistency.py:506:            output_path.parent.mkdir(parents=True, exist_ok=True)
scripts/validate-content-consistency.py-507-            with open(output_path, 'w', encoding='utf-8') as f:
scripts/validate-content-consistency.py-508-                f.write(report)
scripts/validate-content-consistency.py-509-            print(f"\nReport saved to: {output_path}")
scripts/validate-content-consistency.py-510-
scripts/validate-content-consistency.py-511-        return report
--
scripts/validate-source-citations.py-442-**Report generated by**: scripts/validate-source-citations.py
scripts/validate-source-citations.py-443-**Reference**: Section 16.5.3 of planning document
scripts/validate-source-citations.py-444-"""
scripts/validate-source-citations.py-445-
scripts/validate-source-citations.py-446-        if output_path:
scripts/validate-source-citations.py:447:            output_path.parent.mkdir(parents=True, exist_ok=True)
scripts/validate-source-citations.py-448-            with open(output_path, 'w', encoding='utf-8') as f:
scripts/validate-source-citations.py-449-                f.write(report)
scripts/validate-source-citations.py-450-            print(f"\nReport saved to: {output_path}")
scripts/validate-source-citations.py-451-
scripts/validate-source-citations.py-452-        return report
--
scripts/ci/ragas_gate.py-18-
scripts/ci/ragas_gate.py-19-This script is called from .github/workflows/test.yml as a standalone job
scripts/ci/ragas_gate.py-20-with ``continue-on-error: true`` during observation mode. After the first
scripts/ci/ragas_gate.py-21-weekly baseline is recorded in
scripts/ci/ragas_gate.py-22-``openspec/changes/fix-fr-kg-04-schema-drift-and-sync-hardening/ragas-baseline.md``,
scripts/ci/ragas_gate.py:23:the workflow flips it to blocking mode.
scripts/ci/ragas_gate.py-24-"""
scripts/ci/ragas_gate.py-25-
scripts/ci/ragas_gate.py-26-from __future__ import annotations
scripts/ci/ragas_gate.py-27-
scripts/ci/ragas_gate.py-28-import argparse
--
scripts/ci/ragas_gate.py-109-            file=sys.stderr,
scripts/ci/ragas_gate.py-110-        )
scripts/ci/ragas_gate.py-111-        raise SystemExit(3)
scripts/ci/ragas_gate.py-112-
scripts/ci/ragas_gate.py-113-    # Placeholder: once the RAG pipeline entry point is stable, replace
scripts/ci/ragas_gate.py:114:    # this block with the real evaluation loop using ragas_module.evaluate.
scripts/ci/ragas_gate.py-115-    _ = ragas_module  # keep the import
scripts/ci/ragas_gate.py-116-    return {}
scripts/ci/ragas_gate.py-117-
scripts/ci/ragas_gate.py-118-
scripts/ci/ragas_gate.py-119-def main() -> int:
--
scripts/daemon/linear_progress.py-48-
scripts/daemon/linear_progress.py-49-    def is_success(self) -> bool:
scripts/daemon/linear_progress.py-50-        """Check if outcome represents success."""
scripts/daemon/linear_progress.py-51-        return self == StoryOutcome.SUCCESS
scripts/daemon/linear_progress.py-52-
scripts/daemon/linear_progress.py:53:    def is_blocked(self) -> bool:
scripts/daemon/linear_progress.py:54:        """Check if outcome represents a blocked state (needs retry or halt)."""
scripts/daemon/linear_progress.py-55-        return self in [
scripts/daemon/linear_progress.py-56-            StoryOutcome.DEV_BLOCKED,
scripts/daemon/linear_progress.py-57-            StoryOutcome.QA_BLOCKED,
scripts/daemon/linear_progress.py-58-            StoryOutcome.QA_CONCERNS_UNFIXED,
scripts/daemon/linear_progress.py-59-        ]
--
scripts/daemon/linear_progress.py-233-        """Save progress to JSON file."""
scripts/daemon/linear_progress.py-234-        self.last_updated = datetime.now().isoformat()
scripts/daemon/linear_progress.py-235-        self.daemon_pid = os.getpid()
scripts/daemon/linear_progress.py-236-
scripts/daemon/linear_progress.py-237-        try:
scripts/daemon/linear_progress.py:238:            path.parent.mkdir(parents=True, exist_ok=True)
scripts/daemon/linear_progress.py-239-            with open(path, 'w', encoding='utf-8') as f:
scripts/daemon/linear_progress.py-240-                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
scripts/daemon/linear_progress.py-241-        except Exception as e:
scripts/daemon/linear_progress.py-242-            print(f"[LinearProgress] Error saving progress: {e}")
scripts/daemon/linear_progress.py-243-
--
scripts/bmad/scan_feedback.py-192-
scripts/bmad/scan_feedback.py-193-
scripts/bmad/scan_feedback.py-194-def mode_batch_silent(results: list[dict]) -> None:
scripts/bmad/scan_feedback.py-195-    if not results:
scripts/bmad/scan_feedback.py-196-        return
scripts/bmad/scan_feedback.py:197:    ANNOTATIONS_DIR.mkdir(parents=True, exist_ok=True)
scripts/bmad/scan_feedback.py-198-    failed_dir = ANNOTATIONS_DIR / "_failed"
scripts/bmad/scan_feedback.py-199-
scripts/bmad/scan_feedback.py-200-    for r in results:
scripts/bmad/scan_feedback.py-201-        anno_id = r.get("id", "unknown")
scripts/bmad/scan_feedback.py-202-        fname = anno_id if anno_id.startswith("ANNO-") else f"ANNO-{anno_id}"
--
scripts/bmad/scan_feedback.py-209-            out_file.write_text(
scripts/bmad/scan_feedback.py-210-                yaml.dump(payload, allow_unicode=True, default_flow_style=False),
scripts/bmad/scan_feedback.py-211-                encoding="utf-8",
scripts/bmad/scan_feedback.py-212-            )
scripts/bmad/scan_feedback.py-213-        except Exception as exc:
scripts/bmad/scan_feedback.py:214:            failed_dir.mkdir(parents=True, exist_ok=True)
scripts/bmad/scan_feedback.py-215-            err_file = failed_dir / f"{fname}.yaml"
scripts/bmad/scan_feedback.py-216-            err_file.write_text(
scripts/bmad/scan_feedback.py-217-                yaml.dump(
scripts/bmad/scan_feedback.py-218-                    {"id": anno_id, "error": str(exc), "_raw": r},
scripts/bmad/scan_feedback.py-219-                    allow_unicode=True,
--
scripts/daemon/worktree_scanner.py-104-                if line.startswith('worktree '):
scripts/daemon/worktree_scanner.py-105-                    current_path = Path(line[9:])
scripts/daemon/worktree_scanner.py-106-                elif line.startswith('branch refs/heads/'):
scripts/daemon/worktree_scanner.py-107-                    current_branch = line[18:]
scripts/daemon/worktree_scanner.py-108-                elif line == '' and current_path:
scripts/daemon/worktree_scanner.py:109:                    # End of worktree block
scripts/daemon/worktree_scanner.py-110-                    if self._is_dev_worktree(current_path):
scripts/daemon/worktree_scanner.py-111-                        story_id = self._extract_story_id(current_path.name)
scripts/daemon/worktree_scanner.py-112-                        worktrees.append(WorktreeInfo(
scripts/daemon/worktree_scanner.py-113-                            path=current_path,
scripts/daemon/worktree_scanner.py-114-                            branch=current_branch or "unknown",
--
scripts/daemon/linear_develop_daemon.py-154-
scripts/daemon/linear_develop_daemon.py-155-        return True
scripts/daemon/linear_develop_daemon.py-156-
scripts/daemon/linear_develop_daemon.py-157-    def _process_story(self, story_id: str) -> ParsedOutcome:
scripts/daemon/linear_develop_daemon.py-158-        """
scripts/daemon/linear_develop_daemon.py:159:        Process a single Story (blocking until complete).
scripts/daemon/linear_develop_daemon.py-160-
scripts/daemon/linear_develop_daemon.py-161-        Args:
scripts/daemon/linear_develop_daemon.py-162-            story_id: The Story ID to process
scripts/daemon/linear_develop_daemon.py-163-
scripts/daemon/linear_develop_daemon.py-164-        Returns:
--
scripts/daemon/linear_develop_daemon.py-192-
scripts/daemon/linear_develop_daemon.py-193-        except Exception as e:
scripts/daemon/linear_develop_daemon.py-194-            print(f"[Daemon] ERROR: Failed to spawn session: {e}")
scripts/daemon/linear_develop_daemon.py-195-            return ParsedOutcome(
scripts/daemon/linear_develop_daemon.py-196-                outcome=StoryOutcome.ERROR,
scripts/daemon/linear_develop_daemon.py:197:                blocking_reason=str(e),
scripts/daemon/linear_develop_daemon.py-198-            )
scripts/daemon/linear_develop_daemon.py-199-
scripts/daemon/linear_develop_daemon.py:200:        # Wait for process to complete (blocking)
scripts/daemon/linear_develop_daemon.py-201-        print(f"[Daemon] Waiting for Story {story_id} to complete...")
scripts/daemon/linear_develop_daemon.py-202-        return_code = self._current_process.wait()
scripts/daemon/linear_develop_daemon.py-203-        self._current_process = None
scripts/daemon/linear_develop_daemon.py-204-
scripts/daemon/linear_develop_daemon.py-205-        # Calculate duration
--
scripts/daemon/linear_develop_daemon.py-276-            if not self.progress.increment_compact_restart():
scripts/daemon/linear_develop_daemon.py-277-                print(f"[Daemon] CIRCUIT BREAKER: Too many compact restarts for Story {story_id}")
scripts/daemon/linear_develop_daemon.py-278-                self.progress.halt(f"Circuit breaker: {self.progress.max_compact_restarts}+ compact restarts")
scripts/daemon/linear_develop_daemon.py-279-            # Otherwise, continue with same story (current_index unchanged)
scripts/daemon/linear_develop_daemon.py-280-
scripts/daemon/linear_develop_daemon.py:281:        elif outcome.outcome.is_blocked():
scripts/daemon/linear_develop_daemon.py:282:            # Blocked - check if we should retry
scripts/daemon/linear_develop_daemon.py-283-            if self.progress.should_retry():
scripts/daemon/linear_develop_daemon.py-284-                print(f"[Daemon] BLOCKED - attempting retry ({self.progress.current_story.retry_count + 1}/{self.progress.max_retries + 1})")
scripts/daemon/linear_develop_daemon.py-285-                self.progress.increment_retry()
scripts/daemon/linear_develop_daemon.py-286-                # current_index unchanged, will retry same story
scripts/daemon/linear_develop_daemon.py-287-            else:
scripts/daemon/linear_develop_daemon.py-288-                # Already retried, halt
scripts/daemon/linear_develop_daemon.py:289:                print(f"[Daemon] HALT: Story {story_id} blocked after retry")
scripts/daemon/linear_develop_daemon.py:290:                reason = outcome.blocking_reason or outcome.outcome.value
scripts/daemon/linear_develop_daemon.py:291:                self.progress.halt(f"Story {story_id} blocked: {reason}")
scripts/daemon/linear_develop_daemon.py-292-
scripts/daemon/linear_develop_daemon.py-293-                # Record as completed (failed)
scripts/daemon/linear_develop_daemon.py-294-                self.progress.mark_story_complete(
scripts/daemon/linear_develop_daemon.py-295-                    story_id,
scripts/daemon/linear_develop_daemon.py-296-                    outcome.outcome,
--
scripts/daemon/linear_develop_daemon.py-299-                )
scripts/daemon/linear_develop_daemon.py-300-
scripts/daemon/linear_develop_daemon.py-301-        else:
scripts/daemon/linear_develop_daemon.py-302-            # Unknown or error
scripts/daemon/linear_develop_daemon.py-303-            print(f"[Daemon] WARNING: Unexpected outcome {outcome.outcome.value}")
scripts/daemon/linear_develop_daemon.py:304:            if outcome.blocking_reason:
scripts/daemon/linear_develop_daemon.py:305:                print(f"[Daemon]   Reason: {outcome.blocking_reason}")
scripts/daemon/linear_develop_daemon.py-306-
scripts/daemon/linear_develop_daemon.py-307-            # Treat as crash - restart
scripts/daemon/linear_develop_daemon.py-308-            if not self.progress.increment_compact_restart():
scripts/daemon/linear_develop_daemon.py-309-                self.progress.halt(f"Too many unknown outcomes for Story {story_id}")
scripts/daemon/linear_develop_daemon.py-310-
--
scripts/daemon/linear_outcome_parser.py-19-@dataclass
scripts/daemon/linear_outcome_parser.py-20-class ParsedOutcome:
scripts/daemon/linear_outcome_parser.py-21-    """Result of parsing a story execution."""
scripts/daemon/linear_outcome_parser.py-22-    outcome: StoryOutcome
scripts/daemon/linear_outcome_parser.py-23-    commit_sha: Optional[str] = None
scripts/daemon/linear_outcome_parser.py:24:    blocking_reason: Optional[str] = None
scripts/daemon/linear_outcome_parser.py-25-    duration_seconds: float = 0.0
scripts/daemon/linear_outcome_parser.py-26-    is_compact: bool = False
scripts/daemon/linear_outcome_parser.py-27-    raw_result: Optional[dict] = None
scripts/daemon/linear_outcome_parser.py-28-
scripts/daemon/linear_outcome_parser.py-29-
--
scripts/daemon/linear_outcome_parser.py-91-                    is_compact=True,
scripts/daemon/linear_outcome_parser.py-92-                )
scripts/daemon/linear_outcome_parser.py-93-            else:
scripts/daemon/linear_outcome_parser.py-94-                return ParsedOutcome(
scripts/daemon/linear_outcome_parser.py-95-                    outcome=StoryOutcome.CRASH,
scripts/daemon/linear_outcome_parser.py:96:                    blocking_reason=f"Process exited with code {return_code}",
scripts/daemon/linear_outcome_parser.py-97-                )
scripts/daemon/linear_outcome_parser.py-98-
scripts/daemon/linear_outcome_parser.py-99-        # Priority 3: Exit code 0 but no result file
scripts/daemon/linear_outcome_parser.py-100-        # This is unexpected - Claude should always write result
scripts/daemon/linear_outcome_parser.py-101-        return ParsedOutcome(
scripts/daemon/linear_outcome_parser.py-102-            outcome=StoryOutcome.UNKNOWN,
scripts/daemon/linear_outcome_parser.py:103:            blocking_reason="Process exited successfully but no result file found",
scripts/daemon/linear_outcome_parser.py-104-        )
scripts/daemon/linear_outcome_parser.py-105-
scripts/daemon/linear_outcome_parser.py-106-    def _parse_result_file(self, result_file: Path) -> ParsedOutcome:
scripts/daemon/linear_outcome_parser.py-107-        """Parse the .worktree-result.json file."""
scripts/daemon/linear_outcome_parser.py-108-        try:
--
scripts/daemon/linear_outcome_parser.py-113-            outcome = StoryOutcome.from_result_outcome(outcome_str)
scripts/daemon/linear_outcome_parser.py-114-
scripts/daemon/linear_outcome_parser.py-115-            return ParsedOutcome(
scripts/daemon/linear_outcome_parser.py-116-                outcome=outcome,
scripts/daemon/linear_outcome_parser.py-117-                commit_sha=data.get("commit_sha"),
scripts/daemon/linear_outcome_parser.py:118:                blocking_reason=data.get("blocking_reason"),
scripts/daemon/linear_outcome_parser.py-119-                duration_seconds=data.get("duration_seconds", 0.0),
scripts/daemon/linear_outcome_parser.py-120-                is_compact=False,
scripts/daemon/linear_outcome_parser.py-121-                raw_result=data,
scripts/daemon/linear_outcome_parser.py-122-            )
scripts/daemon/linear_outcome_parser.py-123-
scripts/daemon/linear_outcome_parser.py-124-        except json.JSONDecodeError as e:
scripts/daemon/linear_outcome_parser.py-125-            return ParsedOutcome(
scripts/daemon/linear_outcome_parser.py-126-                outcome=StoryOutcome.ERROR,
scripts/daemon/linear_outcome_parser.py:127:                blocking_reason=f"Invalid JSON in result file: {e}",
scripts/daemon/linear_outcome_parser.py-128-            )
scripts/daemon/linear_outcome_parser.py-129-        except Exception as e:
scripts/daemon/linear_outcome_parser.py-130-            return ParsedOutcome(
scripts/daemon/linear_outcome_parser.py-131-                outcome=StoryOutcome.ERROR,
scripts/daemon/linear_outcome_parser.py:132:                blocking_reason=f"Error reading result file: {e}",
scripts/daemon/linear_outcome_parser.py-133-            )
scripts/daemon/linear_outcome_parser.py-134-
scripts/daemon/linear_outcome_parser.py-135-    def _log_contains_compact(self, log_file: Path) -> bool:
scripts/daemon/linear_outcome_parser.py-136-        """
scripts/daemon/linear_outcome_parser.py-137-        Check if log file contains compact indicators.
--
scripts/daemon/linear_outcome_parser.py-188-
scripts/daemon/linear_outcome_parser.py-189-            # Check for success indicators
scripts/daemon/linear_outcome_parser.py-190-            if '"outcome": "SUCCESS"' in content or '"outcome":"SUCCESS"' in content:
scripts/daemon/linear_outcome_parser.py-191-                return True, "SUCCESS"
scripts/daemon/linear_outcome_parser.py-192-
scripts/daemon/linear_outcome_parser.py:193:            # Check for blocked indicators
scripts/daemon/linear_outcome_parser.py-194-            if '"outcome": "DEV_BLOCKED"' in content:
scripts/daemon/linear_outcome_parser.py-195-                return True, "DEV_BLOCKED"
scripts/daemon/linear_outcome_parser.py-196-            if '"outcome": "QA_BLOCKED"' in content:
scripts/daemon/linear_outcome_parser.py-197-                return True, "QA_BLOCKED"
scripts/daemon/linear_outcome_parser.py-198-
--
scripts/daemon/linear_outcome_parser.py-256-    parser = OutcomeParser()
scripts/daemon/linear_outcome_parser.py-257-
scripts/daemon/linear_outcome_parser.py-258-    # Test outcome mapping
scripts/daemon/linear_outcome_parser.py-259-    for outcome_str in ["SUCCESS", "DEV_BLOCKED", "QA_BLOCKED", "UNKNOWN"]:
scripts/daemon/linear_outcome_parser.py-260-        outcome = StoryOutcome.from_result_outcome(outcome_str)
scripts/daemon/linear_outcome_parser.py:261:        print(f"  {outcome_str} -> {outcome.value} (success={outcome.is_success()}, blocked={outcome.is_blocked()})")
scripts/daemon/linear_outcome_parser.py-262-
scripts/daemon/linear_outcome_parser.py-263-    # Test compact patterns
scripts/daemon/linear_outcome_parser.py-264-    test_lines = [
scripts/daemon/linear_outcome_parser.py-265-        "Compacting conversation...",
scripts/daemon/linear_outcome_parser.py-266-        "The context is being compacted",
--
scripts/daemon/qa_spawner.py-76-   *gate {story_id}         # Quality gate decision
scripts/daemon/qa_spawner.py-77-
scripts/daemon/qa_spawner.py-78-5. Based on gate result:
scripts/daemon/qa_spawner.py-79-   - If PASS/WAIVED: Update status to "ready-to-merge"
scripts/daemon/qa_spawner.py-80-   - If CONCERNS: Attempt 1 fix cycle, then re-gate
scripts/daemon/qa_spawner.py:81:   - If FAIL: Update status to "qa-blocked"
scripts/daemon/qa_spawner.py-82-
scripts/daemon/qa_spawner.py-83-6. Update .worktree-status.yaml with:
scripts/daemon/qa_spawner.py:84:   - status: "ready-to-merge" or "qa-blocked"
scripts/daemon/qa_spawner.py-85-   - qa_reviewed: true
scripts/daemon/qa_spawner.py-86-   - qa_gate: PASS/CONCERNS/FAIL/WAIVED
scripts/daemon/qa_spawner.py-87-
scripts/daemon/qa_spawner.py-88-7. Write .worktree-result.json with final outcome
scripts/daemon/qa_spawner.py-89-
--
scripts/daemon/qa_spawner.py-110-        self.max_concurrent = max_concurrent
scripts/daemon/qa_spawner.py-111-        self.allowed_tools = allowed_tools or self.DEFAULT_ALLOWED_TOOLS
scripts/daemon/qa_spawner.py-112-        self.max_turns = max_turns
scripts/daemon/qa_spawner.py-113-
scripts/daemon/qa_spawner.py-114-        self._sessions: Dict[str, QASession] = {}
scripts/daemon/qa_spawner.py:115:        self._lock = threading.Lock()
scripts/daemon/qa_spawner.py-116-
scripts/daemon/qa_spawner.py-117-    @property
scripts/daemon/qa_spawner.py-118-    def active_count(self) -> int:
scripts/daemon/qa_spawner.py-119-        """Get number of active (running) sessions."""
scripts/daemon/qa_spawner.py:120:        with self._lock:
scripts/daemon/qa_spawner.py-121-            return sum(
scripts/daemon/qa_spawner.py-122-                1 for s in self._sessions.values()
scripts/daemon/qa_spawner.py-123-                if s.state == QASessionState.RUNNING
scripts/daemon/qa_spawner.py-124-            )
scripts/daemon/qa_spawner.py-125-
scripts/daemon/qa_spawner.py-126-    @property
scripts/daemon/qa_spawner.py-127-    def pending_count(self) -> int:
scripts/daemon/qa_spawner.py-128-        """Get number of pending sessions."""
scripts/daemon/qa_spawner.py:129:        with self._lock:
scripts/daemon/qa_spawner.py-130-            return sum(
scripts/daemon/qa_spawner.py-131-                1 for s in self._sessions.values()
scripts/daemon/qa_spawner.py-132-                if s.state == QASessionState.PENDING
scripts/daemon/qa_spawner.py-133-            )
scripts/daemon/qa_spawner.py-134-
--
scripts/daemon/qa_spawner.py-141-            worktree_path: Path to the worktree
scripts/daemon/qa_spawner.py-142-
scripts/daemon/qa_spawner.py-143-        Returns:
scripts/daemon/qa_spawner.py-144-            True if session was spawned or queued
scripts/daemon/qa_spawner.py-145-        """
scripts/daemon/qa_spawner.py:146:        with self._lock:
scripts/daemon/qa_spawner.py-147-            # Check if already exists
scripts/daemon/qa_spawner.py-148-            if story_id in self._sessions:
scripts/daemon/qa_spawner.py-149-                existing = self._sessions[story_id]
scripts/daemon/qa_spawner.py-150-                if existing.state in [QASessionState.PENDING, QASessionState.RUNNING]:
scripts/daemon/qa_spawner.py-151-                    print(f"[QASpawner] Session already exists for Story {story_id}")
--
scripts/daemon/qa_spawner.py-192-                text=True,
scripts/daemon/qa_spawner.py-193-                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if hasattr(subprocess, 'CREATE_NEW_PROCESS_GROUP') else 0
scripts/daemon/qa_spawner.py-194-            )
scripts/daemon/qa_spawner.py-195-
scripts/daemon/qa_spawner.py-196-            # Record session
scripts/daemon/qa_spawner.py:197:            with self._lock:
scripts/daemon/qa_spawner.py-198-                self._sessions[story_id] = QASession(
scripts/daemon/qa_spawner.py-199-                    story_id=story_id,
scripts/daemon/qa_spawner.py-200-                    worktree_path=worktree_path,
scripts/daemon/qa_spawner.py-201-                    state=QASessionState.RUNNING,
scripts/daemon/qa_spawner.py-202-                    process=process,
--
scripts/daemon/qa_spawner.py-215-            print(f"[QASpawner]   Log: {log_file}")
scripts/daemon/qa_spawner.py-216-            return True
scripts/daemon/qa_spawner.py-217-
scripts/daemon/qa_spawner.py-218-        except Exception as e:
scripts/daemon/qa_spawner.py-219-            print(f"[QASpawner] Failed to spawn QA session for {story_id}: {e}")
scripts/daemon/qa_spawner.py:220:            with self._lock:
scripts/daemon/qa_spawner.py-221-                self._sessions[story_id] = QASession(
scripts/daemon/qa_spawner.py-222-                    story_id=story_id,
scripts/daemon/qa_spawner.py-223-                    worktree_path=worktree_path,
scripts/daemon/qa_spawner.py-224-                    state=QASessionState.FAILED,
scripts/daemon/qa_spawner.py-225-                    error_message=str(e)
--
scripts/daemon/qa_spawner.py-234-
scripts/daemon/qa_spawner.py-235-        try:
scripts/daemon/qa_spawner.py-236-            # Wait for process to complete
scripts/daemon/qa_spawner.py-237-            return_code = session.process.wait()
scripts/daemon/qa_spawner.py-238-
scripts/daemon/qa_spawner.py:239:            with self._lock:
scripts/daemon/qa_spawner.py-240-                session.completed_at = datetime.now()
scripts/daemon/qa_spawner.py-241-                session.return_code = return_code
scripts/daemon/qa_spawner.py-242-                session.state = (
scripts/daemon/qa_spawner.py-243-                    QASessionState.COMPLETED if return_code == 0
scripts/daemon/qa_spawner.py-244-                    else QASessionState.FAILED
--
scripts/daemon/qa_spawner.py-257-            except:
scripts/daemon/qa_spawner.py-258-                pass
scripts/daemon/qa_spawner.py-259-
scripts/daemon/qa_spawner.py-260-    def _process_pending_queue(self):
scripts/daemon/qa_spawner.py-261-        """Process pending sessions if capacity available."""
scripts/daemon/qa_spawner.py:262:        with self._lock:
scripts/daemon/qa_spawner.py-263-            if self.active_count >= self.max_concurrent:
scripts/daemon/qa_spawner.py-264-                return
scripts/daemon/qa_spawner.py-265-
scripts/daemon/qa_spawner.py-266-            # Find pending sessions
scripts/daemon/qa_spawner.py-267-            for story_id, session in list(self._sessions.items()):
scripts/daemon/qa_spawner.py-268-                if session.state == QASessionState.PENDING:
scripts/daemon/qa_spawner.py:269:                    # Remove lock temporarily to spawn
scripts/daemon/qa_spawner.py-270-                    break
scripts/daemon/qa_spawner.py-271-            else:
scripts/daemon/qa_spawner.py-272-                return
scripts/daemon/qa_spawner.py-273-
scripts/daemon/qa_spawner.py:274:        # Spawn outside lock
scripts/daemon/qa_spawner.py-275-        if session.state == QASessionState.PENDING:
scripts/daemon/qa_spawner.py-276-            self._spawn(story_id, session.worktree_path)
scripts/daemon/qa_spawner.py-277-
scripts/daemon/qa_spawner.py-278-    def get_session(self, story_id: str) -> Optional[QASession]:
scripts/daemon/qa_spawner.py-279-        """Get session info for a story."""
--
scripts/daemon/qa_spawner.py-283-        """Get all sessions."""
scripts/daemon/qa_spawner.py-284-        return dict(self._sessions)
scripts/daemon/qa_spawner.py-285-
scripts/daemon/qa_spawner.py-286-    def get_status_summary(self) -> dict:
scripts/daemon/qa_spawner.py-287-        """Get summary of all sessions."""
scripts/daemon/qa_spawner.py:288:        with self._lock:
scripts/daemon/qa_spawner.py-289-            return {
scripts/daemon/qa_spawner.py-290-                "total": len(self._sessions),
scripts/daemon/qa_spawner.py-291-                "running": self.active_count,
scripts/daemon/qa_spawner.py-292-                "pending": self.pending_count,
scripts/daemon/qa_spawner.py-293-                "completed": sum(1 for s in self._sessions.values() if s.state == QASessionState.COMPLETED),
--
scripts/daemon/qa_gate_generator.py-72-        Returns:
scripts/daemon/qa_gate_generator.py-73-            GateResult with file path and status
scripts/daemon/qa_gate_generator.py-74-        """
scripts/daemon/qa_gate_generator.py-75-        try:
scripts/daemon/qa_gate_generator.py-76-            # Ensure output directory exists
scripts/daemon/qa_gate_generator.py:77:            output_dir.mkdir(parents=True, exist_ok=True)
scripts/daemon/qa_gate_generator.py-78-
scripts/daemon/qa_gate_generator.py-79-            # Generate filename
scripts/daemon/qa_gate_generator.py-80-            slug = self._slugify(story_title)
scripts/daemon/qa_gate_generator.py-81-            filename = f"{story_id}-{slug}.yml"
scripts/daemon/qa_gate_generator.py-82-            gate_file = output_dir / filename
--
scripts/daemon/qa_gate_generator.py-152-        if gate_status == "PASS":
scripts/daemon/qa_gate_generator.py-153-            status_reason = f"Story {story_id} 通过所有验证，代码质量符合标准"
scripts/daemon/qa_gate_generator.py-154-        elif gate_status == "CONCERNS":
scripts/daemon/qa_gate_generator.py-155-            status_reason = f"Story {story_id} 存在非关键问题，需要团队评审"
scripts/daemon/qa_gate_generator.py-156-        elif gate_status == "FAIL":
scripts/daemon/qa_gate_generator.py:157:            status_reason = result.get("blocking_reason", f"Story {story_id} 验证失败")
scripts/daemon/qa_gate_generator.py-158-        elif gate_status == "WAIVED":
scripts/daemon/qa_gate_generator.py-159-            status_reason = f"Story {story_id} 问题已知并接受"
scripts/daemon/qa_gate_generator.py-160-        else:
scripts/daemon/qa_gate_generator.py-161-            status_reason = f"Story {story_id} 自动化验证完成"
scripts/daemon/qa_gate_generator.py-162-
--
scripts/daemon/story_file_updater.py-128-
scripts/daemon/story_file_updater.py-129-            # Sync to main repo if this is a worktree
scripts/daemon/story_file_updater.py-130-            synced = False
scripts/daemon/story_file_updater.py-131-            if worktree_path != main_repo_path:
scripts/daemon/story_file_updater.py-132-                main_story_file = main_repo_path / "docs" / "stories" / story_file.name
scripts/daemon/story_file_updater.py:133:                main_story_file.parent.mkdir(parents=True, exist_ok=True)
scripts/daemon/story_file_updater.py-134-                main_story_file.write_text(content, encoding="utf-8")
scripts/daemon/story_file_updater.py-135-                synced = True
scripts/daemon/story_file_updater.py-136-
scripts/daemon/story_file_updater.py-137-            return UpdateResult(
scripts/daemon/story_file_updater.py-138-                story_file=story_file,
--
scripts/daemon/tests/test_story_file_updater.py-207-            worktree_path = Path(tmpdir) / "worktree"
scripts/daemon/tests/test_story_file_updater.py-208-            main_repo_path = Path(tmpdir) / "main"
scripts/daemon/tests/test_story_file_updater.py-209-
scripts/daemon/tests/test_story_file_updater.py-210-            # Create directories
scripts/daemon/tests/test_story_file_updater.py-211-            worktree_stories = worktree_path / "docs" / "stories"
scripts/daemon/tests/test_story_file_updater.py:212:            worktree_stories.mkdir(parents=True)
scripts/daemon/tests/test_story_file_updater.py-213-            main_stories = main_repo_path / "docs" / "stories"
scripts/daemon/tests/test_story_file_updater.py:214:            main_stories.mkdir(parents=True)
scripts/daemon/tests/test_story_file_updater.py-215-
scripts/daemon/tests/test_story_file_updater.py-216-            # Create story file
scripts/daemon/tests/test_story_file_updater.py-217-            story_file = worktree_stories / "15.1.story.md"
scripts/daemon/tests/test_story_file_updater.py-218-            story_file.write_text(story_content_with_placeholders, encoding="utf-8")
scripts/daemon/tests/test_story_file_updater.py-219-
--
scripts/compare-iterations.py-262-            output = generate_comparison_report(comparison)
scripts/compare-iterations.py-263-
scripts/compare-iterations.py-264-        # 输出结果
scripts/compare-iterations.py-265-        if args.output:
scripts/compare-iterations.py-266-            output_path = Path(args.output)
scripts/compare-iterations.py:267:            output_path.parent.mkdir(parents=True, exist_ok=True)
scripts/compare-iterations.py-268-            with open(output_path, 'w', encoding='utf-8') as f:
scripts/compare-iterations.py-269-                f.write(output)
scripts/compare-iterations.py-270-            print_status(f"Report saved to: {output_path}", "success")
scripts/compare-iterations.py-271-        else:
scripts/compare-iterations.py-272-            print("\n" + output)
--
scripts/migrate_story_frontmatter.py-60-def inject_frontmatter(content: str, fields: dict) -> str:
scripts/migrate_story_frontmatter.py-61-    fm = {
scripts/migrate_story_frontmatter.py-62-        "doc_type": "story",
scripts/migrate_story_frontmatter.py-63-        **fields,
scripts/migrate_story_frontmatter.py-64-        "depends_on": [],
scripts/migrate_story_frontmatter.py:65:        "blocks": [],
scripts/migrate_story_frontmatter.py-66-        "trace": {"decisions": [], "bugs": []},
scripts/migrate_story_frontmatter.py-67-    }
scripts/migrate_story_frontmatter.py-68-    fm_str = yaml.dump(fm, allow_unicode=True, default_flow_style=False).strip()
scripts/migrate_story_frontmatter.py-69-    return f"---\n{fm_str}\n---\n\n{content}"
scripts/migrate_story_frontmatter.py-70-
--
scripts/harness/story_harness.py-138-                    self.progress.increment_retry(story.id)
scripts/harness/story_harness.py-139-                else:
scripts/harness/story_harness.py-140-                    self.progress.mark_failed(
scripts/harness/story_harness.py-141-                        story.id,
scripts/harness/story_harness.py-142-                        gate_result,
scripts/harness/story_harness.py:143:                        error_message=result.get("blocking_reason", "Gate failed")
scripts/harness/story_harness.py-144-                    )
scripts/harness/story_harness.py-145-                    print(f"[StoryHarness] [X] Story {story.id} failed after max retries, halting")
scripts/harness/story_harness.py-146-                    self.progress.halt(f"Story {story.id} failed after max retries")
scripts/harness/story_harness.py-147-                    break
scripts/harness/story_harness.py-148-
--
scripts/harness/story_harness.py-222-        return {
scripts/harness/story_harness.py-223-            "story_id": story_id,
scripts/harness/story_harness.py-224-            "outcome": "ERROR",
scripts/harness/story_harness.py-225-            "tests_passed": False,
scripts/harness/story_harness.py-226-            "qa_gate": None,
scripts/harness/story_harness.py:227:            "blocking_reason": "No result file generated",
scripts/harness/story_harness.py-228-        }
scripts/harness/story_harness.py-229-
scripts/harness/story_harness.py-230-    def _run_gate(self, story_id: str, result: Dict[str, Any]) -> GateResult:
scripts/harness/story_harness.py-231-        """
scripts/harness/story_harness.py-232-        Run simplified CommitGate (G3+G4 only).
--
scripts/generate_state_graph_viz.py-24-    # Get Mermaid diagram
scripts/generate_state_graph_viz.py-25-    mermaid_str = canvas_agentic_rag.get_graph().draw_mermaid()
scripts/generate_state_graph_viz.py-26-
scripts/generate_state_graph_viz.py-27-    # Determine output path
scripts/generate_state_graph_viz.py-28-    output_path = Path(__file__).parent.parent / "docs" / "architecture" / "state-graph.mmd"
scripts/generate_state_graph_viz.py:29:    output_path.parent.mkdir(parents=True, exist_ok=True)
scripts/generate_state_graph_viz.py-30-
scripts/generate_state_graph_viz.py-31-    # Save to file
scripts/generate_state_graph_viz.py-32-    with open(output_path, "w", encoding="utf-8") as f:
scripts/generate_state_graph_viz.py-33-        f.write(mermaid_str)
scripts/generate_state_graph_viz.py-34-
--
scripts/daemon/linear_session_spawner.py-44-**DECISION POINT A - TEST RESULTS**:
scripts/daemon/linear_session_spawner.py-45-- If ALL tests PASS:
scripts/daemon/linear_session_spawner.py-46-  - Update .worktree-status.yaml: status="dev-complete", tests_passed=true
scripts/daemon/linear_session_spawner.py-47-  - PROCEED to Phase 2
scripts/daemon/linear_session_spawner.py-48-- If ANY test FAILS:
scripts/daemon/linear_session_spawner.py:49:  - Update .worktree-status.yaml: status="dev-blocked", tests_passed=false
scripts/daemon/linear_session_spawner.py-50-  - Write .worktree-result.json with outcome="DEV_BLOCKED"
scripts/daemon/linear_session_spawner.py-51-  - HALT WORKFLOW HERE - Do not proceed to QA
scripts/daemon/linear_session_spawner.py-52-
scripts/daemon/linear_session_spawner.py-53-===============================================================================
scripts/daemon/linear_session_spawner.py-54-PHASE 2: QUALITY ASSURANCE (Full QA Sequence)
--
scripts/daemon/linear_session_spawner.py-74-  - If still CONCERNS or FAIL after 1 fix attempt:
scripts/daemon/linear_session_spawner.py-75-    - Update status: qa_gate="CONCERNS"
scripts/daemon/linear_session_spawner.py-76-    - Write .worktree-result.json with outcome="QA_CONCERNS_UNFIXED"
scripts/daemon/linear_session_spawner.py-77-    - HALT WORKFLOW HERE
scripts/daemon/linear_session_spawner.py-78-- If gate = FAIL:
scripts/daemon/linear_session_spawner.py:79:  - Update .worktree-status.yaml: status="qa-blocked", qa_gate="FAIL"
scripts/daemon/linear_session_spawner.py-80-  - Write .worktree-result.json with outcome="QA_BLOCKED"
scripts/daemon/linear_session_spawner.py-81-  - HALT WORKFLOW HERE - Do not commit
scripts/daemon/linear_session_spawner.py-82-
scripts/daemon/linear_session_spawner.py-83-===============================================================================
scripts/daemon/linear_session_spawner.py-84-PHASE 3: GIT COMMIT (Only if QA Gate = PASS or WAIVED)
--
scripts/daemon/linear_session_spawner.py-116-  "tests_passed": true|false,
scripts/daemon/linear_session_spawner.py-117-  "test_count": [number],
scripts/daemon/linear_session_spawner.py-118-  "test_coverage": [percentage, e.g. 94.0],
scripts/daemon/linear_session_spawner.py-119-  "qa_gate": "PASS|CONCERNS|FAIL|WAIVED"|null,
scripts/daemon/linear_session_spawner.py-120-  "commit_sha": "[sha from git log -1 --format=%H]"|null,
scripts/daemon/linear_session_spawner.py:121:  "blocking_reason": "[reason if blocked]"|null,
scripts/daemon/linear_session_spawner.py-122-  "fix_attempts": 0|1,
scripts/daemon/linear_session_spawner.py-123-  "timestamp": "[ISO-8601 timestamp]",
scripts/daemon/linear_session_spawner.py-124-  "duration_seconds": [total seconds from start],
scripts/daemon/linear_session_spawner.py-125-
scripts/daemon/linear_session_spawner.py-126-  "dev_record": {{
--
scripts/health_check_epic12.py-79-        import lancedb
scripts/health_check_epic12.py-80-
scripts/health_check_epic12.py-81-        path = os.environ.get("LANCEDB_PATH", "./data/lancedb")
scripts/health_check_epic12.py-82-
scripts/health_check_epic12.py-83-        # 确保目录存在
scripts/health_check_epic12.py:84:        Path(path).mkdir(parents=True, exist_ok=True)
scripts/health_check_epic12.py-85-
scripts/health_check_epic12.py-86-        db = lancedb.connect(path)
scripts/health_check_epic12.py-87-        tables = db.table_names()
scripts/health_check_epic12.py-88-
scripts/health_check_epic12.py-89-        return True, f"Ready ({path})", {
--
scripts/daemon/worktree_watcher_daemon.py-137-                "base_path": str(self.base_path),
scripts/daemon/worktree_watcher_daemon.py-138-                "known_worktrees": list(self._known_worktrees),
scripts/daemon/worktree_watcher_daemon.py-139-                "qa_sessions": self.spawner.get_status_summary()
scripts/daemon/worktree_watcher_daemon.py-140-            }
scripts/daemon/worktree_watcher_daemon.py-141-
scripts/daemon/worktree_watcher_daemon.py:142:            self.state_file.parent.mkdir(parents=True, exist_ok=True)
scripts/daemon/worktree_watcher_daemon.py-143-            with open(self.state_file, 'w', encoding='utf-8') as f:
scripts/daemon/worktree_watcher_daemon.py-144-                json.dump(state, f, indent=2)
scripts/daemon/worktree_watcher_daemon.py-145-
scripts/daemon/worktree_watcher_daemon.py-146-        except Exception as e:
scripts/daemon/worktree_watcher_daemon.py-147-            print(f"[Daemon] Warning: Could not save state: {e}")
--
scripts/daemon/tests/test_post_process_hook.py-90-            tmpdir = Path(tmpdir)
scripts/daemon/tests/test_post_process_hook.py-91-
scripts/daemon/tests/test_post_process_hook.py-92-            # Create worktree structure
scripts/daemon/tests/test_post_process_hook.py-93-            worktree_path = tmpdir / "Canvas-develop-15.1"
scripts/daemon/tests/test_post_process_hook.py-94-            worktree_stories = worktree_path / "docs" / "stories"
scripts/daemon/tests/test_post_process_hook.py:95:            worktree_stories.mkdir(parents=True)
scripts/daemon/tests/test_post_process_hook.py-96-
scripts/daemon/tests/test_post_process_hook.py-97-            # Create main repo structure
scripts/daemon/tests/test_post_process_hook.py-98-            main_repo_path = tmpdir / "Canvas"
scripts/daemon/tests/test_post_process_hook.py-99-            main_stories = main_repo_path / "docs" / "stories"
scripts/daemon/tests/test_post_process_hook.py:100:            main_stories.mkdir(parents=True)
scripts/daemon/tests/test_post_process_hook.py-101-            main_qa_gates = main_repo_path / "docs" / "qa" / "gates"
scripts/daemon/tests/test_post_process_hook.py:102:            main_qa_gates.mkdir(parents=True)
scripts/daemon/tests/test_post_process_hook.py-103-
scripts/daemon/tests/test_post_process_hook.py-104-            # Create story file
scripts/daemon/tests/test_post_process_hook.py-105-            story_file = worktree_stories / "15.1.story.md"
scripts/daemon/tests/test_post_process_hook.py-106-            story_file.write_text(story_content_with_placeholders, encoding="utf-8")
scripts/daemon/tests/test_post_process_hook.py-107-
--
scripts/daemon/tests/test_post_process_hook.py-136-
scripts/daemon/tests/test_post_process_hook.py-137-    def test_process_missing_result_file(self):
scripts/daemon/tests/test_post_process_hook.py-138-        """Test process handles missing result file."""
scripts/daemon/tests/test_post_process_hook.py-139-        with TemporaryDirectory() as tmpdir:
scripts/daemon/tests/test_post_process_hook.py-140-            main_repo = Path(tmpdir) / "Canvas"
scripts/daemon/tests/test_post_process_hook.py:141:            main_repo.mkdir()
scripts/daemon/tests/test_post_process_hook.py-142-            worktree = Path(tmpdir) / "worktree"
scripts/daemon/tests/test_post_process_hook.py:143:            worktree.mkdir()
scripts/daemon/tests/test_post_process_hook.py-144-
scripts/daemon/tests/test_post_process_hook.py-145-            hook = PostProcessHook(main_repo)
scripts/daemon/tests/test_post_process_hook.py-146-            result = hook.process(
scripts/daemon/tests/test_post_process_hook.py-147-                story_id="15.1",
scripts/daemon/tests/test_post_process_hook.py-148-                worktree_path=worktree,
--
scripts/daemon/tests/test_post_process_hook.py-363-        with TemporaryDirectory() as tmpdir:
scripts/daemon/tests/test_post_process_hook.py-364-            tmpdir = Path(tmpdir)
scripts/daemon/tests/test_post_process_hook.py-365-
scripts/daemon/tests/test_post_process_hook.py-366-            # Create main repo
scripts/daemon/tests/test_post_process_hook.py-367-            main_repo = tmpdir / "Canvas"
scripts/daemon/tests/test_post_process_hook.py:368:            (main_repo / "docs" / "stories").mkdir(parents=True)
scripts/daemon/tests/test_post_process_hook.py:369:            (main_repo / "docs" / "qa" / "gates").mkdir(parents=True)
scripts/daemon/tests/test_post_process_hook.py-370-
scripts/daemon/tests/test_post_process_hook.py-371-            # Create worktree
scripts/daemon/tests/test_post_process_hook.py-372-            worktree = tmpdir / "Canvas-develop-15.1"
scripts/daemon/tests/test_post_process_hook.py-373-            worktree_stories = worktree / "docs" / "stories"
scripts/daemon/tests/test_post_process_hook.py:374:            worktree_stories.mkdir(parents=True)
scripts/daemon/tests/test_post_process_hook.py-375-
scripts/daemon/tests/test_post_process_hook.py-376-            # Create story file with placeholders
scripts/daemon/tests/test_post_process_hook.py-377-            story_content = """# Story 15.1: FastAPI Application Initialization
scripts/daemon/tests/test_post_process_hook.py-378-
scripts/daemon/tests/test_post_process_hook.py-379-## Status
--
scripts/setup-git-hooks.py-135-    print()
scripts/setup-git-hooks.py-136-    print("The pre-commit hook will now automatically:")
scripts/setup-git-hooks.py-137-    print("  1. Detect Planning Phase file changes")
scripts/setup-git-hooks.py-138-    print("  2. Create temporary snapshot")
scripts/setup-git-hooks.py-139-    print("  3. Run validation against previous iteration")
scripts/setup-git-hooks.py:140:    print("  4. Block commit if breaking changes detected")
scripts/setup-git-hooks.py-141-    print()
scripts/setup-git-hooks.py-142-    print("To bypass the hook (NOT RECOMMENDED):")
scripts/setup-git-hooks.py-143-    print("  git commit -n -m \"message\"")
scripts/setup-git-hooks.py-144-    print()
scripts/setup-git-hooks.py-145-    print("To accept breaking changes:")
--
scripts/daemon/tests/test_qa_gate_generator.py-49-                "recommendations": ["Add OpenTelemetry integration", "Improve error handling"]
scripts/daemon/tests/test_qa_gate_generator.py-50-            }
scripts/daemon/tests/test_qa_gate_generator.py-51-        }
scripts/daemon/tests/test_qa_gate_generator.py-52-
scripts/daemon/tests/test_qa_gate_generator.py-53-    @pytest.fixture
scripts/daemon/tests/test_qa_gate_generator.py:54:    def sample_result_blocked(self):
scripts/daemon/tests/test_qa_gate_generator.py-55-        """Sample .worktree-result.json data for DEV_BLOCKED outcome."""
scripts/daemon/tests/test_qa_gate_generator.py-56-        return {
scripts/daemon/tests/test_qa_gate_generator.py-57-            "story_id": "12.6",
scripts/daemon/tests/test_qa_gate_generator.py-58-            "outcome": "DEV_BLOCKED",
scripts/daemon/tests/test_qa_gate_generator.py-59-            "tests_passed": False,
scripts/daemon/tests/test_qa_gate_generator.py-60-            "test_count": 20,
scripts/daemon/tests/test_qa_gate_generator.py-61-            "qa_gate": None,
scripts/daemon/tests/test_qa_gate_generator.py:62:            "blocking_reason": "Unit tests failing - import error in module",
scripts/daemon/tests/test_qa_gate_generator.py-63-            "qa_record": {}
scripts/daemon/tests/test_qa_gate_generator.py-64-        }
scripts/daemon/tests/test_qa_gate_generator.py-65-
scripts/daemon/tests/test_qa_gate_generator.py-66-    @pytest.fixture
scripts/daemon/tests/test_qa_gate_generator.py-67-    def sample_result_concerns(self):
--
scripts/daemon/tests/test_qa_gate_generator.py-131-
scripts/daemon/tests/test_qa_gate_generator.py-132-        # Check issues
scripts/daemon/tests/test_qa_gate_generator.py-133-        assert len(gate_data["top_issues"]) == 2
scripts/daemon/tests/test_qa_gate_generator.py-134-        assert gate_data["top_issues"][0]["severity"] == "low"
scripts/daemon/tests/test_qa_gate_generator.py-135-
scripts/daemon/tests/test_qa_gate_generator.py:136:    def test_build_gate_data_blocked(self, generator, sample_result_blocked):
scripts/daemon/tests/test_qa_gate_generator.py-137-        """Test gate data building for DEV_BLOCKED outcome."""
scripts/daemon/tests/test_qa_gate_generator.py:138:        gate_data = generator._build_gate_data("12.6", "Blocked Story", sample_result_blocked)
scripts/daemon/tests/test_qa_gate_generator.py-139-
scripts/daemon/tests/test_qa_gate_generator.py-140-        assert gate_data["gate"] == "FAIL"
scripts/daemon/tests/test_qa_gate_generator.py-141-        assert "Unit tests failing" in gate_data["status_reason"]
scripts/daemon/tests/test_qa_gate_generator.py-142-
scripts/daemon/tests/test_qa_gate_generator.py-143-    def test_build_gate_data_concerns(self, generator, sample_result_concerns):

exec
/bin/zsh -lc "rg -n -C 5 \"fsrs_due|learning_steps|review_card|quiz.*answer|rating\" backend/app frontend/src scripts canvas-vault/.claude/scripts --glob '*.py' --glob '*.ts' --glob '*.tsx'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
canvas-vault/.claude/scripts/sync_board_concepts.py-170-        beta 档显式 mastery_score 优先于 μ (两把锁的口径必须一致, 否则
canvas-vault/.claude/scripts/sync_board_concepts.py-171-        --check 与 dual_source_gap 会各说各话)。
canvas-vault/.claude/scripts/sync_board_concepts.py-172-
canvas-vault/.claude/scripts/sync_board_concepts.py-173-        ⚠️ 用 μ 而非 pick_score: μ 在闲置折旧下**严格不变** (effective 同比
canvas-vault/.claude/scripts/sync_board_concepts.py-174-        缩放 a,b), 所以行内掌握度不会因为「久没考」而过期 —— 唯一会改动它的
canvas-vault/.claude/scripts/sync_board_concepts.py:175:        是 quiz-answer 写分, 而写分后会立即触发一次本同步 (在唯一会变的时刻同步)。
canvas-vault/.claude/scripts/sync_board_concepts.py-176-        """
canvas-vault/.claude/scripts/sync_board_concepts.py-177-        a, b = fm_num(fm, "mastery_a"), fm_num(fm, "mastery_b")
canvas-vault/.claude/scripts/sync_board_concepts.py-178-        explicit = fm_num(fm, "mastery_score")
canvas-vault/.claude/scripts/sync_board_concepts.py-179-        if a is not None and b is not None:
canvas-vault/.claude/scripts/sync_board_concepts.py-180-            # ⛔ a/b 齐即 beta 档, 非正**不再回落 legacy** (审查 H4): 后端把
--
canvas-vault/.claude/scripts/sync_board_concepts.py-235-            )
canvas-vault/.claude/scripts/sync_board_concepts.py-236-            continue
canvas-vault/.claude/scripts/sync_board_concepts.py-237-        if any(c in path.stem for c in _WIKILINK_HOSTILE):
canvas-vault/.claude/scripts/sync_board_concepts.py-238-            warnings.append(f"节点名含 wikilink 敏感字符 {_WIKILINK_HOSTILE!r}, 生成的双链会断: {path.stem!r}")
canvas-vault/.claude/scripts/sync_board_concepts.py-239-        # ⛔ 状态量必须伴随显式分 (节点关系图审查后加的防线): 唯一写分路径
canvas-vault/.claude/scripts/sync_board_concepts.py:240:        # quiz-answer 的原子替换保证 mastery_a/b 与 mastery_score 同时写入,
canvas-vault/.claude/scripts/sync_board_concepts.py-241-        # 只有手工编辑才会造出「有状态量没显式分」的节点 — 那会让部分只读
canvas-vault/.claude/scripts/sync_board_concepts.py-242-        # mastery_score 的旧消费者显示「—」而权威口径显示 μ, 同屏打架。
canvas-vault/.claude/scripts/sync_board_concepts.py-243-        a, b = fm_num(fm, "mastery_a"), fm_num(fm, "mastery_b")
canvas-vault/.claude/scripts/sync_board_concepts.py-244-        if a is not None and b is not None and a > 0 and b > 0 and fm_num(fm, "mastery_score") is None:
canvas-vault/.claude/scripts/sync_board_concepts.py-245-            warnings.append(f"{path.stem!r}: 有 mastery_a/b 状态量但缺 mastery_score 显式分 (疑似手工编辑)")
--
scripts/daily_review_run.py-84-
scripts/daily_review_run.py-85-
scripts/daily_review_run.py-86-def _nodes_max_mtime(vault: Path) -> float:
scripts/daily_review_run.py-87-    """节点池最新改动时间 (CARD-A3 缓存失效判据)。
scripts/daily_review_run.py-88-
scripts/daily_review_run.py:89:    文件 mtime 抓原地更新 (quiz 写 fsrs_due 不动目录), 目录 mtime 抓
scripts/daily_review_run.py-90-    增删改名 (不留文件 mtime); 误报代价只是一次幂等重扫。保 mtime 的
scripts/daily_review_run.py-91-    还原类操作 (rsync -a / Time Machine) 不在本判据覆盖面内。
scripts/daily_review_run.py-92-    """
scripts/daily_review_run.py-93-    pool = vault / "节点"
scripts/daily_review_run.py-94-    latest = 0.0
--
scripts/daily_review_run.py-107-
scripts/daily_review_run.py-108-def ensure_payload(st: dict, now: datetime, today: str) -> tuple[dict | None, str]:
scripts/daily_review_run.py-109-    """当日 payload: 没有才生成 (生成过则复用 — 补跑只补推送)。
scripts/daily_review_run.py-110-
scripts/daily_review_run.py-111-    CARD-A3 (BATCH-2026-08-24-复习闭环): 复用多一道门 — 节点池比 payload
scripts/daily_review_run.py:112:    新 (quiz 写侧刚更新 fsrs_due / 新增重学卡) 则同日重扫, 否则当天到期的
scripts/daily_review_run.py-113-    重学卡永远进不了投影。push 去重不在此处: last_push_accepted_date 天然
scripts/daily_review_run.py-114-    保证同日只推一次。
scripts/daily_review_run.py-115-    """
scripts/daily_review_run.py-116-    payload_path = VAULT / "outputs" / "今日复习.json"
scripts/daily_review_run.py-117-    first_gen_today = st.get("last_generate_date") != today
--
canvas-vault/.claude/scripts/decay_beta.py-6-    与「越考越准」矛盾 (非平稳性盲点) → 拒绝原版
canvas-vault/.claude/scripts/decay_beta.py-7-  - 合成: 每次观测前按 γ 打折 (有效记忆窗口 ~1/(1-γ)=10 次), 收敛且能
canvas-vault/.claude/scripts/decay_beta.py-8-    跟随掌握状态跳变; σ 解析可得, 不再拍脑袋探索项
canvas-vault/.claude/scripts/decay_beta.py-9-
canvas-vault/.claude/scripts/decay_beta.py-10-被四方共用 (单一真相源):
canvas-vault/.claude/scripts/decay_beta.py:11:  - quiz-answer SKILL 静态 python 段 (写分): update_after_idle / mu / from_legacy
canvas-vault/.claude/scripts/decay_beta.py-12-  - start-exam-board SKILL 选点段: pick_score (μ−β·σ, 低者优先考)
canvas-vault/.claude/scripts/decay_beta.py-13-  - scripts/daily_review_pick.py (每日推送选板): effective + pick_score
canvas-vault/.claude/scripts/decay_beta.py-14-  - backend/tests/regression/test_decay_beta_convergence.py (数学性质锁定)
canvas-vault/.claude/scripts/decay_beta.py-15-"""
canvas-vault/.claude/scripts/decay_beta.py-16-
--
canvas-vault/.claude/scripts/fsrs_bridge.py-1-#!/usr/bin/env python3
canvas-vault/.claude/scripts/fsrs_bridge.py-2-"""FSRS WHEN 桥 (FSRS-V2-2026-07-30, [Decision-FSRS-1/2])。
canvas-vault/.claude/scripts/fsrs_bridge.py-3-
canvas-vault/.claude/scripts/fsrs_bridge.py:4:职责: 把 quiz-answer 的一次评分翻译成 py-fsrs 复习, 产出 6 个加性
canvas-vault/.claude/scripts/fsrs_bridge.py:5:frontmatter 字段 (fsrs_due/state/step/stability/difficulty/last_review)。
canvas-vault/.claude/scripts/fsrs_bridge.py-6-无字段 = New 卡即刻到期 (零迁移)。
canvas-vault/.claude/scripts/fsrs_bridge.py-7-
canvas-vault/.claude/scripts/fsrs_bridge.py:8:调用形态: quiz-answer 静态段用系统 python3 (stdlib) 经 stdin JSON 调本
canvas-vault/.claude/scripts/fsrs_bridge.py-9-文件; 本文件发现 fsrs 不可导入时自动 re-exec backend/.venv python。
canvas-vault/.claude/scripts/fsrs_bridge.py-10-调度计算全部收拢在写侧 — 读侧 (daily_review_pick/Dashboard) 只做字符串
canvas-vault/.claude/scripts/fsrs_bridge.py-11-日期比较, 维持 launchd 纯 stdlib 契约 (审查报告 §四-④)。
canvas-vault/.claude/scripts/fsrs_bridge.py-12-
canvas-vault/.claude/scripts/fsrs_bridge.py-13-参数契约: DEFAULT_PARAMETERS + desired_retention=0.9 + enable_fuzzing=False
--
canvas-vault/.claude/scripts/fsrs_bridge.py-40-        if c.exists():
canvas-vault/.claude/scripts/fsrs_bridge.py-41-            return str(c)
canvas-vault/.claude/scripts/fsrs_bridge.py-42-    return None
canvas-vault/.claude/scripts/fsrs_bridge.py-43-
canvas-vault/.claude/scripts/fsrs_bridge.py-44-FIELD_ORDER = (
canvas-vault/.claude/scripts/fsrs_bridge.py:45:    "fsrs_due", "fsrs_state", "fsrs_step",
canvas-vault/.claude/scripts/fsrs_bridge.py-46-    "fsrs_stability", "fsrs_difficulty", "fsrs_last_review",
canvas-vault/.claude/scripts/fsrs_bridge.py-47-)
canvas-vault/.claude/scripts/fsrs_bridge.py-48-
canvas-vault/.claude/scripts/fsrs_bridge.py-49-
canvas-vault/.claude/scripts/fsrs_bridge.py-50-def _aware(s: str) -> datetime:
--
canvas-vault/.claude/scripts/fsrs_bridge.py-54-
canvas-vault/.claude/scripts/fsrs_bridge.py-55-def _iso(dt: datetime) -> str:
canvas-vault/.claude/scripts/fsrs_bridge.py-56-    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
canvas-vault/.claude/scripts/fsrs_bridge.py-57-
canvas-vault/.claude/scripts/fsrs_bridge.py-58-
canvas-vault/.claude/scripts/fsrs_bridge.py:59:def rating_from_grade(grade_norm: float, abandoned: bool) -> int:
canvas-vault/.claude/scripts/fsrs_bridge.py-60-    """[Decision-FSRS-1] 弃答→Again; 否则还原 grade=1+3·gn 就近落四档。"""
canvas-vault/.claude/scripts/fsrs_bridge.py-61-    if abandoned:
canvas-vault/.claude/scripts/fsrs_bridge.py-62-        return 1
canvas-vault/.claude/scripts/fsrs_bridge.py-63-    g = 1.0 + 3.0 * max(0.0, min(1.0, float(grade_norm)))
canvas-vault/.claude/scripts/fsrs_bridge.py-64-    if g < 1.5:
--
canvas-vault/.claude/scripts/fsrs_bridge.py-84-    """一次评分 → 新 fsrs_* 字段 (需要 fsrs 可导入)。"""
canvas-vault/.claude/scripts/fsrs_bridge.py-85-    from fsrs import Card, Rating, Scheduler, State
canvas-vault/.claude/scripts/fsrs_bridge.py-86-
canvas-vault/.claude/scripts/fsrs_bridge.py-87-    now = _aware(ts)
canvas-vault/.claude/scripts/fsrs_bridge.py-88-    sched = Scheduler(enable_fuzzing=False)
canvas-vault/.claude/scripts/fsrs_bridge.py:89:    if fields.get("fsrs_due"):
canvas-vault/.claude/scripts/fsrs_bridge.py-90-        step = fields.get("fsrs_step")
canvas-vault/.claude/scripts/fsrs_bridge.py-91-        card = Card(
canvas-vault/.claude/scripts/fsrs_bridge.py-92-            state=State(int(fields.get("fsrs_state", 1))),
canvas-vault/.claude/scripts/fsrs_bridge.py-93-            step=int(step) if step not in (None, "") else None,
canvas-vault/.claude/scripts/fsrs_bridge.py-94-            stability=float(fields["fsrs_stability"]) if fields.get("fsrs_stability") else None,
canvas-vault/.claude/scripts/fsrs_bridge.py-95-            difficulty=float(fields["fsrs_difficulty"]) if fields.get("fsrs_difficulty") else None,
canvas-vault/.claude/scripts/fsrs_bridge.py:96:            due=_aware(fields["fsrs_due"]),
canvas-vault/.claude/scripts/fsrs_bridge.py-97-            last_review=_aware(fields["fsrs_last_review"]) if fields.get("fsrs_last_review") else None,
canvas-vault/.claude/scripts/fsrs_bridge.py-98-        )
canvas-vault/.claude/scripts/fsrs_bridge.py-99-    else:
canvas-vault/.claude/scripts/fsrs_bridge.py-100-        card = Card(due=now)  # 无字段 = New 卡即刻到期 (零迁移)
canvas-vault/.claude/scripts/fsrs_bridge.py-101-
canvas-vault/.claude/scripts/fsrs_bridge.py:102:    card, _log = sched.review_card(
canvas-vault/.claude/scripts/fsrs_bridge.py:103:        card, Rating(rating_from_grade(grade_norm, abandoned)), review_datetime=now
canvas-vault/.claude/scripts/fsrs_bridge.py-104-    )
canvas-vault/.claude/scripts/fsrs_bridge.py-105-    out = {
canvas-vault/.claude/scripts/fsrs_bridge.py:106:        "fsrs_due": _iso(card.due),
canvas-vault/.claude/scripts/fsrs_bridge.py-107-        "fsrs_state": int(card.state),
canvas-vault/.claude/scripts/fsrs_bridge.py-108-        "fsrs_step": card.step if card.step is not None else "",
canvas-vault/.claude/scripts/fsrs_bridge.py-109-        "fsrs_stability": round(card.stability, 4) if card.stability is not None else "",
canvas-vault/.claude/scripts/fsrs_bridge.py-110-        "fsrs_difficulty": round(card.difficulty, 4) if card.difficulty is not None else "",
canvas-vault/.claude/scripts/fsrs_bridge.py-111-        "fsrs_last_review": _iso(now),
--
scripts/spec-tools/verify-sync.py-268-                f.write(clean_report)
scripts/spec-tools/verify-sync.py-269-            print(f"\nReport saved to: {report_path}")
scripts/spec-tools/verify-sync.py-270-
scripts/spec-tools/verify-sync.py-271-    # 自动修复
scripts/spec-tools/verify-sync.py-272-    if args.fix and (not spec_age['exists'] or spec_age['age_days'] > 7):
scripts/spec-tools/verify-sync.py:273:        print("\nRegenerating OpenAPI spec...")
scripts/spec-tools/verify-sync.py-274-        os.system(f"python {project_root / 'scripts' / 'spec-tools' / 'export-openapi.py'}")
scripts/spec-tools/verify-sync.py-275-
scripts/spec-tools/verify-sync.py-276-    # 返回码
scripts/spec-tools/verify-sync.py-277-    if comparison['sync_rate'] < 80 or spec_age.get('age_days', 0) > 30:
scripts/spec-tools/verify-sync.py-278-        sys.exit(1)
--
scripts/spec-tools/api-reality-dashboard.py-53-def load_or_generate_openapi() -> Dict:
scripts/spec-tools/api-reality-dashboard.py-54-    """Load OpenAPI spec, generate if not exists."""
scripts/spec-tools/api-reality-dashboard.py-55-    spec_path = BACKEND_DIR / "openapi.json"
scripts/spec-tools/api-reality-dashboard.py-56-
scripts/spec-tools/api-reality-dashboard.py-57-    if not spec_path.exists():
scripts/spec-tools/api-reality-dashboard.py:58:        print(f"  {color('Generating OpenAPI from code...', Colors.YELLOW)}")
scripts/spec-tools/api-reality-dashboard.py-59-        os.system(f'cd "{BACKEND_DIR}" && python ../scripts/spec-tools/export-openapi.py')
scripts/spec-tools/api-reality-dashboard.py-60-
scripts/spec-tools/api-reality-dashboard.py-61-    if spec_path.exists():
scripts/spec-tools/api-reality-dashboard.py-62-        with open(spec_path, 'r', encoding='utf-8') as f:
scripts/spec-tools/api-reality-dashboard.py-63-            return json.load(f)
--
backend/app/services/verification_service.py-2476-        # Story 31.4 AC-31.4.2: Determine question angle based on history
backend/app/services/verification_service.py-2477-        if history_questions:
backend/app/services/verification_service.py-2478-            # Have history - generate question from a new angle
backend/app/services/verification_service.py-2479-            logger.info(
backend/app/services/verification_service.py-2480-                f"Found {len(history_questions)} existing questions for concept '{concept}', "
backend/app/services/verification_service.py:2481:                "generating alternative angle question"
backend/app/services/verification_service.py-2482-            )
backend/app/services/verification_service.py-2483-            question = await self._generate_alternative_question(
backend/app/services/verification_service.py-2484-                concept=concept,
backend/app/services/verification_service.py-2485-                canvas_name=canvas_name,
backend/app/services/verification_service.py-2486-                history_questions=history_questions,
--
backend/app/services/verification_service.py-2490-            if return_difficulty_info:
backend/app/services/verification_service.py-2491-                return self._build_question_response_with_difficulty(question, difficulty)
backend/app/services/verification_service.py-2492-            return question
backend/app/services/verification_service.py-2493-
backend/app/services/verification_service.py-2494-        # No history - generate standard question with difficulty adaptation
backend/app/services/verification_service.py:2495:        logger.debug(f"No history found for concept '{concept}', generating difficulty-adapted question")
backend/app/services/verification_service.py-2496-
backend/app/services/verification_service.py-2497-        # P2: Get enriched context (RAG + Graph + FSRS in parallel)
backend/app/services/verification_service.py-2498-        enriched = await self._get_enriched_context(
backend/app/services/verification_service.py-2499-            concept,
backend/app/services/verification_service.py-2500-            canvas_name,
--
backend/app/services/verification_service.py-2707-        difficulty: Optional[DifficultyResult] = None,
backend/app/services/verification_service.py-2708-        graph_context: Optional[Dict[str, Any]] = None,
backend/app/services/verification_service.py-2709-        fsrs_context: Optional[Dict[str, Any]] = None,
backend/app/services/verification_service.py-2710-    ) -> str:
backend/app/services/verification_service.py-2711-        """
backend/app/services/verification_service.py:2712:        Build a prompt for generating angle-specific verification questions.
backend/app/services/verification_service.py-2713-
backend/app/services/verification_service.py-2714-        Story 31.4 AC-31.4.2: Different angles for diverse question coverage.
backend/app/services/verification_service.py-2715-        Story 31.5: Incorporate difficulty level into prompt generation.
backend/app/services/verification_service.py-2716-
backend/app/services/verification_service.py-2717-        Args:
--
scripts/daily_review_pick.py-44-#: ⚠ 只匹配文件名: 真实节点 frontmatter 可能引用测试会话 id (live 实测
scripts/daily_review_pick.py-45-#: Fundamentals 的 error_candidates 含 m3-e2e-sessionend-test, 按全文匹配会误杀)
scripts/daily_review_pick.py-46-TEST_MARKERS = ("TestConcept", "UAT-2.5", "m3-e2e")
scripts/daily_review_pick.py-47-
scripts/daily_review_pick.py-48-#: [Decision-FSRS-2] WHEN/WHAT 分工 (FSRS-V2-2026-07-30):
scripts/daily_review_pick.py:49:#: FSRS 管 WHEN — fsrs_due 决定今天谁到期, 无字段 = New 卡即刻到期;
scripts/daily_review_pick.py-50-#: 衰减 Beta 管 WHAT — 到期集合内按 pick=μ−σ 排序。
scripts/daily_review_pick.py-51-#: 本文件保持纯 stdlib: 只做 UTC 定长字符串日期比较, 不 import fsrs。
scripts/daily_review_pick.py-52-
scripts/daily_review_pick.py-53-#: Bark 通知标题上限 (方案规范: ≤20 全角字符)
scripts/daily_review_pick.py-54-TITLE_LIMIT = 20
--
scripts/daily_review_pick.py-151-            stats["corrupt"] += 1
scripts/daily_review_pick.py-152-            ineligible["corrupt"].append(stem)
scripts/daily_review_pick.py-153-            print(f"[pick] Beta 参数溢出跳过 {stem}: pick={pick}", file=sys.stderr)
scripts/daily_review_pick.py-154-            continue
scripts/daily_review_pick.py-155-
scripts/daily_review_pick.py:156:        fsrs_due = _fm_str(fm, "fsrs_due") or ""
scripts/daily_review_pick.py-157-        due_fail_open = False
scripts/daily_review_pick.py-158-        # Code-Review M2: Obsidian Properties 面板可能把 datetime 重新序列化成
scripts/daily_review_pick.py-159-        # 带偏移格式, 词法比较会反向误判「永不到期」。非规范格式 fail-open
scripts/daily_review_pick.py-160-        # 视同到期 (与 New 语义一致), 不静默消失。
scripts/daily_review_pick.py-161-        # Codex-A2 M2: 形状正确但日历非法 (如月份 13) 词法比较会误判成未来,
scripts/daily_review_pick.py-162-        # 同样 fail-open — 脏值策略统一为一条。
scripts/daily_review_pick.py:163:        if fsrs_due:
scripts/daily_review_pick.py:164:            due_ok = bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", fsrs_due))
scripts/daily_review_pick.py-165-            if due_ok:
scripts/daily_review_pick.py-166-                try:
scripts/daily_review_pick.py:167:                    datetime.strptime(fsrs_due, "%Y-%m-%dT%H:%M:%SZ")
scripts/daily_review_pick.py-168-                except ValueError:
scripts/daily_review_pick.py-169-                    due_ok = False
scripts/daily_review_pick.py-170-            if not due_ok:
scripts/daily_review_pick.py:171:                print(f"[pick] fsrs_due 非规范格式, 视同到期: {stem} ({fsrs_due})", file=sys.stderr)
scripts/daily_review_pick.py:172:                fsrs_due = ""
scripts/daily_review_pick.py-173-                due_fail_open = True
scripts/daily_review_pick.py-174-        nodes.append({
scripts/daily_review_pick.py-175-            "node": stem,
scripts/daily_review_pick.py-176-            "board": _board_name(_fm_str(fm, "source_board")),
scripts/daily_review_pick.py-177-            "state": state,
scripts/daily_review_pick.py-178-            "pick": pick,
scripts/daily_review_pick.py-179-            "idle_days": idle_days,          # None = 从未考
scripts/daily_review_pick.py-180-            "last_examined": last_exam or "",
scripts/daily_review_pick.py:181:            "fsrs_due": fsrs_due,
scripts/daily_review_pick.py:182:            "due_now": (not fsrs_due) or fsrs_due <= now_z,  # 无字段 = New 即刻到期
scripts/daily_review_pick.py-183-            "due_fail_open": due_fail_open,
scripts/daily_review_pick.py-184-            "difficulty": _fm_str(fm, "fsrs_difficulty") or "",
scripts/daily_review_pick.py-185-        })
scripts/daily_review_pick.py-186-    return nodes, stats, ineligible
scripts/daily_review_pick.py-187-
--
scripts/daily_review_pick.py-199-    ranked, upcoming = [], []
scripts/daily_review_pick.py-200-    for board, members in boards.items():
scripts/daily_review_pick.py-201-        due = [n for n in members if n["due_now"]]
scripts/daily_review_pick.py-202-        if not due:
scripts/daily_review_pick.py-203-            # WHEN: 全员未到期 → 不进推荐榜, 记最近的未来到期 (F1 放假语义)
scripts/daily_review_pick.py:204:            nxt = min(members, key=lambda n: n["fsrs_due"])
scripts/daily_review_pick.py:205:            upcoming.append({"board": board, "next_due": nxt["fsrs_due"], "node": nxt["node"]})
scripts/daily_review_pick.py-206-            continue
scripts/daily_review_pick.py-207-        top = min(due, key=lambda n: n["pick"])   # WHAT: 到期集合内衰减 Beta 排序
scripts/daily_review_pick.py-208-        ranked.append({
scripts/daily_review_pick.py-209-            "board": board,
scripts/daily_review_pick.py-210-            "top_node": top["node"],
scripts/daily_review_pick.py-211-            "priority": round(top["pick"], 4),
scripts/daily_review_pick.py-212-            "pending": len(due),                   # 到期即待复习 (Decision-FSRS-2)
scripts/daily_review_pick.py-213-            "idle_days": (None if top["idle_days"] is None else int(top["idle_days"])),
scripts/daily_review_pick.py-214-            "difficulty": top["difficulty"],
scripts/daily_review_pick.py:215:            "next_due": min((n["fsrs_due"] for n in members if not n["due_now"]), default=""),
scripts/daily_review_pick.py-216-            "_tie": (
scripts/daily_review_pick.py-217-                round(top["pick"], 8),
scripts/daily_review_pick.py-218-                board_last_recommended.get(board, ""),   # 空串 = 从未被推荐, 排最前
scripts/daily_review_pick.py-219-                min(n["last_examined"] for n in due),    # 空串 = 有从未考节点, 排最前
scripts/daily_review_pick.py-220-                board,
--
scripts/daily_review_pick.py-250-        {
scripts/daily_review_pick.py-251-            "node": n["node"],
scripts/daily_review_pick.py-252-            "board": n["board"],
scripts/daily_review_pick.py-253-            "state": n["state"],
scripts/daily_review_pick.py-254-            "pick": round(n["pick"], 4),
scripts/daily_review_pick.py:255:            "fsrs_due": n["fsrs_due"],           # 空串 = 新卡即刻到期
scripts/daily_review_pick.py-256-            # Codex-A2 M1: 消费方须能区分真新卡与 fail-open 的脏日期卡
scripts/daily_review_pick.py-257-            "due_reason": ("malformed" if n["due_fail_open"]
scripts/daily_review_pick.py:258:                           else ("scheduled" if n["fsrs_due"] else "new")),
scripts/daily_review_pick.py-259-            "last_examined": n["last_examined"],
scripts/daily_review_pick.py-260-            "difficulty": n["difficulty"],
scripts/daily_review_pick.py-261-        }
scripts/daily_review_pick.py-262-        for n in nodes if n["board"] and n["due_now"]
scripts/daily_review_pick.py-263-    ]
--
scripts/daily_review_pick.py-328-    if payload.get("unassigned_nodes"):
scripts/daily_review_pick.py-329-        lines += ["", "> ⚠ 未归板节点（无 source_board，不参与推荐）: "
scripts/daily_review_pick.py-330-                  + "、".join(payload["unassigned_nodes"])]
scripts/daily_review_pick.py-331-    lines += [
scripts/daily_review_pick.py-332-        "",
scripts/daily_review_pick.py:333:        "> WHEN=FSRS 到期（无 fsrs_due 字段 = 新卡即刻到期）；WHAT=到期集合内按 μ−σ 排序",
scripts/daily_review_pick.py-334-        "> （含闲置回升，证据质量半衰期 69 天）。未剖析占位节点已跳过；命令已绑定最该考节点。",
scripts/daily_review_pick.py-335-    ]
scripts/daily_review_pick.py-336-    return "\n".join(lines) + "\n"
scripts/daily_review_pick.py-337-
scripts/daily_review_pick.py-338-
--
scripts/generate-file-index.py-203-    endpoints = extract_openapi_endpoints()
scripts/generate-file-index.py-204-
scripts/generate-file-index.py-205-    print("[*] Extracting JSON schemas...")
scripts/generate-file-index.py-206-    schemas = extract_json_schemas()
scripts/generate-file-index.py-207-
scripts/generate-file-index.py:208:    print("[*] Generating markdown...")
scripts/generate-file-index.py-209-    markdown = generate_markdown(files_by_dir, endpoints, schemas)
scripts/generate-file-index.py-210-
scripts/generate-file-index.py-211-    output_path = PROJECT_ROOT / args.output
scripts/generate-file-index.py-212-    with open(output_path, 'w', encoding='utf-8') as f:
scripts/generate-file-index.py-213-        f.write(markdown)
--
scripts/generate_state_graph_viz.py-17-from agentic_rag.state_graph import canvas_agentic_rag
scripts/generate_state_graph_viz.py-18-
scripts/generate_state_graph_viz.py-19-
scripts/generate_state_graph_viz.py-20-def main():
scripts/generate_state_graph_viz.py-21-    """Generate and save Mermaid diagram"""
scripts/generate_state_graph_viz.py:22:    print("Generating Mermaid visualization for Canvas Agentic RAG StateGraph...")
scripts/generate_state_graph_viz.py-23-
scripts/generate_state_graph_viz.py-24-    # Get Mermaid diagram
scripts/generate_state_graph_viz.py-25-    mermaid_str = canvas_agentic_rag.get_graph().draw_mermaid()
scripts/generate_state_graph_viz.py-26-
scripts/generate_state_graph_viz.py-27-    # Determine output path
--
scripts/daemon/linear_develop_daemon.py-41-from post_process_hook import PostProcessHook
scripts/daemon/linear_develop_daemon.py-42-
scripts/daemon/linear_develop_daemon.py-43-
scripts/daemon/linear_develop_daemon.py-44-class LinearDevelopDaemon:
scripts/daemon/linear_develop_daemon.py-45-    """
scripts/daemon/linear_develop_daemon.py:46:    Main daemon orchestrating sequential Story development.
scripts/daemon/linear_develop_daemon.py-47-
scripts/daemon/linear_develop_daemon.py-48-    Features:
scripts/daemon/linear_develop_daemon.py-49-    - 24/7 unattended operation
scripts/daemon/linear_develop_daemon.py-50-    - Automatic compact/crash recovery
scripts/daemon/linear_develop_daemon.py-51-    - Single retry on failure
--
scripts/daemon/worktree_watcher_daemon.py-28-from daemon.qa_spawner import QASessionSpawner
scripts/daemon/worktree_watcher_daemon.py-29-
scripts/daemon/worktree_watcher_daemon.py-30-
scripts/daemon/worktree_watcher_daemon.py-31-class WorktreeWatcherDaemon:
scripts/daemon/worktree_watcher_daemon.py-32-    """
scripts/daemon/worktree_watcher_daemon.py:33:    Main daemon orchestrating worktree monitoring and QA session spawning.
scripts/daemon/worktree_watcher_daemon.py-34-
scripts/daemon/worktree_watcher_daemon.py-35-    This daemon:
scripts/daemon/worktree_watcher_daemon.py-36-    1. Scans for active worktrees periodically
scripts/daemon/worktree_watcher_daemon.py-37-    2. Monitors status files for changes using watchdog
scripts/daemon/worktree_watcher_daemon.py-38-    3. Triggers QA sessions when dev-complete is detected
--
backend/app/services/learning_event_log.py-11-  - event_type: 限 8 类核心动作 (EVENT_TYPES), 未知类型拒绝 — 防事件膨胀
backend/app/services/learning_event_log.py-12-
backend/app/services/learning_event_log.py-13-写点 (批次3' 接入 4 个, node_derived 留批次4' 拆分补强):
backend/app/services/learning_event_log.py-14-  backend: candidate_created (蒸馏) / candidate_accepted / candidate_disputed
backend/app/services/learning_event_log.py-15-           (= dispute 三件套第三件「可追溯」suppression log) / session_archived
backend/app/services/learning_event_log.py:16:  vault:   answer_scored / answer_abandoned (quiz-answer) / exam_created
backend/app/services/learning_event_log.py-17-           (start-exam-board) — SKILL 静态 python 直接 append 同一文件
backend/app/services/learning_event_log.py-18-"""
backend/app/services/learning_event_log.py-19-
backend/app/services/learning_event_log.py-20-from __future__ import annotations
backend/app/services/learning_event_log.py-21-
--
scripts/daemon/post_process_hook.py-220-            result_data: Parsed result data
scripts/daemon/post_process_hook.py-221-
scripts/daemon/post_process_hook.py-222-        Returns:
scripts/daemon/post_process_hook.py-223-            GateResult from QAGateGenerator
scripts/daemon/post_process_hook.py-224-        """
scripts/daemon/post_process_hook.py:225:        print(f"[PostProcessHook] Generating QA Gate for {story_id}...")
scripts/daemon/post_process_hook.py-226-
scripts/daemon/post_process_hook.py-227-        output_dir = self.base_path / self.QA_GATES_DIR
scripts/daemon/post_process_hook.py-228-
scripts/daemon/post_process_hook.py-229-        result = self.gate_generator.generate_gate(
scripts/daemon/post_process_hook.py-230-            story_id=story_id,
--
backend/app/services/review_service.py-25-#    - Card difficulty (1-10 scale)
backend/app/services/review_service.py-26-#    - Review history (reps, lapses)
backend/app/services/review_service.py-27-#    - Desired retention rate (default: 90%)
backend/app/services/review_service.py-28-#
backend/app/services/review_service.py-29-# BACKWARD COMPATIBILITY (AC-32.2.4):
backend/app/services/review_service.py:30:# - score (0-100) is still accepted and auto-converted to FSRS rating (1-4)
backend/app/services/review_service.py-31-# - Conversion logic:
backend/app/services/review_service.py:32:#   * score < 40  → rating 1 (Again/Forgot) - needs immediate relearning
backend/app/services/review_service.py:33:#   * score 40-59 → rating 2 (Hard) - recalled with significant difficulty
backend/app/services/review_service.py:34:#   * score 60-84 → rating 3 (Good) - recalled with some effort
backend/app/services/review_service.py:35:#   * score >= 85 → rating 4 (Easy) - recalled effortlessly
backend/app/services/review_service.py-36-#
backend/app/services/review_service.py-37-# FSRS RATINGS (AC-32.2.2):
backend/app/services/review_service.py-38-# - 1 (Again): Completely forgot, reset to learning state
backend/app/services/review_service.py-39-# - 2 (Hard): Recalled with significant difficulty, shorter interval
backend/app/services/review_service.py-40-# - 3 (Good): Recalled with acceptable effort, optimal interval
--
backend/app/services/review_service.py-88-        sys.path.insert(0, str(_src_path))
backend/app/services/review_service.py-89-
backend/app/services/review_service.py-90-    from memory.temporal.fsrs_manager import (
backend/app/services/review_service.py-91-        CardState,
backend/app/services/review_service.py-92-        FSRSManager,
backend/app/services/review_service.py:93:        get_rating_from_score,
backend/app/services/review_service.py-94-    )
backend/app/services/review_service.py-95-
backend/app/services/review_service.py-96-    FSRS_AVAILABLE = True
backend/app/services/review_service.py-97-except ImportError:
backend/app/services/review_service.py-98-    FSRS_AVAILABLE = False
backend/app/services/review_service.py-99-    FSRSManager = None
backend/app/services/review_service.py:100:    get_rating_from_score = None
backend/app/services/review_service.py-101-    CardState = None
backend/app/services/review_service.py-102-
backend/app/services/review_service.py-103-# Story 38.3 AC-3 Code Review M2 Fix: Module-level runtime FSRS status.
backend/app/services/review_service.py-104-# FSRS_AVAILABLE = library importable (compile-time).
backend/app/services/review_service.py-105-# FSRS_RUNTIME_OK = FSRSManager actually initialized (runtime). None = not yet attempted.
--
backend/app/services/review_service.py-241-class ReviewService:
backend/app/services/review_service.py-242-    """
backend/app/services/review_service.py-243-    Review and verification canvas business logic service.
backend/app/services/review_service.py-244-
backend/app/services/review_service.py-245-    Provides async methods for:
backend/app/services/review_service.py:246:    - Generating verification canvases
backend/app/services/review_service.py-247-    - Scheduling reviews based on Ebbinghaus curve
backend/app/services/review_service.py-248-    - Tracking review progress
backend/app/services/review_service.py-249-
backend/app/services/review_service.py-250-    [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
backend/app/services/review_service.py-251-    """
--
backend/app/services/review_service.py-410-        self._task_canvas_map[task_id] = canvas_name
backend/app/services/review_service.py-411-
backend/app/services/review_service.py-412-        return {
backend/app/services/review_service.py-413-            "task_id": task_id,
backend/app/services/review_service.py-414-            "status": "processing",
backend/app/services/review_service.py:415:            "message": f"Generating verification canvas for {canvas_name}",
backend/app/services/review_service.py-416-        }
backend/app/services/review_service.py-417-
backend/app/services/review_service.py-418-    async def get_progress(self, task_id: str) -> ReviewProgress:
backend/app/services/review_service.py-419-        """
backend/app/services/review_service.py-420-        Get progress of a review generation task.
--
backend/app/services/review_service.py-570-
backend/app/services/review_service.py-571-        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
backend/app/services/review_service.py-572-        [Source: Story 24.1 - Mode Support Implementation]
backend/app/services/review_service.py-573-        """
backend/app/services/review_service.py-574-        logger.debug(
backend/app/services/review_service.py:575:            f"Generating verification canvas from: {source_canvas_name} "
backend/app/services/review_service.py-576-            f"(mode={mode}, weak_weight={weak_weight}, mastered_weight={mastered_weight})"
backend/app/services/review_service.py-577-        )
backend/app/services/review_service.py-578-
backend/app/services/review_service.py-579-        # Get all eligible concepts from canvas
backend/app/services/review_service.py-580-        # Mastery-aware: color filter kept as fallback; mastery engine provides
--
backend/app/services/review_service.py-705-            weak_concepts_data = [
backend/app/services/review_service.py-706-                {
backend/app/services/review_service.py-707-                    "concept_name": c.concept_name,
backend/app/services/review_service.py-708-                    "weakness_score": c.weakness_score,
backend/app/services/review_service.py-709-                    "failure_count": c.failure_count,
backend/app/services/review_service.py:710:                    "avg_rating": c.avg_rating,
backend/app/services/review_service.py-711-                }
backend/app/services/review_service.py-712-                for c in weight_data
backend/app/services/review_service.py-713-                if c.category == "weak"
backend/app/services/review_service.py-714-            ]
backend/app/services/review_service.py-715-
--
backend/app/services/review_service.py-905-    async def record_review_result(
backend/app/services/review_service.py-906-        self,
backend/app/services/review_service.py-907-        canvas_name: str,
backend/app/services/review_service.py-908-        concept_id: str = "",
backend/app/services/review_service.py-909-        score: Optional[float] = None,
backend/app/services/review_service.py:910:        rating: Optional[int] = None,
backend/app/services/review_service.py-911-        card_state: Optional[str] = None,
backend/app/services/review_service.py-912-        details: Optional[Dict[str, Any]] = None,
backend/app/services/review_service.py-913-    ) -> Dict[str, Any]:
backend/app/services/review_service.py-914-        """
backend/app/services/review_service.py-915-        Record the result of a review session using FSRS algorithm (Story 32.2).
backend/app/services/review_service.py-916-
backend/app/services/review_service.py:917:        Story 32.2 AC-32.2.2: Accepts FSRS ratings (1=Again, 2=Hard, 3=Good, 4=Easy)
backend/app/services/review_service.py-918-        Story 32.2 AC-32.2.3: Returns dynamically calculated next review date
backend/app/services/review_service.py-919-        Story 32.2 AC-32.2.4: Backward compatible with score-based inputs (0-100)
backend/app/services/review_service.py-920-
backend/app/services/review_service.py-921-        Args:
backend/app/services/review_service.py-922-            canvas_name: Canvas that was reviewed
backend/app/services/review_service.py-923-            concept_id: Concept identifier for card tracking
backend/app/services/review_service.py:924:            score: Legacy score (0-100), converted to rating if rating not provided
backend/app/services/review_service.py:925:            rating: FSRS rating (1=Again, 2=Hard, 3=Good, 4=Easy)
backend/app/services/review_service.py-926-            card_state: Optional serialized FSRS card JSON from previous review
backend/app/services/review_service.py-927-            details: Optional detailed scoring breakdown
backend/app/services/review_service.py-928-
backend/app/services/review_service.py-929-        Returns:
backend/app/services/review_service.py-930-            Recorded review result with FSRS state:
--
backend/app/services/review_service.py-942-        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
backend/app/services/review_service.py-943-        [Source: Story 32.2 - FSRS Integration]
backend/app/services/review_service.py-944-        """
backend/app/services/review_service.py-945-        logger.debug(f"Recording FSRS review result for {canvas_name}/{concept_id}")
backend/app/services/review_service.py-946-
backend/app/services/review_service.py:947:        # Story 32.2 AC-32.2.2/AC-32.2.4: Convert score to rating if needed
backend/app/services/review_service.py:948:        if rating is None and score is not None:
backend/app/services/review_service.py:949:            if get_rating_from_score is not None:
backend/app/services/review_service.py:950:                rating = get_rating_from_score(score)
backend/app/services/review_service.py:951:                logger.debug(f"Converted score {score} to FSRS rating {rating}")
backend/app/services/review_service.py-952-            else:
backend/app/services/review_service.py-953-                # Fallback conversion
backend/app/services/review_service.py-954-                if score < 40:
backend/app/services/review_service.py:955:                    rating = 1  # Again
backend/app/services/review_service.py-956-                elif score < 60:
backend/app/services/review_service.py:957:                    rating = 2  # Hard
backend/app/services/review_service.py-958-                elif score < 85:
backend/app/services/review_service.py:959:                    rating = 3  # Good
backend/app/services/review_service.py-960-                else:
backend/app/services/review_service.py:961:                    rating = 4  # Easy
backend/app/services/review_service.py:962:        elif rating is None:
backend/app/services/review_service.py:963:            rating = 3  # Default to Good if no input provided
backend/app/services/review_service.py-964-
backend/app/services/review_service.py:965:        # P0-3: Validate rating - handle non-integer types (e.g. "abc", 5.7)
backend/app/services/review_service.py-966-        try:
backend/app/services/review_service.py:967:            rating = int(rating)
backend/app/services/review_service.py-968-        except (TypeError, ValueError):
backend/app/services/review_service.py:969:            logger.warning(f"Invalid rating value '{rating}', defaulting to 3")
backend/app/services/review_service.py:970:            rating = 3
backend/app/services/review_service.py:971:        rating = max(1, min(4, rating))
backend/app/services/review_service.py-972-
backend/app/services/review_service.py-973-        # Story 32.2: Use FSRS for recording if available
backend/app/services/review_service.py-974-        if self._fsrs_manager is not None:
backend/app/services/review_service.py-975-            try:
backend/app/services/review_service.py-976-                # Load or create card (AC-32.2.4 backward compatibility)
--
backend/app/services/review_service.py-989-                        logger.info(
backend/app/services/review_service.py-990-                            f"Created new FSRS card for {concept_id} (migration from Ebbinghaus)"
backend/app/services/review_service.py-991-                        )
backend/app/services/review_service.py-992-
backend/app/services/review_service.py-993-                # Story 32.2 AC-32.2.3: Review card with FSRS algorithm
backend/app/services/review_service.py:994:                updated_card, review_log = self._fsrs_manager.review_card(card, rating)
backend/app/services/review_service.py-995-
backend/app/services/review_service.py-996-                # Get next due date (dynamically calculated by FSRS)
backend/app/services/review_service.py-997-                due_date = self._fsrs_manager.get_due_date(updated_card)
backend/app/services/review_service.py-998-
backend/app/services/review_service.py-999-                # Calculate interval in days
--
backend/app/services/review_service.py-1027-                    state_int = 0
backend/app/services/review_service.py-1028-
backend/app/services/review_service.py-1029-                return {
backend/app/services/review_service.py-1030-                    "canvas_name": canvas_name,
backend/app/services/review_service.py-1031-                    "concept_id": concept_id,
backend/app/services/review_service.py:1032:                    "rating": rating,
backend/app/services/review_service.py-1033-                    "score": score,  # Preserve original score for logging
backend/app/services/review_service.py-1034-                    "next_review": due_date.isoformat()
backend/app/services/review_service.py-1035-                    if due_date
backend/app/services/review_service.py-1036-                    else (
backend/app/services/review_service.py-1037-                        datetime.now(timezone.utc) + timedelta(days=interval_days)
--
backend/app/services/review_service.py-1068-            elif score >= 40:
backend/app/services/review_service.py-1069-                interval = 3
backend/app/services/review_service.py-1070-            else:
backend/app/services/review_service.py-1071-                interval = 1
backend/app/services/review_service.py-1072-        else:
backend/app/services/review_service.py:1073:            # Map rating to interval
backend/app/services/review_service.py:1074:            rating_intervals = {1: 1, 2: 3, 3: 7, 4: 30}
backend/app/services/review_service.py:1075:            interval = rating_intervals.get(rating, 1)
backend/app/services/review_service.py-1076-
backend/app/services/review_service.py-1077-        # Story 32.9 AC-1: next_review must be a future date, not "now"
backend/app/services/review_service.py-1078-        now_utc = datetime.now(timezone.utc)
backend/app/services/review_service.py-1079-        next_review_date = now_utc + timedelta(days=interval)
backend/app/services/review_service.py-1080-        return {
backend/app/services/review_service.py-1081-            "canvas_name": canvas_name,
backend/app/services/review_service.py-1082-            "concept_id": concept_id,
backend/app/services/review_service.py:1083:            "rating": rating,
backend/app/services/review_service.py-1084-            "score": score,
backend/app/services/review_service.py-1085-            "next_review": next_review_date.isoformat(),
backend/app/services/review_service.py-1086-            "interval_days": interval,
backend/app/services/review_service.py-1087-            "details": details or {},
backend/app/services/review_service.py-1088-            "recorded_at": now_utc.isoformat(),
--
backend/app/services/review_service.py-1175-                        "concept", memory.get("concept_name", "")
backend/app/services/review_service.py-1176-                    )
backend/app/services/review_service.py-1177-                    if concept_name and concept_name not in record_concept:
backend/app/services/review_service.py-1178-                        continue
backend/app/services/review_service.py-1179-
backend/app/services/review_service.py:1180:                    # Convert score (0-100) to rating (1-4)
backend/app/services/review_service.py-1181-                    score = memory.get("score", 60)
backend/app/services/review_service.py-1182-                    if score >= 85:
backend/app/services/review_service.py:1183:                        rating = 4
backend/app/services/review_service.py-1184-                    elif score >= 60:
backend/app/services/review_service.py:1185:                        rating = 3
backend/app/services/review_service.py-1186-                    elif score >= 40:
backend/app/services/review_service.py:1187:                        rating = 2
backend/app/services/review_service.py-1188-                    else:
backend/app/services/review_service.py:1189:                        rating = 1
backend/app/services/review_service.py-1190-
backend/app/services/review_service.py-1191-                    all_records.append(
backend/app/services/review_service.py-1192-                        {
backend/app/services/review_service.py-1193-                            "concept_id": memory.get(
backend/app/services/review_service.py-1194-                                "concept_id", memory.get("id", "")
backend/app/services/review_service.py-1195-                            ),
backend/app/services/review_service.py-1196-                            "concept_name": record_concept,
backend/app/services/review_service.py-1197-                            "canvas_path": record_canvas,
backend/app/services/review_service.py:1198:                            "rating": rating,
backend/app/services/review_service.py-1199-                            "review_time": timestamp_str,
backend/app/services/review_service.py-1200-                            "date": record_date.isoformat(),
backend/app/services/review_service.py-1201-                        }
backend/app/services/review_service.py-1202-                    )
backend/app/services/review_service.py-1203-
--
backend/app/services/review_service.py-1257-                    all_records.append(
backend/app/services/review_service.py-1258-                        {
backend/app/services/review_service.py-1259-                            "concept_id": key,
backend/app/services/review_service.py-1260-                            "concept_name": record_concept,
backend/app/services/review_service.py-1261-                            "canvas_path": record_canvas,
backend/app/services/review_service.py:1262:                            "rating": card_data.get("rating", 3),
backend/app/services/review_service.py-1263-                            "review_time": last_review,
backend/app/services/review_service.py-1264-                            "date": record_date.isoformat(),
backend/app/services/review_service.py-1265-                        }
backend/app/services/review_service.py-1266-                    )
backend/app/services/review_service.py-1267-                except (ValueError, AttributeError):
--
backend/app/services/review_service.py-1308-        for date_key in sorted(records_by_date.keys(), reverse=True):
backend/app/services/review_service.py-1309-            daily_records.append(
backend/app/services/review_service.py-1310-                {"date": date_key, "reviews": records_by_date[date_key]}
backend/app/services/review_service.py-1311-            )
backend/app/services/review_service.py-1312-
backend/app/services/review_service.py:1313:        # Story 34.12 AC3: Calculate retention_rate from rating data
backend/app/services/review_service.py:1314:        # retention_rate = count(rating >= 3) / count(total records with rating)
backend/app/services/review_service.py:1315:        rated_records = [r for r in all_records if r.get("rating") is not None]
backend/app/services/review_service.py-1316-        if rated_records:
backend/app/services/review_service.py:1317:            good_count = sum(1 for r in rated_records if r.get("rating", 0) >= 3)
backend/app/services/review_service.py-1318-            retention_rate = round(good_count / len(rated_records), 4)
backend/app/services/review_service.py-1319-        else:
backend/app/services/review_service.py-1320-            retention_rate = None
backend/app/services/review_service.py-1321-
backend/app/services/review_service.py-1322-        return {
--
backend/app/services/review_service.py-1604-
backend/app/services/review_service.py-1605-        Args:
backend/app/services/review_service.py-1606-            canvas_name: Canvas file name
backend/app/services/review_service.py-1607-
backend/app/services/review_service.py-1608-        Returns:
backend/app/services/review_service.py:1609:            List of review records with: concept_id, rating, timestamp, etc.
backend/app/services/review_service.py-1610-        """
backend/app/services/review_service.py-1611-        try:
backend/app/services/review_service.py-1612-            # Import learning memory client
backend/app/services/review_service.py-1613-            from app.clients.graphiti_client import get_learning_memory_client
backend/app/services/review_service.py-1614-
--
backend/app/services/review_service.py-2018-    async def save_card_state(
backend/app/services/review_service.py-2019-        self,
backend/app/services/review_service.py-2020-        concept_id: str,
backend/app/services/review_service.py-2021-        card_data: str,
backend/app/services/review_service.py-2022-        canvas_name: str,
backend/app/services/review_service.py:2023:        rating: int,
backend/app/services/review_service.py-2024-        score: Optional[float] = None,
backend/app/services/review_service.py-2025-    ) -> bool:
backend/app/services/review_service.py-2026-        """
backend/app/services/review_service.py-2027-        Save FSRS card state to persistence layer.
backend/app/services/review_service.py-2028-
--
backend/app/services/review_service.py-2030-
backend/app/services/review_service.py-2031-        Args:
backend/app/services/review_service.py-2032-            concept_id: Concept identifier
backend/app/services/review_service.py-2033-            card_data: Serialized FSRS card JSON
backend/app/services/review_service.py-2034-            canvas_name: Canvas file name
backend/app/services/review_service.py:2035:            rating: FSRS rating (1-4)
backend/app/services/review_service.py-2036-            score: Optional legacy score (0-100)
backend/app/services/review_service.py-2037-
backend/app/services/review_service.py-2038-        Returns:
backend/app/services/review_service.py-2039-            True if saved successfully
backend/app/services/review_service.py-2040-        """
--
backend/app/services/review_service.py-2053-
backend/app/services/review_service.py-2054-                # Create learning memory with FSRS data
backend/app/services/review_service.py-2055-                memory_data = {
backend/app/services/review_service.py-2056-                    "concept": concept_id,
backend/app/services/review_service.py-2057-                    "canvas_name": canvas_name,
backend/app/services/review_service.py:2058:                    "rating": rating,
backend/app/services/review_service.py-2059-                    "score": score,
backend/app/services/review_service.py-2060-                    "card_data": card_data,
backend/app/services/review_service.py-2061-                    "algorithm": "fsrs-4.5",
backend/app/services/review_service.py-2062-                    "timestamp": datetime.now(timezone.utc).isoformat(),
backend/app/services/review_service.py-2063-                }
--
backend/app/services/review_service.py-2155-                        memory_client = get_learning_memory_client()
backend/app/services/review_service.py-2156-                        await memory_client.initialize()
backend/app/services/review_service.py-2157-                        memory_data = {
backend/app/services/review_service.py-2158-                            "concept": cid,
backend/app/services/review_service.py-2159-                            "canvas_name": "auto-created",
backend/app/services/review_service.py:2160:                            "rating": 0,
backend/app/services/review_service.py-2161-                            "card_data": cdata,
backend/app/services/review_service.py-2162-                            "algorithm": "fsrs-4.5",
backend/app/services/review_service.py-2163-                            "auto_created": True,
backend/app/services/review_service.py-2164-                            "timestamp": datetime.now(timezone.utc).isoformat(),
backend/app/services/review_service.py-2165-                        }
--
backend/app/services/agent_service.py-1596-    ) -> AgentResult:
backend/app/services/agent_service.py-1597-        """Run the React Agent for a given agent type. Returns AgentResult.
backend/app/services/agent_service.py-1598-
backend/app/services/agent_service.py-1599-        Args:
backend/app/services/agent_service.py-1600-            gather_only: When True, agent only collects context (search + KG)
backend/app/services/agent_service.py:1601:                         without generating final explanation. Used in two-phase
backend/app/services/agent_service.py-1602-                         multimodal mode where Phase 4b (Vision) generates output.
backend/app/services/agent_service.py-1603-        [Source: Phase 2.5 — gather_only for two-phase multimodal]
backend/app/services/agent_service.py-1604-        """
backend/app/services/agent_service.py-1605-        from app.services.react_agent import run_react_agent
backend/app/services/agent_service.py-1606-
--
backend/app/services/agent_service.py-4196-            mastery_data = {}
backend/app/services/agent_service.py-4197-            try:
backend/app/services/agent_service.py-4198-                from app.clients.neo4j_client import get_neo4j_client
backend/app/services/agent_service.py-4199-                from app.services.mastery_engine import get_mastery_engine
backend/app/services/agent_service.py-4200-                from app.services.mastery_store import MasteryStore
backend/app/services/agent_service.py:4201:                from memory.temporal.fsrs_manager import get_rating_from_score
backend/app/services/agent_service.py-4202-
backend/app/services/agent_service.py:4203:                # Normalize 0-12 AutoSCORE to 0-100 for FSRS rating mapping
backend/app/services/agent_service.py-4204-                score_normalized = (
backend/app/services/agent_service.py-4205-                    (total_score / 12.0) * 100.0 if total_score > 0 else 0.0
backend/app/services/agent_service.py-4206-                )
backend/app/services/agent_service.py:4207:                grade = get_rating_from_score(score_normalized)
backend/app/services/agent_service.py-4208-                concept_id = node_id  # Use node_id as concept_id
backend/app/services/agent_service.py-4209-                engine = get_mastery_engine()  # Uses fusion-enabled singleton
backend/app/services/agent_service.py-4210-                store = MasteryStore(get_neo4j_client())
backend/app/services/agent_service.py-4211-                concept = await store.get_or_create_concept(
backend/app/services/agent_service.py-4212-                    concept_id,
--
backend/app/services/agent_service.py-4459-
backend/app/services/agent_service.py-4460-        context_len = len(adjacent_context) if adjacent_context else 0
backend/app/services/agent_service.py-4461-        images_count = len(images) if images else 0
backend/app/services/agent_service.py-4462-        rag_len = len(rag_context) if rag_context else 0  # Story 12.A.2
backend/app/services/agent_service.py-4463-        logger.debug(
backend/app/services/agent_service.py:4464:            f"Generating {explanation_type} explanation for node {node_id}, context_len={context_len}, images={images_count}, rag_context_len={rag_len}"
backend/app/services/agent_service.py-4465-        )
backend/app/services/agent_service.py-4466-
backend/app/services/agent_service.py-4467-        # ✅ FIX-4.4: 读取用户之前填写的个人理解
backend/app/services/agent_service.py-4468-        user_understandings = []
backend/app/services/agent_service.py-4469-        try:
--
backend/app/services/mastery_engine.py-283-            card = self.fsrs_manager.deserialize_card(concept.fsrs_card_data)
backend/app/services/mastery_engine.py-284-        else:
backend/app/services/mastery_engine.py-285-            card = self.fsrs_manager.create_card()
backend/app/services/mastery_engine.py-286-
backend/app/services/mastery_engine.py-287-        # Review with grade (1-4 maps directly to FSRS Rating)
backend/app/services/mastery_engine.py:288:        card, _log = self.fsrs_manager.review_card(card, grade)
backend/app/services/mastery_engine.py-289-
backend/app/services/mastery_engine.py-290-        # Store updated FSRS state back to concept.
backend/app/services/mastery_engine.py-291-        # fsrs 6.x: stability/difficulty can be None (new-card semantics) and
backend/app/services/mastery_engine.py-292-        # float(None) raises TypeError. ConceptState fields are non-Optional
backend/app/services/mastery_engine.py-293-        # floats whose consumers already guard with `> 0`, and the scheduler
--
backend/app/services/mastery_engine.py-645-        """Serialize concept state to API response dict (includes volatile fields)."""
backend/app/services/mastery_engine.py-646-        eff = self.effective_proficiency(concept)
backend/app/services/mastery_engine.py-647-        level = self.mastery_level(concept)
backend/app/services/mastery_engine.py-648-
backend/app/services/mastery_engine.py-649-        # Extract FSRS due date from card data (Story 5.4: Dashboard needs due_date for sorting)
backend/app/services/mastery_engine.py:650:        fsrs_due_date = None
backend/app/services/mastery_engine.py-651-        if self.fsrs_manager and concept.fsrs_card_data:
backend/app/services/mastery_engine.py-652-            try:
backend/app/services/mastery_engine.py-653-                card = self.fsrs_manager.deserialize_card(concept.fsrs_card_data)
backend/app/services/mastery_engine.py-654-                due = _card_attr(card, "due", None)
backend/app/services/mastery_engine.py-655-                if due is not None:
backend/app/services/mastery_engine.py-656-                    if isinstance(due, datetime):
backend/app/services/mastery_engine.py:657:                        fsrs_due_date = due.isoformat()
backend/app/services/mastery_engine.py-658-                    elif isinstance(due, str):
backend/app/services/mastery_engine.py:659:                        fsrs_due_date = due
backend/app/services/mastery_engine.py-660-            except Exception:
backend/app/services/mastery_engine.py-661-                pass  # Graceful degradation: no due date if card parse fails
backend/app/services/mastery_engine.py-662-
backend/app/services/mastery_engine.py-663-        # Story 5.6: Include fusion details if fusion engine is available
backend/app/services/mastery_engine.py-664-        fusion_details = None
--
backend/app/services/mastery_engine.py-689-            "mastery_level": level,
backend/app/services/mastery_engine.py-690-            "mastery_label": MASTERY_LABELS.get(level, "Unknown"),
backend/app/services/mastery_engine.py-691-            "mastery_color": MASTERY_COLORS.get(level, "#6c757d"),
backend/app/services/mastery_engine.py-692-            "retrievability": round(self._get_retrievability(concept), 3),
backend/app/services/mastery_engine.py-693-            "freshness": self.freshness(concept),
backend/app/services/mastery_engine.py:694:            "fsrs_due_date": fsrs_due_date,
backend/app/services/mastery_engine.py-695-            "override_active": concept.override_value is not None,
backend/app/services/mastery_engine.py-696-            "override_value": concept.override_value,
backend/app/services/mastery_engine.py-697-            "self_assess_value": concept.self_assess_value,
backend/app/services/mastery_engine.py-698-            "false_mastery_risk": round(self.false_mastery_risk(concept), 3),
backend/app/services/mastery_engine.py-699-            "interaction_count": concept.interaction_count,
--
backend/app/api/v1/endpoints/mastery.py-561-    """Get calibration summary for a concept node.
backend/app/api/v1/endpoints/mastery.py-562-
backend/app/api/v1/endpoints/mastery.py-563-    Three-stage progressive assessment:
backend/app/api/v1/endpoints/mastery.py-564-      Stage 1 (< 10 records): Data collection, no assessment
backend/app/api/v1/endpoints/mastery.py-565-      Stage 2 (10-20 records): Preliminary trends + signed_bias
backend/app/api/v1/endpoints/mastery.py:566:      Stage 3 (20+ records): Full report + absolute_bias + rating
backend/app/api/v1/endpoints/mastery.py-567-    """
backend/app/api/v1/endpoints/mastery.py-568-    resolved_group_id = _resolve_vault_group_id(
backend/app/api/v1/endpoints/mastery.py-569-        vault_id, subject_id=subject_id, legacy_group_id=group_id
backend/app/api/v1/endpoints/mastery.py-570-    )
backend/app/api/v1/endpoints/mastery.py-571-    store = _get_store()
--
backend/app/services/calibration_tracker.py-34-
backend/app/services/calibration_tracker.py-35-# Three-stage data thresholds
backend/app/services/calibration_tracker.py-36-STAGE_2_MIN_RECORDS = 10
backend/app/services/calibration_tracker.py-37-STAGE_3_MIN_RECORDS = 20
backend/app/services/calibration_tracker.py-38-
backend/app/services/calibration_tracker.py:39:# Calibration rating threshold
backend/app/services/calibration_tracker.py-40-CALIBRATION_BIAS_THRESHOLD = 0.15
backend/app/services/calibration_tracker.py-41-
backend/app/services/calibration_tracker.py-42-
backend/app/services/calibration_tracker.py-43-def _load_calibration_thresholds() -> None:
backend/app/services/calibration_tracker.py-44-    """Load calibration thresholds from mastery_config.json if present.
--
backend/app/services/calibration_tracker.py-159-        return 0.0
backend/app/services/calibration_tracker.py-160-    total = sum(abs(r.self_confidence - r.actual_performance) for r in records)
backend/app/services/calibration_tracker.py-161-    return round(total / len(records), 3)
backend/app/services/calibration_tracker.py-162-
backend/app/services/calibration_tracker.py-163-
backend/app/services/calibration_tracker.py:164:def compute_calibration_rating(
backend/app/services/calibration_tracker.py-165-    signed_bias: float, record_count: int
backend/app/services/calibration_tracker.py-166-) -> CalibrationRating:
backend/app/services/calibration_tracker.py:167:    """Determine calibration quality rating.
backend/app/services/calibration_tracker.py-168-
backend/app/services/calibration_tracker.py-169-    Three-stage progressive logic:
backend/app/services/calibration_tracker.py-170-      Stage 1 (< 10 records): INSUFFICIENT_DATA
backend/app/services/calibration_tracker.py-171-      Stage 2 (10-20 records): Preliminary — same thresholds, still computed
backend/app/services/calibration_tracker.py-172-      Stage 3 (20+ records): Reliable assessment
--
backend/app/services/calibration_tracker.py-256-def get_calibration_summary(records: List[CalibrationRecord]) -> CalibrationSummary:
backend/app/services/calibration_tracker.py-257-    """Compute calibration summary with three-stage progressive assessment.
backend/app/services/calibration_tracker.py-258-
backend/app/services/calibration_tracker.py-259-    Stage 1 (< 10): Data collection only, no assessment
backend/app/services/calibration_tracker.py-260-    Stage 2 (10-20): Preliminary trends (signed_bias + quadrant distribution)
backend/app/services/calibration_tracker.py:261:    Stage 3 (20+): Reliable assessment (full report + absolute_bias + rating)
backend/app/services/calibration_tracker.py-262-
backend/app/services/calibration_tracker.py-263-    Args:
backend/app/services/calibration_tracker.py-264-        records: All calibration records for a node
backend/app/services/calibration_tracker.py-265-
backend/app/services/calibration_tracker.py-266-    Returns:
--
backend/app/services/calibration_tracker.py-274-            stage=1,
backend/app/services/calibration_tracker.py-275-            record_count=count,
backend/app/services/calibration_tracker.py-276-            quadrant_distribution=compute_quadrant_distribution(records),
backend/app/services/calibration_tracker.py-277-            signed_bias=None,
backend/app/services/calibration_tracker.py-278-            absolute_bias=None,
backend/app/services/calibration_tracker.py:279:            calibration_rating=CalibrationRating.INSUFFICIENT_DATA,
backend/app/services/calibration_tracker.py-280-            stage_label=f"数据收集中（{count}/{STAGE_2_MIN_RECORDS}）",
backend/app/services/calibration_tracker.py-281-        )
backend/app/services/calibration_tracker.py-282-
backend/app/services/calibration_tracker.py-283-    signed_bias = compute_signed_bias(records)
backend/app/services/calibration_tracker.py-284-    quadrant_dist = compute_quadrant_distribution(records)
backend/app/services/calibration_tracker.py-285-
backend/app/services/calibration_tracker.py-286-    if count < STAGE_3_MIN_RECORDS:
backend/app/services/calibration_tracker.py-287-        # Stage 2: Preliminary trends
backend/app/services/calibration_tracker.py:288:        rating = compute_calibration_rating(signed_bias, count)
backend/app/services/calibration_tracker.py-289-        return CalibrationSummary(
backend/app/services/calibration_tracker.py-290-            stage=2,
backend/app/services/calibration_tracker.py-291-            record_count=count,
backend/app/services/calibration_tracker.py-292-            quadrant_distribution=quadrant_dist,
backend/app/services/calibration_tracker.py-293-            signed_bias=signed_bias,
backend/app/services/calibration_tracker.py-294-            absolute_bias=None,
backend/app/services/calibration_tracker.py:295:            calibration_rating=rating,
backend/app/services/calibration_tracker.py-296-            stage_label="初步趋势，仅供参考",
backend/app/services/calibration_tracker.py-297-        )
backend/app/services/calibration_tracker.py-298-
backend/app/services/calibration_tracker.py-299-    # Stage 3: Reliable assessment
backend/app/services/calibration_tracker.py-300-    absolute_bias = compute_absolute_bias(records)
backend/app/services/calibration_tracker.py:301:    rating = compute_calibration_rating(signed_bias, count)
backend/app/services/calibration_tracker.py-302-
backend/app/services/calibration_tracker.py-303-    return CalibrationSummary(
backend/app/services/calibration_tracker.py-304-        stage=3,
backend/app/services/calibration_tracker.py-305-        record_count=count,
backend/app/services/calibration_tracker.py-306-        quadrant_distribution=quadrant_dist,
backend/app/services/calibration_tracker.py-307-        signed_bias=signed_bias,
backend/app/services/calibration_tracker.py-308-        absolute_bias=absolute_bias,
backend/app/services/calibration_tracker.py:309:        calibration_rating=rating,
backend/app/services/calibration_tracker.py-310-        stage_label="可靠评估",
backend/app/services/calibration_tracker.py-311-    )
--
backend/app/services/exam_service_ext.py-465-
backend/app/services/exam_service_ext.py-466-async def skip_question(self, request: SkipRequest) -> SkipResponse:
backend/app/services/exam_service_ext.py-467-    """Skip the current question without BKT/FSRS penalty.
backend/app/services/exam_service_ext.py-468-
backend/app/services/exam_service_ext.py-469-    Skip != wrong answer. p_mastery stays unchanged.
backend/app/services/exam_service_ext.py:470:    FSRS: no rating event recorded.
backend/app/services/exam_service_ext.py-471-
backend/app/services/exam_service_ext.py-472-    [Source: Story 6.6 AC-4]
backend/app/services/exam_service_ext.py-473-    """
backend/app/services/exam_service_ext.py-474-    from app.clients.neo4j_client import get_neo4j_client
backend/app/services/exam_service_ext.py-475-
--
backend/app/services/weight_calculator.py-26-
backend/app/services/weight_calculator.py-27-    Attributes:
backend/app/services/weight_calculator.py-28-        concept_id: Unique concept identifier
backend/app/services/weight_calculator.py-29-        concept_name: Human-readable concept name
backend/app/services/weight_calculator.py-30-        weakness_score: Calculated weakness score (0.0-1.0)
backend/app/services/weight_calculator.py:31:        failure_count: Number of failed reviews (rating <= 2)
backend/app/services/weight_calculator.py:32:        avg_rating: Average review rating (1-4 scale)
backend/app/services/weight_calculator.py-33-        review_count: Total number of reviews
backend/app/services/weight_calculator.py-34-        days_since_review: Days since last review
backend/app/services/weight_calculator.py-35-        category: Classification ("weak", "borderline", "mastered")
backend/app/services/weight_calculator.py-36-    """
backend/app/services/weight_calculator.py-37-
backend/app/services/weight_calculator.py-38-    concept_id: str
backend/app/services/weight_calculator.py-39-    concept_name: str
backend/app/services/weight_calculator.py-40-    weakness_score: float  # 0.0-1.0
backend/app/services/weight_calculator.py-41-    failure_count: int
backend/app/services/weight_calculator.py:42:    avg_rating: float
backend/app/services/weight_calculator.py-43-    review_count: int
backend/app/services/weight_calculator.py-44-    days_since_review: int
backend/app/services/weight_calculator.py-45-    category: str  # "weak", "borderline", "mastered"
backend/app/services/weight_calculator.py-46-
backend/app/services/weight_calculator.py-47-
--
backend/app/services/weight_calculator.py-61-    WEAK_THRESHOLD = 0.6
backend/app/services/weight_calculator.py-62-    MASTERED_THRESHOLD = 0.4
backend/app/services/weight_calculator.py-63-    DEFAULT_NEW_SCORE = 0.5
backend/app/services/weight_calculator.py-64-
backend/app/services/weight_calculator.py-65-    # Score component weights (must sum to 1.0)
backend/app/services/weight_calculator.py:66:    RATING_WEIGHT = 0.4  # Avg rating impact
backend/app/services/weight_calculator.py-67-    FAILURE_WEIGHT = 0.3  # Failure count impact
backend/app/services/weight_calculator.py-68-    RECENCY_WEIGHT = 0.2  # Days since review impact
backend/app/services/weight_calculator.py-69-    TREND_WEIGHT = 0.1  # Improvement trend impact
backend/app/services/weight_calculator.py-70-
backend/app/services/weight_calculator.py-71-    async def calculate_weakness_scores(
--
backend/app/services/weight_calculator.py-73-    ) -> List[ConceptWeightData]:
backend/app/services/weight_calculator.py-74-        """
backend/app/services/weight_calculator.py-75-        Calculate weakness scores for all concepts.
backend/app/services/weight_calculator.py-76-
backend/app/services/weight_calculator.py-77-        AC1: Weakness Score Calculation
backend/app/services/weight_calculator.py:78:        - Factors in: average_rating, failure_count, days_since_last_review, trend_direction
backend/app/services/weight_calculator.py-79-        - Higher weakness_score = weaker concept = higher priority
backend/app/services/weight_calculator.py-80-
backend/app/services/weight_calculator.py-81-        Args:
backend/app/services/weight_calculator.py-82-            concepts: List of concept dicts with id, name
backend/app/services/weight_calculator.py-83-            review_history: Review history from Graphiti/learning memories
--
backend/app/services/weight_calculator.py-98-                weight_data = ConceptWeightData(
backend/app/services/weight_calculator.py-99-                    concept_id=concept_id,
backend/app/services/weight_calculator.py-100-                    concept_name=concept.get("name", ""),
backend/app/services/weight_calculator.py-101-                    weakness_score=score,
backend/app/services/weight_calculator.py-102-                    failure_count=0,
backend/app/services/weight_calculator.py:103:                    avg_rating=0.0,
backend/app/services/weight_calculator.py-104-                    review_count=0,
backend/app/services/weight_calculator.py-105-                    days_since_review=0,
backend/app/services/weight_calculator.py-106-                    category="borderline",
backend/app/services/weight_calculator.py-107-                )
backend/app/services/weight_calculator.py-108-            else:
--
backend/app/services/weight_calculator.py-145-        self, concept: Dict, history: List[Dict]
backend/app/services/weight_calculator.py-146-    ) -> ConceptWeightData:
backend/app/services/weight_calculator.py-147-        """
backend/app/services/weight_calculator.py-148-        Calculate weakness score from review history.
backend/app/services/weight_calculator.py-149-
backend/app/services/weight_calculator.py:150:        AC1: Score factors in rating, failure count, recency, and trend.
backend/app/services/weight_calculator.py-151-
backend/app/services/weight_calculator.py-152-        Args:
backend/app/services/weight_calculator.py-153-            concept: Concept dict with id, name
backend/app/services/weight_calculator.py-154-            history: List of review records for this concept
backend/app/services/weight_calculator.py-155-
backend/app/services/weight_calculator.py-156-        Returns:
backend/app/services/weight_calculator.py-157-            ConceptWeightData with calculated scores
backend/app/services/weight_calculator.py-158-        """
backend/app/services/weight_calculator.py-159-        # Calculate metrics
backend/app/services/weight_calculator.py:160:        ratings = [
backend/app/services/weight_calculator.py:161:            h.get("rating") or h.get("score", 0)
backend/app/services/weight_calculator.py-162-            for h in history
backend/app/services/weight_calculator.py:163:            if h.get("rating") or h.get("score")
backend/app/services/weight_calculator.py-164-        ]
backend/app/services/weight_calculator.py:165:        avg_rating = sum(ratings) / len(ratings) if ratings else 0
backend/app/services/weight_calculator.py-166-        failure_count = sum(
backend/app/services/weight_calculator.py:167:            1 for h in history if (h.get("rating") or h.get("score", 0)) <= 2
backend/app/services/weight_calculator.py-168-        )
backend/app/services/weight_calculator.py-169-        review_count = len(history)
backend/app/services/weight_calculator.py-170-
backend/app/services/weight_calculator.py-171-        # Days since last review
backend/app/services/weight_calculator.py-172-        last_review = max(
--
backend/app/services/weight_calculator.py-181-        if last_review:
backend/app/services/weight_calculator.py-182-            days_since = (datetime.utcnow() - last_review).days
backend/app/services/weight_calculator.py-183-
backend/app/services/weight_calculator.py-184-        # Calculate component scores (all normalized to 0-1, inverted where needed)
backend/app/services/weight_calculator.py-185-        # Rating 1-4 scale: 1 (worst) -> 1.0 weakness, 4 (best) -> 0.0 weakness
backend/app/services/weight_calculator.py:186:        rating_score = 1.0 - (avg_rating - 1) / 3.0 if avg_rating > 0 else 0.5
backend/app/services/weight_calculator.py:187:        rating_score = max(0.0, min(1.0, rating_score))
backend/app/services/weight_calculator.py-188-
backend/app/services/weight_calculator.py-189-        # Failure score: Cap at 5 failures
backend/app/services/weight_calculator.py-190-        failure_score = min(failure_count / 5.0, 1.0)
backend/app/services/weight_calculator.py-191-
backend/app/services/weight_calculator.py-192-        # Recency score: Cap at 30 days
backend/app/services/weight_calculator.py-193-        recency_score = min(days_since / 30.0, 1.0)
backend/app/services/weight_calculator.py-194-
backend/app/services/weight_calculator.py:195:        # Trend score (simplified: comparing recent vs older ratings)
backend/app/services/weight_calculator.py-196-        trend_score = self._calculate_trend_score(history)
backend/app/services/weight_calculator.py-197-
backend/app/services/weight_calculator.py-198-        # Weighted combination
backend/app/services/weight_calculator.py-199-        weakness_score = (
backend/app/services/weight_calculator.py:200:            self.RATING_WEIGHT * rating_score
backend/app/services/weight_calculator.py-201-            + self.FAILURE_WEIGHT * failure_score
backend/app/services/weight_calculator.py-202-            + self.RECENCY_WEIGHT * recency_score
backend/app/services/weight_calculator.py-203-            + self.TREND_WEIGHT * trend_score
backend/app/services/weight_calculator.py-204-        )
backend/app/services/weight_calculator.py-205-
--
backend/app/services/weight_calculator.py-217-        return ConceptWeightData(
backend/app/services/weight_calculator.py-218-            concept_id=concept.get("id", ""),
backend/app/services/weight_calculator.py-219-            concept_name=concept.get("name", ""),
backend/app/services/weight_calculator.py-220-            weakness_score=weakness_score,
backend/app/services/weight_calculator.py-221-            failure_count=failure_count,
backend/app/services/weight_calculator.py:222:            avg_rating=avg_rating,
backend/app/services/weight_calculator.py-223-            review_count=review_count,
backend/app/services/weight_calculator.py-224-            days_since_review=days_since,
backend/app/services/weight_calculator.py-225-            category=category,
backend/app/services/weight_calculator.py-226-        )
backend/app/services/weight_calculator.py-227-
backend/app/services/weight_calculator.py-228-    def _calculate_trend_score(self, history: List[Dict]) -> float:
backend/app/services/weight_calculator.py-229-        """
backend/app/services/weight_calculator.py:230:        Calculate trend score based on rating improvement.
backend/app/services/weight_calculator.py-231-
backend/app/services/weight_calculator.py-232-        AC1: Trend direction affects weakness score.
backend/app/services/weight_calculator.py-233-
backend/app/services/weight_calculator.py-234-        Args:
backend/app/services/weight_calculator.py-235-            history: List of review records
--
backend/app/services/weight_calculator.py-245-            history, key=lambda h: self._parse_timestamp(h.get("timestamp"))
backend/app/services/weight_calculator.py-246-        )
backend/app/services/weight_calculator.py-247-
backend/app/services/weight_calculator.py-248-        # Compare recent half vs older half
backend/app/services/weight_calculator.py-249-        mid = len(sorted_history) // 2
backend/app/services/weight_calculator.py:250:        older_ratings = [
backend/app/services/weight_calculator.py:251:            h.get("rating") or h.get("score", 0)
backend/app/services/weight_calculator.py-252-            for h in sorted_history[:mid]
backend/app/services/weight_calculator.py:253:            if h.get("rating") or h.get("score")
backend/app/services/weight_calculator.py-254-        ]
backend/app/services/weight_calculator.py:255:        recent_ratings = [
backend/app/services/weight_calculator.py:256:            h.get("rating") or h.get("score", 0)
backend/app/services/weight_calculator.py-257-            for h in sorted_history[mid:]
backend/app/services/weight_calculator.py:258:            if h.get("rating") or h.get("score")
backend/app/services/weight_calculator.py-259-        ]
backend/app/services/weight_calculator.py-260-
backend/app/services/weight_calculator.py:261:        if not older_ratings or not recent_ratings:
backend/app/services/weight_calculator.py-262-            return 0.5
backend/app/services/weight_calculator.py-263-
backend/app/services/weight_calculator.py:264:        older_avg = sum(older_ratings) / len(older_ratings)
backend/app/services/weight_calculator.py:265:        recent_avg = sum(recent_ratings) / len(recent_ratings)
backend/app/services/weight_calculator.py-266-
backend/app/services/weight_calculator.py-267-        # Improving = lower weakness score
backend/app/services/weight_calculator.py-268-        # Rating improved: recent > older -> negative trend score
backend/app/services/weight_calculator.py-269-        trend_diff = older_avg - recent_avg  # Positive if getting worse
backend/app/services/weight_calculator.py-270-
--
backend/app/models/review_models.py-365-    """
backend/app/models/review_models.py-366-
backend/app/models/review_models.py-367-    concept_id: str = Field(..., description="Concept identifier")
backend/app/models/review_models.py-368-    concept_name: str = Field(..., description="Concept name")
backend/app/models/review_models.py-369-    canvas_path: str = Field(..., description="Canvas file path")
backend/app/models/review_models.py:370:    rating: int = Field(..., ge=1, le=4, description="FSRS rating (1-4)")
backend/app/models/review_models.py-371-    review_time: datetime = Field(..., description="Review timestamp")
backend/app/models/review_models.py-372-
backend/app/models/review_models.py-373-
backend/app/models/review_models.py-374-class HistoryDayRecord(BaseModel):
backend/app/models/review_models.py-375-    """
--
backend/app/models/review_models.py-393-    Review history statistics.
backend/app/models/review_models.py-394-
backend/app/models/review_models.py-395-    [Source: specs/api/review-api.openapi.yml#L707-728]
backend/app/models/review_models.py-396-    """
backend/app/models/review_models.py-397-
backend/app/models/review_models.py:398:    average_rating: Optional[float] = Field(
backend/app/models/review_models.py:399:        None, description="Average FSRS rating", json_schema_extra={"example": 3.2}
backend/app/models/review_models.py-400-    )
backend/app/models/review_models.py-401-    retention_rate: Optional[float] = Field(
backend/app/models/review_models.py-402-        None,
backend/app/models/review_models.py-403-        ge=0.0,
backend/app/models/review_models.py-404-        le=1.0,
--
backend/app/core/unified_learning_event.py-365-
backend/app/core/unified_learning_event.py-366-
backend/app/core/unified_learning_event.py-367-# =============================================================================
backend/app/core/unified_learning_event.py-368-# Mapping: Old Entity Types -> Unified Model
backend/app/core/unified_learning_event.py-369-# =============================================================================
backend/app/core/unified_learning_event.py:370:# Backward compatibility layer for migrating existing records.
backend/app/core/unified_learning_event.py-371-
backend/app/core/unified_learning_event.py-372-ENTITY_TYPE_TO_UNIFIED: Dict[str, Dict[str, Any]] = {
backend/app/core/unified_learning_event.py-373-    "Misconception": {
backend/app/core/unified_learning_event.py-374-        "event_type": UnifiedEventType.MISCONCEPTION_DETECTED,
backend/app/core/unified_learning_event.py-375-        "knowledge_type": KnowledgeType.CONCEPTUAL,
--
backend/app/api/v1/endpoints/metadata.py-557-):
backend/app/api/v1/endpoints/metadata.py-558-    """
backend/app/api/v1/endpoints/metadata.py-559-    Scan all .md files in the vault and index them to LanceDB vault_notes table.
backend/app/api/v1/endpoints/metadata.py-560-
backend/app/api/v1/endpoints/metadata.py-561-    This enables RAG retrieval to reference vault markdown notes
backend/app/api/v1/endpoints/metadata.py:562:    when generating AI explanations.
backend/app/api/v1/endpoints/metadata.py-563-
backend/app/api/v1/endpoints/metadata.py-564-    Wave-5 Stage B (2026-05-12) — Multi-vault P0-2:
backend/app/api/v1/endpoints/metadata.py-565-    - vault_id 推荐必填, 注入 ContextVar 让 vault_notes 表 vault scoped.
backend/app/api/v1/endpoints/metadata.py-566-
backend/app/api/v1/endpoints/metadata.py-567-    Args:
--
backend/app/models/mastery_models.py-36-    LUCKY = "lucky"  # Low confidence + High performance
backend/app/models/mastery_models.py-37-    UNLEARNED = "unlearned"  # Low confidence + Low performance
backend/app/models/mastery_models.py-38-
backend/app/models/mastery_models.py-39-
backend/app/models/mastery_models.py-40-class CalibrationRating(str, Enum):
backend/app/models/mastery_models.py:41:    """Overall calibration quality rating.
backend/app/models/mastery_models.py-42-
backend/app/models/mastery_models.py-43-    Based on signed_bias with |threshold| = 0.15.
backend/app/models/mastery_models.py-44-    """
backend/app/models/mastery_models.py-45-
backend/app/models/mastery_models.py-46-    WELL_CALIBRATED = "well_calibrated"  # |signed_bias| < 0.15
--
backend/app/models/mastery_models.py-110-    )
backend/app/models/mastery_models.py-111-    absolute_bias: Optional[float] = Field(
backend/app/models/mastery_models.py-112-        default=None,
backend/app/models/mastery_models.py-113-        description="mean(|confidence - performance|), calibration precision",
backend/app/models/mastery_models.py-114-    )
backend/app/models/mastery_models.py:115:    calibration_rating: CalibrationRating = Field(
backend/app/models/mastery_models.py-116-        default=CalibrationRating.INSUFFICIENT_DATA,
backend/app/models/mastery_models.py-117-        description="Overall calibration quality",
backend/app/models/mastery_models.py-118-    )
backend/app/models/mastery_models.py-119-    stage_label: str = Field(
backend/app/models/mastery_models.py-120-        default="数据收集中",
--
backend/app/models/schemas.py-607-# ═══════════════════════════════════════════════════════════════════════════════
backend/app/models/schemas.py-608-
backend/app/models/schemas.py-609-
backend/app/models/schemas.py-610-class VerificationQuestionRequest(BaseModel):
backend/app/models/schemas.py-611-    """
backend/app/models/schemas.py:612:    Request model for generating verification questions.
backend/app/models/schemas.py-613-
backend/app/models/schemas.py-614-    [Source: docs/stories/story-12.A.6-complete-agents.md#AC1]
backend/app/models/schemas.py-615-    [Source: .claude/agents/verification-question-agent.md]
backend/app/models/schemas.py-616-    """
backend/app/models/schemas.py-617-
--
backend/app/models/schemas.py-751-    total_count: int = Field(..., description="Total item count")
backend/app/models/schemas.py-752-
backend/app/models/schemas.py-753-
backend/app/models/schemas.py-754-class GenerateReviewRequest(BaseModel):
backend/app/models/schemas.py-755-    """
backend/app/models/schemas.py:756:    Request model for generating verification canvas.
backend/app/models/schemas.py-757-
backend/app/models/schemas.py-758-    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/GenerateReviewRequest]
backend/app/models/schemas.py-759-    [Source: specs/data/review-generate-request.schema.json - Story 24.1]
backend/app/models/schemas.py-760-    """
backend/app/models/schemas.py-761-
--
backend/app/models/schemas.py-801-    concept_name: str = Field(..., description="Name of the weak concept")
backend/app/models/schemas.py-802-    weakness_score: float = Field(
backend/app/models/schemas.py-803-        ..., ge=0, le=1, description="Calculated weakness score"
backend/app/models/schemas.py-804-    )
backend/app/models/schemas.py-805-    failure_count: int = Field(..., ge=0, description="Historical failure count")
backend/app/models/schemas.py:806:    avg_rating: float = Field(..., ge=0, le=4, description="Average review rating")
backend/app/models/schemas.py-807-
backend/app/models/schemas.py-808-
backend/app/models/schemas.py-809-class WeightConfig(BaseModel):
backend/app/models/schemas.py-810-    """
backend/app/models/schemas.py-811-    Weight configuration for targeted review.
--
backend/app/models/schemas.py-860-
backend/app/models/schemas.py-861-class RecordReviewRequest(BaseModel):
backend/app/models/schemas.py-862-    """
backend/app/models/schemas.py-863-    Request model for recording review result.
backend/app/models/schemas.py-864-
backend/app/models/schemas.py:865:    Story 32.2 AC-32.2.2: Accepts FSRS ratings (1-4) in addition to legacy score.
backend/app/models/schemas.py:866:    Story 32.2 AC-32.2.4: Backward compatible - either rating OR score must be provided.
backend/app/models/schemas.py-867-
backend/app/models/schemas.py-868-    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/RecordReviewRequest]
backend/app/models/schemas.py-869-    [Source: specs/api/review-api.openapi.yml#L542-L563]
backend/app/models/schemas.py-870-    [Source: docs/stories/32.2.story.md]
backend/app/models/schemas.py-871-    """
backend/app/models/schemas.py-872-
backend/app/models/schemas.py-873-    canvas_name: str = Field(..., description="Canvas file name")
backend/app/models/schemas.py-874-    node_id: str = Field(..., description="Node ID (maps to concept_id)")
backend/app/models/schemas.py:875:    # Story 32.2: FSRS rating field (primary)
backend/app/models/schemas.py:876:    rating: Optional[int] = Field(
backend/app/models/schemas.py-877-        None,
backend/app/models/schemas.py-878-        ge=1,
backend/app/models/schemas.py-879-        le=4,
backend/app/models/schemas.py:880:        description="FSRS rating: 1=Again (forgot), 2=Hard, 3=Good, 4=Easy",
backend/app/models/schemas.py-881-    )
backend/app/models/schemas.py-882-    # Story 32.2 AC-32.2.4: Legacy score field (backward compatibility)
backend/app/models/schemas.py-883-    score: Optional[float] = Field(
backend/app/models/schemas.py-884-        None,
backend/app/models/schemas.py-885-        ge=0,
backend/app/models/schemas.py-886-        le=100,
backend/app/models/schemas.py:887:        description="Legacy score (0-100). Auto-converted to rating: <40=Again, 40-59=Hard, 60-84=Good, >=85=Easy",
backend/app/models/schemas.py-888-    )
backend/app/models/schemas.py-889-    # Optional card state for persistence
backend/app/models/schemas.py-890-    card_state: Optional[str] = Field(
backend/app/models/schemas.py-891-        None,
backend/app/models/schemas.py-892-        description="Serialized FSRS card JSON from previous review (for card state continuity)",
--
backend/app/models/schemas.py-924-    difficulty: float = Field(..., ge=1, le=10, description="Card difficulty (1-10)")
backend/app/models/schemas.py-925-    state: int = Field(
backend/app/models/schemas.py-926-        ..., description="Card state: 0=New, 1=Learning, 2=Review, 3=Relearning"
backend/app/models/schemas.py-927-    )
backend/app/models/schemas.py-928-    reps: int = Field(0, description="Successful review count")
backend/app/models/schemas.py:929:    lapses: int = Field(0, description="Failed review count (rating=1)")
backend/app/models/schemas.py-930-    # Story 32.3: Additional fields for plugin priority calculation
backend/app/models/schemas.py-931-    retrievability: Optional[float] = Field(
backend/app/models/schemas.py-932-        None, ge=0, le=1, description="Current retrievability probability (0-1)"
backend/app/models/schemas.py-933-    )
backend/app/models/schemas.py-934-    due: Optional[datetime] = Field(None, description="Next due date/time for review")
--
backend/app/api/v1/endpoints/exam.py-286-    summary="Skip current question -- no BKT/FSRS penalty (Story 6.6)",
backend/app/api/v1/endpoints/exam.py-287-)
backend/app/api/v1/endpoints/exam.py-288-async def skip_exam_question(exam_id: str, request: SkipRequest) -> SkipResponse:
backend/app/api/v1/endpoints/exam.py-289-    """Skip the current question without mastery penalty.
backend/app/api/v1/endpoints/exam.py-290-
backend/app/api/v1/endpoints/exam.py:291:    BKT p_mastery unchanged. FSRS: no rating event.
backend/app/api/v1/endpoints/exam.py-292-    [Source: Story 6.6 AC-4]
backend/app/api/v1/endpoints/exam.py-293-    """
backend/app/api/v1/endpoints/exam.py-294-    svc = get_exam_service()
backend/app/api/v1/endpoints/exam.py-295-    return await svc.skip_question(request)
backend/app/api/v1/endpoints/exam.py-296-
--
backend/app/api/v1/endpoints/review.py-101-
backend/app/api/v1/endpoints/review.py-102-
backend/app/api/v1/endpoints/review.py-103-# FSRS-V2-2026-07-30 收口清算 Tier A: EbbinghausReviewScheduler 幽灵导入
backend/app/api/v1/endpoints/review.py-104-# 已退役 (实体只存在于 _archive, ImportError 恒触发, /review/schedule 因此
backend/app/api/v1/endpoints/review.py-105-# 永远返回空 — 2026-07-29 审查报告暗雷 #1)。复习调度真相源现为 vault
backend/app/api/v1/endpoints/review.py:106:# frontmatter fsrs_due (写侧 quiz-answer × fsrs_bridge, 读侧 daily_review_pick)。
backend/app/api/v1/endpoints/review.py-107-
backend/app/api/v1/endpoints/review.py-108-
backend/app/api/v1/endpoints/review.py-109-# Story 38.9 AC3: ReviewService singleton now lives in services layer.
backend/app/api/v1/endpoints/review.py-110-# Import the canonical factory instead of maintaining a duplicate here.
backend/app/api/v1/endpoints/review.py-111-# Story 34.10 AC3: This direct import (not Depends()) is intentional.
--
backend/app/api/v1/endpoints/review.py-686-        )
backend/app/api/v1/endpoints/review.py-687-
backend/app/api/v1/endpoints/review.py-688-        # Build response
backend/app/api/v1/endpoints/review.py-689-        records = []
backend/app/api/v1/endpoints/review.py-690-        total_reviews = 0
backend/app/api/v1/endpoints/review.py:691:        all_ratings = []
backend/app/api/v1/endpoints/review.py-692-        canvas_counts: Dict[str, int] = {}
backend/app/api/v1/endpoints/review.py-693-
backend/app/api/v1/endpoints/review.py-694-        for day_data in result.get("records", []):
backend/app/api/v1/endpoints/review.py-695-            day_reviews = []
backend/app/api/v1/endpoints/review.py-696-            for review in day_data.get("reviews", []):
backend/app/api/v1/endpoints/review.py-697-                day_reviews.append(
backend/app/api/v1/endpoints/review.py-698-                    HistoryReviewRecord(
backend/app/api/v1/endpoints/review.py-699-                        concept_id=review.get("concept_id", ""),
backend/app/api/v1/endpoints/review.py-700-                        concept_name=review.get("concept_name", ""),
backend/app/api/v1/endpoints/review.py-701-                        canvas_path=review.get("canvas_path", ""),
backend/app/api/v1/endpoints/review.py:702:                        rating=review.get("rating", 3),
backend/app/api/v1/endpoints/review.py-703-                        review_time=review.get("review_time", dt.now()),
backend/app/api/v1/endpoints/review.py-704-                    )
backend/app/api/v1/endpoints/review.py-705-                )
backend/app/api/v1/endpoints/review.py:706:                all_ratings.append(review.get("rating", 3))
backend/app/api/v1/endpoints/review.py-707-                canvas = review.get("canvas_path", "")
backend/app/api/v1/endpoints/review.py-708-                canvas_counts[canvas] = canvas_counts.get(canvas, 0) + 1
backend/app/api/v1/endpoints/review.py-709-
backend/app/api/v1/endpoints/review.py-710-            records.append(HistoryDayRecord(date=day_data.get("date", ""), reviews=day_reviews))
backend/app/api/v1/endpoints/review.py-711-            total_reviews += len(day_reviews)
backend/app/api/v1/endpoints/review.py-712-
backend/app/api/v1/endpoints/review.py-713-        # Calculate statistics
backend/app/api/v1/endpoints/review.py:714:        avg_rating = sum(all_ratings) / len(all_ratings) if all_ratings else None
backend/app/api/v1/endpoints/review.py-715-        statistics = HistoryStatistics(
backend/app/api/v1/endpoints/review.py:716:            average_rating=round(avg_rating, 2) if avg_rating else None,
backend/app/api/v1/endpoints/review.py-717-            retention_rate=result.get("retention_rate"),
backend/app/api/v1/endpoints/review.py-718-            streak_days=result.get("streak_days", 0),
backend/app/api/v1/endpoints/review.py-719-            by_canvas=canvas_counts if canvas_counts else None,
backend/app/api/v1/endpoints/review.py-720-        )
backend/app/api/v1/endpoints/review.py-721-
--
backend/app/api/v1/endpoints/review.py-1037-
backend/app/api/v1/endpoints/review.py-1038-    Story 32.2: FSRS Integration for optimal spaced repetition intervals.
backend/app/api/v1/endpoints/review.py-1039-
backend/app/api/v1/endpoints/review.py-1040-    - **canvas_name**: Canvas file name
backend/app/api/v1/endpoints/review.py-1041-    - **node_id**: Node ID (maps to concept_id)
backend/app/api/v1/endpoints/review.py:1042:    - **rating**: FSRS rating (1=Again, 2=Hard, 3=Good, 4=Easy) - preferred
backend/app/api/v1/endpoints/review.py:1043:    - **score**: Legacy score (0-100) - auto-converted to rating
backend/app/api/v1/endpoints/review.py-1044-    - **card_state**: Optional serialized FSRS card JSON for persistence
backend/app/api/v1/endpoints/review.py-1045-    - **review_duration**: Optional review time in seconds
backend/app/api/v1/endpoints/review.py-1046-
backend/app/api/v1/endpoints/review.py-1047-    Wave-5 Stage B (2026-05-12) — Multi-vault P0-2:
backend/app/api/v1/endpoints/review.py-1048-    - request.vault_id 推荐必填, 注入 ContextVar 防 FSRS 状态串库.
backend/app/api/v1/endpoints/review.py-1049-
backend/app/api/v1/endpoints/review.py-1050-    Rating Conversion (Story 32.2 AC-32.2.4):
backend/app/api/v1/endpoints/review.py:1051:    - score < 40 → rating 1 (Again/Forgot)
backend/app/api/v1/endpoints/review.py:1052:    - score 40-59 → rating 2 (Hard)
backend/app/api/v1/endpoints/review.py:1053:    - score 60-84 → rating 3 (Good)
backend/app/api/v1/endpoints/review.py:1054:    - score >= 85 → rating 4 (Easy)
backend/app/api/v1/endpoints/review.py-1055-
backend/app/api/v1/endpoints/review.py-1056-    [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1review~1record]
backend/app/api/v1/endpoints/review.py-1057-    [Source: docs/stories/32.2.story.md - FSRS Integration]
backend/app/api/v1/endpoints/review.py-1058-    """
backend/app/api/v1/endpoints/review.py-1059-    from datetime import date
--
backend/app/api/v1/endpoints/review.py-1064-        subject_id=request.subject_id,
backend/app/api/v1/endpoints/review.py-1065-        canvas_path=request.canvas_name,
backend/app/api/v1/endpoints/review.py-1066-    )
backend/app/api/v1/endpoints/review.py-1067-
backend/app/api/v1/endpoints/review.py-1068-    logger.info(
backend/app/api/v1/endpoints/review.py:1069:        "PUT /review/record canvas=%s node=%s rating=%s score=%s",
backend/app/api/v1/endpoints/review.py-1070-        request.canvas_name,
backend/app/api/v1/endpoints/review.py-1071-        request.node_id,
backend/app/api/v1/endpoints/review.py:1072:        request.rating,
backend/app/api/v1/endpoints/review.py-1073-        request.score,
backend/app/api/v1/endpoints/review.py-1074-    )
backend/app/api/v1/endpoints/review.py-1075-    # Story 38.9 AC3: Use canonical singleton from services layer
backend/app/api/v1/endpoints/review.py-1076-    review_service = await _get_review_service_singleton()
backend/app/api/v1/endpoints/review.py-1077-
--
backend/app/api/v1/endpoints/review.py-1083-        if request.review_duration is not None:
backend/app/api/v1/endpoints/review.py-1084-            details["review_duration"] = request.review_duration
backend/app/api/v1/endpoints/review.py-1085-        result = await review_service.record_review_result(
backend/app/api/v1/endpoints/review.py-1086-            canvas_name=request.canvas_name,
backend/app/api/v1/endpoints/review.py-1087-            concept_id=request.node_id,
backend/app/api/v1/endpoints/review.py:1088:            rating=request.rating,
backend/app/api/v1/endpoints/review.py-1089-            score=request.score,
backend/app/api/v1/endpoints/review.py-1090-            card_state=request.card_state,
backend/app/api/v1/endpoints/review.py-1091-            details=details if details else None,
backend/app/api/v1/endpoints/review.py-1092-        )
backend/app/api/v1/endpoints/review.py-1093-
--
backend/app/api/v1/endpoints/review.py-1123-        )
backend/app/api/v1/endpoints/review.py-1124-
backend/app/api/v1/endpoints/review.py-1125-    except Exception as e:
backend/app/api/v1/endpoints/review.py-1126-        logger.error(f"Error recording review with FSRS: {e}")
backend/app/api/v1/endpoints/review.py-1127-        # Fallback to legacy Ebbinghaus calculation
backend/app/api/v1/endpoints/review.py:1128:        score = request.score or 50.0  # Default score if only rating provided
backend/app/api/v1/endpoints/review.py:1129:        if request.rating:
backend/app/api/v1/endpoints/review.py:1130:            # Convert rating back to approximate score for fallback
backend/app/api/v1/endpoints/review.py:1131:            score = {1: 20.0, 2: 50.0, 3: 75.0, 4: 95.0}.get(request.rating, 50.0)
backend/app/api/v1/endpoints/review.py-1132-
backend/app/api/v1/endpoints/review.py-1133-        if score >= 85:
backend/app/api/v1/endpoints/review.py-1134-            interval = 30
backend/app/api/v1/endpoints/review.py-1135-        elif score >= 60:
backend/app/api/v1/endpoints/review.py-1136-            interval = 7
--
backend/app/api/v1/endpoints/chat.py-871-
backend/app/api/v1/endpoints/chat.py-872-    # R2 修复 (2026-07-12 对抗审查): 出题/评分轮绝不注入 —— hook 曾把被考
backend/app/api/v1/endpoints/chat.py-873-    # 节点的定义正文 snippet + "必须 Read 完整文件"指令灌进 /start-exam-board
backend/app/api/v1/endpoints/chat.py-874-    # 出题对话, 与 HARD-ISO-4 信息隔离铁律 (d=1.50 命脉) 正面互斥。
backend/app/api/v1/endpoints/chat.py-875-    # 这些 skill 的素材获取有自己的安全通道 (Grep 安全抽取器 / targeting-material)。
backend/app/api/v1/endpoints/chat.py:876:    _EXAM_SKILL_PREFIXES = ("/start-exam-board", "/quiz-answer", "/exam-quick")
backend/app/api/v1/endpoints/chat.py-877-    if user_prompt.startswith(_EXAM_SKILL_PREFIXES):
backend/app/api/v1/endpoints/chat.py-878-        logger.info(
backend/app/api/v1/endpoints/chat.py-879-            "[T1.7-AutoRAG] exam-skill prompt detected, injection skipped (HARD-ISO isolation)",
backend/app/api/v1/endpoints/chat.py-880-            prompt=user_prompt[:60],
backend/app/api/v1/endpoints/chat.py-881-        )
--
backend/app/api/v1/endpoints/profile.py-64-        description="Supportive guidance message, not raw numbers"
backend/app/api/v1/endpoints/profile.py-65-    )
backend/app/api/v1/endpoints/profile.py-66-    interaction_count: int = 0
backend/app/api/v1/endpoints/profile.py-67-    exam_count: int = 0
backend/app/api/v1/endpoints/profile.py-68-    last_exam_date: Optional[str] = None
backend/app/api/v1/endpoints/profile.py:69:    fsrs_due_date: Optional[str] = None
backend/app/api/v1/endpoints/profile.py-70-    freshness: str = "fresh"
backend/app/api/v1/endpoints/profile.py-71-
backend/app/api/v1/endpoints/profile.py-72-
backend/app/api/v1/endpoints/profile.py-73-class TipItem(BaseModel):
backend/app/api/v1/endpoints/profile.py-74-    """A single tip annotation."""
--
backend/app/api/v1/endpoints/profile.py-167-            effective_proficiency=0.0,
backend/app/api/v1/endpoints/profile.py-168-            prescriptive_message=_PRESCRIPTIVE_MESSAGES[0],
backend/app/api/v1/endpoints/profile.py-169-            interaction_count=0,
backend/app/api/v1/endpoints/profile.py-170-            exam_count=0,
backend/app/api/v1/endpoints/profile.py-171-            last_exam_date=None,
backend/app/api/v1/endpoints/profile.py:172:            fsrs_due_date=None,
backend/app/api/v1/endpoints/profile.py-173-            freshness="fresh",
backend/app/api/v1/endpoints/profile.py-174-        )
backend/app/api/v1/endpoints/profile.py-175-
backend/app/api/v1/endpoints/profile.py-176-    resp = engine.concept_to_response(concept)
backend/app/api/v1/endpoints/profile.py-177-    level = resp["mastery_level"]
--
backend/app/api/v1/endpoints/profile.py-191-        interaction_count=concept.interaction_count,
backend/app/api/v1/endpoints/profile.py-192-        exam_count=exam_count,
backend/app/api/v1/endpoints/profile.py-193-        last_exam_date=concept.last_interaction_ts.isoformat()
backend/app/api/v1/endpoints/profile.py-194-        if concept.last_interaction_ts
backend/app/api/v1/endpoints/profile.py-195-        else None,
backend/app/api/v1/endpoints/profile.py:196:        fsrs_due_date=resp.get("fsrs_due_date"),
backend/app/api/v1/endpoints/profile.py-197-        freshness=freshness,
backend/app/api/v1/endpoints/profile.py-198-    )
backend/app/api/v1/endpoints/profile.py-199-
backend/app/api/v1/endpoints/profile.py-200-
backend/app/api/v1/endpoints/profile.py-201-@profile_router.get("/profile/{node_id}/tips")

**Planning detailed daily_review_pick inspection**
exec
/bin/zsh -lc "nl -ba scripts/daily_review_pick.py | sed -n '241,520p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
   241	
   242	
   243	def build_payload(vault: Path, now: datetime, board_last_recommended: dict, decay):
   244	    nodes, stats, ineligible = scan_nodes(vault, now, decay)
   245	    ranked, upcoming, unassigned = rank_boards(nodes, board_last_recommended)
   246	    stats["unassigned"] = len(unassigned)
   247	    # v3 (CARD-A2): due_nodes 明细与 stats 数字同源派生 — 自洽靠构造保证,
   248	    # 本投影是全系统到期口径唯一裁判 (Dashboard 只消费不重算)
   249	    due_rows = [
   250	        {
   251	            "node": n["node"],
   252	            "board": n["board"],
   253	            "state": n["state"],
   254	            "pick": round(n["pick"], 4),
   255	            "fsrs_due": n["fsrs_due"],           # 空串 = 新卡即刻到期
   256	            # Codex-A2 M1: 消费方须能区分真新卡与 fail-open 的脏日期卡
   257	            "due_reason": ("malformed" if n["due_fail_open"]
   258	                           else ("scheduled" if n["fsrs_due"] else "new")),
   259	            "last_examined": n["last_examined"],
   260	            "difficulty": n["difficulty"],
   261	        }
   262	        for n in nodes if n["board"] and n["due_now"]
   263	    ]
   264	    stats["due_nodes"] = len(due_rows)
   265	    stats["future_nodes"] = sum(1 for n in nodes if n["board"] and not n["due_now"])
   266	    payload = {
   267	        "unassigned_nodes": unassigned,  # Code-Review M3: 点名而非只给数字
   268	        "schema_version": 3,             # v3: +due_nodes 明细 +ineligible 分桶
   269	        #                                  (纯加性; v2: FSRS WHEN 化 upcoming/due 语义)
   270	        "date": now.astimezone().date().isoformat(),
   271	        "generated_at": now.astimezone().isoformat(timespec="seconds"),
   272	        "top_boards": ranked[:3],
   273	        "upcoming": upcoming[:3],
   274	        "due_nodes": due_rows,
   275	        "ineligible": ineligible,
   276	        "stats": stats,
   277	        "notification": None,
   278	    }
   279	    day_id = f"canvas-review-{payload['date']}"
   280	    if ranked:
   281	        payload["notification"] = {
   282	            "title": _title(ranked[0]["board"]),
   283	            "body": _body(ranked[0]),
   284	            "group": "canvas复习",
   285	            "id": day_id,
   286	        }
   287	    elif upcoming:
   288	        # F1 放假语义: 有调度中的板但今天零到期 → 诚实说不用复习
   289	        nxt = upcoming[0]
   290	        payload["notification"] = {
   291	            "title": "📚 今日无到期节点",
   292	            "body": f"按计划推进，休息一天 · 最近到期 {nxt['board']} · {nxt['next_due'][:10]}",
   293	            "group": "canvas复习",
   294	            "id": day_id,
   295	        }
   296	    return payload, ranked
   297	
   298	
   299	def render_md(payload, ranked) -> str:
   300	    s = payload["stats"]
   301	    lines = [
   302	        f"# 今日复习 · {payload['date']}",
   303	        "",
   304	        f"> 生成 {payload['generated_at']} · 到期={s['due_nodes']} / 未到期={s['future_nodes']}（不含未归板）"
   305	        f" · 节点状态: new={s['new']} / legacy={s['legacy']}"
   306	        f" / 无字段={s['none']} / 未剖析跳过={s['ineligible']} / 测试排除={s['test_excluded']}"
   307	        f" / 未归板={s['unassigned']} / 损坏={s['corrupt']}",
   308	        "",
   309	        "| 板 | 优先分 | 到期待复习 | 最该考 | 难度 | 闲置 | 板内下次到期 |",
   310	        "|---|---|---|---|---|---|---|",
   311	    ]
   312	    for r in ranked:
   313	        idle = "从未考" if r["idle_days"] is None else f"{r['idle_days']} 天"
   314	        nxt = r["next_due"][:10] if r["next_due"] else "-"
   315	        diff = r["difficulty"] or "-"
   316	        lines.append(
   317	            f"| {r['board']} | {r['priority']} | {r['pending']} | {r['top_node']} | {diff} | {idle} | {nxt} |"
   318	        )
   319	    if payload.get("upcoming"):
   320	        for u in payload["upcoming"]:
   321	            lines.append(f"| {u['board']} | - | 0（未到期） | - | - | - | {u['next_due'][:10]} |")
   322	    if ranked:
   323	        lines += ["", "## 一键开考（整行复制到 Claudian）", ""]
   324	        for r in ranked:
   325	            lines.append(f"- `/start-exam-board from {r['board']} node {r['top_node']}`")
   326	    else:
   327	        lines += ["", "> ✅ 今日无到期节点，休息一天。"]
   328	    if payload.get("unassigned_nodes"):
   329	        lines += ["", "> ⚠ 未归板节点（无 source_board，不参与推荐）: "
   330	                  + "、".join(payload["unassigned_nodes"])]
   331	    lines += [
   332	        "",
   333	        "> WHEN=FSRS 到期（无 fsrs_due 字段 = 新卡即刻到期）；WHAT=到期集合内按 μ−σ 排序",
   334	        "> （含闲置回升，证据质量半衰期 69 天）。未剖析占位节点已跳过；命令已绑定最该考节点。",
   335	    ]
   336	    return "\n".join(lines) + "\n"
   337	
   338	
   339	def atomic_write(path: Path, content: str):
   340	    tmp = path.with_suffix(path.suffix + ".tmp")
   341	    tmp.write_text(content, encoding="utf-8")
   342	    os.replace(tmp, path)
   343	
   344	
   345	def load_decay(vault: Path):
   346	    sys.path.insert(0, str(vault / ".claude" / "scripts"))
   347	    import decay_beta
   348	    return decay_beta
   349	
   350	
   351	def main():
   352	    ap = argparse.ArgumentParser(description="每日复习选板")
   353	    ap.add_argument("--vault", required=True)
   354	    ap.add_argument("--state", help="daily-review.state.json (只读, 取 board_last_recommended)")
   355	    ap.add_argument("--now", help="ISO 时间覆盖 (测试用)")
   356	    ap.add_argument("--write", action="store_true", help="写 outputs/今日复习.md+json")
   357	    args = ap.parse_args()
   358	
   359	    vault = Path(args.vault)
   360	    # 裸时间当本地时区, 与 daily_review_run.py 语义统一 (Code-Review L6)
   361	    if args.now:
   362	        dt = datetime.fromisoformat(args.now.replace("Z", "+00:00"))
   363	        now = dt if dt.tzinfo else dt.astimezone()
   364	    else:
   365	        now = datetime.now(timezone.utc)
   366	    blr = {}
   367	    if args.state and Path(args.state).exists():
   368	        try:
   369	            blr = json.loads(Path(args.state).read_text(encoding="utf-8")).get(
   370	                "board_last_recommended", {})
   371	        except (json.JSONDecodeError, OSError):
   372	            pass  # state 损坏由 runner 处置, 选点侧降级为无记录
   373	
   374	    payload, ranked = build_payload(vault, now, blr, load_decay(vault))
   375	    if args.write:
   376	        out = vault / "outputs"
   377	        out.mkdir(parents=True, exist_ok=True)
   378	        atomic_write(out / "今日复习.md", render_md(payload, ranked))
   379	        atomic_write(out / "今日复习.json",
   380	                     json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
   381	    print(json.dumps(payload, ensure_ascii=False))
   382	
   383	
   384	if __name__ == "__main__":
   385	    main()

exec
/bin/zsh -lc "nl -ba scripts/daily_review_pick.py | sed -n '1,240p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
     1	#!/usr/bin/env python3
     2	"""每日复习选板 (DAILY-REVIEW-PUSH-2026-07-29, ChatGPT 终审 A3 修正版)。
     3	
     4	扫 vault 节点/*.md frontmatter → 衰减 Beta 读时时效 pick → 板级 min 聚合
     5	→ outputs/今日复习.md (人读) + outputs/今日复习.json (推送 payload, 终审 A7:
     6	stdout 是瞬时数据, 推送失败补跑必须有持久化 payload)。
     7	
     8	schema v3 (CARD-A2, BATCH-2026-08-24-复习闭环): 本 JSON 是全系统到期口径
     9	唯一裁判 — Dashboard.md 直接 dv.io.load 消费 due_nodes 明细 + ineligible
    10	分桶 (占位符待剖析积压单独成桶), 不再独立重算。v2→v3 纯加性, 推送链
    11	(daily_review_run/send_bark 只读 notification) 被动兼容。
    12	
    13	三态兼容 (live 实测 18 节点: 新字段 1 / 仅旧 10 / 无字段 7):
    14	  mastery_a/b (+last_examined) → effective() 闲置折扣后 pick
    15	  仅 mastery_score             → from_legacy() 均值继承低置信
    16	  无字段                       → 先验 Beta(0.9,2.1), 从未考 σ 大自动优先
    17	
    18	终审 A3 三修正:
    19	  1. eligibility 与 start-exam-board 同规则 — 含「你的 1-2 句精准定义」
    20	     占位符的未剖析节点跳过 (否则推荐无法出题的节点到手机)
    21	  2. 输出命令绑定 node <top_node> — start-exam-board 自己重选点时不含
    22	     闲置折扣, 不绑定会出现「通知说考 A 实际考 B」
    23	  3. min() 并列 tie-break: 板上次被推荐日期(久者先) → 最老 last_examined
    24	     → 板名 (防启动期先验板按扫描顺序永久霸榜)
    25	
    26	依赖: 仅 stdlib + vault 内 decay_beta.py (launchd 环境无 pip 包可假设)。
    27	"""
    28	
    29	from __future__ import annotations
    30	
    31	import argparse
    32	import json
    33	import math
    34	import os
    35	import re
    36	import sys
    37	from datetime import datetime, timezone
    38	from pathlib import Path
    39	
    40	#: 与 start-exam-board SKILL Step 3 完全同一条占位符规则 (终审 A3)
    41	PLACEHOLDER = "你的 1-2 句精准定义"
    42	
    43	#: 生产数据污染标记 (对齐 memory-health.sh 批次1'⑥ 审计清单) — 不推测试节点。
    44	#: ⚠ 只匹配文件名: 真实节点 frontmatter 可能引用测试会话 id (live 实测
    45	#: Fundamentals 的 error_candidates 含 m3-e2e-sessionend-test, 按全文匹配会误杀)
    46	TEST_MARKERS = ("TestConcept", "UAT-2.5", "m3-e2e")
    47	
    48	#: [Decision-FSRS-2] WHEN/WHAT 分工 (FSRS-V2-2026-07-30):
    49	#: FSRS 管 WHEN — fsrs_due 决定今天谁到期, 无字段 = New 卡即刻到期;
    50	#: 衰减 Beta 管 WHAT — 到期集合内按 pick=μ−σ 排序。
    51	#: 本文件保持纯 stdlib: 只做 UTC 定长字符串日期比较, 不 import fsrs。
    52	
    53	#: Bark 通知标题上限 (方案规范: ≤20 全角字符)
    54	TITLE_LIMIT = 20
    55	
    56	
    57	def _aware(s: str) -> datetime:
    58	    dt = datetime.fromisoformat(str(s).strip().replace("Z", "+00:00"))
    59	    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    60	
    61	
    62	def _fm_num(fm: str, key: str):
    63	    # 容负号 (Code-Review L5): mastery_a: -3 应进 corrupt 分支而非静默当无字段
    64	    m = re.search(rf'^{key}:\s*"?(-?[0-9]*\.?[0-9]+)"?\s*$', fm, re.M)
    65	    return float(m.group(1)) if m else None
    66	
    67	
    68	def _fm_str(fm: str, key: str):
    69	    m = re.search(rf'^{key}:\s*"?([^"\n]+?)"?\s*$', fm, re.M)
    70	    return m.group(1).strip() if m else None
    71	
    72	
    73	def _board_name(raw: str | None):
    74	    """source_board 归一化 → 板名 (live 数据实为 wikilink '[[原白板/X]]')。"""
    75	    if not raw:
    76	        return None
    77	    name = raw.strip()
    78	    if name.startswith("[[") and name.endswith("]]"):
    79	        name = name[2:-2]
    80	    name = name.split("|")[0]                 # [[path|alias]] 取 path
    81	    name = name.rsplit("/", 1)[-1].strip()    # 原白板/X → X
    82	    return name or None
    83	
    84	
    85	def scan_nodes(vault: Path, now: datetime, decay):
    86	    """扫描 节点/ 池 → (nodes, stats, ineligible)。逐节点容错: 单个脏节点不崩全轮。
    87	
    88	    ineligible 分桶 (schema v3, CARD-A2): 被跳过的节点按原因点名, 不再只有
    89	    计数 — Dashboard 消费 placeholder 桶显示"待剖析积压"。
    90	    """
    91	    stats = {"new": 0, "legacy": 0, "none": 0, "ineligible": 0, "test_excluded": 0, "corrupt": 0}
    92	    ineligible = {"placeholder": [], "test_excluded": [], "corrupt": []}
    93	    now_z = now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    94	    nodes = []
    95	    for path in sorted((vault / "节点").glob("*.md")):
    96	        stem = path.stem
    97	        try:
    98	            text = path.read_text(encoding="utf-8")
    99	        except OSError as e:
   100	            stats["corrupt"] += 1
   101	            ineligible["corrupt"].append(stem)
   102	            print(f"[pick] 读取失败跳过 {stem}: {e}", file=sys.stderr)
   103	            continue
   104	        if any(mk in stem for mk in TEST_MARKERS):
   105	            stats["test_excluded"] += 1
   106	            ineligible["test_excluded"].append(stem)
   107	            continue
   108	        m = re.match(r"^﻿?---\r?\n(.*?)\r?\n---\r?\n?(.*)$", text, re.S)
   109	        fm, body = (m.group(1), m.group(2)) if m else ("", text)
   110	        if PLACEHOLDER in body:
   111	            stats["ineligible"] += 1
   112	            ineligible["placeholder"].append(stem)
   113	            continue
   114	
   115	        a_raw, b_raw = _fm_num(fm, "mastery_a"), _fm_num(fm, "mastery_b")
   116	        legacy = next(
   117	            (v for k in ("mastery_score", "mastery", "mastery_level")
   118	             if (v := _fm_num(fm, k)) is not None),
   119	            None,
   120	        )
   121	        if a_raw is not None and b_raw is not None:
   122	            a, b, state = a_raw, b_raw, "new"
   123	        elif legacy is not None:
   124	            a, b = decay.from_legacy(legacy)
   125	            state = "legacy"
   126	        else:
   127	            a, b, state = decay.PRIOR_A, decay.PRIOR_B, "none"
   128	        stats[state] += 1
   129	
   130	        last_exam = _fm_str(fm, "last_examined")
   131	        idle_days = None
   132	        if last_exam:
   133	            try:
   134	                idle_days = max(0.0, (now - _aware(last_exam)).total_seconds() / 86400.0)
   135	            except ValueError:
   136	                print(f"[pick] last_examined 无法解析, 按从未考: {stem}", file=sys.stderr)
   137	                last_exam = None
   138	        try:
   139	            # pick_score 也在 try 内 (Code-Review M2): 除零/溢出同属脏数据
   140	            a_eff, b_eff = decay.effective(a, b, idle_days or 0.0)
   141	            pick = decay.pick_score(a_eff, b_eff)
   142	        except (ValueError, ZeroDivisionError, OverflowError) as e:
   143	            stats["corrupt"] += 1
   144	            ineligible["corrupt"].append(stem)
   145	            print(f"[pick] Beta 参数损坏跳过 {stem}: {e}", file=sys.stderr)
   146	            continue
   147	        if not math.isfinite(pick):
   148	            # Codex-A2 H1: 巨值 mastery 让 pick 静默算成 NaN/inf 不抛异常 —
   149	            # v3 起每个到期节点的 pick 都进 JSON, 单个 NaN = 全文件非法。
   150	            # 与其余脏数据同语义: 进 corrupt 桶, 不崩全轮。
   151	            stats["corrupt"] += 1
   152	            ineligible["corrupt"].append(stem)
   153	            print(f"[pick] Beta 参数溢出跳过 {stem}: pick={pick}", file=sys.stderr)
   154	            continue
   155	
   156	        fsrs_due = _fm_str(fm, "fsrs_due") or ""
   157	        due_fail_open = False
   158	        # Code-Review M2: Obsidian Properties 面板可能把 datetime 重新序列化成
   159	        # 带偏移格式, 词法比较会反向误判「永不到期」。非规范格式 fail-open
   160	        # 视同到期 (与 New 语义一致), 不静默消失。
   161	        # Codex-A2 M2: 形状正确但日历非法 (如月份 13) 词法比较会误判成未来,
   162	        # 同样 fail-open — 脏值策略统一为一条。
   163	        if fsrs_due:
   164	            due_ok = bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", fsrs_due))
   165	            if due_ok:
   166	                try:
   167	                    datetime.strptime(fsrs_due, "%Y-%m-%dT%H:%M:%SZ")
   168	                except ValueError:
   169	                    due_ok = False
   170	            if not due_ok:
   171	                print(f"[pick] fsrs_due 非规范格式, 视同到期: {stem} ({fsrs_due})", file=sys.stderr)
   172	                fsrs_due = ""
   173	                due_fail_open = True
   174	        nodes.append({
   175	            "node": stem,
   176	            "board": _board_name(_fm_str(fm, "source_board")),
   177	            "state": state,
   178	            "pick": pick,
   179	            "idle_days": idle_days,          # None = 从未考
   180	            "last_examined": last_exam or "",
   181	            "fsrs_due": fsrs_due,
   182	            "due_now": (not fsrs_due) or fsrs_due <= now_z,  # 无字段 = New 即刻到期
   183	            "due_fail_open": due_fail_open,
   184	            "difficulty": _fm_str(fm, "fsrs_difficulty") or "",
   185	        })
   186	    return nodes, stats, ineligible
   187	
   188	
   189	def rank_boards(nodes, board_last_recommended: dict):
   190	    """板级聚合: priority = min(pick), 终审 A3 tie-break。"""
   191	    boards: dict[str, list] = {}
   192	    unassigned = []
   193	    for n in nodes:
   194	        if not n["board"]:
   195	            unassigned.append(n["node"])
   196	            continue
   197	        boards.setdefault(n["board"], []).append(n)
   198	
   199	    ranked, upcoming = [], []
   200	    for board, members in boards.items():
   201	        due = [n for n in members if n["due_now"]]
   202	        if not due:
   203	            # WHEN: 全员未到期 → 不进推荐榜, 记最近的未来到期 (F1 放假语义)
   204	            nxt = min(members, key=lambda n: n["fsrs_due"])
   205	            upcoming.append({"board": board, "next_due": nxt["fsrs_due"], "node": nxt["node"]})
   206	            continue
   207	        top = min(due, key=lambda n: n["pick"])   # WHAT: 到期集合内衰减 Beta 排序
   208	        ranked.append({
   209	            "board": board,
   210	            "top_node": top["node"],
   211	            "priority": round(top["pick"], 4),
   212	            "pending": len(due),                   # 到期即待复习 (Decision-FSRS-2)
   213	            "idle_days": (None if top["idle_days"] is None else int(top["idle_days"])),
   214	            "difficulty": top["difficulty"],
   215	            "next_due": min((n["fsrs_due"] for n in members if not n["due_now"]), default=""),
   216	            "_tie": (
   217	                round(top["pick"], 8),
   218	                board_last_recommended.get(board, ""),   # 空串 = 从未被推荐, 排最前
   219	                min(n["last_examined"] for n in due),    # 空串 = 有从未考节点, 排最前
   220	                board,
   221	            ),
   222	        })
   223	    ranked.sort(key=lambda r: r["_tie"])
   224	    for r in ranked:
   225	        del r["_tie"]
   226	    upcoming.sort(key=lambda u: u["next_due"])
   227	    return ranked, upcoming, unassigned
   228	
   229	
   230	def _title(board: str) -> str:
   231	    prefix = "📚 今日复习 · "
   232	    room = TITLE_LIMIT - len(prefix)
   233	    return prefix + (board if len(board) <= room else board[: room - 1] + "…")
   234	
   235	
   236	def _body(top: dict) -> str:
   237	    idle = "从未考察" if top["idle_days"] is None else f"已闲置 {top['idle_days']} 天"
   238	    if top["pending"] >= 2:
   239	        return f"{top['top_node']} 等 {top['pending']} 节点待巩固 · {idle}"
   240	    return f"{top['top_node']} 待巩固 · {idle}"

exec
/bin/zsh -lc "nl -ba scripts/send_bark.py | sed -n '1,180p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
     1	#!/usr/bin/env python3
     2	"""Bark 推送器 (DAILY-REVIEW-PUSH-2026-07-29, 终审 A5 硬化版)。
     3	
     4	安全契约:
     5	  - key 只存 ~/.config/canvas-review/bark.key (600), 不进 URL/argv/日志
     6	  - POST https://api.day.app/push JSON body (非 GET 路径拼接 — 免 URL
     7	    编码地雷 + 免板名进进程参数)
     8	  - 同日稳定 notification id → Bark 端幂等更新 (本地 at-least-once +
     9	    服务端同 id 覆盖, 终审 A4 网络 exactly-once 的正解)
    10	  - 内容形态: 明文具体板名 (用户 2026-07-29 拍板; E2E 加密进 backlog)
    11	
    12	退出码: 0 = 服务端明确接受 (HTTP 200 且 body code==200)
    13	        2 = 未配置 key (跳过, 不算错)
    14	        1 = 发送失败 (调用方走 osascript 兜底)
    15	"""
    16	
    17	from __future__ import annotations
    18	
    19	import argparse
    20	import json
    21	import os
    22	import re
    23	import sys
    24	import time
    25	import urllib.error
    26	import urllib.request
    27	from pathlib import Path
    28	
    29	KEY_FILE = Path(
    30	    os.environ.get("BARK_KEY_FILE")
    31	    or Path.home() / ".config" / "canvas-review" / "bark.key"
    32	)
    33	DEFAULT_SERVER = "https://api.day.app"
    34	TIMEOUT_S = 10
    35	RETRIES = 2
    36	
    37	
    38	def load_key() -> tuple[str, str] | None:
    39	    """读 key 文件 → (server, device_key)。兼容整段 URL 或裸 key。
    40	
    41	    Code-Review L4: 格式不合法 (贴了裸域名/空串) 按未配置处理并给具体
    42	    提示, 不进重试循环报误导性的 net= 错误。
    43	    """
    44	    if not KEY_FILE.exists():
    45	        print("bark skip(未配置) — 写入 ~/.config/canvas-review/bark.key 后启用")
    46	        return None
    47	    raw = KEY_FILE.read_text(encoding="utf-8").strip().rstrip("/")
    48	    if raw.startswith("http"):
    49	        server, _, key = raw.rpartition("/")
    50	    else:
    51	        server, key = DEFAULT_SERVER, raw
    52	    if not re.fullmatch(r"[A-Za-z0-9_-]{8,64}", key) or not server.startswith("http"):
    53	        print("bark skip(key格式不合法 — 应为 Bark app 复制的推送 key)")
    54	        return None
    55	    return (server, key)
    56	
    57	
    58	def send(notification: dict) -> int:
    59	    cfg = load_key()
    60	    if cfg is None:
    61	        return 2
    62	    server, device_key = cfg
    63	    body = json.dumps(
    64	        {
    65	            "device_key": device_key,
    66	            "title": notification["title"],
    67	            "body": notification["body"],
    68	            "group": notification.get("group", "canvas复习"),
    69	            "id": notification["id"],
    70	        },
    71	        ensure_ascii=False,
    72	    ).encode("utf-8")
    73	
    74	    last_err = "unknown"
    75	    for attempt in range(1 + RETRIES):
    76	        if attempt:
    77	            time.sleep(2 * attempt)
    78	        req = urllib.request.Request(
    79	            f"{server}/push", data=body,
    80	            headers={"Content-Type": "application/json; charset=utf-8"},
    81	            method="POST",
    82	        )
    83	        try:
    84	            with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
    85	                http = resp.status
    86	                try:
    87	                    code = json.loads(resp.read().decode("utf-8")).get("code")
    88	                except (json.JSONDecodeError, UnicodeDecodeError):
    89	                    code = None
    90	            if http == 200 and code == 200:
    91	                print(f"bark accepted http={http} code={code}")
    92	                return 0
    93	            last_err = f"http={http} code={code}"
    94	        except urllib.error.HTTPError as e:
    95	            last_err = f"http={e.code}"
    96	        except (urllib.error.URLError, TimeoutError, OSError) as e:
    97	            last_err = f"net={type(e).__name__}"
    98	    print(f"bark failed {last_err}")  # 永不打印 key/URL
    99	    return 1
   100	
   101	
   102	def main():
   103	    ap = argparse.ArgumentParser(description="Bark 推送 (payload 不进命令行)")
   104	    ap.add_argument("--payload", required=True, help="今日复习.json 路径")
   105	    args = ap.parse_args()
   106	    payload = json.loads(Path(args.payload).read_text(encoding="utf-8"))
   107	    noti = payload.get("notification")
   108	    if not noti:
   109	        print("bark skip(无可推内容)")
   110	        return 2
   111	    return send(noti)
   112	
   113	
   114	if __name__ == "__main__":
   115	    sys.exit(main())

exec
/bin/zsh -lc "rg -l \"daily_review_run.py\" scripts --glob '*.sh' --glob '*.plist' | sort" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
scripts/daily-review-push.sh

exec
/bin/zsh -lc "rg -n \"fsrs_due\" canvas-vault/.claude backend/app .claude --glob '*.py' --glob '*.md' --glob '*.js' --glob '*.ts' | head -n 240" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
canvas-vault/.claude/skills/quiz-answer/SKILL.md:252:# 复习, 产出 fsrs_due 等 6 字段供推送链读侧判「今天谁到期」。桥内部自动
canvas-vault/.claude/skills/quiz-answer/SKILL.md:281:    fm = re.sub(r'^(fsrs_due|fsrs_state|fsrs_step|fsrs_stability|fsrs_difficulty|fsrs_last_review):.*\r?\n?', '', fm, flags=re.M)
canvas-vault/.claude/scripts/fsrs_bridge.py:5:frontmatter 字段 (fsrs_due/state/step/stability/difficulty/last_review)。
canvas-vault/.claude/scripts/fsrs_bridge.py:45:    "fsrs_due", "fsrs_state", "fsrs_step",
canvas-vault/.claude/scripts/fsrs_bridge.py:89:    if fields.get("fsrs_due"):
canvas-vault/.claude/scripts/fsrs_bridge.py:96:            due=_aware(fields["fsrs_due"]),
canvas-vault/.claude/scripts/fsrs_bridge.py:106:        "fsrs_due": _iso(card.due),
backend/app/services/mastery_engine.py:650:        fsrs_due_date = None
backend/app/services/mastery_engine.py:657:                        fsrs_due_date = due.isoformat()
backend/app/services/mastery_engine.py:659:                        fsrs_due_date = due
backend/app/services/mastery_engine.py:694:            "fsrs_due_date": fsrs_due_date,
backend/app/api/v1/endpoints/profile.py:69:    fsrs_due_date: Optional[str] = None
backend/app/api/v1/endpoints/profile.py:172:            fsrs_due_date=None,
backend/app/api/v1/endpoints/profile.py:196:        fsrs_due_date=resp.get("fsrs_due_date"),
backend/app/api/v1/endpoints/review.py:106:# frontmatter fsrs_due (写侧 quiz-answer × fsrs_bridge, 读侧 daily_review_pick)。

**Planning wrapper and quiz inspection**
exec
/bin/zsh -lc "nl -ba canvas-vault/.claude/scripts/fsrs_bridge.py | sed -n '1,180p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
     1	#!/usr/bin/env python3
     2	"""FSRS WHEN 桥 (FSRS-V2-2026-07-30, [Decision-FSRS-1/2])。
     3	
     4	职责: 把 quiz-answer 的一次评分翻译成 py-fsrs 复习, 产出 6 个加性
     5	frontmatter 字段 (fsrs_due/state/step/stability/difficulty/last_review)。
     6	无字段 = New 卡即刻到期 (零迁移)。
     7	
     8	调用形态: quiz-answer 静态段用系统 python3 (stdlib) 经 stdin JSON 调本
     9	文件; 本文件发现 fsrs 不可导入时自动 re-exec backend/.venv python。
    10	调度计算全部收拢在写侧 — 读侧 (daily_review_pick/Dashboard) 只做字符串
    11	日期比较, 维持 launchd 纯 stdlib 契约 (审查报告 §四-④)。
    12	
    13	参数契约: DEFAULT_PARAMETERS + desired_retention=0.9 + enable_fuzzing=False
    14	(可复现可测试; 个人化拟合 F6 延后)。被 backend/tests/regression/
    15	test_fsrs_bridge.py 锁定。
    16	"""
    17	
    18	from __future__ import annotations
    19	
    20	import json
    21	import os
    22	import re
    23	import sys
    24	from datetime import datetime, timezone
    25	
    26	def _venv_python() -> str | None:
    27	    """候选顺序: 相对本 vault 的仓库根 backend/.venv (worktree 与主仓副本各自
    28	    成立, Code-Review H1: 不能让 live vault 的 FSRS 写侧系于 dev worktree
    29	    存亡) → 硬编码 worktree 路径兜底。"""
    30	    from pathlib import Path
    31	
    32	    candidates = [
    33	        Path(__file__).resolve().parents[3] / "backend" / ".venv" / "bin" / "python",
    34	        Path(
    35	            "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/"
    36	            "feature-obsidian-hybrid-dev/backend/.venv/bin/python"
    37	        ),
    38	    ]
    39	    for c in candidates:
    40	        if c.exists():
    41	            return str(c)
    42	    return None
    43	
    44	FIELD_ORDER = (
    45	    "fsrs_due", "fsrs_state", "fsrs_step",
    46	    "fsrs_stability", "fsrs_difficulty", "fsrs_last_review",
    47	)
    48	
    49	
    50	def _aware(s: str) -> datetime:
    51	    dt = datetime.fromisoformat(str(s).strip().replace("Z", "+00:00"))
    52	    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    53	
    54	
    55	def _iso(dt: datetime) -> str:
    56	    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    57	
    58	
    59	def rating_from_grade(grade_norm: float, abandoned: bool) -> int:
    60	    """[Decision-FSRS-1] 弃答→Again; 否则还原 grade=1+3·gn 就近落四档。"""
    61	    if abandoned:
    62	        return 1
    63	    g = 1.0 + 3.0 * max(0.0, min(1.0, float(grade_norm)))
    64	    if g < 1.5:
    65	        return 1
    66	    if g < 2.5:
    67	        return 2
    68	    if g < 3.5:
    69	        return 3
    70	    return 4
    71	
    72	
    73	def fields_from_frontmatter(fm: str) -> dict:
    74	    """从 frontmatter 文本抽 fsrs_* 字段 (纯 stdlib, 读侧同款正则)。"""
    75	    out = {}
    76	    for key in FIELD_ORDER:
    77	        m = re.search(rf'^{key}:\s*"?([^"\n]+?)"?\s*$', fm, re.M)
    78	        if m:
    79	            out[key] = m.group(1).strip()
    80	    return out
    81	
    82	
    83	def review(fields: dict, grade_norm: float, abandoned: bool, ts: str) -> dict:
    84	    """一次评分 → 新 fsrs_* 字段 (需要 fsrs 可导入)。"""
    85	    from fsrs import Card, Rating, Scheduler, State
    86	
    87	    now = _aware(ts)
    88	    sched = Scheduler(enable_fuzzing=False)
    89	    if fields.get("fsrs_due"):
    90	        step = fields.get("fsrs_step")
    91	        card = Card(
    92	            state=State(int(fields.get("fsrs_state", 1))),
    93	            step=int(step) if step not in (None, "") else None,
    94	            stability=float(fields["fsrs_stability"]) if fields.get("fsrs_stability") else None,
    95	            difficulty=float(fields["fsrs_difficulty"]) if fields.get("fsrs_difficulty") else None,
    96	            due=_aware(fields["fsrs_due"]),
    97	            last_review=_aware(fields["fsrs_last_review"]) if fields.get("fsrs_last_review") else None,
    98	        )
    99	    else:
   100	        card = Card(due=now)  # 无字段 = New 卡即刻到期 (零迁移)
   101	
   102	    card, _log = sched.review_card(
   103	        card, Rating(rating_from_grade(grade_norm, abandoned)), review_datetime=now
   104	    )
   105	    out = {
   106	        "fsrs_due": _iso(card.due),
   107	        "fsrs_state": int(card.state),
   108	        "fsrs_step": card.step if card.step is not None else "",
   109	        "fsrs_stability": round(card.stability, 4) if card.stability is not None else "",
   110	        "fsrs_difficulty": round(card.difficulty, 4) if card.difficulty is not None else "",
   111	        "fsrs_last_review": _iso(now),
   112	    }
   113	    out["fm_block"] = "\n".join(
   114	        f"{k}: {out[k]}" for k in FIELD_ORDER if out[k] != ""
   115	    )
   116	    return out
   117	
   118	
   119	def _ensure_fsrs() -> bool:
   120	    try:
   121	        import fsrs  # noqa: F401
   122	        return True
   123	    except ImportError:
   124	        venv_py = _venv_python()
   125	        if os.environ.get("FSRS_BRIDGE_REEXEC") != "1" and venv_py:
   126	            os.environ["FSRS_BRIDGE_REEXEC"] = "1"
   127	            os.execv(venv_py, [venv_py, os.path.abspath(__file__)] + sys.argv[1:])
   128	        return False
   129	
   130	
   131	def main() -> int:
   132	    if not _ensure_fsrs():
   133	        print(json.dumps({"error": "fsrs_unavailable — backend/.venv 缺失或未装 fsrs"}))
   134	        return 3
   135	    p = json.load(sys.stdin)
   136	    out = review(
   137	        fields_from_frontmatter(p.get("fm", "")),
   138	        float(p.get("grade_norm", 0.0)),
   139	        bool(p.get("abandoned")),
   140	        p["ts"],
   141	    )
   142	    print(json.dumps(out, ensure_ascii=False))
   143	    return 0
   144	
   145	
   146	if __name__ == "__main__":
   147	    sys.exit(main())

exec
/bin/zsh -lc "nl -ba canvas-vault/.claude/skills/quiz-answer/SKILL.md | sed -n '230,315p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
   230	    A, B = from_legacy(old)  # 旧 EMA 分迁移: 均值继承, 只给等效样本量3的低置信
   231	else:
   232	    A, B = PRIOR_A, PRIOR_B
   233	# 闲置感知评分 (终审 A2, DAILY-REVIEW-PUSH-2026-07-29): 先按闲置天数折旧旧证据
   234	# 再吸收本次成绩 — 否则闲置期抬高的 σ 会被旧 n 一次评分瞬间抹平
   235	# (置信度复活病理: 闲置一年答错, pick 反而 0.632→0.692 更不紧急)。
   236	from datetime import datetime, timezone
   237	def _aware(s):
   238	    dt = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
   239	    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
   240	days_idle = 0.0
   241	mle = re.search(r'^last_examined:\s*"?([^"\n]+)"?\s*$', fm, re.M)
   242	if mle:
   243	    try:
   244	        days_idle = max(0.0, (_aware(p["ts"]) - _aware(mle.group(1))).total_seconds() / 86400.0)
   245	    except ValueError:
   246	        days_idle = 0.0  # 时间戳损坏: 不折旧, 保守按连续考察处理
   247	A, B = max(A, 1e-4), max(B, 1e-4)  # 手工编辑容错: a/b 被改成 0 时 effective 会拒 (Code-Review L7)
   248	A, B = update_after_idle(A, B, GN, days_idle)
   249	new = round(mu(A, B), 2)
   250	
   251	# FSRS WHEN 桥 (FSRS-V2-2026-07-30, [Decision-FSRS-1/2]): 评分即一次 FSRS
   252	# 复习, 产出 fsrs_due 等 6 字段供推送链读侧判「今天谁到期」。桥内部自动
   253	# re-exec backend venv python; 任何失败诚实降级 — 衰减 Beta 照常写, 只丢
   254	# WHEN 字段并在 stdout 明说 (不静默)。
   255	import subprocess
   256	fsrs_block = ""
   257	try:
   258	    _r = subprocess.run(
   259	        ["python3", os.path.join(VAULT, ".claude", "scripts", "fsrs_bridge.py")],
   260	        input=json.dumps({"fm": fm, "grade_norm": GN,
   261	                          "abandoned": bool(p.get("abandoned")), "ts": p["ts"]}),
   262	        capture_output=True, text=True, timeout=30)
   263	    try:
   264	        _out = json.loads(_r.stdout) if _r.stdout.strip() else {}
   265	    except ValueError:
   266	        _out = {}
   267	    fsrs_block = ("\n" + _out["fm_block"]) if _out.get("fm_block") else ""
   268	    if not fsrs_block:
   269	        # Code-Review M1: 无论退出码都先看 stdout 的诚实报错, 再退 stderr
   270	        print(f"[quiz-answer] FSRS 桥降级跳过(不影响评分): {_out.get('error') or _r.stdout[:120] or _r.stderr[:120]}")
   271	except Exception as _e:
   272	    print(f"[quiz-answer] FSRS 桥降级跳过(不影响评分): {_e}")
   273	# A4 (批次2'): 考察历史随节点走 — attempt_count 累加 + last_examined 时间戳,
   274	# 出题侧 (start-exam-board) 回读它们做题目去重与历史感知
   275	mo_att = re.search(r'^attempt_count:\s*(\d+)', fm, re.M)
   276	n_att = (int(mo_att.group(1)) if mo_att else 0) + 1
   277	fm = re.sub(r'^(mastery_score|mastery|mastery_level|mastery_a|mastery_b|attempt_count|last_examined):.*\r?\n?', '', fm, flags=re.M)
   278	# Code-Review H2: 只有桥成功产出新 fsrs 字段才删旧行 — 桥失败时保留节点
   279	# 已积累的调度状态 (否则一次临时故障 = 卡片退回 New, 间隔历史全灭)
   280	if fsrs_block:
   281	    fm = re.sub(r'^(fsrs_due|fsrs_state|fsrs_step|fsrs_stability|fsrs_difficulty|fsrs_last_review):.*\r?\n?', '', fm, flags=re.M)
   282	fm = re.sub(r'^(type:.*)$', lambda x: x.group(1) + f"\nmastery_score: {new}\nmastery_a: {round(A, 4)}\nmastery_b: {round(B, 4)}\nattempt_count: {n_att}\nlast_examined: " + json.dumps(p["ts"], ensure_ascii=False) + fsrs_block, fm, count=1, flags=re.M)
   283	
   284	# calibration_log 结构化事件（开头的事件级幂等已保证本事件未记录过）
   285	q = lambda v: json.dumps(v, ensure_ascii=False)
   286	scn = p.get("self_confidence_norm")
   287	entry = (f'  - event_id: {q(eid)}\n'
   288	         f'    ts: {q(p["ts"])}\n'
   289	         f'    exam_board: {q(p.get("exam_board",""))}\n'
   290	         f'    question_id: {q(p.get("question_id","q1"))}\n'
   291	         f'    self_confidence_raw: {q(p.get("self_confidence_raw") or "null")}\n'
   292	         f'    self_confidence_norm: {scn if scn is not None else "null"}\n'
   293	         f'    grade_norm: {round(GN, 2)}\n'
   294	         f'    abandoned: {"true" if p.get("abandoned") else "false"}')
   295	# F3 修复 (2026-07-12): 定位 calibration_log 块末尾插入 — 旧逻辑无条件追加
   296	# 到 frontmatter 末尾, 当 calibration_log 非最后一个 key 时 (Obsidian
   297	# Properties 面板默认在末尾新增属性, 极常见), 事件条目会被 YAML 静默
   298	# 归档进相邻列表键 (如 aliases), 校准数据丢失且零报错。
   299	mcal = re.search(r'^calibration_log:', fm, re.M)
   300	if mcal:
   301	    lines = fm.split("\n")
   302	    li = next(i for i, ln in enumerate(lines) if re.match(r'^calibration_log:', ln))
   303	    j = li + 1
   304	    while j < len(lines) and lines[j].startswith("  "):
   305	        j += 1
   306	    lines[j:j] = entry.split("\n")
   307	    fm = "\n".join(lines)
   308	else:
   309	    fm = fm.rstrip() + "\ncalibration_log:\n" + entry
   310	
   311	# 疑问归纳 callout（前置空行防并块；内容幂等：续跑不重复 append）
   312	cal = (p.get("callout") or "").strip()
   313	if cal and cal not in body:
   314	    body = body.rstrip() + "\n\n" + cal + "\n"
   315	

exec
/bin/zsh -lc "nl -ba scripts/daily-review-push.sh | sed -n '1,260p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
     1	#!/usr/bin/env bash
     2	# 每日复习推送 — 编排壳 (DAILY-REVIEW-PUSH-2026-07-29)。
     3	# 只做两件事: mkdir 互斥锁 (终审 A7: 手工/kickstart/定时可能重叠) +
     4	# 固定解释器调 runner。业务逻辑全在 daily_review_run.py (--now 可测)。
     5	set -uo pipefail
     6	
     7	REPO="/Users/Heishing/Desktop/canvas/canvas-learning-system"
     8	WT="$REPO/.claude/worktrees/feature-obsidian-hybrid-dev"
     9	LOCK="$REPO/backups/.daily-review.lock"
    10	
    11	mkdir -p "$REPO/backups"
    12	if ! mkdir "$LOCK" 2>/dev/null; then
    13	    # 陈旧锁恢复 (Code-Review M5): 断电/SIGKILL 会留下锁目录, 不处理则
    14	    # 之后每天 "skip: already running" 且 exit 0 永久静默。mtime 超 6h
    15	    # 视为死锁夺回 (单次运行实测秒级, 6h 余量极大)。
    16	    if [ -n "$(find "$LOCK" -maxdepth 0 -mmin +360 2>/dev/null)" ]; then
    17	        echo "stale lock (>6h), reclaiming" >&2
    18	        rmdir "$LOCK" 2>/dev/null || true
    19	    fi
    20	    if ! mkdir "$LOCK" 2>/dev/null; then
    21	        echo "skip: already running" >&2
    22	        exit 0
    23	    fi
    24	fi
    25	# 不用 exec — exec 会替换进程使 trap 失效, 锁永不释放
    26	trap 'rmdir "$LOCK" 2>/dev/null || true' EXIT INT TERM
    27	
    28	PY="$WT/backend/.venv/bin/python"
    29	[ -x "$PY" ] || PY="/usr/bin/python3"   # venv 缺失兜底 (runner 仅 stdlib)
    30	
    31	"$PY" "$WT/scripts/daily_review_run.py" "$@"

exec
/bin/zsh -lc "git show worktree-feature-obsidian-hybrid-dev:scripts/daily_review_run.py | nl -ba | sed -n '70,160p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
    70	
    71	def save_state(st: dict):
    72	    STATE.parent.mkdir(parents=True, exist_ok=True)
    73	    tmp = STATE.with_suffix(".tmp")
    74	    tmp.write_text(json.dumps(st, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    75	    os.replace(tmp, STATE)
    76	
    77	
    78	def log_line(msg: str):
    79	    LOG.parent.mkdir(parents=True, exist_ok=True)
    80	    stamp = datetime.now().astimezone().strftime("%F %T")
    81	    with open(LOG, "a", encoding="utf-8") as f:
    82	        f.write(f"[{stamp}] {msg}\n")
    83	
    84	
    85	def ensure_payload(st: dict, now: datetime, today: str) -> tuple[dict | None, str]:
    86	    """当日 payload: 没有才生成 (生成过则复用 — 补跑只补推送)。"""
    87	    payload_path = VAULT / "outputs" / "今日复习.json"
    88	    if st.get("last_generate_date") == today and payload_path.exists():
    89	        try:
    90	            raw = payload_path.read_text(encoding="utf-8")
    91	            # sha 校验 (Code-Review L3): 外部改动/半写的 payload 不复用, 重新生成
    92	            if hashlib.sha256(raw.encode("utf-8")).hexdigest() == st.get("payload_sha256"):
    93	                return json.loads(raw), "cached"
    94	        except (json.JSONDecodeError, OSError):
    95	            pass  # 落盘 payload 损坏 → 重新生成
    96	
    97	    import daily_review_pick as picker
    98	
    99	    payload, ranked = picker.build_payload(
   100	        VAULT, now, st["board_last_recommended"], picker.load_decay(VAULT))
   101	    out = VAULT / "outputs"
   102	    out.mkdir(parents=True, exist_ok=True)
   103	    picker.atomic_write(out / "今日复习.md", picker.render_md(payload, ranked))
   104	    raw = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
   105	    picker.atomic_write(payload_path, raw)
   106	
   107	    st["last_generate_date"] = today
   108	    st["payload_sha256"] = hashlib.sha256(raw.encode("utf-8")).hexdigest()
   109	    if ranked:
   110	        st["board_last_recommended"][ranked[0]["board"]] = today
   111	    save_state(st)
   112	    return payload, "new"
   113	
   114	
   115	def osascript_fallback(noti: dict) -> bool:
   116	    try:
   117	        r = subprocess.run(
   118	            ["/usr/bin/osascript", "-", noti["title"], noti["body"]],
   119	            input=APPLESCRIPT, text=True, capture_output=True, timeout=15,
   120	        )
   121	        return r.returncode == 0
   122	    except (OSError, subprocess.TimeoutExpired):
   123	        return False
   124	
   125	
   126	def main() -> int:
   127	    global VAULT
   128	    ap = argparse.ArgumentParser(description="每日复习推送编排")
   129	    ap.add_argument("--now", help="ISO 时间覆盖 (12 场景验收矩阵用)")
   130	    ap.add_argument("--vault", help="活 vault 路径 (wrapper 从 .env ACTIVE_VAULT 解析传入; 缺省回退 canvas-vault)")
   131	    args = ap.parse_args()
   132	
   133	    if args.vault:
   134	        VAULT = Path(args.vault)
   135	
   136	    now = _now(args.now)
   137	    local = now.astimezone()
   138	    today = local.date().isoformat()
   139	    st = load_state()
   140	
   141	    try:
   142	        payload, gen = ensure_payload(st, now, today)
   143	    except Exception as e:  # 生成失败 = 无保底, 唯一的非 0 退出
   144	        log_line(f"generate:FAILED err={type(e).__name__}:{str(e)[:120]}")
   145	        print(f"[runner] 生成失败: {e}", file=sys.stderr)
   146	        return 1
   147	
   148	    noti = (payload or {}).get("notification")
   149	    push, fallback = "-", "-"
   150	    if not noti:
   151	        push = "skip-empty"  # 无板可推 (全占位/空 vault): md 已如实落盘
   152	    elif st.get("last_push_accepted_date") == today:
   153	        push = "skip-done"
   154	    elif not (PUSH_WINDOW[0] <= local.time() < PUSH_WINDOW[1]):
   155	        push = "skip-window"  # RunAtLoad 早触发 / 21:00 后唤醒: 只落盘
   156	    else:
   157	        rc = send_bark.send(noti)
   158	        if rc == 0:
   159	            st["last_push_accepted_date"] = today
   160	            st["last_result"], st["last_error"] = "pushed", ""

exec
/bin/zsh -lc 'git diff --check worktree-feature-obsidian-hybrid-dev...HEAD && git show --stat --oneline --decorate HEAD' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
346448b7 (HEAD -> card/a3-relearn) fix(review): same-day relearn card refresh via mtime cache invalidation
 backend/tests/regression/test_daily_review_run.py | 235 ++++++++++++++++++++++
 scripts/daily_review_run.py                       |  45 ++++-
 scripts/launchd/com.canvas.daily-review.plist     |  83 +++++++-
 3 files changed, 353 insertions(+), 10 deletions(-)

**Analyzing board update edge case**
**Evaluating push notification update logic**
**Verifying crash handling and scheduling**
**Clarifying time window and caching logic**
**Verifying mtime comparison and test timing**
**Identifying stale cache risk on stat failure**
**Evaluating cache invalidation risks**
**Verifying atomic write behavior**
exec
/bin/zsh -lc "nl -ba canvas-vault/.claude/skills/quiz-answer/SKILL.md | sed -n '315,390p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
   315	
   316	# F4 修复 (2026-07-12): 真原子写 — tmpfile + os.replace, 进程中断不再截断节点文件
   317	tmp = NODE + ".quiz-tmp"
   318	open(tmp, "w", encoding="utf-8").write(f"---\n{fm}\n---\n{body}")
   319	os.replace(tmp, NODE)
   320	os.remove(P)
   321	print(f"[quiz-answer] {NODE}: mastery {old}->{new}; event={eid}; callout={'yes' if cal else 'no'}")
   322	# 批次3' 2-4 (MEM-FLYWHEEL): 统一学习事件日志 — append-only + 幂等键,
   323	# frontmatter 仍是真相源, 日志供过程回放/图重建兜底。写失败不影响评分。
   324	EV = os.path.join(VAULT, "learning_events.jsonl")
   325	etype = "answer_abandoned" if p.get("abandoned") else "answer_scored"
   326	evid = "quiz:" + eid
   327	try:
   328	    seen = False
   329	    if os.path.exists(EV):
   330	        with open(EV, encoding="utf-8") as _f:
   331	            seen = any(json.dumps(evid, ensure_ascii=False) in ln for ln in _f)
   332	    if not seen:
   333	        rec = {"event_id": evid, "event_version": 1, "event_type": etype,
   334	               "node_id": os.path.splitext(os.path.basename(NODE))[0],
   335	               "recorded_at": p["ts"], "effective_at": p["ts"],
   336	               "payload": {"grade_norm": round(GN, 2),
   337	                           "exam_board": p.get("exam_board", ""),
   338	                           "attempt_count": n_att}}
   339	        with open(EV, "a", encoding="utf-8") as _f:
   340	            _f.write(json.dumps(rec, ensure_ascii=False) + "\n")
   341	        print(f"[quiz-answer] 事件已落日志: {etype}")
   342	except Exception as _e:
   343	    print(f"[quiz-answer] 事件日志写入失败(不影响评分): {_e}")
   344	PYEOF
   345	```
   346	
   347	（衰减 Beta：评分前先按闲置天数折旧 `a,b ← a,b·0.99^days_idle`（防置信度复活，终审 A2），再 `a←γa+grade, b←γb+(1−grade)`，γ=0.9，`mastery_score=μ=a/(a+b)`；越考越准（σ 收窄）且 ~10 次内跟上状态跳变，取代不收敛的恒权 EMA（批次2' A1）。算法与常数见 `.claude/scripts/decay_beta.py`，v2 上层再接 FSRS 调度。python stdout 只给你看，不进回执。）
   348	
   349	## Step 4c-bis · 刷新原白板目录（RAG-S2.6 T2 · 掌握度行内值的唯一保鲜点）
   350	
   351	python 写分成功后，**`Bash` 跑一次目录同步**——把新掌握度 / `attempt_count`
   352	刷进原白板 `## Concepts` 的行内显示：
   353	
   354	```bash
   355	python3 .claude/scripts/sync_board_concepts.py --board "<被考节点的 source_board stem>"
   356	```
   357	
   358	- `<board stem>` 从被考节点 frontmatter `source_board: "[[原白板/<stem>]]"` 取（Step 4 python 已回填过该字段）。
   359	- **为什么放在这里**：`## Concepts` 行内的「掌握度 X.XX · 已考 N 次」是派生值，
   360	  而**全系统唯一会系统性改动掌握度的就是本 Skill 的写分**。在唯一会变的时刻同步，
   361	  行内值就不会过期（闲置折旧不改 μ，只改 σ，所以不闲置不需要同步）。
   362	- ⛔ 本步**不阻断落定**：同步失败照常进 Step 4d 置 `done`，只在 stdout 留一行提示。
   363	
   364	<!-- FALLBACK:BEGIN Step 4c-bis 目录同步降级 -->
   365	脚本缺失 / 非零退出 / 取不到 `source_board` → **跳过本步**，一切照旧：
   366	分数与 `mastery_score` 已写进节点 frontmatter（那才是真相源），
   367	`## Concepts` 只是派生显示，下次任一次同步会自动追平。回执**不因此加 ⚠**。
   368	<!-- FALLBACK:END -->
   369	
   370	## Step 4d · 落定 done（两阶段第二步）
   371	
   372	python 成功（exit 0）后，`Edit` 检验白板 frontmatter：
   373	- **`status: done`** + `node_update_at: <ts>`
   374	- python 失败 → **保持 `scored_pending_node_update`**，回执告知"分数已保存,节点更新失败,重跑 /quiz-answer 会自动续跑"。
   375	
   376	**重量疑问** → 回执引导：在检验白板里选中疑问文字按 `Cmd+Shift+D` 派生独立疑问节点（自动归属原白板、关联被考节点）。
   377	
   378	## Step 5 · 静默回执（不显分 + 诚实声明）
   379	
   380	```
   381	✓ 已静默评分并落定（status: done）。分数已写入检验白板 frontmatter，本 Skill 不主动显示（保护 d=1.50）。
   382	✓ 节点 <concept> 的掌握度已本地更新（具体变化去 Dashboard 看，延迟反馈更利于长期记住）
   383	✓ calibration 事件已记录（event_id 可回灌 v2 校准）
   384	{有疑问时} ✓ 已把你的 N 条新疑问归纳回原节点 节点/<concept>.md（下次考它时会带上）
   385	{有疑问时} 💡 想把某条疑问独立成节点：选中它按 Cmd+Shift+D 派生（自动归属原白板、关联被考节点）
   386	{触发门禁时} ⚠ 该节点正文疑似有基础事实问题（已标 needs_content_review），建议尽快去修正
   387	→ 反馈请开 Dashboard 看 mastery_score 变化 + 复习建议
   388	
   389	ℹ️ 诚实声明（v1）：mastery_score 是本地简易估计、非后端 5 信号融合；
   390	   v1 不宣称"熟练度驱动 / 校准闭环"有效（后端 4 处管道断裂，留 v2）。

exec
/bin/zsh -lc "rg -n -C 5 \"write_text|os.replace|rename|open\\(|Path\\(|target|node_path|vault\" canvas-vault/.claude/skills/quiz-answer/SKILL.md | tail -n 160" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
14----
15-
16-<!-- ROUTING:BEGIN v1 -->
17-## ⛔ 检索平面协议 v1（RAG-S2.6 导航改造 · 先看目录再精读）
18-
19:⛔ **动手前先判定平面**，判错 = 白烧上下文（vault 越大越明显）。四个平面，每个只有一个正确的第一动作：
20-
21-| 平面 | 什么问题属于它 | 第一动作（唯一正确） |
22-|---|---|---|
23-| **STRUCTURE** | 这块板拆了哪些节点 / 谁派生自谁 / 哪个最该考 / 掌握度与考察历史 | **1 次** `get_board_manifest` —— 不先 Grep、不 Read 白板全文 |
24-| **SEMANTIC** | 「关于 X 的内容在哪」「X 和 Y 什么关系」 | 先用 manifest 成员清单**限域**，再在域内检索；⛔ 不得退化成全库 `**/*.md` 裸扫 |
--
29-
30-- **HARD-NAV-1**：`get_board_manifest` **一次调用即返回该板全部结构**（成员 + 派生原因 + 掌握度四态 + 占位标记 + 选点秩 + 考察历史 + 题面摘句）。同一板同一轮**不得调第 2 次**。
31-- **HARD-NAV-2**：manifest **不含节点正文**。要正文 → 转 CONTENT 平面，别指望 manifest 给。
32-- **HARD-NAV-3**：每处 manifest 调用**必须**配成对 `<!-- FALLBACK:BEGIN/END -->` 降级块。失败 / 超时 / 空结果 / 后端未起 → **静默**退回块内写明的原路径，**离线可用不破**，且不因此中止任务。
33-- **HARD-NAV-4**：本块在 8 份 skill 里**逐字节相同**，由 `backend/scripts/check_skill_routing_block.py` 校验。要改就 8 份一起改。
34:- **HARD-NAV-5**：⛔ **任何 skill 一律不得 `Read` / `Grep` / `Glob` `<vault>/.claude/cache/` 下的任何文件。**
35-  那是服务端的降级快照，存的是**未经视图投影的全量原料**（含 exam 禁项：纠错内容 / 批注正文 / 误解记录）。
36-  要结构就调工具走投影，绕过投影直读缓存 = 亲手拆掉 HARD-ISO 信息隔离。
37-<!-- ROUTING:END v1 -->
38-
39-<!-- PLANE-BINDING v1
--
98-
99-```bash
100-python3 - <<'PYEOF'
101-import json, re, os
102-P = "/tmp/quiz-answer-incr.json"
103:p = json.load(open(P, encoding="utf-8"))
104-NODE = p["node"]
105:s = open(NODE, encoding="utf-8").read()
106-m = re.match(r'^﻿?---\r?\n(.*?)\r?\n---[ \t]*\r?\n?(.*)$', s, re.S)
107-if not m:
108-    raise SystemExit("frontmatter 解析失败：" + NODE)
109-fm, body = m.group(1), m.group(2)
110-added = 0
--
112-    cal = cal.strip()
113-    if cal and cal not in body:
114-        body = body.rstrip() + "\n\n" + cal + "\n"
115-        added += 1
116-tmp = NODE + ".incr-tmp"
117:open(tmp, "w", encoding="utf-8").write(f"---\n{fm}\n---\n{body}")
118:os.replace(tmp, NODE)
119-os.remove(P)
120-print(f"[quiz-answer/A3] {NODE}: 增量归纳 {added} 条疑问 (分数未动)")
121-PYEOF
122-```
123-- **`scored_pending_node_update`**（上次 Step 4 节点写入失败的续跑态）→ **跳过 Step 1-3**（分数已在 frontmatter），直接从已存的 `questions[0].score`/`self_confidence` 重建 payload，续跑 Step 4 → Step 4c。python 内置 event_id 幂等，重复续跑不会双写。
--
181-
182-```bash
183-python3 - <<'PYEOF'
184-import json, re, os, sys
185-P = "/tmp/quiz-answer-payload.json"
186:p = json.load(open(P, encoding="utf-8"))
187-NODE = p["node"]; GN = float(p["grade_norm"])
188-# F3 修复 (2026-07-12): grade_norm 钳制 [0,1] — LLM 把 1-4 分误当 grade_norm
189-# 传入时 (如 3.5), 首评分支会把 mastery_score 直接写成 3.5 污染全链
190-GN = max(0.0, min(1.0, GN))
191-
192:s = open(NODE, encoding="utf-8").read()
193-m = re.match(r'^﻿?---\r?\n(.*?)\r?\n---[ \t]*\r?\n?(.*)$', s, re.S)
194-if not m:
195-    raise SystemExit("frontmatter 解析失败：" + NODE)
196-fm, body = m.group(1), m.group(2)
197-
--
311-# 疑问归纳 callout（前置空行防并块；内容幂等：续跑不重复 append）
312-cal = (p.get("callout") or "").strip()
313-if cal and cal not in body:
314-    body = body.rstrip() + "\n\n" + cal + "\n"
315-
316:# F4 修复 (2026-07-12): 真原子写 — tmpfile + os.replace, 进程中断不再截断节点文件
317-tmp = NODE + ".quiz-tmp"
318:open(tmp, "w", encoding="utf-8").write(f"---\n{fm}\n---\n{body}")
319:os.replace(tmp, NODE)
320-os.remove(P)
321-print(f"[quiz-answer] {NODE}: mastery {old}->{new}; event={eid}; callout={'yes' if cal else 'no'}")
322-# 批次3' 2-4 (MEM-FLYWHEEL): 统一学习事件日志 — append-only + 幂等键,
323-# frontmatter 仍是真相源, 日志供过程回放/图重建兜底。写失败不影响评分。
324-EV = os.path.join(VAULT, "learning_events.jsonl")
325-etype = "answer_abandoned" if p.get("abandoned") else "answer_scored"
326-evid = "quiz:" + eid
327-try:
328-    seen = False
329-    if os.path.exists(EV):
330:        with open(EV, encoding="utf-8") as _f:
331-            seen = any(json.dumps(evid, ensure_ascii=False) in ln for ln in _f)
332-    if not seen:
333-        rec = {"event_id": evid, "event_version": 1, "event_type": etype,
334-               "node_id": os.path.splitext(os.path.basename(NODE))[0],
335-               "recorded_at": p["ts"], "effective_at": p["ts"],
336-               "payload": {"grade_norm": round(GN, 2),
337-                           "exam_board": p.get("exam_board", ""),
338-                           "attempt_count": n_att}}
339:        with open(EV, "a", encoding="utf-8") as _f:
340-            _f.write(json.dumps(rec, ensure_ascii=False) + "\n")
341-        print(f"[quiz-answer] 事件已落日志: {etype}")
342-except Exception as _e:
343-    print(f"[quiz-answer] 事件日志写入失败(不影响评分): {_e}")
344-PYEOF

exec
/bin/zsh -lc "rg -n \"def atomic_write|write_text\\(|os.replace\\(\" canvas-vault/.claude/scripts canvas-vault/.claude/skills/quiz-answer -g '*.py' -g 'SKILL.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
canvas-vault/.claude/scripts/sync_board_concepts.py:582:def atomic_write(path: Path, text: str) -> None:
canvas-vault/.claude/scripts/sync_board_concepts.py:604:        os.replace(tmp, path)
canvas-vault/.claude/scripts/sync_board_concepts.py:703:                    bak.write_text(old, encoding="utf-8")
canvas-vault/.claude/skills/quiz-answer/SKILL.md:118:os.replace(tmp, NODE)
canvas-vault/.claude/skills/quiz-answer/SKILL.md:319:os.replace(tmp, NODE)

exec
/bin/zsh -lc "nl -ba scripts/daily_review_run.py | sed -n '78,225p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
    78	
    79	def log_line(msg: str):
    80	    LOG.parent.mkdir(parents=True, exist_ok=True)
    81	    stamp = datetime.now().astimezone().strftime("%F %T")
    82	    with open(LOG, "a", encoding="utf-8") as f:
    83	        f.write(f"[{stamp}] {msg}\n")
    84	
    85	
    86	def _nodes_max_mtime(vault: Path) -> float:
    87	    """节点池最新改动时间 (CARD-A3 缓存失效判据)。
    88	
    89	    文件 mtime 抓原地更新 (quiz 写 fsrs_due 不动目录), 目录 mtime 抓
    90	    增删改名 (不留文件 mtime); 误报代价只是一次幂等重扫。保 mtime 的
    91	    还原类操作 (rsync -a / Time Machine) 不在本判据覆盖面内。
    92	    """
    93	    pool = vault / "节点"
    94	    latest = 0.0
    95	    for p in pool.glob("*.md"):
    96	        try:
    97	            latest = max(latest, p.stat().st_mtime)
    98	        except OSError:
    99	            continue  # 迭代间隙被删: 殿后的目录 stat 捕获该变动
   100	    try:
   101	        # 目录 stat 殿后取样 — 迭代期间发生的删除也已反映在目录 mtime 里
   102	        latest = max(latest, pool.stat().st_mtime)
   103	    except OSError:
   104	        return 0.0  # 节点池不存在: 不因 mtime 失效, 保持旧缓存语义
   105	    return latest
   106	
   107	
   108	def ensure_payload(st: dict, now: datetime, today: str) -> tuple[dict | None, str]:
   109	    """当日 payload: 没有才生成 (生成过则复用 — 补跑只补推送)。
   110	
   111	    CARD-A3 (BATCH-2026-08-24-复习闭环): 复用多一道门 — 节点池比 payload
   112	    新 (quiz 写侧刚更新 fsrs_due / 新增重学卡) 则同日重扫, 否则当天到期的
   113	    重学卡永远进不了投影。push 去重不在此处: last_push_accepted_date 天然
   114	    保证同日只推一次。
   115	    """
   116	    payload_path = VAULT / "outputs" / "今日复习.json"
   117	    first_gen_today = st.get("last_generate_date") != today
   118	    if not first_gen_today and payload_path.exists():
   119	        try:
   120	            raw = payload_path.read_text(encoding="utf-8")
   121	            # sha 校验 (Code-Review L3): 外部改动/半写的 payload 不复用, 重新生成
   122	            if hashlib.sha256(raw.encode("utf-8")).hexdigest() == st.get("payload_sha256"):
   123	                if _nodes_max_mtime(VAULT) <= payload_path.stat().st_mtime:
   124	                    return json.loads(raw), "cached"
   125	        except (json.JSONDecodeError, OSError):
   126	            pass  # 落盘 payload 损坏 → 重新生成
   127	
   128	    import daily_review_pick as picker
   129	
   130	    scan_started = time.time()
   131	    payload, ranked = picker.build_payload(
   132	        VAULT, now, st["board_last_recommended"], picker.load_decay(VAULT))
   133	    out = VAULT / "outputs"
   134	    out.mkdir(parents=True, exist_ok=True)
   135	    picker.atomic_write(out / "今日复习.md", picker.render_md(payload, ranked))
   136	    raw = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
   137	    picker.atomic_write(payload_path, raw)
   138	    # mtime 门基准回拨到扫描起点: 扫描-落盘窗口内落地的写侧更新, 其 mtime
   139	    # 必然 > 基准, 下一轮触发重扫捞回 (否则该更新当天静默丢失, 无日志可查)
   140	    os.utime(payload_path, (scan_started, scan_started))
   141	
   142	    st["last_generate_date"] = today
   143	    st["payload_sha256"] = hashlib.sha256(raw.encode("utf-8")).hexdigest()
   144	    if ranked and first_gen_today:
   145	        # CARD-A3: 重扫路径不写 — tie-break 的「上次被推荐日期」是天级轮转
   146	        # 语义, 重扫换榜也补写会把第二个板标成「今天推荐过」, 污染后续排序
   147	        st["board_last_recommended"][ranked[0]["board"]] = today
   148	    save_state(st)
   149	    return payload, "new"
   150	
   151	
   152	def osascript_fallback(noti: dict) -> bool:
   153	    try:
   154	        r = subprocess.run(
   155	            ["/usr/bin/osascript", "-", noti["title"], noti["body"]],
   156	            input=APPLESCRIPT, text=True, capture_output=True, timeout=15,
   157	        )
   158	        return r.returncode == 0
   159	    except (OSError, subprocess.TimeoutExpired):
   160	        return False
   161	
   162	
   163	def main() -> int:
   164	    global VAULT
   165	    ap = argparse.ArgumentParser(description="每日复习推送编排")
   166	    ap.add_argument("--now", help="ISO 时间覆盖 (12 场景验收矩阵用)")
   167	    ap.add_argument("--vault", help="活 vault 路径 (wrapper 从 .env ACTIVE_VAULT 解析传入; 缺省回退 canvas-vault)")
   168	    args = ap.parse_args()
   169	
   170	    if args.vault:
   171	        VAULT = Path(args.vault)
   172	
   173	    now = _now(args.now)
   174	    local = now.astimezone()
   175	    today = local.date().isoformat()
   176	    st = load_state()
   177	
   178	    try:
   179	        payload, gen = ensure_payload(st, now, today)
   180	    except Exception as e:  # 生成失败 = 无保底, 唯一的非 0 退出
   181	        log_line(f"generate:FAILED err={type(e).__name__}:{str(e)[:120]}")
   182	        print(f"[runner] 生成失败: {e}", file=sys.stderr)
   183	        return 1
   184	
   185	    noti = (payload or {}).get("notification")
   186	    push, fallback = "-", "-"
   187	    if not noti:
   188	        push = "skip-empty"  # 无板可推 (全占位/空 vault): md 已如实落盘
   189	    elif st.get("last_push_accepted_date") == today:
   190	        push = "skip-done"
   191	    elif not (PUSH_WINDOW[0] <= local.time() < PUSH_WINDOW[1]):
   192	        push = "skip-window"  # RunAtLoad 早触发 / 21:00 后唤醒: 只落盘
   193	    else:
   194	        rc = send_bark.send(noti)
   195	        if rc == 0:
   196	            st["last_push_accepted_date"] = today
   197	            st["last_result"], st["last_error"] = "pushed", ""
   198	            save_state(st)
   199	            push = "accepted"
   200	        else:
   201	            push = "skip-nokey" if rc == 2 else "failed"
   202	            if rc != 2:
   203	                st["last_result"] = "generated_push_failed"
   204	                st["last_error"] = "bark-send"
   205	            # 本地兜底每日一次 (Code-Review L1 去重门); 无 key 也提醒一条
   206	            # (Code-Review H1: key 配好前不能一切静默)
   207	            if st.get("last_local_notify_date") != today:
   208	                local_noti = noti if rc != 2 else {
   209	                    "title": "📚 今日复习已生成",
   210	                    "body": noti["body"] + "（Bark 未配置，仅本地提醒）",
   211	                }
   212	                fallback = "ok" if osascript_fallback(local_noti) else "fail"
   213	                if fallback == "ok":
   214	                    st["last_local_notify_date"] = today
   215	            save_state(st)
   216	
   217	    log_line(f"generate:{gen} push:{push} fallback:{fallback}")
   218	    print(f"[runner] generate:{gen} push:{push} fallback:{fallback}")
   219	    return 0
   220	
   221	
   222	if __name__ == "__main__":
   223	    sys.exit(main())

exec
/bin/zsh -lc "nl -ba backend/tests/regression/test_daily_review_run.py | sed -n '1,270p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
     1	"""daily_review_run 当天重学卡刷新 (CARD-A3, BATCH-2026-08-24-复习闭环)。
     2	
     3	ensure_payload 缓存失效三场景锁定: 当天已生成后, 节点池比 payload 新
     4	(quiz 写侧刚更新 fsrs_due / 新增节点) 必须重扫; 无变动仍复用; 重扫后
     5	同日推送去重 (skip-done) 与 tie-break 语义 (board_last_recommended
     6	只在首次生成时写) 不被破坏。
     7	
     8	只 assert dict / 状态 / runner 状态行, 不 assert 今日复习.md 渲染文本
     9	(与 A2 渲染层解耦)。mtime 全部 os.utime 显式钉死, 不依赖墙钟顺序。
    10	"""
    11	
    12	import os
    13	import shutil
    14	import sys
    15	from datetime import datetime, timezone
    16	from pathlib import Path
    17	
    18	WT = Path(__file__).resolve().parents[3]
    19	sys.path.insert(0, str(WT / "scripts"))
    20	
    21	import daily_review_run as runner  # noqa: E402
    22	
    23	NOW = datetime(2026, 7, 30, 2, 0, tzinfo=timezone.utc)
    24	TODAY = "2026-07-30"
    25	BASE = 1_700_000_000  # 人工 mtime 基准: 只比大小, 绝对值无意义
    26	
    27	
    28	def _node(board="普通板", extra=""):
    29	    return f'---\ntype: concept\nsource_board: "[[原白板/{board}]]"\n{extra}---\n真实内容。\n'
    30	
    31	
    32	def _vault(tmp_path, nodes: dict) -> Path:
    33	    vault = tmp_path / "vault"
    34	    scripts = vault / ".claude" / "scripts"
    35	    scripts.mkdir(parents=True)
    36	    (vault / "节点").mkdir()
    37	    shutil.copy(WT / "canvas-vault" / ".claude" / "scripts" / "decay_beta.py", scripts)
    38	    for name, content in nodes.items():
    39	        (vault / "节点" / f"{name}.md").write_text(content, encoding="utf-8")
    40	    return vault
    41	
    42	
    43	def _patch_runner(monkeypatch, vault, tmp_path):
    44	    monkeypatch.setattr(runner, "VAULT", vault)
    45	    monkeypatch.setattr(runner, "STATE", tmp_path / "backups" / "daily-review.state.json")
    46	    monkeypatch.setattr(runner, "LOG", tmp_path / "backups" / "daily-review.log")
    47	
    48	
    49	def _set_mtime(path: Path, ts: float):
    50	    os.utime(path, (ts, ts))
    51	
    52	
    53	def _pin_pool_older_than_payload(vault: Path, payload_ts: float):
    54	    """把 节点/ 目录与现有节点文件全部钉到 payload 之前 (无变动基线)。"""
    55	    for p in (vault / "节点").glob("*.md"):
    56	        _set_mtime(p, payload_ts - 100)
    57	    _set_mtime(vault / "节点", payload_ts - 100)
    58	    _set_mtime(vault / "outputs" / "今日复习.json", payload_ts)
    59	
    60	
    61	# ── 场景 1: 节点变动 → 同日缓存失效, 重扫结果含该节点 ──
    62	
    63	
    64	def test_node_change_invalidates_same_day_cache(tmp_path, monkeypatch):
    65	    vault = _vault(tmp_path, {"甲": _node()})
    66	    _patch_runner(monkeypatch, vault, tmp_path)
    67	    st = runner.load_state()
    68	    payload1, gen1 = runner.ensure_payload(st, NOW, TODAY)
    69	    assert gen1 == "new"
    70	    assert {d["node"] for d in payload1["due_nodes"]} == {"甲"}
    71	
    72	    # 写侧模拟: 当天考完甲后新增重学卡乙 (新卡无 fsrs_due = 即刻到期)
    73	    (vault / "节点" / "乙.md").write_text(_node(), encoding="utf-8")
    74	    _pin_pool_older_than_payload(vault, BASE)
    75	    _set_mtime(vault / "节点" / "乙.md", BASE + 200)
    76	    _set_mtime(vault / "节点", BASE + 200)
    77	
    78	    payload2, gen2 = runner.ensure_payload(st, NOW, TODAY)
    79	    assert gen2 == "new", "节点池比 payload 新时必须重扫, 不得整日复用早晨快照"
    80	    assert "乙" in {d["node"] for d in payload2["due_nodes"]}
    81	    assert payload2["schema_version"] == 3  # 只消费 A2 的 v3, 不改 schema
    82	
    83	
    84	# ── 场景 2: 无变动 → 仍走缓存 (每小时触发不得变成每小时全量重扫) ──
    85	
    86	
    87	def test_unchanged_pool_still_cached(tmp_path, monkeypatch):
    88	    vault = _vault(tmp_path, {"甲": _node()})
    89	    _patch_runner(monkeypatch, vault, tmp_path)
    90	    st = runner.load_state()
    91	    payload1, gen1 = runner.ensure_payload(st, NOW, TODAY)
    92	    assert gen1 == "new"
    93	
    94	    _pin_pool_older_than_payload(vault, BASE)
    95	
    96	    payload2, gen2 = runner.ensure_payload(st, NOW, TODAY)
    97	    assert gen2 == "cached"
    98	    assert payload2 == payload1  # 复用的是同一份落盘 payload
    99	
   100	
   101	# ── 场景 3: 重扫后同日推送仍 skip-done (Bark 同 id 去重门不被重扫击穿) ──
   102	
   103	
   104	def test_rescan_keeps_same_day_push_skip_done(tmp_path, monkeypatch, capsys):
   105	    vault = _vault(tmp_path, {"甲": _node()})
   106	    _patch_runner(monkeypatch, vault, tmp_path)
   107	    now_arg = "2026-07-30T10:00:00+08:00"
   108	    # today 按 runner 同一变换推导 (机器时区无关): skip-done 门在窗口门之前
   109	    today = datetime.fromisoformat(now_arg).astimezone().date().isoformat()
   110	
   111	    st = runner.load_state()
   112	    _, gen1 = runner.ensure_payload(st, datetime.fromisoformat(now_arg), today)
   113	    assert gen1 == "new"
   114	    st["last_push_accepted_date"] = today  # 早晨那次推送已被服务端接受
   115	    runner.save_state(st)
   116	
   117	    (vault / "节点" / "乙.md").write_text(_node(), encoding="utf-8")
   118	    _pin_pool_older_than_payload(vault, BASE)
   119	    _set_mtime(vault / "节点" / "乙.md", BASE + 200)
   120	    _set_mtime(vault / "节点", BASE + 200)
   121	
   122	    # 哨兵而非 mock: 该路径下 send 被调用即测试失败 (同日去重门失守)
   123	    def _sentinel(noti):
   124	        raise AssertionError("同日已推送后, 重扫不得再次触发 Bark 发送")
   125	
   126	    monkeypatch.setattr(runner.send_bark, "send", _sentinel)
   127	    monkeypatch.setattr(
   128	        sys,
   129	        "argv",
   130	        ["daily_review_run.py", "--now", now_arg, "--vault", str(vault)],
   131	    )
   132	    assert runner.main() == 0
   133	    out = capsys.readouterr().out
   134	    assert "generate:new" in out, "重扫必须真的发生 (否则本场景空转)"
   135	    assert "push:skip-done" in out
   136	
   137	    st2 = runner.load_state()
   138	    assert st2["last_push_accepted_date"] == today
   139	    assert st2["last_generate_date"] == today
   140	
   141	
   142	# ── 内审 HIGH (mutation 缺口): 两条 mtime 失效通道各自单独锁定 ──
   143	# 场景 1/3 同时钉文件+目录 mtime, 任一通道被删测试仍绿; 以下两测各锁一半。
   144	
   145	
   146	def test_infile_update_alone_triggers_rescan(tmp_path, monkeypatch):
   147	    """只有文件 mtime 变、目录 mtime 钉旧 (APFS 原地更新 fsrs_due 的
   148	    真实形态 — quiz 写侧头号生产场景) 也必须失效缓存。"""
   149	    vault = _vault(tmp_path, {"甲": _node()})
   150	    _patch_runner(monkeypatch, vault, tmp_path)
   151	    st = runner.load_state()
   152	    _, gen1 = runner.ensure_payload(st, NOW, TODAY)
   153	    assert gen1 == "new"
   154	
   155	    _pin_pool_older_than_payload(vault, BASE)
   156	    _set_mtime(vault / "节点" / "甲.md", BASE + 200)  # 只 bump 文件, 目录不动
   157	
   158	    _, gen2 = runner.ensure_payload(st, NOW, TODAY)
   159	    assert gen2 == "new", "原地更新节点内容 (目录 mtime 不变) 必须触发重扫"
   160	
   161	
   162	def test_deletion_via_dir_mtime_triggers_rescan(tmp_path, monkeypatch):
   163	    """删除节点不留文件 mtime、只改目录 mtime, 也必须失效缓存,
   164	    且被删节点从投影消失 (否则被删节点整天霸占推荐)。"""
   165	    vault = _vault(tmp_path, {"甲": _node(), "乙": _node()})
   166	    _patch_runner(monkeypatch, vault, tmp_path)
   167	    st = runner.load_state()
   168	    payload1, gen1 = runner.ensure_payload(st, NOW, TODAY)
   169	    assert gen1 == "new"
   170	    assert {d["node"] for d in payload1["due_nodes"]} == {"甲", "乙"}
   171	
   172	    (vault / "节点" / "乙.md").unlink()
   173	    _pin_pool_older_than_payload(vault, BASE)
   174	    _set_mtime(vault / "节点", BASE + 200)  # 只 bump 目录 (删除的真实形态)
   175	
   176	    payload2, gen2 = runner.ensure_payload(st, NOW, TODAY)
   177	    assert gen2 == "new"
   178	    assert {d["node"] for d in payload2["due_nodes"]} == {"甲"}
   179	
   180	
   181	# ── 内审 MEDIUM (实测复现): 扫描-落盘窗口内的写侧更新不得整天丢失 ──
   182	
   183	
   184	def test_write_during_scan_window_not_lost(tmp_path, monkeypatch):
   185	    """写侧恰在扫描完成后、payload 落盘前落地一张重学卡: 该卡 mtime 早于
   186	    payload 落盘时刻, 若以落盘时刻为基准则整天 cached 丢卡。基准必须是
   187	    扫描起点。真实 build_payload 照常执行, 仅在其返回后注入竞态写入。"""
   188	    vault = _vault(tmp_path, {"甲": _node()})
   189	    _patch_runner(monkeypatch, vault, tmp_path)
   190	    st = runner.load_state()
   191	
   192	    import daily_review_pick as picker
   193	
   194	    real_build = picker.build_payload
   195	    fired = []
   196	
   197	    def _race_build(*args, **kwargs):
   198	        result = real_build(*args, **kwargs)
   199	        if not fired:  # 只在首轮注入一次
   200	            fired.append(1)
   201	            (vault / "节点" / "竞态.md").write_text(_node(), encoding="utf-8")
   202	        return result
   203	
   204	    monkeypatch.setattr(picker, "build_payload", _race_build)
   205	    payload1, gen1 = runner.ensure_payload(st, NOW, TODAY)
   206	    assert gen1 == "new"
   207	    assert "竞态" not in {d["node"] for d in payload1["due_nodes"]}  # 首轮扫描没看到它
   208	
   209	    payload2, gen2 = runner.ensure_payload(st, NOW, TODAY)
   210	    assert gen2 == "new", "竞态窗口内落地的节点必须在下一轮触发重扫, 不得整天 cached"
   211	    assert "竞态" in {d["node"] for d in payload2["due_nodes"]}
   212	
   213	
   214	# ── tie-break 守卫: 重扫路径不写 board_last_recommended (卡片风险条目) ──
   215	
   216	
   217	def test_rescan_does_not_touch_board_last_recommended(tmp_path, monkeypatch):
   218	    vault = _vault(tmp_path, {"a甲": _node(board="A板")})
   219	    _patch_runner(monkeypatch, vault, tmp_path)
   220	    st = runner.load_state()
   221	    _, gen1 = runner.ensure_payload(st, NOW, TODAY)
   222	    assert gen1 == "new"
   223	    assert st["board_last_recommended"] == {"A板": TODAY}
   224	
   225	    # 新增 B 板节点后重扫: 同分 tie-break 下 B 板 (从未被推荐) 会登顶
   226	    (vault / "节点" / "b乙.md").write_text(_node(board="B板"), encoding="utf-8")
   227	    _pin_pool_older_than_payload(vault, BASE)
   228	    _set_mtime(vault / "节点" / "b乙.md", BASE + 200)
   229	    _set_mtime(vault / "节点", BASE + 200)
   230	
   231	    payload2, gen2 = runner.ensure_payload(st, NOW, TODAY)
   232	    assert gen2 == "new"
   233	    assert payload2["top_boards"][0]["board"] == "B板"
   234	    # 核心: 重扫换榜也不得把 B板 标成「今天推荐过」— 天级轮转语义只属于首扫
   235	    assert st["board_last_recommended"] == {"A板": TODAY}

**Clarifying scan time handling and payload mtime effects**
**Identifying missing commit marker as medium finding**
**Evaluating commit marker severity and user expectations**
**Verifying commit ancestry and schema**
**Planning test execution with escalation**
exec
/bin/zsh -lc '.venv/bin/pytest tests/regression/test_daily_review_run.py tests/regression/test_daily_review_pick.py -q' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/backend
**Planning wait implementation**
 succeeded in 10012ms:
============================= test session starts ==============================
platform darwin -- Python 3.14.4, pytest-9.0.2, pluggy-1.6.0
rootdir: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/backend
configfile: pytest.ini
plugins: hypothesis-6.151.10, cov-7.1.0, xdist-3.8.0, asyncio-1.3.0, schemathesis-4.14.3, bdd-8.1.0, langsmith-0.7.24, anyio-4.13.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 22 items

tests/regression/test_daily_review_run.py .......                        [ 31%]
tests/regression/test_daily_review_pick.py ...............               [100%]

=============================== warnings summary ===============================
.venv/lib/python3.14/site-packages/google/genai/types.py:43
  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/backend/.venv/lib/python3.14/site-packages/google/genai/types.py:43: DeprecationWarning: '_UnionGenericAlias' is deprecated and slated for removal in Python 3.17
    VersionedUnionType = Union[builtin_types.UnionType, _UnionGenericAlias]

.venv/lib/python3.14/site-packages/langchain_core/_api/deprecation.py:25
  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/backend/.venv/lib/python3.14/site-packages/langchain_core/_api/deprecation.py:25: UserWarning: Core Pydantic V1 functionality isn't compatible with Python 3.14 or greater.
    from pydantic.v1.fields import FieldInfo as FieldInfoV1

.venv/lib/python3.14/site-packages/graphiti_core/driver/search_interface/search_interface.py:22
  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/backend/.venv/lib/python3.14/site-packages/graphiti_core/driver/search_interface/search_interface.py:22: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    class SearchInterface(BaseModel):

.venv/lib/python3.14/site-packages/jieba/_compat.py:18
  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/backend/.venv/lib/python3.14/site-packages/jieba/_compat.py:18: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
    import pkg_resources

<frozen importlib._bootstrap>:491
  <frozen importlib._bootstrap>:491: DeprecationWarning: builtin type SwigPyPacked has no __module__ attribute

<frozen importlib._bootstrap>:491
  <frozen importlib._bootstrap>:491: DeprecationWarning: builtin type SwigPyObject has no __module__ attribute

app/api/v1/endpoints/chat.py:803
  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/backend/app/api/v1/endpoints/chat.py:803: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    class HookEnrichRequest(BaseModel):

app/api/v1/endpoints/metadata.py:147
  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/backend/app/api/v1/endpoints/metadata.py:147: FastAPIDeprecationWarning: `example` has been deprecated, please use `examples` instead
    canvas_path: str = Query(

app/api/v1/endpoints/metadata.py:218
  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/backend/app/api/v1/endpoints/metadata.py:218: FastAPIDeprecationWarning: `example` has been deprecated, please use `examples` instead
    canvas_path: str = Query(..., description="Canvas file path", example="Math 54/离散数学.canvas"),

.venv/lib/python3.14/site-packages/pydantic/_internal/_generate_schema.py:2356
  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/backend/.venv/lib/python3.14/site-packages/pydantic/_internal/_generate_schema.py:2356: PydanticDeprecatedSince211: The `__get_pydantic_core_schema__` method of the `BaseModel` class is deprecated. If you are calling `super().__get_pydantic_core_schema__` when overriding the method on a Pydantic model, consider using `handler(source)` instead. However, note that overriding this method on models can lead to unexpected side effects. Deprecated in Pydantic V2.11 to be removed in V3.0.
    schema = annotation_get_schema(source, get_inner_schema)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================= 22 passed, 10 warnings in 0.41s ========================

**Planning adversarial reproduction using tempfile**
**Designing timed node simulation with temp environment**
**Verifying payload and node mtime setup**
**Adjusting production entrypoint calling**
**Planning isolated production tests**
**Verifying initial future due handling**
**Generating initial payload and scheduling nodes**
**Planning sandbox permission escalation for test run**
exec
/bin/zsh -lc "backend/.venv/bin/python -c '
import os, shutil, sys, tempfile
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / \"scripts\"))
import daily_review_run as runner
root = Path(tempfile.mkdtemp(prefix=\"card-a3-audit-\"))
try:
    vault = root / \"vault\"
    (vault / \"节点\").mkdir(parents=True)
    (vault / \".claude\" / \"scripts\").mkdir(parents=True)
    shutil.copy(Path.cwd() / \"canvas-vault\" / \".claude\" / \"scripts\" / \"decay_beta.py\", vault / \".claude\" / \"scripts\" / \"decay_beta.py\")
    node = vault / \"节点\" / \"甲.md\"
    def card(due):
        return \"---\\ntype: concept\\nsource_board: \\\"[[原白板/A板]]\\\"\\nfsrs_due: \" + due + \"\\n---\\n真实内容。\\n\"
    node.write_text(card(\"2026-07-31T00:00:00Z\"), encoding=\"utf-8\")
    runner.VAULT = vault
    runner.STATE = root / \"backups\" / \"state.json\"
    runner.LOG = root / \"backups\" / \"run.log\"
    st = runner.load_state()
    p1, g1 = runner.ensure_payload(st, datetime.fromisoformat(\"2026-07-30T09:05:00+08:00\"), \"2026-07-30\")
    node.write_text(card(\"2026-07-30T02:09:00Z\"), encoding=\"utf-8\")
    os.utime(vault / \"outputs\" / \"今日复习.json\", (1000, 1000))
    os.utime(node, (2000, 2000))
    os.utime(vault / \"节点\", (2000, 2000))
    p2, g2 = runner.ensure_payload(st, datetime.fromisoformat(\"2026-07-30T10:05:00+08:00\"), \"2026-07-30\")
    p3, g3 = runner.ensure_payload(st, datetime.fromisoformat(\"2026-07-30T11:05:00+08:00\"), \"2026-07-30\")
    print({\"09:05\": (g1, [x[\"node\"] for x in p1[\"due_nodes\"]]), \"10:05\": (g2, [x[\"node\"] for x in p2[\"due_nodes\"]]), \"11:05\": (g3, [x[\"node\"] for x in p3[\"due_nodes\"]]), \"due\": \"10:09 local\"})
finally:
    shutil.rmtree(root)
'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
{'09:05': ('new', []), '10:05': ('new', []), '11:05': ('cached', []), 'due': '10:09 local'}

**Classifying core goal failure as BLOCKER**
**Inspecting test timings and file modification issues**
**Identifying stale cache risk on directory deletion**
**Assessing folder rename impact on mtime handling**
**Analyzing cache retention and mtime edge cases**
**Evaluating clock skew effects on rescanning**
**Verifying date handling and state mutation**
**Identifying missing future due scenario test**
**Assessing test isolation and environment contamination**
**Assessing test environment side effects**
**Verifying timezone and payload timestamp handling**
**Identifying stale card due cache issue**
**Analyzing cache invalidation timing**
**Identifying need for time-based cache invalidation**
**Evaluating time-aware cache staleness tests**
**Testing plist parsing commands**
exec
/bin/zsh -lc 'plutil -lint scripts/launchd/com.canvas.daily-review.plist' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
scripts/launchd/com.canvas.daily-review.plist: OK

exec
/bin/zsh -lc 'plutil -p scripts/launchd/com.canvas.daily-review.plist' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
exec
/bin/zsh -lc 'grep -c "<key>Hour</key>" scripts/launchd/com.canvas.daily-review.plist' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
{
  "EnvironmentVariables" => {
    "PATH" => "/usr/bin:/bin:/usr/sbin:/sbin"
  }
  "Label" => "com.canvas.daily-review"
  "ProgramArguments" => [
    0 => "/bin/bash"
    1 => "/Users/Heishing/Library/Application Support/CanvasReview/bin/daily-review-wrapper.sh"
  ]
  "RunAtLoad" => true
  "StandardErrorPath" => "/Users/Heishing/Library/Logs/canvas-daily-review.err.log"
  "StandardOutPath" => "/Users/Heishing/Library/Logs/canvas-daily-review.log"
  "StartCalendarInterval" => [
    0 => {
      "Hour" => 9
      "Minute" => 5
    }
    1 => {
      "Hour" => 10
      "Minute" => 5
    }
    2 => {
      "Hour" => 11
      "Minute" => 5
    }
    3 => {
      "Hour" => 12
      "Minute" => 5
    }
    4 => {
      "Hour" => 13
      "Minute" => 5
    }
    5 => {
      "Hour" => 14
      "Minute" => 5
    }
    6 => {
      "Hour" => 15
      "Minute" => 5
    }
    7 => {
      "Hour" => 16
      "Minute" => 5
    }
    8 => {
      "Hour" => 17
      "Minute" => 5
    }
    9 => {
      "Hour" => 18
      "Minute" => 5
    }
    10 => {
      "Hour" => 19
      "Minute" => 5
    }
    11 => {
      "Hour" => 20
      "Minute" => 5
    }
  ]
}

 succeeded in 0ms:
12

exec
/bin/zsh -lc 'git show -s --format=fuller HEAD && git rev-list --parents -n 1 HEAD' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
commit 346448b7e7af5a49c2278e8e7e5bcd6c41c60390
Author:     oinani0721 <2272104243@qq.com>
AuthorDate: Tue Aug 25 02:37:30 2026 +0800
Commit:     oinani0721 <2272104243@qq.com>
CommitDate: Tue Aug 25 02:37:30 2026 +0800

    fix(review): same-day relearn card refresh via mtime cache invalidation
    
    BATCH-2026-08-24-复习闭环 / CARD-A3
    
    ensure_payload reused the morning payload for the whole day (sha-only gate),
    so relearn cards becoming due after the 9:05 run never entered the projection
    until the next day; launchd fired only once a day anyway.
    
    - daily_review_run: same-day cache also invalidates when the node pool's max
      mtime (files + dir, dir stat last to catch racing deletes) exceeds the
      payload mtime; payload mtime is backdated to scan start so writes landing
      in the scan-to-write window trigger the next hourly rescan instead of
      being silently lost for the day
    - rescan path never writes board_last_recommended (day-level rotation
      semantics belong to the first generation only); push dedup untouched --
      last_push_accepted_date keeps same-day pushes at one (skip-done)
    - launchd plist: StartCalendarInterval becomes a 12-slot array 9:05-20:05
      hourly, all inside the push window; repo copy only, live reinstall is a
      user-confirmed deployment step
    - tests: 7-case regression suite red->green (change->new incl. the node,
      unchanged->cached, rescan keeps push skip-done, tie-break guard, per-
      channel mtime mutation locks, scan-window race repro)
    
    Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
    Claude-Session: https://claude.ai/code/session_01DL5V5ytQdaf4cFRv7xCt3F
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
346448b7e7af5a49c2278e8e7e5bcd6c41c60390 f6a426b35d7324f73caf147018ab200770987b17

exec
/bin/zsh -lc 'git diff --exit-code worktree-feature-obsidian-hybrid-dev...HEAD -- scripts/daily_review_pick.py; git rev-parse worktree-feature-obsidian-hybrid-dev:scripts/daily_review_pick.py; git rev-parse HEAD:scripts/daily_review_pick.py' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
e8e2705b3f89d632c7600fb9cb9d00850dd1da8b
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
e8e2705b3f89d632c7600fb9cb9d00850dd1da8b

**Inspecting launchd wrapper deployment**
exec
/bin/zsh -lc "rg -n -C 6 \"com.canvas.daily-review.plist|daily-review-wrapper.sh|daily-review-push.sh|Application Support/CanvasReview\" scripts docs _bmad-output --glob '*.sh' --glob '*.py' --glob '*.md' --glob '*.plist'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
_bmad-output/审查/2026-07-29-ChatGPT终审全文-每日复习推送+本地模型栈.md-62-- E2E 只保护传输与服务器；锁屏预览是另一隐私面（iOS 通知设置决定）。
_bmad-output/审查/2026-07-29-ChatGPT终审全文-每日复习推送+本地模型栈.md-63-
_bmad-output/审查/2026-07-29-ChatGPT终审全文-每日复习推送+本地模型栈.md-64-## A6. 对本地模型栈依赖与 TCC — PASS
_bmad-output/审查/2026-07-29-ChatGPT终审全文-每日复习推送+本地模型栈.md-65-
_bmad-output/审查/2026-07-29-ChatGPT终审全文-每日复习推送+本地模型栈.md-66-- 每日推送链（Python 读 md → 排序 → 写 md/json → HTTPS Bark → osascript 兜底）零依赖 Graphiti/llama-server/reranker/embedding/Neo4j/LanceDB/Claude API。「零依赖」判断成立。
_bmad-output/审查/2026-07-29-ChatGPT终审全文-每日复习推送+本地模型栈.md-67-- 但 TCC 是整个 MVP 的 release blocker（Desktop 路径 + 已有 exit 126 实证）。未授权时：脚本进不了业务逻辑/扫不了节点/写不了输出/推送无 payload/兜底不会发生/health 只见模糊 126。
_bmad-output/审查/2026-07-29-ChatGPT终审全文-每日复习推送+本地模型栈.md:68:- 最小运维修正：launchd 入口 wrapper 放稳定非 worktree 路径（~/Library/Application Support/CanvasReview/bin/），先写启动日志 → TCC preflight（test -r vault, test -w outputs/state）→ 再调 repo 脚本；plist 绝对路径；固定绝对 Python/venv；PATH/HOME/LANG 显式；安装用 gui/$(id -u)。
_bmad-output/审查/2026-07-29-ChatGPT终审全文-每日复习推送+本地模型栈.md-69-
_bmad-output/审查/2026-07-29-ChatGPT终审全文-每日复习推送+本地模型栈.md-70-## A7. 上线一周最可能翻车点 — FIX-BEFORE-BUILD
_bmad-output/审查/2026-07-29-ChatGPT终审全文-每日复习推送+本地模型栈.md-71-
_bmad-output/审查/2026-07-29-ChatGPT终审全文-每日复习推送+本地模型栈.md-72-- P0：通知节点与实际考察节点不一致（必须传 node）；生成成功推送失败后无可复用 payload（必须持久化 json）；Bark HTTP 失败未被识别（--fail-with-body + 解析，明确接受才更新 accepted_date）；状态竞争/半写入（锁 + os.replace）。
_bmad-output/审查/2026-07-29-ChatGPT终审全文-每日复习推送+本地模型栈.md-73-- P1：节点名 shell/AppleScript 注入（osascript 走 argv heredoc，Bark payload 用 JSON serializer）；时间戳解析混乱（统一 aware datetime，未来钳 0）；launchd 找不到 python3/PyYAML（绝对 venv 路径 + kickstart 验收）；worktree 清理后任务永久失效（wrapper 隔离）；死人开关假绿（解析结构化 state：生成✅ 推送接受✅ 兜底- payload_age）。
_bmad-output/审查/2026-07-29-ChatGPT终审全文-每日复习推送+本地模型栈.md-74-- 12 场景验收矩阵：09:05 正常 / 08:00 RunAtLoad / 10:30 唤醒 / 21:01 唤醒 / 生成成功 Bark 超时 / 失败后 15:00 重跑 / Bark 成功但 state 写前被杀 / 手工+kickstart 并发 / 名含空格引号&?#emoji / TCC 未授权 / state JSON 损坏 / 全板占位符。
--
scripts/daily_review_run.py-1-#!/usr/bin/env python3
scripts/daily_review_run.py-2-"""每日复习推送编排 runner (DAILY-REVIEW-PUSH-2026-07-29, 终审 A4/A7 硬化版)。
scripts/daily_review_run.py-3-
scripts/daily_review_run.py-4-顺序铁律: md/json 先落盘(保底) → 窗口内 Bark → 失败 osascript 兜底。
scripts/daily_review_run.py:5:壳层 daily-review-push.sh 只负责 mkdir 锁 + 固定解释器; 业务全在此处
scripts/daily_review_run.py-6-(可 --now 注入时间跑 12 场景验收矩阵)。
scripts/daily_review_run.py-7-
scripts/daily_review_run.py-8-终审修正落点:
scripts/daily_review_run.py-9-  A4: 时间门 9:05 ≤ 本地时间 < 21:00 (RunAtLoad 早触发只生成不推;
scripts/daily_review_run.py-10-      唤醒补跑窗口内补推; 过窗只落盘) · state JSON 原子写 (os.replace)
scripts/daily_review_run.py-11-      · last_push_accepted_date 命名 (HTTP 成功仅证明服务端接受)
--
_bmad-output/审查/2026-07-29-ChatGPT终审吸收与代码验证.md-41-## 四、修订后的开工步骤（Phase A，替代原手册五步）
_bmad-output/审查/2026-07-29-ChatGPT终审吸收与代码验证.md-42-
_bmad-output/审查/2026-07-29-ChatGPT终审吸收与代码验证.md-43-1. `decay_beta.py` 加 `effective()`（**无 FLOOR** 同比缩放，非正参数跳过）+ `update_after_idle()`；测试补 μ 保持性/σ 单调/不改存量/未来时间戳钳 0；文案统一「证据质量半衰期 69 天」。改完 cp 部署主仓 vault（双副本）
_bmad-output/审查/2026-07-29-ChatGPT终审吸收与代码验证.md-44-2. `quiz-answer/SKILL.md` 静态 python 段：写分前读旧 `last_examined` 算 days_idle → `update_after_idle(A,B,GN,days_idle)`；aware datetime 解析（Z→+00:00）
_bmad-output/审查/2026-07-29-ChatGPT终审吸收与代码验证.md-45-3. `scripts/daily_review_pick.py`：三态兼容 + eligibility 过滤（复用「你的 1-2 句精准定义」占位符规则）+ 板级 min(pick) + tie-break（board_last_recommended → oldest last_examined → 板名）+ 输出①今日复习.md（含三态统计行 + 每板 `/start-exam-board from <板> node <top_node>`）②**今日复习.json 持久化 payload**
_bmad-output/审查/2026-07-29-ChatGPT终审吸收与代码验证.md-46-4. `scripts/send_bark.py`：读 `~/.config/canvas-review/bark.key`（700/600/umask 077）→ `POST api.day.app/push` JSON body + 每日稳定 `id: canvas-review-<date>`；key/payload 不进命令行
_bmad-output/审查/2026-07-29-ChatGPT终审吸收与代码验证.md:47:5. `daily-review-push.sh` 编排壳：mkdir 锁 + JSON state 原子写（os.replace，字段 last_generate_date / **last_push_accepted_date** / payload_sha256 / last_result）+ 时间门 `9:05 ≤ now < 21:00` 才推 + osascript 兜底走 argv heredoc（防注入）
_bmad-output/审查/2026-07-29-ChatGPT终审吸收与代码验证.md:48:6. launchd：入口 wrapper 放 `~/Library/Application Support/CanvasReview/bin/`（TCC preflight：test -r 节点 / test -w outputs / test -w state，失败写明确错误）→ 调 repo 脚本；plist 绝对路径 + 绝对 python；bootstrap `gui/$(id -u)` + print + kickstart 三连
_bmad-output/审查/2026-07-29-ChatGPT终审吸收与代码验证.md-49-7. 死人开关：memory-health.sh 解析结构化 state（生成✅/推送接受✅/兜底/payload_age），不做 grep 假绿
_bmad-output/审查/2026-07-29-ChatGPT终审吸收与代码验证.md-50-8. 验收：12 场景矩阵（正常/RunAtLoad/唤醒补跑/过窗/推送失败补跑/state 写前被杀/并发/特殊字符/TCC/损坏 state/全占位板）+ 原验收三连
_bmad-output/审查/2026-07-29-ChatGPT终审吸收与代码验证.md-51-
_bmad-output/审查/2026-07-29-ChatGPT终审吸收与代码验证.md-52-隐私形态（步骤 4 的推送内容）待用户拍板：明文具体板名（原拍板）/ 泛化内容 / 具体名+Bark 加密。
_bmad-output/审查/2026-07-29-ChatGPT终审吸收与代码验证.md-53-
_bmad-output/审查/2026-07-29-ChatGPT终审吸收与代码验证.md-54-## 五、B 侧加固 backlog（独立 session，非本次范围）
--
_bmad-output/审查/2026-07-29-Code-Review-每日复习推送.md-37-| L5 | 负数 mastery 静默降级 + BOM 不容忍 | `_fm_num` 容负号（进 corrupt 分支）+ frontmatter 容 BOM | 新测试 ×2 |
_bmad-output/审查/2026-07-29-Code-Review-每日复习推送.md-38-| L6 | --now 裸时间两入口语义差 8 小时 | picker 与 runner 统一「裸时间=本地时区」 | 代码对齐 |
_bmad-output/审查/2026-07-29-Code-Review-每日复习推送.md-39-| L7 | 手工把 a/b 改 0 → 评分段裸 traceback | 写分前 `max(A,1e-4)` 容错钳制 | 部署双副本 |
_bmad-output/审查/2026-07-29-Code-Review-每日复习推送.md-40-
_bmad-output/审查/2026-07-29-Code-Review-每日复习推送.md-41-## Backlog（转入吸收文档 §五 加固清单）
_bmad-output/审查/2026-07-29-Code-Review-每日复习推送.md-42-
_bmad-output/审查/2026-07-29-Code-Review-每日复习推送.md:43:- **H2**: memory-health.sh 的 launchd 宿主仍指向 worktree 且 TCC 拦截（上次退出 126）——需同款迁移到 `~/Library/Application Support/CanvasReview/bin/` wrapper + TCC 预检。监控者自身无监控，是既有基建债，非本 MVP 范围。
_bmad-output/审查/2026-07-29-Code-Review-每日复习推送.md-44-- **M3 后半**: 4 个未归板节点（考察-Fundamentals-2026-07-16 / cs-61b-csm / csm-tutoring-unit-credit / my-recursion-notes）的 source_board 回填（从原白板 ## Concepts 反查）。
_bmad-output/审查/2026-07-29-Code-Review-每日复习推送.md-45-- **M6 后半**: runner 状态机单测化（当前由 12 场景运行时矩阵覆盖）。
_bmad-output/审查/2026-07-29-Code-Review-每日复习推送.md-46-
_bmad-output/审查/2026-07-29-Code-Review-每日复习推送.md-47-## 有理由保留（对审查意见的 pushback）
_bmad-output/审查/2026-07-29-Code-Review-每日复习推送.md-48-
_bmad-output/审查/2026-07-29-Code-Review-每日复习推送.md-49-- **L2（board_last_recommended 在生成时记账而非推送成功时）**：刻意保留。无 key / 纯 md 用户也应获得轮转推荐——md 落盘即「已推荐」的产品语义；若改成推送成功才记账，无 key 用户的 tie-break 永不轮转。
--
_bmad-output/审查/codex-review-CARD-A3.md-160-84-- **并行**: 与 A1/B1/E0 并行安全；**与 A3 在 daily_review_pick.py + 回归测试文件上有真实冲突 → A2 先行（schema owner），A3 串行其后只消费不改 schema**。
_bmad-output/审查/codex-review-CARD-A3.md-161-85-
_bmad-output/审查/codex-review-CARD-A3.md-162-86:### CARD-A3: 当天重学卡刷新（串行于 A2 之后）
_bmad-output/审查/codex-review-CARD-A3.md-163-87-
_bmad-output/审查/codex-review-CARD-A3.md-164-88-- **确认状态**: CONFIRMED（launchd plist 全天仅 9:05 一档；`daily_review_run.py:85-112 ensure_payload` 同日 sha 匹配即复用，现网日志实证 `generate:cached push:skip-done`；quiz-answer 写侧全链 grep 零失效触发点；fsrs 6.3.1 实测 learning_steps=(60s,600s) 全落当天）
_bmad-output/审查/codex-review-CARD-A3.md-165-89-- **方案**: ①ensure_payload 缓存条件放宽——当天已生成后，若 `节点/*.md` 最大 mtime > payload mtime 则重扫（push 去重由 last_push_accepted_date 天然保证）；②plist StartCalendarInterval 改数组 9:05–21:00 每小时一档（重扫必须周期性——只做写侧一次性触发的话，due=now+1min 的卡在重生成瞬间仍未到期，缺陷只是位移）。
_bmad-output/审查/codex-review-CARD-A3.md:166:90-- **改动文件**: `scripts/daily_review_run.py`、`scripts/launchd/com.canvas.daily-review.plist`、新增 `backend/tests/regression/test_daily_review_run.py`；部署侧 `~/Library/LaunchAgents/` 重装（**破坏性操作，动手前单独向用户确认**）
_bmad-output/审查/codex-review-CARD-A3.md-167---
_bmad-output/审查/codex-review-CARD-A3.md-168-183-
_bmad-output/审查/codex-review-CARD-A3.md-169-184-**A3（车道 1 第二棒，A2 合并进 worktree-feature-obsidian-hybrid-dev 后才创建 worktree 开工）：**
_bmad-output/审查/codex-review-CARD-A3.md-170-185-
_bmad-output/审查/codex-review-CARD-A3.md-171-186-```
_bmad-output/审查/codex-review-CARD-A3.md-172-187:/goal 完成 CARD-A3：当天重学卡刷新。必读卡片档案：/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-08-24-第一批小goal卡-复习闭环.md 的 CARD-A3 节。前置检查：git merge-base --is-ancestor 确认 A2 的 commit 已在本分支，schema_version==3 已存在，否则 STOP 并报告。完成条件（AND）：
_bmad-output/审查/codex-review-CARD-A3.md-173-188-(1) scripts/daily_review_run.py 的 ensure_payload：当天已生成后，若 节点/*.md 最大 mtime > payload mtime 则重扫；重扫路径不更新 board_last_recommended（防污染 tie-break）；只消费 A2 的 schema v3，不改 schema。
_bmad-output/审查/codex-review-CARD-A3.md:174:189-(2) scripts/launchd/com.canvas.daily-review.plist：StartCalendarInterval 改数组，9:05 起至 21:00 每小时一档；plutil -lint 通过。只改仓库副本——~/Library/LaunchAgents/ 的重装属破坏性部署，写入验收单"待用户确认"一节，你不执行。
_bmad-output/审查/codex-review-CARD-A3.md-175-190-(3) 新增 backend/tests/regression/test_daily_review_run.py 三场景（节点变动→"new"且含该节点 / 无变动→"cached" / 重扫后 push 仍 skip-done），先红后绿；只 assert dict 不 assert md 文本。
_bmad-output/审查/codex-review-CARD-A3.md:176:191-(4) 裁判命令：cd backend && .venv/bin/pytest tests/regression/test_daily_review_run.py tests/regression/test_daily_review_pick.py -q 全绿；grep -c "<key>Hour</key>" scripts/launchd/com.canvas.daily-review.plist ≥2。
_bmad-output/审查/codex-review-CARD-A3.md-177-192:(5) Codex 交叉审查（同 A1 模式，换成 CARD-A3，重点审：缓存失效条件、push 去重、tie-break 语义）存 _bmad-output/审查/codex-review-CARD-A3.md，处理完 BLOCKER/HIGH。
_bmad-output/审查/codex-review-CARD-A3.md-178-193:(6) 小白验收单 ship（含 launchd 重装待确认节）。(7) git commit 含 "BATCH-2026-08-24-复习闭环 / CARD-A3"；不 push。
_bmad-output/审查/codex-review-CARD-A3.md-179-194-硬边界：不改 daily_review_pick.py 的 due 判定与 schema（A2 已定）；不碰 fsrs_bridge.py；不执行 launchctl。
_bmad-output/审查/codex-review-CARD-A3.md-180-195-```
_bmad-output/审查/codex-review-CARD-A3.md-181-196-
_bmad-output/审查/codex-review-CARD-A3.md-182-197-### 3.4 每张卡的生命周期（统一）
--
_bmad-output/审查/codex-review-CARD-A3.md-200-?? "canvas-vault/outputs/\344\273\212\346\227\245\345\244\215\344\271\240.md"
_bmad-output/审查/codex-review-CARD-A3.md-201-
_bmad-output/审查/codex-review-CARD-A3.md-202- succeeded in 0ms:
_bmad-output/审查/codex-review-CARD-A3.md-203-git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
_bmad-output/审查/codex-review-CARD-A3.md-204- backend/tests/regression/test_daily_review_run.py | 235 ++++++++++++++++++++++
_bmad-output/审查/codex-review-CARD-A3.md-205- scripts/daily_review_run.py                       |  45 ++++-
_bmad-output/审查/codex-review-CARD-A3.md:206: scripts/launchd/com.canvas.daily-review.plist     |  83 +++++++-
_bmad-output/审查/codex-review-CARD-A3.md-207- 3 files changed, 353 insertions(+), 10 deletions(-)
_bmad-output/审查/codex-review-CARD-A3.md-208-git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
_bmad-output/审查/codex-review-CARD-A3.md-209-A	backend/tests/regression/test_daily_review_run.py
_bmad-output/审查/codex-review-CARD-A3.md-210-M	scripts/daily_review_run.py
_bmad-output/审查/codex-review-CARD-A3.md:211:M	scripts/launchd/com.canvas.daily-review.plist
_bmad-output/审查/codex-review-CARD-A3.md-212-
_bmad-output/审查/codex-review-CARD-A3.md-213-exec
_bmad-output/审查/codex-review-CARD-A3.md-214-/bin/zsh -lc 'git merge-base worktree-feature-obsidian-hybrid-dev HEAD && git rev-parse HEAD && git rev-parse worktree-feature-obsidian-hybrid-dev && git log --oneline --decorate --no-merges worktree-feature-obsidian-hybrid-dev..HEAD' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
_bmad-output/审查/codex-review-CARD-A3.md-215- succeeded in 0ms:
_bmad-output/审查/codex-review-CARD-A3.md-216-git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
_bmad-output/审查/codex-review-CARD-A3.md-217-f6a426b35d7324f73caf147018ab200770987b17
--
_bmad-output/审查/codex-review-CARD-A3.md-229-/bin/zsh -lc "nl -ba \"/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-08-24-第一批小goal卡-复习闭环.md\" | sed -n '86,105p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
_bmad-output/审查/codex-review-CARD-A3.md-230- succeeded in 0ms:
_bmad-output/审查/codex-review-CARD-A3.md-231-    86	### CARD-A3: 当天重学卡刷新（串行于 A2 之后）
_bmad-output/审查/codex-review-CARD-A3.md-232-    87	
_bmad-output/审查/codex-review-CARD-A3.md-233-    88	- **确认状态**: CONFIRMED（launchd plist 全天仅 9:05 一档；`daily_review_run.py:85-112 ensure_payload` 同日 sha 匹配即复用，现网日志实证 `generate:cached push:skip-done`；quiz-answer 写侧全链 grep 零失效触发点；fsrs 6.3.1 实测 learning_steps=(60s,600s) 全落当天）
_bmad-output/审查/codex-review-CARD-A3.md-234-    89	- **方案**: ①ensure_payload 缓存条件放宽——当天已生成后，若 `节点/*.md` 最大 mtime > payload mtime 则重扫（push 去重由 last_push_accepted_date 天然保证）；②plist StartCalendarInterval 改数组 9:05–21:00 每小时一档（重扫必须周期性——只做写侧一次性触发的话，due=now+1min 的卡在重生成瞬间仍未到期，缺陷只是位移）。
_bmad-output/审查/codex-review-CARD-A3.md:235:    90	- **改动文件**: `scripts/daily_review_run.py`、`scripts/launchd/com.canvas.daily-review.plist`、新增 `backend/tests/regression/test_daily_review_run.py`；部署侧 `~/Library/LaunchAgents/` 重装（**破坏性操作，动手前单独向用户确认**）
_bmad-output/审查/codex-review-CARD-A3.md-236-    91	- **完成判据（机械）**: 三场景测试（节点变动后 ensure_payload 返回 "new" 且含该节点 / 无变动仍 "cached" / 重扫后 push 仍 skip-done）+ `plutil -lint` 通过 + plist Hour 键 ≥2 档。测试只 assert dict 不 assert md 文本（与 A2 解耦）。
_bmad-output/审查/codex-review-CARD-A3.md-237-    92	- **风险**: board_last_recommended 只在首次生成时更新（重扫路径不写，防污染 tie-break 语义）；每小时触发放大 wrapper 双副本 preflight 的暴露频率（是暴露不是引入）；Bark 通知同 id 覆盖靠 skip-done 门守住（场景 3 锁死）。
_bmad-output/审查/codex-review-CARD-A3.md-238-    93	- **并行**: 依赖 A2 的 schema v3 先落地；与 A1/B1/E0 零交集。
_bmad-output/审查/codex-review-CARD-A3.md-239-    94	
_bmad-output/审查/codex-review-CARD-A3.md-240-    95	### CARD-B1: CI Dependency Audit 修复（方案 A 已预验证）
_bmad-output/审查/codex-review-CARD-A3.md-241-    96	
--
_bmad-output/审查/codex-review-CARD-A3.md-247-   102	- **并行**: 与所有卡零交集，完全并行。push 动作放白天由用户知情时执行，夜间车道不 push。
_bmad-output/审查/codex-review-CARD-A3.md-248-   103	
_bmad-output/审查/codex-review-CARD-A3.md-249-   104	### CARD-E0: 夜间车道准备（环境盘点已完成大半）
_bmad-output/审查/codex-review-CARD-A3.md-250-   105	
_bmad-output/审查/codex-review-CARD-A3.md-251-
_bmad-output/审查/codex-review-CARD-A3.md-252-exec
_bmad-output/审查/codex-review-CARD-A3.md:253:/bin/zsh -lc 'git diff --find-renames --find-copies --unified=100 worktree-feature-obsidian-hybrid-dev...HEAD -- scripts/daily_review_run.py scripts/launchd/com.canvas.daily-review.plist' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
_bmad-output/审查/codex-review-CARD-A3.md-254- succeeded in 0ms:
_bmad-output/审查/codex-review-CARD-A3.md-255-git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
_bmad-output/审查/codex-review-CARD-A3.md-256-diff --git a/scripts/daily_review_run.py b/scripts/daily_review_run.py
_bmad-output/审查/codex-review-CARD-A3.md-257-index 4dc943cc..86365f81 100755
_bmad-output/审查/codex-review-CARD-A3.md-258---- a/scripts/daily_review_run.py
_bmad-output/审查/codex-review-CARD-A3.md-259-+++ b/scripts/daily_review_run.py
_bmad-output/审查/codex-review-CARD-A3.md-260-@@ -1,186 +1,223 @@
_bmad-output/审查/codex-review-CARD-A3.md-261- #!/usr/bin/env python3
_bmad-output/审查/codex-review-CARD-A3.md-262- """每日复习推送编排 runner (DAILY-REVIEW-PUSH-2026-07-29, 终审 A4/A7 硬化版)。
_bmad-output/审查/codex-review-CARD-A3.md-263- 
_bmad-output/审查/codex-review-CARD-A3.md-264- 顺序铁律: md/json 先落盘(保底) → 窗口内 Bark → 失败 osascript 兜底。
_bmad-output/审查/codex-review-CARD-A3.md:265: 壳层 daily-review-push.sh 只负责 mkdir 锁 + 固定解释器; 业务全在此处
_bmad-output/审查/codex-review-CARD-A3.md-266- (可 --now 注入时间跑 12 场景验收矩阵)。
_bmad-output/审查/codex-review-CARD-A3.md-267- 
_bmad-output/审查/codex-review-CARD-A3.md-268- 终审修正落点:
_bmad-output/审查/codex-review-CARD-A3.md-269-   A4: 时间门 9:05 ≤ 本地时间 < 21:00 (RunAtLoad 早触发只生成不推;
_bmad-output/审查/codex-review-CARD-A3.md-270-       唤醒补跑窗口内补推; 过窗只落盘) · state JSON 原子写 (os.replace)
_bmad-output/审查/codex-review-CARD-A3.md-271-       · last_push_accepted_date 命名 (HTTP 成功仅证明服务端接受)
--
_bmad-output/审查/codex-review-CARD-A3.md-482-     print(f"[runner] generate:{gen} push:{push} fallback:{fallback}")
_bmad-output/审查/codex-review-CARD-A3.md-483-     return 0
_bmad-output/审查/codex-review-CARD-A3.md-484- 
_bmad-output/审查/codex-review-CARD-A3.md-485- 
_bmad-output/审查/codex-review-CARD-A3.md-486- if __name__ == "__main__":
_bmad-output/审查/codex-review-CARD-A3.md-487-     sys.exit(main())
_bmad-output/审查/codex-review-CARD-A3.md:488:diff --git a/scripts/launchd/com.canvas.daily-review.plist b/scripts/launchd/com.canvas.daily-review.plist
_bmad-output/审查/codex-review-CARD-A3.md-489-index 75913deb..c34fe0b0 100644
_bmad-output/审查/codex-review-CARD-A3.md:490:--- a/scripts/launchd/com.canvas.daily-review.plist
_bmad-output/审查/codex-review-CARD-A3.md:491:+++ b/scripts/launchd/com.canvas.daily-review.plist
_bmad-output/审查/codex-review-CARD-A3.md-492-@@ -1,31 +1,102 @@
_bmad-output/审查/codex-review-CARD-A3.md-493- <?xml version="1.0" encoding="UTF-8"?>
_bmad-output/审查/codex-review-CARD-A3.md-494- <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
_bmad-output/审查/codex-review-CARD-A3.md-495- <plist version="1.0">
_bmad-output/审查/codex-review-CARD-A3.md-496- <dict>
_bmad-output/审查/codex-review-CARD-A3.md-497- 	<key>EnvironmentVariables</key>
--
_bmad-output/审查/codex-review-CARD-A3.md-501- 	</dict>
_bmad-output/审查/codex-review-CARD-A3.md-502- 	<key>Label</key>
_bmad-output/审查/codex-review-CARD-A3.md-503- 	<string>com.canvas.daily-review</string>
_bmad-output/审查/codex-review-CARD-A3.md-504- 	<key>ProgramArguments</key>
_bmad-output/审查/codex-review-CARD-A3.md-505- 	<array>
_bmad-output/审查/codex-review-CARD-A3.md-506- 		<string>/bin/bash</string>
_bmad-output/审查/codex-review-CARD-A3.md:507: 		<string>/Users/Heishing/Library/Application Support/CanvasReview/bin/daily-review-wrapper.sh</string>
_bmad-output/审查/codex-review-CARD-A3.md-508- 	</array>
_bmad-output/审查/codex-review-CARD-A3.md-509- 	<key>RunAtLoad</key>
_bmad-output/审查/codex-review-CARD-A3.md-510- 	<true/>
_bmad-output/审查/codex-review-CARD-A3.md-511- 	<key>StandardErrorPath</key>
_bmad-output/审查/codex-review-CARD-A3.md-512- 	<string>/Users/Heishing/Library/Logs/canvas-daily-review.err.log</string>
_bmad-output/审查/codex-review-CARD-A3.md-513- 	<key>StandardOutPath</key>
--
_bmad-output/审查/codex-review-CARD-A3.md-1365-exec
_bmad-output/审查/codex-review-CARD-A3.md-1366-/bin/zsh -lc "rg -n \"def build_payload|def scan|fsrs_due|board_last_recommended|notification|bark|id\\\"|last_push_accepted_date|daily_review_run|daily-review\" scripts canvas-vault/.claude/scripts backend/app frontend/src --glob '*.py' --glob '*.sh' --glob '*.ts' --glob '*.tsx'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
_bmad-output/审查/codex-review-CARD-A3.md-1367- succeeded in 0ms:
_bmad-output/审查/codex-review-CARD-A3.md-1368-backend/app/dependencies.py:1133:    "resolve_subject_id",  # Story 1.9: per-request subject resolution
_bmad-output/审查/codex-review-CARD-A3.md-1369-canvas-vault/.claude/scripts/sync_board_concepts.py:143:    __slots__ = ("node_id", "role", "derived_from", "mastery", "attempts", "is_stub")
_bmad-output/审查/codex-review-CARD-A3.md-1370-canvas-vault/.claude/scripts/sync_board_concepts.py:206:def scan_members(vault: Path) -> tuple[dict[str, list[Member]], list[str]]:
_bmad-output/审查/codex-review-CARD-A3.md:1371:scripts/daily_review_run.py:5:壳层 daily-review-push.sh 只负责 mkdir 锁 + 固定解释器; 业务全在此处
_bmad-output/审查/codex-review-CARD-A3.md-1372-scripts/daily_review_run.py:11:      · last_push_accepted_date 命名 (HTTP 成功仅证明服务端接受)
_bmad-output/审查/codex-review-CARD-A3.md-1373-scripts/daily_review_run.py:29:import send_bark  # noqa: E402
_bmad-output/审查/codex-review-CARD-A3.md-1374-scripts/daily_review_run.py:35:STATE = REPO / "backups" / "daily-review.state.json"
_bmad-output/审查/codex-review-CARD-A3.md-1375-scripts/daily_review_run.py:36:LOG = REPO / "backups" / "daily-review.log"
_bmad-output/审查/codex-review-CARD-A3.md-1376-scripts/daily_review_run.py:42:    "    display notification (item 2 of argv) with title (item 1 of argv)\n"
_bmad-output/审查/codex-review-CARD-A3.md-1377-scripts/daily_review_run.py:56:        return {"schema_version": 1, "board_last_recommended": {}}
--
_bmad-output/审查/codex-review-CARD-A3.md-1727-backend/app/services/context_enrichment_service.py:60:    node_id = node.get("id", "unknown")
_bmad-output/审查/codex-review-CARD-A3.md-1728-backend/app/services/context_enrichment_service.py:580:                    "id": node.get("id"),
_bmad-output/审查/codex-review-CARD-A3.md-1729-backend/app/services/context_enrichment_service.py:646:        nodes = {n.get("id"): n for n in canvas_data.get("nodes", [])}
_bmad-output/审查/codex-review-CARD-A3.md-1730-backend/app/services/context_enrichment_service.py:893:                adj.node.get("id") for adj in adjacent if adj.node.get("id")
_bmad-output/审查/codex-review-CARD-A3.md-1731-backend/app/services/wikilink_parser.py:137:                    invalid_reason="empty_block_id",
_bmad-output/审查/codex-review-CARD-A3.md-1732-backend/app/models/agent_routing_models.py:75:            "node_id": self.node_id,
_bmad-output/审查/codex-review-CARD-A3.md:1733:scripts/launchd/daily-review-wrapper.sh:12:BOOTLOG="$HOME/Library/Logs/canvas-daily-review.boot.log"
_bmad-output/审查/codex-review-CARD-A3.md:1734:scripts/launchd/daily-review-wrapper.sh:37:head -c 1 "$WT/scripts/daily-review-push.sh" >/dev/null 2>&1 \
_bmad-output/审查/codex-review-CARD-A3.md:1735:scripts/launchd/daily-review-wrapper.sh:47:exec "$WT/scripts/daily-review-push.sh" --vault "$VAULT" "$@"
_bmad-output/审查/codex-review-CARD-A3.md-1736-backend/app/services/health_monitor.py:224:                    threshold="All parameters valid",
_bmad-output/审查/codex-review-CARD-A3.md-1737-backend/app/services/health_monitor.py:231:                value="all valid",
_bmad-output/审查/codex-review-CARD-A3.md-1738-backend/app/services/health_monitor.py:232:                threshold="All parameters valid",
_bmad-output/审查/codex-review-CARD-A3.md-1739-backend/app/services/health_monitor.py:239:                threshold="All parameters valid",
_bmad-output/审查/codex-review-CARD-A3.md-1740-backend/app/api/v1/endpoints/errors.py:125:    candidate_id: str = Field(..., description="error_candidates[].id")
_bmad-output/审查/codex-review-CARD-A3.md-1741-backend/app/api/v1/endpoints/errors.py:139:    candidate_id: str = Field(..., description="error_candidates[].id")
--
_bmad-output/审查/codex-review-CARD-A3.md-2080-backend/app/services/canvas_service.py:952:        new_edge = {"id": edge_id, **edge_data}
_bmad-output/审查/codex-review-CARD-A3.md-2081-backend/app/services/canvas_service.py:964:            edge_id=new_edge["id"],
_bmad-output/审查/codex-review-CARD-A3.md-2082-backend/app/services/canvas_service.py:978:                    edge_id=new_edge["id"],
_bmad-output/审查/codex-review-CARD-A3.md-2083-backend/app/services/canvas_service.py:1012:            e for e in canvas_data.get("edges", []) if e.get("id") != edge_id
_bmad-output/审查/codex-review-CARD-A3.md-2084-backend/app/services/canvas_service.py:1105:                    if node.get("id") == node_id:
_bmad-output/审查/codex-review-CARD-A3.md-2085-backend/app/models/common.py:83:                    "details": {"field": "node_id", "reason": "Invalid format"},
_bmad-output/审查/codex-review-CARD-A3.md:2086:scripts/daily-review-push.sh:4:# 固定解释器调 runner。业务逻辑全在 daily_review_run.py (--now 可测)。
_bmad-output/审查/codex-review-CARD-A3.md:2087:scripts/daily-review-push.sh:9:LOCK="$REPO/backups/.daily-review.lock"
_bmad-output/审查/codex-review-CARD-A3.md:2088:scripts/daily-review-push.sh:31:"$PY" "$WT/scripts/daily_review_run.py" "$@"
_bmad-output/审查/codex-review-CARD-A3.md-2089-backend/app/services/exam_service.py:454:                id=data.get("uuid", ""),
_bmad-output/审查/codex-review-CARD-A3.md-2090-backend/app/services/exam_service.py:455:                source_canvas_id=data.get("source_board_id", ""),
_bmad-output/审查/codex-review-CARD-A3.md-2091-backend/app/services/exam_service.py:461:                target_node_id=data.get("target_node_id") or None,
_bmad-output/审查/codex-review-CARD-A3.md-2092-backend/app/services/exam_service.py:462:                current_node_id=data.get("current_node_id") or None,
_bmad-output/审查/codex-review-CARD-A3.md-2093-backend/app/models/memory_schemas.py:72:                "user_id": "user-123",
_bmad-output/审查/codex-review-CARD-A3.md-2094-backend/app/models/memory_schemas.py:74:                "node_id": "node-abc123",
--
_bmad-output/审查/codex-review-CARD-A3.md-2334-scripts/shard-architecture.py-61-    shards = []
_bmad-output/审查/codex-review-CARD-A3.md-2335---
_bmad-output/审查/codex-review-CARD-A3.md-2336-scripts/daily_review_run.py-1-#!/usr/bin/env python3
_bmad-output/审查/codex-review-CARD-A3.md-2337-scripts/daily_review_run.py-2-"""每日复习推送编排 runner (DAILY-REVIEW-PUSH-2026-07-29, 终审 A4/A7 硬化版)。
_bmad-output/审查/codex-review-CARD-A3.md-2338-scripts/daily_review_run.py-3-
_bmad-output/审查/codex-review-CARD-A3.md-2339-scripts/daily_review_run.py-4-顺序铁律: md/json 先落盘(保底) → 窗口内 Bark → 失败 osascript 兜底。
_bmad-output/审查/codex-review-CARD-A3.md:2340:scripts/daily_review_run.py:5:壳层 daily-review-push.sh 只负责 mkdir 锁 + 固定解释器; 业务全在此处
_bmad-output/审查/codex-review-CARD-A3.md-2341-scripts/daily_review_run.py-6-(可 --now 注入时间跑 12 场景验收矩阵)。
_bmad-output/审查/codex-review-CARD-A3.md-2342-scripts/daily_review_run.py-7-
_bmad-output/审查/codex-review-CARD-A3.md-2343-scripts/daily_review_run.py-8-终审修正落点:
_bmad-output/审查/codex-review-CARD-A3.md-2344-scripts/daily_review_run.py-9-  A4: 时间门 9:05 ≤ 本地时间 < 21:00 (RunAtLoad 早触发只生成不推;
_bmad-output/审查/codex-review-CARD-A3.md-2345-scripts/daily_review_run.py-10-      唤醒补跑窗口内补推; 过窗只落盘) · state JSON 原子写 (os.replace)
_bmad-output/审查/codex-review-CARD-A3.md-2346---
--
_bmad-output/审查/codex-review-CARD-A3.md-2650-scripts/validate_agent_yaml.py-120-
_bmad-output/审查/codex-review-CARD-A3.md-2651-scripts/validate_agent_yaml.py-121-    return warnings
_bmad-output/审查/codex-review-CARD-A3.md-2652-scripts/validate_agent_yaml.py-122-
_bmad-output/审查/codex-review-CARD-A3.md-2653-scripts/validate_agent_yaml.py-123-def validate_agent_file(file_path: Path) -> Dict:
_bmad-output/审查/codex-review-CARD-A3.md-2654-scripts/validate_agent_yaml.py-124-    """验证Agent文件"""
_bmad-output/审查/codex-review-CARD-A3.md-2655---
_bmad-output/审查/codex-review-CARD-A3.md:2656:scripts/daily-review-push.sh-1-#!/usr/bin/env bash
_bmad-output/审查/codex-review-CARD-A3.md:2657:scripts/daily-review-push.sh-2-# 每日复习推送 — 编排壳 (DAILY-REVIEW-PUSH-2026-07-29)。
_bmad-output/审查/codex-review-CARD-A3.md:2658:scripts/daily-review-push.sh:3:# 只做两件事: mkdir 互斥锁 (终审 A7: 手工/kickstart/定时可能重叠) +
_bmad-output/审查/codex-review-CARD-A3.md:2659:scripts/daily-review-push.sh:4:# 固定解释器调 runner。业务逻辑全在 daily_review_run.py (--now 可测)。
_bmad-output/审查/codex-review-CARD-A3.md:2660:scripts/daily-review-push.sh-5-set -uo pipefail
_bmad-output/审查/codex-review-CARD-A3.md:2661:scripts/daily-review-push.sh-6-
_bmad-output/审查/codex-review-CARD-A3.md:2662:scripts/daily-review-push.sh-7-REPO="/Users/Heishing/Desktop/canvas/canvas-learning-system"
_bmad-output/审查/codex-review-CARD-A3.md:2663:scripts/daily-review-push.sh-8-WT="$REPO/.claude/worktrees/feature-obsidian-hybrid-dev"
_bmad-output/审查/codex-review-CARD-A3.md:2664:scripts/daily-review-push.sh:9:LOCK="$REPO/backups/.daily-review.lock"
_bmad-output/审查/codex-review-CARD-A3.md:2665:scripts/daily-review-push.sh-10-
_bmad-output/审查/codex-review-CARD-A3.md:2666:scripts/daily-review-push.sh:11:mkdir -p "$REPO/backups"
_bmad-output/审查/codex-review-CARD-A3.md:2667:scripts/daily-review-push.sh:12:if ! mkdir "$LOCK" 2>/dev/null; then
_bmad-output/审查/codex-review-CARD-A3.md:2668:scripts/daily-review-push.sh-13-    # 陈旧锁恢复 (Code-Review M5): 断电/SIGKILL 会留下锁目录, 不处理则
_bmad-output/审查/codex-review-CARD-A3.md:2669:scripts/daily-review-push.sh-14-    # 之后每天 "skip: already running" 且 exit 0 永久静默。mtime 超 6h
_bmad-output/审查/codex-review-CARD-A3.md:2670:scripts/daily-review-push.sh-15-    # 视为死锁夺回 (单次运行实测秒级, 6h 余量极大)。
_bmad-output/审查/codex-review-CARD-A3.md:2671:scripts/daily-review-push.sh-16-    if [ -n "$(find "$LOCK" -maxdepth 0 -mmin +360 2>/dev/null)" ]; then
_bmad-output/审查/codex-review-CARD-A3.md:2672:scripts/daily-review-push.sh:17:        echo "stale lock (>6h), reclaiming" >&2
_bmad-output/审查/codex-review-CARD-A3.md:2673:scripts/daily-review-push.sh-18-        rmdir "$LOCK" 2>/dev/null || true
_bmad-output/审查/codex-review-CARD-A3.md:2674:scripts/daily-review-push.sh-19-    fi
_bmad-output/审查/codex-review-CARD-A3.md:2675:scripts/daily-review-push.sh:20:    if ! mkdir "$LOCK" 2>/dev/null; then
_bmad-output/审查/codex-review-CARD-A3.md:2676:scripts/daily-review-push.sh-21-        echo "skip: already running" >&2
_bmad-output/审查/codex-review-CARD-A3.md:2677:scripts/daily-review-push.sh-22-        exit 0
_bmad-output/审查/codex-review-CARD-A3.md:2678:scripts/daily-review-push.sh-23-    fi
_bmad-output/审查/codex-review-CARD-A3.md:2679:scripts/daily-review-push.sh-24-fi
_bmad-output/审查/codex-review-CARD-A3.md:2680:scripts/daily-review-push.sh-25-# 不用 exec — exec 会替换进程使 trap 失效, 锁永不释放
_bmad-output/审查/codex-review-CARD-A3.md:2681:scripts/daily-review-push.sh-26-trap 'rmdir "$LOCK" 2>/dev/null || true' EXIT INT TERM
_bmad-output/审查/codex-review-CARD-A3.md:2682:scripts/daily-review-push.sh-27-
_bmad-output/审查/codex-review-CARD-A3.md:2683:scripts/daily-review-push.sh-28-PY="$WT/backend/.venv/bin/python"
_bmad-output/审查/codex-review-CARD-A3.md:2684:scripts/daily-review-push.sh-29-[ -x "$PY" ] || PY="/usr/bin/python3"   # venv 缺失兜底 (runner 仅 stdlib)
_bmad-output/审查/codex-review-CARD-A3.md:2685:scripts/daily-review-push.sh-30-
_bmad-output/审查/codex-review-CARD-A3.md:2686:scripts/daily-review-push.sh:31:"$PY" "$WT/scripts/daily_review_run.py" "$@"
_bmad-output/审查/codex-review-CARD-A3.md-2687---
_bmad-output/审查/codex-review-CARD-A3.md-2688-scripts/daemon/status_watcher.py-52-        self.debounce_seconds = debounce_seconds
_bmad-output/审查/codex-review-CARD-A3.md-2689-scripts/daemon/status_watcher.py-53-
_bmad-output/审查/codex-review-CARD-A3.md-2690-scripts/daemon/status_watcher.py-54-        # Track state
_bmad-output/审查/codex-review-CARD-A3.md-2691-scripts/daemon/status_watcher.py-55-        self._last_event_time: Dict[str, float] = {}
_bmad-output/审查/codex-review-CARD-A3.md-2692-scripts/daemon/status_watcher.py-56-        self._already_triggered: Set[str] = set()
--
_bmad-output/审查/codex-review-CARD-A3.md-2816-scripts/install-vault.sh-149-fi
_bmad-output/审查/codex-review-CARD-A3.md-2817-scripts/install-vault.sh-150-
_bmad-output/审查/codex-review-CARD-A3.md-2818-scripts/install-vault.sh-151-echo ""
_bmad-output/审查/codex-review-CARD-A3.md-2819-scripts/install-vault.sh-152-echo "═══ 结果: $PASS 项通过 / $FAIL 项失败 ═══"
_bmad-output/审查/codex-review-CARD-A3.md-2820-scripts/install-vault.sh-153-echo "📋 后续步骤:"
_bmad-output/审查/codex-review-CARD-A3.md-2821---
_bmad-output/审查/codex-review-CARD-A3.md:2822:scripts/launchd/daily-review-wrapper.sh-1-#!/usr/bin/env bash
_bmad-output/审查/codex-review-CARD-A3.md:2823:scripts/launchd/daily-review-wrapper.sh:2:# 每日复习推送 launchd 入口 wrapper (DAILY-REVIEW-PUSH-2026-07-29, 终审 A6)。
_bmad-output/审查/codex-review-CARD-A3.md:2824:scripts/launchd/daily-review-wrapper.sh:3:# 安装位置: ~/Library/Application Support/CanvasReview/bin/ — launchd 只指向
_bmad-output/审查/codex-review-CARD-A3.md:2825:scripts/launchd/daily-review-wrapper.sh-4-# 这个稳定路径, worktree 移动/清理不再让任务永久失效 (memory-health 6 天
_bmad-output/审查/codex-review-CARD-A3.md:2826:scripts/launchd/daily-review-wrapper.sh-5-# 停摆教训的结构性修复)。本文件是 git 追踪的源码副本, 改动后需重新 cp 安装。
_bmad-output/审查/codex-review-CARD-A3.md:2827:scripts/launchd/daily-review-wrapper.sh-6-set -uo pipefail
_bmad-output/审查/codex-review-CARD-A3.md:2828:scripts/launchd/daily-review-wrapper.sh-7-
_bmad-output/审查/codex-review-CARD-A3.md:2829:scripts/launchd/daily-review-wrapper.sh-8-export PATH="/usr/bin:/bin:/usr/sbin:/sbin"
_bmad-output/审查/codex-review-CARD-A3.md:2830:scripts/launchd/daily-review-wrapper.sh-9-export HOME="${HOME:-/Users/Heishing}"
_bmad-output/审查/codex-review-CARD-A3.md:2831:scripts/launchd/daily-review-wrapper.sh-10-export LANG="zh_CN.UTF-8"
_bmad-output/审查/codex-review-CARD-A3.md:2832:scripts/launchd/daily-review-wrapper.sh-11-
_bmad-output/审查/codex-review-CARD-A3.md:2833:scripts/launchd/daily-review-wrapper.sh-12-BOOTLOG="$HOME/Library/Logs/canvas-daily-review.boot.log"
_bmad-output/审查/codex-review-CARD-A3.md:2834:scripts/launchd/daily-review-wrapper.sh:13:# 第一行探针: 连 ~/Library 都写不了 = launchd 环境彻底异常
_bmad-output/审查/codex-review-CARD-A3.md:2835:scripts/launchd/daily-review-wrapper.sh-14-echo "[$(date '+%F %T')] wrapper start" >> "$BOOTLOG"
_bmad-output/审查/codex-review-CARD-A3.md:2836:scripts/launchd/daily-review-wrapper.sh-15-
_bmad-output/审查/codex-review-CARD-A3.md:2837:scripts/launchd/daily-review-wrapper.sh-16-REPO="/Users/Heishing/Desktop/canvas/canvas-learning-system"
_bmad-output/审查/codex-review-CARD-A3.md:2838:scripts/launchd/daily-review-wrapper.sh-17-WT="$REPO/.claude/worktrees/feature-obsidian-hybrid-dev"
_bmad-output/审查/codex-review-CARD-A3.md:2839:scripts/launchd/daily-review-wrapper.sh-18-
_bmad-output/审查/codex-review-CARD-A3.md:2840:scripts/launchd/daily-review-wrapper.sh-19-fail() { echo "[$(date '+%F %T')] PREFLIGHT-FAIL: $1" >> "$BOOTLOG"; exit 78; }
_bmad-output/审查/codex-review-CARD-A3.md:2841:scripts/launchd/daily-review-wrapper.sh-20-
_bmad-output/审查/codex-review-CARD-A3.md:2842:scripts/launchd/daily-review-wrapper.sh:21:# VAULT-SYNC (2026-08-02 用户拍板): 推送 vault 与 .env ACTIVE_VAULT 同源 —
_bmad-output/审查/codex-review-CARD-A3.md:2843:scripts/launchd/daily-review-wrapper.sh-22-# P0-3 确立「vault 由部署期 .env 固定」后, 推送链不再独立写死, 换 vault
_bmad-output/审查/codex-review-CARD-A3.md:2844:scripts/launchd/daily-review-wrapper.sh-23-# 只改 .env 一处, 后端/skills/推送全部跟走。解析失败回退 canvas-vault
_bmad-output/审查/codex-review-CARD-A3.md:2845:scripts/launchd/daily-review-wrapper.sh-24-# (与旧行为一致); VAULTS_ROOT 取 .env 宿主侧值, 缺省回退主仓根。
_bmad-output/审查/codex-review-CARD-A3.md:2846:scripts/launchd/daily-review-wrapper.sh-25-ENV_FILE="$WT/.env"
_bmad-output/审查/codex-review-CARD-A3.md:2847:scripts/launchd/daily-review-wrapper.sh:26:ACTIVE_VAULT=$(grep -E '^ACTIVE_VAULT=' "$ENV_FILE" 2>/dev/null | tail -1 | cut -d= -f2- | tr -d '"' | tr -d "'")
_bmad-output/审查/codex-review-CARD-A3.md:2848:scripts/launchd/daily-review-wrapper.sh-27-VAULTS_ROOT_HOST=$(grep -E '^VAULTS_ROOT=' "$ENV_FILE" 2>/dev/null | tail -1 | cut -d= -f2- | tr -d '"' | tr -d "'")
_bmad-output/审查/codex-review-CARD-A3.md:2849:scripts/launchd/daily-review-wrapper.sh:28:VAULT="${VAULTS_ROOT_HOST:-$REPO}/${ACTIVE_VAULT:-canvas-vault}"
_bmad-output/审查/codex-review-CARD-A3.md:2850:scripts/launchd/daily-review-wrapper.sh:29:echo "[$(date '+%F %T')] vault=$VAULT (ACTIVE_VAULT=${ACTIVE_VAULT:-<fallback>})" >> "$BOOTLOG"
_bmad-output/审查/codex-review-CARD-A3.md:2851:scripts/launchd/daily-review-wrapper.sh-30-
_bmad-output/审查/codex-review-CARD-A3.md:2852:scripts/launchd/daily-review-wrapper.sh-31-# TCC preflight: Desktop 路径受 TCC 管辖。⚠ 必须真实读取 — [ -r ] 走 access()
_bmad-output/审查/codex-review-CARD-A3.md:2853:scripts/launchd/daily-review-wrapper.sh-32-# 在 TCC 域内会假通过 (2026-07-29 实测: 测试全过但 exec 仍 Operation not
_bmad-output/审查/codex-review-CARD-A3.md:2854:scripts/launchd/daily-review-wrapper.sh-33-# permitted), 只有 ls/head 这类真 I/O 才探得出来
_bmad-output/审查/codex-review-CARD-A3.md:2855:scripts/launchd/daily-review-wrapper.sh-34-ls "$VAULT/节点" >/dev/null 2>&1 \
_bmad-output/审查/codex-review-CARD-A3.md:2856:scripts/launchd/daily-review-wrapper.sh-35-    || fail "vault_not_readable_tcc — 系统设置→隐私与安全性→完全磁盘访问→给 /bin/bash 开启"
_bmad-output/审查/codex-review-CARD-A3.md:2857:scripts/launchd/daily-review-wrapper.sh:36:mkdir -p "$REPO/backups" 2>/dev/null || fail "backups_not_writable_tcc"
_bmad-output/审查/codex-review-CARD-A3.md:2858:scripts/launchd/daily-review-wrapper.sh-37-head -c 1 "$WT/scripts/daily-review-push.sh" >/dev/null 2>&1 \
_bmad-output/审查/codex-review-CARD-A3.md:2859:scripts/launchd/daily-review-wrapper.sh-38-    || fail "repo_script_unreadable_tcc_or_missing — TCC 未授权或 worktree 被清理"
_bmad-output/审查/codex-review-CARD-A3.md:2860:scripts/launchd/daily-review-wrapper.sh-39-# 双副本一致性 (Code-Review M4 + FSRS-V2 H1): runner/quiz-answer 用的是
_bmad-output/审查/codex-review-CARD-A3.md:2861:scripts/launchd/daily-review-wrapper.sh-40-# 活 vault 里的副本, worktree 改了忘 cp 会造成静默行为漂移
_bmad-output/审查/codex-review-CARD-A3.md:2862:scripts/launchd/daily-review-wrapper.sh-41-for f in decay_beta.py fsrs_bridge.py; do
_bmad-output/审查/codex-review-CARD-A3.md-2863---
_bmad-output/审查/codex-review-CARD-A3.md-2864-scripts/diff-openapi.py-640-    report = generate_diff_report(diff, report_spec1_path, spec2_path)
_bmad-output/审查/codex-review-CARD-A3.md-2865-scripts/diff-openapi.py-641-
_bmad-output/审查/codex-review-CARD-A3.md-2866-scripts/diff-openapi.py-642-    # 输出报告
_bmad-output/审查/codex-review-CARD-A3.md-2867-scripts/diff-openapi.py-643-    if args.output:
_bmad-output/审查/codex-review-CARD-A3.md-2868-scripts/diff-openapi.py-644-        output_path = Path(args.output)
--
_bmad-output/审查/codex-review-CARD-A3.md-5579-   114	if __name__ == "__main__":
_bmad-output/审查/codex-review-CARD-A3.md-5580-   115	    sys.exit(main())
_bmad-output/审查/codex-review-CARD-A3.md-5581-
_bmad-output/审查/codex-review-CARD-A3.md-5582-exec
_bmad-output/审查/codex-review-CARD-A3.md-5583-/bin/zsh -lc "rg -l \"daily_review_run.py\" scripts --glob '*.sh' --glob '*.plist' | sort" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
_bmad-output/审查/codex-review-CARD-A3.md-5584- succeeded in 0ms:
_bmad-output/审查/codex-review-CARD-A3.md:5585:scripts/daily-review-push.sh
_bmad-output/审查/codex-review-CARD-A3.md-5586-
_bmad-output/审查/codex-review-CARD-A3.md-5587-exec
_bmad-output/审查/codex-review-CARD-A3.md-5588-/bin/zsh -lc "rg -n \"fsrs_due\" canvas-vault/.claude backend/app .claude --glob '*.py' --glob '*.md' --glob '*.js' --glob '*.ts' | head -n 240" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
_bmad-output/审查/codex-review-CARD-A3.md-5589- succeeded in 0ms:
_bmad-output/审查/codex-review-CARD-A3.md-5590-canvas-vault/.claude/skills/quiz-answer/SKILL.md:252:# 复习, 产出 fsrs_due 等 6 字段供推送链读侧判「今天谁到期」。桥内部自动
_bmad-output/审查/codex-review-CARD-A3.md-5591-canvas-vault/.claude/skills/quiz-answer/SKILL.md:281:    fm = re.sub(r'^(fsrs_due|fsrs_state|fsrs_step|fsrs_stability|fsrs_difficulty|fsrs_last_review):.*\r?\n?', '', fm, flags=re.M)
--
_bmad-output/审查/codex-review-CARD-A3.md-5843-   312	cal = (p.get("callout") or "").strip()
_bmad-output/审查/codex-review-CARD-A3.md-5844-   313	if cal and cal not in body:
_bmad-output/审查/codex-review-CARD-A3.md-5845-   314	    body = body.rstrip() + "\n\n" + cal + "\n"
_bmad-output/审查/codex-review-CARD-A3.md-5846-   315	
_bmad-output/审查/codex-review-CARD-A3.md-5847-
_bmad-output/审查/codex-review-CARD-A3.md-5848-exec
_bmad-output/审查/codex-review-CARD-A3.md:5849:/bin/zsh -lc "nl -ba scripts/daily-review-push.sh | sed -n '1,260p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
_bmad-output/审查/codex-review-CARD-A3.md-5850- succeeded in 0ms:
_bmad-output/审查/codex-review-CARD-A3.md-5851-     1	#!/usr/bin/env bash
_bmad-output/审查/codex-review-CARD-A3.md-5852-     2	# 每日复习推送 — 编排壳 (DAILY-REVIEW-PUSH-2026-07-29)。
_bmad-output/审查/codex-review-CARD-A3.md-5853-     3	# 只做两件事: mkdir 互斥锁 (终审 A7: 手工/kickstart/定时可能重叠) +
_bmad-output/审查/codex-review-CARD-A3.md-5854-     4	# 固定解释器调 runner。业务逻辑全在 daily_review_run.py (--now 可测)。
_bmad-output/审查/codex-review-CARD-A3.md-5855-     5	set -uo pipefail
--
_bmad-output/审查/codex-review-CARD-A3.md-5981- succeeded in 0ms:
_bmad-output/审查/codex-review-CARD-A3.md-5982-git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
_bmad-output/审查/codex-review-CARD-A3.md-5983-git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
_bmad-output/审查/codex-review-CARD-A3.md-5984-346448b7 (HEAD -> card/a3-relearn) fix(review): same-day relearn card refresh via mtime cache invalidation
_bmad-output/审查/codex-review-CARD-A3.md-5985- backend/tests/regression/test_daily_review_run.py | 235 ++++++++++++++++++++++
_bmad-output/审查/codex-review-CARD-A3.md-5986- scripts/daily_review_run.py                       |  45 ++++-
_bmad-output/审查/codex-review-CARD-A3.md:5987: scripts/launchd/com.canvas.daily-review.plist     |  83 +++++++-
_bmad-output/审查/codex-review-CARD-A3.md-5988- 3 files changed, 353 insertions(+), 10 deletions(-)
_bmad-output/审查/codex-review-CARD-A3.md-5989-
_bmad-output/审查/codex-review-CARD-A3.md-5990-**Analyzing board update edge case**
_bmad-output/审查/codex-review-CARD-A3.md-5991-**Evaluating push notification update logic**
_bmad-output/审查/codex-review-CARD-A3.md-5992-**Verifying crash handling and scheduling**
_bmad-output/审查/codex-review-CARD-A3.md-5993-**Clarifying time window and caching logic**
--
_bmad-output/审查/codex-review-CARD-A3.md-6699-**Identifying stale card due cache issue**
_bmad-output/审查/codex-review-CARD-A3.md-6700-**Analyzing cache invalidation timing**
_bmad-output/审查/codex-review-CARD-A3.md-6701-**Identifying need for time-based cache invalidation**
_bmad-output/审查/codex-review-CARD-A3.md-6702-**Evaluating time-aware cache staleness tests**
_bmad-output/审查/codex-review-CARD-A3.md-6703-**Testing plist parsing commands**
_bmad-output/审查/codex-review-CARD-A3.md-6704-exec
_bmad-output/审查/codex-review-CARD-A3.md:6705:/bin/zsh -lc 'plutil -lint scripts/launchd/com.canvas.daily-review.plist' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
_bmad-output/审查/codex-review-CARD-A3.md-6706- succeeded in 0ms:
_bmad-output/审查/codex-review-CARD-A3.md:6707:scripts/launchd/com.canvas.daily-review.plist: OK
_bmad-output/审查/codex-review-CARD-A3.md-6708-
_bmad-output/审查/codex-review-CARD-A3.md-6709-exec
_bmad-output/审查/codex-review-CARD-A3.md:6710:/bin/zsh -lc 'plutil -p scripts/launchd/com.canvas.daily-review.plist' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
_bmad-output/审查/codex-review-CARD-A3.md-6711-exec
_bmad-output/审查/codex-review-CARD-A3.md:6712:/bin/zsh -lc 'grep -c "<key>Hour</key>" scripts/launchd/com.canvas.daily-review.plist' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
_bmad-output/审查/codex-review-CARD-A3.md-6713- succeeded in 0ms:
_bmad-output/审查/codex-review-CARD-A3.md-6714-{
_bmad-output/审查/codex-review-CARD-A3.md-6715-  "EnvironmentVariables" => {
_bmad-output/审查/codex-review-CARD-A3.md-6716-    "PATH" => "/usr/bin:/bin:/usr/sbin:/sbin"
_bmad-output/审查/codex-review-CARD-A3.md-6717-  }
_bmad-output/审查/codex-review-CARD-A3.md-6718-  "Label" => "com.canvas.daily-review"
_bmad-output/审查/codex-review-CARD-A3.md-6719-  "ProgramArguments" => [
_bmad-output/审查/codex-review-CARD-A3.md-6720-    0 => "/bin/bash"
_bmad-output/审查/codex-review-CARD-A3.md:6721:    1 => "/Users/Heishing/Library/Application Support/CanvasReview/bin/daily-review-wrapper.sh"
_bmad-output/审查/codex-review-CARD-A3.md-6722-  ]
_bmad-output/审查/codex-review-CARD-A3.md-6723-  "RunAtLoad" => true
_bmad-output/审查/codex-review-CARD-A3.md-6724-  "StandardErrorPath" => "/Users/Heishing/Library/Logs/canvas-daily-review.err.log"
_bmad-output/审查/codex-review-CARD-A3.md-6725-  "StandardOutPath" => "/Users/Heishing/Library/Logs/canvas-daily-review.log"
_bmad-output/审查/codex-review-CARD-A3.md-6726-  "StartCalendarInterval" => [
_bmad-output/审查/codex-review-CARD-A3.md-6727-    0 => {
--
_bmad-output/审查/codex-review-CARD-A2.md-257-    81	- **并行**: 与 A1/B1/E0 并行安全；**与 A3 在 daily_review_pick.py + 回归测试文件上有真实冲突 → A2 先行（schema owner），A3 串行其后只消费不改 schema**。
_bmad-output/审查/codex-review-CARD-A2.md-258-    82	
_bmad-output/审查/codex-review-CARD-A2.md-259-    83	### CARD-A3: 当天重学卡刷新（串行于 A2 之后）
_bmad-output/审查/codex-review-CARD-A2.md-260-    84	
_bmad-output/审查/codex-review-CARD-A2.md-261-    85	- **确认状态**: CONFIRMED（launchd plist 全天仅 9:05 一档；`daily_review_run.py:85-112 ensure_payload` 同日 sha 匹配即复用，现网日志实证 `generate:cached push:skip-done`；quiz-answer 写侧全链 grep 零失效触发点；fsrs 6.3.1 实测 learning_steps=(60s,600s) 全落当天）
_bmad-output/审查/codex-review-CARD-A2.md-262-    86	- **方案**: ①ensure_payload 缓存条件放宽——当天已生成后，若 `节点/*.md` 最大 mtime > payload mtime 则重扫（push 去重由 last_push_accepted_date 天然保证）；②plist StartCalendarInterval 改数组 9:05–21:00 每小时一档（重扫必须周期性——只做写侧一次性触发的话，due=now+1min 的卡在重生成瞬间仍未到期，缺陷只是位移）。
_bmad-output/审查/codex-review-CARD-A2.md:263:    87	- **改动文件**: `scripts/daily_review_run.py`、`scripts/launchd/com.canvas.daily-review.plist`、新增 `backend/tests/regression/test_daily_review_run.py`；部署侧 `~/Library/LaunchAgents/` 重装（**破坏性操作，动手前单独向用户确认**）
_bmad-output/审查/codex-review-CARD-A2.md-264-    88	- **完成判据（机械）**: 三场景测试（节点变动后 ensure_payload 返回 "new" 且含该节点 / 无变动仍 "cached" / 重扫后 push 仍 skip-done）+ `plutil -lint` 通过 + plist Hour 键 ≥2 档。测试只 assert dict 不 assert md 文本（与 A2 解耦）。
_bmad-output/审查/codex-review-CARD-A2.md-265-    89	- **风险**: board_last_recommended 只在首次生成时更新（重扫路径不写，防污染 tie-break 语义）；每小时触发放大 wrapper 双副本 preflight 的暴露频率（是暴露不是引入）；Bark 通知同 id 覆盖靠 skip-done 门守住（场景 3 锁死）。
_bmad-output/审查/codex-review-CARD-A2.md-266-    90	- **并行**: 依赖 A2 的 schema v3 先落地；与 A1/B1/E0 零交集。
_bmad-output/审查/codex-review-CARD-A2.md-267-    91	
_bmad-output/审查/codex-review-CARD-A2.md-268-    92	### CARD-B1: CI Dependency Audit 修复（方案 A 已预验证）
_bmad-output/审查/codex-review-CARD-A2.md-269-   150	(3) 修正 tests/unit/test_fsrs_state_query.py:202-210 里靠本 bug 维持绿灯的 found=False 断言。
--
_bmad-output/审查/codex-review-CARD-A2.md-1483-/bin/zsh -lc "nl -ba scripts/daily_review_run.py | sed -n '1,230p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
_bmad-output/审查/codex-review-CARD-A2.md-1484- succeeded in 0ms:
_bmad-output/审查/codex-review-CARD-A2.md-1485-     1	#!/usr/bin/env python3
_bmad-output/审查/codex-review-CARD-A2.md-1486-     2	"""每日复习推送编排 runner (DAILY-REVIEW-PUSH-2026-07-29, 终审 A4/A7 硬化版)。
_bmad-output/审查/codex-review-CARD-A2.md-1487-     3	
_bmad-output/审查/codex-review-CARD-A2.md-1488-     4	顺序铁律: md/json 先落盘(保底) → 窗口内 Bark → 失败 osascript 兜底。
_bmad-output/审查/codex-review-CARD-A2.md:1489:     5	壳层 daily-review-push.sh 只负责 mkdir 锁 + 固定解释器; 业务全在此处
_bmad-output/审查/codex-review-CARD-A2.md-1490-     6	(可 --now 注入时间跑 12 场景验收矩阵)。
_bmad-output/审查/codex-review-CARD-A2.md-1491-     7	
_bmad-output/审查/codex-review-CARD-A2.md-1492-     8	终审修正落点:
_bmad-output/审查/codex-review-CARD-A2.md-1493-     9	  A4: 时间门 9:05 ≤ 本地时间 < 21:00 (RunAtLoad 早触发只生成不推;
_bmad-output/审查/codex-review-CARD-A2.md-1494-    10	      唤醒补跑窗口内补推; 过窗只落盘) · state JSON 原子写 (os.replace)
_bmad-output/审查/codex-review-CARD-A2.md-1495-    11	      · last_push_accepted_date 命名 (HTTP 成功仅证明服务端接受)
--
_bmad-output/审查/codex-review-CARD-A2.md-2887-/bin/zsh -lc "nl -ba scripts/daily_review_run.py | sed -n '1,210p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
_bmad-output/审查/codex-review-CARD-A2.md-2888- succeeded in 0ms:
_bmad-output/审查/codex-review-CARD-A2.md-2889-     1	#!/usr/bin/env python3
_bmad-output/审查/codex-review-CARD-A2.md-2890-     2	"""每日复习推送编排 runner (DAILY-REVIEW-PUSH-2026-07-29, 终审 A4/A7 硬化版)。
_bmad-output/审查/codex-review-CARD-A2.md-2891-     3	
_bmad-output/审查/codex-review-CARD-A2.md-2892-     4	顺序铁律: md/json 先落盘(保底) → 窗口内 Bark → 失败 osascript 兜底。
_bmad-output/审查/codex-review-CARD-A2.md:2893:     5	壳层 daily-review-push.sh 只负责 mkdir 锁 + 固定解释器; 业务全在此处
_bmad-output/审查/codex-review-CARD-A2.md-2894-     6	(可 --now 注入时间跑 12 场景验收矩阵)。
_bmad-output/审查/codex-review-CARD-A2.md-2895-     7	
_bmad-output/审查/codex-review-CARD-A2.md-2896-     8	终审修正落点:
_bmad-output/审查/codex-review-CARD-A2.md-2897-     9	  A4: 时间门 9:05 ≤ 本地时间 < 21:00 (RunAtLoad 早触发只生成不推;
_bmad-output/审查/codex-review-CARD-A2.md-2898-    10	      唤醒补跑窗口内补推; 过窗只落盘) · state JSON 原子写 (os.replace)
_bmad-output/审查/codex-review-CARD-A2.md-2899-    11	      · last_push_accepted_date 命名 (HTTP 成功仅证明服务端接受)
--
_bmad-output/审查/codex-review-CARD-A2.md-3565-scripts/daily_review_pick.py:210:    prefix = "📚 今日复习 · "
_bmad-output/审查/codex-review-CARD-A2.md-3566-scripts/daily_review_pick.py:278:        f"# 今日复习 · {payload['date']}",
_bmad-output/审查/codex-review-CARD-A2.md-3567-scripts/daily_review_pick.py:332:    ap.add_argument("--write", action="store_true", help="写 outputs/今日复习.md+json")
_bmad-output/审查/codex-review-CARD-A2.md-3568-scripts/daily_review_pick.py:336:    # 裸时间当本地时区, 与 daily_review_run.py 语义统一 (Code-Review L6)
_bmad-output/审查/codex-review-CARD-A2.md-3569-scripts/daily_review_pick.py:354:        atomic_write(out / "今日复习.md", render_md(payload, ranked))
_bmad-output/审查/codex-review-CARD-A2.md-3570-scripts/daily_review_pick.py:355:        atomic_write(out / "今日复习.json",
_bmad-output/审查/codex-review-CARD-A2.md:3571:scripts/daily-review-push.sh:4:# 固定解释器调 runner。业务逻辑全在 daily_review_run.py (--now 可测)。
_bmad-output/审查/codex-review-CARD-A2.md:3572:scripts/daily-review-push.sh:31:"$PY" "$WT/scripts/daily_review_run.py" "$@"
_bmad-output/审查/codex-review-CARD-A2.md-3573-scripts/send_bark.py:104:    ap.add_argument("--payload", required=True, help="今日复习.json 路径")
_bmad-output/审查/codex-review-CARD-A2.md-3574-backend/tests/regression/test_daily_review_pick.py:200:    """推送链被动性守卫: v2 既有字段一个不少、语义不变 (daily_review_run /
_bmad-output/审查/codex-review-CARD-A2.md-3575-backend/tests/regression/test_daily_review_pick.py:201:    send_bark 只读 notification, 但全字段名保留是加性承诺的下界)。"""
_bmad-output/审查/codex-review-CARD-A2.md-3576-
_bmad-output/审查/codex-review-CARD-A2.md-3577-**Planning runner runtime tests without secrets**
_bmad-output/审查/codex-review-CARD-A2.md-3578-**Evaluating temp fixture creation constraints**
--
_bmad-output/审查/codex-review-CARD-A2.md-4367-**Assessing writer damage severity**
_bmad-output/审查/codex-review-CARD-A2.md-4368-**Evaluating test coverage completeness**
_bmad-output/审查/codex-review-CARD-A2.md-4369-**Listing medium test coverage gaps**
_bmad-output/审查/codex-review-CARD-A2.md-4370-**Identifying partial test coverage and missing push chain test**
_bmad-output/审查/codex-review-CARD-A2.md-4371-**Planning targeted test sufficiency check**
_bmad-output/审查/codex-review-CARD-A2.md-4372-exec
_bmad-output/审查/codex-review-CARD-A2.md:4373:/bin/zsh -lc 'git diff --exit-code worktree-feature-obsidian-hybrid-dev -- scripts/daily_review_run.py scripts/send_bark.py scripts/daily-review-push.sh' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
_bmad-output/审查/codex-review-CARD-A2.md-4374- succeeded in 0ms:
_bmad-output/审查/codex-review-CARD-A2.md-4375-git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
_bmad-output/审查/codex-review-CARD-A2.md-4376-
_bmad-output/审查/codex-review-CARD-A2.md-4377-exec
_bmad-output/审查/codex-review-CARD-A2.md-4378-/bin/zsh -lc 'git diff --numstat worktree-feature-obsidian-hybrid-dev -- backend/tests/regression/test_daily_review_pick.py canvas-vault/Dashboard.md scripts/daily_review_pick.py' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
_bmad-output/审查/codex-review-CARD-A2.md-4379- succeeded in 0ms:
--
_bmad-output/审查/daily-review-push-and-local-llm_pack_2026-07-29.md-121-- 扫 `canvas-vault/节点/*.md` frontmatter（**三态兼容**：mastery_a/b+last_examined 新字段 → effective+pick；仅旧 mastery_score → from_legacy；无字段 → 先验。实测 18 节点中新字段仅 Fundamentals 1 个、旧字段 10 个）
_bmad-output/审查/daily-review-push-and-local-llm_pack_2026-07-29.md-122-- days_idle = 今天 − last_examined（无字段视为从未考 → 先验高 σ）
_bmad-output/审查/daily-review-push-and-local-llm_pack_2026-07-29.md-123-- 按 source_board 分组 → `board_priority = min(effective_pick)` + due count（pick<0.15 的节点数）
_bmad-output/审查/daily-review-push-and-local-llm_pack_2026-07-29.md-124-- 输出①：`canvas-vault/outputs/今日复习.md`（排序表 + 每板一行可粘贴的 `/start-exam-board from <板名>`）
_bmad-output/审查/daily-review-push-and-local-llm_pack_2026-07-29.md-125-- 输出②：stdout 单行 JSON `{top_boards:[{board,top_node,pending,idle_days}]}`
_bmad-output/审查/daily-review-push-and-local-llm_pack_2026-07-29.md-126-
_bmad-output/审查/daily-review-push-and-local-llm_pack_2026-07-29.md:127:### 3. scripts/daily-review-push.sh（编排壳，照抄 memory-health.sh 风格）
_bmad-output/审查/daily-review-push-and-local-llm_pack_2026-07-29.md-128-- 幂等守卫：`backups/daily-review.state` 记 `last_generate_date` / `last_push_date` **分开**（推送失败当天补跑只补推送）
_bmad-output/审查/daily-review-push-and-local-llm_pack_2026-07-29.md-129-- 顺序铁律：md 先落盘 → Bark（`curl -m 10 --retry 2 "$PUSH_URL/📚 今日复习 · <top1板名>/<正文>?group=canvas复习"`，push.env 缺失记「跳过(未配置)」不算错）→ 失败 `osascript -e 'display notification ...'` 兜底
_bmad-output/审查/daily-review-push-and-local-llm_pack_2026-07-29.md-130-- 21:00 后过窗跳推；单行日志 `backups/daily-review.log`（只记 provider+HTTP 码，**永不打印 PUSH_URL**）
_bmad-output/审查/daily-review-push-and-local-llm_pack_2026-07-29.md-131-
_bmad-output/审查/daily-review-push-and-local-llm_pack_2026-07-29.md-132-### 4. launchd 接线（⛔ 上轮血泪教训）
_bmad-output/审查/daily-review-push-and-local-llm_pack_2026-07-29.md:133:- `~/Library/LaunchAgents/com.canvas.daily-review.plist` 照抄 memory-health 模式（StartCalendarInterval 9:05 + RunAtLoad + StandardErrorPath）
_bmad-output/审查/daily-review-push-and-local-llm_pack_2026-07-29.md-134-- **必须**：`launchctl bootstrap gui/501 <plist>` 然后 `launchctl print gui/501/com.canvas.daily-review` 验证 + `kickstart` 实跑一次看退出码——**plist 写了不 bootstrap = 任务永远不存在**（memory-health 停摆 6 天的根因）
_bmad-output/审查/daily-review-push-and-local-llm_pack_2026-07-29.md-135-- 若 kickstart 报 126 = 用户 TCC 未授权，回到前置动作 2
_bmad-output/审查/daily-review-push-and-local-llm_pack_2026-07-29.md-136-
_bmad-output/审查/daily-review-push-and-local-llm_pack_2026-07-29.md-137-### 5. 死人开关 + 验收
_bmad-output/审查/daily-review-push-and-local-llm_pack_2026-07-29.md-138-- memory-health.sh 加字段：`复习推送:<今日跑否>`（grep daily-review.log 当日行）
_bmad-output/审查/daily-review-push-and-local-llm_pack_2026-07-29.md-139-- **验收三连**：① 手工把某节点 last_examined 改为 30 天前 → 跑 pick 脚本该板升榜首 ② kickstart → iPhone 收到 Bark 横幅 ③ 考完一场 `/quiz-answer` 再跑 → 推荐轮转
--
_bmad-output/审查/2026-07-31-ChatGPT第二轮对抗审查吸收与代码验证.md-147-
_bmad-output/审查/2026-07-31-ChatGPT第二轮对抗审查吸收与代码验证.md-148-## 五点五、P0 落地进度（2026-07-31 当日执行）
_bmad-output/审查/2026-07-31-ChatGPT第二轮对抗审查吸收与代码验证.md-149-
_bmad-output/审查/2026-07-31-ChatGPT第二轮对抗审查吸收与代码验证.md-150-| 项 | 状态 | 证据 |
_bmad-output/审查/2026-07-31-ChatGPT第二轮对抗审查吸收与代码验证.md-151-|----|------|------|
_bmad-output/审查/2026-07-31-ChatGPT第二轮对抗审查吸收与代码验证.md-152-| P0-0 端口收口 | ✅ commit `7f63f6a3` | 四端口绑 127.0.0.1，LAN 实测拒绝 |
_bmad-output/审查/2026-07-31-ChatGPT第二轮对抗审查吸收与代码验证.md:153:| P0-1 抢救备份 | ✅（Claude 部分） | 07-22/07-23 dump 已存档 `~/Library/Application Support/CanvasReview/backups-archive/`；FDA 授权待用户 |
_bmad-output/审查/2026-07-31-ChatGPT第二轮对抗审查吸收与代码验证.md-154-| P0-2 MCP 写侧隔离 | ✅ commit `7f63f6a3` | 19→5 只读，14 隔离 410+遥测，31 契约；独立审查 APPROVE-WITH-FIXES 全修 |
_bmad-output/审查/2026-07-31-ChatGPT第二轮对抗审查吸收与代码验证.md-155-| P0-3 去 global vault switch | ✅ commit `b29669b4` | /vault/switch 410、插件 CTA/下拉下架、enrich-hook cwd 推导、tips 必填；审查抓出逃生指引 CANVAS_BASE_PATH 变量名错误（正确旋钮是 ACTIVE_VAULT）已修 |
_bmad-output/审查/2026-07-31-ChatGPT第二轮对抗审查吸收与代码验证.md-156-| P0-4 并发隔离测试 | ✅（并入 P0-3） | 突变向量清零后原测试无标的；`test_switch_does_not_mutate_settings` 锁定核心不变量 |
_bmad-output/审查/2026-07-31-ChatGPT第二轮对抗审查吸收与代码验证.md-157-| P0-5 Tier B 物理删除 | ⏳ 观察期 | 410 遥测挂账中，3-7 个真实 session 零命中后删（追加：infra_tools.switch_vault 死函数、插件 activeVaultName 死字段、test_story_2_5_chatgpt_round2_p0 语义失真） |
_bmad-output/审查/2026-07-31-ChatGPT第二轮对抗审查吸收与代码验证.md-158-| **P0-6 恢复演练** | ✅ **2026-07-31 实跑成功** | 07-23 dump → 隔离容器 neo4j:5.26 `neo4j-admin database load`（114 files/260.7MiB/4s）→ 还原 **118 节点/214 关系**（生产现值 129/229，8 天增量合理）；Entity/LearningConcept/Episodic/CanvasNode 标签体系与 `vault__canvas_vault*` 物理 group_id 全部完整。**结论：现有 dump 可恢复，图谱数据非空非损。** |
_bmad-output/审查/2026-07-31-ChatGPT第二轮对抗审查吸收与代码验证.md-159-
--
scripts/launchd/com.canvas.daily-review.plist-9-	</dict>
scripts/launchd/com.canvas.daily-review.plist-10-	<key>Label</key>
scripts/launchd/com.canvas.daily-review.plist-11-	<string>com.canvas.daily-review</string>
scripts/launchd/com.canvas.daily-review.plist-12-	<key>ProgramArguments</key>
scripts/launchd/com.canvas.daily-review.plist-13-	<array>
scripts/launchd/com.canvas.daily-review.plist-14-		<string>/bin/bash</string>
scripts/launchd/com.canvas.daily-review.plist:15:		<string>/Users/Heishing/Library/Application Support/CanvasReview/bin/daily-review-wrapper.sh</string>
scripts/launchd/com.canvas.daily-review.plist-16-	</array>
scripts/launchd/com.canvas.daily-review.plist-17-	<key>RunAtLoad</key>
scripts/launchd/com.canvas.daily-review.plist-18-	<true/>
scripts/launchd/com.canvas.daily-review.plist-19-	<key>StandardErrorPath</key>
scripts/launchd/com.canvas.daily-review.plist-20-	<string>/Users/Heishing/Library/Logs/canvas-daily-review.err.log</string>
scripts/launchd/com.canvas.daily-review.plist-21-	<key>StandardOutPath</key>
--
scripts/launchd/daily-review-wrapper.sh-1-#!/usr/bin/env bash
scripts/launchd/daily-review-wrapper.sh-2-# 每日复习推送 launchd 入口 wrapper (DAILY-REVIEW-PUSH-2026-07-29, 终审 A6)。
scripts/launchd/daily-review-wrapper.sh:3:# 安装位置: ~/Library/Application Support/CanvasReview/bin/ — launchd 只指向
scripts/launchd/daily-review-wrapper.sh-4-# 这个稳定路径, worktree 移动/清理不再让任务永久失效 (memory-health 6 天
scripts/launchd/daily-review-wrapper.sh-5-# 停摆教训的结构性修复)。本文件是 git 追踪的源码副本, 改动后需重新 cp 安装。
scripts/launchd/daily-review-wrapper.sh-6-set -uo pipefail
scripts/launchd/daily-review-wrapper.sh-7-
scripts/launchd/daily-review-wrapper.sh-8-export PATH="/usr/bin:/bin:/usr/sbin:/sbin"
scripts/launchd/daily-review-wrapper.sh-9-export HOME="${HOME:-/Users/Heishing}"
--
scripts/launchd/daily-review-wrapper.sh-31-# TCC preflight: Desktop 路径受 TCC 管辖。⚠ 必须真实读取 — [ -r ] 走 access()
scripts/launchd/daily-review-wrapper.sh-32-# 在 TCC 域内会假通过 (2026-07-29 实测: 测试全过但 exec 仍 Operation not
scripts/launchd/daily-review-wrapper.sh-33-# permitted), 只有 ls/head 这类真 I/O 才探得出来
scripts/launchd/daily-review-wrapper.sh-34-ls "$VAULT/节点" >/dev/null 2>&1 \
scripts/launchd/daily-review-wrapper.sh-35-    || fail "vault_not_readable_tcc — 系统设置→隐私与安全性→完全磁盘访问→给 /bin/bash 开启"
scripts/launchd/daily-review-wrapper.sh-36-mkdir -p "$REPO/backups" 2>/dev/null || fail "backups_not_writable_tcc"
scripts/launchd/daily-review-wrapper.sh:37:head -c 1 "$WT/scripts/daily-review-push.sh" >/dev/null 2>&1 \
scripts/launchd/daily-review-wrapper.sh-38-    || fail "repo_script_unreadable_tcc_or_missing — TCC 未授权或 worktree 被清理"
scripts/launchd/daily-review-wrapper.sh-39-# 双副本一致性 (Code-Review M4 + FSRS-V2 H1): runner/quiz-answer 用的是
scripts/launchd/daily-review-wrapper.sh-40-# 活 vault 里的副本, worktree 改了忘 cp 会造成静默行为漂移
scripts/launchd/daily-review-wrapper.sh-41-for f in decay_beta.py fsrs_bridge.py; do
scripts/launchd/daily-review-wrapper.sh-42-    cmp -s "$WT/canvas-vault/.claude/scripts/$f" \
scripts/launchd/daily-review-wrapper.sh-43-           "$VAULT/.claude/scripts/$f" \
scripts/launchd/daily-review-wrapper.sh-44-        || fail "${f}_version_skew — worktree 与活 vault 副本不一致, 需 cp 部署"
scripts/launchd/daily-review-wrapper.sh-45-done
scripts/launchd/daily-review-wrapper.sh-46-
scripts/launchd/daily-review-wrapper.sh:47:exec "$WT/scripts/daily-review-push.sh" --vault "$VAULT" "$@"
--
_bmad-output/研究/2026-07-29-每日复习手机推送-MVP方案.md-53-- 扫 `canvas-vault/节点/*.md` frontmatter（**三态兼容**：mastery_a/b+last_examined 新字段 → effective+pick；仅旧 mastery_score → from_legacy；无字段 → 先验。实测 18 节点中新字段仅 Fundamentals 1 个、旧字段 10 个）
_bmad-output/研究/2026-07-29-每日复习手机推送-MVP方案.md-54-- days_idle = 今天 − last_examined（无字段视为从未考 → 先验高 σ）
_bmad-output/研究/2026-07-29-每日复习手机推送-MVP方案.md-55-- 按 source_board 分组 → `board_priority = min(effective_pick)` + due count（pick<0.15 的节点数）
_bmad-output/研究/2026-07-29-每日复习手机推送-MVP方案.md-56-- 输出①：`canvas-vault/outputs/今日复习.md`（排序表 + 每板一行可粘贴的 `/start-exam-board from <板名>`）
_bmad-output/研究/2026-07-29-每日复习手机推送-MVP方案.md-57-- 输出②：stdout 单行 JSON `{top_boards:[{board,top_node,pending,idle_days}]}`
_bmad-output/研究/2026-07-29-每日复习手机推送-MVP方案.md-58-
_bmad-output/研究/2026-07-29-每日复习手机推送-MVP方案.md:59:### 3. scripts/daily-review-push.sh（编排壳，照抄 memory-health.sh 风格）
_bmad-output/研究/2026-07-29-每日复习手机推送-MVP方案.md-60-- 幂等守卫：`backups/daily-review.state` 记 `last_generate_date` / `last_push_date` **分开**（推送失败当天补跑只补推送）
_bmad-output/研究/2026-07-29-每日复习手机推送-MVP方案.md-61-- 顺序铁律：md 先落盘 → Bark（`curl -m 10 --retry 2 "$PUSH_URL/📚 今日复习 · <top1板名>/<正文>?group=canvas复习"`，push.env 缺失记「跳过(未配置)」不算错）→ 失败 `osascript -e 'display notification ...'` 兜底
_bmad-output/研究/2026-07-29-每日复习手机推送-MVP方案.md-62-- 21:00 后过窗跳推；单行日志 `backups/daily-review.log`（只记 provider+HTTP 码，**永不打印 PUSH_URL**）
_bmad-output/研究/2026-07-29-每日复习手机推送-MVP方案.md-63-
_bmad-output/研究/2026-07-29-每日复习手机推送-MVP方案.md-64-### 4. launchd 接线（⛔ 上轮血泪教训）
_bmad-output/研究/2026-07-29-每日复习手机推送-MVP方案.md:65:- `~/Library/LaunchAgents/com.canvas.daily-review.plist` 照抄 memory-health 模式（StartCalendarInterval 9:05 + RunAtLoad + StandardErrorPath）
_bmad-output/研究/2026-07-29-每日复习手机推送-MVP方案.md-66-- **必须**：`launchctl bootstrap gui/501 <plist>` 然后 `launchctl print gui/501/com.canvas.daily-review` 验证 + `kickstart` 实跑一次看退出码——**plist 写了不 bootstrap = 任务永远不存在**（memory-health 停摆 6 天的根因）
_bmad-output/研究/2026-07-29-每日复习手机推送-MVP方案.md-67-- 若 kickstart 报 126 = 用户 TCC 未授权，回到前置动作 2
_bmad-output/研究/2026-07-29-每日复习手机推送-MVP方案.md-68-
_bmad-output/研究/2026-07-29-每日复习手机推送-MVP方案.md-69-### 5. 死人开关 + 验收
_bmad-output/研究/2026-07-29-每日复习手机推送-MVP方案.md-70-- memory-health.sh 加字段：`复习推送:<今日跑否>`（grep daily-review.log 当日行）
_bmad-output/研究/2026-07-29-每日复习手机推送-MVP方案.md-71-- **验收三连**：① 手工把某节点 last_examined 改为 30 天前 → 跑 pick 脚本该板升榜首 ② kickstart → iPhone 收到 Bark 横幅 ③ 考完一场 `/quiz-answer` 再跑 → 推荐轮转
--
_bmad-output/implementation-artifacts/goal-cards/夜间车道运行手册.md-51-```
_bmad-output/implementation-artifacts/goal-cards/夜间车道运行手册.md-52-
_bmad-output/implementation-artifacts/goal-cards/夜间车道运行手册.md-53-### 1.3 CARD-A3（当天重学卡刷新，A2 合并后才开工）
_bmad-output/implementation-artifacts/goal-cards/夜间车道运行手册.md-54-
_bmad-output/implementation-artifacts/goal-cards/夜间车道运行手册.md-55-```bash
_bmad-output/implementation-artifacts/goal-cards/夜间车道运行手册.md-56-cd backend && .venv/bin/pytest tests/regression/test_daily_review_run.py tests/regression/test_daily_review_pick.py -q
_bmad-output/implementation-artifacts/goal-cards/夜间车道运行手册.md:57:plutil -lint scripts/launchd/com.canvas.daily-review.plist
_bmad-output/implementation-artifacts/goal-cards/夜间车道运行手册.md:58:grep -c "<key>Hour</key>" scripts/launchd/com.canvas.daily-review.plist   # 预期 ≥2
_bmad-output/implementation-artifacts/goal-cards/夜间车道运行手册.md-59-```
_bmad-output/implementation-artifacts/goal-cards/夜间车道运行手册.md-60-
_bmad-output/implementation-artifacts/goal-cards/夜间车道运行手册.md-61-### 1.4 CARD-B1（CI Dependency Audit）
_bmad-output/implementation-artifacts/goal-cards/夜间车道运行手册.md-62-
_bmad-output/implementation-artifacts/goal-cards/夜间车道运行手册.md-63-```bash
_bmad-output/implementation-artifacts/goal-cards/夜间车道运行手册.md-64-# 零豁免 pip-audit，预期输出 "No known vulnerabilities found"
--
_bmad-output/验收单/Story-DAILY-REVIEW-PUSH-每日复习手机推送-mini-UAT.md-53->
_bmad-output/验收单/Story-DAILY-REVIEW-PUSH-每日复习手机推送-mini-UAT.md-54-
_bmad-output/验收单/Story-DAILY-REVIEW-PUSH-每日复习手机推送-mini-UAT.md-55-## 7. 🔗 技术 spec 引用（给 Claude 读）
_bmad-output/验收单/Story-DAILY-REVIEW-PUSH-每日复习手机推送-mini-UAT.md-56-
_bmad-output/验收单/Story-DAILY-REVIEW-PUSH-每日复习手机推送-mini-UAT.md-57-- 方案: `_bmad-output/研究/2026-07-29-每日复习手机推送-MVP方案.md`（v2）
_bmad-output/验收单/Story-DAILY-REVIEW-PUSH-每日复习手机推送-mini-UAT.md-58-- 终审吸收: `_bmad-output/审查/2026-07-29-ChatGPT终审吸收与代码验证.md`
_bmad-output/验收单/Story-DAILY-REVIEW-PUSH-每日复习手机推送-mini-UAT.md:59:- 代码: `scripts/daily_review_pick.py` / `send_bark.py` / `daily_review_run.py` / `daily-review-push.sh` / `scripts/launchd/*`
_bmad-output/验收单/Story-DAILY-REVIEW-PUSH-每日复习手机推送-mini-UAT.md-60-- 算法: `canvas-vault/.claude/scripts/decay_beta.py`（effective + update_after_idle）
_bmad-output/验收单/Story-DAILY-REVIEW-PUSH-每日复习手机推送-mini-UAT.md-61-- 测试: `backend/tests/regression/test_decay_beta_convergence.py`（18）+ `test_daily_review_pick.py`（8）

exec
/bin/zsh -lc "rg -n \"PUSH_WINDOW|StartCalendarInterval|skip-window|skip-done|last_push_accepted_date|canvas-review-\" backend/tests scripts -g '*.py' -g '*.plist' -g '*.sh'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
scripts/daily_review_run.py:11:      · last_push_accepted_date 命名 (HTTP 成功仅证明服务端接受)
scripts/daily_review_run.py:38:PUSH_WINDOW = (dtime(9, 5), dtime(21, 0))
scripts/daily_review_run.py:113:    重学卡永远进不了投影。push 去重不在此处: last_push_accepted_date 天然
scripts/daily_review_run.py:189:    elif st.get("last_push_accepted_date") == today:
scripts/daily_review_run.py:190:        push = "skip-done"
scripts/daily_review_run.py:191:    elif not (PUSH_WINDOW[0] <= local.time() < PUSH_WINDOW[1]):
scripts/daily_review_run.py:192:        push = "skip-window"  # RunAtLoad 早触发 / 21:00 后唤醒: 只落盘
scripts/daily_review_run.py:196:            st["last_push_accepted_date"] = today
scripts/daily_review_pick.py:279:    day_id = f"canvas-review-{payload['date']}"
scripts/launchd/com.canvas.daily-review.plist:25:	     同日重复推送由 last_push_accepted_date 去重 (skip-done)。 -->
scripts/launchd/com.canvas.daily-review.plist:26:	<key>StartCalendarInterval</key>
scripts/memory-health.sh:80:if st.get("last_push_accepted_date", "") >= yesterday:
backend/tests/regression/test_daily_review_pick.py:236:    assert noti["id"] == f"canvas-review-{payload['date']}"
backend/tests/regression/test_daily_review_run.py:5:同日推送去重 (skip-done) 与 tie-break 语义 (board_last_recommended
backend/tests/regression/test_daily_review_run.py:101:# ── 场景 3: 重扫后同日推送仍 skip-done (Bark 同 id 去重门不被重扫击穿) ──
backend/tests/regression/test_daily_review_run.py:108:    # today 按 runner 同一变换推导 (机器时区无关): skip-done 门在窗口门之前
backend/tests/regression/test_daily_review_run.py:114:    st["last_push_accepted_date"] = today  # 早晨那次推送已被服务端接受
backend/tests/regression/test_daily_review_run.py:135:    assert "push:skip-done" in out
backend/tests/regression/test_daily_review_run.py:138:    assert st2["last_push_accepted_date"] == today
backend/tests/unit/test_story_30_24_boundary.py:502:        plugin_dir = tmp_path / ".obsidian" / "plugins" / "canvas-review-system"
backend/tests/unit/test_story_30_24_boundary.py:516:        plugin_dir = tmp_path / ".obsidian" / "plugins" / "canvas-review-system"

exec
/bin/zsh -lc 'git diff --numstat worktree-feature-obsidian-hybrid-dev...HEAD && git diff --check worktree-feature-obsidian-hybrid-dev...HEAD' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
235	0	backend/tests/regression/test_daily_review_run.py
41	4	scripts/daily_review_run.py
77	6	scripts/launchd/com.canvas.daily-review.plist
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead

exec
/bin/zsh -lc 'git status --short --branch' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
## card/a3-relearn
?? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-A3.md"
?? "_bmad-output/\351\252\214\346\224\266\345\215\225/Story-CARD-A3-\345\275\223\345\244\251\351\207\215\345\255\246\345\215\241\345\210\267\346\226\260.md"
?? backups/
?? "canvas-vault/outputs/\344\273\212\346\227\245\345\244\215\344\271\240.json"
?? "canvas-vault/outputs/\344\273\212\346\227\245\345\244\215\344\271\240.md"

**Identifying unexpected untracked UAT file**
**Verifying launchd scheduling behavior and untracked file origin**
**Confirming launchd execution timing logic**
**Identifying cache staleness risk from payload timestamp**
**Analyzing mtime race conditions and cache delays**
**Verifying push retry and deduplication logic**
**Inspecting A2 test ID and schema lines**
**Planning UAT creation inquiry**
exec
/bin/zsh -lc "nl -ba backend/tests/regression/test_daily_review_pick.py | sed -n '185,250p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
   185	    assert rows["无type"]["board"] == "B板" and rows["规范到期"]["board"] == "普通板"
   186	    # fail-open 清空语义锁定: Dashboard 的"新卡视同到期"计数依赖 fsrs_due==""
   187	    assert rows["脏due"]["fsrs_due"] == ""
   188	    # Codex-A2 M1/M2: 消费方可区分真新卡 / 已调度 / fail-open 脏日期
   189	    # (含"形状对但月份 13"的日历非法值, 不得被词法比较误判成未来)
   190	    assert rows["脏due"]["due_reason"] == "malformed"
   191	    assert rows["非法日期"]["due_reason"] == "malformed"
   192	    assert rows["无type"]["due_reason"] == "new"
   193	    assert rows["规范到期"]["due_reason"] == "scheduled"
   194	
   195	    ineligible = payload["ineligible"]
   196	    assert set(ineligible) >= {"placeholder", "test_excluded", "corrupt"}
   197	    assert ineligible["placeholder"] == ["占位"]
   198	    assert ineligible["test_excluded"] == ["TestConcept-伪节点"]
   199	    assert ineligible["corrupt"] == ["损坏"]
   200	    assert len(ineligible["placeholder"]) == payload["stats"]["ineligible"]
   201	    assert len(ineligible["test_excluded"]) == payload["stats"]["test_excluded"]
   202	    assert len(ineligible["corrupt"]) == payload["stats"]["corrupt"]
   203	    assert payload["unassigned_nodes"] == ["孤儿"]
   204	
   205	
   206	def test_projection_v3_purely_additive_keeps_v2_contract(tmp_path):
   207	    """推送链被动性守卫: v2 既有字段一个不少、语义不变 (daily_review_run /
   208	    send_bark 只读 notification, 但全字段名保留是加性承诺的下界)。"""
   209	    payload, ranked = _build(tmp_path, {"存量": _node()})
   210	    for key in (
   211	        "unassigned_nodes",
   212	        "date",
   213	        "generated_at",
   214	        "top_boards",
   215	        "upcoming",
   216	        "due_nodes",
   217	        "ineligible",
   218	        "stats",
   219	        "notification",
   220	    ):
   221	        assert key in payload
   222	    for key in (
   223	        "new",
   224	        "legacy",
   225	        "none",
   226	        "ineligible",
   227	        "test_excluded",
   228	        "corrupt",
   229	        "unassigned",
   230	        "due_nodes",
   231	        "future_nodes",
   232	    ):
   233	        assert isinstance(payload["stats"][key], int)
   234	    # Bark 推送硬依赖 notification 四键 (send_bark.py 直接下标访问, 缺键即崩)
   235	    noti = payload["notification"]
   236	    assert noti["id"] == f"canvas-review-{payload['date']}"
   237	    for key in ("title", "body", "group"):
   238	        assert isinstance(noti[key], str) and noti[key]
   239	    assert ranked[0]["board"] == "普通板"
   240	
   241	
   242	def test_nonfinite_pick_goes_corrupt_not_nan_json(tmp_path):
   243	    """Codex-A2 H1: 巨值 mastery 产出 NaN pick 不抛异常 — v3 起全部到期节点
   244	    的 pick 进 JSON, 单个 NaN 会让整个投影文件非法。必须进 corrupt 桶。"""
   245	    import json as _json
   246	
   247	    payload, ranked = _build(
   248	        tmp_path,
   249	        {
   250	            "溢出": _node(extra=f"mastery_a: {'9' * 400}\nmastery_b: 2\n"),

exec
/bin/zsh -lc "nl -ba scripts/launchd/daily-review-wrapper.sh | sed -n '1,90p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
     1	#!/usr/bin/env bash
     2	# 每日复习推送 launchd 入口 wrapper (DAILY-REVIEW-PUSH-2026-07-29, 终审 A6)。
     3	# 安装位置: ~/Library/Application Support/CanvasReview/bin/ — launchd 只指向
     4	# 这个稳定路径, worktree 移动/清理不再让任务永久失效 (memory-health 6 天
     5	# 停摆教训的结构性修复)。本文件是 git 追踪的源码副本, 改动后需重新 cp 安装。
     6	set -uo pipefail
     7	
     8	export PATH="/usr/bin:/bin:/usr/sbin:/sbin"
     9	export HOME="${HOME:-/Users/Heishing}"
    10	export LANG="zh_CN.UTF-8"
    11	
    12	BOOTLOG="$HOME/Library/Logs/canvas-daily-review.boot.log"
    13	# 第一行探针: 连 ~/Library 都写不了 = launchd 环境彻底异常
    14	echo "[$(date '+%F %T')] wrapper start" >> "$BOOTLOG"
    15	
    16	REPO="/Users/Heishing/Desktop/canvas/canvas-learning-system"
    17	WT="$REPO/.claude/worktrees/feature-obsidian-hybrid-dev"
    18	
    19	fail() { echo "[$(date '+%F %T')] PREFLIGHT-FAIL: $1" >> "$BOOTLOG"; exit 78; }
    20	
    21	# VAULT-SYNC (2026-08-02 用户拍板): 推送 vault 与 .env ACTIVE_VAULT 同源 —
    22	# P0-3 确立「vault 由部署期 .env 固定」后, 推送链不再独立写死, 换 vault
    23	# 只改 .env 一处, 后端/skills/推送全部跟走。解析失败回退 canvas-vault
    24	# (与旧行为一致); VAULTS_ROOT 取 .env 宿主侧值, 缺省回退主仓根。
    25	ENV_FILE="$WT/.env"
    26	ACTIVE_VAULT=$(grep -E '^ACTIVE_VAULT=' "$ENV_FILE" 2>/dev/null | tail -1 | cut -d= -f2- | tr -d '"' | tr -d "'")
    27	VAULTS_ROOT_HOST=$(grep -E '^VAULTS_ROOT=' "$ENV_FILE" 2>/dev/null | tail -1 | cut -d= -f2- | tr -d '"' | tr -d "'")
    28	VAULT="${VAULTS_ROOT_HOST:-$REPO}/${ACTIVE_VAULT:-canvas-vault}"
    29	echo "[$(date '+%F %T')] vault=$VAULT (ACTIVE_VAULT=${ACTIVE_VAULT:-<fallback>})" >> "$BOOTLOG"
    30	
    31	# TCC preflight: Desktop 路径受 TCC 管辖。⚠ 必须真实读取 — [ -r ] 走 access()
    32	# 在 TCC 域内会假通过 (2026-07-29 实测: 测试全过但 exec 仍 Operation not
    33	# permitted), 只有 ls/head 这类真 I/O 才探得出来
    34	ls "$VAULT/节点" >/dev/null 2>&1 \
    35	    || fail "vault_not_readable_tcc — 系统设置→隐私与安全性→完全磁盘访问→给 /bin/bash 开启"
    36	mkdir -p "$REPO/backups" 2>/dev/null || fail "backups_not_writable_tcc"
    37	head -c 1 "$WT/scripts/daily-review-push.sh" >/dev/null 2>&1 \
    38	    || fail "repo_script_unreadable_tcc_or_missing — TCC 未授权或 worktree 被清理"
    39	# 双副本一致性 (Code-Review M4 + FSRS-V2 H1): runner/quiz-answer 用的是
    40	# 活 vault 里的副本, worktree 改了忘 cp 会造成静默行为漂移
    41	for f in decay_beta.py fsrs_bridge.py; do
    42	    cmp -s "$WT/canvas-vault/.claude/scripts/$f" \
    43	           "$VAULT/.claude/scripts/$f" \
    44	        || fail "${f}_version_skew — worktree 与活 vault 副本不一致, 需 cp 部署"
    45	done
    46	
    47	exec "$WT/scripts/daily-review-push.sh" --vault "$VAULT" "$@"

exec
/bin/zsh -lc 'git diff worktree-feature-obsidian-hybrid-dev...HEAD --word-diff=porcelain -- scripts/daily_review_pick.py canvas-vault/.claude/scripts/fsrs_bridge.py scripts/send_bark.py scripts/daily-review-push.sh scripts/launchd/daily-review-wrapper.sh' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead

exec
/bin/zsh -lc "git merge-base --is-ancestor f6a426b35d7324f73caf147018ab200770987b17 HEAD; git log -1 --format='%H %s' f6a426b35d7324f73caf147018ab200770987b17" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
f6a426b35d7324f73caf147018ab200770987b17 chore: merge card/b1-ci-e0 [BATCH-2026-08-24-复习闭环 / CARD-B1 + CARD-E0]

**Checking commit order in log**
exec
/bin/zsh -lc 'git log --oneline --decorate -12 worktree-feature-obsidian-hybrid-dev' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
f6a426b3 (origin/worktree-feature-obsidian-hybrid-dev, backup/worktree-feature-obsidian-hybrid-dev, worktree-feature-obsidian-hybrid-dev) chore: merge card/b1-ci-e0 [BATCH-2026-08-24-复习闭环 / CARD-B1 + CARD-E0]
42e29fb3 chore: merge card/a2-projection — unified review projection v3 [BATCH-2026-08-24-复习闭环 / CARD-A2]
a25c6c95 chore: merge card/a1-fsrs-none — fsrs new-card none fix [BATCH-2026-08-24-复习闭环 / CARD-A1]
84644a9d (card/b1-ci-e0) fix(ci): remove dead moviepy, upgrade pillow, zero pip-audit exemptions
4844244f (card/a1-fsrs-none) fix(fsrs): address Codex review findings + archive review & UAT sheet
ba42bfc7 (card/a2-projection) fix(review): unify due projection to schema v3 single judge
6a1c9a01 fix(fsrs): serialize new-card None as JSON null, stop silent Ebbinghaus fallback
848469ca fix(test): bypass orphan-import collection paralysis + nightly runbook
2cf9cbf0 chore(governance): issue generation micro
c1990df5 fix(governance): isolate vault untracked walk [PLAN-CLS-PRODUCTIVITY-2026-08-20]
d3167d06 chore(governance): issue generation approval envelope
efff5a5b fix(governance): validate native verify-pack records

**Planning reproduction for directory disappearance**
**Running reproduction with escalation**
**Evaluating test gaps for true lock behavior**
**Searching tests for send_bark usage**
exec
/bin/zsh -lc "rg -n \"send_bark|bark accepted|device_key|api.day.app|notification.*id|canvas-review-\" backend/tests scripts --glob '*.py' --glob '*.sh' | head -n 260" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
scripts/daily_review_run.py:29:import send_bark  # noqa: E402
scripts/daily_review_run.py:194:        rc = send_bark.send(noti)
scripts/send_bark.py:6:  - POST https://api.day.app/push JSON body (非 GET 路径拼接 — 免 URL
scripts/send_bark.py:8:  - 同日稳定 notification id → Bark 端幂等更新 (本地 at-least-once +
scripts/send_bark.py:33:DEFAULT_SERVER = "https://api.day.app"
scripts/send_bark.py:39:    """读 key 文件 → (server, device_key)。兼容整段 URL 或裸 key。
scripts/send_bark.py:62:    server, device_key = cfg
scripts/send_bark.py:65:            "device_key": device_key,
scripts/send_bark.py:69:            "id": notification["id"],
scripts/send_bark.py:91:                print(f"bark accepted http={http} code={code}")
scripts/daily_review_pick.py:11:(daily_review_run/send_bark 只读 notification) 被动兼容。
scripts/daily_review_pick.py:279:    day_id = f"canvas-review-{payload['date']}"
backend/tests/regression/test_daily_review_pick.py:208:    send_bark 只读 notification, 但全字段名保留是加性承诺的下界)。"""
backend/tests/regression/test_daily_review_pick.py:234:    # Bark 推送硬依赖 notification 四键 (send_bark.py 直接下标访问, 缺键即崩)
backend/tests/regression/test_daily_review_pick.py:236:    assert noti["id"] == f"canvas-review-{payload['date']}"
backend/tests/unit/test_story_30_24_boundary.py:502:        plugin_dir = tmp_path / ".obsidian" / "plugins" / "canvas-review-system"
backend/tests/unit/test_story_30_24_boundary.py:516:        plugin_dir = tmp_path / ".obsidian" / "plugins" / "canvas-review-system"
backend/tests/regression/test_daily_review_run.py:126:    monkeypatch.setattr(runner.send_bark, "send", _sentinel)

**Assessing test coverage gaps**
**Evaluating test precision and coverage limits**
exec
/bin/zsh -lc "backend/.venv/bin/python -c '
import os, shutil, sys, tempfile
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / \"scripts\"))
import daily_review_run as runner
root = Path(tempfile.mkdtemp(prefix=\"card-a3-dir-audit-\"))
try:
    vault = root / \"vault\"
    (vault / \"节点\").mkdir(parents=True)
    (vault / \".claude\" / \"scripts\").mkdir(parents=True)
    shutil.copy(Path.cwd() / \"canvas-vault\" / \".claude\" / \"scripts\" / \"decay_beta.py\", vault / \".claude\" / \"scripts\" / \"decay_beta.py\")
    (vault / \"节点\" / \"甲.md\").write_text(\"---\\ntype: concept\\nsource_board: \\\"[[原白板/A板]]\\\"\\n---\\n真实内容。\\n\", encoding=\"utf-8\")
    runner.VAULT = vault
    runner.STATE = root / \"backups\" / \"state.json\"
    st = runner.load_state()
    p1, g1 = runner.ensure_payload(st, datetime.fromisoformat(\"2026-07-30T09:05:00+08:00\"), \"2026-07-30\")
    (vault / \"节点\").rename(vault / \"节点.off\")
    p2, g2 = runner.ensure_payload(st, datetime.fromisoformat(\"2026-07-30T10:05:00+08:00\"), \"2026-07-30\")
    print({\"pool_exists\": (vault / \"节点\").exists(), \"max_mtime\": runner._nodes_max_mtime(vault), \"first\": (g1, [x[\"node\"] for x in p1[\"due_nodes\"]]), \"after_rename\": (g2, [x[\"node\"] for x in p2[\"due_nodes\"]])})
finally:
    shutil.rmtree(root)
'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
{'pool_exists': False, 'max_mtime': 0.0, 'first': ('new', ['甲']), 'after_rename': ('cached', ['甲'])}

**Analyzing cache freshness risks**
**Tracing file modification scenarios**
**Confirming wrapper preflight prevents directory issues**
**Planning time-aware cache investigation**
**Evaluating full backend test run feasibility**
**Starting full backend test run**
codex
缓存主路径的 BLOCKER 已由三条独立轨迹和真实临时 vault 复现一致；其余静态语义目前是绿的。我再跑仓库规定的完整后端 `tests/ -x -q`，用来区分“目标测试全绿”与“未见更广回归”，同时继续复核 plist 与 push 的测试门强度。
exec
/bin/zsh -lc '.venv/bin/pytest tests/ -x -q' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/backend
**Implementing post-execution wait**
**Adjusting process polling strategy**
**Implementing delayed cell yield using timer**
**Planning periodic test suite monitoring**
**Planning background test execution**
exec
/bin/zsh -lc "nl -ba backend/tests/regression/test_fsrs_bridge.py | sed -n '1,85p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
     1	"""fsrs_bridge 契约锁定 (FSRS-V2-2026-07-30, [Decision-FSRS-1/2])。
     2	
     3	锁四件事: 映射边界 / New卡零迁移语义 / F2 间隔扩张与 F3 当日重学 /
     4	stdlib 入口 re-exec 降级路径。
     5	"""
     6	
     7	import json
     8	import subprocess
     9	import sys
    10	from pathlib import Path
    11	
    12	WT = Path(__file__).resolve().parents[3]
    13	BRIDGE = WT / "canvas-vault" / ".claude" / "scripts" / "fsrs_bridge.py"
    14	sys.path.insert(0, str(BRIDGE.parent))
    15	
    16	import fsrs_bridge as fb  # noqa: E402
    17	
    18	NOW = "2026-07-30T01:00:00Z"
    19	
    20	
    21	# ── [Decision-FSRS-1] 映射边界 ──
    22	
    23	
    24	def test_rating_mapping_boundaries():
    25	    assert fb.rating_from_grade(1.0, abandoned=True) == 1, "弃答一票否决 Again"
    26	    assert fb.rating_from_grade(0.0, False) == 1  # grade 1.0
    27	    assert fb.rating_from_grade(0.1, False) == 1  # 1.3 → Again
    28	    assert fb.rating_from_grade(0.2, False) == 2  # 1.6 → Hard
    29	    assert fb.rating_from_grade(1.0 / 3, False) == 2  # 2.0 → Hard
    30	    assert fb.rating_from_grade(0.5, False) == 3  # 2.5 边界 → Good
    31	    assert fb.rating_from_grade(2.0 / 3, False) == 3  # 3.0 → Good
    32	    assert fb.rating_from_grade(0.84, False) == 4  # 3.52 → Easy
    33	    assert fb.rating_from_grade(1.0, False) == 4
    34	    assert fb.rating_from_grade(9.9, False) == 4, "越界钳制"
    35	
    36	
    37	# ── [Decision-FSRS-2] New 卡零迁移 + 调度行为 ──
    38	
    39	
    40	def test_new_card_first_good_enters_learning_minutes():
    41	    out = fb.review({}, 2.0 / 3, False, NOW)
    42	    assert out["fsrs_state"] == 1 and out["fsrs_step"] == 1
    43	    assert out["fsrs_due"] == "2026-07-30T01:10:00Z", "Learning 第二步 = +10 分钟"
    44	    assert float(out["fsrs_stability"]) > 0 and float(out["fsrs_difficulty"]) > 0
    45	    assert out["fsrs_last_review"] == NOW
    46	
    47	
    48	def test_graduation_then_interval_expands_f2():
    49	    """F2: Good 毕业进 Review 后, 连续 Good 的间隔单调拉长。"""
    50	    out = fb.review({}, 2.0 / 3, False, NOW)
    51	    out = fb.review(out, 2.0 / 3, False, out["fsrs_due"])
    52	    assert out["fsrs_state"] == 2, "毕业进 Review"
    53	    d1 = fb._aware(out["fsrs_due"]) - fb._aware(out["fsrs_last_review"])
    54	    out2 = fb.review(out, 2.0 / 3, False, out["fsrs_due"])
    55	    d2 = fb._aware(out2["fsrs_due"]) - fb._aware(out2["fsrs_last_review"])
    56	    assert d1.days >= 1 and d2 > d1, f"间隔应扩张: {d1} → {d2}"
    57	
    58	
    59	def test_again_relearning_same_day_f3():
    60	    """F3: Review 态答 Again → Relearning, due = +10 分钟 (当日重学环)。"""
    61	    out = fb.review({}, 2.0 / 3, False, NOW)
    62	    out = fb.review(out, 2.0 / 3, False, out["fsrs_due"])  # 进 Review
    63	    ts = out["fsrs_due"]
    64	    out = fb.review(out, 0.0, True, ts)  # 弃答 → Again
    65	    assert out["fsrs_state"] == 3
    66	    assert (fb._aware(out["fsrs_due"]) - fb._aware(ts)).total_seconds() == 600
    67	
    68	
    69	def test_easy_due_later_than_good_f5():
    70	    """F5: 同一张 Review 卡, Easy 的下次到期晚于 Good。"""
    71	    base = fb.review({}, 2.0 / 3, False, NOW)
    72	    base = fb.review(base, 2.0 / 3, False, base["fsrs_due"])
    73	    ts = base["fsrs_due"]
    74	    good = fb.review(dict(base), 2.0 / 3, False, ts)
    75	    easy = fb.review(dict(base), 1.0, False, ts)
    76	    assert fb._aware(easy["fsrs_due"]) > fb._aware(good["fsrs_due"])
    77	
    78	
    79	def test_fields_from_frontmatter_roundtrip():
    80	    """frontmatter 序列化往返: 写出的字段能被解析并继续复习。"""
    81	    out = fb.review({}, 0.5, False, NOW)
    82	    fm = out["fm_block"]
    83	    assert "fsrs_due:" in fm and "fsrs_last_review:" in fm
    84	    parsed = fb.fields_from_frontmatter(fm)
    85	    assert parsed["fsrs_due"] == out["fsrs_due"]

exec
/bin/zsh -lc "rg -n \"StartCalendarInterval|Hour|Minute\" backend/tests --glob '*.py'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 exited 1 in 0ms:
exec
/bin/zsh -lc 'git diff --name-only worktree-feature-obsidian-hybrid-dev...HEAD && git diff --exit-code worktree-feature-obsidian-hybrid-dev...HEAD -- scripts/send_bark.py canvas-vault/Dashboard.md canvas-vault/.claude/scripts/fsrs_bridge.py' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
backend/tests/regression/test_daily_review_run.py
scripts/daily_review_run.py
scripts/launchd/com.canvas.daily-review.plist
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead

**Assessing plist and lock test gaps**
**Classifying plist test gap as medium**
**Evaluating high-severity plist trigger concern**
**Assessing prolonged test execution time**
codex
完整后端集共收集 6,627 项，当前仍在跑且尚无失败；它明显比 CARD-A3 裁判集慢很多。我会继续观察，但最终会明确区分：22 项定向测试已通过、完整集是否真正跑完，避免把“仍在执行”误写成全绿。
**Identifying exact skill and MEMORY.md line citations**
exec
/bin/zsh -lc "nl -ba /Users/Heishing/.codex/memories/MEMORY.md | sed -n '126,140p' && nl -ba /Users/Heishing/.codex/memories/skills/canvas-adversarial-audit/SKILL.md | sed -n '1,90p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 succeeded in 0ms:
   126	### keywords
   127	
   128	- P1-05b, hostile-env, symlink_escape, casefold, vault_backfill, lancedb_client, quarantine__p105b, get_by_node_uuid, node_name_and_summary, pick_eligible, manifest-v3, NaN, CURRENT_TASK
   129	
   130	## User preferences
   131	
   132	- When requesting an audit, the user asked: “启动并行 agent 进行对抗性审查” -> decompose independent evidence tracks, cross-check high-severity findings, and do not treat green tests as closure. [Task 1][Task 2]
   133	- Require code rather than documentation evidence: each finding needs `file:line`, reproducible input/state → path → result chain, severity, conflict explanation, PASS/PARTIAL/FAIL, and stated limits. [Task 2]
   134	- Respect task-book boundaries: read-only work, WT/MAIN labels, explicit `UNVERIFIABLE`, no raw-vault access, and structured delivery; do not fix product code during audit. [Task 1]
   135	
   136	## Reusable knowledge
   137	
   138	- Related skill: skills/canvas-adversarial-audit/SKILL.md. [Task 1][Task 2]
   139	- Latest represented verdict: P1-05/P1-01/P1-08 were STILL-OPEN; F-02 tombstone filtering and F-05 live resilience were closed. Audit actual entrypoints: rejected vault paths must cause zero open/hash/index/write. [Task 1][Task 2]
   140	- Reproduced: `vault/raw/escape.md -> /outside/secret.md` was counted by `backfill_vault(..., execute=False)`; case-sensitive `fnmatch` admitted `.CLAUDE/SKILL.md` and `raw/claude.md`. Graphiti edge filtering alone was insufficient because exact readers/node search could cross groups. [Task 1][Task 2]
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

**Confirming rollout ID citations**
**Clarifying git diff scope and labels**
**Deciding to interrupt slow test suite**
**Planning to stop and report partial tests**
codex
完整集在前几组后进入极慢路径（数分钟只推进少量用例），继续等待不会提高本次三文件审查的有效覆盖。我会中止这次额外全量尝试，并把它明确记为“未完成、不得作为全绿证据”；定向 22 项与真实反例已经足以判定本改动不可通过。
 exited 2 in 216811ms:
============================= test session starts ==============================
platform darwin -- Python 3.14.4, pytest-9.0.2, pluggy-1.6.0
rootdir: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/backend
configfile: pytest.ini
plugins: hypothesis-6.151.10, cov-7.1.0, xdist-3.8.0, asyncio-1.3.0, schemathesis-4.14.3, bdd-8.1.0, langsmith-0.7.24, anyio-4.13.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 6627 items

tests/api/v1/endpoints/test_agents_dedup.py ...............              [  0%]
tests/api/v1/endpoints/test_agents_encoding.py ................          [  0%]
tests/api/v1/endpoints/test_agents_health.py ............                [  0%]
tests/api/v1/endpoints/test_agents_learning_event.py ................... [  0%]
                                                                         [  0%]
tests/api/v1/endpoints/test_fsrs_state_api.py .....

=============================== warnings summary ===============================
.venv/lib/python3.14/site-packages/google/genai/types.py:43
  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/backend/.venv/lib/python3.14/site-packages/google/genai/types.py:43: DeprecationWarning: '_UnionGenericAlias' is deprecated and slated for removal in Python 3.17
    VersionedUnionType = Union[builtin_types.UnionType, _UnionGenericAlias]

.venv/lib/python3.14/site-packages/langchain_core/_api/deprecation.py:25
  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/backend/.venv/lib/python3.14/site-packages/langchain_core/_api/deprecation.py:25: UserWarning: Core Pydantic V1 functionality isn't compatible with Python 3.14 or greater.
    from pydantic.v1.fields import FieldInfo as FieldInfoV1

.venv/lib/python3.14/site-packages/graphiti_core/driver/search_interface/search_interface.py:22
  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/backend/.venv/lib/python3.14/site-packages/graphiti_core/driver/search_interface/search_interface.py:22: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    class SearchInterface(BaseModel):

.venv/lib/python3.14/site-packages/jieba/_compat.py:18
  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/backend/.venv/lib/python3.14/site-packages/jieba/_compat.py:18: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
    import pkg_resources

<frozen importlib._bootstrap>:491
  <frozen importlib._bootstrap>:491: DeprecationWarning: builtin type SwigPyPacked has no __module__ attribute

<frozen importlib._bootstrap>:491
  <frozen importlib._bootstrap>:491: DeprecationWarning: builtin type SwigPyObject has no __module__ attribute

app/api/v1/endpoints/chat.py:803
  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/backend/app/api/v1/endpoints/chat.py:803: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    class HookEnrichRequest(BaseModel):

app/api/v1/endpoints/metadata.py:147
  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/backend/app/api/v1/endpoints/metadata.py:147: FastAPIDeprecationWarning: `example` has been deprecated, please use `examples` instead
    canvas_path: str = Query(

app/api/v1/endpoints/metadata.py:218
  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/backend/app/api/v1/endpoints/metadata.py:218: FastAPIDeprecationWarning: `example` has been deprecated, please use `examples` instead
    canvas_path: str = Query(..., description="Canvas file path", example="Math 54/离散数学.canvas"),

.venv/lib/python3.14/site-packages/pydantic/_internal/_generate_schema.py:2356
  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/backend/.venv/lib/python3.14/site-packages/pydantic/_internal/_generate_schema.py:2356: PydanticDeprecatedSince211: The `__get_pydantic_core_schema__` method of the `BaseModel` class is deprecated. If you are calling `super().__get_pydantic_core_schema__` when overriding the method on a Pydantic model, consider using `handler(source)` instead. However, note that overriding this method on models can lead to unexpected side effects. Deprecated in Pydantic V2.11 to be removed in V3.0.
    schema = annotation_get_schema(source, get_inner_schema)

tests/api/v1/endpoints/test_agents_dedup.py::TestDedupEndpointResponses::test_duplicate_request_returns_409
tests/api/v1/endpoints/test_agents_dedup.py::TestDedupEndpointResponses::test_409_response_detail_format
tests/api/v1/endpoints/test_agents_learning_event.py::TestEndpointIntegration::test_explain_oral_triggers_recording
tests/api/v1/endpoints/test_agents_learning_event.py::TestAllExplainEndpointsRecording::test_explain_endpoint_records_event[explain_oral-explain_oral]
tests/api/v1/endpoints/test_agents_learning_event.py::TestAllExplainEndpointsRecording::test_explain_endpoint_records_event[explain_clarification-explain_clarification]
tests/api/v1/endpoints/test_agents_learning_event.py::TestAllExplainEndpointsRecording::test_explain_endpoint_records_event[explain_comparison-explain_comparison]
tests/api/v1/endpoints/test_agents_learning_event.py::TestAllExplainEndpointsRecording::test_explain_endpoint_records_event[explain_memory-explain_memory]
tests/api/v1/endpoints/test_agents_learning_event.py::TestAllExplainEndpointsRecording::test_explain_endpoint_records_event[explain_four_level-explain_four-level]
tests/api/v1/endpoints/test_agents_learning_event.py::TestAllExplainEndpointsRecording::test_explain_endpoint_records_event[explain_example-explain_example]
  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/backend/app/api/v1/endpoints/agents.py:1168: DeprecationWarning: deprecated
    legacy_group_id=request.group_id,

tests/api/v1/endpoints/test_agents_learning_event.py::TestEndpointIntegration::test_decompose_basic_triggers_recording
tests/api/v1/endpoints/test_agents_learning_event.py::TestEndpointIntegration::test_learning_event_failure_does_not_block_response
  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/backend/app/api/v1/endpoints/agents.py:787: DeprecationWarning: deprecated
    legacy_group_id=request.group_id,

tests/api/v1/endpoints/test_agents_learning_event.py::TestEndpointIntegration::test_decompose_deep_triggers_recording
  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/backend/app/api/v1/endpoints/agents.py:900: DeprecationWarning: deprecated
    legacy_group_id=request.group_id,

tests/api/v1/endpoints/test_agents_learning_event.py::TestEndpointIntegration::test_score_understanding_triggers_recording
  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/backend/app/api/v1/endpoints/agents.py:1019: DeprecationWarning: deprecated
    legacy_group_id=request.group_id,

tests/api/v1/endpoints/test_fsrs_state_api.py::TestFSRSStateEndpoint::test_returns_auto_created_card
tests/api/v1/endpoints/test_fsrs_state_api.py::TestFSRSStateEndpoint::test_returns_auto_created_card
tests/api/v1/endpoints/test_fsrs_state_api.py::TestFSRSStateEndpoint::test_returns_reason_fsrs_not_initialized
tests/api/v1/endpoints/test_fsrs_state_api.py::TestFSRSStateEndpoint::test_returns_reason_on_service_exception
tests/api/v1/endpoints/test_fsrs_state_api.py::TestFSRSStateEndpoint::test_returns_reason_auto_creation_failed
tests/api/v1/endpoints/test_fsrs_state_api.py::TestFSRSStateEndpoint::test_found_true_has_null_reason
  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/backend/lib/agentic_rag/clients/lancedb_client.py:881: DeprecationWarning: table_names() is deprecated, use list_tables() instead
    table_names = self._db.table_names()

tests/api/v1/endpoints/test_fsrs_state_api.py::TestFSRSStateEndpoint::test_returns_auto_created_card
tests/api/v1/endpoints/test_fsrs_state_api.py::TestFSRSStateEndpoint::test_returns_auto_created_card
tests/api/v1/endpoints/test_fsrs_state_api.py::TestFSRSStateEndpoint::test_returns_reason_fsrs_not_initialized
tests/api/v1/endpoints/test_fsrs_state_api.py::TestFSRSStateEndpoint::test_returns_reason_on_service_exception
tests/api/v1/endpoints/test_fsrs_state_api.py::TestFSRSStateEndpoint::test_returns_reason_auto_creation_failed
tests/api/v1/endpoints/test_fsrs_state_api.py::TestFSRSStateEndpoint::test_found_true_has_null_reason
  /opt/homebrew/Cellar/python@3.14/3.14.4_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/asyncio/events.py:94: DeprecationWarning: table_names() is deprecated, use list_tables() instead
    self._context.run(self._callback, *self._args)

tests/api/v1/endpoints/test_fsrs_state_api.py: 738 warnings
  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/backend/.venv/lib/python3.14/site-packages/frontmatter/__init__.py:161: DeprecationWarning: codecs.open() is deprecated. Use open() instead.
    with codecs.open(fd, "r", encoding) as f:

tests/api/v1/endpoints/test_fsrs_state_api.py::TestFSRSStateEndpoint::test_returns_auto_created_card
tests/api/v1/endpoints/test_fsrs_state_api.py::TestFSRSStateEndpoint::test_returns_reason_fsrs_not_initialized
tests/api/v1/endpoints/test_fsrs_state_api.py::TestFSRSStateEndpoint::test_returns_reason_on_service_exception
tests/api/v1/endpoints/test_fsrs_state_api.py::TestFSRSStateEndpoint::test_returns_reason_auto_creation_failed
tests/api/v1/endpoints/test_fsrs_state_api.py::TestFSRSStateEndpoint::test_found_true_has_null_reason
tests/api/v1/endpoints/test_fsrs_state_api.py::TestHealthEndpointFSRS::test_health_includes_fsrs_ok
  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/backend/.venv/lib/python3.14/site-packages/google/genai/_api_client.py:850: DeprecationWarning: Inheritance class AiohttpClientSession from ClientSession is discouraged
    class AiohttpClientSession(aiohttp.ClientSession):  # type: ignore[misc]

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! KeyboardInterrupt !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
/opt/homebrew/Cellar/python@3.14/3.14.4_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/threading.py:369: KeyboardInterrupt
(to show a full traceback on KeyboardInterrupt use --full-trace)
================= 67 passed, 779 warnings in 201.83s (0:03:21) =================
<sys>:0: DeprecationWarning: builtin type swigvarlink has no __module__ attribute

**Running FSRS bridge targeted tests**
exec
/bin/zsh -lc '.venv/bin/pytest tests/regression/test_fsrs_bridge.py -q' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/backend
 succeeded in 10121ms:
============================= test session starts ==============================
platform darwin -- Python 3.14.4, pytest-9.0.2, pluggy-1.6.0
rootdir: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/backend
configfile: pytest.ini
plugins: hypothesis-6.151.10, cov-7.1.0, xdist-3.8.0, asyncio-1.3.0, schemathesis-4.14.3, bdd-8.1.0, langsmith-0.7.24, anyio-4.13.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 8 items

tests/regression/test_fsrs_bridge.py ........                            [100%]

=============================== warnings summary ===============================
.venv/lib/python3.14/site-packages/google/genai/types.py:43
  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/backend/.venv/lib/python3.14/site-packages/google/genai/types.py:43: DeprecationWarning: '_UnionGenericAlias' is deprecated and slated for removal in Python 3.17
    VersionedUnionType = Union[builtin_types.UnionType, _UnionGenericAlias]

.venv/lib/python3.14/site-packages/langchain_core/_api/deprecation.py:25
  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/backend/.venv/lib/python3.14/site-packages/langchain_core/_api/deprecation.py:25: UserWarning: Core Pydantic V1 functionality isn't compatible with Python 3.14 or greater.
    from pydantic.v1.fields import FieldInfo as FieldInfoV1

.venv/lib/python3.14/site-packages/graphiti_core/driver/search_interface/search_interface.py:22
  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/backend/.venv/lib/python3.14/site-packages/graphiti_core/driver/search_interface/search_interface.py:22: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    class SearchInterface(BaseModel):

.venv/lib/python3.14/site-packages/jieba/_compat.py:18
  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/backend/.venv/lib/python3.14/site-packages/jieba/_compat.py:18: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
    import pkg_resources

<frozen importlib._bootstrap>:491
  <frozen importlib._bootstrap>:491: DeprecationWarning: builtin type SwigPyPacked has no __module__ attribute

<frozen importlib._bootstrap>:491
  <frozen importlib._bootstrap>:491: DeprecationWarning: builtin type SwigPyObject has no __module__ attribute

app/api/v1/endpoints/chat.py:803
  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/backend/app/api/v1/endpoints/chat.py:803: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    class HookEnrichRequest(BaseModel):

app/api/v1/endpoints/metadata.py:147
  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/backend/app/api/v1/endpoints/metadata.py:147: FastAPIDeprecationWarning: `example` has been deprecated, please use `examples` instead
    canvas_path: str = Query(

app/api/v1/endpoints/metadata.py:218
  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/backend/app/api/v1/endpoints/metadata.py:218: FastAPIDeprecationWarning: `example` has been deprecated, please use `examples` instead
    canvas_path: str = Query(..., description="Canvas file path", example="Math 54/离散数学.canvas"),

.venv/lib/python3.14/site-packages/pydantic/_internal/_generate_schema.py:2356
  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/backend/.venv/lib/python3.14/site-packages/pydantic/_internal/_generate_schema.py:2356: PydanticDeprecatedSince211: The `__get_pydantic_core_schema__` method of the `BaseModel` class is deprecated. If you are calling `super().__get_pydantic_core_schema__` when overriding the method on a Pydantic model, consider using `handler(source)` instead. However, note that overriding this method on models can lead to unexpected side effects. Deprecated in Pydantic V2.11 to be removed in V3.0.
    schema = annotation_get_schema(source, get_inner_schema)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 8 passed, 10 warnings in 0.53s ========================

**Planning sequential thinking calls**
mcp: sequential-thinking/sequentialthinking started
mcp: sequential-thinking/sequentialthinking (completed)
mcp: sequential-thinking/sequentialthinking started
mcp: sequential-thinking/sequentialthinking (completed)
**Assessing plist test coverage gap**
**Investigating mock usage rule applicability**
exec
/bin/zsh -lc "rg -n -C 8 \"DD-03|mock|Mock|模拟\" .claude/rules/development-discipline.md .claude/rules -g '*.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn
 exited 2 in 0ms:
rg: .claude/rules/development-discipline.md: No such file or directory (os error 2)
rg: .claude/rules: No such file or directory (os error 2)

**Assessing untracked review and UAT files**
**Planning cache invalidation analysis**
**Verifying Graphiti tool availability**
**Confirming no tracked file modifications after tests**
**Preparing test result summary with file links**
**Diagnosing cache key timing issue**
**Clarifying cache invalidation requirements**
**Validating test scenario sufficiency**
**Confirming successful tests and schema stability**
**Noting incomplete test suite and untracked files excluded**
collab: Wait
collab: Wait
**Planning agent interruption strategy**
mcp: sequential-thinking/sequentialthinking started
mcp: sequential-thinking/sequentialthinking (completed)
**Completing update plan**
只读审查完成；核心时序反例经主审和三条独立轨迹交叉确认，定向测试/FSRS/plist/schema/push/tie-break 已复核，完整后端集明确记录为未完成。
  ✓ 读取 CARD-A3、仓库审查规则与相关历史审计记忆，固定验收标准和改动范围
  ✓ 并行审查缓存/重扫/tie-break 与推送去重/plist/schema 路径
  ✓ 审查测试覆盖并运行最小针对性验证与回归检查
  ✓ 交叉复核证据，输出按 BLOCKER/HIGH/MEDIUM 分级的独立结论
**Structuring final detailed summary**
**Assessing test coverage and severity conflicts**
**Finalizing independent review verdict**
**Confirming test results and coverage gaps**
**Evaluating test coverage limitations**
**Detailing blocker justification and test accuracy**
**Verifying review scope and output constraints**
codex
结论：**FAIL / BLOCKED**。审查范围为 `f6a426b3...346448b7` 的 3 个已跟踪文件。发现 **1 BLOCKER、0 HIGH、1 MEDIUM**。

1. **BLOCKER — 缓存未考虑时间推进，核心缺陷仍可复现**

   [daily_review_run.py:118–140](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/scripts/daily_review_run.py:118) 只以节点 mtime 判断重扫，并在重扫后把 payload mtime 推进到扫描起点；但实际到期判断依赖当前时间，[daily_review_pick.py:182](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/scripts/daily_review_pick.py:182)。

   真实 `ensure_payload + daily_review_pick` 临时 vault 复现：

   - 09:05：`new, due_nodes=[]`
   - 09:59：按生产 FSRS 写入 `fsrs_due=10:09`
   - 10:05：mtime 触发重扫，但尚未到期，仍为 `new, []`
   - 11:05：已经到期，却返回 `cached, []`

   FSRS 确实产生 +10 分钟重学时间：[test_fsrs_bridge.py:40–66](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/backend/tests/regression/test_fsrs_bridge.py:40)。这正是 [CARD-A3:89](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-08-24-第一批小goal卡-复习闭环.md:89) 明确要求避免的“缺陷位移”。

   新测试漏掉该转场：[test_daily_review_run.py:64–81](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/backend/tests/regression/test_daily_review_run.py:64) 使用无 `fsrs_due` 的立即到期节点；无变动测试又以同一 `NOW` 重复调用。必须增加“首次重扫发生在 due 前、下一小时跨过 due”的测试，并让缓存因业务时间越过 future due 而失效，或真正每小时重扫。

2. **MEDIUM — plist 的精确 12 档/窗口契约未被测试锁定**

   当前 [plist:26](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/scripts/launchd/com.canvas.daily-review.plist:26) 本身正确：`plutil -lint` 通过，解析为 09:05–20:05 共 12 档，全部处于 `[09:05,21:00)`。

   但测试没有解析 plist；机械门只要求 Hour 键 `>=2`。例如仅保留 09:05、21:05 两档，pytest、`plutil -lint` 和 grep 仍会通过，却同时破坏档数和推送窗口。应断言完整的 12 个 `(Hour, Minute)` 对。

其余请求面为 PASS：

- push：`last_push_accepted_date` 的 `skip-done` 未被重扫击穿；通知 ID 仍稳定为 `canvas-review-<date>` 并原样传给 Bark。
- tie-break：重扫路径不更新 `board_last_recommended`，且有针对性测试。
- schema v3：`daily_review_pick.py` 在 baseline/HEAD 的 blob 完全相同，确为零改动消费。
- 定向裁判：22 passed；FSRS bridge：8 passed。
- 完整后端集收集 6,627 项，因极慢路径主动中止于 67 passed、0 failed；因此**不得宣称全量测试全绿**。
- 未执行 `launchctl` 或 live LaunchAgent 部署；Graphiti MCP 本轮未暴露。


tokens used
148,767
结论：**FAIL / BLOCKED**。审查范围为 `f6a426b3...346448b7` 的 3 个已跟踪文件。发现 **1 BLOCKER、0 HIGH、1 MEDIUM**。

1. **BLOCKER — 缓存未考虑时间推进，核心缺陷仍可复现**

   [daily_review_run.py:118–140](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/scripts/daily_review_run.py:118) 只以节点 mtime 判断重扫，并在重扫后把 payload mtime 推进到扫描起点；但实际到期判断依赖当前时间，[daily_review_pick.py:182](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/scripts/daily_review_pick.py:182)。

   真实 `ensure_payload + daily_review_pick` 临时 vault 复现：

   - 09:05：`new, due_nodes=[]`
   - 09:59：按生产 FSRS 写入 `fsrs_due=10:09`
   - 10:05：mtime 触发重扫，但尚未到期，仍为 `new, []`
   - 11:05：已经到期，却返回 `cached, []`

   FSRS 确实产生 +10 分钟重学时间：[test_fsrs_bridge.py:40–66](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/backend/tests/regression/test_fsrs_bridge.py:40)。这正是 [CARD-A3:89](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-08-24-第一批小goal卡-复习闭环.md:89) 明确要求避免的“缺陷位移”。

   新测试漏掉该转场：[test_daily_review_run.py:64–81](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/backend/tests/regression/test_daily_review_run.py:64) 使用无 `fsrs_due` 的立即到期节点；无变动测试又以同一 `NOW` 重复调用。必须增加“首次重扫发生在 due 前、下一小时跨过 due”的测试，并让缓存因业务时间越过 future due 而失效，或真正每小时重扫。

2. **MEDIUM — plist 的精确 12 档/窗口契约未被测试锁定**

   当前 [plist:26](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a3-relearn/scripts/launchd/com.canvas.daily-review.plist:26) 本身正确：`plutil -lint` 通过，解析为 09:05–20:05 共 12 档，全部处于 `[09:05,21:00)`。

   但测试没有解析 plist；机械门只要求 Hour 键 `>=2`。例如仅保留 09:05、21:05 两档，pytest、`plutil -lint` 和 grep 仍会通过，却同时破坏档数和推送窗口。应断言完整的 12 个 `(Hour, Minute)` 对。

其余请求面为 PASS：

- push：`last_push_accepted_date` 的 `skip-done` 未被重扫击穿；通知 ID 仍稳定为 `canvas-review-<date>` 并原样传给 Bark。
- tie-break：重扫路径不更新 `board_last_recommended`，且有针对性测试。
- schema v3：`daily_review_pick.py` 在 baseline/HEAD 的 blob 完全相同，确为零改动消费。
- 定向裁判：22 passed；FSRS bridge：8 passed。
- 完整后端集收集 6,627 项，因极慢路径主动中止于 67 passed、0 failed；因此**不得宣称全量测试全绿**。
- 未执行 `launchctl` 或 live LaunchAgent 部署；Graphiti MCP 本轮未暴露。



---

# 附录 A：处置记录（Claude Code / Fable 5，2026-08-25）

Codex 初审（gpt-5.6-sol，ultra 档，只读沙箱，审 f6a426b3...346448b7）：**1 BLOCKER / 0 HIGH / 1 MEDIUM**。全部处置完毕，处置后裁判命令重跑 **24 passed** 全绿。

## BLOCKER — 时间推进跨过未来 fsrs_due 不失效缓存（已修）

- **确认有效**：mtime 门只捕获「节点池变动」，捕获不了「业务时间越过生成时尚未到期的 fsrs_due」。Codex 复现链（09:59 落 fsrs_due=10:09 → 10:05 重扫未到期 → 11:05 只看 mtime 判 cached）成立——恰是卡片档案 :89 警告的「缺陷位移」。
- **修复**：`ensure_payload` 生成路径把「最早未来到期点」记入 runner state（`next_due_utc`，取全量 ranked 各板 next_due 与 upcoming[0].next_due 的最小值；upcoming 升序截断不丢全局最小；未归板节点不参与推荐、其到期转场不改变输出）。cached 路径加第二道门：`now(UTC) >= next_due_utc` 则失效重扫。**只动 runner 自己的 state 文件，不碰 A2 的 payload schema v3。**
- **测试**：新增 `test_time_crossing_future_due_invalidates_cache`（先红后绿）：02:00 生成（卡 02:30 到期、清单空）→ 03:05 池零变动必须 "new" 且卡进 due_nodes → 03:06 无剩余未来到期点时回到 "cached"（不退化成每轮全扫）。

## MEDIUM — plist 12 档契约未被测试锁定（已修）

- **确认有效**：机械门 `Hour 键 ≥2` 太弱，留 9:05 + 21:05 两档也能通过但同时破坏档数与推送窗。
- **修复**：新增 `test_plist_hourly_slots_inside_push_window`：plistlib 解析后断言 `StartCalendarInterval == [{Hour:h, Minute:5} for h in 9..20]`（12 档整体相等），并逐档断言落在 `PUSH_WINDOW [9:05, 21:00)` 内。

## Codex 标注的其余 PASS 面（原文复核结论）

push 去重（skip-done 未被重扫击穿、通知 id 稳定）/ tie-break（重扫不写 board_last_recommended）/ schema v3 零改动（baseline 与 HEAD blob 相同）/ 定向裁判 22 passed + FSRS bridge 8 passed。

## 诚实记录（不宣称的部分）

- 全量后端测试集（6627 项收集）Codex 主动中止于 67 passed / 0 failed（慢路径），**本卡不宣称全量测试全绿**；本卡的机械门为卡片档案指定的定向裁判命令（处置后 24 passed）。
- 未执行 `launchctl` / 未部署 live LaunchAgent（卡片硬边界，待用户确认后单独执行）。

## 内审前置（Codex 之前的三视角对抗工作流，13 finding）

- 已修：mutation 缺口两条失效通道单独锁定（2 测试）、扫描-落盘竞态窗口 payload mtime 回拨扫描起点（1 测试）、迭代间隙删除的目录 stat 殿后。
- 记录待裁决（不在本卡范围/与卡片明文规格冲突）：①空首扫日 blr 不落账边界（卡片规定「重扫路径不写」，改动属产品语义决策）；②休息日推送冻结（早间「今日无到期」推送后下午冒出到期卡，手机侧不更新——推送去重语义为卡片明文锁定，建议 backlog 裁决是否放行同 id 覆盖推送）；③保 mtime 还原类操作不触发重扫（纯 mtime 判据固有边界，已在代码注释说明）。
