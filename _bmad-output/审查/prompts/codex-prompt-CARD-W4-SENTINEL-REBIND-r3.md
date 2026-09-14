# 独立复核请求 — CARD-W4-SENTINEL-REBIND **round-3**（按 round-2 的两条 HIGH + MEDIUM-3/4 + LOW-7 整改后复审）

## 一 背景与最小读取面（只读；请严格限定在下列面内，不要扩读全仓）

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4`
分支 `card/t9-w4`。round-1 审 `86535afb`，round-2 审 `5c696c92`，**本轮审查 SHA `9a280b16`（= 当前 HEAD）**。
本卡起点 `a4dbd156`。

**请只读这几处**：

1. `git --no-pager diff --no-color 5c696c92 9a280b16 -- . ':(exclude)_bmad-output'`（**本轮整改的全部代码改动**）
2. 需要整体时：`git --no-pager diff --no-color a4dbd156 9a280b16 -- . ':(exclude)_bmad-output'`
3. `backend/tests/support/w4_sentinel_identity.py` **全文**（本轮唯一改逻辑的文件）
4. `backend/tests/unit/test_w4_sentinel_rebind.py` **全文**（34 → 38 例）
5. `backend/tests/support/hygiene_snapshot_tristate.py` 全文（r1 之后未改）
6. `backend/tests/unit/conftest.py` 的 `:78-106`（docstring）与 `:315-340`（sha 路由）——两处 r1 之后未改
7. 只读锚（不评其设计）：`live_port_guard.py` 的 `:205`/`:207`/`:225`/`:230`/`:282`/`:351-363`/`:440-461`/`:1540-1556`/`:1588-1596`
8. 本轮判据存档（`_bmad-output/审查/evidence-w4-sentinel-rebind/`）：
   `codex-r2-fix-verify-20260914T232556.txt`（拿你 round-2 的四条复现输入逐条验 + 四条反向锚）、
   `w4sr-negctl-r3-20260914T232637.txt`（两段负控重跑，绑最终 parser sha `8cf9cb96…`）、
   `unit-close-r3-20260914T232722.txt`（目录级）、`unit-close-diff-r3-20260914T233251.txt`
9. 前两轮存档（对照）：`codex-review-CARD-W4-SENTINEL-REBIND.md`、`…-r2.md`

## 二 本轮整改自述（请独立核对，不要采信）

**HIGH-1 残留（缺四元组仍被当作可比较）已改**。你的复现成立：`quad_vals` 写成
`{q for … if q is not None}`，那个 `if` 把「A 根本没有汇总行」滤成了「A 没有意见」。
现在：**任一份档缺汇总四元组 ⇒ rc=2（拒判）**，不再退 0。`blocked_count()` 仍单独支持 final-only。

**HIGH-3 残留（线程名含换行仍静默消失）已改**。我原来的 `_BODY_CANDIDATE_RE` 是「这行**像不像**
哨兵记录」的猜测式规则，你的 `"\nworker"` 例把记录切成两半后两半都不像。现在换成**两条痕迹判定**，
不猜内容、只认切割留下的断口：
- `_BODY_TRUNCATED_RE = ^- .* on thread\s*$`（前半段：止于 `on thread`，身份被切走）
- `_BODY_ORPHAN_RE   = ^(?!- ).*\(owner=`（后半段：含 `(owner=` 却不以 `- ` 开头 = 孤儿续行）
命中任一 ⇒ 抛 `W4LedgerConflict`（CLI rc=2）。

**MEDIUM-3（新候选规则误伤普通日志）已改**。这条是我上一版假红的直接后果：
`- waiting on thread worker` 被当畸形记录。新规则下它两条痕迹都不命中，不再误判。
**根因我记下了：判据不该问「这行像不像我要的数据」，只该问「有没有留下被破坏的痕迹」。**

**MEDIUM-4（`CONSISTENT-ZERO` 只看 blocked）已改**：改为整条四元组 `(0,0,0,0)` 才打「全零」标签；
`(12,0,12,0)` 判 rc=0 但**不**打该标签。

**LOW-7 已改**：advisory 的措辞由「真连上了现网」改为「连接尝试被放行，是否连上取决于对端」。

**未改（按你的确认登记移交）**：round-2 的 MEDIUM-5（裸 repr 不保证跨跑稳定 + 切错边界的两行）、
MEDIUM-6（`_FINAL_RE` 只有左锚、混档 `summary=2 + final=3` 返回 3）。

**未改动面**：`live_port_guard.py` / `guard_plugin.py` / 根 `conftest.py` 三份 sha 与 HEAD 逐字同；
地盘仍是那 4 个文件；目录级 diff 对 64 条红基线**完全相同**（`>` 0 条），38 条新测试一条不在红集。
四文件 sha：`w4_sentinel_identity.py=8cf9cb96…`、`hygiene_snapshot_tristate.py=e21500b4…`、
`test_w4_sentinel_rebind.py=4da5db1c…`、`unit/conftest.py=f0ca7225…`。

## 三 请回答的问题（按重要性排序）

① **这是本卡第三轮，前两轮的 HIGH 我都「修得不彻底」——同一个假设换个输入又活过来一次。**
两次的假设分别是「线程名是单行且无空格」和「四元组一定存在」。
请**主动去找这两个假设还在哪里成立**：代码里还有哪些地方隐含「这个字段一定在」「这一行一定是一行」
「解析得上就是全部」？我要的不是「这次的输入过了吗」，而是「造成它的那个假设，还活在哪」。

② **两条痕迹判定（`_BODY_TRUNCATED_RE` / `_BODY_ORPHAN_RE`）本身有没有新的假绿或假红？**
特别是：线程名含 `\r`、含制表符、含 `(owner=` 字面量、地址段含换行（不是线程段）、
正文行被 pytest 的 captured-output 缩进（前导空格）时，分别命中哪条、结论是什么。
以及：**哪种「被破坏的记录」不会留下这两个断口**？

③ **缺四元组即 rc=2 会不会太严**？真实存档里有没有合法却只有总账行没有汇总行的形态
（例如进程被杀在 `_final_accounting` 之后）？若有，你倾向拒判还是退化比较？

④ **本轮是否有回归**：`blocked_count` 的 `final >= summary` 语义、`summary_quad` 的算术自洽门、
重复汇总/总账抛冲突、`normalise_thread` 的 portal 归一、三态函数与 conftest 路由 —— 是否仍成立。

⑤ 还有没有**新的**门未覆盖的路径？请列举，不要求本卡穷尽。

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给出 `file:line` + 一句话复现思路，
用**负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径**表述。
请在开头**明确给出本轮的 BLOCKER 数与 HIGH 数**。经核对成立的项请明说「核对通过」并给出位置。

## 五 边界

- **只读**：不要修改仓库里的任何文件，不要跑 hook，不要暂存文件。
- **不连库**：不要尝试连接 7691 / 7687 / 7692。
- **不评 `live_port_guard.py` 守卫本体的设计**。
- **不做全称封闭证明**。
