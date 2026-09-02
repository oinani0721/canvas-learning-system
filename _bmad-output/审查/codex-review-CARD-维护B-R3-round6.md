BLOCKER/HIGH 清零：否（就计数取值口径而言）

裁定：**0 BLOCKER / 8 HIGH（6 实现 + 2 自证）**。另有 1 条条件性语义 HIGH，以及 inline-code 的待裁决豁免。

### 实现侧

1. ❌ **HIGH-1：ASCII `~` 在区间终核前被删除。**

   `_visible_text()` 无条件删除 `~`，而 `_D2_RANGE_RE` 后运行，故 `9~5个` 会先变为 `95个`，按 95 入池；fallback 同样如此。range 表中的 `~` 分支实际失效。[recap_scan.py:1559](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1559) [recap_scan.py:1594](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1594) [recap_scan.py:1790](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1790) [recap_scan.py:2112](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2112)

2. ❌ **HIGH-2：D2 的 aliased wikilink 在归一前已被破坏。**

   D2 先把 `[[目标` 挖空，才调用 `_visible_text()`；`[[x|987654]]个` 会留下 `|987654]]个`，量词锚失效。单测直接调用 `_visible_text("[[A|五]]")` 虽绿，却没有覆盖生产顺序；CLI 只测了无别名链接。[recap_scan.py:1429](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1429) [recap_scan.py:1735](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1735) [test_recap_scan_signals.py:3987](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3987) [test_recap_scan_signals.py:4029](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4029)

3. ❌ **HIGH-3：fallback 也没有在“最前面”归一。**

   它先在源码行上判断是否含连续“派生”、选择 heading/relation 行，之后才 `_visible_text()`。因此 `#### 派**生**子女 987654 个` 渲染后是明确计数，但既不进入数字绑定，也不触发全文模板外 deny。[recap_scan.py:1284](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1284) [recap_scan.py:2082](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2082) [recap_scan.py:2257](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2257)

4. ❌ **HIGH-4：负数只修了 D2，fallback 仍按正幅值入池。**

   D2 有 `-−－‑` 守卫；fallback 直接 `_NUM_RUN_RE → _count_token_value → pool`，`-5` 会按 5。D2 的符号表自身也漏 `﹣` 等变体。R9 负数门只走 `d2()`。[recap_scan.py:1836](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1836) [recap_scan.py:2120](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2120) [test_recap_scan_signals.py:4038](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4038)

5. ❌ **HIGH-5：`_visible_text()` 尚未形成“读者文本”闭包。**

   它不处理标准 Markdown link；例如裸 `总[计](u)987654个` 渲染后是自陈句，源码句式门却失锚。不可见表也漏 U+2066–U+2069 bidi isolates，且全局禁用使用同一窄表。[recap_scan.py:1590](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1590) [recap_scan.py:1803](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1803) [recap_scan.py:1367](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1367) [recap_scan.py:2177](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2177)

6. ❌ **HIGH-6（存量）：闭表存在虽有登记，但严重性被低估。**

   - `_NUMERAL_LIKE_CHARS` 漏 `仨/俩`、其它 Unicode numeral，可零命中或尾片重锚。
   - `_D2_QUANT` 漏一个自然量词（如“笔”）即可让整句零校验。
   - 千分位只认 `,，`；`1'005个` 在 D2 可按尾片 5，fallback 可分取 1/5。
   - `_CJK_NUM` 的窄赋值本身是安全向的：只要定界先抓全，表外 token 会 `None → FAIL`。危险的是定界或量词根本没抓到。

   这与此前 `廿五`、`九兆五`、漏“层”被判 HIGH 是同机制，不应登记为 MEDIUM。[recap_scan.py:1397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1397) [recap_scan.py:1536](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1536) [recap_scan.py:1623](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1623) [UAT:530](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/_bmad-output/验收单/UAT-CARD-维护B-R3-中文数词终态-2026-09-02.md:530)

### 自证侧

7. ❌ **HIGH-7：`29/29 红` 不能证明 29 项性质逐项承重。**

   没发现 survivor-15…29 中另一条“整条完全 no-op”，但发现：

   - survivor-20 是部分同型空变异：标签已被 `_visible_text()` 先剥，收窄 `_DECIMAL_SEP` 禁不掉“标签包小数点”；它可靠全角逗号等另一子项变红。
   - survivor-14 把 `_join_free` 变恒等后，完整 token 仍被抓到并因 `None` fail-closed；可能靠误拒或诊断变化变红，没有重开尾片碰池。
   - survivor-19/20 是复合变异；24/25/29 也只覆盖部分路径。
   - runner 只要求 broad `-k` 集合中“至少一个测试失败”，不绑定预期用例、失败类别或每项子性质。

   [recap_domain_negverify.py:199](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:199) [recap_domain_negverify.py:272](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:272) [recap_domain_negverify.py:451](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:451)

8. ❌ **HIGH-8：更正后的分类和新门措辞仍比证据宽。**

   `3/10` 作为这十例的实测比例成立；但“源码≠渲染有限且一次收敛”“判据正则可穷尽”“负数已全部落地”“只有封闭表不可清零”均不成立。源码甚至仍保留已被证伪的“前五轮每条 finding 都是源码≠渲染”断言，紧接着又承认自己不是完整 renderer。[假设检验:34](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/_bmad-output/审查/evidence-maintb-r3/o-round6-hypothesis-test.txt:34) [recap_scan.py:1581](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1581) [UAT:669](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/_bmad-output/验收单/UAT-CARD-维护B-R3-中文数词终态-2026-09-02.md:669)

   新门也只输入 `～`、量词“门”、ASCII `-`；合法 `2~3` 又是非自陈句，无法证明生产 `~` range 分支仍活。[test_recap_scan_signals.py:3978](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3978) [test_recap_scan_signals.py:4034](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4034) [test_recap_scan_signals.py:4063](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4063)

### 四问直答

1. **有**：上述 `~` 拼接、aliased wikilink、fallback raw selector、fallback sign、Markdown link/bidi、表外 numeral/量词/分隔符均能造成错值或零校验。

2. 三表登记为 **PARTIAL**：承认“封闭”是诚实的；`_NUMERAL_LIKE_CHARS`、`_D2_QUANT` 的安全后果被低估，且 UAT 仍把已纳入定界的壹貳/廿卅写成“整域免检”；`_CJK_NUM` 的窄赋值则不应与前两者混成同一种风险。[UAT:558](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/_bmad-output/验收单/UAT-CARD-维护B-R3-中文数词终态-2026-09-02.md:558)

3. “定界宽、赋值窄”在两个最终循环的**局部接线**成立：都复用 `_count_token_value()`；端到端 **FAIL**，因为进入循环前已有错误拼接、源码筛选、符号遗漏和结构破坏。[recap_scan.py:1644](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1644)

4. **有空洞/过宽门**：alias helper-only、合法 `~` 非自陈、负数仅 D2、闭表新增字符只测一个代表、mutation 只看任一失败。

### 确认通过的部分

- ✅ 实体先解码、再转全角的顺序正确。[recap_scan.py:1614](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1614)
- ✅ 三个旧死常量已删除；D2/fallback 的最终取值器已统一。
- ✅ 对已识别且未被 `~` 预处理破坏的区间，当前实现确实在句式门后逐端点上报；车道对 #9b 的事实驳回成立。[recap_scan.py:1775](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1775) [recap_scan.py:1805](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1805)
- ⚠️ `_one_problem_has` 已把类别与 token 收到同一 stdout 行，但双端门仍不要求两条不同 problem 或精确 token 边界，故只算 PARTIAL。[test_recap_scan_signals.py:3640](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3640)

### 实际执行与限制

- pytest：**259 passed, 14 warnings in 67.12s**。首次在只读沙箱因无可用临时目录、收集前失败；获准在沙箱外重跑同一命令后得到该结果。计数为 259，故未运行 `git status`。
- `git rev-parse HEAD`：`33ed0da748a92c8d26ca6c766a7b15954439b254`
- 未运行 negverify、探针、临时脚本或其它 pytest；未读取 fixtures 正文；未执行被禁止的 git 命令。
- 当前会话未暴露 `graphiti-canvas`，因此 Graphiti 检索为 **UNVERIFIABLE**。
- round-6 已超“三轮”上限；本报告不构成合并授权或用户追认。若 E2 inline-code 豁免尚未被用户正式接受，round-5 的该项也仍是开放裁决点。
- 条件性语义项：`[多余来几约近超]` 被当噪声，`5多个` 可按精确 5 入池。[recap_scan.py:1356](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1356) 若治理对象包含整句计数语义，应再计 1 HIGH；否则必须明确登记为范围外，不能称其天然安全。


