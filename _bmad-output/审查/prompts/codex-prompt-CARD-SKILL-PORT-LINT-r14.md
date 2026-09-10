# 独立复核请求 — CARD-SKILL-PORT-LINT（BATCH-2026-09-07-第十三批 / 车道 U4 / round-14）

## 一 背景与最小读取面（只读这些，不要扩大）

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts`
分支 `card/u4-hosts`。**本轮绑最终 HEAD**：`fcab3216` → **`7dcf96f2`**。

轮次说明：r5 是 D-15 的 5 轮上限，用户随后授权继续，故有 r6/r7/r8/r9。
本轮唯一代码 commit `7dcf96f2` 是按你 r9 的 5 HIGH + 2 MEDIUM + 3 LOW 全部整改。

**请只读下面这些**：

1. r8 之后的整改 diff（**本轮重点**）：`git -C <树根> diff 51282213 7dcf96f2 -- . ':(exclude)_bmad-output'`
2. 全区间代码 diff：`git -C <树根> diff 9303201a 7dcf96f2 -- . ':(exclude)_bmad-output'`
3. 新测试全文：`backend/tests/skills/test_skill_portability_lint.py`
4. 你上一轮的报告：`_bmad-output/审查/codex-review-CARD-SKILL-PORT-LINT-r8.md`

**不要读**：`quiz-answer/SKILL.md` 正文（3076 行，本卡一字节未改）、live vault 下的文件、
其它车道的卡文。

## 二 round-13 的处置 —— 以及一个**用你七轮数据做的设计决策**

你 r13 的 11 条全部复现、全部整改。但更重要的是这个：

### 2.1 八轮的收敛数据

| 轮次 | HIGH | 我自己整改引入的新回归 | 占比 |
|---|---|---|---|
| r7 | 6 | 3 | 50% |
| r8 | 5 | 3 | 60% |
| r9 | 5 | 2 | 40% |
| r10 | 6 | 3 | 50% |
| r11 | 9 | 3 | 33% |
| r12 | 6 | 5 | 83% |
| r13 | 6 | 5 | 83% |

**HIGH 数量七轮没有下降，新回归占比在上升。** 根因始终是同一件事：判据 ④~⑨ 要做的
是「静态判断一条路径最终指向哪」，那需要 markdown + shell + python **三个真解析器**；
手写近似每补一个边界就开一个新边界。

### 2.2 ⇒ 新增**第十条判据 = 兜底网**（`tmp_block_fingerprints`）

含 `/tmp` 的 fence 块钉**整块指纹**，含 `/tmp` 的散文行钉**行指纹**。
**不做任何语义分析** —— 没有解析、没有正则边界、没有缩进猜测。

**立它的实测依据**：
- 对形态表 51 个反例：**45 个可区分**，分不开的 6 个全是不含 `/tmp` 的 URL/`unset` 形态；
- 对你 r13 的 9 条：**九条判据全部看不见，兜底网区分 8/9**（第 9 条 `${OTHER:-…:8011}`
  不含 `/tmp`，已补进第九条判据）；
- 树上代价 **12 项**。

它与前九条**互补不取代**：那九条告诉你「是哪一类问题」，这条保证「块变了就红」。
你 r13 MEDIUM-3 的「多行 opaque 记录只绑首行 ⇒ 换第二行仍静默」由它直接封住。
新增 `_NET_ONLY_FORMS`（8 行，全是九条全瞎的形态）+ 两条承重断言，把「45/51」和
「兜底网自己不能失效」钉成可执行断言。

### 2.3 r13 其余整改

| 你的意见 | 整改 |
|---|---|
| **HIGH-3** 坐标失真（40 空格即漏） | 用 `finditer` 拿真实坐标 |
| **HIGH-4** closing 把 opening 自身缩进算成额度 | 阈值 = 3 + **容器 marker 宽度**（CommonMark 的 3 空格是绝对的，列表/引用内只是整体右移 marker 宽度） |
| **MEDIUM-1** `unset -f` 排除条件越过命令边界 | 改判定函数：选项只看紧跟 `unset` 的，变量列表止于 `;&\|` |
| **MEDIUM-2** URL 放行没绑定约定变量 | 含 `8011` 但不含 `CLS_BACKEND_URL` 即登记 |
| **LOW-2** 指纹测试没检查正式消费端 | 直接对 `check_opaque_tmp()` 发问：给「行号对、指纹错」的基线必须红 |
| **HIGH-1/2/5/6、MEDIUM-3** | **由兜底网接住**（实测 8/9），不再逐个补语义判据 |

判据 9 → **10 条**，测试 142 → **152**。

## 三 请按重要性排序回答的问题

1. **第十条判据（兜底网）本身有没有缺陷**？这一问最重要 —— 它是本轮的设计决策：
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
