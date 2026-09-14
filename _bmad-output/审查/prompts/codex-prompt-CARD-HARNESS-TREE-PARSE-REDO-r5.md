# 复核任务（round-5，轮次上限）：CARD-HARNESS-TREE-PARSE-REDO（`_harness_tree` 解析整体重做）

你是独立复核者，在做一次普通的代码评审：判断一段读配置文件的解析代码在换成 YAML 解析器
之后是否还有行为不一致。只读，不要修改任何文件，不要连接任何数据库或网络服务。

仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills`
审查绑定：`08100483..4eeaeaa6`（本卡全部代码改动；最终 HEAD = `4eeaeaa6`。前四轮审过的中间态依次为
`f7f10be4` / `4d21bc9b` / `e844d6a1` / `34451227`）。

## 一 背景与最小读取面（请只读下列内容，不要扩面）

被改的是 `canvas-vault/.claude/skills/quiz-answer/SKILL.md` 里的 `_harness_tree`。它解析
vault 的 `.canvas-config.yaml` 中的 `harness_tree` 键，决定 `REPO` —— 那棵装着
`backend/scripts/validate_learning_events.py` 的代码树。选错树 = 事件被写去绑定到另一棵
harness，用户看不见。原实现是逐行正则，本卡整体换成 PyYAML 优先 + 缺库时的降级扫描。

round-1～4 的 BLOCKER / HIGH **每轮都是 0**；作者每轮都把「按合并门可登记不阻断」的
MEDIUM 主动修掉，因而产生新 HEAD、需再送一轮。本轮是**轮次上限（第 5 轮）**，之后不再扩范围。
round-4 的三条结论作者**全部接受**：① LOW-1 —— 作者原先「门结构上测不到判据失效、必须另立
变异卡」的登记理由**是错的**，已按复核方给的配方补 3 条孤立输入（无效指令 / 未定义别名 /
未闭引号），逐变体实测构成对角线：每条只让一组判据的删除变红；② MEDIUM-1/2 —— 两处盲区的
表述从「尚未被证明」改为「**已有反例**」，并补上「不只是判成无键回退，也可能**照样采用**
那棵树」这一半；③ LOW-2 —— `_breaks` 八个字符里只有前三个是换行、后五个是非法字符，说明已改。
⛔ 两处盲区仍**登记不修**（堵法只有「重写 PyYAML」或「缺库时对含引号/非平凡结构的 config
一律拒」，后者是用户可见的行为决定，移交主 session）。请评价这两条移交的定性是否准确。

请读：
1. `git diff 08100483 e844d6a1 -- . ':(exclude)_bmad-output'`（本卡全部代码改动）
2. `git diff 34451227 4eeaeaa6 -- . ':(exclude)_bmad-output'`（本轮整改的增量，最该细看）
3. `canvas-vault/.claude/skills/quiz-answer/SKILL.md` 的 `:370-540`（改后的 `_harness_tree`、
   嵌套的 `_degraded_scan` 与唯一调用点；请用 `grep -n "def _harness_tree"` 重新锚，行号会漂）
4. 同文件 F1 判定段（`grep -n "换 PyYAML 一次解决整类问题"` 定位，前后各 25 行）
5. `backend/tests/regression/test_g3_2_review_ledger.py`：`:40-58`（提取被测代码的机制）、
   `:218-268`（子进程执行写点）、既有 8 个 harness_tree 门（`grep -n "def test_g33r2_harness_tree"`
   的前 8 个）、以及本卡新增的全部门（从 `def _disable_tree` 起到文件末尾）
6. `_bmad-output/审查/codex-review-CARD-HARNESS-TREE-PARSE-REDO-r1.md` 与 `-r2-p2.md`（前两轮原文）
7. `_bmad-output/验收单/UAT-CARD-HARNESS-TREE-PARSE-REDO-2026-09-14.md`（作者自述与证据路径）

## 二 round-2 结论的整改自述（请独立核对，不要采信）

1. **MEDIUM-1（空行/注释早退跳过换行字符检查）**：换行类字符判据**前移**到「跳过空行 /
   整行注释」之前。
2. **MEDIUM-2（原文字串与列首形状不能确定键的身份与上下文）**：新增一组「读不懂就停」
   判据 —— 反斜杠、指令行 `%`、锚点 `&`、别名 `*`、标签 `!`、合并键 `<<:`、流式括号 `{` `[`、
   块标量 `|` `>`、一行内成奇数个的引号，命中任一即 fail-closed。
3. **MEDIUM-3（仍接受部分 PyYAML 会整份拒的配置）**：新增文档标记判据 —— `---` / `...`
   出现在**非首个内容行**时 fail-closed（`safe_load` 只收单文档）。该判据**不以「文件里有没有
   这个键」为条件**：没有该键的多文档同样是「PyYAML 整份拒而降级回退」。
4. **LOW-1（"只有两态"的说明漏掉成功分支）**：docstring 改为三态（可证无键 ⇒ 回退 /
   规范写法且整份可读懂 ⇒ 采用该树 / 其余 ⇒ 拒），并写明**不保证**的那一半：本函数不做
   整份语法校验，语法坏在别处的 config 可能被判成「没这个键」而回退。
5. 作者自查另修两处：① `_breaks` 改 `chr()` 拼装（上一版字面量里的 U+2028/U+2029 被写文件的
   工具层展开成真字符落进 SKILL.md）；② 测试参数 `"harness__tree"` 展开后是
   `harness__tree`（双下划线）不是目标键，已改为 `"harness_tree"`。
6. 作者自跑：83（harness_tree 子集）/ 232（整文件）/ 546（tests/skills）全通过；把 SKILL.md
   还原到 `4d21bc9b` 后新增的 9 条参数中有 5 条变红。

## 三 请按重要性回答的问题

0. **「读不懂就停」这组判据的完备性（按来源分类核对，不必给出具体输入）**：现在的判据集
   合 = 换行类字符 / 反斜杠 / 文档标记 / 指令与锚点别名标签合并键 / 流式括号 / 块标量 /
   奇数引号 / 续行 / 「提到这个键就必须是那一种写法」。请按来源分类核对：YAML 里还有哪
   **类**语法形态，能让「逐行读到的那一行」与「PyYAML 解析出的那个键值」不一致，而不属于
   上述任何一类？指出是**哪一类**以及应由哪条判据负责，不需要给出具体配置文本。
1. **过度拒绝的代价是否可接受**：这组判据会把一些 PyYAML 能正常解析的配置也拒掉（例如
   值里含感叹号、或注释里有单个引号）。在「缺库是罕见态、且下游同样需要 PyYAML」这个
   前提下，这个取舍是否成立；有没有哪一条判据的收益明显小于它的误伤。
2. **判据顺序是否还有早退问题**：换行字符与反斜杠已前移，但文档标记判据在「跳过整行注释」
   之前还是之后？续行判据与 `_seen_content` 的更新顺序有没有让某类输入走空？
3. **`_breaks` 改 `chr()` 之后字符集是否仍完整**，与 PyYAML 实际当作换行/非法的字符集相比
   有没有遗漏或多余。
4. **既有 16 个 nodeid 是否仍逐条行为不变**（与前两轮同一张表）。
5. **新门的 49 条参数里，有没有哪几条其实测不到东西**（两条分支都走进同一个早退路径，
   从而「相同」得没有意义）。
6. **作者自述的两处自查修正是否属实**：`_breaks` 现在是否确实不含字面量不可见字符；
   `"harness_tree"` 在 PyYAML 下是否确实还原成 `harness_tree`。

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给出：
- 一句话结论
- `file:line`
- 一句话说明在什么输入下会出现该结果
没有问题的分级请显式写「无」。

## 五 边界

- 只读。不要修改文件，不要运行会写盘的命令，不要连接 7691 / 7687 / 任何数据库。
- 不评 `backend/app/services/learning_event_log.py`（属另一张卡的面）。
- 不评 `test_g3_2_review_ledger.py` 里 harness_tree 区以外那 150 个测试的设计。
- 不评 `canvas-vault/.claude/scripts/fsrs_bridge.py` 与 `decay_beta.py`（本卡零改动）。
