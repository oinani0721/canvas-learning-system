BLOCKER/HIGH 清零：否

未发现需另立 BLOCKER 的问题，但仍有多条 HIGH 可直接造成“校验器读到的数 ≠ Obsidian 用户看到的数”。

### 本轮改动

- ⚠️ HIGH｜围栏容器区分仅修对窄例。[recap_scan.py:1046-1103](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1046)

  顶层 opener 后的 `- ``` ` 现在不会误闭，目标反例已修。但三类容器仍不正确：

  - 顶层 fence 内的 `> ``` ` 会被剥引用前缀后误闭；真正闭栏反而重新开栏，随后可见计数被剥到 EOF。
  - `> ``` ` 在引用内开栏后，下一行不带 `>` 时，CommonMark 中围栏随引用容器结束；实现却继续剥正文。
  - `10. ``` ` 的列表内容列是 4，合法闭栏 `    ``` ` 因实现只接受绝对 0–3 格而无法关闭。
  - `fence_list_col` 用整行未锚定搜索；顶层 info string 如 `````text - demo`` 会被误判成列表 opener。

  CommonMark 要求闭栏属于同一包含块；未闭合围栏在所在 block quote/list item/document 结束时终止，列表缩进按内容列计算。[Fenced code blocks](https://spec.commonmark.org/0.31.2/#fenced-code-blocks)、[List items](https://spec.commonmark.org/0.31.2/#list-items)

- ✅/⚠️ HIGH｜`(?<!未)批注` 的目标修复正确，但数字域仍漏。[recap_scan.py:2093-2117](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2093)

  `累计/共/已批注 999 条` 会命中，紧邻的 `未批注` 会排除，分支可达。问题是尾部只抓 `\d+`：`共批注 九 条`、反引号切开的可见“批注”、带其他合法数值格式的第二计数仍会漏。反向误伤也存在：与主值相同的重复计数仍被报“冲突”，`未曾批注`、`没有批注` 等否定表达也可能误报。

- ⚠️ HIGH｜ATX 两式只在普通 ASCII 行上基本正确。[recap_scan.py:2167-2175](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2167)

  正确接受 0–3 个 ASCII 空格和 `### 种子 ###`，正确拒绝 `###种子`、`### 种子###`。但接受集不等于 CommonMark：

  - `[^\S\n]` 还接受 NBSP、VT、FF；CommonMark 的结构空白是 space/tab。
  - 先 `_visible_text`、再识别块结构，会把 `**## 非标题**` 伪造成 H2。
  - `### 种子 &#35;` 中实体表示可见内容，不能形成语法 closing hash；实现解码后会误当闭合序列。
  - `### `种子`` 是合法且渲染为“种子”的 H3，却因实现保留反引号而漏识别。
  - 引用/列表容器内的合法 ATX 未覆盖。

  依据见 [CommonMark ATX headings](https://spec.commonmark.org/0.31.2/#atx-headings)。

- ❌ HIGH｜新 H2 与必需段口径分叉，形成直接绕过。[recap_scan.py:1257-1265](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1257)、[recap_scan.py:2183-2195](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2183)

  `_SECTION_RE` 接受未闭合的 `## 台账（x`，新 `_H2_LEDGER_RE` 不接受。于是：

  ```md
  ## 台账（x
  ### 种子
  - A — 批注 999 条
  ```

  必需段门认为台账存在，但种子校验器得到零个 section 后直接返回，999 不绑定。反向，新 helper 接受的 `   ## 台账`、`## 台账 ###` 又会被全局必需段门拒绝。因此新增 ATX 接受并非端到端生效。

- ✅/⚠️｜`seeds` 缺失/非 list 的 fail-closed 正确且可达。[recap_scan.py:2197-2221](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2197)

  但存在两点：

  - ⚠️ MEDIUM｜合法 `seeds: []` 加空种子小节也会报“无可用 ledger”，是潜在合法零值回归。
  - ❌ HIGH｜legacy flat list 仍摊平所有 dict，带 `role: derived` 的节点可冒充 seed。[recap_scan.py:2217-2218](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2217)

- ❌ HIGH｜“小节内跳过围栏”只保护了消费行，没有保护小节终点。[recap_scan.py:2186-2191](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2186)、[recap_scan.py:2232-2236](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2232)

  围栏内的 `##/### 假标题` 会提前截断种子小节；真闭栏后的可见冲突行完全不再遍历。这是本轮修复未闭合，可局部修复。

- ✅/⚠️｜数值、codespan、区间主分支没有发现新增死分支。[recap_scan.py:1539-1593](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1539)、[recap_scan.py:1847-1885](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1847)、[recap_scan.py:1986-2008](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1986)

  已列举的整数、单字 CJK、符号、小数、千分位和二端区间会走预期路径，区间两端均终核。但提取域仍是封闭枚举：Arabic-Indic `٥` 可能完全抽不到 token；`1e5个` 可能从尾部重新锚到 `5`。因此不能宣称覆盖“用户可见的所有数字”。

### 行为门、变异与崩溃识别

- ⚠️ R24 没有字面恒真断言，但文案明显宽于实测。[test_recap_scan_signals.py:4984-5062](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4984)

  - 只测顶层 `- ``` `，未测引用 marker、引用深度、info string。
  - 列表样例 `.strip() == ""` 无法区分“错误地闭栏”和“正确地结束旧 item、在 sibling item 重开 fence”；两种解释都会得到空输出。
  - “缺失/非 list”实际只测缺失。
  - 围栏门只测普通 row，未测围栏内标题截断 section。
  - ATX 只组合测三格缩进，未测四格拒绝、Unicode 空白或 H2 closing hash。
  - helper 绿测未覆盖 `_SECTION_RE` 的全局口径分叉。

- ❌ HIGH｜“58/58 变红”不能证明 58 条 mutant 均按名称所称防线承重。[recap_domain_negverify.py:607-687](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:607)、[recap_domain_negverify.py:931-952](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:931)

  - survivor-51 退回 raw 后，现有非模板 fail-closed 仍会挡冲突；变红主要可能来自合法强调行被误拒，并非“双行逃逸”。
  - survivor-56 把 `seeds` 设为 `None`，只会触发缺失错误，从未恢复“摊平所有角色”。
  - survivor-14、48 会同时破坏合法输入或共享表，归因过宽。
  - 新增 survivor-57、58 的替换本身是针对性的：确实分别重新打开顶层 list-marker 误闭和“排除所有汉字前缀”。

- ⚠️ 崩溃二分仅对当前合成输出成立，不是可靠的 pytest 通则。[recap_domain_negverify.py:701-765](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:701)、[test_recap_scan_signals.py:4585-4648](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4585)

  `E   <类名>:` 与 `E     <续行>` 对当前样例判对，但仍会：

  - 把恰有三格且以类名样式开头的断言续行误判为异常；
  - 把生产代码自身抛出的 `AssertionError` 当成“正常变红”；
  - 把语义测试主动调用的 `pytest.fail()`/`Failed:` 当崩溃；
  - 漏掉无 canonical traceback 的 SyntaxError、fatal signal 或其他 formatter 形态。

  更根本的问题是 runner 只要求“出现任意失败”，不验证失败方向、测试 ID 和预期原因；survivor-51/56 已是源码级反例。

### 存量未闭合

- ❌ HIGH｜tips 两数仍在 raw 文本空间。[recap_scan.py:2383-2404](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2383)
- ❌ HIGH｜③段仍以 raw `^### ③` 多处定位，且边界口径不一致。[recap_scan.py:1141-1143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1141)、[recap_scan.py:2435-2439](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2435)
- ❌ HIGH｜D2 从 H2 结束位置取 body，H2 标题行自身的可见计数不检查。[recap_scan.py:1919-1924](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1919)
- ❌ HIGH｜fallback m7 对 `_visible_text` 保留的 inline-code 反引号仍失配；用户看到连续“派生”，两个门都可能跳过。[recap_scan.py:2449-2459](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2449)、[recap_scan.py:2683-2691](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2683)
- ❌ HIGH｜缩进代码未纳入 fence map；无据式信号接受任意空白，有数式只拦行首缩进，`>     来源覆盖率…` 仍可能作为正文命中。[recap_scan.py:1178-1183](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1178)、[recap_scan.py:1240-1244](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1240)
- ⚠️ LOW｜“行数不变”措辞只在 seed 注释中更正；两个 docstring 仍作过宽承诺。[recap_scan.py:995-1000](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:995)、[recap_scan.py:1813-1823](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1813)

因此，“列表 continuation、tips raw、③ raw、D2 丢 H2、`_visible_text` 非完整 renderer、变异归因过宽均未改”的判断成立。

### 闭合建议

一次改动内可以闭合：

- section 终点排除 `_in_fence`；
- 统一 `_SECTION_RE` 与 H2 唯一语法源；
- 区分 `seeds=[]` 与缺失/损坏，并收紧 flat role；
- tips 使用同一 visible-line 映射，D2 纳入 H2 标题行；
- tail 复用共享 count-token 语法并处理不可解析计数；
- 统一拒绝缩进代码信号；
- 修 survivor-51/56/48，并要求预期测试、失败方向和原因；
- 更正文档及 R24 措辞/覆盖。

需要重做设计：

- CommonMark/Obsidian 容器栈：引用深度、list content column、continuation、sibling item、边界行重解析；
- 先从 raw/AST 判块结构，再提取 inline 可见文本，替换 `_visible_text` 正则近似；
- 完整且“必须消费完”的数字文法；
- 结构化子进程结果与 mutant 预期，而不是解析 pytest 文本并接受任意红灯。

### 实际验证

- ✅ `git rev-parse HEAD`：`1cd60017ac41b579bbaf50800550266d589da04b`，与预期一致。
- ✅ 指定 pytest：`274 passed, 14 warnings in 43.85s`；未观察到该 docstring 的 `SyntaxWarning`。
- ⚠️ 首次只读沙箱运行因系统临时目录不可用而在收集前退出；随后以完全相同命令获准重跑，上述 274 是有效重跑结果。
- 未运行变异脚本或 606 扩大回归；58/58、源码前后字节一致、606 passed 仍只是车道自报。
- 未使用 `git diff/show/log`，未构造探针或临时文件，未读 fixtures 正文，未运行 Obsidian renderer；渲染结论来自源码状态机与 CommonMark 规范推演，不能替代 Obsidian 运行时实测。


