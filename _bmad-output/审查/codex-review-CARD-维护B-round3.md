BLOCKER/HIGH 清零：否

终裁：**FAIL · BLOCKER 2 / HIGH 4 / MEDIUM 3 / LOW 1**。目标套件的 240 项全绿属实，但生产 verifier 仍有可复现的渲染语义分叉。

## Findings

1. **BLOCKER — 列表修复跨 sibling 列表项延续围栏，令可见伪计数 VERIFY PASS**

   [recap_scan.py:998](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:998) 剥掉每行的无序列表标记，[recap_scan.py:999](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:999) 至 1017 却不跟踪列表容器边界；D2 又在 [recap_scan.py:1449](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1449) 信任该结果。

   单变量复现：普通写入“本板共有 987654 个子节点”时 rc=1；仅把它放在两个同级空代码块列表项之间后，当前生产 verifier 变为 **rc=0 / VERIFY PASS**。CommonMark 渲染为三个 sibling `<li>`，中间伪计数是可见正文。新门却将其误认成代码内容并剥除。测试在 [test_recap_scan_signals.py:2385](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:2385) 和 [test_recap_scan_signals.py:2404](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:2404) 锁定了错误容器语义。

   **判词：FAIL；`fd7e1acc` 引入直接治理绕过。**

2. **BLOCKER — 只识别一次无序列表标记，有序/嵌套列表中的真实围栏仍漏识别**

   [recap_scan.py:998](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:998) 仅支持一次 `[-*+]`，不支持有序列表、第二层列表或 list→quote 容器。动态核对中，这些结构经 CommonMark 渲染后四条信号均在 `<code>` 内，但 [recap_scan.py:1035](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1035) 仍保留标签，[recap_scan.py:1060](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1060) 将四条都当作在场标准行，信号校验无问题。

   **判词：FAIL；UAT [line 167](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/_bmad-output/验收单/UAT-CARD-维护B-数字治理域-2026-08-31.md:167) 的 “E1 CommonMark CLOSED” 不成立。**

3. **HIGH — EOF 未闭合围栏的最后一条伪信号逃过二次信号检查**

   `_strip_code_blocks` 在 [recap_scan.py:1019](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1019) 重新 join 空行；[recap_scan.py:1040](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1040) 随后对两侧 `splitlines()` 使用 `zip`。终端空行被丢失，较短一侧令最后原文行不参与比较。

   四条正确信号后追加未闭合围栏，并把伪来源覆盖率放在 EOF 最后一行：原文 7 行、剥离结果 6 行，隐藏标签未进入 `stripped_only`，信号校验仍无问题。

   **判词：FAIL。**

4. **HIGH — `_FALLBACK_DERIVE_ALLOW` #3/#4 全文放行，但信号绑定只检查③段**

   信号范围仅在 [recap_scan.py:1049](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1049) 至 1060；#3/#4 允许式位于 [recap_scan.py:1222](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1222) 至 1230，却在 [recap_scan.py:1835](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1835) 对全文使用。

   在正确③段后追加附录伪信号或与③段矛盾的“无据”信号，两例均命中允许式，信号与 D2 检查均无问题。

   **判词：FAIL；可见重复/矛盾信号未绑定。**

5. **HIGH — ⑦/⑧ 只禁 ASCII 尾数，且前置数值完全未绑定**

   [recap_scan.py:1244](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1244) 和 [recap_scan.py:1250](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1250) 的 `[^0-9]*` 放行全角数字与中文数字；⑦自身还允许任意 `N 个派生角色成员缺来源锚点`，却不与 scan equality 绑定。D2 在 [recap_scan.py:1518](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1518) 因句子没有板级 claim 直接跳过。

   全角 `９８７６５４`、中文“九十八万”以及任意 ASCII 前置 N 均已复现放行。新门 [test_recap_scan_signals.py:2632](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:2632) 只覆盖 ASCII 自由尾段。

   **判词：FAIL；UAT [line 207](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/_bmad-output/验收单/UAT-CARD-维护B-数字治理域-2026-08-31.md:207) 的“尾段禁裸数字”比实现宽。**

6. **HIGH — 允许表的“依据”只是元数据，不是值绑定**

   [recap_scan.py:1197](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1197) 声称逐条有据，但：

   - #2 允许任意含“派生”的 Markdown 标题；D2 在 [recap_scan.py:1453](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1453) 把标题仅作为分段边界，不检查标题文字中的计数。
   - #5 在 [recap_scan.py:1233](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1233) 标注 `scan:counts.relation_types`，但没有把报告里的关系类型数字与该字段全等绑定。

   `test_domain_derive_allow_entries_are_grounded` 在 [test_recap_scan_signals.py:2589](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:2589) 只验证路径存在、模式匹配正例且不命中固定反例，不验证报告值。

   **判词：FAIL；“有依据”不能成立为数据承重。**

7. **MEDIUM — UAT 的“最终态”索引、摘录及轮次状态已漂移**

   - UAT [line 116](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/_bmad-output/验收单/UAT-CARD-维护B-数字治理域-2026-08-31.md:116) 仍写 survivor-7 `4/4`；终态为 [negverify-final.txt:9](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/_bmad-output/审查/evidence-maintb-r2/negverify-final.txt:9) 的 `5/5`。
   - UAT [line 257](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/_bmad-output/验收单/UAT-CARD-维护B-数字治理域-2026-08-31.md:257) 指向 [judge1-final.txt:61](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/_bmad-output/审查/evidence-maintb-r2/judge1-final.txt:61)，该文件是 239；240 在 [judge1-final2.txt:61](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/_bmad-output/审查/evidence-maintb-r2/judge1-final2.txt:61)。
   - UAT [line 256](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/_bmad-output/验收单/UAT-CARD-维护B-数字治理域-2026-08-31.md:256) 仍指 pre-fix replay；列表门在 [replay-after-result2.txt:3](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/_bmad-output/审查/evidence-maintb-r2/replay-after-result2.txt:3)。
   - 自述所称 `f-collect-final2.txt` 不存在；现有 before/final 虽逐字相同，但 final 入库早于 `fd7e1acc`。
   - [UAT:224](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/_bmad-output/验收单/UAT-CARD-维护B-数字治理域-2026-08-31.md:224) 和 [UAT:228](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/_bmad-output/验收单/UAT-CARD-维护B-数字治理域-2026-08-31.md:228) 仍等待已终止的 round-2，而非当前 round-3。

   **判词：PARTIAL；核心数字有证据，但终态追溯链不可照单复核。**

8. **MEDIUM — “每个信号数字逐一改错”是穷尽性过称**

   UAT [line 36](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/_bmad-output/验收单/UAT-CARD-维护B-数字治理域-2026-08-31.md:36) 称每个数字逐一改错；实际 [test_recap_scan_signals.py:2859](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:2859) 只改六个代表字段：三个 percentile 只改一个，coverage/duplicate 只改 numerator。测试 docstring [line 2886](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:2886) 本身也只称“六条各打一个信号字段”。

   **判词：应改为“六种代表性字段篡改全部打回”。**

9. **MEDIUM — 两个未修 round-1 MEDIUM 被单方降为 LOW**

   UAT [lines 177–178](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/_bmad-output/验收单/UAT-CARD-维护B-数字治理域-2026-08-31.md:177) 降级，但风险原样存在：

   - [recap_domain_negverify.py:190](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:190) 仍在恢复 `try/finally` 之前写目标文件。
   - live 哈希门仍在 [test_recap_scan_signals.py:1757](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:1757) 至 1766 固定 `checked == 8`，不会发现新增第五份 live 报告。

   **判词：STILL-OPEN / MEDIUM；无用户裁决不能自行降级。**

10. **LOW — 负验证及 UAT 的承重措辞略宽**

   [recap_domain_negverify.py:67](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:67) 称 survivor-4“恢复字符黑名单”，实际替换仅开放尾部槽；它只证明开放槽会红。UAT [line 77](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/_bmad-output/验收单/UAT-CARD-维护B-数字治理域-2026-08-31.md:77) 的“变红的都是指定门”也过强：证据能证明指定门变红，不能证明只有指定门变红。

   **判词：PARTIAL；不影响 10 条指定 mutation 确实有真实失败。**

## 重点声明核对

| 声明 | 复核 |
|---|---|
| “10/10、8/8 全部承重” | ⚠️ 枚举内成立；锚点均精确命中且 keyword 真实收集，但不能推出行为域完整，c 组本身还锁错容器语义。 |
| “本卡未证明什么” | ⚠️ 基本诚实，确实披露不穷尽、D1/D2 边界及 synthetic 非 live；但有效轮次仍误写 round-2。 |
| round-2 截断处置 | ⚠️ stdout 0、无终裁、不算清零、缩小范围重发均如实；后续状态引用未切到 round-3。 |
| D1–D7 待裁决 | ✅ 七项均为 `☐`，明确“未点头即回退”，没有伪装成已授权。 |
| `_SIGNAL_TAIL_NOTES` | ✅ 当前封闭表与 `re.escape` 整行锚成立；表内放行、表外拦截、同步篡改门成对。 |
| 死代码删除 | ✅ `unicodedata`、`_has_numeric`、`_EXTRA_QUANTITY_CHARS` 无残留引用。 |

## 车道自述三条

1. **⚠️** 允许证据确认 **239 passed**；因本轮禁止读取 round-2 stderr，不能独立确认“由 Codex 亲跑”的 provenance。
2. **❌** 先红证据、`fd7e1acc`、新门与 `---` 反向锁均存在，但“列表项围栏已修复”不成立：一种测试形态误建模为代码块，且有序/嵌套容器仍漏。
3. **⚠️** 当前亲跑 **240 passed, 14 warnings, rc=0**；存档支持 572、10/10、8/8。`f-collect-final2.txt` 不存在，故“fd7 后 live 最终收尾对账”证据链不完整。

## 范围与限制

- WT：`card/v2-recapfix`，`HEAD=40699e285c4b…`，base=`0c4afeb7406d…`。
- 给定 range 实际为 **31 个拓扑提交 / 7 个 first-parent**；四个指定文件由 **5 个** CARD-维护B 提交触及，并非“4 commits”。本轮仍以 exact range 和用户指定四类文件为准。
- 未读取任何 `fixtures/` 下 `.md/.json` 正文；未读取 round-1 之外历史审查正文；未修改工作树。两份既有 untracked round-3 文件保持不动。
- 亲跑范围仅为指定目标套件；572、负验证和 replay 使用允许的终态证据，没有冒充全仓 CI。
- 当前会话没有 `graphiti-canvas` 工具，无法执行规定的 Graphiti 搜索。


