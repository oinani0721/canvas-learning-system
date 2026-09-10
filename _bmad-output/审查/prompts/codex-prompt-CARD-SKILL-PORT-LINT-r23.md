# 独立复核请求 — CARD-SKILL-PORT-LINT（BATCH-2026-09-07-第十三批 / 车道 U4 / round-23）

## 一 背景与最小读取面（只读这些，不要扩大）

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts`
分支 `card/u4-hosts`。**本轮绑最终 HEAD**：`fcab3216` → **`b001cf83`**。

轮次说明：r5 是 D-15 的 5 轮上限，用户随后授权继续，故有 r6/r7/r8/r9。
本轮唯一代码 commit `b001cf83` 是按你 r9 的 5 HIGH + 2 MEDIUM + 3 LOW 全部整改。

**请只读下面这些**：

1. r8 之后的整改 diff（**本轮重点**）：`git -C <树根> diff 7fc33b61 b001cf83 -- . ':(exclude)_bmad-output'`
2. 全区间代码 diff：`git -C <树根> diff 9303201a b001cf83 -- . ':(exclude)_bmad-output'`
3. 新测试全文：`backend/tests/skills/test_skill_portability_lint.py`
4. 你上一轮的报告：`_bmad-output/审查/codex-review-CARD-SKILL-PORT-LINT-r8.md`

**不要读**：`quiz-answer/SKILL.md` 正文（3076 行，本卡一字节未改）、live vault 下的文件、
其它车道的卡文。

## 二 round-22 的处置

你给的那句总结我照收，并按它**重写了判据的模型**（不是继续打补丁）：

> 「正确边界应是**同一执行区内的实际绑定与可达执行关系**。」

拆成三件独立的事，此前我把它们混成一件：

| | 原来 | 现在 |
|---|---|---|
| **绑定** | 整树按裸名字比 | 按作用域分组，`global`/`nonlocal` 并回外层 |
| **可达执行关系** | 按源码行序 | **循环回边 / 互斥分支 / 直线** 三分 |
| **执行区** | 「整块是合法 Python」 | 整块 **+ 每个 Python heredoc**；相邻 fence **不**串联 |

⛔ 你**推翻了我上一轮的一个辩护**，我承认并已改：我把 `if/else` 报红说成
「静态不可判 ⇒ 该报」，你指出**两支都赋合规常量时仍报两处**。该辩护不成立 ——
不可判的是分支，不是结论。

| 你的意见 | 整改 |
|---|---|
| **HIGH-1** 源码行序 ≠ 执行顺序（循环回边漏 + 互斥分支误） | `_risky_reassign()` 三分法；位置用 `(行号, 列偏移)`（顺带消掉 LOW 那条不一致） |
| **HIGH-2** 整块不是合法 Python 时补查整个跳过 | `_python_regions()`：整块 + 每个 Python heredoc |
| **HIGH-3 / MEDIUM-1** | 我在你上一轮中断期间**自查已修**（你绑的是提交态，故仍报） |
| **MEDIUM-2** 顶层转义字符被当结构字符 | 被转义的字符**永远**算数据 |
| **MEDIUM-3** `$( (:) … )` 提前出栈 / 反引号无层 | `$(` 层内跟踪裸括号 + 反引号自成一层（顶层裸 `(` 刻意不跟踪） |
| **MEDIUM-4** URL 边界按原串字符判 | 剥引号到**不动点**后按 token 判；`\"` 去转义、`\$` 保留 |
| **MEDIUM-5** 一处受控放行整词 | **逐处**判 |
| **MEDIUM-6** 与 str 汇合后身份碰撞 | `_ident_text()`：str 与 bytes 同一套编码，两边都先转义已有反斜杠 |
| **MEDIUM-7** `printf -v` 跨命令边界 | 锚在段首且 `-v` 在 `--` 之前 |
| **MEDIUM-8** `-l -c` 漏 / `-c` 后参数被当脚本 | shell 名进正则参与回溯；`-c` 后只取第一个词 |

**我自己踩的两个坑**（当场纠正）：第一版改成**完全顺序无关**，当场把形态表 HIGH-4 的
安全对照判红；单层剥引号不够，被引号包住的整条脚本剥完仍带内层引号 ⇒ 误报。

**回退验证 15 处全部承重**。过程中三条**变异体自身写错**（红的是崩溃不是断言），
重做后 **HIGH-1b 暴露出真的缺一条断言** —— 互斥判定只有在「越界分支在前、合规分支
在后」时才独立于直线规则起作用，原用例被直线规则顺带覆盖了，已补。

判据仍 **10 条**，测试 160 → **162**。真实树耗时 冷 337ms / 暖 107ms。

## 三 请按重要性排序回答的问题

1. **新的三分法（循环 / 互斥 / 直线）本身对不对**？（这一问最重要 —— 它替换的是判据的
   **模型**，不是一个分支）
   - 我把「在循环体内」和「落在互斥分支」都当成「源码序不可信」。还有别的结构会让
     源码序失效吗（`try/finally`、`with` 的异常路径、`continue`、生成器/`await` 的
     重入、递归函数里的模块级 `global`）？
   - 直线情形我只在 `tw.pos < ow.pos` 时登记。**同一行**内多次写入（分号、海象嵌在
     表达式里）的 `col_offset` 顺序等于执行顺序吗？
   - 互斥判定用「分支链在同一节点分岔」。`match` 的 guard（`case P if c:`）、
     `try/else`、`elif` 链在我的 `_branch_index()` 里归类对吗？
2. **`_python_regions()` 的执行区边界对不对**？我只认「整块」和「Python heredoc」。
   - heredoc 的结束标记我按「整行 strip 后等于 tag」找。`<<-` 允许前导 **tab**、
     引号形式、同一行多个 heredoc（`cmd <<A <<B`）—— 我的取法会不会切错区？
   - 反过来：一个 shell fence 里**两个** heredoc 喂给**同一个** python 进程
     （或 `python3 -c` 后跟 heredoc）算不算同一执行区？
3. **我这轮的整改有没有引入新缺陷**？重点看三处：`_sh_strip_quotes()` 的**不动点**
   循环（会不会有输入让它不收敛，或把本该保留的字符剥掉）、`_risky_reassign()` 的
   **两两配对**（成本是 O(tmp×other)，会不会在正文里退化）、`_branch_path()` 的
   父指针表（`_own_nodes` 不下钻嵌套作用域，父表会不会缺边导致分支链算短）。
4. 仍然登记不修的清单（脚本变量数据流、跨物理行引号、`_shell_words` 边界、容器栈四条
   双向反例）——**这个清单现在完整吗**？你上一轮说它「不完整」，我这轮补了哪些、
   还差哪些？请给出**本卡应该修完**与**可以另立卡**的分界。

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
