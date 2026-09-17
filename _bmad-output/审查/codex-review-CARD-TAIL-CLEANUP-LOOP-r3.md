复核绑定 `e68c50d35c0f58e0d783e951f6f81bd4cc97a7cc`。结论：**B0 / H0 / M0 / L2**。

全程只读，未连接数据库、未运行真实定时任务。下述输入通过内存提取生产函数与原测试断言验证，未运行完整 pytest。

- **BLOCKER：无。**
- **HIGH：无。**
- **MEDIUM：无。**

**LOW-1：门未覆盖的路径——成功清理返回非零时的周期延续。**

位置：[test_background_task_manager.py:225](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/unit/test_background_task_manager.py:225)、同文件 `:297`。

两测的成功清理都固定返回 `0`。在生产 [background_task_manager.py:358](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/services/background_task_manager.py:358) 放入以下**未被拦下的输入**，两测仍绿：

```python
if await self.cleanup_old_tasks():
    break
```

复现结果：原两测均通过，包括 `:250`、`:345`；实际清理数量一旦大于零，调度器便永久退出。把两测的成功返回值改成 `1` 作为**对照输入**，当前生产仍绿，上述输入分别红在 `:250`、`:345`。覆盖它不需要修改 `cleanup_old_tasks` 本体。

**LOW-2：协程依赖边界实际未登记，文案仍声称过强。**

位置：[test_background_task_manager.py:189](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/unit/test_background_task_manager.py:189)，另见 `:184-186`、`:260-266`。

“本类不证明什么”只有等待数值与真实定时器两条，**没有“不证明 await 依赖”**；`:266` 仍声称能拦住“没有就地 await”。

复现思路：将生产 `:369` 换成以下**未被拦下的输入**：

```python
asyncio.create_task(asyncio.sleep(settings.TASK_CLEANUP_INTERVAL_SECONDS))
loop = asyncio.get_running_loop()
checkpoint = loop.create_future()
loop.call_soon(checkpoint.set_result, None)
await checkpoint
```

两测仍绿，包括整段序列比较。检查点足以让 spy 完成，却没有等待独立任务中的真实正数间隔。

**接受不增加协程依赖追踪的范围理由，档位维持 LOW；但“已如实声明边界”的自述不成立。**

其余问题逐项结论：

| 问题 | 结论 |
|---|---|
| **1．精确序列是否过紧** | 有合理误红：在生产 `:358` 清理后增加 `await asyncio.sleep(0)`，仍保持配置间隔和周期清理，却分别红在 `:250`、`:345`。全局 spy 将额外让出也计入事件和终止次数。属于当前窄回归门可接受的代价，本轮无需放宽。 |
| **2．异常等待只断言 > 0** | 自洽。`:325` 约束正数，`:335-336` 使用观测到的异常等待值，允许独立常量。 |
| **4．生产循环路径** | 当前没有发现不经过等待便返回循环顶的路径：正常经过 `:357`，捕获普通异常后经过 `:369`，取消则退出。异常分支里的 logger、配置求值或等待再次抛异常，会向外传播并终止协程，不会被同一个 `except` 重新接住形成紧循环。就本卡目标可接受，但意味着该次调度任务停止。 |
| **5．范围** | 排除 `_bmad-output` 后，全卡严格只有指定三文件；r3 只有测试文件。两生产文件自 `8ace89c1` 起无差异。config 新增区位于 `:725-735`，与 `:640-655` 无交集。 |
| **6．证据支持度** | 除 LOW-2 的自述不符外，主要结果有支持；需保留下面的记录边界。 |

证据核对结果：

- 六个**负控输入**均记录了指定测试断言失败；整批前后三文件 SHA 与当前文件一致。[r3 记录](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/_bmad-output/审查/evidence-tail-cleanup/e-negctl-r3-20260914T204116.txt:4)
- 负控输入 1 的 **r3 正文只展示两测守卫红**；独立根因门的红及返回码在旧记录中。生产文件未变，可以沿用，但不能称 r3 日志独立展示了本轮根因门重跑。[旧根因门记录](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/_bmad-output/审查/evidence-tail-cleanup/e-negctl-final-20260914T200649.txt:11)
- 81→82→81 的**对照输入**及精确 `:358:83` 诊断有记录；重新提取 unit 日志得到 **35 FAILED + 29 ERROR**，与既有 64 条基线集合一致。
- ruff 生效配置、F821 锚和 format 既有归因有存档支持。这里确认的是日志证据，未独立重跑这些命令；六段负控记录也没有保存每段完整改动代码。

总评：**当前生产修复成立，r2-LOW-1 的两种输入已被升级后的门拦住。剩余两项 LOW 分别是非零清理结果的覆盖不足，以及协程依赖边界声明未落实；没有发现需要扩大本卡生产修改范围的问题。**
