复核绑定 **`970f7eaa454ae71f83dbd4bd9cfca010e8d98a64`**。全程只读；动态核验仅在内存抽取指定代码，未导入应用、连接数据库或运行真实定时任务。

**BLOCKER：无。**  
**HIGH：无。**  
**MEDIUM：无。**  
**LOW：2 项，均为测试门覆盖不足，当前生产代码没有对应缺陷。**

1. **配置约束存在未被拦下的输入。**  
   位置：[config.py:732](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/config.py:732)、[test_background_task_manager.py:255](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/unit/test_background_task_manager.py:255)。  
   删除 `gt=0`、保持默认 3600，两测仍绿；抽取该字段的 Pydantic 对照输入则由拒绝 `0/-1` 变成接受。另将 `:731` 的默认值改为 `7200`，两测也仍绿，因为期望值来自同一运行时配置。**属于本卡范围**：默认值及正数约束都是本次修复内容。

2. **非 RuntimeError 异常属于门未覆盖的路径。**  
   位置：[background_task_manager.py:361](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/services/background_task_manager.py:361)、[test_background_task_manager.py:317](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/unit/test_background_task_manager.py:317)。  
   将生产代码改成 `except RuntimeError as e:`，两测仍绿；追加清理抛 `ValueError` 的对照输入后，该写法直接退出，当前代码则等待后继续。**属于本卡范围**：异常等待及调度周期性。上述结果均已隔离实证。

另外，已披露的**未被拦下的输入**在 r5 仍成立，不重复计为新问题：把生产 `:369` 替换为：

```python
asyncio.create_task(asyncio.sleep(settings.TASK_CLEANUP_INTERVAL_SECONDS))
loop = asyncio.get_running_loop()
checkpoint = loop.create_future()
loop.call_soon(checkpoint.set_result, None)
await checkpoint
```

当前两测仍绿。这个输入仍违反本卡“异常分支等待完成”的契约；可以明确不扩建测试门，但不能因此把行为判为卡外。

其余问题的核对结果：

- **① 文档边界：**四条边界与 B 新增的局部解释已经一致；开头的“就地 await”应理解为待测契约，不能视为两测通过所证明的事实。`:199` 的“不在本卡范围”应作上述区分。另 `:299` 尚留“下面的 `>= 2` 断言”旧指针，实际由 `:368` 的完整序列断言承担检查，验证能力没有因此减弱。
- **② 0/3 安排：**A 实际为 **3→0**，B 为 **0→3**，均各出现一次。A 的 `:244` 确有事件长度耦合；但当前序列漂移会被完整序列断言判红，未发现由此新增的未被拦下的输入。
- **③ 生产路径：**未发现不经过等待就回到循环顶的路径。正常路径经过 `:357`，异常路径经过 `:369`；取消会退出。异常处理自身再抛异常会退出协程，不会形成无等待回顶。
- **④ 范围：**确认排除 `_bmad-output` 后累计 diff 严格为三文件；本轮仅测试文件变化；生产两文件与 r1 相同。配置新增行仅 `:725–735`，与 `:640–655` 无交集。
- **⑤ 证据：**八个负控输入的存档断言位置全部吻合；整批前后哈希也与当前三文件吻合。64 条既有红基线集合一致；ruff 完整 enabled 列表支持 F401=0、I001=0、F821=1。**仍需保留限制：**负控存档没有逐段实际修改后的 diff；pyright 存档只有 `0/81/0、rc=0` 摘要，没有实际命令及 cwd。因此支持所存结果，不能称这些执行边界已被独立完整重放。

总评：**当前生产修复成立，r4 两条 LOW 的实质处置已落实；本轮新增两项 LOW 覆盖缺口，没有发现 BLOCKER/HIGH/MEDIUM。**按第五轮上限收束时，应保留这些明确边界，不能把两测通过表述为对所有本卡契约的完整证明。


