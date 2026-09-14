你是独立复核者，这是同一张卡的第 4 轮：CARD-TAIL-CLEANUP-LOOP [BATCH-2026-09-11-第十四批]。
只读审查，不改任何文件、不连数据库、不跑真实定时器、不评本车道其它卡（T5-B~E）的面。

## ① 背景 + 本轮变了什么 + 最小读取面

树根：/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs
08100483（B14_BASE）→ r1 审 8ace89c1 → r2 审 85d2c18c → r3 审 e68c50d3 →
**本轮审 19c96f0e（当前 HEAD）**

卡的目标不变：`cleanup_loop` 的 `while True` 里唯一 yield 点是
`await asyncio.sleep(settings.TASK_CLEANUP_INTERVAL_SECONDS)`；`Settings` 原本没有该字段，
参数求值先于 `await` 抛 AttributeError，被同 try 的 `except Exception` 接住、无等待即回到
循环顶 ⇒ CPU 紧循环。修法 = 补字段（default=3600, gt=0）+ 删已多余的类型层抑制注解 +
异常分支补等待。**生产代码自 8ace89c1 起逐字节未变**；r2/r3/r4 只改测试文件。

对你 round-3 两条 LOW 的处置，两条都接受并已落地：

- **LOW-1**（两测成功清理固定返回 0，于是 `if await self.cleanup_old_tasks(): break`
  不被拦下）：成功清理改为返回 `3`。新增**负控 7** 用的就是你给的那段写法，实测现在
  精确红在 `:265` 与 `:360`。
- **LOW-2**（「已如实声明边界」这条自述不成立）：你核得对。round-3 的 commit message
  确实声称写了而实际没写。round-4 已真正落实：测试类 docstring 的「本类不证明什么」
  扩为 4 条，第 3 条明写「事件成对**不**证明协程依赖」，并把你给的
  `create_task` + `loop.call_soon` 检查点写法作为反例写进去；同时补记本门偏紧的代价
  （生产 cleanup 之后加一个无害的 `await asyncio.sleep(0)` 也会误红 —— 这是你 Q1 的答案）。
  evidence `README.md` 也把「自述与实际不符」这一笔如实记了下来。
- 你指出的记录边界也已补：负控 1 的**独立根因门重跑**这一轮进了 `e-negctl-r4-*.txt` 正文
  （r3 正文确实只有两测守卫红）。

最小读取面（请只读这些）：
1. `git --no-pager diff --no-color e68c50d3 19c96f0e -- . ':(exclude)_bmad-output'`（本轮增量，仅测试文件）
2. `git --no-pager diff --no-color 08100483 19c96f0e -- . ':(exclude)_bmad-output'`（本卡全部代码改动，3 文件）
3. `backend/app/services/background_task_manager.py` 的 `start_cleanup_scheduler` = :339-377
   （`cleanup_loop` = :342-369；`cleanup_old_tasks` = :306-337，本卡未改）
4. `backend/app/config.py` :725-735（新字段在 :730）；:640-655 是 T10-E 的 MEMORY_RETRY 段，
   本卡不得落 hunk，供你核不重叠
5. `backend/tests/unit/test_background_task_manager.py` 的 `TestCleanupScheduler` 类全文
   （同文件前半的 `TestContextVarInheritance` 与 autouse fixture 是既有内容，本卡未改）

证据只读目录：`_bmad-output/审查/evidence-tail-cleanup/`（`README.md` 是索引与边界声明；
`e-negctl-r4-*.txt` 是本轮 7 个负控输入）。

## ② 作者自述，请独立核对

- 本轮生产代码零改动（判据：读取面第 1 项 diff 只应出现测试文件）。
- 七个负控输入各自红在**指定**断言：1 → 根因门 + `:210`/`:283`；2 → `:331`；3 → `:331`；
  4/5/6/7 → `:265` + `:360`。整批跑前跑后三文件 `shasum -a 256` 逐字节相同
  （**整批一组，不是每段一组**；每段之间从副本 `cp` 回，中间态不落档）。
- `pyright app`（cwd=backend/）= `0 errors, 81 warnings, 0 informations`。
- `tests/unit` 目录级对 64 条既有红基线 diff 为空。
- ruff：三文件 `ruff check` 通过；**生效配置是 `backend/ruff.toml`，select 只有
  E9/F63/F7/F82**（F401 与 isort 未启用），故用 F821 做验伪锚（rc=1）。
  `config.py` 的 `ruff format --check` 仍 clean。

## ③ 请按重要性排序回答的问题

0. 还有没有**未被拦下的输入** —— 生产被改坏而两测仍绿？若有，给出写法与它应落在哪一行。
1. 测试类 docstring 现在那 4 条「本类不证明什么」是否**如实且完整**？
   有没有仍在声称过强、或者反过来把已经证明的东西写成没证明的？
2. 成功清理改成返回 `3` 这一处，会不会反过来削弱别的断言、或让某种改坏反而漏掉？
3. 生产侧：`cleanup_loop` 是否还有能不经过 `await` 回到循环顶的路径？
   异常分支自身再抛异常时协程终止、调度停摆 —— 对本卡目标是否仍可接受？
4. 本卡 diff 是否严格落在三文件、`config.py` hunk 与 `:640-655` 无交集？
5. 还有没有本卡**自述但未被证据支撑**的说法？（上一轮你抓到过一条，请继续按同样标准看）

## ④ 输出格式

逐条列 BLOCKER / HIGH / MEDIUM / LOW，每条给 `file:line` 与一句复现思路。
描述问题请用这四类说法：「负控输入」「对照输入」「未被拦下的输入」「门未覆盖的路径」。
没有问题的档位明确写「无」。最后给一段总评。

## ⑤ 边界

只读；不连数据库；不跑真实定时任务；不评 T5-B~E 的面；不要求本卡改
`cleanup_old_tasks` / `create_task` / `stop_cleanup_scheduler` 本体；
不要求本卡处理仓库既有的 ruff-format 漂移（主干既有，另有卡负责）。
