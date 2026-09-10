# 独立复核请求 — CARD-SKILL-PORT-LINT（BATCH-2026-09-07-第十三批 / 车道 U4 / round-28）

## 一 背景与最小读取面（只读这些，不要扩大）

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts`
分支 `card/u4-hosts`。**本轮绑最终 HEAD**：`fcab3216` → **`c789ffbf`**。

轮次说明：r5 是 D-15 的 5 轮上限，用户随后授权继续，故有 r6/r7/r8/r9。
本轮唯一代码 commit `c789ffbf` 是按你 r9 的 5 HIGH + 2 MEDIUM + 3 LOW 全部整改。

**请只读下面这些**：

1. r8 之后的整改 diff（**本轮重点**）：`git -C <树根> diff 9c29aacb c789ffbf -- . ':(exclude)_bmad-output'`
2. 全区间代码 diff：`git -C <树根> diff 9303201a c789ffbf -- . ':(exclude)_bmad-output'`
3. 新测试全文：`backend/tests/skills/test_skill_portability_lint.py`
4. 你上一轮的报告：`_bmad-output/审查/codex-review-CARD-SKILL-PORT-LINT-r8.md`

**不要读**：`quiz-answer/SKILL.md` 正文（3076 行，本卡一字节未改）、live vault 下的文件、
其它车道的卡文。

## 二 round-27 的处置

⛔ 我的 heredoc 判别**连续两轮被你证伪**（r25「结束标记存在」、r26「定界符带引号」）。
r27 改用 **fence 的 info string** 作主信号 —— 这块正文早写明了是什么语言，
那是最直接的证据，前几轮一直没用上：

```
info ∈ {python, py, python3, …}   ⇒ `<<` 一定是左移
info ∈ {sh, bash, zsh, console, …} ⇒ 是 heredoc（算术 `(( ))` 由掩码挡在前面）
info 缺失/其它                       ⇒ 回落到「这一行能不能当合法 Python 解析」
```

| 你的意见 | 整改 |
|---|---|
| **HIGH-1（回归）** 引号判别两个方向都错 | 见上 + 顶层 `(( … ))` 算术掩码 |
| **HIGH-2（回归）** 排除带参数 `vars()` 把 `vars(模块)` 一起排除 | `vars(X)` 当 X 是模块表达式时**就是**模块字典；补别名（`import sys as s` / `m = globals()` / `import importlib as imp`）—— 都是**直接可见**的 |
| **HIGH-3（既存）** 解包把整个右值当成每个目标的值 | `_Write.partial`，`_provably_last()` 一律判「证不出」 |
| **HIGH-4（既存）** `del P` 不计为写入 | `ast.Delete` 的目标计为一次写入 |
| **HIGH-5（既存）** 生成器暂停没进必经性检查 | `Yield`/`YieldFrom` 进 `_EARLY_EXIT_NODES` |
| **MEDIUM-1（回归）** 只允许赋值前缀 | 补 `command`/`builtin`/`exec`/`!` 与前置重定向 |
| **MEDIUM-2（既存）** 后备正则绕过命令词检查 | **删除后备正则**。⚠️ 我 r26 给的负控用了 `C'LS'_…`，**恰好避开它** —— 那条负控没有证明普通拼写的误报已消除，你指得对 |

⛔ **你对我自检脚本的批评已采纳**：47 条语料每条带 **`RED`/`GREEN` 预期**，
脚本同时 (a) 比两版差异、(b) 拿新版逐条对预期 —— 后者才抓得住「两版共同漏检」。
本轮实测：47 条预期全符合；8 处差异全是本轮修复。

判据仍 **10 条**，测试 171 → **173**。

## 三 请按重要性排序回答的问题

⛔ **先请你回答一个不同性质的问题**（第 0 问，优先于下面全部）：

**这个判据还应该继续修下去吗？**
r20~r27 八轮的 HIGH 数是 **2 / 2 / 3 / 3 / 5 / 6 / 6 / 4 / 5**，从未到 0。
每一轮你都给出真实的、我复现得了的反例；每一轮我修完，下一轮又出现新的语义角落
（生成器暂停、解包、`del`、算术 `(( ))`、`__lshift__` 重载、模块别名…）。
判据 ④~⑨ 要做的事本质上是**在手写代码里复现 Markdown + shell + Python 三层语义**。
我 r13 的应对是加第十条「块指纹兜底网」，但最近每一个反例都用
`"/t" + "mp/…"` 拆分常量，**恰好是指纹接不住的那一类**。

请直接回答：
- (a) 这条路**能不能**在有限轮次内收敛到 HIGH=0？如果能，还差什么结构性的东西？
- (b) 如果不能，**这张卡的正确终止形态**是什么？（把 ④~⑨ 降级成「登记面」而
  不追求完备？把 `/tmp` 判据缩到只认字面量、拆分常量一律登记？还是别的？）
- (c) 现在这个门**已经能挡住什么**、**挡不住什么**，请给一句可以写进验收单的结论。

—— 以下是常规问题，若第 0 问的答案是「不该继续修」，可以只答第 0 问。

1. **本轮又引入回归了吗**？请优先对照 **`9c29aacb` 能抓、`c789ffbf` 漏掉**。
   本轮改动面：heredoc 判别换 info string、算术掩码、命名空间别名、`partial`、
   `Delete` 记录、`Yield` 进早退名单、删掉 unset 后备正则。
2. **fence info string 作主信号**的口径对吗？info 缺失时回落到「Python 可解析」——
   这个回落方向在哪些形态下仍会错？
3. **别名识别**只做同一区内的直接绑定（`import x as y`、`m = globals()`）。
   这个深度够不够？再深一层（`m = globals(); n = m; n["P"] = …`）现在是什么结果？
4. 分界：**本卡应修完**与**可另立卡**，到这一轮为止划对了吗？

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
