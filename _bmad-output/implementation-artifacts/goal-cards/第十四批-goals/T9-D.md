> ⚠️ 本文件是 CARD-RUNTIME-SHA-SURFACE 的完整卡文——车道开工后必读并逐条执行；它不是 /goal 粘贴文本。/goal 在第十四批手册 §三 T9-D 块。
> 批次标记 `[BATCH-2026-09-11-第十四批 / CARD-RUNTIME-SHA-SURFACE]`。车道：`card-t9-w4`（分支 `card/t9-w4`，NEW @ `B14_BASE` = `08100483`，venv symlink 已建、`backend/.env` 在）。前提：**本车道第 4/4 张，前一卡 T9-C `CARD-W4-SENTINEL-REBIND` 已独立 commit 且 `git status --porcelain` 空——第 0 分钟把当前 HEAD（= T9-C 末 commit）记成 `$PREV`，本卡地盘核以 `$PREV..HEAD` 为准**。用户已裁：D-15 多轮（有代码改动 ⇒ 多轮，上限 5；第 5 轮仍有 HIGH 停下交主 session）/ D-32 纯注释·docstring 尾巴不占轮次不重置 / §0.2.5 批中不装任何包 / 本批部署卡 = T2-B（本卡不涉）/ §0.2.6 `fsrs_bridge.py`·`decay_beta.py` 零写者、live vault·7691·现网 LanceDB 只读。勘探 2026-09-11 于主干 `08100483`（`recon_A_report.md` §B.2「W4 扫描面 T-1 / T-13 / T-15」+「SHELLOPTS=noexec 假绿」、`b14_design.md` §4 T9-D；recon_C 无 T9-D 专节，门体锚点由本卡在主干树实测）。本卡 §〇 每行均在主干树（feature `--add-dir` 那份，当前 HEAD `e58d5c5c` = `08100483` + 1 个纯文档 commit）`sed -n`/`grep -nF`/`ast` 复测，与勘探/设计不符处已标「勘探/设计 :X → 实测 :Y」。协议（**绝对路径**）：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/.claude/rules/card-batch-protocol.md`（§1 合并门 + D-15 轮次 / §2.1 存档首部 / §2.2 裁判落盘 + --no-color / §2.3 批级环境变更 / §3 W4 哨兵 + 最低覆盖）；手册（**绝对路径**）：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-09-11-第十四批开跑手册-10车道43卡.md`（§零 / §一 / §四）。⚠️ **这两份都在 feature 主干 `--add-dir` 那份，不在本车道树**——车道树自己的 `.claude/rules/card-batch-protocol.md` 是 `08100483` 版、本批对协议/手册的回写只在 `--add-dir` 那份上，一律按上面的绝对路径读。

# CARD-RUNTIME-SHA-SURFACE — runtime_sha 运行时文件门扩面（三个运行时文件进监视：`lancedb_pending_index__*.jsonl` / `neo4j_memory.json` / `llm_call_logs.db`）+ `SHELLOPTS=noexec` 假绿的调用方自证契约（脚本内不可防，落调用方断言；每条扩面与注入配「先 unchanged / 后 CHANGED」对照）

## 〇 事实
| 事实 | 位置 / 实测命令 |
|---|---|
| ⛔ **口径更正①（地盘路径）**：设计稿 §3 / 手册 §一·§三地盘表把本卡地盘写作 `scripts/runtime_sha.sh`（repo 根）——**该文件在主干不存在**。真门 = **`backend/scripts/lifespan_isolation_runtime_sha.sh`（649 行）**。**设计/手册 `scripts/runtime_sha.sh` → 实测 `backend/scripts/lifespan_isolation_runtime_sha.sh`**。本卡一切编辑只落在真门；`git diff --stat` 会显示真门路径（非 §3 字面），这是已登记的口径更正，不是越界（见 §四「台账待登记」请主 session 同步 §3 地盘 token）。 | `ls scripts/runtime_sha.sh 2>&1`（No such file）；`wc -l backend/scripts/lifespan_isolation_runtime_sha.sh`=649；`find . -name 'runtime_sha*' -not -path '*/node_modules/*'`=仅 `backend/scripts/lifespan_isolation_{runtime_sha.sh,guard_probes.py,negative_control.py}` |
| 门现行监视面 = `WATCHED_FIXED`（3 固定项，`:482` 起，项在 `:483/:484/:485`）+ `WATCHED_GLOBS`（1 glob，`:504` 起，项在 `:505`）；计数常量 `EXPECTED_FIXED_COUNT=3`（`:507`）/`EXPECTED_GLOB_COUNT=1`（`:508`）；计数自检 fail-closed（`:512-521`，数组长 ≠ 常量即 `GATE-BROKEN`）。三个固定项 = `${BACKEND_DIR}/data/bug_log.jsonl`、`${BACKEND_DIR}/data/outbox/events.jsonl`、`${BACKEND_DIR}/app/data/vault_index_pending.jsonl`；glob = `${BACKEND_DIR}/app/data/vault_index_pending__*.jsonl`。 | `sed -n '475,521p' backend/scripts/lifespan_isolation_runtime_sha.sh` |
| `BACKEND_DIR` = 脚本目录/..（`:462-465`，`pwd -P`），且 `:469-473` 断言它含 `app/main.py`+`tests/`，否则 `GATE-BROKEN`——故三个待加面只要落在 `backend/` 下即与门同基。门自证常量 `SELFTEST_EXPECTED`（`:434`）哈的是固定串，**扩面不动它**；`snapshot()`（`:534`）/ exec 清洗（`:310-311`）/ 判定段（`:639` `if BEFORE != AFTER` → `:640` `CHANGED` exit 1 / `:648` `unchanged`）**一律不动**。 | `grep -nF 'os._exit\|SELFTEST_EXPECTED\|snapshot()\|RUNTIME-FILES: CHANGED\|RUNTIME-FILES: unchanged' backend/scripts/lifespan_isolation_runtime_sha.sh` |
| **待加面 T-1（glob，`${BACKEND_DIR}/app/data/lancedb_pending_index__*.jsonl`）**：生产写点 `backend/app/services/lancedb_index_service.py:75` `self._journal_stem = "lancedb_pending_index"` → `namespaced_state_path(_data_dir, stem, vault_key=…)`，`_data_dir = Path(__file__).parent.parent/"data"` = `backend/app/data`，与 `vault_index_pending__*.jsonl` **同命名空间形态**（双下划线 + `sanitize_vault_id` 只含 `\w`）。门 `:51` 注释明写「`lancedb_pending_index__*.jsonl` **不在**清单里（扩面属另一张卡的范围决策）」= **本卡就是那张卡**。 | `sed -n '73,79p' backend/app/services/lancedb_index_service.py`；`sed -n '50,52p' backend/scripts/lifespan_isolation_runtime_sha.sh` |
| **待加面 T-15a（固定项，`${BACKEND_DIR}/data/neo4j_memory.json`）**：生产默认 `backend/app/clients/neo4j_client.py:54` `DEFAULT_STORAGE_PATH = Path(__file__).parent.parent.parent/"data"/"neo4j_memory.json"`（= `backend/data/neo4j_memory.json`，JSON fallback 落盘）。门 `:53` 注释「不看 Neo4j」指的是**数据库里的 DDL/schema**（socket 门 `live_port_guard.py` 的职责），**不**指这个磁盘 JSON 文件——扩面后要把这条注释措辞收窄，别让后人以为「JSON 落盘文件也不该看」。 | `sed -n '53,56p' backend/scripts/lifespan_isolation_runtime_sha.sh`；`sed -n '54,54p' backend/app/clients/neo4j_client.py` |
| **待加面 T-15b（固定项，`${BACKEND_DIR}/data/llm_call_logs.db`）**：生产默认 `backend/app/middleware/cost_tracker.py:34-35` `_BACKEND_DIR = Path(__file__).parent.parent.parent`（= `backend`）/`_DEFAULT_DB_PATH = _BACKEND_DIR/"data"/"llm_call_logs.db"`。⚠️ 它是 **SQLite 二进制**：门用 `sha256` 比字节（`snapshot()` 的 `hash_stdin <"$f"` + `[[ =~ ^[0-9a-f]{64}$ ]]`），二进制可算 sha、能判 CHANGED；但它会被「正常读」也轻微改头（SQLite header counter/journal），**本卡必须在 (e)/(j) 实测一次正常 wrapped pytest 下它是否稳定 unchanged**，不稳定就是本门新的假红面，登记「本卡未证明什么」。 | `sed -n '33,36p' backend/app/middleware/cost_tracker.py` |
| 三个待加面**均 git-ignored**（= 运行时产物，符合门定位「均 git-ignored 的运行时产物」`:475`）。 | `git check-ignore backend/data/neo4j_memory.json backend/data/llm_call_logs.db backend/app/data/lancedb_pending_index__x.jsonl`（三行全命中） |
| ⛔ **口径更正②（T-13 不同类）**：勘探 A §B.2 把「T-1 / T-13 / T-15」并称「W4 扫描面」。实测 **T-13 = `*_with_status` 兼容壳**，是 **4 个生产方法**：`rag_service.py:344 get_weak_concepts_with_status` / `memory_service.py:1087 get_review_suggestions_with_status` / `memory_service.py:2282 search_memories_with_status` / `memory_service.py:2485 search_error_memories_with_status`。它指的是「补丁/mock 落在兼容壳而非真实路径」的**源码/AST 扫描面**，与 runtime_sha 的「运行时**文件**字节快照」**不同类**，无法「进本门监视」；且这 4 个方法在 `backend/app/services`（production + **出 T9 地盘**）。⇒ **本卡「三面进监视」= 三个运行时文件（T-1 + T-15a + T-15b），T-13 另立一张源码/AST 扫描卡移交**（见 §四「台账待登记」）。 | `grep -rnI 'def .*_with_status' backend/app`（恰 4 行） |
| **noexec 现状（脚本内不可防，如实登记）**：门 `:113-118` + `:290-293` 明写 `SHELLOPTS=noexec` 下 bash「只解析不执行」，连 `:310-311` 那句 `exec` 都不跑，rc=0、零输出、被包裹命令没跑——「**假绿且无法从脚本内部防御**」「**没有修，因为脚本自己的代码正是那个不会执行的东西**」。`:116-118` 已给调用方硬要求「**判据不能只看 rc，必须要求 stdout 里出现 `RUNTIME-FILES: unchanged`/`CHANGED` 这一行结论**」。兄弟项 `SHELLOPTS=errexit`（假红）已由 exec 参数 `-u SHELLOPTS`（`:294`）摘掉。⇒ **noexec 的「修」只能落在非 bash 调用方**（Python 子进程免疫 noexec）：门自证 = 输出结论行，调用方断言「无结论行 ⇒ 门未跑 ⇒ rc≠0」。 | `sed -n '107,124p;290,294p' backend/scripts/lifespan_isolation_runtime_sha.sh` |
| **调用方/探针/镜像耦合（全部出 T9 地盘，本卡禁碰；部分要移交同步）**：① `backend/scripts/lifespan_isolation_guard_probes.py`（2199 行，**§3 既不在 T8 也不在 T9 地盘 = 无归属**）：门头 `:67`「由 **19 条** shell 探针承重」被花名册探针 `shell-probe-roster-matches-declared-count` 钉；M15 glob 探针族（`:1550/:1567/:1589/:1611/:1631`，helper `_fake_backend:1401`/`_run_gate_creating:1423`/`_sh:636`）**按字符串锚定 `vault_index_pending__*.jsonl` glob**。② `backend/scripts/lifespan_isolation_negative_control.py`（**T8 地盘**，T8-D）：`:133 RUNTIME_FILE_RELPATHS`(3) + `:167 RUNTIME_FILE_GLOBS`(1) **镜像门清单**，`:128` 注释「与 runtime_sha.sh 监视清单保持一致」，`:271` `{len(RELPATHS)} 固定项 + {len(GLOBS)} glob`；它是 **`__main__` 脚本态（`:3471`），不被 pytest unit 套件收集**。③ `backend/tests/unit/test_live_port_guard_contract.py`（**无归属**）驱动上面探针。**实测：本卡是加面（加不是改/删）**——M15 探针的锚串 `vault_index_pending__*.jsonl` 仍在、计数自检在 .sh 内自洽 ⇒ pytest 探针套件**应仍绿**（(j) file-level 实测核）；但 ②的镜像会漂（3+1 ≠ 扩面后 5+2），「保持一致」不变量 + 变异正锚覆盖需同步——**出 T9 地盘 ⇒ 本卡只登记移交，不改**。 | `grep -nF '条** shell 探针承重' backend/scripts/lifespan_isolation_runtime_sha.sh`(=67)；`sed -n '126,172p' backend/scripts/lifespan_isolation_negative_control.py`；`grep -nE 'def probe_runtime_glob' backend/scripts/lifespan_isolation_guard_probes.py` |
| **本批纪律**：本卡地盘仅 `backend/scripts/**`（**非 `backend/app`** ⇒ **非 APP_CARD、无 pyright 0 门**；gate 对 `app/main.py` 的引用是 BACKEND_DIR 断言的**只读探测**，不算触及 app）；若实测发现「扩面/noexec 必须碰 `backend/app` 或 T8/无归属文件」才能成 ⇒ ⛔ **停下在验收单登记，不自行扩面**（任务约束 + §0.2）。判据 grep git 输出一律 `--no-color` + 同次验伪锚；承重裁判 `2>&1 \| tee evidence-runtime-sha-surface/<name>-$(date +%Y%m%dT%H%M%S).txt; echo rc=$pipestatus[1]`（zsh，`tee` 吞码）；证据 `.txt` 不 `.log`（仓根 `.gitignore` 全局 `*.log`）；临时换门做 fake-backend 负控一律 `$TMPDIR` 下、EXIT trap 无条件 `rm -rf` 还原 + 真实工作树一字节不碰；批中不装/升任何包；`*.stderr*` 不入库；不改台账；不 push。 | — |

## 一 完成条件（AND，每条可判定：命令 + 期望值）
- **(a) 第 0 分钟**：`pwd` = `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4`；`git branch --show-current` = `card/t9-w4`；`PREV=$(git rev-parse HEAD)` 并记下（= T9-C 末 commit，作本卡地盘基准）；`git status --porcelain` **空**；`ls -l backend/.venv`（symlink）+ `test -f backend/.env`；基线自证——主干树 `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b14/unit-red-baseline-08100483.txt` `grep -vc '^#'` = **64**；门基线自证——跑一次现有探针契约测试 file-level 记绿基线（见 (j)）。
- **(b) 口径核**（一律 `grep -nF`/`ast`，不写死行号、先求锚）：确认真门 649 行、`scripts/runtime_sha.sh` 不存在（口径更正①）；三个待加面生产默认路径锚（`lancedb_index_service.py` `_journal_stem="lancedb_pending_index"`、`neo4j_client.py` `neo4j_memory.json`、`cost_tracker.py` `llm_call_logs.db`）各命中；T-13 = 4 个 `*_with_status` 方法命中（口径更正②，**定性为源码扫描面，移交，不进本门**）；`WATCHED_FIXED=(`/`WATCHED_GLOBS=(`/`EXPECTED_FIXED_COUNT=`/`EXPECTED_GLOB_COUNT=` 四锚现求行号。
- **(c) 先红（扩面前·三面未被监视）**：用 fake-backend（`$TMPDIR` 内搭 `backend/{app/main.py,tests,scripts,data,app/data}`，把**改前**门副本 `cp` 进去，真实工作树一字节不碰）分别让被包裹命令写 `app/data/lancedb_pending_index__probe.jsonl` / `data/neo4j_memory.json` / `data/llm_call_logs.db`，跑门 → 三者各 stdout 含 `RUNTIME-FILES: unchanged` 且 rc=0（证明三面**改前不在**监视面）。
- **(d) 扩面（只动 .sh 的清单 + 计数 + 两处边界注释）**：`WATCHED_FIXED` 追加 `"${BACKEND_DIR}/data/neo4j_memory.json"` 与 `"${BACKEND_DIR}/data/llm_call_logs.db"`，`EXPECTED_FIXED_COUNT` **3→5**；`WATCHED_GLOBS` 追加 `"${BACKEND_DIR}/app/data/lancedb_pending_index__*.jsonl"`，`EXPECTED_GLOB_COUNT` **1→2**；改 `:51` 注释（`lancedb_pending_index__*.jsonl` 现已在清单，连带写明它与 `lancedb_index_service.py` 的命名空间同形）+ `:53` 注释（收窄为「不看 Neo4j **库内 schema**；`neo4j_memory.json` 磁盘落盘文件现已监视」）。**⛔ 不动** `SELFTEST_EXPECTED` / `snapshot()` / exec 清洗段 / 判定段 / `-u SHELLOPTS` 行 / 花名册声明 `:67`。
- **(e) 后绿（扩面后·注入必红）+ 验伪锚**：同 (c) 三面，跑**改后**门 → 三者各 stdout 含 `RUNTIME-FILES: CHANGED` 且 rc=1；**验伪锚（承重，证明没放宽成「全目录监视」）**：在同目录写一个**不在**清单的文件 `app/data/not_watched_probe.txt` → 仍 `RUNTIME-FILES: unchanged` rc=0。T-15b 另核一次「正常读不写」路径下 `llm_call_logs.db` 的 sha 稳定性（建库后只 `SELECT` 一次，前后 sha 应相同；不稳定 → 登记「本卡未证明什么」，并**不**因此放宽监视面）。
- **(f) 计数自检一致**：改后门在 fake-backend 跑一次正常 `-- /usr/bin/true` → stdout **不**含 `GATE-BROKEN — 固定监视项有 … 个` / `GATE-BROKEN — glob 监视模式有 … 条`（证明 `EXPECTED_*_COUNT` 已随数组同步 5/2）。
- **(g) noexec 先红（脚本内不可防，如实复现）**：**Python 子进程**（免疫 noexec）跑 `SHELLOPTS=noexec bash backend/scripts/lifespan_isolation_runtime_sha.sh -- /usr/bin/true`（在真门或 fake-backend 均可）→ rc=0 **且** stdout/stderr 都**不含任何 `RUNTIME-FILES:` 行**（复现门 `:113-118`/`:290-293` 登记的事实：门根本没跑）。
- **(h) noexec 后绿（调用方自证契约）**：对 (g) 的 stdout 施加**调用方断言**「stdout 不含 `RUNTIME-FILES:`（unchanged/CHANGED/GATE-BROKEN 任一前缀）⇒ 判门未跑 → 退出 rc≠0」→ 断言产出 **rc≠0**；对照：一次正常 run（无 noexec）stdout 含 `RUNTIME-FILES: unchanged` ⇒ 断言放行 rc=0（证明断言不是恒红）。断言配方（Python 与 shell 两版）写进验收单原文；.sh 的 `:116-118` 调用方硬要求注释**加固/明确**（措辞指向该断言），这是本卡 noexec「修」的**全部脚本内可做项**。
- **(i) noexec permanent 强制落点 = 移交（禁碰）**：断言的**常驻强制**（`guard_probes.py` 新探针 `shell-shellopts-noexec-caller-requires-sentinel` + 门头 `:67` 花名册 **19→20** + `test_live_port_guard_contract.py` 用例）**全部出 T9 地盘**（guard_probes 无归属、test 无归属）⇒ ⛔ **本卡不新增探针、不改门头 19、不碰 test**；落「台账待登记 + 移交主 session/无归属文件归属裁定」。**本卡也不新建 repo 根 `scripts/runtime_sha.sh` 作 bash launcher**——bash launcher 若本身在 noexec 下被起同样不执行，立一个「看起来能防 noexec」的 bash 壳会制造新的假安全感（理由写进验收单）。
- **(j) 探针套件回归（本门的面 = 这条契约测试，协议 §3「改了什么面跑那个面」）**：跑 `backend/tests/unit/test_live_port_guard_contract.py` **file-level**（门下目录级禁跑真连，见硬边界），改前记绿基线、改后复跑；**期望与 (a) 基线同绿**（加面是加不是改，M15 锚串 `vault_index_pending__*.jsonl` 仍在、计数自检自洽）；任何新红按「主干既有 / 本卡引入」分类——本卡引入 = 阻断必修（若修复只能落在 guard_probes.py 出地盘 ⇒ 停下交主 session，不自行改）。
- **(k) negctrl 镜像漂移登记**：实测 `backend/scripts/lifespan_isolation_negative_control.py` 的 `RUNTIME_FILE_RELPATHS`/`RUNTIME_FILE_GLOBS` 仍 3+1、与扩面后门 5+2 不一致（`:128` 的「保持一致」不变量断裂、`:271` 覆盖面变窄）；该文件 **T8 地盘 ⇒ 本卡不改**，登记「台账待登记 + T8/主 session 同步镜像」。
- **(l) 地盘核**：`git --no-pager diff --stat --no-color $PREV HEAD -- . ':(exclude)_bmad-output'` **只列** `backend/scripts/lifespan_isolation_runtime_sha.sh` 一个文件（`_bmad-output` 里的验收单/prompt/evidence 不在此面）。⚠️ 必用 `':(exclude)…'` 写法，不用 `':!…'`（本机 git 2.50 报 `Unimplemented pathspec magic` rc=128 + 空 stdout → 「为空即绑定」会把没跑成读成绿，见协议 §1）。
- **(m) tests/unit 目录级 diff 只 `<`**：与主干基线 `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b14/unit-red-baseline-08100483.txt`（64 条，nodeid 口径，**带 R-15 `--ignore backend/tests/unit/test_deploy_vault_sh.py`**）对照，`comm -13` 本卡引入的新红 = **空**（本卡只改 `backend/scripts/**`，不应产新红；`test_live_port_guard_contract.py` 属 unit，(j) 的回归绿是这条的充分条件）。
- **(n) Codex 多轮**：**Codex gpt-6-astra ultra 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0**（有代码改动 ⇒ 多轮，上限 5；第 5 轮仍有 HIGH 停下交主 session；审后再改代码必再送一轮；纯注释·docstring 尾巴按 D-32 不占轮次不重置；MEDIUM/LOW 登记不阻断）。
- **(o) 验收单「本卡未证明什么」「台账待登记条目」各 ≥4 条必填**（见 §四）。

## 二 裁判命令（可直接粘贴；cd 到车道树；承重裁判 tee + `rc=$pipestatus[1]`）
```zsh
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4
EV=_bmad-output/审查/evidence-runtime-sha-surface
mkdir -p "$EV"
GATE=backend/scripts/lifespan_isolation_runtime_sha.sh
PREV=$(git rev-parse HEAD)          # = T9-C 末 commit，地盘基准
print -r -- "PREV=$PREV branch=$(git branch --show-current)"; git status --porcelain
grep -vc '^#' /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b14/unit-red-baseline-08100483.txt   # 期望 64

# ① 锚点现求（不写死行号）+ 三面生产写点核 + T-13 定性
grep -nF 'WATCHED_FIXED=(' "$GATE"; grep -nF 'WATCHED_GLOBS=(' "$GATE"
grep -nF 'EXPECTED_FIXED_COUNT=' "$GATE"; grep -nF 'EXPECTED_GLOB_COUNT=' "$GATE"
grep -nF '_journal_stem: str = "lancedb_pending_index"' backend/app/services/lancedb_index_service.py
grep -nF 'neo4j_memory.json' backend/app/clients/neo4j_client.py
grep -nF 'llm_call_logs.db' backend/app/middleware/cost_tracker.py | head -1
grep -rnI 'def .*_with_status' backend/app | tee "$EV/t13-with-status-$(date +%Y%m%dT%H%M%S).txt"   # 期望 4 行（定性移交，不进本门）
git check-ignore backend/data/neo4j_memory.json backend/data/llm_call_logs.db backend/app/data/lancedb_pending_index__x.jsonl

# ② 先红/后绿/验伪锚 —— fake-backend 注入 harness（改前门 vs 改后门，各跑一次；$TMPDIR 内，工作树零碰）
#    把下面脚本落一个临时文件跑；$1=门路径、$2=期望结论（unchanged|CHANGED）
cat > "$EV/inject_probe.zsh" <<'PROBE'
#!/usr/bin/env zsh
set -u
GATE_SRC="$1"; WANT="$2"
typeset -i bad=0
for rel want_file in \
  app/data/lancedb_pending_index__probe.jsonl L \
  data/neo4j_memory.json N \
  data/llm_call_logs.db D \
  app/data/not_watched_probe.txt X ; do
  T=$(mktemp -d); trap "rm -rf $T" EXIT
  mkdir -p "$T/backend/app/data" "$T/backend/data" "$T/backend/tests" "$T/backend/scripts"
  print -r -- '# fake' > "$T/backend/app/main.py"
  cp "$GATE_SRC" "$T/backend/scripts/lifespan_isolation_runtime_sha.sh"
  out=$(bash "$T/backend/scripts/lifespan_isolation_runtime_sha.sh" -- /bin/sh -c "printf 'x\n' >> $T/backend/$rel" 2>&1); rc=$?
  # not_watched 那条永远期望 unchanged（验伪锚）；其余按 WANT
  exp="$WANT"; [[ "$want_file" == X ]] && exp=unchanged
  line=$(print -r -- "$out" | grep -oE 'RUNTIME-FILES: (unchanged|CHANGED)' | tail -1)
  print -r -- "rel=$rel exp=$exp got='${line:-<none>}' rc=$rc"
  [[ "$line" == "RUNTIME-FILES: $exp" ]] || bad=1
  trap - EXIT; rm -rf "$T"
done
print -r -- "INJECT-SUMMARY bad=$bad"; exit $bad
PROBE
# 改前（先红）：三面 exp=unchanged
git stash list >/dev/null   # 只读，别真 stash
cp "$GATE" "$EV/gate-before.sh"
zsh "$EV/inject_probe.zsh" "$EV/gate-before.sh" unchanged 2>&1 | tee "$EV/inject-before-$(date +%Y%m%dT%H%M%S).txt"; echo rc=$pipestatus[1]
#   期望：lancedb/neo4j/llm 三条 got=unchanged、not_watched got=unchanged、bad=0

# …（在此完成 (d) 扩面编辑后再跑下面）改后（后绿+验伪锚）：三面 exp=CHANGED、not_watched 仍 unchanged
zsh "$EV/inject_probe.zsh" "$GATE" CHANGED 2>&1 | tee "$EV/inject-after-$(date +%Y%m%dT%H%M%S).txt"; echo rc=$pipestatus[1]
#   期望：lancedb/neo4j/llm 三条 got=CHANGED、not_watched got=unchanged、bad=0

# ③ 计数自检一致（改后门，fake-backend，正常命令不得 GATE-BROKEN 计数分支）
T=$(mktemp -d); mkdir -p "$T/backend/app/data" "$T/backend/data" "$T/backend/tests" "$T/backend/scripts"
print -r -- '# fake' > "$T/backend/app/main.py"; cp "$GATE" "$T/backend/scripts/lifespan_isolation_runtime_sha.sh"
bash "$T/backend/scripts/lifespan_isolation_runtime_sha.sh" -- /usr/bin/true 2>&1 | tee "$EV/count-selfcheck-$(date +%Y%m%dT%H%M%S).txt"; echo rc=$pipestatus[1]; rm -rf "$T"
#   期望 stdout 不含「固定监视项有」「glob 监视模式有」，末行 RUNTIME-FILES: unchanged

# ④ noexec 先红 + 调用方自证后绿（Python 免疫 noexec；断言 = 无结论行则 rc≠0）
python3 - "$GATE" <<'PY' 2>&1 | tee "$EV/noexec-$(date +%Y%m%dT%H%M%S).txt"
import subprocess, sys, os
gate = sys.argv[1]
# 先红：SHELLOPTS=noexec ⇒ 门没跑、rc=0、无结论行
env = dict(os.environ, SHELLOPTS="noexec")
p = subprocess.run(["bash", gate, "--", "/usr/bin/true"], capture_output=True, text=True, env=env)
both = p.stdout + p.stderr
no_verdict = "RUNTIME-FILES:" not in both
print(f"[noexec先红] rc={p.returncode} no_verdict={no_verdict} out_len={len(both)}")
assert p.returncode == 0 and no_verdict, "noexec 先红前提不成立（门不该在 noexec 下产出结论行）"
# 调用方自证断言：无结论行 ⇒ 判门未跑 → 退出 1
def caller_assert(stdout_stderr: str) -> int:
    return 0 if "RUNTIME-FILES:" in stdout_stderr else 1
print(f"[noexec后绿] caller_assert(noexec输出) = {caller_assert(both)}  (期望 1)")
# 对照：正常 run 有结论行 ⇒ 断言放行
q = subprocess.run(["bash", gate, "--", "/usr/bin/true"], capture_output=True, text=True,
                   cwd=None)  # 正常环境（不注 noexec）
okboth = q.stdout + q.stderr
print(f"[对照] rc={q.returncode} has_verdict={'RUNTIME-FILES:' in okboth} caller_assert={caller_assert(okboth)} (期望 0)")
assert caller_assert(both) == 1 and caller_assert(okboth) == 0, "调用方断言不是「无结论行即红、有结论行即绿」"
print("NOEXEC-CONTRACT: PASS")
PY
echo rc=$pipestatus[1]

# ⑤ 探针套件回归（本门的面；file-level，禁目录级真连）
.venv/bin/python -m pytest backend/tests/unit/test_live_port_guard_contract.py -q 2>&1 | tee "$EV/probe-contract-$(date +%Y%m%dT%H%M%S).txt"; echo rc=$pipestatus[1]
#   期望与改前基线同绿；新红分类「主干既有/本卡引入」，本卡引入=阻断

# ⑥ negctrl 镜像漂移登记（只读核，不改 T8 文件）
grep -nE 'RUNTIME_FILE_RELPATHS|RUNTIME_FILE_GLOBS|保持一致' backend/scripts/lifespan_isolation_negative_control.py | tee "$EV/negctrl-mirror-$(date +%Y%m%dT%H%M%S).txt"
#   实测仍 3 relpaths + 1 glob（与扩面后门 5+2 不一致）⇒ 登记移交

# ⑦ 地盘核（--no-color + exclude 写法）
git --no-pager diff --stat --no-color "$PREV" HEAD -- . ':(exclude)_bmad-output' | tee "$EV/scope-$(date +%Y%m%dT%H%M%S).txt"
#   期望只列 backend/scripts/lifespan_isolation_runtime_sha.sh

# ⑧ tests/unit 目录级 diff 只 < （复跑口径带 R-15 --ignore；本卡只改 backend/scripts，不应产新红）
#    复跑命令与基线同口径：.venv/bin/python -m pytest backend/tests/unit --ignore backend/tests/unit/test_deploy_vault_sh.py -q
#    取当前红 nodeid 与基线 comm -13，本卡引入新红应为空（裁判落盘同 $EV）
```

## 三 禁改与隔离
- ⛔ 禁写 live vault `/Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/**`；⛔ 禁连 7691/7687；⛔ 禁碰 `canvas-vault/.claude/scripts/fsrs_bridge.py` / `decay_beta.py`（§0.2.6 零写者，碰 = 触发 live 部署铁律，立即停下报主 session）；现网 LanceDB 只读。
- 地盘**只 `backend/scripts/lifespan_isolation_runtime_sha.sh` 一个文件**（= 设计/手册 `scripts/runtime_sha.sh` 的口径更正①实指）。**禁改**：`backend/scripts/lifespan_isolation_guard_probes.py`（无地盘归属——花名册 `:67` 19 条、M15 glob 探针；本卡加面禁动它、**门头 19 不改**）；`backend/scripts/lifespan_isolation_negative_control.py`（**T8 地盘**，T8-D；镜像清单只登记漂移不同步）；`backend/tests/unit/test_live_port_guard_contract.py`（无归属，只**读/跑**不改）；`backend/tests/support/live_port_guard.py` / `guard_plugin.py` / `backend/tests/conftest.py` / `backend/tests/unit/conftest.py`（T9-A/T9-B/T9-C 的交付，本卡**不碰**——碰 = 重开前卡）；`backend/app/**`（本卡不触及，gate 对 `app/main.py` 的引用是只读探测）；`backend/tests/**`（除只跑 (j) 契约测试外不改）。
- ⛔ **扩面是「加」不是「放宽」**：只追加三个**可由生产写点证明**的运行时文件项 + 同步两个 `EXPECTED_*_COUNT`；**禁**把任一 fail-closed（计数自检 `:512-521` / glob 排序 `:582-586` / compgen 自检 `:565-569` / 门自证 `:445-449`）改成放行；**禁**把 glob 写宽（如单下划线 `lancedb_pending_index*.jsonl` 会把人手旁文件收进来 = M14 已登记的假红，必须双下划线 `__*`）；**禁**缩小任何现有监视项来消化问题。
- ⛔ **noexec 不在脚本内造「防御」**：只加固 `:116-118` 调用方硬要求注释 + 指向断言配方；**禁**新增声称能防 noexec 的可执行分支（脚本内不可防，虚假防御比如实登记更糟）；**禁**新建 repo 根 `scripts/runtime_sha.sh` bash launcher（同样被 noexec 噎死）。permanent 强制（探针 + 门头 19→20 + test）**出 T9 地盘 ⇒ 移交**，本卡禁碰。
- ⛔ 撤暂存一律 `git reset HEAD -- <path>` + `rm -f`；**禁 `git checkout HEAD -- <path>`**（清暂存区，已 add 的改动静默丢失）；**禁 `git stash`**（栈跨全部 worktree 共享，别的 session 会 pop）；fake-backend 负控一律在 `$TMPDIR`，EXIT trap 无条件 `rm -rf` 还原。
- ⛔ 不往共享 venv 装/升任何包；改共享运行环境 = 批级事件须协议 §2.3 通告 + 主 session 批。
- 不改台账（只主 session 改，卡在验收单写「台账待登记条目」）；不 push；`*.stderr*` 不入库；证据后缀 `.txt`/`.json`/`.sh`，不用 `.log`（仓根 `.gitignore` 全局 `*.log` 会静默吞）；⛔ 禁跑 `tests/integration` / `tests/e2e` 与 `backend/tests/unit` **目录级真连**（`test_live_port_guard_contract.py` 走独立子进程探针，file-level 安全；目录级会起 lifespan 连 7691）。

## 四 Codex / 验收单
命令（照协议 §2 / 设计稿 §0）：`codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-RUNTIME-SHA-SURFACE[-rN].md)" > _bmad-output/审查/codex-review-CARD-RUNTIME-SHA-SURFACE[-rN].md 2> _bmad-output/审查/codex-review-CARD-RUNTIME-SHA-SURFACE[-rN].stderr </dev/null`。轮次：**Codex gpt-6-astra ultra 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0**（有代码改动 ⇒ 多轮，上限 5；第 5 轮仍有 HIGH 停下交主 session；审后再改代码必再送一轮，存档带 `-rN`；对 HIGH 的驳回写理由但不能自判通过，由主 session 复核裁定；MEDIUM/LOW 登记不阻断；纯注释·docstring 尾巴按 D-32 不占轮次不重置）。
- **prompt 五分节**：一 背景 + 最小读取面写死（`backend/scripts/lifespan_isolation_runtime_sha.sh`；三个生产写点文件 `lancedb_index_service.py` / `neo4j_client.py` / `cost_tracker.py` 的对应行；耦合只读面 `lifespan_isolation_guard_probes.py` 的花名册与 M15 glob 探针、`lifespan_isolation_negative_control.py` 的镜像清单）。二 作者自述请独立核对（三面各「先 unchanged / 后 CHANGED」对照 + not_watched 验伪锚；`EXPECTED_*_COUNT` 随数组同步 5/2；noexec 调用方自证断言「无结论行即 rc≠0」；探针契约 file-level 回归绿；negctrl 镜像漂移与 T-13 不同类两项移交）。三 按重要性排序的问题（见下 ①~⑥）。四 输出格式（级别 + 文件:行 + 依据 + 建议；只读判不了的写「未验证」）。五 边界（只读；不要跑 hook、不要暂存文件；`guard_probes.py`/`negative_control.py`/`test_live_port_guard_contract.py`/`backend/app/**`/其余 T9 test-support 文件**不在本卡改面**）。
- **prompt 要点①~⑥**：① 扩面是否**只加不放宽**——三项是否均可由生产写点证明、glob 是否双下划线、有无顺手改宽/缩小任何 fail-closed；② `EXPECTED_FIXED_COUNT`/`EXPECTED_GLOB_COUNT` 是否与数组同步（否则计数自检会 `GATE-BROKEN`）；③ noexec「修」是否**诚实**——有没有在脚本内造出看似能防 noexec 的分支（应只有注释加固 + 调用方断言配方）、断言是否「无结论行即红、有结论行即绿」；④ 三面注入的**对照输入**与**未被拦下的输入**（not_watched 验伪锚）是否都落盘、`llm_call_logs.db` 二进制 sha 稳定性是否被核；⑤ 有无碰到**门未覆盖的路径**/出地盘文件（guard_probes/negctrl/test/app）被误改；⑥ `:51`/`:53` 两处边界注释更新是否与新监视面一致、花名册 `:67`「19 条」是否被误动。措辞用「负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径」。
- **存档首部六行 blockquote**（协议 §2.1）：抄含 `codex --version` 实测值行 + model 行（`gpt-6-astra`）+ reasoning_effort 行（`ultra`）并**括注行号**（从 `.stderr` 会话头自证抄前三行，`.stderr` 本身不入库）；缺「模型 / reasoning_effort / codex」任一字段 = 该轮不计配额。审查绑定写 `$PREV..HEAD` 或最终 HEAD（末轮必绑最终 HEAD）。
- **验收单** `_bmad-output/验收单/UAT-CARD-RUNTIME-SHA-SURFACE-<日期>.md`：DoD-3 双段——4-A Claude 已代验（裁判 ①~⑧ 的存档路径 + 末行 rc）；4-B 你来验（零技术词一句，句型「我做 X → 我看到 Y → 我感觉 Z」+ felt-sense，例：「测试跑完后，那三份自动生成的记录文件要是被悄悄改过，现在系统会明确说『变了』并拦下来——我感觉更放心」，⛔ 0 技术词）。独立小节：「三面注入 before/after 对照表（路径 + unchanged→CHANGED + 验伪锚）」、「noexec 调用方自证断言原文（Python + shell 两版）+ 为什么脚本内不可防」、「`llm_call_logs.db` 二进制 sha 稳定性实测结论」。
- **「本卡未证明什么」≥4（必填）**：1) 三面的**生产真实写路径**是否一定等于门监视的默认路径（生产可能被 settings 覆盖 neo4j storage / cost_tracker db_path / lancedb state_dir——本卡只证「默认路径被监视」，未证「生产一定写默认路径」）；2) `llm_call_logs.db` 在一次**真实长 pytest run** 下是否稳定 unchanged（本卡只在 fake-backend 与单次 SELECT 下核过）；3) noexec 的**常驻强制**（探针 + 门头 19→20 + test）未落地（出地盘，移交）；4) negctrl 镜像（T8）未同步，扩面后门与镜像的覆盖面不再等价；5) T-13（`*_with_status` 补丁落壳）源码扫描面本卡未实现（移交）。
- **「台账待登记条目」≥4（必填）**：1) **口径更正①**：§3/手册地盘 token `scripts/runtime_sha.sh` → 真文件 `backend/scripts/lifespan_isolation_runtime_sha.sh`，请主 session 同步 §3；2) **negctrl 镜像同步（T8）**：`lifespan_isolation_negative_control.py` 的 `RUNTIME_FILE_RELPATHS`/`RUNTIME_FILE_GLOBS` 需随门 5+2 同步 + `:271` 计数 + `:128`「保持一致」不变量，归 T8/主 session；3) **noexec permanent 强制移交**：guard_probes.py 新探针 `shell-shellopts-noexec-caller-requires-sentinel` + 门头 `:67` 花名册 19→20 + `test_live_port_guard_contract.py` 用例，归「无归属文件归属裁定 + 主 session」；4) **T-13 源码扫描卡**：`*_with_status`（4 方法）补丁/mock 落壳检测，另立源码/AST 扫描卡（与 runtime_sha 不同类）；5) guard_probes.py / test_live_port_guard_contract.py **无地盘归属**，建议主 session 明确其归属车道。
- commit header ≤100 含批次标记且含卡号（如 `test(runtime-sha): 扩面三运行时文件 + noexec 调用方自证契约 [BATCH-2026-09-11-第十四批 / CARD-RUNTIME-SHA-SURFACE]`），body 行 ≤100（`wc -m`）；`*.stderr*` 不入库；不 push；**本卡是 T9 末卡（4/4），跑完独立 commit + 工作树干净后说「复核第十四批 T9」**。
