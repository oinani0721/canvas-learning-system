> 批次: BATCH-2026-09-07-第十三批 · 车道 U8 · 卡 CARD-DEBT-mutkill-R2 round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `OpenAI Codex v0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-DEBT-mutkill-R2-r2.md)"`
> 审查绑定: `e5dc313c`（复核自报 `e5dc313cd6c29d13d1ed9c7f246a363f98470fd7`；工作树干净）
> 会话头自证（抄 .stderr 前三行含 model 行，stderr 本身不入库）:
> `Reading additional input from stdin...` / `OpenAI Codex v0.153.3` / `--------`

---
**结论：不通过。确认 2 项 HIGH、7 项 MEDIUM、1 项 LOW。**

复核绑定 `e5dc313cd6c29d13d1ed9c7f246a363f98470fd7`。以下问题由源码控制流确认；**未运行负控输入，也不据此声称本次全跑数字已经发生错判**。全程未运行 harness、pytest 或写文件。

**[级别 HIGH] 三套弱位置判据仍能把不同失败实例的位置与消息拼成 KILLED。**  
位置：[mutation_kill_identity.py:625](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u8-mutgates/backend/scripts/mutation_kill_identity.py:625)。  
依据：610 行只要求 `any(_same_file(p, gp) ...)`；622 行只要求任一目标 reason 命中消息；625 行的配对检查却限定 `and expect_loc is not None`。同一参数化门中，“门内失败、消息不命中”与“门外失败、消息命中”可以分别满足两维，最终进入 651 行 KILLED。g32cb:516、g32ccr1:406、g33:482 的实际调用均只传 `require_gate_file=True`。这突破了现有弱位置承诺，不能归入 D-28 延期的具体断言绑定。  
建议：所有启用位置要求的调用都检查失败归属及同次配对；配对不可证时返回 HARNESS-ERROR。

**[级别 HIGH] 第三方存证后的日志异常仍能阻断原文还原。**  
位置：[g32b_mutation_gates.py:2491](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u8-mutgates/backend/scripts/g32b_mutation_gates.py:2491)。  
依据：2490—2496 行的顺序是 `stash.write_bytes(now)` → 裸 `print(..., flush=True)` → `_p.write_bytes(_orig)`。日志抛异常时，当前文件及后续文件不会完成还原；Guard 的 `_safe_log` 没有包装这个回调。外层 finally 重试还会经过同一条日志。  
建议：让该日志成为不抛异常的诊断操作，保证存证成功后的还原不依赖日志成功。真实信号与 stdout 故障的交错仍**未验证**。

**[级别 MEDIUM] 还原失败时，traceback 输出异常仍能绕过约定的 131 退出码。**  
位置：[mutation_kill_identity.py:768](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u8-mutgates/backend/scripts/mutation_kill_identity.py:768)。  
依据：异常分支先裸调用 `traceback.print_exc()`，773 行才执行 `raise SystemExit(self._exit_code + 1)`。stderr 写入失败会使后者到不了；此时 `_finishing` 已置位，后续 `_finish` 只记录并返回。round-1 的 `_safe_log` 修复没有覆盖此处。  
建议：保护 traceback 输出，并保证诊断失败也执行约定退出。

**[级别 MEDIUM] 全集交集判据会因其他失败位置重合，将有效的目标击杀误降档。**  
位置：[g32b_mutation_gates.py:2909](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u8-mutgates/backend/scripts/g32b_mutation_gates.py:2909)。  
依据：条件是 `set(fa[0]) & set(fb[0])`，没有限定交集必须包含 `EXPECT_LOC[tag]`。主变异失败位置为 `{目标 T, 其他 U}`、空对照只有 `{U}` 时，即使 T 只在施加变异后失败，也会因 U 的交集被降档。该主变异在 `expect_msg=None`、`expect_loc=T` 时能通过共用判据。  
建议：有目标位置绑定时，以空对照是否命中该目标位置判断假杀；其他共享位置仅作诊断。当前真实门是否出现此布局：**未验证**。

**[级别 MEDIUM] 空对照仍用文本子串认定“恰一条失败”，部分多失败输入可以保留 KILLED。**  
位置：[g32b_mutation_gates.py:2844](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u8-mutgates/backend/scripts/g32b_mutation_gates.py:2844)，同型位于 2884 行。  
依据：原文 `_r0_single_red = r0.returncode == 1 and "1 failed" in r0.stdout`。`11 failed`、`1 failed, 1 error` 都满足它；当位置集合非空且与主变异不交时，会进入 2926 行“对照红但失败位置不同”，保留 KILLED。  
建议：结构化核对完整摘要、指定门、恰一条 FAILED 及无 ERROR；其余对照按 HARNESS-ERROR 降档。不能只替换成另一条全文子串。

**[级别 MEDIUM] g32b 三个提前退出点仍把还原漂移报告为 rc=2。**  
位置：[g32b_mutation_gates.py:2716](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u8-mutgates/backend/scripts/g32b_mutation_gates.py:2716)，同型位于 2856、2890 行。  
依据：三个“还原后字节不同”分支均执行 `sys.exit(2)`，会先于末尾 2947 行的 `return 3` 退出。round-1 #7 只修了收尾路径。  
建议：三个已确认还原漂移的出口统一为 rc=3，保持数据完整性错误的优先级。

**[级别 MEDIUM] 符号链接整改只覆盖文件链接，目录链接仍被静默漏扫。**  
位置：[mutation_kill_identity.py:818](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u8-mutgates/backend/scripts/mutation_kill_identity.py:818)。  
依据：`os.walk(..., followlinks=False)` 只将 `filenames` 加入 `candidates`，丢弃 `_dirnames`。825 行的 `f.is_symlink()` 因而收不到目录链接；其子树没被扫描，也不会进入 `errors`。  
建议：把被跳过的目录符号链接同样记入 `errors`。当前树是否存在这种目录布局：**未验证**。

**[级别 MEDIUM] 前提锚筛仍会因不改变 AST 的多行排版而静默漏判。**  
位置：[premise_anchor_screen.py:92](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u8-mutgates/_bmad-output/审查/evidence-mutkill-r2/premise_anchor_screen.py:92)。  
依据：指纹重定位后，只取 `text = lines[ln - 1].strip()`，98 行仍用 `"returncode == 0" in text`。比较表达式移至后续行时，指纹不变、重定位成功，筛选条件却变假；113 行允许零 suspects 返回 PASS。  
建议：检查重定位得到的 `ast.Assert`／`Compare` 节点，避免在语句起始行做子串判断。最新存档所示 M89/M90 仍是单行；当前多行布局**未验证**。

**[级别 MEDIUM] 处置表的“最终裁决”解析漏掉新增的三类降档。**  
位置：[make_disposition_table.py:48](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u8-mutgates/_bmad-output/审查/evidence-mutkill-r2/make_disposition_table.py:48)。  
依据：读取首轮裁决后，51 行仅匹配 `✗ 假杀` 来覆盖终裁。但 g32b:2897、2905、2922 的 complete 对照失败、空对照未跑成、位置判据面缺失，也会将 KILLED 降为 HARNESS-ERROR；它们的输出不匹配该正则，处置表仍会写“最终 KILLED”。  
建议：从统一的逐条终裁记录生成表；至少补齐这些降档，并核对最终六档计数。**当前 35+1 数字仍与最新存档相符**，本发现针对尚未覆盖的终裁路径。

**[级别 LOW] 共用位置说明把不同调用门写成“同一道门”，并混入已撤销的历史绑定。**  
位置：[验收单:205](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u8-mutgates/_bmad-output/验收单/UAT-CARD-DEBT-mutkill-R2-2026-09-08.md:205)。  
依据：此处称五组条目“恰恰绑的是同一道门的同一条断言”；最新日志中 M23/M24/M25 分别是三道 narrow 门，g32b:2283 也明确写“三道 narrow 门共用”。155 行仍列 M89/M90 的位置指纹，而它们已撤销绑定。  
建议：区分共享 helper 位置与相同 nodeid，并标明已撤销绑定属于历史 probe 观察。

其余重点问题的复核结论如下。

| 问题 | 只读结论 |
|---|---|
| 编译期失败是否还会算 KILLED | 四套主变异路径确有编译预检，命中的非法 Python 会进入 SYNTAX-INVALID。不能扩大为所有执行文本均覆盖：Markdown 只编译匹配到的 PYEOF 块；g32b 阶段二两次落盘没有同样的预检，验收单已登记该债。 |
| 原 HIGH-1／HIGH-2 负控 | N1/N2/P1/D 脚本确实使用同一份输出比较新旧判据，目标位置由负控源码独立取得。存档支持两条负控拒绝、正控接受及 captured 开关对照；不证明所有消息／位置组合都安全。 |
| 锚失效路径 | 跑前 `_check_expect_loc()` 能因零命中或多命中以 rc=2 阻断；运行时 `_loc_identity()` 的零命中 HARNESS-ERROR 路径也存在。不过运行时仅检查“存在”，不重新检查唯一性；而门外失败会在更早的 610 行返回 SURVIVED。不能声称所有运行中改门情形都报告锚失效。 |
| AST 指纹变化 | 注释、空白、保持 AST 与函数／类作用域不变的缩进排版不会改变指纹。断言消息改变、`a == b` 改为 `b == a`、所属函数／类改名会改变。调整控制结构但保留同一作用域中的断言 AST，断言自身指纹可能不变。 |
| 39 条绑定 | 当前表、豁免和最新终裁的 **36 新绑定／3 UNBOUND／0 退役，35 最终 KILLED／1 降档**相符。三条自检规则确已实现，但它们只证明登记、唯一性与 token 类型，不能证明目标语义。36 条在当前门源码中的独立唯一性和目标语义仍**未验证**。 |
| g33 自检与继续跑 | `--selfcheck-syntax` 使用同一编译函数检验旧坏串、新好串和原文，与正式分档一致。判据面缺失经共用函数累计 HARNESS-ERROR，最终 rc=2；没有发现继续跑将其绿化。 |
| 信号还原 | 嵌套 `critical()` 不会提前释放外层闩；`_finishing` 防止重复启动还原。`now==orig` 覆盖尚未写入和已经还原两个窗口。除此之外，日志问题见上列 HIGH／MEDIUM。 |
| 合法参数化是否误拒 | **会保守拒绝一部分合法组合**：已绑定位置、多个失败仅部分含期望消息时，即使目标位置实际属于消息命中的实例，625 行仍返回 HARNESS-ERROR。它没有把这类情况判为 SURVIVED，但当前文本报告无法证明配对。 |

三个正则的边界也没有达到“所有失配都明确报错”：

| 解析面 | 实际行为 |
|---|---|
| `_SUMMARY_HEAD_RE` | 要求精确分隔线文本；标题带额外格式字符时可能不匹配。`summary_region()` 只取首个摘要，不验证多摘要的完整性。 |
| `_SUMMARY_TAIL_RE` | 能匹配题述 `= 1 failed, 2 passed in 3s =`；但只匹配计数前缀，没有验证完整统计行。找不到尾行时直接读取到 EOF，**不会因此报 HARNESS-ERROR**。 |
| `_LOC_RE` | 路径不得含空白，必须以 `.py` 结尾，且行格式固定。全部位置失配会报判据面缺失；只漏掉部分位置时，没有完整性核对。 |
| FAILED／ERROR 混排 | 两种前缀都能解析，顺序不用于建立对应关系，类型也没有保留。摘要记录与位置记录没有逐条绑定。 |
| `COLUMNS` | 环境设为 1000，但没有检查 reason 是否被截断。消息因此不命中时可能返回 SURVIVED，不能采信注释所说“这类缺失都会被判据面检查发现”。 |

插件组合、空白参数化 id、上述格式失配在当前真实运行中的表现仍**未验证**。最新 g33 存档确有 `[1]`、`[2]` 两条参数化失败，且位置相同；它只能证明这一种多失败形态，不能验证带 `expect_loc` 的配对分支。

最新全跑存档数字核对无误：

| harness | KILLED | UNBOUND | SURVIVED | HARNESS-ERROR | ANCHOR-ERROR | SYNTAX-INVALID | rc |
|---|---:|---:|---:|---:|---:|---:|---:|
| g32b | 131 | 3 | 0 | 4 | 0 | 0 | 2 |
| g32cb | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| g32ccr1 | 11 | 0 | 0 | 0 | 0 | 0 | 0 |
| g33 | 18 | 0 | 0 | 0 | 0 | 0 | 0 |

仍不能闭合的证据有三项：

- **信号组合未验证。** N3/N4/P2/N5 调用真实 g32b 还原函数，限定顺序下确实覆盖“不误存证／真实改动被存证”两个方向；它们没有递送真实信号。信号负控使用自建还原循环，只实际递送 SIGTERM。真实信号×存证×日志故障、正在写入的窗口及失败退出 131 缺少对应证据。
- **十条“被推翻”不能整体采信。** 符号链接一条已撤回推翻，但修复仍漏目录链接；其余九条缺各自发现原文、位置和反证。允许读取的材料不足以独立判定它们的错杀／漏杀。
- **v3 与 HEAD 的精确绑定未建立。** `negctl-n1n2-v3-20260909T101629.txt:2` 自报模块 **952 行**，HEAD 是 **957 行**；`finalize-v3-20260909T120714.txt:41—43` 仍记录两个脚本为修改状态。四套最新运行存档没有执行脚本的 SHA。它们不能证明逐字节绑定，也不能据此断言存在语义差异。

执行边界补记：审查前后均仅见同样两份未跟踪审查文件，未读取或修改它们。读取旧审档时，一个窗口附带显示了 HIGH-3 开头十行；该范围外内容未用于上述判断。
