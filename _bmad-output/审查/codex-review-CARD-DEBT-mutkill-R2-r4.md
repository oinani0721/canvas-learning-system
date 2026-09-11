**结论：不通过。发现 2 HIGH、2 MEDIUM、1 LOW；无 BLOCKER。** 复核绑定 `01ac27d08d6c78c5f44c49cf50b82d2376b4f0df`。以下区分静态可证问题与既有运行证据；未运行 harness、pytest 或修改文件。

[级别 HIGH] 参数 ID 的括号计数相等，仍不能证明 nodeid/reason 切分正确。
位置：[mutation_kill_identity.py:199](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u8-mutgates/backend/scripts/mutation_kill_identity.py:199)。
依据：实际检查只有 `nodeid.count("[") == nodeid.count("]")`，而第 185 行仍在首个可匹配的 ` - ` 处分隔。对以下**负控输入**：

```text
FAILED tests/x.py::test_x[case] - EXPECT[] - AssertionError: other
```

完整参数 ID 可以是 `case] - EXPECT[`；解析器却接受截断的 `test_x[case]`，把 `EXPECT[] - AssertionError: other` 当成 reason。截断部分括号数相等，三处解析和 `unparsed_failure_lines()` 都放行。若期望消息为 `EXPECT`，三套弱位置判据再遇到门内前提失败，就可以记成 KILLED，尽管真正 reason 不含期望消息。这是解析层问题，不属于 D-28 延期的断言绑定。
建议：校验整行切分的唯一性；无法唯一确定完整 nodeid 的记录进入 HARNESS-ERROR，不能只检查截断结果的括号数。保持不使用贪婪匹配或 `rsplit`。
**未验证**：真实 pytest 生成该参数 ID 的运行链，以及现有变异是否包含这种输入；上述解析结果由代码静态推出。

[级别 HIGH] g33 的保号包装会吞掉正常还原期间首次产生的信号退出。
位置：[g33_mutation_gates.py:443](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u8-mutgates/backend/scripts/g33_mutation_gates.py:443)。
依据：第 481 行正常还原进入包装，其 `try: restore_all()` 包含第 425 行的 `critical()`。期间收到信号后，共用模块第 865–869 行在出口调用 `_finish()`，先设置 `_finishing=True`，再抛 `SystemExit(130)`。这个**首次退出**被第 444 行 `except BaseException` 捕获；第 445 行检查时 `exiting()` 已为 True，于是打印 traceback 后返回，继续后续变异。此后 `_finish()` 第 811–815 行只记录并丢弃信号。
建议：在包装入口记录是否已经进入退出展开，只抑制已有退出过程中的二次还原异常；包装内部首次产生的 `SystemExit` 必须传播。将真实包装纳入临时文件信号负控。
现有信号负控调用自建还原循环，没有经过这个包装，不能反驳该控制流问题。

[级别 MEDIUM] g32cb 的保号函数没有接入实际 finally，二次还原错误仍会覆盖 131。
位置：[g32cb_mutation_gates.py:554](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u8-mutgates/backend/scripts/g32cb_mutation_gates.py:554)。
依据：第 337–353 行定义了 `_restore_active_or_keep_exit_code()`，但没有调用。第 553–555 行仍直接执行：

```python
with _GUARD.critical():
    target.write_text(src, encoding="utf-8")
    _ACTIVE_SNAPSHOT.clear()
```

信号回调还原持续失败、已经抛出 `SystemExit(131)` 后，这次直接写回再次抛异常，仍会替换退出码。round-3 第 3 项对本套尚未落地。
建议：在现有 `critical()` 内调用已定义的保号函数，替换直接写回与手动清表。真实信号叠加持续 I/O 故障的运行验证仍缺失。

[级别 MEDIUM] 处置表生成器漏掉新增的两种对照锚异常，会重新报出已撤销的 KILLED。
位置：[make_disposition_table.py:54](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u8-mutgates/_bmad-output/审查/evidence-mutkill-r2/make_disposition_table.py:54)。
依据：第 48–49 行先保存阶段 1 裁决，第 54–61 行只覆盖四种后续降档。g32b 第 2859 行新增的 `✗ 对照锚点异常, 跳过`、第 2917 行的 `✗ complete 对照锚点异常` 均不匹配；虽然 harness 第 2868、2919 行已降为 HARNESS-ERROR，生成器仍保留 KILLED。第 96 行声称“与全跑存档的六档计数交叉核对”，实际第 98–99 行只对自身解析结果计数、打印，没有比较运行汇总。
建议：补齐两种降档，并将解析后的完整 ID 集合、六档计数与最终汇总硬核对。
**最新 v5 没触发这两条路径，因此当前 39 行表不能据此判为已经错报。**

[级别 LOW] premise 筛只处理顶层 not，内层否定仍会误报“期望子进程成功”。
位置：[premise_anchor_screen.py:53](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u8-mutgates/_bmad-output/审查/evidence-mutkill-r2/premise_anchor_screen.py:53)。
依据：第 54–55 行仅排除整个断言表达式为 `UnaryOp(Not)`；随后第 56–64 行通过 `ast.walk(test)` 搜索任意 `returncode == 0`。该比较位于 `and` 的否定子表达式中时，仍返回 True，尽管该条件要求失败。第 17 行说明结果不自动改判，故影响限于筛选误报。
建议：遍历时保留否定极性；无法确定语义的表达式标为人工核验。**当前门是否存在这种布局未验证。**

其余问题的复核结果如下：

| 核对项 | 结论 |
|---|---|
| 语法不合法导致假杀 | 四套主变异均先编译，再落盘、跑门；编译失败进入 SYNTAX-INVALID。g32b 阶段 2 未编译属于已登记欠账，不能声称所有运行路径都已覆盖。 |
| g33 `--selfcheck-syntax` | 与主循环使用同一编译函数；旧 M15、新 M15、原文及前后 SHA 检查语义一致。它不证明全部 18 条变异。 |
| g33 HARNESS-ERROR 后继续 | 裁决保留在结果中，最终计数并返回 rc=2，没有因此被整体 PASS 掩盖；信号退出问题另见 HIGH。 |
| FAILED/ERROR 混排 | `failure_records()` 保留状态、重复记录；`exactly_one_failed()` 要求恰 1 FAILED、0 ERROR，两处对照已接入。实际 pytest／插件组合是否完整输出这些记录仍未验证。 |
| 对照锚异常撤销 KILLED | harness 内两处整改成立；处置表生成器遗漏如上。 |
| 合法参数化用例被保守拒绝 | **会。** 第 682–694 行遇到多条目标失败、仅部分 reason 命中时统一 HARNESS-ERROR，即使其中确有合法的目标位置＋消息组合。它避免猜配对，但没有实现精确配对。现有门是否触发未验证。 |

三个正则及摘要边界的实际行为是：

- `_SUMMARY_HEAD_RE` 要求完整的纯文本分隔线；多段 summary 只取第一段，没有唯一性检查。格式改变导致找不到时，rc=1 会报 HARNESS-ERROR。
- `_SUMMARY_TAIL_RE` **能识别**你列出的 `= 1 failed, 2 passed in 3s =`，但仅匹配统计前缀，不验证整条统计行。找不到尾行时直接读到 EOF，没有明确报错。
- `_LOC_RE` 不接受含空白的路径，只收符合 `.py:行号: 文本` 的行。全部漏掉会报 HARNESS-ERROR；部分漏掉没有完整性核对。
- `COLUMNS=1000` 已设置，但 `judge_surface_missing()` 没有检查 reason 是否被截断。上述尾行、位置部分漏失和截断问题仍属 #27 未闭合项；本轮没有插件／终端宽度矩阵证据。

位置锚方面，**启动前漂移检查确实可达**：g32b 第 2638–2641 行调用 `_check_expect_loc()`，指纹不存在或不唯一会退出 rc=2；运行判据第 590–594 行也存在“锚失效→HARNESS-ERROR”分支，但它不是所有提前返回路径都会执行的无条件检查。

指纹包含“函数／类作用域＋语句 AST”。普通注释、空行、保持同一 AST 的缩进调整不改变它；修改断言消息、交换 `a == b` 的两侧、修改所属函数名会改变它。把语句移入同一函数的其他分支，可能不改变该语句指纹，因此它不证明周围控制流语义不变。

`check_expect_loc_unique()` 的非空／豁免、恰一处命中、禁止 `file:` 三项检查均存在；同行并列最小语句另由运行判据拒绝。但它们**不证明所绑定语句就是变异意图要求的目标断言**。允许读取面的证据不足以独立重算当前 36 条语句的唯一性、位置来源和目标语义，仍标 **未验证**。

当前 39 条处置表与 v5 逐条日志吻合：**36 条位置绑定，其中 35 条最终 KILLED、M10 为 HARNESS-ERROR；3 条 UNBOUND；退役 0 条**。四套最终数字也与请求一致。五脚本 SHA-256 与 `run-code-state-20260909T135431.txt` 完全相同；该存档记录旧 HEAD 加 dirty 状态，证明范围是这五个文件，不能扩成运行时整树与最终 HEAD 一致。

第三方存证的顺序修复成立：g32b 先比较现盘内容，必要时存证，再还原并清表；`now==orig` 能覆盖“登记后尚未写盘”和“已经还原”。N3/N4/P2/N5 支持这些顺序对照，**不覆盖写到一半、真实信号与存证／日志／I/O 故障的组合**。N1/N2/P1/D 及 PYEOF 存档支持其列出的具体输入，不构成更广格式或时序保证。

对“十条被推翻”，**仍不能整体采信**：符号链接那条错误推翻已撤回，当前文件、目录链接均进入扫描错误；其余九条在允许读取面内缺各自原文和反证，只能保持未验证。

最终状态检查仍为上述 HEAD；工作树有两份未跟踪的本轮复核文档，与开始时相同，未读取或修改。
