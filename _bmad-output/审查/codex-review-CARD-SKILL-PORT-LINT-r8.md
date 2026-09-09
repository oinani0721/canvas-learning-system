> 批次: BATCH-2026-09-07-第十三批 · 车道 U4 · 卡 CARD-SKILL-PORT-LINT round-8
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-SKILL-PORT-LINT-r8.md)"`
> 审查绑定: `fcab3216`（Codex 自证「收尾时工作区文件仍与提交一致」——本轮送审后未碰被审文件，是 r7 那次的教训）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `OpenAI Codex v0.153.3`(:4) / `workdir: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude`(:6) / `model: gpt-6-astra`(:7) / `sandbox: read-only`(:10) / `reasoning effort: ultra`(:11)

---

复核绑定 **`fcab3216b33a8268fdd90f62b4c62d9e4259800b`**，测试文件 blob 为 `769589140f694375d3422fbd897e9c1c6d62226e`，收尾时工作区文件仍与提交一致。未修改文件、运行 pytest、读取禁读正文或连接网络／数据库。

**BLOCKER：未发现。**

**HIGH：5 条，按根因合并。** 以下主反例均经内存验证：安全／坏形态的九项计数相同，五项附加判据均为 `[] → []`。

1. **HIGH — [test_skill_portability_lint.py:420](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:420)：`_unit_end()` 会把合法语句定短，这是新回归。**

   在 shell fence 的 heredoc 中：

   ```sh
   python3 - <<'PYEOF'
   P = ( # )
       "/tmp/cls-exam/"
       + "." + "./x"
   )
   PYEOF
   ```

   注释中的 `)` 抵消真实开括号，第一行即被认作结束；后续路径常量成为独立表达式，拼接关系丢失。安全对照只将 `"."` 改为 `"a"`。**r7 能得到 `/tmp/x`，r8 全漏。**

   同根问题还包括：

   - 字符串内的 `)` 同样能提前抵消深度。
   - `P = """ "` 首行共有四个双引号，奇偶判断认为已闭合，实际三引号仍未结束；因此“三引号只会定长”的声明不成立。
   - `def f(p="/tmp/cls-exam/" + "." * 2 + "/x"):` 括号已经平衡，但仍缺函数体；窗口提前结束，使默认参数、`with`、装饰器中的动态判据由 r7 红变成 r8 漏。
   - **200 行上限仍有漏检**：同一 heredoc 常量拼接，200 行抓到 `/tmp/x`，201 行全部漏掉。固定上限缺口只是移动了边界。

2. **HIGH — [test_skill_portability_lint.py:281](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:281)：转义 opening run 的第一枚反引号，会让新正则丢掉合法 span，这是新回归。**

   精确输入：

   ````text
   执行 \```/var/cache(/tmp/cls-exam/x``
   ````

   本地 CommonMark 解析确认：第一枚反引号被反斜杠转义，剩余两枚开启合法 code span。新正则却按三枚 opening 处理，返回 `spans=[]`；反斜杠又在 span 外，第八条无法兜底。

   安全对照只将路径换成 `/tmp/cls-exam/x`。**r7 能提取完整越界路径，r8 五项全空。** 这是 span 集合真正减少的漏检方向，不是保守误报。

3. **HIGH — [test_skill_portability_lint.py:317](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:317)：列表前缀被同时用于 closing fence，新增了错误闭合。**

   ````text
   ```python
   A = 1
   - ```
   P = "/tmp/cls-exam/" + "." * 2 + "/x"
   ```
   ````

   普通 fence 内的 `- ``` ` 应是内容；新 `_FENCE_RE` 却允许它闭合围栏，后续赋值落入散文。安全对照仅改为普通命名空间内赋值。**r7 动态判据抓到第 4 行，r8 全漏。**

   同一 Markdown 覆盖面还有既存缺口：合法的 `> ```python` 引用内围栏仍整体被当作散文，相同越界表达式也能漏过；不另计一条 HIGH。

4. **HIGH — [test_skill_portability_lint.py:613](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:613)：`AnnAssign` 停止点没有区分注解与实际赋值，属于既存未声明缺口。**

   ```python
   # 安全
   P = "/tmp/cls-exam/x"

   # 等计数替换
   P: "/tmp/cls-exam/x" = "/etc/passwd"
   ```

   `/tmp` 常量现在只是 annotation，实际赋值为 `/etc/passwd`；上溯抵达 `AnnAssign` 就停止，越界判据又忽略不含 `/tmp` 的实际值，因此全部放行。问题是**常量的语义角色未区分**，并非这个注解常量自身参与了动态运算。

5. **HIGH — [test_skill_portability_lint.py:677](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:677)：散文侧只检查成功提取的 span，裸 shell 与跨行 span 仍能绕过，属于整改未覆盖的既存缺口。**

   ```text
   安全：P="/tmp/cls-exam/x"
   越界：P="/tmp/cls-exam/"`printf .`"./x"
   ```

   唯一提取的 span 是 `printf .`，不含 `/tmp`；实际 shell 路径却为 `/tmp/x`。

   合法跨行 code span 同样漏检：

   ````text
   执行 ``cp
   "/tmp/cls-exam/"`printf .`"./x" out``
   ````

   CommonMark 会把换行归为空格，但当前散文已按物理行切开。**仅给正则加 DOTALL 也不足以修复这一层切分。**

**MEDIUM：1 条。**

- **MEDIUM — [test_skill_portability_lint.py:522](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:522)、`:1035`：裸 `/tmp` 仍能通过候选抵消复用已登记额度。**

  将原来的“禁写 `` `/tmp` ``”改成“禁写 /tmp”，同时新增 fence 内 `P = "/tmp"`：九计数仍全零，越界结果仍只有 `[('/tmp', '/tmp')]`，其余四项仍为空。

  单纯追加的旧反例已修复，但**去掉散文反引号造成的候选减少，可以抵消新增代码候选**；Counter 本身没有算错。

**LOW：1 条。**

- **LOW — [test_skill_portability_lint.py:2227](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:2227)：HIGH-3 新断言遗漏 heredoc 背景，不能证明窗口修复承重。**

  样本是完整合法 Python fence，`:512` 整块 AST 已成功，绕开 `_unit_end()`／`_parse_units()`。实测旧 r7 也能通过这条新增断言；在 r8 内存把窗口限回八行，断言仍通过。给同一坏形态补回 heredoc 后，八行变异才会暴露漏检。

其余维度逐项结论：

| 维度 | 复核结果 |
|---|---|
| `With/withitem`、默认参数、装饰器的 AST 上溯 | **未发现节点层误放。** 完整 AST 能触发；实际缺口在 HIGH-1 的前置切分。 |
| `comprehension/keyword/Starred/NamedExpr` | **未发现误放。** 验证的有效表达式均触发动态判据。 |
| `_R7_HIGH_FORMS` 其余七行 | **未发现指名判据承重问题。** 旧版漏、新版抓，安全对照对指名判据为绿。HIGH-5/6 的对照并非严格等结构，但未造成归因失效。 |
| 两条 LOW 整改 | **未发现残留问题。** 删除同字符条件、恢复分号截断，两种内存变异均使对应断言失败。 |
| `:2274` 的“至少有人红” | 前一条指名断言通过后必然成立，**没有额外承重**；不另计缺陷。 |
| Counter 次数诊断 | **未发现算法问题。** 能正确显示重复项的新增、缺失及次数重分配。 |
| 基线数量与误解风险 | 两提交常量实际为 **6→15 条**：board-recap `1→1`、quiz-answer `2→8`、start-exam-board `3→6`。未重测禁读正文。次数是提取结果数，同一物理路径可能被解析器与裸 token 各计一次，格式调整也可能报红。 |
| U5-B 交接 | 需同步九计数、越界多重集及受影响的行号基线；仅更新 `QUIZ_ANSWER_BASELINE` 不够。“新增即债”不能直接理解为新增了同等数量的物理路径。 |
| U6 交接 | **未发现本轮多重集改动带来的新问题。** 独立 scripts 不经过该 Counter；交接常量纯函数返回 `[]`。 |

残余风险尚未完整声明：仍有新引入及既存的、可静态确定的漏检，不能认定只剩保守误报和运行期不确定性。

**本轮 BLOCKER 0 条，HIGH 5 条。**
