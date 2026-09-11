# 独立复核请求 — CARD-SKILL-PORT-LINT（BATCH-2026-09-07-第十三批 / 车道 U4 / round-13）

## 一 背景与最小读取面（只读这些，不要扩大）

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts`
分支 `card/u4-hosts`。**本轮绑最终 HEAD**：`fcab3216` → **`51282213`**。

轮次说明：r5 是 D-15 的 5 轮上限，用户随后授权继续，故有 r6/r7/r8/r9。
本轮唯一代码 commit `51282213` 是按你 r9 的 5 HIGH + 2 MEDIUM + 3 LOW 全部整改。

**请只读下面这些**：

1. r8 之后的整改 diff（**本轮重点**）：`git -C <树根> diff 2c2b6471 51282213 -- . ':(exclude)_bmad-output'`
2. 全区间代码 diff：`git -C <树根> diff 9303201a 51282213 -- . ':(exclude)_bmad-output'`
3. 新测试全文：`backend/tests/skills/test_skill_portability_lint.py`
4. 你上一轮的报告：`_bmad-output/审查/codex-review-CARD-SKILL-PORT-LINT-r8.md`

**不要读**：`quiz-answer/SKILL.md` 正文（3076 行，本卡一字节未改）、live vault 下的文件、
其它车道的卡文。

## 二 round-12 十一条意见的处置（全部整改）

11 个反例**当场全复现**。

⛔ **LOW-2 你抓到的是一条诚信问题**：我在 r11 的 commit message 里声称新增了
`test_opaque_baseline_entries_are_content_bound`，而它**不在提交里**（`grep -c` = 0）。
根因：我在「用 `repr` 重写形态表」时删除了一段区间，把那个测试一并删掉，commit
message 没跟着改。已补回，并在其 docstring 里写下这条教训。

| 你的意见 | 整改 |
|---|---|
| **HIGH-1** 探针拒绝多行 `elif` 头与单行 suite | **去掉探针** —— 它本来就是多余的：直接继续累加即可，`_py_strings` 自己会在整条语句完整时成功、`_py_needs_more` 会在「根本不是 Python」时叫停。同时跳过同级注释 |
| **HIGH-2** NBSP/U+3000 被 `isspace()` 放行；`split(" ")` 错拆引号内空格 | 只认 **ASCII 空白**；新增 `_shell_words()` 按 shell 词边界切 |
| **HIGH-3** 散文仍跨列表项拼段 | 列表 marker / HTML 注释纳入块边界；**且块边界行本身是新块首行，不能 `continue` 掉**（整改中踩到） |
| **HIGH-4** opening 允许任意缩进 | 无容器前缀时缩进 ≥4 是缩进代码块，不开 fence |
| **HIGH-5** `AnnAssign` 覆盖不算重复赋值 | 计数纳入 `AnnAssign` |
| **HIGH-6** 散文裸 shell 的相邻引号拼接 | 散文分支入口不再要求「行内有记号」；含 `/tmp` 的词里引号 >2 即登记 |
| **MEDIUM-1** 多字符列表 marker 下 fence 闭不上 | `open_indent` 取 **fence marker 的列位置**；closing 正则收回 `^[ \t]*`。⛔ 顺带发现 **r11 那次替换其实失败了**，正则一直是绝对 `^ {0,3}` |
| **MEDIUM-2** `unset` 多变量 / `-f` 误报 | 覆盖多变量与选项；`unset -f` 只删同名函数 ⇒ 排除。**残余登记**：`unset C'LS'_BACKEND_URL` 这类引号拼接出的变量名，正则认不出 |
| **LOW-1** 耗时哨兵未清缓存 | 断言前 `cache_clear()` |
| **LOW-2** 声称的测试不在提交 | 补回（见上） |
| **LOW-3** 重复赋值对无关变量误报 | 只在「同名多次赋值**且其中至少一次的值含 `/tmp`**」时登记 |

判据仍 9 条，测试 132 → **142**，形态表 42 → **51 行**。

## 三 请按重要性排序回答的问题

1. **本轮整改有没有引入新缺陷**？（**前五轮每轮都有我引入的回归，这一问最重要**）重点：
   - 去掉探针后，续接判定只剩「下一非空行是不是续接词 / 缩进是否更深」。有没有形态
     让它把**不相干**的后续语句吞进同一单元（成本或误报方向），或反过来仍切早？
   - `_shell_words()` 的正则 `(?:[^\s"']|"[^"]*"|'[^']*')+` 是手写分词。转义引号
     (`\"`)、未闭合引号、`$'...'`、反引号内的空格会怎样？
   - 块边界现在含列表 marker —— fence **内**以 `- ` 开头的代码行会不会被误判为边界？
     （散文段与 fence 体是分开处理的，但请复核这个假设。）
   - `open_indent` 取 fence marker 的列位置：容器前缀含 tab 时列数怎么算？
   - 续接判定现在用 `ast.parse(chunk + line + pad + "pass")` 做探针。这个探针本身有没有
     假阳/假阴？（`pad` 取「该行缩进 + 4」是猜的；`match`/`case` 的软关键字；
     `try/except*`；chunk 末尾已有 `else` 时再接 `elif`）
   - `_strip_quote_prefix` 的迭代剥：列表 marker 与引用交替出现、marker 后跟 tab、
     有序列表 `10.` 这类多字符 marker，会不会剥多或剥少？
   - `lru_cache` 按 body 文本缓存 —— 判据是纯函数吗？（`_parse_units` 依赖的
     `_py_strings`/`_sh_words`/`_quiet_parse` 都不读外部状态，但请复核）
   - 内容指纹用 `strip()` 后的 sha8：**同一行内前后空白的变化不会改指纹**，这算不算
     一个新的静默面？
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
