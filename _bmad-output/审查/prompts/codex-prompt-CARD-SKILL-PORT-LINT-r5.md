# 独立复核请求 — CARD-SKILL-PORT-LINT（BATCH-2026-09-07-第十三批 / 车道 U4 / round-5 · 最终轮）

## 一 背景与最小读取面（只读这些，不要扩大）

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts`
分支 `card/u4-hosts`。**本轮绑最终 HEAD**：`9303201a`（U4-A 末 commit）→ **`4446ac81`**。

区间内八个 commit（前五个你已审过或见于存档）：`ae6a68f3` 初版 → `3b98081a` r1 整改 →
`8bb94475` 作者自查 → `98ca073c` r2 整改 → `83cd6104` r3 整改 → `4446ac81` r4 整改
（**本轮重点**）。这是 D-15 上限 5 轮的最后一轮。

这张卡：(1) 新增静态门，把 vault 内 9 份 SKILL.md 与 7 份 scripts 的「可移植性指标」
钉成基线，新增命中即红、减少也红；(2) 在 `start-exam-board` 一份 SKILL.md 上做最小整改。

**请只读下面这些**：

1. 全区间代码 diff：`git -C <树根> diff 9303201a 4446ac81 -- . ':(exclude)_bmad-output'`
2. r4 之后的整改 diff（**本轮重点**）：`git -C <树根> diff 83cd6104 4446ac81 -- . ':(exclude)_bmad-output'`
3. 新测试全文：`backend/tests/skills/test_skill_portability_lint.py`
4. 你上四轮的报告：`_bmad-output/审查/codex-review-CARD-SKILL-PORT-LINT-r1..r4.md`

**不要读**：`quiz-answer/SKILL.md` 正文（3076 行，本卡一字节未改）、live vault 下的文件、
其它车道的卡文。

## 二 round-4 十一条意见的处置（请逐条独立核对是否真修好，以及整改本身有没有引入新缺陷）

**HIGH-1 + HIGH-2（同根因：正则看不见引号上下文）⇒ 越界判据 v2 根本性重构**，
不再打正则补丁：
- **字面量原子化**：`_literals_in()` 扫描引号字面量（`'`/`"`/backtick；fence 行全认，
  散文行只认 backtick span）——引号内的空格/括号/逗号/分号/中文标点都是路径字符，
  不再是「路径起点/截断」证据。你 r4 的 `"/var/cache /tmp/…"` 与 `"/var/cache(/tmp/…"`
  两种冒充均被整串 normpath 抓住。
- **相邻字面量拼接组**：`_concat_groups_in()` 把 fence 逻辑行内间隙只含空白/括号的
  相邻字面量整组求值——混合引号跨行（`("/tmp/cls-exam/"`␊`'../x')`，逻辑行合并已放宽
  到任意引号混用、原样拼接）与单行点号拼接（`"." "./x"`）都被拼组后的 normpath 抓住。
  ⚠️ 作者自己踩过一个 span 约定坑：拼接间隙必须取「前闭引号+1 → 后开引号」，
  否则间隙永含开引号、分组恒失败——已修并有覆盖表行。
- **裸 token**（`mkdir -p /tmp/cls-exam/`）沿用 r3 白名单边界正则全文扫描；未加引号的
  `/var/cache /tmp/cls-exam/x` 是两个 shell 词、后者本就在命名空间内，不构成攻击；
  攻击必须进引号——已由原子性接管。
- 越界基线随 v2 重测（集合语义：相同 `(候选, normpath)` 去重）：board-recap 多
  `/tmp`（`:58`「禁写 /tmp」声明）、start-exam-board 多 `/tmp`（`:128`）与
  `Bash: mkdir -p /tmp/cls-exam`（`:188` 变更行 backtick 命令 span）、quiz-answer
  去重为 2 条。

**MEDIUM-3（引号内分号/中文逗号变质）**：字面量原子化直接封住（不再依赖逗号入 token）。
**MEDIUM-4（跨行负控被 :577→578 移位代打红）**：改为**直接函数断言**——合并在 ⇒ 拼出的
逻辑行含 `..`；拼接组求值 ⇒ 越界消息含 `/tmp/exam-candidates.json`。两断言各自只被
自己考的那层满足。
**MEDIUM-5（seed 带债迁移被 seed 完整性堵死）**：seed 改「两张表至少一张登记」；
参数用例双向：迁移放行 / 留驻拦截（后者同时抓住 r2 版 seed 豁免的回退）。
**MEDIUM-6（动态扫描副作用）**：符号链接不跟随、>1MB 不整读、`.DS_Store`/`__pycache__`/
`.git` 跳过；未跟踪文本文件**仍读（有意）**——覆盖面外的新债就该被看见。
**LOW-7/9（全角标点紧贴、fence 裸 token 带尾逗号）**：登记为保守误报方向，不修。
**LOW-10**：覆盖表末尾「整字面量 normpath」断言如实声明为纵深防御（退回 `startswith`
不会被现有合规行抓住——不存在前缀失败而 normpath 成立的合规形态）；seed 豁免回退已由
上述留驻拦截用例覆盖。
**LOW-11（指标键无消费断言）**：每张 per-file 表钉 `set(键) == 指标集`。
另：对照组负控补齐越界/可疑行两条判据（r2 遗留）。

## 三 请按重要性排序回答的问题

1. **v2 有没有引入新缺陷**？重点：`_literals_in` 的扫描器（同种引号闭合、反斜杠转义、
   未闭合保守取到行尾）——有没有形态让一个真实越界字面量被错误闭合/吞掉（漏检方向）？
   `_concat_groups_in` 的间隙集合 `[\s()\[\]{}+]`——元组/函数调用参数会不会被误拼
   （误报方向可接受，漏拼呢）？fence 状态机（``` 行切换）对嵌套/未闭合 fence 的行为？
2. **五条判据合起来是否仍有等计数缺口**？请找：九项计数不变、越界集合不变、可疑行集合
   不变，但实际引入可移植性债的替换形态。
3. **哪条断言不承重**？特别看 r4/r5 新增的直接函数断言与 17 行覆盖表——有没有前提不
   成立而空跑的、被别的判据代为打红的？
4. **v2 基线本身**：三条新登记的越界条目（board-recap `/tmp`、start-exam-board `/tmp`
   与 backtick 命令 span）会不会让 U5-B/U6 rebase 时产生**令人误解**的红？
5. **收尾判断**：以你的标准，这道门现在的残余风险面（已登记的保守误报 + 无法静态证明
   的运行期行为）是否都已如实声明？还有没有**未声明的**？

## 四 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给出 `file:line` + 一句话说明**在什么输入
或什么改动下这条会出问题**。没有问题的维度请明确写「未发现」，不要省略。
最后单独给一句结论：本轮 BLOCKER 与 HIGH 各几条。

## 五 边界

- 只读，不要修改任何文件；不要连任何数据库或网络服务。
- 不要跑 pytest（`sandbox` fixture 会复制大文件）。可直接用树内
  `backend/.venv/bin/python` 动态加载被测模块，调用 `_body_counts()` /
  `_literals_in()` / `_concat_groups_in()` / `_logical_lines()` / `escaping_tmp_paths()` /
  `suspicious_tmp_lines()` / `check_handoff_constants()` / `_discover_out_of_scope_8011()`
  等纯函数验证。
- 不评二线宿主（Codex / OpenCode / dsh）的可跑性 —— 那是另一张卡的范围。
- 不评 `quiz-answer/SKILL.md` 的内容质量 —— 本卡对它只钉计数、一字节未改。
- 不评 `_bmad-output/` 下的文档措辞。
