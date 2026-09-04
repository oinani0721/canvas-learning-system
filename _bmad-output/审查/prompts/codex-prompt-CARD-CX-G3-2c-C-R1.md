你是本次改动的独立审查者。请只依据**仓库里的真实文件**作判断，逐条给出 file:line
与你自己跑出来的观测值；不要复述我的说法。

## 仓库与审查范围

工作树根目录（绝对路径）：
`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c`

本轮审两段。

**① 本卡改动**（在 `514cff3c` 之上）：

```
git -C /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c \
    diff 514cff3c -- \
    backend/scripts/validate_learning_events.py \
    backend/tests/regression/test_g3_2_review_ledger.py \
    backend/scripts/g32cb_mutation_gates.py \
    backend/scripts/g32ccr1_negative_controls.py \
    docs/learning-events-schema-v1.md
```

**② 上一张卡整改后**从未被第三方看过的两个 commit（本轮补审）：

```
git -C <上面那个根目录> show 991ae914 -- \
    backend/scripts/validate_learning_events.py \
    backend/tests/regression/test_g3_2_review_ledger.py \
    backend/scripts/g32cb_mutation_gates.py \
    docs/learning-events-schema-v1.md

git -C <上面那个根目录> show ae53fa05
```

范围外的文件、范围外的历史轮次结论，都不在本轮。

## 这次做了什么（一句话）

上一张卡把学习事件账本的**字符轴**从「整条 record」收窄到五个枚举字段
（`CHARSET_STRICT_FIELDS`）。本卡发现它写下的**分界判据**与实现不自洽，于是
把判据措辞与实现对齐、补上三道一致性/行为门、并强化一道判据过弱的既有门。

### 背景：那条判据为什么被判为不自洽

`validate_learning_events.py` 里原来的分界写的是「该字段会不会**逐字进入 YAML
receipt** 或参与身份比较」。把这句话穷举展开：`quiz-answer/SKILL.md` 的 `entry_`
拼接链一共往 receipt 写 14 个键，其中 `question_id` 与 `self_confidence_raw`
同样逐字进 receipt，却不在那五个字段里。`ae53fa05` 的门 docstring 自己也承认了
这一点（"会逐字进入 receipt…但不在账本 payload 键集里，因此不受 §6.1 约束"）。

本卡的裁定是**不扩表、改判据措辞**，理由是：`value_charset_problems()` 只看
**账本 record**，而这两个键根本不在账本行 payload 键集里，把它们加进枚举表只会
加一条恒不触发的路径。receipt 侧的字符防线是写点 `q_()` 的正面往返自证。

## 本卡的具体改动

1. `validate_learning_events.py`：`CHARSET_STRICT_FIELDS` 上方的分界注释与
   `value_charset_problems()` 的 docstring 收窄为「**这条账本记录里**，该字段
   会不会参与身份比较、或被逐字搬进 receipt」，并写明三段分工。**枚举表本身
   一个字节没改**（仍是那 5 项）。
2. `docs/learning-events-schema-v1.md` §6.1「分界标准」同步收窄，枚举表不变。
3. 新增 4 道门（`test_g32ccr1_*`）：
   - 一致性门：锁死 receipt 条目字段集与行序、账本 payload 键集、枚举表三者；
     并反向断言枚举表里没有「够不着任何真实记录」的死条目。
   - 行为门：`question_id` / `self_confidence_raw` 带 `U+0085` 首写 rc=0、
     receipt 里读回逐字等于原值、原样重跑不增行不改 `attempt_count`。
   - 行为门：`ts` 含 `U+0085` 在首次 append 之前被词法门拒，账本零行。
   - 静态+行为门：`value_charset_problems()` 的非 dict 分支从
     `validate_record_full()` 那个调用点不可达（AST 断言守卫在调用之前、
     `record` 不重绑）。
4. 强化 `test_g32cc_emitter_rebuild_never_mutates_existing_entries` 的判据①：
   原为**子串包含**（`assert _snap_A in nd_after`），改为「整条逐字节 +
   出现次数恰为 1 + 仍紧跟在 `calibration_log:` 之后」。
5. `g32cb_mutation_gates.py`：把锚点自检提到所有慢步骤之前，并实现 docstring
   里原本承诺、实际不存在的 `--list`。
6. 新增 `g32ccr1_negative_controls.py`（5 条负控，与 g32cb 同一套纪律）。

## 已裁决、不在本轮讨论的事项

- X7-B（`CARD-G3-2c-B`）验收单 §十 的 **D1–D7**：用户按默认裁定，全部照默认执行。
  即：深度 64 / 节点 20 万上限（D1）、超限即拒不做尽力解析（D2）、foreign 路径
  提升凭据（D3）、fixture 直接写出账本行（D4）、「深层值不再是合法值」这一契约
  变更（D5）、`SKILL.md` 在 X7-B 零改动的范围认定（D6）、变异脚本加启动自愈（D7）。
- schema §6.2 的 duplicate / markerless 语义面：**已移交**，本轮不重开。
- 「禁止集还漏了某某码点」这类开放集合边界意见：不计入本轮（改用区间正是为此）。
- 核心状态机（`fsrs_applied` 严格 bool / 写序锚 / 输入硬上限）：前两张卡已审。

## 请重点回答的问题

1. **判据是否真的自洽了**：按新措辞重做一次差集——`entry_` 拼接链里还有哪个
   键，在**账本 record 里**参与身份比较或被逐字搬进 receipt，却不在枚举表内？
   如果有，请点名并说明它落在哪一段防线下。
2. **「不扩表」这个裁定是否站得住**：`question_id` / `self_confidence_raw`
   有没有任何一条路径能进入账本行的 payload？（请查全部写侧，不只 quiz-answer。）
   如果能，本卡的裁定就失效了，请指出那条路径。
3. **三段分工的边界是否有缝**：字符轴（账本身份键与 `exam_board`）、`q_()`
   往返自证（receipt-only 字段）、`_TS_RE` 词法门（时刻串）——这三段合起来
   是否覆盖了 receipt 条目的全部 14 个键？有没有哪个键**两段都不管**？
4. **强化后的 emitter 判据是否够**：新判据是「整条逐字节 + 出现次数 = 1 +
   紧跟 `calibration_log:`」。在什么情况下已有条目被改动而这三条仍然全绿？
5. **新增 4 道门是否承重**：哪几道即使把对应实现删掉也依然会绿？如果有，
   请指出它被什么别的东西喂饱了。特别看那道一致性门——它靠正则从 `SKILL.md`
   静态提取字段集，这个提取在什么条件下会给出错误的字段集而门仍然绿？
6. **`--list` 与锚点自检**：`g32cb_mutation_gates.py` 的锚点自检以「原文本恰好
   命中 1 次」为判据。命中 2 次或更多时它会中止；这个判据对哪一类锚点漂移
   仍然失明？
7. **补审 `991ae914` / `ae53fa05` 本体**：这两个 commit 从未被第三方看过。
   收窄字符轴适用面这件事，除了本卡已经登记的判据措辞问题之外，是否还留下
   别的隐患？特别看 `value_charset_problems()` 对容器形态的遍历，以及
   `ae53fa05` 换载体之后那道门还守不守得住它原来守的那条性质。

## 我已经跑过的（请独立复核，不要采信）

- 四个回归文件（`test_learning_events_schema_contract.py` / `test_fsrs_bridge.py` /
  `test_learning_event_log.py` / `test_g3_2_review_ledger.py`）：基线
  `335 passed, 1 skipped`（rc=0）；本卡后 `339 passed, 1 skipped`。
- `tests/skills`：`369 passed`。
- `g32cb_mutation_gates.py`：8/8 KILLED；`--list` 锚点自检 rc=0；把 M8 的锚
  前导空格改成 21 个（模拟生产缩进漂移）后 `--list` 报「锚命中 0 次」并 rc=4。
- `g32ccr1_negative_controls.py`：判据强化**前** E1/E2 SURVIVED（子串包含判据
  对「行被复制」「行位移」双盲，且两个变异都能过生产自身的 `_canon_tree`
  逐条比较）、E3/E4/E5 KILLED；强化**后**全部 KILLED。两次跑前跑后目标文件
  `shasum -a 256` 均相同。
- live 账本 `canvas-vault/学习事件/learning_events.jsonl`：开工与收工两次均为
  `NOFILE`（该文件不存在）。

## 输出格式

先给一行结论（`通过` / `需整改`），然后按 `[级别] file:line — 一句话` 列出问题，
每条附你的观测值与可执行的建议。级别用 BLOCKER / HIGH / MEDIUM / LOW。
判断标准以「会不会造成用户的一次评分被少记或多记」为最高优先级；
其次是「会不会把用户正常的输入拒之门外」；再次是「门的说法与它实际证明的范围
是否一致」。
