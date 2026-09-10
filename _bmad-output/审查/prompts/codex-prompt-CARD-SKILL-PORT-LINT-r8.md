# 独立复核请求 — CARD-SKILL-PORT-LINT（BATCH-2026-09-07-第十三批 / 车道 U4 / round-8）

## 一 背景与最小读取面（只读这些，不要扩大）

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts`
分支 `card/u4-hosts`。**本轮绑最终 HEAD**：`26d6df62` → **`fcab3216`**。

轮次说明：r5 是 D-15 的 5 轮上限，用户随后授权继续，故有 r6/r7/r8。
本轮唯一代码 commit `fcab3216` 是按你 r7 的 6 HIGH + 1 MEDIUM + 2 LOW 全部整改。

**请只读下面这些**：

1. r7 之后的整改 diff（**本轮重点**）：`git -C <树根> diff 26d6df62 fcab3216 -- . ':(exclude)_bmad-output'`
2. 全区间代码 diff：`git -C <树根> diff 9303201a fcab3216 -- . ':(exclude)_bmad-output'`
3. 新测试全文：`backend/tests/skills/test_skill_portability_lint.py`
4. 你上一轮的报告：`_bmad-output/审查/codex-review-CARD-SKILL-PORT-LINT-r7.md`

**不要读**：`quiz-answer/SKILL.md` 正文（3076 行，本卡一字节未改）、live vault 下的文件、
其它车道的卡文。

## 二 round-7 九条意见的处置（**全部**整改，无一条按「登记不修」处理）

九条我都先复现再动手，8 个反例当时 8/8 全漏，与你的描述逐字吻合（含 HIGH-6 的模 7
锯齿边界：6 抓 / 7 漏 / 8 抓 / 14 漏）。

| 你的意见 | 根因 | 整改 |
|---|---|---|
| **HIGH-1** 双反引号 code span 内的命令替换 | ① span 正则只认单反引号 ② 第八条跳过散文 | ① `_BACKTICK_SPAN_RE` 改 N 开 N 闭（CommonMark）② 第八条在散文侧看 **span 的内容**（不是整行——散文里反引号是 markdown 语法，看整行会全树误报；span 内部的反引号只可能是命令替换）。全树实测命中 0 |
| **HIGH-2** `~~~` info 含 `~~~` 被误判 / ` ```not-a-close ` 错误闭合 / 列表首行 fence 不识别 | 三处与 CommonMark 不符 | ① 行内 span 判定抽成 `_is_inline_span()` 且**只对反引号生效** ② 闭合 fence 行剩余部分必须为空 ③ `_FENCE_RE` 允许列表项前缀 |
| **HIGH-3** 九行括号语句超窗后拼接关系消失 | 固定 8 行窗口 | 新增 `_unit_end()`：边界由**括号深度/引号奇偶/行尾续行符**决定，不由常数决定 |
| **HIGH-4** `AugAssign` 被当安全停止点 | `+=` 本身就是拼接 | 从 `_STATEMENT_NODES` 移除 |
| **HIGH-5** 合法 shell 跨行引号被拆坏 | 降级只累积 Python 侧 | `_parse_units` 的 shell 窗口同样累积 |
| **HIGH-6** 续行链切窗丢跨组关联 | 链长上限 6 | 去掉小上限（边界由「行尾还是不是 `\`」决定） |
| **MEDIUM** 已登记裸 `/tmp` 成可复用盲槽 | 越界候选去重 | 改**多重集**（顺带修掉「消息写多重集、实现在去重」这处名实不符），基线随之重测 |
| **LOW-1** fence 同字符要求不承重 + `sandbox` 参数空跑 | 用例只考了「长度」那一半 | 补 `~~~` 开、``` 试图闭合的用例；去掉未使用的 fixture 参数 |
| **LOW-2** 分号样本不能证明尾部未截断 | 载体前半本就越界 | 换成 `/tmp/cls-exam/a;sub/../../../x`：截断 ⇒ `/tmp/cls-exam/a`（合规），不截断 ⇒ `/x`（越界） |

**整改期间自己踩到并修掉的两处**（如实声明，请一并复核）：
1. 一度把解析窗口开到「块末尾」以关掉 HIGH-3 的固定上限 ⇒ `quiz-answer` 有个 **2746 行**
   的 fence 块，`escaping_tmp_paths()` 单次 **35.9 秒**，整套测试超时。改 `_unit_end()`
   轻量定界后回到 **0.12 秒**，而固定上限那个漏检面没有回来。
2. 把 Python 与 shell 两个窗口写进同一个循环 ⇒ `shlex` 对 `P = (` 这种单行也「成功」
   （返回 `['P','=','(']`），Python 的多行累积永远轮不到，HIGH-3 与开括号换行整类回来。
   改成两个窗口**先后**而非交错。

**新增断言**：`_R7_HIGH_FORMS` 八行形态表（每行 = 坏形态 + 结构相同的安全对照 + **指名
判据**）。指名是必要的：越界判据把整个 backtick span 当路径（已登记的保守方向），
若只问「有没有人红」，HIGH-1 那一行会用一个**错误的理由**通过。
两条 LOW 的修复各做了内存变异验证（删掉同字符判断 ⇒ 指名断言变红；旧载体截断后仍越界
⇒ 证明不了「不截断」），证据在 `evidence-skill-lint/low-fix-mutation-r8-*.txt`。

判据仍是 8 条，测试 88 → 96。

## 三 请按重要性排序回答的问题

1. **本轮整改有没有引入新缺陷**？重点：
   - `_unit_end()` 的括号/引号计数是**纯文本**的：字符串内的括号、三引号、注释里的
     引号都会算错。哪种形态会让它把边界定**短**（漏检方向）而不是定长（误报方向）？
   - `_BACKTICK_SPAN_RE` 改 N 开 N 闭后，散文侧提取到的 span 集合有没有**变少**的形态？
     （整改中实测过一次：加 `DOTALL` 会跨行吞并小 span，导致基线**缺失**方向的红。）
   - 第八条在散文侧只看 span 内容 —— span **外**的命令替换（例如整行没有反引号包裹的
     裸 shell 片段）是不是新的缺口？
2. **`_STATEMENT_NODES` 现在是 `(Assign, AnnAssign, Expr, Return)`**：还有哪些语句类型
   抵达后**不能**证明「纯静态字面量」？（`With` / `withitem` / `comprehension` /
   `keyword` / `Starred` / `NamedExpr` / 装饰器 / 默认参数）
3. **多重集改动**：基线从 4 项变成 16 项，U5-B（quiz-answer）与 U6 rebase 时会不会产生
   **令人误解**的红？次数变化的红能不能被读懂？
4. **八条判据合起来是否仍有等计数缺口**？九项计数不变、五个集合都不变，但实际引入
   可移植性债的替换形态。
5. **哪条断言不承重**？特别看 `_R7_HIGH_FORMS` 八行（指名判据是否选对了那条？安全对照
   是否真的只差那一处？）与两条 LOW 的整改。
6. **收尾判断**：残余风险面是否都已如实声明？还有没有**未声明的**、可静态确定的漏检？

## 四 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给出 `file:line` + 一句话说明**在什么输入
或什么改动下这条会出问题**。没有问题的维度请明确写「未发现」，不要省略。
最后单独给一句结论：本轮 BLOCKER 与 HIGH 各几条。

## 五 边界

- 只读，不要修改任何文件；不要连任何数据库或网络服务。
- 不要跑 pytest（`sandbox` fixture 会复制大文件）。可直接用树内
  `backend/.venv/bin/python` 动态加载被测模块，调用 `_body_counts()` / `_fence_blocks()` /
  `_is_inline_span()` / `_unit_end()` / `_parse_units()` / `_py_strings()` / `_sh_words()` /
  `_fold_str()` / `_quiet_parse()` / `_has_dynamic_tmp_join()` / `escaping_tmp_paths()` /
  `suspicious_tmp_lines()` / `dynamic_tmp_join_lines()` / `parent_dir_prose_lines()` /
  `opaque_tmp_lines()` / `_script_counts()` / `check_handoff_constants()` /
  `_discover_out_of_scope_8011()` 等纯函数验证。
- 不评二线宿主（Codex / OpenCode / dsh）的可跑性 —— 那是另一张卡的范围。
- 不评 `quiz-answer/SKILL.md` 的内容质量 —— 本卡对它只钉计数、一字节未改。
- 不评 `_bmad-output/` 下的文档措辞。
