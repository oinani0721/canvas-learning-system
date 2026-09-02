BLOCKER/HIGH 清零：否

### 核心结论

❌ **BLOCKER｜本轮引入：H3 改用 `_SECTION_RE` 后并未端到端 fail-closed。**  
[`recap_scan.py:2177-2202`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2177) 用 `_SECTION_RE("### 种子")` 定位，但没有 section 时直接 `return`；全局必需段列表只有 H2，没有 `### 种子`（[`recap_scan.py:825-832`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:825)）。

静态可达反例：保留原有正确台账，再追加 `## 台账 ###`、`### 种子 ###`、`- SeedA — 批注 999 条`：

- 全局门只数原正确 `## 台账`，不把追加的闭合 ATX 算重复；
- seed 扫描见到追加 H2 后把 `_under_ledger` 置为 `False`；
- fallback 形状门只检查首个 exact `### 种子`；
- D2 对该行因不是“本板共有/总计”句式而跳过。

因此 fallback 与 manifest 都存在“用户看到 999、校验器不绑定”的路径。该反例按用户限制未执行，仅由控制流逐步复算。

❌ **HIGH｜共用同一个 regex，仍未共用同一个输入空间。**  
全局门在 raw 整文件上直接搜索（[`recap_scan.py:2617-2622`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2617)），seed 定位却跳过围栏（[`recap_scan.py:2161-2188`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2161)）。所以围栏内 `## 台账` 会被必需段门算“在场”，却不会打开 seed section。正文检查也没有切掉 frontmatter；YAML 中的 `## 台账` 注释同样可能冒充正文标题（[`recap_scan.py:2571-2604`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2571)）。

### 四组处置判断

- ❌ **共用 `_SECTION_RE`：只对 H2 窄例正确，整体未闭合。** H3 没有存在性/唯一性门；`_SECTION_RE` 的 `（[^\n]*$` 还会吞下括号后的任意尾巴，所以“不接受所有 ATX 闭合井号”这句本身也过宽（[`recap_scan.py:1257-1265`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1257)）。

- ✅/⚠️ **终点增加围栏判断：对本次窄反例正确。** `not _in_fence[_j]` 确实阻止了顶层三反引号内的 `## 假标题` 提前截断（[`recap_scan.py:2190-2197`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2190)；行为门 [`test_recap_scan_signals.py:5107-5109`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:5107)）。但它继承了不完整 fence map：quote/list continuation 未建模（[`recap_scan.py:1040-1045`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1040)）。

- ❌ **R25 行为门：没有字面恒真断言，但存在目标无关假绿。** [`test_recap_scan_signals.py:5111-5116`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:5111) 明确把 closed H3 的“静默不检查”编码成 `[]`。唯一 CLI 门只缩进 H2、只断言非零（[`test_recap_scan_signals.py:5118-5127`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:5118)）；该报告是 fallback，缩进后的标题还会被独立的“模板外派生”门拒绝（[`recap_scan.py:2689-2703`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2689)）。即使删除必需段门，这条断言仍可能变红。

- ⚠️ **崩溃识别：不是可靠二分。** 当前实现已不要求冒号，而是匹配 `E` 后 1–3 格及标识符（[`recap_domain_negverify.py:763-785`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:763)）。当前合成样例能区分三格异常与四格以上续行，但仍会：

  - 把三格 `Expected:` 等断言续行误报为崩溃；
  - 把生产代码抛出的 `AssertionError` 当普通门红；
  - 漏掉无 traceback 的子进程 `SyntaxError`、致命信号；
  - 因正文偶含 traceback 或 `1 error` 而假阳。

  源码已在 [`recap_domain_negverify.py:727-733`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:727) 如实降级为 heuristic，这一登记成立。

### 仍在使用自造 section 口径

❌ **HIGH｜D2 有可利用的豁免分叉。**  
[`recap_scan.py:1919-1935`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1919)：

- 把非 Markdown 标题 `##数据来源与新鲜度` 当 H2；
- 接受 `## 数据来源与新鲜度 extra` 为豁免段；
- 其口径允许 ASCII `(` 和任意空白后缀，并不等于 `_SECTION_RE`；
- `text[h.end():]` 丢掉 H2 标题行本身，因此 `## 本板共有 999 个子节点` 不受 D2 检查。

其他副本还包括 ③段三套定位（[`recap_scan.py:1141-1143`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1141)、[`2442-2445`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2442)、[`2635-2641`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2635)）以及 fallback seed 首段定位（[`2662-2683`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2662)）。

### 小节终点剩余问题

⚠️ **延后终止：** [`recap_scan.py:2193-2195`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2193) 要求井号后存在空白，合法空 ATX `##`/`###` 不终止；1–3 格缩进、Setext 标题也不识别。

❌ **提前终止：** 结构判断用的是先经 `_visible_text` 处理的行（[`recap_scan.py:2145-2146`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2145)）。`**## 假标题**`、`<b></b>## 假标题`、`&#35;&#35; 假标题` 原本不是 ATX 标题，却会被合成为标题并截段。

“未改三处”若指表中的围栏容器、`(?<!未)批注` 数字域和窄 ATX 口径：✅ 源码确认三者都仍在；但“窄 ATX 会由全局门兜底”的判断对 H3 不成立。

### 变异脚本源码复核

- ✅ #59/#60 的替换静态上分别改变 H2 定位和移除终点 fence guard，确实能打红各自的窄 R25 断言（[`recap_domain_negverify.py:690-707`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:690)）。但 #59 没覆盖 H3，名称“段落标题口径”偏宽。

- ❌ #51 把 visible 行退成 raw 后，恶意行仍会被非模板 fail-closed 门拦；实际变红来自合法渲染等价行被误拒，不证明“冲突行逃逸”（[`recap_domain_negverify.py:607-614`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:607)）。

- ❌ #55 不是退回布尔翻转，而是令所有 `_in_fence` 为 false；红来自 fenced-seed 误伤（[`recap_domain_negverify.py:647-654`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:647)）。

- ❌ #56 把 `seeds` 强制设为 `None`，生产随即报“缺 seeds”并返回，完全没有“摊平全部角色”（[`recap_domain_negverify.py:657-664`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:657)）。

- ⚠️ #4、#19、#20、#23、#27、#32、#48 都存在名称超出替换范围或一次改变多个性质的问题。尤其 #48 清空共享 range 表，会同时改 code-span 与区间主正则。

根因是 runner 只要求同一 `-k` 集合中 `f > 0`（[`recap_domain_negverify.py:951-972`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:951)），不验证具体 assertion/nodeid。因此自报 `60/60` 不能逐条证明 mutant 名称中的每个性质承重。

### 其他存量未闭合

一次改动内可闭合：

- H3 缺失/重复显式报错，不再 `sections == []` 静默返回；补 fallback 与 manifest 的视觉同名 near-miss E2E 门。
- 全局必需段只检查 frontmatter 后、围栏外的正文。
- R25 CLI 门断言具体 `缺段落` 诊断、`returncode == 1` 且无 traceback。
- tips 两数改用 visible 文本；当前仍 raw（[`recap_scan.py:2405-2420`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2405)）。
- 围栏内信号 label 禁令先做 visible 归一；当前 raw label 可被 `**`/HTML 切开（[`recap_scan.py:1130-1136`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1130)）。
- 修正 mutant #51/#55/#56，并把多性质测试拆成独立关键字。

需要重做设计：

- 用统一的 CommonMark/Obsidian block tokenizer 处理 frontmatter、ATX/Setext、quote/list continuation、fence、HTML block；不能再“先做 inline visible 归一，再猜 block 结构”。
- 重新定义 inline/fenced code 是否属于“用户看到的计数”。当前完整 `` `本板共有 999 个子节点` `` 会被整体挖空（[`recap_scan.py:1547-1593`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1547)）。
- 用数值 token/表达式语法替代封闭字符表；Unicode 数字、分数、科学记数、近似数仍可能落到域外或重锚到尾片。
- 变异归因与崩溃判定改用结构化 pytest report/子进程状态，而不是解析人类输出。

### 实际验证

- ✅ `git rev-parse HEAD`：`11a95fdcd87e38b2c0a992bd1969ba9321808219`
- ✅ 指定 pytest 最终完整结果：`275 passed, 14 warnings in 41.56s`，exit 0。
- ⚠️ 首次沙箱运行因无可用临时目录在收集前失败；获准使用系统临时目录后，同一命令因输出会话捕获问题重跑一次才取得完整退出状态。
- 未运行 `recap_domain_negverify.py`，未重跑 60/60 或 607 passed，未构造探针/临时文件，未读 fixtures 的 `.md/.json` 正文，未运行 `git diff`、`git show` 或 `git log -p`。
- 因禁止查看差异/历史，本次只能判断当前三份文件的行为与注释，无法证明提交级别是否还有其他越界改动。一个并行只读车道额外读取过 `git status --short` 的文件名；该结果未用于上述结论。


