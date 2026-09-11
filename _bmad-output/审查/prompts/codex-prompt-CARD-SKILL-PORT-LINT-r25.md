# 独立复核请求 — CARD-SKILL-PORT-LINT（BATCH-2026-09-07-第十三批 / 车道 U4 / round-25）

## 一 背景与最小读取面（只读这些，不要扩大）

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts`
分支 `card/u4-hosts`。**本轮绑最终 HEAD**：`fcab3216` → **`cb4fa9f8`**。

轮次说明：r5 是 D-15 的 5 轮上限，用户随后授权继续，故有 r6/r7/r8/r9。
本轮唯一代码 commit `cb4fa9f8` 是按你 r9 的 5 HIGH + 2 MEDIUM + 3 LOW 全部整改。

**请只读下面这些**：

1. r8 之后的整改 diff（**本轮重点**）：`git -C <树根> diff e22c6d27 cb4fa9f8 -- . ':(exclude)_bmad-output'`
2. 全区间代码 diff：`git -C <树根> diff 9303201a cb4fa9f8 -- . ':(exclude)_bmad-output'`
3. 新测试全文：`backend/tests/skills/test_skill_portability_lint.py`
4. 你上一轮的报告：`_bmad-output/审查/codex-review-CARD-SKILL-PORT-LINT-r8.md`

**不要读**：`quiz-answer/SKILL.md` 正文（3076 行，本卡一字节未改）、live vault 下的文件、
其它车道的卡文。

## 二 round-24 的处置

你确认了「默认方向正确，沉默条件不够严」，所以本轮修的是**判据**不是方向。
⛔ 你标出的两条**我 r23 引入的回归**（fd 归属、解释器参数）我照单认下并修了。

| 你的意见 | 整改 |
|---|---|
| **HIGH-1** 祖先黑名单证明不了必经（`with suppress` / `return` 在前 / `except*`） | `_CONDITIONAL_NODES` 补 `With`/`AsyncWith`/`TryStar`；新增**提前离开**判定 |
| **HIGH-2** `nonlocal` 要找最近**实际绑定**的函数（含形参），搬运要**迭代到不动点** | `_bound_names()`（赋值目标 + 形参）+ `nonlocal_target()` 逐层外找 + 不动点循环 |
| **HIGH-3** heredoc 按命令/fd/重定向顺序归属（**回归**） | `_REDIR_RE` 解析 `N<<tag` / `<&N` / `<file`，逐命令段维护 fd 表 |
| **HIGH-4** 解释器参数与命令边界（**回归**） | 可执行词去引号；`-W`/`-X`/`-Q` 吃下一个词；`-c'…'` 连写；每个命令段都看 |
| **HIGH-5** 原文里的假 heredoc 标记 | 扫描改用**去注释 + 引号感知**版 |
| **HIGH-6** 反射式写入完全静默 | `globals()[…]=` / `.update(…)` / `exec(…)` / `type P = int` 一律登记 |
| **MEDIUM-1** 定义处表达式重复归属 | `_own_nodes(root)` 按**字段名**跳过（原来按子节点 id 比对，`iter_child_nodes` 产出的是 `arguments`，id 对不上） |
| **MEDIUM-2** 整块可解析 ≠ 一个执行区 | 块里出现真 heredoc 就不取整块 |
| **LOW** 四个控制流 helper 成死代码 | 已删 |

**一个两处共用的错误**：`&` 不总是命令分隔符（`<&3` / `2>&1` / `&>log`）。同一个 bug
在 heredoc 侧是 fd 关联丢失、在 URL 侧是 `2>&1` 错切 ⇒ 抽出 `_is_sh_separator()` 共用。

**差点打破三条负控**：反射写入检测第一版把 `globals().<任意方法>` 都算写，树上
quiz-answer `:1431` 的 `globals().get(...)`（**读**）被判成动态拼接。已收紧到真正会改
映射的方法。

**回退验证 16 处全部承重**，过程中照出**三条考不出差异的断言**（`except*` 用例落在
`ExceptHandler`、不动点用例被另一条配对顺带覆盖、形参绑定**根本没有用例**），已全部改正。

判据仍 **10 条**，测试 165 → **167**。真实树 冷 363ms / 暖 154ms。

## 三 请按重要性排序回答的问题

1. **这一轮的整改有没有再引入回归**？（这一问最重要 —— 上一轮我引入了两条，
   而本轮改动面更大：`_python_regions()` 又重写了一次、`_own_nodes()` 换了跳过口径、
   切段函数换成共用判定）
   请优先对照 **`e22c6d27` 能抓、`cb4fa9f8` 漏掉** 这个方向找。
2. **`_is_sh_separator()` 的口径对吗**？我只把 `<&` / `>&` / `&>` 排除出分隔符。
   `2>&1`、`>&2`、`|&`（bash 的管道带 stderr）、`a&&b`、后台执行的单个 `&`
   —— 这五种现在分别被判成什么？哪种判错、错的方向是漏还是误？
3. **`_provably_last()` 的沉默条件现在够严了吗**？我加了「提前离开」但它是**整段最早
   一处** `return`/`raise`/`break`/`continue` 与 `tw` 比位置 —— 这个近似在什么形态下
   会失效（例如 `return` 在一个不会执行的分支里、或 `raise` 在 `try` 里被接住）？
   方向是漏还是误？
4. **`_reflective_write_line()` 的名单够不够**？我认 `globals`/`locals`/`vars` 的
   下标赋值与六个 mutator 方法，加 `exec`/`eval`。还有哪些**直接可见**的机制会改
   模块命名空间（`importlib.reload`、`setattr(sys.modules[__name__], …)`、
   `from x import *`、`__dict__` 直取）？
5. 仍然登记不修的清单，现在**本卡应修完**与**可另立卡**的分界划对了吗？

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
