> 批次: BATCH-2026-09-07-第十三批 · 车道 U4 · 卡 CARD-SKILL-PORT-LINT round-9
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-SKILL-PORT-LINT-r9.md)"`
> 审查绑定: `b5d0e78d`（Codex 自证「收尾时 HEAD 未变，工作区测试文件与提交 blob 一致」）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `OpenAI Codex v0.153.3`(:4) / `workdir: …/worktrees/card-u4-hosts`(:6) / `model: gpt-6-astra`(:7) / `sandbox: read-only`(:10) / `reasoning effort: ultra`(:11)

---

复核绑定 **`b5d0e78dbfa2b880eaab01d4099e5edb91c61f47`**；收尾时 HEAD 未变，工作区测试文件与提交 blob `2b593c86c734059311a30afb673720ee49260e75` 一致。未修改文件、运行 pytest、读取禁读正文或连接网络／数据库。

**BLOCKER：未发现。**

**HIGH：5 条，按根因合并。** 以下反例均经内存纯函数验证：安全／坏形态九项计数相同，五项附加判据全部 `[] → []`。

1. **HIGH — [test_skill_portability_lint.py:538](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:538)：首次 AST 成功仍会把必须保留上下文的复合语句拆开。**

   将下面代码放进 shell fence 的 Python heredoc：

   ```python
   if False:
       pass
   elif (P := "/tmp/cls-exam/" + "." * 2 + "/x"):
       pass
   ```

   `_parse_units()` 先认走 `if False + pass`；独立的 `elif` 头随后被 `_py_needs_more()` 判为不能继续，转交 shlex，丢失动态表达式。整段 `_has_dynamic_tmp_join()` 为 `True`，正式 `dynamic_tmp_join_lines()` 却为空。安全对照仅将赋值表达式换成 `"/tmp/cls-exam/x"`；坏形态静态得到 `/tmp/x`。**这是既存未声明缺口，codeop 修复没有封住。**

   同根残余还包括 [第 530 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:530) 的 **200 行硬上限**：构造 `P = (`、命名空间常量、197 行注释、`+ "." + "./x"`、`)`，合计 201 行，heredoc 内全部漏检；少一行注释则抓到 `fence:/tmp/x`。**这项 r8 已明确报告，本轮仍未修复。**

2. **HIGH — [test_skill_portability_lint.py:295](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:295)：转义掩码错误作用于 code span 内部，属于新回归。**

   ```text
   安全：执行 `/tmp/cls-exam/x\`
   越界：执行 `/var/cache(/tmp/cls-exam/x\`
   ```

   Code span 内反斜杠是普通字符，末尾反引号应正常闭合；全局掩码却将其抹掉，`_backtick_spans()` 返回空，opaque 的同一套掩码也无法兜底。旧版不掩码时能够提取该 span。

   因而关键缺陷不仅是“只允许转义 ASCII 标点”，还包括**转义规则必须区分 span 内外**。

3. **HIGH — [test_skill_portability_lint.py:281](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:281)、[第 341 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:341)：closing 允许任意引用前缀，没有绑定 opening 的容器层级，属于新回归。**

   ````text
   ```python
   A = 1
   > ```
   P = "/tmp/cls-exam/" + "." * 2 + "/x"
   ```
   ````

   普通 fence 内的 `> ``` ` 应是内容，本轮却提前闭合，后面的赋值落入散文而全漏。安全对照只改为命名空间内普通赋值。

   同一容器识别面还有既存缺口：合法的 **列表→引用** 开启行 `- > ```python` 不被识别；正则只支持引用→列表。引用深度不一致时，body 多出的 `>` 被保留，缺少的层级则直接停止剥离，**不会结束当前引用内 fence**。

4. **HIGH — [test_skill_portability_lint.py:662](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:662)、[第 707 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:707)：AnnAssign 修复只覆盖注解特例，常量与实际赋值仍可脱钩，属于既存未声明缺口。**

   ```python
   # 安全
   P = "/tmp/cls-exam/x"

   # 等计数替换
   "/tmp/cls-exam/x"; P = "/etc/passwd"
   ```

   在普通 Python fence 中，合规常量变成无效用的表达式；上溯遇到 `Expr` 就停止，实际赋值又因不含 `/tmp` 被越界判据忽略。沿用 r8 HIGH-4 的“实际赋值”口径，这仍是可静态确定的漏检。

5. **HIGH — [test_skill_portability_lint.py:374](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:374)、[第 781 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:781)：嵌入式 span 判据仍漏掉合法 shell 与跨行 span，属于 r8 HIGH-5 整改残余。**

   ```text
   安全：执行 cp "/tmp/cls-exam/"_`printf a`_ out
   越界：执行 cp "/var/cache""/tmp/cls-exam/"_`printf a`_ out
   ```

   仅增加 `"/var/cache"`，实际参数变为 `/var/cache/tmp/cls-exam/_a_`；但 span 两侧 `_` 都在分隔符表中，判为非嵌入式。两侧换成 `:` 也全部漏检。**表中字符可以同时是合法 shell 词的一部分，不能据此排除命令替换。**

   另外两种已复现残余：

   - 裸 shell `P="/tmp/cls-exam/"\.\./x`：实际为 `/tmp/x`，没有反引号，opaque 散文分支不登记。
   - 跨行 span：

     ```text
     执行 `/var/cache(
     /tmp/cls-exam/x`
     ```

     CommonMark 将换行归为空格；实际 span 内容越界，但 [第 351 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:351) 仍按物理行产出散文，两行都没有完整 span。新增形态表只覆盖了其中含局部命令替换的特例。

**MEDIUM：2 条。**

- **MEDIUM — [test_skill_portability_lint.py:595](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:595)：同一 `prose` 来源内仍可抵消候选。**

  ```text
  修改前：
  禁止在 `/tmp` 落临时文件。
  留空。

  修改后：
  禁止在 /tmp 落临时文件。
  运行 `mktemp -p` `/tmp`。
  ```

  九计数均全零；越界结果都只有 `('/tmp', 'prose:/tmp')`；其余四项为空。新增命名空间外临时文件指令仍能复用额度。原跨来源反例已修，同来源残余仍在。

- **MEDIUM — [test_skill_portability_lint.py:1141](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1141)：端口放行只验证缺省子串，未声明它不能保证环境变量仍可覆盖。**

  在原命令前增加 `CLS_BACKEND_URL=;`：

  ```sh
  CLS_BACKEND_URL=; curl "${CLS_BACKEND_URL:-http://localhost:8011}/api/v1/ping"
  ```

  九计数及五集合全部不变，但外部配置被清空，命令无条件使用 localhost:8011。这是可静态确定的等计数缺口，不依赖未知运行期输入。

**LOW：3 条。**

- **LOW — [test_skill_portability_lint.py:2277](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:2277)：安全锚漏更新来源前缀，属于新回归。**  
  仍断言 `"/tmp/cls-exam/a" not in norms`。内存额外注入错误候选 `fence:/tmp/cls-exam/a` 后，整条独立参数测试仍通过，无法发现首个合规参数被误报。

- **LOW — [test_skill_portability_lint.py:374](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:374)：常见中文标点遗漏造成新误报。**  
  正常 Markdown `路径：“`/tmp/cls-exam/x`”` 会触发 opaque；`‘’`、`『』`、`〔〕` 同样如此，`（）` 对照不报。方向保守，但当前声明没有具体覆盖这些常见写法。

- **LOW — [test_skill_portability_lint.py:1263](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1263)：来源翻转的报错会误导交接。**  
  将 inline `/tmp` 改为 fenced `/tmp`，九计数不变，却出现 `prose:/tmp` 缺失、`fence:/tmp` 新增；消息仍解释成“新增即债／缺失说明有人整改”。这是提取来源变化，不能据此推断物理债增减。

其余要求逐项结论：

| 维度 | 复核结果 |
|---|---|
| `\` 续行、多行装饰器、`async with` | **已测有效样本未发现新漏检。** `elif` 上下文问题见 HIGH-1。 |
| AnnAssign 原反例 | **未发现修复失效。** 注解现在会触发动态判据。 |
| 非 ASCII 标点转义的多掩 | 确有过宽掩码；**未发现其单独造成丢 span 的反例**。已证实问题是 HIGH-2 的 span 内外混淆。 |
| 形态表 15 行指名判据 | **未发现失效。** 全部坏形态红、安全对照对指名判据绿。 |
| heredoc 内存变异 | **验证成立。** `_py_needs_more=False` 使第 5、9 行由红转漏；相同纯 Python fence 仍被整块 AST 抓住。`_UNIT_MAX_LINES=8` 也能使第 5 行失败。 |
| 安全对照是否只差一处 | **并非全部严格等结构。** HIGH-5/6 保留 r8 已声明差异；未发现因此新增归因失效。 |
| “至少有人红”断言 | 被前面的指名断言蕴涵，仍无额外承重；不另计。 |
| Counter 与来源归属 | **未发现 Counter 算法问题。** 同一物理出现位置只归一种来源；解析器与裸 token 的重复提取仍可能存在。 |
| U5-B／U6 | U5-B 需同步来源多重集及受影响行号，不能只改九计数。**未发现来源前缀给 U6 scripts 带来新问题**；交接常量纯函数返回 `[]`。 |

残余风险**尚未完整声明**：存在两类新 HIGH 回归、r8 已报未修边界，以及上述可静态确定的未声明漏检。不能认定只剩保守误报和运行期不确定性。

**本轮 BLOCKER 0 条，HIGH 5 条。**
