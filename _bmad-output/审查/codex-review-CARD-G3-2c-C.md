需整改

审查绑定最终稳定快照：HEAD `3dfdd69d3b5e528efd6a471ed5297c8c50d534a3`；四文件 blob 依次为 `9cd2dc6`、`f56d5e0`、`8b40c6e`、`adb5cc2`。审查期间工作树被外部更新，最终真实文件已变成 7 道 `g32cc` 门、23 个区间项（含 66 个 noncharacter），不是最初描述的六门/五段；以下结论均已在最终版本重跑。

[BLOCKER] [docs/learning-events-schema-v1.md:118](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/docs/learning-events-schema-v1.md:118)、[docs/learning-events-schema-v1.md:128](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/docs/learning-events-schema-v1.md:128)、[validate_learning_events.py:1664](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/scripts/validate_learning_events.py:1664) — 全体 v1 字符串契约未覆盖所有真实写点，合法多行批注可先进入账本，再阻断下一次评分。

观测：真实 `tips.py:595-602 → learning_event_log.py:116-127` 写入 `callout_ingested.payload.text="第一行\n第二行"`，得到 `append_event=True`、账本 1 行；CLI `rc=1` 且报 `U+000A`；随后同节点真实 quiz writer `rc=1`、同样报 `U+000A`，账本行数 `1→1`，新评分没有记录。另有 `start-exam-board/SKILL.md:437-449`、`ai-linked-doc/SKILL.md:189` 直接追加；全仓只有 quiz-answer 调用 `validate_record_full()`。文档第 128 行把 quiz payload 的 `callout` 字段与独立的 `callout_ingested.payload.text` 混为一谈。

建议：把字符策略改成字段级规则——身份、路径、receipt 载体保持严格；JSONL 自由文本允许转义后的 LF/TAB。所有 producer 必须经同一个 append 前校验入口，并新增“多行 callout 写入后仍能追加 quiz score”的跨 producer 门。

[BLOCKER] [test_g3_2_review_ledger.py:5875](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/tests/regression/test_g3_2_review_ledger.py:5875)、[learning-events-schema-v1.md:356](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/docs/learning-events-schema-v1.md:356) — markerless 歧义只处理“旧字符串→本次浮点”，反方向会把不同事实静默当成幂等。

观测：先用浮点 `exam_board=1e300` 首写，`rc=0`；把 receipt 改成 markerless 裸 `exam_board: 1e+300` 并删除 ledger 行，再以同 ID、字符串板名 `"1e+300"` 重跑。实际 `retry rc=0`、ledger 仍不存在、`attempt_count 1→1`、节点写面不变，stdout 明确为“receipt 事实一致……幂等跳过”。原因是现有比较先发现两个 PyYAML 字符串相等，歧义分支根本不会执行。

建议：markerless 且值可被 JSON 解释成另一类型时，应在“相等”早返之前判歧义；增加 numeric→string、string→numeric 两个 F1-only 门，必须断言非零 rc、零写且明确提示人工裁决。

[MEDIUM] [learning-events-schema-v1.md:357](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/docs/learning-events-schema-v1.md:357)、[test_g3_2_review_ledger.py:5925](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/tests/regression/test_g3_2_review_ledger.py:5925) — markerless 处置建议声称知道旧值来源，但当前解析已经丢失该信息。

观测：我分别预置裸 `exam_board: 1e+300` 和带引号的 `exam_board: "1e+300"`；两者重跑浮点均 `rc=1`，错误都声称旧条目是“裸 JSON 字面”，且同时包含“不是两次不同评分”和“同一个 event_id 承载了两次不同评分”。现门只查三个关键词。另 [test_g3_2_review_ledger.py:5907](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/tests/regression/test_g3_2_review_ledger.py:5907) 注释写成 PyYAML 返回 float，但第 5915 行及实测均为 `str`。

建议：保留 YAML scalar style，或列出两个候选并要求根据 ledger/原始证据选择：浮点对应 `board_form: "json"` + `exam_board: "1e+300"`；真实字符串对应 `exam_board: "\"1e+300\""`。门应实际应用建议并验证重跑结果，而不只匹配关键词。

[MEDIUM] [test_g3_2_review_ledger.py:5821](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/tests/regression/test_g3_2_review_ledger.py:5821)、[g32cb_mutation_gates.py:113](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/scripts/g32cb_mutation_gates.py:113) — “禁止集闭合”门仍是抽样黑名单，不能证明区间闭合。

观测：

- 隔离变异为“仅枚举当前测试触达的 47 个单点”后，7 道 `g32cc` 加两道反转门仍是 `9 passed`；它同时漏放 `U+0000`、`U+0002`、`U+DFFF`、`U+FDD1`。
- 仓库自带 M1–M7 实测 `7/7 KILLED`，但 M7 只杀掉它定义的粗枚举，杀不掉上述完整样例枚举。
- 整个 `value_charset_problems()` 改成恒返回 `[]` 后，7 道新门为 `3 failed, 4 passed`；仍绿的是 normal-text、depth、markerless、emitter 四门。
- 删除 dict 键与 list/tuple 遍历后，7 道门仍 `7 passed`。

建议：用独立期望表遍历全部 2,181 个禁止码点及全部边界邻点；另补嵌套 dict 键、dict 值、list、tuple 四类门。M7 应变异成“枚举全部现有样例”，并要求门将其杀死。

[MEDIUM] [test_g3_2_review_ledger.py:5931](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/tests/regression/test_g3_2_review_ledger.py:5931)、[test_g3_2_review_ledger.py:5954](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/tests/regression/test_g3_2_review_ledger.py:5954)、[test_g3_2_review_ledger.py:5965](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/tests/regression/test_g3_2_review_ledger.py:5965) — 两道反转门移交的“既有条目逐字节不变”性质没有被真正锁住。

观测：该门先经 PyYAML 解析，再用普通 dict `==`，并非字节比较，也非类型敏感。隔离变异让重建把 A 的 `attempt_count` 从 `int 1` 改成 `bool True` 后，观测为 `dict_equal=True`；删账本重跑 `rc=1`、`attempt 2→2`，整道门仍 `1 passed`，因为它没有断言重跑必须成功。全文件也没有其他既有 receipt 字节比较门。

建议：截取 A 条目的原始字节并在追加 B 后逐字节比较；同时断言删除 A 行后的原样重跑 `rc=0`、节点及 ledger 写面不变。

[MEDIUM] [learning-events-schema-v1.md:125](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/docs/learning-events-schema-v1.md:125)、[validate_learning_events.py:415](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/scripts/validate_learning_events.py:415)、[validate_learning_events.py:1631](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/scripts/validate_learning_events.py:1631) — C0 的“真实板名零命中、写后读不回”表述过强，实际是在拒绝文件系统允许的名字。

观测：`检验白板/子目录\中文 🎯：？！　NBSP .md` 真实 writer `rc=0`、validator `rc=0` 且逐字读回；TAB/LF/CR 板名分别 `rc=1`、ledger 0 字节，并准确报告 `U+0009/U+000A/U+000D`。但在当前 macOS 文件系统中，三种 `.md` 文件名均 `exists=True` 且目录枚举逐字相等。JSONL 对转义 LF 也能正常读回。

建议：若继续禁止，应改写为“文件系统允许，但本契约定义为非规范”，并在建板入口提前拒绝；不要等到评分落账阶段才报错。自由文本字段则应单独允许转义控制符。

[LOW] [validate_learning_events.py:1615](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/scripts/validate_learning_events.py:1615)、[learning-events-schema-v1.md:127](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/docs/learning-events-schema-v1.md:127)、[test_g3_2_review_ledger.py:5833](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/tests/regression/test_g3_2_review_ledger.py:5833) — “孤立代理只可能来自内存 record”不准确。

观测：纯 ASCII、合法 UTF-8 的 JSONL 可含 `"\ud800"`；`json.loads` 会从文件构造孤立代理。实测文件 `all_ascii=True`、UTF-8 decode 成功、CLI `rc=1` 并报 `U+D800`。实现是安全的，错误仅在覆盖声明。

建议：改成“裸 UTF-8 不能编码代理码位，但 JSON `\uD800` 转义可从账本重建；读写两路均检查”，并补真实 CLI 文件门。

当前区间实现本身的复核结果：23 个区间项恰拒 2,181 个码点、允许 1,111,931 个；全部允许码点一次性经 JSON→UTF-8→JSON 往返相等，经真实 JSON-inside-YAML 裸形往返也相等；把每个允许码点与 emoji 交错后仍相等。因此在 Python 3.14.4 / PyYAML 6.0.3 的当前实现上，我没有找到区间外的单码点洞。`value_charset_problems()` 运行时也确实覆盖嵌套 dict 键和值、list、tuple，分别实测命中 `U+0085/U+2029/U+007F`。

最终复跑：四回归文件共收集 332 项，`331 passed, 1 skipped, 10 warnings`，`rc=0`，113.84 秒；`git diff --check` 为 `rc=0`。所有变异只发生在 `/tmp` 隔离副本，未编辑工作树。记忆资料只用于选择只读审查流程，不参与任何仓库事实判断。


