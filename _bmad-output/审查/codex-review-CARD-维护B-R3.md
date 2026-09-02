BLOCKER/HIGH 清零：否（就计数取值口径而言）

## 冻结判定

当前审查绑定 HEAD `edd471bc5ff8e5912c535ef793537ebae8ea1dec`。结论为 **FAIL**：合并后的两个主消费循环局部正确，但仍存在可见计数不入池、错值入池及尾片重锚的 HIGH 路径。本报告不构成合并授权。

### 主要发现

- ❌ **HIGH — 仍有第三个窄数值口径副本。** [`recap_scan.py:1492`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1492) 的 inline-code 守卫仍只手写 `(?![0-9]+`)`。它在 `_visible_text` 前挖空，见 `recap_scan.py:1780-1786`。因此中文/全角/千分位数值，甚至 `` `987654个` ``、`` `987654 个` `` 这类完整可见计数都可能整体免检。  
  精确说：没有发现第三份完整 `_D2_QUANT` 或 `_NUMERAL_LIKE_CHARS` 字面副本；但“所有数值闭表副本均消除”不成立。

- ❌ **HIGH — 过度拼接仍不保值。** `_D2_NOISE_ONE`、`_join_free` 会删除可见修饰字、空白、反斜线等，`_visible_text` 又无条件删除 `*`/`_`，见 `recap_scan.py:1416,1434-1449,1637,1664-1666`。`_join_free` 的注释已承认 fail-open，但 `_visible_text` 的注释仍称“安全向、不构成虚构通道”，见 `recap_scan.py:1634-1635,1650-1651`，登记仍自相矛盾。

- ❌ **HIGH — renderer 闭包仍有具体缺口。** full/collapsed reference link 已处理，但 `_VIS_REFLINK_RE` 只覆盖 `[text][ref]`/`[text][]`，不覆盖有定义的 shortcut `[text]`，见 `recap_scan.py:1621-1626`。highlight/math/脚注仍是已承认开放面。此外 `_INVISIBLE_ONE` 覆盖 U+2060–2069，而全文硬拒绝只到 U+2064，见 `recap_scan.py:1429,2244-2247`；bidi isolates 被简单删除而非按视觉顺序解释，逻辑入池顺序与视觉顺序仍可能分叉。

- ⚠️ **HIGH-3 仍仅部分修复。** seed ledger、五元组、tips 两数仍按 raw 文本绑定，见 `recap_scan.py:1255-1258,1941-1960,2015-2033,2060-2075`。统一 `_visible_text` 没覆盖这些专用路径。

## 四个问题的直接回答

1. **有。** 已知的错拼、闭表外尾片重锚、未覆盖 renderer 结构均可令入池值不等于视觉值；inline-code/raw 路径甚至可令可见计数完全不入池。

2. **三张主表的窄义登记诚实，但全链库存被低估。** `_NUMERAL_LIKE_CHARS`、`_D2_QUANT`、`_CJK_NUM` 确是三个主口径；但边界还依赖手工 `_CJK_UNIT`/`_CJK_NUM_EXTRA`，取值还受 join/invisible、range、decimal、千分位、负号和 renderer 闭集影响。负号集还在 D2/fallback 手抄两次，见 `recap_scan.py:1891,2179`。

3. **两个新消费循环内部成立，全链不成立。** D2 在 `recap_scan.py:1886-1911`、fallback 在 `:2186-2201` 都执行宽定界→`_join_free`→窄赋值→`None` fail-closed；区间端点也共用判值器，见 `:1828-1835`。但前置豁免、raw 绑定和开放断点可让完整 token 根本到不了它们。

4. **新门存在空洞或过宽措辞。**

   - `_one_problem_has` 只保证 needle 在同一输出行；problem 尾部会回显完整源行，错误的短 token 可借上下文中的完整 token 通过，见 [`test_recap_scan_signals.py:3441-3448`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3441) 与 `recap_scan.py:1864-1867,1903-1912,2171-2175`。
   - r7 的“区间端点只在句式门后报告”放行样例使用池内 `2~3`；即使错误地在句式门前核验也不会产生坏端点，见测试 `:3573-3579,3621-3628`。
   - 切断矩阵把可见“余”、空格和 inline-code `x` 当作渲染后连续数，实际编码了过度拼接，见测试 `:3323-3333,3354-3365`。
   - r12 注释仍称⑦⑧副本存在，已与当前直接引用实现不符，见测试 `:4117-4134`。

## round-8 九条复核

| 条目 | 冻结结论 |
|---|---|
| HIGH-1 | ✅ `_D2_QUANT` 副本已消除；但 inline-code 的 ASCII-only 数值守卫构成新的窄副本。 |
| HIGH-2 | ✅ 原 55 字分叉副本已消除，⑦⑧直接引用 `_NUMERAL_LIKE_CHARS`，见 `recap_scan.py:1371,1379-1380`；测试注释未同步。 |
| HIGH-3 | ⚠️ 部分；raw 专用绑定仍在，而且不止 seed ledger/五元组，还包括 tips 两数。 |
| HIGH-4 | ⚠️ full/collapsed reference-style 已修；shortcut 与已登记 renderer 开放面未闭。 |
| HIGH-5 | ❌ 未修。round-13 特定修法确实只把错拼放行移成尾片放行，未建立安全不变式；但它有“停止错误拼值”的局部收益，且撞红的三道门部分编码了错误语义。因此“该补丁没闭合问题”成立，“无收益/无有界修法”不成立。 |
| HIGH-6 | ❌ 闭表外尾片重锚仍开放。 |
| HIGH-7 | ⚠️ survivor-20 的具体捕获组崩溃已修，见 `recap_domain_negverify.py:275-285`；新增崩溃识别本身不合格。 |
| HIGH-8 | ⚠️ 仍是部分证明；组合变异及诊断上下文假阳仍存在。 |
| HIGH-9 | ✅ 当前生产行为已补中文“负”和 `例束艘架间`；但负号两侧仍是独立手抄集，门未逐字符锁住全部负号变体。 |

## negverify 静态复核

- ❌ **崩溃假阴存在。** `run_suite` 只扫描外层 pytest stdout，并只枚举五种异常名，见 [`recap_domain_negverify.py:507-531`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:507)。测试的 `run_verify` 把内层 CLI traceback 捕获在 stderr，见测试 `:103-110`，却没有结构化传播保证。`IndexError/ValueError/KeyError/RuntimeError/INTERNALERROR` 等也不识别。
- ⚠️ **假阳可能。** 它只是全文异常名搜索；普通日志、断言文本或源码摘录出现 `TypeError` 等也会被当作生产崩溃。当前目标测试中未发现一个已发生的具体假阳。
- ⚠️ 不要求变异轮 `rc == 1`；只要有 collected failure 且关键词未命中，就可能记为承重，见 negverify `:573-589`。
- survivor-15…39 未发现新的确定性语法崩溃。相对单一的变体为 15–17、22–23、26、28–31、33–39；18–21、24–25、27、32 含组合或过宽退化。尤其 19、20、25 的一次变红只能证明组合中至少一个分量承重。
- 因此车道提供的 **39/39** 只能记为 `PARTIAL`，不能解释为 25 条新增性质全部逐项独立承重。

## 实际执行与边界

- `git rev-parse HEAD`：`edd471bc5ff8e5912c535ef793537ebae8ea1dec`
- 获准 pytest：**262 passed, 14 warnings in 39.49s**
- 首次沙箱启动在收集前因没有可写临时目录退出；同一命令在可写临时环境重跑后得到上述结果，不是代码测试失败。
- 因测试数正好为 262，未运行 `git status`。
- 未运行 negverify、探针、diff/show/log；未读 fixtures 正文。车道自报的 39/39、594、84/84 未由本轮独立重跑。
- 当前工具没有暴露 `graphiti-canvas`，本轮 Graphiti 查询不可执行。
- 卡文轮次超限仍未获追认；本报告仅为当前 HEAD 的冻结测量。


