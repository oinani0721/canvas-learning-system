> ⚠️ **2026-09-14 回填**：本稿是排批期设计快照，地盘逐文件清单以**手册 §一**为准（R-B14-4 / R-B14-8 扩充与错名更正已同步到手册）；下列 token 已按实测就地更正：`core/background_task_manager.py`→`services/`、`core/config.py`→`app/config.py`、`core/security.py`→`app/security.py`、`mcp/infra_tools.py`→`mcp/tools/infra_tools.py`、`core/learning_event_log.py`→`services/`、`backend/scripts/lifespan_isolation_runtime_sha.sh`→`backend/scripts/lifespan_isolation_runtime_sha.sh`、`.claude/skills/deploy-vault/SKILL.md`→`.claude/skills/deploy-vault/SKILL.md`。

# 第十四批设计稿（b14_design.md）— 写卡者与核验者的唯一输入

> 主 session 2026-09-11 产出。所有 file:line 取自主干 `286178d8` 的三份只读勘探（A/B/C，绝对路径见 §0.3）与波 0 实测；**波 0 未改任何勘探过的代码文件**（U6-C 改 `review_app.py`/`review_overview.py`/两 scripts/四测试；U1 改 `services/**`；U2 改 `models/**`/`api/**`/`mcp/**`/`core/**`/`pyrightconfig.json`）——凡卡文引用这些文件的行号，写卡者必须在 `B14_BASE` 树上 `sed -n` 复测（§0.1 给了树路径）。

## 0. 常量（写卡者逐字复制）

### 0.1 批次与树
- 批次 ID：`BATCH-2026-09-11-第十四批`；批次标记写法 `[BATCH-2026-09-11-第十四批 / CARD-<名>]`
- `B14_BASE`：**`081004834e37b1b0253cf81dc7b44e784646c934`**（feature 主干 HEAD；= 286178d8 + U6-C `c3912b42` + U1 `622f3a5d` + U2 `b4705dde` + U2 文档尾巴 `b11829b1` + U1 存档卫生 `08100483`；主 session ff 后与 origin/backup 同步）
- 主干树（`--add-dir` 那份，卡文/协议/手册/基线都在这里）：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev`
- 车道树：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t<N>-<name>`（分支 `card/t<N>-<name>`，全部 NEW @ `B14_BASE`；`backend/.venv` 目录级 symlink → `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv`；`backend/.env` 已拷）
- 手册：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-09-11-第十四批开跑手册-10车道43卡.md`
- 卡文目录：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十四批-goals/<块名>.md`
- 协议：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/.claude/rules/card-batch-protocol.md`（本批回写：§1 D-32 / §2.1 首部改「抄含版本行+model 行+reasoning 行」/ §2.2 ruff zsh 数组 + pyright 绝对路径 + 禁 `| tail -1` / §2.3 过渡保留到 T8-G + pyright 保持 0 / §3 W4 哨兵改绑 / §6 教训）
- pyright（⛔ 一律绝对路径 + `test -x` 自证；主干树 `backend/.venv` 软链指向主仓 venv、无 pyright，`cd backend && .venv/bin/pyright` 会 `no such file` 而 shell rc=0 = 假绿）：`P=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv/bin/pyright; test -x "$P" || { echo "pyright 缺席"; exit 1; }; "$P" app 2>&1 | grep -E '^[0-9]+ errors?, '`（禁 `| tail -1`：1.1.411 末行是升级提示）。`B14_BASE` 上 `pyright app` = **0 errors, 81 warnings**（`evidence-b14/pyright-app-after-u2-*.txt`）
- tests/unit 红基线（nodeid 口径，R-15 `--ignore tests/unit/test_deploy_vault_sh.py`）：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b14/unit-red-baseline-08100483.txt` = **64 条**（65 基线消失 1 = flaky `test_candidate_service.py::test_accept_candidate_already_accepted_returns_422`，新增 0）
- 其余基线：`tests/api` 268 passed / `tests/skills` 546 passed / `tests/regression` 1674 passed（`evidence-b14/reg-integ-*.txt`）/ `tests/contract` **三个非 schemathesis 文件**（`test_openapi_snapshot_drift.py` `test_node_id_patterns.py` `test_health_contract.py`，`-q --hypothesis-seed=0`）= 75 passed / **2 failed 主干既有**（`test_node_id_patterns.py::TestNodeIdPatternConsistency::test_pattern_matches_json_schema`、`test_health_contract.py::test_health_contract[GET /api/v1/health]`，286178d8 同红，`evidence-b14/contract-2files-on-trunk-*.txt`）；⛔ `-k setup-wizard` 定向在 U5-D 后恒零收集（rc=5）、`test_openapi_contract.py`（schemathesis 167 op，每 op 数分钟、首 op `GET /api/v1/health` FAILED）与目录级（pact provider）都不可作候选树裁判——T5-D 开工首项定性 schemathesis 首 op FAILED 与 `test_health_contract` 红，T10-E 顺带定性 `test_pattern_matches_json_schema`
- D-15 固定串（长度门 ⑨，短 goal 与卡文都必含）：`Codex gpt-6-astra ultra 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0`
- 收尾口令：`复核第十四批 T<N>`
- 长度门 ⑪ 禁旧口径字面量（卡文与短 goal 都不得含）：`:1281`、`mutation_kill_identity.py:203`、`stale-mock`、`cd backend && .venv/bin/pyright`、`gpt-5.6`
- 长度门 ⑩：触及 `backend/app` 的卡文必含句「pyright 保持 0」（APP_CARDS 见 §4 各卡「app」标）

### 0.2 本批纪律（写进每张卡 §三 / 手册 §零）
1. **pyright 规则（取代 D-16 甲「禁顺手修存量」）**：`B14_BASE` 上 `pyright app` = 0，语义车道**必须保持 0**——hook `python-typecheck` 正常拦，本卡新增的 error 由本卡自己清（ignore 需带 `# pyright: ignore[rule]  # <一行理由>`），**不得 `LEFTHOOK_EXCLUDE=python-typecheck`**；协议 §2.3 过渡条款只对主干既有 ruff-format 462 文件漂移（`python-lint` 的 `ruff format --check`）保留到 T8-G，用时必贴被跳过门原始输出 + 「格式漂移不在本卡改动行」证明（`ruff format --check` 只对本卡 diff 文件跑，dirty 集 ⊆ 主干既有）。
2. **ruff 判据 zsh 数组写法**（协议 §2.2）：`F=(${(f)"$(git diff --name-only --diff-filter=AM B14_BASE HEAD -- 'backend/**/*.py')"}); print -r -- "files=${#F}"; (( ${#F} )) || exit 1; ruff check -- "${F[@]}"; echo rc=$?`；验伪锚：喂一个已知含 F401 的文件必须 rc=1。
3. **判据 grep git 输出一律 `--no-color`** + 同次验伪锚；evidence `.txt` 不 `.log`；末行 `rc=$pipestatus[1]`（zsh）。
4. **W4 哨兵判据**绑 `blocked=` 次数 + 失败正文 `('::1', 7691, 0, 0) on thread MainThread`，不绑 nodeid（协议 §3）。
5. **批中禁装工具**（不往共享 venv 装/升任何包）；批级环境变更走协议 §2.3 通告。
6. **本批部署卡 = T2-B**：真 `docker compose up -d` 需用户**当次授权**；未授权即 SKIP 并如实登记。`fsrs_bridge.py` / `decay_beta.py` ⛔ 零写者；live vault / 7691 / 现网 LanceDB 只读。
7. **主干脏项不动**（107 项：`.gdr/**`、`research-pack` 删除、四份历史手册 M、`Session N：…` 未命名文件、`board_manifest_last_run.json` 等，非本批产物）。
8. **GATE 末位**：T8-G 全批最后合；T8-F TAIL 代码部分（ignore 注解）叠在语义之上。
9. **D-32**：纯注释/docstring 尾巴不占轮次不重置，主 session 逐行等价核。
10. 台账只主 session 改；卡在验收单写「台账待登记条目」；`*.stderr*` 不入库；commit header ≤100 含批次标记、body 行 ≤100；不 push。
11. 同车道严格串行：前一卡独立 commit + `git status --porcelain` 空后才粘下一块；每卡各自验收单 `UAT-CARD-<名>-<日期>.md` 与 Codex 存档 `codex-review-CARD-<名>-rN.md`。
12. **每卡 commit 带卡号**（commit message 含 `CARD-<名>`），避免第十三批「整车道 diff|apply」的卡级 revert 不可用。

### 0.3 勘探素材（写卡者必读，按卡索引在 §4）
- A 遗留清单：`/private/tmp/claude-501/-Users-Heishing-Desktop-canvas-canvas-learning-system--claude-worktrees-feature-obsidian-hybrid-dev--bmad-output/8634f5a8-fdf8-4332-8c06-f9468d6878fa/scratchpad/recon_A_report.md`（§A 第二波 / §B.1~B.5 候选卡 / §C 裁决 / §D 矛盾）
- B 主 goal 依赖：同目录 `recon_B_report.md`（§A 依赖表 / §B 最短路径 / §C HOST-PROBE 摘要 / §D G2-8 改写 / §E 矛盾）
- C 代码锚点：同目录 `recon_C_report.md`（§1 G2-9-F2 / §2 U8-C / §3 mutkill-R3 / §4 G6-9c-R2 / §5 U7-A HIGH-1 / §6 deploy timeout / §7 RED 三节 / §8 pyright 基线 / §9 红基线 / §10 U9-C / §11 U11-A Neo4j / §12 协议回写 / §13 deploy-vault.sh / §14 Y4-D 尾巴 / 末表 9 处不一致）
- 波 0 证据：`…/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b14/`
- 其它来源（绝对路径前缀 `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/`）：裁定书 `feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b13-integ/RULINGS-2026-09-10.md`；台账 `…/goal-cards/未合卡追踪台账.md`；红对齐 `feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b13/red-align-da690bf8.md`（MOCKFIX `:250` / ENVDEP `:284` / 部署线 `:292` / Y4-D `:375`）；HOST-PROBE `feature-obsidian-hybrid-dev/_bmad-output/研究/2026-09-08-HOST-PROBE-宿主实测表.md`（§三.7 / §三.10 / §四）；U1 TAIL `feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-pyright-svc/TAIL-handover.txt` + U1 验收单 `feature-obsidian-hybrid-dev/_bmad-output/验收单/UAT-CARD-PYRIGHT-DEBT-services-2026-09-08.md`（§十六.2 三条回写建议、§二十.2 三处注释、§十三/§十四 T-new-7/8）；U2 `feature-obsidian-hybrid-dev/_bmad-output/审查/U2-台账待登记-阶段1-2026-09-08.md` §五 + `U2-阶段2-merge挂起-交接主session-2026-09-11.md` + 验收单 `UAT-CARD-PYRIGHT-DEBT-rest-2026-09-11-v2.md`（§6.5 r3 四 LOW）；U11 审计 `card-u11-red-c/_bmad-output/审查/evidence-resilience-audit/VERDICT-merged-2026-09-09.md`；G2-9-F1 裁定请求 `feature-obsidian-hybrid-dev/_bmad-output/审查/CARD-G2-9-F1-裁定请求.md:60-78`；G2-8 原卡文 `…/goal-cards/2026-08-28-主goal全量分goal总账-v2.md:600-605`；第十三批卡文 `…/goal-cards/第十三批-goals/U8-C.md`（T8-A 原样复用）/ `U2-B.md`（T8-G 基底）/ `U5-A.md` `U6-C.md` `U3-C.md` `U4-A.md`（格式与地盘参考）；U6-C 验收单 `feature-obsidian-hybrid-dev/_bmad-output/验收单/UAT-CARD-G6-6-2026-09-09.md`（§六 16/28、:365/:457/:496/:505）；U7 `card-u7-w4guard/_bmad-output/验收单/UAT-CARD-RV-W4-4-2026-09-08.md` / `UAT-CARD-W4-4b-*.md:268-281` / `UAT-CARD-W4-7-*.md:160/:205/:320/:403` + `evidence-w44b/ast-must-flag.patch`；U8 `card-u8-mutgates/_bmad-output/验收单/UAT-CARD-DEBT-mutkill-R2-2026-09-08.md`（§5.1 :80-91 / :343）+ `UAT-CARD-RV-W4-5:136/:196/:212`；U3 `UAT-CARD-G2-7a-2026-09-09.md:114/:296/:305/:327/:333/:334` / `UAT-CARD-G2-7b-2026-09-09.md:57/:366/:367/:395/:408/:454/:474/:633/:780` / `evidence-g27a/manifest-ruling.md`；U5 `UAT-CARD-G3-3-R2:228/:239/:346` / `UAT-CARD-RED-R:62/:93` / `UAT-CARD-HYGIENE-openapi:649/:663/:698/:720`；U4 `UAT-CARD-SKILL-PORT-LINT:203/:398/:1699`；U9 `UAT-CARD-G3-7-R2:172/:174/:262/:280/:283/:288` / `UAT-CARD-G3-5-2026-09-09.md:18/:37/:216/:349/:375/:441`；U10 `UAT-CARD-RED-E:284/:302` / `UAT-CARD-RED-A2:177/:183/:187` / `UAT-CARD-RED-A1-sentinel:504/:588` / `UAT-CARD-HYGIENE-conftest:897/:1004`；U11 `UAT-CARD-RED-C1:205/:217/:220` / `UAT-CARD-RED-NEW:323/:425/:444/:445/:474/:475`。

## 1. 车道表（10 车道 43 卡，同车道严格串行，全部从 B14_BASE 切）

| 车道 | worktree / 分支 | 卡（串行） | 工时 |
|---|---|---|---|
| T1 lance | `card-t1-lance` / `card/t1-lance` | A CARD-G2-9-F2 → B CARD-G2-9-F1-canary | 6+2 |
| T2 deploy | `card-t2-deploy` / `card/t2-deploy` | A CARD-DEPLOY-TIMEOUT → B CARD-G2-8 → C CARD-HOSTS-OPENCODE → D CARD-HOSTS-CODEX → E CARD-G2-7b-TAIL | 2+6+4+4+3 |
| T3 review-time | `card-t3-review` / `card/t3-review` | A CARD-G6-9c-R2 → B CARD-G6-8 → C CARD-G6-9b → D CARD-U6C-HANDOVER | 4+5+3+3 |
| T4 g3+canary | `card-t4-g3` / `card/t4-g3` | A CARD-G3-9 → B CARD-G6-10 → C CARD-U9B-OPENSPEC → D CARD-U9C-EVAL | 5+4+2+2 |
| T5 bugs+security | `card-t5-bugs` / `card/t5-bugs` | A CARD-TAIL-CLEANUP-LOOP → B CARD-T-EDGES → C CARD-T-SWITCHVAULT → D CARD-SEC-DANGLING → E CARD-T-UNREACH | 2+3+2+4+2 |
| T6 neo4j-replay | `card-t6-neo4j` / `card/t6-neo4j` | A CARD-NEO4J-REPLAY-CENSUS → B CARD-NEO4J-REPLAY-WIRE → C CARD-NEO4J-REPLAY-BOUND | 3+6+3 |
| T7 skills-writer | `card-t7-skills` / `card/t7-skills` | A CARD-HARNESS-TREE-PARSE-REDO → B CARD-AILINKED-4TH-WRITER → C CARD-SKILL-PORT-LINT-PARSER → D CARD-G2-7a-TAIL | 4+4+3+3 |
| T8 tools+GATE | `card-t8-tools` / `card/t8-tools` | A CARD-TOOL-residue-fail-open → B CARD-DEBT-mutkill-R3 → C CARD-EXPECT-LOC-NARROW → D CARD-AST-FLAG-PATCH → E CARD-TOOLCHAIN-UNIFY → F CARD-PYRIGHT-TAIL → G CARD-PYRIGHT-GATE | 2+4+3+2+2+3+1 |
| T9 w4-guard | `card-t9-w4` / `card/t9-w4` | A CARD-W4-FINAL-ACCOUNTING → B CARD-W4-4b7-TAIL → C CARD-W4-SENTINEL-REBIND → D CARD-RUNTIME-SHA-SURFACE | 2+4+3+3 |
| T10 red-tests | `card-t10-red` / `card/t10-red` | A CARD-RED-MOCKFIX → B CARD-RED-ENVDEP → C CARD-Y4-D-TAIL → D CARD-EPW-COVERAGE → E CARD-RED-HYGIENE | 4+1+3+5+3 |

合计 43 卡 ≈ 139h；最长 T2 19h（E 可退第十五批）、T8 17h、T10 16h。（计划表写「42 卡 ≈150h」为合计误写，逐格实数 43 / 139。）

## 2. 合并队列（主 session 逐卡 squash；每合一条重算 merge-tree）
1. 零代码/纯文档：T6-A → T4-D → T8-F（census 部分）。
2. 数据面与工具面（不碰 `backend/app` 生产）：T1-A → T1-B → T2-A → T2-B → T2-C → T2-D → T2-E → T7-D → T7-A → T7-B → T7-C → T8-A → T8-B → T8-C → T8-D → T8-E → T9-A → T9-B → T9-C → T9-D → T10-A → T10-B → T10-C → T10-D → T10-E → T4-B。
3. `backend/app` 语义写者：T5-A → T5-B → T5-C → T5-E → T5-D（openapi 变）→ T6-B → T6-C → T3-A → T3-B → T3-C → T3-D → T4-A → T4-C → 主 session 再生 `openapi.json`。
4. 末位：T8-F 代码部分 → pyright `app` = 0 门 → **T8-G GATE 全批最后**。
硬序对子：T8-A→T8-G；T8-B→T8-C；T2-A→T2-B→T2-C/D→T2-E；T3-A→T3-B→T3-C；T6-A→T6-B→T6-C；T9-A→T9-B；T10-A→T10-C→T10-D；全部→T8-F→T8-G。

## 3. 地盘互斥（逐文件；违反 = 集成冲突）
- 只 T1：`backend/lib/agentic_rag/clients/lancedb_client.py`、`backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py`、`backend/scripts/g29_dual_vault_canary.py`。
- 只 T2：`scripts/deploy-vault.sh`、`backend/tests/unit/test_deploy_vault_sh.py`、`scripts/vault-install-manifest.json`、`.claude/skills/deploy-vault/SKILL.md`、`scripts/cls_forbidden_paths.py`、`backend/tests/unit/test_docker_compose_config.py`、`docker-compose*.yml`（只读核，改动须登记）。
- 只 T3：`backend/app/core/display_tz.py`、`scripts/local_tz.py`、`backend/app/api/v1/endpoints/review_overview.py`、`backend/app/api/v1/endpoints/review_app.py`、`canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py`、`canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py`、`backend/tests/unit/test_review_overview.py`、`test_review_app.py`、`backend/tests/regression/test_daily_review_run.py`（T4 G6-8/G6-10 只读比对，新测试落 T4 自己的新文件）。
- 只 T4：`scripts/daily_review_pick.py`、`backend/tests/regression/test_daily_review_pick.py`、`openspec/specs/concept-identity/**`、`_bmad-output/…/A6-phase0-reference-card.md`、`backend/tests/regression/test_g3_7_truth_source.py`、新对账脚本 `backend/scripts/g39_three_view_reconcile.py`、新 canary `backend/scripts/g610_dual_vault_interaction_canary.py`。
- 只 T5：`backend/app/services/background_task_manager.py`、`backend/app/config.py`（只加 `TASK_CLEANUP_INTERVAL_SECONDS` 一项）、`backend/app/api/v1/endpoints/edges.py`、`backend/app/mcp/tools/infra_tools.py`（勘探写 `mcp/infra_tools.py`，开工 `find` 实测真路径）、`backend/app/security.py`、`backend/app/api/v1/system.py`、`backend/app/api/v1/endpoints/boards.py`、`backend/app/mcp/tools/board_manifest_tools.py`、`backend/tests/contract/test_openapi_contract.py`。
- 只 T6：`backend/app/services/memory_service.py`、`backend/app/services/fallback_sync_service.py`、`backend/app/core/failure_counters.py`、`backend/app/api/v1/endpoints/traces.py`、`backend/app/core/failed_writes_constants.py`。
- **`backend/app/main.py` 声明交集**：T5-D 只改 `:568` security 段；T6-B 只改 `:386-404` 回填门段（两卡各自 diff 不得越出各自行段；集成期主 session 核 hunk 不重叠）。
- 只 T7：`canvas-vault/.claude/skills/quiz-answer/SKILL.md`、`canvas-vault/.claude/skills/ai-linked-doc/**`、`backend/app/services/learning_event_log.py`（第四写者边界）、`backend/tests/skills/test_skill_portability_lint.py`、`canvas-vault/.claude/skills/start-exam-board/SKILL.md`、`scripts/verify_vault_install.py`（T7-D）。
- 只 T8：`lefthook.yml`、`backend/scripts/mutation_kill_identity.py`、`backend/scripts/g32b_mutation_gates.py`、`g32cb_mutation_gates.py`、`g32ccr1_negative_controls.py`、`g33_mutation_gates.py`、`backend/scripts/lifespan_isolation_negative_control.py`、`package.json`、`package-lock.json`、`ruff.toml`、`pyrightconfig.json`、协议 §2.3（T8-G 出 patch 交主 session）。
- 只 T9：`backend/tests/support/live_port_guard.py`、`backend/tests/support/guard_plugin.py`、`backend/tests/conftest.py`、`backend/tests/unit/conftest.py`、`backend/scripts/lifespan_isolation_runtime_sha.sh`（T10 禁 autouse、禁改任何 conftest）。
- 只 T10：`backend/tests/unit/test_memory_service_batch.py`、`test_story_30_11_batch_parallel.py`、`test_story_30_13_batch_idempotency.py`、`test_agent_service_extraction.py`、`test_graphiti_json_dual_write.py`、`test_story_38_6_scoring_reliability.py`、`backend/tests/api/v1/endpoints/test_agents_health.py`、`backend/tests/api/.../test_sync_batch_auth.py`、`test_system_endpoint_auth.py`、`backend/requirements.txt`（只加 `pytest-mock`）、新 `backend/tests/unit/test_episode_worker_coverage_epw.py`。
- `backend/openapi.json` 声明交集（T5-D 会变；集成期主 session 再生两次）；`backend/app/models/**` 零写者；`fsrs_bridge.py` / `decay_beta.py` ⛔ 零写者。

## 4. 每卡骨架（写卡者按此扩成完整卡文；★ 标「app」= 触及 backend/app，卡文必含「pyright 保持 0」）

### T1-A CARD-G2-9-F2（首张 · 数据丢失面 · 6h）
- 源：C §1（全部锚：`resolve_table_name:768-798`（`:796`）/ `_owns_table:841-904`（`:904`）/ `_fingerprint_table_name:1065-1081`（`:1081` 拼接侧）/ `drop_vault_tables:937-948`（`:946-947` 吞异常）/ `_cache_tables:1020-1056`；`startswith(f"{vid}_")` 恰 2 处；缺陷锁装饰器 2 处 `:491`/`:505`（nodeid 6）；前提门 1 函数 `:464` × 6）；A B.1 首行 + F2 顺带项（UAT-G2-9-F1 :672/:673/:783/:812）；裁定请求 `:60-78`；R-01。
- 做：拿全量 vault 列表做**最长前缀优先**归属，三处同口径一张卡；修好后删 `:491`/`:505` xfail 标记，前提门 `:464` 改为新口径断言（XPASS 三成因 (1)(2)(3) 逐条分辨写进验收单）；顺带 B-3 指纹夹具真 schema / A-4 B-9 docstring / `:3825` 自愈链；`drop_vault_tables:946` 吞异常改「记账不吞」（返回值或日志含被吞的表名，单测钉）。
- 判据：C §1.5 四条 + F2 后 `grep -cF 'startswith(f"{vid}_")'` = 0 + 前提门/缺陷锁翻转（先跑改前：2 标记 XFAIL；改后：标记删除、新断言绿）+ 双 vault 真库门（`a` / `a_b` 互前缀，各自初始化不删对方）+ `tests/unit` 目录级 diff 只 `<`。
- 口径更正：装饰器 2 ≠ nodeid 6；vault 列表来源必须写明（`.canvas-config.yaml` 枚举 / `vaults_root` 目录 / LanceDB 表名反推三选一并证明）。
- 禁改：`backend/app/**`（不触发 typecheck，但也不许碰）；`test_rag_stage1_index_contracts.py`（源码门保留 `endswith`/`FINGERPRINT_TABLE` 字面量）。
- 不排：现网 LanceDB 备份对账（D-41 需授权）。

### T1-B CARD-G2-9-F1-canary（2h）
- 源：A B.1「CARD-G2-9-F1-canary」（UAT-G2-9-F1 :779）；U5-A 卡文 (e)（`side_effect_probe` 条件键 + 守卫 `:1415-1416`）。
- 做：F2 之后完整 canary 复跑，含 (e) 守卫真跑（`--probe-schema-drift` 开/关两态各一跑，`verdict` PASS 与 rc 对照）；跑前跑后 `g29_dual_vault_canary.py` sha 相同；报告落 `evidence-g29f1-canary/`。零生产改动（若发现缺陷停下登记，不修）。
- 判据：两态 rc + `verdict` 键 + 「B 表在 A init 后仍在」；禁连 7691。

### T2-A CARD-DEPLOY-TIMEOUT（R-15 · 2h）
- 源：C §6（AST：20 处 `subprocess.run`，带 timeout 4 = 77/462/1873/2447，裸跑 16；`grep -c timeout=` = 5 ≠ AST；`deploy-vault.sh:549` `npm run build` 无超时上限；步 5 curl `-m 10` `:1139`）；R-15；A B.3「U3 挂起小卡」。
- 做：16 处裸跑全部加 `timeout=`（helper 化，单一常量）；`deploy-vault.sh:549` 加超时（`timeout` 命令 macOS 缺席 → 用 `perl -e alarm` 或 bash 后台 + `wait`/`kill` 形态，写明）与 preflight 上限 + 离线标志（`npm_config_offline=true` 或 `--offline`）；挂起根因定位（在 evidence 里给出 npm 等网证据或证伪）。
- 判据：AST 判据 `WITHOUT=0`（C §6.4）；`grep -nE 'npm run build'` 行带超时包裹；`test_deploy_vault_sh.py` 文件级单跑全绿 + 墙钟上限；主 session 复跑 unit 时撤 `--ignore`。
- 禁改：步 5/6 语义（T2-B 面）。

### T2-B CARD-G2-8（改写版 · 6h · 本批唯一部署卡）
- 源：B §D（改写一段，整段语义照抄进卡文 §〇）；C §13（六步 `:389/:639/:684/:969/:1060/:1159`、真 activate 桩 `:1118-1157`、`up -d` `:1121`、回滚 `:1126/:1145`、curl `:1139`、`--also-push` `:32`/`:1175` 只解析不实现、`CLS_DEPLOY_ALLOW_DOCKER_UP` 闸门 `:1114-1117`）；原卡文 总账 `:600-605`（只取「阶段/journal/Lance 计时/Graphiti readiness/UAT 提示」结构，**语义按决策页 §一替换**：activate = 起/重建**该 vault 自己的** `cls-<vault>` 实例，不顶别的 vault；失败回滚 = 拆掉本 vault 的 compose 项目，别的实例一动不动）；UAT-G2-7b `:57`（`canvas-vault` 名口径缺口）/ `:366` / `:367`。
- 做：只包裹步 5 `:1060-1157` 与步 6，步 1~4 只复用；补 index journal 隔离 / Lance 首索引计时 / Graphiti readiness `skipped-with-reason`（禁假成功）；实现 `--also-push`（追加 `DAILY_REVIEW_VAULTS` 去重、不动 `ACTIVE_VAULT`）；收 `canvas-vault` 名口径缺口；真 `up -d` **需用户当次授权**（卡文写「未授权即 SKIP 并如实登记，SKIP 不算失败但验收单必须标『真 activate 未执行』」）。
- 判据：注入 health 超时后 `cls-<vault>` down 干净 **且** 另一个已在跑实例端口仍 200（用 dry/桩两态；真态仅授权后）；分阶段可审计日志 `rc=`；`bash -n`；`test_deploy_vault_sh.py` 全绿；禁写面负控（`cls_forbidden_paths.py`）不变。
- 禁改：`backend/app/**`；live vault；`ACTIVE_VAULT`。

### T2-C CARD-HOSTS-OPENCODE（4h · 静态绑定件）
- 源：B §A `--hosts opencode` 行 + §C OpenCode 行；HOST-PROBE §四 / §三.10（D-26(i) 漏 `opencode.jsonc` + `.gitignore`）；A B.5「二线宿主转正」；用户裁：只生成静态绑定件（`.agents/skills` 软链 + `AGENTS.md`）不跑模型；D-26(i) 不放宽并补覆盖面。
- 做：`deploy-vault.sh` 步 3 生成 `.agents/skills`（条目级软链，指向 `.claude/skills/<name>`）+ `AGENTS.md`（含 skills 清单与 MCP `opencode.json` 指引）；manifest 登记；D-26(i) 硬禁面补 `~/.config/opencode/opencode.jsonc` 与 `.gitignore`；静态判据：软链目标存在、frontmatter `name` == 目录名（复用 SKILL-PORT-LINT 层 1）。
- 判据：`--hosts claude,opencode` dry 跑后文件树断言；跑前跑后 D-26(i) 四+二文件 sha 相同；不跑 OpenCode 模型（无凭据）。
- 禁改：`~/.config/opencode/**`（硬禁）；`backend/app/**`。

### T2-D CARD-HOSTS-CODEX（4h · read-only 形态）
- 源：B §A `--hosts codex` 行 + §C Codex 行；HOST-PROBE §三.7（workspace-write 写 `~/.codex/config.toml` trust 表 ⇒ D-26(i) 冲突）；用户裁 D-33：`--sandbox read-only`，**不写** trust 表；HOST-PROBE 提醒：只采信 `--json` 事件流。
- 做：生成 `.codex/`（项目级 MCP 条目模板，不写用户级 config）+ `AGENTS.md`（与 T2-C 共用文件时追加段落，不重写）；负控：`~/.codex/config.toml` 跑前跑后 sha **相同**；探针只用 `codex exec --sandbox read-only --json`，事件流零 `command_execution` 即判「未执行」。
- 判据：sha 相同（承重）；生成物存在；`--json` 事件解析落盘。
- 禁改：`~/.codex/**`；`backend/app/**`。

### T2-E CARD-G2-7b-TAIL（3h · 可退第十五批）
- 源：A B.5「G2-7b 转下一卡（5 项）」（UAT-G2-7b `:395/:408/:454/:474/:633/:780`）。
- 做：目标漂移负控（`src="$VAULT"` 仍 `content-drift=0` 的反例先红）；`mktemp + O_EXCL + rename` 改写；rc 表主张补全（顶层失败不走 `run_step` / 成功报告前五行）；`ancestor_symlink_hits` 独立门；M-1~M-5。
- 判据：每项「改前反例红 / 改后绿」对照 + `bash -n` + `test_deploy_vault_sh.py` 全绿。

### T3-A CARD-G6-9c-R2（★app · 4h）
- 源：C §4（3 HIGH 原文 + 主干锚：`_in_dst` 三年窗 `local_tz.py:176` / `display_tz.py:175`；`dst` 无规则退 UTC `:133`/`:132`（`return None` → `display_tz.py:262` UTC）；固定偏移回退 `review_overview.py:541`；两 TZ 文件与 U6 车道逐字节同，`review_overview.py` sha 不同）；R-03。
- 做：`_in_dst` 候选窗改为按规则实际滚入年（含跨年季度）；`dst` 有而规则省略 → 用 libc 默认规则（`time.tzset`/`zoneinfo` 推导写明）不退 UTC；`:541` 固定偏移回退双向堵（误拒与误放行都钉）；门⑦ 加闰年/年界样本（≥2 个非 2026 年时刻）。
- 判据：三条 HIGH 各一条先红后绿；两文件同源（diff 逻辑段相同）；`tests/unit/test_review_overview.py` + `test_vault_lint.py`（monkeypatch 目标）绿；pyright 保持 0。
- 口径更正：不得写「三文件与 U6 车道一致」。

### T3-B CARD-G6-8（★app · 5h）
- 源：B §A G6-8 行（依赖 G6-6 已合 = 波 0）+ 总账 `:774-778`；A B.4。
- 做：五面一致性契约套件（`review_overview.py` / `review_app.py` / `daily_review_pick.py`（只读）/ 两 skill 脚本 / 推送 payload）：同一 state 输入下五面的桶位/日期/snooze/done 结论逐字段相等；可重跑脚本 `backend/scripts/g68_five_view_contract.py` + `tests/regression/test_g68_five_view_contract.py`。
- 判据：五面矩阵全等；负控：篡改一面必红；pyright 保持 0。
- 禁改：`daily_review_pick.py`（T4 地盘，只读）。

### T3-C CARD-G6-9b（★app · 3h）
- 源：B §A G6-9b 行（`review_overview.py:2089` `runner.state_path()`、`:2228` `json.loads(state_file…)`；runner state `last_result`/`last_error` `daily_review_run.py:655,:661-662`；`grep -c degraded review_overview.py` = 0）；A B.4。
- 做：`/overview` JSON 加 `push_degraded` + `last_error`；`_card_html` 徽标；源 = runner state；无 state 时字段为 `null` 不报错。
- 判据：state 三态（成功/失败/缺失）各一条 API 测试 + HTML 含徽标；openapi 再生由主 session；pyright 保持 0。

### T3-D CARD-U6C-HANDOVER（★app · 3h）
- 源：A B.4「U6-C 移交面（3 项）」（UAT-G6-6 `:457/:496/:505`、§六 16/28、`:365` LOW-1）；A D-10（不得归 U1/U2）；D-37（三个产品口径按现状确认不改）。
- 做：① `due_crossed` 缺判型（同 `if` 并列项、同款 TypeError、先于本卡判型求值）；② 父子进程各读一次墙钟跨午夜分日（`_display_today()` vs `build_payload` 隔一次 spawn）→ 统一由父进程传 `--now`/`--today`；③ `snoozeKey`/`doneKey` NUL 反向碰撞；④ Codex 找到的 3 颗既有哑弹 `:1365/:3533/:1093`（U6-C 验收单点名）逐条定性修或登记。
- 判据：每项先红后绿（午夜跨日用钉钟两侧）；`test_daily_review_run.py` 目录级绿；pyright 保持 0。

### T4-A CARD-G3-9（5h · 含用户 mini-UAT）
- 源：B §A G3-9 行（依赖齐；G3-5 走甲已合，读甲支键；UAT-G3-5 `:37/:349` 甲乙分歧未裁 → 本卡按甲）；总账 `:756-761`。
- 做：picker / Dashboard / 总览三面对账脚本 `backend/scripts/g39_three_view_reconcile.py`（只读三面，输出差异表）；**用户 hands-on mini-UAT**（约 30 分钟；验收单段 4-B「我做 X → 我看到 Y → 我感觉 Z」，主 session 陪跑窗口）。
- 判据：对账脚本对 live 只读跑一次落盘（禁写）；三面零差异或差异逐条归因；mini-UAT 勾选记录。
- 禁改：`review_overview.py`/`review_app.py`（T3）；只改 `daily_review_pick.py` 读侧与对账脚本。

### T4-B CARD-G6-10（4h）
- 源：B §A G6-10 行 + §B N=8 第 8；总账。
- 做：双 vault 交互隔离 canary `backend/scripts/g610_dual_vault_interaction_canary.py` + 7692 真库门：A 库 snooze/done 对 B 库零影响（state 文件 per-vault、Neo4j group 隔离）；不写生产端点。
- 判据：canary rc + 门先红（人为共享 state）后绿；禁 7691。

### T4-C CARD-U9B-OPENSPEC（2h · 产品动作）
- 源：A B.5「U9-B OpenSpec 产品动作」（UAT-G3-7-R2 `:172/:174/:262/:280`）+「两处裸名字」（`:283/:288`）；R-07。
- 做：`openspec/specs/concept-identity/spec.md` 悬空 Requirement → 默认补一条替代 Requirement（带 `#### Scenario:` 四井号）让 `npx openspec archive` 过；`A6-phase0-reference-card.md:96` / `test_g3_7_truth_source.py:14` 两处裸名字更正；`ConceptState.fsrs_*` 标注只登记（`models/**` 零写者）。
- 判据：`npx openspec validate --strict` PASS；archive dry 过；两处 grep 归零。

### T4-D CARD-U9C-EVAL（2h · 评估卡 · 零生产改动）
- 源：C §10（抛出点 `:573`/`:596` 在 `__init__` 内；生产唯一构造点 `:2978` HTTP 依赖链；`scripts/` 0 命中）；R-07；D-38。
- 做：前提改写为「启动后首个 `get_review_service()` 请求拒启」；落评估文档 + 一条口径测试钉「进程不崩、请求 500 带 CARD-G3-5 消息」；legacy 兼容重做不排（设计级）。
- 判据：测试绿；C §10.4 三条 grep。

### T5-A CARD-TAIL-CLEANUP-LOOP（★app · 2h）
- 源：A B.1「T-new-4」（`background_task_manager.py:350` `Settings` 无 `TASK_CLEANUP_INTERVAL_SECONDS` ⇒ 恒 AttributeError 且 `while True` 无退避 = 忙循环）；TAIL-handover §A；R-10「最高优先」。
- 做：`Settings` 加 `TASK_CLEANUP_INTERVAL_SECONDS`（默认值写明依据）+ 循环退避（异常分支 `await asyncio.sleep(backoff)`）；测试证明不再忙循环（计数一秒内迭代次数上限）。
- 判据：先红（忙循环计数爆）后绿；pyright 保持 0。

### T5-B CARD-T-EDGES（★app · 3h）
- 源：A B.1「T-EDGES」（`edges.py:106` 调不存在的 `execute_query`，真名 `run_query(**params)`；except 不含 AttributeError ⇒ 500 非 207）；U2 §五；D-39（7692 测试容器，禁 7691）。
- 做：改 `run_query(**params)`；except 加 AttributeError；207 vs 500 真测试走 7692。
- 判据：先红（500）后绿（207）；pyright 保持 0；openapi 不变（主 session 核）。

### T5-C CARD-T-SWITCHVAULT（★app · 2h）
- 源：A B.1「T-SWITCHVAULT」（`infra_tools.py:56/57` 读 `JSONResponse.vault_name` 恒失败）；U2 §五。
- 做：解析 `JSONResponse.body`（json.loads）；MCP 工具真测试（`tests/unit` 内用 TestClient）。
- 判据：先红后绿；pyright 保持 0。

### T5-D CARD-SEC-DANGLING（★app · 4h · openapi 变）
- 源：A B.3「悬空 security 引用（OPEN）」（U0 17 → HEAD 31；`/system/*` 2 → 16；`main.py:568` / `security.py`）；UAT-RED-A1-sentinel `:504/:588`；R-08。
- 做：31 处悬空 `APIKeyHeader` 引用 → 方案名统一为 `InternalApiKey`（改 `security.py` 定义或 `main.py:568` 注册，二选一写明）；openapi 再生由主 session；`test_openapi_contract.py` 加「securitySchemes ⊇ 所有 per-op security 名」断言。
- 判据：悬空数 0（脚本统计）；contract 三文件 `-q --hypothesis-seed=0`（禁 `-k setup-wizard`：恒零收集）+ 开工首项：单跑 `test_openapi_contract.py` 的 `GET /api/v1/health` op 与 `test_health_contract[GET /api/v1/health]` 定性其主干既有 FAILED（波 0 实测，登记不阻断，若是本卡面则修）；pyright 保持 0；`main.py` 只改 `:568` 段（T6 交集声明）。

### T5-E CARD-T-UNREACH（★app · 2h）
- 源：A B.1「T-UNREACH」（`boards.py:86` / `board_manifest_tools.py:67` `except pydantic.ValidationError` 死分支，ValidationError 是 ValueError 子类）；U2 §五。
- 做：先 census（两处上游 except 顺序）再调顺序，带测试证明 ValidationError 走到宣称的 500 兜底；行为变化写进验收单。
- 判据：先红后绿；pyright 保持 0。

### T6-A CARD-NEO4J-REPLAY-CENSUS（3h · 零代码）
- 源：C §11（四条暂存链；两孤儿 `sync_all_fallbacks:54`/`recover_failed_writes:2679`；`main.py:386` 门；`failed_edge_syncs.jsonl` 5 处零回灌）；U11 审计 VERDICT `:22/:25/:26/:33-37/:38/:108/:146/:148`；R-09；A B.1。
- 做：四条链逐条写侧/读侧/回灌/有界表；现网 `.env` `ENABLE_GRAPHITI_JSON_DUAL_WRITE` 实测取值（只读）；产出处置表「接通 / 退役」交 T6-B/C。
- 判据：C §11.5 三条 grep；文档落 `_bmad-output/审查/2026-09-1x-NEO4J-REPLAY-CENSUS.md`。

### T6-B CARD-NEO4J-REPLAY-WIRE（★app · 6h）
- 源：T6-A 处置表；C §11。
- 做：把 `sync_all_fallbacks:54` 接进真实路径：Neo4j 恢复探测触发 + 管理端点（鉴权同 `/system/*` 口径）；`main.py:386` 门改「离线也登记待回灌」（只改 `:386-404` 段）；回灌幂等 7692 门；DD-03 禁 mock。
- 判据：离线写 → 恢复 → 回灌 → 图内可查 的端到端门（7692）；重复回灌幂等；pyright 保持 0；openapi 由主 session 再生。

### T6-C CARD-NEO4J-REPLAY-BOUND（★app · 3h）
- 源：C §11.2（无界坟场）；A B.1。
- 做：四文件有界（上限/轮转，常量入 Settings）+ `/traces` 暴露积压数与最老时间。
- 判据：超限轮转测试；`/traces` 字段测试；pyright 保持 0。

### T7-A CARD-HARNESS-TREE-PARSE-REDO（4h）
- 源：A B.1「CARD-HARNESS-TREE-PARSE-REDO」（UAT-G3-3-R2 `:239`「⛔ 第十四批必排」/ `:346`「设计级」）；U3-B 定义的 `harness_tree` 字段（`.canvas-config.yaml` 2.1）。
- 做：`quiz-answer/SKILL.md`（与相关脚本）里 `_harness_tree` 解析整体重做：`yaml.safe_load` 优先，正则降级只收一种写法，其余 fail-closed；翻转用例（既有 xfail → 去标）。
- 判据：`tests/skills` 目录级绿 + SKILL-PORT-LINT 基线（若指纹变，T7-C 同批更新基线并声明）。

### T7-B CARD-AILINKED-4TH-WRITER（4h）
- 源：A B.1「CARD-AILINKED-4TH-WRITER」（UAT-G3-3-R2 `:228`：`derive:A` 被 `derive:AB` 子串匹配 ⇒ 事件永久丢失 / 无锁 / 无 LF 守卫 / 无形态门）；R-07 同族。
- 做：写点精确匹配（token 边界）；文件锁（与 U6-B 同款 flock 语义）；LF 守卫；形态门（写点普查门纳入第四写者）。
- 判据：子串反例先红后绿；并发写测试；LF 断言。

### T7-C CARD-SKILL-PORT-LINT-PARSER（3h）
- 源：A B.3「CARD-SKILL-PORT-LINT-PARSER + regression 解耦卡」（UAT-SKILL-PORT-LINT `:203/:398/:1699`）。
- 做：lint 解析器另立模块；`start-exam-board` 裸 `/tmp/` 4→2；`:430/:435` 归 `tests/regression` 解耦。
- 判据：`tests/skills` 546+ 绿；基线指纹更新与理由；负控：伪造一处 `/tmp/` 必红。

### T7-D CARD-G2-7a-TAIL（3h）
- 源：A B.5「G2-7a 转下一卡（4 项）」（UAT-G2-7a `:114/:296/:305/:327/:333/:334`）；D-34（`outputs/**` exclude 语义本批不动）。
- 做：**先修** MEDIUM-2：hotkeys 为无写端 FIFO 时 `open` 阻塞（`os.open(O_NONBLOCK)` + `S_ISFIFO` 拒）；CLAUDE_MD 骨架更新；平台限定（macOS/APFS）文案；`outputs/**` 三条出路留 `evidence-g27a/manifest-ruling.md` 不动语义。
- 判据：FIFO 反例（`mkfifo`）改前挂起（带超时的探针）改后 rc≠0 即返；`verify_vault_install.py` 既有门全绿。

### T8-A CARD-TOOL-residue-fail-open（U8-C 原卡复用 · 2h）
- 源：`第十三批-goals/U8-C.md` 原样复用（把 banner 的批次/车道/前提/协议路径改为本批；正文 §〇~§四 保留）；C §2（补 (e)：g32b 注释 153→151 也过时，`lefthook.yml:312`；基线仍 5 文件 151/11/11/2/13；`.claude/rules/*.md` 三份均不含字面量）。
- 判据：U8-C §二 原判据 + C §2.6 ③「注释数字对账 151/11」。

### T8-B CARD-DEBT-mutkill-R3（4h）
- 源：C §3（H1 落点 `:211` `if not cands:`，`_split_unique` `:188-213`；H2 `:697`；3 MEDIUM 原文；四套六档现状：g32b 只注释无活代码）；UAT-DEBT-mutkill-R2 §5.1 `:80-91` / `:343`；R-12。
- 做：H1 无 reason 读法进候选集（读法空间穷举写进 docstring）；H2 弱位置禁跨门借位（`_loc_identity` 无 `expect_loc` 时也核「所有失败 nodeid 属目标门」）；3 MEDIUM：锚漂移报 HARNESS-ERROR / g33 末次还原失败不吞 / 处置表六档核对。
- 判据：C §3.6 三条锚 + 每条 HIGH/MEDIUM 一条反例先红后绿 + 四套 `--list` 落盘 + 变异跑前跑后 sha。
- 禁：写死 `:203`。

### T8-C CARD-EXPECT-LOC-NARROW（3h）
- 源：D-28（手册 §四.5）；A B.2「expect_loc 三套尾巴卡」（UAT-DEBT-mutkill-R2 `:265/:298`）；C §3.4。
- 做：g32cb 9 / g32ccr1 11 / g33 18 的 `expect_loc` 收窄；弱位置判据挡住 Y1-B HIGH-1 反例。
- 判据：三套 `--list` 前后对照 + 反例 KILLED→非 KILLED 翻转。

### T8-D CARD-AST-FLAG-PATCH（2h）
- 源：A B.2「`_AST_MUST_FLAG` patch 套用」（UAT-DEBT-mutkill-R2 `:295`）+「MEDIUM-6①」（UAT-RV-W4-5 `:136/:196/:212`，`:634` 四轮上限无未收敛分支）；U7 `evidence-w44b/ast-must-flag.patch`。
- 做：套用 patch 到 `lifespan_isolation_negative_control.py`（`git apply --check` 先）；`:634` 加「未收敛」处置分支（显式报错不静默）。
- 判据：patch 干净套用 + 该脚本自测 + 未收敛反例先红后绿。

### T8-E CARD-TOOLCHAIN-UNIFY（2h）
- 源：A B.2「工具链统一卡」（lefthook 三版本：npx 1.13.6 / brew 2.1.6 / package-lock；`scripts/` ruff `select` 空）；台账 X8③/Z7-A。
- 做：`package.json`/`package-lock.json` 的 lefthook 版本对齐 brew 2.1.6（或反向，写明）；`ruff.toml` 给 `scripts/` 补 `select`；不升级 brew（批中禁装）。
- 判据：`/opt/homebrew/bin/lefthook version` 与 `npx lefthook version` 同；`ruff check scripts/` 基线落盘（新增 0）。

### T8-F CARD-PYRIGHT-TAIL（3h · census 为主）
- 源：A B.5「PYRIGHT-TAIL 主卡」+ B.1「T-new-1/2/3/5/6」「T1/T14」；TAIL-handover §A/§B/§C；U1 验收单 §十六.2（三条回写：PHASE0_PENDING 启发式误归 / 禁 `| tail -1` / 死路径「或·和」拆条）、§二十.2（三处注释：M-2 / L-1 / L-3）、T-new-7（`learning_context_service.py:205`）/ T-new-8（`multimodal_service.py:1427`）；U2 §五（T-GATE-GAP / `pyrightconfig` src 死枝 / `dependencies.py:1032` 冗余 ignore / `backend/tests` 1350 + 仓根 `tests/` 168 只登记）；U2 r3 LOW-1（`exam_service.py` 命名空间：`logging` 属性消失、`TYPE_CHECKING=False`）；D-35（T-new-2 / T14 / T1 只 census 不改）；**波 0 实测：候选树 `pyright app` = 0，无残余 ignore**。
- 做：逐条 census 表（编号 / 文件:行 / 性质 / 消费方 / 处置：本批改 or 第十五批立卡）；只改注释类（三处注释措辞 + `exam_service.py` TYPE_CHECKING 注释）；`pyrightconfig` src 死枝清；`dependencies.py:1032` 冗余 ignore 删（pyright 仍 0）；行为变化项一律不改。
- 判据：`pyright app` 保持 0（绝对路径）；census 表落 `_bmad-output/审查/2026-09-1x-PYRIGHT-TAIL-census.md`；`ruff` 数组写法自证。

### T8-G CARD-PYRIGHT-GATE（U2-B 基底 · 1h · 全批最后合）
- 源：`第十三批-goals/U2-B.md`（协议 §2.3 过渡改回硬禁 + lefthook glob 只核 + TAIL 清单）；R-14；波 0 §0.2.1 新规则。
- 做：协议 §2.3 过渡条款改回硬禁（`python-typecheck` 已硬；`python-lint` 的 ruff-format 462 漂移条款 → 改「第十五批末位主 session 单独一 commit 整仓 format（D-40）」）；lefthook `python-typecheck` glob 只核不改（出 patch 交主 session）；TAIL 清单指向 T8-F census。
- 判据：协议 diff 只在 §2.3；零代码；1 轮 Codex。

### T9-A CARD-W4-FINAL-ACCOUNTING（2h）
- 源：C §5（`:1512` print 在 `:1522-1534` 保护块外；`:1535` `os._exit`；三跑对照 A/B/C）；R-11。
- 做：`:1512` 移入 `except BaseException` 保护块（或同型 try）；AST 判据「`_final_accounting` 内每个 print 都在 `except BaseException` try 内」（C §5.4 脚本，`B14_BASE` 上输出 `1512 ⛔ UNPROTECTED`，修后两行 protected）；三跑对照 A/B/C 全 rc=3。
- 禁：写 `:1281`。

### T9-B CARD-W4-4b7-TAIL（4h）
- 源：A B.2「W4-4b / W4-7 转下一卡项」（UAT-W4-4b `:268-281`；UAT-W4-7 `:160/:205/:320/:403`）。
- 做：白名单门间接调用形态 + 失败文案收窄；seam 门 `while True: break` 死语句；顺序门可达剪枝（不止 `if False`）；`_publish_ledger` docstring 收窄；LOW-3a（未拒未知参数）。
- 判据：每项反例先红后绿；`tests/unit -k live_port_guard` 与 guard 自测绿。

### T9-C CARD-W4-SENTINEL-REBIND（3h）
- 源：C §12.1（U1 §五.9-ter 转述 U10-A：五轮 `blocked=12` 恒定、失败正文恒 `('::1', 7691, 0, 0) on thread MainThread`、nodeid 归属同代码翻转）；A B.3「U10-A 移交微卡」（conftest 快照 None↔hash 不区分「变了」与「没查完」）；R-08/R-10。
- 做：判据改绑 `blocked=` 次数 + 失败正文（脚本化）；`backend/tests/unit/conftest.py` 快照 None↔hash 区分（三态：unchanged / changed / unchecked）；协议 §3 已写，本卡落工具。
- 判据：同代码两跑 nodeid 翻转而新判据不变（复现 r4/r4b）；conftest 三态测试。
- 口径：主干 `B14_BASE` 候选树 unit 跑 `blocked=0`（`NEO4J_LIVE_PORT_CONNECT_ATTEMPTS` 未设）——「恒 12」是设了攻击次数的口径，卡文写明两态。

### T9-D CARD-RUNTIME-SHA-SURFACE（3h）
- 源：A B.2「W4 扫描面 T-1 / T-13 / T-15」（`lancedb_pending_index__*.jsonl` / `*_with_status` 兼容壳扫 / `neo4j_memory.json` `llm_call_logs.db`）+「SHELLOPTS=noexec 假绿」（台账 Y7-B）。
- 做：三面进 `runtime_sha.sh` 监视；`SHELLOPTS=noexec` 假绿修（脚本自证真执行）。
- 判据：注入三面变更必红；`SHELLOPTS=noexec` 下必 rc≠0。

### T10-A CARD-RED-MOCKFIX（4h）
- 源：C §7.1（27 条 nodeid 原样；统一失败身份 `MagicMock` await @ `memory_service.py:381`；31 条全裸红无 skip）；A D-3 + D-30（分母 38 vs 27 → 开卡前在 `B14_BASE` 重清一次，两方数字都不沿用）；红对齐 `:250-280`。
- 做：开卡前用 `B14_BASE` 基线文件重清（`grep memory_service.py:381` 身份）定分母；测试侧 `AsyncMock` 替换（**不改生产** `memory_service.py:381`）；3 条「修好后必须重看」（`test_neo4j_disconnected_still_stores_in_memory` / `test_neo4j_unavailable_still_processes_to_memory` / `test_neo4j_unavailable_fallback`）逐条定性。
- 判据：`tests/unit` 目录级 diff 只 `<`（基线 §0.1）；三文件绿；禁改 conftest。

### T10-B CARD-RED-ENVDEP（1h）
- 源：C §7.2（3 条：`fixture 'mocker' not found` ×2 + 读真 `.env` ×1）；UAT-RED-A2 `:177`。
- 做：`pytest-mock` 进 `backend/requirements.txt`（**不往共享 venv 装**——若 venv 缺 `pytest_mock`，测试用 `pytest.importorskip` 兜底并登记为批级通告候选）；`_settings_factory` 各档不读真 `.env`。
- 判据：3 条转绿或 importorskip 明示；diff 只 `<`。

### T10-C CARD-Y4-D-TAIL（3h）
- 源：C §14（4 条原绿：`test_graphiti_json_dual_write.py:33` 模块级 / `test_story_38_6_scoring_reliability.py:162` 类级；可搜锚 `_write_to_graphiti_json`）；红对齐 `:375`；台账 Y4-D 行（wrapper 5 瑕疵）。
- 做：wrapper 5 瑕疵；4 条按 EpisodeWorker 管线重写恢复；删 `:33` 模块级 / `:162` 类级 skip。
- 判据：C §14.5 三条 grep 各减；4 条绿；禁锚 `stale-mock`。

### T10-D CARD-EPW-COVERAGE（5h）
- 源：A B.3「CARD-EPW-COVERAGE」（UAT-RED-C1 `:217`；33 + 4 nodeid；5 条 xfail 的 reason 已写卡 ID，**不可改名**）。
- 做：GraphitiEpisodeWorker 等价覆盖（新文件 `test_episode_worker_coverage_epw.py`）；5 条 xfail 翻转去标。
- 判据：xfail→XPASS→去标；覆盖矩阵落盘。

### T10-E CARD-RED-HYGIENE（3h）
- 源：A B.3（`test_agents_health` 期望 12→13（UAT-RED-E `:302`）；auth 两文件头矩阵失实 + 「鉴权先于 handler」无断言（UAT-RED-A2 `:183/:187`）；flaky 两处定性（R-09/R-13.3/UAT-RED-NEW `:474`）；`MEMORY_RETRY_*` 死配置 CARD-CONFIG-CLEANUP（UAT-RED-C1 `:220`，ID 已被 xfail reason 引用不可改名）。
- 做：期望表对齐 13；两文件头矩阵改实 + 一条「鉴权先于 handler」断言（变异：去掉依赖必红）；flaky 两处定性（单跑 ×5 + 同文件顺序对照）落盘；`MEMORY_RETRY_BASE_DELAY/MAX_DELAY` 退役（`config.py:644/:650`，census=0 证明）。
- 判据：diff 只 `<`；变异反例；pyright 保持 0（config.py 属 backend/app）→ ★app；顺带定性 `tests/contract/test_node_id_patterns.py::TestNodeIdPatternConsistency::test_pattern_matches_json_schema`（主干既有红，波 0 实测）——修或登记。

## 5. 手册 §零 条目（主 session 写手册时逐条落）
1. `B14_BASE` 与 10 条 NEW 车道（表）；旧 T 系车道（早期批次 `card/t1-readleak`…）名不同不冲突。
2. 基线文件 `evidence-b14/unit-red-baseline-08100483.txt`（64，nodeid 口径，带 `--ignore test_deploy_vault_sh.py`；T2-A 合入后主 session 撤 `--ignore` 重取）。
3. pyright 绝对路径 + `test -x` + 禁 `| tail -1`；`B14_BASE` = 0 errors；语义车道保持 0。
4. `--no-color`；`.txt`；`rc=$pipestatus[1]`。
5. ruff zsh 数组写法。
6. W4 哨兵判据改绑。
7. 批中禁装工具。
8. 本批部署卡 = T2-B，真 `up -d` 需当次授权；`fsrs_bridge.py`/`decay_beta.py` 零写者。
9. 主干脏项 107 项不动（清单）。
10. GATE 末位；TAIL 叠在语义之上。
11. 波 0 收尾记录（U6-C `c3912b42` / U1 `622f3a5d` / U2 `b4705dde` / U2 docs `b11829b1`；pyright 0；skills 546；unit 64 vs 65；api 268；tag 处置）。
12. 长度门 ⑪ 旧口径字面量。
13. 每卡 commit 带卡号。
14. D-32 注释尾巴不重置轮次。
15. 协议 §2.1 首部：抄含 codex 版本行 + model 行 + reasoning 行（行号不限、写明行号）。

## 6. 卡文与短 goal 格式（照第十三批）
- 卡文：两行 banner（`> ⚠️ 本文件是 CARD-<名> 的完整卡文——…；/goal 在第十四批手册 §三 <块名> 块。` + `> 批次标记 … 车道 … 前提 … 用户已裁 … 勘探 … 协议（绝对路径）… 手册（绝对路径）… ⚠️ 两份都在 feature 主干 --add-dir 那份`）→ `# CARD-<名> — <标题>` → `## 〇 事实`（表：事实 | 位置/实测命令）→ `## 一 完成条件（AND）`（(a) 第 0 分钟起，每条可判定）→ `## 二 裁判命令`（可直接粘贴；tee + rc）→ `## 三 禁改与隔离`（地盘 + 硬边界）→ `## 四 Codex / 验收单`（多轮 D-15 固定串、prompt 五分节、禁四措辞、存档首部、验收单 DoD-3 双段 + 「本卡未证明什么」「台账待登记条目」各 ≥4）。
- 短 goal（手册 §三，每块恰 7 行、≤3800 字符、以 `/goal` 开头）：① `/goal 完成 CARD-<名>：<一句做什么 + 为什么现在>[BATCH-2026-09-11-第十四批 / CARD-<名>]（<工时>h）` ② `车道：NEW <绝对路径>（分支 …，HEAD B14_BASE，venv symlink + backend/.env 就位）。第 0 分钟：…。前提：…` ③ `⛔ 开工第一件事：通读并逐条执行卡文 <绝对路径>——<本卡最重要的 3~5 条口径>。协议 <绝对路径>；手册 <绝对路径>（§零/§一/§四）。` ④ `完成条件（AND，细节见卡文同字母段）：(a)…(x)` ⑤ `核心裁判：1.…6.` ⑥ `硬边界：…不改台账；不 push。` ⑦ `收尾：Codex gpt-6-astra ultra 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0（…）；裁判输出 tee 进 evidence-<短名>/；验收单 UAT-CARD-<名>-<日期>.md …；commit header ≤100 含批次标记；*.stderr* 不入库；不 push；跑完说「复核第十四批 T<N>」。`
- 核验者只报 defects（不填「核验通过项」）；跨文引用用条目名不用行号。
