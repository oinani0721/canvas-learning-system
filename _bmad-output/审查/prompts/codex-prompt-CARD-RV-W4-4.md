# 独立复核请求 — CARD-RV-W4-4（零代码复审卡）

你是独立复核者。请只读地核对一份**复审报告**的结论是否与代码现状相符。
本卡**一行代码都没改**（commit 只含 `_bmad-output/`），所以你不是在审代码改动，
而是在审「作者对既有代码的定性判断」。

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard`

---

## 一 背景 + 最小读取面（写死，请不要扩大）

第十二批的卡 Y7-A（squash `360a4cb2`，父 `93d47028`）修了一道「测试进程不许连现网 Neo4j 端口」的门。
当时的外部复核给出 0 BLOCKER / 3 HIGH / 5 MEDIUM / 2 LOW 共十条。**那份复核审的是工作区，没有审 SHA**，
而且其中 HIGH-1 / HIGH-3 的整改是**在那次复核之后**才做的、至今没有第二轮外审。

本卡（CARD-RV-W4-4）做的事：把那十条逐条与**当前 HEAD** 对照，定死「哪条真修了 / 哪条只是改了措辞 /
哪条被测试钉成了规格 / 哪条没修」，并对 HIGH-1、HIGH-3 两条的整改做独立复审。

请只读以下内容：

1. `git diff 93d47028 360a4cb2 -- backend/tests/support/live_port_guard.py backend/tests/support/guard_plugin.py backend/tests/conftest.py backend/scripts/lifespan_isolation_guard_probes.py backend/tests/unit/test_live_port_guard_contract.py`
2. HEAD 的 `backend/tests/support/live_port_guard.py` 第 **580-700** 行与第 **1190-1310** 行
3. HEAD 的 `backend/tests/unit/test_live_port_guard_contract.py` 第 **848-906** 行
4. 旧复核存档 `_bmad-output/审查/codex-review-CARD-W4-4-settle-atomic.md` 的 **HIGH-1**（:14-22）与 **HIGH-3**（:44-54）两段
5. 本卡的定性表 `_bmad-output/审查/evidence-rv-w44/triage-20260908.md`
6. 本卡的复现输出 `_bmad-output/审查/evidence-rv-w44/high1-repro-*.txt`（两份，取较新的那份）
   与复现脚本 `_bmad-output/审查/evidence-rv-w44/high1-repro.py`

---

## 二 作者自述（请独立核对，不要采信）

以下是本卡的结论。请逐条对着 HEAD 原文核，不同意就直说。

**(1) 十条的状态判定**（详见定性表 §一）：

| 条目 | 作者判定 |
|---|---|
| HIGH-1 | 审后整改，主症闭合；「身份复核并非必然执行」那半**未闭合**，改为在 `:587-590` 如实声明 |
| HIGH-2 | **未修**；且契约 `:764-775` 的 `assert precheck_at < register_at` 把该顺序钉成了规格 |
| HIGH-3 | 审后整改，已复审 |
| M4 | **未修**（两条写盘路径仍各自 `open`，`:1288` 第二分支原样保留） |
| M5 | 已改措辞，行为未变（`:1116-1131`） |
| M6 | 已改，落在证据脚本 `mutation_teardown.py`，不在代码树 |
| M7 | **未修**（五处判据形态与旧复核描述逐条对得上，行号与旧复核引用行重合） |
| M8 | **未修**（旧复核引用的 `:302` / `:310` / `:378` 三处在 HEAD 上逐字相同） |
| LOW-9 | 已改（`before-repro.py:129-139` 已有 `STAGE-INVALID` 分支），落在证据脚本 |
| LOW-10 | **部分**：`:934→:947-958` 已改、`:1166→:1193` 已改、**`:119-120` 未改** |

**(2) HIGH-1 的独立复现结论**（详见定性表 §二）：

作者认为旧复核的对照口径「在父提交 `93d47028` 上跑同一脚本」**不可执行**——
注入点 `_finalize_race_seam_hook` 是 Y7-A 本卡引入的，父提交里出现 0 次（`RECORD_LATE` 同样 0 次）。
于是作者改用「HEAD 源码 − 整改时加上的 `try/except`」作对照输入（即整改前的那一版写法本身）。三跑：

| 输入 | rc | blocked | unaccounted |
|---|---|---|---|
| HEAD 原文 | 3 | 1 | 1 |
| 对照输入（HEAD − try/except） | 0 | 0 | 0 |
| 父提交 `93d47028` 原文 | 脚本报「本树没有该注入点」 | — | — |

作者称第二行**逐字复现**了旧复核记录的 `blocked=0, unaccounted=0, 退出 0`。

**(3) `except BaseException` 的语义面**（详见定性表 §2.4）：

作者实测注入点改抛 `KeyboardInterrupt` 与 `SystemExit` 两种输入，两跑都得到
`rc=3, blocked=1, unaccounted=1`，且调用方收到的仍是**拦截**异常而不是注入的那个。
据此作者断言：该 `except` 吞掉的严格只是注入点自己抛出的那一个异常，承重路径不经过它；
且默认注入点的函数体被契约 `:855-858` 锁死为「只有 docstring」，所以新语义面在生产路径上是空集。

**(4) 双向声明与反证**（详见定性表 §四）：

`grep -n '⇔'` 得恰 3 行（`:77` / `:293-294` / `:1243`），都声称「`rc=3` ⇔ 账本 `unaccounted>0`」双向成立。
作者认为 `:1288` 的 `if unaccounted > 0 or (blocked > 0 and effective_status == 0):` 第二个析取项
是反证：它允许 `unaccounted == 0` 时 rc=3，因此「rc=3 ⇒ unaccounted>0」这个方向不成立。

**(5) LOW-10 残留的张力**（详见定性表 §四·补）：

作者认为 `:119-120`「最终总账之后……已无人能把它变成非零 rc —— 这段窗口无法在进程内闭合」
与整改后 `:661-680` 的迟到分支（`:662` 注释「只能就地把进程打成非零」+ `:680` `os._exit(3)`）
存在直接张力：那条迟到分支自己就是把 rc 改成非零的那一位。
但作者**不主张** `:119-120` 完全错误，也**不证明**残余不可闭合窗口的边界在哪。

---

## 三 请回答的问题（按重要性排序）

1. **HIGH-1 的 `try/except BaseException`（`:654-657`）是否闭合了旧复核描述的那三步**
   （替换注入点为抛异常的函数 → 发一条受拦端口的审计事件 → 账本为零且进程退出 0）？
   作者的对照输入（HEAD 源码去掉那个 `try/except`）是否与旧复核当时审的形态同构？
   如果你认为不同构，请指出差在哪一行。

2. **该 `except BaseException` 是否引入了作者没说到的语义面**？
   作者只测了注入点抛 `RuntimeError` / `KeyboardInterrupt` / `SystemExit` 三种输入。
   还有哪些输入形态会让这个 `except` 改变承重路径的结果，而作者的三跑覆盖不到？

3. **HIGH-3 的迟到分支 `:661-680`（`try:` 在 `:667`）是否覆盖了 stderr 写入失败的全部形态**？
   现有的门只覆盖「stderr 已关闭」这一种。`sys.stderr` 被替换成 `write()` 抛异常的对象、
   被替换成 `None`、或 fd 被重定向到不可写目标——这些**门未覆盖的路径**里，
   `os._exit(FINAL_EXIT_CODE)` 是否仍必然执行？

4. **「⇔」三处若撤回为单向，探针 `probe_ledger_matches_verdict`（`:1655`）会不会因此弱化**？
   该探针 docstring 声称「两个方向都要」，但钉的是两个具体形态。
   撤回文字表述后，它现有的判据是否仍然承重？

5. **定性表（第 (1) 项十行）的状态判定有没有哪一条与 HEAD 原文不符**？
   特别请核对被判「未修」的四条（HIGH-2 / M4 / M7 / M8）——
   作者的依据是「旧复核引用的行号在 HEAD 上仍指向同样的代码」，这个依据本身是否可靠？

---

## 四 输出格式

每条发现写成：

```
**级别（BLOCKER / HIGH / MEDIUM / LOW） N — 一句话标题**

位置：<文件:行>
依据：<你在源码里看到的原文，以及它为什么与作者的判定不同>
建议：<处置方向>
```

只读判定不了的，请明确写「未验证」并说明缺什么才能判定。
如果某条你核完认为作者判对了，也请写一行说明你核过了——沉默不代表同意。

---

## 五 边界

* **只读**。不要改任何文件。
* **不要连接任何端口**（7691 / 7687 是现网库，本卡全程只用合成的审计事件，没有真实连接）。
* 以下**不在本卡范围**，看到也不必展开：HIGH-2 / M4 / M7 / M8 的修法归下一张卡（U7-B）；
  地址分类函数一族归 U7-C；`lifespan_isolation_negative_control.py` 归 U8。
  本卡只做定性与复审，不改代码。
* 本卡的 commit 只含 `_bmad-output/`，代码树与 `da690bf8` 逐字节相同。
