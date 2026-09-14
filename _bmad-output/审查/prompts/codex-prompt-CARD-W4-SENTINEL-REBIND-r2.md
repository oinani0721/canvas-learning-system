# 独立复核请求 — CARD-W4-SENTINEL-REBIND **round-2**（按 round-1 的三条 HIGH + LOW-7 + MEDIUM-6 整改后复审）

## 一 背景与最小读取面（只读；请严格限定在下列面内，不要扩读全仓）

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4`
分支 `card/t9-w4`。round-1 审 `86535afb`，**本轮审查 SHA `5c696c92`**。前提 commit `a4dbd156`。

**请只读这几处**：

1. `git --no-pager diff --no-color 86535afb 5c696c92 -- . ':(exclude)_bmad-output'`（**本轮整改的全部代码改动**）
2. 需要整体时：`git --no-pager diff --no-color a4dbd156 5c696c92 -- . ':(exclude)_bmad-output'`
3. `backend/tests/support/w4_sentinel_identity.py` **全文**（HIGH-1/2/3 整改面）
4. `backend/tests/unit/test_w4_sentinel_rebind.py` **全文**（28 → 34 例）
5. `backend/tests/support/hygiene_snapshot_tristate.py` 全文（本轮未改）
6. `backend/tests/unit/conftest.py` 的 `:78-106`（docstring，LOW-7 整改）与 `:315-340`（sha 路由，本轮未改）
7. 只读锚（不评其设计）：`live_port_guard.py` 的 `:205`/`:207`/`:225`/`:230`/`:282`/`:351-363`/`:440-461`/`:1540-1556`/`:1588-1596`
8. 本轮判据存档（`_bmad-output/审查/evidence-w4-sentinel-rebind/`）：
   `codex-r1-high-fix-verify-20260914T230922.txt`（拿你 round-1 的三条复现输入逐条验 + 两条反向锚）、
   `w4sr-negctl-r2-20260914T230950.txt`（两段负控重跑，**绑最终 parser sha**）、
   `unit-close-r2-20260914T231032.txt`（目录级，**跑前记 parser sha**）、
   `unit-close-diff-r2-20260914T231646.txt`
9. round-1 存档（对照）：`codex-review-CARD-W4-SENTINEL-REBIND.md`

## 二 本轮整改自述（请独立核对，不要采信）

**HIGH-1（CLI 没接四元组）已改**。你说得对：`_describe()` 只返回 `blocked` 与 bodies，
`summary_quad` 写了却从没接进 CLI —— 而我在 docstring 与验收单里已经写了「CLI 比对整条四元组」。
现在 `_describe()` 返回 `(path, blocked, quad, bodies)`，`main()` 把 `quad` 纳入比对。
你的原例（`advisory=0` vs `advisory=12`）实测 **rc=1**。
**根因我记下了：测 helper 不等于测接线**；上一版的测试只证明 helper 能区分，没有一条走 `main()` 的测试。
本轮补的三条测试都走 `main()`。

**HIGH-2（全零 ≠ 门在位且查完）已改，但只改了「说法」不改「结论」**。
纯文本确实无从区分（`summary_line` 不含 `installed`，xdist 每 worker 独立 STATE）。
仍退 0（否则每一次干净跑都会红），但裁定词改成 `CONSISTENT-ZERO` 并强制打印
「不能证明门当时在位、也不能证明覆盖完整」。**请判断这个处置是否足够**，
或者你认为全零档就该 rc≠0（那会让本卡自己的目录级判据每次都红，我想听你的权衡）。

**HIGH-3（含空格线程名静默丢失）已改**。`_BODY_RE` 的线程段由 `\S+` 改 `.+?`；
新增 `_BODY_CANDIDATE_RE`：**看得出是记录行、却解析不出身份的行一律抛**，不得压成「没有这条记录」。
你的两条原例实测 **rc=1**，身份集分别是
`{"('::1', 7691, 0, 0) on thread Thread-1 (worker)"}` 与 `{"('127.0.0.1', 7687) on thread Thread-2 (worker)"}`。
⛔ 我认下这条的根因：**这和本卡正在修的 conftest 病（`None↔None` 被压成「没问题」）是字面上同一个病**
—— 我一边修它，一边在新代码里犯它。

**LOW-7 已改**：`conftest.py` 的 `_hygiene_snapshot` docstring 不再写「前后同为 None 即视为未变化」。

**MEDIUM-6（判据未绑审查版本）已改**：你算的 `2a16b6f7…` 与存档记的 `73c5fa34…` 不符，是因为我在
那些判据跑完**之后**才跑了 `ruff format`。已把两段负控与目录级**全部重跑**，并在存档头部记下
最终 parser sha（`c52a8a5b…` / `e21500b4…`）。

**未改动面**：`live_port_guard.py` / `guard_plugin.py` / 根 `conftest.py` 三份 sha 与 HEAD 逐字同；
地盘仍是那 4 个文件；目录级 diff 对 64 基线**完全相同**（`>` 0 条），34 条新测试一条不在红集。

## 三 请回答的问题（按重要性排序）

① **三条 HIGH 是否真的封住了，且没有造出新的假绿/假红？** 请用你 round-1 的原例独立重跑。
特别核 HIGH-3 的新写法：`.+?` 非贪婪 + `_BODY_CANDIDATE_RE` 的「看得出是记录行」判定，
在 owner 含 ` on thread ` / 地址含 ` (owner=` / 行内有多个 ` (owner=` 时分别得到什么；
新增的「解析不了就抛」会不会把**合法**存档里的某类行误判成畸形（假红）。

② **HIGH-2 的处置够不够？** `CONSISTENT-ZERO` + 明示边界 vs 全零直接 rc≠0，你倾向哪个、为什么？
若倾向后者，本卡自己的目录级判据（`blocked=0` 是常态）该怎么用这个工具？

③ **本轮是否有回归**：`blocked_count` 的 `final >= summary` 语义、`summary_quad` 的算术自洽门、
三态函数与 conftest 路由、`normalise_thread` 的 portal 归一 —— 是否仍成立。

④ **你 round-1 的 MEDIUM-4/5 我这轮没改**（裸 repr 不保证跨跑稳定、`_FINAL_RE` 只有左锚、
混档的 `summary=2 + final=3` 仍返回 3）。这三条我准备按 MEDIUM「登记不阻断」移交下一张 W4 卡。
请确认这个处置是否恰当，或指出其中哪条其实该在本卡收掉。

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
