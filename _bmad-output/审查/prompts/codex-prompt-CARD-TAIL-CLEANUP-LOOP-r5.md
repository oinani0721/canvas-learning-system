你是独立复核者，这是同一张卡的第 5 轮，也是本卡轮次上限：CARD-TAIL-CLEANUP-LOOP
[BATCH-2026-09-11-第十四批]。只读审查，不改任何文件、不连数据库、不跑真实定时器、
不评本车道其它卡（T5-B~E）的面。

## ① 背景 + 本轮变了什么 + 最小读取面

树根：/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs
08100483（B14_BASE）→ r1 审 8ace89c1 → r2 审 85d2c18c → r3 审 e68c50d3 → r4 审 19c96f0e →
**本轮审 970f7eaa（当前 HEAD）**

卡的目标不变：`cleanup_loop` 的 `while True` 里唯一 yield 点是
`await asyncio.sleep(settings.TASK_CLEANUP_INTERVAL_SECONDS)`；`Settings` 原本没有该字段，
参数求值先于 `await` 抛 AttributeError，被同 try 的 `except Exception` 接住、无等待即回到
循环顶 ⇒ CPU 紧循环。修法 = 补字段（default=3600, gt=0）+ 删已多余的类型层抑制注解 +
异常分支补等待。**生产代码自 8ace89c1 起逐字节未变**；r2~r5 只改测试文件。

对你 round-4 两条 LOW 的处置，两条都接受并已落地：

- **LOW-1**（返回值从 0 改 3 等于换掉一种覆盖，`if not await cleanup(): break` 漏网）：
  你说得对。`cleanup_old_tasks` 返回「本轮清掉几个」，0 与非零都是正常值，所以门必须两种
  都喂。现在成功清理的返回值在一轮内 **0 与 3 各出现一次**。负控 7（truthy 方向
  `if await cleanup(): break`）与**新增负控 8**（falsy 方向 `if not await cleanup(): break`）
  各钉一种，实测两者都红在 `:269` + `:368`。
- **LOW-2**（测试 B 局部 docstring 仍声称能拦「没有就地 await」，与类级边界冲突）：已收窄为
  「拦得住删掉等待 / **直接** create_task 后回循环顶这两种（负控 2 / 3 各实测一种）」，
  并指回类 docstring「本类不证明什么」第 3 条。
- 你提的证据边界（旧 ruff 存档的 enabled 列表在 F722 处截断）已补：`i-ruff-r5-*.txt` 落
  **完整** `linter.rules.enabled` 列表 + 直接判据（F401 命中 0 / I001 命中 0 / F821 命中 1）。

最小读取面（请只读这些）：
1. `git --no-pager diff --no-color 19c96f0e 970f7eaa -- . ':(exclude)_bmad-output'`（本轮增量，仅测试文件）
2. `git --no-pager diff --no-color 08100483 970f7eaa -- . ':(exclude)_bmad-output'`（本卡全部代码改动，3 文件）
3. `backend/app/services/background_task_manager.py` 的 `start_cleanup_scheduler` = :339-377
   （`cleanup_loop` = :342-369；`cleanup_old_tasks` = :306-337，本卡未改）
4. `backend/app/config.py` :725-735（新字段在 :730）；:640-655 是 T10-E 的 MEMORY_RETRY 段，
   本卡不得落 hunk，供你核不重叠
5. `backend/tests/unit/test_background_task_manager.py` 的 `TestCleanupScheduler` 类全文

证据只读目录：`_bmad-output/审查/evidence-tail-cleanup/`（`README.md` 是索引与边界声明；
`e-negctl-r5-*.txt` 是本轮 8 个负控输入；`i-ruff-r5-*.txt` 是完整 ruff 规则集）。

## ② 作者自述，请独立核对

- 本轮生产代码零改动（判据：读取面第 1 项 diff 只应出现测试文件）。
- 八个负控输入各自红在**指定**断言：1 → 根因门 + `:210`/`:290`；2 → `:339`；3 → `:339`；
  4/5/6/7/8 → `:269` + `:368`。整批跑前跑后三文件 `shasum -a 256` 逐字节相同
  （**整批一组，不是每段一组**）。
- `pyright app`（cwd=backend/）= `0 errors, 81 warnings, 0 informations`。
- `tests/unit` 目录级对 64 条既有红基线 diff 为空。
- ruff：三文件 `ruff check` 通过；生效配置 `backend/ruff.toml`，完整 enabled 列表已落档。

## ③ 请按重要性排序回答的问题

0. 还有没有**未被拦下的输入** —— 生产被改坏而两测仍绿？若有，给出写法与它应落在哪一行，
   并说明它是否属于本卡范围（消除忙循环 + 异常路径必须等待 + 调度周期性）。
1. 测试类 docstring 的 4 条「本类不证明什么」与两个测试的局部 docstring，现在是否**彼此一致
   且如实**？还有没有任何一处声称强于证据？
2. 成功清理返回值「一轮内 0 与 3 各一次」这个安排，会不会引入新的脆弱性
   （例如序列一旦变化，返回值的轮转就错位）？
3. 生产侧：`cleanup_loop` 是否还有能不经过 `await` 回到循环顶的路径？
4. 本卡 diff 是否严格落在三文件、`config.py` hunk 与 `:640-655` 无交集？
5. 还有没有本卡**自述但未被证据支撑**的说法？

## ④ 输出格式

逐条列 BLOCKER / HIGH / MEDIUM / LOW，每条给 `file:line` 与一句复现思路。
描述问题请用这四类说法：「负控输入」「对照输入」「未被拦下的输入」「门未覆盖的路径」。
没有问题的档位明确写「无」。最后给一段总评。

## ⑤ 边界

只读；不连数据库；不跑真实定时任务；不评 T5-B~E 的面；不要求本卡改
`cleanup_old_tasks` / `create_task` / `stop_cleanup_scheduler` 本体；
不要求本卡处理仓库既有的 ruff-format 漂移（主干既有，另有卡负责）。
