BLOCKER/HIGH 清零：否

总判定：round-35 修复确实堵住了所述“第三态”；round-36 也比 `-k` 判据可靠。但核心“渲染所见数字 = 校验数字”仍有可放行通道，台账新门同时存在漏检与误伤，变异证明也仍有语义粒度缺口。

### 主要发现

❌ **BLOCKER（存量，本轮新定位载体）** — Obsidian `%%…%%` 注释仍可制造“隐藏硬断点 → 尾片 0 重锚”。

- `_visible_text` 不处理 `%%` 注释，而全局只禁 HTML 注释标记：[recap_scan.py:1773](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1773)、[recap_scan.py:2724](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2724)。
- 静态路径：`本板共有987654%%x%%0个子节点` 在 Obsidian 阅读视图隐藏注释后显示为连续的 `9876540`；校验器仍在 `%/x` 处断开，只提取量词前的 `0`。任一非空数值池都会由 `abs(a-a)` 生成 0：[recap_scan.py:1646](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1646)。
- 这是与 highlight/math 已登记缺口同族的 renderer-open-set 问题；测试自己也明确承认 `==x==`、`$x$` 未覆盖：[test_recap_scan_signals.py:3937](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3937)。
- 本轮没有启动 Obsidian 做 UI 实测，因此这里是源码路径加 Obsidian 注释语义的静态复现；已登记的软换行 A1 则本身已足以维持 BLOCKER。

❌ **HIGH（台账新门）** — 所谓“认可小节之外”实际只检查“被 `_h3_wellformed` 判坏的 H3 之后”。

条件是 `_covered / _in_fence / not _bad_h3` 三项跳过：[recap_scan.py:2257](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2257)、[recap_scan.py:2277](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2277)。因此它不是诊断声称的“所有认可种子小节之外”。

确定存在“第八形态”：

- `### \`种子\``、`### ==种子==`、`###  种子`、`###\t种子` 都不匹配精确 `_H3_SEED_RE`，却会被 `_h3_wellformed` 判为正常 H3，故后面的 `Ghost — 批注 999 条` 被跳过。
- 现有 inline-code/highlight 两门都额外带了尾随 ` ###`：[test_recap_scan_signals.py:5267](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:5267)。它们现在变红是因为“闭合井号被判不合规”，不是因为 inline-code/highlight 归一承重；去掉尾随 closer 即进入上述漏检。
- 已登记的“第一个 H3 之前”也仍漏：`_cur_bad` 初始为 `False`，所以 H2 后、首个 H3 前的台账形状行不进新门。

⚠️ **范围误伤（台账新门）** — `### 派生 ###` 是合法 ATX 闭合写法，旧测试注释也明确如此：[test_recap_scan_signals.py:4930](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4930)。当前 `_h3_wellformed` 却把它判坏；其下合法派生同形行会被误报成“必须写在种子小节”。

此外：

- `### 派生` 正例只用了与 scan 对得上的 `X/1`：[test_recap_scan_signals.py:5280](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:5280)，没有把它改成 `Ghost/999` 证明真实绑定；事实上派生节不进入 binder。
- 所谓“围栏内同形行”正例只有围栏内标题，没有台账形状行：[test_recap_scan_signals.py:5291](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:5291)。
- 指定文件里找到的是正文/附录的说明 H3，不是“台账内说明性 H3”：[test_recap_scan_signals.py:5285](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:5285)。
- 门注释声称“六种、三报三放”，实际表是十种、五报五放：[test_recap_scan_signals.py:5227](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:5227)。

❌ **HIGH（存量，本轮新发现）** — 台账可见数字有现成 JSON 字段，却没有绑定。

`_tail_conflict` 和测试均声称 `理解度未闭环 N` / `已派生 N` 没有逐节点字段：[recap_scan.py:2115](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2115)、[test_recap_scan_signals.py:4858](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4858)，但源码实际已有：

- `tips_open`：[recap_scan.py:483](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:483)、[recap_scan.py:623](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:623)
- manifest 的 `derived_children_count`：[recap_scan.py:3064](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:3064)
- 两者随完整 ledger 输出：[recap_scan.py:3128](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:3128)

当前 binder 只构造 `tips_count` 索引并遍历种子小节：[recap_scan.py:2311](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2311)。测试报告甚至硬编码了派生行 `tips 未闭环 2 条`：[test_recap_scan_signals.py:707](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:707)。manifest 报告里这些数字可改成任意值而不做逐节点绑定。

### round-35

✅ **指定修复成立** — 新前瞻 `(?=[0-9])` 会把所列四种形态完整归一：[recap_scan.py:1840](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1840)。`survivor-66` 精确恢复旧三位前瞻：[recap_domain_negverify.py:783](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:783)，而 r29 在 helper 断言前先走真实 CLI；该变异会在首个 `987654,0` 场景变红，不是假承重：[test_recap_scan_signals.py:5391](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:5391)。

⚠️ **round-35 引入的语义扩张** — 该式不是只删“千分位”，而是删除任何两个 ASCII 数字之间的逗号/撇号，且两侧可吞 `_D2_JOIN_ONE`。后者包含空白及“多余来几约近超”等可见字：[recap_scan.py:1457](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1457)。因此：

- `1, 2个`、`1,约2个` 都会被送成 `12个`；
- 若 12 在池里会假放行；若用户原本表达两个可见数字，则诊断也会错位。

所以“没有新误伤”尚不能成立。更稳妥的策略是识别完整候选，再将合法分组解析、非法/含糊分隔 fail-closed，而不是无条件剥除。

⚠️ **仍有同族硬断点** — `987654,,0`、`987654,，0`、表外撇号/prime，以及上述 `%%…%%` 都能留下断点。所谓“两态”只对“单个、表内、ASCII 数字两侧”的分隔符成立。

⚠️ **r29 门措辞偏宽** — 五个 CLI 场景只断言 `rc != 0`，不绑定完整值及目标诊断；前提也只锁了 `987654∉pool`、`0∈pool`：[test_recap_scan_signals.py:5387](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:5387)。`987654,000` 仍是“池外数被拒”的负例，不是“真实池内值采用千分位后仍通过”的正例。

### round-36

✅ **12 条人工指名没有发现完全指错**。逐项对照后，`survivor-1/6/7/8/9/11/12/15/18/22` 与变异性质方向一致；`survivor-7` 的替换面还包含列表容器，现指名主要证明引用层，措辞应收窄。冻结表见 [recap_domain_negverify.py:929](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:929)。

⚠️ 两条只算“性质相关”，不能证明目标生产行为：

- `survivor-14` 把 `_join_free` 变恒等：[recap_domain_negverify.py:205](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:205)。危险输入仍可能 fail-closed，只是诊断 token 没归一，测试在完整 token/类别断言处红：[test_recap_scan_signals.py:3391](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3391)。
- `survivor-29` 所指 item 会先在 `_visible_text("[[987654]]")` helper 断言失败：[test_recap_scan_signals.py:3812](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3812)，真实 CLI 场景到 3858 行才执行，因此 1/1 红不证明生产入口会漏放。

❌ **HIGH（变异证据完整性）** — `collected == failed == len(指名)` 对“实际传入的 pytest items”数学上是严格的，但“73 个指定门”没有独立冻结：

- 只有变体数 66 有常量：[recap_domain_negverify.py:1036](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:1036)。
- 73 只是从 `DESIGNATED` 动态求和后打印：[recap_domain_negverify.py:1160](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:1160)。
- 从多指名列表删掉一个门，`len` 会同步缩小，剩余门全死仍可成功；单个列表的重复 nodeid 也未预检。
- `run_suite` 从整段 stdout 汇总 `N failed/passed`，没有核对实际失败 nodeid 集：[recap_domain_negverify.py:896](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:896)。
- `collect-only` 的 return code 未检查：[recap_domain_negverify.py:1102](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:1102)。

✅ **SIGTERM/SIGINT 主路径修复成立（静态）** — handler 在取锁前安装，变异写入位于内层 `try/finally`，锁在外层 `finally` 清理：[recap_domain_negverify.py:1123](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:1123)、[recap_domain_negverify.py:1194](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:1194)。

⚠️ 仍有窄窗口：`LOCK.mkdir()` 成功后、进入外层 `try` 前收到信号会留下锁；还原过程中再收到第二个信号也可中断 `write_bytes`。根治仍是隔离副本运行，而非原地写生产文件。

### 剩余工作分类

一次改动内可闭合：

- 原始报告全局禁用 `%%`，与 HTML 注释同口径，并加真实 CLI 门。
- 为分隔符增加“非法/重复/混合 run fail-closed”，补池内合法千分位正例及完整诊断断言。
- 冻结 `DESIGNATED_NODE_COUNT_EXPECTED = 73`，检查每列表唯一性、`collect-only` rc，并核对实际失败 nodeid。
- 把 s14、s29 拆成只含一个目标场景的生产 CLI nodeid。
- 修 r27：去掉 style 用例的尾随 closer；补双空格/tab、`Ghost/999` 派生、围栏内真实台账形状行。
- 使用现有 `tips_open`、`derived_children_count` 绑定台账数字；同步删除“无字段可绑”的错误说明。
- 为种子非模板行、`_tail_conflict` 分支及③段四个 label 补直接行为/变异门。

需要重做设计：

- A1：从源码行改为 Obsidian 渲染段落/AST；一并处理软换行、comments、highlight、math、脚注和列表 continuation。
- 数字提取改为“捕获完整 count-shaped 候选 → 分类合法整数/分组/小数/非法”，避免任何未知字符让尾片重新起锚。
- 从全局数值碰撞池改成按报告字段、节点角色、来源字段的语义绑定。
- 台账改成明确的 H2/H3 层级和允许角色模型，不能再用 `_h3_wellformed` 猜“坏标题”。
- 变异验证在隔离副本/worktree 上跑；Python `finally` 不应是生产文件恢复的唯一边界。

### 实际验证

✅ `git rev-parse HEAD`

`c35f38760d953fe7a25b9b26c5c0cb5ad43e90bf`

✅ 指定 pytest 最终结果

`279 passed, 14 warnings in 46.07s`

首次在只读沙箱中于收集前因 Python 找不到可用临时目录而失败；随后以完全相同的命令取得上述结果，没有运行其他 pytest 范围。

验证限制：

- 没有执行 `recap_domain_negverify.py`，所以未独立证明 66/66、运行前后逐字节一致或信号负控。
- 没跑 611 扩大回归。
- 没有构造探针/临时文件，没有读取 fixtures 的 `.md/.json` 正文。
- 没有运行 `git diff/show/log -p`；因此无法独立证明两个 commit 的历史改动范围，只能审当前源码及用户给出的旧/新描述。
- 没有实际启动 Obsidian；`%%` 路径属于静态源码路径审计。
- 未发现字面恒真断言；发现的目标无关假绿/措辞过宽集中在 r27、r29、s14、s29，已逐项列出。


