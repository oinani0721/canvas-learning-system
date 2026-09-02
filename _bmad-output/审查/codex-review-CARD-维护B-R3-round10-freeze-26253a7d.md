BLOCKER/HIGH 清零：否（就计数取值口径而言）。

终裁：**FAIL**。终态 HEAD 正确且授权单测为 `263 passed`，但仍有 **3 组生产侧有界 HIGH + 1 组证据侧有界 HIGH**。未发现新 BLOCKER。又因审查轮次已经超限且未获追认，本报告不构成合并授权。

## 一、有界 HIGH

1. ❌ **区间首端可绕过负数、小数检查**

   `_D2_RANGE_RE` 的端点不含符号、小数边界；它可从首端负号或小数点之后重新起匹配。随后区间先被整体挖空，负数和小数门才运行。

   静态路径：若 `2`、`3` 都在池，`-2~3个` 会按 `2~3` 终核；`2.2~3个` 会从小数尾片匹配 `2~3`。两者随后都被挖空，不再进入负号/小数门。

   证据：[recap_scan.py:1590](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1590)、[recap_scan.py:1854](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1854)、[recap_scan.py:1866](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1866)、[recap_scan.py:1887](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1887)、[recap_scan.py:1912](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1912)。

2. ❌ **inline-code“纯计数”守卫仍在可见化之前分叉**

   数字和量词字面副本确已消除，但豁免判断仍作用于 raw code span，早于全角、HTML 实体、千分位、负号和小数处理。因此 `` `-5` 个``、`` `5.5个` ``、`` `1,005个` ``、`` `５个` ``会被当作普通字段值整段挖空，后续数值门看不到它们。

   这是已有语法范围内的执行顺序问题，不是未知 renderer 开放集。

   证据：[recap_scan.py:1498](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1498)、[recap_scan.py:1811](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1811)、[recap_scan.py:1820](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1820)。

3. ❌ **raw 专用绑定仍是有限、可枚举的 HIGH，且不止原登记三处**

   已登记的 seed ledger、五元组、tips 仍直接匹配 raw 文本：[recap_scan.py:1965](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1965)、[recap_scan.py:2039](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2039)、[recap_scan.py:2084](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2084)。

   另外两处也属于同一家族：

   - fallback ⑦先用可见文本通过白名单，却在 raw 行绑定前置 N：[recap_scan.py:2134](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2134)、[recap_scan.py:2351](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2351)。
   - signals 按 raw 连续 label 选行和 fullmatch；保留一条正确 raw 行，再增加一条渲染等价但 label 被强调/link 切开的冲突行，后者不会进入“逐条全查”：[recap_scan.py:1081](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1081)、[recap_scan.py:1124](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1124)、[recap_scan.py:1205](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1205)。

   这些入口有限，能够通过一次集中重构统一，因此应归为“有界”，不能归入 renderer 开放集。

4. ❌ **证据侧 HIGH：崩溃假阴仍未闭合**

   `run_suite` 仍只分析外层 pytest 的 `stdout`，完全丢弃 `stderr`。同时异常正则仍是类名后缀闭表，只认 `*Error`/`*Exception`，会漏掉 `SystemExit`、`TimeoutExpired`、裸 `Exception` 等 rc=1 形态。

   子 CLI 又分别捕获 stdout/stderr；若子进程 traceback 只在 stderr，外层可能只留下一个 `AssertionError`，当前判据会把生产崩溃错当成正常“判错变红”。

   证据：[test_recap_scan_signals.py:104](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:104)、[recap_domain_negverify.py:521](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:521)、[recap_domain_negverify.py:547](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:547)。

   ✅ `rc != 1` 拒收是正确且必要的，但不充分：[recap_domain_negverify.py:618](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:618)。

## 二、shortcut link 专项

- ✅ 顺序正确：inline → reference → shortcut，生产实现与注释一致：[recap_scan.py:1670](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1670)、[recap_scan.py:1687](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1687)。

- ✅ `[!x]` 和 `[^1]` 被负前瞻保留，且有精确单元门：[recap_scan.py:1639](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1639)、[test_recap_scan_signals.py:4213](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4213)。

- ⚠️ `[ ]` 会被匹配并替换成内部空格；标准任务框前缀未显示出计数级误伤，但当前没有 `[ ]`/`[x]` 门。`[x]` 会变成字面 `x`，并不等于真实 checkbox 渲染。

- ⚠️ 当前实现并未判断引用定义是否存在；测试中的 `总[计]987654` 也没有 `[计]: ...` 定义。因此它证明的是“无条件剥方括号”，不是完整 shortcut-link 语义：[test_recap_scan_signals.py:4225](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4225)。有效 shortcut、未解析 bracket、任务框的区分仍属于 renderer 开放面。

## 三、三张表与“定界宽、赋值窄”

- ✅ 没有再发现第三份可独立分叉的主 numeral/quant 字面副本。`_NUMERAL_LIKE_CHARS` 由数值表、单位表、extra 与 ASCII 机械生成；⑦⑧直接引用它；inline-code 的数字和量词也由主表派生：[recap_scan.py:1275](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1275)、[recap_scan.py:1326](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1326)、[recap_scan.py:1371](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1371)。

- ✅ 形式不变式成立：D2 与 fallback 主循环都以宽 `_NUM_RUN_*` 定界、经 `_join_free`，再由 `_count_token_value` 只给全 ASCII 或 `_CJK_NUM` 单字赋值：[recap_scan.py:1716](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1716)、[recap_scan.py:1912](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1912)、[recap_scan.py:2193](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2193)。

- ⚠️ 端到端不变式不成立：它只对“已经经过有损归一的 token”成立。`_join_free` 会删除读者仍能看见的字符，raw 专用入口及 inline-code 前置豁免也绕开该主循环。

- ⚠️ 按你转述的验收单登记，“三张表都是闭表”在字面上诚实，但风险画像偏平：

  - `_NUMERAL_LIKE_CHARS`、`_D2_QUANT` 漏项可直接导致漏检/尾片重锚；
  - `_CJK_NUM` 的窄只读赋值表在 token 已完整捕获时是 fail-closed，漏映射主要造成误拒；
  - 范围、小数、千分位、连接字符、负号、不可见字符也都是影响最终值的独立闭表，不能只登记前三张。

- ⚠️ `_D2_DECIMAL_RE` 仍手写 ASCII 数字式，但后面的 `_CJK_DECIMAL_RE` 是其承重超集；它目前是重复门、会重复诊断，不是第三张独立主表：[recap_scan.py:1474](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1474)。

## 四、round-8 九条终态复核

| 项 | 终态 | 复核 |
|---|---|---|
| HIGH-1 inline-code 量词副本 | ✅ | 量词与数字均由主表派生；但存在上述“先 raw 豁免”的新语义分叉。 |
| HIGH-2 ⑦⑧数词禁集 | ✅ | 生产副本已消除。测试注释仍称“副本存在”，已经过期：[test:4118](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4118)。 |
| HIGH-3 `_visible_text` 非统一入口 | ⚠️ | 原三处 raw 绑定未修，另有 fallback ⑦与 signals 两处同族。 |
| HIGH-4 reference-style link | ✅/⚠️ | 生产 `[t][r]`/`[t][]` 顺序正确；仍不是完整 renderer。 |
| HIGH-5 过度拼接不保值 | ⚠️ | 问题仍在；当前注释已诚实。 |
| HIGH-6 闭表外尾片重锚 | ⚠️ | 开放集，未修。 |
| HIGH-7 崩溃伪红 | ❌ | 枚举五异常虽已撤，但 stdout transport 与异常后缀闭表仍产生假阴。 |
| HIGH-8 逐项承重 | ⚠️ | 新增了单性质变体，但组合变异仍存，42/42 不能推出逐项承重。 |
| HIGH-9 门措辞/负号/量词 | ✅ | 指定的中文负号及 `例束艘架间` 已逐字覆盖；闭表全集问题仍开放。 |

## 五、round-13 回退判断

- ✅ 对“成对剥离 + 落单移出连接集”这个**具体方案**，回退成立：保留落单标记会让 `_NUM_RUN_PAT` 从其后尾片重新起匹配，只是把“错误拼接值”搬成“尾片重锚”。

- ⚠️ 这只证明该方案没有闭合收益；一次试修不能证明“问题不存在任何有界修法”。“已实测无有界修法”仍比证据宽。

证据：[recap_scan.py:1434](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1434)、[recap_scan.py:1571](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1571)。

## 六、negverify survivor-15…39

静态逐条结果：

- ✅ 有效且与目标性质一致：**15、16、18、22、23、26、28、29、30、31、32、33、34、35、37、38**。
- ⚠️ **17**：能关闭 D2 的 CJK 小数门，但不能单独证明两个消费点的全局性质。
- ⚠️ **19**：同时摘 fallback 千分位与小数；红灯无法分别归因。
- ⚠️ **20**：同时收窄逗号种类与连接字符容忍；已不再崩溃，但仍是组合变异。
- ❌ **21**：名称称“退回挖空后判句式”，实际只是 `is_claim = False`；非空，但不能证明所命名的顺序性质。
- ⚠️ **24**：替换了端点判值器，却没有真正禁掉共享 range/连接模式；命名比替换范围宽。
- ⚠️ **25**：一次关闭整个 `_visible_text`；且全局 `_INVISIBLE_ONE` 仍独立存在，所谓“零宽全部复活”已过期。
- ⚠️ **27**：同时删中文数词入口和冒号容忍。
- ⚠️ **36**：带圈数字与苏州码两组一起删除，不能分别归因。
- ⚠️ **39**：能破坏 `[t][r]`，但删除 reference handler 后，后置 shortcut 仍会还原 `[t][]`；未禁掉 reference-style 全部形态。

对应源码：[negverify.py:209](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:209)、[negverify.py:240](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:240)、[negverify.py:264](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:264)、[negverify.py:294](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:294)、[negverify.py:347](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:347)、[negverify.py:499](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:499)。

round-14/15/16 的 **40、41、42** 本身是定向变异；但 runner 的崩溃分类缺口仍会污染“42/42 全部承重”的总证明。

## 七、开放集——与上述有界 HIGH 分开

- ⚠️ **源码→Obsidian 渲染映射面**：highlight、math、图片/嵌入、引用定义、未解析 bracket、跨行语义等不在 `_visible_text` 的有限正则闭包内：[recap_scan.py:1612](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1612)。

- ⚠️ **闭表外数词/量词及尾片重锚**：未知 numeral-like 字可使匹配从尾片重新起步；未知量词可让整句不进检查面。

- ⚠️ **过度拼接不保值**：`* _ \ 多余来几约近超` 等既可能可见又被删除，池中的拼接值不证明读者所见表达有出处：[recap_scan.py:1437](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1437)。

这些开放项仍真实存在，但不应拿来遮蔽本报告列出的有限顺序、transport 与 raw-callsite HIGH。

## 八、新门质量

- ✅ `_CJK_NUM` 的期望值独立写死；合成窄池分别证明单字入池与多字 fail-closed，不是空洞门：[test_recap_scan_signals.py:3135](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3135)、[test_recap_scan_signals.py:3212](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3212)、[test_recap_scan_signals.py:3402](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3402)。

- ✅ `_one_problem_has` 确实要求类别与 token 出现在同一输出行：[test_recap_scan_signals.py:3442](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3442)。

- ⚠️ r13 CLI 门只检查 `987654`，没有同时约束诊断类别；证明力弱于前几轮的“类别 + 完整 token”门：[test_recap_scan_signals.py:4233](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4233)。

- ❌ 九形态崩溃单测只是直接喂字符串，没有覆盖 stderr/子进程→外层 pytest 的 transport：[test_recap_scan_signals.py:4236](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4236)。

- ⚠️ `run_suite` 注解/docstring 声称四元组，实际返回和解包五元组，属低等级名实不一致：[negverify.py:537](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:537)。

## 九、实际执行与边界

- `git rev-parse HEAD`：`26253a7d2d104f6cadc41d2834545f700d0054b7`，与目标短 SHA `26253a7d2d10` 一致。
- 授权 pytest：**263 passed, 14 warnings in 37.48s**。
- 第一次在只读沙箱内启动时因无可用临时目录而在收集前退出；同一命令获准在沙箱外重跑后得到上述真实结果。
- 未运行 `git status`；因为 HEAD 与测试计数均匹配，按硬限未增加第二条 git 命令，因此也不额外宣称工作树 clean。
- 未运行 negverify、探针、临时脚本；未读取 fixtures 下 `.md`/`.json` 正文。
- `42/42`、`595 passed`、`84/84` 均仅作为车道提供的数据登记，未在本轮独立复跑。


