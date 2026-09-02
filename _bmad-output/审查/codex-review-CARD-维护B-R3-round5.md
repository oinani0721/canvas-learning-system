BLOCKER/HIGH 清零：否（就计数取值口径而言）

本轮确认：**0 BLOCKER / 10 HIGH 类**，其中 8 条实现路径、2 条自证缺口。

## 实现侧：8 HIGH

1. ❌ **HIGH — inline-code 挖空仍隐藏渲染可见计数。**  
   `_D2_INLINE_CODE_RE` 只保护紧贴反引号的 ASCII 纯数字和旧 32 字量词表；反引号内的中文数词、全角数字、新增量词 `层…维` 会先被挖空。例如渲染可见的 ``本板共有987654 `层`关系`` 会失去量词锚点。[recap_scan.py:1397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1397) [recap_scan.py:1424](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1424) [recap_scan.py:1683](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1683)

2. ❌ **HIGH — 裸规模句式门仍会失锚。**  
   裸 `共有/总计/合计` 只接受源码中的 `空白 + ASCII 数字`。`总计五个子节点`、`总计：987654个`、`总计**987654**个` 渲染后都是明确自陈，但 `is_claim=False`，直接在取数循环前 `continue`。[recap_scan.py:1405](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1405) [recap_scan.py:1723](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1723) [recap_scan.py:1751](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1751)

3. ❌ **HIGH — HTML 解实体晚于全角数字转换。**  
   两消费点均先 `.translate(_FULLWIDTH_DIGITS)`，随后 `_normalize_number_seps()` 才执行 `html.unescape()`。实体 `&#xff19;` 因而在转换后才成为 `９`，不会再转成 ASCII，也不在定界集内；D2/fallback 都可零校验。[recap_scan.py:1569](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1569) [recap_scan.py:1690](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1690) [recap_scan.py:2048](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2048)

4. ❌ **HIGH — 千分位只跨逗号两侧，后三位内部仍不可跨连接字符。**  
   前瞻硬要求紧邻 `[0-9]{3}`。`987654,0<b>0</b>0个` 渲染为 `987654,000个`，但归一失败；D2 只会把尾部 `000` 按 0 入池，fallback 则拆成多个小值碰池。[recap_scan.py:1584](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1584) [recap_scan.py:1784](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1784) [recap_scan.py:2055](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2055)

5. ❌ **HIGH — range 仍有两条 fail-open。**  
   分隔表缺常见 `～/〜/−/‑`，故 `987654～0个` 只核右端 0；此外 range 先于 decimal 且无左边界，`987654.0-0个` 可从小数尾部匹配并挖空 `0-0`，随后小数门已看不到原值。[recap_scan.py:1547](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1547) [recap_scan.py:1726](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1726) [recap_scan.py:1759](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1759)

6. ❌ **HIGH — 有符号整数按无符号幅值入池。**  
   符号不属于 `_NUM_RUN_PAT`；`本板共有-5个` 在两个消费点均按 `+5` 比对。池含 5 时，进池值明确不等于读者所见值。[recap_scan.py:1541](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1541) [recap_scan.py:1593](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1593)

7. ❌ **HIGH（存量已登记但低估）— 两张定界闭表仍能造成零校验。**  
   `_NUMERAL_LIKE_CHARS` 漏自然用法如 `俩人`；`_D2_QUANT` 漏 `门/套/对/场/部` 等常用量词，例如 `本板共有987654门课程`。这与此前 `兆` 尾片重锚、`层` 整句免检是同机制，不应归为 MEDIUM/LOW。[recap_scan.py:1397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1397) [recap_scan.py:1537](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1537) [UAT:521](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/_bmad-output/验收单/UAT-CARD-维护B-R3-中文数词终态-2026-09-02.md:521) [UAT:549](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/_bmad-output/验收单/UAT-CARD-维护B-R3-中文数词终态-2026-09-02.md:549)

8. ❌ **HIGH — Markdown/HTML 渲染包装仍可让可见数字消失或尾片重锚。**  
   无别名 wikilink 的目标本身就是显示文本，但 `_D2_WIKILINK_RE` 会挖掉 `[[987654]]` 的数字；超过 20 字符的合法 HTML 开标签也不属于连接字符，渲染时消失、扫描时却切断数串。验收单所举“长 HTML 注释”反而已被全局门拒绝，真正未闭合的是普通长标签和无别名链接。[recap_scan.py:1356](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1356) [recap_scan.py:1427](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1427) [recap_scan.py:2106](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2106)

## 三表与不变式

- ✅ `_CJK_NUM`：12 个单字赋值表本身诚实、取值正确；完整 token 真正到达 `_count_token_value` 时，赋值确实够窄。
- ⚠️ `_NUMERAL_LIKE_CHARS`：承认“封闭表”是诚实的，但把漏表后果定为 MEDIUM 明显低估。
- ❌ `_D2_QUANT`：当前字符串确为 42 字，但不是单一来源；inline-code 守卫仍藏着旧 32 字副本。
- ❌ “定界宽、赋值窄”：在 D2 普通循环、range 端点、fallback 的**局部调用图**成立；端到端为 FAIL，因为上述句式门、结构挖空、实体顺序、符号和分隔符均能在判值器之前让 token 消失或碎裂。

因此，验收单对“表是封闭的”有登记，但对严重性、隐藏副本及真实渲染残余登记不完整。

## 新门与 survivor 自证

9. ❌ **HIGH — 新测试仍有空洞/过宽断言。**

   - 没有 `_D2_QUANT` 的 exact-set 或长度断言；只测了新增十字中的 `层`，其余九字可漂移。[test_recap_scan_signals.py:3331](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3331) [test_recap_scan_signals.py:3933](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3933)
   - “双端均坏、逐个报”仍未被证明：`_one_problem_has` 只查同一 stdout 行，而每条区间诊断末尾附带整条原句；即使只报一个端点，该行上下文仍同时包含两个 token，两次断言都会通过。[recap_scan.py:1753](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1753) [test_recap_scan_signals.py:3640](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3640) [test_recap_scan_signals.py:3898](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3898)
   - r8 声称覆盖“混写区间端点”，但输入矩阵没有混写端点；r6 声称两个消费点走同一规则，但 fallback 没有跨类混写格。[test_recap_scan_signals.py:3860](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3860) [test_recap_scan_signals.py:3889](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3889)

10. ❌ **HIGH — 24/24 红不能推出七项整改逐项承重。**  
    未发现 survivor-15…24 中“整条什么都没禁”的空变异；重写后的 survivor-18 是实质变异。但逐项结论为：

   - ✅ S15、S17、S18、S21、S22：非空且对其窄目标有效。
   - ⚠️ S16：会先被旧有 `廿五` 用例打红，不能独证新补的 `兆京垓秭穰`。
   - ❌ S19、S20：仍是组合变异；测试在第一个失败断言处终止，后一个替换组件没有被观察。
   - ❌ S23：同时改 D2/fallback，但 r8 只有 D2 左缺小数，fallback 替换未参与红色。
   - ⚠️ S24：只证明端点判值器；没有退窄 `_D2_RANGE_RE`，也没有改 `_D2_QUANT`，不能证明“共用数串式/连接字符/非个量词”承重。

   证据见 [negverify.py:197](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:197)、[negverify.py:228](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:228)、[negverify.py:252](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:252)、[negverify.py:281](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:281)、[negverify.py:296](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:296)、[negverify.py:310](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:310)。

## 实际执行与限制

- 指定 pytest 有效执行结果：**258 passed, 14 warnings in 39.46s**。
- 首次沙箱内启动因系统无可用临时目录，在收集前退出；以相同命令获准重跑后得到上述结果，不是测试失败。
- `git rev-parse HEAD`：`51ffcb0d0a2e2af3a538a7b339da4c7154b7056d`
- 因通过数正好为 258，未额外运行 `git status`。
- 未运行 negverify；未运行探针、变异或临时脚本；未读取 fixtures 下 `.md/.json` 正文；未修改文件。
- 按既有 Canvas 对抗审计流程拆成实现、测试、survivor 三条只读证据轨并交叉复核。当前会话未暴露 `graphiti-canvas` 工具，故无法执行该项记忆查询。


