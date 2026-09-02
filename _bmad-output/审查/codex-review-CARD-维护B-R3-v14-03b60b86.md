BLOCKER/HIGH 清零：否

### 主要发现

- ❌ HIGH（本轮引入，范围误伤）— [recap_scan.py:2191](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2191)  
  `_H3_SEEDISH_RE` 的报错条件没有 `_under_ledger` 约束，遍历全篇执行。因此正文或附录中的合法 `### 种子相关说明` 会直接报错，重新引入 R23 曾修过的“超出台账父级”范围问题。它还允许任意前导空白；而四空格缩进代码块没有被 `_strip_code_blocks` 剥除，[recap_scan.py:1005](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1005)，所以代码示例里的 `    ### 种子说明` 也会误报。R27 只测了围栏代码块，没有覆盖这两类合法输入，[test_recap_scan_signals.py:5265](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:5265)。

- ❌ HIGH（第七形态，静态可达）— [recap_scan.py:1790](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1790)、[recap_scan.py:2211](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2211)  
  强调和 HTML 拆词会被 `_visible_text` 归一，所以 `种**子**` / `种<b>子</b>` 不是有效第七形态。但 inline code 和 Obsidian highlight 明确未归一。可构造：

  ```md
  ### 种子

  ### `种子` ###
  - Ghost — 批注 9 条
  ```

  第一节合规但为空；第二个 H3 会终止第一节，却既不匹配认可标题，也不匹配 `种子` 前缀；Ghost 行因此不进入任何 `sections`。`### ==种子== ###` 同理，源码也明确承认 highlight 未覆盖，[recap_scan.py:1729](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1729)。更一般地，第二节改成 `### 其他` 后装台账形状行也不受种子绑定。以上按要求未执行探针，但控制流静态闭合。

- ❌ HIGH（存量设计）— [recap_scan.py:1646](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1646)、[recap_scan.py:2017](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2017)  
  D2 仍不是字段绑定，而是“全 scan 数值池＋任意一阶和差”的碰撞判据。`本板共有 5 个子节点` 可以因为 5 出现在无关字段、或等于任意两个数的和/差而通过；不要求它等于真正的成员/子节点字段。源码自己已准确承认这是碰撞判据。因此“报告数字有出处”仍不能解释为“该陈述对应的字段有出处”。

- ❌ HIGH（存量直接绕过）— [recap_scan.py:2450](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2450)  
  AI 侧对账的 tips 两数仍在 raw `text/recon.group(1)` 上 `findall`。保留正确行，再追加 `tips 批**注**共 999 条` 或 HTML 拆词冲突行，读者看到的是同一句式，绑定器却看不到。你登记的“tips 两数仍 raw”判断成立。

- ❌ HIGH（存量直接绕过）— [recap_scan.py:1475](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1475)、[recap_scan.py:1749](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1749)  
  `1\*5个` 仍会被归一成 15；若池中有 15 即放行，但 Obsidian 用户看到的是 `1*5`。源码已如实登记为 fail-open，判断成立。

- ⚠️ MEDIUM（存量误伤）— [recap_scan.py:1766](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1766)  
  `_RANGE_LEFT_BAD_RE` 允许“小数点前无数字”并把空白视为连接符，因此句号或名词“点”后加空格再写合法区间，也可能被当成 `.2~3` 的小数碎片。例如 `本板共有要点 2~3 个`。现有门只测真正紧邻的 `.2~3`，未测标点/词语边界。

- ⚠️（存量判断需校正）— [recap_scan.py:2108](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2108)  
  “尾巴只拦 ASCII `批注 N 条`”不完全准确：`\d` 会匹配 Unicode 十进制数字，全角数字还会先转 ASCII。真正未覆盖的是中文数词、带圈数字、苏州码等非 `Nd` 数字形态。

- ⚠️（存量设计债）— ③段仍有三套定位：[recap_scan.py:1142](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1142)、[recap_scan.py:2503](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2503)、[recap_scan.py:2696](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2696)。  
  第三套甚至只在下一个 `### ` 停止，不在 H2 停止。D2 切段又丢掉 H2 标题正文，[recap_scan.py:1919](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1919)，且豁免标题口径与 `_SECTION_RE` 不同。你登记的判断成立。

### 行为门与变异证据

- ✅ `seeds=[None]` 的生产修复正确命中专用损坏诊断，[recap_scan.py:2272](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2272)。R27 三条拒绝形态均绑定关键词，三条放行形态要求 `ps == []`；没有恒真断言，[test_recap_scan_signals.py:5231](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:5231)。

- ✅ R23 已去 `_cli`、去掉无用 `tmp_path`，名实一致，[test_recap_scan_signals.py:4916](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4916)。R26 文案也确已收窄。

- ❌ HIGH（证据结论过宽）— [recap_domain_negverify.py:760](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:760)  
  survivor-64 只禁掉“含非对象条目”专用诊断；后续仍会对 X 报“不在 ledger”。升级后的 R27 会因缺目标关键词而红，但这证明的是专用诊断承重，不是“损坏 seeds 被当合法零种子”。因此“64/64 条语义防线均如期失效”不成立，mutant 名称和脚本铁律仍冲突。

- ❌ HIGH（存量假绿面）— [recap_domain_negverify.py:848](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:848)、[recap_domain_negverify.py:1011](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:1011)  
  `-k` 仍只要求匹配集合 `n>0`、`rc==1`、`f>0`；不核失败 node-id、数量或诊断。集合内任意目标无关失败都能记成“如期变红”。`rc=5` 和 rc 2/3/4 的修复有效，但不足以完成归因。

- ⚠️ R26 三条拒绝仍只 `assert ps`，[test_recap_scan_signals.py:5172](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:5172)。R20、R15–R17、R25 CLI 也仍有只看非零退出的门。源码形状门仍存在于 [test_recap_scan_signals.py:4198](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4198) 和 [test_recap_scan_signals.py:4763](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4763)，可被死代码/无关调用补足，也会拒绝等价重构。

- ⚠️ 崩溃二分仍会判错。[recap_domain_negverify.py:781](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:781) 实际不是“有冒号即异常”，而是 `E` 后 1–3 格的标识符、排除 `assert/AssertionError`。它对当前 `--tb=short` 的列举样本有效，但无 traceback 的子进程退出会假阴、正文含 traceback 会假阳，formatter 改缩进也会失效。测试自身已如实承认“不可靠二分”，[test_recap_scan_signals.py:4599](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4599)。R19 的真实 monkeypatch 接线和 traceback marker 是有效的局部改进。

### 一次改动内能闭合

- 给 seedish 检查加 `_under_ledger`、ATX 0–3 格边界和“种子”词边界；补正文说明标题、四空格代码、inline-code/highlight H3 门。
- 在 `sections` early return 前统一验证 ledger/seeds 形状、必备字段、类型与重复 node-id；补“无 ledger 且无认可 H3”。
- tips 两数改为同源的 visible section/visible lines，并加“好行＋格式化冲突行”的诊断绑定门。
- R26/R20/R25 等拒绝门绑定目标诊断；删除源码调用次数门，改行为哨兵。
- survivor-64 收窄名称为“专用诊断被摘除”，或真正构造会错误接受的 mutant；mutation runner 核精确 node-id/失败数。
- 区间左前文区分小数点紧邻与句号/词语后的空白。

### 需要重做设计

- 用同一 Markdown/Obsidian 解析结果建立段落、容器、围栏和可见文本，替换目前多套 regex 定位；否则标题语义仍是开放集。
- 把 D2 数值池碰撞改成“句式/报告字段 → scan JSON 字段”的结构化绑定。
- 变异在隔离副本中运行，并输出机器可读的测试身份、失败原因和 SUT 异常状态；不能靠解析 pytest 文本可靠区分崩溃。
- 解决落单 Markdown 标记、近似量词等会改变可见数字的归一问题。

### 实际验证

- `git rev-parse HEAD`：`03b60b8617af9d18d030f09d4386b19980b47bd4`，与自报一致。
- 指定 pytest：`277 passed, 14 warnings in 47.68s`。沙箱内首次因无可写临时目录在收集前失败；获准后以完全相同命令重跑通过。
- 未运行变异脚本、609 扩大回归或任何探针；未读 fixtures 正文；未运行 `git diff/show/log`。64/64、扩大回归和前后逐字节一致均未独立复验。当前无 Graphiti 工具入口；未编辑代码，因此未运行 LSP。


