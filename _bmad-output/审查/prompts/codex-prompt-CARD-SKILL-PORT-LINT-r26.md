# 独立复核请求 — CARD-SKILL-PORT-LINT（BATCH-2026-09-07-第十三批 / 车道 U4 / round-26）

## 一 背景与最小读取面（只读这些，不要扩大）

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts`
分支 `card/u4-hosts`。**本轮绑最终 HEAD**：`fcab3216` → **`6540e409`**。

轮次说明：r5 是 D-15 的 5 轮上限，用户随后授权继续，故有 r6/r7/r8/r9。
本轮唯一代码 commit `6540e409` 是按你 r9 的 5 HIGH + 2 MEDIUM + 3 LOW 全部整改。

**请只读下面这些**：

1. r8 之后的整改 diff（**本轮重点**）：`git -C <树根> diff cb4fa9f8 6540e409 -- . ':(exclude)_bmad-output'`
2. 全区间代码 diff：`git -C <树根> diff 9303201a 6540e409 -- . ':(exclude)_bmad-output'`
3. 新测试全文：`backend/tests/skills/test_skill_portability_lint.py`
4. 你上一轮的报告：`_bmad-output/审查/codex-review-CARD-SKILL-PORT-LINT-r8.md`

**不要读**：`quiz-answer/SKILL.md` 正文（3076 行，本卡一字节未改）、live vault 下的文件、
其它车道的卡文。

## 二 round-25 的处置

⛔ 你确认的**四条我自引回归**全部修掉了。它们有个共同形状值得记下来：
**为修一个缺陷新加的判据自己太宽**。

| 我 r24 加的 | 本意 | 副作用 | 修法 |
|---|---|---|---|
| `_REDIR_RE` 逐条解析重定向 | 修 fd 归属 | 引号里的 `'<not-a-file'` 也被当重定向 | 补引号掩码 |
| `_HEREDOC_RE` 带 fd 前缀 | 认 `3<<'B'` | `N = 1 << 2` 也匹配上 | **验结束标记确实存在** |
| `_is_sh_separator` 排除 `<&` | 修 fd 关联 | `\>&` 里被转义的 `>` 也算 | 补转义掩码 |
| `body.startswith("c")` | 认 `-c'…'` | `-Bc` 里 `c` 不在串首 | 认整个短选项串 |

`1 << 2` 那条我没有收紧正则（`<< 2` 在 shell 里确实是合法 heredoc 语法），
而是改成**要求结束标记确实出现在后面的行里** —— 用「这个解释成立吗」代替「这个模式像吗」。

| 你的其余意见 | 整改 |
|---|---|
| **HIGH-5** 裸 `return`/`raise` 不进 `parent.values()` | 改从 `_own_nodes(scope)` 取。原用例 `return P` 恰好因为有 `Name` 子节点才被发现 —— 断言绿了一整轮纯属巧合 |
| **HIGH-6** 反射写入名单不全、写入目标只看顶层 | 目标**整棵**走一遍；名单 4 → **10** 项（`dict.update(globals(),…)` / `setattr(sys.modules[…])` / `__dict__[…]` / `importlib.reload` / `from x import *`） |
| **MEDIUM-1** `_bound_names()` 漏仅注解与 `del` | 两者都补上 |
| **MEDIUM-2** `unset C'LS'_BACKEND_URL` | 按命令词定位 `unset` 后**逐词去引号**再比 —— 不整行去引号，免得把 `printf '%s' 'unset …'` 这类**数据**算成命令 |

**回退验证 10 处全部承重，本轮零「考不出差异」**（前两轮各三条）。
你指出的 `_provably_last()` 两个误报方向（`return P` 在 `if False` 里、`raise` 被
`except` 接住）已作为**明确声明的保守面**记入验收单 §六。

判据仍 **10 条**，测试 167 → **169**。真实树 冷 438ms / 暖 196ms。

## 三 请按重要性排序回答的问题

1. **这一轮又引入回归了吗**？（这一问最重要 —— 连续两轮我都引入了回归：r23 两条、
   r24 四条）请优先对照 **`cb4fa9f8` 能抓、`6540e409` 漏掉** 这个方向找。
   本轮改动面：`_HEREDOC_RE` 加了结束标记存在性检验（会不会把**真**的 heredoc
   判掉，比如结束标记在块外、或整个 fence 就是一段没写完的示例？）、
   重定向与分隔符两处加了掩码、`_reflective_write_line()` 名单扩到 10 项
   （`.reload` / `.update` 这类**方法名匹配**会不会误报普通业务代码？）。
2. **反射写入名单现在会不会太宽**？我认任何 `.reload(` 调用、任何 `_NS_MUTATORS`
   方法作用在命名空间表达式上、以及 `x.__dict__` / `sys.modules[…]`。
   哪些形态是**普通代码里常见**却会被误判的？树上 9 份正文我实测为 0，但误报面未量化。
3. **`_bound_names()` 现在够全了吗**？我认赋值目标、形参、仅注解、`del`。
   还有什么会让一个名字成为该作用域的局部绑定（`import x` / `for` 目标 /
   `with … as` / `except … as` / `match` 捕获 / 嵌套 `def`、`class` 自身）？
   漏掉的方向是漏检还是误报？
4. **heredoc 的结束标记存在性检验**：我只在**本 fence 块内**找。如果一个示例的
   heredoc 结束标记落在下一个 fence、或正文故意省略，现在会被判成「不是 heredoc」
   ⇒ 回落到整块解析。这个回落方向对吗？
5. 仍然登记不修的清单，现在**本卡应修完**与**可另立卡**的分界划对了吗？
   你上一轮说的「即使不求精确结果，直接出现的未知写入机制仍可在本卡登记」我已照做
   （反射名单）——还有哪些属于「直接出现的未知机制」而我仍在静默？

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
