# 独立复核请求 — CARD-SKILL-PORT-LINT（BATCH-2026-09-07-第十三批 / 车道 U4 / round-4）

## 一 背景与最小读取面（只读这些，不要扩大）

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts`
分支 `card/u4-hosts`。**本轮绑最终 HEAD**：`9303201a`（U4-A 末 commit）→ **`83cd6104`**。

区间内六个 commit：`ae6a68f3` 初版 → `3b98081a` r1 整改 → `8bb94475` 作者自查 →
`98ca073c` r2 整改 → `83cd6104` r3 整改（本轮重点）。

这张卡：(1) 新增一道静态门，把 vault 内 9 份 SKILL.md 与 7 份 scripts 的「可移植性
指标」钉成基线，新增命中即红、减少也红；(2) 在 `start-exam-board` 一份 SKILL.md 上
做最小整改（`/tmp/cls-exam/` 命名空间 + `${CLS_BACKEND_URL:-…}` 缺省 URL）。

**请只读下面这些**：

1. 全区间代码 diff：`git -C <树根> diff 9303201a 83cd6104 -- . ':(exclude)_bmad-output'`
2. r3 之后的整改 diff（**本轮重点**）：`git -C <树根> diff 98ca073c 83cd6104 -- . ':(exclude)_bmad-output'`
3. 新测试全文：`backend/tests/skills/test_skill_portability_lint.py`
4. 你上三轮的报告：`_bmad-output/审查/codex-review-CARD-SKILL-PORT-LINT-r1/-r2/-r3.md`

**不要读**：`quiz-answer/SKILL.md` 正文（3076 行，本卡一字节未改）、live vault 下的文件、
其它车道的卡文。

## 二 round-3 七条意见的处置（请逐条独立核对是否真修好，以及整改本身有没有引入新缺陷）

**HIGH-1（黑名单式左边界漏 `/`、`+`、非 ASCII）**：
`_TMP_NS_RE` 与 `_TMP_TOKEN_RE` 的左边界从「排除 `[A-Za-z0-9_.~$-]`」改为**分隔符白名单**
`(?<![^\s"'`(\[{（【])` —— `/tmp` 前只允许空白/引号/反引号/开括号。三种冒充形态的
`tmp_ns` 全部掉零 ⇒ 计数判据红。已知保守误报方向已登记（`P=/tmp/x`、`>/tmp/x`、
`-o/tmp/x`、`file:///tmp/…` 判成债；树上无这些形态）。

**HIGH-2（物理行切分漏跨行拼接；覆盖表 startswith 被内嵌换行骗过）**：
新增 `_logical_lines()`：反斜杠续行 + 相邻同引号字面量拼接（行尾闭引号 + 次行同引号
开头，合并有界 4 次）合并后再判。覆盖表最终断言改为**整字面量 normpath** 在命名空间内
（与越界判据同一「在命名空间内」定义）。

**MEDIUM-3（`$1` 位置参数与引号外拼接 `$REL` 逃过变量展开正则）**：
可疑行触发放宽到「`/tmp` 在行内 且（`..` 或**任意 `$`**）」。基线随之加
start-exam-board `:577`（本卡变更记录行含 `${CLS_BACKEND_URL:-…}`，无害展开照样登记）。

**MEDIUM-4（已登记行在 ASCII 逗号后静默变质）**：
ASCII 逗号不再截断 token（中文标点 `，、。` 仍截断，防散文污染），整段进 normpath ⇒
变质尾巴改变越界多重集 ⇒ 红。r2-(a) 逗号穿越也因此被越界判据直接抓到。

**MEDIUM-5（删 `OUT_OF_SCOPE_8011` 条目 = 静默失明）**：
改**动态发现** `_discover_out_of_scope_8011()`：rglob 全树扫描覆盖面外含 `8011` 的文件，
与常量做集合级对照 —— 删条目/清空/新增债/U3-C 模板化四个方向全红。

**MEDIUM-6（U6 seed 两份不受零余量约束）**：
零余量覆盖**全部**条目（seed 不豁免）；U6 要给 seed 加 `/tmp` 须把条目挪去
`SCRIPTS_BASELINE` 人工审阅。

**LOW-7（`-o/tmp` 连写误报）**：登记为已知保守误报方向，不修（修它会重开冒充面）。

## 三 请按重要性排序回答的问题

1. **整改有没有引入新缺陷**？重点：
   a. 分隔符白名单字符集 `[\s"'`(\[{（【]` 本身 —— 有没有该列入却漏掉的**分隔符**
      （会导致误报），或**不该列入却列入**的字符（会重开冒充面）？
   b. `_logical_lines` 的相邻引号合并 —— 有没有形态让一个真实穿越**仍然**被拆在两个
      逻辑行里（漏检方向），或让行号基线**不稳定**（正常编辑无关行也红）？
   c. ASCII 逗号入 token 后，有没有树上或合理书写中会**污染**越界多重集的形态
      （基线含垃圾条目、脆弱）？
2. **五条判据合起来是否仍有缺口**？请找一个**等计数替换**形态：九项计数不变、越界
   多重集不变、可疑行集合不变，但实际引入了可移植性债。
3. **哪条断言其实不承重**？特别看 r3 新增的四条负控与更新的覆盖表 13 行 —— 有没有
   前提不成立而空跑的、有没有被别的判据代为打红的？
4. **动态发现 `_discover_out_of_scope_8011`**：rglob 全树扫描有没有副作用面（读了不该读
   的文件、性能、二进制文件处理）？「常量 == 发现」在 U3-C 模板化过程中会不会产生
   令人误解的红？
5. **基线维护矩阵**：现在 7 个常量。U5-B / U6 / U3-C 各需同步哪几个？遗漏其一会不会
   静默通过？有没有常量改了而**没有任何断言**会发现？

## 四 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给出 `file:line` + 一句话说明**在什么输入
或什么改动下这条会出问题**。没有问题的维度请明确写「未发现」，不要省略。
最后单独给一句结论：本轮 BLOCKER 与 HIGH 各几条。

## 五 边界

- 只读，不要修改任何文件；不要连任何数据库或网络服务。
- 不要跑 pytest（`sandbox` fixture 会复制大文件）。可直接用树内
  `backend/.venv/bin/python` 动态加载被测模块，调用 `_body_counts()` /
  `escaping_tmp_paths()` / `suspicious_tmp_lines()` / `_logical_lines()` /
  `check_handoff_constants()` / `_discover_out_of_scope_8011()` 等纯函数验证。
- 不评二线宿主（Codex / OpenCode / dsh）的可跑性 —— 那是另一张卡的范围。
- 不评 `quiz-answer/SKILL.md` 的内容质量 —— 本卡对它只钉计数、一字节未改。
- 不评 `_bmad-output/` 下的文档措辞。
