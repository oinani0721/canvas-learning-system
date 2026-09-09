# 独立复核 round-3：CARD-W4-7（W4 测试隔离门 — RV-C 遗留六条）

## 一 背景与最小读取面

被审对象是 pytest 进程内的隔离门（audit `socket.connect` 事件，阻止测试连 7691/7687，
退出前最终结算）。

**这是 round-3。** round-1 = BLOCKER 0 / HIGH 2（已整改，round-2 确认闭合）；
round-2 = **BLOCKER 0 / HIGH 0**，余 MEDIUM 2 / LOW 1。作者**没有把它们留作登记**，
三条都做了整改。本轮请独立核对这三条整改，并确认没有引入新问题。

**只读下面这几处**（工作目录 = 本仓库根）：

1. **round-2 之后的增量**（本轮整改面）：
   `git diff 001a8271 <审SHA> -- backend/tests/support/live_port_guard.py backend/tests/unit/test_live_port_guard_contract.py`
2. `backend/tests/unit/test_live_port_guard_contract.py` 的四处：
   - `test_index_raising_baseexception_is_also_fail_closed`（改成「自己捕获再判逃没逃出来」）、
   - `test_denying_str_subclass_is_still_blocked`（新，参数化 `uvloop` / `uvloop.loop`）、
   - `test_affirming_str_subclass_is_not_mistakenly_blocked`（新，反方向）、
   - `test_uvloop_submodule_import_is_blocked_by_audit` 的 docstring（事件序列的更正）；
3. `backend/tests/support/live_port_guard.py` 的 `_is_uvloop_module` docstring
   （事件序列的更正）；
4. 证据与跑器（`_bmad-output/审查/evidence-w47/`）：
   `m4-importlib-probe.py`（新增 `no-guard__baseline` 形态）+ `m4-importlib-after3-*.txt`、
   `r1-high-negctl.sh`（新增 rc 保存 / FAILED 节点绑定 / `^E` 正文绑定 / `WANT_FAILED` 参数数）
   + `r1-high-negctl-r1-high1-after3-*.txt` / `-r1-high2-after3-*.txt` / `-r2-med1-after3-*.txt`、
   `negctl_patch_w47.py`（新增 `r2-med1` = 你上一轮给的静态反例）。

## 二 作者对 round-2 三条的整改自述（请独立核对）

- **MEDIUM-1（说谎子类拒绝方向覆盖不足）**：接受。原「取反」型子类对 `_Liar("uvloop")`
  的 `startswith("uvloop.")` 恰好返回 True，于是退回绑定调用时正向仍绿。
  改成**两个方法恒返回 False** 的 `_Denier`，并参数化 `"uvloop"` / `"uvloop.loop"`；
  误拦方向另拆一条**恒返回 True** 的 `_Affirmer`（真值 `"json"`，不得误拦）。
  **你给的静态反例已做成负控 `r2-med1`**：把实现改成
  `str.__eq__(...) is True or (str.startswith(...) and name.startswith(...))`，
  实测该门在 `uvloop.loop` 参数上必红（`1/1 个参数全红`）。
- **MEDIUM-2（「无门完整序列」无获准证据）**：接受。探针新增 `no-guard__baseline` 形态
  （**不装门**、只挂旁观 hook，用桩替掉账本读取）。实测结果**又更正了作者一次**：
  完整序列是 **5 个事件** `['uvloop.includes', 'uvloop.loop', 'uvloop.loop', 'uvloop._noop',
  'uvloop._version']`（`uvloop.loop` 出现两次），不是原先写的「四条」。
  两处 docstring 已按实测改写，并各自限定「本机 CPython 3.14.4 + 本 venv 的 uvloop 版本」。
  判据也加了一条：无门基线若一个事件都没看到 ⇒ `INCONCLUSIVE` 返回 2。
- **LOW-3（负控跑器可能错误归因；HIGH-1 只有一个参数实跑）**：接受，且**根因比你说的更靠前**
  —— 原测试直接调用 `extract_port`，回退实现里逃出来的 `KeyboardInterrupt` 被 pytest 当成
  **会话中断**（实测 rc=2），后两个参数**根本没跑**。改成测试内部 `except BaseException`
  捕获再断言「没逃出来」，三个参数各自以普通 `AssertionError` 翻红（实测 `3/3 个参数全红`，
  rc 从 2 变 1），失败正文点名逃出来的异常类型。跑器同时加了：保存 pytest 退出码、
  `FAILED` 行必须点名被测节点、期望串只在 `^E ` 正文里匹配、`FAILED` 参数数必须**等于**期望值。

## 三 请按重要性排序回答（每条给出结论 + 依据行号）

1. **MEDIUM-1 是否闭合**：`_Denier` / `_Affirmer` 两条加起来，是否还有能同时满足它们、
   却按谎话判定的错误实现？参数化只取 `"uvloop"` / `"uvloop.loop"` 够不够？
2. **MEDIUM-2 是否闭合**：`no-guard__baseline` 用桩替掉 `g.STATE` 会不会让该形态与其他形态
   不可比？「5 个事件、`uvloop.loop` 两次」这个记录本身可信吗（旁观 hook 会不会漏记或重复记）？
   两处 docstring 的限定措辞还有没有过宽的地方？
3. **LOW-3 是否闭合**：改成「自己捕获」之后，这条门还测得到它声称的性质吗
   （`extract_port` 不得让异常逸出）？`WANT_FAILED` 写死参数数会不会在将来加参数时变成
   假红/假绿？跑器现在还有没有能返回 0 却其实没验到的路径？
4. **有没有引入新问题**：本轮增量里有没有恒真判据、或比被测性质更宽/更窄的断言？
5. **前两轮结论是否仍成立**（HIGH-1 / HIGH-2 的整改在本轮增量之后是否仍闭合）？

## 四 输出格式

每条给：**级别** + **文件:行** + **依据**（读到的代码/输出，不要复述作者自述）+ **建议**。
只读判定不了的写「未验证」。开头给一行总结：BLOCKER 数 / HIGH 数。

## 五 边界

- **只读**。不跑测试、探针、负控；**不连任何端口**。
- CARD-W4-4b 的 HIGH-2 / M4 / M7 / M8 不在本卡；`negative_control.py` 与四套 harness 归 U8；
  `backend/app/**` 不在本卡。
- 不评价 `_bmad-output/` 的文档写法，只核对证据与代码是否一致。
