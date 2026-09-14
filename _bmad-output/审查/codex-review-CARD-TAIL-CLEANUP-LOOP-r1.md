**总判定：本卡修复成立，可接受；发现 LOW 级测试覆盖与说明问题。** 以下针对 `8ace89c1`，仅做只读核对；新增的负控输入均为静态推演，未实际执行。

- **BLOCKER：无。**
- **HIGH：无。**
- **MEDIUM：无。**
- **LOW：以下三项。**

1. **测试 B 的“两次 sleep”不能充分证明异常分支自身等待了。**  
   位置：[test_background_task_manager.py:291](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/unit/test_background_task_manager.py:291)、`:297`。  
   **负控输入／复现思路：**把生产代码 `:369` 改成 `asyncio.create_task(asyncio.sleep(配置间隔))`；下一轮顶部 sleep 与分离任务中的 sleep 仍可共同满足计数，属于**未被拦下的输入**。另把退避参数改成任意正数常量，也能通过，因此“复用同一配置”也是**门未覆盖的路径**。当前生产代码确实用了正确的 `await` 和配置字段。

2. **两测没有验证成功清理后继续周期运行。**  
   位置：[test_background_task_manager.py:229](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/unit/test_background_task_manager.py:229)、`:283`、`:289`。  
   **负控输入／复现思路：**在生产 `await self.cleanup_old_tasks()` 后加入 `break`；A 首次成功后退出、B 失败恢复成功后退出，仍满足现有断言。这是**门未覆盖的路径**。此外，B 未检查 `gather(return_exceptions=True)` 的结果，不能仅凭事件断言证明最终没有非取消异常。

3. **负控 2 的失败说明夸大了实际含义。**  
   位置：[test_background_task_manager.py:293](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/unit/test_background_task_manager.py:293)。  
   **负控输入／复现思路：**仅删除异常分支的等待，下一轮仍会经过生产 `:357` 的顶部等待。因此“一次 sleep＝紧循环仍在”不成立；该负控证明的是“两次等待”的约定被破坏，并未重新制造原先“不交还事件循环”的缺陷。

对七个问题的具体判断：

**0．默认一小时与保留一天自洽。**  
[config.py:730](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/config.py:730) 确为 `int`、`default=3600`、`gt=0`。[background_task_manager.py:316](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/services/background_task_manager.py:316)、`:327` 按 `completed_at` 计算 24 小时截止。正常持续运行且清理成功时，有完成时间的终态任务约保留 **24～25 小时**，另加执行及调度延迟。刚完成／失败的任务主要因既有 24 小时保留策略而积累；每小时扫描只增加约一小时清理滞后。读取面没有任务量和大小证据，不能认定存在过量积累。

**1．大间隔确实会延迟重试，而且实际是两倍间隔。**  
[background_task_manager.py:369](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/services/background_task_manager.py:369) 等待后，还会执行 `:357`：失败后到下次清理约为 **`2 × interval`**，默认约两小时。**对照输入：**配置为一天，重试约在两天后。改成独立短等待 `b`，仍是 `interval + b`，不能单靠这一改动实现短时重试。本卡未规定恢复时限，故不应将新增独立常量作为阻断条件；若需要快速恢复，应一起明确重试时序。

**2．当前没有无等待回到循环顶的路径。**  
[background_task_manager.py:357](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/services/background_task_manager.py:357) 至 `:369`：正常路径经过顶部等待；异常路径经过异常分支等待；取消在 `try` 内触发 `break`。日志或异常分支等待自身再抛异常，会退出协程，不会回到循环顶。取消发生在异常分支时也会向外传播，不能泛称都由同级 `except CancelledError` 收尾。

**3．两段没有重叠或相邻 hunk 风险。**  
[config.py:725](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/config.py:725) 开始新增 11 行；MEMORY_RETRY 段在 `:640–655`，中间隔着 69 行。两 SHA 的代码 diff 恰为指定三文件，该段未被修改。

**4．monkeypatch 有临时共享影响，但未发现跨测试持久污染证据。**  
[test_background_task_manager.py:215](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/unit/test_background_task_manager.py:215)、`:276` 替换的是共享 `asyncio` 模块函数。**对照输入／复现思路：**在替换有效期间安排另一任务调用 `asyncio.sleep`，它也会占用 spy 计数，甚至收到 `CancelledError`。因此不能保证同期后台任务不受影响；pytest 的 monkeypatch 会在测试结束时恢复属性，两测也等待所建任务结束。

保留原函数并 `await real_sleep(0)` 恰当：避免递归，实际交还事件循环，且不等待正时长。**`sleep(0)` 会让出执行权**，不能与原先完全没有 yield 的紧循环等同。

**5．删除抑制注解在本次检查中正确。**  
[background_task_manager.py:357](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/services/background_task_manager.py:357) 访问的是已声明的 `int` 字段，无需保留原属性访问抑制。权威 [pyright 存档:3](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/_bmad-output/审查/evidence-tail-cleanup/h-pyright-app-final-20260914T200600.txt:3) 确为 `0 errors, 81 warnings, 0 informations`。不能据此保证任意其他配置均无诊断；允许读取的存档也没有“保留注解”的**对照输入**，所以 **81→82** 尚未独立证明。

**6．有未覆盖路径，见 LOW 1、2。**  
现有两条负控确实被指定断言拦下，但不能推广为所有等待、配置复用及持续运行回归都已覆盖。

存档核对还确认：两条测试通过；两条负控按自述失败；负控前后三文件 SHA256 相同，并与审查 commit 原始字节一致；目录级 **64 条既有红清单逐字节一致、无新增红，不能称为全绿**。

总评：缺失配置导致的 CPU 紧循环已被修复，改动范围符合约束，pyright 的本次验收数字成立。现有 LOW 项主要限制测试能证明什么，不构成本卡当前生产实现的阻断问题。
