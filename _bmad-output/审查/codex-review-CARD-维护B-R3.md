BLOCKER/HIGH 清零：否

指定基线成立：HEAD 为 `85d5c32c74f5e2e3268f56c0eb7c0d873566abbf`；指定 pytest 最终结果为 `276 passed, 14 warnings in 51.53s`。

### 本轮四组处置

- ✅ 零种子五个已测形态各自符合预期。[test_recap_scan_signals.py:5164](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:5164)、[recap_scan.py:2205](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2205)、[recap_scan.py:2248](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2248)

  - `seeds=[]`、无种子小节：放行。
  - `seeds=[]`、认可且真正为空的小节：放行。
  - 确有种子却无小节：拒绝。
  - `seeds=[]` 却在认可小节写 Ghost 行：空绑定面自然报“不在 ledger”。
  - 无 ledger 且有认可小节：报“无可用 ledger”。

- ❌ HIGH（存量 H3 未闭合）五形态之外仍有第六形态。[recap_scan.py:2181](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2181)、[recap_scan.py:2205](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2205)

  `seeds=[]` + Obsidian 合法但 `_SECTION_RE` 不认的 `### 种子 ###` + `- Ghost — 批注 9 条` 时，`sections=[]` 且 `_seed_rows=[]` 为假，函数直接返回。更强的形态是：先放一个认可的空 `### 种子`，再放第二个不认可 H3 和 Ghost 行；第二块永远不审，非零种子同样可绕。R26 未覆盖这两种组合。

- ⚠️ R26 的“真的没有 ledger ⇒ 仍 fail-closed”措辞过宽。[test_recap_scan_signals.py:5190](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:5190) 只测了“无 ledger + 有认可 H3”；无 ledger 且无认可 H3 会提前无错返回。测试也没有传入或验证 `counts.seeds == 0`，只测 helper 的 `ledger`。

- ⚠️ 损坏的 `seeds=[None]` 也会被过滤成空 `rows`，随后因原值仍是 list 而被当成合法零种子。[recap_scan.py:2234](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2234)

- ✅ #51 改名已经准确。[recap_domain_negverify.py:607](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:607) 确实把 `vis_lines` 整体退回 raw。变异后恶意冲突行仍被非模板门拒绝，真正红点是合法 `批**注** 2 条` 被误拒，[test_recap_scan_signals.py:4748](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4748) 与新说明一致。

- ✅/⚠️ #55 的替换描述准确、承重措辞仍须收窄。[recap_domain_negverify.py:651](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:651) 把剥围栏结果换回原文，严格导致 `_in_fence` 全为 `False`。但 R23 的 fenced-seed 在原版和变异版下最终都被拒绝，只是诊断从“找不到可绑定”变成数字/非模板错误，[test_recap_scan_signals.py:4981](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4981)。它证明错误路由，不证明最终 PASS→FAIL 的误伤。

- ✅ #56 两步变异现在确实先恢复跨角色摊平，再强制 `seeds=None`；不再是旧版早退假红。[recap_domain_negverify.py:663](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:663)

### “未改动的三处”

三项判断都成立：

- ⚠️ R23 虽名为 `_cli`，实际只直接调用 `_verify_seed_ledger_counts`；`tmp_path` 也未使用。[test_recap_scan_signals.py:4916](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4916)、[test_recap_scan_signals.py:4936](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4936)

- ⚠️ 源码形状门仍在，按字符串统计 `_visible_block(` 调用及精确源码片段。[test_recap_scan_signals.py:4763](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4763) 它不是恒真，但死调用或“删真实调用、添无关调用”可以保持计数；等价重构也会假红。注释还写“四处消费方”，实际断言已是三处。

- ⚠️ `-k` 仍只确认匹配集合里有失败，不确认目标 test/nodeid/断言失败。[recap_domain_negverify.py:841](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:841)、[recap_domain_negverify.py:991](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:991)

没有发现新增门中的字面恒真断言，但有目标无关假绿面：

- R20 恶意例只断言 `returncode != 0`，[test_recap_scan_signals.py:4748](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4748)，崩溃或无关拒绝也算绿。
- R26 三个拒绝例只断言 `ps` 非空，[test_recap_scan_signals.py:5198](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:5198)，没有核各自目标诊断。
- R23 文案声称“八种形态”，实际参数表有九项。
- `count(old)==1` 已在预检逐条落实，[recap_domain_negverify.py:925](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:925)；但预检与实际变异分别读取源码，实际应用仍只检查 `old in text`。[recap_domain_negverify.py:916](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:916)、[recap_domain_negverify.py:955](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:955) 两次读取间若文件变化，仍可能只替换重复锚点中的第一个。

### 崩溃二分

- ⚠️ 当前实现并不是“有冒号即异常”。真实规则是 `E` 后 1–3 格、随后 ASCII/点分标识符，再排除 `assert` 与 `AssertionError`；无冒号异常也算。[recap_domain_negverify.py:803](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:803)、[recap_domain_negverify.py:818](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:818)

- ✅ 在当前仓库 `--tb=short` 的已测样本里，3 格顶层和 4–7 格续行的区分自洽。[test_recap_scan_signals.py:4618](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4618)

- ⚠️ 仍会判错：`pytest.fail()` 或自定义断言类可被误判成崩溃；formatter/tb 风格改变可能改变缩进；内层无 traceback 的 `SyntaxError`、致命信号会假阴；正文或断言消息偶含 `Traceback…`/`N errors` 会假阳。源码已在 [recap_domain_negverify.py:767](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:767) 如实承认这不是可靠二分。

### 其余未闭合 HIGH

以下为静态控制流复算；因你禁止探针，没有冒充运行观测：

- ❌ HIGH（存量）`1\*5个` 仍会被归一为 `15`，`5多个` 被当精确 5。[recap_scan.py:1475](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1475)、[recap_scan.py:1773](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1773)

- ❌ HIGH（本次新发现，无法判断是否本轮引入）code span 的字符白名单不含 `+`，所以 ``本板共有 `+999` 个`` 会把整个可见数挖空。[recap_scan.py:1555](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1555)、[recap_scan.py:1559](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1559)

- ❌ HIGH（本次新发现）数值定界是封闭表；Arabic-Indic 等可见数字不进入 `_NUM_RUN_PAT`。`本板共有 ٩٩٩ 个…` 命中规模句式，却没有 token 可核。[recap_scan.py:1362](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1362)、[recap_scan.py:1667](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1667)

- ❌ HIGH（本次新发现）链式区间可从后半重锚：`本板共有999到2-3个…` 只核 2/3并挖空后半，999 随后不再紧邻量词。[recap_scan.py:1691](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1691)、[recap_scan.py:1766](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1766)、[recap_scan.py:1986](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1986)

- ❌ HIGH（存量）③段信号只绑定 raw 定位出的 section；段外只对 raw 字面“无来源结论”有单项守卫。其余三个信号可在附录追加冲突数字，“无**来源**结论”也可绕过段外 raw 守卫。[recap_scan.py:1141](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1141)、[recap_scan.py:2473](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2473)

- ❌ HIGH（存量）tips 两数仍在 raw 文本中匹配；保留真行后追加 `tips 批**注**共 999 条` 不进入绑定。[recap_scan.py:2420](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2420)、[recap_scan.py:2436](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2436)

- ❌ HIGH（存量）D2 切段时丢掉 H2 标题行，因此 `## 三维审查（999 个节点）` 中的 999 不核；豁免判断又接受 ASCII `(`，与 `_SECTION_RE` 分叉。[recap_scan.py:1919](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1919)、[recap_scan.py:1932](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1932)

- ⚠️ “尾巴只拦 ASCII”这句不准确：Python `\d` 包含 Unicode decimal digits。真实边界是只认固定词序 `批注 \d+ 条`；中文数词及 `批注数为 999 条` 仍漏。[recap_scan.py:2093](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2093)

- ❌ HIGH（存量设计）D2 不是具体字段绑定，而是全 JSON 数值池，并额外合成 JSON 中未实际出现的一阶和/差。[recap_scan.py:1646](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1646) 这不满足严格意义上的“同值在 JSON 中有出处”。

### 闭合分组

一次改动内可以闭合：

- 修 `not sections` 三分支，区分合法空 seeds、非空 seeds、缺失/损坏 ledger；补“关闭式 ATX + Ghost”“认可空节 + 第二个异常 H3”“无 ledger + 无 H3”，并核精确诊断。
- 给 code span 增加 `+`/`＋` 双向门；给 range 左缘加入“前一端点 + 另一区间符”保护。
- tips 改为 visible 空间逐条绑定。
- R23 改 `_helper` 名或补真实 CLI；#55 指向一个真正 PASS→FAIL 的围栏误伤用例。
- 将预检与实际变异绑定到同一份 bytes，并在实际替换处继续检查恰好一次。
- 修 R26、R20 的 `ps`/非零退出断言为目标诊断、无 traceback、明确 rc。

需要重做设计：

- 用统一 Markdown/Obsidian 结构解析结果处理 H2/H3、合法 ATX、围栏、codespan 与显示文本，消除三套③定位及 `_SECTION_RE` 分叉。
- 用统一 Unicode 数值 tokenizer，并以“声明语义 → scan 具体字段”绑定替代全 JSON 池及和差碰撞。
- mutation runner 改为隔离副本执行，并消费结构化 test/nodeid/异常状态；不要再解析 pytest 渲染或原地改生产源码。
- 明确代码块中“用户可见数字是否属于报告断言”的产品口径。

### 验证记录与限制

- ✅ 实跑：`276 passed, 14 warnings in 51.53s`，退出码 0。
- ✅ 实跑：`git rev-parse HEAD` 得到指定 SHA。
- ⚠️ 首次同一 pytest 命令因只读沙箱无可用临时目录，在收集前报 `FileNotFoundError`；沙箱外按原命令重跑后通过。
- 未运行 `recap_domain_negverify.py`、608 扩大回归或自报的 62/62；未构造探针；未读取 fixtures 正文；未运行 `git diff/show/log`；未修改任何文件。
- 因禁止历史 diff，无法证明“本次新发现”究竟由本轮引入还是更早存在。
- 当前会话没有 `graphiti-canvas/search_memory_facts` 工具，故 Graphiti 协议无法执行。


