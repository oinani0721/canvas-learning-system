**结论：不通过。确认 1 HIGH、3 MEDIUM、1 LOW；未发现 BLOCKER。**

复核绑定 `a1d6cb44d91a5a7dc75ddfcb36258962baf5b316`。全程只读，未运行或导入 harness、pytest、负控脚本。v4 起跑记录的五个脚本 SHA-256 与当前文件全部一致。当前有两个未跟踪审查文档，因此工作树并非完全干净；未读取其内容。

以下发现由代码控制流确定；是否已在本树实际触发，另行注明。

**[级别 HIGH] 参数 ID 内的 ` - ` 会被误切成 reason，使异常消息未命中的输入仍被记为 KILLED。**  
位置：[mutation_kill_identity.py:183](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u8-mutgates/backend/scripts/mutation_kill_identity.py:183)，同文件 212、344、621、625、655 行。  
依据：正则为 `^(?:FAILED|ERROR) (\S+?)(?: - (.*))?$`。对于以下负控输入：

```text
FAILED tests/x.py::test_x[case - EXPECT] - AssertionError: other
```

它会解析出截断的 nodeid `tests/x.py::test_x[case`，以及错误的 reason `EXPECT] - AssertionError: other`。整行匹配成功，故不进入 `unparsed_failure_lines`；`startswith(nodeid + "[")` 又接受这个截断 nodeid。三套弱位置调用中，只要失败位置在门文件，便能以参数 ID 里的 `EXPECT` 满足消息判据并返回 `KILLED`。这突破了“消息来自该次异常 reason”的承诺，与延期的具体断言绑定不同。  
建议：仅接受能够确定完整 nodeid/reason 边界的记录；歧义记录判 `HARNESS-ERROR`。不要仅换成贪婪匹配或 `rsplit`，reason 本身也可能包含分隔符。  
验证边界：当前门是否使用这种参数 ID、v4 是否触发，**未验证**。

**[级别 MEDIUM] “恰一条红”仍把同一 nodeid 的 FAILED／ERROR 两条记录合并成一条。**  
位置：[g32b_mutation_gates.py:2857](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u8-mutgates/backend/scripts/g32b_mutation_gates.py:2857)，同文件 2904 行；共用模块 183、312 行。  
依据：注释要求“FAILED 且无 ERROR”，实际检查的是 `len(_r0_fails) == 1`。`parse_failed_nodeids` 同时接受 FAILED／ERROR，再以 `set` 去重，丢失状态和记录数。因此，同一 nodeid 各有一条 FAILED／ERROR 的对照输入仍满足条件；`complete` 分支会进入“变异体单独即可杀”，而非 `HARNESS-ERROR`。  
建议：保留状态与记录数，两处共用“恰一条 FAILED、零条 ERROR、无未解析记录”的检查。  
验证边界：当前 pytest 配置是否实际产生该混排输出，**未验证**；输入经过上述判据的结果可静态确定。

**[级别 MEDIUM] 外层 finally 的再次还原异常仍可覆盖 RestoreGuard 选定的 131 退出码。**  
位置：[g32b_mutation_gates.py:2715](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u8-mutgates/backend/scripts/g32b_mutation_gates.py:2715)；同型位置为 g32cb:533、g32ccr1:419、g33:460／507。  
依据：共用模块 783 行执行 `raise SystemExit(self._exit_code + 1)`，随后调用方栈展开仍进入 `finally` 再次还原。若还原持续遇到同一 I/O 错误，例如 g32b:2492 的存证写入失败，快照尚未清空，第二次异常会替换 `SystemExit(131)`，最终按未捕获异常退出。保护 `traceback.print_exc()` 没有覆盖这条调用方路径。  
建议：统一处理退出展开期间再次还原的异常，保留还原尝试和诊断，同时保持失败退出码 131。  
验证边界：条件控制流已确认；实际 I/O 故障与信号组合**未运行验证**。

**[级别 MEDIUM] 阶段 2 对照锚异常只记 failures，仍保留阶段 1 的 KILLED。**  
位置：[g32b_mutation_gates.py:2837](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u8-mutgates/backend/scripts/g32b_mutation_gates.py:2837)，同文件 2893 行。  
依据：两处对照锚异常都只有 `failures.append(...)` 和 `continue`，没有修改 `_verdicts[tag]`。对照根本未施加时，原来的 `KILLED` 仍进入六档统计；与 2924、2932 行对“对照未跑成”的降档处理不一致。整份运行会失败，但逐条终裁仍说宽了。  
建议：对照锚异常时撤销原 `KILLED`，记 `HARNESS-ERROR` 并保留具体理由；同步处置表抽取。  
验证边界：最新 v4 输出未见该分支触发，不能据此断言当前 131 条已经混入此问题。

**[级别 LOW] 新 AST 前提筛忽略否定语义，会把“期望失败”筛成“期望成功”。**  
位置：[premise_anchor_screen.py:42](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u8-mutgates/_bmad-output/审查/evidence-mutkill-r2/premise_anchor_screen.py:42)。  
依据：50–58 行在 `node.test` 全树寻找 `returncode == 0`，注释明确包括被 `not` 包裹的情况。因此，无消息、首条断言为 `assert not (r.returncode == 0)` 的对照输入也会成为 suspect；未豁免则脚本失败。这与第 13 行“期望 `!= 0`……不算前提”相反。  
建议：至少区分比较表达式的正、负极性；复杂布尔表达式保留人工确认。  
影响边界：这是筛查误报，脚本不会自动修改 harness 裁决；不推翻当前 M89／M90 的处置。

其余重点核对结果：

- **编译期假杀：**四套主变异循环均在落盘、跑门前调用语法检查；`.py` 全文及匹配到的 PYEOF 块编译失败会进入 `SYNTAX-INVALID`。v4 负控支持作者更正的三种 PYEOF 形态。阶段 2 两次落盘仍没有语法检查，已登记在 #20，不能宣称所有写盘路径均已覆盖。
- **原 HIGH-1／HIGH-2：**N1／N2／P1／独立 capture 对照的脚本和 v4 输出相符。但 g32cb、g32ccr1、g33 仍只有消息＋门文件位置，原 HIGH-1 在这三套仍属已登记边界，不能称四套全部闭合。

三个正则的边界可明确到以下程度：

| 判据 | 代码确定的行为 |
|---|---|
| `_SUMMARY_HEAD_RE` | 只认精确英文分隔行；多段 summary 取第一段，不检查唯一性。 |
| `_SUMMARY_TAIL_RE` | 能匹配用户给出的 `= 1 failed, 2 passed in 3s =`；仅检查统计前缀，找不到尾行便读到 EOF。 |
| `_LOC_RE` | 要求无空白的 `.py` 路径；没有完整处理 ANSI 等格式变化，也不核对位置记录是否漏解析。 |

`FAILED`／`ERROR` 可被共同解析，但状态丢失见上文。`COLUMNS=1000` 确实传入，判据却不检查 reason 是否为空或截断。具体插件、终端宽度组合的实际行为仍**未验证**；#27 的解析完整性欠项仍存在。

**位置锚与 39 条处置：**

- g32b:2617 的启动自检确实可达，零命中、多重命中及 `file:` 期望值都会拒绝；实际表现是诊断后退出 2，并非逐条填入六档。
- 动态 `_loc_identity` 也有失锚报错分支，但它位于 rc=0、非目标门、门外失败等早退之后，不能保证运行中任何漂移都必报 `HARNESS-ERROR`。
- 指纹包含作用域名和语句 AST。注释、行号、保持 AST 的空白不改变指纹；断言消息、`a == b` 改为 `b == a`、函数改名会改变。同函数内把原样断言移到另一个控制分支，指纹仍可不变。
- 表与最新存档一致：36 条新增位置绑定中，35 条最终 `KILLED`，M10 降档；M89／M90／M97 保留 `KILLED-UNBOUND`。但这 36 条的**当前唯一性重算和目标性质语义均未独立验证**，需要门源码及逐条意图对照。现有三条自检只能证明语句身份，不能证明绑定的是正确性质断言。

**g33 与参数化配对：**`--selfcheck-syntax` 和主循环使用同一语法检查，语义一致；已识别的判据面异常会记录为 `HARNESS-ERROR`，最终返回 2，继续执行本身没有将其掩盖成 PASS。配对收紧则**确实会保守拒绝合法参数化结果**：实例 A 的目标位置和消息均命中，实例 B 在别处失败且消息不同，625 行仍返回 `HARNESS-ERROR`。不能把它描述成没有误拒；当前存档是否出现这种组合，未验证。

**信号证据：**`critical()` 嵌套、防重入及 `now == orig` 两窗口处理在代码上成立。N3／N4／P2／N5 钉住了真实还原函数的伪告警和真实第三方内容存证两个方向，但其“signal_first”实际是直接调用还原函数两次。信号负控仅实发单次 SIGTERM；其它信号、连续信号、写入中途及日志／存证故障组合继续标为**未验证**。

Round-2 十项逐项结论：#1 对原跨实例条件的修复成立；#2／#3 的局部日志保护成立，但存在上述退出展开缺口；#4／#6／#7 修复成立；#5 未修全；#8 引入否定误筛；#9 四类降档抽取已补，但遗漏上述对照锚异常路径；#10 措辞更正已落实。

最新存档数字核对一致：g32b 六档为 **131／3／0／4／0／0，rc=2**；其余三套为 **9／9、11／11、18／18，rc=0**。这些数字不证明未覆盖输入的判据正确。

十条“被推翻”仍**不能整体采信**：符号链接一条的推翻已撤回；其余九条缺各自原始发现与反证，无法在授权读取面内逐项复判。
