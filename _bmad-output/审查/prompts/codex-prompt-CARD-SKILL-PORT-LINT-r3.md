# 独立复核请求 — CARD-SKILL-PORT-LINT（BATCH-2026-09-07-第十三批 / 车道 U4 / round-3）

## 一 背景与最小读取面（只读这些，不要扩大）

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts`
分支 `card/u4-hosts`。**本轮绑最终 HEAD**：`9303201a`（U4-A 末 commit）→ **`98ca073c`**。

区间内四个 commit：`ae6a68f3`（初版，round-1 审的）→ `3b98081a`（round-1 整改，round-2 审的）
→ `8bb94475`（作者自查：钉住门测不到的 4 处 8011）→ `98ca073c`（round-2 整改）。

这张卡：(1) 新增一道静态门，把 vault 内 9 份 SKILL.md 与 7 份 scripts 的「可移植性指标」
钉成基线，新增命中即红、减少也红；(2) 在 `start-exam-board` 一份 SKILL.md 上做最小整改。

**请只读下面这些**：

1. 全区间代码 diff：`git -C <树根> diff 9303201a 98ca073c -- . ':(exclude)_bmad-output'`
2. round-2 之后的整改 diff（**本轮重点**）：`git -C <树根> diff 3b98081a 98ca073c -- . ':(exclude)_bmad-output'`
3. 新测试全文：`backend/tests/skills/test_skill_portability_lint.py`
4. 你上两轮的报告：`_bmad-output/审查/codex-review-CARD-SKILL-PORT-LINT-r1.md` 与 `-r2.md`

**不要读**：`quiz-answer/SKILL.md` 正文（3076 行，本卡一字节未改）、live vault 下的文件、
其它车道的卡文。

## 二 round-2 七条意见的处置（请逐条独立核对是否真修好，以及整改本身有没有引入新缺陷）

作者已逐条**实测复现**了你的每个反例，确认全部属实。处置如下：

**HIGH（三个子问题）** —— 不追求「完美切分」（那是启发式，修一次换一种坏法），三管齐下：
- `_TMP_TOKEN_RE` 加左边界 `(?<![A-Za-z0-9_.~$-])`，要求 `/tmp/` 是绝对路径起点 → 修 (c) 的误提取；
- `tmp_ns` 改用带左边界的 `_TMP_NS_RE` 计数（**放行端要窄、计入端可宽**：`tmp_all` 仍用裸子串，
  把 `/var/cache/tmp/x` 也算成债是偏保守）→ 修 (c) 的**等计数替换**；
- 新增 `suspicious_tmp_lines()` / `check_suspicious_tmp_lines()`：**不依赖 token 切分**的行级
  判据，凡 `/tmp` 与 `..`（或变量展开）同行一律要登记 → 修 (a)(b)，并覆盖 MEDIUM-4。
  基线 `SUSPICIOUS_TMP_LINES_BASELINE`（现状仅 quiz-answer `:98` 一行，属误报友好项，
  登记而非放宽判据）。

**MEDIUM-2**（删基线条目静默失明）→ `test_every_per_skill_baseline_covers_all_nine_skills`，
三个 per-skill 基线（`BASELINE+QUIZ`/`ESCAPING_TMP`/`SUSPICIOUS_TMP_LINES`）一起钉 `== 9 份`。

**MEDIUM-3**（U6 合法登记锁不住零余量、能挪走主基线项）→ 正式判据加「新登记项必须零余量」
+「只收 U6 地盘」。带债的脚本必须走 `SCRIPTS_BASELINE` 的人工审阅。

**MEDIUM-5**（越界负控用追加 ⇒ 计数判据也红 ⇒ 没证明「计数看不见」）→ 改成
**等计数替换** `_swap_in_start_exam_board()`，并**实际断言** `check_body(...) == []`。

**MEDIUM-6**（U6 用例自己重写集合判断）→ 抽出正式判据 `check_handoff_constants()`
（三个基线全走参数，便于负控喂变异常量），用例全部经由它；作者实测「判据退回 round-1 的
`== U6_SEED`」时，那条「必须放行」的用例会翻转。

**LOW-8**（多重集诊断用 `in` 致「缺失=[]」）→ 改 `Counter` 比次数。

**登记不修**：MEDIUM-4 变量展开的运行期落点（静态门固有边界，已由行级判据要求登记）；
MEDIUM-7 覆盖面外的 cwd 依赖与其它绝对路径形态（你亦指出仓内无可核实实物）。作者另行把
「门测不到的 4 处 8011」做成了 `OUT_OF_SCOPE_8011` 常量 + 带验伪锚的用例（commit `8bb94475`）。

## 三 请按重要性排序回答的问题

1. **整改有没有引入新缺陷**？重点看三条判据的**相互作用**：左边界正则、`tmp_ns` 的严格
   计数、行级判据。有没有输入让它们互相抵消？`_TMP_NS_RE` 的左边界字符集
   `[A-Za-z0-9_.~$-]` 有没有该排除却没排除的字符（或反过来）？
2. **三条判据合起来是否仍有缺口**？请找一个**等计数替换**形态：替换后九项计数全不变、
   越界判据为空、可疑行判据也为空，但实际引入了可移植性债。
   （作者的 `test_three_judges_cover_each_other_without_gap` 断言「三列全放行 ⇒ 必须真在
   命名空间内」，请攻击这条。）
3. **`suspicious_tmp_lines` 的行级口径**：它按 `splitlines()` 逐行判。有没有办法让一处
   `..` 与 `/tmp` **跨行**从而两者不同行（例如 Markdown 软换行、表格、代码块折行），
   于是判据看不见？基线里 quiz-answer `:98` 那条登记是否掩盖了同文件其它真问题？
4. **哪条断言其实不承重**？逐条检查新增用例：有没有恒真的、有没有被别的断言代为打红的、
   有没有前提不成立而空跑的。特别看 `test_handoff_judge_is_load_bearing` 的六个变异是否
   真的各自只被自己那条拦下。
5. **基线维护路径**：现在有五个常量（`BASELINE` / `QUIZ_ANSWER_BASELINE` /
   `ESCAPING_TMP_BASELINE` / `SUSPICIOUS_TMP_LINES_BASELINE` / `OUT_OF_SCOPE_8011`）加
   `SCRIPTS_BASELINE` / `U6_SCRIPTS_BASELINE`。它们之间有没有不一致的可能？有没有哪个改了
   而没有任何断言会发现？U5-B 与 U6 rebase 时各需要动哪几个，遗漏其一会不会静默通过？

## 四 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给出 `file:line` + 一句话说明**在什么输入
或什么改动下这条会出问题**。没有问题的维度请明确写「未发现」，不要省略。
最后单独给一句结论：本轮 BLOCKER 与 HIGH 各几条。

## 五 边界

- 只读，不要修改任何文件；不要连任何数据库或网络服务。
- 不要跑 pytest（`sandbox` fixture 会复制大文件）。可直接用树内
  `backend/.venv/bin/python` 动态加载被测模块，调用 `_body_counts()` /
  `escaping_tmp_paths()` / `suspicious_tmp_lines()` / `check_handoff_constants()` 等纯函数验证。
- 不评二线宿主（Codex / OpenCode / dsh）的可跑性 —— 那是另一张卡的范围。
- 不评 `quiz-answer/SKILL.md` 的内容质量 —— 本卡对它只钉计数、一字节未改。
- 不评 `_bmad-output/` 下的文档措辞。
