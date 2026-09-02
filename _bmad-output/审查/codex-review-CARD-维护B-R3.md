BLOCKER/HIGH 清零：否

核心结论：raw 优先逻辑仅在“raw/visible 来自同一小节、同一源行”这一未验证前提下成立；当前存在可静态推演的错绑路径。另一个直接问题是：所称“第 0 步锚点预检”在当前源码中不存在。

### 主要发现

- ✅ **窄范围 PASS** — raw 可解析时取 raw 身份和值；仅 raw 不可解析才查 visible 索引，多个候选明确 fail-closed。分支可达，不是死代码。[recap_scan.py:2120-2160](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2120)

- ❌ **HIGH｜本轮配对逻辑** — raw/visible 分别用首个 `re.search` 选段，再按下标配对，未验证选中的是同一小节。[recap_scan.py:2081-2117](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2081)  
  静态反例：先放 `### 种**子** / A=999`，后放 `### 种子 / A=正确值`。visible 选前段，raw 选后段；代码随后完全采用后段 raw 的身份和值并 `continue`，可见的 999 未被核对。fallback 的形状门也只选首个 visible 段，不能兜底。[recap_scan.py:2524-2540](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2524)

- ❌ **HIGH｜本轮行数边界** — `_visible_block` 的“行数与顺序不变”声明不成立。`html.unescape()` 可将单个 raw 行中的 `&#10;`、`&#13;` 或 `&NewLine;` 解成换行。[recap_scan.py:1760-1783](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1760)  
  插入一个换行实体即可令后续 visible 假数行按下标取到下一条 raw 合法行；`raw_ms` 分支验证的是错误配对对象。[recap_scan.py:2110-2132](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2110) 行为门明确承认未覆盖行数不齐。[test_recap_scan_signals.py:4783-4785](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4783)

- ❌ **HIGH｜存量** — 只处理首个 `### 种子`，且不限定其位于唯一的 `## 台账` 下。一个正确诱饵小节可遮住后面的冲突小节；H2 唯一性门不检查 H3。[recap_scan.py:825-832](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:825) [recap_scan.py:2081-2085](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2081)

- ⚠️ **合法用法误伤** — raw 行“能解析”不等于 raw 节点串就是精确身份。例如 ledger ID 为 `A&B`、报告合法写成 `A&amp;B` 时，读者看到相同名称，但 raw exact miss 后代码直接报错，不会尝试唯一 visible 候选。[recap_scan.py:2120-2137](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2120)

### 锚点预检与变异证据

- ❌ **HIGH｜声明与源码不符** — 当前没有“52 条恰好命中一次 + 5 条手工 dry-run + 任一失败即中止”的第 0 步。实际流程先跑基线，再逐变体仅检查 `old not in text`，随后 `replace(..., 1)`；重复锚点会静默改第一处，失败也只是累计后继续。[recap_domain_negverify.py:750-775](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:750)

- ⚠️ 没有固定断言 `len(MUTANTS) == 52` 或唯一 ID 集；误删一个变体仍可成功退出，只会动态打印“共 51 条”。[recap_domain_negverify.py:816](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:816)

- ⚠️ “恰好命中一次”本身也不够：它只证明文本定位唯一，不证明位置可达、替换非空或确实禁用了目标防线。脚本自己的历史说明已承认“锚点仍命中但变异已为空”。[recap_domain_negverify.py:11-19](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:11)

- ✅ 每次实际变异目前有 `finally` 还原和 SHA-256 比对；但比对使用 `assert`，优化模式可移除，且 `run_suite` 抛异常后不会执行后续 hash 自检。[recap_domain_negverify.py:786-792](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:786)

- ⚠️ 变异归因仍过宽：
  - survivor-40 实际只丢失 CJK/扩展数词保护，ASCII `987654 个` 仍受保护，名称范围过宽。[recap_domain_negverify.py:479-487](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:479)
  - survivor-44 是无条件挖空全部 code span，不是“退回 raw 判据”。[recap_domain_negverify.py:533-540](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:533)
  - survivor-48 清空共享 `_D2_RANGE_SEPS`，同时破坏 code-span 字符域和主区间正则，红结果无法归因到单一防线。[recap_domain_negverify.py:568-578](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:568)
  - survivor-52 只是强制跳过 raw 分支，并未重建名称所述的“归一名直接查 raw 表”。[recap_domain_negverify.py:611-618](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:611)
  - `-k "A or B"` 加上只要求 `f > 0`，仍只能证明至少一道选中门红了。[recap_domain_negverify.py:793-814](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:793)

### 行为门与崩溃识别

- ⚠️ **调用点门可假绿** — 当前 `_visible_block(` 文本出现 6 次：定义 1、真实调用 4、注释 1。测试只要求 `>=5`；删除任一真实调用仍剩 5，门继续绿。[test_recap_scan_signals.py:4759-4764](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4759) 注释假计数来自 [recap_scan.py:2520](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2520)。

- ⚠️ **11 字双向锁为 PARTIAL** — 当前两个消费面确实都由同一 `_D2_RANGE_SEPS` 派生，新增到该常量的字符也会被循环检查，这是 ✅。但 `len >= 11` 没锁定确切集合或 distinct；用 11 个重复字符替换仍可通过。[test_recap_scan_signals.py:4566-4574](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4566)

- ✅ 没发现新的“无论实现怎么改都恒真”的断言。此前自读源码的恒真接线门已改成 monkeypatch 哨兵，确实验证同一个 `CompletedProcess` 对象及 marker 行为。[test_recap_scan_signals.py:4666-4699](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4666)

- ⚠️ **崩溃识别仅 PARTIAL** — 当前实现已不是题述的“有冒号二分”；冒号条件已删除。实际规则是 `E` 后 1–3 空格加标识符，并白名单排除 `assert`、`AssertionError`。[recap_domain_negverify.py:674-695](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:674)
  - 当前 `--tb=short` 样例可区分 3 格异常和 4–7 格续行。
  - formatter 改缩进、生产代码抛 `AssertionError`、无 traceback 的 SyntaxError/SystemExit/致命信号仍可能假阴。
  - 正文偶含 marker、`Traceback...` 或 `N error(s)` 可假阳。
  - 只有 `run_verify` 抬出了子进程 stderr；`run_collect` 没有接这条通道。[test_recap_scan_signals.py:93-139](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:93)  
  测试文案已诚实承认它不是可靠二分。[test_recap_scan_signals.py:4591-4599](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4591)

### “未改动三处”判断

判断成立：

- ⚠️ tips 仍在 raw `recon.group(1)` / `text` 上找数；③标题/段抓取也仍基于 raw 或仅剥代码块的文本。[recap_scan.py:1113-1115](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1113) [recap_scan.py:2267-2282](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2267)

- ❌ **HIGH｜存量** — manifest seed 的 `rest` 仍接受任意 `；/;/·` 后缀，只验证前面的 tips 数；visible 行不匹配模板时仍静默 `continue`。manifest 没有 fallback 的形状兜底。[recap_scan.py:1262-1265](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1262) [recap_scan.py:2118-2119](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2118)

- ❌ **HIGH｜存量** — D2 分段把 H2 标题本身排除，只检查 `h.end()` 后的正文；`## 本板共有 999 个子节点` 不受 D2 校验。[recap_scan.py:1879-1884](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1879)

### 其他存量问题

- ❌ **HIGH｜表示层缺口** — 非计数 inline code 被整段挖空。`本板`有` 987654 个子节点` 在 Obsidian 里仍显示完整句子，但 D2 先挖掉“有”，claim 门失锚后直接跳过。[recap_scan.py:1525-1559](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1525) [recap_scan.py:1902-1987](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1902) 同型写法也能切开 tips、信号 label 或 m7 固定词。

- ❌ `_join_free` 已在源码中自认 fail-open：`1\*5` 可按 15 入池，`5多个` 可按精确 5 入池；这不能证明“校验器读到的数等于读者看到的数”。[recap_scan.py:1441-1454](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1441)

- ⚠️ manifest 不拒绝重复 raw `node_id`，binder 又以 dict comprehension 静默 last-wins；同 ID 不同 `tips_count` 时没有 fail-closed。[recap_scan.py:368-376](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:368) [recap_scan.py:2098](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2098)

### 闭合分组

一次改动内可以闭合：

- 实装真正的预检：固定 52 个唯一 mutant ID、每个 old 精确一次、5 个 dry-run、失败立即退出。
- 对 `### 种子` 做唯一性和父级作用域检查；拒绝归一后产生行分隔符；显式核对 raw/visible 行映射。
- manifest 对每个非空 visible seed 行 fail-closed，并给 `rest` 定正向模板。
- 把 H2 标题纳入 D2；拒绝重复 exact node ID。
- 用 AST/逐消费方行为哨兵替代源码字符串计数；锁定区间分隔符的独立期望集合。
- 拆开 survivor-48 等组合变异，并让每个 mutant 绑定明确失败测试及失败原因。

需要重做设计：

- 建立一套 Obsidian/Markdown-aware、保留 raw source span 与源行映射的表示；tips、③、五元组、seed、m7、D2 共用它，同时保留 code-span 是否可豁免的类型信息。
- 明确定义 raw 身份与渲染后身份碰撞时的策略，最好用可解析链接目标承载稳定 ID。
- 变异在隔离副本运行，并输出结构化 assertion/crash 结果，停止解析 pytest 人类可读文本。

### 实际验证

- `git rev-parse HEAD`：`8c0b8019d71bac57e25c8bc6e5ebe089447ec5a2`
- 指定 pytest 首次在只读沙箱中因无可用临时目录、收集前失败；获准原样重跑后：`271 passed, 14 warnings in 40.39s`
- 未运行 `recap_domain_negverify.py`，因此未验证自报的 52/52。
- 未运行扩大 603 门、未读 fixtures 正文、未构造探针/临时文件、未运行 diff/show/log。
- 因禁止 diff，无法证明哪些现存问题确属本轮首次引入，也无法审计是否有列出三文件以外的范围变化；上述“本轮/存量”依据用户说明与当前源码注释标注。
- 新反例均为沿控制流的静态推演，不冒充已执行复现。


