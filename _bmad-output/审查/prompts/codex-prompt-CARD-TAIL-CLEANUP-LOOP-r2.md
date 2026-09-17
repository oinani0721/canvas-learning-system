你是独立复核者，这是同一张卡的第 2 轮：CARD-TAIL-CLEANUP-LOOP [BATCH-2026-09-11-第十四批]。
只读审查，不要改任何文件、不要连数据库、不要跑真实定时器、不要评本车道其它卡（T5-B~E）的面。

## ① 背景 + 本轮相对上一轮变了什么 + 最小读取面

树根：/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs
基准 SHA：08100483（B14_BASE）  上一轮审查 SHA：8ace89c1  **本轮审查 SHA：85d2c18c**（当前 HEAD）

卡的目标不变：后台任务清理调度器 `cleanup_loop` 的 `while True` 里，唯一的 yield 点是
`await asyncio.sleep(settings.TASK_CLEANUP_INTERVAL_SECONDS)`；`Settings` 上原本没有这个字段，
参数求值在 `await` 执行之前抛 AttributeError，被同 try 的 `except Exception` 接住、无任何等待
即回到循环顶 ⇒ CPU 紧循环。本卡补字段 + 删多余的类型层抑制注解 + 给异常分支补等待。

**round-1 你给的是 B0/H0/M0/L3。本轮只改了测试文件，生产代码（config.py 与
background_task_manager.py）与 8ace89c1 逐字节相同。** 对三条 LOW 的处置：

- LOW-2（两测没验证「成功清理后继续周期运行」）：**接受并修**。作者先做了实验：给生产
  `await self.cleanup_old_tasks()` 之后注入 `break`，改前两测仍 2 passed —— 你说的假绿面属实。
  现新增两条断言：A `:242` 断言期间完成 2 轮清理；B `:317` 断言失败恢复后 ≥2 轮。
- LOW-1 前半（数 sleep 次数分不出「就地 await」与「丢进 create_task」）：**接受并修**。spy 改为
  记 `sleep-enter` / `sleep-exit` 成对事件；就地 await ⇒ enter/exit/enter/exit 四事件，
  create_task ⇒ 两个 enter 连着。`:307` 断言改成精确比对这四个事件。
- LOW-1 后半（没钉死等待秒数等于配置间隔）：**rejected**。卡文 (c).3 的契约本就是
  「必须 await 一个 > 0 的等待，车道可改用独立常量」，钉死具体值反而与契约冲突。
- LOW-3（断言文案说「少了退避 = 紧循环仍在」夸大）：**接受**。你说得对，循环顶的 sleep 仍会
  让出，删掉异常分支的等待并不重建原先那个不交还事件循环的形态。文案已改写，现在只声称
  「异常路径必须等待」这条约定被破坏。
- 你 Q5 说「81→82 尚未独立证明」：已补对照输入。把抑制注解加回去跑 pyright = 82 warnings，
  精确诊断 `background_task_manager.py:358:83 reportUnnecessaryTypeIgnoreComment`；删回 = 81。

最小读取面（五项，请只读这些）：
1. `git --no-pager diff --no-color 8ace89c1 85d2c18c -- . ':(exclude)_bmad-output'`（本轮增量，仅测试文件）
2. `git --no-pager diff --no-color 08100483 85d2c18c -- . ':(exclude)_bmad-output'`（本卡全部代码改动，3 文件）
3. `backend/app/services/background_task_manager.py` 的 `start_cleanup_scheduler` = :339-377
   （内嵌 `cleanup_loop` = :342-369；`cleanup_old_tasks` = :306-337，本卡未改）
4. `backend/app/config.py` :725-735（新字段，`TASK_CLEANUP_INTERVAL_SECONDS` 在 :730）；
   :640-655 是另一张卡 T10-E 的 MEMORY_RETRY 段，本卡不得落 hunk，供你核不重叠
5. `backend/tests/unit/test_background_task_manager.py` 的 `TestCleanupScheduler` 类全文
   （同文件前半的 `TestContextVarInheritance` 与 autouse fixture 是既有内容，本卡未改）

裁判证据只读目录：`_bmad-output/审查/evidence-tail-cleanup/`（`README.md` 标注权威存档；
`e-negctl-r2-*.txt` 是本轮四个负控输入；`h2-pyright-81vs82-control-*.txt` 是 81/82 对照输入）。

## ② 作者自述，请独立核对

- 生产代码本轮零改动（判据：上面第 1 项 diff 只应出现测试文件）。
- 四个负控输入各自红在**指定**断言，且只红该条：
  1 改名 config 字段 → 根因门 + 两测守卫 `:198` `:259`；
  2 删异常分支的 await → 只有 `:307`（测试 A 仍绿）；
  3 把该 await 换成 `asyncio.create_task(...)` → 只有 `:307`，实测事件序列出现
    `['sleep-enter','sleep-enter','sleep-exit']`；
  4 cleanup 后注入 break → `:242` 与 `:317` 同时红。
  四段跑前跑后三文件 `shasum -a 256` 逐字节相同。
- `pyright app`（cwd=backend/）= `0 errors, 81 warnings, 0 informations`。
- `tests/unit` 目录级对 64 条既有红基线 diff 为空。
- ruff：三文件 `ruff check` 通过（**生效配置是 `backend/ruff.toml`，select 只有
  E9/F63/F7/F82 —— F401 与 isort 都没开**，所以用 F821 做验伪锚，实测 rc=1）；
  `config.py` 的 `ruff format --check` 仍 clean；另两文件的 format 漂移逐 hunk 证为
  08100483 既有（对应关系写在 `i2-ruffformat-drift-attribution-final-*.txt`）。

## ③ 请按重要性排序回答的问题

0. 本轮新增的四条断言（`:237` 首轮序列、`:242` A 轮数、`:307` enter/exit 四事件、`:317` B 轮数）
   有没有哪一条在生产代码被改坏时仍会保持绿？即仍存在的**门未覆盖的路径**。
1. `sleep-enter` / `sleep-exit` 这套记法本身是否可靠？spy 在终止那次抛 `CancelledError`、
   不记 exit，这个不对称会不会让某种真实改坏的形态反而不被拦下？
2. 测试 A 的 `stop_after = 3`、测试 B 的 `stop_after = 5` 是否足以支撑「循环继续周期运行」
   这个结论？还是只证明了「至少跑了 N 轮」而被当成了更强的结论？
3. 对 `asyncio.sleep` 的 monkeypatch 在本轮改动后，是否引入了新的跨测试影响
   （例如 `real_sleep(0)` 的额外让出改变了同 session 其它异步测试的调度）？
4. 生产侧仍未覆盖的风险：`cleanup_loop` 里是否还有任何一条能在不经过 `await` 的情况下
   回到循环顶的路径？异常分支自身再抛异常时的行为是否可接受？
5. `default=3600` 与 `cleanup_old_tasks(max_age_hours=24)` 的量级是否自洽？
   异常后等待 `2 × interval` 才重试（异常分支等待 + 循环顶等待）这一点是否需要在文档里写明？
6. 本卡 diff 是否严格落在三文件、且 `config.py` 的 hunk 与 `:640-655` 无交集？

## ④ 输出格式

逐条列 BLOCKER / HIGH / MEDIUM / LOW，每条给 `file:line` 与一句复现思路。
描述问题请用这四类说法：「负控输入」「对照输入」「未被拦下的输入」「门未覆盖的路径」。
没有问题的档位明确写「无」。最后给一段总评。

## ⑤ 边界

只读；不连数据库；不跑真实定时任务；不评 T5-B~E 的面；不要求本卡改
`cleanup_old_tasks` / `create_task` / `stop_cleanup_scheduler` 本体；
不要求本卡处理仓库既有的 ruff-format 漂移（主干既有，另有卡负责）。
