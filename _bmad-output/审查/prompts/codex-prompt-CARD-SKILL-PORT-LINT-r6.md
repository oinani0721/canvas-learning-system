# 独立复核请求 — CARD-SKILL-PORT-LINT（BATCH-2026-09-07-第十三批 / 车道 U4 / round-6）

## 一 背景与最小读取面（只读这些，不要扩大）

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts`
分支 `card/u4-hosts`。**本轮绑最终 HEAD**：`9303201a`（U4-A 末 commit）→ **`a709856a`**。

轮次说明：r5 是 D-15 的 5 轮上限、仍有 HIGH 4，车道已按规矩停下交人审；**用户随后
授权继续**，故有本轮。r5 之后的唯一代码 commit 是 `a709856a`（本轮重点）。

这张卡：(1) 新增静态门，把 vault 内 9 份 SKILL.md 与 7 份 scripts 的「可移植性指标」
钉成基线，新增命中即红、减少也红；(2) 在 `start-exam-board` 一份 SKILL.md 上做最小整改。

**请只读下面这些**：

1. r5 之后的整改 diff（**本轮重点**）：`git -C <树根> diff 4446ac81 a709856a -- . ':(exclude)_bmad-output'`
2. 全区间代码 diff：`git -C <树根> diff 9303201a a709856a -- . ':(exclude)_bmad-output'`
3. 新测试全文：`backend/tests/skills/test_skill_portability_lint.py`
4. 你上一轮的报告：`_bmad-output/审查/codex-review-CARD-SKILL-PORT-LINT-r5.md`

**不要读**：`quiz-answer/SKILL.md` 正文（3076 行，本卡一字节未改）、live vault 下的文件、
其它车道的卡文。

## 二 round-5 四条 HIGH 的处置：不再补正则，改用真解析（v3）

你 r5 的四条 HIGH 我判定为**同一根因**：手写切分器在模拟解析器，而模拟得不够像。
r1→r5 五轮换了五种坏法，都是这个根因的皮。所以 v3 不再模拟：

- **① fence 整块试 `ast.parse`** —— Python 在**解析期**就把隐式拼接折成单个
  `Constant`（`("/tmp/cls-exam/" r"." "./x")` 直接得到 `/tmp/cls-exam/../x`），
  三引号、`r`/`u` 前缀、`\x2e` 转义全部由解析器还原；显式 `+` 的常量链由
  `_fold_str()` 折叠（折进链里的 `Constant` 不再单独计一次，避免同处两候选）。
- **② 整块非 Python**（SKILL.md 的 fence 多是 bash + heredoc）⇒ **逐行降级**：
  先试单行 `ast.parse`，再试 `shlex.split(posix=True)` 取真 shell 词。
- **③ 裸 token 正则始终再扫**（覆盖 `mkdir -p /tmp/cls-exam/` 这类未加引号片段）。
- **④ 散文只认 markdown backtick span**。
- **⑤ `_fence_blocks` 认 ``` 与 `~~~`**，闭合要求**同字符且长度 ≥ 开启**（四反引号
  块内的三反引号内容行不再切换状态）。

⇒ **每个 `Constant` / shell 词是独立候选**，v2 的「保守拼组」整个删除，HIGH-1 的
遮蔽（那是 v2 引入的回归，比不拼更糟）随之消失。

**方法**：先在原型上把 r1→r5 的**全部 23 个反例**跑通（23/23），再集成；树上基线与
v2 逐字一致，未改任何基线常量。各条 HIGH 都补了负控；HIGH-1 的负控**直接对纯函数
发问**（放进副本会多一个 `/tmp/cls-exam/` 而改变计数，归因不干净），并带验伪锚
「合规的第一个参数不得被误报」。跨行拼接负控改为对**越界判据**发问（原断言钉的是
v2 机制，v3 下不再成立）。

## 三 请按重要性排序回答的问题

1. **v3 有没有引入新缺陷 / 新的等计数缺口**？请找：九项计数不变、越界集合不变、
   可疑行集合不变，但实际引入可移植性债的替换形态。重点可疑面：
   - `_py_strings` 只收 `ast.Constant(str)` 与 `+` 常量链 —— f-string（`JoinedStr`）、
     `%` / `.format()` / `str.join` 拼出的路径会不会整类漏检？这算不算「运行期展开」
     那一档（已由可疑行判据兜）还是新的静态可判漏检？
   - `_fold_str` 只折 `BinOp(Add)`；`*` 重复、下标、切片呢？
   - 整块 `ast.parse` 成功但**语义上是别的语言**（例如一段恰好是合法 Python 的
     YAML/JSON）会不会导致该块的 shell 词被漏扫？
   - `shlex.split(posix=True)` 对 `$'...'`、反引号命令替换、heredoc 体的行为？
2. **fence 状态机**：`_fence_RE` 只匹配行首（允许前导空白）的 ``` / ~~~。
   列表缩进内的 fence、行内三反引号、fence info string 带反引号，会不会错判？
   未闭合 fence 到文件尾的行为是否安全（保守 = 当代码块）？
3. **哪条断言不承重**？特别看本轮新增的 6 条负控（5 条参数化 + `~~~` + 四反引号 +
   HIGH-1 纯函数）—— 有没有前提不成立而空跑、被别的判据代打红、或验伪锚形同虚设？
4. **`_logical_lines` 现在只服务可疑行判据**（越界判据不再用它）。它与 `_fence_blocks`
   的行号计算是否一致？基线 `[98]` / `[577]` 在 v3 下是否仍指向同一物理行？
5. **收尾判断**：这道门现在的残余风险面（已登记的保守误报 + 静态不可判的运行期展开）
   是否都已如实声明？还有没有**未声明的**、可静态确定的漏检？

## 四 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给出 `file:line` + 一句话说明**在什么输入
或什么改动下这条会出问题**。没有问题的维度请明确写「未发现」，不要省略。
最后单独给一句结论：本轮 BLOCKER 与 HIGH 各几条。

## 五 边界

- 只读，不要修改任何文件；不要连任何数据库或网络服务。
- 不要跑 pytest（`sandbox` fixture 会复制大文件）。可直接用树内
  `backend/.venv/bin/python` 动态加载被测模块，调用 `_body_counts()` /
  `_fence_blocks()` / `_py_strings()` / `_sh_words()` / `_fold_str()` /
  `escaping_tmp_paths()` / `suspicious_tmp_lines()` / `check_handoff_constants()` /
  `_discover_out_of_scope_8011()` 等纯函数验证。
- 不评二线宿主（Codex / OpenCode / dsh）的可跑性 —— 那是另一张卡的范围。
- 不评 `quiz-answer/SKILL.md` 的内容质量 —— 本卡对它只钉计数、一字节未改。
- 不评 `_bmad-output/` 下的文档措辞。
