BLOCKER/HIGH 清零：否

### 核心发现

- ❌ HIGH｜本轮引入：节点身份三段式不成立。[recap_scan.py:2070](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2070) 已先归一整个小节，[recap_scan.py:2103](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2103) 取得的 `node` 已不是 raw；因此 [recap_scan.py:2104](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2104) 所谓“raw 精确匹配”其实是“归一结果恰好等于某个 raw ID”。

  - ledger 同时有 `SeedA`、`Seed_A` 时，报告 raw `Seed_A` 会先变成 `SeedA`，直接错绑 `SeedA`，跳过撞车检查；错误批注数可能因此通过。
  - ledger 有 `Seed_A`、`Se_edA` 时，报告 raw `Seed_A` 又会被误判为归一撞车，合法精确身份被拒。
  - 当前门只测后一个“无 raw `SeedA` 候选”的撞车形态，[test_recap_scan_signals.py:4809](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4809)，漏掉会错绑的遮蔽碰撞。

- ❌ HIGH｜存量：“tips raw 绑定”观察成立。AI 对账段及两种 tips 计数均在 raw `text` 上搜索，[recap_scan.py:2218](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2218)、[recap_scan.py:2238](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2238)。保留一条正确标准行后，另一条渲染等价但 label 被 Markdown/HTML 切开的冲突行不会进入 `all_hits`；D2 又只检查全板规模句式，[recap_scan.py:1984](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1984)，不能兜底。

- ❌ HIGH｜存量：“③标题 raw 绑定”观察也成立。③段先按 raw 标题取段，[recap_scan.py:1113](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1113)，仅选中的段内行才走 `_visible_block`，[recap_scan.py:1131](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1131)。所以保留规范③段、再增加一个渲染等价但 raw 不以 `### ③` 开头的第二段时，第二段不会进入四信号全等检查。全文补门只专门处理 raw「无来源结论」，[recap_scan.py:2270](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2270)。

- ❌ HIGH｜存量：manifest seed 问题比“允许任意 tail”更宽。[recap_scan.py:1262](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1262) 的 `rest` 是无约束 `.*`；更严重的是不匹配模板的行直接 `continue`，[recap_scan.py:2100](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2100)。注释称形状由另一处报告，但该形状门只存在于 fallback 分支，[recap_scan.py:2471](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2471)。manifest 下可整行换措辞而完全跳过逐节点数字绑定。

- ❌ HIGH｜存量范围洞：D2 切 H2 段时把标题行本身丢掉；body 从 `h.end()` 开始，[recap_scan.py:1879](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1879)，后续只扫描 body。因此 H2 标题内的“本板共有 N 个……”不受 D2 检查；必需标题又允许任意全角括号补充，[recap_scan.py:1237](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1237)。

### 本轮改动与行为门

- ✅ 区间主实现正确：11 个当前分隔字符由 `_D2_RANGE_SEPS` 单源提供，code-span 引用它，[recap_scan.py:1521](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1521)，区间正则也机械生成，[recap_scan.py:1656](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1656)。

- ⚠️ 但“11/11 双向锁”门只算 PARTIAL。[test_recap_scan_signals.py:4569](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4569) 用 `len >= 11` 且期望集合来自常量自身，没有锁精确集合、唯一性或禁止扩表；删一字符再重复/加入另一字符仍可绿。

- ✅ 四个生产消费点当前确实使用 `_visible_block`：信号、seed 值绑定、五元组、fallback seed 形状门分别在 [recap_scan.py:1131](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1131)、[recap_scan.py:2070](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2070)、[recap_scan.py:2192](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2192)、[recap_scan.py:2491](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2491)。`seed_vis` 是局部变量，没有再次污染后续全文；m7 也已在 `_visible_text(ln)` 上匹配，[recap_scan.py:2294](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2294)。

- ❌ 但调用点计数门会假绿。[test_recap_scan_signals.py:4760](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4760) 当前数到 6 次：4 个真实调用、1 个定义、以及 [recap_scan.py:2487](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2487) 注释中的一次。删除任一真实调用仍满足 `>=5`；第二条断言也只禁止一种逐字内联写法。

- ✅ r19 已真正锁定同一个 `CompletedProcess`：monkeypatch 哨兵、调用次数及 `called[0] is returned` 都成立，[test_recap_scan_signals.py:4667](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4667)。

- ✅ r16 已正确收窄为“③段内伪信号行”，[test_recap_scan_signals.py:4485](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4485)。但其 docstring 仍称 seed raw 未修，[test_recap_scan_signals.py:4456](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4456)，已经过时；且没有“正确 N + 渲染标记仍 PASS”的反向门。

- ⚠️ 崩溃分类不是可靠二分，当前文案已如实承认这一点。[recap_domain_negverify.py:639](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:639) 的 1–3 格规则仍可能：

  - 把生产代码抛出的 `AssertionError` 当成正常判错；
  - 把有意 `pytest.fail()` 的 `Failed:` 当成崩溃；
  - 把 formatter 以 1–3 格输出的断言续行当异常；
  - 漏掉无 traceback 的子进程异常或致命信号。

  此外 emitter 与 classifier 各手抄一份 `[[CHILD-CRASH]]`，[test_recap_scan_signals.py:104](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:104)、[recap_domain_negverify.py:672](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:672)，现有门没有把真实 emitter 输出再喂给 classifier；单侧漂移可双门都绿。

- ✅ 把变异写入纳入 `try/finally` 是正确修复，[recap_domain_negverify.py:779](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:779)。但兜底不到的不只 SIGKILL/断电，还包括默认 SIGTERM/SIGHUP，以及还原写本身失败。

- ⚠️ 静态检查未发现当前 52 条里明显的“不命中”或等价空变异，但归因仍有过宽：

  - survivor-48 将共享 `_D2_RANGE_SEPS` 置空，同时破坏 code-span 和主区间正则，不能证明单一消费方承重，[recap_domain_negverify.py:568](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:568)。
  - survivor-44 不是“退回 raw 判据”，而是删除整个可见计数分支，[recap_domain_negverify.py:533](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:533)。
  - survivor-27 同时删除中文数词和冒号容忍，名称比实际变异窄，[recap_domain_negverify.py:367](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:367)。
  - replacement 仅检查“至少命中”并替换第一次，不证明锚点唯一，[recap_domain_negverify.py:770](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:770)。

### 剩余问题分类

一次改动内可闭合：

- seed 同时保留 raw/visible 行，先用 raw 捕获值精确绑定；不中才查 visible index，并补“exact 候选遮蔽 collision”门。
- tips 与③标题统一到 visible 选行/选段。
- 将 H2 标题行纳入 D2。
- manifest 非模板行直接 fail-closed。
- 用 AST 锁四个实际 `_visible_block` 调用点；精确锁 11 个不同分隔符。
- 打通 crash marker emitter→classifier 的端到端门，拆开 survivor-48。
- 共用③段边界；当前 [recap_scan.py:2464](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2464) 不在下一个 H2 停，会把后续段落的“你选择/你决定”误算进③段。
- 修 scan 根对象及 truthy 非 dict `signals` 的类型守卫；当前 fallback 后续仍可能 `.get()` 崩溃，[recap_scan.py:2283](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2283)。

需要重做设计：

- `_visible_text` 不是 Obsidian renderer，且已知会把读者可见的 `1*5`、`5多` 错绑成另一整数，[recap_scan.py:1444](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1444)。需真实渲染语义，或封闭、严格的报告语法。
- 节点身份应使用 canonical ID，不能从有损显示文本反推。
- manifest tail 若必须保留，需要先定义封闭字段语法。
- `_derived_number_pool` 会加入任意一阶和/差，[recap_scan.py:1612](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1612)。按本次“JSON 中找到同值来源”的定义，这会生成 JSON 中根本不存在的值；即使允许算术，全局无类型池也不能证明“子节点 N”绑定到正确字段。应改为 claim 类型→具体 scan 字段。
- 可靠崩溃分类与变异崩溃恢复分别需要结构化 pytest 结果/子进程协议，以及在隔离副本上变异，而不是继续解析输出和原地改生产文件。

### 实际验证

- `git rev-parse HEAD`：`514d5bfa2ef0a1a091128160c33d52b56ef41c4e`
- 指定 pytest：`271 passed, 14 warnings in 44.77s`
- 第一次在只读沙箱内于收集前因无可用临时目录失败；同一命令获准重跑后通过，代码测试结果以上述成功运行计。

验证限制：未运行 `recap_domain_negverify.py`，未重跑自报的 52/52 或 603 passed；未构造探针/临时文件，未读 fixtures 正文，未运行 `git diff`、`git show` 或 `git log -p`。tips、③标题、身份碰撞等结论来自静态代码路径推演，未声称动态复现。


