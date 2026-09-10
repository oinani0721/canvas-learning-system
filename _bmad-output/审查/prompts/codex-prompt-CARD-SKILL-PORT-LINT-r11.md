# 独立复核请求 — CARD-SKILL-PORT-LINT（BATCH-2026-09-07-第十三批 / 车道 U4 / round-11）

## 一 背景与最小读取面（只读这些，不要扩大）

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts`
分支 `card/u4-hosts`。**本轮绑最终 HEAD**：`fcab3216` → **`8386e41f`**。

轮次说明：r5 是 D-15 的 5 轮上限，用户随后授权继续，故有 r6/r7/r8/r9。
本轮唯一代码 commit `8386e41f` 是按你 r9 的 5 HIGH + 2 MEDIUM + 3 LOW 全部整改。

**请只读下面这些**：

1. r8 之后的整改 diff（**本轮重点**）：`git -C <树根> diff f4dacfe3 8386e41f -- . ':(exclude)_bmad-output'`
2. 全区间代码 diff：`git -C <树根> diff 9303201a 8386e41f -- . ':(exclude)_bmad-output'`
3. 新测试全文：`backend/tests/skills/test_skill_portability_lint.py`
4. 你上一轮的报告：`_bmad-output/审查/codex-review-CARD-SKILL-PORT-LINT-r8.md`

**不要读**：`quiz-answer/SKILL.md` 正文（3076 行，本卡一字节未改）、live vault 下的文件、
其它车道的卡文。

## 二 round-10 十条意见的处置（全部整改）

8 个反例**当场全复现**（含 LOW-3 的二次增长：1000/2000/4000 行 = 0.10/0.37/1.40s，
与你实测吻合）。你指出的 3 条新回归都成立。

| 你的意见 | 整改 |
|---|---|
| **HIGH-1** closing 只查右边界 | closing run 两端都查（CommonMark 要求恰好等长） |
| **HIGH-2** 整体剥容器前缀删掉 Python 缩进 | `>` 后**只吃一个空格**（CommonMark：marker 后至多一个空格属于标记） |
| **HIGH-3** 只看紧邻下一行 | 新增 `_has_continuation_after()`：跳过整个缩进块再看第一个**同级**行 |
| **HIGH-4** 散文合并不守块边界 | **空行断段**；fence 标记行判定加 `not _is_inline_span(...)`（你指出判断范围过宽） |
| **HIGH-5** 表里仍有 `*` 与新增的中文引号 | `_SPAN_SEP_CHARS` **只留空白与中文句读**。代价：树上三行成保守误报并**登记**（`**粗体**` 紧贴 span 边界） |
| **HIGH-6** 预筛只看源码字面 | 改用 `_parse_units()` **解析出的字符串**预筛，源码字面只作兜底 |
| **MEDIUM** 漏 `unset` | 正则一并覆盖 |
| **LOW-1** r9HIGH-1a 不承重 | 换成「表达式**必须依附** `elif` 头才能解析」的形态（`elif ("/tmp/cls-exam/" "../x") == q:`） |
| **LOW-2** r9HIGH-3b 容器样本错 | 换成同一列表项内的合法嵌套（首行 `- > `，后续 `  > `） |
| **LOW-3** O(n) 声明不成立 | **更正声明**：单元内是 **O(k²)**。可接受的理由是**单元长度**有界（树上最长 278 行），不是块长度有界；新增 `test_parse_unit_length_on_current_tree` 把这个前提钉住（>400 行即红） |

**如实声明的两处代价**（请一并复核是否值得）：
1. `OPAQUE_TMP_BASELINE` 不再全空 —— quiz-answer `:205`、start-exam-board `:188`/`:577`
   三行是 `**粗体**` 造成的保守误报。不把 `*` 加回表里的理由：`*` 同样能属于合法
   shell 词，表里多一个字符 = 多一条放行。**漏检不可接受，误报可以登记**。
2. 函数**默认参数**里的合规常量（`def f(p="/tmp/cls-exam/x")`）会被第六条判为动态
   （常量父链是 `arguments`，不是安全停止点）。树上实测 0 处，登记为保守误报方向。

形态表 25 → **32 行**，测试 114 → **122**。

## 三 请按重要性排序回答的问题

1. **本轮整改有没有引入新缺陷**？（前三轮每轮都有我自己引入的回归，这一问最重要）重点：
   - **去掉行数上限**后，`_py_needs_more()` 是唯一的终止条件。有没有输入能让它一直
     判「还没写完」直到块尾，从而把整块吞成一个单元（漏检：块内其它语句的候选全丢）？
   - `_prose_segments()` 的段边界只认 fence 标记行。列表项之间的空行、表格、HTML 块
     会不会让不该相邻的两行拼出假 span（误报）或让该相邻的两行被拆开（漏检）？
   - `_backtick_spans()` 现在是手写扫描：opening 看掩码、closing 看原串。有没有形态
     让它比 CommonMark **多提**或**少提** span？
   - `_STATEMENT_NODES` 去掉 `Expr` 后，`With` / `withitem` / `comprehension` /
     `keyword` / `Starred` / `NamedExpr` / 装饰器 / 默认参数里的常量会怎样？
   - `codeop.compile_command()` 的语义边界：它对 `\` 续行、`if/else` 分支、装饰器、
     异步语句的「完整/不完整」判定，与 `_parse_units` 的贪心「第一次成功即认」
     组合起来，有没有形态会把**该合并的语句拆开**（漏检方向）？
   - `_backtick_spans()` 的掩码只处理 `\` + 单字符。CommonMark 的转义规则比这复杂
     （只有 ASCII 标点可被转义），有没有形态让掩码**多掩**或**少掩**从而丢 span？
   - `_FENCE_OPEN_RE` 允许 `(?:>\s*)*` 与列表前缀的**组合**，`_strip_quote_prefix()`
     按开启行深度剥 —— 深度不一致（body 比开启行多/少一层 `>`）时会怎样？
   - `_SPAN_SEP_CHARS` 是枚举白名单。哪些真实出现在中文技术文档里的分隔符不在表内，
     会造成误报（可接受）或漏报（不可接受）？
2. **来源前缀（`fence:` / `prose:`）**：`_fence_blocks` 现在把 fence 标记行按散文产出，
   所以同一物理路径可能一次记 `prose` 一次记 `fence`。这个归属会不会随无关的格式调整
   翻转，从而产生**令人误解**的红？U5-B / U6 rebase 时读得懂吗？
3. **八条判据合起来是否仍有等计数缺口**？九项计数不变、五个集合都不变，但实际引入
   可移植性债的替换形态。
4. **哪条断言不承重**？特别看形态表 15 行（指名判据是否选对？安全对照是否只差一处？）
   与本轮两处内存变异验证。
5. **收尾判断**：残余风险面是否都已如实声明？还有没有**未声明的**、可静态确定的漏检？

## 四 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给出 `file:line` + 一句话说明**在什么输入
或什么改动下这条会出问题**。没有问题的维度请明确写「未发现」，不要省略。
最后单独给一句结论：本轮 BLOCKER 与 HIGH 各几条。

## 五 边界

- 只读，不要修改任何文件；不要连任何数据库或网络服务。
- 不要跑 pytest（`sandbox` fixture 会复制大文件）。可直接用树内
  `backend/.venv/bin/python` 动态加载被测模块，调用 `_body_counts()` / `_fence_blocks()` /
  `_is_inline_span()` / `_strip_quote_prefix()` / `_backtick_spans()` /
  `_has_embedded_span_near_tmp()` / `_py_needs_more()` / `_sh_needs_more()` /
  `_parse_units()` / `_py_strings()` / `_sh_words()` / `_fold_str()` / `_quiet_parse()` /
  `_has_dynamic_tmp_join()` / `escaping_tmp_paths()` / `suspicious_tmp_lines()` /
  `dynamic_tmp_join_lines()` / `parent_dir_prose_lines()` / `opaque_tmp_lines()` /
  `_script_counts()` / `check_handoff_constants()` / `_discover_out_of_scope_8011()` 等纯函数。
- 不评二线宿主（Codex / OpenCode / dsh）的可跑性 —— 那是另一张卡的范围。
- 不评 `quiz-answer/SKILL.md` 的内容质量 —— 本卡对它只钉计数、一字节未改。
- 不评 `_bmad-output/` 下的文档措辞。
