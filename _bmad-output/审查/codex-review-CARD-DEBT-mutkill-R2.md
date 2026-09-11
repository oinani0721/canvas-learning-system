> 批次: BATCH-2026-09-07-第十三批 · 车道 U8 · 卡 CARD-DEBT-mutkill-R2 round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-DEBT-mutkill-R2.md)"`
> 审查绑定: `f395d900`（= 当时的 HEAD 与工作树，二者一致；diff 基线 3f073a1a）
> 会话头自证（抄 .stderr 前三行含 model 行，stderr 本身不入库）:
> `Reading additional input from stdin...` / `2026-09-08T09:19:29.134875Z ERROR codex_models_manager::manager: failed to refresh available models: timeout waiting for child process to exit` / `2026-09-08T09:19:29.148596Z ERROR codex_models_manager::manager: failed to refresh available models: timeout waiting for child process to exit`

---
**复核结论：不通过。** 新判据修住了存档中的 N1/N2，但仍存在可静态证明的误记 KILLED 路径，以及 g33 的分档回归。

本次未运行 harness、pytest 或负控脚本，未修改文件。下面的“代码级负控路径成立”不代表已经证明当前 39 条中发生了该问题；具体条目无法核实的均注明“未验证”。

**[级别 HIGH] 同行不同语句无法由行号区分，另一条断言失败可被映射成目标断言失败。**  
位置：[mutation_kill_identity.py:428](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u8-mutgates/backend/scripts/mutation_kill_identity.py:428)  
依据：437 行只在 `span < best_span` 时替换候选，同跨度保留第一条。纯内存 AST 核对确认：两条不同断言放在同一行，各自指纹仍唯一，但该行始终映射到第一条。第一条通过、第二条失败时，位置会认错；消息为空或满足消息条件便可判 KILLED。把两行合成分号一行也不改变两条指纹，864–865 行的唯一性检查仍通过。**当前 36 条是否已有这种布局：未验证。**  
建议：行号无法唯一归属语句时判 HARNESS-ERROR，并让位置表自检拒绝这种绑定。

**[级别 HIGH] 空变异对照比较的是第一条失败位置，未必是实际满足 EXPECT_LOC 的那次失败。**  
位置：[g32b_mutation_gates.py:2724](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u8-mutgates/backend/scripts/g32b_mutation_gates.py:2724)  
依据：共用判据用 `expect_loc in tokens` 接受任一命中位置；`observed_loc()` 却固定取 `locs[0]`，2724、2852 行据此保存和比较。位置序列为“其他位置、目标位置”，而空对照也败在目标位置时，两边首项不同，2894 行仍会宣称“变异体有可观测效果”，保留 KILLED。**当前存档是否触发此多失败形态：未验证。**  
建议：记录实际满足击杀身份的失败位置，空对照针对该身份判断；归属无法确定时降为 HARNESS-ERROR。

**[级别 HIGH] 空变异对照把 pytest 未运行成功或多例失败当成“对照绿”。**  
位置：[g32b_mutation_gates.py:2833](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u8-mutgates/backend/scripts/g32b_mutation_gates.py:2833)  
依据：`red0 = r0.returncode == 1 and "1 failed" in r0.stdout`；2866 行的 `b_only` 同型。因此 rc=4/5，或 rc=1 但输出为 `2 failed`，都会走2877/2879行的“门绿／击杀干净归因于变异体”。这与台账承认的“阶段2未做 syntax_check”是独立问题，补编译检查不能解决。另2889–2892行发现位置面缺失时仅追加 `failures`，也没有撤销先前 KILLED。  
建议：对照绿只认 rc=0；其余结果分别判失败或 HARNESS-ERROR，判据缺失须同步更新最终分档。

**[级别 MEDIUM] 正常全绿的 rc=0 被记为 HARNESS-ERROR，g33 因统一调用产生了分档回归。**  
位置：[mutation_kill_identity.py:525](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u8-mutgates/backend/scripts/mutation_kill_identity.py:525)  
依据：`judge_surface_missing(0, ...)` 返回 None，随后 `if rc != 1` 返回 HARNESS-ERROR。g33:482直接采用该裁决，没有绿态分支；基线则把布尔击杀检查的 False 记为 SURVIVED。现在真实未被击杀的变异会被解释为 harness 自己坏了，最终退出2。  
建议：先处理 `rc == 0 → SURVIVED`，再处理其余非1异常码。

**[级别 MEDIUM] 摘要中的部分失败行会被静默丢弃，“所有失败都属于目标门”的前提并未完整验证。**  
位置：[mutation_kill_identity.py:180](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u8-mutgates/backend/scripts/mutation_kill_identity.py:180)  
依据：nodeid 使用 `\S+?`，带空白参数名的失败行不能匹配。344行只要求至少存在一条可解析记录，479行随后对已经遗漏记录的集合执行 `all(...)`。纯内存正则核对确认此行为。**当前四套是否输出过这种参数名：未验证。**  
建议：支持含空白的合法 nodeid；任何 `FAILED `/`ERROR ` 开头却解析失败的记录，都应使判据报错，不能忽略。

**[级别 MEDIUM] 信号路径的日志异常仍能打断处理，并绕开承诺的130/131退出码。**  
位置：[mutation_kill_identity.py:667](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u8-mutgates/backend/scripts/mutation_kill_identity.py:667)  
依据：还原期 handler 登记 pending 后立即调用 `_log`，默认实现是 `print(..., flush=True)`。失败路径690–695行、成功路径698–699行也都先写日志，再抛出规定的 SystemExit；日志抛异常便到不了退出语句，此时 `_finishing` 已置位。**真实信号与日志故障交错是否造成残留：未验证。**  
建议：还原期 handler 只登记状态；日志不得向外抛异常，规定退出码必须独立于日志写入成功。

**[级别 MEDIUM] g32b 未实现验收单声明的“还原错误优先退出3、计数错误退出2”。**  
位置：[g32b_mutation_gates.py:2907](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u8-mutgates/backend/scripts/g32b_mutation_gates.py:2907)  
依据：2715、2844、2872行还原不一致仍 `sys.exit(2)`；最终 `_drifted` 只追加 failures，随后有 HARNESS-ERROR 返回2，否则返回1。2959行的计数不一致也只追加 failures，可能返回1。与验收单233行的新契约不符。  
建议：还原失败统一返回3并优先判断；计数不一致单独返回2。

**[级别 MEDIUM] 被推翻的“生产扫描静默跳过符号链接”在当前代码中确实存在，原行号错误不足以推翻它。**  
位置：[mutation_kill_identity.py:740](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u8-mutgates/backend/scripts/mutation_kill_identity.py:740)  
依据：目录遍历使用 `followlinks=False`，743–744行明确为 `if f.is_symlink() or not f.is_file(): continue`，没有把跳过记入 errors。验收单232行却以“锚点错17行指到散文”将其列为不采信。**当前扫描面是否实际存在此类路径、是否导致具体条目漏检：未验证。**  
建议：撤回该推翻理由；遇到未检查的符号链接时显式报告扫描不完整，不能据此宣称生产侧零命中。

**[级别 MEDIUM] 前提锚筛查仍依赖旧行号，门挪行后可能跳过原断言并返回PASS。**  
位置：[premise_anchor_screen.py:61](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u8-mutgates/_bmad-output/审查/evidence-mutkill-r2/premise_anchor_screen.py:61)  
依据：61行丢弃 probe 中的 `loc` 指纹，只保留原始行号；77–81行按旧行号查当前源码，找不到断言归属便 `continue`；94行零 suspects 也 PASS。40行计算的 `fps` 未使用。**当前筛查存档是否已因此漏项：未验证。**  
建议：按 probe 指纹唯一重定位，并验证 tag 集合及定位完整性；无法重定位应报错。

**[级别 LOW] 39条处置表把“增加位置绑定”写成“最终改判KILLED”，与M10最终裁决矛盾。**  
位置：[make_disposition_table.py:57](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u8-mutgates/_bmad-output/审查/evidence-mutkill-r2/make_disposition_table.py:57)  
依据：只检查 `tag in loc` 就计入“UNBOUND→KILLED”；但最新 run-g32b 存档146、195行已经把 M10 判为同层贡献的假杀并降为 HARNESS-ERROR。  
建议：表述为“36条新增位置绑定”。按最新最终裁决，原39条实际为 **35 KILLED、3 KILLED-UNBOUND、1 HARNESS-ERROR**。

其余重点问题的核对结果：

| 问题 | 独立核对结论 |
|---|---|
| 编译期假杀 | 四套主变异循环都在跑门前做编译检查。PYEOF三种修复与最新负控相符，存档记录真实文件2＋3块提取一致。但阶段2未编译；未匹配到块时 `syntax_check` 仍返回None，不能据此证明所有可执行内容均被检查。 |
| 摘要头、尾边界 | `_SUMMARY_HEAD_RE` 严格匹配固定格式并取第一个头。指定的 `= 1 failed, 2 passed in 3s =` 能匹配尾；首项为 skipped 等形态不能。没有匹配尾时直接取全部余文，多段摘要不会报歧义。 |
| 位置正则、ERROR混排 | `_LOC_RE` 不接受含空白路径或非 `.py` 路径。摘要中的FAILED/ERROR顺序本身不影响提取，但完整性没有验证，不能保证每条位置均有对应摘要记录。 |
| COLUMNS、插件 | 四套确实覆盖设置COLUMNS=1000；`judge_surface_missing` **没有检查reason截断**。格式完全失配通常报HARNESS-ERROR，局部失配可能被忽略或报SURVIVED。其他插件组合的实际行为未验证。 |
| 锚漂移 | 指纹消失→HARNESS-ERROR路径确实存在，启动自检也会拒绝零命中。注释、行号和保持AST结构的空白修改不改变指纹；消息修改、比较两侧交换、函数／类改名会改变。运行期仅检查指纹存在，未重查唯一性。 |
| 三条位置表判据 | 启动时确实检查空值登记、禁止`file:`、指纹恰好一处；它们不覆盖同行歧义，也不证明失败是断言条件为假——位置判据未检查异常类型，断言求值阶段的异常也可能命中同一语句。 |
| 参数化保守分支 | 559–567行确实会拒绝“一个参数实例正确击杀，另一个实例失败消息不同”的合法输出。这是已声明的保守限制，不能解释为门不承重；它只保护已成功解析的记录。 |
| g33自检及继续运行 | `--selfcheck-syntax` 的坏M15／好M15／原文三项语义一致，其rc=0仅代表该自检。判据缺失后继续运行会保留逐条HARNESS-ERROR并最终退出2，这项没有静默放行；正常rc=0错分见上。 |

还原方面，`critical()` 的同步嵌套、`_finishing` 防重复恢复、`now == orig → continue` 两个窗口，以及第三方内容先存证再还原的顺序均成立。最新 N3/N4/P2/N5 支持“无第三方不误报、有第三方保存其内容”两个方向。不过第三方脚本以连续函数调用表示信号路径；信号负控使用自建恢复循环发送一次SIGTERM，**未证明真实四套连续信号、还原异常及131退出路径**。

最新四套全跑存档数字与验收单一致：g32b为 **131／3／0／4／0／0，rc=2**；其余三套分别9、11、18条KILLED，rc=0。后三套的KILLED仍只绑定消息与门文件，HIGH-1按D-28留下的缺口没有闭合。M89/M90/M97保留UNBOUND、退役0条与表和输出一致；36条当前语句的唯一性、目标语义，受读取边界限制未能独立重算。

**那10条“被推翻”不能整体采信。** 给定材料只点名符号链接一条，其推翻依据已被当前代码反驳；另外9条缺原发现和逐项反证，25条人工处置也缺完整对应关系，均未验证。

最后，v2存档与当前代码的精确绑定仍未验证：N1/N2日志记录共用模块860行，当前870行；finalize没有保存五脚本运行时哈希。验收单解释后续仅做格式化，但给定材料不足以独立证明差异全部不影响语义。


