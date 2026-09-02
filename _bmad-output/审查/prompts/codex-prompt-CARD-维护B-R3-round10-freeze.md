# Codex **冻结审查（终态）** · CARD-维护B-R3 —— 绑定最终 commit

⚠️ **本轮性质**：不是「续轮追清零」。上一份冻结审查绑的是 `edd471bc`（round-13），
此后 **round-14 / 15 / 16 三轮整改**已把你那份报告里点名的**有界项逐条闭掉**
（见下表）。卡文条件 (g) 要求报告**绑定最终 commit**，而现有报告已过期 ⇒
本轮只求一件事：**在终态 commit 上给出准确测量**。请不必迁就任何结论。

⚠️ 卡文限「最多 3 轮」，实际已远超；超限未获用户追认，本报告不构成合并授权。
⚠️ 请继续**不要跑 negverify**（原地改写被测源码；round-2 你跑它被打断，
把变异留在工作树里，导致随后的 pytest 测了污染文件、报 240/15）。

## 你上一份（`edd471bc`）报告的逐条处置

| 你的判词 | 处置 |
|---|---|
| ❌ HIGH 第三个窄数值口径副本（inline-code 的 ASCII-only 守卫）| ✅ **round-14 修**：数字部分改为派生自 `_NUMERAL_LIKE_CHARS`，与取数同源；副本消除 |
| ❌ HIGH 过度拼接不保值，且 `_visible_text` 注释仍称「安全向」| ⚠️ 行为**未修**（已实测无有界修法，round-13 试修回退）；但 **round-14 已把措辞统一为「已被证伪、如实登记 fail-open」**——你点的「注释比证据宽」这一半已闭 |
| ❌ HIGH renderer 闭包缺口：shortcut `[t]` 未覆盖 + `_INVISIBLE_ONE` 与全局门分叉 | ✅ **两半都修**：round-15 全局零宽门改为共用 `_INVISIBLE_ONE`（bidi isolate U+2065-2069 原能过门）；round-16 新增 `_VIS_SHORTCUT_LINK_RE` |
| ⚠️ HIGH-3 raw 专用绑定（seed ledger / 五元组 / tips）| ⚠️ **未修**，如实登记（需重设计统一入口，已移交）|
| ❌ 崩溃假阴：只扫外层 stdout、只枚举五种异常名 | ✅ **round-16 修**：判据从「名单」改「形态」——`E <Exc>` 非 `AssertionError` / `Traceback` / `INTERNALERROR` / 收集期 error；提成纯函数 `_looks_like_crash` 并有 9 形态单测 |
| ⚠️ 不要求变异轮 `rc == 1` | ✅ **round-16 修**：`rc != 1` 直接判「不算变红」|
| ⚠️ 负号两侧独立手抄集 | ✅ **round-14 修**：统一 `_NEG_SIGN` |
| ❌ HIGH-6 闭表外尾片重锚 | ⚠️ **开放集，未修**，如实登记 |
| ⚠️ HIGH-8 组合变异 | ⚠️ 部分：新增变体为逐条单一性质；组合变异仍存 |

**请重点回答**：① round-16 的 shortcut link 归一有没有**误伤**（callout `[!x]`、
脚注 `[^1]`、任务框 `[ ]`）或顺序问题（它必须跑在 inline/reference 之后）？
② 新的崩溃判据有没有**新的**假阴/假阳？「非 AssertionError 即崩溃」这个二分成立吗？
③ 到此为止，还剩哪些**有界**（可在一次改动内闭合）的 HIGH？请把它们与
**开放集**（源码→渲染映射面、闭表尾片重锚）分开列——这个区分是本卡的核心争点。

## round-8 九条的处置（请逐条复核）

| 你的判词 | 处置 |
|---|---|
| HIGH-1 inline-code 量词副本手抄旧表 | ✅ **副本已消除**：改为从 `_D2_QUANT` 机械派生 |
| HIGH-2 ⑦⑧手抄数词禁集 | ✅ **副本已消除**：数词/定界集**上移**到允许式之前，两式直接引用 `_NUMERAL_LIKE_CHARS`（实测原分叉 **55 个字符**）|
| HIGH-3 `_visible_text` 非统一入口（多条 raw 专用绑定）| ⚠️ **部分**：全文『派生』门已先归一（round-9）；manifest 种子 ledger / 五元组逐条仍是 raw 绑定，**未修** |
| HIGH-4 reference-style link | ✅ **已修**（如实声明：**仍不是完整 renderer**，highlight/math/脚注未覆盖）|
| HIGH-5 过度拼接不保值 | ⚠️ **未修，且已实测无有界修法**：round-13 试过「成对剥离 + 落单移出连接集」，结果只是把 fail-open 从「拼错的数」挪到「尾片」，还打破 3 道门 ⇒ **已完全回退并登记** |
| HIGH-6 闭表之外尾片重锚 | ⚠️ **开放集，未修**，如实登记 |
| HIGH-7 **崩溃伪红**（survivor-20 `re.error`）| ✅ **已修**，并给脚本加**结构性识别**（`run_suite` 检测 `re.error/NameError/...` 并按失败计，写入铁律 5）|
| HIGH-8 `37/37` 不证明逐项承重 | ⚠️ 部分：round-9~12 新增变体为逐条单一性质；组合变异仍存 |
| HIGH-9 门措辞过宽 | ✅ 中文「负」补 fallback 侧门、量词 `例束艘架间` 逐字补齐（补门后**直接通过** ⇒ 是补证不是新修）|

**请重点回答**：① 两张副本消除后是否还有第三张手抄闭表？
② round-13 那次「试修并回退」的判断是否成立（我只驳"该修法无收益"，没否认问题存在）？
③ 新增的崩溃红识别本身有没有假阴/假阳？

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
survivor-15…39 二十五条新变体的替换内容是否真的禁掉了该性质的全部防线。

## 请回答

1. 还有没有别的路径能让「进池比对的值」≠「读者在渲染后看到的数」？
2. `_NUMERAL_LIKE_CHARS`（定界）、`_D2_QUANT`（量词）、`_CJK_NUM`（赋值）三张封闭表，
   车道在验收单 §五之三 的登记诚实吗？有没有被低估的？
3. 「定界要宽、赋值要窄」这个不变式是否在两个消费点都成立？
4. 新门有无空洞断言或比实现宽的措辞？

## 命令（只跑这一条 pytest + 一条 git）

- `cd backend && PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest
  tests/regression/test_recap_scan_signals.py -q -p no:cacheprovider`
  —— 开工基线 249，现应为 **263**。终态 commit 应为 `26253a7d2d10`。若你得到别的数字，请先检查工作树是否 clean
  （`git status --porcelain` 应为空）再下结论。
- `git rev-parse HEAD`

车道实测（供你核对，**不要**自己重跑变异）：negverify **42/42 全部如期变红** + 一条手工变异（崩溃判据退回枚举名单 → r13 如期变红、还原后复绿）（**崩溃识别已按形态重写**），
被测文件 sha256 见报告附的终态 sha，运行前后逐字节一致；
扩大回归 `tests/skills + test_recap_scan_signals + test_board_manifest_contracts` = **595 passed**；
真实 CLI 探针 84/84。

## 输出格式

- 第一行：「BLOCKER/HIGH 清零：是/否（就计数取值口径而言）」。
- 逐项 ✅/⚠️/❌ + `file:line`。**新问题不限于「本卡引入」**，存量未闭合的也请报并标注。
- 写出你实际跑出的 pytest 结果与 `git rev-parse HEAD`。
- 报告一次给出；先写正文再补过程。
