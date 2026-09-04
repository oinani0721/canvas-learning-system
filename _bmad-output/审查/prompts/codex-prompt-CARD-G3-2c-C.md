你是本次改动的独立审查者。请只依据**仓库里的真实文件**作判断，逐条给出 file:line 与你自己跑出来的观测值；不要复述我的说法。

## 仓库与审查范围

工作树根目录（绝对路径）：
`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c`

本轮**只审**这一段 diff：

```
git -C /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c \
    diff 3dfdd69d -- \
    backend/scripts/validate_learning_events.py \
    backend/tests/regression/test_g3_2_review_ledger.py \
    backend/scripts/g32cb_mutation_gates.py \
    docs/learning-events-schema-v1.md
```

范围外的文件、范围外的历史轮次结论，都不在本轮。

## 这次改了什么（一句话）

给学习事件账本加了一条**字符集规则**：任何字符串字段（含 dict 的键）都不允许出现
下列码点，出现即判违规并**报出具体码点**——

```
C0        U+0000–U+001F
DEL       U+007F
C1        U+0080–U+009F      （含 NEL U+0085）
行段分隔  U+2028 – U+2029
代理码位  U+D800–U+DFFF
```

实现在 `backend/scripts/validate_learning_events.py` 的
`FORBIDDEN_CODEPOINT_RANGES` + `value_charset_problems()`，由 `validate_record_full()`
在前段执行；写入端在追加第一行之前调用同一个 `validate_record_full()`，因此两端
天然一致（这条链在上一张卡已经存在，本卡沿用）。

### 这是一次**方向反转**，请重点看它是否站得住

在此之前，同一批字符是被"支持"的：`quiz-answer/SKILL.md` 里的 `q_()` 会先尝试
原样往返，不行就回落到 `\uXXXX` 转义，两条都不行才拒。也就是说它们**能写进去**。

本次改成一律拒绝。理由是：这批字符在过去 17 轮里修一个冒一个（先 U+0085，
再 U+2028/2029，再 C1，再孤立代理），危险集合由 YAML 版本与解析器实现决定，
不属于本系统。所以改用**码点区间**（闭合）而不是枚举（开放）。

配套：两道原先断言"这些字符能存活"的回归门被反转/移交
（`test_round17_hostile_chars_now_rejected_not_survived`、
`test_round17_rebuild_hostile_carrier_is_unreachable_now`），
新增 6 道 `test_g32cc_*`，契约文字写在 `docs/learning-events-schema-v1.md`
§6.1「字符轴规范输入集」与 §6.3「markerless 旧 receipt 的解析规则」。

## 已裁决、不在本轮讨论的事项

- 「开放集合边界」类意见（"还有某某字符没覆盖"）：本轮不计——这正是改用区间的原因。
- 核心状态机（fsrs_applied 严格 bool / foreign 提升 / 写序锚 / 输入硬上限）：上一张卡已审。
- 并发与锁：归属另一张卡，本卡明确不实现。

## 请重点回答的问题

1. **区间是否真的闭合**：这五段区间之外，还有哪些码点会让"写进去的值读不回来"？
   如果有，说明区间定义有洞；如果没有，请说明你是怎么确认的。
2. **误拒面**：用真实值域（检验白板文件名、中文、emoji、全角标点、路径分隔符）
   实测有没有被拒的。特别看 C0 段——它包含 TAB/LF/CR，是否有正当用途被误伤。
3. **两端是否真的一致**：写入端的拒绝和校验器的拒绝是不是同一个判据？
   有没有哪条路径绕过了 `validate_record_full()`。
4. **`value_charset_problems()` 的正确性**：dict 的键有没有被检查到；
   遍历是否会漏掉嵌套结构里的字符串；孤立代理在什么条件下才可能出现（我的声明是
   "只在内存中的 record 里"，请复核这句是否准确）。
5. **新增 6 道门是否承重**：哪几道即使把实现删掉也依然会绿？
   特别看 `test_g32cc_charaxis_forbidden_set_is_closed_by_ranges` ——
   它想证明"禁止集是闭合的"，这个断言方式成立吗？
6. **两道被反转的门**：原先它们守着"追加新条目时不得改动已有条目"这条性质。
   反转之后，那条性质还有没有门在守？（我认为移交给了
   `test_g32cc_emitter_rebuild_never_mutates_existing_entries`，请复核。）
7. **markerless 旧 receipt 的处置**：`exam_board` 存裸 `1e+300` 时，
   PyYAML 读回是字符串而本次事实是浮点。我的裁决是**拒绝并给出处置建议**，
   而不是按 JSON 猜解。请评估这个裁决，以及 §6.3 的措辞是否与实现一致。

## 我已经跑过的（请独立复核，不要采信）

- 四个回归文件合计：`330 passed, 1 skipped`（rc=0）。
- 校验器命令行：5 个非规范码点各自 rc=1 且报出对应 `U+XXXX`；中文板名对照 rc=0；
  65 层嵌套 rc=1。
- 变异负控 `backend/scripts/g32cb_mutation_gates.py`（含拆字符轴判据、
  把区间退化成枚举两条）。

## 输出格式

先给一行结论（`通过` / `需整改`），然后按 `[级别] file:line — 一句话` 列出问题，
每条附你的观测值与可执行的建议。级别用 BLOCKER / HIGH / MEDIUM / LOW。
判断标准以「会不会造成用户的一次评分被少记或多记」为最高优先级；
其次是「会不会把用户正常的板名拒之门外」。
