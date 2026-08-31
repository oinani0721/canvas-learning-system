# Codex 独立复核存档 — CARD-维护B round-1

> **模型**: `gpt-5.6-sol` · `ultra` · `--sandbox read-only` · 2026-08-31
> **卡**: BATCH-2026-08-31-第七批 / CARD-维护B（board-recap verifier 数字治理域）
>
> ## ⚠️ 存档来源说明（如实）
>
> 本轮 codex 进程在**输出末尾**被其 cyber 过滤器拦截（`ERROR: This content was flagged
> for possible cybersecurity risk`），stdout 落盘为 0 字节。报告正文已从 **stderr 逐字抢救**
> （MEMORY `reference_codex_exec_gotchas` 有载此现象与抢救办法）。
> 下方为抢救所得正文，未做任何删改；末尾 §4 后半被过滤器截断，该部分的两条结论
> 已在正文中出现过（变异脚本 rc 判定 + 恢复顺序），已据其整改。
>
> ## 裁决与处置
>
> **FAIL，不可验收 · BLOCKER 3 / HIGH 5 / MEDIUM 3 / LOW 0**
>
> 这一轮的价值极高——三条 BLOCKER 全部是「**声称做到了、实测没做到**」：
>
> | 条 | 复核者的实证 | 处置 |
> |---|---|---|
> | **BLOCKER-1** E1 仍非 CommonMark | 闭栏后**未要求只有空白**、开栏未限缩进 ⇒ ` ````text` + ` ````not-a-valid-close` 仍 exit 0 | ✅ 修（闭栏须尾随空白 + 缩进≤3 + 反引号围栏 info string 不得含反引号） |
> | **BLOCKER-2** 段名后缀关掉整个 D2 | 别处用宽松段名、D2 用精确标题 ⇒ `## 三维审查（本轮）` + 同一句从 exit 1 变 exit 0 | ✅ 修（D2 改用同一套宽松段名口径） |
> | **BLOCKER-3** 种子绑值门在真实语料上**完全不生效** | 真 manifest 台账行带后续字段 ⇒ 正则不匹配 ⇒ 直接跳过 ⇒ 把「批注 2 条」改 999 仍 exit 0 | ✅ 修（数字后允许 SKILL 明确允许的后续字段）+ 补真实报告篡改门 |
>
> ⛔ BLOCKER-3 是本轮最重要的一条：我的放行门只证明了「真报告 PASS」，
> **没有证明「真报告被篡改后 FAIL」**——正例过了就以为门在工作，是假绿的经典形态。
>
> 其余处置：
> - HIGH 数值池被字符串污染（`544` 只来自 SHA、`111` 只来自用户原话）⇒ ✅ 改为只收数值型；
> - HIGH 范围表达 `2~3 个` 误伤，且**合法与否取决于另一块板的偶然数字** ⇒ ✅ 加 E7 结构豁免；
> - HIGH 变异脚本把 `rc != 0` 当成功（`-k` 写错 rc=5 也算「变红」）⇒ ✅ 改为解析真实 passed/failed；
> - HIGH survivor：砍掉 `_D2_SECTIONS` 一半仍全绿 ⇒ ✅ 两段各配拦截门；
> - HIGH D1 仍是少量枚举（规模 callout 的「1 次调用」、派生行、AI 段其余数字、附录段、
>   frontmatter 非绑定键、HTML 注释均可过）⇒ ⛔ **未修**，如实登记为未完成（验收单裁决点）；
> - HIGH `口径一致` 未兑现 + **我的代码注释与实测冲突** ⇒ ✅ 注释已改；行为仍 FAIL，列裁决点；
> - MEDIUM live fixture 的 4 份 scan **都没有 signals 键** ⇒ 它们证明不了固定尾部无误伤 ⇒ 如实登记。
>
> 整改后 **未再跑 round-2**（时间边界），故**不宣称已清零**——见验收单 §五。

---

裁决：**FAIL，不可验收。BLOCKER 3 / HIGH 5 / MEDIUM 3 / LOW 0。必须再开一轮。**

复核对象为 WT `card/v2-recapfix`、HEAD `3b637af3488e…`。全程只读；探针与 mutation 均在系统临时副本运行。当前 untracked 的 UAT、fixture 和变异脚本也已纳入。

## 1. 治理域：FAIL

### BLOCKER-1 — E1 仍未正确实现 CommonMark

[recap_scan.py:1002](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1002) 的闭栏判断只检查字符和长度，未要求：

- 闭栏后只能有空白；
- 缩进最多三格。

实测输入：

~~~text
````text
````not-a-valid-close
> - 四条合法信号行……
~~~

生产 `--verify`：**exit 0 / VERIFY PASS**。  
`markdown-it` CommonMark 渲染：四条信号实际都位于 `<pre><code>` 内。把伪闭栏换成四空格缩进的 ````，同样 exit 0。

因此卡文所称 E1 CommonMark 闭合仍不成立。现有测试只锁了“短闭栏”这一种情况：[test_recap_scan_signals.py:1575](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:1575)。

### BLOCKER-2 — 合法段名后缀可关闭整个 D2

统一段名口径允许 `## 三维审查（本轮）`：[recap_scan.py:1150](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1150)、[1473](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1473)。  
但 D2 仍只定位精确标题：[recap_scan.py:1236](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1236)。

单变量对照：

- `## 三维审查` + `987654 个子节点` → exit 1
- `## 三维审查（本轮）` + 同一句 → **exit 0**

这是 round-6“存在性与下游定位口径不一致”的同型复发。

### BLOCKER-3 — 新增种子绑值门不覆盖真实 manifest 行

绑定正则要求数字后直接行尾：[recap_scan.py:1177](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1177)，不匹配就直接跳过：[1287](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1287)。

真实报告行带后续字段，例如 [CS 61B fixture:39](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/fixtures/recap_live_reports/回顾-CS 61B-2026-08-27.md:39>)：

```text
- cs-61b-csm — 批注 2 条；未派生……· mastery 0.3……
```

将 `2` 改成 `999` 后，生产 verifier **exit 0**。SKILL 明确允许 manifest 行追加字段：[SKILL.md:243](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/SKILL.md:243)。新增测试只覆盖简化 fallback 行：[test_recap_scan_signals.py:1618](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:1618)。

### HIGH — D1 仍只是少量枚举，不是卡文声明的整域绑定

卡文要求整个固定模板域逐对象绑定：[卡文:38](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/_bmad-output/implementation-artifacts/goal-cards/2026-08-29-维护卡B-board-recap-verifier收紧.md:38>)。下列均实测 **exit 0**：

- 规模 callout：`manifest（1 次调用）` 改为 `999 次调用`；实现只查五元组，[recap_scan.py:1358](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1358)。
- 台账派生行：`tips 未闭环 0 条` 改为 `987654 条`；没有派生行 binder。
- AI 侧对账：`待定纠错候选 0 条` 改为 `987654 条`，或加入 `| 隐藏成员 | 987654 个 |`；实现只绑 tips 两式，[recap_scan.py:1403](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1403)。
- `## 本段新增` 或额外 `## 附录` 写 `987654 个隐藏节点`，均通过。脚注移到附录同样通过。
- frontmatter 非绑定键 `review_count: 999` 通过；这在早期草案中像是有意域外，但最终 §零的 D3 表没有写清。
- 闭合 HTML 注释会被隐式剥除并通过，实际相当于未登记的 E7。

D2 表格/callout 中的 `999 个`会被拦；AI 段同样结构不会。说明当前规则仍由“段名＋几个正则”决定，而不是已裁定的结构域。

## 2. 放行门：FAIL

### HIGH — 合法范围表达被误伤

在真实“递归与分治”fixture 的动作段加入：

```text
4. 用 `/node-chat` 从 2~3 个节点中选择一个深入复盘。【推定】
```

生产 verifier **exit 1**，理由是 `3` 不在该 scan 数值池。相同句子在 CS 61B 报告中会通过，因为其 scan 恰好含无关整数 `3`。

根因是 [recap_scan.py:1184](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1184) 只抽取紧邻量词的尾端整数。合法与否因此依赖另一块板的偶然数字，属于明确误伤。

其他真实感语料结果：

- mastery 小数、量表 `1-4`、分位值、百分比：exit 0；
- 行内代码引用用户原话、wikilink 板名含数字：exit 0；
- 普通中文引号中的“999 个”、纯文本板名“Project 999 个例”：exit 1；
- D2 fenced code 与双反引号 code span 中的 `999 个`：exit 1，违反 E1/E2 豁免。对应实现未先剥围栏，且行内正则只认单反引号：[recap_scan.py:1193](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1193)。

### MEDIUM — live fixture 真实，但证据代表性不足

当前 live `outputs/` 确实只有四份回顾；4 报告＋4 scan 与 fixture **8/8 SHA-256 相同**，所以“从更多样本中挑好样本”不成立。

但四份 scan 全都没有 `signals` 键，生产代码会在 [recap_scan.py:1168](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1168) 跳过整块 H3。它们不能证明固定尾部没有误伤。

哈希门还只遍历 fixture，并固定断言 `checked == 8`；未来 live 增加第五份报告不会失败，且非本机直接 skip：[test_recap_scan_signals.py:1724](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:1724)。

## 3. D2 诚实边界：FAIL

代码注释和 UAT 后半段确实承认“只覆盖 ASCII 整数＋六个量词”，见 [recap_scan.py:1230](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1230)、[UAT:142](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/_bmad-output/验收单/UAT-CARD-维护B-数字治理域-2026-08-31.md:142>)。

但以下仍过称：

- 卡文称“每个数字”、包括小数与百分号、任何未绑定数量表述：[卡文:38](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/_bmad-output/implementation-artifacts/goal-cards/2026-08-29-维护卡B-board-recap-verifier收紧.md:38>)、[48](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/_bmad-output/implementation-artifacts/goal-cards/2026-08-29-维护卡B-board-recap-verifier收紧.md:48>)。
- UAT 开头仍称“区域里的每个数字”：[UAT:7](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/_bmad-output/验收单/UAT-CARD-维护B-数字治理域-2026-08-31.md:7>)。
- UAT 自己又承认 AI 段其他数字未纳管：[UAT:149](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/_bmad-output/验收单/UAT-CARD-维护B-数字治理域-2026-08-31.md:149>)。

D2 不算完全虚设：独特的 `987654 个`在精确标题下会失败。但它的数值池从所有 JSON 字符串抽整数：[recap_scan.py:1198](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1198)。实测：

- `111 个子节点`通过；111 只来自用户作答原话；
- `544 个子节点`通过；544 只来自 SHA 字符串；
- CS 61B 数值池有 41 个值，0–30 已覆盖 20 个。

因此它能拦罕见大数，但对常见小数值的“有出处”语义很弱。

## 4. 变异脚本：PARTIAL / HIGH

[recap_domain_negverify.py:33](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:33) 的现有五条变体均真承重：5/5 都使目标 verifier 变为 exit 0，再由对应测试断言失败；不是异常或其他门造成的假红。

但“覆盖该性质全部防线”不成立。另造三条 survivor，完整 **142 项仍全绿**：

| survivor | 完整套件 | 实际退化 |
|---|---:|---|
| 删除闭栏“同字符”条件，仅保留长度，[recap_scan.py:1014](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1014) | 142 passed | 反引号开栏＋波浪号伪闭栏后信号，mutant exit 0 |
| 把逐节点 `tips_by_node[node]` 改为取第一个节点值，[recap_scan.py:1297](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1297) | 142 passed | 双种子不同 tips 时可借另一个节点的数字 |
| `_D2_SECTIONS` 只保留三维审查，[recap_scan.py:1183](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1183) | 142 passed | 动作段 `999 个子节点` exit 0 |

第三条我独立重放：`142 passed`，敌对报告 `VERIFY PASS`。

另有 MEDIUM 控制面问题：

- [recap_domain_negverify.py:123](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:123) 把任意非零 pytest 状态当成功；`-k __no_such_test__` 的 rc=5、142 deselected 也会报“如期变红”。
- [recap_domain_negverify.py:116](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:116) 先原地写被测文件，之后才进入恢复 `try/finally`；异常中断仍有残留 mutation 风险。

## 5. 既有回归：PASS

没有发现三处断言文案或 `ledger_seed` 改动掩盖回归：

- 当前尾部相关三组共 8 项：8 passed；
- 从 HEAD 解出的旧实现＋旧断言：同样 8 passed；
- 输入始终 exit 1，只是失败路径由字符黑名单变为整行允许式；
- 动态 ledger renderer 位于 [test_recap_scan_signals.py:671](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:671)。零 tips 对照中动态版本 exit 0，恢复旧硬编码后仅因“报告 2、scan 0”而 exit 1，说明旧 fixture 本身确实无据。

实跑结果：

- 目标套件：**142 passed**
- 扩大套件：**474 passed**
- `ruff check --no-cache`：通过
- `git diff --check`：通过

这些证明改动没有击穿既有覆盖，但不抵消上述生产入口绕过。

## 6. `口径一致`：没有兑现要求

精确信号尾注输入当前仍 **exit 1**；卡文却明确要求必须放行：[卡文:242](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/_bmad-output/implementation-artifacts/goal-cards/2026-08-29-维护卡B-board-recap-verifier收紧.md:242>)。

修掉旧误伤机理、不改变可观察结果，不能算兑现行为要求。代码注释声称误伤已经消失也与实测冲突：[recap_scan.py:1121](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1121)。

我的判断是：**不要开放任意自由尾注**。更稳妥的是保持机器信号行严格，把“口径一致”写在下一条独立叙述行——该形态实测 exit 0。若必须让原始同一行输入 PASS，则应定义有限、结构化的注记槽；不能交给当前只覆盖六量词的 D2。

在用户正式修改 goal 前，此项仍是 **HIGH / 未完成**。

限制：未跑全仓 CI，只跑了上述 142/474 项；当前会话没有 `graphiti-canvas` MCP，无法执行仓库要求的 Graphiti 搜索。两项均不影响这些本地生产入口反例。工作树最终状态与审计前范围一致，负验证锁已清除。


ERROR: This content was flagged for possible cybersecurity risk. If this seems wrong, try rephrasing your request. To get authorized for security work, join the Trusted Access for Cyber program: https://chatgpt.com/cyber
tokens used
240,342
