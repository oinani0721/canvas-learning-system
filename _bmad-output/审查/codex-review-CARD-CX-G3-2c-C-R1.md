需整改

1. **[HIGH] [docs/learning-events-schema-v1.md:122](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/docs/learning-events-schema-v1.md:122) — 三段防线漏掉 `self_confidence_norm`，可损坏 receipt 身份并阻塞后续正常评分。**

   [quiz-answer/SKILL.md:1320](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1320) 原样读取该字段，`:1408` 直接拼进 YAML，没有类型检查或 `q_()`。我用真实 writer 输入：
   ```python
   self_confidence_norm = '0.5\n    event_id: "quiz:injected"'
   ```
   实测首写 **rc=0、账本=1、attempt=1**，receipt ID 却成为 `quiz:injected`；原样重跑和下一次正常评分均 **rc=1，账本/attempt 仍为 1/1**。

   这是既存写点缺口，本卡新增的完整覆盖声明没有识别它。建议在首次 append 前限定为有限 `[0,1]` 数值或 `None`，并验证新 receipt 与预期字段逐项一致。

2. **[MEDIUM] [validate_learning_events.py:1621](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/scripts/validate_learning_events.py:1621) — “两个字段结构不可达、扩表恒不触发”不能推广到全部写侧。**

   [learning_event_log.py:65](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/app/services/learning_event_log.py:65) 接受任意 payload，`:124` 原样装入记录，`:127` 写盘。实际调用公共 `append_event()`，传入带 NEL 的 `question_id`、`self_confidence_raw`：**返回 True，两个键均落账，完整 validator 的 violations=[]**。仅在内存严格表中加入 `payload.question_id`，立即报 **U+0085**，并非空操作。

   当前业务调用点没有传这些键；因此可以保留“不扩表”的实现选择，但论据应限定为“当前 quiz-answer 不写、恢复 receipt 不读取这些 payload 字段”。E3 只运行指定一致性门，也没有证明其 docstring 所称的“任何行为门都不变”。

3. **[MEDIUM] [test_g3_2_review_ledger.py:6358](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/tests/regression/test_g3_2_review_ledger.py:6358) — “整条逐字节”实际仍是没有结束边界的前缀子串比较。**

   在真实重建路径中，于追加 B 前给 A 末尾增加同值重复键 `abandoned: false`：**完整 emitter 门 PASS，三个 writer rc=[0,0,0]**；最终该键的行数 **3，基线为 2**。原块仍出现一次、仍紧跟 header，载体行也只有一次；生产 `_canon_tree` 同样放行。

   建议分别提取修改前后完整条目的结束边界，以字节直接比较，并补“末尾追加重复键”负控。

4. **[MEDIUM] [test_g3_2_review_ledger.py:6376](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/tests/regression/test_g3_2_review_ledger.py:6376) — `ae53fa05` 换载体后，最后阶段仍无法证明恢复成功。**

   在真实 F1-only 成功出口前插入 `raise SystemExit(...)`，完整 emitter 门仍 **PASS**，writer 实际 **rc=[0,0,1]**。`:6379` 只比较 attempt；直接拒绝自然满足“不增加”。

   建议断言最后一次 **rc=0**，并比较预期不变的完整节点、账本写面。当前载体能杀死 M8，但不能据此宣称恢复成功也被锁住。

5. **[MEDIUM] [test_g3_2_review_ledger.py:5972](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/tests/regression/test_g3_2_review_ledger.py:5972) — 一致性门能从错误提取结果得到绿灯。**

   我运行了三个语法有效的源码变异，完整一致性门均 **PASS**：

   - 加入双引号 f-string 的新 receipt 键：提取器仍报告原 **14 键**。
   - 注释原 `question_id` 行，再用双引号 f-string 改名：仍把注释里的旧键算进去。
   - 实际账本 payload 加入单引号键 `'question_id'`：`:5986` 漏提取，门仍声称它不在 payload。

   此外，严格表改为空 tuple，新门也 **PASS**；完整套件由旧门 `:5939` 补位。所谓两处 payload 中，第一处实际是比较用 `_mine_env`，不是第二个落账写点。

   建议分析唯一执行块的 AST，识别真实赋值与写入对象；对不能证明的动态更新拒绝放行，并直接断言完整严格表。

6. **[MEDIUM] [test_g3_2_review_ledger.py:6122](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/tests/regression/test_g3_2_review_ledger.py:6122) — 时刻门被 `review_time` 检查满足，没有证明 `ts` 检查承重。**

   删除真实 writer 的 `ts` 词法判据后，该门仍 **PASS、账本零行**；实际 stderr 点名 **`payload 缺稳定业务时刻 review_time`**。原因是测试同时污染两个字段，先在 `SKILL.md:266` 退出。

   建议每次只污染一个字段，并核对具体拒因；为声称承重的入口检查分别加入删除判据的负控。

7. **[MEDIUM] [test_g3_2_review_ledger.py:6169](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/tests/regression/test_g3_2_review_ledger.py:6169) — AST 门漏掉海象赋值，不能证明 `record` 不重绑。**

   把 validator 的形状检查改为：
   ```python
   shape = value_shape_problems(record := b"x")
   ```
   完整 nondict 门仍 **PASS**。另以合法记录调用，并用 `sys.settrace` 观察：字符检查实际收到 **bytes**，随后发生 **AttributeError**。

   建议检查当前作用域全部绑定形式，包括 `NamedExpr`；同时验证守卫确实检查 `dict`、立即返回且支配调用点，不能仅比较行号。

8. **[LOW] [g32cb_mutation_gates.py:214](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/scripts/g32cb_mutation_gates.py:214) — 唯一子串命中不证明命中了目标执行语句。**

   副本实测：M8 的生产行由 **20** 个前导空格变为 **21** 个，`--list` 仍 **count=1、rc=0**。将活行改为等价写法、仅在注释保留旧锚，也同样通过；变异前后执行块的 **AST 完全相同**。

   建议绑定执行块内的语句身份。完整 runner 对这种无效变异仍会报 SURVIVED；本次没有证据表明它会假报 `8/8 KILLED`。

9. **[LOW] [test_g3_2_review_ledger.py:5891](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/tests/regression/test_g3_2_review_ledger.py:5891) — `991ae914` 的容器门声称覆盖 tuple，实际没有 tuple 样本。**

   删除字符遍历的 tuple 支持后，相关五道纯门全部 **PASS**，而 `exam_board=("\x85",)` 的字符检查返回 **[]**。

   建议补外层及嵌套 tuple 样本。当前实现本身对 dict 键、dict 值、list、tuple、混合容器均正确拒绝 NEL；多行自由文本放行，自引用先被形状门拒绝，未复现该生产遍历的新故障。

按真实来源重算，14 个 receipt 键的分工如下；行号均指 [quiz-answer/SKILL.md](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1389)：

| receipt 键 | 来源及实际防线 |
|---|---|
| `event_id`、`pred_id` | 本条/前序记录的 `event_id`，源路径已在字符表；再经 `q_()`。`:1377`、`:1389` |
| `exam_board` | 字符轴＋JSON 双编码＋`q_()`。`:1405` |
| `question_id`、`self_confidence_raw` | 当前输入经 `q_()`；foreign replay 固定 null。`:1319`、`:1334` |
| `ts`、`scored_at` | 来源分别为采用后的 `review_time`、原始评分时刻；时刻校验及 `q_()`。`:1312`、`:1331`、`:1393` |
| `attempt_count`、`grade_norm` | 整数/数值构造或校验，直接插值。`:1332`、`:1395`、`:1409` |
| `id_form`、`board_form` | 固定常量，经 `q_()`。`:1391`、`:1396` |
| `fsrs_applied`、`abandoned` | 内部布尔值，输出固定字面量。`:1392`、`:1410` |
| `self_confidence_norm` | **原样读取后裸插值，缺少强制约束。** `:1320`、`:1408` |

所以新措辞的差集仍包含 **`payload.review_time`、`payload.scored_at`、`payload.attempt_count`、`payload.grade_norm`**。它们不必都扩进字符表，但判据必须明确列出时刻、数值和常量约束，不能把分工概括为当前三段。

时刻分工还需区分输入与已有账本：我令 durable `scored_at="2026-08-01\x8510:00:00Z"`，实测 **validator violations=[]，`_TS_RE.fullmatch=False`**；该路径由后续时刻解析和 `q_()` 处理，不能全部归因于入口词法门。

全部物理写侧核查到四处：[quiz-answer:2701](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/canvas-vault/.claude/skills/quiz-answer/SKILL.md:2701)、[start-exam-board:445](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/canvas-vault/.claude/skills/start-exam-board/SKILL.md:445)、[ai-linked-doc:189](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/canvas-vault/.claude/skills/ai-linked-doc/SKILL.md:189)、[append_event:127](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/app/services/learning_event_log.py:127)。前三者当前不写那两个 payload 键；第四者实际可写，已执行验证。

本次独立验证结果：

| 检查 | 观测 |
|---|---|
| `514cff3c` 范围文件基线副本，四回归 | **335 passed, 1 skipped；rc=0** |
| 当前工作区，四回归 | **339 passed, 1 skipped；rc=0** |
| `tests/skills` | **369 passed；rc=0** |
| 隔离副本 `g32cb` / 新负控 | **8/8、5/5 KILLED；均 rc=0** |
| 两脚本当前 `--list` | 每锚 **1 次，rc=0** |
| 源文件完整性 | 五个审查文件及 writer 的 SHA-256 前后全部相同 |
| 两处账本路径存在性 | 两次检查均 **NOFILE** |

审查绑定 **`514cff3c59c85b00c1125cea91238162635e9a45` 加本次工作区内容**。可执行复现保存在 [门负控脚本](/tmp/x7-independent-gate-review.py) 和 [真实写侧复现脚本](/private/tmp/x7-review-writer-boundary-14wekqft/reproduce.py)，均只写临时 fixture。
