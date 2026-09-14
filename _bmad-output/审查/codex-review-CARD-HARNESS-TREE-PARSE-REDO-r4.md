> 批次: BATCH-2026-09-11-第十四批 · 车道 T7 · 卡 CARD-HARNESS-TREE-PARSE-REDO round-4
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-HARNESS-TREE-PARSE-REDO-r4.md)"`
> 审查绑定: `08100483..34451227`（该轮 HEAD = `34451227`；本轮之后按其 LOW-1 补了 3 条门参数、按 MEDIUM-1/2 与 LOW-2 更正 docstring ⇒ HEAD 已前进到 `4eeaeaa6`，故本轮**不绑最终 HEAD**，见 r5）
> 会话头自证（抄 .stderr 前 12 行中的三条，stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（第 2 行） / `model: gpt-6-astra`（第 5 行） / `reasoning effort: ultra`（第 9 行）

---

审查绑定已确认：HEAD 为 `34451227`，三个代码文件与提交一致。**结论：BLOCKER 0 / HIGH 0 / MEDIUM 2 / LOW 2；降级分支仍不能保证与 PyYAML 同值。**

**BLOCKER：无。**

**HIGH：无。** 本次证明到解析与选树层，未证明真实缺库环境最终完成错误写入。

**MEDIUM：**

1. **整行引号计数仍会把标量内容误认成配置键，已登记问题确实可复现。**  
   位置：[SKILL.md:522](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/canvas-vault/.claude/skills/quiz-answer/SKILL.md:522)。  
   当字面引号、跨行标量定界符和尾注释中的引号恰好凑成偶数时，规范形状的那一行仍可能处于字符串内部；内存执行真实函数确认，PyYAML 分支回退，降级分支却采用另一棵存在的树。

   **MEDIUM-3 的登记理由不足以支持关闭问题。** [验收单:293](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/_bmad-output/验收单/UAT-CARD-HARNESS-TREE-PARSE-REDO-2026-09-14.md:293) 已承认下游缺库也会拒写；按此前提，提前保守拒绝不会损失一次原本能完成的写入。“是否延期”可以交产品决定，但当前状态应表述为**已有反例**，不能仅称“尚未证明”。

2. **未覆盖的块结构和隐式类型构造，会让 PyYAML 整份拒绝而降级采用配置树。**  
   位置：[SKILL.md:524](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/canvas-vault/.claude/skills/quiz-answer/SKILL.md:524)。  
   当其他字段存在不可构造的隐式日期、不可哈希的复杂键，或块集合／普通标量结构错误，同时目标行符合规范时，非目标行直接跳过，降级仍返回存在的树；已分别实证 `ValueError`、`ConstructorError`、`ParserError`、`ScannerError` 与降级成功的差异。`:442–444` 仅承认“可能无键回退”，没有覆盖这种直接采用路径的结果。

**LOW：**

1. **现有参数受到其他判据和固定文件头遮蔽，“补参数无效”的登记理由不成立。**  
   位置：[测试文件:7621](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/regression/test_g3_2_review_ledger.py:7621)、[验收单:300](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/_bmad-output/验收单/UAT-CARD-HARNESS-TREE-PARSE-REDO-2026-09-14.md:300)。  
   分别删除指令、八符号、奇数引号判据后，当前 57 参数确实仍满足断言；但仅补充孤立无效指令、无关键处未定义别名、未闭引号等输入，保持原断言不变，就能分别使三个变体变红。新增三个文档标记参数也被文件头放到了文档中段，测不到本轮修复的开头状态。

   **LOW-1 理由只有一半成立：**允许保守拒绝，确实使该门不检查过度拒绝；但“判据失效测不到”还有样本遮蔽原因，可以补参数改善，并非必须另立变异测试卡。

2. **`_breaks` 的解释仍把五个非法字符说成合法换行字符。**  
   位置：[SKILL.md:462](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/canvas-vault/.claude/skills/quiz-answer/SKILL.md:462)。  
   输入含 VT／FF／FS／GS／RS 时，PyYAML 报 `ReaderError`；它们与 `_nonprint` 重叠，不能称八个字符全部“合法但会断行”。这是说明错误，拒绝行为本身正确。

其余问题逐项核对如下。

**Q0：来源分类仍有缺口。**

| 来源 | 覆盖结论及应负责的判据 |
|---|---|
| 换行、非法字符、常规续行、文档边界 | 本轮整改有效，未发现新的顺序漏检 |
| 转义、锚点／别名／标签、流式集合、块标量 | 现有宽判据会保守拒绝；不代表整份 YAML 已经可判定 |
| 引号上下文 | 属已有类别，但奇偶计数不足，应由可靠的上下文约束或更保守拒绝负责 |
| **块集合与普通标量结构** | 尚未覆盖；显式复杂键、序列／映射结构、其他字段的冒号上下文需要整份结构约束 |
| **隐式类型解析与对象构造** | 尚未覆盖；语法正确也可能构造失败，不属于换行或特殊符号问题 |
| 合并键的空白变体 | 属已有类别内部漏检；逐字 `<<:` 检查覆盖不到冒号前有空格的形式 |

对 **PyYAML 成功解析的合法配置**，本次未找到引号上下文之外的新错树类别；不能据此宣称完备。

**Q1：保守拒绝的总体取舍成立。** 在“缺库罕见、下游同样必须有 PyYAML”的前提下，宽容解析不能换来成功写入。没有证据支持为减少误伤而直接删除某组判据；其中引号奇偶计数的收益最难辩护，因为它既误拒部分合法内容，又漏掉真实跨行上下文。另需更正：**整行注释**中的单个引号会被跳过，参与计数的是**内容行尾注释**中的引号。

**Q2：未发现新的状态顺序早退问题。** 文档标记检查在 `:498`，整行注释跳过在 `:507`，所以前者在先。空行和整行注释保留 `_await_cont`，也不更新 `_seen_content`；续行检查在 `:510–515`，内容状态更新在 `:516`。引号内部的行仍可能被误分类，属于 MEDIUM-1。

**Q3：字符集运行行为完整，说明有误。** `_breaks` 仍是原来的八个字符；NEL／LS／PS 是 PyYAML 换行，另外五个是非法字符。LF／CR 由文件读取的通用换行处理覆盖。新增 `_nonprint` 与本机 **PyYAML 6.0.3** 的对应正则完全一致，逐 Unicode 码点比较无差异；五个重复拦截没有额外行为损害。

**Q4：既有 16 nodeid 的断言未变，解析结果逐条符合原表。**

| 对应用例 | 当前结果 |
|---|---|
| 无键 | 回退父目录 |
| 显式另一棵树 | 采用指定树 |
| 引号值＋尾注释 | 保留引号内完整值 |
| 空值＋注释 | 回退 |
| `#` 前无分隔 | 保留完整路径并拒绝不存在的树 |
| `#` 前 SP | 剥除注释，采用树 |
| `#` 前 TAB | YAML 错误，拒绝 |
| `#` 前 U+3000 | 保留字符与 `#`，按完整路径拒绝 |
| `#` 前 NBSP | 同上 |
| 值首 U+3000 | 保留，按完整相对路径拒绝 |
| 值首 NBSP | 同上 |
| 不存在的绝对路径 | 拒绝 |
| 不存在的 `~` 路径 | 展开后拒绝 |
| 引号包裹的坏路径 | 拒绝 |
| 不存在的相对路径 | 相对 vault 解析后拒绝 |
| 清空值 | 裸空值、空串均回退 |

TAB 的拒绝层上移，但原断言只要求非零退出与零写。上述是源码及内存解析核对，**不是重新认证 16 个端到端测试通过**。

**Q5：49 是上一轮数量，当前为 57。** 原 49 条未发现“两边绕过解析、共同早退”的伪等价：第 1–7、13 条比较完整路径拒因，仍有取值区分力；第 39、40 条共同回退符合预期。第 18、20、21、24、48 条在 PyYAML 侧实际是语法错误，不能作为合法结构同值的证据。当前第 **55–57** 条文档参数无法验证文件开头整改，原因见 LOW-1。

**Q6：两处自查修正属实。** `_breaks` 定义现在全为 ASCII 源码，没有那八种字面量字符。测试 `:7574` 实际拼成带 `\u005f` 转义的双引号键，PyYAML 还原结果确实是 **`harness_tree`**。

本次仅做限定范围读取、`python -B -c` 内存执行及只读路径核验；未修改文件、未运行写盘测试、未连接网络或数据库。作者报告的整套通过数与历史负控日志未独立复跑。
