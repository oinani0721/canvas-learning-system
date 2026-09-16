> 批次: BATCH-2026-09-11-第十四批 · 车道 T3 · 卡 CARD-G6-8 round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G6-8-r2.md)"`
> 审查绑定: `6e2ee891a5e80d8742fda62cb6086a62af1ff2b4`（本轮送审时的 HEAD）
> 会话头自证（抄 .stderr 前三行含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（stderr :2） / `model: gpt-6-astra`（stderr :5） / `reasoning effort: ultra`（stderr :9）

---

**本轮不通过：BLOCKER 0 / HIGH 3 / MEDIUM 6 / LOW 1。**  
绑定最终 HEAD：`6e2ee891a5e80d8742fda62cb6086a62af1ff2b4`。

隔离环境中原版 **20/20**；下述六组完整对照副本也各 **20/20**。四个地盘文件均与 HEAD 一致，仓库未修改；未连库、未跑完整复习链。

1. **HIGH — `MISSING` 仍能作为一致值、甚至多数票放行。**  
   [g68_five_view_contract.py:603](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/scripts/g68_five_view_contract.py:603)  
   **对照输入：** 保留 B 板完整，仅删除 A 板 overview/picker 的 `bucket`；声明检查通过，两格成为 `MISSING`，结果仍为 `undeclared=[]`。进一步让 A 的声明值全部缺失、仅 inbox 日期正确，缺值多数派被跳过，唯一差异反而登记为 inbox 豁免。两组均已实跑。

2. **HIGH — inbox 日期仍未绑定实际入口的产出。**  
   [g68_five_view_contract.py:429](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/scripts/g68_five_view_contract.py:429)  
   这里只调 `parse_now()`，然后在契约内计算日期，未观察 `main()` 交给预览构建器的日期或最终产物。  
   **对照输入：** 分别把 inbox 副本的 `main()` 改成使用 `2099-01-01`、提前 `return 0`；两组都 **20/20**。谓词检查的是契约自行算出的日期，实际入口改日或零产物均不出现 `MISSING`。

3. **HIGH — AST 门仍放行普通间接字段读取。**  
   [g68_five_view_contract.py:396](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/scripts/g68_five_view_contract.py:396)  
   **对照输入：** `def local_due(n, t, key="fsrs_due"): return n.get(key) <= t`，静态门实跑返回 `offenders=[]`，函数却确实按字段值判断到期。模块常量键、`getattr(n, "fsrs_due")`、字典 `match` 读取也通过。直接字符串读取会判红，说明当前覆盖依赖语法形态。

4. **MEDIUM — M5 尚未钉住产出方身份。**  
   [test_g68_five_view_contract.py:153](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/tests/regression/test_g68_five_view_contract.py:153)  
   测试只检查数量下限和字段键集合。  
   **对照输入：** 同步删除 overview 的 `projection_day` 声明与输出，留下 picker/notification，整套仍 **20/20**。此外 `("picker", "picker")` 也满足数量检查；实跑可使该列只剩一个实际产出方，仍零分歧。

5. **MEDIUM — 让位检查未验证队列完整性，fixture 也未覆盖 snooze 的消费。**  
   [g68_five_view_contract.py:241](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/scripts/g68_five_view_contract.py:241)  
   **对照输入：** 提取层在检查前令 `ranked=[]`，整套仍 **20/20**。实际观察还确认：唯一被 snooze 的“板-未来”根本不在 `ranked`。因此当前新增检查不能证明 snooze 让位生效；这与 done/snooze 之间的先后无关。

6. **MEDIUM — 通知点名只检查宽松成员关系，未绑定实际推荐板。**  
   [g68_five_view_contract.py:758](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/scripts/g68_five_view_contract.py:758)  
   **对照输入：** 分别把提取到的通知标题设为 `None`、`📚 今日复习 · 板-未来`；两组均 **20/20**。后一块板虽然被矩阵认识，却不是当前推荐板，而且处于 snooze 状态。

7. **MEDIUM — M7 仍能把已通过断言的源码当成失败原因。**  
   [g68_negctl.py:293](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/_bmad-output/审查/evidence-g68/scripts/g68_negctl.py:293)  
   **对照输入：** 同一 nodeid 先执行 `assert True, "字段=display_day 面=review_overview"`，随后无关断言失败；真实 pytest 输出经现版判据得到 `FAILED=True、文本锚=True、ok=True`。缩到同一失败块仍未绑定真正失败的断言。

8. **MEDIUM — `failure_block()` 会误切同一异常栈。**  
   [g68_negctl.py:261](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/_bmad-output/审查/evidence-g68/scripts/g68_negctl.py:261)  
   **对照输入：** 测试调用 helper，由 helper 抛出含锚异常；标准 pytest traceback 的 `_ _ _ …` 帧分隔线被当成下一测试边界，真实异常锚被截掉。实跑得到 `FAILED=True、文本锚=False`。此项验证的是标准输出形态，未声称当前 15 段已发生该误判。

9. **MEDIUM — 恢复散列不一致没有影响退出码。**  
   [g68_negctl.py:310](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/_bmad-output/审查/evidence-g68/scripts/g68_negctl.py:310)  
   **对照输入：** 给最终核验提供不同的跑前/跑后 SHA，其余检查无失败；现版函数实跑打印 `⛔`，却仍返回 `0`。散列失败未计入 `bad`。

10. **LOW — 正常 `FAIL` 会丢弃计算期 stdout 诊断。**  
    [g68_five_view_contract.py:798](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/scripts/g68_five_view_contract.py:798)  
    **对照输入：** 计算期打印诊断标记，再制造通知日期分歧；实跑 `verdict=FAIL、rc=1`，stdout/stderr 均无该标记。同样标记后抛 `ContractError` 则会保留。当前只在异常路径回放缓冲区。

另外两点不单独判缺陷：**最终日期恰好正确但计算来源不同**，本身不能由结果契约区分；问题是第 2 条没有采集实际产出。`projection_day` 当前也不能仅因日期同源就认定整列恒真，它确实读取不同响应字段；同步缩减导致的覆盖丢失归第 4 条。

未原地运行会改写生产文件的 15 段负控脚本；以上负控判据结论来自指定脚本、纯函数实跑及真实 pytest 输出。


