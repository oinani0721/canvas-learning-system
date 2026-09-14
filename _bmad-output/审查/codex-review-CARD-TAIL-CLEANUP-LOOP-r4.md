复核绑定 `19c96f0e`：**B0 / H0 / M0 / L2**。当前生产修复成立，测试仍有一处覆盖倒退、一处过强说明。

- **BLOCKER：无。**
- **HIGH：无。**
- **MEDIUM：无。**
- **LOW：两条。**

**LOW-1：只返回 `3`，撤掉了零次清理的对照输入。**

位置：[test_background_task_manager.py:240](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/unit/test_background_task_manager.py:240)、同文件 `:312`。

在生产 `background_task_manager.py:358` 放入以下**未被拦下的输入**：

```python
if not await self.cleanup_old_tasks():
    break
```

本轮两测仍绿；真实无过期任务时，清理返回 `0`，调度却会退出。将测试成功返回值恢复为 `0` 作为**对照输入**，精确红在 `:265`、`:360`。

因此，改为 `3` 没削弱事件断言本身，但把“零值输入”换成了“非零输入”，覆盖并非只增不减。同时保留两类输入才能兼顾负控 7。README `:77` 的“真实场景本就非零”也不能支持排除 `0`。

**LOW-2：类级边界已补，测试 B 的局部说明仍声称过强。**

位置：[test_background_task_manager.py:281](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/unit/test_background_task_manager.py:281)、同文件 `:332`。

`:281` 仍声称断言能拦住“没有就地 await”，与类级 `:194–199` 承认的边界冲突。复现思路：在生产 `:369` 使用已经列明的**未被拦下的输入**：

```python
asyncio.create_task(asyncio.sleep(settings.TASK_CLEANUP_INTERVAL_SECONDS))
loop = asyncio.get_running_loop()
checkpoint = loop.create_future()
loop.call_soon(checkpoint.set_result, None)
await checkpoint
```

两测仍绿，循环并不依赖那次正数等待完成。局部说明应限定为已验证的“直接 `create_task` 后回循环顶”这一**负控输入**。

本轮纯内存重放结果如下，提取原调度方法与测试断言、隔离初始化，没有改文件或运行真实定时清理；这不是完整 pytest 重跑：

| 输入 | 测试 A | 测试 B |
|---|---|---|
| 当前生产、当前测试 | 绿 | 绿 |
| 负控 7 | 红 `:265` | 红 `:360` |
| 零次清理即退出、当前测试 | 绿 | 绿 |
| 上述输入、成功返回 `0` 的对照输入 | 红 `:265` | 红 `:360` |
| `create_task`＋检查点 | 绿 | 绿 |

其余问题的结论：

- **Q1：**四条“不证明什么”逐项属实，没有把已经证明的性质写成没证明；但清单未涵盖上述零值输入，整体说明仍有 LOW-2 的冲突。无害 `sleep(0)` 会误红的代价也已如实写入。
- **Q3：**[当前循环](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/services/background_task_manager.py:342)没有不经过等待便重新回到循环顶的路径：正常路径经过 `:357`；异常后继续须经过 `:369`；取消则退出。异常分支的日志、参数求值或等待自身再抛异常，会终止协程，不会被同一组 `except` 再捕获成紧循环。对本卡消除忙循环的目标可接受，持续调度可用性并未因此得到保证。
- **Q4：**排除 `_bmad-output` 后，累计 diff 严格为指定三文件；本轮只有测试文件。生产两文件自 `8ace89c1` 起字节未变。配置新增 hunk 位于 `:725–735`，与 `:640–655` 无交集。
- **Q5：**存档正文支持七个负控的指定断言、根因门重跑、整批前后哈希、pyright `0/81/0`、64 条既有红基线差集为空，以及 ruff 三文件通过、F821 锚 `rc=1`、config format 通过。三文件当前哈希也与存档一致；没有扩大为每段中间态均独立绑定。

另保留一个证据限制：[ruff 设置输出:20](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/_bmad-output/审查/evidence-tail-cleanup/i-ruff-20260914T200503.txt:20)在 F722 后截断。配置路径有输出支撑，但完整 `select` 和 F401/isort 未启用仍不能在限定读取面内独立确认；F821 对照输入只证明该规则生效，不能证明完整规则集合。

总评：**当前生产实现未发现本卡阻断问题；round-4 已落实两项修订，但测试覆盖发生零值／非零值交换，局部证明措辞尚未统一。**上述两条 LOW 均限定于本卡测试与说明，无需扩展修改其它生产方法。


