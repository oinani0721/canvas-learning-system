> 批次: BATCH-2026-09-07-第十三批 · 车道 U8 · 卡 CARD-DEBT-mutkill-R2 round-5（D-15 最后一轮）
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `OpenAI Codex v0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-DEBT-mutkill-R2-r5.md)"`
> 审查绑定: `4a612eb3`（复核自报 `4a612eb3a606bfbc3f6efa339fa43d16359647d6`；工作树干净）
> 会话头自证（抄 .stderr 前三行含 model 行，stderr 本身不入库）:
> `Reading additional input from stdin...` / `OpenAI Codex v0.153.3` / `--------`

---
**结论：不通过。2 HIGH / 3 MEDIUM，未发现 BLOCKER。按 D-15，应交主 session 人审。**

复核绑定 `4a612eb3a606bfbc3f6efa339fa43d16359647d6`。未运行 harness、pytest 或负控脚本，未修改文件；两条 HIGH 使用从当前源码抽取的判定函数做了纯内存核算。**输入级错误裁决已验证；当前 pytest 是否实际生成这些输入，未验证。**

**[级别 HIGH] `_split_unique` 仍会把无 reason 的参数化 nodeid 尾部误当期望消息。**  
位置：[mutation_kill_identity.py:203](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u8-mutgates/backend/scripts/mutation_kill_identity.py:203)  
依据：203–211 行只枚举 ` - ` 切点，只有 `if not cands` 才考虑无 reason。但模块明确支持无 reason 格式。负控输入：

```text
FAILED tests/x.py::test_x[case] - EXPECT[]
```

存在两种读法：截出的 nodeid 加 reason，或者参数 ID 为 `case] - EXPECT[` 的完整 nodeid、没有 reason。当前实际解析为：

```text
nodeid = tests/x.py::test_x[case]
reason = EXPECT[]
unparsed_failure_lines = []
```

接入弱位置判据后，当前 `kill_identity()` 返回 **KILLED**，消息维实际由参数文字满足。round-4 的两条完整 reason 负控被堵住了，但“切分唯一性”尚未成立。  
建议：将结构合法的“整行无 reason”读法也纳入候选；存在第二种读法即 `HARNESS-ERROR`。

**[级别 HIGH] 弱位置判据仍允许借用另一道门的失败位置，合成 KILLED。**  
位置：[mutation_kill_identity.py:697](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u8-mutgates/backend/scripts/mutation_kill_identity.py:697)  
依据：弱位置检查仅为：

```python
any(_same_file(p, gp) for p, _, _ in locs)
```

“所有失败 nodeid 都属于目标门”的检查在 `_loc_identity()` 的 612–614 行，只有提供 `expect_loc` 才执行。708–724 行又只统计目标门自己的 reason。

内存对照输入中，目标门失败位置在文件外、消息命中；另一道门失败位置在指定文件内、消息不命中。目标 reason 只有一条，配对保护没有触发，结果仍为 **KILLED**。这突破了弱位置判据自己的承诺，不能归入 D-28 延期的具体断言绑定。  
建议：弱位置分支同样要求完整失败集全部属于目标门；归属不可证即 `HARNESS-ERROR`。三套实际运行中是否出现过这种混合输出，未验证。

**[级别 MEDIUM] 运行中的锚漂移不保证报 HARNESS-ERROR，重复指纹也没有运行时唯一性复查。**  
位置：[mutation_kill_identity.py:672](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u8-mutgates/backend/scripts/mutation_kill_identity.py:672)、[g32b_mutation_gates.py:2643](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u8-mutgates/backend/scripts/g32b_mutation_gates.py:2643)  
依据：跑前 `_check_expect_loc()` 确实会阻断零命中或多命中。但运行时先处理 `rc == 0 → SURVIVED`，以及 697–700 行“红在门文件之外 → SURVIVED”；这些返回都早于锚检查。即使到达 `_loc_identity()`，620 行也只检查：

```python
if expect_loc[5:] not in fps:
```

没有复查命中数是否为 1。因此，跑前自检后门被改动，不能保证作者所称的漂移报错。当前运行期间是否发生过这种改动，未验证。  
建议：提供 `expect_loc` 时，在返回测试裁决前复查指纹恰好命中一次；失效或重复统一报 `HARNESS-ERROR`。

**[级别 MEDIUM] g33 首次信号还原成功后，最后一次重复还原的新失败仍可能保留 rc=130。**  
位置：[g33_mutation_gates.py:445](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u8-mutgates/backend/scripts/g33_mutation_gates.py:445)、同文件 528–529 行。  
依据：`restore_all()` 每次无条件 `Path(sp).write_bytes(data)`。`_finish()` 成功还原并抛出 130 后，外层 `finally` 再次调用还原；此时 `_was_exiting=True`，新发生的还原异常也被 448–454 行吞掉。原来的 130 继续传播，537 行的 SHA 检查不会执行。

确定的问题是**最后一次还原失败仍报成功还原后的中断码**。若失败发生在文件截断后，可能留下不完整文件；这一文件后果未做运行验证。  
建议：按当前变异登记待还原文件，成功后清除，使成功退出后的 `finally` 成为空操作；保留失败重试及 131，勿恢复全程一次性的 `done` 闩。

**[级别 MEDIUM] 处置表仍未实现六档完整硬核对，缺失汇总也能输出“一致”。**  
位置：[make_disposition_table.py:117](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u8-mutgates/_bmad-output/审查/evidence-mutkill-r2/make_disposition_table.py:117)  
依据：`_mine` 只有四档，123 行为：

```python
_bad = [k for k in _mine if k in _sum and _sum[k] != _mine[k]]
```

缺少汇总字段甚至整个汇总缺失，都不产生 `_bad`；`ANCHOR-ERROR`、`SYNTAX-INVALID` 不参与比较，入口 48 行也未解析这两档。125 行仍可输出“一致 ✓”。**当前 v6 后两档为零且汇总完整，现有表内数字未因此改变。**  
建议：要求六档汇总完整且各出现一次，逐条终裁覆盖六档，并核对全部计数、tag 集合与总数。

其余问题的核对结果如下：

| 项目 | 结论 |
|---|---|
| 编译期假杀 | 四套主变异路径均先做编译检查；g33 `--selfcheck-syntax` 的“旧串拒绝、新串及原文通过”与分档语义一致。最新 PYEOF v6 覆盖三种修复形态并 PASS。阶段 2 两次落盘缺编译检查已登记在 #20，未闭合。 |
| 摘要边界 | `_SUMMARY_TAIL_RE` 能匹配题述 `= 1 failed, 2 passed in 3s =`；但只取首个摘要头，缺尾则读取到 EOF，不拒绝多段摘要。尾正则也未验证完整统计行。 |
| 格式失配 | `_SUMMARY_HEAD_RE` 严格要求既定空格与等号格式；`_LOC_RE` 不接受带空格路径、非 `.py` 路径。全部位置漏认会报错误，部分漏认没有完整性核对。原始 CRLF/ANSI、插件格式与当前实际输出关系未验证。 |
| `COLUMNS` | 四套用 `judge_env()` 覆盖外部宽度为 1000；没有检测 reason 是否仍被截断。 |
| AST 指纹 | 注释、保持 AST 与作用域不变的空白调整不改变指纹；改消息字面值、交换 `a == b` 两侧、改函数名会改变。指纹不包含外层控制分支身份，因此它不证明控制流或循环轮次。 |
| 参数化配对 | 多条目标失败中仅部分消息命中时，确实保守报 `HARNESS-ERROR`；合法的混合参数实例也会被拒绝。这符合当前保守策略，但不能称为完整支持参数化输出。 |
| g33 继续跑 | 已识别的判据面缺失会记录 `HARNESS-ERROR`，最终 rc=2，未被继续执行掩盖；解析器未识别的问题仍受上述边界限制。 |
| round-4 信号整改 | 四套进入时快照均已接入；g32cb 包装确实用于 `finally`。嵌套 `critical()`、pending 兑现、防重入日志及正常失败路径 131 均有对应实现。 |
| 第三方存证 | 最新 N3/N4/P2/N5 覆盖无伪告警、有改动存证、正常还原及尚未写盘窗口，两个历史方向均有证据。它们没有验证真实信号与存证／日志故障的组合。 |

最新四套存档数字核对一致：g32b 为 **131 / 3 / 0 / 4 / 0 / 0，合计 138，rc=2**；另三套分别 **9/9、11/11、18/18，rc=0**。39 条处置对应 **36 条位置绑定、3 条 UNBOUND、退役 0**；其中最终是 **35 KILLED、M10 HARNESS-ERROR、M89/M90/M97 UNBOUND**。

以下仍须保留为**未验证**：

- **36 条绑定的实际唯一性和目标语义**：表项、存档与回填脚本相符，不能替代对门 AST 和变异意图的独立核对。
- **十条“被推翻”**：符号链接一条的推翻已在后续台账撤销；其余九条没有提供逐条原文与反证，不能整体采信 #20。
- **最终提交绑定**：v6 负控记录模块 1073 行，但行数不能证明内容一致；允许读取的 finalize 没有五脚本运行时 SHA。另存的 `run-code-state-*` 不在本次读取面。
- **真实运行边界**：全部四信号、写盘内部中断、失败退出 131，以及 `-rf` 下 ERROR 摘要是否完整，现有允许证据不足以闭合。
