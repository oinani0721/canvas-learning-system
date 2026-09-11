# 独立复核请求 — CARD-SKILL-PORT-LINT（BATCH-2026-09-07-第十三批 / 车道 U4 / round-31）

## 一 背景与最小读取面（只读这些，不要扩大）

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts`
分支 `card/u4-hosts`。**本轮绑最终 HEAD**：`fcab3216` → **`bb85576c`**。

轮次说明：r5 是 D-15 的 5 轮上限，用户随后授权继续，故有 r6/r7/r8/r9。
本轮唯一代码 commit `bb85576c` 是按你 r9 的 5 HIGH + 2 MEDIUM + 3 LOW 全部整改。

**请只读下面这些**：

1. r8 之后的整改 diff（**本轮重点**）：`git -C <树根> diff 492d462d bb85576c -- . ':(exclude)_bmad-output'`
2. 全区间代码 diff：`git -C <树根> diff 9303201a bb85576c -- . ':(exclude)_bmad-output'`
3. 新测试全文：`backend/tests/skills/test_skill_portability_lint.py`
4. 你上一轮的报告：`_bmad-output/审查/codex-review-CARD-SKILL-PORT-LINT-r8.md`

**不要读**：`quiz-answer/SKILL.md` 正文（3076 行，本卡一字节未改）、live vault 下的文件、
其它车道的卡文。

## 二 round-30 的处置 —— **你列的唯一一条 MEDIUM 已封**

你指出 `_real_relpath()` 只遍历根**以下**分量，把整个 `.claude` 换成指向同内容目录的
符号链接时路径键与摘要**一个都不变**、门照绿。

⇒ 补 `_root_untrustworthy()`：根本身是符号链接、或根的目录项名字与期望不逐字符相符
（大小写不敏感文件系统）⇒ **直接判红，不再往下比** —— 根不可信时后面的枚举与摘要
全都不能采信。

配套负控 ⓪ 特意**先断言「沿根链接读出来的键与摘要本来就应该一模一样」**，
否则这条负控考错了对象。

**门禁承重独立验证**：把 `check_managed_files()` 内存退化成 `return []`，
**2/3 条门禁测试变红**（第三条是纯正控，退化后自然仍绿）。

判据 **11 条**，测试 **177**。tests/skills 546 passed。

## 三 请按重要性排序回答的问题

⛔ **收尾轮。只问两件事。**

1. **受管根检查封干净了吗**？`_root_untrustworthy()` 只查「根是不是符号链接」+
   「根名在父目录里逐字符存在」。还有静默面吗 —— 父目录**自己**是符号链接、
   根是**挂载点**、根是硬链接目录、`root.parent` 在容器里被 bind mount？
   哪些属于本卡该封的，哪些应当明确登记为边界？
2. **本轮有没有引入回归**？请对照 **`492d462d` 能抓、`bb85576c` 漏掉**。

如果两问都过，请给一句**可以直接签收**的结论。

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
