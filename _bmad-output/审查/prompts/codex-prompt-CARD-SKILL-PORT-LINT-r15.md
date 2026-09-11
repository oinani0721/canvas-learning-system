# 独立复核请求 — CARD-SKILL-PORT-LINT（BATCH-2026-09-07-第十三批 / 车道 U4 / round-15）

## 一 背景与最小读取面（只读这些，不要扩大）

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts`
分支 `card/u4-hosts`。**本轮绑最终 HEAD**：`fcab3216` → **`7245a67a`**。

轮次说明：r5 是 D-15 的 5 轮上限，用户随后授权继续，故有 r6/r7/r8/r9。
本轮唯一代码 commit `7245a67a` 是按你 r9 的 5 HIGH + 2 MEDIUM + 3 LOW 全部整改。

**请只读下面这些**：

1. r8 之后的整改 diff（**本轮重点**）：`git -C <树根> diff 7dcf96f2 7245a67a -- . ':(exclude)_bmad-output'`
2. 全区间代码 diff：`git -C <树根> diff 9303201a 7245a67a -- . ':(exclude)_bmad-output'`
3. 新测试全文：`backend/tests/skills/test_skill_portability_lint.py`
4. 你上一轮的报告：`_bmad-output/审查/codex-review-CARD-SKILL-PORT-LINT-r8.md`

**不要读**：`quiz-answer/SKILL.md` 正文（3076 行，本卡一字节未改）、live vault 下的文件、
其它车道的卡文。

## 二 round-14 十条意见的处置（全部整改）

你 r14 报 **HIGH 1 / MEDIUM 4 / LOW 5** —— HIGH 从上一轮的 6 降到 1，是八轮来第一次
显著收敛。你独立复核确认的三个数字（`_NET_ONLY_FORMS` 8/8、指名形态表 51/51、45/51
成立）我照收；**其中一条我写错了并已更正**：分不开的六例不是「全归 URL/unset」，
实测是**四例 URL/`unset` + 两例 Python `"/t"`+`"mp/…"` 拼接**。断言随之从
「必须不含 `/tmp`」改成「必须能被别的判据接住」——后者才是真正要保证的性质。

| 你的意见 | 整改 |
|---|---|
| **HIGH-1A** 真实 tab 开头的 ``` 提前闭合围栏 | 缩进改按 **tab 展开后的列数**（CommonMark 就是按列，我原先按字符数） |
| **HIGH-1B** 把一行移进/移出引用块对指纹静默 | 指纹改用**原文行**（含容器前缀）——剥过前缀的 body 里 `> P=…` 与 `P=…` 完全一样 |
| **MEDIUM-1** `strip()` 删掉有 shell 语义的尾随空格 | 指纹**不 strip**，只归一化行尾换行符；opaque 也改存原文行 |
| **MEDIUM-2** `_lead` 减法错删列表容器整体缩进（我 r13 引入的） | 退掉减法，阈值以 fence 标记的**列位置**为基准 |
| **MEDIUM-3** URL 只绑名字**子串** | 改**词边界**匹配（`${CLS_BACKEND_URL_OTHER:-…}` 用户配了也不生效 ⇒ 该红） |
| **MEDIUM-4** URL 按物理行 | 改走**逻辑行**（`unset -v \`␊`CLS_BACKEND_URL` 是合法续行） |
| **LOW-1** 新网负控没验正式消费端 | 加断言：给「键对、指纹错」的基线，`check_tmp_blocks()` 必须红 |
| **LOW-2** sha8 只有 32 位（你真的撞出一对） | 加长到 **16 位**（零成本） |
| **LOW-3** 标为 NBSP 的样本实际是 ASCII 空格 | 更正 |
| **LOW-4** 45/51 归因不符 | 见上，断言改写 |
| **LOW-5** `case = 0` 被软关键字正则当续接 | 要求 `case` 后跟模式且行尾冒号（200 行独立 `case = 0` 原先合成一个单元，0.072s vs 0.0016s） |

判据仍 **10 条**，测试 **152**。

## 三 请按重要性排序回答的问题

1. **兜底网的分块修正到位了吗**？这一问最重要（上一轮唯一的 HIGH 就在这里）：
   - 缩进改按 `expandtabs(4)` 的列数、指纹改用**原文行**。这两处有没有新的边界？
     （tab 宽度在 CommonMark 里是 4，但 opening/closing 混用 tab 与空格时呢？
     原文行取自 `raw_lines[start-1 : start-1+len(body)]`，`start` 与 `len(body)` 的
     对应关系在容器嵌套下还成立吗？）
   - 指纹不 `strip()` 之后，**块末尾的空行**、CRLF、文件末尾无换行会不会造成不稳定？
   - 你 r14 指出的「不含 `/tmp` 的块里改用途仍静默」这条边界，我**没有修**（它需要
     跨块的数据流分析）。请复核这条边界的**实际大小**——它是不是比「少数特殊编码」大得多？
2. **其余九条判据本身有没有缺陷**？（前七轮每轮都有我引入的回归）
   - `tmp_block_fingerprints()` 依赖 `_fence_blocks()` 分块。**分块本身错了**的话，
     兜底网会跟着错（例如块边界判错 ⇒ 两个块合并 ⇒ 一个指纹）。有没有形态能让
     **块划分变了但指纹集合不变**？
   - 它只覆盖「含 `/tmp` 的块」。把债写进**不含** `/tmp` 的块（例如先 `T="/t"+"mp"`
     再在另一块用 `T`），是不是一条完整的静默面？（这是它已声明的边界，但请复核
     这个边界的**实际大小**。）
   - 指纹用 `strip()` 后的 sha8。块内**行序调换**、行尾空白、CRLF 会怎样？
2. **r13 那几条「由兜底网接住」的，接得住吗**？我实测 8/9，请独立复核这个数字。
3. **本轮整改有没有引入新缺陷**？（**前六轮每轮都有我引入的回归**）重点：
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
