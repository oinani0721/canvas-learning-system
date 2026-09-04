需整改

[HIGH] [backend/tests/regression/test_g3_2_review_ledger.py:6035](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/tests/regression/test_g3_2_review_ledger.py:6035) — “追加新条目不得改动已有条目”没有被移交门真正守住。观测：把真实 rebuild 在内存中退回旧 `json.dumps(..., ensure_ascii=False)` 后，当前合法中文门仍 `PASSED`；改用当前契约未禁止的 `self_confidence_raw="半<U+0085>懂"`，A `rc=0`，追加 B `rc=1`，账本仅有 `quiz:板甲#q1`，即 B 评分未入账。现门只比较 PyYAML 解析后的 dict（`:6050-6059`），不是字节，且 `:6069-6073` 未断言重跑 `rc=0`。建议用该载体或手工 seed 历史转义 receipt，逐字节比较 A，明确断言 B `rc=0`、账本含 A/B、retry 完整收敛。

[MEDIUM] [docs/learning-events-schema-v1.md:121](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/docs/learning-events-schema-v1.md:121) — 写端与校验器同源只成立于 quiz-answer，不是账本级保证。文件明确列出 `start-exam-board`、`ai-linked-doc`、`append_event` 三条追加路径不调用 `validate_record_full()`。我实测 macOS 可创建并逐字枚举含 TAB/LF/CR 的 `.md` 文件名，但同值作为 `exam_board` 时 writer 三次均 `rc=1`、账本零行。建议在公共追加层对五个严格字段调用同一字符检查，或至少在建板/改名入口提前拒绝并提供存量迁移；不要等到评分时才发现。

[MEDIUM] [backend/scripts/validate_learning_events.py:437](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/scripts/validate_learning_events.py:437) — “两条路径各兜一半，所以旧实现不构成缺陷”的 noncharacter 论证不成立。实测 `U+FFFE + U+1F3AF`：裸形为 `ReaderError`，ASCII 回落读成 `U+FFFE U+D83C U+DFAF`；`U+FFFF + U+20000` 同样双路失败。因此原五段确有组合洞。当前实现新增全部 66 个 noncharacters，已在 append 前挡住该洞，但 [docs:123](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/docs/learning-events-schema-v1.md:123) 和 [test:6091](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/tests/regression/test_g3_2_review_ledger.py:6091) 的理由仍错误。建议保留新增区间，改正说明，并增加这两个混合字符串的端到端零写门。

[MEDIUM] [backend/tests/regression/test_g3_2_review_ledger.py:5979](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/tests/regression/test_g3_2_review_ledger.py:5979) — markerless 门只有“float 事实必须拒”的负例，没有“真板名是字符串 `1e+300` 必须接受”的正例。实测当前实现对字符串事实首写 `rc=0`、markerless 重跑 `rc=0`、账本 `1→1`；但“凡长得像 JSON 数字就拒”的回归仍可通过现门。建议补字符串正例，并把 `:6011` 错写的“读回来是 float”改为“str”。

[LOW] [backend/tests/regression/test_g3_2_review_ledger.py:5839](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/tests/regression/test_g3_2_review_ledger.py:5839) — 新门已能证明禁止集合恰为 2181 点，但不能证明实现采用区间。观测：把常量替换成 2181 个单点区间后，`matches_expected_exactly`、`every_forbidden`、`boundary_neighbours` 仍是 `3/3 passed`；因此 [M7:113](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/scripts/g32cb_mutation_gates.py:113) 只杀“不完整枚举”。若“必须按区间表达”是契约，建议再断言规范化后的精确区间 tuple。

[LOW] [backend/tests/regression/test_g3_2_review_ledger.py:5891](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/tests/regression/test_g3_2_review_ledger.py:5891) — 测试声称覆盖 tuple，但五个载体没有一个 tuple。实现当前确实能从 `exam_board=("ok", "x<U+0085>")` 报 `U+0085`，但删掉 tuple 分支不会被此门发现。建议补真实 tuple 嵌套载体。

逐项复核结果：

1. 当前仓库已不是题述五段，而是五段 2115 点加 66 个 noncharacters，共 2181 点；五段内 `miss=0`。原五段存在上述混合字符串洞，当前扩集已封住。
2. 扫描 `canvas-vault` 的 65 个真实文件路径，拒绝数为 0；中文、emoji、全角标点、`/`、`\` 均返回 `[]`。自由文本已收窄放行：多行 `callout_ingested.text` 后再评分实测 `rc=0`、账本 `1→2`。
3. v1 quiz 路径使用同一个 `validate_record_full()`；但其他 producer 绕过。未知整数版本也按设计绕过：含 U+0085 的 v1 得 1 条 violation；v2 得 `violations=[]`、1 条 WARN。
4. 当前只检查 `CHARSET_STRICT_FIELDS`。这些字段内部的 dict 键、值、list、tuple 均能递归命中；普通 payload 自由字段及其键按新契约放行。孤立代理并非只来自写点内存：ASCII JSON `"\uD800"` 经 `json.loads` 即可从文件物化；当前实现与文档已正确处理这一点。
5. 当前共有 11 道 `test_g32cc_*`，不是 6 道。仅删除 `validate_record_full()` 中的 charset 调用时，其中 10 道仍绿，只有端到端 `charaxis_nonconforming` 会红；两道反转门也会红。删除字符判据本身则由 M6/全量码点门捕获。
6. 两道反转门只证明 hostile 输入不可达；旧性质没有被现有 emitter 门充分承接，见 HIGH。
7. markerless 裁决合理，§6.3 与当前行为一致：PyYAML 6.0.3 读裸 `1e+300` 为 `str`；float 事实重跑拒绝并给出 `board_form`/改写建议；字符串事实接受。

最终验证绑定 `HEAD=991ae914`，四个文件 blob 为 `1ebec3f4 / 7241f4e / 3b1549b / 5812c3f`：

- 四回归文件：`335 passed, 1 skipped`，rc=0。
- 相关 13 门：`13 passed`。
- CLI 五个样本：均 `rc=1` 且报码点；正常板名 `rc=0`。
- 65 层：报告超过上限 64。
- mutation runner 在隔离 clone 中：`7/7 KILLED`，跑后 SHA 全部还原。

审查方法采用了 Canvas adversarial-audit skill 的只读分轨、真实入口和负控验证流程。


mpt_count` 从 `int 1` 改成 `bool True` 后，观测为 `dict_equal=True`；删账本重跑 `rc=1`、`attempt 2→2`，整道门仍 `1 passed`，因为它没有断言重跑必须成功。全文件也没有其他既有 receipt 字节比较门。

建议：截取 A 条目的原始字节并在追加 B 后逐字节比较；同时断言删除 A 行后的原样重跑 `rc=0`、节点及 ledger 写面不变。

[MEDIUM] [learning-events-schema-v1.md:125](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/docs/learning-events-schema-v1.md:125)、[validate_learning_events.py:415](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/scripts/validate_learning_events.py:415)、[validate_learning_events.py:1631](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/scripts/validate_learning_events.py:1631) — C0 的“真实板名零命中、写后读不回”表述过强，实际是在拒绝文件系统允许的名字。

观测：`检验白板/子目录\中文 🎯：？！　NBSP .md` 真实 writer `rc=0`、validator `rc=0` 且逐字读回；TAB/LF/CR 板名分别 `rc=1`、ledger 0 字节，并准确报告 `U+0009/U+000A/U+000D`。但在当前 macOS 文件系统中，三种 `.md` 文件名均 `exists=True` 且目录枚举逐字相等。JSONL 对转义 LF 也能正常读回。

建议：若继续禁止，应改写为“文件系统允许，但本契约定义为非规范”，并在建板入口提前拒绝；不要等到评分落账阶段才报错。自由文本字段则应单独允许转义控制符。

[LOW] [validate_learning_events.py:1615](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/scripts/validate_learning_events.py:1615)、[learning-events-schema-v1.md:127](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/docs/learning-events-schema-v1.md:127)、[test_g3_2_review_ledger.py:5833](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/tests/regression/test_g3_2_review_ledger.py:5833) — “孤立代理只可能来自内存 record”不准确。

观测：纯 ASCII、合法 UTF-8 的 JSONL 可含 `"\ud800"`；`json.loads` 会从文件构造孤立代理。实测文件 `all_ascii=True`、UTF-8 decode 成功、CLI `rc=1` 并报 `U+D800`。实现是安全的，错误仅在覆盖声明。

建议：改成“裸 UTF-8 不能编码代理码位，但 JSON `\uD800` 转义可从账本重建；读写两路均检查”，并补真实 CLI 文件门。

当前区间实现本身的复核结果：23 个区间项恰拒 2,181 个码点、允许 1,111,931 个；全部允许码点一次性经 JSON→UTF-8→JSON 往返相等，经真实 JSON-inside-YAML 裸形往返也相等；把每个允许码点与 emoji 交错后仍相等。因此在 Python 3.14.4 / PyYAML 6.0.3 的当前实现上，我没有找到区间外的单码点洞。`value_charset_problems()` 运行时也确实覆盖嵌套 dict 键和值、list、tuple，分别实测命中 `U+0085/U+2029/U+007F`。

最终复跑：四回归文件共收集 332 项，`331 passed, 1 skipped, 10 warnings`，`rc=0`，113.84 秒；`git diff --check` 为 `rc=0`。所有变异只发生在 `/tmp` 隔离副本，未编辑工作树。记忆资料只用于选择只读审查流程，不参与任何仓库事实判断。


