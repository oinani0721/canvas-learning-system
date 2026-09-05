你是本次改动的独立审查者。请只依据**仓库里的真实文件**作判断，逐条给出 file:line
与你自己跑出来的观测值；不要复述我的说法。

## 仓库与审查范围

工作树根目录（绝对路径）：
`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c`

本轮**只审**这一段 diff（在 `e22ad10a` 之上）：

```
git -C /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c \
    diff e22ad10a -- \
    backend/scripts/g32cb_mutation_gates.py \
    backend/tests/regression/test_g3_2_review_ledger.py
```

范围外的文件、范围外的历史轮次结论，都不在本轮。

## 这次做了什么（一句话）

给变异负控脚本 `g32cb_mutation_gates.py` 做两件事：① 它原来把 pytest 路径**硬编码**
成另一个工作树的 venv 绝对路径，改成「环境变量 → 本车道 venv → 明确报错」；
② 新增第 9 条变异 M9，给写点 `q_()` 的 **ASCII 转义回落**补上变异承重。

### 背景：M9 是一条**退役变异的复活**，请重点复核这个推理

`q_()`（`canvas-vault/.claude/skills/quiz-answer/SKILL.md` 里主写点 PYEOF 块内）
产出「能原样读回的 YAML 双引号标量」，两条路：
1. `_lit = json.dumps(v, ensure_ascii=False)` + 用 PyYAML 正面证明往返；
2. 证不成就回落 `_asc = json.dumps(v, ensure_ascii=True)`（纯 ASCII 转义），
   再证一次；两条都证不成就 `SystemExit` 拒写。

上一轮（X7-C）有一条变异 `M154-q-bare-ensure-ascii-false` 打的就是第 2 条路，
当时被判**假杀而退役**，理由是：非规范码点在进入 `q_()` **之前**就被校验器的
字符轴拒了，拆 `q_()` 观察不到差异。那份验收单同时自陈「`q_()` 的往返自证那一层
若失效不会被任何门发现」。

本卡的推理是：`CARD-CX-G3-2c-C-R1`（上一张卡）把字符轴从「整条 record」收窄到
5 个枚举字段（`CHARSET_STRICT_FIELDS`）之后，`self_confidence_raw` 这类
**receipt-only** 字段不再受字符轴管辖 ⇒ 敌意值**能到达** `q_()` ⇒ 载体重新可达
⇒ M154 可以复活成 M9，而且**不需要挂 depth 层**。

## 本卡的具体改动

1. `g32cb_mutation_gates.py`：新增 `_pytest_bin()`（`G32CB_PYTEST` → 本车道
   `backend/.venv/bin/pytest` → `SystemExit` 报错），形态与
   `backend/scripts/g32b_mutation_gates.py::_PYTEST_BIN()` 一致；删掉原来的
   `PYTEST` 硬编码常量；`_run_gate()` 改调 `_pytest_bin()`。其余（自愈 / sha 基线 /
   绿态前提 / 跑后复核 / KILLED 判据）一个字没动。
2. `g32cb_mutation_gates.py`：新增 M9，锚 `_asc = json.dumps(v, ensure_ascii=True)`
   → `ensure_ascii=False`，绑定新门。
3. `test_g3_2_review_ledger.py`：新增窄门
   `test_g32ce_q_ascii_escape_fallback_is_load_bearing`，三段断言：
   ① 写入成功 `rc=0`；② receipt 里必须是**转义形态**且**不是裸 NEL**；
   ③ 转义形态读得回原值。

## 已裁决、不在本轮讨论的事项

- `CARD-CX-G3-2c-C-R1`（上一张卡）的 7 条整改与它的 `xfail` 交接门：已裁决，不重开。
- `g32b_mutation_gates.py` 的 138 项全量表：归属另一张卡，本轮不看。
- 字符轴收窄本身（该不该收窄、枚举哪 5 个字段）：已裁决。
- 存量 pyright 类型错误（61 个）：已登记为独立卡，不在本轮。

## 请重点回答的问题

1. **M9 到底承不承重**：请自己拆掉那条回落跑一遍，确认指定的那道门变红；
   并说明它是**因为哪一条断言**红的。如果它是被别的东西喂饱的，请指出来。
2. **假杀面**：M9 没有挂任何 depth 层。请判断「不挂层」这个选择是否成立——
   有没有哪一层别的防线其实也参与了这次击杀，使得归因不纯粹？
3. **归因是否真的可分辨**：我声称拆**回落**（M9）落在门的 ① 上、拆**往返自证**
   落在 ② 上。请自己各跑一次，确认两者的失败身份确实不同。
4. **新门是否会被别的原因喂饱**：`self_confidence_raw` 带 `U+0085` 这条输入，
   有没有可能因为与 `q_()` 无关的原因而写不进去/写得进去，让这道门的绿或红
   说明不了 `q_()` 的状态？
5. **`_pytest_bin()` 的三段回落**：环境变量指向一个**存在但不是 pytest** 的文件时
   会怎样？这个降级是否安全、报错是否说得清？与 g32b 的同名函数是否真的同形态？
6. **有没有动到不该动的地方**：自愈 / sha 基线 / 绿态前提 / KILLED 判据这四段
   我声称一个字没改，请核对。
7. **退役变异复活的推理是否站得住**：`self_confidence_raw` 真的不受字符轴管辖吗？
   请从 `CHARSET_STRICT_FIELDS` 与写点落账时的账本 payload 键集两边各查一次。

## 我已经跑过的（请独立复核，不要采信）

- `grep -c 'card-v5-lance' backend/scripts/g32cb_mutation_gates.py` → 0；
  `grep -c 'G32CB_PYTEST'` → 3。
- `--list` → 9 条，每锚命中 1 次，rc=0。
- 归因对照：无变异时新门 rc=0；拆回落 rc=1 落在 ① ；拆往返自证 rc=1 落在 ② ；
  两次跑完 `SKILL.md` 的 SHA-256 与跑前相同。
- 全量 g32cb：见 `_bmad-output/审查/evidence-g32cb/run-r2.txt`（含跑前/跑后 sha）。

## 输出格式

先给一行结论（`通过` / `需整改`），然后按 `[级别] file:line — 一句话` 列出问题，
每条附你的观测值与可执行的建议。级别用 BLOCKER / HIGH / MEDIUM / LOW。
判断标准以「会不会造成用户的一次评分被少记或多记」为最高优先级；
其次是「这条新变异是不是假杀（击杀由别的层贡献）」；
再次是「脚本的说法与它实际做的事是否一致」。
