# 独立复核请求 — CARD-SKILL-PORT-LINT（BATCH-2026-09-07-第十三批 / 车道 U4 / round-29）

## 一 背景与最小读取面（只读这些，不要扩大）

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts`
分支 `card/u4-hosts`。**本轮绑最终 HEAD**：`fcab3216` → **`869081f8`**。

轮次说明：r5 是 D-15 的 5 轮上限，用户随后授权继续，故有 r6/r7/r8/r9。
本轮唯一代码 commit `869081f8` 是按你 r9 的 5 HIGH + 2 MEDIUM + 3 LOW 全部整改。

**请只读下面这些**：

1. r8 之后的整改 diff（**本轮重点**）：`git -C <树根> diff c789ffbf 869081f8 -- . ':(exclude)_bmad-output'`
2. 全区间代码 diff：`git -C <树根> diff 9303201a 869081f8 -- . ':(exclude)_bmad-output'`
3. 新测试全文：`backend/tests/skills/test_skill_portability_lint.py`
4. 你上一轮的报告：`_bmad-output/审查/codex-review-CARD-SKILL-PORT-LINT-r8.md`

**不要读**：`quiz-answer/SKILL.md` 正文（3076 行，本卡一字节未改）、live vault 下的文件、
其它车道的卡文。

## 二 round-28 的处置 —— **按你的 (b) 做了结构性收口**

你对第 0 问的三段答复我全部照收，并已落地：

**(a) 不收敛的根因**（你的原话）：「当前实现要求**识别出某种风险才登记**，尚未做到
**无法证明属于允许范围就登记**」。你给的例子打穿了包括第⑩条在内的全部十条 ——
`ROOT = "/t"` + `ROOT + "mp/cls-exam/../x"`，因为第⑩条**在输入过滤器上就用连续
`/tmp` 筛**，拆分常量根本进不了指纹集合。这一条解释了 r20 之后几乎所有反例的形状。

**(b) 终止形态**：新增**第十一条判据** —— `MANAGED_FILE_DIGESTS`（16 份受管文件的
**整文件原始字节 sha256**）+ `check_managed_files()`（集合与摘要精确相等）。
不读文本、不按行、不解码、不依赖 `/tmp`／语言标签／Markdown 分块。
配两条测试：正控 + **负控**（负控**先证明前十条对那个形态全部静默**，再证明字节摘要
会变 —— 否则这个负控考错了对象）。
④~⑨ 的承诺已降级为**诊断价值**，「绿色证明所有路径构造安全」这句已从契约里删除。

**(c) 结论句**已原文写进验收单 §六。同时记入：更新 `MANAGED_FILE_DIGESTS`
**表示接受一次人工审核快照，不等于债务消除**。

**三条回归（都是我 r27 引入的）已修**：
| | 修法 |
|---|---|
| 算术掩码没看引号（`echo "(("`） | 只在**未被引用**时才当算术 |
| 「Python 可解析 ⇒ 不是 heredoc」回落方向错 | 照你说的：只有 fence **声明**是 python 时才排除；**语言未声明时两种解释都保留** |
| `{ unset X; }` 复合命令 | 命令词前缀补 `{` / `(` |

你对我自述的更正也记下了：`m = globals(); n = m; n["P"] = …` **新版已能抓**。

判据 **10 → 11 条**，测试 173 → **175**。

## 三 请按重要性排序回答的问题

⛔ **本轮只问一件事：这个收口成立吗？** 不要再扩张语义反例清单 —— 那条路你已经判过了。

1. **第十一条判据（整文件字节摘要 + 精确文件集合）真的能有限验收吗**？
   - 它的**性质**是不是「未改快照必绿；受管文件新增/删除/任何字节变化必红」？
     有没有反例（符号链接、文件模式变化、`.gitattributes` 换行转换、大小写不敏感
     文件系统上的改名）能让它**静默**？
   - 我用 `sha256` 前 **16 位**。这个长度够吗？
   - 文件集合用 `glob("skills/*/SKILL.md")` + `glob("skills/*/scripts/*.py")` +
     `glob("scripts/*.py")` 枚举。有没有**受管面之外**的路径能进来、或**受管面之内**
     的路径被 glob 漏掉？
2. **④~⑨ 的承诺降级，措辞够不够准**？验收单 §六 现在写的是你的 (c) 原文。
   还有哪句现存的 docstring / 断言消息仍在**隐含**「绿色 = 安全」？
3. **本轮三条回归修对了吗**？请对照 **`c789ffbf` 能抓、`869081f8` 漏掉**。
   特别是「语言未声明时两种解释都保留」—— 它会不会产生新的误报面？
4. **这张卡现在可以收尾了吗**？如果可以，请给一句**验收结论**；如果还差什么
   **必须在本卡做完**的，请只列那些（不含可另立卡的）。

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
