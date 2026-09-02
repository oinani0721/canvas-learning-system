BLOCKER/HIGH 清零：否

未发现新的 BLOCKER，但仍有多项 HIGH：③标题、seed、tips 的 raw/visible 夹缝尚未闭合，崩溃识别也不是可靠二分。

### 本轮改动

- ✅ [recap_scan.py:1124](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1124)、[recap_scan.py:2145](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2145)、[recap_scan.py:2241](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2241)：③段信号“选行”、五元组、fallback ⑦前置 N 都已改到 `_visible_text()` 空间；原本各自的双行/raw 绑定漏洞确实被修复，分支可达。

- ⚠️ 本轮引入 MEDIUM — [recap_scan.py:1721](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1721)–1729、1940–1943：区间首端整数部改可选，正确拦住了无整数部分小数；但裸 `点/. /．` 后允许 `_D2_JOIN_ONE*`，其中含空白。普通词尾“点”或句号后再写合法范围，也会被当成小数前缀。r17 只有三个恶意例和无前缀范围正控，[test_recap_scan_signals.py:4521](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4521)–4537，没有锁这个合法反控。

- ⚠️ MEDIUM — [recap_scan.py:1521](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1521)、1652–1655：`str.isspace()` 修改正确，当前 `_D2_RANGE_SEPS` 的值也与主表一致；但并非真正“同源”，主区间正则仍独立手写分隔符。r17 只测 `~～〜到至`，[test_recap_scan_signals.py:4551](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4551)–4558，漏测横线族，无法做到“漂移即被抓”。

- ✅/⚠️ [recap_scan.py:1546](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1546)–1559：主实现已正确改写反引号理由。但测试注释 [test_recap_scan_signals.py:4171](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4171) 仍错误声称“反引号不在连接集”。

- ✅ [test_recap_scan_signals.py:104](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:104)–126、[recap_domain_negverify.py:673](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:673)–699：`run_verify` 当前确实调用 `_surface_child_stderr`，`run_suite` 也确实合并外层 stdout/stderr。接线实现本身正确。

- ❌ HIGH — [recap_domain_negverify.py:607](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:607)–649：`缩进上界 + assert/AssertionError 白名单` 不是可靠二分。

  - 预期 oracle 断言、fixture/前置条件断言、生产代码抛出的 `AssertionError` 都被当成同一种“正常变红”。
  - 内层 CLI 的无 traceback `SyntaxError`、无消息 `SystemExit`、致命信号等，可能只留下外层白名单内的 `AssertionError`，形成假阴。
  - 输出正文偶然含 `Traceback...` 或 `N error(s)` 会形成假阳。
  - 实测依据据称是恰好 3 格，但实现接受 1–3 格，1/2 格没有门证据。当前环境是 pytest 9.0.2，且实际由 [pytest.ini:19](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/pytest.ini:19)–21 强制 `--tb=short`，不是测试注释所称的“-q 默认 tb”。它最多是当前 formatter 的启发式。

### “未改三处”的代码路径结论

- ❌ HIGH，存量 — [recap_scan.py:1113](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1113)–1131、2226–2234、2419–2425：③标题仍按 raw `^### ③` 选段。你加入完整第二段时被拦，能由段外 raw `"无来源结论"` 特判解释；这只是偶然兜底。其他三种信号，或同样被排版切开的该 label，没有这层保证。窄实验成立，安全结论不成立。

- ❌ HIGH，存量 — [recap_scan.py:2046](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2046)–2066、2426–2457：seed 段和行仍按 raw 匹配，未命中行静默 `continue`。fallback 同一 raw 段内通常会被形状门拒绝，解释了你的未复现；但 manifest 没有这层形状门，渲染等价但 raw 不命中的第二个 seed 标题也会把整段置于两道检查之外。

- ❌ HIGH，存量 — [recap_scan.py:2189](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2189)–2204：tips 两式仍在 raw 文本上做存在性、唯一性和值绑定。保留正确行即可满足门；新增渲染等价但 raw 不命中的冲突行不会进入 `all_hits`。D2 又只处理明确全板规模句，[recap_scan.py:1966](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1966)–1969，不兜 tips。

### 行为门与变异证据

- ❌ HIGH，恒真断言 — [test_recap_scan_signals.py:4611](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4611)–4612：测试读取自身源码并查找字符串 `_surface_child_stderr(r)`，而这个字符串就存在于该断言自身。删除真正调用点第 126 行后仍会通过。r19 第 4637–4650 行只证明 helper 会打印，不证明 caller 接线。

- ⚠️ MEDIUM，措辞过宽 — [test_recap_scan_signals.py:4456](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4456)–4478 所称“段外伪信号”，实际注入到 `方向叙述：` 前；该锚仍位于③段内，所以门没有验证真正段外路径。

- ⚠️ LOW — [test_recap_scan_signals.py:4572](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4572) 仍写“缩进 + 冒号”，与已删除冒号条件的实现矛盾；[recap_domain_negverify.py:652](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:652) 声明四元组，实际第 700 行返回五元组。

- ⚠️ 变异源码静态核对：新增 #47、#49、#50 确实修改活防线；#48 只移除部分分隔符，因为 `_D2_COUNTISH_EXTRA` 自带部分横线字符，[recap_domain_negverify.py:568](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:568)–580，名称比实际范围宽。存量 #4、#40、#44 的名称也分别夸大了“恢复黑名单”、ASCII code span 影响面和“退回 raw 判据”。

### 一次改动内可闭合

- ⚠️ 统一生成一份 code-block-aware 的 visible 行/标题表示，让③标题、seed 标题/行、tips 两式和段外检查共同消费；同时补 fallback/manifest 的“保留正确行 + 增加冲突行”门。
- ⚠️ 让 `_D2_RANGE_RE` 从 `_D2_RANGE_SEPS` 机械生成；收窄无整数小数守卫，并补词尾“点”与句号的合法正控。
- ⚠️ fallback 标题/关系行在 `_NUM_RUN_RE` 前没有执行区间终核，[recap_scan.py:2265](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2265)–2339；`~` 会被当连接符删除并按拼接整数查池。可复用 D2 区间处理闭合。
- ⚠️ 对 fallback 的 `signals`/子对象先做类型守卫；当前非空非 dict 可能在 [recap_scan.py:2238](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2238) 后 `.get` 崩溃，而现有门只喂空列表。
- ⚠️ 给超长 ASCII 数串的 `int(token)` 加长度界/`ValueError` 处理；合并会重复报告 ASCII 小数的两道小数检查。
- ⚠️ 用实际 caller 行为/AST 或 monkeypatch sentinel 替换第 4612 行自指源码断言，并修正文案、类型标注和变异名称。

### 需要重做设计

- ❌ HIGH，存量 — [recap_scan.py:1423](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1423)–1456、1674–1682、1734–1765：`_visible_text/_join_free` 明知会删除渲染后仍可见的未配对 `*`、`_`、反斜线语义及“多/约/近/超”等字，可能把读者所见表达拼成另一个恰好在池中的整数。行内代码又以单反引号正则解析，并把 code span 内的 HTML/强调按普通正文渲染；这不符合 Markdown/Obsidian 的 code-span 语义。要么使用真正的 Markdown/Obsidian AST/renderer，要么严格限制并拒绝未支持语法。

- ❌ HIGH，存量 — [recap_scan.py:1612](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1612)–1630：“出处”实际是全 JSON 数值池再加任意两值的一阶和/差，不是字段绑定；JSON 中不存在的数也能进入池。若目标真是“报告数字有出处”，应改成 claim 类型 → 具体字段/显式公式的 provenance 绑定。

- ❌ HIGH，存量 — 数词域仍是封闭字符表；明确规模句使用表外可见 Unicode 数字时，可能 `is_claim=True` 却提取不到任何 token，最终零错误。多字中文数词则一律拒绝，属于安全向误伤。需要统一数值词法或明确只允许阿拉伯数字并在 claim 级 fail-closed。

- ❌ HIGH，存量 — [recap_domain_negverify.py:731](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:731)–735 仍原地改生产源码；SIGKILL、断电、部分写入失败或协作者同时编辑，`finally` 都不能提供可靠恢复。应在隔离副本/worktree 运行，并用结构化 sentinel/JUnit/pytest hook 判断“恰好是哪条 oracle 失败”，不要解析终端文本。

### 实际验证

- ✅ `git rev-parse HEAD`：`6e50fd2286ffc6555af8bc54239b5db441e10a42`
- ✅ 指定命令：`269 passed, 14 warnings in 43.26s`，pytest 9.0.2 / Python 3.14.4。
- ⚠️ 首次在只读沙箱中因无可写临时目录而在收集前失败；获批后以完全相同命令重跑，以上才是有效结果。
- ⚠️ 未运行 `recap_domain_negverify.py`，未复核自报的 50/50 或 601 passed；未构造探针、未读 fixtures 的 `.md/.json` 正文，也未运行被禁止的 git 命令。缩进“顶层恰好 3 格”没有通过失败态实跑独立复现。


