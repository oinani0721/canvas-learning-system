# 独立复核请求 — CARD-SKILL-PORT-LINT（BATCH-2026-09-07-第十三批 / 车道 U4 / round-24）

## 一 背景与最小读取面（只读这些，不要扩大）

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts`
分支 `card/u4-hosts`。**本轮绑最终 HEAD**：`fcab3216` → **`e22c6d27`**。

轮次说明：r5 是 D-15 的 5 轮上限，用户随后授权继续，故有 r6/r7/r8/r9。
本轮唯一代码 commit `e22c6d27` 是按你 r9 的 5 HIGH + 2 MEDIUM + 3 LOW 全部整改。

**请只读下面这些**：

1. r8 之后的整改 diff（**本轮重点**）：`git -C <树根> diff b001cf83 e22c6d27 -- . ':(exclude)_bmad-output'`
2. 全区间代码 diff：`git -C <树根> diff 9303201a e22c6d27 -- . ':(exclude)_bmad-output'`
3. 新测试全文：`backend/tests/skills/test_skill_portability_lint.py`
4. 你上一轮的报告：`_bmad-output/审查/codex-review-CARD-SKILL-PORT-LINT-r8.md`

**不要读**：`quiz-answer/SKILL.md` 正文（3076 行，本卡一字节未改）、live vault 下的文件、
其它车道的卡文。

## 二 round-23 的处置

⛔ 你那句「**暂不支持的执行关系应明确触发登记，不能因源码顺序或解析失败静默放行**」
我照收，并据此**翻转了判据的默认方向**。前几轮我一直在试图证明「这处是安全的」，
所以每补一种结构就漏一种新结构。现在只有同时满足下面四条才沉默，其余一律登记：

| 条件 | 理由 |
|---|---|
| **必经** | 祖先里没有 `if`/`try`/`except`/`match`/循环 |
| **非延迟求值** | 不在生成器表达式里 |
| **源码在后** | 位于全部越界写入之后（位置用 `(行号, 列偏移)`） |
| **双方都非搬运** | `global`/`nonlocal` 迁移过来的记录，父链与调用时机都不可信 |

误报侧一并消掉：循环**之后**的无条件合规写入现在能证明「必然最后执行」⇒ 沉默。

| 你的意见 | 整改 |
|---|---|
| **HIGH-1** 非循环非互斥 ≠ 必经；生成器延迟执行；反向的循环后误报 | 翻转默认（见上） |
| **HIGH-2** `nonlocal` 被并进模块 | 解析到**最近的外层函数**（跳过 class），与 `global` 不同目的地 |
| **HIGH-3** 截断整个作用域节点 | `_outer_eval_children()`：装饰器/默认参数/注解/基类/`returns` 仍属外层 |
| **HIGH-4** 搬运记录丢父链与调用时序 | `_Write.foreign`，一律判「证不出」 |
| **HIGH-5** heredoc 定界/重定向/接收命令语义 + `-c` 字面脚本 | `_python_regions()` 重写：多 heredoc 只有**最后一个**是 stdin；结束标记**整行相等**；`<<-` 逐行剥 tab；定界符可含 `-`；`python -c` 是执行区；接收命令不读 stdin 时不是执行区 |
| **MEDIUM ×4** | `builtin`/`{`/`then` 前缀的 `printf -v`；`env -u "VAR"` 闭引号；`bash -cl`；userinfo 看整个 authority 段；双引号内字面 `(` 不压栈 |
| **LOW** 二次退化 | 先在 `other` 上聚合 ⇒ O(tmp+other)。实测 N=100/200/400/800 = **1.6/3.2/6.4/12.7 ms**，每翻倍 ×1.99 |

**又一条死代码**（本卡第三次，都是回退验证照出来的）：我给三分法写过「共同循环」判定，
回退后没有任何断言变红 —— `For`/`While` 本来就在 `_CONDITIONAL_NODES` 里，那个检查
永远到不了。已删。
**「验过」不等于「钉住」**：四条 MEDIUM 我先用临时探针验过就往下走，回退验证当场照出
「撤掉整改后一条断言都不红」。已补断言。另有一条用例分不出差异（`PY_ = 0` 考不出
「结束标记 strip 还是整行相等」），换成带尾随空格的 `PY ` 才分得开。

**刻意保留的保守面**（你归为误报，我登记而不放行，已记验收单 §六）：
`try` 体写越界 + `else` 写合规；`match` guard 失败后落到下一 `case`。
两者最终值确实取决于运行时，按上面的口径应当登记 —— 如果你认为这个取舍不对，请说明。

判据仍 **10 条**，测试 162 → **165**。真实树 冷 324ms / 暖 111ms。回退验证 **16 处全部承重**。

## 三 请按重要性排序回答的问题

1. **翻转后的默认方向，现在的沉默条件够不够严**？（这一问最重要）
   我只在「必经 + 非延迟求值 + 源码在后 + 双方非搬运」时沉默。还有什么形态能**满足
   这四条**却仍然让合规值被覆盖？（`sys.settrace`/装饰器改写、`del P` 后重绑、
   `locals()` 写入、`exec()`、模块级 `__getattr__`、`try/finally` 里的 `return` …）
   反过来，**误报面**现在有多大 —— 有没有常见写法被无谓登记？
2. **`_python_regions()` 的 shell 语义还有多少缺口**？重点：`<<` 与 `<` 混用、
   heredoc 出现在管道/复合命令里（`{ python3 - <<'A'; } | cat`）、同一行 `cmd1 <<A | cmd2 <<B`、
   `exec 3<<A` 这类非 stdin 的 fd 重定向、以及 `python3 <<'A'`（无 `-`）。
3. **本轮整改有没有引入新缺陷**？重点看 `_outer_eval_children()`（我枚举了
   decorator/defaults/kw_defaults/annotation/bases/keywords/returns —— 漏了什么？
   `type` 语句、PEP 695 泛型参数、`ast.arg` 的 `type_comment`？）与
   `_scope_chain()`（`global` 在**嵌套**函数里声明、同一名字在一个作用域里既
   `global` 又被局部赋值、class 体内的 `global`）。
4. **我保留的两条保守面（`try/else`、`match` guard）对不对**？如果你坚持它们是误报，
   请说明在「证明不了就登记」的口径下应当怎么判 —— 是要我实现真正的可达性分析，
   还是有更简单的正确判法。
5. 仍然登记不修的清单（脚本变量数据流、跨物理行引号、`_shell_words` 边界、容器栈）——
   **本卡应该修完**与**可以另立卡**的分界，现在划对了吗？

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
