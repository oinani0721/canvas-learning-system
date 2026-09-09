# 独立复核请求 — CARD-SKILL-PORT-LINT（BATCH-2026-09-07-第十三批 / 车道 U4 / round-10）

## 一 背景与最小读取面（只读这些，不要扩大）

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts`
分支 `card/u4-hosts`。**本轮绑最终 HEAD**：`fcab3216` → **`f4dacfe3`**。

轮次说明：r5 是 D-15 的 5 轮上限，用户随后授权继续，故有 r6/r7/r8/r9。
本轮唯一代码 commit `f4dacfe3` 是按你 r9 的 5 HIGH + 2 MEDIUM + 3 LOW 全部整改。

**请只读下面这些**：

1. r8 之后的整改 diff（**本轮重点**）：`git -C <树根> diff b5d0e78d f4dacfe3 -- . ':(exclude)_bmad-output'`
2. 全区间代码 diff：`git -C <树根> diff 9303201a f4dacfe3 -- . ':(exclude)_bmad-output'`
3. 新测试全文：`backend/tests/skills/test_skill_portability_lint.py`
4. 你上一轮的报告：`_bmad-output/审查/codex-review-CARD-SKILL-PORT-LINT-r8.md`

**不要读**：`quiz-answer/SKILL.md` 正文（3076 行，本卡一字节未改）、live vault 下的文件、
其它车道的卡文。

## 二 round-9 十一条意见的处置（十条整改，一条明确不修并登记）

11 个反例**当场 11/11 全复现**。你指出的 2 条新回归与 1 条「r8 已报未修」都成立。

| 你的意见 | 整改 |
|---|---|
| **HIGH-1a** 复合语句续接子句被切断 | 认走之前先看下一行是不是 `elif`/`else`/`except`/`finally`/`case` |
| **HIGH-1b** 200 行硬上限（r8 已报、我漏修） | **去掉行数上限** —— `_py_needs_more()` 的剪枝已保证 O(n)，quiz-answer（2746 行 fence 块）实测 0.09s |
| **HIGH-2** 转义掩码作用于 span 内部 | 掩码只用于定位 **opening**；closing 在原串上找（CommonMark：span 内反斜杠是普通字符） |
| **HIGH-3a** closing 允许任意引用前缀 | closing 的引用深度必须**等于** opening 的 |
| **HIGH-3b** 列表→引用嵌套 / body 前缀 | 开启正则认两种顺序；body 按 `_CONTAINER_PREFIX_RE` 整体剥 |
| **HIGH-4** 常量与实际赋值脱钩 | `Expr` 移出 `_STATEMENT_NODES`（树上实测 0 处受影响） |
| **HIGH-5a** `_` `:` 也是合法 shell 词的一部分 | `_SPAN_SEP_CHARS` **去掉全部 ASCII 标点**，只留空白与全角标点 |
| **HIGH-5b** 散文里裸写、无反引号 | 含 `/tmp` 的**词里带反斜杠**即登记 |
| **HIGH-5c** 跨物理行的 code span | 新增 `_prose_segments()` 把连续散文并成段再找 span（`_fence_blocks` 对散文逐行产出，两行都拿不到完整 span） |
| **MEDIUM-2** `CLS_BACKEND_URL=` 架空缺省形态 | **新增第九条判据** `check_url_override`，全树实测 0 |
| **LOW-1/2/3** | 安全锚补前缀；分隔符表补中文引号 `“”‘’『』〔〕`；越界消息补「来源翻转 ≠ 物理债增减」 |

**MEDIUM-1（同一来源内部抵消）⛔ 明确不修**，登记为设计取舍：唯一修法是候选带
**物理行号**，而那会让基线对任何行号移动都报红 —— 你自己在 LOW-3 警告过「来源翻转
的报错会误导交接」，行号会把这个问题放大一个量级（U5-B 每插一行就全表红）。
**任何不带位置的多重集都有这个性质**，这是判据形态的固有代价。如实声明，不假装覆盖。

**整改期间的两次自查（请一并复核）**：
1. `_prose_segments()` 第一版把 fence **标记行**也并进段 ⇒ 相邻两个 ``` 凑成假的跨行
   span，树上误报 board-recap `:135` / quiz-answer `:165`。标记行虽按散文产出（为了让
   裸 token 扫到 info string 上的路径），但它是段边界。
2. 形态表两个安全对照选错了：`elif (P := "/tmp/cls-exam/x")` 的海象、以及孤立的
   `"/tmp/cls-exam/x"` 表达式，**本来就该红**（判据行为正确，是对照没选对）。

判据 8 → **9 条**，测试 103 → **114**，形态表 15 → **25 行**。

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
