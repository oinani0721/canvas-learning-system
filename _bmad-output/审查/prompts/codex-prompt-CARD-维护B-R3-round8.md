# Codex 定向复核 · CARD-维护B-R3 round-8（只审计数取值口径）

你是对抗复核者。本卡 round-7 你判「清零：否 · 0 BLOCKER / 8 HIGH（5 实现 + 3 自证）」。

⚠️ **口径声明**：卡文限「最多 3 轮」，本轮为第 8 轮、已远超限，需用户追认。
车道判断：上限约束**审查轮次**，不约束**修复**。请照常严格审，不必迁就。
⚠️ 请继续**不要跑 negverify**（原地改写被测源码；round-2 你跑它被打断，
把变异留在工作树里，导致随后的 pytest 测了污染文件、报 240/15）。

## round-7 八条的处置（含两条**车道驳回**，请复核驳回是否成立）

| 你的判词 | 车道处置 |
|---|---|
| HIGH-1 fallback「先归一再选行」只修了局部函数 | ✅ **属实已修**：**全文**『派生』白名单门也先归一（同一顺序耦合，round-8 修了局部、漏了全文） |
| HIGH-2a inline-code 手抄旧量词表 ⇒ `987654`笔`` 失锚 | ❌ **反例不可复现**：实测 rc=1，被「`支` 已在量词表（`支出`）」拦下。机制或许仍在，但该例不成立 |
| HIGH-2b ⑦⑧手抄数词禁集 ⇒「…缺来源锚点共仨个」不核数 | ❌ **反例不可复现**：实测 rc=1，被「信号行未整行匹配标准式」拦下 |
| HIGH-3 闭表遗漏（`⑤`/`例`/`负五个`） | ✅ **三条全属实已修**：定界集补 `①-⑳`+`〡-〺`（**只定界不赋值**）、量词补 `例束艘架间`、符号守卫补中文「负」 |
| HIGH-4 reference-style link | ⚠️ **属实未修**，登记 §五之三 |
| HIGH-5 「安全向过度拼接」不是保值关系 | ✅ **属实**：`1\*5个` 渲染可见 `1*5`，实现按 **15** 查池且 15 在池内 ⇒ 放行。**该论证已证伪**，docstring 与 UAT 均改为「已知 fail-open 面」，行为未改（需单独裁决） |
| HIGH-6 bidi CLI 门被纵深遮蔽 | ⚠️ 已知；本轮未单独加门 |
| HIGH-7 `34/34` 不证明逐项承重 | ⚠️ 已知；round-9 新增三条为逐条单一性质 |
| HIGH-8 我方三处文本错误（7条全称"实现"、"修完8条"、"零回归"） | ✅ **三条全属实已改**：改为「5 实现 + 2 自证」「round-7 修 1 + round-8 修 7」「已运行的证据面内未发现回归，不等于零回归」 |

**请重点复核**：① 两条驳回是否成立（我只驳"反例不可复现"，没否认机制）；
② `_visible_text` 现在被**三处**调用（D2 行循环 / fallback 局部选行 / fallback 全文门），
还有没有第四处该调而未调的；③ 三张闭表这次的补漏措辞是否又写宽了。

## ⛔ 硬限（前三次被中断/污染的教训，请严格遵守）

1. **不要运行 `git diff` / `git show` / `git log -p`** —— 本卡 round-1 就是因此被你侧
   内容过滤器中断、正文 0 字节。只按下面的 file:line 静态阅读当前 HEAD 的文件。
2. **不要运行 `tests/regression/recap_domain_negverify.py`**。⚠️ 该脚本会**原地改写
   被测源码再还原**；上一轮你跑它时中途被打断，把 **survivor-9** 的变异**留在了工作树
   里未还原**、互斥锁也未释放。你随后那次 pytest 因此测的是**被变异的文件**，
   报出的 `240 passed, 15 failed` 是该污染的产物、不是真回归；第二次跑它撞上自己
   留下的锁得 rc=2。车道已取证并按 HEAD 逐字节还原。本轮请**只读它的源码**，
   实测输出由车道提供（见下）。
3. **不要构造或运行任何探针 / 变异 / 临时脚本；不读 `fixtures/` 下 `.md`/`.json` 正文。**
4. **报告第一行**：「BLOCKER/HIGH 清零：是/否（就计数取值口径而言）」。

## round-3 的整改（本轮被审对象）

根因：取数原先按字符类分成 **CJK 一条循环 + ASCII 一条循环**，于是跨类或表外的
数词字成为断点，匹配重锚到尾片。⇒ **合并为一条规则**：

- `_NUMERAL_LIKE_CHARS` = 表内 17 字 ∪ 廿卅卌 ∪ 大写金融数字 ∪ 异体，
  **只用于定界**（判断哪些字符属于同一个数），**不赋任何值**；
- `_NUM_RUN_RE` / `_COUNT_BEFORE_QUANT_RE` 取整串 → `_join_free` 剥连接字符 →
  `_count_token_value` 判值：**只有**「全 ASCII 数字」或「表内单字数词」给值，
  其余（多字中文数词 / 混写 / 含表外数词字）一律 None ⇒ fail-closed；
- `_CJK_DECIMAL_RE`：数串 + `点`/`.` + 数串 + 量词 = 小数，与 ASCII 侧
  `_D2_DECIMAL_RE` 同口径恒 FAIL（`3点建议` 的正当量词用法不受伤）；
- 合并后只剩定义、无生产调用的三个常量（`_CJK_NUM_RUN_PAT` / `_CJK_NUM_RUN_RE` /
  `_D2_COUNT_RE`）已**删除** —— 只剩定义的常量是死代码。

## 请按行号静态阅读

`canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py`：
- `:1352-1420` 连接语义（含 `_normalize_number_seps`）（`_D2_NOISE_ONE` / `_INVISIBLE_ONE` / `_D2_JOIN_ONE` /
  `_join_free`，含收窄后的 docstring）
- `:1500-1600` `_CJK_NUM` / `_CJK_UNIT` / `_CJK_NUM_CHARS` / `_CJK_NUM_EXTRA` /
  `_NUMERAL_LIKE_CHARS` / `_NUM_RUN_PAT` / `_COUNT_BEFORE_QUANT_RE` /
  `_CJK_DECIMAL_RE` / `_count_token_value` / `_cjk_single_to_int`
- `:1690-1745` D2 叙述段：区间两端终核（**句式门之后**）、小数检查、唯一取数循环
- `:1975-2010` fallback 允许式：千分位归一 + 小数检查 + 取数循环

`backend/tests/regression/test_recap_scan_signals.py`：
`:3124` 判据契约（期望值独立写死）、`:3184`/`:3364` 两道合成 scan 单元门、
`:3216`、`:3251`、`:3288` 切断矩阵门（docstring 已按你的批评收窄）、
`:3400` 起 `test_domain_r6_cross_class_and_offtable_numeral_cli` 与文件末尾的
`test_domain_r7_range_endpoints_and_fallback_seps_cli`（本轮新增）、
以及 `_one_problem_has`（按你的批评，诊断类别与完整 token 须出现在**同一条** problem）。

`backend/tests/regression/recap_domain_negverify.py`：**只读源码**，看
survivor-15…37 二十三条新变体的替换内容是否真的禁掉了该性质的全部防线。

## 请回答

1. 还有没有别的路径能让「进池比对的值」≠「读者在渲染后看到的数」？
2. `_NUMERAL_LIKE_CHARS`（定界）、`_D2_QUANT`（量词）、`_CJK_NUM`（赋值）三张封闭表，
   车道在验收单 §五之三 的登记诚实吗？有没有被低估的？
3. 「定界要宽、赋值要窄」这个不变式是否在两个消费点都成立？
4. 新门有无空洞断言或比实现宽的措辞？

## 命令（只跑这一条 pytest + 一条 git）

- `cd backend && PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest
  tests/regression/test_recap_scan_signals.py -q -p no:cacheprovider`
  —— 开工基线 249，现应为 **261**。若你得到别的数字，请先检查工作树是否 clean
  （`git status --porcelain` 应为空）再下结论。
- `git rev-parse HEAD`

车道实测（供你核对，**不要**自己重跑变异）：negverify **37/37 全部如期变红**，
被测文件 sha256 前缀 `71d9739956de`，运行前后逐字节一致；
扩大回归 `tests/skills + 两个 regression 文件` = **593 passed**；
真实 CLI 探针 84/84。

## 输出格式

- 第一行：「BLOCKER/HIGH 清零：是/否（就计数取值口径而言）」。
- 逐项 ✅/⚠️/❌ + `file:line`。**新问题不限于「本卡引入」**，存量未闭合的也请报并标注。
- 写出你实际跑出的 pytest 结果与 `git rev-parse HEAD`。
- 报告一次给出；先写正文再补过程。
