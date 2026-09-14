复核结论：**B0 / H0 / M0 / L3**，绑定当前 `85d2c18c`。生产修复成立，测试仍有两类可复现的门未覆盖路径。

全程只读。下面的新增输入采用内存中提取的指定方法和原测试断言验证，sleep 全由 spy 接管；未导入应用、连接数据库或运行真实定时任务，也未完整重跑 pytest。

**BLOCKER：无。**  
**HIGH：无。**  
**MEDIUM：无。**

**LOW：**

1. **调用次数不能证明不同周期，后续周期的间隔也未钉住。**  
   位置：[backend/tests/unit/test_background_task_manager.py:237](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/unit/test_background_task_manager.py:237)，同文件 `:242、:317`。

   **未被拦下的输入**：把生产 `:358` 改为连续两次 `await self.cleanup_old_tasks()`，随后 `break`。实测 A/B 均通过，四条新增断言全部保持绿，但两次成功清理发生在同一轮，随后调度器退出。

   另一个未被拦下的输入是：循环顶首轮等待配置间隔，以后改为 `sleep(0)`；A/B 也均通过。门只检查首轮完整序列，后面统计调用数量，没有验证相邻清理之间的等待。

2. **成对事件不能普遍证明调度循环等待了异常分支的 sleep。**  
   位置：[backend/tests/unit/test_background_task_manager.py:307](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/unit/test_background_task_manager.py:307)，spy 位于同文件 `:271`。

   **未被拦下的输入**：把生产 `:369` 换成：

   ```python
   asyncio.create_task(asyncio.sleep(settings.TASK_CLEANUP_INTERVAL_SECONDS))
   loop = asyncio.get_running_loop()
   checkpoint = loop.create_future()
   loop.call_soon(checkpoint.set_result, None)
   await checkpoint
   ```

   实测 A/B 均通过。子任务中的 spy 经 `real_sleep(0)` 完成，再轮到调度循环继续，仍形成精确四事件；真实正数等待此时却尚未结束。门记录了事件顺序，没有证明父任务与该等待之间的依赖。

   作者提交的“直接替换成 create_task”负控输入确实被拦住；不能据此推广为所有未就地等待的形态都被覆盖。

3. **断言文案仍残留“错误会被立刻重试”的不准确描述。**  
   位置：[backend/tests/unit/test_background_task_manager.py:309](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/unit/test_background_task_manager.py:309)。

   **复现思路**：沿用删除异常分支 await 的负控输入，事件中仍有循环顶的等待。实际是少了一段异常后的等待，重试前仍等待一个 interval。“恢复原始紧循环”的夸大已修，这个括号尚未修准。

其余问题逐项结论：

- **Q1：终止时缺 exit 本身合理。** 它表示等待没有完成，不应伪造完成事件。当前问题是没有验证终止哨兵确实触发，以及事件没有证明等待依赖；上述两类输入均不依赖终止时缺 exit。
- **Q2：3/5 足以观察有限次重复，不能证明永久运行。** 当前甚至还存在“调用次数被当作周期数”的缺口。单纯增加次数不能解决 LOW-1；无需要求有限测试证明无限存活。
- **Q3：未发现本轮新增的跨测试污染。** `real_sleep(0)` 和全局 monkeypatch 在上一轮已经存在，本轮主要延长观测窗口。正常路径等待清理任务结束，monkeypatch 随用例恢复；本次未验证整个 session 的调度隔离。
- **Q4：当前生产代码没有不经过 await 就回到循环顶的路径。** [background_task_manager.py:357](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/services/background_task_manager.py:357) 的正常路径与 `:369` 的异常路径都会等待。异常处理中的日志、配置求值或 sleep 自身再抛异常，会向外传播并结束任务，不会紧循环；对本卡防紧循环目标可接受，但不代表自动恢复能力。连续失败、循环顶求值失败仍属于测试门未覆盖的路径。
- **Q5：量级自洽。** 每小时扫描与按完成时间保留 24 小时相容；健康运行时任务通常在完成约 24～25 小时后被清除，另加执行和调度开销。清理失败后确实要经过异常等待和下一轮顶部等待，默认约两小时才重试，建议在验收说明中明确。接受“不要求异常等待必须等于配置间隔”的处置。
- **Q6：范围通过。** 排除 `_bmad-output` 后，本轮增量只有测试文件；基准至本轮严格为三个文件。两个生产文件在上一轮、本轮及工作树的 SHA256 完全一致。config 新字段位于 `:730`，与 `:640–655` 无交集。

证据核对也支持四个指定负控输入的失败位置、pyright **81→82→81** 对照输入及精确诊断、64 条既有红基线集合不变。需要保留三点证据边界：哈希只有四项负控**整批前后**一组；README 尚未索引 R2；ruff 日志支持三文件检查通过和 F821 对照输入报错，但未提供有效配置展开，不能仅凭它独立证明其他规则全部未启用。

总评：本轮确实修好了上一轮提出的直接负控输入，生产侧未发现阻断问题；仍应把结论限定为已观察到的调度序列，避免将清理计数和事件配对解释为更强的周期性与等待依赖保证。


