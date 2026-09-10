> 批次: BATCH-2026-09-07-第十三批 · 车道 U4 · 卡 CARD-SKILL-PORT-LINT round-7
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-SKILL-PORT-LINT-r7.md)"`
> 审查绑定: `26d6df62`（Codex 自证审计期间工作区有外部修改——那是本 session 改了一段 docstring，它已从该 commit 的文件对象重新加载复验）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `OpenAI Codex v0.153.3`(:2) / `workdir: …/worktrees/card-u4-hosts`(:4) / `model: gpt-6-astra`(:5) · `sandbox: read-only`(:8) · `reasoning effort: ultra`(:9)

---

复核绑定 **`26d6df62`**，测试文件对象为 **`485b6445b168367a23884a84a81f0fe5dc14ffa4`（2516 行）**。期间工作区文件发生外部修改，以下结论均已从指定提交在内存重新加载、复验。未修改文件、运行 pytest、读取禁读正文或连接服务。

**BLOCKER：未发现。**

**HIGH：6 类。** 以下各例都有安全对照，实测九项计数完全相同，越界／可疑行／动态拼接／散文／不透明五集合均为 **`[] → []`**。这些是纯函数证据，不代表整树测试通过。

1. **HIGH — [test_skill_portability_lint.py:274](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:274)、`:592`：合法行内代码中的命令替换仍可完全绕过。**

   ```text
   安全：执行 ``cp "/tmp/cls-exam/x" out``
   越界：执行 ``cp "/tmp/cls-exam/"`printf .`"./x" out``
   ```

   双反引号包住的内容是合法 Markdown code span；内部命令替换产生 `.`，路径规范化为 `/tmp/x`。第八条跳过散文，单反引号正则又无法完整提取该 span，留下整类覆盖缺口。

2. **HIGH — [test_skill_portability_lint.py:299](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:299)、`:311、273`：新 fence 判定误伤合法波浪线围栏，旧的两种边界漏检也仍存在。**

   ```text
   ~~~python title=~~~
   P = "/tmp/cls-exam/" + "." * 2 + "/x"
   ~~~
   ```

   波浪线围栏的 info string 可以含 `~~~`，但新条件把开启行排除，赋值随之落入散文。与安全赋值对照，全部判据不变，实际路径却为 `/tmp/x`。

   同根复验还确认：**带尾随文字的 ` ```not-a-close` 仍被错误闭合；列表首行 `- ```python` 仍不被识别。** 两者均能让后续相同越界表达式漏检，属于 r6 未关闭部分。

3. **HIGH — [test_skill_portability_lint.py:397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:397)、`:404–406、444`：合法 Python 语句超过八行后，外层表达式会被丢弃并放行。**

   放在 `python3 - <<'PYEOF'` heredoc 内：

   ```python
   P = (
       "/tmp/cls-exam/"
       + "."
       + "."
       + "/"
       + "x"
       + "."
       + "json"
   )
   ```

   安全对照仅将前两个 `"."` 改成 `"a"`、`"b"`。完整 AST 可直接折出坏值 `/tmp/cls-exam/../x.json`；窗口失败后，第二行却被认作独立字符串表达式，拼接关系永久消失。**声明八行上限，没有声明超限有效代码会静默漏检。**

4. **HIGH — [test_skill_portability_lint.py:497](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:497)、`:537–538`：`AugAssign` 被错误当作安全停止点。**

   ```python
   P = "/var/cache"
   P += "/tmp/cls-exam/x"
   ```

   与第二行使用普通 `=` 的对照相比，全部判据不变；实际值变为 `/var/cache/tmp/cls-exam/x`。`+=` 本身包含拼接，抵达该语句节点不能证明“纯静态字面量”。问题是停止名单收得过宽。

5. **HIGH — [test_skill_portability_lint.py:405](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:405)、`:445、567`：合法 shell 跨行引号仍被拆坏，即使只有两行也漏检。**

   在 shell fence 内：

   ```sh
   P='
   /tmp/cls-exam/x'
   ```

   与单行安全赋值加一行注释对照，全部判据相同。完整 `_sh_words()` 能得到包含前导换行的赋值，路径实际是命名空间外的相对路径；当前降级分别解析两行，两边都因引号未闭而弃权。它没有反斜杠或反引号，第八条也不触发。**完整输入是合法 shell，不能归入已声明的“畸形 shell”。**

6. **HIGH — [test_skill_portability_lint.py:597](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:597)、`:600、602`：续行链切窗后丢失跨组关联，七条连接出现假绿。**

   ```sh
   P='\
   \
   \
   \
   \
   \
   \
   /tmp/cls-exam/x'
   ```

   前七行分成一组但不含 `/tmp`；最后一行含 `/tmp` 却没有记号，因此第八条返回空。Python 会消掉反斜杠换行，shell 单引号则保留它们，实际值不是命名空间内的绝对路径。与等行数安全对照相比，全部判据不变。边界复测为：**六条连接能抓，七条漏，八条又能抓，十四条再次漏。**

**MEDIUM：1 条续存。**

- **MEDIUM — [test_skill_portability_lint.py:929](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:929)、`:432–433`：已登记裸 `/tmp` 可以被新增代码重复使用而不登记。** 已有“禁写 `/tmp`”的正文末尾新增 fence 内 `P = "/tmp"`，九计数不变、越界仍仅 `[('/tmp', '/tmp')]`，其余集合不变。正文只计 `/tmp/`，候选又去重；r6 此项仍成立。

**LOW：2 条续存。**

- **LOW — [test_skill_portability_lint.py:2082](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:2082)、`:2090`：围栏测试不承重“同字符”要求。** 在内存删除闭合条件中的同字符判断后，该测试仍全部通过。未使用的 `sandbox` 参数也仍会触发复制 fixture。
- **LOW — [test_skill_portability_lint.py:1469](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1469)、`:1500`：分号样本不能证明尾部未被截断。** 在内存将候选于分号处截断后，覆盖表仍 **16/16 通过**，因为截断后的原路径已经越界。

其余问题逐项结论：

| 维度 | 复核结果 |
|---|---|
| 第八条组间重复、覆盖重叠、行号偏一 | **未发现。** `i = j + 1` 保证分组不重叠；HIGH-6 是关联丢失。 |
| 无害长命令的登记噪声 | 会发生，属于该判据选择的保守方向；当前零命中不能证明未来零成本。 |
| U6 修改独立 scripts 是否触发第八条 | **不会。** 第八条正式检查只遍历 SKILL.md；scripts 走计数层。 |
| 普通未闭合 fence 到 EOF | **未发现问题。** 仍保留代码上下文。 |
| 正常关闭后再次开启 fence | **未发现问题。** |
| 八行以内贪心吞并造成独立漏检 | **未发现独立反例。** `if/else` 确会被拆开，但相关漏检在完整 AST 下也存在，不能单独归责贪心。 |
| With／For／comprehension／keyword／Starred | **未发现误放。** 合成输入均触发动态判据。 |
| `ast.walk` 重复访问覆盖常量父链 | **未发现。** |
| 新增三段归因负控 | 同形合成文本中**未发现**前提空跑或其他判据代打红；未执行完整 sandbox。 |
| opaque、parse-units、动态常量验伪锚 | **未发现失效。** 对应恒红／恒绿、窗口退回单行的内存变异均被抓住。 |
| ⑰标记行、⑱scripts 端口断言 | **未发现新增承重问题。** |
| r6 的跨行假越界候选 | **已关闭。** 安全拼接为空，坏拼接返回真实越界路径。 |
| 交接常量 | **未发现问题。** 正式纯函数返回 `[]`。 |

收尾判断：**残余风险尚未完整声明，仍有可静态确定的漏检，不能认定只剩保守误报和运行期不确定性。**

**本轮 BLOCKER 0 条，HIGH 6 条。**
