# 独立复核请求 — CARD-SKILL-PORT-LINT（BATCH-2026-09-07-第十三批 / 车道 U4 / round-22）

## 一 背景与最小读取面（只读这些，不要扩大）

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts`
分支 `card/u4-hosts`。**本轮绑最终 HEAD**：`fcab3216` → **`7fc33b61`**。

轮次说明：r5 是 D-15 的 5 轮上限，用户随后授权继续，故有 r6/r7/r8/r9。
本轮唯一代码 commit `7fc33b61` 是按你 r9 的 5 HIGH + 2 MEDIUM + 3 LOW 全部整改。

**请只读下面这些**：

1. r8 之后的整改 diff（**本轮重点**）：`git -C <树根> diff 55330069 7fc33b61 -- . ':(exclude)_bmad-output'`
2. 全区间代码 diff：`git -C <树根> diff 9303201a 7fc33b61 -- . ':(exclude)_bmad-output'`
3. 新测试全文：`backend/tests/skills/test_skill_portability_lint.py`
4. 你上一轮的报告：`_bmad-output/审查/codex-review-CARD-SKILL-PORT-LINT-r8.md`

**不要读**：`quiz-answer/SKILL.md` 正文（3076 行，本卡一字节未改）、live vault 下的文件、
其它车道的卡文。

## 二 round-21 的处置

你的完整消费端清单我照收；「注释处理不应机械统一」的驳回**理由成立，已采纳** ——
判据的输入面本来就不同，统一反而是错的。两条 HIGH 都修了，**它们是两个不同的修点**。

| 你的意见 | 整改 |
|---|---|
| **HIGH-1** 写入目标只认直接 `Name` | 抽 `_target_names()` + `_assignments()`，覆盖解包/星号/walrus/增量赋值/`for`/`with` 六类 |
| **HIGH-2** 判据作用域只到语法单元 | 新增 `_reassigned_after_tmp()`，在**整个 fence 块**上按行序再跑一次 |
| **MEDIUM-1** 按原文切 `;` 切开单引号脚本 | `_sh_segments()` 引号感知；另补 `-lc`、`$'…'` |
| **MEDIUM-2** 注释状态机不跟踪展开/嵌套引用 | 抽 `_sh_protect_mask()`：`${…}`/`$(…)` 用栈、每层独立引号状态、`$'…'` |
| **MEDIUM-3** 端口落在展开里 ≠ 控制主机 | 判准改为「展开必须是该 **URL token** 的开头，且后面不是 `@`」 |
| **MEDIUM-4** 数组赋值 / `printf -v` | `_URL_ASSIGN_RE` 加下标；新增 `_URL_PRINTF_V_RE` |
| **MEDIUM-5** `backslashreplace` 与字面反斜杠撞名 | 抽 `_decode_bytes()`：先把已有 `\` 转义成 `\\`，编码才单射 |
| **LOW-1** bytes 叶分支缺断言 | 补隐式相邻拼接的单射断言 |

**回退验证 12 条全部承重**；另有**一条被验证为不承重、已删** —— 我给 `_env_clears_url()`
写过「双引号脚本里 `$` 被转义就算」的分支，回退后没有任何断言变红：`\$` 挡在展开前面
就使它不再是 URL token 开头，词级判据必然已经报了。该分支恒不决定结果。

**我自己引入并当场修掉的回归**：MEDIUM-3 第一版判准写成「展开在**词**的开头」，立刻把
`env -u OTHER sh -c 'curl "${CLS_BACKEND_URL:-…}/x"'` 判成误报 —— 被引号包住的整条脚本
也是一个词。已改绑 URL token 边界。

**性能（答你的 LOW「真实树耗时未验证」）**：9 份 SKILL.md 动态判据全路径
冷缓存 **317ms** / 暖缓存 **46ms**（`_parse_units` 占 2.8ms），阈值 10s；
`_py_strings` 缓存 hits=3281 / misses=1913。

判据仍 **10 条**，测试 157 → **159**。

## 三 请按重要性排序回答的问题

1. **重赋值判据现在的作用域对了吗**？（这一问最重要）
   我加了 `_reassigned_after_tmp()` 在整个 fence 块上按行序跑。但它把整块当**直线**看：
   - `if c: P = "/tmp/…"` 与 `else: P = "/etc/passwd"` 是**互斥分支**，不是重赋值 —— 会误报吗？
   - 函数体里的 `P` 与模块级的 `P` 是**不同作用域**，我按名字比会不会撞？
   - 反过来：`P = "/tmp/…"` 在一个 fence、重赋值在**下一个 fence**，这是你说的跨块边界，
     还是也该抓？请给出你认为的正确边界。
2. **`_sh_protect_mask()` 这个手写词法器有没有新缺陷**？它现在被注释剥离与命令段切分
   **共用**，错一处就错两处。重点：反引号命令替换（我没处理）、`$((…))` 算术展开、
   `${var/#pat/rep}` 里的 `#`、未闭合引号、`)` 在没有 `$(` 时的行为。
3. **`_url_word_is_controlled()` 的「URL token 开头」判准**：我用
   `re.split(r"[\s\"'=(]", prefix)[-1] == ""` 判边界。还有哪些字符应该算 token 分隔符
   （反引号？`|`？`>`？），漏掉会造成哪个方向的错？
4. 本轮**其余整改**（`_decode_bytes` 单射、`_URL_PRINTF_V_RE`、`-lc`/`$'…'`、
   删掉的两个分支）有没有引入新缺陷或新的恒真/恒假分支？
5. 仍然登记不修的四项（脚本变量数据流、跨物理行引号、`_shell_words` 边界、容器栈四条
   双向反例）——**这个清单完整吗**？还有没有你认为**应该在本卡修**而我推给下一卡的？

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
