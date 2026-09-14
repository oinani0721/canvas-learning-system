# UAT — CARD-DEBT-mutkill-R3（变异裁决共用判据收口）

> 批次 `[BATCH-2026-09-11-第十四批 / CARD-DEBT-mutkill-R3]` · 车道 `card-t8-tools`（分支 `card/t8-tools`）
> `PREV` = `dde52775d3d643803d3764c57ed94e4224b10f9c`（前一卡 T8-A `CARD-TOOL-residue-fail-open` 末 commit）
> `B14_BASE` = `081004834e37b1b0253cf81dc7b44e784646c934`（`git merge-base --is-ancestor B14_BASE HEAD` 为真）
> 证据目录 `_bmad-output/审查/evidence-mutkill-r3/`

---

## 4-A Claude 已代验（技术侧）

### (a) 第 0 分钟自证

| 项 | 命令 | 实测 |
|---|---|---|
| pwd | `pwd` | `…/worktrees/card-t8-tools` ✓ |
| 分支 | `git rev-parse --abbrev-ref HEAD` | `card/t8-tools` ✓ |
| 清洁 | `git status --porcelain \| wc -l` | `0` ✓ |
| 前提卡 | `git log --oneline -1` | `dde52775 docs(mutant-scan): 收尾核验存档 [… / CARD-TOOL-residue-fail-open]` ✓ |
| 祖先 | `git merge-base --is-ancestor 08100483 HEAD` | 真 ✓ |
| venv/env | `test -e backend/.venv/bin/pytest && test -e backend/.env` | 两者均在 ✓ |
| 基线（R-B14-2 唯一口径） | `test -f "$BASE" && grep -vc '^#' "$BASE"` | **64** ✓ |
| 开工目录级 diff | `diff base.nodeids open.nodeids` | **空**（64 = 64）✓ |

**§〇 符号锚实测**（`open-anchors-20260914T222859.txt`，AST + `grep -nF`，⛔ H1 一律符号名）：

| 符号 | 卡文 | 实测 |
|---|---|---|
| `_split_unique` | 188-211 | **188-211** ✓ |
| `_boundary_ok` | 214-225 | **214-225** ✓ |
| `_same_file` | 566-582 | **566-582** ✓ |
| `_loc_identity` | 610-638 | **610-638** ✓ |
| `kill_identity` | 641-742 | **641-742** ✓ |
| `check_expect_loc_unique` | 1021-1073 | **1021-1073** ✓ |
| `if not cands:` | 209（恰 1 行） | **209**，恰 1 ✓ |
| H2 落点 | 697 | **697** ✓ |
| M① 锚 `if expect_loc[5:] not in fps:` | 620 | **620** ✓ |
| g33 `restore_or_keep_exit_code` | 436-454 | **436-454** ✓ |
| 分母（AST `len(MUTATIONS)`） | 6 / 9 / 11 / 18 | **g32b 6 / g32cb 9 / g32ccr1 11 / g33 18** ✓ |
| `decay_beta` 五文件具名 | 皆 0 | 五行皆 `:0` ✓ |
| 既有单测 | 零文件 import | `grep -rlF` 空、rc=1 ✓ |

**卡文 → 实测的一处口径更正（登台账）**：卡文 §二.1 写 `grep -nF fsrs_bridge backend/scripts/g32b_mutation_gates.py` → `65:`；**实测返回 3 行**（`65:` 常量 + `2609:` / `2674:` 两行注释）。`:65` 是 `BRIDGE` 常量这一事实成立，但「该命令只回一行」不成立 —— 后人勿把行数当判据。

### (b) 先红（改代码前跑）

`r3-red-20260914T223212.txt` — **12 failed, 7 passed, rc=1**：

| 用例 | 改前实得 | 应得 |
|---|---|---|
| `test_h1_ambiguous_no_reason_reading_makes_split_non_unique` | `_split_unique` 返 `True` | `False` |
| `test_h1_ambiguous_line_escalates_to_harness_error` | **KILLED** | HARNESS-ERROR |
| `test_h1_reading_space_is_documented` | docstring 缺读法空间登记 | — |
| `test_h2_weak_position_must_not_borrow_other_gate_failure` | **KILLED**（借位合成） | HARNESS-ERROR |
| `test_h2_boundary_with_d28_is_documented` | docstring 缺 D-28 分界 | — |
| `test_m1_anchor_drift_not_masked_by_rc0_survived` | **SURVIVED** | HARNESS-ERROR |
| `test_m1_anchor_drift_not_masked_by_out_of_gate_survived` | **SURVIVED** | HARNESS-ERROR |
| `test_m1_stmt_fingerprint_hit_count_must_be_one` | **KILLED** | HARNESS-ERROR |
| `test_m2_*`（4 条） | `restore_or_keep_exit_code` 无模块级符号 | 模块级可注入 |

⛔ **正控 7 条改前全绿**（四类 `_split_unique` 正常读法 + H2 单门 KILLED + M① rc=0 锚完好 SURVIVED + M① 锚命中 1 条 KILLED）—— 夹具方向没写反。

**改后全绿**：`r3-green-20260914T223540.txt` — **23 passed, rc=0**（先红那轮之后又补了 4 条用例，见 (e)/(c) 两段的说明）。

### (c) H1 —— 无 reason 读法进候选集

`_split_unique` 现在把三类读法进**同一个** `cands`；读法空间（完整 reason / 参数化 / 无 reason / 括号闭合的二义形态）已穷举进 docstring，并写明「本轮修的是『边界不可判定』这个性质，不是某一条输入」。

⛔ **一条自我更正（如实登记）**：初稿 docstring 写「候选判据只增不减 ⇒ 返回值只会 True→False」，
2026-09-14 实测**推翻**——「无 ` - ` 切点」那一族的判据由「整行方括号成对」换成「整行是 nodeid 形」，
两者**互不包含**，两个方向都会翻：

- `a::b[c - d]` True→**False**（收紧，想要的）；
- `a::b[[c]` False→**True**（放宽；但 `_boundary_ok` 并联那道仍拒它 ⇒ 端到端判据不放宽）。

docstring 已改成如实写法，并补 `test_h1_no_reason_branch_flips_in_both_directions` 把两个方向都钉住。

**保守性的代价也如实写**：参数化 + reason 以 `]` 收尾（`FAILED a::b[c] - AssertionError: [1, 2]`）现判不唯一 ⇒ HARNESS-ERROR。那**确实**是两种合法读法，只看摘要行分不开；要分开只能靠 `expect_loc`（D-28 延期，T8-C 面）。对照用例 `…[1, 2] boom`（reason 不以 `]` 收尾）仍判唯一 —— **不是**把整族参数化门都打成 HARNESS-ERROR。

### (d) H2 —— 弱位置禁跨门借位

`kill_identity` 弱位置分支在 `any(_same_file(...))` **之前**加「所有失败 nodeid 都属于目标门」核；任一失败不属目标门 ⇒ `HARNESS-ERROR`（位置行不带 nodeid，归属不可证）。docstring 写清**只封弱位置判据自己的承诺**，不触碰 D-28 延期的具体断言绑定（未改任何 `expect_loc` 语义、未给任何一套加 `expect_loc`）。

### (e) M① —— 锚漂移优先 + 命中数复核到 1

新增 `anchor_surface_broken()`，排在 `rc==0 ⇒ SURVIVED` 与「红在门文件之外 ⇒ SURVIVED」两条早退**之前**；`_loc_identity` 的 `stmt:` 指纹除「在不在」外**复核命中数恰为 1**（与 `check_expect_loc_unique` 同口径）。⛔ **rc 契约未改**：锚完好时 `rc==0` 仍是 SURVIVED（正控 `test_pc_m1_rc0_with_valid_anchor_still_survived` 钉住）。

⛔ **负控暴露的判据缺口（已修，如实登记）**：首轮负控 `m1b`（拆掉 `_loc_identity` 的命中数核）
**没有让任何用例变红**（19 全绿）—— 因为端到端那条被**两层**同时保护，拆任一层单独都不红，
于是「这一层承重」证不了（「补了控制组 ≠ 控制组成立」）。处置：补两条**直接打在各自层本体上**的用例
（`test_m1_loc_identity_itself_rejects_multi_hit_fingerprint` / `test_m1_anchor_surface_broken_itself_reports_both_shapes`），
并新增负控层 `m1c`。重跑后三层各自显形（见 (h) 表）。

### (f) M② —— g33 末次还原失败不吞、SHA 仍跑

`restore_or_keep_exit_code` 提为**模块级**并接受注入的 `restore_all` / `exiting` 回调（(h)④ 固定走「甲」，R-B14-9 补裁已接受 diff 扩大）。行为：

- 还原成功 ⇒ 控制流一动不动，**首次信号 130 照旧保号**（`test_m2_first_signal_130_is_still_kept`）；
- 进来前**没在**退出展开 ⇒ 异常原样抛出（round-4 HIGH 约定不变，`test_m2_not_exiting_means_new_exception_still_raises`）；
- **非末次**失败 ⇒ 仍吞异常保号，但**返回 `False`**，`main()` 记进 `restore_failures`，汇总段 `ok_restore` 把它算进去；
- **末次**失败 ⇒ 先跑 `_verify_restore()`（还原逐字节自检）并打印，再把退出码**升到 3**。

⛔ SHA 自检**必须在该函数内部**跑：若原先那个 `SystemExit(130)` 继续展开，`main()` 汇总段一行都到不了 —— 这正是收口前「仍报 130 且 SHA 不执行」的形态。汇总段的 `drift` 改调同一个 `_verify_restore()` 闭包（**唯一**一份判据写法，两份手抄必然漂移）。

**同型 census（本卡只读、⛔ 不改那三套）** —— `census-restore-swallow-20260914T224423.txt`：

| 套 | 同型函数 | 吞没形态 | 结论 |
|---|---|---|---|
| `g32b_mutation_gates.py` | `_restore_active_or_keep_exit_code` `:2510-2531` | `_was_exiting = _GUARD.exiting()` `:2522` → `except BaseException: if not _was_exiting: …` `:2525-2526` → `traceback.print_exc()` 后吞 `:2530` | **存在** |
| `g32cb_mutation_gates.py` | 同名 `:337-358` | 同型（`:349` / `:352-353` / `:357`） | **存在** |
| `g32ccr1_negative_controls.py` | 同名 `:245-266` | 同型（`:257` / `:260-261` / `:265`） | **存在** |

⇒ **三套全部存在同型缺陷**（且它们的函数是**模块级** `_restore_active_or_keep_exit_code`，与 g33 的嵌套 def 不同名 —— 所以 `grep -cF 'restore_or_keep_exit_code'` 在三套里是 **0**，⛔ 拿那个名字当判据会得出「不存在」的假阴性）。验伪锚：同一组 grep 在 g33 上命中 3 次 / `:392` 定义行。
本卡按硬边界**不改**那三套 —— 四套统一移交台账（见「台账待登记条目 ③」）。

### (g) M③ —— reconcile 六档硬比

新增 `backend/scripts/mutation_verdict_reconcile.py`。⛔ **按各套实际输出形态取六档**：

- **g33** = 读 `--json` 存档的 `verdict_counts` + `total`（实测**只有 g33** 有这两个字段）；
- **g32b / g32cb / g32ccr1** = 三套实测**无** `--json`、**无** `verdict_counts`，只能解析其 stdout 汇总段，
  且**三套形态互异**，正则按套写（g32cb/g32ccr1 两空格缩进、计数在档名之前；g32b 不缩进、计数在冒号后，
  且多印一行「KILLED 合计」⛔ 不是六档之一）。

**独立分母**：由 reconcile **自己用 AST 从该套源码现算** `len(MUTATIONS)`，⛔ 不采信存档自称的 `total`。
逐档硬比四个数：逐档相加 / 该套印出来的六档之和 / 该套自称分母 / AST 现算条数。

⛔⛔ **分母口径更正（Codex round-4 MEDIUM；连带更正卡文 §〇）**：`g32b_mutation_gates.py` 是
`MUTATIONS = [6 条]` 之后跟着 **36 段** `MUTATIONS += [...]`（共 132 条）—— **真实分母是 138**，
与它自己 `--list` 印的「共 138 条变异 / 171 个锚点」一致。⛔ **卡文 §〇 事实格写「g32b 6」是错的**
（只读了首个赋值），本卡初版 `ast_mutation_count` 照抄了这个错值 ⇒ g32b 的「独立分母」恒为 6 ⇒
**一份只跑 6 条的部分表能冒充全量通过对账**，这道本该是唯一跨源独立判据的门对 g32b 从来就是错的。
现在：模块级 `=` 与 `+= [字面量]` 累加；`MUTATIONS.extend(...)` / `+= 变量` / 非字面量一律
**fail-closed 报错**。实测四套分母 = **g32b 138 / g32cb 9 / g32ccr1 11 / g33 18**。

⛔ **不自证**：reconcile **不重新裁决**任何变异、不统计自己重解析的结果去和自己比；
也**不 `import`** 任何 harness 的 `main()`（分母走 `ast.parse`，只读文本）。
⛔ 六档档名在 reconcile 里**故意手写一份字面量**而不是 `from mutation_kill_identity import VERDICTS`
—— 对账方的档名是它的**独立预期**，跟被对账方共用同一个常量的话「档名漂了」就再也对不出来。

**真跑对账**（`reconcile-real-20260914T230500.txt`，输入 = 上面两套的真实 tee）：

```
── g32cb   逐档相加=9  该套印的六档之和=9  该套自称分母=9  AST 现算条数=9  ✓
── g32ccr1 逐档相加=11 该套印的六档之和=11 该套自称分母=11 AST 现算条数=11 ✓
rc=0
```

### (h) 负控（19 层，每层只拆一层；跑前跑后 `shasum -a 256` 5 行逐字同）

⛔ **以 `r3-negctl-final-<层>-20260915T002701.txt` 十九份为准** —— 绑**最终 HEAD `34473ebd`**。
早于该时间戳的 `r3-negctl-*` 是五轮迭代途中的跑，绑的是后来又被改过的 sha，**不作验收依据**
（Codex round-5 MEDIUM-3 正是指出旧存档只有 17 层且绑旧哈希；本轮已按此补齐重跑）。

| 层 | 拆掉哪一层 | 指定判据 |
|---|---|---|
| `h1` | 无 reason 读法进候选集 | 4 条 H1 用例红 |
| `h2` | 弱位置「所有失败属目标门」核 | `…must_not_borrow_other_gate_failure` |
| `m1a` | 锚漂移优先于两条 SURVIVED 早退 | 2 条锚漂移用例 |
| `m1b` | `_loc_identity` 命中数核 | `…loc_identity_itself_rejects_multi_hit_fingerprint` |
| `m1c` | `anchor_surface_broken` 命中数核 | `…anchor_surface_broken_itself_reports_both_shapes` |
| `m1d` | 参数段起点退回「最后一个 `::` 之后」 | `…double_colon_inside_param_id_still_ambiguous` |
| `m1e` | 参数段起点退回「整串第一个 `[`」 | `…bracket_in_path…` + `…must_follow_a_double_colon` |
| `m1f` | 参数段起点前缀「必须含 `::`」 | `…param_bracket_must_follow_a_double_colon` |
| `m2a` | 末次还原失败升 rc=3 | `…not_swallowed_and_sha_still_runs` |
| `m2b` | 末次还原失败时仍跑 SHA 自检 | 4 条 M② 用例 |
| `m2c` | 「信号退出不是还原失败」整段分辨 | `…signal_exit_during_final_restore…` |
| `m2d` | 「只认干净退出码」（退回只看 SystemExit） | `…exit_code_is_not_a_clean_signal_exit` + `…fail_closed` |
| `m2e` | 末次成功但本轮有失败过 ⇒ 仍显形 | `…mid_loop_failure_surfaces…` |
| `rc1` | reconcile 同档重复即报错 | 坏法 G 变 rc=0 |
| `rc2` | reconcile 计数非负整数 | 坏法 H/I 变 rc=0 |
| `rc3` | 尾档整 token 约束（整个去掉） | 坏法 J/M 变 rc=0 |
| `rc4` | JSON 重复键检测 | 坏法 K/L 变 rc=0 |
| `rc5` | 整 token 退回 `(?![\d.])` | 坏法 M 变 rc=0 |
| `rc6` | AST 分母含 `MUTATIONS += [...]` | 坏法 N 变 rc=0 |

**sha 判据带验伪锚**：每段跑前跑后各落 **5 行** `shasum -a 256`（三个改动脚本 + `fsrs_bridge.py`
+ `decay_beta.py`），判据 = `sha lines 5/5 且逐字同`，⛔ 不是只比较两份可能同为空的输出
（见台账 ⑱ 的假绿）。**十九段实测全部 `5/5 same=yes`。**
定稿 sha：`mutation_kill_identity.py` = `0fcc3c59…`、`g33_mutation_gates.py` = `ee9b6e3a…`、
`mutation_verdict_reconcile.py` = `0730d8a1…`、`fsrs_bridge.py` = `a766fbcc…`、`decay_beta.py` = `3bf4ed94…`。

⛔ 还原走「快照 → 补丁 → 从快照 `copyfile` 写回」，**未用** `git stash` / `git checkout`；
每条替换 `assert count == 1`。④ 段按 (h)④ 固定走 **(甲) 进程内注入**，⛔ **没有启动任何 g33 子进程**。

**⑤ MEDIUM③ reconcile 负控 —— 14 种坏法 + 2 验伪锚**（`reconcile-synthetic-final-20260915T003018.txt`；
⛔ rc 直取 python 退出码，无管道）：

| 坏法 | 形态 | rc | 被哪一条判据抓到 |
|---|---|---|---|
| A | 篡改一档计数（和行不动） | 1 | 逐档相加 ≠ 该套印的和 |
| B | JSON 缺一个档键 | 1 | 缺档不得当 0/「一致」 |
| C | 分母**内部自洽**但 ≠ AST（137/137/137） | 1 | **只有** AST 现算这一维 |
| D | 声明了却不给输入 | 1 | 缺席不是「一致」 |
| E | **真实** tee 截断到无汇总段 | 1 | KILLED 行命中 0 次 |
| F | 形态喂错（g32b 用 `--json`） | 1 | 该套是 stdout 形态 |
| G | stdout 同一档出现两次 | 1 | `_put()` 拒静默覆盖 |
| H | JSON `18.9` 小数截断 | 1 | `_nonneg_int` |
| I | JSON `19 / -1` 负数抵消 | 1 | `_nonneg_int` |
| J | stdout `SURVIVED: 0.5` | 1 | 整 token 约束 |
| K | JSON 重复**档键** | 1 | `object_pairs_hook` |
| L | JSON 重复 `total` | 1 | `object_pairs_hook` |
| M | stdout `SURVIVED: 0x10` | 1 | 整 token 约束 |
| **N** | **6/6/6 部分表冒充全量**（g32b 真实分母 138） | 1 | AST 分母含 `+=` 扩展 |
| 验伪锚 ① | 全对合成样本（g32b 138 + g33 18） | **0** | —（证明能判绿） |
| 验伪锚 ② | **真实** g32cb 全量存档 | **0** | — |

坏法 C 与 N 是「独立分母真参与比较而非装饰」的两个验证点：C 的样本三数内部完全自洽，
N 的样本是**曾经真的能通过**的形态（见 (g) 的 round-4 更正）。

⛔ **本段自己踩过的两个判据坑（已修，如实记）**：① 先用 `python3 … | tail -3; echo rc=$?`
取到的是 `tail` 的退出码 ⇒ 六种坏法全报 `rc=0`（**假绿**）；② 改取 `$pipestatus[1]` 后又因
脚本路径与 `cd backend` 重复 ⇒ 全报 `rc=2`（**假红**）。两次都是「判据在所有输入上给同一个
答案」露的馅 —— **验伪锚的价值正在于此**。

### (i) 只读自检（四份）+ 全量真跑（两套，承重）

| 入口 | rc |
|---|---|
| `g32b_mutation_gates.py --list` | **0** |
| `g32cb_mutation_gates.py --list` | **0** |
| `g32ccr1_negative_controls.py --list` | **0** |
| `g33_mutation_gates.py --selfcheck-syntax` | **0**（⛔ g33 **无** `--list`） |

**承重全量真跑（两套，⛔ 在代码定稿冻结后跑；串行，两套变异的是同一组文件）**：

⛔ **以下是绑最终 HEAD `34473ebd` 的那一轮**（五轮 Codex 整改期间每改一次代码就重跑一次，
共跑了 5 轮；早先几轮的 `*-run-*.txt` 存档保留但**不作验收依据**）。

| 套 | 存档 | rc | 六档 | 变异目标文件 + `fsrs_bridge.py` 前后 sha |
|---|---|---|---|---|
| `g32cb` | `g32cb-run-20260915T001621.txt` | **0** | **9/9 KILLED**，其余五档 0，六档之和 9 = 变异条数 9 ✓ | 3 行逐字同 ✓ |
| `g32ccr1` | `g32ccr1-run-20260915T001953.txt` | **0** | **11/11 KILLED**，其余五档 0，六档之和 11 = 变异条数 11 ✓ | 3 行逐字同 ✓ |

前后 sha（两套各一组 before/after，逐字相同）：
`SKILL.md` = `c1588ec6fda0371c85d801870bd035360891cd63f20c22be10fab779a173a1e4`、
`validate_learning_events.py` = `a7cbaee4b9cabd3431a73a944921d739fe3d3ab9561bdf2555a897bb61272025`、
`fsrs_bridge.py` = `a766fbcc28e3ff917e740843c633e800aa8a75e949295f83efc90f55105f90f0`。
⛔ sha 判据带**验伪锚**（前后存档各须恰好 3 行 `^[0-9a-f]{64}  `，实测 `lines=3` / `lines=3`）——
第一轮因 zsh 不对无引号变量做词分割，两份存档只装着同一句报错却照样 `diff` 判「相同」（见台账 ⑱），
**那一轮已作废**，本表是修正后的第二轮。

⚠️ **关于 H2 / M① 收紧会不会误伤正当 KILLED**：两套共 20 条变异在收紧后**全部仍是 KILLED**，
`HARNESS-ERROR` = 0 —— 本树上未出现新的误判。（⛔ 但这只是这两套 20 条的实测，不覆盖 g32b/g33 的 24 条，见「本卡未证明什么 ⑨」。）

**`g33` 按 R-B14-9 本卡只跑 `--selfcheck-syntax`**（rc=0；排 BRIDGE 条的 g33 真跑放行给 T8-C；含 BRIDGE 条的全量 / 副本树变异属第十五批）。
**`g32b` 排 M5 的 `--only` 全量（可选、非承重）：未跑**。理由：它是可选项，且本卡的 reconcile 对 g32b 形态已用**逐字照 `:3019-3041` 打印格式**的合成样本覆盖；部分跑本就**不产出六档聚合表**（`:3038`），喂不进 reconcile。不跑不扣分，登记在此。

**整卡级零写者哨兵**（`fsrs_bridge.py` / `decay_beta.py`，开工与收工各一组）：

- 开工（`zero-writer-open-20260914T222907.txt`）：`a766fbcc28e3ff917e740843c633e800aa8a75e949295f83efc90f55105f90f0` / `3bf4ed9402a4c8edfde16630a79094a5d4518fd181fa60810319fe46d37abb90`
- 收工（`zero-writer-close-20260914T231104.txt`）：**同上两行，逐字相同**（`diff` 实测 `IDENTICAL=yes (2 行)`）

### (j) 既有不回退 + 目录级 diff 只 `<`

| 项 | 实测 |
|---|---|
| 开工跑 | `unit-open-20260914T222912.txt` — `35 failed, 5077 passed, 48 skipped, 23 xfailed, 29 errors`，nodeid diff 与 `$BASE` **空** |
| 收工跑（绑最终 HEAD `34473ebd`） | `unit-close-20260915T003009.txt` — `35 failed, **5108** passed, 48 skipped, 23 xfailed, 29 errors`（+31 = 本卡新单测全绿） |
| `diff base.nodeids close.nodeids` | **完全为空**（`base=64 close=64`），`grep -c '^>'` = **0** |

⇒ 既有红集一条不多一条不少（连 `<` 都没有 —— 本卡没修好任何既有红，也没弄红任何既有绿）。
⛔ 判据只用 `$RUN` / `$BASE` 两个固定变量，未用 glob 取存档，也未拿 `wc -l` 当判据。
⛔ `--ignore` 按 R-B14-3 写**相对路径** `tests/unit/test_deploy_vault_sh.py`（`cd backend` 之后）。

### (k) 现网只读 + 禁连

- 新单测/负控全部 I/O 落 pytest `tmp_path` 与 scratchpad，未写车道树外任何路径；未设指向现网的环境变量。
- 现网 LanceDB `/Users/Heishing/Desktop/canvas/canvas-learning-system/data/lancedb`：`find … -type f -newer $EV/sentinel | wc -l` = **0** ✓（只 `ls -la` + `find`，未打开）。
- ⛔ 未连 7691 / 7687（目录级跑收尾行 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)`）。
- **fsrs_bridge 判据（卡文 (k) 那条）⛔ 实测 2 ≠ 卡文期望的 0 —— 如实报偏差，不改文档去凑判据、也不放宽判据**
  （证据 `judge-fsrs-bridge-20260914T231442.txt`）：

  | # | 判据 | 实测 |
  |---|---|---|
  | ① | 卡文字面：本卡 diff 的 `+` 行含 `fsrs_bridge` 的条数（期望 0） | **2** ⛔ |
  | ② | 四文件里 `fsrs_bridge` 的**可执行**出现（AST 排除 docstring）`$PREV` vs `HEAD` 多重集 | **完全相同**（仅 g33 既有常量 `'fsrs_bridge.py'`）✓ |
  | ③ | 本卡 diff 面是否含 `canvas-vault/` 任何路径 | **0** ✓ |
  | ④ | 零写者哨兵 开工 vs 收工 sha | **逐字相同** ✓ |

  ① 命中的两行**逐字**是（均为本卡新增的 **docstring**，不是代码）：

  ```
  +    铁律覆盖的 `fsrs_bridge.py`）。提为模块级 + 注入 `restore_all` / `exiting` 回调是
  +铁律覆盖的 `canvas-vault/.claude/scripts/fsrs_bridge.py`。
  ```

  两处都在解释「为什么 M② 的负控**不能**起 g33 子进程」—— 去掉文件名会让这条约束说不清（DD-13）。
  **判据 ① 想量的性质是「本卡有没有新增触碰该文件的代码」，它量的却是「文本里有没有这个词」**；
  卡文本身已为同一原因更正过这条判据一次（旧版对既有常量恒失败），这是同一问题的下一次迭代。
  判据 ②③④ 三条各自独立地证明了那个性质成立。**本条列为卡文判据待更正项，交主 session 裁定**
  （建议改为：新增行里含 `fsrs_bridge` 且**不在** docstring/注释内的条数 = 0，或直接以 ②③④ 为准）。
- 验伪锚（同次执行）：`grep -nF fsrs_bridge backend/scripts/g33_mutation_gates.py` → `63:`（证明 ① 那条管道能命中；⚠️ 卡文写 `:62`，`ruff format` 后既有常量行号已漂到 `:63`）。

### (l) Codex + 提交

**Codex 五轮（D-15：多轮直到绑最终 HEAD 的一轮 B/H = 0；上限 5 轮）**，模型 `gpt-6-astra` ·
`reasoning_effort=ultra` · `codex-cli 0.153.3`，每份存档首部六行 blockquote 自证齐全：

| 轮 | 绑定 SHA | B | H | M | L | 处置 |
|---|---|---|---|---|---|---|
| r1 | `223beed7` | 0 | 0 | 3 | 2 | 五条**全部接受并修** |
| r2 | `767f4b6a` | 0 | **1** | 3 | 0 | 四条**全部接受并修**（那条 HIGH 是 r1 整改**自己引入的回归**） |
| r3 | `98edb541` | 0 | 0 | 2 | 1 | 三条**全部接受并修** |
| r4 | `991373e5` | 0 | 0 | 1 | 1 | 两条**全部接受并修**（含 g32b 分母 6→138 的重要更正） |
| **r5** | **`34473ebd` = 最终 HEAD** | **0** | **0** | 3 | 1 | **达标**；四条按协议 §1 登记不阻断（见下） |

⛔ **十四条全部接受，无一条驳回**（r1~r4）。`_nodeid_shaped` 一个函数被打掉**三次**，
三次错法与反例已全部写进它的 docstring。

**r5 四条登记（⛔ 未修 —— 已到 D-15 的 5 轮上限，再改代码就要第 6 轮）**：

| 级别 | 结论 | 我的评估 |
|---|---|---|
| MEDIUM | AST 分母对 `if True:` 包住的 `+=` / 列表展开仍会少算 | **成立**。当前实现只扫**模块级** `Assign`/`AugAssign`，嵌套块里的扩展数不出来。四套现状都不是这种写法（实测 138/9/11/18 正确），但判据的**覆盖面**确实窄于它的名字。建议下一卡：把 fail-closed 面扩到「模块级出现任何提到 `MUTATIONS` 的其它语句即报错」 |
| MEDIUM | 信号触发的**成功重试**仍能掩盖首次 `OSError` | **成立**。守卫 `critical()` 内重试成功后抛 130，我的 `guard_exit` 认它是干净退出 ⇒ 首次错误无痕。要分开需要守卫侧暴露「本次是否重试过」，属 `RestoreGuard` 签名面（卡文硬边界禁改） |
| MEDIUM | 负控存档只有 17 层、绑旧哈希 | **已修（纯证据，非代码改动）**：本轮重跑 **19 层**全部绑最终 HEAD `34473ebd`，见 (h) |
| LOW | 末次还原**成功**时仍打印「末次还原失败」字样 | **成立**。`pending_failures` 路径复用了 `_report_final_restore_failure`，文案说得比事实宽 —— 正是本卡要消灭的那类措辞。⛔ 纯文案修复也需第 6 轮，故登记 |

**提交**（五个独立 commit，header 均 ≤100 `wc -m`、含批次标记与卡号）：
`223beed7` → `767f4b6a` → `98edb541` → `991373e5` → `34473ebd`。
`*.stderr*` 未入库（`.gitignore:264` 覆盖，实测本卡证据目录 0 个）；**未 push**。

**判据（绑最终 HEAD）**：
- 地盘门 `$PREV..HEAD` 排除 `_bmad-output` = 恰好 4 个文件（`mutation_kill_identity.py` /
  `g33_mutation_gates.py` / `mutation_verdict_reconcile.py` / `test_mutation_kill_identity_r3.py`）；
  `backend/app` 越界 = **0**；
- ruff（zsh 数组）`files=4` → `All checks passed! rc=0`；验伪锚（F821 文件）`rc=1` ✓；
  `ruff format --check` → `4 files already formatted rc=0`；
- 四份只读自检 rc 全 0；两套承重全量 rc 全 0；reconcile 真跑 rc=0。

---

## 4-B 用户侧（零技术词）

我跑那套「检查门有没有真起作用」的自检工具时，它以前会把「其实没检查到」悄悄当成「通过」——
比如一行报错信息有两种读法它却只按一种读、或者它拿**另一道**检查的出错位置冒充**这一道**的、
又或者它对照用的标记早就失效了它还照样给我一个「没问题」。现在这几种情况它都会老实说「这我没检查到」。
还有一处更要紧：以前它收尾时如果没能把临时改动还原回去，这件事会被它自己咽下去、报告里一个字都不提；
现在它会把「可能有东西没还原干净」明确报出来，并且**仍然**去核对文件有没有被改动过。

**felt-sense**：我感觉这套自检终于不会再骗我了 —— 以前它说「通过」我心里得打个问号，
因为分不清是「真的查过而且没事」还是「压根没查到」；现在这两种情况它会说成不同的话。

---

## 本卡未证明什么

1. 未证明 `g32cb` / `g32ccr1` / `g32b` 三套的同型「末次还原吞没」是否存在/已修 —— 本卡只修 `g33` + census，四套统一移交台账。
2. 未证明 H1 的读法空间枚举已是**完全**封闭 —— 只证了已知四类读法 + 本轮反例 + 两个翻转方向；属性测试 / 穷举未做。
3. 未真跑 D-28 延期的 `expect_loc` 具体断言绑定（T8-C 面）；本卡只封弱位置判据自己的承诺。
4. 未证明 reconcile 对「存档被篡改成看似一致」以外的全部对抗形态覆盖（例如两套分母互换但和相等、真实 tee 里混入两次跑的输出且两次数字恰好同形）。
5. 未证明真实 SIGINT/SIGTERM 在「末次还原」那一刻注入的端到端行为 —— 负控用的是**模拟异常**，不是真信号时序。
6. **未跑 g33 / g32b 的全量真跑**（R-B14-9）⇒ 未证明这两套在当前树上「跑完六档之和对得上、还原逐字节相同」，也未证明 reconcile 对这两套**真实**输出的解析（只用合成样本覆盖其格式）。
7. 未证明 g32b `M5-R5` / g33 `M5-cas-revision-only` 两条触及 `BRIDGE` 的变异在不碰 `fsrs_bridge.py` 的前提下有等价跑法（副本树 / 排除名单未做，第十五批面）。
8. 未实测「变异中途被杀会留下变异体」的真场景 —— R-B14-9「等字节 restore 不算碰」是规则裁定，本卡依据的是 sha 门 + squash 时 `git diff` 门双层兜底。
9. 未证明 `ast_mutation_count` 对「`MUTATIONS +=` 被包在 `if`/`for` 等**嵌套块**里」或「列表展开」的写法数得对 —— 当前只扫模块级 `Assign`/`AugAssign`，其余形态**不报错也不计入**（Codex round-5 MEDIUM-1，已登记未修，见 (l)）。四套现状均非该写法（实测 138/9/11/18 正确）。
10. 未证明 g33 守卫在 `critical()` 内**重试成功**后抛 130 的那条路上，首次 `OSError` 能显形 —— 要分开需要守卫侧暴露「本次是否重试过」，属 `RestoreGuard` 签名面（卡文硬边界禁改）（Codex round-5 MEDIUM-2，已登记未修）。
11. 未证明 `pending_failures` 那条新路径的**措辞**与事实一致 —— 末次还原**成功**时它仍打印「末次还原失败」字样（Codex round-5 LOW，已登记未修；纯文案修复也需第 6 轮，超 D-15 上限）。
12. 未证明 H1 那条**保守性代价**（参数化 + reason 以 `]` 收尾 ⇒ HARNESS-ERROR）在四套的**全部** 44 条变异上不产生新的 HARNESS-ERROR —— 只在本卡真跑的两套上实测未出现。

---

## 台账待登记条目

1. CARD-DEBT-mutkill-R3 修复 sha：**五个独立 commit** `223beed7` → `767f4b6a` → `98edb541` → `991373e5` → **`34473ebd`（终审绑定）**；先红后绿 nodeid 与 **19 层**负控路径见 (b)/(h)。
2. 新增两文件 `backend/scripts/mutation_verdict_reconcile.py` / `backend/tests/unit/test_mutation_kill_identity_r3.py` —— **已批 R-B14-8**（地盘第二批放行），登记为「已放行」。
3. **`g32cb` / `g32ccr1` / `g32b` 同型「末次还原吞没」census = 三套全部存在**（模块级 `_restore_active_or_keep_exit_code`，g32b `:2510-2531` / g32cb `:337-358` / g32ccr1 `:245-266`）—— 本卡按硬边界不碰，**建议另立卡做四套统一**（不并入 T8-C，T8-C 是 `expect_loc` 收窄面）。⚠️ 判据坑：这三套的函数**不叫** `restore_or_keep_exit_code`，拿 g33 的符号名 grep 会得到 0 命中的假阴性。
4. 四套只读自检口径更正：**g33 无 `--list`**，用 `--selfcheck-syntax` —— 建议主 session 把设计稿 §4「四套 --list」改为「三套 --list + g33 selfcheck」。
5. recon C §3 的 H1 行号（`:211` / `188-213`）与 UAT-R2 的 H1 落点行号均已漂移 —— 本卡一律符号名锚定，后人勿照抄旧行号。
6. Codex 五轮存档 `_bmad-output/审查/codex-review-CARD-DEBT-mutkill-R3[-rN].md`（prompt 同名在 `prompts/`）；绑定与计数：r1 `223beed7` 0/0/3/2、r2 `767f4b6a` 0/**1**/3/0、r3 `98edb541` 0/0/2/1、r4 `991373e5` 0/0/1/1、**r5 `34473ebd`（=最终 HEAD）0/0/3/1 ⇒ D-15 达标**。r1~r4 共 14 条**全部接受并修，无一条驳回**；r5 四条登记不阻断（其中 1 条已补证据）。
7. `tests/unit` 目录级 diff 结果：**完全为空**（`base=64 close=64`，`grep -c '^>'`=0）；passed 由开工 5077 → 收工 **5108**（+31 = 本卡新单测）。
8. g32b 同型（`:65` / `:135`）**已裁 R-B14-9**：排 M5 后 `--only` 全量可选非承重 —— 本卡跑/未跑与前后 sha 见 (i)。
9. g33：本卡只跑 `--selfcheck-syntax`（R-B14-9）；排 BRIDGE 条的 g33 真跑已放行给 T8-C，含 BRIDGE 条的全量 / 副本树变异仍移交第十五批。
10. MEDIUM③ 口径：**只有 g33** 有 `--json` / `verdict_counts`（`:393` / `:689`），三套为 0；「给三套补 `--json`」**已裁另立第十五批卡**（R-B14-9 末段），本卡登记为「已裁另立卡」。
11. §〇 事实格行号漂移已由本卡逐条复测确认（`_boundary_ok` 214-225、`expect_loc[5:] not in fps` 620、`restore_or_keep_exit_code` 436-454 等），后人引用请勿照抄旧值。
12. 判据口径更正：`grep -rn decay_beta backend/scripts/g32*.py …` 的 glob 会命中两个非 harness 脚本（实测 3 命中），零命中判据须**五文件具名**；后人勿照抄 glob 写法。
13. g33 `--only` 只接**单个** id 前缀（`:394` / `:459`，无逗号多值）⇒「排除 BRIDGE 条」须逐条跑或改 harness —— 登记给 T8-C。
14. g32b 部分跑 rc 口径：预期 4；任一 HARNESS-ERROR 时 `:2812-2814` 返回 2 盖过 4（不算绿，登记「不当通过」）。
15. g32b 启动自愈 `_self_heal_leftovers()`（def `:522` / 调用 `:2605`，**早于** `:2670` 的 `--only` 过滤）会对含 `BRIDGE` 的全部目标写回残留变异体 —— 由 R-B14-9 sha 前后门覆盖，出现即卡阻断。
16. g32b / g32cb / g32ccr1 三套源码均**无** `_TARGET_FILES` 符号（只 g33 有）—— 变异目标文件须具名（g32b `_touched` `:2654-2656`；g32cb `:82-83`；g32ccr1 `:59-60`），后人勿照抄。
17. **卡文 §二.1 判据更正**：`grep -nF fsrs_bridge backend/scripts/g32b_mutation_gates.py` 实测回 **3 行**（`65:` 常量 + `2609:` / `2674:` 注释），不是卡文写的单行 —— 行数不得当判据。
18. ⛔ **本卡自己踩到并记下的判据坑（建议进 `card-batch-protocol.md` §2.2）**：`shasum -a 256 $TARGETS`（`TARGETS` 为**无引号**的普通字符串变量）在 **zsh** 下**不做词分割** ⇒ 整串被当成**一个**文件名 ⇒ `shasum` 报 `No such file or directory`，前后两份存档**各自只装着同一句报错**，`diff` 照样判「相同」= **门通过了但什么都没量到**（与本卡要修的 H1/M① 是同族形态：判据在残缺输入上恒成立）。正确写法 = **zsh 数组** `T=(a b c)` + `"${T[@]}"`；并且 sha 判据必须带**验伪锚**——前后存档各自 `grep -cE '^[0-9a-f]{64}  '` 必须等于文件数，否则停下。本卡第二轮真跑已按此重写（`rerun_suites.sh`）。
19. ⛔ **卡文 §〇 事实格「g32b 分母 = 6」是错的，实测 138**（`MUTATIONS = [6]` + 36 段 `+=` 共 132）。该错值曾被本卡 `ast_mutation_count` 照抄 ⇒ g32b 的「独立分母」恒为 6 ⇒ 部分表可冒充全量。**建议主 session 更正卡文 §〇 与设计稿里所有「g32b 6」的引用**；后人取 harness 分母时必须把 `+=` 扩展算进去（或以该套自己 `--list` 印的条数交叉核）。
20. **Codex round-5 的三条未修项**（1 LOW + 2 MEDIUM）与理由见验收单 (l) —— 已到 D-15 五轮上限，再改代码需第 6 轮，交主 session 裁定是否另立卡。
21. **本卡新增的「每层各留一个显形点」纪律**：首轮负控 `m1b` 拆层后 0 红，暴露「两层冗余 ⇒ 拆一层不红 ⇒ 该层承重不可证」。建议写进 `card-batch-protocol.md` §3（负控最低覆盖）：**多层防线必须每层各有一个独立显形点**，否则负控只证明了「这一组」承重。
