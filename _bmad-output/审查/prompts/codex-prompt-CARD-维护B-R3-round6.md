# Codex 定向复核 · CARD-维护B-R3 round-6（只审计数取值口径）

你是对抗复核者。本卡 round-5 你判「清零：否 · 0 BLOCKER / 10 HIGH（8 实现 + 2 自证）」。
车道复核：**8 条实现侧全部属实**（10/10 探针放行），已整改；
**1 条被驳回**（#9b 称区间门是假门——实测诊断上下文是**挖空之后**的行、
区间段已成空格，两条诊断各自只含自己的端点 token，门成立）。

⚠️ **口径声明**：卡文限「最多 3 轮」，本轮为第 6 轮、已超限，需用户追认。
车道判断是「上限约束审查轮次、不约束修复；留着已复现的洞不修更糟」。
请照常严格审，不必迁就。

⚠️ 上三轮你**遵守了「不要跑 negverify」**（该脚本会原地改写被测源码；round-2 你
跑它时被打断，把变异留在工作树里，导致随后的 pytest 测了污染文件、报 240/15）。
请本轮继续遵守。

## ⛔ 车道本轮自曝：证伪了自己写在结论里的中心断言

round-5 收口时车道在验收单结论里写：「五轮全部 finding 在『先渲染再核数』的设计下
会**同时消失**」。round-6 把 `_visible_text()` 真正实现出来实测：**10 条只闭合 3 条**。
那是一个**未经检验就写进结论**的断言，已按实测更正为 3/10，并重新分类为四类异质缺陷
（源码≠渲染 ~30% / 封闭表 / 判据正则过窄 / 语义缺失）。
证据 `_bmad-output/审查/evidence-maintb-r3/o-round6-hypothesis-test.txt`。
**请一并检查更正后的分类是否仍有过宽之处。**

## round-5 八条实现 HIGH 的整改

| 你的判词 | 整改 |
|---|---|
| inline-code 挖空吞掉量词 | **未修**——`` ` ` `` 内是**有意豁免**的字段值（E2 设计选择），改它需单独裁决。如实登记 |
| 裸 `共有/总计/合计` 句式门失锚 | 其后接**任一数词样字符**（原只认 ASCII 数字）；定义下移以引用定界集 |
| 解实体晚于全角转换 | `_visible_text()` 内**先解实体再转全角**（反了 `&#xff19;` 永远停在 `９`） |
| 千分位后三位内部不可跨连接字符 | 由 `_visible_text()` 剥标签统一解决 |
| range 缺 `～/〜/−/‑` | 分隔表补齐（仍是封闭表） |
| 有符号整数按无符号幅值入池 | 负数计数**恒 FAIL**（scan 计数均非负） |
| 两张定界闭表仍能零校验 | 量词表补 `门套对场部只支株棵`；仍是封闭表，如实登记 |
| 渲染包装让可见数字消失/重锚 | wikilink 只在**有别名**时挖空目标；标签由 `_visible_text()` 剥除 |

新增 `_visible_text()`（实体→全角→剥标签→wikilink 显示文本→去零宽→去强调标记），
在两个消费点**最前面**跑一次，此后所有判据在同一文本空间工作。

## ⛔ 车道自曝的第二条空变异

`html.unescape` 从 `_normalize_number_seps` 移进 `_visible_text` 后，指向旧位置的
`survivor-22` 锚点**仍能匹配**但已禁不掉任何东西 ⇒ 空变异。脚本报「仍全绿 = 不承重」
才暴露，已重指并把规则写进脚本铁律 4。**请特别检查其余 28 条有没有同型空变异。**

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
survivor-15…29 十五条新变体的替换内容是否真的禁掉了该性质的全部防线。

## 请回答

1. 还有没有别的路径能让「进池比对的值」≠「读者在渲染后看到的数」？
2. `_NUMERAL_LIKE_CHARS`（定界）、`_D2_QUANT`（量词）、`_CJK_NUM`（赋值）三张封闭表，
   车道在验收单 §五之三 的登记诚实吗？有没有被低估的？
3. 「定界要宽、赋值要窄」这个不变式是否在两个消费点都成立？
4. 新门有无空洞断言或比实现宽的措辞？

## 命令（只跑这一条 pytest + 一条 git）

- `cd backend && PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest
  tests/regression/test_recap_scan_signals.py -q -p no:cacheprovider`
  —— 开工基线 249，现应为 **259**。若你得到别的数字，请先检查工作树是否 clean
  （`git status --porcelain` 应为空）再下结论。
- `git rev-parse HEAD`

车道实测（供你核对，**不要**自己重跑变异）：negverify **29/29 全部如期变红**，
被测文件 sha256 前缀 `fe8459f4bc76`，运行前后逐字节一致；
扩大回归 `tests/skills + 两个 regression 文件` = **591 passed**；
真实 CLI 探针 70/70。

## 输出格式

- 第一行：「BLOCKER/HIGH 清零：是/否（就计数取值口径而言）」。
- 逐项 ✅/⚠️/❌ + `file:line`。**新问题不限于「本卡引入」**，存量未闭合的也请报并标注。
- 写出你实际跑出的 pytest 结果与 `git rev-parse HEAD`。
- 报告一次给出；先写正文再补过程。
