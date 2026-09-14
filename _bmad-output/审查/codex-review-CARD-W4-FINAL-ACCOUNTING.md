> 批次: BATCH-2026-09-11-第十四批 · 车道 T9 · 卡 CARD-W4-FINAL-ACCOUNTING round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-W4-FINAL-ACCOUNTING.md)"`
> 审查绑定: `5e4d10cf`（= 当时 HEAD，亦为最终 HEAD 的代码面；`git diff --stat --no-color 5e4d10cf HEAD -- . ':(exclude)_bmad-output'` 为空）
> 会话头自证（抄 .stderr 含 codex 版本行 / `model:` 行 / `reasoning effort` 行，括注行号；stderr 本身不入库）:
> `:4 OpenAI Codex v0.153.3` / `:7 model: gpt-6-astra` / `:11 reasoning effort: ultra`

---

本次三行修法成立：新增 `try` 包住完整的落盘失败 `print`，没有改动结账判定和强制退出。**未发现本次改动新增的 BLOCKER/HIGH。** 但现有判据仍有以下证据缺口。

**BLOCKER：0 条。**

**HIGH：0 条。**

**MEDIUM：1 条。**

- **M1｜缺少自动阻断回归。** [three-run-abc.py:59](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-w4final/three-run-abc.py:59) 仅打印结果，没有断言或失败退出；改前存档中的 A 子进程为 `rc=0`，判据脚本自身仍为 `rc=0`。**观察思路：**删除新增保护作为负控输入，人工能看见红结果，但自动执行者仍会收到成功状态。④ 应移交 T9-B：增加 A 格契约用例，断言计数 `1/1`、子进程 `rc=3`，并确认负控输入能使该用例失败；本卡不扩改契约文件。

**LOW：3 条，均属判据或证据局限。**

- **L1｜AST 判据会放过未受保护的结构。** [ast-protected.py:17](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-w4final/ast-protected.py:17) 只判断 `print` 是否落在整个 `try` 的行号范围，以及是否存在 `except BaseException`，没有确认它位于受保护的 `try.body`。**观察思路：**把落盘失败 `print` 移入该 `try` 的 `finally`，作为负控输入；我在内存中复算得到仍为 `protected`，但该处异常不会被同一个 `except` 接住。当前实际三个 `print` 均位于正确的 `try.body`，所以此缺口不推翻本次修法。

- **L2｜① rc=3 尚无退出调用点的直接证据。** [three-run-abc.py:46](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-w4final/three-run-abc.py:46) 只保留返回码和退出前计数，没有记录执行到哪个退出调用点。单 hunk、A 格负控翻转及 [live_port_guard.py:1522](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/live_port_guard.py:1522) 的控制流，**强支持**最终执行 `:1538`，但不能称为运行时排他证明。`CHILD-JSON` 已输出，至少排除了合成事件发生当时就提前退出。**观察思路：**后续回归补充目标回调及 `:1538` 调用点的执行记录，同时保留真实退出调用。

- **L3｜② 真实连接入口的记账等价尚未核实。** [three-run-abc.py:30](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-w4final/three-run-abc.py:30) 使用合成事件且首参为 `None`；读取面没有审计处理器、`record` 或 `finalize_and_snapshot` 的实现。现有证据覆盖的是：**合成审计事件 → 退出前 `late_snapshot()` 计数为 `1/1` → 组合故障下最终返回码**，不能据此确认真实入口走完全相同的分支，也不能把退出前快照当作最终快照的直接观测。**观察思路：**后续获准读取相关实现后，比较真实事件与合成事件两种对照输入是否汇入相同处理器、参数判断和记账分支；目前结论是“未证明等价”，不是“已证明不等价”。

对其余问题的直接回答：

**⓪ 保护范围：**[live_port_guard.py:1513](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/live_port_guard.py:1513) 整个表达式都在保护内，包括字符串格式化、`exc!r` 和 stderr 输出。这里同步抛出的 Python 异常，包括 `BrokenPipeError`、关闭文件的 `ValueError`、替换后的 stderr 方法抛出的 `BaseException` 子类，都会被接住。三跑实际只覆盖了关闭的 `StringIO`。这不等于整个函数的所有路径都有保护，也不能保证阻塞、不返回或直接终止进程的输出实现仍能走到末行。

**③ 可观测性：**“落盘失败仍会尝试说话”成立，“保证运维看见”不成立。A 格可以降级到**账本不可写、错误文字不可见，仅剩非零退出状态**。新增保护吞的是报告异常；发布异常本来已经由外层 `except Exception` 接住。它没有新增“落盘失败本身必须非零退出”的规则，也没有删除原有规则。对本卡“未结账不能以零退出”的目标，这个取舍可接受，并与 [live_port_guard.py:1536](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/live_port_guard.py:1536) 的既有注释一致。另，三跑没有保存 stderr，因此存档没有直接证明 B 格的错误文字实际可见。

**⑤ 迟到路径：未评估。** `_rewrite_ledger_after_late_record` 等实现不在指定读取范围内，不能认定它们存在同型问题，也不能宣布已全部排除。

复核仅使用指定文本及内存 AST 对照，未修改文件、未运行三跑或 pytest、未连接端口。存档中的红→绿→负控回红及首尾哈希一致已核对；但负控档案写的是“与 HEAD blob 相同”，没有绑定当时 HEAD 的 SHA，因此未独立确认其“与 `08100483` 逐字节相同”的执行记录；`151 passed` 也不在允许读取的证据中，未予背书。
