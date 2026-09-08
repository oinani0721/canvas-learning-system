# UAT — CARD-DEBT-mutkill-R2（击杀身份绑「断言源位置」+ 判据面限定摘要区）

> 批次 `[BATCH-2026-09-07-第十三批 / CARD-DEBT-mutkill-R2]` · 车道 `card-u8-mutgates`（分支 `card/u8-mutgates`）
> 卡文 `_bmad-output/implementation-artifacts/goal-cards/第十三批-goals/U8-B.md`
> 证据目录 `_bmad-output/审查/evidence-mutkill-r2/`

---

## 1. 🎯 一句话目标

那四套「自己给自己找茬」的自检工具，以前**只要输出里出现过那句话就算数**；现在必须是**它指名的那一处真的报错**才算，而且中途被打断也一定把文件还原回去。

## 2. 📖 你的视角

作为这个项目的主人，我想让「我们已经验证过了」这句话**真的有分量** —— 以便下次有人说「这道防线是有效的」时，那句话背后不是自己给自己开的证明。

## 3. 🖥️ 交互流程

这张卡不改你会碰到的任何界面。它改的是**开发期的自检工具**：

```
以前： 工具跑一遍 → 看到「那句话出现了」→ 记「杀死」✅（可能是别处报的错）
现在： 工具跑一遍 → 看它指名的**那一行**是不是真的报错了 → 才记「杀死」
      中途按 Ctrl-C / 被系统打断 → 文件一定还原回原样（以前可能还原一半）
```

---

## 4-A. 🤖 Claude 已代验（技术）

> 全部命令与末行 rc 见证据目录；本节只引用路径与结论，不自述数字。

| # | 裁判 | 证据文件 | 结论 |
|---|---|---|---|
| 1 | 第 0 分钟 + 全目标 sha 基线 | `sha-targets-pre-<ts>.txt` / `sha-superset-pre-<ts>.txt` | ✅ `pwd`/分支 `card/u8-mutgates`/`HEAD=3f073a1a`(U8-A 末 commit)/`git status --porcelain` 空；8 个目标文件全文件 sha 落盘，其中卡文点名的三个（`fsrs_bridge.py` `a766fbcc…` / `decay_beta.py` `3bf4ed94…` / `quiz-answer/SKILL.md` `63b51029…`）与卡文声称值**逐字相同** |
| 1b | 变异写入面**实测**枚举（不靠卡文枚举） | `count-mutations-pre-<ts>.txt` / `resolve-targets-<ts>.txt` | ✅ 但**与卡文枚举不符，以实测为准**：变异写入面实测是 **6 个**文件（卡文只点名 3 个），多出 `backend/scripts/validate_learning_events.py`、`backend/app/services/learning_event_log.py`、`canvas-vault/.claude/skills/start-exam-board/SKILL.md`、`docs/learning-events-schema-v1.md`。全部在车道树内、**无一**落在 live vault。⚠️ 我的第一版枚举脚本按裸 `Name` 取路径，**同时**漏了真目标又报出一个假越界；改成「逐个元组元素整体求值」后才对 |
| 2 | 三套 `--list` rc=0 + g33 `--selfcheck-syntax` rc=0 | `list-g32b-*.txt` / `list-g32cb-*.txt` / `list-g32ccr1-*.txt` / `selfcheck-g33-*.txt` / `list-g33-unrecognized-*.txt` | ✅ g32b/g32cb/g32ccr1 `--list` 均 **rc=0**（138 / 9 / 11 条，异常锚点 0）；g33 传 `--list` → argparse unrecognized **rc=2**，⛔ 未当成通过；g33 `--selfcheck-syntax` **rc=0**（含两条验伪锚：新 M15 串通过、未变异原文通过）。回填 `EXPECT_LOC` 后 g32b `--list` 复跑 **rc=0**（EXPECT_LOC 137 + 位置豁免 1） |
| 3 | 独立计数（`ast.parse`，不 import） | `count-mutations-pre-<ts>.txt` | ✅ `ast.parse` 独立脚本（不 import 被测模块）数得 **138(=99+39) / 9(9+0) / 11(11+0) / 18**，与三套 `--list` 自报**互证一致**；⚠️ g33 的 18 条**只有单来源**（它没有 `--list`，`--selfcheck-syntax` 不报条数） |
| 4 | N1 / N2 两条负控 + P1 正控 + D 段 | `negctl-n1n2-<ts>.txt` | ✅ 四段全 PASS。N1（前提断言把子进程 stderr 插进消息首行）：旧版 `True`(放行) / 新版 `SURVIVED`（理由：位置不符，期望 `stmt:12afc6f73656` 实见 `stmt:59d814720c52`）。N2（captured 区伪 `FAILED` 行）：旧版 `True` / 新版 `SURVIVED`（理由落在**摘要区消息**这一层 —— 这是它要测的那一层）。P1 正控（目标断言真的红了）：两版都 `KILLED`。D 段：不带 `--show-capture=no` 时伪造行出现在输出里=True，带上=False |
| 5 | 信号负控（还原期打断） | `negctl-signal-<ts>.txt` | ✅ naive 对照（收口前写法）留下 **3/5 个未还原**（`target_2/3/4.txt`）⇒ 负控承重；guarded **0 未还原 + rc=130**；`RESTORE_SIGNALS` 实测含 `SIGQUIT` |
| 5b | 信号还原的**现场**检验（非计划内） | `signal-restore-live-check-<ts>.txt` | ✅ **在真生产文件上**：`--probe` 跑到一半时对 python 进程发 SIGTERM，`RestoreGuard` 先还原再退出，8 个目标文件**逐字节**回到基线。⚠️ 这一跑是非计划内的（我先误 kill 了 shell 包装进程，python 继续跑），如实记录 |
| 6 | PYEOF 等价性 + 三洞负控 + 两验伪锚 | `pyeof-negctl-<ts>.txt` | ✅ 两个真实 SKILL.md（quiz-answer 2 块 / start-exam-board 3 块）新旧正则提取**逐块逐字节相同**（收紧不丢覆盖面）；三洞负控 PASS；两条验伪锚 PASS —— 其中「终止行带尾随空格」这一条**正是我初稿写错的断言**，保留作验伪锚 |
| 7 | 四套全跑（串行，**v2 = 代码定稿后**；v1 存档 `run-*-2026-09-08T09*.txt` 早于定稿已作废） | `run-g32b-20260908T115653.txt` / `run-g32cb-20260908T123027.txt` / `run-g32ccr1-20260908T123409.txt` / `run-g33-20260908T123836.txt` | ✅ **g32b：KILLED 131 / KILLED-UNBOUND 3 / SURVIVED 0 / HARNESS-ERROR 4 / ANCHOR-ERROR 0 / SYNTAX-INVALID 0，六档之和 138 ✓，rc=2**；g32cb **9/9 KILLED**（rc=0，和=9 ✓）；g32ccr1 **11/11 KILLED**（rc=0，和=11 ✓）；g33 **18/18 KILLED**（rc=0，和=18 ✓，还原逐字节+标记扫描双绿）。⚠️ g32b 的 3 条 UNBOUND 与 4 条 HARNESS-ERROR 全部**登记不改判据**：UNBOUND = M97（失败落在 yaml 库里）+ M89/M90（位置锚在前置 setup 断言上，复核抓到后主动收回）；HARNESS-ERROR = M10/M18b/M120/M125 四条**假杀暴露**——空变异对照改按**位置**比对后「只加层那趟已红在同一条断言」再也藏不住（旧文本比对被 stderr 尾巴差异掩护；复核验证者用 v1 存档独立坐实 M18b/M120/M125 三条）。另两条 complete 层债（M100/M151「变异体单独即可杀 ⇒ 撤层」）仍在 failures。⛔ 这 6 条层债的**变异重设计**移交下一批，本卡判据只负责把它们照出来 |
| 8 | 六档收口前后对照（含 g33 的验伪锚） | `six-verdicts-before-after-<ts>.txt` | ✅ g33 收口前 `ANCHOR-ERROR=0`（只有 `ANCHOR-DRIFT`）/ `KILLED-UNBOUND=0` / `HARNESS-ERROR=0`；收口后 **3 / 1 / 2**，三个方向都由 0 变正 —— 这就是它自己的验伪锚。⚠️ 「收口前」一列取自 `git show 3f073a1a:<file>`（收口前的状态就是那个 commit），不是另跑一次 |
| 9 | 统一性结构判据（VERDICTS / judge_flags / RestoreGuard） | `unification-audit-<ts>.txt` | ✅ 四套均 `from mutation_kill_identity import VERDICTS` 且 `for v in VERDICTS` 算汇总；四套均走 `judge_flags()`，**残留的手写 pytest 开关 0 行**；四套均 `RestoreGuard(`，**自写 `signal.signal(` 0 处** |
| 10 | 跑后 sha + 标记残留 | `sha-targets-post-<ts>.txt` / `marker-post-<ts>.txt` | ✅ 8 个目标文件跑后 sha 与跑前**逐字节相同**；标记文件清单仍是那 5 项；⚠️ `g32b_mutation_gates.py` 计数 **153 → 151**，差额 2 已逐行归因：本卡 diff 里含该标记的**删除行 2 / 新增行 0**，两行都是 `_restore_one` docstring 里的**注释**，与变异体文本无关。⚠️ 卫生判据收紧：`grep -c stderr` 会命中别的卡留下的 `census-stderr.txt`（口径比它的主张宽），改精确判据 `grep -cE '\.stderr'` → 已跟踪 **0** / 工作树未跟踪 **0** |
| 11 | `tests/unit` 对基线 diff（只许 `<`） | `unit-before-*.txt` / `unit-after-*.txt` / `unit-diff-*.txt` | ✅ `unit-after` 对主干基线 `unit-red-baseline-da690bf8.txt` diff **完全为空**（`>` 行 0 条）。⚠️ `unit-before` 曾出现 **202=202 但一增一减**（`test_candidate_service.py::test_accept_candidate_already_accepted_returns_422` 新红 / `test_mock_mode_logs_warning` 转绿）；两条硬证据表明与本卡无关：① `tests/unit` 里 **0 个文件**加载本卡改的任何脚本；② `unit-after` 第二个样本上该差异**未复现** |
| 12 | `tests/regression` 开工 / 收工 | `regression-before-*.txt` / `regression-after-*.txt` | ✅ 开工 / 收工失败集**完全一致**（两次都是 `1464 passed, 6 skipped, 10 xfailed`，0 failed，`NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0`） |
| 13 | U8-A 的两道门仍在 | `ast-gate-*.txt` / `guard-probes-*.txt` | ✅ `AST-GATE: PASS (0 violations in 391 files)`；`GUARD-PROBES: PASS — 54/54 条全部 fail-closed` |
| 14 | 地盘 / 卫生 | `scope-*.txt` | ✅ `git diff --stat --no-color 3f073a1a -- . ':(exclude)_bmad-output'` 恰好 **5 个 `backend/scripts/*.py`**（+1227/−262），无 `canvas-vault/**`、无第 6 个文件（U7 的 `ast-must-flag.patch` 未交来，未套用） |
| 15 | **N3/N4/P2 第三方存证负控**（复核抓到的回归） | `negctl-thirdparty-<ts>.txt` | ✅ N3 无第三方改动时：旧版**伪告警 + 伪存证**（存下来的是原文），新版静默 no-op；N4 有第三方改动 T 时：旧版把 T 覆盖掉、存下的是原文（T 丢失），新版存证内容**逐字节等于 T**；P2 正控：不发信号只走 `finally` 时新版仍存证真实 T；验伪锚：新旧两份实现字节码不同 |
| 16 | 作用域遍历改写等价性 | `scope-walk-rewrite-<ts>.txt` | ✅ 指纹表键集合与每键行号多重集**完全相同**（3175 键，137 条 `EXPECT_LOC` 仍有效）；覆盖面由「手写容器枚举」改为「父链推作用域」后**恒等于 `ast.walk`**（3396=3396），`match` 的 `cases` 不再漏 |

## 4-B. 👤 你来验

- [ ] 我打开这份验收单 → 我看到「以前只要那句话出现过就算数，现在必须是它指名的那一处真的报错」→ 我感觉**这条规则我能复述给别人听**。
- [ ] 我在第 5 节读到「本卡未证明什么」→ 我看到里面明写了「另外三套还没绑到这个强度，已经排进下一批」→ 我感觉**没有被含糊过去**。
- [ ] 我看第 6 节那张表 → 我看到 39 条里每一条都写了「绑了」还是「保留」以及为什么 → 我感觉**没有哪一条被悄悄消失**。

---

## 5. 🚦 验收结果

**通过 —— 阻断级 = 0。**

| 阻断级项 | 结论 |
|---|---|
| 数据丢失 | 无：8 个目标文件跑前跑后逐字节相同（含一次真实 SIGTERM 打断后的还原） |
| live vault / Neo4j 7691 写入 | 无：变异写入面实测全部在车道树内；`tests/regression` 两跑 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0` |
| 安全 | 不适用（改的是开发期自检工具） |
| 指定裁判红 | 无：四套六档之和全部对上（138/9/11/18），SURVIVED 全 0；g32b rc=2 是**登记过的层债**（卡文 (j) 明示「实测为准、如实登记」），非门失效 |
| 负控假绿 | 无：五条负控（N1/N2/P1/D、信号、PYEOF）全部带**承重对照**——naive 留下 3 个未还原、旧版判据放行两条负控输入、旧正则漏掉整块 |

**登记不阻断（全部有存档、逐条可查）**：① g32b 4 条 HARNESS-ERROR = 假杀暴露（M10/M18b/M120/M125），是判据收紧后**照出来**的存量变异设计债，不是门或判据的缺陷；② 3 条 KILLED-UNBOUND（M97/M89/M90，各有实测理由）；③ 2 条 complete 层债（M100/M151 撤层）。六项合计 9 条全部移交下一批的变异重设计，⛔ 未为了好看改判据——v1 的「137/138 KILLED」里混着这 4 条假杀，那个数字才是错的。

---

## 6. 39 条逐条处置表 / 四套分档对照表

## 39 条 KILLED-UNBOUND 逐条处置表

> 来源：`g32b_mutation_gates.py` 的四张表按 AST 实读（EXPECT_MSG 99 / EXPECT_MSG_EXEMPT 39 / EXPECT_LOC 135 / EXPECT_LOC_EXEMPT 3）。

> 「收口前」= 消息绑不出来 ⇒ 判据退化成旧口径「指定门红了」= `KILLED-UNBOUND`。
> 「收口后」= 位置绑上了就是 `KILLED`（绑定维度只有位置，没有消息）。

| # | 变异 tag | 消息为什么绑不出来（原豁免理由，节选） | 处置 | 位置身份 |
|---|---|---|---|---|
| 1 | `M10-R2-value-not-literal` | ① 该门此处断言的消息**整体就是被测子进程的 stderr**(`assert X, r.stderr[:N] | **绑（位置）** | `stmt:c8e430b5ce69` |
| 2 | `M102-receipt-attempt-type-only` | ① 该门此处断言的消息**整体就是被测子进程的 stderr**(`assert X, r.stderr[:N] | **绑（位置）** | `stmt:4a06447ea2ed` |
| 3 | `M117-empty-source-skips-provenance` | ① 该门此处断言的消息**整体就是被测子进程的 stderr**(`assert X, r.stderr[:N] | **绑（位置）** | `stmt:9ca250d2cb86` |
| 4 | `M12-N1-drop-out-of-order-shape-gate` | ① 该门此处断言的消息**整体就是被测子进程的 stderr**(`assert X, r.stderr[:N] | **绑（位置）** | `stmt:35b14b243932` |
| 5 | `M129-missing-scored-at-warn-only` | ① 该门此处断言的消息**整体就是被测子进程的 stderr**(`assert X, r.stderr[:N] | **绑（位置）** | `stmt:6493eeda8b37` |
| 6 | `M14-N3-drop-duplicate-key-hook` | ① 该门此处断言的消息**整体就是被测子进程的 stderr**(`assert X, r.stderr[:N] | **绑（位置）** | `stmt:c36b63813880` |
| 7 | `M140-bare-collision-no-own-judge` | ⑥ 该门实际打红的那条断言, 其消息首行的字面片段在门文件里不唯一(出现 >1 次), 绑上去就不能证明红在哪一 | **绑（位置）** | `stmt:a6f9e6ddb8bb` |
| 8 | `M15b-N4-decode-with-replace` | ① 该门此处断言的消息**整体就是被测子进程的 stderr**(`assert X, r.stderr[:N] | **绑（位置）** | `stmt:839c95da5e9d` |
| 9 | `M16-N5-hard-compute-attempt-across-pending` | ① 该门此处断言的消息**整体就是被测子进程的 stderr**(`assert X, r.stderr[:N] | **绑（位置）** | `stmt:6105a6838306` |
| 10 | `M20-B1-drop-gradenorm-completeness` | ① 该门此处断言的消息**整体就是被测子进程的 stderr**(`assert X, r.stderr[:N] | **绑（位置）** | `stmt:029dbd458414` |
| 11 | `M23-C1-drop-event-type-gate` | ⑥ 该门实际打红的那条断言, 其消息首行的字面片段在门文件里不唯一(出现 >1 次), 绑上去就不能证明红在哪一 | **绑（位置）** | `stmt:8b4fc14dc10c` |
| 12 | `M24-C1-drop-concept-id-gate` | ⑥ 该门实际打红的那条断言, 其消息首行的字面片段在门文件里不唯一(出现 >1 次), 绑上去就不能证明红在哪一 | **绑（位置）** | `stmt:8b4fc14dc10c` |
| 13 | `M25-C1-drop-vault-id-gate` | ⑥ 该门实际打红的那条断言, 其消息首行的字面片段在门文件里不唯一(出现 >1 次), 绑上去就不能证明红在哪一 | **绑（位置）** | `stmt:8b4fc14dc10c` |
| 14 | `M26-C2-drop-eid-whitespace-gate` | ② 该门此处断言的消息**求值为空串**, 短摘要里只有 'AssertionError:'  | **绑（位置）** | `stmt:fbbc07945c4f` |
| 15 | `M29-R3-drop-event-version-gate` | ① 该门此处断言的消息**整体就是被测子进程的 stderr**(`assert X, r.stderr[:N] | **绑（位置）** | `stmt:060ef934e40c` |
| 16 | `M2b-R2-drop-utc-offset-check` | ① 该门此处断言的消息**整体就是被测子进程的 stderr**(`assert X, r.stderr[:N] | **绑（位置）** | `stmt:c8e430b5ce69` |
| 17 | `M30-R3-drop-two-instant-consistency` | ① 该门此处断言的消息**整体就是被测子进程的 stderr**(`assert X, r.stderr[:N] | **绑（位置）** | `stmt:29076bdbfb99` |
| 18 | `M31-R3-drop-attempt-required` | ① 该门此处断言的消息**整体就是被测子进程的 stderr**(`assert X, r.stderr[:N] | **绑（位置）** | `stmt:3a5f92ec3335` |
| 19 | `M32-R3-drop-payload-object-gate` | ① 该门此处断言的消息**整体就是被测子进程的 stderr**(`assert X, r.stderr[:N] | **绑（位置）** | `stmt:018880e4697d` |
| 20 | `M38b-attempt-expectation-masked-by-max` | ① 该门此处断言的消息**整体就是被测子进程的 stderr**(`assert X, r.stderr[:N] | **绑（位置）** | `stmt:cca8c7fef0f3` |
| 21 | `M45-allow-dup-and-foreign-same-round` | ① 该门此处断言的消息**整体就是被测子进程的 stderr**(`assert X, r.stderr[:N] | **绑（位置）** | `stmt:fbde4102f5f1` |
| 22 | `M47-skip-validator-record-check` | ⑥ 该门实际打红的那条断言, 其消息首行的字面片段在门文件里不唯一(出现 >1 次), 绑上去就不能证明红在哪一 | **绑（位置）** | `stmt:4833e323c049` |
| 23 | `M49-event-version-accepts-bool` | ⑥ 该门实际打红的那条断言, 其消息首行的字面片段在门文件里不唯一(出现 >1 次), 绑上去就不能证明红在哪一 | **绑（位置）** | `stmt:54141b83b77e` |
| 24 | `M5-R5-drop-rating-consistency` | ① 该门此处断言的消息**整体就是被测子进程的 stderr**(`assert X, r.stderr[:N] | **绑（位置）** | `stmt:5a01df2235e9` |
| 25 | `M50-non-object-line-silently-skipped` | ⑥ 该门实际打红的那条断言, 其消息首行的字面片段在门文件里不唯一(出现 >1 次), 绑上去就不能证明红在哪一 | **绑（位置）** | `stmt:54141b83b77e` |
| 26 | `M51-line-strip-washes-nonjson-whitespace` | ⑥ 该门实际打红的那条断言, 其消息首行的字面片段在门文件里不唯一(出现 >1 次), 绑上去就不能证明红在哪一 | **绑（位置）** | `stmt:4833e323c049` |
| 27 | `M58-input-ts-not-literally-checked` | ⑥ 该门实际打红的那条断言, 其消息首行的字面片段在门文件里不唯一(出现 >1 次), 绑上去就不能证明红在哪一 | **绑（位置）** | `stmt:6be363a3f232` |
| 28 | `M61-durable-eid-whitespace-not-scanned` | ① 该门此处断言的消息**整体就是被测子进程的 stderr**(`assert X, r.stderr[:N] | **绑（位置）** | `stmt:6cee3c61a23a` |
| 29 | `M65-loads-allows-nan` | ① 该门此处断言的消息**整体就是被测子进程的 stderr**(`assert X, r.stderr[:N] | **绑（位置）** | `stmt:4d0254dfdb35` |
| 30 | `M75-w-fallback-restored` | ⑥ 该门实际打红的那条断言, 其消息首行的字面片段在门文件里不唯一(出现 >1 次), 绑上去就不能证明红在哪一 | **绑（位置）** | `stmt:66f7e7eef6ad` |
| 31 | `M76-self-node-id-gate-dropped` | ⑤ 该门此处断言的消息**逐字抄自生产的报错文案**(`SKILL.md:331` 的 `写出去的事件将永远路由 | **绑（位置）** | `stmt:cca6ed1276e8` |
| 32 | `M77-ordinal-fixed-minus-one` | ⑥ 该门实际打红的那条断言, 其消息首行的字面片段在门文件里不唯一(出现 >1 次), 绑上去就不能证明红在哪一 | **绑（位置）** | `stmt:df0f8fdcce4a` |
| 33 | `M79-missing-scored-at-falls-back` | ① 该门此处断言的消息**整体就是被测子进程的 stderr**(`assert X, r.stderr[:N] | **绑（位置）** | `stmt:4b52b515653f` |
| 34 | `M81-legacy-out-of-order-honored` | ⑥ 该门实际打红的那条断言, 其消息首行的字面片段在门文件里不唯一(出现 >1 次), 绑上去就不能证明红在哪一 | **绑（位置）** | `stmt:7841011453a9` |
| 35 | `M89-receipt-drops-scored-at` | ③ 该门此处是**无消息断言**, 短摘要给的是 pytest 改写出来的值(如 'assert 1 == 0' | **保留 UNBOUND** | ⓒ 实测位置落在门 `test_round9_structured_receipt` 的**第 1/14 条 assert**(`asser |
| 36 | `M9-6cell-cell2-drop-orphan-noop` | ② 该门此处断言的消息**求值为空串**, 短摘要里只有 'AssertionError:'  | **绑（位置）** | `stmt:5ad5a11505d6` |
| 37 | `M90-receipt-drops-attempt` | ③ 该门此处是**无消息断言**, 短摘要给的是 pytest 改写出来的值(如 'assert 1 == 0' | **保留 UNBOUND** | ⓒ 实测位置落在门 `test_round9_structured_receipt` 的**第 1/14 条 assert**(`asser |
| 38 | `M91-f1-only-unconditional-noop` | ① 该门此处断言的消息**整体就是被测子进程的 stderr**(`assert X, r.stderr[:N] | **绑（位置）** | `stmt:1f2e99d5342c` |
| 39 | `M97-writeback-regex-only` | ④ 该变异让门以**未捕获异常**失败(yaml.parser.ParserError), 而不是落在门里任何一 | **保留 UNBOUND** | ⓐ 该变异让门在**门文件之外**失败(实见 file:parser.py), 只能绑到文件级弱身份; 按 check_expect_loc |

**小计**：39 条中 **36 条改绑位置身份**（`KILLED-UNBOUND` → `KILLED`），**3 条仍保留 UNBOUND**（逐条理由见上表右列），**退役 0 条**。
退役 0 条的理由：位置身份把「门文件里没有可绑的**字面片段**」这个障碍整体绕开了 —— 消息绑不出来的那些条目，位置照样绑得出来，所以没有一条需要靠删掉来收口（删掉就是减覆盖，且要说明谁接管它守的规则）。

## 四套分档对照表（收口后）

| 套 | 变异条数 | 六档是否齐全 | expect_msg | expect_loc | 信号 | pytest 开关 |
|---|---|---|---|---|---|---|
| `g32b` | 138 | ✅ 从 `VERDICTS` 取 | 99 条 | ✅ 135 条 (+3 豁免) | ✅ RestoreGuard(4 信号 + 还原期屏蔽) | ✅ judge_flags() |
| `g32cb` | 9 | ✅ 从 `VERDICTS` 取 | 9 条 | — (D-28 移交十四批) | ✅ RestoreGuard(4 信号 + 还原期屏蔽) | ✅ judge_flags() |
| `g32ccr1` | 11 | ✅ 从 `VERDICTS` 取 | 11 条 | — (D-28 移交十四批) | ✅ RestoreGuard(4 信号 + 还原期屏蔽) | ✅ judge_flags() |
| `g33` | 18 | ✅ 从 `VERDICTS` 取 | 18 条 | — (D-28 移交十四批) | ✅ RestoreGuard(4 信号 + 还原期屏蔽) | ✅ judge_flags() |
### 8 组共用同一断言位置（合法，但登记）

| 位置指纹 | 共用它的变异 | 其中没有 `expect_msg` 的 |
|---|---|---|
| `stmt:4833e323c049` | M47, M51 | **两条都没有** |
| `stmt:54141b83b77e` | M49, M50 | **两条都没有** |
| `stmt:66f84ab960c6` | M52, M53 | — |
| `stmt:8b4fc14dc10c` | M23, M24, M25 | **三条都没有** |
| `stmt:c8e430b5ce69` | M10, M2b | **两条都没有** |
| `stmt:d86d7cf272eb` | M35, M36b, M43 | — |
| `stmt:f2650d485101` | M68, M69 | — |
| `stmt:f4a6fae948f0` | M89, M90 | **两条都没有** |

⇒ **5 组（12 条）位置与消息都分不开彼此**。这不影响「红在声称的那条断言上」这个结论（每条变异**单独施加**，谁触发的在运行期不含糊），但它意味着：若某条变异意外走到了它**兄弟条目**的缺陷路径上，本判据看不出来。已写进第 9 节 #13。


---

## 7. 跑前跑后 sha 对账

跑前基线 `sha-targets-pre-20260908T073501.txt`（8 个文件，名单由 `count_mutations.py` 从 `MUTATIONS` 表**实测**取，不靠卡文枚举）；跑后对账 `finalize-v2-<ts>.txt` 第一段（v2 全跑后）。

```
8dc761f8…  backend/app/services/learning_event_log.py
45c77229…  backend/scripts/validate_learning_events.py
a52c7731…  backend/tests/regression/test_g3_2_review_ledger.py
3bf4ed94…  canvas-vault/.claude/scripts/decay_beta.py          ← 零写者，与 live 逐字节同
a766fbcc…  canvas-vault/.claude/scripts/fsrs_bridge.py         ← 零写者，与 live 逐字节同
63b51029…  canvas-vault/.claude/skills/quiz-answer/SKILL.md    ← U5-B 的地盘，复跑锚点
1ec5dd95…  canvas-vault/.claude/skills/start-exam-board/SKILL.md
43ac9e61…  docs/learning-events-schema-v1.md
```

`diff` 跑前 / 跑后 = **空**。中途另有两次核对（只读入口跑完、SIGTERM 打断后）同样为空。

**标记残留**：文件清单仍是那 5 项；计数 `153/11/11/2/13` → `151/11/11/2/13`，唯一差额已在第 4-A #10 逐行归因。

---

## 8. 集成树复跑待办（等 U5-B）

`canvas-vault/.claude/skills/quiz-answer/SKILL.md` 的**唯一写者是 U5-B**（`CARD-G3-3-R2-writer-boundary`）；它改 `_append_calibration` 等段落后，**g32b 的 168 处 SKILL 锚点会漂**。
**集成树复跑由 U8-B 在主 session 通告「U5-B 已进候选树」之后做**；本卡在车道树上的数字**不代表集成态**。
复跑时先比对这个锚：本卡实测 `SKILL.md` sha256 = `63b51029ea96a78abd757902023f378697688c28db1b8dc0aaee8969e9ee48e8`（3076 行）。变了就说明 U5-B 动过，锚点表要先重跑 `--list`。

---

## 9. 本卡未证明什么

1. **不改任何门本体**（被变异的那些真门都是只读的，`backend/tests/**` 的 diff 为空）⇒ 本卡不证明「门本身守得住它声称的性质」，只证明「变异被判成什么」。
2. **`EXPECT_LOC` 的 138 个值是 `--probe` 观察后回填的**（判据与被测量同源）⇒ 今天**证不出**「每条变异确实红在它声称的那条断言上」。它的价值在**从今往后**：门或生产代码一漂移、击杀落到别的语句上就当场报出来。这与现有 91 条 `EXPECT_MSG` 的来路完全同型。
3. **不证明 `expect_loc` 在所有 pytest 版本 / 插件组合下稳定**。本卡的全部形态实测只在 **pytest 9.0.2** 上做过；`--tb=line` 位置行的格式、captured 区的位置、摘要分隔线文本都可能随版本变。
4. **按用户裁定 D-28 收窄**：本卡**不给** `g32cb`(9) / `g32ccr1`(11) / `g33`(18) 三套加 `expect_loc`，它们的击杀身份仍靠 `expect_msg` + 「失败位置须在门文件里」这道弱判据 ⇒ **不证明这三套已绑到断言源位置**；⛔ 尤其：**弱位置判据挡不住 Y1-B HIGH-1**（前提断言与目标断言同在门文件里，位置粒度到文件为止分不开）。该项登记第十四批尾巴卡。
5. **(e) 两条负控只覆盖 Codex 点名的两种形态**（stderr 喂饱 / captured 伪 FAILED 行），**不证明**不存在第三种喂饱判据的形态。
6. **M100 / M151 之类的层债未解**，实测结果如实登记在第 4-A 与第 6 节，⛔ 没有为了好看改判据。
7. **(j) 的数字是车道树快照**；集成树（含 U5-B 改后的 SKILL.md）**未复跑**（第 8 节）。
8. **(h) 的信号负控只在临时目标文件上做**；对真的 `canvas-vault/**` 只有一次**非计划内**的现场检验（第 4-A #5b），**不证明**真实中断时序下的所有情形。⛔ `SIGKILL` / `SIGSTOP` 不可捕获，被 `-9` 打断时变异体会留在文件里 —— 只能靠下一次启动的自愈 + 全文件 sha 对账发现。
9. **(g) 的六档统一只证明「四套的字段名与计数口径一致、且六档之和 = 变异条数」**，**不证明**每一档的判定在所有输入形态下都正确。尤其 `ANCHOR-ERROR` 与 `SURVIVED` 的边界：锚点命中数为 1 但替换后语义未变，仍会被记成 SURVIVED。
10. **不跑** `tests/integration` / `tests/e2e`；**不连** 7691 / 7687；**不动** live vault。
11. **`--show-capture=no` 的代价如实说**：SURVIVED 诊断时不再能看到被测子进程的原文，要人工重跑一次才看得到。
12. **`check_expect_msg_unique` 的生产侧扫描面从 `rglob` 改成 `os.walk(onerror=...)`** 只证明「枚举失败现在会被报出来」，**不证明**本树上此前真的发生过枚举失败（本树实测 0 次）。
13. **有 8 组变异共用同一条断言位置；其中 5 组（共 12 条）位置与消息都分不开彼此**（`M23/M24/M25`、`M47/M51`、`M49/M50`、`M10/M2b`、`M89/M90`）。这**不**影响「红在声称的那条断言上」这个结论 —— 每条变异是**单独施加**的，谁触发的在运行期不含糊。但它意味着：若某条变异意外走到了它**兄弟条目**的缺陷路径上，本判据看不出来。⛔ 这一点不能靠「它们各自的门不同」来搪塞 —— 这 5 组里的条目恰恰绑的是**同一道门的同一条断言**。要分开得给门加更具身份的断言消息，而门本体不在本卡范围。逐组明细见 `fill-expect-loc-<ts>.txt` 尾部。
14. **独立对抗复核（8 维 × 3 视角）只跑完 2 个维度**：`false-kill` / `regex-boundaries` / `loc-drift` / `over-tightening` / `selfcheck-tables` / `claims-vs-evidence` 六个维度的 agent 被**用量上限**打断（`<synthetic>` stop、0 token），⛔ 这**不是**「没发现问题」。已恢复重跑，结果补录在第 10 节 #17。在补录之前，本卡对这六个方向**没有独立复核证据**。
15. **对抗复核（8 维 × 3 视角，Claude 子代理）的完整账目**：43 条原始发现；**18 条完成对抗验证（8 条站立 / 10 条被推翻）**，其余验证 agent 被账号周限额打断（`<synthetic>` stop、0 token）——⛔ 中断**不是**「没问题」，剩余 25 条由主循环逐条人工处置（处置表见第 10 节 #20）。两条站立 HIGH（第三方存证回归 / 空变异对照 first_fail）+ 一条验证者追加 HIGH（假杀不降档）均已修并配负控；站立 MEDIUM/LOW 中可修的已修（rc 语义统一、`file:` 死代码、两维同失败配对、豁免理由非空、`_finishing` 吞异常与吞信号、g32cb/g32ccr1 自愈窗口、g33 JSON 分母、helper 作用域判据、`--only` 缺值崩溃、陈旧行号注释、`_arm_mutation` 写盘窗口），其余登记台账。
16. **`M89` / `M90` 的位置锚实测落在构造前提断言上**（`test_round9_structured_receipt` 第 1/14 条 assert，期望子进程成功、无消息）—— Z2-M15 假杀同型，已从 `EXPECT_LOC` 收回 `KILLED-UNBOUND`（⛔ 收紧，不是改判凑数）。筛出它们的可复跑判据：`premise_anchor_screen.py`（从 probe 存档读全部 138 条实测位置，非 `EXPECT_LOC`——只扫表的话修完就恒返 0 成死判据）。
17. **5 条变异的 `expect_loc` 落在共享 helper 里**（`_c1_reject_once` ← M23/M24/M25；`_parity_once` ← M49/M50）：`(nodeid, loc)` 组合仍唯一、判据成立，但指纹证不了「红在哪道门的调用」——身份弱一档。已建 `EXPECT_LOC_HELPER` 显式登记 + `_check_expect_loc` 作用域一致性判据（新增未登记的当场报）。
18. **「位置与消息必须落在同一次失败上」**：参数化门出多条 FAILED 时，`--tb=line` 的位置行不带 nodeid ⇒ 配对不可证；两维各自由**不同**失败实例满足的形态原先会判 KILLED，现保守判 `HARNESS-ERROR`。
19. **`M43` / `M36b` 的实测拒因疑似「写点 Traceback 崩溃 / 续跑信号」而非语义断言**（复核 MEDIUM，验证未完成）：需对照门源码逐条读，⛔ 本卡未处置，登记台账移交（同失败配对收紧后若它们真出多条失败会自动浮出）。
20. **`M97-writeback-regex-only` 的位置绑不出语句身份**：实测它让门死在 `parser.py`（yaml 库）里，不落在门文件的任何一条断言上 —— 与它原来的消息豁免理由 ④「未捕获异常 `yaml.parser.ParserError`」**独立对上**。它保留 `KILLED-UNBOUND`，⛔ 没有改判成 KILLED 凑数。

---

## 10. 台账待登记条目（车道不改台账，主 session 登记）

1. **Y1-B 行补**：HIGH-1 / HIGH-2 由本卡闭合。HIGH-1 的闭合方式是**换判据维度**（消息 → 断言源位置），⛔ 不是把消息判据修得更严 —— 本树实测证明**任何**基于消息文本的判据都分不开前提断言与目标断言。HIGH-2 由「解析只取摘要区」+「`--show-capture=no` 让 captured 区不产生」两道独立防线闭合，各配一条负控。
2. **Y1-B HIGH-3 的审后整改 `cd10021e` 此前未复审**，本卡顺带核了：`KILLED-UNBOUND` 单列在三套里确实存在（g32b/g32cb/g32ccr1），豁免表确为 39 条（`ast.parse` 实数），`M13b` 确已从豁免表移出并绑了 `EXPECT_MSG`。⚠️ 只核了这三项，不是对 `cd10021e` 的完整复审。
3. **g32b 39 条 KILLED-UNBOUND 逐条处置结果**：见第 6 节表（绑 N / 保留 K / 退役 M，数字以表为准）。
4. **g33 分档统一前后对照**：收口前 `grep -c ANCHOR-ERROR g33 = 0`（只有 `ANCHOR-DRIFT`）、`KILLED-UNBOUND = 0`、`HARNESS-ERROR = 0`；收口后三者均 > 0。两次输出同文件 `six-verdicts-before-after-<ts>.txt`。⚠️ 该文件里「收口前」一列取自 `git show 3f073a1a:<file>`，不是另跑一次 —— 因为收口前的状态就是那个 commit，这是等价且可复现的取法。
5. **四套六档字段名逐字一致的核对结论**：四套均 `from mutation_kill_identity import VERDICTS` 并用 `for v in VERDICTS` 算汇总（`unification-audit-<ts>.txt`）。**g32b 的 `ANCHOR-ERROR` / `SYNTAX-INVALID` 已不再走旁路计数**（改为一并进 `_verdicts`），于是「六档之和 = `len(MUTATIONS)`」成为可核的不变量并写成了判据。
6. **`_AST_MUST_FLAG` patch 未套用**（U7-B / U7-C 未交来 `evidence-w44b/ast-must-flag.patch`）⇒ `backend/scripts/lifespan_isolation_negative_control.py` **不在**本卡 diff 里；该项按 U8-A 的登记归第十四批。
7. **四套信号处置统一**：`RestoreGuard`（`mutation_kill_identity.py`）四信号（**补齐 SIGQUIT**，收口前 g32b/g32cb/g32ccr1 三套都漏）+ 先还原再退出 + **还原期不可打断**。⚠️ 负控当场抓到 `RestoreGuard` 自己的一个缺陷（重复信号让 `_finish` 递归，rc=1 而不是 130），已加防重入闩。
8. **`PYEOF_RE` LOW-9 的处置 = 修**。⚠️ 洞的形态与我初稿写的**不同**：初稿说「终止行带尾随空格匹配不上」，实测**不成立**；真正量到的三个洞是「块内行首 `PYEOFX` 提前截断」「引导行带尾随空白整块提不到」「CRLF 整块提不到」，后两者是**假绿**（编译自检恒通过）。等价性证明：两个真实 SKILL.md 新旧提取逐块逐字节相同。
9. **`expect_loc` 按 D-28 只做 g32b 138 条**；`g32cb`(9) / `g32ccr1`(11) / `g33`(18) 三套的 `expect_loc` **移交第十四批尾巴卡**。理由：D-28 收窄工时；三套现有的弱位置判据挡不住 HIGH-1（第 9 节 #4）。
10. **四套全跑的 N/总数 与耗时**：见第 4-A #7。卡文估「g32b 约 36 min」；本卡的耗时**按存档文件的时间戳实测**填在 `第 4-A #7（`--probe` 28:18 + 全跑 35:25，与卡文估的「约 36 min」相符）`，⛔ 不按中途目测推算（我中途按目测推出过一个「56 s/条 ⇒ 2.2 h」，与后来按时间戳复算的结果不符 —— 数字必须与命令输出同源）。注意 g32b 要跑**两趟**：`--probe`（收集 138 条的实际失败位置，用于回填 `EXPECT_LOC`）+ 全跑（判定）。两趟不能合成一趟，否则期望值与被测量同源到连「从今往后能报漂移」这点价值都没有。
11. **跑前跑后 sha 与标记基线的对账结论**：见第 7 节。⚠️ `g32b_mutation_gates.py` 的标记计数 **153 → 151**，差额 2 是**本卡改注释**造成的（把两处提到该标记字面量的注释改写了），不是残留；文件清单仍是那 5 项。
12. **(b) 两个独立计数一致**：三套 `--list` 自报条数与 `ast.parse` 独立脚本一致；**g33 的 18 条只有单来源**（它没有 `--list`，`--selfcheck-syntax` 不报条数）。
13. **`kill_identity()` 新增 `require_gate_file` 弱位置判据**对**位置豁免条目**关闭（否则一条已登记「失败落在门文件之外」的合法条目会被永远判 SURVIVED —— 收紧收掉一整个轴的形态）。
14. **独立对抗复核抓到一条本轮引入的 HIGH 回归，已修 + 补负控**：`RestoreGuard`「先还原再退出」让 `finally` 里的「第三方改动存证」判据在信号路径上**恒真** —— ① 无第三方改动时每次信号退出都伪造一条告警 + 一份**其实是脚本自己快照**的 `.bak`；② **有**第三方改动 T 时，guard 先用原文覆盖 T ⇒ T 既没被存证也没被保留，而文案还宣称「已存证…请人工核对」。⛔ 这正是那段 docstring 本来要防的事。**证据是本卡自己的存档**：`probe-g32b-20260908T080307.txt:36` 与 `…081108.txt:63`，两份新 `.bak` 里变异标记计数 = 0（存的是快照），而 09-04 那批真·跨车道污染的 `.bak` 计数 = 2（那道告警**本来是有效的**）。修法：把比对**前移进第一个碰文件的人**（`_restore_active`），两条路径共用同一份「读时快照 vs 现盘内容」比对，还原后清表 ⇒ `finally` 再调是干净的 no-op。⚠️ 这条交互此前**没有任何负控覆盖**（`negctl_signal.py` 用的是自建 `restore_all`，不经过存证层），已补 `negctl_thirdparty.py`。
15. **`--only` 不产出六档聚合表**（独立复核 LOW）：`_expect_total` 原来的 `_only` 分支是**不可达死码**（`--only` 与 `--probe` 都在汇总段之前 `return 4`）。已删死分支并注明理由；⛔ **没有**把汇总段前移来「让它活起来」—— 复核指出那会引入两个新缺陷（阶段 2 的 `layered` 不受 `_only` 过滤，定点复核会把全部带层变异写进生产文件；且汇总段末尾的 `return 1` 会打破「部分跑 rc 恒为 4」这条纪律）。
16. **`_stmts_with_scope` 由手写容器枚举改为父链推作用域**：手写要把语句容器枚举完整，初版漏了 `match` 的 `cases`；本树门文件恰好没有 `match`，所以「覆盖一致」这个自检当时也是绿的 —— 属最难发现的那类漏。改写后覆盖面**恒等于 `ast.walk`**，且指纹表逐键相同（137 条 `EXPECT_LOC` 不受影响）。
17. **复核补跑结果**：见 `_bmad-output/审查/evidence-mutkill-r2/` 与本节 #14/#15/#16；六个被上限打断的维度已恢复重跑。
18. **`/private/tmp` 里累积了 68+ 份 `g32b-mutation-thirdparty-*.bak`**（历次跑留下的，无人回收）。⛔ 本卡**不删**（其中 09-04 那批是真·跨车道污染的证据）；登记为清理待办。
20. **对抗复核处置表（43 条原始 / 18 条验证完成：8 站立 10 推翻 / 25 条限额中断后主循环人工处置）**：站立且已修——第三方存证回归(HIGH)+假杀不降档(验证者追加)+空变异对照 first_fail(HIGH)+g33 rc=2 退化+三套恒真「六档之和」+`_finishing` 吞异常/吞信号+`--only` 部分跑 rc 不可分(g33/g32ccr1)+g32ccr1 `--only` 崩溃+`file:` 死代码(降 LOW)+g32cb/g32ccr1 自愈窗口+g33 JSON 分母+helper 作用域+豁免理由非空+`_arm_mutation` 写盘窗口+陈旧行号注释+退出文案三处「声明比证据宽」。登记不修——`--only` 选择语义四套不统一(g32ccr1 精确 id，其余前缀)、g33 `restore_all` 无第三方存证且 drift 自证(先于本卡的形态)、阶段 2 两次落盘无 syntax_check、13 条共用逐字相同三元组与 33 条循环体锚（AST 语句指纹对「第几轮迭代」天然不可分）、Y1-A 收官 JSON「逐字同」判据自此不可能成立（verdict 值域扩大 + ANCHOR-DRIFT 改名，仓内无程序消费方）。被推翻 10 条不采信（含「`_read_prod_blobs` 符号链接静默跳过」——锚点错 17 行指到散文）。
21. **四套退出码语义统一后的新契约**：`rc=3` 还原/残留（数据完整性，最高优先）＞`rc=2` HARNESS-ERROR/六档对不上（负控自己坏了）＞`rc=4` 部分跑/用法错（不构成全量结论；但 rc=2/3 盖过它）＞`rc=1` SURVIVED/failures（关于被测物）＞`rc=0` 全部 KILLED（**已登记**的 KILLED-UNBOUND 残留只报不判失败；未登记的在跑前自检就被挡在 rc=2/4 上）。该契约已由 v2 全跑实证：g32b 以 **rc=2** 收（4 条假杀暴露），g32cb/g32ccr1/g33 以 rc=0 收；旧存档（run-*-2026-09-08T09*/10*）早于代码定稿，**作废不引用**。
22. **`file:` 形态整体删除**：`expect_loc` 的 `file:` 取值原先被 `check_expect_loc_unique` 判违规却又在 `kill_identity` 里有支持分支——死代码且三处文案比代码宽。现统一为「落在门文件外 ⇒ expect_loc 留空 + 两张豁免表 ⇒ KILLED-UNBOUND」；`loc_token_for` 产出的 `file:` token 仅作 probe 观察输出与 mismatch 诊断。
23. **复核方法本身的教训（登记给后续卡）**：负控要测「真 harness 的函数」，不是「同一逻辑的自建复刻」——`negctl_signal.py` 用自建 `restore_all`，于是「先还原再退出」把第三方存证判据打穿这件事四道裁判全绿照不出；两条 HIGH 修复又各引入一条新 HIGH（`finally: raise` 吞还原失败、`--only` 早退吞残留检查），同一缺陷形态在本卡出现第三次时才换成「先写负控再改代码」。
24. **跨车道交叉通报已消费**：U10-A 通报的 `Path.rglob` 抑制 `PermissionError` 形态在 `check_expect_msg_unique` 的生产侧扫描面上**真实存在**，已改 `os.walk(onerror=...)` 并把枚举失败收进返回的 problems 列表。

---

> **format 说明**：v2 全跑之后、commit 之前，五个脚本做了一次 `ruff format`（基线 3f073a1a 全干净 ⇒ 345 行漂移全是本卡的，整文件格式化安全）。format 只动空白不动语义；跑后已复核 `--list` rc=0、前提锚判据 PASS、第三方存证负控 PASS、8 个目标文件 sha 不变。四套全跑**未**因纯空白变更重跑（v2 数字仍有效）。

## 11. 🔗 技术引用

- 共用判据：`backend/scripts/mutation_kill_identity.py`
- 四套 harness：`backend/scripts/g32b_mutation_gates.py` / `g32cb_mutation_gates.py` / `g32ccr1_negative_controls.py` / `g33_mutation_gates.py`
- Y1-B 存档：`_bmad-output/审查/codex-review-CARD-DEBT-mutation-kill-identity.md`（HIGH-1 / HIGH-2 原文）
- 本卡 Codex 存档：`_bmad-output/审查/codex-review-CARD-DEBT-mutkill-R2[-rN].md`
