BLOCKER/HIGH 清零：否

未发现新的 BLOCKER，但仍有可让“用户可见数字”逃出校验的 HIGH。

### 运行锚点

- ✅ `git rev-parse HEAD`：`636b09a421fbe13ae7551e8ba10d376cdec32fbb`
- ✅ 指定 pytest：`273 passed, 15 warnings in 42.58s`
- ⚠️ 首次因只读沙箱无可写临时目录，在收集前失败；获准以同一命令重跑后得到上述通过结果。警告包含 [test_recap_scan_signals.py:4847](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4847) 的无效转义 `\s`。

### 主要结论

- ❌ FAIL/HIGH（存量，本轮继续继承）[recap_scan.py:1046](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1046)：围栏打开后，仍对围栏内容逐行剥列表/引用前缀，再在 [recap_scan.py:1072](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1072) 用剥后的文本判断闭栏。静态可达路径为：

  ````markdown
  ```
  - ```
  ```
  本板共有987654个子节点
  ````

  渲染器把第二行当代码字面、第三行才是真闭栏；校验器却在第二行误闭栏、第三行重新开栏，最终把用户可见的第四行剥到 EOF。代码块兜底 [recap_scan.py:1121](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1121) 只查信号 label，不查普通规模计数。需要容器状态设计重做。

- ❌ FAIL/HIGH（本轮新正则未闭合）[recap_scan.py:1022](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1022)、[recap_scan.py:1046](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1046)：引用 `>` 后五格现在会正确留下四格并拒绝开栏；但列表 marker 后五至七格会先被 `{1,4}` 吃四格，剩余一至三格又被 `open_re` 接受，仍被误认成围栏。R22 只测了 `- ` 后一格和顶层 0/3/4 格，[test_recap_scan_signals.py:4880](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4880) 没锁 1–5 格边界。

- ❌ FAIL/HIGH（本轮引入）[recap_scan.py:2094](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2094)：`(?<![\u4e00-\u9fff])批注` 修好了 `未批注`，却把所有汉字前缀一并排除。尾巴里的 `累计批注 999 条`、`共批注 999 条`、`已批注 999 条` 都不会报错，仍是用户可见的第二个同字段数字。R23 只测裸 `批注` 与 `未批注`，[test_recap_scan_signals.py:4953](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4953) 未覆盖这些正向限定词。

- ❌ FAIL/HIGH（本轮标题修复不完整）[recap_scan.py:2146](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2146)：

  - `## 非台账示例`、`### 种子 ###`、`###种子` 三个指定案例处理正确。
  - 合法的 1–3 格前导缩进 ATX 标题仍不识别；在合规报告后追加 `   ## 台账` / `   ### 种子` 和错误行，可逃出绑定面。
  - `\s*#*` 又会误认 `### 种子###`；无前置空格的尾部井号不是合法 ATX closing sequence，用户看到的标题并非精确“种子”。

- ⚠️ PARTIAL [recap_scan.py:2175](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2175)：正常 grouped ledger 的确只取 `seeds`，派生节点反例修对。但 `seeds` 缺失或不是 list 时，[recap_scan.py:2179](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2179) 仍摊平所有角色。这超出了“只有顶层扁平 list 保持兼容”的登记范围；损坏的 grouped JSON 没有 fail-closed。

### `_strip_code_blocks` 行数前提

- ✅ [recap_scan.py:1024](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1024) 到返回前，每个输入物理行的所有分支都恰好 `append` 一项，索引顺序成立。
- ⚠️ “返回字符串再 `.splitlines()` 后行数不变”不成立：末尾空项会丢失；既有测试自己也在 [test_recap_scan_signals.py:2522](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:2522) 记录三空行只得到两项。
- ✅ 当前 seed 消费方 [recap_scan.py:2141](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2141) 对越界项按空串处理，因此尾部丢项目前不会错位。结论应表述为“索引映射保持、尾项由兜底补偿”，不能写成无条件行数恒等。
- ⚠️ `_in_fence` 只在寻找标题时使用；已进入种子小节后，区间终止与逐行检查 [recap_scan.py:2159](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2159)、[recap_scan.py:2193](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2193) 不再跳过 fenced 行。因此 R23 的“不在围栏内才生效”仍比实际范围宽。

### “未改三处”

判断成立，且都是存量未闭合：

- ❌ HIGH：tips 两数仍在 raw `recon.group(1)` / raw `text` 上查，[recap_scan.py:2363](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2363)。保留正确行，再追加 `tips 批**注**共 999 条`，后者不进入绑定。
- ❌ HIGH：③段仍以 raw `^### ③` 定位，[recap_scan.py:1127](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1127)、[recap_scan.py:2589](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2589)。额外的渲染等价 `### **③**` 冲突段不会按第二个③段全查。
- ❌ HIGH：D2 把正文从 `h.end()` 开始切，[recap_scan.py:1908](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1908)，H2 标题本行的 `## 本板共有 987654 个子节点` 不进入计数循环。
- ⚠️ 设计边界仍在：[recap_scan.py:1706](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1706) 已承认 `_visible_text` 不是完整 renderer；未配对强调符的错误拼接甚至被明确登记为 fail-open，[recap_scan.py:1735](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1735)。

### 行为门与变异证据

- ✅ R23 没有恒真断言；九个 case 都调用真实函数并核对 `problems`。
- ⚠️ 它名为 `_cli`，实际只直接调用私有函数，`tmp_path` 未使用，[test_recap_scan_signals.py:4916](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4916)、[test_recap_scan_signals.py:4936](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4936)。本轮四反引号、角色、标题、尾巴案例没有走真实 CLI。
- ⚠️ [test_recap_scan_signals.py:4932](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4932) 写“八种”，实际是九种；九例又塞在一个普通 `for` 的单一 pytest item 中，因此变异下只能证明“至少一个断言红”，不能逐性质归因。
- ❌ survivor-55 错归因：[recap_domain_negverify.py:647](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:647) 声称退回旧布尔状态机，实际替换成 `_stripped = text.splitlines()`，即彻底关闭围栏排除。4/3/4 冲突案仍会按预期报 999；真正变红的是 fenced-seed 合法负控被误拒。
- ❌ survivor-51 已陈旧：[recap_domain_negverify.py:607](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:607) 改回 raw 后，冲突行会被当前非模板门拒绝；R20 变红来自合法强调行 [test_recap_scan_signals.py:4752](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4752) 被误伤，不证明“双行逃逸复活”。
- ⚠️ survivor-53 会复活旧任意缩进缺陷，但同时混入新 padding 性质，不能给列表 1–4 格修复记功；54 能证明父 H2 条件承重，但不专门模拟 `"台账" in heading`；56 对正常 grouped ledger 的角色收窄有效。
- ✅ preflight 现在准确只承诺“唯一文本锚点＋最终字节变化”，并明确不证明行为非空，[recap_domain_negverify.py:815](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:815)。`run_suite` 的五元组注解也已正确，[recap_domain_negverify.py:745](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:745)。

### 崩溃二分

- ⚠️ PARTIAL：[recap_domain_negverify.py:735](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:735) 对本仓当前 `--tb=short` 已观测的三格顶层、四格以上续行样例有效，但不是可靠二分。
- ❌ 具体反例：门把 `E   Failed:` 固定判成 crash，[test_recap_scan_signals.py:4629](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4629)；同一套件却会用 `pytest.fail(...)` 表达真正的契约失败，[test_recap_scan_signals.py:2702](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:2702)。这不是生产崩溃。
- 反向仍会漏：生产代码自身抛 `AssertionError` 会被白名单当正常判错；断言正文偶含 `Traceback`、`N errors` 或三格标识符行又会假阳。源码已在 [recap_domain_negverify.py:684](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:684) 如实承认其启发式性质。

### 收口分类

一次改动内可闭合：

- 列表 padding 必须消费完整空白 run，并补 1–5/7 格、有序列表和嵌套引用矩阵。
- 修正 ATX 的 0–3 格前导、空格/tab 分隔、closing `#` 前必有空白。
- tail 只排除确切否定语境，避免排除“累计/已/共批注”；同时避免 visible 尾巴二次归一。
- grouped ledger 的 `seeds` 缺失/坏形状直接 fail-closed。
- tips、③标题、H2 标题计数改到同一可见文本面。
- R23 参数化、改名或补真实 CLI；修正“九种”及 mutants 51/55 的目标与期望方向。

需要重做设计：

- 用真实 Markdown 块/container 状态取代围栏前缀 regex；列表 continuation、tab 列宽、容器退出及围栏内字面 marker 必须一起建模。
- 用解析器/渲染 token 面取代 `_visible_text` 的封闭替换表。
- 用 pytest report hook、JSON 结果或确定性结构化标记取代人类可读 traceback 文本二分。
- 变异元数据绑定 exact nodeid/参数 case/预期失败方向，并在隔离副本运行，而不是只聚合 `-k` 下“至少一例红”。

验证限制：未运行 `recap_domain_negverify.py`、605 扩大回归或任何探针；未读 fixtures 的 `.md/.json` 正文；未运行 `git diff/show/log -p`。当前会话未提供 Graphiti 与 Sequential Thinking 接口，故无法执行这两项协议。


