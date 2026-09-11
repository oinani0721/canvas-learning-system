# 独立复核请求 — CARD-SKILL-PORT-LINT（BATCH-2026-09-07-第十三批 / 车道 U4 / round-21）

## 一 背景与最小读取面（只读这些，不要扩大）

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts`
分支 `card/u4-hosts`。**本轮绑最终 HEAD**：`fcab3216` → **`55330069`**。

轮次说明：r5 是 D-15 的 5 轮上限，用户随后授权继续，故有 r6/r7/r8/r9。
本轮唯一代码 commit `55330069` 是按你 r9 的 5 HIGH + 2 MEDIUM + 3 LOW 全部整改。

**请只读下面这些**：

1. r8 之后的整改 diff（**本轮重点**）：`git -C <树根> diff 8c34481a 55330069 -- . ':(exclude)_bmad-output'`
2. 全区间代码 diff：`git -C <树根> diff 9303201a 55330069 -- . ':(exclude)_bmad-output'`
3. 新测试全文：`backend/tests/skills/test_skill_portability_lint.py`
4. 你上一轮的报告：`_bmad-output/审查/codex-review-CARD-SKILL-PORT-LINT-r8.md`

**不要读**：`quiz-answer/SKILL.md` 正文（3076 行，本卡一字节未改）、live vault 下的文件、
其它车道的卡文。

## 二 round-20 的处置

⛔ 你指出的 HIGH-1 是**同一个根因的第三个消费端**：r18 修「长单元源码保住」、
r19 修「预筛用整段源码」、r20 才发现 `tmp_targets` 那圈还停在叶常量，而同一个函数下面
`starts` 那圈从 r11 起就用折叠值了。我连着三轮每轮只修一个读者。

| 你的意见 | 整改 |
|---|---|
| **HIGH-1** 折叠常量的重复赋值漏检（bytes 同形态） | `tmp_targets` 改用 `_fold_str()` 折叠值 |
| **HIGH-2** 列表退出被当 closing | ⛔ 不修，归分块卡（你本轮确认该处置正确） |
| **MEDIUM-1** 注释剥离不识别引号/参数展开 | 换 `_strip_sh_comment()`：POSIX 词首规则 + 引号状态机 |
| **MEDIUM-2** 截 query/fragment ≠ 只看主机端口 | 判准换成「端口号本身必须**落在** `${CLS_BACKEND_URL:-…}` 这次展开里」 |
| **MEDIUM-3** `env` 双向缺陷 | 拆 `_env_clears_url()`：长选项/粘连要抓；**逐命令段**判 + 只认单引号 `-c` 脚本且脚本里真出现该变量 |
| **MEDIUM-4** `decode(…, "replace")` 身份损失 | 拆 `_fold_const()` 保类型 → 整条折完解**一次** → `backslashreplace` |
| **MEDIUM-5** code span 空白归一化 | ✅ **在本卡就地修**（照你说的，这条不需要容器栈） |
| **LOW-1/2/3** | 补 bytes 叶收集断言；新增 `test_r20_judge_branches_are_load_bearing`（5 组 + 等结构安全对照）；哨兵改量整条 `dynamic_tmp_join_lines()`，`_py_strings` 加缓存（存 tuple、返回复制 list） |

**回退验证**：9 条整改逐条单独回退，全部让我声称的那一条断言变红，且红的是指名那条。
**自我发现的探针错误**：MEDIUM-4 首版探针写成 `b"mp/\xff/../x"`，`posixpath` 归一化把
区分字节的那段消掉，两版都得 `/tmp/x` —— 探针避开了显形点，差点判成已修好。

判据仍 **10 条**，测试 156 → **157**。

## 三 请按重要性排序回答的问题

1. **「折叠口径」还有没有第四个消费端**？（这一问最重要）
   与其下一轮再被你找出一个，不如这轮**把名单一次列全**：请枚举模块里**全部**
   「判断某个表达式/文本含不含 `/tmp`（或含不含目标变量）」的判定点，逐个说明它用的是
   **叶常量**、**折叠值**、还是**源码字面**，并指出哪些应该统一而没有统一。
   同样的问法也适用于「注释剥离」——`_strip_sh_comment()` 现在只有 URL 判据在用，
   其余判据（可疑行、opaque、动态拼接）看的是原始行，这是不是又一处口径分叉？
   - 预筛改用「整段源码解析出的全部字符串」后，成本涨了多少？（每个单元多一次 parse）
   - `_fold_str()` 折 bytes 用的是 `decode("utf-8", "replace")`。非 UTF-8 字节序列
     被替换成 U+FFFD 后，会不会把两个不同的 bytes 常量折成同一个字符串？
   - URL 判定重写后的 9 条形态之外，`${X-…}`（无冒号）、`${X:?}`、数组下标、
     `printf` 拼 URL 等形态呢？
2. **本轮五处整改有没有引入新缺陷**？重点看三处新写的代码：
   - `_strip_sh_comment()` 是个**手写状态机**（引号 / 反斜杠 / 词首判定），
     反引号命令替换、`$'…'`、未闭合引号、行尾续行时它的行为对吗？
   - `_normalize_span()` 改的是 `_backtick_spans()` 的**全部**调用点（越界候选、opaque、
     交接），只有两处传 `normalize=False`。归一化会不会让某个原本能区分的形态变成等值？
   - `_py_strings` 的 `functools.lru_cache`：它真的是纯函数吗？返回的 list 是新对象，
     但调用方拿到后还有别的写法能污染缓存吗？
3. **`_env_clears_url()` 只认单引号 `-c` 脚本**——这是为了压掉「外层已展开」的误报。
   但 `env -i bash -c $'curl …'`、`env -i bash -c \\"…\\"`、以及把脚本放进变量再
   `env -i bash -c "$SCRIPT"` 这些形态呢？漏检面有多大，值不值得在本卡处理？
   它们都指向同一件事：本模块不是完整的 CommonMark 容器栈。请给一个**整体判断** ——
   在**当前树的实际写法**下（9 份 SKILL.md 都不用嵌套容器、不用 setext、不用 HTML 块），
   这些缺陷的可触发面是「理论存在」还是「随手一改就中」？
   我需要这个判断来决定它该登记还是该另立卡。
2. **本轮五处整改有没有引入新缺陷**？（前六轮每轮都有我引入的回归）
   - 长单元只贡献 `Counter(长) - Counter(短)`。有没有形态让**该出现的候选被差掉**
     （漏检方向）？例如同一个越界路径在短单元里已出现一次、长单元里出现两次。
   - 循环扩张时 `seen` 逐轮累积。中途某次扩张失败（`grown is None`）后跳出，
     已收的 delta 还对吗？
2. **fence 额度这是第五次修正**，请再找双向反例（CommonMark 闭合而本模块不闭合，或反过来）。
   - 并集会让候选变多。有没有形态让它**多到掩盖真问题**（例如某个假候选恰好占掉了
     基线里的位置），或让树上出现新的误报？
   - 长单元的累加上限是 40 行、且只在「下一非空行像续接词」时触发。有没有合法形态
     跨越 40 行，或者续接词前隔了很多体内行？
   - 收了长单元后 `j = kk` 跳过它覆盖的行 —— 短单元与长单元**重叠**的那几行，候选会
     不会被计两次而影响多重集基线？
2. **fence 额度与 closing 判定这次对了吗**？（同一处我改了四轮）
   - 现在的规则：closing 缩进 ≤ 容器内容基线 + 3，无容器时基线 = 0。
     请找**同时满足**「CommonMark 会闭合而本模块不闭合」或反过来的输入。
   - 容器前缀含 tab、`>` 与列表 marker 交替、marker 后跟 tab 时，展开列宽算得对吗？
2. **HIGH-3 的续接词区分对了吗**？`else`/`try`/`finally` 要冒号，
   `elif`/`except`/`case` 只要后面有非空白。有没有合法 Python 被这条切断，
   或有没有 heredoc 结束标记被它当成续接？
3. **散文改按段绑指纹**后：段边界（空行/ATX 标题/列表 marker/HTML 注释/setext）
   有没有形态让**该分的没分**（前段夺走后段 span）或**不该分的分了**（跨行 span 被切断）？
4. **兜底网的分块修正到位了吗**？
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
