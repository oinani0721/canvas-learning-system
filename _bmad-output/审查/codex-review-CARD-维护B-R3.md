BLOCKER/HIGH 清零：否

总判定：**FAIL，四组窄修在已覆盖形态上有效，但并未完整闭合“Obsidian 所见数字＝校验器所读数字”。**

## 四组改动

1. ❌ **HIGH（本轮未闭合）— 区间首端修复仅部分正确。**

   - ✅ `-2~3`、`2.2~3` 会由左邻守卫捕获，诊断保留 `_pre + 完整区间`，且在规模句式门后才报错，没有形成死分支：[recap_scan.py:1907](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1907)、[recap_scan.py:1923](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1923)、[test_recap_scan_signals.py:4340](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4340)。
   - ❌ 守卫只认负号或“数词＋小数点”，漏掉无整数部分的 `.2~3`、`．二~三`、`点二~三`：[recap_scan.py:1708](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1708)。区间会从 `2~3` 重锚并被挖空，后续小数门已看不到：[recap_scan.py:1938](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1938)、[recap_scan.py:1966](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1966)。既有测试已经把 `.5`、`．五` 定义为必须拒绝的小数，但 R14 未覆盖其区间组合：[test_recap_scan_signals.py:3723](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3723)。

2. ❌ **HIGH（本轮未闭合）— 行内代码的“先归一再判”方向正确，但字符域再次分叉。**

   - ✅ `_codespan_is_visible_count()` 先走 `_visible_text` 和千分位归一，可见计数只保留内文；列举的负数、小数、千分位、全角数字路径正确：[recap_scan.py:1518](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1518)、[recap_scan.py:1536](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1536)。
   - ❌ `_D2_COUNTISH_EXTRA` 不含区间主表支持的 `~／～／〜／到／至／—／–`。因此行内代码里的可见区间会被当字段值整段挖空，区间与普通数字门均不可达：[recap_scan.py:1514](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1514)、[recap_scan.py:1639](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1639)、[recap_scan.py:1867](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1867)。
   - ❌ 主连接集接受 `\s`，code-span 表却只列普通空格和 tab；内部 NBSP 等可见空白同样会使整段被豁免：[recap_scan.py:1423](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1423)、[recap_scan.py:1515](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1515)。
   - ⚠️ 注释称“反引号不在连接字符集”，但连接集明确包含反引号；删除反引号的输出断言不是恒真，却没有证明注释声称的必要性：[recap_scan.py:1421](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1421)、[recap_scan.py:1539](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1539)。

3. ❌ **HIGH（PARTIAL）— 两处行级窄修正确，但段级仍有 raw/visible 夹缝。**

   - ✅ ③段信号行现在先 `_visible_text` 再选行，并用同一个归一行做整行匹配：[recap_scan.py:1124](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1124)、[recap_scan.py:1216](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1216)。
   - ✅ fallback ⑦的白名单和 N 绑定现在都匹配 `_visible_text(ln)`：[recap_scan.py:2213](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2213)、[recap_scan.py:2438](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2438)。
   - ❌ 但③段本身仍由 raw `^### ③` 选取；保留一个正常③段后，另一个渲染等价但源码标题不命中的③段可逃出逐行绑定：[recap_scan.py:1113](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1113)、[recap_scan.py:2393](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2393)。
   - ❌ “无来源结论只许在③段”的段抽取和子串判断也仍是 raw 文本：[recap_scan.py:2200](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2200)。

4. ❌ **HIGH（本轮引入/未闭合）— 崩溃识别二分不成立。**

   - ✅ `_crash_text` 的确合并了**外层 pytest** 的 stdout/stderr：[recap_domain_negverify.py:560](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:560)、[recap_domain_negverify.py:619](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:619)。
   - ❌ 内层 `recap_scan.py` 是由 `run_verify()` 以 `capture_output=True` 执行；很多失败断言只携带 `r.stdout`，内层 traceback 若只在 `r.stderr`，不会可靠进入外层两路输出：[test_recap_scan_signals.py:104](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:104)、[test_recap_scan_signals.py:4348](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4348)。因此真实生产崩溃仍可能被记成正常红。
   - ❌ 实现用的是 `^E\s+IDENT:`，根本没有区分三个空格与更深续行缩进：[recap_domain_negverify.py:589](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:589)。`E       Expected: ...` 会假阳；无消息异常 `E   ValueError` 会因没有冒号而假阴；生产代码抛出的 `AssertionError` 也会与测试断言混同。
   - ⚠️ stderr 行为门只是把合成 traceback 手工传给 helper，没有验证 `run_suite → 外层 pytest → 内层 CLI stderr` 的真实接线：[test_recap_scan_signals.py:4294](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4294)。

## 三处“不改”判断

❌ **HIGH — 该决定不成立。**

- **台账种子行**：raw 子标题定位、raw 行匹配失败都会静默跳过绑定：[recap_scan.py:2029](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2029)、[recap_scan.py:2047](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2047)。后续形状白名单仅在 fallback，且同样依赖 raw `### 种子`；manifest 没有该兜底，[recap_scan.py:2400](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2400)。`### 种子` 也不在必需段落表中：[recap_scan.py:825](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:825)。

- **五元组**：唯一性和值比较仍是 raw `findall`：[recap_scan.py:2118](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2118)。保留一条 raw 正确五元组后，额外的渲染等价冲突行可不计入命中。fallback 的 visible 白名单只验证形状，不绑定五个字段：[recap_scan.py:1343](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1343)。

- **tips**：段内 `in_sec` 和全文 `all_hits` 都基于 raw 文本：[recap_scan.py:2163](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2163)。一条 raw 正确行满足存在性后，额外的渲染等价冲突行可被忽略；后续没有 AI 侧对账逐行白名单。

仅在“唯一原始标准行直接变得不匹配”这个窄场景下，五元组/tips 缺行检查或 fallback 种子白名单会 fail-closed；这不能推出整个输入空间安全。并且实际调用顺序是先 `_verify_numbers`、后 fallback 模板检查，不是所称“更靠前模板门”：[recap_scan.py:2362](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2362)。

## 行为门与变异脚本

- ✅ 新增 R14–R16 未见字面恒真断言；都有基线、注入命中检查并走真实 `run_verify()`。
- ⚠️ R14 的 `-5` 只要求某条诊断含 `"5"`，未绑定“负数形态”类别，弱于其“完整数串/责任防线”措辞：[test_recap_scan_signals.py:4338](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4338)。
- ⚠️ R16 没有“格式化后的正确 N 必须通过”正例，因而“所有前置 N 一律拒绝”也能满足新增断言：[test_recap_scan_signals.py:4442](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4442)。
- ⚠️ R16 所称“段外”两例实际插在 `方向叙述` 前，该锚仍位于③段内：[test_recap_scan_signals.py:724](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:724)、[test_recap_scan_signals.py:4433](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4433)。
- ⚠️ 变异 43、45、46 的替换确实禁掉对应防线；但变异 44 名称称“退回 raw 判据”，实际删除整个可见计数分支、使所有 code span 都被挖空，不能单独证明归一顺序承重：[recap_domain_negverify.py:520](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:520)、[recap_domain_negverify.py:533](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:533)。
- ⚠️ replacement runner 只检查 `old in text` 并替换首次命中，不要求恰好一次；当前锚可命中，但未来重复锚会使证据失真：[recap_domain_negverify.py:671](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:671)。

## 剩余问题分类

**一次改动内可闭合：**

- 补无整数部分的小数区间首端。
- 让 code-span 判据直接复用区间分隔符和完整空白语法，而非再维护字符副本。
- 将 seed/五元组/tips、③段及“段外无来源结论”的选择与绑定统一到同一归一行流。
- 补 manifest seed、渲染等价重复行、真正段外、正确 N 放行、真实内层 stderr 接线门。
- 让 replacement 必须唯一命中，并把变异 44 改成真正的 raw-vs-normalized 变异。

**需要重做设计：**

- ❌ **HIGH（存量）** `_visible_text` 自己承认不是完整 renderer；`_join_free` 还会删除渲染后可见的未配对符号，源码已记录 `1\*5` 可被按 15 查池并放行：[recap_scan.py:1444](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1444)、[recap_scan.py:1661](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1661)。若目标是严格等同 Obsidian 所见，应使用 Markdown/Obsidian 解析语义，或禁止受保护模板行出现排版语法。
- ❌ **HIGH（存量）** 变异脚本仍原地改活源码；恢复 `finally` 无法覆盖 SIGKILL/掉电，且首次 `write_text` 位于内层恢复块之前：[recap_domain_negverify.py:680](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:680)。正常结束后的 hash 相同不能证明崩溃恢复，应改为隔离副本/隔离 worktree。
- 用结构化 pytest 结果和显式内层 crash 通道替代解析人类可读的 `E ...` 文本。

## 实际运行

- `git rev-parse HEAD`：`7bf7dfcf831cc4622fe32830dd9fb1b59f7195cc`，与预期一致。
- 指定 pytest：**266 passed, 14 warnings in 42.57s**。
- 第一次在只读沙箱内于测试收集前因 pytest 无可用临时目录失败；随后以完全相同命令、仅放开临时文件创建权限重跑成功。该第一次失败是执行环境问题，不是代码测试失败。

## 验证限制

未运行 `recap_domain_negverify.py`，因此 `46/46`、运行前后逐字节一致均只是车道自报；未重跑 598 项扩大回归。未构造探针或临时输入，以上绕过均为代码路径推理。未手工读取 fixtures 正文，未运行 `git diff`、`git show` 或 `git log -p`；指定 pytest 自身可能按其既有用例读取 fixtures。


