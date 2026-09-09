# 独立复核请求 — CARD-SKILL-PORT-LINT（BATCH-2026-09-07-第十三批 / 车道 U4 / round-7）

## 一 背景与最小读取面（只读这些，不要扩大）

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts`
分支 `card/u4-hosts`。**本轮绑最终 HEAD**：`a709856a` → **`26d6df62`**。

轮次说明：r5 是 D-15 的 5 轮上限，用户随后授权继续，故有 r6、r7。
r6 之后有三个代码 commit：`ee4d0913`（第六条判据，你 r6 收尾时已察觉 HEAD 前进）、
`069c2150`（按你 r6 的四类 HIGH 整改）、`26d6df62`（按另一路独立复核整改，**本轮重点**）。

这张卡：(1) 新增静态门，把 vault 内 9 份 SKILL.md 与 7 份 scripts 的「可移植性指标」
钉成基线，新增命中即红、减少也红；(2) 在 `start-exam-board` 一份 SKILL.md 上做最小整改。

**请只读下面这些**：

1. r6 之后的整改 diff（**本轮重点**）：`git -C <树根> diff a709856a 26d6df62 -- . ':(exclude)_bmad-output'`
2. 全区间代码 diff：`git -C <树根> diff 9303201a 26d6df62 -- . ':(exclude)_bmad-output'`
3. 新测试全文：`backend/tests/skills/test_skill_portability_lint.py`
4. 你上一轮的报告：`_bmad-output/审查/codex-review-CARD-SKILL-PORT-LINT-r6.md`

**不要读**：`quiz-answer/SKILL.md` 正文（3076 行，本卡一字节未改）、live vault 下的文件、
其它车道的卡文。

## 二 round-6 四类 HIGH 的处置

先实测再动手。**HIGH-1 的七种表达式形态**（`f"…{'.'}…"` / `% "."` / `.format(".")` /
`"".join(...)` / `"." * 2` / `"."[0]` / `".x"[:1]`）在 `ee4d0913` 引入的**第六条判据
（动态拼接 `_has_dynamic_tmp_join`）**下已 7/7 报红——那个 commit 在你审的 `a709856a`
之后，所以你 r6 看不到它。这一类不重复修。

其余 8 个反例逐个复现后分两档：

**【纯 bug，直接修】**
- **HIGH-4 fence 边界**：`_fence_blocks` 现在判定「开启标记同一行若还有同字符、
  长度 ≥ 开启的 run ⇒ 它是**行内 code span** 不是 fence」。你举的
  ` ```/tmp/cls-exam/../x``` ` 原先整行被当标记删掉，现在退回散文由 backtick span
  与裸 token 接管。CommonMark 亦规定反引号 fence 的 info string 不得含反引号。
  （你 r6 提的「列表缩进内 fence」实测原本就已抓到，未改。）
- **HIGH-3 逐行降级丢缩进语义**：补 `textwrap.dedent` 整块重试 + 逐行 `line.strip()`
  重试（缩进行单跑是 `IndentationError`）；第六条判据同修。

**【静态不可判 ⇒ 要求登记：新增第八条判据 `opaque_tmp_lines`】**
你 r6 的 HIGH-1（shell 命令替换）、HIGH-2（JSON `..\/`、shell 反斜杠续行）、
HIGH-3（heredoc 续行）我判定为**同一根因**：v3 的真解析解决了「字面量怎么写」，
没有解决「字面量被谁读」——`ast` 能 parse 出一个 `Constant`，但那个值只在 Python
语义下成立（`\/` 在 JSON 是 `/`，在 Python 是两个字符）。

处置与第六条、兜底可疑行完全同档：**不猜落点，只认记号并要求登记**。记号 =
fence 内的反引号（只可能是 shell 命令替换）或任意反斜杠（转义含义由读它的语言决定；
行尾反斜杠还是续行）。按**行尾反斜杠续行组**扫（链长上限 6）——你那个
`P='\`␊`/tmp/cls-exam/x'` 把反斜杠留在上一行、`/tmp` 留在下一行，物理行粒度两边都
不触发；`_logical_lines` 合并时会擦掉反斜杠（那是它的活），所以第八条自己拼、原样保留。

全树实测命中 **0** ⇒ 基线全 9 份为空，登记成本为零。

另补第七条判据（散文「上一级目录」，`ee4d0913` 之后加、原先无负控）的三段归因负控。

判据 6 → 8，测试 73 → 79。你 r6 的 8 个反例现 8/8 报红。

## 二之二 `26d6df62`：另一路独立复核（50 agent，每条候选三票裁决）的 8 条处置

r7 送审前另跑了一路多视角复核，绑的是 v3（早于第六/八条判据）。它报回 8 条，
逐条在当时 HEAD 实测后 4 条已被第六/七/八条关闭，4 条真漏，按根因归并成三项：

**① 逐物理行降级 = 整类盲区 ⇒ 新增 `_parse_units` 按语法单元切**（原报 BLOCKER×2）
本仓每份 SKILL.md 的 python 都装在 ``python3 - <<'PYEOF'`` heredoc 里 ⇒ 整块
`ast.parse` **恒失败** ⇒ **恒走降级**。降级按物理行做，则任何跨物理行的语法结构
整类失明：`P = os.path.join(`␊`    "/tmp/cls-exam/", updir, "x")` 第一行不完整、
第二行括号不平衡，`ast` 与 `shlex` 双双弃权，只剩裸 token 看到合规前缀
（`black` 折长行就会自然产生这个形态）。现改为从每行起累加至多 8 行、第一次
`ast.parse` 成功即认作一个语法单元并跳过整段；整窗都失败则该行单独退回。
越界判据与第六条判据都改走语法单元。

**② `_has_dynamic_tmp_join` 从节点类型白名单换成完备的取反口径**（原报 HIGH×2）
原白名单是 `BinOp(+/%)` / `JoinedStr` / `Call`，于是 `IfExp` / `Subscript` /
`Tuple` / bytes 常量整类漏掉。`P = "/tmp/cls-exam/x" if 0 else "/etc/passwd"`
的真实落点是 `/etc/passwd`，计数纹丝不动（左边那个字面量还在），越界判据又因
`"/tmp" not in "/etc/passwd"` 早退。现改为：从每个含 `/tmp` 的常量往上走父链，
只要祖先还能被 `_fold_str()` **完全折成一个字符串**就继续上走；一路折到语句层
⇒ 纯静态字面量（交越界判据）；中途遇到折不出来的祖先 ⇒ 要求登记。bytes 一并纳入。

**③ 两处覆盖面缺口**（原报 HIGH×2）
- fence 标记行原先整行不进 body ⇒ ``` ``` P = "/tmp/cls-exam/../x" ``` 对全部集合
  判据隐形。现改为标记行按散文产出，由裸 token 接管。
- 层 3 `SCRIPT_METRICS` 一个端口指标都没有，而层 2 对 SKILL.md 钉了 8011 两端
  ——口径分叉。补 `p8011_all` / `p8011_ns` / `localhost` 三项，7 份实测全 0。

新增负控 ⑮⑯⑰⑱ + `_parse_units` 验伪锚。测试 79 → 88。
⑰ 的归因**如实降级**：该形态会多开一个 fence、把后续每块的内外状态整体翻转
（实测 `:430`/`:577` 随之落进 fence，第八条也跟着红），三段归因不成立 ⇒ 改为对
纯函数发问 + 验伪锚（标记行不含路径时必须绿，证明红来自内容而非 fence 结构）。

两路复核合并 16 个形态现 16/16 报红；树上五条集合判据零漂移。

## 三 请按重要性排序回答的问题

1. **第八条判据有没有引入新缺陷**？重点：
   - 记号集合只有「反引号 + 反斜杠」，且**只在 fence 内**生效。散文侧同类形态
     （backtick span 里的命令替换）是不是漏了一整类？
   - 续行组的链长上限 6、以及「组内任一行含 `/tmp` 且组内任一行含记号」这个或语义，
     会不会在长 shell 命令块上产生大批误报（现状 0，但 U6 改 scripts 时呢）？
   - 空基线 + 集合语义：同一物理行既是续行组首又被别的组覆盖，行号会不会重复或丢失？
2. **`_fence_blocks` 的新判定**：「同行有同字符 ≥ 同宽 run ⇒ 不是 fence」会不会
   误伤合法 fence？例如 info string 本身含 `~~~`、或一行内先开后闭再开的形态。
   未闭合 fence 到文件尾的行为是否仍保守（当代码块）？
3. **`_parse_units` 的累积窗口**：窗口上限 8、「第一次 parse 成功即认作一个单元并
   跳过整段」这个贪心策略，会不会把两条本该独立的语句吞进同一个单元、或反过来在
   某种缩进下切错？树上零漂移是否只是运气好（现有 fence 形态单一）？
4. **`_has_dynamic_tmp_join` 的取反口径**：`_STATEMENT_NODES` 停止上溯的名单
   （Assign/AnnAssign/AugAssign/Expr/Return）是否漏了会导致**误放**的语句类型
   （`With` / `For` / `comprehension` / `keyword` / `Starred` 等）？父链走法在
   `ast.walk` 重复访问下会不会漏判？
5. **八条判据合起来是否仍有等计数缺口**？请找：九项计数不变、越界/可疑行/动态拼接/
   散文/不透明五个集合都不变，但实际引入可移植性债的替换形态。
6. **哪条断言不承重**？特别看本轮新增的 7 条负控（第八条参数化 2 条 + 第七条 1 条）
   与 1 条验伪锚（`test_opaque_judge_does_not_fire_on_plain_literals`）——有没有前提
   不成立而空跑、被别的判据代打红、或验伪锚形同虚设？三段归因里的「② 其余判据都
   看不见」是否真的成立？
7. **收尾判断**：这道门现在的残余风险面是否都已如实声明？还有没有**未声明的**、
   可静态确定的漏检？

## 四 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给出 `file:line` + 一句话说明**在什么输入
或什么改动下这条会出问题**。没有问题的维度请明确写「未发现」，不要省略。
最后单独给一句结论：本轮 BLOCKER 与 HIGH 各几条。

## 五 边界

- 只读，不要修改任何文件；不要连任何数据库或网络服务。
- 不要跑 pytest（`sandbox` fixture 会复制大文件）。可直接用树内
  `backend/.venv/bin/python` 动态加载被测模块，调用 `_body_counts()` /
  `_fence_blocks()` / `_py_strings()` / `_sh_words()` / `_fold_str()` / `_quiet_parse()` /
  `escaping_tmp_paths()` / `suspicious_tmp_lines()` / `dynamic_tmp_join_lines()` /
  `parent_dir_prose_lines()` / `opaque_tmp_lines()` / `_parse_units()` /
  `_has_dynamic_tmp_join()` / `_script_counts()` / `check_handoff_constants()` /
  `_discover_out_of_scope_8011()` 等纯函数验证。
- 不评二线宿主（Codex / OpenCode / dsh）的可跑性 —— 那是另一张卡的范围。
- 不评 `quiz-answer/SKILL.md` 的内容质量 —— 本卡对它只钉计数、一字节未改。
- 不评 `_bmad-output/` 下的文档措辞。
