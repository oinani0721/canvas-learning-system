> ⚠️ 本文件是 CARD-SKILL-PORT-LINT-PARSER 的完整卡文——车道开工后必读并逐条执行；它不是 /goal 粘贴文本。/goal 在第十四批手册 §三 T7-C 块。
> 批次标记 `[BATCH-2026-09-11-第十四批 / CARD-SKILL-PORT-LINT-PARSER]`。车道：`card-t7-skills`（分支 `card/t7-skills`，NEW @ `081004834e37b1b0253cf81dc7b44e784646c934`（B14_BASE），`backend/.venv` symlink 已建、`backend/.env` 在），**本车道第 3/4 张**，前提：**前一卡 T7-B CARD-AILINKED-4TH-WRITER 已独立 commit 且 `git status --porcelain` 空**（开工核 `git log --oneline` 含 `CARD-AILINKED-4TH-WRITER`；开工 `git rev-parse HEAD` 记下 = 前一卡末 commit = 本卡地盘核与 Codex 绑定基线，记作 `<T7B_TIP>`），之后串 T7-D CARD-G2-7a-TAIL。用户已裁：**D-15 多轮**（Codex gpt-6-astra ultra 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0，有代码改动 ⇒ 上限 5 轮）。本卡 = 第十三批 CARD-SKILL-PORT-LINT r5 D-15 人审出口建议的「解析器另立卡」落地 + tests/regression 解耦残留（recon A §B.3）。勘探 2026-09-11 于主干（recon A §B.3 / 设计稿 §4 T7-C + §3 地盘）+ 本卡 2026-09-12 于 `08100483` 树 `sed -n`/`grep` 实测复核。协议（⛔ 只读 **feature 主干树 `--add-dir` 那份**）：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/.claude/rules/card-batch-protocol.md`（§1 合并门 + 串行车道绑定口径 + `':(exclude)…'` 写法 / §2.1 存档首部 / §2.2 裁判落盘 + `--no-color` + `.txt` + ruff zsh 数组 / §2.3 批级通告 / §3 最低覆盖）。手册同理只读主干树那份：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-09-11-第十四批开跑手册-10车道43卡.md`（§零 / §一 / §四）。⚠️ **车道树自己的 `.claude/rules/card-batch-protocol.md` 是 `08100483` 版；本批回写只在 `--add-dir` 那份，别读车道树那份。**

# CARD-SKILL-PORT-LINT-PARSER — lint 解析器从 6294 行巨测文件抽成可导入模块（行为零漂移 / tests/skills 546 绿不变）+ start-exam-board `:430/:435` 裸 `/tmp/` 残留与 4 处 regression 硬钉点登记（真解耦跨地盘，交主 session 裁）

## 〇 事实
| 事实 | 位置 / 实测命令 |
|---|---|
| **巨测文件**（本卡主体地盘）= `backend/tests/skills/test_skill_portability_lint.py`，6294 行 / 349KB；在 B14_BASE 与 HEAD 逐字节同（不在 `08100483..HEAD` 代码 diff 内，该 diff 仅 `.claude/rules/card-batch-protocol.md` 一个纯文档 commit） | `wc -l`；`git diff --stat --no-color 081004834e37b1b0253cf81dc7b44e784646c934 HEAD -- . ':(exclude)_bmad-output'`（仅协议 1 文件） |
| **要抽出的解析器/判据区**：导入 `:154-173`（含 `import pytest` @ `:172`，但解析器本身不依赖 pytest）、`REPO_ROOT :175`（`Path(__file__).resolve().parents[3]`）、`DEFAULT_ROOT :176`（`REPO_ROOT/"canvas-vault"/".claude"`）、正则与解析 helper `:197` 起（`_TMP_TOKEN_RE :357`、`_fold_str :716`、`escaping_tmp_paths :985`、`tmp_block_fingerprints :2971` 等）、**12 个** `def check_`（`check_frontmatter :2418` / `check_body :2465` / `check_escaping_tmp :2486` / `check_suspicious_tmp_lines :2521` / `check_dynamic_tmp_joins :2549` / `check_tmp_blocks :3023` / `check_url_override :3046` / `check_opaque_tmp :3084` / `check_parent_dir_prose :3145` / `check_scripts :3175` / `check_handoff_constants :3208` / `check_managed_files :4441`）——⚠️ **口径更正③：实测 `grep -cE '^def check_'` = 12，非原稿「十一条」** | `grep -nE '^def check_\|^def tmp_block\|^_[A-Z_]+_RE\|^REPO_ROOT\|^DEFAULT_ROOT'`；`grep -cE '^def check_'` = 12 |
| **测试函数区**（留在 test 文件）：`test_*` 从 `:3274`（`test_layer1_frontmatter_matches_baseline`）起；实测 `def test_` **77** 个（全在顶层）+ `@pytest.mark.parametrize` ⇒ 该 grep = **90**；跑出 **546 passed**（§0.1，参数化展开后） | `grep -cE '^def test_'`=77；`grep -cE '^def test_\|^    def test_\|@pytest.mark.parametrize'`=90 |
| **判据常量（测试期望）**：`BASELINE :2025`、`TMP_BLOCK_BASELINE :2235`、`MANAGED_FILE_DIGESTS :4353` —— 其中 `"skills/start-exam-board/SKILL.md"` 的**整文件 sha256** 钉死 = `0f2c085a1bae12446dd74ab89cc1e6aa5c8bc34901dd3be7ac5d8521310d0dce`（@ `:4361`，`test_managed_files_match_digest_baseline` 第 11 条正控） | `sed -n '4353,4440p'`；`shasum -a 256 canvas-vault/.claude/skills/start-exam-board/SKILL.md` |
| **start-exam-board SKILL.md**（本卡地盘，本卡不改）：`/tmp/` 原始 6 处、`/tmp/cls-exam/` 命名空间 4 处 ⇒ 裸 2 处 = `:430`（`Write` 写 `/tmp/exam-created-event.json`）/ `:435`（`P = "/tmp/exam-created-event.json"`）；层 2 基线（test 文件 `:2108-2110`）`tmp_all=6 / tmp_ns=4`，`bare_tmp() :249` = 6-4 = **2** | `grep -oF '/tmp/' … \| wc -l`=6 / `grep -oF '/tmp/cls-exam/'`=4；`grep -nF '/tmp/'` = `:188/:198/:430/:435/:577` |
| **口径更正①（勘探→实测）**：设计稿 §4「start-exam-board 裸 `/tmp/` 4→2」在 B14_BASE 上 **已是 2**（第十三批 U4 CARD-SKILL-PORT-LINT 收工即 4→2，test 文件 `:2098` 注释「裸 4→2(剩 :430/:435)」）。T7-C **不再做 4→2**，只处置「2 残留」+ 抽模块 | test 文件 `:2092-2108` 注释；`bare_tmp` = 2 |
| **口径更正②（勘探→实测）**：`:430/:435` 硬钉点，设计稿/原卡文估「2 处」，**实测 4 处硬钉点**：`backend/tests/regression/test_g3_3_cas.py:49`（模块级 `_SEB_BLOCKS` 列表推导过滤 `'P = "/tmp/exam-created-event.json"' in b`，`:51` `assert len(_SEB_BLOCKS)==1`）+ 同文件 `:144`（`.replace('"/tmp/exam-created-event.json"', …)`）+ `test_learning_events_schema_contract.py:1013`（`matches=[… if 'P = "/tmp/exam-created-event.json"' …]`，`:1014` `assert len(matches)==1`）+ `:1017`（replace）。另 schema `:1016` 的 `tmp_path / "exam-created-event.json"`（无 `/tmp/` 前缀）非钉点 | `grep -nF 'exam-created-event.json' <两文件>` |
| **硬边界（地盘冲突，交主 session 裁）**：上列 4 钉点所在 2 文件 `backend/tests/regression/test_g3_3_cas.py` / `test_learning_events_schema_contract.py` **不在设计稿 §3 任何车道地盘**（grep 设计稿 §3 对两文件名零命中）⇒ 真把 `:430/:435` 改成命名空间必破这 2 文件的**模块级 collect**（`assert len(…)==1` 变 0 ⇒ collect-time ERROR），**T7-C 无权改这 2 文件**（§3 未授权、任务「不要自作主张扩面」）。本卡**不改 SKILL.md**（digest `0f2c085a…` 保持）、**不改 regression**，只登记残留与钉点 | grep 设计稿 §3 |
| **抽模块落点**：新文件 `backend/tests/skills/skill_portability_lint.py`；同目录已有 `__init__.py`（`backend/tests/__init__.py` 与 `backend/tests/skills/__init__.py` 都在）⇒ 包 `tests.skills`；`backend/pytest.ini` 为 rootdir 源；模块与 test 同目录 ⇒ `parents[3]` 算出同一 `REPO_ROOT` | `ls backend/tests/__init__.py backend/tests/skills/__init__.py backend/pytest.ini` |
| **基线**：tests/skills **546 passed**（§0.1）。⚠️ recon A §A-8：集成修复 `3966ddad`（改本 test 的「lint 基线接受快照」）**之后 skills 目录级未复跑**、且该集成存档 rc 与结果自相矛盾 ⇒ **不沿用集成存档**，开工第一件事自跑 tests/skills 一次取本地 546 绿基线落盘 | §0.1；recon A §A-8 |
| **本批纪律**：本卡**零触及 `backend/app`**（地盘全在 `backend/tests/skills/` + `canvas-vault/.claude/skills/start-exam-board/`），不触发 lefthook `python-typecheck`，**pyright 保持 0**（无新增 pyright 面）；判据 grep git 输出一律 `--no-color` + 同次验伪锚；承重裁判 `2>&1 \| tee evidence-skill-port-lint-parser/<name>-$(date +%Y%m%dT%H%M%S).txt`、末行 `rc=$pipestatus[1]`（zsh）、`.txt` 不 `.log`；ruff 判据 zsh 数组写法；**批中禁装/升任何包**；`fsrs_bridge.py` / `decay_beta.py` 零写者；live vault / 7691 / 7687 / 现网 LanceDB 只读 | 协议 §2.2 / §2.3 |

## 一 完成条件（AND）
- **(a) 第 0 分钟**：`pwd` = `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills`；`git rev-parse --abbrev-ref HEAD` = `card/t7-skills`；`git status --porcelain` 空；`git log --oneline -6` 含 `CARD-AILINKED-4TH-WRITER`（前提 T7-B 已独立 commit）与 `CARD-HARNESS-TREE-PARSE-REDO`（T7-A）；`git rev-parse HEAD` 记为 `<T7B_TIP>`（= 本卡地盘核与 Codex 绑定基线）；`test -e backend/.venv/bin/pytest && test -e backend/.env`。**开工逐字核 §〇 每条 file:line**（`sed -n`/`grep -nF`；漂移则在验收单写「卡文 :X → 实测 :Y」，不改卡文）。**开工基线**：自跑一次 `tests/skills` 取本地 546 绿落盘（⛔ 不沿用集成修复 `3966ddad` 后的存档，见 §〇 recon A §A-8）；`shasum -a 256 canvas-vault/.claude/skills/start-exam-board/SKILL.md` 存档（应 = `0f2c085a…`）。
- **(b) 先红①（模块依赖验伪锚——证明抽出真生效，不是留了文件内旧副本）**：抽出完成后，**临时**在**新模块** `skill_portability_lint.py` 里改坏一条判据（如令 `bare_tmp()` 恒返 `0`，或 `check_managed_files()` 恒返 `[]`），跑指定正控 `tests/skills/test_skill_portability_lint.py::test_layer2_body_counts_match_baseline`（或 `::test_managed_files_match_digest_baseline`）**必红**（红在该测试的基线断言），记红的 nodeid + 断言消息 ⇒ 证明 test 文件真的 `import` 了模块；随即**还原模块**、该测试回绿。⛔ 若改坏模块该测试**仍绿** = 抽出是假的（test 还在用文件内旧 `def`），停下重做，不得放行。
- **(c) 先红②（负控 = 设计稿「伪造一处 `/tmp/` 必红」）**：既有负控测试族（`test_negative_control_*`，主锚 **`test_negative_control_new_bare_tmp_reddens_layer2 :5191`**——这条正是设计稿「伪造一处裸 `/tmp/` 必红」的现成裁判；另点名 `test_negative_control_new_script_reddens_layer3_twice :5212` 与 `test_negative_control_hardcoded_port_in_script_reddens_layer3 :6069`）在 sandbox 喂入「新增一处裸 `/tmp/` / 写死端口 / 新脚本」时 **lint 必报 problem**（红在被测断言）；抽出后这些负控**仍全绿**（= 抽出后的 lint 仍能对坏输入变红）。列出 ≥1 条负控 nodeid + 其喂入的坏输入语义（存档）。`grep -cE '^def test_negative_control' test_skill_portability_lint.py` 实测 **25** 条负控（全保留）。
- **(d) 抽出（本卡核心交付）**：解析器/判据区（§〇 第 2 行的正则 + 解析 helper + 12 个 `check_*` + `_merged_*_baseline` 合并 helper + `REPO_ROOT`/`DEFAULT_ROOT` + 判据常量；常量归属由车道自决，可全搬或留 test 文件，只要行为等价）搬进 `backend/tests/skills/skill_portability_lint.py`；`test_skill_portability_lint.py` 改为从该模块导入（`from tests.skills.skill_portability_lint import *` 或逐名，车道自决）。**in-file 旧副本删尽**：`grep -cE '^def check_' backend/tests/skills/test_skill_portability_lint.py` = **0**（check_* 的 `def` 只在模块里）。**模块不 `import pytest`**（`grep -c '^import pytest\|^from pytest' skill_portability_lint.py` = 0）——判据是纯函数，供后续 / 他面静态复用。
- **(e) 行为零漂移**：抽出前后，12 个 `check_*` 对 `DEFAULT_ROOT` 的 problem 列表逐条空（tests/skills 全绿）；全部基线常量（`FRONTMATTER_KEYS`/`EXPECTED_SKILLS`/`BASELINE`/`SCRIPTS_BASELINE`/`U6_SCRIPTS_BASELINE`/`QUIZ_ANSWER_BASELINE`/`ESCAPING_TMP_BASELINE`/`SUSPICIOUS_TMP_LINES_BASELINE`/`DYNAMIC_TMP_JOIN_BASELINE`/`OPAQUE_TMP_BASELINE`/`URL_OVERRIDE_BASELINE`/`PARENT_DIR_PROSE_BASELINE`/`TMP_BLOCK_BASELINE`/`MANAGED_FILE_DIGESTS`）**值逐字节不变**（搬家不改值；若某常量随模块迁移，其 `repr()` 前后 `shasum` 相同）；`tests/skills` **546 passed 不变**（改前改后两存档 `passed` 数相等、无新红）。⚠️ **「基线指纹更新与理由」**：纯搬迁的**正确结果是零漂移**；若任何基线/指纹漂移，必在验收单逐条写理由并定位——漂移 = 抽出引入了行为变化 = 缺陷，不得靠「更新基线接受快照」掩盖。
- **(f) 模块独立可导入**（复用面，验伪锚自带）：`cd backend && python3 -c "from tests.skills.skill_portability_lint import check_frontmatter, check_tmp_blocks, DEFAULT_ROOT; print('import-ok')"` rc=0 且打印 `import-ok`（证明模块脱离 pytest 也能导入）；验伪锚：`python3 -c "from tests.skills.skill_portability_lint import _nonexistent"` 必 rc≠0（证明该 `python3 -c` 判据会对缺失符号报错，不是恒绿）。
- **(g) start-exam-board SKILL.md 不改**：`git diff --no-color <T7B_TIP> HEAD -- canvas-vault/.claude/skills/start-exam-board/SKILL.md` **空**；`shasum -a 256` 仍 = `0f2c085a1bae12446dd74ab89cc1e6aa5c8bc34901dd3be7ac5d8521310d0dce`；`bare_tmp`（`tmp_all=6/tmp_ns=4`）仍 = 2（基线未动）。
- **(h) 残留与钉点登记（doc-only，本卡地盘内，不改 SKILL.md/regression）**：在新模块（或 test 文件头交接注释）写明三条——(i) `:430/:435` 的 `/tmp/exam-created-event.json` = U4 4→2 的 2 残留（非新债）；(ii) 真改命名空间须同改 **4 处 regression 硬钉点** `test_g3_3_cas.py:49/:144` + `test_learning_events_schema_contract.py:1013/:1017`（模块级 collect，改字面量即 collect-time ERROR），引用用「文件名 + `_SEB_BLOCKS`/`matches` 条目名」不用行号（行号会漂）；(iii) 这 2 regression 文件**不在设计稿 §3 任何车道地盘** ⇒ 解耦需主 session 裁「扩 T7-C 地盘 / 另立带 regression 地盘的卡 / 维持残留登记」，本卡只登记不动手。
- **(i) 地盘核**：`git diff --stat --no-color <T7B_TIP> HEAD -- . ':(exclude)_bmad-output'` **只列** `backend/tests/skills/skill_portability_lint.py`（新）+ `backend/tests/skills/test_skill_portability_lint.py`（改 import）两文件；**不含** `canvas-vault/.claude/skills/start-exam-board/SKILL.md`、不含 `backend/app/**`、不含任何 `backend/tests/regression/**`、不含任何 `conftest.py`。⚠️ pathspec 必须写 `':(exclude)_bmad-output'`，**不写** `':!_bmad-output'`（zsh + 本机 git 2.50 报 `Unimplemented pathspec magic`、rc=128、stdout 空 ⇒「为空即绑定」会把没跑成读成绿，协议 §1）。同次带验伪锚：先证该 `git diff --stat` 能列出一个已知正例（即两文件确在列）。
- **(j) ruff + tests/unit 守卫**：改动的 backend `.py`（新模块 + test 文件）过 ruff——zsh 数组写法（§二）+ 验伪锚（喂一个已知含 F401 的临时文件必 rc=1，跑完删）。`tests/unit` 本卡**零触及**；为核 collection/path 无污染（新模块名无 `test_` 前缀 ⇒ 不被收集），可跑一次 `tests/unit` 目录级与基线 `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b14/unit-red-baseline-08100483.txt`（64 条，nodeid 口径）diff **只许 `<`**（预期**零 diff**，因本卡不碰该面；出现新红先停下报主 session）。
- **(k) Codex 多轮**：**Codex gpt-6-astra ultra 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0**（本卡有代码改动 ⇒ 多轮，上限 5 轮；第 5 轮仍有 HIGH 停下交主 session；审后再改代码必再送一轮；车道对 HIGH 的驳回写理由但不能自判通过；0 字节存档重发一次，再 0 字节 → 主 session 人审）。存档首部按协议 §2.1（见 §四）。
- **(l) 收口**：独立 commit（header ≤100 含批次标记且含 `CARD-SKILL-PORT-LINT-PARSER`；body 行 ≤100）；`*.stderr*` 不入库（`.gitignore` 已覆盖）；承重存档逐文件 `git add`（0 字节 / 含 `No such file` 的不入库）；**不改台账**（台账只主 session 改，卡在验收单写「台账待登记条目」）；**不 push**；`git status --porcelain` 空后同车道继续 T7-D。
- **(m)** 验收单「**本卡未证明什么**」≥4 条 + 「**台账待登记条目**」≥4 条必填（见 §四）。

## 二 裁判命令
```bash
# ── 第 0 分钟（cd 车道树；不在本树跑的文件用 feature 主干树绝对路径）──
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills
pwd; git rev-parse --abbrev-ref HEAD; git status --porcelain | head
git log --oneline -6 | grep -E 'CARD-AILINKED-4TH-WRITER|CARD-HARNESS-TREE-PARSE-REDO'   # 前提 T7-A/T7-B 在
T7B_TIP=$(git rev-parse HEAD); echo "T7B_TIP=$T7B_TIP"
test -e backend/.venv/bin/pytest && test -e backend/.env && echo env-ok
mkdir -p _bmad-output/审查/evidence-skill-port-lint-parser
EV=_bmad-output/审查/evidence-skill-port-lint-parser
shasum -a 256 canvas-vault/.claude/skills/start-exam-board/SKILL.md | tee $EV/seb-sha-before-$(date +%Y%m%dT%H%M%S).txt   # 应含 0f2c085a…

# ── 开工基线 + 收工正控：tests/skills 546（改前改后各一次，passed 数相等）──
( cd backend && .venv/bin/python -m pytest tests/skills -q -p no:cacheprovider ) 2>&1 \
  | tee $EV/skills-before-$(date +%Y%m%dT%H%M%S).txt; echo rc=$pipestatus[1]
# …（抽出 + 改 import 完成后再跑一次）…
( cd backend && .venv/bin/python -m pytest tests/skills -q -p no:cacheprovider ) 2>&1 \
  | tee $EV/skills-after-$(date +%Y%m%dT%H%M%S).txt; echo rc=$pipestatus[1]

# ── (b) 模块依赖验伪锚：改坏模块 → 指定正控必红 → 还原 → 回绿（逐条存档）──
( cd backend && .venv/bin/python -m pytest \
    tests/skills/test_skill_portability_lint.py::test_layer2_body_counts_match_baseline \
    tests/skills/test_skill_portability_lint.py::test_managed_files_match_digest_baseline -q ) 2>&1 \
  | tee $EV/module-verifier-$(date +%Y%m%dT%H%M%S).txt; echo rc=$pipestatus[1]

# ── (d) in-file 旧副本删尽 + 模块不依赖 pytest（验伪锚：grep 能命中一条已知正例）──
grep -cE '^def check_' backend/tests/skills/test_skill_portability_lint.py   # 期望 0
grep -cE '^def check_' backend/tests/skills/skill_portability_lint.py        # 期望 >0（验伪锚：判据能数到 def）
grep -cE '^import pytest|^from pytest' backend/tests/skills/skill_portability_lint.py   # 期望 0

# ── (f) 模块独立可导入 + 验伪锚 ──
( cd backend && .venv/bin/python -c "from tests.skills.skill_portability_lint import check_frontmatter, check_tmp_blocks, DEFAULT_ROOT; print('import-ok')" ) ; echo rc=$?
( cd backend && .venv/bin/python -c "from tests.skills.skill_portability_lint import _nonexistent" ) ; echo rc=$?   # 必 rc≠0

# ── (g) SKILL.md 未改 ──
git --no-pager diff --no-color $T7B_TIP HEAD -- canvas-vault/.claude/skills/start-exam-board/SKILL.md | tee $EV/seb-diff-$(date +%Y%m%dT%H%M%S).txt
shasum -a 256 canvas-vault/.claude/skills/start-exam-board/SKILL.md   # 仍 0f2c085a…

# ── (i) 地盘核（⛔ ':(exclude)…' 不写 ':!…'；验伪锚：应列出两文件）──
git --no-pager diff --stat --no-color $T7B_TIP HEAD -- . ':(exclude)_bmad-output' \
  | tee $EV/scope-$(date +%Y%m%dT%H%M%S).txt

# ── (j) ruff（zsh 数组 + F401 验伪锚）──
F=(${(f)"$(git diff --name-only --diff-filter=AM $T7B_TIP HEAD -- 'backend/**/*.py')"})
print -r -- "files=${#F}"; (( ${#F} )) || { echo "空集"; exit 1; }
( cd backend && .venv/bin/ruff check -- "${F[@]}" ) 2>&1 | tee $EV/ruff-$(date +%Y%m%dT%H%M%S).txt; echo rc=$pipestatus[1]
# F401 验伪锚：printf 'import os\n' > /tmp/f401probe.py; ruff check /tmp/f401probe.py 必 rc=1；跑完删

# ── (j) tests/unit 守卫（预期零 diff，基线在 feature 主干树）──
BASE=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b14/unit-red-baseline-08100483.txt
test -f "$BASE" && grep -vc '^#' "$BASE"   # 期望 64（自证基线存在）
```
承重裁判（两次 tests/skills、模块验伪锚、地盘核、ruff）一律 `2>&1 | tee $EV/<name>-$(date +%Y%m%dT%H%M%S).txt; echo rc=$pipestatus[1]`；验收单只**引用路径与末行 rc**，不自述数字。

## 三 禁改与隔离
- **本卡地盘（逐文件，= 设计稿 §3「只 T7」里 T7-C 的两项 + 本卡「另立模块」新文件）**：
  1. `backend/tests/skills/skill_portability_lint.py` —— **新文件**（「lint 解析器另立模块」交付；在本卡 test 文件同目录 `backend/tests/skills/`，无别的车道写此目录，见下）。
  2. `backend/tests/skills/test_skill_portability_lint.py` —— 改为从 1 导入，删 in-file 旧副本（设计稿 §3 列此为 T7-C 地盘）。
  3. `canvas-vault/.claude/skills/start-exam-board/SKILL.md` —— 设计稿 §3 列此为 T7-C 地盘，但**本卡刻意不改**（digest `0f2c085a…` 保持；真改须破 4 处 regression 钉点，见硬边界）。
- **⛔ 禁改（不在本卡地盘）**：`backend/tests/regression/test_g3_3_cas.py` / `test_learning_events_schema_contract.py`（4 处硬钉点所在，**不在设计稿 §3 任何车道地盘** ⇒ 本卡无权改；`:430/:435` 真解耦须主 session 先裁地盘）；`backend/app/**`（零文件，不触发 typecheck，**pyright 保持 0**）；`canvas-vault/.claude/skills/quiz-answer/SKILL.md`（T7-A）/ `ai-linked-doc/**` / `backend/app/core/learning_event_log.py`（T7-B）/ `scripts/verify_vault_install.py`（T7-D）；`backend/tests/conftest.py`（T9）/ `backend/tests/unit/conftest.py`（T9，T10 亦禁改）；`backend/tests/skills/` 下其余 test（`test_g5_6_clear_inbox.py` / `test_g5_9_recap_exam.py` / `test_split_*`）不动；`lefthook.yml` / `pyrightconfig.json`（T8）。
- **硬边界**：⛔ 禁写 live vault `/Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/**`（本卡只读 `canvas-vault/.claude/skills/start-exam-board/SKILL.md`，不落任何写）；⛔ 禁连 7691/7687；⛔ 禁碰 `canvas-vault/.claude/scripts/fsrs_bridge.py` / `decay_beta.py`（零写者，`grep -rn 'fsrs_bridge\|decay_beta' <两改动文件>` 应 0 命中）；⛔ 现网 LanceDB 目录只读；⛔ **批中禁装/升任何包**（本卡只用 `re`/`ast`/`shlex`/`yaml`/`pathlib` 等既有依赖）；禁 `git stash`（共享栈）；不改台账；不 push；`*.stderr*` 不入库；`.log` 后缀不用（仓根 `.gitignore` 全局吞 `*.log`）。
- **禁放宽判据**：(b) 的模块验伪锚**必须**改坏模块后指定正控变红才算「抽出真生效」——不得用「tests/skills 仍 546 绿」替代（旧副本没删也会 546 绿，是假绿）；(e) 的零漂移不得用「更新基线接受快照」掩盖行为变化；(c) 负控必须红在被测断言（不是 import/夹具错）。

## 四 Codex / 验收单
**命令**（协议 §2 固定）：`codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-SKILL-PORT-LINT-PARSER[-rN].md)" > _bmad-output/审查/codex-review-CARD-SKILL-PORT-LINT-PARSER[-rN].md 2> _bmad-output/审查/codex-review-CARD-SKILL-PORT-LINT-PARSER[-rN].stderr </dev/null`。
**轮次**：**Codex gpt-6-astra ultra 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0**（本卡有代码改动 ⇒ 多轮，**上限 5 轮**；最后一轮须绑最终 HEAD：`git diff --stat --no-color <审SHA> HEAD -- . ':(exclude)_bmad-output'` 为空且该轮 BLOCKER=0/HIGH=0，MEDIUM/LOW 登记；审后再改代码必再送一轮；车道对 HIGH 的驳回写理由但不能自判通过；第 5 轮仍有 HIGH 停下交主 session；0 字节存档重发一次，再 0 字节 → 主 session 人审）。
**存档首部**（协议 §2.1，六行 blockquote，缺 `模型 / reasoning_effort / codex` 任一字段该轮**不计配额**）：`批次 / 车道 T7 / 卡 CARD-SKILL-PORT-LINT-PARSER round-N` → `模型: gpt-6-astra · reasoning_effort: ultra · codex: <codex --version 实测值>` → `命令: …` → `审查绑定: <审SHA 或 A..B>`（HEAD 不同须写「不绑合并态」）→ `会话头自证：抄 .stderr 中含 codex 版本行 + model: 行 + reasoning effort 行的三行（行号不限、括注行号；codex 0.153.3 把 model: 排在会话头第 5 行，字面抄前三行会漏字段，按实测行号抄）` → 三行原文。`*.stderr*` 本身不入库。
**prompt 五分节**（⛔ 措辞禁用「构造 / 可复现片段 / 打穿 / 绕过」，改说「负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径」）：
- 一 背景 + **最小读取面写死**：`git diff <T7B_TIP> <审SHA> -- . ':(exclude)_bmad-output'` + 新模块 `backend/tests/skills/skill_portability_lint.py` 全文 + `test_skill_portability_lint.py` 的 import 段与被改动处 + `evidence-skill-port-lint-parser/` 的 before/after tests/skills 存档与模块验伪锚存档。
- 二 作者自述请独立核对：① 抽出是纯搬迁、行为零漂移（12 个判据与全部基线值逐字节不变、tests/skills 546 前后相等）；② in-file 旧 `def check_` 已删尽（test 文件真正依赖模块，非旧副本）；③ 模块不依赖 pytest、可独立导入；④ SKILL.md 未改、digest 保持、裸 `/tmp/` 仍 2；⑤ `:430/:435` 的 4 处 regression 钉点已登记、本卡未改 regression、未改 SKILL.md。
- 三 按重要性排序的问题：① 抽出是否**真**零漂移——有没有某条正则/helper 在搬家时因模块级求值顺序、`__file__` 基准、或 import 副作用而语义改变（`REPO_ROOT = parents[3]` 在模块与 test 同目录下是否仍指同一路径）；② in-file 与模块是否存在**双份**同名判据导致 test 实际调的是旧副本（模块验伪锚是否真的红了指定正控，红在断言而非 import 错）；③ 模块被 T2-C 等静态面复用时，`DEFAULT_ROOT` 写死 `canvas-vault/.claude` 是否限制了复用（登记，不在本卡改）；④ 负控测试族抽出后对「新增一处裸 `/tmp/`」是否仍红（门未覆盖的路径有没有因搬家扩大）；⑤ `:430/:435` 残留登记是否准确描述了 4 处钉点与跨地盘约束。
- 四 输出格式：BLOCKER/HIGH/MEDIUM/LOW + file:line + 一句复现思路（措辞守上方禁用词）。
- 五 边界：只读、不连库、不跑 tests/regression 目录级（pact/真服务会挂）、不评 SKILL.md `:430/:435` 的真解耦方案设计（跨地盘，交主 session）、不评第十三批 U4 已定版的 12 个判据语义本身。
**验收单** `_bmad-output/验收单/UAT-CARD-SKILL-PORT-LINT-PARSER-<日期>.md`，DoD-3 双段：4-A Claude 已代验（tests/skills 546 前后存档、模块验伪锚红/绿、`python3 -c` import-ok、ruff rc=0、地盘两文件、SKILL.md digest `0f2c085a…`、tests/unit 64 基线零 diff）；4-B 零技术词、「我做 X → 我看到 Y → 我感觉 Z」+ felt-sense（如「我随便在一份技能说明里偷偷写一条临时路径 → 保存后那道检查立刻标红 → 我感觉这道‘防止把临时文件写死’的闸门搬了家也照样拦得住，放心」）。
**本卡未证明什么**（≥4）：① 未证明把 `:430/:435` 改成 `/tmp/cls-exam/` 后 4 处 regression 钉点的真解耦方案正确——本卡不改 regression/SKILL.md（跨地盘，交主 session 裁）；② 未证明抽出的模块在 Python 3.11（CI）行为一致——本地 venv 3.14（只用 `re`/`ast`/`shlex`/`yaml`/`pathlib`/`hashlib`，无版本敏感 API，但未实跑 3.11）；③ 未证明 12 个判据语义本身正确——那是第十三批 U4 已定版结论，本卡只搬家不重评；④ 未证明模块被 T2-C/deploy-vault 等复用面的实际可用性（本卡只证「可被独立导入」，未证复用方真跑）；⑤ 未证明 `DEFAULT_ROOT` 写死 `canvas-vault/.claude` 不限制复用（登记，不改）；⑥ 未证明 tests/skills 的 546 在隔离容器/CI 下同值（本地候选树口径）。
**台账待登记条目**（≥4）：① CARD-SKILL-PORT-LINT-PARSER 抽模块完成 → 修复 sha + 新文件 `backend/tests/skills/skill_portability_lint.py` + 模块验伪锚 nodeid（`test_layer2_body_counts_match_baseline` / `test_managed_files_match_digest_baseline`）；② **口径更正①**：设计稿 §4「裸 `/tmp/` 4→2」在 B14_BASE 已是 2（U4 收工即 4→2），T7-C 只处置残留；③ **口径更正②**：`:430/:435` 硬钉点实测 **4 处**（`test_g3_3_cas.py:49/:144` + `test_learning_events_schema_contract.py:1013/:1017`），非原估 2 处；④ **跨地盘裁定请求**：`:430/:435` 真解耦须改的 2 regression 文件不在设计稿 §3 任何车道地盘，主 session 须裁「扩 T7-C 地盘 / 另立带 regression 地盘的卡 / 维持残留登记」（本卡已登记残留、未动手）；⑤ SKILL.md 保持 digest `0f2c085a…`、裸 `/tmp/` 仍 2；⑥ Codex 各轮存档路径、绑定 SHA、B/H/M/L 计数；⑦ tests/unit 64 基线零 diff 结果存档路径；⑧ recon A §A-8 的集成存档 rc 自相矛盾问题——本卡已自跑 tests/skills 取本地绿基线（不沿用集成存档）。
**commit** header ≤100 含批次标记且含 `CARD-SKILL-PORT-LINT-PARSER`；body 行 ≤100；`*.stderr*` 不入库；独立 commit + `git status --porcelain` 空后同车道继续 **T7-D CARD-G2-7a-TAIL**；**不 push**；跑完说「**复核第十四批 T7**」。
