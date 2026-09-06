# UAT — CARD-DEBT-mutation-kill-identity

> 批次 `[BATCH-2026-09-05-第十二批 / CARD-DEBT-mutation-kill-identity]`
> 车道 `card-z2-cas`（分支 `card/z2-cas`）；开工 HEAD `3601051d`（= CARD-G3-3-R1 末 commit），
> `git status --porcelain` 空。日期 2026-09-06。

## 4-B 用户产品体验

**无变化。** 本卡改的是「自检工具的自检」——把三套变异负控从「这个门红了就算杀死」
改成「必须红在它自己说的那条断言上」。用户看不到任何差异：白板、复习、评分链的行为
一个字节都没动（`git diff` 对 `backend/app` 与 `canvas-vault` 为空）。

**felt-sense**：像是把「考试及格了」改成「必须答对指定的那道题才算及格」。以前一份
自检报告说「138 条防线全都有人守着」，其实里面混着「守的人跑错了考场」和「考卷根本
没印出来」两种情况，而报告长得一模一样。现在这两种会各自报出来。

---

## 一 本卡做了什么

| # | 事情 | 位置 |
|---|---|---|
| 1 | 抽出共用判据模块 | `backend/scripts/mutation_kill_identity.py`（新文件） |
| 2 | g33 改 import 共用件，删掉自己的重复实现 | `g33_mutation_gates.py` |
| 3 | g32b / g32cb / g32ccr1 三套回填 `EXPECT_MSG` + 编译自检 + 判据换共用件 | 三个 harness |
| 4 | g32b 补 `--list` 只读入口、`--probe` 观察入口、`--only` 定点入口 | `g32b_mutation_gates.py` |
| 5 | g32b 补 SIGTERM/SIGINT/SIGHUP handler；启动自愈从「只扫主锚」扩到「主锚+同层锚」 | 同上 |
| 6 | 4 条 ANCHOR-ERROR（M142/M143/M145 主锚、M157 层锚）逐条**更锚**到现址 | 同上 |

## 二 判据面的实测依据（不是推断）

`_bmad-output/审查/evidence-mutkill/judge-surface-probe-20260906T103246.txt`
（隔离目录跑的三条玩具用例，不碰任何生产文件）：

| 观察 | 对判据的意义 |
|---|---|
| 多行断言消息的 `-rf` reason **只有第一行**（第二行进不来） | `EXPECT_MSG` 必须落在消息首行内；绑到 `\n` 之后的段 = 恒不命中 |
| `COLUMNS=80` 时 reason 被截成 `…AssertionError: 这是一条很长很长的断...` | `judge_env()` 的 `COLUMNS=1000` **承重**：少了它全部条目会报 SURVIVED，长得跟「所有门都不承重」一模一样 |
| 无消息的 `assert len(xs) == 5` 的 reason 是 `assert 3 == 5` | 那是**值**不是**身份**（换个 fixture 数据就变）⇒ 这类断言只能进 `EXPECT_MSG_EXEMPT`，不能硬凑「看起来唯一」的片段 |

## 三 锚点自检（(a) 分列）

`evidence-mutkill/g32b-list-20260906T100653.txt`（新增的只读 `--list` 入口，跑后
SKILL.md / fsrs_bridge.py / schema 三个文件 sha 与基线逐字同 ⇒ 确认只读）：

- **Z2 引入的新锚漂：0 条。** Z2 那 +207 行没有让 g32b 的任何一条锚失配。
- **Z6-C 登记的旧锚漂：4 条**，与台账逐条对上：
  `M142-dup-uses-global-w`（主锚）/ `M143-missing-applied-flag-tolerated`（主锚）/
  `M145-recovery-does-not-promote-flag`（主锚）/ `M157-anchor-direction-unchecked`（**层**锚）。
- g32cb `--list` 9 条全 1、rc=0；g32ccr1 `--list` 11 条全 1、rc=0
  （`g32cb-list-…txt` / `g32ccr1-list-…txt`）。

## 四-A 🤖 Claude 已代验（技术断言全在这段）

> ⚠️ **本表是「送 Codex 前」那一轮（审 SHA `52f1ccd2`）的数字。**
> 外审整改后的终态跑批见 §六-B 末段与下表「整改后」列 —— 两者都如实留着，
> 因为审 SHA 绑的是前者。

| # | 判据 | 结果 | 证据（`_bmad-output/审查/evidence-mutkill/`） |
|---|---|---|---|
| 1 | `g32b` 全量 | ✅ **`KILLED: 138/138`**、`ANCHOR-ERROR: 0`、`SYNTAX-INVALID: 0`；**末行 `rc=1`** | `g32b-run-20260906T112329.txt` |
| 1b | ↑ rc=1 的**唯一**原因 | `M100` / `M151` 两条「声明为 complete 但变异体单独即可杀 ⇒ 层是多余的」——**Z6-C 早已登记、卡文明确排除**的既有项，非本卡引入；`SURVIVED` 行数 = **0** | 同上 |
| 2 | `g32cb` | ✅ `9/9 KILLED`、`ANCHOR-ERROR 0`、`SYNTAX-INVALID 0`、`rc=0` | `g32cb-run-20260906T111736.txt`（首跑 `8/9` 见 §五.1） |
| 3 | `g32ccr1` | ✅ `11/11 KILLED`、`rc=0` | `g32ccr1-run-20260906T110751.txt` |
| 4 | `g33` | ✅ `18/18`、`SYNTAX-INVALID 0`、还原逐字节相同、残留/基线缺失均「无」、`rc=0`；**verdict 列与 Y1-A 收官 JSON 逐字相同**（id+verdict 序列比对 `True`） | `g33-run-20260906T111250.txt` / `g33-results-20260906T111250.json` |
| 5 | 4 条更锚定点复核 | ✅ 全 KILLED，各自落在**从门源码推导**的那条断言上 | `g32b-only4-20260906T112207.txt` |
| 6 | 6 个生产文件 sha 跑前跑后 | ✅ **逐字相同**（`diff` 无输出）；`MARK` 文件集 = 基线 5 项，一字不差 | `sha-before-20260906T100653.txt` / `sha-after-20260906T120943.txt` |
| 7 | 生产文件未被本卡改动 | ✅ `git diff 3601051d HEAD -- backend/app canvas-vault docs` 为空；`git status --porcelain` 同面为空 | 本文件 |
| 8 | 门本体未动 | ✅ `git diff HEAD -- backend/tests/` 为空 | 本文件 |
| 9 | 两回归文件 | ✅ **`161 passed, 1 xfailed`**（恰 1）、`rc=0` | `regression-20260906T120956.txt` |
| 10 | `tests/skills` 目录级 | ✅ `369 passed`、`rc=0`（收工时生产文件确已还原） | 同上 |
| 11 | 无偷连数据库 | ✅ 两次跑批都报 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)` | 同上 |
| 12 | live vault 账本 | ✅ 开工/收工都是 `NOFILE`（本卡从未写 live vault） | 本文件 |
| 13 | `ruff format --check` + `ruff check` | ✅ 5 files already formatted / All checks passed | `lint-pyright-20260906T121516.txt` |
| 14 | `pyright`（本卡 5 个文件） | ✅ **`0 errors, 0 warnings`**（顺带修掉 2 处**存量** Optional 缺陷：`re.match(...).group()` 可能 None、`fa[:90]` 可能 None） | 同上 |
| 15 | 裁判 3：`grep -c expect_msg` 每套 > 0 | ✅ g32b 27 / g32cb 18 / g32ccr1 18 / g33 16 | 同上 |
| 16 | `g32ccr1` 新增行不含变异标记字面量 | ✅ `git diff -- g32ccr1_negative_controls.py \| grep -c '^+.*<标记>'` = **0**（lefthook `mutant-residue-scan` 允许名单不含它） | 本文件 |

### 整改后（与审 SHA 已失绑，见 §六-B）终态

| # | 判据 | 结果 | 证据 |
|---|---|---|---|
| r1 | `g32b` 全量 | **99 绑定断言身份 + 39 仅证明指定门红了 = 138**；`SURVIVED 0` / `HARNESS-ERROR 0` / `ANCHOR-ERROR 0` / `SYNTAX-INVALID 0`；末行 `rc=1`（仍只因 Z6-C 既有的 M100/M151） | `g32b-run-r2-20260906T124447.txt` |
| r2 | `g32cb` | `9/9 绑定断言身份`、`KILLED-UNBOUND 0`、`HARNESS-ERROR 0`、`rc=0` | `g32cb-run-r2-20260906T123455.txt` |
| r3 | `g32ccr1` | `11/11 绑定断言身份`、`rc=0` | `g32ccr1-run-r2-20260906T123928.txt` |
| r4 | `g33` | `18/18`、`rc=0`，**verdict 列仍与 Y1-A 收官逐字同**（`id+verdict` 序列比对 `True`） | `g33-run-r2-20260906T133140.txt` / `g33-results-r2-20260906T133140.json` |
| r5 | 6 个生产文件 sha + `MARK` 集 | 与**开工基线**逐字相同（`diff` 无输出） | `sha-after-r2-20260906T133126.txt` |
| r6 | 两回归 + `tests/skills` | `161 passed, 1 xfailed` / `369 passed`；两次都 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0` | `regression-r2-20260906T133656.txt` |
| r7 | `ruff` + `pyright` | `5 files already formatted` / `All checks passed!` / `0 errors, 0 warnings` | 同上 |
| r8 | `--only` 缺值 / 空前缀 | 两种形态实测均 `rc=4`（LOW-8 整改的行为验证） | 本文件 |

## 四-B 👤 你来验

本卡**没有任何用户可见的产品变化**（见开头 4-B 段）。要确认这一点，你只需要：

- [ ] 我打开原来的白板，随便点一个概念节点 → 我看到它和昨天**一模一样** → 我感觉放心，
      这次改的确实只是"自己检查自己"的部分，没碰到我的笔记。
- [ ] 我在白板上做一次答题评分 → 我看到评分照常记下、复习时间照常更新 → 我感觉流畅，
      没有多出任何提示或卡顿。
- [ ] 我打开 `节点/` 文件夹随便挑一个 md → 我看到里面的 `calibration_log` 条目没有多、
      没有少、也没有变形 → 我感觉信任，负控跑完是真的把文件还原干净了。

> 上面三条全在 Obsidian 里完成，3 分钟；不需要终端、不需要看任何日志。

## 五 杀灭数变化逐条给原因

| harness | 本卡前 | 本卡后 | 变化原因 |
|---|---|---|---|
| **g32cb** | `9/9`（旧判据：`rc==1 and gate in out and "failed" in out`） | 首跑 **`8/9`** → 更正绑定后 `9/9`、rc=0 | ⛔ **本卡第一个真发现**，见 §五.1 |
| **g32ccr1** | `11/11`（旧判据） | `11/11`、rc=0 | 11 条**全部**落在从门源码推出的那一条断言上，无一例外；另暴露一处**门覆盖缺口**，见 §五.2 |
| **g33** | `18/18`（Y1-A 已有 `expect_msg`） | `18/18`、rc=0 | verdict 列与 `mutation-results-20260906T025116.json` **逐字相同**（id+verdict 序列比对为 True）；换共用模块 + 放宽 PYEOF 正则**没有**改变任何裁决 |
| **g32b** | Z6-C：`134 KILLED + 4 ANCHOR-ERROR`（旧判据，且判据只到「摘要是 1 failed」为止） | 见下（全量跑批结果） | 4 条 ANCHOR-ERROR 已全部更锚并**逐条实测 KILLED**，见 §五.3 |

### §五.1 g32cb M2 —— 击杀落在**别的断言**上（本卡要抓的东西的第一个真实样本）

- 变异：拆掉 foreign 凭据提升（`if _fa_fg is False:` → `if False:`）。
- 脚本自陈 + 作者按源码推的目标：`:5316` 的
  `assert r3.returncode == 0, "⛔ 恢复后 E1 仍不可重跑 ⇒ 两阶段不收敛，那张白板卡死"`。
- **实测**：门红在**更早**的 `:5313`
  `assert r2.returncode == 0, f"E2 应收敛: {r2.stderr[:300]}"` ——
  拆掉提升后 **E2 自己就写不进去了**（writer 撞上「receipt 记 `true` 却仍在待恢复队列」的
  自相矛盾，fail-closed 拒写）。链条在声称的那一步**之前**就断了。
- 处置：把 `EXPECT_MSG["M2"]` 更正为 `"E2 应收敛: "`，并在表内逐条写清原委。
  ⚠️ **防线仍然承重**（门确实红了），错的是卡文的因果叙述；旧判据把这两种完全不同的
  症状记成同一个 KILLED，于是那个叙述**从来没被验证过**。
- ⚠️ `:5316` 那条断言并没有失去承重方：`g32b` 的 `M161-foreign-no-credential-promotion`
  （另一种拆法：`_ok_fg = True` 静默跳过提升并谎报成功）实测正落在它上面。
  两条变异拆同一道防线的不同侧面、症状不同 —— 这正是新判据能分辨出来的东西。

### §五.2 g32ccr1 E3 / E9 —— 一条判据「没有任何变异为它承重」

两条变异（扩表 / 清空表）都落在
`test_g32ccr1_charset_scope_is_bounded_by_ledger_record_reality` 的 ⓪
「严格表逐项钉死」那条断言上（它排在函数最前面），而**不是**脚本 docstring 声称的
③「死条目」判据。⇒ ③ 那条判据当前**没有任何变异为它承重**。
本卡只**登记**（属门覆盖面，不是本卡范围）。

### §五.3 4 条 ANCHOR-ERROR 的处置 —— 全部更锚，无退役

`g32b-only4-20260906T112207.txt`（定点复核，`--only` 的 rc 恒为 4，不构成全量结论）：

| tag | 旧锚为什么失配 | 新锚现址 | 实测落点 |
|---|---|---|---|
| `M142-dup-uses-global-w` | round-17 B① 把 `bool(_rc_dup_applied)` 收紧成 `(_rc_dup_applied is True)` | `SKILL.md:2213-2216` | **KILLED**，落在四格状态机的**④**（`不得再推进水位线`） |
| `M143-missing-applied-flag-tolerated` | 同上，「只拒 None」改成「不是 bool 就拒」 | `SKILL.md:2183` | **KILLED**，落在**①**（`旧条目缺事件级凭据 ⇒ 不可证，必须停`） |
| `M145-recovery-does-not-promote-flag` | 纯重构：那段 `sub()` 抽成了 `_promote_applied()` | `SKILL.md:2726`（**dup** 恢复调用点） | **KILLED**，落在**②**（`⛔ 恢复成功后必须把该条目升为 true`） |
| `M157-anchor-direction-unchecked`（**层**锚） | 多行布尔表达式合成了一行 | `SKILL.md:1997` | **KILLED**，落在 `⛔ 锚点指向后继 ⇒ 与账本自相矛盾, 必须停` |

⇒ 加上本来就绑好的 `M144`（落**③**），
`test_round16_fsrs_applied_across_all_branches` 的**四格状态机现在每格各有一条变异守着，
且逐条证明了它落在自己那一格**。Z6-C 那一轮这四条**什么都没测**。

## 六 三套 harness 的 EXPECT_MSG 与豁免表

| harness | 绑上 `EXPECT_MSG` | 进 `EXPECT_MSG_EXEMPT` | 合计 |
|---|---|---|---|
| g32b | **99** | **39** | 138 |
| g32cb | 9 | 0 | 9 |
| g32ccr1 | 11 | 0 | 11 |
| g33 | 18 | 0 | 18 |

### g32b 那 39 条豁免的分类（都由 `--probe` 的**实际拒因**分类，不是猜的）

| 类 | 条数 | 形态 | 根在哪 |
|---|---|---|---|
| ① | 21 | 断言消息**整体就是被测子进程的 stderr**（`assert X, r.stderr[:N]`）——门文件侧一个字面片段都没有 | 门文件的断言消息写法 |
| ② | 2 | 断言消息**求值为空串**，短摘要里只有 `AssertionError:` | 同上 |
| ③ | 2 | **无消息断言**，短摘要给的是 pytest 改写出来的**值**（`assert 1 == 0`）——那是值不是身份 | 同上 |
| ④ | 1 | 该变异让门以**未捕获异常**失败（`yaml.parser.ParserError`），根本没落在门里任何一条断言上 | 门覆盖面 |
| ⑤ | 1 | 断言消息**逐字抄自生产的报错文案**（`M76`，SKILL.md:331）——绑上去判据就能被生产输出喂饱 | 门文件；**由自检当场拦下**，不是事后补的 |
| ⑥ | **12** | 该门实际打红的那条断言，其消息首行的字面片段在门文件里**不唯一**（>1 次） | 门文件 |

⛔ 六类的根**全在门文件本体**（`backend/tests/**` 的 `git diff` 为空，本卡一个字没改）。
补上断言消息后这些条目就能从豁免表里去掉 —— 已在 §八「台账待登记条目」里移交。

### 自检本身的双向验伪锚（`expectmsg-selfcheck-falsifier-20260906T104055.txt`）

- **负向**：拿一个确实在生产里的串当 `expect_msg` → 自检报出两条问题（门文件里 16 次 ≠ 1、
  且生产文件里也有）⇒ 这道检查**看得见**它该看见的东西；
- **正向**：拿 g32cb M4 的正式 `expect_msg` → 无问题 ⇒ 它**不是恒报错**
  （恒报错会把整份表判死，比没有检查更糟）。
- 扫描面 526 个文件（`canvas-vault` + `backend/app` + `validate_learning_events.py`）。
  ⚠️ **不收 `backend/scripts/` 整目录** —— harness 自己在那儿、表里逐字写着这些片段，
  整目录扫会把「表里写了」误报成「生产里也有」（判据自指）。

---

## 六-B Codex round-1 外审与整改（绑定 `52f1ccd2`）

存档 `_bmad-output/审查/codex-review-CARD-DEBT-mutation-kill-identity.md`（10878 字节，非 0）。
**结论 FAIL；BLOCKER 0，3 HIGH + 4 MEDIUM + 2 LOW。** 按协议 §1「阻断级 = 0 即可合」，
Codex 的 FAIL 字样不进门；下面逐条如实处置。

### 已整改（5 条）

| 编号 | 外审判定 | 我的核实 | 处置 |
|---|---|---|---|
| MEDIUM-5 | `M13b` 的豁免理由不成立，门里有稳定片段可直接绑 | **成立**。该断言消息是 `"裸 \r 结尾在字节上无 LF ⇒ 应按截断隔离: " + r2.stdout + r2.stderr`（字符串拼接）；去掉含转义的开头后 `结尾在字节上无 LF ⇒ 应按截断隔离: ` 在门文件里恰 1 次 | 移出豁免表并绑定；豁免 40 → **39**，绑定 98 → **99** |
| HIGH-3 | 40 条豁免仍与「绑定断言击杀」并进同一个 `138/138`，说宽了 | **成立**。旧汇总只有一个 KILLED 数 | 新增裁决 `KILLED-UNBOUND`，汇总**分开报**：`99/138 绑定断言身份` + `39 仅证明指定门红了` + 一行明写「两者之和**不等于**全部被指定断言杀死」 |
| MEDIUM-4（部分） | `rc != 1` 被印成「SURVIVED ⇒ 假门」，把**负控自己坏了**说成**门不承重**，诊断指错方向 | **成立** | 新增裁决 `HARNESS-ERROR`（rc≠1 或判据面缺失），三套统一，单列计数 |
| MEDIUM-7 | `--list` 的退出码只看锚点；`EXPECT_MSG` 自检已打印错误却仍返回 0 | **成立**（g32cb/g32ccr1 早已把它计入，g32b 漏了） | `--list` 退出码同时取决于锚点与消息自检 |
| LOW-8 | 裸 `--only`（缺值）被静默忽略 → 退化成全量跑 | **成立** | 缺值 / 空前缀一律当场报错 `rc=4`；已实测两种形态都返回 4 |

### 登记不阻断（4 条，本卡不修，写清为什么）

| 编号 | 内容 | 为什么本卡不修 |
|---|---|---|
| **HIGH-1** | `expect_msg` 是**子串匹配**；若一条**前提断言**的消息首行内嵌了 `{r.stderr}`，而子进程运行期恰好拼出目标片段，则目标断言没红也会判 KILLED。Codex 用真实子进程复现 | **属实，是本卡判据的残余口径漏洞**。彻底修法是把身份从「消息片段」换成「断言的源位置」（`--tb=line` 的 `file:line`）—— 那是判据机制的**再设计**，会改变全部 4 套的判定路径，必须自带一轮独立复核；在本轮外审之后追加未经复核的新机制，正是本仓「修复链自我繁殖」踩过的形态。⇒ 移交下一张卡，**不在本卡声称已封堵** |
| **HIGH-2** | 解析器不限定 pytest 的**摘要区**，captured stdout 里的伪 `FAILED …` 行也会被 `parse_failed_nodeids()` 收录 | 同上，与 HIGH-1 同一处（判据面的取法），一并移交。⚠️ 该形态**旧 g33 也有**，不是本卡引入，但本卡把它抽成了共用件、扩到了四套 —— 如实登记 |
| **MEDIUM-6** | 单次信号若恰在 `finally` 已进入、快照写回**之前**到达，`_Terminated` 会中断剩余还原 | 属实。修法是还原期间屏蔽/延迟信号（`signal.pthread_sigmask`）—— 同属机制改动，移交。⚠️ 现有 `_self_heal_leftovers()` 在**下一次启动时**兜底（本卡已把它从「只扫主锚」扩到「主锚+同层锚」），不是完全裸奔 |
| **LOW-9** | PYEOF 提取的边界（`PYEOF_label` 提前截断 / 缺闭合标记 / `cat <<'PYEOF'` 的 YAML 被当 Python 编译） | Codex 明说是**构造输入**才可复现、当前变异未命中；且这是**继承自旧 g33** 的形态。移交 |

### 外审逐条驳回 / 收窄（1 条）

- Codex 说「先推导的名单不一致：脚本列 M142/M143/M145/M157，验收单说四格四条，实际包含 M144、不含 M157」。
  **这条是对的，我的表述确实含混**：先读源码推导的是 **5 条**——四格状态机的
  `M142/M143/M144/M145`（M144 本就绑好、不在更锚之列）**加上** `M157`（它绑的是另一道门
  `test_round17_anchor_direction_is_verified`，不属四格）。「四格四条」与「更锚四条」是
  **两个不同的四条**，重叠 3 条。§五.3 与 `EXPECT_MSG` 表头已按此更正。
- 「其余 91 条」也确实过时：`--probe` 观察到 134 条，减去四格里的 M144 与
  本轮新绑的 M13b 后，probe 派生的是 **94 条**（99 绑定 − 5 条源码推导）。已更正。

### ⛔ 整改未复审（协议 §1 必登记）

上述 5 条整改发生在**送审之后**，因此本卡最终状态与审 SHA `52f1ccd2` **已失绑**。
整改后重跑：g32cb `9/9 rc=0`、g32ccr1 `11/11 rc=0`、g33 `18/18 rc=0`（verdict 列仍与
Y1-A 收官逐字同）、g32b `99 绑定 + 39 未绑 = 138`、SURVIVED 0 / HARNESS-ERROR 0 /
ANCHOR-ERROR 0 / SYNTAX-INVALID 0。**这轮整改没有第二轮外审。**

## 七 本卡未证明什么

1. **门本体一个字都没改**（`backend/tests/**` 的 `git diff` 为空）。于是「门里那条断言
   **没有消息**」的条目只能进 `EXPECT_MSG_EXEMPT` —— pytest 短摘要给的是
   `assert 3 == 5` 这种**值**，换个 fixture 数据就变，不构成稳定身份。给这些断言补
   消息是门文件写者的事（Y6-B / Y7-A 的地盘），不是本卡。
2. **没有证明 `expect_msg` 对「同一条消息出现在多条断言里」的区分力**。判据只保证
   片段在门文件里**恰好 1 次**；两条不同变异绑到**同一条**断言（本卡里 g32ccr1 的
   E2/E6、E3/E9 就是）时，判据分不出是哪一条打红的。要分得开需要门本身给出更细的
   身份，属门文件面。
3. **g32b 大部分条目的 `EXPECT_MSG` 是「先观察后确认」而不是「先推导后验证」。**
   只有 g32cb 9 条、g32ccr1 11 条、以及 g32b 的 **5 条**（四格状态机的 M142/M143/M144/M145
   加上另一道门的 M157），是先读门源码推出「会先撞上哪条断言」再写的；
   本轮整改又按外审补绑了 M13b（读源码确认）。其余 **94 条**是先跑一次 `--probe`（不做判定、rc 恒 4）拿实际拒因，再逐条
   对着变异意图确认后回填。⛔ **这意味着本卡这一次的 g32b 全绿证不出多少东西**
   （判据与被测量同源）；它的价值在**从今往后**：门或生产代码一漂移，击杀落到别的断言上
   就会立刻报 SURVIVED，而不是像过去那样静默记成 KILLED。
4. **M100 / M151 的「层声明过度 → 降普通变异」不在本卡范围**，只登记（Z6-C 移交项，
   本卡卡文明确排除）。
5. **没有在主干版 SKILL.md（2915 行）上重跑**。本卡全部结论是**车道树**（Z2 版，
   3076 行，sha `63b51029…`）上的。合并后主干若与车道树不同，锚点与 `EXPECT_MSG`
   都要重验。
6. **g32b 全量只跑一次（外加一次 `--probe`），没有做时序复现**。「这次全 KILLED」
   不排除偶发性（并发/时序敏感的门在别的负载下可能给出不同结果）。
7. **`syntax_check()` 的 `.md` 分支只覆盖 PYEOF 块**。SKILL.md 里若有别的形态的
   可执行块（不是 `<<'PYEOF'` heredoc），编译自检看不见它 —— 本卡实测两个 SKILL.md
   里没有这种形态，但那是**今天的事实**，不是代码不变量。
8. **没有证明「变异体编译得过」等于「变异真的生效」**。编译自检只排除「编译期就死」
   这一类假杀；「锚落在注释上、AST 完全没变」那一类（g32cb `_anchor_audit` docstring
   自陈的已知盲区）本卡没堵，仍属另立卡。

## 八 台账待登记条目

> 台账 `未合卡追踪台账.md` 只有主 session 改；以下是本卡请求登记的内容。

1. **Z6-C 行（`e6d74ae6`）的 4 条 ANCHOR-ERROR 终态**：`M142-dup-uses-global-w` /
   `M143-missing-applied-flag-tolerated` / `M145-recovery-does-not-promote-flag`
   三条**主锚**、`M157-anchor-direction-unchecked` 一条**层锚** —— 本卡**全部更锚**
   到现址（车道树 `grep -c` 均为 1），**无退役**。锚点现址与更锚理由逐条写在
   `g32b_mutation_gates.py` 的行内注释里。
2. **g32b 缺 SIGTERM handler** —— 已补（`SIGTERM` / `SIGINT` / `SIGHUP`，与
   `g32cb:246-251` 同形）；并把启动自愈从「只扫主锚」扩到「主锚 + 同层锚」。
3. **三套 N/N 变化表** —— 见本验收单 §五。
4. **新模块路径** `backend/scripts/mutation_kill_identity.py`（四套 harness 共用的
   击杀身份判据 + 变异体编译自检）。
5. **移交 Y4**：`g32ccr1_negative_controls.py` 不在 `lefthook.yml:303-305`
   `mutant-residue-scan` 的允许名单里（`:305` 只放行 `_bmad-output/*`）。本卡因此
   刻意**没有**在 g32ccr1 里新增任何含该标记字面量的行；但这条名单缺项本身还在，
   `lefthook.yml` 是 Y4 的地盘。
6. **移交门文件写者（Y6-B / Y7-A 面）**：`test_g3_2_review_ledger.py` 里被本卡绑到的
   若干**无消息断言**（进了 `EXPECT_MSG_EXEMPT`）建议补上断言消息，补完后这些条目
   就能从豁免表里去掉。
7. **Codex 轮次**：CARD-DEBT-mutation-kill-identity round-1（`gpt-6-astra` / `ultra` /
   `codex-cli 0.153.3`），绑 `52f1ccd2`，非 0 字节，存档首部已按协议 §2.1 补齐。
   判 FAIL、**BLOCKER 0**；5 条已整改、4 条登记不阻断。⛔ **整改未复审**（整改在
   送审之后，与审 SHA 失绑，无第二轮）。卡族轮次：本卡用 1 轮。
8. **移交下一张卡（判据机制再设计）**：Codex HIGH-1 / HIGH-2 / MEDIUM-6 —— 把击杀
   身份从「消息片段子串」换成「断言的源位置」+ 限定 pytest 摘要区 + 还原期间屏蔽信号。
   ⚠️ HIGH-2 与 LOW-9 的形态**旧 g33 本就有**，不是本卡引入，但本卡把它抽成共用件
   后扩到了四套 —— 如实登记。
9. **本卡两个 commit**：`52f1ccd2`（送审态）+ `cd10021e`（整改态），均**未 push**。
10. **新暴露（不阻断）**：g32ccr1 的 E3 / E9 实际都落在
   `test_g32ccr1_charset_scope_is_bounded_by_ledger_record_reality` 的 ⓪「严格表逐项
   钉死」那条断言上，而不是脚本 docstring 声称的 ③「死条目」判据 —— ③ 那条
   **当前没有任何变异为它承重**。
