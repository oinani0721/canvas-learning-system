BLOCKER/HIGH 清零：否（就计数取值口径而言）

裁定：**0 BLOCKER / 8 HIGH（5 实现 + 3 自证）**。另有 1 个尚未裁决的 E2 inline-code 条件项。

### 实现侧

1. ❌ **HIGH-1（存量未闭）：fallback“先归一再选行”只修了局部数字函数。**

   `_verify_fallback_derive_numbers()` 先归一后，只选择 heading/relation 两类行；生产入口的全文白名单仍在源码行判断 `"派生" in ln`。因此非标题的 `派**生**出 987654 个` 渲染后是派生断言，却既不进入局部数字循环，也绕过源码全文门。[recap_scan.py:2100](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2100) [recap_scan.py:2112](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2112) [recap_scan.py:2289](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2289)

2. ❌ **HIGH-2：两处隐藏的手抄闭表未随主表整改。**

   - `_D2_INLINE_CODE_RE` 手抄的是旧量词表。主 `_D2_QUANT` 已含 `笔`，但将 `笔` 单独写成 code span 时仍会被提前挖空，使前面的数字失去量词锚点。[recap_scan.py:1399](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1399) [recap_scan.py:1422](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1422) [recap_scan.py:1757](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1757)
   - fallback ⑦/⑧仍手抄旧数词禁集，缺 `仨俩`、金融数字等，且这两类行不进入通用 `_NUM_RUN_RE` 循环；如“派生角色成员缺来源锚点共仨个”可匹配允许式却不核数。[recap_scan.py:1311](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1311) [recap_scan.py:1319](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1319)

3. ❌ **HIGH-3（存量，严重度仍被低估）：闭表遗漏仍可零取数、尾片重锚或改符号。**

   - `⑤`、`٥` 等可见数字不在 `_NUMERAL_LIKE_CHARS`：D2 与 fallback 都可完全不抽 token。
   - 表外量词如 `例` 会令 D2 整句零校验。
   - `负五个` 会从 `五` 开始匹配并按 `+5` 入池；两侧符号守卫只认五个列举符号，仍漏中文“负”及其它连字符。[recap_scan.py:1539](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1539) [recap_scan.py:1555](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1555) [recap_scan.py:1862](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1862) [recap_scan.py:2148](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2148)

4. ❌ **HIGH-4：`_visible_text` 明示不是 renderer，仍存在标准渲染结构绕过。**

   当前只处理 inline Markdown link，不处理 reference-style link。`总[计][r]987654个` 渲染显示“总计987654个”，但源码句式门仍失锚；fallback 的 `派[生][r]` 同时绕过局部选择和源码全文门。Obsidian highlight/math 等未列结构同型。[recap_scan.py:1593](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1593) [recap_scan.py:1613](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1613) [recap_scan.py:1633](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1633) [recap_scan.py:1825](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1825)

5. ❌ **HIGH-5：所谓“安全向过度拼接”不是保值关系。**

   `1\*5个` 渲染为可见的 `1*5个`；实现先删 `*`，再将反斜线当连接字符剥掉，最终把 **15** 送入池。池含 15 并不能证明读者看到的表达式或其值 5 有出处。同理，`5多个` 会按精确 5 入池，但读者看到的是近似计数。本轮只审计数取值口径，因此此前的“条件性”在本范围内成立为 HIGH。[recap_scan.py:1356](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1356) [recap_scan.py:1374](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1374) [recap_scan.py:1609](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1609) [recap_scan.py:1637](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1637)

### 自证侧

6. ❌ **HIGH-6：bidi CLI 门仍被纵深遮蔽。**

   输入使用 `98⁦⁩七654个`；即使生产消费点不调用 `_visible_text`，连接层仍会处理 isolate，而混写的 `七654` 本身也足以触发“无法解析”。断言又只要求该类别，不要求归一后的完整 token。因此 helper 断言证明了函数行为，但 CLI 门没证明消费路径依赖它。[test_recap_scan_signals.py:3897](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3897) [test_recap_scan_signals.py:3930](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3930)

   同时，U+2067/U+2068、`’`、`﹣`、新增量词 `封片卷格`均无行为输入门；`轮次`位于字符类中，且两个字符此前已分别存在，并不是新增的“两字量词成员”。

7. ❌ **HIGH-7：34/34 仍不能推出各性质逐项承重。**

   静态复核确认 survivor-15…34 的锚点均指向活代码；未发现语法错误、NameError 或必然崩溃。`survivor-29` 重指有效，`survivor-31` 的内联正则也安全。

   但仍有混因：

   - `survivor-20` 的标签小数点退化被前置 `_visible_text` 剥标签遮蔽，实际只能靠全角逗号分支变红。
   - `survivor-27` 同时删掉冒号支持，可在中文数词性质运行前仅因冒号 case 变红。
   - `19/23/24/25/32` 分别将多个消费点或子性质合并变异，而测试只证明其中一部分。
   - runner 只要求 broad `-k` 中出现任意 failed，不校验失败类别属于目标性质。[recap_domain_negverify.py:272](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:272) [recap_domain_negverify.py:363](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:363) [recap_domain_negverify.py:503](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:503)

8. ❌ **HIGH-8：分类更正已收窄，但轮次与“零回归”措辞仍宽。**

   “四类都没有被证明有限”以及“`_visible_text` 不是 renderer”这两句成立。[UAT:704](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/_bmad-output/验收单/UAT-CARD-维护B-R3-中文数词终态-2026-09-02.md:704)

   但测试注释把 round-8 余下七条都称作“实现 HIGH”，实际应是 **5 实现 + 2 自证**；又写“本轮修完 8 条”，与 round-7 修 1、round-8 修 7 矛盾。[test_recap_scan_signals.py:3870](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3870) [test_recap_scan_signals.py:3873](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3873)

   `10/10` 只能证明列举的十个放行样例通过，套件全绿只能说“已运行套件未发现回归”；不能写成未测行为也“自引回归 0”。因此“一个数据点不足以支持停止”是正确更正，但“本刀零回归”仍需限定证据面。[UAT:641](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/_bmad-output/验收单/UAT-CARD-维护B-R3-中文数词终态-2026-09-02.md:641) [UAT:649](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/_bmad-output/验收单/UAT-CARD-维护B-R3-中文数词终态-2026-09-02.md:649)

### 三表与不变式

| 对象 | 裁定 |
|---|---|
| `_NUMERAL_LIKE_CHARS` | ⚠️ 承认“封闭表”是诚实的；把遗漏登记成 MEDIUM 则低估。遗漏可造成零取数/尾片重锚，是 HIGH 机制。 |
| `_D2_QUANT` | ❌ 同样被低估；任一表外量词可令 D2 零校验，而且 `_D2_INLINE_CODE_RE` 还维护着陈旧副本。 |
| `_CJK_NUM` | ✅ 窄赋值本身安全：已完整定界的表外、多字或混写 token 会得到 `None` 并 fail-closed。风险在“是否完整进入定界/消费点”，不在这张赋值表。 |

“定界要宽、赋值要窄”在两个**局部消费循环**都成立：

- ✅ D2 普通计数和区间端点均走 `_join_free → _count_token_value`，`None`/池外上报。[recap_scan.py:1800](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1800) [recap_scan.py:1858](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1858)
- ✅ 已被选中的 fallback heading/relation 行也走同一判值器。[recap_scan.py:2139](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2139)
- ❌ 端到端不成立：表外字符、量词、渲染结构或源码选择可让 token 根本进不了循环。

另有 **E2 未裁决条件项**：非纯数字/非旧纯量词的 inline-code span 会被整体挖空；其中写入完整可见计数也不入池。源码将其声明为设计豁免，本轮不把它重复计入 8 HIGH，但它仍是问题 1 的肯定答案，不能当作已闭合。[recap_scan.py:1626](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1626)

### 确认通过

- ✅ `~` 只保留成对 `~~` 删除线，ASCII/全角区间与自陈合法区间门均存在。
- ✅ aliased/plain wikilink 已统一进入 `_visible_text`；旧 `_D2_WIKILINK_RE` 已删除。
- ✅ fallback 局部 heading/relation 选择已先归一；两侧已有列举负号守卫。
- ✅ `_CJK_NUM` 期望值独立写死，两个 `{0,1,2}` 合成池门真实覆盖单字自身值与多字 fail-closed。[test_recap_scan_signals.py:3144](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3144) [test_recap_scan_signals.py:3223](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3223) [test_recap_scan_signals.py:3411](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3411)
- ✅ `_one_problem_has` 至少把多数类别与 token 收到同一物理输出行；bidi case 是明确例外。

### 实际执行与限制

- pytest：**260 passed, 14 warnings in 39.44s**，与预期 260 一致，因此未运行 `git status --porcelain`。
- `git rev-parse HEAD`：`6acda2df5f7b01394f3bf3f46cab7a48879c454f`
- 未运行 negverify、探针、临时脚本、其它 pytest，未读取 fixtures 的 `.md/.json` 正文；未运行被禁止的 git 命令。
- 当前会话未暴露 `graphiti-canvas`，其强制检索为 **UNVERIFIABLE**。
- 本报告不构成对“最多三轮”超限的用户追认，也不构成合并授权。


