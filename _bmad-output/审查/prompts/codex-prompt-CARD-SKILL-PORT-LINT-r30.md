# 独立复核请求 — CARD-SKILL-PORT-LINT（BATCH-2026-09-07-第十三批 / 车道 U4 / round-30）

## 一 背景与最小读取面（只读这些，不要扩大）

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts`
分支 `card/u4-hosts`。**本轮绑最终 HEAD**：`fcab3216` → **`492d462d`**。

轮次说明：r5 是 D-15 的 5 轮上限，用户随后授权继续，故有 r6/r7/r8/r9。
本轮唯一代码 commit `492d462d` 是按你 r9 的 5 HIGH + 2 MEDIUM + 3 LOW 全部整改。

**请只读下面这些**：

1. r8 之后的整改 diff（**本轮重点**）：`git -C <树根> diff 869081f8 492d462d -- . ':(exclude)_bmad-output'`
2. 全区间代码 diff：`git -C <树根> diff 9303201a 492d462d -- . ':(exclude)_bmad-output'`
3. 新测试全文：`backend/tests/skills/test_skill_portability_lint.py`
4. 你上一轮的报告：`_bmad-output/审查/codex-review-CARD-SKILL-PORT-LINT-r8.md`

**不要读**：`quiz-answer/SKILL.md` 正文（3076 行，本卡一字节未改）、live vault 下的文件、
其它车道的卡文。

## 二 round-29 的处置 —— **你列的三项已全部完成**

你上一轮判「结构性方向成立，可以有限验收」，并列出本卡必须完成的三项。逐条：

| 你的意见 | 整改 |
|---|---|
| **MEDIUM-1** 没锁住实际路径与文件类型 | `_real_relpath()`：逐级用 `os.listdir()` 的**真实目录项**核对大小写，任一分量是符号链接即拒收 |
| **MEDIUM-2** 负控没验证正式门禁承重 | 两条 tmp 副本上的**正式门禁负控**，八种情形全部真正走 `check_managed_files()`；另给拆分常量负控补了**计数前提**断言 |
| **LOW-2** sha16 只有 64 bit | 改**全长 64 hex**，措辞改成「路径集合及原始字节摘要一致」 |
| **LOW-1** 诊断降级没贯穿旧说明 | 第⑩条那句「不管什么形态，块变了就红」**已被我自己的拆分常量负控否定**，改成「在它取到的候选范围内」并写明输入过滤器盲区 |
| **LOW-3** 两种保守误报 | 按你说的**就地登记**，不再修解析器 |

你给的验收结论原句已写进验收单 §六。

判据 **11 条**，测试 175 → **177**。tests/skills 546 passed。

## 三 请按重要性排序回答的问题

⛔ **本轮是收尾轮。只问两件事。**

1. **你上一轮列的三项，做完了吗**？请逐条核对：
   - `_real_relpath()` 的大小写核对与符号链接拒收 —— 还有没有静默面？
     （硬链接、`..` 分量、根目录本身是链接、`os.listdir` 抛错时的回落）
   - 两条正式门禁负控 —— 它们真的会因为 `check_managed_files()` 退化而变红吗？
     还有哪种情形没覆盖？
   - 契约说明 —— 还有哪句 docstring / 断言消息仍在**隐含**「绿色 = 安全」？
2. **本轮有没有引入回归**？请对照 **`869081f8` 能抓、`492d462d` 漏掉**。

如果两问都过，请给一句**可以直接签收**的结论；如果还差，请**只列必须在本卡做完的**。

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
