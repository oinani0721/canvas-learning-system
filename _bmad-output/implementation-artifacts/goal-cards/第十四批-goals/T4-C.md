> ⚠️ 本文件是 CARD-U9B-OPENSPEC 的完整卡文——车道开工后必读并逐条执行；它不是 /goal 粘贴文本。/goal 在第十四批手册 §三 T4-C 块。
> 批次标记 `[BATCH-2026-09-11-第十四批 / CARD-U9B-OPENSPEC]`。车道：`card-t4-g3`（分支 `card/t4-g3`，NEW @ `08100483`，venv symlink 已建、`backend/.env` 在），本车道第 3/4 张，前提 = **T4-B CARD-G6-10 已独立 commit 且 `git status --porcelain` 空**，之后串 T4-D CARD-U9C-EVAL。用户已裁：R-07（U9-B OpenSpec 产品动作归第十四批）/ D-15（Codex 多轮直到绑最终 HEAD 的一轮无 BLOCKER/HIGH）。⛔ 处置口径 = **默认「补一条替代 Requirement 让 archive 过」**（主 session 2026-09-11 设计稿 §4 T4-C 定，覆盖 UAT-CARD-G3-7-R2 §8.5 当时「分支乙：仅登记移交、spec 一字未动」的裁定）。勘探 2026-09-11 于主干 `08100483`（代码态；本树 HEAD `e58d5c5c` = 08100483 + 1 个纯协议文档 commit，本卡三个地盘文件在两点间 diff 为空，实测有效）。来源：recon_A_report.md §B.5「U9-B OpenSpec 产品动作」+「U9-B 两处裸名字 + models 标注」；UAT-CARD-G3-7-R2-2026-09-08.md §8 / §10.6 / §11.11 / §11.3 / §11.6；设计稿 §4 T4-C。协议（⛔ 读 feature 主干 `--add-dir` 那份绝对路径）：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/.claude/rules/card-batch-protocol.md`（§1 合并门 + D-15 轮次 / §2.1 存档首部 / §2.2 裁判落盘 + --no-color / §3 最低覆盖）。手册同理只读主干那份：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-09-11-第十四批开跑手册-10车道43卡.md`（§零 / §一 / §四）。⚠️ **车道树自己的协议/手册是 08100483 版、不含本批回写，别读那份；本批回写只在 feature 主干 `--add-dir` 那份。**

# CARD-U9B-OPENSPEC — concept-identity 悬空 Requirement 退役替代（补一条实现态 Requirement 让 archive 不再撞「Spec must have at least one requirement」）+ 两处裸名字 `save_card_state` 更正归零

## 〇 事实

| 事实 | 位置 / 实测命令 |
|---|---|
| **⛔ 口径更正①（最关键）**：A B.5 / 设计稿写「archive 被工具硬不变量拒」——实测 `npx --no-install openspec validate concept-identity --type spec --strict` 在主干上 **already "is valid"**（spec 结构合法：1 Requirement + 3 个 4 井号 Scenario）。真正被拒的是 **archive**：退役 change 把唯一 Requirement 整条 REMOVE 后重建 spec 变空，CLI 抛 `Spec must have at least one requirement` 中止。**「validate --strict PASS」不是本卡的鉴别裁判**（改前就绿）；鉴别裁判是 **archive 不再撞 SPEC_NO_REQUIREMENTS**（先红后绿在此）。 | `npx --no-install openspec validate concept-identity --type spec --strict` → `Specification 'concept-identity' is valid`（主干实测） |
| spec 现状 = 1 个**悬空**（描述未实现行为）Requirement `FSRS Card State Legacy Bucket Preservation On Save` + 3 个 `#### Scenario:`（4 井号；3 井号会静默失败）；3796 字节 | `grep -cE '^### Requirement:' openspec/specs/concept-identity/spec.md` = **1**；`grep -cE '^#### Scenario:' …` = **3**；`grep -cE '^### Scenario:' …` = **0** |
| 悬空实证（语义，非结构）：spec 描述「双桶」模型 `_card_states` + `_legacy_card_states`，按 `is_uuid_v4(key)` 分桶——**两者在生产代码中均不存在** | `git --no-pager grep -nE '_legacy_card_states|is_uuid_v4' -- backend/app` = **0 命中**（UAT §11.3 同法；口径限生产代码，docs/spec 里仍有字符串） |
| 悬空实证：spec Scenario 3 调 `review_service.save_card_state(concept_id=…, concept_name=…, …)`——该公共方法**已退役**（第十三批 CARD-G3-7-R2），主干已无其定义 | `grep -nE 'def save_card_state\b' backend/app/services/review_service.py` → exit 1（不存在）；同语义现由 `_save_card_states` 承担 |
| **口径更正②**：recon/退役 change 草稿引 `review_service.py:2364` 的 `save_card_state` 签名——该行签名在 08100483 已不复存在（方法退役），引它追溯会指空；卡文引用一律用符号名 | `grep -nF 'async def _save_card_states' backend/app/services/review_service.py` = **920**（唯一真实持久化通道） |
| ARCHIVE blocker 原文（UAT §8.3，在 `card-u9-mastery @ 8f7440ef` 实测；08100483 的 spec 内容逐字同 1 req/3 scen ⇒ 确定性复现）：`Validation errors in rebuilt spec for concept-identity (will not write changes): ✗ Spec must have at least one requirement / Aborted. No files were changed.` ⚠️ 该次 `ARCHIVE_RC=0`（中止却退 0）——**判据靠主 spec sha 前后相同，不是 rc** | UAT-CARD-G3-7-R2-2026-09-08.md §8.3 / §8.4 |
| 替代 Requirement 应描述的**真实行为**（DD-01/DD-13 名实一致，卡文引符号名）：`_save_card_states()`（:920）把**单桶** vault-scoped `self._card_states`（init 在 :850 经 `_load_card_states`，无分桶）原子写（临时文件 + rename）到 `_CARD_STATES_FILE`（:124 = `data/fsrs_card_states.json`），全程在 `async with _card_states_lock:`（:949；锁定义 :127）临界区内；它是**投影/缓存**非 FSRS 调度真相源（frontmatter 才是），`persisted` 不得冒充 `truth_source`（docstring CARD-G3-7） | `sed -n '920,965p'` / `grep -nF '_card_states_lock = asyncio.Lock()'`（:127）/ `grep -nF 'self._card_states: "_VaultScopedCardStates" = self._load_card_states()'`（:850）/ `grep -nF '_CARD_STATES_FILE = '`（:124）|
| **两处裸名字**（`-w save_card_state`；退役后 DD-13 名实不符，UAT §11.11 点名移交本卡）：`docs/project-status/fr-exploration/A6-phase0-reference-card.md:96`（「3. Save preserves new UUID entries written via save_card_state」）+ `backend/tests/regression/test_g3_7_truth_source.py:14`（「④ save_card_state → 隔离（仅注释…）」，在模块 docstring 内） | `sed -n '96p' docs/…/A6-phase0-reference-card.md`；`sed -n '14p' backend/tests/regression/test_g3_7_truth_source.py` |
| **口径更正③**：UAT「两处」只指**地盘外**两处；`openspec/specs/concept-identity/spec.md` 本身还有 **3 处** 裸名字（:14/:35/:39，均在悬空 Requirement 文本内），由替换 Requirement **自然清零**。三文件逐文件计数 = spec.md **3** / A6 **1** / test_g3_7 **1** | `for f in openspec/specs/concept-identity/spec.md docs/project-status/fr-exploration/A6-phase0-reference-card.md backend/tests/regression/test_g3_7_truth_source.py; do echo "$(git --no-pager grep -cw save_card_state -- "$f") $f"; done` |
| **地盘外的裸名字是故意保留的**（不得动）：`backend/tests/unit/test_review_service_fsrs.py:611-612`（退役防复活断言 `assert not hasattr(svc,"save_card_state")`）、`docs/fsrs-truth-source-d0-revision.md:68`、`docs/known-gotchas.md:18/:139`（退役文档）、`openspec/changes/archive/2026-04-07-a6-phase0-…/**`（**不可变历史档案**）——故 grep 裁判必**收窄到地盘三文件**，否则正确执行后仍恒红（UAT §11.11 同口径） | `git --no-pager grep -lw save_card_state -- . ':(exclude)_bmad-output'` |
| `ConceptState.fsrs_*` 标注需求 = **只登记**（`models/**` 本批零写者，UAT §11.6 移交面）：`class ConceptState`（mastery_state.py:69），字段 `fsrs_stability`:87 / `fsrs_difficulty`:88 / `fsrs_state`:89 / `fsrs_reps`:90 / `fsrs_lapses`:91 / `fsrs_card_data`:92。**本卡一个字节不碰 models/**，仅在验收单「台账待登记条目」写一行移交** | `grep -n 'class ConceptState' backend/app/models/mastery_state.py`（:69）；`grep -n 'fsrs_' backend/app/models/mastery_state.py` |
| CLI 实测：`npx --no-install openspec --version` = **1.2.0**；`archive` 选项只有 `-y/--skip-specs/--no-validate`（**无 `--dry`**，`--skip-specs` = 根本不改主 spec = 没退役）；`validate` 有 `--specs/--type spec/--strict/--json` | `npx --no-install openspec archive --help` / `validate --help` |
| ⛔ **gitignore 陷阱**：`.gitignore:188 openspec/changes/*/` 忽略在途 change、`:189 !openspec/changes/archive/` 放行档案。⇒ 在 `openspec/changes/<name>/` 建的临时 change **不会进 commit**；但**真跑 `archive`** 会把它移到 `openspec/changes/archive/<日期>-<name>/`（tracked，**在本卡地盘之外**）。故 **archive 证明必须在仓外 SCRATCH COPY 上跑**，真实树只留地盘三文件的手改 | `grep -n openspec .gitignore`（:188/:189） |
| 本批纪律（§0.2）：**T4-C 不触及 `backend/app`**（地盘 = openspec/specs + docs + backend/tests），**不计 pyright 门、不属 APP_CARDS**；判据 grep git 输出一律 `--no-color` + 同次验伪锚；evidence 用 `.txt` 不 `.log`；承重裁判末行 `rc=$pipestatus[1]`（zsh）；ruff 判据 zsh 数组写法（本卡不跑 ruff，仅纪律备忘）；**批中禁装/升任何包**；`fsrs_bridge.py`/`decay_beta.py` ⛔ 零写者；live vault / 7691 / 7687 / 现网 LanceDB 只读 | 设计稿 §0.1/§0.2 |

## 一 完成条件（AND）

> 每条可判定（命令 + 期望值）；承重裁判按 §二 `tee` 落盘。

- **(a) 第 0 分钟（环境 + 基线自证）**：`pwd` 在 `card-t4-g3` 车道树；`git rev-parse --abbrev-ref HEAD` = `card/t4-g3`；`PREV=$(git rev-parse HEAD)` 记下（= T4-B CARD-G6-10 末 commit，且是 `08100483` 的后代，`git merge-base --is-ancestor 081004834e37b1b0253cf81dc7b44e784646c934 HEAD` rc=0）；`git status --porcelain` **空**（前提 = T4-B 已独立 commit + 干净）；`test -L backend/.venv && test -f backend/.env`；基线自证 `grep -vc '^#' "$BASE"` = **64**（`BASE=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b14/unit-red-baseline-08100483.txt`）；CLI 自证 `npx --no-install openspec --version` = `1.2.0`。
- **(b) 先红：archive blocker 复现（仓外 SCRATCH COPY）**：把 `openspec/` 整树拷到仓外 scratch（如 `$TMPDIR/u9b-before/openspec`），在拷贝内经 CLI 建一条退役 change（`openspec new change` → 填四件套，spec delta 用 `## REMOVED Requirements` 整条移除悬空 Requirement）→ `npx openspec archive <name> -y` 的 stdout **必含** `Spec must have at least one requirement`，且拷贝内主 spec `shasum` 前后**相同**（判据 = 文本 + sha，**不看 rc**，见 §〇 ARCHIVE_RC=0 陷阱）。落盘 `evidence-u9b-openspec/before-archive-*.txt`。⚠️ 真实仓内**不**建 change、**不**跑 archive。
- **(c) 改 spec（地盘内，手改 `openspec/specs/concept-identity/spec.md`）**：把悬空 Requirement `FSRS Card State Legacy Bucket Preservation On Save` + 其 3 个 Scenario **整段替换**为**一条实现态替代 Requirement**，要求：① 描述 §〇「真实行为」行（`_save_card_states` 单桶投影序列化契约，引符号名 `_save_card_states` / `_card_states` / `_card_states_lock` / `_CARD_STATES_FILE`，**不出现裸 `save_card_state`**）；② `### Requirement:` 标题 + SHALL/MUST 描述；③ **≥1 个 `#### Scenario:`（恰 4 井号）** + Given/When/Then；④ **不动** `## Purpose` 占位符（A6:102-108 用户裁定：phase1 change 归档时再填，非本卡 scope）。替代 Requirement 必须只陈述**已实现且可在 review_service.py 验证**的不变式，禁止发明新契约（DD-01/DD-04）。
- **(d) 后绿：validate + archive 证（仓外 SCRATCH COPY）**：`npx --no-install openspec validate concept-identity --type spec --strict` → `is valid`；结构门 `grep -cE '^### Requirement:'` **≥1** + `grep -cE '^#### Scenario:'` **≥1** + `grep -cE '^### Scenario:'` **= 0**（防 3 井号静默失败）；把**改后** `openspec/` 整树拷到仓外 scratch（`$TMPDIR/u9b-after/openspec`），建一条 `## MODIFIED Requirements` re-state 替代 Requirement 的 change，`npx openspec archive <name> -y` **成功**且 stdout **不含** `Spec must have at least one requirement`（即 blocker 已解）。落盘 `evidence-u9b-openspec/after-archive-*.txt`。
- **(e) 两处裸名字更正（地盘内）**：`A6-phase0-reference-card.md` 的「当前内容」描述块（:93-96）改为匹配**新** spec 的 Requirement/Scenario 名（line 96 的 `save_card_state` 去掉）；`test_g3_7_truth_source.py:14` 的 `save_card_state` → `_save_card_states`（模块 docstring 注释，**纯文案、无逻辑变化**，描述的 decision.md 裁定④ 语义不变）。**先红后绿（归零）**：改前 `git --no-pager grep -cw save_card_state --` 三文件 = spec.md `3` / A6 `1` / test_g3_7 `1`（验伪锚：先证 grep 能命中正例）；改后三文件各 = **0**。
- **(f) 地盘核**：`git --no-pager diff --stat --no-color $PREV HEAD -- . ':(exclude)_bmad-output'` 列出的文件 **⊆** {`openspec/specs/concept-identity/spec.md`, `docs/project-status/fr-exploration/A6-phase0-reference-card.md`, `backend/tests/regression/test_g3_7_truth_source.py`}（恰 3 个或更少，**一个越界都不行**）；`git status --porcelain -- openspec/changes/` **空**（档案/在途 change 零改动）；`git status --porcelain -- backend/app/models/` **空**（models 零写者）。
- **(g) test_g3_7 不破**：`python3 -c "import ast,sys;ast.parse(open('backend/tests/regression/test_g3_7_truth_source.py',encoding='utf-8').read())"` rc=0；`git --no-pager diff --no-color -- backend/tests/regression/test_g3_7_truth_source.py` 只显示 **:14 一行**改动（docstring）；承重裁判**必须先 `cd backend` 再用相对路径**跑 `PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -m pytest --collect-only tests/regression/test_g3_7_truth_source.py -q -p no:cacheprovider`（手册 §四.1.5 / R-B14-3 同口径），期望 `collected N items` 且 **0 collection error**。⛔ 从车道树根跑 `-m pytest backend/tests/…` 是**假红**：`backend/pytest.ini` 无 `pythonpath`、venv 内无 app 的 editable 安装、`backend/tests/conftest.py` 的 `from tests.support import live_port_guard`（:26）与 `from app.config import …`（:30）也无 `sys.path` 注入 ⇒ 只有 CWD=`backend/` 时可解析。故存档里若出现 `ModuleNotFoundError`/`ImportError`，那是**用法错**、改正后重跑，⛔ **不得**记成「环境缺失 SKIP」（= 把用法错洗成假绿）；只有非 import 类的真实环境缺失才可记 SKIP 并写明缺什么。
- **(h) tests/unit 目录级 diff 只许 `<`**：T4-C 不碰 `backend/tests/unit/`，开工/收工各跑一次目录级并 `diff`（nodeid 口径），差集**只许 `<`（消失/修复）不许 `>`（新增红）**；基线 `evidence-b14/unit-red-baseline-08100483.txt` = 64（`grep -vc '^#'` 口径，R-B14-2）；⛔ 跑法必须 **`cd backend` 后 `--ignore tests/unit/test_deploy_vault_sh.py`（相对路径，R-B14-3，与基线文件头记录的跑法逐字同）**——写成 `--ignore backend/tests/unit/…` 在 `cd backend` 之后**不匹配任何被收集文件 = 空操作**，该重型文件仍会被真收集并挂起；⛔ 承重那跑的存档名先固定成变量、禁 glob（≥2 份会给 grep 每行加「文件名:」前缀使 diff 全变假阻断）。预期**零差异**（本卡不动 unit）。
- **(i) ConceptState.fsrs_* 只登记**：`backend/app/models/**` 一字不碰（见 (f)）；验收单「台账待登记条目」写一条：`ConceptState.fsrs_*`（mastery_state.py:69 / :87-92）标注需求移交（models/** 本批零写者，UAT §11.6）。
- **(j) 硬边界遵守**：现网 LanceDB/backups/live vault 只读；未连 7691/7687；未碰 `fsrs_bridge.py`/`decay_beta.py`；未 `git stash`；未改台账；批中未装/升任何包；未 push。
- **(k) Codex 多轮（D-15）**：本卡改动含 `.py`（test_g3_7 docstring）+ spec/doc，按「有代码改动」走多轮，`Codex gpt-6-astra ultra 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0`（上限 5 轮；审后再改代码必再送一轮；只改 `_bmad-output` 不算）；纯 docstring/文案改动预期 1–2 轮收敛。存档首部按协议 §2.1。
- **(l) 收尾**：验收单 `UAT-CARD-U9B-OPENSPEC-<日期>.md`（DoD-3 双段；「本卡未证明什么」「台账待登记条目」各 **≥4** 条必填）；commit header ≤100 含批次标记与卡号 `CARD-U9B-OPENSPEC`；`*.stderr*` 不入库；独立 commit（后续串 T4-D）；不 push；跑完说「复核第十四批 T4」。

**本卡未证明什么（≥4，验收单必填）**：① 未证明 change 目录的完整 CLI 往返（`openspec new/instructions/status`）在车道树真实 commit——change 被 `.gitignore:188` 忽略，archive 证明只在仓外 scratch 跑；② 未在真实仓内跑 `openspec archive`（会污染 `changes/archive/` 越地盘），故「主 spec 由 CLI 合入」路径只在 scratch 验证、真实树是手改；③ 未证明替代 Requirement 描述的单桶序列化契约在**运行期**被真实调用覆盖（只静态引 review_service.py 符号，未跑 FSRS 端到端）；④ 未证明 `_save_card_states` 的并发/原子写在真 7692 环境的行为（硬边界只读，未连库）；⑤ 未证明 `test_g3_7_truth_source.py` 全量绿（docstring 改动 + collect-only，未跑完整 regression）。

**台账待登记条目（≥4，验收单写，台账只主 session 改）**：① concept-identity spec 悬空 Requirement 已由替代 Requirement 退役（手改主 spec，非 CLI archive；change 草稿仍在 `evidence-g37r2/openspec-draft-retire-fsrs-legacy-bucket-spec/`，**未用其 REMOVE 方案**，改用替代方案）；② 两处裸名字 A6:96 / test_g3_7:14 已归零，地盘外三处（test_review_service_fsrs / fsrs-truth-source-d0-revision / known-gotchas）与 archive 档案故意保留；③ `ConceptState.fsrs_*`（mastery_state.py:69/:87-92）标注需求移交（models/** 零写者）；④ **口径更正**：archive blocker 是 `SPEC_NO_REQUIREMENTS`（validate 本就 PASS），退役 change 引的 `save_card_state:2364` 签名已不存在，spec.md 本身含第三处裸名字由替换自然清零——三条供主 session 回写设计稿/A B.5；⑤ 建议主 session 裁：是否需在真实树补跑一次 CLI archive 把退役正式归档进 `openspec/changes/archive/`（越本卡地盘，故未做）。

## 二 裁判命令

```zsh
# ── 车道树（逐条替换 <你的 card-t4-g3 绝对路径>；本卡在 card-t4-g3）──
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3
EV=_bmad-output/审查/evidence-u9b-openspec; mkdir -p "$EV"
BASE=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b14/unit-red-baseline-08100483.txt

# (a) 第 0 分钟
git rev-parse --abbrev-ref HEAD; PREV=$(git rev-parse HEAD); echo "PREV=$PREV"
git merge-base --is-ancestor 081004834e37b1b0253cf81dc7b44e784646c934 HEAD; echo "anc_rc=$?"
git status --porcelain; test -L backend/.venv && test -f backend/.env && echo "env OK"
grep -vc '^#' "$BASE"                               # 期望 64
npx --no-install openspec --version                 # 期望 1.2.0

# (e 先红验伪锚) 改前三文件裸名字计数（先证 grep 能命中正例）
for f in openspec/specs/concept-identity/spec.md \
         docs/project-status/fr-exploration/A6-phase0-reference-card.md \
         backend/tests/regression/test_g3_7_truth_source.py; do
  echo "$(git --no-pager grep -cw save_card_state -- "$f") $f"
done                                                # 期望 3 / 1 / 1

# (b) 先红：archive blocker 复现（仓外 SCRATCH COPY；真实仓内不建 change）
# ⚠️ 非粘贴即跑：中间「写 delta」是车道 agent 手工步骤（openspec CLI 固有，见 §一(b)）；new/archive 可脚本化，填 delta 不可省。
SB=$(mktemp -d)/openspec; mkdir -p "$(dirname "$SB")"; cp -R openspec "$SB"; SBD="$(dirname "$SB")"
( cd "$SBD" && npx --no-install openspec new change retire-concept-identity-dangling )
# ▶ 手工步骤（非脚本，不可省）：在 $SBD 的 change 目录内，按
#   `npx --no-install openspec instructions <artifact> --change retire-concept-identity-dangling --json` 取模板，
#   写 proposal.md（## Why / ## What Changes）+ specs/concept-identity/spec.md（`## REMOVED Requirements` 整条移除悬空 Requirement）。
#   不写 delta ⇒ archive 不会撞 SPEC_NO_REQUIREMENTS，「先红」拿不到。
( cd "$SBD" && npx --no-install openspec archive retire-concept-identity-dangling -y ) \
  2>&1 | tee "$EV/before-archive-$(date +%Y%m%dT%H%M%S).txt"; echo "rc=$pipestatus[1]"
grep -cF 'Spec must have at least one requirement' "$EV"/before-archive-*.txt   # 期望 ≥1

# ── 此处执行 (c) 改 spec + (e) 改 A6 / test_g3_7 ──

# (d) 后绿：validate + 结构门
npx --no-install openspec validate concept-identity --type spec --strict \
  2>&1 | tee "$EV/validate-after-$(date +%Y%m%dT%H%M%S).txt"; echo "rc=$pipestatus[1]"   # 期望 "is valid"
grep -cE '^### Requirement:'  openspec/specs/concept-identity/spec.md    # ≥1
grep -cE '^#### Scenario:'    openspec/specs/concept-identity/spec.md    # ≥1
grep -cE '^### Scenario:'     openspec/specs/concept-identity/spec.md    # 0（防 3 井号）
# (d) archive 证（仓外 SCRATCH COPY of 改后树）——同 (b)，中间「写 delta」为手工步骤，非粘贴即跑
SA=$(mktemp -d)/openspec; mkdir -p "$(dirname "$SA")"; cp -R openspec "$SA"; SAD="$(dirname "$SA")"
( cd "$SAD" && npx --no-install openspec new change restate-concept-identity )
# ▶ 手工步骤（非脚本，不可省）：取模板写 specs/concept-identity/spec.md
#   （`## MODIFIED Requirements` re-state 替代 Requirement + 4 井号 Scenario）。详见 §一(d)。
( cd "$SAD" && npx --no-install openspec archive restate-concept-identity -y ) \
  2>&1 | tee "$EV/after-archive-$(date +%Y%m%dT%H%M%S).txt"; echo "rc=$pipestatus[1]"
grep -cF 'Spec must have at least one requirement' "$EV"/after-archive-*.txt    # 期望 0

# (e 后绿) 三文件裸名字归零
for f in openspec/specs/concept-identity/spec.md \
         docs/project-status/fr-exploration/A6-phase0-reference-card.md \
         backend/tests/regression/test_g3_7_truth_source.py; do
  echo "$(git --no-pager grep -cw save_card_state -- "$f") $f"
done                                                # 期望 0 / 0 / 0

# (f) 地盘核
git --no-pager diff --stat --no-color "$PREV" HEAD -- . ':(exclude)_bmad-output'
git status --porcelain -- openspec/changes/          # 空
git status --porcelain -- backend/app/models/         # 空

# (g) test_g3_7 不破
python3 -c "import ast;ast.parse(open('backend/tests/regression/test_g3_7_truth_source.py',encoding='utf-8').read())" && echo "ast OK"
git --no-pager diff --no-color -- backend/tests/regression/test_g3_7_truth_source.py   # 只 :14 一行
# ⛔ 必须 cd backend + 相对路径（手册 §四.1.5 / R-B14-3）：从树根跑会在 conftest 阶段 ModuleNotFoundError = 假红
TSG=$(date +%Y%m%dT%H%M%S); RUNG="$EV/collect-g37-$TSG.txt"
( cd backend && PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -m pytest --collect-only \
    tests/regression/test_g3_7_truth_source.py -q -p no:cacheprovider ) 2>&1 | tee "$RUNG"; echo "rc=$pipestatus[1]"
grep -cE 'ModuleNotFoundError|ImportError' "$RUNG"   # 期望 0；≠0 = 用法错(未 cd backend)，改正重跑，禁记 SKIP

# (h) tests/unit 目录级 diff 只许 <（开工/收工各一跑，本卡预期零差异）
# ⛔ cd backend + --ignore 相对路径（R-B14-3；写 backend/tests/unit/… 在 cd 后是空操作，重型文件会被真收集并挂起）
# ⛔ 承重那跑的存档名先固定成变量，禁 glob（多份会给 grep 每行加文件名前缀，使 diff 全变假阻断）
TSU=$(date +%Y%m%dT%H%M%S); RUNU="$EV/unit-close-$TSU.txt"
( cd backend && PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -m pytest tests/unit -q -p no:cacheprovider \
    --ignore tests/unit/test_deploy_vault_sh.py ) 2>&1 | tee "$RUNU"; echo "rc=$pipestatus[1]" | tee -a "$RUNU"
grep -E '^(FAILED|ERROR) tests/' "$RUNU" | sed 's/ - .*//' | sort -u > "$EV/close.nodeids"
grep -v '^#' "$BASE" | sort -u > "$EV/base.nodeids"
diff "$EV/base.nodeids" "$EV/close.nodeids"   # 只允许 < 行（消失/修复）；任何 > = 本卡引入红 = 阻断
```

> ⚠️ (b)/(d) **不是粘贴即跑**（openspec Hybrid 固有：CLI 管结构/校验/归档，delta 内容由 agent 按模板编写）——`▶ 手工步骤` 行已在 §二 内标出承重判据的可执行边界：`openspec new change` 与 `archive` 可脚本化，中间填四件套（proposal `## Why`/`## What Changes`；spec delta `## REMOVED`/`## MODIFIED Requirements` + 4 井号 Scenario）须手工。scratch 在仓外 `mktemp -d`，**零污染真实树**；跳过手工填 delta 则 archive 不触发/不解除 SPEC_NO_REQUIREMENTS，(b)/(d) 期望值均拿不到。

## 三 禁改与隔离

**地盘（只允许改这 3 个文件）**：
- `openspec/specs/concept-identity/spec.md`（替换悬空 Requirement）
- `docs/project-status/fr-exploration/A6-phase0-reference-card.md`（:93-96 描述块更新）
- `backend/tests/regression/test_g3_7_truth_source.py`（仅 :14 docstring 裸名字更正）

**禁改面**：
- `openspec/changes/archive/2026-04-07-a6-phase0-fsrs-card-state-bucket-preservation/**`（**不可变历史档案**，含多处 `save_card_state`，是原始措辞来源，一字不动）；
- `openspec/specs/` 下其它 13 个 capability；`openspec/config.yaml`；`openspec/changes/`（不在真实仓内建/跑 change）；
- `backend/app/**`（含 `models/mastery_state.py` 的 `ConceptState.fsrs_*`——只登记不改）、`backend/app/services/review_service.py`（只读引符号）；
- 地盘外的裸名字 `save_card_state`（`test_review_service_fsrs.py:611-612` / `docs/fsrs-truth-source-d0-revision.md:68` / `docs/known-gotchas.md:18/:139`——故意保留）；
- `daily_review_pick.py` / `g39_three_view_reconcile.py` / `g610_dual_vault_interaction_canary.py`（T4-A/T4-B 地盘）。

**硬边界**：禁写 live vault；禁连 7691/7687；禁碰 `fsrs_bridge.py` / `decay_beta.py`（零写者）；现网 LanceDB/backups 只读；禁 `git stash`（共享栈，用临时 WIP commit 替代）；批中禁装/升任何包（CLI 用 `npx --no-install`，缺则停下登记，不装）；不改台账；**真实仓内不跑 `openspec archive`**（archive 证明只在仓外 `mktemp` scratch 上跑，避免 `changes/archive/` 越地盘）；不 push。

## 四 Codex / 验收单

**Codex 命令（协议 §2 固定）**：
```zsh
codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" \
  "$(cat <车道树>/_bmad-output/审查/prompts/codex-prompt-CARD-U9B-OPENSPEC-r1.md)" \
  > <车道树>/_bmad-output/审查/codex-review-CARD-U9B-OPENSPEC-r1.md \
  2> <车道树>/_bmad-output/审查/codex-review-CARD-U9B-OPENSPEC-r1.stderr </dev/null
```

**prompt 五分节要点**：① 背景——concept-identity 唯一 Requirement 悬空（描述未实现双桶），退役 change 整条 REMOVE 会让 archive 撞 `Spec must have at least one requirement`，本卡改用「补替代 Requirement」让 spec 非空且真实；② 改动面——手改主 spec（替换 Requirement）+ A6 描述块 + test_g3_7 docstring 裸名字；③ 要审什么——替代 Requirement 是否只陈述 review_service.py 可验证的已实现不变式（不发明契约）、4 井号 Scenario 是否齐、裸名字是否三文件归零且未误删档案/地盘外故意保留项、地盘是否 ⊆ 3 文件、archive 证明是否在仓外 scratch（未污染真实树 `changes/archive/`）；④ 最小读取面——`openspec/specs/concept-identity/spec.md`、`docs/project-status/fr-exploration/A6-phase0-reference-card.md`、`backend/tests/regression/test_g3_7_truth_source.py`、`backend/app/services/review_service.py:920-965` / :124 / :127 / :850、`evidence-u9b-openspec/*.txt`；⑤ 禁用措辞——prompt 不得出现协议 §2 点名的那四个被 cyber 拦截的请求词，改说「负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径」；prompt/手册里那个旧 Codex 模型名的 `grep -c` 必 0（本批统一 gpt-6-astra）。

**存档首部（协议 §2.1，每份 `codex-review-CARD-U9B-OPENSPEC-rN.md` 首部 blockquote + 一行 `---` + 正文）**：含 `批次/车道/卡 round-N`、`模型 gpt-6-astra · reasoning_effort ultra · codex <codex --version 实测值>`、`命令`、`审查绑定 <审SHA 或 A..B>`（HEAD 不同须写明）、`会话头自证`（协议 §2.1 第十四批口径：抄 `.stderr` 中含 **codex 版本行 + `model:` 行 + `reasoning effort` 行**的三行，**行号不限、各括注实际行号**；⛔ `model:` 的行号**不固定**——同为 codex 0.153.3，主干存档实测 `codex-review-CARD-W4-7-r3.md` 自证为 `:5`、`-r4.md` 自证为 `:7`（`grep -A2 '会话头自证' _bmad-output/审查/codex-review-CARD-W4-7-r{3,4}.md`），故**不得**照抄任何固定行号、也不得字面抄前三行（两例的前三行都不含 `model:`），必须每轮从**本轮自己的** `.stderr` 里逐行找出三要素再括注其实际行号；`.stderr` 本身不入库）。缺 `模型`/`reasoning_effort`/`codex` 任一字段该轮不计轮次配额。

**D-15（固定串）**：`Codex gpt-6-astra ultra 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0`——有代码改动（test_g3_7 `.py`）⇒ 多轮，上限 5 轮；最后一轮绑最终 HEAD（`git diff --stat --no-color <审SHA> HEAD -- . ':(exclude)_bmad-output'` 为空）且 BLOCKER=0、HIGH=0（MEDIUM/LOW 登记）；审后再改代码必再送一轮（只改 `_bmad-output` 不算）；第 5 轮仍有 HIGH → 停下交主 session 人审。

**验收单**：`_bmad-output/验收单/UAT-CARD-U9B-OPENSPEC-<日期>.md`，DoD-3 双段（4-A Claude 已代验 / 4-B 你来验，段 4-B 禁技术词）；「本卡未证明什么」「台账待登记条目」各 ≥4（见 §一）。

**收尾**：commit header ≤100 含批次标记 `[BATCH-2026-09-11-第十四批 / CARD-U9B-OPENSPEC]` 且含卡号；body 行 ≤100；`*.stderr*` 不入库（`.gitignore` 已覆盖）；独立 commit（后续串 T4-D CARD-U9C-EVAL）；不 push；跑完说「**复核第十四批 T4**」。
