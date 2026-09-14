你是独立复核者，这是同一张卡的第 3 轮：CARD-TAIL-CLEANUP-LOOP [BATCH-2026-09-11-第十四批]。
只读审查，不改任何文件、不连数据库、不跑真实定时器、不评本车道其它卡（T5-B~E）的面。

## ① 背景 + 本轮变了什么 + 最小读取面

树根：/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs
基准 08100483（B14_BASE）→ r1 审 8ace89c1 → r2 审 85d2c18c → **本轮审 e68c50d3（当前 HEAD）**

卡的目标不变：`cleanup_loop` 的 `while True` 里唯一 yield 点是
`await asyncio.sleep(settings.TASK_CLEANUP_INTERVAL_SECONDS)`；`Settings` 原本没有该字段，
参数求值先于 `await` 抛 AttributeError，被同 try 的 `except Exception` 接住、无等待即回到
循环顶 ⇒ CPU 紧循环。修法 = 补字段（default=3600, gt=0）+ 删已多余的类型层抑制注解 +
异常分支补等待。**生产代码自 8ace89c1 起逐字节未变**，r2/r3 只改测试文件。

对你 round-2 三条 LOW 的处置：

- LOW-1（调用次数不能证明不同周期；后续周期间隔未钉住）：**接受并修**。你给的两种未被拦下的
  输入都实测复现了。现把 A（`:250`）与 B（`:345`）的断言升级为**整段事件序列精确比对**，
  元组里带每次 sleep 的 delay 值。新增两个负控输入逐条验证：
  负控 5 =「首轮等配置间隔、之后各轮 `sleep(0)`」→ `:250` 与 `:345` 同时红；
  负控 6 =「一轮里连做两次 cleanup 后退出」→ `:250` 与 `:345` 同时红。
  异常分支那次等待的秒数**刻意不钉死等于配置间隔**（卡文契约是「> 0 即可，车道可换独立常量」），
  它只由 `:325` 的 `> 0` 断言约束。
- LOW-2（enter/exit 配对不能普遍证明 await 依赖 —— 你给的 create_task + `loop.call_soon`
  检查点写法能凑出精确四事件）：**rejected 并登记**。理由：要拦住那一类需要对协程间依赖做
  追踪，与本卡范围不成比例；已在测试类 docstring 的「本类不证明什么」里如实写明这条边界，
  不再声称「四事件 = 证明了 await 依赖」。若你认为这个理由不成立，请明确说明并给出档位。
- LOW-3（文案仍写「错误会被立刻重试」）：**接受并改**，现写「失败后只剩循环顶那一次等待，
  不是立刻重试，但『异常路径必须等待』这条约定没了」。
- 你提的证据边界两条已落实：evidence `README.md` 已索引 r2/r3；`shasum` 是**整批前后各一组**
  这一点已写进 README（不是每段一组）。ruff 生效配置一条见下面 ②。

最小读取面（请只读这些）：
1. `git --no-pager diff --no-color 85d2c18c e68c50d3 -- . ':(exclude)_bmad-output'`（本轮增量，仅测试文件）
2. `git --no-pager diff --no-color 08100483 e68c50d3 -- . ':(exclude)_bmad-output'`（本卡全部代码改动，3 文件）
3. `backend/app/services/background_task_manager.py` 的 `start_cleanup_scheduler` = :339-377
   （`cleanup_loop` = :342-369；`cleanup_old_tasks` = :306-337，本卡未改）
4. `backend/app/config.py` :725-735（新字段在 :730）；:640-655 是 T10-E 的 MEMORY_RETRY 段，
   本卡不得落 hunk，供你核不重叠
5. `backend/tests/unit/test_background_task_manager.py` 的 `TestCleanupScheduler` 类全文
   （同文件前半的 `TestContextVarInheritance` 与 autouse fixture 是既有内容，本卡未改）

证据只读目录：`_bmad-output/审查/evidence-tail-cleanup/`（`README.md` 是索引与边界声明；
`e-negctl-r3-*.txt` 是本轮 6 个负控输入；`h2-pyright-81vs82-control-*.txt` 是 81/82 对照输入）。

## ② 作者自述，请独立核对

- 本轮生产代码零改动（判据：读取面第 1 项 diff 只应出现测试文件）。
- 六个负控输入各自红在**指定**断言：1 → 根因门 + `:198`/`:268`；2 → `:316`；3 → `:316`；
  4 → `:250`+`:345`；5 → `:250`+`:345`；6 → `:250`+`:345`。
  整批跑前跑后三文件 `shasum -a 256` 逐字节相同（**整批一组，不是每段一组**）。
- `pyright app`（cwd=backend/）= `0 errors, 81 warnings, 0 informations`；
  81↔82 已由对照输入独立证明，第 82 条的精确诊断是
  `background_task_manager.py:358:83 - Unnecessary "# pyright: ignore" rule: "reportAttributeAccessIssue"`。
- `tests/unit` 目录级对 64 条既有红基线 diff 为空。
- ruff：三文件 `ruff check` 通过。**生效配置是 `backend/ruff.toml`，`select = ["E9","F63","F7","F82"]`**
  —— 仓根 `ruff.toml`（`select = []`）与 `pyproject.toml` 的 `[tool.ruff.lint]` 都被它遮蔽，
  所以 F401 与 isort(I) 在 `backend/**` 上**没有启用**，卡文模板给的 F401 验伪锚恒不触发，
  改用启用集里的 F821 做锚（实测 rc=1）。这条覆盖面限制已登记，不主张 `ruff check` 覆盖了风格规则。
- `config.py` 的 `ruff format --check` 仍 clean；另两文件的 format 漂移逐 hunk 证为 08100483 既有。

## ③ 请按重要性排序回答的问题

0. 升级后的整段序列比对（`:250` / `:345`）是否仍有**未被拦下的输入** —— 即生产被改坏而两测仍绿？
   若有，请给出具体写法与它会落在哪一行。
1. 整段序列精确比对是否**过紧**：有没有合理的生产改动（不是改坏）会被它误红？
   若有，这属于可接受的回归门代价还是应当放宽？
2. 异常分支等待秒数不钉死（只断言 > 0）这个处置，与「本卡契约允许独立常量」是否自洽？
3. 测试类 docstring 里那段「本类不证明什么」的边界声明，是否已覆盖 r2-LOW-2 那类形态？
   有没有仍在**声称过强**的措辞？
4. 生产侧：`cleanup_loop` 是否还有任何能在不经过 `await` 的情况下回到循环顶的路径？
   异常分支自身再抛异常（例如 logger 或配置求值失败）时的行为是否可接受？
5. 本卡 diff 是否严格落在三文件，且 `config.py` 的 hunk 与 `:640-655` 无交集？
6. 还有没有本卡**自述但未被证据支撑**的说法？

## ④ 输出格式

逐条列 BLOCKER / HIGH / MEDIUM / LOW，每条给 `file:line` 与一句复现思路。
描述问题请用这四类说法：「负控输入」「对照输入」「未被拦下的输入」「门未覆盖的路径」。
没有问题的档位明确写「无」。最后给一段总评。

## ⑤ 边界

只读；不连数据库；不跑真实定时任务；不评 T5-B~E 的面；不要求本卡改
`cleanup_old_tasks` / `create_task` / `stop_cleanup_scheduler` 本体；
不要求本卡处理仓库既有的 ruff-format 漂移（主干既有，另有卡负责）。
