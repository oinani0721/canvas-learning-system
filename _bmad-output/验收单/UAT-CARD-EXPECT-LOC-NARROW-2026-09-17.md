# UAT — CARD-EXPECT-LOC-NARROW（给 g32cb / g32ccr1 / g33 三套变异 harness 补 `expect_loc`）

> 批次 `[BATCH-2026-09-11-第十四批 / CARD-EXPECT-LOC-NARROW]` · 车道 `card-t8-tools`（分支 `card/t8-tools`）
> 依据：用户裁定 **D-28**（三套 `expect_loc` 移交本卡）、**R-B14-9**（零写者规则 / g33 排 M5 / g32cb 补 flag 允许 / `--json` 另立第十五批）、**R-B14-2**（基线 `grep -vc '^#'` = 64）、**R-B14-3**（`--ignore` 相对路径）、**R-B14-11**（`--no-color` 是 git 的 flag / 含 `exit` 的判据块包子 shell）
> 卡文：`_bmad-output/implementation-artifacts/goal-cards/第十四批-goals/T8-C.md`（feature 主干树那份）

---

## 〇 第 0 分钟自证

| 项 | 实测 |
|---|---|
| `pwd` | `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools` ✅ |
| 分支 | `card/t8-tools` ✅ |
| `PREREQ=$(git rev-parse HEAD)` | `796f6490ba951a1826e2c28e97037ab47d71f4b8` ✅ |
| `git log -1 --format=%s` | `docs(mutkill): 收口 —— 验收单/存档/证据补齐 [BATCH-2026-09-11-第十四批 / CARD-DEBT-mutkill-R3]` ⇒ 含 `CARD-DEBT-mutkill-R3` ✅（T8-B 已落，前提成立） |
| `git status --porcelain` | 空 ✅ |
| `test -e backend/.venv/bin/pytest` / `backend/.env` | 均在 ✅ |
| `$BASE` = feature 主干树 `evidence-b14/unit-red-baseline-08100483.txt` | 存在；`grep -vc '^#' $BASE` = **64** ✅（R-B14-2） |

## 〇.1 卡文行号锚漂移登记（卡文 :X → 实测 :Y）

串行前序 **T8-B** 改过 `mutation_kill_identity.py` 与 `g33_mutation_gates.py`，卡文里那两份的行号（B14_BASE `08100483` 实测值）已漂。本卡全部按 `grep -nF` / AST **重锚**，如实登记：

| 符号 / 锚 | 卡文（B14_BASE） | 本卡实测（PREREQ `796f6490`） |
|---|---|---|
| `mutation_kill_identity.py::kill_identity` | :641 | **:996** |
| `…::_loc_identity` | :610 | **:869** |
| `…::check_expect_loc_unique` | :1021 | **:1471** |
| `…::loc_token_for` | :585 | **:810** |
| `…::stmt_fingerprints` | :508 | **:733** |
| `…::failed_locations` | :410 | **:635** |
| `…::parse_failed_nodeids` | :381 | **:606** |
| `…::expect_loc is None and expect_msg is None` | （卡文未给行号） | 注释 :1021 / 判据 **:1170** |
| `…::if require_gate_file or expect_loc is not None:` | （卡文未给行号） | **:1058** |
| `g33::MUTATIONS` | :77 | **:82** |
| `g33::kill_identity(` 调用行 | :503 | **:729**（开括号行；另 2 条注释行 :719 / :727，均无 `expect_loc=`） |
| `g33::argparse add_argument` | :393-395 | **:615 / :616 / :617** |
| `g33::_TARGET_FILES` | :248 | **:253** |
| `g33::SKILL/BRIDGE/EVLOG/TESTS` | :61-64 | **:62 / :63 / :64 / :65**（各下移 1 行） |
| `g33` 汇总打印（含 D-28 过时文案） | :649-651 | **:897-899**（文案行 :899） |
| `g33` rc 语义注释（`rc=4 部分跑（--only / --probe / --list …）`） | :724 | **:990**（⚠️ 卡文 §一(c) 明令本卡**不顺手改它**；它写的 `--list` 在 g33 仍不存在 —— 登记进台账，见 §六 ⑬） |

`g32cb` / `g32ccr1` **无**串行前序写者，行号未漂（`g32cb::MUTATIONS` :161 ✅、`EXPECT_MSG` :278 ✅、`kill_identity(` :541 ✅；`g32ccr1::MUTATIONS` :70 ✅、`EXPECT_MSG` :195 ✅、`kill_identity(` :431 ✅；`LEDGER_TEST`/`GATE_FILE` :84/:86 与 :63/:65 ✅）。

## 〇.2 开工基线自证（口径更正①/②复核）

- `grep -cF 'expect_loc' <三套>` → 各 **4**，`grep -nF` 逐行核：**全是注释行**，无任何 `kill_identity(..., expect_loc=...)` 调用 ⇒ 卡文「9/11/18 是**变异条数**、不是 `expect_loc` 出现次数」口径成立，本卡是**新增**绑定。
- AST 实测 `MUTATIONS` = **9 / 11 / 18** ✅（与 D-28 一致）。
- `grep -cE -e loc_token_for -e stmt_fingerprints -e check_expect_loc_unique <三套>` 开工 → **0 / 0 / 0**；**验伪锚**同模式对 `g32b_mutation_gates.py` → **6**（证明模式能命中，不是恒 0）。收工三套各 ≥1（见 §四.1）。
- 口径更正②复核：`kill_identity` 只在 `expect_loc is None and expect_msg is None` 时返 `KILLED-UNBOUND`（:1170）；三套 `expect_msg` 覆盖率 **100%**（g32cb 9/9、g32ccr1 11/11、g33 18 条内联全非 None）、`EXPECT_MSG_EXEMPT` 各 **0** ⇒ **本三套取不到 `KILLED-UNBOUND` 档**；`require_gate_file` 三套一律保持 `True`（见 §三.3）。

---

## 一 对照输入：先红 / 反例翻转（承重，三套各一对）

驱动 `_bmad-output/审查/evidence-expect-loc-narrow/negctl_expect_loc_driver.py`（**只读**：不跑 pytest、不改文件、不连库）合成一份 `out`，形状与真 pytest `-q -p no:cacheprovider --tb=line -rfE --show-capture=no`（`judge_flags()` 实测值）输出逐段同构：

- `=== FAILURES ===` 区放一条 `--tb=line` 位置行，**落在门文件里的「前提断言」**上；
- 该行的消息里**原样内嵌**一段模拟被测子进程输出的文本，其中**含目标断言的 `expect_msg` 子串**；
- `=== short test summary info ===` 区放 `FAILED <nodeid> - <同一条消息>`。

⇒ 摘要维（reason 含 `expect_msg`）与弱位置维（有失败落在门文件里）**同时**被满足，而目标断言根本没执行。这就是 Y1-B HIGH-1。

两条断言的 `stmt:` 指纹都由 `stmt_fingerprints(<门文件>)` **实测**取得（⛔ 不推算行号）：
目标断言 = 该门作用域里**源码含 `expect_msg` 字面量**的那条 `assert`（唯一）；前提断言 = 同作用域里行号最小、不含该字面量、且指纹在全门文件恰命中 1 条的那条 `assert`。

| 套 | 变异 | 前提断言（位置行落这里） | 目标断言 | `expect_loc=None` | `expect_loc=<表里那个值>` |
|---|---|---|---|---|---|
| g32cb | `M1` | 行 5214 `assert _run_writer_settled(vault, _payload(...)).returncode == 0` → `stmt:caf9d5c3e98d` | 行 5221 `assert r.returncode != 0, f"⛔ [{_bad}] 非布尔凭据不得被当成「已应用」"` → `stmt:03581c229ae0` | **KILLED**（误判） | **SURVIVED**「位置不符」 ✅ |
| g32ccr1 | `E1` | 行 6540 `assert _run_writer_settled(vault, pA).returncode == 0, "A 首写"` → `stmt:a8608eba5723` | 行 6581 `assert nd_after.count(_snap_A) == 1, (…)` → `stmt:53162da695b2` | **KILLED**（误判） | **SURVIVED**「位置不符」 ✅ |
| g33 | `M2-cas-guard` | 行 640 `assert _race_fired(vault), f"竞态注入没有触发, 本门的前提不成立\nSTDOUT{out}\nSTDERR{err}"` → `stmt:10fee07a4d79` | 行 641 `assert rc != 0, f"外部写者插队后仍照常发布 = CAS 门没起作用\nSTDOUT{out}"` → `stmt:cba02d3de9fe` | **KILLED**（误判） | **SURVIVED**「位置不符」 ✅ |

> g33 那条前提断言**本身**就把子进程的 `STDOUT` / `STDERR` 原样拼进了消息 —— 不是构造出来的形态，是门文件里现成的写法。

存档（成对）：`negctl-before-{g32cb,g32ccr1,g33}-<ts>.txt` / `negctl-after-{g32cb,g32ccr1,g33}-<ts>.txt`，末行 `rc=0`（驱动自己的判据：before 必须 `KILLED`、after 必须非 `KILLED`，不成立则 rc=1）。

⚠️ `after` 模式的 `expect_loc` **不是驱动现算的**，而是 `import` 该套 harness 后读它的 `EXPECT_LOC[<mid>]` —— 证的是「本卡真正写进表里的那个值」能翻转。

### 一.1 一个独立的交叉核（如实说明它证到哪一步）

驱动挑目标断言用的是**静态**依据（门源码里含 `expect_msg` 字面量的那条 `assert`），`EXPECT_LOC` 回填用的是 `--probe` 的**真跑观察**。两条路径互不相干，而三套抽到的这三条**结果逐字相同**：

| 套 | 驱动静态挑出的目标断言 | probe 真跑观察回填的值 |
|---|---|---|
| g32cb `M1` | `stmt:03581c229ae0` | `stmt:03581c229ae0` |
| g32ccr1 `E1` | `stmt:53162da695b2` | `stmt:53162da695b2` |
| g33 `M2-cas-guard` | `stmt:cba02d3de9fe` | `stmt:cba02d3de9fe` |

⚠️ **它证到哪一步**：只证明**这 3 条**抽样上「真跑实际红的那条语句」= 「该条变异声称要打红的那条断言」。它**不**把 `EXPECT_LOC` 表头那句「判据与被测量同源」撤销 —— 其余 34 条没有这样的独立对照。

## 二 指纹探针（实测取值）+ 每次真跑前后 sha

`EXPECT_LOC` 的每个 `stmt:` 值都来自本卡新增的 `--probe` 观察入口（跑变异、**不判定**、一律 `OBSERVED`、rc 恒 4），⛔ 没有一条是推算行号或手抄的。

| 套 | probe 命令 | 存档 | 观察到的条数 | 落在门文件里 | 指纹作用域 = 该条点名的门 |
|---|---|---|---|---|---|
| g32cb | `scripts/g32cb_mutation_gates.py --probe` | `probe-g32cb-<ts>.txt` rc=4 | 9 | 9/9 | 9/9 ✅ |
| g32ccr1 | `scripts/g32ccr1_negative_controls.py --probe` | `probe-g32ccr1-<ts>.txt` rc=4 | 11 | 11/11 | 11/11 ✅ |
| g33 | `scripts/g33_mutation_gates.py --probe --skip M5-cas-revision-only` | `probe-g33-skipM5-clean-<ts>.txt` rc=4 | 17 | 17/17 | 17/17 ✅ |

⇒ 三套 `EXPECT_LOC_HELPER` 均为空（没有一条落在被多道门共用的 helper 断言上）。

### 二.1 g33 的第一次 probe 崩在收尾打印（如实登记，不遮）

第一次 g33 probe（`probe-g33-skipM5-<ts>.txt`）**17 条观察值全部打印完毕、还原自检报「是」、跑前跑后 sha 逐字同**之后，在收尾那段打印上崩于 `UnboundLocalError: _selected` —— 我新加的 probe 早退块引用了当时还定义在它**后面**的 `_selected`。
同一处被 `ruff check` 以 **F821 Undefined name `_selected`** 独立抓到（那次 ruff 与这次 probe 是并行的，进程里跑的是修复前的字节）。
修法：把 `_selected` 的定义**上提**到 `--skip` 校验之后（⚠️ 没有把循环改成遍历 `_selected` —— 循环里的过滤与 `_selected` 分别写一遍，「六档之和 = len(_selected)」才能顺带抓到「过滤与分母漂开」）。
修完**重跑**取干净存档，并把两次观察值逐条对照：

```
grep -oE '"M[0-9a-b-]+[a-z0-9-]*": "stmt:[0-9a-f]{12}"' <首跑> | sort > A
grep -oE '"M[0-9a-b-]+[a-z0-9-]*": "stmt:[0-9a-f]{12}"' <重跑> | sort > B
diff A B     →  无差异（各 17 行）
```

⇒ 顺带得到一条**跨跑稳定性**证据：两次独立真跑观察到的 17 条失败语句**逐条相同**。

### 二.2 每次真跑的 sha 前后（承重：零写者 `fsrs_bridge.py`）

每份真跑存档的**首部**是跑前 `shasum -a 256`、**尾部**是跑后 `shasum -a 256`（同一组文件、同一顺序），末行 `rc=`。
g33 的那组覆盖 AST 实测的全部 4 个被变异文件；`canvas-vault/.claude/scripts/fsrs_bridge.py` 是本批点名的**零写者**，它跑前跑后逐字相同是**承重判据**（裁定 R-B14-9 (2)(3)；`restore_all()` 对 `_TARGET_FILES` 全量 `write_bytes`，所以任何一次 g33 真跑都会**等字节重写**它一次，裁定明确「等字节 restore 不算碰」）。

## 三 本卡代码改动（地盘 = 恰三个文件）

| 文件 | 新增 |
|---|---|
| `backend/scripts/g32cb_mutation_gates.py` | 导入 `check_expect_loc_unique` / `loc_token_for` / `stmt_fingerprints`；`EXPECT_LOC`(9) + `EXPECT_LOC_HELPER`(0) + `EXPECT_LOC_EXEMPT`(0) 三张表；`_check_expect_loc()` + `_loc_coverage_line()` + `_observed_loc()`；`--list` 并入位置自检与覆盖行；`--probe` 观察入口（不判定、rc 恒 4）；跑前位置自检（probe 跳过）；`kill_identity(..., expect_loc=EXPECT_LOC.get(mid))`；汇总文案改实 |
| `backend/scripts/g32ccr1_negative_controls.py` | 同上（`EXPECT_LOC` 11 条 / 两张登记表为空） |
| `backend/scripts/g33_mutation_gates.py` | 同上，另加：`--selfcheck-loc`（本套无 `--list`，与 `--selfcheck-syntax` **同层早退**、纯只读）、`--skip <完整 mid>`（**精确**匹配，排除零写者条目；四处同步：循环过滤 / `_selected` 分母 / `--json` 的 `partial` / 「rc 恒 4」分支；未知取值当场 rc=4 拒跑）；`_selected` 定义上提到 `--skip` 校验之后 |

**未碰**（只读）：`mutation_kill_identity.py`（T8-B 地盘）、`g32b_mutation_gates.py`（范式）、两个门文件、`lefthook.yml`、`ruff.toml` / `pyrightconfig.json` / `package*.json`、`backend/tests/conftest.py`、`backend/app/**`。

### 三.3 `require_gate_file` 一律 `True`（⛔ 没照抄 g32b）

三套 `kill_identity(...)` 调用点均写死 `require_gate_file=True`，**不随豁免表放松**。
依据（口径更正②）：`kill_identity()` 里 `if require_gate_file or expect_loc is not None:` 是**整块**弱位置判据；
对「有 `expect_msg`、无 `expect_loc`」的条目把它置 `False`，等于把该条从「弱位置 AND 消息」降成「只消息」= **放宽判据**。
g32b 之所以敢写 `require_gate_file=tag not in EXPECT_LOC_EXEMPT`，是因为它那 3 条位置豁免**同时**在 `EXPECT_MSG_EXEMPT` 里（两维皆空 ⇒ `KILLED-UNBOUND`）；本三套 `expect_msg` 覆盖率 100%、`EXPECT_MSG_EXEMPT` 各 0，前提不成立。

## 四-A 🤖 Claude 已代验（证据全在 `_bmad-output/审查/evidence-expect-loc-narrow/`）

| # | 判据 | 结果 | 存档 |
|---|---|---|---|
| 1 | AST 核 `MUTATIONS` = 9 / 11 / 18 | ✅ 9 / 11 / 18 | §〇.2 |
| 1b | 开工三套 `kill_identity(` 调用**无** `expect_loc=`；`grep -cF expect_loc` 各 4 全是注释 | ✅ | §〇.2 |
| 2 | **对照输入成对**：`expect_loc=None` ⇒ `KILLED`；`expect_loc=<表内值>` ⇒ 非 `KILLED` | ✅ 三套皆 `KILLED` → `SURVIVED`「位置不符」 | `negctl-before-{g32cb,g32ccr1,g33}-*.txt` / `negctl-after-*.txt`（各末行 `rc=0`） |
| 3 | **覆盖自检前后对照** | ✅ 见下表 | `list-before-*.txt` / `list-after-*.txt` |
| 3a | g32cb `--list` 改前 rc=0 **无** EXPECT_LOC 行 → 改后 rc=0 **有**「EXPECT_MSG 9 / EXPECT_LOC 9 / 消息豁免 0 / 位置豁免 0 / helper 0（共 9）」 | ✅ | `list-before-g32cb-*` / `list-after-g32cb-*` |
| 3b | g32ccr1 `--list` 同上 → 改后「EXPECT_MSG 11 / EXPECT_LOC 11 / 0 / 0 / 0（共 11）」 | ✅ | `list-before-g32ccr1-*` / `list-after-g32ccr1-*` |
| 3c | **g33 无 `--list`** ⇒ 走本卡新增 `--selfcheck-loc`：改前 argparse `unrecognized arguments: --selfcheck-loc` **rc=2**（flag 不存在，此即改前自证）→ 改后 rc=0「内联 expect_msg 18 / EXPECT_LOC 17 / 位置豁免 1 / helper 0（共 18）」 | ✅ | `list-before-g33-*`（rc=2）/ `list-after-g33-*`（rc=0） |
| 4 | **每次真跑前后 `shasum -a 256` 逐字同**（含零写者 `fsrs_bridge.py`，承重） | ✅ 7 次真跑全部 `sha前后同=True` | 每份存档首尾（`probe-*` / `only-*` / `skipctl-*`） |
| 4b | 收工 `git status --porcelain` 对 `fsrs_bridge.py` / `decay_beta.py` / `backend/app` | ✅ 三者皆空 | §四-A 下方命令回执 |
| 5 | **地盘** = 恰三个 harness 文件 | ✅ `g32cb_mutation_gates.py` / `g32ccr1_negative_controls.py` / `g33_mutation_gates.py` | §四-A 下方 |
| 6 | **目录级** `tests/unit`（`cd backend` 在前 + `--ignore tests/unit/test_deploy_vault_sh.py`，R-B14-3） | ✅ 与 `$BASE` nodeid 集合**完全相同**（base 64 / close 64，`>` 行 **0**、`<` 行 **0**） | `unit-close-*.txt`（`35 failed, 5161 passed, 48 skipped, 23 xfailed, 29 errors`，rc=1）/ `unit-diff-*.txt` |
| 7 | **ruff**（`python-lint` 覆盖 `backend/scripts`） | ✅ `ruff check` rc=0 / `ruff format --check` rc=0（3 文件）；验伪锚 rc=1 + F821 | `ruff-*.txt` / `ruff-enabled-rules-*.txt` |
| 8 | 跑后**纯注释**编辑的等价证明 | ✅ 三套 `AST 相同 = True`，验伪锚两侧都翻转 | `ast-equal-after-comment-edit-*.txt`（两份：首版把说明写成 **docstring** 被这把尺子当场判 False，改成 `#` 注释后重证 True —— 两份都留档） |

### 四-A.1 抽样确认击杀不退化（⛔ 三套 `--only` 形态各不相同）

| 套 | 走的形态 | 实测 | 存档 |
|---|---|---|---|
| **g32cb** | **① 跑全量 9 条**（实测该套 `main()` 只认 `--list`，**没有** `--only`；⛔ 传 `--only` 会被静默忽略并跑满 9 条，那样在验收单写「只跑了一条」就是失实）。**没有**按 R-B14-9 允许的 ② 给它补 `--only` | **9/9 KILLED**，每条 why 都是「红在声称的那一条断言上（绑定维度: **位置+消息**）」；`SURVIVED 0` / `HARNESS-ERROR 0` / 六档之和 9 ✓ / **rc=0** | `only-g32cb-full-*.txt` |
| **g32ccr1** | `--only=E1`（该套 `--only` 是**精确 mid 集合** `m[0] in only`，不是前缀） | **1/1 KILLED**（位置+消息）；「选中 1/11 条 —— 部分跑不构成全量结论」**rc 恒 4**（⛔ 不得读成失败） | `only-g32ccr1-E1-*.txt` |
| **g33** | **(乙) 补 `--skip M5-cas-revision-only`**（该套 `--only` 是**前缀**匹配 `mid.startswith(args.only)`，「排除一条」表达不出来；(甲) 逐条 `--only` 要 17 次真跑） | **17/17 KILLED**；`SURVIVED 0` / `HARNESS-ERROR 0` / 「六档之和: 17（应 = 选中的变异条数 17）✓」/「还原逐字节相同: 是」/「选中 17/18 条」**rc 恒 4** | `only-g33-skipM5-*.txt` |

### 四-A.2 `--skip` 的三条反例（(g) 乙 的判据）

| 反例 | 期望 | 实测 | 存档 |
|---|---|---|---|
| `--skip M5-cas-revision-only --skip M1-per-node-lock` | 「选中 **16**/18 条」 | ✅「选中 16/18 条」+ **16/16 KILLED** + 六档之和 16 ✓ + rc=4 | `skipctl-g33-two-*.txt` |
| `--skip NOPE`（未知 mid） | 当场 rc=4 拒跑、**不施加任何变异** | ✅「`--skip` 取值不在变异表里: ['NOPE'] —— 拒跑, 未施加任何变异 (rc=4)」，跑前跑后 sha 逐字同 | `skipctl-g33-unknown-*.txt` |
| `--skip M1`（**短值**：若按前缀会静默选中 M1 + M10~M17 共 9 条） | 当场 rc=4 拒跑 | ✅ 同上拒跑，sha 前后同 ⇒ **打错开关不会静默退化成部分跑** | `skipctl-g33-prefixtrap-*.txt` |

> `--skip` 是**精确**匹配的正面证据不是这条反例，而是上面两次真跑的分母：18 → **17**（排 1 条）、18 → **16**（排 2 条）。前缀语义下 `--skip M5-cas-revision-only` 同样排 1 条，但 `--skip M1-per-node-lock` 也只排 1 条 —— 两次分母各减 1，与「每个 `--skip` 恰好排掉 1 条」一致。

### 四-A.3 位置绑定 / 豁免逐套计数

| 套 | `MUTATIONS` | `EXPECT_LOC` 绑定 | `EXPECT_LOC_EXEMPT` | `EXPECT_LOC_HELPER` | 豁免条目实际落哪一档 |
|---|---|---|---|---|---|
| g32cb | 9 | **9** | 0 | 0 | — |
| g32ccr1 | 11 | **11**（E2/E6、E3/E9、E5/E10 三对各绑**同一条**断言） | 0 | 0 | — |
| g33 | 18 | **17** | **1**（`M5-cas-revision-only`） | 0 | **`KILLED` + 「仅消息维」**（`require_gate_file` 仍 `True`、内联 `expect_msg` 仍在）⛔ **不是** `KILLED-UNBOUND` |
| 合计 | 38 | **37** | **1** | **0** | |

### 四-A.4 命令回执（`--no-color` 是 **git** 的 flag，R-B14-11(a)）

```
# 地盘（工作树对 PREREQ；commit 后同一判据换成 $PREREQ HEAD）
git --no-pager diff --name-only --no-color $PREREQ -- . ':(exclude)_bmad-output'
  → backend/scripts/g32cb_mutation_gates.py
    backend/scripts/g32ccr1_negative_controls.py
    backend/scripts/g33_mutation_gates.py          （恰三个，⊆ 本卡地盘 ✅）

# 零写者 / T7-B 面 收工核
git status --porcelain -- canvas-vault/.claude/scripts/fsrs_bridge.py   → 空 ✅
git status --porcelain -- canvas-vault/.claude/scripts/decay_beta.py    → 空 ✅
git status --porcelain -- backend/app                                   → 空 ✅
```

### 四-A.5 ruff 验伪锚第一版是**假阴性**（已查实根因，不是猜）

第一版把锚点写到 `/tmp/_ruff_anchor.py`、cwd 在仓根跑 `ruff check -- /tmp/...` ⇒ `All checks passed!` **rc=0** —— 锚**恒不红**。`ruff check -v` 给出原因：

```
[ruff::resolve][DEBUG] Using configuration file (via parent) at: <仓根>/ruff.toml
```

而**仓根 `ruff.toml:39` 是 `select = []`**（其注释自述：2000+ 存量违规，lint 规则暂时全关、只留 format 检查）⇒ 解析到它的路径 `linter.rules.enabled = []`，**任何**规则都不触发。

| 口径 | 解析到的配置 | 结果 |
|---|---|---|
| cwd=仓根，路径 `/tmp/x.py` | 仓根 `ruff.toml`（`select=[]`） | rc=0 ⛔ **假阴性** |
| cwd=`/tmp`，路径 `x.py` | 无配置 → ruff 缺省 | rc=1 F821 ✅ |
| cwd=仓根，`--stdin-filename backend/scripts/x.py` | `backend/ruff.toml` | rc=1 F821 ✅ ← **本卡采用** |

`--show-settings` 实测两面的启用规则：`backend/scripts/**` = `select = ["E9","F63","F7","F82"]` ⇒ **14 条**（含 **F821 undefined-name**）；仓根 `scripts/**` = **空集**。

> ⛔ 与 MEMORY `reference_ruff_f401_anchor_never_fires_in_backend` 同族、换了一面：那条说「F401 在 backend 面没启用」，这条说「**锚点路径**若解析到仓根 `select=[]`，连 F821 也不会红」。锚点必须落在**被判据实际覆盖的那一面**上。

**本判据是承重的实证**：作业期内 `ruff check` 的 **F821 Undefined name `_selected`** 真抓到一个缺陷（见 §二.1），不是摆设。

⚠️ **验伪锚的正确时机**：`git --no-pager diff --name-only $PREREQ -- .`（去掉 exclude）在 commit **之前**返回 0 条 `_bmad-output/` —— 因为那些证据文件还是 **untracked**，`git diff` 看不见。所以地盘门的验伪锚必须在 commit **之后**用 `$PREREQ HEAD` 跑（见 §七 下方回执），⛔ 不能拿 commit 前那次「0 命中」当「锚失效」或「锚成立」。

## 四-B 👤 你来验（3 分钟，全程只在这份文档里读，不用打开任何别的东西）

- [ ] 我读 §一 那张表的最后两列 → 我看到**同一份输入**，左边一列写着「抓到了」、右边一列写着「没抓到、位置不符」→ 我感觉这不是文字游戏，是真的分开了两件事。
- [ ] 我读 §一 中间那两列（前提断言 / 目标断言）→ 我看到它们是**同一页里挨着的两行**（比如第 640 行和第 641 行）→ 我感觉「以前分不开」这句话我看懂了：就差一行，旧办法只能说「这一页红了」。
- [ ] 我读 §二 的「跑前 / 跑后」两组指纹 → 我看到每一行前后**一模一样** → 我感觉这套自检在自己身上也没偷懒：它动过的文件都放回原样了。
- [ ] 我读 §一.1 那段「它证到哪一步」→ 我看到它主动说了「只证明这 3 条，其余 34 条没有这样的独立对照」→ 我感觉这份报告不打算糊弄我。

**一句话**：以前系统自检变异时，只要在那一页里随便哪条检查红了就算抓到，哪怕抓错地方；现在它能认准是不是抓在该抓的那一条上——我感觉这个自检终于分得清对错、不会再自己骗自己。

**没做到的，也写在这**：三套里有 **1 条**（g33 的 `M5-cas-revision-only`）本批**没跑**，因为它会去改一个本批明令不许动的文件；它现在仍然只能说「这一页红了」，已经登记、留给下一批。

## 五 本卡未证明什么

1. **未证明**三套门文件里每条目标断言的 `stmt:` 指纹在**所有** pytest 版本 / 插件组合下稳定。指纹取自 `ast.dump` + 作用域名，理论上与 pytest 无关，但本卡只在本树这一套解释器/插件下实测过。
2. **未做**四套全量**裁决**复跑。probe 跑只**观察**失败位置、不裁决；本卡的裁决覆盖是 g32cb 全量 9 条 + g32ccr1 抽样 1 条 + g33 `--skip M5` 的 17 条 —— 不证明「所有已绑条目在任意时刻真跑都仍 KILLED」。
3. **未证明**门外 / 取不到指纹的豁免条目「确实绑不出来」而非「本可绑」：判据只是**实测失败落点**，而落点会随门文件改动而变。
4. **未改** `mutation_kill_identity.py`，因此不证明 T8-B 修的 H1 / H2 在所有输入形态下完备；本卡只在其之上补位置身份这一维。
5. 对照输入是**合成** `out`（形状与真 pytest 输出同构），不是真跑触发的 Y1-B HIGH-1；不证明不存在别的「同时喂饱位置与消息两维」的第三种形态。
6. 不证明 g33 的**内联** `expect_msg`（`MUTATIONS` 第 7 字段）与新 `EXPECT_LOC` 之间除「键对齐」以外没有别的耦合。
7. **未真跑** g33 的 `M5-cas-revision-only`（零写者铁律 / 裁定 R-B14-9 (1)）⇒ 不证明它的失败位置落在门文件里、也不证明它「本可绑」，只证明**本批取不到**它的指纹。
8. **未证明**「`restore_all()` 对 `fsrs_bridge.py` 的**等字节重写**在**变异中途被杀**时仍留不下变异体」。R-B14-9 (2) 的「等字节 restore 不算碰」是**规则裁定**（裁定书自述依据 = sha 门 + squash 门双层兜底，未实测被杀场景）；本卡只按「每次真跑前后 sha 逐字同」这条承重判据执行。
9. g32cb 走的是「跑全量 9 条」而不是补 `--only`，因此**不证明** g32cb 与另两套在 `--only` 的 rc 语义 / 缺值防线上等价（本卡根本没给它加那个入口）。
10. g33 的 `EVLOG`（`backend/app/services/learning_event_log.py`，本批 T7-B 面）真跑期临时写 + 还原，只证明**本车道树**上 sha 前后同、`git status` 干净；**不证明**与 T7-B 车道那份改动在集成期无交集（两树独立，集成期由主 session 核）。
11. `--skip` 只证明本卡用到的三种形态（单条排除 ⇒ 17/18、双条排除 ⇒ 16/18、未知 mid ⇒ rc=4 未施加）；**不证明** `--skip` 与 `--only` 同时给时交集语义的全部形态。
12. g32cb / g32ccr1 的 argv 解析仍是**成员判定**（`"--probe" in sys.argv[1:]`），未知开关**静默忽略** —— 本卡新增的 `--probe` 沿用了这个既有形态，**不证明**打错开关时不会退化成另一种跑法。（该「未知开关 fail-open」是 T8-B 收官登记的**卡外**缺陷，本卡未扩大也未修复它；g33 走 argparse，未知开关 rc=2 拒跑。）
13. **Codex r1 LOW-1 复现的「未被拦下的输入」**：位置判据是「任一 token 命中」，所以只要 `FAILURES` 区里**另有**一条位置行落在目标语句上，`expect_loc` 照样命中、判回 `KILLED` —— 本卡三套实测全部复现（`negctl_extra_loc_uncovered.py` / `uncovered-extra-loc-*.txt`，三套 `rc=0` 即「复现成立」）。⚠️ **未证明**真实 pytest 在跑一条测试时会打出两条位置行；也**未证明**前提断言内嵌的子进程输出里能否恰好拼出 `<门文件>:<目标行>: <Exc>: <msg>` 这种形态被 `_LOC_RE` 当成位置行收下 —— 两者都没实测，如实留空。⛔ 该判据在 `mutation_kill_identity._loc_identity()` 里，是 **T8-B 地盘**，本卡未改；按协议 LOW **登记不阻断**，且⛔ 不得为了「看起来更干净」去动一条已判通过的 LOW（那会亲手打破终审绑定）。
14. **对照输入的 reason 是统一合成的**（Codex r1 LOW-1 后半段，如实收窄）：驱动给三套用的是同一段「子进程 stderr 原样内嵌」文本；而三套**真实**的前提断言形态并不相同 —— g32cb 那条 `assert _run_writer_settled(...).returncode == 0` **没有显式消息**，g32ccr1 是 `"A 首写"`，g33 的 `{out}{err}` 在**换行之后**。⇒ 这些存档证明的是**裁判会翻转**，**不是**三套真实输出路径的完整复现。
15. **g33 固定门文件的隐含前提未做成运行时检查**（Codex r1 LOW-2 确认为「后续加固，不阻断本卡」）：唯一性核逐条从 `nodeid` 推门文件，作用域核却固定读 `BACKEND / TESTS`，查不到指纹就跳过 ⇒ 将来加一条**别的**测试文件里的门时，`--selfcheck-loc` 可能错报通过、要等正式裁决才报锚失效。当前 18/18 nodeid 都在 `TESTS` 里，故今天不可达；已在 `_check_expect_loc()` 上方注释写明并登记移交。

## 六 台账待登记条目

1. **D-28 的三套 `expect_loc` 由本卡落地**：g32cb 绑 9 / 豁免 0、g32ccr1 绑 11 / 豁免 0、g33 绑 17 / 豁免 1（`M5-cas-revision-only`）；合计**新增 37 条**位置绑定 + 1 条显式豁免。修复 commit sha 见 §七。
2. **Y1-B HIGH-1：本卡三份对照输入已被拦下**（⚠️ 措辞按 Codex r1 LOW-1 收窄，原写「在三套闭合」比证据宽）：同一份对照输入在 `expect_loc=None` 下判 `KILLED`、换成表里的 `stmt:` 值后判 `SURVIVED`（位置不符）。⛔ **未被拦下的输入已复现并登记**：保持前提失败 / 单条摘要 / `rc=1` 不变，只在 `FAILURES` 区**额外加一条**落在**目标行**的位置行，三套又都判回 `KILLED` —— 因为共用裁判 `_loc_identity()` 的位置判据是 `expect_loc in tokens`（**任一** token 命中）。归属 `backend/scripts/mutation_kill_identity.py`（T8-B 地盘，本卡未改它），复现脚本 + 存档见 §五.13。
3. **四套全量裁决复跑移交**：本卡只做 g32cb 全量 + g32ccr1 抽样 + g33 17 条；四套一起的全量复跑登记移交。
4. **位置豁免清单**（供后人复核）：g33 `M5-cas-revision-only` —— 理由「本批零写者铁律禁真跑（R-B14-9 (1)）⇒ 指纹无法实测」；它实际落 **`KILLED` + 仅消息维**，**不是** `KILLED-UNBOUND`。
5. **Codex 各轮存档路径 / 绑定 SHA / B-H-M-L 计数**（见 §七）。
6. **g32ccr1 进 `mutant-residue-scan` 名单依赖前序 T8-A**：实测 `lefthook.yml` 的 case 名单已含 `backend/scripts/g32ccr1_negative_controls.py`（串行顺序证据）；g33 不在名单、也不需要（它的标记是 `"MUT" + "ANT"` 拼接，文件里 0 个字面量）。
7. **口径更正①**：「9 / 11 / 18」是 `MUTATIONS` **变异条数**，不是 `expect_loc` 出现次数；三套开工时 `grep -cF expect_loc` 各 4、**全是注释**。设计稿标「源：C §3.4」处实为六档统一表，条数出处是 A §B.2。
8. **口径更正②**：本三套**取不到** `KILLED-UNBOUND`（`expect_msg` 覆盖率 100%、`EXPECT_MSG_EXEMPT` 各 0），且 `require_gate_file` 必须保持 `True`；卡文原写法「豁免 ⇒ KILLED-UNBOUND / `require_gate_file=(mid not in EXPECT_LOC_EXEMPT)`」**已作废**，位置豁免条目实际落「仅消息维 `KILLED`」。
9. **g33 `M5-cas-revision-only` 的 `expect_loc` 移交第十五批**，前置 = 给 g33 `_TARGET_FILES` 加 live 部署链文件排除、或改副本树变异（依据 R-B14-9 (1)，修订 R-B14-6）。其余 17 条本卡已按 R-B14-9 (2) 真跑取指纹，排 `M5` 走的是 **(乙) 补 `--skip`**。
10. **g32cb 实测没有 `--only`**（argv 只认 `--list`）：本卡走 **① 跑全量 9 条**，**没有**补 `--only`（R-B14-9 允许补但非必须），因此本卡对 g32cb 的新增入口只有 `--probe`。
11. **R-B14-9 末句**：给 g32cb / g32ccr1（及 g32b）补 `--json` / `verdict_counts` **另立第十五批卡**，本卡未做。
12. **零写者 / T7-B 面的 sha 存档**：每次 g33 真跑前后 `shasum -a 256` 对 `canvas-vault/.claude/scripts/fsrs_bridge.py` 与 `backend/app/services/learning_event_log.py` 逐字同（存档见 §二）；收工 `git status --porcelain` 对两路径皆空（R-B14-9 (2)(4)）。
13. **g33 的 rc 语义注释（实测 PREREQ :990）仍写着 `--list`**，而 g33 至今没有 `--list` 入口 —— 卡文 §一(c) 明令本卡**不顺手改它**，登记移交。（本卡新增 `--probe` 后，那句里的 `--probe` 已成立；`--list` 仍不成立。）
14. **原判据「三个改动文件 `grep -rn fsrs_bridge` 0 命中」恒假**（g33 的 `BRIDGE` 常量实测 PREREQ :63 有该串），已换成三条可翻转判据（见 §四.4）。
15. **`tests/unit` 目录级必须带 `--ignore tests/unit/test_deploy_vault_sh.py`**（R-B14-3），且 `cd backend` 在前，与 `$BASE` 文件头跑法逐字一致。
16. **⛔ 移交共用裁判面（T8-B 地盘）**：`mutation_kill_identity._loc_identity()` 的位置判据是 `expect_loc in tokens`（**任一** token 命中）⇒ `FAILURES` 区里只要**另有**一条位置行落在目标语句上，`expect_loc` 照样命中。本卡三套已复现（Codex r1 LOW-1；脚本 `negctl_extra_loc_uncovered.py`、存档 `uncovered-extra-loc-*.txt`）。⚠️ 未实测真实 pytest 能否产生该形态、也未实测前提断言内嵌的子进程输出能否被 `_LOC_RE` 当成位置行收下 —— 两者都是下一张卡的面。本卡**未改**共用裁判（LOW 按协议登记不阻断）。
17. **g33 固定门文件的隐含前提**（Codex r1 LOW-2，判为「后续加固，不阻断本卡」）：`_check_expect_loc()` 的作用域核固定读 `BACKEND / TESTS`，唯一性核却逐条从 `nodeid` 推门文件；今天 18/18 nodeid 都在 `TESTS` 里所以一致。加别的门文件时须同改三处（已在该函数上方注释写明）。
18. **Codex r1 对目录级结论的收窄（采纳）**：`tests/unit` 是「失败集合与 64 条基线**相同**」，**不是全绿**（实测 `35 failed / 5161 passed / 29 errors`，rc=1）。验收单 §四-A 第 6 行已按此写，后人引用勿简写成「unit 全绿」。
19. **AST 等价证明的编辑前快照已入库**（Codex r1 指出限定读取面里没有它、无法独立重算）：`evidence-expect-loc-narrow/pre-comment-edit/`（3 份 + `README.md` 写了复算命令与验伪锚）。
20. **卡文行号锚漂移清单**见 §〇.1（`mutation_kill_identity.py` 与 `g33_mutation_gates.py` 两份被 T8-B 改过，卡文的 B14_BASE 行号已全漂）—— 后人引用请勿照抄旧值。

## 七 Codex 独立审查（gpt-6-astra · ultra · 多轮）

prompt：`_bmad-output/审查/prompts/codex-prompt-CARD-EXPECT-LOC-NARROW[-rN].md`（五分节；最小读取面写死 = 本卡 diff + `mutation_kill_identity` 三函数只读 + g32b `EXPECT_LOC` 范式段 + 两门文件断言段 + 对照输入/覆盖自检存档）
存档：`_bmad-output/审查/codex-review-CARD-EXPECT-LOC-NARROW[-rN].md`（首部按协议 §2.1 六行 blockquote；`.stderr` 不入库）

| 轮 | 审查绑定 SHA | 绑最终 HEAD | BLOCKER | HIGH | MEDIUM | LOW | 处置 |
|---|---|---|---|---|---|---|---|
| r1 | `796f6490…` → `0e6d82c0…` | ✅ 是（`git diff --stat <审SHA> HEAD -- . ':(exclude)_bmad-output'` 实测**空**） | **0** | **0** | **0** | **2** | 两条 LOW 均**登记不阻断**（协议 §1）：LOW-1 已**自己复现**（不采信，`uncovered-extra-loc-*.txt` 三套 rc=0）并按其建议把「闭合」收窄为「本卡三份对照输入已被拦下」；LOW-2 已在代码注释 + 台账登记。⛔ **未改代码** —— 改一条已判通过的 LOW 会亲手打破终审绑定，且 LOW-1 的判据在 T8-B 地盘。 |

> **轮次（D-15）**：本卡有代码改动 ⇒ 需「多轮直到**绑最终 HEAD**的那一轮 BLOCKER = HIGH = 0」。r1 即满足（绑定实测为空 + B/H = 0），审后**只改 `_bmad-output`**（收窄文案、登记 LOW、补快照），代码树未动 ⇒ 绑定仍成立，不需要第二轮。
>
> **审后改了哪些 `_bmad-output`**（如实列，便于主 session 复核）：验收单 §五 新增 13/14/15、§六 新增 16~19、§六 ②收窄措辞、§七 本表；新增 `negctl_extra_loc_uncovered.py` + `uncovered-extra-loc-*.txt`；新增 `pre-comment-edit/`（3 份快照 + README）。

### 七.1 终审绑定回执

```
git --no-pager diff --stat --no-color 0e6d82c00fad046a434461fa1a102617bd2d03c7 HEAD -- . ':(exclude)_bmad-output'
  → 空（代码树仍绑定审查 SHA）
git --no-pager diff --name-only --no-color 796f6490… HEAD -- . ':(exclude)_bmad-output'
  → 恰 3 个 harness 文件
验伪锚：去掉 ':(exclude)_bmad-output' ⇒ 多出 37 个 _bmad-output/ 路径（⚠️ 该锚必须在 commit **之后**跑，
        commit 前证据还是 untracked、git diff 看不见，会给出「0 命中」的假象）
```

