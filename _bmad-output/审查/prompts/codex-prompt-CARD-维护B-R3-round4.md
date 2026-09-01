# Codex 定向复核 · CARD-维护B-R3 round-3（末轮；只审计数取值口径）

你是对抗复核者。本卡 round-3 你判「清零：否 · 0 BLOCKER / 3 HIGH」。
车道对**三条都实跑复现属实**并已整改（见下）。本轮复核这些整改。

⚠️ 上一轮你**遵守了「不要跑 negverify」**，pytest 得 256 与车道一致、无污染 ——
请本轮继续遵守（该脚本会原地改写被测源码）。

## round-3 三条 HIGH 的整改

| 你的判词 | 整改 |
|---|---|
| 区间只终核右端（`987654-0个` 只按右端 `0` 查池，0 恒在池内） | 区间**两端都终核**，无出处端点逐个报并挖空整段。⚠️ 报错放在**句式门之后**——第一版放在之前，当场误伤非自陈句 `建议覆盖 2~3 个节点` |
| fallback 无小数/千分位防线（`0.0个`/`零点零个`/`1,005个` 逐片碰池） | `_normalize_number_seps`（认半角与全角逗号）与 `_DECIMAL_ANY_RE` **下沉为 D2/fallback 共用** |
| 小数/分隔符非渲染语义定界（`987654<b>.</b>0个`、`987654，000个`） | 小数分隔符两侧**容连接字符**，认 `.`／`．`／`点`；千分位同时认半角与全角逗号 |
| （你另指出）区间正则手抄旧 11 字量词表，与 `_D2_QUANT` 分叉 | 改为共用 `_D2_QUANT` |
| （你另指出）`980,005` 门未绑「找不到同值来源」；定界集断言只做子集包含 | 已分别补绑与改为**精确相等** |

## 上一轮（round-2）五条 HIGH 的处置回顾（供你核对车道有没有改口）

| round-2 判词 | 车道复核 | 处置 |
|---|---|---|

| 你的判词 | 车道复核 | 处置 |
|---|---|---|
| fallback ASCII 仍按碎片入池（`1 000`→[1,000]、`9**5`→[9,5]） | ✅ 属实，实测 rc=0 | 已修 |
| 表外/跨类导致尾片重锚：`九十八万5个`、`廿五个` | ✅ 属实；`壹佰个` 更甚（整域抽不出 token） | 已修 |
| 同上第三例 `980,005个` 被逗号切断只取 `005` | ❌ **不成立**：逗号归一化先于取数生效，实测按 **980005** 查池、rc=1 | **驳回**，并配门钉住该事实 |
| 连接表内含渲染可见字符，`_join_free`「还原读者看到的那个数」过宽 | ⚠️ **措辞问题、非缺陷**：过度拼接是**安全向**（查到的值 ⊇ 读者看到的数，不构成虚构通道），危险的是**欠拼接** | 措辞收窄，行为不改 |
| `_D2_QUANT` 含 `点`：`五点五个`/`5点5个` 拆成两个 5 碰池 | ✅ 属实，均 rc=0 | 已修 |

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
survivor-15/16/17/18/19/20 六条新变体的替换内容是否真的禁掉了该性质的全部防线。

## 请回答

1. 还有没有别的路径能让「进池比对的值」≠「读者在渲染后看到的数」？
2. `_NUMERAL_LIKE_CHARS`（定界）、`_D2_QUANT`（量词）、`_CJK_NUM`（赋值）三张封闭表，
   车道在验收单 §五之三 的登记诚实吗？有没有被低估的？
3. 「定界要宽、赋值要窄」这个不变式是否在两个消费点都成立？
4. 新门有无空洞断言或比实现宽的措辞？

## 命令（只跑这一条 pytest + 一条 git）

- `cd backend && PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest
  tests/regression/test_recap_scan_signals.py -q -p no:cacheprovider`
  —— 开工基线 249，现应为 **257**。若你得到别的数字，请先检查工作树是否 clean
  （`git status --porcelain` 应为空）再下结论。
- `git rev-parse HEAD`

车道实测（供你核对，**不要**自己重跑变异）：negverify **20/20 全部如期变红**，
被测文件 sha256 前缀 `f3257f209527`，运行前后逐字节一致；
扩大回归 `tests/skills + 两个 regression 文件` = **589 passed**；
真实 CLI 探针 46/46。

## 输出格式

- 第一行：「BLOCKER/HIGH 清零：是/否（就计数取值口径而言）」。
- 逐项 ✅/⚠️/❌ + `file:line`。**新问题不限于「本卡引入」**，存量未闭合的也请报并标注。
- 写出你实际跑出的 pytest 结果与 `git rev-parse HEAD`。
- 报告一次给出；先写正文再补过程。
