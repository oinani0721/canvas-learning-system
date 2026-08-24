Reading additional input from stdin...
OpenAI Codex v0.147.0
--------
workdir: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
model: gpt-5.6-sol
provider: openai
approval: on-request
sandbox: read-only
reasoning effort: ultra
reasoning summaries: auto
session id: 01a0346a-8e09-7be2-8b2c-8446b3b1c9c4
--------
user
你是独立代码审查者。读 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-08-24-第一批小goal卡-复习闭环.md 的 CARD-A2 节，然后在 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection 用 git diff worktree-feature-obsidian-hybrid-dev 审查本改动（改动未提交，diff 对比的是工作树）。重点审查：(1) outputs/今日复习.json 的 payload schema v2→3 是否纯加性——既有字段名与语义有无任何改动；(2) 推送链 daily_review_run.py 与 send_bark.py 对新增字段是否保持被动消费、有无被破坏；(3) fail-open/fail-closed 语义是否统一——脏 fsrs_due 的处理在生成侧与 Dashboard 消费侧是否一致；(4) canvas-vault/Dashboard.md 的 dataviewjs 是否真消费投影而非独立重算，JSON 缺失/损坏/旧版三条降级路径是否不白屏；(5) backend/tests/regression/test_daily_review_pick.py 新增测试是否真覆盖卡片列的 5 类口径分歧节点；(6) 有无引入回归。输出 BLOCKER/HIGH/MEDIUM 分级 finding 清单，没有就写 PASS
2026-08-24T15:36:35.294710Z ERROR codex_memories_write::phase2: Phase 2 no changes
2026-08-24T15:36:38.544442Z ERROR codex_models_manager::manager: failed to refresh available models: timeout waiting for child process to exit
**Assessing available audit skills**
**Planning multiagent audit approach**
**Analyzing git diff and untracked files**
codex
我会按独立、只读、fail-closed 的审查方式处理：先锁定 CARD-A2 的验收口径与当前工作树范围，再并行核查 schema/推送链、Dashboard 降级语义、测试覆盖与回归；所有结论都会落到可复现的 `file:line` 证据。由于这是 Canvas 项目的治理式审查，我也会先读取既有的审查记忆与规程，避免沿用实现者结论。
exec
/bin/zsh -lc 'rg -n "CARD-A2|projection|daily_review|canvas-adversarial-audit|goal.card|复习闭环" /Users/Heishing/.codex/memories/MEMORY.md' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
 succeeded in 0ms:
138:- Related skill: skills/canvas-adversarial-audit/SKILL.md. [Task 1][Task 2]

**Planning code inspection around lines 100-145**
exec
/bin/zsh -lc "sed -n '100,145p' /Users/Heishing/.codex/memories/MEMORY.md && wc -l /Users/Heishing/.codex/memories/skills/canvas-adversarial-audit/SKILL.md && sed -n '1,260p' /Users/Heishing/.codex/memories/skills/canvas-adversarial-audit/SKILL.md" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
 succeeded in 0ms:
## Failures and how to do differently

- Symptom: an old GOV receipt/envelope seems to permit execution. Cause: it was `pending-user-confirmation` and expired. Fix: issue a new envelope/digest/challenge; never substitute a narrative anchor for exact current binding. [Task 1]
- Symptom: an existing scanner appears usable for final census. Cause: `scripts/bmad/scan_feedback.py` does not cover the actual annotation output. Fix: freeze a new scanner contract and no-write boundary before census. [Task 1]
- Do not call dual-model review complete without the required runtime sequence and fresh receipt. Before GOV-01-VERIFIED, hard-block all listed execution, private/Vault/transcript, external send, writes, commit, and push actions. [Task 1]

# Task Group: Canvas Learning System P1-05/P1-01/P1-08 adversarial security review
scope: Read-only, parallel, evidence-first audit of vault admission/indexing, Graphiti quarantine isolation, SnapshotV3, and recovery-anchor closure claims.
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

## Failures and how to do differently

- Green tests can still be unsafe when they hit source strings, helpers, fake clients, `__new__`, or monkeypatches. Pivot to production entrypoints and full stdout/trace. [Task 1][Task 2]
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

**Planning precise memory citations**
**Planning explicit skill usage announcement**
codex
我将采用保存的 `canvas-adversarial-audit` 审查规程，因为它要求把实现者测试与真实生产入口分开验证，并对高严重度问题做独立交叉核查。该规程只影响审查方法；本轮不会修改产品代码、卡片文档或工作树。Graphiti 与 Sequential Thinking 工具在当前会话未提供，我会把这项验证限制如实计入报告。
**Planning task book and agents inspection**
**Planning concurrent git and agents inspections**
  → 锁定 CARD-A2 验收口径、工作树基线与完整 diff 范围
  • 并行审查 schema/推送链、Dashboard 降级语义、测试覆盖与回归
  • 复现关键反例并运行相关测试/静态验证
  • 交叉核验 finding，输出分级结论与验证限制
exec
/bin/zsh -lc "rg -n '"'^#{1,6} .*CARD-A[123]|CARD-A2'"' '/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-08-24-第一批小goal卡-复习闭环.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
 succeeded in 0ms:
53:### CARD-A1: FSRS 新卡 None 序列化崩溃修复
73:### CARD-A2: 统一 Review Projection 最小版（到期口径）
83:### CARD-A3: 当天重学卡刷新（串行于 A2 之后）
161:/goal 完成 CARD-A2：统一 Review Projection 最小版（到期口径 13 vs 6）。必读卡片档案：/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-08-24-第一批小goal卡-复习闭环.md 的 CARD-A2 节（含 5 个口径分歧的 file:line）。完成条件（AND）：
166:(5) Codex 交叉审查（同 A1 模式，把提示词里的 CARD-A1 换成 CARD-A2，重点审：schema 是否纯加性、推送链字段是否被动、fail-open/fail-closed 语义是否统一）输出存 _bmad-output/审查/codex-review-CARD-A2.md，处理完 BLOCKER/HIGH。
168:(7) git commit 含 "BATCH-2026-08-24-复习闭环 / CARD-A2"；不 push。

exec
/bin/zsh -lc 'git diff --name-status worktree-feature-obsidian-hybrid-dev' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
M	backend/tests/regression/test_daily_review_pick.py
M	canvas-vault/Dashboard.md
M	scripts/daily_review_pick.py

exec
/bin/zsh -lc 'git diff --stat worktree-feature-obsidian-hybrid-dev' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
 backend/tests/regression/test_daily_review_pick.py | 76 ++++++++++++++++++++++
 canvas-vault/Dashboard.md                          | 42 ++++++++++--
 scripts/daily_review_pick.py                       | 41 ++++++++++--
 3 files changed, 147 insertions(+), 12 deletions(-)

exec
/bin/zsh -lc 'git status --short --branch' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
exec
/bin/zsh -lc 'pwd
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
git rev-parse worktree-feature-obsidian-hybrid-dev' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
## card/a2-projection
 M backend/tests/regression/test_daily_review_pick.py
 M canvas-vault/Dashboard.md
 M scripts/daily_review_pick.py
?? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-A2.md"
?? "_bmad-output/\351\252\214\346\224\266\345\215\225/Story-CARD-A2-\345\244\215\344\271\240\345\210\260\346\234\237\345\217\243\345\276\204\347\273\237\344\270\200.md"

 succeeded in 0ms:
/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
card/a2-projection
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
2cf9cbf0f73479805d4d413fd72829ff825b38bf
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
2cf9cbf0f73479805d4d413fd72829ff825b38bf

exec
/bin/zsh -lc 'find .. -name AGENTS.md -print' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
 succeeded in 3709ms:
../card-b1-ci-e0/backend/.venv/lib/python3.14/site-packages/litellm/proxy/_experimental/mcp_server/AGENTS.md
../feature-obsidian-hybrid-dev/_bmad-output/AGENTS.md

**Inspecting CARD-A2 section lines**
**Reading related AGENTS.md file**
exec
/bin/zsh -lc "wc -l '/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/AGENTS.md' && sed -n '1,260p' '/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/AGENTS.md'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
exec
/bin/zsh -lc "nl -ba '/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-08-24-第一批小goal卡-复习闭环.md' | sed -n '65,92p;150,172p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
 succeeded in 0ms:
      31 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/AGENTS.md
# Repository Guidelines

## Project Structure & Module Organization

Run commands from the repository root (the parent of `_bmad-output/`). The active frontend is `frontend/obsidian-plugin/src/`, with tests in `frontend/obsidian-plugin/tests/`. Tauri/React paths `frontend/src/`, `frontend/src-tauri/`, and `frontend/sidecar/` are deprecated. FastAPI code is under `backend/app/`, RAG components under `backend/lib/agentic_rag/`, and tests under `backend/tests/`. Specifications and documentation live in `specs/`, `openspec/`, and `docs/`; story and audit artifacts live in `_bmad-output/implementation-artifacts/`.

## Build, Test, and Development Commands

- `npm --prefix frontend/obsidian-plugin install` installs plugin dependencies.
- `npm --prefix frontend/obsidian-plugin run dev` watches the plugin; `run build` creates its production bundle.
- `npm --prefix frontend/obsidian-plugin test` bundles and runs the Node test suite.
- `cd backend && pip install -r requirements.txt` installs backend dependencies.
- `cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000` starts FastAPI locally.
- `cd backend && .venv/bin/pytest tests/ -x -q` runs backend tests, stopping at the first failure.
- `npm run verify:spec` checks generated API/spec synchronization; `npx lefthook run pre-commit` runs repository gates.

## Coding Style & Naming Conventions

Python uses four spaces, type hints, `snake_case` functions/modules, and `PascalCase` classes. Ruff enforces formatting/imports with a 120-character limit; Pyright checks types. TypeScript uses two spaces, double quotes, `camelCase` values, `PascalCase` types/classes, and strict null/implicit-any checks. Use kebab-case filenames such as `ai-linked-doc.ts`. Do not add mock data, fake APIs, placeholder functions, or misleading names.

## Testing Guidelines

Name Python tests `test_*.py` and plugin tests `*.test.ts`. Add regression coverage beside affected modules; exercise failure, boundary, and async paths. Default pytest has no global coverage threshold, but changed code should not lose coverage. Integration tests may require configured services such as Neo4j.

## Commit & Pull Request Guidelines

Use Conventional Commits, for example `fix(vault): prevent cross-vault lookup PLAN-123`; headers must be lowercase and at most 100 characters. Code commits require `PLAN-`, `FR-`, or `@spec:` and should include a `Story: x.y` trailer. Complete every PR template section: traceability, summary, user-level acceptance criteria, tests, and logging. Link issues/specs and include UI screenshots.

## Security & Agent-Specific Rules

Never commit `.env`, API keys, vault contents, or generated private data. Use the root `.env` as configuration source. Build new Graphiti group IDs with `build_vault_group_id()` and guard Cypher through `cypher_with_group_filter()` to prevent cross-vault leakage. Create new OpenSpec changes with the CLI and validate them with `npx openspec validate <name> --strict`.

 succeeded in 0ms:
    65	- **完成判据（机械）**:
    66	  1. 新增回归测试（真实库对象，禁 mock）四断言：serialize_card(新卡) 无异常可 roundtrip / card_to_state 无异常 / get_fsrs_state("新概念") found=True / schedule_review 新卡 algorithm=="fsrs-4.5" 非 fallback——**先跑确认全红，修后全绿**；
    67	  2. 修正 test_fsrs_state_query.py:202-210 矛盾断言；
    68	  3. 裁判命令：`cd backend && .venv/bin/pytest tests/regression/test_fsrs_new_card_none_serialization.py tests/unit/test_fsrs_manager.py tests/unit/test_fsrs_state_query.py tests/unit/test_story_38_3_fsrs_init_guarantee.py tests/unit/test_review_service_fsrs.py tests/regression/test_fsrs_bridge.py -q` 全绿；
    69	  4. 冒烟：`.venv/bin/python -c "import sys; sys.path.insert(0,'lib'); from memory.temporal.fsrs_manager import FSRSManager; m=FSRSManager(); print(m.serialize_card(m.create_card()))"` 输出 JSON。
    70	- **风险**: get_fsrs_state 对新概念 found=False→True 的行为变化需过一眼插件调用方；勘探顺带发现相邻潜伏 bug——`fsrs_manager.py:319` `State(0)` 在 v6 抛 ValueError（历史 state:0 数据反序列化会崩），**本卡不修，列入第二批候选**。
    71	- **并行**: 与 A2/A3/B1/E0 零文件交集，完全并行安全。注意与未来"grade→rating 映射"卡在 fsrs_manager.py 同文件（函数级不相交）。
    72	
    73	### CARD-A2: 统一 Review Projection 最小版（到期口径）
    74	
    75	- **确认状态**: CONFIRMED（live vault 实测复现 13 vs 6，两集合交集仅 5、互不为子集）
    76	- **证据摘要**: 5 个口径分歧代码原因——①picker 跳占位符节点（`scripts/daily_review_pick.py:97`）Dashboard 不跳（贡献 8 个差值）；②Dashboard 强制 type==concept（`canvas-vault/Dashboard.md:22`）picker 不要求（反向漏 1 个无 type 节点）；③picker due_nodes 要求 source_board（pick.py:212）；④picker 排除 TEST_MARKERS（pick.py:92）；⑤脏 fsrs_due 一边 fail-open 一边 fail-closed + UTC 词法比较 vs 本地时区 DateTime。已排除第三套口径（board_manifest_service 不做 due 判定）。
    77	- **方案**: daily_review_pick 为唯一裁判；`outputs/今日复习.json` schema_version 2→3 **纯加性**扩展（`due_nodes` 明细 + `ineligible` 分桶）；Dashboard FSRS 块改 `dv.io.load("outputs/今日复习.json")` 消费投影 + 显示 generated_at，删除独立重算。
    78	- **改动文件**: `scripts/daily_review_pick.py`、`canvas-vault/Dashboard.md`（worktree 与 live vault **两份都要**）、`backend/tests/regression/test_daily_review_pick.py`（现成 fixture 可扩）、验收单
    79	- **完成判据（机械)**: parity 测试覆盖全部 5 类分歧节点，断言 due_nodes 明细==期望集合、数字与明细自洽、schema_version==3；`grep -c "schedCnt\|newCnt" canvas-vault/Dashboard.md` == 0 且 `grep -c "今日复习.json"` ≥1；live 冒烟两处数字一致。
    80	- **风险**: schema v3 必须纯加性（daily_review_run.py 推送链消费同一 JSON，改坏=Bark 推送断）；Dashboard.md 双副本必须同步部署（memory 已有 worktree vault 陈旧副本教训）；dv.io.load 失败需降级文案；**产品语义决策点见上方"拍板 1"**。
    81	- **并行**: 与 A1/B1/E0 并行安全；**与 A3 在 daily_review_pick.py + 回归测试文件上有真实冲突 → A2 先行（schema owner），A3 串行其后只消费不改 schema**。
    82	
    83	### CARD-A3: 当天重学卡刷新（串行于 A2 之后）
    84	
    85	- **确认状态**: CONFIRMED（launchd plist 全天仅 9:05 一档；`daily_review_run.py:85-112 ensure_payload` 同日 sha 匹配即复用，现网日志实证 `generate:cached push:skip-done`；quiz-answer 写侧全链 grep 零失效触发点；fsrs 6.3.1 实测 learning_steps=(60s,600s) 全落当天）
    86	- **方案**: ①ensure_payload 缓存条件放宽——当天已生成后，若 `节点/*.md` 最大 mtime > payload mtime 则重扫（push 去重由 last_push_accepted_date 天然保证）；②plist StartCalendarInterval 改数组 9:05–21:00 每小时一档（重扫必须周期性——只做写侧一次性触发的话，due=now+1min 的卡在重生成瞬间仍未到期，缺陷只是位移）。
    87	- **改动文件**: `scripts/daily_review_run.py`、`scripts/launchd/com.canvas.daily-review.plist`、新增 `backend/tests/regression/test_daily_review_run.py`；部署侧 `~/Library/LaunchAgents/` 重装（**破坏性操作，动手前单独向用户确认**）
    88	- **完成判据（机械）**: 三场景测试（节点变动后 ensure_payload 返回 "new" 且含该节点 / 无变动仍 "cached" / 重扫后 push 仍 skip-done）+ `plutil -lint` 通过 + plist Hour 键 ≥2 档。测试只 assert dict 不 assert md 文本（与 A2 解耦）。
    89	- **风险**: board_last_recommended 只在首次生成时更新（重扫路径不写，防污染 tie-break 语义）；每小时触发放大 wrapper 双副本 preflight 的暴露频率（是暴露不是引入）；Bark 通知同 id 覆盖靠 skip-done 门守住（场景 3 锁死）。
    90	- **并行**: 依赖 A2 的 schema v3 先落地；与 A1/B1/E0 零交集。
    91	
    92	### CARD-B1: CI Dependency Audit 修复（方案 A 已预验证）
   150	(3) 修正 tests/unit/test_fsrs_state_query.py:202-210 里靠本 bug 维持绿灯的 found=False 断言。
   151	(4) 裁判命令全绿：cd backend && .venv/bin/pytest tests/regression/test_fsrs_new_card_none_serialization.py tests/unit/test_fsrs_manager.py tests/unit/test_fsrs_state_query.py tests/unit/test_story_38_3_fsrs_init_guarantee.py tests/unit/test_review_service_fsrs.py tests/regression/test_fsrs_bridge.py -q
   152	(5) Codex 交叉审查（统一命令：锁 gpt-5.6-sol + ultra 档）：codex exec --sandbox read-only -m gpt-5.6-sol -c model_reasoning_effort="ultra" "你是独立代码审查者。读 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-08-24-第一批小goal卡-复习闭环.md 的 CARD-A1 节，然后 git diff worktree-feature-obsidian-hybrid-dev...HEAD 审查本改动：修复是否正确、None 语义是否被写死 0.0、测试是否真用真实库对象、有无引入回归。输出 BLOCKER/HIGH/MEDIUM 分级 finding 清单，没有就写 PASS" > _bmad-output/审查/codex-review-CARD-A1.md，处理完全部 BLOCKER/HIGH 后重跑裁判命令。
   153	(6) 按 _bmad-output/templates/uat-sheet-template.md 写小白验收单到本 worktree 的 _bmad-output/验收单/Story-CARD-A1-fsrs新卡修复.md。
   154	(7) git commit（含 "BATCH-2026-08-24-复习闭环 / CARD-A1"，把测试、修复、审查存档、验收单都提交）。
   155	硬边界：只改上述文件；不 push；不碰 canvas-vault；不装新依赖；不改 scripts/ 与 .github/；遇到需要产品语义决策的岔路，选卡片档案"设计要点"写明的方案，不自创。
   156	```
   157	
   158	**A2（车道 1）：**
   159	
   160	```
   161	/goal 完成 CARD-A2：统一 Review Projection 最小版（到期口径 13 vs 6）。必读卡片档案：/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-08-24-第一批小goal卡-复习闭环.md 的 CARD-A2 节（含 5 个口径分歧的 file:line）。完成条件（AND）：
   162	(1) scripts/daily_review_pick.py：outputs/今日复习.json 的 payload schema_version 2→3 纯加性扩展——新增 due_nodes 逐节点明细与 ineligible 分桶（占位符未剖析节点单独成桶，不静默吞掉）；不改既有字段名与语义（daily_review_run.py 推送链在消费它）。
   163	(2) 本 worktree 的 canvas-vault/Dashboard.md：FSRS 块删除 schedCnt/newCnt 独立重算，改为 dv.io.load("outputs/今日复习.json") 消费投影，显示 generated_at 与"待剖析积压"分桶；JSON 缺失/损坏时显示降级文案不白屏。注意：只改本 worktree 副本，live vault 的部署由用户白天确认后单独执行，你不碰 /Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/。
   164	(3) 扩展 backend/tests/regression/test_daily_review_pick.py（用现成 _build() fixture）：构造覆盖全部 5 类分歧节点的 vault，断言 due_nodes 明细==期望集合、len(due_nodes)==stats.due_nodes、schema_version==3、ineligible 分桶存在；先红后绿。
   165	(4) 裁判命令：cd backend && .venv/bin/pytest tests/regression/test_daily_review_pick.py -q 全绿；grep -c "schedCnt\|newCnt" canvas-vault/Dashboard.md 输出 0；grep -c "今日复习.json" canvas-vault/Dashboard.md ≥1。
   166	(5) Codex 交叉审查（同 A1 模式，把提示词里的 CARD-A1 换成 CARD-A2，重点审：schema 是否纯加性、推送链字段是否被动、fail-open/fail-closed 语义是否统一）输出存 _bmad-output/审查/codex-review-CARD-A2.md，处理完 BLOCKER/HIGH。
   167	(6) 小白验收单 ship 到本 worktree _bmad-output/验收单/（须含"live vault 部署待用户确认"一节）。
   168	(7) git commit 含 "BATCH-2026-08-24-复习闭环 / CARD-A2"；不 push。
   169	硬边界：不碰 backend/lib/memory/ 与 review_service.py（那是 A1 的地盘）；不改 daily_review_run.py（那是 A3 的地盘，你只定义 schema 它消费）；测试只 assert dict 不 assert md 渲染文本。
   170	```
   171	
   172	**B1+E0（车道 3，同一 Session 先 E0 后 B1）：**

exec
/bin/zsh -lc "if test -f CURRENT_TASK.md; then nl -ba CURRENT_TASK.md | sed -n '1,220p'; else echo 'CURRENT_TASK.md absent'; fi" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
 succeeded in 0ms:
     1	# CURRENT_TASK: Canvas Learning System × Obsidian Hybrid（回归路径）
     2	
     3	> **前 15 行是 Clear Context 后的恢复锚点 — 必须自包含**
     4	
     5	**当前状态**（2026-08-20 · **Codex 四轮拒绝收官 → 九路验证 9/9 CONFIRMED → C1-C4 修复批全部落地，五轮送审就绪** · 最近完成的产品提交 `c154a7f2`(C1 真实入口准入) · PLAN `R11-BATCH2-2026-08-17`。⚠️ 锚点纪律：①不记累计 commit 数 ②不落盘 CI run 号/通过数（连续两轮落盘即过期被抓——CI 状态以 `gh run list --limit 3` 实查为准）③收官状态由外部复核裁定不由施工方自宣）:
     6	- 🔴 **下一步执行顺序（用户 2026-08-19 裁定，逐项独立提交独立验收，禁止合并成大返工）**：
     7	  **① P1-05 第四轮返工（P1-05d）已落地，待五轮终裁** — Codex 四轮（`2026-08-19` 终裁文档）判 F-02/F-05 CLOSED、其余 STILL-OPEN；九路验证（`2026-08-20-Codex四轮终裁-九路验证与C批次方案.md`）9/9 CONFIRMED 含 B3 新回归一条。C 批全部落地：**C2**（`1683328c`：脏 last_examined 投影 None 止血 B3 新回归 · freshness 嵌套错型自愈 · 5 处 ID 切片改丢弃 · _id_ok 写侧过滤同源 · lag_seconds finite · 控制字符全拒）· **C3**（`d39983ce`：conversation_summary caller 显式传 vault 组修恒空 bug · ensure_entity_node 隔离身份拒绝复用）· **C1**（`c154a7f2`：lib 层 _resolves_outside_vault 接 LanceDB 两真实入口 open 前 · orchestrator 裸 fnmatch 换 canon + 扫描产出过 should_index 根除 hash-before-admission + realpath containment · by-node missing→404/path_rejected→422；新 test_real_entrypoint_admission.py 6 条真实入口行为锁）· **C4**（census Q2 中性化+前缀分类）。**遗留**：B4（payload 命名空间/provenance）独立轮 · TOCTOU 换链残余窗口（realpath 判定与 open 非原子，诚实登记）· P1-03/P1-04 押后
     8	  **② P1-01 快照安全 — SnapshotV3+B3+C2 全部落地，⛔ 收官待 Codex 五轮裁定**（四轮三反例已修：同代伪造死区→写侧全量 validate 自愈 · 根[]与嵌套 freshness=[] 双防御 · strict 契约+ID 拒绝不截断+丢条目不丢整包；四轮新发现三洞 V3/V4/V5 已在 C2 闭合并有反例锁）。已知完整性余量（Codex 登记）：同 generation 且 schema 合法的数值篡改可通过 validator——validator 证形状不证来源，归 B4 provenance
     9	  **③ P1-03 + P1-04 合并做**（不许先改 degraded 以后再补测试）— 返回值改明确状态枚举 `ok/empty/degraded/unavailable`，原因写入 `CanvasRAGState` 并验证 API/trace 可见；MemoryService 内部异常返回 `[]` 被判成「真没记忆」的吞噬点必须堵。**验收门**：真实 Neo4j 或真实不可达端点覆盖成功/空结果/故障/fallback 四态；`test_story_2_3_error_reminders.py` 那 5 个相邻失败**属于新链依赖（node 过滤与 schema），不得归为无关旧账**
    10	- ⚠️ **Codex 二轮复核（`_bmad-output/审查/2026-08-19-Codex对抗审查-R11返工反馈进一步复核.md`）判 P1×8 + P2×3。已修 3 条（`0acefe1b`）**：P1-02 我上一轮的 group 层级传错（写基组读子组 overlap=∅，"修复"召回仍恒空）· P1-06 fallback 只挡语法不挡 schema（`[]`→崩溃、`{}`→旧值 5 从 `get_max_references` 默认参数泄漏）· P1-07 部分（4 个新契约锁根本不在 CI，测试清单 5→9 文件）。**剩余未闭合 = ③ P1-03/P1-04（用户裁定押后）+ B4 payload 命名空间（独立一轮）+ P1-07 剩余（5 个未豁免 CVE、required checks）+ P2-01 generation 可倒退；①② 的收官判定权在 Codex 四轮复核**
    11	- 📊 **CI 状态（⛔ 不落盘 run 号/通过数——以 `gh run list --limit 3` 实查为准）**：定性事实=Tests 双版本绿（含本轮 +5 契约文件：snapshot_v3/hostile_env/tombstone/vault_admission/real_entrypoint）· **Dependency Audit 红**（5 个未豁免 CVE，pillow 修复被 moviepy `<12.0` 卡住）→ 整体 failure · branch protection 404 未设置、rulesets 空 — required checks 前提不满足
    12	- ✅ **已交付且经复核确认通过的**：compose 地雷 6 份处置 + 权重三方 md5 一致 · A-9/A-4 索引边界（含根级 casefold 精确排除、深层同名保留）· E-2 快照脱敏投影（缺版本/v1 且结构正常者强制迁移 + 原子发布不产生半截 JSON）· 配置缺文件/语法损坏不再回旧方向性权重 · CI 失败传播（两次远端红灯验证）· D-2 重数 92 条 + 无自动 replay consumer · A-1 语义死链改指 08-02 文档 §施工顺序与工期
    13	- ⚠️ **已知不实表述已撤**：不是「T1-T7 全完成」（E-3 产物丢失，经裁定移出验收范围）· D-2 根因**不是**"16998/正文撑爆"而是 schema/prompt 固定开销拟合截距 ~16861 已超 16384 窗口（分片对 71/89 条无效）· mastery 契约锁现为 **12 条**非 8 条 · 「92 条永久搁浅」应表述为「无自动出口，人工可恢复性未知」（未验证原始来源仍可取）
    14	- 📋 **其它遗留**：重写 `test_memory_service_contextvar_leak.py`（守护 P0 跨 vault 泄漏，现被 CI `--ignore` 隔离）· 全量 tests/ 跑不完的根因（本地串行 1h03m 未完）+ xdist 收集不确定性 · 四个休眠 worktree 的 `docker-compose.yml` 仍为未提交 `M`，待收回 · A-8 授权与 E-3 移出范围仅记录在 `0ff6876c` 新增文档中，**仓库无法独立验证**（Codex 裁为 UNVERIFIABLE，需用户本人确认闭合）· 主仓 `2c5a4683` 混入 `session-end-archive.py`（已裁定不修正历史）
    15	- ⚠️ **开工前必读**：① 动 board manifest 快照时注意 `write_snapshot_if_changed` 内已有 `_project_for_snapshot`，**不要在 `full` dict 上就地改**（`:716` 契约：live 与快照共用同一 state）② mastery 的 `_search_via_memory_service` 是 **vault 级语义补充召回、不是 node 精确读**（Tier1 映射已丢弃 attributes/node_id）；真正的精确读是 `graphiti_memory_reader.py` 的 `read_node_tips`/`read_node_errors`，但需要 `CanvasRAGState` 里没有的真实 node_id ③ 扩 CI 覆盖面前先解决「全量测试跑不完」，别直接加文件
    16	
    17	**上一状态**（2026-08-17 · **R10 复审 11 项 (P0×1+P1×6+P2×4) 全部处置完毕 · 收官门解除 · 8 commits + 真实 Neo4j 验收门 6/6 + 证据包落盘** · PLAN `P0-SYNC-ISO-2026-08-17`）:
    18	- ✅ **R10 复审处置全清**（回应文档 `_bmad-output/审查/2026-08-17-R10复审11项发现-处置回应.md`，证据包 `r10-evidence-2026-08-17/`）: P0-01 vault 身份注册表（垃圾输入 422 / 首claim绑定 / 碰撞 409，端点实测四面全过，生产桶已用真名 `canvas-vault` 预注册）· P1-01 commit 后才 ACK（回滚段整段失败）· P1-02 edge 独立事务 · P1-03 exam 空写如实（RETURN 校验+fallback 拒写+ok/partial/error 分级）· P1-04 回滚先建旧后删新+预检 · P1-05 歧义 census blocker · P1-06 读侧五文件 12+ 站点收口（等值 OR `__` 终止前缀，:Subject 元数据 by-design 全局有测试锁）· P2-01 边关系唯一约束（现网约束 3→**5 条**）+ stale 边清理 · P2-02 schema gate（启动验证+确认缺失拦写 503）· P2-03 真实 Neo4j 验收门 `tests/integration/test_sync_real_neo4j_gate.py` **6/6**（双 vault 写删/poisoned-tx/边不连坐真回查/stale/注册表碰撞）· P2-04 JUnit 112 passed + live-state.json + SHA 清单
    19	- Commits: `05cd1512`(核心写侧)/`c9ab31ca`(读侧)/`d8c4ea9c`+`8006d3ed`(迁移加固+集成门，前者 subject 被 commitlint 长度限占位、注解补正)/`7ba4a4b2`(conftest 注册表 stub)。容器已重启，gate 启动日志 `canvas_schema_gate_ok required=3`
    20	- ⚠️ **本轮自曝并修掉**: 单测经真实注册表污染生产注册行（认领成 `canvas_vault`，真插件发 `canvas-vault` 将必 409）→ conftest autouse stub + 现网修正 + 复跑零污染
    21	- 📋 挂账: 插件侧持久化 vault UUID（增强项）· 迁移脚本原子性（gate 已兜底）· verification 两处委托侧 scope · canvas.py:548 显式线程化 group
    22	
    23	**上一状态**（2026-08-17 · **P0-1 /sync/batch 跨 vault 隔离 ✅ 全链收官：4 commits + 审查处置 + --apply + 容器重启 + 双 vault E2E 实测通过 + 金集 34/34** · PLAN `P0-SYNC-ISO-2026-08-17`）:
    24	- ✅ **E2E 双 vault 实测全过（2026-08-17 用户批准后执行）**: 同 entity_id 两 vault 各写一份互不覆盖（Neo4j 实查 2 节点各归其组、title 互异）→ vault_a 删除只删自己、vault_b 存活 → 测试数据清零、库回 11 节点原状；缺 vault_id → 422、空白 vault_id → 422 双验证；金集 board manifest 34/34 对照面零回归。`--apply` 已跑（回填 0 行如预期，3 条复合约束 SHOW CONSTRAINTS 在位），容器已重启（挂载确认 /app=worktree backend）
    25	- 🐛 **C4 `79ea0e41` E2E 抓获存量炸弹**: 三条 upsert 的 `SET ... ON CREATE SET` 是非法 Cypher（Story 1.5 原始写法即错！路由无调用方+单测 stub tx.run 从未被真实 Neo4j 校验）→ ON CREATE SET 提到 MERGE 后 + 3 条子句顺序教训锁。**即：/sync/batch 的 upsert 从 Story 1.5 起就没在真实 Neo4j 上成功写入过任何东西**
    26	- ✅ **C1 `32e9e29c` 写侧闭环**: SyncBatchRequest.vault_id 升必填（缺失 422，唯一调用方 DEPRECATED Tauri 前端属预期）; sync.py handler 显式接 resolve 返回值 → `to_physical_group_id` → `process_sync_batch(request, group_id=物理gid)`; 六条 Cypher MERGE/MATCH 键全部变 `{id, group_id}` 复合键（`_delete_board` 级联双侧都带 group）; canvas_projection_sync/exam_service_ext 三方共键同批切换; 新 `test_sync_group_isolation.py` 10 条**行为断言**（红灯先行，检查 run_calls 实际 Cypher+参数，教训锁: wave5 静态断言逃逸）
    27	- ✅ **C2 `496a2147` 迁移件**: `migrations/003` 五段式 + `scripts/migrate_canvas_group_isolation.py`（--dry-run/--apply, ⚠️ 不复用 group_id_migration_service 的 IS NOT NULL 扫描器）+ 11 条脚本测试
    28	- ✅ **现网 dry-run census 已跑（只读）**: NULL 三 label 全 0 / CanvasBoard label 不存在（库里 11 CanvasNode + 9 CANVAS_EDGE 全在 `vault__canvas_vault`）/ **SHOW CONSTRAINTS 为空 = migrations/001 从未在 7691 生效过** → --apply 实际变更 = 纯新建 3 条复合约束，回填是 no-op
    29	- ✅ **零旁路破坏已证**: stash 基线对照，HEAD 与修复后失败集逐条一致（19 条全存量: auth Settings 校验器 / exception P0-2 fail-closed / wave5 tips 静态断言 / projection 旧签名 / qa_38_6×5 / story_38_8×1）
    30	- 🔒 **[Code-Review] 独立对抗审查已收官**: APPROVE-WITH-FIXES；核心修复被证实无漏（六条 Cypher 全带键 / 物理格式链闭合 / 无 cypher_with_group_filter 误用 / 无 ContextVar 依赖 / 全仓无旁路写入点，11 条候选证伪）。F1 HIGH（exam sync-node 边写入空匹配谎报 edge_created=True）+ F2（迁移 edge 回填不继承端点 group）+ F3（空白 vault_id 绕必填）已在 **C3 `ad82529a`** 处置并加行为测试；F4（verify_targeted_exam_chain.py 裸 id MERGE）/ F5（DEPRECATED 前端 sync-engine 无限重试）/ F6（head(collect) 非确定边角）+ **exam sync-node vault_id 必填化（F1 根治）** 挂账 Phase 2
    31	- ⏳ **收尾两步（等用户批）**: ①census 过目后批 `--apply`（实际=纯新建 3 条复合约束，回填 no-op）②**重启 backend 容器**（Dockerfile 无 --reload，代码不重启不生效）→ 双 vault curl 最小验收（两 vault 同 entity_id 写 → 两节点; 删其一 → 另一存活）+ targeting_material_service 出题链正向验证
    32	- 📋 **挂账 Phase 2（按 6-8 项/轮递审批）**: 读侧 10+ 处 group 过滤（recommendation_service:167/176/192/227/242、verification_service:2175/2208 by-name、question_generator:951、cross_subject_bridge:153、subjects.py:64/234）· cypher_with_group_filter() MERGE 适配 · Graphiti 记录本轮 [Decision]/[Code-Review]（本 session 无 graphiti MCP，欠账）
    33	
    34	**上一状态**（2026-08-17 · **双外审收官（ChatGPT+Codex 盲评交叉）· 用户 8/8 裁决全批 · 下一步=P0-1 修复方案** · PLAN `CODEX-ABSORB-2026-08-17`）:
    35	- ⛔ **新 session 第一件事**: 进 Plan Mode 为 **P0-1 `/sync/batch` 跨 vault 裸 ID 写删**单独出修复方案（选项: 全部 MATCH/MERGE/DELETE 键补物理 group_id vs 临时禁用路由），用户确认后再实施、不与其他修复混提。证据: `[WT] sync_service.py` 全文 grep group 零命中、:358 裸 `MERGE {id:$entity_id}`、:532-538 按 canvasId 级联 DETACH DELETE、sync.py:101 ContextVar 注入后执行层从不消费。⚠️ `cypher_with_group_filter()` 对 MERGE/CREATE 生成非法语法，禁止机械套用；方案必须含 MATCH/MERGE/DELETE 三类双 vault 隔离测试
    36	- ✅ **用户 8/8 全批**（R9 批注逐字）: ①P0-1 方案先行 ②E-2 快照选 **A**（只存投影安全面+秩数值，MEDIUM-2 悬案定案）③执行序改 Codex 8 步（P0 止血→数据边界→可信基线→证据修复→安全写入基建→分批落地→价值验证→缓行）④审批每轮只递 **6-8 项** ⑤A-2 扩容: mastery 提交前并入 tiktoken 断网兜底（compression.py:46 只捕 ImportError）+ nodes.py:97 timeout 200ms→按实测校准，WT 代码与 MAIN/.gitignore **分 commit** ⑥D-2 先按真实路径重数 DLQ（live=`WT/data/dead_letter_episodes.jsonl` 仅 1 条；`WT/backend/data/` 92 条为陈旧文件）⑦B-2 广度回顾先做**薄版 MVP**（只新增回顾报告文件，零改原白板/YAML，真实板试跑用户说「有帮到」再扩）⑧E-5 Dashboard webUI 入缓行区
    37	- ⛔ **拓扑修正（Codex 发现，已入记忆）**: compose `./data:/app/data` 子挂载**遮蔽** `backend/data/` → 容器内 reference_config 读 `/app/data/…json`（不存在）走 **fallback 旧权重**（videos 1.5/1.4）；权重 split-brain 实为三方（容器 fallback / 宿主脚本新值 / MAIN 旧值）。修复归 8 步序第 3 步「可信基线」
    38	- 未提交变更（有意，对应⑤）: `backend/lib/agentic_rag/mastery_injection.py` 修复 + `backend/tests/unit/test_mastery_injection_memory_contract.py` + `MAIN/.gitignore` raw 行
    39	- 关键文档: Codex 报告 `_bmad-output/审查/2026-08-17-Codex对抗审查-独立裁定报告.md` · 吸收+逐条复核+8 项裁决 `_bmad-output/审查/2026-08-17-Codex裁定-吸收与两家交叉对照.md` · 通俗版+用户批注原文 `_bmad-output/研究/2026-08-17-批注回复-R9-八项裁决通俗解释.md` · 审批单（待按 8 步序重排 + 用户旧批注待合并去重）`_bmad-output/研究/2026-08-16-设计讨论书-待批事项完整汇总-逐项审批单.md` · 事实基线（待按吸收文档 §二 打 5 处补丁）`_bmad-output/研究/2026-08-15-全项目现状核实-设计说的vs代码做的.md`
    40	- 事实勘误随手账: 审批单确认点 ≥29 非 21 · S2.6 mini-UAT 实为 **3 勾 2 未**（非四条待签）· gen_excalidraw_v3.py 不在仓内（仍在 session scratchpad，会丢）· doc_type `primary-record` 族在 TYPE_WEIGHTS **整族未接线**（两种写法均落 0.5 fallback）· `_待处理`/`_archive` 无索引排除规则（→ A-9 必须前置于 B-1/C-1）· 批注格式已到**第五代** `**User ：`/`**User 修正：`
    41	
    42	**上一状态**（2026-08-11 · **阶段 2.6 导航改造施工完成 · 金集 34/34 + 协议校验 35/35 + M1-M4 全达标 · 待用户 mini-UAT（3 勾 2 未）** · PLAN `RAG-S2.6-2026-08-11`）:
    43	- ✅ **T0 落点校准**: live vault = `canvas-learning-system/canvas-vault/`（`.env` CANVAS_BASE_PATH，Obsidian/Claudian 实读）；纪律 = **改 live → 定向文件级同步 worktree → 每批末 `diff -rq`**。⛔ 禁整目录同步（worktree vault 缺 CS188/CS189 与 6 张检验白板、却多 TestConceptA/B fixture）。**计划的「5 份 skill 未入 git」前提证伪**：那是 main 分支视角，本分支 8 份早已全部入库（04-17~07-30），裁定门自动消解
    44	- ✅ **T1 backend 两字段**（commit `ec9c6849`）: `pick_hint.pick_rank`（板内**可考察**候选秩，排序键 `(pick_score, node_id)`；⛔ 只覆盖非占位——占位若占掉 rank1 消费侧过滤后就扑空；在 `_carve` 而非 scan 赋秩 → 历史快照降级态也有秩）+ `past_question_digests[].score_scale`（⛔ 不是自由文本槽位：「数字–数字」形状白名单 + 40 字硬截断，不合形状降级定长文案；缺字段 → `1-4 (1=最低) [推定]`，DD-13 不把推断说成声明）。契约 46→52 绿、金集 32→34、全量 regression 393 passed、延迟 6.1/2.6/2.5ms、exam payload 4.63/6.60KB
    45	- ✅ **T2 Concepts 视图化**（commit `487d7851`）: 新 `canvas-vault/.claude/scripts/sync_board_concepts.py`（真相源=节点 `source_board`，零外部依赖，tmp+os.replace 原子写，比对**排除 synced 时间戳**否则 `--check` 永远报漂移）。⛔ 托管区间取**包络**（实测 6 板两种历史形态）且 **sentinel 存在时并进段内游离概念行**——插件 `appendBoardLines`(main.ts:2558) 插在**整段边界前**即落在 END 之外，只取 BEGIN..END 会留重复行（已按插件真实语义写模拟器复验）。写侧三点接线（ai-linked-doc Step7 / configure-whiteboard Step6 / quiz-answer 新 Step4c-bis）+ 模板换 sentinel 空块；⛔ 顺带修真缺口：configure-whiteboard Skill 此前**没给种子写 `source_board`**（plugin 有写、Skill 漏了）。双锁全绿 + doc_count 漂移×2 归零 + 关 Dataview 仍明文可读
    46	- ✅ **T3+T4+T5 八份 skill 接入**（commit `4244c021`）: canonical ROUTING 块 8 份逐字节相同（SHA `06b0167cc02c`），四平面 STRUCTURE/SEMANTIC/CONTENT/EXAM + HARD-NAV-1..4 + 每份 PLANE-BINDING 5 字段。旗舰 start-exam-board Step3 **19-26 次 → 1 次**、Step4.8 **零工具调用**、Step4 折入 calibration 删 Step5 独立 Grep、Step7 回执要求逐行照抄 `pick_rank`（可外部机械比对的锚点）；⛔ DD-13 修正 HARD CONSTRAINT #1 名实（澄清 HARD-21 管语义检索、与结构检索无关）；⛔ FALLBACK inline python 补 `effective()`——考察链是四方里唯一漏掉闲置折旧的一方（用户裁定 3）。configure-whiteboard Step4.2 全库唯一 O(节点数) 全节点 Read 循环 15→5 次；study-question §3.0 / chat-with-context 开场前**条件触发**限域（⛔ HARD-11/17/21 一字未动）；exam-quick/quiz-answer/node-chat 各写明**为什么禁用 STRUCTURE**
    47	- ✅ **验证四层**: 校验器 `check_skill_routing_block.py` **35/35**（C0 全集/C1 逐字节/C2 硬约束齐/C3 绑定自洽/C4 **工具面⇔绑定**/C5 FALLBACK 成对不嵌套）· 探针 `run_skill_navigation_probe.py` **M1-M4 全达标**（⛔ 不模拟 LLM，真 vault 真文件真字节，旧基线取自迁移前 .bak；M1 median 1→0 / M2 median 7.5→1 / CS188 板 **21→1 次**）· 真机 E2E 三板 · **降级路径与主路径逐行相等（三板 1e-6）**
    48	- 🐛 **顺带修的真 bug**: `csm-tutoring-unit-credit` 有 `source_board` 但不在 `## Concepts` ⇒ 2.6 前读 Concepts 选点的 skill **永远考不到它**；T2 从写侧根除后两条路径都能选到（不是只在主路径绕过去）
    49	- ⚠️ **金集 G3 期望值同批改**: 2.5 把 CS 61B `frontmatter_only: ["csm-tutoring-unit-credit"]` 封成期望（「漏记告警必须亮」），T2 根除后归零 → 改 `[]` 并 `--update-baseline --reason`（修复带来的期望变更，非回归）
    50	- ⚠️ **登记 backlog**: worktree 的 `canvas-vault/原白板`、`节点` 是**陈旧副本**，在其上跑迁移会得出对 live 错误的派生值 → 白板内容**不入库**（已回滚 HEAD）；live vault 白板改动保持未提交 + `.bak` 存于 `.claude/cache/rag-s2.6-concepts-backup/` 可回滚。真正修法是把 live 内容同步进 worktree，不在 2.6 范围
    51	- 🔒 **[Code-Review] 三视角独立对抗审查 24 条发现全部处置 + 全部加回归锁**（每条先自行复现再改，未直接采信）:
    52	  - ⛔ **C-H1 真实数据损坏（最严重）**: `managed_region` 取 min..max **包络** ⇒ 用户在 `## Concepts` 段手写的备注/代码块/`---` **被静默删除**（完整触发链已跑通: 手写 → 下次 Cmd+Shift+D 时 plugin 在段尾追加裸行 → 手写内容夹在中间被连坐）→ 重写成 `managed_lines()` **逐行**标记受管行
    53	  - ⛔ **HIGH-1 泄漏**: `score_scale` 形状白名单**只有头锚没尾锚**(`.match()` 无 `$`) ⇒ `1-4 反例 diag(-1,-1)…`（**G6 金集禁串**）整串原样透出 → `fullmatch` + 收紧文法 + 先验形状再截断
    54	  - ⛔ **HIGH-2 静默劫持**: `mastery_a: .inf/.nan` ⇒ nan 比较恒 False 让 Timsort 保持输入序，投毒节点吃掉 `pick_rank=1` 且 `parse_errors` 空；自查另发现 exam JSON 吐**裸 NaN = 非法 JSON** → `_num` 加 `isfinite` 门 + 显式上报 + 秩过滤 + 严格 JSON 断言
    55	  - ⛔ **D-HIGH-1 我自己的方法论错误**: 上一版「降级路径逐行相等」验的是**我修好的路径**——SKILL 的 Grep 当时没取 `last_examined`，闲置折旧在降级态整体失效 → 补字段 + **写脚本从 SKILL 正文抠出 Grep 与 python 直接执行**重验（三板逐字段相等，`idle=16.9d` 是折旧生效的证据）
    56	  - ⛔ **C-M6 已在真 vault 生效**: `mkstemp` 恒 0600 + `os.replace` 继承 ⇒ 6 块白板权限被从 0644 静默改成 0600 → `os.chmod(tmp, 原 mode)` + **已改回并复验不再复发**
    57	  - ⛔ **D-MEDIUM-5 校验器只数信封不看信**: 掏空降级块/改坏 import/新增裸调用/把降级反转成「停止并叫用户起服务」六种腐烂全判绿 → 加 C6(按小节校 HARD-NAV-3)/C7(ast.parse + import 符号存在)/C8(禁中止语义)，**35 → 59 项**
    58	  - 其余: MEDIUM-1 G8 子串判定被 `[推定]` 前缀绕过→改闭集 / MEDIUM-3 SKILL 把 manifest 划进可信面→新增 **HARD-ISO-5b** / D-HIGH-2 降级把占位也编秩致秩号错位→排序前剔除 / D-HIGH-3 反向引用 regex 未 `re.escape` 致含括号节点整批漏检→已修 / D-MEDIUM-4 缺 Concepts 段时 exit 0 还说「已同步」→抛异常+退出码分层 / C-H3 frontmatter 自由文本被逐字写进白板→只认真 wikilink / C-H4 与后端 7 条语义分歧→逐条对齐 / C-H5 批次非原子 / C-M7 无 fsync / C-M9 行尾归一 / C-M10 doc_count 只改首处 / C-M11-13 断链·孤儿·多 sentinel 静默→全改成告警且 `--check` 红 / C-M14 `.bak` 二次覆盖
    59	  - **复验**: 协议校验 35→**59/59** · 全量 regression **425 passed**（393→+32: 契约 46→64 + 新 `test_sync_board_concepts.py` 20 项）· 金集 34/34 · 探针 M1-M4 全达标 · 脚本 `--check` 幂等无告警 · ruff 全绿
    60	- ⚠️ **待用户裁定（我没单方面改）**: 审查 MEDIUM-2 —— `view:"exam"` 调用**本身**把全量禁项原料明文落盘到 `<vault>/.claude/cache/`（真 vault 那份 22KB 快照含 G6 禁串明文，出题 agent 有 Read 权限）。本轮只做 prompt 级 **HARD-NAV-5**（禁读 `.claude/cache/`）+ gitignore；彻底修法二选一: **A** 快照只存投影安全面（代价: 降级态 study 视图丢 tips/errors）/ **B** 快照移出 vault 到 backend 侧（代价: 反转 2.5「落 .claude 双黑名单」的架构决定）
    61	- 📋 **用户 mini-UAT 卡**: `_bmad-output/验收单/Story-RAG-S2.6-导航改造-mini-UAT.md`（DoD-3 七段 + 4-A/4-B 双段，段 4-B 禁词 0 命中 / 4 条全用「我做 X → 我看到 Y → 我感觉 Z」句型；⚠️ 首行提醒 `Cmd+Q` 完全退出重开 Obsidian —— MCP/skill session 缓存 2.5 踩过两次）
    62	- ⏭ **下一步**: 用户 mini-UAT 签字 → **阶段 3**（退役 8765）。2.6 明确不做: structure-navigator 子代理（用户已砍，回退阈值：单次 skill >3 次 manifest 调用或单板 exam JSON 常态 >8KB 则 2.7 重议）/ 批量 candidate 端点（manifest 已是）/ backend `calibration_gap` 字段（折入 skill 抽取器）/ 改前端插件（DD-12）/ 改 `score_scale` 写侧（vault 已有）/ 砍 study-question HARD-11/17/21 / LLM 查询改写 / 1.5 稳定 ID / Neo4j 投影
    63	
    64	**上一状态**（2026-08-11 · **阶段 2.5 Board Manifest 施工完成 · 金集 31/31 全绿 · 待用户 mini-UAT** · PLAN `RAG-S2.5-2026-08-10`）:
    65	- ✅ **T0 依赖+迁移**: python-frontmatter 依赖洞首 commit 修复（364d2b39, docker build 验证过）; vault 迁移用户四项签字（删 TestConceptA/B/C + csm-tutoring 归 CS 61B + 考察产物移检验白板 + main 直接 commit 44113f54）→ **14/14 节点全员 source_board, 孤儿清零**; T0.5 特征值 Concepts 实测 3 条定案（Plan agent「空 section」说法证伪）
    66	- ✅ **T1-T3 已 ship**（worktree commits 870ca8f5/55f9421e/bcdde1ad）: board_manifest_service（ManifestDataSource Protocol + mastery 四态归一化 + is_stub + dual_source_gap 窄解析 + pick_hint 内联 decay_beta 1e-9 契约锁）; exam/study 双视图 Pydantic 投影（**exam 禁项=模型结构性缺字段**, live/快照 serve 共用唯一投影点）; 快照三态降级 `.claude/cache/board-manifest/manifest-v1.json`（generation 变更才重写+原子写, live→snapshot→error 诚实申报, 真实环境实测退快照+恢复全过）; HTTP `POST /api/v1/boards/manifest`（prefix=/boards 防 wildcard, require_internal_api_key + vault fail-closed 409）+ MCP `get_board_manifest`（第 6 只读工具, 空 body 防 P16, quarantine 测试 5→6 同步）
    67	- ✅ **T4 金集**: `scripts/run_board_manifest_regression.py` + `board_manifest_gold_set.yaml` 31 条硬禁通道（G1 成员×6/G2 孤儿/G3 gap×3/G4 字段×10/G5 历史×3/G6 泄漏×8 含合成投毒）**宿主+容器双姿势全绿, 基线封版**; 契约测试 41 绿; 全量 regression 381 passed 零旁路破坏; 实测延迟: 列板 104ms/exam 79ms/study 61ms（预算 <300ms）
    68	- 🐛 live 实测抓 bug: BUG-361BD6FC（YAML datetime 透传 tips/error_candidates 炸快照 json.dumps）→ _json_safe 深度清洗+回归锁
    69	- 📋 **用户 mini-UAT 卡**: `_bmad-output/验收单/Story-RAG-S2.5-BoardManifest-mini-UAT.md`（技术三条 Claude 已全部代跑留档, 用户只验 Claudian 产品体验; ⚠️ 宿主改目录名容器 ~10s 才可见=VirtioFS 缓存）
    70	- 🐛 **UAT 两轮实锤两个 MCP 面 bug（已修复+回归锁）**: ① 旧 Claudian session 缓存 5 工具列表（server listChanged:false 不推变更, JSON-RPC 实测 server 侧 6 工具一直在列）→ 用户侧 /mcp 重连即可, 非 bug; ② ⛔ `input: X | None = None` P16 模板让 requestBody 变 anyOf → fastapi-mcp 展不开 properties → **MCP inputSchema 参数全丢**（Claudian 只能无参列板, board_id/view 调不出）→ 改 `Body(default_factory=...)`（该模板只适用空输入模型, check_backend_health 恰好无参才没炸）+ quarantine 新增参数面回归锁; E2E 复验: tools/list 三参数齐 + 带参单板 exam 调用 3 节点/6 历史 + 空参列板 P16 不炸
    71	- 🔒 [Code-Review] 独立对抗审查（E2E 复现式）**3 HIGH / 3 MEDIUM / 5 LOW → 全部处置, 复验 32/32 全绿**: ⛔ H1 orphans 回显通道（source_board 塞定义全文进 exam 视图, 已复现）→ reason 定长枚举文案+raw 截断 120+模型 max_length 门; ⛔ H2 parse_errors 回显（last_examined repr 无界+纯 Python yaml loader str(e) 引用原文行含 correction 禁串）→ _safe_err 去内容化（异常类型+行号）+repr[:80]+模型 200 字门; ⛔ H3 untrusted 标量炸投影（`doc_count: 大约五个`/`title: 2026` → ValidationError 500 整端点含列板）→ _bounded_str 类型归一×7 字段+双暴露面 ValidationError 纵深兜底; M4 digest 吸入相邻 [!feedback]/[!hint] callout（可含正确答案）→ callout 边界终止收集; M6 #heading 锚点+大小写敏感→假孤儿（喂 H1 通道）→ resolve 剥锚点+boards_ci casefold 匹配; M7 金集合成A恒真条件（自比较）→ 改「挖掉 reason 槽位后 0 命中」; M8 禁串无正向对照会静默腐烂→禁串必须仍在 vault 源文件+G5 digest 非空对照（金集 31→32 条）; L 批: 快照 tmp 唯一名防竞态/load 快照 schema 必备键校验/exam_board_count 恒用 full 历史/信封字段统一截断/set_current_subject_id 移到 fail-close 之后。审查确认: 投影穿透 E2E 失败（防线真实）、快照双黑名单成立、serve 路径唯一、pick 数学锁死、无 DD-03 违规。新增回归锁 6 条（契约 77 绿）
    72	- 📌 顺手发现: **8 个未剖析占位节点**（CS188×7+特征值 Eigenvalues-special, is_stub 如实标注）; doc_count 漂移×2（CS 61B 声明1实际2/递归声明0实际1, 归 2.6 写侧）; 金集 shadow 分区已作观察面
    73	- ✅ **UAT 产品体验项第三轮实测通过（待用户签字）**: Claudian 单次带参调用拿全量拆解并直接给学习诊断（beta/score_only 双轨判「板有没有真在用」= manifest 立足点的活证明）
    74	- 📌 **2.5 收尾 backlog（新增 3 条）**: ① digest 裸 score 无量纲标注被消费侧误读成满分（实际 1-4 制 1=最低; 加 score_scale 字段属 exam keyset 契约变更, 走 --update-baseline 流程, 归 2.6）② 选点贪心锁定观察（枢纽 μ 极低时叶子排不上; 注意 Eigenvalues-special 是 stub 本就该跳过）③ Concepts 行内 "(mastery: 0.30)" 快照文案与真值脱节（2.6 写侧视图化处理）
    75	- ⏭ **下一步**: 用户 mini-UAT 签字 → **2.6**（`## Concepts` 写侧视图化 + 8 skill 接入 manifest 替代 Grep 拼图）; 2.5 明确不做: 1.5 稳定 ID（字段已标注 basename_v1）/ Neo4j 投影修复（backlog, Protocol 接口已留）/ 写端点 / exam 承载 misconception / FSRS 字段
    76	
    77	**上一状态**（2026-08-10 · **阶段 2 收官 ✅ 用户 UAT 四步全过** · 下一步: 九阶段路线 2.5/2.6 · PLAN `RAG-S2-2026-08-09`）:
    78	- ✅ **阶段 2 UAT 通过（用户实测四步全过 2026-08-10, 记录在卡）**: ①手写优先+dedup+wikilink 7/7 真实 ②vault 外主题零编造（`ce_gate_all_filtered` 标注实锤）③search_notes 与 hook 同源（加权分量纲 0.55-0.60 实证）④检验白板零泄漏（弃答闭环记录/原白板导航均为设计特性非泄漏）。卡: `_bmad-output/验收单/Story-RAG-S2-阶段2-强化fastpath-UAT.md`
    79	- 📌 **UAT 新观察项**: 「特征方程」query 注入 7 条 RL「特征表示」— 中文共词假匹配 CE 门未杀（已知 CE 盲区家族), Claude verifier 层自行绕开转 search_notes; 归 CE 盲区 backlog 追踪
    80	- ✅ **三决策用户已裁定（全采纳推荐项）**: ① **f06/h07 移 shadow**（金集 v2, 58 条; 基线: MRR 0.7889/nDCG 0.7121/交付 84.91%/污染 38.60%/FPR 6%; 红档只剩 f04/z04 真实能力缺口; file_locate 意图路由 backlog, exam_board 任何方案绝不放行）② **f04 扩池不做**（扩池仅 file 级 rank4、+31% 延迟 — 根因段落级召回, backlog 等 chunk 侧补强）③ **[!note] STRIP 维持现状**（census 零误伤实锤）
    81	- ⏭ **下一步**: 九阶段路线（0→1→1.5→**2 ✅**→2.5→2.6→3→4→4.5）进 **2.5/2.6**（开工前重读九阶段路线定义 `_bmad-output/研究/2026-08-02-RAG修复计划-用户审阅版.md` §施工顺序与工期 L93 — A-1 修正于 R11-BATCH2: 原指 `2026-08-09-RAG阶段2-强化fastpath实施计划.md`，该文件存在但仅 36 行、是阶段 2 的单阶段计划，不含九阶段路线，反而把 2.5/2.6/4.5 列入「明确不做」）; 阶段 2 backlog 汇总: CE 盲区类（a01/z02/z05/特征共词）/ f04 段落级召回 / file_locate 意图路由 / extended 分支 taint / MCP top_k 漂移 / tier-2 legacy exam_board / RETRIEVAL_RERANKER_* compose 白名单
    82	- ✅ **T6 验证收尾完成**（17-agent workflow: 4 路验证 + 3 lens 全链路对抗审查 + 逐 finding 证伪）: 金集终验通过 + shadow 空（设计态）; live 实测 9 项全 PASS（hook 四态/MCP confidence/考察隔离/M6 410/refresh-changed 存活/18012 双向可达）; **[!note] STRIP census 实锤零误伤**（206 md 仅 1 处且嵌套 error-candidate 内被 EXTRACT 保留; info/video 55 处全系统模板）; **vq-f04 扩池实测**（50 池 file 级 rank4 但「烘」段落仍不召回, 延迟 +31%）; **vq-f06/h07 结构性死档实锤**（期望文件全 doc_type=whiteboard 被查询侧排除, 反事实去排除 rank1 立即回归, 选项 B>A>C 待用户裁定）
    83	- 🔒 [Code-Review] T6 全链路审查 **8 CONFIRMED / 2 REFUTED → 全部处置**: ⛔ **HARD-ISO live 泄漏**（vault_notes_retriever 默认排除表漏 exam_board, 经无鉴权 /api/v1/rag/query + agents.py 六处可达 → 补齐; react_agent/tool_executor/agent_graph 三条 flag-gated 链同批纵深补齐）; **fts_confirmed 名实颠倒**（_rrf_score 写给所有融合行, dense-only 恒 True/真词法命中反 False → _rrf_fuse 新 _fts_hit 通道标记 + 白名单 + svc 公式改 `_fts_hit and not _fts_only`, 仍遥测-only）; **检索层故障吞噬纵深**（_search_internal 全分支故障 raise 受 enable_fallback 门控[默认 True 调用方行为不变] + open_table 失败 raise + hook singleton 关吞噬/init 失败不缓存 + 空交付文案不再主动断言「检索正常」）; ⛔ **elbow telescoping = 三轮金集 A/B 裁决保留 T4 行为**（审查数学观点成立, 但两种修复均被金集打回: 全量序列 floor → 污染 39.83→57.38%/FPR 8%; dedup 后门前 floor → 48.25%/8%; +1.8pp 命中换不回 +8~17pp 污染 — 门后 telescoping 截断是净正收益保守护栏, 数据与翻案条件锁进 test_gate_thinning_elbow_is_deliberate_t4_behavior）; REFUTED×2: react_agent/agent_graph「拨真即泄漏」不可达（仍随批纵深补齐排除表）; LOW backlog: extended 分支无 taint / MCP top_k 参数漂移 10vs15 / TYPE_WEIGHTS concept 死键
    84	- 📋 **用户 UAT 卡**: `_bmad-output/验收单/Story-RAG-S2-阶段2-强化fastpath-UAT.md`（产品语言 4 步 + ⚠️ 问句/探针分两条消息坑已进模板）
    85	- ⏳ **三个待用户决策**（数据已备齐, 选择题形式问）: ① f06/h07 死档（建议 B 移 shadow 升 version）② f04 扩池（数据: 收益仅 file 级、grade3 不达、+31% 延迟 — 建议 backlog 等 chunk 侧补强）③ [!note] STRIP（数据: 零误伤 — 建议维持现状）
    86	- 金集（审查修复后复验）: 见 baseline history 最新条目; T6 契约锁 15 条 + 链统一 24 条全绿
    87	
    88	**上一状态**（2026-08-10 · 阶段 2 T1-T5 已 ship · T6 前 · PLAN `RAG-S2-2026-08-09`）:
    89	- ✅ **T5 链统一+诚实遥测已落地**: MCP `search_notes` fast path 改走共享后处理（`search_supplementary` + `include_content` profile, 生产参数 0.50/0.25）→ hybrid FTS+RRF/加权序/taint(含全文扫描)/空文档检测/源文件 dedup/CE 门在 MCP 链全部生效, score 量纲=加权分; **retrieval_confidence 双面注入**（hook XML 根元素 `confidence="high|medium|low|none"` 离散档 + MCP 顶层 `retrieval_confidence` 字段——⛔ pydantic 模型已声明防 response_model 裁剪; 裸分数不进 prompt 面, `ce_score not in xml` 契约保持）; **hook 降级失明修复**（client未就绪/5s超时/异常/空交付四分支注入 `degraded/reason/confidence` 标注 XML, exam-skill/system-op/短句跳过保持零注入）; **M6 incremental 端点 410 退役**（指引走 `/api/v1/index/refresh-changed`, 照 vault.py P0-3 姿势）; Step 0 vector 回退分支补 exam_board（HARD-ISO 旁路堵死）
    90	- ⛔ **T5 探针定案（勿翻案）**: `fts_confirmed` **不进交付门** — 垃圾 query n01 5条/n03 7条 raw≥0.50 全 fts=True（zh 常用词「节点/删除/平衡」FTS 命中）, 真命中 a01/z05 的 Fundamentals（appended 咖啡段）反而 fts=False → 词法双通道不可分, 只作 confidence 遥测（回归锁已铺）。h08/m04 真命中在 T4 门下已能过（dedup CE 证据合并 ce 0.204/0.027）; a01/z02/z05 仍丢, confidence 已能标注这类丢失
    91	- 🔒 [Code-Review] T5 独立对抗审查 2H/2M/2L → **全修**: HIGH-1 基础设施故障被吞成 ok_empty（fast client `enable_fallback=False` + `_two_tier_search` 两级全败 raise 走 search_failed + `_fast_path_search` embedding 预检恢复阶段0语义, 真实路径回归锁×2）/ HIGH-2 MCP 全文交付但 taint 只扫 300 字 snippet（content 挂载前移进扫描面, 交付面=扫描面）/ MEDIUM-3 tainted 材料 metadata 收窄（doc_type/source_type frontmatter 自由文本不随隔离材料外带）/ MEDIUM-4 enrich-context rerank 后 confidence 失真（摘除不渲染, 重算留待后续）; LOW-6 tier-2 legacy 表无 exam_board 排除 → backlog（env-gate 默认关, 暴露≈0）
    92	- 金集: **全指标持平 T4 基线**（recall 92.73%/MRR 0.7602/nDCG 0.6862/FPR 6%≤8%/交付 81.82%）门禁通过+基线已锁（交付命中持平=预期, Step 4 收复按计划退回遥测-only）; regression 324 绿+新契约 24 条; live 实测: MCP confidence 透出+CE 门生效（h08 只交付 节点/lecture 2 全文）、hook 空交付注入 `count="0" reason="ce_gate_all_filtered" confidence="none"`、非空注入 `confidence="medium"`
    93	- ⏭ **T6 验证收尾**: 金集终验+live 实测+对抗审查+用户 UAT 卡（产品语言; ⚠️ 问句/探针分两条消息的坑写进卡模板）; **待用户决策（勿擅自做）**: vq-f06/h07 whiteboard 排除与金集期望冲突（file_locate 放行 or 修订金集升 version）、vq-f04 扩池≥50（延迟代价）、`[!note]` STRIP 误伤面 census
    94	
    95	**上一状态**（2026-08-10 · 阶段 2 T1-T4 已 ship · T5 前 · PLAN `RAG-S2-2026-08-09`）:
    96	- ✅ **T4 dedup+CE 交付门已落地**: 新 `backend/app/services/retrieval_reranker.py`（长活 AsyncClient/MaxP 5×400字窗口/sigmoid/1.5s超时/3败熔断60s/env 链 RETRIEVAL_RERANKER_* 回落 GRAPHITI_RERANKER_BASE_URL）+ svc 接入源文件级 dedup（taint fail-closed 合并+CE 证据拼接）。⛔ **架构定案: CE 是交付判官不是排序器** — 两轮金集校准实证 CE 排序（纯CE/CE×权重）让 raw/ 转录反扑（手写占比 59.5→29/31%），排序保持 T2/T3 加权序；CE 门（floor 0.02，min_relevance=0 时不激活）杀垃圾+放行低 raw 正解（预过滤放宽 0.30，放宽行不占 top_k_max 配额）。金集: recall **92.73%** MRR **0.7602** nDCG **0.6862** 全升、FPR **42→6%**、交付污染 47.6→39.8%、交付 81.82% 持平 T3、rank1/2 同文件重复根治。基线已锁 3 轮（校准轨迹在 history jsonl）
    97	- 🔒 [Code-Review] T4 workflow 审查（45 agent, 3维find+双盲证伪, 21报12实9拦）→ **全修**: HIGH 池挤占（放宽行挤出 raw≥0.50 正解, 修后交付 80→81.82%）/ AttributeError 逃逸契约+绕熔断（畸形200封堵）/ 英文chunk 1200字盲区（MaxP 3→5窗）/ dedup 丢被合并 chunk CE 证据 / 单测隐藏网络依赖 / ce_gate_all_filtered 观测区分 / CancelledError 熔断记账 / 6 条新回归锁（含池饱和等价+半开恢复+XML 不渗漏）。contracts 26+chunk 21 绿, unit svc 55 绿
    98	- ⚠️ T4 已知边界（T5 靶）: CE 盲区类 query 交付丢失（h08「我做过哪些笔记」meta/z02 转述/z05/a01 — CE 分与垃圾区间重叠, 纯 CE 无解 → T5 fts_confirmed+intent 信号收复, `ce_gate_all_filtered` 日志信号已铺好）; vq-f04 需扩池≥50、f06/h07 是 whiteboard 排除与金集期望冲突（用户决策）、z04 稠密召回失败; 代码块原子 chunk >2000 字残余 CE 盲区; RETRIEVAL_RERANKER_* 未进 docker-compose environment 白名单（回落链可用, 加白名单需 recreate）
    99	- 手写占比@10 59.5→33% 与污染@10 24→37% 是 **dedup 度量语义重定义**（同文件×N 刷分终结, top10=10 个不同文件, 手写文件总数决定物理上限 ~35%）— 非质量回退, 基线 reason 已记录
   100	
   101	**上一状态**（2026-08-09 · 阶段 2 T1+T2+T3 已 ship（`25dc54a2`+`fcd34953`+`89d51dc9`）· PLAN `RAG-S2-2026-08-09`）:
   102	- ✅ **T3 chunk 改造已落地**（lancedb_client.py 单文件）: 段落级三级切分(段落→句子→子句)+overlap 段落化 / callout 三级分级(EXTRACT question/error/error-candidate 独立成块; STRIP info/video/note+"💬 围绕这个概念讨论"模板标记; KEEP 其余) / 模板样板 section 零 chunk / **考察文件 exam_question_id→exam_board 推断堵题面泄漏**(用户截图 rank3 考察文件已从检索消失, 索引唯一考察文件已转 exam_board) / 短块(<150tok)面包屑只留文件名 / line_start 补 frontmatter 偏移。金集: recall **90.91%**(+1.8pp) 假阳性 **58→42%** 污染@10 24.17% nDCG 0.6415(容差内) 交付 81.82% 持平; vq-a02 咖啡 rank 7→4, vq-a03 rank1 交付 9 条; 基线已锁(history 归档)。契约测试 21 条(组A-F), regression 全绿
   103	- 🔒 [Code-Review] T3 独立对抗审查 0C/1H/2M/5L → **HIGH-1(YAML 解析失败绕过 exam_board 推断=泄漏复活, 已修嗅探兜底)+MEDIUM-1(紧贴 callout 吞批注, 已修断块)+MEDIUM-2(占位误杀, 已收紧)+LOW-4(tiktoken 冷启动, 已降级兜底) 全修**+4 红线测试; 未修 backlog: LOW-1 超长 EXTRACT 降级切分丢 [!question] 标记 / LOW-3 [!note] STRIP 误伤面待 census 复核 / LOW-5 建议 exam-quick.ts frontmatter 标量加引号(前端, 勿混本批)
   104	- ⏭ **T4 dedup+rerank**（下一步）: 源文件级 dedup + 新 retrieval_reranker.py(复用 graphiti/rerank_client 连接池; ⛔512token 超限整请求 500 必须截断 400 字; 1.5-2s 超时回落原分; elbow 迁 sigmoid(logit) 重校准; 假阳性 42% 与 vq-f04/f06/h07/z04 四残留 query 是靶), 接入 supplementary_search_service 归一化后/elbow 前, env RETRIEVAL_RERANKER_BASE_URL 回落 GRAPHITI. T5 链统一+confidence。T6 审查+UAT(问句/探针分两条消息坑进卡模板)
   105	- ⚠️ 金集必须容器内跑 docker exec; force_rebuild 入口 canvas-meta/index/vault + X-CLS-Internal-Key; T1/T2 详情见 git log 与计划文档 `_bmad-output/研究/2026-08-09-RAG阶段2-强化fastpath实施计划.md`
   106	
   107	**上一状态**（2026-08-09 · 阶段 1 ✅ 用户完整 UAT 通过）:
   108	- ✅ **阶段 1 索引层验收通过**（测试卡 v2 全项: 新建 0.585/改写 0.648/删除三层清/大文件追加 3min 重索引）; MCP -32602 根治（mount_http+.mcp.json http, `d93631ac`）; 观测加固（相对秒数/逐task/excluded 计数, `a87f04ea`）
   109	- ⛔ **阶段 2 头号靶子实证: chunk 稀释** — 大文件尾部追加异质内容并入 598 字符主导 chunk → 相关度 -0.11~-0.17（独立小文件 0.648, 差 30+ 倍）→ hook 不可见。阶段 2 = chunk 策略 + rerank(18012) + doc_type 权重 + golden set
   110	- 📋 教训入卡: 问句/探针分两条消息（hook 词黑名单）; 语义零重合问法必须先实机校准（0.498 灰区实锤）
   111	
   112	**上一状态**（2026-08-03 · 阶段 1 已 ship · PLAN `RAG-S1-2026-08-02`）:
   113	- ⛔ **九阶段路线**（0→1→1.5→2→2.5→2.6→3→4→4.5）; 阶段 1 全落地: `vault_index_orchestrator.py` 统一五原语 + durable per-path pending（JSONL 意图日志+退避重试）+ watchfiles 事件加速 + 60s anti-entropy 扫描 + orphan sweep 收敛 + freshness 遥测
   114	- ✅ **live 实测**: 保存→可检索 **5-6s** / 删除→不可检索 **5s**（SLO 60s）; 索引冻结解除（3604→2174 行 100% 新写, Fundamentals 1→5 chunks, chunks/ 双份冗余清除）; 重启恢复 66 pending 实测; 抓获并根治 6 文件空产出永动循环 + status 端点 9.5s→0.009s
   115	- 🔒 [Code-Review] 0C/4H/6M/7L→**H1-H4+M1-M5 全修**（H1 embed 挂=假成功/H2 短写丢行/H3 DELETE default 抹全 vault 指纹/H4 事件循环阻塞+O(N²) persist/M1 毒文件退避/M3 路径穿越）; M6 增量端点收编+L6 NFC 挂账阶段 2; 契约测试 32 条（四组+5 审查锁）; regression 252 passed
   116	- 📋 **用户 mini-UAT（1 分钟）**: `_bmad-output/验收单/Story-RAG-S1-索引重写-mini-UAT.md` — 改笔记→1 分钟内 Claudian 引用新内容
   117	- ⏭ 阶段 1 后: 1.5 稳定身份 或 2 强化 fast path（rerank/golden set/配比治理）; backlog: M6/L6/传递依赖连坐锁/metadata 每请求新建 client
   118	- 📄 决策链（勿重新推导）: `_bmad-output/审查/2026-08-02-RAG检索设计对抗性审查-三问三答.md` → `…ChatGPT-RAG三P0审查吸收与验证.md` → `…ChatGPT-规模化结构检索终审-吸收与验证.md` → `_bmad-output/研究/2026-08-02-RAG修复计划-用户审阅版.md`
   119	- 🔒 已定裁决: 6 源管道退役出默认链（阶段 4 shadow 定生死）; quality=low 假信号废除; ~~path_map~~/~~configurable~~ 已证伪（正解 async router + `context=`, 属阶段 4）; 三平面架构=frontmatter 唯一可写真相源 / Neo4j 确定性投影 / Graphiti 时间记忆
   120	- ⏭ 阶段 0 后: 阶段 1 索引重写（开工前重读 ChatGPT 第一轮 §四）; 明早 9:05 Bark 推送有机验证勾 `Story-DAILY-REVIEW-PUSH` mini-UAT
   121	
   122	**上一状态**（2026-07-31 · 二轮对抗审查 P0 安全收口一二批落地 `7f63f6a3`+P0-3）:
   123	- ✅ **P0-0 端口收口**（四端口绑 127.0.0.1, LAN 拒绝）; **P0-2 MCP 写侧隔离**（19→5 只读, 14 隔离 410+遥测, 31 契约）; **P0-3 去 global vault switch**: /vault/switch 410 隔离（逃生=改 .env ACTIVE_VAULT+compose up, 审查抓出 CANVAS_BASE_PATH 文案错误已修）+ 插件 CTA/下拉下架改只读 + enrich-hook cwd→vault 推导（段名 NFC 匹配, 多命中回退）+ tips 写侧 vault_id 必填 + deploy-vault skill 死端点清理。两轮独立审查 APPROVE-WITH-FIXES 全修
   124	- 📄 审查链: `_bmad-output/审查/2026-07-30-全系统功能状态对抗性审查-三分类报告.md` → `2026-07-31-ChatGPT第二轮对抗审查吸收与代码验证.md`
   125	- ✅ **08-01 launchd 五腿全活**（`6de130d4`）: TCC 根因=plist 须显式 /bin/bash + python3.14 单独 FDA（用户已加 3 条 FDA; brew upgrade python 后 python 条目要重加）; memory-health/neo4j-backup（断 9 天后新 dump）/qwen/reranker/daily-review 全 exit 0; P0-6 恢复演练 ✅（118 节点/214 关系完整）
   126	- ⏳ **P0 余量**: ①用户装 Bark 贴 key（`~/.config/canvas-review/bark.key`, 明早 9:05 无 key 走本地通知 fallback）②P0-5 Tier B 观察期后物理删（+infra_tools.switch_vault 死函数、plugin activeVaultName 死字段）③P1: split-brain 文件路径 vault_id 化（多 vault 激活前必做）
   127	- ⚠️ 存量债: test_vault_id_changes_after_reload 环境依赖失败（stash 实锤非本批）+ 插件 7 个 source-regex 测试失败（HEAD 同挂）
   128	
   129	**上一状态**（2026-07-30 · FSRS-V2 真实到期调度全落地，与推送 MVP 同待用户 UAT）:
   130	- ✅ **FSRS v2 上线**: quiz-answer×fsrs_bridge 写 6 个 fsrs_* 字段（py-fsrs 6.3.1, 关 fuzzing）; 推送链 WHEN 化（due 过滤+放假消息）; Dashboard 到期接活; 幽灵调度器/schedule 端点/插件死命令退役（生产 404 实测）; 38 测试绿 + 审查 0 CRITICAL 8 项修复
   131	- 📄 决策: `_bmad-output/研究/2026-07-30-FSRS-v2-D0-决策记录.md`（映射四档 + WHEN/WHAT 分工）; UAT: `_bmad-output/验收单/Story-FSRS-V2-真实到期调度-mini-UAT.md`
   132	- 📋 Tier B 退役移交（未做）: /review/record + fsrs-state + history、MCP mastery 工具、review-suggestions +1 天写死、exam 回退链、WeightCalculator 死方法 — 清单见范围报告 §五
   133	
   134	**上一状态**（2026-07-29 · DAILY-REVIEW-PUSH 每日复习手机推送 MVP 代码全落地，待用户 UAT）:
   135	- ✅ ChatGPT 终审 CONDITIONAL GO + 本地模型栈 KEEP（不迁 MLX-VLM 不换 122B）→ 全部修正已吸收: `_bmad-output/审查/2026-07-29-ChatGPT终审吸收与代码验证.md`
   136	- ✅ 修订八步全落地: decay_beta effective/update_after_idle（26 测试绿）+ daily_review_pick/send_bark/daily_review_run + launchd wrapper（稳定路径+TCC 预检）+ 死人开关; 12 场景矩阵全过; 独立 Code-Review 0 CRITICAL 15 项已修
   137	- ✅ live 首跑成功: 今日复习.md 榜首=特征值与特征向量/Fundamentals; launchd 已 bootstrap（当前 TCC 拦, exit 78 有人话诊断）
   138	- ⏳ **用户 UAT 3 步**: 装 Bark 贴 key（写 `~/.config/canvas-review/bark.key`）+ 系统设置 FDA 授权 /bin/bash + 明早 9:05 看横幅 → 验收单 `_bmad-output/验收单/Story-DAILY-REVIEW-PUSH-每日复习手机推送-mini-UAT.md`
   139	- 📋 Backlog: 模型栈加固 H-1~H-6（版本锁/canary attestation/distiller schema）+ H-7 memory-health 宿主迁移 + H-8 孤儿节点回填 + H-9 Bark 加密
   140	
   141	---
   142	
   143	**历史状态**（2026-05-13 · Session-End · Story 2.3 + ChatGPT-DR Wave-6 安全硬化 7 commits ship）:
   144	- ✅ **Story 2.3 v1.0 ship** (`d9a7164`): historical error reminder, 5 AC, 21 tests, 待用户 UAT (路径 A/B/C 见操作指引)
   145	- ✅ **Wave-5 Stage B followup** (`438666d`): `index.py:delete_vault_index` ContextVar 注入 (3 tests)
   146	- ✅ **ChatGPT-DR Wave-6 安全硬化** (4 commits):
   147	  - `b2b773d` **P0-1** `/memory/extract-conversation` fail-closed + dev bypass opt-in (12 tests)
   148	  - `c9bb6c9` **P0-2** DEBUG=False 默认 + `require_internal_api_key` Branch 2 hardening (13 tests + 3 legacy 改契约)
   149	  - `e5ff53c` **P0-3** Memory API 6 endpoint 加 `require_internal_api_key`
   150	  - `7cc3c1c` **P0-5** source_description schema 对齐 — typed enum + IN list reader + 18 contract tests
   151	- ✅ **Docs** (`cda47a7`): 4 个 session 文档 (UAT 指引 / 全景 / 评估 / ChatGPT prompt)
   152	- ⚠️ **ChatGPT-DR 调研** (2 轮 deep research): Claude FAIL 判定 + 用户核心闭环不可行 (G1-G10 + 5 盲点); ChatGPT 推荐 A+ 路径
   153	
   154	**下一步 — Session-Start 锚点**:
   155	- (1) 用户跑 **Story 2.3 UAT** (3 paths: A 现有数据 / B 自然产生 / C 授权 seed) @ `_bmad-output/验收单/Story-2.3-UAT-操作指引-2026-05-13.md`
   156	- (2) 用户读 ChatGPT 报告 Part 4 — **5 个 Claude 漏看盲点** (annotation identity drift / 多存储一致性 / prompt injection in verbatim / 可观察性 evidence trace / 成本队列)
   157	- (3) 下次启动方向 (ChatGPT A+ 推荐): **P0-6 callout→mastery 桥接 (1-2d)** → **P0-7 LanceDB AnnotationDoc 重构 (1-2d)** → **🌟 GOLDEN-PATH demo (3-5d)** — 不要走 P0-4 网络收口 (除非部署到 LAN/共享主机)
   158	- (4) 推迟: **P0-4 MCP loopback + WS 鉴权** (网络收口，本地单机不紧急)
   159	- (5) Story 2.3 通过后启动 Story 5.1 BKT (CURRENT_TASK 8-Session plan S3，但 ChatGPT 警告**优先做 P0-6/7 + GOLDEN-PATH 不要继续横向 Story dev**)
   160	
   161	**关键调研产物归档**:
   162	- ChatGPT-DR 安全审查: `_bmad-output/research/2026-05-13-chatgpt-security-audit-INLINE.md`
   163	- ChatGPT-DR 第二轮回答 (verdict + 10 gaps 打分 + 7 Q 回答 + 5 盲点): 见用户 conversation log Part 1-6
   164	- 设计可行性评估: `_bmad-output/验收单/批注回复/2026-05-13-设计可行性评估-用户核心闭环.md`
   165	- 后端运行机制全景 (5 Agent deep explore): `_bmad-output/验收单/批注回复/2026-05-13-User批注-后端运行机制与-Graphiti-全景.md`
   166	
   167	**当前状态**（2026-05-12 续 · wave-4 Q3 rollback + SKILL.md native Grep ship）:
   168	- ✅ ChatGPT 全链路对抗审查完成（5 Tasks verdict + 3 P0：Multi-Vault 全链路 / 生产默认值 / 修主检索链路），response 归档 `_bmad-output/chatgpt-review-response-2026-05-11.md`
   169	- ✅ **合并 Story 2.2+2.9** spec ship + checklist 全勾 (7 AC + 7 Tasks 除 T0 / T6.2/T6.3 perf)
   170	- ✅ T1 plugin timeout (`c5e5a92`) + T2 backend (`6d2c05e`) + T3a assembler (`e0d91c0`) + T3+T5 rerank/evidence (`549d5f0`) — 用户 UAT 通过
   171	- ✅ **Q1+Q2 P0 + Wave-2 hotfix 全闭口** (`de0b4a7` → `f018580`,backend 219 + frontend 186 + 4 security 回归)
   172	- ✅ **Wave-3 hotfix done** (`ec58ee0`,W3-1/2/3/4a/4b — metadata redaction / multi-vault 隔离 / lancedb ContextVar / trim auth header)
   173	- ✅ **Wave-4 Q3 rollback + SKILL.md native Grep 改造 done** (`46fc501`,17 files / +70 / -1478):
   174	  - frontend 删除 `canvas:global-search` 命令 + `handleGlobalSearch` + `global-search.ts` helper + 19 测试
   175	  - backend 删除 POST `/api/v1/chat/global-search` endpoint + multi-seed BFS / `additional_seeds` / `TraceItem.seed_origin`
   176	  - `canvas-vault/.claude/skills/study-question/SKILL.md` 加 HARD-21（native Grep 优先）
   177	  - `canvas-vault/.claude/skills/chat-with-context/SKILL.md` 加 HARD-19（native Grep 优先）
   178	  - Q3 验收单标 `status: deprecated`（audit trail 保留）
   179	
   180	**下一步**:
   181	- 用户跑 wave-3 mini-UAT（`Story-2.2+2.9-wave-3-mini-UAT-2026-05-12.md`,Step 1 改为 SKILL.md native Grep 验证）
   182	- 用户跑 Q1/Q2 验收单（Q3 已废,改走 wave-3 mini-UAT Step 1）
   183	- T0 主链路修复 + RAGAs 基准（3-5d 独立 session, P0-C）
   184	
   185	**8-Session 全 plan（Round-14 用户原话需求 #1#2#3 落地）**:
   186	- S1: Story 2.2 (用户原话 #1) | S2: 2.3 历史误解 | S3: 5.1 BKT MCP (用户原话 #2)
   187	- S4: 5.2 FSRS (用户原话 #3) | S5: 5.3 五信号融合 | S6: 综合 UAT
   188	
   189	**关键路径**:
   190	- 本 worktree: `~/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/`
   191	- archive worktree: `~/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-deeptutor-canvas-mvp/`
   192	- 主仓 read-only: `~/Desktop/canvas/canvas-learning-system/`
   193	
   194	---
   195	
   196	## Round-22 弃用决策（2026-05-08）
   197	
   198	### 弃用原因（双重证据）
   199	
   200	1. **"内容越多幻觉越严重"**: Liu 2023 (Lost in Middle) + Cuconasu SIGIR 2024 (Power of Noise) + Chroma 2025 (Context Rot) + Karpathy llm-wiki Gist 共同实证。60KB vault scale 应抛弃 RAG 走 Karpathy LLM Wiki 模式（compile once + inline）
   201	2. **"wiki 范式只承载 final state，缺 4 维度"**: Concept Map (Novak 1972) + Spatial Hypertext (Marshall 1995) + TextNet (Trigg 1986) + Tree-of-Thoughts (Wei 2022) 4 学术 framework 共识 — wiki 丢了时间(when) / 空间(where) / 原因(why) / 置信度(how-sure)
   202	
   203	### 路径对比
   204	
   205	| 路径 | 状态 |
   206	|---|---|
   207	| Round-22 fork MVP（DeepTutor 集成） | ⛔ 弃用 |
   208	| Obsidian Hybrid（回归路径） | ✅ 主线 |
   209	| Tauri v0（更早历史） | 已淘汰 |
   210	
   211	### archive 内容指针（DeepTutor worktree 仍保留）
   212	
   213	- 17 份 round-22-* 调研报告
   214	- Epic-10 / Epic-11 implementation-artifacts（9 + 4 stories）
   215	- Story 10.1-10.4 验收单 v2.0 双段重写版
   216	- 决策批注 D17（fork mvp）/ D18（desktop electron）/ D19（docker compose）
   217	- adapter 6 文件（在 fork repo `~/Desktop/canvas/deeptutor-fork/adapter/`，可删）
   218	- DeepTutor fork repo（116MB）+ vanilla repo（28MB）— 用户决定是否 rm
   219	
   220	---

**Planning independent read-only agents**
**Confirming full context for agents**
**Planning detailed git diff inspection**
exec
/bin/zsh -lc 'git diff --no-ext-diff --unified=100 worktree-feature-obsidian-hybrid-dev -- canvas-vault/Dashboard.md' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
exec
/bin/zsh -lc 'git diff --no-ext-diff --unified=100 worktree-feature-obsidian-hybrid-dev -- scripts/daily_review_pick.py' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
exec
/bin/zsh -lc 'wc -l scripts/daily_review_pick.py scripts/daily_review_run.py scripts/send_bark.py canvas-vault/Dashboard.md backend/tests/regression/test_daily_review_pick.py' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
diff --git a/canvas-vault/Dashboard.md b/canvas-vault/Dashboard.md
index 6190e74a..2c5c53fa 100644
--- a/canvas-vault/Dashboard.md
+++ b/canvas-vault/Dashboard.md
@@ -1,162 +1,190 @@
 ---
 type: dashboard
 layout: active-learning-view
 created_at: 2026-05-01
 version: 1.0
 story: "1.18"
 ---
 
 # 📊 Canvas 学习仪表盘
 
 > [!info]+ 这是什么？
 > 一站式查看所有原白板状态 + 节点总数 + 平均掌握度 + 待复习节点。**Cmd+P 打开命令面板** → 搜索"启动考察"可以一键发起考察（复制 /start-exam-board 命令）。
 >
-> **数据源**：Plugin 实时从 `原白板/*.md` 和 `节点/*.md` 的 frontmatter 自动聚合。手动派生 / 追加 / 配置后**无需刷新**，DataviewJS 会自动重算。
+> **数据源**：Plugin 实时从 `原白板/*.md` 和 `节点/*.md` 的 frontmatter 自动聚合。手动派生 / 追加 / 配置后**无需刷新**，DataviewJS 会自动重算。**例外**：FSRS 到期数消费 `outputs/今日复习.json` 投影（daily_review_pick 是到期口径唯一裁判，每日 9:05 生成），不做独立重算。
 
 ---
 
 ## 🎯 三大核心指标
 
 ```dataviewjs
 const boards = dv.pages('"原白板"').where(p => p.type === "whiteboard");
 const nodes = dv.pages('"节点"').where(p => p.type === "concept");
 
 // 1. 平均掌握度（含颜色编码）
 const masteryValues = nodes
   .map(p => typeof p.mastery_score === "number" ? p.mastery_score : 0.30)
   .array();
 const avgMastery = masteryValues.length
   ? masteryValues.reduce((s, v) => s + v, 0) / masteryValues.length
   : 0;
 const masteryColor = avgMastery > 0.7 ? "🟢" : avgMastery > 0.4 ? "🟡" : "🔴";
 const masteryLabel = avgMastery > 0.7 ? "优秀" : avgMastery > 0.4 ? "进行中" : "起步";
 
 // 2. 节点总数（按白板分组）
 const nodesByBoard = {};
 for (const node of nodes) {
   const sb = node.source_board;
   let boardName = "（无归属）";
   if (sb) {
     const path = typeof sb === "string" ? sb : (sb.path || sb.link || "");
     const m = path.match(/原白板\/([^\]|]+?)(?:\.md)?(?:\|[^\]]*)?(?:\]\])?$/);
     if (m) boardName = m[1].trim();
   }
   nodesByBoard[boardName] = (nodesByBoard[boardName] || 0) + 1;
 }
 const groupedStr = Object.entries(nodesByBoard)
   .sort((a, b) => b[1] - a[1])
   .map(([k, v]) => `${k}: ${v}`)
   .join(" / ");
 
-// 3. FSRS 到期数（FSRS-V2 2026-07-30 接活: WHEN=fsrs_due, 无字段=新卡视同到期
-//    — 与 Decision-FSRS-2 同口径, 新卡计入到期）
-const schedCnt = nodes.filter(n => n.fsrs_due && dv.date(String(n.fsrs_due)) <= dv.date("now")).length;
-const newCnt = nodes.filter(n => !n.fsrs_due).length;
-const fsrsPlaceholder = `${schedCnt + newCnt}（含 ${newCnt} 张新卡视同到期 · 完整口径见 outputs/今日复习.md）`;
+// 3. FSRS 到期数（CARD-A2 2026-08-24: daily_review_pick 是到期口径唯一裁判,
+//    这里只消费 outputs/今日复习.json 投影 (schema v3), 不再独立重算 —
+//    修复 live 实测 13 vs 6 的口径分裂）
+let fsrsLine = "⏳ 投影未生成 — `outputs/今日复习.json` 缺失（每日复习任务每天 9:05 自动生成，生成后此处自动出数）";
+let backlogNames = [];
+try {
+  const raw = await dv.io.load("outputs/今日复习.json");
+  if (raw) {
+    const proj = JSON.parse(raw);
+    const hasDetail = Array.isArray(proj.due_nodes);
+    const dueCnt = hasDetail ? proj.due_nodes.length : (proj.stats?.due_nodes ?? 0);
+    const newCardCnt = hasDetail ? proj.due_nodes.filter(d => !d.fsrs_due).length : null;
+    backlogNames = Array.isArray(proj.ineligible?.placeholder) ? proj.ineligible.placeholder : [];
+    const backlogCnt = backlogNames.length || (proj.stats?.ineligible ?? 0);
+    const parts = [];
+    if (newCardCnt !== null) parts.push(`含 ${newCardCnt} 张新卡视同到期`);
+    parts.push(`待剖析积压 ${backlogCnt} 张另计`);
+    const unassignedCnt = proj.stats?.unassigned ?? 0;
+    if (unassignedCnt > 0) parts.push(`未归板 ${unassignedCnt} 张另计`);
+    parts.push(`投影生成于 ${proj.generated_at ?? "?"}`);
+    fsrsLine = `\`${dueCnt}\`（${parts.join(" · ")}）`;
+  }
+} catch (e) {
+  fsrsLine = "⚠️ 投影损坏 — `outputs/今日复习.json` 解析失败，等下次生成自动覆盖修复";
+}
 
 dv.paragraph(
   `📊 **平均精通度**: \`${avgMastery.toFixed(2)}\` ${masteryColor} ${masteryLabel}\n\n` +
   `📚 **节点总数**: \`${nodes.length}\`（${groupedStr || "暂无"}）\n\n` +
-  `⏰ **FSRS 到期**: ${fsrsPlaceholder}\n\n` +
+  `⏰ **FSRS 到期**: ${fsrsLine}\n\n` +
   `🗂️ **原白板总数**: \`${boards.length}\``
 );
+
+if (backlogNames.length > 0) {
+  // 文件名含 wikilink 保留字符 (|[]#^) 时退化为纯文本, 防死链
+  dv.paragraph(
+    `> 🗂️ **待剖析积压**（${backlogNames.length} 张占位节点，定义未写完不参与复习，不计入到期数）: ` +
+    backlogNames.map(n => /[|\[\]#^]/.test(n) ? n : `[[节点/${n}|${n}]]`).join("、")
+  );
+}
 ```
 
 ---
 
 ## 🗺️ 活跃原白板（按节点数排序，含交互按钮）
 
 > [!success]+ v4.3 路径 1 升级 — 交互式按钮已就绪
 > 每个白板行右侧多 2 个按钮：📂 打开白板 / 🚀 启动考察。点击直接调 plugin API（无需 Cmd+P）。
 
 ```dataviewjs
 const plugin = app.plugins.plugins["canvas-learning-system"];
 if (!plugin) {
   dv.paragraph("> ❌ Canvas plugin 未加载，请先在 Settings → Community plugins 启用。");
 } else {
   const boards = dv.pages('"原白板"').where(p => p.type === "whiteboard");
   if (boards.length === 0) {
     dv.paragraph("> 🌱 暂无原白板。Cmd+P → 搜「建/配置原白板」从零建第一个。");
   } else {
     // v4.3 用 plugin API 聚合（带缓存，<10ms）
     const boardStats = boards.array().map(board => {
       const stats = plugin.getMasteryBatch(board.file.name);
       const color = stats.avgMastery > 0.7 ? "🟢" : stats.avgMastery > 0.4 ? "🟡" : "🔴";
       return { board, ...stats, color };
     });
 
     boardStats.sort((a, b) => b.count - a.count);
 
     const container = dv.el("div", "");
     const table = container.createEl("table");
     const thead = table.createEl("thead");
     const headerRow = thead.createEl("tr");
     ["白板", "节点数", "平均掌握度", "状态", "操作"].forEach(h => {
       headerRow.createEl("th", { text: h });
     });
     const tbody = table.createEl("tbody");
 
     boardStats.forEach(s => {
       const row = tbody.createEl("tr");
       const nameCell = row.createEl("td");
       const link = nameCell.createEl("a", {
         text: s.board.file.name,
         cls: "internal-link",
       });
       link.onclick = (e) => {
         e.preventDefault();
         plugin.executeBoardCommand(s.board.file.name, "open-board");
       };
 
       row.createEl("td", { text: String(s.count) });
       row.createEl("td", { text: `${s.color} ${s.avgMastery.toFixed(2)}` });
 
       const statusText = s.count === 0
         ? "空白板（用 Cmd+Shift+D 派生节点）"
         : s.avgMastery > 0.7
           ? "✅ 掌握良好"
           : s.avgMastery > 0.4
             ? "📖 进行中"
             : "🚀 起步阶段";
       row.createEl("td", { text: statusText });
 
       const actionsCell = row.createEl("td");
       actionsCell.style.whiteSpace = "nowrap";
 
       const openBtn = actionsCell.createEl("button", { text: "📂" });
       openBtn.title = `打开 原白板/${s.board.file.name}.md`;
       openBtn.style.marginRight = "4px";
       openBtn.onclick = () => {
         plugin.executeBoardCommand(s.board.file.name, "open-board");
       };
 
       const examBtn = actionsCell.createEl("button", { text: "🚀 考察" });
       examBtn.title = "复制 /start-exam-board 命令 → 粘贴到 Claudian / Claude Code 执行（v1 检验白板，不走旧后端）";
       examBtn.style.marginRight = "4px";
       examBtn.disabled = s.count === 0;
       if (s.count === 0) {
         examBtn.style.opacity = "0.4";
         examBtn.style.cursor = "not-allowed";
       } else {
         examBtn.onclick = () => {
           plugin.executeBoardCommand(s.board.file.name, "exam-start");
         };
       }
     });
 
     // 全局刷新按钮
     const refreshDiv = container.createEl("div");
     refreshDiv.style.marginTop = "8px";
     const refreshBtn = refreshDiv.createEl("button", {
       text: "🔄 强制刷新缓存",
     });
     refreshBtn.title = "清空 plugin mastery 缓存，下次表格渲染重新聚合";
     refreshBtn.onclick = () => {
       plugin.invalidateMasteryCache();
       // 触发当前 dataview 块重新计算（用 dv.app.workspace.activeLeaf 重新刷新当前文件）
       const file = app.workspace.getActiveFile();
       if (file) {
         app.workspace.getActiveViewOfType(require("obsidian").MarkdownView)?.previewMode?.rerender(true);
       }
     };
   }

 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
diff --git a/scripts/daily_review_pick.py b/scripts/daily_review_pick.py
index 9955da69..936f8afd 100755
--- a/scripts/daily_review_pick.py
+++ b/scripts/daily_review_pick.py
@@ -1,320 +1,351 @@
 #!/usr/bin/env python3
 """每日复习选板 (DAILY-REVIEW-PUSH-2026-07-29, ChatGPT 终审 A3 修正版)。
 
 扫 vault 节点/*.md frontmatter → 衰减 Beta 读时时效 pick → 板级 min 聚合
 → outputs/今日复习.md (人读) + outputs/今日复习.json (推送 payload, 终审 A7:
 stdout 是瞬时数据, 推送失败补跑必须有持久化 payload)。
 
+schema v3 (CARD-A2, BATCH-2026-08-24-复习闭环): 本 JSON 是全系统到期口径
+唯一裁判 — Dashboard.md 直接 dv.io.load 消费 due_nodes 明细 + ineligible
+分桶 (占位符待剖析积压单独成桶), 不再独立重算。v2→v3 纯加性, 推送链
+(daily_review_run/send_bark 只读 notification) 被动兼容。
+
 三态兼容 (live 实测 18 节点: 新字段 1 / 仅旧 10 / 无字段 7):
   mastery_a/b (+last_examined) → effective() 闲置折扣后 pick
   仅 mastery_score             → from_legacy() 均值继承低置信
   无字段                       → 先验 Beta(0.9,2.1), 从未考 σ 大自动优先
 
 终审 A3 三修正:
   1. eligibility 与 start-exam-board 同规则 — 含「你的 1-2 句精准定义」
      占位符的未剖析节点跳过 (否则推荐无法出题的节点到手机)
   2. 输出命令绑定 node <top_node> — start-exam-board 自己重选点时不含
      闲置折扣, 不绑定会出现「通知说考 A 实际考 B」
   3. min() 并列 tie-break: 板上次被推荐日期(久者先) → 最老 last_examined
      → 板名 (防启动期先验板按扫描顺序永久霸榜)
 
 依赖: 仅 stdlib + vault 内 decay_beta.py (launchd 环境无 pip 包可假设)。
 """
 
 from __future__ import annotations
 
 import argparse
 import json
 import os
 import re
 import sys
 from datetime import datetime, timezone
 from pathlib import Path
 
 #: 与 start-exam-board SKILL Step 3 完全同一条占位符规则 (终审 A3)
 PLACEHOLDER = "你的 1-2 句精准定义"
 
 #: 生产数据污染标记 (对齐 memory-health.sh 批次1'⑥ 审计清单) — 不推测试节点。
 #: ⚠ 只匹配文件名: 真实节点 frontmatter 可能引用测试会话 id (live 实测
 #: Fundamentals 的 error_candidates 含 m3-e2e-sessionend-test, 按全文匹配会误杀)
 TEST_MARKERS = ("TestConcept", "UAT-2.5", "m3-e2e")
 
 #: [Decision-FSRS-2] WHEN/WHAT 分工 (FSRS-V2-2026-07-30):
 #: FSRS 管 WHEN — fsrs_due 决定今天谁到期, 无字段 = New 卡即刻到期;
 #: 衰减 Beta 管 WHAT — 到期集合内按 pick=μ−σ 排序。
 #: 本文件保持纯 stdlib: 只做 UTC 定长字符串日期比较, 不 import fsrs。
 
 #: Bark 通知标题上限 (方案规范: ≤20 全角字符)
 TITLE_LIMIT = 20
 
 
 def _aware(s: str) -> datetime:
     dt = datetime.fromisoformat(str(s).strip().replace("Z", "+00:00"))
     return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
 
 
 def _fm_num(fm: str, key: str):
     # 容负号 (Code-Review L5): mastery_a: -3 应进 corrupt 分支而非静默当无字段
     m = re.search(rf'^{key}:\s*"?(-?[0-9]*\.?[0-9]+)"?\s*$', fm, re.M)
     return float(m.group(1)) if m else None
 
 
 def _fm_str(fm: str, key: str):
     m = re.search(rf'^{key}:\s*"?([^"\n]+?)"?\s*$', fm, re.M)
     return m.group(1).strip() if m else None
 
 
 def _board_name(raw: str | None):
     """source_board 归一化 → 板名 (live 数据实为 wikilink '[[原白板/X]]')。"""
     if not raw:
         return None
     name = raw.strip()
     if name.startswith("[[") and name.endswith("]]"):
         name = name[2:-2]
     name = name.split("|")[0]                 # [[path|alias]] 取 path
     name = name.rsplit("/", 1)[-1].strip()    # 原白板/X → X
     return name or None
 
 
 def scan_nodes(vault: Path, now: datetime, decay):
-    """扫描 节点/ 池 → (nodes, stats)。逐节点容错: 单个脏节点不崩全轮。"""
+    """扫描 节点/ 池 → (nodes, stats, ineligible)。逐节点容错: 单个脏节点不崩全轮。
+
+    ineligible 分桶 (schema v3, CARD-A2): 被跳过的节点按原因点名, 不再只有
+    计数 — Dashboard 消费 placeholder 桶显示"待剖析积压"。
+    """
     stats = {"new": 0, "legacy": 0, "none": 0, "ineligible": 0, "test_excluded": 0, "corrupt": 0}
+    ineligible = {"placeholder": [], "test_excluded": [], "corrupt": []}
     now_z = now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
     nodes = []
     for path in sorted((vault / "节点").glob("*.md")):
         stem = path.stem
         try:
             text = path.read_text(encoding="utf-8")
         except OSError as e:
             stats["corrupt"] += 1
+            ineligible["corrupt"].append(stem)
             print(f"[pick] 读取失败跳过 {stem}: {e}", file=sys.stderr)
             continue
         if any(mk in stem for mk in TEST_MARKERS):
             stats["test_excluded"] += 1
+            ineligible["test_excluded"].append(stem)
             continue
         m = re.match(r"^﻿?---\r?\n(.*?)\r?\n---\r?\n?(.*)$", text, re.S)
         fm, body = (m.group(1), m.group(2)) if m else ("", text)
         if PLACEHOLDER in body:
             stats["ineligible"] += 1
+            ineligible["placeholder"].append(stem)
             continue
 
         a_raw, b_raw = _fm_num(fm, "mastery_a"), _fm_num(fm, "mastery_b")
         legacy = next(
             (v for k in ("mastery_score", "mastery", "mastery_level")
              if (v := _fm_num(fm, k)) is not None),
             None,
         )
         if a_raw is not None and b_raw is not None:
             a, b, state = a_raw, b_raw, "new"
         elif legacy is not None:
             a, b = decay.from_legacy(legacy)
             state = "legacy"
         else:
             a, b, state = decay.PRIOR_A, decay.PRIOR_B, "none"
         stats[state] += 1
 
         last_exam = _fm_str(fm, "last_examined")
         idle_days = None
         if last_exam:
             try:
                 idle_days = max(0.0, (now - _aware(last_exam)).total_seconds() / 86400.0)
             except ValueError:
                 print(f"[pick] last_examined 无法解析, 按从未考: {stem}", file=sys.stderr)
                 last_exam = None
         try:
             # pick_score 也在 try 内 (Code-Review M2): 除零/溢出同属脏数据
             a_eff, b_eff = decay.effective(a, b, idle_days or 0.0)
             pick = decay.pick_score(a_eff, b_eff)
         except (ValueError, ZeroDivisionError, OverflowError) as e:
             stats["corrupt"] += 1
+            ineligible["corrupt"].append(stem)
             print(f"[pick] Beta 参数损坏跳过 {stem}: {e}", file=sys.stderr)
             continue
 
         fsrs_due = _fm_str(fm, "fsrs_due") or ""
         # Code-Review M2: Obsidian Properties 面板可能把 datetime 重新序列化成
         # 带偏移格式, 词法比较会反向误判「永不到期」。非规范格式 fail-open
         # 视同到期 (与 New 语义一致), 不静默消失。
         if fsrs_due and not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", fsrs_due):
             print(f"[pick] fsrs_due 非规范格式, 视同到期: {stem} ({fsrs_due})", file=sys.stderr)
             fsrs_due = ""
         nodes.append({
             "node": stem,
             "board": _board_name(_fm_str(fm, "source_board")),
             "state": state,
             "pick": pick,
             "idle_days": idle_days,          # None = 从未考
             "last_examined": last_exam or "",
             "fsrs_due": fsrs_due,
             "due_now": (not fsrs_due) or fsrs_due <= now_z,  # 无字段 = New 即刻到期
             "difficulty": _fm_str(fm, "fsrs_difficulty") or "",
         })
-    return nodes, stats
+    return nodes, stats, ineligible
 
 
 def rank_boards(nodes, board_last_recommended: dict):
     """板级聚合: priority = min(pick), 终审 A3 tie-break。"""
     boards: dict[str, list] = {}
     unassigned = []
     for n in nodes:
         if not n["board"]:
             unassigned.append(n["node"])
             continue
         boards.setdefault(n["board"], []).append(n)
 
     ranked, upcoming = [], []
     for board, members in boards.items():
         due = [n for n in members if n["due_now"]]
         if not due:
             # WHEN: 全员未到期 → 不进推荐榜, 记最近的未来到期 (F1 放假语义)
             nxt = min(members, key=lambda n: n["fsrs_due"])
             upcoming.append({"board": board, "next_due": nxt["fsrs_due"], "node": nxt["node"]})
             continue
         top = min(due, key=lambda n: n["pick"])   # WHAT: 到期集合内衰减 Beta 排序
         ranked.append({
             "board": board,
             "top_node": top["node"],
             "priority": round(top["pick"], 4),
             "pending": len(due),                   # 到期即待复习 (Decision-FSRS-2)
             "idle_days": (None if top["idle_days"] is None else int(top["idle_days"])),
             "difficulty": top["difficulty"],
             "next_due": min((n["fsrs_due"] for n in members if not n["due_now"]), default=""),
             "_tie": (
                 round(top["pick"], 8),
                 board_last_recommended.get(board, ""),   # 空串 = 从未被推荐, 排最前
                 min(n["last_examined"] for n in due),    # 空串 = 有从未考节点, 排最前
                 board,
             ),
         })
     ranked.sort(key=lambda r: r["_tie"])
     for r in ranked:
         del r["_tie"]
     upcoming.sort(key=lambda u: u["next_due"])
     return ranked, upcoming, unassigned
 
 
 def _title(board: str) -> str:
     prefix = "📚 今日复习 · "
     room = TITLE_LIMIT - len(prefix)
     return prefix + (board if len(board) <= room else board[: room - 1] + "…")
 
 
 def _body(top: dict) -> str:
     idle = "从未考察" if top["idle_days"] is None else f"已闲置 {top['idle_days']} 天"
     if top["pending"] >= 2:
         return f"{top['top_node']} 等 {top['pending']} 节点待巩固 · {idle}"
     return f"{top['top_node']} 待巩固 · {idle}"
 
 
 def build_payload(vault: Path, now: datetime, board_last_recommended: dict, decay):
-    nodes, stats = scan_nodes(vault, now, decay)
+    nodes, stats, ineligible = scan_nodes(vault, now, decay)
     ranked, upcoming, unassigned = rank_boards(nodes, board_last_recommended)
     stats["unassigned"] = len(unassigned)
-    stats["due_nodes"] = sum(1 for n in nodes if n["board"] and n["due_now"])
+    # v3 (CARD-A2): due_nodes 明细与 stats 数字同源派生 — 自洽靠构造保证,
+    # 本投影是全系统到期口径唯一裁判 (Dashboard 只消费不重算)
+    due_rows = [
+        {
+            "node": n["node"],
+            "board": n["board"],
+            "state": n["state"],
+            "pick": round(n["pick"], 4),
+            "fsrs_due": n["fsrs_due"],           # 空串 = 新卡即刻到期
+            "last_examined": n["last_examined"],
+            "difficulty": n["difficulty"],
+        }
+        for n in nodes if n["board"] and n["due_now"]
+    ]
+    stats["due_nodes"] = len(due_rows)
     stats["future_nodes"] = sum(1 for n in nodes if n["board"] and not n["due_now"])
     payload = {
         "unassigned_nodes": unassigned,  # Code-Review M3: 点名而非只给数字
-        "schema_version": 2,             # v2: FSRS WHEN 化 (upcoming/due 语义)
+        "schema_version": 3,             # v3: +due_nodes 明细 +ineligible 分桶
+        #                                  (纯加性; v2: FSRS WHEN 化 upcoming/due 语义)
         "date": now.astimezone().date().isoformat(),
         "generated_at": now.astimezone().isoformat(timespec="seconds"),
         "top_boards": ranked[:3],
         "upcoming": upcoming[:3],
+        "due_nodes": due_rows,
+        "ineligible": ineligible,
         "stats": stats,
         "notification": None,
     }
     day_id = f"canvas-review-{payload['date']}"
     if ranked:
         payload["notification"] = {
             "title": _title(ranked[0]["board"]),
             "body": _body(ranked[0]),
             "group": "canvas复习",
             "id": day_id,
         }
     elif upcoming:
         # F1 放假语义: 有调度中的板但今天零到期 → 诚实说不用复习
         nxt = upcoming[0]
         payload["notification"] = {
             "title": "📚 今日无到期节点",
             "body": f"按计划推进，休息一天 · 最近到期 {nxt['board']} · {nxt['next_due'][:10]}",
             "group": "canvas复习",
             "id": day_id,
         }
     return payload, ranked
 
 
 def render_md(payload, ranked) -> str:
     s = payload["stats"]
     lines = [
         f"# 今日复习 · {payload['date']}",
         "",
         f"> 生成 {payload['generated_at']} · 到期={s['due_nodes']} / 未到期={s['future_nodes']}（不含未归板）"
         f" · 节点状态: new={s['new']} / legacy={s['legacy']}"
         f" / 无字段={s['none']} / 未剖析跳过={s['ineligible']} / 测试排除={s['test_excluded']}"
         f" / 未归板={s['unassigned']} / 损坏={s['corrupt']}",
         "",
         "| 板 | 优先分 | 到期待复习 | 最该考 | 难度 | 闲置 | 板内下次到期 |",
         "|---|---|---|---|---|---|---|",
     ]
     for r in ranked:
         idle = "从未考" if r["idle_days"] is None else f"{r['idle_days']} 天"
         nxt = r["next_due"][:10] if r["next_due"] else "-"
         diff = r["difficulty"] or "-"
         lines.append(
             f"| {r['board']} | {r['priority']} | {r['pending']} | {r['top_node']} | {diff} | {idle} | {nxt} |"
         )
     if payload.get("upcoming"):
         for u in payload["upcoming"]:
             lines.append(f"| {u['board']} | - | 0（未到期） | - | - | - | {u['next_due'][:10]} |")
     if ranked:
         lines += ["", "## 一键开考（整行复制到 Claudian）", ""]
         for r in ranked:
             lines.append(f"- `/start-exam-board from {r['board']} node {r['top_node']}`")
     else:
         lines += ["", "> ✅ 今日无到期节点，休息一天。"]
     if payload.get("unassigned_nodes"):
         lines += ["", "> ⚠ 未归板节点（无 source_board，不参与推荐）: "
                   + "、".join(payload["unassigned_nodes"])]
     lines += [
         "",
         "> WHEN=FSRS 到期（无 fsrs_due 字段 = 新卡即刻到期）；WHAT=到期集合内按 μ−σ 排序",
         "> （含闲置回升，证据质量半衰期 69 天）。未剖析占位节点已跳过；命令已绑定最该考节点。",
     ]
     return "\n".join(lines) + "\n"
 
 
 def atomic_write(path: Path, content: str):
     tmp = path.with_suffix(path.suffix + ".tmp")
     tmp.write_text(content, encoding="utf-8")
     os.replace(tmp, path)
 
 
 def load_decay(vault: Path):
     sys.path.insert(0, str(vault / ".claude" / "scripts"))
     import decay_beta
     return decay_beta
 
 
 def main():
     ap = argparse.ArgumentParser(description="每日复习选板")
     ap.add_argument("--vault", required=True)
     ap.add_argument("--state", help="daily-review.state.json (只读, 取 board_last_recommended)")
     ap.add_argument("--now", help="ISO 时间覆盖 (测试用)")
     ap.add_argument("--write", action="store_true", help="写 outputs/今日复习.md+json")
     args = ap.parse_args()
 
     vault = Path(args.vault)
     # 裸时间当本地时区, 与 daily_review_run.py 语义统一 (Code-Review L6)
     if args.now:
         dt = datetime.fromisoformat(args.now.replace("Z", "+00:00"))
         now = dt if dt.tzinfo else dt.astimezone()
     else:
         now = datetime.now(timezone.utc)
     blr = {}
     if args.state and Path(args.state).exists():
         try:
             blr = json.loads(Path(args.state).read_text(encoding="utf-8")).get(
                 "board_last_recommended", {})
         except (json.JSONDecodeError, OSError):
             pass  # state 损坏由 runner 处置, 选点侧降级为无记录
 
     payload, ranked = build_payload(vault, now, blr, load_decay(vault))
     if args.write:

 succeeded in 0ms:
     361 scripts/daily_review_pick.py
     186 scripts/daily_review_run.py
     115 scripts/send_bark.py
     551 canvas-vault/Dashboard.md
     219 backend/tests/regression/test_daily_review_pick.py
    1432 total

exec
/bin/zsh -lc 'git diff --no-ext-diff --unified=100 worktree-feature-obsidian-hybrid-dev -- backend/tests/regression/test_daily_review_pick.py' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
diff --git a/backend/tests/regression/test_daily_review_pick.py b/backend/tests/regression/test_daily_review_pick.py
index e397cdd0..bfba3ca3 100644
--- a/backend/tests/regression/test_daily_review_pick.py
+++ b/backend/tests/regression/test_daily_review_pick.py
@@ -44,100 +44,176 @@ def test_pathological_last_examined_does_not_kill_run(tmp_path):
             "正常": _node(),
         },
     )
     assert payload["stats"]["corrupt"] == 0 and len(ranked) == 1
     assert all(r["priority"] == r["priority"] for r in ranked)  # 无 NaN
 
 
 def test_wikilink_board_normalization(tmp_path):
     payload, ranked = _build(tmp_path, {"甲": _node(board="我的板")})
     assert ranked[0]["board"] == "我的板"
     assert "node 甲" in picker.render_md(payload, ranked)
 
 
 def test_placeholder_node_skipped_empty_notification(tmp_path):
     payload, ranked = _build(
         tmp_path,
         {
             "占位": _node(extra="").replace("真实内容。", "> 你的 1-2 句精准定义"),
         },
     )
     assert payload["stats"]["ineligible"] == 1
     assert ranked == [] and payload["notification"] is None
 
 
 def test_tiebreak_prefers_least_recently_recommended(tmp_path):
     nodes = {"a节点": _node(board="A板"), "b节点": _node(board="B板")}
     _, ranked = _build(tmp_path, nodes, blr={"A板": "2026-07-29"})
     assert ranked[0]["board"] == "B板", "同分时从未被推荐的板优先"
     _, ranked2 = _build(tmp_path, nodes)
     assert ranked2[0]["board"] == "A板", "全无记录时按板名稳定排序"
 
 
 def test_negative_mastery_counted_corrupt_not_silent(tmp_path):
     """Code-Review L5: mastery_a: -3 必须进 corrupt, 不得静默当无字段。"""
     payload, ranked = _build(
         tmp_path,
         {
             "脏": _node(extra="mastery_a: -3\nmastery_b: 2\n"),
         },
     )
     assert payload["stats"]["corrupt"] == 1 and ranked == []
 
 
 def test_bom_frontmatter_tolerated(tmp_path):
     payload, _ = _build(
         tmp_path,
         {
             "带bom": "﻿" + _node(extra="mastery_a: 1.0\nmastery_b: 1.0\n"),
         },
     )
     assert payload["stats"]["new"] == 1
 
 
 # ── FSRS WHEN 语义 ([Decision-FSRS-2], FSRS-V2-2026-07-30) ──
 
 
 def test_future_due_board_gets_rest_notification(tmp_path):
     """F1: 唯一板全员未到期 → 不进推荐榜, 推送改为诚实的放假消息。"""
     payload, ranked = _build(
         tmp_path,
         {
             "已排期": _node(extra="mastery_a: 2.0\nmastery_b: 2.0\nfsrs_due: 2026-08-15T01:00:00Z\n"),
         },
     )
     assert ranked == [] and payload["stats"]["future_nodes"] == 1
     noti = payload["notification"]
     assert "无到期" in noti["title"] and "2026-08-15" in noti["body"]
     assert payload["upcoming"][0]["board"] == "普通板"
 
 
 def test_due_filter_beats_pick_within_board(tmp_path):
     """WHEN 先于 WHAT: 板内未到期节点即使 pick 更低也不能当 top_node。"""
     payload, ranked = _build(
         tmp_path,
         {
             "低分未到期": _node(extra="mastery_a: 0.1\nmastery_b: 5.0\nfsrs_due: 2026-08-15T01:00:00Z\n"),
             "到期节点": _node(extra="mastery_a: 3.0\nmastery_b: 1.0\nfsrs_due: 2026-07-29T01:00:00Z\n"),
         },
     )
     assert ranked[0]["top_node"] == "到期节点" and ranked[0]["pending"] == 1
     assert ranked[0]["next_due"] == "2026-08-15T01:00:00Z"
 
 
 def test_no_fsrs_field_means_new_card_due_now(tmp_path):
     """零迁移: 无 fsrs_due 字段的存量节点 = New 卡即刻到期, 行为与 MVP 一致。"""
     payload, ranked = _build(tmp_path, {"存量": _node()})
     assert ranked[0]["pending"] == 1 and payload["stats"]["due_nodes"] == 1
 
 
 def test_unassigned_nodes_named_in_md(tmp_path):
     """Code-Review M3: 无 source_board 节点点名可见, 不再只是个数字。"""
     payload, ranked = _build(
         tmp_path,
         {
             "孤儿": "---\ntype: concept\n---\n真实内容。\n",
             "正常": _node(),
         },
     )
     assert payload["unassigned_nodes"] == ["孤儿"]
     assert "孤儿" in picker.render_md(payload, ranked)
+
+
+# ── Review Projection v3 (CARD-A2, BATCH-2026-08-24-复习闭环) ──
+# daily_review_pick 为到期口径唯一裁判: Dashboard 消费 due_nodes 明细与
+# ineligible 分桶, 不再独立重算 (live 实测 13 vs 6 口径分裂的修复锁定)。
+
+
+def test_projection_v3_due_nodes_and_ineligible_buckets(tmp_path):
+    """5 类口径分歧节点全覆盖: 明细集合与 stats 数字必须同源自洽。
+
+    ① 占位符未剖析 → ineligible.placeholder 单独成桶 (不静默吞掉)
+    ② 无 type 字段 → picker 口径照收 (旧 Dashboard type==concept 反向漏掉的那类)
+    ③ 无 source_board → 不计入 due_nodes, 点名在 unassigned_nodes
+    ④ TEST_MARKERS 文件名 → ineligible.test_excluded 桶
+    ⑤ 脏 fsrs_due (带时区偏移) → fail-open 视同到期, 进 due_nodes
+
+    另锁 due 边界 (对抗性验证 M2): fsrs_due==now 判到期 (<= 语义),
+    now+1h 判未到期 — 词法比较改 < 或引入时区漂移都会红。
+    """
+    payload, _ = _build(
+        tmp_path,
+        {
+            "占位": _node().replace("真实内容。", "> 你的 1-2 句精准定义"),
+            "无type": '---\nsource_board: "[[原白板/B板]]"\n---\n真实内容。\n',
+            "孤儿": "---\ntype: concept\n---\n真实内容。\n",
+            "TestConcept-伪节点": _node(),
+            "脏due": _node(extra="fsrs_due: 2026-07-29T01:00:00+08:00\n"),
+            "规范到期": _node(extra="fsrs_due: 2026-07-29T01:00:00Z\n"),
+            "边界到期": _node(extra="fsrs_due: 2026-07-30T01:00:00Z\n"),
+            "小时级未到期": _node(extra="fsrs_due: 2026-07-30T02:00:00Z\n"),
+            "未到期": _node(extra="fsrs_due: 2026-08-15T01:00:00Z\n"),
+            "损坏": _node(extra="mastery_a: -3\nmastery_b: 2\n"),
+        },
+    )
+    assert payload["schema_version"] == 3
+    assert {d["node"] for d in payload["due_nodes"]} == {"无type", "脏due", "规范到期", "边界到期"}
+    assert len(payload["due_nodes"]) == payload["stats"]["due_nodes"]
+    for row in payload["due_nodes"]:
+        assert set(row) >= {"node", "board", "state", "fsrs_due"}
+    rows = {d["node"]: d for d in payload["due_nodes"]}
+    assert rows["无type"]["board"] == "B板" and rows["规范到期"]["board"] == "普通板"
+    # fail-open 清空语义锁定: Dashboard 的"新卡视同到期"计数依赖 fsrs_due==""
+    assert rows["脏due"]["fsrs_due"] == ""
+
+    ineligible = payload["ineligible"]
+    assert set(ineligible) >= {"placeholder", "test_excluded", "corrupt"}
+    assert ineligible["placeholder"] == ["占位"]
+    assert ineligible["test_excluded"] == ["TestConcept-伪节点"]
+    assert ineligible["corrupt"] == ["损坏"]
+    assert len(ineligible["placeholder"]) == payload["stats"]["ineligible"]
+    assert len(ineligible["test_excluded"]) == payload["stats"]["test_excluded"]
+    assert len(ineligible["corrupt"]) == payload["stats"]["corrupt"]
+    assert payload["unassigned_nodes"] == ["孤儿"]
+
+
+def test_projection_v3_purely_additive_keeps_v2_contract(tmp_path):
+    """推送链被动性守卫: v2 既有字段一个不少、语义不变 (daily_review_run /
+    send_bark 只读 notification, 但全字段名保留是加性承诺的下界)。"""
+    payload, ranked = _build(tmp_path, {"存量": _node()})
+    for key in ("unassigned_nodes", "date", "generated_at", "top_boards",
+                "upcoming", "due_nodes", "ineligible", "stats", "notification"):
+        assert key in payload
+    for key in ("new", "legacy", "none", "ineligible", "test_excluded",
+                "corrupt", "unassigned", "due_nodes", "future_nodes"):
+        assert isinstance(payload["stats"][key], int)
+    assert payload["notification"]["id"] == f"canvas-review-{payload['date']}"
+    assert ranked[0]["board"] == "普通板"
+
+
+def test_projection_v3_empty_vault_keeps_contract_keys(tmp_path):
+    """空 vault 契约完整性: 分桶与明细键必须恒在 (Dashboard 不做存在性分支)。"""
+    payload, ranked = _build(tmp_path, {})
+    assert ranked == [] and payload["due_nodes"] == []
+    assert set(payload["ineligible"]) == {"placeholder", "test_excluded", "corrupt"}
+    assert all(v == [] for v in payload["ineligible"].values())
+    assert payload["notification"] is None

**Assessing API changes impact**
**Verifying JSON fallback robustness**
**Checking dashboard data handling**
**Identifying semantic mislabel in due field**
**Planning to review initial product semantics section**
exec
/bin/zsh -lc "nl -ba '/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-08-24-第一批小goal卡-复习闭环.md' | sed -n '1,64p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
 succeeded in 0ms:
     1	# 第一批小 Goal 卡 — 复习闭环起步（待你过目批准）
     2	
     3	> **批次 ID**: BATCH-2026-08-24-复习闭环
     4	> **日期**: 2026-08-24 · **状态**: ⏸️ 等待用户批准，未动一行产品代码
     5	> **来源**: 用户 2026-08-24 决策"就这么干"（弃 24h 自建 supervisor 编排，改小 goal 卡并行：Fable 开发 + Codex gpt-5.6-sol 审查 + worktree 隔离 + 你早上验收）
     6	> **勘探方法**: 5 路只读 agent 并行勘探真实代码，每张卡均有 file:line 级证据与实测复现，无一张凭计划书文字转述
     7	> **上游依据**: `审查/2026-08-24-主Goal拆解运行可能性-并行对抗性审查报告.md` §7
     8	
     9	---
    10	
    11	## 一、你只需要看这部分（大白话）
    12	
    13	这批一共 **4 张产品卡 + 1 张准备卡**，全部围绕"每天复习"这条你最常用的链路。勘探发现的问题比计划书写的还严重一点——好消息是每个问题都定位到了具体哪一行代码，修起来是外科手术不是大动干戈。
    14	
    15	### 卡片速览
    16	
    17	| 卡 | 一句话说明 | 修完你能感觉到什么 | 预计 |
    18	|---|---|---|---|
    19	| **A1 新概念排程静默失效** | 每个**新**概念的智能排程（FSRS）其实从来没生效过——底层库返回空值，代码一碰就崩，然后悄悄退回最笨的固定间隔法，你完全看不出来 | 新学的概念开始按记忆科学排复习间隔，而不是死板的固定天数 | 约 5 小时 |
    20	| **A2 到期数字打架** | Dashboard 说今天到期 13 个，每日推荐说 6 个——实测确认两边用了两套完全不同的算法（连"哪些节点算数"都不一致） | 所有地方显示同一个数字，并且能看到"8 个还没剖析的节点"单独列出来，不再糊在一起 | 约 5 小时 |
    21	| **A3 当天重学卡消失** | 答错的卡本该 1/10 分钟后重新出现，但系统每天早上 9:05 只算一次、缓存一整天——答错的卡要等到**第二天**才回来 | 答错的卡当天就会重新出现在复习清单里（每小时刷新一次） | 约 5 小时 |
    22	| **B1 质量门红灯** | 自动检查发现 5 个图像库安全漏洞挡住了质量门；根因是一个**从来没人用过**的视频处理依赖把图像库锁在了旧版本 | 质量门变绿，以后每次改动都有真实的自动把关 | 约 3 小时 |
    23	| **E0 夜间车道准备** | 修一个卡住自动测试的孤儿文件 + 写好夜间运行手册（Codex 审查环境已确认就绪，不用装任何东西） | 夜间自动推进的前提条件齐了 | 约 2.5 小时 |
    24	
    25	### 并行安排（三条车道）
    26	
    27	```
    28	车道 1（串行链）:  A2 到期数字打架  →  A3 当天重学卡    ← A3 要用 A2 定好的数据格式，必须排队
    29	车道 2（独立）:    A1 新概念排程                        ← 和谁都不冲突，可同时跑
    30	车道 3（独立）:    B1 质量门 + E0 夜间准备               ← 和谁都不冲突，可同时跑
    31	```
    32	
    33	### 第一晚试点建议：**A1**
    34	
    35	理由：它的完成标准最"机械"——先写一个会失败的测试（证明 bug 存在），修到测试全绿为止，全程不碰你的笔记内容、不用联网、不用推送代码。Fable 晚上修，修完 Codex 审查，你早上看验收单。
    36	
    37	### 需要你顺手拍板的 2 个产品语义（不拍板就按推荐做）
    38	
    39	1. **A2**：统一数字后，那 8 个"还没写定义的占位节点"从到期数里拿出来单独显示为"待剖析积压"，而不是假装它们能复习。**推荐：单独显示**。
    40	2. **A3**：修复后 Dashboard 显示的是"最近一次计算的快照 + 计算时间"，每小时刷新（9:05–21:00），不是秒级实时。**推荐：接受每小时刷新**（秒级实时要引入常驻服务，代价不成比例）。
    41	
    42	### 你怎么启动
    43	
    44	回复以下任一句：
    45	- **"批准，今晚跑 A1"** —— 三条车道白天推进，今晚 A1 进夜间试点；
    46	- **"批准，白天先跑"** —— 只白天推进，夜间试点等你看过第一张卡的成果再说；
    47	- 或对任何一张卡说"去掉/改成…"。
    48	
    49	---
    50	
    51	## 二、技术档案（给 Claude / Codex 读，你可以不看）
    52	
    53	### CARD-A1: FSRS 新卡 None 序列化崩溃修复
    54	
    55	- **确认状态**: CONFIRMED（真实 fsrs 6.3.1 实测复现 4 个崩溃点）
    56	- **证据摘要**:
    57	  - `Card().stability == None`（fsrs 6.3.1 新卡语义），`float(None)` → TypeError；
    58	  - 崩溃点 1/2: `backend/lib/memory/temporal/fsrs_manager.py:278-283, 350-353`——`hasattr` 守卫失效（属性存在但值为 None）；
    59	  - 崩溃点 3: `backend/app/services/review_service.py:835-836` f-string `:.2f` 格式化 None → 被 `:864 except` 吞掉 → **每个新概念静默降级 Ebbinghaus**（:869-870）；
    60	  - 崩溃点 4: `review_service.py:2117-2118` → Story 38.3 AC-4"新概念自动建卡"在真实库下完全死亡；
    61	  - 测试全用 FakeCard（stability=0.0/1.0 真实数值）或 MagicMock，真实新卡零覆盖；`test_fsrs_state_query.py:202-210` 的绿灯**靠这个 bug 维持**（found=False 断言与 38.3 AC-4 矛盾）；
    62	  - vault 侧 `canvas-vault/.claude/scripts/fsrs_bridge.py:94-95,109-110` 已有防御，缺陷仅在 backend 侧。
    63	- **改动文件**: `backend/lib/memory/temporal/fsrs_manager.py`、`backend/app/services/review_service.py`、`backend/tests/unit/test_fsrs_state_query.py`、新增 `backend/tests/regression/test_fsrs_new_card_none_serialization.py`、（加固）`backend/app/services/mastery_engine.py`
    64	- **设计要点**: None 序列化为 JSON null 并可 roundtrip 还原（保持 py-fsrs 新卡语义），**不许写死 0.0**（会让 scheduler 把新卡当已学卡）；API 响应层再做 None→默认值转换。

**Inspecting payload fields and consumption**
exec
/bin/zsh -lc "nl -ba scripts/send_bark.py | sed -n '1,180p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
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
/bin/zsh -lc "nl -ba scripts/daily_review_run.py | sed -n '1,230p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
 succeeded in 0ms:
     1	#!/usr/bin/env python3
     2	"""每日复习推送编排 runner (DAILY-REVIEW-PUSH-2026-07-29, 终审 A4/A7 硬化版)。
     3	
     4	顺序铁律: md/json 先落盘(保底) → 窗口内 Bark → 失败 osascript 兜底。
     5	壳层 daily-review-push.sh 只负责 mkdir 锁 + 固定解释器; 业务全在此处
     6	(可 --now 注入时间跑 12 场景验收矩阵)。
     7	
     8	终审修正落点:
     9	  A4: 时间门 9:05 ≤ 本地时间 < 21:00 (RunAtLoad 早触发只生成不推;
    10	      唤醒补跑窗口内补推; 过窗只落盘) · state JSON 原子写 (os.replace)
    11	      · last_push_accepted_date 命名 (HTTP 成功仅证明服务端接受)
    12	  A7: payload 持久化 今日复习.json (生成成功推送失败 → 补跑只补推送)
    13	      · osascript 走 argv (板名注入免疫) · 损坏 state 隔离重建不炸
    14	"""
    15	
    16	from __future__ import annotations
    17	
    18	import argparse
    19	import hashlib
    20	import json
    21	import os
    22	import subprocess
    23	import sys
    24	from datetime import datetime, time as dtime, timezone
    25	from pathlib import Path
    26	
    27	sys.path.insert(0, str(Path(__file__).resolve().parent))
    28	import send_bark  # noqa: E402
    29	
    30	REPO = Path(os.environ.get("CANVAS_REPO", "/Users/Heishing/Desktop/canvas/canvas-learning-system"))
    31	# VAULT-SYNC (2026-08-02): 默认值仅作兜底 — 生产链由 wrapper 从 .env
    32	# ACTIVE_VAULT 解析后经 --vault 传入, 与后端同源 (换 vault 只改 .env 一处)
    33	VAULT = REPO / "canvas-vault"
    34	STATE = REPO / "backups" / "daily-review.state.json"
    35	LOG = REPO / "backups" / "daily-review.log"
    36	
    37	PUSH_WINDOW = (dtime(9, 5), dtime(21, 0))
    38	
    39	APPLESCRIPT = (
    40	    "on run argv\n"
    41	    "    display notification (item 2 of argv) with title (item 1 of argv)\n"
    42	    "end run\n"
    43	)
    44	
    45	
    46	def _now(arg: str | None) -> datetime:
    47	    if arg:
    48	        dt = datetime.fromisoformat(arg.replace("Z", "+00:00"))
    49	        return dt if dt.tzinfo else dt.astimezone()
    50	    return datetime.now(timezone.utc)
    51	
    52	
    53	def load_state() -> dict:
    54	    if not STATE.exists():
    55	        return {"schema_version": 1, "board_last_recommended": {}}
    56	    try:
    57	        st = json.loads(STATE.read_text(encoding="utf-8"))
    58	        st.setdefault("board_last_recommended", {})
    59	        return st
    60	    except (json.JSONDecodeError, OSError):
    61	        quarantine = STATE.with_name(
    62	            STATE.name + ".corrupt-" + datetime.now().strftime("%Y%m%dT%H%M%S"))
    63	        try:
    64	            os.replace(STATE, quarantine)
    65	        except OSError:
    66	            pass
    67	        print(f"[runner] state 损坏, 已隔离到 {quarantine.name}, 重建", file=sys.stderr)
    68	        return {"schema_version": 1, "board_last_recommended": {}}
    69	
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
   161	            save_state(st)
   162	            push = "accepted"
   163	        else:
   164	            push = "skip-nokey" if rc == 2 else "failed"
   165	            if rc != 2:
   166	                st["last_result"] = "generated_push_failed"
   167	                st["last_error"] = "bark-send"
   168	            # 本地兜底每日一次 (Code-Review L1 去重门); 无 key 也提醒一条
   169	            # (Code-Review H1: key 配好前不能一切静默)
   170	            if st.get("last_local_notify_date") != today:
   171	                local_noti = noti if rc != 2 else {
   172	                    "title": "📚 今日复习已生成",
   173	                    "body": noti["body"] + "（Bark 未配置，仅本地提醒）",
   174	                }
   175	                fallback = "ok" if osascript_fallback(local_noti) else "fail"
   176	                if fallback == "ok":
   177	                    st["last_local_notify_date"] = today
   178	            save_state(st)
   179	
   180	    log_line(f"generate:{gen} push:{push} fallback:{fallback}")
   181	    print(f"[runner] generate:{gen} push:{push} fallback:{fallback}")
   182	    return 0
   183	
   184	
   185	if __name__ == "__main__":
   186	    sys.exit(main())

exec
/bin/zsh -lc "nl -ba scripts/daily_review_pick.py | sed -n '35,300p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
 succeeded in 0ms:
    35	import sys
    36	from datetime import datetime, timezone
    37	from pathlib import Path
    38	
    39	#: 与 start-exam-board SKILL Step 3 完全同一条占位符规则 (终审 A3)
    40	PLACEHOLDER = "你的 1-2 句精准定义"
    41	
    42	#: 生产数据污染标记 (对齐 memory-health.sh 批次1'⑥ 审计清单) — 不推测试节点。
    43	#: ⚠ 只匹配文件名: 真实节点 frontmatter 可能引用测试会话 id (live 实测
    44	#: Fundamentals 的 error_candidates 含 m3-e2e-sessionend-test, 按全文匹配会误杀)
    45	TEST_MARKERS = ("TestConcept", "UAT-2.5", "m3-e2e")
    46	
    47	#: [Decision-FSRS-2] WHEN/WHAT 分工 (FSRS-V2-2026-07-30):
    48	#: FSRS 管 WHEN — fsrs_due 决定今天谁到期, 无字段 = New 卡即刻到期;
    49	#: 衰减 Beta 管 WHAT — 到期集合内按 pick=μ−σ 排序。
    50	#: 本文件保持纯 stdlib: 只做 UTC 定长字符串日期比较, 不 import fsrs。
    51	
    52	#: Bark 通知标题上限 (方案规范: ≤20 全角字符)
    53	TITLE_LIMIT = 20
    54	
    55	
    56	def _aware(s: str) -> datetime:
    57	    dt = datetime.fromisoformat(str(s).strip().replace("Z", "+00:00"))
    58	    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    59	
    60	
    61	def _fm_num(fm: str, key: str):
    62	    # 容负号 (Code-Review L5): mastery_a: -3 应进 corrupt 分支而非静默当无字段
    63	    m = re.search(rf'^{key}:\s*"?(-?[0-9]*\.?[0-9]+)"?\s*$', fm, re.M)
    64	    return float(m.group(1)) if m else None
    65	
    66	
    67	def _fm_str(fm: str, key: str):
    68	    m = re.search(rf'^{key}:\s*"?([^"\n]+?)"?\s*$', fm, re.M)
    69	    return m.group(1).strip() if m else None
    70	
    71	
    72	def _board_name(raw: str | None):
    73	    """source_board 归一化 → 板名 (live 数据实为 wikilink '[[原白板/X]]')。"""
    74	    if not raw:
    75	        return None
    76	    name = raw.strip()
    77	    if name.startswith("[[") and name.endswith("]]"):
    78	        name = name[2:-2]
    79	    name = name.split("|")[0]                 # [[path|alias]] 取 path
    80	    name = name.rsplit("/", 1)[-1].strip()    # 原白板/X → X
    81	    return name or None
    82	
    83	
    84	def scan_nodes(vault: Path, now: datetime, decay):
    85	    """扫描 节点/ 池 → (nodes, stats, ineligible)。逐节点容错: 单个脏节点不崩全轮。
    86	
    87	    ineligible 分桶 (schema v3, CARD-A2): 被跳过的节点按原因点名, 不再只有
    88	    计数 — Dashboard 消费 placeholder 桶显示"待剖析积压"。
    89	    """
    90	    stats = {"new": 0, "legacy": 0, "none": 0, "ineligible": 0, "test_excluded": 0, "corrupt": 0}
    91	    ineligible = {"placeholder": [], "test_excluded": [], "corrupt": []}
    92	    now_z = now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    93	    nodes = []
    94	    for path in sorted((vault / "节点").glob("*.md")):
    95	        stem = path.stem
    96	        try:
    97	            text = path.read_text(encoding="utf-8")
    98	        except OSError as e:
    99	            stats["corrupt"] += 1
   100	            ineligible["corrupt"].append(stem)
   101	            print(f"[pick] 读取失败跳过 {stem}: {e}", file=sys.stderr)
   102	            continue
   103	        if any(mk in stem for mk in TEST_MARKERS):
   104	            stats["test_excluded"] += 1
   105	            ineligible["test_excluded"].append(stem)
   106	            continue
   107	        m = re.match(r"^﻿?---\r?\n(.*?)\r?\n---\r?\n?(.*)$", text, re.S)
   108	        fm, body = (m.group(1), m.group(2)) if m else ("", text)
   109	        if PLACEHOLDER in body:
   110	            stats["ineligible"] += 1
   111	            ineligible["placeholder"].append(stem)
   112	            continue
   113	
   114	        a_raw, b_raw = _fm_num(fm, "mastery_a"), _fm_num(fm, "mastery_b")
   115	        legacy = next(
   116	            (v for k in ("mastery_score", "mastery", "mastery_level")
   117	             if (v := _fm_num(fm, k)) is not None),
   118	            None,
   119	        )
   120	        if a_raw is not None and b_raw is not None:
   121	            a, b, state = a_raw, b_raw, "new"
   122	        elif legacy is not None:
   123	            a, b = decay.from_legacy(legacy)
   124	            state = "legacy"
   125	        else:
   126	            a, b, state = decay.PRIOR_A, decay.PRIOR_B, "none"
   127	        stats[state] += 1
   128	
   129	        last_exam = _fm_str(fm, "last_examined")
   130	        idle_days = None
   131	        if last_exam:
   132	            try:
   133	                idle_days = max(0.0, (now - _aware(last_exam)).total_seconds() / 86400.0)
   134	            except ValueError:
   135	                print(f"[pick] last_examined 无法解析, 按从未考: {stem}", file=sys.stderr)
   136	                last_exam = None
   137	        try:
   138	            # pick_score 也在 try 内 (Code-Review M2): 除零/溢出同属脏数据
   139	            a_eff, b_eff = decay.effective(a, b, idle_days or 0.0)
   140	            pick = decay.pick_score(a_eff, b_eff)
   141	        except (ValueError, ZeroDivisionError, OverflowError) as e:
   142	            stats["corrupt"] += 1
   143	            ineligible["corrupt"].append(stem)
   144	            print(f"[pick] Beta 参数损坏跳过 {stem}: {e}", file=sys.stderr)
   145	            continue
   146	
   147	        fsrs_due = _fm_str(fm, "fsrs_due") or ""
   148	        # Code-Review M2: Obsidian Properties 面板可能把 datetime 重新序列化成
   149	        # 带偏移格式, 词法比较会反向误判「永不到期」。非规范格式 fail-open
   150	        # 视同到期 (与 New 语义一致), 不静默消失。
   151	        if fsrs_due and not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", fsrs_due):
   152	            print(f"[pick] fsrs_due 非规范格式, 视同到期: {stem} ({fsrs_due})", file=sys.stderr)
   153	            fsrs_due = ""
   154	        nodes.append({
   155	            "node": stem,
   156	            "board": _board_name(_fm_str(fm, "source_board")),
   157	            "state": state,
   158	            "pick": pick,
   159	            "idle_days": idle_days,          # None = 从未考
   160	            "last_examined": last_exam or "",
   161	            "fsrs_due": fsrs_due,
   162	            "due_now": (not fsrs_due) or fsrs_due <= now_z,  # 无字段 = New 即刻到期
   163	            "difficulty": _fm_str(fm, "fsrs_difficulty") or "",
   164	        })
   165	    return nodes, stats, ineligible
   166	
   167	
   168	def rank_boards(nodes, board_last_recommended: dict):
   169	    """板级聚合: priority = min(pick), 终审 A3 tie-break。"""
   170	    boards: dict[str, list] = {}
   171	    unassigned = []
   172	    for n in nodes:
   173	        if not n["board"]:
   174	            unassigned.append(n["node"])
   175	            continue
   176	        boards.setdefault(n["board"], []).append(n)
   177	
   178	    ranked, upcoming = [], []
   179	    for board, members in boards.items():
   180	        due = [n for n in members if n["due_now"]]
   181	        if not due:
   182	            # WHEN: 全员未到期 → 不进推荐榜, 记最近的未来到期 (F1 放假语义)
   183	            nxt = min(members, key=lambda n: n["fsrs_due"])
   184	            upcoming.append({"board": board, "next_due": nxt["fsrs_due"], "node": nxt["node"]})
   185	            continue
   186	        top = min(due, key=lambda n: n["pick"])   # WHAT: 到期集合内衰减 Beta 排序
   187	        ranked.append({
   188	            "board": board,
   189	            "top_node": top["node"],
   190	            "priority": round(top["pick"], 4),
   191	            "pending": len(due),                   # 到期即待复习 (Decision-FSRS-2)
   192	            "idle_days": (None if top["idle_days"] is None else int(top["idle_days"])),
   193	            "difficulty": top["difficulty"],
   194	            "next_due": min((n["fsrs_due"] for n in members if not n["due_now"]), default=""),
   195	            "_tie": (
   196	                round(top["pick"], 8),
   197	                board_last_recommended.get(board, ""),   # 空串 = 从未被推荐, 排最前
   198	                min(n["last_examined"] for n in due),    # 空串 = 有从未考节点, 排最前
   199	                board,
   200	            ),
   201	        })
   202	    ranked.sort(key=lambda r: r["_tie"])
   203	    for r in ranked:
   204	        del r["_tie"]
   205	    upcoming.sort(key=lambda u: u["next_due"])
   206	    return ranked, upcoming, unassigned
   207	
   208	
   209	def _title(board: str) -> str:
   210	    prefix = "📚 今日复习 · "
   211	    room = TITLE_LIMIT - len(prefix)
   212	    return prefix + (board if len(board) <= room else board[: room - 1] + "…")
   213	
   214	
   215	def _body(top: dict) -> str:
   216	    idle = "从未考察" if top["idle_days"] is None else f"已闲置 {top['idle_days']} 天"
   217	    if top["pending"] >= 2:
   218	        return f"{top['top_node']} 等 {top['pending']} 节点待巩固 · {idle}"
   219	    return f"{top['top_node']} 待巩固 · {idle}"
   220	
   221	
   222	def build_payload(vault: Path, now: datetime, board_last_recommended: dict, decay):
   223	    nodes, stats, ineligible = scan_nodes(vault, now, decay)
   224	    ranked, upcoming, unassigned = rank_boards(nodes, board_last_recommended)
   225	    stats["unassigned"] = len(unassigned)
   226	    # v3 (CARD-A2): due_nodes 明细与 stats 数字同源派生 — 自洽靠构造保证,
   227	    # 本投影是全系统到期口径唯一裁判 (Dashboard 只消费不重算)
   228	    due_rows = [
   229	        {
   230	            "node": n["node"],
   231	            "board": n["board"],
   232	            "state": n["state"],
   233	            "pick": round(n["pick"], 4),
   234	            "fsrs_due": n["fsrs_due"],           # 空串 = 新卡即刻到期
   235	            "last_examined": n["last_examined"],
   236	            "difficulty": n["difficulty"],
   237	        }
   238	        for n in nodes if n["board"] and n["due_now"]
   239	    ]
   240	    stats["due_nodes"] = len(due_rows)
   241	    stats["future_nodes"] = sum(1 for n in nodes if n["board"] and not n["due_now"])
   242	    payload = {
   243	        "unassigned_nodes": unassigned,  # Code-Review M3: 点名而非只给数字
   244	        "schema_version": 3,             # v3: +due_nodes 明细 +ineligible 分桶
   245	        #                                  (纯加性; v2: FSRS WHEN 化 upcoming/due 语义)
   246	        "date": now.astimezone().date().isoformat(),
   247	        "generated_at": now.astimezone().isoformat(timespec="seconds"),
   248	        "top_boards": ranked[:3],
   249	        "upcoming": upcoming[:3],
   250	        "due_nodes": due_rows,
   251	        "ineligible": ineligible,
   252	        "stats": stats,
   253	        "notification": None,
   254	    }
   255	    day_id = f"canvas-review-{payload['date']}"
   256	    if ranked:
   257	        payload["notification"] = {
   258	            "title": _title(ranked[0]["board"]),
   259	            "body": _body(ranked[0]),
   260	            "group": "canvas复习",
   261	            "id": day_id,
   262	        }
   263	    elif upcoming:
   264	        # F1 放假语义: 有调度中的板但今天零到期 → 诚实说不用复习
   265	        nxt = upcoming[0]
   266	        payload["notification"] = {
   267	            "title": "📚 今日无到期节点",
   268	            "body": f"按计划推进，休息一天 · 最近到期 {nxt['board']} · {nxt['next_due'][:10]}",
   269	            "group": "canvas复习",
   270	            "id": day_id,
   271	        }
   272	    return payload, ranked
   273	
   274	
   275	def render_md(payload, ranked) -> str:
   276	    s = payload["stats"]
   277	    lines = [
   278	        f"# 今日复习 · {payload['date']}",
   279	        "",
   280	        f"> 生成 {payload['generated_at']} · 到期={s['due_nodes']} / 未到期={s['future_nodes']}（不含未归板）"
   281	        f" · 节点状态: new={s['new']} / legacy={s['legacy']}"
   282	        f" / 无字段={s['none']} / 未剖析跳过={s['ineligible']} / 测试排除={s['test_excluded']}"
   283	        f" / 未归板={s['unassigned']} / 损坏={s['corrupt']}",
   284	        "",
   285	        "| 板 | 优先分 | 到期待复习 | 最该考 | 难度 | 闲置 | 板内下次到期 |",
   286	        "|---|---|---|---|---|---|---|",
   287	    ]
   288	    for r in ranked:
   289	        idle = "从未考" if r["idle_days"] is None else f"{r['idle_days']} 天"
   290	        nxt = r["next_due"][:10] if r["next_due"] else "-"
   291	        diff = r["difficulty"] or "-"
   292	        lines.append(
   293	            f"| {r['board']} | {r['priority']} | {r['pending']} | {r['top_node']} | {diff} | {idle} | {nxt} |"
   294	        )
   295	    if payload.get("upcoming"):
   296	        for u in payload["upcoming"]:
   297	            lines.append(f"| {u['board']} | - | 0（未到期） | - | - | - | {u['next_due'][:10]} |")
   298	    if ranked:
   299	        lines += ["", "## 一键开考（整行复制到 Claudian）", ""]
   300	        for r in ranked:

exec
/bin/zsh -lc "git show worktree-feature-obsidian-hybrid-dev:scripts/daily_review_pick.py | nl -ba | sed -n '35,285p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
    35	PLACEHOLDER = "你的 1-2 句精准定义"
    36	
    37	#: 生产数据污染标记 (对齐 memory-health.sh 批次1'⑥ 审计清单) — 不推测试节点。
    38	#: ⚠ 只匹配文件名: 真实节点 frontmatter 可能引用测试会话 id (live 实测
    39	#: Fundamentals 的 error_candidates 含 m3-e2e-sessionend-test, 按全文匹配会误杀)
    40	TEST_MARKERS = ("TestConcept", "UAT-2.5", "m3-e2e")
    41	
    42	#: [Decision-FSRS-2] WHEN/WHAT 分工 (FSRS-V2-2026-07-30):
    43	#: FSRS 管 WHEN — fsrs_due 决定今天谁到期, 无字段 = New 卡即刻到期;
    44	#: 衰减 Beta 管 WHAT — 到期集合内按 pick=μ−σ 排序。
    45	#: 本文件保持纯 stdlib: 只做 UTC 定长字符串日期比较, 不 import fsrs。
    46	
    47	#: Bark 通知标题上限 (方案规范: ≤20 全角字符)
    48	TITLE_LIMIT = 20
    49	
    50	
    51	def _aware(s: str) -> datetime:
    52	    dt = datetime.fromisoformat(str(s).strip().replace("Z", "+00:00"))
    53	    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    54	
    55	
    56	def _fm_num(fm: str, key: str):
    57	    # 容负号 (Code-Review L5): mastery_a: -3 应进 corrupt 分支而非静默当无字段
    58	    m = re.search(rf'^{key}:\s*"?(-?[0-9]*\.?[0-9]+)"?\s*$', fm, re.M)
    59	    return float(m.group(1)) if m else None
    60	
    61	
    62	def _fm_str(fm: str, key: str):
    63	    m = re.search(rf'^{key}:\s*"?([^"\n]+?)"?\s*$', fm, re.M)
    64	    return m.group(1).strip() if m else None
    65	
    66	
    67	def _board_name(raw: str | None):
    68	    """source_board 归一化 → 板名 (live 数据实为 wikilink '[[原白板/X]]')。"""
    69	    if not raw:
    70	        return None
    71	    name = raw.strip()
    72	    if name.startswith("[[") and name.endswith("]]"):
    73	        name = name[2:-2]
    74	    name = name.split("|")[0]                 # [[path|alias]] 取 path
    75	    name = name.rsplit("/", 1)[-1].strip()    # 原白板/X → X
    76	    return name or None
    77	
    78	
    79	def scan_nodes(vault: Path, now: datetime, decay):
    80	    """扫描 节点/ 池 → (nodes, stats)。逐节点容错: 单个脏节点不崩全轮。"""
    81	    stats = {"new": 0, "legacy": 0, "none": 0, "ineligible": 0, "test_excluded": 0, "corrupt": 0}
    82	    now_z = now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    83	    nodes = []
    84	    for path in sorted((vault / "节点").glob("*.md")):
    85	        stem = path.stem
    86	        try:
    87	            text = path.read_text(encoding="utf-8")
    88	        except OSError as e:
    89	            stats["corrupt"] += 1
    90	            print(f"[pick] 读取失败跳过 {stem}: {e}", file=sys.stderr)
    91	            continue
    92	        if any(mk in stem for mk in TEST_MARKERS):
    93	            stats["test_excluded"] += 1
    94	            continue
    95	        m = re.match(r"^﻿?---\r?\n(.*?)\r?\n---\r?\n?(.*)$", text, re.S)
    96	        fm, body = (m.group(1), m.group(2)) if m else ("", text)
    97	        if PLACEHOLDER in body:
    98	            stats["ineligible"] += 1
    99	            continue
   100	
   101	        a_raw, b_raw = _fm_num(fm, "mastery_a"), _fm_num(fm, "mastery_b")
   102	        legacy = next(
   103	            (v for k in ("mastery_score", "mastery", "mastery_level")
   104	             if (v := _fm_num(fm, k)) is not None),
   105	            None,
   106	        )
   107	        if a_raw is not None and b_raw is not None:
   108	            a, b, state = a_raw, b_raw, "new"
   109	        elif legacy is not None:
   110	            a, b = decay.from_legacy(legacy)
   111	            state = "legacy"
   112	        else:
   113	            a, b, state = decay.PRIOR_A, decay.PRIOR_B, "none"
   114	        stats[state] += 1
   115	
   116	        last_exam = _fm_str(fm, "last_examined")
   117	        idle_days = None
   118	        if last_exam:
   119	            try:
   120	                idle_days = max(0.0, (now - _aware(last_exam)).total_seconds() / 86400.0)
   121	            except ValueError:
   122	                print(f"[pick] last_examined 无法解析, 按从未考: {stem}", file=sys.stderr)
   123	                last_exam = None
   124	        try:
   125	            # pick_score 也在 try 内 (Code-Review M2): 除零/溢出同属脏数据
   126	            a_eff, b_eff = decay.effective(a, b, idle_days or 0.0)
   127	            pick = decay.pick_score(a_eff, b_eff)
   128	        except (ValueError, ZeroDivisionError, OverflowError) as e:
   129	            stats["corrupt"] += 1
   130	            print(f"[pick] Beta 参数损坏跳过 {stem}: {e}", file=sys.stderr)
   131	            continue
   132	
   133	        fsrs_due = _fm_str(fm, "fsrs_due") or ""
   134	        # Code-Review M2: Obsidian Properties 面板可能把 datetime 重新序列化成
   135	        # 带偏移格式, 词法比较会反向误判「永不到期」。非规范格式 fail-open
   136	        # 视同到期 (与 New 语义一致), 不静默消失。
   137	        if fsrs_due and not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", fsrs_due):
   138	            print(f"[pick] fsrs_due 非规范格式, 视同到期: {stem} ({fsrs_due})", file=sys.stderr)
   139	            fsrs_due = ""
   140	        nodes.append({
   141	            "node": stem,
   142	            "board": _board_name(_fm_str(fm, "source_board")),
   143	            "state": state,
   144	            "pick": pick,
   145	            "idle_days": idle_days,          # None = 从未考
   146	            "last_examined": last_exam or "",
   147	            "fsrs_due": fsrs_due,
   148	            "due_now": (not fsrs_due) or fsrs_due <= now_z,  # 无字段 = New 即刻到期
   149	            "difficulty": _fm_str(fm, "fsrs_difficulty") or "",
   150	        })
   151	    return nodes, stats
   152	
   153	
   154	def rank_boards(nodes, board_last_recommended: dict):
   155	    """板级聚合: priority = min(pick), 终审 A3 tie-break。"""
   156	    boards: dict[str, list] = {}
   157	    unassigned = []
   158	    for n in nodes:
   159	        if not n["board"]:
   160	            unassigned.append(n["node"])
   161	            continue
   162	        boards.setdefault(n["board"], []).append(n)
   163	
   164	    ranked, upcoming = [], []
   165	    for board, members in boards.items():
   166	        due = [n for n in members if n["due_now"]]
   167	        if not due:
   168	            # WHEN: 全员未到期 → 不进推荐榜, 记最近的未来到期 (F1 放假语义)
   169	            nxt = min(members, key=lambda n: n["fsrs_due"])
   170	            upcoming.append({"board": board, "next_due": nxt["fsrs_due"], "node": nxt["node"]})
   171	            continue
   172	        top = min(due, key=lambda n: n["pick"])   # WHAT: 到期集合内衰减 Beta 排序
   173	        ranked.append({
   174	            "board": board,
   175	            "top_node": top["node"],
   176	            "priority": round(top["pick"], 4),
   177	            "pending": len(due),                   # 到期即待复习 (Decision-FSRS-2)
   178	            "idle_days": (None if top["idle_days"] is None else int(top["idle_days"])),
   179	            "difficulty": top["difficulty"],
   180	            "next_due": min((n["fsrs_due"] for n in members if not n["due_now"]), default=""),
   181	            "_tie": (
   182	                round(top["pick"], 8),
   183	                board_last_recommended.get(board, ""),   # 空串 = 从未被推荐, 排最前
   184	                min(n["last_examined"] for n in due),    # 空串 = 有从未考节点, 排最前
   185	                board,
   186	            ),
   187	        })
   188	    ranked.sort(key=lambda r: r["_tie"])
   189	    for r in ranked:
   190	        del r["_tie"]
   191	    upcoming.sort(key=lambda u: u["next_due"])
   192	    return ranked, upcoming, unassigned
   193	
   194	
   195	def _title(board: str) -> str:
   196	    prefix = "📚 今日复习 · "
   197	    room = TITLE_LIMIT - len(prefix)
   198	    return prefix + (board if len(board) <= room else board[: room - 1] + "…")
   199	
   200	
   201	def _body(top: dict) -> str:
   202	    idle = "从未考察" if top["idle_days"] is None else f"已闲置 {top['idle_days']} 天"
   203	    if top["pending"] >= 2:
   204	        return f"{top['top_node']} 等 {top['pending']} 节点待巩固 · {idle}"
   205	    return f"{top['top_node']} 待巩固 · {idle}"
   206	
   207	
   208	def build_payload(vault: Path, now: datetime, board_last_recommended: dict, decay):
   209	    nodes, stats = scan_nodes(vault, now, decay)
   210	    ranked, upcoming, unassigned = rank_boards(nodes, board_last_recommended)
   211	    stats["unassigned"] = len(unassigned)
   212	    stats["due_nodes"] = sum(1 for n in nodes if n["board"] and n["due_now"])
   213	    stats["future_nodes"] = sum(1 for n in nodes if n["board"] and not n["due_now"])
   214	    payload = {
   215	        "unassigned_nodes": unassigned,  # Code-Review M3: 点名而非只给数字
   216	        "schema_version": 2,             # v2: FSRS WHEN 化 (upcoming/due 语义)
   217	        "date": now.astimezone().date().isoformat(),
   218	        "generated_at": now.astimezone().isoformat(timespec="seconds"),
   219	        "top_boards": ranked[:3],
   220	        "upcoming": upcoming[:3],
   221	        "stats": stats,
   222	        "notification": None,
   223	    }
   224	    day_id = f"canvas-review-{payload['date']}"
   225	    if ranked:
   226	        payload["notification"] = {
   227	            "title": _title(ranked[0]["board"]),
   228	            "body": _body(ranked[0]),
   229	            "group": "canvas复习",
   230	            "id": day_id,
   231	        }
   232	    elif upcoming:
   233	        # F1 放假语义: 有调度中的板但今天零到期 → 诚实说不用复习
   234	        nxt = upcoming[0]
   235	        payload["notification"] = {
   236	            "title": "📚 今日无到期节点",
   237	            "body": f"按计划推进，休息一天 · 最近到期 {nxt['board']} · {nxt['next_due'][:10]}",
   238	            "group": "canvas复习",
   239	            "id": day_id,
   240	        }
   241	    return payload, ranked
   242	
   243	
   244	def render_md(payload, ranked) -> str:
   245	    s = payload["stats"]
   246	    lines = [
   247	        f"# 今日复习 · {payload['date']}",
   248	        "",
   249	        f"> 生成 {payload['generated_at']} · 到期={s['due_nodes']} / 未到期={s['future_nodes']}（不含未归板）"
   250	        f" · 节点状态: new={s['new']} / legacy={s['legacy']}"
   251	        f" / 无字段={s['none']} / 未剖析跳过={s['ineligible']} / 测试排除={s['test_excluded']}"
   252	        f" / 未归板={s['unassigned']} / 损坏={s['corrupt']}",
   253	        "",
   254	        "| 板 | 优先分 | 到期待复习 | 最该考 | 难度 | 闲置 | 板内下次到期 |",
   255	        "|---|---|---|---|---|---|---|",
   256	    ]
   257	    for r in ranked:
   258	        idle = "从未考" if r["idle_days"] is None else f"{r['idle_days']} 天"
   259	        nxt = r["next_due"][:10] if r["next_due"] else "-"
   260	        diff = r["difficulty"] or "-"
   261	        lines.append(
   262	            f"| {r['board']} | {r['priority']} | {r['pending']} | {r['top_node']} | {diff} | {idle} | {nxt} |"
   263	        )
   264	    if payload.get("upcoming"):
   265	        for u in payload["upcoming"]:
   266	            lines.append(f"| {u['board']} | - | 0（未到期） | - | - | - | {u['next_due'][:10]} |")
   267	    if ranked:
   268	        lines += ["", "## 一键开考（整行复制到 Claudian）", ""]
   269	        for r in ranked:
   270	            lines.append(f"- `/start-exam-board from {r['board']} node {r['top_node']}`")
   271	    else:
   272	        lines += ["", "> ✅ 今日无到期节点，休息一天。"]
   273	    if payload.get("unassigned_nodes"):
   274	        lines += ["", "> ⚠ 未归板节点（无 source_board，不参与推荐）: "
   275	                  + "、".join(payload["unassigned_nodes"])]
   276	    lines += [
   277	        "",
   278	        "> WHEN=FSRS 到期（无 fsrs_due 字段 = 新卡即刻到期）；WHAT=到期集合内按 μ−σ 排序",
   279	        "> （含闲置回升，证据质量半衰期 69 天）。未剖析占位节点已跳过；命令已绑定最该考节点。",
   280	    ]
   281	    return "\n".join(lines) + "\n"
   282	
   283	
   284	def atomic_write(path: Path, content: str):
   285	    tmp = path.with_suffix(path.suffix + ".tmp")

exec
/bin/zsh -lc "rg -n \"scan_nodes\\(|build_payload\\(|schema_version|due_nodes|unassigned_nodes|top_boards|upcoming|notification|generated_at|今日复习\\.json\" . --glob '"'!_bmad-output/审查/codex-review-CARD-A2.md'"' --glob '"'!frontend/obsidian-plugin/node_modules/**'"' --glob '"'!backend/.venv/**'"'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
 succeeded in 0ms:
./config/alerts.yaml:147:notification:
./frontend/obsidian-plugin/src/configure-whiteboard.ts:49:  schema_version?: string;
./frontend/obsidian-plugin/src/configure-whiteboard.ts:83:    schema_version: out.schema_version ?? undefined,
./frontend/obsidian-plugin/src/onboarding-helpers.ts:48:schema_version: "2.0-multi-vault-2026-05-10"
./frontend/obsidian-plugin/src/exam-quick.ts:14: *   POST /api/v1/exam/quick  body: {node_id, vault_id?}   resp: {question_id, question_text, generated_at?}
./frontend/obsidian-plugin/src/exam-quick.ts:79:    `generated_at: ${input.generatedAt ?? new Date().toISOString()}`,
./frontend/obsidian-plugin/src/exam-quick.ts:237:      generated_at?: string;
./frontend/obsidian-plugin/src/exam-quick.ts:252:      generatedAt: r.generated_at,
./frontend/obsidian-plugin/tests/exam-quick.test.ts:103:  test("含 frontmatter 5 字段 (exam_question_id / source_concept / generated_at / exam_status)", () => {
./frontend/obsidian-plugin/tests/exam-quick.test.ts:113:    assert.ok(body.includes("generated_at: 2026-05-14T10:00:00Z"));
./frontend/obsidian-plugin/tests/exam-quick.test.ts:146:    assert.match(body, /generated_at: \d{4}-\d{2}-\d{2}T/);
./frontend/obsidian-plugin/tests/onboarding-helpers.test.ts:75:  test("生成含必需字段的 yaml (vault_id / display_name / subject / schema_version)", () => {
./frontend/obsidian-plugin/tests/onboarding-helpers.test.ts:80:    assert.ok(yaml.includes('schema_version: "2.0-multi-vault-2026-05-10"'));
./frontend/obsidian-plugin/tests/configure-whiteboard.test.ts:66:schema_version: "1.0-flat-architecture-2026-04-20"
./canvas-vault/Dashboard.md:14:> **数据源**：Plugin 实时从 `原白板/*.md` 和 `节点/*.md` 的 frontmatter 自动聚合。手动派生 / 追加 / 配置后**无需刷新**，DataviewJS 会自动重算。**例外**：FSRS 到期数消费 `outputs/今日复习.json` 投影（daily_review_pick 是到期口径唯一裁判，每日 9:05 生成），不做独立重算。
./canvas-vault/Dashboard.md:52://    这里只消费 outputs/今日复习.json 投影 (schema v3), 不再独立重算 —
./canvas-vault/Dashboard.md:54:let fsrsLine = "⏳ 投影未生成 — `outputs/今日复习.json` 缺失（每日复习任务每天 9:05 自动生成，生成后此处自动出数）";
./canvas-vault/Dashboard.md:57:  const raw = await dv.io.load("outputs/今日复习.json");
./canvas-vault/Dashboard.md:60:    const hasDetail = Array.isArray(proj.due_nodes);
./canvas-vault/Dashboard.md:61:    const dueCnt = hasDetail ? proj.due_nodes.length : (proj.stats?.due_nodes ?? 0);
./canvas-vault/Dashboard.md:62:    const newCardCnt = hasDetail ? proj.due_nodes.filter(d => !d.fsrs_due).length : null;
./canvas-vault/Dashboard.md:70:    parts.push(`投影生成于 ${proj.generated_at ?? "?"}`);
./canvas-vault/Dashboard.md:74:  fsrsLine = "⚠️ 投影损坏 — `outputs/今日复习.json` 解析失败，等下次生成自动覆盖修复";
./_bmad-archive/archived-v2/epic-7/7-2-prescriptive-wording-status.md:60:  - [ ] 2.2 端点返回结构：`{concepts: [{name, mastery_score, zone, label, due_date}], generated_at}`
./_bmad-output/审查/2026-07-29-ChatGPT终审全文-每日复习推送+本地模型栈.md:52:- last_generate_date/last_push_date 分开必要但不充分，还缺：持久化 payload（今日复习.json）、原子状态写（os.replace）、运行锁（mkdir lock）、传输成功校验（--fail-with-body + 解析响应）、Bark 端幂等 ID。
./_bmad-output/审查/2026-07-29-ChatGPT终审全文-每日复习推送+本地模型栈.md:54:- 网络 exactly-once 本地做不到 → 用 Bark 官方稳定 `id`（同 ID 更新已有通知）：本地 at-least-once + Bark notification ID 幂等更新。
./_bmad-output/审查/2026-07-29-ChatGPT终审全文-每日复习推送+本地模型栈.md:118:4. 持久化今日复习.json
./_bmad-output/审查/2026-07-29-ChatGPT终审全文-每日复习推送+本地模型栈.md:120:6. Bark 改 JSON POST /push + 每日稳定 notification ID
./_bmad-output/审查/2026-05-26-graphiti-sprint-2-决策清单.md:117:  "schema_version": "CanvasGraphEpisodeV1",
./scripts/send_bark.py:8:  - 同日稳定 notification id → Bark 端幂等更新 (本地 at-least-once +
./scripts/send_bark.py:58:def send(notification: dict) -> int:
./scripts/send_bark.py:66:            "title": notification["title"],
./scripts/send_bark.py:67:            "body": notification["body"],
./scripts/send_bark.py:68:            "group": notification.get("group", "canvas复习"),
./scripts/send_bark.py:69:            "id": notification["id"],
./scripts/send_bark.py:104:    ap.add_argument("--payload", required=True, help="今日复习.json 路径")
./scripts/send_bark.py:107:    noti = payload.get("notification")
./scripts/daily_review_run.py:12:  A7: payload 持久化 今日复习.json (生成成功推送失败 → 补跑只补推送)
./scripts/daily_review_run.py:41:    "    display notification (item 2 of argv) with title (item 1 of argv)\n"
./scripts/daily_review_run.py:55:        return {"schema_version": 1, "board_last_recommended": {}}
./scripts/daily_review_run.py:68:        return {"schema_version": 1, "board_last_recommended": {}}
./scripts/daily_review_run.py:87:    payload_path = VAULT / "outputs" / "今日复习.json"
./scripts/daily_review_run.py:99:    payload, ranked = picker.build_payload(
./scripts/daily_review_run.py:148:    noti = (payload or {}).get("notification")
./_bmad-output/审查/2026-07-29-ChatGPT终审吸收与代码验证.md:45:3. `scripts/daily_review_pick.py`：三态兼容 + eligibility 过滤（复用「你的 1-2 句精准定义」占位符规则）+ 板级 min(pick) + tie-break（board_last_recommended → oldest last_examined → 板名）+ 输出①今日复习.md（含三态统计行 + 每板 `/start-exam-board from <板> node <top_node>`）②**今日复习.json 持久化 payload**
./_bmad-output/审查/2026-08-20-Codex四轮终裁-九路验证与C批次方案.md:13:| V3 | `{"snapshot_schema_version":3,"freshness":[]}` → `:956` AttributeError 被 B3 外层兜底吞成"写失败" return False → 坏快照**永不自愈**（settrace 定位实证）。B3 前该输入直接 live 500——B3 把崩溃降为静默不自愈，F-05 成立 F-04 未兑现 | B3 不完整 |
./_bmad-archive/archived-v2/epic-1/1-5-obsidian-git-backup.md:41:  - [ ] 1.3 说明推荐配置：Auto backup interval = 30 min，Disable notifications = true（避免打断学习），Commit message = "auto-backup: {{date}}"
./_bmad-output/审查/rag-scale_pack_2026-08-02.md:660:    schema_version: Literal["CanvasGraphEpisodeV1"] = "CanvasGraphEpisodeV1"
./_bmad-output/审查/rag-scale_pack_2026-08-02.md:3072:schema_version: "2.0-multi-vault-2026-05-10"
./_bmad-output/审查/rag-scale_pack_2026-08-02.md:6209:backend 返回的 JSON 结构是 `{question_id: uuid, question_text: str, generated_at: iso}`。
./_bmad-output/审查/rag-scale_pack_2026-08-02.md:6228:generated_at: {当前 ISO 8601 时间戳}
./_bmad-output/审查/2026-05-26-chatgpt-graphiti-deep-research-报告.md:52:  "schema_version": "CanvasGraphEpisodeV1",
./_bmad-output/审查/r11-evidence-2026-08-17/e2-snapshot-slimming.json:21:    "generated_at": "2026-08-15T01:55:53.603279+00:00",
./scripts/daily_review_pick.py:5:→ outputs/今日复习.md (人读) + outputs/今日复习.json (推送 payload, 终审 A7:
./scripts/daily_review_pick.py:9:唯一裁判 — Dashboard.md 直接 dv.io.load 消费 due_nodes 明细 + ineligible
./scripts/daily_review_pick.py:11:(daily_review_run/send_bark 只读 notification) 被动兼容。
./scripts/daily_review_pick.py:84:def scan_nodes(vault: Path, now: datetime, decay):
./scripts/daily_review_pick.py:178:    ranked, upcoming = [], []
./scripts/daily_review_pick.py:184:            upcoming.append({"board": board, "next_due": nxt["fsrs_due"], "node": nxt["node"]})
./scripts/daily_review_pick.py:205:    upcoming.sort(key=lambda u: u["next_due"])
./scripts/daily_review_pick.py:206:    return ranked, upcoming, unassigned
./scripts/daily_review_pick.py:222:def build_payload(vault: Path, now: datetime, board_last_recommended: dict, decay):
./scripts/daily_review_pick.py:223:    nodes, stats, ineligible = scan_nodes(vault, now, decay)
./scripts/daily_review_pick.py:224:    ranked, upcoming, unassigned = rank_boards(nodes, board_last_recommended)
./scripts/daily_review_pick.py:226:    # v3 (CARD-A2): due_nodes 明细与 stats 数字同源派生 — 自洽靠构造保证,
./scripts/daily_review_pick.py:240:    stats["due_nodes"] = len(due_rows)
./scripts/daily_review_pick.py:243:        "unassigned_nodes": unassigned,  # Code-Review M3: 点名而非只给数字
./scripts/daily_review_pick.py:244:        "schema_version": 3,             # v3: +due_nodes 明细 +ineligible 分桶
./scripts/daily_review_pick.py:245:        #                                  (纯加性; v2: FSRS WHEN 化 upcoming/due 语义)
./scripts/daily_review_pick.py:247:        "generated_at": now.astimezone().isoformat(timespec="seconds"),
./scripts/daily_review_pick.py:248:        "top_boards": ranked[:3],
./scripts/daily_review_pick.py:249:        "upcoming": upcoming[:3],
./scripts/daily_review_pick.py:250:        "due_nodes": due_rows,
./scripts/daily_review_pick.py:253:        "notification": None,
./scripts/daily_review_pick.py:257:        payload["notification"] = {
./scripts/daily_review_pick.py:263:    elif upcoming:
./scripts/daily_review_pick.py:265:        nxt = upcoming[0]
./scripts/daily_review_pick.py:266:        payload["notification"] = {
./scripts/daily_review_pick.py:280:        f"> 生成 {payload['generated_at']} · 到期={s['due_nodes']} / 未到期={s['future_nodes']}（不含未归板）"
./scripts/daily_review_pick.py:295:    if payload.get("upcoming"):
./scripts/daily_review_pick.py:296:        for u in payload["upcoming"]:
./scripts/daily_review_pick.py:304:    if payload.get("unassigned_nodes"):
./scripts/daily_review_pick.py:306:                  + "、".join(payload["unassigned_nodes"])]
./scripts/daily_review_pick.py:350:    payload, ranked = build_payload(vault, now, blr, load_decay(vault))
./scripts/daily_review_pick.py:355:        atomic_write(out / "今日复习.json",
./_bmad-output/研究/2026-08-17-R11-下一批次开发清单-第2批数据边界与可信基线.md:114:| P1-01 快照旧版不迁移 | ✅ **接受已修** | 属实。加 `snapshot_schema_version`，版本落后强制重写 + load 对 v1 fail closed。全盘清点现存快照 1 份，已脱敏 |
./docs/project-status/orphan-code.md:118:| notification_channels.py | NotificationChannel (ABC) | — | 基础设施 |
./scripts/install-vault.sh:108:schema_version: "2.0-multi-vault-2026-05-10"
./_bmad-archive/archived-v2/epic-3/3-6-progressive-hints.md:58:  - [ ] 1.3 `HintResult`：`{ hint_id, hint_level, hint_text, question_id, generated_at }`
./_bmad/tea/testarch/knowledge/test-quality.md:364:  // 100 lines of notification preferences
./_bmad/tea/testarch/knowledge/test-quality.md:365:  await page.click('[data-testid="notification-settings"]');
./_bmad/tea/testarch/knowledge/test-quality.md:434:test('admin can update notification preferences', async ({ adminPage, seedUser }) => {
./_bmad/tea/testarch/knowledge/test-quality.md:437:  await adminPage.goto(`/admin/users/${user.id}/notifications`);
./_bmad/tea/testarch/knowledge/test-quality.md:438:  await adminPage.check('[data-testid="email-notifications"]');
./_bmad/tea/testarch/knowledge/test-quality.md:439:  await adminPage.uncheck('[data-testid="sms-notifications"]');
./_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md:141:4. state、lock、log、notification ID 和 `board_last_recommended` 未完整带 vault ID，两个 vault 同日运行会互相影响。
./_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md:265:- [ ] pending journal、state、lock、log、notification ID 和 board 历史全部按 vault 命名空间。
./_bmad-output/审查/rag-p0_pack_2026-08-02.md:22801:        1. .canvas-config.yaml `vault_id` field (explicit, schema_version >= 2.0)
./_bmad-output/审查/rag-p0_pack_2026-08-02.md:23622:from app.services.notification_channels import create_default_dispatcher  # noqa: E402
./_bmad-output/审查/rag-p0_pack_2026-08-02.md:23669:    notification_dispatcher = create_default_dispatcher()
./_bmad-output/审查/rag-p0_pack_2026-08-02.md:23672:        notification_dispatcher=notification_dispatcher,
./_bmad/tea/testarch/knowledge/feature-flags.md:43:  DISABLE_EMAIL_NOTIFICATIONS: 'disable-email-notifications',
./_bmad-output/审查/daily-review-push-and-local-llm_pack_2026-07-29.md:125:- 输出②：stdout 单行 JSON `{top_boards:[{board,top_node,pending,idle_days}]}`
./_bmad-output/审查/daily-review-push-and-local-llm_pack_2026-07-29.md:129:- 顺序铁律：md 先落盘 → Bark（`curl -m 10 --retry 2 "$PUSH_URL/📚 今日复习 · <top1板名>/<正文>?group=canvas复习"`，push.env 缺失记「跳过(未配置)」不算错）→ 失败 `osascript -e 'display notification ...'` 兜底
./_bmad/tea/testarch/knowledge/selector-resilience.md:170:    const firstNotification = page.getByTestId('notification').nth(0);
./_bmad/tea/testarch/knowledge/selector-resilience.md:174:    // await page.getByTestId('notification').nth(5).click()
./_bmad/tea/testarch/knowledge/selector-resilience.md:177:    await page.getByTestId('notification').filter({ hasText: 'Critical Alert' }).click();
./docs/community-product-research.md:171:- History tracking and change notifications built-in
./_bmad-archive/test-artifacts/tea-trace-coverage-matrix-epic34.json:3:  "generated_at": "2026-02-10T12:00:00Z",
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-envelope-generation-v1.py:4992:        "schema_version": "gov-01-toolchain-static-envelope-generation-envelope-v1",
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-envelope-generation-v1.py:5190:            "schema_version", "artifact_type", "artifact_id", "plan_id", "state",
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-envelope-generation-v1.py:5201:        "schema_version": "gov-01-toolchain-static-envelope-generation-envelope-v1",
./_bmad-archive/test-artifacts/tea-trace-coverage-matrix-epic35.json:3:  "generated_at": "2026-02-11T12:00:00Z",
./_bmad-output/审查/phase0a-annotation-truth/2026-08-20-GOV-01-追踪真相源修复决策稿.md:134:schema_version: cls-current-task-v2
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-envelope-generation-envelope-v1.GOV01-GEN-20260823-7d4b43294a931ef8824df1d9d36a41dfe4b29737d639cd30407a4c1d28556827.json:1:{"approval_challenge_id":"GOV01-GEN-20260823-7d4b43294a931ef8824df1d9d36a41dfe4b29737d639cd30407a4c1d28556827","artifact_id":"GOV-01-STATIC-ENVELOPE-GENERATION-20260823-407a4c1d28556827","artifact_type":"gov-01-toolchain-static-envelope-generation-envelope","artifacts":[{"byte_length":77024,"file_kind":"regular","path":"_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md","raw_file_sha256":"4841abe51a29110be92f1d6810d02654a82e8e2be9c4f922c0541561246ca512","role":"goal"},{"byte_length":42685,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/2026-08-20-GOV-01-追踪真相源修复决策稿.md","raw_file_sha256":"836a18560bc50d2fdd5c6c86c1de8b310498c523fb0e777abf117863d18f3b2a","role":"governance-decision"},{"byte_length":39848,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/2026-08-20-Phase0A-A01-A02-批注真相层实施契约.md","raw_file_sha256":"da0acd5558ef9669c3f2b948464e5ceda72288895d0bb3a3b4571b5bbd94b540","role":"phase0a-contract"},{"byte_length":8954,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-first-receipt-envelope-v1.json","raw_file_sha256":"0b73b83e1dbd92dd0a4684a83438dafc7afae6a6fde42b4130d776d7ee246410","role":"first-receipt-envelope"},{"byte_length":17623,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-first-receipt-envelope-v1.schema.json","raw_file_sha256":"bb680b866b89fad649953e23da1a8ba9e3529523485516ebd969849bff468298","role":"first-receipt-schema"},{"byte_length":5110,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/2026-08-20-GOV-01-Bootstrap-0-safe-mode.patch","raw_file_sha256":"d2f9a1ff45006cf19bd5295b751e2b620dc6043d6ec1ff26494c1d2d722aa8aa","role":"bootstrap-patch"},{"byte_length":13463,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-control-prep-envelope-v1.json","raw_file_sha256":"ef424f80672568076d750ae0f6d662ebfdae242fdea8fcda2b37f39e6406945b","role":"control-prep-envelope"},{"byte_length":23437,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-control-prep-envelope-v1.schema.json","raw_file_sha256":"5c6c07ffe71a8c39a6993b2c717b751988b94338800972bbcfe93363a152f984","role":"control-prep-schema"},{"byte_length":291290,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-envelope-generation-v1.py","raw_file_sha256":"c6745b954a3647d52e40d05773af0961b116134363239ceaa0bd1f5e64772f6c","role":"static-envelope-generator"},{"byte_length":41393,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-envelope-generation-envelope-v1.schema.json","raw_file_sha256":"547633e952c77e1b850ca3c8874bc6704286169afa98f275475fac9b0130132a","role":"generation-envelope-schema"},{"byte_length":255338,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-envelope-generation-hostile-fixtures-v1.py","raw_file_sha256":"9bcf6a61c97647436af7451ac386e5ba9cd0a4a13aee6b95143e8ebf19097682","role":"generation-hostile-fixture"},{"byte_length":715949,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py","raw_file_sha256":"6c6e31b70714af46ed6d6c1eb794487e49631e189c15f663b418d422dfa8c131","role":"static-executor"},{"byte_length":50895,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-verifier-v2.py","raw_file_sha256":"98bcaaa35e2e4e7713e51e016af6c7223713acdb47a1b4b27859e70f75725064","role":"static-verifier"},{"byte_length":389578,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-static-acquisition-hostile-fixtures-v2.py","raw_file_sha256":"692e409bedbd1a32f365dfec7a49afd8fecd98af743a4564d93777f41fdd3f07","role":"static-hostile-fixture"},{"byte_length":100919,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-envelope-v2.schema.json","raw_file_sha256":"d31c617bb20cc30c46d64f9556caf3d5e22032ac04b7b25249b40339ddbc328c","role":"pending-envelope-schema"},{"byte_length":98752,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-private-evidence-v2.schema.json","raw_file_sha256":"90db2312de86f62869109f7b716f861080e9ffc0d686eb6c2c0dc759ca2b26fd","role":"private-evidence-schema"},{"byte_length":195320,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-public-attestation-v2.schema.json","raw_file_sha256":"4b878030491bee3438184e44a15c56d1e9cdd4e6c85c161212f58d3b63906736","role":"public-attestation-schema"},{"byte_length":817,"file_kind":"regular","path":"package.json","raw_file_sha256":"bd5c4e933e2dcbf7f2019bec9fec555b5b1adff1c4a6e5c36ea4415ff9a711fe","role":"package-manifest"},{"byte_length":83153,"file_kind":"regular","path":"package-lock.json","raw_file_sha256":"c6e190741427b99ff132d6504b2a782d75c418d6ae93066769ac422bff6b7cea","role":"package-lock"},{"byte_length":5413,"file_kind":"regular","path":".gitignore","raw_file_sha256":"679c83badb0067729c75a48f9391849542fc71a03c133d8d0dc33cfe7e836351","role":"gitignore"}],"authorized_reads":{"git_generation_output_exclusion":"exclude exactly the one derived regular-file generation output path from Git status and dirty-content commitment; never exclude its parent directory or a wildcard subtree; separately require output preimage ABSENT and later bind raw output bytes by the external acquisition receipt","npm_cache_index_read_count":0,"private_roles_after_approval":["exact 0600 32-byte hmac.key for domain-separated HMAC only","derived control root and claims metadata plus exact fresh acquisition challenge child absence","exact locator-free canonical control-preparation receipt content for predecessor-chain verification","Git marker commondir local config index refs contained hooks and dirty or untracked metadata and regular content, with Vault and .obsidian paths rejected before open","package-lock-selected direct-SRI npm cache content-v2 blobs only","target-worktree-associated Claude process census evidence"],"public_repo_artifact_policy":"only exact versioned artifact paths listed in this envelope plus package.json package-lock.json .gitignore and Git control evidence required by the frozen static executor","user_or_managed_settings_read_count":0,"vault_read_count":0},"authorized_subprocesses":{"environment_profile":"new exact sanitized environment; HOME=/var/empty and TMPDIR=DARWIN_USER_TEMP_DIR=/tmp; every Git child starts only after fchdir to the exact identity-bound adapter Git directory and uses relative --git-dir=.; bootstrap Git receives only exact captured GIT_OBJECT_DIRECTORY while global/system config, inherited alternates and protocols are disabled; final Git evidence unsets live object access and uses only the sealed adapter; fsmonitor, hooks, attributes, includes, alternates, grafts, network, and worktree reads are rejected or sandbox-denied","git_child_sandbox_profile":"every Git child calls /usr/lib/libsandbox.1.dylib sandbox_init exactly once before exec with a generated default-deny profile; before every Git exec the parent passes only one per-child duplicate of the pinned adapter-Git directory FD, and preexec performs fchdir of that exact identity, closes the duplicate, then calls sandbox_init exactly once; no usable directory FD reaches Git, fixed argv uses relative --git-dir=., and no path discovery is permitted; the git-metadata-adapter-bootstrap role permits only the content-bound CommandLineTools tree, one unsealed checkpoint-scoped private-temporary adapter, captured live pack or loose object containers needed to extract the exact approved OID set, and adapter-only writes needed by index-pack; it denies network, worktree payload, every live Git control path, alternates and graft bytes, and all other reads or writes; after source CAS and sealing, git-read-only-evidence permits only the CommandLineTools tree and sealed adapter and denies writes and all live Git or worktree reads; the parent revalidates captured live source before adapter removal; every child profile explicitly denies create rename unlink or write authority over the private-temporary parent namespace and sibling adapter roots, while index-pack writes are restricted to the pinned current adapter objects/pack directory; sandbox initialization failure is terminal; /usr/bin/sandbox-exec is never executed","network_allowed":false,"node_npm_npx_openspec_allowed":false,"roles":["xcode-select-resolver","xcrun-resolver","git-metadata-adapter-bootstrap","git-read-only-evidence","pgrep-read-only-evidence","lsof-read-only-evidence"],"shell_allowed":false},"challenge_and_time_contract":{"acquisition_entropy":"exactly one os.urandom(32) call after generation approval and before private census; lowercase 64-hex suffix; caller-supplied entropy forbidden","challenge_date_binding":"each challenge YYYYMMDD component equals its own canonical UTC issued or census date","clock_skew_ceiling_seconds":300,"expiry_checkpoints":["micro-envelope load","immediately before the persistent generation claim mkdir","after generation claim verification and immediately before the public output create","after output reopen before emitting pending-user-confirmation"],"generation_entropy":"exactly one os.urandom(32) call before the public generation micro-envelope is written; lowercase 64-hex suffix; caller-supplied entropy forbidden","namespace_separation":"generation challenge uses GOV01-GEN and acquisition challenge uses GOV01-SA; equality or cross-namespace reuse is impossible by grammar","ttl_ceiling_seconds":86400},"encoding_profile":"UTF-8-NFC-LF-no-BOM-no-duplicate-json-keys","failure_contract":{"existing_complete_output":"under the same still-valid exact GEN receipt, authenticate the retained generation claim, reuse only its fixed acquisition challenge and timestamps, revalidate every public and private commitment including hmac.key-derived commitments, require rebuilt raw bytes exact, then re-emit the same raw receipt digest without writing anything","existing_partial_or_invalid_output":"a partial or invalid generation claim is terminal consumed; a valid claim with absent output may recreate only its exact fixed raw output; any partial invalid or drifted existing output is retained and requires a new generation micro-envelope","post_create_failure":"after the generation claim mkdir, retain claim record and any output bytes and stop; never truncate delete overwrite repair or mint another acquisition challenge from this generation authority","pre_output_failure":"before the generation claim mkdir, no persistent repository control product claim or output write; the exact approved preflight may use only checkpoint-scoped private-temporary Git metadata adapters and may rerun before expiry only after exact cleanup with zero residue while every bound input is unchanged and both claim and output remain absent","retry_policy":"single-use begins at successful exclusive generation claim mkdir; only a pre-claim failure with confirmed temporary-adapter cleanup and zero residue may rerun within the exact receipt TTL; every post-claim path is pinned to the claim-authenticated acquisition challenge timestamps and final raw digest","temporary_adapter_failure":"adapter cleanup failure root-identity uncertainty or any residue is terminal fail-closed for this attempt: do not publish, do not report retryable, retain evidence for private inspection, and require new authority before another attempt"},"generation_claim_contract":{"generation_claim_profile":"exclusive-0700-generation-claim-directory-with-exclusive-0600-canonical-HMAC-record-v1","generation_claim_record_profile":"HMAC-SHA-256 with the authorized 32-byte private key over ASCII(CLS/GOV01/STATIC-ENVELOPE-GENERATION-CLAIM/v1) || NUL || uint64be(canonical-body-byte-length) || canonical JSON binding GEN receipt/raw, C1/C2 identities, one SA/time tuple and final raw SHA-256/bytes/domain receipt","generation_claim_required":true,"generation_claim_retention":"retain permanently; never delete, overwrite or repair; a complete valid claim permits only byte-exact recovery with its recorded SA and times"},"issued_at_utc":"2026-08-23T09:43:45Z","locator_derivation_contract":{"cache_root":"pwd.getpwuid(the control-preparation expected created uid).pw_dir plus exact suffix .npm; normalize once, require absolute realpath equality, owner uid equality, no symlink component and no Vault component","caller_supplied_locator_count":0,"claims_root":"exact direct child claims beneath the derived state root; validate retained GOV01-SA claim directories and generation-claim-GOV01-GEN directories, require this GEN claim preimage ABSENT before fresh entropy, and require the fresh acquisition challenge child preimage ABSENT","final_locator_commitment_timing":"resolve derived private locators and calculate domain-separated keyed commitments only after approval; serialize commitments but never raw private locators into the final acquisition envelope","generation_output":"repo root plus exact control-prefix regular-file name GOV-01-toolchain-static-acquisition-pending-<approved-GOV01-GEN-challenge>.json; the final envelope separately carries one fresh GOV01-SA acquisition challenge","key_file":"exact direct child hmac.key beneath the derived state root","repo_root":"derive from the no-symlink realpath of the content-addressed generator __file__ by removing its exact repo-relative suffix","state_root":"read the exact target.absolute_path from the content-addressed committed control-preparation envelope only after this generation receipt is approved"},"mutation_scope":{"allowed_ephemeral_mutations":["create one fresh unique checkpoint-scoped private-temporary 0700 Git metadata adapter for each production Git evidence checkpoint after the applicable public issue invocation or exact GEN receipt has authorized Git inspection; permit at most one active adapter owner within a process","write only its 0600 sanitized Git control metadata through pinned root and Git directory FDs; resolve bootstrap and import argv only from the identity-bound adapter Git cwd with relative --git-dir=., keep index-pack pack/index output beneath objects/pack, verify every exact-OID partial-pack object hash, then seal files 0400 beneath 0500 directories through pinned FDs; no adapter locator or raw metadata may enter public output","within the declared trust boundary and host assurance, remove the unique registered adapter at its authorized pathname only after captured root and Git identity checks, then require authorized-path absence and zero registry residue before success or retryable pre-claim failure"],"allowed_persistent_mutations":["create and fsync exactly one previously-absent 0700 generation claim directory beneath the existing receipt-bound claims container","create and fsync exactly one 0600 canonical HMAC-authenticated generation-record.json beneath that claim and fsync both claim and claims directories","create and fsync exactly one previously-absent public acquisition envelope regular file beneath the repository control prefix","fsync its already-existing parent directory"],"commit_allowed":false,"first_authority_consuming_persistent_write":"exclusive mkdirat of exact claims/generation-claim-<approved-GOV01-GEN-challenge> mode 0700 after every private read schema manual privacy and drift check has passed; EEXIST permanently forbids minting another acquisition challenge","git_metadata_adapter_cleanup_guarantee":"under the declared Git metadata adapter trust boundary and host assurance, cleanup success or retryable pre-claim failure requires pre-removal root and Git identity agreement, authorized-path removal, post-removal absence, and zero pathname and registry residue; any observed root or Git identity drift, missing authorized pathname, cleanup error, or residue is terminal and quiescence must fail; preservation against a non-cooperating same-UID replacement at the final pathname-deletion linearization point is outside the supported guarantee","git_metadata_adapter_host_assurance":"every spawned Git child is sandboxed and has no authority to create, rename, unlink or write the private-temporary parent namespace or any sibling adapter root; the product owns only the fresh exact adapter entry, root and descendants for that invocation, while /private/tmp and sibling entries remain ambient host namespace; every product invocation creates one fresh unique adapter root; the process-wide non-reentrant scope and registry forbid interleaved adapter ownership within one process and do not claim cross-process exclusion","git_metadata_adapter_trust_boundary":"the kernel and each owning same-UID production process are trusted; POSIX 0600 and 0700 modes isolate other UIDs but do not isolate an unsandboxed process with the same effective UID, so each adapter root has exactly one owning process and compliant same-UID product processes never mutate another invocation's root; non-cooperating same-UID filesystem mutation, out-of-process ptrace or code injection, and out-of-process access to the 0600 private HMAC key are outside the supported threat model","output_mode":"0644","overwrite_allowed":false,"product_state_cleanup_allowed":false,"push_allowed":false,"sidecar_allowed":false,"temporary_adapter_cleanup_required":true,"temporary_adapter_residue_allowed":false,"temporary_git_metadata_adapter_profile":"checkpoint-scoped-private-temp-sanitized-required-path-ancestor-exact-oid-index-root-proven-one-exact-public-opaque-gitlink-identity-bound-git-fd-metadata-adapter-v5"},"not_after_utc":"2026-08-24T09:43:45Z","plan_id":"PLAN-CLS-PRODUCTIVITY-2026-08-20","predecessor":{"bootstrap_commit_oid":"0e0f0150be184f4dad83a859b0fdd232ec53e8b5","bootstrap_patch_raw_sha256":"d2f9a1ff45006cf19bd5295b751e2b620dc6043d6ec1ff26494c1d2d722aa8aa","control_preparation_envelope_raw_sha256":"ef424f80672568076d750ae0f6d662ebfdae242fdea8fcda2b37f39e6406945b","control_preparation_receipt_domain_sha256":"dbb28c7627b63989e98b70ff608c20976d687541364af95804537dda7867541c","control_preparation_state":"independently-verified-control-prepared","first_approval_envelope_raw_sha256":"0b73b83e1dbd92dd0a4684a83438dafc7afae6a6fde42b4130d776d7ee246410","first_receipt_domain_sha256":"c89e7195e67b60a26117469e2b212fb508c0a5a64cac5d25a59a257f73b55740","static_contract_commit_oid":"c1990df5395267058a8ec74e415a2ae646d3c261","static_contract_tree_oid":"e85de91908491becb7a334b3f30ef8202bf1eac9"},"privacy":{"git_metadata_adapter_trust_boundary":"the kernel and each owning same-UID production process are trusted; POSIX 0600 and 0700 modes isolate other UIDs but do not isolate an unsandboxed process with the same effective UID, so each adapter root has exactly one owning process and compliant same-UID product processes never mutate another invocation's root; non-cooperating same-UID filesystem mutation, out-of-process ptrace or code injection, and out-of-process access to the 0600 private HMAC key are outside the supported threat model","graphiti_call_count":0,"network_call_count":0,"private_key_publication_allowed":false,"raw_command_output_publication_allowed":false,"raw_private_locator_public_count":0,"vault_read_count":0,"whole_envelope_checker":"field-aware recursive checker before write and before stdout; repo paths use strict relative grammar; tool logical IDs and versions use role-specific ASCII grammar; only schema-enumerated fixed public system command locators and placeholders are allowed; all other absolute home file-URI Vault .obsidian control bidi and secret-bearing values are rejected"},"receipt_digest_profile":"SHA-256(ASCII(CLS/GOV01-STATIC-ENVELOPE-GENERATION-RECEIPT/v1) || NUL || raw-envelope-bytes); digest supplied by user and stored externally","repository_transition":{"approved_commit_shape":"current HEAD has exactly one parent equal to authorization_baseline_head; a path-local Merkle comparison of authenticated current and parent ancestor tree objects proves exactly the micro envelope regular file was added with bytes equal to the approved raw envelope and every non-target entry is byte-identical; no other path is added modified deleted renamed or type-changed","authorization_baseline_head":"c1990df5395267058a8ec74e415a2ae646d3c261","authorization_baseline_head_ref_bytes":47,"authorization_baseline_head_ref_profile":"SHA-256(ASCII(CLS/GOV01-STATIC-ENVELOPE-HEAD-REF/v1) || NUL || exact symbolic HEAD ref ASCII bytes); raw ref is never serialized","authorization_baseline_head_ref_sha256":"c58034b19de75ff292906142ab44cd41a8b688b48862a63dd8c01f42040459d2","authorization_baseline_head_symbolic":true,"authorization_baseline_other_refs_bytes":3648,"authorization_baseline_other_refs_sha256":"56d06c459e4cff8a2a871f24b2b335f1739edee6126eb5a8f9be4ecb84016b3d","authorization_baseline_tree":"e85de91908491becb7a334b3f30ef8202bf1eac9","captured_index_root_profile":"strict captured DIRC v2 or v3 canonical bottom-up root-tree recomputation equal to authenticated HEAD; require the mode 160000 opaque-leaf path set to equal the exact public singleton _reference/obsidian-sample-plugin without opening requesting or dereferencing its object OID; reject a missing or mode-replaced singleton and every extra or substituted gitlink; in a parsed required-path ancestor tree permit that same singleton only as an unselected opaque sibling, and reject it if selected as a required terminal or ancestor","generation_output_preimage":"ABSENT","generation_output_repo_relative":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-pending-GOV01-GEN-20260823-7d4b43294a931ef8824df1d9d36a41dfe4b29737d639cd30407a4c1d28556827.json","git_control_profile":{"alternate_object_controls_absent":true,"common_directory_relation":"git-directory-contained-under-common-worktrees","include_controls_absent":true,"marker_kind":"gitfile"},"index_must_equal_head":true,"issue_publication_checkpoint_profile":"capture one initial exact Git-source index-root and public-artifact checkpoint; while holding a nonblocking advisory lock on the exact shared control-parent directory FD, recapture an equal checkpoint immediately before micro-envelope O_EXCL and require both micro and generation-output preimages absent; after fsync and same-FD byte-exact reopen, require generation-output absence, recapture the same equal checkpoint, and require generation-output absence again before success","micro_envelope_preimage":"ABSENT","micro_envelope_repo_relative":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-envelope-generation-envelope-v1.GOV01-GEN-20260823-7d4b43294a931ef8824df1d9d36a41dfe4b29737d639cd30407a4c1d28556827.json","refs_except_head_must_be_unchanged":true},"schema_binding":{"content_addressed_manual_checker_required":true,"external_draft202012_validation_required":true,"schema_artifact_path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-envelope-generation-envelope-v1.schema.json","schema_id":"urn:canvas-learning-system:gov-01:toolchain-static-envelope-generation-envelope:v1","schema_raw_file_sha256":"547633e952c77e1b850ca3c8874bc6704286169afa98f275475fac9b0130132a","whole_envelope_privacy_checker_required":true},"schema_version":"gov-01-toolchain-static-envelope-generation-envelope-v1","single_use":true,"state":"pending-user-confirmation","success_contract":{"acquisition_execution_authorized":false,"maximum_state":"ACQUISITION-ENVELOPE-FROZEN-PENDING-USER-CONFIRMATION","next_required_authority":"user must separately cite the exact final acquisition raw-envelope receipt digest and GOV01-SA challenge before verify or acquire; acquisition success still stops at static-attested-unexecuted","runtime_use_authorized":false,"stdout_fields":["state","artifact_path","raw_envelope_receipt_digest","generation_approval_challenge_id","approval_challenge_id","not_after_utc"]}}
./_bmad-output/审查/phase0a-annotation-truth/A01-source-boundary-draft.json:2:  "schema_version": "2.0-draft",
./_bmad-output/审查/phase0a-annotation-truth/A02-public-ledger-v2.schema.json:9:    "schema_version",
./_bmad-output/审查/phase0a-annotation-truth/A02-public-ledger-v2.schema.json:28:    "schema_version": {
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-first-receipt-envelope-v1.schema.json:8:    "schema_version",
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-first-receipt-envelope-v1.schema.json:26:    "schema_version": { "const": "gov-01-first-receipt-envelope-v1" },
./_bmad-output/_status/mvp-alpha-broadcast-session-b.yaml:57:      response: {question_id: str, question_text: str, generated_at?: iso}
./_bmad-output/_status/mvp-alpha-broadcast-session-b.yaml:90:      - generated_at
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-public-attestation-v2.schema.json:9:    "schema_version", "artifact_type", "ok", "mode", "phase", "state",
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-public-attestation-v2.schema.json:14:      "schema_version", "artifact_type", "ok", "mode", "phase", "state",
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-public-attestation-v2.schema.json:21:    "schema_version": { "const": "gov-01-toolchain-static-acquisition-public-result-v2" },
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-public-attestation-v2.schema.json:30:    "generated_at_utc": {
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-public-attestation-v2.schema.json:983:      "required": ["schema_version", "gate_id", "scope", "phase", "status", "checker_role", "assurance", "evidence", "receipt_sha256"],
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-public-attestation-v2.schema.json:985:        "schema_version": { "const": "gov01-static-acquisition-gate-evidence-v2" },
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-public-attestation-v2.schema.json:1044:    "actualG23": {"properties":{"gate_id":{"const":"G23"},"scope":{"const":"ledger-terminal"},"phase":{"const":"ledger-terminal"}},"allOf":[{"if":{"properties":{"status":{"const":"PASS"}},"required":["status"]},"then":{"properties":{"evidence":{"type":"object","additionalProperties":false,"required":["canonical_jsonl_and_hmac_chain_valid","checker_interface","ledger_head_hmac_sha256","private_projection_schema_version","record_count","terminal_kind"],"properties":{"canonical_jsonl_and_hmac_chain_valid":{"const":true},"checker_interface":{"const":"gov01-ledger-semantic-checker-v2"},"ledger_head_hmac_sha256":{"$ref":"#/$defs/sha256"},"private_projection_schema_version":{"const":"gov-01-toolchain-static-acquisition-private-evidence-v2"},"record_count":{"const":6},"terminal_kind":{"const":"success"}}}}}}]},
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-public-attestation-v2.schema.json:1143:      "required": ["schema_version", "approval_challenge_id", "receipt_digest", "schema_binding_observation", "public_repo_artifact_set_receipt_sha256", "git_snapshot_commitment", "private_preapproval_commitment", "private_control_identity_commitment", "toolchain", "source_and_receipts", "publication", "containment", "execution_counters", "next_required_authorization"],
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-public-attestation-v2.schema.json:1145:        "schema_version": { "const": "gov01-static-acquisition-success-attestation-v2" },
./docs/deep-research/01-subsystem-design-review/deep-research-b3-graphiti-history.md:29:*   **`schema_version`**: Versioning for backward compatibility.
./_bmad-archive/test-artifacts/traceability-matrix.md:422:  - `canvas-progress-tracker/obsidian-plugin/tests/services/GraphitiAssociationService.test.ts` — Sync status transitions, listener notifications (5 tests)
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-private-evidence-v2.schema.json:12:    "schema_version",
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-private-evidence-v2.schema.json:30:    "schema_version": {
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-private-evidence-v2.schema.json:82:    "generated_at_utc": {
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-private-evidence-v2.schema.json:999:        "schema_version",
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-private-evidence-v2.schema.json:1010:        "schema_version": { "const": "gov01-static-acquisition-ledger-event-v2" },
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-private-evidence-v2.schema.json:1576:        "schema_version",
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-private-evidence-v2.schema.json:1594:        "schema_version": { "const": "gov-01-toolchain-static-acquisition-private-evidence-v2" },
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-private-evidence-v2.schema.json:1635:      "required": ["schema_version", "sequence", "at_utc", "challenge", "receipt_digest", "event", "previous_hmac_sha256", "data", "hmac_sha256"],
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-private-evidence-v2.schema.json:1637:        "schema_version": { "const": "gov01-static-acquisition-ledger-event-v2" },
./_bmad-output/研究/2026-07-29-每日复习手机推送-MVP方案.md:57:- 输出②：stdout 单行 JSON `{top_boards:[{board,top_node,pending,idle_days}]}`
./_bmad-output/研究/2026-07-29-每日复习手机推送-MVP方案.md:61:- 顺序铁律：md 先落盘 → Bark（`curl -m 10 --retry 2 "$PUSH_URL/📚 今日复习 · <top1板名>/<正文>?group=canvas复习"`，push.env 缺失记「跳过(未配置)」不算错）→ 失败 `osascript -e 'display notification ...'` 兜底
./_bmad-archive/test-artifacts/tea-trace-coverage-matrix-epic32.json:4:  "generated_at": "2026-02-11",
./_bmad-archive/test-artifacts/tea-trace-coverage-matrix-epic31.json:3:  "generated_at": "2026-02-11T12:00:00Z",
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-envelope-generation-envelope-v1.schema.json:8:    "schema_version",
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-envelope-generation-envelope-v1.schema.json:34:    "schema_version": {
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-first-receipt-envelope-v1.json:2:  "schema_version": "gov-01-first-receipt-envelope-v1",
./docs/deep-research/01-subsystem-design-review/deep-research-b3-graphiti-history-zh.md:29:*   **`schema_version`**：用于向后兼容的版本号。
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-envelope-generation-envelope-v1.GOV01-GEN-20260821-cb0f360ded46f0d1a2fd5e807e260df6b6e238a6e3e485f25b8eed5b821e2438.json:1:{"approval_challenge_id":"GOV01-GEN-20260821-cb0f360ded46f0d1a2fd5e807e260df6b6e238a6e3e485f25b8eed5b821e2438","artifact_id":"GOV-01-STATIC-ENVELOPE-GENERATION-20260821-5b8eed5b821e2438","artifact_type":"gov-01-toolchain-static-envelope-generation-envelope","artifacts":[{"byte_length":77024,"file_kind":"regular","path":"_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md","raw_file_sha256":"4841abe51a29110be92f1d6810d02654a82e8e2be9c4f922c0541561246ca512","role":"goal"},{"byte_length":42685,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/2026-08-20-GOV-01-追踪真相源修复决策稿.md","raw_file_sha256":"836a18560bc50d2fdd5c6c86c1de8b310498c523fb0e777abf117863d18f3b2a","role":"governance-decision"},{"byte_length":39848,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/2026-08-20-Phase0A-A01-A02-批注真相层实施契约.md","raw_file_sha256":"da0acd5558ef9669c3f2b948464e5ceda72288895d0bb3a3b4571b5bbd94b540","role":"phase0a-contract"},{"byte_length":8954,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-first-receipt-envelope-v1.json","raw_file_sha256":"0b73b83e1dbd92dd0a4684a83438dafc7afae6a6fde42b4130d776d7ee246410","role":"first-receipt-envelope"},{"byte_length":17623,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-first-receipt-envelope-v1.schema.json","raw_file_sha256":"bb680b866b89fad649953e23da1a8ba9e3529523485516ebd969849bff468298","role":"first-receipt-schema"},{"byte_length":5110,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/2026-08-20-GOV-01-Bootstrap-0-safe-mode.patch","raw_file_sha256":"d2f9a1ff45006cf19bd5295b751e2b620dc6043d6ec1ff26494c1d2d722aa8aa","role":"bootstrap-patch"},{"byte_length":13463,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-control-prep-envelope-v1.json","raw_file_sha256":"ef424f80672568076d750ae0f6d662ebfdae242fdea8fcda2b37f39e6406945b","role":"control-prep-envelope"},{"byte_length":23437,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-control-prep-envelope-v1.schema.json","raw_file_sha256":"5c6c07ffe71a8c39a6993b2c717b751988b94338800972bbcfe93363a152f984","role":"control-prep-schema"},{"byte_length":291290,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-envelope-generation-v1.py","raw_file_sha256":"c6745b954a3647d52e40d05773af0961b116134363239ceaa0bd1f5e64772f6c","role":"static-envelope-generator"},{"byte_length":41393,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-envelope-generation-envelope-v1.schema.json","raw_file_sha256":"547633e952c77e1b850ca3c8874bc6704286169afa98f275475fac9b0130132a","role":"generation-envelope-schema"},{"byte_length":215500,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-envelope-generation-hostile-fixtures-v1.py","raw_file_sha256":"764b8f06dfec3b176a6ef61eeebb22a2a56cf15a1584dfc441a2b85343764dd7","role":"generation-hostile-fixture"},{"byte_length":703588,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py","raw_file_sha256":"ece03c04319a94006cb031c887b8aa54ef8f03d0f6b60999c29d720caf0ac4ee","role":"static-executor"},{"byte_length":50895,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-verifier-v2.py","raw_file_sha256":"98bcaaa35e2e4e7713e51e016af6c7223713acdb47a1b4b27859e70f75725064","role":"static-verifier"},{"byte_length":343512,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-static-acquisition-hostile-fixtures-v2.py","raw_file_sha256":"a93a7cbd58a4fbf0ebe9a2a3fe7501a440fc1f9a6dc1d22db8f54d38814fb4a1","role":"static-hostile-fixture"},{"byte_length":98605,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-envelope-v2.schema.json","raw_file_sha256":"b793700286408a1dcb9c37c314eca1c92284e33c8b093adc4d61086e2c5760bc","role":"pending-envelope-schema"},{"byte_length":98395,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-private-evidence-v2.schema.json","raw_file_sha256":"5c40d48e0338fe89277fd1e54c2702e620a10b946b0023baed05ee7d07acb231","role":"private-evidence-schema"},{"byte_length":195320,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-public-attestation-v2.schema.json","raw_file_sha256":"7cc4d80825b454c3de59838b8c292093c14156b30255fd1805c2c6f5be827563","role":"public-attestation-schema"},{"byte_length":817,"file_kind":"regular","path":"package.json","raw_file_sha256":"bd5c4e933e2dcbf7f2019bec9fec555b5b1adff1c4a6e5c36ea4415ff9a711fe","role":"package-manifest"},{"byte_length":83153,"file_kind":"regular","path":"package-lock.json","raw_file_sha256":"c6e190741427b99ff132d6504b2a782d75c418d6ae93066769ac422bff6b7cea","role":"package-lock"},{"byte_length":5413,"file_kind":"regular","path":".gitignore","raw_file_sha256":"679c83badb0067729c75a48f9391849542fc71a03c133d8d0dc33cfe7e836351","role":"gitignore"}],"authorized_reads":{"git_generation_output_exclusion":"exclude exactly the one derived regular-file generation output path from Git status and dirty-content commitment; never exclude its parent directory or a wildcard subtree; separately require output preimage ABSENT and later bind raw output bytes by the external acquisition receipt","npm_cache_index_read_count":0,"private_roles_after_approval":["exact 0600 32-byte hmac.key for domain-separated HMAC only","derived control root and claims metadata plus exact fresh acquisition challenge child absence","exact locator-free canonical control-preparation receipt content for predecessor-chain verification","Git marker commondir local config index refs contained hooks and dirty or untracked metadata and regular content, with Vault and .obsidian paths rejected before open","package-lock-selected direct-SRI npm cache content-v2 blobs only","target-worktree-associated Claude process census evidence"],"public_repo_artifact_policy":"only exact versioned artifact paths listed in this envelope plus package.json package-lock.json .gitignore and Git control evidence required by the frozen static executor","user_or_managed_settings_read_count":0,"vault_read_count":0},"authorized_subprocesses":{"environment_profile":"new exact sanitized environment; HOME=/var/empty and TMPDIR=DARWIN_USER_TEMP_DIR=/tmp; every Git child starts only after fchdir to the exact identity-bound adapter Git directory and uses relative --git-dir=.; bootstrap Git receives only exact captured GIT_OBJECT_DIRECTORY while global/system config, inherited alternates and protocols are disabled; final Git evidence unsets live object access and uses only the sealed adapter; fsmonitor, hooks, attributes, includes, alternates, grafts, network, and worktree reads are rejected or sandbox-denied","git_child_sandbox_profile":"every Git child calls /usr/lib/libsandbox.1.dylib sandbox_init exactly once before exec with a generated default-deny profile; before every Git exec the parent passes only one per-child duplicate of the pinned adapter-Git directory FD, and preexec performs fchdir of that exact identity, closes the duplicate, then calls sandbox_init exactly once; no usable directory FD reaches Git, fixed argv uses relative --git-dir=., and no path discovery is permitted; the git-metadata-adapter-bootstrap role permits only the content-bound CommandLineTools tree, one unsealed checkpoint-scoped private-temporary adapter, captured live pack or loose object containers needed to extract the exact approved OID set, and adapter-only writes needed by index-pack; it denies network, worktree payload, every live Git control path, alternates and graft bytes, and all other reads or writes; after source CAS and sealing, git-read-only-evidence permits only the CommandLineTools tree and sealed adapter and denies writes and all live Git or worktree reads; the parent revalidates captured live source before adapter removal; every child profile explicitly denies create rename unlink or write authority over the private-temporary parent namespace and sibling adapter roots, while index-pack writes are restricted to the pinned current adapter objects/pack directory; sandbox initialization failure is terminal; /usr/bin/sandbox-exec is never executed","network_allowed":false,"node_npm_npx_openspec_allowed":false,"roles":["xcode-select-resolver","xcrun-resolver","git-metadata-adapter-bootstrap","git-read-only-evidence","pgrep-read-only-evidence","lsof-read-only-evidence"],"shell_allowed":false},"challenge_and_time_contract":{"acquisition_entropy":"exactly one os.urandom(32) call after generation approval and before private census; lowercase 64-hex suffix; caller-supplied entropy forbidden","challenge_date_binding":"each challenge YYYYMMDD component equals its own canonical UTC issued or census date","clock_skew_ceiling_seconds":300,"expiry_checkpoints":["micro-envelope load","immediately before the persistent generation claim mkdir","after generation claim verification and immediately before the public output create","after output reopen before emitting pending-user-confirmation"],"generation_entropy":"exactly one os.urandom(32) call before the public generation micro-envelope is written; lowercase 64-hex suffix; caller-supplied entropy forbidden","namespace_separation":"generation challenge uses GOV01-GEN and acquisition challenge uses GOV01-SA; equality or cross-namespace reuse is impossible by grammar","ttl_ceiling_seconds":86400},"encoding_profile":"UTF-8-NFC-LF-no-BOM-no-duplicate-json-keys","failure_contract":{"existing_complete_output":"under the same still-valid exact GEN receipt, authenticate the retained generation claim, reuse only its fixed acquisition challenge and timestamps, revalidate every public and private commitment including hmac.key-derived commitments, require rebuilt raw bytes exact, then re-emit the same raw receipt digest without writing anything","existing_partial_or_invalid_output":"a partial or invalid generation claim is terminal consumed; a valid claim with absent output may recreate only its exact fixed raw output; any partial invalid or drifted existing output is retained and requires a new generation micro-envelope","post_create_failure":"after the generation claim mkdir, retain claim record and any output bytes and stop; never truncate delete overwrite repair or mint another acquisition challenge from this generation authority","pre_output_failure":"before the generation claim mkdir, no persistent repository control product claim or output write; the exact approved preflight may use only checkpoint-scoped private-temporary Git metadata adapters and may rerun before expiry only after exact cleanup with zero residue while every bound input is unchanged and both claim and output remain absent","retry_policy":"single-use begins at successful exclusive generation claim mkdir; only a pre-claim failure with confirmed temporary-adapter cleanup and zero residue may rerun within the exact receipt TTL; every post-claim path is pinned to the claim-authenticated acquisition challenge timestamps and final raw digest","temporary_adapter_failure":"adapter cleanup failure root-identity uncertainty or any residue is terminal fail-closed for this attempt: do not publish, do not report retryable, retain evidence for private inspection, and require new authority before another attempt"},"generation_claim_contract":{"generation_claim_profile":"exclusive-0700-generation-claim-directory-with-exclusive-0600-canonical-HMAC-record-v1","generation_claim_record_profile":"HMAC-SHA-256 with the authorized 32-byte private key over ASCII(CLS/GOV01/STATIC-ENVELOPE-GENERATION-CLAIM/v1) || NUL || uint64be(canonical-body-byte-length) || canonical JSON binding GEN receipt/raw, C1/C2 identities, one SA/time tuple and final raw SHA-256/bytes/domain receipt","generation_claim_required":true,"generation_claim_retention":"retain permanently; never delete, overwrite or repair; a complete valid claim permits only byte-exact recovery with its recorded SA and times"},"issued_at_utc":"2026-08-21T18:34:59Z","locator_derivation_contract":{"cache_root":"pwd.getpwuid(the control-preparation expected created uid).pw_dir plus exact suffix .npm; normalize once, require absolute realpath equality, owner uid equality, no symlink component and no Vault component","caller_supplied_locator_count":0,"claims_root":"exact direct child claims beneath the derived state root; validate retained GOV01-SA claim directories and generation-claim-GOV01-GEN directories, require this GEN claim preimage ABSENT before fresh entropy, and require the fresh acquisition challenge child preimage ABSENT","final_locator_commitment_timing":"resolve derived private locators and calculate domain-separated keyed commitments only after approval; serialize commitments but never raw private locators into the final acquisition envelope","generation_output":"repo root plus exact control-prefix regular-file name GOV-01-toolchain-static-acquisition-pending-<approved-GOV01-GEN-challenge>.json; the final envelope separately carries one fresh GOV01-SA acquisition challenge","key_file":"exact direct child hmac.key beneath the derived state root","repo_root":"derive from the no-symlink realpath of the content-addressed generator __file__ by removing its exact repo-relative suffix","state_root":"read the exact target.absolute_path from the content-addressed committed control-preparation envelope only after this generation receipt is approved"},"mutation_scope":{"allowed_ephemeral_mutations":["create one fresh unique checkpoint-scoped private-temporary 0700 Git metadata adapter for each production Git evidence checkpoint after the applicable public issue invocation or exact GEN receipt has authorized Git inspection; permit at most one active adapter owner within a process","write only its 0600 sanitized Git control metadata through pinned root and Git directory FDs; resolve bootstrap and import argv only from the identity-bound adapter Git cwd with relative --git-dir=., keep index-pack pack/index output beneath objects/pack, verify every exact-OID partial-pack object hash, then seal files 0400 beneath 0500 directories through pinned FDs; no adapter locator or raw metadata may enter public output","within the declared trust boundary and host assurance, remove the unique registered adapter at its authorized pathname only after captured root and Git identity checks, then require authorized-path absence and zero registry residue before success or retryable pre-claim failure"],"allowed_persistent_mutations":["create and fsync exactly one previously-absent 0700 generation claim directory beneath the existing receipt-bound claims container","create and fsync exactly one 0600 canonical HMAC-authenticated generation-record.json beneath that claim and fsync both claim and claims directories","create and fsync exactly one previously-absent public acquisition envelope regular file beneath the repository control prefix","fsync its already-existing parent directory"],"commit_allowed":false,"first_authority_consuming_persistent_write":"exclusive mkdirat of exact claims/generation-claim-<approved-GOV01-GEN-challenge> mode 0700 after every private read schema manual privacy and drift check has passed; EEXIST permanently forbids minting another acquisition challenge","git_metadata_adapter_cleanup_guarantee":"under the declared Git metadata adapter trust boundary and host assurance, cleanup success or retryable pre-claim failure requires pre-removal root and Git identity agreement, authorized-path removal, post-removal absence, and zero pathname and registry residue; any observed root or Git identity drift, missing authorized pathname, cleanup error, or residue is terminal and quiescence must fail; preservation against a non-cooperating same-UID replacement at the final pathname-deletion linearization point is outside the supported guarantee","git_metadata_adapter_host_assurance":"every spawned Git child is sandboxed and has no authority to create, rename, unlink or write the private-temporary parent namespace or any sibling adapter root; the product owns only the fresh exact adapter entry, root and descendants for that invocation, while /private/tmp and sibling entries remain ambient host namespace; every product invocation creates one fresh unique adapter root; the process-wide non-reentrant scope and registry forbid interleaved adapter ownership within one process and do not claim cross-process exclusion","git_metadata_adapter_trust_boundary":"the kernel and each owning same-UID production process are trusted; POSIX 0600 and 0700 modes isolate other UIDs but do not isolate an unsandboxed process with the same effective UID, so each adapter root has exactly one owning process and compliant same-UID product processes never mutate another invocation's root; non-cooperating same-UID filesystem mutation, out-of-process ptrace or code injection, and out-of-process access to the 0600 private HMAC key are outside the supported threat model","output_mode":"0644","overwrite_allowed":false,"product_state_cleanup_allowed":false,"push_allowed":false,"sidecar_allowed":false,"temporary_adapter_cleanup_required":true,"temporary_adapter_residue_allowed":false,"temporary_git_metadata_adapter_profile":"checkpoint-scoped-private-temp-sanitized-required-path-ancestor-exact-oid-index-root-proven-one-exact-public-opaque-gitlink-identity-bound-git-fd-metadata-adapter-v5"},"not_after_utc":"2026-08-22T18:34:59Z","plan_id":"PLAN-CLS-PRODUCTIVITY-2026-08-20","predecessor":{"bootstrap_commit_oid":"0e0f0150be184f4dad83a859b0fdd232ec53e8b5","bootstrap_patch_raw_sha256":"d2f9a1ff45006cf19bd5295b751e2b620dc6043d6ec1ff26494c1d2d722aa8aa","control_preparation_envelope_raw_sha256":"ef424f80672568076d750ae0f6d662ebfdae242fdea8fcda2b37f39e6406945b","control_preparation_receipt_domain_sha256":"dbb28c7627b63989e98b70ff608c20976d687541364af95804537dda7867541c","control_preparation_state":"independently-verified-control-prepared","first_approval_envelope_raw_sha256":"0b73b83e1dbd92dd0a4684a83438dafc7afae6a6fde42b4130d776d7ee246410","first_receipt_domain_sha256":"c89e7195e67b60a26117469e2b212fb508c0a5a64cac5d25a59a257f73b55740","static_contract_commit_oid":"d6c7c79d8b09688309626408b8f1317f3e5004aa","static_contract_tree_oid":"4b2b221be8951bd0804ea7a81dfeb3e24b6f1c90"},"privacy":{"git_metadata_adapter_trust_boundary":"the kernel and each owning same-UID production process are trusted; POSIX 0600 and 0700 modes isolate other UIDs but do not isolate an unsandboxed process with the same effective UID, so each adapter root has exactly one owning process and compliant same-UID product processes never mutate another invocation's root; non-cooperating same-UID filesystem mutation, out-of-process ptrace or code injection, and out-of-process access to the 0600 private HMAC key are outside the supported threat model","graphiti_call_count":0,"network_call_count":0,"private_key_publication_allowed":false,"raw_command_output_publication_allowed":false,"raw_private_locator_public_count":0,"vault_read_count":0,"whole_envelope_checker":"field-aware recursive checker before write and before stdout; repo paths use strict relative grammar; tool logical IDs and versions use role-specific ASCII grammar; only schema-enumerated fixed public system command locators and placeholders are allowed; all other absolute home file-URI Vault .obsidian control bidi and secret-bearing values are rejected"},"receipt_digest_profile":"SHA-256(ASCII(CLS/GOV01-STATIC-ENVELOPE-GENERATION-RECEIPT/v1) || NUL || raw-envelope-bytes); digest supplied by user and stored externally","repository_transition":{"approved_commit_shape":"current HEAD has exactly one parent equal to authorization_baseline_head; a path-local Merkle comparison of authenticated current and parent ancestor tree objects proves exactly the micro envelope regular file was added with bytes equal to the approved raw envelope and every non-target entry is byte-identical; no other path is added modified deleted renamed or type-changed","authorization_baseline_head":"d6c7c79d8b09688309626408b8f1317f3e5004aa","authorization_baseline_head_ref_bytes":47,"authorization_baseline_head_ref_profile":"SHA-256(ASCII(CLS/GOV01-STATIC-ENVELOPE-HEAD-REF/v1) || NUL || exact symbolic HEAD ref ASCII bytes); raw ref is never serialized","authorization_baseline_head_ref_sha256":"c58034b19de75ff292906142ab44cd41a8b688b48862a63dd8c01f42040459d2","authorization_baseline_head_symbolic":true,"authorization_baseline_other_refs_bytes":3648,"authorization_baseline_other_refs_sha256":"56d06c459e4cff8a2a871f24b2b335f1739edee6126eb5a8f9be4ecb84016b3d","authorization_baseline_tree":"4b2b221be8951bd0804ea7a81dfeb3e24b6f1c90","captured_index_root_profile":"strict captured DIRC v2 or v3 canonical bottom-up root-tree recomputation equal to authenticated HEAD; require the mode 160000 opaque-leaf path set to equal the exact public singleton _reference/obsidian-sample-plugin without opening requesting or dereferencing its object OID; reject a missing or mode-replaced singleton and every extra or substituted gitlink; in a parsed required-path ancestor tree permit that same singleton only as an unselected opaque sibling, and reject it if selected as a required terminal or ancestor","generation_output_preimage":"ABSENT","generation_output_repo_relative":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-pending-GOV01-GEN-20260821-cb0f360ded46f0d1a2fd5e807e260df6b6e238a6e3e485f25b8eed5b821e2438.json","git_control_profile":{"alternate_object_controls_absent":true,"common_directory_relation":"git-directory-contained-under-common-worktrees","include_controls_absent":true,"marker_kind":"gitfile"},"index_must_equal_head":true,"issue_publication_checkpoint_profile":"capture one initial exact Git-source index-root and public-artifact checkpoint; while holding a nonblocking advisory lock on the exact shared control-parent directory FD, recapture an equal checkpoint immediately before micro-envelope O_EXCL and require both micro and generation-output preimages absent; after fsync and same-FD byte-exact reopen, require generation-output absence, recapture the same equal checkpoint, and require generation-output absence again before success","micro_envelope_preimage":"ABSENT","micro_envelope_repo_relative":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-envelope-generation-envelope-v1.GOV01-GEN-20260821-cb0f360ded46f0d1a2fd5e807e260df6b6e238a6e3e485f25b8eed5b821e2438.json","refs_except_head_must_be_unchanged":true},"schema_binding":{"content_addressed_manual_checker_required":true,"external_draft202012_validation_required":true,"schema_artifact_path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-envelope-generation-envelope-v1.schema.json","schema_id":"urn:canvas-learning-system:gov-01:toolchain-static-envelope-generation-envelope:v1","schema_raw_file_sha256":"547633e952c77e1b850ca3c8874bc6704286169afa98f275475fac9b0130132a","whole_envelope_privacy_checker_required":true},"schema_version":"gov-01-toolchain-static-envelope-generation-envelope-v1","single_use":true,"state":"pending-user-confirmation","success_contract":{"acquisition_execution_authorized":false,"maximum_state":"ACQUISITION-ENVELOPE-FROZEN-PENDING-USER-CONFIRMATION","next_required_authority":"user must separately cite the exact final acquisition raw-envelope receipt digest and GOV01-SA challenge before verify or acquire; acquisition success still stops at static-attested-unexecuted","runtime_use_authorized":false,"stdout_fields":["state","artifact_path","raw_envelope_receipt_digest","generation_approval_challenge_id","approval_challenge_id","not_after_utc"]}}
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-static-acquisition-hostile-fixtures-v2.py:461:            "schema_version": "gov01-static-acquisition-ledger-event-v2",
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-static-acquisition-hostile-fixtures-v2.py:574:        "G23": {"checker_interface": "gov01-ledger-semantic-checker-v2", "record_count": 6, "terminal_kind": "success", "ledger_head_hmac_sha256": zero, "canonical_jsonl_and_hmac_chain_valid": True, "private_projection_schema_version": "gov-01-toolchain-static-acquisition-private-evidence-v2"},
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-static-acquisition-hostile-fixtures-v2.py:678:            "schema_version": "gov01-static-acquisition-gate-set-v2",
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-static-acquisition-hostile-fixtures-v2.py:872:        "schema_version": "gov01-static-acquisition-success-attestation-v2",
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-static-acquisition-hostile-fixtures-v2.py:6802:            "schema_version": "gov-01-toolchain-static-acquisition-envelope-v2",
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-static-acquisition-hostile-fixtures-v2.py:6822:            domain = acquisition["RECEIPT_DOMAINS"][value["schema_version"]]
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-static-acquisition-hostile-fixtures-v2.py:7072:            b'{"schema_version":"x","schema_version":"y"}\n', ledger_key, challenge, receipt
./_bmad-output/审查/phase0a-annotation-truth/A01-public-source-manifest-v2.schema.json:8:    "schema_version",
./_bmad-output/审查/phase0a-annotation-truth/A01-public-source-manifest-v2.schema.json:38:    "schema_version": { "const": "2.0-draft" },
./_bmad-archive/test-artifacts/tea-trace-coverage-matrix-epic30.json:3:  "generated_at": "2026-02-10T18:00:00Z",
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-control-prep-envelope-v1.json:2:  "schema_version": "gov-01-toolchain-control-prep-envelope-v1",
./docs/superpowers/plans/2026-04-07-fr-kg-04-a7-deep-research-manifest.md:566:5. **Sidecar `canUseTool` fail-closed** — IPC tool guardrails. Out of scope per design.md L34 (`fr-kg-04-sidecar-and-mcp-hardening` upcoming change).
./docs/superpowers/plans/2026-04-07-fr-kg-04-a7-deep-research-manifest.md:567:6. **MCP server token middleware** — auth on MCP-side endpoints. Same upcoming change as #5.
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-control-prep-envelope-v1.schema.json:8:    "schema_version",
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-control-prep-envelope-v1.schema.json:31:    "schema_version": { "const": "gov-01-toolchain-control-prep-envelope-v1" },
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-control-prep-v1.py:630:        "schema_version", "artifact_type", "artifact_id", "plan_id", "state",
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-control-prep-v1.py:638:        "schema_version": "gov-01-toolchain-control-prep-envelope-v1",
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-control-prep-v1.py:1121:            "schema_version": "gov-01-toolchain-control-prep-consumption-v1",
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-control-prep-v1.py:1230:            "schema_version": "gov-01-toolchain-control-prep-evidence-v1",
./docs/deep-research/06-prd-planning/deep-research-prd-granularity-solutions.md:130:*   **Polling Overhead:** Agents lacked push notifications and had to actively poll a shared `TaskList`, wasting tokens [cite: 15].
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py:632:    "schema_version artifact_type artifact_id plan_id state approval_challenge_id single_use census_at_utc "
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py:741:    "schema_version",
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py:765:_PENDING_ENVELOPE_V2_STATIC_TEMPLATE_JSON = r'''{"approval_receipt_contract":{"authority_expansion_allowed":false,"authority_is_exact":true,"challenge_must_match":true,"first_authority_consuming_persistent_write":"mkdirat exact state-root/claims/<approval_challenge_id> with mode 0700 is the first authority-consuming persistent write; EEXIST is terminal replay; earlier writes are limited to the exact nonpersistent /private/tmp Git adapter scratch, which must be identity-bound and fully removed before any return","receipt_before_first_authority_consuming_persistent_write":true,"receipt_must_match_raw_envelope_bytes":true,"required_user_reference":"exact domain-separated envelope SHA-256 plus exact approval_challenge_id"},"artifact_path_uniqueness_policy":"content-addressed checker MUST reject duplicate path even when role, byte_length or raw_file_sha256 differs; JSON Schema uniqueItems is not sufficient","authorization_preimage":{"absent_control_paths":[".npmrc","npm-shrinkwrap.json","pnpm-lock.yaml","yarn.lock","bun.lock","bun.lockb"],"absent_control_state":"all exact repo-root direct children ABSENT before and required ABSENT after","acquisition_control_root_state":"existing-real-directory-no-symlink-ancestor","envelope_git_status_exclusion_profile":"git-diff-files-ignore-submodules-all-plus-ls-files-others-with-exact-root-directory-command-exclusion-and-exact-opaque-gitlink-subtree-and-exact-top-literal-envelope-file-exclusion-v4; captured index root must equal HEAD and must contain exactly one opaque gitlink at _reference/obsidian-sample-plugin, which is excluded as an exact subtree from both dirty commands; ls-files carries exactly one root-anchored directory pattern in its command exclude channel before -z; the pending envelope exclusion has no parent, subtree, wildcard or glob authority","envelope_repo_relative_path":null,"forbidden_process_match_count":null,"git_object_format":null,"git_snapshot_commitment":null,"git_snapshot_commitment_profile":"HMAC-SHA-256 with 32-byte private key over ASCII(CLS/GOV01/GIT-SNAPSHOT/v2) || NUL || uint64be(canonical-body-byte-length) || UTF-8-NFC-LF sorted-key compact canonical JSON of the full private Git snapshot body excluding commitment; body includes git_control,head,tree,object_format,status_sha256,status_bytes,dirty_manifest_commitment,worktree_tree_exclusions,worktree_exact_file_exclusions,refs_sha256,refs_bytes,index,index_root_tree_oid,index_version,index_entry_count,index_gitlink_profile,index_gitlink_count,index_extension_profile,index_extension_count,index_extension_receipt_sha256,index_recomputation_profile,adapter_index_sanitization_profile,adapter_index_sha256,adapter_index_bytes,config,hooks,index_locator_commitment,config_locator_commitment,hooks_locator_commitment,hooks_config_state,git_binary_sha256,git_metadata_source_commitment,git_metadata_adapter_profile,git_metadata_adapter_cleanup_state,git_metadata_adapter_residue_count,live_git_control_child_read_count; git_metadata_source_commitment is a framed HMAC under ASCII(CLS/GOV01/GIT-METADATA-SOURCE/v1) over a path-free canonical body containing the live metadata capture fingerprint for HEAD,index,configs,refs,hooks,control absences, the object-root anchor and the captured exact pack/index search dependency receipt, plus the exact private adapter object-manifest receipt for captured HEAD, only the tree OIDs selected by the frozen required-path trie and exactly 20 approved artifact blob paths, including sealed batch-all exact-set, per-object OID recomputation and a sealed required-path-trie replay; the captured index is strictly framed and its bottom-up recomputed root tree OID must equal HEAD without diff-index; the captured index must contain exactly one mode-160000 opaque index/root-tree leaf at _reference/obsidian-sample-plugin, and its object or worktree descendants are never requested; every optional extension is captured in a path-free receipt but stripped from the adapter index before an object-format checksum is recomputed, so dirty-evidence children see only the strictly parsed entry region; adapter profile is checkpoint-scoped-private-temp-sanitized-required-path-ancestor-exact-oid-index-root-proven-one-exact-public-opaque-gitlink-identity-bound-git-fd-metadata-adapter-v5, cleanup_state is removed and residue count is zero; live_git_control_child_read_count is zero, meaning zero successful child file-data or byte reads of live Git-control files and excluding only an exact file-test-existence probe of the parent-prevalidated-absent live common-dir/objects/info/alternates path by live-object bootstrap children, which have no metadata or data-read authority for that path; worktree tree exclusions are exactly the opaque gitlink, challenge stage and node_modules while the exact-file exclusion contains exactly the challenge-suffixed pending envelope; dirty manifest is keyed content-and-metadata evidence for the union of nonexcluded diff-files --ignore-submodules=all and ls-files --others with the exact opaque-gitlink subtree excluded","head_commit_oid":null,"head_tree_oid":null,"node_modules_parent_or_sibling_reuse_allowed":false,"node_modules_state":"ABSENT","preexisting_dirty_policy":"private exact pre/post inventory required; no public paths or raw dirty/index/local-settings digest; zero mutation outside the exact new target","private_preapproval_commitment":null,"private_preapproval_commitment_profile":"HMAC-SHA-256 with the authorized 32-byte private key over ASCII(CLS/GOV01/PRIVATE-PREAPPROVAL/v2) || NUL || uint64be(canonical-body-byte-length) || UTF-8-NFC-LF canonical JSON of exactly {schema_version,approval_challenge_id,census_at_utc,hmac_key_id,authorized_locator_commitments,private_control_identity_commitment,public_repo_artifact_set_receipt_sha256,git_snapshot_commitment,toolchain_set_receipt_sha256,package_lock_raw_sha256,host_platform,host_architecture,target_worktree_claude_sessions,forbidden_process_match_count,host_selected_package_count,host_selected_cache_bytes,host_bin_link_count,content_receipt_sha256,ustar_closure_sha256,resolution_receipt_sha256,expected_tree_sha256}; no envelope digest, receipt digest, generated timestamp, raw private locator, inode/device or command bytes are in this deterministic body","private_preimage_capture":"census and post-approval checks may materialize only an identity-bound nonpersistent Git metadata adapter under /private/tmp; every child fchdir's through a dedicated duplicate of the held adapter Git-directory FD, closes that child-only FD, and reads the sealed frozen adapter with literal --git-dir=., explicit --work-tree and zero live Git-control byte reads; live-object bootstrap children may additionally perform only an exact file-test-existence probe of the parent-prevalidated-absent live common-dir/objects/info/alternates path, with metadata and data reads denied; source CAS runs after capture, before and after sealed evidence, and immediately before cleanup; exact cleanup and zero residue are required before returning; the persistent O_EXCL challenge claim remains the first authority-consuming persistent write","private_vault_census_allowed":false,"protected_existing_control_paths":["package.json","package-lock.json",".gitignore"],"protected_existing_control_state":"PRESENT regular files; raw SHA-256 bound in artifacts; byte-identical before and after","public_repo_artifact_set_receipt_sha256":null,"target_preimage":"ABSENT","target_worktree_claude_sessions":null,"worktree_state":null},"execution_plan":{"allowed_subprocess_executable_roles":["xcode-select-resolver","xcrun-resolver","git-metadata-adapter-bootstrap","git-read-only-evidence","pgrep-read-only-evidence","lsof-read-only-evidence"],"archive_or_payload_execution_allowed":false,"attempt_policy":"single-use; any failure consumes challenge; retry requires a new envelope and challenge","compression_policy":"exactly one RFC1952 gzip stream through frozen Python stdlib zlib; MAX_TAR_STREAM prebound; eof required; unused_data and unconsumed_tail empty; concatenated/trailing stream rejected","duplicate_collision_policy":"reject duplicate normalized path, file-directory conflict, Unicode NFC collision and case-fold collision before first target write","environment_mode":"executor requires Python -I -S -B and self-attests those runtime flags; every authorized evidence subprocess receives a newly constructed exact environment and never inherits caller environment; assurance ceiling is runtime-self-attested-not-pre-exec","environment_name_allowlist":["PATH","HOME","LC_ALL","LANG","GIT_OPTIONAL_LOCKS","GIT_CONFIG_GLOBAL","GIT_CONFIG_NOSYSTEM","GIT_CONFIG_SYSTEM","GIT_TERMINAL_PROMPT","GIT_NO_REPLACE_OBJECTS","GIT_PROTOCOL_FROM_USER","GIT_ALLOW_PROTOCOL","GIT_ATTR_NOSYSTEM","GIT_DISCOVERY_ACROSS_FILESYSTEM","GIT_OBJECT_DIRECTORY"],"evidence_command_templates":[{"argv_allowlist":[["{RESOLVED_CLT_GIT_PRIVATE}","--no-optional-locks","-c","core.fsmonitor=false","-c","core.untrackedCache=false","-c","core.hooksPath=/dev/null","-c","core.bare=false","-c","core.excludesFile=/dev/null","-c","core.attributesFile=/dev/null","-c","submodule.recurse=false","-c","protocol.allow=never","-c","core.commitGraph=false","-c","core.multiPackIndex=false","-c","pack.useBitmap=false","-c","pack.writeReverseIndex=false","--git-dir=.","--work-tree={REPO_ROOT_PRIVATE}","--no-pager","cat-file","--batch"],["{RESOLVED_CLT_GIT_PRIVATE}","--no-optional-locks","-c","core.fsmonitor=false","-c","core.untrackedCache=false","-c","core.hooksPath=/dev/null","-c","core.bare=false","-c","core.excludesFile=/dev/null","-c","core.attributesFile=/dev/null","-c","submodule.recurse=false","-c","protocol.allow=never","-c","core.commitGraph=false","-c","core.multiPackIndex=false","-c","pack.useBitmap=false","-c","pack.writeReverseIndex=false","--git-dir=.","--work-tree={REPO_ROOT_PRIVATE}","--no-pager","pack-objects","--stdout","--no-reuse-delta","--no-reuse-object"],["{RESOLVED_CLT_GIT_PRIVATE}","--no-optional-locks","-c","core.fsmonitor=false","-c","core.untrackedCache=false","-c","core.hooksPath=/dev/null","-c","core.bare=false","-c","core.excludesFile=/dev/null","-c","core.attributesFile=/dev/null","-c","submodule.recurse=false","-c","protocol.allow=never","-c","core.commitGraph=false","-c","core.multiPackIndex=false","-c","pack.useBitmap=false","-c","pack.writeReverseIndex=false","--git-dir=.","--work-tree={REPO_ROOT_PRIVATE}","--no-pager","index-pack","--stdin","--index-version=2"],["{RESOLVED_CLT_GIT_PRIVATE}","--no-optional-locks","-c","core.fsmonitor=false","-c","core.untrackedCache=false","-c","core.hooksPath=/dev/null","-c","core.bare=false","-c","core.excludesFile=/dev/null","-c","core.attributesFile=/dev/null","-c","submodule.recurse=false","-c","protocol.allow=never","-c","core.commitGraph=false","-c","core.multiPackIndex=false","-c","pack.useBitmap=false","-c","pack.writeReverseIndex=false","--git-dir=.","--work-tree={REPO_ROOT_PRIVATE}","--no-pager","verify-pack","-v","{GIT_METADATA_ADAPTER_PACK_INDEX_RELATIVE_PRIVATE}"]],"environment_name_allowlist":["PATH","HOME","LC_ALL","LANG","GIT_OPTIONAL_LOCKS","GIT_CONFIG_GLOBAL","GIT_CONFIG_NOSYSTEM","GIT_CONFIG_SYSTEM","GIT_TERMINAL_PROMPT","GIT_NO_REPLACE_OBJECTS","GIT_PROTOCOL_FROM_USER","GIT_ALLOW_PROTOCOL","GIT_ATTR_NOSYSTEM","GIT_DISCOVERY_ACROSS_FILESYSTEM","GIT_OBJECT_DIRECTORY"],"executable":"{RESOLVED_CLT_GIT_PRIVATE}","read_only":false,"role":"git-metadata-adapter-bootstrap","shell":false,"write_scope":"checkpoint-scoped-private-temp-adapter-only"},{"argv_allowlist":[["{RESOLVED_CLT_GIT_PRIVATE}","--no-optional-locks","-c","core.fsmonitor=false","-c","core.untrackedCache=false","-c","core.hooksPath=/dev/null","-c","core.bare=false","-c","core.excludesFile=/dev/null","-c","core.attributesFile=/dev/null","-c","submodule.recurse=false","-c","protocol.allow=never","-c","core.commitGraph=false","-c","core.multiPackIndex=false","-c","pack.useBitmap=false","-c","pack.writeReverseIndex=false","--git-dir=.","--work-tree={REPO_ROOT_PRIVATE}","--no-pager","rev-parse","--verify","HEAD"],["{RESOLVED_CLT_GIT_PRIVATE}","--no-optional-locks","-c","core.fsmonitor=false","-c","core.untrackedCache=false","-c","core.hooksPath=/dev/null","-c","core.bare=false","-c","core.excludesFile=/dev/null","-c","core.attributesFile=/dev/null","-c","submodule.recurse=false","-c","protocol.allow=never","-c","core.commitGraph=false","-c","core.multiPackIndex=false","-c","pack.useBitmap=false","-c","pack.writeReverseIndex=false","--git-dir=.","--work-tree={REPO_ROOT_PRIVATE}","--no-pager","rev-parse","--verify","HEAD^{tree}"],["{RESOLVED_CLT_GIT_PRIVATE}","--no-optional-locks","-c","core.fsmonitor=false","-c","core.untrackedCache=false","-c","core.hooksPath=/dev/null","-c","core.bare=false","-c","core.excludesFile=/dev/null","-c","core.attributesFile=/dev/null","-c","submodule.recurse=false","-c","protocol.allow=never","-c","core.commitGraph=false","-c","core.multiPackIndex=false","-c","pack.useBitmap=false","-c","pack.writeReverseIndex=false","--git-dir=.","--work-tree={REPO_ROOT_PRIVATE}","--no-pager","rev-parse","--show-object-format"],["{RESOLVED_CLT_GIT_PRIVATE}","--no-optional-locks","-c","core.fsmonitor=false","-c","core.untrackedCache=false","-c","core.hooksPath=/dev/null","-c","core.bare=false","-c","core.excludesFile=/dev/null","-c","core.attributesFile=/dev/null","-c","submodule.recurse=false","-c","protocol.allow=never","-c","core.commitGraph=false","-c","core.multiPackIndex=false","-c","pack.useBitmap=false","-c","pack.writeReverseIndex=false","--git-dir=.","--work-tree={REPO_ROOT_PRIVATE}","--no-pager","cat-file","--batch"],["{RESOLVED_CLT_GIT_PRIVATE}","--no-optional-locks","-c","core.fsmonitor=false","-c","core.untrackedCache=false","-c","core.hooksPath=/dev/null","-c","core.bare=false","-c","core.excludesFile=/dev/null","-c","core.attributesFile=/dev/null","-c","submodule.recurse=false","-c","protocol.allow=never","-c","core.commitGraph=false","-c","core.multiPackIndex=false","-c","pack.useBitmap=false","-c","pack.writeReverseIndex=false","--git-dir=.","--work-tree={REPO_ROOT_PRIVATE}","--no-pager","cat-file","--batch-all-objects","--batch-check=%(objectname) %(objecttype) %(objectsize)"],["{RESOLVED_CLT_GIT_PRIVATE}","--no-optional-locks","-c","core.fsmonitor=false","-c","core.untrackedCache=false","-c","core.hooksPath=/dev/null","-c","core.bare=false","-c","core.excludesFile=/dev/null","-c","core.attributesFile=/dev/null","-c","submodule.recurse=false","-c","protocol.allow=never","-c","core.commitGraph=false","-c","core.multiPackIndex=false","-c","pack.useBitmap=false","-c","pack.writeReverseIndex=false","--git-dir=.","--work-tree={REPO_ROOT_PRIVATE}","--no-pager","diff-files","--ignore-submodules=all","--name-only","-z","--",".",":(exclude).git",":(exclude).git/**",":(exclude)canvas-vault",":(exclude)canvas-vault/**",":(exclude)_reference/obsidian-sample-plugin",":(exclude)_reference/obsidian-sample-plugin/**",":(exclude){STAGE_REPO_RELATIVE}",":(exclude){STAGE_REPO_RELATIVE}/**",":(exclude)node_modules",":(exclude)node_modules/**",":(top,literal,exclude){ENVELOPE_REPO_RELATIVE}"],["{RESOLVED_CLT_GIT_PRIVATE}","--no-optional-locks","-c","core.fsmonitor=false","-c","core.untrackedCache=false","-c","core.hooksPath=/dev/null","-c","core.bare=false","-c","core.excludesFile=/dev/null","-c","core.attributesFile=/dev/null","-c","submodule.recurse=false","-c","protocol.allow=never","-c","core.commitGraph=false","-c","core.multiPackIndex=false","-c","pack.useBitmap=false","-c","pack.writeReverseIndex=false","--git-dir=.","--work-tree={REPO_ROOT_PRIVATE}","--no-pager","ls-files","--others","--exclude-standard","--exclude=/canvas-vault/","-z","--",".",":(exclude).git",":(exclude).git/**",":(exclude)canvas-vault",":(exclude)canvas-vault/**",":(exclude)_reference/obsidian-sample-plugin",":(exclude)_reference/obsidian-sample-plugin/**",":(exclude){STAGE_REPO_RELATIVE}",":(exclude){STAGE_REPO_RELATIVE}/**",":(exclude)node_modules",":(exclude)node_modules/**",":(top,literal,exclude){ENVELOPE_REPO_RELATIVE}"],["{RESOLVED_CLT_GIT_PRIVATE}","--no-optional-locks","-c","core.fsmonitor=false","-c","core.untrackedCache=false","-c","core.hooksPath=/dev/null","-c","core.bare=false","-c","core.excludesFile=/dev/null","-c","core.attributesFile=/dev/null","-c","submodule.recurse=false","-c","protocol.allow=never","-c","core.commitGraph=false","-c","core.multiPackIndex=false","-c","pack.useBitmap=false","-c","pack.writeReverseIndex=false","--git-dir=.","--work-tree={REPO_ROOT_PRIVATE}","--no-pager","for-each-ref","--sort=refname","--format=%(objectname) %(refname)","refs"],["{RESOLVED_CLT_GIT_PRIVATE}","--no-optional-locks","-c","core.fsmonitor=false","-c","core.untrackedCache=false","-c","core.hooksPath=/dev/null","-c","core.bare=false","-c","core.excludesFile=/dev/null","-c","core.attributesFile=/dev/null","-c","submodule.recurse=false","-c","protocol.allow=never","-c","core.commitGraph=false","-c","core.multiPackIndex=false","-c","pack.useBitmap=false","-c","pack.writeReverseIndex=false","--git-dir=.","--work-tree={REPO_ROOT_PRIVATE}","--no-pager","ls-tree","-z","--full-tree","{GENERATION_AUTHORIZATION_COMMIT_OID_PUBLIC}","--","{PUBLIC_ARTIFACT_REPO_RELATIVE}"],["{RESOLVED_CLT_GIT_PRIVATE}","--no-optional-locks","-c","core.fsmonitor=false","-c","core.untrackedCache=false","-c","core.hooksPath=/dev/null","-c","core.bare=false","-c","core.excludesFile=/dev/null","-c","core.attributesFile=/dev/null","-c","submodule.recurse=false","-c","protocol.allow=never","-c","core.commitGraph=false","-c","core.multiPackIndex=false","-c","pack.useBitmap=false","-c","pack.writeReverseIndex=false","--git-dir=.","--work-tree={REPO_ROOT_PRIVATE}","--no-pager","show","{GENERATION_AUTHORIZATION_COMMIT_OID_PUBLIC}:{PUBLIC_ARTIFACT_REPO_RELATIVE}"]],"environment_name_allowlist":["PATH","HOME","LC_ALL","LANG","GIT_OPTIONAL_LOCKS","GIT_CONFIG_GLOBAL","GIT_CONFIG_NOSYSTEM","GIT_CONFIG_SYSTEM","GIT_TERMINAL_PROMPT","GIT_NO_REPLACE_OBJECTS","GIT_PROTOCOL_FROM_USER","GIT_ALLOW_PROTOCOL","GIT_ATTR_NOSYSTEM","GIT_DISCOVERY_ACROSS_FILESYSTEM"],"executable":"{RESOLVED_CLT_GIT_PRIVATE}","read_only":true,"role":"git-read-only-evidence","shell":false},{"argv_allowlist":[["/usr/bin/xcode-select","-p"]],"environment_name_allowlist":["PATH","HOME","LC_ALL","LANG","GIT_OPTIONAL_LOCKS","GIT_CONFIG_GLOBAL","GIT_CONFIG_NOSYSTEM","GIT_CONFIG_SYSTEM","GIT_TERMINAL_PROMPT","GIT_NO_REPLACE_OBJECTS","GIT_PROTOCOL_FROM_USER","GIT_ALLOW_PROTOCOL","GIT_ATTR_NOSYSTEM","GIT_DISCOVERY_ACROSS_FILESYSTEM"],"executable":"/usr/bin/xcode-select","read_only":true,"role":"xcode-select-resolver","shell":false},{"argv_allowlist":[["/usr/bin/xcrun","--find","git"]],"environment_name_allowlist":["PATH","HOME","LC_ALL","LANG","GIT_OPTIONAL_LOCKS","GIT_CONFIG_GLOBAL","GIT_CONFIG_NOSYSTEM","GIT_CONFIG_SYSTEM","GIT_TERMINAL_PROMPT","GIT_NO_REPLACE_OBJECTS","GIT_PROTOCOL_FROM_USER","GIT_ALLOW_PROTOCOL","GIT_ATTR_NOSYSTEM","GIT_DISCOVERY_ACROSS_FILESYSTEM"],"executable":"/usr/bin/xcrun","read_only":true,"role":"xcrun-resolver","shell":false},{"argv_allowlist":[["/usr/bin/pgrep","-if","(^|[/ ])claude([ ]|$)|@anthropic-ai/claude-code"]],"environment_name_allowlist":["PATH","LC_ALL","LANG"],"executable":"/usr/bin/pgrep","read_only":true,"role":"pgrep-read-only-evidence","shell":false},{"argv_allowlist":[["/usr/sbin/lsof","-nP","-a","-p","{CLAUDE_CANDIDATE_PID_DECIMAL}","-d","cwd","-Fpn"]],"environment_name_allowlist":["PATH","LC_ALL","LANG"],"executable":"/usr/sbin/lsof","read_only":true,"role":"lsof-read-only-evidence","shell":false}],"evidence_command_templates_sha256":null,"executor_argv_template":["{BOUND_PYTHON_PRIVATE}","-I","-S","-B","{REPO_ROOT_PRIVATE}/_bmad-output/\u5ba1\u67e5/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py","acquire","--repo-root","{REPO_ROOT_PRIVATE}","--cache-root","{CACHE_ROOT_PRIVATE}","--state-root","{STATE_ROOT_PRIVATE}","--key-file","{HMAC_KEY_FILE_PRIVATE}","--envelope","{ENVELOPE_PRIVATE}","--receipt-digest","{APPROVED_RECEIPT_DIGEST_PUBLIC}","--approval-challenge","{APPROVAL_CHALLENGE_ID_PUBLIC}"],"executor_argv_template_sha256":null,"executor_interface_state":"frozen-content-addressed-before-user-receipt","executor_interface_version":"gov01-static-acquisition-executor-draft-v2","expiry_checkpoints":["on-envelope-load","immediately-before-persistent-ledger-claim","immediately-before-renameatx_np-RENAME_EXCL"],"forbidden_executable_names":["npm","npx","node","nodejs","openspec","sandbox-exec","tar","bsdtar","gtar"],"git_child_sandbox_profile":"every Git child receives a dedicated duplicate of the identity-bound adapter Git-directory FD, fchdir's to that inode, closes the child-only FD, then calls /usr/lib/libsandbox.1.dylib sandbox_init exactly once before exec with a generated default-deny profile; permits only the content-bound CommandLineTools tree, one initially-0700 then sealed-0500 /private/tmp metadata adapter, required path ancestors, and the exact repository worktree only for commands that must enumerate it; every child uses literal --git-dir=. plus an explicit absolute --work-tree and never -C or repository discovery; live config, refs, index, HEAD and object stores are denied; the exact opaque public gitlink worktree subtree _reference/obsidian-sample-plugin is denied to every child; an explicit file-write* deny prevents creation, rename, unlink or mutation of /private/tmp, the adapter root entry and every sibling adapter entry; network, writes, Vault/.obsidian paths, config includes, alternates, grafts and all other reads are denied; sandbox initialization failure is terminal; /usr/bin/sandbox-exec is never executed","git_metadata_adapter_bootstrap_sandbox_profile":"each git-metadata-adapter-bootstrap child receives a dedicated duplicate of the identity-bound adapter Git directory FD, fchdir's to that inode, closes the child-only FD, then calls /usr/lib/libsandbox.1.dylib sandbox_init exactly once before exec with a generated default-deny profile; argv always has literal --git-dir=. and an explicit absolute repo --work-tree with no -C or discovery; only cat-file --batch for captured HEAD and required-path-trie tree OIDs plus exact-OID pack-objects --stdout receive GIT_OBJECT_DIRECTORY with only exact loose-object paths or per-request pack/index pairs selected by independently verified frozen v2 pack-index search receipts under the live common-dir/objects root; the parent verifies the streamed pack checksum, then index-pack --stdin materializes only that bounded stream into the adapter with the live bridge unset, and verify-pack also runs with that bridge unset; in live-object bootstrap children, the exact live common-dir/objects/info/alternates path is parent-prevalidated ABSENT and receives file-test-existence only, never file-read-metadata or file-read-data authority, so an absent-path Apple Git probe succeeds while any regular, hardlinked or symlinked control that appears fails closed at its denied read; live HEAD,index,configs,refs,hooks,logs,grafts,unselected loose objects and every other common objects/info path including http-alternates are denied; when the live worktree Git directory differs from the common directory, its objects/info subtree is denied wholesale and never receives the common-store existence exception; pack-objects has no child filesystem write authority and only index-pack may write, only beneath the exact identity-bound private adapter objects/pack subtree; explicit write denies protect the /private/tmp parent, adapter root/Git/object directory entries, every sibling adapter and every path outside that exact objects/pack subtree; worktree payload, Vault/.obsidian, other reads/writes, network and subprocess executables other than the content-bound Git binary are denied; direct full-source CAS brackets bootstrap and the bridge is absent from every sealed-adapter evidence child","git_metadata_adapter_host_assurance":"every spawned Git child is sandboxed and has no authority to create, rename, unlink or write the private-temporary parent namespace or any sibling adapter root; the product owns only the fresh exact adapter entry, root and descendants for that invocation, while /private/tmp and sibling entries remain ambient host namespace; every product invocation creates one fresh unique adapter root; the process-wide non-reentrant scope and registry forbid interleaved adapter ownership within one process and do not claim cross-process exclusion","git_metadata_adapter_trust_boundary":"the kernel and each owning same-UID production process are trusted; POSIX 0600 and 0700 modes isolate other UIDs but do not isolate an unsandboxed process with the same effective UID, so each adapter root has exactly one owning process and compliant same-UID product processes never mutate another invocation's root; non-cooperating same-UID filesystem mutation, out-of-process ptrace or code injection, and out-of-process access to the 0600 private HMAC key are outside the supported threat model","launcher_executable_role":"python-interpreter","member_type_policy":"archive accepts regular files and directories only; rejects archive symlink, hardlink, fifo, socket, block/character device and unknown types","network_allowed":false,"phase_order":["read-only-verify-user-receipt-envelope-digest-challenge-and-expiry","read-only-hash-bound-schema-compare-schema-binding-and-run-manual-critical-envelope-checks-before-verifier-compilation","read-only-compare-repo-cache-state-key-envelope-locator-commitments","read-only-hash-every-public-artifact-and-load-only-the-bound-verifier-source","directly capture live Git metadata, freeze and seal an exact private-temp adapter, run explicit-adapter sealed Git evidence children with zero live-control byte reads, permit only the exact existence-only probe of parent-prevalidated-absent live common-dir/objects/info/alternates in live-object bootstrap children, revalidate the live source and remove the exact adapter with zero residue before comparing Git-snapshot and private-preapproval commitments","verify-no-active-Claude-session-whose-cwd-is-the-target-worktree; no broader ambient-process absence claim","read-only-direct-SRI-cache-census-build-expected-tree-and-freeze-all-compressed-and-payload-bytes-in-memory","recheck-approval-expiry-immediately-before-persistent-claim","create-persistent-0700-challenge-claim-directory-with-exclusive-mkdirat-and-record-first-authority-consuming-persistent-write","append-frozen-preflight-event-to-persistent-ledger","create-0700-same-parent-same-filesystem-exclusive-stage-with-incomplete-marker","stream-decompress-and-custom-parse-only-approved-USTAR-members","materialize-only-expected-resolution-destinations-without-running-payload","fsync-stage-and-verify-closure-resolution-and-stage-tree-receipts","run-full-pre-promotion-CAS-for-private-inputs-public-artifacts-toolchain-Git-dirty-content-process-census-lock-cache-control-files-stage-identity-and-target-absence","remove-only-the-incomplete-marker-seal-root-0755-and-run-two-stable-fingerprints; failure-after-this-point-retains-a-hidden-unmarked-stage","recheck-approval-expiry-and-target-absence-immediately-before-publication","publish-exact-stage-to-absent-target-with-renameatx_np-RENAME_EXCL","fsync-target-parent-and-recompute-final-tree-and-private-postimage","append-terminal-private-ledger-event-and-emit-locator-free-stdout-projection-only-if-every-success-condition-holds","stop-with-payload-unexecuted"],"runner":"caller invokes exact executor with a CPython 3.9-compatible interpreter and -I -S -B; executor self-attests isolation flags, interpreter, stdlib, executor, verifier, schema and five evidence binaries only after Python startup; no pre-exec launcher or pre-exec hash assurance exists; no shell","shell_allowed":false,"stop_after_static_attestation":true,"subprocess_from_executor_allowed":true,"ustar_parser":"custom Python stdlib fixed-512-byte POSIX.1-1988 USTAR parser; tarfile.extract/extractall forbidden","ustar_safety_policy":"strict magic/version/checksum/octal/padding/two-zero-block terminator; reject PAX, GNU, sparse, base-256 numeric, trailing payload, absolute/dot/dotdot/backslash/NUL/control path, symlink ancestor and path escape","verifier_census_argv_template":["{BOUND_PYTHON_PRIVATE}","-I","-S","-B","{BOUND_VERIFIER_PRIVATE}","census","--cache-root","{CACHE_ROOT_PRIVATE}"],"verifier_installed_argv_template":["{BOUND_PYTHON_PRIVATE}","-I","-S","-B","{BOUND_VERIFIER_PRIVATE}","verify-installed","--cache-root","{CACHE_ROOT_PRIVATE}","--expected-tree-sha256","{EXPECTED_TREE_SHA256_PUBLIC}"],"verifier_profile_version":"gov-01-toolchain-static-verifier-v2"},"failure_contract":{"challenge_state":"before the first authority-consuming persistent write no persistent consumption record exists but this envelope/challenge must be treated as rejected and replaced; after exclusive claim mkdir the persistent state is consumed-rejected","evidence_action":"pre-claim failures may create only the authorized Git adapter scratch; under the declared trust boundary and host assurance, return and conditional retry require pre-removal root/Git identity agreement, removal of only the authorized adapter paths, post-removal absence and zero pathname/registry residue; any observed identity drift, missing pathname, cleanup error or residue is terminal fail-closed, forbids success and automatic retry, and requires new explicit approval after private-state inspection; no claim, ledger, stage, target or other persistent write occurs before the challenge claim; after a persistent claim exists, append/fsync and semantically verify a terminal failure event only while the retained ledger writer is healthy and nonterminal; never repair or delete retained persistent state","existing_target_action":"never modify or delete; if a target was newly published before a later failure, retain as unauthorized and require user decision","failed_stage_action":"retain in place with no automatic cleanup, deletion, quarantine move or glob: before marker removal it remains a hidden 0700 stage carrying the 0600 incomplete marker; after marker removal/seal but before rename it remains a hidden 0755 stage without the marker; after successful rename followed by later failure the published target is retained as unauthorized pending user decision","failure_action":"STOP immediately at first failed gate","git_metadata_adapter_cleanup_guarantee":"under the declared Git metadata adapter trust boundary and host assurance, cleanup success or retryable pre-claim failure requires pre-removal root and Git identity agreement, authorized-path removal, post-removal absence, and zero pathname and registry residue; any observed root or Git identity drift, missing authorized pathname, cleanup error, or residue is terminal and quiescence must fail; preservation against a non-cooperating same-UID replacement at the final pathname-deletion linearization point is outside the supported guarantee","new_authority_required":"new complete envelope, new raw envelope digest and new challenge","postclaim_retry_allowed":false,"preclaim_retry_allowed":true,"public_success_attestation_allowed":false},"lock_closure":{"archive_member_types":["regular-file","directory"],"content_receipt_profile":"SHA-256(ASCII(CLS/GOV01-OFFLINE-CACHE/v1) || NUL || UTF-8 body); body is lexicographically sorted LF-terminated rows of exactly 6 TAB-separated columns: lock_key, version, resolved, integrity, compressed_bytes, actual_integrity","content_receipt_sha256":null,"direct_sri_policy":"no npm cache index read; sha512 SRI bytes map directly to _cacache/content-v2/sha512/<first-2>/<next-2>/<remainder>; missing or mismatched blob is terminal failure","expected_archive_member_count":null,"expected_resolved_tree_entry_count":null,"expected_tree_receipt_profile":"SHA-256(ASCII(CLS/GOV01/DETERMINISTIC-NODE-MODULES/v2) || NUL || UTF-8 body); body is LF-terminated rows sorted by UTF-8 path bytes with exactly 5 TAB-separated columns: kind,path,mode,size,file_sha256_or_link_text","expected_tree_sha256":null,"generated_symlink_policy":"only exact relative symlink text bound by the resolution receipt; resolved target remains beneath final tree","host_bin_link_count":null,"host_selected_cache_bytes":null,"host_selected_package_count":null,"network_fetch_allowed":false,"resolution_receipt_profile":"SHA-256(ASCII(CLS/GOV01/NODE-RESOLUTION-CLOSURE/v2) || NUL || UTF-8 body); body is lexicographically sorted LF-terminated rows of exactly 7 TAB-separated columns: source,edge_type,dependency_name,spec,target,target_version,state; this is deterministic package-lock path-closure evidence only and is not a general semver solver or semantic-version satisfiability proof","resolution_receipt_sha256":null,"resource_limits":{"compressed_closure_bytes_max":14000000,"final_path_utf8_bytes_max":128,"member_count_per_archive_max":5000,"payload_closure_bytes_max":64000000,"required_bin_link_count":12,"required_raw_regular_count":4099,"selected_archive_count":167,"single_file_bytes_max":15000000,"tar_stream_bytes_per_archive_max":24000000},"source_kind":"preapproved-local-content-addressed-ustar-set","source_locator_policy":"private absolute locators omitted; after challenge claim, derive each content-v2 locator directly from the package-lock sha512 SRI and require actual_integrity equality","ustar_closure_receipt_profile":"SHA-256(ASCII(CLS/GOV01/USTAR-CLOSURE/v2) || NUL || UTF-8 body); body is lexicographically sorted LF-terminated rows of exactly 13 TAB-separated columns: lock_key,version,integrity,compressed_bytes,tar_bytes,member_count,raw_regular_count,raw_directory_count,payload_bytes,strip_root,package_name,package_version,member_manifest_sha256; each member_manifest_sha256 uses CLS/GOV01/USTAR-PACKAGE-MEMBERS/v2 NUL plus sorted 8-column member rows","ustar_closure_sha256":null},"mutation_scope":{"allowed_ephemeral_mutations":["before each Git child sequence create one unpredictable exact 0700 /private/tmp/gov01-git-adapter-* scratch root, freeze sanitized config plus captured HEAD,refs,info-exclude and shallow, strictly parse the captured index, require exactly one opaque mode-160000 root-tree leaf at _reference/obsidian-sample-plugin, and materialize only its extension-free rechecksummed entry region, then use a sandboxed object-only live bridge to stream a pack containing exactly captured HEAD, only required-path-trie tree OIDs and only approved artifact blob OIDs; those live-object bootstrap children may additionally perform only an exact file-test-existence probe of the parent-prevalidated-absent live common-dir/objects/info/alternates path, with metadata and data reads denied; independently verify the stream checksum, import it through bridge-free index-pack, verify the exact pack object set, seal the self-contained adapter 0500/0400, then remove that exact dev/inode-bound root before returning; this nonpersistent scratch neither consumes the challenge nor authorizes any repo/state/cache mutation","create one exact 0700 same-parent same-filesystem stage with an exact 0600 incomplete marker; this stage is publication-working-state but is retained rather than ephemeral on any failure","write only the frozen expected directories, regular-file payload bytes and generated relative bin symlinks beneath that stage","remove only the exact incomplete marker and chmod the stage root 0755 immediately before two stable fingerprints and exclusive publication; failure in this sealed pre-publication window retains a hidden 0755 stage without the marker"],"allowed_persistent_mutations":["create one exact persistent 0700 challenge claim directory with exclusive mkdirat semantics and create/append one 0600 hash-chained ledger beneath it; the claim and ledger are never automatically deleted","create exactly one previously-absent approved target by a single successful renameatx_np(RENAME_EXCL)"],"forbidden_mutations":["overwrite, merge, unlink, replace or repair any existing target","modify existing repo-root package.json, package-lock.json or .gitignore; create any absent alternate lock file or .npmrc","write outside the exact identity-bound /private/tmp Git adapter scratch, exact persistent challenge claim/ledger, exact stage and exact exclusive target publication","modify Git objects, refs, index, hooks, config or any existing worktree file","modify parent or sibling worktree, user home, private Vault, Graphiti or external service","commit, push, branch/ref creation, OpenSpec execution or governance apply"],"git_metadata_adapter_cleanup_guarantee":"under the declared Git metadata adapter trust boundary and host assurance, cleanup success or retryable pre-claim failure requires pre-removal root and Git identity agreement, authorized-path removal, post-removal absence, and zero pathname and registry residue; any observed root or Git identity drift, missing authorized pathname, cleanup error, or residue is terminal and quiescence must fail; preservation against a non-cooperating same-UID replacement at the final pathname-deletion linearization point is outside the supported guarantee","git_metadata_adapter_host_assurance":"every spawned Git child is sandboxed and has no authority to create, rename, unlink or write the private-temporary parent namespace or any sibling adapter root; the product owns only the fresh exact adapter entry, root and descendants for that invocation, while /private/tmp and sibling entries remain ambient host namespace; every product invocation creates one fresh unique adapter root; the process-wide non-reentrant scope and registry forbid interleaved adapter ownership within one process and do not claim cross-process exclusion","git_metadata_adapter_trust_boundary":"the kernel and each owning same-UID production process are trusted; POSIX 0600 and 0700 modes isolate other UIDs but do not isolate an unsandboxed process with the same effective UID, so each adapter root has exactly one owning process and compliant same-UID product processes never mutate another invocation's root; non-cooperating same-UID filesystem mutation, out-of-process ptrace or code injection, and out-of-process access to the 0600 private HMAC key are outside the supported threat model","overwrite_allowed":false,"publish_attempt_ceiling":1,"publish_flag":"RENAME_EXCL","publish_syscall":"renameatx_np","target_preimage":"ABSENT"},"privacy":{"git_metadata_adapter_trust_boundary":"the kernel and each owning same-UID production process are trusted; POSIX 0600 and 0700 modes isolate other UIDs but do not isolate an unsandboxed process with the same effective UID, so each adapter root has exactly one owning process and compliant same-UID product processes never mutate another invocation's root; non-cooperating same-UID filesystem mutation, out-of-process ptrace or code injection, and out-of-process access to the 0600 private HMAC key are outside the supported threat model","graphiti_call_count":0,"network_call_count":0,"private_locator_public_count":0,"private_raw_sha256_only_for":["cache-root and direct-SRI content blob private locator evidence","dirty/untracked inventory","Git index/private config/hooks locator receipts","local settings","command output/open-file/process traces","persistent ledger and challenge claim"],"private_vault_read_count":0,"public_raw_sha256_allowed_for":["public repo artifacts including executor/verifier/schemas","locator-free toolchain content identities","content, USTAR, closure Merkle, resolution, expected-tree and public receipt digests"]},"private_state_authorization":{"all_cli_locators_compared_before_any_write":true,"authorized_locator_commitments":null,"challenge_claim_preimage":"exact state-root/claims/<approval_challenge_id> direct child ABSENT","claims_container_preimage":"state-root/claims already exists as a receipt-bound-owner-and-group real 0700 directory and is not created by this attempt","destruction_authorized":false,"first_authority_consuming_persistent_write":"mkdirat exact state-root/claims/<approval_challenge_id> with mode 0700 is the first authority-consuming persistent write; EEXIST is terminal replay; earlier writes are limited to the exact nonpersistent /private/tmp Git adapter scratch, which must be identity-bound and fully removed before any return","hmac_key_id":null,"hmac_key_id_profile":"HMAC-SHA-256 with the same private key over ASCII(CLS/GOV01/HMAC-KEY-ID/v2) || NUL || eight zero bytes; locator and raw key bytes are never serialized","locator_commitment_profile":"HMAC-SHA-256 with the authorized 32-byte private key over ASCII(CLS/GOV01/PRIVATE-LOCATOR/v2) || NUL || uint64be(canonical-body-byte-length) || UTF-8-NFC-LF canonical JSON {label,locator}; labels and absolute normalized no-symlink locators are exact and comparison uses hmac.compare_digest","persistent_single_use_ledger_required":true,"private_control_identity_commitment":null,"private_control_identity_commitment_profile":"HMAC-SHA-256 with the authorized 32-byte private key over ASCII(CLS/GOV01/PRIVATE-CONTROL-IDENTITY/v2) || NUL || uint64be(canonical-body-byte-length) || UTF-8-NFC-LF canonical JSON binding the receipt-approved owner UID, inherited control GID, exact state-root/claims/key modes and expected claim/ledger modes without serializing private locators","private_evidence_schema_required":"gov-01-toolchain-static-acquisition-private-evidence-v2","private_file_modes":{"directory":"0700","file":"0600","umask":"0077"},"private_preimage_checks":["five exact HMAC-bound locators; repo, cache and state roots are pairwise separated; the HMAC key is the exact state-root/hmac.key direct child; the envelope is contained by the control prefix; no symlink ancestor and no Vault or .obsidian component","cache-root locator and direct-SRI content blob bytes/digests; npm cache index read is prohibited","directly capture Git control marker, commondir, local configs, HEAD, index, refs, hooks and object store with absent alternate controls before constructing a sealed private adapter; sealed-evidence and bridge-free Git children use only the adapter through explicit --git-dir/--work-tree, while live-object bootstrap children may test existence only at the exact parent-prevalidated-absent live common-dir/objects/info/alternates path and cannot read its metadata or bytes; live metadata is revalidated after capture and before cleanup","pgrep Claude candidates and per-candidate lsof cwd stdout commitments without public command output","state-root, claims-container and HMAC-key owner/group/mode are bound by the private control identity commitment; exact challenge child absence, HMAC-key bytes, raw envelope bytes and approved receipt digest are rechecked before the first authority-consuming persistent write; only exact identity-bound Git adapter scratch creation and mandatory cleanup may occur earlier"],"private_read_authority":["resolve and hash exact toolchain realpaths bound by public content digests","derive and read exact local content-v2 archive blobs directly from package-lock sha512 SRI without reading any npm cache index","directly capture live Git control, HEAD, index, refs, config, hooks and object-store evidence into a path-free keyed source receipt; the captured index is strictly parsed and its root tree OID is recomputed with exactly one opaque gitlink at _reference/obsidian-sample-plugin without reading that gitlink object/subtree or unrelated tree/blob descendants; sealed-evidence and bridge-free Git children read only the adapter, while live-object bootstrap children may test existence only at the exact parent-prevalidated-absent live common-dir/objects/info/alternates path and cannot read its metadata or bytes; source CAS runs after capture, before and after sealed evidence, and before cleanup","run pgrep only for Claude candidates and lsof only for each returned PID cwd; no machine-wide lsof or broader process absence claim","read the pre-existing state-root/claims directory identities and require the exact challenge child absent; no pre-existing ledger is read"],"private_vault_authorized":false,"private_write_authority":["create, seal and mandatorily remove only the exact dev/inode-bound /private/tmp Git metadata adapter scratch; cleanup uncertainty or residue is terminal and this scratch never consumes the challenge","create exact 0700 persistent challenge claim directory and create/append its exact 0600 ledger.jsonl","create exact same-filesystem stage and publish exact absent target with RENAME_EXCL"],"public_serialization_forbidden":["private absolute or home-relative locator","cache-root locator or direct-SRI content blob private locator","dirty/untracked inventory or its raw digest","environment values, command output or open-file locator list","ledger locator/raw bytes, raw HMAC key or user receipt body","private Vault locator, name, content or digest"],"retention":"persistent challenge claim and ledger are retained outside repo and never automatically deleted; failed stage and any published target are never automatically deleted; the private-temp Git adapter is never retained intentionally and success requires exact cleanup with residue_count zero"},"schema_binding":{"external_validator_profile":"JSON-Schema-draft-2020-12-strict-additionalProperties-false-format-annotation-plus-content-addressed-strict-UTC-calendar-and-duplicate-key-checker","preapproval_external_validation_required":true,"runtime_checkpoint":"after raw receipt/challenge/expiry verification and schema artifact hash verification, before any other envelope-controlled read, verifier-source compilation, subprocess or write","runtime_json_schema_execution_allowed":false,"runtime_manual_critical_field_checks_required":true,"runtime_schema_hash_binding_required":true,"schema_artifact_path":"_bmad-output/\u5ba1\u67e5/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-envelope-v2.schema.json","schema_artifact_role":"pending-envelope-schema","schema_digest_must_equal_artifact_entry":true,"schema_id":"urn:canvas-learning-system:gov-01:toolchain-static-acquisition-pending-envelope:v2:draft","schema_raw_file_sha256":null,"validation_failure_action":"fail closed before any authorized write or verifier-source compilation"},"static_acquisition_contract":{"absent_control_paths":[".npmrc","npm-shrinkwrap.json","pnpm-lock.yaml","yarn.lock","bun.lock","bun.lockb"],"absent_control_pre_post_lstat_check_required":true,"compressed_blobs_memory_resident_before_write":true,"executor_artifact_path":"_bmad-output/\u5ba1\u67e5/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py","executor_sha256":null,"expected":null,"hidden_package_lock_generation_allowed":false,"lifecycle_execution_allowed":false,"network_allowed":false,"node_execution_allowed":false,"npm_execution_allowed":false,"openspec_execution_allowed":false,"openspec_scaffold_allowed":false,"payload_bytes_memory_resident_before_write":true,"protected_control_paths":["package.json","package-lock.json",".gitignore"],"protected_control_pre_post_hash_check_required":true,"stage_repo_relative":null,"target_repo_relative":"node_modules","verifier_artifact_path":"_bmad-output/\u5ba1\u67e5/phase0a-annotation-truth/GOV-01-toolchain-static-verifier-v2.py","verifier_profile_version":"gov-01-toolchain-static-verifier-v2","verifier_sha256":null},"success_contract":{"archive_member_execution_count":0,"commit_allowed":false,"content_mismatches":0,"forbidden_control_paths_present":0,"governance_apply_allowed":false,"host_package_count":167,"javascript_execution_count":0,"lifecycle_execution_count":0,"maximum_state":"static-attested-unexecuted","missing_expected_entries":0,"network_attempt_count":0,"next_required_authorization":"new runtime-use envelope binding the final-tree receipt and a fresh single-use challenge","npm_node_npx_execution_count":0,"outside_scope_mutation_count":0,"payload_execution_allowed_after_success":false,"protected_control_paths_changed":0,"push_allowed":false,"sandbox_exec_execution_count":0,"target_created_count":1,"target_tree_must_equal_expected_merkle":true,"unexpected_entries":0}}'''
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py:943:        "schema_version": PUBLIC_RESULT_SCHEMA_VERSION,
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py:1402:        or body.get("schema_version") != "gov-01-toolchain-control-prep-evidence-v1"
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py:1956:            "schema_version": "gov01-static-acquisition-gate-evidence-v2",
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py:2057:            "schema_version": "gov01-static-acquisition-gate-set-v2",
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py:2137:                "schema_version", "gate_id", "scope", "phase", "status",
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py:2151:            record.get("schema_version") != "gov01-static-acquisition-gate-evidence-v2"
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py:2178:            "schema_version": "gov01-static-acquisition-gate-set-v2",
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py:2202:    if result.get("schema_version") != PUBLIC_RESULT_SCHEMA_VERSION or result.get("artifact_type") != PUBLIC_RESULT_ARTIFACT_TYPE:
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py:2385:            "schema_version", "artifact_type", "ok", "mode", "phase", "state",
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py:2562:                "schema_version", "approval_challenge_id", "receipt_digest",
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py:2570:        cross(attestation.get("schema_version") == "gov01-static-acquisition-success-attestation-v2", "SUCCESS_ATTESTATION_VERSION")
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py:3539:        "schema_version": PUBLIC_RESULT_SCHEMA_VERSION,
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py:3684:            "schema_version sequence at_utc challenge receipt_digest event previous_hmac_sha256 data hmac_sha256".split(),
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py:3687:        if record.get("schema_version") != "gov01-static-acquisition-ledger-event-v2" or record.get("sequence") != index:
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py:3759:        "schema_version": "gov-01-toolchain-static-acquisition-private-evidence-v2",
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py:3838:    version = value.get("schema_version")
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py:3952:        "canonical_jsonl_and_hmac_chain_valid", "private_projection_schema_version",
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py:4117:            "private_projection_schema_version": "gov-01-toolchain-static-acquisition-private-evidence-v2",
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py:4287:                "schema_version artifact_type classification projection_kind ledger_parse_state "
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py:4296:                "schema_version artifact_type ok mode phase state terminal_state runtime_assurance gate_results "
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py:4387:    if envelope.get("schema_version") != "gov-01-toolchain-static-acquisition-envelope-v2":
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py:5118:        or value.get("schema_version") != "gov-01-toolchain-static-envelope-generation-envelope-v1"
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py:5289:    if envelope.get("schema_version") != "gov-01-toolchain-static-acquisition-envelope-v2":
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py:6466:            "schema_version": "gov01-static-acquisition-dynamic-toolchain-v2",
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py:6513:        "schema_version": "gov01-private-preapproval-census-v2",
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py:10870:            "schema_version": "gov01-static-acquisition-incomplete-v2",
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py:11082:            "schema_version": "gov01-static-acquisition-ledger-event-v2",
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py:11218:        "schema_version": "gov01-private-control-identity-v2",
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py:11234:            "schema_version owner_uid group_gid state_root_mode claims_mode hmac_key_mode "
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py:13649:        "schema_version": "gov-01-toolchain-static-acquisition-envelope-v2",
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py:14675:                "private_projection_schema_version": private_projection["schema_version"],
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py:14679:            "schema_version": "gov01-static-acquisition-success-attestation-v2",
./_bmad-output/research/obsidian-qa-round6-claude-answers-2026-04-15.md:190:| `notification_channels.py:25` | 警报触发时发送通知（structlog 日志 + alerts.log + Obsidian SSE 推送）|
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-envelope-generation-envelope-v1.GOV01-GEN-20260821-c2d2aed1adb598c76282e9826ef28797f13ccc3591bbd0f897b335d6ad8e9a5f.json:1:{"approval_challenge_id":"GOV01-GEN-20260821-c2d2aed1adb598c76282e9826ef28797f13ccc3591bbd0f897b335d6ad8e9a5f","artifact_id":"GOV-01-STATIC-ENVELOPE-GENERATION-20260821-97b335d6ad8e9a5f","artifact_type":"gov-01-toolchain-static-envelope-generation-envelope","artifacts":[{"byte_length":77024,"file_kind":"regular","path":"_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md","raw_file_sha256":"4841abe51a29110be92f1d6810d02654a82e8e2be9c4f922c0541561246ca512","role":"goal"},{"byte_length":42685,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/2026-08-20-GOV-01-追踪真相源修复决策稿.md","raw_file_sha256":"836a18560bc50d2fdd5c6c86c1de8b310498c523fb0e777abf117863d18f3b2a","role":"governance-decision"},{"byte_length":39848,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/2026-08-20-Phase0A-A01-A02-批注真相层实施契约.md","raw_file_sha256":"da0acd5558ef9669c3f2b948464e5ceda72288895d0bb3a3b4571b5bbd94b540","role":"phase0a-contract"},{"byte_length":8954,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-first-receipt-envelope-v1.json","raw_file_sha256":"0b73b83e1dbd92dd0a4684a83438dafc7afae6a6fde42b4130d776d7ee246410","role":"first-receipt-envelope"},{"byte_length":17623,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-first-receipt-envelope-v1.schema.json","raw_file_sha256":"bb680b866b89fad649953e23da1a8ba9e3529523485516ebd969849bff468298","role":"first-receipt-schema"},{"byte_length":5110,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/2026-08-20-GOV-01-Bootstrap-0-safe-mode.patch","raw_file_sha256":"d2f9a1ff45006cf19bd5295b751e2b620dc6043d6ec1ff26494c1d2d722aa8aa","role":"bootstrap-patch"},{"byte_length":13463,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-control-prep-envelope-v1.json","raw_file_sha256":"ef424f80672568076d750ae0f6d662ebfdae242fdea8fcda2b37f39e6406945b","role":"control-prep-envelope"},{"byte_length":23437,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-control-prep-envelope-v1.schema.json","raw_file_sha256":"5c6c07ffe71a8c39a6993b2c717b751988b94338800972bbcfe93363a152f984","role":"control-prep-schema"},{"byte_length":291290,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-envelope-generation-v1.py","raw_file_sha256":"c6745b954a3647d52e40d05773af0961b116134363239ceaa0bd1f5e64772f6c","role":"static-envelope-generator"},{"byte_length":41393,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-envelope-generation-envelope-v1.schema.json","raw_file_sha256":"547633e952c77e1b850ca3c8874bc6704286169afa98f275475fac9b0130132a","role":"generation-envelope-schema"},{"byte_length":232153,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-envelope-generation-hostile-fixtures-v1.py","raw_file_sha256":"82e33f145243b7dc84a0a7bae9c1c6cb13ea0cbd0a00ec41616432e854a12f60","role":"generation-hostile-fixture"},{"byte_length":709622,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py","raw_file_sha256":"e74e9cbe9c2403212dca3e40b0e9f8e2b732bce77dde04a05035099c5eb31ac5","role":"static-executor"},{"byte_length":50895,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-verifier-v2.py","raw_file_sha256":"98bcaaa35e2e4e7713e51e016af6c7223713acdb47a1b4b27859e70f75725064","role":"static-verifier"},{"byte_length":367213,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-static-acquisition-hostile-fixtures-v2.py","raw_file_sha256":"52108650cc4aaadb2606da44b4dd746f5a7670a519007abf8543fa104a3ac9a0","role":"static-hostile-fixture"},{"byte_length":100745,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-envelope-v2.schema.json","raw_file_sha256":"f07c4d19c1d22596520d2e201dcb56f701a00716e5390a15800f3ca83510f4bb","role":"pending-envelope-schema"},{"byte_length":98752,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-private-evidence-v2.schema.json","raw_file_sha256":"f2120fea08da5c726801ec9ec7311c78aaf28629494f4d6a4a39cfa6cffa9c8c","role":"private-evidence-schema"},{"byte_length":195320,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-public-attestation-v2.schema.json","raw_file_sha256":"9ae37b5e46e626ef738d451d56085a7bb714a3768009b2e141f940c9d585b7ac","role":"public-attestation-schema"},{"byte_length":817,"file_kind":"regular","path":"package.json","raw_file_sha256":"bd5c4e933e2dcbf7f2019bec9fec555b5b1adff1c4a6e5c36ea4415ff9a711fe","role":"package-manifest"},{"byte_length":83153,"file_kind":"regular","path":"package-lock.json","raw_file_sha256":"c6e190741427b99ff132d6504b2a782d75c418d6ae93066769ac422bff6b7cea","role":"package-lock"},{"byte_length":5413,"file_kind":"regular","path":".gitignore","raw_file_sha256":"679c83badb0067729c75a48f9391849542fc71a03c133d8d0dc33cfe7e836351","role":"gitignore"}],"authorized_reads":{"git_generation_output_exclusion":"exclude exactly the one derived regular-file generation output path from Git status and dirty-content commitment; never exclude its parent directory or a wildcard subtree; separately require output preimage ABSENT and later bind raw output bytes by the external acquisition receipt","npm_cache_index_read_count":0,"private_roles_after_approval":["exact 0600 32-byte hmac.key for domain-separated HMAC only","derived control root and claims metadata plus exact fresh acquisition challenge child absence","exact locator-free canonical control-preparation receipt content for predecessor-chain verification","Git marker commondir local config index refs contained hooks and dirty or untracked metadata and regular content, with Vault and .obsidian paths rejected before open","package-lock-selected direct-SRI npm cache content-v2 blobs only","target-worktree-associated Claude process census evidence"],"public_repo_artifact_policy":"only exact versioned artifact paths listed in this envelope plus package.json package-lock.json .gitignore and Git control evidence required by the frozen static executor","user_or_managed_settings_read_count":0,"vault_read_count":0},"authorized_subprocesses":{"environment_profile":"new exact sanitized environment; HOME=/var/empty and TMPDIR=DARWIN_USER_TEMP_DIR=/tmp; every Git child starts only after fchdir to the exact identity-bound adapter Git directory and uses relative --git-dir=.; bootstrap Git receives only exact captured GIT_OBJECT_DIRECTORY while global/system config, inherited alternates and protocols are disabled; final Git evidence unsets live object access and uses only the sealed adapter; fsmonitor, hooks, attributes, includes, alternates, grafts, network, and worktree reads are rejected or sandbox-denied","git_child_sandbox_profile":"every Git child calls /usr/lib/libsandbox.1.dylib sandbox_init exactly once before exec with a generated default-deny profile; before every Git exec the parent passes only one per-child duplicate of the pinned adapter-Git directory FD, and preexec performs fchdir of that exact identity, closes the duplicate, then calls sandbox_init exactly once; no usable directory FD reaches Git, fixed argv uses relative --git-dir=., and no path discovery is permitted; the git-metadata-adapter-bootstrap role permits only the content-bound CommandLineTools tree, one unsealed checkpoint-scoped private-temporary adapter, captured live pack or loose object containers needed to extract the exact approved OID set, and adapter-only writes needed by index-pack; it denies network, worktree payload, every live Git control path, alternates and graft bytes, and all other reads or writes; after source CAS and sealing, git-read-only-evidence permits only the CommandLineTools tree and sealed adapter and denies writes and all live Git or worktree reads; the parent revalidates captured live source before adapter removal; every child profile explicitly denies create rename unlink or write authority over the private-temporary parent namespace and sibling adapter roots, while index-pack writes are restricted to the pinned current adapter objects/pack directory; sandbox initialization failure is terminal; /usr/bin/sandbox-exec is never executed","network_allowed":false,"node_npm_npx_openspec_allowed":false,"roles":["xcode-select-resolver","xcrun-resolver","git-metadata-adapter-bootstrap","git-read-only-evidence","pgrep-read-only-evidence","lsof-read-only-evidence"],"shell_allowed":false},"challenge_and_time_contract":{"acquisition_entropy":"exactly one os.urandom(32) call after generation approval and before private census; lowercase 64-hex suffix; caller-supplied entropy forbidden","challenge_date_binding":"each challenge YYYYMMDD component equals its own canonical UTC issued or census date","clock_skew_ceiling_seconds":300,"expiry_checkpoints":["micro-envelope load","immediately before the persistent generation claim mkdir","after generation claim verification and immediately before the public output create","after output reopen before emitting pending-user-confirmation"],"generation_entropy":"exactly one os.urandom(32) call before the public generation micro-envelope is written; lowercase 64-hex suffix; caller-supplied entropy forbidden","namespace_separation":"generation challenge uses GOV01-GEN and acquisition challenge uses GOV01-SA; equality or cross-namespace reuse is impossible by grammar","ttl_ceiling_seconds":86400},"encoding_profile":"UTF-8-NFC-LF-no-BOM-no-duplicate-json-keys","failure_contract":{"existing_complete_output":"under the same still-valid exact GEN receipt, authenticate the retained generation claim, reuse only its fixed acquisition challenge and timestamps, revalidate every public and private commitment including hmac.key-derived commitments, require rebuilt raw bytes exact, then re-emit the same raw receipt digest without writing anything","existing_partial_or_invalid_output":"a partial or invalid generation claim is terminal consumed; a valid claim with absent output may recreate only its exact fixed raw output; any partial invalid or drifted existing output is retained and requires a new generation micro-envelope","post_create_failure":"after the generation claim mkdir, retain claim record and any output bytes and stop; never truncate delete overwrite repair or mint another acquisition challenge from this generation authority","pre_output_failure":"before the generation claim mkdir, no persistent repository control product claim or output write; the exact approved preflight may use only checkpoint-scoped private-temporary Git metadata adapters and may rerun before expiry only after exact cleanup with zero residue while every bound input is unchanged and both claim and output remain absent","retry_policy":"single-use begins at successful exclusive generation claim mkdir; only a pre-claim failure with confirmed temporary-adapter cleanup and zero residue may rerun within the exact receipt TTL; every post-claim path is pinned to the claim-authenticated acquisition challenge timestamps and final raw digest","temporary_adapter_failure":"adapter cleanup failure root-identity uncertainty or any residue is terminal fail-closed for this attempt: do not publish, do not report retryable, retain evidence for private inspection, and require new authority before another attempt"},"generation_claim_contract":{"generation_claim_profile":"exclusive-0700-generation-claim-directory-with-exclusive-0600-canonical-HMAC-record-v1","generation_claim_record_profile":"HMAC-SHA-256 with the authorized 32-byte private key over ASCII(CLS/GOV01/STATIC-ENVELOPE-GENERATION-CLAIM/v1) || NUL || uint64be(canonical-body-byte-length) || canonical JSON binding GEN receipt/raw, C1/C2 identities, one SA/time tuple and final raw SHA-256/bytes/domain receipt","generation_claim_required":true,"generation_claim_retention":"retain permanently; never delete, overwrite or repair; a complete valid claim permits only byte-exact recovery with its recorded SA and times"},"issued_at_utc":"2026-08-21T23:51:28Z","locator_derivation_contract":{"cache_root":"pwd.getpwuid(the control-preparation expected created uid).pw_dir plus exact suffix .npm; normalize once, require absolute realpath equality, owner uid equality, no symlink component and no Vault component","caller_supplied_locator_count":0,"claims_root":"exact direct child claims beneath the derived state root; validate retained GOV01-SA claim directories and generation-claim-GOV01-GEN directories, require this GEN claim preimage ABSENT before fresh entropy, and require the fresh acquisition challenge child preimage ABSENT","final_locator_commitment_timing":"resolve derived private locators and calculate domain-separated keyed commitments only after approval; serialize commitments but never raw private locators into the final acquisition envelope","generation_output":"repo root plus exact control-prefix regular-file name GOV-01-toolchain-static-acquisition-pending-<approved-GOV01-GEN-challenge>.json; the final envelope separately carries one fresh GOV01-SA acquisition challenge","key_file":"exact direct child hmac.key beneath the derived state root","repo_root":"derive from the no-symlink realpath of the content-addressed generator __file__ by removing its exact repo-relative suffix","state_root":"read the exact target.absolute_path from the content-addressed committed control-preparation envelope only after this generation receipt is approved"},"mutation_scope":{"allowed_ephemeral_mutations":["create one fresh unique checkpoint-scoped private-temporary 0700 Git metadata adapter for each production Git evidence checkpoint after the applicable public issue invocation or exact GEN receipt has authorized Git inspection; permit at most one active adapter owner within a process","write only its 0600 sanitized Git control metadata through pinned root and Git directory FDs; resolve bootstrap and import argv only from the identity-bound adapter Git cwd with relative --git-dir=., keep index-pack pack/index output beneath objects/pack, verify every exact-OID partial-pack object hash, then seal files 0400 beneath 0500 directories through pinned FDs; no adapter locator or raw metadata may enter public output","within the declared trust boundary and host assurance, remove the unique registered adapter at its authorized pathname only after captured root and Git identity checks, then require authorized-path absence and zero registry residue before success or retryable pre-claim failure"],"allowed_persistent_mutations":["create and fsync exactly one previously-absent 0700 generation claim directory beneath the existing receipt-bound claims container","create and fsync exactly one 0600 canonical HMAC-authenticated generation-record.json beneath that claim and fsync both claim and claims directories","create and fsync exactly one previously-absent public acquisition envelope regular file beneath the repository control prefix","fsync its already-existing parent directory"],"commit_allowed":false,"first_authority_consuming_persistent_write":"exclusive mkdirat of exact claims/generation-claim-<approved-GOV01-GEN-challenge> mode 0700 after every private read schema manual privacy and drift check has passed; EEXIST permanently forbids minting another acquisition challenge","git_metadata_adapter_cleanup_guarantee":"under the declared Git metadata adapter trust boundary and host assurance, cleanup success or retryable pre-claim failure requires pre-removal root and Git identity agreement, authorized-path removal, post-removal absence, and zero pathname and registry residue; any observed root or Git identity drift, missing authorized pathname, cleanup error, or residue is terminal and quiescence must fail; preservation against a non-cooperating same-UID replacement at the final pathname-deletion linearization point is outside the supported guarantee","git_metadata_adapter_host_assurance":"every spawned Git child is sandboxed and has no authority to create, rename, unlink or write the private-temporary parent namespace or any sibling adapter root; the product owns only the fresh exact adapter entry, root and descendants for that invocation, while /private/tmp and sibling entries remain ambient host namespace; every product invocation creates one fresh unique adapter root; the process-wide non-reentrant scope and registry forbid interleaved adapter ownership within one process and do not claim cross-process exclusion","git_metadata_adapter_trust_boundary":"the kernel and each owning same-UID production process are trusted; POSIX 0600 and 0700 modes isolate other UIDs but do not isolate an unsandboxed process with the same effective UID, so each adapter root has exactly one owning process and compliant same-UID product processes never mutate another invocation's root; non-cooperating same-UID filesystem mutation, out-of-process ptrace or code injection, and out-of-process access to the 0600 private HMAC key are outside the supported threat model","output_mode":"0644","overwrite_allowed":false,"product_state_cleanup_allowed":false,"push_allowed":false,"sidecar_allowed":false,"temporary_adapter_cleanup_required":true,"temporary_adapter_residue_allowed":false,"temporary_git_metadata_adapter_profile":"checkpoint-scoped-private-temp-sanitized-required-path-ancestor-exact-oid-index-root-proven-one-exact-public-opaque-gitlink-identity-bound-git-fd-metadata-adapter-v5"},"not_after_utc":"2026-08-22T23:51:28Z","plan_id":"PLAN-CLS-PRODUCTIVITY-2026-08-20","predecessor":{"bootstrap_commit_oid":"0e0f0150be184f4dad83a859b0fdd232ec53e8b5","bootstrap_patch_raw_sha256":"d2f9a1ff45006cf19bd5295b751e2b620dc6043d6ec1ff26494c1d2d722aa8aa","control_preparation_envelope_raw_sha256":"ef424f80672568076d750ae0f6d662ebfdae242fdea8fcda2b37f39e6406945b","control_preparation_receipt_domain_sha256":"dbb28c7627b63989e98b70ff608c20976d687541364af95804537dda7867541c","control_preparation_state":"independently-verified-control-prepared","first_approval_envelope_raw_sha256":"0b73b83e1dbd92dd0a4684a83438dafc7afae6a6fde42b4130d776d7ee246410","first_receipt_domain_sha256":"c89e7195e67b60a26117469e2b212fb508c0a5a64cac5d25a59a257f73b55740","static_contract_commit_oid":"858202058e186110488658ca6dad0e47c78d47c0","static_contract_tree_oid":"f3256a72be6d8094236cd4824355b94ccdc127ab"},"privacy":{"git_metadata_adapter_trust_boundary":"the kernel and each owning same-UID production process are trusted; POSIX 0600 and 0700 modes isolate other UIDs but do not isolate an unsandboxed process with the same effective UID, so each adapter root has exactly one owning process and compliant same-UID product processes never mutate another invocation's root; non-cooperating same-UID filesystem mutation, out-of-process ptrace or code injection, and out-of-process access to the 0600 private HMAC key are outside the supported threat model","graphiti_call_count":0,"network_call_count":0,"private_key_publication_allowed":false,"raw_command_output_publication_allowed":false,"raw_private_locator_public_count":0,"vault_read_count":0,"whole_envelope_checker":"field-aware recursive checker before write and before stdout; repo paths use strict relative grammar; tool logical IDs and versions use role-specific ASCII grammar; only schema-enumerated fixed public system command locators and placeholders are allowed; all other absolute home file-URI Vault .obsidian control bidi and secret-bearing values are rejected"},"receipt_digest_profile":"SHA-256(ASCII(CLS/GOV01-STATIC-ENVELOPE-GENERATION-RECEIPT/v1) || NUL || raw-envelope-bytes); digest supplied by user and stored externally","repository_transition":{"approved_commit_shape":"current HEAD has exactly one parent equal to authorization_baseline_head; a path-local Merkle comparison of authenticated current and parent ancestor tree objects proves exactly the micro envelope regular file was added with bytes equal to the approved raw envelope and every non-target entry is byte-identical; no other path is added modified deleted renamed or type-changed","authorization_baseline_head":"858202058e186110488658ca6dad0e47c78d47c0","authorization_baseline_head_ref_bytes":47,"authorization_baseline_head_ref_profile":"SHA-256(ASCII(CLS/GOV01-STATIC-ENVELOPE-HEAD-REF/v1) || NUL || exact symbolic HEAD ref ASCII bytes); raw ref is never serialized","authorization_baseline_head_ref_sha256":"c58034b19de75ff292906142ab44cd41a8b688b48862a63dd8c01f42040459d2","authorization_baseline_head_symbolic":true,"authorization_baseline_other_refs_bytes":3648,"authorization_baseline_other_refs_sha256":"56d06c459e4cff8a2a871f24b2b335f1739edee6126eb5a8f9be4ecb84016b3d","authorization_baseline_tree":"f3256a72be6d8094236cd4824355b94ccdc127ab","captured_index_root_profile":"strict captured DIRC v2 or v3 canonical bottom-up root-tree recomputation equal to authenticated HEAD; require the mode 160000 opaque-leaf path set to equal the exact public singleton _reference/obsidian-sample-plugin without opening requesting or dereferencing its object OID; reject a missing or mode-replaced singleton and every extra or substituted gitlink; in a parsed required-path ancestor tree permit that same singleton only as an unselected opaque sibling, and reject it if selected as a required terminal or ancestor","generation_output_preimage":"ABSENT","generation_output_repo_relative":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-pending-GOV01-GEN-20260821-c2d2aed1adb598c76282e9826ef28797f13ccc3591bbd0f897b335d6ad8e9a5f.json","git_control_profile":{"alternate_object_controls_absent":true,"common_directory_relation":"git-directory-contained-under-common-worktrees","include_controls_absent":true,"marker_kind":"gitfile"},"index_must_equal_head":true,"issue_publication_checkpoint_profile":"capture one initial exact Git-source index-root and public-artifact checkpoint; while holding a nonblocking advisory lock on the exact shared control-parent directory FD, recapture an equal checkpoint immediately before micro-envelope O_EXCL and require both micro and generation-output preimages absent; after fsync and same-FD byte-exact reopen, require generation-output absence, recapture the same equal checkpoint, and require generation-output absence again before success","micro_envelope_preimage":"ABSENT","micro_envelope_repo_relative":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-envelope-generation-envelope-v1.GOV01-GEN-20260821-c2d2aed1adb598c76282e9826ef28797f13ccc3591bbd0f897b335d6ad8e9a5f.json","refs_except_head_must_be_unchanged":true},"schema_binding":{"content_addressed_manual_checker_required":true,"external_draft202012_validation_required":true,"schema_artifact_path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-envelope-generation-envelope-v1.schema.json","schema_id":"urn:canvas-learning-system:gov-01:toolchain-static-envelope-generation-envelope:v1","schema_raw_file_sha256":"547633e952c77e1b850ca3c8874bc6704286169afa98f275475fac9b0130132a","whole_envelope_privacy_checker_required":true},"schema_version":"gov-01-toolchain-static-envelope-generation-envelope-v1","single_use":true,"state":"pending-user-confirmation","success_contract":{"acquisition_execution_authorized":false,"maximum_state":"ACQUISITION-ENVELOPE-FROZEN-PENDING-USER-CONFIRMATION","next_required_authority":"user must separately cite the exact final acquisition raw-envelope receipt digest and GOV01-SA challenge before verify or acquire; acquisition success still stops at static-attested-unexecuted","runtime_use_authorized":false,"stdout_fields":["state","artifact_path","raw_envelope_receipt_digest","generation_approval_challenge_id","approval_challenge_id","not_after_utc"]}}
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-envelope-generation-envelope-v1.GOV01-GEN-20260822-b7c580f0b4d253b41448efc57582c1037fe30fa440d79d0ff7b602f7040c9d20.json:1:{"approval_challenge_id":"GOV01-GEN-20260822-b7c580f0b4d253b41448efc57582c1037fe30fa440d79d0ff7b602f7040c9d20","artifact_id":"GOV-01-STATIC-ENVELOPE-GENERATION-20260822-f7b602f7040c9d20","artifact_type":"gov-01-toolchain-static-envelope-generation-envelope","artifacts":[{"byte_length":77024,"file_kind":"regular","path":"_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md","raw_file_sha256":"4841abe51a29110be92f1d6810d02654a82e8e2be9c4f922c0541561246ca512","role":"goal"},{"byte_length":42685,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/2026-08-20-GOV-01-追踪真相源修复决策稿.md","raw_file_sha256":"836a18560bc50d2fdd5c6c86c1de8b310498c523fb0e777abf117863d18f3b2a","role":"governance-decision"},{"byte_length":39848,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/2026-08-20-Phase0A-A01-A02-批注真相层实施契约.md","raw_file_sha256":"da0acd5558ef9669c3f2b948464e5ceda72288895d0bb3a3b4571b5bbd94b540","role":"phase0a-contract"},{"byte_length":8954,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-first-receipt-envelope-v1.json","raw_file_sha256":"0b73b83e1dbd92dd0a4684a83438dafc7afae6a6fde42b4130d776d7ee246410","role":"first-receipt-envelope"},{"byte_length":17623,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-first-receipt-envelope-v1.schema.json","raw_file_sha256":"bb680b866b89fad649953e23da1a8ba9e3529523485516ebd969849bff468298","role":"first-receipt-schema"},{"byte_length":5110,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/2026-08-20-GOV-01-Bootstrap-0-safe-mode.patch","raw_file_sha256":"d2f9a1ff45006cf19bd5295b751e2b620dc6043d6ec1ff26494c1d2d722aa8aa","role":"bootstrap-patch"},{"byte_length":13463,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-control-prep-envelope-v1.json","raw_file_sha256":"ef424f80672568076d750ae0f6d662ebfdae242fdea8fcda2b37f39e6406945b","role":"control-prep-envelope"},{"byte_length":23437,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-control-prep-envelope-v1.schema.json","raw_file_sha256":"5c6c07ffe71a8c39a6993b2c717b751988b94338800972bbcfe93363a152f984","role":"control-prep-schema"},{"byte_length":291290,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-envelope-generation-v1.py","raw_file_sha256":"c6745b954a3647d52e40d05773af0961b116134363239ceaa0bd1f5e64772f6c","role":"static-envelope-generator"},{"byte_length":41393,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-envelope-generation-envelope-v1.schema.json","raw_file_sha256":"547633e952c77e1b850ca3c8874bc6704286169afa98f275475fac9b0130132a","role":"generation-envelope-schema"},{"byte_length":246645,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-envelope-generation-hostile-fixtures-v1.py","raw_file_sha256":"3b472df90684527ecc27fc75e2a448e1f6602e01e0ac557d8a171e78e0e47e3b","role":"generation-hostile-fixture"},{"byte_length":715461,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py","raw_file_sha256":"ac06e7c7747ffafcb16a270d246438f8e68f8343127ecec1d8216964ce2c52e2","role":"static-executor"},{"byte_length":50895,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-verifier-v2.py","raw_file_sha256":"98bcaaa35e2e4e7713e51e016af6c7223713acdb47a1b4b27859e70f75725064","role":"static-verifier"},{"byte_length":384784,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-static-acquisition-hostile-fixtures-v2.py","raw_file_sha256":"7fbff21f32ae34ef80b280f3c452372a7549656857c0951f891cdf39d9af0f9c","role":"static-hostile-fixture"},{"byte_length":100745,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-envelope-v2.schema.json","raw_file_sha256":"082ff5a141c9b21e355a31ed6ab70794e6c3e5216174976e47440464aa943b14","role":"pending-envelope-schema"},{"byte_length":98752,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-private-evidence-v2.schema.json","raw_file_sha256":"d6d46c961f778163a6b9ba5a216d00983cae76d00a33a7e1f5ad8bed4e34be1d","role":"private-evidence-schema"},{"byte_length":195320,"file_kind":"regular","path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-public-attestation-v2.schema.json","raw_file_sha256":"71e160ef7e4cbd56497b865e5d2a27837312d109e759b8f879586b36152624b1","role":"public-attestation-schema"},{"byte_length":817,"file_kind":"regular","path":"package.json","raw_file_sha256":"bd5c4e933e2dcbf7f2019bec9fec555b5b1adff1c4a6e5c36ea4415ff9a711fe","role":"package-manifest"},{"byte_length":83153,"file_kind":"regular","path":"package-lock.json","raw_file_sha256":"c6e190741427b99ff132d6504b2a782d75c418d6ae93066769ac422bff6b7cea","role":"package-lock"},{"byte_length":5413,"file_kind":"regular","path":".gitignore","raw_file_sha256":"679c83badb0067729c75a48f9391849542fc71a03c133d8d0dc33cfe7e836351","role":"gitignore"}],"authorized_reads":{"git_generation_output_exclusion":"exclude exactly the one derived regular-file generation output path from Git status and dirty-content commitment; never exclude its parent directory or a wildcard subtree; separately require output preimage ABSENT and later bind raw output bytes by the external acquisition receipt","npm_cache_index_read_count":0,"private_roles_after_approval":["exact 0600 32-byte hmac.key for domain-separated HMAC only","derived control root and claims metadata plus exact fresh acquisition challenge child absence","exact locator-free canonical control-preparation receipt content for predecessor-chain verification","Git marker commondir local config index refs contained hooks and dirty or untracked metadata and regular content, with Vault and .obsidian paths rejected before open","package-lock-selected direct-SRI npm cache content-v2 blobs only","target-worktree-associated Claude process census evidence"],"public_repo_artifact_policy":"only exact versioned artifact paths listed in this envelope plus package.json package-lock.json .gitignore and Git control evidence required by the frozen static executor","user_or_managed_settings_read_count":0,"vault_read_count":0},"authorized_subprocesses":{"environment_profile":"new exact sanitized environment; HOME=/var/empty and TMPDIR=DARWIN_USER_TEMP_DIR=/tmp; every Git child starts only after fchdir to the exact identity-bound adapter Git directory and uses relative --git-dir=.; bootstrap Git receives only exact captured GIT_OBJECT_DIRECTORY while global/system config, inherited alternates and protocols are disabled; final Git evidence unsets live object access and uses only the sealed adapter; fsmonitor, hooks, attributes, includes, alternates, grafts, network, and worktree reads are rejected or sandbox-denied","git_child_sandbox_profile":"every Git child calls /usr/lib/libsandbox.1.dylib sandbox_init exactly once before exec with a generated default-deny profile; before every Git exec the parent passes only one per-child duplicate of the pinned adapter-Git directory FD, and preexec performs fchdir of that exact identity, closes the duplicate, then calls sandbox_init exactly once; no usable directory FD reaches Git, fixed argv uses relative --git-dir=., and no path discovery is permitted; the git-metadata-adapter-bootstrap role permits only the content-bound CommandLineTools tree, one unsealed checkpoint-scoped private-temporary adapter, captured live pack or loose object containers needed to extract the exact approved OID set, and adapter-only writes needed by index-pack; it denies network, worktree payload, every live Git control path, alternates and graft bytes, and all other reads or writes; after source CAS and sealing, git-read-only-evidence permits only the CommandLineTools tree and sealed adapter and denies writes and all live Git or worktree reads; the parent revalidates captured live source before adapter removal; every child profile explicitly denies create rename unlink or write authority over the private-temporary parent namespace and sibling adapter roots, while index-pack writes are restricted to the pinned current adapter objects/pack directory; sandbox initialization failure is terminal; /usr/bin/sandbox-exec is never executed","network_allowed":false,"node_npm_npx_openspec_allowed":false,"roles":["xcode-select-resolver","xcrun-resolver","git-metadata-adapter-bootstrap","git-read-only-evidence","pgrep-read-only-evidence","lsof-read-only-evidence"],"shell_allowed":false},"challenge_and_time_contract":{"acquisition_entropy":"exactly one os.urandom(32) call after generation approval and before private census; lowercase 64-hex suffix; caller-supplied entropy forbidden","challenge_date_binding":"each challenge YYYYMMDD component equals its own canonical UTC issued or census date","clock_skew_ceiling_seconds":300,"expiry_checkpoints":["micro-envelope load","immediately before the persistent generation claim mkdir","after generation claim verification and immediately before the public output create","after output reopen before emitting pending-user-confirmation"],"generation_entropy":"exactly one os.urandom(32) call before the public generation micro-envelope is written; lowercase 64-hex suffix; caller-supplied entropy forbidden","namespace_separation":"generation challenge uses GOV01-GEN and acquisition challenge uses GOV01-SA; equality or cross-namespace reuse is impossible by grammar","ttl_ceiling_seconds":86400},"encoding_profile":"UTF-8-NFC-LF-no-BOM-no-duplicate-json-keys","failure_contract":{"existing_complete_output":"under the same still-valid exact GEN receipt, authenticate the retained generation claim, reuse only its fixed acquisition challenge and timestamps, revalidate every public and private commitment including hmac.key-derived commitments, require rebuilt raw bytes exact, then re-emit the same raw receipt digest without writing anything","existing_partial_or_invalid_output":"a partial or invalid generation claim is terminal consumed; a valid claim with absent output may recreate only its exact fixed raw output; any partial invalid or drifted existing output is retained and requires a new generation micro-envelope","post_create_failure":"after the generation claim mkdir, retain claim record and any output bytes and stop; never truncate delete overwrite repair or mint another acquisition challenge from this generation authority","pre_output_failure":"before the generation claim mkdir, no persistent repository control product claim or output write; the exact approved preflight may use only checkpoint-scoped private-temporary Git metadata adapters and may rerun before expiry only after exact cleanup with zero residue while every bound input is unchanged and both claim and output remain absent","retry_policy":"single-use begins at successful exclusive generation claim mkdir; only a pre-claim failure with confirmed temporary-adapter cleanup and zero residue may rerun within the exact receipt TTL; every post-claim path is pinned to the claim-authenticated acquisition challenge timestamps and final raw digest","temporary_adapter_failure":"adapter cleanup failure root-identity uncertainty or any residue is terminal fail-closed for this attempt: do not publish, do not report retryable, retain evidence for private inspection, and require new authority before another attempt"},"generation_claim_contract":{"generation_claim_profile":"exclusive-0700-generation-claim-directory-with-exclusive-0600-canonical-HMAC-record-v1","generation_claim_record_profile":"HMAC-SHA-256 with the authorized 32-byte private key over ASCII(CLS/GOV01/STATIC-ENVELOPE-GENERATION-CLAIM/v1) || NUL || uint64be(canonical-body-byte-length) || canonical JSON binding GEN receipt/raw, C1/C2 identities, one SA/time tuple and final raw SHA-256/bytes/domain receipt","generation_claim_required":true,"generation_claim_retention":"retain permanently; never delete, overwrite or repair; a complete valid claim permits only byte-exact recovery with its recorded SA and times"},"issued_at_utc":"2026-08-22T07:02:45Z","locator_derivation_contract":{"cache_root":"pwd.getpwuid(the control-preparation expected created uid).pw_dir plus exact suffix .npm; normalize once, require absolute realpath equality, owner uid equality, no symlink component and no Vault component","caller_supplied_locator_count":0,"claims_root":"exact direct child claims beneath the derived state root; validate retained GOV01-SA claim directories and generation-claim-GOV01-GEN directories, require this GEN claim preimage ABSENT before fresh entropy, and require the fresh acquisition challenge child preimage ABSENT","final_locator_commitment_timing":"resolve derived private locators and calculate domain-separated keyed commitments only after approval; serialize commitments but never raw private locators into the final acquisition envelope","generation_output":"repo root plus exact control-prefix regular-file name GOV-01-toolchain-static-acquisition-pending-<approved-GOV01-GEN-challenge>.json; the final envelope separately carries one fresh GOV01-SA acquisition challenge","key_file":"exact direct child hmac.key beneath the derived state root","repo_root":"derive from the no-symlink realpath of the content-addressed generator __file__ by removing its exact repo-relative suffix","state_root":"read the exact target.absolute_path from the content-addressed committed control-preparation envelope only after this generation receipt is approved"},"mutation_scope":{"allowed_ephemeral_mutations":["create one fresh unique checkpoint-scoped private-temporary 0700 Git metadata adapter for each production Git evidence checkpoint after the applicable public issue invocation or exact GEN receipt has authorized Git inspection; permit at most one active adapter owner within a process","write only its 0600 sanitized Git control metadata through pinned root and Git directory FDs; resolve bootstrap and import argv only from the identity-bound adapter Git cwd with relative --git-dir=., keep index-pack pack/index output beneath objects/pack, verify every exact-OID partial-pack object hash, then seal files 0400 beneath 0500 directories through pinned FDs; no adapter locator or raw metadata may enter public output","within the declared trust boundary and host assurance, remove the unique registered adapter at its authorized pathname only after captured root and Git identity checks, then require authorized-path absence and zero registry residue before success or retryable pre-claim failure"],"allowed_persistent_mutations":["create and fsync exactly one previously-absent 0700 generation claim directory beneath the existing receipt-bound claims container","create and fsync exactly one 0600 canonical HMAC-authenticated generation-record.json beneath that claim and fsync both claim and claims directories","create and fsync exactly one previously-absent public acquisition envelope regular file beneath the repository control prefix","fsync its already-existing parent directory"],"commit_allowed":false,"first_authority_consuming_persistent_write":"exclusive mkdirat of exact claims/generation-claim-<approved-GOV01-GEN-challenge> mode 0700 after every private read schema manual privacy and drift check has passed; EEXIST permanently forbids minting another acquisition challenge","git_metadata_adapter_cleanup_guarantee":"under the declared Git metadata adapter trust boundary and host assurance, cleanup success or retryable pre-claim failure requires pre-removal root and Git identity agreement, authorized-path removal, post-removal absence, and zero pathname and registry residue; any observed root or Git identity drift, missing authorized pathname, cleanup error, or residue is terminal and quiescence must fail; preservation against a non-cooperating same-UID replacement at the final pathname-deletion linearization point is outside the supported guarantee","git_metadata_adapter_host_assurance":"every spawned Git child is sandboxed and has no authority to create, rename, unlink or write the private-temporary parent namespace or any sibling adapter root; the product owns only the fresh exact adapter entry, root and descendants for that invocation, while /private/tmp and sibling entries remain ambient host namespace; every product invocation creates one fresh unique adapter root; the process-wide non-reentrant scope and registry forbid interleaved adapter ownership within one process and do not claim cross-process exclusion","git_metadata_adapter_trust_boundary":"the kernel and each owning same-UID production process are trusted; POSIX 0600 and 0700 modes isolate other UIDs but do not isolate an unsandboxed process with the same effective UID, so each adapter root has exactly one owning process and compliant same-UID product processes never mutate another invocation's root; non-cooperating same-UID filesystem mutation, out-of-process ptrace or code injection, and out-of-process access to the 0600 private HMAC key are outside the supported threat model","output_mode":"0644","overwrite_allowed":false,"product_state_cleanup_allowed":false,"push_allowed":false,"sidecar_allowed":false,"temporary_adapter_cleanup_required":true,"temporary_adapter_residue_allowed":false,"temporary_git_metadata_adapter_profile":"checkpoint-scoped-private-temp-sanitized-required-path-ancestor-exact-oid-index-root-proven-one-exact-public-opaque-gitlink-identity-bound-git-fd-metadata-adapter-v5"},"not_after_utc":"2026-08-23T07:02:45Z","plan_id":"PLAN-CLS-PRODUCTIVITY-2026-08-20","predecessor":{"bootstrap_commit_oid":"0e0f0150be184f4dad83a859b0fdd232ec53e8b5","bootstrap_patch_raw_sha256":"d2f9a1ff45006cf19bd5295b751e2b620dc6043d6ec1ff26494c1d2d722aa8aa","control_preparation_envelope_raw_sha256":"ef424f80672568076d750ae0f6d662ebfdae242fdea8fcda2b37f39e6406945b","control_preparation_receipt_domain_sha256":"dbb28c7627b63989e98b70ff608c20976d687541364af95804537dda7867541c","control_preparation_state":"independently-verified-control-prepared","first_approval_envelope_raw_sha256":"0b73b83e1dbd92dd0a4684a83438dafc7afae6a6fde42b4130d776d7ee246410","first_receipt_domain_sha256":"c89e7195e67b60a26117469e2b212fb508c0a5a64cac5d25a59a257f73b55740","static_contract_commit_oid":"efff5a5b803e84cf193c6b5dd67e7c947cb9f09d","static_contract_tree_oid":"10df659d060c2c26b914cadea9b2e9233824d365"},"privacy":{"git_metadata_adapter_trust_boundary":"the kernel and each owning same-UID production process are trusted; POSIX 0600 and 0700 modes isolate other UIDs but do not isolate an unsandboxed process with the same effective UID, so each adapter root has exactly one owning process and compliant same-UID product processes never mutate another invocation's root; non-cooperating same-UID filesystem mutation, out-of-process ptrace or code injection, and out-of-process access to the 0600 private HMAC key are outside the supported threat model","graphiti_call_count":0,"network_call_count":0,"private_key_publication_allowed":false,"raw_command_output_publication_allowed":false,"raw_private_locator_public_count":0,"vault_read_count":0,"whole_envelope_checker":"field-aware recursive checker before write and before stdout; repo paths use strict relative grammar; tool logical IDs and versions use role-specific ASCII grammar; only schema-enumerated fixed public system command locators and placeholders are allowed; all other absolute home file-URI Vault .obsidian control bidi and secret-bearing values are rejected"},"receipt_digest_profile":"SHA-256(ASCII(CLS/GOV01-STATIC-ENVELOPE-GENERATION-RECEIPT/v1) || NUL || raw-envelope-bytes); digest supplied by user and stored externally","repository_transition":{"approved_commit_shape":"current HEAD has exactly one parent equal to authorization_baseline_head; a path-local Merkle comparison of authenticated current and parent ancestor tree objects proves exactly the micro envelope regular file was added with bytes equal to the approved raw envelope and every non-target entry is byte-identical; no other path is added modified deleted renamed or type-changed","authorization_baseline_head":"efff5a5b803e84cf193c6b5dd67e7c947cb9f09d","authorization_baseline_head_ref_bytes":47,"authorization_baseline_head_ref_profile":"SHA-256(ASCII(CLS/GOV01-STATIC-ENVELOPE-HEAD-REF/v1) || NUL || exact symbolic HEAD ref ASCII bytes); raw ref is never serialized","authorization_baseline_head_ref_sha256":"c58034b19de75ff292906142ab44cd41a8b688b48862a63dd8c01f42040459d2","authorization_baseline_head_symbolic":true,"authorization_baseline_other_refs_bytes":3648,"authorization_baseline_other_refs_sha256":"56d06c459e4cff8a2a871f24b2b335f1739edee6126eb5a8f9be4ecb84016b3d","authorization_baseline_tree":"10df659d060c2c26b914cadea9b2e9233824d365","captured_index_root_profile":"strict captured DIRC v2 or v3 canonical bottom-up root-tree recomputation equal to authenticated HEAD; require the mode 160000 opaque-leaf path set to equal the exact public singleton _reference/obsidian-sample-plugin without opening requesting or dereferencing its object OID; reject a missing or mode-replaced singleton and every extra or substituted gitlink; in a parsed required-path ancestor tree permit that same singleton only as an unselected opaque sibling, and reject it if selected as a required terminal or ancestor","generation_output_preimage":"ABSENT","generation_output_repo_relative":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-pending-GOV01-GEN-20260822-b7c580f0b4d253b41448efc57582c1037fe30fa440d79d0ff7b602f7040c9d20.json","git_control_profile":{"alternate_object_controls_absent":true,"common_directory_relation":"git-directory-contained-under-common-worktrees","include_controls_absent":true,"marker_kind":"gitfile"},"index_must_equal_head":true,"issue_publication_checkpoint_profile":"capture one initial exact Git-source index-root and public-artifact checkpoint; while holding a nonblocking advisory lock on the exact shared control-parent directory FD, recapture an equal checkpoint immediately before micro-envelope O_EXCL and require both micro and generation-output preimages absent; after fsync and same-FD byte-exact reopen, require generation-output absence, recapture the same equal checkpoint, and require generation-output absence again before success","micro_envelope_preimage":"ABSENT","micro_envelope_repo_relative":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-envelope-generation-envelope-v1.GOV01-GEN-20260822-b7c580f0b4d253b41448efc57582c1037fe30fa440d79d0ff7b602f7040c9d20.json","refs_except_head_must_be_unchanged":true},"schema_binding":{"content_addressed_manual_checker_required":true,"external_draft202012_validation_required":true,"schema_artifact_path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-envelope-generation-envelope-v1.schema.json","schema_id":"urn:canvas-learning-system:gov-01:toolchain-static-envelope-generation-envelope:v1","schema_raw_file_sha256":"547633e952c77e1b850ca3c8874bc6704286169afa98f275475fac9b0130132a","whole_envelope_privacy_checker_required":true},"schema_version":"gov-01-toolchain-static-envelope-generation-envelope-v1","single_use":true,"state":"pending-user-confirmation","success_contract":{"acquisition_execution_authorized":false,"maximum_state":"ACQUISITION-ENVELOPE-FROZEN-PENDING-USER-CONFIRMATION","next_required_authority":"user must separately cite the exact final acquisition raw-envelope receipt digest and GOV01-SA challenge before verify or acquire; acquisition success still stops at static-attested-unexecuted","runtime_use_authorized":false,"stdout_fields":["state","artifact_path","raw_envelope_receipt_digest","generation_approval_challenge_id","approval_challenge_id","not_after_utc"]}}
./docs/security/prompt-injection-playbook.md:176:  `fr-kg-04-sidecar-and-mcp-hardening` (upcoming change) for the next
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-envelope-v2.schema.json:9:    "schema_version",
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-envelope-v2.schema.json:39:    "schema_version": {
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-envelope-v2.schema.json:308:        "private_preapproval_commitment_profile": { "const": "HMAC-SHA-256 with the authorized 32-byte private key over ASCII(CLS/GOV01/PRIVATE-PREAPPROVAL/v2) || NUL || uint64be(canonical-body-byte-length) || UTF-8-NFC-LF canonical JSON of exactly {schema_version,approval_challenge_id,census_at_utc,hmac_key_id,authorized_locator_commitments,private_control_identity_commitment,public_repo_artifact_set_receipt_sha256,git_snapshot_commitment,toolchain_set_receipt_sha256,package_lock_raw_sha256,host_platform,host_architecture,target_worktree_claude_sessions,forbidden_process_match_count,host_selected_package_count,host_selected_cache_bytes,host_bin_link_count,content_receipt_sha256,ustar_closure_sha256,resolution_receipt_sha256,expected_tree_sha256}; no envelope digest, receipt digest, generated timestamp, raw private locator, inode/device or command bytes are in this deterministic body" },
./_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-envelope-v2.schema.json:380:          "description": "SHA-256 over ASCII(CLS/GOV01/STATIC-ACQUISITION-DYNAMIC-CLOSURE/v2), one NUL byte, and UTF-8-NFC-LF sorted-key compact canonical JSON containing schema_version, exact flags [-I,-S,-B], observed Python version/implementation and the ordered nine observed toolchain entries. It is runtime self-attestation, not pre-exec assurance."
./_bmad/tea/workflows/testarch/ci/instructions.md:12:Scaffold a production-ready CI/CD quality pipeline with test execution, burn-in loops for flaky detection, parallel sharding, artifact collection, and notifications.
./docs/prd-phase3-phase4.md:156:*   **Data Management Stubs (Task 8):** Render a "Data Management" section with placeholder buttons for "Manual Backup" and "Rebuild Index". Clicking these must trigger toast notifications indicating future story implementation (`Story 1.8` and `Story 2.7` respectively) [cite: 1].
./docs/prd-phase3-phase4.md:266:3.  **Configuration Security:** API Keys entered into the system are masked via password inputs, trigger an explicit security notification, and successfully persist to the backend `SystemModelConfig` via `POST /api/v1/system/config` without console leakage [cite: 1].
./_bmad/tea/workflows/testarch/ci/checklist.md:187:7. [ ] Set up notifications (optional)
./_bmad-output/research/canvas-index-md-spec-v1.md:70:schema_version: v1
./_bmad-output/research/canvas-index-md-spec-v1.md:123:| `schema_version` | string | ✅ | 版本（当前 `v1`） |
./_bmad-output/research/2026-05-21-gap-audit-chatgpt-prompt.md:88:- Verification / topic_clustering / notification_channels
./_bmad-archive/brainstorming/brainstorming-session-S8-A4-indexing-pipeline-2026-03-13.md:179:| 2 | **HIGH** | SSEConnectionManager.broadcast() 是 stub（无法通知前端索引完成） | `notification_channels.py:370-396` |
./_bmad-archive/brainstorming/brainstorming-session-S8-A4-indexing-pipeline-2026-03-13.md:310:| 8 | HIGH | notification_channels.py:370 | SSEConnectionManager.broadcast() 是 stub | 中等 |
./_bmad-output/implementation-artifacts/epic-4/LITE-4-3.md:76:     "generated_at": "datetime"
./_bmad-output/implementation-artifacts/epic-4/LITE-4-3.md:129:  - [ ] `generate_question` 返回前 `INSERT INTO questions_registry` (含 question_id / session_id / node_id / question_text / context_used / generated_at)
./docs/deep-research/03-agent-teams/deep-research-docker-agent-teams.md:41:3.  **`VishalJ99/claude-docker`**: This image offers advanced developer ergonomics, including Twilio SMS notifications upon task completion, automatic conda environment mounting, and native GPU access [cite: 12, 13]. While highly functional for overnight autonomous development, it introduces unnecessary bloat for a pipeline that already orchestrates GPU passthrough via Docker Compose [cite: 12].
./_bmad/tea/workflows/testarch/ci/steps-c/step-03-configure-quality-gates.md:3:description: 'Configure burn-in, quality gates, and notifications'
./_bmad/tea/workflows/testarch/ci/steps-c/step-03-configure-quality-gates.md:12:Configure burn-in loops, quality thresholds, and notification hooks.
./_bmad/tea/workflows/testarch/ci/steps-c/step-03-configure-quality-gates.md:61:- Failure notifications (Slack/email)
./_bmad/tea/workflows/testarch/ci/steps-c/step-04-validate-and-summary.md:55:- Artifacts and notifications
./_bmad-output/research/round-23-chatgpt-dr-response-v3-multi-vault-2026-05-10.md:106:| `frontend/obsidian-plugin/src/configure-whiteboard.ts` 与 `canvas-vault/.canvas-config.yaml` | vault 配置 schema 为 `subject / subject_display / active_board / schema_version`，明显偏"单 subject per vault"。 | 多 vault 没问题，但"一个 vault 内多个 subject / 多来源 trust tier"无法表达。 | 配置 schema 升级为 `vault_id / subjects[] / trust_policies / indexing_policies`。 |
./_bmad-output/research/2026-05-21-chatgpt-adversarial-review.xml:3506:- Archive scheduler / notification
./_bmad-output/research/2026-05-21-chatgpt-adversarial-review.xml:6505: *   POST /api/v1/exam/quick  body: {node_id, vault_id?}   resp: {question_id, question_text, generated_at?}
./_bmad-output/research/2026-05-21-chatgpt-adversarial-review.xml:6570:    `generated_at: ${input.generatedAt ?? new Date().toISOString()}`,
./_bmad-output/research/2026-05-21-chatgpt-adversarial-review.xml:6728:      generated_at?: string;
./_bmad-output/research/2026-05-21-chatgpt-adversarial-review.xml:6743:      generatedAt: r.generated_at,
./_bmad-output/research/2026-05-21-chatgpt-adversarial-review.xml:7493:  schema_version?: string;
./_bmad-output/research/2026-05-21-chatgpt-adversarial-review.xml:7527:    schema_version: out.schema_version ?? undefined,
./_bmad-output/research/2026-05-21-chatgpt-adversarial-review.xml:8791:backend 返回的 JSON 结构是 `{question_id: uuid, question_text: str, generated_at: iso}`。
./_bmad-output/research/2026-05-21-chatgpt-adversarial-review.xml:8810:generated_at: {当前 ISO 8601 时间戳}
./_bmad-output/research/round-23-chatgpt-dr-response-v4-study-question-2026-05-10.md:87:**第一层是 Vault/内容层**。`.canvas-config.yaml` 定义了 `subject`、`subject_display`、`active_board` 与 `schema_version`，说明系统把 vault 当成课程级命名空间，而不是通用文件夹。
./_bmad-output/research/round-23-chatgpt-dr-response-v4-study-question-2026-05-10.md:211:    VAULT { string vault_id; string subject; string subject_display; string active_board; string schema_version }
./backend/openapi.json:22395:          "generated_at": {
./backend/openapi.json:22414:          "generated_at"
./backend/start-backend-hidden.vbs:22:' Optional: Show notification (comment out if not needed)
./_bmad-output/research/2026-05-14-mvp-alpha-parallel-dev-plan.md:146:   - 返回 {question_id: uuid, question_text: str, generated_at: iso}
./_bmad/tea/workflows/testarch/trace/steps-c/step-04-analyze-gaps.md:130:  generated_at: new Date().toISOString(),
./_bmad-output/implementation-artifacts/epic-2/2-7-concept-extraction-edge-inject.md:140:| 压缩通知 | unit | `pytest tests/unit/test_context_compression.py::test_notification -x` | 通知文本正确 |
./_bmad-output/research/2026-05-21-gap-audit-chatgpt-review.xml:101:P2 阶段先 stub, P7-P8 重写为干净版（去掉监控/cost-tracker/notification scope creep）。
./_bmad-output/research/2026-05-21-gap-audit-chatgpt-review.xml:181:from app.services.notification_channels import create_default_dispatcher  # noqa: E402
./_bmad-output/research/2026-05-21-gap-audit-chatgpt-review.xml:228:    notification_dispatcher = create_default_dispatcher()
./_bmad-output/research/2026-05-21-gap-audit-chatgpt-review.xml:231:        notification_dispatcher=notification_dispatcher,
./_bmad-output/research/2026-05-21-gap-audit-chatgpt-review.xml:810:- Archive scheduler / notification
./_bmad-output/research/2026-05-21-gap-audit-chatgpt-review.xml:10362: *   POST /api/v1/exam/quick  body: {node_id, vault_id?}   resp: {question_id, question_text, generated_at?}
./_bmad-output/research/2026-05-21-gap-audit-chatgpt-review.xml:10427:    `generated_at: ${input.generatedAt ?? new Date().toISOString()}`,
./_bmad-output/research/2026-05-21-gap-audit-chatgpt-review.xml:10585:      generated_at?: string;
./_bmad-output/research/2026-05-21-gap-audit-chatgpt-review.xml:10600:      generatedAt: r.generated_at,
./_bmad-output/research/2026-05-21-gap-audit-chatgpt-review.xml:12014:backend 返回的 JSON 结构是 `{question_id: uuid, question_text: str, generated_at: iso}`。
./_bmad-output/research/2026-05-21-gap-audit-chatgpt-review.xml:12033:generated_at: {当前 ISO 8601 时间戳}
./_bmad/bmm/workflows/document-project/documentation-requirements.csv:3:mobile,true,true,true,true,true,package.json;pubspec.yaml;Podfile;build.gradle;app.json;capacitor.config.*;ionic.config.json,src/;app/;screens/;components/;services/;models/;assets/;ios/;android/,*client.ts;*service.ts;*api.ts;fetch*.ts;axios*.ts;*http*.ts,*.test.ts;*.test.tsx;*_test.dart;*.test.dart;**/__tests__/**,.env*;config/*;app.json;capacitor.config.*;google-services.json;GoogleService-Info.plist,*auth*.ts;*session*.ts;*authenticat*;*permission*;*biometric*;secure-store*,migrations/**;realm/**;*.realm;watermelondb/**;sqlite/**,main.ts;index.ts;App.tsx;App.ts;main.dart,shared/**;common/**;utils/**;lib/**;components/shared/**;@*/**,pnpm-workspace.yaml;lerna.json;nx.json;turbo.json,*event*.ts;*notification*.ts;*push*.ts;background-fetch*,fastlane/**;.github/workflows/**;.gitlab-ci.yml;bitbucket-pipelines.yml;appcenter-*,assets/**;Resources/**;res/**;*.xcassets;drawable*/;mipmap*/;images/**,N/A,*.proto;graphql/**;*.graphql,i18n/**;locales/**;translations/**;*.strings;*.xml,false,true
./_bmad-output/research/round-23-multi-vault-implementation-plan-2026-05-10.md:115:schema_version: "1.0-flat-architecture-2026-04-20"
./_bmad-output/research/round-23-multi-vault-implementation-plan-2026-05-10.md:194:schema_version: "2.0-multi-vault-2026-05-10"
./_bmad-output/research/round-23-multi-vault-implementation-plan-2026-05-10.md:224:            schema_version: '2.0-multi-vault-2026-05-10',
./docs/deep-research/04-tdd-workflow/deep-research-tdd-workflow-community.md:90:Furthermore, asynchronous agent workflows necessitate robust notification systems. The **Tmux Notification System** (`mcpmarket.com/tools/skills/tmux-notification-system`) bridges the gap between CLI tools and the macOS UI [cite: 30]. It utilizes macOS `LaunchAgents` to create a background webhook service. When an agent in a background `tmux` pane completes a task, hits an API limit, or requires human intervention (a 'Stop' event), the system triggers a native macOS notification [cite: 30]. Clicking the notification automatically routes the developer back to the specific `tmux` pane where the agent is waiting, dramatically reducing downtime in multi-agent workflows [cite: 30].
./docs/deep-research/04-tdd-workflow/deep-research-tdd-workflow-community.md:146:6.  **Stateless Reset:** Upon successful completion, native macOS notifications alert the human developer [cite: 30]. The agent's context is wiped, the `progress.txt` is updated, and the loop restarts, guaranteeing zero context rot [cite: 3, 39].
./_bmad-output/research/round-23-chatgpt-dr-prompt-2026-05-09.md:752:- `canvas-vault/.canvas-config.yaml` — 当前 schema (subject / subject_display / active_board / schema_version / deprecated_paths)
./_bmad-output/implementation-artifacts/epic-5a-graphiti-runtime/5-ge-1-canvas-graph-episode-v1.md:34:       schema_version: Literal["CanvasGraphEpisodeV1"] = "CanvasGraphEpisodeV1"
./_bmad-output/验收单/Story-CARD-A2-复习到期口径统一.md:57:| 2 | payload schema v2→v3 纯加性：既有字段一个未改名未删（推送链 daily_review_run.py / send_bark.py 只读 notification，被动兼容），新增 due_nodes 明细 + ineligible 分桶 | ✅ 加性守卫测试锁定 |
./_bmad-output/验收单/Story-CARD-A2-复习到期口径统一.md:58:| 3 | 数字与明细自洽：stats.due_nodes 直接由 due_nodes 明细长度派生，靠构造保证不再漂移；三个分桶长度==stats 计数逐一断言 | ✅ len==stats 断言过 |
./_bmad-output/验收单/Story-CARD-A2-复习到期口径统一.md:59:| 4 | Dashboard 独立重算已删除：`grep -c "schedCnt\|newCnt" canvas-vault/Dashboard.md` == 0；`grep -c "今日复习.json"` == 5 | ✅ 0 / 5 |
./_bmad-output/验收单/Story-CARD-A2-复习到期口径统一.md:60:| 5 | 真实 vault 冒烟：worktree 副本跑生成脚本，schema_version=3、due=2 与明细一致、占位积压 1 张点名、测试节点 4 张单独成桶 | ✅ 自洽 True |
./_bmad-output/验收单/Story-CARD-A2-复习到期口径统一.md:145:  - `scripts/daily_review_pick.py`（schema v3：due_nodes 明细 + ineligible 分桶，scan_nodes 三桶点名）
./_bmad-output/验收单/Story-CARD-A2-复习到期口径统一.md:152:  - 判据 (3) 5 类分歧测试 → test_daily_review_pick.py:test_projection_v3_due_nodes_and_ineligible_buckets
./backend/app/services/board_manifest_service.py:725:            "generated_at": now.isoformat(),
./backend/app/services/board_manifest_service.py:959:                    prev_version = prev.get("snapshot_schema_version")
./backend/app/services/board_manifest_service.py:1054:    version = data.get("snapshot_schema_version")
./backend/app/services/board_manifest_service.py:1109:        gen_at = _aware_dt(snap.get("freshness", {}).get("generated_at"))
./_bmad/bmm/workflows/3-solutioning/create-architecture/data/domain-complexity.csv:5:social,"social network,community,users,friends,posts,sharing",high,advanced,"social graph algorithms, feed ranking, notification systems, privacy"
./_bmad/bmm/workflows/3-solutioning/create-architecture/data/domain-complexity.csv:7:productivity,"productivity,workflow,tasks,management,business,tools",medium,standard,"collaboration patterns, real-time editing, notification systems, integration"
./backend/tests/regression/test_snapshot_schema_migration_contract.py:23:  3. 新写快照必带 snapshot_schema_version 且不含禁项
./backend/tests/regression/test_snapshot_schema_migration_contract.py:69:        # 刻意不写 snapshot_schema_version —— 这正是 v1 的识别特征
./backend/tests/regression/test_snapshot_schema_migration_contract.py:71:            "generated_at": "2026-08-01T00:00:00+00:00",
./backend/tests/regression/test_snapshot_schema_migration_contract.py:175:    v2["snapshot_schema_version"] = 2
./backend/tests/regression/test_snapshot_schema_migration_contract.py:190:    assert loaded.get("snapshot_schema_version") == svc.SNAPSHOT_SCHEMA_VERSION
./backend/tests/regression/test_snapshot_schema_migration_contract.py:222:    assert data["snapshot_schema_version"] == svc.SNAPSHOT_SCHEMA_VERSION
./backend/tests/regression/test_snapshot_schema_migration_contract.py:232:    assert projected["snapshot_schema_version"] == svc.SNAPSHOT_SCHEMA_VERSION
./backend/tests/regression/test_snapshot_schema_migration_contract.py:233:    assert "snapshot_schema_version" not in full, "投影把版本字段写回了 live state"
./backend/app/graphiti/canvas_episode.py:214:    schema_version: Literal["CanvasGraphEpisodeV1"] = "CanvasGraphEpisodeV1"
./backend/app/main.py:68:from app.services.notification_channels import create_default_dispatcher  # noqa: E402
./backend/app/main.py:124:    notification_dispatcher = create_default_dispatcher()
./backend/app/main.py:127:        notification_dispatcher=notification_dispatcher,
./_bmad/bmm/workflows/2-plan-workflows/create-prd/data/prd-purpose.md:83:- ❌ "The system shall provide notifications"
./_bmad/bmm/workflows/2-plan-workflows/create-prd/data/prd-purpose.md:84:- ✅ "The system shall send email notifications within 30 seconds of trigger event"
./_bmad/bmm/workflows/2-plan-workflows/create-prd/data/project-types.csv:3:mobile_app,"iOS,Android,app,mobile,iPhone,iPad","Native or cross-platform?;Offline needed?;Push notifications?;Device features?;Store compliance?","platform_reqs;device_permissions;offline_mode;push_strategy;store_compliance","desktop_features;cli_commands","app store guidelines;platform requirements","Gesture innovation;AR/VR features"
./backend/tests/regression/test_snapshot_v3_contract.py:83:    assert data["snapshot_schema_version"] == 3
./backend/tests/regression/test_snapshot_v3_contract.py:142:    data["snapshot_schema_version"] = 999
./backend/tests/regression/test_snapshot_v3_contract.py:147:    data["snapshot_schema_version"] = "3"
./backend/tests/regression/test_snapshot_v3_contract.py:152:    data["freshness"] = {"generated_at": "2026-08-19T00:00:00+00:00", "generation": 12345}
./backend/tests/regression/test_snapshot_v3_contract.py:187:    _put_snapshot(vault, {"snapshot_schema_version": "3", "junk": True})
./backend/tests/regression/test_snapshot_v3_contract.py:194:    assert data["snapshot_schema_version"] == 3
./backend/tests/regression/test_snapshot_v3_contract.py:272:        ("v999", {**good, "snapshot_schema_version": 999}),
./backend/tests/regression/test_snapshot_v3_contract.py:279:        assert on_disk["snapshot_schema_version"] == 3, f"{tamper_name}: 版本未被自愈"
./backend/tests/regression/test_snapshot_v3_contract.py:295:    assert on_disk["snapshot_schema_version"] == 3, "坏根快照应被合法 v3 覆盖"
./backend/tests/regression/test_snapshot_v3_contract.py:325:    c["freshness"]["generated_at"] = "not-a-time"
./backend/tests/regression/test_snapshot_v3_contract.py:379:    """V3: {"snapshot_schema_version":3,"freshness":[]} 曾在 :956 抛 AttributeError
./backend/tests/regression/test_snapshot_v3_contract.py:382:    _put_snapshot(vault, {"snapshot_schema_version": 3, "freshness": []})
./backend/tests/regression/test_snapshot_v3_contract.py:447:            generated_at="2026-08-20T00:00:00+00:00",
./backend/tests/regression/test_daily_review_pick.py:31:    return picker.build_payload(vault, NOW, blr or {}, picker.load_decay(vault))
./backend/tests/regression/test_daily_review_pick.py:57:def test_placeholder_node_skipped_empty_notification(tmp_path):
./backend/tests/regression/test_daily_review_pick.py:65:    assert ranked == [] and payload["notification"] is None
./backend/tests/regression/test_daily_review_pick.py:100:def test_future_due_board_gets_rest_notification(tmp_path):
./backend/tests/regression/test_daily_review_pick.py:109:    noti = payload["notification"]
./backend/tests/regression/test_daily_review_pick.py:111:    assert payload["upcoming"][0]["board"] == "普通板"
./backend/tests/regression/test_daily_review_pick.py:130:    assert ranked[0]["pending"] == 1 and payload["stats"]["due_nodes"] == 1
./backend/tests/regression/test_daily_review_pick.py:133:def test_unassigned_nodes_named_in_md(tmp_path):
./backend/tests/regression/test_daily_review_pick.py:142:    assert payload["unassigned_nodes"] == ["孤儿"]
./backend/tests/regression/test_daily_review_pick.py:147:# daily_review_pick 为到期口径唯一裁判: Dashboard 消费 due_nodes 明细与
./backend/tests/regression/test_daily_review_pick.py:151:def test_projection_v3_due_nodes_and_ineligible_buckets(tmp_path):
./backend/tests/regression/test_daily_review_pick.py:156:    ③ 无 source_board → 不计入 due_nodes, 点名在 unassigned_nodes
./backend/tests/regression/test_daily_review_pick.py:158:    ⑤ 脏 fsrs_due (带时区偏移) → fail-open 视同到期, 进 due_nodes
./backend/tests/regression/test_daily_review_pick.py:178:    assert payload["schema_version"] == 3
./backend/tests/regression/test_daily_review_pick.py:179:    assert {d["node"] for d in payload["due_nodes"]} == {"无type", "脏due", "规范到期", "边界到期"}
./backend/tests/regression/test_daily_review_pick.py:180:    assert len(payload["due_nodes"]) == payload["stats"]["due_nodes"]
./backend/tests/regression/test_daily_review_pick.py:181:    for row in payload["due_nodes"]:
./backend/tests/regression/test_daily_review_pick.py:183:    rows = {d["node"]: d for d in payload["due_nodes"]}
./backend/tests/regression/test_daily_review_pick.py:196:    assert payload["unassigned_nodes"] == ["孤儿"]
./backend/tests/regression/test_daily_review_pick.py:201:    send_bark 只读 notification, 但全字段名保留是加性承诺的下界)。"""
./backend/tests/regression/test_daily_review_pick.py:203:    for key in ("unassigned_nodes", "date", "generated_at", "top_boards",
./backend/tests/regression/test_daily_review_pick.py:204:                "upcoming", "due_nodes", "ineligible", "stats", "notification"):
./backend/tests/regression/test_daily_review_pick.py:207:                "corrupt", "unassigned", "due_nodes", "future_nodes"):
./backend/tests/regression/test_daily_review_pick.py:209:    assert payload["notification"]["id"] == f"canvas-review-{payload['date']}"
./backend/tests/regression/test_daily_review_pick.py:216:    assert ranked == [] and payload["due_nodes"] == []
./backend/tests/regression/test_daily_review_pick.py:219:    assert payload["notification"] is None
./backend/app/core/unified_learning_event.py:212:        schema_version: For forward-compatible migration
./backend/app/core/unified_learning_event.py:256:    schema_version: int = Field(
./backend/app/core/unified_learning_event.py:295:      3. Forward compatibility via schema_version field
./backend/app/core/unified_learning_event.py:298:    schema_version: int = Field(default=1, description="Payload schema version")
./backend/app/core/unified_learning_event.py:324:        schema_version=event.schema_version,
./backend/app/core/unified_learning_event.py:814:    """Check if an episode_body is in the new JSON format (schema_version present)."""
./backend/app/core/unified_learning_event.py:821:        return "schema_version" in data
./backend/app/models/snapshot_v3.py:227:    generated_at: str = Field(min_length=1, max_length=64)
./backend/app/models/snapshot_v3.py:235:    _t = field_validator("generated_at")(classmethod(lambda cls, v: _require_iso_or_none(v)))
./backend/app/models/snapshot_v3.py:244:    snapshot_schema_version: Literal[3]
./backend/app/models/snapshot_v3.py:270:    @field_validator("snapshot_schema_version", mode="before")
./backend/app/models/snapshot_v3.py:276:            raise ValueError(f"snapshot_schema_version 必须是 int {SNAPSHOT_V3_VERSION}, got {v!r}")
./backend/app/models/snapshot_v3.py:331:            "snapshot_schema_version": self.snapshot_schema_version,
./backend/app/models/snapshot_v3.py:481:            "snapshot_schema_version": SNAPSHOT_V3_VERSION,
./backend/app/models/snapshot_v3.py:484:                "generated_at": str((full.get("freshness") or {}).get("generated_at") or "")[:64],
./backend/app/config.py:769:        1. .canvas-config.yaml `vault_id` field (explicit, schema_version >= 2.0)
./backend/app/api/v1/endpoints/exam_quick.py:6:# 输出: {question_id, question_text, tip_count, tips_used, generated_at}
./backend/app/api/v1/endpoints/exam_quick.py:80:    generated_at: str = Field(..., description="生成时间 ISO 8601")
./backend/app/api/v1/endpoints/exam_quick.py:124:    generated_at = datetime.now(timezone.utc).isoformat()
./backend/app/api/v1/endpoints/exam_quick.py:132:        "generated_at": generated_at,
./backend/app/api/v1/endpoints/exam_quick.py:146:        generated_at=generated_at,
./backend/app/services/notification_channels.py:11:- Obsidian SSE notifications
./backend/app/services/notification_channels.py:37:    """Abstract base class for notification channels.
./backend/app/services/notification_channels.py:41:    All notification channels must implement the send() method.
./backend/app/services/notification_channels.py:46:        """Send notification for an alert event.
./backend/app/services/notification_channels.py:53:            bool: True if notification was sent successfully
./backend/app/services/notification_channels.py:65:    """Console logging notification channel.
./backend/app/services/notification_channels.py:76:        """Send notification via structlog.
./backend/app/services/notification_channels.py:107:    """File logging notification channel.
./backend/app/services/notification_channels.py:120:        """Initialize file notification channel.
./backend/app/services/notification_channels.py:129:        """Write notification to log file.
./backend/app/services/notification_channels.py:150:                "file_notification.failed",
./backend/app/services/notification_channels.py:164:    """Obsidian plugin SSE notification channel.
./backend/app/services/notification_channels.py:176:        """Initialize Obsidian notification channel.
./backend/app/services/notification_channels.py:184:        """Send notification via SSE broadcast.
./backend/app/services/notification_channels.py:195:                "obsidian_notification.skipped",
./backend/app/services/notification_channels.py:210:                "obsidian_notification.failed",
./backend/app/services/notification_channels.py:224:    """Webhook notification channel.
./backend/app/services/notification_channels.py:234:        """Initialize webhook notification channel.
./backend/app/services/notification_channels.py:244:        """Send notification via HTTP POST.
./backend/app/services/notification_channels.py:268:            logger.error("webhook_notification.httpx_not_installed")
./backend/app/services/notification_channels.py:272:                "webhook_notification.failed",
./backend/app/services/notification_channels.py:288:    Routes alert events to all configured notification channels.
./backend/app/services/notification_channels.py:303:        """Initialize notification dispatcher.
./backend/app/services/notification_channels.py:306:            channels: List of notification channels to dispatch to
./backend/app/services/notification_channels.py:325:                    "notification_dispatch.failed",
./backend/app/services/notification_channels.py:342:    """Create notification dispatcher with default channels.
./backend/app/services/notification_channels.py:352:        sse_manager: Optional SSE connection manager for Obsidian notifications
./backend/app/services/notification_channels.py:353:        log_path: Path for file notifications
./backend/app/services/notification_channels.py:367:        "notification_dispatcher.created",
./backend/app/models/schemas.py:665:    generated_at: datetime = Field(..., description="Generation timestamp")
./docs/test-artifacts/atdd-checklist-38.4.md:98:| `app.main.create_default_dispatcher` | `patch` | Skip notification setup |
./backend/app/models/board_manifest.py:132:    generated_at: str
./_bmad/bmm/workflows/2-plan-workflows/create-prd/steps-c/step-04-journeys.md:116:- Connect journey needs to concrete capabilities (onboarding, dashboards, notifications, etc.)
./backend/app/domains/infra/gateway.py:10:       error_aggregator, notification_channels, prompt_registry,
./backend/app/domains/infra/gateway.py:47:from app.services.notification_channels import create_default_dispatcher
./backend/app/api/v1/endpoints/agents.py:1749:            generated_at=datetime.now(),
./_bmad-output/验收单/Story-MVP-α-end-to-end-learning-loop.md:142:| 7 | 接口签名跟 Session B plugin 期望对齐 (question_id / question_text / tip_count / tips_used / generated_at) | ✅ |
./backend/app/services/agent_service.py:5383:            Dict with questions list, concept, generated_at, and created_nodes
./backend/app/services/agent_service.py:5511:                "generated_at": datetime.now().isoformat(),
./backend/app/services/review_service.py:740:            "generated_at": datetime.now(timezone.utc).isoformat(),
./backend/app/services/review_service.py:1671:        RETURN review, r.mode, r.generated_at
./backend/app/services/review_service.py:1672:        ORDER BY r.generated_at DESC
./backend/tests/test_alert_manager.py:29:from app.services.notification_channels import NotificationDispatcher
./backend/tests/test_alert_manager.py:65:def mock_notification_dispatcher() -> MagicMock:
./backend/tests/test_alert_manager.py:66:    """Create a mock notification dispatcher."""
./backend/tests/test_alert_manager.py:75:    mock_notification_dispatcher: MagicMock,
./backend/tests/test_alert_manager.py:80:        notification_dispatcher=mock_notification_dispatcher,
./backend/tests/test_alert_manager.py:212:        mock_notification_dispatcher: MagicMock,
./backend/tests/test_alert_manager.py:219:            notification_dispatcher=mock_notification_dispatcher,
./backend/tests/test_alert_manager.py:361:    """Tests for alert notification dispatch."""
./backend/tests/test_alert_manager.py:364:    async def test_notification_dispatcher_called(
./backend/tests/test_alert_manager.py:367:        mock_notification_dispatcher: MagicMock,
./backend/tests/test_alert_manager.py:369:        """Test notification dispatcher can be called."""
./backend/tests/test_alert_manager.py:385:        # Dispatch notification
./backend/tests/test_alert_manager.py:386:        await alert_manager.notification_dispatcher.dispatch(alert, "fired")
./backend/tests/test_alert_manager.py:389:        mock_notification_dispatcher.dispatch.assert_called_once()
./backend/tests/test_alert_manager.py:390:        call_args = mock_notification_dispatcher.dispatch.call_args
./backend/app/services/alert_manager.py:11:- Alert notification dispatch
./backend/app/services/alert_manager.py:32:    from .notification_channels import NotificationDispatcher
./backend/app/services/alert_manager.py:65:    - FIRING: Alert triggered, notifications sent
./backend/app/services/alert_manager.py:177:        notification_dispatcher: "NotificationDispatcher",
./backend/app/services/alert_manager.py:184:            notification_dispatcher: Dispatcher for sending notifications
./backend/app/services/alert_manager.py:188:        self.notification_dispatcher = notification_dispatcher
./backend/app/services/alert_manager.py:437:        """Fire an alert and send notifications.
./backend/app/services/alert_manager.py:453:        await self.notification_dispatcher.dispatch(alert, "fired")
./backend/app/services/alert_manager.py:456:        """Resolve an alert and send notifications.
./backend/app/services/alert_manager.py:469:        await self.notification_dispatcher.dispatch(alert, "resolved")
./tests/bdd/test_three_layer_memory_agentic_rag.py:870:def verify_review_notification(count, memory_context):
./backend/tests/unit/test_vault_switch.py:152:            'vault_id: "explicit_yaml_id"\nsubject: math\nschema_version: "2.0-multi-vault-2026-05-10"\n',
./backend/tests/unit/test_vault_switch.py:187:            'subject: cs-61b\nschema_version: "1.0-flat-architecture-2026-04-20"\n',
./backend/tests/unit/test_vault_switch.py:205:            'vault_id: "数学101"\nsubject: math\nschema_version: "2.0-multi-vault-2026-05-10"\n',
./backend/tests/test_notification_channels.py:5:Unit tests for notification channels.
./backend/tests/test_notification_channels.py:23:from app.services.notification_channels import (
./backend/tests/test_notification_channels.py:87:    """Tests for console notification channel."""
./backend/tests/test_notification_channels.py:94:        with patch("app.services.notification_channels.logger") as mock_logger:
./backend/tests/test_notification_channels.py:105:        with patch("app.services.notification_channels.logger") as mock_logger:
./backend/tests/test_notification_channels.py:128:    """Tests for file notification channel."""
./backend/tests/test_notification_channels.py:193:            with patch("app.services.notification_channels.logger") as mock_logger:
./backend/tests/test_notification_channels.py:207:    """Tests for Obsidian SSE notification channel."""
./backend/tests/test_notification_channels.py:244:        with patch("app.services.notification_channels.logger"):
./backend/tests/test_notification_channels.py:256:    """Tests for webhook notification channel."""
./backend/tests/test_notification_channels.py:300:            with patch("app.services.notification_channels.logger"):
./backend/tests/test_notification_channels.py:313:            with patch("app.services.notification_channels.logger"):
./backend/tests/test_notification_channels.py:325:    """Tests for notification dispatcher routing."""
./backend/tests/test_notification_channels.py:354:        with patch("app.services.notification_channels.logger"):
./backend/tests/unit/test_review_mode_support.py:194:        assert "generated_at" in result
./backend/tests/unit/test_canvas_episode_v1.py:79:    assert ep.schema_version == "CanvasGraphEpisodeV1"
./docs/stories/8.14.story.md:325:    error_notification: true
./docs/stories/9-5-session-monitor.story.md:74:                'enable_notifications': True,
./docs/stories/9-5-session-monitor.story.md:300:        if not self.config['monitoring']['enable_notifications']:
./docs/stories/9-5-session-monitor.story.md:693:  - Created alert notification system
./docs/stories/24.2.story.md:237:           r.generated_at AS date,
./docs/stories/24.2.story.md:242:    ORDER BY r.generated_at DESC
./docs/stories/8.8.story.md:146:    "generated_at": "2025-01-22T16:00:00Z",
./docs/stories/story-9.10.2-cli-deep-integration.md:101:   - Command status updates and progress notifications
./docs/stories/11.5.story.md:38:  - [x] Subtask 1.8: 实现schema版本管理表（`schema_version`）和迁移机制
./docs/stories/11.5.story.md:78:  - [x] Subtask 7.1: 创建`schema_version`表记录当前schema版本
./docs/stories/11.5.story.md:79:  - [x] Subtask 7.2: 实现`_get_current_schema_version()`方法
./docs/stories/11.5.story.md:220:CREATE TABLE schema_version (
./docs/stories/11.5.story.md:293:        """创建数据库schema（4个核心表 + schema_version表）"""
./docs/stories/11.5.story.md:296:    def _get_current_schema_version(self) -> int:
./docs/stories/11.5.story.md:897:   - Schema版本管理表: schema_version
./docs/stories/11.5.story.md:934:   - _get_current_schema_version(): 获取当前版本
./docs/stories/11.5.story.md:1048:- [x] Created 4 core tables + schema_version table
./docs/stories/story-9.8.2-review-dashboard-component.md:60:   - Show upcoming review schedule with calendar view
./docs/stories/31.7.story.md:322:- ✅ `Notice` → Verified for user notifications
./docs/stories/story-9.10.1-review-decision-engine.md:76:   - WebSocket-based review reminders and notifications
./docs/stories/story-9.10.1-review-decision-engine.md:78:   - Support for mobile-friendly review notifications
./docs/stories/story-9.10.1-review-decision-engine.md:123:   - Real-time notifications should arrive within 500ms
./docs/stories/story-9.10.1-review-decision-engine.md:223:   - Mobile-friendly notifications sent
./docs/stories/story-9.10.1-review-decision-engine.md:245:4. Create notification system
./docs/stories/story-9.10.1-review-decision-engine.md:266:- ✅ Performance requirements met (2s decision generation, 500ms notifications)
./docs/stories/story-9.10.1-review-decision-engine.md:300:- WebSocket server for real-time notifications
./docs/stories/story-9.10.1-review-decision-engine.md:302:- Mobile notification service for cross-device reminders
./docs/stories/1.10.story.md:649:  - **How**: Added inline comment noting this is forward-looking documentation and the class will be implemented in upcoming stories.
./docs/stories/31.6.story.md:393:- ✅ `Notice` class → For user notifications
./docs/stories/9.5.story.md:190:  upcomingReviews: ReviewTask[];
./docs/stories/9.5.story.md:339:      upcomingReviews: reviewPriorities.filter(p => p.urgency === 'scheduled'),
./docs/stories/9.5.story.md:668:  const { todayReviews, urgentReviews, upcomingReviews, reviewTimeline } = reviewReminders || {};
./docs/stories/story-9.8.2-completion-summary.md:290:- **Notification System**: Push notifications for review reminders
./docs/stories/story-9.8.2-completion-summary.md:380:- Integration with upcoming Epic 9 features
./docs/stories/24.4.story.md:277:    RETURN review, r.mode, r.generated_at
./docs/stories/24.4.story.md:278:    ORDER BY r.generated_at DESC
./docs/stories/24.4.story.md:286:           r.generated_at AS date,
./docs/stories/24.4.story.md:290:    ORDER BY r.generated_at DESC
./docs/stories/24.4.story.md:484:ORDER BY r.generated_at DESC
./docs/stories/1.7.story.md:748:- No blocking operations without user notification
./docs/architecture/backend-deps.svg:4138:<!-- app_services_notification_channels -->
./docs/architecture/backend-deps.svg:4140:<title>app_services_notification_channels</title><style>.edge>path:hover{stroke-width:8}</style>
./docs/architecture/backend-deps.svg:4144:<text xml:space="preserve" text-anchor="middle" x="13911.21" y="-2196.15" font-family="Helvetica,sans-Serif" font-size="10.00" fill="white">notification_channels</text>
./docs/architecture/backend-deps.svg:4795:<!-- app_services_notification_channels&#45;&gt;app_main -->
./docs/architecture/backend-deps.svg:4797:<title>app_services_notification_channels&#45;&gt;app_main</title><style>.edge>path:hover{stroke-width:8}</style>
./docs/architecture/backend-deps.svg:4801:<!-- app_services_notification_channels&#45;&gt;app_services_alert_manager -->
./docs/architecture/backend-deps.svg:4803:<title>app_services_notification_channels&#45;&gt;app_services_alert_manager</title><style>.edge>path:hover{stroke-width:8}</style>
./docs/architecture/backend-deps.svg:5903:<!-- httpx&#45;&gt;app_services_notification_channels -->
./docs/architecture/backend-deps.svg:5905:<title>httpx&#45;&gt;app_services_notification_channels</title><style>.edge>path:hover{stroke-width:8}</style>
./docs/architecture/backend-deps.svg:7098:<!-- structlog&#45;&gt;app_services_notification_channels -->
./docs/architecture/backend-deps.svg:7100:<title>structlog&#45;&gt;app_services_notification_channels</title><style>.edge>path:hover{stroke-width:8}</style>
./docs/stories/35.5.story.md:315:5. **Task 4**: Success notification implemented in modal showing thumbnail preview. Notice displays media type and "上传成功" message.
./docs/stories/story-9.10.3-review-visualization-interface.md:82:   - Push notifications for timely reminders
./docs/stories/story-9.10.3-review-visualization-interface.md:350:- ✅ Real-time updates and notifications working
./docs/stories/story-9.10.3-review-visualization-interface.md:356:- ✅ Calendar sync and notification systems
./docs/stories/story-9.10.3-review-visualization-interface.md:394:- Push notification service
./docs/stories/story-9.8.6.6-global-error-handling.story.md:297:  notifications: {
./docs/stories/story-9.8.6.6-global-error-handling.story.md:338:    this.errorNotifier = new ErrorNotifier(this.config.notifications);
./docs/stories/story-12.G.5-frontend-error-display.md:95:| `src/errors/error-notification-map.ts` | 新建 | 错误码映射表 |
./docs/stories/story-12.G.5-frontend-error-display.md:105:// src/errors/error-notification-map.ts
./docs/stories/story-12.G.5-frontend-error-display.md:149:import { ERROR_NOTIFICATION_MAP, NotificationLevel } from './error-notification-map';
./docs/stories/story-12.G.5-frontend-error-display.md:440:| AC2 | 实现错误码映射 | ✅ PASS | `error-notification-map.ts` 实现1xxx-5xxx错误码，NotificationLevel枚举 |
./docs/stories/story-12.G.5-frontend-error-display.md:459:| `src/errors/error-notification-map.ts` | 170 | 新建 | ✅ |
./docs/stories/story-12.A.6-complete-agents.md:167:    generated_at: datetime
./docs/stories/17.3.story.md:56:  - [ ] 创建 `backend/app/services/notification_channels.py`
./docs/stories/17.3.story.md:71:  - [ ] 创建 `tests/unit/test_notification_channels.py`
./docs/stories/17.3.story.md:104:- [ ] FastAPI BackgroundTasks for async notification → Context7: /fastapi/fastapi
./docs/stories/17.3.story.md:106:- [ ] SSE EventSourceResponse for Obsidian notification → ADR-006
./docs/stories/17.3.story.md:286:        notification_dispatcher: "NotificationDispatcher",
./docs/stories/17.3.story.md:290:        self.notification_dispatcher = notification_dispatcher
./docs/stories/17.3.story.md:470:        await self.notification_dispatcher.dispatch(alert, "fired")
./docs/stories/17.3.story.md:480:        await self.notification_dispatcher.dispatch(alert, "resolved")
./docs/stories/17.3.story.md:500:# backend/app/services/notification_channels.py
./docs/stories/17.3.story.md:569:            logger.error("file_notification.failed", error=str(e))
./docs/stories/17.3.story.md:592:            logger.error("obsidian_notification.failed", error=str(e))
./docs/stories/17.3.story.md:611:                    "notification_dispatch.failed",
./docs/stories/17.3.story.md:774:- 新增: `backend/app/services/notification_channels.py`
./docs/stories/17.3.story.md:780:- 新增: `tests/unit/test_notification_channels.py`
./docs/stories/9.8.story.md:619:  const [notifications, setNotifications] = useState<Notification[]>([]);
./docs/stories/9.8.story.md:627:      const notification: Notification = {
./docs/stories/9.8.story.md:638:      setNotifications(prev => [notification, ...prev.slice(0, maxNotifications - 1)]);
./docs/stories/9.8.story.md:662:    RealtimeService.subscribe('notification', handleRealtimeNotification);
./docs/stories/9.8.story.md:666:      RealtimeService.unsubscribe('notification');
./docs/stories/9.8.story.md:672:    const sortedNotifications = notifications
./docs/stories/9.8.story.md:685:  }, [notifications, maxNotifications, settings]);
./docs/stories/9.8.story.md:687:  const handleNotificationAction = useCallback((notificationId: string, action: () => void) => {
./docs/stories/9.8.story.md:689:    markAsRead(notificationId);
./docs/stories/9.8.story.md:692:  const markAsRead = useCallback((notificationId: string) => {
./docs/stories/9.8.story.md:695:        n.id === notificationId ? { ...n, read: true } : n
./docs/stories/9.8.story.md:712:    <div className={`notification-center notification-${position}`}>
./docs/stories/9.8.story.md:713:      <div className="notification-list">
./docs/stories/9.8.story.md:714:        {visibleNotifications.map(notification => (
./docs/stories/9.8.story.md:716:            key={notification.id}
./docs/stories/9.8.story.md:717:            notification={notification}
./docs/stories/9.8.story.md:719:            onClose={() => markAsRead(notification.id)}
./docs/stories/9.8.story.md:724:      <div className="notification-controls">
./docs/stories/9.8.story.md:725:        <Badge count={notifications.filter(n => !n.read).length}>
./docs/stories/9.8.story.md:949:- ✅ **类型定义完整：** websocket.ts、datasync.ts、notifications.ts
./docs/stories/9.8.story.md:960:- `src/types/notifications.ts` - 通知系统相关类型定义
./docs/stories/8.12.story.md:404:    notification_channels: ["console", "log"]
./docs/stories/8.18.story.md:329:    "system_alerts_and_notifications": {
./docs/stories/8.18.story.md:352:      "notification_channels": {
./docs/stories/8.18.story.md:353:        "console_notifications": "enabled",
./docs/stories/8.18.story.md:354:        "log_file_notifications": "enabled",
./docs/stories/8.18.story.md:355:        "email_notifications": "disabled",
./docs/stories/8.18.story.md:356:        "slack_notifications": "disabled"
./docs/stories/8.18.story.md:686:    notification_channels:
./docs/stories/story-12.H.3-task-queue-modal.md:659:| ADR-009 | Error Handling & Retry Strategy | ✅ Cancel notification via Notice (INFO level), ApiClient handles user-cancel without retry |
./docs/stories/story-14.7.story.md:36:- localStorage for last notification timestamp
./docs/stories/story-14.7.story.md:97:const LAST_NOTIFICATION_KEY = 'canvas-review-last-notification';
./docs/stories/24.1.story.md:255:        properties={"mode": mode, "generated_at": datetime.utcnow().isoformat()}
./docs/stories/6.5.story.md:368:            "generated_at": datetime.now(),
./docs/stories/6.5.story.md:533:            "generated_at": datetime.now()
./docs/stories/15.5.story.md:123:def write_notification(email: str, message=""):
./docs/stories/15.5.story.md:125:        content = f"notification for {email}: {message}"
./docs/stories/15.5.story.md:128:@app.post("/send-notification/{email}")
./docs/stories/15.5.story.md:129:async def send_notification(email: str, background_tasks: BackgroundTasks):
./docs/stories/15.5.story.md:130:    background_tasks.add_task(write_notification, email, message="some notification")
./docs/stories/10.5.error-handling-and-recovery-system.md:163:    user_notification: Optional[str] = None
./docs/stories/11.1.story.md:517:- ✅ **Observer Pattern**: callback list pattern for change notifications
./docs/stories/1.4.story.md:1184:**Recommendation**: Mark story as DONE. This work sets an excellent standard for upcoming Layer 2 and Layer 3 implementations.
./docs/stories/6.3.story.md:344:            "generated_at": datetime.now().isoformat()
./docs/stories/6.3.story.md:1178:        assert "generated_at" in dashboard

**Extracting runner/bark output separately**
exec
/bin/zsh -lc "nl -ba scripts/send_bark.py | sed -n '1,150p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
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
/bin/zsh -lc "nl -ba scripts/daily_review_run.py | sed -n '1,210p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
 succeeded in 0ms:
     1	#!/usr/bin/env python3
     2	"""每日复习推送编排 runner (DAILY-REVIEW-PUSH-2026-07-29, 终审 A4/A7 硬化版)。
     3	
     4	顺序铁律: md/json 先落盘(保底) → 窗口内 Bark → 失败 osascript 兜底。
     5	壳层 daily-review-push.sh 只负责 mkdir 锁 + 固定解释器; 业务全在此处
     6	(可 --now 注入时间跑 12 场景验收矩阵)。
     7	
     8	终审修正落点:
     9	  A4: 时间门 9:05 ≤ 本地时间 < 21:00 (RunAtLoad 早触发只生成不推;
    10	      唤醒补跑窗口内补推; 过窗只落盘) · state JSON 原子写 (os.replace)
    11	      · last_push_accepted_date 命名 (HTTP 成功仅证明服务端接受)
    12	  A7: payload 持久化 今日复习.json (生成成功推送失败 → 补跑只补推送)
    13	      · osascript 走 argv (板名注入免疫) · 损坏 state 隔离重建不炸
    14	"""
    15	
    16	from __future__ import annotations
    17	
    18	import argparse
    19	import hashlib
    20	import json
    21	import os
    22	import subprocess
    23	import sys
    24	from datetime import datetime, time as dtime, timezone
    25	from pathlib import Path
    26	
    27	sys.path.insert(0, str(Path(__file__).resolve().parent))
    28	import send_bark  # noqa: E402
    29	
    30	REPO = Path(os.environ.get("CANVAS_REPO", "/Users/Heishing/Desktop/canvas/canvas-learning-system"))
    31	# VAULT-SYNC (2026-08-02): 默认值仅作兜底 — 生产链由 wrapper 从 .env
    32	# ACTIVE_VAULT 解析后经 --vault 传入, 与后端同源 (换 vault 只改 .env 一处)
    33	VAULT = REPO / "canvas-vault"
    34	STATE = REPO / "backups" / "daily-review.state.json"
    35	LOG = REPO / "backups" / "daily-review.log"
    36	
    37	PUSH_WINDOW = (dtime(9, 5), dtime(21, 0))
    38	
    39	APPLESCRIPT = (
    40	    "on run argv\n"
    41	    "    display notification (item 2 of argv) with title (item 1 of argv)\n"
    42	    "end run\n"
    43	)
    44	
    45	
    46	def _now(arg: str | None) -> datetime:
    47	    if arg:
    48	        dt = datetime.fromisoformat(arg.replace("Z", "+00:00"))
    49	        return dt if dt.tzinfo else dt.astimezone()
    50	    return datetime.now(timezone.utc)
    51	
    52	
    53	def load_state() -> dict:
    54	    if not STATE.exists():
    55	        return {"schema_version": 1, "board_last_recommended": {}}
    56	    try:
    57	        st = json.loads(STATE.read_text(encoding="utf-8"))
    58	        st.setdefault("board_last_recommended", {})
    59	        return st
    60	    except (json.JSONDecodeError, OSError):
    61	        quarantine = STATE.with_name(
    62	            STATE.name + ".corrupt-" + datetime.now().strftime("%Y%m%dT%H%M%S"))
    63	        try:
    64	            os.replace(STATE, quarantine)
    65	        except OSError:
    66	            pass
    67	        print(f"[runner] state 损坏, 已隔离到 {quarantine.name}, 重建", file=sys.stderr)
    68	        return {"schema_version": 1, "board_last_recommended": {}}
    69	
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
   161	            save_state(st)
   162	            push = "accepted"
   163	        else:
   164	            push = "skip-nokey" if rc == 2 else "failed"
   165	            if rc != 2:
   166	                st["last_result"] = "generated_push_failed"
   167	                st["last_error"] = "bark-send"
   168	            # 本地兜底每日一次 (Code-Review L1 去重门); 无 key 也提醒一条
   169	            # (Code-Review H1: key 配好前不能一切静默)
   170	            if st.get("last_local_notify_date") != today:
   171	                local_noti = noti if rc != 2 else {
   172	                    "title": "📚 今日复习已生成",
   173	                    "body": noti["body"] + "（Bark 未配置，仅本地提醒）",
   174	                }
   175	                fallback = "ok" if osascript_fallback(local_noti) else "fail"
   176	                if fallback == "ok":
   177	                    st["last_local_notify_date"] = today
   178	            save_state(st)
   179	
   180	    log_line(f"generate:{gen} push:{push} fallback:{fallback}")
   181	    print(f"[runner] generate:{gen} push:{push} fallback:{fallback}")
   182	    return 0
   183	
   184	
   185	if __name__ == "__main__":
   186	    sys.exit(main())

exec
/bin/zsh -lc "rg -n \"scan_nodes\\(|build_payload\\(\" scripts backend/tests --glob '"'!backend/.venv/**'"'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
 succeeded in 0ms:
scripts/daily_review_run.py:99:    payload, ranked = picker.build_payload(
scripts/daily_review_pick.py:84:def scan_nodes(vault: Path, now: datetime, decay):
scripts/daily_review_pick.py:222:def build_payload(vault: Path, now: datetime, board_last_recommended: dict, decay):
scripts/daily_review_pick.py:223:    nodes, stats, ineligible = scan_nodes(vault, now, decay)
scripts/daily_review_pick.py:350:    payload, ranked = build_payload(vault, now, blr, load_decay(vault))
backend/tests/regression/test_daily_review_pick.py:31:    return picker.build_payload(vault, NOW, blr or {}, picker.load_decay(vault))

exec
/bin/zsh -lc "rg -n \"今日复习\\.json|\\[.?notification.?\\]|\\.get\\(.notification.|schema_version.*[23]|due_nodes|ineligible\" scripts backend/tests canvas-vault --glob '"'!backend/.venv/**'"' --glob '"'!canvas-vault/outputs/**'"'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
 succeeded in 0ms:
scripts/daily_review_run.py:12:  A7: payload 持久化 今日复习.json (生成成功推送失败 → 补跑只补推送)
scripts/daily_review_run.py:87:    payload_path = VAULT / "outputs" / "今日复习.json"
scripts/daily_review_run.py:148:    noti = (payload or {}).get("notification")
backend/tests/regression/test_snapshot_schema_migration_contract.py:175:    v2["snapshot_schema_version"] = 2
canvas-vault/Dashboard.md:14:> **数据源**：Plugin 实时从 `原白板/*.md` 和 `节点/*.md` 的 frontmatter 自动聚合。手动派生 / 追加 / 配置后**无需刷新**，DataviewJS 会自动重算。**例外**：FSRS 到期数消费 `outputs/今日复习.json` 投影（daily_review_pick 是到期口径唯一裁判，每日 9:05 生成），不做独立重算。
canvas-vault/Dashboard.md:52://    这里只消费 outputs/今日复习.json 投影 (schema v3), 不再独立重算 —
canvas-vault/Dashboard.md:54:let fsrsLine = "⏳ 投影未生成 — `outputs/今日复习.json` 缺失（每日复习任务每天 9:05 自动生成，生成后此处自动出数）";
canvas-vault/Dashboard.md:57:  const raw = await dv.io.load("outputs/今日复习.json");
canvas-vault/Dashboard.md:60:    const hasDetail = Array.isArray(proj.due_nodes);
canvas-vault/Dashboard.md:61:    const dueCnt = hasDetail ? proj.due_nodes.length : (proj.stats?.due_nodes ?? 0);
canvas-vault/Dashboard.md:62:    const newCardCnt = hasDetail ? proj.due_nodes.filter(d => !d.fsrs_due).length : null;
canvas-vault/Dashboard.md:63:    backlogNames = Array.isArray(proj.ineligible?.placeholder) ? proj.ineligible.placeholder : [];
canvas-vault/Dashboard.md:64:    const backlogCnt = backlogNames.length || (proj.stats?.ineligible ?? 0);
canvas-vault/Dashboard.md:74:  fsrsLine = "⚠️ 投影损坏 — `outputs/今日复习.json` 解析失败，等下次生成自动覆盖修复";
backend/tests/regression/test_snapshot_v3_contract.py:83:    assert data["snapshot_schema_version"] == 3
backend/tests/regression/test_snapshot_v3_contract.py:147:    data["snapshot_schema_version"] = "3"
backend/tests/regression/test_snapshot_v3_contract.py:187:    _put_snapshot(vault, {"snapshot_schema_version": "3", "junk": True})
backend/tests/regression/test_snapshot_v3_contract.py:194:    assert data["snapshot_schema_version"] == 3
backend/tests/regression/test_snapshot_v3_contract.py:279:        assert on_disk["snapshot_schema_version"] == 3, f"{tamper_name}: 版本未被自愈"
backend/tests/regression/test_snapshot_v3_contract.py:295:    assert on_disk["snapshot_schema_version"] == 3, "坏根快照应被合法 v3 覆盖"
backend/tests/regression/test_snapshot_v3_contract.py:379:    """V3: {"snapshot_schema_version":3,"freshness":[]} 曾在 :956 抛 AttributeError
backend/tests/regression/test_snapshot_v3_contract.py:382:    _put_snapshot(vault, {"snapshot_schema_version": 3, "freshness": []})
backend/tests/regression/test_daily_review_pick.py:64:    assert payload["stats"]["ineligible"] == 1
backend/tests/regression/test_daily_review_pick.py:65:    assert ranked == [] and payload["notification"] is None
backend/tests/regression/test_daily_review_pick.py:109:    noti = payload["notification"]
backend/tests/regression/test_daily_review_pick.py:130:    assert ranked[0]["pending"] == 1 and payload["stats"]["due_nodes"] == 1
backend/tests/regression/test_daily_review_pick.py:147:# daily_review_pick 为到期口径唯一裁判: Dashboard 消费 due_nodes 明细与
backend/tests/regression/test_daily_review_pick.py:148:# ineligible 分桶, 不再独立重算 (live 实测 13 vs 6 口径分裂的修复锁定)。
backend/tests/regression/test_daily_review_pick.py:151:def test_projection_v3_due_nodes_and_ineligible_buckets(tmp_path):
backend/tests/regression/test_daily_review_pick.py:154:    ① 占位符未剖析 → ineligible.placeholder 单独成桶 (不静默吞掉)
backend/tests/regression/test_daily_review_pick.py:156:    ③ 无 source_board → 不计入 due_nodes, 点名在 unassigned_nodes
backend/tests/regression/test_daily_review_pick.py:157:    ④ TEST_MARKERS 文件名 → ineligible.test_excluded 桶
backend/tests/regression/test_daily_review_pick.py:158:    ⑤ 脏 fsrs_due (带时区偏移) → fail-open 视同到期, 进 due_nodes
backend/tests/regression/test_daily_review_pick.py:178:    assert payload["schema_version"] == 3
backend/tests/regression/test_daily_review_pick.py:179:    assert {d["node"] for d in payload["due_nodes"]} == {"无type", "脏due", "规范到期", "边界到期"}
backend/tests/regression/test_daily_review_pick.py:180:    assert len(payload["due_nodes"]) == payload["stats"]["due_nodes"]
backend/tests/regression/test_daily_review_pick.py:181:    for row in payload["due_nodes"]:
backend/tests/regression/test_daily_review_pick.py:183:    rows = {d["node"]: d for d in payload["due_nodes"]}
backend/tests/regression/test_daily_review_pick.py:188:    ineligible = payload["ineligible"]
backend/tests/regression/test_daily_review_pick.py:189:    assert set(ineligible) >= {"placeholder", "test_excluded", "corrupt"}
backend/tests/regression/test_daily_review_pick.py:190:    assert ineligible["placeholder"] == ["占位"]
backend/tests/regression/test_daily_review_pick.py:191:    assert ineligible["test_excluded"] == ["TestConcept-伪节点"]
backend/tests/regression/test_daily_review_pick.py:192:    assert ineligible["corrupt"] == ["损坏"]
backend/tests/regression/test_daily_review_pick.py:193:    assert len(ineligible["placeholder"]) == payload["stats"]["ineligible"]
backend/tests/regression/test_daily_review_pick.py:194:    assert len(ineligible["test_excluded"]) == payload["stats"]["test_excluded"]
backend/tests/regression/test_daily_review_pick.py:195:    assert len(ineligible["corrupt"]) == payload["stats"]["corrupt"]
backend/tests/regression/test_daily_review_pick.py:204:                "upcoming", "due_nodes", "ineligible", "stats", "notification"):
backend/tests/regression/test_daily_review_pick.py:206:    for key in ("new", "legacy", "none", "ineligible", "test_excluded",
backend/tests/regression/test_daily_review_pick.py:207:                "corrupt", "unassigned", "due_nodes", "future_nodes"):
backend/tests/regression/test_daily_review_pick.py:209:    assert payload["notification"]["id"] == f"canvas-review-{payload['date']}"
backend/tests/regression/test_daily_review_pick.py:216:    assert ranked == [] and payload["due_nodes"] == []
backend/tests/regression/test_daily_review_pick.py:217:    assert set(payload["ineligible"]) == {"placeholder", "test_excluded", "corrupt"}
backend/tests/regression/test_daily_review_pick.py:218:    assert all(v == [] for v in payload["ineligible"].values())
backend/tests/regression/test_daily_review_pick.py:219:    assert payload["notification"] is None
scripts/daily_review_pick.py:5:→ outputs/今日复习.md (人读) + outputs/今日复习.json (推送 payload, 终审 A7:
scripts/daily_review_pick.py:9:唯一裁判 — Dashboard.md 直接 dv.io.load 消费 due_nodes 明细 + ineligible
scripts/daily_review_pick.py:85:    """扫描 节点/ 池 → (nodes, stats, ineligible)。逐节点容错: 单个脏节点不崩全轮。
scripts/daily_review_pick.py:87:    ineligible 分桶 (schema v3, CARD-A2): 被跳过的节点按原因点名, 不再只有
scripts/daily_review_pick.py:90:    stats = {"new": 0, "legacy": 0, "none": 0, "ineligible": 0, "test_excluded": 0, "corrupt": 0}
scripts/daily_review_pick.py:91:    ineligible = {"placeholder": [], "test_excluded": [], "corrupt": []}
scripts/daily_review_pick.py:100:            ineligible["corrupt"].append(stem)
scripts/daily_review_pick.py:105:            ineligible["test_excluded"].append(stem)
scripts/daily_review_pick.py:110:            stats["ineligible"] += 1
scripts/daily_review_pick.py:111:            ineligible["placeholder"].append(stem)
scripts/daily_review_pick.py:143:            ineligible["corrupt"].append(stem)
scripts/daily_review_pick.py:165:    return nodes, stats, ineligible
scripts/daily_review_pick.py:223:    nodes, stats, ineligible = scan_nodes(vault, now, decay)
scripts/daily_review_pick.py:226:    # v3 (CARD-A2): due_nodes 明细与 stats 数字同源派生 — 自洽靠构造保证,
scripts/daily_review_pick.py:240:    stats["due_nodes"] = len(due_rows)
scripts/daily_review_pick.py:244:        "schema_version": 3,             # v3: +due_nodes 明细 +ineligible 分桶
scripts/daily_review_pick.py:250:        "due_nodes": due_rows,
scripts/daily_review_pick.py:251:        "ineligible": ineligible,
scripts/daily_review_pick.py:257:        payload["notification"] = {
scripts/daily_review_pick.py:266:        payload["notification"] = {
scripts/daily_review_pick.py:280:        f"> 生成 {payload['generated_at']} · 到期={s['due_nodes']} / 未到期={s['future_nodes']}（不含未归板）"
scripts/daily_review_pick.py:282:        f" / 无字段={s['none']} / 未剖析跳过={s['ineligible']} / 测试排除={s['test_excluded']}"
scripts/daily_review_pick.py:355:        atomic_write(out / "今日复习.json",
scripts/install-vault.sh:108:schema_version: "2.0-multi-vault-2026-05-10"
scripts/send_bark.py:104:    ap.add_argument("--payload", required=True, help="今日复习.json 路径")
scripts/send_bark.py:107:    noti = payload.get("notification")
backend/tests/unit/test_vault_switch.py:152:            'vault_id: "explicit_yaml_id"\nsubject: math\nschema_version: "2.0-multi-vault-2026-05-10"\n',
backend/tests/unit/test_vault_switch.py:187:            'subject: cs-61b\nschema_version: "1.0-flat-architecture-2026-04-20"\n',
backend/tests/unit/test_vault_switch.py:205:            'vault_id: "数学101"\nsubject: math\nschema_version: "2.0-multi-vault-2026-05-10"\n',

**Identifying test coverage gaps**
**Analyzing parity test coverage limitations**
**Assessing degrade path handling**
**Inspecting dataview plugin presence**
codex
范围已锁定：基线与当前 HEAD 都是 `2cf9cbf0`，因此这确实是“基线提交 → 当前工作树”的 3 个已跟踪文件 diff；另有 2 个未跟踪交付文档，我不会读取或改动，避免把施工方自审当证据。接下来我会直接跑生产 `build_payload`/runner 消费路径与 Dashboard 三种输入反例，而不只看新增测试是否绿。
exec
/bin/zsh -lc "find canvas-vault/.obsidian -maxdepth 4 -type f -iname '*dataview*' -o -path '*/dataview/*' 2>/dev/null | head -80" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
exec
/bin/zsh -lc "nl -ba canvas-vault/Dashboard.md | sed -n '1,105p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
 succeeded in 0ms:
 succeeded in 0ms:
     1	---
     2	type: dashboard
     3	layout: active-learning-view
     4	created_at: 2026-05-01
     5	version: 1.0
     6	story: "1.18"
     7	---
     8	
     9	# 📊 Canvas 学习仪表盘
    10	
    11	> [!info]+ 这是什么？
    12	> 一站式查看所有原白板状态 + 节点总数 + 平均掌握度 + 待复习节点。**Cmd+P 打开命令面板** → 搜索"启动考察"可以一键发起考察（复制 /start-exam-board 命令）。
    13	>
    14	> **数据源**：Plugin 实时从 `原白板/*.md` 和 `节点/*.md` 的 frontmatter 自动聚合。手动派生 / 追加 / 配置后**无需刷新**，DataviewJS 会自动重算。**例外**：FSRS 到期数消费 `outputs/今日复习.json` 投影（daily_review_pick 是到期口径唯一裁判，每日 9:05 生成），不做独立重算。
    15	
    16	---
    17	
    18	## 🎯 三大核心指标
    19	
    20	```dataviewjs
    21	const boards = dv.pages('"原白板"').where(p => p.type === "whiteboard");
    22	const nodes = dv.pages('"节点"').where(p => p.type === "concept");
    23	
    24	// 1. 平均掌握度（含颜色编码）
    25	const masteryValues = nodes
    26	  .map(p => typeof p.mastery_score === "number" ? p.mastery_score : 0.30)
    27	  .array();
    28	const avgMastery = masteryValues.length
    29	  ? masteryValues.reduce((s, v) => s + v, 0) / masteryValues.length
    30	  : 0;
    31	const masteryColor = avgMastery > 0.7 ? "🟢" : avgMastery > 0.4 ? "🟡" : "🔴";
    32	const masteryLabel = avgMastery > 0.7 ? "优秀" : avgMastery > 0.4 ? "进行中" : "起步";
    33	
    34	// 2. 节点总数（按白板分组）
    35	const nodesByBoard = {};
    36	for (const node of nodes) {
    37	  const sb = node.source_board;
    38	  let boardName = "（无归属）";
    39	  if (sb) {
    40	    const path = typeof sb === "string" ? sb : (sb.path || sb.link || "");
    41	    const m = path.match(/原白板\/([^\]|]+?)(?:\.md)?(?:\|[^\]]*)?(?:\]\])?$/);
    42	    if (m) boardName = m[1].trim();
    43	  }
    44	  nodesByBoard[boardName] = (nodesByBoard[boardName] || 0) + 1;
    45	}
    46	const groupedStr = Object.entries(nodesByBoard)
    47	  .sort((a, b) => b[1] - a[1])
    48	  .map(([k, v]) => `${k}: ${v}`)
    49	  .join(" / ");
    50	
    51	// 3. FSRS 到期数（CARD-A2 2026-08-24: daily_review_pick 是到期口径唯一裁判,
    52	//    这里只消费 outputs/今日复习.json 投影 (schema v3), 不再独立重算 —
    53	//    修复 live 实测 13 vs 6 的口径分裂）
    54	let fsrsLine = "⏳ 投影未生成 — `outputs/今日复习.json` 缺失（每日复习任务每天 9:05 自动生成，生成后此处自动出数）";
    55	let backlogNames = [];
    56	try {
    57	  const raw = await dv.io.load("outputs/今日复习.json");
    58	  if (raw) {
    59	    const proj = JSON.parse(raw);
    60	    const hasDetail = Array.isArray(proj.due_nodes);
    61	    const dueCnt = hasDetail ? proj.due_nodes.length : (proj.stats?.due_nodes ?? 0);
    62	    const newCardCnt = hasDetail ? proj.due_nodes.filter(d => !d.fsrs_due).length : null;
    63	    backlogNames = Array.isArray(proj.ineligible?.placeholder) ? proj.ineligible.placeholder : [];
    64	    const backlogCnt = backlogNames.length || (proj.stats?.ineligible ?? 0);
    65	    const parts = [];
    66	    if (newCardCnt !== null) parts.push(`含 ${newCardCnt} 张新卡视同到期`);
    67	    parts.push(`待剖析积压 ${backlogCnt} 张另计`);
    68	    const unassignedCnt = proj.stats?.unassigned ?? 0;
    69	    if (unassignedCnt > 0) parts.push(`未归板 ${unassignedCnt} 张另计`);
    70	    parts.push(`投影生成于 ${proj.generated_at ?? "?"}`);
    71	    fsrsLine = `\`${dueCnt}\`（${parts.join(" · ")}）`;
    72	  }
    73	} catch (e) {
    74	  fsrsLine = "⚠️ 投影损坏 — `outputs/今日复习.json` 解析失败，等下次生成自动覆盖修复";
    75	}
    76	
    77	dv.paragraph(
    78	  `📊 **平均精通度**: \`${avgMastery.toFixed(2)}\` ${masteryColor} ${masteryLabel}\n\n` +
    79	  `📚 **节点总数**: \`${nodes.length}\`（${groupedStr || "暂无"}）\n\n` +
    80	  `⏰ **FSRS 到期**: ${fsrsLine}\n\n` +
    81	  `🗂️ **原白板总数**: \`${boards.length}\``
    82	);
    83	
    84	if (backlogNames.length > 0) {
    85	  // 文件名含 wikilink 保留字符 (|[]#^) 时退化为纯文本, 防死链
    86	  dv.paragraph(
    87	    `> 🗂️ **待剖析积压**（${backlogNames.length} 张占位节点，定义未写完不参与复习，不计入到期数）: ` +
    88	    backlogNames.map(n => /[|\[\]#^]/.test(n) ? n : `[[节点/${n}|${n}]]`).join("、")
    89	  );
    90	}
    91	```
    92	
    93	---
    94	
    95	## 🗺️ 活跃原白板（按节点数排序，含交互按钮）
    96	
    97	> [!success]+ v4.3 路径 1 升级 — 交互式按钮已就绪
    98	> 每个白板行右侧多 2 个按钮：📂 打开白板 / 🚀 启动考察。点击直接调 plugin API（无需 Cmd+P）。
    99	
   100	```dataviewjs
   101	const plugin = app.plugins.plugins["canvas-learning-system"];
   102	if (!plugin) {
   103	  dv.paragraph("> ❌ Canvas plugin 未加载，请先在 Settings → Community plugins 启用。");
   104	} else {
   105	  const boards = dv.pages('"原白板"').where(p => p.type === "whiteboard");

exec
/bin/zsh -lc "rg -n 'dataview' package.json package-lock.json frontend/obsidian-plugin/package.json frontend/obsidian-plugin/package-lock.json 2>/dev/null" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
 exited 2 in 0ms:
exec
/bin/zsh -lc "nl -ba backend/tests/regression/test_daily_review_pick.py | sed -n '1,240p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
 succeeded in 0ms:
     1	"""daily_review_pick 选板逻辑锁定 (DAILY-REVIEW-PUSH-2026-07-29, Code-Review M6)。
     2	
     3	12 场景运行时矩阵之外的纯逻辑层: 病理日期不崩全轮 / wikilink 归一 /
     4	占位符跳过 / tie-break 三级 / 脏数值进 corrupt / BOM 容忍。
     5	"""
     6	
     7	import shutil
     8	import sys
     9	from datetime import datetime, timezone
    10	from pathlib import Path
    11	
    12	WT = Path(__file__).resolve().parents[3]
    13	sys.path.insert(0, str(WT / "scripts"))
    14	
    15	import daily_review_pick as picker  # noqa: E402
    16	
    17	NOW = datetime(2026, 7, 30, 1, 0, tzinfo=timezone.utc)
    18	
    19	
    20	_seq = iter(range(1000))
    21	
    22	
    23	def _build(tmp_path, nodes: dict, blr: dict | None = None):
    24	    vault = tmp_path / f"vault{next(_seq)}"  # 同一测试可多次调用, 各建独立 vault
    25	    scripts = vault / ".claude" / "scripts"
    26	    scripts.mkdir(parents=True)
    27	    (vault / "节点").mkdir()
    28	    shutil.copy(WT / "canvas-vault" / ".claude" / "scripts" / "decay_beta.py", scripts)
    29	    for name, content in nodes.items():
    30	        (vault / "节点" / f"{name}.md").write_text(content, encoding="utf-8")
    31	    return picker.build_payload(vault, NOW, blr or {}, picker.load_decay(vault))
    32	
    33	
    34	def _node(board="普通板", extra=""):
    35	    return f'---\ntype: concept\nsource_board: "[[原白板/{board}]]"\n{extra}---\n真实内容。\n'
    36	
    37	
    38	def test_pathological_last_examined_does_not_kill_run(tmp_path):
    39	    """Code-Review M2: 年份手滑成 0001 的节点不得崩掉整轮生成。"""
    40	    payload, ranked = _build(
    41	        tmp_path,
    42	        {
    43	            "病理": _node(extra="mastery_a: 2.0\nmastery_b: 3.0\nlast_examined: 0001-01-01T00:00:00Z\n"),
    44	            "正常": _node(),
    45	        },
    46	    )
    47	    assert payload["stats"]["corrupt"] == 0 and len(ranked) == 1
    48	    assert all(r["priority"] == r["priority"] for r in ranked)  # 无 NaN
    49	
    50	
    51	def test_wikilink_board_normalization(tmp_path):
    52	    payload, ranked = _build(tmp_path, {"甲": _node(board="我的板")})
    53	    assert ranked[0]["board"] == "我的板"
    54	    assert "node 甲" in picker.render_md(payload, ranked)
    55	
    56	
    57	def test_placeholder_node_skipped_empty_notification(tmp_path):
    58	    payload, ranked = _build(
    59	        tmp_path,
    60	        {
    61	            "占位": _node(extra="").replace("真实内容。", "> 你的 1-2 句精准定义"),
    62	        },
    63	    )
    64	    assert payload["stats"]["ineligible"] == 1
    65	    assert ranked == [] and payload["notification"] is None
    66	
    67	
    68	def test_tiebreak_prefers_least_recently_recommended(tmp_path):
    69	    nodes = {"a节点": _node(board="A板"), "b节点": _node(board="B板")}
    70	    _, ranked = _build(tmp_path, nodes, blr={"A板": "2026-07-29"})
    71	    assert ranked[0]["board"] == "B板", "同分时从未被推荐的板优先"
    72	    _, ranked2 = _build(tmp_path, nodes)
    73	    assert ranked2[0]["board"] == "A板", "全无记录时按板名稳定排序"
    74	
    75	
    76	def test_negative_mastery_counted_corrupt_not_silent(tmp_path):
    77	    """Code-Review L5: mastery_a: -3 必须进 corrupt, 不得静默当无字段。"""
    78	    payload, ranked = _build(
    79	        tmp_path,
    80	        {
    81	            "脏": _node(extra="mastery_a: -3\nmastery_b: 2\n"),
    82	        },
    83	    )
    84	    assert payload["stats"]["corrupt"] == 1 and ranked == []
    85	
    86	
    87	def test_bom_frontmatter_tolerated(tmp_path):
    88	    payload, _ = _build(
    89	        tmp_path,
    90	        {
    91	            "带bom": "﻿" + _node(extra="mastery_a: 1.0\nmastery_b: 1.0\n"),
    92	        },
    93	    )
    94	    assert payload["stats"]["new"] == 1
    95	
    96	
    97	# ── FSRS WHEN 语义 ([Decision-FSRS-2], FSRS-V2-2026-07-30) ──
    98	
    99	
   100	def test_future_due_board_gets_rest_notification(tmp_path):
   101	    """F1: 唯一板全员未到期 → 不进推荐榜, 推送改为诚实的放假消息。"""
   102	    payload, ranked = _build(
   103	        tmp_path,
   104	        {
   105	            "已排期": _node(extra="mastery_a: 2.0\nmastery_b: 2.0\nfsrs_due: 2026-08-15T01:00:00Z\n"),
   106	        },
   107	    )
   108	    assert ranked == [] and payload["stats"]["future_nodes"] == 1
   109	    noti = payload["notification"]
   110	    assert "无到期" in noti["title"] and "2026-08-15" in noti["body"]
   111	    assert payload["upcoming"][0]["board"] == "普通板"
   112	
   113	
   114	def test_due_filter_beats_pick_within_board(tmp_path):
   115	    """WHEN 先于 WHAT: 板内未到期节点即使 pick 更低也不能当 top_node。"""
   116	    payload, ranked = _build(
   117	        tmp_path,
   118	        {
   119	            "低分未到期": _node(extra="mastery_a: 0.1\nmastery_b: 5.0\nfsrs_due: 2026-08-15T01:00:00Z\n"),
   120	            "到期节点": _node(extra="mastery_a: 3.0\nmastery_b: 1.0\nfsrs_due: 2026-07-29T01:00:00Z\n"),
   121	        },
   122	    )
   123	    assert ranked[0]["top_node"] == "到期节点" and ranked[0]["pending"] == 1
   124	    assert ranked[0]["next_due"] == "2026-08-15T01:00:00Z"
   125	
   126	
   127	def test_no_fsrs_field_means_new_card_due_now(tmp_path):
   128	    """零迁移: 无 fsrs_due 字段的存量节点 = New 卡即刻到期, 行为与 MVP 一致。"""
   129	    payload, ranked = _build(tmp_path, {"存量": _node()})
   130	    assert ranked[0]["pending"] == 1 and payload["stats"]["due_nodes"] == 1
   131	
   132	
   133	def test_unassigned_nodes_named_in_md(tmp_path):
   134	    """Code-Review M3: 无 source_board 节点点名可见, 不再只是个数字。"""
   135	    payload, ranked = _build(
   136	        tmp_path,
   137	        {
   138	            "孤儿": "---\ntype: concept\n---\n真实内容。\n",
   139	            "正常": _node(),
   140	        },
   141	    )
   142	    assert payload["unassigned_nodes"] == ["孤儿"]
   143	    assert "孤儿" in picker.render_md(payload, ranked)
   144	
   145	
   146	# ── Review Projection v3 (CARD-A2, BATCH-2026-08-24-复习闭环) ──
   147	# daily_review_pick 为到期口径唯一裁判: Dashboard 消费 due_nodes 明细与
   148	# ineligible 分桶, 不再独立重算 (live 实测 13 vs 6 口径分裂的修复锁定)。
   149	
   150	
   151	def test_projection_v3_due_nodes_and_ineligible_buckets(tmp_path):
   152	    """5 类口径分歧节点全覆盖: 明细集合与 stats 数字必须同源自洽。
   153	
   154	    ① 占位符未剖析 → ineligible.placeholder 单独成桶 (不静默吞掉)
   155	    ② 无 type 字段 → picker 口径照收 (旧 Dashboard type==concept 反向漏掉的那类)
   156	    ③ 无 source_board → 不计入 due_nodes, 点名在 unassigned_nodes
   157	    ④ TEST_MARKERS 文件名 → ineligible.test_excluded 桶
   158	    ⑤ 脏 fsrs_due (带时区偏移) → fail-open 视同到期, 进 due_nodes
   159	
   160	    另锁 due 边界 (对抗性验证 M2): fsrs_due==now 判到期 (<= 语义),
   161	    now+1h 判未到期 — 词法比较改 < 或引入时区漂移都会红。
   162	    """
   163	    payload, _ = _build(
   164	        tmp_path,
   165	        {
   166	            "占位": _node().replace("真实内容。", "> 你的 1-2 句精准定义"),
   167	            "无type": '---\nsource_board: "[[原白板/B板]]"\n---\n真实内容。\n',
   168	            "孤儿": "---\ntype: concept\n---\n真实内容。\n",
   169	            "TestConcept-伪节点": _node(),
   170	            "脏due": _node(extra="fsrs_due: 2026-07-29T01:00:00+08:00\n"),
   171	            "规范到期": _node(extra="fsrs_due: 2026-07-29T01:00:00Z\n"),
   172	            "边界到期": _node(extra="fsrs_due: 2026-07-30T01:00:00Z\n"),
   173	            "小时级未到期": _node(extra="fsrs_due: 2026-07-30T02:00:00Z\n"),
   174	            "未到期": _node(extra="fsrs_due: 2026-08-15T01:00:00Z\n"),
   175	            "损坏": _node(extra="mastery_a: -3\nmastery_b: 2\n"),
   176	        },
   177	    )
   178	    assert payload["schema_version"] == 3
   179	    assert {d["node"] for d in payload["due_nodes"]} == {"无type", "脏due", "规范到期", "边界到期"}
   180	    assert len(payload["due_nodes"]) == payload["stats"]["due_nodes"]
   181	    for row in payload["due_nodes"]:
   182	        assert set(row) >= {"node", "board", "state", "fsrs_due"}
   183	    rows = {d["node"]: d for d in payload["due_nodes"]}
   184	    assert rows["无type"]["board"] == "B板" and rows["规范到期"]["board"] == "普通板"
   185	    # fail-open 清空语义锁定: Dashboard 的"新卡视同到期"计数依赖 fsrs_due==""
   186	    assert rows["脏due"]["fsrs_due"] == ""
   187	
   188	    ineligible = payload["ineligible"]
   189	    assert set(ineligible) >= {"placeholder", "test_excluded", "corrupt"}
   190	    assert ineligible["placeholder"] == ["占位"]
   191	    assert ineligible["test_excluded"] == ["TestConcept-伪节点"]
   192	    assert ineligible["corrupt"] == ["损坏"]
   193	    assert len(ineligible["placeholder"]) == payload["stats"]["ineligible"]
   194	    assert len(ineligible["test_excluded"]) == payload["stats"]["test_excluded"]
   195	    assert len(ineligible["corrupt"]) == payload["stats"]["corrupt"]
   196	    assert payload["unassigned_nodes"] == ["孤儿"]
   197	
   198	
   199	def test_projection_v3_purely_additive_keeps_v2_contract(tmp_path):
   200	    """推送链被动性守卫: v2 既有字段一个不少、语义不变 (daily_review_run /
   201	    send_bark 只读 notification, 但全字段名保留是加性承诺的下界)。"""
   202	    payload, ranked = _build(tmp_path, {"存量": _node()})
   203	    for key in ("unassigned_nodes", "date", "generated_at", "top_boards",
   204	                "upcoming", "due_nodes", "ineligible", "stats", "notification"):
   205	        assert key in payload
   206	    for key in ("new", "legacy", "none", "ineligible", "test_excluded",
   207	                "corrupt", "unassigned", "due_nodes", "future_nodes"):
   208	        assert isinstance(payload["stats"][key], int)
   209	    assert payload["notification"]["id"] == f"canvas-review-{payload['date']}"
   210	    assert ranked[0]["board"] == "普通板"
   211	
   212	
   213	def test_projection_v3_empty_vault_keeps_contract_keys(tmp_path):
   214	    """空 vault 契约完整性: 分桶与明细键必须恒在 (Dashboard 不做存在性分支)。"""
   215	    payload, ranked = _build(tmp_path, {})
   216	    assert ranked == [] and payload["due_nodes"] == []
   217	    assert set(payload["ineligible"]) == {"placeholder", "test_excluded", "corrupt"}
   218	    assert all(v == [] for v in payload["ineligible"].values())
   219	    assert payload["notification"] is None

exec
/bin/zsh -lc "rg -n \"dv\\.io\\.load\\(\" canvas-vault . --glob '*.md' --glob '"'!_bmad-output/审查/codex-review-CARD-A2.md'"' --glob '"'!canvas-vault/outputs/**'"'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
 succeeded in 0ms:
canvas-vault/Dashboard.md:57:  const raw = await dv.io.load("outputs/今日复习.json");
./canvas-vault/Dashboard.md:57:  const raw = await dv.io.load("outputs/今日复习.json");
canvas-vault/原白板/递归与分治 (Recursion & Divide-Conquer).md:59:for (const p of nodes.array()) bodies[p.file.path] = await dv.io.load(p.file.path);
./canvas-vault/原白板/递归与分治 (Recursion & Divide-Conquer).md:59:for (const p of nodes.array()) bodies[p.file.path] = await dv.io.load(p.file.path);
canvas-vault/原白板/CS 61B.md:61:for (const p of nodes.array()) bodies[p.file.path] = await dv.io.load(p.file.path);
./canvas-vault/原白板/CS 61B.md:61:for (const p of nodes.array()) bodies[p.file.path] = await dv.io.load(p.file.path);
canvas-vault/原白板/线性代数.md:57:for (const p of nodes.array()) bodies[p.file.path] = await dv.io.load(p.file.path);
./canvas-vault/原白板/线性代数.md:57:for (const p of nodes.array()) bodies[p.file.path] = await dv.io.load(p.file.path);
canvas-vault/原白板/特征值与特征向量.md:68:for (const p of nodes.array()) bodies[p.file.path] = await dv.io.load(p.file.path);
canvas-vault/原白板/特征值与特征向量.md:115:for (const p of nodes.array()) bodies[p.file.path] = await dv.io.load(p.file.path);
./canvas-vault/原白板/特征值与特征向量.md:68:for (const p of nodes.array()) bodies[p.file.path] = await dv.io.load(p.file.path);
./canvas-vault/原白板/特征值与特征向量.md:115:for (const p of nodes.array()) bodies[p.file.path] = await dv.io.load(p.file.path);

**Evaluating local testing and sandbox limits**
**Planning isolated pytest execution with cache disabled**
**Assessing safe Node.js inline execution**
**Evaluating node execution options without file writes**
**Designing async eval with mock DataArray**
**Verifying code extraction accuracy**
2026-08-24T15:39:43.530837Z ERROR codex_models_manager::manager: failed to refresh available models: timeout waiting for child process to exit
**Implementing async data loader with filtering subclass**
**Handling io.load error fallback**
**Clarifying schema version caching strategy**
**Reviewing notification parsing and due date handling**
**Fixing state increment with corrupt handling**
**Analyzing due count and dashboard projection handling**
**Identifying schema v3 validation gaps causing false zero due**
**Noting mismatch handling between stats and due_nodes**
**Assessing path degradation severity**
**Verifying data corruption handling and fallbacks**
**Identifying test coverage gaps for Dashboard**
**Searching git history for runner tests**
exec
/bin/zsh -lc "rg -n \"ensure_payload|send_bark|daily_review_run|今日复习\" backend/tests scripts --glob '"'!backend/.venv/**'"'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
 succeeded in 0ms:
scripts/daily_review_run.py:12:  A7: payload 持久化 今日复习.json (生成成功推送失败 → 补跑只补推送)
scripts/daily_review_run.py:28:import send_bark  # noqa: E402
scripts/daily_review_run.py:85:def ensure_payload(st: dict, now: datetime, today: str) -> tuple[dict | None, str]:
scripts/daily_review_run.py:87:    payload_path = VAULT / "outputs" / "今日复习.json"
scripts/daily_review_run.py:103:    picker.atomic_write(out / "今日复习.md", picker.render_md(payload, ranked))
scripts/daily_review_run.py:142:        payload, gen = ensure_payload(st, now, today)
scripts/daily_review_run.py:157:        rc = send_bark.send(noti)
scripts/daily_review_run.py:172:                    "title": "📚 今日复习已生成",
scripts/daily_review_pick.py:5:→ outputs/今日复习.md (人读) + outputs/今日复习.json (推送 payload, 终审 A7:
scripts/daily_review_pick.py:11:(daily_review_run/send_bark 只读 notification) 被动兼容。
scripts/daily_review_pick.py:210:    prefix = "📚 今日复习 · "
scripts/daily_review_pick.py:278:        f"# 今日复习 · {payload['date']}",
scripts/daily_review_pick.py:332:    ap.add_argument("--write", action="store_true", help="写 outputs/今日复习.md+json")
scripts/daily_review_pick.py:336:    # 裸时间当本地时区, 与 daily_review_run.py 语义统一 (Code-Review L6)
scripts/daily_review_pick.py:354:        atomic_write(out / "今日复习.md", render_md(payload, ranked))
scripts/daily_review_pick.py:355:        atomic_write(out / "今日复习.json",
scripts/daily-review-push.sh:4:# 固定解释器调 runner。业务逻辑全在 daily_review_run.py (--now 可测)。
scripts/daily-review-push.sh:31:"$PY" "$WT/scripts/daily_review_run.py" "$@"
scripts/send_bark.py:104:    ap.add_argument("--payload", required=True, help="今日复习.json 路径")
backend/tests/regression/test_daily_review_pick.py:200:    """推送链被动性守卫: v2 既有字段一个不少、语义不变 (daily_review_run /
backend/tests/regression/test_daily_review_pick.py:201:    send_bark 只读 notification, 但全字段名保留是加性承诺的下界)。"""

**Planning runner runtime tests without secrets**
**Evaluating temp fixture creation constraints**
**Testing send_bark with in-memory payload**
**Exploring payload construction methods**
**Planning real payload tests with temp fixtures**
**Planning separate payload and send calls**
**Planning rigorous notification schema tests**
**Designing baseline module import via exec**
**Verifying exact field equality in fixtures**
**Setting globals and verifying payload flow**
已读取 CARD-A2、确认基线 SHA 与 3 文件 diff；开始对真实生成/消费路径做并行与反例审查。
  ✓ 锁定 CARD-A2 验收口径、工作树基线与完整 diff 范围
  → 并行审查 schema/推送链、Dashboard 降级语义、测试覆盖与回归
  • 复现关键反例并运行相关测试/静态验证
  • 交叉核验 finding，输出分级结论与验证限制
exec
/bin/zsh -lc "grep -c 'schedCnt\\|newCnt' canvas-vault/Dashboard.md; grep -c '今日复习.json' canvas-vault/Dashboard.md" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
 succeeded in 0ms:
0
5

exec
/bin/zsh -lc 'git diff --check worktree-feature-obsidian-hybrid-dev' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead

exec
/bin/zsh -lc '.venv/bin/pytest tests/regression/test_daily_review_pick.py -q -p no:cacheprovider' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/backend
 exited 1 in 274ms:
Traceback (most recent call last):
  File "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/backend/.venv/bin/pytest", line 6, in <module>
    sys.exit(console_main())
             ~~~~~~~~~~~~^^
  File "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/backend/.venv/lib/python3.14/site-packages/_pytest/config/__init__.py", line 223, in console_main
    code = main()
  File "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/backend/.venv/lib/python3.14/site-packages/_pytest/config/__init__.py", line 193, in main
    config = _prepareconfig(new_args, plugins)
  File "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/backend/.venv/lib/python3.14/site-packages/_pytest/config/__init__.py", line 361, in _prepareconfig
    config: Config = pluginmanager.hook.pytest_cmdline_parse(
                     ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^
        pluginmanager=pluginmanager, args=args
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/backend/.venv/lib/python3.14/site-packages/pluggy/_hooks.py", line 512, in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/backend/.venv/lib/python3.14/site-packages/pluggy/_manager.py", line 120, in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/backend/.venv/lib/python3.14/site-packages/pluggy/_callers.py", line 167, in _multicall
    raise exception
  File "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/backend/.venv/lib/python3.14/site-packages/pluggy/_callers.py", line 139, in _multicall
    teardown.throw(exception)
    ~~~~~~~~~~~~~~^^^^^^^^^^^
  File "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/backend/.venv/lib/python3.14/site-packages/_pytest/helpconfig.py", line 124, in pytest_cmdline_parse
    config = yield
             ^^^^^
  File "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/backend/.venv/lib/python3.14/site-packages/pluggy/_callers.py", line 121, in _multicall
    res = hook_impl.function(*args)
  File "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/backend/.venv/lib/python3.14/site-packages/_pytest/config/__init__.py", line 1186, in pytest_cmdline_parse
    self.parse(args)
    ~~~~~~~~~~^^^^^^
  File "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/backend/.venv/lib/python3.14/site-packages/_pytest/config/__init__.py", line 1556, in parse
    self.hook.pytest_load_initial_conftests(
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^
        early_config=self, args=args, parser=self._parser
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/backend/.venv/lib/python3.14/site-packages/pluggy/_hooks.py", line 512, in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/backend/.venv/lib/python3.14/site-packages/pluggy/_manager.py", line 120, in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/backend/.venv/lib/python3.14/site-packages/pluggy/_callers.py", line 167, in _multicall
    raise exception
  File "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/backend/.venv/lib/python3.14/site-packages/pluggy/_callers.py", line 139, in _multicall
    teardown.throw(exception)
    ~~~~~~~~~~~~~~^^^^^^^^^^^
  File "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/backend/.venv/lib/python3.14/site-packages/_pytest/warnings.py", line 128, in pytest_load_initial_conftests
    return (yield)
            ^^^^^
  File "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/backend/.venv/lib/python3.14/site-packages/pluggy/_callers.py", line 116, in _multicall
    next(function_gen)  # first yield
    ~~~~^^^^^^^^^^^^^^
  File "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/backend/.venv/lib/python3.14/site-packages/_pytest/capture.py", line 170, in pytest_load_initial_conftests
    capman.start_global_capturing()
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/backend/.venv/lib/python3.14/site-packages/_pytest/capture.py", line 773, in start_global_capturing
    self._global_capturing = _get_multicapture(self._method)
                             ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^
  File "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/backend/.venv/lib/python3.14/site-packages/_pytest/capture.py", line 714, in _get_multicapture
    return MultiCapture(in_=FDCapture(0), out=FDCapture(1), err=FDCapture(2))
                                              ~~~~~~~~~^^^
  File "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/backend/.venv/lib/python3.14/site-packages/_pytest/capture.py", line 493, in __init__
    TemporaryFile(buffering=0),
    ~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.4_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/tempfile.py", line 652, in TemporaryFile
    prefix, suffix, dir, output_type = _sanitize_params(prefix, suffix, dir)
                                       ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.4_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/tempfile.py", line 127, in _sanitize_params
    dir = gettempdir()
  File "/opt/homebrew/Cellar/python@3.14/3.14.4_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/tempfile.py", line 312, in gettempdir
    return _os.fsdecode(_gettempdir())
                        ~~~~~~~~~~~^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.4_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/tempfile.py", line 305, in _gettempdir
    tempdir = _get_default_tempdir()
  File "/opt/homebrew/Cellar/python@3.14/3.14.4_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/tempfile.py", line 222, in _get_default_tempdir
    raise FileNotFoundError(_errno.ENOENT,
                            "No usable temporary directory found in %s" %
                            dirlist)
FileNotFoundError: [Errno 2] No usable temporary directory found in ['/var/folders/vq/gssw8vy54671lh9nlqc_ft2w0000gn/T/', '/tmp', '/var/tmp', '/usr/tmp', '/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/backend']

**Requesting escalated pytest execution**
exec
/bin/zsh -lc '.venv/bin/pytest tests/regression/test_daily_review_pick.py -q -p no:cacheprovider' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/backend
**Clarifying async exec and wait usage**
 succeeded in 12123ms:
============================= test session starts ==============================
platform darwin -- Python 3.14.4, pytest-9.0.2, pluggy-1.6.0
rootdir: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/backend
configfile: pytest.ini
plugins: hypothesis-6.151.10, cov-7.1.0, xdist-3.8.0, asyncio-1.3.0, schemathesis-4.14.3, bdd-8.1.0, langsmith-0.7.24, anyio-4.13.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 13 items

tests/regression/test_daily_review_pick.py .............                 [100%]

=============================== warnings summary ===============================
.venv/lib/python3.14/site-packages/google/genai/types.py:43
  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/backend/.venv/lib/python3.14/site-packages/google/genai/types.py:43: DeprecationWarning: '_UnionGenericAlias' is deprecated and slated for removal in Python 3.17
    VersionedUnionType = Union[builtin_types.UnionType, _UnionGenericAlias]

.venv/lib/python3.14/site-packages/langchain_core/_api/deprecation.py:25
  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/backend/.venv/lib/python3.14/site-packages/langchain_core/_api/deprecation.py:25: UserWarning: Core Pydantic V1 functionality isn't compatible with Python 3.14 or greater.
    from pydantic.v1.fields import FieldInfo as FieldInfoV1

.venv/lib/python3.14/site-packages/graphiti_core/driver/search_interface/search_interface.py:22
  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/backend/.venv/lib/python3.14/site-packages/graphiti_core/driver/search_interface/search_interface.py:22: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    class SearchInterface(BaseModel):

.venv/lib/python3.14/site-packages/jieba/_compat.py:18
  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/backend/.venv/lib/python3.14/site-packages/jieba/_compat.py:18: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
    import pkg_resources

<frozen importlib._bootstrap>:491
  <frozen importlib._bootstrap>:491: DeprecationWarning: builtin type SwigPyPacked has no __module__ attribute

<frozen importlib._bootstrap>:491
  <frozen importlib._bootstrap>:491: DeprecationWarning: builtin type SwigPyObject has no __module__ attribute

app/api/v1/endpoints/chat.py:803
  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/backend/app/api/v1/endpoints/chat.py:803: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    class HookEnrichRequest(BaseModel):

app/api/v1/endpoints/metadata.py:147
  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/backend/app/api/v1/endpoints/metadata.py:147: FastAPIDeprecationWarning: `example` has been deprecated, please use `examples` instead
    canvas_path: str = Query(

app/api/v1/endpoints/metadata.py:218
  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/backend/app/api/v1/endpoints/metadata.py:218: FastAPIDeprecationWarning: `example` has been deprecated, please use `examples` instead
    canvas_path: str = Query(..., description="Canvas file path", example="Math 54/离散数学.canvas"),

.venv/lib/python3.14/site-packages/pydantic/_internal/_generate_schema.py:2356
  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/backend/.venv/lib/python3.14/site-packages/pydantic/_internal/_generate_schema.py:2356: PydanticDeprecatedSince211: The `__get_pydantic_core_schema__` method of the `BaseModel` class is deprecated. If you are calling `super().__get_pydantic_core_schema__` when overriding the method on a Pydantic model, consider using `handler(source)` instead. However, note that overriding this method on models can lead to unexpected side effects. Deprecated in Pydantic V2.11 to be removed in V3.0.
    schema = annotation_get_schema(source, get_inner_schema)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================= 13 passed, 10 warnings in 0.33s ========================

**Planning escalated test execution**
**Designing comprehensive test script**
**Validating state consistency and key imports**
exec
/bin/zsh -lc "backend/.venv/bin/python - <<'PY'
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import types
from datetime import datetime, timezone
from pathlib import Path
import shutil

wt = Path.cwd()
sys.path.insert(0, str(wt / \"scripts\"))
import daily_review_pick as current
import daily_review_run as runner
import send_bark

baseline_source = subprocess.check_output(
    [\"git\", \"show\", \"worktree-feature-obsidian-hybrid-dev:scripts/daily_review_pick.py\"],
    cwd=wt,
    text=True,
)
baseline = types.ModuleType(\"baseline_daily_review_pick\")
baseline.__file__ = \"<git:worktree-feature-obsidian-hybrid-dev:scripts/daily_review_pick.py>\"
exec(compile(baseline_source, baseline.__file__, \"exec\"), baseline.__dict__)

now = datetime(2026, 7, 30, 1, 0, tzinfo=timezone.utc)

def node(board=\"普通板\", extra=\"\", body=\"真实内容。\"):
    return f'---\\ntype: concept\\nsource_board: \"[[原白板/{board}]]\"\\n{extra}---\\n{body}\\n'

with tempfile.TemporaryDirectory(prefix=\"card-a2-audit-\") as td:
    root = Path(td)
    vault = root / \"vault\"
    (vault / \"节点\").mkdir(parents=True)
    decay_dir = vault / \".claude\" / \"scripts\"
    decay_dir.mkdir(parents=True)
    shutil.copy(wt / \"canvas-vault\" / \".claude\" / \"scripts\" / \"decay_beta.py\", decay_dir)
    fixtures = {
        \"正常\": node(),
        \"未来\": node(extra=\"fsrs_due: 2026-08-15T01:00:00Z\\n\"),
        \"占位\": node(body=\"> 你的 1-2 句精准定义\"),
        \"无type\": '---\\nsource_board: \"[[原白板/B板]]\"\\n---\\n真实内容。\\n',
        \"孤儿\": \"---\\ntype: concept\\n---\\n真实内容。\\n\",
        \"TestConcept-伪节点\": node(),
        \"脏due\": node(extra=\"fsrs_due: 2026-07-29T01:00:00+08:00\\n\"),
        \"损坏\": node(extra=\"mastery_a: -3\\nmastery_b: 2\\n\"),
    }
    for name, content in fixtures.items():
        (vault / \"节点\" / f\"{name}.md\").write_text(content, encoding=\"utf-8\")

    decay = current.load_decay(vault)
    p2, ranked2 = baseline.build_payload(vault, now, {}, decay)
    p3, ranked3 = current.build_payload(vault, now, {}, decay)
    stripped = copy.deepcopy(p3)
    stripped.pop(\"due_nodes\")
    stripped.pop(\"ineligible\")
    stripped[\"schema_version\"] = 2
    print(json.dumps({
        \"existing_payload_fields_byte_equivalent_as_values\": stripped == p2,
        \"ranked_equivalent\": ranked3 == ranked2,
        \"v2_keys\": sorted(p2),
        \"v3_added_keys\": sorted(set(p3) - set(p2)),
        \"notification_equal\": p3[\"notification\"] == p2[\"notification\"],
        \"stats_equal\": p3[\"stats\"] == p2[\"stats\"],
    }, ensure_ascii=False))
    assert stripped == p2
    assert ranked3 == ranked2

    runner.VAULT = vault
    runner.STATE = root / \"daily-review.state.json\"
    runner.LOG = root / \"daily-review.log\"
    state = {\"schema_version\": 1, \"board_last_recommended\": {}}
    generated, first = runner.ensure_payload(state, now, now.date().isoformat())
    cached, second = runner.ensure_payload(state, now, now.date().isoformat())
    send_bark.KEY_FILE = root / \"definitely-absent-bark.key\"
    bark_rc = send_bark.send(generated[\"notification\"])
    print(json.dumps({
        \"runner_first\": first,
        \"runner_second\": second,
        \"cached_equal\": cached == generated,
        \"runner_schema\": generated[\"schema_version\"],
        \"bark_no_key_rc\": bark_rc,
        \"notification_keys\": sorted(generated[\"notification\"]),
    }, ensure_ascii=False))
    assert (first, second, bark_rc) == (\"new\", \"cached\", 2)
    assert cached == generated
PY" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
 succeeded in 0ms:
[pick] Beta 参数损坏跳过 损坏: Beta 参数必须为正: a=-3.0, b=2.0
[pick] fsrs_due 非规范格式, 视同到期: 脏due (2026-07-29T01:00:00+08:00)
[pick] Beta 参数损坏跳过 损坏: Beta 参数必须为正: a=-3.0, b=2.0
[pick] fsrs_due 非规范格式, 视同到期: 脏due (2026-07-29T01:00:00+08:00)
[pick] Beta 参数损坏跳过 损坏: Beta 参数必须为正: a=-3.0, b=2.0
[pick] fsrs_due 非规范格式, 视同到期: 脏due (2026-07-29T01:00:00+08:00)
{"existing_payload_fields_byte_equivalent_as_values": true, "ranked_equivalent": true, "v2_keys": ["date", "generated_at", "notification", "schema_version", "stats", "top_boards", "unassigned_nodes", "upcoming"], "v3_added_keys": ["due_nodes", "ineligible"], "notification_equal": true, "stats_equal": true}
bark skip(未配置) — 写入 ~/.config/canvas-review/bark.key 后启用
{"runner_first": "new", "runner_second": "cached", "cached_equal": true, "runner_schema": 3, "bark_no_key_rc": 2, "notification_keys": ["body", "group", "id", "title"]}

2026-08-24T15:42:48.529492Z ERROR codex_models_manager::manager: failed to refresh available models: timeout waiting for child process to exit
**Preparing async dashboard runtime execution**
**Simulating diverse runtime scenarios**
exec
/bin/zsh -lc "node -e '
const fs = require(\"fs\");
const source = fs.readFileSync(\"canvas-vault/Dashboard.md\", \"utf8\");
const code = source.split(\""'```dataviewjs")[1].split("```")[0];
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
class DVArray extends Array {
  where(fn) { return DVArray.from(Array.prototype.filter.call(this, fn)); }
  map(fn) { return DVArray.from(Array.prototype.map.call(this, fn)); }
  array() { return Array.from(this); }
}
async function run(name, loader) {
  const paragraphs = [];
  const dv = {
    pages: () => DVArray.from([]),
    io: { load: loader },
    paragraph: value => paragraphs.push(String(value)),
  };
  try {
    await new AsyncFunction("dv", code)(dv);
    return { name, status: "rendered", paragraphs };
  } catch (error) {
    return { name, status: "white-screen-exception", error: error.name + ":" + error.message, paragraphs };
  }
}
(async () => {
  const cases = [
    ["missing-undefined", async () => undefined],
    ["missing-throws", async () => { throw new Error("not found"); }],
    ["syntax-broken", async () => "{"],
    ["old-v2", async () => JSON.stringify({schema_version: 2, stats: {due_nodes: 6, ineligible: 8, unassigned: 1}, generated_at: "2026-08-24T09:05:00+08:00"})],
    ["v3", async () => JSON.stringify({schema_version: 3, due_nodes: [{fsrs_due: ""}, {fsrs_due: "2026-08-24T00:00:00Z"}], ineligible: {placeholder: ["占位"]}, stats: {due_nodes: 2, ineligible: 1, unassigned: 0}, generated_at: "2026-08-24T09:05:00+08:00"})],
    ["valid-empty-object", async () => "{}"],
    ["valid-array", async () => "[]"],
    ["wrong-due-type", async () => JSON.stringify({schema_version: 3, due_nodes: "oops", stats: {due_nodes: 9}, generated_at: "bad"})],
  ];
  for (const [name, loader] of cases) console.log(JSON.stringify(await run(name, loader), null, 0));
})().catch(error => { console.error(error); process.exit(1); });
'"'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
 succeeded in 0ms:
{"name":"missing-undefined","status":"rendered","paragraphs":["📊 **平均精通度**: `0.00` 🔴 起步\n\n📚 **节点总数**: `0`（暂无）\n\n⏰ **FSRS 到期**: ⏳ 投影未生成 — `outputs/今日复习.json` 缺失（每日复习任务每天 9:05 自动生成，生成后此处自动出数）\n\n🗂️ **原白板总数**: `0`"]}
{"name":"missing-throws","status":"rendered","paragraphs":["📊 **平均精通度**: `0.00` 🔴 起步\n\n📚 **节点总数**: `0`（暂无）\n\n⏰ **FSRS 到期**: ⚠️ 投影损坏 — `outputs/今日复习.json` 解析失败，等下次生成自动覆盖修复\n\n🗂️ **原白板总数**: `0`"]}
{"name":"syntax-broken","status":"rendered","paragraphs":["📊 **平均精通度**: `0.00` 🔴 起步\n\n📚 **节点总数**: `0`（暂无）\n\n⏰ **FSRS 到期**: ⚠️ 投影损坏 — `outputs/今日复习.json` 解析失败，等下次生成自动覆盖修复\n\n🗂️ **原白板总数**: `0`"]}
{"name":"old-v2","status":"rendered","paragraphs":["📊 **平均精通度**: `0.00` 🔴 起步\n\n📚 **节点总数**: `0`（暂无）\n\n⏰ **FSRS 到期**: `6`（待剖析积压 8 张另计 · 未归板 1 张另计 · 投影生成于 2026-08-24T09:05:00+08:00）\n\n🗂️ **原白板总数**: `0`"]}
{"name":"v3","status":"rendered","paragraphs":["📊 **平均精通度**: `0.00` 🔴 起步\n\n📚 **节点总数**: `0`（暂无）\n\n⏰ **FSRS 到期**: `2`（含 1 张新卡视同到期 · 待剖析积压 1 张另计 · 投影生成于 2026-08-24T09:05:00+08:00）\n\n🗂️ **原白板总数**: `0`","> 🗂️ **待剖析积压**（1 张占位节点，定义未写完不参与复习，不计入到期数）: [[节点/占位|占位]]"]}
{"name":"valid-empty-object","status":"rendered","paragraphs":["📊 **平均精通度**: `0.00` 🔴 起步\n\n📚 **节点总数**: `0`（暂无）\n\n⏰ **FSRS 到期**: `0`（待剖析积压 0 张另计 · 投影生成于 ?）\n\n🗂️ **原白板总数**: `0`"]}
{"name":"valid-array","status":"rendered","paragraphs":["📊 **平均精通度**: `0.00` 🔴 起步\n\n📚 **节点总数**: `0`（暂无）\n\n⏰ **FSRS 到期**: `0`（待剖析积压 0 张另计 · 投影生成于 ?）\n\n🗂️ **原白板总数**: `0`"]}
{"name":"wrong-due-type","status":"rendered","paragraphs":["📊 **平均精通度**: `0.00` 🔴 起步\n\n📚 **节点总数**: `0`（暂无）\n\n⏰ **FSRS 到期**: `9`（待剖析积压 0 张另计 · 投影生成于 bad）\n\n🗂️ **原白板总数**: `0`"]}

**Investigating NaN inclusion in due_nodes causing regression**
**Analyzing infinite decay_beta causing NaN picks and JSON errors**
**Planning pytest with huge number JSON validation**
codex
定向测试 13/13 通过，且基线/当前的既有 payload 字段在正常与五类口径夹具上逐值相同；runner 的 `new→cached` 和 Bark 无密钥分支也保持兼容。不过对抗轨发现一个不能被这 13 条测试捕获的候选回归：新增逐节点 `pick` 可能把非有限值写成裸 `NaN`，令 Dashboard 的 `JSON.parse` 失败。我正在用基线与当前实现独立复现并判级。
**Preparing minimal reproduction script**
exec
/bin/zsh -lc "nl -ba canvas-vault/.claude/scripts/decay_beta.py | sed -n '1,220p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
 succeeded in 0ms:
     1	"""批次2' A1 — 带遗忘因子的 Beta 后验 (衰减 Beta) 掌握度收敛算法。
     2	
     3	MEM-FLYWHEEL-2026-07-22, 对账 §2 合成方案 (2026-07-23 用户默认拍板):
     4	  - 纯 EMA (α=0.5 恒权) 不收敛: 考 100 次和考 3 次估计精度一样 → 已弃
     5	  - ChatGPT 纯 Beta 后验收敛但僵化: a,b 无限累计, 新证据边际影响趋零,
     6	    与「越考越准」矛盾 (非平稳性盲点) → 拒绝原版
     7	  - 合成: 每次观测前按 γ 打折 (有效记忆窗口 ~1/(1-γ)=10 次), 收敛且能
     8	    跟随掌握状态跳变; σ 解析可得, 不再拍脑袋探索项
     9	
    10	被四方共用 (单一真相源):
    11	  - quiz-answer SKILL 静态 python 段 (写分): update_after_idle / mu / from_legacy
    12	  - start-exam-board SKILL 选点段: pick_score (μ−β·σ, 低者优先考)
    13	  - scripts/daily_review_pick.py (每日推送选板): effective + pick_score
    14	  - backend/tests/regression/test_decay_beta_convergence.py (数学性质锁定)
    15	"""
    16	
    17	import math
    18	
    19	#: 先验 Beta(0.9, 2.1) — 均值 0.30 (与旧 EMA 默认档一致), 等效样本量 3
    20	#: (比 ChatGPT 提案的 2 稍保守, 抗首评噪声)
    21	PRIOR_A = 0.9
    22	PRIOR_B = 2.1
    23	
    24	#: 遗忘因子 — 每次观测前 a,b 同乘 γ, 有效记忆窗口 ~1/(1-γ) = 10 次观测
    25	GAMMA = 0.9
    26	
    27	#: 选点探索权重 (μ − β·σ)
    28	BETA_EXPLORE = 1.0
    29	
    30	#: 质量地板 — 防连续同质证据下 γ 打折把 a 或 b 衰减到零 (Beta(n,0) 退化
    31	#: 分布 σ=0, 「永远保留复习压力」承诺被破坏; 单测抓到的边界)。
    32	#: 代价: μ 上限从 1.0 降到 ~0.995, 可忽略。
    33	FLOOR = 0.05
    34	
    35	
    36	def update(a: float, b: float, grade_norm: float, gamma: float = GAMMA):
    37	    """一次评分观测: 先打折 (遗忘), 再累计证据。返回 (a', b')。"""
    38	    grade = max(0.0, min(1.0, float(grade_norm)))
    39	    a, b = gamma * a, gamma * b
    40	    return max(a + grade, FLOOR), max(b + (1.0 - grade), FLOOR)
    41	
    42	
    43	def mu(a: float, b: float) -> float:
    44	    """掌握度点估计 (Beta 均值)。"""
    45	    return a / (a + b)
    46	
    47	
    48	def sigma(a: float, b: float) -> float:
    49	    """掌握度不确定度 (Beta 标准差, 解析)。"""
    50	    n = a + b
    51	    return math.sqrt(a * b / (n * n * (n + 1.0)))
    52	
    53	
    54	def from_legacy(mastery_score: float, pseudo_n: float = 3.0):
    55	    """旧 EMA 的 mastery_score → 初始 (a, b)。
    56	
    57	    继承已有掌握度但只给等效样本量 3 的置信 (与先验同量级) — 老分数是
    58	    恒权 EMA 产物, 不配高置信。0/1 极端值钳到 0.05 防 σ 退化为零。
    59	    """
    60	    m = max(0.0, min(1.0, float(mastery_score)))
    61	    return max(0.05, m * pseudo_n), max(0.05, (1.0 - m) * pseudo_n)
    62	
    63	
    64	def pick_score(a: float, b: float, beta: float = BETA_EXPLORE) -> float:
    65	    """选点分 = μ − β·σ, 越低越优先考。
    66	
    67	    σ 项破解 P3 死循环 (旧逻辑 argmin μ 把最低分节点锁死循环考):
    68	    久考节点 σ 收窄退出竞争, 久不考节点被 γ 间接抬 σ 回到候选池。
    69	    """
    70	    return mu(a, b) - beta * sigma(a, b)
    71	
    72	
    73	#: 读时时效折扣 — 每闲置 1 天 a,b 同乘 γ_d。证据质量 n=a+b 半衰期 ≈69 天
    74	#: (0.99^69≈0.5)。σ 无统一半衰期: σ²=μ(1−μ)/(n·f+1), 随闲置向上限渐近
    75	#: 回升, 回升速度取决于节点已有证据量 (ChatGPT 终审 A1 口径, 2026-07-29)。
    76	GAMMA_DAILY = 0.99
    77	
    78	
    79	def effective(a: float, b: float, days_idle: float, gamma_daily: float = GAMMA_DAILY):
    80	    """读时时效: a,b 同比缩放 → μ 严格不变, σ 随闲置回升。纯读时, 不写回。
    81	
    82	    ⛔ 无 FLOOR — 逐坐标截断会破坏 a:b 比例使 μ 长期漂向 0.5 (先验
    83	    288 天起漂移, 双触底后被强改 0.50; 终审 A1)。存量 a,b 经 update()/
    84	    from_legacy() 恒 ≥ FLOOR>0, 同比缩放不产生无效 Beta 参数。
    85	    非正参数 = 数据损坏 → 抛错, 批处理调用方逐节点捕获跳过 (不崩全轮)。
    86	    """
    87	    a, b = float(a), float(b)
    88	    if a <= 0.0 or b <= 0.0:
    89	        raise ValueError(f"Beta 参数必须为正: a={a}, b={b}")
    90	    f = gamma_daily ** max(0.0, float(days_idle))
    91	    # 下溢防护 (Code-Review M2): 病理 last_examined (如年份打成 0001) 的
    92	    # 巨量天数会把 f 压到 0.0 → a=b=0 → pick_score 除零崩全轮。
    93	    # 同比下限不破「μ 不变」契约, σ 已到达上限附近。
    94	    f = max(f, 1e-150)
    95	    return a * f, b * f
    96	
    97	
    98	def update_after_idle(
    99	    a: float,
   100	    b: float,
   101	    grade_norm: float,
   102	    days_idle: float,
   103	    gamma: float = GAMMA,
   104	    gamma_daily: float = GAMMA_DAILY,
   105	):
   106	    """闲置感知评分: 先按闲置天数折旧旧证据, 再吸收新观测。
   107	
   108	    防「置信度复活」(终审 A2): 裸 update(原始 a,b) 会让闲置期抬高的 σ
   109	    被旧 n 一次评分瞬间抹平 — a=9,b=1 闲置 365 天答错, pick 反而
   110	    0.632→0.692 变得更不紧急。旧证据最终权重 γ·γ_d^d: 按次 + 按时
   111	    两层折扣机制不同, 有意复合 (非 double-discount 错误)。
   112	    """
   113	    a_eff, b_eff = effective(a, b, days_idle, gamma_daily)
   114	    return update(a_eff, b_eff, grade_norm, gamma)

exec
/bin/zsh -lc "nl -ba scripts/daily_review_pick.py | sed -n '220,365p'; nl -ba scripts/daily_review_run.py | sed -n '85,112p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
 succeeded in 0ms:
   220	
   221	
   222	def build_payload(vault: Path, now: datetime, board_last_recommended: dict, decay):
   223	    nodes, stats, ineligible = scan_nodes(vault, now, decay)
   224	    ranked, upcoming, unassigned = rank_boards(nodes, board_last_recommended)
   225	    stats["unassigned"] = len(unassigned)
   226	    # v3 (CARD-A2): due_nodes 明细与 stats 数字同源派生 — 自洽靠构造保证,
   227	    # 本投影是全系统到期口径唯一裁判 (Dashboard 只消费不重算)
   228	    due_rows = [
   229	        {
   230	            "node": n["node"],
   231	            "board": n["board"],
   232	            "state": n["state"],
   233	            "pick": round(n["pick"], 4),
   234	            "fsrs_due": n["fsrs_due"],           # 空串 = 新卡即刻到期
   235	            "last_examined": n["last_examined"],
   236	            "difficulty": n["difficulty"],
   237	        }
   238	        for n in nodes if n["board"] and n["due_now"]
   239	    ]
   240	    stats["due_nodes"] = len(due_rows)
   241	    stats["future_nodes"] = sum(1 for n in nodes if n["board"] and not n["due_now"])
   242	    payload = {
   243	        "unassigned_nodes": unassigned,  # Code-Review M3: 点名而非只给数字
   244	        "schema_version": 3,             # v3: +due_nodes 明细 +ineligible 分桶
   245	        #                                  (纯加性; v2: FSRS WHEN 化 upcoming/due 语义)
   246	        "date": now.astimezone().date().isoformat(),
   247	        "generated_at": now.astimezone().isoformat(timespec="seconds"),
   248	        "top_boards": ranked[:3],
   249	        "upcoming": upcoming[:3],
   250	        "due_nodes": due_rows,
   251	        "ineligible": ineligible,
   252	        "stats": stats,
   253	        "notification": None,
   254	    }
   255	    day_id = f"canvas-review-{payload['date']}"
   256	    if ranked:
   257	        payload["notification"] = {
   258	            "title": _title(ranked[0]["board"]),
   259	            "body": _body(ranked[0]),
   260	            "group": "canvas复习",
   261	            "id": day_id,
   262	        }
   263	    elif upcoming:
   264	        # F1 放假语义: 有调度中的板但今天零到期 → 诚实说不用复习
   265	        nxt = upcoming[0]
   266	        payload["notification"] = {
   267	            "title": "📚 今日无到期节点",
   268	            "body": f"按计划推进，休息一天 · 最近到期 {nxt['board']} · {nxt['next_due'][:10]}",
   269	            "group": "canvas复习",
   270	            "id": day_id,
   271	        }
   272	    return payload, ranked
   273	
   274	
   275	def render_md(payload, ranked) -> str:
   276	    s = payload["stats"]
   277	    lines = [
   278	        f"# 今日复习 · {payload['date']}",
   279	        "",
   280	        f"> 生成 {payload['generated_at']} · 到期={s['due_nodes']} / 未到期={s['future_nodes']}（不含未归板）"
   281	        f" · 节点状态: new={s['new']} / legacy={s['legacy']}"
   282	        f" / 无字段={s['none']} / 未剖析跳过={s['ineligible']} / 测试排除={s['test_excluded']}"
   283	        f" / 未归板={s['unassigned']} / 损坏={s['corrupt']}",
   284	        "",
   285	        "| 板 | 优先分 | 到期待复习 | 最该考 | 难度 | 闲置 | 板内下次到期 |",
   286	        "|---|---|---|---|---|---|---|",
   287	    ]
   288	    for r in ranked:
   289	        idle = "从未考" if r["idle_days"] is None else f"{r['idle_days']} 天"
   290	        nxt = r["next_due"][:10] if r["next_due"] else "-"
   291	        diff = r["difficulty"] or "-"
   292	        lines.append(
   293	            f"| {r['board']} | {r['priority']} | {r['pending']} | {r['top_node']} | {diff} | {idle} | {nxt} |"
   294	        )
   295	    if payload.get("upcoming"):
   296	        for u in payload["upcoming"]:
   297	            lines.append(f"| {u['board']} | - | 0（未到期） | - | - | - | {u['next_due'][:10]} |")
   298	    if ranked:
   299	        lines += ["", "## 一键开考（整行复制到 Claudian）", ""]
   300	        for r in ranked:
   301	            lines.append(f"- `/start-exam-board from {r['board']} node {r['top_node']}`")
   302	    else:
   303	        lines += ["", "> ✅ 今日无到期节点，休息一天。"]
   304	    if payload.get("unassigned_nodes"):
   305	        lines += ["", "> ⚠ 未归板节点（无 source_board，不参与推荐）: "
   306	                  + "、".join(payload["unassigned_nodes"])]
   307	    lines += [
   308	        "",
   309	        "> WHEN=FSRS 到期（无 fsrs_due 字段 = 新卡即刻到期）；WHAT=到期集合内按 μ−σ 排序",
   310	        "> （含闲置回升，证据质量半衰期 69 天）。未剖析占位节点已跳过；命令已绑定最该考节点。",
   311	    ]
   312	    return "\n".join(lines) + "\n"
   313	
   314	
   315	def atomic_write(path: Path, content: str):
   316	    tmp = path.with_suffix(path.suffix + ".tmp")
   317	    tmp.write_text(content, encoding="utf-8")
   318	    os.replace(tmp, path)
   319	
   320	
   321	def load_decay(vault: Path):
   322	    sys.path.insert(0, str(vault / ".claude" / "scripts"))
   323	    import decay_beta
   324	    return decay_beta
   325	
   326	
   327	def main():
   328	    ap = argparse.ArgumentParser(description="每日复习选板")
   329	    ap.add_argument("--vault", required=True)
   330	    ap.add_argument("--state", help="daily-review.state.json (只读, 取 board_last_recommended)")
   331	    ap.add_argument("--now", help="ISO 时间覆盖 (测试用)")
   332	    ap.add_argument("--write", action="store_true", help="写 outputs/今日复习.md+json")
   333	    args = ap.parse_args()
   334	
   335	    vault = Path(args.vault)
   336	    # 裸时间当本地时区, 与 daily_review_run.py 语义统一 (Code-Review L6)
   337	    if args.now:
   338	        dt = datetime.fromisoformat(args.now.replace("Z", "+00:00"))
   339	        now = dt if dt.tzinfo else dt.astimezone()
   340	    else:
   341	        now = datetime.now(timezone.utc)
   342	    blr = {}
   343	    if args.state and Path(args.state).exists():
   344	        try:
   345	            blr = json.loads(Path(args.state).read_text(encoding="utf-8")).get(
   346	                "board_last_recommended", {})
   347	        except (json.JSONDecodeError, OSError):
   348	            pass  # state 损坏由 runner 处置, 选点侧降级为无记录
   349	
   350	    payload, ranked = build_payload(vault, now, blr, load_decay(vault))
   351	    if args.write:
   352	        out = vault / "outputs"
   353	        out.mkdir(parents=True, exist_ok=True)
   354	        atomic_write(out / "今日复习.md", render_md(payload, ranked))
   355	        atomic_write(out / "今日复习.json",
   356	                     json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
   357	    print(json.dumps(payload, ensure_ascii=False))
   358	
   359	
   360	if __name__ == "__main__":
   361	    main()
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

exec
/bin/zsh -lc 'rg -n "isfinite|allow_nan|NaN|Infinity" scripts/daily_review_pick.py backend/tests/regression/test_daily_review_pick.py canvas-vault/.claude/scripts/decay_beta.py' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
 succeeded in 0ms:
backend/tests/regression/test_daily_review_pick.py:48:    assert all(r["priority"] == r["priority"] for r in ranked)  # 无 NaN

**Planning independent reproduction with escalation**
exec
/bin/zsh -lc "backend/.venv/bin/python - <<'PY'
from __future__ import annotations
import json
import math
import subprocess
import sys
import tempfile
import types
from datetime import datetime, timezone
from pathlib import Path
import shutil

wt = Path.cwd()
sys.path.insert(0, str(wt / \"scripts\"))
import daily_review_pick as current

source = subprocess.check_output(
    [\"git\", \"show\", \"worktree-feature-obsidian-hybrid-dev:scripts/daily_review_pick.py\"],
    cwd=wt,
    text=True,
)
baseline = types.ModuleType(\"baseline_daily_review_pick\")
baseline.__file__ = \"<baseline>\"
exec(compile(source, baseline.__file__, \"exec\"), baseline.__dict__)

with tempfile.TemporaryDirectory(prefix=\"card-a2-nan-\") as td:
    vault = Path(td) / \"vault\"
    (vault / \"节点\").mkdir(parents=True)
    scripts = vault / \".claude\" / \"scripts\"
    scripts.mkdir(parents=True)
    shutil.copy(wt / \"canvas-vault\" / \".claude\" / \"scripts\" / \"decay_beta.py\", scripts)
    normal = '---\\ntype: concept\\nsource_board: \"[[原白板/板]]\"\\nmastery_a: 2\\nmastery_b: 2\\n---\\n真实内容。\\n'
    huge = '---\\ntype: concept\\nsource_board: \"[[原白板/板]]\"\\nmastery_a: ' + (\"9\" * 400) + '\\nmastery_b: 2\\n---\\n真实内容。\\n'
    (vault / \"节点\" / \"a-normal.md\").write_text(normal, encoding=\"utf-8\")
    (vault / \"节点\" / \"z-huge.md\").write_text(huge, encoding=\"utf-8\")
    decay = current.load_decay(vault)
    now = datetime(2026, 7, 30, 1, 0, tzinfo=timezone.utc)
    old, old_ranked = baseline.build_payload(vault, now, {}, decay)
    new, new_ranked = current.build_payload(vault, now, {}, decay)
    strict = {}
    for name, payload in [(\"v2\", old), (\"v3\", new)]:
        try:
            json.dumps(payload, ensure_ascii=False, allow_nan=False)
            strict[name] = \"valid\"
        except ValueError as exc:
            strict[name] = type(exc).__name__ + \":\" + str(exc)
    serialized = json.dumps(new, ensure_ascii=False)
    print(json.dumps({
        \"old_top\": old_ranked[0][\"top_node\"],
        \"new_top\": new_ranked[0][\"top_node\"],
        \"new_due_picks\": [
            {\"node\": row[\"node\"], \"pick\": repr(row[\"pick\"]), \"finite\": math.isfinite(row[\"pick\"])}
            for row in new[\"due_nodes\"]
        ],
        \"strict_json\": strict,
        \"default_json_contains_bare_NaN\": \": NaN\" in serialized,
    }, ensure_ascii=False, indent=2))
PY" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
 succeeded in 0ms:
{
  "old_top": "a-normal",
  "new_top": "a-normal",
  "new_due_picks": [
    {
      "node": "a-normal",
      "pick": "0.2764",
      "finite": true
    },
    {
      "node": "z-huge",
      "pick": "nan",
      "finite": false
    }
  ],
  "strict_json": {
    "v2": "valid",
    "v3": "ValueError:Out of range float values are not JSON compliant: nan"
  },
  "default_json_contains_bare_NaN": true
}

**Assessing regression severity and impact**
**Labeling regression as high priority**
**Identifying edge cases with numeric inputs**
**Confirming JSON parse failure with NaN**
**Evaluating JSON schema validation and severity**
**Identifying mislabeled scheduled cards as new**
**Assessing dirty bucket handling inconsistency**
**Evaluating fail-open consistency on dirty timestamps**
**Confirming Dashboard parsing consistency**
**Assessing datetime validation limitations**
**Planning official Dataview docs search**
web search: 
web search: site:blacksmithgu.github.io/obsidian-dataview dv.io.load missing file returns undefined
**Confirming missing path requirement**
**Verifying test coverage and untracked files**
**Planning baseline test execution**
2026-08-24T15:45:53.529847Z ERROR codex_models_manager::manager: failed to refresh available models: timeout waiting for child process to exit
**Evaluating test coverage gaps**
**Assessing test gap severity on UTC handling**
**Clarifying test severity as medium**
**Assessing regression and schema corruption severity**
**Analyzing fail-open versus fail-closed consistency**
**Confirming no invalid calendar finding**
**Identifying need for schema version check**
**Planning independent schema corruption tests**
**Identifying datetime parsing edge cases**
2026-08-24T15:48:58.530779Z ERROR codex_models_manager::manager: failed to refresh available models: timeout waiting for child process to exit
**Planning full pytest run for coverage**
**Verifying notification compatibility and test details**
**Confirming test exclusion and bucket consistency**
**Planning test reproduction with pytest**
exec
/bin/zsh -lc "backend/.venv/bin/python - <<'PY'
from __future__ import annotations
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
import shutil

wt = Path.cwd()
sys.path.insert(0, str(wt / \"scripts\"))
import daily_review_pick as picker

with tempfile.TemporaryDirectory(prefix=\"card-a2-due-\") as td:
    vault = Path(td) / \"vault\"
    (vault / \"节点\").mkdir(parents=True)
    scripts = vault / \".claude\" / \"scripts\"
    scripts.mkdir(parents=True)
    shutil.copy(wt / \"canvas-vault\" / \".claude\" / \"scripts\" / \"decay_beta.py\", scripts)
    (vault / \"节点\" / \"坏日期.md\").write_text(
        '---\\ntype: concept\\nsource_board: \"[[原白板/板]]\"\\nfsrs_due: 2026-13-01T00:00:00Z\\n---\\n真实内容。\\n',
        encoding=\"utf-8\",
    )
    payload, ranked = picker.build_payload(
        vault,
        datetime(2026, 8, 24, tzinfo=timezone.utc),
        {},
        picker.load_decay(vault),
    )
    print(json.dumps({
        \"due_nodes\": payload[\"stats\"][\"due_nodes\"],
        \"future_nodes\": payload[\"stats\"][\"future_nodes\"],
        \"upcoming\": payload[\"upcoming\"],
        \"notification\": payload[\"notification\"],
        \"ranked\": ranked,
    }, ensure_ascii=False))
PY" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
 succeeded in 0ms:
{"due_nodes": 0, "future_nodes": 1, "upcoming": [{"board": "板", "next_due": "2026-13-01T00:00:00Z", "node": "坏日期"}], "notification": {"title": "📚 今日无到期节点", "body": "按计划推进，休息一天 · 最近到期 板 · 2026-13-01", "group": "canvas复习", "id": "canvas-review-2026-08-24"}, "ranked": []}

**Verifying test impact on repository state**
**Assessing NaN handling in JSON payloads**
**Analyzing schema version fallback behavior**
**Assessing writer damage severity**
**Evaluating test coverage completeness**
**Listing medium test coverage gaps**
**Identifying partial test coverage and missing push chain test**
**Planning targeted test sufficiency check**
exec
/bin/zsh -lc 'git diff --exit-code worktree-feature-obsidian-hybrid-dev -- scripts/daily_review_run.py scripts/send_bark.py scripts/daily-review-push.sh' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead

exec
/bin/zsh -lc 'git diff --numstat worktree-feature-obsidian-hybrid-dev -- backend/tests/regression/test_daily_review_pick.py canvas-vault/Dashboard.md scripts/daily_review_pick.py' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
76	0	backend/tests/regression/test_daily_review_pick.py
35	7	canvas-vault/Dashboard.md
36	5	scripts/daily_review_pick.py

exec
/bin/zsh -lc 'git status --short --branch' in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
 succeeded in 0ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
## card/a2-projection
 M backend/tests/regression/test_daily_review_pick.py
 M canvas-vault/Dashboard.md
 M scripts/daily_review_pick.py
?? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-A2.md"
?? "_bmad-output/\351\252\214\346\224\266\345\215\225/Story-CARD-A2-\345\244\215\344\271\240\345\210\260\346\234\237\345\217\243\345\276\204\347\273\237\344\270\200.md"

codex
已确认两条关键结论：正常有限输入下，v3 仅新增 `due_nodes`/`ineligible`，旧字段与 Bark 通知逐值不变；但异常输入暴露了真实回归——一个被旧版容忍的极端 Beta 节点会因新增 `due_nodes.pick = NaN` 让 Dashboard 投影永久降级。Dashboard 的缺失、语法损坏、v2 三条基本路径都能渲染，但“合法 JSON、结构损坏/未知版本”会被伪报成正常 `0` 或任意数字。现在只剩严重度与测试覆盖结论的交叉收敛。
并行三轨与主审反例已完成；正在交叉核验严重度并整理最终 finding 矩阵。
  ✓ 锁定 CARD-A2 验收口径、工作树基线与完整 diff 范围
  ✓ 并行审查 schema/推送链、Dashboard 降级语义、测试覆盖与回归
  ✓ 复现关键反例并运行相关测试/静态验证
  → 交叉核验 finding，输出分级结论与验证限制
**Planning exact memory line citation**
exec
/bin/zsh -lc "nl -ba /Users/Heishing/.codex/memories/MEMORY.md | sed -n '108,143p'; nl -ba /Users/Heishing/.codex/memories/skills/canvas-adversarial-audit/SKILL.md | sed -n '1,55p'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
 succeeded in 0ms:
   108	applies_to: cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output; reuse_rule=reuse the audit method and source handles for the same project family, but revalidate findings, SHA, CI, and live Neo4j state in the target checkout.
   109	
   110	## Task 1: P1-05c/P1-01/P1-08 parallel adversarial review, closure rejected
   111	
   112	### rollout_summary_files
   113	
   114	- rollout_summaries/2026-08-17T01-56-07-ZNCd-agents_guide_and_p1_05c_adversarial_audit.md (cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output, rollout_path=/Users/Heishing/.codex/sessions/2026/08/17/rollout-2026-08-17T09-56-07-01a00d6e-ea40-70a1-a23c-d51342eeeacd.jsonl, updated_at=2026-08-19T17:56:56+00:00, thread_id=01a00d6e-ea40-70a1-a23c-d51342eeeacd, outcome=partial; final read-only verdict)
   115	
   116	### keywords
   117	
   118	- P1-05c, P1-05, P1-01, P1-08, DD-03, check_vault_path, vault_index_orchestrator, LanceDB, Graphiti, DEFAULT_GROUP_ID, SnapshotV3, CURRENT_TASK.md, Dependency Audit, 32280954498
   119	
   120	## Task 2: P1-05b five-question adversarial audit, reproducible bypasses
   121	
   122	### rollout_summary_files
   123	
   124	- rollout_summaries/2026-08-19T14-44-08-upza-p1_05b_adversarial_review_finds_admission_quarantine_snapsho.md (cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output, rollout_path=/Users/Heishing/.codex/sessions/2026/08/19/rollout-2026-08-19T22-44-08-01a01a7a-c47f-70e2-8e5e-524e1591da78.jsonl, updated_at=2026-08-19T15:12:50+00:00, thread_id=01a01a7a-c47f-70e2-8e5e-524e1591da78, outcome=partial; detailed counterexamples, final report unfinished)
   125	
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
   141	- SnapshotV3 needs same-generation invalid/future-version self-healing, extra-field, strict-type, huge finite mastery, and identity/length collision coverage. Regenerate `CURRENT_TASK.md` from HEAD, Actions, and actual open items; targeted Python success was not whole-CI success. [Task 1]
   142	
   143	## Failures and how to do differently
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

**Aligning memory citations with rollout IDs**
**Summarizing failure findings in Chinese**
**Testing float overflow with 308 digits**
**Planning pure Python overflow test**
exec
/bin/zsh -lc "backend/.venv/bin/python -c 'import math,sys; sys.path.insert(0,\"canvas-vault/.claude/scripts\"); import decay_beta as d; a=float(\"9\"*308); p=d.pick_score(*d.effective(a,2.0,0.0)); print(repr(a), math.isfinite(a), repr(p), math.isfinite(p))'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
 succeeded in 0ms:
1e+308 True nan False

**Planning 308-digit baseline rerun**
**Planning v99 schema crosscheck rerun**
exec
/bin/zsh -lc "node -e '
const fs = require(\"fs\");
const source = fs.readFileSync(\"canvas-vault/Dashboard.md\", \"utf8\");
const code = source.split(\""'```dataviewjs")[1].split("```")[0];
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
class D extends Array { where(f){ return D.from(this.filter(f)); } map(f){ return D.from(Array.prototype.map.call(this,f)); } array(){ return Array.from(this); } }
async function run(payload) {
  const out = [];
  const dv = {pages:()=>D.from([]), io:{load:async()=>JSON.stringify(payload)}, paragraph:x=>out.push(String(x))};
  await new AsyncFunction("dv", code)(dv);
  return out[0].match(/⏰ '"\\*\\*FSRS 到期\\*\\*: (["'^'"\\n]+)/)?.[1];
}
(async()=>{
  console.log(JSON.stringify({
    malformed_v3: await run({schema_version:3, generated_at:\"2026-08-24T09:05:00+08:00\", stats:{}}),
    unknown_v99: await run({schema_version:99, generated_at:\"2026-08-24T09:05:00+08:00\", stats:{due_nodes:9,ineligible:4}})
  }, null, 2));
})().catch(e=>{console.error(e);process.exit(1)});
'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection
 succeeded in 0ms:
{
  "malformed_v3": "`0`（待剖析积压 0 张另计 · 投影生成于 2026-08-24T09:05:00+08:00）",
  "unknown_v99": "`9`（待剖析积压 4 张另计 · 投影生成于 2026-08-24T09:05:00+08:00）"
}

**Planning date comparison tests**
**Identifying test coverage gap for non-UTC dates**
**Finalizing agent completion status**
高严重度反例已由主审独立复现，结论与并行轨一致；报告整理完成。
  ✓ 锁定 CARD-A2 验收口径、工作树基线与完整 diff 范围
  ✓ 并行审查 schema/推送链、Dashboard 降级语义、测试覆盖与回归
  ✓ 复现关键反例并运行相关测试/静态验证
  ✓ 交叉核验 finding，输出分级结论与验证限制
**Planning detailed audit report structure**
**Clarifying medium severity findings and scope**
**Nuancing test coverage assessment**
**Assessing test coverage gaps**
**Verifying test pass and diff scope**
**Planning official doc citation**
**Confirming missing data handling and citation placement**
**Verifying numeric edge case serialization behavior**
**Analyzing schema version handling and UI due display**
**Confirming date handling logic**
**Assessing test coverage and mutation resilience**
**Evaluating runner and dashboard limitations**
**Confirming audit methodology compliance**
**Drafting final failure conclusion with findings**
**Planning inclusion of memory reference notes**
codex
结论：**FAIL — BLOCKER 0 / HIGH 2 / MEDIUM 3**，当前不能判 PASS。

## HIGH

1. **新增 `due_nodes.pick` 可把单个脏节点扩散成非法 JSON 回归**

   [daily_review_pick.py:61](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/scripts/daily_review_pick.py:61) 接受极大数值但未检查有限性；`:228-238` 将所有到期节点的 `pick` 写入 v3 明细。

   复现：正常节点加一个 `mastery_a≈1e308` 节点，后者产生 `pick=NaN`。基线 v2 严格 JSON 序列化成功；v3 严格序列化报 `ValueError`，默认落盘包含裸 `NaN`，Dashboard 的 `JSON.parse` 随即降级为“投影损坏”。

   这违反了“单脏节点不崩全轮”，也是本 diff 新引入的回归。

2. **结构损坏或未知 schema 被伪装成可信数字**

   [Dashboard.md:59](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/canvas-vault/Dashboard.md:59) 不校验 `schema_version` 或必需字段类型。

   实际执行该 dataviewjs 块：

   - v3 缺少 `due_nodes`、`stats={}` → 显示正常到期数 `0`
   - `schema_version=99`、`stats.due_nodes=9` → 显示 `9`

   没有白屏，但会产生更危险的“零到期”假象；损坏/不支持版本应进入明确降级路径。

## MEDIUM

1. **脏 due 被误报成新卡**

   [daily_review_pick.py:147](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/scripts/daily_review_pick.py:147) 把带偏移的脏值清成 `""`；[Dashboard.md:62](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/canvas-vault/Dashboard.md:62) 再以 `!d.fsrs_due` 统计“新卡”。到期总数一致，但已调度脏卡被错误分类为新卡；新增测试还在 `:185-186` 锁死了这一失真。

2. **fail-open 没覆盖形状正确但日期非法的 due**

   `fsrs_due: 2026-13-01T00:00:00Z` 通过正则后被词法判为未来。实测结果为 `due_nodes=0`、`future_nodes=1`，并生成“今日无到期”通知。此逻辑基线已存在，不是新回归，但 CARD-A2 仍未完整封闭脏值策略。

3. **新增测试只是部分验收守卫**

   [test_daily_review_pick.py:151](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/backend/tests/regression/test_daily_review_pick.py:151) 确实构造了五类代表节点，但固定 `NOW` 为 UTC，没有覆盖“本地时区当前时间 vs UTC due”的根因。

   `:199-210` 的“纯加性”测试也没有对照 v2 既有字段值，且未锁定 Bark 必需的 `notification.title/body/group`；隔离删除 `body` 后 13 条测试仍全绿，而 [send_bark.py:66](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/scripts/send_bark.py:66) 会实际抛 `KeyError`。

## 已确认通过

- 正常有限混合夹具下，旧字段值完全不变；新增键仅 `due_nodes`、`ineligible`，版本按要求 `2→3`。
- `daily_review_run.py`、`send_bark.py` 和 wrapper 相对基线零 diff；真实 `new→cached` 与 Bark 无密钥路径兼容 v3。
- Dashboard 的 FSRS 数字确实只消费投影；缺失、语法损坏、v2 三条基本路径均不白屏。官方契约也确认 `dv.io.load` 在文件缺失时返回 `undefined`。[Dataview API](https://blacksmithgu.github.io/obsidian-dataview/api/code-reference/)
- 定向 pytest：`13 passed`；`git diff --check`：PASS；机械 grep：`schedCnt|newCnt=0`、`今日复习.json=5`。

验证边界：未跑全量后端 CI、Obsidian GUI 或 Bark 网络发送；未读取 live vault。Dashboard 验证执行了实际首个 dataviewjs 块，但使用最小 `dv` 契约替身。两个未跟踪交付文档不属于 `git diff`，本审查未读取。


tokens used
149,208
结论：**FAIL — BLOCKER 0 / HIGH 2 / MEDIUM 3**，当前不能判 PASS。

## HIGH

1. **新增 `due_nodes.pick` 可把单个脏节点扩散成非法 JSON 回归**

   [daily_review_pick.py:61](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/scripts/daily_review_pick.py:61) 接受极大数值但未检查有限性；`:228-238` 将所有到期节点的 `pick` 写入 v3 明细。

   复现：正常节点加一个 `mastery_a≈1e308` 节点，后者产生 `pick=NaN`。基线 v2 严格 JSON 序列化成功；v3 严格序列化报 `ValueError`，默认落盘包含裸 `NaN`，Dashboard 的 `JSON.parse` 随即降级为“投影损坏”。

   这违反了“单脏节点不崩全轮”，也是本 diff 新引入的回归。

2. **结构损坏或未知 schema 被伪装成可信数字**

   [Dashboard.md:59](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/canvas-vault/Dashboard.md:59) 不校验 `schema_version` 或必需字段类型。

   实际执行该 dataviewjs 块：

   - v3 缺少 `due_nodes`、`stats={}` → 显示正常到期数 `0`
   - `schema_version=99`、`stats.due_nodes=9` → 显示 `9`

   没有白屏，但会产生更危险的“零到期”假象；损坏/不支持版本应进入明确降级路径。

## MEDIUM

1. **脏 due 被误报成新卡**

   [daily_review_pick.py:147](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/scripts/daily_review_pick.py:147) 把带偏移的脏值清成 `""`；[Dashboard.md:62](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/canvas-vault/Dashboard.md:62) 再以 `!d.fsrs_due` 统计“新卡”。到期总数一致，但已调度脏卡被错误分类为新卡；新增测试还在 `:185-186` 锁死了这一失真。

2. **fail-open 没覆盖形状正确但日期非法的 due**

   `fsrs_due: 2026-13-01T00:00:00Z` 通过正则后被词法判为未来。实测结果为 `due_nodes=0`、`future_nodes=1`，并生成“今日无到期”通知。此逻辑基线已存在，不是新回归，但 CARD-A2 仍未完整封闭脏值策略。

3. **新增测试只是部分验收守卫**

   [test_daily_review_pick.py:151](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/backend/tests/regression/test_daily_review_pick.py:151) 确实构造了五类代表节点，但固定 `NOW` 为 UTC，没有覆盖“本地时区当前时间 vs UTC due”的根因。

   `:199-210` 的“纯加性”测试也没有对照 v2 既有字段值，且未锁定 Bark 必需的 `notification.title/body/group`；隔离删除 `body` 后 13 条测试仍全绿，而 [send_bark.py:66](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a2-projection/scripts/send_bark.py:66) 会实际抛 `KeyError`。

## 已确认通过

- 正常有限混合夹具下，旧字段值完全不变；新增键仅 `due_nodes`、`ineligible`，版本按要求 `2→3`。
- `daily_review_run.py`、`send_bark.py` 和 wrapper 相对基线零 diff；真实 `new→cached` 与 Bark 无密钥路径兼容 v3。
- Dashboard 的 FSRS 数字确实只消费投影；缺失、语法损坏、v2 三条基本路径均不白屏。官方契约也确认 `dv.io.load` 在文件缺失时返回 `undefined`。[Dataview API](https://blacksmithgu.github.io/obsidian-dataview/api/code-reference/)
- 定向 pytest：`13 passed`；`git diff --check`：PASS；机械 grep：`schedCnt|newCnt=0`、`今日复习.json=5`。

验证边界：未跑全量后端 CI、Obsidian GUI 或 Bark 网络发送；未读取 live vault。Dashboard 验证执行了实际首个 dataviewjs 块，但使用最小 `dv` 契约替身。两个未跟踪交付文档不属于 `git diff`，本审查未读取。



---

# 附录 A：Finding 处置记录（Claude Fable 5，2026-08-24）

> 以上为 Codex (gpt-5.6-sol, ultra) 只读审查原文，裁决 FAIL — 0 BLOCKER / 2 HIGH / 3 MEDIUM。
> 以下为逐条处置。处置后重跑裁判命令：pytest 15 passed；grep schedCnt|newCnt == 0；grep 今日复习.json == 6；真实 vault 冒烟 schema=3、strict JSON (allow_nan=False) 序列化通过。

| # | 级别 | Finding | 处置 |
|---|---|---|---|
| H1 | HIGH | due_nodes.pick 可把单个 NaN 节点扩散成非法 JSON | ✅ 已修：scan_nodes 在 pick 计算后加 `math.isfinite` 检查，非有限值与其余脏数据同语义进 corrupt 桶（daily_review_pick.py）。新增回归测试 `test_nonfinite_pick_goes_corrupt_not_nan_json`（巨值 mastery 复现 + 全 payload `allow_nan=False` 严格序列化断言） |
| H2 | HIGH | Dashboard 不校验结构，损坏投影伪装成可信 "0 到期" | ✅ 已修：Dashboard 加结构校验（schema_version 为数字且 ≥2、due_nodes 数组或 stats.due_nodes 为数字，否则显式「投影结构异常」降级文案，不显示不可信数字）；未来版本 (sv>3) 渲染时标注「按 v3 口径解读」 |
| M1 | MEDIUM | fail-open 脏日期卡被 Dashboard 误计为新卡 | ✅ 已修：v3 明细新增 `due_reason` 字段（new/scheduled/malformed，v3 尚未 ship，属 schema 定版内加字段非破坏）；Dashboard 按 due_reason 分别显示「含 N 张新卡」与「脏日期按到期处理 N 张」 |
| M2 | MEDIUM | 形状正确但日历非法（月份 13）被词法误判成未来 | ✅ 已修：正则通过后再 strptime 校验日历合法性，非法即 fail-open 视同到期（脏值策略统一为一条），测试「非法日期」fixture 锁定 |
| M3 | MEDIUM | 测试守卫不足（本地时区根因未覆盖；notification 必需键未锁定） | ✅ 已修：新增 `test_due_boundary_survives_local_timezone_now`（+08:00 表示的 now 与 UTC due 词法边界不漂移）；加性契约测试补 notification title/body/group 非空断言（send_bark 直接下标访问的硬依赖） |

# 附录 B：前置三视角对抗验证（Claude 内部 workflow，Codex 审查前已跑）

3 个独立 agent 并行审 schema 加性 / Dashboard 降级 / 测试充分性：0 BLOCKER / 0 HIGH / 2 MEDIUM / 8 LOW。
两条 MEDIUM（未归板节点在 Dashboard 静默消失 → 已加「未归板 N 张另计」；due 边界未锁定 → 已加恰好==now 与 now+1h fixture）与 4 条 LOW（降级文案不可执行命令、wikilink 特殊字符坏链、脏 due 清空语义断言、空 vault 契约键）均在 Codex 审查前修复。
记录在案未修（评估为非缺陷或超出本卡范围）：
- ensure_payload 当日 sha 缓存使 v2 payload 存活到次日 9:05 — 非缺陷（Dashboard 有 v2 回退，数字不错，次日自愈）；live 部署步骤中包含「手动重新生成一次」即可当天见到 v3 明细
- 占位符+TEST_MARKERS 双命中分桶顺序未测试（当前 test_excluded 优先，未来重构守卫）
- OSError→corrupt 桶路径零覆盖（probe 已实证行为正确，纯测试缺口）
