# 独立复核请求 — CARD-SKILL-PORT-LINT（BATCH-2026-09-07-第十三批 / 车道 U4 / round-2）

## 一 背景与最小读取面（只读这些，不要扩大）

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts`
分支 `card/u4-hosts`。**本轮绑最终 HEAD**：`9303201a`（U4-A 末 commit）→ **`3b98081a`**。
区间内两个 commit：`ae6a68f3`（round-1 审的那个）+ `3b98081a`（按 round-1 意见整改）。

这张卡：(1) 新增一道静态门，把 vault 内 9 份 SKILL.md 与 7 份 scripts 的「可移植性指标」
钉成基线，新增命中即红、减少也红；(2) 在 `start-exam-board` 一份 SKILL.md 上做最小整改。

**请只读下面这些**：

1. 全区间代码 diff：
   `git -C <树根> diff 9303201a 3b98081a -- . ':(exclude)_bmad-output'`
2. round-1 之后的整改 diff（本轮重点）：
   `git -C <树根> diff ae6a68f3 3b98081a -- . ':(exclude)_bmad-output'`
3. 新测试全文：`backend/tests/skills/test_skill_portability_lint.py`
4. 上一轮你的报告：`_bmad-output/审查/codex-review-CARD-SKILL-PORT-LINT-r1.md`
5. 基线两份：`_bmad-output/审查/evidence-skill-lint/baseline-counts-open-20260908T090832.txt`
   与 `baseline-counts-close-20260908T092313.txt`

**不要读**：`quiz-answer/SKILL.md` 正文（3076 行，本卡一字节未改）、live vault 路径下的
文件、其它车道的卡文。

## 二 round-1 三条意见的处置（请逐条独立核对是否真的修好，以及整改本身有没有引入新缺陷）

**HIGH — `/tmp/cls-exam/../x` 穿越在命名空间之后**：
新增第四类判据 `check_escaping_tmp()` —— 把每份 SKILL.md 的越界 `normpath` **多重集**
钉成基线（`ESCAPING_TMP_BASELINE`，现状 6 处，全是只钉不改的已知项）。它与子串计数
**互补**：计数管「命中数变没变」，越界判据管「命中的路径规范化后指向哪里」。
配 3 条参数化负控（`../x` / `a/../../y` / `./../z`），每条**同时**断言「计数判据看不见」
与「越界判据看得见」。另加 `test_two_judges_cover_each_other_without_gap` 分工表：6 个
形态逐个钉住各自该被哪条拦下，并断言「两条都放行」的行必须真在命名空间内。

**MEDIUM — `U6_SCRIPTS_BASELINE` 的 `==` 断言与其交接注释自相矛盾**：
改为两条各管一面 —— (i) 原两份 `⊆` 该常量（不许删交接项）；(ii) 新登记条目必须落在
U6 的两个 scripts 目录下（不许拿它当垃圾桶、让别人地盘的脚本免于 `SCRIPTS_BASELINE` 的审阅）。
「未登记的新脚本立刻红」仍由层 3 文件集合精确相等保证。新增用例正反双向验证。

**MEDIUM — 一增一减总数相等仍绿**：
基线由「钉裸值差值」改为钉 `tmp_all` / `tmp_ns` / `p8011_all` / `p8011_ns` **四端**；
差值降级为派生算式 `bare_tmp()` / `bare_8011()`，只用于断言消息与对账用例。
层 2 由 7 指标增至 9 指标。配负控（前置断言「裸值此时不变」以保归因）。

## 三 请按重要性排序回答的问题

1. **整改有没有引入新缺陷**？重点看 `check_escaping_tmp()` 与 `_TMP_TOKEN_RE`：
   切分规则是「遇空白/反引号/引号/圆括号/中文括号/逗号/分号/冒号就停」。
   有没有输入能让一个真实的越界路径被切成看起来合规的 token，或反过来把合规路径
   切成越界？`normpath` 对 symlink 无感知这一点在本场景重要吗？
2. **两条判据的分工是否真的无缝隙**？作者的分工表声称「每个不合规形态都至少被一条
   拦下，完全放行的只有真正合规的两个」。请找反例：一个既不抬高裸值、`normpath`
   后又在命名空间内、但实际仍是可移植性债的形态。
3. **U6 那条整改后的判据是否够**？现在允许 U6 往常量里加 U6 目录下的任意脚本。
   有没有办法在「合法登记」的掩护下把真实的债放进来而无人察觉？
4. **哪条断言其实不承重**？逐条检查：有没有恒真的断言、有没有负控其实是被别的断言
   打红的（而不是它点名的那一层）、有没有 fixture 前提不成立导致用例空跑？
   `sandbox` fixture 只复制 `skills/` 与 `scripts/` 两个子树 —— 这会不会让某些用例的
   前提悄悄失效？
5. **门根本没测量的面**：可移植性债还能藏在哪里而这道门完全看不见？例如
   `skills/*/templates/`、skills 目录下的非 `.py` 文件、`canvas-vault/.claude/` 下
   skills 与 scripts 之外的目录、写死路径的其它形态（`~/`、`$HOME`、`/var/folders`、
   `8011` 之外的写死端口、`localhost` 之外的回环写法）。请具体指出**真实存在的**
   债形态逃出了全部四类判据。
6. **基线维护路径**：门要求「减少也红，逼人同步基线常量」。一个想省事的人怎么在
   「合法更新基线」的掩护下把真实的债一起放进去？`BASELINE` / `ESCAPING_TMP_BASELINE` /
   `QUIZ_ANSWER_BASELINE` 三者的覆盖面有没有互相校验？有没有哪个常量改了但没有任何
   断言会发现？

## 四 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给出 `file:line` + 一句话说明**在什么输入
或什么改动下这条会出问题**。没有问题的维度请明确写「未发现」，不要省略。
最后请单独给一句结论：本轮 BLOCKER 与 HIGH 各几条。

## 五 边界

- 只读，不要修改任何文件；不要连任何数据库或网络服务。
- 不要跑 pytest（`sandbox` fixture 会复制大文件）。你可以直接用树内的
  `backend/.venv/bin/python` 动态加载被测模块、调用 `_body_counts()` /
  `escaping_tmp_paths()` 等纯函数来验证你的猜想。
- 不评二线宿主（Codex / OpenCode / dsh）的可跑性 —— 那是另一张卡的范围。
- 不评 `quiz-answer/SKILL.md` 的内容质量 —— 本卡对它只钉计数、一字节未改。
- 不评 `_bmad-output/` 下的文档措辞。
