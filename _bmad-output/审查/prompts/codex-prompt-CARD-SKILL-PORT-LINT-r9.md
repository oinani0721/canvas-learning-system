# 独立复核请求 — CARD-SKILL-PORT-LINT（BATCH-2026-09-07-第十三批 / 车道 U4 / round-9）

## 一 背景与最小读取面（只读这些，不要扩大）

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts`
分支 `card/u4-hosts`。**本轮绑最终 HEAD**：`fcab3216` → **`b5d0e78d`**。

轮次说明：r5 是 D-15 的 5 轮上限，用户随后授权继续，故有 r6/r7/r8/r9。
本轮唯一代码 commit `b5d0e78d` 是按你 r8 的 5 HIGH + 1 MEDIUM + 1 LOW 全部整改。

**请只读下面这些**：

1. r8 之后的整改 diff（**本轮重点**）：`git -C <树根> diff fcab3216 b5d0e78d -- . ':(exclude)_bmad-output'`
2. 全区间代码 diff：`git -C <树根> diff 9303201a b5d0e78d -- . ':(exclude)_bmad-output'`
3. 新测试全文：`backend/tests/skills/test_skill_portability_lint.py`
4. 你上一轮的报告：`_bmad-output/审查/codex-review-CARD-SKILL-PORT-LINT-r8.md`

**不要读**：`quiz-answer/SKILL.md` 正文（3076 行，本卡一字节未改）、live vault 下的文件、
其它车道的卡文。

## 二 round-8 七条意见的处置（全部整改）

你 r8 指出的 5 条 HIGH 里**有 3 条是我 r7 整改自己引入的新回归**，这个判断成立。
根因归并起来是同一件事：我连续三次用「手写近似」去做语言解析器该做的事
（r5 手写扫描器 → r7 手写括号计数 → r7 手写 span 正则），每次都在关掉旧洞时开新洞。

| 你的意见 | 新/旧 | 整改 |
|---|---|---|
| **HIGH-1** `_unit_end()` 把合法语句定短（注释里的 `)` / 字符串里的 `)` / 三引号奇偶 / 缺函数体 / 200 行上限） | 新回归 | 删掉手写计数，改用 **`codeop.compile_command()`**（标准库为 REPL 写的语句完整性判据）：返回 code ⇒ 完整、None ⇒ 还没写完、抛错 ⇒ 根本不是 Python。上一版 docstring 声称「只会定长（误报方向）」，那句话是错的且未经验证，已删。副作用：bash 行立刻判「语法错误」⇒ 不累加 ⇒ 复杂度回到 O(n) |
| **HIGH-2** 转义 opening 反引号丢 span | 新回归 | 匹配前把 `\x` 掩成等长占位符（`_backtick_spans()`），按位置回原串取内容 |
| **HIGH-3a** 列表前缀被用于闭合 | 新回归 | 拆成 `_FENCE_OPEN_RE`（允许列表与引用前缀）/ `_FENCE_CLOSE_RE`（不允许列表前缀） |
| **HIGH-3b** 引用块内 fence 整体当散文 | 既存 | 开启行允许 `> `，body 按开启行的引用深度剥前缀 |
| **HIGH-4** `AnnAssign` 不区分注解与实际值 | 既存 | 上溯时若常量落在 `.annotation` 子树 ⇒ 判为动态 |
| **HIGH-5** 散文裸 shell / 跨行 span | 既存 | 加「**嵌入式** span」判据：span 两侧紧贴非空白。分隔符集 `_SPAN_SEP_CHARS` **刻意不含引号**——命令替换的反引号正是被引号夹住的 |
| **MEDIUM** 候选抵消 | 既存 | 越界 normpath 带**来源前缀**（`fence:` / `prose:`）分开钉。已用你的原反例验证：`prose:/tmp` 缺失 + `fence:/tmp` 新增，两侧都红 |
| **LOW** HIGH-3 断言遗漏 heredoc 背景 | 既存 | 形态表那行裹进 heredoc。内存变异验证：禁掉 `_py_needs_more` 后 heredoc 形态**由红转漏**（承重），纯 python fence 形态**仍红**（考不到）——你这条完全成立 |

**误报侧我自己踩了两次并收紧**（如实声明，请一并复核）：HIGH-5 第一版写成「行内有
反引号」⇒ 误报 board-recap `:139`（那些反引号是 `` `Write` `` 之类正常 markdown）；
第二版写成「同一非空白片段」⇒ 仍误报 `:58` 与 quiz-answer `:98`/`:205`（中文标点不是
`isspace()`）。最终判据 = 嵌入式 span + 中英文标点分隔符集，树上八条全绿。

形态表并入 r8 七个形态（共 15 行），测试 96 → 103。

## 三 请按重要性排序回答的问题

1. **本轮整改有没有引入新缺陷**？重点：
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
