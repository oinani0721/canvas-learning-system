# UAT — CARD-CX-G3-2c-C-R1：字符轴判据自洽 + emitter 门承重

> 批次 `[BATCH-2026-09-05-第十一批 / CARD-CX-G3-2c-C-R1]`；车道 `card-x7-ledger-c`（分支 `card/x7-ledger-c`，开工 HEAD `514cff3c`）。
> 本卡是 X7-C 两个**整改后无复审** commit（`991ae914` / `ae53fa05`）的补审：定性 + 补判据 + 1 轮 Codex。
> ⚠️ 本文提到的敌意载体一律写成码点记号 `U+0085`，不在文档里裸嵌不可见字符。

---

## 〇 一句话结论

上一张卡收窄字符轴时写下的**分界判据**，穷举展开后与实现不自洽；本卡裁定
**不扩表、改判据措辞**，并补了四道一致性/行为门、强化了一道判据过弱的既有门。

⚠️ **一轮 Codex 把我第一版的每一条判据都打回了一次**（1 HIGH + 6 MEDIUM + 2 LOW，
全部逐条整改，见 §九）。两个结论要如实说在最前面：
1. 「不扩表」仍然成立，但依据从「结构上够不着」收窄成「**当前 quiz-answer 写点
   不写、复放路径不读**」——`append_event()` 那条路**能**写进去。
2. 「receipt 条目 14 键都有人管」这句话**不成立**：`self_confidence_norm` 没有
   任何约束，可改写 receipt 身份并让节点评不了分。本卡按硬边界不修写点，
   立 `xfail(strict=True)` 交接门移交。

---

## 一 (a) 判据自洽性：穷举展开与差集

### 1. 把「逐字进入 YAML receipt」穷举展开

receipt 条目由 `quiz-answer/SKILL.md` 的 `entry_` 拼接链产出，共 **14 个键**
（顺序即落盘行序，静态提取自源码）：

| # | 键 | 值来源 | 归哪一段防线 |
|---|---|---|---|
| 0 | `event_id` | `q_(_e_id)` | 字符轴（顶层 `event_id`）|
| 1 | `pred_id` | `q_(_e_pred)` | 取自**另一条账本行**的 `event_id` ⇒ 传递覆盖 |
| 2 | `id_form` | `q_("full")` | 常量字面，不含用户输入 |
| 3 | `fsrs_applied` | `"true"/"false"` | 非字符串标量 |
| 4 | `ts` | `q_(ts_str)` | 写点入口 `_TS_RE.fullmatch()` 词法门 |
| 5 | `scored_at` | `q_(_e_sa)` | 同上 |
| 6 | `attempt_count` | `{_e_att}` | 整数构造后裸插值 |
| 7 | `board_form` | `q_("json")` | 常量字面 |
| 8 | `exam_board` | `q_(json.dumps(...))` | 字符轴（`payload.exam_board`）|
| 9 | **`question_id`** | `q_(p.get("question_id","q1"))` | ⛔ **差集** |
| 10 | **`self_confidence_raw`** | `q_(p.get("self_confidence_raw") or "null")` | ⛔ **差集** |
| 11 | `self_confidence_norm` | 数值 | ⛔ **没有任何约束**（Codex round-1 HIGH，见 §九#1）|
| 12 | `grade_norm` | 数值 | 数值校验后裸插值 |
| 13 | `abandoned` | `"true"/"false"` | 非字符串标量 |

`CHARSET_STRICT_FIELDS` = `event_id` / `node_id` / `payload.vault_id` /
`payload.concept_id` / `payload.exam_board`。

**字符串差集 = `{question_id, self_confidence_raw}`**（非空 ⇒ 卡文的判断成立：
判据与实现不一致）。

⚠️ **Codex round-1 更正了这张表**：把 `attempt_count` / `grade_norm` /
`self_confidence_norm` 一句「非字符串标量」带过是不够的——它们同样是**裸插值**，
只是前两个另有构造/校验约束，而 `self_confidence_norm` **一个约束都没有**
（§九#1 的 HIGH）。所以完整的差集不止字符串那两个；本卡对每一键写明约束在哪，
不再用「三段防线全覆盖」概括。

### 2. 三选一：② 改判据措辞收窄（不扩表）

**关键事实**（写点两处 `"payload": {"schema_ext": "review/1"` 构造的并集实测）：
账本行 payload 键集 = `schema_ext / vault_id / concept_id / rating / grade_norm /
review_time / scored_at / fsrs_library_version / fsrs_params_hash / exam_board /
attempt_count` —— **`question_id` 与 `self_confidence_raw` 不在其中**。

而 `value_charset_problems()` 只看**账本 record**。所以把
`("payload","question_id")` 加进严格表，只是加一条**恒不触发**的路径 =
看着像防线的装饰。这不是"风险大不大"的权衡，是**结构上做不到**。

⚠️ 卡文的 ⚠️ 要求「扩表须先过『65 真实路径拒绝数 = 0』实证」。本卡走的是更直接
的对照实证（下面 §一.3），结论比"拒绝数不变"更强：**没有任何行为门发生变化**。

判据措辞改为：「**这条账本记录里**，该字段会不会参与身份比较、或被逐字搬进
receipt」。同步落在三处：`validate_learning_events.py` 的表上方注释与
`value_charset_problems()` docstring、`docs/learning-events-schema-v1.md` §6.1
「分界标准」。**枚举字段表本身一个字节没改**（仍是那 5 项）。

### 3. 「扩表是空操作」的对照实证

把 `("payload","question_id")` 与 `("payload","self_confidence_raw")` 加进严格表，
跑四回归文件与基线对照（临时变异 + 无条件还原 + `shasum` 对比）：

| 阶段 | 命令 | 结果 |
|---|---|---|
| 扩表**前** | 四回归文件全量 | `rc=0`，`339 passed, 1 skipped`，`FAILED=（无）` |
| 扩表**后** | 同上 | `rc=1`，`2 failed, 337 passed, 1 skipped` |
| 还原核对 | `shasum -a 256` | ✅ 与改前相同（`6a698eab…c68`）|

**扩表新引入的红，恰好 2 条，且都是「断言严格字段表内容」的表声明门**：

- `test_g32cc_charset_only_applies_to_identity_and_receipt_fields`（X7-C 的表锁）
- `test_g32ccr1_charset_scope_is_bounded_by_ledger_record_reality`（本卡的一致性门，
  它直接判「`payload.question_id` 不是账本 payload 的键 ⇒ 死条目」）

⇒ **没有任何行为门变红**：真实输入的拒绝面**一条都没变**。这比卡文要求的
「65 个真实路径拒绝数仍为 0」更强——不是"拒绝数恰好没变"，而是那两条路径
**根本不会被求值**（`value_charset_problems()` 沿路径下钻时 `payload` 里没有
这两个键，第一步就 `node = None; break`）。

⚠️ 这条实证同时是**不扩表**裁定的验伪锚：若哪天 `question_id` 真的进了账本
payload，一致性门 §③ 会红，逼着重做这次裁定。

---

## 二 (b) 差集字段逐个实测「写得进读不回」是否可达

载体沿用 `U+0085`（NEL）：`question_id` 取 `"q1" + U+0085 + "x"`，
`self_confidence_raw` 取 `"半" + U+0085 + "懂"`。

| 字段 | 实测 | 定性 |
|---|---|---|
| `question_id` | 首写 `rc=0`、账本 **1 行**；receipt 读回**逐字等于**原值；原样重跑 `rc=0`、账本仍 1 行、`attempt_count` 1→1 | **不可达**（不是数据丢失，也不是显示畸形）|
| `self_confidence_raw` | 同上（同一次写入一并覆盖）| **不可达** |
| `ts` / `scored_at` | 值取 `"2026-08-01T10:00:00Z" + U+0085`，**一次只污染一个字段**并核对拒因点名：`ts` → `本次输入 ts=…不符 §三 受理语法`；`review_time` → `缺稳定业务时刻 review_time`。两次都 `rc≠0`、账本 **0 行**、写入面 sha 不变 | **不可达（仅限本次输入）**——账本里**已有**的行不走这道入口：durable `scored_at` 含 U+0085 时 validator 不报违规（Codex 实测），那段由后续时刻解析与 `q_()` 承担 |
| `pred_id` | 取值来自另一条账本行的 `event_id`，该字段本身在严格表内 | 传递覆盖 |

**为什么不可达**：receipt 侧另有一道**承重**防线——`q_()` 先用 PyYAML 正面证明
往返，证不成回落 `\uXXXX` 转义形态，两条都证不成就**拒写**（round-17）。
它不是"顺带管住了"：负控 E4 拆掉那条往返判据后，(b) 那道门立刻抓到
「写得进读不回」。

⇒ **字符串差集那两个字段没有被放过**：它们落在另一段防线下。
⛔ 但「差集字段都有人管」这句话**不成立**：`self_confidence_norm` 没有任何约束，
Codex round-1 HIGH 实测可改写 receipt 身份并让该节点评不了分（§九#1）。
本卡按硬边界不修写点，改为立 `xfail(strict=True)` 交接门锁住它。

门：`test_g32ccr1_receipt_only_fields_roundtrip_under_hostile_codepoints`（负控 E4）/
`test_g32ccr1_timestamp_axis_rejects_hostile_codepoints_before_any_write`（负控 E8）/
`test_g32ccr1_self_confidence_norm_must_not_forge_receipt_identity`（xfail 交接）。

---

## 三 (c) `value_charset_problems()` 非 dict 分支的可达性

`validate_learning_events.py:1662` 的 `if not isinstance(value, dict): return []`
从生产调用点 **不可达**，两条独立证据：

1. **静态**（AST）：`validate_record_full()` 定义于 `:1694–1774`；非 dict 早退守卫
   在 `:1704`，`value_charset_problems(record)` 调用在 `:1715`，守卫在前；
   且函数体内 `record` **从不重新绑定**（AST 扫 Assign / AugAssign / AnnAssign /
   For / withitem 全部目标，命中数 0）⇒ 传进去的实参必定是 dict。
2. **行为**：`validate_record_full` 对 `"字符串" / 123 / None / ["列表"] / (1,2) / True`
   一律返回 `["顶层必须是 JSON object"]`。

**那条分支为什么还留着**：全仓的**直接调用方**共 11 处，全在
`test_g3_2_review_ledger.py` 的单元门里（其中 1 处是本卡新加的 (c) 门自己）。
它服务的是直接调用方，不是 `validate_record_full()` 这条链。

门：`test_g32ccr1_nondict_branch_unreachable_from_validate_record_full`。
⚠️ **Codex round-1 MEDIUM 打回后收紧了三处**：① 重绑扫描改成「任何 `Store`
上下文的 `record` 名字」——上一版列举了 5 种绑定形式却**漏掉海象**
（`value_shape_problems(record := b"x")`），实测那样改完门仍 PASS 而字符检查
真的收到了 `bytes`；② 守卫与调用都必须是函数体的**顶层语句**且守卫在前
（只比行号不代表支配）；③ 守卫必须真的比 `dict` 且**立即 return**。
负控 **E5**（普通重绑）与 **E10**（海象重绑）各打一个靶，都 KILLED。

---

## 四 (d) emitter 门的子串包含判据：两个变异实测

`ae53fa05` 的判据①是 `assert _snap_A in nd_after` —— **子串包含**。
两个变异打在生产重建路径上（`g32ccr1_negative_controls.py` E1/E2）：

| 变异 | 做了什么 | 强化前 | 强化后 |
|---|---|---|---|
| E1 | A 的载体行被**复制**成两行 | **SURVIVED**（`1 passed`）| **KILLED** |
| E2 | A 的键序重排（载体行字节不变、位置变）| **SURVIVED**（`1 passed`）| **KILLED** |

⚠️ 两个变异都**过得了生产自身的自检**：`_canon_tree(_kept)` 是 dict 比较，
对键序不敏感；重复键被 PyYAML `safe_load` 取最后一个，条目数也不变。
所以这不是"造一个不可能的状态"，是真的会溜过去。

**补的判据**（Codex round-1 又打回一轮后的终态）：
① `nd_after.count(_snap_A) == 1`（挡复制）；
② 把**变更后**那一条也按边界切出来（`_first_calibration_entry_block()`），
   两边**整块相等**（挡键序重排，也挡"末尾追加一行"）；
③ 整条紧跟在 `calibration_log:` 之后（挡"A 被挪到 B 后面"）；
④ 第三阶段补 `rc == 0` + receipt 条目数不变。

⚠️ ②④ 是 Codex round-1 打回的：我第一版写的 `_blk_A in nd_after` **仍然是
没有结束边界的前缀比较**——在 A 末尾追加一个同值重复键，门照样 PASS；
而第三阶段只比「attempt 不增加」，**直接拒绝也满足**（在 F1-only 成功出口前
插一句 `raise SystemExit`，writer rc=[0,0,1] 而门 PASS）。
负控 **E6**（末尾追加重复键）与 **E7**（成功出口坏掉）各打一个靶，都 KILLED。

---

## 五 (e) M8 硬编码字面量的锚点自检

⚠️ **卡文事实与实况的偏差，如实登记**：卡文说「缩进变动会让变异静默失配，
8/8 KILLED 变假绿」。实况是 `g32cb_mutation_gates.py` 的变异循环里**本来就有**
`if src.count(old) != 1: → ANCHOR-ERROR + continue`，且末尾按
`n_killed == len(MUTATIONS)` 判定 ⇒ 锚漂时会 `return 1`，**不会**报成 8/8 假绿。

本卡实际补的是另外两件事：
1. **锚点自检提到所有慢步骤之前**：原先要等 8 道门的绿态前提跑完（约 1 分钟）
   才逐条发现锚漂；现在锚一漂就 `rc=4`、一条变异都不跑。
2. **兑现 `--list`**：docstring 的「用法」里写着 `[--list]`，而 `main()` 里
   **没有任何 argv 处理** —— 敲 `--list` 会静默跑完整套变异（名实不一致）。

**验伪锚**（证明这道自检真的会红）：把 M8 **锚字面量**的前导空格从 20 个改成
21 个后跑 `--list` → 报 `[M8] 锚命中 0 次`、`rc=4`；还原后 `shasum -a 256`
与改前相同。

### ⚠️ 已知盲区（Codex round-1 LOW，**不修，如实登记**）

这道自检判的是「原文本在**整个文件**里出现 1 次」，不是「命中了那条**执行语句**」。
Codex 在副本上实测两种它看不见的漂移：
- **生产那行**的前导空格由 20 变 21 —— 锚仍是子串，`count` 仍为 1；
- 把活行改成等价写法、只在**注释**里留下旧锚 —— 同样 `count` 为 1，变异落在
  注释上，变异前后执行块的 **AST 完全相同**。

⇒ 这两种情况下变异是**无效**的。但 Codex 也明确写了：完整 runner 会把它报成
**SURVIVED**（脚本非零退出），**没有证据表明会假报 `8/8 KILLED`**。真正堵上要
绑定执行块内的语句身份（AST），属另立卡。已把这段盲区写进 `_anchor_audit()`
的 docstring —— 声明不能比证据宽。

---

## 六 裁判命令与实测

> 下表是 **Codex 整改后**的终态实测。整改前的数字（339/1 无 xfail、负控 5/5）
> 记在 §四 与 §九，不与终态混写。

| # | 命令 | 期望 | 实测（终态）| 判定 |
|---|---|---|---|---|
| 1 | 四回归文件全量 pytest | 335 不回退 | **`339 passed, 1 skipped, 1 xfailed`**，`rc=0`（基线 `335 passed, 1 skipped`；本卡 +4 门 +1 xfail 交接门）| ✅ |
| 1b | 卡文原命令（**单**文件 `test_g3_2_review_ledger.py`）| 卡文写 335+1 | **`129 passed, 1 xfailed`**（基线 `125 passed`）—— 见下方偏差说明 | ⚠️ 卡文数字错 |
| 2 | `-k "charset or emitter or charaxis"` | 全绿 | **`6 passed, 124 deselected`** | ✅ |
| 2b | 补跑 `-k "g32ccr1"`（卡文 `-k` 覆盖不到本卡另 3 道门）| 全绿 | **`4 passed, 125 deselected, 1 xfailed`** | ✅ |
| 3 | `g32cb_mutation_gates.py` | 8/8 KILLED + sha 同 | **8/8 KILLED**（干净重跑，跑前跑后两个目标文件 `shasum -a 256` 逐个相同）| ✅ |
| 3b | `g32ccr1_negative_controls.py`（本卡新增，11 条）| 全 KILLED | **11/11 KILLED**；sha 前后相同；`grep -c MUTANT` = 0 | ✅ |
| 4 | live 账本 sha | 开工 = 收工 | 开工 `NOFILE`、收工 `NOFILE`（该文件不存在）| ✅ |
| 5 | `tests/skills` | 369 起 | **`369 passed`**（与基线同；`SKILL.md` 本卡零改动）| ✅ |

### ⚠️ 裁判 3 第一次跑的 sha 判据作废（我的操作失误，如实记）

第一次裁判 3 报了 `8/8 KILLED` 但末尾 **`⛔ 有文件未还原：validate_learning_events.py`**
—— 不是脚本没还原，是**我在它运行期间改了那个文件的注释**。它的 sha 复核
拿跑前基线比跑后现值，于是如实报了「变了」。**这道守卫工作正常**，作废的是
那一次的 sha 判据，不是 8/8 结论。已在无并发编辑的条件下**干净重跑**，
上表记的是重跑结果。教训：变异 harness 的目标文件在它跑的时候一个字都不能碰。

### ⚠️ 裁判 1 的卡文数字与命令不匹配（如实）

卡文写的命令是**单**文件 `tests/regression/test_g3_2_review_ledger.py`，期望
`335 passed 1 skipped`。实测该文件 `--collect-only` 恰好 **125 项**，跑出来就是
`125 passed`（基线）。`335 + 1` 出自 X7-C 验收单的「**四**回归文件全量」
（`test_learning_events_schema_contract.py` / `test_fsrs_bridge.py` /
`test_learning_event_log.py` / `test_g3_2_review_ledger.py`）。
本卡两个都跑并如实记，不拿其中一个去凑另一个的数字。

### ⚠️ `G32CB_PYTEST=` 这个环境变量目前不起作用（如实）

卡文裁判 3 写 `G32CB_PYTEST=$(pwd)/.venv/bin/pytest`，但 `g32cb_mutation_gates.py`
的 `PYTEST` 是**硬编码常量**（指向 `card-v5-lance` 那棵树的 venv），根本不读这个
环境变量——去硬编码属 Z6-B 的范围，本卡不动。实测那条硬编码路径当前存在、可跑，
所以 8/8 结果有效；但「设了环境变量」这件事没有产生任何作用。
（本卡新增的 `g32ccr1_negative_controls.py` 读 `G32CCR1_PYTEST`，缺省回落**本树**
`backend/.venv`，不硬编码别的车道。）

---

## 七 4-A 🤖 Claude 已代验

| 检查项 | 证据 |
|---|---|
| 四回归文件全绿、无回退 | `339 passed, 1 skipped`（基线 335+1）|
| `tests/skills` 无回退 | `369 passed`（与基线逐字相同）|
| 两套变异负控全 KILLED | g32cb **8/8**（干净重跑，sha 同）、g32ccr1 **11/11**（判据强化前 E1/E2 SURVIVED；Codex 打回的 6 条各配一条负控 E6–E11，整改前全 SURVIVED）|
| 变异脚本无残留 | 两个目标文件跑前跑后 sha 逐个相同；`grep -c MUTANT` = 0；`git status` 只剩本卡的 4 改 + 4 新增 |
| live vault 零写 | 开工 / 收工两次 `shasum` 均为 `NOFILE` |
| `SKILL.md` 零改动 | 不在 `git status` 里（硬边界：禁改 quiz-answer 语义）|
| 严格字段表零改动 | `CHARSET_STRICT_FIELDS` 仍是那 5 项（两道门各自锁：X7-C 的表锁 + 本卡一致性门 ⓪，后者堵住「空表空真」）|
| 格式门 | `ruff check` All checks passed；`ruff format --check` 全部 already formatted（本卡引入的漂移已修；HEAD 版本逐文件对照过，本来就是干净的，不是存量漂移）|
| 类型门 | ⚠️ **情况变了**：`pyright` 于 **2026-09-05 07:42** 被装进共享 venv（`backend/.venv/bin/pyright`，本树是 symlink），lefthook 的 `python-typecheck` 从「诚实 SKIP」变成**真跑并阻断**。实测本卡两个 py 文件共 **66 errors**，其中落在**本卡新增行**上的 **5 个已全部修掉**（`re.search(...).group` 的 Optional 收窄 ×2、`ast.stmt` 到 `ast.If` 的类型收窄 ×3）；剩 **61 个全部落在本卡没碰过的行上**（判据：把 `git diff --cached -U0` 的 `+` 行号区间与 pyright 报的行号求交，交集为空）。本卡**不修存量**（禁止一次修复混合多个不相关变更），commit 用 `LEFTHOOK_EXCLUDE=python-typecheck` 外科绕过并在此登记 |

## 八 4-B 👤 你来验

**无变化**。这张卡没有改任何你会看到的行为——它把上一批我自己改的两处
（字符检查的适用范围、一道校验的写法）请第三方看了一遍，并把**代码里写的说法**
和**代码实际做的事**对齐：原来那句话说得比代码做的宽，容易让下一个人照着它
把规则加到用不上的地方。评分、检验白板、笔记的表现都和之前一模一样。

---

## 九 Codex 审查（(f) 一轮）

命令与协议一致（`gpt-6-astra` + `ultra`，read-only，1 轮）。结论 **需整改**：
1 HIGH + 6 MEDIUM + 2 LOW。它没有复述我的说法——把仓库快照到隔离副本，逐条
**自己造反例**验证我的门是不是承重，然后独立复跑了四回归 / skills / 两套变异。

### 逐条处置

| # | 级别 | Codex 的观测 | 本卡处置 |
|---|---|---|---|
| 1 | **HIGH** | `self_confidence_norm` 未经类型检查就**裸插值**进 receipt YAML（`SKILL.md:1320` 读、`:1408` 拼）。喂 `0.5\n    event_id: "quiz:injected"`：首写 rc=0、账本 1 行、attempt 1，但 receipt 的 `event_id` 变成 `quiz:injected`；此后原样重跑与下一次正常评分**全部 rc=1**，该节点评不了分 | ⛔ **不修，移交**——本卡硬边界禁改 quiz-answer SKILL.md 语义。改为立 **`xfail(strict=True)` 交接门** `test_g32ccr1_self_confidence_norm_must_not_forge_receipt_identity`：现在如实红（`AssertionError: receipt 身份被 self_confidence_norm 注入改写: 'quiz:injected'`），写点修好后它会 XPASS(strict) 报红，逼下一张卡把它转正。同时把本卡「三段防线覆盖 14 键」的声明收窄 |
| 2 | MEDIUM | 「结构不可达 / 扩表恒不触发」不能推广到全部写侧：`learning_event_log.append_event()` 接受任意 payload，实测能把带 U+0085 的 `question_id` 写进账本且 validator violations=[]；此时扩表**会**报 U+0085，不是空操作 | ✅ **论据收窄**：裁定仍是「不扩表」，但依据改成「**当前 quiz-answer 落账写点不写、复放路径不读**」，不再说「结构上够不着」。代码注释 / §6.1 / 一致性门 docstring 三处同步；E3 的 docstring 也删掉了「任何行为门都不变」这句（它只跑指定门） |
| 3 | MEDIUM | 「整条逐字节」其实是**没有结束边界**的前缀子串：在 A 末尾追加同值重复键 `abandoned: false`，门 PASS 而该键行数 2→3 | ✅ 新增 `_first_calibration_entry_block()`，对**变更后**那一条也按边界切出来整块比。负控 **E6** 打这个靶 |
| 4 | MEDIUM | emitter 门第三段只比 `attempt` 不增 —— **直接拒绝也满足**。在 F1-only 成功出口前插 `raise SystemExit`，writer rc=[0,0,1] 而门 PASS | ✅ 补 `rc == 0` + receipt 条目数不变。负控 **E7** 打这个靶 |
| 5 | MEDIUM | 一致性门能从**错误的提取结果**得到绿灯：双引号 f-string 新键漏提取、注释掉的旧键被算进去、单引号 payload 键漏提取；**严格表清空**时新门也 PASS | ✅ 提取器从正则改 **AST**（只解析唯一执行块，注释天然排除；`ast.unparse` 取值表达式）；并加 ⓪「严格表逐项钉死」堵住空表空真。两处 payload 也按 `review_time` 分成「落账写点 / 比较用 envelope」，不再笼统说「两处写点」。负控 **E9** 打这个靶 |
| 6 | MEDIUM | 时刻门**同时污染两个字段**，删掉 `ts` 判据仍 PASS —— 实际拒因是 `payload 缺稳定业务时刻 review_time` | ✅ 拆成两个用例，一次只污染一个字段，并**核对拒因点名的是哪个字段**。负控 **E8** 打这个靶 |
| 7 | MEDIUM | AST 门漏掉**海象**：`value_shape_problems(record := b"x")` 后门仍 PASS，而字符检查真的收到 `bytes` | ✅ 重绑扫描改成「任何 `Store` 上下文的 `record` 名字」+ `ExceptHandler`；并加「守卫与调用都必须是**顶层语句**且守卫在前」「守卫必须比 `dict` 且立即 return」。负控 **E10** 打这个靶 |
| 8 | LOW | 锚点自检判的是「原文本在**整个文件**出现 1 次」，不是「命中执行语句」：缩进 20→21 仍 count=1；注释诱饵也 count=1、AST 不变。Codex 自己写明「完整 runner 对这种无效变异仍报 SURVIVED，没有证据表明会假报 8/8 KILLED」 | ⚠️ **不修，如实登记**：在 `_anchor_audit()` docstring 里写清这两种盲区与「它只会报 SURVIVED、不会伪装成 KILLED」。绑定执行块语句身份属另立卡 |
| 9 | LOW | `991ae914` 的容器门 docstring 声称覆盖 **tuple**，样本里一个 tuple 都没有；删掉遍历的 tuple 支持后五道门全绿 | ✅ 补三个 tuple 样本（裸 tuple / list 嵌 tuple / tuple 嵌 dict+list）。负控 **E11** 打这个靶 |

### Codex 还更正了我的分工表

它按真实来源重算 14 键，指出差集**还应包含** `review_time` / `scored_at` /
`attempt_count` / `grade_norm` —— 它们同样是**裸插值**，只是各自另有约束
（时刻校验 / 整数构造）。并指出时刻分工要分「本次输入」与「账本已有行」：
durable `scored_at` 含 U+0085 时 validator 不报违规，那段由后续解析与 `q_()`
处理，不能一并算在入口词法门头上。⇒ §一 的分工表与 §二 的措辞已按此收窄。

它也核到**四处物理写侧**（quiz-answer:2701 / start-exam-board:445 /
ai-linked-doc:189 / append_event:127），前三者当前不写那两个 payload 键，
第四者**可写**（已执行验证）。

### Codex 的独立复跑（与我的数字对齐）

| 检查 | 它的观测 |
|---|---|
| `514cff3c` 基线副本，四回归 | `335 passed, 1 skipped`，rc=0 |
| 当前工作区，四回归 | `339 passed, 1 skipped`，rc=0 |
| `tests/skills` | `369 passed`，rc=0 |
| 隔离副本 g32cb / 新负控 | 8/8、5/5 KILLED |
| 两脚本 `--list` | 每锚 1 次，rc=0 |
| 五个审查文件 + writer 的 SHA-256 | 前后全部相同 |
| 两处账本路径 | 两次均 `NOFILE` |

### ⚠️ 整改后**无复审**（本卡自己踩进了它要修的那个坑）

本卡族（`CARD-G3-2c-C` → 本卡）轮次已累计 **3 轮**（round-1 / round-2 / 本轮），
按协议 §1 到顶。上面 7 条整改**没有再送第三方**——这正是本卡开卡的原因
（「整改后无复审」）。区别在于：本卡给**每一条**整改都配了一条会变红的负控
（E6–E11，实测 11/11 KILLED），而不是只留一句「已修」。仍建议下一批排一张
纯复审卡看这 7 条整改本身。

---

## 十 本卡未证明什么

1. **没有证明「所有 producer 写出的 receipt 都安全」**。本卡只走 quiz-answer
   这一条写点。`start-exam-board` / `ai-linked-doc` / `append_event` 不产出
   `calibration_log` 条目，所以不在 receipt 面上；但它们能往账本追加行，
   而**只有 quiz-answer 调 `validate_record_full()`** —— 这条既有缺口本卡没动。
2. **没有证明 `q_()` 对全部码点都成立**。(b) 只用 `U+0085` 一个载体实测；
   `q_()` 的判据是"正面证明往返"而不是枚举，本卡未做全码点扫描（那是 X7-C
   在字符轴一侧做过的事，`q_()` 一侧没做）。
3. **没有证明差集只有这两个字段是"永远"的**。提取器已从正则改成 **AST**
   （只解析唯一执行块，注释与改名都会暴露），但它仍只认「`entry_` 是一条
   f-string 拼接链」这一种形态。若将来改成循环拼、或从别处 update 进去，
   门会因为「前提没了」而红——**但它红的理由是"提取前提变了"，不会告诉你
   新字段该归哪段防线**。
3b. **没有修 `self_confidence_norm` 的写点缺口**（Codex round-1 HIGH）。它是
   本卡硬边界外的写点语义面，只立了 `xfail(strict=True)` 交接门锁住现象。
   在它被修好之前，「receipt 条目 14 键都有人管」这句话**不成立**。
3c. **没有证明 `append_event` 那条路的安全性**。Codex 实测它能把带 U+0085 的
   `question_id` / `self_confidence_raw` 写进账本且校验器不报违规。本卡只把
   「不扩表」的依据从「结构上够不着」收窄成「当前没人写、没人读」，
   **没有**给那条路加任何门。
4. **没有跑 `g32b_mutation_gates.py`**（138 项全量表，属 Z6-C 卡）。
5. **没有部署验证**。live vault 全程只读，`learning_events.jsonl` 不存在
   （`NOFILE`）；所有行为证据都在 pytest 的 tmp vault 里。
6. **没有清掉存量类型错误**：`pyright` 今天才被装进共享 venv，`python-typecheck`
   从 SKIP 变成真跑。本卡把自己引入的 5 个修干净了，但**61 个存量错误没动**，
   commit 用 `LEFTHOOK_EXCLUDE=python-typecheck` 绕过。⇒ 「类型门通过」这句话
   对本卡**不成立**，只成立「本卡没有新增类型错误」。
7. **7 条整改本身没有第三方复审**。本卡族轮次已到顶（3 轮），Codex 打回的
   7 条整改是我自己改自己验的——区别只在于每条都配了一条会变红的负控
   （E6–E11，实测 11/11 KILLED）。这与本卡开卡时批评 X7-C 的那件事是同一形态，
   如实登记，建议下批排纯复审卡。
8. **锚点自检对「注释诱饵 / 缩进漂移」仍失明**（§五 已展开），未修。

---

## 十一 待你裁决

| # | 事项 | 默认处置（已按此执行） | 需要你确认 |
|---|---|---|---|
| **D1** | 差集的处置：不扩表、改判据措辞 | 已按此执行；理由是扩表结构上是空操作（§一.3 对照实证）| 同意 / 要求扩表 |
| **D2** | `docs/learning-events-schema-v1.md` §6.1「分界标准」措辞同步收窄（枚举表不变）| 已改，并与代码注释、一致性门三处同源 | 同意这一范围认定 |
| **D3** | 新增 `g32ccr1_negative_controls.py` 作为**独立**负控脚本，而不是往 `g32cb` 里加 M9/M10 | 已按此做——裁判 3 的「8/8 KILLED」是卡文写死的数字，往里加会改掉那个判据 | 同意 / 要求合并进 g32cb |
| **D4** | (e) 按「卡文前提部分不成立」处理：不假装补了一个不存在的洞，改为补 pre-flight + 兑现 `--list` | 已按此执行并在 §五 如实登记 | 同意这一范围认定 |
| **D5** | 一致性门的提取方式：**AST**（不是正则）| 已按 Codex round-1 打回改成 AST：只解析唯一执行块，注释诱饵/改名/双引号 f-string 三种漂移都会暴露 | 同意 / 要求换成运行时提取 |
| **D6** ⭐ | **新增**：Codex round-1 HIGH（`self_confidence_norm` 可改写 receipt 身份）**不修**，立 `xfail(strict=True)` 交接门 + 契约里如实登记 | 已按此执行——修它要动 quiz-answer SKILL.md 写点语义，本卡硬边界明令禁止 | 同意移交 / 要求本卡破边界修 |
| **D7** ⭐ | **新增**：Codex 的 7 条整改**没有再送第三方**（本卡族轮次 3 轮到顶）| 已按此执行，并给每条整改配了一条会变红的负控（E6–E11）；§十.7 如实登记 | 同意 / 要求下批排纯复审卡 |
| **D8** ⭐ | **新增**：Codex LOW#8（锚点自检对注释诱饵/缩进漂移失明）**不修**，只在 docstring 如实登记 | 已按此执行（它只会报 SURVIVED，不会假报 KILLED）| 同意 / 要求本卡修 |

---

## 十二 台账待登记条目

> 本卡按硬边界**未改**《未合卡追踪台账》。以下条目请主 session 登记。

1. `card/x7-ledger-c` 新增本卡 commit（未合并、未 push）。
2. **卡文裁判 1 的命令与期望值不匹配**：卡文写的是单文件
   `tests/regression/test_g3_2_review_ledger.py` 却期望 `335 passed 1 skipped`；
   实测该文件**恰好 125 项**（`--collect-only` 125）。`335 + 1` 是 X7-C 验收单里
   **四回归文件**的合计。本卡两个都跑并如实记（协议 §5「数字与命令输出一致」）。
3. **卡文 (e) 的前提部分不成立**：`g32cb` 早已有 `count(old) != 1` 的锚点检查，
   锚漂不会假绿成 8/8（见 §五）。本卡改做 pre-flight + 兑现 `--list`。
4. **发现并修掉一处名实不一致**：`g32cb_mutation_gates.py` docstring 承诺
   `--list`，`main()` 里没有 argv 处理（DD-13 面）。
5. **既有缺口，本卡未动**：全仓只有 quiz-answer 调 `validate_record_full()`，
   其余三个 producer 可绕开账本校验直接追加行（§6.1 已如实写明，属另立卡）。
6. **裁判 2 的 `-k` 选择集覆盖不全**：`-k "charset or emitter or charaxis"` 只命中
   本卡 5 道新门里的 1 道（`charset_scope_is_bounded`）；其余靠裁判 1 全量跑到。
   建议下批把 `-k` 补成 `... or g32ccr1`。
7. **⛔ 移交：quiz-answer 写点边界卡**（Codex round-1 HIGH）。
   `self_confidence_norm` 未经类型/取值检查就裸插值进 receipt YAML
   （`SKILL.md:1320` 读、`:1408` 拼），可改写新 receipt 条目的 `event_id`，
   此后该节点评不了分。缺陷已锁在 `xfail(strict=True)` 门
   `test_g32ccr1_self_confidence_norm_must_not_forge_receipt_identity`；
   修好后它会 XPASS(strict) 报红。建议一并检查 `attempt_count` / `grade_norm`
   两个同样裸插值但另有约束的字段。
8. **移交：`g32cb` 锚点自检绑定执行块语句身份**（Codex round-1 LOW）。
   现判据「原文本全文件出现 1 次」对注释诱饵与缩进漂移失明；它只会报
   SURVIVED、不会假报 KILLED，故非阻断。
9. **移交：`append_event` 那条写侧无账本校验**。Codex 实测它能写入带
   非规范码点的 `question_id` / `self_confidence_raw` 且 validator 不报违规。
   本卡只收窄了措辞，没有加门。
10. **本卡的操作失误，如实记**：我在 `g32cb_mutation_gates.py` 运行期间改了它的
   目标文件 `validate_learning_events.py`（只改注释），导致那一次的 sha 复核
   报「有文件未还原」。**守卫工作正常**，作废的是那次 sha 判据；已在无并发
   编辑的条件下干净重跑。规矩：变异 harness 跑的时候，它的目标文件一个字都不能碰。
11. **⛔ 批级：`pyright` 于 2026-09-05 07:42 装进共享 venv ⇒ `python-typecheck`
   从「诚实 SKIP」变成**真跑并阻断**。存量 61 个错误在
   `test_g3_2_review_ledger.py` / `validate_learning_events.py` 上，任何动这两个
   文件的车道**都会被拦**。本卡用 `LEFTHOOK_EXCLUDE=python-typecheck` 绕过并登记；
   建议主 session 立刻通知同批其余车道，并排一张「存量类型错误清零」卡。
12. **本卡族轮次已用满 3 轮**（round-1 / round-2 / 本轮），Codex 打回的 7 条整改
   **无第三方复审**。建议第十二批排一张纯复审卡，审面就是本卡的 diff。
