BLOCKER/HIGH 清零：否

有效基线为 `272 passed, 15 warnings in 44.97s`，但源码静态反例表明仍有多处“校验文本 ≠ Obsidian 用户所见文本”的 HIGH。

### 本轮四组改动

- ❌ HIGH｜围栏前缀只修对了一半。[recap_scan.py:1040–1083](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1040)

  无 marker 的四格缩进现在确实会保留；`>```、> > ```、- ```、- - ```、1. ```、1) ```` 也能识别。

  但 marker 后的 `[^\S\n]*` 会吞任意空白。例如 `>` 后 5 格再跟三反引号，会被剥成顶层 fence；CommonMark 中其中至多 1 格属于引用 padding，余下 4 格使其成为 indented code，不应开栏。由于纯引用没有 `fence_list_col`，其后的可见正文会被错误剥掉。

  列表 continuation 也未建模：`- item` 后缩进 2 格的 fence 会开栏，却不记录列表边界，之后已经出列表容器的可见正文仍可能被吞；`10. item` 后相对内容列合法的 4 格 fence 又会被当作顶层四格而拒识。继续补单条 regex 无法闭合这一面。

- ❌ HIGH｜`_tail_conflict()` 的狭义裸文本路径正确，但渲染边界未堵住。[recap_scan.py:2073–2090](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2073)、[recap_scan.py:2191–2203](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2191)

  裸 `批注 2 条（批注 999 条）` 会 fail-closed，且其它已声明不绑定字段会放行，这部分正确。

  但 raw 节点精确命中后只检查 `raw_ms` 并立即 `continue`。因此尾巴写成 `批**注** 999 条`、`批<b>注</b> 999 条` 或全角数字时，用户看到第二个同名字段，检查却漏掉。反向边界也不准：`未批注 999 条` 会因 substring 命中而被当成同名字段。

- ❌ HIGH｜种子小节范围仍未收口。[recap_scan.py:2124–2148](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2124)

  围栏状态仅遇到任何三反引号/波浪线就布尔翻转，不校验同字符、长度、合法闭栏尾巴或 info string。四反引号开栏、块内三反引号伪闭栏、四反引号真闭栏，会使状态依次变成 `True → False → True`，从而跳过真闭栏后的可见冲突小节。

  父级又用 `"台账" in heading`，[recap_scan.py:2141](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2141) 会把 `## 非台账示例` 纳入。`### 种子 ###` 这种渲染等价的合法 ATX 标题不被识别，而非合法标题 `###种子` 反而会命中。[recap_scan.py:2144](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2144)

  另外绑定索引摊平了 ledger 的所有角色，不只 `seeds`；派生节点可被放进“种子”小节并按其 `tips_count` 通过。[recap_scan.py:2154–2165](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2154)

- ✅/⚠️｜preflight 的实现增强正确，说明仍矛盾。[recap_domain_negverify.py:803–820](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:803)

  它现在确实按真实顺序模拟整组替换、要求每个锚点唯一，并要求最终源码变化；成功消息也已注明不证明语义承重。

  但 docstring 先说能证明“替换非空”，下一条又说“不证明替换非空”。后者应改成“不证明行为非空/目标防线确被禁掉”。[recap_domain_negverify.py:787–793](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:787)

  当前代码中，失效的 survivor-7 锚点会由 `hits != 1` 抓到，而不是由最终 `mutated == src` 检查抓到；所以“survivor-7 证明了新增最终变化门”这一归因过宽。

### 行为门与变异证据

- ⚠️ 没发现新增门存在字面恒真断言；R19 的 monkeypatch 哨兵确实替代了此前恒真的源码自读检查。[test_recap_scan_signals.py:4654–4680](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4654)

- ⚠️ R22 四格拒绝门不是完整的“诊断原因绑定”：它只要求非零并在某条输出行看到 `987654`，没有同时绑定“找不到同值来源/围栏误判”类别。[test_recap_scan_signals.py:4875–4878](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4875)

- ❌ R22 文案声称证明“种子小节不在围栏内才生效”，实际只测了 `## 附录`，没有 fenced-seed 用例。[test_recap_scan_signals.py:4842–4896](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4842)

- ❌ `survivor-51` 的归因已经失真。[recap_domain_negverify.py:607–614](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:607)

  把 visible 行退回 raw 后，格式化冲突行仍会撞上“非模板行”防线；真正变红的是“格式化但数值正确的行应 PASS”正控。[test_recap_scan_signals.py:4748–4754](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4748) 因此它证明的是双向兼容性承重，不是名称所称的“双行冲突逃逸”。

- ⚠️ survivor-53/54 的替换各自落在活路径，方向正确；但 54 个 mutant 中没有 `_tail_conflict` 或 fenced-seed 状态机变体。`-k A or B` 加“只需至少一个失败”的策略，也仍只能证明集合中至少一道门承重。[recap_domain_negverify.py:101–114](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:101)、[recap_domain_negverify.py:877–898](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:877)

### 崩溃识别

- ✅ 对测试列出的当前 `--tb=short` 形态，分类结果正确。
- ⚠️ 实现已经不是“有冒号类名 vs 缩进续行”，而是 `^E {1,3}<标识符>` 加 `assert/AssertionError` 白名单。[recap_domain_negverify.py:692–716](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:692)
- ❌ 它不是可靠二分：1–3 格的自由续行可能假阳；4 格以上异常、Unicode 异常类名、子进程无 traceback 的 `SyntaxError`/致命信号可能假阴；正文偶含 traceback 或 `N error(s)` 又可能假阳。
- ⚠️ `[[CHILD-CRASH]]` 也只是字符串标记：测试 helper 仅凭 stderr 含 traceback 打标，甚至未结合 return code。[test_recap_scan_signals.py:109–126](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:109)
- ⚠️ `run_suite` 注解/docstring写四元组，实际返回五元组。[recap_domain_negverify.py:720–768](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:720)

### 存量判断

你列出的未改项均成立：

- ❌ tips 两数仍从 raw `text` 提取。[recap_scan.py:2321–2352](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2321)
- ❌ ③段标题仍先在 raw 文本定位。[recap_scan.py:1121](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1121)、[recap_scan.py:2374](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2374)
- ❌ D2 每段从 `h.end()` 开始，H2 标题行自身的可见数字不受检。[recap_scan.py:1899–1905](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1899)
- ⚠️ `_visible_text` 明确不是完整 renderer；highlight、转义后 HTML、math、脚注及未配对强调字符仍有偏差。[recap_scan.py:1693–1713](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1693)
- ⚠️ `_join_free` 的过度拼接和封闭 numeral/量词表仍在。[recap_scan.py:1455–1470](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1455)
- ✅ 在当前封闭语法内，code-span 判定、区间两端终核、单字中文/ASCII 判值以及 fallback m7 的 visible N 绑定均为活分支，局部逻辑正确。[recap_scan.py:1539](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1539)、[recap_scan.py:1966](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1966)、[recap_scan.py:2387](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2387)

### 闭合分类

一次改动内可以闭合：

- tail 始终在同源 visible 行上查第二字段，并补格式化、全角、近邻负控及对应 mutant。
- 父级 H2 改为精确“台账/台账（补充）”，统一合法 ATX 语法；只索引 `ledger.seeds`。
- tips/③段改为同源 visible 定位；D2 纳入非豁免 H2 标题。
- R22 绑定诊断类别；补 fenced-seed 门。
- 修 survivor-51 名称或变异内容、preflight 文案、五元组注解及测试 docstring 的 `\s` SyntaxWarning。

需要重做设计：

- `_strip_code_blocks` 与 seed 围栏扫描合并为一个真正维护 blockquote/list 容器、相对列、tab 与 fence 开闭规则的解析器。
- 要求“与 Obsidian 渲染后相同”时，应复用实际 Markdown 解析结果或定义受支持语法白名单，不能继续扩张 `_visible_text` 正则。
- 崩溃/断言失败改用结构化执行结果，不解析 pytest 的渲染文本。
- 变异验证拆成单性质、单门，并逐门验证失败原因。

### 实际运行

- `git rev-parse HEAD`：`8fa72b2fd4ab8e4cf534a8aa7c0aef335873b2dd`
- 指定 pytest：`272 passed, 15 warnings in 44.97s`
- 首次在只读沙箱内启动时因无可写临时目录而在收集前失败；同一命令获准在可写临时目录边界重跑后得到上述有效结果。

验证限制：未运行 `recap_domain_negverify.py`，未独立确认自报的 `54/54` 或 `604 passed`；未读 fixtures 的 `.md/.json` 正文；未运行 `git diff/show/log`；未构造探针或临时文件。项目要求的 Graphiti 工具本轮不可用，因此没有伪称完成该查询。


