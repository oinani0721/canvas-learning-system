BLOCKER/HIGH 清零：否

### 本轮处置复核

- ❌ HIGH #51 的改名并未落实。[recap_domain_negverify.py:607](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:607) 仍称“冲突行逃逸”，实际替换把整个 `vis_lines` 退回 raw，连 H2/H3 定位、终点和行形状都一起退化。冲突行仍会被非模板门拒绝（[recap_scan.py:2261](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2261)）；真正变红的是合法渲染等价行被误拒（[test_recap_scan_signals.py:4752](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4752)）。

- ❌ HIGH #55 同样仍是旧名称。[recap_domain_negverify.py:647](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:647) 实际令 `_stripped == raw_lines`，代入 [recap_scan.py:2161](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2161) 后 `_in_fence` 恒为 `False`，不存在名称声称的布尔翻转。红因是 fenced seed 被当正文、诊断不再是“找不到可绑定”（[test_recap_scan_signals.py:4982](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4982)）。

- ✅ #56 两步替换名实一致。[recap_domain_negverify.py:662](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:662) 先恢复遍历 `groups.values()` 摊平，随后把 `seeds` 置 `None`；替换按顺序执行。`DerivedX` 确实会进入索引并按 `tips_count=5` 被错误放行，从而打红 [test_recap_scan_signals.py:4980](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4980)。

- ❌ HIGH 新 H3 fail-closed 只处理“零个认可 section”，没有闭合全部 H3：

  ```md
  ## 台账
  ### 种子
  ### 种子 ###
  - SeedA — 批注 999 条
  ```

  第一处令 `sections` 非空；第二处会截断前一小节，却不被 `_H3_SEED_RE` 接受，因此 999 行不属于任何受检区间，且 [recap_scan.py:2205](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2205) 的新门不再触发。

- ⚠️ 新 H3 门确实扩大了合法拒绝面。`### 种子 ###` 是 Obsidian/CommonMark 合法 ATX 标题，测试自己也如此描述（[test_recap_scan_signals.py:4925](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4925)），当前却把拒绝锁成正确行为。只有把“合法”限定为校验器的窄模板语法，才不算误伤。

- ❌ 存量合法零种子也会失败。生成侧允许 `seeds=[]`、`counts.seeds=0`（[recap_scan.py:2945](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2945)），但 [recap_scan.py:2226](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2226) 把空 seed 列表当成“无可用 ledger”。现有空板门只测 collect，没有生成并 verify 报告（[test_recap_scan_signals.py:602](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:602)）。

### 行为门与崩溃识别

- ✅ 新 H3 断言本身不是恒真；它们直接调用 helper 并要求特定诊断。R19 原来的自读源码恒真门也已改为 monkeypatch 哨兵，并核对同一个 `CompletedProcess`（[test_recap_scan_signals.py:4654](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4654)）。

- ⚠️ 但门的措辞仍过宽：名为 `_cli` 的 R23 实际只调用 helper（[test_recap_scan_signals.py:4916](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4916)）；文案称“八种”，参数表实际九项。R25 的 H3 部分也没有走公开 CLI。

- ⚠️ #51/#55/#56 都把一个含多项断言的测试函数交给 `-k`；runner 只确认“某项失败”，不确认失败断言就是目标性质。因此 #56 的归因是本次静态控制流确认的，不是 runner 自身能证明的。

- ❌ 崩溃二分会判错，而且当前实现已经不要求冒号。实际规则是 `^E {1,3}<token>`，除 `assert/AssertionError` 外都算崩溃（[recap_domain_negverify.py:787](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:787)）。例如：

  ```text
  E   AssertionError: x
  E   Expected: 3
  ```

  第二行会被误认成异常类 `Expected`。反向，生产代码或依赖真正抛出的 `AssertionError` 会被当作正常门红。无 traceback 的子进程崩溃仍可漏报，而正文偶含 traceback、`INTERNALERROR` 或 `N errors` 又可误报；源码自身已把它降格为启发式。

- ⚠️ 仍有源码形状门而非行为门，例如 [test_recap_scan_signals.py:4198](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4198) 和 [test_recap_scan_signals.py:4763](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4763)。它们不是字面恒真，但死调用、无关调用或保留字符串可以造成目标无关假绿。

### 存量未闭合问题

- ❌ HIGH “未改动的三处”判断成立：

  - ③段仍有三套定位口径：[recap_scan.py:1142](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1142)、[recap_scan.py:2457](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2457)、[recap_scan.py:2650](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2650)。
  - D2 切段丢掉 H2 标题行，豁免规则也与 `_SECTION_RE` 不同（[recap_scan.py:1919](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1919)）。`## 本板共有 987654 个子节点` 的数字不进入正文循环。
  - 小节终点仍不覆盖空 ATX、Setext；而 `**## 假标题**` 会被 `_visible_text` 合成为结构标题并提前截断种子段（[recap_scan.py:1773](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1773)、[recap_scan.py:2197](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2197)）。

- ❌ HIGH tips 两数仍在 raw 文本上匹配（[recap_scan.py:2420](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2420)）。保留正确行，再增加 `tips 批**注**共 999 条`，读者能看到冲突数字，但两次 `findall` 都看不到。

- ❌ HIGH 种子行尾巴只拦第二个 ASCII `批注 N 条`（[recap_scan.py:2093](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2093)）。`理解度未闭环 999 条`、`已派生 999 点` 可放行；注释称没有对应字段并不属实，ledger 已有 `tips_open`（[recap_scan.py:483](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:483)）和 manifest 的 `derived_children_count`（[recap_scan.py:2948](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2948)）。

- ❌ HIGH 核心“读到的数等于读者所见”仍被源码自己的已知反例否定：`1\*5个` 在 Obsidian 显示为 `1*5`，实现却剥成 `15`；若池内有 15 即放行（[recap_scan.py:1475](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1475)）。

- ❌ HIGH 扁平 legacy ledger 分支仍把所有角色当种子（[recap_scan.py:2238](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2238)）；derived 行仍可冒充 seed。

- ❌ HIGH 即使数值抽取正确，判据也不是字段绑定：[recap_scan.py:1646](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1646) 收集整个 JSON 的整数并额外加入任意两值的和、差。报告的“子节点 7 个”可能因无关的 `2+5` 入池通过，JSON 中甚至不必存在字面 7。

### 闭合分类

一次改动内可闭合：

- 修正 #51/#55 名称，并为每个 mutant 使用单一目标测试/失败标识。
- 区分合法 `seeds=[]` 与损坏 ledger；扁平 ledger 按 `role` 过滤，缺 role 时 fail-closed。
- tips、段外信号统一到 visible 行空间。
- 将 `tips_open`、`derived_children_count` 与种子尾字段绑定，或禁止这些未绑定数字。
- 增加“合法诱饵 H3 + 第二个冲突 H3”的门，并走一次真实 CLI。
- 对 scan 顶层及子对象先做类型校验，避免有效 JSON、错误形状直接抛异常。

需要重做设计：

- 用统一的 Markdown/Obsidian 块级解析模型处理标题、软换行、围栏、Setext、列表 continuation、注释和嵌入；不能继续让行内 `_visible_text` 决定文档拓扑。
- 用“报告句式/字段 → 明确 JSON 路径或批准公式”替换全局整数池及任意和差。
- 变异应在隔离副本运行，并从执行源头记录目标断言与子进程终止原因，不能依赖 pytest 文本缩进猜崩溃。

### 实跑与限制

- ✅ `git rev-parse HEAD`：`3872a81518ae5a4304630faf9d8cb28630e538f7`
- ✅ 指定 pytest：`275 passed, 14 warnings in 45.34s`
- ⚠️ 第一次在只读沙箱内于收集前因“无可用临时目录”失败；获准后原样重跑得到上述结果。
- 未运行 `recap_domain_negverify.py`、607 项扩大回归、任何探针；未读 fixtures 正文；未运行 `git diff/show/log -p`。因此 61/61、源码前后逐字节一致均仅是车道自报，未独立证明。
- Graphiti 工具未暴露；已按仓库要求使用 Sequential Thinking。审计采用只读、并行、证据优先并区分 helper 与公开入口的规程，未修改工作树。


