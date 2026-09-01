BLOCKER/HIGH 清零：否（就计数取值口径而言）

判词：**0 BLOCKER / 7 HIGH**。257 门全绿，但仍有静态可达的取值绕过。

### 实现问题

1. ❌ **HIGH — 区间先挖空、后判句式，裸 `共有/总计/合计` 自陈失锚。**  
   `_D2_CLAIM_RE` 的第二分支依赖其后仍有数字；区间替换先把数字整段挖空，随后句式门直接 `continue`，已收集的坏端点不再报告。静态例：`总计987654-0个…`。[recap_scan.py:1401-1404](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1401) [recap_scan.py:1690-1717](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1690)

2. ❌ **HIGH — 区间仍是独立的裸 ASCII 窄路径。**  
   `_D2_RANGE_RE` 没复用 `_NUM_RUN_PAT/_D2_JOIN_ONE`。`本板共有987654<b>-</b>0个…` 渲染为同一区间，但只会按右端 `0` 入池；中文/混写端点同理。[recap_scan.py:1434-1436](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1434) [recap_scan.py:1743-1755](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1743)

3. ❌ **HIGH — 千分位只认源码中紧邻数字的逗号。**  
   `987654<b>,</b>000个` 渲染为 `987654,000个`，但归一化不命中；D2 只查 `000→0`。fallback 的 `1<b>,</b>005` 会按 `[1,5]` 碰池。两消费点虽共用函数，但共用的是不完整防线。[recap_scan.py:1550-1559](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1550) [recap_scan.py:2007-2029](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2007)

4. ❌ **HIGH — HTML character reference 未规范化。**  
   仅特判 `&nbsp;/&#160;`；例如 `987654&#46;0个` 渲染为小数却只查尾端 `0`，`987654&#20010;` 渲染为 `987654个` 却完全没有源码量词锚点。[recap_scan.py:1355](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1355) [recap_scan.py:2039-2076](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2039)

5. ❌ **HIGH — 小数门要求分隔符两侧均有数串。**  
   `.5个`／`．五个` 不命中小数式，两个消费点都会把 `5` 入池；这违反“小数计数恒 FAIL”的现有口径。[recap_scan.py:1405-1406](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1405) [recap_scan.py:1543-1547](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1543)

6. ❌ **HIGH（存量）— `_NUMERAL_LIKE_CHARS` 的遗漏仍会尾片重锚。**  
   例如常用大数单位 `兆` 不在表内；`九兆五个` 会从 `五` 重锚。验收单承认闭表，但把此类后果列为 MEDIUM，低于此前 `廿五` 同机制的 HIGH 口径。[recap_scan.py:1525-1534](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1525) [UAT:511-514](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/_bmad-output/验收单/UAT-CARD-维护B-R3-中文数词终态-2026-09-02.md:511)

7. ❌ **HIGH（存量）— `_D2_QUANT` 漏常见计数量词时整句零校验。**  
   如 `本板共有987654层关系`；`层/节/列/枚/步/级` 等均不在表内。另 `_D2_INLINE_CODE_RE` 仍手抄同一量词表，当前相等但保留后续分叉面。[recap_scan.py:1393-1421](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1393)

### 四问结论

- ✅ `_CJK_NUM` 的窄赋值正确；测试期望独立写死。
- ⚠️ `_NUMERAL_LIKE_CHARS` 的精确集合已锁定，但“宽”只相对于赋值表成立，不足以保证真实数词不重锚。
- ❌ `_D2_QUANT` 未被精确冻结；验收单称“34 字”，实现实际为 32 字。[UAT:162-163](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/_bmad-output/验收单/UAT-CARD-维护B-R3-中文数词终态-2026-09-02.md:162)
- ⚠️ “定界宽、赋值窄”在普通 D2/fallback token 上成立，但端到端仅 **PARTIAL**：range、实体、分隔符和漏表字符会在统一判值前切断。
- ⚠️ 字面上的“入池值等于渲染所见数”本来也不成立：`_join_free` 明示 `1*0→10`；这是安全向过拼接，不是上述 fail-open。[recap_scan.py:1371-1378](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1371)

### 门与 negverify

- ✅ 独立期望、定界集精确相等、`980005 + 找不到同值来源` 同行绑定均成立。
- ⚠️ R7 三个区间都只用“大数 `987654` + 池内 `0`”；只检查 `max(ends)` 的错误实现仍可全绿，也没有“双端均坏、逐个报”的门。[test:3579-3587](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3579)
- ⚠️ 所有区间门都用 `个`，未证明 range 真正共享完整 `_D2_QUANT`；全角小数点 `．` 也没有输入门。[test:3553-3605](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3553)
- ⚠️ `_one_problem_has` 保证同一输出行，但只做子串包含，不证明 token 边界精确。[test:3427-3434](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3427)
- ⚠️ survivor-15/16/17 静态上确实击穿对应共享防线；18 只证明左端防线，19/20 各组合多个替换且共用一个串行测试函数。“20/20 变红”只能证明每个组合至少一项承重，不能分别证明所有子性质。[negverify:197-266](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:197)

### 实际执行

- 定向 pytest：**257 passed，14 warnings，36.53s**。
- 首次沙箱内调用在收集前因无可用临时目录退出；随后以完全相同命令在可写临时环境执行成功。
- `git rev-parse HEAD`：`1d668ffc29e2d85d256c6ba05b79507f033cd5de`
- 未运行 `git status`（计数与预期一致）；未运行 negverify、探针或变异。


