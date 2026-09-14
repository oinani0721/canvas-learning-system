你是独立复核者。对象是一张已完成的小卡：CARD-TAIL-CLEANUP-LOOP [BATCH-2026-09-11-第十四批]。
只读审查，不要改任何文件、不要连任何数据库、不要跑真实定时器、不要评价本车道其它卡（T5-B~E）的面。

## ① 背景 + 最小读取面（请只读下面这些，不要扩面）

仓库树根：/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs
基准 SHA：08100483（B14_BASE）  审查 SHA：8ace89c1（本卡唯一 commit）

本卡修一个运行期真缺陷（上游登记为 T-new-4，被主 session 定为 TAIL 最高优先）：
后台任务清理调度器 `cleanup_loop` 的 `while True` 里，唯一的 yield 点是
`await asyncio.sleep(settings.TASK_CLEANUP_INTERVAL_SECONDS)`；而 `Settings` 上没有
`TASK_CLEANUP_INTERVAL_SECONDS` 这个字段，于是参数求值在 `await` 执行之前就抛 AttributeError，
被同一 try 的 `except Exception` 接住、无任何等待即回到循环顶 ⇒ 清理调度退化为不交还事件循环的
CPU 紧循环。本卡同时要求 pyright 保持 0 errors。

最小读取面（五项）：
1. `git --no-pager diff --no-color 08100483 8ace89c1 -- . ':(exclude)_bmad-output'`（本卡全部代码改动，3 文件）
2. `backend/app/services/background_task_manager.py` 的 `start_cleanup_scheduler` = :339-377
   （内嵌 `cleanup_loop` = :342-369；参考 `cleanup_old_tasks` = :306-337，本卡未改它）
3. `backend/app/config.py` 的新增字段段 = :725-735（`TASK_CLEANUP_INTERVAL_SECONDS` 在 :730）
   以及 :640-655 的 MEMORY_RETRY 段（那是另一张卡 T10-E 的面，本卡不得落 hunk，仅供你核不重叠）
4. `backend/tests/unit/test_background_task_manager.py` 的 `TestCleanupScheduler` 类全文 = :161-297
   （同文件 :26-158 的 `TestContextVarInheritance` 与 autouse fixture 是既有内容，本卡未改）
5. 上游缺陷登记原文：
   `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-pyright-svc/TAIL-handover.txt` 的 §A 中 `T-new-4` 那两行（:11-12）

裁判证据（如需核对数字，只读，不必重跑）：
`_bmad-output/审查/evidence-tail-cleanup/`，其中 `README.md` 标注了每条判据的权威存档
与被取代存档（代码定稿期做过一次只收行不改语义的编辑，行号整体下移，故承重裁判都重跑过）。

## ② 作者自述，请你独立核对（不要采信，逐条自己验）

- `TASK_CLEANUP_INTERVAL_SECONDS` 已进 `Settings`，`default=3600`、带 `gt=0` 约束。
- 原先挂在 sleep 参数行上的那条类型层抑制注解（reportAttributeAccessIssue）已删除；
  仓根 pyrightconfig 把 reportUnnecessaryTypeIgnoreComment 设为 warning，留着会让 warnings 从 81 涨到 82。
  实测 `pyright app`（cwd=backend/）= `0 errors, 81 warnings, 0 informations`。
- `except Exception` 分支在 `logger.error` 之后补了 `await asyncio.sleep(settings.TASK_CLEANUP_INTERVAL_SECONDS)`，
  复用同一间隔、零新增配置面。
- 两条新单测确定性终止：monkeypatch `asyncio.sleep` 换成记录入参的 spy，spy 在第 N 次被调用时抛
  `asyncio.CancelledError`（它继承 BaseException，不会被 `except Exception` 吞掉），由
  `except asyncio.CancelledError: break` 收尾；不依赖墙钟。每个测试首行是
  `assert hasattr(settings, "TASK_CLEANUP_INTERVAL_SECONDS"), "no field"` 的 fail-fast 守卫。
- 测试 B 判「异常路径确实等待了」用的是因果位置而非数值：数「抛异常那次清理」与「下一次清理」
  之间隔了几次 sleep（有等待 = 2 次，没有 = 1 次）。因为退避复用同一间隔，数值维度分辨不出。
- 两个负控输入各自红在指定断言（负控 1 改名 config 字段 → 根因门与两测守卫红；
  负控 2 删掉 except 分支那行 await → 只有测试 B 的 sleeps_between 断言红、测试 A 仍绿），
  跑前跑后三文件 `shasum -a 256` 逐字节相同。
- `tests/unit` 目录级对 64 条既有红基线 diff 为空（无新增红）。
- 本卡代码面 diff 恰为三文件；config.py 的 hunk 在 :725，与 :640-655 无交集。

## ③ 请按重要性排序回答的问题

0. `default=3600` 会不会让「刚完成 / 刚失败的任务」在崩溃诊断窗口里堆积过久？
   请结合 `cleanup_old_tasks(max_age_hours: int = 24)` 的保留截止一起判断这个量级是否自洽。
1. `except Exception` 分支复用 `TASK_CLEANUP_INTERVAL_SECONDS` 作为错误后的等待，
   在「间隔被运维配得很大」时会不会让错误长时间得不到重试？是否应改用一个更短的独立等待常量？
2. `cleanup_loop` 里是否还剩别的紧循环路径 —— 即任何一条能在不经过 `await` 的情况下回到循环顶的路径？
3. 新字段的插入点是否与 MEMORY_RETRY 段（:640-655，T10-E 的面）有任何形式的重叠或相邻风险？
4. 单测对 `asyncio.sleep` 的 monkeypatch 是否可能污染事件循环或同一 session 的其它测试？
   spy 内部保留了对原始 `asyncio.sleep` 的引用并在非终止分支 `await real_sleep(0)`，这样做是否恰当？
5. 删掉那条抑制注解，是否可能在某个 pyright 配置下反而触发新诊断？
6. 两条测试的断言里，有没有哪一条在生产代码被改坏时仍会保持绿（即门未覆盖的路径）？

## ④ 输出格式

逐条列 BLOCKER / HIGH / MEDIUM / LOW，每条给出 `file:line` 与一句复现思路。
描述问题时请使用这四类说法：「负控输入」「对照输入」「未被拦下的输入」「门未覆盖的路径」。
没有问题的档位请明确写「无」。最后给一段总评。

## ⑤ 边界

只读；不连数据库；不跑真实定时任务；不评 T5-B~E 的面（edges.py / mcp 工具 / security.py /
system.py / boards.py / board_manifest_tools.py / test_openapi_contract.py）；
不要求本卡去改 `cleanup_old_tasks` 本体、`create_task`、`stop_cleanup_scheduler` 的逻辑
（那些不在本卡范围）；不要求本卡处理仓库既有的 ruff-format 漂移（主干既有，另有卡负责）。
