# 独立复核请求 — CARD-W4-FINAL-ACCOUNTING（W4 守卫最终结账：落盘失败 print 移入退出保护块）

## 一 背景与最小读取面（只读；请严格限定在下列面内，不要扩读全仓）

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4`
分支 `card/t9-w4`，基线 `08100483`（B14_BASE），审查 SHA `5e4d10cf`。

**请只读这几处**：

1. `git --no-pager diff --no-color 08100483 5e4d10cf -- . ':(exclude)_bmad-output'`（代码面全部改动，单文件单 hunk）
2. `backend/tests/support/live_port_guard.py` 的 **:1485-1540**（改后实测范围，含 `_final_accounting` 全函数：AST 实测 1487–1538）
3. `_bmad-output/审查/evidence-w4final/ast-protected.py` 全文（判据 1 脚本）
4. `_bmad-output/审查/evidence-w4final/three-run-abc.py` 全文（判据 2 脚本）
5. 判据存档（纯文本）：`_bmad-output/审查/evidence-w4final/` 下 `ast-before-*.txt` / `ast-after-*.txt` / `three-run-before-*.txt` / `three-run-after-*.txt` / `nc-negative-control-*.txt`

**勘探摘要（recon C §5，供背景，不必再核）**：
- §5.1 机理：环境变量 `W4_GUARD_LEDGER`（`:222`）若指向一个**目录**，`_publish_ledger` → `write_ledger` 的 `open(path,"w")` 抛 `IsADirectoryError`（`OSError` 子类），被改前 `:1511 except Exception` 接住，进而执行 `:1512` 的落盘失败 print。若此时 stderr 已关闭（atexit 是 LIFO：后注册的「让 stderr 失效」回调**先**跑，`_final_accounting` 后跑时 stderr 已坏），`:1512` 的 print **自身抛出**并逸出 `_final_accounting`（它是 atexit 回调）⇒ `:1535` 的 `os._exit(3)` 永不执行 ⇒ 进程 **rc=0**，而账本里 `blocked=1 / unaccounted=1`（有未结账拦截却以 0 收场）。
- §5.2 三跑对照基线（改前）：A（ledger=目录 + stderr 坏）rc=0 / B（只落盘失败）rc=3 / C（只 stderr 坏）rc=3 —— 只有 A 红，说明缺陷恰落在两条件同时成立那一格。
- §5.3 口径更正：更早审 SHA 的验收单写的 `:1291-1303` 行号整体较本主干 −231 行，已作废；一律以主干实测行号为准。
- §5.4 口径更正：`_final_accounting` 内 `print(...)` 实测 **3 个**（改前 `:1512 / :1523 / :1530`），不是设计稿写的两个。

**裁定 R-11 原文**（`_bmad-output/审查/evidence-b13-integ/RULINGS-2026-09-10.md`）：
> ## R-11 U7 车道 → **人判合入**
> - U7-A 外审 HIGH-1（`_final_accounting` 落盘失败 print 在退出保护块外，rc=0 假绿形态）→ **登记 TAIL 高优先（第十四批）**：W4 门是测试基建非产品数据面；U7-C 5 轮已尽；复核员独立复现确认。
> - U7-A 方法学替代（93d47028 树对照不可执行，改 HEAD−try/except 对照）→ **追认**。

## 二 作者自述（请独立核对，不要采信）

1. 改动只有一处：改前 `:1512` 的落盘失败 print 被套进一层嵌套 `try: … except BaseException: pass`（与退出保护块改前 `:1522-1534` 同型），净增 3 行；`:1511` 的 `except Exception as exc:` 行本身、取快照 `:1504`、`_publish_ledger` 调用 `:1510`、裁定分支 `:1519`、退出保护块、`os._exit(FINAL_EXIT_CODE)` 全部未改。
2. 判据 1（AST 逐 print 报 protected / UNPROTECTED）：改前名单 = `1512 UNPROTECTED` / `1523 protected` / `1530 protected`；改后名单 = `1513 protected` / `1526 protected` / `1533 protected`，UNPROTECTED 计数 0。
3. 判据 2（三跑，子进程内以 `sys.audit("socket.connect", None, ("127.0.0.1", 7691))` 合成受拦事件，不建立真实连接、不设 `W4_GUARD_REQUIRE_BLOCKED_TARGET`）：改前 A rc=0 / B rc=3 / C rc=3；改后 A/B/C 全 rc=3；三跑进程内账本恒 `blocked == 1 and unaccounted == 1`。
4. 负控输入（删掉新加的嵌套保护）使两个判据**同时**翻回：AST 回到恰 1 行 `1512 UNPROTECTED`，三跑 A 回 rc=0；且负控后的文件与 `08100483` 的该文件逐字节相同（即负控恰是本次修法的逆操作）；负控段前后 `shasum -a 256` 逐字同 `56c589ac…`。
5. 结账 / 发布 / 退出语义一律未改：落盘失败仍然「说话」，只是该 print 自身抛出的异常被就地吞掉，与改前 `:1534` 同语义。
6. 契约套件 `backend/tests/unit/test_live_port_guard_contract.py` 开工 / 收工均 151 passed、0 failed。

## 三 请回答的问题（按重要性排序）

⓪ `:1512`（改后在 `:1514`）那层嵌套保护是否真的吞掉**所有**可能逸出的路径——包含 `BrokenPipeError`、`ValueError: I/O operation on closed file`、以及 stderr 对象被替换成其它坏态时的异常？反过来，它是否引入了新的「把真实的结账失败信号一并吞掉」的风险（例如原本应当让运维看见的落盘错误从此彻底无声）？

① 改后 A 格的 rc=3 是否**确实**来自 `:1538`（改后行号）的 `os._exit(FINAL_EXIT_CODE)` 真正执行，而不是别处提前退出、或被另一条兜底路径掩盖成同样的 3？

② 三跑用 `sys.audit` 合成的受拦事件，与真实 `socket.connect` 触发的拦截，在记账路径上是否等价（`blocked` / `unaccounted` 计数一致、`record` 与 `finalize_and_snapshot` 走同一分支）？若不等价，这套判据覆盖到的究竟是哪一段。

③ 保护 print 吞掉异常之后，「落盘失败要说话」这条原意是否仍成立？可观测性降级到什么程度、是否可接受（请对照改前 `:1533-1534` 那段同款注释的取舍）。

④ 本卡的先红后绿只存在于 `evidence-w4final/` 的脚本里，committed 的 pytest 套件**没有**新增回归锁。这是否遗漏了面？是否应当把一条 A 格（ledger=目录 + stderr 坏 ⇒ rc=3）的回归用例写进契约套件？（背景：该契约文件按裁定 R-B14-4 属于下一张卡 T9-B 的地盘，本卡只登记移交、不扩面。）

⑤ 同一文件里 `_rewrite_ledger_after_late_record` 等**迟到路径**是否存在同型的未被保护的 print（同样可能在 stderr 坏态下逸出）？

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级列出，每条给 `file:line` 与一句说明如何观察到该问题的思路。措辞请用「负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径」。若某级为空请明确写 0 条。

## 五 边界

只读，不要修改任何文件。不要连接任何数据库或网络端口（本仓 7691 / 7687 为受拦端口）。不需要也不要运行完整的真库门（7692 容器）套件。不评估真实 atexit 迟到线程与 `_publish_ledger` 锁竞态下的行为（本卡未覆盖，已如实登记）。不评估 W4 哨兵判据改绑（那是 T9-C 的面）。
