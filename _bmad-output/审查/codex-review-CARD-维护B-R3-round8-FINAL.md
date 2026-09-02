BLOCKER/HIGH 清零：否（就计数取值口径而言）

终裁：**0 BLOCKER / 9 HIGH（6 实现 + 3 自证，按根因合并）**。两条车道驳回只对原反例成立，不能推出机制闭合。

### 实现侧

1. ❌ **HIGH — inline-code 量词副本仍分叉。** 主表已含 `例束艘架间`，但 inline-code 正则仍手抄旧表并止于 `章`，且在 `_visible_text` 前挖空。[recap_scan.py:1405](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1405) [recap_scan.py:1428](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1428) [recap_scan.py:1770](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1770)

   原 `笔`+`支出` 的确会被后继 `支` 偶然重新锚定，故“该反例不可复现”✅成立；但类似 `本板共有987654 \`例\`记录` 会把 `例` 挖空，机制仍可静态到达。

2. ❌ **HIGH — ⑦/⑧继续手抄旧数词禁集。** 两式没有复用 `_NUMERAL_LIKE_CHARS`，缺 `仨/俩/带圈数字/苏州码` 等；m7 又只绑定前置 ASCII N。[recap_scan.py:1311](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1311) [recap_scan.py:1548](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1548) [recap_scan.py:2095](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2095)

   追加在标准信号行后的“共仨个”确会被信号整行门拦下，[recap_scan.py:1205](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1205) 因而原反例驳回✅成立；但普通允许式行如“派生角色成员缺来源锚点另有仨个。”仍能匹配⑦、避开 m7 值绑定和 D2 claim 门。

3. ❌ **HIGH — `_visible_text` 并未成为所有计数绑定的统一入口。** 当前是四个调用表达式、三个逻辑路径：D2 `:1779`、fallback 局部 `:2127/:2154`、全文门 `:2314`。缺口不止一个：

   - ⑦前置 N 仍匹配 raw `ln`；格式化 N 可被可见化后的全文白名单接受，却跳过值绑定。[recap_scan.py:2095](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2095) [recap_scan.py:2314](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2314)
   - manifest 种子 ledger 不匹配 raw 行就 `continue`；fallback 才另有形状兜底。[recap_scan.py:1926](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1926) [recap_scan.py:2271](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2271)
   - 五元组及 tips 的“全文逐条”也只枚举 raw 匹配；保留一条真行再追加渲染同形、源码被标记切断的假行，不进入唯一性/值核对。[recap_scan.py:2000](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2000) [recap_scan.py:2045](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2045)

4. ❌ **HIGH（已知未修）— reference-style Markdown link。** 仅支持 inline link `[x](url)`；`[x][ref]` 仍能切断 claim 或数串。[recap_scan.py:1609](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1609)

5. ❌ **HIGH（已知未修）— 过度拼接不保值。** `_join_free` 与 `_visible_text` 会删除渲染可见的反斜杠、未配对 `*`/`_`、空白和修饰字，故 `1\*5` 可按 15、`5多个`可按精确 5 入池。[recap_scan.py:1356](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1356) [recap_scan.py:1374](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1374)

   `_join_free` 文档已诚实承认；但 `_visible_text` 附近仍称“安全向、不构成虚构通道”，与现状矛盾。[recap_scan.py:1380](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1380) [recap_scan.py:1620](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1620)

6. ❌ **HIGH（存量已登记）— 闭表之外仍可能尾片重锚。** 例如传统 `點`、科学记数 `9e5个` 或未登记 Unicode 数字，都可能使前片退出定界，只按紧邻量词的尾片查池。[recap_scan.py:1548](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1548) [recap_scan.py:1587](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1587)

### 三张闭表与不变式

- ✅ `_CJK_NUM` 的窄赋值正确：实际是 **12 个可赋值字符**；所谓“17 字”是 `_CJK_NUM_CHARS` 的 12 数字字加 5 单位字，后五个不赋值。[recap_scan.py:1502](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1502)
- ⚠️ `_NUMERAL_LIKE_CHARS` 的“只定界不赋值”准确，①–⑳也全部存在；但 `〡-〺` 写宽了。实际是 **`〡–〩` 加 `〸–〺`**，不是连续区间。[recap_scan.py:1548](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1548)
- ⚠️ `_D2_QUANT` 确实含 `例束艘架间`，但仍是遗漏即零校验的 fail-open 闭表；本轮测试只承重 `例`，没有全等契约或 `束/艘/架/间` 行为门。[test_recap_scan_signals.py:4267](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4267)
- ❌ 若 §五之三只登记“三张表”，仍属低估：inline-code 量词副本与⑦/⑧数词禁集是另外两张活跃闭表。

“定界要宽、赋值要窄”在两个主消费循环内部✅成立：D2 与 fallback 都是宽模式 → `_join_free` → `_count_token_value`，`None`/池外即报错。[recap_scan.py:1871](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1871) [recap_scan.py:2171](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2171)

端到端只能判⚠️ PARTIAL：前置挖空、raw 专用绑定和闭表遗漏会让 token 根本到不了这两个循环。

### 自证侧

7. ❌ **HIGH — negverify 至少有一个确定的异常伪红。** survivor-20 把千分位 pattern 改成无捕获组 lookaround，却保留生产代码 replacement `r"\1"`，调用即产生 `re.error: invalid group reference`；脚本把任意 pytest failure 都记作“承重”。[recap_domain_negverify.py:272](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:272) [recap_scan.py:1668](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1668) [recap_domain_negverify.py:537](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:537)

8. ❌ **HIGH — `37/37` 不证明 23 项逐项生产承重。** survivor-15…37 静态分类：

   - ✅ 生产性质充分：`15,16,18,21,22,23,31,33,35`
   - ⚠️ 单侧、组合、措辞过宽或仅部分分支：`17,19,24,27,28,32,37`
   - ⚠️ 所选大测试先死于 helper，后续 CLI 根本不执行：`25,26,29,30,34,36`
   - ❌ 异常崩溃伪红：`20`

   特别是 survivor-37 只删除 D2 的中文“负”，fallback 那份仍活；survivor-36 先死于成员集合 helper，不能证明 CLI 行为。[recap_domain_negverify.py:439](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:439)

9. ❌ **HIGH — 新门仍有比证据宽的措辞。**

   - 中文“负”只测 D2；fallback 仅测西文 `-5`，两份守卫又不是共享常量。[test_recap_scan_signals.py:4181](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4181) [test_recap_scan_signals.py:4274](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4274)
   - `例束艘架间` 只测 `例`。
   - round-11 的三条输入位于一个普通 `for` 循环和一个 pytest item 内；可称“逐输入断言”，不能称“三个独立 pytest 项”。[test_recap_scan_signals.py:4220](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4220)
   - “此后所有判据在同一文本空间”及“全文所有五元组逐条校验”均被 raw 专用绑定反证。[recap_scan.py:1602](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1602) [recap_scan.py:1995](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1995)

同时确认以下门不是空洞：判据期望值独立写死、两个合成池都钉死为 `{0,1,2}`、`_one_problem_has` 确实要求类别与完整 token 同处一条诊断。[test_recap_scan_signals.py:3340](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3340) [test_recap_scan_signals.py:3406](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3406) [test_recap_scan_signals.py:3608](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3608) [test_recap_scan_signals.py:3654](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3654)

### 实际执行

- pytest：`261 passed, 14 warnings in 40.44s`
- `git rev-parse HEAD`：`efcc92499bfa37c36ed797416e3d81ef088095be`
- 首次沙箱启动在收集前因无可用临时目录失败；同一命令获准重试后得到上述结果。因计数正好 261，未运行 `git status`。
- 未运行 negverify；未读取 fixtures 正文；未运行禁用的 Git 命令；未构造或执行探针。
- 第 8 轮超限事实保留。本报告仅给技术审计结论，不把超限审查自动等同于卡文治理完成。


